from __future__ import annotations

from pathlib import Path

from neuroimaging_neuromodulation.cli.preprocess import main as preprocess_main
from neuroimaging_neuromodulation.preprocess.ants import (
    build_ants_apply_transform_command,
    build_ants_registration_command,
)


def test_ants_command_builders(tmp_path: Path) -> None:
    registration = build_ants_registration_command(
        tmp_path / "moving.nii",
        tmp_path / "fixed.nii",
        tmp_path / "warp",
    )
    assert registration[0] == "antsRegistration"
    assert "--transform" in registration
    apply_transform = build_ants_apply_transform_command(
        tmp_path / "input.nii",
        tmp_path / "reference.nii",
        tmp_path / "output.nii",
        [tmp_path / "warp1Warp.nii.gz"],
    )
    assert apply_transform[0] == "antsApplyTransforms"
    assert "-t" in apply_transform


def test_ants_cli_dry_run(tmp_path: Path) -> None:
    assert (
        preprocess_main(
            [
                "ants-register",
                "--moving",
                str(tmp_path / "moving.nii"),
                "--fixed",
                str(tmp_path / "fixed.nii"),
                "--output-prefix",
                str(tmp_path / "warp"),
                "--dry-run",
            ]
        )
        == 0
    )
