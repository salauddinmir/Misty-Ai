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
