"""
Reinforcement Learning.

Simple RL agent that learns from reward/punishment signals.
"""

import hashlib
import random
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ReinforcementLearner:
    """Simple reinforcement learner using Q-value estimation."""

    q_values: Dict[str, Dict[str, float]] = field(default_factory=dict)
    learning_rate: float = 0.1
    discount_factor: float = 0.9
    exploration_rate: float = 0.2

    # Number of state buckets used to generalise similar intents. Raw intent
    # strings are mapped to one of these buckets so learning transfers across
    # superficially different but semantically similar inputs (e.g. the same
    # QUERY intent arriving with slightly different NLU metadata).
    n_buckets: int = 16

    def bucket(self, state: str) -> str:
        """Map a raw state string to a generalisation bucket.

        Reduces the state space so that Q-values learned for one utterance
        can help decide actions for similar utterances, instead of each
        distinct string learning in isolation.
        """
        # Avoid double-hashing an already-bucketed key, which would scatter
        # one state across many second-level buckets and dilute learning.
        base_state = state.split("#")[0]
        digest = hashlib.md5(base_state.encode("utf-8")).hexdigest()
        index = int(digest[:8], 16) % self.n_buckets
        return f"{base_state}#{index}"

    def get_value(self, state: str, action: str) -> float:
        """Get the estimated value of a state-action pair."""
        total = 0.0
        count = 0
        for bucket_key in (state, self.bucket(state)):
            if bucket_key in self.q_values and action in self.q_values[bucket_key]:
                total += self.q_values[bucket_key][action]
                count += 1
        return total / count if count else 0.0

    def get_best_action(self, state: str, available_actions: List[str]) -> str | None:
        """Select the best action for a state using epsilon-greedy policy.

        With probability `exploration_rate` a random action is chosen to
        keep discovering better strategies; otherwise the highest Q-value
        action is returned. This replaces the previous purely greedy
        selection so the learner does not get stuck in a local optimum.
        """
        if not available_actions:
            return None

        if random.random() < self.exploration_rate and len(available_actions) > 1:
            return random.choice(available_actions)

        best_action = available_actions[0]
        best_value = self.get_value(state, best_action)

        for action in available_actions[1:]:
            value = self.get_value(state, action)
            if value > best_value:
                best_value = value
                best_action = action

        return best_action

    def update(
        self,
        state: str,
        action: str,
        reward: float,
        next_state: str | None = None,
        next_actions: List[str] | None = None,
    ) -> float:
        """Update Q-value based on received reward."""
        if state not in self.q_values:
            self.q_values[state] = {}

        current_q = self.q_values[state].get(action, 0.0)

        future_value = 0.0
        if next_state and next_actions:
            best_next = self.get_best_action(next_state, next_actions)
            if best_next:
                future_value = self.get_value(next_state, best_next)

        target = reward + self.discount_factor * future_value
        new_q = current_q + self.learning_rate * (target - current_q)
        self.q_values[state][action] = new_q

        # Also update the generalisation bucket with a smaller step so
        # learning from one state gently informs related states.
        bucket_key = self.bucket(state)
        if bucket_key not in self.q_values:
            self.q_values[bucket_key] = {}
        bucket_q = self.q_values[bucket_key].get(action, 0.0)
        self.q_values[bucket_key][action] = bucket_q + 0.05 * (new_q - bucket_q)

        return new_q

    def decay_exploration(self, min_rate: float = 0.01) -> None:
        """Reduce exploration rate over time."""
        self.exploration_rate = max(min_rate, self.exploration_rate * 0.99)

    def __repr__(self) -> str:
        total_entries = sum(len(v) for v in self.q_values.values())
        return f"ReinforcementLearner(states={len(self.q_values)}, entries={total_entries})"
