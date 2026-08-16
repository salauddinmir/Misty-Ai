"""
Hebbian Associative Learning.

Implements ``fire together, wire together``: whenever two concepts are
co-activated in the same cognitive cycle, the edge between them is
strengthened; edges that are never used slowly weaken.

This is a lightweight, LLM-free rule applied on top of the knowledge
graph. It runs in the ASSOCIATE phase (strengthening) and as part of
memory consolidation (decay of unused edges).
"""

from typing import Any, Dict, Iterable, List


class HebbianLearner:
    """Hebbian weight updater for the concept graph.

    Attributes:
        learning_rate: Maximum per-step weight increase for co-activated edges.
        decay_rate: Multiplicative decay applied to edges that did not fire.
        min_weight: Floor below which an edge weight is never pushed.
        max_weight: Ceiling for edge weights.
        coactivation_window: Number of most recent cycles kept for
            co-activation bookkeeping.
    """

    def __init__(
        self,
        learning_rate: float = 0.1,
        decay_rate: float = 0.995,
        min_weight: float = 0.01,
        max_weight: float = 3.0,
        coactivation_window: int = 10,
    ) -> None:
        self.learning_rate = learning_rate
        self.decay_rate = decay_rate
        self.min_weight = min_weight
        self.max_weight = max_weight
        self.coactivation_window = coactivation_window
        # cycle_id -> list of activated concept ids (bounded ring buffer)
        self._recent_activations: List[List[str]] = []

    # ------------------------------------------------------------------

    def register_activations(self, activated_ids: Iterable[str]) -> None:
        """Record the concepts that fired in the current cycle."""
        self._recent_activations.append(list(dict.fromkeys(activated_ids)))
        if len(self._recent_activations) > self.coactivation_window:
            self._recent_activations.pop(0)

    def coactive_pairs(self) -> Dict[str, float]:
        """Co-activation counts for concept pairs seen in recent cycles.

        Returns a dict keyed by ``"{id_a}|{id_b}"`` (sorted) with the
        number of cycles where both fired.
        """
        counts: Dict[str, float] = {}
        for cycle_ids in self._recent_activations:
            ids = list(dict.fromkeys(cycle_ids))
            for i in range(len(ids)):
                for j in range(i + 1, len(ids)):
                    key = f"{ids[i]}|{ids[j]}"
                    counts[key] = counts.get(key, 0.0) + 1.0
        return counts

    def update(
        self,
        graph: Any,
        activated_ids: Iterable[str],
    ) -> List[Dict[str, Any]]:
        """Strengthen edges between concepts that fired together this cycle.

        For every pair of activated concepts that shares an edge in the
        graph, the edge weight is increased toward ``max_weight``.
        Returns the list of updated edges (id, weight) for logging.

        Args:
            graph: The ConceptGraph instance.
            activated_ids: Concept IDs that fired in this cycle.

        Returns:
            List of updated relations with their new weights.
        """
        ids = list(dict.fromkeys(activated_ids))
        updated: List[Dict[str, Any]] = []
        if len(ids) < 2:
            return updated

        all_relations = graph.get_all_relations()
        edges_by_pair: Dict[str, List[Dict[str, Any]]] = {}
        for rel in all_relations:
            key = f"{rel['source_id']}|{rel['target_id']}"
            edges_by_pair.setdefault(key, []).append(rel)

        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                for key in (f"{ids[i]}|{ids[j]}", f"{ids[j]}|{ids[i]}"):
                    for rel in edges_by_pair.get(key, []):
                        # Edges stored directly in the graph carry their
                        # persistent id in edge metadata (load_relations).
                        if not rel.get("relation_id") and graph.graph.has_edge(rel["source_id"], rel["target_id"]):
                            edge_meta = graph.graph[rel["source_id"]][rel["target_id"]]
                            if "relation_id" in edge_meta:
                                rel = dict(rel)
                                rel["relation_id"] = edge_meta["relation_id"]
                        old = float(rel.get("weight", 1.0))
                        delta = self.learning_rate * (self.max_weight - old)
                        new_weight = max(self.min_weight, min(self.max_weight, old + delta))
                        relation_id = rel.get("relation_id")
                        if relation_id:
                            graph.update_relation_weight(relation_id, new_weight)
                        else:
                            graph.set_edge_weight(rel["source_id"], rel["target_id"], new_weight)
                        updated.append(
                            {
                                "relation_id": relation_id,
                                "source": rel["source_id"],
                                "target": rel["target_id"],
                                "weight_before": round(old, 4),
                                "weight_after": round(new_weight, 4),
                            }
                        )
        return updated

    def decay_unused(
        self,
        graph: Any,
        fired_ids: Iterable[str] | None = None,
    ) -> List[Dict[str, Any]]:
        """Slowly decay every edge weight toward ``min_weight``.

        Edges incident to concepts that fired this cycle decay less
        (``decay_rate``), others decay twice as fast. Edges never drop
        below ``min_weight``. Returns the list of decayed edges.

        Args:
            graph: The ConceptGraph instance.
            fired_ids: Concept IDs that fired this cycle (optional).

        Returns:
            List of decayed relations with their new weights.
        """
        fired = set(fired_ids or [])
        updated: List[Dict[str, Any]] = []
        for rel in graph.get_all_relations():
            old = float(rel.get("weight", 1.0))
            rate = self.decay_rate if (rel["source_id"] in fired or rel["target_id"] in fired) else self.decay_rate**2
            new_weight = max(self.min_weight, old * rate)
            if abs(new_weight - old) > 1e-6:
                relation_id = rel.get("relation_id")
                if relation_id:
                    graph.update_relation_weight(relation_id, new_weight)
                else:
                    # Edge added directly (no persistent id yet): update the
                    # graph edge in place; it will pick up an id on the next
                    # database round-trip.
                    graph.set_edge_weight(rel["source_id"], rel["target_id"], new_weight)
                updated.append(
                    {
                        "relation_id": relation_id,
                        "weight_before": round(old, 4),
                        "weight_after": round(new_weight, 4),
                    }
                )
        return updated

    def reset(self) -> None:
        """Clear the co-activation history (used in tests)."""
        self._recent_activations.clear()
