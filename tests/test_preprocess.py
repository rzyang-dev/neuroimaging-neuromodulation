from __future__ import annotations

from pathlib import Path

import nibabel as nib
import numpy as np

from neuroimaging_neuromodulation.cli.preprocess import main
from neuroimaging_neuromodulation.io.nifti import load_volume
from neuroimaging_neuromodulation.preprocess.imaging import flip_left_right
from neuroimaging_neuromodulation.preprocess.spatial import smooth_volume


def test_smooth_real_mask(package_data_dir: Path) -> None:
    img, data = load_volume(package_data_dir / "BrainMask_05_61x73x61.nii")
    smoothed = smooth_volume(data, 4.0, img.affine)
    assert smoothed.shape == data.shape
    assert np.isfinite(smoothed).all()
    assert (smoothed > 0).sum() > (data > 0).sum()


def test_flip_left_right_real_mask(package_data_dir: Path) -> None:
    img, data = load_volume(package_data_dir / "BrainMask_05_61x73x61.nii")
    flipped = flip_left_right(data)
    assert flipped.shape == data.shape
    assert np.array_equal(flipped[::-1], data)


def test_combine_images_cli(package_data_dir: Path, tmp_path: Path) -> None:
    a = package_data_dir / "BrainMask_05_61x73x61.nii"
    b = package_data_dir / "WhiteMask_09_61x73x61.nii"
    output = tmp_path / "combined.nii"
    assert main(["combine-images", "--images", str(a), str(b), "--output", str(output), "--operation", "sum"]) == 0
    _, data = load_volume(output)
    assert data.shape == (61, 73, 61)
    assert (data > 0).sum() > 0


def test_merge_images_cli(package_data_dir: Path, tmp_path: Path) -> None:
    _, a = load_volume(package_data_dir / "BrainMask_05_61x73x61.nii")
    _, b = load_volume(package_data_dir / "WhiteMask_09_61x73x61.nii")
    nib.Nifti1Image(np.stack([a, b], axis=-1), np.eye(4)).to_filename(tmp_path / "a.nii")
    nib.Nifti1Image(np.stack([b, a], axis=-1), np.eye(4)).to_filename(tmp_path / "b.nii")
    output = tmp_path / "merged.nii"
    assert main(["merge-images", "--images", str(tmp_path / "a.nii"), str(tmp_path / "b.nii"), "--output", str(output)]) == 0
    _, merged = load_volume(output)
    assert merged.shape == (61, 73, 61, 4)


def test_reslice_cli(package_data_dir: Path, tmp_path: Path) -> None:
    output = tmp_path / "resliced.nii"
    assert main(
        [
            "reslice",
            "--source",
            str(package_data_dir / "BrainMask_05_61x73x61.nii"),
            "--sample",
            str(package_data_dir / "grey333.nii"),
            "--output",
            str(output),
            "--order",
            "0",
        ]
    ) == 0
    _, data = load_volume(output)
    assert data.shape == (61, 73, 61)


def test_text_to_nifti_cli(tmp_path: Path) -> None:
    text = tmp_path / "data.txt"
    text.write_text("\n".join(str(i) for i in range(8)), encoding="utf-8")
    output = tmp_path / "data.nii"
    assert main(["text-to-nifti", "--text", str(text), "--output", str(output), "--shape", "2,2,2"]) == 0
    _, data = load_volume(output)
    assert data.shape == (2, 2, 2)
