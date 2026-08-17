"""Bounded autonomous cognition scheduler.

The scheduler is deliberately deterministic and budgeted. It does not browse,
write unverified knowledge, or run hidden language generation by itself.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Awaitable, Callable


@dataclass(frozen=True)
class InnerLoopConfig:
    interval_seconds: float = 60.0
    max_ticks: int = 0
    max_tick_seconds: float = 1.0


class AutonomousInnerLoop:
    """Run safe internal reflection at a controlled cadence."""

    def __init__(
        self,
        tick: Callable[[], Awaitable[None]],
        config: InnerLoopConfig | None = None,
    ) -> None:
        self.tick = tick
        self.config = config or InnerLoopConfig()
        self.tick_count = 0
        self.last_tick_at: float | None = None
        self.last_error: str | None = None

    async def run(self) -> None:
        """Run until cancelled or the configured tick budget is exhausted."""
        while self.config.max_ticks <= 0 or self.tick_count < self.config.max_ticks:
            started = time.monotonic()
            try:
                await asyncio.wait_for(self.tick(), timeout=self.config.max_tick_seconds)
                self.last_error = None
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # pragma: no cover - defensive worker boundary
                self.last_error = f"{type(exc).__name__}: {exc}"
            self.tick_count += 1
            self.last_tick_at = time.time()
            elapsed = time.monotonic() - started
            await asyncio.sleep(max(0.0, self.config.interval_seconds - elapsed))
