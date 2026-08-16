"""
Reinforcement Learning.

Simple RL agent that learns from reward/punishment signals.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ReinforcementLearner:
    """Simple reinforcement learner using Q-value estimation."""

    q_values: Dict[str, Dict[str, float]] = field(default_factory=dict)
    learning_rate: float = 0.1
    discount_factor: float = 0.9
    exploration_rate: float = 0.2

    def get_value(self, state: str, action: str) -> float:
        """Get the estimated value of a state-action pair."""
        return self.q_values.get(state, {}).get(action, 0.0)

    def get_best_action(self, state: str, available_actions: List[str]) -> Optional[str]:
        """Select the best action for a state."""
        if not available_actions:
            return None

        best_action = available_actions[0]
        best_value = self.get_value(state, best_action)

        for action in available_actions[1:]:
            value = self.get_value(state, action)
            if value > best_value:
                best_value = value
                best_action = action

        return best_action

    def update(
        self,
        state: str,
        action: str,
        reward: float,
        next_state: Optional[str] = None,
        next_actions: Optional[List[str]] = None,
    ) -> float:
        """Update Q-value based on received reward."""
        if state not in self.q_values:
            self.q_values[state] = {}

        current_q = self.q_values[state].get(action, 0.0)

        future_value = 0.0
        if next_state and next_actions:
            best_next = self.get_best_action(next_state, next_actions)
            if best_next:
                future_value = self.get_value(next_state, best_next)

        target = reward + self.discount_factor * future_value
        new_q = current_q + self.learning_rate * (target - current_q)
        self.q_values[state][action] = new_q

        return new_q

    def decay_exploration(self, min_rate: float = 0.01) -> None:
        """Reduce exploration rate over time."""
        self.exploration_rate = max(min_rate, self.exploration_rate * 0.99)

    def __repr__(self) -> str:
        total_entries = sum(len(v) for v in self.q_values.values())
        return f"ReinforcementLearner(states={len(self.q_values)}, entries={total_entries})"
