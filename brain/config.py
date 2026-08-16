"""
Brain Configuration Module.

Provides a centralized BrainConfig dataclass that holds all simulation
parameters for the neural system, including neuron defaults, connectivity,
and plasticity settings.
"""

from dataclasses import dataclass


@dataclass
class BrainConfig:
    """Configuration parameters for the brain simulation.

    Centralizes all tunable parameters for neuron dynamics, connectivity,
    and learning rules. Provides biologically-motivated defaults.

    Attributes:
        dt: Simulation timestep in arbitrary time units.
        default_threshold: Default firing threshold for LIF neurons.
        default_decay: Default membrane potential decay rate (0-1).
        default_rest_potential: Default resting membrane potential.
        default_refractory: Default refractory period in timesteps.
        excitatory_ratio: Fraction of neurons that are excitatory (0-1).
        inhibitory_ratio: Fraction of neurons that are inhibitory (0-1).
        connection_probability: Default probability for random connections.
        weight_min: Minimum absolute weight for new connections.
        weight_max: Maximum absolute weight for new connections.
        stdp_enabled: Whether spike-timing-dependent plasticity is active.
        stdp_learning_rate: Learning rate for STDP weight updates.
        stdp_window: Time window (in timesteps) for STDP coincidence detection.
        max_weight: Maximum allowed absolute synaptic weight.
        min_weight: Minimum allowed absolute synaptic weight (for pruning).
        population_size: Default population size for new populations.
    """

    # Simulation parameters
    dt: float = 1.0

    # Neuron defaults
    default_threshold: float = 1.0
    default_decay: float = 0.9
    default_rest_potential: float = 0.0
    default_refractory: int = 2

    # Population composition
    excitatory_ratio: float = 0.8
    inhibitory_ratio: float = 0.2

    # Connectivity
    connection_probability: float = 0.1
    weight_min: float = 0.01
    weight_max: float = 0.1

    # Plasticity / STDP
    stdp_enabled: bool = True
    stdp_learning_rate: float = 0.01
    stdp_window: int = 20
    max_weight: float = 1.0
    min_weight: float = 0.001

    # Defaults
    population_size: int = 1000

    def __post_init__(self) -> None:
        """Validate configuration parameters."""
        if not (0.0 <= self.excitatory_ratio <= 1.0):
            raise ValueError("excitatory_ratio must be between 0 and 1")
        if not (0.0 <= self.inhibitory_ratio <= 1.0):
            raise ValueError("inhibitory_ratio must be between 0 and 1")
        if abs(self.excitatory_ratio + self.inhibitory_ratio - 1.0) > 1e-9:
            raise ValueError("excitatory_ratio + inhibitory_ratio must equal 1.0")
        if not (0.0 < self.default_decay <= 1.0):
            raise ValueError("default_decay must be in (0, 1]")
        if self.default_threshold <= self.default_rest_potential:
            raise ValueError("default_threshold must be greater than default_rest_potential")
        if self.weight_min > self.weight_max:
            raise ValueError("weight_min must not exceed weight_max")
