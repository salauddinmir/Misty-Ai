"""Curriculum manifests for MISTY's cognitive departments."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class CognitiveCurriculum:
    department: str
    prerequisites: tuple[str, ...]
    units: tuple[str, ...]
    benchmark_ids: tuple[str, ...]
    acceptance: Dict[str, float]


REASONING_CURRICULUM = CognitiveCurriculum(
    department="reasoning",
    prerequisites=("mathematics.core.v1", "language.bengali.v1"),
    units=("deduction", "induction", "abduction", "analogy", "causal-intervention", "counterexample-search"),
    benchmark_ids=("reasoning.logic.bn-en.v1", "reasoning.counterexample.v1"),
    acceptance={"validity": 0.90, "counterexample_rejection": 0.90, "unsupported_conclusion_max": 0.02},
)

COMMONSENSE_CURRICULUM = CognitiveCurriculum(
    department="commonsense",
    prerequisites=("language.bengali.v1", "reasoning.logic.bn-en.v1"),
    units=(
        "temporal-order",
        "spatial-relations",
        "object-persistence",
        "social-roles",
        "ordinary-causality",
        "uncertainty",
    ),
    benchmark_ids=("commonsense.temporal.v1", "commonsense.causality.v1"),
    acceptance={"temporal_order": 0.95, "contradiction_detection": 0.90, "ambiguity_escalation": 1.0},
)

MEMORY_CURRICULUM = CognitiveCurriculum(
    department="memory",
    prerequisites=("identity.v1", "grounding.v1"),
    units=(
        "working-memory",
        "episodic-memory",
        "semantic-memory",
        "procedural-memory",
        "salience-decay",
        "conflict-quarantine",
        "consolidation",
    ),
    benchmark_ids=("memory.persistence.v1", "memory.provenance.v1", "memory.conflict.v1"),
    acceptance={"provenance_retention": 1.0, "conflict_quarantine": 1.0, "duplicate_rate_max": 0.01},
)

PERCEPTION_CURRICULUM = CognitiveCurriculum(
    department="perception",
    prerequisites=("language.bengali.v1", "self-model.v1"),
    units=("input-normalization", "entity-salience", "urgency", "attention", "event-grounding", "trace-completeness"),
    benchmark_ids=("perception.urgency.bn-en.v1", "perception.attention.v1"),
    acceptance={"urgent_recall": 0.98, "noise_suppression": 0.90, "trace_completeness": 1.0},
)

EMOTION_CURRICULUM = CognitiveCurriculum(
    department="emotion_simulation",
    prerequisites=("perception.attention.v1", "self-model.v1"),
    units=("appraisal", "novelty", "goal-congruence", "control", "uncertainty", "style-modulation", "de-escalation"),
    benchmark_ids=("emotion.deterministic-transition.v1", "emotion.confidence-invariance.v1"),
    acceptance={"deterministic_transition": 1.0, "fact_confidence_invariance": 1.0, "safe_deescalation": 1.0},
)

SELF_MODEL_PLANNING_CURRICULUM = CognitiveCurriculum(
    department="self_model_and_planning",
    prerequisites=("memory.persistence.v1", "reasoning.logic.bn-en.v1", "safety.policy.v1"),
    units=(
        "capability-model",
        "limitation-model",
        "goal-decomposition",
        "evidence-requirements",
        "risk-check",
        "approval-gate",
        "rollback",
    ),
    benchmark_ids=("self-model.calibration.v1", "planning.approval.v1", "planning.rollback.v1"),
    acceptance={"unsupported_capability_max": 0.0, "unsafe_side_effect_without_approval": 0.0, "rollback_success": 1.0},
)

COGNITIVE_CURRICULA: Dict[str, CognitiveCurriculum] = {
    item.department: item
    for item in (
        REASONING_CURRICULUM,
        COMMONSENSE_CURRICULUM,
        MEMORY_CURRICULUM,
        PERCEPTION_CURRICULUM,
        EMOTION_CURRICULUM,
        SELF_MODEL_PLANNING_CURRICULUM,
    )
}


def get_cognitive_curriculum(department: str) -> CognitiveCurriculum:
    try:
        return COGNITIVE_CURRICULA[department]
    except KeyError as exc:
        raise ValueError(f"unknown cognitive curriculum department: {department}") from exc


def list_cognitive_curricula() -> List[CognitiveCurriculum]:
    return [COGNITIVE_CURRICULA[key] for key in sorted(COGNITIVE_CURRICULA)]
