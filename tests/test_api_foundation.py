"""Regression tests for the P0 API configuration foundation."""

from fastapi.testclient import TestClient

from apps.api.config import APISettings
from apps.api.main import app


def test_settings_parse_environment_overrides(monkeypatch):
    monkeypatch.setenv("MISTY_ENV", "production")
    monkeypatch.setenv("MISTY_CORS_ORIGINS", "https://one.example, https://two.example")
    monkeypatch.setenv("MISTY_ALLOWED_HOSTS", "api.example")
    monkeypatch.setenv("MISTY_MAX_REQUEST_BYTES", "2048")
    monkeypatch.setenv("MISTY_LLM_TIMEOUT_SECONDS", "12.5")
    monkeypatch.setenv("MISTY_LLM_MAX_RETRIES", "3")
    monkeypatch.setenv("MISTY_AUTONOMY_ENABLED", "false")

    settings = APISettings.from_environment()

    assert settings.environment == "production"
    assert settings.cors_origins == ("https://one.example", "https://two.example")
    assert settings.allowed_hosts == ("api.example",)
    assert settings.max_request_bytes == 2048
    assert settings.llm_timeout_seconds == 12.5
    assert settings.llm_max_retries == 3
    assert settings.autonomy_enabled is False


def test_settings_reject_invalid_positive_values_with_defaults(monkeypatch):
    monkeypatch.setenv("MISTY_MAX_REQUEST_BYTES", "-1")
    monkeypatch.setenv("MISTY_LLM_TIMEOUT_SECONDS", "invalid")
    monkeypatch.setenv("MISTY_LLM_MAX_RETRIES", "0")

    settings = APISettings.from_environment()

    assert settings.max_request_bytes == 1048576
    assert settings.llm_timeout_seconds == 30.0
    assert settings.llm_max_retries == 1


def test_health_response_contains_security_headers():
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert response.headers["permissions-policy"] == "camera=(), microphone=(), geolocation=()"


async def _read_schema_migrations(db):
    rows = await db.fetchall("SELECT version, description FROM misty_schema_migrations ORDER BY version")
    return [(row[0], row[1]) for row in rows]


def test_api_returns_request_id_and_rejects_oversized_body(monkeypatch):
    from dataclasses import replace

    from fastapi.testclient import TestClient

    from apps.api.config import settings
    from apps.api.main import app

    monkeypatch.setattr("apps.api.main.settings", replace(settings, max_request_bytes=8))
    with TestClient(app) as client:
        response = client.post("/api/chat", content="123456789")
        assert response.status_code == 413
        assert response.headers["X-Request-ID"]
        assert "request body exceeds" in response.json()["detail"]

        health = client.get("/health")
        assert health.headers["X-Request-ID"]


def test_sqlite_records_baseline_schema_version(tmp_path):
    import asyncio

    from apps.api.database import Database

    db = Database(db_path=str(tmp_path / "schema-version.db"))
    asyncio.run(db.initialize())
    try:
        rows = asyncio.run(_read_schema_migrations(db))
        assert rows == [(1, "baseline schema with cognitive memory and audit persistence")]
        asyncio.run(db.initialize())
        rows_after_reinitialize = asyncio.run(_read_schema_migrations(db))
        assert rows_after_reinitialize == rows
    finally:
        asyncio.run(db.close())
