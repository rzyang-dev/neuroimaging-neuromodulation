from __future__ import annotations

from pathlib import Path

import nibabel as nib
import numpy as np
import pytest

pytest.importorskip("dipy")

from dipy.data import get_fnames  # noqa: E402

from neuroimaging_neuromodulation.diffusion.connectivity import (  # noqa: E402
    count_streamlines_between_masks,
)
from neuroimaging_neuromodulation.diffusion.dti import (  # noqa: E402
    fit_tensor,
    load_dwi,
    write_tensor_metrics,
)
from neuroimaging_neuromodulation.diffusion.tracking import (  # noqa: E402
    track_deterministic,
    track_probabilistic,
)
from neuroimaging_neuromodulation.io.nifti import load_volume  # noqa: E402


def _real_dwi() -> tuple[Path, Path, Path]:
    dwi, bval, bvec = get_fnames(name="small_64D")
    return Path(dwi), Path(bval), Path(bvec)


def test_fit_tensor_real_dwi(tmp_path: Path) -> None:
    dwi, bval, bvec = _real_dwi()
    data, _affine, gtab, img = load_dwi(dwi, bval, bvec)
    mask = data[..., 0] > 0
    fit = fit_tensor(data, gtab, mask=mask)
    paths = write_tensor_metrics(fit, img, tmp_path, prefix="DTI")
    assert all(path.exists() for path in paths.values())
    _, fa = load_volume(paths["FA"])
    assert np.isfinite(fa).all()


def test_track_and_connectivity_real_dwi(tmp_path: Path) -> None:
    dwi, bval, bvec = _real_dwi()
    data, affine, gtab, img = load_dwi(dwi, bval, bvec)
    fit = fit_tensor(data, gtab, mask=data[..., 0] > 0)
    seed = np.zeros(data.shape[:3], dtype=bool)
    seed[4:6, 4:6, 4:6] = True
    target = np.zeros(data.shape[:3], dtype=bool)
    target[7:9, 4:6, 4:6] = True
    stop = np.nan_to_num(fit.fa)
    streamlines = track_deterministic(
        data,
        gtab,
        affine,
        seed_mask=seed,
        stop_map=stop,
        fa_threshold=0.15,
        step_size=0.5,
        min_length=2,
        max_length=50,
        max_angle=60,
        seed_density=1,
        out_trk=tmp_path / "tracks.trk",
    )
    assert len(streamlines) > 0
    assert (tmp_path / "tracks.trk").exists()
    result = count_streamlines_between_masks(streamlines, affine, seed, target)
    assert result["streamlines"] == len(streamlines)
    assert result["count"] >= 0


def test_probabilistic_tracking_real_dwi(tmp_path: Path) -> None:
    dwi, bval, bvec = _real_dwi()
    data, affine, gtab, _ = load_dwi(dwi, bval, bvec)
    fit = fit_tensor(data, gtab, mask=data[..., 0] > 0)
    seed = np.zeros(data.shape[:3], dtype=bool)
    seed[4:6, 4:6, 4:6] = True
    stop = np.nan_to_num(fit.fa)
    streamlines = track_probabilistic(
        data,
        gtab,
        affine,
        seed_mask=seed,
        stop_map=stop,
        fa_threshold=0.15,
        step_size=0.5,
        min_length=2,
        max_length=50,
        max_angle=60,
        random_seed=1,
        out_trk=tmp_path / "prob.trk",
    )
    assert len(streamlines) > 0
    assert (tmp_path / "prob.trk").exists()
