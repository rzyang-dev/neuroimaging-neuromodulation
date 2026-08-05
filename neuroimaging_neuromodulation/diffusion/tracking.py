"""Deterministic tensor tractography."""

from __future__ import annotations

from pathlib import Path

import nibabel as nib
import numpy as np

from .dti import fit_tensor


def _reference_image(mask: np.ndarray, affine: np.ndarray) -> nib.Nifti1Image:
    return nib.Nifti1Image(mask.astype(np.float32), affine)


def _world_to_voxel(points: np.ndarray, affine: np.ndarray) -> np.ndarray:
    homogeneous = np.column_stack([points, np.ones(len(points), dtype=float)])
    return (np.linalg.inv(affine) @ homogeneous.T).T[:, :3]


def _voxel_to_world(points: np.ndarray, affine: np.ndarray) -> np.ndarray:
    homogeneous = np.column_stack([points, np.ones(len(points), dtype=float)])
    return (affine @ homogeneous.T).T[:, :3]


def _seed_points(
    seed_mask: np.ndarray,
    affine: np.ndarray,
    density: int,
) -> list[np.ndarray]:
    points: list[np.ndarray] = []
    seed_mask = np.asarray(seed_mask, dtype=bool)
    offsets = [(index + 0.5) / density - 0.5 for index in range(density)]
    for x, y, z in np.argwhere(seed_mask):
        for dx in offsets:
            for dy in offsets:
                for dz in offsets:
                    points.append(np.array([x + dx, y + dy, z + dz], dtype=float))
    return points


def _tensor_at(tensors: np.ndarray, voxel: np.ndarray) -> np.ndarray | None:
    index = np.rint(voxel).astype(int)
    if np.any(index < 0) or np.any(index >= np.asarray(tensors.shape[:3])):
        return None
    tensor = tensors[index[0], index[1], index[2]]
    if not np.isfinite(tensor).all():
        return None
    return tensor


def _fa_at(fa: np.ndarray, voxel: np.ndarray) -> float:
    index = np.rint(voxel).astype(int)
    if np.any(index < 0) or np.any(index >= np.asarray(fa.shape)):
        return 0.0
    return float(fa[index[0], index[1], index[2]])


def _principal_direction(tensor: np.ndarray) -> np.ndarray:
    _values, vectors = np.linalg.eigh(tensor)
    return vectors[:, 2]


def _follow(
    start: np.ndarray,
    direction: np.ndarray,
    tensors: np.ndarray,
    fa: np.ndarray,
    *,
    step_size: float,
    fa_threshold: float,
    max_length: float,
    max_angle: float,
) -> list[np.ndarray]:
    points = [start]
    current = start.copy()
    previous_direction = direction.copy()
    max_angle = np.deg2rad(max_angle)
    while len(points) * step_size <= max_length:
        candidate = current + previous_direction * step_size
        if _fa_at(fa, candidate) < fa_threshold:
            break
        tensor = _tensor_at(tensors, candidate)
        if tensor is None:
            break
        new_direction = _principal_direction(tensor)
        if np.dot(previous_direction, new_direction) < 0:
            new_direction = -new_direction
        cosine = np.clip(np.dot(previous_direction, new_direction), -1.0, 1.0)
        if np.arccos(cosine) > max_angle:
            break
        points.append(candidate)
        previous_direction = new_direction
        current = candidate
    return points


def _track_one(
    start: np.ndarray,
    tensors: np.ndarray,
    fa: np.ndarray,
    affine: np.ndarray,
    *,
    step_size: float,
    fa_threshold: float,
    min_length: float,
    max_length: float,
    max_angle: float,
) -> np.ndarray | None:
    tensor = _tensor_at(tensors, start)
    if tensor is None or _fa_at(fa, start) < fa_threshold:
        return None
    direction = _principal_direction(tensor)
    forward = _follow(
        start,
        direction,
        tensors,
        fa,
        step_size=step_size,
        fa_threshold=fa_threshold,
        max_length=max_length,
        max_angle=max_angle,
    )
    backward = _follow(
        start,
        -direction,
        tensors,
        fa,
        step_size=step_size,
        fa_threshold=fa_threshold,
        max_length=max_length,
        max_angle=max_angle,
    )
    voxel_streamline = np.asarray(backward[::-1] + forward[1:], dtype=float)
    if len(voxel_streamline) < 2:
        return None
    world = _voxel_to_world(voxel_streamline, affine)
    length = float(np.sum(np.linalg.norm(np.diff(world, axis=0), axis=1)))
    if length < min_length:
        return None
    return world


def _follow_probabilistic(
    start: np.ndarray,
    direction: np.ndarray,
    tensors: np.ndarray,
    fa: np.ndarray,
    rng: np.random.Generator,
    *,
    step_size: float,
    fa_threshold: float,
    max_length: float,
    max_angle: float,
    noise_scale: float = 0.3,
) -> list[np.ndarray]:
    points = [start]
    current = start.copy()
    previous_direction = direction.copy()
    max_angle = np.deg2rad(max_angle)
    while len(points) * step_size <= max_length:
        candidate = current + previous_direction * step_size
        if _fa_at(fa, candidate) < fa_threshold:
            break
        tensor = _tensor_at(tensors, candidate)
        if tensor is None:
            break
        principal = _principal_direction(tensor)
        if np.dot(previous_direction, principal) < 0:
            principal = -principal
        auxiliary = np.array([1.0, 0.0, 0.0], dtype=float)
        if abs(np.dot(principal, auxiliary)) > 0.9:
            auxiliary = np.array([0.0, 1.0, 0.0], dtype=float)
        basis_a = auxiliary - np.dot(auxiliary, principal) * principal
        basis_a /= np.linalg.norm(basis_a)
        basis_b = np.cross(principal, basis_a)
        perturbation = (
            basis_a * rng.normal(scale=noise_scale)
            + basis_b * rng.normal(scale=noise_scale)
        )
        new_direction = principal + perturbation
        norm = np.linalg.norm(new_direction)
        if norm < 1e-12:
            break
        new_direction = new_direction / norm
        if np.dot(previous_direction, new_direction) < 0:
            new_direction = -new_direction
        cosine = np.clip(np.dot(previous_direction, new_direction), -1.0, 1.0)
        if np.arccos(cosine) > max_angle:
            break
        points.append(candidate)
        previous_direction = new_direction
        current = candidate
    return points


def _track_probabilistic_one(
    start: np.ndarray,
    tensors: np.ndarray,
    fa: np.ndarray,
    affine: np.ndarray,
    rng: np.random.Generator,
    *,
    step_size: float,
    fa_threshold: float,
    min_length: float,
    max_length: float,
    max_angle: float,
) -> np.ndarray | None:
    tensor = _tensor_at(tensors, start)
    if tensor is None or _fa_at(fa, start) < fa_threshold:
        return None
    direction = _principal_direction(tensor)
    forward = _follow_probabilistic(
        start,
        direction,
        tensors,
        fa,
        rng,
        step_size=step_size,
        fa_threshold=fa_threshold,
        max_length=max_length,
        max_angle=max_angle,
    )
    backward = _follow_probabilistic(
        start,
        -direction,
        tensors,
        fa,
        rng,
        step_size=step_size,
        fa_threshold=fa_threshold,
        max_length=max_length,
        max_angle=max_angle,
    )
    voxel_streamline = np.asarray(backward[::-1] + forward[1:], dtype=float)
    if len(voxel_streamline) < 2:
        return None
    world = _voxel_to_world(voxel_streamline, affine)
    length = float(np.sum(np.linalg.norm(np.diff(world, axis=0), axis=1)))
    if length < min_length:
        return None
    return world


def _save_trk(streamlines: list[np.ndarray], affine: np.ndarray, out_trk: str | Path) -> None:
    from .streamlines_io import save_tract_streamlines

    save_tract_streamlines(streamlines, _reference_image(np.zeros((1, 1, 1), dtype=np.uint8), affine), out_trk)


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
    """Run deterministic tractography from a seed mask with a NumPy/SciPy engine."""

    seed_mask = np.asarray(seed_mask, dtype=bool)
    stop_map = np.asarray(stop_map, dtype=float)
    fit = fit_tensor(data, gtab, mask=stop_map > 0)
    tensors = np.asarray(fit.tensors, dtype=float)
    fa = np.nan_to_num(np.asarray(fit.fa, dtype=float))
    seeds = _seed_points(seed_mask, affine, seed_density)
    streamlines: list[np.ndarray] = []
    for seed in seeds:
        streamline = _track_one(
            seed,
            tensors,
            fa,
            affine,
            step_size=step_size,
            fa_threshold=fa_threshold,
            min_length=min_length,
            max_length=max_length,
            max_angle=max_angle,
        )
        if streamline is not None:
            streamlines.append(streamline)
    if out_trk is not None:
        _save_trk(streamlines, affine, out_trk)
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
    """Run probabilistic tractography with the NumPy/SciPy tensor engine."""

    seed_mask = np.asarray(seed_mask, dtype=bool)
    stop_map = np.asarray(stop_map, dtype=float)
    fit = fit_tensor(data, gtab, mask=stop_map > 0)
    tensors = np.asarray(fit.tensors, dtype=float)
    fa = np.nan_to_num(np.asarray(fit.fa, dtype=float))
    seeds = _seed_points(seed_mask, affine, seed_density)
    rng = np.random.default_rng(random_seed)
    streamlines: list[np.ndarray] = []
    for seed in seeds:
        streamline = _track_probabilistic_one(
            seed,
            tensors,
            fa,
            affine,
            rng,
            step_size=step_size,
            fa_threshold=fa_threshold,
            min_length=min_length,
            max_length=max_length,
            max_angle=max_angle,
        )
        if streamline is not None:
            streamlines.append(streamline)
    if out_trk is not None:
        _save_trk(streamlines, affine, out_trk)
    return streamlines


__all__ = ["track_deterministic", "track_probabilistic"]
