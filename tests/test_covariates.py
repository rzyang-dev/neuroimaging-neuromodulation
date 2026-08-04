from __future__ import annotations

import numpy as np

from neuroimaging_neuromodulation.preprocess.covariates import extract_signal, friston24


def test_extract_signal_excludes_zero_values_like_original() -> None:
    data = np.array(
        [
            [0.0, 1.0],
            [2.0, 3.0],
            [4.0, 5.0],
        ]
    )
    mask = np.array([True, True, False])
    assert np.allclose(extract_signal(data, mask), [2.0, 2.0])


def test_extract_signal_all_zero_timepoint_is_nan() -> None:
    data = np.array(
        [
            [0.0, 1.0],
            [0.0, 2.0],
        ]
    )
    mask = np.array([True, True])
    result = extract_signal(data, mask)
    assert np.isnan(result[0])
    assert result[1] == 1.5


def test_friston24_shape_and_squared_terms() -> None:
    rp = np.array([[1.0, 0.0, 0.0, 0.0, 0.0, 0.0], [2.0, 0.0, 0.0, 0.0, 0.0, 0.0]])
    expanded = friston24(rp)
    assert expanded.shape == (2, 24)
    assert expanded[1, 6] == 1.0
    assert expanded[1, 12] == 4.0
