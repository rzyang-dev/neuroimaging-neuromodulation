"""White-matter fMRI command-line interface."""

from __future__ import annotations

import argparse

from ..wm.alff import compute_alff
from ..wm.masks import make_gm_mask, make_wm_mask


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


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
