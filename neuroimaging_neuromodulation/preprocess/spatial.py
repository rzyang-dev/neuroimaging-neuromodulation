"""Spatial preprocessing implemented with SciPy."""

from __future__ import annotations

import numpy as np
from scipy import ndimage


def smooth_volume(
    data: np.ndarray,
    fwhm_mm: float,
    affine: np.ndarray,
) -> np.ndarray:
    """Gaussian-smooth a 3D or 4D array in physical millimeters."""

    data = np.asarray(data, dtype=float)
    voxel = np.sqrt(np.sum(np.asarray(affine, dtype=float)[:3, :3] ** 2, axis=0))
    sigma_mm = fwhm_mm / (2.0 * np.sqrt(2.0 * np.log(2.0)))
    sigma_voxel = tuple(max(float(sigma_mm / v), 0.01) for v in voxel)
    if data.ndim == 4:
        return np.stack(
            [ndimage.gaussian_filter(data[..., t], sigma=sigma_voxel) for t in range(data.shape[3])],
            axis=-1,
        )
    return ndimage.gaussian_filter(data, sigma=sigma_voxel)


__all__ = ["smooth_volume"]
