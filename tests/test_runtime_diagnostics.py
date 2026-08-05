from __future__ import annotations

import json
from pathlib import Path

from neuroimaging_neuromodulation.cli.main import main as toolbox_main
from neuroimaging_neuromodulation.runtime.diagnostics import (
    check_system,
    discover_optional_providers,
    render_doctor_report,
)


def test_check_system_reports_core_and_data(package_data_dir: Path) -> None:
    report = check_system()
    assert report["package"]["version"] == "0.20.0"
    assert all(item["installed"] for item in report["core_dependencies"])
    assert report["data"]["present"] is True
    assert any(name.endswith(".nii") or name.endswith(".nii.gz") for name in report["data"]["bundled_nifti_files"])


def test_discover_optional_providers_uses_env(
    monkeypatch,
    tmp_path: Path,
) -> None:
    bin_dir = tmp_path / "ants-bin"
    bin_dir.mkdir()
    (bin_dir / "antsRegistration").write_text("", encoding="utf-8")
    monkeypatch.setenv("NM_ANTS_DIR", str(bin_dir))
    providers = discover_optional_providers()
    ants = next(item for item in providers if item["name"] == "ants")
    assert ants["available"] is True
    assert str(bin_dir / "antsRegistration") in ants["detail"]


def test_doctor_cli_json(capsys) -> None:
    exit_code = toolbox_main(["doctor", "--json"])
    captured = capsys.readouterr()
    assert exit_code == 0
    report = json.loads(captured.out)
    assert report["package"]["name"] == "neuroimaging-neuromodulation"


def test_doctor_report_text() -> None:
    text = render_doctor_report(check_system())
    assert "nm-toolbox doctor" in text
    assert "version: 0.20.0" in text
