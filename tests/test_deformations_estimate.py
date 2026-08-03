from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("dipy")

from neuroimaging_neuromodulation.deformations.estimate import estimate_deformation  # noqa: E402
from neuroimaging_neuromodulation.io.deformations import apply_deformation  # noqa: E402
from neuroimaging_neuromodulation.io.nifti import load_volume  # noqa: E402


def test_estimate_deformation_real_data(tmp_path: Path) -> None:
    t1 = Path.home() / ".dipy" / "stanford_hardi" / "t1.nii.gz"
    if not t1.exists():
        pytest.skip("Stanford T1 dataset is not downloaded")
    paths = estimate_deformation(
        t1,
        "neuroimaging_neuromodulation/data/grey333.nii",
        tmp_path,
        metric="CC",
        level_iters=(2, 1, 1),
        step_length=0.25,
    )
    assert all(path.exists() for path in paths.values())
    _, iy = load_volume(paths["iy_field"])
    _, y = load_volume(paths["y_field"])
    assert iy.shape[:3] == (61, 73, 61)
    assert y.shape[:3] == (81, 106, 76)
    _, warped = load_volume(paths["warped_moving"])
    _, resampled = apply_deformation(t1, paths["iy_field"], order=1)
    assert np.corrcoef(resampled.ravel(), warped.ravel())[0, 1] > 0.5
