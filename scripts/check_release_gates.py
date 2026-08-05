"""Release-gate checks for metadata, dependencies, and required docs."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def main() -> int:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    init = (ROOT / "neuroimaging_neuromodulation" / "__init__.py").read_text(
        encoding="utf-8"
    )
    pyproject_version = re.search(r'^version = "([^"]+)"', pyproject, re.MULTILINE)
    init_version = re.search(r'^__version__ = "([^"]+)"', init, re.MULTILINE)
    if not pyproject_version or not init_version:
        _fail("version is missing from pyproject.toml or package __init__")
    if pyproject_version.group(1) != init_version.group(1):
        _fail("pyproject.toml and package __init__ versions disagree")

    core_section = pyproject.split("[project.optional-dependencies]", 1)[0]
    for optional in ("nilearn", "dipy", "dicom2nifti", "pydicom"):
        if optional in core_section:
            _fail(f"{optional} must not be a core dependency")

    required_docs = (
        "docs/gap-matrix.md",
        "docs/roadmap.md",
        "docs/production-readiness.md",
        "docs/porting-status.md",
        "docs/testing.md",
    )
    for doc in required_docs:
        if not (ROOT / doc).exists():
            _fail(f"required document is missing: {doc}")

    print("OK: release gates passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
