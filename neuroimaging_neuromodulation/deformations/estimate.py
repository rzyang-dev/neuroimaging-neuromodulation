"""Nonlinear deformation estimation using DIPY."""

from __future__ import annotations

import logging
from pathlib import Path

import nibabel as nib
import numpy as np
from scipy import ndimage

from ..io.nifti import load_volume, save_volume


def _coordinates_from_mapping(
    mapping: object,
    shape: tuple[int, int, int],
    coord2world: np.ndarray,
    world2coord: np.ndarray,
    direction: str = "forward",
) -> np.ndarray:
    """Sample DIPY mapping coordinates on a grid and return voxel coordinates."""

    grid = np.indices(shape, dtype=np.float32)
    points = grid.reshape(3, -1).T
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
    return coords.reshape((*shape, 3)).astype(np.float32)


def _normalize(data: np.ndarray) -> np.ndarray:
    data = np.asarray(data, dtype=float)
    minimum = float(np.min(data))
    maximum = float(np.max(data))
    if maximum - minimum < 1e-12:
        return np.zeros_like(data)
    return (data - minimum) / (maximum - minimum)


def _internal_demons(
    moving: np.ndarray,
    static: np.ndarray,
    *,
    iterations: int = 80,
    smooth_sigma: float = 1.0,
    step_limit: float = 0.5,
) -> tuple[np.ndarray, np.ndarray]:
    """Estimate a dense static-to-moving displacement field with Demons flow."""

    moving = _normalize(moving)
    static = _normalize(static)
    grid = np.indices(static.shape, dtype=float)
    displacement = np.zeros((3, *static.shape), dtype=float)
    warped = moving.copy()
    gradient = np.asarray(np.gradient(static), dtype=float)
    for _ in range(iterations):
        warped = ndimage.map_coordinates(
            moving,
            grid + displacement,
            order=1,
            mode="constant",
            cval=0.0,
        )
        difference = static - warped
        numerator = difference[None, ...] * gradient
        denominator = (
            np.sum(gradient**2, axis=0)
            + difference**2
            + 1e-6
        )
        update = numerator / denominator[None, ...]
        update = np.clip(update, -step_limit, step_limit)
        update = ndimage.gaussian_filter(update, sigma=smooth_sigma)
        displacement = displacement + update
    return displacement, warped


def estimate_deformation(
    moving_image: str | Path | nib.Nifti1Image,
    static_image: str | Path | nib.Nifti1Image,
    output_dir: str | Path,
    *,
    metric: str = "CC",
    level_iters: tuple[int, ...] = (10, 10, 5),
    step_length: float = 0.25,
    engine: str = "internal",
) -> dict[str, Path]:
    """Estimate a nonlinear mapping and write DIPY + coordinate-field outputs.

    The coordinate field uses SPM's world-coordinate convention, so it can be
    passed directly to ``apply_deformation`` and target/seed resampling
    commands. ``y_ac_coT1.nii`` is the template-to-native pullback field used
    by ``apply_deformation``; ``iy_ac_coT1.nii`` is the native-to-template
    forward field used by streamline transforms.
    """

    moving_img = moving_image if isinstance(moving_image, nib.Nifti1Image) else nib.load(str(moving_image))
    static_img = static_image if isinstance(static_image, nib.Nifti1Image) else nib.load(str(static_image))
    moving_data = np.asanyarray(moving_img.dataobj).astype(np.float32)
    static_data = np.asanyarray(static_img.dataobj).astype(np.float32)
    if moving_data.ndim != 3 or static_data.ndim != 3:
        raise ValueError("moving and static images must be 3D")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    static_shape = tuple(int(x) for x in static_data.shape)
    moving_shape = tuple(int(x) for x in moving_data.shape)

    if engine == "internal":
        displacement, warped = _internal_demons(
            moving_data,
            static_data,
            iterations=max(int(level_iters[-1]) * 20, 40),
        )
        mapping_path = output_dir / "dipy_mapping.nii.gz"
        save_volume(
            np.moveaxis(displacement, 0, -1),
            static_img,
            mapping_path,
        )
        static_grid = np.indices(static_shape, dtype=float)
        moving_grid = np.indices(moving_shape, dtype=float)
        y_coordinates = static_grid + displacement
        displacement_at_moving = np.stack(
            [
                ndimage.map_coordinates(
                    displacement[channel],
                    moving_grid,
                    order=1,
                    mode="constant",
                    cval=0.0,
                )
                for channel in range(3)
            ],
            axis=0,
        )
        iy_coordinates = moving_grid - displacement_at_moving

        def _to_world(coordinates: np.ndarray, affine: np.ndarray) -> np.ndarray:
            flat = np.ascontiguousarray(coordinates).reshape(3, -1).T
            hom = np.column_stack([flat, np.ones(len(flat), dtype=float)])
            return (affine @ hom.T).T[:, :3].reshape((*coordinates.shape[1:], 3))

        y_world = _to_world(y_coordinates, moving_img.affine)
        iy_world = _to_world(iy_coordinates, static_img.affine)
        coordinate_path = output_dir / "coordinate_field.nii"
        save_volume(iy_world, static_img, coordinate_path)
        y_path = output_dir / "y_ac_coT1.nii"
        save_volume(iy_world, static_img, y_path)
        iy_path = output_dir / "iy_ac_coT1.nii"
        save_volume(y_world, moving_img, iy_path)
        warped_path = output_dir / "warped_moving.nii"
        save_volume(np.asarray(warped, dtype=np.float32), static_img, warped_path)
        return {
            "dipy_mapping": mapping_path,
            "coordinate_field": coordinate_path,
            "iy_field": iy_path,
            "y_field": y_path,
            "warped_moving": warped_path,
        }
    if engine != "dipy":
        raise ValueError("engine must be 'internal' or 'dipy'")

    try:
        from dipy.align import syn_registration, write_mapping
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "DIPY is required for the optional 'dipy' deformation engine."
        ) from exc

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
    mapping_path = output_dir / "dipy_mapping.nii.gz"
    write_mapping(mapping, str(mapping_path))
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
    def _to_world(coordinates: np.ndarray, affine: np.ndarray) -> np.ndarray:
        flat = np.ascontiguousarray(coordinates).reshape(-1, 3)
        hom = np.column_stack([flat, np.ones(len(flat), dtype=float)])
        return (affine @ hom.T).T[:, :3].reshape((*coordinates.shape[:3], 3))

    iy_world = _to_world(iy_coordinates, moving_img.affine)
    y_world = _to_world(y_coordinates, static_img.affine)
    coordinate_path = output_dir / "coordinate_field.nii"
    save_volume(iy_world, static_img, coordinate_path)
    y_path = output_dir / "y_ac_coT1.nii"
    save_volume(iy_world, static_img, y_path)
    iy_path = output_dir / "iy_ac_coT1.nii"
    save_volume(y_world, moving_img, iy_path)
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
