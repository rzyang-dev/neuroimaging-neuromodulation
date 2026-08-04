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
    seed_image: str | Path | None = None,
) -> list[str]:
    cmd = [
        "tckgen",
        "-algorithm",
        algorithm,
        "-select",
        str(num_tracks),
    ]
    if seed_image is not None:
        cmd += ["-seed_image", str(seed_image)]
    cmd += ["-mask", str(mask), str(dwi), str(output)]
    return cmd


def build_fsl_bet_command(
    input_image: str | Path,
    output_image: str | Path,
    *,
    robust: bool = True,
    zero_gradient: bool = True,
    no_ss: bool = True,
    mask: bool = True,
) -> list[str]:
    """Build the FSL BET command used by the original ``TMSBET.sh``."""

    cmd = ["bet", str(input_image), str(output_image)]
    if robust:
        cmd.append("-F")
    if zero_gradient:
        cmd.append("-g")
        cmd.append("0")
    if no_ss:
        cmd.append("-n")
    if mask:
        cmd.append("-m")
    return cmd


def build_fsl_eddy_correct_command(
    input_image: str | Path,
    output_image: str | Path,
    reference_volume: int = 0,
) -> list[str]:
    """Build the legacy FSL eddy_correct command from ``TMSEddyCorr.sh``."""

    return ["eddy_correct", str(input_image), str(output_image), str(reference_volume)]


def build_fsl_flirt_command(
    input_image: str | Path,
    reference_image: str | Path,
    output_image: str | Path | None = None,
    *,
    init_matrix: str | Path | None = None,
    apply_xfm: bool = False,
    out_matrix: str | Path | None = None,
) -> list[str]:
    """Build an FSL FLIRT command for FA-to-T1 or native/MNI transforms."""

    cmd = [
        "flirt",
        "-in",
        str(input_image),
        "-ref",
        str(reference_image),
    ]
    if output_image is not None:
        cmd += ["-out", str(output_image)]
    if init_matrix is not None:
        cmd += ["-init", str(init_matrix)]
    if apply_xfm:
        cmd.append("-applyxfm")
    if out_matrix is not None:
        cmd += ["-omat", str(out_matrix)]
    return cmd


def build_fsl_convert_xfm_command(
    input_matrix: str | Path,
    output_matrix: str | Path,
    *,
    inverse: bool = False,
) -> list[str]:
    cmd = ["convert_xfm"]
    if inverse:
        cmd.append("-inverse")
    cmd += ["-omat", str(output_matrix), str(input_matrix)]
    return cmd


def build_fsl_applywarp_command(
    input_image: str | Path,
    reference_image: str | Path,
    output_image: str | Path,
    warp: str | Path,
    *,
    premat: str | Path | None = None,
) -> list[str]:
    cmd = [
        "applywarp",
        "--ref",
        str(reference_image),
        "--in",
        str(input_image),
        "--warp",
        str(warp),
        "--out",
        str(output_image),
    ]
    if premat is not None:
        cmd += ["--premat", str(premat)]
    return cmd


def build_fsl_fnirt_command(
    input_image: str | Path,
    reference_image: str | Path,
    output_coeff: str | Path,
    *,
    affine: str | Path | None = None,
    config: str | Path | None = None,
) -> list[str]:
    cmd = [
        "fnirt",
        "--in",
        str(input_image),
        "--ref",
        str(reference_image),
        "--cout",
        str(output_coeff),
    ]
    if affine is not None:
        cmd += ["--aff", str(affine)]
    if config is not None:
        cmd += ["--config", str(config)]
    return cmd


def build_fsl_invwarp_command(
    warp: str | Path,
    output_warp: str | Path,
    reference_image: str | Path,
) -> list[str]:
    return [
        "invwarp",
        "-w",
        str(warp),
        "-o",
        str(output_warp),
        "-r",
        str(reference_image),
    ]


def build_fsl_topup_command(
    imain: str | Path,
    datain: str | Path,
    config: str | Path,
    output_prefix: str | Path,
) -> list[str]:
    return [
        "topup",
        "--imain",
        str(imain),
        "--datain",
        str(datain),
        "--config",
        str(config),
        "--out",
        str(output_prefix),
    ]


def build_fsl_applytopup_command(
    imain: str | Path,
    inindex: str,
    datain: str | Path,
    topup_prefix: str | Path,
    output_image: str | Path,
) -> list[str]:
    return [
        "applytopup",
        "--imain",
        str(imain),
        "--inindex",
        inindex,
        "--datain",
        str(datain),
        "--topup",
        str(topup_prefix),
        "--out",
        str(output_image),
    ]


def build_fsl_design_ttest2_command(
    output_prefix: str | Path,
    n_group1: int,
    n_group2: int,
) -> list[str]:
    """Build the FSL ``design_ttest2`` command for two-group Randomise."""

    return [
        "design_ttest2",
        str(output_prefix),
        str(n_group1),
        str(n_group2),
    ]


def build_fsl_randomise_command(
    input_4d: str | Path,
    output_prefix: str | Path,
    mask: str | Path,
    design_mat: str | Path,
    design_con: str | Path,
    *,
    n_permutations: int = 5000,
    tfce: bool = True,
) -> list[str]:
    """Build an FSL Randomise command from the original two-sample workflow."""

    cmd = [
        "randomise",
        "-i",
        str(input_4d),
        "-o",
        str(output_prefix),
        "-m",
        str(mask),
        "-d",
        str(design_mat),
        "-t",
        str(design_con),
        "-n",
        str(n_permutations),
    ]
    if tfce:
        cmd.append("-T")
    return cmd


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
    seed_image: str | Path | None = None,
) -> dict[str, object]:
    return _run(
        build_mrtrix_tckgen_command(
            dwi,
            mask,
            output,
            algorithm=algorithm,
            num_tracks=num_tracks,
            seed_image=seed_image,
        )
    )


def run_fsl_bet(
    input_image: str | Path,
    output_image: str | Path,
    **kwargs: object,
) -> dict[str, object]:
    return _run(build_fsl_bet_command(input_image, output_image, **kwargs))


def run_fsl_eddy_correct(
    input_image: str | Path,
    output_image: str | Path,
    reference_volume: int = 0,
) -> dict[str, object]:
    return _run(build_fsl_eddy_correct_command(input_image, output_image, reference_volume))


def run_fsl_flirt(
    input_image: str | Path,
    reference_image: str | Path,
    output_image: str | Path | None = None,
    **kwargs: object,
) -> dict[str, object]:
    return _run(build_fsl_flirt_command(input_image, reference_image, output_image, **kwargs))


def run_fsl_applywarp(
    input_image: str | Path,
    reference_image: str | Path,
    output_image: str | Path,
    warp: str | Path,
    **kwargs: object,
) -> dict[str, object]:
    return _run(build_fsl_applywarp_command(input_image, reference_image, output_image, warp, **kwargs))


def run_fsl_fnirt(
    input_image: str | Path,
    reference_image: str | Path,
    output_coeff: str | Path,
    **kwargs: object,
) -> dict[str, object]:
    return _run(build_fsl_fnirt_command(input_image, reference_image, output_coeff, **kwargs))


def run_fsl_invwarp(
    warp: str | Path,
    output_warp: str | Path,
    reference_image: str | Path,
) -> dict[str, object]:
    return _run(build_fsl_invwarp_command(warp, output_warp, reference_image))


def run_fsl_topup(
    imain: str | Path,
    datain: str | Path,
    config: str | Path,
    output_prefix: str | Path,
) -> dict[str, object]:
    return _run(build_fsl_topup_command(imain, datain, config, output_prefix))


def run_fsl_applytopup(
    imain: str | Path,
    inindex: str,
    datain: str | Path,
    topup_prefix: str | Path,
    output_image: str | Path,
) -> dict[str, object]:
    return _run(build_fsl_applytopup_command(imain, inindex, datain, topup_prefix, output_image))


def run_fsl_design_ttest2(
    output_prefix: str | Path,
    n_group1: int,
    n_group2: int,
) -> dict[str, object]:
    return _run(build_fsl_design_ttest2_command(output_prefix, n_group1, n_group2))


def run_fsl_randomise(
    input_4d: str | Path,
    output_prefix: str | Path,
    mask: str | Path,
    design_mat: str | Path,
    design_con: str | Path,
    **kwargs: object,
) -> dict[str, object]:
    return _run(
        build_fsl_randomise_command(
            input_4d,
            output_prefix,
            mask,
            design_mat,
            design_con,
            **kwargs,
        )
    )


__all__ = [
    "build_fsl_applytopup_command",
    "build_fsl_applywarp_command",
    "build_fsl_bedpostx_command",
    "build_fsl_bet_command",
    "build_fsl_convert_xfm_command",
    "build_fsl_dtifit_command",
    "build_fsl_design_ttest2_command",
    "build_fsl_eddy_correct_command",
    "build_fsl_flirt_command",
    "build_fsl_fnirt_command",
    "build_fsl_invwarp_command",
    "build_fsl_probtrackx_command",
    "build_fsl_randomise_command",
    "build_fsl_topup_command",
    "build_mrtrix_tckgen_command",
    "check_external_tools",
    "run_fsl_bedpostx",
    "run_fsl_bet",
    "run_fsl_applytopup",
    "run_fsl_applywarp",
    "run_fsl_dtifit",
    "run_fsl_design_ttest2",
    "run_fsl_eddy_correct",
    "run_fsl_flirt",
    "run_fsl_fnirt",
    "run_fsl_invwarp",
    "run_fsl_probtrackx",
    "run_fsl_randomise",
    "run_fsl_topup",
    "run_mrtrix_tckgen",
]
