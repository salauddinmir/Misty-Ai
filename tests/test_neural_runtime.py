"""
Tests for the neural simulation runtime (Phase 1 merge).

Exercises use_neural_sim=True end-to-end: brain regions, concept
encoding, spike propagation through the synaptic network, and the
associate/act paths of the cognitive cycle.
"""

import numpy as np

from brain.core.brain import Brain
from brain.encoding.concept_encoder import ConceptEncoder
from brain.regions.association import AssociationRegion
from brain.regions.memory_region import MemoryRegion
from brain.regions.sensory import SensoryRegion
from brain.simulation.config import SimulationConfig
from brain.simulation.engine import SimulationEngine
from brain.synapses.network import SynapticNetwork


class TestBrainRegions:
    """Each brain region must initialize and step its vectorized population."""

    def test_sensory_region_step(self):
        region = SensoryRegion(name="sensory", size=256, gain=2.0)
        region.encode_input(np.ones(256))
        spikes = region.step()
        assert spikes is not None
        assert len(spikes) == 256

    def test_association_region(self):
        region = AssociationRegion(name="association", size=512)
        assert region is not None

    def test_memory_region_store_and_retrieve(self):
        region = MemoryRegion(name="memory", size=512)
        pattern = np.random.binomial(1, 0.1, size=(1, 512))
        idx = region.encode(pattern, label="test")
        assert idx is not None
        retrieved, score = region.retrieve(cue=pattern)
        assert retrieved is not None
        assert score >= 0.0


class TestConceptEncoder:
    """Concepts must encode to valid, deterministic spike patterns."""

    def test_encodes_concept_id(self):
        encoder = ConceptEncoder()
        pattern = encoder.encode_concept("test-concept")
        assert pattern.size > 0
        assert np.any(pattern)

    def test_deterministic(self):
        encoder = ConceptEncoder()
        a = encoder.encode_concept("abc")
        b = encoder.encode_concept("abc")
        np.testing.assert_array_equal(a, b)

    def test_different_concepts_differ(self):
        encoder = ConceptEncoder()
        a = encoder.encode_concept("alpha")
        b = encoder.encode_concept("beta")
        assert not np.array_equal(a, b)


class TestSimulationEngine:
    """The simulation engine must step connected regions without error."""

    def _make_engine(self):
        sensory = SensoryRegion(name="sensory", size=256, gain=2.0)
        association = AssociationRegion(name="association", size=512)
        memory = MemoryRegion(name="memory", size=512)
        network = SynapticNetwork()
        network.connect_populations(sensory.population, association.population, probability=0.15)
        network.connect_populations(association.population, memory.population, probability=0.15)
        config = SimulationConfig(total_time=20, record_spikes=True)
        return SimulationEngine(regions=[sensory, association, memory], network=network, config=config)

    def test_step_runs(self):
        engine = self._make_engine()
        engine.step()
        assert engine.current_step == 1

    def test_run_multiple_steps(self):
        engine = self._make_engine()
        engine.run(4)
        assert engine.current_step == 4

    def test_recorder_captures_spikes(self):
        engine = self._make_engine()
        engine.run(10)
        assert len(engine.recorder.recorded_regions) > 0


class TestBrainWithNeuralSim:
    """Brain(use_neural_sim=True) must run a full cognitive cycle."""

    def test_init_neural_mode(self):
        brain = Brain(use_neural_sim=True)
        assert brain.use_neural_sim is True
        assert brain._neural_sim_engine is not None

    def test_process_greeting(self):
        brain = Brain(use_neural_sim=True)
        result = brain.process("Hello")
        assert result["response"]

    def test_process_name_declaration(self):
        brain = Brain(use_neural_sim=True)
        brain.process("আমার নাম Neuro")
        assert "Neuro" in brain.user_name or brain.concept_graph.num_concepts > 0

    def test_graph_fallback_when_no_target(self):
        # Inputs with no target entity should gracefully skip neural encode
        brain = Brain(use_neural_sim=True)
        result = brain.process("ভালো আছো?")
        assert result["response"]

    def test_learn_cycle_stores_episode(self):
        brain = Brain(use_neural_sim=True)
        brain.process("আমার নাম Salauddin")
        assert brain.episodic_memory.size > 0
