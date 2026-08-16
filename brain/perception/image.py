"""Image feature encoder.

Extracts low-frequency visual features from raw image data using only
NumPy (no heavy model dependency). The design mirrors what a lightweight
production model (CLIP, MobileNet, etc.) would later provide: a fixed-size
descriptor summarizing brightness, color balance, and spatial structure.

Feature layout (total ``feature_size`` = 64 by default):
- 1  : mean luminance
- 1  : luminance contrast (std)
- 3  : mean RGB channel values
- 3  : RGB channel standard deviations
- 8  : brightness histogram (equal-width bins)
- 16 : low-resolution 4x4 spatial grid luminance averages
- 32 : corner energy from a 2x2 block Haar-like filter bank (x2 channels
        via horizontal/vertical edge responses)

Inputs:
- ``np.ndarray`` of shape (H, W, 3) with uint8 RGB pixels, or
- raw PNG/JPEG ``bytes`` (decoded with Pillow when available; falls back
  to a simple grayscale sampling of raw bytes when Pillow is missing).
"""

import numpy as np

from brain.perception.encoder import ModalityEncoder


class ImageEncoder(ModalityEncoder):
    """Encode raw image data into a 64-dimensional feature vector."""

    modality = "image"
    feature_size = 64

    def _extract(self, raw) -> np.ndarray:
        pixels = self._to_array(raw)
        return self._features(pixels)

    @staticmethod
    def _to_array(raw) -> np.ndarray:
        """Convert bytes or an array into an (H, W, 3) float array.

        Bytes input tries Pillow first; raw-byte fallback yields a
        deterministic grayscale tiling of the byte stream.
        """
        if isinstance(raw, np.ndarray):
            arr = raw.astype(np.float64)
            if arr.ndim == 2:
                arr = np.stack([arr, arr, arr], axis=-1)
            if arr.ndim == 3 and arr.shape[-1] == 4:
                arr = arr[..., :3]
            return arr
        if isinstance(raw, (bytes, bytearray)):
            try:
                from io import BytesIO

                from PIL import Image
            except ImportError:
                pass
            else:
                try:
                    img = Image.open(BytesIO(bytes(raw))).convert("RGB")
                except Exception:
                    # Unrecognized bytes: fall through to the raw-byte path.
                    pass
                else:
                    return np.asarray(img, dtype=np.float64)
            # No Pillow or unidentifiable bytes: tile the byte stream into a
            # 64x64 RGB canvas.
            buf = np.frombuffer(bytes(raw), dtype=np.uint8)
            tiled = np.tile(
                buf[: 64 * 64 * 3]
                if buf.size >= 64 * 64 * 3
                else np.concatenate([buf, np.zeros(64 * 64 * 3 - buf.size, dtype=np.uint8)]),
                (1,),
            )[: 64 * 64 * 3]
            return tiled.reshape(64, 64, 3).astype(np.float64)
        raise TypeError(f"Unsupported image input type: {type(raw)}")

    @staticmethod
    def _features(pixels: np.ndarray) -> np.ndarray:
        h, w = pixels.shape[:2]
        lum = pixels.mean(axis=-1) / 255.0

        hist, _ = np.histogram(lum, bins=8, range=(0.0, 1.0))
        hist = hist.astype(np.float64) / max(lum.size, 1)

        grid_h, grid_w = 4, 4
        sh, sw = h // grid_h, w // grid_w
        grid = np.zeros(grid_h * grid_w, dtype=np.float64)
        for i in range(grid_h):
            for j in range(grid_w):
                patch = lum[i * sh : (i + 1) * sh, j * sw : (j + 1) * sw]
                if patch.size:
                    grid[i * grid_w + j] = float(patch.mean())

        # Haar-like horizontal and vertical edge energy on 2x2 blocks,
        # pooled into a fixed-size orientation histogram so the descriptor
        # does not depend on the input resolution.
        bh, bw = 2 * (h // 2), 2 * (w // 2)
        q = lum[:bh, :bw].reshape(h // 2, 2, w // 2, 2)
        horiz = (q[:, 0, :, 0] + q[:, 0, :, 1]) - (q[:, 1, :, 0] + q[:, 1, :, 1])
        vert = (q[:, 0, :, 0] + q[:, 1, :, 0]) - (q[:, 0, :, 1] + q[:, 1, :, 1])
        edges = np.abs(horiz.flatten()).astype(np.float64) + np.abs(vert.flatten()).astype(np.float64)
        edges = edges / max(edges.max(), 1e-10) if edges.max() > 1e-10 else edges
        # Mean-pool to a fixed 32-bin histogram regardless of image size
        n_pool = 32
        per_bin = edges.size // n_pool
        if per_bin > 0:
            edges = np.array([edges[i * per_bin : (i + 1) * per_bin].mean() for i in range(n_pool)], dtype=np.float64)
        else:
            padded = np.zeros(n_pool, dtype=np.float64)
            padded[: edges.size] = edges
            edges = padded

        return np.concatenate(
            [
                np.array([float(lum.mean()), float(lum.std())]),
                np.mean(pixels, axis=(0, 1)).astype(np.float64) / 255.0,
                np.std(pixels, axis=(0, 1)).astype(np.float64) / 255.0,
                hist,
                grid,
                edges,
            ]
        )
