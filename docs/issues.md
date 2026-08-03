# Known Issues and Limitations

## Functional and Release Issues

1. SPM/DARTEL-compatible normalization is not fully reproduced.

   This package can apply existing inverse deformation fields and estimate
   nonlinear mappings with DIPY. It now emits SPM-style `y_ac_coT1.nii` and
   `iy_ac_coT1.nii` fields in the documented 1-based convention, but exact
   SPM/DARTEL numerical compatibility is not guaranteed.

2. Vendor-specific DICOM edge cases may require manual review.

   DICOM conversion is implemented through dicom2nifti, and `nm-dicom inspect`
   / `validate-series` help catch ambiguous input before conversion. Tests now
   cover generic, GE, Philips, Siemens, Hyperfine, and Hitachi series.

3. Tissue segmentation is approximate and not DARTEL-grade.

   Atlas-guided GM/WM/CSF probability estimation is implemented for common T1
   data. Validated SPM/DARTEL segmentation remains recommended for clinical or
   publication-grade normalization.

4. FSL BEDPOSTX-based probabilistic tractography is optional.

   DIPY-based tensor fitting, deterministic and probabilistic tensor
   tractography, and seed-target connectivity are implemented. FSL
   BEDPOSTX/PROBTRACKX and MRtrix commands are available as optional wrappers
   when the external binaries are installed.

5. The GUI is optional and not tested in headless CI.

6. Deformation-field support currently targets SPM-style inverse fields
   (`iy_*.nii`). Forward `y_*.nii` fields are not inverted automatically.

## Data Issues

1. `ExampleData.zip` contains zero-byte placeholder DICOMs and is not usable.
2. The real development-fMRI NIfTI header reports a fourth-dimension zoom of
   1.0, while Nilearn reports TR=2.0. Tests use the documented TR=2.0.
3. The downloaded public fMRI subject is for validation, not for clinical
   claims.

## Recommended Next Work

- Validate estimated `y_*.nii` / `iy_*.nii` fields against SPM/DARTEL output on
  a shared reference dataset.
- Add validated DARTEL-compatible normalization integration.
- Validate FSL/MRtrix wrapper commands against installed binary versions.
- Add an HTML or web report for target coordinates and QC images.
