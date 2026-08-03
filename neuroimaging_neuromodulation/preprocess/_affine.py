"""Shared low-level DIPY affine registration pipeline."""

from __future__ import annotations

import numpy as np


_TRANSFORMS = {
    "translation": "TranslationTransform3D",
    "rigid": "RigidTransform3D",
    "rigid_isoscaling": "RigidIsoScalingTransform3D",
    "rigid_scaling": "RigidScalingTransform3D",
    "affine": "AffineTransform3D",
}


def affine_registration_pipeline(
    moving: np.ndarray,
    static: np.ndarray,
    *,
    moving_affine: np.ndarray,
    static_affine: np.ndarray,
    pipeline: tuple[str, ...] = ("translation", "rigid"),
    level_iters: tuple[int, ...] = (20, 10, 5),
    optimizer_options: dict | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Run a DIPY affine pipeline and return resampled data plus the affine."""

    from dipy.align.imaffine import AffineMap, AffineRegistration, MutualInformationMetric
    from dipy.align import transforms as dipy_transforms

    moving = np.asarray(moving, dtype=float)
    static = np.asarray(static, dtype=float)
    moving_affine = np.asarray(moving_affine, dtype=float)
    static_affine = np.asarray(static_affine, dtype=float)
    affreg = AffineRegistration(
        metric=MutualInformationMetric(),
        level_iters=list(level_iters),
        options=optimizer_options,
        verbosity=0,
    )
    final_affine = np.eye(4)
    for name in pipeline:
        if name not in _TRANSFORMS:
            raise ValueError(f"Unsupported registration step: {name}")
        transform = getattr(dipy_transforms, _TRANSFORMS[name])()
        xform, _xopt, _fopt = affreg.optimize(
            static,
            moving,
            transform,
            None,
            static_grid2world=static_affine,
            moving_grid2world=moving_affine,
            starting_affine=final_affine,
            ret_metric=True,
        )
        final_affine = xform.affine
    affine_map = AffineMap(
        final_affine,
        domain_grid_shape=static.shape,
        domain_grid2world=static_affine,
        codomain_grid_shape=moving.shape,
        codomain_grid2world=moving_affine,
    )
    resampled = affine_map.transform(moving)
    return np.asarray(resampled, dtype=float), final_affine


__all__ = ["affine_registration_pipeline"]
