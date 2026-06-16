"""Override endpoints — append-only verdict override audit trail."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.line_item import LineItem
from app.models.override import Override
from app.schemas.override import OverrideCreate, OverrideOut

router = APIRouter(prefix="/api/line-items", tags=["overrides"])


@router.post("/{line_item_id}/override", response_model=OverrideOut, status_code=201)
async def create_override(
    line_item_id: str,
    payload: OverrideCreate,
    session: AsyncSession = Depends(get_session),
) -> Override:
    """Record a human reviewer override for a line item verdict."""
    item = await session.get(LineItem, line_item_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"LineItem {line_item_id} not found")

    override = Override(
        id=str(uuid.uuid4()),
        line_item_id=line_item_id,
        reviewer_id=payload.reviewer_id,
        original_verdict=item.verdict,
        new_verdict=payload.new_verdict,
        comment=payload.comment,
    )
    item.verdict = payload.new_verdict
    session.add(override)
    await session.commit()
    await session.refresh(override)
    return override


@router.get("/{line_item_id}/overrides", response_model=list[OverrideOut])
async def list_overrides(
    line_item_id: str,
    session: AsyncSession = Depends(get_session),
) -> list[Override]:
    """Return full override audit trail for a line item."""
    item = await session.get(LineItem, line_item_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"LineItem {line_item_id} not found")

    result = await session.execute(
        select(Override)
        .where(Override.line_item_id == line_item_id)
        .order_by(Override.created_at)
    )
    return list(result.scalars().all())
