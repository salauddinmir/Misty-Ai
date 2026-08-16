"""
Plan Evaluation.

Evaluates plans based on expected outcomes and historical success rates.
"""

from dataclasses import dataclass, field
from typing import Dict

from brain.planner.planner import Plan


@dataclass
class PlanEvaluator:
    """Evaluates plan quality and tracks outcomes."""

    action_success_rates: Dict[str, float] = field(default_factory=dict)
    action_costs: Dict[str, float] = field(default_factory=dict)

    def evaluate_plan(self, plan: Plan) -> float:
        """Evaluate a plan's expected quality."""
        if not plan.steps:
            return 0.0

        success_prob = 1.0
        for step in plan.steps:
            rate = self.action_success_rates.get(step.action, 0.5)
            success_prob *= rate

        efficiency = 1.0 / (1.0 + len(plan.steps) * 0.1)
        return success_prob * 0.7 + efficiency * 0.3

    def record_outcome(self, action: str, success: bool) -> None:
        """Record the outcome of an action for future evaluation."""
        current_rate = self.action_success_rates.get(action, 0.5)
        alpha = 0.3
        new_rate = alpha * (1.0 if success else 0.0) + (1.0 - alpha) * current_rate
        self.action_success_rates[action] = new_rate

    def __repr__(self) -> str:
        return f"PlanEvaluator(tracked_actions={len(self.action_success_rates)})"
