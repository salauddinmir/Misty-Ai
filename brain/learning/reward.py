"""
Reward Signal Generation.

Generates reward signals based on goal achievement and user feedback.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class RewardSignal:
    """Generates and tracks reward signals for learning."""

    total_reward: float = 0.0
    reward_history: List[float] = field(default_factory=list)
    max_history: int = 100

    def compute_reward(
        self,
        goal_achieved: bool = False,
        prediction_correct: bool = False,
        user_satisfaction: float = 0.0,
    ) -> float:
        """Compute a reward signal based on multiple factors."""
        reward = 0.0

        if goal_achieved:
            reward += 1.0
        if prediction_correct:
            reward += 0.3
        reward += user_satisfaction * 0.5

        self._record(reward)
        return reward

    def generate_curiosity_reward(self, novelty: float) -> float:
        """Generate intrinsic reward from novelty/curiosity."""
        reward = novelty * 0.5
        self._record(reward)
        return reward

    def generate_penalty(self, severity: float = 0.5) -> float:
        """Generate a negative reward (punishment)."""
        reward = -severity
        self._record(reward)
        return reward

    def _record(self, reward: float) -> None:
        """Record a reward in history."""
        self.total_reward += reward
        self.reward_history.append(reward)
        if len(self.reward_history) > self.max_history:
            self.reward_history.pop(0)

    @property
    def average_reward(self) -> float:
        """Average recent reward."""
        if not self.reward_history:
            return 0.0
        return sum(self.reward_history) / len(self.reward_history)

    def __repr__(self) -> str:
        return f"RewardSignal(total={self.total_reward:.3f}, avg={self.average_reward:.3f})"
