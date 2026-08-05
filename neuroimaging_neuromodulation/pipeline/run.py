"""Config-driven pipeline execution."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import numpy as np

from .. import __version__
from ..io.dicom import convert_dicom_directory, convert_dicom_series_by_index
from ..io.nifti import load_volume, save_volume
from ..preprocess.covariates import design_matrix, extract_signal, regress_out_nuisance
from ..preprocess.motion import estimate_motion_parameters
from ..preprocess.temporal import slice_timing_correct_volume
from ..reporting.manifest import write_reproducibility_manifest
from ..reporting.html import render_target_report
from ..targets.pipeline import seed_based_fc, target_site


def _load_config(config: dict[str, Any] | str | Path) -> dict[str, Any]:
    if isinstance(config, (str, Path)):
        path = Path(config)
        if not path.exists():
            raise ValueError(f"Pipeline config not found: {path}")
        return json.loads(path.read_text(encoding="utf-8"))
    return config


def _first_nifti(directory: Path) -> Path:
    candidates = sorted(directory.rglob("*.nii*"))
    if not candidates:
        raise ValueError(f"No NIfTI file found in {directory}")
    return candidates[0]


def validate_pipeline_config(config: dict[str, Any]) -> dict[str, Any]:
    """Validate the user-facing pipeline configuration before running."""

    config = dict(config)
    subject = config.get("subject", "subject")
    if not isinstance(subject, str) or not subject.strip():
        raise ValueError("Pipeline requires a non-empty string 'subject'")
    output_dir = Path(config.get("output_dir", "data/pipeline"))
    if not output_dir:
        raise ValueError("Pipeline requires a non-empty 'output_dir'")

    functional = config.get("functional")
    dicom = config.get("dicom") or {}
    if not functional and dicom.get("functional"):
        dicom_path = Path(str(dicom["functional"]))
        if not dicom_path.exists():
            raise ValueError(f"DICOM directory does not exist: {dicom_path}")
    if not functional and not dicom.get("functional"):
        raise ValueError("Pipeline requires 'functional' or dicom.functional")
    if functional:
        functional_path = Path(os.path.expanduser(str(functional)))
        if not functional_path.exists():
            raise ValueError(f"Functional image does not exist: {functional_path}")

    for key in ("seed", "mask"):
        value = config.get(key)
        if not value:
            raise ValueError(f"Pipeline requires '{key}'")
        path = Path(os.path.expanduser(str(value)))
        if not path.exists():
            raise ValueError(f"{key} image does not exist: {path}")

    if config.get("tr") is not None and float(config["tr"]) <= 0:
        raise ValueError("'tr' must be greater than zero")
    if config.get("slice_order") and config.get("tr") is None:
        raise ValueError("'tr' is required when 'slice_order' is set")
    return config


def run_pipeline(config: dict[str, Any] | str | Path) -> dict[str, Any]:
    """Run an end-to-end workflow from a JSON/dict configuration."""

    config = _load_config(config)
    config = validate_pipeline_config(config)
    subject = config.get("subject", "subject")
    output_dir = Path(config.get("output_dir", "data/pipeline"))
    subject_dir = output_dir / subject
    subject_dir.mkdir(parents=True, exist_ok=True)

    functional_path = config.get("functional")
    dicom = config.get("dicom") or {}
    if not functional_path and dicom.get("functional"):
        if dicom.get("functional_series_index") is not None:
            functional_path = subject_dir / "FunImg" / "fundata.nii"
            convert_dicom_series_by_index(
                dicom["functional"],
                int(dicom["functional_series_index"]),
                functional_path,
            )
        else:
            convert_dicom_directory(dicom["functional"], subject_dir / "FunImg")
            functional_path = _first_nifti(subject_dir / "FunImg")
    if not functional_path:
        raise ValueError("Pipeline requires 'functional' or dicom.functional")

    t1_path = config.get("t1")
    if not t1_path and dicom.get("structural"):
        if dicom.get("structural_series_index") is not None:
            t1_path = subject_dir / "T1Img" / "t1.nii"
            convert_dicom_series_by_index(
                dicom["structural"],
                int(dicom["structural_series_index"]),
                t1_path,
            )
        else:
            convert_dicom_directory(dicom["structural"], subject_dir / "T1Img")
            t1_path = _first_nifti(subject_dir / "T1Img")

    img, data = load_volume(functional_path)
    if data.ndim != 4:
        raise ValueError("Functional input must be 4D")

    current_path = Path(functional_path)
    if config.get("slice_order"):
        tr = float(config["tr"])
        order = [int(x) for x in config["slice_order"]]
        ref_slice = int(config.get("ref_slice", 1))
        data = slice_timing_correct_volume(data, tr, order, ref_slice)
        current_path = subject_dir / "slice_timed.nii"
        save_volume(data, img, current_path)

    rp_path = None
    if config.get("estimate_motion", False):
        motion = config.get("motion") or {}
        level_iters = tuple(motion.get("level_iters", (5, 2, 1)))
        pipeline = tuple(motion.get("pipeline", ("translation", "rigid")))
        corrected, rp = estimate_motion_parameters(
            data,
            img.affine,
            reference_volume=int(motion.get("reference_volume", 0)),
            pipeline=pipeline,
            level_iters=level_iters,
            optimizer_options={"maxiter": int(motion.get("maxiter", 10))},
        )
        current_path = subject_dir / "motion_corrected.nii"
        save_volume(corrected, img, current_path)
        rp_path = subject_dir / "rp.txt"
        np.savetxt(rp_path, rp, fmt="%.10f")

    regressed_path = None
    nuisance = config.get("nuisance") or {}
    if config.get("regress_covariates", False) or nuisance:
        rp = np.loadtxt(rp_path) if rp_path else None
        wm_signal = None
        csf_signal = None
        global_signal = None
        if nuisance.get("wm_signal"):
            wm_signal = np.loadtxt(nuisance["wm_signal"]).reshape(-1)
        if nuisance.get("csf_signal"):
            csf_signal = np.loadtxt(nuisance["csf_signal"]).reshape(-1)
        if nuisance.get("global_signal"):
            global_signal = np.loadtxt(nuisance["global_signal"]).reshape(-1)
        matrix = data.reshape(-1, data.shape[3])
        for key, mask_path in (
            ("wm_mask", nuisance.get("wm_mask")),
            ("csf_mask", nuisance.get("csf_mask")),
            ("global_mask", nuisance.get("global_mask")),
        ):
            if not mask_path:
                continue
            _, mask_data = load_volume(mask_path)
            signal = extract_signal(matrix, mask_data.reshape(-1) > 0)
            if key == "wm_mask":
                wm_signal = signal
            elif key == "csf_mask":
                csf_signal = signal
            else:
                global_signal = signal
        design = design_matrix(
            matrix.shape[1],
            motion_parameters=rp,
            wm_signal=wm_signal,
            csf_signal=csf_signal,
            global_signal=global_signal,
        )
        regressed = regress_out_nuisance(matrix, design)
        current_path = subject_dir / "regressed.nii"
        save_volume(regressed.reshape(data.shape), img, current_path)
        regressed_path = current_path

    tr = float(config["tr"]) if config.get("tr") is not None else None
    fc_result = seed_based_fc(
        current_path,
        config["seed"],
        config["mask"],
        output_dir,
        subject=subject,
        target_mask_image=config.get("target_mask"),
        c6_image=config.get("c6"),
        c1_image=config.get("c1"),
        depth_mm=config.get("depth_mm"),
        extend_iterations=int(config.get("extend_iterations", 15)),
        tr=tr,
        band=(float(config.get("low_cutoff", 0.01)), float(config.get("high_cutoff", 0.1)))
        if config.get("filter", False)
        else None,
        filter_data=bool(config.get("filter", False)),
    )

    target_result = None
    if config.get("target", True):
        target_cfg = config.get("target") or {}
        if target_cfg is True:
            target_cfg = {}
        target_result = target_site(
            fc_result["SeedFCinROI"],
            output_dir,
            subject=subject,
            posneg=target_cfg.get("posneg", ["Positive", "Negative"]),
            p_value=float(target_cfg.get("p_value", 0.05)),
            n_samples=int(target_cfg.get("n_samples", 212)),
            native_deformation=target_cfg.get("native_deformation"),
        )

    t1_target_result = None
    t1_target_cfg = config.get("t1_target")
    if t1_target_cfg:
        if t1_target_cfg is True:
            t1_target_cfg = {}
        if not t1_path:
            raise ValueError("t1_target requires a structural T1 path")
        target_path = t1_target_cfg.get("target") or config.get("target_mask")
        if not target_path:
            raise ValueError("t1_target requires 'target' or top-level 'target_mask'")
        from ..targets.t1 import generate_t1_target

        t1_target_result = generate_t1_target(
            t1_path,
            target_path,
            Path(t1_target_cfg.get("output") or subject_dir / "IndiTarget_T1Sp.nii"),
            deformation_field=t1_target_cfg.get("deformation"),
            spm_exe=t1_target_cfg.get("spm_exe"),
            spm_output_dir=t1_target_cfg.get("spm_dir"),
            timeout=int(t1_target_cfg.get("timeout", 1800)),
        )

    report_path = None
    if config.get("report", True):
        report_path = render_target_report(output_dir, subject)

    manifest_path = write_reproducibility_manifest(
        subject_dir,
        {
            "package_version": __version__,
            "config": config,
            "outputs": {
                "report": str(report_path) if report_path else None,
                "subject_dir": str(subject_dir),
            },
        },
    )

    return {
        "subject": subject,
        "output_dir": str(output_dir),
        "functional": str(current_path),
        "t1": str(t1_path) if t1_path else None,
        "rp": str(rp_path) if rp_path else None,
        "regressed": str(regressed_path) if regressed_path else None,
        "seed_fc": {key: str(value) for key, value in fc_result.items() if hasattr(value, "__fspath__")},
        "target": target_result,
        "t1_target": {
            "output": str(t1_target_result["output_path"]),
            "metrics": t1_target_result.get("metrics"),
        }
        if t1_target_result
        else None,
        "report": str(report_path) if report_path else None,
        "manifest": str(manifest_path),
    }


__all__ = ["run_pipeline", "validate_pipeline_config"]
