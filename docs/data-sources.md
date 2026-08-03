# Data Sources

## Bundled Template and Mask Data

The package includes real NIfTI assets copied from the original repository:

- `BrainMask_05_61x73x61.nii`
- `WhiteMask_09_61x73x61.nii`
- `CsfMask_07_61x73x61.nii`
- `excludHOAsub25prob617361.nii`
- SPM tissue probability templates `grey333.nii`, `grey.nii`, `white.nii`,
  `csf.nii`
- `AAL_618361.nii`
- `Yeo2011_7Nets_618361.nii`
- `ch2.nii`
- Yeo/JHU label text files

These are real anatomical reference files used by the original toolbox.

## Public fMRI Validation Data

One real adult subject from the Nilearn development fMRI dataset is downloaded
into `data/real_development_fmri/`:

- Dataset: OpenNeuro `ds000228`, movie-watching development dataset
- Nilearn fetcher: `nilearn.datasets.fetch_development_fmri`
- Subject: `sub-pixar123`
- Grid: 4 mm MNI, 50 x 59 x 50, 168 volumes
- Documented TR: 2.0 seconds

This data is used only for development and smoke tests. It is not clinical
evidence and must not be used to draw clinical conclusions.

## Original Example Data

In the local academic repository,
`Neuroimaging-and-Neuromodulation/ExampleData.zip` is included but contains
zero-byte placeholder DICOM files. It was inspected and explicitly not used.

## Real DICOM Validation Data

`data/real_dicom/hitachi/` contains a real four-slice Hitachi anatomical DICOM
series copied from the dicom2nifti project's test data. It is used only to
verify conversion behavior, not as clinical evidence.

Additional real vendor DICOM series are included under `data/real_dicom/` for
generic, GE, Philips, Siemens, and Hyperfine data. These are also copied from
the dicom2nifti project's test data and used only for conversion validation.

Compressed JPEG, JPEG-LS, JPEG2000, RLE, Siemens multiframe, and Philips
enhanced series are included under the same directory to validate conversion
edge cases.

## Stanford T1 Validation Data

The segmentation test uses DIPY's real Stanford T1 dataset, downloaded by
DIPY to `~/.dipy/stanford_hardi/t1.nii.gz` when available.

## Download Command

```bash
.venv/bin/nm-toolbox demo-data --output-dir data/real_development_fmri
```

Use the Tsinghua PyPI mirror for package installation in mainland China.
