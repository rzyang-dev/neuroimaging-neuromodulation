# Known Issues and Limitations

## Functional and Release Issues

1. SPM/DARTEL-compatible normalization is not fully reproduced.

   This package can apply SPM world-coordinate `y_`/`iy_` fields and emits
   matching DIPY-derived fields, but exact SPM/DARTEL numerical compatibility
   is not guaranteed.

2. Vendor-specific DICOM edge cases may require manual review.

   DICOM conversion is implemented through dicom2nifti, and `nm-dicom inspect`
   / `validate-series` help catch ambiguous input before conversion. Tests now
   cover generic, GE, Philips, Siemens, Hyperfine, and Hitachi series.

3. Tissue segmentation is approximate and not DARTEL-grade.

   Atlas-guided GM/WM/CSF probability estimation is implemented for common T1
   data. SPM25 standalone can be used optionally for SPM segmentation, `y_`/
   `iy_` field generation, DARTEL template estimation, and DARTEL
   Normalise-to-MNI; the Python-native atlas path remains an approximation.

4. FSL BEDPOSTX-based probabilistic tractography is optional.

   DIPY-based tensor fitting, deterministic and probabilistic tensor
   tractography, and seed-target connectivity are implemented. FSL
   BEDPOSTX/PROBTRACKX and MRtrix commands are available as optional wrappers
   when the external binaries are installed.

5. The GUI is optional and not tested in headless CI.

6. Deformation fields use SPM's world-coordinate convention. `y_*.nii` is the
   template-to-native pullback field, `iy_*.nii` is the native-to-template
   forward field, and legacy 1-based voxel fields remain available through
   `coordinate_system="voxel"`.

7. The migration is partial, not a full port of the original MATLAB toolbox.

   Missing workflows now include validated AFQ/ANTs integration and
   DARTEL-grade parity. See `docs/porting-status.md`.

8. The individualized target-mask path is exposed through `nm-tms seed-fc` and
   `nm-pipeline`, and T1-space target generation is now available in `nm-app`;
   the seed-fc target-mask path is still not exposed in the desktop apps.

9. Fixed: `bandpass_filter` now disambiguates orientation from the supplied
   mask length, with an explicit `voxel_major` override.

10. Fixed: `extract_signal` now follows `TMSextract.m` by averaging only
    nonzero masked signal values.

11. Fixed: the end-user app's DICOM folder choice now changes Browse to a
    directory picker.

12. Fixed: `nm-pipeline` and `nm-dicom` now support selecting DICOM series by
    index; the old first-NIfTI behavior remains only when no index is supplied.

13. Fixed: external-execution tests for FSL/MRtrix now pass 3/3 against the
    installed WSL binaries on 2026-08-04. FSL `eddy_correct` and BET pass on a
    realistic ellipsoid fixture, and MRtrix `tckgen` passes with the required
    `-seed_image` source. ANTs execution tests pass 3/3 on Windows.

## Data Issues

1. `ExampleData.zip` contains zero-byte placeholder DICOMs and is not usable.
2. The real development-fMRI NIfTI header reports a fourth-dimension zoom of
   1.0, while Nilearn reports TR=2.0. Tests use the documented TR=2.0.
3. The downloaded public fMRI subject is for validation, not for clinical
   claims.

## Recommended Next Work

- Add validated DARTEL-compatible normalization integration.
- Add an HTML or web report for target coordinates and QC images.
