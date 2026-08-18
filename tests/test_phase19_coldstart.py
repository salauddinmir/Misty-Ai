"""Phase 19: Render cold-start connection-drop regression guards.

The user observed "Unable to connect to MISTY brain" right after a deploy,
when Render was spinning up a fresh instance. Two mechanisms prevent this:

1. The application lifespan now runs a warmup cognitive cycle during
   startup and exposes readiness through GET /health
   ({"status": "warm", "ready": true} once warmed).
2. If the brain is not attached yet (early boot), POST /api/chat answers
   503 with a Retry-After header instead of raising an unhandled error
   that drops the TCP connection.
"""

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app


@pytest.fixture(name="client")
def client() -> TestClient:
    with TestClient(app) as client:
        yield client


def test_health_reports_warm_after_startup(client: TestClient) -> None:
    """After the lifespan warmup, /health reports ready == True."""
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("ready") is True
    assert payload.get("status") in {"warm", "cold"}


def test_first_chat_after_boot_succeeds(client: TestClient) -> None:
    """A chat message immediately after boot must not fail with a dropped
    connection; the lazy warmup path handles it inside the handler."""
    response = client.post("/api/chat", json={"message": "হেলো"})
    assert response.status_code == 200
    assert response.json()["response"]


def test_warmup_flag_set(client: TestClient) -> None:
    """The first chat turn completes and leaves warmup_complete True."""
    client.post("/api/chat", json={"message": "hi"})
    assert getattr(app.state, "warmup_complete", False) is True
