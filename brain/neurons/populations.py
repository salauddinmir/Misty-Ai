"""
Neuron Population Manager.

Manages groups of neurons that represent concepts, features,
or processing layers within the cognitive system.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import uuid

from brain.neurons.lif import LIFNeuron


@dataclass
class NeuronPopulation:
    """A managed group of LIF neurons.

    Attributes:
        population_id: Unique identifier for this population.
        name: Human-readable name for the population.
        neurons: Dictionary mapping neuron IDs to LIFNeuron instances.
        size: Number of neurons in this population.
    """

    name: str = "unnamed"
    population_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    neurons: Dict[str, LIFNeuron] = field(default_factory=dict)

    @property
    def size(self) -> int:
        """Number of neurons in this population."""
        return len(self.neurons)

    def create_neurons(
        self,
        count: int,
        threshold: float = 1.0,
        decay: float = 0.9,
        refractory_period: int = 2,
    ) -> List[LIFNeuron]:
        """Create and add multiple neurons to this population.

        Args:
            count: Number of neurons to create.
            threshold: Firing threshold for the neurons.
            decay: Membrane potential decay rate.
            refractory_period: Refractory period after firing.

        Returns:
            List of created neurons.
        """
        created = []
        for _ in range(count):
            neuron = LIFNeuron(
                threshold=threshold,
                decay=decay,
                refractory_period=refractory_period,
            )
            self.neurons[neuron.neuron_id] = neuron
            created.append(neuron)
        return created

    def step(self, inputs: Optional[Dict[str, float]] = None) -> Dict[str, bool]:
        """Advance all neurons by one timestep.

        Args:
            inputs: Optional mapping of neuron_id -> input_current.
                    Neurons not in the dict receive 0 input.

        Returns:
            Dictionary mapping neuron_id -> spike (True/False).
        """
        inputs = inputs or {}
        spikes = {}
        for nid, neuron in self.neurons.items():
            current = inputs.get(nid, 0.0)
            spikes[nid] = neuron.step(current)
        return spikes

    def get_active_neurons(self) -> List[str]:
        """Get IDs of neurons that just fired (in refractory at max)."""
        return [
            nid for nid, neuron in self.neurons.items()
            if neuron.refractory_counter == neuron.refractory_period
        ]

    def reset(self) -> None:
        """Reset all neurons in this population."""
        for neuron in self.neurons.values():
            neuron.reset()

    def __repr__(self) -> str:
        return f"NeuronPopulation(name={self.name}, size={self.size})"
