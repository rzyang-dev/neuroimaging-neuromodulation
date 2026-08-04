from __future__ import annotations

import nibabel as nib
import numpy as np

from neuroimaging_neuromodulation.diffusion.tract_profile import tract_profile


def test_tract_profile_samples_scalar_image_along_streamline() -> None:
    data = np.broadcast_to(np.arange(20, dtype=float).reshape(20, 1, 1), (20, 20, 20)).copy()
    img = nib.Nifti1Image(data, np.eye(4))
    streamlines = [np.array([[2.0, 5.0, 5.0], [10.0, 5.0, 5.0], [18.0, 5.0, 5.0]])]
    result = tract_profile(streamlines, img, n_points=5)
    profile = np.asarray(result["profile"])
    assert profile.shape == (5,)
    assert profile[0] == 2.0
    assert profile[-1] == 18.0
    assert np.allclose(profile, np.linspace(2.0, 18.0, 5))
    assert result["n_streamlines"] == 1
    assert np.allclose(result["std"], 0.0)
