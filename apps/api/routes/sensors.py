"""
Phase 9: sensor event REST API.

POST /api/sensors/events
    body: [{"sensor_id": "distance", "event_type": "distance",
            "value": 0.35, "unit": "m"}]
    Pushes hardware sensor readings into the brain's sensor channel,
    which forwards each reading through the cognitive cycle exactly
    like typed language input. This is the bridge endpoint a
    Raspberry Pi (GPIO), MQTT broker, or any other sensor backend
    calls — the brain itself stays dependency-free.

GET /api/sensors/history
    Returns the bounded event history so external tooling can inspect
    what the brain has perceived through its sensors.

POST /api/sensors/register
    body: {"sensor_id": "distance", "event_type": "distance",
           "unit": "m"}
    Registers a new sensor with the sensor hub.
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from brain.sensors import Sensor, SensorReading

router = APIRouter(prefix="/sensors", tags=["sensors"])


class EventRequest(BaseModel):
    sensor_id: str = Field(..., min_length=1, max_length=64)
    event_type: str = Field(..., min_length=1, max_length=64)
    value: float
    unit: str = Field(default="", max_length=16)


class RegisterRequest(BaseModel):
    sensor_id: str = Field(..., min_length=1, max_length=64)
    event_type: str = Field(..., min_length=1, max_length=64)
    unit: str = Field(default="", max_length=16)


@router.post("/events")
async def push_sensor_events(request: Request, body: list[EventRequest]) -> dict:
    """Push one or more sensor readings into the brain."""
    brain = request.app.state.brain
    results = []
    for item in body:
        if item.sensor_id not in brain.sensors.sensors:
            # Auto-register on first reading so ad-hoc devices work.
            brain.sensors.register(Sensor(sensor_id=item.sensor_id, event_type=item.event_type, unit=item.unit))
        sensor = brain.sensors.sensors[item.sensor_id]
        reading = SensorReading(sensor_id=item.sensor_id, value=item.value, unit=item.unit or sensor.unit)
        event = brain.sensors.make_event(item.sensor_id, reading)
        brain.sensors.record_event(event)
        result = brain.process_sensor_event(event)
        results.append(
            {
                "event_id": event.event_id,
                "sensor_id": item.sensor_id,
                "response": result.get("response", ""),
                "intent": result.get("intent", ""),
                "emotional_state": result.get("emotional_state", {}),
                "processing_time": result.get("processing_time", 0.0),
            }
        )
    return {"processed": len(results), "events": results}


@router.post("/register")
async def register_sensor(request: Request, body: RegisterRequest) -> dict:
    """Register a sensor explicitly."""
    brain = request.app.state.brain
    brain.sensors.register(Sensor(sensor_id=body.sensor_id, event_type=body.event_type, unit=body.unit))
    return {"registered": body.sensor_id, "total": len(brain.sensors.sensors)}


@router.get("/history")
async def sensor_history(request: Request) -> dict:
    """Bounded sensor event history."""
    brain = request.app.state.brain
    history = brain.sensors.history
    return {
        "count": len(history),
        "events": [
            {
                "event_id": e.event_id,
                "sensor_id": e.sensor_id,
                "event_type": e.event_type,
                "value": e.value,
                "unit": e.unit,
                "text_input": e.text_input,
                "timestamp": e.timestamp,
            }
            for e in history[-100:]
        ],
    }
