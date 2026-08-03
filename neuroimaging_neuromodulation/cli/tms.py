"""TMS-target command-line interface."""

from __future__ import annotations

import argparse

import numpy as np

from ..io.deformations import apply_deformation
from ..io.nifti import load_volume, save_volume
from ..preprocess.spatial import smooth_volume
from ..preprocess.temporal import apply_motion_parameters, slice_timing_correct_volume
from ..reporting.html import render_target_report
from ..stats.classification import leave_one_out_gfc_classification
from ..targets.pipeline import seed_based_fc, target_site
from ..targets.roi import deep_target, sphere_roi
from .common import add_io_arguments, parse_center


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nm-tms",
        description="Python-native TMS target tools",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    fc = subparsers.add_parser("seed-fc", help="Compute seed-based FC")
    fc.add_argument("--functional", required=True, help="4D functional NIfTI")
    fc.add_argument("--seed", required=True, help="Seed ROI NIfTI")
    fc.add_argument("--mask", required=True, help="Analysis mask NIfTI")
    fc.add_argument("--seed-deformation", help="Optional SPM inverse field to move seed into native space")
    fc.add_argument("--mask-deformation", help="Optional SPM inverse field to move mask into native space")
    fc.add_argument("--tr", type=float, required=True, help="Repetition time in seconds")
    fc.add_argument("--low-cutoff", type=float, default=0.01)
    fc.add_argument("--high-cutoff", type=float, default=0.1)
    fc.add_argument("--filter", action="store_true", help="Band-pass filter before correlation")
    fc.add_argument("--z-score", action="store_true", help="Fisher z-transform FC values")
    add_io_arguments(fc)
    fc.set_defaults(handler=run_fc)

    site = subparsers.add_parser("target-site", help="Generate target candidates from an FC map")
    site.add_argument("--fc", required=True, help="3D FC map NIfTI")
    site.add_argument("--p", type=float, default=0.05, dest="p_value")
    site.add_argument("--n", type=int, default=212, dest="n_samples")
    site.add_argument("--posneg", nargs="+", default=["Positive", "Negative"], choices=["Positive", "Negative", "Both"])
    add_io_arguments(site)
    site.set_defaults(handler=run_target_site)

    sphere = subparsers.add_parser("sphere", help="Create a spherical ROI")
    sphere.add_argument("--center", type=parse_center, required=True, help="MNI center: x,y,z")
    sphere.add_argument("--radius", type=float, required=True, help="Radius in mm")
    sphere.add_argument("--reference", required=True, help="Reference NIfTI")
    sphere.add_argument("--output", required=True, help="Output NIfTI path")
    sphere.set_defaults(handler=run_sphere)

    deep = subparsers.add_parser("deep-target", help="Compute a deep target coordinate")
    deep.add_argument("--tissue", required=True, help="Tissue probability NIfTI (e.g. c1)")
    deep.add_argument("--center", type=parse_center, required=True, help="MNI center: x,y,z")
    deep.add_argument("--radius", type=float, default=40.0)
    deep.add_argument("--depth", type=float, default=6.0)
    deep.add_argument("--output", required=True, help="Output text file path")
    deep.set_defaults(handler=run_deep_target)

    deform = subparsers.add_parser("deform", help="Apply a nonlinear deformation field")
    deform.add_argument("--source", required=True, help="Image to sample")
    deform.add_argument("--deformation", required=True, help="SPM-style deformation field NIfTI")
    deform.add_argument("--output", required=True, help="Output NIfTI path")
    deform.add_argument("--order", type=int, default=1, choices=[0, 1, 2, 3])
    deform.add_argument("--zero-based", action="store_true", help="Treat field coordinates as 0-based")
    deform.set_defaults(handler=run_deform)

    st = subparsers.add_parser("slice-timing", help="Correct slice timing with Fourier interpolation")
    st.add_argument("--functional", required=True)
    st.add_argument("--output", required=True)
    st.add_argument("--tr", type=float, required=True)
    st.add_argument("--slice-order", required=True, help="Comma-separated 1-based slice order")
    st.add_argument("--ref-slice", type=int, required=True)
    st.set_defaults(handler=run_slice_timing)

    mc = subparsers.add_parser("motion-correct", help="Resample volumes using SPM-style realignment parameters")
    mc.add_argument("--functional", required=True)
    mc.add_argument("--rp", required=True, help="Six-column realignment parameter text file")
    mc.add_argument("--output", required=True)
    mc.add_argument("--order", type=int, default=3, choices=[0, 1, 2, 3])
    mc.set_defaults(handler=run_motion_correct)

    sm = subparsers.add_parser("smooth", help="Gaussian-smooth a 3D/4D image in mm")
    sm.add_argument("--functional", required=True)
    sm.add_argument("--fwhm", type=float, required=True, help="Full-width at half maximum in mm")
    sm.add_argument("--output", required=True)
    sm.set_defaults(handler=run_smooth)

    report = subparsers.add_parser("report", help="Generate an HTML report and SHA-256 manifest for a subject")
    report.add_argument("--output-dir", required=True)
    report.add_argument("--subject", required=True)
    report.add_argument("--output", help="Output HTML path (default: <output-dir>/<subject>/report.html)")
    report.set_defaults(handler=run_report)

    cls = subparsers.add_parser("classify-gfc", help="Leave-one-out GFC classification")
    cls.add_argument("--matrix", required=True, help="NxSubjects matrix in .npy or text format")
    cls.add_argument("--n-group1", type=int, required=True)
    cls.add_argument("--output", required=True, help="Output score text file")
    cls.set_defaults(handler=run_classify_gfc)

    return parser


def run_fc(args: argparse.Namespace) -> int:
    result = seed_based_fc(
        args.functional,
        args.seed,
        args.mask,
        args.output_dir,
        subject=args.subject,
        z_score=args.z_score,
        tr=args.tr if args.filter else None,
        band=(args.low_cutoff, args.high_cutoff) if args.filter else None,
        filter_data=args.filter,
        seed_deformation=args.seed_deformation,
        mask_deformation=args.mask_deformation,
    )
    print(result["SeedFCinWB"])
    print(result["SeedFCinROI"])
    return 0


def run_target_site(args: argparse.Namespace) -> int:
    posneg = ["Positive", "Negative"] if "Both" in args.posneg else args.posneg
    results = target_site(
        args.fc,
        args.output_dir,
        subject=args.subject,
        posneg=posneg,
        p_value=args.p_value,
        n_samples=args.n_samples,
    )
    for result in results:
        print(result["direction"], result["extremum_mni"].tolist())
        if result["largest_cluster_size"]:
            print("largest_cluster", result["largest_cluster_size"], result.get("center_mni", []).tolist())
    return 0


def run_sphere(args: argparse.Namespace) -> int:
    _, mask = sphere_roi(args.center, args.radius, args.reference, args.output)
    print(args.output, int(mask.sum()))
    return 0


def run_deep_target(args: argparse.Namespace) -> int:
    cortical, deep = deep_target(
        args.tissue,
        args.center,
        radius_mm=args.radius,
        depth_mm=args.depth,
        out_path=args.output,
    )
    print("cortical", cortical.tolist())
    print("deep", deep.tolist())
    return 0


def run_deform(args: argparse.Namespace) -> int:
    img, data = apply_deformation(
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


def run_report(args: argparse.Namespace) -> int:
    path = render_target_report(args.output_dir, args.subject, args.output)
    print(path)
    return 0


def run_classify_gfc(args: argparse.Namespace) -> int:
    path = Path(args.matrix)
    matrix = np.load(path) if path.suffix == ".npy" else np.loadtxt(path)
    result = leave_one_out_gfc_classification(matrix, args.n_group1)
    np.savetxt(args.output, result["scores"], fmt="%.10f")
    print(
        f"sensitivity={result['sensitivity']:.4f} "
        f"specificity={result['specificity']:.4f} "
        f"accuracy={result['accuracy']:.4f} "
        f"auc={result['auc']:.4f}"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
