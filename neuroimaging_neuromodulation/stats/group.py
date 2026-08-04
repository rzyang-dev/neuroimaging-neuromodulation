"""Group-level statistical helpers from the original Others/ directory."""

from __future__ import annotations

import numpy as np
from scipy import optimize, stats


def compare_correlation_coefficients(
    r1: float | np.ndarray,
    r2: float | np.ndarray,
    n1: int,
    n2: int,
    tail: str = "both",
) -> tuple[np.ndarray, np.ndarray]:
    """Compare two correlation coefficients using Fisher z transformation."""

    z1 = np.arctanh(np.asarray(r1, dtype=float))
    z2 = np.arctanh(np.asarray(r2, dtype=float))
    zscore = (z1 - z2) / np.sqrt(1.0 / (n1 - 3) + 1.0 / (n2 - 3))
    if tail == "right":
        pvalue = stats.norm.cdf(-zscore)
    elif tail == "left":
        pvalue = stats.norm.cdf(zscore)
    elif tail == "both":
        pvalue = 2.0 * stats.norm.cdf(-np.abs(zscore))
    else:
        raise ValueError("tail must be 'right', 'left', or 'both'")
    return zscore, pvalue


def chi_square_test(observed: np.ndarray) -> float:
    """Return the p-value for a chi-square test on an observed contingency table."""

    observed = np.asarray(observed, dtype=float)
    if observed.ndim != 2 or observed.size == 0:
        raise ValueError("observed must be a non-empty 2D contingency table")
    row_sums = observed.sum(axis=1, keepdims=True)
    col_sums = observed.sum(axis=0, keepdims=True)
    total = observed.sum()
    expected = row_sums @ col_sums / total
    q = np.sum((observed - expected) ** 2 / expected)
    df = (observed.shape[0] - 1) * (observed.shape[1] - 1)
    return float(stats.chi2.sf(q, df))


def ttest2_with_covariates(
    dep_var: np.ndarray,
    group_label: np.ndarray,
    covs: np.ndarray | None = None,
) -> tuple[float, float]:
    """Run the original two-group t-test with covariates."""

    y = np.asarray(dep_var, dtype=float).reshape(-1)
    group = np.asarray(group_label, dtype=float).reshape(-1)
    if y.size != group.size:
        raise ValueError("dep_var and group_label must have the same length")
    cov_matrix = np.asarray(covs, dtype=float) if covs is not None else np.empty((y.size, 0))
    if cov_matrix.ndim != 2 or cov_matrix.shape[0] != y.size:
        raise ValueError("covs must have rows equal to dep_var")

    reduced_x = np.column_stack([np.ones(y.size), cov_matrix])
    full_x = np.column_stack([np.ones(y.size), group, cov_matrix])
    df_e = y.size - full_x.shape[1]
    if df_e <= 0:
        raise ValueError("Not enough observations for the covariate model")
    beta_reduced, _ = np.linalg.lstsq(reduced_x, y, rcond=None)[:2]
    sse_h = float(np.sum((y - reduced_x @ beta_reduced) ** 2))
    beta_full, _ = np.linalg.lstsq(full_x, y, rcond=None)[:2]
    sse = float(np.sum((y - full_x @ beta_full) ** 2))
    f = ((sse_h - sse) / 1.0) / (sse / df_e)
    pvalue = float(stats.f.sf(f, 1, df_e))
    t = float(np.sqrt(f) * np.sign(beta_full[1]))
    return t, pvalue


def quantile_regression(
    x: np.ndarray,
    y: np.ndarray,
    tau: float,
    order: int = 1,
    nboot: int = 200,
    random_seed: int = 0,
) -> dict[str, object]:
    """Fit quantile regression using the original rho objective."""

    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float).reshape(-1)
    if x.ndim == 1:
        x = x[:, None]
    if x.ndim != 2 or x.shape[0] != y.size:
        raise ValueError("x and y must have the same number of rows")
    if not 0 < tau < 1:
        raise ValueError("tau must be between 0 and 1")
    if x.shape[1] == 1:
        order = abs(int(order))
        if order == 0:
            design = np.ones((y.size, 1))
        else:
            powers = np.arange(order, -1, -1)
            design = np.column_stack([x[:, 0] ** power for power in powers])
    else:
        design = x

    def rho(beta: np.ndarray) -> float:
        residual = y - design @ beta
        return float(np.sum(np.abs(residual * (tau - (residual < 0)))))

    beta0 = np.linalg.lstsq(design, y, rcond=None)[0]
    result = optimize.minimize(rho, beta0, method="Nelder-Mead")
    if not result.success:
        raise RuntimeError(f"Quantile regression failed to converge: {result.message}")
    beta = result.x
    yfit = design @ beta
    residual = y - yfit

    rng = np.random.default_rng(random_seed)
    boot = np.empty((nboot, beta.size))
    for i in range(nboot):
        boot_y = yfit + rng.choice(residual, size=y.size, replace=True)
        boot_result = optimize.minimize(
            lambda b: float(np.sum(np.abs((boot_y - design @ b) * (tau - ((boot_y - design @ b) < 0))))),
            beta,
            method="Nelder-Mead",
        )
        boot[i] = boot_result.x
    yfit_boot = design @ boot.T
    return {
        "beta": beta,
        "pse": np.std(boot, axis=0),
        "pboot": boot,
        "yfitci": np.percentile(yfit_boot, [2.5, 97.5], axis=1).T,
    }


def permutation_ttest(
    y: np.ndarray,
    group: np.ndarray,
    *,
    n_permutations: int = 5000,
    random_seed: int = 0,
) -> dict[str, float]:
    """Run a permutation two-sample t-test."""

    y = np.asarray(y, dtype=float).reshape(-1)
    group = np.asarray(group, dtype=bool).reshape(-1)
    if y.size != group.size:
        raise ValueError("y and group must have the same length")
    if group.sum() == 0 or group.sum() == group.size:
        raise ValueError("group must contain both classes")
    observed = float(stats.ttest_ind(y[group], y[~group], equal_var=False)[0])
    rng = np.random.default_rng(random_seed)
    extreme = 1
    for _ in range(int(n_permutations)):
        permuted = rng.permutation(group)
        permuted_t = stats.ttest_ind(y[permuted], y[~permuted], equal_var=False)[0]
        if abs(permuted_t) >= abs(observed):
            extreme += 1
    return {
        "t": observed,
        "p": extreme / (int(n_permutations) + 1),
    }


__all__ = [
    "chi_square_test",
    "compare_correlation_coefficients",
    "permutation_ttest",
    "quantile_regression",
    "ttest2_with_covariates",
]
