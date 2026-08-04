"""Simple image utilities from the original toolbox."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from ..io.nifti import load_4d_matrix


def flip_left_right(data: np.ndarray) -> np.ndarray:
    """Flip a 3D or 4D image along the first (left-right) axis."""

    data = np.asarray(data)
    return data[::-1, ...]


def combine_images(images: list[np.ndarray], operation: str = "sum") -> np.ndarray:
    """Sum or multiply a list of 3D arrays."""

    if not images:
        raise ValueError("At least one image is required")
    result = np.asarray(images[0], dtype=float).copy()
    for image in images[1:]:
        if result.shape != np.asarray(image).shape:
            raise ValueError("All images must have the same shape")
        if operation == "sum":
            result = result + np.asarray(image, dtype=float)
        elif operation == "product":
            result = result * np.asarray(image, dtype=float)
        else:
            raise ValueError("operation must be 'sum' or 'product'")
    return result


def concatenate_sessions(
    images: list[str | Path],
    *,
    operation: str = "add",
    demean: bool = True,
) -> tuple[object, np.ndarray]:
    """Combine functional sessions using the original MultiRunCalc behavior."""

    if not images:
        raise ValueError("At least one session image is required")
    matrices = []
    reference = None
    for image in images:
        img, matrix = load_4d_matrix(image)
        matrices.append(matrix)
        reference = img if reference is None else reference
    if operation == "add":
        combined = np.concatenate(matrices, axis=1)
        if demean:
            combined = combined - np.mean(combined, axis=1, keepdims=True)
    elif operation == "mean":
        if not all(matrix.shape == matrices[0].shape for matrix in matrices):
            raise ValueError("All sessions must have the same shape for mean")
        combined = np.mean(np.stack(matrices, axis=2), axis=2)
    else:
        raise ValueError("operation must be 'add' or 'mean'")
    return reference, combined


def merge_images(images: list[str | Path]) -> tuple[object, np.ndarray]:
    """Merge 4D NIfTI sessions along the time axis."""

    if not images:
        raise ValueError("At least one image is required")
    matrices = []
    reference = None
    for image in images:
        img, matrix = load_4d_matrix(image)
        matrices.append(matrix)
        reference = img if reference is None else reference
    return reference, np.concatenate(matrices, axis=1)


__all__ = ["combine_images", "concatenate_sessions", "flip_left_right", "merge_images"]
