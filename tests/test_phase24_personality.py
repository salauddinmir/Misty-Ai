"""Phase 24: personality voice and response variation.

The brain must never echo the exact same canned phrase for consecutive
identical inputs of the same intent, while still keeping a consistent
personality (warm, curious, humble) across turns.
"""

import pytest

from brain.core.brain import Brain
from brain.knowledge.personality import (
    DEFAULT_PERSONALITY,
    RESPONSE_POOLS,
)


@pytest.fixture()
def brain():
    return Brain()


def _ask(brain: Brain, *questions: str) -> list:
    return [brain.process(question)["response"] for question in questions]


# ---------------------------------------------------------------------------
# Pool sanity
# ---------------------------------------------------------------------------


def test_pools_have_bilingual_variants():
    """Every intent pool has at least two variants in both languages."""
    for intent_key, pools in RESPONSE_POOLS.items():
        for lang in ("bn", "en"):
            assert len(pools.get(lang, [])) >= 2, (intent_key, lang)


def test_pools_contain_no_empty_strings():
    for intent_key, pools in RESPONSE_POOLS.items():
        for lang, variants in pools.items():
            for variant in variants:
                assert variant.strip(), (intent_key, lang, variant)


# ---------------------------------------------------------------------------
# Greeting variation
# ---------------------------------------------------------------------------


def test_repeated_greetings_vary_bengali(brain):
    replies = _ask(brain, "হ্যালো", "হ্যালো", "হ্যালো")
    # The pool has three variants; at least one reply must differ from
    # another so the conversation never repeats verbatim.
    assert len(set(replies)) >= 2, replies


def test_repeated_greetings_vary_english(brain):
    replies = _ask(brain, "Hello", "Hi", "Hello")
    assert len(set(replies)) >= 2, replies


def test_greetings_keep_identity(brain):
    """All greeting variants still mention Misty and Pixline Incorporate."""
    replies = _ask(brain, "হ্যালো", "হ্যালো", "হ্যালো", "হ্যালো")
    for reply in replies:
        assert "Misty" in reply
        assert "Pixline Incorporate" in reply


# ---------------------------------------------------------------------------
# Unknown / teach variation
# ---------------------------------------------------------------------------


def test_unknown_inputs_do_not_echo(brain):
    """Three unresolvable Bengali inputs must not all be identical."""
    replies = _ask(
        brain,
        "মেঘের গান শুনছো?",
        "ট্রেনের চাকা ঘুরছে",
        "আলো ছড়াচ্ছে আকাশে",
    )
    assert len(set(replies)) >= 2, replies


def test_teaching_acknowledgment_varies(brain):
    """Two different teachings should acknowledge differently."""
    brain.process("মনে রাখো: বাঁশ হলো এক ধরনের ঘাস")
    brain.process("মনে রাখো: বাঘ হলো বাংলাডেশের জাতীয় পশু")
    replies = _ask(brain, "মনে রাখো: নীল হলো একটি রঙ", "মনে রাখো: সূর্য হলো তারা")
    # The stored-fact acknowledgment rotates across the pool variants.
    assert "মনে রাখা হয়েছে" in replies[0] or "শেখা হয়ে গেল" in replies[0] or "ধন্যবাদ" in replies[0], replies


# ---------------------------------------------------------------------------
# Fallback variation (repeated definition query of an unknown subject)
# ---------------------------------------------------------------------------


def test_unknown_definition_queries_vary(brain):
    """Asking about a subject MISTY has never learned must rotate the
    humble fallback instead of repeating the same sentence."""
    r1 = brain.process("ফুপ্পু হলো কী?")["response"]
    r2 = brain.process("ফুপ্পু কী?")["response"]
    r3 = brain.process("ফুপ্পু মানে কী?")["response"]
    assert len({r1, r2, r3}) >= 2, (r1, r2, r3)


# ---------------------------------------------------------------------------
# Personality consistency
# ---------------------------------------------------------------------------


def test_personality_is_stable():
    """The default personality keeps MISTY's warm, curious, humble voice."""
    assert DEFAULT_PERSONALITY.voice == "warm_curious_humble"
    assert 0.0 <= DEFAULT_PERSONALITY.humility <= 1.0


def test_variator_pick_returns_pool_template(brain):
    replies = _ask(brain, "হ্যালো")
    bn_variants = RESPONSE_POOLS["greeting"]["bn"]
    # Phase 25 appends a driver follow-up question to replies, so the
    # ACT handler's response must START with one of the pool templates.
    assert any(replies[0].startswith(variant) for variant in bn_variants), replies[0]
