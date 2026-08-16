"""
Curiosity-Driven Exploration.

An artificial agent that never asks questions never discovers anything
new. This module implements an intrinsic-motivation signal that nudges
the brain toward *under-explored* parts of its knowledge graph:

- Concepts with low activation that sit near recently fired concepts
  get a **curiosity bonus**.
- When the bonus exceeds a threshold and the dialogue allows it, the
  brain *asks a question* about that concept instead of waiting to be
  taught.
- Curiosity is suppressed when the brain is busy (high urgency / high
  satisfaction) or when the concept has already been asked about.
"""

from typing import Any, Dict, Set


class CuriosityExplorer:
    """Intrinsic-motivation explorer for the knowledge graph.

    Args:
        bonus_strength: Curiosity bonus applied to low-activation
            neighbors (default 0.25).
        activation_floor: Concepts above this activation never receive
            the bonus (they are already well known).
        ask_threshold: Bonus above this triggers a question prompt.
        cooldown_cycles: Cycles a concept stays suppressed after being
            asked about.
    """

    def __init__(
        self,
        bonus_strength: float = 0.25,
        activation_floor: float = 0.5,
        ask_threshold: float = 0.2,
        cooldown_cycles: int = 8,
    ) -> None:
        self.bonus_strength = bonus_strength
        self.activation_floor = activation_floor
        self.ask_threshold = ask_threshold
        self.cooldown_cycles = cooldown_cycles
        # concept_id -> remaining cooldown cycles
        self._cooldowns: Dict[str, int] = {}
        self._asked_concepts: Set[str] = set()

    # ------------------------------------------------------------------

    def evaluate(
        self,
        graph: Any,
        activation_map: Dict[str, float],
        urgency: float = 0.0,
        satisfaction: float = 0.0,
    ) -> Dict[str, Any]:
        """Find under-explored concepts adjacent to currently active ones.

        Args:
            graph: The ConceptGraph instance.
            activation_map: Current cycle's activated concepts and
                levels (concept_id -> activation).
            urgency: Current urgency (0-1); high urgency suppresses
                curiosity.
            satisfaction: Current satisfaction (0-1); high satisfaction
                partially suppresses curiosity.

        Returns:
            Dict with ``target`` (best concept_id or None),
            ``bonus`` level, and ``question`` prompt or None.
        """
        result: Dict[str, Any] = {
            "target": None,
            "bonus": 0.0,
            "question": None,
        }
        if not activation_map or graph.num_concepts == 0:
            return result
        # Urgency suppresses exploration completely.
        if urgency > 0.7 or satisfaction > 0.9:
            return result

        # Seed: concepts active in this cycle.
        seeds = [cid for cid, lvl in activation_map.items() if lvl > 0.01]
        candidates: Dict[str, float] = {}
        for seed in seeds:
            for neighbor_id in graph.get_neighbors(seed):
                level = activation_map.get(neighbor_id, 0.0)
                if level >= self.activation_floor or neighbor_id in seeds:
                    continue
                candidates[neighbor_id] = max(
                    candidates.get(neighbor_id, 0.0),
                    level + self.bonus_strength,
                )

        # Apply cooldowns.
        best_id: str | None = None
        best_score = -1.0
        for cid, score in candidates.items():
            remaining = self._cooldowns.get(cid, 0)
            if remaining > 0 or cid in self._asked_concepts:
                continue
            if score > best_score:
                best_score = score
                best_id = cid

        if best_id is None or best_score < self.ask_threshold:
            return result

        concept = graph.get_concept(best_id)
        name = concept.name if concept else best_id
        result["target"] = best_id
        result["bonus"] = round(min(1.0, best_score), 4)
        result["question"] = f"{name} সম্পর্কে আমি আরো জানতে চাই। তুমি কি বলবে?"
        # Suppress this concept for a while (and stop re-asking).
        self._cooldowns[best_id] = self.cooldown_cycles
        self._asked_concepts.add(best_id)
        return result

    def step_cooldowns(self) -> None:
        """Tick all cooldown counters down by one (call once per cycle)."""
        expired = [cid for cid, n in self._cooldowns.items() if n <= 1]
        for cid in expired:
            del self._cooldowns[cid]
        for cid in self._cooldowns:
            self._cooldowns[cid] -= 1

    def reset(self) -> None:
        """Clear exploration state (used in tests)."""
        self._cooldowns.clear()
        self._asked_concepts.clear()

    def reset_asked(self) -> None:
        """Forget previously asked concepts so they can be asked again.

        Used after cooldowns expire: the same missing-knowledge concept
        may be revisited in a later conversation.
        """
        self._asked_concepts.clear()
