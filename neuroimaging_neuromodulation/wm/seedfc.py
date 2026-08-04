"""White-matter seed-based functional connectivity from the original toolbox."""

from __future__ import annotations

from pathlib import Path

import nibabel as nib
import numpy as np

from ..io.nifti import load_4d_matrix, resample_to_grid, save_volume
from ..stats.functional import fast_corr


def _seed_signal(func_matrix: np.ndarray, seed_data: np.ndarray) -> np.ndarray:
    seed_flat = np.asarray(seed_data, dtype=float).reshape(-1)
    if seed_flat.size != func_matrix.shape[0]:
        raise ValueError("Seed does not match functional grid")
    positive = seed_flat > 0
    if not positive.any():
        raise ValueError("Seed mask is empty after resampling")
    signal = np.mean(func_matrix[positive, :] * seed_flat[positive, None], axis=0)
    signal = np.where(np.isfinite(signal), signal, 0.0)
    return signal


def wm_seed_fc(
    functional_image: str | Path,
    seed_image: str | Path,
    mask_image: str | Path,
    output_path: str | Path | None = None,
) -> tuple[Path | None, np.ndarray]:
    """Compute white-matter seed FC and return the Fisher z-transformed map."""

    func_img, func_matrix = load_4d_matrix(functional_image)
    if func_matrix.shape[1] < 3:
        raise ValueError("Functional data must contain at least three timepoints")

    seed_img, seed_data = resample_to_grid(seed_image, func_img, order=0)
    _, mask_data = resample_to_grid(mask_image, func_img, order=0)
    seed_flat = np.asarray(seed_data, dtype=float).reshape(-1)
    mask_flat = np.asarray(mask_data, dtype=bool).reshape(-1)
    if seed_flat.size != func_matrix.shape[0] or mask_flat.size != func_matrix.shape[0]:
        raise ValueError("Seed or mask does not match functional grid")
    if not mask_flat.any():
        raise ValueError("Analysis mask is empty after resampling")

    signal = _seed_signal(func_matrix, seed_flat)
    r_values = fast_corr(signal[:, None], func_matrix[mask_flat, :].T).ravel()
    z_values = np.arctanh(np.clip(r_values, -1 + 1e-12, 1 - 1e-12))
    z_map = np.zeros(func_matrix.shape[0], dtype=np.float32)
    z_map[mask_flat] = z_values

    path = None
    if output_path is not None:
        path = save_volume(z_map.reshape(func_img.shape[:3]), func_img, output_path)
    return path, z_map.reshape(func_img.shape[:3])


def wm_multi_seed_fc(
    functional_image: str | Path,
    seed_images: list[str | Path],
    mask_image: str | Path,
    output_dir: str | Path | None = None,
) -> dict[str, tuple[Path | None, np.ndarray]]:
    """Run white-matter seed FC for multiple seeds and write one map per seed."""

    results: dict[str, tuple[Path | None, np.ndarray]] = {}
    output_dir = Path(output_dir) if output_dir is not None else None
    for seed_image in seed_images:
        seed_path = Path(seed_image)
        name = seed_path.name
        for suffix in (".nii.gz", ".nii"):
            if name.endswith(suffix):
                name = name[: -len(suffix)]
                break
        output_path = None
        if output_dir is not None:
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{name}_zFCmap.nii"
        path, z_map = wm_seed_fc(
            functional_image,
            seed_image,
            mask_image,
            output_path=output_path,
        )
        results[name] = (path, z_map)
    return results


__all__ = ["wm_multi_seed_fc", "wm_seed_fc"]
