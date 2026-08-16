"""
Simulation Module.

Provides the network simulation engine that orchestrates multiple
brain regions, processes synaptic transmission, applies plasticity
rules, and records spike history.
"""

from brain.simulation.config import SimulationConfig
from brain.simulation.engine import SimulationEngine
from brain.simulation.recorder import SpikeRecorder

__all__ = ["SimulationConfig", "SimulationEngine", "SpikeRecorder"]
