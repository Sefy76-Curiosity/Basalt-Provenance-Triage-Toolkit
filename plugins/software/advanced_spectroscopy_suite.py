"""
ADVANCED SPECTROSCOPY SUITE v1.4 – Batch, Pass/Fail, Diagnostics
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Author: DeepSeek
"""

PLUGIN_INFO = {
    "id": "advanced_spectroscopy_suite_compact",
    "name": "Advanced Spectroscopy Suite",
    "category": "software",
    "field": "Spectroscopy",
    "icon": "⚡",
    "version": "1.5.0",
    "author": "Sefy Levy & DeepSeek",
    "description": "Hyper · Wizard · Apply · Batch · Kinetics · Diagnostics",
    "requires": ["numpy", "pandas", "scipy", "matplotlib", "joblib"],
    "optional": ["scikit-learn", "plotly", "spectral"],
    "window_size": "850x600"
}

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import pandas as pd
import threading
import queue
import os
import json
import time
from datetime import datetime
from pathlib import Path
import importlib.util
import sys
import warnings
warnings.filterwarnings("ignore")

# ============================================================================
# DEPENDENCY CHECK
# ============================================================================
REQUIRED_MODULES = ["numpy", "pandas", "scipy", "matplotlib", "joblib"]
missing = []
for mod in REQUIRED_MODULES:
    if importlib.util.find_spec(mod) is None:
        missing.append(mod)
if missing:
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(
        "Missing Dependencies",
        f"The following required modules are not installed:\n\n{', '.join(missing)}\n\n"
        f"Please install them using:\npip install {' '.join(missing)}"
    )
    root.destroy()
    sys.exit(1)

# ============================================================================
# OPTIONAL IMPORTS
# ============================================================================
try:
    import joblib
    HAS_JOBLIB = True
except ImportError:
    HAS_JOBLIB = False

try:
    from scipy import signal, ndimage, stats, optimize, interpolate
    from scipy.signal import savgol_filter, find_peaks
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    from sklearn.cross_decomposition import PLSRegression
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import cross_val_predict
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

try:
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    from matplotlib.figure import Figure
    from matplotlib.widgets import RectangleSelector
    from mpl_toolkits.mplot3d import Axes3D
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import plotly.offline as pyo
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

try:
    import spectral.io.envi as envi
    HAS_SPECTRAL = True
except ImportError:
    HAS_SPECTRAL = False

# ============================================================================
# IMPORT ORIGINAL SUITE ENGINES (with fallback stubs)
# ============================================================================
try:
    from spectroscopy_analysis_suite import LibrarySearchEngine, PreprocessingEngine, CalibrationEngine
    HAS_ORIGINAL = True
except ImportError:
    HAS_ORIGINAL = False
    # Fallback stubs (minimal functionality)
    class LibrarySearchEngine:
        @staticmethod
        def dot_product(ref, target):
            return np.dot(ref, target) / (np.linalg.norm(ref)*np.linalg.norm(target) + 1e-10)
        @staticmethod
        def align_wavelengths(ref_wl, ref_int, target_wl):
            f = interpolate.interp1d(target_wl, ref_int, bounds_error=False, fill_value=0)
            return f(ref_wl)
    class PreprocessingEngine:
        @staticmethod
        def snv(x):
            return (x - np.mean(x)) / (np.std(x) + 1e-10)
        @staticmethod
        def savgol(x, window, order):
            from scipy.signal import savgol_filter
            return savgol_filter(x, window, order)
    class CalibrationEngine:
        @staticmethod
        def pls(X, y, n_comp, cv):
            return {'rmsec':0, 'rmsecv':0, 'r2_cal':0, 'r2_cv':0, 'model':None,
                    'scaler_X':None, 'scaler_y':None}
        @staticmethod
        def pcr(X, y, n_comp, cv):
            return {'rmsec':0, 'rmsecv':0, 'r2_cal':0, 'r2_cv':0, 'model':None,
                    'scaler_X':None, 'scaler_y':None}

# ============================================================================
# COLOR PALETTE
# ============================================================================
C_HEADER   = "#1A1A2E"
C_ACCENT   = "#E94560"
C_ACCENT2  = "#0F3460"
C_LIGHT    = "#F8F9FA"
C_BORDER   = "#CED4DA"
C_STATUS   = "#28A745"
C_WARN     = "#DC3545"

# ============================================================================
# THREAD‑SAFE UI QUEUE
# ============================================================================
class ThreadSafeUI:
    def __init__(self, root):
        self.root = root
        self.queue = queue.Queue()
        self._poll()

    def _poll(self):
        try:
            while True:
                callback = self.queue.get_nowait()
                callback()
        except queue.Empty:
            pass
        finally:
            self.root.after(50, self._poll)

    def schedule(self, callback):
        self.queue.put(callback)

# ============================================================================
# BASE TAB (compact)
# ============================================================================
class AdvancedTab:
    def __init__(self, parent, app, ui_queue, tab_name):
        self.parent = parent
        self.app = app
        self.ui_queue = ui_queue
        self.tab_name = tab_name
        self.frame = ttk.Frame(parent)
        self.status_label = tk.Label(self.frame, text="", font=("Arial", 8), bg="white", fg=C_STATUS)
        self.status_label.pack(fill=tk.X, padx=2, pady=1)
        self.content_frame = tk.Frame(self.frame, bg="white")
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

# ============================================================================
# HYPERSPECTRAL DATA HANDLER
# ============================================================================
class HyperspectralData:
    def __init__(self):
        self.data = None
        self.wavelengths = None
        self.metadata = {}

    def load_envi(self, image_file, header_file):
        if HAS_SPECTRAL:
            try:
                img = envi.open(header_file, image_file)
                self.data = img.load()
                self.wavelengths = np.array([float(w) for w in img.metadata.get('wavelength', range(img.nbands))])
                self.metadata = img.metadata
                return True
            except Exception as e:
                print(f"ENVI load error: {e}")
                return False
        else:
            rows, cols, bands = 100, 100, 50
            self.data = np.random.rand(rows, cols, bands)
            self.wavelengths = np.linspace(400, 1000, bands)
            self.metadata = {"description": "Random demo cube (install spectral for real ENVI)"}
            return True

    def get_spectrum(self, row, col):
        if self.data is not None:
            return self.data[row, col, :]
        return None

    def get_roi_spectrum(self, rows, cols):
        if self.data is None:
            return None
        sub = self.data[rows, cols, :]
        return np.mean(sub, axis=(0,1))

# ============================================================================
# METHOD MANAGER
# ============================================================================
class MethodManager:
    def __init__(self, base_dir=None):
        self.base_dir = Path(base_dir or Path.home() / ".spectroscopy" / "methods")
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_method(self, name, model, scaler_X=None, scaler_y=None, metadata=None):
        if not HAS_JOBLIB:
            messagebox.showerror("Error", "joblib not installed. Cannot save method.")
            return None
        path = self.base_dir / f"{name}.joblib"
        data = {
            'model': model,
            'scaler_X': scaler_X,
            'scaler_y': scaler_y,
            'metadata': metadata or {}
        }
        joblib.dump(data, path)
        return str(path)

    def load_method(self, name):
        if not HAS_JOBLIB:
            return None
        path = self.base_dir / f"{name}.joblib"
        if path.exists():
            return joblib.load(path)
        return None

    def list_methods(self):
        if not HAS_JOBLIB:
            return []
        return [p.stem for p in self.base_dir.glob("*.joblib")]

# ============================================================================
# MAIN PLUGIN CLASS
# ============================================================================
class AdvancedSpectroscopySuite:
    def __init__(self, main_app):
        self.app = main_app
        self.window = None
        self.ui_queue = None
        self.tabs = {}
        self.method_manager = MethodManager()

    def show_interface(self):
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("⚡ Advanced Spectroscopy Suite (Compact)")
        self.window.geometry("850x600")
        self.window.minsize(800, 550)
        self.window.transient(self.app.root)

        self.ui_queue = ThreadSafeUI(self.window)
        self._build_ui()

        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        header = tk.Frame(self.window, bg=C_HEADER, height=35)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="⚡", font=("Arial", 16),
                bg=C_HEADER, fg="white").pack(side=tk.LEFT, padx=5)
        tk.Label(header, text="ADVANCED SPECTROSCOPY SUITE",
                font=("Arial", 11, "bold"), bg=C_HEADER, fg="white").pack(side=tk.LEFT)
        tk.Label(header, text="v1.4 · Compact · Batch · Pass/Fail · Diagnostics",
                font=("Arial", 8), bg=C_HEADER, fg=C_ACCENT).pack(side=tk.LEFT, padx=10)

        self.status_var = tk.StringVar(value="Ready")
        status_bar = tk.Label(self.window, textvariable=self.status_var, relief=tk.SUNKEN,
                              anchor=tk.W, bg=C_LIGHT, fg=C_HEADER, font=("Arial", 8))
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)

        self.tabs['hyperspectral'] = HyperspectralTab(notebook, self.app, self.ui_queue)
        notebook.add(self.tabs['hyperspectral'].frame, text=" Hyper ")

        self.tabs['wizard'] = WizardLauncherTab(notebook, self.app, self.ui_queue, self.method_manager)
        notebook.add(self.tabs['wizard'].frame, text=" Wizard ")

        self.tabs['apply'] = ApplyMethodTab(notebook, self.app, self.ui_queue, self.method_manager)
        notebook.add(self.tabs['apply'].frame, text=" Apply ")

        self.tabs['batch'] = BatchTab(notebook, self.app, self.ui_queue, self.method_manager)
        notebook.add(self.tabs['batch'].frame, text=" Batch ")

        self.tabs['kinetics'] = KineticsTab(notebook, self.app, self.ui_queue)
        notebook.add(self.tabs['kinetics'].frame, text=" Kinetics ")

    def _on_close(self):
        if self.window:
            self.window.destroy()
            self.window = None

# ============================================================================
# TAB 1: HYPERSPECTRAL VIEWER
# ============================================================================
class HyperspectralTab(AdvancedTab):
    def __init__(self, parent, app, ui_queue):
        super().__init__(parent, app, ui_queue, "Hyper")
        self.hs_data = HyperspectralData()
        self.roi_active = False
        self.roi_coords = None
        self._build_ui()

    def _build_ui(self):
        ctrl = tk.Frame(self.content_frame, bg="white", height=30)
        ctrl.pack(fill=tk.X)
        ctrl.pack_propagate(False)

        tk.Button(ctrl, text="Load ENVI", command=self._load, width=10).pack(side=tk.LEFT, padx=2)
        self.info_label = tk.Label(ctrl, text="No data", bg="white", font=("Arial", 7))
        self.info_label.pack(side=tk.LEFT, padx=5)

        tk.Label(ctrl, text="R:", bg="white", font=("Arial", 7)).pack(side=tk.LEFT, padx=(5,0))
        self.r_band = tk.Spinbox(ctrl, from_=0, to=0, width=3, state='readonly')
        self.r_band.pack(side=tk.LEFT)
        tk.Label(ctrl, text="G:", bg="white", font=("Arial", 7)).pack(side=tk.LEFT, padx=(2,0))
        self.g_band = tk.Spinbox(ctrl, from_=0, to=0, width=3, state='readonly')
        self.g_band.pack(side=tk.LEFT)
        tk.Label(ctrl, text="B:", bg="white", font=("Arial", 7)).pack(side=tk.LEFT, padx=(2,0))
        self.b_band = tk.Spinbox(ctrl, from_=0, to=0, width=3, state='readonly')
        self.b_band.pack(side=tk.LEFT)
        tk.Button(ctrl, text="RGB", command=self._update_rgb, width=4).pack(side=tk.LEFT, padx=2)

        self.roi_btn = tk.Button(ctrl, text="ROI", command=self._toggle_roi, width=4)
        self.roi_btn.pack(side=tk.LEFT, padx=2)

        paned = ttk.PanedWindow(self.content_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        left = tk.Frame(paned, bg="white")
        paned.add(left, weight=2)
        right = tk.Frame(paned, bg="white", width=200)
        paned.add(right, weight=1)

        if HAS_MPL:
            self.fig_left = Figure(figsize=(4,3), dpi=90)
            self.ax_img = self.fig_left.add_subplot(111)
            self.canvas_left = FigureCanvasTkAgg(self.fig_left, left)
            self.canvas_left.draw()
            self.canvas_left.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            self.roi_selector = RectangleSelector(self.ax_img, self._roi_callback,
                                                  useblit=True, button=[1], minspanx=5, minspany=5,
                                                  spancoords='pixels', interactive=True)
            self.roi_selector.set_active(False)

            self.fig_right = Figure(figsize=(3,3), dpi=90)
            self.ax_spec = self.fig_right.add_subplot(111)
            self.canvas_right = FigureCanvasTkAgg(self.fig_right, right)
            self.canvas_right.draw()
            self.canvas_right.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            self.canvas_left.mpl_connect('button_press_event', self._on_click)

    def _load(self):
        path_img = filedialog.askopenfilename(title="Select ENVI image", filetypes=[("ENVI", "*.img;*.dat"), ("All", "*.*")])
        if not path_img:
            return
        path_hdr = filedialog.askopenfilename(title="Select ENVI header", filetypes=[("ENVI", "*.hdr"), ("All", "*.*")])
        if not path_hdr:
            return
        self.status_label.config(text="Loading...")
        def worker():
            success = self.hs_data.load_envi(path_img, path_hdr)
            def update():
                if success:
                    rows, cols, bands = self.hs_data.data.shape
                    self.info_label.config(text=f"{rows}x{cols}, {bands}b")
                    self.r_band.config(to=bands-1)
                    self.g_band.config(to=bands-1)
                    self.b_band.config(to=bands-1)
                    self.r_band.delete(0, tk.END); self.r_band.insert(0, "0")
                    self.g_band.delete(0, tk.END); self.g_band.insert(0, str(bands//3))
                    self.b_band.delete(0, tk.END); self.b_band.insert(0, str(2*bands//3))
                    self._show_rgb()
                else:
                    messagebox.showerror("Error", "Failed to load ENVI cube")
                self.status_label.config(text="")
            self.ui_queue.schedule(update)
        threading.Thread(target=worker, daemon=True).start()

    def _show_rgb(self):
        if self.hs_data.data is None:
            return
        try:
            r = int(self.r_band.get())
            g = int(self.g_band.get())
            b = int(self.b_band.get())
            rgb = np.stack([self.hs_data.data[:,:,r],
                            self.hs_data.data[:,:,g],
                            self.hs_data.data[:,:,b]], axis=2)
            rgb = (rgb - rgb.min()) / (rgb.max() - rgb.min() + 1e-10)
            self.ax_img.clear()
            self.ax_img.imshow(rgb)
            self.ax_img.set_title("RGB", fontsize=8)
            self.canvas_left.draw()
        except Exception as e:
            print("RGB error:", e)

    def _update_rgb(self):
        self._show_rgb()

    def _toggle_roi(self):
        self.roi_active = not self.roi_active
        self.roi_selector.set_active(self.roi_active)
        self.roi_btn.config(relief=tk.SUNKEN if self.roi_active else tk.RAISED)

    def _roi_callback(self, eclick, erelease):
        x1, y1 = int(eclick.xdata), int(eclick.ydata)
        x2, y2 = int(erelease.xdata), int(erelease.ydata)
        x1, x2 = sorted([x1, x2])
        y1, y2 = sorted([y1, y2])
        self.roi_coords = (slice(y1, y2), slice(x1, x2))
        if self.hs_data.data is not None:
            spectrum = self.hs_data.get_roi_spectrum(self.roi_coords[0], self.roi_coords[1])
            self.ax_spec.clear()
            self.ax_spec.plot(self.hs_data.wavelengths, spectrum, lw=1)
            self.ax_spec.set_xlabel("Wavelength", fontsize=7)
            self.ax_spec.set_ylabel("Intensity", fontsize=7)
            self.ax_spec.set_title(f"ROI ({x2-x1}x{y2-y1})", fontsize=7)
            self.canvas_right.draw()

    def _on_click(self, event):
        if event.inaxes != self.ax_img or self.roi_active or self.hs_data.data is None:
            return
        x, y = int(event.xdata), int(event.ydata)
        if x < 0 or y < 0 or x >= self.hs_data.data.shape[1] or y >= self.hs_data.data.shape[0]:
            return
        spectrum = self.hs_data.get_spectrum(y, x)
        if spectrum is not None:
            self.ax_spec.clear()
            self.ax_spec.plot(self.hs_data.wavelengths, spectrum, lw=1)
            self.ax_spec.set_xlabel("Wavelength", fontsize=7)
            self.ax_spec.set_ylabel("Intensity", fontsize=7)
            self.ax_spec.set_title(f"Spectrum ({x},{y})", fontsize=7)
            self.canvas_right.draw()

# ============================================================================
# TAB 2: METHOD WIZARD LAUNCHER
# ============================================================================
class WizardLauncherTab(AdvancedTab):
    def __init__(self, parent, app, ui_queue, method_manager):
        super().__init__(parent, app, ui_queue, "Wizard")
        self.method_manager = method_manager
        self._build_ui()

    def _build_ui(self):
        tk.Label(self.content_frame, text="Method Wizard", font=("Arial", 12, "bold"),
                 bg="white").pack(pady=10)
        tk.Label(self.content_frame,
                text="Build PLS/PCR calibration models.\n"
                     "Select samples, preprocessing, model type,\n"
                     "validate, and save for later use.",
                bg="white", justify=tk.LEFT, font=("Arial", 8)).pack(pady=5)
        tk.Button(self.content_frame, text="Launch Wizard", command=self._launch,
                 bg=C_ACCENT, fg="white", width=15).pack(pady=10)

    def _launch(self):
        parent_window = self.parent.winfo_toplevel()
        wizard = MethodWizard(parent_window, self.app, self.method_manager)
        parent_window.wait_window(wizard)

# ============================================================================
# METHOD WIZARD DIALOG (with diagnostics)
# ============================================================================
class MethodWizard(tk.Toplevel):
    def __init__(self, parent, app, method_manager):
        super().__init__(parent)
        self.app = app
        self.method_manager = method_manager
        self.title("Method Wizard")
        self.geometry("600x500")
        self.transient(parent)
        self.grab_set()

        self.current_step = 0
        self.steps = ["Data", "Preproc", "Model", "Params", "Validate", "Save"]
        self.data = {}
        self.model_result = None

        self.header = tk.Label(self, text=self.steps[0], font=("Arial", 10, "bold"),
                               bg=C_HEADER, fg="white")
        self.header.pack(fill=tk.X)

        self.content = tk.Frame(self, bg="white")
        self.content.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.btn_frame = tk.Frame(self)
        self.btn_frame.pack(fill=tk.X, pady=5)
        self.back_btn = tk.Button(self.btn_frame, text="< Back", command=self._back, state=tk.DISABLED)
        self.back_btn.pack(side=tk.LEFT, padx=5)
        self.next_btn = tk.Button(self.btn_frame, text="Next >", command=self._next)
        self.next_btn.pack(side=tk.RIGHT, padx=5)
        self.cancel_btn = tk.Button(self.btn_frame, text="Cancel", command=self.destroy)
        self.cancel_btn.pack(side=tk.RIGHT, padx=5)

        self._build_step(0)

    def _build_step(self, step):
        for widget in self.content.winfo_children():
            widget.destroy()
        self.header.config(text=self.steps[step])

        if step == 0:
            tk.Label(self.content, text="Select samples (main table):", bg="white",
                     font=("Arial", 8)).pack(pady=5)
            self.sample_listbox = tk.Listbox(self.content, selectmode=tk.MULTIPLE, height=6)
            self.sample_listbox.pack(fill=tk.BOTH, expand=True, padx=5)
            if hasattr(self.app, 'data_hub'):
                samples = self.app.data_hub.get_all()
                for i, s in enumerate(samples):
                    self.sample_listbox.insert(tk.END, f"{i}: {s.get('Sample_ID', 'Unknown')}")
            # Restore previous selection if any
            if 'selected_indices' in self.data:
                for idx in self.data['selected_indices']:
                    self.sample_listbox.selection_set(idx)
            tk.Label(self.content, text="Concentration column:", bg="white",
                     font=("Arial", 8)).pack(pady=2)
            self.conc_col = tk.Entry(self.content, width=20)
            self.conc_col.pack()
            # Restore previous concentration column
            self.conc_col.insert(0, self.data.get('conc_col', 'Concentration'))

        elif step == 1:
            tk.Label(self.content, text="Preprocessing:", bg="white",
                     font=("Arial", 8)).pack(anchor=tk.W)
            self.snv_var = tk.BooleanVar(value=self.data.get('snv', False))
            tk.Checkbutton(self.content, text="SNV", variable=self.snv_var, bg="white").pack(anchor=tk.W)
            self.sg_var = tk.BooleanVar(value=self.data.get('savgol', False))
            tk.Checkbutton(self.content, text="Savitzky-Golay", variable=self.sg_var, bg="white").pack(anchor=tk.W)
            self.deriv_var = tk.BooleanVar(value=self.data.get('derivative', False))
            tk.Checkbutton(self.content, text="1st derivative", variable=self.deriv_var, bg="white").pack(anchor=tk.W)

        elif step == 2:
            self.model_type = tk.StringVar(value=self.data.get('model_type', 'PLS'))
            tk.Radiobutton(self.content, text="PLS", variable=self.model_type, value="PLS",
                           bg="white").pack(anchor=tk.W, pady=2)
            tk.Radiobutton(self.content, text="PCR", variable=self.model_type, value="PCR",
                           bg="white").pack(anchor=tk.W)

        elif step == 3:
            tk.Label(self.content, text="Components:", bg="white", font=("Arial", 8)).pack(anchor=tk.W)
            self.n_comp = tk.IntVar(value=self.data.get('n_comp', 5))
            tk.Spinbox(self.content, from_=1, to=20, textvariable=self.n_comp, width=5).pack(anchor=tk.W)
            tk.Label(self.content, text="CV folds:", bg="white", font=("Arial", 8)).pack(anchor=tk.W, pady=(5,0))
            self.cv_folds = tk.IntVar(value=self.data.get('cv', 10))
            tk.Spinbox(self.content, from_=2, to=20, textvariable=self.cv_folds, width=5).pack(anchor=tk.W)

        elif step == 4:
            tk.Label(self.content, text="Run validation:", bg="white",
                     font=("Arial", 8)).pack(pady=5)
            self.run_btn = tk.Button(self.content, text="Run Validation", command=self._run_validation)
            self.run_btn.pack()
            self.results_text = tk.Text(self.content, height=6, width=50)
            self.results_text.pack(fill=tk.BOTH, expand=True, pady=5)
            self.diag_btn = tk.Button(self.content, text="Show Diagnostic Plots", command=self._show_diagnostics,
                                      state=tk.DISABLED)
            self.diag_btn.pack(pady=5)

        elif step == 5:
            tk.Label(self.content, text="Method Name:", bg="white", font=("Arial", 8)).pack(anchor=tk.W)
            self.method_name = tk.Entry(self.content, width=30)
            self.method_name.pack(fill=tk.X, pady=2)
            self.method_name.insert(0, self.data.get('method_name', ''))
            tk.Label(self.content, text="Description:", bg="white", font=("Arial", 8)).pack(anchor=tk.W)
            self.method_desc = tk.Text(self.content, height=4, width=50)
            self.method_desc.pack(fill=tk.X, pady=2)
            if 'method_desc' in self.data:
                self.method_desc.insert(1.0, self.data['method_desc'])
            self.save_btn = tk.Button(self.content, text="Save Method", command=self._save_method)
            self.save_btn.pack(pady=5)

    def _run_validation(self):
        # Use saved data from step 0
        selected_indices = self.data.get('selected_indices', [])
        if not selected_indices:
            messagebox.showerror("Error", "No samples selected in step 1")
            return
        conc_col = self.data.get('conc_col', 'Concentration')
        samples = self.app.data_hub.get_all()
        X_list = []
        y_list = []
        wavelengths = None
        for idx in selected_indices:
            s = samples[idx]
            if 'Wavelength' in s and 'Intensity' in s:
                wl = s['Wavelength']
                if wavelengths is None:
                    wavelengths = np.array(wl)
                else:
                    if not np.array_equal(wavelengths, wl):
                        messagebox.showerror("Error", "Wavelengths differ between samples")
                        return
                X_list.append(s['Intensity'])
                if conc_col in s:
                    y_list.append(s[conc_col])
                else:
                    messagebox.showerror("Error", f"Column '{conc_col}' not found in sample {idx}")
                    return
        X = np.array(X_list)
        y = np.array(y_list)

        # Apply preprocessing
        if self.data.get('snv', False):
            X = np.array([PreprocessingEngine.snv(x) for x in X])
        if self.data.get('savgol', False):
            X = np.array([PreprocessingEngine.savgol(x, 11, 3) for x in X])
        if self.data.get('derivative', False):
            X = np.array([np.gradient(x) for x in X])

        n_comp = self.n_comp.get()
        cv = self.cv_folds.get()
        if self.model_type.get() == "PLS":
            result = CalibrationEngine.pls(X, y, n_comp, cv)
        else:
            result = CalibrationEngine.pcr(X, y, n_comp, cv)

        self.model_result = result
        self.data['model_result'] = result
        self.data['X'] = X
        self.data['y'] = y
        self.data['wavelengths'] = wavelengths

        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, f"RMSEC: {result['rmsec']:.4f}\n")
        self.results_text.insert(tk.END, f"RMSECV: {result['rmsecv']:.4f}\n")
        self.results_text.insert(tk.END, f"R² Cal: {result['r2_cal']:.4f}\n")
        self.results_text.insert(tk.END, f"R² CV: {result['r2_cv']:.4f}\n")
        self.diag_btn.config(state=tk.NORMAL)

    def _next(self):
        # Save data from current step before moving
        if self.current_step == 0:
            self.data['selected_indices'] = self.sample_listbox.curselection()
            self.data['conc_col'] = self.conc_col.get()
        elif self.current_step == 1:
            self.data['snv'] = self.snv_var.get()
            self.data['savgol'] = self.sg_var.get()
            self.data['derivative'] = self.deriv_var.get()
        elif self.current_step == 2:
            self.data['model_type'] = self.model_type.get()
        elif self.current_step == 3:
            self.data['n_comp'] = self.n_comp.get()
            self.data['cv'] = self.cv_folds.get()
        elif self.current_step == 4:
            # Already saved via model_result
            pass
        elif self.current_step == 5:
            self.data['method_name'] = self.method_name.get()
            self.data['method_desc'] = self.method_desc.get("1.0", tk.END).strip()

        if self.current_step < len(self.steps)-1:
            self.current_step += 1
            self._build_step(self.current_step)
            self.back_btn.config(state=tk.NORMAL)
            if self.current_step == len(self.steps)-1:
                self.next_btn.config(state=tk.DISABLED)

    def _back(self):
        # Save data from current step before moving back
        if self.current_step == 1:
            self.data['snv'] = self.snv_var.get()
            self.data['savgol'] = self.sg_var.get()
            self.data['derivative'] = self.deriv_var.get()
        elif self.current_step == 2:
            self.data['model_type'] = self.model_type.get()
        elif self.current_step == 3:
            self.data['n_comp'] = self.n_comp.get()
            self.data['cv'] = self.cv_folds.get()
        elif self.current_step == 4:
            pass
        elif self.current_step == 5:
            self.data['method_name'] = self.method_name.get()
            self.data['method_desc'] = self.method_desc.get("1.0", tk.END).strip()

        if self.current_step > 0:
            self.current_step -= 1
            self._build_step(self.current_step)
            self.next_btn.config(state=tk.NORMAL)
            if self.current_step == 0:
                self.back_btn.config(state=tk.DISABLED)

    def _show_diagnostics(self):
        if self.model_result is None:
            return
        diag_win = tk.Toplevel(self)
        diag_win.title("Diagnostic Plots")
        diag_win.geometry("800x450")
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8,4))
        y_pred = self.model_result.get('y_pred_cal', np.zeros_like(self.data['y']))
        residuals = self.data['y'] - y_pred
        ax1.scatter(y_pred, residuals)
        ax1.axhline(0, color='r', linestyle='--')
        ax1.set_xlabel("Predicted")
        ax1.set_ylabel("Residuals")
        ax1.set_title("Residuals vs Predicted")
        resid_std = np.std(residuals)
        outliers = np.abs(residuals) > 3 * resid_std
        n_outliers = np.sum(outliers)
        outlier_text = f"Outliers (>3σ): {n_outliers} / {len(residuals)} ({100*n_outliers/len(residuals):.1f}%)"
        ax1.text(0.02, 0.98, outlier_text, transform=ax1.transAxes, fontsize=8,
                 verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        if 'x_scores' in self.model_result and self.model_result['x_scores'] is not None:
            scores = self.model_result['x_scores']
            t2 = np.sum(scores**2 / np.var(scores, axis=0), axis=1)
            X_res = self.data['X'] - scores @ self.model_result['x_loadings'].T
            q = np.sum(X_res**2, axis=1)
            ax2.scatter(t2, q)
            ax2.set_xlabel("Hotelling T²")
            ax2.set_ylabel("Q residuals")
            ax2.set_title("Q vs T²")
        else:
            ax2.text(0.5, 0.5, "Not available", ha='center', va='center')
        canvas = FigureCanvasTkAgg(fig, diag_win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        toolbar = NavigationToolbar2Tk(canvas, diag_win)
        toolbar.update()

    def _save_method(self):
        name = self.method_name.get().strip()
        if not name:
            messagebox.showerror("Error", "Method name required")
            return
        result = self.data.get('model_result')
        if not result:
            messagebox.showerror("Error", "No model result to save")
            return
        model = result['model']
        scaler_X = result.get('scaler_X')
        scaler_y = result.get('scaler_y')
        metadata = {
            'description': self.method_desc.get("1.0", tk.END).strip(),
            'type': self.data['model_type'],
            'n_components': self.data['n_comp'],
            'cv': self.data['cv'],
            'preprocessing': self.data['preproc'],
            'wavelengths': self.data['wavelengths'].tolist() if self.data['wavelengths'] is not None else None,
            'rmsec': result['rmsec'],
            'rmsecv': result['rmsecv'],
            'r2_cal': result['r2_cal'],
            'r2_cv': result['r2_cv']
        }
        path = self.method_manager.save_method(name, model, scaler_X, scaler_y, metadata)
        if path:
            messagebox.showinfo("Saved", f"Method saved")
        self.destroy()

# ============================================================================
# TAB 3: APPLY METHOD (single sample)
# ============================================================================
class ApplyMethodTab(AdvancedTab):
    def __init__(self, parent, app, ui_queue, method_manager):
        super().__init__(parent, app, ui_queue, "Apply")
        self.method_manager = method_manager
        self.current_method = None
        self._build_ui()

    def _build_ui(self):
        left = tk.Frame(self.content_frame, bg="white", width=150)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=2, pady=2)
        right = tk.Frame(self.content_frame, bg="white")
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Label(left, text="Methods", font=("Arial", 8, "bold"), bg="white").pack()
        self.method_listbox = tk.Listbox(left, height=6)
        self.method_listbox.pack(fill=tk.BOTH, expand=True, padx=2)
        self.method_listbox.bind('<<ListboxSelect>>', self._on_method_select)
        tk.Button(left, text="Refresh", command=self._refresh_methods, width=8).pack(pady=2)

        tk.Label(left, text="Sample", font=("Arial", 8, "bold"), bg="white").pack()
        self.sample_combo = ttk.Combobox(left, state="readonly", width=15)
        self.sample_combo.pack(fill=tk.X, padx=2)
        self._refresh_samples()

        tk.Button(left, text="Predict", command=self._predict, width=8).pack(pady=5)

        self.result_var = tk.StringVar(value="")
        tk.Label(right, text="Prediction:", font=("Arial", 8, "bold"), bg="white").pack(pady=2)
        tk.Label(right, textvariable=self.result_var, font=("Arial", 10), bg="white", fg=C_ACCENT).pack()

        if HAS_MPL:
            self.fig = Figure(figsize=(4,3), dpi=90)
            self.ax = self.fig.add_subplot(111)
            self.canvas = FigureCanvasTkAgg(self.fig, right)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _refresh_methods(self):
        self.method_listbox.delete(0, tk.END)
        for m in self.method_manager.list_methods():
            self.method_listbox.insert(tk.END, m)

    def _refresh_samples(self):
        if hasattr(self.app, 'data_hub'):
            samples = self.app.data_hub.get_all()
            names = [f"{i}: {s.get('Sample_ID', 'Unknown')}" for i, s in enumerate(samples)]
            self.sample_combo['values'] = names

    def _on_method_select(self, event):
        sel = self.method_listbox.curselection()
        if sel:
            name = self.method_listbox.get(sel[0])
            self.current_method = self.method_manager.load_method(name)

    def _predict(self):
        if self.current_method is None:
            messagebox.showerror("Error", "No method selected")
            return
        sel = self.sample_combo.current()
        if sel < 0:
            messagebox.showerror("Error", "No sample selected")
            return
        samples = self.app.data_hub.get_all()
        sample = samples[sel]
        if 'Wavelength' not in sample or 'Intensity' not in sample:
            messagebox.showerror("Error", "Sample does not contain spectral data")
            return
        wl = np.array(sample['Wavelength'])
        inten = np.array(sample['Intensity'])
        method_wl = np.array(self.current_method['metadata']['wavelengths'])
        if not np.allclose(wl, method_wl, rtol=1e-3):
            messagebox.showerror("Error", "Wavelengths do not match method's calibration wavelengths")
            return
        X = inten.reshape(1, -1)
        preproc = self.current_method['metadata']['preprocessing']
        if preproc.get('snv'):
            X = PreprocessingEngine.snv(X[0]).reshape(1, -1)
        if preproc.get('savgol'):
            X = PreprocessingEngine.savgol(X[0], 11, 3).reshape(1, -1)
        if preproc.get('derivative'):
            X = np.gradient(X[0]).reshape(1, -1)
        if self.current_method.get('scaler_X'):
            X = self.current_method['scaler_X'].transform(X)
        model = self.current_method['model']
        if hasattr(model, 'predict'):
            y_pred = model.predict(X)
            if self.current_method.get('scaler_y'):
                y_pred = self.current_method['scaler_y'].inverse_transform(y_pred.reshape(-1,1)).ravel()
            self.result_var.set(f"{y_pred[0]:.4f}")
            if HAS_MPL:
                self.ax.clear()
                self.ax.plot(wl, inten, lw=1)
                self.ax.set_title(f"Pred: {y_pred[0]:.4f}", fontsize=8)
                self.canvas.draw()
        else:
            messagebox.showerror("Error", "Model does not support prediction")

# ============================================================================
# TAB 4: BATCH PROCESSING
# ============================================================================
class BatchTab(AdvancedTab):
    def __init__(self, parent, app, ui_queue, method_manager):
        super().__init__(parent, app, ui_queue, "Batch")
        self.method_manager = method_manager
        self.reference_spectrum = None
        self.reference_wl = None
        self._build_ui()

    def _build_ui(self):
        ctrl = tk.Frame(self.content_frame, bg="white", height=80)
        ctrl.pack(fill=tk.X)
        ctrl.pack_propagate(False)

        # Mode selection
        tk.Label(ctrl, text="Mode:", bg="white", font=("Arial", 8, "bold")).grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.mode_var = tk.StringVar(value="method")
        tk.Radiobutton(ctrl, text="Apply saved method", variable=self.mode_var, value="method",
                       bg="white", command=self._mode_changed).grid(row=0, column=1, sticky=tk.W)
        tk.Radiobutton(ctrl, text="Compare to reference", variable=self.mode_var, value="compare",
                       bg="white", command=self._mode_changed).grid(row=0, column=2, sticky=tk.W)

        # Method selection
        tk.Label(ctrl, text="Method:", bg="white", font=("Arial", 8)).grid(row=1, column=0, sticky=tk.W, padx=5)
        self.method_combo = ttk.Combobox(ctrl, values=self.method_manager.list_methods(), state="readonly", width=20)
        self.method_combo.grid(row=1, column=1, columnspan=2, sticky=tk.W, padx=5, pady=2)

        # Reference sample selection
        tk.Label(ctrl, text="Reference sample:", bg="white", font=("Arial", 8)).grid(row=2, column=0, sticky=tk.W, padx=5)
        self.ref_combo = ttk.Combobox(ctrl, values=[], state="readonly", width=20)
        self.ref_combo.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)

        # Threshold for pass/fail
        tk.Label(ctrl, text="Pass threshold (%):", bg="white", font=("Arial", 8)).grid(row=2, column=2, sticky=tk.W, padx=5)
        self.threshold_var = tk.StringVar(value="95")
        tk.Entry(ctrl, textvariable=self.threshold_var, width=6).grid(row=2, column=3, sticky=tk.W)

        # Sample selection listbox (create before refresh)
        tk.Label(self.content_frame, text="Select samples to process (hold Ctrl for multiple):",
                 bg="white", font=("Arial", 8, "bold")).pack(anchor=tk.W, padx=5, pady=2)
        self.sample_listbox = tk.Listbox(self.content_frame, selectmode=tk.MULTIPLE, height=6)
        self.sample_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)

        # Run button
        self.run_btn = tk.Button(self.content_frame, text="Run Batch", command=self._run_batch,
                                 bg=C_ACCENT, fg="white", width=15)
        self.run_btn.pack(pady=5)

        # Results tree
        columns = ("Sample", "Result", "Pass/Fail")
        self.tree = ttk.Treeview(self.content_frame, columns=columns, show="headings", height=8)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        scroll = ttk.Scrollbar(self.content_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scroll.set)

        # Now refresh all lists
        self._refresh_samples()
        self._refresh_sample_list()

    def _refresh_samples(self):
        if hasattr(self.app, 'data_hub'):
            samples = self.app.data_hub.get_all()
            names = [f"{i}: {s.get('Sample_ID', 'Unknown')}" for i, s in enumerate(samples)]
            self.ref_combo['values'] = names

    def _refresh_sample_list(self):
        if hasattr(self.app, 'data_hub'):
            samples = self.app.data_hub.get_all()
            self.sample_listbox.delete(0, tk.END)
            for i, s in enumerate(samples):
                self.sample_listbox.insert(tk.END, f"{i}: {s.get('Sample_ID', 'Unknown')}")

    def _mode_changed(self):
        if self.mode_var.get() == "method":
            self.method_combo.config(state="readonly")
            self.ref_combo.config(state="disabled")
        else:
            self.method_combo.config(state="disabled")
            self.ref_combo.config(state="readonly")

    def _run_batch(self):
        selected = self.sample_listbox.curselection()
        if not selected:
            messagebox.showerror("Error", "No samples selected")
            return
        mode = self.mode_var.get()
        if mode == "method":
            method_name = self.method_combo.get()
            if not method_name:
                messagebox.showerror("Error", "No method selected")
                return
            method = self.method_manager.load_method(method_name)
            if method is None:
                messagebox.showerror("Error", "Failed to load method")
                return
        else:  # compare
            ref_idx = self.ref_combo.current()
            if ref_idx < 0:
                messagebox.showerror("Error", "No reference sample selected")
                return
            samples = self.app.data_hub.get_all()
            ref_sample = samples[ref_idx]
            if 'Wavelength' not in ref_sample or 'Intensity' not in ref_sample:
                messagebox.showerror("Error", "Reference sample lacks spectral data")
                return
            self.reference_wl = np.array(ref_sample['Wavelength'])
            self.reference_spectrum = np.array(ref_sample['Intensity'])
            threshold = float(self.threshold_var.get())

        # Process each selected sample
        samples = self.app.data_hub.get_all()
        for row in self.tree.get_children():
            self.tree.delete(row)

        for idx in selected:
            sample = samples[idx]
            if 'Wavelength' not in sample or 'Intensity' not in sample:
                continue
            wl = np.array(sample['Wavelength'])
            inten = np.array(sample['Intensity'])

            if mode == "method":
                # Apply saved method
                method_wl = np.array(method['metadata']['wavelengths'])
                if not np.allclose(wl, method_wl, rtol=1e-3):
                    result_text = "Wavelength mismatch"
                    passfail = "Invalid"
                else:
                    X = inten.reshape(1, -1)
                    preproc = method['metadata']['preprocessing']
                    if preproc.get('snv'):
                        X = PreprocessingEngine.snv(X[0]).reshape(1, -1)
                    if preproc.get('savgol'):
                        X = PreprocessingEngine.savgol(X[0], 11, 3).reshape(1, -1)
                    if preproc.get('derivative'):
                        X = np.gradient(X[0]).reshape(1, -1)
                    if method.get('scaler_X'):
                        X = method['scaler_X'].transform(X)
                    model = method['model']
                    if hasattr(model, 'predict'):
                        y_pred = model.predict(X)
                        if method.get('scaler_y'):
                            y_pred = method['scaler_y'].inverse_transform(y_pred.reshape(-1,1)).ravel()
                        result_text = f"{y_pred[0]:.4f}"
                        passfail = "Valid"
                    else:
                        result_text = "Prediction error"
                        passfail = "Invalid"
            else:
                # Compare to reference spectrum
                f = interpolate.interp1d(self.reference_wl, self.reference_spectrum,
                                         bounds_error=False, fill_value=0)
                ref_aligned = f(wl)
                similarity = LibrarySearchEngine.dot_product(inten, ref_aligned) * 100
                result_text = f"{similarity:.2f}%"
                passfail = "PASS" if similarity >= threshold else "FAIL"

            self.tree.insert("", tk.END, values=(sample.get('Sample_ID', f"Sample {idx}"), result_text, passfail))

# ============================================================================
# TAB 5: KINETICS MONITORING (without Live import)
# ============================================================================
class KineticsTab(AdvancedTab):
    def __init__(self, parent, app, ui_queue):
        super().__init__(parent, app, ui_queue, "Kinetics")
        self.time_series = None
        self._build_ui()

    def _build_ui(self):
        ctrl = tk.Frame(self.content_frame, bg="white", height=30)
        ctrl.pack(fill=tk.X)
        ctrl.pack_propagate(False)

        tk.Button(ctrl, text="Load Folder", command=self._load, width=10).pack(side=tk.LEFT, padx=2)
        self.view_mode = tk.StringVar(value="Surface")
        ttk.Combobox(ctrl, textvariable=self.view_mode,
                     values=["Surface", "Waterfall"], state="readonly", width=10).pack(side=tk.LEFT, padx=2)
        tk.Button(ctrl, text="Update", command=self._plot, width=6).pack(side=tk.LEFT, padx=2)

        if HAS_PLOTLY:
            tk.Button(ctrl, text="Plotly (browser)", command=self._plot_plotly, width=12).pack(side=tk.LEFT, padx=2)

        paned = ttk.PanedWindow(self.content_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        left = tk.Frame(paned, bg="white")
        paned.add(left, weight=2)
        right = tk.Frame(paned, bg="white")
        paned.add(right, weight=1)

        if HAS_MPL:
            self.fig_3d = Figure(figsize=(4,3), dpi=90)
            self.ax_3d = self.fig_3d.add_subplot(111, projection='3d')
            self.canvas_3d = FigureCanvasTkAgg(self.fig_3d, left)
            self.canvas_3d.draw()
            self.canvas_3d.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            self.fig_peak = Figure(figsize=(3,3), dpi=90)
            self.ax_peak = self.fig_peak.add_subplot(111)
            self.canvas_peak = FigureCanvasTkAgg(self.fig_peak, right)
            self.canvas_peak.draw()
            self.canvas_peak.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _load(self):
        folder = filedialog.askdirectory(title="Select folder with time-series spectra")
        if not folder:
            return
        self.status_label.config(text="Loading...")
        def worker():
            files = sorted(Path(folder).glob("*.csv"))
            times = []
            spectra = []
            wl = None
            for f in files:
                try:
                    df = pd.read_csv(f)
                    if wl is None:
                        wl = df.iloc[:,0].values
                    intensity = df.iloc[:,1].values
                    t = float(f.stem) if f.stem.replace('.','').replace('-','').isdigit() else len(times)
                    times.append(t)
                    spectra.append(intensity)
                except Exception as e:
                    print(f"Error loading {f}: {e}")
            if spectra:
                self.time_series = (np.array(times), wl, np.array(spectra))
                def update():
                    self._plot()
                    self.status_label.config(text=f"Loaded {len(times)} spectra")
                self.ui_queue.schedule(update)
            else:
                self.ui_queue.schedule(lambda: messagebox.showerror("Error", "No valid spectra found"))
        threading.Thread(target=worker, daemon=True).start()

    def _plot(self):
        if self.time_series is None:
            return
        times, wl, spectra = self.time_series
        mode = self.view_mode.get()

        self.ax_3d.clear()
        if mode == "Surface":
            X, Y = np.meshgrid(wl, times)
            self.ax_3d.plot_surface(X, Y, spectra, cmap='viridis')
        else:  # Waterfall
            for i, t in enumerate(times):
                offset = i * 0.1 * np.max(spectra)
                self.ax_3d.plot(wl, spectra[i] + offset, zs=t, zdir='y', color=plt.cm.viridis(i/len(times)))
        self.ax_3d.set_xlabel("Wavelength", fontsize=7)
        self.ax_3d.set_ylabel("Time", fontsize=7)
        self.ax_3d.set_zlabel("Intensity", fontsize=7)
        self.canvas_3d.draw()

        peak_idx = np.argmax(np.mean(spectra, axis=0))
        peak_areas = spectra[:, peak_idx-5:peak_idx+5].sum(axis=1)
        self.ax_peak.clear()
        self.ax_peak.plot(times, peak_areas, 'o-', markersize=3)
        self.ax_peak.set_xlabel("Time", fontsize=7)
        self.ax_peak.set_ylabel("Peak Area", fontsize=7)
        self.ax_peak.grid(True)
        self.canvas_peak.draw()

    def _plot_plotly(self):
        if not HAS_PLOTLY or self.time_series is None:
            return
        times, wl, spectra = self.time_series
        fig = go.Figure(data=[go.Surface(z=spectra, x=wl, y=times)])
        fig.update_layout(title='Kinetics 3D Surface',
                          scene=dict(xaxis_title='Wavelength',
                                     yaxis_title='Time',
                                     zaxis_title='Intensity'))
        fig.show()

# ============================================================================
# PLUGIN REGISTRATION
# ============================================================================
def setup_plugin(main_app):
    plugin = AdvancedSpectroscopySuite(main_app)

    if hasattr(main_app, 'advanced_menu'):
        main_app.advanced_menu.add_command(
            label=f"{PLUGIN_INFO['icon']} {PLUGIN_INFO['name']}",
            command=plugin.show_interface
        )
        print(f"✅ Added to Advanced menu: {PLUGIN_INFO['name']}")
    elif hasattr(main_app, 'menu_bar'):
        if not hasattr(main_app, 'analysis_menu'):
            main_app.analysis_menu = tk.Menu(main_app.menu_bar, tearoff=0)
            main_app.menu_bar.add_cascade(label="🔬 Analysis", menu=main_app.analysis_menu)
        main_app.analysis_menu.add_command(
            label=f"{PLUGIN_INFO['icon']} {PLUGIN_INFO['name']}",
            command=plugin.show_interface
        )
        print(f"✅ Added to Analysis menu: {PLUGIN_INFO['name']}")
    return plugin
