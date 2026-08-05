"""Multi-run merge utilities for repeated functional sessions."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import numpy as np

from ..io.nifti import load_volume, save_volume


def merge_runs(
    inputs: Sequence[str | Path],
    output_path: str | Path,
    *,
    mode: str = "add",
    demean: bool = True,
) -> Path:
    """Merge repeated functional runs by concatenation or element-wise mean.

    ``mode="add"`` concatenates demeaned runs along the time axis, matching the
    original multi-run analysis pattern. ``mode="mean"`` averages corresponding
    volumes and timepoints across runs.
    """

    if mode not in {"add", "mean"}:
        raise ValueError("mode must be 'add' or 'mean'")
    if len(inputs) < 2:
        raise ValueError("multi-run requires at least two input runs")

    images = []
    arrays: list[np.ndarray] = []
    for path in inputs:
        img, data = load_volume(path)
        if data.ndim != 4:
            raise ValueError(f"Each run must be 4D, got shape {data.shape}")
        arrays.append(np.asarray(data, dtype=np.float64))
        images.append(img)

    shape = arrays[0].shape
    if any(array.shape != shape for array in arrays[1:]):
        raise ValueError("All runs must have the same spatial and time dimensions")
    for index, array in enumerate(arrays):
        if demean:
            arrays[index] = array - array.mean(axis=3, keepdims=True)

    if mode == "add":
        merged = np.concatenate(arrays, axis=3)
    else:
        merged = np.mean(np.stack(arrays, axis=0), axis=0)

    return save_volume(merged, images[0], output_path)


__all__ = ["merge_runs"]
