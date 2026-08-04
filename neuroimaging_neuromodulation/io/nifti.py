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


def load_4d_matrix_dir(directory: Union[str, Path]) -> tuple[nib.Nifti1Image, np.ndarray]:
    """Load 3D NIfTI files from a directory and stack them into a matrix.

    This mirrors the original ``TMSReadNii`` directory mode.
    """

    directory = Path(directory)
    paths = sorted(
        path
        for path in directory.rglob("*.nii*")
        if path.is_file()
        and not path.name.startswith("._")
        and "AppleDouble" not in str(path)
    )
    if not paths:
        raise ValueError(f"No NIfTI files found in {directory}")
    img = nib.load(str(paths[0]))
    volumes = []
    for path in paths:
        data = np.asanyarray(nib.load(str(path)).dataobj)
        if data.ndim == 4:
            for t in range(data.shape[3]):
                volumes.append(data[..., t])
        elif data.ndim == 3:
            volumes.append(data)
        else:
            raise ValueError(f"Expected 3D/4D NIfTI, got shape {data.shape}")
    stacked = np.stack(volumes, axis=-1)
    return img, stacked.reshape(-1, stacked.shape[-1])


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


def write_text_as_nifti(
    text_path: Union[str, Path],
    output_path: Union[str, Path],
    shape: tuple[int, int, int],
    reference: ImageLike | None = None,
    *,
    dtype: np.dtype | type = np.int16,
) -> Path:
    """Write a text array as a NIfTI image, matching the original txt2nii flow."""

    values = np.loadtxt(text_path).reshape(shape)
    output_path = Path(output_path)
    if reference is None:
        reference = nib.Nifti1Image(np.zeros(shape, dtype=np.float32), np.eye(4))
    return save_volume(values.astype(dtype), reference, output_path, dtype=dtype)
