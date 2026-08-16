"""
Semantic Memory.

Stores facts and concepts linked to the knowledge graph.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SemanticFact:
    """A factual assertion stored in semantic memory."""

    subject: str
    predicate: str
    obj: str
    confidence: float = 1.0
    source: str = "user_input"


@dataclass
class SemanticMemory:
    """Long-term fact/concept storage linked to the knowledge graph."""

    facts: Dict[str, SemanticFact] = field(default_factory=dict)
    concept_associations: Dict[str, List[str]] = field(default_factory=dict)

    def store_fact(
        self,
        subject: str,
        predicate: str,
        obj: str,
        confidence: float = 1.0,
        source: str = "user_input",
    ) -> str:
        """Store a semantic fact (subject-predicate-object triple)."""
        key = f"{subject}:{predicate}:{obj}"
        fact = SemanticFact(
            subject=subject,
            predicate=predicate,
            obj=obj,
            confidence=confidence,
            source=source,
        )
        self.facts[key] = fact

        for concept_id in (subject, obj):
            if concept_id not in self.concept_associations:
                self.concept_associations[concept_id] = []
            if key not in self.concept_associations[concept_id]:
                self.concept_associations[concept_id].append(key)

        return key

    def query(
        self,
        subject: Optional[str] = None,
        predicate: Optional[str] = None,
        obj: Optional[str] = None,
    ) -> List[SemanticFact]:
        """Query semantic memory with optional filters."""
        results = []
        for fact in self.facts.values():
            if subject is not None and fact.subject != subject:
                continue
            if predicate is not None and fact.predicate != predicate:
                continue
            if obj is not None and fact.obj != obj:
                continue
            results.append(fact)
        return results

    def get_facts_for_concept(self, concept_id: str) -> List[SemanticFact]:
        """Get all facts involving a concept."""
        keys = self.concept_associations.get(concept_id, [])
        return [self.facts[k] for k in keys if k in self.facts]

    def remove_fact(self, key: str) -> bool:
        """Remove a fact by its key."""
        if key in self.facts:
            fact = self.facts.pop(key)
            for concept_id in (fact.subject, fact.obj):
                if concept_id in self.concept_associations:
                    self.concept_associations[concept_id] = [
                        k for k in self.concept_associations[concept_id] if k != key
                    ]
            return True
        return False

    @property
    def size(self) -> int:
        """Number of stored facts."""
        return len(self.facts)

    def __repr__(self) -> str:
        return f"SemanticMemory(facts={self.size})"
