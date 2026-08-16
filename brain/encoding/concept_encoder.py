"""
Concept Encoder Module.

Provides sparse distributed representations (SDRs) for concepts.
Each concept gets a unique binary pattern with configurable sparsity,
enabling efficient neural representation and similarity computation.
"""

from typing import Dict, List

import numpy as np


class ConceptEncoder:
    """Encodes concepts as sparse distributed representations (SDRs).

    Each concept is assigned a unique binary pattern where a small
    percentage of bits are active (sparse). The same concept always
    maps to the same pattern (deterministic via hashing). Patterns
    can also be manually registered.

    Properties of SDRs:
      - Sparse: Only ~5-10% of neurons are active per concept.
      - Distributed: Each concept activates neurons spread across the population.
      - Unique: Different concepts have low overlap.
      - Consistent: Same concept always produces the same pattern.

    Attributes:
        population_size: Size of the neural population (pattern length).
        sparsity: Target fraction of active bits in each pattern.
        patterns: Dictionary mapping concept IDs to their binary patterns.
    """

    def __init__(
        self,
        population_size: int = 1000,
        sparsity: float = 0.07,
    ) -> None:
        """Initialize the concept encoder.

        Args:
            population_size: Number of neurons in the target population.
            sparsity: Target fraction of active bits (default 0.07 = 7%).
        """
        self.population_size: int = population_size
        self.sparsity: float = sparsity
        self.patterns: Dict[str, np.ndarray] = {}

    def encode_concept(self, concept_id: str) -> np.ndarray:
        """Get or generate the SDR pattern for a concept.

        If the concept has been previously encoded or registered,
        returns the stored pattern. Otherwise, generates a new
        deterministic pattern and stores it.

        Args:
            concept_id: Unique identifier for the concept.

        Returns:
            Binary array of shape (population_size,) with ~sparsity fraction
            of ones.
        """
        if concept_id in self.patterns:
            return self.patterns[concept_id].copy()

        # Generate deterministic pattern
        pattern = self._generate_pattern(concept_id)
        self.patterns[concept_id] = pattern
        return pattern.copy()

    def register_concept(self, concept_id: str, pattern: np.ndarray | None = None) -> np.ndarray:
        """Register a concept with an explicit or auto-generated pattern.

        Args:
            concept_id: Unique identifier for the concept.
            pattern: Optional binary pattern array. If None, generates
                    a new pattern automatically.

        Returns:
            The registered pattern.
        """
        if pattern is not None:
            flat = np.asarray(pattern, dtype=np.float64).flatten()
            # Resize to match population size
            registered = np.zeros(self.population_size, dtype=np.float64)
            n = min(len(flat), self.population_size)
            registered[:n] = flat[:n]
            # Binarize
            registered = (registered > 0.5).astype(np.float64)
            self.patterns[concept_id] = registered
            return registered.copy()
        else:
            return self.encode_concept(concept_id)

    def get_pattern(self, concept_id: str) -> np.ndarray | None:
        """Retrieve the stored pattern for a concept.

        Args:
            concept_id: The concept identifier to look up.

        Returns:
            The binary pattern array, or None if the concept is not registered.
        """
        if concept_id in self.patterns:
            return self.patterns[concept_id].copy()
        return None

    def get_all_concepts(self) -> List[str]:
        """Get a list of all registered concept IDs.

        Returns:
            List of concept ID strings.
        """
        return list(self.patterns.keys())

    def _generate_pattern(self, concept_id: str) -> np.ndarray:
        """Generate a deterministic sparse pattern for a concept.

        Uses consistent hashing to select which neurons are active,
        ensuring the same concept_id always produces the same pattern.

        Args:
            concept_id: The concept identifier to generate a pattern for.

        Returns:
            Binary array of shape (population_size,) with target sparsity.
        """
        seed = self._concept_to_seed(concept_id)
        rng = np.random.default_rng(seed)

        # Number of active bits
        n_active = max(1, int(self.population_size * self.sparsity))

        # Select random positions (deterministic due to seeded RNG)
        active_indices = rng.choice(self.population_size, size=n_active, replace=False)

        pattern = np.zeros(self.population_size, dtype=np.float64)
        pattern[active_indices] = 1.0

        return pattern

    def _concept_to_seed(self, concept_id: str) -> int:
        """Convert a concept ID string to a deterministic integer seed.

        Uses FNV-1a inspired hash for consistency across sessions.

        Args:
            concept_id: The concept identifier string.

        Returns:
            Non-negative integer suitable for use as a random seed.
        """
        h = 2166136261
        for char in concept_id:
            h ^= ord(char)
            h = (h * 16777619) & 0xFFFFFFFF
        return h

    def compute_overlap(self, pattern_a: np.ndarray, pattern_b: np.ndarray) -> float:
        """Compute the overlap between two patterns (Jaccard similarity).

        Args:
            pattern_a: First binary pattern.
            pattern_b: Second binary pattern.

        Returns:
            Overlap score between 0.0 and 1.0.
        """
        a = (np.asarray(pattern_a) > 0.5).astype(np.float64)
        b = (np.asarray(pattern_b) > 0.5).astype(np.float64)

        intersection = np.sum(a * b)
        union = np.sum(np.clip(a + b, 0, 1))

        if union == 0:
            return 0.0
        return float(intersection / union)

    def __repr__(self) -> str:
        return (
            f"ConceptEncoder(population_size={self.population_size}, "
            f"sparsity={self.sparsity}, concepts={len(self.patterns)})"
        )
