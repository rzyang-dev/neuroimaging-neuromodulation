"""NIfTI input/output helpers."""

from .deformations import apply_deformation, deformation_coordinates, identity_deformation
from .dicom import (
    convert_dicom_directory,
    convert_dicom_series,
    convert_dicom_series_by_index,
    inspect_dicom_directory,
    validate_dicom_series,
)
from .nifti import (
    load_4d_matrix,
    load_4d_matrix_dir,
    load_volume,
    resample_to_grid,
    save_volume,
    write_text_as_nifti,
)

__all__ = [
    "apply_deformation",
    "convert_dicom_directory",
    "convert_dicom_series",
    "convert_dicom_series_by_index",
    "inspect_dicom_directory",
    "deformation_coordinates",
    "identity_deformation",
    "load_4d_matrix",
    "load_4d_matrix_dir",
    "load_volume",
    "resample_to_grid",
    "save_volume",
    "validate_dicom_series",
    "write_text_as_nifti",
]
