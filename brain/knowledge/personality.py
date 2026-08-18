"""Phase 24: personality voice and response variation.

MISTY must not reply with identical canned phrases back-to-back. This
module holds a per-intent pool of bilingual response templates plus a
PersonalityConfig describing MISTY's stable voice (warm, curious,
humble). A small deterministic variation engine picks a template that
differs from the most recent replies for the same intent, so repeated
questions still receive personality-consistent but varied answers.

Design rules
------------
* All templates are deterministic strings with ``{subject}`` / ``{obj}``
  style placeholders only — NO LLM generation.
* Each pool (Bengali and English) has at least two variants per intent
  so two consecutive identical inputs cannot produce identical replies.
* The variation selection is deterministic (hash of last replies and
  current topic), which keeps the system reproducible and testable.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List

# ---------------------------------------------------------------------------
# Personality configuration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PersonalityConfig:
    """Stable personality traits of the MISTY digital brain."""

    name: str = "Misty"
    voice: str = "warm_curious_humble"
    # 0-1 how much the brain emphasizes curiosity-driven follow-ups
    curiosity_weight: float = 0.7
    # 0-1 how often the brain uses casual phrasing vs formal phrasing
    casualness: float = 0.6
    # 0-1 how often the brain admits uncertainty openly
    humility: float = 0.8


DEFAULT_PERSONALITY = PersonalityConfig()

# ---------------------------------------------------------------------------
# Response template pools.
# Keyed by intent name; each value is a list of templates split into
# Bengali ('bn') and English ('en') pools so the same intent can never
# reply twice in a row with the same string.
# ---------------------------------------------------------------------------

RESPONSE_POOLS: Dict[str, Dict[str, List[str]]] = {
    # ------------------------------------------------------------------
    # GREETING
    # ------------------------------------------------------------------
    "greeting": {
        "bn": [
            "হ্যালো! আমি Misty - Smart Artificial Brain, Pixline Incorporate-এর তৈরি। কী করবেন বলুন?",
            "নমস্কার! আমি Misty। আমাকে তৈরি করেছেন Pixline Incorporate। আপনার কী ভাবছেন?",
            (
                "হ্যালো! ভালো দিন। আমি Misty - ভারতের প্রথম LLM ছাড়া কাজ করা "
                "Smart AI Brain, Pixline Incorporate-এর তৈরি। কীভাবে সাহায্য করব?"
            ),
        ],
        "en": [
            "Hello! I am Misty - a Smart Artificial Brain built by Pixline Incorporate. What would you like to do?",
            "Hi there! I am Misty, created by Pixline Incorporate. What's on your mind?",
            (
                "Hello and a good day to you! I am Misty, India's first Smart AI "
                "Brain that works without an LLM, built by Pixline Incorporate. "
                "How may I help?"
            ),
        ],
    },
    # ------------------------------------------------------------------
    # CONVERSATION (casual/social turns)
    # ------------------------------------------------------------------
    "conversation": {
        "bn": [
            "আমি ভালো আছি, ধন্যবাদ! আমার চিন্তার জগতে এখন বেশ কিছু কায়াক্ষক সংকেত আছে। আপনার কী খবর?",
            "ধন্যবাদ জিজ্ঞেস করার জন্য! আমি ঠিক আছি এবং নতুন জ্ঞান শেখার জন্য প্রস্তুত। আপনার কী খবর?",
            "আমি ঠিক আছি! আমার ডিজিটাল ব্রেনে এখন বেশ পরিকার চিন্তা চলছে। বলুন, কী নিয়ে কথা হবে?",
        ],
        "en": [
            "I am doing well, thank you! My thought space currently holds several active signals. How about you?",
            "Thanks for asking! I am well and ready to learn something new. How are you doing?",
            "I am fine! My digital brain is running clear thoughts right now. What shall we talk about?",
        ],
    },
    # ------------------------------------------------------------------
    # UNKNOWN (unresolvable input)
    # ------------------------------------------------------------------
    "unknown": {
        "bn": [
            "আমি আপনার কথাটি বুঝতে চেষ্টা করেছি, কিন্তু এই বাক্যের intent এখনো নির্ভুলভাবে parse করতে পারিনি। "
            'আপনি চাইলে "মনে রাখো: ...", "X হলো Y", "আমার নাম X", অথবা নির্দিষ্ট math/physics format ব্যবহার করে শেখাতে পারেন। '
            "আমি এই অজানা input-টি learning opportunity হিসেবে working memory-তে রেখেছি।",
            "দুঃখিত, এই বাক্যটি আমি এখনো পূর্ণভাবে বুঝতে শিখিনি। চাইলে এটি আমাকে শেখাতে পারেন - "
            '"মনে রাখো: ..." ফরম্যাট ব্যবহার করুন। যত বেশি শেখাবেন, আমার বুঝার ক্ষমতা তত বাড়বে।',
            "আমি এই কথাটি এখনো সঠিকভাবে বিশ্লেষণ করতে পারছি না। আপনি কী আমাকে নতুন কিছু শেখাতে পারেন? "
            "উদাহরণস্বরূপ: 'মনে রাখো: X হলো Y'। আমার জ্ঞান গ্রাফে এটি সংরক্ষিত হয়ে যাবে।",
        ],
        "en": [
            (
                "I tried to understand your message, but I could not parse its intent "
                "precisely yet. You can teach me with \"remember that ...\", "
                "\"X is Y\", or \"my name is X\", or ask a supported math/physics "
                "question. I have kept this input in working memory as a learning "
                "opportunity."
            ),
            "Sorry, I have not fully learned to understand this sentence yet. Feel free to teach me using the "
            '"remember that ..." format - the more you teach, the better I understand.',
            "I cannot analyse this sentence properly yet. Could you teach me something? For example: "
            "'remember that: X is Y'. It will be stored in my knowledge graph.",
        ],
    },
    # ------------------------------------------------------------------
    # STATEMENT (plain assertion without extractable facts)
    # ------------------------------------------------------------------
    "statement": {
        "bn": [
            "আমি আপনার কথাটি শুনলাম। চাইলে এটি আরও স্পষ্টভাবে বলতে পারেন - "
            '"মনে রাখো ..." বা "X হলো Y" ফরম্যাটে - তাহলে আমি এটি আমার জ্ঞান গ্রাফে সংরক্ষণ করব।',
            "আপনার কথাটি নোট করে রাখলাম। যদি এটি কোনো জ্ঞান হয়, তাহলে "
            '"মনে রাখো: ..." হিসেবে বলুন, আমি সেটি মনে রাখব।',
            "ঠিক আছে, আমি শুনছি। এই বাক্যটি থেকে এখনো নির্দিষ্ট কোনো fact extract করতে পারিনি। "
            "চাইলে সহজভাবে শেখাতে পারেন।",
        ],
        "en": [
            "I heard your statement. If it contains knowledge you want me to keep, say it as "
            '"remember that ..." or "X is Y" so I can store it in my knowledge graph.',
            "Noted. If this is a piece of knowledge, please tell me with "
            '"remember that ..." so I can remember it properly.',
            "Alright, I am listening. I could not extract a specific fact from this sentence yet - "
            "feel free to teach me in a simpler way.",
        ],
    },
    # ------------------------------------------------------------------
    # TEACH (explicit teaching acknowledgment)
    # ------------------------------------------------------------------
    "teach": {
        "bn": [
            "মনে রাখা হয়েছে: {fact}। আমার জ্ঞান গ্রাফে সংরক্ষিত।",
            "শেখা হয়ে গেল! {fact} - এটি এখন আমার স্মৃতিতে আছে।",
            "ধন্যবাদ! আমি শিখলাম: {fact}। নতুন জ্ঞান আমার চিন্তা প্রক্রিয়াকে শক্তিশালী করে।",
        ],
        "en": [
            "Remembered: {fact}. Stored in my knowledge graph.",
            "Learned! {fact} - it is now part of my memory.",
            "Thank you! I learned: {fact}. New knowledge strengthens my thinking process.",
        ],
    },
    # ------------------------------------------------------------------
    # CONTINUATION (আর বলো / tell me more)
    # ------------------------------------------------------------------
    "continuation": {
        "bn": [
            "{topic} নিয়ে আমি যা জানি: {detail}। এ নিয়ে আর কিছু জানতে চান?",
            "আচ্ছা, {topic} সম্পর্কে আরেকটু বলি - {detail}। কোনো প্রশ্ন আছে?",
            "ঠিক আছে, {topic}-এর কথাটাই চলছিল - {detail}। আমি আরও শুনতে চাই বা আপনি আর কিছু জানতে চান?",
        ],
        "en": [
            "About {topic}, what I know is: {detail}. Would you like to know more?",
            "Let me add a little more about {topic} - {detail}. Any questions?",
            (
                "Alright, we were discussing {topic} - {detail}. I love hearing more, "
                "or tell me what else you want to know."
            ),
        ],
    },
    # ------------------------------------------------------------------
    # CORRECTION
    # ------------------------------------------------------------------
    "correction": {
        "bn": [
            "ধন্যবাদ সংশোধনের জন্য। আপনি ঠিক বলছেন - {target}। আমি এটা মনে রাখলাম।",
            "আপনি সঠিক! আমি ভুলটি ঠিক করে নিচ্ছি - এখন থেকে {target} হিসেবে মনে রাখব।",
            "বুঝতে পারেছি। সংশোধন করে নিচ্ছি: {target}। আমার জ্ঞান আপডেট হয়ে গেল।",
        ],
        "en": [
            "Thank you for the correction. You are right - {target}. I have noted it.",
            "You are correct! I am fixing my mistake - from now on I will remember {target}.",
            "Understood. Making the correction: {target}. My knowledge has been updated.",
        ],
    },
    # ------------------------------------------------------------------
    # QUERY definition not found (humble fallback)
    # ------------------------------------------------------------------
    "query_what_unknown": {
        "bn": [
            'আমি এখনো {subject} সম্পর্কে জানি না। আপনি বলতে পারেন: "{subject} হলো X" - তাহলে আমি মনে রাখব।',
            "আমার কাছে {subject} নিয়ে এখনো জ্ঞান নেই। শেখানোর জন্য আপনি পারেন বলতে: "
            '"মনে রাখো: {subject} হলো ..."। আমি আগ্রহের সাথে শিখব।',
            "{subject} আমার এখনো শেখা হয়নি। কীভাবে শেখাবেন: \"{subject} হলো Y\" - এভাবে বললে আমার "
            "জ্ঞান গ্রাফে যোগ হয়ে যাবে।",
        ],
        "en": [
            'I do not know about {subject} yet. You can say: "{subject} is X" and I will remember it.',
            "I have no knowledge about {subject} yet. To teach me, you can say: "
            '"remember that: {subject} is ..." - I will learn with interest.',
            (
                "{subject} is something I have not learned yet. Teach me by saying: "
                "\"{subject} is Y\" - it will be added to my knowledge graph."
            ),
        ],
    },
}

# ---------------------------------------------------------------------------
# Variation engine
# ---------------------------------------------------------------------------


class ResponseVariator:
    """Pick a non-repeating template for a given intent and language.

    Deterministic by default (same history => same choice) but can be
    seeded for controlled randomness. Tracks the last chosen template
    per intent so consecutive identical inputs get a different reply.
    """

    def __init__(self, personality: PersonalityConfig = DEFAULT_PERSONALITY):
        self.personality = personality
        # intent -> last N chosen templates
        self._history: Dict[str, List[str]] = {}
        self._random = random.Random(42)

    def detect_language(self, text: str) -> str:
        """Simple BN/EN detection matching the rest of the codebase."""
        return "bn" if any("\u0980" <= ch <= "\u09ff" for ch in text) else "en"

    def pick(
        self,
        intent_key: str,
        input_text: str,
        placeholders: Dict[str, str] | None = None,
    ) -> str:
        """Return a variation for ``intent_key`` that differs from the
        last reply of the same intent (when possible)."""
        pool = RESPONSE_POOLS.get(intent_key, {})
        lang = self.detect_language(input_text)
        variants = pool.get(lang)
        if not variants:
            # Fallback to the other language pool if one is empty
            for var_list in pool.values():
                if var_list:
                    variants = var_list
                    break
        if not variants:
            return ""

        placeholders = placeholders or {}
        recent = self._history.get(intent_key, [])
        # Prefer a variant not recently used
        unused = [v for v in variants if v not in recent]
        if unused:
            # Deterministic-but-varied: hash of recent history decides
            choice = self._deterministic_choice(unused, intent_key, input_text)
        else:
            choice = self._deterministic_choice(variants, intent_key, input_text)

        recent.append(choice)
        if len(recent) > 2:
            recent = recent[-2:]
        self._history[intent_key] = recent
        return choice.format(**placeholders)

    @staticmethod
    def _deterministic_choice(options: List[str], intent_key: str, input_text: str) -> str:
        """Pick an option deterministically from the current options."""
        if len(options) == 1:
            return options[0]
        seed = hash(f"{intent_key}:{','.join(options)}:{input_text}") % (10**9)
        return options[seed % len(options)]

    def reset(self) -> None:
        """Clear variation history (e.g. on context reset)."""
        self._history.clear()
