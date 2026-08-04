"""Dynamic ALFF workflows matching the original ``dyALFF`` script."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from ..io.nifti import load_4d_matrix, load_volume, save_volume
from .alff import compute_alff_2d


def dynamic_alff(
    functional_image: str | Path,
    mask_image: str | Path,
    output_dir: str | Path,
    *,
    tr: float,
    low_cutoff: float = 0.01,
    high_cutoff: float = 0.1,
    window_length: int = 50,
    step: int = 5,
) -> dict[str, object]:
    """Compute sliding-window mean ALFF and the across-window variability map."""

    func_img, func_matrix = load_4d_matrix(functional_image)
    if func_matrix.shape[1] < window_length:
        raise ValueError("Functional data has fewer timepoints than the window length")
    _, mask_data = load_volume(mask_image)
    mask = np.asarray(mask_data, dtype=bool).reshape(-1)
    if mask.size != func_matrix.shape[0]:
        raise ValueError("Mask does not match functional grid")
    if not mask.any():
        raise ValueError("Mask is empty")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    starts = list(range(0, func_matrix.shape[1] - window_length + 1, max(int(step), 1)))
    if not starts:
        raise ValueError("No windows fit inside the functional series")

    window_paths: list[Path] = []
    m_alff_stack: list[np.ndarray] = []
    for start in starts:
        window = func_matrix[:, start : start + window_length].T
        maps = compute_alff_2d(
            window,
            tr=tr,
            low_cutoff=low_cutoff,
            high_cutoff=high_cutoff,
            mask=mask,
        )
        m_alff = maps["mALFF"]
        m_alff_stack.append(m_alff)
        path = output_dir / f"mALFF_{start:04d}.nii"
        save_volume(m_alff.reshape(func_img.shape[:3]), func_img, path)
        window_paths.append(path)

    stack = np.stack(m_alff_stack, axis=0)
    d_alff = np.zeros(m_alff.shape, dtype=np.float32)
    d_alff[mask] = np.std(stack[:, mask], axis=0)
    d_path = output_dir / "dALFF.nii"
    save_volume(d_alff.reshape(func_img.shape[:3]), func_img, d_path)
    return {"dALFF": d_path, "windows": window_paths}


__all__ = ["dynamic_alff"]
