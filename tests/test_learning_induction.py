"""Tests for evidence-gated autonomous semantic learning."""

from brain.learning import EvidenceGatedInducer
from brain.memory.semantic import SemanticMemory


def test_candidate_waits_for_repeated_evidence() -> None:
    inducer = EvidenceGatedInducer()
    memory = SemanticMemory()

    inducer.observe("water", "is_a", "liquid", confidence=0.95, source="lesson")
    assert inducer.promote_ready(memory) == []
    assert memory.size == 0

    promoted = inducer.observe("water", "is_a", "liquid", confidence=0.9, source="observation")
    assert promoted.observations == 2
    assert inducer.promote_ready(memory) == ["water:is_a:liquid"]
    assert memory.query(subject="water", predicate="is_a")[0].source == "induced_repeated_evidence"


def test_low_confidence_observations_do_not_promote() -> None:
    inducer = EvidenceGatedInducer()
    memory = SemanticMemory()

    for source in ("a", "b", "c"):
        inducer.observe("x", "relates_to", "y", confidence=0.4, source=source)

    assert inducer.promote_ready(memory) == []
    assert len(inducer.pending()) == 1
    assert memory.size == 0
