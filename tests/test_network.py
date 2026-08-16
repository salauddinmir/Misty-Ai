"""
Tests for Synaptic Network and Simulation Engine.

Tests cover:
- SynapticNetwork creation and connection
- Sparse matrix propagation
- Excitatory/inhibitory sign enforcement
- Self-connections (recurrent)
- SimulationEngine multi-region simulation
"""

import numpy as np
import pytest

from brain.neurons.vectorized import VectorizedPopulation, NeuronType
from brain.synapses.network import SynapticNetwork, ConnectionInfo
from brain.regions.sensory import SensoryRegion
from brain.regions.association import AssociationRegion
from brain.simulation.engine import SimulationEngine
from brain.simulation.config import SimulationConfig
from brain.simulation.recorder import SpikeRecorder


class TestSynapticNetworkCreation:
    """Test SynapticNetwork initialization and registration."""

    def test_empty_network(self) -> None:
        """Can create empty network."""
        net = SynapticNetwork()
        assert len(net.populations) == 0
        assert len(net.connections) == 0
        assert net.total_synapses == 0

    def test_add_population(self) -> None:
        """Can register populations."""
        net = SynapticNetwork()
        pop = VectorizedPopulation(size=100, name="test_pop")
        net.add_population(pop)
        assert "test_pop" in net.populations

    def test_duplicate_population_raises(self) -> None:
        """Adding duplicate population name raises ValueError."""
        net = SynapticNetwork()
        pop1 = VectorizedPopulation(size=100, name="same_name")
        pop2 = VectorizedPopulation(size=50, name="same_name")
        net.add_population(pop1)
        with pytest.raises(ValueError):
            net.add_population(pop2)


class TestConnectionCreation:
    """Test connection creation between populations."""

    def test_connect_populations(self) -> None:
        """connect_populations creates a sparse weight matrix."""
        net = SynapticNetwork()
        source = VectorizedPopulation(size=100, name="source")
        target = VectorizedPopulation(size=50, name="target")
        conn = net.connect_populations(source, target, probability=0.2, seed=42)
        assert conn.source_name == "source"
        assert conn.target_name == "target"
        assert conn.weight_matrix.shape == (50, 100)
        assert conn.weight_matrix.nnz > 0

    def test_connection_sparsity(self) -> None:
        """Connection density roughly matches probability."""
        net = SynapticNetwork()
        source = VectorizedPopulation(size=200, name="src")
        target = VectorizedPopulation(size=200, name="tgt")
        prob = 0.1
        conn = net.connect_populations(source, target, probability=prob, seed=42)
        # Expected connections: 200*200*0.1 = 4000
        actual = conn.weight_matrix.nnz
        expected = 200 * 200 * prob
        # Allow 20% tolerance
        assert abs(actual - expected) < expected * 0.2

    def test_excitatory_positive_weights(self) -> None:
        """Excitatory source neurons produce positive weights."""
        net = SynapticNetwork()
        source = VectorizedPopulation(size=10, name="exc_src", excitatory_ratio=1.0)
        target = VectorizedPopulation(size=10, name="tgt1")
        conn = net.connect_populations(
            source, target, probability=1.0, weight_range=(0.1, 0.5), seed=42
        )
        # All weights should be positive
        weights = conn.weight_matrix.toarray()
        nonzero = weights[weights != 0]
        assert np.all(nonzero > 0)

    def test_inhibitory_negative_weights(self) -> None:
        """Inhibitory source neurons produce negative weights."""
        net = SynapticNetwork()
        source = VectorizedPopulation(size=10, name="inh_src", excitatory_ratio=0.0)
        target = VectorizedPopulation(size=10, name="tgt2")
        conn = net.connect_populations(
            source, target, probability=1.0, weight_range=(0.1, 0.5), seed=42
        )
        # All weights should be negative (inhibitory source)
        weights = conn.weight_matrix.toarray()
        nonzero = weights[weights != 0]
        assert np.all(nonzero < 0)

    def test_mixed_population_weights(self) -> None:
        """Mixed population produces both positive and negative weights."""
        net = SynapticNetwork()
        source = VectorizedPopulation(size=100, name="mixed_src", excitatory_ratio=0.5)
        target = VectorizedPopulation(size=50, name="tgt3")
        conn = net.connect_populations(
            source, target, probability=0.5, weight_range=(0.1, 0.3), seed=42
        )
        weights = conn.weight_matrix.toarray()
        nonzero = weights[weights != 0]
        assert np.any(nonzero > 0), "Should have positive weights from excitatory"
        assert np.any(nonzero < 0), "Should have negative weights from inhibitory"

    def test_connect_self(self) -> None:
        """Self-connections create a square matrix."""
        net = SynapticNetwork()
        pop = VectorizedPopulation(size=100, name="recurrent")
        conn = net.connect_self(pop, probability=0.1, seed=42)
        assert conn.weight_matrix.shape == (100, 100)
        assert conn.source_name == "recurrent"
        assert conn.target_name == "recurrent"

    def test_connect_self_no_autapse(self) -> None:
        """Self-connections without autapses have zero diagonal."""
        net = SynapticNetwork()
        pop = VectorizedPopulation(size=50, name="no_autapse")
        conn = net.connect_self(pop, probability=0.5, allow_autapse=False, seed=42)
        diagonal = conn.weight_matrix.toarray().diagonal()
        assert np.all(diagonal == 0)

    def test_connect_self_with_autapse(self) -> None:
        """Self-connections with autapses may have non-zero diagonal."""
        net = SynapticNetwork()
        pop = VectorizedPopulation(size=50, name="with_autapse")
        conn = net.connect_self(pop, probability=0.9, allow_autapse=True, seed=42)
        diagonal = conn.weight_matrix.toarray().diagonal()
        # With 90% probability, most should be non-zero
        assert np.sum(diagonal != 0) > 0


class TestSpikePropagation:
    """Test spike propagation through the network."""

    def test_propagate_basic(self) -> None:
        """Spikes propagate through connections correctly."""
        net = SynapticNetwork()
        source = VectorizedPopulation(size=10, name="prop_src", excitatory_ratio=1.0)
        target = VectorizedPopulation(size=10, name="prop_tgt")
        net.connect_populations(
            source, target, probability=1.0, weight_range=(0.5, 0.5), seed=42
        )

        # All source neurons fire
        spikes = np.ones(10, dtype=bool)
        currents = net.propagate(source, target, spikes)
        assert currents.shape == (10,)
        # Should have positive currents (excitatory source, full connectivity)
        assert np.all(currents > 0)

    def test_propagate_no_spikes_no_current(self) -> None:
        """No spikes produces zero current."""
        net = SynapticNetwork()
        source = VectorizedPopulation(size=10, name="no_spike_src")
        target = VectorizedPopulation(size=10, name="no_spike_tgt")
        net.connect_populations(source, target, probability=1.0, seed=42)

        spikes = np.zeros(10, dtype=bool)
        currents = net.propagate(source, target, spikes)
        assert np.all(currents == 0.0)

    def test_propagate_all(self) -> None:
        """propagate_all processes all connections."""
        net = SynapticNetwork()
        p1 = VectorizedPopulation(size=10, name="region_a", excitatory_ratio=1.0)
        p2 = VectorizedPopulation(size=10, name="region_b")
        net.connect_populations(p1, p2, probability=1.0, weight_range=(0.1, 0.1), seed=42)

        spike_dict = {
            "region_a": np.ones(10, dtype=bool),
            "region_b": np.zeros(10, dtype=bool),
        }
        currents = net.propagate_all(spike_dict)
        assert "region_a" in currents
        assert "region_b" in currents
        # region_b should receive current from region_a spikes
        assert np.sum(currents["region_b"]) > 0
        # region_a should receive nothing (no connection from b to a)
        assert np.all(currents["region_a"] == 0.0)


class TestSimulationEngine:
    """Test SimulationEngine orchestration."""

    def test_engine_creation(self) -> None:
        """Can create a simulation engine."""
        s = SensoryRegion(name="s_eng", size=50)
        a = AssociationRegion(name="a_eng", size=50)
        net = SynapticNetwork()
        net.connect_populations(s.population, a.population, probability=0.1, seed=42)
        engine = SimulationEngine([s, a], net)
        assert engine.current_step == 0

    def test_engine_step(self) -> None:
        """Engine step advances all regions."""
        s = SensoryRegion(name="s_step", size=50)
        a = AssociationRegion(name="a_step", size=50)
        net = SynapticNetwork()
        net.connect_populations(s.population, a.population, probability=0.1, seed=42)
        engine = SimulationEngine([s, a], net)

        # Inject input to sensory
        s.encode_input(np.ones(50))
        result = engine.step()
        assert engine.current_step == 1
        assert "s_step" in result
        assert "a_step" in result

    def test_engine_run_multiple_steps(self) -> None:
        """Engine.run() executes multiple steps."""
        s = SensoryRegion(name="s_run", size=50)
        a = AssociationRegion(name="a_run", size=50)
        net = SynapticNetwork()
        net.connect_populations(s.population, a.population, probability=0.1, seed=42)
        engine = SimulationEngine([s, a], net)
        engine.run(100)
        assert engine.current_step == 100

    def test_engine_records_spikes(self) -> None:
        """Engine records spikes when configured."""
        s = SensoryRegion(name="s_rec", size=50)
        a = AssociationRegion(name="a_rec", size=50)
        net = SynapticNetwork()
        net.connect_populations(s.population, a.population, probability=0.1, seed=42)
        config = SimulationConfig(record_spikes=True)
        engine = SimulationEngine([s, a], net, config)

        s.encode_input(np.ones(50) * 2.0)
        engine.run(10)

        # Recorder should have data
        assert "s_rec" in engine.recorder.spike_trains

    def test_engine_inject_current(self) -> None:
        """Can inject external current into a region."""
        s = SensoryRegion(name="s_inj", size=50)
        net = SynapticNetwork()
        net.add_population(s.population)
        engine = SimulationEngine([s], net)

        engine.inject_current("s_inj", np.full(50, 2.0))
        result = engine.step()
        # Should have some spikes from injected current
        assert np.sum(result["s_inj"]) > 0

    def test_engine_inject_invalid_region_raises(self) -> None:
        """Injecting into non-existent region raises ValueError."""
        s = SensoryRegion(name="s_err", size=50)
        net = SynapticNetwork()
        net.add_population(s.population)
        engine = SimulationEngine([s], net)

        with pytest.raises(ValueError):
            engine.inject_current("nonexistent", np.zeros(50))

    def test_engine_reset(self) -> None:
        """Engine reset clears all state."""
        s = SensoryRegion(name="s_rst", size=50)
        net = SynapticNetwork()
        net.add_population(s.population)
        engine = SimulationEngine([s], net)
        engine.run(10)
        assert engine.current_step == 10
        engine.reset()
        assert engine.current_step == 0

    def test_engine_get_state(self) -> None:
        """Engine get_state returns region info."""
        s = SensoryRegion(name="s_state", size=50)
        net = SynapticNetwork()
        net.add_population(s.population)
        engine = SimulationEngine([s], net)
        state = engine.get_state()
        assert "s_state" in state
        assert "size" in state["s_state"]
        assert "firing_rate" in state["s_state"]


class TestSpikeRecorder:
    """Test SpikeRecorder functionality."""

    def test_add_and_retrieve_spikes(self) -> None:
        """Can record and retrieve spike trains."""
        recorder = SpikeRecorder()
        spikes = np.array([True, False, True, False, True])
        recorder.add_spikes("test_region", 0, spikes)
        train = recorder.get_spike_train("test_region")
        assert train is not None
        assert train.shape == (1, 5)
        np.testing.assert_array_equal(train[0], spikes)

    def test_firing_rate_computation(self) -> None:
        """Firing rate is computed correctly."""
        recorder = SpikeRecorder()
        # Add 100% firing
        recorder.add_spikes("r1", 0, np.ones(10, dtype=bool))
        assert recorder.get_firing_rate("r1") == 1.0

        # Add 0% firing
        recorder.add_spikes("r1", 1, np.zeros(10, dtype=bool))
        assert recorder.get_firing_rate("r1", window=2) == 0.5

    def test_get_history(self) -> None:
        """get_history returns recent spike arrays."""
        recorder = SpikeRecorder()
        for t in range(20):
            spikes = np.random.rand(10) > 0.5
            recorder.add_spikes("r2", t, spikes)
        history = recorder.get_history("r2", last_n_steps=5)
        assert history is not None
        assert history.shape == (5, 10)

    def test_unknown_region_returns_none(self) -> None:
        """Querying unknown region returns None."""
        recorder = SpikeRecorder()
        assert recorder.get_spike_train("unknown") is None
        assert recorder.get_firing_rate("unknown") == 0.0

    def test_reset(self) -> None:
        """Reset clears all recorded data."""
        recorder = SpikeRecorder()
        recorder.add_spikes("r3", 0, np.ones(5, dtype=bool))
        recorder.reset()
        assert recorder.get_spike_train("r3") is None
        assert recorder.total_timesteps == 0
