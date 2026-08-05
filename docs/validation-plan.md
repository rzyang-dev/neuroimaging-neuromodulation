# Validation Plan for Production Release

Status date: 2026-08-05

This document lists the remaining validation work and the exact commands and
acceptance thresholds needed before a `1.0.0` production sign-off.

## Current External Blocker

The installer workflow was triggered from CI on 2026-08-05, but GitHub
Actions could not start the jobs because the account has a billing or spending
limit block. No installer artifacts were produced. Resume this section after
GitHub Actions billing is restored.

## 1. Clinical-Scale Deformation Validation

Run the internal engine and, when DIPY is installed, the optional DIPY engine
on real multi-subject data:

```bash
nm-preprocess compare-deformation-engines \
  --moving <native-t1.nii> \
  --static <mni-template.nii> \
  --output-dir <output>/deformation \
  --output-json <output>/deformation-compare.json
```

Acceptance:

- Internal warped output is finite for all subjects.
- Internal warped output agrees with DIPY at mean correlation > 0.85 on the
  same subjects.
- `y_`/`iy_` fields are finite and can be applied without errors.
- At least one clinical or public multi-subject T1 dataset is recorded in
  `docs/data-sources.md`.

## 2. AFQ/TrackQC Reference Parity

Record reference AFQ JSON outputs and compare them to the Python output:

```bash
nm-wm afq-validate \
  --reference <reference-afq.json> \
  --candidate <python-afq.json> \
  --output-json <output>/afq-compare.json
```

Acceptance:

- All reference tract labels are matched.
- Mean profile correlation > 0.9 on reference datasets.
- Mean profile MAE is recorded in the comparison JSON.
- TrackQC reports do not contain unexpected QC warnings on valid reference
  data.

## 3. Installer Validation

Trigger `.github/workflows/installers.yml` from the GitHub Actions UI or by
creating a release tag after release gates pass.

2026-08-05 result: workflow run `30981200366` failed before starting jobs due
to the GitHub billing/spending-limit block described above.

Acceptance:

- `nm-toolbox doctor --json` succeeds from the packaged CLI on Windows, macOS,
  and Linux.
- `nm-app` and `nm-gui` launch on a machine with a desktop display.
- Installer artifacts include package data and report a package version
  matching `pyproject.toml`.

## 4. Final Release Gates

Run:

```bash
python scripts/check_release_gates.py
python -m pytest
python -m pip check
python -m build --wheel
```

Acceptance:

- All commands return zero.
- Minimal-core install works without optional dependencies.
- Gap matrix, roadmap, status docs, and changelog are current.
- No stale `ported` claims remain.
- Release artifacts contain the wheel, checksums, and executable installers.

## 5. Completion Rule

Do not tag `1.0.0` until the validation above is recorded in this repository
and all acceptance thresholds pass. Until then, the package remains in active
development.

## Local Results

Local-only validation completed on 2026-08-05 without GitHub Actions:

- Full local test suite passes (`190` tests).
- Release gates pass.
- Wheel builds locally under `release/wheels/`.
- Packaged `nm-toolbox` CLI runs `doctor --json` from
  `release/binaries/nm-toolbox/`.
- `nm-app` and `nm-gui` bundles built locally under
  `release/binaries/`.
- Local launch check: both `nm-app.exe` and `nm-gui.exe` started and remained
  running for 3 seconds before being closed.
- Validation JSON records are copied to `release/validation/`.
- Previous release output is archived under `release/archive/`, not deleted.
- Reproducible build command:
  `python scripts/build_local.py --build-gui --run-tests`
