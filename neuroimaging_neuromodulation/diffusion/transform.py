"""Transform streamlines with SPM-style deformation fields."""

from __future__ import annotations

from pathlib import Path

import nibabel as nib
import numpy as np
from scipy import ndimage

from ..io.nifti import load_volume


def transform_streamlines_with_field(
    streamlines: list[np.ndarray],
    deformation_image: str | Path | nib.Nifti1Image,
    source_image: str | Path | nib.Nifti1Image,
    reference_image: str | Path | nib.Nifti1Image,
    *,
    one_based: bool = True,
    coordinate_system: str = "world",
) -> list[np.ndarray]:
    """Apply a 4D coordinate field to streamlines in source world space.

    SPM fields store world coordinates (``coordinate_system="world"``). The
    legacy 1-based voxel convention used by earlier DIPY field writers is
    available through ``coordinate_system="voxel"``.
    """

    field_img, field_data = load_volume(deformation_image)
    if field_data.ndim == 5 and field_data.shape[3] == 1 and field_data.shape[4] == 3:
        field_data = field_data[..., 0, :]
    if field_data.ndim != 4 or field_data.shape[3] != 3:
        raise ValueError("deformation_image must be a 4D NIfTI with three coordinate channels")
    source_img = source_image if isinstance(source_image, nib.Nifti1Image) else nib.load(str(source_image))
    reference_img = reference_image if isinstance(reference_image, nib.Nifti1Image) else nib.load(str(reference_image))
    if field_data.shape[:3] != source_img.shape[:3]:
        raise ValueError("deformation field grid must match the source image grid")

    inv_source = np.linalg.inv(source_img.affine)
    transformed = []
    for streamline in streamlines:
        points = np.asarray(streamline, dtype=float)
        if points.ndim != 2 or points.shape[1] != 3:
            raise ValueError("Each streamline must be an Nx3 array")
        source_voxel = inv_source @ np.column_stack(
            [points, np.ones(len(points), dtype=float)]
        ).T
        sampled = np.stack(
            [
                ndimage.map_coordinates(
                    field_data[..., channel],
                    source_voxel[:3, :],
                    order=1,
                    mode="constant",
                    cval=0.0,
                )
                for channel in range(3)
            ],
            axis=0,
        )
        if coordinate_system == "world":
            world = sampled.T
        elif coordinate_system == "voxel":
            if one_based:
                sampled = sampled - 1.0
            reference_voxel = np.vstack([sampled, np.ones(sampled.shape[1], dtype=float)])
            world = (reference_img.affine @ reference_voxel).T[:, :3]
        else:
            raise ValueError("coordinate_system must be 'voxel' or 'world'")
        transformed.append(world)
    return transformed


__all__ = ["transform_streamlines_with_field"]
