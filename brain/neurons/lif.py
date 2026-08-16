"""
Leaky Integrate-and-Fire (LIF) Neuron Model.

A biologically-inspired neuron model that:
- Integrates incoming current into membrane potential
- Leaks (decays) potential over time
- Fires a binary spike when threshold is reached
- Enters a refractory period after firing
"""

import uuid
from dataclasses import dataclass, field


@dataclass
class LIFNeuron:
    """Leaky Integrate-and-Fire neuron with configurable dynamics.

    Attributes:
        neuron_id: Unique identifier for the neuron.
        membrane_potential: Current voltage of the neuron membrane.
        threshold: Voltage at which the neuron fires a spike.
        rest_potential: Resting membrane potential (reset value after spike).
        decay: Rate at which membrane potential decays toward rest (0-1).
        refractory_period: Number of timesteps the neuron is inactive after firing.
        refractory_counter: Remaining refractory timesteps.
    """

    neuron_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    membrane_potential: float = 0.0
    threshold: float = 1.0
    rest_potential: float = 0.0
    decay: float = 0.9
    refractory_period: int = 2
    refractory_counter: int = 0

    def step(self, input_current: float = 0.0) -> bool:
        """Advance the neuron by one timestep.

        Args:
            input_current: External current injected into the neuron.

        Returns:
            True if the neuron fires a spike, False otherwise.
        """
        # If in refractory period, count down and do not fire
        if self.refractory_counter > 0:
            self.refractory_counter -= 1
            self.membrane_potential = self.rest_potential
            return False

        # Integrate: decay toward rest and add input current
        self.membrane_potential = (
            self.decay * (self.membrane_potential - self.rest_potential) + self.rest_potential + input_current
        )

        # Fire if above threshold
        if self.membrane_potential >= self.threshold:
            self.membrane_potential = self.rest_potential
            self.refractory_counter = self.refractory_period
            return True

        return False

    def reset(self) -> None:
        """Reset the neuron to its initial state."""
        self.membrane_potential = self.rest_potential
        self.refractory_counter = 0

    def __repr__(self) -> str:
        return (
            f"LIFNeuron(id={self.neuron_id}, V={self.membrane_potential:.3f}, "
            f"thresh={self.threshold}, decay={self.decay})"
        )
