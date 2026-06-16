"""Override ORM model — immutable audit trail of verdict changes."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Override(Base):
    """Immutable record of a human reviewer overriding an AI verdict.

    Never UPDATE this table — append-only.
    """

    __tablename__ = "overrides"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    line_item_id: Mapped[str] = mapped_column(ForeignKey("line_items.id"), nullable=False)
    reviewer_id: Mapped[str] = mapped_column(String, nullable=False)
    original_verdict: Mapped[str] = mapped_column(String, nullable=False)
    new_verdict: Mapped[str] = mapped_column(String, nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    line_item: Mapped["LineItem"] = relationship("LineItem", back_populates="overrides")  # type: ignore[name-defined]
