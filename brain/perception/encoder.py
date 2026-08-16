"""Base class for modality-specific feature encoders."""

from typing import Any

import numpy as np


class ModalityEncoder:
    """Base encoder that maps raw modality data to a fixed-size feature vector.

    Subclasses implement ``_extract(raw)`` to convert bytes or arrays into
    a 1-D feature vector. The public ``encode`` method validates the output
    size and applies optional L2 normalization so downstream neural regions
    receive scale-consistent inputs.

    Attributes:
        modality: Machine-readable modality name (e.g. "image", "audio").
        feature_size: Fixed output dimensionality.
    """

    modality: str = "generic"
    feature_size: int = 64

    def encode(self, raw: Any) -> np.ndarray:
        """Encode raw data into a normalized feature vector.

        Args:
            raw: Modality-specific raw input (bytes, numpy array, etc.).

        Returns:
            Feature vector of shape ``(feature_size,``) with unit L2 norm.
        """
        features = self._extract(raw)
        if features.shape[0] != self.feature_size:
            raise ValueError(
                f"{type(self).__name__} produced {features.shape[0]} features instead of {self.feature_size}"
            )
        norm = float(np.linalg.norm(features))
        if norm > 1e-10:
            features = features / norm
        return features

    def _extract(self, raw: Any) -> np.ndarray:
        """Extract a raw (un-normalized) feature vector from the input."""
        raise NotImplementedError
