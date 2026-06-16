"""Index policy PDFs into ChromaDB on startup."""

import structlog

from app.services.rag import RAGService

logger = structlog.get_logger(__name__)


async def seed_policies(rag: RAGService) -> None:
    """Index all policy PDFs. Idempotent — skips already-indexed chunks."""
    total = rag.index_policies()
    logger.info("Policy seeding complete", total_chunks=total)
