from __future__ import annotations

from pathlib import Path

import numpy as np

from neuroimaging_neuromodulation.io.nifti import load_volume
from neuroimaging_neuromodulation.preprocess.imaging import flip_left_right
from neuroimaging_neuromodulation.preprocess.spatial import smooth_volume


def test_smooth_real_mask(package_data_dir: Path) -> None:
    img, data = load_volume(package_data_dir / "BrainMask_05_61x73x61.nii")
    smoothed = smooth_volume(data, 4.0, img.affine)
    assert smoothed.shape == data.shape
    assert np.isfinite(smoothed).all()
    assert (smoothed > 0).sum() > (data > 0).sum()


def test_flip_left_right_real_mask(package_data_dir: Path) -> None:
    img, data = load_volume(package_data_dir / "BrainMask_05_61x73x61.nii")
    flipped = flip_left_right(data)
    assert flipped.shape == data.shape
    assert np.array_equal(flipped[::-1], data)
