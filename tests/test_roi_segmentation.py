from __future__ import annotations

import nibabel as nib
import numpy as np

from neuroimaging_neuromodulation.diffusion import roi_segmentation


def test_segment_streamlines_by_rois(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        roi_segmentation,
        "TRACT_ROI_FILES",
        [("roi1.nii.gz", "roi2.nii.gz")],
    )
    roi1 = np.zeros((20, 20, 20), dtype=np.uint8)
    roi1[5:15, 5:15, 5:7] = 1
    roi2 = np.zeros((20, 20, 20), dtype=np.uint8)
    roi2[5:15, 5:15, 12:14] = 1
    affine = np.eye(4)
    nib.Nifti1Image(roi1, affine).to_filename(tmp_path / "roi1.nii.gz")
    nib.Nifti1Image(roi2, affine).to_filename(tmp_path / "roi2.nii.gz")

    atlas = np.zeros((20, 20, 20, 1), dtype=np.float32)
    atlas[5:15, 5:15, 5:15, 0] = 1.0
    nib.Nifti1Image(atlas, affine).to_filename(tmp_path / "atlas.nii.gz")

    good = np.array([[6.0, 6.0, 6.0], [8.0, 8.0, 8.0], [10.0, 10.0, 13.0]])
    bad = np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0], [2.0, 2.0, 2.0]])
    result = roi_segmentation.segment_streamlines_by_rois(
        [good, bad],
        tmp_path,
        atlas_image=tmp_path / "atlas.nii.gz",
        min_dist=1.0,
        n_samples=10,
    )
    assert result["labels"] == [1, 0]
