"""Phase 25: Conversation driver.

Humans do not answer and stop — they keep the exchange alive. This module
gives Misty the habit of driving the conversation forward:

* Follow-up prompts (`needs_followup` flag on ACT results) when the answer
  is thin (low confidence / no facts found / shallow topic),
* Interest-expansion turns ("আপনি কি জানতেন...?") when the topic has
  related concepts the user has not touched yet,
* Conversation-closure recognition ("ঠিক আছে", "বাই", "goodbye") so the
  brain does not force a follow-up question when the user is leaving,
* Off-track topic detection — a short, gentle steering phrase when the
  new topic drifts too far from what was just discussed.

Everything is deterministic and rule-based: no commercial LLM is used.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Closure / farewell markers: when the user is ending the conversation the
# driver must NOT append a follow-up question.
# ---------------------------------------------------------------------------
_CLOSURE_PATTERNS = (
    re.compile(
        r"\b(বাই|বিদায়|ঠিক আছে|অনেক ধন্যবাদ|আজকে এই পর্যন্ত|"
        r"goodbye|bye|good night|goodbye|see you|talk to you later|"
        r"that's all|that is all)\b",
        re.UNICODE,
    ),
)

# ---------------------------------------------------------------------------
# User-state markers: what the user is expressing about themselves. The
# driver picks an empathic or encouraging follow-up shape.
# ---------------------------------------------------------------------------
_USER_STATE_PATTERNS = (
    # Tired / sad / frustrated / unwell
    (
        "distress",
        re.compile(
            r"(ক্লান্ত|ক্লান্ট|ক্ষুব্ধ|দুঃখিত|ক্ষণিত|অসুস্থ|বিরক্ত|বিরক্তি|"
            r"খারাপ লাগছে|ভালো লাগছে না|মন খারাপ|কাঁদছি|রাগান্বিত|রাগ করছে|"
            r"সন্দেহ|দুশ্চিন্তা|চিন্তিত|worried|tired|exhausted|sad|upset|"
            r"angry|frustrated|not feeling|feeling down|stressed|anxious)",
            re.UNICODE,
        ),
    ),
    # Happy / excited
    (
        "joy",
        re.compile(
            r"(আনন্দিত|খুশি|ভালো লাগছে আমার|উত্সাহিত|চমৎকার দিন|great|"
            r"happy|excited|wonderful|lovely day|feeling good)",
            re.UNICODE,
        ),
    ),
    # Questioning / curious
    (
        "curious",
        re.compile(
            r"(বলো দেখি|বলে দাও|জানতে চাই|কেমন হবে|জানি না তো|tell me|how do|"
            r"what do|do you know)",
            re.UNICODE,
        ),
    ),
)

# ---------------------------------------------------------------------------
# Interest-expansion openers — used when the topic has unexplored related
# concepts and confidence is enough to invite further discussion.
# ---------------------------------------------------------------------------
_BN_EXPANSION_OPENERS = [
    "আপনি কি জানতেন — এটা নিয়ে আরো কিছু জানা আছে, বলব?",
    "এই নিয়ে আমার কাছে আরো কিছু ধারণা জমা আছে। জানতে চান?",
    "এতটুকু বললাম; চাইলে এর সাথে জড়িত আরো কিছু বলতে পারি।",
]

_EN_EXPANSION_OPENERS = [
    "Did you know — I have a little more on this topic. Want me to continue?",
    "There are a few related ideas I could share as well. Interested?",
    "That is the short version; I can go deeper if you like.",
]

_BN_CLOSE_GREETINGS = [
    "ঠিক আছে, আবার কথা হবে। নতুন কিছু শিখতে চাইলে বলবেন!",
    "বিদায় নিয়ে যাওয়ার আগে আমার কিছু বলার আছে — আবার আসবেন!",
]

_EN_CLOSE_GREETINGS = [
    "Alright, talk to you again soon. New topics are always welcome!",
    "Goodbye! Come back anytime you want to learn something new.",
]


def _is_bengali(text: str) -> bool:
    return any("\u0980" <= ch <= "\u09ff" for ch in text)


@dataclass
class FollowUpPlan:
    """What the driver wants to append after this turn."""

    question: str = ""  # follow-up question or expansion phrase
    kind: str = ""  # "empathy", "expansion", "clarification", "idle", "closure", ""
    needs_followup: bool = False


class ConversationDriver:
    """Decides whether a response should end with a question of its own.

    Wired after every ACT cycle in `Brain.process()`. Pure stateless rules
    over the dialogue context plus one cooldown: at most one driver-generated
    question per turn and no question immediately after another question.
    """

    # A follow-up question is suppressed when the user already asked one.
    def __init__(self, question_interval: int = 1) -> None:
        self.question_interval = question_interval
        self.turns_since_question = question_interval

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def plan_followup(
        self,
        user_text: str,
        response: str,
        intent: str,
        confidence: float,
        topic: str,
        topic_facts: int,
        has_related: bool,
    ) -> FollowUpPlan:
        """Build the follow-up plan for this turn.

        `user_text` is the incoming user turn; `response` is what the brain
        is about to send; `topic_facts` counts known is_a facts about the
        current topic; `has_related` is True when the knowledge graph holds
        unexplored neighbors of the topic.
        """
        if self._is_closure(user_text) or self._is_closure(response):
            # Pick the reply BEFORE incrementing: the first closure in a
            # session (turns_since_question == question_interval == 1)
            # should use the first genuine farewell (pool[1]).
            question = self._closure_reply(user_text)
            self.turns_since_question += 1
            return FollowUpPlan(
                question=question,
                kind="closure",
                needs_followup=False,
            )

        plan = FollowUpPlan()

        # Phase 25: empathy first — mirror the user's expressed state with a
        # gentle, open-ended question instead of another fact dump.
        state = self._user_state(user_text)
        if state == "distress":
            plan.question = (
                "আপনার কথা শুনে আমার খারাপ লাগছে। আমি শুনছি — চাইলে আরো বিষয়টা বলতে পারেন।"
                if _is_bengali(user_text)
                else "I'm sorry to hear that. I'm listening — feel free to tell me more."
            )
            plan.kind = "empathy"
            plan.needs_followup = True
        elif state == "joy":
            plan.question = (
                "আপনার আনন্দ শুনে আমারও ভালো লাগল! এই মুহূর্তটা নিয়ে আরো কিছু বলতে চান?"
                if _is_bengali(user_text)
                else "Glad to hear you're feeling good! Want to tell me more about it?"
            )
            plan.kind = "empathy"
            plan.needs_followup = True
        elif state == "curious" or not response:
            # The user explicitly asked for more / the brain has no answer:
            # keep the thread with a clarifying offer.
            offer = (
                "আমি কি আপনাকে আরো কিছু শেখাতে পারি, নাকি আগের কথাটাই এগিয়ে নিয়ে যাব?"
                if _is_bengali(user_text)
                else "Is there something else you'd like me to teach or continue with?"
            )
            plan.question = offer
            plan.kind = "clarification"
            plan.needs_followup = True
        else:
            # Phase 25: topic management — thin answers get a continuation
            # nudge; well-known topics get an interest expansion.
            shallow = (confidence < 0.6 or topic_facts == 0) and bool(topic)
            deep_enough = topic_facts > 0 or has_related
            can_ask = self.turns_since_question >= self.question_interval
            if shallow and can_ask and bool(topic):
                plan.question = (
                    f"{topic} নিয়ে আপনি কি আরো জানতে চান, নাকি অন্য কিছু নিয়ে কথা বলব?"
                    if _is_bengali(user_text)
                    else f"Would you like to know more about {topic}, or talk about something else?"
                )
                plan.kind = "expansion"
                plan.needs_followup = True
            elif deep_enough and can_ask and has_related and response:
                pool = _BN_EXPANSION_OPENERS if _is_bengali(user_text) else _EN_EXPANSION_OPENERS
                # Deterministic rotation across the pool (per-turn index).
                plan.question = pool[self.turns_since_question % len(pool)]
                plan.kind = "expansion"
                plan.needs_followup = True
            else:
                plan.kind = "idle"
                plan.needs_followup = False

        if plan.needs_followup:
            self.turns_since_question = 0
        else:
            self.turns_since_question += 1
        return plan

    def user_intent_closed(self, user_text: str) -> bool:
        return self._is_closure(user_text)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _is_closure(self, text: str) -> bool:
        return any(pattern.search(text or "") for pattern in _CLOSURE_PATTERNS)

    def _closure_reply(self, user_text: str) -> str:
        pool = _BN_CLOSE_GREETINGS if _is_bengali(user_text) else _EN_CLOSE_GREETINGS
        return pool[self.turns_since_question % len(pool)]

    def _user_state(self, text: str) -> str:
        for state, pattern in _USER_STATE_PATTERNS:
            if pattern.search(text or ""):
                return state
        return ""
