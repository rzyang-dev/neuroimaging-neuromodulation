from __future__ import annotations

import os
import shutil

import nibabel as nib
import numpy as np
import pytest

from neuroimaging_neuromodulation.diffusion.external import (
    run_fsl_randomise,
)
from neuroimaging_neuromodulation.wm.design import write_two_group_design

_RUN_EXTERNAL = os.environ.get("NM_RUN_EXTERNAL") == "1"
pytestmark = pytest.mark.skipif(
    not _RUN_EXTERNAL,
    reason="set NM_RUN_EXTERNAL=1 to run optional external-runtime tests",
)


@pytest.mark.skipif(
    shutil.which("design_ttest2") is None or shutil.which("randomise") is None,
    reason="FSL Randomise not installed",
)
def test_fsl_randomise_execution(tmp_path) -> None:
    size = 16
    data = np.zeros((size, size, size, 2), dtype=np.float32)
    data[4:12, 4:12, 4:12, 0] = 1.0
    data[4:12, 4:12, 4:12, 1] = 2.0
    mask = np.zeros((size, size, size), dtype=np.uint8)
    mask[4:12, 4:12, 4:12] = 1
    affine = np.diag([2.0, 2.0, 2.0, 1.0])
    input_path = tmp_path / "merged4d.nii.gz"
    mask_path = tmp_path / "mask.nii.gz"
    nib.Nifti1Image(data, affine).to_filename(input_path)
    nib.Nifti1Image(mask, affine).to_filename(mask_path)
    design = tmp_path / "design"
    write_two_group_design(design, 1, 1)
    assert (tmp_path / "design.mat").exists()
    assert (tmp_path / "design.con").exists()
    result = run_fsl_randomise(
        input_path,
        tmp_path / "diff",
        mask_path,
        tmp_path / "design.mat",
        tmp_path / "design.con",
        n_permutations=10,
    )
    assert result["returncode"] == 0
    assert list(tmp_path.glob("diff_*.nii.gz"))
