"""Tests for the bounded autonomous inner loop."""

import asyncio

import pytest

from brain.cognition import AutonomousInnerLoop, InnerLoopConfig


@pytest.mark.asyncio
async def test_inner_loop_respects_tick_budget() -> None:
    calls: list[int] = []

    async def tick() -> None:
        calls.append(1)

    loop = AutonomousInnerLoop(
        tick,
        InnerLoopConfig(interval_seconds=0.0, max_ticks=3, max_tick_seconds=0.2),
    )

    await loop.run()

    assert len(calls) == 3
    assert loop.tick_count == 3
    assert loop.last_error is None


@pytest.mark.asyncio
async def test_inner_loop_isolates_tick_errors() -> None:
    async def tick() -> None:
        raise RuntimeError("test failure")

    loop = AutonomousInnerLoop(
        tick,
        InnerLoopConfig(interval_seconds=0.0, max_ticks=1, max_tick_seconds=0.2),
    )

    await loop.run()

    assert loop.tick_count == 1
    assert loop.last_error == "RuntimeError: test failure"


@pytest.mark.asyncio
async def test_inner_loop_can_be_cancelled() -> None:
    started = asyncio.Event()

    async def tick() -> None:
        started.set()
        await asyncio.sleep(10)

    loop = AutonomousInnerLoop(
        tick,
        InnerLoopConfig(interval_seconds=0.0, max_tick_seconds=20.0),
    )
    task = asyncio.create_task(loop.run())
    await started.wait()
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task
