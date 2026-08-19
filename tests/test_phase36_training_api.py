"""
Phase 36: authorized web-learning API route tests.

Covers the three security guarantees of the endpoint:
1. The training API key gate (401 for missing/wrong keys, refusal when the
   deployment key is unset)
2. The per-client sliding-window rate limiter (429 after the limit)
3. End-to-end batch ingestion through the route (report bubbles up from
   WebSearchLearner.ingest_batch)
"""

import importlib
import os
import unittest
from unittest import mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

import apps.api.routes.training as training_module
from apps.api.routes.training import _rate_windows
from brain.core.brain import Brain

VALID_KEY = "misty-secret-key-36"
EMPTY_REPORT = {
    "topics": [],
    "learned": [],
    "quarantined": [],
    "skipped": [],
    "cross_topic_conflicts": [],
}


def _reload_with_key(key: str | None) -> object:
    """Module reads MISTY_TRAINING_API_KEY at import time — fix the env and
    reload so each test configuration is exercised in isolation."""
    if key is None:
        os.environ.pop("MISTY_TRAINING_API_KEY", None)
    else:
        os.environ["MISTY_TRAINING_API_KEY"] = key
    module = importlib.reload(training_module)
    _rate_windows.clear()
    return module


def _client(module: object) -> TestClient:
    """Fresh FastAPI app mounting the reloaded module's router, with a fake
    app.state.brain exactly like the lifespan in apps/api/main.py."""
    app = FastAPI()
    app.include_router(module.router, prefix="")
    app.state.brain = Brain()
    return TestClient(app)


def _ingest_mock(report: dict | None = None) -> mock._patch:
    return mock.patch(
        "brain.knowledge.web_learning.WebSearchLearner.ingest_batch",
        return_value=report if report is not None else EMPTY_REPORT,
    )


class TestWebLearnApiKey(unittest.TestCase):
    """Key gate behaviour."""

    def test_missing_key_rejected(self) -> None:
        module = _reload_with_key(VALID_KEY)
        with _client(module) as client:
            response = client.post(
                "/api/training/web_learn", json={"topics": ["satellite"]}
            )
            self.assertEqual(response.status_code, 401)
            self.assertIn("missing", response.json()["detail"].lower())

    def test_wrong_key_rejected(self) -> None:
        module = _reload_with_key(VALID_KEY)
        with _client(module) as client:
            response = client.post(
                "/api/training/web_learn",
                json={"topics": ["satellite"]},
                headers={"X-Misty-Training-Key": "wrong-key"},
            )
            self.assertEqual(response.status_code, 401)

    def test_correct_key_accepted_for_batch(self) -> None:
        module = _reload_with_key(VALID_KEY)
        with _client(module) as client:
            with _ingest_mock():
                response = client.post(
                    "/api/training/web_learn",
                    json={"topics": ["satellite"]},
                    headers={"X-Misty-Training-Key": VALID_KEY},
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["topics_requested"], ["satellite"])

    def test_unset_key_refuses_everything(self) -> None:
        module = _reload_with_key(None)
        with _client(module) as client:
            response = client.post(
                "/api/training/web_learn",
                json={"topics": ["satellite"]},
                headers={"X-Misty-Training-Key": VALID_KEY},
            )
            self.assertEqual(response.status_code, 401)
            self.assertIn("not configured", response.json()["detail"])


class TestRateLimiting(unittest.TestCase):
    """Sliding-window rate limiting by client."""

    def test_exceeding_limit_returns_429(self) -> None:
        module = _reload_with_key(VALID_KEY)
        with _client(module) as client:
            headers = {"X-Misty-Training-Key": VALID_KEY}
            payload = {"topics": ["satellite"]}
            with _ingest_mock():
                # Default window: 10 per 60s. The 11th request must trip the
                # limiter (client ip is 127.0.0.1 on TestClient).
                for _ in range(10):
                    response = client.post(
                        "/api/training/web_learn", json=payload, headers=headers
                    )
                    self.assertEqual(response.status_code, 200)
                response = client.post(
                    "/api/training/web_learn", json=payload, headers=headers
                )
                self.assertEqual(response.status_code, 429)

    def test_different_clients_have_separate_windows(self) -> None:
        module = _reload_with_key(VALID_KEY)
        with _client(module) as client:
            payload = {"topics": ["satellite"]}
            with _ingest_mock():
                # Exhaust the window for the first client identity.
                for _ in range(10):
                    client.post(
                        "/api/training/web_learn",
                        json=payload,
                        headers={
                            "X-Misty-Training-Key": VALID_KEY,
                            "X-Forwarded-For": "203.0.113.10",
                        },
                    )
                # A second client identity still gets through.
                response = client.post(
                    "/api/training/web_learn",
                    json=payload,
                    headers={
                        "X-Misty-Training-Key": VALID_KEY,
                        "X-Forwarded-For": "198.51.100.5",
                    },
                )
                self.assertEqual(response.status_code, 200)


class TestRequestValidation(unittest.TestCase):
    """Bad payloads get 400; good payloads reach the learner with weights."""

    def test_empty_topics_rejected(self) -> None:
        module = _reload_with_key(VALID_KEY)
        with _client(module) as client:
            response = client.post(
                "/api/training/web_learn",
                json={"topics": []},
                headers={"X-Misty-Training-Key": VALID_KEY},
            )
            self.assertEqual(response.status_code, 400)

    def test_topic_weights_forwarded(self) -> None:
        module = _reload_with_key(VALID_KEY)
        with _client(module) as client:
            with _ingest_mock() as mocked:
                response = client.post(
                    "/api/training/web_learn",
                    json={
                        "topics": ["satellite", "lighthouse"],
                        "topic_weights": {"satellite": 2.0, "lighthouse": 0.5},
                    },
                    headers={"X-Misty-Training-Key": VALID_KEY},
                )
                self.assertEqual(response.status_code, 200)
                args, kwargs = mocked.call_args
                self.assertEqual(args[0], ["satellite", "lighthouse"])
                self.assertEqual(
                    kwargs["topic_weights"], {"satellite": 2.0, "lighthouse": 0.5}
                )

    def test_invalid_json_rejected(self) -> None:
        module = _reload_with_key(VALID_KEY)
        with _client(module) as client:
            response = client.post(
                "/api/training/web_learn",
                content="not json",
                headers={"X-Misty-Training-Key": VALID_KEY},
            )
            self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
