"""Diffusion MRI command-line interface."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import nibabel as nib
import numpy as np

from ..diffusion.connectivity import count_streamlines_between_masks
from ..diffusion.dti import fit_tensor, load_dwi, write_tensor_metrics
from ..diffusion.tracking import track_deterministic, track_probabilistic
from ..diffusion.external import (
    build_fsl_bedpostx_command,
    build_fsl_dtifit_command,
    build_fsl_probtrackx_command,
    build_mrtrix_tckgen_command,
    check_external_tools,
    run_fsl_bedpostx,
    run_fsl_dtifit,
    run_fsl_probtrackx,
    run_mrtrix_tckgen,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nm-diffusion",
        description="Python-native DTI and tractography tools",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    fit = subparsers.add_parser("fit-tensor", help="Fit tensors and write scalar maps")
    fit.add_argument("--dwi", required=True)
    fit.add_argument("--bval", required=True)
    fit.add_argument("--bvec", required=True)
    fit.add_argument("--output-dir", required=True)
    fit.add_argument("--prefix", default="DTI")
    fit.set_defaults(handler=run_fit_tensor)

    track = subparsers.add_parser("track", help="Run deterministic tensor tractography")
    track.add_argument("--dwi", required=True)
    track.add_argument("--bval", required=True)
    track.add_argument("--bvec", required=True)
    track.add_argument("--seed", required=True)
    track.add_argument("--stop", required=True)
    track.add_argument("--output", required=True)
    track.add_argument("--fa-threshold", type=float, default=0.2)
    track.add_argument("--step-size", type=float, default=0.5)
    track.add_argument("--min-length", type=float, default=10.0)
    track.add_argument("--max-length", type=float, default=500.0)
    track.add_argument("--max-angle", type=float, default=30.0)
    track.add_argument("--seed-density", type=int, default=1)
    track.set_defaults(handler=run_track)

    prob = subparsers.add_parser("track-probabilistic", help="Run probabilistic tensor tractography")
    prob.add_argument("--dwi", required=True)
    prob.add_argument("--bval", required=True)
    prob.add_argument("--bvec", required=True)
    prob.add_argument("--seed", required=True)
    prob.add_argument("--stop", required=True)
    prob.add_argument("--output", required=True)
    prob.add_argument("--fa-threshold", type=float, default=0.2)
    prob.add_argument("--step-size", type=float, default=0.5)
    prob.add_argument("--min-length", type=float, default=10.0)
    prob.add_argument("--max-length", type=float, default=500.0)
    prob.add_argument("--max-angle", type=float, default=20.0)
    prob.add_argument("--seed-density", type=int, default=1)
    prob.add_argument("--random-seed", type=int, default=1)
    prob.set_defaults(handler=run_track_probabilistic)

    conn = subparsers.add_parser("connectivity", help="Track and count seed-target connections")
    conn.add_argument("--dwi", required=True)
    conn.add_argument("--bval", required=True)
    conn.add_argument("--bvec", required=True)
    conn.add_argument("--seed", required=True)
    conn.add_argument("--target", required=True)
    conn.add_argument("--stop", required=True)
    conn.add_argument("--trk-output", required=True)
    conn.add_argument("--count-output", required=True)
    conn.add_argument("--fa-threshold", type=float, default=0.2)
    conn.set_defaults(handler=run_connectivity)

    bedpostx = subparsers.add_parser("fsl-bedpostx", help="Run FSL bedpostx (requires FSL)")
    bedpostx.add_argument("--bedpostx-dir", required=True)
    bedpostx.add_argument("--dry-run", action="store_true")
    bedpostx.set_defaults(handler=run_fsl_bedpostx_cmd)

    dtifit = subparsers.add_parser("fsl-dtifit", help="Run FSL dtifit (requires FSL)")
    dtifit.add_argument("--dwi", required=True)
    dtifit.add_argument("--mask", required=True)
    dtifit.add_argument("--bvec", required=True)
    dtifit.add_argument("--bval", required=True)
    dtifit.add_argument("--output-prefix", required=True)
    dtifit.add_argument("--dry-run", action="store_true")
    dtifit.set_defaults(handler=run_fsl_dtifit_cmd)

    prob = subparsers.add_parser("fsl-probtrackx", help="Run FSL probtrackx2 (requires FSL)")
    prob.add_argument("--seed", required=True)
    prob.add_argument("--target", required=True)
    prob.add_argument("--bedpostx-dir", required=True)
    prob.add_argument("--output-dir", required=True)
    prob.add_argument("--samples", type=int, default=5000)
    prob.add_argument("--steps", type=int, default=2000)
    prob.add_argument("--dry-run", action="store_true")
    prob.set_defaults(handler=run_fsl_probtrackx_cmd)

    tckgen = subparsers.add_parser("mrtrix-tckgen", help="Run MRtrix tckgen (requires MRtrix3)")
    tckgen.add_argument("--dwi", required=True)
    tckgen.add_argument("--mask", required=True)
    tckgen.add_argument("--output", required=True)
    tckgen.add_argument("--algorithm", default="iFOD2")
    tckgen.add_argument("--num-tracks", type=int, default=100000)
    tckgen.add_argument("--dry-run", action="store_true")
    tckgen.set_defaults(handler=run_mrtrix_tckgen_cmd)

    check = subparsers.add_parser("check-external", help="Check FSL/MRtrix binary availability")
    check.set_defaults(handler=run_check_external)

    return parser


def _load_bool(path: str) -> tuple[np.ndarray, nib.Nifti1Image]:
    img = nib.load(path)
    return np.asanyarray(img.dataobj) > 0, img


def run_fit_tensor(args: argparse.Namespace) -> int:
    data, _affine, gtab, img = load_dwi(args.dwi, args.bval, args.bvec)
    mask = np.asanyarray(img.dataobj)[..., 0] > 0
    fit = fit_tensor(data, gtab, mask=mask)
    paths = write_tensor_metrics(fit, img, args.output_dir, prefix=args.prefix)
    for key, path in paths.items():
        print(key, path)
    return 0


def run_track(args: argparse.Namespace) -> int:
    data, affine, gtab, _ = load_dwi(args.dwi, args.bval, args.bvec)
    seed_mask, _ = _load_bool(args.seed)
    stop_map = np.asanyarray(nib.load(args.stop).dataobj)
    streamlines = track_deterministic(
        data,
        gtab,
        affine,
        seed_mask=seed_mask,
        stop_map=stop_map,
        fa_threshold=args.fa_threshold,
        step_size=args.step_size,
        min_length=args.min_length,
        max_length=args.max_length,
        max_angle=args.max_angle,
        seed_density=args.seed_density,
        out_trk=args.output,
    )
    print(args.output, len(streamlines))
    return 0


def run_track_probabilistic(args: argparse.Namespace) -> int:
    data, affine, gtab, _ = load_dwi(args.dwi, args.bval, args.bvec)
    seed_mask, _ = _load_bool(args.seed)
    stop_map = np.asanyarray(nib.load(args.stop).dataobj)
    streamlines = track_probabilistic(
        data,
        gtab,
        affine,
        seed_mask=seed_mask,
        stop_map=stop_map,
        fa_threshold=args.fa_threshold,
        step_size=args.step_size,
        min_length=args.min_length,
        max_length=args.max_length,
        max_angle=args.max_angle,
        seed_density=args.seed_density,
        random_seed=args.random_seed,
        out_trk=args.output,
    )
    print(args.output, len(streamlines))
    return 0


def run_connectivity(args: argparse.Namespace) -> int:
    data, affine, gtab, _ = load_dwi(args.dwi, args.bval, args.bvec)
    seed_mask, _ = _load_bool(args.seed)
    target_mask, _ = _load_bool(args.target)
    stop_map = np.asanyarray(nib.load(args.stop).dataobj)
    streamlines = track_deterministic(
        data,
        gtab,
        affine,
        seed_mask=seed_mask,
        stop_map=stop_map,
        fa_threshold=args.fa_threshold,
        out_trk=args.trk_output,
    )
    result = count_streamlines_between_masks(
        streamlines,
        affine,
        seed_mask,
        target_mask,
    )
    Path(args.count_output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(args.trk_output)
    print(args.count_output)
    return 0


def run_fsl_bedpostx_cmd(args: argparse.Namespace) -> int:
    cmd = build_fsl_bedpostx_command(args.bedpostx_dir)
    if args.dry_run:
        print(" ".join(cmd))
        return 0
    result = run_fsl_bedpostx(args.bedpostx_dir)
    print(result["returncode"])
    return 0


def run_fsl_dtifit_cmd(args: argparse.Namespace) -> int:
    cmd = build_fsl_dtifit_command(args.dwi, args.mask, args.bvec, args.bval, args.output_prefix)
    if args.dry_run:
        print(" ".join(cmd))
        return 0
    result = run_fsl_dtifit(args.dwi, args.mask, args.bvec, args.bval, args.output_prefix)
    print(result["returncode"])
    return 0


def run_fsl_probtrackx_cmd(args: argparse.Namespace) -> int:
    cmd = build_fsl_probtrackx_command(
        args.seed,
        args.target,
        args.bedpostx_dir,
        args.output_dir,
        samples=args.samples,
        steps=args.steps,
    )
    if args.dry_run:
        print(" ".join(cmd))
        return 0
    result = run_fsl_probtrackx(
        args.seed,
        args.target,
        args.bedpostx_dir,
        args.output_dir,
        samples=args.samples,
        steps=args.steps,
    )
    print(result["returncode"])
    return 0


def run_mrtrix_tckgen_cmd(args: argparse.Namespace) -> int:
    cmd = build_mrtrix_tckgen_command(args.dwi, args.mask, args.output, algorithm=args.algorithm, num_tracks=args.num_tracks)
    if args.dry_run:
        print(" ".join(cmd))
        return 0
    result = run_mrtrix_tckgen(args.dwi, args.mask, args.output, algorithm=args.algorithm, num_tracks=args.num_tracks)
    print(result["returncode"])
    return 0


def run_check_external(args: argparse.Namespace) -> int:
    print(json.dumps(check_external_tools(), indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
