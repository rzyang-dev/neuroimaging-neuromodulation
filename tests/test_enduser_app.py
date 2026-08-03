from __future__ import annotations

from pathlib import Path

from neuroimaging_neuromodulation.gui.enduser import build_config


def test_build_config_nifti(tmp_path: Path) -> None:
    config = build_config(
        subject="test",
        output_dir=tmp_path,
        functional=tmp_path / "func.nii",
        seed=tmp_path / "seed.nii",
        mask=tmp_path / "mask.nii",
        t1=tmp_path / "t1.nii",
        input_type="nifti",
        tr=2.0,
    )
    assert config["functional"] == str(tmp_path / "func.nii")
    assert config["t1"] == str(tmp_path / "t1.nii")


def test_build_config_dicom(tmp_path: Path) -> None:
    config = build_config(
        subject="test",
        output_dir=tmp_path,
        functional=tmp_path / "dicom",
        seed=tmp_path / "seed.nii",
        mask=tmp_path / "mask.nii",
        input_type="dicom",
        tr=2.0,
    )
    assert config["dicom"]["functional"] == str(tmp_path / "dicom")
