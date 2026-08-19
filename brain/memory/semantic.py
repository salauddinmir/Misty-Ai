"""
Semantic Memory.

Stores facts and concepts linked to the knowledge graph.
"""

from dataclasses import dataclass, field
from functools import lru_cache
from typing import Dict, List

from brain.knowledge.normalize import canonicalize, linked_names


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
        subject: str | None = None,
        predicate: str | None = None,
        obj: str | None = None,
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

    def query_flexible(
        self,
        subject: str | None = None,
        predicate: str | None = None,
        obj: str | None = None,
    ) -> List[SemanticFact]:
        """Query while tolerating spelling, inflection, and language differences.

        ``query`` stays strict for callers that depend on exact identity. This
        variant additionally matches normalized forms and linked Bengali/English
        names for the same concept, so knowledge stored as "গতিশক্তি" answers a
        question about "kinetic energy" and vice versa.
        """
        wanted_subjects = self._match_keys(subject)
        wanted_objects = self._match_keys(obj)
        wanted_predicates = self._match_keys(predicate)

        results: List[SemanticFact] = []
        for fact in self.facts.values():
            if wanted_subjects and not self._field_matches(fact.subject, wanted_subjects):
                continue
            if wanted_predicates and not self._field_matches(fact.predicate, wanted_predicates):
                continue
            if wanted_objects and not self._field_matches(fact.obj, wanted_objects):
                continue
            results.append(fact)
        results.sort(key=lambda item: float(item.confidence), reverse=True)
        return results

    @staticmethod
    @lru_cache(maxsize=100_000)
    def _match_keys(term: str | None) -> frozenset[str]:
        """Canonical keys that should be treated as equal to ``term``."""
        if term is None:
            return frozenset()
        keys = {canonicalize(term)}
        keys.update(canonicalize(name) for name in linked_names(term))
        return frozenset(key for key in keys if key)

    @staticmethod
    def _field_matches(value: str, wanted_keys: frozenset[str]) -> bool:
        return bool(SemanticMemory._match_keys(value) & wanted_keys)

    def subjects(self) -> List[str]:
        """Distinct subjects currently stored."""
        return list(dict.fromkeys(fact.subject for fact in self.facts.values()))

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
