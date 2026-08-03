from __future__ import annotations

from pathlib import Path

import nibabel as nib
import numpy as np

from neuroimaging_neuromodulation.io.deformations import identity_deformation
from neuroimaging_neuromodulation.targets.cluster import largest_cluster
from neuroimaging_neuromodulation.targets.pipeline import seed_based_fc, target_site
from neuroimaging_neuromodulation.targets.roi import (
    deep_target,
    extend_roi,
    individual_target_mask,
    sphere_roi,
)


def test_sphere_roi_on_real_template(package_data_dir: Path) -> None:
    reference = package_data_dir / "BrainMask_05_61x73x61.nii"
    img, mask = sphere_roi([0.0, 0.0, 0.0], 5.0, reference)
    assert img.shape == (61, 73, 61)
    assert mask.sum() > 0
    center = np.unravel_index(np.argmax(mask), mask.shape)
    assert np.allclose(center, (29, 41, 23), atol=1)


def test_extend_roi_dilates() -> None:
    mask = np.zeros((10, 10, 10), dtype=bool)
    mask[5, 5, 5] = True
    extended = extend_roi(mask, iterations=2)
    assert extended.sum() > mask.sum()


def test_largest_cluster() -> None:
    data = np.zeros((10, 10, 10))
    data[3:6, 3:6, 3:6] = 0.5
    data[8, 8, 8] = 0.8
    mask, size = largest_cluster(data, 0.05, 20, "Positive")
    assert size == 27
    assert mask.sum() == 27


def test_deep_target_on_real_gm(package_data_dir: Path) -> None:
    cortical, deep = deep_target(
        package_data_dir / "grey.nii",
        [0.0, 0.0, 0.0],
        radius_mm=20.0,
        depth_mm=6.0,
    )
    assert cortical.shape == (3,)
    assert deep.shape == (3,)
    assert np.isfinite(deep).all()


def test_individual_target_mask_real_templates(package_data_dir: Path, tmp_path: Path) -> None:
    _, _ = sphere_roi(
        [0.0, 0.0, 0.0],
        10.0,
        package_data_dir / "grey333.nii",
        tmp_path / "target.nii",
    )
    img, result = individual_target_mask(
        tmp_path / "target.nii",
        package_data_dir / "BrainMask_05_61x73x61.nii",
        package_data_dir / "grey333.nii",
        tmp_path / "targetmask.nii",
        depth_mm=None,
    )
    assert img.shape == (61, 73, 61)
    assert result.sum() > 0
    assert (tmp_path / "targetmask.nii").exists()


def test_seed_fc_on_real_data(real_fmri_path: Path | None, real_fmri_available: bool, tmp_path: Path) -> None:
    if not real_fmri_available:
        return
    func_img = nib.load(real_fmri_path)
    _, seed = sphere_roi([0.0, 0.0, 0.0], 8.0, func_img, tmp_path / "seed.nii")
    _, mask = sphere_roi([0.0, 0.0, 0.0], 18.0, func_img, tmp_path / "mask.nii")
    result = seed_based_fc(
        real_fmri_path,
        tmp_path / "seed.nii",
        tmp_path / "mask.nii",
        tmp_path / "fc",
        subject="test",
    )
    assert result["SeedFCinWB"].exists()
    assert result["SeedFCinROI"].exists()
    assert np.isfinite(result["r_values"]).all()


def test_seed_fc_accepts_identity_deformation(real_fmri_path: Path | None, real_fmri_available: bool, tmp_path: Path) -> None:
    if not real_fmri_available:
        return
    func_img = nib.load(real_fmri_path)
    _, seed = sphere_roi([0.0, 0.0, 0.0], 8.0, func_img, tmp_path / "seed.nii")
    _, mask = sphere_roi([0.0, 0.0, 0.0], 18.0, func_img, tmp_path / "mask.nii")
    _, _ = identity_deformation(func_img, tmp_path / "identity_def.nii")
    result = seed_based_fc(
        real_fmri_path,
        tmp_path / "seed.nii",
        tmp_path / "mask.nii",
        tmp_path / "fc_def",
        subject="test",
        seed_deformation=tmp_path / "identity_def.nii",
        mask_deformation=tmp_path / "identity_def.nii",
    )
    assert result["SeedFCinWB"].exists()
    assert np.isfinite(result["r_values"]).all()


def test_target_site_on_real_fc(real_fmri_path: Path | None, real_fmri_available: bool, tmp_path: Path) -> None:
    if not real_fmri_available:
        return
    func_img = nib.load(real_fmri_path)
    _, seed = sphere_roi([0.0, 0.0, 0.0], 8.0, func_img, tmp_path / "seed.nii")
    _, mask = sphere_roi([0.0, 0.0, 0.0], 18.0, func_img, tmp_path / "mask.nii")
    result = seed_based_fc(
        real_fmri_path,
        tmp_path / "seed.nii",
        tmp_path / "mask.nii",
        tmp_path / "fc",
        subject="test",
    )
    sites = target_site(
        result["SeedFCinROI"],
        tmp_path / "targets",
        subject="test",
        posneg=["Positive", "Negative"],
        p_value=0.05,
        n_samples=168,
    )
    assert len(sites) == 2
