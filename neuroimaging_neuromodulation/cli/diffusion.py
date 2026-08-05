"""Diffusion MRI command-line interface."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import nibabel as nib
import numpy as np

from ..paths import package_data_dir
from ..diffusion.afq import afq_subject_pipeline
from ..diffusion.connectivity import count_streamlines_between_masks
from ..diffusion.dti import fit_tensor, load_dwi, write_tensor_metrics
from ..diffusion.outliers import remove_fiber_outliers
from ..diffusion.render import render_streamlines_3d_html, render_streamlines_html
from ..diffusion.roi_segmentation import segment_streamlines_by_rois
from ..diffusion.segmentation import segment_streamlines_by_atlas
from ..diffusion.streamlines_io import save_tract_streamlines
from ..diffusion.tracking import track_deterministic, track_probabilistic
from ..diffusion.tract_profile import load_tract_streamlines, tract_profile
from ..diffusion.transform import (
    transform_streamlines_with_ants,
    transform_streamlines_with_field,
)
from ..diffusion.external import (
    build_fsl_applytopup_command,
    build_fsl_applywarp_command,
    build_fsl_bedpostx_command,
    build_fsl_bet_command,
    build_fsl_convert_xfm_command,
    build_fsl_dtifit_command,
    build_fsl_eddy_correct_command,
    build_fsl_flirt_command,
    build_fsl_fnirt_command,
    build_fsl_invwarp_command,
    build_fsl_probtrackx_command,
    build_fsl_topup_command,
    build_mrtrix_tckgen_command,
    check_external_tools,
    run_fsl_applytopup,
    run_fsl_applywarp,
    run_fsl_bedpostx,
    run_fsl_bet,
    run_fsl_dtifit,
    run_fsl_eddy_correct,
    run_fsl_flirt,
    run_fsl_fnirt,
    run_fsl_invwarp,
    run_fsl_probtrackx,
    run_fsl_topup,
    run_mrtrix_tckgen,
)
from ..diffusion import external as external_module


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nm-diffusion",
        description="Python-native DTI and tractography tools",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    fit = subparsers.add_parser("fit-tensor", help="Fit tensors and write scalar maps")
    fit.add_argument("--dwi", required=True)
    fit.add_argument("--bval", required=True)
    fit.add_argument("--bvec", required=True)
    fit.add_argument("--output-dir", required=True)
    fit.add_argument("--prefix", default="DTI")
    fit.set_defaults(handler=run_fit_tensor)

    track = subparsers.add_parser("track", help="Run deterministic tensor tractography")
    track.add_argument("--dwi", required=True)
    track.add_argument("--bval", required=True)
    track.add_argument("--bvec", required=True)
    track.add_argument("--seed", required=True)
    track.add_argument("--stop", required=True)
    track.add_argument("--output", required=True)
    track.add_argument("--fa-threshold", type=float, default=0.2)
    track.add_argument("--step-size", type=float, default=0.5)
    track.add_argument("--min-length", type=float, default=10.0)
    track.add_argument("--max-length", type=float, default=500.0)
    track.add_argument("--max-angle", type=float, default=30.0)
    track.add_argument("--seed-density", type=int, default=1)
    track.set_defaults(handler=run_track)

    prob = subparsers.add_parser("track-probabilistic", help="Run probabilistic tensor tractography")
    prob.add_argument("--dwi", required=True)
    prob.add_argument("--bval", required=True)
    prob.add_argument("--bvec", required=True)
    prob.add_argument("--seed", required=True)
    prob.add_argument("--stop", required=True)
    prob.add_argument("--output", required=True)
    prob.add_argument("--fa-threshold", type=float, default=0.2)
    prob.add_argument("--step-size", type=float, default=0.5)
    prob.add_argument("--min-length", type=float, default=10.0)
    prob.add_argument("--max-length", type=float, default=500.0)
    prob.add_argument("--max-angle", type=float, default=20.0)
    prob.add_argument("--seed-density", type=int, default=1)
    prob.add_argument("--random-seed", type=int, default=1)
    prob.set_defaults(handler=run_track_probabilistic)

    conn = subparsers.add_parser("connectivity", help="Track and count seed-target connections")
    conn.add_argument("--dwi", required=True)
    conn.add_argument("--bval", required=True)
    conn.add_argument("--bvec", required=True)
    conn.add_argument("--seed", required=True)
    conn.add_argument("--target", required=True)
    conn.add_argument("--stop", required=True)
    conn.add_argument("--trk-output", required=True)
    conn.add_argument("--count-output", required=True)
    conn.add_argument("--fa-threshold", type=float, default=0.2)
    conn.set_defaults(handler=run_connectivity)

    profile = subparsers.add_parser("tract-profile", help="Extract scalar values along tract streamlines")
    profile.add_argument("--tracks", required=True, help="TRK or TCK tractogram")
    profile.add_argument("--scalar", required=True, help="3D scalar NIfTI")
    profile.add_argument("--output", required=True, help="Output .npy profile")
    profile.add_argument("--output-csv", help="Optional output CSV profile")
    profile.add_argument("--n-points", type=int, default=100)
    profile.add_argument("--volume-index", type=int, default=0)
    profile.set_defaults(handler=run_tract_profile)

    segment = subparsers.add_parser("segment-tracts", help="Segment streamlines with an atlas label map")
    segment.add_argument("--tracks", required=True)
    segment.add_argument("--atlas", required=True)
    segment.add_argument("--output-json", required=True)
    segment.add_argument("--n-samples", type=int, default=50)
    segment.set_defaults(handler=run_segment_tracts)

    roi_segment = subparsers.add_parser("segment-tracts-roi", help="Segment streamlines using AFQ waypoint ROIs")
    roi_segment.add_argument("--tracks", required=True)
    roi_segment.add_argument("--roi-dir", default=None, help="Directory containing MNI_JHU_tracts_ROIs")
    roi_segment.add_argument("--atlas", default=None, help="4D JHU tract probability atlas")
    roi_segment.add_argument("--output-json", required=True)
    roi_segment.add_argument("--min-dist", type=float, default=2.0)
    roi_segment.add_argument("--n-samples", type=int, default=50)
    roi_segment.set_defaults(handler=run_segment_tracts_roi)

    clean = subparsers.add_parser("clean-tracts", help="Remove AFQ-style streamline outliers")
    clean.add_argument("--tracks", required=True)
    clean.add_argument("--reference", required=True, help="Reference NIfTI for tractogram space")
    clean.add_argument("--output", required=True, help="Output cleaned TRK tractogram")
    clean.add_argument("--keep-json", required=True)
    clean.add_argument("--max-dist", type=float, default=4.0)
    clean.add_argument("--max-len", type=float, default=4.0)
    clean.add_argument("--num-nodes", type=int, default=25)
    clean.add_argument("--max-iter", type=int, default=5)
    clean.set_defaults(handler=run_clean_tracts)

    transform = subparsers.add_parser("transform-tracts", help="Transform streamlines with a deformation field")
    transform.add_argument("--tracks", required=True)
    transform.add_argument("--field", required=True)
    transform.add_argument("--source", required=True)
    transform.add_argument("--reference", required=True)
    transform.add_argument("--output", required=True)
    transform.add_argument("--zero-based", action="store_true")
    transform.set_defaults(handler=run_transform_tracts)

    transform_ants = subparsers.add_parser("transform-tracts-ants", help="Transform streamlines with ANTs point transforms")
    transform_ants.add_argument("--tracks", required=True)
    transform_ants.add_argument("--reference", required=True)
    transform_ants.add_argument("--transforms", nargs="+", required=True)
    transform_ants.add_argument("--output", required=True)
    transform_ants.add_argument("--use-inverse", type=int, default=1, choices=[0, 1])
    transform_ants.add_argument("--transform-inverse", default=None, help="Comma-separated use-inverse flags per transform")
    transform_ants.set_defaults(handler=run_transform_tracts_ants)

    render = subparsers.add_parser("render-tracts", help="Render streamlines as HTML/SVG projections")
    render.add_argument("--tracks", required=True)
    render.add_argument("--atlas", required=True)
    render.add_argument("--output", required=True)
    render.add_argument("--n-samples", type=int, default=50)
    render.add_argument("--title", default="Tract render")
    render.set_defaults(handler=run_render_tracts)

    render_3d = subparsers.add_parser("render-tracts-3d", help="Render streamlines as an interactive HTML/WebGL viewer")
    render_3d.add_argument("--tracks", required=True)
    render_3d.add_argument("--atlas", required=True)
    render_3d.add_argument("--output", required=True)
    render_3d.add_argument("--n-samples", type=int, default=50)
    render_3d.add_argument("--title", default="Tract render 3D")
    render_3d.set_defaults(handler=run_render_tracts_3d)

    afq = subparsers.add_parser("afq-pipeline", help="Run a subject-level AFQ-style tract analysis")
    afq.add_argument("--tracks", required=True)
    afq.add_argument("--atlas", required=True)
    afq.add_argument("--scalar", required=True)
    afq.add_argument("--output-dir", required=True)
    afq.add_argument("--n-samples", type=int, default=50)
    afq.add_argument("--num-nodes", type=int, default=30)
    afq.add_argument("--max-dist", type=float, default=4.0)
    afq.add_argument("--max-len", type=float, default=4.0)
    afq.add_argument("--method", choices=["atlas", "roi"], default="atlas")
    afq.add_argument("--roi-dir", default=None)
    afq.add_argument("--tract-atlas", default=None)
    afq.add_argument("--min-dist", type=float, default=2.0)
    afq.set_defaults(handler=run_afq_pipeline)

    bedpostx = subparsers.add_parser("fsl-bedpostx", help="Run FSL bedpostx (requires FSL)")
    bedpostx.add_argument("--bedpostx-dir", required=True)
    bedpostx.add_argument("--dry-run", action="store_true")
    bedpostx.set_defaults(handler=run_fsl_bedpostx_cmd)

    dtifit = subparsers.add_parser("fsl-dtifit", help="Run FSL dtifit (requires FSL)")
    dtifit.add_argument("--dwi", required=True)
    dtifit.add_argument("--mask", required=True)
    dtifit.add_argument("--bvec", required=True)
    dtifit.add_argument("--bval", required=True)
    dtifit.add_argument("--output-prefix", required=True)
    dtifit.add_argument("--dry-run", action="store_true")
    dtifit.set_defaults(handler=run_fsl_dtifit_cmd)

    prob = subparsers.add_parser("fsl-probtrackx", help="Run FSL probtrackx2 (requires FSL)")
    prob.add_argument("--seed", required=True)
    prob.add_argument("--target", required=True)
    prob.add_argument("--bedpostx-dir", required=True)
    prob.add_argument("--output-dir", required=True)
    prob.add_argument("--samples", type=int, default=5000)
    prob.add_argument("--steps", type=int, default=2000)
    prob.add_argument("--dry-run", action="store_true")
    prob.set_defaults(handler=run_fsl_probtrackx_cmd)

    tckgen = subparsers.add_parser("mrtrix-tckgen", help="Run MRtrix tckgen (requires MRtrix3)")
    tckgen.add_argument("--dwi", required=True)
    tckgen.add_argument("--mask", required=True)
    tckgen.add_argument("--seed-image", required=True)
    tckgen.add_argument("--output", required=True)
    tckgen.add_argument("--algorithm", default="iFOD2")
    tckgen.add_argument("--num-tracks", type=int, default=100000)
    tckgen.add_argument("--dry-run", action="store_true")
    tckgen.set_defaults(handler=run_mrtrix_tckgen_cmd)

    bet = subparsers.add_parser("fsl-bet", help="Run FSL BET (requires FSL)")
    bet.add_argument("--input", required=True)
    bet.add_argument("--output", required=True)
    bet.add_argument("--no-mask", action="store_true")
    bet.add_argument("--dry-run", action="store_true")
    bet.set_defaults(handler=run_fsl_bet_cmd)

    eddy = subparsers.add_parser("fsl-eddy-correct", help="Run legacy FSL eddy_correct (requires FSL)")
    eddy.add_argument("--input", required=True)
    eddy.add_argument("--output", required=True)
    eddy.add_argument("--reference", type=int, default=0)
    eddy.add_argument("--dry-run", action="store_true")
    eddy.set_defaults(handler=run_fsl_eddy_correct_cmd)

    fa2t1 = subparsers.add_parser("fsl-fa2t1", help="Build FSL FA-to-T1 transform commands")
    fa2t1.add_argument("--fa", required=True)
    fa2t1.add_argument("--ref", required=True)
    fa2t1.add_argument("--output", required=True)
    fa2t1.add_argument("--matrix", required=True)
    fa2t1.add_argument("--inverse-matrix", required=True)
    fa2t1.add_argument("--dry-run", action="store_true")
    fa2t1.set_defaults(handler=run_fsl_fa2t1_cmd)

    t12mni = subparsers.add_parser("fsl-t12mni", help="Build FSL T1-to-MNI warp commands")
    t12mni.add_argument("--t1", required=True)
    t12mni.add_argument("--mni", required=True)
    t12mni.add_argument("--out-prefix", required=True)
    t12mni.add_argument("--config", default="T1_2_MNI152_2mm")
    t12mni.add_argument("--dry-run", action="store_true")
    t12mni.set_defaults(handler=run_fsl_t12mni_cmd)

    mni2native = subparsers.add_parser("fsl-mni2native", help="Build FSL MNI-to-native transform commands")
    mni2native.add_argument("--image", required=True)
    mni2native.add_argument("--t1", required=True)
    mni2native.add_argument("--fa", required=True)
    mni2native.add_argument("--warp", required=True)
    mni2native.add_argument("--premat", required=True)
    mni2native.add_argument("--output", required=True)
    mni2native.add_argument("--dry-run", action="store_true")
    mni2native.set_defaults(handler=run_fsl_mni2native_cmd)

    native2mni = subparsers.add_parser("fsl-native2mni", help="Build FSL native-to-MNI transform commands")
    native2mni.add_argument("--image", required=True)
    native2mni.add_argument("--t1", required=True)
    native2mni.add_argument("--fa", required=True)
    native2mni.add_argument("--matrix", required=True)
    native2mni.add_argument("--warp", required=True)
    native2mni.add_argument("--mni", required=True)
    native2mni.add_argument("--output", required=True)
    native2mni.add_argument("--dry-run", action="store_true")
    native2mni.set_defaults(handler=run_fsl_native2mni_cmd)

    topup = subparsers.add_parser("fsl-topup", help="Run FSL topup and applytopup (requires FSL)")
    topup.add_argument("--imain", required=True)
    topup.add_argument("--datain", required=True)
    topup.add_argument("--config", required=True)
    topup.add_argument("--output-prefix", required=True)
    topup.add_argument("--pa-image", required=True)
    topup.add_argument("--inindex", default="1,2")
    topup.add_argument("--output", required=True)
    topup.add_argument("--dry-run", action="store_true")
    topup.set_defaults(handler=run_fsl_topup_cmd)

    check = subparsers.add_parser("check-external", help="Check FSL/MRtrix binary availability")
    check.set_defaults(handler=run_check_external)

    return parser


def _load_bool(path: str) -> tuple[np.ndarray, nib.Nifti1Image]:
    img = nib.load(path)
    return np.asanyarray(img.dataobj) > 0, img


def run_fit_tensor(args: argparse.Namespace) -> int:
    data, _affine, gtab, img = load_dwi(args.dwi, args.bval, args.bvec)
    mask = np.asanyarray(img.dataobj)[..., 0] > 0
    fit = fit_tensor(data, gtab, mask=mask)
    paths = write_tensor_metrics(fit, img, args.output_dir, prefix=args.prefix)
    for key, path in paths.items():
        print(key, path)
    return 0


def run_track(args: argparse.Namespace) -> int:
    data, affine, gtab, _ = load_dwi(args.dwi, args.bval, args.bvec)
    seed_mask, _ = _load_bool(args.seed)
    stop_map = np.asanyarray(nib.load(args.stop).dataobj)
    streamlines = track_deterministic(
        data,
        gtab,
        affine,
        seed_mask=seed_mask,
        stop_map=stop_map,
        fa_threshold=args.fa_threshold,
        step_size=args.step_size,
        min_length=args.min_length,
        max_length=args.max_length,
        max_angle=args.max_angle,
        seed_density=args.seed_density,
        out_trk=args.output,
    )
    print(args.output, len(streamlines))
    return 0


def run_track_probabilistic(args: argparse.Namespace) -> int:
    data, affine, gtab, _ = load_dwi(args.dwi, args.bval, args.bvec)
    seed_mask, _ = _load_bool(args.seed)
    stop_map = np.asanyarray(nib.load(args.stop).dataobj)
    streamlines = track_probabilistic(
        data,
        gtab,
        affine,
        seed_mask=seed_mask,
        stop_map=stop_map,
        fa_threshold=args.fa_threshold,
        step_size=args.step_size,
        min_length=args.min_length,
        max_length=args.max_length,
        max_angle=args.max_angle,
        seed_density=args.seed_density,
        random_seed=args.random_seed,
        out_trk=args.output,
    )
    print(args.output, len(streamlines))
    return 0


def run_connectivity(args: argparse.Namespace) -> int:
    data, affine, gtab, _ = load_dwi(args.dwi, args.bval, args.bvec)
    seed_mask, _ = _load_bool(args.seed)
    target_mask, _ = _load_bool(args.target)
    stop_map = np.asanyarray(nib.load(args.stop).dataobj)
    streamlines = track_deterministic(
        data,
        gtab,
        affine,
        seed_mask=seed_mask,
        stop_map=stop_map,
        fa_threshold=args.fa_threshold,
        out_trk=args.trk_output,
    )
    result = count_streamlines_between_masks(
        streamlines,
        affine,
        seed_mask,
        target_mask,
    )
    Path(args.count_output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(args.trk_output)
    print(args.count_output)
    return 0


def run_tract_profile(args: argparse.Namespace) -> int:
    streamlines = load_tract_streamlines(args.tracks, args.scalar)
    result = tract_profile(
        streamlines,
        args.scalar,
        n_points=args.n_points,
        volume_index=args.volume_index,
    )
    np.save(args.output, result["profile"])
    if args.output_csv:
        np.savetxt(args.output_csv, result["profile"], delimiter=",")
    print(args.output, result["n_streamlines"])
    return 0


def run_segment_tracts(args: argparse.Namespace) -> int:
    streamlines = load_tract_streamlines(args.tracks, args.atlas)
    result = segment_streamlines_by_atlas(
        streamlines,
        args.atlas,
        n_samples=args.n_samples,
    )
    Path(args.output_json).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(args.output_json)
    return 0


def run_segment_tracts_roi(args: argparse.Namespace) -> int:
    package_data = package_data_dir()
    roi_dir = args.roi_dir or package_data / "MNI_JHU_tracts_ROIs"
    atlas = args.atlas or package_data / "MNI_JHU_tracts_prob.nii.gz"
    streamlines = load_tract_streamlines(args.tracks, atlas)
    result = segment_streamlines_by_rois(
        streamlines,
        roi_dir,
        atlas_image=atlas,
        min_dist=args.min_dist,
        n_samples=args.n_samples,
    )
    Path(args.output_json).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(args.output_json)
    return 0


def run_clean_tracts(args: argparse.Namespace) -> int:
    reference = nib.load(args.reference)
    streamlines = load_tract_streamlines(args.tracks, reference)
    cleaned, keep = remove_fiber_outliers(
        streamlines,
        max_dist=args.max_dist,
        max_len=args.max_len,
        num_nodes=args.num_nodes,
        max_iter=args.max_iter,
    )
    save_tract_streamlines(cleaned, reference, args.output)
    Path(args.keep_json).write_text(
        json.dumps(
            {
                "input_streamlines": len(streamlines),
                "output_streamlines": len(cleaned),
                "keep": keep.astype(int).tolist(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(args.output, len(cleaned))
    return 0


def run_transform_tracts(args: argparse.Namespace) -> int:
    source = nib.load(args.source)
    reference = nib.load(args.reference)
    streamlines = load_tract_streamlines(args.tracks, source)
    transformed = transform_streamlines_with_field(
        streamlines,
        args.field,
        source,
        reference,
        one_based=not args.zero_based,
    )
    save_tract_streamlines(transformed, reference, args.output)
    print(args.output, len(transformed))
    return 0


def run_transform_tracts_ants(args: argparse.Namespace) -> int:
    reference = nib.load(args.reference)
    streamlines = load_tract_streamlines(args.tracks, reference)
    transformed = transform_streamlines_with_ants(
        streamlines,
        [Path(transform) for transform in args.transforms],
        use_inverse=args.use_inverse,
        transform_inverse=(
            [int(value) for value in args.transform_inverse.split(",")]
            if args.transform_inverse
            else None
        ),
    )
    save_tract_streamlines(transformed, reference, args.output)
    print(args.output, len(transformed))
    return 0


def run_render_tracts(args: argparse.Namespace) -> int:
    streamlines = load_tract_streamlines(args.tracks, args.atlas)
    segmentation = segment_streamlines_by_atlas(
        streamlines,
        args.atlas,
        n_samples=args.n_samples,
    )
    path = render_streamlines_html(
        streamlines,
        segmentation["labels"],
        args.output,
        title=args.title,
    )
    print(path)
    return 0


def run_render_tracts_3d(args: argparse.Namespace) -> int:
    streamlines = load_tract_streamlines(args.tracks, args.atlas)
    segmentation = segment_streamlines_by_atlas(
        streamlines,
        args.atlas,
        n_samples=args.n_samples,
    )
    path = render_streamlines_3d_html(
        streamlines,
        segmentation["labels"],
        args.output,
        title=args.title,
    )
    print(path)
    return 0


def run_afq_pipeline(args: argparse.Namespace) -> int:
    package_data = package_data_dir()
    roi_dir = args.roi_dir or package_data / "MNI_JHU_tracts_ROIs"
    tract_atlas = args.tract_atlas or package_data / "MNI_JHU_tracts_prob.nii.gz"
    streamlines = load_tract_streamlines(args.tracks, args.atlas)
    result = afq_subject_pipeline(
        streamlines,
        args.atlas,
        args.scalar,
        n_samples=args.n_samples,
        num_nodes=args.num_nodes,
        max_dist=args.max_dist,
        max_len=args.max_len,
        segmentation=args.method,
        roi_dir=roi_dir,
        tract_atlas=tract_atlas,
        min_dist=args.min_dist,
    )
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_tracts = []
    for tract in result["tracts"]:
        label = tract["label"]
        np.save(output_dir / f"tract_{label:02d}_profile.npy", tract["profile"])
        np.save(output_dir / f"tract_{label:02d}_std.npy", tract["std"])
        summary_tracts.append(
            {
                "label": label,
                "input_streamlines": tract["input_streamlines"],
                "output_streamlines": tract["output_streamlines"],
            }
        )
    summary_path = output_dir / "afq_summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "n_streamlines": result["n_streamlines"],
                "tracts": summary_tracts,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(summary_path)
    return 0


def run_fsl_bedpostx_cmd(args: argparse.Namespace) -> int:
    cmd = build_fsl_bedpostx_command(args.bedpostx_dir)
    if args.dry_run:
        print(" ".join(cmd))
        return 0
    result = run_fsl_bedpostx(args.bedpostx_dir)
    print(result["returncode"])
    return 0


def run_fsl_dtifit_cmd(args: argparse.Namespace) -> int:
    cmd = build_fsl_dtifit_command(args.dwi, args.mask, args.bvec, args.bval, args.output_prefix)
    if args.dry_run:
        print(" ".join(cmd))
        return 0
    result = run_fsl_dtifit(args.dwi, args.mask, args.bvec, args.bval, args.output_prefix)
    print(result["returncode"])
    return 0


def run_fsl_probtrackx_cmd(args: argparse.Namespace) -> int:
    cmd = build_fsl_probtrackx_command(
        args.seed,
        args.target,
        args.bedpostx_dir,
        args.output_dir,
        samples=args.samples,
        steps=args.steps,
    )
    if args.dry_run:
        print(" ".join(cmd))
        return 0
    result = run_fsl_probtrackx(
        args.seed,
        args.target,
        args.bedpostx_dir,
        args.output_dir,
        samples=args.samples,
        steps=args.steps,
    )
    print(result["returncode"])
    return 0


def run_mrtrix_tckgen_cmd(args: argparse.Namespace) -> int:
    cmd = build_mrtrix_tckgen_command(
        args.dwi,
        args.mask,
        args.output,
        algorithm=args.algorithm,
        num_tracks=args.num_tracks,
        seed_image=args.seed_image,
    )
    if args.dry_run:
        print(" ".join(cmd))
        return 0
    result = run_mrtrix_tckgen(
        args.dwi,
        args.mask,
        args.output,
        algorithm=args.algorithm,
        num_tracks=args.num_tracks,
        seed_image=args.seed_image,
    )
    print(result["returncode"])
    return 0


def _execute_commands(commands: list[list[str]], dry_run: bool) -> int:
    if dry_run:
        for command in commands:
            print(" ".join(command))
        return 0
    for command in commands:
        external_module._run(command)
    return 0


def run_fsl_bet_cmd(args: argparse.Namespace) -> int:
    commands = [
        build_fsl_bet_command(
            args.input,
            args.output,
            mask=not args.no_mask,
        )
    ]
    return _execute_commands(commands, args.dry_run)


def run_fsl_eddy_correct_cmd(args: argparse.Namespace) -> int:
    commands = [
        build_fsl_eddy_correct_command(
            args.input,
            args.output,
            args.reference,
        )
    ]
    return _execute_commands(commands, args.dry_run)


def run_fsl_fa2t1_cmd(args: argparse.Namespace) -> int:
    commands = [
        build_fsl_flirt_command(
            args.fa,
            args.ref,
            args.output,
            out_matrix=args.matrix,
        ),
        build_fsl_convert_xfm_command(
            args.matrix,
            args.inverse_matrix,
            inverse=True,
        ),
    ]
    return _execute_commands(commands, args.dry_run)


def run_fsl_t12mni_cmd(args: argparse.Namespace) -> int:
    affine = f"{args.out_prefix}_affine.mat"
    coeff = f"{args.out_prefix}_coeff"
    inverse_warp = f"{args.out_prefix}_MNI2T1transf"
    commands = [
        build_fsl_flirt_command(
            args.t1,
            args.mni,
            out_matrix=affine,
        ),
        build_fsl_fnirt_command(
            args.t1,
            args.mni,
            coeff,
            affine=affine,
            config=args.config,
        ),
        build_fsl_invwarp_command(coeff, inverse_warp, args.t1),
    ]
    return _execute_commands(commands, args.dry_run)


def run_fsl_mni2native_cmd(args: argparse.Namespace) -> int:
    t1_space = f"{args.output}_T1Sp"
    commands = [
        build_fsl_applywarp_command(
            args.image,
            args.t1,
            t1_space,
            args.warp,
        ),
        build_fsl_flirt_command(
            t1_space,
            args.fa,
            args.output,
            init_matrix=args.premat,
            apply_xfm=True,
        ),
    ]
    return _execute_commands(commands, args.dry_run)


def run_fsl_native2mni_cmd(args: argparse.Namespace) -> int:
    t1_space = f"{args.output}_T1Sp"
    commands = [
        build_fsl_flirt_command(
            args.image,
            args.t1,
            t1_space,
            init_matrix=args.matrix,
            apply_xfm=True,
        ),
        build_fsl_applywarp_command(
            t1_space,
            args.mni,
            args.output,
            args.warp,
        ),
    ]
    return _execute_commands(commands, args.dry_run)


def run_fsl_topup_cmd(args: argparse.Namespace) -> int:
    commands = [
        build_fsl_topup_command(
            args.imain,
            args.datain,
            args.config,
            args.output_prefix,
        ),
        build_fsl_applytopup_command(
            f"{args.imain},{args.pa_image}",
            args.inindex,
            args.datain,
            args.output_prefix,
            args.output,
        ),
    ]
    return _execute_commands(commands, args.dry_run)


def run_check_external(args: argparse.Namespace) -> int:
    print(json.dumps(check_external_tools(), indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
