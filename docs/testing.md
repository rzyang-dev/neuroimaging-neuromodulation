# Testing and Issues

## Test Strategy

Tests are grouped by responsibility:

- `test_io.py` verifies NIfTI loading/saving and 4D matrix conversion.
- `test_deformations.py` verifies identity and shifted deformation fields.
- `test_temporal.py` verifies Fourier shifts, slice timing, and motion
  resampling.
- `test_motion.py` verifies DIPY-based rigid motion estimation on a real fMRI
  subset.
- `test_coordinates.py` verifies MNI/matrix conversions against the SPM-style
  affine convention.
- `test_stats.py` verifies correlation, inverse Pearson threshold, filtering,
  and regression.
- `test_targets.py` verifies sphere ROIs, dilation, depth masks, FC, and target
  site selection.
- `test_wm.py` verifies ALFF/fALFF and white-matter mask construction.
- `test_reporting.py` verifies manifests and HTML reports on real outputs.
- `test_classification.py` verifies leave-one-out GFC classification.
- `test_coregister.py` verifies DIPY coregistration on a real fMRI volume.
- `test_diffusion.py` verifies DTI fitting, tractography, and connectivity on
  DIPY's real `small_64D` diffusion dataset.
- `test_dicom.py` verifies DICOM conversion on a real Hitachi anatomical
  series.
- `test_segmentation.py` verifies tissue estimation on a real Stanford T1.
- `test_diffusion.py` also verifies probabilistic tensor tractography.
- `test_deformations_estimate.py` verifies DIPY deformation estimation and
  `y_`/`iy_` coordinate-field conversion on real data.
- `test_spm_reference.py` verifies SPM world-coordinate `y_`/`iy_` handling
  against SPM25 standalone output when SPM is installed.
- `test_targets.py` and `test_pipeline.py` verify T1-space target generation
  with a supplied SPM `y_` field.
- `test_enduser_app.py` verifies the `nm-app` pipeline config includes
  T1-space target generation when T1 and target ROI are supplied.
- `test_preprocess.py` verifies the `nm-preprocess spm-segment` parser exposes
  the SPM25 workflow.
- `test_roi_segmentation.py` verifies the bundled AFQ ROI list aligns with the
  20-channel JHU tract probability atlas.
- `test_spm_motion_reference.py` verifies DIPY motion estimates against SPM25
  realignment on real fMRI.
- `test_spm_coreg_reference.py` verifies DIPY rigid coregistration against
  SPM25 on known real-image shifts.
- `test_render_tracts.py` verifies the interactive HTML/WebGL 3D streamline
  viewer output.
- `test_trackqc.py` verifies TrackQC reports can embed the interactive 3D
  fiber viewer.
- `test_tract_ms2nii.py` verifies per-subject NIfTI conversion, merged 4D
  output, and the analysis mask.
- `test_external.py` and `test_wm.py` verify the FSL `design_ttest2`/Randomise
  command builders and CLI dry-run path.
- `test_randomise_execution.py` runs FSL `randomise` on a small 4D input when
  FSL is installed.
- `test_spm_normalization_reference.py` compares SPM and DIPY normalization
  deformation fields on real templates.
- `test_spm_reference.py` verifies SPM segmentation also emits the imported
  `rc1/rc2/rc3` DARTEL tissue maps.
- `test_spm_dartel_batch.py` verifies the SPM DARTEL create-template batch
  writer.
- `test_spm_dartel_batch.py` and `test_preprocess.py` also verify the DARTEL
  Normalise-to-MNI batch and CLI parser.
- Manual SPM DARTEL reference verification compares DARTEL and SPM unified
  normalization outputs on twenty-seven real template-derived subjects (mean
  correlation > 0.87).
- `test_preprocess.py` verifies the multi-subject `dartel-parity` CLI parser.
- `test_fsl_normalization_execution.py` runs FSL FNIRT on real templates when
  FSL is installed.
- `test_streamline_transform.py` and `test_ants_execution.py` verify ANTs
  point-based streamline transformation.
- `test_ants_execution.py` also verifies ANTs SyN affine + inverse warp
  streamline transformation on real templates.
- `test_pipeline.py` verifies a config-driven real-data pipeline.
- `test_validation.py` verifies image and deformation validation metrics.
- `test_external.py` verifies FSL/MRtrix command builders and missing-binary
  behavior.
- `test_external.py` verifies external-tool availability reporting.
- `test_regression_cli.py` verifies regression, nuisance regression, signal
  extraction, and Friston-24 CLI commands.
- `test_dicom.py` also verifies DICOM inspection and single-series validation.
- `test_dicom.py` covers six real DICOM vendor series.
- `test_dicom.py` covers compressed and enhanced multiframe DICOM variants.
- `test_runtime_diagnostics.py` verifies `nm-toolbox doctor` and optional
  runtime-provider discovery.
- `test_wm_connectivity.py` verifies homotopic connectivity, FC asymmetry, and
  FC pattern correlation on real fMRI.
- `test_multirun_subjects.py` verifies multi-run merge and subject-name
  validation.
- `test_target_center.py` verifies MNI region centers and timepoint counting.
- `test_packaging.py` verifies the minimal core dependency budget and optional
  extras.

Functional-data tests use one real adult subject from the Nilearn development
fMRI dataset. Geometry tests use real bundled templates and masks.

## Current Results

```text
176 tests collected and passing
```

Python 3.10 also passes the full suite:

```text
176 tests collected and passing
```

The test command is:

```bash
.venv/bin/python -m pytest
```

## Manual Validation

The CLI was exercised end to end on the real downloaded fMRI subject:

- `nm-tms seed-fc` produced `SeedFCinWB.nii` and `SeedFCinROI.nii`.
- `nm-tms target-site` produced positive and negative target candidates.
- `nm-wm alff` produced ALFF/fALFF and normalized variants.
- `nm-preprocess deform` preserved a real mask under an identity deformation field.
- `nm-preprocess slice-timing` corrected the real 50-slice fMRI volume.
- `nm-preprocess motion-correct` resampled the real fMRI volume using motion
  parameters extracted from its real confound file.
- `nm-preprocess estimate-motion` estimated realignment parameters from a
  real 5-volume fMRI subset and wrote corrected data plus an SPM-style RP file.

## Packaging Verification

`pip wheel` builds successfully:

```text
neuroimaging_neuromodulation-0.20.0-py3-none-any.whl
```

The wheel contains the package modules, bundled real template/mask data, CLI
entry points, and license metadata.

## Known Issues

See `docs/issues.md`.

## Test Limitations

The current suite is a smoke-test suite for the implemented Python subset. It
does not prove migration completeness or numerical equivalence with the
original MATLAB toolbox:

- Several tests assert only that outputs exist, shapes are correct, or values
  are finite.
- Probabilistic tractography can pass with zero streamlines.
- Motion, coregistration, and normalization now have SPM/FSL reference
  comparisons; segmentation and tractography still lack full reference
  comparison against MATLAB/SPM/FSL/AFQ outputs.
- GUI tests cover config construction only; the desktop UIs are not exercised.
- Missing workflows listed in `docs/porting-status.md` have no coverage.

These limitations must be resolved before the project can claim a complete
migration or production readiness.

External-execution tests for FSL BET, `eddy_correct`, MRtrix `tckgen`, ANTs,
SPM reference checks, Randomise, and FNIRT are optional. They skip by default
and run when `NM_RUN_EXTERNAL=1` is set. They also skip automatically when the
corresponding binary is unavailable.
The MRtrix `tckgen` wrapper now accepts `seed_image`; the execution test uses
the `SeedTest` algorithm so it verifies binary/wrapper integration without
requiring FOD generation.

On this development machine the FSL/MRtrix binaries live inside WSL, so these
tests can be run from the WSL dev environment (`~/nm-dev-venv`, editable
install `~/nm-src`) with `source /home/dev/fsl/etc/fslconf/fsl.sh` so that
`shutil.which` finds them. ANTs 2.6.5 is installed on Windows
(`C:\Program Files\ants-2.6.5\bin`) and has been added to the user PATH
(2026-08-04), so `shutil.which` finds its binaries in new processes.

## External-Execution Results (2026-08-04)

Verified against the installed binaries:

- `tests/test_ants_execution.py` (Windows, `.venv-win`): **4/4 pass**
  (`antsRegistration --version`, `antsApplyTransforms --help`, real-template
  rigid/affine registration/apply, and SyN streamline transformation).
- `tests/test_spm_reference.py` (Windows, `.venv-win`, SPM25 standalone):
  **1/1 pass**. Applying SPM's `y_T1.nii` with the package reproduces SPM's
  `wc1T1.nii` warped tissue output with correlation > 0.99.
- `tests/test_spm_motion_reference.py` (Windows, `.venv-win`, SPM25
  standalone): **1/1 pass**. DIPY motion estimates agree with SPM after
  sign-convention alignment.
- `tests/test_spm_coreg_reference.py` (Windows, `.venv-win`, SPM25
  standalone): **1/1 pass**. DIPY rigid coregistration agrees with SPM on
  known real-image shifts.
- `tests/test_spm_normalization_reference.py` (Windows, `.venv-win`, SPM25
  standalone): **1/1 pass**. DIPY deformation fields agree with SPM on real
  templates with minimum correlation > 0.99.
- `tests/test_fsl_normalization_execution.py` (WSL, FSL): **1/1 pass**. FSL
  FNIRT and DIPY warped images agree on real templates.
- `tests/test_external_execution.py` (WSL, `~/nm-dev-venv` on `~/nm-src`,
  with `fsl.sh` sourced): **3/3 pass**
  - `test_fsl_eddy_correct_execution`: pass.
  - `test_fsl_bet_execution`: pass on a realistic 32x32x32 ellipsoid fixture.
    The previous constant 8x8x8 input segfaulted FSL `bet2`, so the fixture was
    replaced with a non-degenerate input.
  - `test_mrtrix_tckgen_execution`: pass with `-seed_image` and the
    `SeedTest` algorithm.
- `tests/test_randomise_execution.py` (WSL, FSL): **1/1 pass** with a small
  two-group 4D input and analysis mask.

The external wrapper smoke coverage is complete for the installed binaries;
reference parity against MATLAB/SPM/FSL remains a separate objective.
