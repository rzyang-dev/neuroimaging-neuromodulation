# CI Validation

This branch exists to trigger the GitHub Actions matrix on Ubuntu, macOS, and
Windows for Python 3.10, 3.11, and 3.12.

The workflow is defined in `.github/workflows/ci.yml`. It installs the package
with test, diffusion, DICOM, and demo dependencies and runs:

```bash
python -m pytest
```

CI results should be reported after the pull request run completes.

Observed final status:

- Ubuntu 3.10, 3.11, 3.12: pass
- macOS 3.10, 3.11, 3.12: pass
- Windows 3.10, 3.11, 3.12: pass

All CI matrix jobs pass in the recorded run. The matrix now includes Python
3.10-3.14 on Ubuntu, macOS, and Windows. Optional external-runtime tests are
skipped by default and can be enabled with `NM_RUN_EXTERNAL=1`.

`ci.yml` also includes a minimal-core job that installs the package without
optional extras and verifies core motion, coregistration, DTI, tractography,
and runtime diagnostics. Tagged releases are handled by
`.github/workflows/release.yml`, which builds and uploads the wheel.
`.github/workflows/installers.yml` builds standalone PyInstaller executables
for the desktop apps and CLI on Ubuntu, macOS, and Windows. Tagged releases
call that workflow and attach both the wheel and executables to the GitHub
release.

## Verification Caveat

This page records the observed status at the time of writing. The repository
does not contain CI run artifacts or a workflow badge, so the result cannot be
independently reproduced from files in this workspace. Local verification is
documented separately in `docs/testing.md`.
