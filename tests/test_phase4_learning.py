"""
Phase 4 tests: associative learning depth.

Covers Hebbian weight updates on co-activated concepts, decaying unused
edges, recency/frequency/emotional weighted recall, and curiosity-driven
exploration that prompts questions about under-explored neighbor concepts.
"""

import time

import pytest

from brain.graph.concepts import ConceptGraph
from brain.graph.hebbian import HebbianLearner
from brain.learning.curiosity import CuriosityExplorer
from brain.memory.weighted_recall import WeightedRecall

# -----------------------------------------------------------------------
# Hebbian learning
# -----------------------------------------------------------------------


class TestHebbianLearner:
    """Co-activation strengthens edges; inactivity weakens them."""

    def setup_method(self) -> None:
        self.graph = ConceptGraph()
        self.a = self.graph.create_concept("apple")
        self.b = self.graph.create_concept("fruit")
        self.c = self.graph.create_concept("car")
        self.graph.add_relation(self.a.concept_id, self.b.concept_id, "is_a")
        self.graph.add_relation(self.a.concept_id, self.c.concept_id, "related_to")

    def test_coactivation_strengthens_edge(self) -> None:
        learner = HebbianLearner(learning_rate=0.5)
        updates = learner.update(self.graph, [self.a.concept_id, self.b.concept_id])
        assert len(updates) == 1
        assert updates[0]["weight_after"] > updates[0]["weight_before"]
        # The apple-fruit edge grew.
        edge = self.graph.graph[self.a.concept_id][self.b.concept_id]
        assert edge["weight"] == updates[0]["weight_after"]

    def test_uncorrelated_edges_not_updated(self) -> None:
        learner = HebbianLearner(learning_rate=0.5)
        learner.update(self.graph, [self.a.concept_id, self.b.concept_id])
        unrelated = self.graph.graph[self.a.concept_id][self.c.concept_id]["weight"]
        assert unrelated == pytest.approx(1.0)

    def test_decay_weakens_unused_edges(self) -> None:
        learner = HebbianLearner(decay_rate=0.8)
        # Fire only the apple concept: apple-fruit edge is partially used,
        # apple-car edge is unused and decays faster.
        decayed = learner.decay_unused(self.graph, fired_ids=[self.a.concept_id])
        assert len(decayed) == 2
        apple_fruit = self.graph.graph[self.a.concept_id][self.b.concept_id]["weight"]
        apple_car = self.graph.graph[self.a.concept_id][self.c.concept_id]["weight"]
        # Unused edge (apple-car) must end up weaker than the fired neighbor.
        assert apple_car <= apple_fruit

    def test_update_via_persistent_relation_id(self) -> None:
        # After a DB round-trip edges carry a persistent relation_id.
        self.graph.load_relations(
            [
                {
                    "relation_id": "rel-123",
                    "source_id": self.a.concept_id,
                    "target_id": self.b.concept_id,
                    "relation_type": "is_a",
                    "weight": 1.0,
                    "confidence": 1.0,
                }
            ]
        )
        learner = HebbianLearner(learning_rate=0.5)
        updates = learner.update(self.graph, [self.a.concept_id, self.b.concept_id])
        # update() reports each edge's persistent id if present.
        ids = [u.get("relation_id") for u in updates]
        assert "rel-123" in ids
        assert self.graph.graph[self.a.concept_id][self.b.concept_id]["weight"] > 1.0

    def test_register_activations_tracks_bookkeeping(self) -> None:
        learner = HebbianLearner()
        learner.register_activations(["x", "y"])
        pairs = learner.coactive_pairs()
        assert "x|y" in pairs and pairs["x|y"] == 1.0

    def test_reset_clears_state(self) -> None:
        learner = HebbianLearner()
        learner.register_activations(["x"])
        learner.reset()
        assert learner.coactive_pairs() == {}


# -----------------------------------------------------------------------
# Weighted recall
# -----------------------------------------------------------------------


class TestWeightedRecall:
    """Recency, frequency and emotion shape memory retrieval."""

    def test_recall_marks_recent(self) -> None:
        scorer = WeightedRecall()
        scorer.record_recall("c1")
        assert scorer.recency_score("c1") == pytest.approx(1.0, abs=1e-6)
        assert scorer.recency_score("never_recalled") == pytest.approx(0.0)

    def test_recency_decays_over_days(self) -> None:
        scorer = WeightedRecall(recency_halflife_days=7.0)
        now = 1000.0
        scorer.record_recall("c1")
        scorer._last_recall_at["c1"] = now - 7 * 86400  # one halflife ago
        assert scorer.recency_score("c1", now=now) == pytest.approx(0.5, abs=1e-9)

    def test_frequency_is_logarithmic(self) -> None:
        scorer = WeightedRecall(max_frequency_score=0.4)
        for _ in range(8):
            scorer.record_recall("c1")
        freq = scorer.frequency_score("c1")
        assert freq > 0.0
        assert freq <= 0.4
        # Zero count returns zero.
        assert scorer.frequency_score("c2") == pytest.approx(0.0)

    def test_emotion_boosts_memorable_events(self) -> None:
        scorer = WeightedRecall(emotion_boost=0.3)
        assert scorer.emotion_score(0.9) == pytest.approx(0.27, abs=1e-9)
        assert scorer.emotion_score(-0.9) == pytest.approx(0.27, abs=1e-9)
        assert scorer.emotion_score(None) == pytest.approx(0.0)

    def test_total_clamped_to_one(self) -> None:
        scorer = WeightedRecall(emotion_boost=1.0, max_frequency_score=1.0)
        scorer.record_recall("c1")
        scores = scorer.score("c1", emotional_valence=1.0)
        assert scores["total"] <= 1.0

    def test_rank_orders_recent_more_frequent(self) -> None:
        scorer = WeightedRecall(recency_halflife_days=7.0)
        scorer.record_recall("c1")
        scorer.record_recall("c2")
        now = time.time()
        scorer._last_recall_at["c2"] = now - 30 * 86400  # old
        ranked = scorer.rank(
            [{"concept_id": "c2"}, {"concept_id": "c1"}],
            now=now,
        )
        assert ranked[0]["concept_id"] == "c1"

    def test_forget_removes_tracking(self) -> None:
        scorer = WeightedRecall()
        scorer.record_recall("c1")
        scorer.forget("c1")
        assert scorer.frequency_score("c1") == pytest.approx(0.0)


# -----------------------------------------------------------------------
# Curiosity-driven exploration
# -----------------------------------------------------------------------


class TestCuriosityExplorer:
    """The agent asks about what it does not yet know."""

    def setup_method(self) -> None:
        self.graph = ConceptGraph()
        self.misty = self.graph.create_concept("misty")
        self.owner = self.graph.create_concept("owner")
        self.unknown_neighbor = self.graph.create_concept("unknown_project")
        self.graph.add_relation(self.misty.concept_id, self.owner.concept_id, "created_by")
        self.graph.add_relation(self.misty.concept_id, self.unknown_neighbor.concept_id, "related_to")

    def test_asks_about_under_explored_neighbor(self) -> None:
        explorer = CuriosityExplorer()
        suggestion = explorer.evaluate(
            self.graph,
            {self.misty.concept_id: 0.8, self.owner.concept_id: 0.9},
        )
        assert suggestion["target"] == self.unknown_neighbor.concept_id
        assert "unknown_project" in suggestion["question"]
        assert suggestion["bonus"] >= explorer.ask_threshold

    def test_ignores_well_known_concepts(self) -> None:
        explorer = CuriosityExplorer()
        # Everything active and above the floor: nothing to explore.
        suggestion = explorer.evaluate(
            self.graph,
            {
                self.misty.concept_id: 0.8,
                self.owner.concept_id: 0.9,
                self.unknown_neighbor.concept_id: 0.6,
            },
        )
        assert suggestion["target"] is None
        assert suggestion["question"] is None

    def test_urgency_suppresses_curiosity(self) -> None:
        explorer = CuriosityExplorer()
        suggestion = explorer.evaluate(
            self.graph,
            {self.misty.concept_id: 0.8, self.owner.concept_id: 0.9},
            urgency=0.8,
        )
        assert suggestion["target"] is None

    def test_asked_concept_is_cooldown(self) -> None:
        explorer = CuriosityExplorer(cooldown_cycles=4)
        explorer.evaluate(
            self.graph,
            {self.misty.concept_id: 0.8, self.owner.concept_id: 0.9},
        )
        # Immediately re-evaluating returns nothing for the same concept.
        suggestion = explorer.evaluate(
            self.graph,
            {self.misty.concept_id: 0.8, self.owner.concept_id: 0.9},
        )
        assert suggestion["target"] is None

    def test_step_cooldowns_reopens_concept(self) -> None:
        explorer = CuriosityExplorer(cooldown_cycles=2)
        explorer.evaluate(
            self.graph,
            {self.misty.concept_id: 0.8, self.owner.concept_id: 0.9},
        )
        explorer.step_cooldowns()
        explorer.step_cooldowns()
        explorer.reset_asked()  # after cooldown, asking again is allowed
        suggestion = explorer.evaluate(
            self.graph,
            {self.misty.concept_id: 0.8, self.owner.concept_id: 0.9},
        )
        assert suggestion["target"] == self.unknown_neighbor.concept_id

    def test_empty_graph_no_op(self) -> None:
        explorer = CuriosityExplorer()
        suggestion = explorer.evaluate(ConceptGraph(), {})
        assert suggestion["target"] is None
