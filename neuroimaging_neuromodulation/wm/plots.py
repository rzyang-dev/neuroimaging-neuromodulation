"""Dependency-free SVG profile plots matching the original AFQplot style."""

from __future__ import annotations

import html
from pathlib import Path

import numpy as np


def _load_profile_matrix(path: str | Path) -> np.ndarray:
    path = Path(path)
    if path.suffix == ".npy":
        data = np.load(path)
    else:
        data = np.loadtxt(path)
    return np.asarray(data, dtype=float)


def _polygon_points(
    x_values: np.ndarray,
    mean: np.ndarray,
    upper: np.ndarray,
    lower: np.ndarray,
    width: float,
    height: float,
    y_min: float,
    y_max: float,
) -> str:
    points = []
    span = max(y_max - y_min, 1e-12)
    for x, y in zip(x_values, lower):
        px = 50.0 + x / max(len(x_values) - 1, 1) * (width - 90.0)
        py = height - 40.0 - (y - y_min) / span * (height - 70.0)
        points.append(f"{px:.2f},{py:.2f}")
    for x, y in zip(x_values[::-1], upper[::-1]):
        px = 50.0 + x / max(len(x_values) - 1, 1) * (width - 90.0)
        py = height - 40.0 - (y - y_min) / span * (height - 70.0)
        points.append(f"{px:.2f},{py:.2f}")
    return " ".join(points)


def _mean_line(
    x_values: np.ndarray,
    mean: np.ndarray,
    width: float,
    height: float,
    y_min: float,
    y_max: float,
    color: str,
) -> str:
    points = []
    span = max(y_max - y_min, 1e-12)
    for x, y in zip(x_values, mean):
        px = 50.0 + x / max(len(x_values) - 1, 1) * (width - 90.0)
        py = height - 40.0 - (y - y_min) / span * (height - 70.0)
        points.append(f"{px:.2f},{py:.2f}")
    return (
        f'<polyline points="{" ".join(points)}" fill="none" '
        f'stroke="{color}" stroke-width="2.5"/>'
    )


def plot_group_profiles(
    profile_files: list[str | Path],
    output_dir: str | Path,
    *,
    n_group1: int,
    labels: list[str] | None = None,
    title_prefix: str = "Tract",
) -> list[Path]:
    """Plot one SVG per tract profile with group means and standard-error bands."""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    if labels is None:
        labels = [f"{title_prefix} {i + 1}" for i in range(len(profile_files))]
    if len(labels) != len(profile_files):
        raise ValueError("labels must match profile_files")

    paths: list[Path] = []
    for index, profile_file in enumerate(profile_files):
        matrix = _load_profile_matrix(profile_file)
        if matrix.ndim == 1:
            matrix = matrix[None, :]
        if matrix.ndim != 2:
            raise ValueError(f"Profile file must be 2D or 1D: {profile_file}")
        if not 0 < n_group1 < matrix.shape[0]:
            raise ValueError("n_group1 must split the profile matrix into two groups")

        group1 = matrix[:n_group1, :]
        group2 = matrix[n_group1:, :]
        mean1 = np.mean(group1, axis=0)
        mean2 = np.mean(group2, axis=0)
        se1 = np.std(group1, axis=0) / np.sqrt(max(group1.shape[0] - 1, 1))
        se2 = np.std(group2, axis=0) / np.sqrt(max(group2.shape[0] - 1, 1))
        y_min = float(np.min([mean1 - se1, mean2 - se2]))
        y_max = float(np.max([mean1 + se1, mean2 + se2]))
        x_values = np.arange(matrix.shape[1], dtype=float)

        width, height = 600.0, 300.0
        poly1 = _polygon_points(x_values, mean1, mean1 + se1, mean1 - se1, width, height, y_min, y_max)
        poly2 = _polygon_points(x_values, mean2, mean2 + se2, mean2 - se2, width, height, y_min, y_max)
        line1 = _mean_line(x_values, mean1, width, height, y_min, y_max, "#000000")
        line2 = _mean_line(x_values, mean2, width, height, y_min, y_max, "#cc0000")
        title = html.escape(str(labels[index]))
        safe_name = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in str(labels[index]))
        path = output_dir / f"profile_{index:03d}_{safe_name}.svg"
        svg = f"""<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" viewBox="0 0 {width:.0f} {height:.0f}">
  <rect x="0" y="0" width="{width:.0f}" height="{height:.0f}" fill="#ffffff"/>
  <text x="50" y="24" font-family="sans-serif" font-size="14">{title}</text>
  <line x1="50" y1="{height - 40:.0f}" x2="{width - 40:.0f}" y2="{height - 40:.0f}" stroke="#444" stroke-width="1"/>
  <line x1="50" y1="30" x2="50" y2="{height - 40:.0f}" stroke="#444" stroke-width="1"/>
  <polygon points="{poly1}" fill="#000000" fill-opacity="0.25" stroke="none"/>
  <polygon points="{poly2}" fill="#cc0000" fill-opacity="0.25" stroke="none"/>
  {line1}
  {line2}
  <text x="80" y="{height - 12:.0f}" font-family="sans-serif" font-size="11" fill="#000">Group 1</text>
  <text x="180" y="{height - 12:.0f}" font-family="sans-serif" font-size="11" fill="#cc0000">Group 2</text>
</svg>
"""
        path.write_text(svg, encoding="utf-8")
        paths.append(path)
    return paths


__all__ = ["plot_group_profiles"]
