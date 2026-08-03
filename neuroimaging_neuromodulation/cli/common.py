"""Shared CLI helpers."""

from __future__ import annotations

import argparse


def add_io_arguments(parser: argparse.ArgumentParser) -> None:
    """Add common NIfTI input/output arguments."""

    parser.add_argument("--output-dir", required=True, help="Directory for result files")
    parser.add_argument("--subject", default="subject", help="Subject identifier used in filenames")


def parse_center(value: str) -> list[float]:
    """Parse a comma-separated or space-separated MNI coordinate string."""

    raw = value.replace(",", " ").split()
    if len(raw) != 3:
        raise argparse.ArgumentTypeError("Expected exactly three numbers")
    return [float(item) for item in raw]


__all__ = ["add_io_arguments", "parse_center"]
