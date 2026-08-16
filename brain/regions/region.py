"""
Base Brain Region Module.

Provides the abstract base class BrainRegion that wraps a VectorizedPopulation
with specialized region-level behavior including input buffering, output tracking,
and firing rate computation.
"""

from typing import Optional

import numpy as np

from brain.neurons.vectorized import VectorizedPopulation


class BrainRegion:
    """Base class for specialized brain regions.

    A BrainRegion wraps a VectorizedPopulation and adds region-level
    functionality: an input buffer that accumulates currents from
    connected regions, output spike tracking, and firing rate
    computation.

    Subclasses implement specialized behavior (sensory encoding,
    memory retrieval, reward signaling, etc.) by overriding or
    extending the step() method.

    Attributes:
        name: Human-readable name for this region.
        population: The underlying VectorizedPopulation of neurons.
        input_buffer: Accumulated input currents for the next timestep.
        output_spikes: Spike array from the most recent step.
    """

    def __init__(
        self,
        name: str,
        size: int,
        excitatory_ratio: float = 0.8,
        threshold: float = 1.0,
        rest_potential: float = 0.0,
        decay: float = 0.9,
        refractory_period: int = 2,
    ) -> None:
        """Initialize a brain region with an underlying neuron population.

        Args:
            name: Human-readable identifier for the region.
            size: Number of neurons in the region's population.
            excitatory_ratio: Fraction of excitatory neurons (0-1).
            threshold: Firing threshold for neurons.
            rest_potential: Resting membrane potential.
            decay: Membrane potential decay rate (0-1).
            refractory_period: Refractory period in timesteps.
        """
        self.name: str = name
        self.population: VectorizedPopulation = VectorizedPopulation(
            size=size,
            name=name,
            excitatory_ratio=excitatory_ratio,
            threshold_val=threshold,
            rest_potential_val=rest_potential,
            decay_val=decay,
            refractory_period_val=refractory_period,
        )
        self.input_buffer: np.ndarray = np.zeros(size, dtype=np.float64)
        self.output_spikes: np.ndarray = np.zeros(size, dtype=bool)
        self._spike_history_length: int = 100
        self._spike_history: np.ndarray = np.zeros(
            self._spike_history_length, dtype=np.float64
        )
        self._step_count: int = 0

    @property
    def size(self) -> int:
        """Number of neurons in this region."""
        return self.population.size

    def receive_input(self, currents: np.ndarray) -> None:
        """Accumulate input currents into the input buffer.

        Multiple calls before a step() will sum their contributions.

        Args:
            currents: Array of shape (size,) with input currents to add.
        """
        currents = np.asarray(currents, dtype=np.float64)
        self.input_buffer += currents

    def step(self) -> np.ndarray:
        """Advance the region by one timestep.

        Feeds the accumulated input buffer into the population,
        records the output spikes, clears the buffer, and updates
        firing rate history.

        Returns:
            Boolean array of shape (size,) indicating which neurons fired.
        """
        self.output_spikes = self.population.step(self.input_buffer)
        self.input_buffer[:] = 0.0

        # Track firing rate history
        rate = np.mean(self.output_spikes.astype(np.float64))
        idx = self._step_count % self._spike_history_length
        self._spike_history[idx] = rate
        self._step_count += 1

        return self.output_spikes

    def reset(self) -> None:
        """Reset the region to its initial state."""
        self.population.reset()
        self.input_buffer[:] = 0.0
        self.output_spikes[:] = False
        self._spike_history[:] = 0.0
        self._step_count = 0

    def get_firing_rate(self) -> float:
        """Compute the average firing rate over recent history.

        Returns the mean fraction of neurons that fired per timestep,
        averaged over the most recent steps (up to the history length).

        Returns:
            Float between 0.0 and 1.0 representing the average firing rate.
        """
        if self._step_count == 0:
            return 0.0
        valid_steps = min(self._step_count, self._spike_history_length)
        return float(np.mean(self._spike_history[:valid_steps]))

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(name='{self.name}', "
            f"size={self.size}, firing_rate={self.get_firing_rate():.4f})"
        )
