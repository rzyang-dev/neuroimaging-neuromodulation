from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from neuroimaging_neuromodulation.io.nifti import load_volume, save_volume
from neuroimaging_neuromodulation.wm.connectivity import (
    fc_asymmetry_index,
    fc_pattern_correlations,
    functional_homotopic_connectivity,
)


def _small_real_fmri_and_mask(
    real_fmri_path: Path | None,
    tmp_path: Path,
) -> tuple[Path, Path, Path]:
    if real_fmri_path is None:
        pytest.skip("real fMRI data not available")
    img, data = load_volume(real_fmri_path)
    subset = np.asarray(data[..., :10], dtype=np.float32)
    functional = tmp_path / "subset.nii"
    save_volume(subset, img, functional)

    mask = np.zeros(subset.shape[:3], dtype=np.uint8)
    left_x = 8
    right_x = subset.shape[0] - left_x - 3
    mask[left_x : left_x + 3, 30:33, 30:33] = 1
    mask[right_x : right_x + 3, 30:33, 30:33] = 1
    mask_path = tmp_path / "mask.nii"
    save_volume(mask, img, mask_path)
    return functional, mask_path, img


def test_functional_homotopic_connectivity(
    real_fmri_path: Path | None,
    tmp_path: Path,
) -> None:
    functional, mask, reference = _small_real_fmri_and_mask(real_fmri_path, tmp_path)
    output = tmp_path / "conn-homo.nii"
    _map, summary = functional_homotopic_connectivity(functional, mask, output)
    assert output.exists()
    assert summary["pairs"] > 0
    assert _map.shape == reference.shape[:3]


def test_fc_asymmetry_index(
    real_fmri_path: Path | None,
    tmp_path: Path,
) -> None:
    functional, mask, reference = _small_real_fmri_and_mask(real_fmri_path, tmp_path)
    output = tmp_path / "fc-asym.nii"
    _map, summary = fc_asymmetry_index(
        functional,
        mask,
        output,
        r_threshold=0.1,
        chunk_size=100,
    )
    assert output.exists()
    assert summary["left_voxels"] > 0
    assert summary["right_voxels"] > 0
    assert _map.shape == reference.shape[:3]


def test_fc_pattern_correlations(
    real_fmri_path: Path | None,
    tmp_path: Path,
) -> None:
    if real_fmri_path is None:
        pytest.skip("real fMRI data not available")
    img, data = load_volume(real_fmri_path)
    map_a = tmp_path / "map-a.nii"
    map_b = tmp_path / "map-b.nii"
    save_volume(np.asarray(data[..., :5].mean(axis=3), dtype=np.float32), img, map_a)
    save_volume(np.asarray(data[..., 5:10].mean(axis=3), dtype=np.float32), img, map_b)
    result_json = tmp_path / "pattern.json"
    result = fc_pattern_correlations(
        [map_a, map_b],
        [1.0, 2.0],
        output_json=result_json,
    )
    assert result_json.exists()
    loaded = json.loads(result_json.read_text(encoding="utf-8"))
    assert len(loaded["correlations"]) == 2
    assert result["image_count"] == 2
