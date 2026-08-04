"""Dependency-free HTML/SVG image viewer for QC reports."""

from __future__ import annotations

import html
from pathlib import Path

import numpy as np

from ..io.nifti import load_volume


def _downsample(slice_2d: np.ndarray, max_dim: int = 80) -> np.ndarray:
    step = max(1, int(np.ceil(max(slice_2d.shape) / max_dim)))
    return slice_2d[::step, ::step]


def _normalize(slice_2d: np.ndarray) -> np.ndarray:
    values = np.asarray(slice_2d, dtype=float)
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return np.zeros_like(values)
    lo, hi = np.percentile(finite, [1.0, 99.0])
    normalized = (values - lo) / max(float(hi - lo), 1e-8)
    return np.clip(normalized, 0.0, 1.0)


def _slice_svg(reference: np.ndarray, overlay: np.ndarray | None, max_dim: int = 80) -> str:
    ref = _downsample(reference, max_dim)
    gray = (255.0 * _normalize(ref)).astype(int)
    overlay_down = _downsample(overlay, max_dim) if overlay is not None else None
    rows, cols = gray.shape
    rects = []
    for y in range(rows):
        for x in range(cols):
            r, g, b = gray[y, x], gray[y, x], gray[y, x]
            if overlay_down is not None and overlay_down[y, x] > 0:
                r, g, b = 255, 40, 40
            rects.append(
                f'<rect x="{x}" y="{y}" width="1" height="1" fill="rgb({r},{g},{b})"/>'
            )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{cols}" height="{rows}" '
        f'viewBox="0 0 {cols} {rows}">{"".join(rects)}</svg>'
    )


def render_viewer_report(
    reference_image: str | Path,
    output_html: str | Path,
    *,
    target_image: str | Path | None = None,
    slices: int = 9,
    max_dim: int = 80,
) -> Path:
    """Write an HTML QC report with axial slices and optional target overlay."""

    ref_img, ref_data = load_volume(reference_image)
    if ref_data.ndim == 4:
        ref_data = ref_data[..., 0]
    if ref_data.ndim != 3:
        raise ValueError("reference_image must be 3D")

    overlay_data = None
    if target_image is not None:
        _img, overlay_data = load_volume(target_image)
        if overlay_data.ndim == 4:
            overlay_data = overlay_data[..., 0]
        if overlay_data.shape != ref_data.shape:
            raise ValueError("target_image must match the reference image shape")

    indices = np.linspace(0, ref_data.shape[2] - 1, max(int(slices), 1)).astype(int)
    panels = []
    for index in indices:
        ref_slice = np.asarray(ref_data[:, :, int(index)], dtype=float)
        overlay_slice = np.asarray(overlay_data[:, :, int(index)], dtype=float) if overlay_data is not None else None
        panels.append(
            "<div>"
            f"<h3>Slice {int(index)}</h3>"
            f"{_slice_svg(ref_slice, overlay_slice, max_dim)}"
            "</div>"
        )
    content = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Image viewer QC</title>
<style>
body {{ font-family: sans-serif; margin: 2rem; color: #1f2933; }}
div {{ display: inline-block; margin: 0 1rem 1rem 0; }}
h3 {{ font-size: 0.9rem; }}
svg {{ image-rendering: pixelated; border: 1px solid #d2d6dc; }}
</style></head><body>
<h1>Image viewer QC</h1>
<p>Reference: {html.escape(str(reference_image))}</p>
<p>Target overlay: {html.escape(str(target_image) if target_image else "none")}</p>
{''.join(panels)}
</body></html>
"""
    output_html = Path(output_html)
    output_html.parent.mkdir(parents=True, exist_ok=True)
    output_html.write_text(content, encoding="utf-8")
    return output_html


__all__ = ["render_viewer_report"]
