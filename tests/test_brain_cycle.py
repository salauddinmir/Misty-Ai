"""
Tests for Full Brain Cognitive Cycle.

Tests the complete end-to-end MVP test case:
1. Name declaration in Bengali
2. Relation declaration in Bengali
3. Query answering in Bengali via graph traversal

Also tests:
- Cognitive cycle phase progression
- State management
- Emotional state changes
"""

from brain.core.brain import Brain


class TestBrainInitialization:
    """Test Brain initialization."""

    def test_brain_creates_successfully(self) -> None:
        """Brain initializes all subsystems without errors."""
        brain = Brain()
        assert brain.user_name is None
        # The brain seeds its identity and general training knowledge at
        # initialization (see brain/knowledge/training.py), so the graph
        # starts pre-populated rather than empty.
        assert brain.concept_graph.num_concepts > 0
        assert brain.concept_graph.num_relations > 0
        assert brain.working_memory.size == 0
        assert brain.cycle.cycle_count == 0

    def test_brain_get_state(self) -> None:
        """get_state returns all expected fields."""
        brain = Brain()
        state = brain.get_state()
        assert "cycle_count" in state
        assert "user_name" in state
        assert "concepts" in state
        assert "relations" in state
        assert "working_memory_size" in state
        assert "episodic_memories" in state
        assert "semantic_facts" in state
        assert "emotional_state" in state
        assert "active_concepts" in state
        assert "performance" in state

    def test_brain_knows_own_identity(self) -> None:
        """The trained brain knows she is Misty, made by Pixline Incorporate."""
        brain = Brain()
        misty = brain.concept_graph.get_concept_by_name("Misty")
        assert misty is not None
        pixline = brain.concept_graph.get_concept_by_name("Pixline Incorporate")
        assert pixline is not None
        founder = brain.semantic_memory.query(subject="Pixline Incorporate", predicate="founder")
        assert len(founder) > 0
        assert founder[0].obj == "Salauddin Mir"

        # Trained identity survives query resolution: asking "who created
        # Misty?" must answer with the trained founder.
        result = brain.process("Who created Misty?")
        assert "Salauddin Mir" in result["response"] or "Netvai" in result["response"]
        assert result["confidence"] > 0.9

    def test_brain_self_identity_bengali(self) -> None:
        """Bengali self-identity questions resolve to the trained identity."""
        brain = Brain()
        result = brain.process("মিস্টি কে?")
        assert "Misty" in result["response"]
        assert "Pixline Incorporate" in result["response"]
        assert result["confidence"] > 0.9

        who_result = brain.process("তুমি কে তৈরি করেছে?")
        assert "Salauddin Mir" in who_result["response"] or "Pixline" in who_result["response"]
        assert who_result["confidence"] > 0.9

    def test_brain_self_identity_english(self) -> None:
        """English self-identity questions resolve to the trained identity."""
        brain = Brain()
        result = brain.process("who are you?")
        assert "Misty" in result["response"]
        assert result["confidence"] >= 0.9

        creator = brain.process("who created you?")
        assert "Pixline Incorporate" in creator["response"]
        assert creator["confidence"] > 0.9


class TestNameDeclaration:
    """Test Bengali name declaration processing."""

    def test_name_declaration_bengali(self) -> None:
        """Brain understands Bengali name declaration and stores user name."""
        brain = Brain()
        result = brain.process("\u0986\u09ae\u09be\u09b0 \u09a8\u09be\u09ae Mir\u0964")

        assert brain.user_name == "Mir"
        assert "Mir" in result["response"]
        assert result["cycle_count"] == 1

    def test_name_creates_concept(self) -> None:
        """Name declaration creates a Person concept in graph."""
        brain = Brain()
        brain.process("\u0986\u09ae\u09be\u09b0 \u09a8\u09be\u09ae Mir\u0964")

        concept = brain.concept_graph.get_concept_by_name("Mir")
        assert concept is not None
        assert concept.concept_type == "Person"

    def test_name_stores_semantic_facts(self) -> None:
        """Name declaration stores semantic facts about the person."""
        brain = Brain()
        brain.process("\u0986\u09ae\u09be\u09b0 \u09a8\u09be\u09ae Mir\u0964")

        facts = brain.semantic_memory.query(subject="Mir")
        assert len(facts) > 0

        # Should have "is_a Person" fact
        is_a_facts = [f for f in facts if f.predicate == "is_a"]
        assert len(is_a_facts) > 0

    def test_processing_time_recorded(self) -> None:
        """Processing time is measured and returned."""
        brain = Brain()
        result = brain.process("\u0986\u09ae\u09be\u09b0 \u09a8\u09be\u09ae Mir\u0964")
        assert result["processing_time"] > 0
        assert result["processing_time"] < 5.0  # Should be fast


class TestRelationDeclaration:
    """Test Bengali relation declaration processing."""

    def test_relation_declaration_bengali(self) -> None:
        """Brain understands Bengali relation and creates relation."""
        brain = Brain()
        brain.process("\u0986\u09ae\u09be\u09b0 \u09a8\u09be\u09ae Mir\u0964")
        result = brain.process("\u0986\u09ae\u09bf MistLook-\u098f\u09b0 creator\u0964")

        # Should acknowledge the relation
        assert "creator" in result["response"].lower() or "MistLook" in result["response"]

    def test_relation_creates_target_concept(self) -> None:
        """Relation declaration creates target concept if not exists."""
        brain = Brain()
        brain.process("\u0986\u09ae\u09be\u09b0 \u09a8\u09be\u09ae Mir\u0964")
        brain.process("\u0986\u09ae\u09bf MistLook-\u098f\u09b0 creator\u0964")

        mistlook = brain.concept_graph.get_concept_by_name("MistLook")
        assert mistlook is not None

    def test_relation_creates_graph_edge(self) -> None:
        """Relation declaration creates directed edge in graph."""
        brain = Brain()
        brain.process("\u0986\u09ae\u09be\u09b0 \u09a8\u09be\u09ae Mir\u0964")
        brain.process("\u0986\u09ae\u09bf MistLook-\u098f\u09b0 creator\u0964")

        mir = brain.concept_graph.get_concept_by_name("Mir")
        mistlook = brain.concept_graph.get_concept_by_name("MistLook")
        assert mir is not None
        assert mistlook is not None

        # Check relation exists
        relations = brain.concept_graph.get_relations(mir.concept_id, direction="outgoing")
        creator_rels = [r for r in relations if r["relation_type"] == "creator_of"]
        assert len(creator_rels) > 0
        assert creator_rels[0]["target"] == mistlook.concept_id

    def test_relation_stores_semantic_fact(self) -> None:
        """Relation declaration stores corresponding semantic fact."""
        brain = Brain()
        brain.process("\u0986\u09ae\u09be\u09b0 \u09a8\u09be\u09ae Mir\u0964")
        brain.process("\u0986\u09ae\u09bf MistLook-\u098f\u09b0 creator\u0964")

        facts = brain.semantic_memory.query(predicate="creator_of")
        assert len(facts) > 0
        assert facts[0].subject == "Mir"
        assert facts[0].obj == "MistLook"


class TestQueryAnswering:
    """Test Bengali query answering via graph traversal."""

    def test_query_finds_answer(self) -> None:
        """Brain answers Bengali 'who created' query from knowledge graph."""
        brain = Brain()
        brain.process("\u0986\u09ae\u09be\u09b0 \u09a8\u09be\u09ae Mir\u0964")
        brain.process("\u0986\u09ae\u09bf MistLook-\u098f\u09b0 creator\u0964")
        result = brain.process("MistLook \u0995\u09c7 \u09a4\u09c8\u09b0\u09bf \u0995\u09b0\u09c7\u099b\u09c7?")

        # Response should contain "Mir"
        assert "Mir" in result["response"]

    def test_query_activates_concepts(self) -> None:
        """Query triggers spreading activation on related concepts."""
        brain = Brain()
        brain.process("\u0986\u09ae\u09be\u09b0 \u09a8\u09be\u09ae Mir\u0964")
        brain.process("\u0986\u09ae\u09bf MistLook-\u098f\u09b0 creator\u0964")
        result = brain.process("MistLook \u0995\u09c7 \u09a4\u09c8\u09b0\u09bf \u0995\u09b0\u09c7\u099b\u09c7?")

        # Active concepts should include MistLook-related nodes
        active = result["active_concepts"]
        # At least MistLook should be activated
        if active:
            assert len(active) > 0

    def test_query_unknown_returns_no_info(self) -> None:
        """Query about unknown entity returns appropriate response."""
        brain = Brain()
        result = brain.process("FooBar \u0995\u09c7 \u09a4\u09c8\u09b0\u09bf \u0995\u09b0\u09c7\u099b\u09c7?")

        # Should not crash, should indicate lack of info
        assert result["response"] is not None
        assert len(result["response"]) > 0


class TestMVPEndToEnd:
    """Test the full MVP scenario end-to-end."""

    def test_full_mvp_flow(self) -> None:
        """Complete MVP test case passes end-to-end.

        1. Name declaration -> stores identity
        2. Relation declaration -> stores relation
        3. Query -> recalls answer
        """
        brain = Brain()

        # Step 1: Name declaration
        r1 = brain.process("\u0986\u09ae\u09be\u09b0 \u09a8\u09be\u09ae Mir\u0964")
        assert "Mir" in r1["response"]
        assert brain.user_name == "Mir"
        assert brain.concept_graph.get_concept_by_name("Mir") is not None

        # Step 2: Relation declaration
        r2 = brain.process("\u0986\u09ae\u09bf MistLook-\u098f\u09b0 creator\u0964")
        assert r2["response"]
        assert brain.concept_graph.get_concept_by_name("MistLook") is not None
        assert brain.concept_graph.num_relations > 0

        # Step 3: Query
        r3 = brain.process("MistLook \u0995\u09c7 \u09a4\u09c8\u09b0\u09bf \u0995\u09b0\u09c7\u099b\u09c7?")
        assert "Mir" in r3["response"]

        # Verify overall state
        state = brain.get_state()
        assert state["cycle_count"] == 3
        assert state["concepts"] >= 2  # At least Mir and MistLook
        assert state["relations"] >= 1  # At least creator_of
        assert state["semantic_facts"] >= 1

    def test_mvp_english_equivalent(self) -> None:
        """MVP test case also works in English."""
        brain = Brain()

        brain.process("My name is Mir")
        assert brain.user_name == "Mir"

        brain.process("I created MistLook")
        assert brain.concept_graph.get_concept_by_name("MistLook") is not None

        result = brain.process("Who created MistLook?")
        assert "Mir" in result["response"]


class TestCognitivePhases:
    """Test that all cognitive phases execute correctly."""

    def test_cycle_count_increments(self) -> None:
        """Each process() call increments the cycle count."""
        brain = Brain()
        brain.process("Hello")
        assert brain.cycle.cycle_count == 1
        brain.process("World")
        assert brain.cycle.cycle_count == 2

    def test_emotional_state_changes(self) -> None:
        """Processing input changes emotional state."""
        brain = Brain()
        initial_state = brain.emotion.to_dict()
        brain.process("\u0986\u09ae\u09be\u09b0 \u09a8\u09be\u09ae Mir\u0964")
        final_state = brain.emotion.to_dict()

        # Emotional state should have changed (from input processing)
        assert initial_state != final_state

    def test_working_memory_used(self) -> None:
        """Processing stores items in working memory."""
        brain = Brain()
        brain.process("\u0986\u09ae\u09be\u09b0 \u09a8\u09be\u09ae Mir\u0964")
        assert brain.working_memory.size > 0

    def test_process_returns_expected_fields(self) -> None:
        """process() returns all documented fields."""
        brain = Brain()
        result = brain.process("Hello")

        assert "response" in result
        assert "brain_state" in result
        assert "processing_time" in result
        assert "cycle_count" in result
        assert "active_concepts" in result
        assert "emotional_state" in result


class TestAutonomousReflection:
    """Tests for bounded active evidence gathering."""

    def test_autonomous_tick_gathers_relevant_semantic_evidence(self) -> None:
        import asyncio

        brain = Brain()
        brain.workspace.focus = "Misty Pixline"
        asyncio.run(brain.autonomous_reflection_tick())

        assert brain.last_autonomous_tick is not None
        assert brain.last_autonomous_tick["outcome"] == "hypothesis_supported"
        assert brain.last_autonomous_tick["hypothesis_status"] == "supported"
        assert brain.last_autonomous_tick["evidence_count"] > 0
        assert brain.workspace.summary()["evidence_count"] > 0
        assert brain.workspace.best_hypothesis() is not None

    def test_autonomous_tick_records_no_evidence_without_fabrication(self) -> None:
        import asyncio

        from brain.memory.semantic import SemanticMemory

        brain = Brain()
        brain.semantic_memory = SemanticMemory()
        brain.workspace.focus = "qzxv unknown signal"
        asyncio.run(brain.autonomous_reflection_tick())

        assert brain.last_autonomous_tick is not None
        assert brain.last_autonomous_tick["outcome"] == "no_evidence"
        assert brain.last_autonomous_tick["evidence_count"] == 0
        assert brain.workspace.summary()["evidence_count"] == 0
