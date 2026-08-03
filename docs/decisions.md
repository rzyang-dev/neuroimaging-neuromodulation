# Decision Record

## ADR-001: Use a separate Python package instead of modifying MATLAB files

Decision: Create `neuroimaging_neuromodulation/` as a new Python package and
leave the original MATLAB source untouched.

Why: The original files are a research artifact. Rewriting them in place would
destroy provenance and make comparison against the academic code difficult.

Consequence: The package is self-contained but references the original mapping
in `docs/analysis.md`.

## ADR-002: Use NumPy, SciPy, NiBabel, and Nilearn

Decision: Use these four scientific Python libraries.

Why: They are standard, reasonably lightweight, available on PyPI mirrors, and
provide NIfTI I/O, resampling, FFT, regression, morphology, and real-data
download support without MATLAB/SPM/FSL.

Consequence: The package cannot reproduce every SPM operation, but the core
algorithm layer is fully Python-native.

## ADR-003: Keep preprocessing dependencies out of the core

Decision: Do not reimplement SPM segmentation, DARTEL normalization, FSL eddy,
or tractography in this release.

Why: These are research-grade image-processing systems. A partial reimplementation
would be less reliable and more dangerous for clinical decision support.

Consequence: The current user contract is "preprocessed NIfTI in, analysis
maps out." This is documented in the README and user manual.

## ADR-004: Validate with real public data

Decision: Download one real adult subject from the Nilearn development-fMRI
dataset for smoke and integration tests, and use real bundled templates/masks
for geometry tests.

Why: The user explicitly forbade mock data. Real data exposes actual grid,
orientation, and numerical edge cases.

Consequence: Tests skip functional-data cases if the real download is absent,
but the local environment has the data downloaded.

## ADR-005: Use 1-based matrix coordinates internally where the MATLAB code uses them

Decision: Preserve the original toolbox convention that sphere and target
functions use 1-based matrix indices and direct affine multiplication.

Why: `TMSsphereROI` and `TMSmat2mni` depend on that convention. Changing to
0-based silently would produce target locations different from the original.

Consequence: Coordinate helpers are explicit and documented in
`coordinates.py`.

## ADR-006: Use `depth_mm=None` as the safe default for individualized masks

Decision: The new `individual_target_mask` keeps all target voxels unless the
user supplies a depth threshold.

Why: The original default `targetdepth=0` has behavior that could erase the
mask under a literal reading of the MATLAB loop. A production API should not
silently discard the target.

Consequence: Users who need the original distance-threshold behavior must pass
an explicit depth.

## ADR-007: Use DIPY for rigid motion estimation

Decision: Add DIPY as a dependency for motion-parameter estimation.

Why: DIPY is a Python-native neuroimaging library with a well-tested affine
registration API. It avoids MATLAB, SPM, and FSL while staying lighter than a
full preprocessing system.

Consequence: Motion estimation requires DIPY, but the rest of the package
continues to work with NumPy, SciPy, NiBabel, and Nilearn. The extracted
parameters are written in SPM-style text format.

## ADR-008: Use dicom2nifti for DICOM conversion

Decision: Add `dicom2nifti` and `pydicom` as dependencies.

Why: This keeps DICOM conversion inside the virtual environment instead of
requiring a system-wide binary install.

Consequence: `nm-dicom` handles common vendor series without SPM/FSL, but
unusual scanner edge cases should still be visually inspected.

## ADR-009: Provide approximate tissue segmentation instead of pretending SPM parity

Decision: Implement atlas-guided tissue probability estimation as a utility,
and keep the documentation clear that it is not a DARTEL replacement.

Why: Users need c1/c2/c3-like maps for mask construction and target depth, but
claiming SPM/DARTEL equivalence would be unsafe.

Consequence: The package is more useful end to end while preserving honesty
about its accuracy boundary.

## ADR-010: Use DIPY for nonlinear deformation estimation

Decision: Add DIPY-based nonlinear registration and a coordinate-field
converter.

Why: It closes the native-to-MNI workflow without installing SPM or ANTs.

Consequence: Users get reproducible mapping and warped outputs, but must not
assume exact SPM/DARTEL deformation conventions.
