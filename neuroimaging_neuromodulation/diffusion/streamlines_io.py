"""NumPy/NiBabel streamline I/O without DIPY."""

from __future__ import annotations

from pathlib import Path

import nibabel as nib
import numpy as np


def load_tract_streamlines(
    track_path: str | Path,
    _reference_image: str | Path | nib.Nifti1Image | None = None,
) -> list[np.ndarray]:
    """Load TRK/TCK streamlines with NiBabel's native streamlines support."""

    tractogram = nib.streamlines.load(str(track_path))
    return [np.asarray(streamline, dtype=float) for streamline in tractogram.streamlines]


def save_tract_streamlines(
    streamlines: list[np.ndarray],
    reference_image: str | Path | nib.Nifti1Image,
    output_path: str | Path,
) -> Path:
    """Save streamlines as TRK with NiBabel, using the reference affine."""

    reference = reference_image if isinstance(reference_image, nib.Nifti1Image) else nib.load(str(reference_image))
    output_path = Path(output_path)
    tractogram = nib.streamlines.Tractogram(
        [np.asarray(streamline, dtype=float) for streamline in streamlines],
        affine_to_rasmm=reference.affine,
    )
    nib.streamlines.save(tractogram, str(output_path))
    return output_path


__all__ = ["load_tract_streamlines", "save_tract_streamlines"]
