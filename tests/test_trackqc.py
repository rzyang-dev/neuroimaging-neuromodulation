from __future__ import annotations

import json

import numpy as np

from neuroimaging_neuromodulation.wm.trackqc import tract_qc_report


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
