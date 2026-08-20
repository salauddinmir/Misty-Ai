"""
Phase 48: Connection-based reasoning layer.

``ReasoningEngine`` lets MISTY derive NEW conclusions from what it already
knows instead of merely retrieving stored facts. Working over the semantic
memory triples and the knowledge graph, it applies three deterministic
inference rules — transitivity, category inheritance, and symmetric
predicates — and stores the derived facts back into semantic memory with
source ``inferred`` and a confidence composed (and decayed) from the
supporting chain.

This is the "যা ভাবে তৈরি করে সেখান থেকে উত্তর দেবে" step: reasoning
that happens inside the brain's own memory fabric, with zero LLM
dependency.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

_HOP_DECAY = 0.9
_MAX_DERIVED_PER_TURN = 8
_MIN_DERIVED_CONFIDENCE = 0.25
_MAX_CONFIDENCE = 0.95
_DECISION_LOG_MAX = 100

# Relation types in the knowledge graph that express category membership.
_CATEGORY_RELATIONS = ("is_a", "type_of", "kind_of", "instance_of")

# Predicates where a reverse derived fact is sound.
# Maps stored predicate -> (derived predicate).
_SYMMETRIC_PREDICATES: Dict[str, str] = {
    "is_adjacent_to": "is_adjacent_to",
    "is_symmetric_with": "is_symmetric_with",
    "is_connected_to": "is_connected_to",
}

# Predicates that chain transitively.
_TRANSITIVE_PREDICATES = ("is_a", "type_of", "kind_of", "contains", "is_part_of")


@dataclass
class DerivationDecision:
    """A single recorded reasoning step."""

    rule: str
    key: str
    confidence: float
    stored: bool


class ReasoningEngine:
    """Derives new facts from semantic triples and graph edges."""

    def __init__(self, brain: Any) -> None:
        self._brain = brain
        self._total_derived = 0
        self._decisions: List[DerivationDecision] = []
        self._last_derived: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def derive(self) -> Dict[str, Any]:
        """Run one reasoning pass for the current turn.

        Bounded: at most ``_MAX_DERIVED_PER_TURN`` new facts are derived per
        call, each stored with source ``inferred``. Returns a short summary
        of this pass.
        """
        derived_this_pass: List[Dict[str, Any]] = []
        rules_fired: Dict[str, int] = {}

        for rule_fn in (self._transitive_derive, self._inheritance_derive, self._symmetric_derive):
            for rule, key, confidence, stored in rule_fn():
                self._log(rule, key, confidence, stored)
                rules_fired[rule] = rules_fired.get(rule, 0) + 1
                if stored:
                    derived_this_pass.append({"rule": rule, "key": key, "confidence": confidence})
                if len(derived_this_pass) >= _MAX_DERIVED_PER_TURN:
                    break
            if len(derived_this_pass) >= _MAX_DERIVED_PER_TURN:
                break

        self._last_derived = derived_this_pass[-5:]
        return {
            "derived_this_pass": len(derived_this_pass),
            "rules_fired": rules_fired,
        }

    def summary(self) -> Dict[str, Any]:
        """Bounded snapshot for the brain state API."""
        rule_totals: Dict[str, int] = {}
        for decision in self._decisions:
            rule_totals[decision.rule] = rule_totals.get(decision.rule, 0) + 1
        return {
            "enabled": True,
            "total_derived": self._total_derived,
            "recent": [
                {
                    "rule": d.rule,
                    "key": d.key,
                    "confidence": d.confidence,
                    "stored": d.stored,
                }
                for d in self._decisions[-5:]
            ],
            "rules_fired": rule_totals,
            "config": {
                "max_derived_per_turn": _MAX_DERIVED_PER_TURN,
                "min_derived_confidence": _MIN_DERIVED_CONFIDENCE,
                "hop_decay": _HOP_DECAY,
            },
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _log(self, rule: str, key: str, confidence: float, stored: bool) -> None:
        self._total_derived += 1
        self._decisions.append(DerivationDecision(rule, key, confidence, stored))
        if len(self._decisions) > _DECISION_LOG_MAX:
            self._decisions = self._decisions[-_DECISION_LOG_MAX // 2 :]

    def _facts(self) -> List[Any]:
        """Snapshot of stored facts as tuples."""
        return [(f.subject, f.predicate, f.obj, f.confidence) for f in self._brain.semantic_memory.facts.values()]

    def _store_derived(
        self,
        subject: str,
        predicate: str,
        obj: str,
        confidence: float,
    ) -> bool:
        semantic = self._brain.semantic_memory
        key = f"{subject}:{predicate}:{obj}"
        if key in semantic.facts:
            return False
        if confidence < _MIN_DERIVED_CONFIDENCE:
            return False
        semantic.store_fact(subject, predicate, obj, confidence, source="inferred")
        return True

    def _index_by_subject(self) -> Dict[str, List[Tuple[str, str, float]]]:
        index: Dict[str, List[Tuple[str, str, float]]] = {}
        for subject, predicate, obj, confidence in self._facts():
            index.setdefault(subject, []).append((predicate, obj, confidence))
        return index

    # ------------------------------------------------------------------
    # Rule implementations
    # ------------------------------------------------------------------

    def _transitive_derive(self) -> List[Tuple[str, str, float, bool]]:
        """(A p B) and (B p C) => (A p C) for transitive predicates."""
        results: List[Tuple[str, str, float, bool]] = []
        by_subject = self._index_by_subject()
        for subject, pairs in by_subject.items():
            for predicate, mid, c1 in pairs:
                if predicate not in _TRANSITIVE_PREDICATES:
                    continue
                for predicate2, obj, c2 in by_subject.get(mid, []):
                    if predicate2 != predicate:
                        continue
                    key = f"{subject}:{predicate}:{obj}"
                    if key in self._brain.semantic_memory.facts:
                        continue
                    confidence = min(c1, c2) * _HOP_DECAY
                    stored = self._store_derived(subject, predicate, obj, confidence)
                    results.append(("transitivity", key, confidence, stored))
        return results

    def _inheritance_derive(self) -> List[Tuple[str, str, float, bool]]:
        """If A -(is_a/type_of)-> B in the graph and B has a fact
        (B p C), then A likely inherits (A p C)."""
        results: List[Tuple[str, str, float, bool]] = []
        graph = self._brain.concept_graph
        by_subject = self._index_by_subject()
        seen: Dict[str, None] = {}
        for subject in by_subject.keys():
            concept = graph.get_concept_by_name(subject)
            if concept is None:
                continue
            # Children of ``subject`` are concepts whose outgoing category
            # edge points at ``subject`` (e.g. mango -(is_a)-> fruit).
            children_by_confidence: Dict[str, float] = {}
            for child_id in graph.get_neighbors(concept.concept_id):
                for rel in graph.get_relations(child_id, direction="outgoing"):
                    if rel.get("target") == concept.concept_id and rel.get("relation_type") in _CATEGORY_RELATIONS:
                        children_by_confidence[child_id] = rel.get("confidence", 1.0)
                        break
            if not children_by_confidence:
                continue
            for child_id, edge_conf in children_by_confidence.items():
                child_concept = graph.get_concept(child_id)
                if child_concept is None:
                    continue
                child_name = child_concept.name
                for predicate, obj, c2 in by_subject.get(subject, []):
                    if predicate in _CATEGORY_RELATIONS:
                        # Category membership chains are already handled by
                        # the transitivity rule with a per-hop decay; also
                        # inheriting category labels would produce wrong
                        # labels (e.g. "Misty is_a Field of computer
                        # science" from "AI is_a Field of computer
                        # science"), so only descriptive properties are
                        # inherited here.
                        continue
                    key = f"{child_name}:{predicate}:{obj}"
                    if key in self._brain.semantic_memory.facts or key in seen:
                        continue
                    seen[key] = None
                    confidence = min(c2, edge_conf) * _HOP_DECAY
                    stored = self._store_derived(child_name, predicate, obj, confidence)
                    results.append(("inheritance", key, confidence, stored))
        return results

    def _symmetric_derive(self) -> List[Tuple[str, str, float, bool]]:
        """(A p B) => (B p' A) for symmetric predicates."""
        results: List[Tuple[str, str, float, bool]] = []
        for subject, predicate, obj, confidence in self._facts():
            derived_predicate = _SYMMETRIC_PREDICATES.get(predicate)
            if derived_predicate is None:
                continue
            key = f"{obj}:{derived_predicate}:{subject}"
            if key in self._brain.semantic_memory.facts:
                continue
            stored = self._store_derived(obj, derived_predicate, subject, confidence)
            results.append(("symmetric", key, confidence, stored))
        return results
