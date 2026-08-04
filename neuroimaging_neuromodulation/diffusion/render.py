"""Dependency-free SVG streamline rendering for tract QC."""

from __future__ import annotations

import html
from pathlib import Path

import numpy as np


COLORS = [
    "#e6194b",
    "#3cb44b",
    "#4363d8",
    "#f58231",
    "#911eb4",
    "#42d4f4",
    "#f032e6",
    "#bfef45",
    "#fabed4",
    "#469990",
    "#dcbeff",
    "#9A6324",
    "#fffac8",
    "#800000",
    "#aaffc3",
    "#808000",
    "#ffd8b1",
    "#000075",
    "#a9a9a9",
    "#ffffff",
]


def _projection_svg(
    streamlines: list[np.ndarray],
    labels: list[int],
    x_axis: int,
    y_axis: int,
    width: int = 700,
    height: int = 500,
) -> str:
    all_points = np.vstack([streamline for streamline in streamlines if len(streamline) > 1])
    if len(all_points) == 0:
        return f'<svg width="{width}" height="{height}"></svg>'
    x_min, x_max = float(np.min(all_points[:, x_axis])), float(np.max(all_points[:, x_axis]))
    y_min, y_max = float(np.min(all_points[:, y_axis])), float(np.max(all_points[:, y_axis]))
    x_span = max(x_max - x_min, 1e-12)
    y_span = max(y_max - y_min, 1e-12)
    polylines = []
    for streamline, label in zip(streamlines, labels):
        if len(streamline) < 2:
            continue
        color = COLORS[int(label) % len(COLORS)] if int(label) > 0 else "#999999"
        points = []
        for point in streamline:
            px = 60.0 + (point[x_axis] - x_min) / x_span * (width - 100.0)
            py = height - 40.0 - (point[y_axis] - y_min) / y_span * (height - 70.0)
            points.append(f"{px:.2f},{py:.2f}")
        polylines.append(
            f'<polyline points="{" ".join(points)}" fill="none" stroke="{color}" stroke-width="1.2"/>'
        )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
        f'<rect width="{width}" height="{height}" fill="#111111"/>'
        f'{"".join(polylines)}</svg>'
    )


def render_streamlines_html(
    streamlines: list[np.ndarray],
    labels: list[int],
    output_html: str | Path,
    *,
    title: str = "Tract render",
) -> Path:
    """Write an HTML report with axial, coronal, and sagittal SVG projections."""

    if len(streamlines) != len(labels):
        raise ValueError("streamlines and labels must have the same length")
    panels = []
    for panel_name, x_axis, y_axis in (("Axial", 0, 1), ("Coronal", 0, 2), ("Sagittal", 1, 2)):
        panels.append(
            "<div>"
            f"<h3>{panel_name}</h3>"
            f"{_projection_svg(streamlines, labels, x_axis, y_axis)}"
            "</div>"
        )
    content = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>{html.escape(title)}</title>
<style>
body {{ font-family: sans-serif; margin: 2rem; color: #1f2933; }}
div {{ display: inline-block; margin: 0 1rem 1rem 0; }}
h3 {{ font-size: 0.9rem; }}
svg {{ border: 1px solid #444; }}
</style></head><body>
<h1>{html.escape(title)}</h1>
{''.join(panels)}
</body></html>
"""
    output_html = Path(output_html)
    output_html.parent.mkdir(parents=True, exist_ok=True)
    output_html.write_text(content, encoding="utf-8")
    return output_html


__all__ = ["render_streamlines_html"]
