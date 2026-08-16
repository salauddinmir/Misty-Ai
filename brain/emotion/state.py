"""
Emotional State.

Internal states that influence cognitive processing:
curiosity, confidence, uncertainty, attention, urgency,
satisfaction, frustration, and interest.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class EmotionalState:
    """Internal emotional/motivational state of the brain.

    All values are floats between 0.0 and 1.0.
    """

    curiosity: float = 0.5
    confidence: float = 0.5
    uncertainty: float = 0.3
    attention: float = 0.5
    urgency: float = 0.3
    satisfaction: float = 0.5
    frustration: float = 0.0
    interest: float = 0.5

    def _clamp(self, value: float) -> float:
        """Clamp a value between 0.0 and 1.0."""
        return max(0.0, min(1.0, value))

    def update_curiosity(self, delta: float) -> None:
        """Adjust curiosity level."""
        self.curiosity = self._clamp(self.curiosity + delta)

    def update_confidence(self, delta: float) -> None:
        """Adjust confidence level."""
        self.confidence = self._clamp(self.confidence + delta)

    def update_from_outcome(self, success: bool, novelty: float = 0.0) -> None:
        """Update emotional state based on action outcome."""
        if success:
            self.satisfaction = self._clamp(self.satisfaction + 0.2)
            self.confidence = self._clamp(self.confidence + 0.1)
            self.frustration = self._clamp(self.frustration - 0.2)
        else:
            self.frustration = self._clamp(self.frustration + 0.2)
            self.confidence = self._clamp(self.confidence - 0.1)
            self.satisfaction = self._clamp(self.satisfaction - 0.1)

        self.curiosity = self._clamp(self.curiosity + novelty * 0.3)
        self.interest = self._clamp(self.interest + novelty * 0.2)

    def update_from_input(self, is_question: bool = False, is_new_info: bool = False) -> None:
        """Update state when receiving new input."""
        if is_question:
            self.urgency = self._clamp(self.urgency + 0.3)
            self.attention = self._clamp(self.attention + 0.2)

        if is_new_info:
            self.curiosity = self._clamp(self.curiosity + 0.1)
            self.interest = self._clamp(self.interest + 0.2)
            self.uncertainty = self._clamp(self.uncertainty - 0.1)

    def decay(self, rate: float = 0.95) -> None:
        """Apply temporal decay - emotions return toward baseline."""
        baseline = 0.5
        self.curiosity += (baseline - self.curiosity) * (1 - rate)
        self.attention += (baseline - self.attention) * (1 - rate)
        self.urgency += (0.3 - self.urgency) * (1 - rate)
        self.satisfaction += (baseline - self.satisfaction) * (1 - rate)
        self.frustration += (0.0 - self.frustration) * (1 - rate)
        self.interest += (baseline - self.interest) * (1 - rate)

    def to_dict(self) -> Dict[str, float]:
        """Convert emotional state to a dictionary."""
        return {
            "curiosity": round(self.curiosity, 3),
            "confidence": round(self.confidence, 3),
            "uncertainty": round(self.uncertainty, 3),
            "attention": round(self.attention, 3),
            "urgency": round(self.urgency, 3),
            "satisfaction": round(self.satisfaction, 3),
            "frustration": round(self.frustration, 3),
            "interest": round(self.interest, 3),
        }

    def __repr__(self) -> str:
        return (
            f"EmotionalState(curiosity={self.curiosity:.2f}, "
            f"confidence={self.confidence:.2f}, attention={self.attention:.2f})"
        )
