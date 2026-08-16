"""
Simulation Configuration Module.

Provides a SimulationConfig dataclass that defines all parameters
for running the neural network simulation.
"""

from dataclasses import dataclass


@dataclass
class SimulationConfig:
    """Configuration parameters for the simulation engine.

    Attributes:
        dt: Simulation timestep in arbitrary time units (default 1.0ms).
        total_time: Total simulation time in timesteps.
        record_spikes: Whether to record individual spike events.
        record_rates: Whether to record population firing rates.
        stdp_enabled: Whether spike-timing-dependent plasticity is active.
        snapshot_interval: How often (in timesteps) to take state snapshots.
        settling_steps: Number of initial steps before recording begins.
    """

    dt: float = 1.0
    total_time: int = 1000
    record_spikes: bool = True
    record_rates: bool = True
    stdp_enabled: bool = True
    snapshot_interval: int = 100
    settling_steps: int = 0

    def __post_init__(self) -> None:
        """Validate configuration parameters."""
        if self.dt <= 0:
            raise ValueError("dt must be positive")
        if self.total_time < 1:
            raise ValueError("total_time must be at least 1")
        if self.snapshot_interval < 1:
            raise ValueError("snapshot_interval must be at least 1")
        if self.settling_steps < 0:
            raise ValueError("settling_steps must be non-negative")

    def __repr__(self) -> str:
        return (
            f"SimulationConfig(dt={self.dt}, total_time={self.total_time}, "
            f"record_spikes={self.record_spikes}, stdp={self.stdp_enabled})"
        )
