"""
Phase 33: Autonomous Self-Assessment (Knowledge Gap Detection) tests.

Verifies that MISTY can assess its own knowledge: it knows what it knows,
honestly admits what it does not know, and exposes an inspectable gap list
through the state snapshot /api/brain/state (``knowledge_gaps``).

Master plan section 33:
  - 8 of 10 benchmark cases correctly classified known-vs-unknown.
  - Gap list visible in the tick/state metrics API.
All tests are deterministic and run without any LLM.
"""

from __future__ import annotations

import unittest
from typing import Dict, List

from brain.core.brain import Brain
from brain.learning.self_assessment import (
    GapAssessor,
    _expected_present,
    _is_honest_unknown,
    _normalize,
)


def _cases_from_cases_module() -> List[Dict[str, str]]:
    """Import the conversation benchmark cases without executing the
    benchmark runner (the module is import-safe: it only defines data)."""
    from tests import benchmark_conversation

    return benchmark_conversation.BENCHMARK_CASES


class TestAssessorHelpers(unittest.TestCase):
    """Pure helper logic: normalization, honest-unknown detection, matching."""

    def test_normalize_unifies_digits(self) -> None:
        self.assertEqual(_normalize("১২৩ টি শহর"), "123 টি শহর")

    def test_normalize_collapses_whitespace(self) -> None:
        self.assertEqual(_normalize("a   b  c"), "a b c")

    def test_expected_present_single_fragment(self) -> None:
        self.assertTrue(_expected_present("ঢাকা হলো রাজধানী শহর", "ঢাকা"))
        self.assertFalse(_expected_present("চট্টগ্রাম হলো বন্দর", "ঢাকা"))

    def test_expected_present_multi_fragment(self) -> None:
        self.assertTrue(_expected_present("a and b and c", "a||b||c"))
        self.assertFalse(_expected_present("a and b", "a||b||c"))

    def test_honest_unknown_bn(self) -> None:
        self.assertTrue(_is_honest_unknown("আমি এটা জানি না, শেখাও আমাকে।"))
        self.assertFalse(_is_honest_unknown("ঢাকা হলো বাংলাদেশের রাজধানী"))

    def test_honest_unknown_en(self) -> None:
        self.assertTrue(_is_honest_unknown("I do not know the answer yet; could you teach me?"))
        self.assertFalse(_is_honest_unknown("Dhaka is the capital of Bangladesh"))

    def test_honest_unknown_learn_request(self) -> None:
        # Admitting ignorance AND asking to learn counts as self-assessment
        self.assertTrue(_is_honest_unknown("আমি এখনো এটা শিখিনি। আমাকে এটা শেখাও।"))


class TestGapAssessorClassification(unittest.TestCase):
    """The assessor classifies benchmark cases correctly (>=8/10 bar)."""

    def setUp(self) -> None:
        self.brain = Brain()
        self.assessor = GapAssessor(self.brain)

    def _classify_all(self) -> None:
        cases = _cases_from_cases_module()
        self.report = self.assessor.evaluate(cases)

    def test_all_cases_classified(self) -> None:
        cases = _cases_from_cases_module()
        self._classify_all()
        total = (
            self.report.known_count
            + self.report.unknown_honest_count
            + self.report.incorrect_count
            + self.report.missing_count
        )
        self.assertEqual(total, len(cases))

    def test_eight_of_ten_correctly_classified(self) -> None:
        # Master plan bar: 8 of 10 benchmark cases correctly graded.
        cases = _cases_from_cases_module()
        self.assertGreaterEqual(len(cases), 10)
        self._classify_all()
        correct = self.report.known_count + self.report.unknown_honest_count
        # The benchmark suite is designed to be answerable; unknown_honest
        # should be rare on a fully trained brain, so known dominates.
        self.assertGreaterEqual(self.report.known_count, 8)
        self.assertGreaterEqual(correct, 8)

    def test_known_answers_still_returned(self) -> None:
        self._classify_all()
        known_entries = [e for e in self.report.entries if e.status == "known"]
        # Identity knowledge must be known, never classified as missing.
        identity = [e for e in known_entries if e.topic == "identity"]
        self.assertGreaterEqual(len(identity), 2)
        self.assertTrue(all("Misty" in e.answer or "Pixline" in e.answer for e in identity))

    def test_gap_list_only_incorrect_and_missing(self) -> None:
        self._classify_all()
        gaps = self.assessor.gap_dicts()
        # Only incorrect/missing entries may appear in the gap list.
        gap_entry_ids = {e.case_id for e in self.report.entries if e.status in ("incorrect", "missing")}
        gap_ids = {g["case_id"] for g in gaps}
        self.assertSetEqual(gap_ids, gap_entry_ids)
        for entry in self.report.entries:
            if entry.status in ("incorrect", "missing"):
                self.assertIn(entry.case_id, gap_ids)


class TestGapReportStructure(unittest.TestCase):
    """Report dict shape consumed by the state API."""

    def setUp(self) -> None:
        self.brain = Brain()
        self.assessor = GapAssessor(self.brain)

    def test_report_fields(self) -> None:
        cases = _cases_from_cases_module()[:5]
        report = self.assessor.evaluate(cases)
        as_dict = report.to_dict()
        for key in (
            "total_cases",
            "known",
            "unknown_honest",
            "incorrect",
            "missing",
            "self_assessment_score",
            "gaps",
            "honest_unknowns",
        ):
            self.assertIn(key, as_dict, f"missing field {key}")
        self.assertAlmostEqual(
            as_dict["self_assessment_score"],
            report.score,
            places=4,
        )

    def test_score_range(self) -> None:
        report = self.assessor.evaluate(_cases_from_cases_module()[:20])
        self.assertGreaterEqual(report.score, 0.0)
        self.assertLessEqual(report.score, 1.0)

    def test_history_accumulates(self) -> None:
        cases = _cases_from_cases_module()[:3]
        self.assessor.evaluate(cases)
        self.assessor.evaluate(cases)
        self.assertEqual(len(self.assessor.history), 2)
        self.assertIsNotNone(self.assessor.last_report())


class TestQuarantineReview(unittest.TestCase):
    """Earlier web-learning candidates can be re-checked after learning."""

    def setUp(self) -> None:
        self.brain = Brain()
        self.assessor = GapAssessor(self.brain)

    def test_contradiction_resolved_by_later_curriculum(self) -> None:
        # Candidate blocked before because the brain lacked the fact.
        candidate = {
            "subject": "পদ্মা",
            "predicate": "is_a",
            "obj": "বাংলাদেশের সবচেয়ে বড় নদী",
            "confidence": 0.8,
            "observations": 1,
            "source_ref": "web_search",
        }
        reviewed = self.assessor.review_quarantine([candidate])
        # The culture curriculum now teaches Padma facts, so this
        # specific 'is_a' triple no longer contradicts anything.
        decision = reviewed[0]["review_decision"]
        self.assertEqual(decision, "allow")

    def test_genuine_contradiction_stays_quarantined(self) -> None:
        candidate = {
            "subject": "সূর্য",
            "predicate": "is_a",
            "obj": "একটি গ্রহ",  # contradicts the commonsense fact
            "confidence": 0.8,
            "observations": 1,
            "source_ref": "web_search",
        }
        reviewed = self.assessor.review_quarantine([candidate])
        self.assertEqual(reviewed[0]["review_decision"], "stay_quarantined")

    def test_release_passes_safety_gate(self) -> None:
        candidate = {
            "subject": "মহাশূন্যের নতুন তারা X-42",
            "predicate": "is_a",
            "obj": "একটি নেবুলা",
            "confidence": 0.8,
            "observations": 2,
            "source_ref": "web_search",
            "now_contradicts_existing": False,
            "triple": {
                "subject": "মহাশূন্যের নতুন তারা X-42",
                "predicate": "is_a",
                "obj": "একটি নেবুলা",
            },
        }
        released = GapAssessor.release_candidate(self.brain, candidate)
        self.assertEqual(released["decision"], "allow")
        facts = self.brain.semantic_memory.query(subject="মহাশূন্যের নতুন তারা X-42")
        self.assertTrue(len(facts) >= 1)

    def test_release_blocks_contradiction(self) -> None:
        candidate = {
            "triple": {
                "subject": "আকাশ",
                "predicate": "color",
                "obj": "সবুজ",
            },
            "confidence": 0.9,
            "observations": 1,
            "source_ref": "",
            "now_contradicts_existing": True,
        }
        released = GapAssessor.release_candidate(self.brain, candidate)
        # The safety gate must NOT allow a contradicting triple; it returns
        # REJECT (no provenance on contradicted candidates) or QUARANTINE.
        self.assertIn(released["decision"], ("reject", "quarantine"))


class TestBrainStateKnowledgeGaps(unittest.TestCase):
    """Gap list is exposed via the brain state snapshot (API contract)."""

    def setUp(self) -> None:
        self.brain = Brain()

    def test_state_snapshot_has_gaps_key(self) -> None:
        state = self.brain.get_state()
        self.assertIn("knowledge_gaps", state)
        self.assertIsInstance(state["knowledge_gaps"], list)

    def test_gaps_populated_after_evaluation(self) -> None:
        cases = _cases_from_cases_module()
        self.brain.gap_assessor.evaluate(cases)
        state = self.brain.get_state()
        gaps = state["knowledge_gaps"]
        # Every gap entry carries the inspectable fields the API
        # consumer needs.
        for gap in gaps:
            for field in ("case_id", "topic", "query", "expected", "answer", "status", "confidence"):
                self.assertIn(field, gap, f"missing {field}")
        statuses = {g["status"] for g in gaps}
        self.assertTrue(statuses <= {"incorrect", "missing"})


if __name__ == "__main__":
    unittest.main()
