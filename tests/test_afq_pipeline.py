from __future__ import annotations

import nibabel as nib
import numpy as np

from neuroimaging_neuromodulation.diffusion.afq import afq_subject_pipeline
from neuroimaging_neuromodulation.diffusion import roi_segmentation


def test_afq_subject_pipeline() -> None:
    atlas = np.zeros((20, 20, 20), dtype=np.uint8)
    atlas[5:15, 5:15, 5:10] = 1
    atlas[5:15, 5:15, 12:17] = 2
    atlas_img = nib.Nifti1Image(atlas, np.eye(4))
    scalar = np.broadcast_to(np.arange(20, dtype=float).reshape(20, 1, 1), (20, 20, 20)).copy()
    scalar_img = nib.Nifti1Image(scalar, np.eye(4))
    rng = np.random.default_rng(4)
    x = np.linspace(5.0, 15.0, 8)
    streamlines = []
    for z, label in [(7, 1), (14, 2)]:
        for _ in range(25):
            y = 10.0 + rng.normal(scale=0.1, size=8)
            zz = z + rng.normal(scale=0.1, size=8)
            streamlines.append(np.column_stack([x, y, zz]))
    result = afq_subject_pipeline(
        streamlines,
        atlas_img,
        scalar_img,
        n_samples=8,
        num_nodes=5,
        max_dist=4.0,
        max_len=4.0,
    )
    assert len(result["tracts"]) == 2
    for tract in result["tracts"]:
        assert tract["output_streamlines"] > 0
        assert np.asarray(tract["profile"]).shape == (5,)


def test_afq_subject_pipeline_roi_method(monkeypatch, tmp_path) -> None:
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
    tract_atlas = np.zeros((20, 20, 20, 1), dtype=np.float32)
    tract_atlas[5:15, 5:15, 5:15, 0] = 1.0
    nib.Nifti1Image(tract_atlas, affine).to_filename(tmp_path / "tract_atlas.nii.gz")
    scalar = np.broadcast_to(np.arange(20, dtype=float).reshape(20, 1, 1), (20, 20, 20)).copy()
    scalar_img = nib.Nifti1Image(scalar, affine)
    streamline = np.array([[6.0, 6.0, 6.0], [8.0, 8.0, 8.0], [10.0, 10.0, 13.0]])
    result = afq_subject_pipeline(
        [streamline],
        scalar_img,
        scalar_img,
        n_samples=8,
        num_nodes=5,
        max_dist=4.0,
        max_len=4.0,
        segmentation="roi",
        roi_dir=tmp_path,
        tract_atlas=tmp_path / "tract_atlas.nii.gz",
        min_dist=1.0,
    )
    assert len(result["tracts"]) == 1
    assert result["tracts"][0]["output_streamlines"] == 1
