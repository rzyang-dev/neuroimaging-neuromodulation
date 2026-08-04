"""Quantitative validation helpers."""

from .metrics import compare_volumes, validate_deformation
from .spm import (
    find_spm25,
    run_spm_coreg,
    run_spm_dartel_template,
    run_spm_dartel_mni_norm,
    run_spm_segmentation,
    run_spm_realign,
    validate_coreg_against_spm,
    validate_normalization_against_spm,
    validate_spm_deformation_convention,
    validate_motion_against_spm,
)

__all__ = [
    "compare_volumes",
    "find_spm25",
    "run_spm_coreg",
    "run_spm_dartel_template",
    "run_spm_dartel_mni_norm",
    "run_spm_segmentation",
    "run_spm_realign",
    "validate_coreg_against_spm",
    "validate_deformation",
    "validate_normalization_against_spm",
    "validate_spm_deformation_convention",
    "validate_motion_against_spm",
]
