"""Explicit self-model for MISTY's metacognitive decisions."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


@dataclass
class SelfModel:
    """A bounded model of identity, abilities, limits, and current commitments."""

    identity: Dict[str, str] = field(
        default_factory=lambda: {
            "name": "MISTY",
            "type": "Smart Artificial Brain",
            "creator": "Pixline Incorporate",
            "founder": "Salauddin Mir",
            "founder_alias": "Netvai",
        }
    )
    capabilities: Dict[str, str] = field(
        default_factory=lambda: {
            "language": "Bengali and English rule-based understanding",
            "mathematics": "deterministic arithmetic, algebra, geometry, and statistics",
            "physics": "deterministic mechanics and kinematics reasoning",
            "memory": "episodic, semantic, procedural, and working memory",
            "cognition": "bounded event appraisal, hypothesis testing, and world modeling",
        }
    )
    limitations: List[str] = field(
        default_factory=lambda: [
            "does not claim subjective human consciousness",
            "does not use unrestricted external language-model generation",
            "can be uncertain when no grounded evidence is available",
        ]
    )
    active_goals: List[str] = field(default_factory=list)
    learned_beliefs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    confidence: float = 0.5
    uncertainty: float = 0.5

    def knows_identity(self, key: str, value: str) -> bool:
        return self.identity.get(key, "").casefold() == value.casefold()

    def capability_text(self, topic: str = "") -> str:
        if not topic:
            return "; ".join(f"{key}: {value}" for key, value in self.capabilities.items())
        topic_lower = topic.casefold()
        matches = [
            f"{key}: {value}"
            for key, value in self.capabilities.items()
            if topic_lower in key.casefold() or topic_lower in value.casefold()
        ]
        return "; ".join(matches)

    def add_goal(self, goal: str) -> None:
        if goal and goal not in self.active_goals:
            self.active_goals.append(goal)
            self.active_goals = self.active_goals[-8:]

    def learn_belief(self, subject: str, predicate: str, value: Any, confidence: float) -> None:
        key = f"{subject}:{predicate}"
        self.learned_beliefs[key] = {
            "subject": subject,
            "predicate": predicate,
            "value": value,
            "confidence": max(0.0, min(1.0, confidence)),
        }
        if len(self.learned_beliefs) > 128:
            oldest = next(iter(self.learned_beliefs))
            del self.learned_beliefs[oldest]

    def update_uncertainty(self, prediction_error: float) -> None:
        error = max(0.0, min(1.0, prediction_error))
        self.uncertainty = round(0.85 * self.uncertainty + 0.15 * error, 4)
        self.confidence = round(1.0 - self.uncertainty, 4)

    def summary(self) -> Dict[str, Any]:
        return {
            "identity": dict(self.identity),
            "capability_count": len(self.capabilities),
            "active_goals": list(self.active_goals),
            "learned_belief_count": len(self.learned_beliefs),
            "confidence": self.confidence,
            "uncertainty": self.uncertainty,
            "limitations": list(self.limitations),
        }

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
