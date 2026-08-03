from __future__ import annotations

import numpy as np

from neuroimaging_neuromodulation.preprocess.temporal import (
    apply_motion_parameters,
    shift_series,
    slice_timing_correct_volume,
)


def test_shift_series_fourier() -> None:
    n = 128
    dt = 1.0
    frequency = 4.0 / n
    t = np.arange(n) * dt
    signal = np.sin(2 * np.pi * frequency * t)
    shifted = shift_series(signal[:, None], dt, dt)[:, 0]
    expected = np.sin(2 * np.pi * frequency * (t + dt))
    assert np.allclose(shifted, expected, atol=1e-8)


def test_slice_timing_correct_volume_aligns_slices() -> None:
    n_time = 128
    frequency = 4.0 / n_time
    t = np.arange(n_time)
    data = np.zeros((2, 2, 4, n_time))
    for z in range(4):
        data[:, :, z, :] = np.sin(2 * np.pi * frequency * (t + z / 4.0))
    corrected = slice_timing_correct_volume(data, 2.0, [1, 2, 3, 4], 1)
    for z in range(4):
        assert np.allclose(corrected[:, :, z, :], corrected[:, :, 0, :], atol=1e-6)


def test_motion_zero_params_identity() -> None:
    rng = np.random.default_rng(4)
    data = rng.normal(size=(8, 8, 8, 3))
    rp = np.zeros((3, 6))
    affine = np.diag([2.0, 2.0, 2.0, 1.0])
    out = apply_motion_parameters(data, rp, affine)
    assert np.allclose(out, data)


def test_motion_translation_moves_center_of_mass() -> None:
    data = np.zeros((20, 20, 20, 1))
    data[10, 10, 10, 0] = 1.0
    rp = np.array([[4.0, 0.0, 0.0, 0.0, 0.0, 0.0]])
    affine = np.diag([2.0, 2.0, 2.0, 1.0])
    out = apply_motion_parameters(data, rp, affine, order=1)
    center = np.unravel_index(np.argmax(out), out.shape[:3])
    assert tuple(center) == (8, 10, 10)
