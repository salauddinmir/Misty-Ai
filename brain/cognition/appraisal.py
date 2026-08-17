"""Deterministic appraisal and motivational drive computation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from brain.cognition.perception import Percept
from brain.emotion.state import EmotionalState


@dataclass(frozen=True)
class DrivePriority:
    """Inspectable priority for the next cognitive action."""

    name: str
    value: float
    reason: str

    def to_dict(self) -> Dict[str, object]:
        return {"name": self.name, "value": round(self.value, 3), "reason": self.reason}


class AppraisalEngine:
    """Map cognitive appraisal signals into bounded affective drives."""

    def appraise(
        self,
        percept: Percept,
        emotion: EmotionalState,
        *,
        prediction_error: float = 0.0,
    ) -> list[DrivePriority]:
        novelty_drive = percept.novelty * 0.45
        answer_drive = percept.question_demand * 0.55
        safety_drive = percept.urgency * 0.8
        repair_drive = min(1.0, prediction_error) * 0.7

        emotion.update_curiosity(novelty_drive * 0.08)
        emotion.interest = emotion._clamp(emotion.interest + novelty_drive * 0.06)
        emotion.attention = emotion._clamp(emotion.attention + max(percept.attention_weight, safety_drive) * 0.08)
        emotion.urgency = emotion._clamp(emotion.urgency + safety_drive * 0.06)
        emotion.uncertainty = emotion._clamp(emotion.uncertainty + repair_drive * 0.05)

        priorities = [
            DrivePriority("answer", answer_drive, "epistemic demand from the percept"),
            DrivePriority("explore", novelty_drive, "novelty exceeds baseline"),
            DrivePriority("protect", safety_drive, "urgent or risk-related signal"),
            DrivePriority("repair", repair_drive, "prediction error requires model revision"),
        ]
        return sorted(priorities, key=lambda item: item.value, reverse=True)
