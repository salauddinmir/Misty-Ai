"""
Weighted Memory Recall.

Scores memories along three psychological dimensions and ranks them for
retrieval:

- **Recency**  — more recent memories score higher (exponential decay)
- **Frequency** — memories recalled/used often score higher
- **Emotional salience** — high-valence memories survive longer and
  score higher

This mirrors human memory: recent, repeated and emotionally charged
experiences are the easiest to recall.
"""

import math
import time
from typing import Any, Dict, List

# Seconds in a day, used as the recency time base.
_DAY_SECONDS = 86400.0


class WeightedRecall:
    """Recency / frequency / emotional weighted recall scorer.

    Args:
        recency_halflife_days: Days after which a memory's recency score
            halves (default 7).
        max_frequency_score: Score ceiling contributed by frequency.
        emotion_boost: Maximum additive boost from emotional salience.
    """

    def __init__(
        self,
        recency_halflife_days: float = 7.0,
        max_frequency_score: float = 0.4,
        emotion_boost: float = 0.3,
    ) -> None:
        self.recency_halflife_days = recency_halflife_days
        self.max_frequency_score = max_frequency_score
        self.emotion_boost = emotion_boost
        # concept_id -> number of times recalled
        self._recall_counts: Dict[str, int] = {}
        # concept_id -> last recall timestamp (epoch)
        self._last_recall_at: Dict[str, float] = {}

    # ------------------------------------------------------------------

    def record_recall(self, concept_id: str) -> None:
        """Mark a concept as recalled now (updates frequency + recency)."""
        self._recall_counts[concept_id] = self._recall_counts.get(concept_id, 0) + 1
        self._last_recall_at[concept_id] = time.time()

    def recency_score(self, concept_id: str, now: float | None = None) -> float:
        """Exponential recency score in [0, 1].

        Uses the last time the concept was recalled (or its creation
        time) as the timestamp.
        """
        last = self._last_recall_at.get(concept_id)
        if last is None:
            return 0.0
        days = ((now or time.time()) - last) / _DAY_SECONDS
        return math.pow(0.5, days / self.recency_halflife_days)

    def frequency_score(self, concept_id: str) -> float:
        """Logarithmic frequency score in [0, max_frequency_score]."""
        count = self._recall_counts.get(concept_id, 0)
        if count == 0:
            return 0.0
        return self.max_frequency_score * min(1.0, math.log2(1 + count) / 4.0)

    def emotion_score(self, emotional_valence: float | None = None) -> float:
        """Emotional salience score in [0, emotion_boost]."""
        if emotional_valence is None:
            return 0.0
        # Strong valence (positive or negative) is memorable.
        return self.emotion_boost * min(1.0, abs(emotional_valence))

    def score(
        self,
        concept_id: str,
        emotional_valence: float | None = None,
        now: float | None = None,
    ) -> Dict[str, float]:
        """Total weighted recall score for a concept.

        Returns a dict with per-component scores and the final
        ``total`` (clamped to [0, 1]).
        """
        components = {
            "recency": round(self.recency_score(concept_id, now=now), 4),
            "frequency": round(self.frequency_score(concept_id), 4),
            "emotion": round(self.emotion_score(emotional_valence), 4),
        }
        total = sum(components.values())
        components["total"] = round(min(1.0, total), 4)
        return components

    def rank(
        self,
        candidates: List[Dict[str, Any]],
        valence_lookup: Any | None = None,
        now: float | None = None,
    ) -> List[Dict[str, Any]]:
        """Rank candidate concept dicts by weighted recall score.

        Each candidate must have at least a ``concept_id`` key.
        ``valence_lookup`` is an optional dict ``concept_id -> valence``
        (e.g. from an episode's emotional valence).
        """
        scored: List[Dict[str, Any]] = []
        for cand in candidates:
            cid = cand["concept_id"]
            valence = (valence_lookup or {}).get(cid)
            scores = self.score(cid, emotional_valence=valence, now=now)
            entry = dict(cand)
            entry["recall_scores"] = scores
            scored.append(entry)
        scored.sort(key=lambda e: e["recall_scores"]["total"], reverse=True)
        return scored

    def forget(self, concept_id: str) -> None:
        """Remove a concept from recall bookkeeping (used in tests)."""
        self._recall_counts.pop(concept_id, None)
        self._last_recall_at.pop(concept_id, None)
