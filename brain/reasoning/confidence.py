"""
Confidence Scoring.

Computes confidence scores for derived conclusions.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class ConfidenceScorer:
    """Computes confidence scores for reasoning outputs."""

    base_confidence: float = 1.0
    decay_per_hop: float = 0.1
    min_confidence: float = 0.1

    def score_direct(self, source_confidence: float = 1.0) -> float:
        """Score confidence for a directly observed/stated fact."""
        return min(self.base_confidence, source_confidence)

    def score_derived(
        self,
        premise_confidences: List[float],
        rule_confidence: float = 1.0,
        inference_depth: int = 1,
    ) -> float:
        """Score confidence for a derived conclusion."""
        if not premise_confidences:
            return self.min_confidence

        combined = 1.0
        for conf in premise_confidences:
            combined *= conf

        combined *= rule_confidence
        depth_factor = max(0.0, 1.0 - (inference_depth * self.decay_per_hop))
        combined *= depth_factor

        return max(self.min_confidence, combined)

    def combine(self, confidences: List[float]) -> float:
        """Combine multiple confidence scores."""
        if not confidences:
            return self.min_confidence

        result = 1.0
        for conf in confidences:
            result *= conf
        return max(self.min_confidence, result)

    def __repr__(self) -> str:
        return (
            f"ConfidenceScorer(base={self.base_confidence}, "
            f"decay_per_hop={self.decay_per_hop})"
        )
