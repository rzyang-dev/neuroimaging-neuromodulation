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


def test_internal_deformation_recovers_smooth_nonlinear_warp(tmp_path) -> None:
    grid = np.indices((24, 24, 24), dtype=float)
    center = np.array([12.0, 12.0, 12.0])
    moving = np.exp(-np.sum((grid - center.reshape(3, 1, 1, 1)) ** 2, axis=0))
    coordinates = grid.copy()
    coordinates[0] = coordinates[0] + 2.0 * np.sin(grid[1] / 4.0)
    static = ndimage.map_coordinates(
        moving,
        coordinates,
        order=1,
        mode="constant",
        cval=0.0,
    )
    reference = __import__("nibabel").Nifti1Image(
        np.zeros((24, 24, 24), dtype=np.float32),
        np.eye(4),
    )
    moving_path = tmp_path / "moving-nonlinear.nii"
    static_path = tmp_path / "static-nonlinear.nii"
    save_volume(moving, reference, moving_path)
    save_volume(static, reference, static_path)
    result = estimate_deformation(
        moving_path,
        static_path,
        tmp_path / "deform-nonlinear",
        level_iters=(1, 1, 1),
    )
    _, warped = load_volume(result["warped_moving"])
    mask = np.isfinite(warped) & np.isfinite(static)
    assert np.corrcoef(warped[mask].ravel(), static[mask].ravel())[0, 1] > 0.9


def test_internal_deformation_recovers_nonlinear_warp_on_real_template(
    tmp_path,
    package_data_dir,
) -> None:
    from neuroimaging_neuromodulation.io.nifti import load_volume

    img, data = load_volume(package_data_dir / "grey333.nii")
    grid = np.indices(data.shape, dtype=float)
    coordinates = grid.copy()
    coordinates[0] = coordinates[0] + 1.5 * np.sin(grid[1] / 10.0)
    static = ndimage.map_coordinates(
        np.asarray(data, dtype=float),
        coordinates,
        order=1,
        mode="constant",
        cval=0.0,
    )
    moving_path = tmp_path / "real-moving.nii"
    static_path = tmp_path / "real-static.nii"
    save_volume(data, img, moving_path)
    save_volume(static, img, static_path)
    result = estimate_deformation(
        moving_path,
        static_path,
        tmp_path / "real-deform",
        level_iters=(1, 1, 1),
    )
    _, warped = load_volume(result["warped_moving"])
    mask = np.isfinite(warped) & np.isfinite(static)
    assert np.corrcoef(warped[mask].ravel(), static[mask].ravel())[0, 1] > 0.9
