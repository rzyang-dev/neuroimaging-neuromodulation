from __future__ import annotations

import numpy as np

from neuroimaging_neuromodulation.diffusion.dti import (
    GradientTable,
    fit_tensor,
)


def test_fit_tensor_without_dipy() -> None:
    bvals = np.array([0.0, 1000.0, 1000.0, 1000.0, 1000.0, 1000.0, 1000.0])
    bvecs = np.array(
        [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [1.0, 1.0, 0.0],
            [1.0, 0.0, 1.0],
            [0.0, 1.0, 1.0],
        ]
    )
    gtab = GradientTable(bvals=bvals, bvecs=bvecs)
    data = np.zeros((4, 4, 4, 7), dtype=float)
    data[..., 0] = 1000.0
    data[..., 1] = 700.0
    data[..., 2] = 850.0
    data[..., 3] = 850.0
    data[..., 4] = 770.0
    data[..., 5] = 770.0
    data[..., 6] = 800.0
    fit = fit_tensor(data, gtab, mask=data[..., 0] > 0)
    assert np.isfinite(fit.fa).all()
    assert np.isfinite(fit.md).all()
    assert np.isfinite(fit.ad).all()
    assert np.isfinite(fit.rd).all()
    mask = data[..., 0] > 0
    assert fit.fa[mask].mean() > 0.0
