"""
Phase 6: Goal Manager — hierarchical goal-driven behavior.

Extends the simple Planner with goal-driven behavior:
- Hierarchical goal decomposition: complex goals are broken into
  sub-goals, which can themselves be decomposed (bounded depth).
- Multi-step plans with progress tracking per goal.
- Goal prioritization: the planner picks the highest-priority
  non-terminal goal each cycle.
- Automatic pruning of completed terminal goals (bounded registry).

Design constraints:
- Pure Python (no LLM, no external ML model).
- All structures bounded so memory usage never grows unbounded.
- Serializable; state survives reloads from JSON.
"""

from __future__ import annotations

import time as time_module
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class GoalStatus(str, Enum):
    """Possible states of a goal."""

    PENDING = "pending"
    ACTIVE = "active"
    ACHIEVED = "achieved"
    FAILED = "failed"
    ABANDONED = "abandoned"


# Templates for decomposing the intents MISTY actually encounters.
# Each template maps an intent to a sequence of plan steps.
INTENT_STEP_TEMPLATES: Dict[str, List[str]] = {
    "name_declaration": [
        "interpret_input",
        "extract_entity",
        "store_identity",
    ],
    "relation_declaration": [
        "interpret_input",
        "resolve_entities",
        "store_relation",
    ],
    "query_who": [
        "interpret_input",
        "recall_relevant",
        "activate_associations",
        "compose_answer",
    ],
    "query_what": [
        "interpret_input",
        "recall_relevant",
        "activate_associations",
        "compose_answer",
    ],
    "greeting": [
        "interpret_input",
        "compose_greeting",
    ],
    "teach": [
        "interpret_input",
        "store_fact",
        "strengthen_association",
    ],
    "statement": [
        "interpret_input",
        "store_fact",
    ],
    "correction": [
        "interpret_input",
        "update_fact",
    ],
    "continuation": [
        "interpret_input",
        "recall_topic",
        "continue_topic",
    ],
}


@dataclass
class PlanStep:
    """A single step in a goal plan."""

    action: str
    completed: bool = False
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Goal:
    """A goal the brain is pursuing, optionally with sub-goals.

    Goals can be hierarchical: a parent goal keeps an ordered list of
    child goal ids, and the parent is only achieved when all children
    have reached a terminal achieved state.
    """

    description: str
    intent: str = "unknown"
    priority: float = 0.5
    goal_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    status: GoalStatus = GoalStatus.PENDING
    parent_id: str | None = None
    sub_goal_ids: List[str] = field(default_factory=list)
    steps: List[PlanStep] = field(default_factory=list)
    progress: float = 0.0
    created_at: float = field(default_factory=time_module.time)
    context: Dict[str, Any] = field(default_factory=dict)

    def activate(self) -> None:
        self.status = GoalStatus.ACTIVE

    def advance_step(self) -> None:
        """Complete the current plan step and recompute progress."""
        for step in self.steps:
            if not step.completed:
                step.completed = True
                break
        done = sum(1 for s in self.steps if s.completed)
        total = len(self.steps) or 1
        self.progress = min(done / total, 1.0)

    def achieve(self) -> None:
        self.progress = 1.0
        self.status = GoalStatus.ACHIEVED

    def fail(self, reason: str = "") -> None:
        self.status = GoalStatus.FAILED
        self.context["failure_reason"] = reason

    def abandon(self) -> None:
        self.status = GoalStatus.ABANDONED

    @property
    def is_terminal(self) -> bool:
        return self.status in (
            GoalStatus.ACHIEVED,
            GoalStatus.FAILED,
            GoalStatus.ABANDONED,
        )

    def current_step(self) -> PlanStep | None:
        """Next incomplete plan step, if any."""
        for step in self.steps:
            if not step.completed:
                return step
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "description": self.description,
            "intent": self.intent,
            "priority": self.priority,
            "status": self.status.value,
            "parent_id": self.parent_id,
            "sub_goal_ids": list(self.sub_goal_ids),
            "steps": [{"action": s.action, "completed": s.completed, "parameters": s.parameters} for s in self.steps],
            "progress": self.progress,
            "created_at": self.created_at,
            "context": dict(self.context),
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> Goal:
        goal = Goal(
            description=data.get("description", ""),
            intent=data.get("intent", "unknown"),
            priority=data.get("priority", 0.5),
            goal_id=data.get("goal_id", uuid.uuid4().hex[:8]),
            status=GoalStatus(data.get("status", "pending")),
            parent_id=data.get("parent_id"),
            sub_goal_ids=list(data.get("sub_goal_ids", [])),
            progress=data.get("progress", 0.0),
            created_at=data.get("created_at", time_module.time()),
        )
        goal.steps = [
            PlanStep(
                action=s.get("action", ""), completed=s.get("completed", False), parameters=s.get("parameters", {})
            )
            for s in data.get("steps", [])
        ]
        goal.context = dict(data.get("context", {}))
        # Recompute progress from the restored steps so completion state
        # always matches the derived progress fraction.
        done = sum(1 for s in goal.steps if s.completed)
        total = len(goal.steps) or 1
        goal.progress = min(done / total, 1.0)
        return goal


class GoalManager:
    """Hierarchical goal-driven planner with progress tracking.

    Responsibilities:
    - Decompose a top-level goal (triggered by an intent) into a plan of
      steps and optional child goals.
    - Track per-goal progress and pick the highest-priority active goal.
    - Prune terminal goals when the registry exceeds its capacity.
    """

    def __init__(
        self,
        max_goals: int = 64,
        max_depth: int = 3,
        max_steps: int = 8,
    ) -> None:
        self.max_goals = max_goals
        self.max_depth = max_depth
        self.max_steps = max_steps
        self.goals: Dict[str, Goal] = {}
        self._goal_counter = 0

    # ------------------------------------------------------------------
    # Goal creation and decomposition
    # ------------------------------------------------------------------

    def _next_goal_id(self) -> str:
        self._goal_counter += 1
        return f"g{self._goal_counter:04d}"

    def decompose(self, intent: str, description: str, priority: float = 0.5) -> Goal:
        """Create a top-level goal decomposed into plan steps for the intent.

        Unknown intents get a single acknowledge step. Decomposition is
        bounded by max_depth / max_steps so plan generation stays cheap.
        """
        steps: List[str] = INTENT_STEP_TEMPLATES.get(intent, ["acknowledge"])
        steps = steps[: self.max_steps]
        goal = Goal(
            goal_id=self._next_goal_id(),
            description=description,
            intent=intent,
            priority=priority,
            steps=[PlanStep(action=a) for a in steps],
        )
        self.add_goal(goal)
        goal.activate()
        return goal

    def decompose_hierarchy(self, intent: str, description: str, priority: float = 0.5) -> Goal:
        """Create a goal with child goals (one per plan segment)."""
        steps: List[str] = INTENT_STEP_TEMPLATES.get(intent, ["acknowledge"])
        steps = steps[: self.max_steps]
        # Split steps into at most two segments for a shallow hierarchy.
        split = len(steps) // 2
        segments = [steps[:split] or steps[:1], steps[split:]]
        segments = [seg for seg in segments if seg]

        parent = Goal(
            goal_id=self._next_goal_id(),
            description=description,
            intent=intent,
            priority=priority,
        )
        self.add_goal(parent)
        for seg in segments:
            child = Goal(
                goal_id=self._next_goal_id(),
                description=f"{description} ({seg[0]})",
                intent=intent,
                priority=priority,
                parent_id=parent.goal_id,
                steps=[PlanStep(action=a) for a in seg],
            )
            self.add_goal(child)
            child.activate()
            parent.sub_goal_ids.append(child.goal_id)
        parent.activate()
        return parent

    def add_goal(self, goal: Goal) -> None:
        self.goals[goal.goal_id] = goal
        if len(self.goals) > self.max_goals:
            # Prune the oldest terminal goal; otherwise the oldest goal.
            terminals = [g for g in self.goals.values() if g.is_terminal]
            victim = min(terminals, key=lambda g: g.created_at) if terminals else None
            if victim is None:
                victim = min(self.goals.values(), key=lambda g: g.created_at)
            self.remove_goal(victim.goal_id)

    def remove_goal(self, goal_id: str) -> None:
        self.goals.pop(goal_id, None)

    # ------------------------------------------------------------------
    # Progress tracking
    # ------------------------------------------------------------------

    def advance_goal(self, goal_id: str) -> Dict[str, Any]:
        """Advance the next step of the given goal and return status."""
        goal = self.goals.get(goal_id)
        if goal is None or goal.is_terminal:
            return {"goal_id": goal_id, "done": True, "progress": 0.0}
        goal.advance_step()
        step = goal.current_step()
        if step is None:
            # All steps completed — check children before achieving.
            children_ok = all(
                self.goals[cid].status == GoalStatus.ACHIEVED for cid in goal.sub_goal_ids if cid in self.goals
            )
            if goal.sub_goal_ids and not children_ok:
                return {
                    "goal_id": goal_id,
                    "done": False,
                    "progress": goal.progress,
                    "waiting_on_children": True,
                }
            goal.achieve()
        return {"goal_id": goal_id, "done": goal.is_terminal, "progress": goal.progress}

    def active_goal(self) -> Goal | None:
        """Highest-priority non-terminal goal, preferring ACTIVE ones."""
        pending = [g for g in self.goals.values() if not g.is_terminal]
        if not pending:
            return None
        return max(pending, key=lambda g: (g.status == GoalStatus.ACTIVE, g.priority))

    def leaf_active_goal(self) -> Goal | None:
        """The deepest (child-most) non-terminal goal, by depth then priority.

        Root goals only achieve once their children are done, so plan
        progress is actually made by advancing leaf goals first.
        """
        pending = [g for g in self.goals.values() if not g.is_terminal]
        if not pending:
            return None

        def depth(goal: Goal) -> int:
            level = 0
            node = goal
            while node.parent_id in self.goals:
                node = self.goals[node.parent_id]
                level += 1
            return level

        return max(pending, key=lambda g: (g.status == GoalStatus.ACTIVE, depth(g), g.priority))

    def root_goal(self, goal_id: str) -> Goal | None:
        """Walk up to the top-level parent goal of a goal."""
        goal = self.goals.get(goal_id)
        while goal is not None and goal.parent_id in self.goals:
            goal = self.goals[goal.parent_id]
        return goal

    def stats(self) -> Dict[str, int]:
        by_status: Dict[str, int] = {s.value: 0 for s in GoalStatus}
        for g in self.goals.values():
            by_status[g.status.value] += 1
        return by_status

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goals": {gid: g.to_dict() for gid, g in self.goals.items()},
        }

    def load(self, data: Dict[str, Any]) -> None:
        self.goals = {gid: Goal.from_dict(g) for gid, g in data.get("goals", {}).items()}

    def reset(self) -> None:
        self.goals.clear()
