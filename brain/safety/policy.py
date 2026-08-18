"""Deterministic safety and autonomy gates for MISTY learning actions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping


class Decision(str, Enum):
    ALLOW = "allow"
    QUARANTINE = "quarantine"
    REQUIRE_APPROVAL = "require_approval"
    REJECT = "reject"


@dataclass(frozen=True)
class SafetyDecision:
    decision: Decision
    reason: str
    audit_code: str
    requires_human: bool = False


@dataclass(frozen=True)
class AutonomyPolicy:
    min_memory_confidence: float = 0.75
    min_consolidation_observations: int = 2
    max_tick_actions: int = 4
    allow_external_side_effects: bool = False
    allow_identity_mutation: bool = False

    def validate(self) -> None:
        if not 0 <= self.min_memory_confidence <= 1:
            raise ValueError("min_memory_confidence must be between 0 and 1")
        if self.min_consolidation_observations < 1:
            raise ValueError("min_consolidation_observations must be positive")
        if self.max_tick_actions < 1:
            raise ValueError("max_tick_actions must be positive")


def evaluate_learning(
    candidate: Mapping[str, Any],
    *,
    policy: AutonomyPolicy | None = None,
) -> SafetyDecision:
    """Gate a proposed memory/rule before it enters durable knowledge."""
    policy = policy or AutonomyPolicy()
    policy.validate()
    confidence = float(candidate.get("confidence", 0.0))
    observations = int(candidate.get("observations", 1))
    provenance = candidate.get("source_ref")
    contradicts = bool(candidate.get("contradicts_existing", False))
    if not provenance:
        return SafetyDecision(Decision.REJECT, "missing provenance", "LEARN_NO_PROVENANCE")
    if contradicts:
        return SafetyDecision(Decision.QUARANTINE, "contradicts existing knowledge", "LEARN_CONTRADICTION")
    if confidence < policy.min_memory_confidence or observations < policy.min_consolidation_observations:
        return SafetyDecision(
            Decision.QUARANTINE, "insufficient evidence for consolidation", "LEARN_INSUFFICIENT_EVIDENCE"
        )
    return SafetyDecision(Decision.ALLOW, "evidence threshold satisfied", "LEARN_ALLOWED")


def evaluate_action(action: Mapping[str, Any], *, policy: AutonomyPolicy | None = None) -> SafetyDecision:
    """Gate an autonomous action; external side effects always need explicit policy."""
    policy = policy or AutonomyPolicy()
    policy.validate()
    action_type = str(action.get("type", "unknown"))
    if action_type in {"identity_mutation", "delete_memory", "external_side_effect"}:
        if action_type == "identity_mutation" and policy.allow_identity_mutation:
            return SafetyDecision(
                Decision.REQUIRE_APPROVAL, "identity change requires review", "ACT_IDENTITY_REVIEW", True
            )
        if action_type == "external_side_effect" and policy.allow_external_side_effects:
            return SafetyDecision(
                Decision.REQUIRE_APPROVAL, "external side effect requires review", "ACT_EXTERNAL_REVIEW", True
            )
        return SafetyDecision(Decision.REJECT, "action is disabled by autonomy policy", "ACT_POLICY_REJECT")
    if action.get("requires_human", False):
        return SafetyDecision(Decision.REQUIRE_APPROVAL, "action declares human approval", "ACT_DECLARED_REVIEW", True)
    return SafetyDecision(Decision.ALLOW, "bounded internal action", "ACT_INTERNAL_ALLOWED")
