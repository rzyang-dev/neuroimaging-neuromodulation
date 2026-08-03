# Requirements and Planning

## Stakeholder Requirements

1. Transform the MATLAB academic project into a production-oriented Python
   package.
2. Use an isolated virtual environment.
3. Do not invent mock clinical data.
4. Keep decisions based on real, reliable data.
5. Keep comprehensive records.
6. Prefer lightweight Python implementations over heavyweight external tools.
7. Respect system resources.
8. Use Nilearn to obtain real data for development.
9. Support mainland China network constraints through mirrors.

## Functional Requirements

- Load and save 3D/4D NIfTI images.
- Convert DICOM series and directories to NIfTI.
- Estimate GM/WM/CSF tissue probability maps from a T1 image.
- Estimate nonlinear deformation fields between two images.
- Resample seed and mask images into the functional grid.
- Apply SPM-style inverse deformation fields.
- Correct slice timing without MATLAB.
- Resample functional volumes using existing realignment parameter files.
- Estimate rigid motion parameters from a 4D functional series.
- Band-pass filter a functional series through a standalone command.
- Fit diffusion tensors, run deterministic tractography, and count seed-target
  structural connections.
- Run probabilistic tensor tractography with a documented DIPY-based method.
- Compute seed-based functional connectivity.
- Filter fMRI time series with the original ideal-frequency algorithm.
- Compute ALFF/fALFF family of maps.
- Regress nuisance signals from fMRI data.
- Create spherical ROIs from MNI coordinates.
- Dilate ROIs.
- Compute deep target coordinates.
- Build an individualized target mask.
- Find positive/negative target candidates and largest clusters.
- Provide a command-line interface.
- Provide an optional desktop GUI.
- Provide a config-driven end-to-end pipeline.

## Non-Functional Requirements

- Python-only analysis path for implemented algorithms.
- No MATLAB, SPM, or FSL required for implemented algorithms.
- Tests should run without a GPU and with modest memory.
- CLI and GUI should not require knowledge of MATLAB.
- Documentation must clearly separate implemented behavior from future work.

## Scope Decision

This release covers the analysis and target-selection layer plus application of
existing deformation fields, slice timing, motion estimation, coregistration,
DICOM conversion, approximate tissue probability estimation, DTI fitting,
deterministic and probabilistic tensor tractography, and motion-parameter
resampling. Nonlinear deformation estimation is available through DIPY, but
DARTEL-grade segmentation, SPM-compatible deformation conventions, and FSL
BEDPOSTX tractography are outside this release because replacing SPM/FSL
reliably is not feasible within the lightweight-dependency constraint.
