"""Submission request/response schemas."""

from datetime import date, datetime

from pydantic import BaseModel

from app.schemas.employee import EmployeeOut
from app.schemas.line_item import LineItemOut


class SubmissionCreate(BaseModel):
    """Payload to create a new submission."""

    employee_id: str
    trip_purpose: str
    trip_start: date
    trip_end: date


class SubmissionStatusPatch(BaseModel):
    """Payload to update submission status."""

    status: str


class SubmissionOut(BaseModel):
    """Submission summary response."""

    id: str
    employee_id: str
    trip_purpose: str
    trip_start: date
    trip_end: date
    status: str
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class SubmissionDetailOut(BaseModel):
    """Full submission including employee and line items."""

    id: str
    employee_id: str
    trip_purpose: str
    trip_start: date
    trip_end: date
    status: str
    created_at: datetime
    updated_at: datetime | None = None
    employee: EmployeeOut | None = None
    line_items: list[LineItemOut] = []

    model_config = {"from_attributes": True}
