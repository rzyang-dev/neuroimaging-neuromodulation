"""Structural connectivity counts between ROIs."""

from __future__ import annotations

import numpy as np


def count_streamlines_between_masks(
    streamlines: list[np.ndarray],
    affine: np.ndarray,
    seed_mask: np.ndarray,
    target_mask: np.ndarray,
) -> dict[str, object]:
    """Count streamlines connecting seed and target endpoint masks."""

    from dipy.tracking import utils

    seed_mask = np.asarray(seed_mask, dtype=bool)
    target_mask = np.asarray(target_mask, dtype=bool)
    labels = seed_mask.astype(int) + 2 * target_mask.astype(int)
    matrix = utils.connectivity_matrix(
        streamlines,
        np.asarray(affine, dtype=float),
        labels,
        inclusive=True,
        symmetric=False,
    )
    count = int(matrix[1, 2] + matrix[2, 1])
    return {
        "count": count,
        "seed_voxels": int(seed_mask.sum()),
        "target_voxels": int(target_mask.sum()),
        "streamlines": len(streamlines),
    }


__all__ = ["count_streamlines_between_masks"]
