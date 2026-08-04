"""Signal-processing and correlation primitives from the MATLAB toolbox."""

from __future__ import annotations

import numpy as np
from scipy import fft, signal, stats


def fast_corr(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Fast Pearson correlation between columns of ``x`` and ``y``.

    The original ``TMSfastCorr`` normalizes each column, replaces NaNs with
    zero, and computes ``X' * Y / (n - 1)``.
    """

    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if x.shape[0] != y.shape[0]:
        raise ValueError(f"Time dimensions must match: {x.shape[0]} != {y.shape[0]}")
    with np.errstate(divide="ignore", invalid="ignore"):
        x = (x - np.nanmean(x, axis=0, keepdims=True)) / np.nanstd(x, axis=0, ddof=1, keepdims=True)
        y = (y - np.nanmean(y, axis=0, keepdims=True)) / np.nanstd(y, axis=0, ddof=1, keepdims=True)
    x = np.where(np.isfinite(x), x, 0.0)
    y = np.where(np.isfinite(y), y, 0.0)
    return x.T @ y / (x.shape[0] - 1)


def inverse_pearson(p_value: float, n_samples: int) -> float:
    """Convert a two-tailed p-value to the corresponding Pearson r threshold."""

    if not 0 < p_value < 1:
        raise ValueError("p_value must be between 0 and 1")
    if n_samples <= 2:
        raise ValueError("n_samples must be greater than 2")
    t = stats.t.ppf(1 - p_value / 2.0, df=n_samples - 2)
    return float(np.sqrt(t**2 / (n_samples - 2 + t**2)))


def ideal_filter(
    data: np.ndarray,
    sample_period: float,
    band: tuple[float, float],
) -> np.ndarray:
    """Apply the ideal frequency-domain band-pass used by ``TMSIdealFilter``.

    ``data`` is shaped ``(n_timepoints, n_series)``. The returned series are
    zero-mean, matching the MATLAB implementation.
    """

    data = np.asarray(data, dtype=float)
    if data.ndim != 2:
        raise ValueError(f"Expected 2D data, got {data.shape}")
    sample_freq = 1.0 / float(sample_period)
    sample_length, n_series = data.shape
    padded_length = int(2 ** np.ceil(np.log2(sample_length)))
    low_cut, high_cut = band

    if low_cut >= sample_freq / 2:
        idx_low = padded_length // 2 + 1
    else:
        idx_low = int(np.ceil(low_cut * padded_length * sample_period + 1))

    if high_cut >= sample_freq / 2 or high_cut == 0:
        idx_high = padded_length // 2 + 1
    else:
        idx_high = int(np.trunc(high_cut * padded_length * sample_period + 1))

    if idx_low > idx_high:
        raise ValueError("Band lower cutoff exceeds upper cutoff")

    frequency_mask = np.zeros(padded_length, dtype=bool)
    frequency_mask[idx_low - 1 : idx_high] = True
    mirror_start_zero = padded_length - idx_low + 1
    mirror_end_zero = padded_length - idx_high + 1
    if mirror_start_zero <= padded_length and mirror_end_zero >= 1:
        frequency_mask[mirror_end_zero : mirror_start_zero + 1] = True

    demeaned = data - np.mean(data, axis=0, keepdims=True)
    padded = np.vstack([demeaned, np.zeros((padded_length - sample_length, n_series), dtype=float)])
    spectrum = fft.fft(padded, axis=0)
    spectrum[~frequency_mask, :] = 0
    filtered = fft.ifft(spectrum, axis=0).real[:sample_length, :]
    return filtered


def bandpass_filter(
    data: np.ndarray,
    tr: float,
    band: tuple[float, float],
    mask: np.ndarray | None = None,
    *,
    voxel_major: bool | None = None,
) -> np.ndarray:
    """Band-pass filter a functional matrix and restore the voxel mean.

    ``data`` may be ``(n_voxels, n_timepoints)`` (toolbox convention) or
    ``(n_timepoints, n_voxels)``. When a mask is supplied, its length is used to
    disambiguate the orientation unless ``voxel_major`` is set explicitly. The
    output shape matches the input shape.
    """

    data = np.asarray(data, dtype=float)
    if mask is not None:
        mask = np.asarray(mask, dtype=bool).reshape(-1)
        if voxel_major is None:
            if mask.size == data.shape[0] == data.shape[1]:
                voxel_major = data.shape[0] > data.shape[1]
            elif mask.size == data.shape[0]:
                voxel_major = True
            elif mask.size == data.shape[1]:
                voxel_major = False
            else:
                raise ValueError(
                    "Mask length does not match either matrix axis; pass voxel_major explicitly"
                )
        expected = data.shape[0] if voxel_major else data.shape[1]
        if mask.size != expected:
            raise ValueError("Mask length does not match the number of voxels")
    else:
        voxel_major = data.shape[0] > data.shape[1] if voxel_major is None else voxel_major
    matrix = data.T if voxel_major else data
    if mask is not None:
        means = np.mean(matrix[:, mask], axis=0, keepdims=True)
        filtered = ideal_filter(matrix[:, mask], tr, band)
        out = np.zeros_like(matrix)
        out[:, mask] = filtered + means
    else:
        means = np.mean(matrix, axis=0, keepdims=True)
        out = ideal_filter(matrix, tr, band) + means
    return out.T if voxel_major else out


def detrend(data: np.ndarray, axis: int = 0) -> np.ndarray:
    """Linear detrend with NaN-safe behavior."""

    data = np.asarray(data, dtype=float)
    nan_mask = ~np.isfinite(data)
    clean = np.where(nan_mask, 0.0, data)
    out = signal.detrend(clean, axis=axis)
    out[nan_mask] = np.nan
    return out


def detrend_preserve_mean(data: np.ndarray) -> np.ndarray:
    """Detrend voxel-by-time data and restore each voxel's original mean."""

    data = np.asarray(data, dtype=float)
    if data.ndim != 2:
        raise ValueError("Expected voxel-by-time data")
    means = np.mean(data, axis=1, keepdims=True)
    detrended = detrend(data.T, axis=0).T
    return detrended + means


def roi_correlation_matrix(
    data: np.ndarray,
    roi_masks: list[np.ndarray],
) -> np.ndarray:
    """Return the Pearson correlation matrix between ROI mean time courses.

    ``data`` has shape ``(n_voxels, n_timepoints)`` and each mask has the same
    voxel count.
    """

    data = np.asarray(data, dtype=float)
    if data.ndim != 2:
        raise ValueError("data must be a voxel-by-time matrix")
    timecourses = []
    for mask in roi_masks:
        mask = np.asarray(mask, dtype=bool).reshape(-1)
        if mask.size != data.shape[0]:
            raise ValueError("ROI mask length does not match voxel count")
        if not mask.any():
            raise ValueError("ROI mask is empty")
        timecourses.append(np.mean(data[mask, :], axis=0))
    return np.corrcoef(np.stack(timecourses, axis=0))


__all__ = [
    "bandpass_filter",
    "detrend",
    "detrend_preserve_mean",
    "fast_corr",
    "ideal_filter",
    "inverse_pearson",
    "roi_correlation_matrix",
]
