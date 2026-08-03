"""DICOM conversion command-line interface."""

from __future__ import annotations

import argparse
import json

from ..io.dicom import (
    convert_dicom_directory,
    convert_dicom_series,
    inspect_dicom_directory,
    validate_dicom_series,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nm-dicom",
        description="DICOM-to-NIfTI conversion using dicom2nifti",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    series = subparsers.add_parser("convert-series", help="Convert one DICOM series")
    series.add_argument("--dicom-dir", required=True)
    series.add_argument("--output", required=True, help="Output NIfTI path")
    series.add_argument("--no-reorient", action="store_true")
    series.set_defaults(handler=run_series)

    directory = subparsers.add_parser("convert-dir", help="Convert all DICOM series in a directory")
    directory.add_argument("--dicom-dir", required=True)
    directory.add_argument("--output-dir", required=True)
    directory.add_argument("--no-compression", action="store_true")
    directory.add_argument("--no-reorient", action="store_true")
    directory.set_defaults(handler=run_directory)

    inspect = subparsers.add_parser("inspect", help="Summarize DICOM series metadata")
    inspect.add_argument("--dicom-dir", required=True)
    inspect.add_argument("--output-json")
    inspect.set_defaults(handler=run_inspect)

    validate = subparsers.add_parser("validate-series", help="Validate a directory contains one DICOM series")
    validate.add_argument("--dicom-dir", required=True)
    validate.set_defaults(handler=run_validate)

    return parser


def run_series(args: argparse.Namespace) -> int:
    result = convert_dicom_series(
        args.dicom_dir,
        args.output,
        reorient=not args.no_reorient,
    )
    print(result.get("NII_FILE", args.output))
    return 0


def run_directory(args: argparse.Namespace) -> int:
    files = convert_dicom_directory(
        args.dicom_dir,
        args.output_dir,
        compression=not args.no_compression,
        reorient=not args.no_reorient,
    )
    for path in files:
        print(path)
    return 0


def run_inspect(args: argparse.Namespace) -> int:
    summary = inspect_dicom_directory(args.dicom_dir)
    text = json.dumps(summary, indent=2, default=str)
    if args.output_json:
        from pathlib import Path

        Path(args.output_json).write_text(text, encoding="utf-8")
    print(text)
    return 0


def run_validate(args: argparse.Namespace) -> int:
    series = validate_dicom_series(args.dicom_dir)
    print(json.dumps(series, indent=2, default=str))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
