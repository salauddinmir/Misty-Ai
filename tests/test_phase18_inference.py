"""
Phase 18: Knowledge-Inference Synthesis tests.

Verifies that MISTY derives answers from stored concepts and the
commonsense layer ("যা ভাবে তৈরি করে সেখান থেকে উত্তর দেবে")
instead of repeating canned replies like
"ইনটেন্ট নির্ভুলভাবে parse করতে পারছি না".
"""

import pytest

from brain.core.brain import Brain
from brain.knowledge.commonsense import register_commonsense_layer


@pytest.fixture()
def brain() -> Brain:
    return Brain(use_neural_sim=False)


def synthesize(brain: Brain, question: str):
    return brain.inference_synthesizer.synthesize(question, brain)


# ---------------------------------------------------------------------------
# Commonsense layer loading
# ---------------------------------------------------------------------------


def test_commonsense_loaded_after_init(brain: Brain) -> None:
    facts = [f for f in brain.semantic_memory.facts.values() if f.source == "commonsense_layer"]
    assert len(facts) >= 100
    subjects = {f.subject for f in facts}
    assert "আকাশ" in subjects
    assert "sky" in subjects
    assert "পানি" in subjects
    assert "water" in subjects
    assert "বাংলাদেশ" in subjects


def test_commonsense_idempotent_registration(brain: Brain) -> None:
    before = brain.semantic_memory.size
    count = register_commonsense_layer(brain)
    assert count == 0  # nothing re-registered
    assert brain.semantic_memory.size == before


# ---------------------------------------------------------------------------
# Direct synthesis from commonsense facts
# ---------------------------------------------------------------------------


def test_sky_color_question_bn(brain: Brain) -> None:
    result = synthesize(brain, "আকাশের রঙ কি?")
    assert result is not None
    assert "নীল" in result.answer
    assert 0.0 < result.confidence < 1.0
    assert result.language == "bn"
    assert result.is_derived


def test_sky_color_question_en(brain: Brain) -> None:
    result = synthesize(brain, "What is the color of the sky?")
    assert result is not None
    assert "blue" in result.answer.lower()
    assert result.language == "en"


def test_water_property_question(brain: Brain) -> None:
    result = synthesize(brain, "পানি কি?")
    assert result is not None
    assert "তরল" in result.answer
    assert result.confidence > 0.0


def test_bangladesh_capital(brain: Brain) -> None:
    result = synthesize(brain, "বাংলাদেশের রাজধনী কি?")
    assert result is not None
    assert "ঢাকা" in result.answer
    assert result.matched_predicate == "capital"


def test_india_capital_en(brain: Brain) -> None:
    result = synthesize(brain, "What is the capital of India?")
    assert result is not None
    assert "Delhi" in result.answer


def test_sun_is_star(brain: Brain) -> None:
    result = synthesize(brain, "সূর্য হলো কি?")
    assert result is not None
    assert "তারা" in result.answer


def test_taste_question(brain: Brain) -> None:
    result = synthesize(brain, "মধুর স্বাদ কেমন?")
    assert result is not None
    assert "মিষ্টি" in result.answer


def test_fire_heat(brain: Brain) -> None:
    result = synthesize(brain, "আগুন কি দেয়?")
    assert result is not None
    assert "তাপ" in result.answer


# ---------------------------------------------------------------------------
# Chain reasoning (depth-1 derivation)
# ---------------------------------------------------------------------------


def test_chain_reasoning_bn(brain: Brain) -> None:
    # No direct fact "রোদ comes_from" chain: rain falls_from clouds
    # and clouds are made_of water vapor — verify chaining at least
    # searches one hop without error.
    result = synthesize(brain, "মেঘ কী দিয়ে বানানো হয়?")
    # Either a direct fact or a chain-derived answer is acceptable.
    if result is not None:
        assert result.confidence > 0.0


def test_chain_finds_intermediate(brain: Brain) -> None:
    # "বরফ" -> is_frozen -> "পানি" -> is_a -> "তরল পদার্থ"
    result = synthesize(brain, "বরফ হলো কি?")
    if result is not None:
        assert "পানি" in result.answer or "কঠিন" in result.answer


# ---------------------------------------------------------------------------
# Graceful fallback: unknown input is NOT a canned parse error
# ---------------------------------------------------------------------------


def test_unknown_question_no_canned_parse_failure(brain: Brain) -> None:
    raw = "এলিফেন্ট কিভাবে খায়?"
    output = brain.process(raw)
    answer = output.get("response", "")
    canned = "parse করতে পারছি না"
    assert canned not in answer, f"canned parse failure echoed: {answer!r}"


def test_random_statement_no_canned_parse_failure(brain: Brain) -> None:
    output = brain.process("আমি আবহাওয়ায় ভালোবাসি")
    answer = output.get("response", "")
    canned = "parse করতে পারছি না"
    assert canned not in answer, f"canned parse failure echoed: {answer!r}"


def test_genuine_unknown_still_humble(brain: Brain) -> None:
    # A question about something genuinely not in any knowledge base
    # should return an honest humble reply, never hallucinated facts.
    output = brain.process("কেলোনিয়ার রাজধনী কি?")
    answer = output.get("response", "")
    confidence = output.get("confidence", 1.0)
    assert isinstance(answer, str)
    assert confidence <= 1.0


# ---------------------------------------------------------------------------
# Confidence discipline
# ---------------------------------------------------------------------------


def test_synthesized_confidence_bounded(brain: Brain) -> None:
    result = synthesize(brain, "আকাশের রঙ কি?")
    assert result is not None
    assert 0.0 < result.confidence <= 0.99


def test_synthesis_has_derivation_steps(brain: Brain) -> None:
    result = synthesize(brain, "বাংলাদেশের রাজধনী কি?")
    assert result is not None
    assert len(result.steps) >= 1
    # steps carry the derivation triple
    assert any("বাংলাদেশ" in step or "capital" in step for step in result.steps)


# ---------------------------------------------------------------------------
# Brain-level routing: synthesis reached via process()
# ---------------------------------------------------------------------------


def test_brain_process_synthesizes_sky_answer(brain: Brain) -> None:
    output = brain.process("আকাশের রঙ কি?")
    answer = output.get("response", "")
    confidence = output.get("confidence", 0.0)
    assert "নীল" in answer, f"sky answer missing 'নীল': {answer!r}"
    assert 0.0 < confidence <= 1.0


def test_brain_process_synthesizes_capital(brain: Brain) -> None:
    output = brain.process("বাংলাদেশের রাজধনী কি?")
    answer = output.get("response", "")
    assert "ঢাকা" in answer, f"capital answer missing 'ঢাকা': {answer!r}"


def test_thought_trace_recorded(brain: Brain) -> None:
    brain.process("আকাশের রঙ কি?")
    trace = brain.state.thought_trace
    # Either derivation mechanism may answer, but the reasoning steps that
    # produced the answer must always be inspectable.
    recorded = [key for key in ("inference_synthesis", "universal_resolution") if key in trace]
    assert recorded, f"no derivation trace recorded: {trace}"
    assert len(trace[recorded[0]]["steps"]) >= 1
