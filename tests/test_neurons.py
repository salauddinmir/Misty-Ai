"""
Tests for LIF Neuron Model.

Tests cover:
- Spike generation when threshold is reached
- Refractory period behavior (no firing during refractory)
- Membrane potential decay toward rest potential
- Threshold configuration
- Reset functionality
- Sub-threshold integration
"""

import pytest

from brain.neurons.lif import LIFNeuron


class TestLIFNeuronBasics:
    """Test basic neuron creation and properties."""

    def test_default_creation(self) -> None:
        """Neuron starts at rest potential with no refractory counter."""
        neuron = LIFNeuron()
        assert neuron.membrane_potential == 0.0
        assert neuron.threshold == 1.0
        assert neuron.rest_potential == 0.0
        assert neuron.refractory_counter == 0
        assert neuron.decay == 0.9

    def test_custom_parameters(self) -> None:
        """Neuron respects custom parameters."""
        neuron = LIFNeuron(
            threshold=2.0,
            rest_potential=-0.5,
            decay=0.8,
            refractory_period=5,
        )
        assert neuron.threshold == 2.0
        assert neuron.rest_potential == -0.5
        assert neuron.decay == 0.8
        assert neuron.refractory_period == 5

    def test_unique_ids(self) -> None:
        """Each neuron gets a unique ID."""
        n1 = LIFNeuron()
        n2 = LIFNeuron()
        assert n1.neuron_id != n2.neuron_id


class TestSpikeGeneration:
    """Test spike generation behavior."""

    def test_spike_at_threshold(self) -> None:
        """Neuron fires when input pushes potential to threshold."""
        neuron = LIFNeuron(threshold=1.0, decay=0.9)
        # Single large input should trigger spike
        fired = neuron.step(input_current=1.5)
        assert fired is True

    def test_no_spike_below_threshold(self) -> None:
        """Neuron does not fire if potential stays below threshold."""
        neuron = LIFNeuron(threshold=1.0, decay=0.9)
        fired = neuron.step(input_current=0.3)
        assert fired is False
        assert neuron.membrane_potential > 0.0

    def test_spike_from_accumulation(self) -> None:
        """Neuron fires after multiple sub-threshold inputs accumulate."""
        neuron = LIFNeuron(threshold=1.0, decay=0.95)
        # Repeated small inputs should eventually cause spike
        fired = False
        for _ in range(50):
            if neuron.step(input_current=0.3):
                fired = True
                break
        assert fired is True, "Neuron should fire from accumulated inputs"

    def test_spike_resets_potential(self) -> None:
        """After firing, membrane potential resets to rest."""
        neuron = LIFNeuron(threshold=1.0, rest_potential=0.0)
        neuron.step(input_current=1.5)  # Should fire
        assert neuron.membrane_potential == neuron.rest_potential

    def test_exact_threshold(self) -> None:
        """Neuron fires when potential exactly reaches threshold."""
        neuron = LIFNeuron(threshold=1.0, decay=1.0, rest_potential=0.0)
        # With decay=1.0 and rest=0.0, input goes directly to potential
        fired = neuron.step(input_current=1.0)
        assert fired is True


class TestRefractoryPeriod:
    """Test refractory period behavior."""

    def test_no_fire_during_refractory(self) -> None:
        """Neuron cannot fire during refractory period."""
        neuron = LIFNeuron(threshold=1.0, refractory_period=3)
        # Trigger a spike
        neuron.step(input_current=2.0)
        assert neuron.refractory_counter == 3

        # Try to fire during refractory - should not fire
        for _ in range(3):
            fired = neuron.step(input_current=5.0)
            assert fired is False

    def test_refractory_counter_decrements(self) -> None:
        """Refractory counter decreases each step."""
        neuron = LIFNeuron(threshold=1.0, refractory_period=3)
        neuron.step(input_current=2.0)  # Fire
        assert neuron.refractory_counter == 3

        neuron.step(0.0)
        assert neuron.refractory_counter == 2
        neuron.step(0.0)
        assert neuron.refractory_counter == 1
        neuron.step(0.0)
        assert neuron.refractory_counter == 0

    def test_can_fire_after_refractory(self) -> None:
        """Neuron can fire again once refractory period ends."""
        neuron = LIFNeuron(threshold=1.0, refractory_period=2)
        neuron.step(input_current=2.0)  # Fire

        # Wait out refractory
        neuron.step(0.0)
        neuron.step(0.0)

        # Should be able to fire again
        fired = neuron.step(input_current=2.0)
        assert fired is True

    def test_potential_at_rest_during_refractory(self) -> None:
        """Membrane potential stays at rest during refractory."""
        neuron = LIFNeuron(threshold=1.0, rest_potential=0.0, refractory_period=2)
        neuron.step(input_current=2.0)  # Fire

        neuron.step(input_current=5.0)  # High input during refractory
        assert neuron.membrane_potential == 0.0


class TestDecay:
    """Test membrane potential decay."""

    def test_decay_toward_rest(self) -> None:
        """Potential decays toward rest when no input is given."""
        neuron = LIFNeuron(threshold=1.0, decay=0.5, rest_potential=0.0)
        neuron.step(input_current=0.5)  # Set some potential
        initial_potential = neuron.membrane_potential

        neuron.step(input_current=0.0)  # No input, just decay
        assert neuron.membrane_potential < initial_potential
        assert neuron.membrane_potential >= 0.0

    def test_high_decay_preserves_potential(self) -> None:
        """High decay rate (close to 1) preserves more potential."""
        neuron_fast_decay = LIFNeuron(threshold=2.0, decay=0.5)
        neuron_slow_decay = LIFNeuron(threshold=2.0, decay=0.95)

        neuron_fast_decay.step(input_current=0.5)
        neuron_slow_decay.step(input_current=0.5)

        # After one more step with no input
        neuron_fast_decay.step(0.0)
        neuron_slow_decay.step(0.0)

        assert neuron_slow_decay.membrane_potential > neuron_fast_decay.membrane_potential

    def test_zero_decay_loses_all_potential(self) -> None:
        """Zero decay causes potential to return to rest immediately."""
        neuron = LIFNeuron(threshold=2.0, decay=0.0, rest_potential=0.0)
        neuron.step(input_current=0.5)
        # With decay=0.0, next step potential = 0.0 * (V - rest) + rest + input
        neuron.step(input_current=0.0)
        assert neuron.membrane_potential == 0.0


class TestReset:
    """Test neuron reset functionality."""

    def test_reset_clears_potential(self) -> None:
        """Reset returns potential to rest."""
        neuron = LIFNeuron(rest_potential=0.0)
        neuron.step(input_current=0.5)
        assert neuron.membrane_potential != 0.0
        neuron.reset()
        assert neuron.membrane_potential == 0.0

    def test_reset_clears_refractory(self) -> None:
        """Reset clears the refractory counter."""
        neuron = LIFNeuron(threshold=1.0, refractory_period=5)
        neuron.step(input_current=2.0)  # Fire
        assert neuron.refractory_counter == 5
        neuron.reset()
        assert neuron.refractory_counter == 0
