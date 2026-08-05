from __future__ import annotations

import json
from pathlib import Path

import nibabel as nib
import numpy as np
import pytest

from neuroimaging_neuromodulation.pipeline.run import run_pipeline, validate_pipeline_config
from neuroimaging_neuromodulation.targets.roi import sphere_roi


def test_pipeline_real_fmri_subset(
    real_fmri_path: Path | None,
    real_fmri_available: bool,
    tmp_path: Path,
    package_data_dir: Path,
) -> None:
    if not real_fmri_available:
        pytest.skip("real fMRI data not available")
    img = nib.load(real_fmri_path)
    five_vol = nib.Nifti1Image(img.dataobj[..., :5], img.affine)
    five_vol.to_filename(tmp_path / "fivevol.nii")
    _, _ = sphere_roi([0.0, 0.0, 0.0], 8.0, img, tmp_path / "seed.nii")
    _, _ = sphere_roi([0.0, 0.0, 0.0], 18.0, img, tmp_path / "mask.nii")
    _, _ = sphere_roi([0.0, 0.0, 0.0], 10.0, img, tmp_path / "wm.nii")
    _, _ = sphere_roi([0.0, 0.0, 0.0], 10.0, img, tmp_path / "csf.nii")
    _, _ = sphere_roi([0.0, 0.0, 0.0], 10.0, package_data_dir / "grey333.nii", tmp_path / "t1target.nii")
    from neuroimaging_neuromodulation.io.deformations import identity_deformation

    _, _ = identity_deformation(package_data_dir / "grey333.nii", tmp_path / "identity_t1.nii")
    config = {
        "subject": "pipe-test",
        "output_dir": str(tmp_path / "out"),
        "functional": str(tmp_path / "fivevol.nii"),
        "seed": str(tmp_path / "seed.nii"),
        "mask": str(tmp_path / "mask.nii"),
        "t1": str(package_data_dir / "grey333.nii"),
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
        "t1_target": {
            "target": str(tmp_path / "t1target.nii"),
            "deformation": str(tmp_path / "identity_t1.nii"),
            "output": str(tmp_path / "out" / "pipe-test" / "IndiTarget_T1Sp.nii"),
        },
        "report": True,
    }
    result = run_pipeline(config)
    assert (tmp_path / "out" / "pipe-test" / "motion_corrected.nii").exists()
    assert (tmp_path / "out" / "pipe-test" / "rp.txt").exists()
    assert (tmp_path / "out" / "pipe-test" / "regressed.nii").exists()
    assert (tmp_path / "out" / "pipe-test" / "SeedFCinROI.nii").exists()
    assert (tmp_path / "out" / "pipe-test" / "IndiTarget_T1Sp.nii").exists()
    assert (tmp_path / "out" / "pipe-test" / "report.html").exists()
    assert result["report"] is not None
    assert result["t1_target"]["output"] is not None
    assert result["manifest"] is not None
    manifest = json.loads(Path(result["manifest"]).read_text(encoding="utf-8"))
    assert manifest["metadata"]["package_version"] == "0.20.0"


def test_validate_pipeline_config_rejects_missing_required_input(tmp_path: Path) -> None:
    functional = tmp_path / "func.nii"
    functional.write_text("not-a-real-nifti", encoding="utf-8")
    with pytest.raises(ValueError, match="seed"):
        validate_pipeline_config(
            {
                "subject": "test",
                "output_dir": str(tmp_path),
                "functional": str(functional),
                "mask": str(tmp_path / "missing-mask.nii"),
            }
        )


def test_pipeline_wm_analysis(
    real_fmri_path: Path | None,
    real_fmri_available: bool,
    tmp_path: Path,
) -> None:
    if not real_fmri_available:
        pytest.skip("real fMRI data not available")
    img = nib.load(real_fmri_path)
    subset = nib.Nifti1Image(np.asarray(img.dataobj[..., :10], dtype=np.float32), img.affine)
    functional = tmp_path / "wm-func.nii"
    subset.to_filename(functional)
    _, _ = sphere_roi([0.0, 0.0, 0.0], 8.0, img, tmp_path / "wm-seed.nii")
    mask = np.zeros(img.shape[:3], dtype=np.uint8)
    left_x = 8
    right_x = img.shape[0] - left_x - 3
    mask[left_x : left_x + 3, 30:33, 30:33] = 1
    mask[right_x : right_x + 3, 30:33, 30:33] = 1
    mask_path = tmp_path / "wm-mask.nii"
    nib.Nifti1Image(mask, img.affine).to_filename(mask_path)
    result = run_pipeline(
        {
            "subject": "wm-test",
            "output_dir": str(tmp_path / "out"),
            "functional": str(functional),
            "seed": str(tmp_path / "wm-seed.nii"),
            "mask": str(mask_path),
            "target": False,
            "report": False,
            "wm_analysis": {
                "conn_homo": {
                    "mask": str(mask_path),
                    "r_threshold": 0.1,
                },
                "fc_asym": {
                    "mask": str(mask_path),
                    "r_threshold": 0.1,
                    "chunk_size": 100,
                },
            },
        }
    )
    assert Path(result["wm_analysis"]["conn_homo"]["output"]).exists()
    assert Path(result["wm_analysis"]["fc_asym"]["output"]).exists()
