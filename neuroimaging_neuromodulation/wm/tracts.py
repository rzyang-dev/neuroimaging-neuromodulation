"""White-matter tract-overlap reporting matching ``TMSCluRep4WM.m``."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from ..io.nifti import load_volume, resample_to_grid


def cluster_report_in_jhu(
    result_map: str | Path,
    template_map: str | Path,
    output_dir: str | Path,
    *,
    labels_file: str | Path | None = None,
    n_tracts: int = 20,
) -> Path:
    """Write overlap counts between a binary result and a JHU tract label map."""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    result_img, result_data = load_volume(result_map)
    if result_data.ndim != 3:
        raise ValueError("result_map must be 3D")
    template_img, template_data = load_volume(template_map)
    if template_data.shape != result_data.shape:
        _, template_data = resample_to_grid(template_map, result_img, order=0)
    template_data = np.asarray(template_data, dtype=float)
    result_binary = (np.asarray(result_data, dtype=float) > 0).astype(float)
    overlap = result_binary * template_data

    count = np.zeros(n_tracts, dtype=int)
    template_count = np.zeros(n_tracts, dtype=int)
    for tract in range(1, n_tracts + 1):
        count[tract - 1] = int(np.sum(overlap == tract))
        template_count[tract - 1] = int(np.sum(template_data == tract))
    percent = np.divide(
        100.0 * count,
        template_count,
        out=np.zeros(n_tracts, dtype=float),
        where=template_count > 0,
    )

    if labels_file is None:
        labels_file = Path(__file__).resolve().parents[1] / "data" / "JHUtractsLabel.txt"
    labels = Path(labels_file).read_text(encoding="utf-8").splitlines()
    labels = [label.strip() for label in labels if label.strip()]
    labels = labels[:n_tracts] + [f"Tract {i}" for i in range(len(labels) + 1, n_tracts + 1)]

    label_path = output_dir / "JHUtractsLabel.txt"
    if not label_path.exists():
        label_path.write_text("\n".join(labels[:n_tracts]) + "\n", encoding="utf-8")

    report_path = output_dir / "ResInJHUtracts.txt"
    with report_path.open("w", encoding="utf-8") as handle:
        for name, n_voxels, pct in zip(labels[:n_tracts], count, percent):
            handle.write(f"{name}  {n_voxels}  {pct:.6f}\n")
    return report_path


__all__ = ["cluster_report_in_jhu"]
