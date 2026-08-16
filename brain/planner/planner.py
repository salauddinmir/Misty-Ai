"""
Simple Goal-Based Planner.

Creates and manages plans to achieve goals.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List

from brain.planner.goals import Goal, GoalStatus


@dataclass
class PlanStep:
    """A single step in a plan."""

    action: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    completed: bool = False


@dataclass
class Plan:
    """A sequence of steps to achieve a goal."""

    goal_id: str
    steps: List[PlanStep] = field(default_factory=list)
    current_step: int = 0

    @property
    def is_complete(self) -> bool:
        """Whether all steps have been completed."""
        return self.current_step >= len(self.steps)

    def next_step(self) -> PlanStep | None:
        """Get the next step to execute."""
        if self.is_complete:
            return None
        return self.steps[self.current_step]

    def advance(self) -> None:
        """Mark current step as complete and move to next."""
        if not self.is_complete:
            self.steps[self.current_step].completed = True
            self.current_step += 1


@dataclass
class Planner:
    """Simple goal-based planner."""

    goals: Dict[str, Goal] = field(default_factory=dict)
    plans: Dict[str, Plan] = field(default_factory=dict)

    def add_goal(self, goal: Goal) -> None:
        """Add a goal to the planner."""
        self.goals[goal.goal_id] = goal

    def create_goal(
        self,
        description: str,
        goal_type: str = "respond",
        priority: float = 0.5,
    ) -> Goal:
        """Create and add a new goal."""
        goal = Goal(description=description, goal_type=goal_type, priority=priority)
        self.add_goal(goal)
        return goal

    def plan_for_goal(self, goal: Goal) -> Plan:
        """Generate a plan for a goal."""
        steps: List[PlanStep] = []

        if goal.goal_type == "respond":
            steps = [
                PlanStep(action="interpret_input", parameters=goal.context),
                PlanStep(action="recall_relevant", parameters=goal.context),
                PlanStep(action="generate_response", parameters=goal.context),
            ]
        elif goal.goal_type == "learn":
            steps = [
                PlanStep(action="parse_input", parameters=goal.context),
                PlanStep(action="store_knowledge", parameters=goal.context),
                PlanStep(action="consolidate", parameters=goal.context),
            ]
        elif goal.goal_type == "recall":
            steps = [
                PlanStep(action="activate_concepts", parameters=goal.context),
                PlanStep(action="search_graph", parameters=goal.context),
                PlanStep(action="retrieve_answer", parameters=goal.context),
            ]
        else:
            steps = [PlanStep(action="process_input", parameters=goal.context)]

        plan = Plan(goal_id=goal.goal_id, steps=steps)
        self.plans[goal.goal_id] = plan
        goal.activate()
        return plan

    def get_current_plan(self) -> Plan | None:
        """Get the plan for the highest-priority active goal."""
        active_goals = [g for g in self.goals.values() if g.status == GoalStatus.ACTIVE]
        if not active_goals:
            return None

        active_goals.sort(key=lambda g: g.priority, reverse=True)
        return self.plans.get(active_goals[0].goal_id)

    def complete_goal(self, goal_id: str) -> None:
        """Mark a goal and its plan as complete."""
        if goal_id in self.goals:
            self.goals[goal_id].achieve()

    def __repr__(self) -> str:
        active = sum(1 for g in self.goals.values() if g.status == GoalStatus.ACTIVE)
        return f"Planner(goals={len(self.goals)}, active={active})"
