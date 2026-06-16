"""Tests for the receipt ingestion service."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.ingestion import ExtractedReceipt, compute_file_hash, extract_receipt


def test_compute_file_hash_deterministic():
    """Same content always yields same hash."""
    content = b"hello world"
    assert compute_file_hash(content) == compute_file_hash(content)


def test_compute_file_hash_differs():
    """Different content yields different hash."""
    assert compute_file_hash(b"abc") != compute_file_hash(b"def")


@pytest.mark.asyncio
async def test_extract_receipt_unsupported_type():
    """Unsupported file extension raises ValueError."""
    with pytest.raises(ValueError, match="Unsupported file type"):
        await extract_receipt("file.docx", b"content", ".docx")


@pytest.mark.asyncio
async def test_extract_receipt_txt():
    """TXT receipts go through the extraction tool."""
    mock_tool_use = MagicMock()
    mock_tool_use.type = "tool_use"
    mock_tool_use.input = {
        "vendor": "Acme Cafe",
        "date": "2025-04-14",
        "amount": 25.50,
        "line_items": [],
        "category": "Meals",
        "alcohol_present": False,
    }

    mock_response = MagicMock()
    mock_response.content = [mock_tool_use]

    with patch("app.services.ingestion.anthropic.Anthropic") as MockClient:
        instance = MockClient.return_value
        instance.messages.create.return_value = mock_response

        result = await extract_receipt("test.txt", b"Acme Cafe\nTotal: $25.50", ".txt")

    assert result.vendor == "Acme Cafe"
    assert result.amount == 25.50
    assert result.category == "Meals"
    assert result.alcohol_present is False
    assert result.date == date(2025, 4, 14)
