"""Optional wrappers around FSL and MRtrix binaries.

These functions do not install or emulate external tools. They check for the
binary, build the command from real inputs, and fail with clear instructions
when the external dependency is absent.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def require_binary(name: str, hint: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise RuntimeError(f"{name} was not found. {hint}")
    return path


def check_external_tools() -> dict[str, dict[str, object]]:
    """Report availability and paths for supported external binaries."""

    tools = {
        "bedpostx": "FSL bedpostx",
        "dtifit": "FSL dtifit",
        "probtrackx2": "FSL probtrackx2",
        "tckgen": "MRtrix3 tckgen",
    }
    result: dict[str, dict[str, object]] = {}
    for binary, label in tools.items():
        path = shutil.which(binary)
        result[binary] = {
            "label": label,
            "available": path is not None,
            "path": path,
        }
    return result


def build_fsl_bedpostx_command(bedpostx_dir: str | Path) -> list[str]:
    return ["bedpostx", str(bedpostx_dir)]


def build_fsl_dtifit_command(
    dwi: str | Path,
    mask: str | Path,
    bvec: str | Path,
    bval: str | Path,
    output_prefix: str | Path,
) -> list[str]:
    return [
        "dtifit",
        "-k",
        str(dwi),
        "-o",
        str(output_prefix),
        "-m",
        str(mask),
        "-r",
        str(bvec),
        "-b",
        str(bval),
    ]


def build_fsl_probtrackx_command(
    seed: str | Path,
    target: str | Path,
    bedpostx_dir: str | Path,
    output_dir: str | Path,
    *,
    samples: int = 5000,
    steps: int = 2000,
) -> list[str]:
    bedpostx_dir = Path(bedpostx_dir)
    merged = bedpostx_dir / "merged"
    mask = bedpostx_dir / "nodif_brain_mask"
    return [
        "probtrackx2",
        "-x",
        str(seed),
        "-l",
        "--onewaycondition",
        "-c",
        "0.2",
        "-S",
        str(steps),
        "--steplength=0.5",
        "-P",
        str(samples),
        "--fibthresh=0.01",
        "--distthresh=0.0",
        "--sampvox=0.0",
        "--forcedir",
        "--opd",
        "-s",
        str(merged),
        "-m",
        str(mask),
        "--dir",
        str(output_dir),
        "--waypoints",
        str(target),
        "--waycond",
        "AND",
    ]


def build_mrtrix_tckgen_command(
    dwi: str | Path,
    mask: str | Path,
    output: str | Path,
    *,
    algorithm: str = "iFOD2",
    num_tracks: int = 100000,
) -> list[str]:
    return [
        "tckgen",
        "-algorithm",
        algorithm,
        "-select",
        str(num_tracks),
        "-mask",
        str(mask),
        str(dwi),
        str(output),
    ]


def _run(cmd: list[str]) -> dict[str, object]:
    binary = cmd[0]
    require_binary(binary, f"Install {binary} and add it to PATH before using this command.")
    completed = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(
            f"{binary} failed with exit code {completed.returncode}: {completed.stderr.strip()}"
        )
    return {
        "command": cmd,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def run_fsl_bedpostx(bedpostx_dir: str | Path) -> dict[str, object]:
    return _run(build_fsl_bedpostx_command(bedpostx_dir))


def run_fsl_dtifit(
    dwi: str | Path,
    mask: str | Path,
    bvec: str | Path,
    bval: str | Path,
    output_prefix: str | Path,
) -> dict[str, object]:
    return _run(build_fsl_dtifit_command(dwi, mask, bvec, bval, output_prefix))


def run_fsl_probtrackx(
    seed: str | Path,
    target: str | Path,
    bedpostx_dir: str | Path,
    output_dir: str | Path,
    *,
    samples: int = 5000,
    steps: int = 2000,
) -> dict[str, object]:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    return _run(build_fsl_probtrackx_command(seed, target, bedpostx_dir, output_dir, samples=samples, steps=steps))


def run_mrtrix_tckgen(
    dwi: str | Path,
    mask: str | Path,
    output: str | Path,
    *,
    algorithm: str = "iFOD2",
    num_tracks: int = 100000,
) -> dict[str, object]:
    return _run(build_mrtrix_tckgen_command(dwi, mask, output, algorithm=algorithm, num_tracks=num_tracks))


__all__ = [
    "build_fsl_bedpostx_command",
    "build_fsl_dtifit_command",
    "build_fsl_probtrackx_command",
    "build_mrtrix_tckgen_command",
    "check_external_tools",
    "run_fsl_bedpostx",
    "run_fsl_dtifit",
    "run_fsl_probtrackx",
    "run_mrtrix_tckgen",
]
