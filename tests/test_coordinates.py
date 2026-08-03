from __future__ import annotations

import numpy as np

from neuroimaging_neuromodulation.coordinates import (
    mat_to_mni,
    mni_to_mat,
    voxel_size,
)


def test_roundtrip_mni_matrix() -> None:
    affine = np.array(
        [
            [-3.0, 0.0, 0.0, 90.0],
            [0.0, 3.0, 0.0, -126.0],
            [0.0, 0.0, 3.0, -72.0],
            [0.0, 0.0, 0.0, 1.0],
        ]
    )
    mni = np.array([12.0, -30.0, 45.0])
    mat = mni_to_mat(mni, affine)
    restored = mat_to_mni(mat, affine)
    assert np.allclose(restored, mni)


def test_origin_matches_spm_template() -> None:
    affine = np.array(
        [
            [-3.0, 0.0, 0.0, 90.0],
            [0.0, 3.0, 0.0, -126.0],
            [0.0, 0.0, 3.0, -72.0],
            [0.0, 0.0, 0.0, 1.0],
        ]
    )
    origin = mni_to_mat([0.0, 0.0, 0.0], affine)
    assert list(origin) == [30, 42, 24]


def test_voxel_size() -> None:
    affine = np.diag([2.0, 3.0, 4.0, 1.0])
    assert np.allclose(voxel_size(affine), [2.0, 3.0, 4.0])
