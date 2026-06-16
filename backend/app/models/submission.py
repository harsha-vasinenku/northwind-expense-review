"""Submission ORM model."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Submission(Base):
    """Expense submission (one per trip)."""

    __tablename__ = "submissions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    employee_id: Mapped[str] = mapped_column(ForeignKey("employees.id"), nullable=False)
    trip_purpose: Mapped[str] = mapped_column(String, nullable=False)
    trip_start: Mapped[date] = mapped_column(Date, nullable=False)
    trip_end: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, onupdate=func.now(), nullable=True)

    line_items: Mapped[list["LineItem"]] = relationship(  # type: ignore[name-defined]
        "LineItem", back_populates="submission", lazy="selectin"
    )
    employee: Mapped["Employee"] = relationship("Employee", lazy="selectin")  # type: ignore[name-defined]
