# Completion Audit

Status date: 2026-08-04

This document records the migration status requirement by requirement. The
current conclusion is **partial / alpha**: the implemented subset works, but
the full port and production-readiness claims are not met.

## Requirement Evidence

| Requirement | Evidence | Status |
| --- | --- | --- |
| Use venv | `.venv/` exists and editable install uses it | Met |
| Be honest about limitations | `docs/issues.md`, `docs/decisions.md`, `docs/porting-status.md`, and this audit record known gaps | Met |
| Do not use mock data | Real DICOM, fMRI, diffusion, T1, template, and mask data are used | Met |
| Keep comprehensive records | Analysis, design, testing, issues, decisions, and status documents exist | Met |
| Data-oriented mental model | `docs/design.md` and `docs/analysis.md` describe the implemented data flow | Met for implemented subset |
| Use source code and dependencies in workspace | Original MATLAB source is present locally; it is not tracked in Git | Partial |
| Avoid heavyweight external dependencies when possible | Core uses standard Python neuroimaging libraries | Met |
| No MATLAB | Implemented commands are Python-native | Met for implemented subset |
| Limit system resources | Tests use small real datasets | Met |
| Use Nilearn for real data | One real public development-fMRI subject is used | Met |
| Support mainland China network constraints | README and docs include Tsinghua PyPI mirror commands | Met |
| Original algorithm contribution | Seed FC, target-site, depth, white-matter, ALFF/fALFF, GFC classification, and structural connectivity are partially implemented | Partial |
| User-friendly software | CLI and GUI exist, but GUI is alpha and several workflows are not exposed | Partial |
| End-user desktop application | `nm-app` exists; DICOM folder browsing is fixed, but several promised paths are incomplete | Partial |
| Split into multiple programs | Nine entry points are defined in `pyproject.toml` | Met |
| Production package | Wheel builds and tests pass, but package is Alpha, lacks full workflow coverage, and has no reference-parity validation | Not met |

## Verification Evidence

- `158` automated tests are collected and pass locally.
- Wheel build succeeds: `dist/neuroimaging_neuromodulation-0.19.0-py3-none-any.whl`.
- `pip check` reports no broken requirements.
- SPM25 reference validation confirms the package applies SPM `y_`/`iy_`
  world-coordinate fields correctly and reproduces SPM's warped tissue output.
- SPM25 realignment reference validation compares DIPY motion estimates with
  SPM output on real fMRI after sign-convention alignment.
- SPM25 coregistration reference validation compares DIPY rigid coregistration
  with SPM on known real-image shifts.
- SPM25 normalization reference validation compares DIPY deformation fields
  with SPM output on real templates.
- FSL FNIRT normalization execution validation compares FSL and DIPY warped
  images on real templates.
- SPM DARTEL reference comparison compares DARTEL-normalized tissue maps with
  SPM unified-normalization outputs on real data.
- SPM DARTEL multi-subject reference comparison on nine real template-derived
  subjects achieves mean correlation > 0.86.
- CI matrix results are recorded in `docs/ci-validation.md`; no run artifacts
  are present in this workspace.
- Tests are primarily smoke tests. They do not prove numerical equivalence
  with MATLAB, SPM, FSL, or AFQ.

## Remaining Work

The remaining work is listed in `docs/porting-status.md` and `docs/issues.md`.
It includes, but is not limited to:

- Porting missing white-matter/AFQ statistics and TrackQC workflows.
- Integrating the individualized target-mask path into the desktop apps.
- Adding reference comparisons against original MATLAB/SPM/FSL outputs.
- Hardening the GUI, DICOM series selection, and production packaging.
- Re-running the audit only after each missing item has implementation and
  verification evidence.

## Audit Conclusion

The full migration is **not complete**. The implemented Python-native subset is
a useful prototype, but it is not a production-ready replacement for the
original MATLAB toolbox.

## External Runtime Status

MATLAB R2015b, SPM standalone, ANTs 2.6.5 (Windows) and FSL/MRtrix (WSL dev
environment) are installed, so reference/parity execution is possible.
SPM `y_`/`iy_` world-coordinate convention, realignment, coregistration,
normalization, FSL FNIRT, and DARTEL reference comparisons are implemented,
while full numerical parity across a larger clinical multi-subject DARTEL
dataset beyond the nine real template-derived subjects remains to be
demonstrated.
External-execution smoke tests pass
(FSL/MRtrix 3/3 in WSL, ANTs 4/4 on Windows). A 3D rendering runtime for
interactive fiber visualization is still missing. See `docs/porting-status.md`.
