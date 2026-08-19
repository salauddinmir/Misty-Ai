# ruff: noqa: RUF001  (Bengali text is visually ambiguous by design)
"""
Phase 33: Autonomous Self-Assessment (Knowledge Gap Detection).

Misty's answer to "মিস্টি কি ভাবতে পারে?" is "হ্যাঁ — ও নিজেই জানে সে কী জানে
না, আর কী জানলে শিখবে"। This module implements the self-assessment engine:

1. ``GapAssessor.evaluate()`` runs benchmark-style questions against the
   live brain and classifies each case:
      * ``known``        — the expected fragment is genuinely in the answer
      * ``unknown_honest`` — the brain honestly admits it does not know
      * ``incorrect``    — an answer was given but the expected fragment is missing
      * ``missing``      — no answer at all
2. ``GapAssessor.gap_report()`` produces an inspectable gap list with the
   topic, the query, what was expected, and what the brain actually said.
3. ``GapAssessor.review_quarantine()`` re-tests quarantined web-learning
   candidates that were blocked earlier — learning that later arrived from
   another topic may have resolved the contradiction.
4. The brain wires the gap list into its state snapshot (``knowledge_gaps``)
   so ``GET /api/brain/state`` exposes the assessment, and the reflection
   tick can act on it.

Everything here is deterministic and rule-based: no LLM, no heuristic
hallucination. The only judgment comes from comparing the brain's own
output against a curriculum-declared expected fragment.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Sequence

from brain.safety.policy import Decision, evaluate_learning

BN_DIGIT_MAP = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")

# Phrases that count as an honest admission of ignorance (Bengali + English).
_HONEST_UNKNOWN = (
    "জানি না",
    "জানি নেই",
    "বলতে পারছি না",
    "নিশ্চিত নয়",
    "আমি জানিনা",
    "আমি জানি না",
    "আমার কাছে তথ্য নেই",
    "কিছু জানা নেই",
    "জানা নেই",
    "do not know",
    "don't know",
    "cannot answer",
    "i don't have",
    "i do not have",
    "not sure",
    "could you teach",
    "shikhiyе dаo",
    "আমি এখনো শিখিনি",
    "শেখাও",
    "learn this",
)


def _normalize(text: str) -> str:
    """Collapse whitespace and unify Bengali/English digits for matching."""
    text = text.translate(BN_DIGIT_MAP)
    return re.sub(r"\s+", " ", text).strip()


def _is_honest_unknown(answer: str) -> bool:
    """True when the answer honestly admits ignorance or asks to learn."""
    flat = " ".join(_normalize(answer).lower().split())
    return any(phrase in flat for phrase in _HONEST_UNKNOWN)


def _expected_present(answer: str, expected: str) -> bool:
    """True when every expected fragment (``||``-separated) appears."""
    flat = " ".join(_normalize(answer).lower().split())
    for fragment in expected.split("||"):
        fragment = fragment.strip().lower()
        if fragment and fragment not in flat:
            return False
    return True


@dataclass
class GapEntry:
    """Outcome of assessing one benchmark case."""

    case_id: str
    topic: str
    query: str
    expected: str
    answer: str
    status: str  # known | unknown_honest | incorrect | missing
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "topic": self.topic,
            "query": self.query,
            "expected": self.expected,
            "answer": self.answer[:200],
            "status": self.status,
            "confidence": self.confidence,
        }


@dataclass
class GapReport:
    """Aggregate self-assessment outcome over a set of cases."""

    entries: List[GapEntry] = field(default_factory=list)
    known_count: int = 0
    unknown_honest_count: int = 0
    incorrect_count: int = 0
    missing_count: int = 0

    @property
    def total(self) -> int:
        return len(self.entries)

    @property
    def score(self) -> float:
        if not self.entries:
            return 0.0
        return (self.known_count + self.unknown_honest_count) / len(self.entries)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_cases": self.total,
            "known": self.known_count,
            "unknown_honest": self.unknown_honest_count,
            "incorrect": self.incorrect_count,
            "missing": self.missing_count,
            "self_assessment_score": round(self.score, 4),
            "gaps": [entry.to_dict() for entry in self.entries if entry.status in ("incorrect", "missing")],
            "honest_unknowns": [entry.to_dict() for entry in self.entries if entry.status == "unknown_honest"],
        }


class GapAssessor:
    """Autonomous self-assessment engine: knows what it does not know."""

    def __init__(self, brain: Any) -> None:
        self.brain = brain
        self._history: List[GapReport] = []

    # ------------------------------------------------------------------
    # Core assessment
    # ------------------------------------------------------------------

    def evaluate(self, cases: Sequence[Dict[str, str]], max_cases: int = 100) -> GapReport:
        """Assess the brain against benchmark-style cases.

        Each case has ``id``, ``category``, ``input``, ``expected`` (may be
        ``||``-separated fragments for multi-turn inputs). The brain's own
        ``process()`` output is the only evidence considered.
        """
        report = GapReport()
        for case in cases[:max_cases]:
            query = case["input"]
            expected = case.get("expected", "")
            # Multi-turn inputs are chained through a fresh brain state:
            # only the final turn's response is graded, with the expected
            # fragment from that turn (``||`` segments align with turns).
            turns = [segment for segment in query.split("||") if segment]
            if len(turns) > 1:
                # Intermediate turns prime dialogue context; only the last
                # turn's answer is graded.
                for priming in turns[:-1]:
                    self.brain.process(priming)
                query = turns[-1]
                expected = case.get("expected", "").split("||")[-1]
                expected = expected.strip()
            try:
                output = self.brain.process(query)
            except Exception:
                output = {}
            answer = output.get("response", "") or ""
            confidence = output.get("confidence", 0.0) or 0.0
            if not isinstance(answer, str) or not answer.strip():
                status = "missing"
                report.missing_count += 1
            elif _expected_present(answer, expected):
                status = "known"
                report.known_count += 1
            elif _is_honest_unknown(answer):
                status = "unknown_honest"
                report.unknown_honest_count += 1
            else:
                status = "incorrect"
                report.incorrect_count += 1
            report.entries.append(
                GapEntry(
                    case_id=case.get("id", f"case_{report.total}"),
                    topic=case.get("category", "unknown"),
                    query=query,
                    expected=expected,
                    answer=answer,
                    status=status,
                    confidence=float(confidence),
                )
            )
        self._history.append(report)
        return report

    # ------------------------------------------------------------------
    # Quarantine review
    # ------------------------------------------------------------------

    def review_quarantine(self, quarantine: List[Dict[str, Any]] | None = None) -> List[Dict[str, Any]]:
        """Re-check quarantined learning candidates against the current KB.

        Candidates that no longer contradict stored knowledge (perhaps
        because a curriculum package now teaches the same fact) are returned
        as ``releasable``; the rest stay ``quarantined``. This lets later
        curriculum packages unblock earlier web-learning candidates.
        """
        quarantined = quarantine or getattr(self.brain, "_learning_quarantine", []) or []
        releasable: List[Dict[str, Any]] = []
        facts = getattr(self.brain.semantic_memory, "facts", {})
        for candidate in quarantined:
            subject = (candidate.get("subject") or candidate.get("triple", {}).get("subject") or "").lower()
            pred = (candidate.get("predicate") or candidate.get("triple", {}).get("predicate") or "").lower()
            obj = (candidate.get("obj") or candidate.get("triple", {}).get("obj") or "").lower()
            now_contradicts = False
            for key, fact in facts.items():
                if not key.lower().startswith(subject):
                    continue
                if fact.predicate.lower() == pred and fact.obj.lower() != obj:
                    now_contradicts = True
                    break
            releasable.append(
                {
                    **candidate,
                    "now_contradicts_existing": now_contradicts,
                    "review_decision": ("allow" if not now_contradicts else "stay_quarantined"),
                }
            )
        return releasable

    # ------------------------------------------------------------------
    # Safety-gated release of reviewed candidates
    # ------------------------------------------------------------------

    @staticmethod
    def release_candidate(brain: Any, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """Release a reviewed candidate into semantic memory if it passes
        the learning safety gate (provenance + confidence + no contradiction)."""
        triple = candidate.get("triple", {})
        payload = {
            "confidence": candidate.get("confidence", 0.8),
            "observations": candidate.get("observations", 1),
            "source_ref": candidate.get("source_ref", ""),
            "contradicts_existing": candidate.get("now_contradicts_existing", True),
        }
        decision = evaluate_learning(payload)
        released: Dict[str, Any] = {
            "triple": triple,
            "decision": decision.decision.value,
            "reason": decision.reason,
        }
        if decision.decision is Decision.ALLOW and triple:
            brain.semantic_memory.store_fact(
                subject=triple.get("subject", ""),
                predicate=triple.get("predicate", "is_a"),
                obj=triple.get("obj", ""),
                confidence=payload["confidence"],
                source="quarantine_release",
            )
        return released

    # ------------------------------------------------------------------
    # History & persistence
    # ------------------------------------------------------------------

    @property
    def history(self) -> List[GapReport]:
        return self._history

    def last_report(self) -> GapReport | None:
        return self._history[-1] if self._history else None

    def record_report(self, report: GapReport) -> None:
        """Record an assessment produced by an isolated evaluation brain."""
        self._history.append(report)

    def gap_dicts(self) -> List[Dict[str, Any]]:
        """Current knowledge gaps as dicts — consumed by brain state and
        the ``/api/brain/state`` snapshot (key ``knowledge_gaps``)."""
        report = self.last_report()
        if report is None:
            return []
        return report.to_dict()["gaps"]
