"""Numerical agreement metrics for images and deformation fields."""

from __future__ import annotations

import json
from pathlib import Path

import nibabel as nib
import numpy as np

from ..io.deformations import apply_deformation


def _finite_arrays(reference: np.ndarray, test: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    reference = np.asarray(reference, dtype=float).reshape(-1)
    test = np.asarray(test, dtype=float).reshape(-1)
    mask = np.isfinite(reference) & np.isfinite(test)
    if mask.sum() < 2:
        raise ValueError("Reference and test images have too few finite overlapping voxels")
    return reference[mask], test[mask]


def compare_volumes(reference: str | Path | nib.Nifti1Image, test: str | Path | nib.Nifti1Image) -> dict[str, float]:
    """Return correlation, RMSE, normalized RMSE, and MAE between two images."""

    if isinstance(reference, nib.Nifti1Image):
        ref_data = np.asanyarray(reference.dataobj)
    elif isinstance(reference, np.ndarray):
        ref_data = reference
    else:
        ref_data = np.asanyarray(nib.load(str(reference)).dataobj)
    if isinstance(test, nib.Nifti1Image):
        test_data = np.asanyarray(test.dataobj)
    elif isinstance(test, np.ndarray):
        test_data = test
    else:
        test_data = np.asanyarray(nib.load(str(test)).dataobj)
    if ref_data.shape != test_data.shape:
        raise ValueError(f"Shape mismatch: reference {ref_data.shape}, test {test_data.shape}")
    ref_flat, test_flat = _finite_arrays(ref_data, test_data)
    correlation = float(np.corrcoef(ref_flat, test_flat)[0, 1])
    rmse = float(np.sqrt(np.mean((ref_flat - test_flat) ** 2)))
    value_range = float(np.ptp(ref_flat))
    normalized_rmse = float(rmse / value_range) if value_range > 0 else float("nan")
    mae = float(np.mean(np.abs(ref_flat - test_flat)))
    return {
        "correlation": correlation,
        "rmse": rmse,
        "normalized_rmse": normalized_rmse,
        "mae": mae,
    }


def validate_deformation(
    moving_image: str | Path | nib.Nifti1Image,
    field_image: str | Path | nib.Nifti1Image,
    reference_image: str | Path | nib.Nifti1Image,
    *,
    order: int = 1,
    output_json: str | Path | None = None,
) -> dict[str, object]:
    """Apply a deformation field and compare the result to a reference image."""

    _, resampled = apply_deformation(moving_image, field_image, order=order)
    metrics = compare_volumes(reference_image, resampled)
    result: dict[str, object] = {
        "metrics": metrics,
        "moving_image": str(moving_image),
        "field_image": str(field_image),
        "reference_image": str(reference_image),
    }
    if output_json is not None:
        output_json = Path(output_json)
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
        result["output_json"] = str(output_json)
    return result


__all__ = ["compare_volumes", "validate_deformation"]
