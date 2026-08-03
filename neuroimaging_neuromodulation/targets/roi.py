"""ROI, dilation, depth, and deep-target utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Union

import nibabel as nib
import numpy as np
from scipy import ndimage

from ..coordinates import mat_to_mni, mni_to_mat, voxel_size
from ..io.nifti import load_volume, resample_to_grid, save_volume


def sphere_roi(
    center_mni: Union[list, tuple, np.ndarray],
    radius_mm: float,
    reference_image: Union[str, Path, nib.Nifti1Image],
    out_path: Union[str, Path] | None = None,
) -> tuple[nib.Nifti1Image, np.ndarray]:
    """Create a sphere ROI on the grid of ``reference_image``.

    The implementation follows ``TMSsphereROI.m``: coordinates are converted
    through the affine's origin using 1-based matrix indexing.
    """

    img = reference_image if isinstance(reference_image, nib.Nifti1Image) else nib.load(str(reference_image))
    shape = img.shape[:3]
    affine = img.affine
    center = mni_to_mat(np.asarray(center_mni, dtype=float), affine).astype(int)
    vsize = voxel_size(affine)
    radius_voxel = np.maximum(np.round(radius_mm / vsize).astype(int), 1)
    ranges: list[slice] = []
    for axis in range(3):
        lo = max(center[axis] - radius_voxel[axis], 1)
        hi = min(center[axis] + radius_voxel[axis], shape[axis])
        ranges.append(slice(lo - 1, hi))
    grid = np.mgrid[
        ranges[0].start : ranges[0].stop,
        ranges[1].start : ranges[1].stop,
        ranges[2].start : ranges[2].stop,
    ]
    coords = grid + 1.0
    distances = np.sqrt(np.sum(((coords - center[:, None, None, None]) * vsize[:, None, None, None]) ** 2, axis=0))
    mask = np.zeros(shape, dtype=np.float32)
    mask[tuple(slice(r.start, r.stop) for r in ranges)] = (distances <= radius_mm).astype(np.float32)
    if out_path is not None:
        save_volume(mask, img, out_path)
    return img, mask


def extend_roi(mask: np.ndarray, iterations: int = 1) -> np.ndarray:
    """Dilate a binary ROI with a 3x3x3 full-connectivity structuring element."""

    mask = np.asarray(mask, dtype=bool)
    structure = np.ones((3, 3, 3), dtype=bool)
    return ndimage.binary_dilation(mask, structure=structure, iterations=max(int(iterations), 0))


def c6_outbrain_boundary(
    c6_data: np.ndarray,
    c1_to_c5_data: np.ndarray | None = None,
) -> np.ndarray:
    """Build the outer-brain surface mask from SPM's c6 tissue class."""

    c6 = np.asarray(c6_data, dtype=bool)
    if c1_to_c5_data is not None:
        c1_to_c5 = np.asarray(c1_to_c5_data, dtype=bool)
        if c1_to_c5.shape != c6.shape:
            raise ValueError("c6 and c1..c5 images must have the same shape")
        c6[c1_to_c5] = False
    if c6.ndim != 3:
        raise ValueError("Expected a 3D c6 tissue image")
    boundary = c6.copy()
    boundary[0, :, :] = True
    boundary[-1, :, :] = True
    boundary[:, 0, :] = True
    boundary[:, -1, :] = True
    boundary[:, :, 0] = True
    boundary[:, :, -1] = True
    return boundary


def depth_mask(
    target_mask: np.ndarray,
    boundary_mask: np.ndarray,
    max_depth_mm: float,
    affine: np.ndarray,
) -> np.ndarray:
    """Keep target voxels whose nearest boundary distance is within ``max_depth_mm``."""

    target = np.asarray(target_mask, dtype=bool)
    boundary = np.asarray(boundary_mask, dtype=bool)
    if target.shape != boundary.shape:
        raise ValueError("Target and boundary masks must have the same shape")
    distances = ndimage.distance_transform_edt(~boundary, sampling=voxel_size(affine))
    return target & (distances <= float(max_depth_mm))


def individual_target_mask(
    target_image: Union[str, Path, nib.Nifti1Image],
    c6_image: Union[str, Path, nib.Nifti1Image],
    c1_image: Union[str, Path, nib.Nifti1Image] | None = None,
    out_path: Union[str, Path] | None = None,
    *,
    depth_mm: float | None = None,
    extend_iterations: int = 15,
) -> tuple[nib.Nifti1Image, np.ndarray]:
    """Build the individualized target-area mask used by ``TMSSeedFC``.

    The target is resampled to the c6 grid, restricted to grey matter when c1
    is provided, dilated to overlap the outer-brain surface, and optionally
    thresholded by distance to that surface. A ``depth_mm=None`` keeps all
    target voxels and is the safer production default when the scalp distance
    parameter was not part of the study design.
    """

    c6_img = c6_image if isinstance(c6_image, nib.Nifti1Image) else nib.load(str(c6_image))
    _, c6 = load_volume(c6_img)
    _, target = resample_to_grid(target_image, c6_img, order=0)
    c1 = None
    if c1_image is not None:
        _, c1_data = resample_to_grid(c1_image, c6_img, order=1)
        c1 = np.asarray(c1_data, dtype=bool)
    target_area = np.asarray(target, dtype=bool)
    if c1 is not None:
        if c1.shape != target_area.shape:
            raise ValueError("Resampled c1 and target must have the same shape")
        target_area = target_area & c1
    if not target_area.any():
        raise ValueError("Target area is empty after resampling/restriction")
    boundary = c6_outbrain_boundary(np.asarray(c6, dtype=bool), c1)
    enlarged = extend_roi(target_area, extend_iterations)
    outbrain = enlarged & boundary
    if depth_mm is None:
        result = target_area.astype(np.float32)
    else:
        if not outbrain.any():
            raise ValueError("Enlarged target does not overlap the outer-brain surface")
        distances = ndimage.distance_transform_edt(~outbrain, sampling=voxel_size(c6_img.affine))
        result = (target_area & (distances <= float(depth_mm))).astype(np.float32)
    if out_path is not None:
        save_volume(result, c6_img, out_path)
    return c6_img, result


def deep_target(
    tissue_image: Union[str, Path, nib.Nifti1Image],
    center_mni: Union[list, tuple, np.ndarray],
    radius_mm: float = 40.0,
    depth_mm: float = 6.0,
    out_path: Union[str, Path] | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute a deep target from a cortical coordinate and a tissue probability map.

    The original ``TMSDeepTargetComp`` finds the nearest tissue-positive voxel
    inside a sphere, then moves inward along the vector to the supplied MNI
    coordinate. Output order is ``(cortical_coordinate_mni, deep_coordinate_mni)``.
    """

    img = tissue_image if isinstance(tissue_image, nib.Nifti1Image) else nib.load(str(tissue_image))
    tissue = np.asarray(img.dataobj, dtype=float)
    _, sphere = sphere_roi(center_mni, radius_mm, img)
    candidates = tissue * sphere
    positive = candidates > 0
    if not positive.any():
        raise ValueError("No positive tissue voxel was found inside the sphere ROI")
    center_mat = mni_to_mat(np.asarray(center_mni, dtype=float), img.affine)
    coords = np.argwhere(positive) + 1.0
    distances = np.linalg.norm((coords - center_mat) * voxel_size(img.affine), axis=1)
    closest_mat = coords[int(np.argmin(distances))]
    cortical = mat_to_mni(closest_mat, img.affine)
    center = np.asarray(center_mni, dtype=float)
    direction_norm = np.linalg.norm(center - cortical)
    if direction_norm > 0:
        delta = (center - cortical) / direction_norm * depth_mm
        deep = cortical - np.sign(cortical) * delta
    else:
        deep = cortical.copy()
    if out_path is not None:
        Path(out_path).write_text("cortical_mni_x cortical_mni_y cortical_mni_z deep_mni_x deep_mni_y deep_mni_z\n")
        with open(out_path, "a", encoding="utf-8") as handle:
            handle.write(" ".join(f"{v:.6f}" for v in np.hstack([cortical, deep])) + "\n")
    return cortical, deep


__all__ = [
    "c6_outbrain_boundary",
    "deep_target",
    "depth_mask",
    "extend_roi",
    "individual_target_mask",
    "sphere_roi",
]
