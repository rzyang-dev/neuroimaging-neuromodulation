"""Linear regression utilities matching the original ``TMSregression``."""

from __future__ import annotations

import numpy as np


def regress(y: np.ndarray, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return beta coefficients and residuals for ``y = X b + r``."""

    y = np.asarray(y, dtype=float).reshape(-1)
    x = np.asarray(x, dtype=float)
    if x.ndim != 2 or x.shape[0] != y.size:
        raise ValueError("Design matrix must be 2D with rows equal to observations")
    beta, _, _, _ = np.linalg.lstsq(x, y, rcond=None)
    residual = y - x @ beta
    return beta, residual


def regress_out(y_matrix: np.ndarray, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Regress columns of ``y_matrix`` on the same design matrix.

    Input ``y_matrix`` is ``(n_timepoints, n_series)``. The first row of the
    returned residuals can be restored with the intercept beta when needed.
    """

    y_matrix = np.asarray(y_matrix, dtype=float)
    x = np.asarray(x, dtype=float)
    if y_matrix.shape[0] != x.shape[0]:
        raise ValueError("Design matrix and data must have the same number of timepoints")
    beta, _, _, _ = np.linalg.lstsq(x, y_matrix, rcond=None)
    residual = y_matrix - x @ beta
    return beta, residual


__all__ = ["regress", "regress_out"]
