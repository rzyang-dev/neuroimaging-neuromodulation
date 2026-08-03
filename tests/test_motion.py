from __future__ import annotations

from pathlib import Path

import nibabel as nib
import numpy as np
import pytest

pytest.importorskip("dipy")

from neuroimaging_neuromodulation.preprocess.motion import (  # noqa: E402
    affine_to_rp,
    estimate_motion_parameters,
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
        return
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
