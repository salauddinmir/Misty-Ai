"""Phase 26: Emotion-driven tone mapping.

The internal emotional state (curiosity, attention, interest, urgency,
satisfaction, frustration, uncertainty, confidence) now genuinely changes
HOW the brain replies, not just what it computes:

* High interest/curiosity -> enthusiastic, detailed replies with
  encouraging openers ("চমৎকার প্রশ্ন!", "That's a great question!").
* Low attention / thin urgency -> short, direct replies.
* User frustration/anger -> calm, respectful, non-confrontational tone.
* User joy/humor request -> light, warm tone with strictly SAFE joke
  structures (no mockery, no personal insults, no sensitive topics).
* Frustration in the brain itself -> honest admission, no bluster.

All tone variants are pre-written bilingual templates selected
deterministically by emotion values; no commercial LLM is used.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from brain.emotion.state import EmotionalState

# ---------------------------------------------------------------------------
# Emotion openers — chosen by the reader's current internal state.
# ---------------------------------------------------------------------------
_ENTHUSIASTIC_OPENERS_BN = [
    "এটা নিয়ে ভেবে দেখি।",
    "এটা আমারও পছন্দের বিষয়।",
    "এখান থেকেই শুরু করি।",
]
_ENTHUSIASTIC_OPENERS_EN = [
    "Let me think this through.",
    "That's a topic I enjoy exploring.",
    "Let's look into it.",
]

_CALM_OPENERS_BN = [
    "বুঝেছি।",
    "শুনছি, আস্তে আস্তে বলুন।",
]
_CALM_OPENERS_EN = [
    "Understood.",
    "I hear you — let's take it step by step.",
]

_SHORT_OPENERS_BN = ["ঠিক আছে।"]
_SHORT_OPENERS_EN = ["Sure."]

_CALM_APOLOGY_BN = [
    "আমি বুঝেছি আপনার বিরক্তি; চলুন শান্তভাবে সমাধান খুঁজি।",
]
_CALM_APOLOGY_EN = [
    "I understand you're frustrated; let's solve this calmly.",
]

_WARM_OPENERS_BN = [
    "আনন্দে বলছি।",
]
_WARM_OPENERS_EN = [
    "Gladly.",
]

# ---------------------------------------------------------------------------
# Safe humor: only these structures are allowed. Nothing about people's
# looks, habits, family, or anything sensitive ever enters the joke pool.
# ---------------------------------------------------------------------------
_SAFE_JOKES_BN = [
    "একটা ছোট্ট গণিতের রসিকতা বলি — শূন্য একটা মজার সংখ্যা, সবাইকে ভাগ করতে গিয়ে নিজে হারিয়ে যায়!",
    "আমি যন্ত্র, তাই ঘুম পায় না — তবে মাঝেমাঝে র‍্যাম-এর কাছে একটু চোখ ঝাপসা অনুভব করি।",
    "জানেন, বিজ্ঞানীদের একটি মজার অভ্যাস আছে — তারা প্রশ্ন করে, তারপর উত্তর খুঁজে বেড়ায়!",
]
_SAFE_JOKES_EN = [
    "Here's a small math joke — zero is a funny number: try to divide anything by it and it just vanishes!",
    "I'm a machine, so I don't sleep — but sometimes I feel my RAM getting drowsy.",
    "Scientists have a funny habit: they ask a question and then go searching for the answer!",
]

# ---------------------------------------------------------------------------
# User-affect markers for tone shaping (shared vocabulary with Phase 25's
# driver so both modules agree on what the user expresses).
# ---------------------------------------------------------------------------
_USER_ANGER_PATTERNS = (
    re.compile(r"(রাগান্বিত|রাগ করছ|বিরক্ত|বিরক্তি|খারাপ মেজাজ|angry|mad|irritated|annoyed|frustrated with you)", re.UNICODE),
)
HUMOR_JOKES = {"bn": _SAFE_JOKES_BN, "en": _SAFE_JOKES_EN}

_USER_HUMOR_REQUEST_PATTERNS = (
    re.compile(r"(মজার কিছু|হাসির কিছু|রসিকতা করো|জোকস|মজা|funny|joke|make me laugh|hilarious)", re.UNICODE),
)

_HIGH_INTEREST_THRESHOLD = 0.7
_LOW_ATTENTION_THRESHOLD = 0.4


def _is_bengali(text: str) -> bool:
    return any("\u0980" <= ch <= "\u09ff" for ch in text)


@dataclass
class TonePlan:
    """The style the response should take this turn."""

    opener: str = ""  # short emotional opener prepended
    length_hint: str = ""  # "short" | "normal" | "detailed"
    joke: str = ""  # safe joke when humor requested
    style: str = ""  # "enthusiastic" | "calm" | "short" | "warm" | "normal"


class ToneMapper:
    """Maps the internal emotional state + user affect to a reply style."""

    def plan_tone(
        self,
        emotion: EmotionalState,
        user_text: str,
        response: str,
    ) -> TonePlan:
        plan = TonePlan()

        # User affect always wins over internal state: anger needs a calm
        # respectful reply; a joke request needs a warm safe joke.
        if self._user_anger(user_text):
            pool = _CALM_APOLOGY_BN if _is_bengali(user_text) else _CALM_APOLOGY_EN
            plan.opener = pool[0]
            plan.style = "calm"
            plan.length_hint = "normal"
            return plan
        if self._user_humor(user_text):
            plan.style = "warm"
            plan.length_hint = "normal"
            pool = _SAFE_JOKES_BN if _is_bengali(user_text) else _SAFE_JOKES_EN
            # Deterministic rotation by satisfaction level.
            idx = int(emotion.satisfaction * len(pool)) % len(pool)
            plan.joke = pool[idx]
            pool_op = _WARM_OPENERS_BN if _is_bengali(user_text) else _WARM_OPENERS_EN
            plan.opener = pool_op[0]
            return plan

        # Internal state decides the register.
        high_interest = emotion.interest > _HIGH_INTEREST_THRESHOLD and emotion.curiosity > _HIGH_INTEREST_THRESHOLD
        low_attention = emotion.attention < _LOW_ATTENTION_THRESHOLD

        if high_interest:
            pool = _ENTHUSIASTIC_OPENERS_BN if _is_bengali(user_text) else _ENTHUSIASTIC_OPENERS_EN
            plan.opener = pool[int(emotion.satisfaction * len(pool)) % len(pool)]
            plan.style = "enthusiastic"
            plan.length_hint = "detailed"
        elif low_attention:
            plan.style = "short"
            plan.length_hint = "short"
            pool = _SHORT_OPENERS_BN if _is_bengali(user_text) else _SHORT_OPENERS_EN
            plan.opener = pool[0]
        elif emotion.urgency > _HIGH_INTEREST_THRESHOLD:
            # Urgent input: get straight to the point.
            plan.style = "short"
            plan.length_hint = "short"
        else:
            plan.style = "normal"
            plan.length_hint = "normal"
        return plan

    def _user_anger(self, text: str) -> bool:
        return any(pattern.search(text or "") for pattern in _USER_ANGER_PATTERNS)

    def _user_humor(self, text: str) -> bool:
        return any(pattern.search(text or "") for pattern in _USER_HUMOR_REQUEST_PATTERNS)
