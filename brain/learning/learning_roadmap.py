"""
Phase 39: Self-Assessment-Driven Learning Roadmap (স্ব-মূল্যায়ন-চালিত শিক্ষা-পরিকল্পনা).

Misty's self-assessment (Phase 33) tells it *what it does not know*. Phase 39
closes the loop the other way around: the brain now *plans what to learn next*
from those gaps, exactly like a real student:

1. ``LearningPlanner.plan_next_topics()`` takes the latest GapAssessor report
   and, together with a department priority list and a learning-budget,
   produces an ordered ``LearningPlan``: which topics to learn, in what
   order, with what effort (weight), and *why* (evidence: which gap cases
   point at it).
2. Priority is a blend of four deterministic signals:
   * gap density per topic (how many cases failed / how many were asked),
   * incorrect-vs-honest-unknown severity (incorrect answers are punished
     more than honest unknowns — being confidently wrong is worse than not
     knowing),
   * recency (recently taught topics get a small decay so the brain does
     not over-learn one department),
   * user interest hints (topics the user asked about and got a weak
     answer are boosted by ``boost_for_user_questions``).
3. ``LearningPlanner.estimate_coverage()`` gives an inspectable per-topic
   scorecard so the roadmap is auditable: humans can see *why* Misty
   decided to study "ভেক্টর" next.
4. ``Brain.run_learning_roadmap()`` is the convenience hook: run the plan
   through the existing safety-gated web-learner batch ingestion
   (Phase 35/36) and the post-learning self-assessment loop (Phase 37) —
   the brain studies, then grades itself again.

Everything stays deterministic and rule-based: no LLM, no heuristic
guesswork — only counts, weights, and the gap report produced by the
brain's own self-assessment.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Sequence

DEFAULT_DEPARTMENTS: tuple = (
    ("identity", "training"),
    ("commonsense", "commonsense_layer"),
    ("conversation", "conversation_corpus"),
    ("mathematics", "misty-mathematics"),
    ("physics", "misty-physics"),
    ("literature", "misty-literature"),
    ("culture", "misty-culture"),
)

# Bengali/English topic aliases: gap-case categories -> learnable web topics.
TOPIC_ALIAS: Dict[str, str] = {
    "identity": "Pixline Incorporate Misty",
    "commonsense": "common sense reasoning",
    "conversation": "conversation skills Bengali",
    "mathematics": "mathematics",
    "physics": "physics",
    "literature": "Bengali literature",
    "culture": "Bangladesh culture geography",
    # finer-grained aliases users/benchmarks may emit
    "math": "mathematics",
    "physics_kinematics": "physics",
    "forces": "physics",
    "energy": "physics",
    "algebra": "mathematics",
    "geometry": "mathematics",
    "trigonometry": "mathematics",
    "tagore": "Bengali literature Rabindranath Tagore",
    "nazrul": "Bengali literature Kazi Nazrul Islam",
    "geometry_series": "mathematics",
    "number_theory": "mathematics",
    "bangladesh": "Bangladesh culture geography",
    "india": "India history geography",
    "world": "world geography history",
}

# How much an "incorrect" answer weighs versus an honest "don't know".
_INCORRECT_WEIGHT = 2.0
_HONEST_UNKNOWN_WEIGHT = 1.0


@dataclass
class RoadmapItem:
    """One planned learning stop."""

    rank: int
    topic: str
    reason: str  # human-readable, bilingual safe
    gap_cases: int
    gap_ratio: float  # failed / asked in this topic
    severity: float  # weighted error pressure for this topic
    weight: float  # 0.0-1.0 effort passed to the web learner
    aliases: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rank": self.rank,
            "topic": self.topic,
            "reason": self.reason,
            "gap_cases": self.gap_cases,
            "gap_ratio": round(self.gap_ratio, 4),
            "severity": round(self.severity, 4),
            "weight": round(self.weight, 4),
            "aliases": self.aliases,
        }


@dataclass
class LearningPlan:
    """Deterministic learning roadmap produced from a self-assessment gap report."""

    created_at: float = 0.0
    plan_id: int = 0
    items: List[RoadmapItem] = field(default_factory=list)
    topic_scores: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    plan_id_counter: int = 0

    @property
    def total_planned_topics(self) -> int:
        return len(self.items)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "created_at": self.created_at,
            "plan_id": self.plan_id,
            "total_planned_topics": self.total_planned_topics,
            "items": [item.to_dict() for item in self.items],
            "topic_scores": {
                topic: {**scores, "gap_ratio": round(scores["gap_ratio"], 4)}
                for topic, scores in self.topic_scores.items()
            },
        }


class LearningPlanner:
    """Plans what the brain should learn next from its own gap report.

    Usage::

        planner = LearningPlanner(brain)
        plan = planner.plan_next_topics(max_topics=5, budget=1.0)
    """

    def __init__(self, brain: Any) -> None:
        self.brain = brain
        self._plan_id_counter: int = 0
        self._history: List[LearningPlan] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def plan_next_topics(
        self,
        max_topics: int = 5,
        budget: float = 1.0,
        boost_topics: Sequence[str] = (),
    ) -> LearningPlan:
        """Produce the next learning roadmap.

        * ``max_topics``: how many topics the plan may contain.
        * ``budget``: total effort to distribute across items (sum of
          ``weight`` <= budget).
        * ``boost_topics``: topics the user explicitly asked about (from the
          conversation driver / episodic memory) — these are bumped to the
          front of the plan with extra weight.
        """
        plan = LearningPlan(
            created_at=time.time(),
            plan_id=self._plan_id_counter + 1,
        )
        self._plan_id_counter = plan.plan_id

        gap_report = self.brain.gap_assessor.last_report()
        topic_scores = self._topic_gap_scores(gap_report)
        plan.topic_scores = topic_scores

        scored: List[Dict[str, Any]] = []
        for topic, scores in topic_scores.items():
            if scores["asked"] == 0:
                continue
            recency_decay = scores.get("recency_decay", 0.0)
            priority = scores["gap_ratio"] * (1.0 - recency_decay) + scores["severity"] * 0.25
            scored.append(
                {
                    "topic": topic,
                    "scores": scores,
                    "priority": max(0.0, min(1.0, priority)),
                }
            )

        # Boost user-interest topics to the front.
        boost_set = [t for t in boost_topics if t in topic_scores]
        scored.sort(key=lambda item: (item["topic"] in boost_set, item["priority"]), reverse=True)

        # Distribute the effort budget proportionally to priority.
        total_priority = sum(item["priority"] for item in scored) or 1.0
        items: List[RoadmapItem] = []
        remaining = float(budget)
        for index, entry in enumerate(scored[:max_topics]):
            if total_priority > 0 and len(scored) <= max_topics:
                weight = float(budget) * entry["priority"] / total_priority
            else:
                weight = remaining / max(1, max_topics - index)
            weight = min(weight, remaining)
            remaining -= weight
            scores = entry["scores"]
            reason = self._reason_for_topic(entry["topic"], scores)
            aliases = TOPIC_ALIAS.get(entry["topic"], entry["topic"])
            items.append(
                RoadmapItem(
                    rank=len(items) + 1,
                    topic=entry["topic"],
                    reason=reason,
                    gap_cases=int(scores["incorrect"] + scores["missing"]),
                    gap_ratio=scores["gap_ratio"],
                    severity=scores["severity"],
                    weight=weight,
                    aliases=[aliases] if aliases != entry["topic"] else [],
                )
            )
        plan.items = items
        self._history.append(plan)
        return plan

    def estimate_coverage(self, gap_report: Any = None) -> Dict[str, Any]:
        """Inspectable per-topic scorecard (what the planner sees)."""
        report = gap_report or self.brain.gap_assessor.last_report()
        return {
            topic: {**scores, "gap_ratio": round(scores["gap_ratio"], 4)}
            for topic, scores in self._topic_gap_scores(report).items()
        }

    @property
    def history(self) -> List[LearningPlan]:
        return self._history

    def last_plan(self) -> LearningPlan | None:
        return self._history[-1] if self._history else None

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _topic_gap_scores(self, gap_report: Any) -> Dict[str, Dict[str, Any]]:
        """Aggregate the gap report per topic: asked/failed/severity/recency."""
        scores: Dict[str, Dict[str, Any]] = {}
        entries = getattr(gap_report, "entries", []) or []
        # Recency signal: later entries = more recent assessment.
        total = len(entries)
        for position, entry in enumerate(entries):
            topic = (entry.topic or "unknown").strip().lower()
            bucket = scores.setdefault(
                topic,
                {
                    "asked": 0,
                    "known": 0,
                    "incorrect": 0,
                    "unknown_honest": 0,
                    "missing": 0,
                    "recency_decay": 0.0,
                    "latest_position": -1,
                },
            )
            bucket["asked"] += 1
            status = entry.status or "missing"
            if status == "known":
                bucket["known"] += 1
            elif status == "incorrect":
                bucket["incorrect"] += 1
            elif status == "unknown_honest":
                bucket["unknown_honest"] += 1
            else:
                bucket["missing"] += 1
            bucket["latest_position"] = position
        for bucket in scores.values():
            asked = bucket["asked"] or 1
            bucket["gap_ratio"] = (bucket["incorrect"] + bucket["missing"]) / asked
            bucket["severity"] = (
                bucket["incorrect"] * _INCORRECT_WEIGHT
                + bucket["unknown_honest"] * _HONEST_UNKNOWN_WEIGHT
                + bucket["missing"]
            ) / asked
            # Recent topics got attention; decay them a little so the brain
            # does not over-study one department in a row.
            bucket["recency_decay"] = 0.15 * (bucket["latest_position"] + 1) / max(1, total)
        return scores

    @staticmethod
    def _reason_for_topic(topic: str, scores: Dict[str, Any]) -> str:
        failed = int(scores["incorrect"] + scores["missing"])
        asked = scores["asked"]
        if scores["incorrect"] >= scores["unknown_honest"]:
            return (
                f"Topic '{topic}': {failed}/{asked} cases answered incorrectly or not at all; "
                "fixing wrong answers has the highest priority."
            )
        if failed:
            return f"Topic '{topic}': {failed}/{asked} cases are not yet known; learning will close the gap."
        return f"Topic '{topic}': no failures detected ({asked} asked); kept as maintenance stop."
