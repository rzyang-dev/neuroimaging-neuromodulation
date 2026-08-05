from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_core_dependencies_do_not_require_optional_libraries() -> None:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    core_section = text.split("[project.optional-dependencies]", 1)[0]
    for optional in ("nilearn", "dipy", "dicom2nifti", "pydicom"):
        assert optional not in core_section, f"{optional} must not be a core dependency"
    assert "numpy>=1.24" in core_section
    assert "scipy>=1.10" in core_section
    assert "nibabel>=5.0" in core_section


def test_optional_extras_are_declared() -> None:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    for extra in ("core = []", "dicom = [", "diffusion = [", "demo = [", "all = ["):
        assert extra in text
