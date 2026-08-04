"""Group-level GM/WM mask construction from individual tissue segments."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from ..io.nifti import load_volume, save_volume


def group_probability_maps(
    segment_images: list[str | Path],
    output_path: str | Path,
    *,
    threshold: float = 0.9,
    output_threshold: float | None = None,
) -> tuple[Path, np.ndarray]:
    """Average binarized segment maps and optionally apply a group threshold."""

    if not segment_images:
        raise ValueError("At least one segment image is required")
    reference = None
    binary_stack = []
    for image in segment_images:
        img, data = load_volume(image)
        if data.ndim != 3:
            raise ValueError("Segment images must be 3D")
        binary_stack.append((np.asarray(data, dtype=float) > float(threshold)).astype(float))
        reference = img if reference is None else reference
    probability = np.mean(np.stack(binary_stack, axis=0), axis=0)
    result = probability.copy()
    if output_threshold is not None:
        result = (result >= float(output_threshold)).astype(np.float32)
    path = save_volume(result, reference, output_path)
    return path, result


__all__ = ["group_probability_maps"]
