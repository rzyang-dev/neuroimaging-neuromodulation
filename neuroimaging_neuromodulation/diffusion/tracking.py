"""Deterministic tensor tractography."""

from __future__ import annotations

from pathlib import Path

import nibabel as nib
import numpy as np


def _reference_image(mask: np.ndarray, affine: np.ndarray) -> nib.Nifti1Image:
    return nib.Nifti1Image(mask.astype(np.float32), affine)


def track_deterministic(
    data: np.ndarray,
    gtab: object,
    affine: np.ndarray,
    *,
    seed_mask: np.ndarray,
    stop_map: np.ndarray,
    fa_threshold: float = 0.2,
    step_size: float = 0.5,
    min_length: float = 10.0,
    max_length: float = 500.0,
    max_angle: float = 30.0,
    seed_density: int = 1,
    out_trk: str | Path | None = None,
) -> list[np.ndarray]:
    """Run deterministic tractography from a seed mask using tensor peaks."""

    try:
        from dipy.direction import peaks_from_model
        from dipy.io.stateful_tractogram import Space, StatefulTractogram
        from dipy.io.streamline import save_tractogram
        from dipy.reconst.dti import TensorModel
        from dipy.tracking import utils
        from dipy.tracking.stopping_criterion import ThresholdStoppingCriterion
        from dipy.tracking.tracker import deterministic_tracking
        from dipy.data import get_sphere
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("DIPY is required for tractography.") from exc

    seed_mask = np.asarray(seed_mask, dtype=bool)
    stop_map = np.asarray(stop_map, dtype=float)
    model = TensorModel(gtab, fit_method="WLS")
    sphere = get_sphere(name="symmetric724")
    peaks = peaks_from_model(
        model,
        data,
        sphere,
        0.5,
        25,
        mask=stop_map > 0,
        return_sh=True,
        normalize_peaks=False,
        legacy=False,
    )
    stopping_criterion = ThresholdStoppingCriterion(stop_map, fa_threshold)
    seeds = utils.seeds_from_mask(
        seed_mask,
        affine,
        density=[seed_density, seed_density, seed_density],
    )
    streamlines = list(
        deterministic_tracking(
            seeds,
            stopping_criterion,
            affine,
            sh=peaks.shm_coeff,
            sphere=sphere,
            step_size=step_size,
            min_len=min_length,
            max_len=max_length,
            max_angle=max_angle,
            nbr_threads=0,
            legacy=False,
        )
    )
    if out_trk is not None:
        reference = _reference_image(seed_mask, affine)
        sft = StatefulTractogram(streamlines, reference, Space.RASMM)
        save_tractogram(sft, str(out_trk), bbox_valid_check=False)
    return streamlines


def track_probabilistic(
    data: np.ndarray,
    gtab: object,
    affine: np.ndarray,
    *,
    seed_mask: np.ndarray,
    stop_map: np.ndarray,
    fa_threshold: float = 0.2,
    step_size: float = 0.5,
    min_length: float = 10.0,
    max_length: float = 500.0,
    max_angle: float = 20.0,
    seed_density: int = 1,
    random_seed: int = 1,
    out_trk: str | Path | None = None,
) -> list[np.ndarray]:
    """Run probabilistic tractography using DIPY's probabilistic tracker."""

    try:
        from dipy.data import get_sphere
        from dipy.direction import peaks_from_model
        from dipy.io.stateful_tractogram import Space, StatefulTractogram
        from dipy.io.streamline import save_tractogram
        from dipy.reconst.dti import TensorModel
        from dipy.tracking import utils
        from dipy.tracking.stopping_criterion import ThresholdStoppingCriterion
        from dipy.tracking.tracker import probabilistic_tracking
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("DIPY is required for probabilistic tractography.") from exc

    seed_mask = np.asarray(seed_mask, dtype=bool)
    stop_map = np.asarray(stop_map, dtype=float)
    model = TensorModel(gtab, fit_method="WLS")
    sphere = get_sphere(name="symmetric724")
    peaks = peaks_from_model(
        model,
        data,
        sphere,
        0.5,
        25,
        mask=stop_map > 0,
        return_sh=True,
        normalize_peaks=False,
        legacy=False,
    )
    stopping_criterion = ThresholdStoppingCriterion(stop_map, fa_threshold)
    seeds = utils.seeds_from_mask(
        seed_mask,
        affine,
        density=[seed_density, seed_density, seed_density],
    )
    streamlines = list(
        probabilistic_tracking(
            seeds,
            stopping_criterion,
            affine,
            sh=peaks.shm_coeff,
            sphere=sphere,
            step_size=step_size,
            min_len=min_length,
            max_len=max_length,
            max_angle=max_angle,
            nbr_threads=0,
            random_seed=random_seed,
            legacy=False,
        )
    )
    if out_trk is not None:
        reference = _reference_image(seed_mask, affine)
        sft = StatefulTractogram(streamlines, reference, Space.RASMM)
        save_tractogram(sft, str(out_trk), bbox_valid_check=False)
    return streamlines


__all__ = ["track_deterministic", "track_probabilistic"]
