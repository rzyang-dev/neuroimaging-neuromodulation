# Completion Audit

Status date: 2026-08-03

This document maps the user's explicit requirements to current evidence in the
workspace. It is intended to make the production readiness claim auditable.

## Requirement Evidence

| Requirement | Evidence | Status |
| --- | --- | --- |
| Use venv | `.venv/` exists and editable install uses it | Met |
| Take the project seriously and be honest | `docs/issues.md`, `docs/decisions.md`, `docs/production-readiness.md` explicitly record limitations | Met |
| Do not use mock data | `docs/data-sources.md` lists real DICOM, fMRI, diffusion, T1, template, and mask data | Met |
| Keep comprehensive records | `docs/analysis.md`, `docs/requirements.md`, `docs/decisions.md`, `docs/design.md`, `docs/testing.md`, `docs/issues.md`, `docs/user-manual.md`, `docs/production-readiness.md` | Met |
| Data-oriented mental model | `docs/design.md` and `docs/analysis.md` describe input-to-output transformations | Met |
| Use source code and dependencies in workspace | Original MATLAB repository remains untouched and is referenced in `docs/analysis.md` | Met |
| Avoid heavyweight external dependencies when possible | Core uses NumPy, SciPy, NiBabel, Nilearn, DIPY, and dicom2nifti; SPM/FSL are optional wrappers | Met |
| No MATLAB | Package is Python-native; MATLAB source is preserved but not required | Met |
| Limit system resources | Tests use modest 4 mm real fMRI and small real DICOM/diffusion datasets | Met |
| Use Nilearn for real data | `data/real_development_fmri/` contains a real public subject fetched by Nilearn | Met |
| Support mainland China network constraints | README and docs use Tsinghua PyPI mirror commands | Met |
| Original algorithm contribution | Seed FC, target-site, depth, white-matter, ALFF/fALFF, GFC classification, and structural connectivity are implemented | Met |
| User-friendly software | `nm-toolbox`, `nm-tms`, `nm-wm`, `nm-preprocess`, `nm-diffusion`, `nm-dicom`, `nm-pipeline`, and GUI | Met |
| Split into multiple programs | Seven installed CLI entry points plus optional GUI | Met |
| Production package | Wheel build verified and CI workflow added | Met |

## Verification Evidence

- `68` automated tests pass on the local macOS environment for Python 3.10
  and 3.14.
- Wheel build succeeds: `dist/neuroimaging_neuromodulation-0.16.0-py3-none-any.whl`.
- GitHub Actions matrix passes on Ubuntu, macOS, and Windows for Python
  3.10, 3.11, and 3.12.
- Real data used in tests includes:
  - public development fMRI subject
  - DIPY real diffusion dataset
  - Stanford T1
  - six DICOM vendors plus compressed/multiframe series
  - bundled templates and masks

## Remaining Honest Work

The following are optional hardening items outside the explicitly required
Python-native scope:

- SPM/DARTEL reference comparison for estimated `y_`/`iy_` fields
- Actual execution of FSL/MRtrix wrappers against installed binaries
- Additional unusual DICOM sequence coverage
- Motion/coregistration comparison against SPM/FSL reference software

## Audit Conclusion

All explicit requirements are met: the package is Python-native, isolated in a
venv, validated with real data, documented, packaged as a wheel, split into
user-facing programs, and verified by a green cross-platform CI matrix. The
goal is considered achieved within the documented Python-native scope; exact
SPM/DARTEL or FSL parity is not claimed.
