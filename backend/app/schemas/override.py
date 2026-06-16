"""Override request/response schemas."""

from datetime import datetime

from pydantic import BaseModel

from app.constants import Verdict


class OverrideCreate(BaseModel):
    """Payload to submit a verdict override."""

    reviewer_id: str
    new_verdict: Verdict
    comment: str


class OverrideOut(BaseModel):
    """Override response shape."""

    id: str
    line_item_id: str
    reviewer_id: str
    original_verdict: str
    new_verdict: str
    comment: str
    created_at: datetime

    model_config = {"from_attributes": True}
