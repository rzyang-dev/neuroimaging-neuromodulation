"""Build a local release without CI.

This script is the local alternative to GitHub Actions. It does not trigger
remote workflows and it preserves prior release output by archiving it.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
RELEASE = ROOT / "release"

EXCLUDED_MODULES = (
    "dipy",
    "nilearn",
    "dicom2nifti",
    "pydicom",
    "matplotlib",
    "PIL",
    "sklearn",
    "pandas",
    "plotly",
    "PyQt5",
    "PySide2",
)


def _run(command: list[str], timeout: int) -> None:
    print("$", " ".join(str(item) for item in command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True, timeout=timeout)


def _archive_previous_release() -> None:
    if not RELEASE.exists():
        return
    entries = [path for path in RELEASE.iterdir() if path.name != "archive"]
    if not entries:
        return
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive_dir = RELEASE / "archive" / timestamp
    archive_dir.mkdir(parents=True, exist_ok=True)
    for path in entries:
        shutil.move(str(path), str(archive_dir / path.name))
    print(f"Archived previous release to {archive_dir}")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _data_arg() -> str:
    source = "neuroimaging_neuromodulation/data"
    target = "neuroimaging_neuromodulation/data"
    return source + os.pathsep + target


def _pyinstaller_args(name: str, windowed: bool, launcher: str) -> list[str]:
    args = [
        PYTHON,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onedir",
        "--name",
        name,
        "--paths",
        ".",
        "--collect-submodules",
        "neuroimaging_neuromodulation",
        "--add-data",
        _data_arg(),
        "--contents-directory",
        "_internal",
    ]
    if windowed:
        args.append("--windowed")
    for module in EXCLUDED_MODULES:
        args.extend(["--exclude-module", module])
    args.append(launcher)
    return args


def _build_gui(name: str, launcher: str, timeout: int) -> None:
    try:
        _run(_pyinstaller_args(name, True, launcher), timeout)
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as exc:
        error_path = RELEASE / "gui-build-errors.txt"
        with error_path.open("a", encoding="utf-8") as handle:
            handle.write(f"{datetime.now(timezone.utc).isoformat()} {name}: {exc}\n")
        print(f"WARNING: {name} build did not complete; recorded in {error_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a local release without CI")
    parser.add_argument("--run-tests", action="store_true", help="Run the full test suite")
    parser.add_argument("--build-gui", action="store_true", help="Attempt GUI executable builds")
    parser.add_argument("--timeout", type=int, default=600, help="Per-build timeout in seconds")
    args = parser.parse_args()

    _archive_previous_release()
    RELEASE.mkdir(parents=True, exist_ok=True)

    _run([PYTHON, "scripts/check_release_gates.py"], 60)
    if args.run_tests:
        _run([PYTHON, "-m", "pytest", "-q"], 900)
    _run([PYTHON, "-m", "pip", "check"], 60)

    wheel_dir = RELEASE / "wheels"
    wheel_dir.mkdir(parents=True, exist_ok=True)
    _run([PYTHON, "-m", "pip", "wheel", ".", "--no-deps", "-w", str(wheel_dir)], 300)

    binaries = RELEASE / "binaries"
    binaries.mkdir(parents=True, exist_ok=True)
    _run(_pyinstaller_args("nm-toolbox", False, "packaging/launch_nm_toolbox.py"), args.timeout)
    cli_source = ROOT / "dist" / "nm-toolbox"
    cli_dest = binaries / "nm-toolbox"
    if cli_dest.exists():
        shutil.rmtree(cli_dest)
    shutil.copytree(cli_source, cli_dest)
    cli_executable = cli_dest / ("nm-toolbox.exe" if os.name == "nt" else "nm-toolbox")
    if not cli_executable.exists():
        raise SystemExit(f"Packaged CLI executable not found: {cli_executable}")
    _run([str(cli_executable), "doctor", "--json"], 120)

    if args.build_gui:
        _build_gui("nm-app", "packaging/launch_nm_app.py", args.timeout)
        _build_gui("nm-gui", "packaging/launch_nm_gui.py", args.timeout)
        for name in ("nm-app", "nm-gui"):
            source = ROOT / "dist" / name
            if source.exists():
                dest = binaries / name
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(source, dest)
                print(f"Copied {name} bundle to {dest}")

    validation_dir = RELEASE / "validation"
    validation_dir.mkdir(parents=True, exist_ok=True)
    for json_path in (ROOT / "data" / "validation").glob("*.json"):
        shutil.copy2(json_path, validation_dir / json_path.name)

    archive_dir = RELEASE / "archives"
    archive_dir.mkdir(parents=True, exist_ok=True)
    wheel = next(wheel_dir.glob("*.whl"), None)
    if wheel is None:
        raise SystemExit("No wheel was produced")
    archive_stem = archive_dir / wheel.stem
    shutil.make_archive(str(archive_stem), "zip", wheel.parent, wheel.name)
    cli_archive_stem = archive_dir / "nm-toolbox-local"
    shutil.make_archive(str(cli_archive_stem), "zip", cli_dest)

    checksum_lines = []
    for path in sorted(RELEASE.rglob("*")):
        if path.is_file() and path.suffix not in {".json"}:
            checksum_lines.append(f"{_sha256(path)}  {path.relative_to(RELEASE)}")
    (RELEASE / "checksums.txt").write_text(
        "\n".join(checksum_lines) + "\n",
        encoding="utf-8",
    )

    release_readme = RELEASE / "README.md"
    release_readme.write_text(
        "\n".join(
            [
                "# Local Release",
                "",
                f"Built: {datetime.now(timezone.utc).isoformat()}",
                "",
                "Contents:",
                "- `wheels/`: installable Python wheel",
                "- `binaries/`: locally built executable bundle",
                "- `binaries/nm-app/`: guided GUI bundle when built",
                "- `binaries/nm-gui/`: advanced GUI bundle when built",
                "- `validation/`: recorded local validation JSON",
                "- `archives/`: wheel and CLI zip archives",
                "- `checksums.txt`: SHA-256 checksums",
                "",
                "Build without CI: `python scripts/build_local.py --run-tests --build-gui`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"Local release written to {RELEASE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
