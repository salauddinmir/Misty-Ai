"""Phase 45: consolidation sweep — rehearsal, quarantine cleanup, merge."""

import pytest

from brain.core.brain import Brain
from brain.learning.consolidation_sweep import (
    _MAX_LOG_ENTRIES,
    _PROTECTED_SOURCES,
    ConsolidationEngine,
)


@pytest.fixture
def brain() -> Brain:
    return Brain()


@pytest.fixture
def engine(brain: Brain) -> ConsolidationEngine:
    return ConsolidationEngine(brain)


# ---------------------------------------------------------------------------
# Sweep mechanics
# ---------------------------------------------------------------------------


class TestConsolidationSweep:
    def test_brain_has_consolidation_engine(self, brain):
        assert isinstance(brain.consolidation_engine, ConsolidationEngine)

    def test_sweep_empty_memory_is_noop(self, engine):
        # With no facts at all (clearing pre-seeded curriculum) the sweep
        # must be a clean no-op.
        engine.brain.semantic_memory.facts.clear()
        summary = engine.consolidation_sweep()
        assert summary == {
            "scanned": 0,
            "rehearsed": 0,
            "merged": 0,
            "removed": 0,
            "protected": 0,
        }

    def test_rehearse_mid_confidence_fact(self, engine):
        engine.brain.semantic_memory.store_fact("rh", "has", "prop", confidence=0.6, source="web_learning")
        before = engine.brain.concept_graph.get_concept("rh")
        before_act = getattr(before, "activation", 0.0)
        summary = engine.consolidation_sweep()
        assert summary["rehearsed"] >= 1
        actions = [d.action for d in engine.decisions]
        assert "rehearsed" in actions
        # The rehearsed fact's subject concept should have gained activation.
        after = engine.brain.concept_graph.get_concept("rh")
        assert getattr(after, "activation", 0.0) >= before_act

    def test_very_weak_facts_not_rehearsed(self, engine):
        engine.brain.semantic_memory.store_fact("wk", "is", "x", confidence=0.15, source="web_learning")
        summary = engine.consolidation_sweep()
        assert summary["rehearsed"] == 0
        assert "rehearsal:wk:is:x" not in engine.brain.working_memory.items

    def test_high_confidence_facts_not_rehearsed(self, engine):
        engine.brain.semantic_memory.store_fact("st", "is", "y", confidence=0.95, source="web_learning")
        summary = engine.consolidation_sweep()
        assert summary["rehearsed"] == 0

    def test_protected_facts_anchored_not_merged(self, engine):
        engine.brain.semantic_memory.store_fact("pr", "is", "z", confidence=0.5, source="curriculum")
        summary = engine.consolidation_sweep()
        assert summary["protected"] >= 1
        assert summary["merged"] == 0
        assert "pr:is:z" in engine.brain.semantic_memory.facts

    def test_merge_duplicates_keeps_strongest(self, engine):
        mem = engine.brain.semantic_memory
        mem.store_fact("mg", "capital_of", "old_wrong", confidence=0.4, source="web_learning")
        mem.store_fact("mg", "capital_of", "new_right", confidence=0.9, source="web_learning")
        summary = engine.consolidation_sweep()
        assert summary["merged"] >= 1
        remaining = mem.query(subject="mg")
        assert len(remaining) == 1
        assert remaining[0].obj == "new_right"
        assert remaining[0].confidence == 0.9

    def test_merge_respects_sweep_budget(self, engine):
        mem = engine.brain.semantic_memory
        for i in range(engine.max_merged_per_sweep * 2 + 3):
            mem.store_fact("bd", "dup_p", f"v{i}", confidence=0.5, source="web_learning")
        summary = engine.consolidation_sweep()
        assert 1 <= summary["merged"] <= engine.max_merged_per_sweep
        remaining = max(0, len(mem.query(subject="bd")) - 1)
        assert summary["merged"] == engine.max_merged_per_sweep or summary["merged"] == remaining

    def test_quarantine_losers_removed(self, engine):
        mem = engine.brain.semantic_memory
        key = mem.store_fact("q_x", "q_p", "loser", confidence=0.3, source="web_learning")
        engine.brain._learning_quarantine = [{"fact_key": key, "reason": "defeated"}]
        summary = engine.consolidation_sweep()
        assert summary["removed"] >= 1
        assert key not in mem.facts
        actions = [d.action for d in engine.decisions]
        assert "quarantine_removed" in actions

    def test_log_bounded(self, engine):
        mem = engine.brain.semantic_memory
        for i in range(_MAX_LOG_ENTRIES * 2):
            mem.store_fact(f"log{i}", "p", "o", confidence=0.6, source="web_learning")
            engine.consolidation_sweep()
        assert len(engine.decisions) <= _MAX_LOG_ENTRIES

    def test_get_state_includes_consolidation(self, brain):
        state = brain.get_state()
        assert "consolidation" in state
        assert state["consolidation"]["enabled"] is True

    def test_state_route_exposes_consolidation(self):
        from apps.api.routes.brain import BrainStateResponse

        assert "consolidation" in BrainStateResponse.model_fields
        app = None
        try:
            from apps.api.app import create_app

            app = create_app()
        except ImportError:
            pass
        if app is not None:
            from fastapi.testclient import TestClient

            with TestClient(app) as client:
                resp = client.get("/api/brain/state")
                assert "consolidation" in resp.json()

    def test_protected_sources_complete(self):
        expected = {
            "training",
            "user_input",
            "curriculum",
            "commonsense_layer",
            "misty-mathematics-phase29",
            "misty-physics-phase30",
            "misty-literature-phase31",
            "misty-culture-phase32",
            "conversation_corpus",
        }
        assert expected.issubset(set(_PROTECTED_SOURCES))

    def test_reflection_tick_runs_sweep(self, brain):
        brain.semantic_memory.store_fact("tk", "has", "q", confidence=0.6, source="web_learning")
        import asyncio

        asyncio.run(brain.autonomous_reflection_tick())
        actions = [d.action for d in brain.consolidation_engine.decisions]
        assert "rehearsed" in actions or "protected" in actions
