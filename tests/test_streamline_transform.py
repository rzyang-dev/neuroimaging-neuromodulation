from __future__ import annotations

import nibabel as nib
import numpy as np

from neuroimaging_neuromodulation.diffusion.transform import transform_streamlines_with_field


def test_transform_streamlines_with_identity_field() -> None:
    source = nib.Nifti1Image(np.zeros((10, 10, 10), dtype=np.float32), np.eye(4))
    grid = np.mgrid[0:10, 0:10, 0:10].astype(np.float32) + 1.0
    field = nib.Nifti1Image(np.moveaxis(grid, 0, -1), np.eye(4))
    reference_affine = np.eye(4)
    reference_affine[0, 3] = 10.0
    reference = nib.Nifti1Image(np.zeros((10, 10, 10), dtype=np.float32), reference_affine)
    streamline = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
    transformed = transform_streamlines_with_field(
        [streamline],
        field,
        source,
        reference,
        one_based=True,
        coordinate_system="voxel",
    )
    assert np.allclose(transformed[0], streamline + np.array([10.0, 0.0, 0.0]))


def test_transform_streamlines_with_world_identity_field() -> None:
    source = nib.Nifti1Image(np.zeros((10, 10, 10), dtype=np.float32), np.eye(4))
    grid = np.mgrid[0:10, 0:10, 0:10].astype(np.float32)
    world_grid = np.moveaxis(grid, 0, -1)
    field = nib.Nifti1Image(world_grid, np.eye(4))
    reference = nib.Nifti1Image(np.zeros((10, 10, 10), dtype=np.float32), np.eye(4))
    streamline = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
    transformed = transform_streamlines_with_field(
        [streamline],
        field,
        source,
        reference,
        coordinate_system="world",
    )
    assert np.allclose(transformed[0], streamline)
