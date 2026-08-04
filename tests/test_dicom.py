from __future__ import annotations

from pathlib import Path

import nibabel as nib
import pytest

pytest.importorskip("dicom2nifti")

from neuroimaging_neuromodulation.io.dicom import (  # noqa: E402
    convert_dicom_directory,
    convert_dicom_series,
    convert_dicom_series_by_index,
    inspect_dicom_directory,
    validate_dicom_series,
)


def test_convert_real_dicom_series(tmp_path: Path) -> None:
    output = tmp_path / "series.nii"
    result = convert_dicom_series("data/real_dicom/hitachi", output)
    path = Path(result["NII_FILE"])
    assert path.exists()
    img = nib.load(path)
    assert img.ndim == 3
    assert all(dim > 0 for dim in img.shape)


def test_convert_real_dicom_directory(tmp_path: Path) -> None:
    output_dir = tmp_path / "out"
    files = convert_dicom_directory("data/real_dicom/hitachi", output_dir, compression=True)
    assert files
    assert any(path.suffix == ".gz" for path in files)


def test_convert_dicom_series_by_index(tmp_path: Path) -> None:
    output = tmp_path / "selected.nii"
    result = convert_dicom_series_by_index("data/real_dicom/hitachi", 0, output)
    assert Path(result["NII_FILE"]).exists()


def test_inspect_real_dicom_directory(tmp_path: Path) -> None:
    summary = inspect_dicom_directory("data/real_dicom/hitachi")
    assert summary["dicom_file_count"] == 4
    assert summary["series_count"] == 1
    assert summary["series"][0]["modality"] == "MR"


def test_validate_real_dicom_series() -> None:
    series = validate_dicom_series("data/real_dicom/hitachi")
    assert series["number_of_files"] == 4


def test_validate_empty_dicom_directory(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="No readable DICOM"):
        validate_dicom_series(tmp_path)


@pytest.mark.parametrize("vendor", ["generic", "ge", "philips", "siemens", "hyperfine", "hitachi"])
def test_vendor_dicom_inspect_and_convert(vendor: str, tmp_path: Path) -> None:
    dicom_dir = Path("data/real_dicom") / vendor
    summary = inspect_dicom_directory(dicom_dir)
    assert summary["series_count"] == 1
    assert summary["series"][0]["modality"] == "MR"
    output = tmp_path / f"{vendor}.nii"
    result = convert_dicom_series(dicom_dir, output)
    assert Path(result["NII_FILE"]).exists()


@pytest.mark.parametrize(
    "variant",
    [
        "compressed_jpeg",
        "compressed_j2k",
        "compressed_rle",
        "compressed_jpegls",
        "siemens_multiframe",
        "philips_enhanced",
    ],
)
def test_compressed_and_multiframe_dicom(variant: str, tmp_path: Path) -> None:
    dicom_dir = Path("data/real_dicom") / variant
    summary = inspect_dicom_directory(dicom_dir)
    assert summary["series_count"] == 1
    output = tmp_path / f"{variant}.nii"
    result = convert_dicom_series(dicom_dir, output)
    assert Path(result["NII_FILE"]).exists()
