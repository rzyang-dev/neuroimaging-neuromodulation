from __future__ import annotations

import os
from pathlib import Path

import pytest

from neuroimaging_neuromodulation.validation.spm import (
    find_spm25,
    validate_coreg_against_spm,
)

_RUN_EXTERNAL = os.environ.get("NM_RUN_EXTERNAL") == "1"
pytestmark = pytest.mark.skipif(
    not _RUN_EXTERNAL,
    reason="set NM_RUN_EXTERNAL=1 to run optional external-runtime tests",
)


@pytest.mark.skipif(find_spm25() is None, reason="SPM25 standalone not installed")
def test_spm_coreg_reference_on_real_fmri(
    real_fmri_path: Path | None,
    real_fmri_available: bool,
    tmp_path: Path,
) -> None:
    if not real_fmri_available:
        pytest.skip("real fMRI data not available")
    result = validate_coreg_against_spm(
        real_fmri_path,
        tmp_path / "spm_coreg",
        timeout=1800,
    )
    assert result["n_cases"] == 4
    assert min(result["aligned_correlations"]) > 0.5
    assert max(result["aligned_mae"]) < 0.15
    assert min(result["warped_correlations"]) > 0.9
