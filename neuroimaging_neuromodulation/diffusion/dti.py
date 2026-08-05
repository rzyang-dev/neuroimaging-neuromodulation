"""Diffusion tensor fitting and scalar metrics."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Union

import nibabel as nib
import numpy as np
from scipy import linalg

from ..io.nifti import save_volume


@dataclass(frozen=True)
class GradientTable:
    """Minimal gradient-table object used when DIPY is not installed."""

    bvals: np.ndarray
    bvecs: np.ndarray


@dataclass
class TensorFit:
    """NumPy-compatible tensor fit result exposed to metric/reporting code."""

    fa: np.ndarray
    md: np.ndarray
    ad: np.ndarray
    rd: np.ndarray
    eigenvalues: np.ndarray
    tensors: np.ndarray | None = None


def load_dwi(
    dwi_image: str | Path,
    bval_path: str | Path,
    bvec_path: str | Path,
) -> tuple[np.ndarray, np.ndarray, object, nib.Nifti1Image]:
    """Load DWI data, affine, and a gradient table.

    DIPY's gradient table is used when the ``diffusion`` extra is installed;
    otherwise a minimal NumPy gradient table is returned so tensor fitting can
    still run without DIPY.
    """

    img = nib.load(str(dwi_image))
    data = np.asanyarray(img.dataobj)
    if data.ndim != 4:
        raise ValueError(f"Expected 4D DWI data, got {data.shape}")
    bvals = np.loadtxt(bval_path)
    bvecs = np.loadtxt(bvec_path)
    if bvals.ndim != 1 or bvecs.ndim != 2 or bvecs.shape[1] != 3:
        raise ValueError("bval must be 1D and bvec must be Nx3")
    if bvals.size != data.shape[3] or bvecs.shape[0] != data.shape[3]:
        raise ValueError("bval/bvec length does not match DWI volumes")
    try:
        from dipy.core.gradients import gradient_table

        gtab = gradient_table(bvals, bvecs=bvecs)
    except ImportError:  # pragma: no cover - exercised in minimal installs
        gtab = GradientTable(bvals=bvals, bvecs=bvecs)
    return data, img.affine, gtab, img


def fit_tensor(
    data: np.ndarray,
    gtab: object,
    *,
    mask: np.ndarray | None = None,
) -> TensorFit:
    """Fit a diffusion tensor model with NumPy/SciPy weighted least squares."""

    data = np.asarray(data, dtype=float)
    if data.ndim != 4:
        raise ValueError(f"Expected 4D DWI data, got {data.shape}")
    bvals = np.asarray(getattr(gtab, "bvals"), dtype=float)
    bvecs = np.asarray(getattr(gtab, "bvecs"), dtype=float)
    if bvals.ndim != 1 or bvecs.ndim != 2 or bvecs.shape[1] != 3:
        raise ValueError("bvals must be 1D and bvecs must be Nx3")
    if bvals.size != data.shape[-1] or bvecs.shape[0] != data.shape[-1]:
        raise ValueError("bval/bvec length does not match DWI volumes")
    if mask is None:
        mask = np.any(data != 0, axis=3)
    mask = np.asarray(mask, dtype=bool)
    if mask.shape != data.shape[:3]:
        raise ValueError(f"Mask shape {mask.shape} does not match DWI grid")

    bvals = np.clip(bvals, 0.0, None)
    design = np.column_stack(
        [
            -bvals * bvecs[:, 0] ** 2,
            -bvals * bvecs[:, 1] ** 2,
            -bvals * bvecs[:, 2] ** 2,
            -2.0 * bvals * bvecs[:, 0] * bvecs[:, 1],
            -2.0 * bvals * bvecs[:, 0] * bvecs[:, 2],
            -2.0 * bvals * bvecs[:, 1] * bvecs[:, 2],
            np.ones_like(bvals),
        ]
    )
    voxel_indices = np.argwhere(mask)
    eigenvalues = np.zeros((*data.shape[:3], 3), dtype=float)
    tensors = np.zeros((*data.shape[:3], 3, 3), dtype=float)
    for x, y, z in voxel_indices:
        signal = np.maximum(data[x, y, z], np.finfo(float).tiny)
        log_signal = np.log(signal)
        weights = signal
        weighted_design = design * weights[:, None]
        weighted_target = log_signal * weights
        normal_matrix = np.asarray(
            weighted_design.T @ weighted_design,
            dtype=np.float64,
        )
        normal_target = np.asarray(
            weighted_design.T @ weighted_target,
            dtype=np.float64,
        )
        params = linalg.solve(
            normal_matrix + np.eye(design.shape[1], dtype=np.float64) * 1e-12,
            normal_target,
            assume_a="pos",
            check_finite=False,
        )
        tensor = np.array(
            [
                [params[0], params[3], params[4]],
                [params[3], params[1], params[5]],
                [params[4], params[5], params[2]],
            ]
        )
        vals = np.linalg.eigvalsh(tensor)
        eigenvalues[x, y, z] = vals
        tensors[x, y, z] = tensor

    md = eigenvalues.mean(axis=3)
    ad = eigenvalues[..., 2]
    rd = eigenvalues[..., :2].mean(axis=3)
    numerator = np.sqrt(1.5 * np.sum((eigenvalues - md[..., None]) ** 2, axis=3))
    denominator = np.sqrt(np.sum(eigenvalues**2, axis=3))
    fa = np.divide(
        numerator,
        denominator,
        out=np.zeros_like(md),
        where=denominator > 0,
    )
    return TensorFit(
        fa=fa,
        md=md,
        ad=ad,
        rd=rd,
        eigenvalues=eigenvalues,
        tensors=tensors,
    )


def write_tensor_metrics(
    fit: object,
    reference_image: nib.Nifti1Image,
    output_dir: str | Path,
    *,
    prefix: str = "DTI",
) -> dict[str, Path]:
    """Write FA, MD, AD, and RD maps as NIfTI files."""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics = {
        "FA": fit.fa,
        "MD": fit.md,
        "AD": fit.ad,
        "RD": fit.rd,
    }
    paths: dict[str, Path] = {}
    for name, values in metrics.items():
        values = np.asarray(values, dtype=np.float32)
        paths[name] = save_volume(values, reference_image, output_dir / f"{prefix}_{name}.nii")
    return paths


__all__ = ["GradientTable", "TensorFit", "fit_tensor", "load_dwi", "write_tensor_metrics"]
