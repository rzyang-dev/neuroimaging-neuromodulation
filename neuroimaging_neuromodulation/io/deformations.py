"""Nonlinear deformation-field resampling utilities.

SPM stores deformation fields as 4D NIfTI files whose fourth dimension
contains three voxel-coordinate channels. The convention used here follows
SPM's ``iy_*.nii`` inverse fields: for each output voxel, the field value is
the 1-based voxel coordinate in the image being sampled.
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

import nibabel as nib
import numpy as np
from scipy import ndimage

from .nifti import load_volume, save_volume

ImageLike = Union[str, Path, nib.spatialimages.SpatialImage]


def deformation_coordinates(
    deformation_image: ImageLike,
    *,
    one_based: bool = True,
) -> tuple[nib.Nifti1Image, np.ndarray]:
    """Return the 0-based sampling coordinates from a deformation field."""

    img, data = load_volume(deformation_image)
    if data.ndim != 4 or data.shape[3] != 3:
        raise ValueError(f"Expected a deformation field with shape (X, Y, Z, 3), got {data.shape}")
    coords = np.moveaxis(np.asarray(data, dtype=float)[..., :3], -1, 0)
    if one_based:
        coords = coords - 1.0
    return img, coords


def apply_deformation(
    source_image: ImageLike,
    deformation_image: ImageLike,
    out_path: str | Path | None = None,
    *,
    order: int = 1,
    one_based: bool = True,
) -> tuple[nib.Nifti1Image, np.ndarray]:
    """Sample ``source_image`` at the coordinates in ``deformation_image``.

    The returned image uses the deformation field's grid and affine. Binary
    masks should normally use ``order=0``; continuous images should use
    ``order=1`` or higher.
    """

    source_img = source_image if isinstance(source_image, nib.spatialimages.SpatialImage) else nib.load(str(source_image))
    source_data = np.asanyarray(source_img.dataobj)
    if source_data.ndim not in (3, 4):
        raise ValueError(f"Source image must be 3D or 4D, got {source_data.shape}")
    def_img, coords = deformation_coordinates(deformation_image, one_based=one_based)
    shape = def_img.shape[:3]
    if coords.shape[1:] != shape:
        raise ValueError("Deformation coordinate grid does not match deformation image shape")

    def sample_volume(volume: np.ndarray) -> np.ndarray:
        return ndimage.map_coordinates(
            volume,
            coords,
            order=order,
            mode="constant",
            cval=0.0,
            prefilter=True,
        )

    if source_data.ndim == 4:
        sampled = np.stack([sample_volume(source_data[..., t]) for t in range(source_data.shape[3])], axis=-1)
    else:
        sampled = sample_volume(source_data)
    result_img = nib.Nifti1Image(sampled.astype(np.float32), def_img.affine, header=def_img.header.copy())
    if hasattr(result_img.header, "set_slope_inter"):
        result_img.header.set_slope_inter(1.0, 0.0)
    result_data = np.asanyarray(result_img.dataobj)
    if out_path is not None:
        save_volume(result_data, def_img, out_path)
    return result_img, result_data


def identity_deformation(
    reference_image: ImageLike,
    out_path: str | Path | None = None,
    *,
    one_based: bool = True,
) -> tuple[nib.Nifti1Image, np.ndarray]:
    """Create an identity deformation field on a reference grid."""

    ref = reference_image if isinstance(reference_image, nib.spatialimages.SpatialImage) else nib.load(str(reference_image))
    grid = np.mgrid[0 : ref.shape[0], 0 : ref.shape[1], 0 : ref.shape[2]].astype(np.float32)
    coords = np.moveaxis(grid, 0, -1)
    if one_based:
        coords = coords + 1.0
    img = nib.Nifti1Image(coords, ref.affine, header=ref.header.copy())
    if out_path is not None:
        img.to_filename(str(out_path))
    return img, coords


__all__ = ["apply_deformation", "deformation_coordinates", "identity_deformation"]
