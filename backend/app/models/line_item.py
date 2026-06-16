"""LineItem ORM model — one per uploaded receipt."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class LineItem(Base):
    """A single receipt within a submission, with its verdict."""

    __tablename__ = "line_items"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    submission_id: Mapped[str] = mapped_column(ForeignKey("submissions.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    file_hash: Mapped[str] = mapped_column(String, nullable=False)
    vendor: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    verdict: Mapped[str] = mapped_column(String, nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    cited_clause: Mapped[str] = mapped_column(Text, nullable=False)
    policy_doc_ids: Mapped[str] = mapped_column(String, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    flags: Mapped[str] = mapped_column(String, nullable=False, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    submission: Mapped["Submission"] = relationship("Submission", back_populates="line_items")  # type: ignore[name-defined]
    overrides: Mapped[list["Override"]] = relationship(  # type: ignore[name-defined]
        "Override", back_populates="line_item", lazy="selectin"
    )
