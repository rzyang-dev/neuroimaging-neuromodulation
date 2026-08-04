# Production Readiness Checklist

Status date: 2026-08-04

Current status: **not production-ready**. This checklist records what is true
and what remains before the package can be called production-ready.

## Environment and Packaging

- [x] Python package with `pyproject.toml`
- [x] Isolated `.venv` used for development
- [x] Editable install works
- [x] Wheel build verified with `pip wheel`
- [x] GitHub Actions workflow exists
- [ ] CI matrix result independently reproducible from repository artifacts
- [x] CLI entry points installed
- [x] Optional Tkinter desktop GUI
- [ ] GUI behavior verified outside config-construction tests
- [ ] Direct runtime dependency declarations complete (for example, `pydicom`
  is imported directly but only a transitive dependency)

## Data-Oriented Core

- [x] NIfTI loading/saving and world-space resampling
- [x] SPM world-coordinate `y_`/`iy_` deformation application
- [x] DICOM conversion and inspection through `dicom2nifti`
- [x] Six-vendor and compressed DICOM fixture coverage
- [x] DICOM series selection by index in `nm-dicom` and `nm-pipeline`
- [x] fMRI preprocessing primitives: slice timing, motion, coregistration,
  smoothing, filtering, left-right flipping
- [x] SPM motion and coregistration reference comparisons
- [x] Seed-based FC, ALFF/fALFF, nuisance regression
- [x] ROI, depth, target-site, largest-cluster target selection primitives
- [x] Individualized target-mask workflow exposed through CLI and pipeline
- [x] T1-based target generation workflow with optional SPM25 segmentation
- [x] DTI fitting and tensor tractography primitives
- [ ] Full AFQ tract segmentation and tract-profile workflow
- [x] Approximate GM/WM/CSF tissue probability estimation
- [ ] SPM/DARTEL-compatible segmentation and normalization
- [x] Exact `y_`/`iy_` deformation-convention validation against SPM25
- [x] Config-driven pipeline for a subset of workflows
- [x] Quantitative image/deformation validation commands
- [x] FSL/MRtrix command builders and availability check
- [x] FSL/MRtrix execution smoke tests against installed binaries
  (2026-08-04: 3/3 pass; ANTs execution tests pass 3/3)
- [x] HTML reports and SHA-256 manifests

## Verification

- [x] `146` automated tests pass locally
- [ ] Tests prove numerical equivalence to original MATLAB/SPM/FSL workflows
- [ ] Tests cover missing workflows listed in `docs/porting-status.md`
- [x] Tests use real public fMRI, diffusion, DICOM, T1, template, and mask data

The current evidence supports an Alpha research migration, not a production
release. See `docs/porting-status.md` for the authoritative status record.
