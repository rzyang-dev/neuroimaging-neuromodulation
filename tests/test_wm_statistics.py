from __future__ import annotations

import numpy as np

from neuroimaging_neuromodulation.wm.statistics import profile_group_statistics


def test_profile_group_statistics(tmp_path) -> None:
    rng = np.random.default_rng(0)
    profile = np.vstack(
        [
            1.0 + 0.1 * rng.normal(size=(3, 20)),
            3.0 + 0.1 * rng.normal(size=(3, 20)),
        ]
    )
    path = tmp_path / "profile.npy"
    np.save(path, profile)
    result = profile_group_statistics([path], n_group1=3)
    assert result["n_group2"] == 3
    assert len(result["profiles"]) == 1
    assert np.asarray(result["profiles"][0]["p"]).shape == (20,)
    assert np.min(result["profiles"][0]["p"]) < 0.05
