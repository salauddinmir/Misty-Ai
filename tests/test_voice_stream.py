"""
Phase 7 tests: full duplex voice pipeline helpers — PCM/WAV encoding,
energy-based voice activity detection, and the voice session state.
"""

import base64
import io
import struct
import wave

from apps.api.routes.voice_stream import (
    FRAME_SAMPLES,
    VoiceSession,
    _decode_pcm_frame,
    _pcm_to_wav_bytes,
    _rms,
)


def _encode_pcm(samples: list[float]) -> str:
    """Test helper: float samples -> base64 16-bit PCM."""
    raw = b"".join(struct.pack("<h", max(-32768, min(32767, int(s * 32767)))) for s in samples)
    return base64.b64encode(raw).decode()


class TestPcmEncoding:
    def test_round_trip(self) -> None:
        samples = [0.0, 0.5, -0.5, 1.0, -1.0, 0.25]
        wav_bytes = _pcm_to_wav_bytes(samples)
        buffer = io.BytesIO(wav_bytes)
        with wave.open(buffer, "rb") as wf:
            assert wf.getnchannels() == 1
            assert wf.getsampwidth() == 2
            assert wf.getframerate() == 16000
            raw = wf.readframes(len(samples))
        decoded = [s / 32767.0 for s in struct.unpack(f"<{len(samples)}h", raw)]
        for orig, dec in zip(samples, decoded, strict=True):
            assert abs(orig - dec) < 0.0001

    def test_decode_frame(self) -> None:
        samples = [0.0, 0.5, -0.5, 0.25]
        restored = _decode_pcm_frame(_encode_pcm(samples))
        for orig, dec in zip(samples, restored, strict=True):
            assert abs(orig - dec) < 0.0001

    def test_decode_clamps_values(self) -> None:
        restored = _decode_pcm_frame(_encode_pcm([2.0, -2.0]))
        assert restored[0] == 1.0
        assert restored[1] == -1.0

    def test_rms(self) -> None:
        assert _rms([]) == 0.0
        assert _rms([0.0, 0.0]) == 0.0
        # Constant 0.5 amplitude should give ~0.5 RMS.
        assert abs(_rms([0.5, 0.5, 0.5, 0.5]) - 0.5) < 1e-9


class TestVoiceSession:
    def test_loud_frames_reset_silence(self) -> None:
        session = VoiceSession()
        loud = [0.5] * FRAME_SAMPLES
        silent = [0.0] * FRAME_SAMPLES
        session.add_pcm(loud)
        assert session.silent_frames == 0
        session.add_pcm(silent)
        assert session.silent_frames == 1
        session.add_pcm(loud)
        assert session.silent_frames == 0

    def test_speech_ready_on_pause(self) -> None:
        session = VoiceSession()
        session.add_pcm([0.5] * FRAME_SAMPLES)
        for _ in range(12):
            session.add_pcm([0.0] * FRAME_SAMPLES)
        assert session.speech_ready()

    def test_speech_ready_on_long_buffer(self) -> None:
        session = VoiceSession()
        for _ in range(10):
            session.add_pcm([0.5] * FRAME_SAMPLES)
        assert session.speech_ready()

    def test_drain_clears_buffer(self) -> None:
        session = VoiceSession()
        session.add_pcm([0.5] * (2 * FRAME_SAMPLES))
        wav = session.drain()
        assert wav.startswith(b"RIFF")
        assert session.buffer == []
        assert not session.speech_ready()
