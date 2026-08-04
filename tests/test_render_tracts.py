from __future__ import annotations

import numpy as np

from neuroimaging_neuromodulation.diffusion.render import (
    render_streamlines_3d_html,
    render_streamlines_html,
)


def test_render_streamlines_html(tmp_path) -> None:
    streamlines = [
        np.array([[0.0, 0.0, 0.0], [5.0, 2.0, 3.0], [10.0, 4.0, 6.0]]),
        np.array([[1.0, 1.0, 1.0], [6.0, 3.0, 4.0], [11.0, 5.0, 7.0]]),
    ]
    output = render_streamlines_html(
        streamlines,
        [1, 2],
        tmp_path / "render.html",
        title="QC",
    )
    content = output.read_text(encoding="utf-8")
    assert "<svg" in content
    assert "Axial" in content
    assert "Coronal" in content
    assert "Sagittal" in content


def test_render_streamlines_3d_html(tmp_path) -> None:
    streamlines = [
        np.array([[0.0, 0.0, 0.0], [5.0, 2.0, 3.0], [10.0, 4.0, 6.0]]),
        np.array([[1.0, 1.0, 1.0], [6.0, 3.0, 4.0], [11.0, 5.0, 7.0]]),
    ]
    output = render_streamlines_3d_html(
        streamlines,
        [1, 2],
        tmp_path / "render3d.html",
        title="3D QC",
    )
    content = output.read_text(encoding="utf-8")
    assert "three.min.js" in content
    assert "WebGLRenderer" in content
    assert "const streamlines =" in content
    assert "const labels =" in content
