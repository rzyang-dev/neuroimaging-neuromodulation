"""NIfTI loading, saving, and resampling utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Union

import nibabel as nib
import numpy as np

ImageLike = Union[str, Path, nib.spatialimages.SpatialImage]


def load_volume(path: ImageLike) -> tuple[nib.Nifti1Image, np.ndarray]:
    """Load a NIfTI file and return the image object plus its data array.

    The data array is returned as a plain NumPy array so downstream code can
    mutate it without affecting lazy file-backed arrays.
    """

    if isinstance(path, nib.spatialimages.SpatialImage):
        img = path
    else:
        img = nib.load(str(path))
    data = np.asanyarray(img.dataobj)
    return img, data


def load_4d_matrix(path: ImageLike) -> tuple[nib.Nifti1Image, np.ndarray]:
    """Load a 4D NIfTI as a matrix with shape ``(n_voxels, n_timepoints)``.

    This matches the convention used by the original MATLAB toolbox, where
    functional volumes are flattened along spatial dimensions before analysis.
    """

    img, data = load_volume(path)
    if data.ndim not in (3, 4):
        raise ValueError(f"Expected a 3D or 4D NIfTI image, got shape {data.shape}")
    matrix = data.reshape(-1, data.shape[-1]) if data.ndim == 4 else data.reshape(-1, 1)
    return img, matrix


def _reference_for_3d_source(source: nib.Nifti1Image, target: nib.Nifti1Image) -> nib.Nifti1Image:
    """Return a 3D reference when a 3D source is resampled to a 4D target."""

    if source.ndim == 3 and target.ndim == 4:
        return nib.Nifti1Image(np.zeros(target.shape[:3], dtype=np.float32), target.affine)
    return target


def resample_to_grid(
    source: ImageLike,
    target: ImageLike,
    order: int = 0,
) -> tuple[nib.Nifti1Image, np.ndarray]:
    """Resample ``source`` onto the world-space grid of ``target``.

    ``order=0`` is nearest-neighbor and is used when preserving binary masks.
    ``order=1`` is trilinear interpolation and is used for continuous images.
    """

    from nibabel.processing import resample_from_to

    source_img = source if isinstance(source, nib.spatialimages.SpatialImage) else nib.load(str(source))
    target_img = target if isinstance(target, nib.spatialimages.SpatialImage) else nib.load(str(target))
    target_ref = _reference_for_3d_source(source_img, target_img)
    resampled = resample_from_to(
        source_img,
        target_ref,
        order=order,
        mode="constant",
        cval=0.0,
    )
    return resampled, np.asanyarray(resampled.dataobj)


def save_volume(
    data: np.ndarray,
    reference: ImageLike,
    out_path: Union[str, Path],
    *,
    dtype: np.dtype | None = None,
) -> Path:
    """Save ``data`` to ``out_path`` using the affine/header of ``reference``."""

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ref = reference if isinstance(reference, nib.spatialimages.SpatialImage) else nib.load(str(reference))
    out_data = np.asarray(data)
    if out_data.dtype.kind not in "fiu":
        out_data = out_data.astype(np.float32)
    if dtype is not None:
        out_data = out_data.astype(dtype)
    out_data = np.squeeze(out_data) if out_data.ndim == 4 and out_data.shape[3] == 1 else out_data
    header = ref.header.copy()
    if hasattr(header, "set_slope_inter"):
        header.set_slope_inter(1.0, 0.0)
    img = nib.Nifti1Image(out_data, ref.affine, header=header)
    img.set_data_dtype(np.float32 if dtype is None else dtype)
    img.to_filename(str(out_path))
    return out_path
