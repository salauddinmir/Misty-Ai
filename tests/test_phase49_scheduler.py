"""
Phase 49 Tests: Autonomous Learning Scheduler.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from brain.core.brain import Brain
from brain.learning.autonomous_scheduler import AutonomousScheduler


def _fresh_brain():
    brain = Brain()
    # Mock components to avoid real web/network I/O
    brain.learning_planner = MagicMock()
    brain.web_learner = MagicMock()
    brain.web_learner.ingest = AsyncMock()
    brain.gap_assessor = MagicMock()
    brain.gap_assessor.last_report = MagicMock(return_value=None)
    return brain


@pytest.mark.asyncio
async def test_scheduler_initialization():
    brain = _fresh_brain()
    scheduler = AutonomousScheduler(brain)
    summary = scheduler.summary()
    assert summary["enabled"] is True
    assert summary["total_topics_learned"] == 0
    assert len(summary["recent_events"]) == 0


@pytest.mark.asyncio
async def test_scheduler_triggers_planning_on_cooldown():
    brain = _fresh_brain()
    scheduler = AutonomousScheduler(brain)

    # Force planning cooldown to expire
    scheduler._last_plan_time = 0.0

    # Tick
    await scheduler.tick()

    # Verify planner was called
    brain.learning_planner.plan_next_topics.assert_called_once()
    assert any(e.action == "plan" for e in scheduler._events)


@pytest.mark.asyncio
async def test_scheduler_triggers_learning_on_cooldown():
    brain = _fresh_brain()
    scheduler = AutonomousScheduler(brain)

    # Mock a plan with one topic
    mock_item = MagicMock()
    mock_item.topic = "Quantum Physics"
    mock_plan = MagicMock()
    mock_plan.items = [mock_item]
    brain.learning_planner.last_plan.return_value = mock_plan

    # Mock successful ingest
    mock_result = MagicMock()
    mock_result.facts_stored = 3
    brain.web_learner.ingest.return_value = mock_result

    # Force learning cooldown to expire
    scheduler._last_learn_time = 0.0

    # Tick
    await scheduler.tick()

    # Verify learning was triggered
    brain.web_learner.ingest.assert_called_once_with("Quantum Physics", max_facts=6)
    summary = scheduler.summary()
    assert summary["total_topics_learned"] == 1
    assert any(e.action == "learn" and e.topic == "Quantum Physics" for e in scheduler._events)


@pytest.mark.asyncio
async def test_scheduler_skips_learning_if_no_plan():
    brain = _fresh_brain()
    scheduler = AutonomousScheduler(brain)

    # Mock no plan
    brain.learning_planner.last_plan.return_value = None

    # Force learning cooldown to expire
    scheduler._last_learn_time = 0.0

    # Tick
    await scheduler.tick()

    # Verify learning NOT triggered
    brain.web_learner.ingest.assert_not_called()
    assert scheduler._total_topics_learned == 0


@pytest.mark.asyncio
async def test_scheduler_handles_learning_failure():
    brain = _fresh_brain()
    scheduler = AutonomousScheduler(brain)

    # Mock a plan
    mock_item = MagicMock()
    mock_item.topic = "Failing Topic"
    mock_plan = MagicMock()
    mock_plan.items = [mock_item]
    brain.learning_planner.last_plan.return_value = mock_plan

    # Mock failure
    brain.web_learner.ingest.side_effect = Exception("Network timeout")

    # Force learning cooldown to expire
    scheduler._last_learn_time = 0.0

    # Tick
    await scheduler.tick()

    # Verify failure logged
    summary = scheduler.summary()
    assert summary["total_topics_learned"] == 0
    event = next(e for e in scheduler._events if e.action == "learn")
    assert event.success is False
    assert "Network timeout" in event.detail


@pytest.mark.asyncio
async def test_brain_reflection_tick_triggers_scheduler():
    brain = Brain()
    brain.autonomous_scheduler = MagicMock()
    brain.autonomous_scheduler.tick = AsyncMock()

    await brain.autonomous_reflection_tick()

    brain.autonomous_scheduler.tick.assert_called_once()


@pytest.mark.asyncio
async def test_api_state_includes_autonomous_learning():
    brain = Brain()
    state = brain.get_state()
    assert "autonomous_learning" in state
    assert state["autonomous_learning"]["enabled"] is True
