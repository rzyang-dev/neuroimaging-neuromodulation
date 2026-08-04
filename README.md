# Neuroimaging and Neuromodulation Toolbox

Python-native implementation of the core algorithms from the academic
Neuroimaging-and-Neuromodulation MATLAB toolbox. The project is organized
around data transformation: NIfTI images and parameter files are converted
into connectivity maps, amplitude maps, ROIs, and TMS target candidates.

## Status

**Alpha / partial migration.** This is not a complete port of the original
MATLAB toolbox and is not production-ready. The repository contains a working
Python-native subset that is useful for development and method comparison, but
several original workflows are still missing or approximate. See
`docs/porting-status.md`, `docs/completion-audit.md`, and `docs/issues.md` for
the current requirement-by-requirement status.

In the local workspace, the MATLAB source is preserved untouched under
`Neuroimaging-and-Neuromodulation/`. The published Python package is a
separate, isolated implementation with its own virtual environment and does
not redistribute the vendored MATLAB/SPM/FSL directories. See
`docs/source-repository.md`.

## What Is Included

- NIfTI loading, saving, and world-space resampling
- Image reslicing onto a reference grid
- Nonlinear deformation-field resampling for SPM world-coordinate `y_`/`iy_`
  fields
- Seed-based functional connectivity (`TMSSeedFC`, `WMSeedFC`)
- ROI-wise functional-connectivity matrices
- Fast Pearson correlation (`TMSfastCorr`)
- Ideal frequency filtering (`TMSIdealFilter`, `TMSfilter`)
- Fourier slice-timing correction and motion-parameter-based resampling
- Detrending and world-space image reslicing
- Text-to-NIfTI conversion for tract-matrix output workflows
- Rigid motion-parameter estimation through DIPY
- SPM25-validated motion parameter reference comparison
- SPM25-validated rigid coregistration reference comparison
- DIPY-based volume coregistration
- DTI fitting, deterministic tractography, and seed-target structural
  connectivity through `nm-diffusion`
- Tract-profile extraction from TRK/TCK streamlines and scalar images
- Atlas-based streamline tract segmentation using JHU-style label maps
- ROI-based AFQ 20-tract segmentation using the original Mori/JHU waypoint
  ROIs and probability atlas
- Deformation-field transform for native-to-MNI streamline normalization
- Optional ANTs registration and transform-application commands
- AFQ-style streamline outlier cleaning with length and Mahalanobis distance
  criteria
- Subject-level AFQ pipeline combining atlas segmentation, cleaning, and
  tract-profile extraction, with atlas- or ROI-based segmentation methods
- HTML tract QC reports combining profile statistics, plots, and segmentation
  counts
- AFQ-style group profile plots and per-node profile statistics
- Deterministic and probabilistic tensor tractography through `nm-diffusion`
- DICOM-to-NIfTI conversion through `nm-dicom`
- DICOM inspection and single-series validation through `nm-dicom`
- Real DICOM vendor coverage for generic, GE, Philips, Siemens, Hyperfine, and
  Hitachi series
- Compressed and enhanced multiframe DICOM conversion coverage
- Atlas-guided GM/WM/CSF tissue probability estimation (approximate, not a
  validated SPM/DARTEL replacement)
- DIPY-based nonlinear deformation estimation with SPM world-coordinate
  `y_`/`iy_` output
- SPM25 standalone segmentation command through `nm-preprocess spm-segment`
- SPM25-validated `y_`/`iy_` world-coordinate convention
- Quantitative deformation/image validation commands
- Optional FSL/MRtrix wrappers with clear missing-binary errors
- External tool health check through `nm-diffusion check-external`
- Verified test-suite execution on Python 3.10 and 3.14
- Config-driven end-to-end pipeline through `nm-pipeline`
- Standalone band-pass filtering command
- Leave-one-out GFC classification and left-right image flipping
- Correlation-comparison, chi-square, quantile-regression, and
  covariate-adjusted/permutation two-group t-test commands
- Desktop GUI preprocessing tab for motion, slice timing, deformation, and
  smoothing
- White-matter seed FC and multi-seed FC
- Dynamic ALFF, group GM/WM masks, and JHU tract-overlap reporting
- Head-motion QC metrics
- Approximate outer-brain c6 mask construction
- DICOM series selection by index
- FSL command pipelines for BET, eddy correction, FA/T1 transforms,
  native/MNI transforms, and topup
- ALFF, zALFF, mALFF, fALFF, zfALFF, and mfALFF
- Nuisance regression and Friston-24 motion regressors
- CLI commands for generic regression, nuisance regression, signal extraction,
  and Friston-24 regressors
- Sphere ROI creation, ROI dilation, and deep-target coordinates
- Individual target mask construction from tissue segments
- T1-space target image generation through `nm-tms t1-target` and
  `nm-pipeline`, with optional SPM25 segmentation integration
- Correlation thresholding and largest-cluster target selection
- CLI commands and an optional Tkinter desktop interface
- Guided end-user desktop application via `nm-app`
- Advanced desktop interface via `nm-gui`
- Separate `nm-preprocess` program for deformation, slice timing, motion
  resampling, and smoothing
- HTML target reports and SHA-256 output manifests for traceability
- HTML/SVG image QC viewer with axial slices and target overlays
- HTML/SVG streamline rendering with axial, coronal, and sagittal projections
- Interactive HTML/WebGL 3D streamline viewer through `nm-diffusion
  render-tracts-3d`
- HTML tract QC reports can embed the interactive 3D fiber viewer

## What Is Not Included

This release does not reimplement SPM/FSL preprocessing internally. It includes
an approximate atlas-guided tissue probability estimator and can invoke SPM25
standalone for SPM segmentation when installed, but DARTEL-grade segmentation,
FSL BEDPOSTX tractography, and SPM/DARTEL-compatible deformation estimation are
not reproduced by the Python core.
DICOM conversion is handled through `nm-dicom`, and other inputs should already
be in the expected NIfTI space or produced with existing preprocessing tools.
The decision record in `docs/decisions.md` explains why this boundary is
intentional.

The following original workflows are not yet ported:

- Full AFQ 20-tract segmentation
- Desktop T1 target workflow with interactive SPM/DARTEL segmentation setup
- TrackQC and tract-profile statistical workflows
- SPM/DARTEL-compatible segmentation, normalization, and QC workflows

The shipped CLI exposes a subset of the Python-native primitives, not a full
replacement for the original end-user application.

## Setup

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e ".[test]"
```

Use the Tsinghua PyPI mirror in mainland China when the default index is slow:

```bash
.venv/bin/python -m pip install -e ".[test]" -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## Quick Start

Download one real public fMRI subject:

```bash
.venv/bin/nm-toolbox demo-data --output-dir data/real_development_fmri
```

Compute seed-based FC:

```bash
.venv/bin/nm-tms seed-fc \
  --functional data/real_development_fmri/development_fmri/development_fmri/sub-pixar123_task-pixar_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz \
  --seed data/derived/seed.nii \
  --mask data/derived/brainmask_func.nii \
  --tr 2.0 \
  --output-dir data/derived/fc
```

Compute ALFF/fALFF:

```bash
.venv/bin/nm-wm alff \
  --functional <4D fMRI.nii> \
  --mask <analysis-mask.nii> \
  --output-dir <output-dir> \
  --tr 2.0
```

Launch the guided end-user app:

```bash
.venv/bin/nm-app
```

## Tests

```bash
.venv/bin/python -m pytest
```

Tests use the real templates and masks bundled in
`neuroimaging_neuromodulation/data/` and, when present, one real public fMRI
subject downloaded through Nilearn.

## Build

```bash
.venv/bin/python -m pip wheel . --no-deps -w dist
```

The verified wheel is `dist/neuroimaging_neuromodulation-0.19.0-py3-none-any.whl`.

## Documentation

- `docs/analysis.md` - source-code inventory and algorithm mapping
- `docs/production-readiness.md` - production readiness checklist
- `docs/completion-audit.md` - requirement-by-requirement audit
- `docs/source-repository.md` - source repository and redistribution note
- `docs/ci-validation.md` - CI validation branch notes
- `docs/end-user-app.md` - end-user desktop application guide
- `configs/pipeline.example.json` - example end-to-end pipeline config
- `.github/workflows/ci.yml` - CI matrix for Python 3.10-3.12 on Ubuntu,
  macOS, and Windows
- `docs/requirements.md` - requirements and planning
- `docs/decisions.md` - design and dependency decisions
- `docs/design.md` - package design and data flow
- `docs/testing.md` - test strategy and results
- `docs/issues.md` - known limitations and issues
- `docs/user-manual.md` - user manual
- `docs/data-sources.md` - real data provenance

## Citation

Please cite the original publications when this toolbox is useful to your work:

1. Gong-Jun JI, Wei Liao, et al. Low-frequency Blood Oxygen Level-dependent
   Fluctuations in the Brain White Matter: More Than Just Noise. Science
   Bulletin, 2017, 62(9): 656-657.
2. Gong-Jun JI, et al. Regional and network properties of white matter function
   in Parkinson's disease. Human Brain Mapping, 2019, 40(4):1253-1263.
3. Gong-Jun Ji, Jinmei Sun, et al. White matter dysfunction in psychiatric
   disorders is associated with neurotransmitter and genetic profiles. Nature
   Mental Health, 2023.
