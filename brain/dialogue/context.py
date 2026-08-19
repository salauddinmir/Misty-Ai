"""Dialogue Context Memory.
Maintains a bounded multi-turn conversation history with entity
salience tracking. The most recently mentioned entity becomes the
default target for pronoun resolution (e.g. "সে" / "it" / "his"),
and the recent history allows the system to refer back to what the
user said earlier in the same conversation.

This module is pure-Python with no external dependencies so it works
in all CI Python versions.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List


def extract_entity_candidates(text: str) -> List[str]:
    """Extract likely entity mentions from a turn of text.

    Candidates are proper-noun-like tokens: sequences of Bengali word
    characters that look like a name, or capitalized English words
    (excluding sentence-start tokens in mixed text). Interrogative and
    common Bengali words are filtered out to avoid false salience.
    """
    if not text:
        return []
    candidates: List[str] = []
    _banned = {
        # Common Bengali words that must never be entities
        "আমি",
        "তুমি",
        "আপনি",
        "আমার",
        "তুমার",
        "সে",
        "তার",
        "এর",
        "এই",
        "সেই",
        "ও",
        "এ",
        "যা",
        "কে",
        "কি",
        "কী",
        "হলো",
        "মানে",
        "আছে",
        "থাকে",
        "বলো",
        "বলুন",
        "জানো",
        "করো",
        "আমাকে",
        "তোমাকে",
        "না",
        "হ্যাঁ",
        "ঠিক",
        "আচ্ছা",
        "অনে",
        "ভালো",
        "কেমন",
        "এখন",
        "তৈরি",
        "স্থাপক",
        "creator",
        "আগে",
        "পারে",
        "এটা",
        "ওটা",
        "এটাই",
        "সব",
        "কেনো",
        "এবং",
        "তবে",
        "নাম",
        "মনে",
        "রাখো",
        "রাখুন",
        "জানি",
        "রাখা",
        "হয়েছে",
        "আরো",
        "আসলে",
        "আসলেই",
        "ভুল",
        # Common English stopwords that must never be entities
        "I",
        "Me",
        "My",
        "You",
        "Your",
        "He",
        "Him",
        "His",
        "She",
        "Her",
        "It",
        "Its",
        "This",
        "That",
        "The",
        "Is",
        "Am",
        "Are",
        "Was",
        "Were",
        "Be",
        "Who",
        "What",
        "Where",
        "When",
        "Why",
        "How",
        "A",
        "An",
        "Not",
        "No",
        "Yes",
        "Okay",
        "Ok",
        "Please",
        "Tell",
        "Say",
        "Know",
        "Think",
        "Can",
        "Will",
        "Would",
        "Could",
        # Explicit-teaching discourse verbs must never seed salience:
        # "Remember that a drone is ..." should rank 'drone' above
        # 'Remember' when the brain scrapes entities from the input.
        "Remember",
        "Keep",
        "Learn",
        "Note",
    }
    # Bengali multi-word name spans: 1-3 word sequences of Bengali chars
    bn_token_re = re.compile(r"[\u0980-\u09FF]+", re.UNICODE)
    bn_words = bn_token_re.findall(text)
    candidates = [word for word in bn_words if word not in _banned and len(word) >= 2]
    # English candidates: capitalized words in the middle of the text
    # plus any remaining content words after the ban filter, so taught
    # lowercase entities ("drone", "robot") still join the salience
    # ranking instead of being invisible to pronoun resolution.
    en_token_re = re.compile(r"\b([A-Z][a-zA-Z0-9_-]+)\b")
    for match in en_token_re.finditer(text):
        word = match.group(1)
        if word not in _banned:
            candidates.append(word)
    # Lowercase English content words only count when preceded by an
    # article ("a drone", "the robot") so common words like "who", "what",
    # "does", "mean" never pollute salience and break pronoun resolution.
    for match in re.finditer(r"\b(?:a|an|the)\s+([a-z][a-z0-9_-]{2,})\b", text, re.IGNORECASE):
        word = match.group(1)
        if word not in _banned and word not in {
            c.lower() for c in candidates
        }:
            candidates.append(word)
    # Deduplicate while preserving order
    seen: set = set()
    ordered: List[str] = []
    for candidate in candidates:
        lower = candidate.lower()
        if lower not in seen:
            seen.add(lower)
            ordered.append(candidate)
    return ordered


@dataclass
class TurnRecord:
    """A single recorded turn in the conversation."""

    role: str  # "user" | "brain"
    text: str
    entities: List[str] = field(default_factory=list)
    intent: str = "unknown"
    timestamp: float = 0.0


class DialogueContext:
    """Bounded conversational context memory with entity salience.

    The context keeps the last `max_history` turns and maintains an
    ordered salience list of mentioned entities: the most recently
    mentioned entity ranks first, so pronoun resolution ("সে", "it")
    can map to the most salient prior entity.
    """

    def __init__(self, max_history: int = 10, max_salience: int = 5) -> None:
        self.max_history = max_history
        self.max_salience = max_salience
        self.history: List[TurnRecord] = []
        self.salient_entities: List[str] = []
        self.topic: str = ""

    # ------------------------------------------------------------------
    def add_turn(
        self,
        text: str,
        role: str = "user",
        entities: List[str] | None = None,
        intent: str = "unknown",
    ) -> None:
        """Record a conversation turn and update entity salience.

        Only user turns feed entity salience by default, because brain
        outputs mention many common words that would otherwise pollute
        the pronoun-resolution ranking.
        """
        if entities is not None:
            discovered = list(entities)
        elif role == "user":
            discovered = extract_entity_candidates(text)
        else:
            # Brain outputs mention many common words that would pollute
            # pronoun-resolution salience ranking, so they do not feed it.
            discovered = []
        self.history.append(TurnRecord(role=role, text=text, entities=discovered, intent=intent))
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history :]
        # Refresh salience: newest entities rank first, older ones kept
        updated: List[str] = []
        seen: set = set()
        for name in discovered:
            lower = name.lower()
            if lower not in seen:
                seen.add(lower)
                updated.append(name)
        for name in self.salient_entities:
            lower = name.lower()
            if lower not in seen:
                seen.add(lower)
                updated.append(name)
        self.salient_entities = updated[: self.max_salience]
        # A discovered entity only seeds the topic when the context has no
        # better anchor yet (the brain's interpret phase sets the topic
        # from the parsed structure, which must not be overwritten by a
        # generic scrape such as the discourse word "Remember").
        if discovered and not self.topic:
            self.topic = discovered[0]

    # ------------------------------------------------------------------
    @property
    def last_user_turn(self) -> TurnRecord | None:
        """The most recent user turn."""
        for turn in reversed(self.history):
            if turn.role == "user":
                return turn
        return None

    @property
    def last_brain_turn(self) -> TurnRecord | None:
        """The most recent brain turn."""
        for turn in reversed(self.history):
            if turn.role == "brain":
                return turn
        return None

    @property
    def most_salient_entity(self) -> str | None:
        """The entity most likely referred to by a pronoun right now."""
        return self.salient_entities[0] if self.salient_entities else None

    # ------------------------------------------------------------------
    def get_history_texts(self, include_last_n: int = 0) -> List[str]:
        """Return user turns (and optionally brain turns) as text list.

        If include_last_n is positive, include the last N turns of any
        role in chronological order.
        """
        if include_last_n > 0:
            return [turn.text for turn in self.history[-include_last_n:]]
        return [turn.text for turn in self.history if turn.role == "user"]

    def get_salient_entities(self) -> List[str]:
        """Current entity salience ranking (most recent first)."""
        return list(self.salient_entities)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize context state for brain state snapshots."""
        return {
            "turn_count": len(self.history),
            "topic": self.topic,
            "salient_entities": self.salient_entities,
            "recent_inputs": self.get_history_texts(include_last_n=3),
        }

    def reset(self) -> None:
        """Clear the context memory."""
        self.history.clear()
        self.salient_entities.clear()
        self.topic = ""
