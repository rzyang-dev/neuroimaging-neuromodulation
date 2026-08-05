"""Python-native white-matter connectivity analyses.

These functions implement the useful algorithmic parts of the original
MATLAB scripts without requiring MATLAB, SPM, FSL, or DIPY.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

import numpy as np

from ..io.nifti import load_volume, save_volume


def _validate_functional(data: np.ndarray, mask: np.ndarray | None) -> None:
    if data.ndim != 4:
        raise ValueError(f"Functional data must be 4D, got shape {data.shape}")
    if data.shape[-1] < 2:
        raise ValueError("Functional data must contain at least two timepoints")
    if mask is not None and mask.shape != data.shape[:3]:
        raise ValueError(
            f"Mask shape {mask.shape} does not match functional grid {data.shape[:3]}"
        )


def _hemisphere_masks(
    mask: np.ndarray,
    axis: int = 0,
    *,
    left_first: bool = True,
) -> tuple[np.ndarray, np.ndarray]:
    if mask.ndim != 3:
        raise ValueError(f"Mask must be 3D, got shape {mask.shape}")
    if axis not in (0, 1, 2):
        raise ValueError("axis must be 0, 1, or 2")
    binary = mask > 0
    midpoint = (binary.shape[axis] + 1) // 2
    left = np.zeros_like(binary)
    right = np.zeros_like(binary)
    first = [slice(None)] * 3
    second = [slice(None)] * 3
    first[axis] = slice(0, midpoint)
    second[axis] = slice(midpoint, None)
    if left_first:
        left[tuple(first)] = binary[tuple(first)]
        right[tuple(second)] = binary[tuple(second)]
    else:
        right[tuple(first)] = binary[tuple(first)]
        left[tuple(second)] = binary[tuple(second)]
    return left, right


def _mirror_pairs(
    left: np.ndarray,
    right: np.ndarray,
    axis: int = 0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    left_indices = np.argwhere(left)
    right_indices = np.argwhere(right)
    right_lookup = {
        tuple(int(v) for v in idx): n for n, idx in enumerate(right_indices)
    }
    left_for_right: list[int] = []
    right_for_left: list[int] = []
    left_pairs: list[np.ndarray] = []
    right_pairs: list[np.ndarray] = []
    for left_idx in left_indices:
        mirror = left_idx.copy()
        mirror[axis] = int(left.shape[axis] - 1 - mirror[axis])
        right_pos = right_lookup.get(tuple(int(v) for v in mirror))
        if right_pos is not None:
            left_pairs.append(left_idx)
            right_pairs.append(mirror)
            left_for_right.append(len(left_pairs) - 1)
            right_for_left.append(right_pos)
    if not left_pairs:
        raise ValueError("No homotopic left/right mask pairs found")
    return (
        np.asarray(left_pairs, dtype=int),
        np.asarray(right_pairs, dtype=int),
        np.asarray(left_for_right, dtype=int),
        np.asarray(right_for_left, dtype=int),
    )


def _zscore_selected(data: np.ndarray, indices: np.ndarray) -> np.ndarray:
    flat = (
        indices[:, 0] * data.shape[1] * data.shape[2]
        + indices[:, 1] * data.shape[2]
        + indices[:, 2]
    )
    values = data.reshape(-1, data.shape[-1])[flat]
    values = values.astype(np.float64)
    centered = values - values.mean(axis=1, keepdims=True)
    std = centered.std(axis=1, keepdims=True)
    std[std < 1e-12] = 1.0
    return centered / std


def functional_homotopic_connectivity(
    functional: str | Path,
    mask: str | Path | None = None,
    output_path: str | Path | None = None,
    *,
    axis: int = 0,
    left_first: bool = True,
    r_threshold: float | None = None,
) -> tuple[np.ndarray, dict[str, object]]:
    """Compute mirrored homotopic voxel-wise functional connectivity."""

    img, data = load_volume(functional)
    mask_data = None
    if mask is not None:
        _mask_img, mask_data = load_volume(mask)
    _validate_functional(data, mask_data)
    if mask_data is None:
        mask_data = np.any(np.asarray(data) != 0, axis=3).astype(np.uint8)
    left, right = _hemisphere_masks(mask_data, axis=axis, left_first=left_first)
    left_pairs, right_pairs, left_for_right, right_for_left = _mirror_pairs(
        left, right, axis=axis
    )
    left_series = _zscore_selected(np.asarray(data), left_pairs)
    right_series = _zscore_selected(np.asarray(data), right_pairs)
    correlations = np.sum(left_series * right_series, axis=1) / (data.shape[-1] - 1)
    if r_threshold is not None:
        correlations[correlations < float(r_threshold)] = 0.0
    result = np.zeros(data.shape[:3], dtype=np.float32)
    result[left_pairs[:, 0], left_pairs[:, 1], left_pairs[:, 2]] = correlations
    result[right_pairs[:, 0], right_pairs[:, 1], right_pairs[:, 2]] = correlations
    summary = {
        "axis": axis,
        "left_first": left_first,
        "pairs": int(len(correlations)),
        "mean": float(np.mean(correlations)) if len(correlations) else None,
        "std": float(np.std(correlations)) if len(correlations) else None,
    }
    if output_path is not None:
        save_volume(result, img, output_path)
    return result, summary


def fc_asymmetry_index(
    functional: str | Path,
    mask: str | Path | None = None,
    output_path: str | Path | None = None,
    *,
    axis: int = 0,
    left_first: bool = True,
    r_threshold: float = 0.25,
    chunk_size: int = 2000,
) -> tuple[np.ndarray, dict[str, object]]:
    """Compute a thresholded left/right functional-connectivity asymmetry map."""

    img, data = load_volume(functional)
    mask_data = None
    if mask is not None:
        _mask_img, mask_data = load_volume(mask)
    _validate_functional(data, mask_data)
    if mask_data is None:
        mask_data = np.any(np.asarray(data) != 0, axis=3).astype(np.uint8)
    left, right = _hemisphere_masks(mask_data, axis=axis, left_first=left_first)
    left_indices = np.argwhere(left)
    right_indices = np.argwhere(right)
    if len(left_indices) == 0 or len(right_indices) == 0:
        raise ValueError("FC asymmetry requires non-empty left and right masks")
    left_series = _zscore_selected(np.asarray(data), left_indices)
    right_series = _zscore_selected(np.asarray(data), right_indices)
    n_time = data.shape[-1] - 1

    degree_left_inside = np.zeros(len(left_indices), dtype=np.int32)
    degree_left_across = np.zeros(len(left_indices), dtype=np.int32)
    for start in range(0, len(left_indices), chunk_size):
        end = min(start + chunk_size, len(left_indices))
        block = left_series[start:end]
        inside = (block @ left_series.T) / n_time
        across = (block @ right_series.T) / n_time
        degree_left_inside[start:end] = np.sum(inside > r_threshold, axis=1)
        degree_left_across[start:end] = np.sum(across > r_threshold, axis=1)

    degree_right_inside = np.zeros(len(right_indices), dtype=np.int32)
    degree_right_across = np.zeros(len(right_indices), dtype=np.int32)
    for start in range(0, len(right_indices), chunk_size):
        end = min(start + chunk_size, len(right_indices))
        block = right_series[start:end]
        inside = (block @ right_series.T) / n_time
        across = (block @ left_series.T) / n_time
        degree_right_inside[start:end] = np.sum(inside > r_threshold, axis=1)
        degree_right_across[start:end] = np.sum(across > r_threshold, axis=1)

    denom_left = degree_left_inside + degree_left_across
    denom_right = degree_right_inside + degree_right_across
    index_left = np.divide(
        degree_left_inside - degree_left_across,
        denom_left,
        out=np.zeros_like(degree_left_inside, dtype=float),
        where=denom_left > 0,
    )
    index_right = np.divide(
        degree_right_inside - degree_right_across,
        denom_right,
        out=np.zeros_like(degree_right_inside, dtype=float),
        where=denom_right > 0,
    )
    result = np.zeros(data.shape[:3], dtype=np.float32)
    result[left_indices[:, 0], left_indices[:, 1], left_indices[:, 2]] = index_left
    result[right_indices[:, 0], right_indices[:, 1], right_indices[:, 2]] = index_right
    values = np.concatenate([index_left, index_right])
    summary = {
        "axis": axis,
        "left_first": left_first,
        "r_threshold": r_threshold,
        "left_voxels": int(len(left_indices)),
        "right_voxels": int(len(right_indices)),
        "mean": float(np.mean(values)),
        "std": float(np.std(values)),
    }
    if output_path is not None:
        save_volume(result, img, output_path)
    return result, summary


def _pearson(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=float).ravel()
    b = np.asarray(b, dtype=float).ravel()
    if a.std() < 1e-12 or b.std() < 1e-12:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def fc_pattern_correlations(
    images: Sequence[str | Path],
    outcomes: Sequence[float],
    output_json: str | Path | None = None,
    reference_output: str | Path | None = None,
) -> dict[str, object]:
    """Compute leave-one-out correlations to a weighted reference FC pattern."""

    if len(images) < 2:
        raise ValueError("fc-pattern requires at least two images")
    if len(images) != len(outcomes):
        raise ValueError("images and outcomes must have the same length")
    outcome_values = np.asarray(outcomes, dtype=float)
    if np.allclose(outcome_values, 0.0):
        raise ValueError("outcomes must contain at least one nonzero value")

    vectors: list[np.ndarray] = []
    reference_image = None
    shape = None
    for path in images:
        img, data = load_volume(path)
        if data.ndim != 3:
            raise ValueError(f"FC pattern images must be 3D, got shape {data.shape}")
        vectors.append(np.asarray(data, dtype=float).ravel())
        reference_image = img
        shape = data.shape

    matrix = np.vstack(vectors)
    reference = np.average(matrix, axis=0, weights=outcome_values)
    correlations: list[float] = []
    for index in range(len(matrix)):
        weights = outcome_values.copy()
        weights[index] = 0.0
        if np.allclose(weights, 0.0):
            correlations.append(0.0)
            continue
        leave_one_out = np.average(matrix, axis=0, weights=weights)
        correlations.append(_pearson(matrix[index], leave_one_out))

    result: dict[str, object] = {
        "image_count": len(images),
        "correlations": correlations,
        "mean_correlation": float(np.mean(correlations)),
        "std_correlation": float(np.std(correlations)),
    }
    if reference_output is not None and reference_image is not None and shape is not None:
        save_volume(reference.reshape(shape), reference_image, reference_output)
        result["reference_output"] = str(Path(reference_output))
    if output_json is not None:
        path = Path(output_json)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


__all__ = [
    "fc_asymmetry_index",
    "fc_pattern_correlations",
    "functional_homotopic_connectivity",
]
