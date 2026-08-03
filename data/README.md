# Bundled and downloaded data

The package includes a small set of real template and mask NIfTI files copied
from the original MATLAB repository:

- BrainMask, WhiteMask, and CSF masks
- SPM tissue probability templates
- AAL and Yeo atlas files
- HOA exclusion mask

The `real_development_fmri/` directory, when present, contains a real public
fMRI subject downloaded with Nilearn from the OpenNeuro-derived OSF resource.
It is used for development and validation, not as clinical evidence.

The original `ExampleData.zip` in the MATLAB repository contains zero-byte
placeholder DICOM files and is not used by this package.
