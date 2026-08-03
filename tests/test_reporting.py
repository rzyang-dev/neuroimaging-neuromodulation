from __future__ import annotations

import json
from pathlib import Path

import nibabel as nib

from neuroimaging_neuromodulation.reporting.html import render_target_report
from neuroimaging_neuromodulation.reporting.manifest import write_target_manifest
from neuroimaging_neuromodulation.targets.pipeline import seed_based_fc, target_site
from neuroimaging_neuromodulation.targets.roi import sphere_roi


def test_manifest_real_files(package_data_dir: Path, tmp_path: Path) -> None:
    source = package_data_dir / "BrainMask_05_61x73x61.nii"
    manifest = write_target_manifest(source.parent, tmp_path / "manifest.json")
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data["file_count"] > 0
    assert any(entry["sha256"] for entry in data["files"])


def test_report_real_target(real_fmri_path: Path | None, real_fmri_available: bool, tmp_path: Path) -> None:
    if not real_fmri_available:
        return
    func_img = nib.load(real_fmri_path)
    _, _ = sphere_roi([0.0, 0.0, 0.0], 8.0, func_img, tmp_path / "seed.nii")
    _, _ = sphere_roi([0.0, 0.0, 0.0], 18.0, func_img, tmp_path / "mask.nii")
    result = seed_based_fc(
        real_fmri_path,
        tmp_path / "seed.nii",
        tmp_path / "mask.nii",
        tmp_path / "fc",
        subject="report-test",
    )
    target_site(
        result["SeedFCinROI"],
        tmp_path / "targets",
        subject="report-test",
        posneg=["Positive", "Negative"],
        p_value=0.05,
        n_samples=168,
    )
    report = render_target_report(tmp_path / "targets", "report-test")
    manifest = tmp_path / "targets" / "report-test" / "manifest.json"
    assert report.exists()
    assert manifest.exists()
    content = report.read_text(encoding="utf-8")
    assert "report-test" in content
    assert "MNICoordinate" in content
