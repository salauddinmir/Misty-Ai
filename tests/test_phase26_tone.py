"""Phase 26 tests: emotion-driven tone mapping.

The brain's internal emotional state changes the STYLE of its reply:
enthusiastic openers when interest and curiosity are high, calm respectful
replies to anger, warm safe jokes on humor requests, and short replies
when attention is low. All templates are pre-written; no commercial LLM.
"""

from __future__ import annotations

import pytest

from brain.core.brain import Brain
from brain.emotion.state import EmotionalState
from brain.emotion.tone import (
    _SAFE_JOKES_BN,
    _SAFE_JOKES_EN,
    ToneMapper,
)


@pytest.fixture()
def brain():
    return Brain()


@pytest.fixture()
def mapper():
    return ToneMapper()


def _emotion(**values) -> EmotionalState:
    state = EmotionalState()
    for key, value in values.items():
        setattr(state, key, value)
    return state


# ---------------------------------------------------------------------------
# Unit behavior of the tone mapper
# ---------------------------------------------------------------------------


def test_angry_user_gets_calm_tone(mapper):
    plan = mapper.plan_tone(
        emotion=_emotion(interest=0.9, curiosity=0.9),
        user_text="আমি খুব রাগান্বিত তুমার কথায়",
        response="আমি বুঝতে পারছি।",
    )
    assert plan.style == "calm"
    assert "শান্ত" in plan.opener or "সমাধান" in plan.opener, plan.opener


def test_angry_user_gets_calm_tone_en(mapper):
    plan = mapper.plan_tone(
        emotion=_emotion(interest=0.9, curiosity=0.9),
        user_text="I am angry with you",
        response="I understand.",
    )
    assert plan.style == "calm"
    assert "calmly" in plan.opener, plan.opener


def test_high_interest_gets_enthusiastic_tone(mapper):
    plan = mapper.plan_tone(
        emotion=_emotion(interest=0.9, curiosity=0.8),
        user_text="সেতু কী?",
        response="সেতু হলো নদীর উপরের রাস্তা।",
    )
    assert plan.style == "enthusiastic"
    assert plan.length_hint == "detailed"
    assert plan.opener in ("এটা নিয়ে ভেবে দেখি।", "এটা আমারও পছন্দের বিষয়।", "এখান থেকেই শুরু করি।"), plan.opener


def test_low_attention_gets_short_tone(mapper):
    plan = mapper.plan_tone(
        emotion=_emotion(attention=0.2),
        user_text="আমি বই পড়ছি",
        response="ভালো, পড়া চালিয়ে যান।",
    )
    assert plan.style == "short"
    assert plan.length_hint == "short"


def test_humor_request_gets_warm_tone_and_safe_joke(mapper):
    plan = mapper.plan_tone(
        emotion=_emotion(satisfaction=0.6),
        user_text="মজার কিছু বলো",
        response="বলছি।",
    )
    assert plan.style == "warm"
    assert plan.joke in _SAFE_JOKES_BN, plan.joke
    assert plan.opener == "আনন্দে বলছি।", plan.opener


def test_humor_request_en_gets_english_joke(mapper):
    plan = mapper.plan_tone(
        emotion=_emotion(satisfaction=0.6),
        user_text="Tell me a funny joke",
        response="Sure thing.",
    )
    assert plan.style == "warm"
    assert plan.joke in _SAFE_JOKES_EN, plan.joke


def test_joke_never_insults(mapper):
    """Safe humor pool never contains mockery or personal insults."""
    forbidden = {"বোকা", "মূর্খ", "নিকৃষ্ট", "stupid", "dumb", "ugly", "idiot"}
    for joke in _SAFE_JOKES_BN + _SAFE_JOKES_EN:
        lower = joke.lower()
        assert not any(word in lower for word in forbidden), joke


def test_normal_state_gives_plain_tone(mapper):
    plan = mapper.plan_tone(
        emotion=EmotionalState(),
        user_text="আমার একটা প্রশ্ন আছে",
        response="প্রশ্ন করুন।",
    )
    assert plan.style == "normal"
    assert plan.length_hint == "normal"
    assert plan.joke == ""


def test_urgency_gets_short_pointed_tone(mapper):
    plan = mapper.plan_tone(
        emotion=_emotion(urgency=0.9, interest=0.4),
        user_text="দ্রুত উত্তর দাও",
        response="উত্তর হাজির।",
    )
    assert plan.style == "short"
    assert plan.length_hint == "short"


# ---------------------------------------------------------------------------
# End-to-end through Brain.process
# ---------------------------------------------------------------------------


def test_brain_answers_angry_user_calmly(brain):
    response = brain.process("আমি খুব রাগান্বিত, তুমি কিছু বুঝছো না!")["response"]
    assert "শান্ত" in response or "সমাধান" in response or "বুঝ" in response, response


def test_brain_tells_safe_joke_on_request(brain):
    response = brain.process("মজার কিছু বলো")["response"]
    assert any(joke[:12] in response for joke in _SAFE_JOKES_BN), response
    # And no mockery slips in:
    assert "বোকা" not in response and "মূর্খ" not in response, response


def test_brain_high_interest_enthusiastic(brain):
    brain.emotion.update_curiosity(0.5)  # 0.5 -> 1.0 clamped at 1.0? update adds
    brain.emotion.interest = 0.95
    brain.emotion.curiosity = 0.95
    response = brain.process("সেতু কী?")["response"]
    assert "ভেবে দেখি" in response or "পছন্দের" in response or "শুরু করি" in response, response


def test_tone_preserves_content(brain):
    """Tone openers never destroy the factual answer underneath."""
    brain.process("মনে রাখো: সেতু হলো নদীর উপরের রাস্তা")
    brain.emotion.interest = 0.95
    brain.emotion.curiosity = 0.95
    response = brain.process("সেতু কী?")["response"]
    assert "সেতু" in response, response
    assert "নদী" in response, response
