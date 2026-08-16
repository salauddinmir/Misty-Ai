"""
Brain State.

Holds the complete current state of the brain including
all subsystem states, active concepts, and processing context.
"""

from dataclasses import dataclass, field
from typing import Any, Dict
import time as time_module


@dataclass
class BrainState:
    """Complete snapshot of the brain's current state."""

    cycle_count: int = 0
    current_phase: str = "idle"
    active_concepts: Dict[str, float] = field(default_factory=dict)
    working_memory_snapshot: Dict[str, Any] = field(default_factory=dict)
    emotional_state: Dict[str, float] = field(default_factory=dict)
    last_input: str = ""
    last_output: str = ""
    timestamp: float = field(default_factory=time_module.time)
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert brain state to a serializable dictionary."""
        return {
            "cycle_count": self.cycle_count,
            "current_phase": self.current_phase,
            "active_concepts": self.active_concepts,
            "working_memory_snapshot": self.working_memory_snapshot,
            "emotional_state": self.emotional_state,
            "last_input": self.last_input,
            "last_output": self.last_output,
            "timestamp": self.timestamp,
            "context": self.context,
        }

    def __repr__(self) -> str:
        return (
            f"BrainState(cycle={self.cycle_count}, "
            f"phase={self.current_phase}, "
            f"active_concepts={len(self.active_concepts)})"
        )
