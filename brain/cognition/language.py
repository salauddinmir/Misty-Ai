"""Deterministic language grounding and compositional response metadata."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GroundedUtterance:
    """A response plus the cognitive evidence used to compose it."""

    text: str
    language: str
    intent: str
    confidence: float
    uncertainty: float
    claims: tuple[str, ...]
    strategy: str
    grounding_source: str = "fallback"
    evidence_sources: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "language": self.language,
            "intent": self.intent,
            "confidence": self.confidence,
            "uncertainty": self.uncertainty,
            "claims": list(self.claims),
            "strategy": self.strategy,
            "grounding_source": self.grounding_source,
            "evidence_sources": list(self.evidence_sources),
            "evidence_ids": list(self.evidence_ids),
        }


class LanguageGrounder:
    """Compose inspectable output metadata without an external language model.

    The grounder deliberately does not invent prose. It records which bounded
    cognitive sources justify the already-selected deterministic response.
    """

    @staticmethod
    def ground(
        text: str,
        *,
        raw_input: str,
        intent: str,
        confidence: float,
        evidence_count: int,
        hypothesis_count: int,
        strategy: str = "deterministic_action",
        grounding_source: str = "fallback",
        evidence_sources: tuple[str, ...] = (),
        evidence_ids: tuple[str, ...] = (),
    ) -> GroundedUtterance:
        has_bengali = any("\u0980" <= char <= "\u09ff" for char in raw_input)
        claims: list[str] = []
        if evidence_count:
            claims.append("workspace_evidence")
            if hypothesis_count:
                claims.append("workspace_hypothesis")
        if intent in {"math", "physics"}:
            claims.append(f"deterministic_{intent}_engine")
        if not claims:
            claims.append("intent_and_dialogue_context")
        bounded_confidence = max(0.0, min(1.0, float(confidence)))
        return GroundedUtterance(
            text=text,
            language="bn" if has_bengali else "en",
            intent=intent,
            confidence=bounded_confidence,
            uncertainty=round(1.0 - bounded_confidence, 6),
            claims=tuple(claims),
            strategy=strategy,
            grounding_source=grounding_source,
            evidence_sources=tuple(dict.fromkeys(evidence_sources)),
            evidence_ids=tuple(dict.fromkeys(evidence_ids)),
        )
