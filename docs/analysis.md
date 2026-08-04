# Source-Code Analysis

## Goal

The original MATLAB repository is a GUI-heavy academic toolbox. The production
value is not the GUI scaffolding but the data transformations behind it. This
document records the mapping from MATLAB functions to Python modules.

## Algorithm Inventory

| MATLAB source | Python implementation | Status |
| --- | --- | --- |
| `TMSReadNii.m`, `TMSWriteNii.m` | `io/nifti.py` | Implemented |
| `TMSreslice.m` | `io/nifti.py`, `cli/preprocess.py` | Implemented as resample/reslice command |
| `TMSDicomConvert.m`, `DCM2NII` | `io/dicom.py` | Implemented through dicom2nifti |
| `TMSmat2mni.m`, `TMSmni2mat.m` | `coordinates.py` | Implemented |
| `TMSfastCorr.m` | `stats/functional.py` | Implemented |
| `TMSIdealFilter.m`, `TMSfilter.m` | `stats/functional.py` | Implemented |
| `TMSdetrend.m` | `stats/functional.py`, `cli/preprocess.py` | Implemented as detrend command |
| `txt2nii.sh` | `io/nifti.py`, `cli/preprocess.py` | Implemented as text-to-nifti command |
| `restFC.m` | `stats/functional.py`, `cli/tms.py` | ROI-wise FC matrix implemented; full REST voxel/ROI option set remains partial |
| `TMSregression.m` | `stats/regression.py` | Implemented |
| `rest_regress_ss.m` | `preprocess/covariates.py`, `stats/regression.py` | Implemented with CLI and pipeline integration |
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
| `TMSwriteDTL.m` | `io/deformations.py`, `deformations/estimate.py` | SPM world-coordinate `y_`/`iy_` fields applied; DIPY nonlinear fields converted to matching `y_`/`iy_` fields |
| `TMSDTIFIT.sh`, `TMSTargetSC.m` | `diffusion/` | Tensor fitting, deterministic tractography, connectivity implemented with DIPY; probabilistic FSL workflow not reproduced |
| `TMSProbTrack.sh` | `diffusion/tracking.py` | DIPY-based probabilistic tensor tractography; FSL BEDPOSTX not reproduced |
| `TMSProbTrack.sh`, `TMSBEDPOSTX.sh`, `TMSDTIFIT.sh` | `diffusion/external.py` | Optional FSL/MRtrix binary wrappers |
| `TMSSmooth.m` | `preprocess/spatial.py` | Implemented as Gaussian smoothing |
| `WMSeedFC.m`, `WMMultiSeedFC.m` | `wm/seedfc.py` | Implemented for Python-native FC workflows |
| `HMCalc.m`, `y_FD_Jenkinson.m` | `preprocess/motion_metrics.py` | Implemented as Python motion-QC metrics |
| `dyALFF.m` | `wm/dynamic.py` | Implemented as sliding-window dynamic ALFF |
| `TMSCluRep4WM.m` | `wm/tracts.py` | Implemented with bundled JHU tract templates |
| `TMSmkC6.m` | `segmentation/c6.py` | Implemented as approximate outer-brain mask |
| `TMSimgcomp.m` | `preprocess/imaging.py`, `cli/preprocess.py` | Implemented as combine-images command |
| `TMStargetT1_run.m` | `targets/t1.py`, `cli/tms.py`, `pipeline/run.py` | Implemented: writes MNI ROI into T1 space; optional SPM25 segmentation integration |
| `AFQTractValue.m` | `diffusion/tract_profile.py`, `cli/diffusion.py` | Partial: Python-native tract-profile extraction; AFQ 20-tract segmentation remains external |
| `AFQplot.m` | `wm/plots.py`, `cli/wm.py` | Partial: group profile SVG plots implemented; full AFQ rendering remains external |
| `AFQstat.m` | `wm/statistics.py`, `cli/wm.py` | Partial: per-node group profile statistics implemented; full AFQ statistical workflow remains external |
| `AFQ_SegmentFiberGroups.m` | `diffusion/segmentation.py`, `diffusion/roi_segmentation.py`, `cli/diffusion.py` | ROI-based and atlas-based segmentation implemented; original spatial-normalization integration remains external |
| `AFQ_removeFiberOutliers.m` | `diffusion/outliers.py`, `cli/diffusion.py` | Implemented as Python outlier cleaning with length and Mahalanobis distance criteria |
| `AFQ_TrackAndSegmentOneSub.m` | `diffusion/afq.py`, `diffusion/transform.py`, `cli/diffusion.py` | Partial: subject-level atlas/ROI pipeline and streamline transforms implemented; validated SPM/ANTS normalization remains external |
| `dtiXformFiberCoords.m` | `diffusion/transform.py`, `cli/diffusion.py` | Implemented as deformation-field streamline transform |
| `ANTS_normalize.m` | `preprocess/ants.py`, `cli/preprocess.py` | Partial: ANTs command builders implemented; validated normalization remains external |
| `TrackQC.m` | `wm/trackqc.py`, `cli/wm.py` | Partial: HTML QC report implemented; fiber-rendering visualization remains external |
| `AFQ_RenderFibers.m` | `diffusion/render.py`, `cli/diffusion.py` | Partial: HTML/SVG 2D projections implemented; interactive 3D rendering remains external |
| `TMSviewer.m` | `reporting/viewer.py`, `cli/tms.py` | Partial: HTML/SVG slice viewer implemented; interactive MATLAB viewer remains external |
| `CompCoefs.m`, `chi2test2.m`, `TMSttest2_cov.m`, `quantreg.m` | `stats/group.py`, `cli/tms.py` | Implemented as Python group-statistics commands |
| `TwoSamTTest.sh` | `stats/group.py`, `cli/tms.py` | Partial: permutation t-test implemented; FSL Randomise integration remains external |
| `TMSBET.sh`, `TMSEddyCorr.sh`, `topup.sh`, `TMSFA2T1.sh`, `TMSMNI2Native.sh`, `TMSNative2MNI.sh`, `TMST12MNI.sh` | `diffusion/external.py`, `cli/diffusion.py` | FSL command builders and dry-run workflows |

## Data Flow

The package intentionally follows a data-oriented model:

1. Read real NIfTI inputs.
2. Validate grid alignment or resample masks into the functional grid.
3. Apply numerical transforms with SciPy/NumPy.
4. Write NIfTI outputs and text coordinate files with traceable paths.
5. Record provenance in `docs/data-sources.md`.

## Preprocessing Boundary

SPM and FSL are optional external runtimes; the project requirement is to avoid
heavyweight dependencies in the core package. Reimplementing SPM segmentation,
deformation-field estimation, and FSL eddy correction inside this package would
be a large research project by itself and would not be honest to ship as a
stable replacement. Motion estimation and coregistration are implemented
through DIPY. The implemented package accepts already preprocessed NIfTI data
for the analysis layer and applies SPM world-coordinate `y_`/`iy_` fields when
they are available; the convention is validated against SPM25 output.

## Missing Source Inventory

The original repository contains more than the algorithm table above. The
following source groups are present in the local MATLAB workspace but have no
equivalent Python implementation:

- White-matter workflows: `TractMS2Nii.m`, `TMSmerge.sh`, `TwoSamTTest.sh`,
  `txt2nii.sh`
- T1 target workflows: `TMStargetT1.m`, `TMStargetT1_run.m`
- Utility/QC workflows: `TMSSloverSPM.m`, `TMSwrite.m`, `TMSreslice_GUI.m`,
  `TMSsphereROI_GUI.m`, `TMSUtility_GUI.m`, `TMSFC_GUI.m`, `WhiteFun.m`,
  `WhiteMatter.m`, `WhiteMatterSF.m`

The following originally missing items now have Python-native or wrapper
implementations and should be treated as partial ports: `WMSeedFC`,
`WMMultiSeedFC`, `HMCalc`, `y_FD_Jenkinson`, `dyALFF`, `TMSCluRep4WM`,
`TMSmkC6`, `TMSBET.sh`, `TMSEddyCorr.sh`, `topup.sh`, `TMSFA2T1.sh`,
`TMSMNI2Native.sh`, `TMSNative2MNI.sh`, `TMST12MNI.sh`, and
`TMSimgcomp.m`.

Status entries in this document that say "Implemented" should be read as
"implemented in the Python subset" unless the table explicitly claims exact
MATLAB/SPM/FSL equivalence.
