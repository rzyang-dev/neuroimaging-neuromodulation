"""Reference comparison utilities for AFQ-style outputs."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np


def _load_afq_result(path: str | Path) -> dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def compare_afq_profiles(
    reference_path: str | Path,
    candidate_path: str | Path,
) -> dict[str, object]:
    """Compare AFQ tract profiles by label and return per-tract metrics."""

    reference = _load_afq_result(reference_path)
    candidate = _load_afq_result(candidate_path)
    reference_tracts = {
        int(item["label"]): item for item in reference.get("tracts", [])
    }
    tract_results: list[dict[str, object]] = []
    for candidate_tract in candidate.get("tracts", []):
        label = int(candidate_tract["label"])
        reference_tract = reference_tracts.get(label)
        if reference_tract is None:
            tract_results.append(
                {
                    "label": label,
                    "matched": False,
                    "correlation": None,
                    "mae": None,
                }
            )
            continue
        reference_profile = np.asarray(reference_tract["profile"], dtype=float)
        candidate_profile = np.asarray(candidate_tract["profile"], dtype=float)
        if (
            reference_profile.shape != candidate_profile.shape
            or reference_profile.std() < 1e-12
            or candidate_profile.std() < 1e-12
        ):
            tract_results.append(
                {
                    "label": label,
                    "matched": True,
                    "correlation": None,
                    "mae": float(np.mean(np.abs(reference_profile - candidate_profile))),
                }
            )
            continue
        correlation = float(np.corrcoef(reference_profile, candidate_profile)[0, 1])
        tract_results.append(
            {
                "label": label,
                "matched": True,
                "correlation": correlation,
                "mae": float(np.mean(np.abs(reference_profile - candidate_profile))),
            }
        )
    correlations = [
        float(item["correlation"])
        for item in tract_results
        if item["correlation"] is not None
    ]
    mae_values = [float(item["mae"]) for item in tract_results if item["mae"] is not None]
    return {
        "reference": str(reference_path),
        "candidate": str(candidate_path),
        "tracts": tract_results,
        "matched_tracts": sum(1 for item in tract_results if item["matched"]),
        "mean_correlation": float(np.mean(correlations)) if correlations else None,
        "mean_mae": float(np.mean(mae_values)) if mae_values else None,
    }


__all__ = ["compare_afq_profiles"]
