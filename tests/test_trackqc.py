from __future__ import annotations

import json

import numpy as np

from neuroimaging_neuromodulation.wm.trackqc import tract_qc_report
from neuroimaging_neuromodulation.diffusion.render import render_streamlines_3d_html


def test_tract_qc_report(tmp_path) -> None:
    rng = np.random.default_rng(2)
    profile = np.vstack(
        [
            1.0 + 0.1 * rng.normal(size=(3, 20)),
            2.0 + 0.1 * rng.normal(size=(3, 20)),
        ]
    )
    profile_path = tmp_path / "profile.npy"
    np.save(profile_path, profile)
    segmentation_path = tmp_path / "segmentation.json"
    segmentation_path.write_text(
        json.dumps({"counts": {"1": 4, "0": 1}}),
        encoding="utf-8",
    )
    report = tract_qc_report(
        [profile_path],
        tmp_path / "qc",
        n_group1=3,
        labels=["Corticospinal"],
        segmentation_json=segmentation_path,
    )
    content = report.read_text(encoding="utf-8")
    assert "Tract QC report" in content
    assert "Corticospinal" in content
    assert "Tract segmentation counts" in content


def test_tract_qc_report_embeds_3d_viewer(tmp_path) -> None:
    profile = np.vstack(
        [
            1.0 + 0.1 * np.random.default_rng(1).normal(size=(3, 20)),
            2.0 + 0.1 * np.random.default_rng(1).normal(size=(3, 20)),
        ]
    )
    profile_path = tmp_path / "profile.npy"
    np.save(profile_path, profile)
    render_path = render_streamlines_3d_html(
        [np.array([[0.0, 0.0, 0.0], [5.0, 2.0, 3.0]])],
        [1],
        tmp_path / "tract_3d.html",
    )
    report = tract_qc_report(
        [profile_path],
        tmp_path / "qc",
        n_group1=3,
        labels=["Corticospinal"],
        render_html=render_path,
    )
    content = report.read_text(encoding="utf-8")
    assert "Interactive 3D fiber viewer" in content
    assert (tmp_path / "qc" / "tract_3d.html").exists()


def test_tract_qc_report_warns_on_empty_tract(tmp_path) -> None:
    profile = np.vstack(
        [
            1.0 + 0.1 * np.random.default_rng(3).normal(size=(3, 20)),
            2.0 + 0.1 * np.random.default_rng(3).normal(size=(3, 20)),
        ]
    )
    profile_path = tmp_path / "profile.npy"
    np.save(profile_path, profile)
    segmentation_path = tmp_path / "segmentation.json"
    segmentation_path.write_text(
        json.dumps({"counts": {"1": 0, "2": 5}}),
        encoding="utf-8",
    )
    report = tract_qc_report(
        [profile_path],
        tmp_path / "qc",
        n_group1=3,
        segmentation_json=segmentation_path,
    )
    content = report.read_text(encoding="utf-8")
    assert "QC warnings" in content
    assert "has zero streamlines" in content
