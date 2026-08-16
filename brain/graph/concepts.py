"""
Concept Graph.

Represents concepts as nodes in a NetworkX graph with
activation levels, types, and metadata.
"""

import time as time_module
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List

import networkx as nx


@dataclass
class Concept:
    """A concept node in the knowledge graph."""

    name: str
    concept_type: str = "generic"
    concept_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    activation_level: float = 0.0
    created_at: float = field(default_factory=time_module.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def activate(self, amount: float = 1.0) -> None:
        """Increase activation level."""
        self.activation_level = min(1.0, self.activation_level + amount)

    def decay(self, rate: float = 0.9) -> None:
        """Apply decay to activation level."""
        self.activation_level *= rate

    def to_dict(self) -> Dict[str, Any]:
        """Convert concept to a dictionary representation."""
        return {
            "concept_id": self.concept_id,
            "name": self.name,
            "concept_type": self.concept_type,
            "activation_level": self.activation_level,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }

    def __repr__(self) -> str:
        return f"Concept(name={self.name}, type={self.concept_type}, activation={self.activation_level:.3f})"


class ConceptGraph:
    """Knowledge graph managing concepts and their relationships.

    Uses NetworkX internally for graph operations.
    """

    def __init__(self) -> None:
        """Initialize an empty concept graph."""
        self._graph: nx.DiGraph = nx.DiGraph()
        self._concepts: Dict[str, Concept] = {}
        self._name_index: Dict[str, str] = {}  # name -> concept_id
        self._relation_ids: Dict[str, str] = {}  # "source_id|target_id" -> relation_id

    def add_concept(self, concept: Concept) -> None:
        """Add a concept to the graph."""
        self._concepts[concept.concept_id] = concept
        self._name_index[concept.name.lower()] = concept.concept_id
        self._graph.add_node(concept.concept_id, concept=concept)

    def create_concept(
        self,
        name: str,
        concept_type: str = "generic",
        metadata: Dict[str, Any] | None = None,
    ) -> Concept:
        """Create and add a new concept to the graph."""
        concept = Concept(
            name=name,
            concept_type=concept_type,
            metadata=metadata or {},
        )
        self.add_concept(concept)
        return concept

    def get_concept(self, concept_id: str) -> Concept | None:
        """Get a concept by its ID."""
        return self._concepts.get(concept_id)

    def get_concept_by_name(self, name: str) -> Concept | None:
        """Get a concept by its name (case-insensitive)."""
        concept_id = self._name_index.get(name.lower())
        if concept_id:
            return self._concepts.get(concept_id)
        return None

    def add_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: str,
        weight: float = 1.0,
        confidence: float = 1.0,
    ) -> bool:
        """Add a directed relation between two concepts."""
        if source_id not in self._concepts or target_id not in self._concepts:
            return False
        self._graph.add_edge(
            source_id,
            target_id,
            relation_type=relation_type,
            weight=weight,
            confidence=confidence,
        )
        return True

    def update_relation_weight(self, relation_id: str, weight: float) -> bool:
        """Update the weight of an existing relation by its persistent ID.

        The persistent ``relation_id`` is stored on the graph nodes' edge
        metadata when relations are restored from the database (see
        ``load_relations``), allowing Hebbian weight updates to round-trip
        to the persistence layer.

        Args:
            relation_id: The persistent database relation ID.
            weight: The new edge weight.

        Returns:
            True if a matching edge was updated.
        """
        for source_id, target_id, data in self._graph.edges(data=True):
            if data.get("relation_id") == relation_id:
                self._graph[source_id][target_id]["weight"] = float(weight)
                return True
        return False

    def load_relations(self, relations: List[Dict[str, Any]]) -> None:
        """Restore relations from the database with their persistent IDs.

        Args:
            relations: List of relation dicts as returned by
                ``Database.load_relations``.
        """
        for rel in relations:
            src, tgt = rel["source_id"], rel["target_id"]
            if src not in self._concepts or tgt not in self._concepts:
                continue
            self._graph.add_edge(
                src,
                tgt,
                relation_type=rel["relation_type"],
                weight=float(rel.get("weight", 1.0)),
                confidence=float(rel.get("confidence", 1.0)),
                relation_id=rel.get("relation_id"),
            )

    def get_relations(
        self,
        concept_id: str,
        direction: str = "outgoing",
    ) -> List[Dict[str, Any]]:
        """Get all relations for a concept."""
        relations = []

        if direction in ("outgoing", "both"):
            for _, target, data in self._graph.out_edges(concept_id, data=True):
                relations.append(
                    {
                        "source": concept_id,
                        "target": target,
                        "relation_type": data.get("relation_type", "related_to"),
                        "weight": data.get("weight", 1.0),
                        "confidence": data.get("confidence", 1.0),
                    }
                )

        if direction in ("incoming", "both"):
            for source, _, data in self._graph.in_edges(concept_id, data=True):
                relations.append(
                    {
                        "source": source,
                        "target": concept_id,
                        "relation_type": data.get("relation_type", "related_to"),
                        "weight": data.get("weight", 1.0),
                        "confidence": data.get("confidence", 1.0),
                    }
                )

        return relations

    def find_related(
        self,
        concept_id: str,
        relation_type: str | None = None,
        direction: str = "outgoing",
    ) -> List[Concept]:
        """Find concepts related to a given concept."""
        related = []
        relations = self.get_relations(concept_id, direction)

        for rel in relations:
            if relation_type and rel["relation_type"] != relation_type:
                continue
            other_id = rel["target"] if rel["source"] == concept_id else rel["source"]
            concept = self._concepts.get(other_id)
            if concept:
                related.append(concept)

        return related

    def get_neighbors(self, concept_id: str) -> List[str]:
        """Get all neighbor concept IDs (both directions)."""
        neighbors = set()
        neighbors.update(self._graph.successors(concept_id))
        neighbors.update(self._graph.predecessors(concept_id))
        return list(neighbors)

    def set_edge_weight(self, source_id: str, target_id: str, weight: float) -> None:
        """Update an existing edge's weight by its node pair (in place)."""
        if source_id not in self._concepts or target_id not in self._concepts:
            return
        if self._graph.has_edge(source_id, target_id):
            self._graph[source_id][target_id]["weight"] = float(weight)

    @property
    def graph(self) -> nx.DiGraph:
        """Access the underlying NetworkX graph."""
        return self._graph

    @property
    def num_concepts(self) -> int:
        """Number of concepts in the graph."""
        return len(self._concepts)

    def get_all_relations(self) -> List[Dict[str, Any]]:
        """Return every relation (edge) in the knowledge graph.

        Used by the persistence layer to save the learned graph to the
        database so knowledge survives server restarts.

        Returns:
            List of dicts with source_id, target_id, relation_type,
            weight and confidence for every edge.
        """
        relations = []
        for source_id, target_id, data in self._graph.edges(data=True):
            relations.append(
                {
                    "source_id": source_id,
                    "target_id": target_id,
                    "relation_type": data.get("relation_type", "related_to"),
                    "weight": data.get("weight", 1.0),
                    "confidence": data.get("confidence", 1.0),
                }
            )
        return relations

    @property
    def num_relations(self) -> int:
        """Number of relations in the graph."""
        return self._graph.number_of_edges()

    def __repr__(self) -> str:
        return f"ConceptGraph(concepts={self.num_concepts}, relations={self.num_relations})"
