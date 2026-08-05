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

    seed_mask = np.asarray(seed_mask, dtype=bool)
    target_mask = np.asarray(target_mask, dtype=bool)
    affine = np.asarray(affine, dtype=float)
    inverse = np.linalg.inv(affine)
    count = 0
    for streamline in streamlines:
        points = np.asarray(streamline, dtype=float)
        if points.ndim != 2 or points.shape[1] != 3:
            continue
        homogeneous = np.column_stack([points, np.ones(len(points), dtype=float)])
        voxels = (inverse @ homogeneous.T).T[:, :3]
        voxel_indices = np.rint(voxels).astype(int)
        in_bounds = np.all(
            (voxel_indices >= 0)
            & (voxel_indices < np.asarray(seed_mask.shape, dtype=int)),
            axis=1,
        )
        if not np.any(in_bounds):
            continue
        indices = voxel_indices[in_bounds]
        hits_seed = bool(seed_mask[indices[:, 0], indices[:, 1], indices[:, 2]].any())
        hits_target = bool(target_mask[indices[:, 0], indices[:, 1], indices[:, 2]].any())
        if hits_seed and hits_target:
            count += 1
    return {
        "count": count,
        "seed_voxels": int(seed_mask.sum()),
        "target_voxels": int(target_mask.sum()),
        "streamlines": len(streamlines),
    }


__all__ = ["count_streamlines_between_masks"]
