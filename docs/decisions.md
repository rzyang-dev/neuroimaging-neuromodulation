# Decision Record

The following decisions update and, where needed, supersede earlier ADRs.

## ADR-011: Minimal core dependency budget

Decision: The normal analysis path must run with only NumPy, SciPy, and NiBabel.
Nilearn, DIPY, pydicom, and dicom2nifti are optional extras.

Why: The product is aimed at broad users, not only researchers with prebuilt
academic environments. A small core install must work predictably.

Consequence: Optional libraries are lazily imported and never required by
`nm-toolbox`, `nm-tms`, `nm-wm`, or `nm-preprocess` core paths.

## ADR-012: External academic runtimes are optional providers only

Decision: MATLAB, SPM, FSL, DARTEL, ANTs, and SimNIBS are never required for
normal use. They may be discovered through explicit runtime providers and may
be bundled into installers only after license review.

Why: The product must not depend on machine-specific academic software or
implicitly assume a researcher workstation.

Consequence: Core code never imports these runtimes. Optional provider checks
are reported by `nm-toolbox doctor` and isolated behind a provider boundary.

## ADR-013: Python-native algorithm implementation is the default

Decision: The project reimplements the toolbox’s algorithmic contributions in
Python rather than wrapping SPM/FSL workflows as the product path.

Why: Academic toolchains are not a reliable runtime for general users, and
their internal behavior should not be treated as unchangeable product code.

Consequence: External binaries are used only for optional validation or
advanced provider features, and every such use is documented as optional.

## ADR-001: Use a separate Python package instead of modifying MATLAB files

Decision: Create `neuroimaging_neuromodulation/` as a new Python package and
leave the original MATLAB source untouched.

Why: The original files are a research artifact. Rewriting them in place would
destroy provenance and make comparison against the academic code difficult.

Consequence: The package is self-contained but references the original mapping
in `docs/analysis.md`.

## ADR-002: Use NumPy, SciPy, NiBabel, and Nilearn

Status: superseded by ADR-011 for the core dependency budget.

Decision: Use these four scientific Python libraries.

Why: They are standard, reasonably lightweight, available on PyPI mirrors, and
provide NIfTI I/O, resampling, FFT, regression, morphology, and real-data
download support without MATLAB/SPM/FSL.

Consequence: The package cannot reproduce every SPM operation, but the core
algorithm layer is fully Python-native.

## ADR-003: Keep preprocessing dependencies out of the core

Status: superseded by ADR-013; external academic runtimes are optional
providers rather than product dependencies.

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

Status: superseded by ADR-011; DIPY is an optional diffusion extra until the
needed algorithm is replaced internally.

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

Status: superseded by ADR-011 and ADR-013; the default is the NumPy/SciPy dense
deformation engine, with DIPY available as an optional compatibility engine.

Decision: Add DIPY-based nonlinear registration and a coordinate-field
converter.

Why: It closes the native-to-MNI workflow without installing SPM or ANTs.

Consequence: Users get reproducible mapping and warped outputs in SPM
world-coordinate `y_`/`iy_` form. The convention is validated against SPM25,
but users must not assume exact SPM/DARTEL numerical equivalence.
