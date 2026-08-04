"""HTML tract QC report generation for AFQ-style outputs."""

from __future__ import annotations

import html
import json
import shutil
from pathlib import Path

import numpy as np

from .plots import plot_group_profiles
from .statistics import profile_group_statistics


def tract_qc_report(
    profile_files: list[str | Path],
    output_dir: str | Path,
    *,
    n_group1: int,
    labels: list[str] | None = None,
    segmentation_json: str | Path | None = None,
    render_html: str | Path | None = None,
) -> Path:
    """Write an HTML QC report with profile statistics and SVG plots."""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    stats = profile_group_statistics(profile_files, n_group1=n_group1, labels=labels)
    plots = plot_group_profiles(
        profile_files,
        output_dir,
        n_group1=n_group1,
        labels=labels,
    )

    segmentation_counts = ""
    if segmentation_json is not None:
        data = json.loads(Path(segmentation_json).read_text(encoding="utf-8"))
        count_rows = "".join(
            f"<tr><td>{html.escape(label)}</td><td>{count}</td></tr>"
            for label, count in data.get("counts", {}).items()
        )
        segmentation_counts = (
            "<h2>Tract segmentation counts</h2><table>"
            "<tr><th>Atlas label</th><th>Streamlines</th></tr>"
            f"{count_rows}</table>"
        )
    render_link = ""
    if render_html is not None:
        render_dest = output_dir / "tract_3d.html"
        shutil.copy2(Path(render_html), render_dest)
        render_link = (
            '<h2><a href="tract_3d.html">Interactive 3D fiber viewer</a></h2>'
        )

    rows = []
    for index, (profile, plot_path) in enumerate(zip(stats["profiles"], plots)):
        p_values = np.asarray(profile["p"])
        mean_diff = float(np.mean(np.asarray(profile["group2_mean"]) - np.asarray(profile["group1_mean"])))
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(profile['label']))}</td>"
            f"<td>{mean_diff:.6f}</td>"
            f"<td>{float(np.min(p_values)):.6g}</td>"
            f'<td><a href="{html.escape(plot_path.name)}">SVG</a></td>'
            "</tr>"
        )
    content = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Tract QC report</title>
<style>
body {{ font-family: sans-serif; margin: 2rem; color: #1f2933; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #d2d6dc; padding: 0.5rem; text-align: left; }}
</style></head><body>
<h1>Tract QC report</h1>
<table><tr><th>Tract</th><th>Mean group difference</th><th>Minimum p</th><th>Plot</th></tr>
{''.join(rows)}</table>
{segmentation_counts}
{render_link}
</body></html>
"""
    report_path = output_dir / "qc.html"
    report_path.write_text(content, encoding="utf-8")
    return report_path


__all__ = ["tract_qc_report"]
