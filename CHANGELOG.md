# Changelog

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
