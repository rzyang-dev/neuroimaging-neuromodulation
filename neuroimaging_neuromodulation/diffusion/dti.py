"""Diffusion tensor fitting and scalar metrics."""

from __future__ import annotations

from pathlib import Path
from typing import Union

import nibabel as nib
import numpy as np

from ..io.nifti import save_volume


def load_dwi(
    dwi_image: str | Path,
    bval_path: str | Path,
    bvec_path: str | Path,
) -> tuple[np.ndarray, np.ndarray, object, nib.Nifti1Image]:
    """Load DWI data, affine, and a DIPY gradient table."""

    from dipy.core.gradients import gradient_table

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
    gtab = gradient_table(bvals, bvecs=bvecs)
    return data, img.affine, gtab, img


def fit_tensor(
    data: np.ndarray,
    gtab: object,
    *,
    mask: np.ndarray | None = None,
) -> object:
    """Fit a diffusion tensor model with DIPY."""

    from dipy.reconst.dti import TensorModel

    model = TensorModel(gtab, fit_method="WLS")
    return model.fit(data, mask=mask)


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


__all__ = ["fit_tensor", "load_dwi", "write_tensor_metrics"]
