from __future__ import annotations

from pathlib import Path

import pytest

from neuroimaging_neuromodulation.validation.spm import (
    find_spm25,
    validate_motion_against_spm,
)


@pytest.mark.skipif(find_spm25() is None, reason="SPM25 standalone not installed")
def test_spm_motion_reference_on_real_fmri(
    real_fmri_path: Path | None,
    real_fmri_available: bool,
    tmp_path: Path,
) -> None:
    if not real_fmri_available:
        pytest.skip("real fMRI data not available")
    result = validate_motion_against_spm(
        real_fmri_path,
        tmp_path / "spm_motion",
        n_volumes=4,
        timeout=1800,
    )
    assert result["returncode"] == 0
    assert min(result["aligned_correlations"]) > 0.5
    assert max(result["aligned_mae"]) < 0.02
