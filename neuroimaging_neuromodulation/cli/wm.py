"""White-matter fMRI command-line interface."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..wm.alff import compute_alff
from ..wm.dynamic import dynamic_alff
from ..wm.group import group_probability_maps
from ..wm.masks import make_gm_mask, make_wm_mask
from ..wm.ms2nii import tract_measures_to_nifti
from ..wm.plots import plot_group_profiles
from ..wm.seedfc import wm_multi_seed_fc, wm_seed_fc
from ..wm.statistics import profile_group_statistics
from ..wm.trackqc import tract_qc_report
from ..wm.tracts import cluster_report_in_jhu


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nm-wm",
        description="Python-native white-matter fMRI tools",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    alff = subparsers.add_parser("alff", help="Compute ALFF/fALFF maps")
    alff.add_argument("--functional", required=True)
    alff.add_argument("--mask", required=True)
    alff.add_argument("--output-dir", required=True)
    alff.add_argument("--tr", type=float, required=True)
    alff.add_argument("--low-cutoff", type=float, default=0.01)
    alff.add_argument("--high-cutoff", type=float, default=0.1)
    alff.add_argument("--prefix", default="ALFF")
    alff.set_defaults(handler=run_alff)

    wm_mask = subparsers.add_parser("wm-mask", help="Build a functional-space WM mask")
    wm_mask.add_argument("--functional", required=True)
    wm_mask.add_argument("--segment", required=True, help="c2 white-matter segment NIfTI")
    wm_mask.add_argument("--exclude", required=True, help="HOA exclusion NIfTI")
    wm_mask.add_argument("--output-dir", required=True)
    wm_mask.add_argument("--threshold", type=float, default=0.9)
    wm_mask.set_defaults(handler=run_wm_mask)

    gm_mask = subparsers.add_parser("gm-mask", help="Build a functional-space GM mask")
    gm_mask.add_argument("--functional", required=True)
    gm_mask.add_argument("--segment", required=True, help="c1 grey-matter segment NIfTI")
    gm_mask.add_argument("--exclude", required=True, help="HOA exclusion NIfTI")
    gm_mask.add_argument("--output-dir", required=True)
    gm_mask.add_argument("--threshold", type=float, default=0.1)
    gm_mask.set_defaults(handler=run_gm_mask)

    seed_fc = subparsers.add_parser("seed-fc", help="Compute white-matter seed FC")
    seed_fc.add_argument("--functional", required=True)
    seed_fc.add_argument("--seed", required=True)
    seed_fc.add_argument("--mask", required=True)
    seed_fc.add_argument("--output", required=True, help="Output Fisher z FC map NIfTI")
    seed_fc.set_defaults(handler=run_seed_fc)

    multi_seed_fc = subparsers.add_parser("multi-seed-fc", help="Compute FC for multiple white-matter seeds")
    multi_seed_fc.add_argument("--functional", required=True)
    multi_seed_fc.add_argument("--seeds", nargs="+", required=True)
    multi_seed_fc.add_argument("--mask", required=True)
    multi_seed_fc.add_argument("--output-dir", required=True)
    multi_seed_fc.set_defaults(handler=run_multi_seed_fc)

    cluster = subparsers.add_parser("cluster-report", help="Report result overlap with JHU tracts")
    cluster.add_argument("--result", required=True)
    cluster.add_argument("--template", default=None, help="JHU tract label NIfTI")
    cluster.add_argument("--output-dir", required=True)
    cluster.add_argument("--labels", default=None, help="Optional JHU label text file")
    cluster.set_defaults(handler=run_cluster_report)

    d_alff = subparsers.add_parser("dynamic-alff", help="Compute dynamic ALFF maps")
    d_alff.add_argument("--functional", required=True)
    d_alff.add_argument("--mask", required=True)
    d_alff.add_argument("--output-dir", required=True)
    d_alff.add_argument("--tr", type=float, required=True)
    d_alff.add_argument("--low-cutoff", type=float, default=0.01)
    d_alff.add_argument("--high-cutoff", type=float, default=0.1)
    d_alff.add_argument("--window-length", type=int, default=50)
    d_alff.add_argument("--step", type=int, default=5)
    d_alff.set_defaults(handler=run_dynamic_alff)

    group = subparsers.add_parser("group-mask", help="Build a group GM/WM mask from segment maps")
    group.add_argument("--segments", nargs="+", required=True)
    group.add_argument("--output", required=True)
    group.add_argument("--threshold", type=float, default=0.9)
    group.add_argument("--group-threshold", type=float, default=None)
    group.set_defaults(handler=run_group_mask)

    plot = subparsers.add_parser("plot-profiles", help="Plot AFQ-style group tract profiles as SVG")
    plot.add_argument("--profiles", nargs="+", required=True, help="Profile matrices (.npy or text)")
    plot.add_argument("--n-group1", type=int, required=True)
    plot.add_argument("--output-dir", required=True)
    plot.add_argument("--labels", nargs="*", default=None)
    plot.add_argument("--title-prefix", default="Tract")
    plot.set_defaults(handler=run_plot_profiles)

    afq_stat = subparsers.add_parser("afq-stat", help="Run AFQ-style group profile statistics")
    afq_stat.add_argument("--profiles", nargs="+", required=True)
    afq_stat.add_argument("--n-group1", type=int, required=True)
    afq_stat.add_argument("--labels", nargs="*", default=None)
    afq_stat.add_argument("--output-json", required=True)
    afq_stat.set_defaults(handler=run_afq_stat)

    qc = subparsers.add_parser("tract-qc", help="Generate an HTML tract QC report")
    qc.add_argument("--profiles", nargs="+", required=True)
    qc.add_argument("--n-group1", type=int, required=True)
    qc.add_argument("--labels", nargs="*", default=None)
    qc.add_argument("--segmentation-json")
    qc.add_argument("--render-html", help="Optional interactive 3D fiber viewer HTML")
    qc.add_argument("--output-dir", required=True)
    qc.set_defaults(handler=run_tract_qc)

    ms2nii = subparsers.add_parser("tract-ms2nii", help="Convert tract measures to NIfTI/4D for group analysis")
    ms2nii.add_argument("--profiles", nargs="+", required=True, help="Per-subject tract profile matrices (.npy or text)")
    ms2nii.add_argument("--subject-names", nargs="*", default=None)
    ms2nii.add_argument("--n-tracts", type=int, default=18)
    ms2nii.add_argument("--output-dir", required=True)
    ms2nii.set_defaults(handler=run_tract_ms2nii)

    randomise = subparsers.add_parser("randomise", help="Run FSL two-sample Randomise workflow")
    randomise.add_argument("--input", required=True, help="Merged 4D NIfTI")
    randomise.add_argument("--mask", required=True, help="Analysis mask NIfTI")
    randomise.add_argument("--output-prefix", required=True)
    randomise.add_argument("--n-group1", type=int, required=True)
    randomise.add_argument("--n-group2", type=int, required=True)
    randomise.add_argument("--design-prefix", default=None)
    randomise.add_argument("--n-permutations", type=int, default=5000)
    randomise.add_argument("--no-tfce", action="store_true")
    randomise.add_argument("--dry-run", action="store_true")
    randomise.set_defaults(handler=run_randomise)

    return parser


def run_alff(args: argparse.Namespace) -> int:
    paths = compute_alff(
        args.functional,
        args.mask,
        args.output_dir,
        tr=args.tr,
        low_cutoff=args.low_cutoff,
        high_cutoff=args.high_cutoff,
        prefix=args.prefix,
    )
    for key, path in paths.items():
        print(key, path)
    return 0


def run_wm_mask(args: argparse.Namespace) -> int:
    path, _ = make_wm_mask(
        args.functional,
        args.segment,
        args.exclude,
        args.output_dir,
        threshold=args.threshold,
    )
    print(path)
    return 0


def run_gm_mask(args: argparse.Namespace) -> int:
    path, _ = make_gm_mask(
        args.functional,
        args.segment,
        args.exclude,
        args.output_dir,
        threshold=args.threshold,
    )
    print(path)
    return 0


def run_seed_fc(args: argparse.Namespace) -> int:
    path, _ = wm_seed_fc(
        args.functional,
        args.seed,
        args.mask,
        output_path=args.output,
    )
    print(path)
    return 0


def run_multi_seed_fc(args: argparse.Namespace) -> int:
    results = wm_multi_seed_fc(
        args.functional,
        [Path(seed) for seed in args.seeds],
        args.mask,
        output_dir=args.output_dir,
    )
    for name, (path, _) in results.items():
        print(name, path)
    return 0


def run_cluster_report(args: argparse.Namespace) -> int:
    package_data = Path(__file__).resolve().parents[1] / "data"
    template = args.template or package_data / "JHUtractsThr25_3mm.nii"
    report = cluster_report_in_jhu(
        args.result,
        template,
        args.output_dir,
        labels_file=args.labels,
    )
    print(report)
    return 0


def run_dynamic_alff(args: argparse.Namespace) -> int:
    result = dynamic_alff(
        args.functional,
        args.mask,
        args.output_dir,
        tr=args.tr,
        low_cutoff=args.low_cutoff,
        high_cutoff=args.high_cutoff,
        window_length=args.window_length,
        step=args.step,
    )
    print(result["dALFF"])
    print(len(result["windows"]))
    return 0


def run_group_mask(args: argparse.Namespace) -> int:
    path, _ = group_probability_maps(
        args.segments,
        args.output,
        threshold=args.threshold,
        output_threshold=args.group_threshold,
    )
    print(path)
    return 0


def run_plot_profiles(args: argparse.Namespace) -> int:
    paths = plot_group_profiles(
        args.profiles,
        args.output_dir,
        n_group1=args.n_group1,
        labels=args.labels,
        title_prefix=args.title_prefix,
    )
    for path in paths:
        print(path)
    return 0


def run_afq_stat(args: argparse.Namespace) -> int:
    import json

    result = profile_group_statistics(
        args.profiles,
        n_group1=args.n_group1,
        labels=args.labels,
    )
    Path(args.output_json).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(args.output_json)
    return 0


def run_tract_qc(args: argparse.Namespace) -> int:
    report = tract_qc_report(
        args.profiles,
        args.output_dir,
        n_group1=args.n_group1,
        labels=args.labels,
        segmentation_json=args.segmentation_json,
        render_html=args.render_html,
    )
    print(report)
    return 0


def run_tract_ms2nii(args: argparse.Namespace) -> int:
    result = tract_measures_to_nifti(
        args.profiles,
        args.output_dir,
        subject_names=args.subject_names,
        n_tracts=args.n_tracts,
    )
    for subject_path in result["subject_images"]:
        print(subject_path)
    print(result["merged"])
    print(result["mask"])
    return 0


def run_randomise(args: argparse.Namespace) -> int:
    from ..diffusion.external import (
        build_fsl_design_ttest2_command,
        build_fsl_randomise_command,
        run_fsl_design_ttest2,
        run_fsl_randomise,
    )

    design_prefix = args.design_prefix or str(Path(args.output_prefix).parent / "design")
    design_mat = f"{design_prefix}.mat"
    design_con = f"{design_prefix}.con"
    design_cmd = build_fsl_design_ttest2_command(
        design_prefix,
        args.n_group1,
        args.n_group2,
    )
    randomise_cmd = build_fsl_randomise_command(
        args.input,
        args.output_prefix,
        args.mask,
        design_mat,
        design_con,
        n_permutations=args.n_permutations,
        tfce=not args.no_tfce,
    )
    if args.dry_run:
        print(" ".join(design_cmd))
        print(" ".join(randomise_cmd))
        return 0
    run_fsl_design_ttest2(design_prefix, args.n_group1, args.n_group2)
    run_fsl_randomise(
        args.input,
        args.output_prefix,
        args.mask,
        design_mat,
        design_con,
        n_permutations=args.n_permutations,
        tfce=not args.no_tfce,
    )
    print(args.output_prefix)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
