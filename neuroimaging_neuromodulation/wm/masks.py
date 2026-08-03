"""Tissue mask construction used by the white-matter workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Union

import nibabel as nib
import numpy as np

from ..io.nifti import load_volume, resample_to_grid, save_volume


def make_wm_mask(
    functional_image: str | Path,
    t1_segment_image: str | Path,
    exclude_image: str | Path,
    output_dir: str | Path,
    *,
    threshold: float = 0.9,
    out_name: str = "WMmask.nii",
) -> tuple[Path, np.ndarray]:
    """Build a white-matter mask in functional space from a c2 tissue segment."""

    func_img = nib.load(str(functional_image))
    _, segment = resample_to_grid(t1_segment_image, func_img, order=1)
    _, exclude = resample_to_grid(exclude_image, func_img, order=1)
    mask = np.asarray(segment, dtype=float)
    mask[np.asarray(exclude, dtype=bool)] = 0.0
    mask[mask < float(threshold)] = 0.0
    mask = (mask > 0).astype(np.float32)
    path = save_volume(mask, func_img, Path(output_dir) / out_name)
    return path, mask


def make_gm_mask(
    functional_image: str | Path,
    t1_segment_image: str | Path,
    exclude_image: str | Path,
    output_dir: str | Path,
    *,
    threshold: float = 0.1,
    out_name: str = "GMmask.nii",
) -> tuple[Path, np.ndarray]:
    """Build a grey-matter mask in functional space from a c1 tissue segment."""

    func_img = nib.load(str(functional_image))
    _, segment = resample_to_grid(t1_segment_image, func_img, order=1)
    _, exclude = resample_to_grid(exclude_image, func_img, order=1)
    mask = np.asarray(segment, dtype=float)
    mask[mask < float(threshold)] = 0.0
    mask = mask + np.asarray(exclude, dtype=float)
    mask = (mask > 0).astype(np.float32)
    path = save_volume(mask, func_img, Path(output_dir) / out_name)
    return path, mask


__all__ = ["make_gm_mask", "make_wm_mask"]
