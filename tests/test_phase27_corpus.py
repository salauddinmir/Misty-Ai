"""Phase 27 tests: conversation corpus training package.

Verifies the TrainingPackageV2 validates, registers in the package
registry, and that a live Brain loads the corpus' social-norm facts and
dialogue-act concepts. Live behavior checks reuse the benchmark cases
embedded in the corpus so the Phase 28 benchmark runner can share them.
"""

from __future__ import annotations

import pytest

from brain.core.brain import Brain
from brain.knowledge.corpus_conversation import (
    CONVERSATION_BENCHMARK,
    CONVERSATION_EXAMPLES,
    CONVERSATION_FACTS,
    conversation_corpus,
)
from brain.knowledge.registry import PackageRegistry, validate_package


@pytest.fixture()
def brain():
    return Brain()


@pytest.fixture()
def registry():
    return PackageRegistry()


# ---------------------------------------------------------------------------
# Package validation and registration
# ---------------------------------------------------------------------------


def test_corpus_validates():
    package = conversation_corpus()
    assert validate_package(package) is package


def test_corpus_registers():
    registry = PackageRegistry()
    package = registry.register(conversation_corpus())
    assert registry.get("conversation_corpus") is package


def test_corpus_identity():
    package = conversation_corpus()
    assert package.package_id == "conversation_corpus"
    assert package.department == "conversation"
    assert package.version == "1.0.0"
    assert set(package.languages) == {"bn", "en"}
    assert package.source.content_hash.startswith("sha256:")


def test_corpus_record_depths():
    package = conversation_corpus()
    assert len(package.concepts) >= 9, package.concepts
    assert len(package.relations) >= 8, package.relations
    assert len(package.facts) >= 40, package.facts
    assert len(package.rules) >= 8, package.rules
    assert len(package.examples) >= 8, package.examples
    assert len(package.tests) >= 8, package.tests


def test_corpus_fact_confidence_bounds():
    for fact in CONVERSATION_FACTS:
        confidence = fact.get("confidence")
        if confidence is not None:
            assert 0.0 <= confidence <= 1.0, fact


def test_corpus_bilingual_coverage():
    langs = {fact.get("lang") for fact in CONVERSATION_FACTS}
    assert "bn" in langs and "en" in langs, langs


def test_corpus_joke_examples_safe():
    """No example output contains mockery or personal insults."""
    forbidden = {"বোকা", "মূর্খ", "stupid", "idiot", "ugly"}
    for example in CONVERSATION_EXAMPLES:
        output = example["output"].lower()
        assert not any(word in output for word in forbidden), example


def test_corpus_tests_have_required_fields():
    for test in CONVERSATION_BENCHMARK:
        assert all(key in test for key in ("id", "input", "expected_output")), test
    ids = [test["id"] for test in CONVERSATION_BENCHMARK]
    assert len(ids) == len(set(ids))


# ---------------------------------------------------------------------------
# Live loading into the brain
# ---------------------------------------------------------------------------


def test_brain_loads_corpus_facts(brain):
    facts = brain.semantic_memory.query(subject="গ্রিটিং", predicate="norm")
    assert len(facts) >= 1, facts
    facts_en = brain.semantic_memory.query(subject="greeting", predicate="norm")
    assert len(facts_en) >= 1, facts_en


def test_brain_loads_corpus_concepts(brain):
    concept = brain.concept_graph.get_concept_by_name("empathy")
    assert concept is not None


def test_brain_can_query_social_norm(brain):
    facts = brain.semantic_memory.query(subject="closure", predicate="norm")
    subjects = {fact.subject for fact in facts}
    assert "closure" in subjects, facts


# ---------------------------------------------------------------------------
# Live benchmark cases from the corpus
# ---------------------------------------------------------------------------


def _run_corpus_case(brain: Brain, case: dict) -> str:
    """Multi-turn cases use '||' to separate turns; return last response."""
    turns = case["input"].split("||")
    last = ""
    for turn in turns:
        last = brain.process(turn)["response"]
    return last


def test_benchmark_greeting_bn(brain):
    case = next(case for case in CONVERSATION_BENCHMARK if case["id"] == "conv_bn_greeting")
    response = _run_corpus_case(brain, case)
    assert case["expected_output"] in response, response


def test_benchmark_empathy_bn(brain):
    case = next(case for case in CONVERSATION_BENCHMARK if case["id"] == "conv_bn_empathy")
    response = _run_corpus_case(brain, case)
    assert case["expected_output"] in response, response


def test_benchmark_knowledge_answer(brain):
    case = next(case for case in CONVERSATION_BENCHMARK if case["id"] == "conv_bn_knowledge_answer")
    response = _run_corpus_case(brain, case)
    assert case["expected_output"] in response, response


def test_benchmark_closure_no_question(brain):
    case = next(case for case in CONVERSATION_BENCHMARK if case["id"] == "conv_bn_closure_no_question")
    response = _run_corpus_case(brain, case)
    assert case["expected_output"] in response, response
    assert "?" not in response, response


def test_benchmark_no_duplicate_replies(brain):
    """Two identical greetings must both yield a valid Misty greeting with
    the brain's identity, and the second reply must not be a byte-for-byte
    repeat of the first (Phase 24 personality variation)."""
    case = next(case for case in CONVERSATION_BENCHMARK if case["id"] == "conv_bn_no_duplicate_replies")
    turns = case["input"].split("||")
    replies: list[str] = []
    for turn in turns:
        result = brain.process(turn)
        replies.append(result["response"])
    for reply in replies:
        assert "Misty" in reply, reply
    assert replies[0] != replies[1], (replies[0], replies[1])
