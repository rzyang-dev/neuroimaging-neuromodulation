# Validation Plan for Production Release

Status date: 2026-08-05

This document lists the remaining validation work and the exact commands and
acceptance thresholds needed before a `1.0.0` production sign-off.

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
