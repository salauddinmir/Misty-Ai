"""
Base Synapse Model.

Represents a connection between two neurons with a weight,
transmission delay, and references to pre/post synaptic neurons.
"""

from dataclasses import dataclass, field
import uuid


@dataclass
class Synapse:
    """A weighted connection between two neurons.

    Attributes:
        synapse_id: Unique identifier for this synapse.
        pre_neuron_id: ID of the presynaptic (source) neuron.
        post_neuron_id: ID of the postsynaptic (target) neuron.
        weight: Connection strength (can be positive or negative).
        delay: Transmission delay in timesteps.
        active: Whether this synapse is currently active.
    """

    pre_neuron_id: str
    post_neuron_id: str
    weight: float = 0.5
    delay: int = 1
    active: bool = True
    synapse_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    # Timing tracking for STDP
    last_pre_spike_time: int = -1
    last_post_spike_time: int = -1

    def transmit(self, pre_spike: bool) -> float:
        """Compute the transmitted signal through this synapse.

        Args:
            pre_spike: Whether the presynaptic neuron fired.

        Returns:
            Weighted signal if pre fires and synapse is active, else 0.
        """
        if not self.active or not pre_spike:
            return 0.0
        return self.weight

    def update_weight(self, delta: float, min_weight: float = 0.0, max_weight: float = 1.0) -> None:
        """Update the synapse weight, clamped to bounds.

        Args:
            delta: Change in weight (positive = strengthen, negative = weaken).
            min_weight: Minimum allowed weight.
            max_weight: Maximum allowed weight.
        """
        self.weight = max(min_weight, min(max_weight, self.weight + delta))

    def record_pre_spike(self, time: int) -> None:
        """Record timing of a presynaptic spike."""
        self.last_pre_spike_time = time

    def record_post_spike(self, time: int) -> None:
        """Record timing of a postsynaptic spike."""
        self.last_post_spike_time = time

    def __repr__(self) -> str:
        return (
            f"Synapse(id={self.synapse_id}, "
            f"{self.pre_neuron_id}->{self.post_neuron_id}, "
            f"w={self.weight:.3f})"
        )
