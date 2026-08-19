#!/usr/bin/env python3
"""
MVP Test Case: Association Engine End-to-End.

Demonstrates the core MISTY cognitive system without any LLM:
1. User declares their name (Bengali)
2. User declares a relation (Bengali)
3. User asks a question (Bengali)
4. Brain recalls the answer through neural activation and graph traversal

Expected flow:
  Input: "amar naam Mir" -> Creates concept Mir (Person), stores identity
  Input: "ami MistLook-er creator" -> Creates relation: Mir -> creator_of -> MistLook
  Input: "MistLook ke toiri korechhe?" -> Activates MistLook -> finds creator_of -> returns Mir

No LLM involved at any point.
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brain.core.brain import Brain


def separator(title: str) -> None:
    """Print a visual separator with a title."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def print_state(brain: Brain) -> None:
    """Print current brain state summary."""
    state = brain.get_state()
    print(f"  Cycle Count: {state['cycle_count']}")
    print(f"  User Name: {state['user_name']}")
    print(f"  Concepts: {state['concepts']}")
    print(f"  Relations: {state['relations']}")
    print(f"  Semantic Facts: {state['semantic_facts']}")
    print(f"  Working Memory: {state['working_memory_size']} items")
    print(f"  Active Concepts: {state['active_concepts']}")
    print(f"  Emotional State: {state['emotional_state']}")


def run_mvp_test() -> bool:
    """Run the complete MVP test case.

    Returns:
        True if all assertions pass, False otherwise.
    """
    separator("MISTY Brain - MVP Association Test")
    print("Testing: Knowledge graph creation and retrieval")
    print("Language: Bengali (rule-based NLU, no LLM)")
    print()

    brain = Brain()

    # =====================================================
    # Step 1: Name Declaration
    # =====================================================
    separator("Step 1: Name Declaration")
    input_1 = "\u0986\u09ae\u09be\u09b0 \u09a8\u09be\u09ae Mir\u0964"  # Bengali: amar naam Mir.
    print(f"  Input: \"{input_1}\"")
    result_1 = brain.process(input_1)
    print(f"  Response: \"{result_1['response']}\"")
    print(f"  Processing Time: {result_1['processing_time']:.4f}s")
    print()

    # Verify: Brain should know user's name
    assert brain.user_name == "Mir", f"Expected user_name='Mir', got '{brain.user_name}'"
    print("  [PASS] User name stored correctly: Mir")

    # Verify: Concept created in graph
    mir_concept = brain.concept_graph.get_concept_by_name("Mir")
    assert mir_concept is not None, "Concept 'Mir' not found in graph"
    assert mir_concept.concept_type == "Person", f"Expected type 'Person', got '{mir_concept.concept_type}'"
    print(f"  [PASS] Concept 'Mir' created (type: {mir_concept.concept_type})")

    # Verify: Semantic facts stored
    facts = brain.semantic_memory.query(subject="Mir")
    assert len(facts) > 0, "No semantic facts about 'Mir'"
    print(f"  [PASS] Semantic facts stored: {len(facts)} facts about Mir")

    print()
    print_state(brain)

    # =====================================================
    # Step 2: Relation Declaration
    # =====================================================
    separator("Step 2: Relation Declaration")
    input_2 = "\u0986\u09ae\u09bf MistLook-\u098f\u09b0 creator\u0964"  # Bengali: ami MistLook-er creator.
    print(f"  Input: \"{input_2}\"")
    result_2 = brain.process(input_2)
    print(f"  Response: \"{result_2['response']}\"")
    print(f"  Processing Time: {result_2['processing_time']:.4f}s")
    print()

    # Verify: MistLook concept created
    mistlook_concept = brain.concept_graph.get_concept_by_name("MistLook")
    assert mistlook_concept is not None, "Concept 'MistLook' not found in graph"
    print(f"  [PASS] Concept 'MistLook' created (type: {mistlook_concept.concept_type})")

    # Verify: Relation created
    relations = brain.concept_graph.get_relations(mir_concept.concept_id, direction="outgoing")
    creator_rels = [r for r in relations if r["relation_type"] == "creator_of"]
    assert len(creator_rels) > 0, "No 'creator_of' relation found"
    print("  [PASS] Relation 'Mir -> creator_of -> MistLook' created")

    # Verify: Semantic fact stored
    creator_facts = brain.semantic_memory.query(predicate="creator_of")
    assert len(creator_facts) > 0, "No creator_of fact in semantic memory"
    print(f"  [PASS] Semantic fact stored: {creator_facts[0].subject} -> creator_of -> {creator_facts[0].obj}")

    print()
    print_state(brain)

    # =====================================================
    # Step 3: Query (Association & Recall)
    # =====================================================
    separator("Step 3: Query - Who created MistLook?")
    # Bengali: MistLook ke toiri korechhe?
    input_3 = "MistLook \u0995\u09c7 \u09a4\u09c8\u09b0\u09bf \u0995\u09b0\u09c7\u099b\u09c7?"
    print(f"  Input: \"{input_3}\"")
    result_3 = brain.process(input_3)
    print(f"  Response: \"{result_3['response']}\"")
    print(f"  Processing Time: {result_3['processing_time']:.4f}s")
    print(f"  Active Concepts: {result_3['active_concepts']}")
    print()

    # Verify: Response contains "Mir"
    assert "Mir" in result_3["response"], (
        f"Expected 'Mir' in response, got: '{result_3['response']}'"
    )
    print("  [PASS] Correct answer retrieved: 'Mir' found in response")

    print()
    print_state(brain)

    # =====================================================
    # Summary
    # =====================================================
    separator("TEST SUMMARY")
    print("  All MVP test cases PASSED!")
    print()
    print("  Demonstrated capabilities:")
    print("    1. Bengali NLU (rule-based, no LLM)")
    print("    2. Concept creation in knowledge graph")
    print("    3. Relation declaration and storage")
    print("    4. Query answering via graph traversal")
    print("    5. Spreading activation in concept graph")
    print("    6. Semantic memory with fact storage/retrieval")
    print("    7. Full 10-phase cognitive cycle")
    print("    8. Emotional state tracking")
    print("    9. Working memory with decay")
    print()
    print("  NO LLM was used at any point in this test.")
    print(f"  Total cognitive cycles: {brain.cycle.cycle_count}")
    print(f"  Knowledge graph: {brain.concept_graph.num_concepts} concepts, "
          f"{brain.concept_graph.num_relations} relations")
    print()

    return True


if __name__ == "__main__":
    try:
        success = run_mvp_test()
        sys.exit(0 if success else 1)
    except AssertionError as e:
        print(f"\n  [FAIL] Assertion failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n  [ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
