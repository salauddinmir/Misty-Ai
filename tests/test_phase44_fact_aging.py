"""Phase 44: fact aging and confidence decay for web-learned knowledge."""

import time

import pytest

from brain.core.brain import Brain
from brain.learning.fact_aging import (
    _HALF_LIFE_DAYS,
    _MAX_LOG_ENTRIES,
    _PROTECTED_SOURCES,
    FactAger,
)
from brain.memory.semantic import SemanticMemory


@pytest.fixture
def brain() -> Brain:
    return Brain()


@pytest.fixture
def ager(brain: Brain) -> FactAger:
    return FactAger(brain)


@pytest.fixture
def memory() -> SemanticMemory:
    return SemanticMemory()


# ---------------------------------------------------------------------------
# Decay mechanics
# ---------------------------------------------------------------------------


class TestDecayMechanics:
    def test_decay_half_life(self, memory):
        fact = memory.store_fact("a", "is", "b", confidence=0.8, source="web_learning")
        now = memory.facts[fact].created_at
        after = FactAger._decayed_confidence(0.8, _HALF_LIFE_DAYS)
        assert abs(after - 0.4) < 1e-9
        assert now > 0

    def test_decay_monotone_in_time(self, ager):
        older = ager._decayed_confidence(0.8, 90.0)
        newer = ager._decayed_confidence(0.8, 30.0)
        assert older < newer < 0.8

    def test_decay_bounded_at_zero(self, ager):
        assert ager._decayed_confidence(0.5, 3650.0) >= 0.0

    def test_recent_facts_unchanged(self, ager):
        assert ager._decayed_confidence(0.7, 0.0) == 0.7


# ---------------------------------------------------------------------------
# Aging pass behavior
# ---------------------------------------------------------------------------


class TestAgingPass:
    def test_decay_applied_to_web_learning_fact(self, ager):
        now = time.time()
        ager.brain.semantic_memory.store_fact("x", "y", "z", confidence=0.9, source="web_learning")
        fact = ager.brain.semantic_memory.query(subject="x")[0]
        # Pretend the fact was stored one half-life ago.
        fact.created_at = now - _HALF_LIFE_DAYS * 86400.0
        summary = ager.age_facts(now=now)
        assert summary["decayed"] >= 1
        assert fact.confidence < 0.5  # below half of 0.9

    def test_protected_sources_never_decayed(self, ager):
        now = time.time()
        key = ager.brain.semantic_memory.store_fact("p", "q", "r", confidence=1.0, source="user_input")
        fact = ager.brain.semantic_memory.facts[key]
        fact.created_at = now - 365 * 86400.0
        summary = ager.age_facts(now=now)
        assert summary["protected"] >= 1
        assert fact.confidence == 1.0
        assert key in ager.brain.semantic_memory.facts

    def test_protected_sources_never_pruned(self, ager):
        now = time.time()
        key = ager.brain.semantic_memory.store_fact("cur", "subject", "math", confidence=1.0, source="curriculum")
        fact = ager.brain.semantic_memory.facts[key]
        fact.created_at = now - 10000 * 86400.0
        summary = ager.age_facts(now=now)
        assert key in ager.brain.semantic_memory.facts
        assert summary["pruned"] == 0

    def test_old_web_fact_below_threshold_is_pruned(self, ager):
        now = time.time()
        key = ager.brain.semantic_memory.store_fact("o", "o", "o", confidence=0.5, source="web_learning")
        fact = ager.brain.semantic_memory.facts[key]
        fact.created_at = now - 400 * 86400.0  # ~4.4 half-lives → 0.025
        summary = ager.age_facts(now=now)
        assert summary["pruned"] >= 1
        assert key not in ager.brain.semantic_memory.facts

    def test_fresh_web_fact_is_refreshed_not_decayed(self, ager):
        now = time.time()
        ager.brain.semantic_memory.store_fact("f", "f", "f", confidence=0.8, source="web_learning")
        target = ager.brain.semantic_memory.query(subject="f")[0]
        summary = ager.age_facts(now=now)
        assert summary["refreshed"] >= 1
        assert target.confidence == 0.8

    def test_accessed_at_refreshed_each_sweep(self, ager):
        now = time.time()
        key = ager.brain.semantic_memory.store_fact("s", "s", "s", confidence=0.7, source="web_learning")
        fact = ager.brain.semantic_memory.facts[key]
        before = fact.accessed_at
        later = now + 60.0
        ager.age_facts(now=later)
        assert ager.brain.semantic_memory.facts[key].accessed_at >= later
        assert ager.brain.semantic_memory.facts[key].accessed_at != before

    def test_junk_fact_pruned_immediately(self, ager):
        now = time.time()
        key = ager.brain.semantic_memory.store_fact("jnk_x", "jnk_p", "jnk_o", confidence=0.15, source="web_learning")
        summary = ager.age_facts(now=now)
        assert key not in ager.brain.semantic_memory.facts
        assert summary["pruned"] >= 1

    def test_sweep_empty_memory_is_noop(self, ager):
        # A brand-new empty memory should produce an all-zero sweep.
        ager.brain.semantic_memory.facts.clear()
        summary = ager.age_facts(now=time.time())
        assert summary == {
            "scanned": 0,
            "decayed": 0,
            "refreshed": 0,
            "pruned": 0,
            "protected": 0,
            "skipped": 0,
        }

    def test_every_fact_decides_is_recorded(self, ager):
        now = time.time()
        ager.brain.semantic_memory.store_fact("d1", "d1", "d1", confidence=0.9, source="web_learning")
        ager.brain.semantic_memory.store_fact("d2", "d2", "d2", confidence=0.9, source="user_input")
        fact = next(f for f in ager.brain.semantic_memory.facts.values() if f.subject == "d1")
        fact.created_at = now - _HALF_LIFE_DAYS * 86400.0
        ager.age_facts(now=now)
        actions = [d.action for d in ager.decisions]
        assert "decayed" in actions
        assert "protected" in actions

    def test_log_bounded_at_max_entries(self, ager):
        now = time.time()
        for i in range(_MAX_LOG_ENTRIES * 2):
            ager.brain.semantic_memory.store_fact(f"b{i}", "b", "b", confidence=0.9, source="web_learning")
            ager.brain.semantic_memory.facts[f"b{i}:b:b"].created_at = now - 100 * 86400.0
            ager.age_facts(now=now)
        assert len(ager.decisions) <= _MAX_LOG_ENTRIES


# ---------------------------------------------------------------------------
# Brain wiring
# ---------------------------------------------------------------------------


class TestBrainWiring:
    def test_brain_has_fact_ager(self, brain):
        assert isinstance(brain.fact_ager, FactAger)

    def test_get_state_includes_fact_aging(self, brain):
        state = brain.get_state()
        assert "fact_aging" in state
        assert state["fact_aging"]["enabled"] is True

    def test_reflection_tick_runs_aging_sweep(self, brain):
        now = time.time()
        brain.semantic_memory.store_fact("t", "t", "t", confidence=0.9, source="web_learning")
        fact = next(iter(brain.semantic_memory.facts.values()))
        fact.created_at = now - _HALF_LIFE_DAYS * 86400.0
        import asyncio

        asyncio.run(brain.autonomous_reflection_tick())
        assert brain.fact_ager.decisions
        assert any(d.action == "decayed" for d in brain.fact_ager.decisions)

    def test_state_route_exposes_fact_aging(self):
        from apps.api.routes.brain import BrainStateResponse

        assert "fact_aging" in BrainStateResponse.model_fields
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
                assert "fact_aging" in resp.json()

    def test_protected_sources_tuple_complete(self):
        assert {"training", "user_input", "curriculum"}.issubset(set(_PROTECTED_SOURCES))
