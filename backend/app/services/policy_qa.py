"""Policy Q&A service — thin wrapper delegating to RAGService.answer_question."""

from app.schemas.policy_qa import CitedClause, Message, PolicyQAResponse
from app.services.rag import RAGService


async def answer_policy_question(
    question: str,
    conversation_history: list[Message],
    rag: RAGService,
) -> PolicyQAResponse:
    """Answer a policy question using the RAG pipeline."""
    history = [{"role": m.role, "content": m.content} for m in conversation_history]
    result = await rag.answer_question(question=question, conversation_history=history)

    citations = [
        CitedClause(
            doc_id=c["doc_id"],
            section_id=c["section_id"],
            section_title=c["section_title"],
            text=c["text"],
        )
        for c in result.get("citations", [])
    ]

    return PolicyQAResponse(
        answer=result.get("answer", ""),
        citations=citations,
        refused=bool(result.get("refused", False)),
        refusal_reason=result.get("refusal_reason"),
    )
