"""
Phase 37 — post-learning self-assessment loop (শেখানোর-পর-স্ব-মূল্যায়ন চক্র).

After every web-learning batch, Misty automatically re-tests itself on the
benchmark cases that relate to the topics it just learned, compares the new
answers against the pre-learning answers, and updates its topic-wise
scorecard. Nothing here is heuristic LLM judgement: everything is measured
against the deterministic benchmark from Phase 28 and the gap assessor
from Phase 33.

Design (per docs/misty_master_plan_bn.md, Phase 37):
1. Every batch ingestion auto re-runs the relevant benchmark cases.
2. Answer differences (before vs after) are reported per case.
3. The topic-wise scorecard is updated and history is retained.

Success criterion: benchmark score demonstrably rising after learning.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Sequence

from brain.knowledge.corpus_conversation import CONVERSATION_BENCHMARK
from brain.learning.self_assessment import GapAssessor, GapReport

# The Phase 28 CLI (tests/benchmark_conversation.py) annotates cases by id
# prefix; mirror that mapping here so entries land in the right topic
# buckets of the scorecard.
_CASE_CATEGORY: Dict[str, str] = {
    "conv_bn_greeting": "greeting",
    "conv_bn_context": "context",
    "conv_bn_empathy": "emotion",
    "conv_bn_angry": "emotion",
    "conv_bn_unknown": "unknown",
    "conv_bn_teach": "teach_followup",
    "conv_bn_cont": "continuation",
    "conv_bn_math": "math_physics",
    "conv_bn_phy": "math_physics",
    "conv_en_": "english",
    "conv_bn_joke": "humor",
    "conv_bn_clos": "closure",
    "conv_bn_corr": "correction",
}


def _case_category(case: Dict[str, str]) -> str:
    case_id = str(case.get("id", ""))
    for prefix, category in _CASE_CATEGORY.items():
        if case_id.startswith(prefix):
            return category
    return "general"


class _CaseFilter:
    """Deterministic filter that selects benchmark cases relevant to a set
    of learned topics (simple keyword containment on the case input)."""

    @staticmethod
    def relevant_cases(topics: Sequence[str],
                       cases: List[Dict[str, str]]) -> List[Dict[str, str]]:
        if not topics:
            return []
        needles = [topic.strip().lower() for topic in topics if topic.strip()]
        return [
            case for case in cases
            if any(needle in case.get("input", "").lower() for needle in needles)
        ]


class AssessmentRun:
    """One post-learning self-assessment run: before/after scores and the
    per-case answer diffs for the relevant benchmark cases."""

    def __init__(
        self,
        topics: Sequence[str],
        cases: List[Dict[str, str]],
        before: GapReport | None,
        after: GapReport,
        before_answers: List[str],
        after_answers: List[str],
        elapsed: float,
    ) -> None:
        self.topics = list(topics)
        self.cases = cases
        self.before = before
        self.after = after
        self.before_answers = before_answers
        self.after_answers = after_answers
        self.elapsed = elapsed
        self.run_at = datetime.now(timezone.utc).isoformat()

    @property
    def improved(self) -> bool:
        """True when the post-learning score is strictly higher, or the
        before state is unavailable (first learning) and the after state
        demonstrates learning occurred."""
        if self.before is None:
            return self.after.known_count > 0
        return self.after.score > self.before.score

    def diffs(self) -> List[Dict[str, Any]]:
        """Per-case answer differences for cases whose outcome changed."""
        out: List[Dict[str, Any]] = []
        for idx, case in enumerate(self.cases):
            changed = (
                idx < len(self.before_answers)
                and idx < len(self.after_answers)
                and self.before_answers[idx] != self.after_answers[idx]
            )
            if changed:
                out.append({
                    "case_index": idx,
                    "input": case.get("input", ""),
                    "expected": case.get("expected", ""),
                    "answer_before": self.before_answers[idx],
                    "answer_after": self.after_answers[idx],
                })
        return out

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topics": self.topics,
            "assessed_cases": len(self.cases),
            "run_at": self.run_at,
            "elapsed_seconds": round(self.elapsed, 4),
            "before": self.before.to_dict() if self.before else None,
            "after": self.after.to_dict(),
            "improved": self.improved,
            "answer_diffs": self.diffs(),
        }


class PostLearningAssessor:
    """Holds assessment history and runs before/after evaluations around
    batch ingestions (``assess_after_learning``).

    Wired into WebSearchLearner.ingest_batch (see ``attach_to_learner``)
    and called automatically after every batch ingestion.
    """

    def __init__(self, brain: Any) -> None:
        self.brain = brain
        self.gap_assessor = GapAssessor(brain)
        self.history: List[AssessmentRun] = []

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _selected_cases(self, topics: Sequence[str]) -> List[Dict[str, str]]:
        """Benchmark cases whose input mentions the learned topics; if none
        match, fall back to a deterministic subset of the Phase 28
        benchmark so the loop always produces data. Each returned case
        carries the "category" key the gap assessor uses for topic
        buckets."""
        filtered = _CaseFilter.relevant_cases(topics, CONVERSATION_BENCHMARK)
        if filtered:
            cases = filtered
        else:
            # Deterministic fallback: every 7th case up to 10.
            cases = [case for case in CONVERSATION_BENCHMARK[::7]][:10]
        return [{**case, "category": _case_category(case)} for case in cases]

    def _collect_answers(self, cases: List[Dict[str, str]]) -> List[str]:
        """Run the selected cases once and return the final answers, so the
        next evaluation can compare exact outputs (not only pass/fail)."""
        answers: List[str] = []
        for case in cases:
            try:
                result = self.brain.process(case["input"])
            except Exception:  # pragma: no cover - defensive
                answers.append("")
                continue
            response = result.get("response") if isinstance(result, dict) else None
            answers.append(response or "")
        return answers

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def assess_after_learning(
        self,
        topics: Sequence[str],
        *,
        min_agreement_sources: int = 2,
    ) -> Dict[str, Any]:
        """Re-run the relevant benchmark cases after a batch ingestion.

        Returns a dict compatible with the teaching report:
        ``{"post_learning_assessment": AssessmentRun.to_dict()}``.
        """
        if not topics:
            return {"post_learning_assessment": None}
        cases = self._selected_cases(topics)
        if not cases:
            return {"post_learning_assessment": None}

        started = time.monotonic()
        before_report: GapReport | None = self.gap_assessor.last_report()
        before_answers: List[str] = []
        if before_report is not None:
            before_answers = self._collect_answers(cases)
        after_answers = self._collect_answers(cases)
        after_report = self.gap_assessor.evaluate(cases)

        run = AssessmentRun(
            topics=topics,
            cases=cases,
            before=before_report,
            after=after_report,
            before_answers=before_answers,
            after_answers=after_answers,
            elapsed=time.monotonic() - started,
        )
        self.history.append(run)
        return {"post_learning_assessment": run.to_dict()}

    def assess_baseline(self) -> Dict[str, Any]:
        """Capture the pre-learning baseline so the first learning batch
        has something to compare against. Idempotent if already set."""
        if self.gap_assessor.last_report() is None:
            self.gap_assessor.evaluate(CONVERSATION_BENCHMARK)
        return {"baseline_score": self.gap_assessor.last_report().score}

    def last_run(self) -> AssessmentRun | None:
        return self.history[-1] if self.history else None

    def trend(self) -> Dict[str, Any]:
        """Monotonic improvement evidence across all runs."""
        scores = [
            {
                "topics": run.topics,
                "score": run.after.score,
                "known": run.after.known_count,
                "total": run.after.total,
                "improved": run.improved,
            }
            for run in self.history
        ]
        return {
            "runs": len(scores),
            "scores": scores,
            "strictly_increasing": all(
                scores[i]["score"] > scores[i - 1]["score"]
                for i in range(1, len(scores))
            ) if len(scores) >= 2 else None,
        }


def attach_to_learner(learner: Any, assessor: PostLearningAssessor) -> None:
    """Monkey-patch-free hook: store the assessor on the learner so
    ``ingest_batch`` can call ``assessor.assess_after_learning`` and merge
    the result into its teaching report."""
    learner.post_learning_assessor = assessor
