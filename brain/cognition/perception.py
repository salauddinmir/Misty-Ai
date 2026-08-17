"""Deterministic perception and attention primitives."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict

from brain.cognition.workspace import CognitiveEvent

_URGENT_TERMS = re.compile(r"জরুরি|তাড়াতাড়ি|বিপদ|urgent|asap|emergency|help", re.IGNORECASE)
_QUESTION_TERMS = re.compile(r"\?|কী|কি|কেন|কিভাবে|কীভাবে|কে|where|what|why|how|who", re.IGNORECASE)


@dataclass(frozen=True)
class Percept:
    """A scored percept selected for the current cognitive cycle."""

    event: CognitiveEvent
    novelty: float
    urgency: float
    question_demand: float
    attention_weight: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event": self.event.to_dict(),
            "novelty": self.novelty,
            "urgency": self.urgency,
            "question_demand": self.question_demand,
            "attention_weight": self.attention_weight,
        }


class PerceptionPipeline:
    """Convert raw input into an inspectable, attention-ranked percept."""

    def perceive(self, text: str, *, source: str = "text") -> Percept:
        normalized = " ".join(text.split())
        length_signal = min(1.0, len(normalized) / 160.0)
        question_demand = 0.8 if _QUESTION_TERMS.search(normalized) else 0.2
        urgency = 0.9 if _URGENT_TERMS.search(normalized) else 0.1
        novelty = min(1.0, 0.35 + length_signal * 0.35 + (0.2 if source != "text" else 0.0))
        salience = min(1.0, 0.35 * novelty + 0.4 * question_demand + 0.25 * urgency)
        event = CognitiveEvent(
            content=normalized,
            source=source,
            event_type="utterance" if source == "text" else "sensor_percept",
            salience=salience,
            reliability=0.9 if source == "text" else 0.75,
            metadata={
                "normalized_length": len(normalized),
                "question_signal": question_demand,
                "urgency_signal": urgency,
            },
        )
        return Percept(
            event=event,
            novelty=novelty,
            urgency=urgency,
            question_demand=question_demand,
            attention_weight=salience,
        )
