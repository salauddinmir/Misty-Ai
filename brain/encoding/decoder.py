"""
Decoder Module.

Decodes active neural spike patterns back to concept identities
by comparing them against known concept patterns using similarity
metrics.
"""

from typing import List, Tuple

import numpy as np

from brain.encoding.concept_encoder import ConceptEncoder


class Decoder:
    """Decodes neural spike patterns into concept identities.

    Compares an observed spike pattern against all registered concept
    patterns in a ConceptEncoder and returns ranked matches based on
    cosine similarity scores.

    Attributes:
        similarity_threshold: Minimum similarity score for a valid match.
    """

    def __init__(self, similarity_threshold: float = 0.1) -> None:
        """Initialize the decoder.

        Args:
            similarity_threshold: Minimum similarity to include a concept
                                 in the decoded results.
        """
        self.similarity_threshold: float = similarity_threshold

    def decode(
        self,
        spike_pattern: np.ndarray,
        concept_encoder: ConceptEncoder,
    ) -> List[Tuple[str, float]]:
        """Decode a spike pattern into concept identities.

        Compares the given spike pattern against all registered concept
        patterns using cosine similarity and returns ranked matches.

        Args:
            spike_pattern: Array representing the observed neural activity.
                          Can be binary (0/1) or continuous (firing rates).
            concept_encoder: The ConceptEncoder containing registered concepts.

        Returns:
            List of (concept_id, confidence) tuples sorted by confidence
            in descending order. Only includes matches above the similarity
            threshold.
        """
        pattern = np.asarray(spike_pattern, dtype=np.float64).flatten()

        # Resize pattern to match encoder's population size if needed
        if len(pattern) != concept_encoder.population_size:
            resized = np.zeros(concept_encoder.population_size, dtype=np.float64)
            n = min(len(pattern), concept_encoder.population_size)
            resized[:n] = pattern[:n]
            pattern = resized

        concepts = concept_encoder.get_all_concepts()
        if not concepts:
            return []

        # Compute pattern norm once
        pattern_norm = np.linalg.norm(pattern)
        if pattern_norm < 1e-10:
            return []

        matches: List[Tuple[str, float]] = []

        for concept_id in concepts:
            concept_pattern = concept_encoder.patterns[concept_id]

            # Cosine similarity
            concept_norm = np.linalg.norm(concept_pattern)
            if concept_norm < 1e-10:
                continue

            similarity = float(
                np.dot(pattern, concept_pattern) / (pattern_norm * concept_norm)
            )

            if similarity >= self.similarity_threshold:
                matches.append((concept_id, similarity))

        # Sort by confidence descending
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches

    def decode_top_k(
        self,
        spike_pattern: np.ndarray,
        concept_encoder: ConceptEncoder,
        k: int = 5,
    ) -> List[Tuple[str, float]]:
        """Decode and return only the top-k matching concepts.

        Args:
            spike_pattern: Array representing the observed neural activity.
            concept_encoder: The ConceptEncoder containing registered concepts.
            k: Maximum number of results to return.

        Returns:
            List of up to k (concept_id, confidence) tuples sorted by
            confidence in descending order.
        """
        all_matches = self.decode(spike_pattern, concept_encoder)
        return all_matches[:k]

    def decode_best(
        self,
        spike_pattern: np.ndarray,
        concept_encoder: ConceptEncoder,
    ) -> Tuple[str, float]:
        """Decode and return only the best matching concept.

        Args:
            spike_pattern: Array representing the observed neural activity.
            concept_encoder: The ConceptEncoder containing registered concepts.

        Returns:
            Tuple of (concept_id, confidence) for the best match.
            Returns ("", 0.0) if no match is found above threshold.
        """
        matches = self.decode(spike_pattern, concept_encoder)
        if matches:
            return matches[0]
        return ("", 0.0)

    def __repr__(self) -> str:
        return f"Decoder(similarity_threshold={self.similarity_threshold})"
