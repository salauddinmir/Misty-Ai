"""
Phase 49: Autonomous Learning Scheduler.

``AutonomousScheduler`` orchestrates the brain's background self-improvement.
It hooks into the reflection tick to periodically:
1. Run a Gap Assessment (if stale).
2. Generate a Learning Roadmap (LearningPlanner).
3. Execute one high-priority Web Search Learning task (WebSearchLearner).
4. Log activities for the brain monitor.

This transforms MISTY from a reactive learner into an active expert-seeker.
"""

import time
from dataclasses import dataclass
from typing import Any, Dict, List

_SCHEDULER_LOG_MAX = 50
_MIN_GAP_SCORE_FOR_LEARNING = 0.05
_LEARNING_COOLDOWN_SECONDS = 3600  # 1 hour between autonomous learning runs
_PLANNING_COOLDOWN_SECONDS = 7200  # 2 hours between roadmap updates


@dataclass
class SchedulerEvent:
    """A record of an autonomous learning action."""

    timestamp: float
    action: str  # "assess", "plan", "learn", "skip"
    topic: str | None = None
    detail: str = ""
    success: bool = True


class AutonomousScheduler:
    """Orchestrates background gap-assessment and web-learning."""

    def __init__(self, brain: Any) -> None:
        self._brain = brain
        self._last_assess_time = 0.0
        self._last_plan_time = 0.0
        self._last_learn_time = 0.0
        self._events: List[SchedulerEvent] = []
        self._total_topics_learned = 0

    async def tick(self) -> Dict[str, Any]:
        """Run one autonomous learning step if cooldowns allow.

        Called by the Brain's reflection tick.
        """
        now = time.time()
        result = {"action": "idle", "topic": None}

        # 1. Periodically update the roadmap (assessment + planning)
        if now - self._last_plan_time > _PLANNING_COOLDOWN_SECONDS:
            await self._update_roadmap()
            result["action"] = "planned"
            self._last_plan_time = now

        # 2. Periodically execute the top item from the roadmap
        if now - self._last_learn_time > _LEARNING_COOLDOWN_SECONDS:
            plan = self._brain.learning_planner.last_plan()
            if plan and plan.items:
                # Pick the highest ranked item not recently learned
                target = plan.items[0]
                learned = await self._learn_topic(target.topic)
                if learned:
                    result["action"] = "learned"
                    result["topic"] = target.topic
                    self._last_learn_time = now
            else:
                # No plan? Force an assessment next tick
                self._last_plan_time = 0.0

        return result

    def summary(self) -> Dict[str, Any]:
        """State snapshot for the brain monitor."""
        return {
            "enabled": True,
            "total_topics_learned": self._total_topics_learned,
            "last_learn_time": self._last_learn_time,
            "next_learn_in": max(0, _LEARNING_COOLDOWN_SECONDS - (time.time() - self._last_learn_time)),
            "recent_events": [
                {
                    "time": e.timestamp,
                    "action": e.action,
                    "topic": e.topic,
                    "detail": e.detail,
                    "success": e.success,
                }
                for e in self._events[-5:]
            ],
        }

    # ------------------------------------------------------------------
    # Internal actions
    # ------------------------------------------------------------------

    async def _update_roadmap(self) -> None:
        """Trigger gap assessment and plan generation."""
        try:
            # Note: Assessment usually requires case-sets; if empty, it
            # relies on existing gap history or simple coverage.
            # Here we just trigger a new plan based on existing gap data.
            self._brain.learning_planner.plan_next_topics(max_topics=5)
            self._log("plan", detail="updated autonomous roadmap")
        except Exception as e:
            self._log("plan", success=False, detail=str(e))

    async def _learn_topic(self, topic: str) -> bool:
        """Execute web search learning for a specific topic."""
        try:
            # Bounded ingest
            learn_result = await self._brain.web_learner.ingest(topic, max_facts=6)
            success = learn_result.facts_stored > 0
            detail = f"stored {learn_result.facts_stored} facts"
            if not success and learn_result.errors:
                detail = f"error: {learn_result.errors[0]}"

            self._log("learn", topic=topic, detail=detail, success=success)
            if success:
                self._total_topics_learned += 1
            return success
        except Exception as e:
            self._log("learn", topic=topic, success=False, detail=str(e))
            return False

    def _log(
        self,
        action: str,
        topic: str | None = None,
        detail: str = "",
        success: bool = True,
    ) -> None:
        event = SchedulerEvent(
            timestamp=time.time(),
            action=action,
            topic=topic,
            detail=detail,
            success=success,
        )
        self._events.append(event)
        if len(self._events) > _SCHEDULER_LOG_MAX:
            self._events = self._events[-_SCHEDULER_LOG_MAX // 2 :]
