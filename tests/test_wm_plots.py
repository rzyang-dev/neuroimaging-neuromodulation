from __future__ import annotations

import numpy as np

from neuroimaging_neuromodulation.wm.plots import plot_group_profiles


def test_plot_group_profiles_creates_svg(tmp_path) -> None:
    rng = np.random.default_rng(0)
    profile = np.vstack(
        [
            1.0 + 0.1 * rng.normal(size=(3, 20)),
            2.0 + 0.1 * rng.normal(size=(3, 20)),
        ]
    )
    path = tmp_path / "profile.npy"
    np.save(path, profile)
    outputs = plot_group_profiles(
        [path],
        tmp_path / "plots",
        n_group1=3,
        labels=["Left Corticospinal"],
    )
    assert len(outputs) == 1
    content = outputs[0].read_text(encoding="utf-8")
    assert "<svg" in content
    assert "Group 1" in content
    assert "Group 2" in content
