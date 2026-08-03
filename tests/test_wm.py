from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from neuroimaging_neuromodulation.io.nifti import load_volume, resample_to_grid, save_volume
from neuroimaging_neuromodulation.wm.alff import compute_alff
from neuroimaging_neuromodulation.wm.masks import make_wm_mask


def test_alff_real_data(real_fmri_path: Path | None, real_fmri_available: bool, package_data_dir: Path, tmp_path: Path) -> None:
    if not real_fmri_available:
        pytest.skip("real fMRI data not available")
    func_img = __import__("nibabel").load(real_fmri_path)
    _, mask = resample_to_grid(package_data_dir / "BrainMask_05_61x73x61.nii", func_img, order=0)
    save_volume(mask, func_img, tmp_path / "mask.nii")
    paths = compute_alff(
        real_fmri_path,
        tmp_path / "mask.nii",
        tmp_path / "alff",
        tr=2.0,
        low_cutoff=0.01,
        high_cutoff=0.1,
    )
    assert all(path.exists() for path in paths.values())
    _, alff = load_volume(paths["ALFF"])
    assert np.isfinite(alff).all()
    assert (alff > 0).sum() > 0


def test_make_wm_mask_real_data(real_fmri_path: Path | None, real_fmri_available: bool, package_data_dir: Path, tmp_path: Path) -> None:
    if not real_fmri_available:
        pytest.skip("real fMRI data not available")
    path, mask = make_wm_mask(
        real_fmri_path,
        package_data_dir / "white.nii",
        package_data_dir / "excludHOAsub25prob617361.nii",
        tmp_path,
        threshold=0.9,
    )
    assert path.exists()
    assert mask.dtype == np.float32
    assert mask.sum() > 0
