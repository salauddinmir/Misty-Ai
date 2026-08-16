"""
Rule-Based Inference Rules.

Defines production rules (condition-action pairs) for the reasoning engine.
"""

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Rule:
    """A production rule for inference."""

    name: str
    conditions: List[Dict[str, Any]]
    conclusions: List[Dict[str, Any]]
    rule_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    confidence: float = 1.0
    priority: int = 0

    def matches(self, facts: Dict[str, Any]) -> bool:
        """Check if all conditions are satisfied by the given facts."""
        for condition in self.conditions:
            cond_type = condition.get("type", "exists")
            key = condition.get("key", "")

            if cond_type == "exists":
                if key not in facts:
                    return False
            elif cond_type == "equals":
                value = condition.get("value")
                if facts.get(key) != value:
                    return False
            elif cond_type == "contains":
                value = condition.get("value")
                if value not in facts.get(key, []):
                    return False

        return True

    def __repr__(self) -> str:
        return f"Rule(name={self.name}, priority={self.priority})"


@dataclass
class RuleBase:
    """Collection of inference rules."""

    rules: Dict[str, Rule] = field(default_factory=dict)

    def add_rule(self, rule: Rule) -> None:
        """Add a rule to the rule base."""
        self.rules[rule.rule_id] = rule

    def create_rule(
        self,
        name: str,
        conditions: List[Dict[str, Any]],
        conclusions: List[Dict[str, Any]],
        confidence: float = 1.0,
        priority: int = 0,
    ) -> Rule:
        """Create and add a new rule."""
        rule = Rule(
            name=name,
            conditions=conditions,
            conclusions=conclusions,
            confidence=confidence,
            priority=priority,
        )
        self.add_rule(rule)
        return rule

    def get_matching_rules(self, facts: Dict[str, Any]) -> List[Rule]:
        """Find all rules whose conditions match the given facts."""
        matching = [r for r in self.rules.values() if r.matches(facts)]
        return sorted(matching, key=lambda r: r.priority, reverse=True)

    @property
    def size(self) -> int:
        """Number of rules in the base."""
        return len(self.rules)

    def __repr__(self) -> str:
        return f"RuleBase(rules={self.size})"
