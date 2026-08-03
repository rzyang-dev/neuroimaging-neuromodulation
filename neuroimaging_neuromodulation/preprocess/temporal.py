"""Temporal preprocessing implemented in Python."""

from __future__ import annotations

import numpy as np
from scipy import fft, ndimage


def shift_series(
    series: np.ndarray,
    shift_seconds: float,
    tr: float,
) -> np.ndarray:
    """Shift each time series by ``shift_seconds`` using Fourier interpolation."""

    series = np.asarray(series, dtype=float)
    n_time = series.shape[0]
    frequencies = fft.fftfreq(n_time, d=float(tr))
    phase = np.exp(2j * np.pi * frequencies * float(shift_seconds))
    return fft.ifft(fft.fft(series, axis=0) * phase[:, None], axis=0).real


def slice_timing_correct_volume(
    data4d: np.ndarray,
    tr: float,
    slice_order: list[int] | tuple[int, ...] | np.ndarray,
    reference_slice: int,
) -> np.ndarray:
    """Correct a 4D volume array ``(X, Y, Z, Time)`` for slice timing."""

    data = np.asarray(data4d, dtype=float)
    if data.ndim != 4:
        raise ValueError("Expected 4D functional data")
    shape = data.shape
    order = np.asarray(slice_order, dtype=int)
    if order.size != shape[2]:
        raise ValueError(f"slice_order has {order.size} entries but data has {shape[2]} slices")
    nslices = int(order.max())
    if reference_slice < 1 or reference_slice > nslices:
        raise ValueError("reference_slice must be within the slice order")
    time_first = np.moveaxis(data, -1, 0)  # (time, X, Y, Z)
    out = time_first.copy()
    for z in range(shape[2]):
        shift = (reference_slice - order[z]) * float(tr) / nslices
        series = out[:, :, :, z].reshape(time_first.shape[0], -1)
        out[:, :, :, z] = shift_series(series, shift, tr).reshape(out[:, :, :, z].shape)
    return np.moveaxis(out, 0, -1)


def _rotation_matrix(rx: float, ry: float, rz: float) -> np.ndarray:
    """Build a Z-Y-X rotation matrix from SPM-style rotation parameters."""

    cx, sx = np.cos(rx), np.sin(rx)
    cy, sy = np.cos(ry), np.sin(ry)
    cz, sz = np.cos(rz), np.sin(rz)
    rot_x = np.array([[1.0, 0.0, 0.0], [0.0, cx, -sx], [0.0, sx, cx]])
    rot_y = np.array([[cy, 0.0, sy], [0.0, 1.0, 0.0], [-sy, 0.0, cy]])
    rot_z = np.array([[cz, -sz, 0.0], [sz, cz, 0.0], [0.0, 0.0, 1.0]])
    return rot_z @ rot_y @ rot_x


def apply_motion_parameters(
    data: np.ndarray,
    motion_parameters: np.ndarray,
    affine: np.ndarray,
    *,
    order: int = 3,
    inverse: bool = True,
) -> np.ndarray:
    """Resample 4D data using SPM-style realignment parameters.

    ``motion_parameters`` columns are translations in mm (x, y, z) followed by
    rotations in radians (pitch, roll, yaw). With ``inverse=True``, the function
    undoes the motion, which is the operation needed for motion correction.
    With ``inverse=False``, it applies the motion to the input volumes.
    """

    data = np.asarray(data, dtype=float)
    if data.ndim != 4:
        raise ValueError("Expected 4D functional data")
    rp = np.asarray(motion_parameters, dtype=float)
    if rp.ndim != 2 or rp.shape[1] != 6 or rp.shape[0] != data.shape[3]:
        raise ValueError("motion_parameters must have shape (n_time, 6)")
    affine = np.asarray(affine, dtype=float)
    inv_affine = np.linalg.inv(affine)
    center = (np.asarray(data.shape[:3], dtype=float) - 1.0) / 2.0
    out = np.empty_like(data)
    for t in range(data.shape[3]):
        tx, ty, tz, rx, ry, rz = rp[t]
        rotation = _rotation_matrix(rx, ry, rz)
        inverse_rotation = np.linalg.inv(rotation)
        # Compose the voxel-coordinate sampling transform for the inverse motion.
        matrix = inv_affine[:3, :3] @ inverse_rotation @ affine[:3, :3]
        translation_world = np.array([tx, ty, tz])
        motion_offset = inverse_rotation @ translation_world
        offset = inv_affine[:3, :3] @ (motion_offset if inverse else -motion_offset)
        # Express the transform about the volume center for stable interpolation.
        matrix, offset = _recenter(matrix, offset, center)
        out[..., t] = ndimage.affine_transform(
            data[..., t],
            matrix,
            offset=offset,
            order=order,
            mode="constant",
            cval=0.0,
        )
    return out


def _recenter(matrix: np.ndarray, offset: np.ndarray, center: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return an affine transform expressed around a voxel-space center."""

    offset = np.asarray(offset, dtype=float)
    centered_offset = offset + matrix @ center - center
    return matrix, centered_offset


__all__ = [
    "apply_motion_parameters",
    "shift_series",
    "slice_timing_correct_volume",
]
