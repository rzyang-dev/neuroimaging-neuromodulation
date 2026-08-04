from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from neuroimaging_neuromodulation.cli.wm import main
from neuroimaging_neuromodulation.io.nifti import load_volume, resample_to_grid, save_volume
from neuroimaging_neuromodulation.targets.roi import sphere_roi
from neuroimaging_neuromodulation.wm.alff import compute_alff
from neuroimaging_neuromodulation.wm.dynamic import dynamic_alff
from neuroimaging_neuromodulation.wm.group import group_probability_maps
from neuroimaging_neuromodulation.wm.masks import make_wm_mask
from neuroimaging_neuromodulation.wm.seedfc import wm_multi_seed_fc, wm_seed_fc
from neuroimaging_neuromodulation.wm.tracts import cluster_report_in_jhu


def test_alff_real_data(real_fmri_path: Path | None, real_fmri_available: bool, package_data_dir: Path, tmp_path: Path) -> None:
    if not real_fmri_available:
        pytest.skip("real fMRI data not available")
    func_img = __import__("nibabel").load(real_fmri_path)
    _, mask = resample_to_grid(package_data_dir / "BrainMask_05_61x73x61.nii", func_img, order=0)
    save_volume(mask, func_img, tmp_path / "mask.nii")
    paths = compute_alff(
        real_fmri_path,
        tmp_path / "mask.nii",
        tmp_path / "alff",
        tr=2.0,
        low_cutoff=0.01,
        high_cutoff=0.1,
    )
    assert all(path.exists() for path in paths.values())
    _, alff = load_volume(paths["ALFF"])
    assert np.isfinite(alff).all()
    assert (alff > 0).sum() > 0


def test_make_wm_mask_real_data(real_fmri_path: Path | None, real_fmri_available: bool, package_data_dir: Path, tmp_path: Path) -> None:
    if not real_fmri_available:
        pytest.skip("real fMRI data not available")
    path, mask = make_wm_mask(
        real_fmri_path,
        package_data_dir / "white.nii",
        package_data_dir / "excludHOAsub25prob617361.nii",
        tmp_path,
        threshold=0.9,
    )
    assert path.exists()
    assert mask.dtype == np.float32
    assert mask.sum() > 0


def test_wm_seed_fc_real_data(
    real_fmri_path: Path | None,
    real_fmri_available: bool,
    package_data_dir: Path,
    tmp_path: Path,
) -> None:
    if not real_fmri_available:
        pytest.skip("real fMRI data not available")
    func_img = __import__("nibabel").load(real_fmri_path)
    _, seed = resample_to_grid(package_data_dir / "BrainMask_05_61x73x61.nii", func_img, order=0)
    save_volume(seed, func_img, tmp_path / "seed.nii")
    _, mask = resample_to_grid(package_data_dir / "WhiteMask_09_61x73x61.nii", func_img, order=0)
    save_volume(mask, func_img, tmp_path / "mask.nii")
    path, z_map = wm_seed_fc(
        real_fmri_path,
        tmp_path / "seed.nii",
        tmp_path / "mask.nii",
        output_path=tmp_path / "zFCmap.nii",
    )
    assert path.exists()
    assert z_map.shape == func_img.shape[:3]
    assert np.isfinite(z_map[z_map != 0]).all()


def test_wm_multi_seed_fc_real_data(
    real_fmri_path: Path | None,
    real_fmri_available: bool,
    package_data_dir: Path,
    tmp_path: Path,
) -> None:
    if not real_fmri_available:
        pytest.skip("real fMRI data not available")
    func_img = __import__("nibabel").load(real_fmri_path)
    _, seed = resample_to_grid(package_data_dir / "BrainMask_05_61x73x61.nii", func_img, order=0)
    save_volume(seed, func_img, tmp_path / "seed-a.nii")
    save_volume(seed, func_img, tmp_path / "seed-b.nii")
    _, mask = resample_to_grid(package_data_dir / "WhiteMask_09_61x73x61.nii", func_img, order=0)
    save_volume(mask, func_img, tmp_path / "mask.nii")
    results = wm_multi_seed_fc(
        real_fmri_path,
        [tmp_path / "seed-a.nii", tmp_path / "seed-b.nii"],
        tmp_path / "mask.nii",
        output_dir=tmp_path / "out",
    )
    assert set(results) == {"seed-a", "seed-b"}
    assert all(path.exists() for path, _ in results.values())


def test_cluster_report_in_jhu(package_data_dir: Path, tmp_path: Path) -> None:
    template = package_data_dir / "JHUtractsThr25_3mm.nii"
    _, _ = sphere_roi([0.0, 0.0, 0.0], 10.0, template, tmp_path / "result.nii")
    report = cluster_report_in_jhu(
        tmp_path / "result.nii",
        template,
        tmp_path / "out",
    )
    assert report.exists()
    content = report.read_text(encoding="utf-8")
    assert len(content.splitlines()) == 20


def test_dynamic_alff_real_data(real_fmri_path: Path | None, real_fmri_available: bool, package_data_dir: Path, tmp_path: Path) -> None:
    if not real_fmri_available:
        pytest.skip("real fMRI data not available")
    func_img = __import__("nibabel").load(real_fmri_path)
    _, mask = resample_to_grid(package_data_dir / "BrainMask_05_61x73x61.nii", func_img, order=0)
    save_volume(mask, func_img, tmp_path / "mask.nii")
    result = dynamic_alff(
        real_fmri_path,
        tmp_path / "mask.nii",
        tmp_path / "out",
        tr=2.0,
        window_length=20,
        step=20,
    )
    assert Path(result["dALFF"]).exists()
    assert len(result["windows"]) >= 7
    assert all(path.exists() for path in result["windows"])


def test_group_probability_maps(package_data_dir: Path, tmp_path: Path) -> None:
    segment = package_data_dir / "white.nii"
    output, result = group_probability_maps(
        [segment, segment],
        tmp_path / "prob.nii",
        threshold=0.9,
        output_threshold=1.0,
    )
    assert output.exists()
    assert set(np.unique(result)) <= {0.0, 1.0}


def test_randomise_cli_dry_run(tmp_path: Path) -> None:
    assert (
        main(
            [
                "randomise",
                "--input",
                str(tmp_path / "merged4d.nii.gz"),
                "--mask",
                str(tmp_path / "mask.nii.gz"),
                "--output-prefix",
                str(tmp_path / "diff"),
                "--n-group1",
                "3",
                "--n-group2",
                "4",
                "--n-permutations",
                "100",
                "--dry-run",
            ]
        )
        == 0
    )
