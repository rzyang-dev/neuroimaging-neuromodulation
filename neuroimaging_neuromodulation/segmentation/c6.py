"""Outer-brain c6 mask construction matching ``TMSmkC6.m``."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import ndimage

from ..io.nifti import load_volume, save_volume


def _largest_cluster(data: np.ndarray) -> np.ndarray:
    labels, n_labels = ndimage.label(data > 0, structure=np.ones((3, 3, 3)))
    if n_labels == 0:
        return np.zeros_like(data, dtype=np.uint8)
    sizes = ndimage.sum_labels(labels, labels, index=np.arange(1, n_labels + 1))
    largest = int(np.argmax(sizes) + 1)
    return (labels == largest).astype(np.uint8)


def make_c6_mask(
    t1_image: str | Path,
    output_path: str | Path | None = None,
    *,
    threshold: float = 1000.0,
) -> tuple[object, np.ndarray]:
    """Construct an approximate outer-brain mask from a T1 image.

    This follows the original MATLAB workflow: low-intensity voxels are kept,
    and the largest connected cluster is retained across adjacent slices in all
    three orientations. It is intentionally a research utility, not a validated
    SPM/DARTEL c6 replacement.
    """

    img, data = load_volume(t1_image)
    if data.ndim != 3:
        raise ValueError("T1 image must be 3D")
    binary = (np.asarray(data, dtype=float) < float(threshold)).astype(np.uint8)

    for axis in range(3):
        for s in range(binary.shape[axis] - 1):
            sl = [slice(None), slice(None), slice(None)]
            sl[axis] = slice(s, s + 2)
            pair = binary[tuple(sl)]
            if pair.any():
                binary[tuple(sl)] = _largest_cluster(pair)

    result = binary.astype(np.float32)
    if output_path is not None:
        save_volume(result, img, output_path)
    return img, result


__all__ = ["make_c6_mask"]
