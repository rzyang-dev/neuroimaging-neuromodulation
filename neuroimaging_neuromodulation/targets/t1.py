"""T1-based target image generation matching the original T1 workflow."""

from __future__ import annotations

from pathlib import Path

import nibabel as nib
import numpy as np

from ..io.deformations import apply_deformation
from ..io.nifti import load_volume, resample_to_grid, save_volume
from ..validation.metrics import compare_volumes
from ..validation.spm import run_spm_segmentation


def individual_target_from_t1(
    target_image: str | Path,
    deformation_field: str | Path,
    t1_image: str | Path,
    output_path: str | Path,
) -> tuple[Path, np.ndarray]:
    """Write an MNI target ROI into T1 space using an SPM y_ field."""

    deformed_img, deformed = apply_deformation(
        target_image,
        deformation_field,
        order=0,
    )
    t1_img = t1_image if isinstance(t1_image, nib.Nifti1Image) else nib.load(str(t1_image))
    _, resampled = resample_to_grid(
        nib.Nifti1Image(deformed.astype(np.float32), deformed_img.affine),
        t1_img,
        order=0,
    )
    output_path = Path(output_path)
    save_volume(resampled, t1_img, output_path)
    return output_path, np.asarray(resampled, dtype=float)


def generate_t1_target(
    t1_image: str | Path,
    target_image: str | Path,
    output_path: str | Path,
    *,
    deformation_field: str | Path | None = None,
    spm_exe: str | Path | None = None,
    spm_output_dir: str | Path | None = None,
    timeout: int = 1800,
) -> dict[str, object]:
    """Generate a T1-space target, optionally via SPM25 segmentation."""

    if deformation_field is not None:
        path, data = individual_target_from_t1(
            target_image,
            deformation_field,
            t1_image,
            output_path,
        )
        return {
            "output_path": path,
            "deformation_field": Path(deformation_field),
            "target_data_shape": data.shape,
        }

    output_path = Path(output_path)
    spm_dir = Path(spm_output_dir) if spm_output_dir is not None else output_path.parent / "spm_segmentation"
    result = run_spm_segmentation(t1_image, spm_dir, spm_exe=spm_exe, timeout=timeout)
    y_path = Path(result["y_field"])
    _, resampled = apply_deformation(
        Path(result["c1"]),
        y_path,
        coordinate_system="world",
        order=1,
    )
    result["metrics"] = compare_volumes(Path(result["wc1"]), resampled)
    path, data = individual_target_from_t1(
        target_image,
        y_path,
        t1_image,
        output_path,
    )
    result.update(
        {
            "output_path": path,
            "target_data_shape": data.shape,
        }
    )
    return result


__all__ = ["generate_t1_target", "individual_target_from_t1"]
