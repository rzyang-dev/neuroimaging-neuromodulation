"""DICOM conversion through the pure-Python dicom2nifti library."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path


def inspect_dicom_directory(dicom_directory: str | Path) -> dict[str, object]:
    """Summarize DICOM series metadata without reading pixel data."""

    try:
        from pydicom import dcmread
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "pydicom is required for DICOM inspection. Install the optional "
            "extra with `.venv/bin/python -m pip install "
            "neuroimaging-neuromodulation[dicom]`."
        ) from exc

    dicom_directory = Path(dicom_directory)
    series: dict[tuple[str, str], dict[str, object]] = {}
    total = 0
    for path in sorted(dicom_directory.rglob("*")):
        if not path.is_file():
            continue
        try:
            dataset = dcmread(path, stop_before_pixels=True)
        except Exception:
            continue
        total += 1
        uid = str(dataset.get("SeriesInstanceUID", ""))
        number = str(dataset.get("SeriesNumber", ""))
        key = (uid, number)
        entry = series.setdefault(
            key,
            {
                "series_uid": uid,
                "series_number": number,
                "modality": str(dataset.get("Modality", "")),
                "series_description": str(dataset.get("SeriesDescription", "")),
                "manufacturer": str(dataset.get("Manufacturer", "")),
                "patient_id": str(dataset.get("PatientID", "")),
                "number_of_files": 0,
                "rows": dataset.get("Rows"),
                "columns": dataset.get("Columns"),
                "slice_thickness": dataset.get("SliceThickness"),
                "pixel_spacing": list(dataset.get("PixelSpacing", [])) if dataset.get("PixelSpacing") else None,
                "files": [],
            },
        )
        entry["number_of_files"] = int(entry["number_of_files"]) + 1
        entry["files"].append(str(path))
    if total == 0:
        raise RuntimeError(f"No readable DICOM files found in {dicom_directory}")
    return {
        "dicom_directory": str(dicom_directory),
        "dicom_file_count": total,
        "series_count": len(series),
        "series": sorted(series.values(), key=lambda item: str(item["series_number"])),
    }


def validate_dicom_series(dicom_directory: str | Path) -> dict[str, object]:
    """Return series metadata only when the directory contains one DICOM series."""

    summary = inspect_dicom_directory(dicom_directory)
    if summary["series_count"] != 1:
        raise RuntimeError(
            f"Expected exactly one DICOM series, found {summary['series_count']}"
        )
    series = summary["series"][0]
    if series["number_of_files"] < 1:
        raise RuntimeError("DICOM series contains no readable files")
    return series


def convert_dicom_directory(
    dicom_directory: str | Path,
    output_directory: str | Path,
    *,
    compression: bool = True,
    reorient: bool = True,
) -> list[Path]:
    """Convert every DICOM series in a directory to NIfTI files."""

    try:
        from dicom2nifti import convert_directory
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "dicom2nifti is required for DICOM conversion. Install it with "
            "`.venv/bin/python -m pip install dicom2nifti`."
        ) from exc

    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    convert_directory(
        str(dicom_directory),
        str(output_directory),
        compression=compression,
        reorient=reorient,
    )
    return sorted(path for path in output_directory.rglob("*") if path.is_file())


def convert_dicom_series(
    dicom_directory: str | Path,
    output_file: str | Path | None = None,
    *,
    reorient: bool = True,
) -> dict[str, object]:
    """Convert a single DICOM series and return the result metadata."""

    try:
        from dicom2nifti import dicom_series_to_nifti
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "dicom2nifti is required for DICOM conversion. Install it with "
            "`.venv/bin/python -m pip install dicom2nifti`."
        ) from exc

    result = dicom_series_to_nifti(
        str(dicom_directory),
        output_file=str(output_file) if output_file is not None else None,
        reorient_nifti=reorient,
    )
    return result


def convert_dicom_series_by_index(
    dicom_directory: str | Path,
    series_index: int,
    output_file: str | Path,
    *,
    reorient: bool = True,
) -> dict[str, object]:
    """Convert one DICOM series from a mixed directory by series index."""

    summary = inspect_dicom_directory(dicom_directory)
    series = summary["series"]
    if not 0 <= int(series_index) < len(series):
        raise ValueError(
            f"series_index must be between 0 and {len(series) - 1}, got {series_index}"
        )
    files = [Path(path) for path in series[int(series_index)]["files"]]
    if not files:
        raise RuntimeError("Selected DICOM series contains no readable files")
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="nm-dicom-series-") as temp_dir:
        copied = []
        for index, source in enumerate(sorted(files)):
            target = Path(temp_dir) / f"{index:06d}.dcm"
            shutil.copy2(source, target)
            copied.append(target)
        return convert_dicom_series(temp_dir, output_file, reorient=reorient)


__all__ = [
    "convert_dicom_directory",
    "convert_dicom_series",
    "convert_dicom_series_by_index",
    "inspect_dicom_directory",
    "validate_dicom_series",
]
