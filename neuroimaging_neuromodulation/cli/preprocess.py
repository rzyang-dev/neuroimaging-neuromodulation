"""Preprocessing command-line interface."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from ..io.deformations import apply_deformation
from ..io.nifti import load_4d_matrix, load_volume, save_volume
from ..deformations.estimate import estimate_deformation
from ..preprocess.covariates import design_matrix, extract_signal, friston24, regress_out_nuisance
from ..preprocess.coregister import coregister_images
from ..preprocess.imaging import flip_left_right
from ..preprocess.motion import estimate_motion_parameters
from ..preprocess.spatial import smooth_volume
from ..preprocess.temporal import apply_motion_parameters, slice_timing_correct_volume
from ..segmentation.tissue import segment_tissue
from ..validation.metrics import compare_volumes, validate_deformation
from ..stats.functional import bandpass_filter
from ..stats.regression import regress


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nm-preprocess",
        description="Python-native neuroimaging preprocessing commands",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    deform = subparsers.add_parser("deform", help="Apply a nonlinear deformation field")
    deform.add_argument("--source", required=True)
    deform.add_argument("--deformation", required=True)
    deform.add_argument("--output", required=True)
    deform.add_argument("--order", type=int, default=1, choices=[0, 1, 2, 3])
    deform.add_argument("--zero-based", action="store_true")
    deform.set_defaults(handler=run_deform)

    st = subparsers.add_parser("slice-timing", help="Correct slice timing with Fourier interpolation")
    st.add_argument("--functional", required=True)
    st.add_argument("--output", required=True)
    st.add_argument("--tr", type=float, required=True)
    st.add_argument("--slice-order", required=True)
    st.add_argument("--ref-slice", type=int, required=True)
    st.set_defaults(handler=run_slice_timing)

    mc = subparsers.add_parser("motion-correct", help="Resample volumes using SPM-style realignment parameters")
    mc.add_argument("--functional", required=True)
    mc.add_argument("--rp", required=True)
    mc.add_argument("--output", required=True)
    mc.add_argument("--order", type=int, default=3, choices=[0, 1, 2, 3])
    mc.set_defaults(handler=run_motion_correct)

    sm = subparsers.add_parser("smooth", help="Gaussian-smooth a 3D/4D image in mm")
    sm.add_argument("--functional", required=True)
    sm.add_argument("--fwhm", type=float, required=True)
    sm.add_argument("--output", required=True)
    sm.set_defaults(handler=run_smooth)

    em = subparsers.add_parser("estimate-motion", help="Estimate rigid motion and reslice a 4D series")
    em.add_argument("--functional", required=True)
    em.add_argument("--output", required=True)
    em.add_argument("--rp-output", required=True)
    em.add_argument("--reference", type=int, default=0)
    em.add_argument("--pipeline", default="translation,rigid", help="Comma-separated DIPY registration pipeline")
    em.add_argument("--level-iters", default="20,10,5", help="Comma-separated pyramid iteration counts")
    em.add_argument("--maxiter", type=int, default=50)
    em.set_defaults(handler=run_estimate_motion)

    flt = subparsers.add_parser("filter", help="Band-pass filter a functional series")
    flt.add_argument("--functional", required=True)
    flt.add_argument("--mask", required=True)
    flt.add_argument("--output", required=True)
    flt.add_argument("--tr", type=float, required=True)
    flt.add_argument("--low-cutoff", type=float, default=0.01)
    flt.add_argument("--high-cutoff", type=float, default=0.1)
    flt.set_defaults(handler=run_filter)

    flip = subparsers.add_parser("flip-lr", help="Flip an image along the left-right axis")
    flip.add_argument("--image", required=True)
    flip.add_argument("--output", required=True)
    flip.set_defaults(handler=run_flip_lr)

    co = subparsers.add_parser("coregister", help="Coregister a moving volume to a static volume")
    co.add_argument("--moving", required=True)
    co.add_argument("--static", required=True)
    co.add_argument("--output", required=True)
    co.add_argument("--affine-output", help="Optional text file for the 4x4 affine")
    co.add_argument("--volume", type=int, default=0, help="Volume index when moving is 4D")
    co.add_argument("--pipeline", default="translation,rigid")
    co.add_argument("--level-iters", default="20,10,5")
    co.add_argument("--maxiter", type=int, default=50)
    co.set_defaults(handler=run_coregister)

    seg = subparsers.add_parser("segment-tissue", help="Estimate GM/WM/CSF tissue probability maps")
    seg.add_argument("--t1", required=True)
    seg.add_argument("--output-dir", required=True)
    seg.add_argument("--grey-prior")
    seg.add_argument("--white-prior")
    seg.add_argument("--csf-prior")
    seg.add_argument("--iterations", type=int, default=20)
    seg.set_defaults(handler=run_segment_tissue)

    est = subparsers.add_parser("estimate-deformation", help="Estimate a nonlinear deformation with DIPY")
    est.add_argument("--moving", required=True)
    est.add_argument("--static", required=True)
    est.add_argument("--output-dir", required=True)
    est.add_argument("--metric", default="CC")
    est.add_argument("--level-iters", default="10,10,5")
    est.add_argument("--step-length", type=float, default=0.25)
    est.set_defaults(handler=run_estimate_deformation)

    vd = subparsers.add_parser("validate-deformation", help="Apply a deformation field and compare to a reference warped image")
    vd.add_argument("--moving", required=True)
    vd.add_argument("--field", required=True)
    vd.add_argument("--reference", required=True)
    vd.add_argument("--output-json", required=True)
    vd.add_argument("--order", type=int, default=1, choices=[0, 1, 2, 3])
    vd.set_defaults(handler=run_validate_deformation)

    vi = subparsers.add_parser("validate-image", help="Compare two aligned images")
    vi.add_argument("--reference", required=True)
    vi.add_argument("--test", required=True)
    vi.add_argument("--output-json", required=True)
    vi.set_defaults(handler=run_validate_image)

    reg = subparsers.add_parser("regress", help="Run generic linear regression on text matrices")
    reg.add_argument("--y", required=True, help="Nx1 response matrix")
    reg.add_argument("--x", required=True, help="NxK design matrix")
    reg.add_argument("--beta-output", required=True)
    reg.add_argument("--residual-output", required=True)
    reg.set_defaults(handler=run_regress)

    cov = subparsers.add_parser("regress-covariates", help="Regress nuisance signals from functional data")
    cov.add_argument("--functional", required=True)
    cov.add_argument("--output", required=True)
    cov.add_argument("--rp", help="Six-column realignment parameters")
    cov.add_argument("--wm-signal", help="White-matter signal text file")
    cov.add_argument("--csf-signal", help="CSF signal text file")
    cov.add_argument("--global-signal", help="Global signal text file")
    cov.add_argument("--wm-mask", help="White-matter mask NIfTI")
    cov.add_argument("--csf-mask", help="CSF mask NIfTI")
    cov.add_argument("--global-mask", help="Global signal mask NIfTI")
    cov.set_defaults(handler=run_regress_covariates)

    sig = subparsers.add_parser("extract-signal", help="Extract mean signal from a mask")
    sig.add_argument("--functional", required=True)
    sig.add_argument("--mask", required=True)
    sig.add_argument("--output", required=True)
    sig.set_defaults(handler=run_extract_signal)

    f24 = subparsers.add_parser("friston24", help="Build Friston-24 motion regressors")
    f24.add_argument("--rp", required=True)
    f24.add_argument("--output", required=True)
    f24.set_defaults(handler=run_friston24)

    return parser


def run_deform(args: argparse.Namespace) -> int:
    img, _ = apply_deformation(
        args.source,
        args.deformation,
        args.output,
        order=args.order,
        one_based=not args.zero_based,
    )
    print(args.output, img.shape)
    return 0


def run_slice_timing(args: argparse.Namespace) -> int:
    img, data = load_volume(args.functional)
    if data.ndim != 4:
        raise ValueError("slice-timing expects 4D functional data")
    order = [
        int(x)
        for x in args.slice_order.replace(";", ",").replace(" ", ",").split(",")
        if x
    ]
    corrected = slice_timing_correct_volume(data, args.tr, order, args.ref_slice)
    save_volume(corrected, img, args.output)
    print(args.output)
    return 0


def run_motion_correct(args: argparse.Namespace) -> int:
    img, data = load_volume(args.functional)
    if data.ndim != 4:
        raise ValueError("motion-correct expects 4D functional data")
    rp = np.loadtxt(args.rp)
    if rp.ndim != 2 or rp.shape[1] != 6:
        raise ValueError("RP file must contain six columns: translations mm and rotations rad")
    corrected = apply_motion_parameters(data, rp, img.affine, order=args.order)
    save_volume(corrected, img, args.output)
    print(args.output)
    return 0


def run_smooth(args: argparse.Namespace) -> int:
    img, data = load_volume(args.functional)
    smoothed = smooth_volume(data, args.fwhm, img.affine)
    save_volume(smoothed, img, args.output)
    print(args.output)
    return 0


def run_estimate_motion(args: argparse.Namespace) -> int:
    img, data = load_volume(args.functional)
    if data.ndim != 4:
        raise ValueError("estimate-motion expects 4D functional data")
    pipeline = tuple(x for x in args.pipeline.replace(" ", "").split(",") if x)
    level_iters = tuple(int(x) for x in args.level_iters.replace(" ", "").split(",") if x)
    corrected, rp = estimate_motion_parameters(
        data,
        img.affine,
        reference_volume=args.reference,
        pipeline=pipeline,
        level_iters=level_iters,
        optimizer_options={"maxiter": args.maxiter},
    )
    save_volume(corrected, img, args.output)
    np.savetxt(args.rp_output, rp, fmt="%.10f")
    print(args.output)
    print(args.rp_output)
    return 0


def run_filter(args: argparse.Namespace) -> int:
    img, data = load_4d_matrix(args.functional)
    _, mask_data = load_volume(args.mask)
    mask = mask_data.reshape(-1) > 0
    if mask.size != data.shape[0]:
        raise ValueError("Mask does not match functional grid")
    filtered = bandpass_filter(data, args.tr, (args.low_cutoff, args.high_cutoff), mask=mask)
    save_volume(filtered.reshape(*img.shape[:3], -1), img, args.output)
    print(args.output)
    return 0


def run_flip_lr(args: argparse.Namespace) -> int:
    img, data = load_volume(args.image)
    save_volume(flip_left_right(data), img, args.output)
    print(args.output)
    return 0


def run_coregister(args: argparse.Namespace) -> int:
    moving_img, moving_data = load_volume(args.moving)
    static_img, static_data = load_volume(args.static)
    if moving_data.ndim == 4:
        moving_data = moving_data[..., args.volume]
    if static_data.ndim == 4:
        static_data = static_data[..., args.volume]
    pipeline = tuple(x for x in args.pipeline.replace(" ", "").split(",") if x)
    level_iters = tuple(int(x) for x in args.level_iters.replace(" ", "").split(",") if x)
    resampled, affine = coregister_images(
        moving_data,
        static_data,
        moving_affine=moving_img.affine,
        static_affine=static_img.affine,
        pipeline=pipeline,
        level_iters=level_iters,
        optimizer_options={"maxiter": args.maxiter},
    )
    save_volume(resampled, static_img, args.output)
    if args.affine_output:
        np.savetxt(args.affine_output, affine, fmt="%.10f")
    print(args.output)
    if args.affine_output:
        print(args.affine_output)
    return 0


def run_segment_tissue(args: argparse.Namespace) -> int:
    package_data = Path(__file__).resolve().parents[1] / "data"
    paths = segment_tissue(
        args.t1,
        args.output_dir,
        grey_prior=args.grey_prior or package_data / "grey.nii",
        white_prior=args.white_prior or package_data / "white.nii",
        csf_prior=args.csf_prior or package_data / "csf.nii",
        iterations=args.iterations,
    )
    for key, path in paths.items():
        print(key, path)
    return 0


def run_estimate_deformation(args: argparse.Namespace) -> int:
    level_iters = tuple(int(x) for x in args.level_iters.replace(" ", "").split(",") if x)
    paths = estimate_deformation(
        args.moving,
        args.static,
        args.output_dir,
        metric=args.metric,
        level_iters=level_iters,
        step_length=args.step_length,
    )
    for key, path in paths.items():
        print(key, path)
    return 0


def run_validate_deformation(args: argparse.Namespace) -> int:
    result = validate_deformation(
        args.moving,
        args.field,
        args.reference,
        order=args.order,
        output_json=args.output_json,
    )
    print(json.dumps(result, indent=2, default=str))
    return 0


def run_validate_image(args: argparse.Namespace) -> int:
    metrics = compare_volumes(args.reference, args.test)
    Path(args.output_json).write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    return 0


def _read_signal(path: str | None) -> np.ndarray | None:
    if not path:
        return None
    value = np.loadtxt(path).reshape(-1)
    return value


def run_regress(args: argparse.Namespace) -> int:
    y = np.loadtxt(args.y).reshape(-1)
    x = np.loadtxt(args.x)
    beta, residual = regress(y, x)
    np.savetxt(args.beta_output, beta)
    np.savetxt(args.residual_output, residual)
    print(args.beta_output)
    print(args.residual_output)
    return 0


def run_regress_covariates(args: argparse.Namespace) -> int:
    img, data = load_volume(args.functional)
    if data.ndim != 4:
        raise ValueError("regress-covariates expects 4D functional data")
    matrix = data.reshape(-1, data.shape[3])
    rp = np.loadtxt(args.rp) if args.rp else None
    if rp is not None and (rp.ndim != 2 or rp.shape[1] != 6):
        raise ValueError("RP file must have six columns")
    signals = [None, None, None]
    masks = [args.wm_mask, args.csf_mask, args.global_mask]
    for index, signal_path in enumerate([args.wm_signal, args.csf_signal, args.global_signal]):
        signals[index] = _read_signal(signal_path)
    for index, mask_path in enumerate(masks):
        if mask_path:
            _, mask_data = load_volume(mask_path)
            signals[index] = extract_signal(matrix, mask_data.reshape(-1) > 0)
    design = design_matrix(
        matrix.shape[1],
        motion_parameters=rp,
        wm_signal=signals[0],
        csf_signal=signals[1],
        global_signal=signals[2],
    )
    regressed = regress_out_nuisance(matrix, design)
    save_volume(regressed.reshape(data.shape), img, args.output)
    print(args.output)
    return 0


def run_extract_signal(args: argparse.Namespace) -> int:
    img, data = load_volume(args.functional)
    if data.ndim != 4:
        raise ValueError("extract-signal expects 4D functional data")
    _, mask_data = load_volume(args.mask)
    signal = extract_signal(data.reshape(-1, data.shape[3]), mask_data.reshape(-1) > 0)
    np.savetxt(args.output, signal, fmt="%.10f")
    print(args.output)
    return 0


def run_friston24(args: argparse.Namespace) -> int:
    rp = np.loadtxt(args.rp)
    expanded = friston24(rp)
    np.savetxt(args.output, expanded, fmt="%.10f")
    print(args.output)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
