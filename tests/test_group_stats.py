from __future__ import annotations

import numpy as np

from neuroimaging_neuromodulation.stats.group import (
    chi_square_test,
    compare_correlation_coefficients,
    permutation_ttest,
    quantile_regression,
    ttest2_with_covariates,
)


def test_compare_correlation_coefficients() -> None:
    z, p = compare_correlation_coefficients(0.8, 0.2, 50, 50)
    assert np.isfinite(z)
    assert p < 0.05


def test_chi_square_test() -> None:
    observed = np.array([[10.0, 20.0], [20.0, 40.0]])
    assert np.isclose(chi_square_test(observed), 1.0, atol=1e-8)


def test_ttest2_with_covariates() -> None:
    rng = np.random.default_rng(0)
    group = np.repeat([0.0, 1.0], 20)
    cov = rng.normal(size=40)
    y = 1.0 + 0.5 * cov + 2.0 * group + rng.normal(size=40)
    t, p = ttest2_with_covariates(y, group, cov[:, None])
    assert t > 0
    assert p < 0.05


def test_quantile_regression() -> None:
    x = np.linspace(-2.0, 2.0, 60)
    y = 1.0 + 0.5 * x + 0.2 * np.random.default_rng(1).normal(size=60)
    result = quantile_regression(x, y, 0.5, order=1, nboot=5, random_seed=1)
    assert np.asarray(result["beta"]).shape == (2,)
    assert np.asarray(result["pse"]).shape == (2,)
    assert np.asarray(result["yfitci"]).shape == (60, 2)


def test_permutation_ttest() -> None:
    rng = np.random.default_rng(2)
    y = np.concatenate([rng.normal(size=20), rng.normal(loc=2.0, size=20)])
    group = np.repeat([False, True], 20)
    result = permutation_ttest(y, group, n_permutations=500, random_seed=1)
    assert result["t"] > 0
    assert result["p"] < 0.05
