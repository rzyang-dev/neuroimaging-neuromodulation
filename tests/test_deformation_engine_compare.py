from __future__ import annotations

import json

import numpy as np
import pytest
from scipy import ndimage

from neuroimaging_neuromodulation.io.nifti import save_volume
from neuroimaging_neuromodulation.validation.deformation import compare_deformation_engines


def test_compare_deformation_engines(tmp_path) -> None:
    grid = np.indices((40, 40, 40), dtype=float)
    center = np.array([20.0, 20.0, 20.0])
    moving = np.exp(-np.sum((grid - center.reshape(3, 1, 1, 1)) ** 2, axis=0))
    static = ndimage.shift(moving, (1.0, 0.0, 0.0), order=1)
    reference = __import__("nibabel").Nifti1Image(
        np.zeros((40, 40, 40), dtype=np.float32),
        np.eye(4),
    )
    moving_path = tmp_path / "moving.nii"
    static_path = tmp_path / "static.nii"
    save_volume(moving, reference, moving_path)
    save_volume(static, reference, static_path)
    result = compare_deformation_engines(
        moving_path,
        static_path,
        tmp_path / "compare",
        level_iters=(1, 1),
        output_json=tmp_path / "compare.json",
    )
    if not result["dipy_available"]:
        pytest.skip("DIPY optional engine is not available")
    assert (tmp_path / "compare.json").exists()
    metrics = json.loads((tmp_path / "compare.json").read_text(encoding="utf-8"))["metrics"]
    assert "correlation" in metrics
    assert np.isfinite(metrics["correlation"])
