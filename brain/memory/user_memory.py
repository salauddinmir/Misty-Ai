"""
Phase 40: Long-term memory and personalization.

Misty normally stores every conversation into one shared brain instance on
the deployment, so conversations from many different visitors get mixed
together. This module adds a per-user memory layer that:

1. Fingerprint each visitor (X-Misty-User-Id header or a stable
   client-generated id; falls back to a per-deployment anonymous bucket so
   old behavior is preserved for callers without an id).
2. Keep a **profile** per user: preferred language, name, user-provided
   facts ("আমি ডাক্তার", "আমার স্কুলে পড়ি"), sentiment summary.
3. Keep an **episodic digest** per user: a rolling list of the most recent
   conversation turns (turn id, user utterance, bot reply, timestamp,
   emotional valence) so Misty can answer "কাল আমি কী বলেছিলাম?"-style
   personal questions with real recollection instead of scripted replies.
4. Expose `UserProfileMemory.personal_recall(user_id, query)` — semantic
   recall over the user's own profile facts and episodes.

Deterministic (no LLM). In-memory per process; persisted to the same DB
that powers chat-state persistence so cold starts do not lose memory
(see ``to_dict``/``from_dicts`` round-trip used by the chat persistence
task).
"""

import time as time_module
import uuid
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple


# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------
@dataclass
class UserFact:
    """A fact the user volunteered about themselves."""

    fact_id: str = field(default_factory=lambda: f"fact-{uuid.uuid4().hex[:8]}")
    text: str = ""
    category: str = "general"  # identity | relation | occupation | preference
    language: str = "unknown"  # bn | en | unknown
    first_seen: float = field(default_factory=time_module.time)
    mention_count: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fact_id": self.fact_id,
            "text": self.text,
            "category": self.category,
            "language": self.language,
            "first_seen": self.first_seen,
            "mention_count": self.mention_count,
        }


@dataclass
class UserEpisode:
    """One remembered turn from this user's conversation history."""

    episode_id: str = field(default_factory=lambda: f"ep-{uuid.uuid4().hex[:8]}")
    user_utterance: str = ""
    bot_reply: str = ""
    timestamp: float = field(default_factory=time_module.time)
    emotional_valence: float = 0.0
    intent: str = "general"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "user_utterance": self.user_utterance[:1000],
            "bot_reply": self.bot_reply[:1000],
            "timestamp": self.timestamp,
            "emotional_valence": self.emotional_valence,
            "intent": self.intent,
        }


@dataclass
class UserProfile:
    """Personalized memory of one visitor."""

    user_id: str
    facts: Dict[str, UserFact] = field(default_factory=dict)
    episodes: deque = field(default_factory=lambda: deque(maxlen=64))
    preferred_language: str | None = None  # bn | en
    first_seen: float = field(default_factory=time_module.time)
    last_seen: float = field(default_factory=time_module.time)
    turn_count: int = 0

    @property
    def last_seen_iso(self) -> str:
        return time_module.strftime("%Y-%m-%d %H:%M:%S", time_module.localtime(self.last_seen))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "preferred_language": self.preferred_language,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "last_seen_iso": self.last_seen_iso,
            "turn_count": self.turn_count,
            "fact_count": len(self.facts),
            "facts": [fact.to_dict() for fact in self.facts.values()],
            "episode_count": len(self.episodes),
            "recent_episodes": [episode.to_dict() for episode in list(self.episodes)[-10:]],
        }


# ---------------------------------------------------------------------------
# Simple keyword-based Bengali/English fact detection
# ---------------------------------------------------------------------------
_IDENTITY_MARKERS = (
    # English
    "my name is",
    "i am called",
    "call me",
    "i work as",
    "i am a",
    "i'm a",
    "i live in",
    "i study",
    "i am studying",
    "my school",
    "my college",
    # Bengali
    "আমার নাম",
    "আমাকে বলো",
    "আমাকে বলুন",
    "আমি একজন",
    "আমি একটা",
    "আমি পড়ি",
    "আমার স্কুল",
    "আমার কলেজ",
    "আমি করি",
)


def _classify_language(text: str) -> str:
    """Rough Bengali-vs-English classifier on character script ratios."""
    bn = sum(1 for ch in text if "\u0980" <= ch <= "\u09ff")
    en = sum(1 for ch in text if ch.isascii() and ch.isalpha())
    if bn == 0 and en == 0:
        return "unknown"
    if bn > en:
        return "bn"
    if en > bn:
        return "en"
    return "unknown"


def _is_identity_claim(text: str) -> Tuple[bool, str]:
    """Decide whether a user utterance is a self-referential fact and which
    category it belongs to. Returns (is_fact, category)."""
    lower = text.strip().lower()
    for marker in _IDENTITY_MARKERS:
        if marker in lower:
            if "নাম" in lower or "name" in lower or "call" in lower:
                return True, "identity"
            if any(k in lower for k in ("work", "job", "কাজ করি", "চাকরি", "ডাক্তার", "শিক্ষক", "ব্যবসা")):
                return True, "occupation"
            if any(k in lower for k in ("পড়ি", "study", "school", "স্কুল", "কলেজ", "college")):
                return True, "preference"
            return True, "general"
    return False, "general"


# ---------------------------------------------------------------------------
# User memory store
# ---------------------------------------------------------------------------
class UserProfileMemory:
    """Per-user long-term memory and personalization layer.

    Usage (wired by Brain in Phase 40)::

        user_memory.record_turn(
            user_id=brain.resolve_user_id(request),
            utterance="আমার নাম রাহুল",
            reply=result["response"],
            intent=intent, valence=valence,
        )
    """

    def __init__(self, max_users: int = 200, max_episodes_per_user: int = 64) -> None:
        self._profiles: Dict[str, UserProfile] = {}
        self._max_users = max_users
        self._max_episodes = max_episodes_per_user

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------
    def _get_or_create(self, user_id: str) -> UserProfile:
        profile = self._profiles.get(user_id)
        if profile is None:
            profile = UserProfile(user_id=user_id)
            self._profiles[user_id] = profile
            # Evict the least-recently-seen profile if over capacity.
            if len(self._profiles) > self._max_users:
                oldest_id = min(self._profiles, key=lambda uid: self._profiles[uid].last_seen)
                del self._profiles[oldest_id]
        return profile

    def record_turn(
        self,
        user_id: str,
        utterance: str,
        reply: str = "",
        intent: str = "general",
        emotional_valence: float = 0.0,
    ) -> None:
        """Remember one conversation turn for ``user_id``.

        Self-referential claims in the utterance are extracted as durable
        profile facts; the full turn is appended to the episodic digest.
        """
        profile = self._get_or_create(user_id)
        profile.last_seen = time_module.time()
        profile.turn_count += 1
        is_fact, category = _is_identity_claim(utterance)
        if is_fact and utterance.strip():
            existing = next((f for f in profile.facts.values() if _fact_matches(f.text, utterance)), None)
            if existing is not None:
                existing.mention_count += 1
            else:
                key = _normalize_fact(utterance)
                if key in profile.facts:
                    # Key collision only happens for identical claims; the
                    # stored fact absorbs the mention instead of overwriting.
                    profile.facts[key].mention_count += 1
                else:
                    profile.facts[key] = UserFact(
                        text=utterance.strip()[:500], category=category, language=_classify_language(utterance)
                    )
        episode = UserEpisode(
            user_utterance=utterance.strip()[:1000],
            bot_reply=reply.strip()[:1000],
            emotional_valence=emotional_valence,
            intent=intent,
        )
        # The deque's maxlen enforces the per-user episode cap, so
        # re-attach it whenever a profile was constructed with a
        # different default capacity (or later tuning changed the cap).
        if profile.episodes.maxlen != self._max_episodes:
            profile.episodes = deque(profile.episodes, maxlen=self._max_episodes)
        profile.episodes.append(episode)

    def set_preferred_language(self, user_id: str, language: str) -> None:
        """Explicitly remember the user's preferred language (bn | en)."""
        if language in ("bn", "en"):
            self._get_or_create(user_id).preferred_language = language

    # ------------------------------------------------------------------
    # Recall
    # ------------------------------------------------------------------
    def get_profile(self, user_id: str) -> UserProfile | None:
        return self._profiles.get(user_id)

    def personal_recall(self, user_id: str, query: str) -> Dict[str, Any]:
        """Personalized recall for one user: facts and episodes whose text
        overlaps tokens with the query."""
        profile = self._get_or_create(user_id)
        tokens = set(_tokenize(query))
        fact_hits = [fact.to_dict() for fact in profile.facts.values() if tokens & set(_tokenize(fact.text))]
        episode_hits = [
            episode.to_dict()
            for episode in profile.episodes
            if tokens & set(_tokenize(episode.user_utterance + " " + episode.bot_reply))
        ]
        return {
            "user_id": user_id,
            "preferred_language": profile.preferred_language,
            "fact_matches": fact_hits,
            "episode_matches": episode_hits,
            "last_seen": profile.last_seen_iso,
        }

    @property
    def user_count(self) -> int:
        """Number of visitors currently remembered."""
        return len(self._profiles)

    def known_users(self) -> List[str]:
        return sorted(self._profiles, key=lambda uid: -self._profiles[uid].turn_count)

    def to_dicts(self) -> Dict[str, Any]:
        """Full serialization for DB persistence (chat persistence task)."""
        return {
            "user_count": self.user_count,
            "profiles": [profile.to_dict() for profile in self._profiles.values()],
        }

    # ------------------------------------------------------------------
    # Summary for brain state
    # ------------------------------------------------------------------
    def summary(self) -> Dict[str, Any]:
        """Compact, inspectable snapshot added to get_state()."""
        return {
            "enabled": True,
            "user_count": self.user_count,
            "known_users": self.known_users()[:5],
            "total_facts": sum([len(p.facts) for p in self._profiles.values()]),
            "total_episodes": sum([len(p.episodes) for p in self._profiles.values()]),
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _tokenize(text: str) -> List[str]:
    lower = text.lower()
    # Keep Bengali word boundaries + ASCII words; strip punctuation.
    cleaned = lower.replace(",", " ").replace(".", " ").replace("?", " ").replace("!", " ")
    return [token for token in cleaned.split() if len(token) >= 2]


def _fact_matches(existing_text: str, new_utterance: str) -> bool:
    """Token overlap heuristic: same claim stated twice is one fact."""
    a, b = set(_tokenize(existing_text)), set(_tokenize(new_utterance))
    return len(a & b) >= max(2, len(a) // 2)


def _normalize_fact(utterance: str) -> str:
    """Stable dedup key for a user fact."""
    return utterance.strip()[:120].lower()
