from __future__ import annotations

from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def package_data_dir() -> Path:
    return ROOT / "neuroimaging_neuromodulation" / "data"


@pytest.fixture
def real_fmri_path() -> Path | None:
    root = ROOT / "data" / "real_development_fmri"
    candidates = sorted(
        path
        for path in root.rglob("*.nii.gz")
        if not path.name.startswith("._") and "AppleDouble" not in str(path)
    )
    return candidates[0] if candidates else None


@pytest.fixture
def real_fmri_available(real_fmri_path: Path | None) -> bool:
    return real_fmri_path is not None
