# Design

## Package Layout

```text
neuroimaging_neuromodulation/
  io/          NIfTI loading, saving, resampling
  stats/       correlation, filtering, regression
  preprocess/  lightweight spatial and nuisance processing
  targets/     ROIs, depth masks, FC, target-site selection
  wm/          ALFF/fALFF and tissue masks
  cli/         argparse command-line interfaces
  gui/         optional Tkinter desktop interface
  data/        real templates and masks bundled with the package
```

## Runtime Boundary

The normal analysis path depends only on NumPy, SciPy, and NiBabel. DIPY,
pydicom/dicom2nifti, and Nilearn are optional extras. MATLAB, SPM, FSL, ANTs,
and SimNIBS are never imported by core code; they are discovered through
optional runtime providers and reported by `nm-toolbox doctor`.

## Core Data Structures

Functional data are represented as `(n_voxels, n_timepoints)` matrices, the
same convention used by `TMSReadNii`. This makes the Python implementation
comparable to the MATLAB source and keeps FFT/correlation operations vectorized.

Coordinate transforms use the affine matrix directly. The package supports
both 0-based NumPy array indices and the 1-based matrix indices used by the
original toolbox.

## Deformation Fields

SPM deformation fields are 4D/5D images whose last axis stores world mm
coordinates. `y_*.nii` is the template-to-native pullback field used by
`apply_deformation` to move a target mask from MNI space into native T1 space;
`iy_*.nii` is the native-to-template forward field used by streamline
transforms. Legacy 1-based voxel fields remain supported through
`coordinate_system="voxel"`.

## Temporal Processing

Slice timing is implemented as a Fourier phase shift, avoiding resampling in
time and preserving signal shape for periodic resting-state signals. Motion
correction is implemented as affine voxel resampling from existing SPM-style
realignment parameters.

Motion parameter estimation is implemented through DIPY's affine registration
API. The default pipeline starts with translation and then fits a rigid
transform for each volume. DIPY affines are converted to SPM-style
`[tx, ty, tz, rx, ry, rz]` text output.

## Reporting and Traceability

Every subject result can be summarized as an HTML report and a JSON manifest.
The manifest records relative paths, byte sizes, SHA-256 hashes, and NIfTI
metadata for each output file. This makes result directories auditable without
relying on filenames alone.

## Diffusion and Structural Connectivity

DTI fitting uses DIPY's weighted least-squares tensor model. Deterministic
tractography uses tensor peaks and a threshold stopping criterion on FA.
Seed-target connectivity counts streamlines that pass through both ROIs, which
approximates the structural-connectivity role of the original FSL-based
workflow without requiring BEDPOSTX or PROBTRACKX.

## DICOM Conversion

DICOM conversion uses `dicom2nifti`, a pure-Python library with vendor-specific
handlers for Siemens, GE, Philips, Hitachi, and generic series. The `nm-dicom`
program exposes both single-series and whole-directory conversion.

## Tissue Segmentation

The segmentation module resamples real SPM tissue priors into the T1 grid and
uses an expectation-maximization Gaussian mixture to estimate GM, WM, and CSF
probability maps. This is intentionally documented as approximate and is not
claimed to reproduce SPM/DARTEL.

## Deformation Estimation

Nonlinear deformation estimation uses DIPY's symmetric diffeomorphic
registration. The DIPY mapping is saved for reproducibility and also converted
into SPM world-coordinate `y_ac_coT1.nii` and `iy_ac_coT1.nii` fields. This is
an approximate Python-native normalization path, not an SPM DARTEL clone.

## Config-Driven Pipeline

`nm-pipeline` reads a JSON config and executes the main data-oriented workflow:
DICOM conversion (optional), slice timing (optional), motion estimation
(optional), nuisance regression (optional), seed-based FC, target-site
selection, optional T1-space target generation, and reporting. Output paths are
recorded in the returned summary so the same workflow can be audited or re-run
with changed parameters.

## Validation

The validation module computes correlation, RMSE, normalized RMSE, and MAE
between aligned images. `validate-deformation` applies a field and compares it
to a reference warped image, making SPM/DARTEL comparison workflows explicit.
SPM25 standalone reference generation is also exposed through the validation
module for convention checks and T1-space target workflows.

## Pipeline Design

### Seed-based FC

```text
4D fMRI -> (voxels x time)
seed NIfTI -> resample -> seed mask
analysis mask -> resample -> analysis mask
seed signal = mean over seed voxels
r = fast_corr(seed signal, masked time series)
write SeedFCinWB.nii and SeedFCinROI.nii
```

### Target selection

```text
FC map -> positive/negative extremum -> 5 mm sphere target
FC map -> p-value threshold -> largest 26-connected cluster
cluster -> center of mass -> 8 mm sphere target
write coordinate text files and target NIfTIs
```

### ALFF/fALFF

```text
4D fMRI -> (time x voxels) inside mask
linear detrend -> zero padding to next power of two
FFT -> 2*abs(FFT)/N
band mean -> ALFF, zALFF, mALFF
band sum / full-band sum -> fALFF, zfALFF, mfALFF
```

## Error Handling

The package raises `ValueError` for invalid shapes, empty masks, inconsistent
TR/band parameters, and missing required companion images. CLI and GUI layers
translate exceptions into user-facing messages.

## Memory Control

ALFF processing chunks voxels to avoid loading the whole spectrum as one dense
matrix. Filtering processes the voxel-by-time matrix with vectorized NumPy
operations. The real test fMRI is 4 mm and uses only a few hundred MB at peak.
