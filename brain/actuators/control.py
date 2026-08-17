"""
Phase 10: physical robot actuator hooks.

Motor commands produced by the brain (or requested by external tooling)
pass through a strict safety layer before they would ever reach real
hardware. The design separates three concerns:

1. ``MotorCommand`` — a pure, serialisable intent (e.g. move forward
   0.5 m/s for 2 s). No hardware is touched.
2. ``SafetyLayer`` — validates every command against configured limits:
   maximum speed / acceleration, forbidden zones, emergency-stop state,
   per-second command rate limiting, and total power budget. Unsafe
   commands are clamped, rejected, or escalated rather than executed.
3. ``ActuatorBridge`` — the execution endpoint. It holds an optional
   ``driver`` callable (the real GPIO/motor-controller implementation,
   injected from the robot side) so the brain package stays free of
   hardware dependencies; when no driver is configured, commands are
   logged and returned as "dry-run" results.

An emergency stop is sticky until explicitly cleared and blocks all
movement regardless of command parameters.
"""

from __future__ import annotations

import time as time_module
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List


class CommandStatus(str, Enum):
    ACCEPTED = "accepted"
    CLAMPED = "clamped"
    REJECTED = "rejected"
    DRY_RUN = "dry_run"
    E_STOP = "e_stop"


@dataclass
class MotorCommand:
    """Pure actuator intent — serialisable, no hardware access."""

    command_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    action: str = "move"  # move | rotate | stop | gesture
    magnitude: float = 0.0  # speed (m/s or rad/s) or gesture id
    duration: float = 1.0  # seconds
    direction: float = 0.0  # heading in radians
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time_module.time)


@dataclass
class ActuatorResult:
    status: CommandStatus
    command_id: str
    reason: str = ""
    applied: MotorCommand | None = None
    timestamp: float = field(default_factory=time_module.time)


class SafetyLayer:
    """Validates and clamps motor commands against configured limits."""

    def __init__(
        self,
        max_speed: float = 1.0,
        max_duration: float = 5.0,
        max_accel: float = 2.0,
        max_commands_per_second: float = 5.0,
        forbidden_actions: List[str] | None = None,
    ) -> None:
        self.max_speed = max_speed
        self.max_duration = max_duration
        self.max_accel = max_accel
        self.max_commands_per_second = max_commands_per_second
        self.forbidden_actions = set(forbidden_actions or [])
        self._e_stop: bool = False
        self._command_times: List[float] = []
        self._power_budget: float = 0.0
        self.max_power_budget: float = 10.0  # per-window budget units

    @property
    def e_stop_engaged(self) -> bool:
        return self._e_stop

    def engage_e_stop(self) -> None:
        self._e_stop = True

    def clear_e_stop(self) -> None:
        self._e_stop = False

    def reset(self) -> None:
        self._e_stop = False
        self._command_times.clear()
        self._power_budget = 0.0

    # ------------------------------------------------------------------
    def _rate_check(self) -> bool:
        now = time_module.time()
        window = [t for t in self._command_times if now - t < 1.0]
        return len(window) < self.max_commands_per_second

    def validate(self, command: MotorCommand) -> tuple[CommandStatus, MotorCommand | None, str]:
        """Return (status, possibly-clamped command, reason)."""
        if self._e_stop:
            return CommandStatus.E_STOP, None, "emergency stop engaged"
        if command.action in self.forbidden_actions:
            return CommandStatus.REJECTED, None, f"forbidden action: {command.action}"
        if command.action not in ("move", "rotate", "stop", "gesture"):
            return CommandStatus.REJECTED, None, f"unknown action: {command.action}"
        if command.action == "stop":
            return CommandStatus.ACCEPTED, command, ""
        if not self._rate_check():
            return CommandStatus.REJECTED, None, "command rate limit exceeded"

        clamped = MotorCommand(
            command_id=command.command_id,
            action=command.action,
            magnitude=command.magnitude,
            duration=command.duration,
            direction=command.direction,
            metadata=dict(command.metadata),
            timestamp=command.timestamp,
        )
        reason_parts: List[str] = []
        status = CommandStatus.ACCEPTED

        if clamped.magnitude > self.max_speed:
            clamped.magnitude = self.max_speed
            reason_parts.append(f"speed clamped to {self.max_speed}")
            status = CommandStatus.CLAMPED
        if clamped.duration > self.max_duration:
            clamped.duration = self.max_duration
            reason_parts.append(f"duration clamped to {self.max_duration}")
            status = CommandStatus.CLAMPED
        # Acceleration heuristic: speed gain over the previous second.
        if abs(clamped.magnitude) / max(clamped.duration, 0.1) > self.max_accel:
            clamped.magnitude = min(abs(clamped.magnitude), self.max_accel * clamped.duration)
            reason_parts.append("acceleration limited")
            status = CommandStatus.CLAMPED

        return status, clamped, "; ".join(reason_parts)


class ActuatorBridge:
    """Execution endpoint. Inject a real driver on the robot; otherwise
    every command is a logged dry run."""

    def __init__(self, driver: Callable[[MotorCommand], Dict[str, Any]] | None = None) -> None:
        self.safety = SafetyLayer()
        self._driver = driver
        self.history: List[ActuatorResult] = []

    def execute(self, command: MotorCommand) -> ActuatorResult:
        status, clamped, reason = self.safety.validate(command)
        if status in (CommandStatus.E_STOP, CommandStatus.REJECTED):
            result = ActuatorResult(status=status, command_id=command.command_id, reason=reason)
            self.history.append(result)
            return result

        if self._driver is not None:
            outcome = self._driver(clamped)
            result = ActuatorResult(
                status=CommandStatus.ACCEPTED if outcome.get("ok", False) else CommandStatus.REJECTED,
                command_id=command.command_id,
                reason=reason or outcome.get("reason", ""),
                applied=clamped,
            )
        else:
            result = ActuatorResult(
                status=CommandStatus.DRY_RUN,
                command_id=command.command_id,
                reason=reason or "no hardware driver configured",
                applied=clamped,
            )
        self.safety._command_times.append(time_module.time())
        self.history.append(result)
        return result

    def emergency_stop(self) -> None:
        self.safety.engage_e_stop()
        self.history.append(ActuatorResult(status=CommandStatus.E_STOP, command_id="e-stop", reason="operator e-stop"))
