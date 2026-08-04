# Changelog

## 0.19.0 - 2026-08-03

- Corrected status records to describe the project as an Alpha partial
  migration instead of a complete production port.
- Fixed `bandpass_filter` matrix-orientation handling.
- Fixed `extract_signal` to match the original nonzero-value mean behavior.
- Fixed the end-user app's DICOM folder Browse action.
- Added DICOM series selection by index in `nm-dicom` and `nm-pipeline`.
- Exposed individualized target-mask and native target-site options in CLI and
  pipeline config.
- Added white-matter seed FC, multi-seed FC, dynamic ALFF, group masks, JHU
  tract reporting, head-motion QC metrics, c6 mask construction,
  tract-profile extraction, AFQ-style SVG profile plots, and per-node profile
  statistics, atlas-based streamline tract segmentation, and HTML tract QC
  reports, plus AFQ-style streamline outlier cleaning and a subject-level
  AFQ pipeline, ROI-based tract segmentation with the original Mori/JHU
  templates, ROI/atlas method selection in the AFQ pipeline, and an HTML/SVG
  image QC viewer, plus deformation-field streamline transforms.
- Added HTML/SVG streamline rendering with axial, coronal, and sagittal
  projections.
- Added a permutation two-sample t-test command.
- Added optional ANTs registration and transform-application commands.
- Added ANTs execution tests that skip when ANTs is unavailable.
- Added independent numerical-reference tests for ideal filtering and
  head-motion metrics.
- Added external-execution tests for FSL BET, eddy_correct, and MRtrix
  tckgen that skip when binaries are unavailable.
- Added `--seed-image` to the MRtrix tckgen wrapper and replaced the degenerate
  FSL BET execution fixture; FSL/MRtrix external-execution tests pass 3/3 on
  2026-08-04.
- Changed DIPY deformation output to SPM world-coordinate `y_`/`iy_` fields,
  with `y_` as the template-to-native pullback field used by
  `apply_deformation`.
- Added SPM25 standalone reference validation for the SPM `y_`/`iy_`
  world-coordinate convention.
- Added optional SPM25 segmentation integration to `nm-tms t1-target` and
  `nm-pipeline` for T1-space target image generation.
- Added T1-space target generation controls to the `nm-app` and `nm-gui`
  desktop workflows.
- Added `nm-preprocess spm-segment` for SPM25 standalone segmentation and
  reference validation output.
- Aligned the AFQ ROI segmentation list with the bundled 20-channel JHU
  tract probability atlas.
- Added a real-template ANTs registration/apply integration execution test.
- Added SPM25 realignment reference validation against the DIPY motion
  estimator.
- Added SPM25 coregistration reference validation against DIPY rigid
  registration.
- Added an interactive HTML/WebGL 3D streamline viewer and
  `nm-diffusion render-tracts-3d`.
- Added optional embedding of the 3D streamline viewer in `nm-wm tract-qc`
  reports.
- Added Python-native `nm-wm tract-ms2nii` for tract-measure NIfTI conversion,
  merged 4D images, and analysis masks.
- Added FSL `design_ttest2`/`randomise` command builders and the `nm-wm
  randomise` workflow.
- Added a Python-native two-group design file writer and a real FSL Randomise
  execution test.
- Added SPM normalization reference validation comparing DIPY and SPM
  deformation fields on real templates.
- Added FSL FNIRT normalization execution validation against the DIPY warped
  image.
- Added ANTs point-based streamline transformation and `nm-diffusion
  transform-tracts-ants`.
- Added ANTs SyN affine + inverse warp streamline transformation execution
  validation.
- Added an interactive SPM segmentation action to the advanced desktop GUI.
- Added an interactive DARTEL template action to the advanced desktop GUI.
- SPM25 segmentation now emits imported `rc1/rc2/rc3` DARTEL tissue maps.
- Added `nm-preprocess dartel-template` and a real SPM DARTEL template/flow
  field smoke run.
- Added `nm-preprocess dartel-mni-norm` and a real SPM DARTEL Normalise-to-MNI
  smoke run.
- Added an SPM DARTEL reference comparison helper with real-data verification.
- Extended the SPM DARTEL reference check to seven real subjects with mean
  correlation > 0.85.
- Added `nm-preprocess dartel-parity` for running multi-subject DARTEL
  reference comparisons from the CLI.
- Added FSL command pipelines for BET, eddy correction, FA/T1 transforms,
  native/MNI transforms, and topup.
- Added group-statistics commands for correlation comparison, chi-square,
  quantile regression, covariate-adjusted t-tests, and ROI-wise FC.
- Added reslice, detrend, merge-images, concatenate-sessions, combine-images,
  timepoint-count, text-to-nifti, and directory-of-3D signal-extraction
  commands.
- Expanded tests from 74 to 158 collected/passing tests.

## 0.18.0 - 2026-08-03

- Added `regress`, `regress-covariates`, `extract-signal`, and `friston24` CLI
  commands.
- Integrated nuisance regression into `nm-pipeline`.
- Added `nm-gui` launcher for the advanced desktop interface.
- Fixed test data globs to exclude AppleDouble files and replaced silent test
  returns with explicit pytest skips.

## 0.17.0 - 2026-08-03

- Added `nm-app`, a guided end-user desktop application.

## 0.16.0 - 2026-08-03

- Fixed DIPY registration compatibility across DIPY 1.11/1.12 and Python
  3.10/3.14.
- Added verified Python 3.10 test-suite execution.

## 0.15.0 - 2026-08-03

- Added `nm-diffusion check-external` to report FSL/MRtrix binary availability.
- Added `docs/completion-audit.md` with requirement-by-requirement evidence.
- GitHub Actions matrix passed on Ubuntu, macOS, and Windows for Python
  3.10-3.12.

## 0.14.0 - 2026-08-03

- Added compressed JPEG, JPEG-LS, JPEG2000, RLE, Siemens multiframe, and
  Philips enhanced DICOM conversion coverage.

## 0.13.0 - 2026-08-03

- Added real DICOM vendor coverage for generic, GE, Philips, Siemens,
  Hyperfine, and Hitachi series.

## 0.12.0 - 2026-08-03

- Added `nm-dicom inspect` and `validate-series` commands for real DICOM
  metadata and single-series validation.

## 0.11.0 - 2026-08-03

- Added optional FSL and MRtrix command wrappers with dry-run support.
- Expanded CI workflow to Ubuntu, macOS, and Windows.

## 0.10.0 - 2026-08-03

- Added `nm-preprocess validate-deformation` and `validate-image` quantitative
  validation commands.

## 0.9.0 - 2026-08-03

- Added SPM-style `y_ac_coT1.nii` and `iy_ac_coT1.nii` coordinate-field outputs
  from DIPY nonlinear deformation estimation.

## 0.8.0 - 2026-08-03

- Added config-driven `nm-pipeline` for end-to-end DICOM, preprocessing, seed
  FC, target selection, and reporting workflows.

## 0.7.0 - 2026-08-03

- Added DIPY-based nonlinear deformation estimation with SPM-style coordinate
  field conversion.
- Added `nm-preprocess estimate-deformation`.

## 0.6.0 - 2026-08-03

- Added atlas-guided tissue probability estimation for T1 images.
- Added `nm-preprocess segment-tissue` and validation with a real Stanford T1.
- Added DIPY-based probabilistic tensor tractography.

## 0.5.0 - 2026-08-03

- Added `nm-dicom` for DICOM-to-NIfTI conversion using `dicom2nifti`.
- Added validation with a real Hitachi DICOM anatomical series.

## 0.4.0 - 2026-08-03

- Added `nm-diffusion` with DTI tensor fitting, deterministic tractography, and
  seed-target connectivity counting.
- Added validation against DIPY's real `small_64D` diffusion dataset.

## 0.3.0 - 2026-08-03

- Added DIPY-based motion estimation, coregistration, and their CLI/GUI
  integrations.
- Added standalone filtering, left-right flipping, GFC classification,
  deformation-field application, slice timing, and report/manifest tools.

## 0.2.0 - 2026-08-03

- Added nonlinear deformation-field resampling for SPM-style `iy_*.nii`
  inverse fields.
- Added Fourier-based slice timing correction.
- Added motion-parameter-based volume resampling for SPM-style realignment
  parameter files.
- Added `deform`, `slice-timing`, and `motion-correct` CLI commands.
- Added a `smooth` CLI command using physical-mm Gaussian smoothing.
- Added optional inverse-field application inside the seed-FC pipeline.
- Added HTML target reports and SHA-256 output manifests.
- Added rigid motion-parameter estimation through DIPY with `estimate-motion`.
- Added a standalone band-pass `filter` preprocessing command.
- Added leave-one-out GFC classification and left-right image flipping.
- Added DIPY-based volume coregistration.
- Added deformation and temporal preprocessing tests.

## 0.1.0 - 2026-08-03

- Added Python package skeleton and isolated virtual environment.
- Implemented NIfTI I/O and resampling.
- Implemented seed-based FC, ideal filtering, regression, ALFF/fALFF.
- Implemented sphere ROI, ROI dilation, deep target, individual target mask,
  largest-cluster target selection.
- Added CLI entry points and optional Tkinter GUI.
- Added tests against bundled real templates/masks and one real public fMRI
  subject.
