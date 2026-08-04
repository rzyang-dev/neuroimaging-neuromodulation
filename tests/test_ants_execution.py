from __future__ import annotations

import shutil
import subprocess

import numpy as np
import pytest

from neuroimaging_neuromodulation.diffusion.transform import transform_streamlines_with_ants
from neuroimaging_neuromodulation.preprocess.ants import (
    run_ants_apply_transform,
    run_ants_apply_transforms_to_points,
    run_ants_registration,
)


@pytest.mark.skipif(shutil.which("antsRegistration") is None, reason="ANTs antsRegistration not installed")
def test_ants_registration_binary_execution() -> None:
    result = subprocess.run(
        ["antsRegistration", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0


@pytest.mark.skipif(shutil.which("antsApplyTransforms") is None, reason="ANTs antsApplyTransforms not installed")
def test_ants_apply_transform_binary_execution() -> None:
    result = subprocess.run(
        ["antsApplyTransforms", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0


@pytest.mark.skipif(
    shutil.which("antsRegistration") is None or shutil.which("antsApplyTransforms") is None,
    reason="ANTs not installed",
)
def test_ants_registration_and_apply_real_templates(package_data_dir, tmp_path) -> None:
    moving = package_data_dir / "grey.nii"
    fixed = package_data_dir / "white.nii"
    prefix = tmp_path / "warp"
    result = run_ants_registration(
        moving,
        fixed,
        prefix,
        stages=("rigid", "affine"),
    )
    assert result["returncode"] == 0
    affine = tmp_path / "warp0GenericAffine.mat"
    assert affine.exists()
    output = tmp_path / "warped.nii.gz"
    applied = run_ants_apply_transform(
        moving,
        fixed,
        output,
        [affine],
    )
    assert applied["returncode"] == 0
    assert output.exists()
    points_csv = tmp_path / "points.csv"
    points_out = tmp_path / "points_out.csv"
    points_csv.write_text("x,y,z,t\n1,2,3,0\n4,5,6,1\n", encoding="ascii")
    points_result = run_ants_apply_transforms_to_points(
        points_csv,
        points_out,
        [affine],
    )
    assert points_result["returncode"] == 0
    assert points_out.exists()
    streamlines = transform_streamlines_with_ants(
        [np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])],
        [affine],
    )
    assert len(streamlines) == 1
    assert streamlines[0].shape == (2, 3)
