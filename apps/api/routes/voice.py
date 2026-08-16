"""Voice input endpoint for the Misty brain.

POST /api/chat/voice
    body: {"audio_base64": "<base64 WAV>", "format": "wav"}
    The audio is decoded to a WAV buffer, transcribed by the offline
    STT engine, and the resulting text is fed through the brain's
    cognitive cycle exactly like a typed message.

The response contains both the transcription (so the client can show
what the brain "heard") and the normal brain reply, plus an optional
TTS audio payload when the offline TTS engine is available.
"""

from __future__ import annotations

import base64
import binascii
import io
import wave

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from brain.speech import OfflineSTT, OfflineTTS

router = APIRouter(prefix="/chat", tags=["voice"])


class VoiceRequest(BaseModel):
    audio_base64: str = Field(..., min_length=8, description="base64 encoded audio (WAV)")
    format: str = Field(default="wav", description="audio container, currently 'wav'")


def _get_speech_engines(brain: object) -> tuple[OfflineSTT | None, OfflineTTS | None]:
    """Lazily attach shared STT/TTS engines to the brain state."""
    if not hasattr(brain, "_offline_stt"):
        brain._offline_stt = OfflineSTT()  # type: ignore[attr-defined]
    if not hasattr(brain, "_offline_tts"):
        brain._offline_tts = OfflineTTS()  # type: ignore[attr-defined]
    return brain._offline_stt, brain._offline_tts  # type: ignore[attr-defined]


def _decode_audio(b64: str) -> bytes:
    try:
        raw = base64.b64decode(b64, validate=True)
    except binascii.Error as exc:
        raise HTTPException(status_code=400, detail="Invalid base64 audio data") from exc

    buffer = io.BytesIO(raw)
    try:
        with wave.open(buffer, "rb") as wf:
            if wf.getnchannels() not in (1, 2):
                raise ValueError("unsupported channel count")
            if wf.getframerate() <= 0:
                raise ValueError("unsupported sample rate")
            buffer.seek(0)
            wav_bytes = buffer.read()
    except wave.Error as exc:
        raise HTTPException(status_code=400, detail="Audio is not a valid WAV file") from exc
    return wav_bytes


@router.post("/voice")
async def chat_voice(request: Request, body: VoiceRequest) -> dict:
    """Transcribe voice input and run it through the cognitive cycle."""
    brain = request.app.state.brain
    wav_bytes = _decode_audio(body.audio_base64)

    stt, tts = _get_speech_engines(brain)

    # ---- speech-to-text (offline) ---------------------------------------
    stt_result = stt.transcribe(wav_bytes)
    transcription = stt_result.get("text", "")
    stt_source = stt_result.get("source", "none")
    language = stt_result.get("language", "")

    if not transcription:
        if stt_source == "none":
            raise HTTPException(
                status_code=501,
                detail=(
                    "Offline speech-to-text is not installed on this "
                    "server. Send text to POST /api/chat instead, or "
                    "install whisper to enable voice input."
                ),
            )
        raise HTTPException(
            status_code=400,
            detail="Could not recognize any speech in the audio.",
        )

    # ---- cognitive cycle -------------------------------------------------
    cycle_result = brain.process(transcription)

    # ---- text-to-speech (offline, optional) ------------------------------
    tts_audio = b""
    tts_source = "none"
    if tts is not None:
        tts_result = tts.synthesize(cycle_result.get("response", ""))
        if tts_result.get("available"):
            tts_audio = tts_result.get("audio", b"")
            tts_source = tts_result.get("source", "none")

    return {
        "transcription": transcription,
        "transcription_language": language,
        "transcription_source": stt_source,
        "response": cycle_result.get("response", ""),
        "intent": cycle_result.get("intent", ""),
        "confidence": cycle_result.get("confidence", 0.0),
        "processing_time": cycle_result.get("processing_time", 0.0),
        "cycle_count": cycle_result.get("cycle_count", 0),
        "emotional_state": cycle_result.get("emotional_state", {}),
        "speech": {
            "audio_base64": base64.b64encode(tts_audio).decode() if tts_audio else "",
            "source": tts_source,
            "rate": 16000,
            "channels": 1,
        },
    }
