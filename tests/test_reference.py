from __future__ import annotations

import numpy as np

from neuroimaging_neuromodulation.preprocess.motion_metrics import fd_power, fd_van_dijk
from neuroimaging_neuromodulation.stats.functional import ideal_filter


def _matlab_style_ideal_filter(
    data: np.ndarray,
    sample_period: float,
    band: tuple[float, float],
) -> np.ndarray:
    n_time = data.shape[0]
    padded_length = int(2 ** np.ceil(np.log2(n_time)))
    sample_freq = 1.0 / sample_period
    low_cutoff, high_cutoff = band
    if low_cutoff >= sample_freq / 2:
        idx_low = padded_length // 2 + 1
    else:
        idx_low = int(np.ceil(low_cutoff * padded_length * sample_period + 1))
    if high_cutoff >= sample_freq / 2 or high_cutoff == 0:
        idx_high = padded_length // 2 + 1
    else:
        idx_high = int(np.trunc(high_cutoff * padded_length * sample_period + 1))
    frequency_mask = np.zeros(padded_length, dtype=bool)
    frequency_mask[idx_low - 1 : idx_high] = True
    mirror_start = padded_length - idx_low + 2
    mirror_end = padded_length - idx_high + 2
    frequency_mask[mirror_end - 1 : mirror_start] = True
    demeaned = data - np.mean(data, axis=0, keepdims=True)
    padded = np.vstack([demeaned, np.zeros((padded_length - n_time, data.shape[1]))])
    spectrum = np.fft.fft(padded, axis=0)
    spectrum[~frequency_mask, :] = 0.0
    return np.fft.ifft(spectrum, axis=0).real[:n_time, :]


def test_ideal_filter_matches_matlab_frequency_mask_reference() -> None:
    rng = np.random.default_rng(7)
    for n_time in (10, 16, 20, 100):
        for band in ((0.01, 0.1), (0.02, 0.2), (0.0, 0.2)):
            data = rng.normal(size=(n_time, 4))
            actual = ideal_filter(data, 2.0, band)
            expected = _matlab_style_ideal_filter(data, 2.0, band)
            assert np.allclose(actual, expected, atol=1e-12)


def test_fd_metrics_match_original_formulas() -> None:
    rp = np.array(
        [
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [2.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ]
    )
    expected_power = np.array([0.0, 1.0, 1.0])
    expected_vandijk = np.array([0.0, 1.0, 1.0])
    assert np.allclose(fd_power(rp), expected_power)
    assert np.allclose(fd_van_dijk(rp), expected_vandijk)
