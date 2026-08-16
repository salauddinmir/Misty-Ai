"""
Text Encoder Module.

Converts text input into spike probability arrays suitable for
driving sensory neuron populations. Uses rate coding where token
importance maps to higher spike probability.
"""

from typing import List

import numpy as np


class TextEncoder:
    """Encodes text into neural spike probability patterns.

    Tokenizes input text and distributes tokens across a neural population
    using hash-based mapping. Token importance (based on position and
    frequency) determines the spike probability at each neuron position.

    The encoding is deterministic: the same text always produces the
    same output array.

    Attributes:
        population_size: Default size of the output spike probability array.
        min_rate: Minimum spike probability for active neurons.
        max_rate: Maximum spike probability for active neurons.
    """

    def __init__(
        self,
        population_size: int = 1000,
        min_rate: float = 0.1,
        max_rate: float = 0.9,
    ) -> None:
        """Initialize the text encoder.

        Args:
            population_size: Default size of the output array.
            min_rate: Minimum spike probability for encoded tokens.
            max_rate: Maximum spike probability for encoded tokens.
        """
        self.population_size: int = population_size
        self.min_rate: float = min_rate
        self.max_rate: float = max_rate

    def encode(self, text: str, population_size: int = 0) -> np.ndarray:
        """Encode text into a spike probability array.

        Tokenizes the text by whitespace, computes importance scores
        based on token frequency and position, then maps each token
        to neuron positions using deterministic hashing.

        Args:
            text: Input text to encode.
            population_size: Size of the output array. If 0, uses
                           the instance default.

        Returns:
            Array of shape (population_size,) with values in [0, 1]
            representing spike probability at each neuron position.
        """
        size = population_size if population_size > 0 else self.population_size
        output = np.zeros(size, dtype=np.float64)

        if not text or not text.strip():
            return output

        tokens = self._tokenize(text)
        if not tokens:
            return output

        # Compute importance scores for each token
        importance = self._compute_importance(tokens)

        # Map tokens to neuron positions using hash-based distribution
        for i, token in enumerate(tokens):
            positions = self._hash_to_positions(token, size)
            rate = self.min_rate + importance[i] * (self.max_rate - self.min_rate)
            for pos in positions:
                output[pos] = max(output[pos], rate)

        return output

    def _tokenize(self, text: str) -> List[str]:
        """Split text into tokens.

        Performs basic whitespace tokenization with lowercasing
        and punctuation stripping.

        Args:
            text: Input text.

        Returns:
            List of cleaned token strings.
        """
        raw_tokens = text.lower().split()
        cleaned = []
        for token in raw_tokens:
            token = token.strip(".,!?;:\"'()[]{}/-")
            if token:
                cleaned.append(token)
        return cleaned

    def _compute_importance(self, tokens: List[str]) -> np.ndarray:
        """Compute importance scores for each token.

        Uses a combination of:
        - Inverse position weighting (earlier tokens slightly more important)
        - Frequency weighting (rare tokens more important, like TF-IDF)

        Args:
            tokens: List of token strings.

        Returns:
            Array of shape (len(tokens),) with importance scores in [0, 1].
        """
        n = len(tokens)
        scores = np.zeros(n, dtype=np.float64)

        # Count token frequencies
        freq: dict = {}
        for t in tokens:
            freq[t] = freq.get(t, 0) + 1

        for i, token in enumerate(tokens):
            # Position score: slight preference for earlier tokens
            position_score = 1.0 - (i / (n + 1)) * 0.3

            # Frequency score: rare tokens get higher importance
            freq_score = 1.0 / freq[token]

            # Combined score
            scores[i] = position_score * freq_score

        # Normalize to [0, 1]
        if scores.max() > 0:
            scores = scores / scores.max()

        return scores

    def _hash_to_positions(self, token: str, size: int, spread: int = 5) -> List[int]:
        """Map a token to multiple neuron positions using hashing.

        Uses multiple hash seeds to spread each token across several
        neuron positions, creating a distributed representation.

        Args:
            token: The token string to map.
            size: Size of the target population.
            spread: Number of neuron positions to activate per token.

        Returns:
            List of neuron indices that this token activates.
        """
        positions = []
        for seed in range(spread):
            # Deterministic hash using FNV-1a style
            h = 2166136261
            for char in f"{token}_{seed}_misty":
                h ^= ord(char)
                h = (h * 16777619) & 0xFFFFFFFF
            pos = h % size
            positions.append(pos)
        return positions

    def __repr__(self) -> str:
        return (
            f"TextEncoder(population_size={self.population_size}, "
            f"rate_range=[{self.min_rate}, {self.max_rate}])"
        )
