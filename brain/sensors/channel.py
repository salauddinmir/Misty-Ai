"""
Phase 9: hardware sensor abstraction.

Sensors are any source of structured, non-linguistic observations:
distance sensors, temperature probes, motion detectors, GPIO buttons,
camera snapshots, etc. Each reading is normalised into a
`SensorEvent` and forwarded to the brain as a structured percept,
where it becomes an OBSERVE-phase input parallel to language input.

The design is transport-agnostic:

- ``SensorHub`` is the in-process registry: call ``register(sensor)``
  with any object exposing ``read() -> SensorReading`` and the hub
  polls or reacts to it.
- ``record_event()`` pushes a ``SensorEvent`` onto an event channel.
- ``Brain.process_sensor_event()`` converts an event into the same
  cognitive cycle as a typed sentence would (e.g. the event
  ``{"sensor": "distance", "value": 0.35}`` is processed as the
  statement ``"sensor distance 0.35"`` so the brain learns about the
  world through its senses), and logs the percept in the world model.

A REST/WebSocket bridge for Raspberry Pi GPIO, MQTT, or any other
backend simply calls ``record_event()``; the brain side stays pure
Python with no external dependencies.
"""

from __future__ import annotations

import time as time_module
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class SensorReading:
    """A single raw sample from a sensor."""

    sensor_id: str
    value: float
    unit: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time_module.time)


@dataclass
class SensorEvent:
    """Normalised percept pushed into the brain's cognitive cycle."""

    event_id: str
    sensor_id: str
    event_type: str  # e.g. "distance", "temperature", "motion", "button"
    value: float
    unit: str = ""
    text_input: str = ""  # natural-language rendering for the brain
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time_module.time)


class Sensor:
    """Minimal sensor interface: anything with a read() method works."""

    def __init__(self, sensor_id: str, event_type: str, unit: str = "") -> None:
        self.sensor_id = sensor_id
        self.event_type = event_type
        self.unit = unit

    def read(self) -> SensorReading:
        raise NotImplementedError


class SensorHub:
    """Registry of sensors plus an event channel.

    Sensors are polled via ``tick()`` (call it each cycle from the host
    loop), and any event pushed through ``record_event()`` is queued for
    the brain. The hub keeps a bounded history so memory stays limited.
    """

    def __init__(self, max_history: int = 200) -> None:
        self._sensors: Dict[str, Sensor] = {}
        self._queue: List[SensorEvent] = []
        self._history: List[SensorEvent] = []
        self.max_history = max_history

    def register(self, sensor: Sensor) -> None:
        self._sensors[sensor.sensor_id] = sensor

    @property
    def sensors(self) -> Dict[str, Sensor]:
        return dict(self._sensors)

    @property
    def queue(self) -> List[SensorEvent]:
        return list(self._queue)

    @property
    def history(self) -> List[SensorEvent]:
        return list(self._history)

    def record_event(self, event: SensorEvent) -> None:
        self._queue.append(event)
        self._history.append(event)
        if len(self._history) > self.max_history:
            self._history = self._history[-self.max_history :]

    def make_event(
        self,
        sensor_id: str,
        reading: SensorReading,
        text_input: str | None = None,
        metadata: Dict[str, Any] | None = None,
    ) -> SensorEvent:
        sensor = self._sensors.get(sensor_id)
        event_type = sensor.event_type if sensor else "reading"
        unit = sensor.unit if sensor else reading.unit
        return SensorEvent(
            event_id=uuid.uuid4().hex[:8],
            sensor_id=sensor_id,
            event_type=event_type,
            value=reading.value,
            unit=unit,
            text_input=text_input or f"sensor {event_type} {reading.value}",
            metadata={**reading.metadata, **(metadata or {})},
            timestamp=reading.timestamp,
        )

    def tick(self) -> List[SensorEvent]:
        """Poll every registered sensor and enqueue fresh readings."""
        events: List[SensorEvent] = []
        for sensor in self._sensors.values():
            try:
                reading = sensor.read()
            except Exception:
                continue
            event = self.make_event(sensor.sensor_id, reading)
            self.record_event(event)
            events.append(event)
        return events

    def latest(self, sensor_id: str) -> SensorEvent | None:
        for event in reversed(self._history):
            if event.sensor_id == sensor_id:
                return event
        return None

    def reset(self) -> None:
        self._queue.clear()
        self._history.clear()
