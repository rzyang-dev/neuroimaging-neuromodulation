"""NumPy/SciPy image registration used by the minimal core path."""

from __future__ import annotations

import numpy as np
from scipy import ndimage
from scipy.optimize import minimize


def _rotation_matrix(rx: float, ry: float, rz: float) -> np.ndarray:
    cx, sx = np.cos(rx), np.sin(rx)
    cy, sy = np.cos(ry), np.sin(ry)
    cz, sz = np.cos(rz), np.sin(rz)
    rot_x = np.array([[1.0, 0.0, 0.0], [0.0, cx, -sx], [0.0, sx, cx]])
    rot_y = np.array([[cy, 0.0, sy], [0.0, 1.0, 0.0], [-sy, 0.0, cy]])
    rot_z = np.array([[cz, -sz, 0.0], [sz, cz, 0.0], [0.0, 0.0, 1.0]])
    return rot_z @ rot_y @ rot_x


def _transform_from_params(params: np.ndarray, kind: str) -> np.ndarray:
    params = np.asarray(params, dtype=float)
    if kind == "translation":
        if params.size != 3:
            raise ValueError("translation requires 3 parameters")
        transform = np.eye(4)
        transform[:3, 3] = params
        return transform
    if kind == "rigid":
        if params.size != 6:
            raise ValueError("rigid requires 6 parameters")
        tx, ty, tz, rx, ry, rz = params
        transform = np.eye(4)
        transform[:3, :3] = _rotation_matrix(rx, ry, rz)
        transform[:3, 3] = [tx, ty, tz]
        return transform
    if kind == "affine":
        if params.size != 12:
            raise ValueError("affine requires 12 parameters")
        transform = np.eye(4)
        transform[:3, :3] = params[:9].reshape(3, 3)
        transform[:3, 3] = params[9:12]
        return transform
    raise ValueError(f"Unsupported registration kind: {kind}")


def _sample_matrix(
    transform: np.ndarray,
    moving_affine: np.ndarray,
    static_affine: np.ndarray,
) -> np.ndarray:
    return (
        np.linalg.inv(moving_affine)
        @ np.linalg.inv(transform)
        @ static_affine
    )


def resample_moving_to_static(
    moving: np.ndarray,
    static: np.ndarray,
    transform: np.ndarray,
    moving_affine: np.ndarray,
    static_affine: np.ndarray,
    *,
    order: int = 1,
) -> np.ndarray:
    """Resample a moving volume onto a static grid for a world transform."""

    matrix = _sample_matrix(transform, moving_affine, static_affine)
    center_static = (np.asarray(static.shape, dtype=float) - 1.0) / 2.0
    center_moving = (np.asarray(moving.shape, dtype=float) - 1.0) / 2.0
    offset = matrix[:3, :3] @ center_static + matrix[:3, 3] - center_moving
    return ndimage.affine_transform(
        np.asarray(moving, dtype=float),
        matrix,
        offset=offset,
        output_shape=static.shape,
        order=order,
        mode="constant",
        cval=0.0,
    )


def _negative_correlation(resampled: np.ndarray, static: np.ndarray) -> float:
    resampled = np.asarray(resampled, dtype=float)
    static = np.asarray(static, dtype=float)
    finite = np.isfinite(resampled) & np.isfinite(static)
    mask = finite & ((resampled != 0) | (static != 0))
    if mask.sum() < 32:
        mask = finite
    a = resampled[mask]
    b = static[mask]
    if a.std() < 1e-12 or b.std() < 1e-12:
        return 1e6
    return -float(np.corrcoef(a, b)[0, 1])


def _objective(
    params: np.ndarray,
    kind: str,
    moving: np.ndarray,
    static: np.ndarray,
    moving_affine: np.ndarray,
    static_affine: np.ndarray,
) -> float:
    transform = _transform_from_params(params, kind)
    try:
        resampled = resample_moving_to_static(
            moving,
            static,
            transform,
            moving_affine,
            static_affine,
        )
    except Exception:
        return 1e6
    return _negative_correlation(resampled, static)


def internal_affine_registration(
    moving: np.ndarray,
    static: np.ndarray,
    *,
    moving_affine: np.ndarray,
    static_affine: np.ndarray,
    pipeline: tuple[str, ...],
    optimizer_options: dict | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Register two volumes without DIPY using Powell optimization."""

    moving = np.asarray(moving, dtype=float)
    static = np.asarray(static, dtype=float)
    moving_affine = np.asarray(moving_affine, dtype=float)
    static_affine = np.asarray(static_affine, dtype=float)
    options = dict(optimizer_options or {})
    maxiter = int(options.pop("maxiter", 50))
    final_transform = np.eye(4)

    for kind in pipeline:
        if kind not in {"translation", "rigid", "affine"}:
            raise ValueError(f"Unsupported registration step: {kind}")
        n_params = 3 if kind == "translation" else 6 if kind == "rigid" else 12
        initial = np.zeros(n_params)
        result = minimize(
            _objective,
            initial,
            args=(kind, moving, static, moving_affine, static_affine),
            method="Powell",
            options={
                "maxiter": maxiter,
                "xtol": 1e-3,
                "ftol": 1e-4,
                **options,
            },
        )
        final_transform = _transform_from_params(result.x, kind) @ final_transform

    resampled = resample_moving_to_static(
        moving,
        static,
        final_transform,
        moving_affine,
        static_affine,
    )
    return np.asarray(resampled, dtype=float), final_transform


__all__ = ["internal_affine_registration", "resample_moving_to_static"]
