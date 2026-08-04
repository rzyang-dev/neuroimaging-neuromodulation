"""Atlas-based streamline segmentation for AFQ-style tract workflows."""

from __future__ import annotations

from pathlib import Path

import nibabel as nib
import numpy as np

from ..io.nifti import load_volume
from .tract_profile import _resample_streamline


def segment_streamlines_by_atlas(
    streamlines: list[np.ndarray],
    atlas_image: str | Path | nib.Nifti1Image,
    *,
    n_samples: int = 50,
) -> dict[str, object]:
    """Assign each streamline to a JHU-style atlas label by majority sampling."""

    img, atlas = load_volume(atlas_image)
    if atlas.ndim == 4:
        atlas = atlas[..., 0]
    if atlas.ndim != 3:
        raise ValueError("atlas_image must be 3D")
    inv_affine = np.linalg.inv(img.affine)
    labels: list[int] = []
    for streamline in streamlines:
        resampled = _resample_streamline(streamline, n_samples)
        if resampled is None:
            labels.append(0)
            continue
        voxel = inv_affine @ np.column_stack(
            [resampled, np.ones(len(resampled), dtype=float)]
        ).T
        voxel = np.rint(voxel[:3, :]).astype(int)
        valid = (
            (voxel[0, :] >= 0)
            & (voxel[0, :] < atlas.shape[0])
            & (voxel[1, :] >= 0)
            & (voxel[1, :] < atlas.shape[1])
            & (voxel[2, :] >= 0)
            & (voxel[2, :] < atlas.shape[2])
        )
        values = atlas[tuple(voxel[:, valid])] if valid.any() else np.array([], dtype=int)
        nonzero = values[values > 0]
        if nonzero.size == 0:
            labels.append(0)
        else:
            unique, counts = np.unique(nonzero, return_counts=True)
            labels.append(int(unique[int(np.argmax(counts))]))

    counts: dict[str, int] = {}
    for label in sorted(set(labels)):
        counts[str(label)] = int(labels.count(label))
    return {
        "n_streamlines": len(streamlines),
        "labels": labels,
        "counts": counts,
    }


__all__ = ["segment_streamlines_by_atlas"]
