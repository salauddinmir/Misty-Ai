"""
Media Route.

POST /api/chat/media endpoint that accepts image or audio input, runs it
through the multimodal perception gateway, and feeds the resulting feature
vector into the brain's sensory region for cognitive processing.

Inputs are base64-encoded payloads (to stay JSON-compatible). The gateway
chooses the correct encoder per modality and the feature vector drives the
sensory population of the spiking neural runtime.
"""

import base64
from typing import Any, Dict

import numpy as np
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from brain.perception import AudioEncoder, ImageEncoder, MultimodalGateway
from brain.regions.sensory import SensoryRegion

router = APIRouter()


class MediaRequest(BaseModel):
    """Request body for the media endpoint.

    Attributes:
        modality: One of "image" or "audio".
        data: Base64-encoded payload. For ``image`` this is raw PNG/JPEG
            bytes. For ``audio`` this is raw PCM float32 samples (mono,
            little-endian); the sample rate defaults to 16 kHz when omitted.
        message: Optional text context accompanying the media input.
        sample_rate: Audio sample rate in Hz (only used for ``audio``).
    """

    modality: str = Field(..., description='"image" or "audio".')
    data: str = Field(..., description="Base64-encoded raw input data.")
    message: str = Field(default="", description="Optional text context.")
    sample_rate: int = Field(default=16000, description="Audio sample rate in Hz.")


class MediaResponse(BaseModel):
    """Response body from the media endpoint.

    Attributes:
        perception: Perception metadata (encoder used, fallback flag).
        feature_norm: L2 norm of the produced feature vector (should be ~1).
        sensory_spikes: Number of neurons that fired in the sensory region.
        response: Brain's text response to the media input.
    """

    perception: Dict[str, Any]
    feature_norm: float
    sensory_spikes: int
    response: str


def _media_gateway(brain: Any) -> MultimodalGateway:
    """Build the gateway lazily so brain instances stay interchangeable."""
    gateway = MultimodalGateway()
    gateway.register(ImageEncoder(), AudioEncoder())
    return gateway


@router.post("/chat/media", response_model=MediaResponse)
async def media(request: Request, body: MediaRequest) -> MediaResponse:
    """Process an image or audio input through the cognitive system.

    Args:
        request: The FastAPI request object (contains app state).
        body: The media request with modality, base64 data and context.

    Returns:
        MediaResponse with perception metadata and the brain's response.
    """
    brain = request.app.state.brain
    database = request.app.state.database

    try:
        raw = base64.b64decode(body.data, validate=True)
    except Exception:
        return MediaResponse(
            perception={"modality": body.modality, "encoder": None, "fallback": True},
            feature_norm=0.0,
            sensory_spikes=0,
            response="The input data could not be decoded; please send valid base64.",
        )

    # Image encoder works on raw image bytes; audio gets a (samples, rate)
    # tuple so the encoder can compute frequency-domain features correctly.
    if body.modality == "image":
        input_data: Any = raw
    elif body.modality == "audio":
        samples = np.frombuffer(raw, dtype=np.float32)
        input_data = (samples, body.sample_rate)
    else:
        return MediaResponse(
            perception={"modality": body.modality, "encoder": None, "fallback": True},
            feature_norm=0.0,
            sensory_spikes=0,
            response="I can perceive images and audio, but I don't recognize that format.",
        )

    gateway = _media_gateway(brain)
    vector, meta = gateway.process_input(body.modality, input_data)

    # Feed the percept into a fresh sensory region matching the neural
    # population size, then drive one timestep to observe spiking output.
    size = vector.size
    sensory = SensoryRegion(name="media", size=int(size))
    sensory.encode_input(vector)
    spikes = sensory.step()

    # Build a short text description so the cognitive cycle can still
    # attach language to the percept (e.g. store an episodic trace).
    context = f"[{body.modality} input via {meta.get('encoder')}]"
    if body.message:
        context += f" {body.message}"

    result = brain.process(context)

    await database.save_episode(content=f"{context}: feature vector received", importance=0.3)

    return MediaResponse(
        perception=meta,
        feature_norm=float(np.linalg.norm(vector)),
        sensory_spikes=int(np.sum(spikes)),
        response=result["response"],
    )
