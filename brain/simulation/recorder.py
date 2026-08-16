"""
Spike Recorder Module.

Records spike trains, firing rates, and network state during
simulation for monitoring and analysis.
"""

from typing import Dict, List, Optional

import numpy as np


class SpikeRecorder:
    """Records spike activity from brain regions during simulation.

    Stores spike trains per region as lists of boolean arrays,
    computes firing rates over configurable windows, and provides
    access to recording history.

    Attributes:
        spike_trains: Dictionary mapping region names to spike history.
        rate_history: Dictionary mapping region names to firing rate history.
    """

    def __init__(self, max_history: int = 10000) -> None:
        """Initialize the spike recorder.

        Args:
            max_history: Maximum number of timesteps to store.
                        Older records are discarded (FIFO).
        """
        self.max_history: int = max_history
        self.spike_trains: Dict[str, List[np.ndarray]] = {}
        self.rate_history: Dict[str, List[float]] = {}
        self._timestep: int = 0

    def add_spikes(
        self, region_name: str, timestep: int, spikes: np.ndarray
    ) -> None:
        """Record a spike array for a region at a given timestep.

        Args:
            region_name: Name of the region producing the spikes.
            timestep: Current simulation timestep.
            spikes: Boolean array indicating which neurons fired.
        """
        if region_name not in self.spike_trains:
            self.spike_trains[region_name] = []
            self.rate_history[region_name] = []

        # Store spike array (compressed as bool)
        self.spike_trains[region_name].append(spikes.astype(np.bool_).copy())

        # Compute and store firing rate
        rate = float(np.mean(spikes.astype(np.float64)))
        self.rate_history[region_name].append(rate)

        # Enforce max history
        if len(self.spike_trains[region_name]) > self.max_history:
            self.spike_trains[region_name].pop(0)
            self.rate_history[region_name].pop(0)

        self._timestep = timestep

    def get_spike_train(self, region_name: str) -> Optional[np.ndarray]:
        """Get the full spike train matrix for a region.

        Args:
            region_name: Name of the region.

        Returns:
            2D array of shape (timesteps, neurons) with boolean values,
            or None if no data is recorded for the region.
        """
        if region_name not in self.spike_trains:
            return None
        if not self.spike_trains[region_name]:
            return None
        return np.array(self.spike_trains[region_name])

    def get_firing_rate(self, region_name: str, window: int = 50) -> float:
        """Get the average firing rate over the last N timesteps.

        Args:
            region_name: Name of the region.
            window: Number of recent timesteps to average over.

        Returns:
            Average fraction of neurons firing per timestep.
            Returns 0.0 if no data is available.
        """
        if region_name not in self.rate_history:
            return 0.0
        history = self.rate_history[region_name]
        if not history:
            return 0.0
        recent = history[-window:]
        return float(np.mean(recent))

    def get_history(
        self, region_name: str, last_n_steps: int = 100
    ) -> Optional[np.ndarray]:
        """Get the most recent spike history for a region.

        Args:
            region_name: Name of the region.
            last_n_steps: Number of most recent timesteps to return.

        Returns:
            2D array of shape (last_n_steps, neurons), or None if no data.
        """
        if region_name not in self.spike_trains:
            return None
        trains = self.spike_trains[region_name]
        if not trains:
            return None
        recent = trains[-last_n_steps:]
        return np.array(recent)

    def get_all_rates(self) -> Dict[str, float]:
        """Get current firing rates for all recorded regions.

        Returns:
            Dictionary mapping region names to their current firing rates.
        """
        rates = {}
        for name in self.rate_history:
            rates[name] = self.get_firing_rate(name)
        return rates

    @property
    def recorded_regions(self) -> List[str]:
        """List of all region names being recorded."""
        return list(self.spike_trains.keys())

    @property
    def total_timesteps(self) -> int:
        """Total number of timesteps recorded."""
        return self._timestep

    def reset(self) -> None:
        """Clear all recorded data."""
        self.spike_trains.clear()
        self.rate_history.clear()
        self._timestep = 0

    def __repr__(self) -> str:
        return (
            f"SpikeRecorder(regions={len(self.spike_trains)}, "
            f"timesteps={self._timestep})"
        )
