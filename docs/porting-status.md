# Porting Status

Status date: 2026-08-05

This document is the authoritative status record for the migration from the
original `Neuroimaging-and-Neuromodulation` MATLAB toolbox to the Python
package. The status is **partial / alpha**. It is updated when code, tests, or
documentation change.

## Requirement Status

| Requirement | Evidence | Status |
| --- | --- | --- |
| Use an isolated virtual environment | `.venv/` exists and the package is installed in it | Met |
| Do not use mock data | Real DICOM, fMRI, diffusion, T1, template, and mask data are committed or fetched by dependency tests | Met |
| Keep comprehensive records | `docs/analysis.md`, `docs/gap-matrix.md`, `docs/roadmap.md`, `docs/decisions.md`, `docs/issues.md`, `docs/testing.md`, `docs/design.md`, and this file | Met |
| Prefer lightweight Python implementations where possible | Core uses NumPy, SciPy, and NiBabel; DIPY, DICOM, and demo libraries are optional extras | Met |
| No MATLAB required for the implemented subset | The implemented commands are Python-native | Met for implemented subset |
| Full source-to-Python port of the original algorithms | Only a subset is mapped in `docs/analysis.md`; many original `.m`/`.sh` workflows are absent | Not met |
| Production-ready package | Wheel builds and tests pass, but package is classified Alpha, reference validation is partial, and full workflow coverage and production UI hardening are missing | Not met |

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
- NumPy/SciPy motion estimation and coregistration
- NumPy/SciPy diffusion tensor fitting
- NumPy/SciPy deterministic tractography and connectivity
- NumPy/SciPy deterministic and probabilistic tensor tractography and
  streamline connectivity
- NumPy/SciPy nonlinear deformation estimation
- Optional DIPY deformation engine for compatibility
- SPM25 standalone segmentation through `nm-preprocess spm-segment`, including
  native `c*` maps, imported `rc*` DARTEL maps, and warped `wc*` maps
- SPM DARTEL template runner through `nm-preprocess dartel-template`
- SPM DARTEL Normalise-to-MNI runner through `nm-preprocess dartel-mni-norm`
- Multi-subject SPM DARTEL reference comparison through `nm-preprocess
  dartel-parity`
- Tract-profile extraction from TRK/TCK streamlines and scalar images
- Atlas-based streamline tract segmentation using JHU-style label maps
- ROI-based AFQ 20-tract segmentation using the original Mori/JHU waypoint
  ROIs and 20-channel probability atlas
- Deformation-field transform for native-to-MNI streamline normalization
- Optional ANTs registration and transform-application command builders
- AFQ-style streamline outlier cleaning using length and per-node Mahalanobis
  distance criteria
- Subject-level AFQ pipeline combining atlas segmentation, outlier cleaning,
  and scalar tract-profile extraction, with atlas- or ROI-based segmentation
  methods
- HTML tract QC reports combining profile statistics, plots, and segmentation
  counts
- TrackQC reports can embed the interactive HTML/WebGL 3D fiber viewer
- Python-native tract-measure NIfTI conversion, merged 4D images, and analysis
  masks through `nm-wm tract-ms2nii`
- FSL `design_ttest2`/`randomise` command builders and `nm-wm randomise`
  workflow integration
- HTML/SVG image QC viewer with axial slices and target overlays
- HTML/SVG streamline rendering with axial, coronal, and sagittal projections
- Interactive HTML/WebGL 3D streamline viewer through `nm-diffusion
  render-tracts-3d`
- ANTs point-based streamline transformation through `nm-diffusion
  transform-tracts-ants`
- ANTs SyN affine + inverse warp streamline transformation composition
- AFQ-style group profile plots and per-node profile statistics
- FSL/MRtrix command builders for BET, eddy correction, FA/T1 transforms,
  native/MNI transforms, topup, bedpostx, dtifit, probtrackx, and tckgen
- Session concatenation/merging, image combination, directory-of-3D signal
  extraction, timepoint counting, detrending, text-to-NIfTI, and world-space
  reslicing
- HTML reports and SHA-256 manifests
- CLI entry points and optional Tkinter interfaces
- Minimal core dependency budget through NumPy/SciPy/NiBabel
- `nm-toolbox doctor` for package, dependency, data, and optional runtime
  provider health checks
- Python-native mirrored homotopic functional connectivity
- Python-native thresholded FC asymmetry
- Python-native leave-one-out FC pattern correlation
- Python-native multi-run merge and subject-name validation
- Python-native MNI region-center and timepoint-count target utilities
- Optional `wm_analysis` pipeline integration for homotopic connectivity and
  FC asymmetry
- Optional `afq` pipeline integration for subject-level tract analysis
- Deformation-engine comparison between the internal NumPy/SciPy engine and
  the optional DIPY engine

## Not Yet Ported or Verified

### T1 target workflows

- Desktop apps expose T1 target generation and interactive SPM segmentation;
  the advanced GUI also exposes an interactive DARTEL template action

### SPM/DARTEL-equivalent preprocessing

- Full numerical parity across a larger clinical multi-subject DARTEL dataset
  beyond the twenty-seven real template-derived subjects

## Verification Evidence

- Independent numerical-reference tests for ideal filtering and head-motion
  metrics
- External-execution tests for FSL BET, eddy_correct, and MRtrix tckgen that
  skip when binaries are not installed; first run against installed binaries on
  2026-08-04: 3/3 pass (see External Runtime Environment below)
- SPM25 reference validation on 2026-08-04: applying the SPM `y_T1.nii`
  template-to-native field with the package reproduces SPM's `wc1T1.nii`
  warped tissue output (correlation > 0.99)
- SPM25 realignment reference validation on 2026-08-04: DIPY motion estimates
  agree with SPM after sign-convention alignment (minimum column correlation
  > 0.57 on real fMRI)
- SPM25 coregistration reference validation on 2026-08-04: DIPY rigid
  coregistration agrees with SPM on known real-image shifts (minimum aligned
  column correlation > 0.59)
- FSL Randomise execution test passes in the WSL dev environment on
  2026-08-04 with a small 4D input and analysis mask
- SPM normalization reference validation on 2026-08-04: DIPY deformation
  fields agree with SPM on real templates (minimum correlation > 0.99)
- FSL FNIRT normalization execution validation passes in WSL on real templates,
  comparing the FSL warped image with the DIPY warped image
- SPM DARTEL template runner executed on two real segmentation outputs,
  producing `Template_0/1.nii` and `u_*` flow fields
- SPM DARTEL Normalise-to-MNI runner executed on real template/flow outputs,
  producing `sw*` warped images
- SPM DARTEL reference comparison on twenty-seven real template-derived subjects:
  tissue maps agree with SPM unified-normalization outputs (mean correlation
  > 0.87)
- Internal vs DIPY deformation-engine comparison on real bundled grey/white
  templates: warped-output correlation 0.854, MAE 0.057 (2026-08-05)
- Multi-subject nonlinear-warp validation for the internal deformation engine
  with three known warp patterns (2026-08-05)
- ANTs execution tests that skip when binaries are not installed; first run
  against installed ANTs 2.6.5 on 2026-08-04: 4/4 pass, including real-template
  registration/apply and SyN streamline transformation tests
- Local test suite: `190 tests collected` and passing
- `pip check`: no broken requirements
- Wheel: `dist/neuroimaging_neuromodulation-0.20.0-py3-none-any.whl`
- CI claim: recorded in `docs/ci-validation.md`, but not independently
  reproducible from repository artifacts in this workspace

This file must be updated before any future claim that the migration is
complete.

## External Runtime Environment

As of 2026-08-05 the external runtimes below are installed and usable for
reference/comparison work. The execution tests were run for the first time on
2026-08-04; SPM `y_`/`iy_` convention, realignment, coregistration,
normalization, FSL FNIRT, and DARTEL reference comparisons are now implemented,
while full numerical parity across a larger clinical multi-subject DARTEL
dataset beyond the twenty-seven real template-derived subjects is not yet
demonstrated. External-runtime tests are optional and skipped by default;
set `NM_RUN_EXTERNAL=1` to run them:

- MATLAB R2015b and SPM standalone 25.01.02 are installed on Windows
  (`C:\Program Files\MATLAB\R2015b\bin`,
  `C:\Users\ginger\spm_standalone_25.01.02_Windows`); SPM/DARTEL template,
  Normalise-to-MNI, and parity comparisons are implemented and have been run
  through twenty-seven real template-derived subjects; larger clinical parity
  remains to be demonstrated.
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
  - `test_randomise_execution`: pass with Python-generated two-group design
    files and FSL `randomise`.
  - `test_fsl_normalization_execution`: pass with FSL FNIRT on real templates.
- ANTs 2.6.5 is installed on Windows (`C:\Program Files\ants-2.6.5\bin`) and
  has been added to the user PATH (2026-08-04). `tests/test_ants_execution.py`
  was run on 2026-08-04 with `.venv-win` (`antsRegistration --version`,
  `antsApplyTransforms --help`, and a real-template rigid/affine
  registration/apply workflow plus a SyN streamline transform): 4/4 pass.
- Interactive 3D fiber rendering is available as an HTML/WebGL viewer that runs
  in any WebGL-capable browser.

The Python-native port is substantially implemented, and SPM `y_`/`iy_`
world-coordinate convention, realignment, coregistration, normalization, FSL
FNIRT, and DARTEL reference validation now pass. Full numerical parity across a
larger clinical multi-subject DARTEL dataset beyond the twenty-seven real
template-derived subjects remains to be demonstrated. ANTs
execution tests pass (4/4); FSL/MRtrix execution smoke tests pass (3/3) as of
2026-08-04.
