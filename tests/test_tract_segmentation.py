from __future__ import annotations

import nibabel as nib
import numpy as np

from neuroimaging_neuromodulation.diffusion.segmentation import segment_streamlines_by_atlas


def test_segment_streamlines_by_atlas() -> None:
    atlas = np.zeros((20, 20, 20), dtype=np.uint8)
    atlas[5:15, 5:15, 5:15] = 1
    atlas[5:10, 5:10, 12:18] = 2
    img = nib.Nifti1Image(atlas, np.eye(4))
    streamlines = [
        np.array([[6.0, 6.0, 6.0], [8.0, 8.0, 8.0], [10.0, 10.0, 10.0]]),
        np.array([[6.0, 6.0, 13.0], [8.0, 8.0, 15.0]]),
        np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]]),
    ]
    result = segment_streamlines_by_atlas(streamlines, img, n_samples=20)
    assert result["labels"] == [1, 2, 0]
    assert result["counts"] == {"0": 1, "1": 1, "2": 1}
