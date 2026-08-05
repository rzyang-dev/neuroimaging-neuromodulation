"""Tract-profile extraction from streamlines and scalar images."""

from __future__ import annotations

from pathlib import Path

import nibabel as nib
import numpy as np
from scipy import ndimage

from ..io.nifti import load_volume
from .streamlines_io import load_tract_streamlines as _load_tract_streamlines


def _resample_streamline(points: np.ndarray, n_points: int) -> np.ndarray | None:
    points = np.asarray(points, dtype=float)
    if points.ndim != 2 or points.shape[1] != 3 or len(points) < 2:
        return None
    segment_lengths = np.linalg.norm(np.diff(points, axis=0), axis=1)
    cumulative = np.concatenate([[0.0], np.cumsum(segment_lengths)])
    total = float(cumulative[-1])
    if total <= 0:
        return None
    targets = np.linspace(0.0, total, int(n_points))
    resampled = np.empty((int(n_points), 3), dtype=float)
    for axis in range(3):
        resampled[:, axis] = np.interp(targets, cumulative, points[:, axis])
    return resampled


def tract_profile(
    streamlines: list[np.ndarray],
    scalar_image: str | Path | nib.Nifti1Image,
    *,
    n_points: int = 100,
    volume_index: int = 0,
) -> dict[str, object]:
    """Resample streamlines and compute mean/std scalar values along a profile."""

    img, data = load_volume(scalar_image)
    if data.ndim == 4:
        data = data[..., int(volume_index)]
    if data.ndim != 3:
        raise ValueError("scalar_image must be 3D or a 4D image with volume_index")
    inv_affine = np.linalg.inv(img.affine)
    profiles: list[np.ndarray] = []
    for streamline in streamlines:
        resampled = _resample_streamline(streamline, n_points)
        if resampled is None:
            continue
        voxel = inv_affine @ np.column_stack(
            [resampled, np.ones(len(resampled), dtype=float)]
        ).T
        values = ndimage.map_coordinates(
            data,
            voxel[:3, :],
            order=1,
            mode="constant",
            cval=0.0,
            prefilter=True,
        )
        profiles.append(values)
    if not profiles:
        raise ValueError("No usable streamlines for tract profiling")
    profile_matrix = np.stack(profiles, axis=0)
    return {
        "profile": np.mean(profile_matrix, axis=0),
        "std": np.std(profile_matrix, axis=0),
        "n_streamlines": len(profile_matrix),
        "n_points": int(n_points),
    }


def load_tract_streamlines(
    track_path: str | Path,
    reference_image: str | Path | nib.Nifti1Image,
) -> list[np.ndarray]:
    """Load TRK/TCK streamlines in the reference image's world space."""

    return _load_tract_streamlines(track_path, reference_image)


__all__ = ["load_tract_streamlines", "tract_profile"]
