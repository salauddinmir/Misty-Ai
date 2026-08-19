"""
Self-directed learning: close the brain's own knowledge gaps.

When an answer path fails, :meth:`Brain._record_knowledge_gap` records the
topic. This module turns that queue into autonomous study: it picks the gaps
asked about most often, researches them through the existing
:class:`~brain.knowledge.web_learning.WebSearchLearner`, and lets the normal
safety gate decide what may enter durable memory.

Design rules kept deliberately strict:

* **Opt-in.** Nothing here runs unless self-directed learning is enabled, so a
  deployment that must stay offline behaves exactly as before.
* **Same safety gate.** Facts still flow through ``evaluate_learning`` with
  provenance, multi-source agreement, and contradiction checks. Autonomy
  changes *when* learning happens, never *what* is allowed.
* **No chat-path fetching.** Study happens on the background loop, so a user
  message can never trigger a live network call inside a response.
* **Never during evaluation.** Assessment clones are skipped entirely.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class StudyResult:
    """Outcome of one self-directed study cycle."""

    attempted: List[str] = field(default_factory=list)
    learned: Dict[str, int] = field(default_factory=dict)
    quarantined: Dict[str, int] = field(default_factory=dict)
    skipped: List[str] = field(default_factory=list)
    error: str | None = None
    started_at: float = field(default_factory=time.time)
    duration_seconds: float = 0.0

    @property
    def learned_total(self) -> int:
        return sum(self.learned.values())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "attempted": list(self.attempted),
            "learned": dict(self.learned),
            "learned_total": self.learned_total,
            "quarantined": dict(self.quarantined),
            "skipped": list(self.skipped),
            "error": self.error,
            "started_at": self.started_at,
            "duration_seconds": round(self.duration_seconds, 3),
        }


class SelfDirectedLearner:
    """Study the brain's own unanswered questions."""

    def __init__(
        self,
        brain: Any,
        *,
        enabled: bool = False,
        topics_per_cycle: int = 2,
        min_gap_count: int = 1,
        max_facts_per_topic: int = 4,
    ) -> None:
        self.brain = brain
        self.enabled = enabled
        self.topics_per_cycle = max(1, topics_per_cycle)
        self.min_gap_count = max(1, min_gap_count)
        self.max_facts_per_topic = max(1, max_facts_per_topic)
        self.last_result: Dict[str, Any] | None = None
        self.studied_topics: Dict[str, float] = {}

    # ------------------------------------------------------------------
    def select_topics(self) -> List[str]:
        """Gaps worth studying now, most frequently asked first."""
        gaps = [
            gap
            for gap in getattr(self.brain, "knowledge_gaps", [])
            if int(gap.get("count", 1)) >= self.min_gap_count
            and gap.get("topic")
            and gap["topic"].casefold() not in self.studied_topics
        ]
        gaps.sort(key=lambda gap: (int(gap.get("count", 1)), gap.get("last_seen", 0.0)), reverse=True)
        return [str(gap["topic"]) for gap in gaps[: self.topics_per_cycle]]

    async def study_once(self) -> StudyResult:
        """Research the current top gaps and record what was learned."""
        started = time.perf_counter()
        result = StudyResult()

        if not self.enabled:
            result.error = "self_directed_learning_disabled"
            self.last_result = result.to_dict()
            return result
        if getattr(self.brain, "_assessment_mode", False):
            result.error = "assessment_mode"
            self.last_result = result.to_dict()
            return result
        learner = getattr(self.brain, "web_learner", None)
        if learner is None:
            result.error = "no_web_learner"
            self.last_result = result.to_dict()
            return result

        topics = self.select_topics()
        if not topics:
            result.duration_seconds = time.perf_counter() - started
            self.last_result = result.to_dict()
            return result

        result.attempted = list(topics)
        before = self.brain.semantic_memory.size
        try:
            batch = await learner.ingest_batch(topics, max_facts_per_topic=self.max_facts_per_topic)
        except Exception as exc:  # network/parse failures must never crash the loop
            result.error = f"{type(exc).__name__}: {exc}"
            result.duration_seconds = time.perf_counter() - started
            self.last_result = result.to_dict()
            return result

        # Mark attempts so a permanently unavailable topic is not retried
        # every cycle.
        now = time.time()
        for topic in topics:
            self.studied_topics[topic.casefold()] = now

        for topic in topics:
            learned = self._count(batch, topic, "committed")
            quarantined = self._count(batch, topic, "quarantined")
            if learned:
                result.learned[topic] = learned
            if quarantined:
                result.quarantined[topic] = quarantined
            if not learned and not quarantined:
                result.skipped.append(topic)

        gained = self.brain.semantic_memory.size - before
        if gained > 0:
            # Answered gaps are no longer gaps.
            self._clear_answered(topics)

        result.duration_seconds = time.perf_counter() - started
        payload = result.to_dict()
        payload["facts_added"] = max(0, gained)
        self.last_result = payload
        return result

    # ------------------------------------------------------------------
    @staticmethod
    def _count(batch: Any, topic: str, kind: str) -> int:
        """Count committed/quarantined items reported for ``topic``."""
        items = getattr(batch, kind, None)
        if items is None and isinstance(batch, dict):
            items = batch.get(kind)
        if not items:
            return 0
        total = 0
        for item in items:
            if isinstance(item, dict):
                haystack = " ".join(str(value) for value in item.values()).casefold()
            else:
                haystack = str(item).casefold()
            if topic.casefold() in haystack:
                total += 1
        # A batch result without per-topic attribution still counts once.
        return total or (len(items) if len(topic) > 0 and len(items) else 0)

    def _clear_answered(self, topics: List[str]) -> None:
        """Drop gaps the brain can now answer."""
        remaining = []
        for gap in getattr(self.brain, "knowledge_gaps", []):
            topic = str(gap.get("topic", ""))
            if topic.casefold() in {item.casefold() for item in topics}:
                if self.brain.universal_resolver.resolve(topic, self.brain, target=topic) is not None:
                    continue
            remaining.append(gap)
        self.brain.knowledge_gaps = remaining
