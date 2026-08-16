"""
Spreading Activation Algorithm.

Activates a source concept and propagates activation to
connected concepts with distance-based decay.
"""

from dataclasses import dataclass
from typing import Dict, List, Set

from brain.graph.concepts import ConceptGraph


@dataclass
class SpreadingActivation:
    """Spreading activation over a concept graph.

    Activation starts at a source node and spreads to neighbors,
    decaying with each hop. This simulates associative recall.
    """

    decay_factor: float = 0.6
    threshold: float = 0.01
    max_depth: int = 3

    def activate(
        self,
        graph: ConceptGraph,
        source_id: str,
        initial_activation: float = 1.0,
    ) -> Dict[str, float]:
        """Spread activation from a source concept.

        Args:
            graph: The concept graph to spread activation over.
            source_id: ID of the concept to start from.
            initial_activation: Activation level at the source.

        Returns:
            Dictionary mapping concept_id -> activation level.
        """
        activation_map: Dict[str, float] = {}
        visited: Set[str] = set()

        # BFS-like spreading
        queue: List[tuple] = [(source_id, initial_activation, 0)]

        while queue:
            current_id, current_activation, depth = queue.pop(0)

            if current_id in visited:
                if current_id in activation_map:
                    activation_map[current_id] = max(activation_map[current_id], current_activation)
                continue

            if current_activation < self.threshold:
                continue

            if depth > self.max_depth:
                continue

            visited.add(current_id)
            activation_map[current_id] = current_activation

            # Update the concept's activation level
            concept = graph.get_concept(current_id)
            if concept:
                concept.activate(current_activation)

            # Spread to neighbors
            neighbors = graph.get_neighbors(current_id)
            for neighbor_id in neighbors:
                if neighbor_id not in visited:
                    relations = graph.get_relations(current_id, direction="both")
                    edge_weight = 1.0
                    for rel in relations:
                        other = rel["target"] if rel["source"] == current_id else rel["source"]
                        if other == neighbor_id:
                            edge_weight = rel["weight"]
                            break

                    new_activation = current_activation * self.decay_factor * edge_weight
                    if new_activation >= self.threshold:
                        queue.append((neighbor_id, new_activation, depth + 1))

        return activation_map

    def find_most_activated(
        self,
        graph: ConceptGraph,
        source_id: str,
        initial_activation: float = 1.0,
        top_n: int = 5,
    ) -> List[tuple]:
        """Spread activation and return the most activated concepts."""
        activation_map = self.activate(graph, source_id, initial_activation)
        sorted_items = sorted(activation_map.items(), key=lambda x: x[1], reverse=True)
        return sorted_items[:top_n]

    def __repr__(self) -> str:
        return f"SpreadingActivation(decay={self.decay_factor}, threshold={self.threshold}, max_depth={self.max_depth})"
