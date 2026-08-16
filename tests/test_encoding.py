"""
Tests for Spike Encoding Module.

Tests cover:
- TextEncoder produces arrays from text
- ConceptEncoder consistency and sparsity
- Decoder round-trip (encode -> decode recovers concept)
- Decoder with noisy input
"""

import numpy as np
import pytest

from brain.encoding.text_encoder import TextEncoder
from brain.encoding.concept_encoder import ConceptEncoder
from brain.encoding.decoder import Decoder


class TestTextEncoder:
    """Test TextEncoder functionality."""

    def test_encode_produces_array(self) -> None:
        """Encoding text produces a numpy array of correct size."""
        encoder = TextEncoder(population_size=500)
        result = encoder.encode("hello world")
        assert result.shape == (500,)
        assert result.dtype == np.float64

    def test_encode_nonempty_text_has_activity(self) -> None:
        """Non-empty text produces non-zero array."""
        encoder = TextEncoder(population_size=1000)
        result = encoder.encode("The cat sat on the mat")
        assert np.sum(result > 0) > 0

    def test_encode_empty_text_is_zero(self) -> None:
        """Empty text produces all-zero array."""
        encoder = TextEncoder(population_size=500)
        result = encoder.encode("")
        assert np.all(result == 0.0)

    def test_encode_deterministic(self) -> None:
        """Same text always produces same encoding."""
        encoder = TextEncoder(population_size=1000)
        r1 = encoder.encode("hello world")
        r2 = encoder.encode("hello world")
        np.testing.assert_array_equal(r1, r2)

    def test_different_text_different_encoding(self) -> None:
        """Different texts produce different encodings."""
        encoder = TextEncoder(population_size=1000)
        r1 = encoder.encode("hello world")
        r2 = encoder.encode("goodbye universe")
        assert not np.array_equal(r1, r2)

    def test_custom_population_size(self) -> None:
        """Can override population size in encode call."""
        encoder = TextEncoder(population_size=100)
        result = encoder.encode("test", population_size=200)
        assert result.shape == (200,)

    def test_values_in_valid_range(self) -> None:
        """All output values are in [0, 1]."""
        encoder = TextEncoder(population_size=1000)
        result = encoder.encode("The quick brown fox jumps over the lazy dog")
        assert np.all(result >= 0.0)
        assert np.all(result <= 1.0)


class TestConceptEncoder:
    """Test ConceptEncoder functionality."""

    def test_encode_concept_produces_binary(self) -> None:
        """Encoded concept is a binary array."""
        encoder = ConceptEncoder(population_size=1000, sparsity=0.07)
        pattern = encoder.encode_concept("cat")
        assert pattern.shape == (1000,)
        # Should only contain 0s and 1s
        assert np.all((pattern == 0) | (pattern == 1))

    def test_sparsity_target(self) -> None:
        """Pattern sparsity matches target (~7%)."""
        encoder = ConceptEncoder(population_size=1000, sparsity=0.07)
        pattern = encoder.encode_concept("cat")
        actual_sparsity = np.sum(pattern) / len(pattern)
        assert 0.05 <= actual_sparsity <= 0.10

    def test_consistency(self) -> None:
        """Same concept always produces same pattern."""
        encoder = ConceptEncoder(population_size=1000)
        p1 = encoder.encode_concept("dog")
        p2 = encoder.encode_concept("dog")
        np.testing.assert_array_equal(p1, p2)

    def test_different_concepts_different_patterns(self) -> None:
        """Different concepts produce different patterns."""
        encoder = ConceptEncoder(population_size=1000)
        p1 = encoder.encode_concept("cat")
        p2 = encoder.encode_concept("dog")
        assert not np.array_equal(p1, p2)

    def test_low_overlap_between_concepts(self) -> None:
        """Different concepts have low overlap."""
        encoder = ConceptEncoder(population_size=1000, sparsity=0.07)
        p1 = encoder.encode_concept("cat")
        p2 = encoder.encode_concept("dog")
        overlap = encoder.compute_overlap(p1, p2)
        # With 7% sparsity, random overlap should be low
        assert overlap < 0.3

    def test_register_concept_manual(self) -> None:
        """Can register a concept with a manual pattern."""
        encoder = ConceptEncoder(population_size=100)
        custom_pattern = np.zeros(100)
        custom_pattern[0:10] = 1.0
        registered = encoder.register_concept("custom", custom_pattern)
        assert np.sum(registered) == 10
        # Verify retrieval
        retrieved = encoder.get_pattern("custom")
        np.testing.assert_array_equal(registered, retrieved)

    def test_get_pattern_unregistered_returns_none(self) -> None:
        """get_pattern returns None for unregistered concepts."""
        encoder = ConceptEncoder(population_size=100)
        assert encoder.get_pattern("unknown") is None

    def test_get_all_concepts(self) -> None:
        """get_all_concepts returns registered concept IDs."""
        encoder = ConceptEncoder(population_size=100)
        encoder.encode_concept("cat")
        encoder.encode_concept("dog")
        concepts = encoder.get_all_concepts()
        assert "cat" in concepts
        assert "dog" in concepts
        assert len(concepts) == 2


class TestDecoder:
    """Test Decoder functionality."""

    def test_decode_exact_pattern(self) -> None:
        """Decoding an exact concept pattern recovers the concept."""
        encoder = ConceptEncoder(population_size=500, sparsity=0.07)
        decoder = Decoder(similarity_threshold=0.1)

        # Register some concepts
        encoder.encode_concept("cat")
        encoder.encode_concept("dog")
        encoder.encode_concept("bird")

        # Decode exact cat pattern
        cat_pattern = encoder.get_pattern("cat")
        matches = decoder.decode(cat_pattern, encoder)

        assert len(matches) > 0
        assert matches[0][0] == "cat"
        assert matches[0][1] > 0.9  # High confidence for exact match

    def test_decode_noisy_pattern(self) -> None:
        """Decoding a noisy pattern still finds correct concept."""
        encoder = ConceptEncoder(population_size=500, sparsity=0.07)
        decoder = Decoder(similarity_threshold=0.1)

        encoder.encode_concept("cat")
        encoder.encode_concept("dog")
        encoder.encode_concept("bird")
        encoder.encode_concept("fish")

        # Add noise to cat pattern
        cat_pattern = encoder.get_pattern("cat").copy()
        # Flip some bits
        noise_indices = np.random.choice(500, size=10, replace=False)
        cat_pattern[noise_indices] = 1.0 - cat_pattern[noise_indices]

        matches = decoder.decode(cat_pattern, encoder)
        # Cat should still be top match
        assert len(matches) > 0
        assert matches[0][0] == "cat"

    def test_decode_best(self) -> None:
        """decode_best returns single best match."""
        encoder = ConceptEncoder(population_size=500)
        decoder = Decoder()

        encoder.encode_concept("apple")
        pattern = encoder.get_pattern("apple")
        concept_id, confidence = decoder.decode_best(pattern, encoder)
        assert concept_id == "apple"
        assert confidence > 0.9

    def test_decode_empty_encoder(self) -> None:
        """Decoding with no registered concepts returns empty list."""
        encoder = ConceptEncoder(population_size=100)
        decoder = Decoder()
        matches = decoder.decode(np.random.rand(100), encoder)
        assert matches == []

    def test_decode_zero_pattern(self) -> None:
        """Decoding a zero pattern returns empty list."""
        encoder = ConceptEncoder(population_size=100)
        encoder.encode_concept("test")
        decoder = Decoder()
        matches = decoder.decode(np.zeros(100), encoder)
        assert matches == []

    def test_round_trip_encode_decode(self) -> None:
        """Full round-trip: encode concept, decode back, recovers identity."""
        encoder = ConceptEncoder(population_size=1000, sparsity=0.07)
        decoder = Decoder(similarity_threshold=0.1)

        # Register multiple concepts
        concepts = ["cat", "dog", "bird", "fish", "tree", "house"]
        for c in concepts:
            encoder.encode_concept(c)

        # For each concept, verify round-trip
        for c in concepts:
            pattern = encoder.get_pattern(c)
            best_id, confidence = decoder.decode_best(pattern, encoder)
            assert best_id == c, f"Round-trip failed for {c}: got {best_id}"
            assert confidence > 0.9
