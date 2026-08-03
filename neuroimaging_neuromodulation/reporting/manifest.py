"""File provenance manifest generation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import nibabel as nib


def sha256_file(path: str | Path, chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def write_target_manifest(
    subject_dir: str | Path,
    output_path: str | Path | None = None,
) -> Path:
    """Write a JSON manifest for all NIfTI/text outputs in a subject directory."""

    subject_dir = Path(subject_dir)
    if not subject_dir.exists():
        raise ValueError(f"Subject output directory does not exist: {subject_dir}")
    entries: list[dict[str, object]] = []
    for path in sorted(subject_dir.rglob("*")):
        if not path.is_file():
            continue
        entry: dict[str, object] = {
            "path": str(path.relative_to(subject_dir)),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        if path.suffix.lower() in {".nii", ".gz"}:
            try:
                img = nib.load(str(path))
                entry["shape"] = list(img.shape)
                entry["zooms"] = list(img.header.get_zooms())
                entry["affine"] = img.affine.tolist()
            except Exception:
                entry["nifti_metadata_error"] = "unreadable"
        entries.append(entry)
    manifest = {
        "subject_dir": str(subject_dir),
        "file_count": len(entries),
        "files": entries,
    }
    output_path = Path(output_path) if output_path is not None else subject_dir / "manifest.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    return output_path


__all__ = ["sha256_file", "write_target_manifest"]
