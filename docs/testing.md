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

Functional-data tests use one real adult subject from the Nilearn development
fMRI dataset. Geometry tests use real bundled templates and masks.

## Current Results

```text
74 passed
```

Python 3.10 also passes the full suite:

```text
74 passed in 13.59s
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
neuroimaging_neuromodulation-0.18.0-py3-none-any.whl
```

The wheel contains the package modules, bundled real template/mask data, CLI
entry points, and license metadata.

## Known Issues

See `docs/issues.md`.
