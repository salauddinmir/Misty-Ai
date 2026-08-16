"""
Simple Binary Neuron Model.

A minimal neuron that outputs 1 (active) or 0 (inactive)
based on whether its input exceeds a threshold.
"""

from dataclasses import dataclass, field
import uuid


@dataclass
class BinaryNeuron:
    """Simple binary neuron with threshold activation.

    Attributes:
        neuron_id: Unique identifier for the neuron.
        threshold: Input threshold for activation.
        state: Current binary state (True=active, False=inactive).
    """

    neuron_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    threshold: float = 0.5
    state: bool = False

    def activate(self, input_value: float) -> bool:
        """Compute binary output based on input value.

        Args:
            input_value: Summed input to this neuron.

        Returns:
            True if input exceeds threshold, False otherwise.
        """
        self.state = input_value >= self.threshold
        return self.state

    def reset(self) -> None:
        """Reset neuron state to inactive."""
        self.state = False

    def __repr__(self) -> str:
        return (
            f"BinaryNeuron(id={self.neuron_id}, "
            f"threshold={self.threshold}, state={self.state})"
        )
