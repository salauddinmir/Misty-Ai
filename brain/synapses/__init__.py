"""Synapse models and plasticity rules for neural connections."""

from brain.synapses.synapse import Synapse
from brain.synapses.stdp import STDPRule
from brain.synapses.plasticity import PlasticityManager

__all__ = ["Synapse", "STDPRule", "PlasticityManager"]
