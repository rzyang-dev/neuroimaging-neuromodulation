"""Coregistration between two 3D volumes using DIPY."""

from __future__ import annotations

import numpy as np

from ._affine import affine_registration_pipeline


def coregister_images(
    moving: np.ndarray,
    static: np.ndarray,
    *,
    moving_affine: np.ndarray,
    static_affine: np.ndarray,
    pipeline: tuple[str, ...] = ("translation", "rigid"),
    level_iters: tuple[int, ...] = (20, 10, 5),
    optimizer_options: dict | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Register ``moving`` to ``static`` and return the resampled volume + affine.

    This uses DIPY's mutual-information affine registration with a rigid
    pipeline. The returned affine maps moving-world coordinates to
    static-world coordinates.
    """

    moving = np.asarray(moving, dtype=float)
    static = np.asarray(static, dtype=float)
    if moving.ndim != 3 or static.ndim != 3:
        raise ValueError("moving and static must be 3D volumes")
    resampled, final_affine = affine_registration_pipeline(
        moving,
        static,
        moving_affine=moving_affine,
        static_affine=static_affine,
        pipeline=pipeline,
        level_iters=level_iters,
        optimizer_options=optimizer_options,
    )
    return np.asarray(resampled, dtype=float), np.asarray(final_affine, dtype=float)


__all__ = ["coregister_images"]
