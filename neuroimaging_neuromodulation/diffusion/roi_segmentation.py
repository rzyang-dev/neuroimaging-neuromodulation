"""ROI-based AFQ streamline segmentation using the Mori/JHU templates."""

from __future__ import annotations

from pathlib import Path

import nibabel as nib
import numpy as np
from scipy import ndimage, spatial

from ..io.nifti import load_volume
from .tract_profile import _resample_streamline


TRACT_ROI_FILES = [
    ("ATR_roi1_L.nii.gz", "ATR_roi2_L.nii.gz"),
    ("ATR_roi1_R.nii.gz", "ATR_roi2_R.nii.gz"),
    ("CST_roi1_L.nii.gz", "CST_roi2_L.nii.gz"),
    ("CST_roi1_R.nii.gz", "CST_roi2_R.nii.gz"),
    ("CGC_roi1_L.nii.gz", "CGC_roi2_L.nii.gz"),
    ("CGC_roi1_R.nii.gz", "CGC_roi2_R.nii.gz"),
    ("HCC_roi1_L.nii.gz", "HCC_roi2_L.nii.gz"),
    ("HCC_roi1_R.nii.gz", "HCC_roi2_R.nii.gz"),
    ("FP_L.nii.gz", "FP_R.nii.gz"),
    ("FA_L.nii.gz", "FA_R.nii.gz"),
    ("IFO_roi1_L.nii.gz", "IFO_roi2_L.nii.gz"),
    ("IFO_roi1_R.nii.gz", "IFO_roi2_R.nii.gz"),
    ("ILF_roi1_L.nii.gz", "ILF_roi2_L.nii.gz"),
    ("ILF_roi1_R.nii.gz", "ILF_roi2_R.nii.gz"),
    ("SLF_roi1_L.nii.gz", "SLF_roi2_L.nii.gz"),
    ("SLF_roi1_R.nii.gz", "SLF_roi2_R.nii.gz"),
    ("UNC_roi1_L.nii.gz", "UNC_roi2_L.nii.gz"),
    ("UNC_roi1_R.nii.gz", "UNC_roi2_R.nii.gz"),
    ("SLF_roi1_L.nii.gz", "SLFt_roi2_L.nii.gz"),
    ("SLF_roi1_R.nii.gz", "SLFt_roi2_R.nii.gz"),
]


def _world_coordinates(img: nib.Nifti1Image, mask: np.ndarray) -> np.ndarray:
    voxels = np.argwhere(mask).astype(float)
    if voxels.size == 0:
        return np.empty((0, 3), dtype=float)
    ones = np.ones((len(voxels), 1), dtype=float)
    return (img.affine @ np.hstack([voxels, ones]).T).T[:, :3]


def _passes_roi(
    nodes: np.ndarray,
    roi_img: nib.Nifti1Image,
    roi_data: np.ndarray,
    min_dist: float,
) -> bool:
    centers = _world_coordinates(roi_img, roi_data > 0)
    if len(centers) == 0:
        return False
    tree = spatial.cKDTree(centers)
    distances, _ = tree.query(nodes, k=1)
    return bool(np.any(distances <= float(min_dist)))


def _atlas_probabilities(
    atlas_img: nib.Nifti1Image,
    atlas_data: np.ndarray,
    nodes: np.ndarray,
) -> np.ndarray:
    inv_affine = np.linalg.inv(atlas_img.affine)
    voxel = inv_affine @ np.column_stack([nodes, np.ones(len(nodes), dtype=float)]).T
    values = []
    for tract in range(atlas_data.shape[3]):
        sampled = ndimage.map_coordinates(
            atlas_data[..., tract],
            voxel[:3, :],
            order=1,
            mode="constant",
            cval=0.0,
        )
        values.append(float(np.mean(sampled)))
    return np.asarray(values, dtype=float)


def segment_streamlines_by_rois(
    streamlines: list[np.ndarray],
    roi_dir: str | Path,
    *,
    atlas_image: str | Path | None = None,
    min_dist: float = 2.0,
    n_samples: int = 50,
) -> dict[str, object]:
    """Assign streamlines to JHU tracts using both waypoint ROIs and atlas scores."""

    roi_dir = Path(roi_dir)
    roi_images = []
    for roi1_name, roi2_name in TRACT_ROI_FILES:
        roi1_img, roi1_data = load_volume(roi_dir / roi1_name)
        roi2_img, roi2_data = load_volume(roi_dir / roi2_name)
        roi_images.append((roi1_img, roi1_data, roi2_img, roi2_data))

    atlas_img = None
    atlas_data = None
    if atlas_image is not None:
        atlas_img, atlas_data = load_volume(atlas_image)
        if atlas_data.ndim != 4 or atlas_data.shape[3] != len(TRACT_ROI_FILES):
            raise ValueError(
                f"atlas_image must be a 4D NIfTI with {len(TRACT_ROI_FILES)} tract probabilities"
            )

    labels: list[int] = []
    for streamline in streamlines:
        nodes = _resample_streamline(streamline, n_samples)
        if nodes is None:
            labels.append(0)
            continue
        candidates = []
        for tract_index, (roi1_img, roi1_data, roi2_img, roi2_data) in enumerate(roi_images):
            if _passes_roi(nodes, roi1_img, roi1_data, min_dist) and _passes_roi(
                nodes, roi2_img, roi2_data, min_dist
            ):
                candidates.append(tract_index + 1)
        if not candidates:
            labels.append(0)
            continue
        if atlas_data is None:
            labels.append(candidates[0])
        else:
            scores = _atlas_probabilities(atlas_img, atlas_data, nodes)
            labels.append(max(candidates, key=lambda index: scores[index - 1]))

    counts: dict[str, int] = {}
    for label in sorted(set(labels)):
        counts[str(label)] = int(labels.count(label))
    return {"n_streamlines": len(streamlines), "labels": labels, "counts": counts}


__all__ = ["segment_streamlines_by_rois"]
