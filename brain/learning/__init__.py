"""Learning systems: reinforcement learning, reward signals, and memory consolidation."""

from brain.learning.consolidation import MemoryConsolidator
from brain.learning.induction import EvidenceGatedInducer, LearningCandidate
from brain.learning.reinforcement import ReinforcementLearner
from brain.learning.reward import RewardSignal

__all__ = [
    "EvidenceGatedInducer",
    "LearningCandidate",
    "MemoryConsolidator",
    "ReinforcementLearner",
    "RewardSignal",
]
