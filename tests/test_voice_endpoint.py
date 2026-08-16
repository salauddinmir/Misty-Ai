"""Tests for the voice input endpoint (POST /api/chat/voice)."""

import base64
import io
import struct
import wave
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app


def _synthetic_wav(samples: list[float], sample_rate: int = 16000) -> str:
    """Build a minimal mono 16-bit WAV buffer and return it base64-encoded."""
    pcm = b"".join(struct.pack("<h", int(max(-1.0, min(1.0, s)) * 32767)) for s in samples)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm)
    return base64.b64encode(buffer.getvalue()).decode()


@pytest.fixture(autouse=True)
def _wire_mock_brain():
    """Point app state at a mock brain with fake STT/TTS engines.

    The voice route caches engines on the brain via
    ``_get_speech_engines`` (``brain._offline_stt`` / ``brain._offline_tts``),
    so we pre-populate those attributes with mocks before the first call.
    """
    brain = MagicMock()
    stt = MagicMock()
    tts = MagicMock()
    brain._offline_stt = stt
    brain._offline_tts = tts
    app.state.brain = brain
    yield brain, stt, tts
    # Clean up so other tests are not affected
    app.state.brain = None


class TestVoiceEndpoint:
    def test_invalid_base64_rejected(self) -> None:
        client = TestClient(app)
        resp = client.post(
            "/api/chat/voice",
            json={"audio_base64": "not valid base64 !!!", "format": "wav"},
        )
        assert resp.status_code == 400

    def test_invalid_wav_rejected(self) -> None:
        client = TestClient(app)
        resp = client.post(
            "/api/chat/voice",
            json={"audio_base64": base64.b64encode(b"garbage-data-not-a-wav").decode(), "format": "wav"},
        )
        assert resp.status_code == 400

    def test_stt_unavailable_returns_501(self, _wire_mock_brain) -> None:
        stt = _wire_mock_brain[1]
        stt.transcribe.return_value = {
            "text": "",
            "source": "none",
            "language": "",
        }
        client = TestClient(app)
        resp = client.post(
            "/api/chat/voice",
            json={"audio_base64": _synthetic_wav([0.0] * 16000), "format": "wav"},
        )
        assert resp.status_code == 501

    def test_successful_voice_pipeline(self, _wire_mock_brain) -> None:
        brain, stt, tts = _wire_mock_brain
        brain.process.return_value = {
            "response": "ধন্যবাদ, আমি শুনেছি",
            "intent": "statement",
            "confidence": 0.9,
            "processing_time": 0.01,
            "cycle_count": 1,
            "emotional_state": {},
        }
        stt.transcribe.return_value = {
            "text": "আমার নাম রহুল",
            "source": "whisper",
            "language": "bn",
        }
        tts.synthesize.return_value = {
            "audio": b"PCM-PAYLOAD",
            "source": "espeak",
            "available": True,
            "rate": 16000,
            "channels": 1,
        }

        client = TestClient(app)
        resp = client.post(
            "/api/chat/voice",
            json={"audio_base64": _synthetic_wav([0.0] * 16000), "format": "wav"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["transcription"] == "আমার নাম রহুল"
        assert data["transcription_source"] == "whisper"
        assert data["response"] == "ধন্যবাদ, আমি শুনেছি"
        assert data["speech"]["audio_base64"]
        assert data["speech"]["source"] == "espeak"
        brain.process.assert_called_once_with("আমার নাম রহুল")
