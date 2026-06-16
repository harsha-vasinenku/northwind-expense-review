"""Policy Q&A endpoint."""

import structlog
from fastapi import APIRouter

from app.schemas.policy_qa import PolicyQARequest, PolicyQAResponse
from app.services.policy_qa import answer_policy_question
from app.services.rag import get_rag_service

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/policy", tags=["policy"])


@router.post("/ask", response_model=PolicyQAResponse)
async def ask_policy_question(payload: PolicyQARequest) -> PolicyQAResponse:
    """Answer a policy question using the RAG pipeline."""
    rag = get_rag_service()
    result = await answer_policy_question(
        question=payload.question,
        conversation_history=payload.conversation_history,
        rag=rag,
    )
    logger.info(
        "Policy Q&A",
        question=payload.question[:80],
        refused=result.refused,
        citations=len(result.citations),
    )
    return result
