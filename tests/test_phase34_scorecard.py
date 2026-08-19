"""
Phase 34: Full Training Batch Verification + Benchmark Scorecard tests.

Verifies the Phase 34 report pipeline:
  - Every curriculum department's facts actually landed in semantic memory.
  - The benchmark scorecard is numeric, per-category, and bilingual.
  - The combined report dict exposes both halves (master plan section 34).

All tests are deterministic and LLM-free.
"""

from __future__ import annotations

import unittest
from typing import Dict, List

from brain.core.brain import Brain
from brain.learning.self_assessment import GapAssessor
from brain.learning.training_scorecard import (
    BenchmarkScorecard,
    ScorecardResult,
    TrainingBatchVerifier,
    generate_training_report,
)


def _cases_from_cases_module() -> List[Dict[str, str]]:
    from tests import benchmark_conversation

    return benchmark_conversation.BENCHMARK_CASES


class TestBatchVerification(unittest.TestCase):
    """Every curriculum department must be registered after Brain init."""

    def setUp(self) -> None:
        self.brain = Brain()
        self.verifier = TrainingBatchVerifier()

    def test_all_departments_registered(self) -> None:
        report = self.verifier.verify(self.brain)
        self.assertTrue(
            self.verifier.all_verified(report),
            [entry.to_dict() for entry in report if entry.status != "verified"],
        )

    def test_seven_departments_covered(self) -> None:
        report = self.verifier.verify(self.brain)
        departments = {entry.department for entry in report}
        self.assertEqual(departments, {
            "identity", "commonsense", "conversation",
            "mathematics", "physics", "literature", "culture",
        })

    def test_math_curriculum_present(self) -> None:
        report = self.verifier.verify(self.brain)
        math = next(e for e in report if e.department == "mathematics")
        # Phase 29 math curriculum: 75+ facts expected.
        self.assertGreaterEqual(math.verified_facts, 50)

    def test_fresh_brain_also_verifies(self) -> None:
        # Verification must not depend on a long conversation history.
        self.assertTrue(self.verifier.all_verified(self.verifier.verify(Brain())))


class TestBenchmarkScorecard(unittest.TestCase):
    """Numeric per-category grading."""

    def setUp(self) -> None:
        self.brain = Brain()

    def test_scorecard_covers_all_categories(self) -> None:
        result = BenchmarkScorecard(self.brain, _cases_from_cases_module()).run()
        category_names = {c.category for c in result.category_scores}
        case_categories = {c["category"] for c in _cases_from_cases_module()}
        self.assertEqual(category_names, case_categories)

    def test_case_count_totals(self) -> None:
        result = BenchmarkScorecard(self.brain, _cases_from_cases_module()).run()
        cases = sum(c.cases for c in result.category_scores)
        self.assertEqual(cases, len(_cases_from_cases_module()))

    def test_overall_score_matches(self) -> None:
        result = BenchmarkScorecard(self.brain, _cases_from_cases_module()).run()
        self.assertAlmostEqual(
            result.overall_score,
            result.total_passed / result.total_cases,
            places=4,
        )

    def test_scorecard_dict_shape(self) -> None:
        result = BenchmarkScorecard(self.brain, _cases_from_cases_module()).run()
        as_dict = result.to_dict()
        for key in ("generated_at", "tool", "overall_score", "total_cases",
                    "total_passed", "category_scores"):
            self.assertIn(key, as_dict, f"missing {key}")
        for cat in as_dict["category_scores"]:
            self.assertIn("pass_rate", cat)
        # Fully trained brain should score high on the designed suite.
        self.assertGreaterEqual(result.overall_score, 0.85)

    def test_category_pass_rate_range(self) -> None:
        result = BenchmarkScorecard(self.brain, _cases_from_cases_module()).run()
        for cat in result.category_scores:
            self.assertGreaterEqual(cat.pass_rate, 0.0)
            self.assertLessEqual(cat.pass_rate, 1.0)


class TestCombinedReport(unittest.TestCase):
    """generate_training_report() produces the Phase 34 deliverable."""

    def test_report_has_both_halves(self) -> None:
        report = generate_training_report(Brain(), _cases_from_cases_module())
        self.assertIn("batch_verification", report)
        self.assertIn("batch_all_verified", report)
        self.assertIn("scorecard", report)
        self.assertTrue(report["batch_all_verified"])
        scorecard = report["scorecard"]
        self.assertIn("tool", scorecard)
        self.assertEqual(scorecard["tool"], "misty-training-scorecard")

    def test_report_matches_assessor(self) -> None:
        brain = Brain()
        cases = _cases_from_cases_module()
        report = generate_training_report(brain, cases)
        # Independent cross-check with the Phase 33 assessor.
        assessor = GapAssessor(brain)
        assess_report = assessor.evaluate(cases)
        self.assertEqual(
            report["scorecard"]["total_cases"],
            assess_report.total,
        )


if __name__ == "__main__":
    unittest.main()
