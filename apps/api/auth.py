"""Small, explicit request-authentication boundary for production API routes.

The API can continue to run in local anonymous mode, but production deployments
may set ``MISTY_AUTH_REQUIRED=true`` and provide ``MISTY_SESSION_SECRET``. The
session format is a compact HMAC-signed token with a subject and expiry; no
client-provided user id is trusted when authentication is required.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any

from fastapi import HTTPException, Request

from apps.api.config import settings


def _decode_part(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}")


def _verify_signed_session(token: str, secret: str) -> str:
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("invalid session format")
    encoded_header, encoded_payload, encoded_signature = parts
    signing_input = f"{encoded_header}.{encoded_payload}".encode("ascii")
    expected = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    supplied = _decode_part(encoded_signature)
    if not hmac.compare_digest(expected, supplied):
        raise ValueError("invalid session signature")
    header = json.loads(_decode_part(encoded_header))
    payload: dict[str, Any] = json.loads(_decode_part(encoded_payload))
    if header.get("alg") != "HS256" or header.get("typ") != "MISTY_SESSION":
        raise ValueError("unsupported session token")
    subject = str(payload.get("sub", "")).strip()
    expiry = float(payload.get("exp", 0))
    if not subject or expiry <= time.time():
        raise ValueError("expired or empty session")
    return subject[:128]


def resolve_user_id(request: Request) -> str:
    """Return a trusted tenant subject or the legacy anonymous id.

    ``X-Misty-User-Id`` is intentionally accepted only when auth is disabled;
    this keeps local development and existing fixtures compatible without
    allowing production callers to impersonate another memory namespace.
    """
    if not settings.auth_required:
        header = request.headers.get("x-misty-user-id", "").strip()
        return header[:128] or "anon"

    authorization = request.headers.get("authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.casefold() != "bearer" or not token.strip():
        raise HTTPException(status_code=401, detail="Authentication required.")
    if not settings.session_secret:
        raise HTTPException(status_code=503, detail="Authentication is not configured.")
    try:
        return _verify_signed_session(token.strip(), settings.session_secret)
    except (ValueError, TypeError, json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(status_code=401, detail="Invalid or expired session.") from None
