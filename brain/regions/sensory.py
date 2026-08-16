"""
Sensory Region Module.

Implements a SensoryRegion that encodes raw input data (numerical arrays)
into neural spike patterns suitable for downstream processing. This acts
as the interface between external data and the spiking neural system.
"""

from typing import Optional

import numpy as np

from brain.regions.region import BrainRegion


class SensoryRegion(BrainRegion):
    """Sensory cortex region that encodes external input into spike patterns.

    Converts raw numerical input data into current injections that drive
    the underlying neuron population. Supports normalization and gain
    control to maintain appropriate firing rates across different input
    magnitudes.

    The encoding pipeline:
      1. Normalize input to [0, 1] range.
      2. Apply gain factor to scale into effective current range.
      3. Optionally add noise for stochastic encoding.
      4. Feed resulting currents into the population.

    Attributes:
        gain: Multiplicative gain applied to normalized inputs.
        noise_level: Standard deviation of Gaussian noise added to encoding.
    """

    def __init__(
        self,
        name: str = "sensory",
        size: int = 256,
        gain: float = 2.0,
        noise_level: float = 0.05,
        excitatory_ratio: float = 0.9,
        threshold: float = 1.0,
        decay: float = 0.9,
        refractory_period: int = 2,
    ) -> None:
        """Initialize a sensory region.

        Args:
            name: Human-readable name for the region.
            size: Number of neurons in the sensory population.
            gain: Gain factor applied to normalized input before injection.
            noise_level: Standard deviation of encoding noise (0 for deterministic).
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
        self.gain: float = gain
        self.noise_level: float = noise_level

    def encode_input(self, data: np.ndarray) -> np.ndarray:
        """Encode raw input data into neural current patterns.

        Normalizes the input to [0, 1], applies gain, adds optional noise,
        and stores the result in the input buffer for the next step().

        If the input array is smaller than the population size, it is
        zero-padded. If larger, it is truncated.

        Args:
            data: Raw input array of arbitrary shape (will be flattened).

        Returns:
            Array of shape (size,) with the encoded currents that were
            placed into the input buffer.
        """
        flat_data = np.asarray(data, dtype=np.float64).flatten()

        # Fit data to population size
        currents = np.zeros(self.size, dtype=np.float64)
        n = min(len(flat_data), self.size)
        currents[:n] = flat_data[:n]

        # Normalize to [0, 1]
        data_min = currents.min()
        data_max = currents.max()
        if data_max - data_min > 1e-10:
            currents = (currents - data_min) / (data_max - data_min)
        else:
            # Constant input: set to 0.5 if non-zero, else 0
            if abs(data_max) > 1e-10:
                currents[:n] = 0.5
            else:
                currents[:] = 0.0

        # Apply gain
        currents *= self.gain

        # Add noise
        if self.noise_level > 0.0:
            noise = np.random.default_rng().normal(0.0, self.noise_level, self.size)
            currents += noise
            # Clamp to non-negative
            np.clip(currents, 0.0, None, out=currents)

        # Store in input buffer
        self.input_buffer = currents
        return currents

    def step(self) -> np.ndarray:
        """Advance the sensory region by one timestep.

        Uses the currents from encode_input() (stored in input_buffer)
        to drive the neural population.

        Returns:
            Boolean array of shape (size,) indicating which neurons fired.
        """
        return super().step()

    def __repr__(self) -> str:
        return (
            f"SensoryRegion(name='{self.name}', size={self.size}, "
            f"gain={self.gain}, noise={self.noise_level})"
        )
