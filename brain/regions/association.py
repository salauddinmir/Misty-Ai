"""
Association Region Module.

Implements an AssociationRegion that links concepts and performs
pattern completion using recurrent neural dynamics. This region
stores attractor patterns and can reconstruct full patterns from
partial or noisy cues.
"""

from typing import List, Optional

import numpy as np

from brain.regions.region import BrainRegion


class AssociationRegion(BrainRegion):
    """Association cortex region for linking concepts and pattern completion.

    Uses recurrent dynamics within the neuron population to implement
    attractor-like behavior. Stored patterns act as attractors: when
    a partial pattern is presented, the recurrent dynamics settle into
    the closest stored pattern.

    The pattern completion process:
      1. Store patterns as weight modifications (Hebbian-style).
      2. Present partial input as current injection.
      3. Run recurrent steps until activity stabilizes.
      4. Read out the final spike pattern as the completed result.

    Attributes:
        stored_patterns: List of stored pattern arrays.
        recurrent_weight: Strength of recurrent connections.
        completion_steps: Number of recurrent steps for pattern completion.
    """

    def __init__(
        self,
        name: str = "association",
        size: int = 512,
        recurrent_weight: float = 0.3,
        completion_steps: int = 10,
        excitatory_ratio: float = 0.8,
        threshold: float = 1.0,
        decay: float = 0.85,
        refractory_period: int = 2,
    ) -> None:
        """Initialize an association region.

        Args:
            name: Human-readable name for the region.
            size: Number of neurons in the association population.
            recurrent_weight: Strength multiplier for recurrent connections.
            completion_steps: Number of recurrent steps for pattern completion.
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
        self.recurrent_weight: float = recurrent_weight
        self.completion_steps: int = completion_steps
        self.stored_patterns: List[np.ndarray] = []

        # Hebbian weight matrix for recurrent connections (dense for simplicity)
        self._recurrent_weights: np.ndarray = np.zeros(
            (size, size), dtype=np.float64
        )

    def store_pattern(self, pattern: np.ndarray) -> None:
        """Store a pattern using Hebbian learning.

        Updates the recurrent weight matrix so that the pattern becomes
        an attractor in the network dynamics. Uses outer-product (Hopfield)
        learning rule.

        Args:
            pattern: Binary array of shape (size,) representing the pattern
                     to store (1 = active, 0 = inactive).
        """
        pattern = np.asarray(pattern, dtype=np.float64).flatten()

        # Resize/pad if needed
        full_pattern = np.zeros(self.size, dtype=np.float64)
        n = min(len(pattern), self.size)
        full_pattern[:n] = pattern[:n]

        # Convert to bipolar (-1, +1) for Hopfield rule
        bipolar = 2.0 * full_pattern - 1.0

        # Outer product Hebbian update
        update = np.outer(bipolar, bipolar) * self.recurrent_weight / self.size
        np.fill_diagonal(update, 0.0)  # No autapses
        self._recurrent_weights += update

        self.stored_patterns.append(full_pattern.copy())

    def pattern_completion(self, partial_pattern: np.ndarray) -> np.ndarray:
        """Complete a partial pattern using recurrent dynamics.

        Presents the partial pattern as initial current, then runs
        multiple recurrent steps allowing the attractor dynamics to
        settle into the nearest stored pattern.

        Args:
            partial_pattern: Array of shape (size,) with partial input.
                            Non-zero entries are the known elements.

        Returns:
            Array of shape (size,) with the completed pattern (firing rates
            over the completion steps, values between 0 and 1).
        """
        partial = np.asarray(partial_pattern, dtype=np.float64).flatten()
        full_input = np.zeros(self.size, dtype=np.float64)
        n = min(len(partial), self.size)
        full_input[:n] = partial[:n]

        # Reset population state for clean completion
        self.population.reset()

        # Accumulate spikes over completion steps
        spike_accumulator = np.zeros(self.size, dtype=np.float64)

        for step_i in range(self.completion_steps):
            # Combine external input with recurrent feedback
            if step_i == 0:
                current = full_input * self.population.threshold[0]
            else:
                # Recurrent input from previous spikes
                recurrent_input = self._recurrent_weights @ self.output_spikes.astype(
                    np.float64
                )
                current = recurrent_input + full_input * 0.3

            self.input_buffer = current
            spikes = super().step()
            spike_accumulator += spikes.astype(np.float64)

        # Return normalized pattern (firing probability)
        if self.completion_steps > 0:
            result = spike_accumulator / self.completion_steps
        else:
            result = spike_accumulator

        return result

    def step(self) -> np.ndarray:
        """Advance the association region by one timestep with recurrent dynamics.

        Applies recurrent feedback from the previous step's output
        in addition to any external input in the buffer.

        Returns:
            Boolean array of shape (size,) indicating which neurons fired.
        """
        # Add recurrent feedback from previous output
        recurrent_input = self._recurrent_weights @ self.output_spikes.astype(
            np.float64
        )
        self.input_buffer += recurrent_input

        return super().step()

    def __repr__(self) -> str:
        return (
            f"AssociationRegion(name='{self.name}', size={self.size}, "
            f"stored_patterns={len(self.stored_patterns)})"
        )
