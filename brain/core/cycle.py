"""
Cognitive Cycle.

Defines the phases of the cognitive cycle:
OBSERVE -> INTERPRET -> RECALL -> ASSOCIATE -> REASON ->
PLAN -> ACT -> EVALUATE -> LEARN -> CONSOLIDATE
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class CognitivePhase(str, Enum):
    """Phases of the cognitive cycle."""

    IDLE = "idle"
    OBSERVE = "observe"
    INTERPRET = "interpret"
    RECALL = "recall"
    ASSOCIATE = "associate"
    REASON = "reason"
    PLAN = "plan"
    ACT = "act"
    EVALUATE = "evaluate"
    LEARN = "learn"
    CONSOLIDATE = "consolidate"


# Ordered cycle sequence
CYCLE_ORDER: List[CognitivePhase] = [
    CognitivePhase.OBSERVE,
    CognitivePhase.INTERPRET,
    CognitivePhase.RECALL,
    CognitivePhase.ASSOCIATE,
    CognitivePhase.REASON,
    CognitivePhase.PLAN,
    CognitivePhase.ACT,
    CognitivePhase.EVALUATE,
    CognitivePhase.LEARN,
    CognitivePhase.CONSOLIDATE,
]


@dataclass
class CycleResult:
    """Result of a single cognitive cycle phase."""

    phase: CognitivePhase
    data: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    notes: str = ""


@dataclass
class CognitiveCycle:
    """Manages the cognitive cycle progression."""

    current_phase: CognitivePhase = CognitivePhase.IDLE
    phase_results: List[CycleResult] = field(default_factory=list)
    phase_timings_ms: Dict[str, float] = field(default_factory=dict)
    cycle_count: int = 0

    def start_cycle(self) -> CognitivePhase:
        """Start a new cognitive cycle."""
        self.phase_results = []
        self.phase_timings_ms = {}
        self.current_phase = CognitivePhase.OBSERVE
        return self.current_phase

    def advance(self, result: CycleResult) -> CognitivePhase | None:
        """Advance to the next phase after recording result."""
        self.phase_results.append(result)

        current_index = CYCLE_ORDER.index(self.current_phase)
        if current_index + 1 < len(CYCLE_ORDER):
            self.current_phase = CYCLE_ORDER[current_index + 1]
            return self.current_phase
        else:
            self.cycle_count += 1
            self.current_phase = CognitivePhase.IDLE
            return None

    def get_phase_result(self, phase: CognitivePhase) -> CycleResult | None:
        """Get the result from a specific phase in the current cycle."""
        for result in self.phase_results:
            if result.phase == phase:
                return result
        return None

    def is_active(self) -> bool:
        """Whether a cycle is currently in progress."""
        return self.current_phase != CognitivePhase.IDLE

    def __repr__(self) -> str:
        return f"CognitiveCycle(phase={self.current_phase.value}, cycles={self.cycle_count})"
