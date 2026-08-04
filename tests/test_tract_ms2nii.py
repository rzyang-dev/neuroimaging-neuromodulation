from __future__ import annotations

import nibabel as nib
import numpy as np

from neuroimaging_neuromodulation.cli.wm import main
from neuroimaging_neuromodulation.wm.ms2nii import tract_measures_to_nifti


def test_tract_measures_to_nifti(tmp_path) -> None:
    rng = np.random.default_rng(4)
    profiles = []
    for subject_index in range(2):
        matrix = 1.0 + subject_index + 0.1 * rng.normal(size=(100, 18))
        path = tmp_path / f"subject_{subject_index + 1}.npy"
        np.save(path, matrix)
        profiles.append(path)
    result = tract_measures_to_nifti(
        profiles,
        tmp_path / "out",
        subject_names=["s1", "s2"],
        n_tracts=18,
    )
    merged_img = nib.load(result["merged"])
    assert merged_img.shape == (100, 100, 100, 2)
    mask_data = np.asanyarray(nib.load(result["mask"]).dataobj)
    assert mask_data.sum() == 18 * 100
    assert (tmp_path / "out" / "s1.nii.gz").exists()
    assert (tmp_path / "out" / "subject_list.txt").read_text(encoding="ascii").splitlines() == ["s1", "s2"]


def test_tract_ms2nii_cli(tmp_path) -> None:
    rng = np.random.default_rng(5)
    path = tmp_path / "profile.txt"
    np.savetxt(path, rng.normal(size=(18, 100)))
    output = tmp_path / "cli_out"
    assert main(
        [
            "tract-ms2nii",
            "--profiles",
            str(path),
            "--subject-names",
            "subject_a",
            "--n-tracts",
            "18",
            "--output-dir",
            str(output),
        ]
    ) == 0
    assert (output / "merged4d.nii.gz").exists()
    assert (output / "mask.nii.gz").exists()
