"""LineItem request/response schemas."""

import json
from datetime import date, datetime

from pydantic import BaseModel, field_validator

from app.schemas.override import OverrideOut


class LineItemOut(BaseModel):
    """Line item response shape."""

    id: str
    submission_id: str
    filename: str
    vendor: str
    date: date
    amount: float
    category: str
    verdict: str
    reasoning: str
    cited_clause: str
    policy_doc_ids: list[str]
    confidence: float
    flags: list[str]
    created_at: datetime
    overrides: list[OverrideOut] = []

    model_config = {"from_attributes": True}

    @field_validator("policy_doc_ids", mode="before")
    @classmethod
    def parse_policy_doc_ids(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return json.loads(v)
        return v

    @field_validator("flags", mode="before")
    @classmethod
    def parse_flags(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return json.loads(v)
        return v
