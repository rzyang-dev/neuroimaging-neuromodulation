from __future__ import annotations

from pathlib import Path

import pytest

from neuroimaging_neuromodulation.cli.diffusion import main as diffusion_main
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
        seed_image=tmp_path / "seed.nii",
    )
    assert cmd[0] == "tckgen"
    assert "-seed_image" in cmd
    assert cmd[cmd.index("-seed_image") + 1] == str(tmp_path / "seed.nii")
    assert cmd[-1] == str(tmp_path / "tracks.tck")
    legacy = external.build_mrtrix_tckgen_command(
        tmp_path / "dwi.nii",
        tmp_path / "mask.nii",
        tmp_path / "tracks.tck",
    )
    assert "-seed_image" not in legacy
    assert (
        diffusion_main(
            [
                "mrtrix-tckgen",
                "--dwi",
                str(tmp_path / "dwi.nii"),
                "--mask",
                str(tmp_path / "mask.nii"),
                "--seed-image",
                str(tmp_path / "seed.nii"),
                "--output",
                str(tmp_path / "tracks.tck"),
                "--num-tracks",
                "10",
                "--dry-run",
            ]
        )
        == 0
    )


def test_fsl_bet_and_eddy_command_builders(tmp_path: Path) -> None:
    bet = external.build_fsl_bet_command(tmp_path / "data.nii", tmp_path / "dataB.nii")
    assert bet[:3] == ["bet", str(tmp_path / "data.nii"), str(tmp_path / "dataB.nii")]
    assert "-m" in bet
    eddy = external.build_fsl_eddy_correct_command(
        tmp_path / "dataB.nii",
        tmp_path / "dataBC.nii.gz",
        reference_volume=0,
    )
    assert eddy[-1] == "0"


def test_fsl_transform_command_builders(tmp_path: Path) -> None:
    flirt = external.build_fsl_flirt_command(
        tmp_path / "FA.nii",
        tmp_path / "dataB.nii",
        tmp_path / "FAinT1.nii",
        out_matrix=tmp_path / "FA2T1.mat",
    )
    assert "-omat" in flirt
    inv = external.build_fsl_convert_xfm_command(
        tmp_path / "FA2T1.mat",
        tmp_path / "T12FA.mat",
        inverse=True,
    )
    assert inv[1] == "-inverse"
    applywarp = external.build_fsl_applywarp_command(
        tmp_path / "SeedImage.nii",
        tmp_path / "dataB.nii",
        tmp_path / "SeedImage_T1Sp.nii",
        tmp_path / "MNI2T1transf.nii.gz",
    )
    assert applywarp[1] == "--ref"
    topup = external.build_fsl_topup_command(
        tmp_path / "data_appa_b0.nii",
        tmp_path / "para.txt",
        tmp_path / "b02b0.cnf",
        tmp_path / "Topup_Output",
    )
    assert topup[0] == "topup"


def test_fsl_randomise_command_builders(tmp_path: Path) -> None:
    design = external.build_fsl_design_ttest2_command(tmp_path / "design", 3, 4)
    assert design == ["design_ttest2", str(tmp_path / "design"), "3", "4"]
    randomise = external.build_fsl_randomise_command(
        tmp_path / "merged4d.nii.gz",
        tmp_path / "diff",
        tmp_path / "mask.nii.gz",
        tmp_path / "design.mat",
        tmp_path / "design.con",
        n_permutations=100,
    )
    assert randomise[0] == "randomise"
    assert "-T" in randomise
    assert "-n" in randomise


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


def test_new_fsl_cli_dry_run(tmp_path: Path) -> None:
    assert (
        diffusion_main(
            [
                "fsl-fa2t1",
                "--fa",
                str(tmp_path / "FA.nii"),
                "--ref",
                str(tmp_path / "dataB.nii"),
                "--output",
                str(tmp_path / "FAinT1.nii"),
                "--matrix",
                str(tmp_path / "FA2T1.mat"),
                "--inverse-matrix",
                str(tmp_path / "T12FA.mat"),
                "--dry-run",
            ]
        )
        == 0
    )
