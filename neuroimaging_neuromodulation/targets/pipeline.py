"""End-to-end seed FC and target-site pipeline functions."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import nibabel as nib
import numpy as np

from ..coordinates import mat_to_mni
from ..io.deformations import apply_deformation
from ..io.nifti import load_4d_matrix, load_volume, resample_to_grid, save_volume
from ..stats.functional import fast_corr
from ..stats.functional import bandpass_filter
from .cluster import largest_cluster, label_centers_mni
from .roi import individual_target_mask, sphere_roi


def _binarize(data: np.ndarray) -> np.ndarray:
    return np.asarray(data > 0, dtype=bool).reshape(-1)


def seed_based_fc(
    functional_image: str | Path,
    seed_image: str | Path,
    mask_image: str | Path,
    output_dir: str | Path,
    *,
    subject: str = "subject",
    z_score: bool = False,
    tr: float | None = None,
    band: tuple[float, float] | None = None,
    filter_data: bool = False,
    target_mask_image: str | Path | None = None,
    c6_image: str | Path | None = None,
    c1_image: str | Path | None = None,
    depth_mm: float | None = None,
    extend_iterations: int = 15,
    seed_deformation: str | Path | None = None,
    mask_deformation: str | Path | None = None,
) -> dict[str, object]:
    """Compute seed-based functional connectivity and write FC maps.

    The seed and mask are resampled to the functional grid. The FC map follows
    the original ``TMSSeedFC`` convention (Pearson r, no Fisher z by default).
    """

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    func_img, func_matrix = load_4d_matrix(functional_image)
    if func_matrix.shape[1] < 3:
        raise ValueError("Functional data must contain at least three timepoints")

    seed_for_resample = seed_image
    if seed_deformation is not None:
        seed_for_resample, _ = apply_deformation(seed_image, seed_deformation, order=0)
    mask_for_resample = mask_image
    if mask_deformation is not None:
        mask_for_resample, _ = apply_deformation(mask_image, mask_deformation, order=0)
    seed_img, seed_data = resample_to_grid(seed_for_resample, func_img, order=0)
    mask_img, mask_data = resample_to_grid(mask_for_resample, func_img, order=0)
    seed_mask = _binarize(seed_data)
    analysis_mask = _binarize(mask_data)
    if seed_mask.size != func_matrix.shape[0] or analysis_mask.size != func_matrix.shape[0]:
        raise ValueError("Resampled seed/mask shape does not match functional matrix")
    if not seed_mask.any():
        raise ValueError("Seed mask is empty after resampling")
    if not analysis_mask.any():
        raise ValueError("Analysis mask is empty after resampling")
    roi_mask = analysis_mask.copy()
    target_mask_path = None
    if target_mask_image is not None:
        if c6_image is None:
            raise ValueError("c6_image is required when target_mask_image is provided")
        c6_img, target_mask = individual_target_mask(
            target_mask_image,
            c6_image,
            c1_image,
            output_dir / subject / "IndiTargetMask_c6.nii",
            depth_mm=depth_mm,
            extend_iterations=extend_iterations,
        )
        target_mask_path = output_dir / subject / "IndiTargetMask_c6.nii"
        _, target_in_func = resample_to_grid(
            nib.Nifti1Image(target_mask.astype(np.float32), c6_img.affine),
            func_img,
            order=0,
        )
        roi_mask = analysis_mask & _binarize(target_in_func)
        if not roi_mask.any():
            raise ValueError("Individual target mask has no overlap with the analysis mask")

    if filter_data:
        if tr is None or band is None:
            raise ValueError("TR and band must be provided when filter_data=True")
        func_matrix = bandpass_filter(func_matrix, tr, band, mask=analysis_mask)

    seed_signal = np.mean(func_matrix[seed_mask, :], axis=0)[:, None]
    r_values = fast_corr(seed_signal, func_matrix[analysis_mask, :].T).ravel()
    roi_r_values = r_values[roi_mask[analysis_mask]]
    if z_score:
        r_values = np.arctanh(np.clip(r_values, -1 + 1e-12, 1 - 1e-12))

    wb_map = np.zeros(func_matrix.shape[0], dtype=np.float32)
    wb_map[analysis_mask] = r_values
    roi_map = np.zeros(func_matrix.shape[0], dtype=np.float32)
    roi_map[roi_mask] = roi_r_values
    shape = func_img.shape[:3]
    wb_path = save_volume(wb_map.reshape(shape), func_img, output_dir / subject / "SeedFCinWB.nii")
    roi_path = save_volume(roi_map.reshape(shape), func_img, output_dir / subject / "SeedFCinROI.nii")
    return {
        "seed_signal": seed_signal.ravel(),
        "r_values": r_values,
        "SeedFCinWB": wb_path,
        "SeedFCinROI": roi_path,
        "IndiTargetMask": target_mask_path,
    }


def _write_coordinate(
    coordinate: np.ndarray,
    output_dir: Path,
    subject: str,
    name: str,
) -> Path:
    path = output_dir / subject / f"MNICoordinate_{name}.txt"
    np.savetxt(path, coordinate, fmt="%.6f")
    return path


def _target_site_from_extremum(
    fc_img: nib.Nifti1Image,
    fc_data: np.ndarray,
    output_dir: Path,
    subject: str,
    direction: str,
    *,
    p_value: float,
    n_samples: int,
    native_deformation: str | Path | None = None,
) -> dict[str, object]:
    positive = direction.lower().startswith("pos")
    if positive:
        idx = int(np.argmax(fc_data))
    else:
        idx = int(np.argmin(fc_data))
    mat = np.unravel_index(idx, fc_data.shape)
    mat_1based = np.array(mat) + 1.0
    mni = mat_to_mni(mat_1based, fc_img.affine)
    prefix = "PosiPt" if positive else "NegaPt"
    sphere_img, _ = sphere_roi(
        mni,
        5.0,
        fc_img,
        output_dir / subject / f"StiTarget{prefix}_MNI.nii",
    )
    native_path = None
    if native_deformation is not None:
        native_path = output_dir / subject / f"StiTarget{prefix}_T1Sp.nii"
        apply_deformation(
            output_dir / subject / f"StiTarget{prefix}_MNI.nii",
            native_deformation,
            native_path,
            order=0,
        )
    coord_path = _write_coordinate(np.hstack([mni, float(fc_data[tuple(mat)])]), output_dir, subject, prefix)

    cluster, size = largest_cluster(fc_data, p_value, n_samples, direction)
    cluster_result: dict[str, object] = {}
    if size:
        cluster_path = output_dir / subject / f"FCinROI{direction[:4]}LCt.nii"
        save_volume(cluster.astype(np.float32), fc_img, cluster_path)
        centers = label_centers_mni(cluster.astype(np.uint8), fc_img.affine)
        if centers:
            center_mni = centers[0]["mni"]
            center_path = _write_coordinate(center_mni, output_dir, subject, f"{direction[:4]}LCt")
            sphere_roi(
                center_mni,
                8.0,
                fc_img,
                output_dir / subject / f"StiTarget{direction[:4]}LCt_MNI.nii",
            )
            if native_deformation is not None:
                apply_deformation(
                    output_dir / subject / f"StiTarget{direction[:4]}LCt_MNI.nii",
                    native_deformation,
                    output_dir / subject / f"StiTarget{direction[:4]}LCt_T1Sp.nii",
                    order=0,
                )
            cluster_result = {"center_mni": center_mni, "center_path": center_path}
    return {
        "direction": direction,
        "extremum_mni": mni,
        "extremum_value": float(fc_data[tuple(mat)]),
        "extremum_coordinate_path": coord_path,
        "native_target_path": str(native_path) if native_path is not None else None,
        "largest_cluster_size": size,
        **cluster_result,
    }


def target_site(
    fc_image: str | Path,
    output_dir: str | Path,
    *,
    subject: str = "subject",
    posneg: Iterable[str] = ("Positive", "Negative"),
    p_value: float = 0.05,
    n_samples: int = 212,
    native_deformation: str | Path | None = None,
) -> list[dict[str, object]]:
    """Generate target candidates from an FC map."""

    fc_img, fc_data = load_volume(fc_image)
    fc_data = np.asarray(fc_data, dtype=float)
    if fc_data.ndim != 3:
        raise ValueError("target_site expects a 3D FC map")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for direction in posneg:
        results.append(
            _target_site_from_extremum(
                fc_img,
                fc_data,
                output_dir,
                subject,
                direction,
                p_value=p_value,
                n_samples=n_samples,
                native_deformation=native_deformation,
            )
        )
    return results


__all__ = ["seed_based_fc", "target_site"]
