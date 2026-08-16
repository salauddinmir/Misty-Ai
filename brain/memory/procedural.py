"""
Procedural Memory.

Stores learned procedures and rules that the brain can execute.
"""

import uuid
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Procedure:
    """A learned procedure or rule."""

    name: str
    condition: str
    action: str
    procedure_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    strength: float = 0.5
    use_count: int = 0
    success_count: int = 0

    @property
    def success_rate(self) -> float:
        """Success rate of this procedure."""
        if self.use_count == 0:
            return 0.0
        return self.success_count / self.use_count

    def reinforce(self, success: bool, amount: float = 0.1) -> None:
        """Reinforce or weaken this procedure based on outcome."""
        self.use_count += 1
        if success:
            self.success_count += 1
            self.strength = min(1.0, self.strength + amount)
        else:
            self.strength = max(0.0, self.strength - amount * 0.5)


@dataclass
class ProceduralMemory:
    """Storage for learned procedures and behavioral rules."""

    procedures: Dict[str, Procedure] = field(default_factory=dict)

    def store(
        self,
        name: str,
        condition: str,
        action: str,
        strength: float = 0.5,
    ) -> Procedure:
        """Store a new procedure."""
        proc = Procedure(name=name, condition=condition, action=action, strength=strength)
        self.procedures[proc.procedure_id] = proc
        return proc

    def find_matching(self, context: str) -> List[Procedure]:
        """Find procedures whose condition matches the given context."""
        matches = [proc for proc in self.procedures.values() if proc.condition.lower() in context.lower()]
        return sorted(matches, key=lambda p: p.strength, reverse=True)

    def get_strongest(self, context: str) -> Procedure | None:
        """Get the strongest matching procedure for a context."""
        matches = self.find_matching(context)
        return matches[0] if matches else None

    @property
    def size(self) -> int:
        """Number of stored procedures."""
        return len(self.procedures)

    def __repr__(self) -> str:
        return f"ProceduralMemory(procedures={self.size})"
