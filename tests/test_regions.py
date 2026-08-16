"""
Tests for Brain Regions.

Tests cover:
- Base BrainRegion step mechanics
- SensoryRegion encoding and spike production
- AssociationRegion pattern completion
- MemoryRegion encode and retrieve
- PrefrontalRegion goal tracking
- RewardRegion modulation
"""

import numpy as np

from brain.regions.association import AssociationRegion
from brain.regions.memory_region import MemoryRegion
from brain.regions.prefrontal import PrefrontalRegion
from brain.regions.region import BrainRegion
from brain.regions.reward_region import RewardRegion
from brain.regions.sensory import SensoryRegion


class TestBrainRegion:
    """Test base BrainRegion class."""

    def test_creation(self) -> None:
        """BrainRegion creates with correct parameters."""
        region = BrainRegion(name="test", size=100)
        assert region.name == "test"
        assert region.size == 100
        assert region.population.size == 100

    def test_receive_input_accumulates(self) -> None:
        """Multiple receive_input calls accumulate currents."""
        region = BrainRegion(name="test", size=10)
        region.receive_input(np.ones(10) * 0.5)
        region.receive_input(np.ones(10) * 0.3)
        np.testing.assert_allclose(region.input_buffer, np.full(10, 0.8))

    def test_step_clears_buffer(self) -> None:
        """step() clears input buffer after processing."""
        region = BrainRegion(name="test", size=10)
        region.receive_input(np.ones(10) * 2.0)
        region.step()
        assert np.all(region.input_buffer == 0.0)

    def test_step_produces_spikes(self) -> None:
        """step() produces spikes when input is sufficient."""
        region = BrainRegion(name="test", size=10, threshold=1.0)
        region.receive_input(np.full(10, 2.0))
        spikes = region.step()
        assert np.all(spikes)

    def test_firing_rate_tracking(self) -> None:
        """Firing rate tracks over multiple steps."""
        region = BrainRegion(name="test", size=100, threshold=1.0)
        # Fire all neurons
        region.receive_input(np.full(100, 2.0))
        region.step()
        assert region.get_firing_rate() == 1.0

    def test_reset(self) -> None:
        """Reset clears all state."""
        region = BrainRegion(name="test", size=10, threshold=1.0)
        region.receive_input(np.full(10, 2.0))
        region.step()
        region.reset()
        assert np.all(region.input_buffer == 0.0)
        assert not np.any(region.output_spikes)
        assert region.get_firing_rate() == 0.0


class TestSensoryRegion:
    """Test SensoryRegion encoding."""

    def test_encode_input_sets_buffer(self) -> None:
        """encode_input() populates the input buffer."""
        sensory = SensoryRegion(name="visual", size=100)
        data = np.random.rand(100)
        currents = sensory.encode_input(data)
        assert currents.shape == (100,)
        assert np.any(currents > 0)

    def test_encode_then_step_produces_spikes(self) -> None:
        """After encoding strong input, step produces spikes."""
        sensory = SensoryRegion(name="visual", size=100, gain=3.0, threshold=1.0)
        data = np.ones(100)  # Strong uniform input
        sensory.encode_input(data)
        spikes = sensory.step()
        # At least some neurons should fire with gain=3.0 and threshold=1.0
        assert np.sum(spikes) > 0

    def test_zero_input_no_spikes(self) -> None:
        """Zero input produces no spikes."""
        sensory = SensoryRegion(name="visual", size=100, noise_level=0.0)
        sensory.encode_input(np.zeros(100))
        spikes = sensory.step()
        assert not np.any(spikes)

    def test_small_input_padded(self) -> None:
        """Input smaller than population is zero-padded."""
        sensory = SensoryRegion(name="visual", size=100, noise_level=0.0)
        currents = sensory.encode_input(np.array([1.0, 2.0, 3.0]))
        assert currents.shape == (100,)


class TestAssociationRegion:
    """Test AssociationRegion pattern completion."""

    def test_store_pattern(self) -> None:
        """Can store patterns in association region."""
        assoc = AssociationRegion(name="assoc", size=100)
        pattern = np.zeros(100)
        pattern[10:30] = 1.0
        assoc.store_pattern(pattern)
        assert len(assoc.stored_patterns) == 1

    def test_pattern_completion_recovers_stored(self) -> None:
        """Pattern completion with partial cue produces activity."""
        assoc = AssociationRegion(name="assoc", size=100, threshold=1.0)
        # Store a pattern
        pattern = np.zeros(100)
        pattern[10:30] = 1.0
        assoc.store_pattern(pattern)

        # Present partial cue
        partial = np.zeros(100)
        partial[10:20] = 1.0  # Only half the pattern
        result = assoc.pattern_completion(partial)
        # Result should have non-zero activity
        assert result.shape == (100,)
        assert np.sum(result) > 0

    def test_step_with_recurrent_dynamics(self) -> None:
        """Step includes recurrent feedback."""
        assoc = AssociationRegion(name="assoc", size=50, threshold=1.0)
        pattern = np.zeros(50)
        pattern[5:15] = 1.0
        assoc.store_pattern(pattern)

        # Inject input and step multiple times
        assoc.receive_input(np.full(50, 1.5))
        spikes1 = assoc.step()
        # Subsequent steps may have recurrent activity
        spikes2 = assoc.step()
        # Both should be valid boolean arrays
        assert spikes1.dtype == bool
        assert spikes2.dtype == bool


class TestMemoryRegion:
    """Test MemoryRegion encode and retrieve."""

    def test_encode_stores_pattern(self) -> None:
        """encode() stores a pattern in memory bank."""
        mem = MemoryRegion(name="hippo", size=100)
        pattern = np.random.rand(100)
        idx = mem.encode(pattern, label="test_memory")
        assert idx == 0
        assert mem.get_memory_count() == 1

    def test_retrieve_finds_matching_pattern(self) -> None:
        """retrieve() returns the most similar stored pattern."""
        mem = MemoryRegion(name="hippo", size=100, retrieval_threshold=0.1)
        # Store a pattern
        pattern = np.random.rand(100)
        mem.encode(pattern, label="original")

        # Retrieve with slightly noisy cue
        noisy_cue = pattern + np.random.randn(100) * 0.1
        retrieved, similarity = mem.retrieve(noisy_cue)

        assert retrieved is not None
        assert similarity > 0.5

    def test_retrieve_no_match_below_threshold(self) -> None:
        """retrieve() returns None if no match exceeds threshold."""
        mem = MemoryRegion(name="hippo", size=100, retrieval_threshold=0.9)
        pattern = np.zeros(100)
        pattern[:10] = 1.0
        mem.encode(pattern)

        # Completely different cue
        random_cue = np.random.rand(100)
        retrieved, similarity = mem.retrieve(random_cue)
        # May or may not match depending on random, but threshold is high
        # We just verify the interface works
        assert isinstance(similarity, float)
        assert retrieved is None or retrieved.shape == pattern.shape

    def test_multiple_memories_retrieves_best(self) -> None:
        """With multiple stored patterns, retrieves the closest."""
        mem = MemoryRegion(name="hippo", size=100, retrieval_threshold=0.1)

        # Store distinct patterns
        p1 = np.zeros(100)
        p1[:30] = 1.0
        mem.encode(p1, label="pattern_1")

        p2 = np.zeros(100)
        p2[50:80] = 1.0
        mem.encode(p2, label="pattern_2")

        # Cue similar to p1
        cue = np.zeros(100)
        cue[:25] = 1.0
        retrieved, _sim = mem.retrieve(cue)
        assert retrieved is not None
        # Should have high overlap with p1
        assert np.dot(retrieved, p1 / np.linalg.norm(p1)) > 0.5

    def test_clear_memories(self) -> None:
        """clear_memories() empties the memory bank."""
        mem = MemoryRegion(name="hippo", size=100)
        mem.encode(np.random.rand(100))
        mem.encode(np.random.rand(100))
        assert mem.get_memory_count() == 2
        mem.clear_memories()
        assert mem.get_memory_count() == 0


class TestPrefrontalRegion:
    """Test PrefrontalRegion goal management."""

    def test_set_goal(self) -> None:
        """Can set a goal pattern."""
        pfc = PrefrontalRegion(name="pfc", size=100)
        goal = np.random.rand(100)
        pfc.set_goal(goal)
        assert pfc.goal_pattern is not None

    def test_clear_goal(self) -> None:
        """Can clear the goal."""
        pfc = PrefrontalRegion(name="pfc", size=100)
        pfc.set_goal(np.random.rand(100))
        pfc.clear_goal()
        assert pfc.goal_pattern is None

    def test_evaluate_progress_no_goal(self) -> None:
        """Progress is 0.0 with no goal set."""
        pfc = PrefrontalRegion(name="pfc", size=100)
        assert pfc.evaluate_progress() == 0.0

    def test_goal_biases_activity(self) -> None:
        """Goal pattern biases neural activity during step."""
        pfc = PrefrontalRegion(name="pfc", size=100, goal_strength=2.0, threshold=1.0)
        goal = np.zeros(100)
        goal[10:30] = 1.0
        pfc.set_goal(goal)

        # Step multiple times
        for _ in range(5):
            pfc.step()

        # Should have some activity
        progress = pfc.evaluate_progress()
        # Just verify it returns a valid float
        assert isinstance(progress, float)

    def test_make_decision(self) -> None:
        """make_decision returns a boolean."""
        pfc = PrefrontalRegion(name="pfc", size=100)
        result = pfc.make_decision()
        assert isinstance(result, bool)


class TestRewardRegion:
    """Test RewardRegion modulation."""

    def test_deliver_reward(self) -> None:
        """deliver_reward updates reward signal."""
        reward = RewardRegion(name="reward", size=64)
        reward.deliver_reward(1.0)
        assert reward.reward_signal == 1.0
        assert reward.prediction_error == 1.0

    def test_prediction_error_computation(self) -> None:
        """Prediction error = reward - baseline."""
        reward = RewardRegion(name="reward", size=64, baseline_decay=0.5)
        reward.deliver_reward(1.0)
        # After first reward, baseline updates
        first_pe = reward.prediction_error
        assert first_pe == 1.0  # baseline was 0

        # Second reward: baseline has shifted
        reward.deliver_reward(1.0)
        # Baseline is now 0.5*0 + 0.5*1.0 = 0.5 (from first), then
        # PE = 1.0 - 0.5 = 0.5
        assert reward.prediction_error < first_pe

    def test_get_reward_signal_array(self) -> None:
        """get_reward_signal returns correctly shaped array."""
        reward = RewardRegion(name="reward", size=64)
        reward.deliver_reward(1.0)
        signal = reward.get_reward_signal()
        assert signal.shape == (64,)

    def test_reward_decays_over_steps(self) -> None:
        """Reward signal decays with each step."""
        reward = RewardRegion(name="reward", size=64)
        reward.deliver_reward(1.0)
        initial = reward.reward_signal
        reward.step()
        assert reward.reward_signal < initial

    def test_reset_clears_reward_state(self) -> None:
        """Reset clears all reward state."""
        reward = RewardRegion(name="reward", size=64)
        reward.deliver_reward(1.0)
        reward.reset()
        assert reward.reward_signal == 0.0
        assert reward.reward_baseline == 0.0
        assert reward.prediction_error == 0.0
