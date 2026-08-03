from __future__ import annotations

from pathlib import Path

import nibabel as nib
import numpy as np
import pytest

pytest.importorskip("dipy")

from neuroimaging_neuromodulation.preprocess.coregister import coregister_images  # noqa: E402
from neuroimaging_neuromodulation.preprocess.temporal import apply_motion_parameters  # noqa: E402


def test_coregister_real_volume(real_fmri_path: Path | None, real_fmri_available: bool) -> None:
    if not real_fmri_available:
        pytest.skip("real fMRI data not available")
    img = nib.load(real_fmri_path)
    static = np.asanyarray(img.dataobj)[..., 0]
    moving = apply_motion_parameters(
        static[..., None],
        np.array([[4.0, 0.0, 0.0, 0.0, 0.0, 0.0]]),
        img.affine,
        inverse=False,
    )[..., 0]
    resampled, affine = coregister_images(
        moving,
        static,
        moving_affine=img.affine,
        static_affine=img.affine,
        pipeline=("translation", "rigid"),
        level_iters=(3, 2, 1),
        optimizer_options={"maxiter": 10},
    )
    assert resampled.shape == static.shape
    assert np.isfinite(resampled).all()
    assert np.isfinite(affine).all()
    correlation = np.corrcoef(resampled.ravel(), static.ravel())[0, 1]
    assert correlation > 0.9
