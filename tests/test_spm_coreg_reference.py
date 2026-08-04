from __future__ import annotations

from pathlib import Path

import pytest

from neuroimaging_neuromodulation.validation.spm import (
    find_spm25,
    validate_coreg_against_spm,
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
