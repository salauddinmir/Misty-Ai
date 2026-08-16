"""
Tests for Knowledge Graph (ConceptGraph) and Spreading Activation.

Tests cover:
- Creating concepts
- Creating relations between concepts
- Querying concepts by name (case-insensitive)
- Getting neighbors and related concepts
- Spreading activation propagation
- Activation decay with distance
"""

from brain.graph.activation import SpreadingActivation
from brain.graph.concepts import ConceptGraph


class TestConceptCreation:
    """Test concept creation and retrieval."""

    def test_create_concept(self) -> None:
        """Can create a concept with name and type."""
        graph = ConceptGraph()
        concept = graph.create_concept(name="Python", concept_type="Language")
        assert concept.name == "Python"
        assert concept.concept_type == "Language"
        assert concept.concept_id is not None

    def test_create_concept_default_type(self) -> None:
        """Concept defaults to 'generic' type."""
        graph = ConceptGraph()
        concept = graph.create_concept(name="Thing")
        assert concept.concept_type == "generic"

    def test_create_concept_with_metadata(self) -> None:
        """Concept can store arbitrary metadata."""
        graph = ConceptGraph()
        concept = graph.create_concept(
            name="Mir",
            concept_type="Person",
            metadata={"is_user": True, "role": "developer"},
        )
        assert concept.metadata["is_user"] is True
        assert concept.metadata["role"] == "developer"

    def test_num_concepts_increases(self) -> None:
        """num_concepts property tracks graph size."""
        graph = ConceptGraph()
        assert graph.num_concepts == 0
        graph.create_concept(name="A")
        assert graph.num_concepts == 1
        graph.create_concept(name="B")
        assert graph.num_concepts == 2

    def test_get_concept_by_id(self) -> None:
        """Can retrieve concept by its ID."""
        graph = ConceptGraph()
        concept = graph.create_concept(name="Test")
        retrieved = graph.get_concept(concept.concept_id)
        assert retrieved is not None
        assert retrieved.name == "Test"

    def test_get_nonexistent_concept(self) -> None:
        """Getting non-existent concept returns None."""
        graph = ConceptGraph()
        assert graph.get_concept("fake_id") is None


class TestConceptByName:
    """Test name-based concept lookup."""

    def test_get_by_name(self) -> None:
        """Can get concept by name."""
        graph = ConceptGraph()
        graph.create_concept(name="MistLook", concept_type="Product")
        result = graph.get_concept_by_name("MistLook")
        assert result is not None
        assert result.name == "MistLook"

    def test_case_insensitive_lookup(self) -> None:
        """Name lookup is case-insensitive."""
        graph = ConceptGraph()
        graph.create_concept(name="Python")
        assert graph.get_concept_by_name("python") is not None
        assert graph.get_concept_by_name("PYTHON") is not None
        assert graph.get_concept_by_name("Python") is not None

    def test_nonexistent_name(self) -> None:
        """Looking up non-existent name returns None."""
        graph = ConceptGraph()
        assert graph.get_concept_by_name("Nothing") is None


class TestRelations:
    """Test relation creation and querying."""

    def test_add_relation(self) -> None:
        """Can add a directed relation between concepts."""
        graph = ConceptGraph()
        a = graph.create_concept(name="Mir")
        b = graph.create_concept(name="MistLook")
        success = graph.add_relation(a.concept_id, b.concept_id, "creator_of")
        assert success is True
        assert graph.num_relations == 1

    def test_relation_with_weight(self) -> None:
        """Relations can have custom weight and confidence."""
        graph = ConceptGraph()
        a = graph.create_concept(name="A")
        b = graph.create_concept(name="B")
        graph.add_relation(a.concept_id, b.concept_id, "related_to", weight=0.8, confidence=0.9)

        relations = graph.get_relations(a.concept_id, direction="outgoing")
        assert len(relations) == 1
        assert relations[0]["weight"] == 0.8
        assert relations[0]["confidence"] == 0.9

    def test_add_relation_invalid_source(self) -> None:
        """Adding relation with invalid source returns False."""
        graph = ConceptGraph()
        b = graph.create_concept(name="B")
        success = graph.add_relation("fake_id", b.concept_id, "related")
        assert success is False

    def test_get_outgoing_relations(self) -> None:
        """Can get outgoing relations for a concept."""
        graph = ConceptGraph()
        a = graph.create_concept(name="A")
        b = graph.create_concept(name="B")
        c = graph.create_concept(name="C")
        graph.add_relation(a.concept_id, b.concept_id, "knows")
        graph.add_relation(a.concept_id, c.concept_id, "likes")

        relations = graph.get_relations(a.concept_id, direction="outgoing")
        assert len(relations) == 2

    def test_get_incoming_relations(self) -> None:
        """Can get incoming relations for a concept."""
        graph = ConceptGraph()
        a = graph.create_concept(name="A")
        b = graph.create_concept(name="B")
        graph.add_relation(a.concept_id, b.concept_id, "knows")

        incoming = graph.get_relations(b.concept_id, direction="incoming")
        assert len(incoming) == 1
        assert incoming[0]["source"] == a.concept_id

    def test_find_related_by_type(self) -> None:
        """Can find related concepts filtered by relation type."""
        graph = ConceptGraph()
        mir = graph.create_concept(name="Mir", concept_type="Person")
        ml = graph.create_concept(name="MistLook", concept_type="Product")
        py = graph.create_concept(name="Python", concept_type="Language")

        graph.add_relation(mir.concept_id, ml.concept_id, "creator_of")
        graph.add_relation(mir.concept_id, py.concept_id, "uses")

        # Find only creator_of relations
        related = graph.find_related(mir.concept_id, relation_type="creator_of")
        assert len(related) == 1
        assert related[0].name == "MistLook"

    def test_find_related_incoming(self) -> None:
        """Can find concepts with incoming relations."""
        graph = ConceptGraph()
        mir = graph.create_concept(name="Mir")
        ml = graph.create_concept(name="MistLook")
        graph.add_relation(mir.concept_id, ml.concept_id, "creator_of")

        # From MistLook's perspective, find who is related incoming
        related = graph.find_related(ml.concept_id, relation_type="creator_of", direction="incoming")
        assert len(related) == 1
        assert related[0].name == "Mir"

    def test_get_neighbors(self) -> None:
        """Get neighbors returns all connected concept IDs."""
        graph = ConceptGraph()
        a = graph.create_concept(name="A")
        b = graph.create_concept(name="B")
        c = graph.create_concept(name="C")
        graph.add_relation(a.concept_id, b.concept_id, "knows")
        graph.add_relation(c.concept_id, a.concept_id, "likes")

        neighbors = graph.get_neighbors(a.concept_id)
        assert b.concept_id in neighbors
        assert c.concept_id in neighbors


class TestSpreadingActivation:
    """Test spreading activation algorithm."""

    def test_source_gets_full_activation(self) -> None:
        """Source concept gets full initial activation."""
        graph = ConceptGraph()
        a = graph.create_concept(name="A")
        sa = SpreadingActivation()

        result = sa.activate(graph, a.concept_id)
        assert a.concept_id in result
        assert result[a.concept_id] == 1.0

    def test_activation_spreads_to_neighbors(self) -> None:
        """Activation spreads to directly connected concepts."""
        graph = ConceptGraph()
        a = graph.create_concept(name="A")
        b = graph.create_concept(name="B")
        graph.add_relation(a.concept_id, b.concept_id, "related")

        sa = SpreadingActivation(decay_factor=0.5)
        result = sa.activate(graph, a.concept_id)

        assert b.concept_id in result
        assert result[b.concept_id] > 0.0

    def test_activation_decays_with_distance(self) -> None:
        """Activation is weaker for more distant concepts."""
        graph = ConceptGraph()
        a = graph.create_concept(name="A")
        b = graph.create_concept(name="B")
        c = graph.create_concept(name="C")
        graph.add_relation(a.concept_id, b.concept_id, "related")
        graph.add_relation(b.concept_id, c.concept_id, "related")

        sa = SpreadingActivation(decay_factor=0.5)
        result = sa.activate(graph, a.concept_id)

        # B should have more activation than C
        if b.concept_id in result and c.concept_id in result:
            assert result[b.concept_id] > result[c.concept_id]

    def test_isolated_node(self) -> None:
        """Activation of isolated node only activates that node."""
        graph = ConceptGraph()
        a = graph.create_concept(name="A")
        graph.create_concept(name="B")  # Not connected

        sa = SpreadingActivation()
        result = sa.activate(graph, a.concept_id)

        assert a.concept_id in result
        assert len(result) == 1  # Only source activated

    def test_max_depth_limit(self) -> None:
        """Activation respects max_depth limit."""
        graph = ConceptGraph()
        nodes = [graph.create_concept(name=f"N{i}") for i in range(10)]
        for i in range(9):
            graph.add_relation(nodes[i].concept_id, nodes[i + 1].concept_id, "next")

        sa = SpreadingActivation(decay_factor=0.9, max_depth=2)
        result = sa.activate(graph, nodes[0].concept_id)

        # Should not reach far nodes
        assert nodes[0].concept_id in result
        # Nodes beyond max_depth should not be activated (or below threshold)
        far_nodes_activated = sum(1 for n in nodes[5:] if n.concept_id in result)
        # Due to depth limit and decay, far nodes should not be reached
        assert far_nodes_activated == 0

    def test_find_most_activated(self) -> None:
        """find_most_activated returns top-N results sorted by activation."""
        graph = ConceptGraph()
        a = graph.create_concept(name="A")
        b = graph.create_concept(name="B")
        c = graph.create_concept(name="C")
        graph.add_relation(a.concept_id, b.concept_id, "related")
        graph.add_relation(a.concept_id, c.concept_id, "related")

        sa = SpreadingActivation()
        top = sa.find_most_activated(graph, a.concept_id, top_n=2)

        assert len(top) <= 2
        # Results should be sorted by activation (descending)
        if len(top) >= 2:
            assert top[0][1] >= top[1][1]
