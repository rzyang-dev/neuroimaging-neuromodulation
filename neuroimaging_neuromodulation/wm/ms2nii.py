"""Convert tract-profile measures to NIfTI for group-level image analysis."""

from __future__ import annotations

from pathlib import Path

import nibabel as nib
import numpy as np


def _load_profile_matrix(path: str | Path) -> np.ndarray:
    path = Path(path)
    if path.suffix == ".npy":
        data = np.load(path)
    else:
        data = np.loadtxt(path)
    return np.asarray(data, dtype=float)


def tract_measures_to_nifti(
    profile_files: list[str | Path],
    output_dir: str | Path,
    *,
    subject_names: list[str] | None = None,
    n_tracts: int = 18,
    grid_size: int = 100,
    spacing: int = 4,
) -> dict[str, object]:
    """Write per-subject tract-measure NIfTIs, a merged 4D file, and a mask.

    This follows the original ``TractMS2Nii.m`` layout: each tract profile is
    placed along the y axis at fixed x positions on a 100x100x100 grid.
    """

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    if subject_names is None:
        subject_names = [f"subject_{index + 1:02d}" for index in range(len(profile_files))]
    if len(subject_names) != len(profile_files):
        raise ValueError("subject_names must match profile_files")
    if not 0 < n_tracts <= grid_size:
        raise ValueError("n_tracts must be between 1 and grid_size")

    subject_paths: list[Path] = []
    volumes: list[np.ndarray] = []
    for profile_file, subject_name in zip(profile_files, subject_names):
        matrix = _load_profile_matrix(profile_file)
        if matrix.ndim != 2:
            raise ValueError(f"Profile file must be 2D: {profile_file}")
        if matrix.shape[0] == n_tracts and matrix.shape[1] != n_tracts:
            tract_profiles = matrix
        elif matrix.shape[1] == n_tracts:
            tract_profiles = matrix.T
        else:
            raise ValueError(
                f"Profile file must have {n_tracts} tract rows/columns: {profile_file}"
            )
        n_nodes = tract_profiles.shape[1]
        if n_nodes > grid_size:
            raise ValueError("Profile node count exceeds the NIfTI grid size")
        volume = np.zeros((grid_size, grid_size, grid_size), dtype=np.float32)
        for tract_index in range(n_tracts):
            volume[1 + spacing * tract_index, :n_nodes, 0] = tract_profiles[tract_index]
        subject_path = output_dir / f"{subject_name}.nii.gz"
        nib.Nifti1Image(volume, np.eye(4)).to_filename(subject_path)
        subject_paths.append(subject_path)
        volumes.append(volume)

    merged = np.stack(volumes, axis=-1)
    merged_path = output_dir / "merged4d.nii.gz"
    nib.Nifti1Image(merged, np.eye(4)).to_filename(merged_path)

    mask = np.zeros((grid_size, grid_size, grid_size), dtype=np.uint8)
    for tract_index in range(n_tracts):
        mask[1 + spacing * tract_index, :, 0] = 1
    mask_path = output_dir / "mask.nii.gz"
    nib.Nifti1Image(mask, np.eye(4)).to_filename(mask_path)

    subject_list_path = output_dir / "subject_list.txt"
    subject_list_path.write_text(
        "\n".join(str(name) for name in subject_names) + "\n",
        encoding="ascii",
    )
    return {
        "subject_images": subject_paths,
        "merged": merged_path,
        "mask": mask_path,
        "subject_list": subject_list_path,
        "merged_shape": merged.shape,
    }


__all__ = ["tract_measures_to_nifti"]
