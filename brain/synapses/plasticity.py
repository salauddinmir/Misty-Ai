"""
Plasticity Manager.

Manages all synapses and applies learning rules (STDP)
across the network during simulation.
"""

from dataclasses import dataclass, field
from typing import Dict, List

from brain.synapses.stdp import STDPRule
from brain.synapses.synapse import Synapse


@dataclass
class PlasticityManager:
    """Manages synaptic plasticity across the neural network.

    Attributes:
        synapses: Dictionary of all managed synapses by ID.
        stdp_rule: The STDP rule to apply.
        current_time: Current simulation timestep.
    """

    synapses: Dict[str, Synapse] = field(default_factory=dict)
    stdp_rule: STDPRule = field(default_factory=STDPRule)
    current_time: int = 0

    def add_synapse(self, synapse: Synapse) -> None:
        """Register a synapse for plasticity management."""
        self.synapses[synapse.synapse_id] = synapse

    def create_synapse(
        self,
        pre_neuron_id: str,
        post_neuron_id: str,
        weight: float = 0.5,
        delay: int = 1,
    ) -> Synapse:
        """Create and register a new synapse."""
        synapse = Synapse(
            pre_neuron_id=pre_neuron_id,
            post_neuron_id=post_neuron_id,
            weight=weight,
            delay=delay,
        )
        self.add_synapse(synapse)
        return synapse

    def record_spike(self, neuron_id: str, is_pre: bool = True) -> None:
        """Record a spike event for STDP tracking."""
        for synapse in self.synapses.values():
            if is_pre and synapse.pre_neuron_id == neuron_id:
                synapse.record_pre_spike(self.current_time)
            elif not is_pre and synapse.post_neuron_id == neuron_id:
                synapse.record_post_spike(self.current_time)

    def apply_stdp(self) -> Dict[str, float]:
        """Apply STDP learning rule to all managed synapses."""
        changes = {}
        for sid, synapse in self.synapses.items():
            delta = self.stdp_rule.apply(synapse, self.current_time)
            if delta != 0.0:
                changes[sid] = delta
        return changes

    def step(self) -> None:
        """Advance the simulation clock by one timestep."""
        self.current_time += 1

    def get_synapses_for_neuron(self, neuron_id: str, as_pre: bool = True) -> List[Synapse]:
        """Get all synapses connected to a neuron."""
        if as_pre:
            return [s for s in self.synapses.values() if s.pre_neuron_id == neuron_id]
        else:
            return [s for s in self.synapses.values() if s.post_neuron_id == neuron_id]

    def __repr__(self) -> str:
        return f"PlasticityManager(synapses={len(self.synapses)}, t={self.current_time})"
