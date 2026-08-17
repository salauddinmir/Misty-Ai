"""
Phase 10: actuator control REST API.

POST /api/actuators/commands
    body: [{"action": "move", "magnitude": 0.4, "duration": 2.0,
            "direction": 0.0}]
    Executes motor commands through the safety layer. With no hardware
    driver configured (default), commands execute as dry runs so the
    brain logic can be validated off-robot.

POST /api/actuators/e_stop
    Engages the sticky emergency stop — blocks all movement until
    cleared.

POST /api/actuators/clear_e_stop
    Disengages the emergency stop.

GET  /api/actuators/status
    Returns safety-layer state and the recent command history.

The robot-side developer injects a real motor driver into
``brain.actuators`` before deploying on hardware; every command is
still validated by the same safety layer.
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from brain.actuators import MotorCommand

router = APIRouter(prefix="/actuators", tags=["actuators"])


class CommandRequest(BaseModel):
    action: str = Field(..., min_length=1, max_length=32)
    magnitude: float = 0.0
    duration: float = Field(default=1.0, ge=0.0, le=300.0)
    direction: float = 0.0
    metadata: dict = Field(default_factory=dict)


@router.post("/commands")
async def execute_commands(request: Request, body: list[CommandRequest]) -> dict:
    brain = request.app.state.brain
    results = []
    for item in body:
        command = MotorCommand(
            action=item.action,
            magnitude=item.magnitude,
            duration=item.duration,
            direction=item.direction,
            metadata=item.metadata,
        )
        outcome = brain.actuators.execute(command)
        results.append(
            {
                "command_id": outcome.command_id,
                "status": outcome.status.value,
                "reason": outcome.reason,
                "applied": {
                    "action": outcome.applied.action,
                    "magnitude": outcome.applied.magnitude,
                    "duration": outcome.applied.duration,
                    "direction": outcome.applied.direction,
                }
                if outcome.applied
                else None,
            }
        )
    return {"executed": len(results), "results": results}


@router.post("/e_stop")
async def engage_e_stop(request: Request) -> dict:
    brain = request.app.state.brain
    brain.actuators.emergency_stop()
    return {"e_stop": True}


@router.post("/clear_e_stop")
async def clear_e_stop(request: Request) -> dict:
    brain = request.app.state.brain
    brain.actuators.safety.clear_e_stop()
    return {"e_stop": False}


@router.get("/status")
async def actuator_status(request: Request) -> dict:
    brain = request.app.state.brain
    bridge = brain.actuators
    return {
        "e_stop": bridge.safety.e_stop_engaged,
        "limits": {
            "max_speed": bridge.safety.max_speed,
            "max_duration": bridge.safety.max_duration,
            "max_accel": bridge.safety.max_accel,
            "max_commands_per_second": bridge.safety.max_commands_per_second,
        },
        "history": [
            {
                "status": r.status.value,
                "command_id": r.command_id,
                "reason": r.reason,
                "timestamp": r.timestamp,
            }
            for r in bridge.history[-50:]
        ],
    }
