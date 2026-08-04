"""Small Tkinter desktop interface for the toolbox."""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import numpy as np

from ..io.deformations import apply_deformation
from ..io.nifti import load_volume, save_volume
from ..preprocess.coregister import coregister_images
from ..preprocess.motion import estimate_motion_parameters
from ..preprocess.spatial import smooth_volume
from ..preprocess.temporal import slice_timing_correct_volume
from ..targets.pipeline import seed_based_fc, target_site
from ..targets.roi import deep_target, sphere_roi
from ..targets.t1 import generate_t1_target
from ..wm.alff import compute_alff


class ToolboxApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Neuroimaging and Neuromodulation Toolbox")
        self.geometry("900x680")
        self.minsize(760, 560)
        self.queue: queue.Queue[tuple[str, str]] = queue.Queue()
        self._build_ui()
        self.after(100, self._poll_queue)

    def _build_ui(self) -> None:
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)
        self.tms_tab = ttk.Frame(notebook)
        self.wm_tab = ttk.Frame(notebook)
        self.preprocess_tab = ttk.Frame(notebook)
        self.utility_tab = ttk.Frame(notebook)
        notebook.add(self.tms_tab, text="TMS Target")
        notebook.add(self.wm_tab, text="White Matter")
        notebook.add(self.preprocess_tab, text="Preprocess")
        notebook.add(self.utility_tab, text="Utilities")
        self._build_tms_tab()
        self._build_wm_tab()
        self._build_preprocess_tab()
        self._build_utility_tab()

        log_frame = ttk.LabelFrame(self, text="Log")
        log_frame.pack(fill="both", expand=False, padx=8, pady=(0, 8))
        self.log = tk.Text(log_frame, height=9, wrap="word", state="disabled")
        scroll = ttk.Scrollbar(log_frame, command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.log.pack(side="left", fill="both", expand=True)

    def _row(self, parent: tk.Widget) -> ttk.Frame:
        frame = ttk.Frame(parent)
        frame.pack(fill="x", padx=8, pady=4)
        return frame

    def _file_picker(self, frame: ttk.Frame, var: tk.StringVar, label: str, filetypes: tuple[tuple[str, str], ...]) -> None:
        ttk.Label(frame, text=label, width=16).pack(side="left")
        ttk.Entry(frame, textvariable=var).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(frame, text="Browse", command=lambda: self._pick_file(var, filetypes)).pack(side="left")

    def _dir_picker(self, frame: ttk.Frame, var: tk.StringVar, label: str) -> None:
        ttk.Label(frame, text=label, width=16).pack(side="left")
        ttk.Entry(frame, textvariable=var).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(frame, text="Browse", command=lambda: self._pick_dir(var)).pack(side="left")

    def _pick_file(self, var: tk.StringVar, filetypes: tuple[tuple[str, str], ...]) -> None:
        path = filedialog.askopenfilename(filetypes=filetypes)
        if path:
            var.set(path)

    def _pick_dir(self, var: tk.StringVar) -> None:
        path = filedialog.askdirectory()
        if path:
            var.set(path)

    def _build_tms_tab(self) -> None:
        self.func_var = tk.StringVar()
        self.seed_var = tk.StringVar()
        self.mask_var = tk.StringVar()
        self.tms_out_var = tk.StringVar()
        self.subject_var = tk.StringVar(value="subject")
        self.tr_var = tk.StringVar(value="2.0")
        self.low_var = tk.StringVar(value="0.01")
        self.high_var = tk.StringVar(value="0.1")
        self.zscore_var = tk.BooleanVar(value=False)

        frame = self._row(self.tms_tab)
        self._file_picker(frame, self.func_var, "Functional", (("NIfTI", "*.nii *.nii.gz"),))
        frame = self._row(self.tms_tab)
        self._file_picker(frame, self.seed_var, "Seed", (("NIfTI", "*.nii *.nii.gz"),))
        frame = self._row(self.tms_tab)
        self._file_picker(frame, self.mask_var, "Mask", (("NIfTI", "*.nii *.nii.gz"),))
        frame = self._row(self.tms_tab)
        self._dir_picker(frame, self.tms_out_var, "Output")
        frame = self._row(self.tms_tab)
        ttk.Label(frame, text="Subject").pack(side="left", padx=(0, 12))
        ttk.Entry(frame, textvariable=self.subject_var, width=24).pack(side="left")
        ttk.Label(frame, text="TR").pack(side="left", padx=(12, 4))
        ttk.Entry(frame, textvariable=self.tr_var, width=8).pack(side="left")
        ttk.Label(frame, text="Band").pack(side="left", padx=(12, 4))
        ttk.Entry(frame, textvariable=self.low_var, width=8).pack(side="left")
        ttk.Label(frame, text="-").pack(side="left")
        ttk.Entry(frame, textvariable=self.high_var, width=8).pack(side="left")
        ttk.Checkbutton(frame, text="Fisher z", variable=self.zscore_var).pack(side="left", padx=12)
        button_frame = ttk.Frame(self.tms_tab)
        button_frame.pack(fill="x", padx=8, pady=8)
        ttk.Button(button_frame, text="Compute Seed FC", command=self._run_fc).pack(side="left")
        ttk.Button(button_frame, text="Generate Target", command=self._run_target).pack(side="left", padx=8)

        ttk.Label(self.tms_tab, text="T1-space target", font=("Helvetica", 11, "bold")).pack(anchor="w", padx=8, pady=(12, 0))
        self.t1_image_var = tk.StringVar()
        self.t1_target_var = tk.StringVar()
        self.t1_deformation_var = tk.StringVar()
        self.t1_output_var = tk.StringVar()

        frame = self._row(self.tms_tab)
        self._file_picker(frame, self.t1_image_var, "T1", (("NIfTI", "*.nii *.nii.gz"),))
        frame = self._row(self.tms_tab)
        self._file_picker(frame, self.t1_target_var, "Target ROI", (("NIfTI", "*.nii *.nii.gz"),))
        frame = self._row(self.tms_tab)
        self._file_picker(frame, self.t1_deformation_var, "Def Field", (("NIfTI", "*.nii *.nii.gz"),))
        frame = self._row(self.tms_tab)
        ttk.Label(frame, text="Output").pack(side="left", padx=(0, 4))
        ttk.Entry(frame, textvariable=self.t1_output_var).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(frame, text="Browse", command=lambda: self._pick_file(self.t1_output_var, (("NIfTI", "*.nii"),))).pack(side="left")
        frame = self._row(self.tms_tab)
        ttk.Button(frame, text="Generate T1 Target", command=self._run_t1_target).pack(side="left")

    def _build_wm_tab(self) -> None:
        self.wm_func_var = tk.StringVar()
        self.wm_mask_var = tk.StringVar()
        self.wm_out_var = tk.StringVar()
        self.wm_tr_var = tk.StringVar(value="2.0")
        self.wm_low_var = tk.StringVar(value="0.01")
        self.wm_high_var = tk.StringVar(value="0.1")

        frame = self._row(self.wm_tab)
        self._file_picker(frame, self.wm_func_var, "Functional", (("NIfTI", "*.nii *.nii.gz"),))
        frame = self._row(self.wm_tab)
        self._file_picker(frame, self.wm_mask_var, "Mask", (("NIfTI", "*.nii *.nii.gz"),))
        frame = self._row(self.wm_tab)
        self._dir_picker(frame, self.wm_out_var, "Output")
        frame = self._row(self.wm_tab)
        ttk.Label(frame, text="TR").pack(side="left", padx=(0, 12))
        ttk.Entry(frame, textvariable=self.wm_tr_var, width=8).pack(side="left")
        ttk.Label(frame, text="Band").pack(side="left", padx=(12, 4))
        ttk.Entry(frame, textvariable=self.wm_low_var, width=8).pack(side="left")
        ttk.Label(frame, text="-").pack(side="left")
        ttk.Entry(frame, textvariable=self.wm_high_var, width=8).pack(side="left")
        frame = ttk.Frame(self.wm_tab)
        frame.pack(fill="x", padx=8, pady=8)
        ttk.Button(frame, text="Compute ALFF/fALFF", command=self._run_alff).pack(side="left")

    def _build_utility_tab(self) -> None:
        self.ref_var = tk.StringVar()
        self.center_var = tk.StringVar()
        self.radius_var = tk.StringVar(value="5")
        self.sphere_out_var = tk.StringVar()
        self.tissue_var = tk.StringVar()
        self.depth_var = tk.StringVar(value="6")
        self.deep_out_var = tk.StringVar()

        frame = self._row(self.utility_tab)
        self._file_picker(frame, self.ref_var, "Reference", (("NIfTI", "*.nii *.nii.gz"),))
        frame = self._row(self.utility_tab)
        ttk.Label(frame, text="MNI center").pack(side="left")
        ttk.Entry(frame, textvariable=self.center_var, width=32).pack(side="left", padx=4)
        ttk.Label(frame, text="Radius mm").pack(side="left")
        ttk.Entry(frame, textvariable=self.radius_var, width=8).pack(side="left", padx=4)
        frame = self._row(self.utility_tab)
        ttk.Label(frame, text="Output NIfTI").pack(side="left")
        ttk.Entry(frame, textvariable=self.sphere_out_var).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(frame, text="Browse", command=lambda: self._pick_file(self.sphere_out_var, (("NIfTI", "*.nii"),))).pack(side="left")
        frame = self._row(self.utility_tab)
        ttk.Button(frame, text="Create Sphere", command=self._run_sphere).pack(side="left")

        frame = self._row(self.utility_tab)
        self._file_picker(frame, self.tissue_var, "Tissue", (("NIfTI", "*.nii *.nii.gz"),))
        frame = self._row(self.utility_tab)
        ttk.Label(frame, text="Center").pack(side="left")
        ttk.Entry(frame, textvariable=self.center_var, width=32).pack(side="left", padx=4)
        ttk.Label(frame, text="Depth mm").pack(side="left")
        ttk.Entry(frame, textvariable=self.depth_var, width=8).pack(side="left", padx=4)
        frame = self._row(self.utility_tab)
        ttk.Label(frame, text="Output txt").pack(side="left")
        ttk.Entry(frame, textvariable=self.deep_out_var).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(frame, text="Browse", command=lambda: self._pick_file(self.deep_out_var, (("Text", "*.txt"),))).pack(side="left")
        frame = self._row(self.utility_tab)
        ttk.Button(frame, text="Compute Deep Target", command=self._run_deep).pack(side="left")

    def _build_preprocess_tab(self) -> None:
        self.em_func_var = tk.StringVar()
        self.em_out_var = tk.StringVar()
        self.em_rp_var = tk.StringVar()
        self.em_ref_var = tk.StringVar(value="0")
        self.em_iters_var = tk.StringVar(value="5,2,1")
        self.em_pipeline_var = tk.StringVar(value="translation,rigid")

        self.st_func_var = tk.StringVar()
        self.st_out_var = tk.StringVar()
        self.st_tr_var = tk.StringVar(value="2.0")
        self.st_order_var = tk.StringVar()
        self.st_ref_var = tk.StringVar(value="1")

        self.def_source_var = tk.StringVar()
        self.def_field_var = tk.StringVar()
        self.def_out_var = tk.StringVar()
        self.def_order_var = tk.StringVar(value="1")

        self.sm_func_var = tk.StringVar()
        self.sm_out_var = tk.StringVar()
        self.sm_fwhm_var = tk.StringVar(value="4.0")

        self.co_moving_var = tk.StringVar()
        self.co_static_var = tk.StringVar()
        self.co_out_var = tk.StringVar()
        self.co_affine_var = tk.StringVar()
        self.co_volume_var = tk.StringVar(value="0")

        frame = self._row(self.preprocess_tab)
        self._file_picker(frame, self.em_func_var, "Motion fMRI", (("NIfTI", "*.nii *.nii.gz"),))
        frame = self._row(self.preprocess_tab)
        ttk.Label(frame, text="Corrected").pack(side="left")
        ttk.Entry(frame, textvariable=self.em_out_var).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(frame, text="Browse", command=lambda: self._pick_file(self.em_out_var, (("NIfTI", "*.nii"),))).pack(side="left")
        ttk.Label(frame, text="RP").pack(side="left", padx=8)
        ttk.Entry(frame, textvariable=self.em_rp_var).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(frame, text="Browse", command=lambda: self._pick_file(self.em_rp_var, (("Text", "*.txt"),))).pack(side="left")
        frame = self._row(self.preprocess_tab)
        ttk.Label(frame, text="Ref vol").pack(side="left")
        ttk.Entry(frame, textvariable=self.em_ref_var, width=8).pack(side="left", padx=4)
        ttk.Label(frame, text="Levels").pack(side="left")
        ttk.Entry(frame, textvariable=self.em_iters_var, width=14).pack(side="left", padx=4)
        ttk.Label(frame, text="Pipeline").pack(side="left")
        ttk.Entry(frame, textvariable=self.em_pipeline_var, width=22).pack(side="left", padx=4)
        ttk.Button(frame, text="Estimate Motion", command=self._run_estimate_motion).pack(side="left", padx=8)

        frame = self._row(self.preprocess_tab)
        self._file_picker(frame, self.st_func_var, "Slice fMRI", (("NIfTI", "*.nii *.nii.gz"),))
        frame = self._row(self.preprocess_tab)
        ttk.Label(frame, text="Output").pack(side="left")
        ttk.Entry(frame, textvariable=self.st_out_var).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(frame, text="Browse", command=lambda: self._pick_file(self.st_out_var, (("NIfTI", "*.nii"),))).pack(side="left")
        ttk.Label(frame, text="TR").pack(side="left", padx=8)
        ttk.Entry(frame, textvariable=self.st_tr_var, width=8).pack(side="left")
        ttk.Label(frame, text="Order").pack(side="left", padx=8)
        ttk.Entry(frame, textvariable=self.st_order_var, width=30).pack(side="left")
        ttk.Label(frame, text="Ref").pack(side="left", padx=8)
        ttk.Entry(frame, textvariable=self.st_ref_var, width=8).pack(side="left")
        frame = self._row(self.preprocess_tab)
        ttk.Button(frame, text="Slice Timing", command=self._run_slice_timing).pack(side="left")

        frame = self._row(self.preprocess_tab)
        self._file_picker(frame, self.def_source_var, "Source", (("NIfTI", "*.nii *.nii.gz"),))
        frame = self._row(self.preprocess_tab)
        self._file_picker(frame, self.def_field_var, "Def Field", (("NIfTI", "*.nii *.nii.gz"),))
        frame = self._row(self.preprocess_tab)
        ttk.Label(frame, text="Output").pack(side="left")
        ttk.Entry(frame, textvariable=self.def_out_var).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(frame, text="Browse", command=lambda: self._pick_file(self.def_out_var, (("NIfTI", "*.nii"),))).pack(side="left")
        ttk.Label(frame, text="Order").pack(side="left", padx=8)
        ttk.Entry(frame, textvariable=self.def_order_var, width=6).pack(side="left")
        frame = self._row(self.preprocess_tab)
        ttk.Button(frame, text="Apply Deformation", command=self._run_deform).pack(side="left")

        frame = self._row(self.preprocess_tab)
        self._file_picker(frame, self.sm_func_var, "Smooth", (("NIfTI", "*.nii *.nii.gz"),))
        frame = self._row(self.preprocess_tab)
        ttk.Label(frame, text="Output").pack(side="left")
        ttk.Entry(frame, textvariable=self.sm_out_var).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(frame, text="Browse", command=lambda: self._pick_file(self.sm_out_var, (("NIfTI", "*.nii"),))).pack(side="left")
        ttk.Label(frame, text="FWHM").pack(side="left", padx=8)
        ttk.Entry(frame, textvariable=self.sm_fwhm_var, width=8).pack(side="left")
        frame = self._row(self.preprocess_tab)
        ttk.Button(frame, text="Smooth", command=self._run_smooth).pack(side="left")

        frame = self._row(self.preprocess_tab)
        self._file_picker(frame, self.co_moving_var, "Coreg Moving", (("NIfTI", "*.nii *.nii.gz"),))
        frame = self._row(self.preprocess_tab)
        self._file_picker(frame, self.co_static_var, "Coreg Static", (("NIfTI", "*.nii *.nii.gz"),))
        frame = self._row(self.preprocess_tab)
        ttk.Label(frame, text="Output").pack(side="left")
        ttk.Entry(frame, textvariable=self.co_out_var).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(frame, text="Browse", command=lambda: self._pick_file(self.co_out_var, (("NIfTI", "*.nii"),))).pack(side="left")
        ttk.Label(frame, text="Affine").pack(side="left", padx=8)
        ttk.Entry(frame, textvariable=self.co_affine_var).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(frame, text="Browse", command=lambda: self._pick_file(self.co_affine_var, (("Text", "*.txt"),))).pack(side="left")
        ttk.Label(frame, text="Vol").pack(side="left", padx=8)
        ttk.Entry(frame, textvariable=self.co_volume_var, width=6).pack(side="left")
        frame = self._row(self.preprocess_tab)
        ttk.Button(frame, text="Coregister", command=self._run_coregister).pack(side="left")

    def _append_log(self, text: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _poll_queue(self) -> None:
        while True:
            try:
                kind, text = self.queue.get_nowait()
            except queue.Empty:
                break
            if kind == "log":
                self._append_log(text)
            elif kind == "done":
                self._append_log(text)
            elif kind == "error":
                self._append_log(f"ERROR: {text}")
                messagebox.showerror("Error", text)
        self.after(100, self._poll_queue)

    def _run_worker(self, fn, *args) -> None:
        def worker() -> None:
            try:
                result = fn(*args)
                self.queue.put(("done", str(result)))
            except Exception as exc:  # noqa: BLE001 - shown to the user
                self.queue.put(("error", str(exc)))

        threading.Thread(target=worker, daemon=True).start()

    def _run_fc(self) -> None:
        try:
            tr = float(self.tr_var.get())
            low = float(self.low_var.get())
            high = float(self.high_var.get())
        except ValueError as exc:
            messagebox.showerror("Invalid settings", str(exc))
            return
        self._run_worker(
            lambda: seed_based_fc(
                self.func_var.get(),
                self.seed_var.get(),
                self.mask_var.get(),
                self.tms_out_var.get(),
                subject=self.subject_var.get(),
                z_score=self.zscore_var.get(),
            ),
        )

    def _run_target(self) -> None:
        fc_path = Path(self.tms_out_var.get()) / self.subject_var.get() / "SeedFCinROI.nii"
        if not fc_path.exists():
            messagebox.showwarning("Missing FC map", "Run Seed FC first or choose an output that contains SeedFCinROI.nii")
            return
        self._run_worker(
            lambda: target_site(
                fc_path,
                self.tms_out_var.get(),
                subject=self.subject_var.get(),
            ),
        )

    def _run_t1_target(self) -> None:
        def task() -> str:
            result = generate_t1_target(
                self.t1_image_var.get(),
                self.t1_target_var.get(),
                self.t1_output_var.get(),
                deformation_field=self.t1_deformation_var.get() or None,
            )
            return str(result["output_path"])

        self._run_worker(task)

    def _run_alff(self) -> None:
        try:
            tr = float(self.wm_tr_var.get())
            low = float(self.wm_low_var.get())
            high = float(self.wm_high_var.get())
        except ValueError as exc:
            messagebox.showerror("Invalid settings", str(exc))
            return
        self._run_worker(
            lambda: compute_alff(
                self.wm_func_var.get(),
                self.wm_mask_var.get(),
                self.wm_out_var.get(),
                tr=tr,
                low_cutoff=low,
                high_cutoff=high,
            ),
        )

    def _run_sphere(self) -> None:
        try:
            center = [float(x) for x in self.center_var.get().replace(",", " ").split()]
            if len(center) != 3:
                raise ValueError("Enter three MNI coordinates")
            radius = float(self.radius_var.get())
        except ValueError as exc:
            messagebox.showerror("Invalid settings", str(exc))
            return
        self._run_worker(lambda: sphere_roi(center, radius, self.ref_var.get(), self.sphere_out_var.get()))

    def _run_deep(self) -> None:
        try:
            center = [float(x) for x in self.center_var.get().replace(",", " ").split()]
            if len(center) != 3:
                raise ValueError("Enter three MNI coordinates")
            depth = float(self.depth_var.get())
        except ValueError as exc:
            messagebox.showerror("Invalid settings", str(exc))
            return
        self._run_worker(lambda: deep_target(self.tissue_var.get(), center, depth_mm=depth, out_path=self.deep_out_var.get()))

    def _run_estimate_motion(self) -> None:
        try:
            ref = int(self.em_ref_var.get())
            iters = tuple(int(x) for x in self.em_iters_var.get().replace(" ", "").split(",") if x)
            pipeline = tuple(x for x in self.em_pipeline_var.get().replace(" ", "").split(",") if x)
        except ValueError as exc:
            messagebox.showerror("Invalid settings", str(exc))
            return

        def task() -> str:
            img, data = load_volume(self.em_func_var.get())
            corrected, rp = estimate_motion_parameters(
                data,
                img.affine,
                reference_volume=ref,
                pipeline=pipeline,
                level_iters=iters,
                optimizer_options={"maxiter": 20},
            )
            save_volume(corrected, img, self.em_out_var.get())
            np.savetxt(self.em_rp_var.get(), rp, fmt="%.10f")
            return self.em_out_var.get()

        self._run_worker(task)

    def _run_slice_timing(self) -> None:
        try:
            tr = float(self.st_tr_var.get())
            order = [int(x) for x in self.st_order_var.get().replace(";", ",").replace(" ", ",").split(",") if x]
            ref = int(self.st_ref_var.get())
        except ValueError as exc:
            messagebox.showerror("Invalid settings", str(exc))
            return

        def task() -> str:
            img, data = load_volume(self.st_func_var.get())
            corrected = slice_timing_correct_volume(data, tr, order, ref)
            save_volume(corrected, img, self.st_out_var.get())
            return self.st_out_var.get()

        self._run_worker(task)

    def _run_deform(self) -> None:
        try:
            order = int(self.def_order_var.get())
        except ValueError as exc:
            messagebox.showerror("Invalid settings", str(exc))
            return
        self._run_worker(
            lambda: apply_deformation(
                self.def_source_var.get(),
                self.def_field_var.get(),
                self.def_out_var.get(),
                order=order,
            )
        )

    def _run_smooth(self) -> None:
        try:
            fwhm = float(self.sm_fwhm_var.get())
        except ValueError as exc:
            messagebox.showerror("Invalid settings", str(exc))
            return

        def task() -> str:
            img, data = load_volume(self.sm_func_var.get())
            save_volume(smooth_volume(data, fwhm, img.affine), img, self.sm_out_var.get())
            return self.sm_out_var.get()

        self._run_worker(task)

    def _run_coregister(self) -> None:
        try:
            volume = int(self.co_volume_var.get())
        except ValueError as exc:
            messagebox.showerror("Invalid settings", str(exc))
            return

        def task() -> str:
            moving_img, moving_data = load_volume(self.co_moving_var.get())
            static_img, static_data = load_volume(self.co_static_var.get())
            if moving_data.ndim == 4:
                moving_data = moving_data[..., volume]
            if static_data.ndim == 4:
                static_data = static_data[..., volume]
            resampled, affine = coregister_images(
                moving_data,
                static_data,
                moving_affine=moving_img.affine,
                static_affine=static_img.affine,
                pipeline=("translation", "rigid"),
                level_iters=(5, 2, 1),
                optimizer_options={"maxiter": 10},
            )
            save_volume(resampled, static_img, self.co_out_var.get())
            np.savetxt(self.co_affine_var.get(), affine, fmt="%.10f")
            return self.co_out_var.get()

        self._run_worker(task)


def launch_gui() -> int:
    """Launch the Tkinter desktop interface."""

    app = ToolboxApp()
    app.mainloop()
    return 0


__all__ = ["ToolboxApp", "launch_gui"]
