"""Head-motion metrics matching the original WMfun/HMCalc workflow."""

from __future__ import annotations

from pathlib import Path

import nibabel as nib
import numpy as np


def _rigid_matrix(rp: np.ndarray) -> np.ndarray:
    """Build the SPM-style rigid transform used by y_FD_Jenkinson.m."""

    tx, ty, tz, rx, ry, rz = rp
    cx, sx = np.cos(rx), np.sin(rx)
    cy, sy = np.cos(ry), np.sin(ry)
    cz, sz = np.cos(rz), np.sin(rz)
    m1 = np.array(
        [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, cx, sx, 0.0],
            [0.0, -sx, cx, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ]
    )
    m2 = np.array(
        [
            [cy, 0.0, sy, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [-sy, 0.0, cy, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ]
    )
    m3 = np.array(
        [
            [cz, sz, 0.0, 0.0],
            [-sz, cz, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ]
    )
    mt = np.eye(4)
    mt[:3, 3] = [tx, ty, tz]
    return mt @ m1 @ m2 @ m3


def _rms_from_difference(m: np.ndarray, center: np.ndarray, radius: float = 80.0) -> float:
    a = m[:3, :3]
    t = m[:3, 3]
    return float(
        np.sqrt(
            radius * radius / 5.0 * np.trace(a.T @ a)
            + (t + a @ center) @ (t + a @ center)
        )
    )


def fd_jenkinson(
    motion_parameters: np.ndarray,
    reference_image: str | Path | nib.Nifti1Image,
) -> np.ndarray:
    """Return FD_Jenkinson relative RMS, with the first timepoint set to zero."""

    rp = np.asarray(motion_parameters, dtype=float)
    if rp.ndim != 2 or rp.shape[1] != 6:
        raise ValueError("motion_parameters must have shape (n_time, 6)")
    if isinstance(reference_image, nib.Nifti1Image):
        ref_img = reference_image
    else:
        ref_img = nib.load(str(reference_image))
    center = (ref_img.affine @ np.array([0.5 * ref_img.shape[0], 0.5 * ref_img.shape[1], 0.5 * ref_img.shape[2], 1.0]))[:3]
    rel = np.zeros(rp.shape[0])
    for t in range(1, rp.shape[0]):
        m_prev = _rigid_matrix(rp[t - 1])
        m_curr = _rigid_matrix(rp[t])
        rel[t] = _rms_from_difference(m_prev @ np.linalg.inv(m_curr) - np.eye(4), center)
    return rel


def fd_van_dijk(motion_parameters: np.ndarray) -> np.ndarray:
    """Return the Van Dijk framewise-displacement series."""

    rp = np.asarray(motion_parameters, dtype=float)
    if rp.ndim != 2 or rp.shape[1] != 6:
        raise ValueError("motion_parameters must have shape (n_time, 6)")
    rms = np.sqrt(np.sum(rp[:, :3] ** 2, axis=1))
    fd = np.abs(np.diff(rms, prepend=0.0))
    return fd


def fd_power(motion_parameters: np.ndarray) -> np.ndarray:
    """Return the Power framewise-displacement series."""

    rp = np.asarray(motion_parameters, dtype=float)
    if rp.ndim != 2 or rp.shape[1] != 6:
        raise ValueError("motion_parameters must have shape (n_time, 6)")
    diff = np.diff(rp, prepend=np.zeros((1, 6)), axis=0)
    diff_sphere = diff.copy()
    diff_sphere[:, 3:] *= 50.0
    return np.sum(np.abs(diff_sphere), axis=1)


def head_motion_metrics(
    motion_parameters: np.ndarray,
    reference_image: str | Path | nib.Nifti1Image,
) -> dict[str, object]:
    """Compute the original HMCalc summary and component series."""

    rp = np.asarray(motion_parameters, dtype=float)
    if rp.ndim != 2 or rp.shape[1] != 6:
        raise ValueError("motion_parameters must have shape (n_time, 6)")
    max_rp = np.max(np.abs(rp), axis=0)
    mean_rp = np.mean(np.abs(rp), axis=0)
    max_degrees = max_rp.copy()
    max_degrees[3:] *= 180.0 / np.pi
    mean_degrees = mean_rp.copy()
    mean_degrees[3:] *= 180.0 / np.pi

    rms = np.sqrt(np.sum(rp[:, :3] ** 2, axis=1))
    fd_vandijk = fd_van_dijk(rp)
    fd_power_series = fd_power(rp)
    fd_jenkinson_series = fd_jenkinson(rp, reference_image)

    summary = np.concatenate(
        [
            max_degrees,
            mean_degrees,
            [float(np.mean(rms))],
            [float(np.mean(fd_vandijk))],
            [float(np.mean(fd_power_series))],
            [int(np.sum(fd_power_series > 0.5))],
            [float(np.mean(fd_power_series > 0.5))],
            [int(np.sum(fd_power_series > 0.2))],
            [float(np.mean(fd_power_series > 0.2))],
            [float(np.mean(fd_jenkinson_series))],
        ]
    )
    return {
        "summary": summary,
        "max_abs_degrees": max_degrees,
        "mean_abs_degrees": mean_degrees,
        "mean_rms": float(np.mean(rms)),
        "fd_van_dijk": fd_vandijk,
        "fd_power": fd_power_series,
        "fd_jenkinson": fd_jenkinson_series,
    }


__all__ = ["fd_jenkinson", "fd_power", "fd_van_dijk", "head_motion_metrics"]
