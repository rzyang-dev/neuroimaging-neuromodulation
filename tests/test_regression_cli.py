from __future__ import annotations

from pathlib import Path

import nibabel as nib
import numpy as np
import pytest

from neuroimaging_neuromodulation.cli.preprocess import main
from neuroimaging_neuromodulation.targets.roi import sphere_roi


def test_friston24_cli(tmp_path: Path) -> None:
    rp = tmp_path / "rp.txt"
    np.savetxt(rp, np.zeros((4, 6)))
    output = tmp_path / "f24.txt"
    assert main(["friston24", "--rp", str(rp), "--output", str(output)]) == 0
    expanded = np.loadtxt(output)
    assert expanded.shape == (4, 24)


def test_regress_cli(tmp_path: Path) -> None:
    x = np.column_stack([np.ones(20), np.arange(20)])
    y = x @ np.array([1.0, 2.0]) + 0.1
    x_path = tmp_path / "x.txt"
    y_path = tmp_path / "y.txt"
    np.savetxt(x_path, x)
    np.savetxt(y_path, y)
    beta_path = tmp_path / "beta.txt"
    residual_path = tmp_path / "residual.txt"
    assert main(["regress", "--y", str(y_path), "--x", str(x_path), "--beta-output", str(beta_path), "--residual-output", str(residual_path)]) == 0
    assert np.loadtxt(beta_path).shape == (2,)
    assert np.loadtxt(residual_path).shape == (20,)


def test_extract_signal_cli(real_fmri_path: Path | None, real_fmri_available: bool, tmp_path: Path) -> None:
    if not real_fmri_available:
        pytest.skip("real fMRI data not available")
    img = nib.load(real_fmri_path)
    five_vol = nib.Nifti1Image(img.dataobj[..., :5], img.affine)
    five_vol.to_filename(tmp_path / "five.nii")
    _, _ = sphere_roi([0.0, 0.0, 0.0], 10.0, img, tmp_path / "mask.nii")
    output = tmp_path / "signal.txt"
    assert main(["extract-signal", "--functional", str(tmp_path / "five.nii"), "--mask", str(tmp_path / "mask.nii"), "--output", str(output)]) == 0
    signal = np.loadtxt(output)
    assert signal.shape == (5,)


def test_regress_covariates_cli(real_fmri_path: Path | None, real_fmri_available: bool, tmp_path: Path) -> None:
    if not real_fmri_available:
        pytest.skip("real fMRI data not available")
    img = nib.load(real_fmri_path)
    five_vol = nib.Nifti1Image(img.dataobj[..., :5], img.affine)
    five_vol.to_filename(tmp_path / "five.nii")
    _, _ = sphere_roi([0.0, 0.0, 0.0], 10.0, img, tmp_path / "mask.nii")
    output = tmp_path / "regressed.nii"
    assert main(
        [
            "regress-covariates",
            "--functional",
            str(tmp_path / "five.nii"),
            "--wm-mask",
            str(tmp_path / "mask.nii"),
            "--output",
            str(output),
        ]
    ) == 0
    assert output.exists()
