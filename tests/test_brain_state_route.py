"""Tests for the brain state route exposing Phase-14 tick metrics."""

from fastapi.testclient import TestClient

from apps.api.main import app

client = TestClient(app, raise_server_exceptions=False)


class TestBrainStateRoute:
    """GET /api/brain/state exposes the autonomous tick audit snapshot."""

    def test_state_shape(self) -> None:
        with client:
            response = client.get("/api/brain/state")
        assert response.status_code == 200
        payload = response.json()
        assert isinstance(payload["last_autonomous_tick"], dict)
        for key in ("cycle_count", "working_memory_size", "semantic_facts", "emotional_state"):
            assert key in payload, f"missing key: {key}"

    def test_tick_metrics_present_after_tick(self) -> None:
        """The latest reflection tick snapshot is surfaced through the route.
        The autonomous worker runs on its own schedule in production, so this
        test drives a tick directly when the worker is not enabled."""
        with client:
            brain = client.app.state.brain
            import asyncio

            asyncio.run(brain.autonomous_reflection_tick())
            response = client.get("/api/brain/state")
        payload = response.json()
        tick = payload["last_autonomous_tick"]
        assert tick, "expected at least one autonomous tick before this request"
        required_keys = (
            "tick_index",
            "evidence_budget",
            "evidence_count",
            "elapsed_ms",
            "outcome",
            "quarantined_candidates",
        )
        for key in required_keys:
            assert key in tick, f"missing metric: {key}"
        assert isinstance(tick["quarantined_candidates"], list)
