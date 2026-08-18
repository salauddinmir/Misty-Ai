"""Phase 14 tests: bounded autonomous hypothesis loop.

Covers:
- Per-tick evidence budget enforcement in Brain.autonomous_reflection_tick
- Consolidation per-cycle mutation budget (max_consolidations_per_cycle)
- Consolidation safety gate integration (evaluate_learning quarantine)
- Last autonomous tick metrics (tick_index, evidence_budget, elapsed_ms,
  quarantined_candidates) surfaced in the brain state snapshot.
"""

from brain.core.brain import Brain
from brain.learning.consolidation import MemoryConsolidator
from brain.memory.episodic import EpisodicMemory
from brain.memory.semantic import SemanticMemory
from brain.memory.working import MemoryItem, WorkingMemory
from brain.safety.policy import AutonomyPolicy, Decision, evaluate_learning


def _seeded_item(index: int = 0, prefix: str = "k", observations: int = 5, activation: float = 0.9) -> MemoryItem:
    """Build a working-memory item whose provenance and observation count
    let it pass the learning gate; its content must not exceed 120 chars."""
    item = MemoryItem(
        content={
            "subject": f"{prefix}subject{index}",
            "predicate": f"pred{index}",
            "object": f"obj{index}",
            "source": "seed",
            "observations": observations,
        }
    )
    item.activation = activation
    return item


class TestAutonomousTickBudget:
    """The reflection tick never gathers more evidence than its budget."""

    async def test_evidence_count_bounded_by_budget(self) -> None:
        brain = Brain()
        brain.max_evidence_per_tick = 2
        # Seed semantic memory with many facts that overlap the default goal.
        for index in range(20):
            brain.semantic_memory.store_fact(
                subject="knowledge",
                predicate=f"review_{index}",
                obj=f"value_{index}",
                confidence=0.9,
                source="seed",
            )
        await brain.autonomous_reflection_tick()
        assert brain.last_autonomous_tick is not None
        assert brain.last_autonomous_tick["evidence_count"] <= brain.max_evidence_per_tick

    async def test_tick_records_index_and_latency(self) -> None:
        brain = Brain()
        await brain.autonomous_reflection_tick()
        await brain.autonomous_reflection_tick()
        snapshot = brain.last_autonomous_tick
        assert snapshot is not None
        assert snapshot["tick_index"] == 2
        assert isinstance(snapshot["elapsed_ms"], float)
        assert snapshot["elapsed_ms"] >= 0.0
        assert snapshot["evidence_budget"] == brain.max_evidence_per_tick

    async def test_tick_state_snapshot_includes_metrics(self) -> None:
        brain = Brain()
        await brain.autonomous_reflection_tick()
        state = brain.get_state()
        snapshot = state["last_autonomous_tick"]
        assert snapshot is not None
        required_keys = (
            "tick_index", "evidence_budget", "evidence_count", "elapsed_ms", "outcome", "quarantined_candidates",
        )
        for key in required_keys:
            assert key in snapshot, f"missing metric: {key}"
        assert isinstance(snapshot["quarantined_candidates"], list)


class TestConsolidationTickBudget:
    """A consolidation cycle stops once its mutation budget is exhausted."""

    def test_max_consolidations_per_cycle(self) -> None:
        consolidator = MemoryConsolidator(max_consolidations_per_cycle=3)
        working = WorkingMemory()
        # Items carry provenance and an observations hint so they pass the
        # learning gate; the budget cap is what truncates the cycle.
        for index in range(10):
            working.items[f"key_{index}"] = _seeded_item(index, prefix="s")
        consolidated = consolidator.consolidate(working, EpisodicMemory(), None)
        assert len(consolidated) == 3

    def test_consolidation_stops_at_budget_boundary(self) -> None:
        consolidator = MemoryConsolidator(max_consolidations_per_cycle=2)
        working = WorkingMemory()
        for index in range(5):
            working.items[f"k{index}"] = _seeded_item(index, prefix="x")
        semantic = SemanticMemory()
        consolidated = consolidator.consolidate(working, None, semantic)
        assert len(consolidated) == 2
        assert len(semantic.facts) == 2

    def test_budget_resets_each_cycle(self) -> None:
        consolidator = MemoryConsolidator(max_consolidations_per_cycle=2)
        working = WorkingMemory()
        for index in range(4):
            working.items[f"a{index}"] = _seeded_item(index, prefix="a")
        first = consolidator.consolidate(working, EpisodicMemory(), None)
        assert len(first) == 2
        # A fresh working memory set is a new cycle; previously consolidated
        # keys are still skipped but the cycle cap applies to new ones.
        working2 = WorkingMemory()
        for index in range(4):
            working2.items[f"b{index}"] = _seeded_item(index, prefix="b")
        second = consolidator.consolidate(working2, EpisodicMemory(), None)
        assert len(second) == 2


class TestConsolidationSafetyGate:
    """Candidates failing the learning gate are quarantined, not stored."""

    def test_low_confidence_candidate_quarantined(self) -> None:
        consolidator = MemoryConsolidator(safety_gate_threshold=0.5)
        working = WorkingMemory()
        item = MemoryItem(
            content={
                "subject": "x",
                "predicate": "is_y",
                "object": "y",
                "source": "inference",
                "observations": 3,
            }
        )
        item.activation = 0.6  # above gate threshold but below 0.75 minimum
        working.items["weak"] = item
        semantic = SemanticMemory()
        consolidated = consolidator.consolidate(working, None, semantic)
        assert consolidated == []
        assert len(semantic.facts) == 0
        assert len(consolidator.rejected_candidates) == 1
        assert consolidator.rejected_candidates[0]["decision"] == Decision.QUARANTINE.value

    def test_missing_provenance_candidate_rejected(self) -> None:
        consolidator = MemoryConsolidator(safety_gate_threshold=0.5)
        working = WorkingMemory()
        item = MemoryItem(
            content={
                "subject": "x",
                "predicate": "is_z",
                "object": "z",
                # Deliberately no "source" key so provenance is missing.
                "observations": 3,
            }
        )
        item.activation = 0.8
        working.items["unproven"] = item
        semantic = SemanticMemory()
        consolidator.consolidate(working, None, semantic)
        assert len(semantic.facts) == 0
        assert consolidator.rejected_candidates[0]["audit_code"] == "LEARN_NO_PROVENANCE"

    def test_good_candidate_passes_through(self) -> None:
        consolidator = MemoryConsolidator(safety_gate_threshold=0.5)
        working = WorkingMemory()
        working.items["strong"] = _seeded_item()
        semantic = SemanticMemory()
        consolidated = consolidator.consolidate(working, None, semantic)
        assert consolidated == ["strong"]
        assert semantic.facts.get("ksubject0:pred0:obj0") is not None
        assert consolidator.rejected_candidates == []

    def test_contradicting_candidate_quarantined(self) -> None:
        consolidator = MemoryConsolidator(safety_gate_threshold=0.5)
        working = WorkingMemory()
        item = MemoryItem(
            content={
                "subject": "x",
                "predicate": "is_v",
                "object": "v",
                "source": "seed",
                "observations": 3,
                "contradicts_existing": True,
            }
        )
        item.activation = 0.95
        working.items["contradict"] = item
        semantic = SemanticMemory()
        consolidator.consolidate(working, None, semantic)
        assert len(consolidator.rejected_candidates) == 1
        assert consolidator.rejected_candidates[0]["audit_code"] == "LEARN_CONTRADICTION"

    def test_low_importance_items_skip_the_gate(self) -> None:
        consolidator = MemoryConsolidator(safety_gate_threshold=0.5)
        working = WorkingMemory()
        item = MemoryItem(
            content={
                "subject": "x",
                "predicate": "is_u",
                "object": "u",
                "source": "seed",
            }
        )
        item.activation = 0.35
        working.items["quiet"] = item
        semantic = SemanticMemory()
        consolidated = consolidator.consolidate(working, None, semantic)
        assert consolidated == ["quiet"]
        assert consolidator.rejected_candidates == []

    def test_policy_override_relaxes_gate(self) -> None:
        consolidator = MemoryConsolidator(safety_gate_threshold=0.5)
        working = WorkingMemory()
        working.items["relaxed"] = _seeded_item()
        semantic = SemanticMemory()
        permissive = AutonomyPolicy(min_memory_confidence=0.75, min_consolidation_observations=1)
        consolidated = consolidator.consolidate(working, None, semantic, policy=permissive)
        assert consolidated == ["relaxed"]
        assert consolidator.rejected_candidates == []


class TestEvaluateLearningBasics:
    """The learning gate itself behaves deterministically."""

    def test_allowed_candidate(self) -> None:
        decision = evaluate_learning(
            {"confidence": 0.8, "observations": 3, "source_ref": "seed", "contradicts_existing": False}
        )
        assert decision.decision is Decision.ALLOW

    def test_repeated_call_identical(self) -> None:
        candidate = {"confidence": 0.8, "observations": 3, "source_ref": "seed", "contradicts_existing": False}
        first = evaluate_learning(candidate)
        second = evaluate_learning(candidate)
        assert first == second
