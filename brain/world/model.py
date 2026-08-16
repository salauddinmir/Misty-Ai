"""
World Model — structured representation of the environment and
next-intent prediction.

This module gives MISTY an internal model of "the world" it interacts
with: a bounded set of known entities with attributes, causal links
between concepts, and a lightweight statistical predictor that guesses
the next likely user intent. The difference between prediction and what
actually happens (prediction error) is exposed so downstream learners
(e.g. reinforcement learner) can use it as a learning signal.

Design constraints:
- Pure Python / NumPy (no LLM, no external ML model).
- All structures bounded in size so memory usage never grows unbounded.
- Serializable; state survives reloads from JSON.
"""

from __future__ import annotations

from typing import Any, Dict, List


class WorldEntity:
    """A known object in the environment with typed attributes."""

    def __init__(
        self,
        entity_id: str,
        entity_type: str = "object",
        location: str = "",
    ) -> None:
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.location = location
        self.attributes: Dict[str, Any] = {}
        self.updated_at: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "location": self.location,
            "attributes": dict(self.attributes),
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> WorldEntity:
        entity = WorldEntity(
            data["entity_id"],
            data.get("entity_type", "object"),
            data.get("location", ""),
        )
        entity.attributes = dict(data.get("attributes", {}))
        return entity


class WorldModel:
    """Structured world state plus a next-intent predictor.

    Responsibilities:
    - Maintain a bounded registry of known entities (location + attrs).
    - Record causal links (cause -> effect) observed during learning.
    - Predict the next likely user intent from recent intent history;
      expose prediction error after the real intent arrives.
    """

    def __init__(
        self,
        max_entities: int = 200,
        max_causal_links: int = 200,
        history_window: int = 16,
    ) -> None:
        self.max_entities = max_entities
        self.max_causal_links = max_causal_links
        self.history_window = history_window
        self.entities: Dict[str, WorldEntity] = {}
        self.causal_links: List[Dict[str, str]] = []
        # transition counts: (prev_intent, next_intent) -> count
        self.transitions: Dict[str, Dict[str, float]] = {}
        self.intent_history: List[str] = []
        self.last_prediction: str | None = None

    # ------------------------------------------------------------------
    # Entities
    # ------------------------------------------------------------------

    def add_entity(
        self,
        entity_id: str,
        entity_type: str = "object",
        location: str = "",
        attributes: Dict[str, Any] | None = None,
    ) -> WorldEntity:
        """Register or refresh a known world entity (bounded registry)."""
        if entity_id in self.entities:
            entity = self.entities[entity_id]
            entity.entity_type = entity_type or entity.entity_type
            entity.location = location or entity.location
            entity.attributes.update(attributes or {})
        else:
            entity = WorldEntity(entity_id, entity_type, location)
            entity.attributes = dict(attributes or {})
            self.entities[entity_id] = entity
            if len(self.entities) > self.max_entities:
                # Evict the oldest entry (insertion order).
                oldest = next(iter(self.entities))
                del self.entities[oldest]
        return entity

    def get_entity(self, entity_id: str) -> WorldEntity | None:
        return self.entities.get(entity_id)

    # ------------------------------------------------------------------
    # Causal links
    # ------------------------------------------------------------------

    def record_cause(self, cause: str, effect: str) -> None:
        """Remember an observed cause -> effect link (bounded)."""
        link = {"cause": cause, "effect": effect}
        self.causal_links.append(link)
        if len(self.causal_links) > self.max_causal_links:
            self.causal_links = self.causal_links[-self.max_causal_links :]

    def causes_of(self, effect: str) -> List[str]:
        return [link["cause"] for link in self.causal_links if link["effect"] == effect]

    def effects_of(self, cause: str) -> List[str]:
        return [link["effect"] for link in self.causal_links if link["cause"] == cause]

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    def predict_next_intent(self) -> str | None:
        """Guess the next intent from recent intent-history transitions.

        Returns None when there is not enough history yet.
        """
        if not self.intent_history:
            self.last_prediction = None
            return None
        # The most recent intent has no learned follow-up yet (its
        # transition is counted when the NEXT intent arrives), so look
        # back at the newest completed transition pair in history.
        for prev in reversed(self.intent_history):
            prediction = self.predict_from(prev)
            if prediction is not None:
                return prediction
        return None

    def predict_from(self, prev_intent: str) -> str | None:
        """Predict the most likely next intent given a previous intent."""
        counts = self.transitions.get(prev_intent, {})
        total = sum(counts.values())
        if total == 0:
            self.last_prediction = None
            return None
        self.last_prediction = max(counts, key=counts.get)
        return self.last_prediction

    def record_intent(self, intent: str) -> Dict[str, Any]:
        """Log the actual intent that occurred and compute prediction error.

        Args:
            intent: The intent that just happened (from NLU).

        Returns:
            Dict with previous prediction, whether it was correct and the
            scalar prediction error in [0, 1] for downstream learners.
        """
        prediction = self.predict_next_intent()
        correct = prediction == intent
        error = 0.0 if correct else 1.0

        # Slide the history window and update transition counts for the
        # newest observed transition (older transitions were already
        # counted when they first appeared).
        if self.intent_history:
            prev, nxt = self.intent_history[-1], intent
            self.transitions.setdefault(prev, {})
            self.transitions[prev][nxt] = self.transitions[prev].get(nxt, 0.0) + 1.0
        self.intent_history.append(intent)
        if len(self.intent_history) > self.history_window:
            self.intent_history = self.intent_history[-self.history_window :]

        self.last_prediction = self.predict_next_intent()
        return {
            "predicted": prediction,
            "actual": intent,
            "correct": correct,
            "error": error,
        }

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entities": {eid: e.to_dict() for eid, e in self.entities.items()},
            "causal_links": self.causal_links,
            "transitions": {k: dict(v) for k, v in self.transitions.items()},
            "intent_history": self.intent_history,
        }

    def load(self, data: Dict[str, Any]) -> None:
        self.entities = {eid: WorldEntity.from_dict(e) for eid, e in data.get("entities", {}).items()}
        self.causal_links = list(data.get("causal_links", []))
        self.transitions = {k: dict(v) for k, v in data.get("transitions", {}).items()}
        self.intent_history = list(data.get("intent_history", []))

    def reset(self) -> None:
        """Clear all world state (used in tests)."""
        self.entities.clear()
        self.causal_links.clear()
        self.transitions.clear()
        self.intent_history.clear()
        self.last_prediction = None
