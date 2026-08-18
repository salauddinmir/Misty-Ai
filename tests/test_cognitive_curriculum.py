import pytest

from brain.knowledge.cognitive_curriculum import (
    COGNITIVE_CURRICULA,
    get_cognitive_curriculum,
    list_cognitive_curricula,
)


def test_cognitive_departments_are_registered():
    assert set(COGNITIVE_CURRICULA) == {
        "reasoning",
        "commonsense",
        "memory",
        "perception",
        "emotion_simulation",
        "self_model_and_planning",
    }
    assert len(list_cognitive_curricula()) == 6


def test_every_cognitive_curriculum_has_units_benchmarks_and_thresholds():
    for curriculum in list_cognitive_curricula():
        assert curriculum.prerequisites
        assert curriculum.units
        assert curriculum.benchmark_ids
        assert curriculum.acceptance
        assert all(0 <= value <= 1 for value in curriculum.acceptance.values())


def test_planning_has_zero_tolerance_for_unsafe_side_effects():
    planning = get_cognitive_curriculum("self_model_and_planning")
    assert planning.acceptance["unsafe_side_effect_without_approval"] == 0.0
    assert "approval-gate" in planning.units


def test_emotion_simulation_does_not_change_fact_confidence():
    emotion = get_cognitive_curriculum("emotion_simulation")
    assert emotion.acceptance["fact_confidence_invariance"] == 1.0


def test_unknown_cognitive_department_has_explicit_error():
    with pytest.raises(ValueError, match="unknown cognitive curriculum department"):
        get_cognitive_curriculum("telepathy")
