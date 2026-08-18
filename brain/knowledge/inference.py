"""
Knowledge-Inference Synthesis.

``InferenceSynthesizer`` is the module that makes MISTY *think*: given a
question the NLU could not resolve into a supported intent, the
synthesizer looks for relevant concepts in the question, searches the
semantic memory (commonsense layer + learned facts) for triples that
match, chains related facts (depth <= 2) when needed, and assembles a
derived answer with a confidence score and an explicit derivation trace.

The result lets the Brain replace the old canned reply
"ইনটেন্ট নির্ভুলভাবে parse করতে পারছি না" with an honest, reasoned
answer derived from what MISTY actually knows — "যা ভাবে তৈরি করে
সেখান থেকে উত্তর দেবে"।
"""

import re
from collections import Counter
from dataclasses import dataclass
from typing import Any, Dict, List

from brain.knowledge.commonsense import (
    QUESTION_PATTERNS,
)

# Very common Bengali stop words stripped before concept matching.
_BN_STOP = {
    "কি", "কী", "কিছু", "এটা", "ওটা", "সেটা", "আমি", "তুমি", "আপনি",
    "আমার", "তার", "এর", "কেন", "কীভাবে", "কোথায়", "কখন", "হয়", "হয়ে",
    "থেকে", "জন্য", "দিয়ে", "হয়েছে", "যা", "যে", "এই", "ওই", "সেই",
    "তাহলে", "আছে", "আর", "এবং", "বা", "তো", "না", "বলুন",
    "জানতে", "চাই", "ভালো", "পারি", "পারো", "পারবে", "নেই",
}

_EXTRA_BN_STOP = {"কি", "কী", "কে", "এর", "ের", "র", "হলো"}

_EN_STOP = {
    "what", "is", "the", "a", "an", "of", "and", "or", "why", "how",
    "when", "where", "who", "does", "do", "have", "has", "can", "could",
    "would", "tell", "me", "please", "about", "its", "your", "my", "it",
    "i", "you", "we", "they", "this", "that", "these", "those", "are",
    "was", "were", "being", "known", "say",
    "by", "from", "in", "to", "at", "on", "with",
}


@dataclass
class InferenceResult:
    """Output of a single synthesis attempt."""

    answer: str
    confidence: float
    steps: List[str]
    is_derived: bool
    language: str = "bn"
    matched_predicate: str | None = None
    subject: str | None = None
    obj: str | None = None
    chain_depth: int = 0


class InferenceSynthesizer:
    """Derives answers from the Brain's semantic memory and commonsense
    layer instead of echoing memorized phrases."""

    def __init__(self) -> None:
        self._all_facts: List[Any] | None = None
        self._question_patterns = QUESTION_PATTERNS

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def synthesize(self, question: str, brain: Any) -> InferenceResult | None:
        """Try to derive an answer to ``question`` from stored knowledge.

        Returns an ``InferenceResult`` when at least one relevant fact is
        found, otherwise ``None`` so the Brain can fall back to its
        contextual humble reply.
        """
        text = question.strip()
        if not text:
            return None
        is_bengali = any("\u0980" <= ch <= "\u09ff" for ch in text)
        tokens = self._tokenize(text, is_bengali)
        concepts = self._extract_concepts(tokens, brain, is_bengali)
        if not concepts:
            return None
        # 1. Decide which predicate the question asks about
        predicate = self._detect_predicate(text, tokens, is_bengali)

        # 2. Search semantic memory: exact-concept direct lookup first
        matched_facts: List[Any] = []
        for concept in concepts:
            direct = self._lookup(brain, concept, predicate=predicate)
            matched_facts.extend(direct)
        # Deduplicate while preserving order
        seen: set = set()
        deduped: List[Any] = []
        for fact in matched_facts:
            key = f"{fact.subject}:{fact.predicate}:{fact.obj}"
            if key not in seen:
                seen.add(key)
                deduped.append(fact)
        matched_facts = deduped

        if not matched_facts:
            # 3. Chain reasoning: for each concept, follow one hop
            matched_facts = self._chain_lookup(brain, concepts, predicate)

        if not matched_facts:
            return None

        # Prefer the predicate actually carried by the matched facts.
        # A bare "আকাশ কী?" asks for identity, but when the brain only
        # knows color/reason facts, those specific predicates describe
        # the topic better than a mislabeled identity answer.
        pred_counts = Counter(f.predicate for f in matched_facts)
        if predicate and pred_counts.get(predicate, 0):
            effective_predicate = predicate
        else:
            effective_predicate = pred_counts.most_common(1)[0][0]

        return self._compose_answer(
            text, matched_facts[:3], concepts[0],
            effective_predicate, is_bengali,
        )

    # ------------------------------------------------------------------
    # Tokenization / concept extraction
    # ------------------------------------------------------------------

    # Bengali word pattern: letters (\u0980-\u09ff) plus dependent vowel
    # signs (matras) that attach to them. ASCII words fall back to \w.
    _BN_WORD_RE = re.compile(r"[\u0980-\u09ff\u09d7]+|[A-Za-z0-9_]+")

    @staticmethod
    def _tokenize(text: str, is_bengali: bool) -> List[str]:
        lowered = text.lower()
        tokens: List[str] = []
        if is_bengali:
            tokens.extend(
                m.group(0) for m in InferenceSynthesizer._BN_WORD_RE.finditer(lowered)
            )
        else:
            tokens.extend(token for token in re.split(r"\W+", lowered) if token)
        stop = _BN_STOP if is_bengali else _EN_STOP
        tokens = [t for t in tokens if t and t not in stop]
        # Drop leftover Bengali-only stop words that are single
        # characters or genitive particles (e.g. "আক", "শ", "র").
        if is_bengali:
            tokens = [t for t in tokens if t not in _EXTRA_BN_STOP]
        return tokens

    def _extract_concepts(
        self, tokens: List[str], brain: Any, is_bengali: bool
    ) -> List[str]:
        """Return question tokens that correspond to stored concept
        names (case-insensitive). Exact token-to-subject equality wins;
        a token may also count when it equals the whole question topic
        (e.g. "আকাশ" inside "আকাশের" after stop-word stripping).
        """
        concepts: List[str] = []
        stored = {subj.lower() for subj, _ in self._iter_stored_concepts(brain)}
        # Exact equality first (longer spans preferred)
        for length in (3, 2, 1):
            for start in range(len(tokens) - length + 1):
                span = " ".join(tokens[start : start + length])
                if span in stored and span not in concepts:
                    concepts.append(span)
        # Fallback 1: a question token fully contains a stored subject
        # (e.g. "আকাশের" contains "আক"-free subject "আকা" -> "আকাশ")
        for token in tokens:
            for subject in stored:
                if subject in token and len(subject) >= 2:
                    if subject not in concepts:
                        concepts.append(subject)
        # Fallback 2: strip common Bengali inflection suffixes so that
        # "আকাশের" / "আকাশকে" match the stored subject "আকাশ".
        if is_bengali and not concepts:
            for suffix in ("ের", "কে", "র", "টি", "টা"):
                stripped: List[str] = [
                    token[: -len(suffix)]
                    for token in tokens
                    if token.endswith(suffix) and len(token) > len(suffix) + 1
                ]
                for base in stripped:
                    for subject in stored:
                        if base in subject or subject in base:
                            if subject not in concepts:
                                concepts.append(subject)
        return concepts

    @staticmethod
    def _iter_stored_concepts(brain: Any):
        """Yield (subject, fact) for every subject stored in semantic
        memory."""
        for fact in brain.semantic_memory.facts.values():
            yield fact.subject, fact

    # ------------------------------------------------------------------
    # Predicate detection
    # ------------------------------------------------------------------

    def _detect_predicate(
        self, text: str, tokens: List[str], is_bengali: bool
    ) -> str | None:
        """Map question wording to a semantic predicate, e.g.
        'আকাশের রঙ' -> 'color', 'capital of India' -> 'capital'.

        Phrase markers (scored by length) win; when no phrase matched,
        a remaining token whose name equals a specific predicate
        (capital, color, taste, capital) counts as the question word.
        """
        lowered = text.lower()
        scored: Dict[str, int] = {}
        for pattern in self._question_patterns:
            phrases = pattern["bn"] if is_bengali else pattern["en"]
            # Also check both scripts for questions with mixed code
            for phrase in phrases:
                if phrase.lower() in lowered:
                    scored[pattern["predicate"]] = scored.get(
                        pattern["predicate"], 0
                    ) + len(phrase)
        # Phrase match among specific (non-generic) predicates wins
        specific = max(
            (p for p in scored if p != "is_a"), key=scored.get, default=None
        )
        if specific:
            return specific
        if "is_a" in scored:
            return "is_a"
        # Token-set fallback: "What is the capital of India?"
        for pattern in self._question_patterns:
            if pattern["predicate"] in tokens:
                return pattern["predicate"]
        return None

    # ------------------------------------------------------------------
    # Fact lookup and chaining
    # ------------------------------------------------------------------

    def _lookup(
        self, brain: Any, subject: str, predicate: str | None
    ) -> List[Any]:
        """Direct semantic-memory lookup for ``subject``."""
        facts: List[Any] = []
        # 1. Exact-concept facts (case-insensitive)
        exact = [
            f
            for f in brain.semantic_memory.facts.values()
            if f.subject.lower() == subject.lower()
        ]
        facts.extend(exact)
        # 2. If a predicate was asked about, prioritize matching facts
        if predicate:
            pred_facts = [
                f for f in exact if f.predicate.lower() == predicate.lower()
            ]
            if pred_facts:
                return pred_facts
        # 3. Substring-subject matches (e.g. question "আকাশ" matches
        #    a stored subject containing it)
        if not facts:
            facts.extend(
                fact
                for fact in brain.semantic_memory.facts.values()
                if (
                    subject in fact.subject.lower()
                    or fact.subject.lower() in subject
                )
                and fact.subject.lower() != subject.lower()
            )
        return facts

    def _chain_lookup(
        self,
        brain: Any,
        concepts: List[str],
        predicate: str | None,
        max_depth: int = 2,
    ) -> List[Any]:
        """One-hop chain: concept A has fact (A -> r -> B) and B has a
        fact that answers the question. Returns at most 2 derived facts.
        """
        results: List[Any] = []
        for concept in concepts:
            for fact in brain.semantic_memory.facts.values():
                if fact.subject.lower() != concept.lower():
                    continue
                intermediate = fact.obj
                for fact2 in brain.semantic_memory.facts.values():
                    if fact2.subject.lower() == intermediate.lower():
                        if predicate and fact2.predicate != predicate:
                            continue
                        results.append(fact2)
                        if len(results) >= 2:
                            return results
        return results

    # ------------------------------------------------------------------
    # Answer composition (the "synthesis" step)
    # ------------------------------------------------------------------

    def _compose_answer(
        self,
        question: str,
        facts: List[Any],
        subject: str,
        predicate: str | None,
        is_bengali: bool,
    ) -> InferenceResult:
        """Turn matched facts into a natural derived answer with a
        confidence that is the product of premise confidences."""
        steps: List[str] = []
        confidence = 1.0
        objects: List[str] = []
        for fact in facts:
            confidence *= max(fact.confidence, 0.2)
            steps.append(f"{fact.subject} {fact.predicate} {fact.obj}")
            if fact.obj and fact.obj not in objects:
                objects.append(fact.obj)

        # Find answer label for the detected predicate
        ans_bn = "উত্তর"
        ans_en = "answer"
        matched_predicate = None
        if predicate:
            for pattern in self._question_patterns:
                if pattern["predicate"] == predicate:
                    ans_bn = pattern["ans_bn"]
                    ans_en = pattern["ans_en"]
                    matched_predicate = predicate
                    break

        values = ", ".join(objects)
        strength = (
            "নিশ্চিত ভাবে জানি"
            if confidence >= 0.9
            else "আমার সংরক্ষিত জ্ঞান অনুযায়ী"
        )
        is_derived = confidence < 1.0 or any(
            f.source != "commonsense_layer" for f in facts
        )

        if is_bengali:
            # Possessive form: attach "ের" only when the subject does not
            # already carry a genitive ending (ে/র).
            possessive = subject
            if not subject.endswith(("ের", "র", "র ")) and not subject.endswith("ে"):
                possessive = f"{subject}ের"
            # The identity predicate asks "what is X"; answer directly.
            # Other predicates keep the label and add "হলো".
            if matched_predicate == "is_a":
                body = f"{subject} হলো {values}"
            else:
                body = f"{possessive} {ans_bn} হলো {values}"
            answer = (
                f"আমি {strength} বলতে পারি: {body}। "
                f"এটি আমার সংরক্ষিত কনসেপ্ট ও নিয়ম থেকে ডেরাইভ করা হয়েছে।"
            )
        else:
            answer = (
                f"Based on my stored knowledge, the {ans_en} of "
                f"{subject.title()} is {values}. Derived from concepts "
                f"and rules in my knowledge base."
            )

        return InferenceResult(
            answer=answer,
            confidence=round(min(confidence, 0.99), 3),
            steps=steps,
            is_derived=is_derived,
            language="bn" if is_bengali else "en",
            matched_predicate=matched_predicate,
            subject=subject,
            obj=values,
            chain_depth=1 if len(facts) == 1 and facts[0].subject.lower() != subject.lower() else 0,
        )
