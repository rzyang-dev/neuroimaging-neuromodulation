"""Atlas-guided tissue probability estimation.

This is a lightweight approximation of SPM-style tissue classification. It
uses real SPM tissue priors and a Gaussian mixture expectation-maximization
step. It is not a replacement for validated SPM/DARTEL segmentation in clinical
work.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import nibabel as nib
import numpy as np

from ..io.nifti import load_volume, resample_to_grid, save_volume


def _normalize_intensities(data: np.ndarray, mask: np.ndarray) -> np.ndarray:
    values = data[mask]
    lo, hi = np.percentile(values, [1.0, 99.0])
    normalized = (data - lo) / max(float(hi - lo), 1e-8)
    return np.clip(normalized, 0.0, 1.0)


def _em_responsibilities(
    intensities: np.ndarray,
    priors: np.ndarray,
    iterations: int = 20,
) -> np.ndarray:
    n_classes, n_voxels = priors.shape
    prior_sum = priors.sum(axis=0, keepdims=True)
    prior_sum[prior_sum == 0] = 1.0
    priors = priors / prior_sum
    responsibilities = priors.copy()
    for _ in range(iterations):
        totals = responsibilities.sum(axis=1)
        totals[totals == 0] = 1.0
        means = (responsibilities @ intensities) / totals
        centered = intensities[None, :] - means[:, None]
        variances = (responsibilities * centered**2).sum(axis=1) / totals + 1e-6
        log_p = -0.5 * (centered**2 / variances[:, None] + np.log(2.0 * np.pi * variances[:, None]))
        log_posterior = log_p + np.log(np.maximum(priors, 1e-12))
        max_log = log_posterior.max(axis=0, keepdims=True)
        posterior = np.exp(log_posterior - max_log)
        responsibilities = posterior / posterior.sum(axis=0, keepdims=True)
    return responsibilities


def segment_tissue(
    t1_image: str | Path,
    output_dir: str | Path,
    *,
    grey_prior: str | Path,
    white_prior: str | Path,
    csf_prior: str | Path,
    iterations: int = 20,
    threshold: float = 0.05,
) -> dict[str, Path]:
    """Estimate GM/WM/CSF probability maps on a T1 grid."""

    img, data = load_volume(t1_image)
    if data.ndim != 3:
        raise ValueError("T1 image must be 3D")
    priors: list[np.ndarray] = []
    for prior_path in (grey_prior, white_prior, csf_prior):
        _, prior = resample_to_grid(prior_path, img, order=1)
        priors.append(np.asarray(prior, dtype=float))
    prior_stack = np.stack(priors, axis=0)
    mask = prior_stack.sum(axis=0) > threshold
    if mask.sum() < 100:
        raise ValueError("Tissue priors have insufficient overlap with the T1 grid")
    flat_mask = mask.reshape(-1)
    intensities = _normalize_intensities(np.asarray(data, dtype=float), mask)
    responsibilities = _em_responsibilities(
        intensities[mask],
        prior_stack.reshape(3, -1)[:, flat_mask],
        iterations=iterations,
    )

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    labels = ["c1", "c2", "c3"]
    paths: dict[str, Path] = {}
    for index, label in enumerate(labels):
        volume = np.zeros(data.shape, dtype=np.float32)
        volume[mask] = responsibilities[index]
        paths[label] = save_volume(volume, img, output_dir / f"{label}.nii")
    label_volume = np.zeros(data.shape, dtype=np.uint8)
    label_volume[mask] = np.argmax(responsibilities, axis=0) + 1
    paths["label"] = save_volume(label_volume, img, output_dir / "SegLabel.nii")
    return paths


__all__ = ["segment_tissue"]
