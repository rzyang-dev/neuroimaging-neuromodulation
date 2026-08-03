"""Simple image utilities from the original toolbox."""

from __future__ import annotations

import numpy as np


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


__all__ = ["combine_images", "flip_left_right"]
