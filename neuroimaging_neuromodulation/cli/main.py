"""Unified command-line entry point."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

from .. import __version__
from ..paths import package_data_dir, package_dir


def _fetch_demo_data(output_dir: str) -> int:
    try:
        from nilearn import datasets
    except ImportError:
        print(
            "demo-data requires the optional 'demo' extra: "
            "`pip install neuroimaging-neuromodulation[demo]`."
        )
        return 1

    data = datasets.fetch_development_fmri(
        n_subjects=1,
        data_dir=output_dir,
        age_group="adult",
        reduce_confounds=False,
    )
    print(data.func[0])
    print(f"TR={data.t_r}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nm-toolbox",
        description=(
            "Neuroimaging and Neuromodulation Python toolbox. "
            "Run 'nm-toolbox tms --help', 'nm-toolbox wm --help', or "
            "'nm-toolbox preprocess --help' for pipelines. "
            "Run 'nm-toolbox diffusion --help' for DTI tools and "
            "'nm-toolbox dicom --help' for DICOM conversion. "
            "Run 'nm-toolbox pipeline --help' for end-to-end workflows."
        ),
    )
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    gui = subparsers.add_parser("gui", help="Launch the optional desktop GUI")
    gui.set_defaults(handler=lambda _args: _launch_gui())

    info = subparsers.add_parser("info", help="Print package and data information")
    info.set_defaults(handler=_run_info)

    doctor = subparsers.add_parser("doctor", help="Check package health and optional runtimes")
    doctor.add_argument("--json", action="store_true", help="Print a JSON report")
    doctor.set_defaults(handler=_run_doctor)

    demo = subparsers.add_parser("demo-data", help="Download one real public fMRI subject")
    demo.add_argument("--output-dir", default="data/real_development_fmri")
    demo.set_defaults(handler=lambda args: _fetch_demo_data(args.output_dir))

    return parser


def _launch_gui() -> int:
    try:
        from ..gui.enduser import main as launch_gui
    except ImportError:
        print("Tkinter is not available in this Python installation.")
        return 1
    return launch_gui()


def _run_info(_args: argparse.Namespace) -> int:
    from ..io.nifti import load_volume

    pkg_dir = package_dir()
    data_dir = package_data_dir()
    info = {
        "version": __version__,
        "package_dir": str(pkg_dir),
    }
    for name in ["BrainMask_05_61x73x61.nii", "WhiteMask_09_61x73x61.nii"]:
        path = data_dir / name
        if path.exists():
            img, data = load_volume(path)
            info[name] = {
                "shape": list(img.shape),
                "zooms": list(img.header.get_zooms()),
                "nonzero": int((data > 0).sum()),
            }
    print(json.dumps(info, indent=2, default=str))
    return 0


def _run_doctor(args: argparse.Namespace) -> int:
    from ..runtime.diagnostics import check_system, render_doctor_report

    report = check_system()
    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        print(render_doctor_report(report))
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "tms":
        module = importlib.import_module("neuroimaging_neuromodulation.cli.tms")
        return module.main(argv[1:])
    if argv and argv[0] == "wm":
        module = importlib.import_module("neuroimaging_neuromodulation.cli.wm")
        return module.main(argv[1:])
    if argv and argv[0] == "preprocess":
        module = importlib.import_module("neuroimaging_neuromodulation.cli.preprocess")
        return module.main(argv[1:])
    if argv and argv[0] == "diffusion":
        module = importlib.import_module("neuroimaging_neuromodulation.cli.diffusion")
        return module.main(argv[1:])
    if argv and argv[0] == "dicom":
        module = importlib.import_module("neuroimaging_neuromodulation.cli.dicom")
        return module.main(argv[1:])
    if argv and argv[0] == "pipeline":
        module = importlib.import_module("neuroimaging_neuromodulation.cli.pipeline")
        return module.main(argv[1:])
    args = build_parser().parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
