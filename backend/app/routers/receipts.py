"""Receipt upload endpoint — runs ingestion + verdict pipeline."""

import json
import uuid
from pathlib import Path

import structlog
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.constants import MAX_UPLOAD_BYTES, SUPPORTED_EXTENSIONS
from app.database import get_session
from app.models.line_item import LineItem
from app.models.submission import Submission
from app.schemas.line_item import LineItemOut
from app.services.ingestion import compute_file_hash, extract_receipt
from app.services.rag import get_rag_service
from app.services.verdict import run_verdict

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/submissions", tags=["receipts"])


@router.post("/{submission_id}/receipts", response_model=LineItemOut, status_code=201)
async def upload_receipt(
    submission_id: str,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
) -> LineItem:
    """Upload a receipt file, run the ingestion + verdict pipeline, persist the result."""
    sub = await session.get(Submission, submission_id)
    if not sub:
        raise HTTPException(status_code=404, detail=f"Submission {submission_id} not found")

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=422,
            detail={
                "error": f"Unsupported file type: {suffix}",
                "detail": f"Accepted types: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
                "code": "UNSUPPORTED_FILE_TYPE",
            },
        )

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail={"error": "File too large", "code": "FILE_TOO_LARGE"},
        )

    file_hash = compute_file_hash(content)

    existing = await session.execute(
        select(LineItem).where(
            LineItem.submission_id == submission_id,
            LineItem.file_hash == file_hash,
        )
    )
    dup = existing.scalar_one_or_none()
    if dup:
        logger.info("Duplicate receipt skipped", filename=file.filename, submission_id=submission_id)
        return dup

    settings = get_settings()
    upload_dir = Path(settings.upload_dir) / submission_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid.uuid4()}{suffix}"
    file_path = upload_dir / safe_name
    file_path.write_bytes(content)

    try:
        extracted = await extract_receipt(
            filename=file.filename or safe_name,
            content=content,
            suffix=suffix,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={"error": str(exc), "code": "RECEIPT_PARSE_FAILED"},
        ) from exc
    except Exception as exc:
        logger.exception("Receipt extraction failed", filename=file.filename)
        raise HTTPException(
            status_code=500,
            detail={"error": "Receipt extraction failed", "code": "RECEIPT_PARSE_FAILED"},
        ) from exc

    emp = sub.employee
    rag = get_rag_service()

    try:
        verdict = await run_verdict(
            receipt=extracted,
            employee_name=emp.name,
            employee_grade=emp.grade,
            employee_title=emp.title,
            trip_purpose=sub.trip_purpose,
            trip_start=sub.trip_start,
            trip_end=sub.trip_end,
            rag=rag,
        )
    except Exception as exc:
        logger.exception("Verdict engine failed", filename=file.filename)
        raise HTTPException(
            status_code=500,
            detail={"error": "Verdict engine failed", "code": "VERDICT_FAILED"},
        ) from exc

    line_item = LineItem(
        id=str(uuid.uuid4()),
        submission_id=submission_id,
        filename=file.filename or safe_name,
        file_path=str(file_path),
        file_hash=file_hash,
        vendor=extracted.vendor,
        date=extracted.date,
        amount=extracted.amount,
        category=extracted.category,
        raw_text=extracted.raw_text,
        verdict=verdict.verdict,
        reasoning=verdict.reasoning,
        cited_clause=verdict.cited_clause,
        policy_doc_ids=json.dumps(verdict.policy_doc_ids),
        confidence=verdict.confidence,
        flags=json.dumps(verdict.flags),
    )
    session.add(line_item)

    if sub.status == "pending":
        sub.status = "in_review"

    await session.commit()
    await session.refresh(line_item)

    logger.info(
        "Receipt processed",
        submission_id=submission_id,
        filename=file.filename,
        verdict=verdict.verdict,
        confidence=verdict.confidence,
    )
    return line_item


@router.get("/{submission_id}/receipts", response_model=list[LineItemOut])
async def list_receipts(
    submission_id: str,
    session: AsyncSession = Depends(get_session),
) -> list[LineItem]:
    """List all receipts for a submission."""
    sub = await session.get(Submission, submission_id)
    if not sub:
        raise HTTPException(status_code=404, detail=f"Submission {submission_id} not found")

    result = await session.execute(
        select(LineItem)
        .where(LineItem.submission_id == submission_id)
        .order_by(LineItem.created_at)
    )
    return list(result.scalars().all())
