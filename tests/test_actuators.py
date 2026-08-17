"""
Phase 10 tests: physical robot actuator hooks — SafetyLayer clamps and
rejects commands, the emergency stop is sticky, dry runs work without a
hardware driver, and the REST bridge is wired through the brain.
"""

from fastapi import FastAPI

from apps.api.routes.actuators import router as actuators_router
from brain.actuators import (
    ActuatorBridge,
    CommandStatus,
    MotorCommand,
    SafetyLayer,
)
from brain.core.brain import Brain

# -----------------------------------------------------------------------
# SafetyLayer
# -----------------------------------------------------------------------


class TestSafetyLayer:
    def test_accepts_safe_move(self) -> None:
        safety = SafetyLayer(max_speed=1.0)
        status, clamped, reason = safety.validate(MotorCommand(action="move", magnitude=0.5, duration=1.0))
        assert status == CommandStatus.ACCEPTED
        assert clamped is not None and clamped.magnitude == 0.5
        assert reason == ""

    def test_clamps_speed_and_duration(self) -> None:
        safety = SafetyLayer(max_speed=1.0, max_duration=2.0)
        status, clamped, reason = safety.validate(MotorCommand(action="move", magnitude=5.0, duration=10.0))
        assert status == CommandStatus.CLAMPED
        assert clamped is not None
        assert clamped.magnitude == 1.0
        assert clamped.duration == 2.0
        assert "clamped" in reason

    def test_rejects_forbidden_action(self) -> None:
        safety = SafetyLayer(forbidden_actions=["spin_fast"])
        status, _, reason = safety.validate(MotorCommand(action="spin_fast", magnitude=1.0))
        assert status == CommandStatus.REJECTED
        assert "forbidden" in reason

    def test_rejects_unknown_action(self) -> None:
        safety = SafetyLayer()
        status, _, reason = safety.validate(MotorCommand(action="fly", magnitude=1.0))
        assert status == CommandStatus.REJECTED
        assert "unknown action" in reason

    def test_stop_action_always_ok(self) -> None:
        safety = SafetyLayer(max_speed=0.01)
        status, clamped, _ = safety.validate(MotorCommand(action="stop"))
        assert status == CommandStatus.ACCEPTED
        assert clamped is not None

    def test_rate_limit(self) -> None:
        safety = SafetyLayer(max_commands_per_second=2.0)
        for _ in range(2):
            safety._command_times.append(__import__("time").time())
        status, _, reason = safety.validate(MotorCommand(action="move", magnitude=0.5))
        assert status == CommandStatus.REJECTED
        assert "rate limit" in reason

    def test_e_stop_blocks_everything(self) -> None:
        safety = SafetyLayer()
        safety.engage_e_stop()
        assert safety.e_stop_engaged
        status, _, reason = safety.validate(MotorCommand(action="move", magnitude=0.1))
        assert status == CommandStatus.E_STOP
        assert "emergency stop" in reason
        # Even stop commands are blocked while e-stop is engaged.
        assert safety.validate(MotorCommand(action="stop"))[0] == CommandStatus.E_STOP
        safety.clear_e_stop()
        assert safety.validate(MotorCommand(action="move", magnitude=0.1))[0] == CommandStatus.ACCEPTED


# -----------------------------------------------------------------------
# ActuatorBridge
# -----------------------------------------------------------------------


class TestActuatorBridge:
    def test_dry_run_without_driver(self) -> None:
        bridge = ActuatorBridge()
        result = bridge.execute(MotorCommand(action="move", magnitude=0.4))
        assert result.status == CommandStatus.DRY_RUN
        assert result.applied is not None
        assert len(bridge.history) == 1

    def test_driver_injection(self) -> None:
        calls: list = []

        def driver(cmd: MotorCommand) -> dict:
            calls.append(cmd)
            return {"ok": True}

        bridge = ActuatorBridge(driver=driver)
        result = bridge.execute(MotorCommand(action="rotate", magnitude=0.5, direction=1.5))
        assert result.status == CommandStatus.ACCEPTED
        assert len(calls) == 1
        assert calls[0].direction == 1.5

    def test_driver_failure_rejected(self) -> None:
        bridge = ActuatorBridge(driver=lambda cmd: {"ok": False, "reason": "stall"})
        result = bridge.execute(MotorCommand(action="move", magnitude=0.4))
        assert result.status == CommandStatus.REJECTED
        assert result.reason == "stall"

    def test_e_stop_history_and_block(self) -> None:
        bridge = ActuatorBridge()
        bridge.emergency_stop()
        bridge.execute(MotorCommand(action="move", magnitude=0.4))
        assert all(r.status == CommandStatus.E_STOP for r in bridge.history[1:])


# -----------------------------------------------------------------------
# Brain wiring
# -----------------------------------------------------------------------


class TestBrainActuatorWiring:
    def test_bridge_attached(self) -> None:
        brain = Brain()
        assert isinstance(brain.actuators, ActuatorBridge)


# -----------------------------------------------------------------------
# REST API
# -----------------------------------------------------------------------


def _build_app() -> FastAPI:
    app = FastAPI()
    brain = Brain()
    app.state.brain = brain
    app.include_router(actuators_router, prefix="/api")
    return app


class TestActuatorApi:
    def test_execute_commands_dry_run(self) -> None:
        from fastapi.testclient import TestClient

        client = TestClient(_build_app())
        response = client.post(
            "/api/actuators/commands",
            json=[{"action": "move", "magnitude": 0.4, "duration": 2.0}],
        )
        assert response.status_code == 200
        data = response.json()
        assert data["executed"] == 1
        assert data["results"][0]["status"] == "dry_run"

    def test_clamping_through_api(self) -> None:
        from fastapi.testclient import TestClient

        client = TestClient(_build_app())
        response = client.post(
            "/api/actuators/commands",
            json=[{"action": "move", "magnitude": 50.0, "duration": 250.0}],
        )
        assert response.status_code == 200
        applied = response.json()["results"][0]["applied"]
        assert applied["magnitude"] <= 1.0
        assert applied["duration"] <= 5.0

    def test_e_stop_cycle(self) -> None:
        from fastapi.testclient import TestClient

        client = TestClient(_build_app())
        assert client.post("/api/actuators/e_stop").status_code == 200
        resp = client.post(
            "/api/actuators/commands",
            json=[{"action": "move", "magnitude": 0.4}],
        )
        assert resp.json()["results"][0]["status"] == "e_stop"
        client.post("/api/actuators/clear_e_stop")
        status = client.get("/api/actuators/status").json()
        assert status["e_stop"] is False
        assert status["limits"]["max_speed"] == 1.0
