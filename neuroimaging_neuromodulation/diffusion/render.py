"""Dependency-free SVG streamline rendering for tract QC."""

from __future__ import annotations

import html
import json
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


def render_streamlines_3d_html(
    streamlines: list[np.ndarray],
    labels: list[int],
    output_html: str | Path,
    *,
    title: str = "Tract render 3D",
) -> Path:
    """Write an interactive HTML/WebGL viewer for streamline tract QC."""

    if len(streamlines) != len(labels):
        raise ValueError("streamlines and labels must have the same length")
    streamlines_json = json.dumps(
        [[[float(value) for value in point] for point in streamline] for streamline in streamlines],
        separators=(",", ":"),
    )
    labels_json = json.dumps([int(label) for label in labels], separators=(",", ":"))
    content = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>__TITLE__</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<style>
html, body { margin: 0; height: 100%; background: #111827; color: #e5e7eb; font-family: sans-serif; }
#legend { position: absolute; top: 1rem; left: 1rem; z-index: 2; background: rgba(17,24,39,0.82); padding: 0.6rem 0.8rem; border-radius: 6px; font-size: 0.8rem; }
#fallback { position: absolute; inset: 0; display: none; align-items: center; justify-content: center; z-index: 1; }
canvas { display: block; }
</style></head><body>
<div id="legend">Drag to rotate, scroll to zoom.</div>
<div id="fallback">WebGL is not available in this browser.</div>
<script>
const streamlines = __STREAMLINES__;
const labels = __LABELS__;
const colors = ["#e6194b","#3cb44b","#4363d8","#f58231","#911eb4","#42d4f4","#f032e6","#bfef45","#fabed4","#469990","#dcbeff","#9A6324","#fffac8","#800000","#aaffc3","#808000","#ffd8b1","#000075","#a9a9a9","#ffffff"];
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 5000);
camera.position.set(120, 100, 180);
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);
const group = new THREE.Group();
scene.add(group);
const allPoints = [];
for (const streamline of streamlines) for (const p of streamline) allPoints.push(p);
if (allPoints.length) {
  const xs = allPoints.map(p => p[0]), ys = allPoints.map(p => p[1]), zs = allPoints.map(p => p[2]);
  const center = new THREE.Vector3(
    (Math.min(...xs) + Math.max(...xs)) / 2,
    (Math.min(...ys) + Math.max(...ys)) / 2,
    (Math.min(...zs) + Math.max(...zs)) / 2
  );
  const radius = Math.max(Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys), Math.max(...zs) - Math.min(...zs)) / 2;
  camera.position.copy(center).add(new THREE.Vector3(radius * 2.4, radius * 2.0, radius * 3.4));
  camera.lookAt(center);
  const grid = new THREE.GridHelper(Math.max(radius * 3, 1), 20, 0x4b5563, 0x374151);
  group.add(grid);
  streamlines.forEach((streamline, index) => {
    if (streamline.length < 2) return;
    const points = streamline.map(p => new THREE.Vector3(p[0] - center.x, p[1] - center.y, p[2] - center.z));
    const geometry = new THREE.BufferGeometry().setFromPoints(points);
    const color = labels[index] > 0 ? colors[labels[index] % colors.length] : "#9ca3af";
    group.add(new THREE.Line(geometry, new THREE.LineBasicMaterial({ color })));
  });
}
let dragging = false;
let last = { x: 0, y: 0 };
renderer.domElement.addEventListener("mousedown", event => {
  dragging = true;
  last = { x: event.clientX, y: event.clientY };
});
window.addEventListener("mouseup", () => { dragging = false; });
window.addEventListener("mousemove", event => {
  if (!dragging) return;
  const dx = event.clientX - last.x;
  const dy = event.clientY - last.y;
  group.rotation.y += dx * 0.01;
  group.rotation.x += dy * 0.01;
  last = { x: event.clientX, y: event.clientY };
});
renderer.domElement.addEventListener("wheel", event => {
  event.preventDefault();
  camera.position.multiplyScalar(event.deltaY > 0 ? 1.08 : 0.92);
  camera.lookAt(scene.position);
}, { passive: false });
window.addEventListener("resize", () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});
function animate() {
  requestAnimationFrame(animate);
  renderer.render(scene, camera);
}
if (renderer.getContext()) {
  animate();
} else {
  document.getElementById("fallback").style.display = "flex";
}
</script>
</body></html>
"""
    content = (
        content.replace("__TITLE__", html.escape(title))
        .replace("__STREAMLINES__", streamlines_json)
        .replace("__LABELS__", labels_json)
    )
    output_html = Path(output_html)
    output_html.parent.mkdir(parents=True, exist_ok=True)
    output_html.write_text(content, encoding="utf-8")
    return output_html


__all__ = ["render_streamlines_3d_html", "render_streamlines_html"]
