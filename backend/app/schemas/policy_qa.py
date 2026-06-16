"""Policy Q&A request/response schemas."""

from pydantic import BaseModel


class Message(BaseModel):
    """A single turn in a conversation."""

    role: str
    content: str


class PolicyQARequest(BaseModel):
    """Payload for a policy Q&A question."""

    question: str
    conversation_history: list[Message] = []


class CitedClause(BaseModel):
    """A policy clause cited in an answer."""

    doc_id: str
    section_id: str
    section_title: str
    text: str


class PolicyQAResponse(BaseModel):
    """Policy Q&A answer with citations."""

    answer: str
    citations: list[CitedClause]
    refused: bool = False
    refusal_reason: str | None = None
