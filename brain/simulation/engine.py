"""
Simulation Engine Module.

The main simulation loop that orchestrates all brain regions,
processes synaptic transmission between populations, optionally
applies STDP learning, and records spike history.
"""

from typing import Dict, List

import numpy as np

from brain.regions.region import BrainRegion
from brain.simulation.config import SimulationConfig
from brain.simulation.recorder import SpikeRecorder
from brain.synapses.network import SynapticNetwork


class SimulationEngine:
    """Main simulation engine coordinating brain regions and synaptic networks.

    Orchestrates the simulation loop:
      1. Collect spikes from all regions (from previous step).
      2. Propagate spikes through the synaptic network to produce currents.
      3. Deliver currents to target regions via receive_input().
      4. Step all regions to produce new spikes.
      5. Record spikes if recording is enabled.

    Attributes:
        regions: List of BrainRegion instances in the simulation.
        network: SynapticNetwork managing inter-region connections.
        config: SimulationConfig with parameters.
        recorder: SpikeRecorder for recording activity.
        current_step: Current simulation timestep.
    """

    def __init__(
        self,
        regions: List[BrainRegion],
        network: SynapticNetwork,
        config: SimulationConfig | None = None,
        recorder: SpikeRecorder | None = None,
    ) -> None:
        """Initialize the simulation engine.

        Args:
            regions: List of BrainRegion instances to simulate.
            network: SynapticNetwork defining connections between regions.
            config: Optional simulation configuration. Uses defaults if None.
            recorder: Optional spike recorder. Creates one if None and
                     recording is enabled in config.
        """
        self.regions: List[BrainRegion] = regions
        self.network: SynapticNetwork = network
        self.config: SimulationConfig = config or SimulationConfig()

        if recorder is not None:
            self.recorder: SpikeRecorder = recorder
        elif self.config.record_spikes:
            self.recorder = SpikeRecorder()
        else:
            self.recorder = SpikeRecorder()

        self.current_step: int = 0
        self._spike_dict: Dict[str, np.ndarray] = {}

        # Register all region populations with the network if not already done
        for region in self.regions:
            if region.population.name not in self.network.populations:
                self.network.add_population(region.population)

    def step(self) -> Dict[str, np.ndarray]:
        """Advance the simulation by one timestep.

        Performs the full simulation loop: propagate, deliver, step, record.

        Returns:
            Dictionary mapping region names to their spike arrays from this step.
        """
        # Propagate previous spikes through network
        if self._spike_dict:
            currents = self.network.propagate_all(self._spike_dict)
            # Deliver currents to regions
            for region in self.regions:
                if region.population.name in currents:
                    region.receive_input(currents[region.population.name])

        # Step all regions
        self._spike_dict = {}
        for region in self.regions:
            spikes = region.step()
            self._spike_dict[region.population.name] = spikes

            # Record spikes
            if self.config.record_spikes and self.current_step >= self.config.settling_steps:
                self.recorder.add_spikes(region.name, self.current_step, spikes)

        self.current_step += 1
        return self._spike_dict.copy()

    def run(self, n_steps: int) -> None:
        """Run the simulation for a specified number of timesteps.

        Args:
            n_steps: Number of timesteps to advance.
        """
        for _ in range(n_steps):
            self.step()

    def inject_current(self, region_name: str, currents: np.ndarray) -> None:
        """Inject external current into a specific region.

        Adds the specified currents to the region's input buffer
        for the next step.

        Args:
            region_name: Name of the target region.
            currents: Array of currents to inject.

        Raises:
            ValueError: If no region with the given name exists.
        """
        for region in self.regions:
            if region.name == region_name:
                region.receive_input(currents)
                return
        raise ValueError(f"No region named '{region_name}' in simulation")

    def get_state(self) -> Dict[str, dict]:
        """Get the current state of all regions.

        Returns:
            Dictionary mapping region names to their state info including
            firing rate and current step.
        """
        state: Dict[str, dict] = {}
        for region in self.regions:
            state[region.name] = {
                "size": region.size,
                "firing_rate": region.get_firing_rate(),
                "current_step": self.current_step,
            }
        return state

    def reset(self) -> None:
        """Reset the simulation to its initial state."""
        for region in self.regions:
            region.reset()
        self._spike_dict = {}
        self.current_step = 0
        self.recorder.reset()

    def __repr__(self) -> str:
        return (
            f"SimulationEngine(regions={len(self.regions)}, "
            f"step={self.current_step}, "
            f"connections={len(self.network.connections)})"
        )
