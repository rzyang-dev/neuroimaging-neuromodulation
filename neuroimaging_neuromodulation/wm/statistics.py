"""AFQ-style tract-profile group statistics."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import stats

from .plots import _load_profile_matrix


def profile_group_statistics(
    profile_files: list[str | Path],
    *,
    n_group1: int,
    labels: list[str] | None = None,
) -> dict[str, object]:
    """Run per-node two-sample t-tests on tract profile matrices."""

    if labels is None:
        labels = [f"Tract {i + 1}" for i in range(len(profile_files))]
    if len(labels) != len(profile_files):
        raise ValueError("labels must match profile_files")
    results = []
    n_group2: int | None = None
    for label, profile_file in zip(labels, profile_files):
        matrix = _load_profile_matrix(profile_file)
        if matrix.ndim == 1:
            matrix = matrix[None, :]
        if matrix.ndim != 2:
            raise ValueError(f"Profile file must be 2D or 1D: {profile_file}")
        if not 0 < n_group1 < matrix.shape[0]:
            raise ValueError("n_group1 must split the profile matrix into two groups")
        current_group2 = matrix.shape[0] - n_group1
        if n_group2 is None:
            n_group2 = current_group2
        elif n_group2 != current_group2:
            raise ValueError("All profile matrices must have the same number of rows")
        group1 = matrix[:n_group1, :]
        group2 = matrix[n_group1:, :]
        t, p = stats.ttest_ind(group1, group2, axis=0, equal_var=False)
        results.append(
            {
                "label": str(label),
                "group1_mean": group1.mean(axis=0).tolist(),
                "group2_mean": group2.mean(axis=0).tolist(),
                "t": t.tolist(),
                "p": p.tolist(),
            }
        )
    return {"n_group1": n_group1, "n_group2": n_group2, "profiles": results}


__all__ = ["profile_group_statistics"]
