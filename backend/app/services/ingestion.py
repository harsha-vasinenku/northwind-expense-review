"""Receipt ingestion pipeline.

Accepts PDF / image / .txt files, extracts structured data via Claude.
"""

import base64
import hashlib
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import anthropic
import pdfplumber
import structlog

from app.config import get_settings
from app.constants import SUPPORTED_EXTENSIONS

logger = structlog.get_logger(__name__)


@dataclass
class ExtractedReceipt:
    """Structured data extracted from a receipt file."""

    vendor: str
    date: date
    amount: float
    line_items: list[dict[str, object]]
    category: str
    alcohol_present: bool
    alcohol_amount: float | None
    guest_count: int | None
    notes: str | None
    raw_text: str


def compute_file_hash(content: bytes) -> str:
    """Return SHA-256 hex digest for deduplication."""
    return hashlib.sha256(content).hexdigest()


def _extract_text_from_pdf(content: bytes) -> str:
    """Extract text from a PDF. Returns empty string if extraction fails."""
    import io

    with pdfplumber.open(io.BytesIO(content)) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def _extract_text_via_vision(content: bytes, mime_type: str) -> str:
    """Use Claude vision to OCR an image receipt."""
    settings = get_settings()
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    b64 = base64.standard_b64encode(content).decode()

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": mime_type,
                            "data": b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": "Extract all text from this receipt image. Return verbatim.",
                    },
                ],
            }
        ],
    )
    return response.content[0].text if response.content else ""


EXTRACT_TOOL = {
    "name": "extract_receipt_data",
    "description": "Extract structured data from receipt text.",
    "input_schema": {
        "type": "object",
        "properties": {
            "vendor": {"type": "string", "description": "Merchant name"},
            "date": {"type": "string", "description": "Transaction date in ISO format (YYYY-MM-DD)"},
            "amount": {
                "type": "number",
                "description": "Total amount charged (not subtotal, include tax/tip)",
            },
            "line_items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "description": {"type": "string"},
                        "amount": {"type": "number"},
                    },
                },
                "description": "Individual items on the receipt",
            },
            "category": {
                "type": "string",
                "enum": ["Meals", "Travel-Air", "Travel-Ground", "Lodging", "Conference", "Other"],
                "description": "Expense category",
            },
            "alcohol_present": {
                "type": "boolean",
                "description": "Whether any alcohol was purchased",
            },
            "alcohol_amount": {
                "type": "number",
                "description": "Total alcohol charges (null if none)",
            },
            "guest_count": {
                "type": "integer",
                "description": "Number of people covered by this receipt (null if unclear)",
            },
            "notes": {
                "type": "string",
                "description": "Any anomalies or notable items the model noticed",
            },
        },
        "required": ["vendor", "date", "amount", "category", "alcohol_present", "line_items"],
    },
}


def _parse_date(date_str: str) -> date:
    """Parse ISO date string, returning today on failure."""
    from datetime import date as dt_date

    try:
        return dt_date.fromisoformat(date_str[:10])
    except (ValueError, TypeError):
        return dt_date.today()


async def extract_receipt(
    filename: str,
    content: bytes,
    suffix: str,
) -> ExtractedReceipt:
    """Extract structured data from a receipt file.

    Raises ValueError for unsupported file types.
    """
    suffix = suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {suffix}")

    settings = get_settings()
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    if suffix == ".txt":
        raw_text = content.decode("utf-8", errors="replace")
    elif suffix == ".pdf":
        raw_text = _extract_text_from_pdf(content)
        if len(raw_text.strip()) < 50:
            logger.info("PDF text extraction sparse, falling back to vision", filename=filename)
            raw_text = _extract_text_via_vision(content, "application/pdf")
    elif suffix in {".jpg", ".jpeg"}:
        raw_text = _extract_text_via_vision(content, "image/jpeg")
    elif suffix == ".png":
        raw_text = _extract_text_via_vision(content, "image/png")
    else:
        raise ValueError(f"Unsupported file type: {suffix}")

    logger.debug("Raw text extracted", filename=filename, chars=len(raw_text))

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        tools=[EXTRACT_TOOL],  # type: ignore[list-item]
        tool_choice={"type": "tool", "name": "extract_receipt_data"},
        messages=[
            {
                "role": "user",
                "content": (
                    f"Extract structured data from this receipt.\n\n"
                    f"RECEIPT TEXT:\n{raw_text}\n\n"
                    "Call extract_receipt_data with the extracted fields."
                ),
            }
        ],
    )

    tool_use = next(
        (block for block in response.content if block.type == "tool_use"),
        None,
    )
    if not tool_use:
        raise RuntimeError(f"Claude did not call extract_receipt_data for {filename}")

    inp = tool_use.input  # type: ignore[attr-defined]

    return ExtractedReceipt(
        vendor=inp.get("vendor", "Unknown"),
        date=_parse_date(inp.get("date", "")),
        amount=float(inp.get("amount", 0.0)),
        line_items=inp.get("line_items", []),
        category=inp.get("category", "Other"),
        alcohol_present=bool(inp.get("alcohol_present", False)),
        alcohol_amount=inp.get("alcohol_amount"),
        guest_count=inp.get("guest_count"),
        notes=inp.get("notes"),
        raw_text=raw_text,
    )
