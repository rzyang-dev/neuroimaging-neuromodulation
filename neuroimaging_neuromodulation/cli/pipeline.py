"""Config-driven pipeline command-line interface."""

from __future__ import annotations

import argparse
import json

from ..pipeline.run import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nm-pipeline",
        description="Run a config-driven neuroimaging analysis pipeline",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="Run a pipeline from a JSON config")
    run.add_argument("config", help="Path to pipeline config JSON")
    run.set_defaults(handler=run_pipeline_command)

    return parser


def run_pipeline_command(args: argparse.Namespace) -> int:
    result = run_pipeline(args.config)
    print(json.dumps(result, indent=2, default=str))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
