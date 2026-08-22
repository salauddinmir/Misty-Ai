"""Inspectable cognitive workspace primitives.

These records are intentionally small and deterministic. They represent the
parts of a cognitive cycle that must be inspectable without exposing a hidden
chain-of-thought or relying on a commercial language model.
"""

from __future__ import annotations

import time
import uuid
from collections import deque
from dataclasses import asdict, dataclass, field
from typing import Any, Deque, Dict, Iterable, List


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


@dataclass(frozen=True)
class CognitiveEvent:
    """A normalized stimulus entering the cognitive system."""

    content: str
    source: str = "text"
    event_type: str = "utterance"
    timestamp: float = field(default_factory=time.time)
    salience: float = 0.5
    reliability: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: _id("evt"))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Evidence:
    """A provenance-carrying item used to support or challenge a hypothesis."""

    source: str
    content: Any
    confidence: float = 0.5
    polarity: str = "support"
    metadata: Dict[str, Any] = field(default_factory=dict)
    evidence_id: str = field(default_factory=lambda: _id("ev"))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class HypothesisRecord:
    """A testable interpretation, answer plan, or predicted outcome."""

    statement: str
    goal: str = "answer"
    premises: List[str] = field(default_factory=list)
    predictions: List[str] = field(default_factory=list)
    evidence: List[Evidence] = field(default_factory=list)
    confidence: float = 0.5
    uncertainty: float = 0.5
    status: str = "proposed"
    hypothesis_id: str = field(default_factory=lambda: _id("hyp"))
    test_count: int = 0
    support_count: int = 0
    contradiction_count: int = 0
    last_tested_at: float | None = None

    def add_evidence(self, evidence: Evidence) -> None:
        self.evidence.append(evidence)
        if evidence.polarity == "contradict":
            self.contradiction_count += 1
        elif evidence.polarity == "support":
            self.support_count += 1
        self._recalculate()

    def mark_tested(self, passed: bool) -> None:
        """Record a bounded test result and update confidence.

        A hypothesis is never considered supported merely because it was
        proposed. A contradictory test explicitly moves it to ``rejected``.
        """
        self.test_count += 1
        self.last_tested_at = time.time()
        self.status = "supported" if passed else "rejected"
        if passed:
            self.confidence = min(1.0, self.confidence + 0.12)
            self.uncertainty = max(0.0, self.uncertainty - 0.12)
        else:
            self.confidence = max(0.0, self.confidence - 0.2)
            self.uncertainty = min(1.0, self.uncertainty + 0.2)

    def mark_contradicted(self, evidence: Evidence) -> None:
        """Attach falsifying evidence and reject the hypothesis."""
        if evidence.polarity != "contradict":
            evidence = Evidence(
                source=evidence.source,
                content=evidence.content,
                confidence=evidence.confidence,
                polarity="contradict",
            )
        self.add_evidence(evidence)
        self.mark_tested(False)

    def _recalculate(self) -> None:
        if not self.evidence:
            return
        support = [item.confidence for item in self.evidence if item.polarity == "support"]
        contradiction = [item.confidence for item in self.evidence if item.polarity == "contradict"]
        support_score = sum(support) / len(support) if support else 0.0
        contradiction_score = sum(contradiction) / len(contradiction) if contradiction else 0.0
        self.confidence = max(0.0, min(1.0, 0.5 + 0.5 * support_score - 0.5 * contradiction_score))
        self.uncertainty = max(0.0, min(1.0, 1.0 - abs(self.confidence - 0.5) * 2.0))

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["evidence"] = [item.to_dict() for item in self.evidence]
        return payload


@dataclass(frozen=True)
class ThoughtTraceSummary:
    """Safe user-facing summary of a cognitive trace."""

    focus: str
    intent: str
    evidence_count: int
    hypothesis_count: int
    confidence: float
    uncertainty: float
    decision: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AppraisalEvent:
    """A reasoned affect/motivation update, not a random UI value."""

    trigger: str
    appraisal: str
    intensity: float
    affected_dimensions: Dict[str, float] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    event_id: str = field(default_factory=lambda: _id("app"))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class GlobalWorkspace:
    """Bounded blackboard for the current cognitive cycle.

    The workspace broadcasts selected records to downstream phases. It keeps
    only a bounded history so a long-running process cannot grow without limit.
    """

    def __init__(self, capacity: int = 32) -> None:
        if capacity < 4:
            raise ValueError("workspace capacity must be at least 4")
        self.capacity = capacity
        self.events: Deque[CognitiveEvent] = deque(maxlen=capacity)
        self.evidence: Deque[Evidence] = deque(maxlen=capacity)
        self.hypotheses: Deque[HypothesisRecord] = deque(maxlen=capacity)
        self.appraisals: Deque[AppraisalEvent] = deque(maxlen=capacity)
        self.active_goal: str = ""
        self.focus: str = ""

    def reset_cycle(self, goal: str = "") -> None:
        self.events.clear()
        self.evidence.clear()
        self.hypotheses.clear()
        self.appraisals.clear()
        self.active_goal = goal
        self.focus = ""

    def broadcast_event(self, event: CognitiveEvent) -> None:
        self.events.append(event)
        self.focus = event.content[:160]

    def broadcast_evidence(self, evidence: Evidence) -> None:
        self.evidence.append(evidence)

    def propose(self, hypothesis: HypothesisRecord) -> None:
        self.hypotheses.append(hypothesis)

    def appraise(self, event: AppraisalEvent) -> None:
        self.appraisals.append(event)

    def best_hypothesis(self) -> HypothesisRecord | None:
        if not self.hypotheses:
            return None
        return max(self.hypotheses, key=lambda item: item.confidence - item.uncertainty * 0.25)

    def summary(self) -> Dict[str, Any]:
        best = self.best_hypothesis()
        return {
            "active_goal": self.active_goal,
            "focus": self.focus,
            "event_count": len(self.events),
            "evidence_count": len(self.evidence),
            "hypothesis_count": len(self.hypotheses),
            "appraisal_count": len(self.appraisals),
            "best_hypothesis": best.to_dict() if best else None,
            "recent_evidence": [
                {
                    "evidence_id": item.evidence_id,
                    "source": item.source,
                    "confidence": item.confidence,
                    "polarity": item.polarity,
                    "content": item.content,
                }
                for item in list(self.evidence)[-5:]
            ],
            "recent_appraisals": [item.to_dict() for item in list(self.appraisals)[-3:]],
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "events": [item.to_dict() for item in self.events],
            "evidence": [item.to_dict() for item in self.evidence],
            "hypotheses": [item.to_dict() for item in self.hypotheses],
            "appraisals": [item.to_dict() for item in self.appraisals],
            "summary": self.summary(),
        }

    def add_evidence_many(self, records: Iterable[Evidence]) -> None:
        for record in records:
            self.broadcast_evidence(record)
