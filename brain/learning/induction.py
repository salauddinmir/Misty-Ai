"""Evidence-gated autonomous semantic induction."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from brain.memory.semantic import SemanticMemory


@dataclass
class LearningCandidate:
    """A possible fact awaiting independent/repeated support."""

    subject: str
    predicate: str
    obj: str
    observations: int = 0
    confidence_sum: float = 0.0
    sources: set[str] = field(default_factory=set)

    @property
    def confidence(self) -> float:
        if self.observations == 0:
            return 0.0
        return self.confidence_sum / self.observations


@dataclass
class EvidenceGatedInducer:
    """Promote candidates only after repeated, sufficiently confident evidence."""

    min_observations: int = 2
    min_confidence: float = 0.75
    candidates: Dict[str, LearningCandidate] = field(default_factory=dict)
    promoted_count: int = 0

    def observe(
        self,
        subject: str,
        predicate: str,
        obj: str,
        *,
        confidence: float = 1.0,
        source: str = "cycle",
    ) -> LearningCandidate:
        key = f"{subject}:{predicate}:{obj}"
        candidate = self.candidates.setdefault(
            key,
            LearningCandidate(subject=subject, predicate=predicate, obj=obj),
        )
        candidate.observations += 1
        candidate.confidence_sum += max(0.0, min(1.0, confidence))
        candidate.sources.add(source)
        return candidate

    def promote_ready(self, semantic_memory: SemanticMemory | None = None) -> List[str]:
        promoted: List[str] = []
        for key, candidate in list(self.candidates.items()):
            if candidate.observations < self.min_observations:
                continue
            if candidate.confidence < self.min_confidence:
                continue
            if semantic_memory is not None:
                semantic_memory.store_fact(
                    subject=candidate.subject,
                    predicate=candidate.predicate,
                    obj=candidate.obj,
                    confidence=candidate.confidence,
                    source="induced_repeated_evidence",
                )
            promoted.append(key)
            del self.candidates[key]
            self.promoted_count += 1
        return promoted

    def pending(self) -> List[LearningCandidate]:
        return list(self.candidates.values())
