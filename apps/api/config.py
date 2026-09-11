"""Centralized runtime configuration for the MISTY API.

The module deliberately uses the standard library instead of a second settings
framework so local SQLite development and Render deployment share one contract.
Secrets remain environment-only and are never serialized into API responses.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


def _positive_float(value: str, default: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _positive_int(value: str, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


@dataclass(frozen=True, slots=True)
class APISettings:
    """Validated, non-secret runtime settings used by the API process."""

    environment: str
    cors_origins: tuple[str, ...]
    allowed_hosts: tuple[str, ...]
    max_request_bytes: int
    llm_timeout_seconds: float
    llm_max_retries: int
    autonomy_enabled: bool

    @classmethod
    def from_environment(cls) -> APISettings:
        environment = os.getenv("MISTY_ENV", "development").strip().casefold() or "development"
        default_origins = (
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        )
        configured_origins = _csv(os.getenv("MISTY_CORS_ORIGINS", ""))
        configured_hosts = _csv(os.getenv("MISTY_ALLOWED_HOSTS", ""))
        return cls(
            environment=environment,
            cors_origins=configured_origins or default_origins,
            allowed_hosts=configured_hosts,
            max_request_bytes=_positive_int(os.getenv("MISTY_MAX_REQUEST_BYTES", "1048576"), 1048576),
            llm_timeout_seconds=_positive_float(os.getenv("MISTY_LLM_TIMEOUT_SECONDS", "30"), 30.0),
            llm_max_retries=_positive_int(os.getenv("MISTY_LLM_MAX_RETRIES", "1"), 1),
            autonomy_enabled=os.getenv("MISTY_AUTONOMY_ENABLED", "true").casefold() == "true",
        )


settings = APISettings.from_environment()
