"""Tests for MISTY's explicit self-model."""

from brain.cognition import SelfModel


def test_self_model_has_identity_and_capabilities() -> None:
    model = SelfModel()

    assert model.knows_identity("name", "MISTY")
    assert model.knows_identity("creator", "Pixline Incorporate")
    assert "mathematics" in model.capabilities
    assert model.capability_text("physics")


def test_self_model_tracks_goals_and_beliefs() -> None:
    model = SelfModel()
    model.add_goal("learn Bengali literature")
    model.learn_belief("user", "preferred_language", "Bengali", 0.9)

    summary = model.summary()

    assert summary["active_goals"] == ["learn Bengali literature"]
    assert summary["learned_belief_count"] == 1


def test_prediction_error_updates_self_uncertainty() -> None:
    model = SelfModel()
    initial = model.uncertainty

    model.update_uncertainty(1.0)

    assert model.uncertainty > initial
    assert model.confidence < 0.5
