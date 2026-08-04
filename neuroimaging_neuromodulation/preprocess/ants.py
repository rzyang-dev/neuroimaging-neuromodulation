"""Optional ANTs normalization command builders and runners."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def build_ants_registration_command(
    moving: str | Path,
    fixed: str | Path,
    output_prefix: str | Path,
    *,
    dimensionality: int = 3,
    stages: tuple[str, ...] = ("rigid", "affine", "syn"),
) -> list[str]:
    """Build an ANTs registration command for rigid/affine/SyN normalization."""

    cmd = [
        "antsRegistration",
        "--dimensionality",
        str(dimensionality),
        "--output",
        f"[{output_prefix},{output_prefix}Warped.nii.gz]",
        "--use-histogram-matching",
        "1",
        "--initial-moving-transform",
        f"[{fixed},{moving},1]",
    ]
    stage_commands = {
        "rigid": [
            "--transform",
            "Rigid[0.1]",
            "--metric",
            f"MI[{fixed},{moving},1,32,Regular,0.25]",
            "--convergence",
            "[1000x500x250x100,1e-6,10]",
            "--smoothing-sigmas",
            "4x2x1x0vox",
            "--shrink-factors",
            "8x4x2x1",
        ],
        "affine": [
            "--transform",
            "Affine[0.1]",
            "--metric",
            f"MI[{fixed},{moving},1,32,Regular,0.25]",
            "--convergence",
            "[1000x500x250x100,1e-6,10]",
            "--smoothing-sigmas",
            "4x2x1x0vox",
            "--shrink-factors",
            "8x4x2x1",
        ],
        "syn": [
            "--transform",
            "SyN[0.1,3,0]",
            "--metric",
            f"CC[{fixed},{moving},1,4]",
            "--convergence",
            "[100x70x50x20,1e-6,10]",
            "--smoothing-sigmas",
            "4x2x1x0vox",
            "--shrink-factors",
            "8x4x2x1",
        ],
    }
    for stage in stages:
        if stage not in stage_commands:
            raise ValueError(f"Unsupported ANTs stage: {stage}")
        cmd.extend(stage_commands[stage])
    return cmd


def build_ants_apply_transform_command(
    input_image: str | Path,
    reference_image: str | Path,
    output_image: str | Path,
    transforms: list[str | Path],
    *,
    interpolation: str = "Linear",
) -> list[str]:
    """Build an antsApplyTransforms command."""

    cmd = [
        "antsApplyTransforms",
        "-d",
        "3",
        "-i",
        str(input_image),
        "-r",
        str(reference_image),
        "-o",
        str(output_image),
        "-n",
        interpolation,
    ]
    for transform in transforms:
        cmd.extend(["-t", str(transform)])
    return cmd


def build_ants_apply_transforms_to_points_command(
    input_csv: str | Path,
    output_csv: str | Path,
    transforms: list[str | Path],
    *,
    dimensionality: int = 3,
    use_inverse: int = 1,
    transform_inverse: list[int] | None = None,
) -> list[str]:
    """Build an antsApplyTransformsToPoints command for streamline points."""

    cmd = [
        "antsApplyTransformsToPoints",
        "-d",
        str(dimensionality),
        "-i",
        str(input_csv),
        "-o",
        str(output_csv),
    ]
    if transform_inverse is not None and len(transform_inverse) != len(transforms):
        raise ValueError("transform_inverse must match transforms")
    for index, transform in enumerate(transforms):
        inverse = transform_inverse[index] if transform_inverse is not None else use_inverse
        cmd += ["-t", f"[{transform},{inverse}]"]
    return cmd


def check_ants_tools() -> dict[str, dict[str, object]]:
    """Report ANTs binary availability."""

    return {
        name: {
            "available": shutil.which(name) is not None,
            "path": shutil.which(name),
        }
        for name in ("antsRegistration", "antsApplyTransforms", "antsApplyTransformsToPoints")
    }


def _run(cmd: list[str]) -> dict[str, object]:
    binary = cmd[0]
    if shutil.which(binary) is None:
        raise RuntimeError(f"{binary} was not found. Install ANTs and add it to PATH.")
    completed = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"{binary} failed: {completed.stderr.strip()}")
    return {
        "command": cmd,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def run_ants_registration(
    moving: str | Path,
    fixed: str | Path,
    output_prefix: str | Path,
    **kwargs: object,
) -> dict[str, object]:
    return _run(build_ants_registration_command(moving, fixed, output_prefix, **kwargs))


def run_ants_apply_transform(
    input_image: str | Path,
    reference_image: str | Path,
    output_image: str | Path,
    transforms: list[str | Path],
    **kwargs: object,
) -> dict[str, object]:
    return _run(
        build_ants_apply_transform_command(
            input_image,
            reference_image,
            output_image,
            transforms,
            **kwargs,
        )
    )


def run_ants_apply_transforms_to_points(
    input_csv: str | Path,
    output_csv: str | Path,
    transforms: list[str | Path],
    **kwargs: object,
) -> dict[str, object]:
    return _run(
        build_ants_apply_transforms_to_points_command(
            input_csv,
            output_csv,
            transforms,
            **kwargs,
        )
    )


__all__ = [
    "build_ants_apply_transform_command",
    "build_ants_apply_transforms_to_points_command",
    "build_ants_registration_command",
    "check_ants_tools",
    "run_ants_apply_transform",
    "run_ants_apply_transforms_to_points",
    "run_ants_registration",
]
