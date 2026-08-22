"""
Phase 52 (Recursive Inference) and Phase 53 (Reasoning Trace) Tests.
"""

import pytest

from brain.core.brain import Brain
from brain.learning.reasoning import ReasoningEngine


def test_recursive_inference_chains():
    brain = Brain()
    engine = ReasoningEngine(brain)

    # 1. Setup a chain: A is_a B, B is_a C, C is_a D
    brain.semantic_memory.store_fact("A", "is_a", "B", 1.0)
    brain.semantic_memory.store_fact("B", "is_a", "C", 1.0)
    brain.semantic_memory.store_fact("C", "is_a", "D", 1.0)

    # 2. Run derivation
    summary = engine.derive()

    # 3. Verify recursion depth and derived facts
    # Pass 1: A is_a C, B is_a D
    # Pass 2: A is_a D
    assert summary["recursion_depth"] >= 2
    assert "A:is_a:C" in brain.semantic_memory.facts
    assert "B:is_a:D" in brain.semantic_memory.facts
    assert "A:is_a:D" in brain.semantic_memory.facts

    # Verify confidence decay (1.0 * 0.9 * 0.9 = 0.81 for A:is_a:C)
    assert brain.semantic_memory.facts["A:is_a:C"].confidence == pytest.approx(0.9)
    assert brain.semantic_memory.facts["A:is_a:D"].confidence == pytest.approx(0.81)


def test_reasoning_trace_metadata():
    brain = Brain()
    engine = ReasoningEngine(brain)

    # 1. Setup facts for symmetric rule
    brain.semantic_memory.store_fact("Delhi", "is_adjacent_to", "Gurgaon", 1.0)

    # 2. Run derivation
    engine.derive()

    # 3. Verify trace exists in metadata
    derived = brain.semantic_memory.facts["Gurgaon:is_adjacent_to:Delhi"]
    assert "reasoning_trace" in derived.metadata
    assert derived.metadata["reasoning_trace"] == ["Delhi is_adjacent_to Gurgaon"]


def test_inheritance_trace():
    brain = Brain()
    engine = ReasoningEngine(brain)

    # 1. Setup inheritance: Mango is_a Fruit, Fruit tastes_like sweet
    fruit = brain.concept_graph.create_concept("Fruit")
    mango = brain.concept_graph.create_concept("Mango")
    brain.concept_graph.add_relation(mango.concept_id, fruit.concept_id, "is_a", confidence=1.0)

    brain.semantic_memory.store_fact("Fruit", "tastes_like", "sweet", 0.9)

    # 2. Run derivation
    engine.derive()

    # 3. Verify inheritance trace
    derived = brain.semantic_memory.facts["Mango:tastes_like:sweet"]
    assert "reasoning_trace" in derived.metadata
    assert "Mango is a Fruit" in derived.metadata["reasoning_trace"]
    assert "Fruit tastes_like sweet" in derived.metadata["reasoning_trace"]
