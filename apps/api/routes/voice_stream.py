"""Phase 7: full duplex voice conversation over WebSocket.

WebSocket endpoint for real-time voice conversation:
- Client sends raw PCM chunks (16 kHz mono) or base64 WAV frames.
- Server accumulates audio, runs offline STT when a pause/silence is
  detected (energy-based VAD), feeds the transcript through the brain's
  cognitive cycle, and streams back the TTS audio chunks plus text.

No LLM and no cloud service is involved; STT (whisper) and TTS (espeak)
run entirely on the server. When the speech engines are unavailable the
endpoint degrades gracefully by echoing text-only frames.
"""

from __future__ import annotations

import base64
import io
import json
import struct
import time as time_module
import wave
from typing import Any, Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from brain.core.brain import Brain
from brain.speech import OfflineSTT, OfflineTTS

ROUTER_PREFIX = "/ws/voice"

# Energy below this RMS threshold (0..1) counts as silence for VAD.
SILENCE_RMS_THRESHOLD = 0.02
# Consecutive silent frames before we consider speech finished.
SILENCE_FRAMES = 10
# Each PCM frame covers this many samples (160 ms at 16 kHz).
FRAME_SAMPLES = 2560


def _rms(samples: list[float]) -> float:
    """Root mean square of a sample list (0 for empty input)."""
    if not samples:
        return 0.0
    return (sum(s * s for s in samples) / len(samples)) ** 0.5


def _pcm_to_wav_bytes(pcm_samples: list[float], sample_rate: int = 16000) -> bytes:
    """Encode float PCM samples (-1..1) as 16-bit little-endian WAV bytes."""
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        raw = b"".join(struct.pack("<h", max(-32768, min(32767, int(s * 32767)))) for s in pcm_samples)
        wf.writeframes(raw)
    return buffer.getvalue()


def _decode_pcm_frame(payload: str) -> list[float]:
    """Decode base64-encoded 16-bit PCM samples to floats in [-1, 1]."""
    raw = base64.b64decode(payload, validate=True)
    count = len(raw) // 2
    samples = struct.unpack(f"<{count}h", raw[: count * 2])
    return [max(-1.0, min(1.0, s / 32767.0)) for s in samples]


def _get_speech_engines(brain: Any) -> tuple[OfflineSTT | None, OfflineTTS | None]:
    """Lazily attach shared offline STT/TTS engines to the brain state."""
    if not hasattr(brain, "_offline_stt"):
        brain._offline_stt = OfflineSTT()  # type: ignore[attr-defined]
    if not hasattr(brain, "_offline_tts"):
        brain._offline_tts = OfflineTTS()  # type: ignore[attr-defined]
    return brain._offline_stt, brain._offline_tts  # type: ignore[attr-defined]


async def _send(websocket: WebSocket, payload: Dict[str, Any]) -> None:
    """Send a JSON event if the connection is still open."""
    if websocket.client_state is WebSocketState.DISCONNECTED:
        return
    try:
        payload.setdefault("timestamp", time_module.time())
        await websocket.send_text(json.dumps(payload))
    except Exception:
        pass


class VoiceSession:
    """Per-connection voice session state: audio buffering + VAD."""

    def __init__(self) -> None:
        self.buffer: list[float] = []
        self.silent_frames = 0
        self.started_at: float = time_module.time()

    def add_pcm(self, samples: list[float]) -> None:
        self.buffer.extend(samples)
        tail = samples[-FRAME_SAMPLES:] if len(samples) >= FRAME_SAMPLES else samples
        if _rms(tail) < SILENCE_RMS_THRESHOLD:
            self.silent_frames += 1
        else:
            self.silent_frames = 0

    def speech_ready(self) -> bool:
        """Enough audio buffered and a pause detected (or a stop sent)."""
        return bool(self.buffer) and (self.silent_frames >= SILENCE_FRAMES or len(self.buffer) >= 8 * FRAME_SAMPLES)

    def drain(self) -> bytes:
        """Consume the buffer as a WAV payload."""
        samples = self.buffer
        self.buffer = []
        self.silent_frames = 0
        return _pcm_to_wav_bytes(samples)


async def _run_voice_loop(websocket: WebSocket) -> None:
    """Read PCM/text frames, transcribe on pauses, run the brain, reply."""
    brain: Brain = websocket.app.state.brain
    stt, tts = _get_speech_engines(brain)
    session = VoiceSession()

    await _send(websocket, {"type": "voice_ready", "data": {"stt": stt is not None, "tts": tts is not None}})

    while True:
        raw = await websocket.receive_text()
        try:
            frame = json.loads(raw)
        except json.JSONDecodeError:
            await _send(websocket, {"type": "error", "data": {"message": "Invalid JSON frame"}})
            continue

        # Voice chunk: base64 PCM samples at 16 kHz mono.
        if frame.get("type") == "pcm":
            try:
                samples = _decode_pcm_frame(frame.get("data", ""))
            except Exception:
                await _send(websocket, {"type": "error", "data": {"message": "Bad PCM frame"}})
                continue
            session.add_pcm(samples)
            if not session.speech_ready():
                continue
            wav_bytes = session.drain()
            if stt is None:
                await _send(websocket, {"type": "stt_unavailable", "data": {}})
                continue
            transcript = stt.transcribe(wav_bytes).get("text", "")
            if not transcript:
                await _send(websocket, {"type": "no_speech", "data": {}})
                continue
            # Text mode: direct transcript input (debug / accessibility).
        elif frame.get("type") == "text":
            transcript = str(frame.get("data", "")).strip()
            if not transcript:
                continue
        elif frame.get("type") == "stop":
            # Force immediate transcription of the buffered audio.
            if not session.buffer:
                continue
            wav_bytes = session.drain()
            if stt is None:
                continue
            transcript = stt.transcribe(wav_bytes).get("text", "")
            if not transcript:
                await _send(websocket, {"type": "no_speech", "data": {}})
                continue
        else:
            await _send(websocket, {"type": "error", "data": {"message": f"Unknown frame type: {frame.get('type')}"}})
            continue

        # Cognitive cycle
        await _send(websocket, {"type": "processing_start", "data": {"transcript": transcript}})
        result = brain.process(transcript)
        await _send(
            websocket,
            {
                "type": "processing_complete",
                "data": {
                    "transcript": transcript,
                    "response": result["response"],
                    "intent": result.get("intent"),
                    "emotional_state": result.get("emotional_state", {}),
                },
            },
        )

        # Text-to-speech reply streamed back as chunks.
        if tts is not None:
            tts_result = tts.synthesize(result.get("response", ""))
            if tts_result.get("available") and tts_result.get("audio"):
                audio = tts_result["audio"]
                chunk_size = 3200  # ~100 ms chunks
                for i in range(0, max(len(audio), 1), chunk_size):
                    await _send(
                        websocket,
                        {
                            "type": "tts_chunk",
                            "data": {
                                "audio_base64": base64.b64encode(audio[i : i + chunk_size]).decode(),
                                "done": i + chunk_size >= len(audio),
                            },
                        },
                    )
        await _send(websocket, {"type": "tts_done", "data": {"tts": tts is not None}})


router = APIRouter(prefix=ROUTER_PREFIX, tags=["voice-stream"])


@router.websocket("/")
async def voice_websocket(websocket: WebSocket) -> None:
    """Full duplex voice conversation.

    Clients send JSON frames:
    - {"type": "pcm", "data": "<base64 16-bit PCM 16kHz mono>"}
    - {"type": "text", "data": "<manual transcript>"}
    - {"type": "stop", "data": null}

    Server pushes JSON events:
    - voice_ready, processing_start, processing_complete,
      tts_chunk (base64 WAV chunks), tts_done,
      no_speech, stt_unavailable, error
    """
    await websocket.accept()
    try:
        await _run_voice_loop(websocket)
    except WebSocketDisconnect:
        pass
    except Exception:
        try:
            await _send(websocket, {"type": "error", "data": {"message": "Voice pipeline failure"}})
        except Exception:
            pass
