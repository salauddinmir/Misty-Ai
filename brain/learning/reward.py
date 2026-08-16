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

    # Emotional valence modifier applied on top of every reward.
    # Positive emotions (satisfaction, curiosity) boost learning signals,
    # while negative emotions (frustration) dampen them, tying the reward
    # channel to the emotion engine instead of remaining static.
    valence_modifier: float = 0.0

    # Running streak of consecutive positive rewards — used by the
    # emotion engine and reflection layer as a confidence signal.
    positive_streak: int = 0

    def _apply_valence(self, reward: float) -> float:
        return reward * (1.0 + max(-0.5, min(0.5, self.valence_modifier)))

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

        reward = self._apply_valence(reward)
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

        # Track consecutive positive rewards as a confidence streak.
        if reward > 0.0:
            self.positive_streak += 1
        else:
            self.positive_streak = 0

    @property
    def average_reward(self) -> float:
        """Average recent reward."""
        if not self.reward_history:
            return 0.0
        return sum(self.reward_history) / len(self.reward_history)

    @property
    def recent_reward(self) -> float:
        """Recency-weighted average of the last rewards.

        More recent rewards count more (linearly increasing weights), so the
        value reflects how the brain is doing right now rather than ever.
        """
        history = self.reward_history[-20:]
        if not history:
            return 0.0
        weights = [i + 1 for i in range(len(history))]
        total_weight = sum(weights)
        return sum(r * w for r, w in zip(history, weights, strict=False)) / total_weight

    def __repr__(self) -> str:
        return f"RewardSignal(total={self.total_reward:.3f}, avg={self.average_reward:.3f})"
