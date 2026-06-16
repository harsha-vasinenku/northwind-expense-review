"""Tests for the verdict engine."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.ingestion import ExtractedReceipt
from app.services.verdict import run_verdict


def _make_receipt(**kwargs) -> ExtractedReceipt:
    defaults = {
        "vendor": "Test Vendor",
        "date": date(2025, 4, 14),
        "amount": 50.0,
        "line_items": [],
        "category": "Meals",
        "alcohol_present": False,
        "alcohol_amount": None,
        "guest_count": 1,
        "notes": None,
        "raw_text": "Test receipt",
    }
    defaults.update(kwargs)
    return ExtractedReceipt(**defaults)


@pytest.mark.asyncio
async def test_verdict_uses_tool_use_only():
    """Verdict engine calls submit_expense_verdict tool and parses structured output."""
    mock_tool_use = MagicMock()
    mock_tool_use.type = "tool_use"
    mock_tool_use.input = {
        "verdict": "compliant",
        "category": "Meals",
        "reasoning": "Within policy limits.",
        "cited_clause": "TEP-001 §2.1: expenses must be reasonable",
        "policy_doc_ids": ["TEP-001"],
        "confidence": 0.9,
        "flags": [],
    }
    mock_response = MagicMock()
    mock_response.content = [mock_tool_use]

    mock_rag = MagicMock()
    mock_rag.search = AsyncMock(return_value=[])
    mock_rag.get_indexed_doc_ids.return_value = {"TEP-001"}

    with patch("app.services.verdict.anthropic.Anthropic") as MockClient:
        instance = MockClient.return_value
        instance.messages.create.return_value = mock_response

        result = await run_verdict(
            receipt=_make_receipt(),
            employee_name="Sarah Chen",
            employee_grade=5,
            employee_title="Operations Manager",
            trip_purpose="Client visit",
            trip_start=date(2025, 4, 14),
            trip_end=date(2025, 4, 16),
            rag=mock_rag,
        )

    assert result.verdict == "compliant"
    assert result.confidence == 0.9
    assert result.policy_doc_ids == ["TEP-001"]


@pytest.mark.asyncio
async def test_verdict_returns_needs_review_when_no_tool_called():
    """If Claude fails to call the tool, verdict defaults to needs_review with 0 confidence."""
    mock_response = MagicMock()
    mock_response.content = []

    mock_rag = MagicMock()
    mock_rag.search = AsyncMock(return_value=[])
    mock_rag.get_indexed_doc_ids.return_value = set()

    with patch("app.services.verdict.anthropic.Anthropic") as MockClient:
        instance = MockClient.return_value
        instance.messages.create.return_value = mock_response

        result = await run_verdict(
            receipt=_make_receipt(),
            employee_name="Test User",
            employee_grade=4,
            employee_title="Analyst",
            trip_purpose="Research",
            trip_start=date(2025, 1, 1),
            trip_end=date(2025, 1, 2),
            rag=mock_rag,
        )

    assert result.verdict == "needs_review"
    assert result.confidence == 0.0
