"""MNI region-center utilities for target and QC workflows."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy import ndimage

from ..io.nifti import load_volume


def image_region_centers(
    image_path: str | Path,
    output_json: str | Path | None = None,
    *,
    min_voxels: int = 1,
) -> list[dict[str, object]]:
    """Return center-of-mass coordinates for each positive region in an image."""

    img, data = load_volume(image_path)
    if data.ndim != 3:
        raise ValueError(f"Region-center input must be 3D, got shape {data.shape}")
    binary = np.asarray(data) > 0
    labeled, count = ndimage.label(binary)
    centers: list[dict[str, object]] = []
    for index in range(1, count + 1):
        mask = labeled == index
        voxel_count = int(mask.sum())
        if voxel_count < min_voxels:
            continue
        voxel_center = np.asarray(ndimage.center_of_mass(binary, labeled, index), dtype=float)
        world = img.affine @ np.array([*voxel_center, 1.0], dtype=float)
        centers.append(
            {
                "label": index,
                "voxels": voxel_count,
                "center_voxel_0based": voxel_center.tolist(),
                "center_mni": world[:3].tolist(),
            }
        )
    if output_json is not None:
        path = Path(output_json)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(centers, indent=2), encoding="utf-8")
    return centers


__all__ = ["image_region_centers"]
