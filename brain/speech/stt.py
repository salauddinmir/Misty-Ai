"""Offline speech-to-text for the Misty brain.

The preferred backend is OpenAI's Whisper (``tiny`` / ``base`` model),
which runs fully offline. Whisper is an *optional* dependency and is
only imported lazily — if it is not installed the engine reports
``available=False`` and callers must fall back to typed/text input.

No cloud API call is ever made: Whisper weights are used locally and
the ``audio`` tensor is passed to ``whisper.transcribe`` directly.
"""

from __future__ import annotations

import io
import wave
from dataclasses import dataclass, field


@dataclass
class OfflineSTT:
    """Offline STT engine. Available only when whisper is installed."""

    model_size: str = "tiny"
    language: str = "auto"
    available: bool = field(default=False, init=False)
    _model: object = field(default=None, init=False)

    # ---- private -------------------------------------------------------

    def _load_model(self) -> object | None:
        if self._model is not None:
            return self._model
        try:
            import whisper  # type: ignore

            self._model = whisper.load_model(self.model_size)
            self.available = True
            return self._model
        except ImportError:
            self.available = False
            return None

    # ---- public API ----------------------------------------------------

    def transcribe(self, audio_wav: bytes) -> dict:
        """Transcribe a WAV byte buffer to text (Bengali/English).

        Returns ``{"text": str, "segments": list, "language": str,
        "source": str, "available": bool}``. When Whisper is not
        installed the ``text`` field is empty and ``source`` is
        ``"none"``.
        """
        model = self._load_model()
        if model is None:
            return {
                "text": "",
                "segments": [],
                "language": "",
                "source": "none",
                "available": False,
            }

        import whisper  # type: ignore

        samples, _sample_rate = _samples_from_wav(audio_wav)
        if not samples:
            return {
                "text": "",
                "segments": [],
                "language": "",
                "source": "none",
                "available": True,
            }

        kwargs: dict = {"fp16": False}
        if self.language != "auto":
            kwargs["language"] = self.language
        result = whisper.transcribe(model, io.BytesIO(audio_wav), **kwargs)
        return {
            "text": (result.get("text") or "").strip(),
            "segments": [
                {"text": seg.get("text", ""), "start": seg.get("start"), "end": seg.get("end")}
                for seg in result.get("segments") or []
            ],
            "language": result.get("language", ""),
            "source": "whisper",
            "available": True,
        }


def _samples_from_wav(data: bytes) -> tuple[list[float], int]:
    """Extract float samples and sample rate from a WAV buffer."""
    buffer = io.BytesIO(data)
    with wave.open(buffer, "rb") as wf:
        n_channels = wf.getnchannels()
        width = wf.getsampwidth()
        rate = wf.getframerate()
        n_frames = wf.getnframes()
        frames = wf.readframes(n_frames)

    if width != 2:
        return [], rate
    import struct

    n_samples = len(frames) // 2
    samples = struct.unpack(f"<{n_samples}h", frames[: n_samples * 2])
    if n_channels > 1:
        samples = [sum(samples[i : i + n_channels]) / n_channels for i in range(0, len(samples), n_channels)]
    return [float(s) / 32768.0 for s in samples], rate
