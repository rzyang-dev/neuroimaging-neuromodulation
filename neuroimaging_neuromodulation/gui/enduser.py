"""End-user desktop application for the neuroimaging toolbox."""

from __future__ import annotations

import queue
import subprocess
import sys
import threading
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from ..pipeline.run import run_pipeline


def build_config(
    *,
    subject: str,
    output_dir: str | Path,
    functional: str | Path | None,
    seed: str | Path,
    mask: str | Path,
    t1: str | Path | None = None,
    input_type: str = "nifti",
    tr: float = 2.0,
    low_cutoff: float = 0.01,
    high_cutoff: float = 0.1,
    estimate_motion: bool = True,
    filter_data: bool = False,
    generate_target: bool = True,
    generate_t1_target: bool = False,
    homotopic_fc: bool = False,
    fc_asymmetry: bool = False,
    target_image: str | Path | None = None,
    report: bool = True,
) -> dict[str, object]:
    """Build a pipeline config from end-user form values."""

    config: dict[str, object] = {
        "subject": subject,
        "output_dir": str(output_dir),
        "seed": str(seed),
        "mask": str(mask),
        "tr": float(tr),
        "low_cutoff": float(low_cutoff),
        "high_cutoff": float(high_cutoff),
        "estimate_motion": bool(estimate_motion),
        "filter": bool(filter_data),
        "target": bool(generate_target),
        "report": bool(report),
    }
    if input_type == "dicom":
        config["dicom"] = {"functional": str(functional)}
        if t1:
            config["dicom"]["structural"] = str(t1)
    else:
        config["functional"] = str(functional)
        if t1:
            config["t1"] = str(t1)
    if generate_t1_target:
        if not t1:
            raise ValueError("T1 image is required to generate a T1-space target")
        if not target_image:
            raise ValueError("Target image is required to generate a T1-space target")
        config["t1_target"] = {
            "target": str(target_image),
            "deformation": None,
            "output": str(Path(output_dir) / subject / "IndiTarget_T1Sp.nii"),
            "spm_dir": None,
            "timeout": 1800,
        }
    wm_analysis: dict[str, object] = {}
    if homotopic_fc:
        wm_analysis["conn_homo"] = {"mask": str(mask)}
    if fc_asymmetry:
        wm_analysis["fc_asym"] = {"mask": str(mask)}
    if wm_analysis:
        config["wm_analysis"] = wm_analysis
    return config


class EndUserApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Neuroimaging Neuromodulation Workbench")
        self.geometry("980x720")
        self.minsize(820, 620)
        self.queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self.last_report: Path | None = None
        self._configure_style()
        self._build_ui()
        self.after(100, self._poll_queue)

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Title.TLabel", font=("Helvetica", 18, "bold"))
        style.configure("Section.TLabel", font=("Helvetica", 12, "bold"))
        style.configure("Hint.TLabel", foreground="#55606a")
        style.configure("Run.TButton", font=("Helvetica", 13, "bold"), padding=10)

    def _build_ui(self) -> None:
        header = ttk.Frame(self, padding=(16, 12))
        header.pack(fill="x")
        ttk.Label(header, text="Neuroimaging Neuromodulation Workbench", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Select your data, choose settings, then press Run. You do not need to use commands.",
            style="Hint.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=8)
        self.data_page = ttk.Frame(self.notebook, padding=14)
        self.settings_page = ttk.Frame(self.notebook, padding=14)
        self.run_page = ttk.Frame(self.notebook, padding=14)
        self.notebook.add(self.data_page, text="1. Data")
        self.notebook.add(self.settings_page, text="2. Settings")
        self.notebook.add(self.run_page, text="3. Run and Results")
        self._build_data_page()
        self._build_settings_page()
        self._build_run_page()

    def _row(self, parent: tk.Widget) -> ttk.Frame:
        frame = ttk.Frame(parent)
        frame.pack(fill="x", pady=6)
        return frame

    def _label_entry(self, parent: tk.Widget, text: str, variable: tk.StringVar, width: int = 62) -> None:
        ttk.Label(parent, text=text, width=24).pack(side="left")
        ttk.Entry(parent, textvariable=variable, width=width).pack(side="left", fill="x", expand=True, padx=6)

    def _file_picker(
        self,
        parent: tk.Widget,
        label: str,
        variable: tk.StringVar,
        filetypes: tuple[tuple[str, str], ...],
        *,
        directory: bool = False,
    ) -> ttk.Button:
        ttk.Label(parent, text=label, width=24).pack(side="left")
        ttk.Entry(parent, textvariable=variable).pack(side="left", fill="x", expand=True, padx=6)
        command = lambda: self._pick_directory(variable) if directory else self._pick_file(variable, filetypes)
        button = ttk.Button(parent, text="Browse", command=command)
        button.pack(side="left")
        return button

    def _pick_file(self, variable: tk.StringVar, filetypes: tuple[tuple[str, str], ...]) -> None:
        path = filedialog.askopenfilename(filetypes=filetypes)
        if path:
            variable.set(path)

    def _pick_directory(self, variable: tk.StringVar) -> None:
        path = filedialog.askdirectory()
        if path:
            variable.set(path)

    def _build_data_page(self) -> None:
        self.subject_var = tk.StringVar(value="subject")
        self.functional_type_var = tk.StringVar(value="nifti")
        self.functional_var = tk.StringVar()
        self.seed_var = tk.StringVar()
        self.mask_var = tk.StringVar()
        self.t1_var = tk.StringVar()
        self.target_image_var = tk.StringVar()

        frame = self._row(self.data_page)
        self._label_entry(frame, "Subject ID", self.subject_var)

        frame = self._row(self.data_page)
        ttk.Label(frame, text="Functional data type", width=24).pack(side="left")
        ttk.Radiobutton(frame, text="NIfTI file", variable=self.functional_type_var, value="nifti", command=self._update_functional_browse).pack(side="left")
        ttk.Radiobutton(frame, text="DICOM folder", variable=self.functional_type_var, value="dicom", command=self._update_functional_browse).pack(side="left", padx=8)

        frame = self._row(self.data_page)
        self.functional_browse_button = self._file_picker(
            frame,
            "Functional data",
            self.functional_var,
            (("NIfTI", "*.nii *.nii.gz"),),
            directory=False,
        )

        frame = self._row(self.data_page)
        self._file_picker(frame, "Seed image", self.seed_var, (("NIfTI", "*.nii *.nii.gz"),))

        frame = self._row(self.data_page)
        self._file_picker(frame, "Analysis mask", self.mask_var, (("NIfTI", "*.nii *.nii.gz"),))

        frame = self._row(self.data_page)
        self._file_picker(frame, "T1 image (optional)", self.t1_var, (("NIfTI", "*.nii *.nii.gz"),), directory=False)

        frame = self._row(self.data_page)
        self._file_picker(frame, "Target ROI (MNI)", self.target_image_var, (("NIfTI", "*.nii *.nii.gz"),), directory=False)

        ttk.Label(
            self.data_page,
            text="Tip: Seed and mask images should already be in MNI space or in the same space as your functional data.",
            style="Hint.TLabel",
        ).pack(anchor="w", pady=(12, 0))

    def _update_functional_browse(self) -> None:
        if not hasattr(self, "functional_browse_button"):
            return
        if self.functional_type_var.get() == "dicom":
            self.functional_browse_button.configure(
                command=lambda: self._pick_directory(self.functional_var)
            )
        else:
            self.functional_browse_button.configure(
                command=lambda: self._pick_file(
                    self.functional_var,
                    (("NIfTI", "*.nii *.nii.gz"),),
                )
            )

    def _build_settings_page(self) -> None:
        self.output_var = tk.StringVar(value=str(Path.home() / "NeuroModulationResults"))
        self.tr_var = tk.StringVar(value="2.0")
        self.low_var = tk.StringVar(value="0.01")
        self.high_var = tk.StringVar(value="0.1")
        self.motion_var = tk.BooleanVar(value=True)
        self.filter_var = tk.BooleanVar(value=False)
        self.target_var = tk.BooleanVar(value=True)
        self.t1_target_var = tk.BooleanVar(value=False)
        self.homotopic_fc_var = tk.BooleanVar(value=False)
        self.fc_asymmetry_var = tk.BooleanVar(value=False)
        self.report_var = tk.BooleanVar(value=True)

        frame = self._row(self.settings_page)
        ttk.Label(frame, text="Output folder", width=24).pack(side="left")
        ttk.Entry(frame, textvariable=self.output_var).pack(side="left", fill="x", expand=True, padx=6)
        ttk.Button(frame, text="Browse", command=lambda: self._pick_directory(self.output_var)).pack(side="left")

        frame = self._row(self.settings_page)
        self._label_entry(frame, "Repetition time (TR)", self.tr_var, width=14)

        frame = self._row(self.settings_page)
        ttk.Label(frame, text="Frequency band", width=24).pack(side="left")
        ttk.Entry(frame, textvariable=self.low_var, width=10).pack(side="left", padx=4)
        ttk.Label(frame, text="to").pack(side="left")
        ttk.Entry(frame, textvariable=self.high_var, width=10).pack(side="left", padx=4)

        frame = self._row(self.settings_page)
        ttk.Checkbutton(frame, text="Estimate head motion", variable=self.motion_var).pack(anchor="w", padx=24)

        frame = self._row(self.settings_page)
        ttk.Checkbutton(frame, text="Band-pass filter", variable=self.filter_var).pack(anchor="w", padx=24)

        frame = self._row(self.settings_page)
        ttk.Checkbutton(frame, text="Generate TMS target candidates", variable=self.target_var).pack(anchor="w", padx=24)

        frame = self._row(self.settings_page)
        ttk.Checkbutton(frame, text="Generate T1-space target image", variable=self.t1_target_var).pack(anchor="w", padx=24)

        frame = self._row(self.settings_page)
        ttk.Checkbutton(frame, text="Compute homotopic FC", variable=self.homotopic_fc_var).pack(anchor="w", padx=24)

        frame = self._row(self.settings_page)
        ttk.Checkbutton(frame, text="Compute FC asymmetry", variable=self.fc_asymmetry_var).pack(anchor="w", padx=24)

        frame = self._row(self.settings_page)
        ttk.Checkbutton(frame, text="Create an HTML report", variable=self.report_var).pack(anchor="w", padx=24)

    def _build_run_page(self) -> None:
        self.status_var = tk.StringVar(value="Ready")
        frame = self._row(self.run_page)
        self.run_button = ttk.Button(frame, text="Run Analysis", style="Run.TButton", command=self._run_analysis)
        self.run_button.pack(side="left")

        self.progress = ttk.Progressbar(frame, mode="indeterminate", length=320)
        self.progress.pack(side="left", padx=16, fill="x", expand=True)

        frame = self._row(self.run_page)
        ttk.Label(frame, textvariable=self.status_var, style="Section.TLabel").pack(anchor="w")

        log_frame = ttk.LabelFrame(self.run_page, text="Progress log", padding=8)
        log_frame.pack(fill="both", expand=True, pady=(8, 0))
        self.log_text = tk.Text(log_frame, height=12, wrap="word", state="disabled")
        scroll = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.log_text.pack(side="left", fill="both", expand=True)

        frame = self._row(self.run_page)
        self.open_report_button = ttk.Button(frame, text="Open Report", state="disabled", command=self._open_report)
        self.open_report_button.pack(side="left")
        self.open_folder_button = ttk.Button(frame, text="Open Output Folder", state="disabled", command=self._open_output_folder)
        self.open_folder_button.pack(side="left", padx=8)

    def _append_log(self, text: str) -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _validate_form(self) -> dict[str, object] | None:
        subject = self.subject_var.get().strip()
        if not subject:
            messagebox.showerror("Missing subject ID", "Enter a subject ID first.")
            return None
        functional = self.functional_var.get().strip()
        if not functional or not Path(functional).exists():
            messagebox.showerror("Functional data missing", "Select a functional NIfTI file or DICOM folder.")
            return None
        seed = self.seed_var.get().strip()
        mask = self.mask_var.get().strip()
        if not seed or not Path(seed).exists():
            messagebox.showerror("Seed image missing", "Select a seed image.")
            return None
        if not mask or not Path(mask).exists():
            messagebox.showerror("Mask image missing", "Select an analysis mask.")
            return None
        try:
            tr = float(self.tr_var.get())
            low = float(self.low_var.get())
            high = float(self.high_var.get())
            if tr <= 0 or low < 0 or high <= low:
                raise ValueError("TR must be positive and the frequency band must be valid.")
        except ValueError as exc:
            messagebox.showerror("Invalid settings", str(exc))
            return None
        t1 = self.t1_var.get().strip() or None
        if t1 and not Path(t1).exists():
            messagebox.showerror("T1 image missing", "The selected T1 image does not exist.")
            return None
        target_image = self.target_image_var.get().strip() or None
        if self.t1_target_var.get():
            if not t1:
                messagebox.showerror("T1 image missing", "Select a T1 image for T1-space target generation.")
                return None
            if not target_image or not Path(target_image).exists():
                messagebox.showerror("Target image missing", "Select an MNI target ROI image.")
                return None
        config = build_config(
            subject=subject,
            output_dir=self.output_var.get().strip() or str(Path.home() / "NeuroModulationResults"),
            functional=functional,
            seed=seed,
            mask=mask,
            t1=t1,
            input_type=self.functional_type_var.get(),
            tr=tr,
            low_cutoff=low,
            high_cutoff=high,
            estimate_motion=self.motion_var.get(),
            filter_data=self.filter_var.get(),
            generate_target=self.target_var.get(),
            generate_t1_target=self.t1_target_var.get(),
            homotopic_fc=self.homotopic_fc_var.get(),
            fc_asymmetry=self.fc_asymmetry_var.get(),
            target_image=target_image,
            report=self.report_var.get(),
        )
        return config

    def _run_analysis(self) -> None:
        config = self._validate_form()
        if config is None:
            return
        self.run_button.configure(state="disabled")
        self.open_report_button.configure(state="disabled")
        self.open_folder_button.configure(state="disabled")
        self.status_var.set("Running...")
        self.progress.start(12)
        self._append_log("Starting analysis...")
        threading.Thread(target=self._worker, args=(config,), daemon=True).start()

    def _worker(self, config: dict[str, object]) -> None:
        try:
            result = run_pipeline(config)
            self.queue.put(("done", result))
        except Exception as exc:  # noqa: BLE001 - shown to end users
            self.queue.put(("error", str(exc)))

    def _poll_queue(self) -> None:
        try:
            kind, payload = self.queue.get_nowait()
        except queue.Empty:
            self.after(100, self._poll_queue)
            return
        if kind == "done":
            self.progress.stop()
            self.run_button.configure(state="normal")
            self.open_folder_button.configure(state="normal")
            self.status_var.set("Complete")
            result = payload
            report = result.get("report")
            self.last_report = Path(report) if report else None
            if self.last_report and self.last_report.exists():
                self.open_report_button.configure(state="normal")
                self._append_log(f"Report: {self.last_report}")
                if self.report_var.get():
                    webbrowser.open(self.last_report.as_uri())
            else:
                self._append_log("Analysis completed without an HTML report.")
            self._append_log(f"Output folder: {result.get('output_dir')}")
        elif kind == "error":
            self.progress.stop()
            self.run_button.configure(state="normal")
            self.status_var.set("Error")
            self._append_log(f"ERROR: {payload}")
            messagebox.showerror("Analysis failed", str(payload))
        self.after(100, self._poll_queue)

    def _open_report(self) -> None:
        if self.last_report and self.last_report.exists():
            webbrowser.open(self.last_report.as_uri())

    def _open_output_folder(self) -> None:
        output = Path(self.output_var.get().strip() or str(Path.home() / "NeuroModulationResults"))
        output.mkdir(parents=True, exist_ok=True)
        if sys.platform.startswith("darwin"):
            subprocess.Popen(["open", str(output)])
        elif sys.platform.startswith("win"):
            subprocess.Popen(["explorer", str(output)])
        else:
            subprocess.Popen(["xdg-open", str(output)])


def main() -> int:
    app = EndUserApp()
    app.mainloop()
    return 0


__all__ = ["EndUserApp", "build_config", "main"]
