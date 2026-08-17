"""Tests for MISTY's inspectable cognitive workspace primitives."""

from brain.cognition import (
    AppraisalEngine,
    AppraisalEvent,
    CognitiveEvent,
    Evidence,
    GlobalWorkspace,
    HypothesisRecord,
    PerceptionPipeline,
    ThoughtTraceSummary,
)
from brain.emotion.state import EmotionalState


def test_workspace_broadcasts_event_and_returns_bounded_summary() -> None:
    workspace = GlobalWorkspace(capacity=4)
    workspace.reset_cycle(goal="answer")
    workspace.broadcast_event(CognitiveEvent(content="তুমি কী জানো?"))
    workspace.appraise(
        AppraisalEvent(
            trigger="question",
            appraisal="epistemic_demand",
            intensity=0.7,
        )
    )

    summary = workspace.summary()

    assert summary["active_goal"] == "answer"
    assert summary["focus"] == "তুমি কী জানো?"
    assert summary["event_count"] == 1
    assert summary["appraisal_count"] == 1


def test_hypothesis_updates_from_support_and_rejection() -> None:
    hypothesis = HypothesisRecord(
        statement="input is a capability question",
        confidence=0.5,
        uncertainty=0.5,
    )
    hypothesis.add_evidence(Evidence(source="nlu", content="capability", confidence=0.9))
    assert hypothesis.confidence > 0.5
    initial_uncertainty = hypothesis.uncertainty

    hypothesis.mark_tested(False)
    assert hypothesis.status == "rejected"
    assert hypothesis.confidence < 0.9
    assert hypothesis.uncertainty > initial_uncertainty


def test_workspace_selects_best_hypothesis() -> None:
    workspace = GlobalWorkspace()
    workspace.propose(
        HypothesisRecord(
            statement="weak",
            confidence=0.4,
            uncertainty=0.7,
        )
    )
    strong = HypothesisRecord(
        statement="strong",
        confidence=0.85,
        uncertainty=0.15,
    )
    workspace.propose(strong)

    assert workspace.best_hypothesis() is strong
    assert workspace.summary()["best_hypothesis"]["statement"] == "strong"


def test_thought_trace_is_json_safe() -> None:
    trace = ThoughtTraceSummary(
        focus="formula",
        intent="math",
        evidence_count=2,
        hypothesis_count=1,
        confidence=0.8,
        uncertainty=0.2,
        decision="respond",
    )

    assert trace.to_dict()["decision"] == "respond"


def test_appraisal_prioritizes_answer_for_questions() -> None:
    percept = PerceptionPipeline().perceive("তুমি কীভাবে কাজ করো?")
    drives = AppraisalEngine().appraise(percept, EmotionalState())

    assert drives[0].name == "answer"
    assert drives[0].value > drives[1].value


def test_appraisal_prioritizes_protection_for_urgent_input() -> None:
    percept = PerceptionPipeline().perceive("জরুরি বিপদ")
    drives = AppraisalEngine().appraise(percept, EmotionalState())

    assert drives[0].name == "protect"
    assert drives[0].value > 0.7


def test_prediction_error_increases_uncertainty() -> None:
    emotion = EmotionalState(uncertainty=0.2)
    percept = PerceptionPipeline().perceive("নতুন তথ্য")
    AppraisalEngine().appraise(percept, emotion, prediction_error=1.0)

    assert emotion.uncertainty > 0.2
