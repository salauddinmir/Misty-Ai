"""Synapse models and plasticity rules for neural connections."""

from brain.synapses.plasticity import PlasticityManager
from brain.synapses.stdp import STDPRule
from brain.synapses.synapse import Synapse

__all__ = ["PlasticityManager", "STDPRule", "Synapse"]
