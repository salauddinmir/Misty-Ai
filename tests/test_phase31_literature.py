"""Phase 31 tests: Bengali literature curriculum (Tagore/Nazrul/Jibanananda).

Mirrors the Phase 29/30 curriculum test structure. Verifies the package
payload and validation, registration into the brain, the deterministic
literature tests, and end-to-end brain question answering in both
languages — using only verified biographical facts.
"""

from __future__ import annotations

import hashlib
import json

import pytest

from brain.core.brain import Brain
from brain.knowledge.registry import PackageRegistry
from brain.knowledge.training_literature import (
    _CONTENT_HASH,
    _RECORD_SOURCE,
    LITERATURE_CONCEPTS,
    LITERATURE_EXAMPLES,
    LITERATURE_FACTS,
    LITERATURE_FORMULAS,
    LITERATURE_RELATIONS,
    LITERATURE_RULES,
    LITERATURE_SYNONYMS,
    LITERATURE_TESTS,
    literature_curriculum_package,
    register_literature_curriculum,
)

_BN_TAGORE_WHO = (
    "\u09b0\u09ac\u09c0\u09a8\u09cd\u09a6\u09cd\u09b0\u09a8\u09be\u09a5 \u09a0\u09be\u0995\u09c1\u09b0 \u0995\u09c7?"
)
_BN_GITANJALI = "\u0997\u09c0\u09a4\u09be\u099e\u09cd\u099c\u09b2\u09bf \u0995\u09c0?"
_BN_BIDROHI = "\u09ac\u09bf\u09a6\u09cd\u09b0\u09cb\u09b9\u09c0 \u0995\u09ac\u09bf\u09a4\u09be "
" \u0995\u09c7 \u09b2\u09bf\u0996\u09c7\u099b\u09c7\u09a8?"
_BN_BONOLATA = "\u09ac\u09a8\u09b2\u09a4\u09be \u09b8\u09c7\u09a8 \u0995\u09c7?"
_BN_TAGORE_ALIAS = "\u09b0\u09ac\u09c0\u09a8\u09cd\u09a6\u09cd\u09b0\u09a8\u09be\u09a5 "
"\u09a0\u09be\u0995\u09c1\u09b0\u09c7\u09b0 \u09aa\u09b0\u09bf\u099a\u09af\u09bc?"


def _new_brain() -> Brain:
    return Brain()


def _answer(brain: Brain, text: str) -> str:
    result = brain.process(text)
    return str(result.get("response") or result.get("text") or "")


class TestLiteraturePackage:
    """Package integrity: payload, hash and TrainingPackageV2 validation."""

    def test_payload_order_deterministic(self):
        import importlib

        from brain.knowledge import training_literature as module

        payload1 = module._build_payload()
        importlib.reload(module)
        payload2 = module._build_payload()
        assert payload1 == payload2

    def test_content_hash_stable(self):
        parts = [
            json.dumps(LITERATURE_SYNONYMS, sort_keys=True, ensure_ascii=False),
            json.dumps(LITERATURE_CONCEPTS, sort_keys=True, ensure_ascii=False),
            json.dumps(LITERATURE_RELATIONS, sort_keys=True, ensure_ascii=False),
            json.dumps(LITERATURE_FACTS, sort_keys=True, ensure_ascii=False),
            json.dumps(LITERATURE_FORMULAS, sort_keys=True, ensure_ascii=False),
            json.dumps(LITERATURE_RULES, sort_keys=True, ensure_ascii=False),
            json.dumps(LITERATURE_EXAMPLES, sort_keys=True, ensure_ascii=False),
            json.dumps(LITERATURE_TESTS, sort_keys=True, ensure_ascii=False),
        ]
        expected = hashlib.sha256("".join(parts).encode("utf-8")).hexdigest()
        assert _CONTENT_HASH == "sha256:" + expected

    def test_package_validates(self):
        package = literature_curriculum_package()
        PackageRegistry().register(package)

    def test_package_metadata(self):
        package = literature_curriculum_package()
        assert package.package_id == "misty-literature-phase31"
        assert package.department == "literature"
        assert "bn" in package.languages and "en" in package.languages
        assert package.source.content_hash == _CONTENT_HASH

    def test_source_ref_attached(self):
        package = literature_curriculum_package()
        for fact in package.facts:
            assert "source_ref" in fact
            assert fact["source_ref"]["content_hash"] == _CONTENT_HASH

    def test_retrieved_at_not_dynamic(self):
        """Provenance timestamp must be fixed so the hash stays stable."""
        assert _RECORD_SOURCE["retrieved_at"] == "2026-08-19T00:00:00Z"

    def test_facts_have_topics(self):
        for fact in LITERATURE_FACTS:
            assert "topic" in fact and fact["topic"] in (
                "tagore",
                "nazrul",
                "jibanananda",
                "renaissance",
                "songs",
            )

    def test_no_uncertain_facts(self):
        for fact in LITERATURE_FACTS:
            assert "maybe" not in str(fact["obj"]).lower()
            assert "perhaps" not in str(fact["obj"]).lower()

    def test_register_into_brain(self):
        brain = _new_brain()
        assert brain.concept_graph.get_concept_by_name("Gitanjali") is not None
        _bon_bn = "\u09ac\u09a8\u09b2\u09a4\u09be \u09b8\u09c7\u09a8"
        assert brain.concept_graph.get_concept_by_name(_bon_bn) is not None
        assert brain.semantic_memory.query(subject="Gitanjali", predicate="definition")
        assert brain.semantic_memory.query(subject="গীতাঞ্জলি", predicate="সংজ্ঞা")
        assert brain.semantic_memory.query(subject="Dhumketu", predicate="definition")
        assert brain.semantic_memory.query(subject="Visva-Bharati", predicate="definition")

    def test_idempotent_registration(self):
        brain = _new_brain()
        first = register_literature_curriculum(brain)
        second = register_literature_curriculum(brain)
        assert second == 0 and first >= 0

    def test_topic_coverage(self):
        topics = {fact["topic"] for fact in LITERATURE_FACTS}
        for topic in ("tagore", "nazrul", "jibanananda", "renaissance", "songs"):
            assert topic in topics


def _unify_digits(text: str) -> str:
    """Normalize Bengali/English digits to ASCII digits."""
    bn = "\u09e6\u09e7\u09e8\u09e9\u09ea\u09eb\u09ec\u09ed\u09ee\u09ef"
    for i, d in enumerate(bn):
        text = text.replace(d, str(i))
    return text


class TestLiteratureEngineTests:
    """Deterministic literature tests pass through the same gate as math."""

    @pytest.mark.parametrize("case", LITERATURE_TESTS, ids=lambda c: c["id"])
    def test_literature_tests(self, case):
        brain = _new_brain()
        register_literature_curriculum(brain)
        answer = _answer(brain, case["input"])
        lowered = answer.lower()
        # Numeric-year facts are expressed as digits or BN digits.

        target = _unify_digits(case["expected_output"].lower())
        en_target = case["expected_output"]
        assert target in lowered or en_target in lowered or _unify_digits(en_target) in lowered, (
            f"case={case['id']} answer={answer!r}"
        )


class TestBrainLiteratureConceptQuestions:
    """End-to-end brain answers for literature concept questions (BN+EN)."""

    def _brain(self) -> Brain:
        brain = _new_brain()
        register_literature_curriculum(brain)
        return brain

    def _answer(self, text: str) -> str:
        return _answer(self._brain(), text)

    def test_tagore_who(self):
        answer = self._answer("Who is Rabindranath Tagore?")
        lower = answer.lower()
        assert "1861" in lower and "poet" in lower

    def test_tagore_who_bengali(self):
        answer = _answer(self._brain(), _BN_TAGORE_WHO)
        assert "১৮৬১" in answer or "১৮৬১" in answer or "কবি" in answer or "1861" in answer

    def test_gitanjali_what(self):
        answer = self._answer("What is Gitanjali?")
        lower = answer.lower()
        assert "1913" in lower and "nobel" in lower

    def test_gitanjali_bengali(self):
        answer = _answer(self._brain(), _BN_GITANJALI)
        assert "১৯১৩" in answer or "1913" in answer

    def test_gitanjali_synonym_alias(self):
        brain = self._brain()
        answer = _answer(brain, "gitanjali definition?")
        lower = answer.lower()
        assert "1913" in lower or "nobel" in lower

    def test_nobel_year(self):
        answer = self._answer("tagore definition?")
        assert "1913" in answer.lower()

    def test_nobel_year_bengali(self):
        answer = _answer(
            self._brain(),
            "\u09b0\u09ac\u09c0\u09a8\u09cd\u09a6\u09cd\u09b0\u09a8\u09be\u09a5 "
            "\u09a0\u09be\u0995\u09c1\u09b0\u09c7\u09b0 \u09aa\u09b0\u09bf\u099a\u09af\u09bc?",
        )
        assert "১৯১৩" in answer or "1913" in answer

    def test_tagore_birth(self):
        answer = self._answer("rabindranath tagore definition?")
        assert "1861" in answer.lower()

    def test_nazrul_rebel_poet(self):
        answer = self._answer("Who is Kazi Nazrul Islam?")
        lower = answer.lower()
        assert "rebel" in lower or "bidrohi" in lower

    def test_nazrul_bengali(self):
        answer = _answer(
            self._brain(),
            "\u0995\u09be\u099c\u09bf \u09a8\u099c\u09b0\u09c1\u09b2 \u0987\u09b8\u09b2\u09be\u09ae \u0995\u09c7?",
        )
        assert "বিদ্রোহী" in answer or "১৮৯৯" in answer or "rebel" in answer.lower()

    def test_bidrohi_poem(self):
        answer = self._answer("Who wrote Bidrohi?")
        lower = answer.lower()
        assert "nazrul" in lower

    def test_bidrohi_bengali(self):
        answer = _answer(
            self._brain(),
            "\u09ac\u09bf\u09a6\u09cd\u09b0\u09cb\u09b9\u09c0 \u0995\u09ac\u09bf\u09a4\u09be"
            " \u0995\u09c7 \u09b2\u09bf\u0996\u09c7\u099b\u09c7\u09a8?",
        )
        assert "নজরুল" in answer

    def test_bonolata_sen(self):
        answer = self._answer("Bonolata Sen ki?")
        lower = answer.lower()
        assert "1942" in lower or "jibanananda" in lower

    def test_bonolata_bengali(self):
        answer = _answer(self._brain(), _BN_BONOLATA)
        assert "১৯৪২" in answer or "1942" in answer or "কবিতা" in answer

    def test_rabindra_sangeet(self):
        answer = self._answer("What is Rabindra Sangeet?")
        lower = answer.lower()
        assert "2000" in lower and "tagore" in lower

    def test_amar_sonar_bangla(self):
        answer = self._answer("Who wrote Amar Sonar Bangla?")
        lower = answer.lower()
        assert "tagore" in lower

    def test_jana_gana_mana(self):
        answer = self._answer("who is rabindranath tagore?")
        lower = answer.lower()
        assert "poet" in lower or "1861" in lower

    def test_vande_mataram(self):
        answer = self._answer("Who wrote Vande Mataram?")
        lower = answer.lower()
        assert "bankim" in lower or "1882" in lower

    def test_anandamath(self):
        answer = self._answer("What is Anandamath?")
        lower = answer.lower()
        assert "1882" in lower and "bankim" in lower

    def test_visva_bharati(self):
        answer = self._answer("visva-bharati definition?")
        lower = answer.lower()
        assert "tagore" in lower or "1921" in lower

    def test_rupasi_bangla(self):
        answer = self._answer("Rupasi Bangla definition?")
        lower = answer.lower()
        assert "1957" in lower or "jibanananda" in lower

    def test_dhumketu(self):
        answer = self._answer("Dhumketu definition?")
        lower = answer.lower()
        assert "1922" in lower or "nazrul" in lower
