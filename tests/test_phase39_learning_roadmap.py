"""
Phase 39: self-assessment-driven learning roadmap tests.

Covers the LearningPlanner / LearningPlan / RoadmapItem components in
brain/learning/learning_roadmap.py and their wiring into brain/core/brain.py
(learning_planner attribute, get_state "learning_roadmap" field,
run_learning_roadmap async method).

The gap assessor is exercised directly (no live web calls) so these tests
are deterministic.
"""

import os
from unittest.mock import AsyncMock

import pytest

from brain.core.brain import Brain
from brain.learning.learning_roadmap import LearningPlan, LearningPlanner, RoadmapItem
from brain.learning.self_assessment import GapEntry, GapReport


@pytest.fixture
def brain():
    """Fresh Brain using SQLite (dev default) with no production DB needed."""
    os.environ.setdefault(
        "MISTY_DB_URL",
        "sqlite+aiosqlite://",
    )
    return Brain()


def _make_gap_report(*, incorrect: int = 0, unknown_honest: int = 0, missing: int = 0, known: int = 0) -> GapReport:
    """Build a minimal synthetic GapReport with sequential case ids."""
    entries: list[GapEntry] = []
    counters = {"incorrect": 0, "unknown_honest": 0, "missing": 0, "known": 0}
    for status, total in (
        ("incorrect", incorrect),
        ("unknown_honest", unknown_honest),
        ("missing", missing),
        ("known", known),
    ):
        for _ in range(total):
            counters[status] += 1
            entries.append(
                GapEntry(
                    case_id=f"case-{counters[status]:03d}",
                    topic="mathematics",
                    query=f"test question {counters[status]}",
                    expected="expected answer",
                    answer="actual answer" if status != "missing" else "",
                    status=status,
                    confidence=0.0 if status == "unknown_honest" else 0.5,
                )
            )
    report = GapReport(entries=entries)
    return report


def test_learning_planner_wired_on_brain(brain):
    assert isinstance(brain.learning_planner, LearningPlanner)
    assert brain.learning_planner.brain is brain


def test_state_exposes_learning_roadmap_field(brain):
    state = brain.get_state()
    assert "learning_roadmap" in state
    assert state["learning_roadmap"] is None


def test_plan_empty_when_no_gap_report(brain):
    planner = brain.learning_planner
    plan = planner.plan_next_topics()
    assert isinstance(plan, LearningPlan)
    assert plan.items == []
    assert plan.total_planned_topics == 0


def test_plan_ranks_gap_topics_when_report_present(brain):
    planner = brain.learning_planner
    report = _make_gap_report(incorrect=2, unknown_honest=1, missing=1, known=4)
    brain.gap_assessor.record_report(report)

    plan = planner.plan_next_topics()
    assert len(plan.items) >= 1
    topics = [item.topic for item in plan.items]
    assert "mathematics" in topics


def test_incorrect_weighted_higher_than_honest_unknown(brain):
    planner = brain.learning_planner

    heavy = _make_gap_report(incorrect=4, known=2)
    light = _make_gap_report(unknown_honest=4, known=2)

    brain.gap_assessor.record_report(heavy)
    plan_heavy = planner.plan_next_topics()
    heavy_item = next(item for item in plan_heavy.items if item.topic == "mathematics")

    # A fresh planner instance (fresh history) so the light report is the
    # only report the planner can see.
    fresh = LearningPlanner(brain)
    brain.gap_assessor.record_report(light)
    plan_light = fresh.plan_next_topics()
    light_item = next(item for item in plan_light.items if item.topic == "mathematics")

    assert heavy_item.severity > light_item.severity
    # Weights are comparable only within the same plan context; both plans
    # distribute the same 1.0 budget over a single mathematics topic, so
    # the heavy-report plan must give mathematics at least as much weight.
    assert heavy_item.weight >= light_item.weight


def test_gap_severity_formula_missing_case(brain):
    """Severity must count unknown_honest and missing as failures."""
    planner = brain.learning_planner
    report = _make_gap_report(missing=2, known=6)
    brain.gap_assessor.record_report(report)
    plan = planner.plan_next_topics()
    assert len(plan.items) == 1
    assert plan.items[0].severity > 0.0


def test_boost_topics_promoted_first(brain):
    planner = brain.learning_planner
    report = _make_gap_report(incorrect=1, missing=1, known=2)
    # boost_topics only promotes topics the assessor has actually seen,
    # so the report must contain a "literature" entry to be promotable.
    report.entries.append(
        GapEntry(
            case_id="case-lit-001",
            topic="literature",
            query="test bengali poetry question",
            expected="expected answer",
            answer="",
            status="missing",
            confidence=0.0,
        )
    )
    brain.gap_assessor.record_report(report)

    plan = planner.plan_next_topics(boost_topics=("literature",))
    topics = [item.topic for item in plan.items]
    assert topics and topics[0] == "literature"


def test_budget_respected(brain):
    planner = brain.learning_planner
    report = _make_gap_report(incorrect=3, missing=3, known=2)
    brain.gap_assessor.record_report(report)

    plan = planner.plan_next_topics(budget=1.0)
    assert plan.items
    assert sum(item.weight for item in plan.items) <= 1.0 + 1e-9


def test_max_topics_respected(brain):
    planner = brain.learning_planner
    report = _make_gap_report(incorrect=10, known=2)
    brain.gap_assessor.record_report(report)

    plan = planner.plan_next_topics(max_topics=2)
    assert len(plan.items) <= 2


def test_roadmap_item_dict_shape(brain):
    planner = brain.learning_planner
    report = _make_gap_report(incorrect=1, known=1)
    brain.gap_assessor.record_report(report)

    plan = planner.plan_next_topics()
    assert plan.items, "a 50% incorrect topic must enter the plan"
    item = plan.items[0]
    assert isinstance(item, RoadmapItem)
    d = item.to_dict()
    for key in ("rank", "topic", "reason", "gap_cases", "gap_ratio", "severity", "weight", "aliases"):
        assert key in d, key
    assert isinstance(d["aliases"], list)


def test_plan_dict_shape_and_history(brain):
    planner = brain.learning_planner
    report = _make_gap_report(incorrect=1, missing=1, known=1)
    brain.gap_assessor.record_report(report)

    plan = planner.plan_next_topics()
    d = plan.to_dict()
    for key in ("plan_id", "total_planned_topics", "items", "topic_scores"):
        assert key in d, key
    assert d["total_planned_topics"] == len(plan.items)
    assert plan is planner.last_plan()
    assert plan in planner.history


def test_estimate_coverage_independent_of_plan(brain):
    report = _make_gap_report(incorrect=1, unknown_honest=1, missing=1, known=3)
    scores = brain.learning_planner.estimate_coverage(gap_report=report)

    assert isinstance(scores, dict) and scores
    for topic, topic_scores in scores.items():
        assert isinstance(topic, str)
        assert isinstance(topic_scores, dict)
        assert 0.0 <= topic_scores["gap_ratio"] <= 1.0


@pytest.mark.asyncio
async def test_run_learning_roadmap_wires_planning_and_ingestion(brain):
    brain.web_learner.ingest_batch = AsyncMock(return_value={"learned": 2, "quarantined": 0, "skipped": 0})
    report = _make_gap_report(incorrect=1, known=1)
    brain.gap_assessor.record_report(report)

    result = await brain.run_learning_roadmap(max_topics=3)
    assert "plan" in result and "ingestion" in result
    brain.web_learner.ingest_batch.assert_called_once()
    called_topics, kw = brain.web_learner.ingest_batch.call_args
    assert isinstance(called_topics[0], list) and kw.get("topic_weights") is not None
    state = brain.get_state()
    assert isinstance(state["learning_roadmap"], dict)


@pytest.mark.asyncio
async def test_run_learning_roadmap_no_op_without_gaps(brain):
    brain.web_learner.ingest_batch = AsyncMock()
    # No report recorded -> no gaps to plan for.
    brain.gap_assessor._history = []  # type: ignore[attr-defined]

    result = await brain.run_learning_roadmap()
    brain.web_learner.ingest_batch.assert_not_called()
    # No gaps: the planner returns an empty plan and skips ingestion.
    assert result["plan"]["total_planned_topics"] == 0
    assert result["ingestion"] is None


@pytest.mark.asyncio
async def test_run_learning_roadmap_all_known_gets_zero_weight(brain):
    """Topics with no failures get zero priority and zero weight, but the
    plan still records the scorecard so the roadmap stays inspectable."""
    brain.web_learner.ingest_batch = AsyncMock(return_value={"learned": 0})
    brain.gap_assessor.record_report(_make_gap_report(known=5))

    result = await brain.run_learning_roadmap()
    topics = [item["topic"] for item in result["plan"]["items"]]
    assert "mathematics" in topics
    math_item = next(item for item in result["plan"]["items"] if item["topic"] == "mathematics")
    assert math_item["weight"] == 0.0
