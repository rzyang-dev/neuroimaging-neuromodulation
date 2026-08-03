"""ALFF/fALFF computation from the original white-matter toolbox."""

from __future__ import annotations

from pathlib import Path

import nibabel as nib
import numpy as np
from scipy import fft, signal

from ..io.nifti import load_4d_matrix, load_volume, save_volume


def _next_pow2(n: int) -> int:
    return int(2 ** np.ceil(np.log2(max(n, 1))))


def compute_alff_2d(
    data: np.ndarray,
    tr: float,
    low_cutoff: float,
    high_cutoff: float,
    mask: np.ndarray | None = None,
    *,
    chunk_size: int = 100000,
) -> dict[str, np.ndarray]:
    """Compute ALFF, zALFF, mALFF, fALFF, zfALFF, and mfALFF.

    ``data`` has shape ``(n_timepoints, n_voxels)``. If ``mask`` is omitted,
    all voxels are used. The returned arrays are zero-filled full-length maps.
    """

    data = np.asarray(data, dtype=float)
    if data.ndim != 2:
        raise ValueError(f"Expected 2D data, got {data.shape}")
    n_time, n_voxels = data.shape
    if mask is None:
        mask = np.ones(n_voxels, dtype=bool)
    else:
        mask = np.asarray(mask, dtype=bool).reshape(-1)
        if mask.size != n_voxels:
            raise ValueError("Mask length does not match voxel count")
    selected = np.flatnonzero(mask)
    if selected.size == 0:
        raise ValueError("Mask is empty")

    sample_freq = 1.0 / float(tr)
    padded_length = _next_pow2(n_time)
    if low_cutoff >= sample_freq / 2:
        idx_low = padded_length // 2 + 1
    else:
        idx_low = int(np.ceil(low_cutoff * padded_length * tr + 1))
    if high_cutoff >= sample_freq / 2 or high_cutoff == 0:
        idx_high = padded_length // 2 + 1
    else:
        idx_high = int(np.trunc(high_cutoff * padded_length * tr + 1))
    if idx_low > idx_high:
        raise ValueError("Band lower cutoff exceeds upper cutoff")

    alff = np.zeros(n_voxels, dtype=np.float64)
    falff = np.zeros(n_voxels, dtype=np.float64)
    for start in range(0, selected.size, chunk_size):
        end = min(start + chunk_size, selected.size)
        segment = data[:, selected[start:end]]
        segment = signal.detrend(segment, axis=0)
        padded = np.vstack([segment, np.zeros((padded_length - n_time, segment.shape[1]))])
        spectrum = fft.fft(padded, axis=0)
        amplitude = 2.0 * np.abs(spectrum) / n_time
        band = amplitude[idx_low - 1 : idx_high, :]
        alff[selected[start:end]] = np.mean(band, axis=0)
        full_band = amplitude[1 : padded_length // 2 + 1, :]
        with np.errstate(divide="ignore", invalid="ignore"):
            ratio = np.sum(band, axis=0) / np.sum(full_band, axis=0)
        falff[selected[start:end]] = np.where(np.isfinite(ratio), ratio, 0.0)

    mask_values = alff[mask]
    mean_alff = np.mean(mask_values)
    std_alff = np.std(mask_values)
    z_alff = np.zeros_like(alff)
    m_alff = np.zeros_like(alff)
    if mean_alff != 0 and np.isfinite(mean_alff):
        z_alff[mask] = (alff[mask] - mean_alff) / std_alff
        m_alff[mask] = alff[mask] / mean_alff

    mask_falff = falff[mask]
    mean_falff = np.mean(mask_falff)
    std_falff = np.std(mask_falff)
    z_falff = np.zeros_like(falff)
    m_falff = np.zeros_like(falff)
    if mean_falff != 0 and np.isfinite(mean_falff):
        z_falff[mask] = (falff[mask] - mean_falff) / std_falff
        m_falff[mask] = falff[mask] / mean_falff

    return {
        "ALFF": alff,
        "zALFF": z_alff,
        "mALFF": m_alff,
        "fALFF": falff,
        "zfALFF": z_falff,
        "mfALFF": m_falff,
    }


def compute_alff(
    functional_image: str | Path,
    mask_image: str | Path,
    output_dir: str | Path,
    *,
    tr: float,
    low_cutoff: float = 0.01,
    high_cutoff: float = 0.1,
    prefix: str = "ALFF",
) -> dict[str, Path]:
    """Compute ALFF/fALFF for a 4D NIfTI and write the result maps."""

    func_img, func_matrix = load_4d_matrix(functional_image)
    _, mask_data = load_volume(mask_image)
    mask = np.asarray(mask_data, dtype=bool).reshape(-1)
    if mask.size != func_matrix.shape[0]:
        raise ValueError("Mask does not match functional image grid")
    maps = compute_alff_2d(
        func_matrix.T,
        tr=tr,
        low_cutoff=low_cutoff,
        high_cutoff=high_cutoff,
        mask=mask,
    )
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    shape = func_img.shape[:3]
    paths: dict[str, Path] = {}
    default_names = {
        "ALFF": f"{prefix}.nii",
        "zALFF": f"z{prefix}.nii",
        "mALFF": f"m{prefix}.nii",
        "fALFF": f"f{prefix}.nii",
        "zfALFF": f"zf{prefix}.nii",
        "mfALFF": f"mf{prefix}.nii",
    }
    for name, values in maps.items():
        filename = default_names.get(name, f"{prefix}{name}.nii")
        paths[name] = save_volume(values.reshape(shape), func_img, output_dir / filename)
    return paths


__all__ = ["compute_alff", "compute_alff_2d"]
