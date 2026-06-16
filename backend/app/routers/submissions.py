"""Submission endpoints."""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.employee import Employee
from app.models.submission import Submission
from app.schemas.submission import (
    SubmissionCreate,
    SubmissionDetailOut,
    SubmissionOut,
    SubmissionStatusPatch,
)

router = APIRouter(prefix="/api/submissions", tags=["submissions"])


@router.post("", response_model=SubmissionOut, status_code=201)
async def create_submission(
    payload: SubmissionCreate,
    session: AsyncSession = Depends(get_session),
) -> Submission:
    """Create a new expense submission."""
    emp = await session.get(Employee, payload.employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail=f"Employee {payload.employee_id} not found")

    sub = Submission(
        id=str(uuid.uuid4()),
        employee_id=payload.employee_id,
        trip_purpose=payload.trip_purpose,
        trip_start=payload.trip_start,
        trip_end=payload.trip_end,
        status="pending",
    )
    session.add(sub)
    await session.commit()
    await session.refresh(sub)
    return sub


@router.get("", response_model=list[SubmissionOut])
async def list_submissions(
    employee_id: str | None = Query(None),
    status: str | None = Query(None),
    from_date: date | None = Query(None, alias="from"),
    to_date: date | None = Query(None, alias="to"),
    session: AsyncSession = Depends(get_session),
) -> list[Submission]:
    """List submissions with optional filters."""
    query = select(Submission).order_by(Submission.created_at.desc())

    if employee_id:
        query = query.where(Submission.employee_id == employee_id)
    if status:
        query = query.where(Submission.status == status)
    if from_date:
        query = query.where(Submission.trip_start >= from_date)
    if to_date:
        query = query.where(Submission.trip_end <= to_date)

    result = await session.execute(query)
    return list(result.scalars().all())


@router.get("/{submission_id}", response_model=SubmissionDetailOut)
async def get_submission(
    submission_id: str,
    session: AsyncSession = Depends(get_session),
) -> Submission:
    """Return full submission detail including line items."""
    sub = await session.get(Submission, submission_id)
    if not sub:
        raise HTTPException(status_code=404, detail=f"Submission {submission_id} not found")
    return sub


@router.patch("/{submission_id}/status", response_model=SubmissionOut)
async def update_submission_status(
    submission_id: str,
    payload: SubmissionStatusPatch,
    session: AsyncSession = Depends(get_session),
) -> Submission:
    """Update submission status."""
    valid_statuses = {"pending", "in_review", "approved", "rejected"}
    if payload.status not in valid_statuses:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid status. Must be one of: {valid_statuses}",
        )

    sub = await session.get(Submission, submission_id)
    if not sub:
        raise HTTPException(status_code=404, detail=f"Submission {submission_id} not found")

    sub.status = payload.status
    await session.commit()
    await session.refresh(sub)
    return sub
