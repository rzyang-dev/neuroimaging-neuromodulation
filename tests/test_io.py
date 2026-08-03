from __future__ import annotations

from pathlib import Path

import nibabel as nib
import numpy as np

from neuroimaging_neuromodulation.io.nifti import load_4d_matrix, load_volume, save_volume


def test_load_real_mask(package_data_dir: Path) -> None:
    path = package_data_dir / "BrainMask_05_61x73x61.nii"
    img, data = load_volume(path)
    assert img.shape == (61, 73, 61)
    assert data.shape == (61, 73, 61)
    assert (data > 0).sum() > 10000


def test_save_roundtrip(tmp_path: Path, package_data_dir: Path) -> None:
    source = package_data_dir / "WhiteMask_09_61x73x61.nii"
    img, data = load_volume(source)
    out = save_volume(data, img, tmp_path / "roundtrip.nii")
    loaded = nib.load(out)
    assert loaded.shape == img.shape
    assert np.allclose(np.asanyarray(loaded.dataobj), data, atol=1e-6)


def test_load_4d_matrix(real_fmri_path: Path | None, real_fmri_available: bool) -> None:
    if not real_fmri_available:
        return
    img, matrix = load_4d_matrix(real_fmri_path)
    assert matrix.ndim == 2
    assert matrix.shape == (np.prod(img.shape[:3]), img.shape[3])
