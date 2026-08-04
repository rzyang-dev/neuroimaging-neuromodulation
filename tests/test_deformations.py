from __future__ import annotations

from pathlib import Path

import numpy as np

from neuroimaging_neuromodulation.io.deformations import (
    apply_deformation,
    deformation_coordinates,
    identity_deformation,
)
from neuroimaging_neuromodulation.io.nifti import load_volume


def test_identity_deformation_preserves_real_mask(package_data_dir: Path, tmp_path: Path) -> None:
    source = package_data_dir / "BrainMask_05_61x73x61.nii"
    img, data = load_volume(source)
    _, _ = identity_deformation(img, tmp_path / "identity_def.nii")
    out_img, out_data = apply_deformation(source, tmp_path / "identity_def.nii", tmp_path / "identity_out.nii", order=0)
    assert out_img.shape == img.shape
    assert np.allclose(out_data, data, atol=1e-6)


def test_shifted_deformation_moves_real_mask(package_data_dir: Path, tmp_path: Path) -> None:
    source = package_data_dir / "WhiteMask_09_61x73x61.nii"
    img, data = load_volume(source)
    _, coords = identity_deformation(img)
    shifted = coords.copy()
    delta = img.affine @ np.array([1.0, 0.0, 0.0, 0.0])
    shifted[..., :3] += delta[:3]
    def_img = type(img)(shifted, img.affine)
    _, out_data = apply_deformation(source, def_img, order=0)
    interior = out_data[:-2, :, :]
    expected_interior = data[1:-1, :, :]
    assert np.allclose(interior[interior > 0], expected_interior[interior > 0], atol=1e-6)


def test_deformation_coordinates_shape(package_data_dir: Path, tmp_path: Path) -> None:
    source = package_data_dir / "grey333.nii"
    img = __import__("nibabel").load(source)
    _, _ = identity_deformation(img, tmp_path / "def.nii")
    def_img, coords = deformation_coordinates(tmp_path / "def.nii", source_image=source)
    assert def_img.shape == (*img.shape, 3)
    assert coords.shape == (3, *img.shape[:3])


def test_voxel_coordinate_deformation_remains_supported(package_data_dir: Path, tmp_path: Path) -> None:
    source = package_data_dir / "BrainMask_05_61x73x61.nii"
    img, data = load_volume(source)
    _, _ = identity_deformation(img, tmp_path / "voxel_def.nii", coordinate_system="voxel")
    out_img, out_data = apply_deformation(
        source,
        tmp_path / "voxel_def.nii",
        coordinate_system="voxel",
        order=0,
    )
    assert out_img.shape == img.shape
    assert np.allclose(out_data, data, atol=1e-6)
