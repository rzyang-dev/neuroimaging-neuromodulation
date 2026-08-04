from __future__ import annotations

import shutil
import subprocess

import pytest


@pytest.mark.skipif(shutil.which("antsRegistration") is None, reason="ANTs antsRegistration not installed")
def test_ants_registration_binary_execution() -> None:
    result = subprocess.run(
        ["antsRegistration", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0


@pytest.mark.skipif(shutil.which("antsApplyTransforms") is None, reason="ANTs antsApplyTransforms not installed")
def test_ants_apply_transform_binary_execution() -> None:
    result = subprocess.run(
        ["antsApplyTransforms", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
