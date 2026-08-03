"""Optional motion-parameter estimation using DIPY registration."""

from __future__ import annotations

import numpy as np

from ._affine import affine_registration_pipeline


def affine_to_rp(affine: np.ndarray) -> np.ndarray:
    """Convert a 4x4 affine to SPM-style ``[tx, ty, tz, rx, ry, rz]``.

    Translations are in mm. Rotations are extracted as XYZ Euler angles in
    radians from the rotation component of the DIPY registration affine.
    """

    from scipy.spatial.transform import Rotation

    affine = np.asarray(affine, dtype=float)
    if affine.shape != (4, 4):
        raise ValueError("Expected a 4x4 affine")
    rotation = Rotation.from_matrix(affine[:3, :3])
    euler = rotation.as_euler("xyz", degrees=False)
    return np.concatenate([affine[:3, 3], euler])


def estimate_motion_parameters(
    data: np.ndarray,
    affine: np.ndarray,
    *,
    reference_volume: int = 0,
    pipeline: tuple[str, ...] = ("translation", "rigid"),
    level_iters: tuple[int, ...] = (20, 10, 5),
    optimizer_options: dict | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Estimate rigid motion parameters for a 4D series and reslice it.

    This uses DIPY's native affine registration. The returned first array is
    the motion-corrected 4D data; the second is ``(n_time, 6)`` SPM-style
    realignment parameters derived from the DIPY affines.
    """

    data = np.asarray(data, dtype=float)
    if data.ndim != 4:
        raise ValueError("Expected 4D functional data")
    affine = np.asarray(affine, dtype=float)
    corrected = np.empty_like(data)
    rp = np.zeros((data.shape[3], 6))
    for t in range(data.shape[3]):
        if t == reference_volume:
            corrected[..., t] = data[..., t]
            continue
        resampled, final_affine = affine_registration_pipeline(
            data[..., t],
            data[..., reference_volume],
            moving_affine=affine,
            static_affine=affine,
            pipeline=pipeline,
            level_iters=level_iters,
            optimizer_options=optimizer_options,
        )
        corrected[..., t] = resampled
        rp[t] = affine_to_rp(final_affine)
    return corrected, rp


__all__ = ["affine_to_rp", "estimate_motion_parameters"]
