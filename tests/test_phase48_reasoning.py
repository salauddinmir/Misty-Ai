"""
Phase 48 tests — connection-based reasoning layer.

Covers the three inference rules (transitivity, category inheritance,
symmetric predicates), confidence composition with hop decay, the derived
confidence floor, deduplication, the per-turn derivation budget, and the
Brain/API wiring.
"""

from brain.core.brain import Brain
from brain.learning.reasoning import (
    _HOP_DECAY,
    _MAX_DERIVED_PER_TURN,
    _MIN_DERIVED_CONFIDENCE,
    ReasoningEngine,
)


def _fresh_brain() -> Brain:
    brain = Brain()
    brain.semantic_memory.facts.clear()
    for key in list(brain.concept_graph._concepts):
        brain.concept_graph._graph.remove_node(key)
    brain.concept_graph._concepts.clear()
    brain.concept_graph._name_index.clear()
    return brain


def test_engine_instantiates():
    engine = ReasoningEngine(_fresh_brain())
    summary = engine.summary()
    assert summary["enabled"] is True
    assert summary["total_derived"] == 0


def test_transitive_derivation_composes_confidence():
    brain = _fresh_brain()
    sm = brain.semantic_memory
    sm.store_fact("mango", "is_a", "fruit", 0.9)
    sm.store_fact("fruit", "is_a", "plant", 0.9)
    derived = ReasoningEngine(brain).derive()
    assert derived["derived_this_pass"] == 1
    assert "mango:is_a:plant" in sm.facts
    fact = sm.facts["mango:is_a:plant"]
    assert fact.source == "inferred"
    expected = min(0.9, 0.9) * _HOP_DECAY
    assert abs(fact.confidence - expected) < 1e-9


def test_transitivity_skips_existing_facts():
    brain = _fresh_brain()
    sm = brain.semantic_memory
    sm.store_fact("mango", "is_a", "fruit", 0.9)
    sm.store_fact("fruit", "is_a", "plant", 0.9)
    sm.store_fact("mango", "is_a", "plant", 0.95, source="training")
    derived = ReasoningEngine(brain).derive()
    assert derived["derived_this_pass"] == 0
    assert sm.facts["mango:is_a:plant"].source == "training"


def test_inheritance_via_graph_edge():
    brain = _fresh_brain()
    sm = brain.semantic_memory
    graph = brain.concept_graph
    mango = graph.create_concept("mango")
    fruit = graph.create_concept("fruit")
    graph.add_relation(mango.concept_id, fruit.concept_id, "is_a", confidence=1.0)
    sm.store_fact("fruit", "tastes_like", "sweet", 0.9)
    derived = ReasoningEngine(brain).derive()
    assert derived["derived_this_pass"] == 1
    fact = sm.facts["mango:tastes_like:sweet"]
    assert fact.source == "inferred"
    assert fact.confidence == min(0.9, 1.0) * _HOP_DECAY


def test_symmetric_derivation():
    brain = _fresh_brain()
    sm = brain.semantic_memory
    sm.store_fact("delhi", "is_adjacent_to", "gurgaon", 0.85)
    derived = ReasoningEngine(brain).derive()
    assert derived["derived_this_pass"] == 1
    fact = sm.facts["gurgaon:is_adjacent_to:delhi"]
    assert fact.source == "inferred"
    assert abs(fact.confidence - 0.85) < 1e-9


def test_symmetric_skip_when_reverse_exists():
    brain = _fresh_brain()
    sm = brain.semantic_memory
    sm.store_fact("delhi", "is_adjacent_to", "gurgaon", 0.85)
    sm.store_fact("gurgaon", "is_adjacent_to", "delhi", 0.9, source="user_input")
    derived = ReasoningEngine(brain).derive()
    assert derived["derived_this_pass"] == 0


def test_low_confidence_chain_not_stored():
    brain = _fresh_brain()
    sm = brain.semantic_memory
    sm.store_fact("a", "is_a", "b", _MIN_DERIVED_CONFIDENCE - 0.02)
    sm.store_fact("b", "is_a", "c", _MIN_DERIVED_CONFIDENCE - 0.02)
    engine = ReasoningEngine(brain)
    derived = engine.derive()
    assert derived["derived_this_pass"] == 0
    assert "a:is_a:c" not in sm.facts
    # The attempt is still logged (not stored).
    summary = engine.summary()
    assert any(not d["stored"] for d in summary["recent"]) or summary["total_derived"] >= 1


def test_per_turn_derivation_budget():
    brain = _fresh_brain()
    sm = brain.semantic_memory
    for i in range(30):
        sm.store_fact(f"cat{i}", "is_a", "animal", 0.9)
    # chain: animal -> organism (one extra hop so transitivity fires per cat)
    sm.store_fact("animal", "is_a", "organism", 0.9)
    # symmetric: each cat0..cat29 yields one symmetric derivation too.
    for i in range(30):
        sm.store_fact(f"cat{i}", "is_connected_to", f"region{i}", 0.9)
    derived = ReasoningEngine(brain).derive()
    assert derived["derived_this_pass"] == _MAX_DERIVED_PER_TURN


def test_derived_facts_recorded_in_summary():
    brain = _fresh_brain()
    brain.semantic_memory.store_fact("x", "is_adjacent_to", "y", 0.8)
    engine = ReasoningEngine(brain)
    engine.derive()
    summary = engine.summary()
    assert summary["total_derived"] == 1
    assert summary["rules_fired"].get("symmetric", 0) == 1
    assert summary["recent"][0]["key"] == "y:is_adjacent_to:x"
    assert summary["recent"][0]["stored"] is True


def test_brain_has_reasoning_engine():
    brain = Brain()
    assert isinstance(brain.reasoning_engine, ReasoningEngine)


def test_brain_state_includes_reasoning():
    brain = Brain()
    brain.semantic_memory.store_fact("a", "is_adjacent_to", "b", 0.8)
    brain.process("a এর পাশে কী কী আছে?")
    state = brain.get_state()
    assert "reasoning" in state
    assert state["reasoning"]["enabled"] is True


def test_brain_state_response_includes_reasoning():
    from apps.api.routes.brain import BrainStateResponse

    state = BrainStateResponse(
        cycle_count=1,
        user_name=None,
        concepts=0,
        relations=0,
        working_memory_size=0,
        episodic_memories=0,
        semantic_facts=0,
        emotional_state={},
        active_concepts={},
        performance={},
        last_autonomous_tick={},
        reasoning=None,
    )
    assert state.reasoning is None
