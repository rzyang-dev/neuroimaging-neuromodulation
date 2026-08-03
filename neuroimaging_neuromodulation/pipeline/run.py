"""Config-driven pipeline execution."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from ..io.dicom import convert_dicom_directory
from ..io.nifti import load_volume, save_volume
from ..preprocess.covariates import design_matrix, extract_signal, regress_out_nuisance
from ..preprocess.motion import estimate_motion_parameters
from ..preprocess.temporal import slice_timing_correct_volume
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


def run_pipeline(config: dict[str, Any] | str | Path) -> dict[str, Any]:
    """Run an end-to-end workflow from a JSON/dict configuration."""

    config = _load_config(config)
    subject = config.get("subject", "subject")
    output_dir = Path(config.get("output_dir", "data/pipeline"))
    subject_dir = output_dir / subject
    subject_dir.mkdir(parents=True, exist_ok=True)

    functional_path = config.get("functional")
    dicom = config.get("dicom") or {}
    if not functional_path and dicom.get("functional"):
        convert_dicom_directory(dicom["functional"], subject_dir / "FunImg")
        functional_path = _first_nifti(subject_dir / "FunImg")
    if not functional_path:
        raise ValueError("Pipeline requires 'functional' or dicom.functional")

    t1_path = config.get("t1")
    if not t1_path and dicom.get("structural"):
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
        )

    report_path = None
    if config.get("report", True):
        report_path = render_target_report(output_dir, subject)

    return {
        "subject": subject,
        "output_dir": str(output_dir),
        "functional": str(current_path),
        "t1": str(t1_path) if t1_path else None,
        "rp": str(rp_path) if rp_path else None,
        "regressed": str(regressed_path) if regressed_path else None,
        "seed_fc": {key: str(value) for key, value in fc_result.items() if hasattr(value, "__fspath__")},
        "target": target_result,
        "report": str(report_path) if report_path else None,
    }


__all__ = ["run_pipeline"]
