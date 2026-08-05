from __future__ import annotations

from pathlib import Path

import nibabel as nib
import numpy as np
import pytest

from neuroimaging_neuromodulation.preprocess.motion import (  # noqa: E402
    affine_to_rp,
    estimate_motion_parameters,
)
from neuroimaging_neuromodulation.preprocess.motion_metrics import (  # noqa: E402
    fd_power,
    fd_van_dijk,
    head_motion_metrics,
)


def test_affine_to_rp_roundtrip() -> None:
    from scipy.spatial.transform import Rotation

    rotation = Rotation.from_euler("xyz", [0.01, -0.02, 0.03])
    affine = np.eye(4)
    affine[:3, :3] = rotation.as_matrix()
    affine[:3, 3] = [1.2, -2.3, 3.4]
    rp = affine_to_rp(affine)
    assert np.allclose(rp[:3], [1.2, -2.3, 3.4])
    assert np.allclose(rp[3:], [0.01, -0.02, 0.03])


def test_estimate_motion_real_subset(real_fmri_path: Path | None, real_fmri_available: bool) -> None:
    if not real_fmri_available:
        pytest.skip("real fMRI data not available")
    img = nib.load(real_fmri_path)
    data = np.asanyarray(img.dataobj)[..., :4]
    corrected, rp = estimate_motion_parameters(
        data,
        img.affine,
        reference_volume=0,
        pipeline=("translation", "rigid"),
        level_iters=(5, 2, 1),
        optimizer_options={"maxiter": 10},
    )
    assert corrected.shape == data.shape
    assert np.isfinite(corrected).all()
    assert rp.shape == (4, 6)
    assert np.allclose(rp[0], 0.0, atol=1e-6)


def test_head_motion_metrics_known_simple_series() -> None:
    reference = nib.Nifti1Image(np.zeros((10, 10, 10)), np.eye(4))
    rp = np.array(
        [
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [2.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ]
    )
    result = head_motion_metrics(rp, reference)
    assert np.allclose(result["fd_van_dijk"], [0.0, 1.0, 1.0])
    assert np.allclose(result["fd_power"], [0.0, 1.0, 1.0])
    assert result["fd_jenkinson"][0] == 0.0
    assert result["summary"].shape == (20,)


def test_fd_series_helpers() -> None:
    rp = np.zeros((4, 6))
    rp[:, 0] = [0.0, 0.5, 1.0, 1.5]
    assert np.allclose(fd_van_dijk(rp), [0.0, 0.5, 0.5, 0.5])
    assert np.allclose(fd_power(rp), [0.0, 0.5, 0.5, 0.5])
