from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from neuroimaging_neuromodulation.io.nifti import count_timepoints, load_volume, save_volume
from neuroimaging_neuromodulation.wm.multirun import merge_runs
from neuroimaging_neuromodulation.wm.subjects import compare_subject_names


def test_merge_runs(
    real_fmri_path: Path | None,
    tmp_path: Path,
) -> None:
    if real_fmri_path is None:
        pytest.skip("real fMRI data not available")
    img, data = load_volume(real_fmri_path)
    run_a = tmp_path / "run-a.nii"
    run_b = tmp_path / "run-b.nii"
    save_volume(np.asarray(data[..., :5], dtype=np.float32), img, run_a)
    save_volume(np.asarray(data[..., 5:10], dtype=np.float32), img, run_b)

    added = merge_runs([run_a, run_b], tmp_path / "added.nii", mode="add")
    mean = merge_runs([run_a, run_b], tmp_path / "mean.nii", mode="mean")
    assert count_timepoints(added) == 10
    assert count_timepoints(mean) == 5


def test_compare_subject_names(tmp_path: Path) -> None:
    t1 = tmp_path / "t1"
    functional = tmp_path / "fun"
    for directory in (t1, functional):
        directory.mkdir()
        (directory / "sub-01").mkdir()
        (directory / "sub-02").mkdir()
    output_json = tmp_path / "subjects.json"
    result = compare_subject_names(t1, functional, output_json)
    assert result["matched"] is True
    assert result["matched_subject_count"] == 2
    assert json.loads(output_json.read_text(encoding="utf-8"))["matched"] is True

    (functional / "sub-03").mkdir()
    mismatch = compare_subject_names(t1, functional)
    assert mismatch["matched"] is False
    assert mismatch["functional_only"] == ["sub-03"]
