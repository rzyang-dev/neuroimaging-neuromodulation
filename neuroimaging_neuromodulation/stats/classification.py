"""Leave-one-out group classification from FC pattern matrices."""

from __future__ import annotations

import numpy as np
from scipy import stats


def _pearson_r(x: np.ndarray, y: np.ndarray) -> float:
    if np.std(x) == 0 or np.std(y) == 0:
        return 0.0
    return float(np.corrcoef(x, y)[0, 1])


def auc_binary(scores: np.ndarray, labels: np.ndarray) -> float:
    """Compute the Mann-Whitney AUC for positive vs negative class scores."""

    scores = np.asarray(scores, dtype=float)
    labels = np.asarray(labels, dtype=bool)
    n_pos = int(labels.sum())
    n_neg = int((~labels).sum())
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    ranks = stats.rankdata(scores)
    rank_sum = float(ranks[labels].sum())
    auc = (rank_sum - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)
    return float(auc)


def leave_one_out_gfc_classification(
    ccmatrix: np.ndarray,
    n_group1: int,
) -> dict[str, object]:
    """Run the original TMSGFCClass leave-one-out classifier.

    ``ccmatrix`` has shape ``(n_features, n_subjects)`` and the first
    ``n_group1`` subjects belong to group 1. For each left-out subject, the
    mean feature vectors of the two training groups are correlated with the
    left-out subject; the score is ``r_group1 - r_group2``.
    """

    matrix = np.asarray(ccmatrix, dtype=float)
    if matrix.ndim != 2:
        raise ValueError("ccmatrix must be 2D")
    n_subjects = matrix.shape[1]
    if not 0 < n_group1 < n_subjects:
        raise ValueError("n_group1 must be between 1 and n_subjects - 1")
    scores = np.zeros(n_subjects)
    for leftout in range(n_subjects):
        train = np.delete(matrix, leftout, axis=1)
        seed = matrix[:, leftout]
        if leftout < n_group1:
            group1 = train[:, : n_group1 - 1]
            group2 = train[:, n_group1 - 1 :]
        else:
            group1 = train[:, :n_group1]
            group2 = train[:, n_group1 :]
        mean1 = np.mean(group1, axis=1)
        mean2 = np.mean(group2, axis=1)
        r1 = _pearson_r(mean1, seed)
        r2 = _pearson_r(mean2, seed)
        scores[leftout] = r1 - r2
    labels = np.arange(n_subjects) < n_group1
    sensitivity = float(np.mean(scores[labels] > 0))
    specificity = float(np.mean(scores[~labels] < 0))
    accuracy = float((np.sum(scores[labels] > 0) + np.sum(scores[~labels] < 0)) / n_subjects)
    return {
        "scores": scores,
        "sensitivity": sensitivity,
        "specificity": specificity,
        "accuracy": accuracy,
        "auc": auc_binary(scores, labels),
    }


__all__ = ["auc_binary", "leave_one_out_gfc_classification"]
