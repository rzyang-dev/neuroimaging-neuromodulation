"""Production health checks for the Python-native package.

The normal analysis path must not require MATLAB, SPM, FSL, DARTEL, ANTs,
SimNIBS, or any optional Python extra. This module reports whether those
optional components are available without importing them.
"""

from __future__ import annotations

import importlib.util
import os
import platform
import shutil
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from .. import __version__
from ..paths import package_data_dir, package_dir

CORE_DEPENDENCIES = ("numpy", "scipy", "nibabel")

OPTIONAL_DEPENDENCIES = {
    "nilearn": "demo",
    "dipy": "diffusion",
    "pydicom": "dicom",
    "dicom2nifti": "dicom",
}

PROVIDER_SPECS = {
    "spm": {
        "env_var": "NM_SPM_EXECUTABLE",
        "executables": ("spm12", "spm12_mcr", "run_spm12.sh"),
        "description": "SPM standalone, optional validation provider",
    },
    "fsl": {
        "env_var": "NM_FSL_DIR",
        "executables": ("fsl", "bet", "randomise"),
        "description": "FSL, optional external provider",
    },
    "ants": {
        "env_var": "NM_ANTS_DIR",
        "executables": ("antsRegistration", "antsApplyTransforms"),
        "description": "ANTs, optional external provider",
    },
    "simnibs": {
        "env_var": "NM_SIMNIBS_BIN",
        "executables": ("simnibs",),
        "description": "SimNIBS, optional external provider",
    },
}


@dataclass(frozen=True)
class DependencyStatus:
    name: str
    extra: str | None
    installed: bool
    detail: str


@dataclass(frozen=True)
class ProviderStatus:
    name: str
    available: bool
    detail: str
    description: str


def _dependency_status(name: str, extra: str | None) -> DependencyStatus:
    spec = importlib.util.find_spec(name)
    if spec is None:
        detail = "not installed"
        if extra:
            detail = f"not installed; optional extra: {extra}"
        return DependencyStatus(name=name, extra=extra, installed=False, detail=detail)
    detail = getattr(spec, "origin", "installed") or "installed"
    return DependencyStatus(name=name, extra=extra, installed=True, detail=detail)


def _provider_path(spec: dict[str, object], name: str) -> Path | None:
    env_var = str(spec["env_var"])
    configured = os.environ.get(env_var)
    if configured:
        candidate = Path(configured)
        if candidate.is_dir():
            for executable in spec["executables"]:
                path = candidate / executable
                if path.is_file():
                    return path
        if candidate.is_file():
            return candidate
    for executable in spec["executables"]:
        found = shutil.which(executable)
        if found:
            return Path(found)
    return None


def discover_optional_providers() -> list[dict[str, object]]:
    """Return availability information for optional external runtimes."""

    providers: list[dict[str, object]] = []
    for name, spec in PROVIDER_SPECS.items():
        path = _provider_path(spec, name)
        if path is None:
            providers.append(
                asdict(
                    ProviderStatus(
                        name=name,
                        available=False,
                        detail="not configured or not found on PATH",
                        description=str(spec["description"]),
                    )
                )
            )
        else:
            providers.append(
                asdict(
                    ProviderStatus(
                        name=name,
                        available=True,
                        detail=str(path),
                        description=str(spec["description"]),
                    )
                )
            )
    return providers


def check_system() -> dict[str, object]:
    """Return a JSON-friendly production health report."""

    pkg_dir = package_dir()
    data_dir = package_data_dir()
    data_files = sorted(path.name for path in data_dir.glob("*.nii*")) if data_dir.exists() else []
    return {
        "package": {
            "name": "neuroimaging-neuromodulation",
            "version": __version__,
            "package_dir": str(pkg_dir),
        },
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python": sys.version.split()[0],
            "executable": sys.executable,
        },
        "core_dependencies": [
            asdict(_dependency_status(name, None)) for name in CORE_DEPENDENCIES
        ],
        "optional_dependencies": [
            asdict(_dependency_status(name, extra))
            for name, extra in OPTIONAL_DEPENDENCIES.items()
        ],
        "optional_providers": discover_optional_providers(),
        "data": {
            "directory": str(data_dir),
            "present": data_dir.exists(),
            "bundled_nifti_files": data_files,
        },
        "environment": {
            "cwd": str(Path.cwd()),
            "cwd_writable": os.access(Path.cwd(), os.W_OK),
        },
    }


def render_doctor_report(report: dict[str, object] | None = None) -> str:
    """Render the doctor report as human-readable text."""

    report = report or check_system()
    lines: list[str] = []
    package = report["package"]
    lines.append(f"nm-toolbox doctor")
    lines.append(f"version: {package['version']}")
    lines.append(f"python: {report['platform']['python']} on {report['platform']['system']} {report['platform']['machine']}")
    for item in report["core_dependencies"]:
        lines.append(f"core dependency {item['name']}: {'ok' if item['installed'] else 'missing'}")
    for item in report["optional_dependencies"]:
        lines.append(f"optional dependency {item['name']} ({item['extra']}): {'ok' if item['installed'] else 'not installed'}")
    for item in report["optional_providers"]:
        state = "ok" if item["available"] else "optional"
        lines.append(f"provider {item['name']}: {state} ({item['detail']})")
    data = report["data"]
    lines.append(f"bundled data: {'present' if data['present'] else 'missing'}")
    lines.append(f"output directory writable: {'yes' if report['environment']['cwd_writable'] else 'no'}")
    return "\n".join(lines)


__all__ = ["check_system", "discover_optional_providers", "render_doctor_report"]
