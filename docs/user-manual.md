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
  --seed-deformation <iy-field.nii> \
  --mask-deformation <iy-field.nii> \
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
  --deformation <iy-field.nii> \
  --output <deformed.nii> \
  --order 0
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
`warped_moving.nii`, plus SPM-style `y_ac_coT1.nii` and `iy_ac_coT1.nii`.

### Validate a deformation field

```bash
.venv/bin/nm-preprocess validate-deformation \
  --moving <native-image.nii> \
  --field <iy-field.nii> \
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
  --output <tracks.tck> \
  --num-tracks 100000
```

### Check external tool availability

```bash
.venv/bin/nm-diffusion check-external
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

### Target site

```bash
.venv/bin/nm-tms target-site \
  --fc <SeedFCinROI.nii> \
  --output-dir <output> \
  --subject <subject-id> \
  --p 0.05 \
  --n 212 \
  --posneg Positive Negative
```

Outputs:

- MNI coordinate text files
- 5 mm extremum sphere targets
- largest-cluster masks
- 8 mm cluster-center sphere targets

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
