# End-User App

`nm-app` is the guided desktop application for end users. It wraps the Python
package behind a simple workflow:

**Status: alpha.** The app is not yet a production end-user tool. Known
limitations are recorded in `docs/issues.md`.

1. Enter a subject ID.
2. Choose functional data as a NIfTI file or DICOM folder.
3. Choose a seed image and analysis mask.
4. Optionally choose a T1 image and an MNI target ROI image.
5. Review settings such as TR, frequency band, and T1-space target generation.
6. Press Run Analysis.
7. Open the generated HTML report or output folder.

No command-line knowledge is required.

## Launch

```bash
.venv/bin/nm-app
```

Or:

```bash
.venv/bin/nm-toolbox gui
```

Developers and advanced users can open the more detailed tabbed interface with:

```bash
.venv/bin/nm-gui
```

## What It Does

The app builds a pipeline config and runs:

- DICOM conversion when a DICOM folder is selected
- motion estimation, when enabled
- seed-based FC
- TMS target candidates, when enabled
- T1-space target image generation, when enabled with a T1 and target ROI
- HTML report and SHA-256 manifest

Errors are shown in plain language instead of requiring users to inspect logs.
