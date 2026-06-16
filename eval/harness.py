"""Northwind Expense Review — Eval Harness.

Usage:
    python eval/harness.py --fixture eval/fixtures/expected_outcomes_sample.json
    python eval/harness.py --fixture eval/fixtures/expected_outcomes_sample.json --base-url http://localhost:8000
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from eval.metrics import EvalMetrics

SUBMISSIONS_DIR = Path(__file__).parent.parent / "backend" / "data" / "submissions"

EMPLOYEE_MAP = {
    "01_clean_denver": "NW-04821",
    "02_clean_boston_conf": "NW-02719",
    "03_dinner_over_cap": "NW-05117",
    "04_alcohol_solo_travel": "NW-03488",
    "05_receipt_mismatch": "NW-04102",
}

TRIP_MAP = {
    "01_clean_denver": ("Quarterly client review", "2025-04-14", "2025-04-16"),
    "02_clean_boston_conf": ("AWS re:Inforce conference", "2025-06-09", "2025-06-12"),
    "03_dinner_over_cap": ("Vendor site visit Chicago", "2025-05-06", "2025-05-07"),
    "04_alcohol_solo_travel": ("Solo carrier research Austin", "2025-03-18", "2025-03-20"),
    "05_receipt_mismatch": ("PNW client QBR Seattle", "2025-02-11", "2025-02-13"),
}


async def run_verdict_test(
    client: httpx.AsyncClient,
    base_url: str,
    test_case: dict,
    metrics: EvalMetrics,
) -> None:
    """Run a single verdict test case against the live API."""
    folder = test_case["submission_folder"]
    filename = test_case["receipt_filename"]
    expected = test_case["expected"]
    test_id = test_case["id"]

    receipt_path = SUBMISSIONS_DIR / folder / "receipts" / filename
    if not receipt_path.exists():
        print(f"  SKIP {test_id}: file not found: {receipt_path}")
        return

    employee_id = EMPLOYEE_MAP.get(folder)
    trip_info = TRIP_MAP.get(folder)
    if not employee_id or not trip_info:
        print(f"  SKIP {test_id}: no mapping for folder {folder}")
        return

    purpose, start, end = trip_info
    sub_resp = await client.post(
        f"{base_url}/api/submissions",
        json={
            "employee_id": employee_id,
            "trip_purpose": purpose,
            "trip_start": start,
            "trip_end": end,
        },
    )
    if sub_resp.status_code not in (200, 201):
        print(f"  FAIL {test_id}: submission creation failed: {sub_resp.text[:200]}")
        return

    sub_id = sub_resp.json()["id"]

    with open(receipt_path, "rb") as f:
        content = f.read()

    upload_resp = await client.post(
        f"{base_url}/api/submissions/{sub_id}/receipts",
        files={"file": (filename, content, "application/octet-stream")},
        timeout=60.0,
    )

    if upload_resp.status_code not in (200, 201):
        print(f"  FAIL {test_id}: upload failed: {upload_resp.text[:200]}")
        return

    result = upload_resp.json()
    actual_verdict = result.get("verdict", "")
    actual_flags = result.get("flags", [])
    actual_cited = result.get("cited_clause", "")
    actual_doc_ids = result.get("policy_doc_ids", [])
    confidence = result.get("confidence", 0.0)

    metrics.record_verdict(
        test_id=test_id,
        expected=expected,
        actual_verdict=actual_verdict,
        actual_flags=actual_flags,
        actual_cited=actual_cited,
        actual_doc_ids=actual_doc_ids,
        confidence=confidence,
    )

    verdict_ok = actual_verdict == expected.get("verdict", "")
    status = "PASS" if verdict_ok else "FAIL"
    print(
        f"  {status} {test_id}: expected={expected.get('verdict')} "
        f"actual={actual_verdict} conf={confidence:.2f} flags={actual_flags}"
    )


async def run_qa_test(
    client: httpx.AsyncClient,
    base_url: str,
    test_case: dict,
    metrics: EvalMetrics,
) -> None:
    """Run a policy Q&A test case (refusal or answer quality)."""
    test_id = test_case["id"]
    question = test_case["question"]
    expected = test_case["expected"]

    resp = await client.post(
        f"{base_url}/api/policy/ask",
        json={"question": question, "conversation_history": []},
        timeout=30.0,
    )

    if resp.status_code != 200:
        print(f"  FAIL {test_id}: Q&A request failed: {resp.status_code}")
        return

    data = resp.json()
    actually_refused = data.get("refused", False)
    answer = data.get("answer", "")
    citations = data.get("citations", [])

    if test_case.get("type") == "policy_qa_refusal":
        should_refuse = expected.get("should_refuse", True)
        metrics.record_refusal(test_id, should_refuse, actually_refused)
        status = "PASS" if (should_refuse == actually_refused) else "FAIL"
        print(f"  {status} {test_id}: refusal expected={should_refuse} actual={actually_refused}")
    else:
        metrics.record_qa_answer(test_id, expected, answer, citations)
        status = "PASS"
        print(f"  PASS {test_id}: Q&A answer received, citations={len(citations)}")


async def main(fixture_path: str, base_url: str) -> None:
    """Run the eval harness against a fixture file."""
    fixture = json.loads(Path(fixture_path).read_text())
    test_cases = fixture.get("test_cases", [])
    metrics = EvalMetrics()

    print(f"\nRunning {len(test_cases)} test cases against {base_url}…\n")

    async with httpx.AsyncClient() as client:
        health = await client.get(f"{base_url}/health", timeout=10.0)
        if health.status_code != 200:
            print(f"ERROR: Server not healthy: {health.status_code}")
            sys.exit(1)
        print(f"Server healthy: {health.json()}\n")

        for tc in test_cases:
            tc_type = tc.get("type", "verdict")
            if tc_type == "verdict":
                await run_verdict_test(client, base_url, tc, metrics)
            elif tc_type in ("policy_qa_refusal", "policy_qa_answer"):
                await run_qa_test(client, base_url, tc, metrics)
            else:
                print(f"  SKIP {tc['id']}: unknown type {tc_type}")

    metrics.print_report()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Northwind Eval Harness")
    parser.add_argument(
        "--fixture",
        default="eval/fixtures/expected_outcomes_sample.json",
        help="Path to fixture JSON file",
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL of the running API",
    )
    args = parser.parse_args()
    asyncio.run(main(args.fixture, args.base_url))
