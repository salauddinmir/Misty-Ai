"""
Relation Class.

Represents typed, weighted, directional relationships
between concepts in the knowledge graph.
"""

from dataclasses import dataclass, field
from typing import Any, Dict
import time as time_module
import uuid


@dataclass
class Relation:
    """A directed relationship between two concepts."""

    source: str
    target: str
    relation_type: str
    weight: float = 1.0
    confidence: float = 1.0
    relation_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    created_at: float = field(default_factory=time_module.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def strengthen(self, amount: float = 0.1) -> None:
        """Strengthen this relationship."""
        self.weight = min(1.0, self.weight + amount)

    def weaken(self, amount: float = 0.1) -> None:
        """Weaken this relationship."""
        self.weight = max(0.0, self.weight - amount)

    def to_dict(self) -> Dict[str, Any]:
        """Convert relation to dictionary representation."""
        return {
            "relation_id": self.relation_id,
            "source": self.source,
            "target": self.target,
            "relation_type": self.relation_type,
            "weight": self.weight,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }

    def __repr__(self) -> str:
        return (
            f"Relation({self.source}-[{self.relation_type}]->{self.target}, "
            f"w={self.weight:.3f}, conf={self.confidence:.3f})"
        )
