"""Tests for deterministic language grounding metadata."""

from brain.cognition import LanguageGrounder


def test_bengali_math_grounding_exposes_engine_claim() -> None:
    result = LanguageGrounder.ground(
        "উত্তর",
        raw_input="২ + ২ কত?",
        intent="math",
        confidence=0.95,
        evidence_count=1,
        hypothesis_count=1,
    )

    assert result.language == "bn"
    assert "deterministic_math_engine" in result.claims
    assert result.uncertainty == 0.05
    assert result.to_dict()["claims"] == list(result.claims)


def test_english_unknown_grounding_is_bounded() -> None:
    result = LanguageGrounder.ground(
        "I need more evidence.",
        raw_input="What is this?",
        intent="unknown",
        confidence=1.4,
        evidence_count=0,
        hypothesis_count=0,
    )

    assert result.language == "en"
    assert result.confidence == 1.0
    assert result.uncertainty == 0.0
    assert result.claims == ("intent_and_dialogue_context",)
