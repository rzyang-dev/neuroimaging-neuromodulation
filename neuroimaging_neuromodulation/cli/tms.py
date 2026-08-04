"""TMS-target command-line interface."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from ..io.deformations import apply_deformation
from ..io.nifti import load_4d_matrix, load_volume, save_volume
from ..preprocess.spatial import smooth_volume
from ..preprocess.temporal import apply_motion_parameters, slice_timing_correct_volume
from ..reporting.html import render_target_report
from ..reporting.viewer import render_viewer_report
from ..stats.classification import leave_one_out_gfc_classification
from ..stats.group import (
    chi_square_test,
    compare_correlation_coefficients,
    permutation_ttest,
    quantile_regression,
    ttest2_with_covariates,
)
from ..stats.functional import roi_correlation_matrix
from ..targets.pipeline import seed_based_fc, target_site
from ..targets.roi import deep_target, sphere_roi
from ..targets.t1 import generate_t1_target
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
    fc.add_argument("--seed-deformation", help="Optional SPM y_ template-to-native field")
    fc.add_argument("--mask-deformation", help="Optional SPM y_ template-to-native field")
    fc.add_argument("--target-mask", help="MNI target ROI used for individualized target masks")
    fc.add_argument("--c6", help="T1-space c6 outer-brain tissue image")
    fc.add_argument("--c1", help="Optional T1-space c1 grey-matter tissue image")
    fc.add_argument("--depth-mm", type=float, help="Maximum distance from outer-brain surface in mm")
    fc.add_argument("--extend-iterations", type=int, default=15)
    fc.add_argument("--tr", type=float, required=True, help="Repetition time in seconds")
    fc.add_argument("--low-cutoff", type=float, default=0.01)
    fc.add_argument("--high-cutoff", type=float, default=0.1)
    fc.add_argument("--filter", action="store_true", help="Band-pass filter before correlation")
    fc.add_argument("--z-score", action="store_true", help="Fisher z-transform FC values")
    add_io_arguments(fc)
    fc.set_defaults(handler=run_fc)

    roi_fc = subparsers.add_parser("roi-fc", help="Compute ROI-wise functional connectivity")
    roi_fc.add_argument("--functional", required=True)
    roi_fc.add_argument("--rois", nargs="+", required=True)
    roi_fc.add_argument("--output", required=True, help="Output correlation matrix text file")
    roi_fc.set_defaults(handler=run_roi_fc)

    site = subparsers.add_parser("target-site", help="Generate target candidates from an FC map")
    site.add_argument("--fc", required=True, help="3D FC map NIfTI")
    site.add_argument("--p", type=float, default=0.05, dest="p_value")
    site.add_argument("--n", type=int, default=212, dest="n_samples")
    site.add_argument("--posneg", nargs="+", default=["Positive", "Negative"], choices=["Positive", "Negative", "Both"])
    site.add_argument("--native-deformation", help="Optional SPM y_ template-to-native field")
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

    t1_target = subparsers.add_parser("t1-target", help="Write an MNI target ROI into T1 space")
    t1_target.add_argument("--target", required=True, help="MNI target ROI NIfTI")
    t1_target.add_argument("--deformation", help="Optional SPM y_ template-to-native field NIfTI")
    t1_target.add_argument("--t1", required=True, help="T1 reference image")
    t1_target.add_argument("--output", required=True)
    t1_target.add_argument("--spm-exe", help="Path to SPM25 standalone executable")
    t1_target.add_argument("--spm-dir", help="Directory for SPM segmentation outputs")
    t1_target.add_argument("--timeout", type=int, default=1800)
    t1_target.set_defaults(handler=run_t1_target)

    deform = subparsers.add_parser("deform", help="Apply a nonlinear deformation field")
    deform.add_argument("--source", required=True, help="Image to sample")
    deform.add_argument("--deformation", required=True, help="SPM-style deformation field NIfTI")
    deform.add_argument("--output", required=True, help="Output NIfTI path")
    deform.add_argument("--order", type=int, default=1, choices=[0, 1, 2, 3])
    deform.add_argument("--coordinate-system", choices=["voxel", "world"], default="world")
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

    view = subparsers.add_parser("view-report", help="Generate an HTML image QC viewer")
    view.add_argument("--reference", required=True)
    view.add_argument("--target")
    view.add_argument("--output", required=True)
    view.add_argument("--slices", type=int, default=9)
    view.add_argument("--max-dim", type=int, default=80)
    view.set_defaults(handler=run_view_report)

    cls = subparsers.add_parser("classify-gfc", help="Leave-one-out GFC classification")
    cls.add_argument("--matrix", required=True, help="NxSubjects matrix in .npy or text format")
    cls.add_argument("--n-group1", type=int, required=True)
    cls.add_argument("--output", required=True, help="Output score text file")
    cls.set_defaults(handler=run_classify_gfc)

    compare = subparsers.add_parser("compare-correlations", help="Compare two correlation coefficients")
    compare.add_argument("--r1", required=True, help="Comma-separated r1 values")
    compare.add_argument("--r2", required=True, help="Comma-separated r2 values")
    compare.add_argument("--n1", type=int, required=True)
    compare.add_argument("--n2", type=int, required=True)
    compare.add_argument("--tail", choices=["both", "right", "left"], default="both")
    compare.add_argument("--output", required=True)
    compare.set_defaults(handler=run_compare_correlations)

    chi = subparsers.add_parser("chi-square", help="Run a chi-square test")
    chi.add_argument("--matrix", required=True, help="Contingency table text file")
    chi.add_argument("--output", required=True)
    chi.set_defaults(handler=run_chi_square)

    ttest = subparsers.add_parser("ttest2-covariates", help="Two-group t-test with covariates")
    ttest.add_argument("--y", required=True)
    ttest.add_argument("--group", required=True)
    ttest.add_argument("--covs", required=True)
    ttest.add_argument("--output-json", required=True)
    ttest.set_defaults(handler=run_ttest2_covariates)

    quant = subparsers.add_parser("quantreg", help="Fit quantile regression")
    quant.add_argument("--x", required=True)
    quant.add_argument("--y", required=True)
    quant.add_argument("--tau", type=float, required=True)
    quant.add_argument("--order", type=int, default=1)
    quant.add_argument("--nboot", type=int, default=200)
    quant.add_argument("--random-seed", type=int, default=0)
    quant.add_argument("--output-json", required=True)
    quant.set_defaults(handler=run_quantreg)

    perm = subparsers.add_parser("permutation-ttest", help="Run a permutation two-sample t-test")
    perm.add_argument("--y", required=True)
    perm.add_argument("--group", required=True)
    perm.add_argument("--n-permutations", type=int, default=5000)
    perm.add_argument("--random-seed", type=int, default=0)
    perm.add_argument("--output-json", required=True)
    perm.set_defaults(handler=run_permutation_ttest)

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
        target_mask_image=args.target_mask,
        c6_image=args.c6,
        c1_image=args.c1,
        depth_mm=args.depth_mm,
        extend_iterations=args.extend_iterations,
        seed_deformation=args.seed_deformation,
        mask_deformation=args.mask_deformation,
    )
    print(result["SeedFCinWB"])
    print(result["SeedFCinROI"])
    return 0


def run_roi_fc(args: argparse.Namespace) -> int:
    _img, matrix = load_4d_matrix(args.functional)
    masks = []
    for roi in args.rois:
        _roi_img, roi_data = load_volume(roi)
        masks.append(roi_data.reshape(-1) > 0)
    corr = roi_correlation_matrix(matrix, masks)
    np.savetxt(args.output, corr, fmt="%.10f")
    print(args.output)
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
        native_deformation=args.native_deformation,
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


def run_t1_target(args: argparse.Namespace) -> int:
    result = generate_t1_target(
        args.t1,
        args.target,
        args.output,
        deformation_field=args.deformation,
        spm_exe=Path(args.spm_exe) if args.spm_exe else None,
        spm_output_dir=Path(args.spm_dir) if args.spm_dir else None,
        timeout=args.timeout,
    )
    print(result["output_path"])
    if "metrics" in result:
        print(result["metrics"])
    return 0


def run_deform(args: argparse.Namespace) -> int:
    img, data = apply_deformation(
        args.source,
        args.deformation,
        args.output,
        order=args.order,
        one_based=not args.zero_based,
        coordinate_system=args.coordinate_system,
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


def run_view_report(args: argparse.Namespace) -> int:
    path = render_viewer_report(
        args.reference,
        args.output,
        target_image=args.target,
        slices=args.slices,
        max_dim=args.max_dim,
    )
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


def run_compare_correlations(args: argparse.Namespace) -> int:
    r1 = np.array([float(x) for x in args.r1.split(",")])
    r2 = np.array([float(x) for x in args.r2.split(",")])
    if r1.size != r2.size:
        raise ValueError("r1 and r2 must have the same number of values")
    z, p = compare_correlation_coefficients(r1, r2, args.n1, args.n2, tail=args.tail)
    np.savetxt(args.output, np.column_stack([r1, r2, z, p]), fmt="%.10f")
    print(args.output)
    return 0


def run_chi_square(args: argparse.Namespace) -> int:
    observed = np.loadtxt(args.matrix)
    p = chi_square_test(observed)
    Path(args.output).write_text(f"{p:.10f}\n", encoding="utf-8")
    print(args.output, p)
    return 0


def run_ttest2_covariates(args: argparse.Namespace) -> int:
    y = np.loadtxt(args.y)
    group = np.loadtxt(args.group)
    covs = np.loadtxt(args.covs)
    t, p = ttest2_with_covariates(y, group, covs)
    Path(args.output_json).write_text(json.dumps({"t": t, "p": p}), encoding="utf-8")
    print(args.output_json)
    return 0


def run_quantreg(args: argparse.Namespace) -> int:
    x = np.loadtxt(args.x)
    y = np.loadtxt(args.y)
    result = quantile_regression(
        x,
        y,
        args.tau,
        order=args.order,
        nboot=args.nboot,
        random_seed=args.random_seed,
    )
    serializable = {
        key: value.tolist() if isinstance(value, np.ndarray) else value
        for key, value in result.items()
    }
    Path(args.output_json).write_text(json.dumps(serializable), encoding="utf-8")
    print(args.output_json)
    return 0


def run_permutation_ttest(args: argparse.Namespace) -> int:
    y = np.loadtxt(args.y)
    group = np.loadtxt(args.group)
    result = permutation_ttest(
        y,
        group,
        n_permutations=args.n_permutations,
        random_seed=args.random_seed,
    )
    Path(args.output_json).write_text(json.dumps(result), encoding="utf-8")
    print(args.output_json)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
