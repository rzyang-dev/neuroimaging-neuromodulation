# Neuroimaging and Neuromodulation Toolbox

Python-native implementation of the core algorithms from the academic
Neuroimaging-and-Neuromodulation MATLAB toolbox. The project is organized
around data transformation: NIfTI images and parameter files are converted
into connectivity maps, amplitude maps, ROIs, and TMS target candidates.

In the local workspace, the MATLAB source is preserved untouched under
`Neuroimaging-and-Neuromodulation/`. The published Python package is a
separate, isolated implementation with its own virtual environment and does
not redistribute the vendored MATLAB/SPM/FSL directories. See
`docs/source-repository.md`.

## What Is Included

- NIfTI loading, saving, and world-space resampling
- Nonlinear deformation-field resampling for SPM-style inverse fields
- Seed-based functional connectivity (`TMSSeedFC`, `WMSeedFC`)
- Fast Pearson correlation (`TMSfastCorr`)
- Ideal frequency filtering (`TMSIdealFilter`, `TMSfilter`)
- Fourier slice-timing correction and motion-parameter-based resampling
- Rigid motion-parameter estimation through DIPY
- DIPY-based volume coregistration
- DTI fitting, deterministic tractography, and seed-target structural
  connectivity through `nm-diffusion`
- Deterministic and probabilistic tensor tractography through `nm-diffusion`
- DICOM-to-NIfTI conversion through `nm-dicom`
- DICOM inspection and single-series validation through `nm-dicom`
- Real DICOM vendor coverage for generic, GE, Philips, Siemens, Hyperfine, and
  Hitachi series
- Compressed and enhanced multiframe DICOM conversion coverage
- Atlas-guided GM/WM/CSF tissue probability estimation (approximate, not a
  validated SPM/DARTEL replacement)
- DIPY-based nonlinear deformation estimation with SPM-style coordinate-field
  output
- SPM-style `y_`/`iy_` coordinate-field conversion from estimated DIPY mappings
- Quantitative deformation/image validation commands
- Optional FSL/MRtrix wrappers with clear missing-binary errors
- External tool health check through `nm-diffusion check-external`
- Verified test-suite execution on Python 3.10 and 3.14
- Config-driven end-to-end pipeline through `nm-pipeline`
- Standalone band-pass filtering command
- Leave-one-out GFC classification and left-right image flipping
- Desktop GUI preprocessing tab for motion, slice timing, deformation, and
  smoothing
- ALFF, zALFF, mALFF, fALFF, zfALFF, and mfALFF
- Nuisance regression and Friston-24 motion regressors
- Sphere ROI creation, ROI dilation, and deep-target coordinates
- Individual target mask construction from tissue segments
- Correlation thresholding and largest-cluster target selection
- CLI commands and an optional Tkinter desktop interface
- Separate `nm-preprocess` program for deformation, slice timing, motion
  resampling, and smoothing
- HTML target reports and SHA-256 output manifests for traceability

## What Is Not Included

This release does not reimplement SPM/FSL preprocessing. It includes an
approximate atlas-guided tissue probability estimator, but DARTEL-grade
segmentation, FSL BEDPOSTX tractography, and SPM/DARTEL-compatible
deformation-field estimation are not reproduced.
DICOM conversion is handled through `nm-dicom`, and other inputs should already
be in the expected NIfTI space or produced with existing preprocessing tools.
The decision record in `docs/decisions.md` explains why this boundary is
intentional.

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

Launch the desktop GUI:

```bash
.venv/bin/nm-toolbox gui
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

The verified wheel is `dist/neuroimaging_neuromodulation-0.16.0-py3-none-any.whl`.

## Documentation

- `docs/analysis.md` - source-code inventory and algorithm mapping
- `docs/production-readiness.md` - production readiness checklist
- `docs/completion-audit.md` - requirement-by-requirement audit
- `docs/source-repository.md` - source repository and redistribution note
- `docs/ci-validation.md` - CI validation branch notes
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
