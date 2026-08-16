"""
Reward Region Module.

Implements a RewardRegion that models the dopaminergic reward system.
Tracks reward signals, computes reward prediction errors, and provides
reinforcement signals for learning in connected regions.
"""

from typing import List

import numpy as np

from brain.regions.region import BrainRegion


class RewardRegion(BrainRegion):
    """Reward/dopamine system for reinforcement signals.

    Models a simplified dopaminergic reward system that:
      - Receives reward signals from the environment.
      - Maintains a running estimate of expected reward (baseline).
      - Computes reward prediction errors (RPE = actual - expected).
      - Modulates its neural output based on reward signals.

    The reward prediction error signal can be used by other regions
    to implement reinforcement-based plasticity.

    Attributes:
        reward_signal: Current reward value.
        reward_baseline: Running average of received rewards.
        prediction_error: Most recent reward prediction error.
        baseline_decay: Exponential decay rate for reward baseline.
        reward_history: Recent reward values.
    """

    def __init__(
        self,
        name: str = "reward",
        size: int = 128,
        baseline_decay: float = 0.95,
        excitatory_ratio: float = 0.9,
        threshold: float = 1.0,
        decay: float = 0.9,
        refractory_period: int = 2,
    ) -> None:
        """Initialize a reward region.

        Args:
            name: Human-readable name for the region.
            size: Number of neurons in the reward population.
            baseline_decay: Exponential decay for reward baseline updates.
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
        self.baseline_decay: float = baseline_decay
        self.reward_signal: float = 0.0
        self.reward_baseline: float = 0.0
        self.prediction_error: float = 0.0
        self.reward_history: List[float] = []

    def deliver_reward(self, amount: float) -> None:
        """Deliver a reward signal to the region.

        Updates the reward signal, computes the prediction error
        (difference from baseline), and updates the baseline using
        exponential moving average.

        Args:
            amount: Reward amount. Positive for reward, negative for punishment.
        """
        self.reward_signal = amount

        # Compute reward prediction error
        self.prediction_error = amount - self.reward_baseline

        # Update baseline with exponential moving average
        self.reward_baseline = self.baseline_decay * self.reward_baseline + (1.0 - self.baseline_decay) * amount

        # Record history
        self.reward_history.append(amount)

    def get_reward_signal(self) -> np.ndarray:
        """Get the current reward signal as a neural current pattern.

        Converts the scalar reward prediction error into a spatially
        distributed current pattern that can be used to modulate
        activity in connected regions.

        Positive prediction errors produce excitatory currents,
        negative prediction errors produce inhibitory currents.

        Returns:
            Array of shape (size,) with reward-modulated currents.
        """
        # Scale prediction error into current
        # Distribute uniformly across the population with some structure
        signal = np.full(self.size, self.prediction_error, dtype=np.float64)

        # Add spatial structure: excitatory neurons carry positive signals,
        # inhibitory neurons carry negative signals
        signal *= self.population.type_array.astype(np.float64)

        # Scale by threshold for appropriate magnitude
        signal *= self.population.threshold[0]

        return signal

    def step(self) -> np.ndarray:
        """Advance the reward region with reward-modulated activity.

        Injects reward-derived currents into the population before
        stepping. The reward signal decays after each step.

        Returns:
            Boolean array of shape (size,) indicating which neurons fired.
        """
        # Inject reward signal as current
        if abs(self.reward_signal) > 1e-10:
            reward_current = self.get_reward_signal()
            self.input_buffer += reward_current

        # Step the population
        spikes = super().step()

        # Decay reward signal over time
        self.reward_signal *= 0.8

        return spikes

    def reset(self) -> None:
        """Reset the reward region to initial state."""
        super().reset()
        self.reward_signal = 0.0
        self.reward_baseline = 0.0
        self.prediction_error = 0.0
        self.reward_history.clear()

    def __repr__(self) -> str:
        return (
            f"RewardRegion(name='{self.name}', size={self.size}, "
            f"baseline={self.reward_baseline:.4f}, "
            f"prediction_error={self.prediction_error:.4f})"
        )
