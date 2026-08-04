"""Python-native FSL design file generation for two-group Randomise."""

from __future__ import annotations

from pathlib import Path


def write_two_group_design(
    output_prefix: str | Path,
    n_group1: int,
    n_group2: int,
) -> tuple[Path, Path]:
    """Write FSL ``design.mat`` and ``design.con`` for a two-group t-test."""

    if n_group1 <= 0 or n_group2 <= 0:
        raise ValueError("Group sizes must be positive")
    total = n_group1 + n_group2
    mat_path = Path(f"{output_prefix}.mat")
    con_path = Path(f"{output_prefix}.con")
    mat_path.parent.mkdir(parents=True, exist_ok=True)
    rows = ["1 0"] * n_group1 + ["0 1"] * n_group2
    mat_path.write_text(
        "/NumWaves 2\n"
        f"/NumPoints {total}\n"
        "/PPheights 1 1\n"
        "/Matrix\n"
        + "\n".join(rows)
        + "\n",
        encoding="ascii",
    )
    con_path.write_text(
        "/NumWaves 2\n"
        "/NumContrasts 2\n"
        "/PPheights 1 1\n"
        "/Matrix\n"
        "1 -1\n"
        "-1 1\n",
        encoding="ascii",
    )
    return mat_path, con_path


__all__ = ["write_two_group_design"]
