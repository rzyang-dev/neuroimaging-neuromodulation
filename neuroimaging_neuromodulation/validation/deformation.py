"""Validation between the internal and optional DIPY deformation engines."""

from __future__ import annotations

import json
from pathlib import Path

from .metrics import compare_volumes


def compare_deformation_engines(
    moving_image: str | Path,
    static_image: str | Path,
    output_dir: str | Path,
    *,
    level_iters: tuple[int, ...] = (2, 1, 1),
    output_json: str | Path | None = None,
) -> dict[str, object]:
    """Run internal and DIPY engines and quantify warped-output agreement."""

    from ..deformations.estimate import estimate_deformation

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        dipy_result = estimate_deformation(
            moving_image,
            static_image,
            output_dir / "dipy",
            level_iters=level_iters,
            engine="dipy",
        )
    except (ImportError, RuntimeError):
        return {"dipy_available": False, "detail": "DIPY optional engine is not available"}

    internal_result = estimate_deformation(
        moving_image,
        static_image,
        output_dir / "internal",
        level_iters=level_iters,
        engine="internal",
    )
    metrics = compare_volumes(
        dipy_result["warped_moving"],
        internal_result["warped_moving"],
    )
    result: dict[str, object] = {
        "dipy_available": True,
        "metrics": metrics,
        "dipy_warped": str(dipy_result["warped_moving"]),
        "internal_warped": str(internal_result["warped_moving"]),
    }
    if output_json is not None:
        path = Path(output_json)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
        result["output_json"] = str(path)
    return result


__all__ = ["compare_deformation_engines"]
