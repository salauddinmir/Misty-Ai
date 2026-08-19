"""
Phase 32: bilingual social-cultural curriculum tests.

Validates the Bangladesh/India and world basics training package
(states, festivals, geography) registered by the Brain at init.
All tests are deterministic and run without any LLM.
"""

import unittest
from typing import Any, Dict, List

from brain.core.brain import Brain
from brain.knowledge.training_culture import (
    CULTURE_CONCEPTS,
    CULTURE_FACTS,
    CULTURE_SYNONYMS,
    CULTURE_TESTS,
    culture_curriculum_package,
    register_culture_curriculum,
)


def _unify_digits(text: str) -> str:
    """Normalize Bengali/English digits so tests can assert one form."""
    bn = "০১২৩৪৫৬৭৮৯"
    en = "0123456789"
    table = str.maketrans(bn, en)
    return text.translate(table)


class TestCulturePackage(unittest.TestCase):
    """Structure and content quality of the curriculum package."""

    def test_package_creation(self) -> None:
        package = culture_curriculum_package()
        self.assertEqual(package.package_id, "misty-culture-phase32")
        self.assertEqual(package.department, "culture")
        self.assertEqual(package.languages, ["bn", "en"])
        self.assertTrue(len(package.facts) > 30)
        self.assertTrue(len(package.concepts) > 20)

    def test_topics_covered(self) -> None:
        topics = {f.get("topic") for f in CULTURE_FACTS if f.get("topic")}
        for topic in ("bd_state", "bd_festivals", "bd_geography", "in_state", "in_geography", "world"):
            self.assertIn(topic, topics, f"missing topic {topic}")

    def test_fact_records(self) -> None:
        complete = [f for f in CULTURE_FACTS if f.get("subject") and f.get("predicate") and f.get("obj")]
        self.assertEqual(len(CULTURE_FACTS), len(complete))
        package = culture_curriculum_package()
        for fact in package.facts:
            self.assertIn("source_ref", fact, f"missing source_ref in {fact.get('subject')}")

    def test_concept_records(self) -> None:
        names = [c["name"] for c in CULTURE_CONCEPTS]
        self.assertEqual(len(names), len(set(names)), "duplicate concept names")
        bn_names = [n for n in names if any("\u0980" <= ch <= "\u09ff" for ch in n)]
        self.assertTrue(len(bn_names) >= 10, f"insufficient Bengali concepts: {len(bn_names)}")

    def test_synonym_coverage(self) -> None:
        bn_aliases = {k: v for k, v in CULTURE_SYNONYMS.items() if any("\u0980" <= ch <= "\u09ff" for ch in k)}
        self.assertTrue(len(bn_aliases) >= 10, f"insufficient Bengali aliases: {len(bn_aliases)}")

    def test_test_suite_bilingual(self) -> None:
        ids_: List[str] = [t["id"] for t in CULTURE_TESTS]
        self.assertEqual(len(ids_), len(set(ids_)), "duplicate test ids")
        langs = {t["lang"] for t in CULTURE_TESTS}
        self.assertIn("en", langs)
        self.assertIn("bn", langs)
        self.assertTrue(len(CULTURE_TESTS) >= 20)


class TestCultureBrainConceptQuestions(unittest.TestCase):
    """The Brain answers definition queries from the culture curriculum."""

    def setUp(self) -> None:
        self.brain = Brain()

    def _answer(self, question: str) -> str:
        return self.brain.process(question)["response"]

    def test_topics_still_registered(self) -> None:
        answer = self._answer("dhaka definition?")
        self.assertIn("Dhaka", answer)
        self.assertIn("capital", answer.lower())

    def test_topics_still_registered_bengali(self) -> None:
        answer = self._answer("\u09a2\u09be\u0995\u09be \u0995\u09c0")
        self.assertIn("\u09b0\u09be\u099c\u09a7\u09a8\u09c0", answer)

    def test_india_capital(self) -> None:
        answer = self._answer("new delhi definition?")
        self.assertIn("capital", answer.lower())

    def test_india_capital_bengali(self) -> None:
        answer = self._answer("\u09a8\u09a4\u09c1\u09a8 \u09a6\u09bf\u09b2\u09cd\u09b2\u09c0 \u0995\u09c0")
        self.assertIn("india", answer.lower())

    def test_festival_pahela(self) -> None:
        answer = self._answer("pahela baishakh definition?")
        self.assertIn("baishakh", answer.lower())

    def test_festival_pahela_bengali(self) -> None:
        answer = self._answer("\u09aa\u09b9\u09c7\u09b2\u09be \u09ac\u09c8\u09b6\u09be\u0996")
        self.assertIn("bengali", answer.lower())

    def test_geography_sundarbans(self) -> None:
        answer = self._answer("sundarbans definition?")
        self.assertIn("mangrove", answer.lower())

    def test_world_continents(self) -> None:
        answer = self._answer("continents definition?")
        self.assertIn("continent", answer.lower())

    def test_register_into_brain(self) -> None:
        # A fresh Brain can still be re-registered without errors
        count = register_culture_curriculum(self.brain)
        self.assertIsInstance(count, int)

    def test_concept_graph_entry(self) -> None:
        concept = self.brain.concept_graph.get_concept_by_name("Bangladesh")
        self.assertIsNotNone(concept)


class TestCultureTestSuite(unittest.TestCase):
    """All CULTURE_TESTS pass against a fresh Brain with BN digit parity."""

    def setUp(self) -> None:
        self.brain = Brain()

    def _engine_answer(self, question: str) -> str:
        return self.brain.process(question)["response"]

    def test_no_empty_outputs(self) -> None:
        for t in CULTURE_TESTS:
            self.assertTrue(bool(t["expected_output"]), t["id"])

    def test_engine_test_passes(self) -> None:
        failures: List[Dict[str, Any]] = []
        for t in CULTURE_TESTS:
            answer = self._engine_answer(t["input"])
            answer_flat = _unify_digits(answer).lower()
            expected_flat = _unify_digits(t["expected_output"]).lower()
            if expected_flat not in answer_flat:
                failures.append(
                    {"id": t["id"], "input": t["input"], "expected": t["expected_output"], "answer": answer[:200]}
                )
        if failures:
            detail = "\n".join(f"{f['id']}: expected {f['expected']!r} in {f['answer']!r}" for f in failures[:8])
            self.fail(f"{len(failures)} culture tests failed:\n{detail}")


if __name__ == "__main__":
    unittest.main()
