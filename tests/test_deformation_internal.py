from __future__ import annotations

import numpy as np
from scipy import ndimage

from neuroimaging_neuromodulation.deformations.estimate import estimate_deformation
from neuroimaging_neuromodulation.io.nifti import load_volume, save_volume


def test_internal_deformation_recovers_shift(tmp_path) -> None:
    grid = np.indices((24, 24, 24), dtype=float)
    center = np.array([12.0, 12.0, 12.0])
    moving = np.exp(-np.sum((grid - center.reshape(3, 1, 1, 1)) ** 2, axis=0))
    static = ndimage.shift(moving, (2.0, 0.0, 0.0), order=1)
    reference = __import__("nibabel").Nifti1Image(
        np.zeros((24, 24, 24), dtype=np.float32),
        np.eye(4),
    )
    moving_path = tmp_path / "moving.nii"
    static_path = tmp_path / "static.nii"
    save_volume(moving, reference, moving_path)
    save_volume(static, reference, static_path)

    result = estimate_deformation(
        moving_path,
        static_path,
        tmp_path / "deform",
        level_iters=(1, 1, 1),
    )
    assert all(path.exists() for path in result.values())
    _, warped = load_volume(result["warped_moving"])
    mask = np.isfinite(warped) & np.isfinite(static)
    assert np.corrcoef(warped[mask].ravel(), static[mask].ravel())[0, 1] > 0.8
    _, y_field = load_volume(result["y_field"])
    _, iy_field = load_volume(result["iy_field"])
    assert y_field.shape[:3] == static.shape
    assert iy_field.shape[:3] == moving.shape
