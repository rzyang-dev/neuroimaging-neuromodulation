from __future__ import annotations

from pathlib import Path

import pytest

from neuroimaging_neuromodulation.validation.spm import write_dartel_batch


def test_write_dartel_batch(tmp_path: Path) -> None:
    rc_groups = [
        [tmp_path / "subj1" / "rc1.nii", tmp_path / "subj2" / "rc1.nii"],
        [tmp_path / "subj1" / "rc2.nii", tmp_path / "subj2" / "rc2.nii"],
        [tmp_path / "subj1" / "rc3.nii", tmp_path / "subj2" / "rc3.nii"],
    ]
    batch = write_dartel_batch(rc_groups, tmp_path / "dartel.m")
    content = batch.read_text(encoding="ascii")
    assert "spm.tools.dartel.warp.images" in content
    assert "settings.template = 'Template'" in content
    assert "rc1.nii" in content
    assert "rc3.nii" in content


def test_write_dartel_batch_requires_equal_groups(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="same number"):
        write_dartel_batch(
            [
                [tmp_path / "a.nii", tmp_path / "b.nii"],
                [tmp_path / "c.nii"],
            ],
            tmp_path / "bad.m",
        )
