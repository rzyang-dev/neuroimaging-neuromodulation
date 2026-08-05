from __future__ import annotations

import os
import shutil

import nibabel as nib
import numpy as np
import pytest

from neuroimaging_neuromodulation.diffusion import external

_RUN_EXTERNAL = os.environ.get("NM_RUN_EXTERNAL") == "1"
pytestmark = pytest.mark.skipif(
    not _RUN_EXTERNAL,
    reason="set NM_RUN_EXTERNAL=1 to run optional external-runtime tests",
)


@pytest.mark.skipif(shutil.which("bet") is None, reason="FSL BET not installed")
def test_fsl_bet_execution(tmp_path) -> None:
    image = tmp_path / "data.nii"
    size = 32
    z, y, x = np.mgrid[0:size, 0:size, 0:size]
    center = size / 2
    radius_sq = 120.0
    distance_sq = (x - center) ** 2 + (y - center) ** 2 + (z - center) ** 2
    data = np.where(distance_sq < radius_sq, 120.0 - distance_sq * 0.5, 0.0).astype(
        np.float32
    )
    nib.Nifti1Image(data, np.diag([2.0, 2.0, 2.0, 1.0])).to_filename(image)
    output = tmp_path / "dataB.nii.gz"
    result = external.run_fsl_bet(image, output)
    assert result["returncode"] == 0
    assert output.exists()


@pytest.mark.skipif(shutil.which("eddy_correct") is None, reason="FSL eddy_correct not installed")
def test_fsl_eddy_correct_execution(tmp_path) -> None:
    image = tmp_path / "dataB.nii"
    nib.Nifti1Image(
        np.ones((8, 8, 8, 4), dtype=np.float32),
        np.eye(4),
    ).to_filename(image)
    output = tmp_path / "dataBC.nii.gz"
    result = external.run_fsl_eddy_correct(image, output, reference_volume=0)
    assert result["returncode"] == 0
    assert output.exists()


@pytest.mark.skipif(shutil.which("tckgen") is None, reason="MRtrix tckgen not installed")
def test_mrtrix_tckgen_execution(tmp_path) -> None:
    dwi = tmp_path / "dwi.nii"
    mask = tmp_path / "mask.nii"
    seed = tmp_path / "seed.nii"
    output = tmp_path / "tracks.tck"
    nib.Nifti1Image(
        np.ones((8, 8, 8, 2), dtype=np.float32),
        np.eye(4),
    ).to_filename(dwi)
    seed_data = np.zeros((8, 8, 8), dtype=np.uint8)
    seed_data[2:6, 2:6, 2:6] = 1
    nib.Nifti1Image(seed_data, np.eye(4)).to_filename(mask)
    nib.Nifti1Image(seed_data, np.eye(4)).to_filename(seed)
    result = external.run_mrtrix_tckgen(
        dwi,
        mask,
        output,
        algorithm="SeedTest",
        num_tracks=2,
        seed_image=seed,
    )
    assert result["returncode"] == 0
    assert output.exists()
