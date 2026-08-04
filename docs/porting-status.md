# Porting Status

Status date: 2026-08-04

This document is the authoritative status record for the migration from the
original `Neuroimaging-and-Neuromodulation` MATLAB toolbox to the Python
package. The status is **partial / alpha**. It is updated when code, tests, or
documentation change.

## Requirement Status

| Requirement | Evidence | Status |
| --- | --- | --- |
| Use an isolated virtual environment | `.venv/` exists and the package is installed in it | Met |
| Do not use mock data | Real DICOM, fMRI, diffusion, T1, template, and mask data are committed or fetched by dependency tests | Met |
| Keep comprehensive records | `docs/analysis.md`, `docs/decisions.md`, `docs/issues.md`, `docs/testing.md`, `docs/design.md`, and this file | Met |
| Prefer lightweight Python implementations where possible | Core uses NumPy, SciPy, NiBabel, Nilearn, DIPY, and dicom2nifti | Met |
| No MATLAB required for the implemented subset | The implemented commands are Python-native | Met for implemented subset |
| Full source-to-Python port of the original algorithms | Only a subset is mapped in `docs/analysis.md`; many original `.m`/`.sh` workflows are absent | Not met |
| Production-ready package | Wheel builds and tests pass, but package is classified Alpha and lacks reference validation, full workflow coverage, and production UI hardening | Not met |

## Implemented Subset

The following areas have working Python-native implementations, with the
noted limitations:

- NIfTI I/O, resampling, and coordinate transforms
- World-space image reslicing onto a reference grid
- Seed-based FC, fast Pearson correlation, ideal filtering, ALFF/fALFF, nuisance
  regression, Friston-24 regressors, and leave-one-out GFC classification
- ROI-wise functional-connectivity matrix computation
- White-matter seed FC, multi-seed FC, dynamic ALFF, group GM/WM masks, and JHU
  tract-overlap reporting
- Group-level statistical helpers: correlation comparison, chi-square test,
  quantile regression, covariate-adjusted t-test, and permutation t-test
- Sphere ROI, ROI dilation, deep-target coordinates, largest-cluster target
  selection, and target-site generation from a precomputed FC map
- Individualized target-mask workflow exposed through `nm-tms seed-fc` and
  `nm-pipeline`
- T1-space target image generation through `nm-tms t1-target` and
  `nm-pipeline`, with optional SPM25 standalone segmentation for `y_` fields
- Head-motion QC metrics (`FD_VanDijk`, `FD_Power`, `FD_Jenkinson`, and summary)
- Approximate outer-brain c6 mask construction
- DICOM inspection and conversion through `dicom2nifti`
- DICOM series selection by index in `nm-dicom` and `nm-pipeline`
- DIPY-based motion estimation, coregistration, nonlinear deformation
  estimation with SPM world-coordinate `y_`/`iy_` output, DTI fitting, and
  deterministic/probabilistic tensor tractography
- Tract-profile extraction from TRK/TCK streamlines and scalar images
- Atlas-based streamline tract segmentation using JHU-style label maps
- ROI-based AFQ tract segmentation using the original Mori/JHU waypoint ROIs
  and probability atlas
- Deformation-field transform for native-to-MNI streamline normalization
- Optional ANTs registration and transform-application command builders
- AFQ-style streamline outlier cleaning using length and per-node Mahalanobis
  distance criteria
- Subject-level AFQ pipeline combining atlas segmentation, outlier cleaning,
  and scalar tract-profile extraction, with atlas- or ROI-based segmentation
  methods
- HTML tract QC reports combining profile statistics, plots, and segmentation
  counts
- HTML/SVG image QC viewer with axial slices and target overlays
- HTML/SVG streamline rendering with axial, coronal, and sagittal projections
- AFQ-style group profile plots and per-node profile statistics
- FSL/MRtrix command builders for BET, eddy correction, FA/T1 transforms,
  native/MNI transforms, topup, bedpostx, dtifit, probtrackx, and tckgen
- Session concatenation/merging, image combination, directory-of-3D signal
  extraction, timepoint counting, detrending, text-to-NIfTI, and world-space
  reslicing
- HTML reports and SHA-256 manifests
- CLI entry points and optional Tkinter interfaces

## Not Yet Ported or Verified

### White-matter and AFQ workflows

- Full AFQ 20-tract segmentation with validated ANTs integration and
  interactive 3D fiber rendering
- Full `TrackQC` fiber-rendering visualization and the
  `TractMS2Nii`/`TMSmerge.sh`/`TwoSamTTest.sh` statistical workflow

### T1 target workflows

- Full `TMStargetT1` workflow inside the desktop apps, including interactive
  SPM/DARTEL segmentation setup

### Diffusion preprocessing and full tractography workflow

- Full AFQ tract segmentation

### SPM/DARTEL-equivalent preprocessing

- DARTEL-grade segmentation
- SPM/FSL reference comparisons for motion, coregistration, and normalization

## Verification Evidence

- Independent numerical-reference tests for ideal filtering and head-motion
  metrics
- External-execution tests for FSL BET, eddy_correct, and MRtrix tckgen that
  skip when binaries are not installed; first run against installed binaries on
  2026-08-04: 3/3 pass (see External Runtime Environment below)
- SPM25 reference validation on 2026-08-04: applying the SPM `y_T1.nii`
  template-to-native field with the package reproduces SPM's `wc1T1.nii`
  warped tissue output (correlation > 0.99)
- ANTs execution tests that skip when binaries are not installed; first run
  against installed ANTs 2.6.5 on 2026-08-04: 2/2 pass
- Local test suite: `130 tests collected` and passing
- `pip check`: no broken requirements
- Wheel: `dist/neuroimaging_neuromodulation-0.19.0-py3-none-any.whl`
- CI claim: recorded in `docs/ci-validation.md`, but not independently
  reproducible from repository artifacts in this workspace

This file must be updated before any future claim that the migration is
complete.

## External Runtime Environment

As of 2026-08-04 the external runtimes below are installed and usable for
reference/comparison work. The execution tests were run for the first time on
2026-08-04; SPM `y_`/`iy_` convention validation is now implemented, while
DARTEL-grade normalization and motion/coregistration reference comparisons are
still not implemented:

- MATLAB R2015b and SPM standalone 25.01.02 are installed on Windows
  (`C:\Program Files\MATLAB\R2015b\bin`,
  `C:\Users\ginger\spm_standalone_25.01.02_Windows`); SPM/DARTEL parity
  comparisons can be executed but are not yet implemented.
- FSL 6.0.7.23 and MRtrix 3.0.4 are installed inside WSL (Ubuntu). FSL
  binaries (`bet`, `dtifit`, `probtrackx2`, `bedpostx`) require
  `source /home/dev/fsl/etc/fslconf/fsl.sh`; MRtrix `tckgen` is on the default
  PATH. `nm-diffusion check-external` reports all four supported binaries
  available inside WSL. `tests/test_external_execution.py` was run on
  2026-08-04 from the WSL dev environment (`~/nm-dev-venv`, editable install
  `~/nm-src`, verified in sync with this workspace by MD5 on the involved
  files): 3/3 pass.
  - `test_fsl_eddy_correct_execution`: pass.
  - `test_fsl_bet_execution`: pass on a realistic 32x32x32 ellipsoid fixture.
  - `test_mrtrix_tckgen_execution`: pass with the new `-seed_image` option and
    the `SeedTest` algorithm.
- ANTs 2.6.5 is installed on Windows (`C:\Program Files\ants-2.6.5\bin`) and
  has been added to the user PATH (2026-08-04). `tests/test_ants_execution.py`
  was run on 2026-08-04 with `.venv-win` (`antsRegistration --version`,
  `antsApplyTransforms --help`): 2/2 pass.
- Interactive 3D fiber rendering still requires a rendering runtime that is
  not part of this environment.

The Python-native port is substantially implemented, and SPM `y_`/`iy_`
world-coordinate convention validation now passes against SPM25. DARTEL-grade
normalization and FSL reference comparisons remain unproven. ANTs execution
tests pass (2/2); FSL/MRtrix execution smoke tests pass (3/3) as of 2026-08-04.
