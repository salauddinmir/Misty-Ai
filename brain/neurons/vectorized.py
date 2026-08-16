"""
Vectorized Neuron Population using NumPy arrays.

Provides a high-performance implementation of LIF neuron populations
that simulates thousands of neurons simultaneously using vectorized
NumPy operations instead of per-neuron Python loops.
"""

from dataclasses import dataclass, field
from enum import IntEnum

import numpy as np


class NeuronType(IntEnum):
    """Types of neurons based on their synaptic effect.

    EXCITATORY neurons produce positive output that increases
    post-synaptic potential. INHIBITORY neurons produce negative
    output that decreases post-synaptic potential.
    """

    EXCITATORY = 1
    INHIBITORY = -1


@dataclass
class VectorizedPopulation:
    """A population of LIF neurons simulated with vectorized NumPy operations.

    This class maintains arrays for all neuron state variables and applies
    the Leaky Integrate-and-Fire dynamics in a single vectorized step,
    enabling efficient simulation of thousands to tens of thousands of neurons.

    The LIF dynamics are identical to LIFNeuron.step():
      1. Refractory neurons: decrement counter, hold at rest potential.
      2. Active neurons: integrate (decay toward rest + input current).
      3. Fire neurons above threshold: reset potential, set refractory.

    Attributes:
        size: Number of neurons in the population.
        name: Optional human-readable name for the population.
        membrane_potential: Array of membrane voltages for each neuron.
        threshold: Array of firing thresholds for each neuron.
        rest_potential: Array of resting potentials for each neuron.
        decay: Array of decay constants (0-1) for each neuron.
        refractory_period: Array of refractory durations per neuron.
        refractory_counter: Array of remaining refractory timesteps.
        type_array: Array of NeuronType values (1 for excitatory, -1 for inhibitory).
    """

    size: int
    name: str = "population"
    excitatory_ratio: float = 0.8
    threshold_val: float = 1.0
    rest_potential_val: float = 0.0
    decay_val: float = 0.9
    refractory_period_val: int = 2

    # These are initialized in __post_init__
    membrane_potential: np.ndarray = field(init=False, repr=False)
    threshold: np.ndarray = field(init=False, repr=False)
    rest_potential: np.ndarray = field(init=False, repr=False)
    decay: np.ndarray = field(init=False, repr=False)
    refractory_period: np.ndarray = field(init=False, repr=False)
    refractory_counter: np.ndarray = field(init=False, repr=False)
    type_array: np.ndarray = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Initialize all neuron state arrays."""
        n = self.size

        # State arrays
        self.membrane_potential = np.full(n, self.rest_potential_val, dtype=np.float64)
        self.threshold = np.full(n, self.threshold_val, dtype=np.float64)
        self.rest_potential = np.full(n, self.rest_potential_val, dtype=np.float64)
        self.decay = np.full(n, self.decay_val, dtype=np.float64)
        self.refractory_period = np.full(n, self.refractory_period_val, dtype=np.int32)
        self.refractory_counter = np.zeros(n, dtype=np.int32)

        # Assign neuron types: ~80% excitatory, ~20% inhibitory by default
        num_excitatory = int(n * self.excitatory_ratio)
        self.type_array = np.ones(n, dtype=np.int32)  # Default excitatory
        self.type_array[num_excitatory:] = NeuronType.INHIBITORY

    def step(self, input_current: np.ndarray) -> np.ndarray:
        """Advance all neurons by one timestep using vectorized LIF dynamics.

        Implements identical dynamics to LIFNeuron.step() but for all neurons
        simultaneously:
          1. Refractory neurons: decrement counter, hold at rest potential.
          2. Active neurons: integrate (decay toward rest + input current).
          3. Fire neurons above threshold: reset potential, set refractory.

        Args:
            input_current: Array of shape (size,) with input current for each neuron.

        Returns:
            Boolean array of shape (size,) where True indicates a spike.
        """
        input_current = np.asarray(input_current, dtype=np.float64)
        spikes = np.zeros(self.size, dtype=bool)

        # Identify refractory vs active neurons
        refractory_mask = self.refractory_counter > 0
        active_mask = ~refractory_mask

        # Step 1: Refractory neurons - decrement counter, hold at rest
        self.refractory_counter[refractory_mask] -= 1
        self.membrane_potential[refractory_mask] = self.rest_potential[refractory_mask]

        # Step 2: Active neurons - integrate (decay toward rest + input)
        self.membrane_potential[active_mask] = (
            self.decay[active_mask] * (self.membrane_potential[active_mask] - self.rest_potential[active_mask])
            + self.rest_potential[active_mask]
            + input_current[active_mask]
        )

        # Step 3: Fire check - only active neurons can fire
        fire_mask = active_mask & (self.membrane_potential >= self.threshold)
        spikes[fire_mask] = True

        # Reset fired neurons
        self.membrane_potential[fire_mask] = self.rest_potential[fire_mask]
        self.refractory_counter[fire_mask] = self.refractory_period[fire_mask]

        return spikes

    def get_output(self, spikes: np.ndarray) -> np.ndarray:
        """Get the signed output of neurons based on their type and spike state.

        Excitatory neurons produce +1 when spiking, inhibitory produce -1.

        Args:
            spikes: Boolean array of shape (size,) indicating which neurons fired.

        Returns:
            Array of shape (size,) with signed spike values (+1 or -1 for firing neurons, 0 otherwise).
        """
        return spikes.astype(np.float64) * self.type_array

    def reset(self) -> None:
        """Reset all neurons to their initial resting state."""
        self.membrane_potential[:] = self.rest_potential
        self.refractory_counter[:] = 0

    @property
    def excitatory_count(self) -> int:
        """Number of excitatory neurons in the population."""
        return int(np.sum(self.type_array == NeuronType.EXCITATORY))

    @property
    def inhibitory_count(self) -> int:
        """Number of inhibitory neurons in the population."""
        return int(np.sum(self.type_array == NeuronType.INHIBITORY))

    def __repr__(self) -> str:
        return (
            f"VectorizedPopulation(name='{self.name}', size={self.size}, "
            f"excitatory={self.excitatory_count}, inhibitory={self.inhibitory_count})"
        )
