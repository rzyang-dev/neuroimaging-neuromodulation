from __future__ import annotations

import numpy as np

from neuroimaging_neuromodulation.stats.classification import (
    auc_binary,
    leave_one_out_gfc_classification,
)


def test_leave_one_out_classification_separates_groups() -> None:
    rng = np.random.default_rng(9)
    pattern = np.linspace(-1, 1, 20)
    group1 = np.column_stack([pattern + 0.4 * rng.normal(size=20) for _ in range(3)])
    group2 = np.column_stack([-pattern + 0.4 * rng.normal(size=20) for _ in range(3)])
    matrix = np.column_stack([group1, group2])
    result = leave_one_out_gfc_classification(matrix, n_group1=3)
    assert result["sensitivity"] == 1.0
    assert result["specificity"] == 1.0
    assert result["accuracy"] == 1.0
    assert result["auc"] == 1.0


def test_auc_binary() -> None:
    scores = np.array([2.0, 1.0, -1.0, -2.0])
    labels = np.array([True, True, False, False])
    assert auc_binary(scores, labels) == 1.0
