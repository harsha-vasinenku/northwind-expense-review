"""Scoring functions for the eval harness."""

from dataclasses import dataclass, field


@dataclass
class VerdictResult:
    """Holds evaluation result for a single test case."""

    test_id: str
    passed: bool
    details: str
    expected_verdict: str = ""
    actual_verdict: str = ""
    confidence: float = 0.0


@dataclass
class EvalMetrics:
    """Aggregated metrics across all test cases."""

    total: int = 0
    verdict_correct: int = 0
    verdict_total: int = 0
    correctly_flagged: int = 0
    flagged_total: int = 0
    correctly_compliant: int = 0
    compliant_total: int = 0
    correctly_needs_review: int = 0
    needs_review_total: int = 0
    citation_matches: int = 0
    citation_total: int = 0
    refusals_correct: int = 0
    refusal_total: int = 0
    qa_answers_correct: int = 0
    qa_answer_total: int = 0
    high_conf_correct: int = 0
    high_conf_total: int = 0
    low_conf_correct: int = 0
    low_conf_total: int = 0
    failures: list[str] = field(default_factory=list)

    def record_verdict(
        self,
        test_id: str,
        expected: dict,
        actual_verdict: str,
        actual_flags: list[str],
        actual_cited: str,
        actual_doc_ids: list[str],
        confidence: float,
    ) -> None:
        """Record a verdict test case result."""
        self.verdict_total += 1
        expected_verdict = expected.get("verdict", "")

        if expected_verdict == "flagged":
            self.flagged_total += 1
        elif expected_verdict == "compliant":
            self.compliant_total += 1
        elif expected_verdict == "needs_review":
            self.needs_review_total += 1

        verdict_ok = actual_verdict == expected_verdict
        if verdict_ok:
            self.verdict_correct += 1
            if expected_verdict == "flagged":
                self.correctly_flagged += 1
            elif expected_verdict == "compliant":
                self.correctly_compliant += 1
            elif expected_verdict == "needs_review":
                self.correctly_needs_review += 1

        flags_ok = True
        for flag in expected.get("flags_should_include", []):
            if flag not in actual_flags:
                flags_ok = False
                self.failures.append(f"{test_id}: missing flag '{flag}' (got {actual_flags})")

        cited_check = expected.get("cited_clause_should_contain", "")
        if cited_check:
            self.citation_total += 1
            if cited_check.lower() in actual_cited.lower():
                self.citation_matches += 1
            else:
                self.failures.append(
                    f"{test_id}: cited_clause missing '{cited_check}' (got: {actual_cited[:80]})"
                )

        conf_min = expected.get("confidence_min", 0.0)
        if confidence >= conf_min:
            pass
        else:
            self.failures.append(
                f"{test_id}: confidence {confidence:.2f} < min {conf_min}"
            )

        if confidence >= 0.8:
            self.high_conf_total += 1
            if verdict_ok:
                self.high_conf_correct += 1
        elif confidence < 0.6:
            self.low_conf_total += 1
            if verdict_ok or actual_verdict == "needs_review":
                self.low_conf_correct += 1

    def record_refusal(
        self, test_id: str, expected_refuse: bool, actually_refused: bool
    ) -> None:
        """Record a policy Q&A refusal test case."""
        self.refusal_total += 1
        if expected_refuse == actually_refused:
            self.refusals_correct += 1
        else:
            self.failures.append(
                f"{test_id}: expected refused={expected_refuse}, got refused={actually_refused}"
            )

    def record_qa_answer(
        self, test_id: str, expected: dict, answer: str, citations: list[dict]
    ) -> None:
        """Record a Q&A answer quality check."""
        self.qa_answer_total += 1
        checks_ok = True
        should_contain = expected.get("answer_should_contain", "")
        if should_contain and should_contain.lower() not in answer.lower():
            checks_ok = False
            self.failures.append(
                f"{test_id}: answer missing '{should_contain}' (got: {answer[:80]})"
            )

        doc_req = expected.get("should_cite_doc", "")
        if doc_req:
            cited_docs = [c.get("doc_id", "") for c in citations]
            if doc_req not in cited_docs:
                checks_ok = False
                self.failures.append(
                    f"{test_id}: missing citation {doc_req} (got: {cited_docs})"
                )

        if checks_ok:
            self.qa_answers_correct += 1

    def pct(self, num: int, denom: int) -> str:
        if denom == 0:
            return "N/A"
        return f"{num}/{denom}  ({100 * num / denom:.1f}%)"

    def print_report(self) -> None:
        """Print a formatted metrics report."""
        print("\n" + "=" * 50)
        print("  Northwind Eval Harness Results")
        print("=" * 50)

        print(f"\nVerdict Accuracy        {self.pct(self.verdict_correct, self.verdict_total)}")
        print(f"  - Correctly flagged:   {self.pct(self.correctly_flagged, self.flagged_total)}")
        print(f"  - Correctly compliant: {self.pct(self.correctly_compliant, self.compliant_total)}")
        print(f"  - Needs review:        {self.pct(self.correctly_needs_review, self.needs_review_total)}")

        print(f"\nCitation Faithfulness   {self.pct(self.citation_matches, self.citation_total)}")
        print(f"\nRefusal Rate (OOS)      {self.pct(self.refusals_correct, self.refusal_total)}")
        print(f"\nQ&A Answer Quality      {self.pct(self.qa_answers_correct, self.qa_answer_total)}")

        print(f"\nConfidence Calibration")
        print(f"  - High conf (>=0.8) accuracy: {self.pct(self.high_conf_correct, self.high_conf_total)}")
        print(f"  - Low conf (<0.6) correct/acceptable: {self.pct(self.low_conf_correct, self.low_conf_total)}")

        all_scored = (
            self.verdict_correct
            + self.citation_matches
            + self.refusals_correct
            + self.qa_answers_correct
        )
        all_total = (
            self.verdict_total
            + self.citation_total
            + self.refusal_total
            + self.qa_answer_total
        )
        if all_total > 0:
            overall = 100 * all_scored / all_total
            print(f"\nOverall Score: {overall:.1f}%")

        if self.failures:
            print(f"\nFailures ({len(self.failures)}):")
            for f in self.failures:
                print(f"  ✗ {f}")

        print("=" * 50 + "\n")
