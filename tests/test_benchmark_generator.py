"""Tests for automated benchmark generation from curriculum manifests."""

import unittest

from brain.evaluation.benchmark_generator import (
    UNIT_CASE_SPECS,
    all_acceptance_cases,
    cases_from_specs,
    curriculum_cases,
    generated_benchmark_cases,
    unit_coverage_map,
)
from brain.evaluation.bilingual import BenchmarkCase, default_bilingual_cases


class BenchmarkGeneratorTest(unittest.TestCase):
    def test_all_departments_have_specs(self):
        expected = (
            "language", "mathematics", "physics", "literature", "reasoning",
            "commonsense", "memory", "perception", "emotion", "self_model",
        )
        for department in expected:
            self.assertIn(department, UNIT_CASE_SPECS)
            self.assertTrue(UNIT_CASE_SPECS[department])

    def test_cases_are_bilingual(self):
        cases = generated_benchmark_cases()
        self.assertTrue(cases)
        for case in cases:
            self.assertIn(case.language, ("bn", "en"))
            self.assertTrue(case.case_id.endswith(f".{case.language}"))

    def test_case_shape_and_defaults(self):
        cases = generated_benchmark_cases()
        for case in cases:
            self.assertIsInstance(case, BenchmarkCase)
            self.assertTrue(case.prompt)
            self.assertTrue(case.expected_fragments)
            self.assertGreaterEqual(case.minimum_confidence, 0.0)
            self.assertLessEqual(case.minimum_confidence, 1.0)

    def test_generation_is_deterministic(self):
        first = tuple(case.case_id for case in generated_benchmark_cases())
        second = tuple(case.case_id for case in generated_benchmark_cases())
        self.assertEqual(first, second)

    def test_no_duplicate_case_ids(self):
        ids = [case.case_id for case in generated_benchmark_cases()]
        self.assertEqual(len(ids), len(set(ids)))

    def test_curriculum_cases_scope(self):
        math_cases = curriculum_cases("mathematics")
        self.assertTrue(math_cases)
        self.assertTrue(all("mathematics" in case.case_id for case in math_cases))
        unknown_cases = curriculum_cases("nonexistent-department")
        self.assertEqual(unknown_cases, [])

    def test_curriculum_cases_language_scope(self):
        en_only = curriculum_cases("mathematics", languages=("en",))
        self.assertTrue(en_only)
        self.assertTrue(all(case.language == "en" for case in en_only))
        self.assertEqual(len(en_only), len(curriculum_cases("mathematics", languages=("bn", "en"))) / 2)

    def test_all_acceptance_cases_includes_defaults(self):
        defaults = default_bilingual_cases()
        suite = all_acceptance_cases()
        default_ids = {case.case_id for case in defaults}
        self.assertTrue(default_ids.issubset({case.case_id for case in suite}))
        self.assertGreater(len(suite), len(defaults))

    def test_coverage_map_matches_specs(self):
        mapping = unit_coverage_map()
        for department, specs in UNIT_CASE_SPECS.items():
            self.assertEqual(mapping[department]["total_specs"], len(specs))
            self.assertEqual(mapping[department]["generated_cases"], len(specs) * 2)

    def test_unit_coverage_lists_units(self):
        mapping = unit_coverage_map()
        math_units = mapping["mathematics"]["units"]
        self.assertIn("arithmetic-and-number-theory", math_units)
        self.assertIn("geometry-and-trigonometry", math_units)

    def test_generated_cases_pass_fragment_convention(self):
        suite = generated_benchmark_cases()
        for case in suite:
            self.assertTrue(all(fragment.strip() for fragment in case.expected_fragments))

    def test_cases_from_specs_empty_specs(self):
        self.assertEqual(cases_from_specs({}), [])


if __name__ == "__main__":
    unittest.main()
