# End-User App

`nm-app` is the guided desktop application for end users. It wraps the Python
package behind a simple workflow:

1. Enter a subject ID.
2. Choose functional data as a NIfTI file or DICOM folder.
3. Choose a seed image and analysis mask.
4. Optionally choose a T1 image.
5. Review settings such as TR and frequency band.
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

## What It Does

The app builds a pipeline config and runs:

- DICOM conversion when a DICOM folder is selected
- motion estimation, when enabled
- seed-based FC
- TMS target candidates, when enabled
- HTML report and SHA-256 manifest

Errors are shown in plain language instead of requiring users to inspect logs.
