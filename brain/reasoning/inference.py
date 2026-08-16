"""
Inference Engine.

Supports forward chaining (data-driven) and backward chaining
(goal-driven) inference using the rule base.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List

from brain.reasoning.rules import RuleBase


@dataclass
class InferenceEngine:
    """Forward and backward chaining inference engine."""

    rule_base: RuleBase = field(default_factory=RuleBase)
    working_facts: Dict[str, Any] = field(default_factory=dict)
    derived_facts: Dict[str, Any] = field(default_factory=dict)
    max_iterations: int = 100

    def assert_fact(self, key: str, value: Any) -> None:
        """Add a fact to working memory."""
        self.working_facts[key] = value

    def forward_chain(self) -> List[Dict[str, Any]]:
        """Apply forward chaining - derive new facts from existing ones."""
        new_facts: List[Dict[str, Any]] = []
        iterations = 0
        changed = True

        while changed and iterations < self.max_iterations:
            changed = False
            iterations += 1

            all_facts = {**self.working_facts, **self.derived_facts}
            matching_rules = self.rule_base.get_matching_rules(all_facts)

            for rule in matching_rules:
                for conclusion in rule.conclusions:
                    key = conclusion.get("key", "")
                    value = conclusion.get("value")

                    if key not in all_facts:
                        self.derived_facts[key] = value
                        new_facts.append(
                            {
                                "key": key,
                                "value": value,
                                "derived_from": rule.name,
                                "confidence": rule.confidence,
                            }
                        )
                        changed = True

        return new_facts

    def backward_chain(self, goal_key: str) -> Any | None:
        """Apply backward chaining - try to prove a goal."""
        if goal_key in self.working_facts:
            return self.working_facts[goal_key]
        if goal_key in self.derived_facts:
            return self.derived_facts[goal_key]

        for rule in self.rule_base.rules.values():
            for conclusion in rule.conclusions:
                if conclusion.get("key") == goal_key:
                    all_met = True
                    for condition in rule.conditions:
                        cond_key = condition.get("key", "")
                        if cond_key not in self.working_facts:
                            sub_result = self.backward_chain(cond_key)
                            if sub_result is None:
                                all_met = False
                                break

                    if all_met:
                        value = conclusion.get("value")
                        self.derived_facts[goal_key] = value
                        return value

        return None

    def query(self, key: str) -> Any | None:
        """Query for a fact, using inference if needed."""
        if key in self.working_facts:
            return self.working_facts[key]
        if key in self.derived_facts:
            return self.derived_facts[key]
        return self.backward_chain(key)

    def reset(self) -> None:
        """Reset derived facts (keep working facts and rules)."""
        self.derived_facts.clear()

    def __repr__(self) -> str:
        return (
            f"InferenceEngine(rules={self.rule_base.size}, "
            f"facts={len(self.working_facts)}, "
            f"derived={len(self.derived_facts)})"
        )
