"""Neuroimaging and Neuromodulation Python toolbox."""

from .io.deformations import apply_deformation
from .io.nifti import load_volume, save_volume
from .preprocess.temporal import apply_motion_parameters, slice_timing_correct_volume
from .stats.functional import fast_corr, inverse_pearson
from .targets.pipeline import seed_based_fc, target_site
from .wm.alff import compute_alff

__all__ = [
    "apply_deformation",
    "apply_motion_parameters",
    "compute_alff",
    "fast_corr",
    "inverse_pearson",
    "load_volume",
    "save_volume",
    "seed_based_fc",
    "slice_timing_correct_volume",
    "target_site",
]

__version__ = "0.17.0"
