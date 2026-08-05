from __future__ import annotations

import json
from pathlib import Path

import pytest

from neuroimaging_neuromodulation.io.nifti import count_timepoints
from neuroimaging_neuromodulation.targets.center import image_region_centers


def test_image_region_centers_real_mask(package_data_dir: Path, tmp_path: Path) -> None:
    image = package_data_dir / "BrainMask_05_61x73x61.nii"
    output_json = tmp_path / "centers.json"
    centers = image_region_centers(image, output_json)
    assert centers
    assert centers[0]["voxels"] > 0
    assert len(centers[0]["center_mni"]) == 3
    assert json.loads(output_json.read_text(encoding="utf-8")) == centers


def test_count_timepoints_real_fmri(real_fmri_path: Path | None) -> None:
    if real_fmri_path is None:
        pytest.skip("real fMRI data not available")
    assert count_timepoints(real_fmri_path) > 0
