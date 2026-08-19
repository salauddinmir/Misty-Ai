"""
Universal answer resolver.

The answer path used to be a long ladder of special cases, each doing its own
exact-string lookup. A question that did not fit one of those shapes fell
through to "I have not learned that yet" even when the required facts were
already stored under a different spelling, inflection, or language.

This resolver runs a single ordered strategy list over *all* stored knowledge:

1. direct facts for the asked concept (any predicate, either language),
2. predicate-directed facts when the question names a relation,
3. reverse facts (the concept appears as the object),
4. knowledge-graph relations,
5. a bounded multi-hop chain when nothing direct exists.

Every returned answer carries the exact facts it used, so grounding stays
inspectable and nothing is invented. When no strategy succeeds the resolver
returns ``None`` and the caller records the question as a learning gap.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Sequence, Tuple

from brain.knowledge.commonsense import QUESTION_PATTERNS
from brain.knowledge.normalize import canonicalize, is_bengali, linked_names, variants

# Predicates that answer "what is X" style questions.
_DEFINITION_PREDICATES: Tuple[str, ...] = (
    "is_a",
    "definition",
    "সংজ্ঞা",
    "meaning",
    "অর্থ",
    "সূত্র",
    "formula",
    "genre",
)

# Predicates that are structural rather than descriptive; they make poor
# stand-alone answers when a better predicate is available.
_WEAK_PREDICATES: frozenset[str] = frozenset({"same_as", "alias", "type_of"})

# Relations that answer the same question under different names, so a question
# about "creator" also finds "wrote", "founder", or "made_by" knowledge.
_PREDICATE_SYNONYMS: Tuple[Tuple[str, ...], ...] = (
    ("creator_of", "creator", "wrote", "made_by", "invented", "discovered", "founder", "রচয়িতা", "লেখক"),
    ("capital", "রাজধানী", "রাজধনী"),
    ("formula", "সূত্র"),
    ("definition", "সংজ্ঞা", "is_a", "meaning", "অর্থ"),
    ("unit", "একক"),
    ("population", "জনসংখ্যা"),
    ("currency", "মুদ্রা"),
    ("language", "ভাষা"),
    ("use", "uses", "ব্যবহার", "function"),
    ("color", "colour", "রঙ"),
    ("independence", "স্বাধীনতা"),
    ("largest", "বৃহত্তম", "সবচেয়ে বড়"),
    ("highest", "সর্বোচ্চ"),
    ("longest", "দীর্ঘতম"),
    ("cause", "কারণ", "why_reason"),
    ("function", "কাজ", "use"),
)

# Readable (english, bengali) names for relations used in answer sentences.
_PREDICATE_LABELS: Dict[str, Tuple[str, str]] = {
    "wrote": ("author", "রচয়িতা"),
    "creator_of": ("creator", "নির্মাতা"),
    "creator": ("creator", "নির্মাতা"),
    "made_by": ("maker", "নির্মাতা"),
    "invented": ("inventor", "আবিষ্কারক"),
    "discovered": ("discoverer", "আবিষ্কারক"),
    "founder": ("founder", "প্রতিষ্ঠাতা"),
    "capital": ("capital", "রাজধানী"),
    "formula": ("formula", "সূত্র"),
    "unit": ("unit", "একক"),
    "population": ("population", "জনসংখ্যা"),
    "currency": ("currency", "মুদ্রা"),
    "language": ("language", "ভাষা"),
    "definition": ("definition", "সংজ্ঞা"),
    "genre": ("genre", "ধরন"),
    "translated": ("translator", "অনুবাদক"),
    "independence": ("independence", "স্বাধীনতা"),
    "largest": ("largest", "বৃহত্তম"),
    "highest": ("highest", "সর্বোচ্চ"),
    "longest": ("longest", "দীর্ঘতম"),
    "function": ("function", "কাজ"),
    "cause": ("cause", "কারণ"),
}

_MAX_FACTS_PER_ANSWER = 3

# Relation phrases the curated commonsense patterns do not cover. Checked
# before them because they are more specific ("who wrote" beats "who").
_EXTRA_PREDICATE_PHRASES: Tuple[Tuple[str, str], ...] = (
    ("who wrote", "wrote"),
    ("written by", "wrote"),
    ("author of", "wrote"),
    ("কে লিখেছেন", "wrote"),
    ("কে লিখেছে", "wrote"),
    ("রচনা করেছেন", "wrote"),
    ("লেখক কে", "wrote"),
    ("who invented", "invented"),
    ("who discovered", "discovered"),
    ("কে আবিষ্কার", "invented"),
    ("capital of", "capital"),
    ("রাজধানী", "capital"),
    ("রাজধনী", "capital"),
    ("who founded", "founder"),
    ("প্রতিষ্ঠাতা", "founder"),
    ("formula of", "formula"),
    ("সূত্র", "formula"),
    ("unit of", "unit"),
    ("এককে", "unit"),
    ("একক", "unit"),
    ("symbol of", "symbol"),
    ("প্রতীক", "symbol"),
    ("population of", "population"),
    ("জনসংখ্যা", "population"),
    ("currency of", "currency"),
    ("মুদ্রা", "currency"),
    ("born", "birth"),
    ("জন্ম", "birth"),
    ("independence of", "independence"),
    ("স্বাধীনতা", "independence"),
    ("largest", "largest"),
    ("biggest", "largest"),
    ("বৃহত্তম", "largest"),
    ("সবচেয়ে বড়", "largest"),
    ("highest", "highest"),
    ("tallest", "highest"),
    ("সর্বোচ্চ", "highest"),
    ("longest", "longest"),
    ("দীর্ঘতম", "longest"),
    ("meaning of", "meaning"),
    ("মানে কি", "meaning"),
    ("অর্থ কি", "meaning"),
)


@dataclass
class ResolvedAnswer:
    """An answer composed strictly from stored knowledge."""

    text: str
    confidence: float
    predicate: str
    subject: str
    facts: List[Any] = field(default_factory=list)
    strategy: str = "direct_fact"
    steps: List[str] = field(default_factory=list)

    @property
    def fact_keys(self) -> List[Tuple[str, str, str]]:
        return [(fact.subject, fact.predicate, fact.obj) for fact in self.facts]


class UniversalResolver:
    """Answer arbitrary factual questions from everything the brain knows."""

    def __init__(self) -> None:
        self._predicate_phrases = self._build_predicate_index()

    # -- public API ------------------------------------------------------
    def resolve(self, question: str, brain: Any, *, target: str | None = None) -> ResolvedAnswer | None:
        """Return the best grounded answer for ``question``, or ``None``."""
        question = (question or "").strip()
        if not question and not target:
            return None

        bengali = is_bengali(question or target or "")
        predicate = self._detect_predicate(question)
        subjects = self._candidate_subjects(question, brain, explicit_target=target)
        if not subjects:
            return None

        # A specific relation question must exhaust relation-shaped strategies
        # before the catch-all "anything known about the subject" answer.
        if predicate and predicate not in _DEFINITION_PREDICATES:
            strategies = (
                self._by_predicate,
                self._by_reverse_fact,
                self._by_graph_relation,
                self._by_definition,
                self._by_any_predicate,
            )
        else:
            strategies = (
                self._by_definition,
                self._by_predicate,
                self._by_any_predicate,
                self._by_graph_relation,
            )

        # First pass: a subject that actually holds the asked relation wins over
        # a subject that merely exists. Without this an alias entry such as
        # "india capital definition" would answer with its own description
        # instead of the capital stored on "India".
        if predicate:
            for subject in subjects:
                answer = self._by_predicate(subject, predicate, brain, bengali)
                if answer is not None:
                    return answer

        for subject in subjects:
            for strategy in strategies:
                answer = strategy(subject, predicate, brain, bengali)
                if answer is not None:
                    return answer

        # Nothing direct: try one bounded inference hop.
        for subject in subjects[:2]:
            answer = self._by_chain(subject, brain, bengali)
            if answer is not None:
                return answer
        return None

    # -- subject selection ----------------------------------------------
    def _candidate_subjects(self, question: str, brain: Any, explicit_target: str | None = None) -> List[str]:
        """Stored subjects the question plausibly refers to, best first."""
        stored: Dict[str, List[str]] = {}
        for subject in brain.semantic_memory.subjects():
            key = canonicalize(subject)
            if key:
                stored.setdefault(key, []).append(subject)

        ordered: List[str] = []
        seen: set[str] = set()

        def _accept(candidate: str) -> None:
            for name in stored.get(canonicalize(candidate), []):
                if name.casefold() not in seen:
                    seen.add(name.casefold())
                    ordered.append(name)

        if explicit_target:
            for variant in variants(explicit_target):
                _accept(variant)

        # Longest phrases first so "kinetic energy" beats "energy".
        for phrase in self._phrases(question):
            for variant in variants(phrase):
                _accept(variant)

        if ordered:
            return ordered

        # Last resort: a stored subject that shares a distinctive word.
        question_keys = {canonicalize(word) for word in self._words(question)}
        question_keys.discard("")
        ordered.extend(
            name
            for key, names in stored.items()
            if set(key.split()) and set(key.split()) <= question_keys
            for name in names
        )
        return ordered[:5]

    @staticmethod
    def _words(text: str) -> List[str]:
        return [word for word in re.findall(r"[A-Za-z\u0980-\u09ff]+", text or "") if len(word) > 1]

    def _phrases(self, question: str) -> List[str]:
        """Contiguous word spans, longest first, so compounds win."""
        words = self._words(question)
        spans: List[str] = []
        for size in (4, 3, 2, 1):
            spans.extend(" ".join(words[start : start + size]) for start in range(0, max(0, len(words) - size + 1)))
        return spans

    # -- predicate detection --------------------------------------------
    @staticmethod
    def _build_predicate_index() -> List[Tuple[str, str, int]]:
        index: List[Tuple[str, str, int]] = []
        for entry in QUESTION_PATTERNS:
            predicate = entry.get("predicate", "")
            for language in ("bn", "en"):
                for phrase in entry.get(language, []) or []:
                    phrase = phrase.strip().casefold()
                    if phrase:
                        index.append((phrase, predicate, len(phrase)))
        index.sort(key=lambda item: item[2], reverse=True)
        return index

    def detect_predicate(self, question: str) -> str | None:
        """Public predicate detection, shared with the recall phase."""
        return self._detect_predicate(question)

    def predicate_label(self, predicate: str, bengali: bool) -> str:
        """Public readable relation name, shared with answer composition."""
        return self._predicate_label(predicate, bengali)

    def relation_facts(self, question: str, brain: Any, predicate: str, target: str | None = None) -> List[Any]:
        """Facts holding ``predicate`` for any subject the question names.

        Used by the recall phase so evidence ranking sees the relation that was
        actually asked about, even when it lives on a different subject than the
        parsed target (an alias, a translation, or a compound spelling).
        """
        for subject in self._candidate_subjects(question, brain, explicit_target=target):
            for candidate in self._predicate_family(predicate):
                facts = brain.semantic_memory.query_flexible(subject=subject, predicate=candidate)
                if facts:
                    return facts
        return []

    def _detect_predicate(self, question: str) -> str | None:
        lowered = (question or "").casefold()
        for phrase, predicate in _EXTRA_PREDICATE_PHRASES:
            if phrase in lowered:
                return predicate
        for phrase, predicate, _ in self._predicate_phrases:
            if phrase in lowered:
                return predicate
        return None

    # -- strategies ------------------------------------------------------
    @staticmethod
    def _predicate_family(predicate: str | None) -> Tuple[str, ...]:
        """Expand a predicate into equivalent relation names."""
        if not predicate:
            return ()
        for family in _PREDICATE_SYNONYMS:
            if predicate in family:
                return family
        return (predicate,)

    def _by_predicate(self, subject: str, predicate: str | None, brain: Any, bengali: bool) -> ResolvedAnswer | None:
        if not predicate:
            return None
        for candidate in self._predicate_family(predicate):
            facts = brain.semantic_memory.query_flexible(subject=subject, predicate=candidate)
            if facts:
                return self._compose(subject, candidate, facts, bengali, "predicate_match")
        return None

    def _by_definition(self, subject: str, predicate: str | None, brain: Any, bengali: bool) -> ResolvedAnswer | None:
        if predicate and predicate not in _DEFINITION_PREDICATES:
            return None
        for candidate in _DEFINITION_PREDICATES:
            facts = brain.semantic_memory.query_flexible(subject=subject, predicate=candidate)
            if facts:
                return self._compose(subject, candidate, facts, bengali, "definition")
        return None

    def _by_any_predicate(
        self, subject: str, predicate: str | None, brain: Any, bengali: bool
    ) -> ResolvedAnswer | None:
        """Answer with whatever is known about the subject."""
        facts = [
            fact
            for fact in brain.semantic_memory.query_flexible(subject=subject)
            if fact.predicate not in _WEAK_PREDICATES
        ]
        if not facts:
            return None
        # Prefer facts written in the question's language.
        facts.sort(key=lambda fact: (is_bengali(fact.obj) != bengali, -float(fact.confidence)))
        return self._compose(subject, facts[0].predicate, facts, bengali, "known_attributes")

    def _by_reverse_fact(self, subject: str, predicate: str | None, brain: Any, bengali: bool) -> ResolvedAnswer | None:
        facts: List[Any] = []
        for candidate in self._predicate_family(predicate) or (None,):
            facts = brain.semantic_memory.query_flexible(obj=subject, predicate=candidate)
            if facts:
                break
        if not facts:
            return None
        subjects = list(dict.fromkeys(fact.subject for fact in facts))[:_MAX_FACTS_PER_ANSWER]
        joined = ", ".join(subjects)
        relation = facts[0].predicate
        text = (
            f"আমার সংরক্ষিত জ্ঞান অনুসারে {joined} — {subject}-এর সাথে '{relation}' সম্পর্কে যুক্ত।"
            if bengali
            else f"From my stored knowledge, {joined} relate to {subject} through '{relation}'."
        )
        confidence = min(0.9, min(float(fact.confidence) for fact in facts[:_MAX_FACTS_PER_ANSWER]))
        return ResolvedAnswer(
            text=text,
            confidence=confidence,
            predicate=relation,
            subject=subject,
            facts=facts[:_MAX_FACTS_PER_ANSWER],
            strategy="reverse_fact",
            steps=[f"{fact.subject} --{fact.predicate}--> {fact.obj}" for fact in facts[:_MAX_FACTS_PER_ANSWER]],
        )

    def _by_graph_relation(
        self, subject: str, predicate: str | None, brain: Any, bengali: bool
    ) -> ResolvedAnswer | None:
        concept = None
        for name in (subject, *linked_names(subject)):
            concept = brain.concept_graph.get_concept_by_name(name)
            if concept:
                break
        if concept is None:
            return None
        relations = brain.concept_graph.get_relations(concept.concept_id, direction="both")
        family = set(self._predicate_family(predicate))
        if family:
            asked = [item for item in relations if item.get("relation_type") in family]
            if asked:
                # The graph holds exactly the asked relation, so name the
                # related concept as the answer instead of a neighbour list.
                names: List[str] = []
                for relation in asked[:_MAX_FACTS_PER_ANSWER]:
                    other_id = (
                        relation.get("source")
                        if relation.get("target") == concept.concept_id
                        else relation.get("target")
                    )
                    other = brain.concept_graph.get_concept(other_id) if other_id else None
                    if other and other.name not in names:
                        names.append(other.name)
                if names:
                    joined = ", ".join(names)
                    label = self._predicate_label(predicate or "", bengali)
                    text = (
                        f"{subject}-এর {label} হলো {joined}।" if bengali else f"The {label} of {subject} is {joined}."
                    )
                    return ResolvedAnswer(
                        text=text,
                        confidence=0.85,
                        predicate=predicate or "related_to",
                        subject=subject,
                        strategy="graph_relation_match",
                        steps=[f"{subject} --{predicate}--> {name}" for name in names],
                    )
            relations = relations or []
        neighbours: List[str] = []
        for relation in relations[:_MAX_FACTS_PER_ANSWER]:
            other_id = (
                relation.get("target") if relation.get("source") == concept.concept_id else relation.get("source")
            )
            other = brain.concept_graph.get_concept(other_id) if other_id else None
            if other and other.name not in neighbours:
                neighbours.append(other.name)
        if not neighbours:
            return None
        joined = ", ".join(neighbours)
        text = (
            f"{subject} সম্পর্কে আমার গ্রাফে যা আছে: {joined}।"
            if bengali
            else f"In my knowledge graph, {subject} is connected to {joined}."
        )
        return ResolvedAnswer(
            text=text,
            confidence=0.6,
            predicate=predicate or "related_to",
            subject=subject,
            strategy="graph_relation",
            steps=[f"{subject} --graph--> {name}" for name in neighbours],
        )

    def _by_chain(self, subject: str, brain: Any, bengali: bool) -> ResolvedAnswer | None:
        """One inference hop: subject -> middle -> answer."""
        first_hop = [
            fact
            for fact in brain.semantic_memory.query_flexible(subject=subject)
            if fact.predicate not in _WEAK_PREDICATES
        ]
        for link in first_hop[:3]:
            second_hop = [
                fact
                for fact in brain.semantic_memory.query_flexible(subject=link.obj)
                if fact.predicate not in _WEAK_PREDICATES
            ]
            if not second_hop:
                continue
            end = second_hop[0]
            confidence = round(max(0.3, float(link.confidence) * float(end.confidence)), 3)
            text = (
                f"সরাসরি তথ্য না থাকলেও যুক্তি দিয়ে বলা যায়: {subject} → {link.obj} → {end.obj}।"
                if bengali
                else f"I do not have a direct fact, but I can derive it: {subject} → {link.obj} → {end.obj}."
            )
            return ResolvedAnswer(
                text=text,
                confidence=confidence,
                predicate=end.predicate,
                subject=subject,
                facts=[link, end],
                strategy="inference_chain",
                steps=[
                    f"{link.subject} --{link.predicate}--> {link.obj}",
                    f"{end.subject} --{end.predicate}--> {end.obj}",
                ],
            )
        return None

    # -- composition -----------------------------------------------------
    def _compose(
        self,
        subject: str,
        predicate: str,
        facts: Sequence[Any],
        bengali: bool,
        strategy: str,
    ) -> ResolvedAnswer:
        # Answer in the language of the question: knowledge is stored in both
        # Bengali and English, and mixing them reads as two half answers.
        same_language = [fact for fact in facts if is_bengali(str(fact.obj)) == bengali]
        used = list((same_language or list(facts))[:_MAX_FACTS_PER_ANSWER])
        values: List[str] = []
        for fact in used:
            value = str(fact.obj).strip()
            if not value:
                continue
            # Two curricula may describe the same thing at different lengths;
            # repeating both reads as the answer stuttering.
            if any(value in kept or kept in value for kept in values):
                continue
            values.append(value)
        joined = ", ".join(values)
        label = self._predicate_label(predicate, bengali)
        if predicate in _DEFINITION_PREDICATES:
            text = f"{subject} হলো {joined}।" if bengali else f"{subject} is {joined}."
        else:
            text = f"{subject}-এর {label} হলো {joined}।" if bengali else f"The {label} of {subject} is {joined}."
        confidence = min(0.95, min(float(fact.confidence) for fact in used))
        return ResolvedAnswer(
            text=text,
            confidence=confidence,
            predicate=predicate,
            subject=subject,
            facts=used,
            strategy=strategy,
            steps=[f"{fact.subject} --{fact.predicate}--> {fact.obj}" for fact in used],
        )

    @staticmethod
    def _predicate_label(predicate: str, bengali: bool) -> str:
        readable = _PREDICATE_LABELS.get(predicate)
        if readable:
            return readable[1] if bengali else readable[0]
        for entry in QUESTION_PATTERNS:
            if entry.get("predicate") == predicate:
                label = entry.get("ans_bn" if bengali else "ans_en")
                if label:
                    return str(label)
        return predicate.replace("_", " ")


#: Shared instance; the resolver is stateless apart from its phrase index.
UNIVERSAL_RESOLVER = UniversalResolver()
