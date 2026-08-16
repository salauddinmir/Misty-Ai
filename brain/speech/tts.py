"""Offline text-to-speech for the Misty brain.

Uses ``espeak`` (a small, dependency-free synthesizer available on most
Linux systems) through a subprocess so the brain never depends on any
cloud TTS service or heavy ML model. When espeak is not installed the
``available`` flag simply stays ``False`` and callers can fall back to
text responses — no errors are raised.

Audio is produced as raw PCM via espeak's ``--stdout`` flag, then the
raw samples are packed into a minimal 16 kHz mono WAV buffer so the
web client can play the result directly.
"""

from __future__ import annotations

import io
import shutil
import struct
import subprocess
import wave
from dataclasses import dataclass, field

ESPEAK_BIN = shutil.which("espeak")


@dataclass
class OfflineTTS:
    """Offline TTS engine backed by espeak (optional dependency)."""

    rate: int = 150
    pitch: int = 40
    voice: str = "default"
    # Cached after the first availability probe so repeated calls are cheap.
    available: bool = field(default=ESPEAK_BIN is not None, init=False)
    _probe_done: bool = field(default=False, init=False)

    # ---- public API ----------------------------------------------------

    def probe(self) -> bool:
        """Check once whether espeak is installed and playable."""
        if not self.available:
            return False
        try:
            subprocess.run(
                [ESPEAK_BIN, "--version"],
                capture_output=True,
                timeout=5,
                check=True,
            )
            self.available = True
        except (subprocess.SubprocessError, FileNotFoundError):
            self.available = False
        self._probe_done = True
        return self.available

    def synthesize(self, text: str, language: str = "en") -> dict:
        """Synthesize ``text`` into a WAV byte buffer.

        Returns a dict ``{"audio": bytes, "rate": int,
        "channels": int, "source": str, "available": bool}``.
        When espeak is unavailable, ``audio`` is an empty buffer and
        ``source`` is ``"none"`` — callers should treat that as "reply
        in text only".
        """
        if not self.available and not self.probe():
            return {
                "audio": b"",
                "rate": 16000,
                "channels": 1,
                "source": "none",
                "available": False,
            }

        try:
            result = subprocess.run(
                [
                    ESPEAK_BIN,
                    text,
                    "-a",
                    "150",
                    "-p",
                    str(self.pitch),
                    "-s",
                    str(self.rate),
                    "-v",
                    self.voice,
                    f"--stdin={language}",
                    "--stdout",
                ],
                capture_output=True,
                timeout=30,
                check=True,
            )
            raw = result.stdout
            audio = _raw_to_wav(raw, sample_rate=22050)
            return {
                "audio": audio,
                "rate": 16000,
                "channels": 1,
                "source": "espeak",
                "available": True,
            }
        except (subprocess.SubprocessError, FileNotFoundError):
            self.available = False
            return {
                "audio": b"",
                "rate": 16000,
                "channels": 1,
                "source": "none",
                "available": False,
            }


def _raw_to_wav(raw: bytes, sample_rate: int) -> bytes:
    """Wrap espeak's signed 16-bit little-endian PCM into a WAV buffer."""
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(raw)
    return buffer.getvalue()


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
    n_samples = len(frames) // 2
    samples = struct.unpack(f"<{n_samples}h", frames[: n_samples * 2])
    # Interleave -> mono: average channels
    if n_channels > 1:
        samples = [sum(samples[i : i + n_channels]) / n_channels for i in range(0, len(samples), n_channels)]
    return [float(s) / 32768.0 for s in samples], rate
