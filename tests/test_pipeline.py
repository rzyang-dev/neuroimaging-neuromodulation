from __future__ import annotations

from pathlib import Path

import nibabel as nib
import pytest

from neuroimaging_neuromodulation.pipeline.run import run_pipeline
from neuroimaging_neuromodulation.targets.roi import sphere_roi


def test_pipeline_real_fmri_subset(real_fmri_path: Path | None, real_fmri_available: bool, tmp_path: Path) -> None:
    if not real_fmri_available:
        pytest.skip("real fMRI data not available")
    img = nib.load(real_fmri_path)
    five_vol = nib.Nifti1Image(img.dataobj[..., :5], img.affine)
    five_vol.to_filename(tmp_path / "fivevol.nii")
    _, _ = sphere_roi([0.0, 0.0, 0.0], 8.0, img, tmp_path / "seed.nii")
    _, _ = sphere_roi([0.0, 0.0, 0.0], 18.0, img, tmp_path / "mask.nii")
    _, _ = sphere_roi([0.0, 0.0, 0.0], 10.0, img, tmp_path / "wm.nii")
    _, _ = sphere_roi([0.0, 0.0, 0.0], 10.0, img, tmp_path / "csf.nii")
    config = {
        "subject": "pipe-test",
        "output_dir": str(tmp_path / "out"),
        "functional": str(tmp_path / "fivevol.nii"),
        "seed": str(tmp_path / "seed.nii"),
        "mask": str(tmp_path / "mask.nii"),
        "tr": 2.0,
        "estimate_motion": True,
        "motion": {"level_iters": [3, 2, 1], "maxiter": 5},
        "regress_covariates": True,
        "nuisance": {
            "wm_mask": str(tmp_path / "wm.nii"),
            "csf_mask": str(tmp_path / "csf.nii"),
            "global_mask": str(tmp_path / "mask.nii"),
        },
        "target": {"p_value": 0.05, "n_samples": 5},
        "report": True,
    }
    result = run_pipeline(config)
    assert (tmp_path / "out" / "pipe-test" / "motion_corrected.nii").exists()
    assert (tmp_path / "out" / "pipe-test" / "rp.txt").exists()
    assert (tmp_path / "out" / "pipe-test" / "regressed.nii").exists()
    assert (tmp_path / "out" / "pipe-test" / "SeedFCinROI.nii").exists()
    assert (tmp_path / "out" / "pipe-test" / "report.html").exists()
    assert result["report"] is not None
