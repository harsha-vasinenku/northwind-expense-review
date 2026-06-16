"""ChromaDB-backed policy RAG service.

Indexes all policy PDFs at startup and provides semantic search over policy clauses.
"""

import re
from dataclasses import dataclass
from pathlib import Path

import chromadb
import pdfplumber
import structlog

from app.config import get_settings
from app.constants import NON_TE_POLICY_IDS

logger = structlog.get_logger(__name__)

POLICIES_DIR = Path(__file__).parent.parent.parent / "data" / "policies"
COLLECTION_NAME = "northwind_policies"


@dataclass
class PolicyChunk:
    """A single indexed chunk from a policy document."""

    chunk_id: str
    doc_id: str
    doc_title: str
    section_id: str
    section_title: str
    text: str
    is_noise: bool = False


class RAGService:
    """Manages policy indexing and semantic search via ChromaDB."""

    def __init__(self) -> None:
        settings = get_settings()
        self._client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def _extract_doc_metadata(self, text: str) -> tuple[str, str]:
        """Parse doc ID and title from policy header text."""
        doc_id_match = re.search(r"Document:\s*([\w-]+)", text)
        doc_id = doc_id_match.group(1) if doc_id_match else "UNKNOWN"

        title_match = re.match(r"^(.+?)\n", text)
        doc_title = title_match.group(1).strip() if title_match else doc_id

        return doc_id, doc_title

    def _chunk_policy_text(self, text: str, doc_id: str, doc_title: str) -> list[PolicyChunk]:
        """Split policy text into section-level chunks.

        Splits on numbered section headings (e.g. '2.', '2.1.') and § markers.
        Never splits mid-sentence.
        """
        section_pattern = re.compile(
            r"(?m)^(?:§\s*[\d.]+|(?:\d+\.)+\d*)\s+.{3,80}$"
        )

        matches = list(section_pattern.finditer(text))
        chunks: list[PolicyChunk] = []

        if not matches:
            chunk = PolicyChunk(
                chunk_id=f"{doc_id}-full",
                doc_id=doc_id,
                doc_title=doc_title,
                section_id="§0",
                section_title="Full document",
                text=text[:4000],
                is_noise=doc_id in NON_TE_POLICY_IDS,
            )
            chunks.append(chunk)
            return chunks

        for idx, match in enumerate(matches):
            section_heading = match.group(0).strip()
            start = match.end()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
            section_body = text[start:end].strip()

            if len(section_body) < 30:
                continue

            section_num_match = re.match(r"(§[\d.]+|(?:\d+\.)+\d*)", section_heading)
            section_id = section_num_match.group(1) if section_num_match else f"§{idx}"
            section_title_part = section_heading.replace(
                section_num_match.group(1) if section_num_match else "", ""
            ).strip()

            chunk_text = f"{section_heading}\n{section_body}"[:4000]
            chunk_id = f"{doc_id}-{section_id}".replace(".", "_")

            chunks.append(
                PolicyChunk(
                    chunk_id=chunk_id,
                    doc_id=doc_id,
                    doc_title=doc_title,
                    section_id=section_id,
                    section_title=section_title_part or section_heading,
                    text=chunk_text,
                    is_noise=doc_id in NON_TE_POLICY_IDS,
                )
            )

        return chunks

    def index_policies(self) -> int:
        """Index all policy PDFs from the policies directory.

        Returns the total number of chunks indexed.
        Idempotent — existing chunks are not re-embedded.
        """
        existing_ids: set[str] = set(self._collection.get()["ids"])
        new_chunks: list[PolicyChunk] = []

        for pdf_path in sorted(POLICIES_DIR.glob("*.pdf")):
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    full_text = "\n".join(
                        page.extract_text() or "" for page in pdf.pages
                    )
            except Exception:
                logger.exception("Failed to extract PDF", path=str(pdf_path))
                continue

            doc_id, doc_title = self._extract_doc_metadata(full_text)
            chunks = self._chunk_policy_text(full_text, doc_id, doc_title)

            for chunk in chunks:
                if chunk.chunk_id not in existing_ids:
                    new_chunks.append(chunk)

            logger.info(
                "Policy indexed",
                doc_id=doc_id,
                doc_title=doc_title,
                chunks=len(chunks),
                file=pdf_path.name,
            )

        # Deduplicate by chunk_id within the batch (handles section ID collisions)
        seen_ids: set[str] = set()
        deduped: list[PolicyChunk] = []
        for chunk in new_chunks:
            if chunk.chunk_id not in seen_ids:
                seen_ids.add(chunk.chunk_id)
                deduped.append(chunk)
        new_chunks = deduped

        if new_chunks:
            self._collection.add(
                ids=[c.chunk_id for c in new_chunks],
                documents=[c.text for c in new_chunks],
                metadatas=[
                    {
                        "doc_id": c.doc_id,
                        "doc_title": c.doc_title,
                        "section_id": c.section_id,
                        "section_title": c.section_title,
                        "is_noise": str(c.is_noise),
                    }
                    for c in new_chunks
                ],
            )
            logger.info("New chunks indexed", count=len(new_chunks))

        total = self._collection.count()
        logger.info("RAG index ready", total_chunks=total)
        return total

    def get_indexed_doc_ids(self) -> set[str]:
        """Return the set of doc_ids currently in the ChromaDB collection."""
        results = self._collection.get(include=["metadatas"])
        return {m["doc_id"] for m in results["metadatas"] if m}

    async def search(
        self,
        query: str,
        category: str | None = None,
        n_results: int = 5,
    ) -> list[PolicyChunk]:
        """Search policy library for relevant clauses.

        T&E policy chunks are prioritised; noise docs returned only as fallback.
        """
        raw = self._collection.query(
            query_texts=[query],
            n_results=min(n_results * 2, self._collection.count() or 1),
            include=["documents", "metadatas"],
        )

        chunks = []
        for doc, meta in zip(raw["documents"][0], raw["metadatas"][0]):
            chunks.append(
                PolicyChunk(
                    chunk_id="",
                    doc_id=meta["doc_id"],
                    doc_title=meta["doc_title"],
                    section_id=meta["section_id"],
                    section_title=meta["section_title"],
                    text=doc,
                    is_noise=meta.get("is_noise", "False") == "True",
                )
            )

        te_chunks = [c for c in chunks if not c.is_noise]
        result = te_chunks[:n_results] if te_chunks else chunks[:n_results]
        return result

    async def answer_question(
        self,
        question: str,
        conversation_history: list[dict[str, str]],
    ) -> dict[str, object]:
        """Answer a policy question using RAG + Claude.

        Returns a dict matching PolicyQAResponse shape.
        """
        import anthropic

        from app.config import get_settings as _get_settings

        settings = _get_settings()
        chunks = await self.search(question, n_results=5)

        if not chunks:
            return {
                "answer": "",
                "citations": [],
                "refused": True,
                "refusal_reason": "No relevant policy content found for this question.",
            }

        context = "\n\n".join(
            f"[{c.doc_id} {c.section_id} — {c.section_title}]\n{c.text}" for c in chunks
        )

        system_prompt = (
            "You are a policy assistant for Northwind Logistics. "
            "Answer questions about company T&E policy using ONLY the policy excerpts provided. "
            "If the question is out of scope (not about T&E policy) or cannot be answered from "
            "the provided excerpts, respond with a refusal. "
            "Always cite the specific policy doc and section (e.g. TEP-001 §2.1)."
        )

        messages: list[dict[str, str]] = list(conversation_history)
        messages.append(
            {
                "role": "user",
                "content": (
                    f"POLICY EXCERPTS:\n{context}\n\n"
                    f"QUESTION: {question}\n\n"
                    "If this question is about something outside Northwind T&E policies (e.g. salaries, "
                    "stock price, personal advice), reply with exactly: "
                    "REFUSED: <one sentence explaining why you cannot answer>. "
                    "Otherwise answer concisely with citations."
                ),
            }
        )

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=system_prompt,
            messages=messages,
        )

        answer_text = response.content[0].text if response.content else ""

        if answer_text.startswith("REFUSED:"):
            return {
                "answer": "",
                "citations": [],
                "refused": True,
                "refusal_reason": answer_text[len("REFUSED:"):].strip(),
            }

        citations = []
        for chunk in chunks:
            if chunk.doc_id in answer_text or chunk.section_id in answer_text:
                citations.append(
                    {
                        "doc_id": chunk.doc_id,
                        "section_id": chunk.section_id,
                        "section_title": chunk.section_title,
                        "text": chunk.text[:400],
                    }
                )

        return {
            "answer": answer_text,
            "citations": citations,
            "refused": False,
            "refusal_reason": None,
        }


_rag_service: RAGService | None = None


def get_rag_service() -> RAGService:
    """Return the singleton RAGService instance."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
