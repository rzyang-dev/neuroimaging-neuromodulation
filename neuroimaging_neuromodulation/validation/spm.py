"""SPM standalone helpers for deformation-convention reference validation."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import nibabel as nib
import numpy as np

from ..io.deformations import apply_deformation
from ..io.nifti import load_volume
from ..preprocess.motion import affine_registration_pipeline, affine_to_rp
from .metrics import compare_volumes

DEFAULT_SPM25_EXE = Path(
    r"C:\Users\ginger\spm_standalone_25.01.02_Windows\spm_standalone\spm25.exe"
)


def find_spm25() -> Path | None:
    """Locate the SPM25 standalone executable."""

    candidates: list[str] = []
    if os.environ.get("SPM25_EXE"):
        candidates.append(os.environ["SPM25_EXE"])
    if os.environ.get("SPM25_HOME"):
        candidates.append(str(Path(os.environ["SPM25_HOME"]) / "spm25.exe"))
    candidates.append(str(DEFAULT_SPM25_EXE))
    which = shutil.which("spm25")
    if which:
        candidates.append(which)
    for candidate in candidates:
        path = Path(candidate)
        if path.is_file():
            return path
    return None


def find_tpm_dir(spm_exe: Path | None = None) -> Path:
    """Return the SPM tissue probability map directory."""

    if os.environ.get("SPM_TPM_DIR"):
        return Path(os.environ["SPM_TPM_DIR"])
    exe = spm_exe or find_spm25()
    candidates: list[Path] = []
    if exe is not None:
        candidates.extend(
            [
                exe.parent / "spm25_mcr" / "spm25" / "tpm",
                exe.parent / "tpm",
            ]
        )
    candidates.append(Path.cwd() / "spm" / "tpm")
    for candidate in candidates:
        if (candidate / "TPM.nii").is_file():
            return candidate
    raise RuntimeError("SPM TPM.nii not found; set SPM_TPM_DIR")


def _matlab_str(path: Path) -> str:
    value = str(path).replace("\\", "/").replace("'", "''")
    return f"'{value}'"


def _matlab_volume(path: str | Path, index: int) -> str:
    value = f"{path},{index}".replace("\\", "/").replace("'", "''")
    return f"'{value}'"


def write_segment_batch(
    t1_path: Path,
    batch_path: Path,
    tpm_dir: Path,
) -> Path:
    """Write an SPM segmentation batch that emits y_ and iy_ fields."""

    batch_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"matlabbatch{{1}}.spm.spatial.preproc.channel.vols = {{{_matlab_str(t1_path)}}};",
        "matlabbatch{1}.spm.spatial.preproc.channel.biasreg = 0.001;",
        "matlabbatch{1}.spm.spatial.preproc.channel.biasfwhm = 60;",
        "matlabbatch{1}.spm.spatial.preproc.channel.write = [0 0];",
    ]
    ngaus = {1: 1, 2: 1, 3: 2, 4: 3, 5: 4, 6: 2}
    for tissue_index in range(1, 7):
        tpm = tpm_dir / f"TPM.nii,{tissue_index}"
        native = "[1 0]" if tissue_index <= 3 else "[0 0]"
        warped = "[1 1]" if tissue_index <= 3 else "[0 0]"
        lines.extend(
            [
                f"matlabbatch{{1}}.spm.spatial.preproc.tissue({tissue_index}).tpm = {{{_matlab_str(tpm)}}};",
                f"matlabbatch{{1}}.spm.spatial.preproc.tissue({tissue_index}).ngaus = {ngaus[tissue_index]};",
                f"matlabbatch{{1}}.spm.spatial.preproc.tissue({tissue_index}).native = {native};",
                f"matlabbatch{{1}}.spm.spatial.preproc.tissue({tissue_index}).warped = {warped};",
            ]
        )
    lines.extend(
        [
            "matlabbatch{1}.spm.spatial.preproc.warp.mrf = 1;",
            "matlabbatch{1}.spm.spatial.preproc.warp.cleanup = 1;",
            "matlabbatch{1}.spm.spatial.preproc.warp.reg = [0 0.001 0.5 0.05 0.2];",
            "matlabbatch{1}.spm.spatial.preproc.warp.affreg = 'mni';",
            "matlabbatch{1}.spm.spatial.preproc.warp.fwhm = 0;",
            "matlabbatch{1}.spm.spatial.preproc.warp.samp = 3;",
            "matlabbatch{1}.spm.spatial.preproc.warp.write = [1 1];",
        ]
    )
    batch_path.write_text("\n".join(lines) + "\n", encoding="ascii")
    return batch_path


def write_realign_batch(
    nifti_path: Path,
    batch_path: Path,
    n_volumes: int | None = None,
) -> Path:
    """Write an SPM realign-estwrite batch for a 4D NIfTI."""

    if n_volumes is None:
        data = np.asanyarray(nib.load(str(nifti_path)).dataobj)
        n_volumes = data.shape[3] if data.ndim == 4 else 1
    volumes = "; ".join(_matlab_volume(nifti_path, i) for i in range(1, int(n_volumes) + 1))
    session = "{" + volumes + "}"
    batch_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"matlabbatch{{1}}.spm.spatial.realign.estwrite.data = {{{session}}};",
        "matlabbatch{1}.spm.spatial.realign.estwrite.eoptions.quality = 0.9;",
        "matlabbatch{1}.spm.spatial.realign.estwrite.eoptions.sep = 4;",
        "matlabbatch{1}.spm.spatial.realign.estwrite.eoptions.fwhm = 5;",
        "matlabbatch{1}.spm.spatial.realign.estwrite.eoptions.rtm = 1;",
        "matlabbatch{1}.spm.spatial.realign.estwrite.eoptions.interp = 2;",
        "matlabbatch{1}.spm.spatial.realign.estwrite.eoptions.wrap = [0 0 0];",
        "matlabbatch{1}.spm.spatial.realign.estwrite.eoptions.weight = '';",
        "matlabbatch{1}.spm.spatial.realign.estwrite.roptions.which = [2 1];",
        "matlabbatch{1}.spm.spatial.realign.estwrite.roptions.interp = 4;",
        "matlabbatch{1}.spm.spatial.realign.estwrite.roptions.wrap = [0 0 0];",
        "matlabbatch{1}.spm.spatial.realign.estwrite.roptions.mask = 1;",
        "matlabbatch{1}.spm.spatial.realign.estwrite.roptions.prefix = 'r';",
    ]
    batch_path.write_text("\n".join(lines) + "\n", encoding="ascii")
    return batch_path


def run_spm_realign(
    fmri_path: str | Path,
    output_dir: str | Path,
    *,
    spm_exe: Path | None = None,
    timeout: int = 1800,
) -> dict[str, object]:
    """Run SPM25 realign-estwrite and return the realignment outputs."""

    exe = spm_exe or find_spm25()
    if exe is None:
        raise RuntimeError("SPM25 standalone executable not found")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    work_nifti = output_dir / "realign_input.nii"
    nib.save(nib.load(str(fmri_path)), work_nifti)
    batch_path = write_realign_batch(work_nifti, output_dir / "realign_batch.m")
    completed = subprocess.run(
        [str(exe), "batch", str(batch_path), "--silent"],
        cwd=str(output_dir),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"SPM realign failed with exit code {completed.returncode}:\n"
            f"{completed.stdout}\n{completed.stderr}"
        )
    paths = {
        "input": work_nifti,
        "rp_file": output_dir / "rp_realign_input.txt",
        "realigned": output_dir / "rrealign_input.nii",
        "mean": output_dir / "meanrealign_input.nii",
    }
    missing = [name for name, path in paths.items() if name != "mean" and not Path(path).exists()]
    if missing:
        raise RuntimeError(f"SPM realign did not produce expected outputs: {', '.join(missing)}")
    result: dict[str, object] = {
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "output_dir": output_dir,
    }
    result.update(paths)
    return result


def validate_motion_against_spm(
    fmri_path: str | Path,
    output_dir: str | Path,
    *,
    n_volumes: int = 4,
    spm_exe: Path | None = None,
    timeout: int = 1800,
) -> dict[str, object]:
    """Compare DIPY motion estimates with SPM25 realignment parameters."""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    img = nib.load(str(fmri_path))
    data = np.asanyarray(img.dataobj)
    if data.ndim != 4:
        raise ValueError("fmri_path must be a 4D NIfTI")
    n_volumes = min(int(n_volumes), data.shape[3])
    subset = data[..., :n_volumes].astype(np.float32)
    subset_path = output_dir / "fivevol.nii"
    nib.Nifti1Image(subset, img.affine).to_filename(subset_path)
    spm_result = run_spm_realign(subset_path, output_dir, spm_exe=spm_exe, timeout=timeout)
    dipy_affines = []
    for volume_index in range(n_volumes):
        if volume_index == 0:
            dipy_affines.append(np.eye(4))
            continue
        _resampled, final_affine = affine_registration_pipeline(
            subset[..., volume_index],
            subset[..., 0],
            moving_affine=img.affine,
            static_affine=img.affine,
            pipeline=("translation", "rigid"),
            level_iters=(5, 2, 1),
            optimizer_options={"maxiter": 10},
        )
        dipy_affines.append(np.linalg.inv(final_affine))
    dipy_rp = np.vstack([affine_to_rp(affine) for affine in dipy_affines])
    spm_rp = np.loadtxt(Path(spm_result["rp_file"]))
    if spm_rp.ndim == 1:
        spm_rp = spm_rp.reshape(1, -1)
    if spm_rp.shape[0] < n_volumes:
        raise ValueError("SPM RP file has fewer rows than the input volumes")
    spm_rp = spm_rp[:n_volumes]
    columns = ["tx", "ty", "tz", "rx", "ry", "rz"]
    correlations: list[float] = []
    mae: list[float] = []
    aligned_dipy_rp = dipy_rp.copy()
    sign_flipped: list[bool] = []
    for index in range(6):
        dipy_column = dipy_rp[:, index]
        spm_column = spm_rp[:, index]
        if np.std(dipy_column) > 1e-9 and np.std(spm_column) > 1e-9:
            correlation = float(np.corrcoef(dipy_column, spm_column)[0, 1])
        else:
            correlation = float("nan")
        if not np.isnan(correlation) and correlation < 0:
            aligned_dipy_rp[:, index] *= -1.0
            sign_flipped.append(True)
            correlation = abs(correlation)
        else:
            sign_flipped.append(False)
        correlations.append(correlation)
        mae.append(float(np.mean(np.abs(dipy_column - spm_column))))
    aligned_mae = [
        float(np.mean(np.abs(aligned_dipy_rp[:, index] - spm_rp[:, index])))
        for index in range(6)
    ]
    return {
        **spm_result,
        "n_volumes": n_volumes,
        "spm_rp": spm_rp,
        "dipy_rp": dipy_rp,
        "columns": columns,
        "correlations": correlations,
        "mae": mae,
        "aligned_dipy_rp": aligned_dipy_rp,
        "aligned_correlations": correlations,
        "aligned_mae": aligned_mae,
        "sign_flipped": sign_flipped,
    }


def run_spm_segmentation(
    t1_path: str | Path,
    output_dir: str | Path,
    *,
    spm_exe: Path | None = None,
    timeout: int = 1800,
) -> dict[str, object]:
    """Run SPM standalone segmentation and return the reference field paths."""

    exe = spm_exe or find_spm25()
    if exe is None:
        raise RuntimeError("SPM25 standalone executable not found")
    tpm_dir = find_tpm_dir(exe)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    work_t1 = output_dir / "T1.nii"
    nib.save(nib.load(str(t1_path)), work_t1)
    batch_path = write_segment_batch(work_t1, output_dir / "segment.m", tpm_dir)
    completed = subprocess.run(
        [str(exe), "batch", str(batch_path), "--silent"],
        cwd=str(output_dir),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"SPM segmentation failed with exit code {completed.returncode}:\n"
            f"{completed.stdout}\n{completed.stderr}"
        )
    paths = {
        "t1": work_t1,
        "batch": batch_path,
        "y_field": output_dir / "y_T1.nii",
        "iy_field": output_dir / "iy_T1.nii",
        "c1": output_dir / "c1T1.nii",
        "c2": output_dir / "c2T1.nii",
        "c3": output_dir / "c3T1.nii",
        "wc1": output_dir / "wc1T1.nii",
        "wc2": output_dir / "wc2T1.nii",
        "wc3": output_dir / "wc3T1.nii",
    }
    missing = [name for name, path in paths.items() if name not in {"batch", "t1"} and not Path(path).exists()]
    if missing:
        raise RuntimeError(f"SPM did not produce expected outputs: {', '.join(missing)}")
    result: dict[str, object] = {
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "output_dir": output_dir,
    }
    result.update(paths)
    return result


def validate_spm_deformation_convention(
    t1_path: str | Path,
    output_dir: str | Path,
    *,
    spm_exe: Path | None = None,
    timeout: int = 1800,
) -> dict[str, object]:
    """Generate SPM y_/iy_ fields and validate the package's world handling."""

    result = run_spm_segmentation(t1_path, output_dir, spm_exe=spm_exe, timeout=timeout)
    y_path = Path(result["y_field"])
    _, y_data = load_volume(y_path)
    shape = y_data.shape[:3]
    if y_data.min() >= 0 and y_data.max() <= max(shape):
        raise ValueError("SPM field does not look like a world-coordinate field")
    iy_path = Path(result["iy_field"])
    _, iy_data = load_volume(iy_path)
    _, c1_data = load_volume(Path(result["c1"]))
    if iy_data.shape[:3] != c1_data.shape[:3]:
        raise ValueError("SPM iy_ field grid does not match the native image grid")
    if iy_data.min() >= 0 and iy_data.max() <= max(iy_data.shape[:3]):
        raise ValueError("SPM iy_ field does not look like a world-coordinate field")
    _, resampled = apply_deformation(
        Path(result["c1"]),
        y_path,
        coordinate_system="world",
        order=1,
    )
    metrics = compare_volumes(Path(result["wc1"]), resampled)
    return {
        **result,
        "metrics": metrics,
    }


__all__ = [
    "find_spm25",
    "find_tpm_dir",
    "run_spm_segmentation",
    "run_spm_realign",
    "validate_spm_deformation_convention",
    "validate_motion_against_spm",
    "write_segment_batch",
    "write_realign_batch",
]
