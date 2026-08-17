"""
Phase 9 tests: hardware sensor abstraction — SensorHub, brain wiring,
and the REST sensor event API.
"""

from fastapi import FastAPI

from apps.api.routes.sensors import router as sensors_router
from brain.core.brain import Brain
from brain.sensors import Sensor, SensorEvent, SensorHub, SensorReading

# -----------------------------------------------------------------------
# SensorHub
# -----------------------------------------------------------------------


class _DummySensor(Sensor):
    def __init__(self, sensor_id: str, event_type: str, value: float) -> None:
        super().__init__(sensor_id, event_type)
        self.value = value

    def read(self) -> SensorReading:
        return SensorReading(sensor_id=self.sensor_id, value=self.value)


class TestSensorHub:
    def setup_method(self) -> None:
        self.hub = SensorHub()

    def test_register_and_read(self) -> None:
        self.hub.register(_DummySensor("distance", "distance", 0.35))
        events = self.hub.tick()
        assert len(events) == 1
        assert events[0].value == 0.35
        assert events[0].event_id

    def test_record_event_queue_and_history(self) -> None:
        self.hub.record_event(SensorEvent(event_id="e1", sensor_id="temp", event_type="temperature", value=22.5))
        assert len(self.hub.queue) == 1
        assert self.hub.latest("temp").value == 22.5

    def test_history_bounded(self) -> None:
        for i in range(300):
            self.hub.record_event(SensorEvent(event_id=f"e{i}", sensor_id="m", event_type="motion", value=float(i)))
        assert len(self.hub.history) == 200

    def test_latest_unknown_returns_none(self) -> None:
        assert self.hub.latest("nope") is None

    def test_reset_clears(self) -> None:
        self.hub.record_event(SensorEvent(event_id="e1", sensor_id="m", event_type="motion", value=1.0))
        self.hub.reset()
        assert not self.hub.queue and not self.hub.history

    def test_broken_sensor_skipped(self) -> None:
        class Broken(Sensor):
            def read(self) -> SensorReading:
                raise RuntimeError("boom")

        self.hub.register(Broken("bad", "reading"))
        assert self.hub.tick() == []

    def test_make_event_unknown_sensor(self) -> None:
        reading = SensorReading(sensor_id="unknown", value=0.1)
        event = self.hub.make_event("unknown", reading)
        assert event.event_type == "reading"


# -----------------------------------------------------------------------
# Wiring: brain processes sensor events like language
# -----------------------------------------------------------------------


class TestBrainSensorWiring:
    def test_sensor_hub_attached(self) -> None:
        brain = Brain()
        assert isinstance(brain.sensors, SensorHub)

    def test_sensor_event_runs_cycle(self) -> None:
        brain = Brain()
        event = SensorEvent(
            event_id="e1",
            sensor_id="distance",
            event_type="distance",
            value=0.35,
            text_input="sensor distance 0.35",
        )
        result = brain.process_sensor_event(event)
        assert result.get("response")
        # Percept registered in the world model.
        assert "sensor:distance" in brain.world.entities

    def test_hub_tick_feeds_brain(self) -> None:
        brain = Brain()
        brain.sensors.register(_DummySensor("temp", "temperature", 25.0))
        events = brain.sensors.tick()
        assert len(events) == 1
        brain.process_sensor_event(events[0])
        assert "sensor:temp" in brain.world.entities


# -----------------------------------------------------------------------
# REST API
# -----------------------------------------------------------------------


def _build_app() -> FastAPI:
    app = FastAPI()
    brain = Brain()
    app.state.brain = brain
    app.include_router(sensors_router, prefix="/api")
    return app


class TestSensorApi:
    def test_push_events(self) -> None:
        from fastapi.testclient import TestClient

        client = TestClient(_build_app())
        response = client.post(
            "/api/sensors/events",
            json=[{"sensor_id": "distance", "event_type": "distance", "value": 0.4}],
        )
        assert response.status_code == 200
        data = response.json()
        assert data["processed"] == 1
        assert data["events"][0]["intent"] == "statement"

    def test_register_and_history(self) -> None:
        from fastapi.testclient import TestClient

        client = TestClient(_build_app())
        assert (
            client.post(
                "/api/sensors/register",
                json={"sensor_id": "motion", "event_type": "motion"},
            ).status_code
            == 200
        )
        client.post(
            "/api/sensors/events",
            json=[{"sensor_id": "motion", "event_type": "motion", "value": 1.0}],
        )
        history = client.get("/api/sensors/history").json()
        assert history["count"] >= 1
        assert history["events"][0]["sensor_id"] == "motion"

    def test_push_with_unknown_sensor_auto_registers(self) -> None:
        from fastapi.testclient import TestClient

        client = TestClient(_build_app())
        response = client.post(
            "/api/sensors/events",
            json=[{"sensor_id": "laser", "event_type": "distance", "value": 0.9}],
        )
        assert response.status_code == 200
        assert "laser" in client.app.state.brain.sensors.sensors
