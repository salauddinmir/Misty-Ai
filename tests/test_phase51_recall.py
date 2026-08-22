"""
Phase 51 Tests: Inference-Supported Recall.
"""

from brain.core.brain import Brain
from brain.memory.semantic import SemanticFact
from brain.nlu.parser import IntentType, ParseResult


def test_inference_recall_broadcasting():
    brain = Brain()
    # 1. Inject an inferred fact
    brain.semantic_memory.store_fact(subject="Mango", predicate="is_a", obj="Plant", confidence=0.81, source="inferred")

    # 2. Mock a query for Mango
    parse_result = ParseResult(
        intent=IntentType.QUERY_WHAT, query={"target": "Mango"}, confidence=1.0, raw_text="Mango কি?"
    )

    # 3. Run recall phase
    result = brain._phase_recall(parse_result)

    # 4. Verify evidence was broadcast
    assert result.success is True
    assert "inferred_facts" in result.data
    assert len(result.data["inferred_facts"]) == 1
    assert result.data["inferred_facts"][0]["obj"] == "Plant"

    # 5. Check workspace evidence
    evidence_id = result.data["evidence_ids"][0]
    evidence = next(e for e in brain.workspace.evidence if e.evidence_id == evidence_id)
    assert evidence.source == "reasoning_engine"
    assert evidence.content["kind"] == "inferred_fact"
    assert evidence.content["obj"] == "Plant"


def test_inference_recall_skips_if_no_target():
    brain = Brain()
    parse_result = ParseResult(intent=IntentType.GREETING, query={}, confidence=1.0, raw_text="Hello")
    result = brain._phase_recall(parse_result)
    assert "inferred_facts" not in result.data
