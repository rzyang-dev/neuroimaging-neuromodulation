from __future__ import annotations

from pathlib import Path

import pytest

from neuroimaging_neuromodulation.gui.app import ToolboxApp
from neuroimaging_neuromodulation.gui.enduser import build_config
from neuroimaging_neuromodulation.gui.enduser import EndUserApp


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


def test_build_config_t1_target(tmp_path: Path) -> None:
    config = build_config(
        subject="test",
        output_dir=tmp_path,
        functional=tmp_path / "func.nii",
        seed=tmp_path / "seed.nii",
        mask=tmp_path / "mask.nii",
        t1=tmp_path / "t1.nii",
        target_image=tmp_path / "target.nii",
        generate_t1_target=True,
        input_type="nifti",
        tr=2.0,
    )
    assert config["t1_target"]["target"] == str(tmp_path / "target.nii")
    assert config["t1_target"]["deformation"] is None
    assert config["t1_target"]["output"].endswith("IndiTarget_T1Sp.nii")


def test_enduser_app_smoke() -> None:
    try:
        app = EndUserApp()
    except Exception as exc:  # pragma: no cover - depends on local display
        pytest.skip(f"Tkinter display is not available: {exc}")
    try:
        app.withdraw()
        app.update_idletasks()
    finally:
        app.destroy()


def test_advanced_gui_smoke() -> None:
    try:
        app = ToolboxApp()
    except Exception as exc:  # pragma: no cover - depends on local display
        pytest.skip(f"Tkinter display is not available: {exc}")
    try:
        app.withdraw()
        app.update_idletasks()
    finally:
        app.destroy()
