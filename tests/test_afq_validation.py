from __future__ import annotations

import json

import numpy as np

from neuroimaging_neuromodulation.wm.reference import compare_afq_profiles


def test_compare_afq_profiles(tmp_path) -> None:
    reference = {
        "tracts": [
            {
                "label": 1,
                "profile": [1.0, 2.0, 3.0, 4.0, 5.0],
                "std": [0.1] * 5,
            }
        ]
    }
    candidate = {
        "tracts": [
            {
                "label": 1,
                "profile": [1.1, 2.1, 3.1, 4.1, 5.1],
                "std": [0.1] * 5,
            }
        ]
    }
    reference_path = tmp_path / "reference.json"
    candidate_path = tmp_path / "candidate.json"
    reference_path.write_text(json.dumps(reference), encoding="utf-8")
    candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
    result = compare_afq_profiles(reference_path, candidate_path)
    assert result["matched_tracts"] == 1
    assert result["tracts"][0]["correlation"] > 0.99
    assert np.isclose(result["tracts"][0]["mae"], 0.1)
    assert np.isclose(result["mean_mae"], 0.1)
