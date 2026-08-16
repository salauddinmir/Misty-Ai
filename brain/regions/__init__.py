"""
Brain Regions Module.

Provides specialized neuron groups that wrap VectorizedPopulations
with domain-specific behavior for sensory processing, association,
memory, executive control, and reward signaling.
"""

from brain.regions.region import BrainRegion
from brain.regions.sensory import SensoryRegion
from brain.regions.association import AssociationRegion
from brain.regions.memory_region import MemoryRegion
from brain.regions.prefrontal import PrefrontalRegion
from brain.regions.reward_region import RewardRegion

__all__ = [
    "BrainRegion",
    "SensoryRegion",
    "AssociationRegion",
    "MemoryRegion",
    "PrefrontalRegion",
    "RewardRegion",
]
