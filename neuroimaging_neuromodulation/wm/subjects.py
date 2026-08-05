"""Subject directory validation utilities."""

from __future__ import annotations

import json
from pathlib import Path


def _subject_names(directory: Path) -> list[str]:
    return sorted(
        path.name
        for path in directory.iterdir()
        if path.is_dir() and not path.name.startswith((".", "_"))
    )


def compare_subject_names(
    t1_directory: str | Path,
    functional_directory: str | Path,
    output_json: str | Path | None = None,
) -> dict[str, object]:
    """Compare subject folder names between T1 and functional directories."""

    t1 = Path(t1_directory)
    functional = Path(functional_directory)
    if not t1.is_dir():
        raise ValueError(f"T1 directory does not exist: {t1}")
    if not functional.is_dir():
        raise ValueError(f"Functional directory does not exist: {functional}")
    t1_names = _subject_names(t1)
    fun_names = _subject_names(functional)
    t1_only = sorted(set(t1_names) - set(fun_names))
    fun_only = sorted(set(fun_names) - set(t1_names))
    result = {
        "t1_directory": str(t1),
        "functional_directory": str(functional),
        "t1_subject_count": len(t1_names),
        "functional_subject_count": len(fun_names),
        "matched_subject_count": len(set(t1_names) & set(fun_names)),
        "t1_only": t1_only,
        "functional_only": fun_only,
        "matched": t1_names == fun_names,
    }
    if output_json is not None:
        path = Path(output_json)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


__all__ = ["compare_subject_names"]
