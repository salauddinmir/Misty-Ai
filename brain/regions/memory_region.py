"""
Memory Region Module.

Implements a MemoryRegion inspired by hippocampal memory systems.
Supports encoding new patterns and retrieving stored patterns
using cosine similarity matching between cues and stored memories.
"""

from typing import List, Tuple

import numpy as np

from brain.regions.region import BrainRegion


class MemoryRegion(BrainRegion):
    """Hippocampus-inspired memory region for pattern encoding and retrieval.

    Stores patterns as dense vectors and retrieves the best matching
    stored memory given a cue using cosine similarity. The region's
    neuron population is driven by the retrieved pattern during recall,
    producing spike-based output.

    The memory process:
      1. Encode: Store a pattern (activity vector) in the memory bank.
      2. Retrieve: Given a cue, find the most similar stored pattern
         using cosine similarity, then inject it as current to produce spikes.

    Attributes:
        memory_bank: List of stored pattern vectors.
        memory_labels: Optional labels for stored patterns.
        retrieval_threshold: Minimum cosine similarity for successful retrieval.
        max_memories: Maximum number of stored patterns (oldest are overwritten).
    """

    def __init__(
        self,
        name: str = "memory",
        size: int = 512,
        retrieval_threshold: float = 0.3,
        max_memories: int = 1000,
        excitatory_ratio: float = 0.8,
        threshold: float = 1.0,
        decay: float = 0.9,
        refractory_period: int = 2,
    ) -> None:
        """Initialize a memory region.

        Args:
            name: Human-readable name for the region.
            size: Number of neurons in the memory population.
            retrieval_threshold: Minimum cosine similarity for retrieval.
            max_memories: Maximum number of stored memories.
            excitatory_ratio: Fraction of excitatory neurons.
            threshold: Firing threshold.
            decay: Membrane decay rate.
            refractory_period: Refractory period in timesteps.
        """
        super().__init__(
            name=name,
            size=size,
            excitatory_ratio=excitatory_ratio,
            threshold=threshold,
            decay=decay,
            refractory_period=refractory_period,
        )
        self.retrieval_threshold: float = retrieval_threshold
        self.max_memories: int = max_memories
        self.memory_bank: List[np.ndarray] = []
        self.memory_labels: List[str] = []

    def encode(self, pattern: np.ndarray, label: str | None = None) -> int:
        """Encode a new pattern into the memory bank.

        Stores the pattern vector. If the memory bank is full, the oldest
        memory is overwritten (FIFO replacement).

        Args:
            pattern: Array to store. Will be flattened and resized to
                     match the region's size.
            label: Optional human-readable label for the memory.

        Returns:
            Index at which the pattern was stored.
        """
        flat = np.asarray(pattern, dtype=np.float64).flatten()

        # Resize to match population size
        memory_vec = np.zeros(self.size, dtype=np.float64)
        n = min(len(flat), self.size)
        memory_vec[:n] = flat[:n]

        # Normalize for consistent cosine similarity
        norm = np.linalg.norm(memory_vec)
        if norm > 1e-10:
            memory_vec = memory_vec / norm

        # Store (with FIFO replacement if full)
        if len(self.memory_bank) >= self.max_memories:
            # Replace oldest
            idx = len(self.memory_bank) % self.max_memories
            self.memory_bank[idx] = memory_vec
            self.memory_labels[idx] = label or ""
            return idx
        else:
            self.memory_bank.append(memory_vec)
            self.memory_labels.append(label or "")
            return len(self.memory_bank) - 1

    def retrieve(self, cue: np.ndarray) -> Tuple[np.ndarray | None, float]:
        """Retrieve the most similar stored pattern given a cue.

        Computes cosine similarity between the cue and all stored patterns,
        returning the best match if it exceeds the retrieval threshold.

        The retrieved pattern is also injected into the population as
        current, producing spike-based output on the next step().

        Args:
            cue: Query array used to search the memory bank.

        Returns:
            Tuple of (retrieved_pattern, similarity_score).
            If no memory exceeds the threshold, returns (None, 0.0).
        """
        if not self.memory_bank:
            return None, 0.0

        # Prepare cue vector
        flat_cue = np.asarray(cue, dtype=np.float64).flatten()
        cue_vec = np.zeros(self.size, dtype=np.float64)
        n = min(len(flat_cue), self.size)
        cue_vec[:n] = flat_cue[:n]

        # Normalize cue
        cue_norm = np.linalg.norm(cue_vec)
        if cue_norm < 1e-10:
            return None, 0.0
        cue_vec = cue_vec / cue_norm

        # Compute cosine similarity with all stored patterns
        # Stack memory bank into a matrix for vectorized computation
        memory_matrix = np.array(self.memory_bank)  # (num_memories, size)
        similarities = memory_matrix @ cue_vec  # cosine sim (patterns are normalized)

        # Find best match
        best_idx = int(np.argmax(similarities))
        best_similarity = float(similarities[best_idx])

        if best_similarity < self.retrieval_threshold:
            return None, best_similarity

        retrieved = self.memory_bank[best_idx]

        # Inject retrieved pattern as current for next step
        self.input_buffer = retrieved * self.population.threshold[0] * 1.5

        return retrieved.copy(), best_similarity

    def get_memory_count(self) -> int:
        """Return the number of currently stored memories.

        Returns:
            Number of patterns in the memory bank.
        """
        return len(self.memory_bank)

    def clear_memories(self) -> None:
        """Clear all stored memories."""
        self.memory_bank.clear()
        self.memory_labels.clear()

    def __repr__(self) -> str:
        return (
            f"MemoryRegion(name='{self.name}', size={self.size}, "
            f"memories={self.get_memory_count()}/{self.max_memories})"
        )
