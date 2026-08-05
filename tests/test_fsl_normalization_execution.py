from __future__ import annotations

import os
import shutil

import nibabel as nib
import numpy as np
import pytest

from neuroimaging_neuromodulation.deformations.estimate import estimate_deformation
from neuroimaging_neuromodulation.diffusion.external import (
    build_fsl_fnirt_command,
    run_fsl_fnirt,
)
from neuroimaging_neuromodulation.io.nifti import load_volume, resample_to_grid

_RUN_EXTERNAL = os.environ.get("NM_RUN_EXTERNAL") == "1"
pytestmark = pytest.mark.skipif(
    not _RUN_EXTERNAL,
    reason="set NM_RUN_EXTERNAL=1 to run optional external-runtime tests",
)


@pytest.mark.skipif(shutil.which("fnirt") is None, reason="FSL FNIRT not installed")
def test_fsl_normalization_execution(package_data_dir, tmp_path) -> None:
    moving = package_data_dir / "grey.nii"
    static = package_data_dir / "white.nii"
    coeff = tmp_path / "coeff"
    warped = tmp_path / "warped.nii.gz"
    cmd = build_fsl_fnirt_command(moving, static, coeff, iout=warped)
    assert any(arg.startswith("--iout=") for arg in cmd)
    result = run_fsl_fnirt(moving, static, coeff, iout=warped)
    assert result["returncode"] == 0
    assert warped.exists()
    dipy = estimate_deformation(
        moving,
        static,
        tmp_path / "dipy",
        metric="CC",
        level_iters=(2, 1, 1),
        step_length=0.25,
    )
    fsl_img = nib.load(warped)
    dipy_img = nib.load(dipy["warped_moving"])
    if fsl_img.shape[:3] != dipy_img.shape[:3]:
        _, fsl_data = resample_to_grid(warped, dipy_img, order=1)
    else:
        _, fsl_data = load_volume(warped)
    _, dipy_data = load_volume(dipy["warped_moving"])
    fsl_flat = np.asarray(fsl_data, dtype=float).ravel()
    dipy_flat = np.asarray(dipy_data, dtype=float).ravel()
    mask = np.isfinite(fsl_flat) & np.isfinite(dipy_flat)
    correlation = float(np.corrcoef(fsl_flat[mask], dipy_flat[mask])[0, 1])
    assert correlation > 0.3
