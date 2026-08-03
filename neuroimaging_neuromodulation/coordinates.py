"""Voxel/world coordinate helpers matching the original toolbox conventions."""

from __future__ import annotations

import numpy as np


def voxel_size(affine: np.ndarray) -> np.ndarray:
    """Return the physical voxel size in mm for each axis."""

    affine = np.asarray(affine, dtype=float)
    return np.sqrt(np.sum(affine[:3, :3] ** 2, axis=0))


def affine_origin_1based(affine: np.ndarray) -> np.ndarray:
    """Return the voxel coordinate of the world origin using 1-based indexing.

    The original MATLAB toolbox derives this as ``inv(mat) * [0 0 0 1]`` and
    treats the result as a MATLAB matrix index.
    """

    affine = np.asarray(affine, dtype=float)
    return np.linalg.inv(affine) @ np.array([0.0, 0.0, 0.0, 1.0])


def mni_to_mat(coordinates: np.ndarray, affine: np.ndarray) -> np.ndarray:
    """Convert MNI/world coordinates to 1-based MATLAB matrix coordinates."""

    coordinates = np.asarray(coordinates, dtype=float)
    single = coordinates.ndim == 1
    coordinates = coordinates.reshape(-1, 3) if not single else coordinates.reshape(1, 3)
    affine = np.asarray(affine, dtype=float)
    vsize = voxel_size(affine)
    origin = affine_origin_1based(affine)[:3]
    sign = np.array([-1.0 if affine[0, 0] < 0 else 1.0, 1.0, 1.0])
    mat = np.round(coordinates * sign / vsize + origin)
    return mat[0] if single else mat


def mat_to_mni(coordinates: np.ndarray, affine: np.ndarray) -> np.ndarray:
    """Convert 1-based matrix coordinates to MNI/world coordinates.

    This intentionally mirrors ``TMSmat2mni.m``: it applies the affine directly
    to 1-based MATLAB coordinates.
    """

    coordinates = np.asarray(coordinates, dtype=float)
    single = coordinates.ndim == 1
    coordinates = coordinates.reshape(-1, 3) if not single else coordinates.reshape(1, 3)
    affine = np.asarray(affine, dtype=float)
    ones = np.ones((coordinates.shape[0], 1), dtype=float)
    world = (affine @ np.hstack([coordinates, ones]).T).T[:, :3]
    return world[0] if single else world


def voxel_indices(shape: tuple[int, ...]) -> np.ndarray:
    """Return all 1-based voxel indices for a volume as ``(N, 3)``."""

    indices = np.indices(shape, dtype=float)
    flat = indices.reshape(3, -1).T + 1.0
    return flat


def world_coordinates(shape: tuple[int, ...], affine: np.ndarray) -> np.ndarray:
    """Return all 1-based voxel coordinates transformed to world space."""

    return mat_to_mni(voxel_indices(shape), affine)
