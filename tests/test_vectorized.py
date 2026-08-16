"""
Tests for Vectorized Neuron Population.

Tests cover:
- Basic creation and parameter initialization
- Spike generation with vectorized LIF dynamics
- Refractory period behavior
- Excitatory/inhibitory neuron types and ratios
- Large population simulation (1000+ neurons)
- Signed output (excitatory positive, inhibitory negative)
- Reset functionality
- Performance with large populations
"""

import time

import numpy as np
import pytest

from brain.neurons.vectorized import VectorizedPopulation, NeuronType
from brain.neurons.lif import LIFNeuron


class TestVectorizedCreation:
    """Test population creation and initialization."""

    def test_default_creation(self) -> None:
        """Population creates with correct defaults."""
        pop = VectorizedPopulation(size=100)
        assert pop.size == 100
        assert pop.name == "population"
        assert pop.threshold_val == 1.0
        assert pop.decay_val == 0.9
        assert pop.rest_potential_val == 0.0
        assert pop.refractory_period_val == 2

    def test_custom_parameters(self) -> None:
        """Population respects custom parameters."""
        pop = VectorizedPopulation(
            name="test_pop",
            size=500,
            threshold_val=2.0,
            decay_val=0.8,
            rest_potential_val=-0.5,
            refractory_period_val=3,
            excitatory_ratio=0.7,
        )
        assert pop.name == "test_pop"
        assert pop.size == 500
        assert pop.threshold_val == 2.0
        assert pop.decay_val == 0.8

    def test_initial_membrane_at_rest(self) -> None:
        """All membrane potentials start at rest potential."""
        pop = VectorizedPopulation(size=100, rest_potential_val=-0.5)
        assert np.all(pop.membrane_potential == -0.5)

    def test_initial_no_spikes(self) -> None:
        """No spikes from a fresh population with zero input."""
        pop = VectorizedPopulation(size=100)
        spikes = pop.step(np.zeros(100))
        # With zero input, no neuron should fire
        assert not np.any(spikes)


class TestExcitatoryInhibitory:
    """Test excitatory/inhibitory neuron type assignment."""

    def test_default_ratio(self) -> None:
        """Default ratio is 80% excitatory, 20% inhibitory."""
        pop = VectorizedPopulation(size=1000)
        assert pop.excitatory_count == 800
        assert pop.inhibitory_count == 200

    def test_custom_ratio(self) -> None:
        """Custom excitatory ratio is respected."""
        pop = VectorizedPopulation(size=100, excitatory_ratio=0.6)
        assert pop.excitatory_count == 60
        assert pop.inhibitory_count == 40

    def test_all_excitatory(self) -> None:
        """Can create fully excitatory population."""
        pop = VectorizedPopulation(size=100, excitatory_ratio=1.0)
        assert pop.excitatory_count == 100
        assert pop.inhibitory_count == 0

    def test_neuron_type_values(self) -> None:
        """Neuron types have correct numeric values."""
        pop = VectorizedPopulation(size=10, excitatory_ratio=0.5)
        types = pop.type_array
        # First 5 excitatory (+1), last 5 inhibitory (-1)
        assert np.all(types[:5] == NeuronType.EXCITATORY)
        assert np.all(types[5:] == NeuronType.INHIBITORY)


class TestSpikeGeneration:
    """Test spike generation matches LIF dynamics."""

    def test_spike_at_threshold(self) -> None:
        """Neurons fire when input pushes potential to threshold."""
        pop = VectorizedPopulation(size=10, threshold_val=1.0, decay_val=0.9)
        inputs = np.full(10, 1.5)
        spikes = pop.step(inputs)
        assert np.all(spikes)

    def test_no_spike_below_threshold(self) -> None:
        """Neurons do not fire if potential stays below threshold."""
        pop = VectorizedPopulation(size=10, threshold_val=1.0, decay_val=0.9)
        inputs = np.full(10, 0.3)
        spikes = pop.step(inputs)
        assert not np.any(spikes)
        assert np.all(pop.membrane_potential > 0.0)

    def test_spike_from_accumulation(self) -> None:
        """Neurons fire after multiple sub-threshold inputs accumulate."""
        pop = VectorizedPopulation(size=10, threshold_val=1.0, decay_val=0.95)
        inputs = np.full(10, 0.3)
        fired = False
        for _ in range(50):
            spikes = pop.step(inputs)
            if np.any(spikes):
                fired = True
                break
        assert fired, "Neurons should fire from accumulated inputs"

    def test_selective_firing(self) -> None:
        """Only neurons receiving sufficient input fire."""
        pop = VectorizedPopulation(size=10, threshold_val=1.0, decay_val=0.9)
        inputs = np.zeros(10)
        inputs[0:3] = 1.5
        spikes = pop.step(inputs)
        assert np.all(spikes[:3])
        assert not np.any(spikes[3:])

    def test_matches_scalar_lif_dynamics(self) -> None:
        """Vectorized dynamics match individual LIFNeuron behavior."""
        lif = LIFNeuron(threshold=1.0, decay=0.9, rest_potential=0.0, refractory_period=2)
        pop = VectorizedPopulation(
            size=1, threshold_val=1.0, decay_val=0.9,
            rest_potential_val=0.0, refractory_period_val=2
        )

        test_inputs = [0.3, 0.4, 0.5, 1.5, 0.0, 0.0, 1.2, 0.8, 0.0, 2.0]
        for current in test_inputs:
            lif_spike = lif.step(current)
            pop_spikes = pop.step(np.array([current]))
            assert lif_spike == pop_spikes[0], (
                f"Mismatch at input={current}: LIF={lif_spike}, Vec={pop_spikes[0]}"
            )


class TestRefractoryPeriod:
    """Test refractory period behavior."""

    def test_no_fire_during_refractory(self) -> None:
        """Neurons cannot fire during refractory period."""
        pop = VectorizedPopulation(size=5, threshold_val=1.0, refractory_period_val=3)
        pop.step(np.full(5, 2.0))
        assert np.all(pop.refractory_counter == 3)

        for _ in range(3):
            spikes = pop.step(np.full(5, 5.0))
            assert not np.any(spikes)

    def test_can_fire_after_refractory(self) -> None:
        """Neurons can fire again once refractory period ends."""
        pop = VectorizedPopulation(size=1, threshold_val=1.0, refractory_period_val=2)
        pop.step(np.array([2.0]))  # Fire
        pop.step(np.array([0.0]))  # Refractory
        pop.step(np.array([0.0]))  # Refractory done
        spikes = pop.step(np.array([2.0]))
        assert spikes[0]

    def test_potential_at_rest_during_refractory(self) -> None:
        """Membrane potential stays at rest during refractory."""
        pop = VectorizedPopulation(
            size=1, threshold_val=1.0, rest_potential_val=0.0, refractory_period_val=2
        )
        pop.step(np.array([2.0]))  # Fire
        pop.step(np.array([5.0]))  # High input during refractory
        assert pop.membrane_potential[0] == 0.0


class TestSignedOutput:
    """Test signed output from excitatory/inhibitory neurons."""

    def test_excitatory_positive_output(self) -> None:
        """Excitatory neurons produce +1 when firing."""
        pop = VectorizedPopulation(size=10, excitatory_ratio=1.0, threshold_val=1.0)
        spikes = pop.step(np.full(10, 2.0))
        output = pop.get_output(spikes)
        assert np.all(output == 1.0)

    def test_inhibitory_negative_output(self) -> None:
        """Inhibitory neurons produce -1 when firing."""
        pop = VectorizedPopulation(size=10, excitatory_ratio=0.0, threshold_val=1.0)
        spikes = pop.step(np.full(10, 2.0))
        output = pop.get_output(spikes)
        assert np.all(output == -1.0)

    def test_mixed_output(self) -> None:
        """Mixed population produces correct signed output."""
        pop = VectorizedPopulation(size=10, excitatory_ratio=0.5, threshold_val=1.0)
        spikes = pop.step(np.full(10, 2.0))
        output = pop.get_output(spikes)
        assert np.all(output[:5] == 1.0)
        assert np.all(output[5:] == -1.0)

    def test_non_firing_zero_output(self) -> None:
        """Non-firing neurons produce 0 output."""
        pop = VectorizedPopulation(size=10, excitatory_ratio=0.5, threshold_val=1.0)
        spikes = pop.step(np.full(10, 0.1))
        output = pop.get_output(spikes)
        assert np.all(output == 0.0)


class TestLargePopulation:
    """Test performance and correctness with large populations."""

    def test_1000_neurons(self) -> None:
        """Can simulate 1000 neurons."""
        pop = VectorizedPopulation(size=1000, threshold_val=1.0, decay_val=0.9)
        inputs = np.random.uniform(0.0, 2.0, size=1000)
        spikes = pop.step(inputs)
        assert spikes.shape == (1000,)
        assert np.sum(spikes) > 0

    def test_10000_neurons(self) -> None:
        """Can simulate 10000 neurons."""
        pop = VectorizedPopulation(size=10000, threshold_val=1.0, decay_val=0.9)
        inputs = np.random.uniform(0.0, 2.0, size=10000)
        spikes = pop.step(inputs)
        assert spikes.shape == (10000,)
        assert np.sum(spikes) > 0

    def test_performance_10000_neurons(self) -> None:
        """10000 neurons simulate quickly (< 10ms per step)."""
        pop = VectorizedPopulation(size=10000, threshold_val=1.0, decay_val=0.9)
        inputs = np.random.uniform(0.0, 1.5, size=10000)

        # Warm up
        pop.step(inputs)
        pop.reset()

        # Time 100 steps
        start = time.time()
        for _ in range(100):
            pop.step(inputs)
        elapsed = time.time() - start

        # 100 steps should take < 1 second (10ms per step target)
        assert elapsed < 1.0, f"Too slow: {elapsed:.3f}s for 100 steps"


class TestReset:
    """Test reset functionality."""

    def test_reset_clears_potential(self) -> None:
        """Reset returns all potentials to rest."""
        pop = VectorizedPopulation(size=100, rest_potential_val=0.0)
        pop.step(np.full(100, 0.5))
        assert np.any(pop.membrane_potential != 0.0)
        pop.reset()
        assert np.all(pop.membrane_potential == 0.0)

    def test_reset_clears_refractory(self) -> None:
        """Reset clears all refractory counters."""
        pop = VectorizedPopulation(size=100, threshold_val=1.0, refractory_period_val=5)
        pop.step(np.full(100, 2.0))
        assert np.all(pop.refractory_counter == 5)
        pop.reset()
        assert np.all(pop.refractory_counter == 0)
