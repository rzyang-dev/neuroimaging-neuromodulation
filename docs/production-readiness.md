# Production Readiness Checklist

Status date: 2026-08-03

## Environment and Packaging

- [x] Python package with `pyproject.toml`
- [x] Isolated `.venv` used for all development
- [x] Editable install works
- [x] Wheel build verified with `pip wheel`
- [x] GitHub Actions CI workflow for Python 3.10-3.12 on Ubuntu, macOS, and
  Windows
- [x] Full test suite verified locally on Python 3.10 and 3.14
- [x] CLI entry points installed: `nm-toolbox`, `nm-tms`, `nm-wm`,
  `nm-preprocess`, `nm-diffusion`, `nm-dicom`
- [x] Optional Tkinter desktop GUI

## Data-Oriented Core

- [x] NIfTI loading/saving and world-space resampling
- [x] SPM-style inverse deformation-field application
- [x] DICOM series/directory conversion
- [x] DICOM inspection and single-series validation
- [x] Six-vendor DICOM conversion coverage
- [x] Compressed and enhanced multiframe DICOM conversion coverage
- [x] DICOM validation with real Hitachi data
- [x] fMRI preprocessing: slice timing, motion estimation/resampling,
  coregistration, smoothing, filtering, left-right flipping
- [x] Seed-based FC, ALFF/fALFF, nuisance regression
- [x] ROI, depth mask, target site, largest-cluster target selection
- [x] DTI fitting, deterministic/probabilistic tensor tractography,
  seed-target connectivity
- [x] Approximate GM/WM/CSF tissue probability estimation
- [x] DIPY nonlinear deformation estimation and SPM-style `y_`/`iy_` conversion
- [x] Config-driven end-to-end pipeline (`nm-pipeline`)
- [x] Quantitative image/deformation validation commands
- [x] Optional FSL/MRtrix wrappers with dry-run support
- [x] FSL/MRtrix availability health check
- [x] HTML reports and SHA-256 manifests

## Verification

- [x] `68` automated tests pass on Python 3.10 and 3.14
- [x] GitHub Actions matrix passes on Ubuntu, macOS, and Windows for Python
  3.10-3.12
- [x] Tests use real public fMRI, diffusion, DICOM, T1, template, and mask data
- [x] CLI smoke tests run on real data

## Honest Remaining Work

- Optional hardening: SPM/DARTEL reference comparison, FSL/MRtrix execution
  against installed binaries, and more unusual DICOM sequences

The full algorithm inventory and issue list are in `docs/analysis.md` and
`docs/issues.md`. Requirement-by-requirement evidence is in
`docs/completion-audit.md`.
