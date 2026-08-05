# Roadmap and Release Gates

Status date: 2026-08-05

The project target is a Python-native, production-ready package for academic
researchers and general users. Normal use must not require MATLAB, SPM, FSL,
DARTEL, ANTs, SimNIBS, or DIPY.

## Current Status

- Version: `0.20.0`
- Tests: `181` collected and passing locally
- Minimal core: NumPy, SciPy, NiBabel
- Optional extras: DIPY, DICOM libraries, Nilearn demo
- Optional external providers: SPM, FSL, ANTs, SimNIBS
- CI: Python 3.10-3.14 on Ubuntu, macOS, and Windows
- Release: tag-triggered wheel build workflow

## Milestones

### 0.20.0: Corrected architecture

Completed:

- Split mandatory and optional dependencies.
- Added `nm-toolbox doctor`.
- Added runtime-provider boundary.
- Added gap matrix and corrected decision records.
- Added Python-native white-matter, target, and QC workflows.
- Added pipeline validation and reproducibility manifests.
- Added GUI launch smoke tests and guided end-user options.
- Added minimal-core CI and wheel release workflow.

### 0.21.0: Python-native core completion

Completed:

- NumPy/SciPy motion estimation and coregistration.
- NumPy/SciPy DTI fitting.
- NumPy/SciPy deterministic and probabilistic tractography.
- NumPy/SciPy streamline connectivity and I/O.
- NumPy/SciPy nonlinear deformation estimation.

Remaining for this milestone:

- Full AFQ/TrackQC numerical parity against reference outputs.
- Validation of the internal deformation engine on real clinical-scale data.
- Optional DIPY engine remains available but must not be required.

### 0.22.0: Workflow completion

Target:

- Complete AFQ/TrackQC reference validation.
- Add remaining original white-matter/statistical workflows from the gap matrix.
- Expose completed workflows in CLI, `nm-pipeline`, `nm-app`, and `nm-gui`.

### 0.30.0: Production hardening

Target:

- Platform installers for Windows, macOS, and Linux where practical.
- GUI behavior tests beyond launch/config construction.
- Atomic output handling, crash recovery, and user-facing error reporting.
- Signed or checksummed release artifacts.
- Independent CI artifact reproducibility.

### 1.0.0: Production release

Release gates:

- Full test suite passes on all supported platforms.
- Minimal-core install works without optional dependencies.
- Wheel and installer builds succeed.
- `pip check` passes.
- Gap matrix has no stale `ported` claims.
- Every shipped workflow has at least one real-data test.
- Outputs include package, parameter, provider, and checksum metadata.
- Docs and release notes describe exact supported behavior and limitations.

## Completion Rule

The project is production-ready only when all `1.0.0` gates are independently
verified. Until then, the package remains in active development and status
documents must not claim production readiness.
