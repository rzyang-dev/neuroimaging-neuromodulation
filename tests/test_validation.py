from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("dipy")

from neuroimaging_neuromodulation.deformations.estimate import estimate_deformation  # noqa: E402
from neuroimaging_neuromodulation.validation.metrics import compare_volumes, validate_deformation  # noqa: E402


def test_compare_identical_images(package_data_dir: Path) -> None:
    path = package_data_dir / "BrainMask_05_61x73x61.nii"
    metrics = compare_volumes(path, path)
    assert metrics["correlation"] == pytest.approx(1.0)
    assert metrics["rmse"] == pytest.approx(0.0)


def test_validate_deformation_real_data(tmp_path: Path) -> None:
    t1 = Path.home() / ".dipy" / "stanford_hardi" / "t1.nii.gz"
    if not t1.exists():
        pytest.skip("Stanford T1 dataset is not downloaded")
    paths = estimate_deformation(
        t1,
        "neuroimaging_neuromodulation/data/grey333.nii",
        tmp_path / "def",
        metric="CC",
        level_iters=(2, 1, 1),
        step_length=0.25,
    )
    result = validate_deformation(
        t1,
        paths["iy_field"],
        paths["warped_moving"],
        order=1,
        output_json=tmp_path / "validation.json",
    )
    assert result["metrics"]["correlation"] > 0.5
    assert (tmp_path / "validation.json").exists()
