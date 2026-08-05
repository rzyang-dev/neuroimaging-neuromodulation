# Gap Matrix

Status date: 2026-08-05

This matrix is the authoritative mapping from the original MATLAB/script
workflows to the Python package. Dependency class refers to the runtime
required by the Python implementation:

- `core`: NumPy, SciPy, NiBabel only
- `diffusion`: optional DIPY extra
- `dicom`: optional pydicom/dicom2nifti extra
- `external`: optional SPM/FSL/ANTs/SimNIBS provider
- `out-of-scope`: third-party or GUI-only code not ported

## Implemented Core

| Original source | Python implementation | Dependency class | Test evidence |
| --- | --- | --- | --- |
| `TMSReadNii.m`, `TMSWriteNii.m`, `TMSreslice.m` | `io/nifti.py` | core | `test_io.py` |
| `TMSmat2mni.m`, `TMSmni2mat.m` | `coordinates.py` | core | `test_coordinates.py` |
| `TMSfastCorr.m`, `TMSIdealFilter.m`, `TMSfilter.m`, `TMSdetrend.m` | `stats/functional.py` | core | `test_stats.py` |
| `TMSregression.m`, `rest_regress_ss.m` | `stats/regression.py`, `preprocess/covariates.py` | core | `test_regression_cli.py`, `test_covariates.py` |
| `TMSsphereROI.m`, `TMSExtendROI.m`, `TMSDeepTargetComp.m` | `targets/roi.py` | core | `test_targets.py` |
| `TMSSeedFC.m`, `TMSTargetSite.m`, `TMSLargeCluster.m` | `targets/pipeline.py`, `targets/cluster.py` | core | `test_targets.py`, `test_reporting.py` |
| `TMSSliceTiming.m`, `TMSRealign.m`, `TMSRealignEW.m` | `preprocess/temporal.py`, `preprocess/motion.py` | core | `test_temporal.py`, `test_motion.py` |
| `TMSfalff.m`, `dyALFF.m`, `WMSeedFC.m`, `WMMultiSeedFC.m` | `wm/alff.py`, `wm/dynamic.py`, `wm/seedfc.py` | core | `test_wm.py` |
| `HMCalc.m`, `y_FD_Jenkinson.m`, `TMSmkC6.m` | `preprocess/motion_metrics.py`, `segmentation/c6.py` | core | `test_preprocess.py` |
| `TMSwriteDTL.m`, deformation application | `io/deformations.py`, `deformations/estimate.py` | core | `test_deformations.py` |
| `TMSDicomConvert.m`, `DCM2NII` | `io/dicom.py` | dicom | `test_dicom.py` |
| `TMSDTIFIT.sh` | `diffusion/dti.py` | core | `test_dti_internal.py`, `test_diffusion.py` |
| `TMSProbTrack.sh`, `TMSTargetSC.m` | `diffusion/tracking.py`, `diffusion/connectivity.py` | diffusion | `test_diffusion.py` |
| `TMSRealign.m`, `TMSRealignEW.m`, `TMScoregister.m` | `preprocess/_registration.py`, `preprocess/motion.py`, `preprocess/coregister.py` | core | `test_motion.py`, `test_coregister.py` |

## Implemented Partial

| Original source | Python implementation | Remaining gap |
| --- | --- | --- |
| `restFC.m` | `stats/functional.py` ROI matrix | Full original voxel/ROI option set |
| `AFQTractValue.m`, `AFQplot.m`, `AFQstat.m` | `diffusion/tract_profile.py`, `wm/plots.py`, `wm/statistics.py` | Full AFQ numerical parity |
| `AFQ_SegmentFiberGroups.m`, `AFQ_removeFiberOutliers.m` | `diffusion/segmentation.py`, `diffusion/roi_segmentation.py`, `diffusion/outliers.py` | Full AFQ reference validation |
| `TrackQC.m`, `AFQ_RenderFibers.m`, `TMSviewer.m` | `wm/trackqc.py`, `diffusion/render.py`, `reporting/viewer.py` | Full original QC parity |
| `TMStargetT1.m`, `TMStargetT1_run.m` | `targets/t1.py` | Desktop and pipeline coverage |

## Implemented in This Slice

| Original source | Python implementation | Test evidence |
| --- | --- | --- |
| `TMSMNICenter.m` | `targets/center.py`, `nm-tms mni-center` | `test_target_center.py` |
| `TMSTPCalc.m` | `io/nifti.count_timepoints`, `nm-tms tp-calc` | `test_target_center.py` |
| `ConnFuncHomo.m`, `FuncHomoConn.m` | `wm/connectivity.py`, `nm-wm conn-homo` | `test_wm_connectivity.py` |
| `FCAsymIndex.m` | `wm/connectivity.py`, `nm-wm fc-asym` | `test_wm_connectivity.py` |
| `FCPatternAnalysis.m` | `wm/connectivity.py`, `nm-wm fc-pattern` | `test_wm_connectivity.py` |
| `MultiRunCalc.m` | `wm/multirun.py`, `nm-wm multi-run` | `test_multirun_subjects.py` |
| `SubjNameComp.m` | `wm/subjects.py`, `nm-wm validate-subjects` | `test_multirun_subjects.py` |

## Missing or Future Work

| Workflow | Dependency class | Next action |
| --- | --- | --- |
| Full original GUI orchestration (`WhiteFun`, `WhiteMatter`, `WhiteMatterSF`, `TSA`, `TMStargetFC`) | core | Expose equivalent guided workflows in `nm-app`/`nm-gui`, not GUI clones |
| Full AFQ/TrackQC numerical parity | core/diffusion | Add reference tests and complete subject-level pipeline |
| DIPY-independent deformation and probabilistic-tractography paths | core | Replace optional diffusion extra with internal implementations |
| DARTEL-grade normalization parity | external | Keep optional provider only; not required for normal use |
| SimNIBS field simulation | external | Optional provider integration only |

## Out of Scope

- `export_fig-master/`, `vistasoftScripts/`, `WMfun/slover/`, and other third-party MATLAB utilities are reference/vendor code.
- Original GUIDE screens are not cloned; their algorithmic workflows are ported into CLI, pipeline, and Python-native GUI actions.

This file is updated whenever implementation status changes. `docs/analysis.md`
should be treated as the algorithm inventory, while this file is the
requirement-by-requirement status record.
