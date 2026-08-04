"""Transform streamlines with SPM-style deformation fields."""

from __future__ import annotations

import tempfile
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


def transform_streamlines_with_ants(
    streamlines: list[np.ndarray],
    transforms: list[str | Path],
    *,
    use_inverse: int = 1,
    transform_inverse: list[int] | None = None,
) -> list[np.ndarray]:
    """Transform streamlines with ANTs point transforms.

    ANTs expects points in LPS coordinates, so RAS streamlines are converted
    before running ``antsApplyTransformsToPoints`` and converted back after.
    """

    from ..preprocess.ants import run_ants_apply_transforms_to_points

    rows = []
    for streamline_index, streamline in enumerate(streamlines):
        for point in np.asarray(streamline, dtype=float):
            rows.append([-point[0], -point[1], point[2], streamline_index])
    if not rows:
        return []
    with tempfile.TemporaryDirectory() as tmp:
        input_csv = Path(tmp) / "points.csv"
        output_csv = Path(tmp) / "points_out.csv"
        np.savetxt(
            input_csv,
            np.asarray(rows, dtype=float),
            delimiter=",",
            header="x,y,z,t",
            comments="",
        )
        run_ants_apply_transforms_to_points(
            input_csv,
            output_csv,
            transforms,
            use_inverse=use_inverse,
            transform_inverse=transform_inverse,
        )
        transformed_data = np.loadtxt(output_csv, delimiter=",", skiprows=1)
        if transformed_data.ndim == 1:
            transformed_data = transformed_data.reshape(1, -1)
    transformed: list[np.ndarray] = []
    for streamline_index in range(len(streamlines)):
        points = transformed_data[transformed_data[:, 3] == streamline_index, :3].copy()
        points[:, 0] *= -1.0
        points[:, 1] *= -1.0
        transformed.append(points)
    return transformed


__all__ = ["transform_streamlines_with_ants", "transform_streamlines_with_field"]
