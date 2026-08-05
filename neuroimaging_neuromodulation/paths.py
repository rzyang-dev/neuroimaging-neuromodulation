"""Frozen/runtime-aware package path helpers."""

from __future__ import annotations

import sys
from pathlib import Path


def package_dir() -> Path:
    """Return the package directory in normal and PyInstaller-frozen runs."""

    if getattr(sys, "frozen", False):
        meipass = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
        candidate = meipass / "neuroimaging_neuromodulation"
        if candidate.is_dir():
            return candidate
        return meipass
    return Path(__file__).resolve().parent


def package_data_dir() -> Path:
    """Return the bundled data directory in normal and frozen runs."""

    base = package_dir()
    candidates = (
        base / "data",
        Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent)) / "data",
    )
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return base / "data"


__all__ = ["package_data_dir", "package_dir"]
