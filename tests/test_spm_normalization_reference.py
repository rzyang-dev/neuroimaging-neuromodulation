from __future__ import annotations

from pathlib import Path

import pytest

from neuroimaging_neuromodulation.validation.spm import (
    find_spm25,
    validate_normalization_against_spm,
)


@pytest.mark.skipif(find_spm25() is None, reason="SPM25 standalone not installed")
def test_spm_normalization_reference_on_real_templates(
    tmp_path: Path,
    package_data_dir: Path,
) -> None:
    result = validate_normalization_against_spm(
        package_data_dir / "grey.nii",
        package_data_dir / "white.nii",
        tmp_path / "norm",
        timeout=1800,
    )
    assert min(result["correlations"]) > 0.99
    assert max(result["mae"]) < 5.0
    assert max(result["rmse"]) < 5.0
