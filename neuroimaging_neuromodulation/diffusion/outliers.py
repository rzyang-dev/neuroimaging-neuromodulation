"""AFQ-style fiber outlier removal."""

from __future__ import annotations

import numpy as np

from .tract_profile import _resample_streamline


def _orient_fibers(streamlines: list[np.ndarray]) -> list[np.ndarray]:
    if not streamlines:
        return streamlines
    reference = streamlines[0]
    if len(reference) < 2:
        return streamlines
    reference_vector = reference[-1] - reference[0]
    oriented = []
    for streamline in streamlines:
        if len(streamline) < 2:
            oriented.append(streamline)
            continue
        vector = streamline[-1] - streamline[0]
        oriented.append(streamline if np.dot(reference_vector, vector) >= 0 else streamline[::-1])
    return oriented


def _mahalanobis_distances(
    resampled: list[np.ndarray],
    core: np.ndarray,
    covariances: np.ndarray,
) -> np.ndarray:
    n_fibers = len(resampled)
    n_nodes = core.shape[1]
    distances = np.zeros((n_fibers, n_nodes), dtype=float)
    for node in range(n_nodes):
        points = np.stack([fiber[node, :] for fiber in resampled], axis=0)
        centered = points - core[node]
        covariance = covariances[node]
        if np.linalg.matrix_rank(covariance) < 3:
            distances[:, node] = np.linalg.norm(centered, axis=1)
        else:
            inv_covariance = np.linalg.inv(covariance)
            distances[:, node] = np.sqrt(
                np.einsum("ij,jk,ik->i", centered, inv_covariance, centered)
            )
    return distances


def remove_fiber_outliers(
    streamlines: list[np.ndarray],
    *,
    max_dist: float = 4.0,
    max_len: float = 4.0,
    num_nodes: int = 25,
    max_iter: int = 5,
) -> tuple[list[np.ndarray], np.ndarray]:
    """Remove fibers that differ from the group core in length or shape."""

    streamlines = list(streamlines)
    keep = np.ones(len(streamlines), dtype=bool)
    for _ in range(max_iter):
        indices = np.flatnonzero(keep)
        if len(indices) == 0:
            break
        current = [streamlines[i] for i in indices]
        lengths = np.array([np.sum(np.linalg.norm(np.diff(s, axis=0), axis=1)) for s in current])
        mean_len = float(np.mean(lengths))
        std_len = float(np.std(lengths))
        keep1 = np.ones(len(current), dtype=bool)
        if std_len > 1e-12:
            keep1 = np.abs(lengths - mean_len) / std_len < max_len

        keep_local = keep1.copy()
        if int(keep1.sum()) > 20:
            kept_streamlines = [s for s, flag in zip(current, keep1) if flag]
            oriented = _orient_fibers(kept_streamlines)
            resampled = [_resample_streamline(s, num_nodes) for s in oriented]
            valid = [item for item in resampled if item is not None]
            if len(valid) > 20:
                stack = np.stack(valid, axis=2)
                core = np.mean(stack, axis=2)
                centered = stack - core[:, :, None]
                covariances = np.einsum("ijn,ikn->ijk", centered, centered) / max(len(valid) - 1, 1)
                distances = _mahalanobis_distances(valid, core, covariances)
                distance_flags = np.all(distances < max_dist, axis=1)
                valid_index = 0
                for local_index, flag in enumerate(keep1):
                    if flag:
                        if resampled[valid_index] is not None:
                            keep_local[local_index] = distance_flags[valid_index]
                        else:
                            keep_local[local_index] = False
                        valid_index += 1

        new_keep = keep.copy()
        new_keep[indices] = keep_local
        if np.array_equal(new_keep, keep):
            break
        keep = new_keep

    return [s for s, flag in zip(streamlines, keep) if flag], keep


__all__ = ["remove_fiber_outliers"]
