from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

import nibabel as nib
from neuroimaging_neuromodulation.io.nifti import load_volume
from neuroimaging_neuromodulation.segmentation.c6 import make_c6_mask
from neuroimaging_neuromodulation.segmentation.tissue import segment_tissue


def test_segment_real_stanford_t1(tmp_path: Path) -> None:
    t1 = Path.home() / ".dipy" / "stanford_hardi" / "t1.nii.gz"
    if not t1.exists():
        pytest.skip("Stanford T1 dataset is not downloaded")
    paths = segment_tissue(
        t1,
        tmp_path,
        grey_prior="neuroimaging_neuromodulation/data/grey.nii",
        white_prior="neuroimaging_neuromodulation/data/white.nii",
        csf_prior="neuroimaging_neuromodulation/data/csf.nii",
        iterations=5,
    )
    assert all(path.exists() for path in paths.values())
    _, label = load_volume(paths["label"])
    assert np.isfinite(label).all()
    assert len(np.unique(label)) >= 2


def test_make_c6_mask_keeps_largest_low_intensity_cluster(tmp_path: Path) -> None:
    data = np.full((20, 20, 20), 2000.0, dtype=np.float32)
    data[4:8, 4:8, 4:8] = 100.0
    data[14:17, 14:17, 14:17] = 100.0
    img = nib.Nifti1Image(data, np.eye(4))
    img.to_filename(tmp_path / "t1.nii")
    _, mask = make_c6_mask(tmp_path / "t1.nii", tmp_path / "c6.nii", threshold=1000.0)
    assert mask.shape == data.shape
    assert (mask[4:8, 4:8, 4:8] > 0).sum() > 0
    assert (mask[14:17, 14:17, 14:17] > 0).sum() > 0
    assert (tmp_path / "c6.nii").exists()
