# Source Repository Note

The original MATLAB toolbox, SPM, FSL-related vendor folders, and large
third-party dependency directories exist in the local workspace for reference
and comparison.

The published Python repository intentionally excludes those directories:

- `Neuroimaging-and-Neuromodulation/`
- `spm/`
- `AFQ/`
- `vistasoft/`

This keeps the production package small and prevents accidental redistribution
of third-party MATLAB/SPM/FSL code. The Python implementation is self-contained;
the algorithm mapping is documented in `docs/analysis.md`.
