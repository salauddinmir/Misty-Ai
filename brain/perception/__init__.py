"""
Perception Module.

Provides a lightweight, dependency-free foundation for multimodal input:

- ``ModalityEncoder``: base class for modality-specific feature extraction
- ``ImageEncoder``: extracts low-frequency pixel features from raw images
- ``AudioEncoder``: extracts spectral band energy features from raw audio
- ``MultimodalGateway``: routes inputs by modality and encodes them into
  fixed-size vectors suitable for the neural sensory region.

All encoders are pure Python/NumPy so the system stays LLM- and
heavy-model-free. Production-grade embeddings (CLIP, Whisper, etc.) can be
plugged in later by subclassing ``ModalityEncoder``.
"""

from brain.perception.audio import AudioEncoder
from brain.perception.encoder import ModalityEncoder
from brain.perception.gateway import MultimodalGateway
from brain.perception.image import ImageEncoder

__all__ = [
    "AudioEncoder",
    "ImageEncoder",
    "ModalityEncoder",
    "MultimodalGateway",
]
