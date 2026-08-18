"""
Brain State.

Holds the complete current state of the brain including
all subsystem states, active concepts, and processing context.
"""

import time as time_module
from dataclasses import dataclass, field
from typing import Any, Dict


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
    last_prediction_error: float = 0.0
    thought_trace: Dict[str, Any] = field(default_factory=dict)

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
            "last_prediction_error": self.last_prediction_error,
            "thought_trace": self.thought_trace,
        }

    def add_thought(self, name: str, steps: Any) -> None:
        """Append an inspectable reasoning step to the thought trace.

        Records the cognitive method used (e.g. ``inference_synthesis``)
        together with its derivation steps so external systems can see
        *how* the brain arrived at an answer, not just the answer.
        """
        self.thought_trace[name] = {
            "steps": steps if isinstance(steps, list) else [str(steps)],
            "timestamp": time_module.time(),
        }

    def __repr__(self) -> str:
        return (
            f"BrainState(cycle={self.cycle_count}, "
            f"phase={self.current_phase}, "
            f"active_concepts={len(self.active_concepts)})"
        )
