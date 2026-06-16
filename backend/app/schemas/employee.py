"""Employee request/response schemas."""

from datetime import datetime

from pydantic import BaseModel


class EmployeeCreate(BaseModel):
    """Payload to create a new employee."""

    id: str
    name: str
    grade: int
    title: str
    department: str
    manager_id: str | None = None
    home_base: str


class EmployeeOut(BaseModel):
    """Employee response shape."""

    id: str
    name: str
    grade: int
    title: str
    department: str
    manager_id: str | None
    home_base: str
    created_at: datetime

    model_config = {"from_attributes": True}
