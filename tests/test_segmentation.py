from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from neuroimaging_neuromodulation.io.nifti import load_volume
from neuroimaging_neuromodulation.segmentation.tissue import segment_tissue


def test_segment_real_stanford_t1(tmp_path: Path) -> None:
    t1 = Path.home() / ".dipy" / "stanford_hardi" / "t1.nii.gz"
    if not t1.exists():
        pytest.skip("Stanford T1 dataset is not downloaded")
    paths = segment_tissue(
        t1,
        tmp_path,
        grey_prior="neuroimaging_neuromodulation/data/grey.nii",
        white_prior="neuroimaging_neuromodulation/data/white.nii",
        csf_prior="neuroimaging_neuromodulation/data/csf.nii",
        iterations=5,
    )
    assert all(path.exists() for path in paths.values())
    _, label = load_volume(paths["label"])
    assert np.isfinite(label).all()
    assert len(np.unique(label)) >= 2
