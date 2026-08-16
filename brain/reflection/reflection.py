"""
Reflection and Meta-Cognition.

Self-monitoring system that evaluates the brain's own performance.
"""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class PerformanceRecord:
    """Record of a processing cycle's performance."""

    cycle_number: int
    input_type: str = "unknown"
    goal_achieved: bool = False
    response_quality: float = 0.5
    processing_time: float = 0.0
    confidence: float = 0.5


@dataclass
class ReflectionEngine:
    """Meta-cognitive self-monitoring system."""

    performance_history: List[PerformanceRecord] = field(default_factory=list)
    max_history: int = 100
    cycle_count: int = 0
    success_count: int = 0

    def record_performance(
        self,
        input_type: str = "unknown",
        goal_achieved: bool = False,
        response_quality: float = 0.5,
        processing_time: float = 0.0,
        confidence: float = 0.5,
    ) -> PerformanceRecord:
        """Record a cycle's performance for self-evaluation."""
        self.cycle_count += 1
        if goal_achieved:
            self.success_count += 1

        record = PerformanceRecord(
            cycle_number=self.cycle_count,
            input_type=input_type,
            goal_achieved=goal_achieved,
            response_quality=response_quality,
            processing_time=processing_time,
            confidence=confidence,
        )
        self.performance_history.append(record)

        if len(self.performance_history) > self.max_history:
            self.performance_history.pop(0)

        return record

    def evaluate_recent_performance(self, window: int = 10) -> Dict[str, float]:
        """Evaluate recent performance metrics."""
        recent = self.performance_history[-window:]
        if not recent:
            return {
                "success_rate": 0.0,
                "avg_quality": 0.0,
                "avg_confidence": 0.0,
            }

        success_rate = sum(1 for r in recent if r.goal_achieved) / len(recent)
        avg_quality = sum(r.response_quality for r in recent) / len(recent)
        avg_confidence = sum(r.confidence for r in recent) / len(recent)

        return {
            "success_rate": success_rate,
            "avg_quality": avg_quality,
            "avg_confidence": avg_confidence,
        }

    def detect_problems(self) -> List[str]:
        """Detect performance problems that need attention."""
        problems = []
        metrics = self.evaluate_recent_performance()

        if metrics["success_rate"] < 0.5:
            problems.append("Low success rate - may need to adjust processing strategy")
        if metrics["avg_confidence"] < 0.3:
            problems.append("Low confidence - may lack sufficient knowledge")
        if metrics["avg_quality"] < 0.4:
            problems.append("Low response quality - may need more context or learning")

        return problems

    @property
    def overall_success_rate(self) -> float:
        """Overall success rate across all cycles."""
        if self.cycle_count == 0:
            return 0.0
        return self.success_count / self.cycle_count

    def __repr__(self) -> str:
        return f"ReflectionEngine(cycles={self.cycle_count}, success_rate={self.overall_success_rate:.2f})"
