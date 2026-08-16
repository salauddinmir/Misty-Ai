"""Multimodal input gateway.

Routes raw inputs (text, image, audio) through the correct encoder and
returns a normalized feature vector plus a short semantic caption when
available. The gateway is deliberately model-free: encoders are pure
NumPy feature extractors, and richer perception (CLIP/Whisper-style) can
be attached by registering custom ``ModalityEncoder`` subclasses.

Usage::

    gateway = MultimodalGateway()
    gateway.register(ImageEncoder(), AudioEncoder())

    vector, meta = gateway.process_input("image", raw_bytes)
"""

from typing import Any, Dict, Tuple

import numpy as np

from brain.perception.encoder import ModalityEncoder


class MultimodalGateway:
    """Routes raw multimodal inputs to registered modality encoders.

    Attributes:
        default_text_modality: Modality name used when no encoder matches.
    """

    def __init__(self) -> None:
        self._encoders: Dict[str, ModalityEncoder] = {}

    def register(self, *encoders: ModalityEncoder) -> None:
        """Register one or more encoders, keyed by ``encoder.modality``."""
        for encoder in encoders:
            self._encoders[encoder.modality] = encoder

    @property
    def modalities(self):
        """List of registered modality names."""
        return list(self._encoders.keys())

    def process_input(self, modality: str, raw: Any) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Encode raw input for the given modality.

        Falls back to a zero vector with ``fallback=True`` metadata when
        the modality is unknown, so callers always get a usable pair.

        Args:
            modality: One of the registered modality names (or "text").
            raw: Modality-specific raw input.

        Returns:
            (feature_vector, metadata) where metadata contains the
            modality, encoder name and a fallback flag.
        """
        encoder = self._encoders.get(modality)
        if encoder is None:
            # "text" is intentionally first-class but model-free here:
            # downstream NLU handles textual content, so we emit a zero
            # vector with an explicit marker.
            size = self._encoders[next(iter(self._encoders))].feature_size if self._encoders else 64
            return np.zeros(size, dtype=np.float64), {
                "modality": modality,
                "encoder": None,
                "fallback": True,
            }
        vector = encoder.encode(raw)
        return vector, {
            "modality": modality,
            "encoder": type(encoder).__name__,
            "fallback": False,
        }

    def feature_size(self, modality: str) -> int:
        """Feature dimensionality for a registered modality."""
        encoder = self._encoders.get(modality)
        if encoder is None:
            return 64
        return encoder.feature_size
