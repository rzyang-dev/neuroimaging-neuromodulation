"""Nuisance regression helpers."""

from __future__ import annotations

import numpy as np

from ..stats.regression import regress_out


def friston24(motion_parameters: np.ndarray) -> np.ndarray:
    """Build the Friston-24 head-motion expansion from six rigid-body params."""

    h6 = np.asarray(motion_parameters, dtype=float)
    if h6.ndim != 2 or h6.shape[1] != 6:
        raise ValueError("Expected motion parameters with shape (n_time, 6)")
    lag = np.vstack([np.zeros((1, 6)), h6[:-1, :]])
    return np.hstack([h6, lag, h6**2, lag**2])


def extract_signal(data: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Extract the mean signal inside ``mask`` from a voxel-by-time matrix."""

    data = np.asarray(data, dtype=float)
    mask = np.asarray(mask, dtype=bool).reshape(-1)
    if mask.size != data.shape[0]:
        raise ValueError("Mask length does not match the number of voxels")
    if not mask.any():
        raise ValueError("Mask is empty")
    return np.nanmean(data[mask, :], axis=0)


def design_matrix(
    n_timepoints: int,
    motion_parameters: np.ndarray | None = None,
    wm_signal: np.ndarray | None = None,
    csf_signal: np.ndarray | None = None,
    global_signal: np.ndarray | None = None,
) -> np.ndarray:
    """Build a nuisance design matrix with constant, linear, motion, and ROI signals."""

    columns: list[np.ndarray] = [np.ones(n_timepoints), np.arange(1, n_timepoints + 1)]
    if motion_parameters is not None:
        columns.append(friston24(motion_parameters))
    for signal in (wm_signal, csf_signal, global_signal):
        if signal is not None:
            signal = np.asarray(signal, dtype=float).reshape(-1)
            if signal.size != n_timepoints:
                raise ValueError("Nuisance signal length does not match n_timepoints")
            columns.append(signal)
    design = np.column_stack(columns)
    if design.shape[1] > 1:
        design[:, 1:] -= np.mean(design[:, 1:], axis=0, keepdims=True)
    return design


def regress_out_nuisance(
    data: np.ndarray,
    design: np.ndarray,
    *,
    restore_intercept: bool = True,
) -> np.ndarray:
    """Regress nuisance columns from a voxel-by-time matrix.

    The original toolbox keeps the constant/modeled mean and adds it back to
    the residuals. Set ``restore_intercept=False`` to get pure residuals.
    """

    data = np.asarray(data, dtype=float)
    beta, residual = regress_out(data.T, design)
    if restore_intercept and design.shape[1] > 0:
        residual = residual + beta[0, :][None, :]
    return residual.T


__all__ = ["design_matrix", "extract_signal", "friston24", "regress_out_nuisance"]
