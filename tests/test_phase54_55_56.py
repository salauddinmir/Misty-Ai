"""
Phase 54 (Explainable Reasoning), Phase 55 (Contextual Boosting), and Phase 56 (Conflict Resolution) Tests.
"""

from brain.core.brain import Brain
from brain.learning.reasoning import ReasoningEngine
from brain.nlu.parser import IntentType, ParseResult


def test_explainable_reasoning_trace_in_evidence():
    brain = Brain()
    # 1. Store a fact with a trace
    brain.semantic_memory.store_fact(
        "A",
        "is_a",
        "B",
        1.0,
        source="inferred",
        metadata={"reasoning_trace": ["A is a child of B"]},
    )

    # 2. Run recall phase
    parse_result = ParseResult(intent=IntentType.QUERY_WHAT, query={"target": "A"}, raw_text="A is a B")
    brain._phase_recall(parse_result)

    # 3. Check evidence in workspace
    evidences = [e for e in brain.workspace.evidence if e.content.get("subject") == "A"]
    assert len(evidences) > 0
    assert evidences[0].metadata["reasoning_trace"] == ["A is a child of B"]


def test_contextual_fact_boosting():
    brain = Brain()
    sm = brain.semantic_memory

    # 1. Store two facts with same subject to trigger boosting in recall
    sm.store_fact("fruit", "includes", "Apple", 0.8)
    sm.store_fact("fruit", "includes", "Banana", 0.8)

    # 2. Add "Apple" to dialogue context
    brain.dialogue_context.add_turn("I like Apple", role="user")

    # 3. Run recall with "fruit" query
    # "Apple" fact should be boosted and appear first
    parse_result = ParseResult(intent=IntentType.QUERY_WHAT, query={"target": "fruit"}, raw_text="Tell me about fruit")
    brain._phase_recall(parse_result)

    evidences = [e for e in brain.workspace.evidence if e.content.get("kind") == "semantic_fact"]
    # The first evidence should be about Apple due to boosting
    assert evidences[0].content["obj"] == "Apple"


def test_conflict_resolution_backtracking():
    brain = Brain()
    engine = ReasoningEngine(brain)
    sm = brain.semantic_memory

    # 1. Store conflicting inferred facts
    sm.store_fact("Sky", "is_color", "Blue", 0.9, source="inferred")
    sm.store_fact("Sky", "is_color", "Green", 0.7, source="inferred")

    # 2. Run derivation (which triggers conflict resolution)
    summary = engine.derive()

    # 3. Verify Green is removed, Blue remains
    assert summary["conflicts_resolved"] == 1
    assert "Sky:is_color:Blue" in sm.facts
    assert "Sky:is_color:Green" not in sm.facts
