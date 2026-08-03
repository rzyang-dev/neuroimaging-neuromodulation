"""Thresholding and largest-cluster target extraction."""

from __future__ import annotations

import numpy as np
from scipy import ndimage

from ..coordinates import mat_to_mni
from ..stats.functional import inverse_pearson


def threshold_map(
    data: np.ndarray,
    p_value: float,
    n_samples: int,
    direction: str = "Positive",
) -> np.ndarray:
    """Threshold a correlation map by the inverse Pearson p-value."""

    data = np.asarray(data, dtype=float).copy()
    data[~np.isfinite(data)] = 0.0
    threshold = inverse_pearson(p_value, n_samples)
    if direction.lower().startswith("pos"):
        data[data < threshold] = 0.0
    elif direction.lower().startswith("neg"):
        data = -data
        data[data < threshold] = 0.0
    else:
        raise ValueError("direction must be 'Positive' or 'Negative'")
    return data


def largest_cluster(
    data: np.ndarray,
    p_value: float,
    n_samples: int,
    direction: str = "Positive",
) -> tuple[np.ndarray, int]:
    """Return the largest 26-connected supra-threshold cluster as a binary mask."""

    thresholded = threshold_map(data, p_value, n_samples, direction)
    thresholded = (thresholded > 0).astype(np.uint8)
    labels, n_labels = ndimage.label(thresholded, structure=np.ones((3, 3, 3)))
    if n_labels == 0:
        return np.zeros_like(thresholded, dtype=bool), 0
    sizes = ndimage.sum_labels(labels, labels, index=np.arange(1, n_labels + 1))
    largest = int(np.argmax(sizes) + 1)
    return labels == largest, int(sizes[largest - 1])


def label_centers_mni(
    data: np.ndarray,
    affine: np.ndarray,
) -> list[dict[str, object]]:
    """Return MNI centers for each integer-valued connected region."""

    data = np.asarray(data, dtype=float)
    centers: list[dict[str, object]] = []
    for value in np.unique(data[data > 0]):
        binary = (data == value).astype(np.uint8)
        labels, n_labels = ndimage.label(binary, structure=np.ones((3, 3, 3)))
        if n_labels == 0:
            continue
        for label in range(1, n_labels + 1):
            mask = labels == label
            centroid = ndimage.center_of_mass(mask, labels, label)
            mat = np.array(centroid) + 1.0
            centers.append(
                {
                    "value": float(value),
                    "size": int(mask.sum()),
                    "mni": mat_to_mni(mat, affine),
                    "matrix_1based": mat,
                }
            )
    return centers


__all__ = ["label_centers_mni", "largest_cluster", "threshold_map"]
