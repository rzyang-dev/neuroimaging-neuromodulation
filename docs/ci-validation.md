# CI Validation

This branch exists to trigger the GitHub Actions matrix on Ubuntu, macOS, and
Windows for Python 3.10, 3.11, and 3.12.

The workflow is defined in `.github/workflows/ci.yml`. It installs the package
with test dependencies and runs:

```bash
python -m pytest
```

CI results should be reported after the pull request run completes.

Observed final status:

- Ubuntu 3.10, 3.11, 3.12: pass
- macOS 3.10, 3.11, 3.12: pass
- Windows 3.10, 3.11, 3.12: pass

All nine CI matrix jobs pass.

## Verification Caveat

This page records the observed status at the time of writing. The repository
does not contain CI run artifacts or a workflow badge, so the result cannot be
independently reproduced from files in this workspace. Local verification is
documented separately in `docs/testing.md`.
