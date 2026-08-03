# Source-Code Analysis

## Goal

The original MATLAB repository is a GUI-heavy academic toolbox. The production
value is not the GUI scaffolding but the data transformations behind it. This
document records the mapping from MATLAB functions to Python modules.

## Algorithm Inventory

| MATLAB source | Python implementation | Status |
| --- | --- | --- |
| `TMSReadNii.m`, `TMSWriteNii.m` | `io/nifti.py` | Implemented |
| `TMSDicomConvert.m`, `DCM2NII` | `io/dicom.py` | Implemented through dicom2nifti |
| `TMSmat2mni.m`, `TMSmni2mat.m` | `coordinates.py` | Implemented |
| `TMSfastCorr.m` | `stats/functional.py` | Implemented |
| `TMSIdealFilter.m`, `TMSfilter.m` | `stats/functional.py` | Implemented |
| `TMSregression.m` | `stats/regression.py` | Implemented |
| `TMSGFCClass.m` | `stats/classification.py` | Implemented |
| `TMSFlipImageLR.m` | `preprocess/imaging.py` | Implemented |
| `TMSfalff.m` | `wm/alff.py` | Implemented |
| `TMSsphereROI.m` | `targets/roi.py` | Implemented |
| `TMSExtendROI.m` | `targets/roi.py` | Implemented |
| `TMSDeepTargetComp.m` | `targets/roi.py` | Implemented |
| `TMSSeedFC.m` | `targets/pipeline.py` | Implemented |
| `TMSLargeCluster.m` | `targets/cluster.py` | Implemented |
| `TMSTargetSite.m` | `targets/pipeline.py` | Implemented |
| `mkWMmask.m`, `mkGMmask.m` | `wm/masks.py` | Implemented |
| `TMSSliceTiming.m` | `preprocess/temporal.py` | Implemented with Fourier interpolation |
| `TMSRealign.m`, `TMSRealignEW.m` | `preprocess/motion.py`, `preprocess/temporal.py` | Rigid motion estimation and resampling implemented through DIPY |
| `TMScoregister.m` | `preprocess/coregister.py` | Implemented with DIPY affine registration |
| `TMSSegDartel.m`, `TMSseg.m` | `segmentation/tissue.py` | Approximate atlas-guided GM/WM/CSF estimation; DARTEL normalization remains external |
| `TMSwriteDTL.m` | `io/deformations.py`, `deformations/estimate.py` | SPM-style `iy_` fields applied; DIPY nonlinear fields estimated and converted to `y_`/`iy_` fields |
| `TMSDTIFIT.sh`, `TMSTargetSC.m` | `diffusion/` | Tensor fitting, deterministic tractography, connectivity implemented with DIPY; probabilistic FSL workflow not reproduced |
| `TMSProbTrack.sh` | `diffusion/tracking.py` | DIPY-based probabilistic tensor tractography; FSL BEDPOSTX not reproduced |
| `TMSProbTrack.sh`, `TMSBEDPOSTX.sh`, `TMSDTIFIT.sh` | `diffusion/external.py` | Optional FSL/MRtrix binary wrappers |
| `TMSSmooth.m` | `preprocess/spatial.py` | Implemented as Gaussian smoothing |

## Data Flow

The package intentionally follows a data-oriented model:

1. Read real NIfTI inputs.
2. Validate grid alignment or resample masks into the functional grid.
3. Apply numerical transforms with SciPy/NumPy.
4. Write NIfTI outputs and text coordinate files with traceable paths.
5. Record provenance in `docs/data-sources.md`.

## Preprocessing Boundary

SPM and FSL are not installed, and the project requirement says to avoid
heavyweight dependencies when possible. Reimplementing SPM segmentation,
deformation-field estimation, and FSL eddy correction inside this package would
be a large research project by itself and would not be honest to ship as a
stable replacement. Motion estimation and coregistration are implemented
through DIPY. The implemented package accepts already preprocessed NIfTI data
for the analysis layer and applies existing inverse deformation fields when
they are available.
