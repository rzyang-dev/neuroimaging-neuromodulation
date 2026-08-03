from __future__ import annotations

from pathlib import Path

import pytest

from neuroimaging_neuromodulation.diffusion import external


def test_fsl_probtrackx_command_builder(tmp_path: Path) -> None:
    cmd = external.build_fsl_probtrackx_command(
        tmp_path / "seed.nii",
        tmp_path / "target.nii",
        tmp_path / "bedpostx",
        tmp_path / "out",
        samples=100,
        steps=50,
    )
    assert cmd[0] == "probtrackx2"
    assert "--waypoints" in cmd
    assert "-P" in cmd


def test_mrtrix_command_builder(tmp_path: Path) -> None:
    cmd = external.build_mrtrix_tckgen_command(
        tmp_path / "dwi.nii",
        tmp_path / "mask.nii",
        tmp_path / "tracks.tck",
        algorithm="iFOD2",
        num_tracks=10,
    )
    assert cmd[0] == "tckgen"
    assert cmd[-1] == str(tmp_path / "tracks.tck")


def test_missing_binary_raises(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(external.shutil, "which", lambda _name: None)
    with pytest.raises(RuntimeError, match="not found"):
        external.run_fsl_probtrackx(
            tmp_path / "seed.nii",
            tmp_path / "target.nii",
            tmp_path / "bedpostx",
            tmp_path / "out",
        )


def test_check_external_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        external.shutil,
        "which",
        lambda name: f"/usr/bin/{name}" if name == "tckgen" else None,
    )
    result = external.check_external_tools()
    assert set(result) == {"bedpostx", "dtifit", "probtrackx2", "tckgen"}
    assert result["tckgen"]["available"] is True
    assert result["probtrackx2"]["available"] is False
