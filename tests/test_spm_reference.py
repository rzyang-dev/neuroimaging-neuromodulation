from __future__ import annotations

import os
from pathlib import Path

import pytest

from neuroimaging_neuromodulation.validation.spm import (
    find_spm25,
    validate_spm_deformation_convention,
)

_RUN_EXTERNAL = os.environ.get("NM_RUN_EXTERNAL") == "1"
pytestmark = pytest.mark.skipif(
    not _RUN_EXTERNAL,
    reason="set NM_RUN_EXTERNAL=1 to run optional external-runtime tests",
)


@pytest.mark.skipif(find_spm25() is None, reason="SPM25 standalone not installed")
def test_spm_deformation_convention_on_real_template(tmp_path: Path, package_data_dir: Path) -> None:
    t1 = package_data_dir / "ch2.nii"
    result = validate_spm_deformation_convention(t1, tmp_path / "spm", timeout=1800)
    assert Path(result["iy_field"]).exists()
    assert Path(result["y_field"]).exists()
    assert Path(result["rc1"]).exists()
    assert Path(result["rc2"]).exists()
    assert Path(result["rc3"]).exists()
    assert result["metrics"]["correlation"] > 0.8
