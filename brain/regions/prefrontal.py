"""
Prefrontal Region Module.

Implements a PrefrontalRegion responsible for goal management,
planning, and decision-making. Maintains a goal representation
and evaluates progress toward it using neural population dynamics.
"""

from typing import List

import numpy as np

from brain.regions.region import BrainRegion


class PrefrontalRegion(BrainRegion):
    """Prefrontal cortex region for planning and goal management.

    Maintains a goal pattern that biases the region's neural activity,
    implements decision-making through competitive dynamics, and
    evaluates progress toward goals by comparing current activity
    to the goal representation.

    The goal management process:
      1. Set a goal pattern that represents the desired state.
      2. Each step() biases activity toward the goal.
      3. Evaluate progress by computing similarity between
         current activity and the goal.

    Attributes:
        goal_pattern: Current goal representation (None if no goal set).
        goal_strength: How strongly the goal biases neural activity.
        decision_threshold: Threshold for making a binary decision.
        progress_history: Recent progress measurements.
    """

    def __init__(
        self,
        name: str = "prefrontal",
        size: int = 256,
        goal_strength: float = 0.5,
        decision_threshold: float = 0.6,
        excitatory_ratio: float = 0.8,
        threshold: float = 1.0,
        decay: float = 0.85,
        refractory_period: int = 2,
    ) -> None:
        """Initialize a prefrontal region.

        Args:
            name: Human-readable name for the region.
            size: Number of neurons in the prefrontal population.
            goal_strength: Strength of goal-directed bias (0-1).
            decision_threshold: Activity threshold for decisions.
            excitatory_ratio: Fraction of excitatory neurons.
            threshold: Firing threshold.
            decay: Membrane decay rate.
            refractory_period: Refractory period in timesteps.
        """
        super().__init__(
            name=name,
            size=size,
            excitatory_ratio=excitatory_ratio,
            threshold=threshold,
            decay=decay,
            refractory_period=refractory_period,
        )
        self.goal_strength: float = goal_strength
        self.decision_threshold: float = decision_threshold
        self.goal_pattern: np.ndarray | None = None
        self.progress_history: List[float] = []
        self._activity_accumulator: np.ndarray = np.zeros(size, dtype=np.float64)
        self._accumulator_steps: int = 0

    def set_goal(self, goal_pattern: np.ndarray) -> None:
        """Set the current goal pattern.

        The goal pattern biases neural activity during each step(),
        guiding the population toward goal-relevant firing.

        Args:
            goal_pattern: Array representing the goal state. Will be
                         flattened and resized to match the region's size.
        """
        flat = np.asarray(goal_pattern, dtype=np.float64).flatten()
        self.goal_pattern = np.zeros(self.size, dtype=np.float64)
        n = min(len(flat), self.size)
        self.goal_pattern[:n] = flat[:n]

        # Normalize goal pattern
        norm = np.linalg.norm(self.goal_pattern)
        if norm > 1e-10:
            self.goal_pattern = self.goal_pattern / norm

        # Reset progress tracking for new goal
        self.progress_history.clear()
        self._activity_accumulator[:] = 0.0
        self._accumulator_steps = 0

    def clear_goal(self) -> None:
        """Clear the current goal."""
        self.goal_pattern = None
        self.progress_history.clear()
        self._activity_accumulator[:] = 0.0
        self._accumulator_steps = 0

    def evaluate_progress(self) -> float:
        """Evaluate progress toward the current goal.

        Computes cosine similarity between the accumulated activity
        pattern and the goal pattern. A value of 1.0 means perfect
        alignment; 0.0 means no progress.

        Returns:
            Float between -1.0 and 1.0 representing progress toward goal.
            Returns 0.0 if no goal is set or no steps have occurred.
        """
        if self.goal_pattern is None or self._accumulator_steps == 0:
            return 0.0

        # Normalize accumulated activity
        activity = self._activity_accumulator / self._accumulator_steps
        activity_norm = np.linalg.norm(activity)
        goal_norm = np.linalg.norm(self.goal_pattern)

        if activity_norm < 1e-10 or goal_norm < 1e-10:
            return 0.0

        # Cosine similarity
        similarity = float(np.dot(activity, self.goal_pattern) / (activity_norm * goal_norm))

        self.progress_history.append(similarity)
        return similarity

    def step(self) -> np.ndarray:
        """Advance the prefrontal region with goal-directed bias.

        Adds goal-directed current to the input buffer before
        stepping the neural population. Tracks activity for
        progress evaluation.

        Returns:
            Boolean array of shape (size,) indicating which neurons fired.
        """
        # Add goal bias to input
        if self.goal_pattern is not None:
            goal_current = self.goal_pattern * self.goal_strength * self.population.threshold[0]
            self.input_buffer += goal_current

        # Step the population
        spikes = super().step()

        # Track activity
        self._activity_accumulator += spikes.astype(np.float64)
        self._accumulator_steps += 1

        return spikes

    def make_decision(self) -> bool:
        """Make a binary decision based on current firing rate.

        Returns True if the population's recent firing rate exceeds
        the decision threshold, indicating enough evidence has
        accumulated for a positive decision.

        Returns:
            Boolean decision based on activity level.
        """
        return self.get_firing_rate() >= self.decision_threshold

    def __repr__(self) -> str:
        has_goal = self.goal_pattern is not None
        return f"PrefrontalRegion(name='{self.name}', size={self.size}, has_goal={has_goal})"
