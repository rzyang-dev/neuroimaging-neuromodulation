"""Nonlinear deformation estimation using DIPY."""

from __future__ import annotations

import logging
from pathlib import Path

import nibabel as nib
import numpy as np

from ..io.nifti import load_volume, save_volume


def _coordinates_from_mapping(
    mapping: object,
    shape: tuple[int, int, int],
    coord2world: np.ndarray,
    world2coord: np.ndarray,
    direction: str = "forward",
) -> np.ndarray:
    """Sample DIPY mapping coordinates on a grid and make them 1-based."""

    grid = np.indices(shape, dtype=np.float32)
    points = np.moveaxis(grid, 0, -1).reshape(-1, 3)
    if direction == "forward":
        coords = mapping._warp_coordinates_forward(
            points,
            coord2world=np.asarray(coord2world, dtype=float),
            world2coord=np.asarray(world2coord, dtype=float),
        )
    elif direction == "backward":
        coords = mapping._warp_coordinates_backward(
            points,
            coord2world=np.asarray(coord2world, dtype=float),
            world2coord=np.asarray(world2coord, dtype=float),
        )
    else:
        raise ValueError("direction must be 'forward' or 'backward'")
    return coords.reshape((*shape, 3)).astype(np.float32) + 1.0


def estimate_deformation(
    moving_image: str | Path | nib.Nifti1Image,
    static_image: str | Path | nib.Nifti1Image,
    output_dir: str | Path,
    *,
    metric: str = "CC",
    level_iters: tuple[int, ...] = (10, 10, 5),
    step_length: float = 0.25,
) -> dict[str, Path]:
    """Estimate a nonlinear mapping and write DIPY + coordinate-field outputs.

    The coordinate field is in the same 1-based SPM-style convention used by
    ``apply_deformation``, so it can be passed directly to target and seed
    resampling commands.
    """

    try:
        from dipy.align import syn_registration, write_mapping
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("DIPY is required for deformation estimation.") from exc

    moving_img = moving_image if isinstance(moving_image, nib.Nifti1Image) else nib.load(str(moving_image))
    static_img = static_image if isinstance(static_image, nib.Nifti1Image) else nib.load(str(static_image))
    moving_data = np.asanyarray(moving_img.dataobj).astype(np.float32)
    static_data = np.asanyarray(static_img.dataobj).astype(np.float32)
    if moving_data.ndim != 3 or static_data.ndim != 3:
        raise ValueError("moving and static images must be 3D")

    logging.getLogger("dipy").setLevel(logging.ERROR)
    warped, mapping = syn_registration(
        moving_data,
        static_data,
        moving_affine=moving_img.affine,
        static_affine=static_img.affine,
        metric=metric,
        level_iters=list(level_iters),
        step_length=step_length,
    )
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    mapping_path = output_dir / "dipy_mapping.nii.gz"
    write_mapping(mapping, str(mapping_path))
    static_shape = tuple(int(x) for x in static_data.shape)
    moving_shape = tuple(int(x) for x in moving_data.shape)
    iy_coordinates = _coordinates_from_mapping(
        mapping,
        static_shape,
        static_img.affine,
        np.linalg.inv(moving_img.affine),
        direction="forward",
    )
    y_coordinates = _coordinates_from_mapping(
        mapping,
        moving_shape,
        moving_img.affine,
        np.linalg.inv(static_img.affine),
        direction="backward",
    )
    coordinate_path = output_dir / "coordinate_field.nii"
    save_volume(iy_coordinates, static_img, coordinate_path)
    iy_path = output_dir / "iy_ac_coT1.nii"
    save_volume(iy_coordinates, static_img, iy_path)
    y_path = output_dir / "y_ac_coT1.nii"
    save_volume(y_coordinates, moving_img, y_path)
    warped_path = output_dir / "warped_moving.nii"
    save_volume(np.asarray(warped, dtype=np.float32), static_img, warped_path)
    return {
        "dipy_mapping": mapping_path,
        "coordinate_field": coordinate_path,
        "iy_field": iy_path,
        "y_field": y_path,
        "warped_moving": warped_path,
    }


__all__ = ["estimate_deformation"]
