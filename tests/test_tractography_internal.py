from __future__ import annotations

import numpy as np

from neuroimaging_neuromodulation.diffusion.connectivity import (
    count_streamlines_between_masks,
)
from neuroimaging_neuromodulation.diffusion.dti import GradientTable
from neuroimaging_neuromodulation.diffusion.tracking import track_deterministic


def _synthetic_dwi_and_gtab() -> tuple[np.ndarray, GradientTable]:
    bvals = np.array([0.0, 1000.0, 1000.0, 1000.0, 1000.0, 1000.0, 1000.0])
    bvecs = np.array(
        [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [1.0, 1.0, 0.0],
            [1.0, 0.0, 1.0],
            [0.0, 1.0, 1.0],
        ]
    )
    gtab = GradientTable(bvals=bvals, bvecs=bvecs)
    tensor = np.diag([0.0012, 0.0003, 0.0003])
    apparent = np.sum(bvecs * (bvecs @ tensor), axis=1)
    signal = np.exp(-bvals * apparent)
    data = np.broadcast_to(signal, (8, 8, 8, 7)).copy()
    data[..., 0] = 1.0
    return data, gtab


def test_deterministic_tracking_and_connectivity_without_dipy(tmp_path) -> None:
    data, gtab = _synthetic_dwi_and_gtab()
    affine = np.eye(4)
    seed = np.zeros(data.shape[:3], dtype=bool)
    target = np.zeros(data.shape[:3], dtype=bool)
    seed[2:4, 3:5, 3:5] = True
    target[6:8, 3:5, 3:5] = True
    from neuroimaging_neuromodulation.diffusion.dti import fit_tensor

    fit = fit_tensor(data, gtab, mask=np.ones(data.shape[:3], dtype=bool))
    stop = np.nan_to_num(fit.fa)
    streamlines = track_deterministic(
        data,
        gtab,
        affine,
        seed_mask=seed,
        stop_map=stop,
        fa_threshold=0.1,
        step_size=0.5,
        min_length=2.0,
        max_length=50.0,
        max_angle=60.0,
        seed_density=1,
        out_trk=tmp_path / "tracks.trk",
    )
    assert len(streamlines) > 0
    assert (tmp_path / "tracks.trk").exists()
    result = count_streamlines_between_masks(streamlines, affine, seed, target)
    assert result["count"] > 0
