"""Tests for the /api/chat/media endpoint (multimodal perception)."""

import base64

import numpy as np
from fastapi.testclient import TestClient

from apps.api.main import app

client = TestClient(app, raise_server_exceptions=False)


def _image_bytes() -> bytes:
    """Tiny 16x16 RGB image as raw PNG via PIL if available."""
    try:
        from io import BytesIO

        from PIL import Image
    except ImportError:
        return b"\x00" * (16 * 16 * 3)
    img = Image.new("RGB", (16, 16), (128, 64, 200))
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _audio_bytes(n_samples: int = 4000, freq: float = 440.0) -> bytes:
    t = np.arange(n_samples) / 16000.0
    samples = (np.sin(2 * np.pi * freq * t) * 0.5).astype(np.float32)
    return samples.tobytes()


class TestMediaEndpoint:
    def test_image_input(self) -> None:
        with client:
            response = client.post(
                "/api/chat/media",
                json={
                    "modality": "image",
                    "data": base64.b64encode(_image_bytes()).decode(),
                    "message": "what do you see",
                },
            )
        assert response.status_code == 200
        payload = response.json()
        assert payload["perception"]["modality"] == "image"
        assert payload["perception"]["fallback"] is False
        assert abs(payload["feature_norm"] - 1.0) < 1e-4
        assert payload["sensory_spikes"] >= 0
        assert isinstance(payload["response"], str)

    def test_audio_input(self) -> None:
        with client:
            response = client.post(
                "/api/chat/media",
                json={
                    "modality": "audio",
                    "data": base64.b64encode(_audio_bytes()).decode(),
                    "sample_rate": 16000,
                },
            )
        assert response.status_code == 200
        payload = response.json()
        assert payload["perception"]["modality"] == "audio"
        assert abs(payload["feature_norm"] - 1.0) < 1e-4

    def test_unknown_modality_fallback(self) -> None:
        with client:
            response = client.post(
                "/api/chat/media",
                json={
                    "modality": "smell",
                    "data": base64.b64encode(b"").decode(),
                },
            )
        assert response.status_code == 200
        payload = response.json()
        assert payload["perception"]["fallback"] is True
        assert "don't recognize" in payload["response"]

    def test_invalid_base64(self) -> None:
        with client:
            # Invalid base64 is rejected with a graceful error response
            # rather than crashing the server.
            response = client.post(
                "/api/chat/media",
                json={"modality": "image", "data": "not-valid-base64!!!"},
            )
        assert response.status_code == 200
        assert response.json()["perception"]["fallback"] is True
        assert "could not be decoded" in response.json()["response"]
