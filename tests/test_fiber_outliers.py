from __future__ import annotations

import numpy as np

from neuroimaging_neuromodulation.diffusion.outliers import remove_fiber_outliers


def test_remove_fiber_outliers_removes_off_tract_streamline() -> None:
    rng = np.random.default_rng(3)
    x = np.linspace(0.0, 10.0, 10)
    core = []
    for _ in range(25):
        y = 5.0 + rng.normal(scale=0.1, size=10)
        z = 5.0 + rng.normal(scale=0.1, size=10)
        core.append(np.column_stack([x, y, z]))
    outlier = np.column_stack([x, 50.0 + np.zeros(10), 5.0 + np.zeros(10)])
    streamlines = core + [outlier]
    cleaned, keep = remove_fiber_outliers(
        streamlines,
        max_dist=4.0,
        max_len=4.0,
        num_nodes=10,
        max_iter=3,
    )
    assert len(cleaned) == 25
    assert keep.sum() == 25
    assert not keep[-1]
