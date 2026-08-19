"""Deterministic pre/post assessment for web-learning batches."""

from __future__ import annotations

import copy
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Sequence

from brain.knowledge.corpus_conversation import CONVERSATION_BENCHMARK
from brain.learning.self_assessment import GapAssessor, GapReport

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
    """Select benchmark cases whose input contains a learned topic."""

    @staticmethod
    def relevant_cases(topics: Sequence[str], cases: List[Dict[str, str]]) -> List[Dict[str, str]]:
        if not topics:
            return []
        needles = [topic.strip().lower() for topic in topics if topic.strip()]
        return [case for case in cases if any(needle in case.get("input", "").lower() for needle in needles)]


@dataclass(frozen=True)
class PreparedAssessment:
    """Frozen case set and baseline captured before candidate facts commit."""

    topics: tuple[str, ...]
    cases: tuple[Dict[str, str], ...]
    before: GapReport
    started_at: float
    min_agreement_sources: int
    selection_mode: str
    evaluation_brain: Any


class AssessmentRun:
    """A matched before/after assessment over one frozen case set."""

    def __init__(
        self,
        topics: Sequence[str],
        cases: List[Dict[str, str]],
        before: GapReport | None,
        after: GapReport,
        before_answers: List[str],
        after_answers: List[str],
        elapsed: float,
        *,
        min_agreement_sources: int = 2,
        selection_mode: str = "topic_match",
        committed_facts: int | None = None,
    ) -> None:
        self.topics = list(topics)
        self.cases = cases
        self.before = before
        self.after = after
        self.before_answers = before_answers
        self.after_answers = after_answers
        self.elapsed = elapsed
        self.min_agreement_sources = min_agreement_sources
        self.selection_mode = selection_mode
        self.committed_facts = committed_facts
        self.run_at = datetime.now(timezone.utc).isoformat()

    @property
    def improved(self) -> bool:
        """Report improvement only when a comparable baseline increased."""
        if self.before is None or self.committed_facts == 0:
            return False
        return self.after.score > self.before.score

    def diffs(self) -> List[Dict[str, Any]]:
        """Return answer changes for the matched cases."""
        out: List[Dict[str, Any]] = []
        for idx, case in enumerate(self.cases):
            if idx >= len(self.before_answers) or idx >= len(self.after_answers):
                continue
            if self.before_answers[idx] == self.after_answers[idx]:
                continue
            out.append(
                {
                    "case_index": idx,
                    "case_id": case.get("id", f"case_{idx}"),
                    "input": case.get("input", ""),
                    "expected": case.get("expected", ""),
                    "answer_before": self.before_answers[idx],
                    "answer_after": self.after_answers[idx],
                }
            )
        return out

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topics": self.topics,
            "assessed_cases": len(self.cases),
            "case_ids": [case.get("id", f"case_{idx}") for idx, case in enumerate(self.cases)],
            "selection_mode": self.selection_mode,
            "run_at": self.run_at,
            "elapsed_seconds": round(self.elapsed, 4),
            "before": self.before.to_dict() if self.before else None,
            "after": self.after.to_dict(),
            "comparison_available": self.before is not None,
            "improved": self.improved,
            "answer_diffs": self.diffs(),
            "committed_facts": self.committed_facts,
            "assessment_config": {
                "min_agreement_sources": self.min_agreement_sources,
            },
        }


class PostLearningAssessor:
    """Capture a baseline before commit and assess the same cases after it."""

    def __init__(self, brain: Any, *, gap_assessor: GapAssessor | None = None) -> None:
        self.brain = brain
        self.gap_assessor = gap_assessor or getattr(brain, "gap_assessor", None) or GapAssessor(brain)
        self.history: List[AssessmentRun] = []

    def _selected_cases(self, topics: Sequence[str]) -> tuple[List[Dict[str, str]], str]:
        filtered = _CaseFilter.relevant_cases(topics, CONVERSATION_BENCHMARK)
        if filtered:
            cases = filtered
            selection_mode = "topic_match"
        else:
            cases = list(CONVERSATION_BENCHMARK[::7])[:10]
            selection_mode = "deterministic_fallback"
        return ([{**case, "category": _case_category(case)} for case in cases], selection_mode)

    @staticmethod
    def _answers(report: GapReport) -> List[str]:
        return [entry.answer for entry in report.entries]

    def _evaluation_clone(self) -> Any:
        """Create an isolated evaluator with the same learned knowledge."""
        clone = type(self.brain)(use_neural_sim=False)
        for attribute in (
            "semantic_memory",
            "concept_graph",
            "episodic_memory",
            "procedural_memory",
            "working_memory",
            "emotion",
            "state",
            "world",
            "goal_manager",
            "variator",
            "conversation_driver",
            "dialogue_context",
            "self_model",
            "recall_scorer",
            "hebbian",
        ):
            setattr(clone, attribute, copy.deepcopy(getattr(self.brain, attribute)))
        clone.user_name = self.brain.user_name
        clone.enable_assessment_mode()
        return clone

    def prepare_assessment(
        self,
        topics: Sequence[str],
        *,
        min_agreement_sources: int = 2,
    ) -> PreparedAssessment | None:
        """Freeze selected cases and evaluate them before any fact commit."""
        normalized_topics = tuple(topic.strip() for topic in topics if topic.strip())
        if not normalized_topics:
            return None
        cases, selection_mode = self._selected_cases(normalized_topics)
        if not cases:
            return None
        started = time.monotonic()
        baseline_brain = self._evaluation_clone()
        evaluation_brain = self._evaluation_clone()
        before = GapAssessor(baseline_brain).evaluate(cases)
        return PreparedAssessment(
            topics=normalized_topics,
            cases=tuple(dict(case) for case in cases),
            before=before,
            started_at=started,
            min_agreement_sources=int(min_agreement_sources),
            selection_mode=selection_mode,
            evaluation_brain=evaluation_brain,
        )

    def complete_assessment(
        self,
        prepared: PreparedAssessment | None,
        *,
        committed_facts: int | None,
        committed_records: Sequence[Dict[str, Any]] | None = None,
    ) -> Dict[str, Any]:
        """Evaluate the frozen cases after applying only the committed delta."""
        if prepared is None or committed_facts == 0:
            return {"post_learning_assessment": None}
        cases = [dict(case) for case in prepared.cases]
        evaluation_brain = prepared.evaluation_brain
        for record in committed_records or ():
            evaluation_brain.semantic_memory.store_fact(
                subject=str(record["subject"]),
                predicate=str(record["predicate"]),
                obj=str(record["obj"]),
                confidence=float(record.get("confidence", 0.8)),
                source="web_learning_batch",
            )
        after = GapAssessor(evaluation_brain).evaluate(cases)
        self.gap_assessor.record_report(after)
        run = AssessmentRun(
            topics=prepared.topics,
            cases=cases,
            before=prepared.before,
            after=after,
            before_answers=self._answers(prepared.before),
            after_answers=self._answers(after),
            elapsed=time.monotonic() - prepared.started_at,
            min_agreement_sources=prepared.min_agreement_sources,
            selection_mode=prepared.selection_mode,
            committed_facts=committed_facts,
        )
        self.history.append(run)
        return {"post_learning_assessment": run.to_dict()}

    def assess_after_learning(
        self,
        topics: Sequence[str],
        *,
        min_agreement_sources: int = 2,
        prepared: PreparedAssessment | None = None,
        committed_facts: int | None = None,
        committed_records: Sequence[Dict[str, Any]] | None = None,
    ) -> Dict[str, Any]:
        """Complete a prepared assessment or run the compatibility flow.

        Web ingestion supplies ``prepared`` from the pre-commit stage. Direct
        callers still receive the established result wrapper without
        consulting unrelated historical reports.
        """
        if prepared is None:
            prepared = self.prepare_assessment(
                topics,
                min_agreement_sources=min_agreement_sources,
            )
        return self.complete_assessment(
            prepared,
            committed_facts=committed_facts,
            committed_records=committed_records,
        )

    def assess_baseline(self) -> Dict[str, Any]:
        """Capture the full benchmark baseline once."""
        if self.gap_assessor.last_report() is None:
            self.gap_assessor.evaluate(CONVERSATION_BENCHMARK)
        report = self.gap_assessor.last_report()
        return {"baseline_score": report.score if report else 0.0}

    def last_run(self) -> AssessmentRun | None:
        return self.history[-1] if self.history else None

    def trend(self) -> Dict[str, Any]:
        """Expose score history without treating different case sets as causal."""
        scores = [
            {
                "topics": run.topics,
                "case_ids": [case.get("id", "") for case in run.cases],
                "score": run.after.score,
                "known": run.after.known_count,
                "total": run.after.total,
                "improved": run.improved,
            }
            for run in self.history
        ]
        comparable = len(scores) >= 2 and all(item["case_ids"] == scores[0]["case_ids"] for item in scores[1:])
        return {
            "runs": len(scores),
            "scores": scores,
            "strictly_increasing": (
                all(scores[i]["score"] > scores[i - 1]["score"] for i in range(1, len(scores))) if comparable else None
            ),
        }


def attach_to_learner(learner: Any, assessor: PostLearningAssessor) -> None:
    """Attach an assessor explicitly without monkey-patching behavior."""
    learner.post_learning_assessor = assessor
