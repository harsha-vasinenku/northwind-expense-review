"""Verdict engine — reviews an extracted receipt against policy and returns a structured verdict.

Uses Claude tool use exclusively; never parses free-text verdict responses.
"""

import json
from dataclasses import dataclass
from datetime import date

import anthropic
import structlog

from app.config import get_settings
from app.constants import ALL_TE_POLICY_IDS, Verdict
from app.services.ingestion import ExtractedReceipt
from app.services.rag import PolicyChunk, RAGService

logger = structlog.get_logger(__name__)

VERDICT_TOOL: dict[str, object] = {
    "name": "submit_expense_verdict",
    "description": "Submit a structured verdict for an expense line item after policy analysis.",
    "input_schema": {
        "type": "object",
        "properties": {
            "verdict": {
                "type": "string",
                "enum": ["compliant", "flagged", "needs_review"],
                "description": (
                    "compliant = clearly within policy; "
                    "flagged = clear policy violation with specific clause; "
                    "needs_review = ambiguous, missing policy, or borderline case"
                ),
            },
            "category": {"type": "string"},
            "reasoning": {
                "type": "string",
                "description": "2-4 sentences explaining the verdict. Reference specific facts from the receipt.",
            },
            "cited_clause": {
                "type": "string",
                "description": (
                    "The exact quoted text from the policy that supports this verdict. "
                    "Format: 'DOC-ID §X.Y: [verbatim quote]'. "
                    "If no applicable policy found, write: 'No applicable policy found in provided documents.'"
                ),
            },
            "policy_doc_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of policy document IDs referenced (e.g. ['TEP-002', 'TEP-001'])",
            },
            "confidence": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": (
                    "0.9+ = controlling policy present and clear; "
                    "0.6-0.9 = policy present but ambiguous; "
                    "below 0.6 = policy absent or retrieval uncertain"
                ),
            },
            "flags": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Specific issues: ['alcohol_on_solo_trip', 'over_meal_cap', "
                    "'booked_outside_concur', 'premium_class_upgrade']"
                ),
            },
        },
        "required": ["verdict", "category", "reasoning", "cited_clause", "policy_doc_ids", "confidence"],
    },
}


@dataclass
class VerdictResult:
    """Structured verdict from the Claude compliance engine."""

    verdict: str
    category: str
    reasoning: str
    cited_clause: str
    policy_doc_ids: list[str]
    confidence: float
    flags: list[str]


def _build_system_prompt() -> str:
    return (
        "You are a finance compliance assistant for Northwind Logistics.\n"
        "Your job is to review expense receipts against company policy and return a structured verdict.\n"
        "Rules:\n"
        "- Only cite policies that are in the POLICY CLAUSES section below.\n"
        "- If the controlling policy is not present, set verdict to 'needs_review' and confidence below 0.6.\n"
        "- Never invent a dollar cap or rule that is not explicitly stated in the provided clauses.\n"
        "- Always call the submit_expense_verdict tool — do not respond in prose."
    )


def _build_user_prompt(
    receipt: ExtractedReceipt,
    employee_name: str,
    employee_grade: int,
    employee_title: str,
    trip_purpose: str,
    trip_start: date,
    trip_end: date,
    chunks: list[PolicyChunk],
    missing_policies: list[str],
) -> str:
    retrieved_text = "\n\n".join(
        f"[{c.doc_id} {c.section_id} — {c.section_title}]\n{c.text}" for c in chunks
    )
    missing_text = "\n".join(f"- {p}" for p in missing_policies) if missing_policies else "None"

    is_solo = (receipt.guest_count or 1) <= 1

    return (
        f"EMPLOYEE CONTEXT:\n"
        f"  Name: {employee_name}\n"
        f"  Grade: {employee_grade} ({employee_title})\n"
        f"  Trip purpose: {trip_purpose}\n"
        f"  Trip dates: {trip_start} to {trip_end}\n\n"
        f"RECEIPT:\n"
        f"  Vendor: {receipt.vendor}\n"
        f"  Date: {receipt.date}\n"
        f"  Amount: ${receipt.amount:.2f}\n"
        f"  Category: {receipt.category}\n"
        f"  Alcohol present: {receipt.alcohol_present}"
        + (f" (${receipt.alcohol_amount:.2f})" if receipt.alcohol_amount else "")
        + f"\n"
        f"  Solo traveler: {is_solo}\n"
        f"  Guest count on receipt: {receipt.guest_count}\n"
        f"  Line items: {json.dumps(receipt.line_items)}\n"
        f"  Notes from extraction: {receipt.notes or 'None'}\n\n"
        f"POLICY CLAUSES (retrieved — only these are authoritative):\n{retrieved_text}\n\n"
        f"MISSING POLICIES (not available in provided documents):\n{missing_text}\n\n"
        "Analyze this receipt and call submit_expense_verdict with your verdict."
    )


async def run_verdict(
    receipt: ExtractedReceipt,
    employee_name: str,
    employee_grade: int,
    employee_title: str,
    trip_purpose: str,
    trip_start: date,
    trip_end: date,
    rag: RAGService,
) -> VerdictResult:
    """Run the full verdict pipeline for a single receipt.

    Retrieves relevant policy chunks, builds the prompt, calls Claude with tool use.
    """
    query = f"{receipt.category} expense {receipt.vendor} ${receipt.amount}"
    chunks = await rag.search(query=query, category=receipt.category, n_results=5)

    indexed_ids = rag.get_indexed_doc_ids()
    missing = [
        f"{doc_id} ({title})"
        for doc_id, title in ALL_TE_POLICY_IDS.items()
        if doc_id not in indexed_ids
    ]

    settings = get_settings()
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=_build_system_prompt(),
        tools=[VERDICT_TOOL],  # type: ignore[list-item]
        tool_choice={"type": "tool", "name": "submit_expense_verdict"},
        messages=[
            {
                "role": "user",
                "content": _build_user_prompt(
                    receipt=receipt,
                    employee_name=employee_name,
                    employee_grade=employee_grade,
                    employee_title=employee_title,
                    trip_purpose=trip_purpose,
                    trip_start=trip_start,
                    trip_end=trip_end,
                    chunks=chunks,
                    missing_policies=missing,
                ),
            }
        ],
    )

    tool_use = next(
        (block for block in response.content if block.type == "tool_use"),
        None,
    )
    if not tool_use:
        logger.error("Verdict tool not called", vendor=receipt.vendor, amount=receipt.amount)
        return VerdictResult(
            verdict=Verdict.NEEDS_REVIEW,
            category=receipt.category,
            reasoning="Verdict engine did not return a structured response.",
            cited_clause="No applicable policy found in provided documents.",
            policy_doc_ids=[],
            confidence=0.0,
            flags=[],
        )

    inp = tool_use.input  # type: ignore[attr-defined]

    logger.info(
        "Verdict issued",
        vendor=receipt.vendor,
        amount=receipt.amount,
        verdict=inp.get("verdict"),
        confidence=inp.get("confidence"),
    )

    return VerdictResult(
        verdict=inp.get("verdict", Verdict.NEEDS_REVIEW),
        category=inp.get("category", receipt.category),
        reasoning=inp.get("reasoning", ""),
        cited_clause=inp.get("cited_clause", "No applicable policy found in provided documents."),
        policy_doc_ids=inp.get("policy_doc_ids", []),
        confidence=float(inp.get("confidence", 0.0)),
        flags=inp.get("flags", []),
    )
