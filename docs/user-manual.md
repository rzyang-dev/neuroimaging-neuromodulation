# User Manual

## Install

Create and use the project virtual environment:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e ".[test]"
```

## Command-Line Interface

### Seed-based FC

```bash
.venv/bin/nm-tms seed-fc \
  --functional <4D fMRI.nii> \
  --seed <seed.nii> \
  --mask <analysis-mask.nii> \
  --seed-deformation <y-field.nii> \
  --mask-deformation <y-field.nii> \
  --target-mask <target-roi-mni.nii> \
  --c6 <c6ac_coT1.nii> \
  --c1 <c1ac_coT1.nii> \
  --depth-mm <depth-in-mm> \
  --tr 2.0 \
  --low-cutoff 0.01 \
  --high-cutoff 0.1 \
  --output-dir <output> \
  --subject <subject-id>
```

Outputs:

- `<output>/<subject>/SeedFCinWB.nii`
- `<output>/<subject>/SeedFCinROI.nii`

### Apply a deformation field

```bash
.venv/bin/nm-preprocess deform \
  --source <native-image.nii> \
  --deformation <y-field.nii> \
  --output <deformed.nii> \
  --order 0 \
  --coordinate-system world
```

### Slice timing correction

```bash
.venv/bin/nm-preprocess slice-timing \
  --functional <4D fMRI.nii> \
  --output <slice-timed.nii> \
  --tr 2.0 \
  --slice-order 1,3,5,2,4 \
  --ref-slice 3
```

### Motion resampling from realignment parameters

```bash
.venv/bin/nm-preprocess motion-correct \
  --functional <4D fMRI.nii> \
  --rp <rp-file.txt> \
  --output <motion-corrected.nii> \
  --order 1
```

### Estimate motion parameters

```bash
.venv/bin/nm-preprocess estimate-motion \
  --functional <4D fMRI.nii> \
  --output <motion-corrected.nii> \
  --rp-output <rp-file.txt> \
  --reference 0 \
  --pipeline translation,rigid \
  --level-iters 20,10,5
```

### Band-pass filter

```bash
.venv/bin/nm-preprocess filter \
  --functional <4D fMRI.nii> \
  --mask <analysis-mask.nii> \
  --output <filtered.nii> \
  --tr 2.0 \
  --low-cutoff 0.01 \
  --high-cutoff 0.1
```

### Generic linear regression

```bash
.venv/bin/nm-preprocess regress \
  --y <response.txt> \
  --x <design.txt> \
  --beta-output <beta.txt> \
  --residual-output <residual.txt>
```

### Nuisance regression

```bash
.venv/bin/nm-preprocess regress-covariates \
  --functional <4D fMRI.nii> \
  --rp <rp-file.txt> \
  --wm-mask <white-matter-mask.nii> \
  --csf-mask <csf-mask.nii> \
  --global-mask <brain-mask.nii> \
  --output <regressed.nii>
```

### Extract signal from a mask

```bash
.venv/bin/nm-preprocess extract-signal \
  --functional <4D fMRI.nii> \
  --mask <mask.nii> \
  --output <signal.txt>
```

### Friston-24 regressors

```bash
.venv/bin/nm-preprocess friston24 \
  --rp <rp-file.txt> \
  --output <friston24.txt>
```

### Flip left-right

```bash
.venv/bin/nm-preprocess flip-lr \
  --image <image.nii> \
  --output <flipped.nii>
```

### Coregister a volume

```bash
.venv/bin/nm-preprocess coregister \
  --moving <moving.nii> \
  --static <static.nii> \
  --output <coregistered.nii> \
  --affine-output <affine.txt>
```

### GFC classification

```bash
.venv/bin/nm-tms classify-gfc \
  --matrix <features-by-subjects.npy> \
  --n-group1 3 \
  --output <scores.txt>
```

### Diffusion tensor fitting

```bash
.venv/bin/nm-diffusion fit-tensor \
  --dwi <dwi.nii> \
  --bval <bval> \
  --bvec <bvec> \
  --output-dir <output-dir>
```

### Deterministic tractography

```bash
.venv/bin/nm-diffusion track \
  --dwi <dwi.nii> \
  --bval <bval> \
  --bvec <bvec> \
  --seed <seed-mask.nii> \
  --stop <fa-map.nii> \
  --output <tracks.trk>
```

### Probabilistic tensor tractography

```bash
.venv/bin/nm-diffusion track-probabilistic \
  --dwi <dwi.nii> \
  --bval <bval> \
  --bvec <bvec> \
  --seed <seed-mask.nii> \
  --stop <fa-map.nii> \
  --output <probabilistic-tracks.trk>
```

### Seed-target structural connectivity

```bash
.venv/bin/nm-diffusion connectivity \
  --dwi <dwi.nii> \
  --bval <bval> \
  --bvec <bvec> \
  --seed <seed-mask.nii> \
  --target <target-mask.nii> \
  --stop <fa-map.nii> \
  --trk-output <tracks.trk> \
  --count-output <count.json>
```

### Tract profile extraction

```bash
.venv/bin/nm-diffusion tract-profile \
  --tracks <tracks.trk> \
  --scalar <ALFF.nii> \
  --output <profile.npy> \
  --output-csv <profile.csv> \
  --n-points 100

.venv/bin/nm-diffusion segment-tracts \
  --tracks <tracks.trk> \
  --atlas <JHUtractsThr25_3mm.nii> \
  --output-json <segmentation.json> \
  --n-samples 50

.venv/bin/nm-diffusion segment-tracts-roi \
  --tracks <tracks.trk> \
  --output-json <roi-segmentation.json> \
  --min-dist 2.0

.venv/bin/nm-diffusion transform-tracts \
  --tracks <native-tracks.trk> \
  --field <iy_ac_coT1.nii> \
  --source <native-T1.nii> \
  --reference <MNI-template.nii> \
  --output <mni-tracks.trk>

.venv/bin/nm-diffusion render-tracts \
  --tracks <tracks.trk> \
  --atlas <JHUtractsThr25_3mm.nii> \
  --output <tract-render.html> \
  --title "Tract QC"

.venv/bin/nm-diffusion clean-tracts \
  --tracks <tracks.trk> \
  --reference <T1.nii> \
  --output <cleaned.trk> \
  --keep-json <keep.json> \
  --max-dist 4.0 \
  --max-len 4.0

.venv/bin/nm-diffusion afq-pipeline \
  --tracks <tracks.trk> \
  --atlas <JHUtractsThr25_3mm.nii> \
  --scalar <ALFF.nii> \
  --output-dir <subject-afq> \
  --num-nodes 30 \
  --method roi \
  --min-dist 2.0
```

### DICOM series conversion

```bash
.venv/bin/nm-dicom convert-series \
  --dicom-dir <dicom-series-directory> \
  --output <output.nii>
```

### DICOM directory conversion

```bash
.venv/bin/nm-dicom convert-dir \
  --dicom-dir <dicom-directory> \
  --output-dir <output-directory>
```

### Inspect DICOM series metadata

```bash
.venv/bin/nm-dicom inspect \
  --dicom-dir <dicom-directory> \
  --output-json <summary.json>
```

### Validate a single DICOM series

```bash
.venv/bin/nm-dicom validate-series \
  --dicom-dir <dicom-series-directory>
```

### Tissue probability estimation

```bash
.venv/bin/nm-preprocess segment-tissue \
  --t1 <T1.nii> \
  --output-dir <output-directory>
```

Outputs `c1.nii`, `c2.nii`, `c3.nii`, and `SegLabel.nii`.

### Estimate a nonlinear deformation

```bash
.venv/bin/nm-preprocess estimate-deformation \
  --moving <native-T1.nii> \
  --static <mni-template.nii> \
  --output-dir <output-directory> \
  --level-iters 10,10,5
```

Outputs include `dipy_mapping.nii.gz`, `coordinate_field.nii`, and
`warped_moving.nii`, plus SPM world-coordinate `y_ac_coT1.nii` and
`iy_ac_coT1.nii` fields. `y_ac_coT1.nii` is the template-to-native pullback
field for `apply_deformation`; `iy_ac_coT1.nii` is the native-to-template
forward field for streamline transforms.

### Validate a deformation field

```bash
.venv/bin/nm-preprocess validate-deformation \
  --moving <native-image.nii> \
  --field <y-field.nii> \
  --reference <reference-warped.nii> \
  --output-json <validation.json>
```

### Validate two aligned images

```bash
.venv/bin/nm-preprocess validate-image \
  --reference <reference.nii> \
  --test <test.nii> \
  --output-json <validation.json>
```

### FSL probtrackx wrapper

```bash
.venv/bin/nm-diffusion fsl-probtrackx \
  --seed <seed.nii> \
  --target <target.nii> \
  --bedpostx-dir <bedpostx-dir> \
  --output-dir <output-dir>
```

Add `--dry-run` to print the command without executing it.

### MRtrix tckgen wrapper

```bash
.venv/bin/nm-diffusion mrtrix-tckgen \
  --dwi <dwi.nii> \
  --mask <mask.nii> \
  --seed-image <seed.nii> \
  --output <tracks.tck> \
  --num-tracks 100000
```

`--seed-image` is required because MRtrix needs at least one streamline seeding
source.

### Check external tool availability

```bash
.venv/bin/nm-diffusion check-external
```

The command reports availability of `bedpostx`, `dtifit`, `probtrackx2`, and
`tckgen` found on `PATH`. FSL binaries must be reachable on `PATH` (for
example after `source $FSLDIR/etc/fslconf/fsl.sh`); MRtrix `tckgen` is found
normally. On the development machine the FSL/MRtrix binaries are installed
inside WSL, so run the check there, for example:

```bash
wsl bash -lc "source /home/dev/fsl/etc/fslconf/fsl.sh; ~/nm-dev-venv/bin/nm-diffusion check-external"
```

### End-to-end pipeline

Create a JSON config from [configs/pipeline.example.json](/Users/ginger/Documents/workspace/configs/pipeline.example.json), then run:

```bash
.venv/bin/nm-pipeline run pipeline.config.json
```

The pipeline can convert DICOM directories, apply slice timing, estimate
motion, compute seed FC, generate target candidates, and write an HTML report
with a SHA-256 manifest.

### Spatial smoothing

```bash
.venv/bin/nm-preprocess smooth \
  --functional <4D fMRI.nii> \
  --fwhm 4.0 \
  --output <smoothed.nii>
```

### Generate a target report and manifest

```bash
.venv/bin/nm-tms report \
  --output-dir <result-dir> \
  --subject <subject-id>
```

This writes `report.html` and `manifest.json` under the subject directory.

### Image QC viewer

```bash
.venv/bin/nm-tms view-report \
  --reference <T1.nii> \
  --target <StiTargetPosiPt_T1Sp.nii> \
  --output <viewer.html> \
  --slices 9
```

### Target site

```bash
.venv/bin/nm-tms target-site \
  --fc <SeedFCinROI.nii> \
  --output-dir <output> \
  --subject <subject-id> \
  --p 0.05 \
  --n 212 \
  --posneg Positive Negative \
  --native-deformation <y-field.nii>
```

Outputs:

- MNI coordinate text files
- 5 mm extremum sphere targets
- largest-cluster masks
- 8 mm cluster-center sphere targets
- Optional `*_T1Sp.nii` target spheres when `--native-deformation` is supplied

### Sphere ROI

```bash
.venv/bin/nm-tms sphere \
  --center 0,0,0 \
  --radius 5 \
  --reference <template.nii> \
  --output <sphere.nii>
```

### Deep target

```bash
.venv/bin/nm-tms deep-target \
  --tissue <c1-grey.nii> \
  --center 0,0,0 \
  --radius 40 \
  --depth 6 \
  --output <coordinates.txt>
```

### ALFF/fALFF

```bash
.venv/bin/nm-wm alff \
  --functional <4D fMRI.nii> \
  --mask <mask.nii> \
  --output-dir <output> \
  --tr 2.0 \
  --low-cutoff 0.01 \
  --high-cutoff 0.1
```

Outputs:

- `ALFF.nii`
- `zALFF.nii`
- `mALFF.nii`
- `fALFF.nii`
- `zfALFF.nii`
- `mfALFF.nii`

### White-matter and grey-matter masks

```bash
.venv/bin/nm-wm wm-mask \
  --functional <4D fMRI.nii> \
  --segment <c2-white-segment.nii> \
  --exclude <HOA-exclusion.nii> \
  --output-dir <output> \
  --threshold 0.9
```

## Desktop GUI

Run:

```bash
.venv/bin/nm-toolbox gui
```

This launches the guided end-user app.

For the advanced tabbed desktop interface, run:

```bash
.venv/bin/nm-gui
```

The advanced GUI has tabs:

- TMS Target: choose functional, seed, mask, and output paths; run seed FC or
  generate target candidates.
- White Matter: choose functional and mask; run ALFF/fALFF.
- Preprocess: estimate motion, coregister volumes, correct slice timing, apply
  deformation fields, or smooth images.
- Utilities: create sphere ROIs or compute deep-target coordinates.

The GUI requires Tkinter, which is included with many Python distributions.

### End-user app

For a simpler guided workflow, run:

```bash
.venv/bin/nm-app
```

The end-user app provides three steps: Data, Settings, and Run and Results.
After analysis, it can open the HTML report and output folder directly.

## Additional Ported Commands

### White-matter seed FC

```bash
.venv/bin/nm-wm seed-fc \
  --functional <4D fMRI.nii> \
  --seed <seed.nii> \
  --mask <mask.nii> \
  --output <zFCmap.nii>

.venv/bin/nm-wm multi-seed-fc \
  --functional <4D fMRI.nii> \
  --seeds <seed1.nii> <seed2.nii> \
  --mask <mask.nii> \
  --output-dir <output>
```

### Dynamic ALFF, group masks, and tract reporting

```bash
.venv/bin/nm-wm dynamic-alff \
  --functional <4D fMRI.nii> \
  --mask <mask.nii> \
  --output-dir <output> \
  --tr 2.0 \
  --window-length 50 \
  --step 5

.venv/bin/nm-wm group-mask \
  --segments <c2-subject1.nii> <c2-subject2.nii> \
  --output <group-wm.nii> \
  --threshold 0.9 \
  --group-threshold 0.9

.venv/bin/nm-wm cluster-report \
  --result <statistic.nii> \
  --output-dir <output>

.venv/bin/nm-wm plot-profiles \
  --profiles <profile1.npy> <profile2.npy> \
  --n-group1 3 \
  --output-dir <plots> \
  --labels "Left Corticospinal" "Right Corticospinal"

.venv/bin/nm-wm afq-stat \
  --profiles <profile1.npy> <profile2.npy> \
  --n-group1 3 \
  --output-json <afq-stat.json>

.venv/bin/nm-wm tract-qc \
  --profiles <profile1.npy> <profile2.npy> \
  --n-group1 3 \
  --segmentation-json <segmentation.json> \
  --output-dir <qc-report>
```

### Head-motion QC and c6 mask

```bash
.venv/bin/nm-preprocess motion-metrics \
  --rp <rp.txt> \
  --reference <mean-fundata.nii> \
  --output-json <motion.json>

.venv/bin/nm-preprocess make-c6 \
  --t1 <ac_coT1.nii> \
  --output <c6ac_coT1.nii>
```

### T1-space target image

```bash
.venv/bin/nm-tms t1-target \
  --target <target-roi-mni.nii> \
  --t1 <ac_coT1.nii> \
  --output <IndiTarget_T1Sp.nii> \
  --deformation <y-field.nii>
```

If `--deformation` is omitted, `nm-tms t1-target` runs SPM25 standalone
segmentation automatically to generate the `y_` field, then writes the
individualized target into T1 space. Use `--spm-exe` and `--spm-dir` to point
to the standalone executable and segmentation output directory.

### Group statistics

```bash
.venv/bin/nm-tms roi-fc \
  --functional <4D fMRI.nii> \
  --rois <roi1.nii> <roi2.nii> \
  --output <roi-fc.txt>

.venv/bin/nm-tms compare-correlations \
  --r1 0.8 --r2 0.2 --n1 50 --n2 50 \
  --tail both \
  --output <comparison.txt>

.venv/bin/nm-tms chi-square \
  --matrix <contingency.txt> \
  --output <pvalue.txt>

.venv/bin/nm-tms ttest2-covariates \
  --y <dependent.txt> \
  --group <group-labels.txt> \
  --covs <covariates.txt> \
  --output-json <result.json>

.venv/bin/nm-tms quantreg \
  --x <predictor.txt> \
  --y <response.txt> \
  --tau 0.5 \
  --order 1 \
  --nboot 200 \
  --output-json <quantreg.json>

.venv/bin/nm-tms permutation-ttest \
  --y <response.txt> \
  --group <group-labels.txt> \
  --n-permutations 5000 \
  --output-json <permutation.json>
```

### Utility commands

```bash
.venv/bin/nm-preprocess combine-images \
  --images <image1.nii> <image2.nii> \
  --operation sum \
  --output <combined.nii>

.venv/bin/nm-preprocess concatenate-sessions \
  --images <run1.nii> <run2.nii> \
  --operation add \
  --output <fundata.nii>

.venv/bin/nm-preprocess merge-images \
  --images <session1.nii> <session2.nii> \
  --output <merged.nii>

.venv/bin/nm-preprocess reslice \
  --source <image-to-resample.nii> \
  --sample <reference-grid.nii> \
  --output <resliced.nii> \
  --order 0

.venv/bin/nm-preprocess extract-signal \
  --functional <directory-of-3d-nifti-or-4d.nii> \
  --mask <mask.nii> \
  --output <signal.txt>

.venv/bin/nm-preprocess timepoint-count \
  --input <4D NIfTI or directory> \
  --output <timepoints.tsv>

.venv/bin/nm-preprocess detrend \
  --functional <4D fMRI.nii> \
  --output <detrended.nii>

.venv/bin/nm-preprocess text-to-nifti \
  --text <data.txt> \
  --output <data.nii> \
  --shape 100,100,100
```

### DICOM series selection

```bash
.venv/bin/nm-dicom inspect --dicom-dir <directory>
.venv/bin/nm-dicom convert-series-index \
  --dicom-dir <directory> \
  --index 0 \
  --output <series.nii>
```

### Additional FSL workflows

```bash
.venv/bin/nm-diffusion fsl-bet --input <data.nii> --output <dataB.nii>
.venv/bin/nm-diffusion fsl-eddy-correct --input <dataB.nii> --output <dataBC.nii.gz>
.venv/bin/nm-diffusion fsl-fa2t1 --fa <FA.nii> --ref <dataB.nii> --output <FAinT1.nii> --matrix <FA2T1.mat> --inverse-matrix <T12FA.mat>
.venv/bin/nm-diffusion fsl-t12mni --t1 <dataB.nii> --mni <MNI.nii> --out-prefix <warp-prefix>
.venv/bin/nm-diffusion fsl-mni2native --image <SeedImage.nii> --t1 <dataB.nii> --fa <FA.nii> --warp <MNI2T1transf.nii.gz> --premat <T12FA.mat> --output <SeedImage_NaSp.nii>
.venv/bin/nm-diffusion fsl-native2mni --image <Fiber.nii> --t1 <dataB.nii> --fa <FA.nii> --matrix <FA2T1.mat> --warp <T12MNItransf.nii.gz> --mni <MNI.nii> --output <Fiber_MNISp.nii>
.venv/bin/nm-diffusion fsl-topup --imain <data_appa_b0.nii> --pa-image <datapa.nii> --datain <para.txt> --config <b02b0.cnf> --output-prefix <Topup_Output> --output <my_hifi_data.nii>
```

All FSL commands support `--dry-run` to print the command without executing.

### ANTs normalization

```bash
.venv/bin/nm-preprocess ants-register \
  --moving <native-T1.nii> \
  --fixed <MNI-template.nii> \
  --output-prefix <warp-prefix>

.venv/bin/nm-preprocess ants-apply-transform \
  --input <native-image.nii> \
  --reference <MNI-template.nii> \
  --output <mni-image.nii> \
  --transforms <warp-prefix1Warp.nii.gz> <warp-prefix0GenericAffine.mat>

.venv/bin/nm-preprocess check-ants
```

## Input Data Expectations

- Functional images should be 3D or 4D NIfTI.
- Seed and mask images should be in a related world space.
- Masks are resampled into the functional grid when necessary.
- For target-site generation, the input FC map should be a 3D NIfTI.
- For individualized target masks, provide a target image, c6 tissue image, and
  optionally a c1 grey-matter image.

## Output Conventions

- NIfTI outputs are float32 unless the input dtype is explicitly preserved.
- MNI coordinate text files list `x y z` plus an optional value column.
- ROI masks are binary 0/1 float images.

## Safety Notes

This is research software. TMS targeting is a medical decision. Do not use
output coordinates for clinical stimulation without review by a qualified
clinician, validation against the subject's own images, and confirmation with
the neuronavigation system.
