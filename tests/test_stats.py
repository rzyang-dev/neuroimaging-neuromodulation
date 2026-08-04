from __future__ import annotations

import numpy as np

from neuroimaging_neuromodulation.stats.functional import (
    bandpass_filter,
    detrend_preserve_mean,
    fast_corr,
    ideal_filter,
    inverse_pearson,
    roi_correlation_matrix,
)
from neuroimaging_neuromodulation.stats.regression import regress, regress_out


def test_fast_corr_known_value() -> None:
    rng = np.random.default_rng(7)
    x = rng.normal(size=(100, 1))
    y = 2.0 * x + 0.1 * rng.normal(size=(100, 1))
    r = fast_corr(x, y)
    assert 0.99 < r[0, 0] <= 1.0


def test_fast_corr_handles_constant_columns() -> None:
    x = np.column_stack([np.ones(20), np.arange(20)])
    y = np.arange(20).reshape(20, 1)
    r = fast_corr(x, y)
    assert np.isfinite(r).all()


def test_inverse_pearson_monotonic() -> None:
    low = inverse_pearson(0.05, 100)
    high = inverse_pearson(0.001, 100)
    assert 0.0 < low < high < 1.0


def test_ideal_filter_band_preserves_signal() -> None:
    n = 256
    t = np.arange(n) * 2.0
    signal = np.sin(2 * np.pi * t * 0.02)
    filtered = ideal_filter(signal[:, None], 2.0, (0.01, 0.1))
    assert np.abs(np.corrcoef(signal, filtered[:, 0])[0, 1]) > 0.9


def test_bandpass_filter_restores_mean() -> None:
    data = np.arange(100, dtype=float).reshape(1, 100) + np.arange(100)[:, None]
    out = bandpass_filter(data, 2.0, (0.0, 0.2), mask=np.ones(data.shape[1], dtype=bool))
    assert np.allclose(np.mean(out, axis=0), np.mean(data, axis=0), atol=1e-8)


def test_bandpass_filter_small_voxel_count_uses_mask_orientation() -> None:
    rng = np.random.default_rng(19)
    data = rng.normal(size=(20, 200))
    mask = np.ones(data.shape[0], dtype=bool)
    out = bandpass_filter(data, 2.0, (0.01, 0.1), mask=mask)
    assert out.shape == data.shape
    assert np.allclose(np.mean(out, axis=1), np.mean(data, axis=1), atol=0.05)


def test_bandpass_filter_time_major_with_mask() -> None:
    rng = np.random.default_rng(21)
    data = rng.normal(size=(200, 20))
    mask = np.ones(data.shape[1], dtype=bool)
    out = bandpass_filter(data, 2.0, (0.01, 0.1), mask=mask, voxel_major=False)
    assert out.shape == data.shape
    assert np.allclose(np.mean(out, axis=0), np.mean(data, axis=0), atol=0.05)


def test_regression_residual_orthogonal() -> None:
    rng = np.random.default_rng(11)
    x = np.column_stack([np.ones(50), rng.normal(size=50)])
    y = x @ np.array([2.0, 3.0]) + rng.normal(size=50)
    beta, residual = regress(y, x)
    assert np.allclose(x @ beta + residual, y)
    assert np.abs(residual @ x[:, 1]) < 1e-8


def test_regress_out_shape() -> None:
    rng = np.random.default_rng(3)
    x = np.column_stack([np.ones(20), np.arange(20)])
    y = rng.normal(size=(20, 5))
    beta, residual = regress_out(y, x)
    assert beta.shape == (2, 5)
    assert residual.shape == y.shape


def test_roi_correlation_matrix_known() -> None:
    rng = np.random.default_rng(5)
    x = rng.normal(size=(100,))
    y = -x + 0.1 * rng.normal(size=100)
    data = np.column_stack([x, y]).T.reshape(2, 100)
    masks = [np.array([True, False]), np.array([False, True])]
    corr = roi_correlation_matrix(data, masks)
    assert corr.shape == (2, 2)
    assert abs(corr[0, 1]) > 0.9


def test_detrend_preserve_mean() -> None:
    time = np.arange(50, dtype=float)
    data = np.vstack([time, 10.0 + 2.0 * time])
    out = detrend_preserve_mean(data)
    assert np.allclose(np.mean(out, axis=1), np.mean(data, axis=1))
    assert np.allclose(np.diff(out[0, :]), 0.0, atol=1e-8)
