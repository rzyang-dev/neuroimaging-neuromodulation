from __future__ import annotations

from neuroimaging_neuromodulation.reporting.viewer import render_viewer_report


def test_render_viewer_report(package_data_dir, tmp_path) -> None:
    reference = package_data_dir / "grey333.nii"
    output = render_viewer_report(
        reference,
        tmp_path / "viewer.html",
        target_image=reference,
        slices=3,
        max_dim=20,
    )
    content = output.read_text(encoding="utf-8")
    assert "<svg" in content
    assert "Image viewer QC" in content
