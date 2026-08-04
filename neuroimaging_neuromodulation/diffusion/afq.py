"""Subject-level AFQ-style tract analysis pipeline."""

from __future__ import annotations

from pathlib import Path

import nibabel as nib
import numpy as np

from .outliers import remove_fiber_outliers
from .roi_segmentation import segment_streamlines_by_rois
from .segmentation import segment_streamlines_by_atlas
from .tract_profile import tract_profile


def afq_subject_pipeline(
    streamlines: list[np.ndarray],
    atlas_image: str | Path | nib.Nifti1Image,
    scalar_image: str | Path | nib.Nifti1Image,
    *,
    n_samples: int = 50,
    num_nodes: int = 30,
    max_dist: float = 4.0,
    max_len: float = 4.0,
    segmentation: str = "atlas",
    roi_dir: str | Path | None = None,
    tract_atlas: str | Path | nib.Nifti1Image | None = None,
    min_dist: float = 2.0,
) -> dict[str, object]:
    """Segment, clean, and profile a subject's streamlines by atlas label."""

    if segmentation == "roi":
        if roi_dir is None or tract_atlas is None:
            raise ValueError("roi segmentation requires roi_dir and tract_atlas")
        segmentation_result = segment_streamlines_by_rois(
            streamlines,
            roi_dir,
            atlas_image=tract_atlas,
            min_dist=min_dist,
            n_samples=n_samples,
        )
    elif segmentation == "atlas":
        segmentation_result = segment_streamlines_by_atlas(
            streamlines,
            atlas_image,
            n_samples=n_samples,
        )
    else:
        raise ValueError("segmentation must be 'atlas' or 'roi'")
    labels = np.asarray(segmentation_result["labels"])
    results = []
    for label in sorted(set(int(value) for value in labels if int(value) > 0)):
        group = [streamline for streamline, tract_label in zip(streamlines, labels) if int(tract_label) == label]
        cleaned, keep = remove_fiber_outliers(
            group,
            max_dist=max_dist,
            max_len=max_len,
            num_nodes=num_nodes,
            max_iter=5,
        )
        if cleaned:
            profile_result = tract_profile(
                cleaned,
                scalar_image,
                n_points=num_nodes,
            )
            profile = np.asarray(profile_result["profile"], dtype=float)
            std = np.asarray(profile_result["std"], dtype=float)
        else:
            profile = np.full(num_nodes, np.nan, dtype=float)
            std = np.full(num_nodes, np.nan, dtype=float)
        results.append(
            {
                "label": int(label),
                "input_streamlines": len(group),
                "output_streamlines": int(keep.sum()),
                "profile": profile,
                "std": std,
            }
        )
    return {
        "n_streamlines": len(streamlines),
        "tracts": results,
    }


__all__ = ["afq_subject_pipeline"]
