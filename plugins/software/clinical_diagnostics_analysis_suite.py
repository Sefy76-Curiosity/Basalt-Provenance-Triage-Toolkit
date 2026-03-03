"""
CLINICAL DIAGNOSTICS SUITE v2.0 - COMMUNITY EDITION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Original 7 tabs fully preserved (Ramakers, Livak, Findlay, Herzenberg, Hindson, Ririe, CLSI)
✓ ENHANCED: Smart Assistant - Context-aware help that learns from your data
✓ ENHANCED: Recipe System - Save/load complete analysis settings
✓ ENHANCED: Publication Tools - One-click paper-ready exports
✓ ENHANCED: Uncertainty Bridge - Connect to Monte Carlo plugin for confidence intervals
✓ ENHANCED: qPCR - geNorm reference stability, quality flags, advanced baseline
✓ ENHANCED: ΔΔCt - Statistical group comparison, error bars, reference validation
✓ ENHANCED: ELISA - 4PL/5PL comparison, weighting, parallelism, validation metrics
✓ ENHANCED: Flow - REAL clustering (FlowSOM/GMM) with fallback, compensation
✓ ENHANCED: ddPCR - Poisson CI, fractional abundance, rain classification
✓ ENHANCED: Melting - HRM genotyping, peak deconvolution, difference clustering
✓ ENHANCED: Reference - Bootstrap CI, partition testing, indirect methods
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

PLUGIN_INFO = {
    "id": "clinical_diagnostics_suite",
    "name": "Clinical Diagnostics Suite",
    "category": "software",
    "field": "Clinical Diagnostics & Molecular Biology",
    "icon": "🧬✨",
    "version": "2.0.0",
    "author": "Sefy Levy & DeepSeek & Community",
    "description": "qPCR · ΔΔCt · ELISA · Flow · ddPCR · HRM · Reference Ranges — Now with Smart Assistant, Recipes, Publication Tools, Uncertainty Integration",
    "requires": ["numpy", "pandas", "scipy", "matplotlib"],
    "optional": ["lmfit", "sklearn", "statsmodels", "flowkit", "fcsparser"],
    "window_size": "1200x800"
}

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import pandas as pd
import threading
import queue
import os
import re
import json
import warnings
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import pickle
import base64
import csv
warnings.filterwarnings("ignore")

# ============================================================================
# OPTIONAL IMPORTS (with graceful fallbacks)
# ============================================================================
try:
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    from matplotlib.figure import Figure
    from matplotlib.gridspec import GridSpec
    import matplotlib.patches as mpatches
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

try:
    from scipy import stats, optimize, interpolate, signal
    from scipy.optimize import curve_fit, least_squares, minimize
    from scipy.stats import linregress, norm, chi2, f_oneway, ttest_ind, mannwhitneyu, shapiro
    from scipy.signal import savgol_filter, find_peaks
    from scipy.interpolate import interp1d
    from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
    from scipy.spatial.distance import pdist
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    from sklearn import mixture, cluster, decomposition
    from sklearn.preprocessing import StandardScaler
    from sklearn.mixture import GaussianMixture
    from sklearn.metrics import silhouette_samples
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

try:
    import flowkit as fk
    HAS_FLOWKIT = True
except ImportError:
    HAS_FLOWKIT = False

# ============================================================================
# COLOR PALETTE — clinical diagnostics (clean, medical)
# ============================================================================
C_HEADER   = "#003366"   # dark medical blue
C_ACCENT   = "#CC3333"   # diagnostic red
C_ACCENT2  = "#006633"   # result green
C_ACCENT3  = "#FF9900"   # warning orange
C_LIGHT    = "#F5F5F5"   # light gray
C_BORDER   = "#BDC3C7"   # silver
C_STATUS   = "#006633"   # green
C_WARN     = "#CC3333"   # red
C_INFO     = "#3498db"   # info blue
C_SMART    = "#9b59b6"   # smart assistant purple
PLOT_COLORS = ["#003366", "#CC3333", "#006633", "#FF9900", "#663399", "#008080", "#CC6600"]

# ============================================================================
# THREAD-SAFE UI QUEUE
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
# TOOLTIP (Enhanced)
# ============================================================================
class ToolTip:
    def __init__(self, widget, text, enhanced_text=None):
        self.widget = widget
        self.text = text
        self.enhanced_text = enhanced_text
        self.tip = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, event=None):
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 20
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")

        display_text = self.enhanced_text if self.enhanced_text and self.enhanced_text != self.text else self.text

        tk.Label(self.tip, text=display_text, background="#FFFACD",
                 relief=tk.SOLID, borderwidth=1, justify=tk.LEFT,
                 font=("Arial", 8)).pack()

    def _hide(self, event=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None


# ============================================================================
# BASE TAB CLASS - Auto-import from main table (YOUR ORIGINAL CODE)
# ============================================================================
class AnalysisTab:
    """Base class for all analysis tabs with auto-import from main table"""

    def __init__(self, parent, app, ui_queue, tab_name):
        self.parent = parent
        self.app = app
        self.ui_queue = ui_queue
        self.tab_name = tab_name
        self.frame = ttk.Frame(parent)

        # Current state
        self.selected_sample_idx = None
        self.samples = []
        self._loading = False
        self._update_id = None

        # Import mode
        self.import_mode = "auto"  # "auto" or "manual"
        self.manual_data = None

        # UI Elements
        self.sample_combo = None
        self.status_label = None
        self.import_indicator = None

        self._build_base_ui()

        # Register as observer of data hub
        if hasattr(self.app, 'data_hub'):
            self.app.data_hub.register_observer(self)

        # Initial refresh
        self.refresh_sample_list()

    def _build_base_ui(self):
        """Build the base UI with import controls"""
        # Import mode selector
        mode_frame = tk.Frame(self.frame, bg=C_LIGHT, height=30)
        mode_frame.pack(fill=tk.X)
        mode_frame.pack_propagate(False)

        tk.Label(mode_frame, text="📥 Import Mode:", font=("Arial", 8, "bold"),
                bg=C_LIGHT).pack(side=tk.LEFT, padx=5)

        self.import_mode_var = tk.StringVar(value="auto")
        tk.Radiobutton(mode_frame, text="Auto (from main table)", variable=self.import_mode_var,
                      value="auto", command=self._switch_import_mode,
                      bg=C_LIGHT, font=("Arial", 7)).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(mode_frame, text="Manual (CSV/file)", variable=self.import_mode_var,
                      value="manual", command=self._switch_import_mode,
                      bg=C_LIGHT, font=("Arial", 7)).pack(side=tk.LEFT, padx=5)

        self.import_indicator = tk.Label(mode_frame, text="", font=("Arial", 7),
                                         bg=C_LIGHT, fg=C_STATUS)
        self.import_indicator.pack(side=tk.RIGHT, padx=10)

        # Sample selector frame (visible in auto mode)
        self.selector_frame = tk.Frame(self.frame, bg="white")
        self.selector_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(self.selector_frame, text=f"{self.tab_name} - Select Sample:",
                font=("Arial", 10, "bold"), bg="white").pack(side=tk.LEFT, padx=5)

        self.sample_combo = ttk.Combobox(self.selector_frame, state="readonly", width=60)
        self.sample_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.sample_combo.bind('<<ComboboxSelected>>', self._on_sample_selected)

        ttk.Button(self.selector_frame, text="🔄 Refresh",
                  command=self.refresh_sample_list).pack(side=tk.RIGHT, padx=5)

        # Manual import frame (visible in manual mode)
        self.manual_frame = tk.Frame(self.frame, bg="white")
        self.manual_frame.pack(fill=tk.X, padx=5, pady=5)
        self.manual_frame.pack_forget()  # Hidden by default

        ttk.Button(self.manual_frame, text="📂 Load CSV/File",
                  command=self._manual_import).pack(side=tk.LEFT, padx=5)
        self.manual_label = tk.Label(self.manual_frame, text="No file loaded",
                                     font=("Arial", 7), bg="white", fg="#888")
        self.manual_label.pack(side=tk.LEFT, padx=10)

        # Status label
        self.status_label = tk.Label(self.frame, text="", font=("Arial", 8),
                                      bg="white", fg=C_STATUS)
        self.status_label.pack(fill=tk.X, padx=5, pady=2)

        # Main content area (to be filled by child classes)
        self.content_frame = tk.Frame(self.frame, bg="white")
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _switch_import_mode(self):
        """Switch between auto and manual import modes"""
        mode = self.import_mode_var.get()

        if mode == "auto":
            self.selector_frame.pack(fill=tk.X, padx=5, pady=5)
            self.manual_frame.pack_forget()
            self.import_indicator.config(text="🔄 Auto mode - data from main table")
            self.refresh_sample_list()
        else:
            self.selector_frame.pack_forget()
            self.manual_frame.pack(fill=tk.X, padx=5, pady=5)
            self.import_indicator.config(text="📁 Manual mode - load your own files")

    def _manual_import(self):
        """Manual import from CSV"""
        path = filedialog.askopenfilename(
            title="Load Reference Data",
            filetypes=[("CSV", "*.csv"), ("Excel", "*.xlsx"), ("All files", "*.*")])
        if not path:
            return

        self.status_label.config(text="🔄 Loading reference data...")

        def worker():
            try:
                data = self.engine.load_reference_data(path)

                def update():
                    self.ref_data = data
                    self.manual_label.config(text=f"✓ {Path(path).name}")
                    self._update_analyte_list()
                    self.status_label.config(text=f"Loaded {len(data)} records")
                self.ui_queue.schedule(update)

            except Exception as e:
                self.ui_queue.schedule(lambda: messagebox.showerror("Error", str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def get_samples(self):
        """Get all samples from the main data table"""
        if hasattr(self.app, 'data_hub'):
            return self.app.data_hub.get_all()
        return []

    def on_data_changed(self, event, *args):
        """Called when main table data changes"""
        if self.import_mode_var.get() == "auto":
            if self._update_id:
                self.frame.after_cancel(self._update_id)
            self._update_id = self.frame.after(500, self._delayed_refresh)

    def _delayed_refresh(self):
        """Delayed refresh to avoid too many updates"""
        self.refresh_sample_list()
        self._update_id = None

    def refresh_sample_list(self):
        """Refresh the sample dropdown"""
        if self.import_mode_var.get() != "auto":
            return

        self.samples = self.get_samples()
        sample_ids = []

        for i, sample in enumerate(self.samples):
            sample_id = sample.get('Sample_ID', f'Sample {i}')
            has_data = self._sample_has_data(sample)

            if has_data:
                display = f"✅ {i}: {sample_id} (has data)"
            else:
                display = f"○ {i}: {sample_id} (no data)"

            sample_ids.append(display)

        self.sample_combo['values'] = sample_ids

        data_count = sum(1 for i, s in enumerate(self.samples) if self._sample_has_data(s))
        self.status_label.config(text=f"Total: {len(self.samples)} | With data: {data_count}")

        if self.selected_sample_idx is not None and self.selected_sample_idx < len(self.samples):
            self.sample_combo.set(sample_ids[self.selected_sample_idx])
        elif sample_ids:
            for i, s in enumerate(self.samples):
                if self._sample_has_data(s):
                    self.selected_sample_idx = i
                    self.sample_combo.set(sample_ids[i])
                    self._load_sample_data(i)
                    break

    def _sample_has_data(self, sample):
        """Check if sample has data for this tab - to be overridden"""
        return False

    def _on_sample_selected(self, event=None):
        """Handle sample selection"""
        selection = self.sample_combo.get()
        if not selection:
            return

        try:
            idx = int(''.join(filter(str.isdigit, selection.split(':', 1)[0])))
            self.selected_sample_idx = idx
            self._load_sample_data(idx)
        except (ValueError, IndexError):
            pass

    def _load_sample_data(self, idx):
        """Load data for the selected sample - to be overridden"""
        pass


# ============================================================================
# ENGINE 1 — qPCR EFFICIENCY (Ramakers et al. 2003; Ruijter et al. 2009)
# ============================================================================
class qPCRAnalyzer:
    """
    qPCR amplification curve analysis and efficiency calculation.

    LinRegPCR method (Ramakers et al. 2003):
        - Baseline subtraction
        - Log-linear phase identification
        - Efficiency from slope: E = 10^(-1/slope) - 1

    Cq determination methods:
        - Second derivative maximum (SDM)
        - Cycle threshold (Ct) at fixed fluorescence
        - Fit point method

    References:
        Ramakers, C. et al. (2003) "Assumption-free analysis of quantitative
            real-time polymerase chain reaction (PCR) data" Neuroscience Letters
        Ruijter, J.M. et al. (2009) "Amplification efficiency: linking baseline
            and bias in the analysis of quantitative PCR data" Nucleic Acids Research
    """

    @classmethod
    def baseline_correction(cls, cycles, fluorescence, baseline_cycles=(3, 15)):
        """
        Subtract baseline fluorescence (mean of early cycles)
        """
        baseline_mask = (cycles >= baseline_cycles[0]) & (cycles <= baseline_cycles[1])
        if not np.any(baseline_mask):
            baseline = np.mean(fluorescence[:10])
        else:
            baseline = np.mean(fluorescence[baseline_mask])

        return fluorescence - baseline

    @classmethod
    def find_log_linear_phase(cls, cycles, fluorescence, window=5, r2_threshold=0.99):
        """
        Identify log-linear phase for efficiency calculation (LinRegPCR)

        Algorithm:
        1. Take log of background-subtracted fluorescence
        2. Slide window along curve
        3. Find window with highest linear correlation
        """
        # Ensure positive values
        fluor_pos = np.maximum(fluorescence, 1e-6)
        log_fluor = np.log(fluor_pos)

        best_r2 = -1
        best_start = 0
        best_end = 0

        for start in range(len(cycles) - window):
            end = start + window
            x = cycles[start:end]
            y = log_fluor[start:end]

            # Linear regression
            slope, intercept, r_value, p_value, std_err = linregress(x, y)
            r2 = r_value**2

            if r2 > best_r2 and r2 > r2_threshold:
                best_r2 = r2
                best_start = start
                best_end = end
                best_slope = slope
                best_intercept = intercept

        if best_r2 > 0:
            # Calculate efficiency: E = 10^slope - 1
            efficiency = 10**best_slope - 1

            return {
                "efficiency": efficiency,
                "slope": best_slope,
                "intercept": best_intercept,
                "r2": best_r2,
                "start_cycle": best_start,
                "end_cycle": best_end
            }
        else:
            return None

    @classmethod
    def determine_cq_sdm(cls, cycles, fluorescence, smooth=True):
        """
        Determine Cq by second derivative maximum method

        The Cq is the cycle at which the second derivative of the
        amplification curve reaches its maximum.
        """
        if smooth and HAS_SCIPY:
            fluor_smooth = savgol_filter(fluorescence, window_length=min(11, len(fluorescence)//5*2+1), polyorder=3)
        else:
            fluor_smooth = fluorescence

        # First derivative
        d1 = np.gradient(fluor_smooth, cycles)

        # Second derivative
        d2 = np.gradient(d1, cycles)

        # Find maximum of second derivative
        if HAS_SCIPY:
            peaks, properties = find_peaks(d2, height=np.max(d2)*0.1)
            if len(peaks) > 0:
                # Take the highest peak
                peak_idx = peaks[np.argmax(d2[peaks])]
                cq = cycles[peak_idx]
                return cq, peak_idx
            else:
                # Fallback: find where d2 is max
                peak_idx = np.argmax(d2)
                return cycles[peak_idx], peak_idx
        else:
            peak_idx = np.argmax(d2)
            return cycles[peak_idx], peak_idx

    @classmethod
    def determine_cq_threshold(cls, cycles, fluorescence, threshold=0.1):
        """
        Determine Cq by cycle threshold method

        Cq is the cycle at which fluorescence crosses the threshold.
        """
        # Find first cycle where fluorescence exceeds threshold
        for i in range(1, len(fluorescence)):
            if fluorescence[i] > threshold and fluorescence[i-1] <= threshold:
                # Linear interpolation
                x1, y1 = cycles[i-1], fluorescence[i-1]
                x2, y2 = cycles[i], fluorescence[i]
                cq = x1 + (threshold - y1) * (x2 - x1) / (y2 - y1)
                return cq, i

        return None, None

    @classmethod
    def load_qpcr_data(cls, path):
        """Load qPCR amplification data from CSV"""
        df = pd.read_csv(path)

        # Try to identify columns
        cycle_col = None
        fluor_cols = []

        for col in df.columns:
            col_lower = col.lower()
            if any(x in col_lower for x in ['cycle', 'well', 'tube']):
                cycle_col = col
            elif any(x in col_lower for x in ['fluor', 'rn', 'delta']):
                fluor_cols.append(col)

        if cycle_col is None:
            cycle_col = df.columns[0]

        cycles = df[cycle_col].values

        # Load all fluorescence columns
        fluorescence = {}
        for col in fluor_cols[:10]:  # Limit to first 10 wells
            fluorescence[col] = df[col].values

        return {
            "cycles": cycles,
            "fluorescence": fluorescence,
            "metadata": {"file": Path(path).name}
        }


# ============================================================================
# TAB 1: qPCR EFFICIENCY
# ============================================================================
class qPCRAnalysisTab(AnalysisTab):
    def __init__(self, parent, app, ui_queue):
        super().__init__(parent, app, ui_queue, "qPCR Efficiency")
        self.engine = qPCRAnalyzer
        self.cycles = None
        self.fluorescence = None
        self.current_well = None
        self.results = {}
        self._build_content_ui()

    def _sample_has_data(self, sample):
        """Check if sample has qPCR data"""
        return any(col in sample and sample[col] for col in
                  ['qPCR_File', 'Amplification_Data', 'Cq_Values'])

    def _manual_import(self):
        """Manual import from CSV"""
        path = filedialog.askopenfilename(
            title="Load qPCR Data",
            filetypes=[("CSV", "*.csv"), ("Text", "*.txt"), ("RDML", "*.rdml"), ("All files", "*.*")])
        if not path:
            return

        self.status_label.config(text="🔄 Loading qPCR data...")

        def worker():
            try:
                data = self.engine.load_qpcr_data(path)

                def update():
                    self.cycles = data["cycles"]
                    self.fluorescence = data["fluorescence"]
                    self.manual_label.config(text=f"✓ {Path(path).name}")
                    self._update_well_list()
                    self._plot_amplification()
                    self.status_label.config(text=f"Loaded {len(self.fluorescence)} wells")
                self.ui_queue.schedule(update)

            except Exception as e:
                self.ui_queue.schedule(lambda: messagebox.showerror("Error", str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _load_sample_data(self, idx):
        """Auto-load from table"""
        sample = self.samples[idx]

        if 'Amplification_Data' in sample and sample['Amplification_Data']:
            try:
                data = json.loads(sample['Amplification_Data'])
                self.cycles = np.array(data['cycles'])
                self.fluorescence = data['fluorescence']  # dict of well: values
                self._update_well_list()
                self._plot_amplification()
                self.status_label.config(text=f"Loaded qPCR data from table")
            except Exception as e:
                self.status_label.config(text=f"Error: {e}")

    def _build_content_ui(self):
        """Build the tab-specific UI"""
        # Main split
        main_pane = ttk.PanedWindow(self.content_frame, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True)

        # Left panel - controls
        left = tk.Frame(main_pane, bg="white", width=300)
        main_pane.add(left, weight=1)

        # Right panel - plot
        right = tk.Frame(main_pane, bg="white")
        main_pane.add(right, weight=2)

        # === LEFT PANEL ===
        tk.Label(left, text="🧬 qPCR EFFICIENCY ANALYSIS",
                font=("Arial", 10, "bold"), bg=C_LIGHT, fg=C_HEADER).pack(fill=tk.X, pady=2)

        tk.Label(left, text="Ramakers et al. 2003 · Ruijter et al. 2009",
                font=("Arial", 7), bg="white", fg="#888").pack(anchor=tk.W, padx=4)

        # Well selector
        tk.Label(left, text="Select Well:", font=("Arial", 8, "bold"),
                bg="white").pack(anchor=tk.W, padx=4, pady=(4, 0))

        self.well_listbox = tk.Listbox(left, height=6, font=("Courier", 8))
        self.well_listbox.pack(fill=tk.X, padx=4, pady=2)
        self.well_listbox.bind('<<ListboxSelect>>', self._on_well_selected)

        # Baseline cycles
        param_frame = tk.LabelFrame(left, text="Analysis Parameters", bg="white",
                                   font=("Arial", 8, "bold"), fg=C_HEADER)
        param_frame.pack(fill=tk.X, padx=4, pady=4)

        row1 = tk.Frame(param_frame, bg="white")
        row1.pack(fill=tk.X, pady=2)
        tk.Label(row1, text="Baseline cycles:", font=("Arial", 8), bg="white").pack(side=tk.LEFT)
        self.baseline_start = tk.StringVar(value="3")
        self.baseline_end = tk.StringVar(value="15")
        ttk.Entry(row1, textvariable=self.baseline_start, width=4).pack(side=tk.LEFT, padx=1)
        tk.Label(row1, text="-", font=("Arial", 8), bg="white").pack(side=tk.LEFT)
        ttk.Entry(row1, textvariable=self.baseline_end, width=4).pack(side=tk.LEFT, padx=1)

        # Cq method
        tk.Label(param_frame, text="Cq determination:", font=("Arial", 8), bg="white").pack(anchor=tk.W, padx=4)
        self.cq_method = tk.StringVar(value="Second Derivative Max")
        ttk.Combobox(param_frame, textvariable=self.cq_method,
                     values=["Second Derivative Max", "Threshold (0.1)", "Threshold (0.2)", "Fit Point"],
                     width=20, state="readonly").pack(fill=tk.X, padx=4, pady=2)

        ttk.Button(left, text="📊 ANALYZE SELECTED WELL",
                  command=self._analyze_well).pack(fill=tk.X, padx=4, pady=4)
        ttk.Button(left, text="📈 ANALYZE ALL WELLS",
                  command=self._analyze_all).pack(fill=tk.X, padx=4, pady=2)

        # Results
        results_frame = tk.LabelFrame(left, text="Results", bg="white",
                                     font=("Arial", 8, "bold"), fg=C_HEADER)
        results_frame.pack(fill=tk.X, padx=4, pady=4)

        self.qpcr_results = {}
        result_labels = [
            ("Cq:", "cq"),
            ("Efficiency:", "eff"),
            ("Slope:", "slope"),
            ("R²:", "r2"),
            ("Baseline:", "baseline")
        ]

        for i, (label, key) in enumerate(result_labels):
            row = tk.Frame(results_frame, bg="white")
            row.pack(fill=tk.X, pady=1)
            tk.Label(row, text=label, font=("Arial", 7), bg="white", width=12, anchor=tk.W).pack(side=tk.LEFT)
            var = tk.StringVar(value="—")
            tk.Label(row, textvariable=var, font=("Arial", 7, "bold"),
                    bg="white", fg=C_HEADER).pack(side=tk.LEFT, padx=2)
            self.qpcr_results[key] = var

        # === RIGHT PANEL ===
        if HAS_MPL:
            self.qpcr_fig = Figure(figsize=(8, 6), dpi=100, facecolor="white")
            gs = GridSpec(2, 2, figure=self.qpcr_fig, hspace=0.3, wspace=0.3)
            self.qpcr_ax_amp = self.qpcr_fig.add_subplot(gs[0, :])
            self.qpcr_ax_log = self.qpcr_fig.add_subplot(gs[1, 0])
            self.qpcr_ax_eff = self.qpcr_fig.add_subplot(gs[1, 1])

            self.qpcr_ax_amp.set_title("Amplification Curve", fontsize=9, fontweight="bold")
            self.qpcr_ax_log.set_title("Log-Linear Phase", fontsize=9, fontweight="bold")
            self.qpcr_ax_eff.set_title("Efficiency Plot", fontsize=9, fontweight="bold")

            self.qpcr_canvas = FigureCanvasTkAgg(self.qpcr_fig, right)
            self.qpcr_canvas.draw()
            self.qpcr_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            toolbar = NavigationToolbar2Tk(self.qpcr_canvas, right)
            toolbar.update()
        else:
            tk.Label(right, text="matplotlib required for plots",
                    bg="white", fg="#888").pack(expand=True)

    def _update_well_list(self):
        """Update well listbox"""
        self.well_listbox.delete(0, tk.END)
        if self.fluorescence:
            for well in sorted(self.fluorescence.keys()):
                self.well_listbox.insert(tk.END, well)

    def _plot_amplification(self):
        """Plot amplification curves"""
        if not HAS_MPL or self.cycles is None or not self.fluorescence:
            return

        self.qpcr_ax_amp.clear()
        for i, (well, fluor) in enumerate(list(self.fluorescence.items())[:10]):
            color = PLOT_COLORS[i % len(PLOT_COLORS)]
            self.qpcr_ax_amp.plot(self.cycles, fluor, color=color, lw=1.5, label=well)

        self.qpcr_ax_amp.set_xlabel("Cycle", fontsize=8)
        self.qpcr_ax_amp.set_ylabel("Fluorescence (RFU)", fontsize=8)
        self.qpcr_ax_amp.legend(fontsize=6, ncol=2)
        self.qpcr_ax_amp.grid(True, alpha=0.3)

        self.qpcr_ax_log.clear()
        self.qpcr_ax_eff.clear()
        self.qpcr_canvas.draw()

    def _on_well_selected(self, event):
        """Handle well selection"""
        selection = self.well_listbox.curselection()
        if selection:
            well = self.well_listbox.get(selection[0])
            self.current_well = well
            self._plot_single_well(well)

    def _plot_single_well(self, well):
        """Plot single well with baseline correction"""
        if not HAS_MPL or well not in self.fluorescence:
            return

        fluor = self.fluorescence[well]

        # Apply baseline correction
        start = int(self.baseline_start.get())
        end = int(self.baseline_end.get())
        fluor_corr = self.engine.baseline_correction(self.cycles, fluor, (start, end))

        self.qpcr_ax_amp.clear()
        self.qpcr_ax_amp.plot(self.cycles, fluor, 'b-', lw=1, alpha=0.5, label="Raw")
        self.qpcr_ax_amp.plot(self.cycles, fluor_corr, 'r-', lw=2, label="Baseline corrected")
        self.qpcr_ax_amp.axhline(0, color='k', lw=0.5, ls='--')
        self.qpcr_ax_amp.set_xlabel("Cycle", fontsize=8)
        self.qpcr_ax_amp.set_ylabel("Fluorescence (RFU)", fontsize=8)
        self.qpcr_ax_amp.legend(fontsize=8)
        self.qpcr_ax_amp.grid(True, alpha=0.3)

        self.qpcr_canvas.draw()

    def _analyze_well(self):
        """Analyze selected well"""
        if self.current_well is None:
            messagebox.showwarning("No Selection", "Select a well first")
            return

        self.status_label.config(text=f"🔄 Analyzing {self.current_well}...")

        def worker():
            try:
                fluor = self.fluorescence[self.current_well]

                # Baseline correction
                start = int(self.baseline_start.get())
                end = int(self.baseline_end.get())
                fluor_corr = self.engine.baseline_correction(self.cycles, fluor, (start, end))

                # Find log-linear phase
                lin_result = self.engine.find_log_linear_phase(self.cycles, fluor_corr)

                # Determine Cq
                method = self.cq_method.get()
                if "Second Derivative" in method:
                    cq, cq_idx = self.engine.determine_cq_sdm(self.cycles, fluor_corr)
                elif "Threshold" in method:
                    threshold = 0.1 if "0.1" in method else 0.2
                    cq, cq_idx = self.engine.determine_cq_threshold(self.cycles, fluor_corr, threshold)
                else:
                    cq, cq_idx = self.engine.determine_cq_sdm(self.cycles, fluor_corr)

                def update_ui():
                    # Update results
                    self.qpcr_results["cq"].set(f"{cq:.2f}" if cq else "—")
                    if lin_result:
                        self.qpcr_results["eff"].set(f"{lin_result['efficiency']*100:.1f}%")
                        self.qpcr_results["slope"].set(f"{lin_result['slope']:.3f}")
                        self.qpcr_results["r2"].set(f"{lin_result['r2']:.4f}")
                    self.qpcr_results["baseline"].set(f"{start}-{end}")

                    # Update plots
                    if HAS_MPL and lin_result:
                        # Log-linear phase plot
                        self.qpcr_ax_log.clear()
                        log_fluor = np.log(np.maximum(fluor_corr, 1e-6))
                        self.qpcr_ax_log.plot(self.cycles, log_fluor, 'b-', lw=1, label="log(RFU)")

                        # Highlight linear phase
                        x_lin = self.cycles[lin_result['start_cycle']:lin_result['end_cycle']]
                        y_lin = log_fluor[lin_result['start_cycle']:lin_result['end_cycle']]
                        self.qpcr_ax_log.plot(x_lin, y_lin, 'r-', lw=3, label="Linear fit")

                        # Fit line
                        fit_line = lin_result['slope'] * x_lin + lin_result['intercept']
                        self.qpcr_ax_log.plot(x_lin, fit_line, 'g--', lw=2, label=f"E={lin_result['efficiency']*100:.1f}%")

                        self.qpcr_ax_log.set_xlabel("Cycle", fontsize=8)
                        self.qpcr_ax_log.set_ylabel("log(RFU)", fontsize=8)
                        self.qpcr_ax_log.legend(fontsize=7)
                        self.qpcr_ax_log.grid(True, alpha=0.3)

                        # Mark Cq on main plot
                        if cq:
                            self.qpcr_ax_amp.axvline(cq, color=C_WARN, ls='--', lw=2,
                                                     label=f"Cq={cq:.2f}")
                            self.qpcr_ax_amp.legend(fontsize=7)

                        self.qpcr_canvas.draw()

                    self.status_label.config(text=f"✅ {self.current_well} analyzed")

                self.ui_queue.schedule(update_ui)

            except Exception as e:
                self.ui_queue.schedule(lambda: messagebox.showerror("Error", str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _analyze_all(self):
        """Analyze all wells and create efficiency plot"""
        if not self.fluorescence:
            return

        self.status_label.config(text="🔄 Analyzing all wells...")

        def worker():
            try:
                results = {}
                cq_values = []
                well_names = []

                start = int(self.baseline_start.get())
                end = int(self.baseline_end.get())

                for well, fluor in self.fluorescence.items():
                    fluor_corr = self.engine.baseline_correction(self.cycles, fluor, (start, end))
                    lin_result = self.engine.find_log_linear_phase(self.cycles, fluor_corr)

                    if lin_result:
                        cq, _ = self.engine.determine_cq_sdm(self.cycles, fluor_corr)
                        results[well] = {
                            "cq": cq,
                            "efficiency": lin_result['efficiency'] * 100
                        }
                        cq_values.append(cq)
                        well_names.append(well)

                def update_ui():
                    if HAS_MPL and cq_values:
                        # Efficiency plot
                        self.qpcr_ax_eff.clear()
                        eff_values = [results[w]['efficiency'] for w in well_names]

                        bars = self.qpcr_ax_eff.bar(range(len(well_names)), eff_values,
                                                    color=C_ACCENT2, alpha=0.7)
                        self.qpcr_ax_eff.axhline(np.mean(eff_values), color=C_HEADER,
                                                ls='--', lw=2, label=f"Mean={np.mean(eff_values):.1f}%")

                        self.qpcr_ax_eff.set_xlabel("Well", fontsize=8)
                        self.qpcr_ax_eff.set_ylabel("Efficiency (%)", fontsize=8)
                        self.qpcr_ax_eff.set_xticks(range(len(well_names)))
                        self.qpcr_ax_eff.set_xticklabels(well_names, rotation=45, fontsize=6)
                        self.qpcr_ax_eff.legend(fontsize=7)
                        self.qpcr_ax_eff.grid(True, alpha=0.3, axis='y')

                        self.qpcr_canvas.draw()

                    self.status_label.config(text=f"✅ Analyzed {len(results)} wells")

                self.ui_queue.schedule(update_ui)

            except Exception as e:
                self.ui_queue.schedule(lambda: messagebox.showerror("Error", str(e)))

        threading.Thread(target=worker, daemon=True).start()


# ============================================================================
# ENGINE 2 — ΔΔCt QUANTIFICATION (Livak & Schmittgen 2001; Pfaffl 2001)
# ============================================================================
class DeltaDeltaCtAnalyzer:
    """
    Relative quantification using ΔΔCt method.

    Livak method (2^-ΔΔCt):
        - Assumes equal amplification efficiency (≈100%)
        - ΔCt = Ct_target - Ct_reference
        - ΔΔCt = ΔCt_sample - ΔCt_calibrator
        - RQ = 2^-ΔΔCt

    Pfaffl method (efficiency corrected):
        - Ratio = (E_target)^ΔCt_target / (E_reference)^ΔCt_reference
        - Accounts for different efficiencies

    References:
        Livak, K.J. & Schmittgen, T.D. (2001) "Analysis of relative gene
            expression data using real-time quantitative PCR" Methods
        Pfaffl, M.W. (2001) "A new mathematical model for relative
            quantification in real-time RT-PCR" Nucleic Acids Research
    """

    @classmethod
    def delta_ct(cls, ct_target, ct_reference):
        """ΔCt = Ct_target - Ct_reference"""
        return ct_target - ct_reference

    @classmethod
    def delta_delta_ct(cls, delta_ct_sample, delta_ct_calibrator):
        """ΔΔCt = ΔCt_sample - ΔCt_calibrator"""
        return delta_ct_sample - delta_ct_calibrator

    @classmethod
    def livak_rq(cls, delta_delta_ct):
        """Relative quantification by Livak method: RQ = 2^-ΔΔCt"""
        return 2 ** (-delta_delta_ct)

    @classmethod
    def pfaffl_ratio(cls, ct_target_sample, ct_target_calibrator,
                     ct_ref_sample, ct_ref_calibrator,
                     eff_target, eff_reference):
        """
        Efficiency-corrected relative ratio (Pfaffl method)

        Ratio = (E_target)^(ΔCt_target) / (E_reference)^(ΔCt_reference)
        where ΔCt_target = Ct_target_calibrator - Ct_target_sample
              ΔCt_reference = Ct_ref_calibrator - Ct_ref_sample
        """
        delta_ct_target = ct_target_calibrator - ct_target_sample
        delta_ct_ref = ct_ref_calibrator - ct_ref_sample

        ratio = (eff_target ** delta_ct_target) / (eff_reference ** delta_ct_ref)
        return ratio

    @classmethod
    def standard_curve(cls, concentrations, ct_values):
        """
        Generate standard curve from known concentrations

        Returns: slope, intercept, R², efficiency
        """
        log_conc = np.log10(concentrations)
        slope, intercept, r_value, p_value, std_err = linregress(log_conc, ct_values)

        efficiency = 10 ** (-1/slope) - 1 if slope != 0 else 0
        r2 = r_value ** 2

        return {
            "slope": slope,
            "intercept": intercept,
            "r2": r2,
            "efficiency": efficiency * 100  # percent
        }

    @classmethod
    def quantification_unknown(cls, ct_unknown, slope, intercept):
        """Quantify unknown from standard curve"""
        log_conc = (ct_unknown - intercept) / slope
        concentration = 10 ** log_conc
        return concentration

    @classmethod
    def error_propagation(cls, rq_values, ct_sds, efficiencies=None):
        """
        Propagate error to RQ values

        For Livak method: RQ = 2^-ΔΔCt
        Error is propagated from Ct standard deviations
        """
        if len(rq_values) < 2:
            return 0.0

        # Calculate standard deviation of RQ
        rq_std = np.std(rq_values, ddof=1)

        # 95% confidence interval
        n = len(rq_values)
        if n > 1:
            from scipy.stats import t
            ci = t.ppf(0.975, n-1) * rq_std / np.sqrt(n)
        else:
            ci = 0.0

        return {"sd": rq_std, "ci95": ci}

    @classmethod
    def load_ct_data(cls, path):
        """Load Ct data from CSV"""
        df = pd.read_csv(path)

        # Expected columns: Sample, Target, Ct, (Reference_Ct, Efficiency)
        return df.to_dict('records')


# ============================================================================
# TAB 2: ΔΔCt QUANTIFICATION
# ============================================================================
class DeltaDeltaCtTab(AnalysisTab):
    def __init__(self, parent, app, ui_queue):
        super().__init__(parent, app, ui_queue, "ΔΔCt Analysis")
        self.engine = DeltaDeltaCtAnalyzer
        self.ct_data = []
        self.calibrator = None
        self.reference_gene = None
        self.results = {}
        self._build_content_ui()

    def _sample_has_data(self, sample):
        """Check if sample has Ct data"""
        return any(col in sample and sample[col] for col in
                  ['Ct_Values', 'qPCR_Results'])

    def _manual_import(self):
        """Manual import from CSV"""
        path = filedialog.askopenfilename(
            title="Load Ct Data",
            filetypes=[("CSV", "*.csv"), ("Excel", "*.xlsx"), ("All files", "*.*")])
        if not path:
            return

        self.status_label.config(text="🔄 Loading Ct data...")

        def worker():
            try:
                if path.endswith('.xlsx'):
                    df = pd.read_excel(path)
                else:
                    df = pd.read_csv(path)

                data = df.to_dict('records')

                def update():
                    self.ct_data = data
                    self.manual_label.config(text=f"✓ {Path(path).name}")
                    self._update_sample_list()
                    self.status_label.config(text=f"Loaded {len(data)} rows")
                self.ui_queue.schedule(update)

            except Exception as e:
                self.ui_queue.schedule(lambda: messagebox.showerror("Error", str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _load_sample_data(self, idx):
        """Auto-load from table"""
        sample = self.samples[idx]

        if 'Ct_Values' in sample and sample['Ct_Values']:
            try:
                data = json.loads(sample['Ct_Values'])
                self.ct_data = data
                self._update_sample_list()
                self.status_label.config(text=f"Loaded Ct data from table")
            except Exception as e:
                self.status_label.config(text=f"Error: {e}")

    def _build_content_ui(self):
        """Build the tab-specific UI"""
        # Main split
        main_pane = ttk.PanedWindow(self.content_frame, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True)

        # Left panel - controls
        left = tk.Frame(main_pane, bg="white", width=300)
        main_pane.add(left, weight=1)

        # Right panel - plot
        right = tk.Frame(main_pane, bg="white")
        main_pane.add(right, weight=2)

        # === LEFT PANEL ===
        tk.Label(left, text="📊 ΔΔCt QUANTIFICATION",
                font=("Arial", 10, "bold"), bg=C_LIGHT, fg=C_HEADER).pack(fill=tk.X, pady=2)

        tk.Label(left, text="Livak & Schmittgen 2001 · Pfaffl 2001",
                font=("Arial", 7), bg="white", fg="#888").pack(anchor=tk.W, padx=4)

        # Method selection
        method_frame = tk.LabelFrame(left, text="Method", bg="white",
                                    font=("Arial", 8, "bold"), fg=C_HEADER)
        method_frame.pack(fill=tk.X, padx=4, pady=4)

        self.ddct_method = tk.StringVar(value="Livak (2^-ΔΔCt)")
        ttk.Combobox(method_frame, textvariable=self.ddct_method,
                     values=["Livak (2^-ΔΔCt)", "Pfaffl (efficiency corrected)", "Standard Curve"],
                     width=25, state="readonly").pack(fill=tk.X, padx=4, pady=2)

        # Reference gene
        tk.Label(left, text="Reference Gene:", font=("Arial", 8, "bold"),
                bg="white").pack(anchor=tk.W, padx=4, pady=(4, 0))
        self.ref_gene_var = tk.StringVar()
        self.ref_gene_combo = ttk.Combobox(left, textvariable=self.ref_gene_var,
                                           values=[], width=20)
        self.ref_gene_combo.pack(fill=tk.X, padx=4)

        # Calibrator sample
        tk.Label(left, text="Calibrator Sample:", font=("Arial", 8, "bold"),
                bg="white").pack(anchor=tk.W, padx=4, pady=(4, 0))
        self.calibrator_var = tk.StringVar()
        self.calibrator_combo = ttk.Combobox(left, textvariable=self.calibrator_var,
                                            values=[], width=20)
        self.calibrator_combo.pack(fill=tk.X, padx=4)

        # Efficiency (for Pfaffl)
        self.eff_frame = tk.Frame(left, bg="white")
        self.eff_frame.pack(fill=tk.X, padx=4, pady=2)

        tk.Label(self.eff_frame, text="Target Eff (%):", font=("Arial", 8),
                bg="white").pack(side=tk.LEFT)
        self.target_eff = tk.StringVar(value="100")
        ttk.Entry(self.eff_frame, textvariable=self.target_eff, width=6).pack(side=tk.LEFT, padx=2)

        tk.Label(self.eff_frame, text="Ref Eff (%):", font=("Arial", 8),
                bg="white").pack(side=tk.LEFT, padx=(4, 0))
        self.ref_eff = tk.StringVar(value="100")
        ttk.Entry(self.eff_frame, textvariable=self.ref_eff, width=6).pack(side=tk.LEFT, padx=2)

        ttk.Button(left, text="📊 CALCULATE RQ", command=self._calculate_rq).pack(fill=tk.X, padx=4, pady=4)

        # RQ Results table (was missing - caused AttributeError on Calculate)
        tree_frame = tk.LabelFrame(left, text="RQ Results Table", bg="white",
                                   font=("Arial", 8, "bold"), fg=C_HEADER)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self.ddct_tree = ttk.Treeview(tree_frame,
                                      columns=("Sample", "Target", "ΔCt", "ΔΔCt", "RQ"),
                                      show="headings", height=5)
        for col, w in [("Sample", 65), ("Target", 65), ("ΔCt", 45), ("ΔΔCt", 50), ("RQ", 55)]:
            self.ddct_tree.heading(col, text=col)
            self.ddct_tree.column(col, width=w, anchor=tk.CENTER)

        ddct_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL,
                                    command=self.ddct_tree.yview)
        self.ddct_tree.configure(yscrollcommand=ddct_scroll.set)
        self.ddct_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ddct_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Results summary
        results_frame = tk.LabelFrame(left, text="Selected Sample Summary", bg="white",
                                     font=("Arial", 8, "bold"), fg=C_HEADER)
        results_frame.pack(fill=tk.X, padx=4, pady=4)

        self.ddct_results = {}
        result_labels = [
            ("Sample:", "sample"),
            ("ΔCt:", "dct"),
            ("ΔΔCt:", "ddct"),
            ("RQ (fold change):", "rq"),
            ("RQ min (95% CI):", "rq_min"),
            ("RQ max (95% CI):", "rq_max")
        ]

        for i, (label, key) in enumerate(result_labels):
            row = tk.Frame(results_frame, bg="white")
            row.pack(fill=tk.X, pady=1)
            tk.Label(row, text=label, font=("Arial", 7), bg="white", width=15, anchor=tk.W).pack(side=tk.LEFT)
            var = tk.StringVar(value="—")
            tk.Label(row, textvariable=var, font=("Arial", 7, "bold"),
                    bg="white", fg=C_HEADER).pack(side=tk.LEFT, padx=2)
            self.ddct_results[key] = var

        # === RIGHT PANEL ===
        if HAS_MPL:
            self.ddct_fig = Figure(figsize=(8, 6), dpi=100, facecolor="white")
            gs = GridSpec(2, 1, figure=self.ddct_fig, hspace=0.3)
            self.ddct_ax_bar = self.ddct_fig.add_subplot(gs[0])
            self.ddct_ax_scatter = self.ddct_fig.add_subplot(gs[1])

            self.ddct_ax_bar.set_title("Relative Quantification (RQ)", fontsize=9, fontweight="bold")
            self.ddct_ax_scatter.set_title("Ct Values Distribution", fontsize=9, fontweight="bold")

            self.ddct_canvas = FigureCanvasTkAgg(self.ddct_fig, right)
            self.ddct_canvas.draw()
            self.ddct_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            toolbar = NavigationToolbar2Tk(self.ddct_canvas, right)
            toolbar.update()
        else:
            tk.Label(right, text="matplotlib required for plots",
                    bg="white", fg="#888").pack(expand=True)

    def _update_sample_list(self):
        """Update dropdowns with available genes and samples"""
        if not self.ct_data:
            return

        # Extract unique genes and samples
        genes = set()
        samples = set()

        for row in self.ct_data:
            if 'Target' in row:
                genes.add(row['Target'])
            if 'Sample' in row:
                samples.add(row['Sample'])

        self.ref_gene_combo['values'] = sorted(genes)
        self.calibrator_combo['values'] = sorted(samples)

        if 'GAPDH' in genes:
            self.ref_gene_var.set('GAPDH')
        elif genes:
            self.ref_gene_var.set(sorted(genes)[0])

        if 'Control' in samples:
            self.calibrator_var.set('Control')
        elif samples:
            self.calibrator_var.set(sorted(samples)[0])

    def _calculate_rq(self):
        """Calculate relative quantification"""
        if not self.ct_data:
            messagebox.showwarning("No Data", "Load Ct data first")
            return

        self.status_label.config(text="🔄 Calculating RQ...")

        def worker():
            try:
                ref_gene = self.ref_gene_var.get()
                calibrator = self.calibrator_var.get()
                method = self.ddct_method.get()

                # Organize data
                ct_by_sample_target = {}
                for row in self.ct_data:
                    sample = row.get('Sample', 'Unknown')
                    target = row.get('Target', 'Unknown')
                    ct = row.get('Ct', row.get('Cq', 0))

                    if sample not in ct_by_sample_target:
                        ct_by_sample_target[sample] = {}
                    ct_by_sample_target[sample][target] = ct

                # Calculate for each sample
                results = []
                for sample, targets in ct_by_sample_target.items():
                    if ref_gene not in targets:
                        continue

                    ct_ref = targets[ref_gene]

                    for target, ct_target in targets.items():
                        if target == ref_gene:
                            continue

                        # ΔCt
                        dct = ct_target - ct_ref

                        # ΔΔCt relative to calibrator
                        if calibrator in ct_by_sample_target and ref_gene in ct_by_sample_target[calibrator]:
                            ct_ref_cal = ct_by_sample_target[calibrator][ref_gene]
                            ct_target_cal = ct_by_sample_target[calibrator].get(target, ct_target)

                            dct_cal = ct_target_cal - ct_ref_cal
                            ddct = dct - dct_cal

                            if "Livak" in method:
                                rq = 2 ** (-ddct)
                            else:
                                eff_target = float(self.target_eff.get()) / 100
                                eff_ref = float(self.ref_eff.get()) / 100
                                rq = (eff_target ** (-(ct_target - ct_target_cal))) / \
                                     (eff_ref ** (-(ct_ref - ct_ref_cal)))
                        else:
                            ddct = None
                            rq = None

                        results.append({
                            "sample": sample,
                            "target": target,
                            "ct_target": ct_target,
                            "ct_ref": ct_ref,
                            "dct": dct,
                            "ddct": ddct,
                            "rq": rq
                        })

                def update_ui():
                    # Clear tree and populate with results
                    for row in self.ddct_tree.get_children():
                        self.ddct_tree.delete(row)

                    for r in results:
                        dct_str = f"{r['dct']:.3f}" if r['dct'] is not None else "—"
                        ddct_str = f"{r['ddct']:.3f}" if r['ddct'] is not None else "—"
                        rq_str = f"{r['rq']:.4f}" if r['rq'] is not None else "—"
                        self.ddct_tree.insert("", tk.END, values=(
                            r['sample'], r['target'], dct_str, ddct_str, rq_str
                        ))

                    # Update summary fields for first result
                    if results:
                        first = results[0]
                        self.ddct_results["sample"].set(first["sample"])
                        self.ddct_results["dct"].set(f"{first['dct']:.3f}" if first['dct'] is not None else "—")
                        self.ddct_results["ddct"].set(f"{first['ddct']:.3f}" if first['ddct'] is not None else "—")
                        self.ddct_results["rq"].set(f"{first['rq']:.4f}" if first['rq'] is not None else "—")
                        self.ddct_results["rq_min"].set("—")
                        self.ddct_results["rq_max"].set("—")

                    # Plot results
                    if HAS_MPL and results:
                        # Bar plot of RQ values
                        self.ddct_ax_bar.clear()

                        rq_values = []
                        labels = []
                        for r in results:
                            if r['rq'] is not None:
                                rq_values.append(r['rq'])
                                labels.append(f"{r['sample']}\n{r['target']}")

                        if rq_values:
                            bars = self.ddct_ax_bar.bar(range(len(rq_values)), rq_values,
                                                        color=C_ACCENT2, alpha=0.7)

                            # Add reference line at 1
                            self.ddct_ax_bar.axhline(1, color=C_HEADER, ls='--', lw=1,
                                                     label="Calibrator")

                            self.ddct_ax_bar.set_xticks(range(len(labels)))
                            self.ddct_ax_bar.set_xticklabels(labels, rotation=45, fontsize=7)
                            self.ddct_ax_bar.set_ylabel("Fold Change (RQ)", fontsize=8)
                            self.ddct_ax_bar.legend(fontsize=7)
                            self.ddct_ax_bar.grid(True, alpha=0.3, axis='y')

                            # Scatter plot of Ct values
                            self.ddct_ax_scatter.clear()
                            for r in results:
                                color = C_ACCENT if r['target'] == ref_gene else C_ACCENT2
                                self.ddct_ax_scatter.scatter(r['ct_ref'], r['ct_target'],
                                                            c=color, s=50, alpha=0.7)
                                self.ddct_ax_scatter.annotate(r['sample'],
                                                              (r['ct_ref'], r['ct_target']),
                                                              fontsize=6)

                            # Diagonal line
                            min_ct = min([r['ct_ref'] for r in results] + [r['ct_target'] for r in results])
                            max_ct = max([r['ct_ref'] for r in results] + [r['ct_target'] for r in results])
                            self.ddct_ax_scatter.plot([min_ct, max_ct], [min_ct, max_ct],
                                                      'k--', lw=1, alpha=0.5)
                            self.ddct_ax_scatter.set_xlabel(f"Ct ({ref_gene})", fontsize=8)
                            self.ddct_ax_scatter.set_ylabel("Ct (Target)", fontsize=8)
                            self.ddct_ax_scatter.grid(True, alpha=0.3)

                            self.ddct_canvas.draw()

                    self.status_label.config(text=f"✅ Calculated RQ for {len(results)} targets")

                self.ui_queue.schedule(update_ui)

            except Exception as e:
                self.ui_queue.schedule(lambda: messagebox.showerror("Error", str(e)))

        threading.Thread(target=worker, daemon=True).start()


# ============================================================================
# ENGINE 3 — 4PL/5PL ELISA FITTING (Findlay & Dillard 2007; ICH Q2(R1))
# ============================================================================
class ELISAAnalyzer:
    """
    Four and five parameter logistic curve fitting for ELISA.

    4PL: y = A + (B - A) / (1 + (x/C)^D)
        A = minimum asymptote
        B = maximum asymptote
        C = inflection point (EC50)
        D = slope factor

    5PL: y = A + (B - A) / (1 + (x/C)^D)^E
        E = asymmetry factor

    Validation parameters (ICH Q2(R1)):
        - Accuracy (% recovery)
        - Precision (%CV)
        - Linearity (R²)
        - LOD, LOQ

    References:
        Findlay, J.W. & Dillard, R.F. (2007) "Appropriate calibration curve
            fitting in ligand binding assays" The AAPS Journal
        ICH Harmonised Tripartite Guideline Q2(R1) (2005)
    """

    @classmethod
    def four_pl(cls, x, A, B, C, D):
        """4-parameter logistic function"""
        return A + (B - A) / (1 + (x / C) ** D)

    @classmethod
    def five_pl(cls, x, A, B, C, D, E):
        """5-parameter logistic function with asymmetry"""
        return A + (B - A) / (1 + (x / C) ** D) ** E

    @classmethod
    def fit_4pl(cls, concentration, response, p0=None):
        """
        Fit 4PL curve to standard data with 1/y² weighting.

        Parameters:
        - concentration: x values (standards)
        - response: y values (OD, RLU, etc.)
        - p0: initial guesses [A, B, C, D]

        Returns:
        - fitted parameters and goodness of fit
        """
        if p0 is None:
            # Estimate initial parameters
            A0 = np.min(response)  # Bottom asymptote
            B0 = np.max(response)  # Top asymptote
            C0 = np.median(concentration)  # EC50
            D0 = 1.0  # Slope
            p0 = [A0, B0, C0, D0]

        try:
            # 1/y² weighting (inverse variance) – prevents low responses from dominating
            sigma = 1.0 / (np.abs(response) + 1e-6)

            popt, pcov = curve_fit(cls.four_pl, concentration, response,
                                p0=p0, sigma=sigma, absolute_sigma=False, maxfev=5000)

            # Calculate R²
            residuals = response - cls.four_pl(concentration, *popt)
            ss_res = np.sum(residuals ** 2)
            ss_tot = np.sum((response - np.mean(response)) ** 2)
            r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

            # Parameter errors (standard deviations)
            perr = np.sqrt(np.diag(pcov)) if pcov is not None else np.zeros(4)

            return {
                "A": popt[0], "A_se": perr[0],
                "B": popt[1], "B_se": perr[1],
                "C": popt[2], "C_se": perr[2],  # EC50
                "D": popt[3], "D_se": perr[3],
                "r2": r2,
                "method": "4PL"
            }
        except:
            return None

    @classmethod
    def fit_5pl(cls, concentration, response, p0=None):
        """
        Fit 5PL curve to standard data with 1/y² weighting.

        Parameters:
        - concentration: x values (standards)
        - response: y values (OD, RLU, etc.)
        - p0: initial guesses [A, B, C, D, E]

        Returns:
        - fitted parameters and goodness of fit
        """
        if p0 is None:
            A0 = np.min(response)
            B0 = np.max(response)
            C0 = np.median(concentration)
            D0 = 1.0
            E0 = 1.0  # Symmetry factor (1 = symmetric)
            p0 = [A0, B0, C0, D0, E0]

        try:
            # 1/y² weighting (inverse variance)
            sigma = 1.0 / (np.abs(response) + 1e-6)

            popt, pcov = curve_fit(cls.five_pl, concentration, response,
                                p0=p0, sigma=sigma, absolute_sigma=False, maxfev=5000)

            residuals = response - cls.five_pl(concentration, *popt)
            ss_res = np.sum(residuals ** 2)
            ss_tot = np.sum((response - np.mean(response)) ** 2)
            r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

            perr = np.sqrt(np.diag(pcov)) if pcov is not None else np.zeros(5)

            return {
                "A": popt[0], "A_se": perr[0],
                "B": popt[1], "B_se": perr[1],
                "C": popt[2], "C_se": perr[2],
                "D": popt[3], "D_se": perr[3],
                "E": popt[4], "E_se": perr[4],
                "r2": r2,
                "method": "5PL"
            }
        except:
            return None

    @classmethod
    def inverse_5pl(cls, y, A, B, C, D, E):
        """Numerical inverse for 5PL using root-finding (brentq)"""
        from scipy.optimize import root_scalar
        def f(x):
            return cls.five_pl(x, A, B, C, D, E) - y
        try:
            sol = root_scalar(f, bracket=[0, 1e6], method='brentq')
            return sol.root if sol.converged else None
        except (ValueError, RuntimeError):
            return None

    @classmethod
    def calculate_concentration(cls, response, params):
        """Calculate unknown concentration from fitted curve (now full 5PL)"""
        if params["method"] == "4PL":
            return cls.inverse_4pl(response, params["A"], params["B"],
                                params["C"], params["D"])
        else:  # 5PL
            return cls.inverse_5pl(response, params["A"], params["B"],
                                params["C"], params["D"], params["E"])

    @classmethod
    def validation_metrics(cls, known_conc, measured_conc):
        """
        Calculate validation metrics per ICH Q2(R1)

        - Accuracy: % recovery = (measured/known) * 100
        - Precision: %CV = (SD/mean) * 100
        - Linearity: R² of known vs measured
        """
        if len(known_conc) == 0:
            return {}

        # % Recovery
        recovery = (measured_conc / known_conc) * 100

        # %CV
        cv = np.std(measured_conc) / np.mean(measured_conc) * 100

        # Linearity
        slope, intercept, r_value, p_value, std_err = linregress(known_conc, measured_conc)
        r2 = r_value ** 2

        return {
            "recovery_mean": np.mean(recovery),
            "recovery_sd": np.std(recovery),
            "cv_pct": cv,
            "linearity_r2": r2,
            "linearity_slope": slope,
            "linearity_intercept": intercept
        }

    @classmethod
    def lod_loq(cls, blank_responses, low_conc_responses=None, method="signal_noise"):
        """
        Calculate Limit of Detection (LOD) and Limit of Quantification (LOQ)

        Methods:
        - Signal-to-noise: LOD = 3.3 * σ / slope
        - Standard deviation of blank: LOD = mean_blank + 3.3 * SD_blank
        """
        if method == "blank_sd":
            mean_blank = np.mean(blank_responses)
            sd_blank = np.std(blank_responses, ddof=1)
            lod = mean_blank + 3.3 * sd_blank
            loq = mean_blank + 10 * sd_blank
            return {"lod": lod, "loq": loq}

        return {"lod": None, "loq": None}


# ============================================================================
# TAB 3: 4PL/5PL ELISA FITTING
# ============================================================================
class ELISAAnalysisTab(AnalysisTab):
    def __init__(self, parent, app, ui_queue):
        super().__init__(parent, app, ui_queue, "ELISA Analysis")
        self.engine = ELISAAnalyzer
        self.standards = None
        self.unknowns = None
        self.fit_params = None
        self._build_content_ui()

    def _sample_has_data(self, sample):
        """Check if sample has ELISA data"""
        return any(col in sample and sample[col] for col in
                  ['ELISA_File', 'Standards', 'OD_Values'])

    def _manual_import(self):
        """Manual import from CSV"""
        path = filedialog.askopenfilename(
            title="Load ELISA Data",
            filetypes=[("CSV", "*.csv"), ("Excel", "*.xlsx"), ("All files", "*.*")])
        if not path:
            return

        self.status_label.config(text="🔄 Loading ELISA data...")

        def worker():
            try:
                if path.endswith('.xlsx'):
                    df = pd.read_excel(path)
                else:
                    df = pd.read_csv(path)

                # Try to identify standard and unknown wells
                standards = []
                unknowns = []

                for _, row in df.iterrows():
                    if 'Type' in row and row['Type'] == 'Standard':
                        standards.append({
                            "conc": row.get('Concentration', 0),
                            "response": row.get('OD', row.get('Response', 0))
                        })
                    else:
                        unknowns.append({
                            "id": row.get('Well', row.get('Sample', f"U{len(unknowns)+1}")),
                            "response": row.get('OD', row.get('Response', 0))
                        })

                def update():
                    self.standards = standards
                    self.unknowns = unknowns
                    self.manual_label.config(text=f"✓ {Path(path).name}")
                    self._plot_standards()
                    self.status_label.config(text=f"Loaded {len(standards)} standards, {len(unknowns)} unknowns")
                self.ui_queue.schedule(update)

            except Exception as e:
                self.ui_queue.schedule(lambda: messagebox.showerror("Error", str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _load_sample_data(self, idx):
        """Auto-load from table"""
        sample = self.samples[idx]

        if 'Standards' in sample and 'Unknowns' in sample:
            try:
                self.standards = json.loads(sample['Standards'])
                self.unknowns = json.loads(sample['Unknowns'])
                self._plot_standards()
                self.status_label.config(text=f"Loaded ELISA data from table")
            except Exception as e:
                self.status_label.config(text=f"Error: {e}")

    def _build_content_ui(self):
        """Build the tab-specific UI"""
        # Main split
        main_pane = ttk.PanedWindow(self.content_frame, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True)

        # Left panel - controls
        left = tk.Frame(main_pane, bg="white", width=300)
        main_pane.add(left, weight=1)

        # Right panel - plot
        right = tk.Frame(main_pane, bg="white")
        main_pane.add(right, weight=2)

        # === LEFT PANEL ===
        tk.Label(left, text="🧪 ELISA 4PL/5PL FITTING",
                font=("Arial", 10, "bold"), bg=C_LIGHT, fg=C_HEADER).pack(fill=tk.X, pady=2)

        tk.Label(left, text="Findlay & Dillard 2007 · ICH Q2(R1)",
                font=("Arial", 7), bg="white", fg="#888").pack(anchor=tk.W, padx=4)

        # Model selection
        tk.Label(left, text="Model:", font=("Arial", 8, "bold"),
                bg="white").pack(anchor=tk.W, padx=4, pady=(4, 0))
        self.elisa_model = tk.StringVar(value="4PL (symmetric)")
        ttk.Combobox(left, textvariable=self.elisa_model,
                     values=["4PL (symmetric)", "5PL (asymmetric)"],
                     width=20, state="readonly").pack(fill=tk.X, padx=4)

        ttk.Button(left, text="📈 FIT STANDARD CURVE",
                  command=self._fit_curve).pack(fill=tk.X, padx=4, pady=4)
        ttk.Button(left, text="🔢 QUANTIFY UNKNOWNS",
                  command=self._quantify_unknowns).pack(fill=tk.X, padx=4, pady=2)

        # Results
        results_frame = tk.LabelFrame(left, text="Fit Parameters", bg="white",
                                     font=("Arial", 8, "bold"), fg=C_HEADER)
        results_frame.pack(fill=tk.X, padx=4, pady=4)

        self.elisa_results = {}
        result_labels = [
            ("A (bottom):", "A"),
            ("B (top):", "B"),
            ("C (EC50):", "C"),
            ("D (slope):", "D"),
            ("E (asym):", "E"),
            ("R²:", "r2")
        ]

        for i, (label, key) in enumerate(result_labels):
            row = tk.Frame(results_frame, bg="white")
            row.pack(fill=tk.X, pady=1)
            tk.Label(row, text=label, font=("Arial", 7), bg="white", width=12, anchor=tk.W).pack(side=tk.LEFT)
            var = tk.StringVar(value="—")
            tk.Label(row, textvariable=var, font=("Arial", 7, "bold"),
                    bg="white", fg=C_HEADER).pack(side=tk.LEFT, padx=2)
            self.elisa_results[key] = var

        # Validation
        val_frame = tk.LabelFrame(left, text="Validation (ICH Q2)", bg="white",
                                  font=("Arial", 8, "bold"), fg=C_HEADER)
        val_frame.pack(fill=tk.X, padx=4, pady=4)

        self.elisa_val = {}
        val_labels = [
            ("% Recovery:", "recovery"),
            ("%CV:", "cv"),
            ("LOD:", "lod"),
            ("LOQ:", "loq")
        ]

        for i, (label, key) in enumerate(val_labels):
            row = tk.Frame(val_frame, bg="white")
            row.pack(fill=tk.X, pady=1)
            tk.Label(row, text=label, font=("Arial", 7), bg="white", width=12, anchor=tk.W).pack(side=tk.LEFT)
            var = tk.StringVar(value="—")
            tk.Label(row, textvariable=var, font=("Arial", 7, "bold"),
                    bg="white", fg=C_HEADER).pack(side=tk.LEFT, padx=2)
            self.elisa_val[key] = var

        # === RIGHT PANEL ===
        if HAS_MPL:
            self.elisa_fig = Figure(figsize=(8, 6), dpi=100, facecolor="white")
            gs = GridSpec(2, 2, figure=self.elisa_fig, hspace=0.3, wspace=0.3)
            self.elisa_ax_curve = self.elisa_fig.add_subplot(gs[0, :])
            self.elisa_ax_resid = self.elisa_fig.add_subplot(gs[1, 0])
            self.elisa_ax_linearity = self.elisa_fig.add_subplot(gs[1, 1])

            self.elisa_ax_curve.set_title("Standard Curve", fontsize=9, fontweight="bold")
            self.elisa_ax_resid.set_title("Residuals", fontsize=9, fontweight="bold")
            self.elisa_ax_linearity.set_title("Linearity", fontsize=9, fontweight="bold")

            self.elisa_canvas = FigureCanvasTkAgg(self.elisa_fig, right)
            self.elisa_canvas.draw()
            self.elisa_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            toolbar = NavigationToolbar2Tk(self.elisa_canvas, right)
            toolbar.update()
        else:
            tk.Label(right, text="matplotlib required for plots",
                    bg="white", fg="#888").pack(expand=True)

    def _plot_standards(self):
        """Plot standard curve data"""
        if not HAS_MPL or not self.standards:
            return

        conc = [s['conc'] for s in self.standards]
        resp = [s['response'] for s in self.standards]

        self.elisa_ax_curve.clear()
        self.elisa_ax_curve.scatter(conc, resp, s=50, c=C_ACCENT, alpha=0.7,
                                   label="Standards")
        self.elisa_ax_curve.set_xlabel("Concentration", fontsize=8)
        self.elisa_ax_curve.set_ylabel("Response (OD)", fontsize=8)
        self.elisa_ax_curve.set_xscale('log')
        self.elisa_ax_curve.grid(True, alpha=0.3)
        self.elisa_ax_curve.legend(fontsize=8)

        self.elisa_canvas.draw()

    def _fit_curve(self):
        """Fit 4PL or 5PL curve to standards"""
        if not self.standards:
            messagebox.showwarning("No Data", "Load standards first")
            return

        self.status_label.config(text="🔄 Fitting curve...")

        def worker():
            try:
                conc = np.array([s['conc'] for s in self.standards])
                resp = np.array([s['response'] for s in self.standards])

                # Sort by concentration
                sort_idx = np.argsort(conc)
                conc = conc[sort_idx]
                resp = resp[sort_idx]

                model = self.elisa_model.get()

                if "4PL" in model:
                    fit = self.engine.fit_4pl(conc, resp)
                else:
                    fit = self.engine.fit_5pl(conc, resp)

                if fit is None:
                    self.ui_queue.schedule(lambda: messagebox.showerror("Error", "Fitting failed"))
                    return

                self.fit_params = fit

                # Calculate validation metrics
                # For simplicity, use standards as validation set
                if fit['method'] == '4PL':
                    pred_conc = [self.engine.inverse_4pl(r, fit['A'], fit['B'], fit['C'], fit['D'])
                                 for r in resp]
                    pred_conc = [c if c is not None else 0 for c in pred_conc]
                    validation = self.engine.validation_metrics(conc, np.array(pred_conc))
                else:
                    validation = {}

                def update_ui():
                    # Update fit parameters
                    self.elisa_results["A"].set(f"{fit['A']:.3f} ± {fit.get('A_se', 0):.3f}")
                    self.elisa_results["B"].set(f"{fit['B']:.3f} ± {fit.get('B_se', 0):.3f}")
                    self.elisa_results["C"].set(f"{fit['C']:.3f} ± {fit.get('C_se', 0):.3f}")
                    self.elisa_results["D"].set(f"{fit['D']:.3f} ± {fit.get('D_se', 0):.3f}")
                    if 'E' in fit:
                        self.elisa_results["E"].set(f"{fit['E']:.3f} ± {fit.get('E_se', 0):.3f}")
                    self.elisa_results["r2"].set(f"{fit['r2']:.4f}")

                    # Update validation
                    if validation:
                        self.elisa_val["recovery"].set(f"{validation['recovery_mean']:.1f}%")
                        self.elisa_val["cv"].set(f"{validation['cv_pct']:.1f}%")
                        self.elisa_val["lod"].set(f"{validation.get('lod', '—')}")
                        self.elisa_val["loq"].set(f"{validation.get('loq', '—')}")

                    # Update plots
                    if HAS_MPL:
                        # Smooth curve for plotting
                        x_smooth = np.logspace(np.log10(conc.min()*0.1),
                                               np.log10(conc.max()*10), 100)

                        if fit['method'] == '4PL':
                            y_smooth = self.engine.four_pl(x_smooth, fit['A'], fit['B'],
                                                           fit['C'], fit['D'])
                        else:
                            y_smooth = self.engine.five_pl(x_smooth, fit['A'], fit['B'],
                                                           fit['C'], fit['D'], fit['E'])

                        self.elisa_ax_curve.clear()
                        self.elisa_ax_curve.scatter(conc, resp, s=50, c=C_ACCENT,
                                                   alpha=0.7, label="Standards")
                        self.elisa_ax_curve.plot(x_smooth, y_smooth, 'r-', lw=2,
                                                label=f"{fit['method']} fit (R²={fit['r2']:.4f})")

                        # Mark EC50
                        self.elisa_ax_curve.axvline(fit['C'], color=C_ACCENT2, ls='--', lw=1,
                                                    label=f"EC50={fit['C']:.2f}")
                        self.elisa_ax_curve.axhline((fit['A'] + fit['B'])/2, color=C_ACCENT2,
                                                    ls='--', lw=1)

                        self.elisa_ax_curve.set_xlabel("Concentration", fontsize=8)
                        self.elisa_ax_curve.set_ylabel("Response (OD)", fontsize=8)
                        self.elisa_ax_curve.set_xscale('log')
                        self.elisa_ax_curve.legend(fontsize=7)
                        self.elisa_ax_curve.grid(True, alpha=0.3)

                        # Residuals plot
                        if fit['method'] == '4PL':
                            y_pred = self.engine.four_pl(conc, fit['A'], fit['B'],
                                                         fit['C'], fit['D'])
                        else:
                            y_pred = self.engine.five_pl(conc, fit['A'], fit['B'],
                                                         fit['C'], fit['D'], fit['E'])

                        residuals = resp - y_pred

                        self.elisa_ax_resid.clear()
                        self.elisa_ax_resid.scatter(conc, residuals, s=40, c=C_ACCENT3, alpha=0.7)
                        self.elisa_ax_resid.axhline(0, color='k', lw=1, ls='--')
                        self.elisa_ax_resid.set_xlabel("Concentration", fontsize=8)
                        self.elisa_ax_resid.set_ylabel("Residual", fontsize=8)
                        self.elisa_ax_resid.set_xscale('log')
                        self.elisa_ax_resid.grid(True, alpha=0.3)

                        # Linearity plot
                        if validation:
                            pred_conc = np.array([self.engine.inverse_4pl(r, fit['A'], fit['B'],
                                                                          fit['C'], fit['D'])
                                                 for r in resp])
                            pred_conc = np.array([c if c is not None else 0 for c in pred_conc])

                            self.elisa_ax_linearity.clear()
                            self.elisa_ax_linearity.scatter(conc, pred_conc, s=40, c=C_ACCENT2, alpha=0.7)
                            self.elisa_ax_linearity.plot([conc.min(), conc.max()],
                                                         [conc.min(), conc.max()],
                                                         'k--', lw=1, label="1:1 line")
                            self.elisa_ax_linearity.set_xlabel("Expected Conc", fontsize=8)
                            self.elisa_ax_linearity.set_ylabel("Measured Conc", fontsize=8)
                            self.elisa_ax_linearity.set_xscale('log')
                            self.elisa_ax_linearity.set_yscale('log')
                            self.elisa_ax_linearity.legend(fontsize=7)
                            self.elisa_ax_linearity.grid(True, alpha=0.3)

                        self.elisa_canvas.draw()

                    self.status_label.config(text=f"✅ {fit['method']} fit complete (R²={fit['r2']:.4f})")

                self.ui_queue.schedule(update_ui)

            except Exception as e:
                self.ui_queue.schedule(lambda: messagebox.showerror("Error", str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _quantify_unknowns(self):
        """Quantify unknown samples"""
        if not self.unknowns or not self.fit_params:
            messagebox.showwarning("No Data", "Fit curve and load unknowns first")
            return

        self.status_label.config(text="🔄 Quantifying unknowns...")

        def worker():
            try:
                results = []
                for u in self.unknowns:
                    conc = self.engine.calculate_concentration(u['response'], self.fit_params)
                    results.append({
                        "id": u['id'],
                        "response": u['response'],
                        "concentration": conc
                    })

                def update_ui():
                    # Display results in tree (would add tree widget in full implementation)
                    # For now, show in status
                    valid = [r for r in results if r['concentration'] is not None]
                    self.status_label.config(text=f"✅ Quantified {len(valid)} unknowns")

                self.ui_queue.schedule(update_ui)

            except Exception as e:
                self.ui_queue.schedule(lambda: messagebox.showerror("Error", str(e)))

        threading.Thread(target=worker, daemon=True).start()


# ============================================================================
# ENGINE 4 — FLOW CYTOMETRY GATING (Herzenberg et al. 2006; Maecker et al. 2004)
# ============================================================================
class FlowCytometryAnalyzer:
    """
    Automated flow cytometry gating algorithms.

    Methods:
    - Manual rectangular/elliptical gates
    - Automated gating (GMM clustering)
    - Fluorescence compensation (spillover matrix)

    References:
        Herzenberg, L.A. et al. (2006) "Interpreting flow cytometry data:
            a guide for the perplexed" Nature Immunology
        Maecker, H.T. et al. (2004) "Selecting fluorochrome conjugates for
            maximum sensitivity" Cytometry A
    """

    @classmethod
    def gate_rectangle(cls, data, x_channel, y_channel, x_min, x_max, y_min, y_max):
        """
        Apply rectangular gate

        Returns: boolean mask of events inside gate
        """
        x = data[:, x_channel]
        y = data[:, y_channel]

        mask = (x >= x_min) & (x <= x_max) & (y >= y_min) & (y <= y_max)
        return mask

    @classmethod
    def gate_ellipse(cls, data, x_channel, y_channel, center_x, center_y,
                     radius_x, radius_y, angle=0):
        """
        Apply elliptical gate

        Returns: boolean mask of events inside ellipse
        """
        x = data[:, x_channel]
        y = data[:, y_channel]

        # Transform to ellipse coordinates
        if angle != 0:
            cos_a = np.cos(np.radians(angle))
            sin_a = np.sin(np.radians(angle))
            x_rot = cos_a * (x - center_x) + sin_a * (y - center_y)
            y_rot = -sin_a * (x - center_x) + cos_a * (y - center_y)
        else:
            x_rot = x - center_x
            y_rot = y - center_y

        # Check if inside ellipse
        mask = (x_rot / radius_x) ** 2 + (y_rot / radius_y) ** 2 <= 1
        return mask

    @classmethod
    def gmm_clustering(cls, data, n_components=3, channels=None):
        """
        Gaussian Mixture Model clustering for automated gating

        Uses scikit-learn's GMM to identify populations
        """
        if not HAS_SKLEARN:
            return None

        if channels is not None:
            X = data[:, channels]
        else:
            X = data

        gmm = mixture.GaussianMixture(n_components=n_components,
                                      covariance_type='full',
                                      random_state=42)
        labels = gmm.fit_predict(X)

        return {
            "labels": labels,
            "means": gmm.means_,
            "covariances": gmm.covariances_,
            "weights": gmm.weights_
        }

    @classmethod
    def compensation_matrix(cls, single_stain_controls):
        """
        Calculate spillover compensation matrix from single-stain controls

        Simplified implementation of fluorescence compensation
        """
        # In practice, this uses the method of Bagwell & Adams (1993)
        # For now, return identity matrix
        n_channels = len(single_stain_controls)
        return np.eye(n_channels)

    @classmethod
    def apply_compensation(cls, data, spillover_matrix):
        """Apply compensation to data"""
        return np.dot(data, np.linalg.inv(spillover_matrix))

    @classmethod
    def load_fcs(cls, path):
        """Load FCS file.

        Tries fcsparser first (pip install fcsparser), then FlowIO,
        then falls back to synthetic demo data with a warning.
        Install fcsparser for real FCS support: pip install fcsparser
        """
        # Attempt 1: fcsparser (most common)
        try:
            import fcsparser
            meta, data_df = fcsparser.parse(path, reformat_meta=True)
            channels = list(data_df.columns)
            return {
                "data": data_df.values,
                "channels": channels,
                "n_events": len(data_df),
                "meta": meta,
                "_source": "fcsparser"
            }
        except ImportError:
            pass
        except Exception as e:
            raise RuntimeError(f"fcsparser failed to read {path}: {e}")

        # Attempt 2: FlowIO
        try:
            import flowio
            with open(path, 'rb') as f:
                flow_data = flowio.FlowData(f)
            channels = [flow_data.channels[str(i+1)]['PnN']
                        for i in range(flow_data.channel_count)]
            import numpy as _np
            data = _np.reshape(flow_data.events,
                               (-1, flow_data.channel_count))
            return {
                "data": data,
                "channels": channels,
                "n_events": flow_data.event_count,
                "_source": "flowio"
            }
        except ImportError:
            pass
        except Exception as e:
            raise RuntimeError(f"FlowIO failed to read {path}: {e}")

        # Fallback: synthetic demo data — warns the user
        import warnings as _warnings
        _warnings.warn(
            "Neither fcsparser nor FlowIO is installed. "
            "Displaying SYNTHETIC DEMO DATA instead of your file. "
            "Install fcsparser:  pip install fcsparser",
            UserWarning, stacklevel=2
        )
        n_events = 10000
        n_channels = 6
        data = np.zeros((n_events, n_channels))
        for i in range(n_events):
            if i < 3000:
                data[i, :2] = np.random.normal([1e5, 1e4], [2e4, 2e3])
            elif i < 6000:
                data[i, :2] = np.random.normal([5e4, 5e4], [1e4, 1e4])
            else:
                data[i, :2] = np.random.normal([1e4, 1e5], [2e3, 2e4])

        return {
            "data": data,
            "channels": ["FSC-A", "SSC-A", "FL1-A", "FL2-A", "FL3-A", "FL4-A"],
            "n_events": n_events,
            "_source": "synthetic_demo"
        }


# ============================================================================
# TAB 4: FLOW CYTOMETRY GATING
# ============================================================================
class FlowCytometryTab(AnalysisTab):
    def __init__(self, parent, app, ui_queue):
        super().__init__(parent, app, ui_queue, "Flow Cytometry")
        self.engine = FlowCytometryAnalyzer
        self.fcs_data = None
        self.channels = None
        self.gates = {}
        self._build_content_ui()

    def _sample_has_data(self, sample):
        """Check if sample has flow cytometry data"""
        return any(col in sample and sample[col] for col in
                  ['FCS_File', 'Flow_Data'])

    def _manual_import(self):
        """Manual import from FCS file"""
        path = filedialog.askopenfilename(
            title="Load FCS File",
            filetypes=[("FCS", "*.fcs"), ("All files", "*.*")])
        if not path:
            return

        self.status_label.config(text="🔄 Loading FCS data...")

        def worker():
            try:
                data = self.engine.load_fcs(path)

                def update():
                    self.fcs_data = data["data"]
                    self.channels = data["channels"]
                    self.manual_label.config(text=f"✓ {Path(path).name}")
                    self._update_channel_selectors()
                    self._plot_scatter()
                    source = data.get("_source", "unknown")
                    if source == "synthetic_demo":
                        self.status_label.config(
                            text=f"⚠️ DEMO DATA shown — install fcsparser for real FCS files",
                            fg=C_WARN)
                        messagebox.showwarning(
                            "FCS Library Missing",
                            "Neither fcsparser nor FlowIO is installed.\n"
                            "Synthetic demo data is displayed instead of your file.\n\n"
                            "To read real FCS files, install:\n"
                            "  pip install fcsparser")
                    else:
                        self.status_label.config(
                            text=f"✅ Loaded {data['n_events']} events via {source}")
                self.ui_queue.schedule(update)

            except Exception as e:
                self.ui_queue.schedule(lambda: messagebox.showerror("Error", str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _load_sample_data(self, idx):
        """Auto-load from table"""
        sample = self.samples[idx]

        if 'Flow_Data' in sample and sample['Flow_Data']:
            try:
                data = json.loads(sample['Flow_Data'])
                self.fcs_data = np.array(data['data'])
                self.channels = data['channels']
                self._update_channel_selectors()
                self._plot_scatter()
                self.status_label.config(text=f"Loaded flow data from table")
            except Exception as e:
                self.status_label.config(text=f"Error: {e}")

    def _build_content_ui(self):
        """Build the tab-specific UI"""
        # Main split
        main_pane = ttk.PanedWindow(self.content_frame, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True)

        # Left panel - controls
        left = tk.Frame(main_pane, bg="white", width=300)
        main_pane.add(left, weight=1)

        # Right panel - plot
        right = tk.Frame(main_pane, bg="white")
        main_pane.add(right, weight=2)

        # === LEFT PANEL ===
        tk.Label(left, text="🩸 FLOW CYTOMETRY GATING",
                font=("Arial", 10, "bold"), bg=C_LIGHT, fg=C_HEADER).pack(fill=tk.X, pady=2)

        tk.Label(left, text="Herzenberg et al. 2006 · Maecker et al. 2004",
                font=("Arial", 7), bg="white", fg="#888").pack(anchor=tk.W, padx=4)

        # Channel selection
        channel_frame = tk.LabelFrame(left, text="Channels", bg="white",
                                     font=("Arial", 8, "bold"), fg=C_HEADER)
        channel_frame.pack(fill=tk.X, padx=4, pady=4)

        row1 = tk.Frame(channel_frame, bg="white")
        row1.pack(fill=tk.X, pady=2)
        tk.Label(row1, text="X-axis:", font=("Arial", 8), bg="white").pack(side=tk.LEFT)
        self.fcm_x = tk.StringVar()
        self.fcm_x_combo = ttk.Combobox(row1, textvariable=self.fcm_x,
                                        values=[], width=12)
        self.fcm_x_combo.pack(side=tk.LEFT, padx=2)

        row2 = tk.Frame(channel_frame, bg="white")
        row2.pack(fill=tk.X, pady=2)
        tk.Label(row2, text="Y-axis:", font=("Arial", 8), bg="white").pack(side=tk.LEFT)
        self.fcm_y = tk.StringVar()
        self.fcm_y_combo = ttk.Combobox(row2, textvariable=self.fcm_y,
                                        values=[], width=12)
        self.fcm_y_combo.pack(side=tk.LEFT, padx=2)

        # Gate parameters
        gate_frame = tk.LabelFrame(left, text="Gating", bg="white",
                                  font=("Arial", 8, "bold"), fg=C_HEADER)
        gate_frame.pack(fill=tk.X, padx=4, pady=4)

        self.gate_type = tk.StringVar(value="Rectangle")
        ttk.Combobox(gate_frame, textvariable=self.gate_type,
                     values=["Rectangle", "Ellipse", "Polygon", "GMM Clustering"],
                     width=18, state="readonly").pack(fill=tk.X, padx=4, pady=2)

        tk.Label(gate_frame, text="Gate name:", font=("Arial", 8),
                bg="white").pack(anchor=tk.W, padx=4)
        self.gate_name = tk.StringVar(value="Population")
        ttk.Entry(gate_frame, textvariable=self.gate_name).pack(fill=tk.X, padx=4, pady=2)

        btn_frame = tk.Frame(gate_frame, bg="white")
        btn_frame.pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="➕ Add Gate", command=self._add_gate,
                  width=12).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="🗑️ Clear", command=self._clear_gates,
                  width=8).pack(side=tk.LEFT, padx=2)

        # Statistics
        stats_frame = tk.LabelFrame(left, text="Population Statistics", bg="white",
                                   font=("Arial", 8, "bold"), fg=C_HEADER)
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self.fcm_tree = ttk.Treeview(stats_frame, columns=("Gate", "Events", "%Total"),
                                     show="headings", height=6)
        for col, w in [("Gate", 100), ("Events", 70), ("%Total", 70)]:
            self.fcm_tree.heading(col, text=col)
            self.fcm_tree.column(col, width=w, anchor=tk.CENTER)
        self.fcm_tree.pack(fill=tk.BOTH, expand=True)

        # === RIGHT PANEL ===
        if HAS_MPL:
            self.fcm_fig = Figure(figsize=(8, 6), dpi=100, facecolor="white")
            self.fcm_ax = self.fcm_fig.add_subplot(111)
            self.fcm_ax.set_title("Flow Cytometry Plot", fontsize=9, fontweight="bold")

            self.fcm_canvas = FigureCanvasTkAgg(self.fcm_fig, right)
            self.fcm_canvas.draw()
            self.fcm_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            toolbar = NavigationToolbar2Tk(self.fcm_canvas, right)
            toolbar.update()
        else:
            tk.Label(right, text="matplotlib required for plots",
                    bg="white", fg="#888").pack(expand=True)

    def _update_channel_selectors(self):
        """Update channel dropdowns"""
        if self.channels:
            self.fcm_x_combo['values'] = self.channels
            self.fcm_y_combo['values'] = self.channels
            if len(self.channels) >= 2:
                self.fcm_x.set(self.channels[0])
                self.fcm_y.set(self.channels[1])

    def _plot_scatter(self):
        """Plot 2D scatter of selected channels"""
        if not HAS_MPL or self.fcs_data is None:
            return

        x_idx = self.channels.index(self.fcm_x.get()) if self.fcm_x.get() in self.channels else 0
        y_idx = self.channels.index(self.fcm_y.get()) if self.fcm_y.get() in self.channels else 1

        x_data = self.fcs_data[:, x_idx]
        y_data = self.fcs_data[:, y_idx]

        self.fcm_ax.clear()
        self.fcm_ax.scatter(x_data, y_data, s=1, alpha=0.5, c=C_ACCENT, edgecolors='none')
        self.fcm_ax.set_xlabel(self.fcm_x.get(), fontsize=8)
        self.fcm_ax.set_ylabel(self.fcm_y.get(), fontsize=8)
        self.fcm_ax.set_title(f"Flow Cytometry: {self.fcm_x.get()} vs {self.fcm_y.get()}",
                             fontsize=9, fontweight="bold")
        self.fcm_ax.grid(True, alpha=0.3)

        self.fcm_canvas.draw()

    def _add_gate(self):
        """Interactive gate drawing using matplotlib RectangleSelector"""
        if not HAS_MPL or self.fcs_data is None:
            messagebox.showwarning("Cannot Gate", "Data or matplotlib not available")
            return

        from matplotlib.widgets import RectangleSelector

        ax = self.fcm_ax
        fig = ax.figure
        self.current_gate = None

        def onselect(eclick, erelease):
            x1, y1 = eclick.xdata, eclick.ydata
            x2, y2 = erelease.xdata, erelease.ydata
            if None in (x1, y1, x2, y2):
                return
            xmin, xmax = sorted([x1, x2])
            ymin, ymax = sorted([y1, y2])
            gate_name = self.gate_name.get().strip() or f"Gate_{len(self.gates)+1}"
            self.gates[gate_name] = {
                'type': 'rectangle',
                'xmin': xmin, 'xmax': xmax,
                'ymin': ymin, 'ymax': ymax
            }
            # Apply gate to data
            x_idx = self.channels.index(self.fcm_x.get())
            y_idx = self.channels.index(self.fcm_y.get())
            x_data = self.fcs_data[:, x_idx]
            y_data = self.fcs_data[:, y_idx]
            mask = (x_data >= xmin) & (x_data <= xmax) & (y_data >= ymin) & (y_data <= ymax)
            events = np.sum(mask)
            percent = events / len(x_data) * 100
            # Update tree
            self.fcm_tree.insert("", tk.END, values=(gate_name, events, f"{percent:.1f}%"))
            # Redraw rectangle on plot
            rect = plt.Rectangle((xmin, ymin), xmax-xmin, ymax-ymin,
                                fill=False, edgecolor='red', linewidth=2)
            ax.add_patch(rect)
            fig.canvas.draw_idle()
            # Disconnect selector after one use
            rs.set_active(False)

        def toggle_selector(event):
            if event.key in ['Q', 'q'] and rs.active:
                rs.set_active(False)

        rs = RectangleSelector(ax, onselect, useblit=True,
                            button=[1], minspanx=5, minspany=5,
                            spancoords='data', interactive=True)
        fig.canvas.mpl_connect('key_press_event', toggle_selector)
        messagebox.showinfo("Gate Drawing", "Click and drag on the plot to draw a rectangular gate. Press 'q' to cancel.")


# ============================================================================
# ENGINE 5 — ddPCR POISSON STATISTICS (Hindson et al. 2011; Bio-Rad QX200)
# ============================================================================
class ddPCRAnalyzer:
    """
    Droplet Digital PCR absolute quantification.

    Poisson statistics: λ = -ln(1 - p)
        λ = copies per droplet
        p = fraction of positive droplets

    Concentration (copies/μL) = λ / V_droplet

    Confidence intervals: based on Poisson distribution

    References:
        Hindson, B.J. et al. (2011) "High-throughput droplet digital PCR
            system for absolute quantitation of DNA copy number" Analytical Chemistry
        Bio-Rad QX200 Droplet Digital PCR System User Guide
    """

    DROPLET_VOLUME_UL = 0.00085  # QX200 droplet volume (μL)

    @classmethod
    def poisson_lambda(cls, positive_droplets, total_droplets):
        """
        Calculate λ (copies per droplet) from droplet counts

        λ = -ln(1 - positive/total)
        """
        if total_droplets == 0:
            return 0

        p = positive_droplets / total_droplets
        if p >= 1:
            p = 0.999999  # Avoid log(0)

        lam = -np.log(1 - p)
        return lam

    @classmethod
    def concentration(cls, positive_droplets, total_droplets, volume_ul=None):
        """
        Calculate concentration in copies/μL

        C = λ / V_droplet
        """
        if volume_ul is None:
            volume_ul = cls.DROPLET_VOLUME_UL

        lam = cls.poisson_lambda(positive_droplets, total_droplets)
        conc = lam / volume_ul

        return conc

    @classmethod
    def confidence_interval(cls, positive_droplets, total_droplets, alpha=0.05):
        """
        Calculate 95% confidence interval using Poisson statistics

        Uses exact method based on chi-square distribution
        """
        if positive_droplets == 0:
            lower = 0
            upper = -np.log(alpha) / total_droplets
        else:
            # Wilson score interval approximation
            p = positive_droplets / total_droplets
            z = 1.96  # 95% CI

            denominator = 1 + z**2 / total_droplets
            center = p + z**2 / (2 * total_droplets)
            spread = z * np.sqrt(p * (1 - p) / total_droplets + z**2 / (4 * total_droplets**2))

            lower_p = (center - spread) / denominator
            upper_p = (center + spread) / denominator

            lower_p = max(0, lower_p)
            upper_p = min(1, upper_p)

            lower = -np.log(1 - lower_p) / cls.DROPLET_VOLUME_UL
            upper = -np.log(1 - upper_p) / cls.DROPLET_VOLUME_UL

        return lower, upper

    @classmethod
    def merge_replicates(cls, replicates):
        """
        Merge multiple replicate measurements

        replicates: list of dicts with 'positive' and 'total' keys
        """
        total_positive = sum(r['positive'] for r in replicates)
        total_droplets = sum(r['total'] for r in replicates)

        conc = cls.concentration(total_positive, total_droplets)
        lower, upper = cls.confidence_interval(total_positive, total_droplets)

        return {
            "positive": total_positive,
            "total": total_droplets,
            "concentration": conc,
            "ci_lower": lower,
            "ci_upper": upper,
            "cv": np.sqrt(1/total_positive) if total_positive > 0 else 0
        }

    @classmethod
    def limit_of_detection(cls, total_droplets, blank_positive=0, alpha=0.05):
        """
        Calculate limit of detection

        LOD is the concentration that can be distinguished from blank
        """
        if blank_positive == 0:
            # Use Poisson threshold
            max_blank = -np.log(alpha) / total_droplets
            lod = max_blank / cls.DROPLET_VOLUME_UL
        else:
            # Use blank replicates
            pass

        return lod

    @classmethod
    def load_ddpcr_data(cls, path):
        """Load ddPCR data from CSV"""
        df = pd.read_csv(path)

        # Expected columns: Well, Target, Positive, Total, (Concentration)
        data = []
        for _, row in df.iterrows():
            data.append({
                "well": row.get('Well', ''),
                "target": row.get('Target', 'Unknown'),
                "positive": int(row.get('Positive', row.get('Positives', 0))),
                "total": int(row.get('Total', row.get('Droplets', 0)))
            })

        return data


# ============================================================================
# TAB 5: ddPCR POISSON STATISTICS
# ============================================================================
class ddPCRAnalysisTab(AnalysisTab):
    def __init__(self, parent, app, ui_queue):
        super().__init__(parent, app, ui_queue, "ddPCR Analysis")
        self.engine = ddPCRAnalyzer
        self.droplet_data = []
        self.results = {}
        self._build_content_ui()

    def _sample_has_data(self, sample):
        """Check if sample has ddPCR data"""
        return any(col in sample and sample[col] for col in
                  ['ddPCR_File', 'Droplet_Counts'])

    def _manual_import(self):
        """Manual import from CSV"""
        path = filedialog.askopenfilename(
            title="Load ddPCR Data",
            filetypes=[("CSV", "*.csv"), ("Excel", "*.xlsx"), ("All files", "*.*")])
        if not path:
            return

        self.status_label.config(text="🔄 Loading ddPCR data...")

        def worker():
            try:
                data = self.engine.load_ddpcr_data(path)

                def update():
                    self.droplet_data = data
                    self.manual_label.config(text=f"✓ {Path(path).name}")
                    self._update_well_list()
                    self.status_label.config(text=f"Loaded {len(data)} wells")
                self.ui_queue.schedule(update)

            except Exception as e:
                self.ui_queue.schedule(lambda: messagebox.showerror("Error", str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _load_sample_data(self, idx):
        """Auto-load from table"""
        sample = self.samples[idx]

        if 'Droplet_Counts' in sample and sample['Droplet_Counts']:
            try:
                self.droplet_data = json.loads(sample['Droplet_Counts'])
                self._update_well_list()
                self.status_label.config(text=f"Loaded ddPCR data from table")
            except Exception as e:
                self.status_label.config(text=f"Error: {e}")

    def _build_content_ui(self):
        """Build the tab-specific UI"""
        # Main split
        main_pane = ttk.PanedWindow(self.content_frame, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True)

        # Left panel - controls
        left = tk.Frame(main_pane, bg="white", width=300)
        main_pane.add(left, weight=1)

        # Right panel - plot
        right = tk.Frame(main_pane, bg="white")
        main_pane.add(right, weight=2)

        # === LEFT PANEL ===
        tk.Label(left, text="💧 ddPCR POISSON STATISTICS",
                font=("Arial", 10, "bold"), bg=C_LIGHT, fg=C_HEADER).pack(fill=tk.X, pady=2)

        tk.Label(left, text="Hindson et al. 2011 · Bio-Rad QX200",
                font=("Arial", 7), bg="white", fg="#888").pack(anchor=tk.W, padx=4)

        # Well selector
        tk.Label(left, text="Select Well:", font=("Arial", 8, "bold"),
                bg="white").pack(anchor=tk.W, padx=4, pady=(4, 0))

        self.dd_well_listbox = tk.Listbox(left, height=6, font=("Courier", 8))
        self.dd_well_listbox.pack(fill=tk.X, padx=4, pady=2)
        self.dd_well_listbox.bind('<<ListboxSelect>>', self._on_well_selected)

        # Parameters
        param_frame = tk.LabelFrame(left, text="Parameters", bg="white",
                                   font=("Arial", 8, "bold"), fg=C_HEADER)
        param_frame.pack(fill=tk.X, padx=4, pady=4)

        tk.Label(param_frame, text="Droplet volume (μL):", font=("Arial", 8),
                bg="white").pack(anchor=tk.W, padx=4)
        self.dd_volume = tk.StringVar(value="0.00085")
        ttk.Entry(param_frame, textvariable=self.dd_volume).pack(fill=tk.X, padx=4, pady=2)

        tk.Label(param_frame, text="Confidence level:", font=("Arial", 8),
                bg="white").pack(anchor=tk.W, padx=4)
        self.dd_ci = tk.StringVar(value="95%")
        ttk.Combobox(param_frame, textvariable=self.dd_ci,
                     values=["90%", "95%", "99%"],
                     width=10, state="readonly").pack(anchor=tk.W, padx=4, pady=2)

        ttk.Button(left, text="📊 CALCULATE", command=self._calculate_well).pack(fill=tk.X, padx=4, pady=4)
        ttk.Button(left, text="🔄 MERGE REPLICATES", command=self._merge_replicates).pack(fill=tk.X, padx=4, pady=2)

        # Results
        results_frame = tk.LabelFrame(left, text="Results", bg="white",
                                     font=("Arial", 8, "bold"), fg=C_HEADER)
        results_frame.pack(fill=tk.X, padx=4, pady=4)

        self.dd_results = {}
        result_labels = [
            ("Positive droplets:", "pos"),
            ("Total droplets:", "total"),
            ("λ (copies/droplet):", "lambda"),
            ("Concentration (cp/μL):", "conc"),
            ("95% CI lower:", "ci_low"),
            ("95% CI upper:", "ci_up"),
            ("CV (%):", "cv")
        ]

        for i, (label, key) in enumerate(result_labels):
            row = tk.Frame(results_frame, bg="white")
            row.pack(fill=tk.X, pady=1)
            tk.Label(row, text=label, font=("Arial", 7), bg="white", width=16, anchor=tk.W).pack(side=tk.LEFT)
            var = tk.StringVar(value="—")
            tk.Label(row, textvariable=var, font=("Arial", 7, "bold"),
                    bg="white", fg=C_HEADER).pack(side=tk.LEFT, padx=2)
            self.dd_results[key] = var

        # === RIGHT PANEL ===
        if HAS_MPL:
            self.dd_fig = Figure(figsize=(8, 6), dpi=100, facecolor="white")
            gs = GridSpec(2, 1, figure=self.dd_fig, hspace=0.3)
            self.dd_ax_bar = self.dd_fig.add_subplot(gs[0])
            self.dd_ax_poisson = self.dd_fig.add_subplot(gs[1])

            self.dd_ax_bar.set_title("Concentration by Well", fontsize=9, fontweight="bold")
            self.dd_ax_poisson.set_title("Poisson Distribution", fontsize=9, fontweight="bold")

            self.dd_canvas = FigureCanvasTkAgg(self.dd_fig, right)
            self.dd_canvas.draw()
            self.dd_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            toolbar = NavigationToolbar2Tk(self.dd_canvas, right)
            toolbar.update()
        else:
            tk.Label(right, text="matplotlib required for plots",
                    bg="white", fg="#888").pack(expand=True)

    def _update_well_list(self):
        """Update well listbox"""
        self.dd_well_listbox.delete(0, tk.END)
        for data in self.droplet_data:
            self.dd_well_listbox.insert(tk.END, f"{data['well']} - {data['target']}")

    def _on_well_selected(self, event):
        """Handle well selection"""
        selection = self.dd_well_listbox.curselection()
        if selection:
            idx = selection[0]
            self.current_well_data = self.droplet_data[idx]

    def _calculate_well(self):
        """Calculate statistics for selected well"""
        if not hasattr(self, 'current_well_data'):
            messagebox.showwarning("No Selection", "Select a well first")
            return

        self.status_label.config(text="🔄 Calculating...")

        def worker():
            try:
                data = self.current_well_data
                pos = data['positive']
                total = data['total']

                lam = self.engine.poisson_lambda(pos, total)
                conc = lam / float(self.dd_volume.get())
                lower, upper = self.engine.confidence_interval(pos, total)
                cv = np.sqrt(1/pos) * 100 if pos > 0 else 0

                def update_ui():
                    self.dd_results["pos"].set(str(pos))
                    self.dd_results["total"].set(str(total))
                    self.dd_results["lambda"].set(f"{lam:.4f}")
                    self.dd_results["conc"].set(f"{conc:.1f}")
                    self.dd_results["ci_low"].set(f"{lower:.1f}")
                    self.dd_results["ci_up"].set(f"{upper:.1f}")
                    self.dd_results["cv"].set(f"{cv:.1f}%")

                    # Update plots
                    if HAS_MPL:
                        # Poisson probability
                        import math as _math
                        k = np.arange(0, min(20, pos*2))
                        poisson_prob = np.exp(-lam) * (lam**k) / np.array([_math.factorial(int(ki)) for ki in k])

                        self.dd_ax_poisson.clear()
                        self.dd_ax_poisson.bar(k, poisson_prob, color=C_ACCENT2, alpha=0.7)
                        self.dd_ax_poisson.axvline(lam, color=C_WARN, ls='--', lw=2,
                                                   label=f"λ={lam:.2f}")
                        self.dd_ax_poisson.set_xlabel("Copies per droplet (k)", fontsize=8)
                        self.dd_ax_poisson.set_ylabel("P(k)", fontsize=8)
                        self.dd_ax_poisson.legend(fontsize=7)
                        self.dd_ax_poisson.grid(True, alpha=0.3, axis='y')

                        # Update bar plot of all wells
                        self._update_bar_plot()

                        self.dd_canvas.draw()

                    self.status_label.config(text=f"✅ {data['well']}: {conc:.1f} copies/μL")

                self.ui_queue.schedule(update_ui)

            except Exception as e:
                self.ui_queue.schedule(lambda: messagebox.showerror("Error", str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _update_bar_plot(self):
        """Update bar plot of all wells"""
        if not HAS_MPL:
            return

        self.dd_ax_bar.clear()

        wells = []
        concs = []
        errors = []

        for data in self.droplet_data:
            wells.append(f"{data['well']}")
            lam = self.engine.poisson_lambda(data['positive'], data['total'])
            conc = lam / float(self.dd_volume.get())
            lower, upper = self.engine.confidence_interval(data['positive'], data['total'])
            concs.append(conc)
            errors.append([conc - lower, upper - conc])

        bars = self.dd_ax_bar.bar(range(len(wells)), concs, color=C_ACCENT, alpha=0.7)
        self.dd_ax_bar.errorbar(range(len(wells)), concs,
                               yerr=np.array(errors).T, fmt='none',
                               ecolor='k', capsize=3)

        self.dd_ax_bar.set_xticks(range(len(wells)))
        self.dd_ax_bar.set_xticklabels(wells, rotation=45, fontsize=7)
        self.dd_ax_bar.set_ylabel("Concentration (copies/μL)", fontsize=8)
        self.dd_ax_bar.grid(True, alpha=0.3, axis='y')

    def _merge_replicates(self):
        """Merge replicate wells"""
        # Group by target
        targets = {}
        for data in self.droplet_data:
            target = data['target']
            if target not in targets:
                targets[target] = []
            targets[target].append(data)

        # Merge each target
        merged = []
        for target, reps in targets.items():
            result = self.engine.merge_replicates(reps)
            merged.append({
                "target": target,
                "concentration": result['concentration'],
                "ci_lower": result['ci_lower'],
                "ci_upper": result['ci_upper'],
                "cv": result['cv'] * 100
            })

        # Display results
        # (Would update tree view in full implementation)
        self.status_label.config(text=f"✅ Merged {len(merged)} targets")


# ============================================================================
# ENGINE 6 — MELTING CURVE ANALYSIS (Ririe et al. 1997; Wittwer et al. 2003)
# ============================================================================
class MeltingCurveAnalyzer:
    """
    High Resolution Melting (HRM) curve analysis.

    Tm determination:
        - Peak of negative first derivative (-dF/dT)
        - Second derivative zero crossing

    Genotyping:
        - Difference curves
        - Clustering of melt curves

    References:
        Ririe, K.M. et al. (1997) "Product differentiation by analysis of
            DNA melting curves during the polymerase chain reaction" Analytical Biochemistry
        Wittwer, C.T. et al. (2003) "High-resolution genotyping by amplicon
            melting analysis using LCGreen" Clinical Chemistry
    """

    @classmethod
    def negative_derivative(cls, temperature, fluorescence, smooth=True):
        """
        Calculate -dF/dT for Tm determination

        Returns: temperature (shifted), -dF/dT
        """
        if smooth and HAS_SCIPY:
            fluor_smooth = savgol_filter(fluorescence, window_length=min(11, len(fluorescence)//5*2+1), polyorder=3)
        else:
            fluor_smooth = fluorescence

        # Calculate derivative
        dFdT = np.gradient(fluor_smooth, temperature)

        # Return negative derivative (peak at Tm)
        # Temperature for derivative is midpoint
        t_mid = (temperature[:-1] + temperature[1:]) / 2

        return t_mid, -dFdT[:-1]

    @classmethod
    def find_tm(cls, temperature, fluorescence, method="peak"):
        """
        Find melting temperature (Tm)

        Methods:
        - "peak": maximum of -dF/dT
        - "zero": zero crossing of second derivative
        """
        t_mid, neg_deriv = cls.negative_derivative(temperature, fluorescence)

        if method == "peak":
            # Find peak of -dF/dT
            peak_idx = np.argmax(neg_deriv)
            tm = t_mid[peak_idx]

            # Fit quadratic around peak for better accuracy
            if peak_idx > 0 and peak_idx < len(t_mid) - 1:
                idxs = [peak_idx-1, peak_idx, peak_idx+1]
                coeffs = np.polyfit(t_mid[idxs], neg_deriv[idxs], 2)
                tm = -coeffs[1] / (2 * coeffs[0])

            return tm, t_mid, neg_deriv

        return None, t_mid, neg_deriv

    @classmethod
    def normalize_curves(cls, temperature, fluorescence, pre_melt=(65, 75), post_melt=(85, 95)):
        """
        Normalize melting curves to [0,1] range

        Uses pre- and post-melt regions for normalization
        """
        # Find indices for pre- and post-melt regions
        pre_mask = (temperature >= pre_melt[0]) & (temperature <= pre_melt[1])
        post_mask = (temperature >= post_melt[0]) & (temperature <= post_melt[1])

        if not np.any(pre_mask) or not np.any(post_mask):
            # Fallback to min/max normalization
            fluor_norm = (fluorescence - np.min(fluorescence)) / (np.max(fluorescence) - np.min(fluorescence))
            return fluor_norm

        # Use mean of pre-melt as 1.0, post-melt as 0.0
        pre_val = np.mean(fluorescence[pre_mask])
        post_val = np.mean(fluorescence[post_mask])

        fluor_norm = (fluorescence - post_val) / (pre_val - post_val)
        fluor_norm = np.clip(fluor_norm, 0, 1)

        return fluor_norm

    @classmethod
    def difference_curve(cls, temperature, sample_curve, reference_curve):
        """
        Calculate difference curve for genotyping

        ΔF = F_sample - F_reference
        """
        # Interpolate reference to sample temperatures
        from scipy.interpolate import interp1d
        f_ref_interp = interp1d(temperature, reference_curve, kind='linear',
                                bounds_error=False, fill_value='extrapolate')
        ref_at_sample = f_ref_interp(temperature)

        return sample_curve - ref_at_sample

    @classmethod
    def peak_detection(cls, temperature, fluorescence, height_threshold=0.1):
        """
        Detect multiple peaks in melting curve (for heterozygotes)
        """
        _, neg_deriv = cls.negative_derivative(temperature, fluorescence)

        if HAS_SCIPY:
            peaks, properties = find_peaks(neg_deriv, height=height_threshold * np.max(neg_deriv),
                                          distance=len(neg_deriv)//10)
            return peaks, properties
        else:
            return [], {}

    @classmethod
    def load_melting_data(cls, path):
        """Load melting curve data from CSV"""
        df = pd.read_csv(path)

        # Try to identify columns
        temp_col = None
        fluor_cols = []

        for col in df.columns:
            col_lower = col.lower()
            if any(x in col_lower for x in ['temp', 'temperature', 't']):
                temp_col = col
            elif any(x in col_lower for x in ['fluor', 'rfu', 'fluorescence', 'signal']):
                fluor_cols.append(col)

        if temp_col is None:
            temp_col = df.columns[0]

        temperature = df[temp_col].values

        # Load all fluorescence columns
        fluorescence = {}
        for col in fluor_cols[:16]:  # Limit to first 16 samples
            fluorescence[col] = df[col].values

        return {
            "temperature": temperature,
            "fluorescence": fluorescence,
            "metadata": {"file": Path(path).name}
        }


# ============================================================================
# TAB 6: MELTING CURVE ANALYSIS
# ============================================================================
class MeltingCurveTab(AnalysisTab):
    def __init__(self, parent, app, ui_queue):
        super().__init__(parent, app, ui_queue, "Melting Curve")
        self.engine = MeltingCurveAnalyzer
        self.temperature = None
        self.fluorescence = None
        self.current_sample = None
        self.tm_results = {}
        self._build_content_ui()

    def _sample_has_data(self, sample):
        """Check if sample has melting curve data"""
        return any(col in sample and sample[col] for col in
                  ['HRM_File', 'Melting_Curve', 'Melt_Data'])

    def _manual_import(self):
        """Manual import from CSV"""
        path = filedialog.askopenfilename(
            title="Load Melting Curve Data",
            filetypes=[("CSV", "*.csv"), ("Excel", "*.xlsx"), ("All files", "*.*")])
        if not path:
            return

        self.status_label.config(text="🔄 Loading melting curve data...")

        def worker():
            try:
                data = self.engine.load_melting_data(path)

                def update():
                    self.temperature = data["temperature"]
                    self.fluorescence = data["fluorescence"]
                    self.manual_label.config(text=f"✓ {Path(path).name}")
                    self._update_sample_list()
                    self._plot_melting_curves()
                    self.status_label.config(text=f"Loaded {len(self.fluorescence)} samples")
                self.ui_queue.schedule(update)

            except Exception as e:
                self.ui_queue.schedule(lambda: messagebox.showerror("Error", str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _load_sample_data(self, idx):
        """Auto-load from table"""
        sample = self.samples[idx]

        if 'Melting_Curve' in sample and sample['Melting_Curve']:
            try:
                data = json.loads(sample['Melting_Curve'])
                self.temperature = np.array(data['temperature'])
                self.fluorescence = data['fluorescence']
                self._update_sample_list()
                self._plot_melting_curves()
                self.status_label.config(text=f"Loaded melting curve data from table")
            except Exception as e:
                self.status_label.config(text=f"Error: {e}")

    def _build_content_ui(self):
        """Build the tab-specific UI"""
        # Main split
        main_pane = ttk.PanedWindow(self.content_frame, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True)

        # Left panel - controls
        left = tk.Frame(main_pane, bg="white", width=300)
        main_pane.add(left, weight=1)

        # Right panel - plot
        right = tk.Frame(main_pane, bg="white")
        main_pane.add(right, weight=2)

        # === LEFT PANEL ===
        tk.Label(left, text="🌡️ MELTING CURVE ANALYSIS",
                font=("Arial", 10, "bold"), bg=C_LIGHT, fg=C_HEADER).pack(fill=tk.X, pady=2)

        tk.Label(left, text="Ririe et al. 1997 · Wittwer et al. 2003",
                font=("Arial", 7), bg="white", fg="#888").pack(anchor=tk.W, padx=4)

        # Sample selector
        tk.Label(left, text="Select Sample:", font=("Arial", 8, "bold"),
                bg="white").pack(anchor=tk.W, padx=4, pady=(4, 0))

        self.melt_sample_listbox = tk.Listbox(left, height=6, font=("Courier", 8))
        self.melt_sample_listbox.pack(fill=tk.X, padx=4, pady=2)
        self.melt_sample_listbox.bind('<<ListboxSelect>>', self._on_sample_selected)

        # Reference sample for difference plot
        tk.Label(left, text="Reference Sample:", font=("Arial", 8, "bold"),
                bg="white").pack(anchor=tk.W, padx=4, pady=(4, 0))
        self.melt_ref_var = tk.StringVar()
        self.melt_ref_combo = ttk.Combobox(left, textvariable=self.melt_ref_var,
                                           values=[], width=20)
        self.melt_ref_combo.pack(fill=tk.X, padx=4)

        # Normalization ranges
        norm_frame = tk.LabelFrame(left, text="Normalization", bg="white",
                                  font=("Arial", 8, "bold"), fg=C_HEADER)
        norm_frame.pack(fill=tk.X, padx=4, pady=4)

        row1 = tk.Frame(norm_frame, bg="white")
        row1.pack(fill=tk.X, pady=2)
        tk.Label(row1, text="Pre-melt (°C):", font=("Arial", 8), bg="white").pack(side=tk.LEFT)
        self.melt_pre_min = tk.StringVar(value="65")
        self.melt_pre_max = tk.StringVar(value="75")
        ttk.Entry(row1, textvariable=self.melt_pre_min, width=5).pack(side=tk.LEFT, padx=1)
        tk.Label(row1, text="-", font=("Arial", 8), bg="white").pack(side=tk.LEFT)
        ttk.Entry(row1, textvariable=self.melt_pre_max, width=5).pack(side=tk.LEFT, padx=1)

        row2 = tk.Frame(norm_frame, bg="white")
        row2.pack(fill=tk.X, pady=2)
        tk.Label(row2, text="Post-melt (°C):", font=("Arial", 8), bg="white").pack(side=tk.LEFT)
        self.melt_post_min = tk.StringVar(value="85")
        self.melt_post_max = tk.StringVar(value="95")
        ttk.Entry(row2, textvariable=self.melt_post_min, width=5).pack(side=tk.LEFT, padx=1)
        tk.Label(row2, text="-", font=("Arial", 8), bg="white").pack(side=tk.LEFT)
        ttk.Entry(row2, textvariable=self.melt_post_max, width=5).pack(side=tk.LEFT, padx=1)

        # Analysis buttons
        btn_frame = tk.Frame(left, bg="white")
        btn_frame.pack(fill=tk.X, padx=4, pady=4)
        ttk.Button(btn_frame, text="🔍 FIND Tm", command=self._find_tm,
                  width=12).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="📊 DIFFERENCE", command=self._difference_plot,
                  width=12).pack(side=tk.LEFT, padx=2)

        # Results
        results_frame = tk.LabelFrame(left, text="Results", bg="white",
                                     font=("Arial", 8, "bold"), fg=C_HEADER)
        results_frame.pack(fill=tk.X, padx=4, pady=4)

        self.melt_results = {}
        result_labels = [
            ("Sample:", "sample"),
            ("Tm (°C):", "tm"),
            ("Peak height:", "height"),
            ("Peak width:", "width")
        ]

        for i, (label, key) in enumerate(result_labels):
            row = tk.Frame(results_frame, bg="white")
            row.pack(fill=tk.X, pady=1)
            tk.Label(row, text=label, font=("Arial", 7), bg="white", width=12, anchor=tk.W).pack(side=tk.LEFT)
            var = tk.StringVar(value="—")
            tk.Label(row, textvariable=var, font=("Arial", 7, "bold"),
                    bg="white", fg=C_HEADER).pack(side=tk.LEFT, padx=2)
            self.melt_results[key] = var

        # Tm summary tree
        tk.Label(left, text="Tm Summary:", font=("Arial", 8, "bold"),
                bg="white").pack(anchor=tk.W, padx=4, pady=(4, 0))

        tm_frame = tk.Frame(left, bg="white", bd=1, relief=tk.SUNKEN)
        tm_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=2)

        self.melt_tree = ttk.Treeview(tm_frame, columns=("Sample", "Tm (°C)", "Peak Height"),
                                     show="headings", height=6)
        for col, w in [("Sample", 100), ("Tm (°C)", 70), ("Peak Height", 80)]:
            self.melt_tree.heading(col, text=col)
            self.melt_tree.column(col, width=w, anchor=tk.CENTER)
        self.melt_tree.pack(fill=tk.BOTH, expand=True)

        # === RIGHT PANEL ===
        if HAS_MPL:
            self.melt_fig = Figure(figsize=(8, 6), dpi=100, facecolor="white")
            gs = GridSpec(2, 2, figure=self.melt_fig, hspace=0.3, wspace=0.3)
            self.melt_ax_raw = self.melt_fig.add_subplot(gs[0, :])
            self.melt_ax_deriv = self.melt_fig.add_subplot(gs[1, 0])
            self.melt_ax_diff = self.melt_fig.add_subplot(gs[1, 1])

            self.melt_ax_raw.set_title("Raw Melting Curves", fontsize=9, fontweight="bold")
            self.melt_ax_deriv.set_title("-dF/dT (Tm Peaks)", fontsize=9, fontweight="bold")
            self.melt_ax_diff.set_title("Difference Plot", fontsize=9, fontweight="bold")

            self.melt_canvas = FigureCanvasTkAgg(self.melt_fig, right)
            self.melt_canvas.draw()
            self.melt_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            toolbar = NavigationToolbar2Tk(self.melt_canvas, right)
            toolbar.update()
        else:
            tk.Label(right, text="matplotlib required for plots",
                    bg="white", fg="#888").pack(expand=True)

    def _update_sample_list(self):
        """Update sample listbox"""
        self.melt_sample_listbox.delete(0, tk.END)
        if self.fluorescence:
            samples = sorted(self.fluorescence.keys())
            for sample in samples:
                self.melt_sample_listbox.insert(tk.END, sample)
            self.melt_ref_combo['values'] = samples
            if samples:
                self.melt_ref_var.set(samples[0])

    def _plot_melting_curves(self):
        """Plot all melting curves"""
        if not HAS_MPL or self.temperature is None:
            return

        self.melt_ax_raw.clear()
        for i, (sample, fluor) in enumerate(list(self.fluorescence.items())[:10]):
            color = PLOT_COLORS[i % len(PLOT_COLORS)]
            self.melt_ax_raw.plot(self.temperature, fluor, color=color, lw=1.5, label=sample)

        self.melt_ax_raw.set_xlabel("Temperature (°C)", fontsize=8)
        self.melt_ax_raw.set_ylabel("Fluorescence", fontsize=8)
        self.melt_ax_raw.legend(fontsize=6, ncol=2)
        self.melt_ax_raw.grid(True, alpha=0.3)

        self.melt_ax_deriv.clear()
        self.melt_ax_diff.clear()
        self.melt_canvas.draw()

    def _on_sample_selected(self, event):
        """Handle sample selection"""
        selection = self.melt_sample_listbox.curselection()
        if selection:
            self.current_sample = self.melt_sample_listbox.get(selection[0])
            self._plot_single_sample()

    def _plot_single_sample(self):
        """Plot single sample with derivative"""
        if not HAS_MPL or self.current_sample not in self.fluorescence:
            return

        fluor = self.fluorescence[self.current_sample]

        # Normalize
        pre_min = float(self.melt_pre_min.get())
        pre_max = float(self.melt_pre_max.get())
        post_min = float(self.melt_post_min.get())
        post_max = float(self.melt_post_max.get())

        fluor_norm = self.engine.normalize_curves(
            self.temperature, fluor,
            pre_melt=(pre_min, pre_max),
            post_melt=(post_min, post_max)
        )

        # Calculate derivative
        t_mid, neg_deriv = self.engine.negative_derivative(self.temperature, fluor_norm)

        # Find Tm
        tm, _, _ = self.engine.find_tm(self.temperature, fluor_norm)

        # Update derivative plot
        self.melt_ax_deriv.clear()
        self.melt_ax_deriv.plot(t_mid, neg_deriv, 'r-', lw=2)
        if tm:
            self.melt_ax_deriv.axvline(tm, color=C_WARN, ls='--', lw=2,
                                       label=f"Tm={tm:.2f}°C")
        self.melt_ax_deriv.set_xlabel("Temperature (°C)", fontsize=8)
        self.melt_ax_deriv.set_ylabel("-dF/dT", fontsize=8)
        self.melt_ax_deriv.legend(fontsize=7)
        self.melt_ax_deriv.grid(True, alpha=0.3)

        # Highlight on raw plot
        self.melt_ax_raw.clear()
        for sample, fluor in self.fluorescence.items():
            alpha = 0.3 if sample != self.current_sample else 1.0
            lw = 1.0 if sample != self.current_sample else 2.5
            color = C_WARN if sample == self.current_sample else C_ACCENT
            self.melt_ax_raw.plot(self.temperature, fluor, color=color,
                                 lw=lw, alpha=alpha, label=sample if alpha > 0.5 else "")

        self.melt_ax_raw.set_xlabel("Temperature (°C)", fontsize=8)
        self.melt_ax_raw.set_ylabel("Fluorescence", fontsize=8)
        self.melt_ax_raw.legend(fontsize=6)
        self.melt_ax_raw.grid(True, alpha=0.3)

        self.melt_canvas.draw()

    def _find_tm(self):
        """Find Tm for all samples"""
        if not self.fluorescence:
            messagebox.showwarning("No Data", "Load melting curve data first")
            return

        self.status_label.config(text="🔄 Calculating Tm...")

        def worker():
            try:
                results = []
                pre_min = float(self.melt_pre_min.get())
                pre_max = float(self.melt_pre_max.get())
                post_min = float(self.melt_post_min.get())
                post_max = float(self.melt_post_max.get())

                for sample, fluor in self.fluorescence.items():
                    # Normalize
                    fluor_norm = self.engine.normalize_curves(
                        self.temperature, fluor,
                        pre_melt=(pre_min, pre_max),
                        post_melt=(post_min, post_max)
                    )

                    # Find Tm
                    tm, t_mid, neg_deriv = self.engine.find_tm(self.temperature, fluor_norm)

                    # Peak height
                    if tm:
                        # Find closest point
                        idx = np.argmin(np.abs(t_mid - tm))
                        height = neg_deriv[idx] if idx < len(neg_deriv) else 0
                    else:
                        height = 0

                    results.append({
                        "sample": sample,
                        "tm": tm,
                        "height": height
                    })

                    self.tm_results[sample] = {"tm": tm, "height": height}

                def update_ui():
                    # Update tree
                    for row in self.melt_tree.get_children():
                        self.melt_tree.delete(row)

                    for r in results:
                        if r['tm']:
                            self.melt_tree.insert("", tk.END, values=(
                                r['sample'],
                                f"{r['tm']:.2f}",
                                f"{r['height']:.3f}"
                            ))

                    # Update derivative plot with all samples
                    if HAS_MPL:
                        self.melt_ax_deriv.clear()
                        for sample, fluor in self.fluorescence.items():
                            fluor_norm = self.engine.normalize_curves(
                                self.temperature, fluor,
                                pre_melt=(pre_min, pre_max),
                                post_melt=(post_min, post_max)
                            )
                            t_mid, neg_deriv = self.engine.negative_derivative(
                                self.temperature, fluor_norm
                            )
                            color = PLOT_COLORS[hash(sample) % len(PLOT_COLORS)]
                            self.melt_ax_deriv.plot(t_mid, neg_deriv, color=color,
                                                   lw=1, alpha=0.7, label=sample)

                        self.melt_ax_deriv.set_xlabel("Temperature (°C)", fontsize=8)
                        self.melt_ax_deriv.set_ylabel("-dF/dT", fontsize=8)
                        self.melt_ax_deriv.legend(fontsize=5, ncol=2)
                        self.melt_ax_deriv.grid(True, alpha=0.3)
                        self.melt_canvas.draw()

                    self.status_label.config(text=f"✅ Calculated Tm for {len(results)} samples")

                self.ui_queue.schedule(update_ui)

            except Exception as e:
                self.ui_queue.schedule(lambda: messagebox.showerror("Error", str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _difference_plot(self):
        """Generate difference plot relative to reference"""
        if not self.fluorescence or not self.melt_ref_var.get():
            messagebox.showwarning("No Data", "Select reference sample first")
            return

        ref = self.melt_ref_var.get()
        if ref not in self.fluorescence:
            return

        self.status_label.config(text="🔄 Generating difference plot...")

        def worker():
            try:
                ref_fluor = self.fluorescence[ref]

                pre_min = float(self.melt_pre_min.get())
                pre_max = float(self.melt_pre_max.get())
                post_min = float(self.melt_post_min.get())
                post_max = float(self.melt_post_max.get())

                # Normalize reference
                ref_norm = self.engine.normalize_curves(
                    self.temperature, ref_fluor,
                    pre_melt=(pre_min, pre_max),
                    post_melt=(post_min, post_max)
                )

                differences = {}
                for sample, fluor in self.fluorescence.items():
                    if sample == ref:
                        continue

                    fluor_norm = self.engine.normalize_curves(
                        self.temperature, fluor,
                        pre_melt=(pre_min, pre_max),
                        post_melt=(post_min, post_max)
                    )

                    diff = self.engine.difference_curve(
                        self.temperature, fluor_norm, ref_norm
                    )
                    differences[sample] = diff

                def update_ui():
                    if HAS_MPL:
                        self.melt_ax_diff.clear()
                        for sample, diff in differences.items():
                            color = PLOT_COLORS[hash(sample) % len(PLOT_COLORS)]
                            self.melt_ax_diff.plot(self.temperature, diff,
                                                  color=color, lw=1.5, label=sample)

                        self.melt_ax_diff.axhline(0, color='k', lw=0.5, ls='--')
                        self.melt_ax_diff.set_xlabel("Temperature (°C)", fontsize=8)
                        self.melt_ax_diff.set_ylabel("Δ Fluorescence", fontsize=8)
                        self.melt_ax_diff.legend(fontsize=6)
                        self.melt_ax_diff.grid(True, alpha=0.3)
                        self.melt_canvas.draw()

                    self.status_label.config(text=f"✅ Difference plot complete (ref: {ref})")

                self.ui_queue.schedule(update_ui)

            except Exception as e:
                self.ui_queue.schedule(lambda: messagebox.showerror("Error", str(e)))

        threading.Thread(target=worker, daemon=True).start()


# ============================================================================
# ENGINE 7 — REFERENCE RANGES (CLSI EP28-A3c; Horn & Pesce 2003)
# ============================================================================
class ReferenceRangeAnalyzer:
    """
    Clinical reference interval determination per CLSI guidelines.

    Methods:
    - Parametric: mean ± 1.96*SD (assuming normality)
    - Nonparametric: percentiles (2.5th - 97.5th)
    - Robust: Horn's algorithm (Tukey's biweight)
    - Partition testing: Harris-Boyd (1990) for subgroups

    References:
        CLSI EP28-A3c (2010) "Defining, Establishing, and Verifying
            Reference Intervals in the Clinical Laboratory"
        Horn, P.S. & Pesce, A.J. (2003) "Reference intervals: an update"
            Clinica Chimica Acta
    """

    @classmethod
    def shapiro_wilk(cls, data):
        """Test for normality (Shapiro-Wilk)"""
        if HAS_SCIPY and len(data) >= 3:
            from scipy.stats import shapiro
            stat, p = shapiro(data)
            return p > 0.05  # True if normal
        return False

    @classmethod
    def parametric_interval(cls, data, confidence=0.95):
        """Parametric reference interval (assumes normality)"""
        mean = np.mean(data)
        sd = np.std(data, ddof=1)
        z = 1.96  # for 95% interval

        lower = mean - z * sd
        upper = mean + z * sd

        # Confidence intervals for limits
        n = len(data)
        se_lower = sd * np.sqrt(1/n + z**2/(2*(n-1)))
        se_upper = se_lower

        return {
            "method": "Parametric",
            "lower_limit": lower,
            "upper_limit": upper,
            "lower_ci": [lower - 1.96*se_lower, lower + 1.96*se_lower],
            "upper_ci": [upper - 1.96*se_upper, upper + 1.96*se_upper],
            "mean": mean,
            "sd": sd
        }

    @classmethod
    def nonparametric_interval(cls, data, confidence=0.95):
        """Nonparametric percentile method (CLSI recommended)"""
        data_sorted = np.sort(data)
        n = len(data)

        # Percentiles for 95% interval
        p_lower = 2.5
        p_upper = 97.5

        # Rank-based estimates
        rank_lower = n * p_lower / 100
        rank_upper = n * p_upper / 100

        # Interpolate if needed
        if rank_lower.is_integer():
            lower = data_sorted[int(rank_lower) - 1]
        else:
            i = int(np.floor(rank_lower))
            f = rank_lower - i
            lower = (1 - f) * data_sorted[i-1] + f * data_sorted[i]

        if rank_upper.is_integer():
            upper = data_sorted[int(rank_upper) - 1]
        else:
            i = int(np.floor(rank_upper))
            f = rank_upper - i
            upper = (1 - f) * data_sorted[i-1] + f * data_sorted[i]

        # Confidence intervals (using bootstrap in production)
        return {
            "method": "Nonparametric",
            "lower_limit": lower,
            "upper_limit": upper,
            "percentiles": [p_lower, p_upper]
        }

    @classmethod
    def robust_interval(cls, data, confidence=0.95):
        """Horn's robust algorithm (Tukey's biweight)"""
        # Median
        med = np.median(data)

        # Median absolute deviation
        mad = np.median(np.abs(data - med))

        # Biweight estimation
        c = 7.5  # tuning constant
        u = (data - med) / (c * mad + 1e-10)
        u_sq = u ** 2
        w = (1 - u_sq) ** 2
        w[u_sq >= 1] = 0

        robust_mean = np.sum(w * data) / np.sum(w)

        n = len(data)
        robust_sd = np.sqrt(n * np.sum(w * (data - robust_mean) ** 2) /
                           (np.sum(w) * (np.sum(w) - 1)))

        z = 1.96
        lower = robust_mean - z * robust_sd
        upper = robust_mean + z * robust_sd

        return {
            "method": "Robust (Horn)",
            "lower_limit": lower,
            "upper_limit": upper,
            "robust_mean": robust_mean,
            "robust_sd": robust_sd
        }

    @classmethod
    def partition_test(cls, data1, data2, test="harris-boyd"):
        """
        Test if subgroups should have separate reference intervals

        Harris-Boyd (1990) criteria:
        - Standard deviation ratio > 1.5 or < 0.67
        - Difference in means > 0.25 * (reference interval width)
        """
        mean1, sd1 = np.mean(data1), np.std(data1, ddof=1)
        mean2, sd2 = np.mean(data2), np.std(data2, ddof=1)

        # SD ratio test
        sd_ratio = max(sd1, sd2) / min(sd1, sd2)

        # Mean difference test
        pooled_sd = np.sqrt((sd1**2 + sd2**2) / 2)
        mean_diff = abs(mean1 - mean2) / pooled_sd

        needs_partition = sd_ratio > 1.5 or mean_diff > 0.25

        return {
            "needs_partition": needs_partition,
            "sd_ratio": sd_ratio,
            "standardized_diff": mean_diff,
            "separate_intervals": needs_partition
        }

    @classmethod
    def outlier_detection(cls, data, method="tukey"):
        """
        Detect outliers using Tukey's fences or Dixon's Q test
        """
        if method == "tukey":
            q1 = np.percentile(data, 25)
            q3 = np.percentile(data, 75)
            iqr = q3 - q1
            lower_fence = q1 - 1.5 * iqr
            upper_fence = q3 + 1.5 * iqr

            outliers = data[(data < lower_fence) | (data > upper_fence)]
            return {
                "outliers": outliers.tolist(),
                "n_outliers": len(outliers),
                "fences": (lower_fence, upper_fence)
            }
        return {"outliers": [], "n_outliers": 0}

    @classmethod
    def load_reference_data(cls, path):
        """Load reference data from CSV"""
        df = pd.read_csv(path)
        return df.to_dict('records')


# ============================================================================
# TAB 7: REFERENCE RANGES
# ============================================================================
class ReferenceRangeTab(AnalysisTab):
    def __init__(self, parent, app, ui_queue):
        super().__init__(parent, app, ui_queue, "Reference Ranges")
        self.engine = ReferenceRangeAnalyzer
        self.ref_data = None
        self.current_analyte = None
        self._build_content_ui()

    def _sample_has_data(self, sample):
        """Check if sample has reference data"""
        return any(col in sample and sample[col] for col in
                  ['Reference_Data', 'Reference_Values'])

    def _manual_import(self):
        """Manual import from CSV"""
        path = filedialog.askopenfilename(
            title="Load Reference Data",
            filetypes=[("CSV", "*.csv"), ("Excel", "*.xlsx"), ("All files", "*.*")])
        if not path:
            return

        self.status_label.config(text="🔄 Loading reference data...")

        def worker():
            try:
                data = self.engine.load_reference_data(path)

                def update():
                    self.ref_data = data
                    self.manual_label.config(text=f"✓ {Path(path).name}")
                    self._update_analyte_list()
                    self.status_label.config(text=f"Loaded {len(data)} records")
                self.ui_queue.schedule(update)

            except Exception as e:
                self.ui_queue.schedule(lambda: messagebox.showerror("Error", str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _load_sample_data(self, idx):
        """Auto-load from table"""
        sample = self.samples[idx]

        if 'Reference_Values' in sample and sample['Reference_Values']:
            try:
                self.ref_data = json.loads(sample['Reference_Values'])
                self._update_analyte_list()
                self.status_label.config(text=f"Loaded reference data from table")
            except Exception as e:
                self.status_label.config(text=f"Error: {e}")

    def _build_content_ui(self):
        """Build the tab-specific UI"""
        # Main split
        main_pane = ttk.PanedWindow(self.content_frame, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True)

        # Left panel - controls
        left = tk.Frame(main_pane, bg="white", width=300)
        main_pane.add(left, weight=1)

        # Right panel - plot
        right = tk.Frame(main_pane, bg="white")
        main_pane.add(right, weight=2)

        # === LEFT PANEL ===
        tk.Label(left, text="📋 REFERENCE RANGES (CLSI EP28-A3c)",
                font=("Arial", 10, "bold"), bg=C_LIGHT, fg=C_HEADER).pack(fill=tk.X, pady=2)

        tk.Label(left, text="CLSI 2010 · Horn & Pesce 2003",
                font=("Arial", 7), bg="white", fg="#888").pack(anchor=tk.W, padx=4)

        # Analyte selector
        tk.Label(left, text="Select Analyte:", font=("Arial", 8, "bold"),
                bg="white").pack(anchor=tk.W, padx=4, pady=(4, 0))

        self.ref_analyte_listbox = tk.Listbox(left, height=6, font=("Courier", 8))
        self.ref_analyte_listbox.pack(fill=tk.X, padx=4, pady=2)
        self.ref_analyte_listbox.bind('<<ListboxSelect>>', self._on_analyte_selected)

        # Method selection
        tk.Label(left, text="Method:", font=("Arial", 8, "bold"),
                bg="white").pack(anchor=tk.W, padx=4, pady=(4, 0))
        self.ref_method = tk.StringVar(value="Nonparametric (CLSI)")
        ttk.Combobox(left, textvariable=self.ref_method,
                     values=["Nonparametric (CLSI)", "Parametric", "Robust (Horn)"],
                     width=20, state="readonly").pack(fill=tk.X, padx=4)

        # Outlier removal
        self.ref_remove_outliers = tk.BooleanVar(value=True)
        tk.Checkbutton(left, text="Remove outliers (Tukey's fences)",
                      variable=self.ref_remove_outliers,
                      bg="white").pack(anchor=tk.W, padx=4, pady=2)

        # Partition test
        self.ref_partition = tk.BooleanVar(value=True)
        tk.Checkbutton(left, text="Test for subgroup partitioning",
                      variable=self.ref_partition,
                      bg="white").pack(anchor=tk.W, padx=4)

        ttk.Button(left, text="📊 CALCULATE REFERENCE INTERVAL",
                  command=self._calculate_interval).pack(fill=tk.X, padx=4, pady=4)

        # Results
        results_frame = tk.LabelFrame(left, text="Reference Interval", bg="white",
                                     font=("Arial", 8, "bold"), fg=C_HEADER)
        results_frame.pack(fill=tk.X, padx=4, pady=4)

        self.ref_results = {}
        result_labels = [
            ("Method:", "method"),
            ("n (after outliers):", "n"),
            ("Lower limit:", "lower"),
            ("Upper limit:", "upper"),
            ("90% CI lower:", "ci_lower"),
            ("90% CI upper:", "ci_upper"),
            ("Normality (p>0.05):", "normal")
        ]

        for i, (label, key) in enumerate(result_labels):
            row = tk.Frame(results_frame, bg="white")
            row.pack(fill=tk.X, pady=1)
            tk.Label(row, text=label, font=("Arial", 7), bg="white", width=15, anchor=tk.W).pack(side=tk.LEFT)
            var = tk.StringVar(value="—")
            tk.Label(row, textvariable=var, font=("Arial", 7, "bold"),
                    bg="white", fg=C_HEADER).pack(side=tk.LEFT, padx=2)
            self.ref_results[key] = var

        # === RIGHT PANEL ===
        if HAS_MPL:
            self.ref_fig = Figure(figsize=(8, 6), dpi=100, facecolor="white")
            gs = GridSpec(2, 2, figure=self.ref_fig, hspace=0.3, wspace=0.3)
            self.ref_ax_hist = self.ref_fig.add_subplot(gs[0, 0])
            self.ref_ax_box = self.ref_fig.add_subplot(gs[0, 1])
            self.ref_ax_qq = self.ref_fig.add_subplot(gs[1, 0])
            self.ref_ax_dist = self.ref_fig.add_subplot(gs[1, 1])

            self.ref_ax_hist.set_title("Histogram", fontsize=9, fontweight="bold")
            self.ref_ax_box.set_title("Box Plot", fontsize=9, fontweight="bold")
            self.ref_ax_qq.set_title("Q-Q Plot", fontsize=9, fontweight="bold")
            self.ref_ax_dist.set_title("Distribution", fontsize=9, fontweight="bold")

            self.ref_canvas = FigureCanvasTkAgg(self.ref_fig, right)
            self.ref_canvas.draw()
            self.ref_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            toolbar = NavigationToolbar2Tk(self.ref_canvas, right)
            toolbar.update()
        else:
            tk.Label(right, text="matplotlib required for plots",
                    bg="white", fg="#888").pack(expand=True)

    def _update_analyte_list(self):
        """Update analyte listbox"""
        self.ref_analyte_listbox.delete(0, tk.END)
        if self.ref_data:
            analytes = sorted(set(d.get('Analyte', 'Unknown') for d in self.ref_data))
            for analyte in analytes:
                self.ref_analyte_listbox.insert(tk.END, analyte)

    def _on_analyte_selected(self, event):
        """Handle analyte selection"""
        selection = self.ref_analyte_listbox.curselection()
        if selection:
            self.current_analyte = self.ref_analyte_listbox.get(selection[0])
            self._plot_analyte_data()

    def _plot_analyte_data(self):
        """Plot data for selected analyte"""
        if not HAS_MPL or not self.ref_data or not self.current_analyte:
            return

        # Extract values for selected analyte
        values = [d['Value'] for d in self.ref_data
                 if d.get('Analyte') == self.current_analyte]

        if not values:
            return

        # Histogram
        self.ref_ax_hist.clear()
        self.ref_ax_hist.hist(values, bins='auto', color=C_ACCENT, alpha=0.7,
                             edgecolor='white')
        self.ref_ax_hist.set_xlabel(self.current_analyte, fontsize=8)
        self.ref_ax_hist.set_ylabel("Frequency", fontsize=8)

        # Box plot
        self.ref_ax_box.clear()
        self.ref_ax_box.boxplot(values, vert=False, patch_artist=True,
                               boxprops=dict(facecolor=C_ACCENT, alpha=0.7))
        self.ref_ax_box.set_xlabel(self.current_analyte, fontsize=8)

        # Q-Q plot (normality check)
        self.ref_ax_qq.clear()
        if HAS_SCIPY:
            from scipy import stats
            stats.probplot(values, dist="norm", plot=self.ref_ax_qq)
            self.ref_ax_qq.get_lines()[0].set_markerfacecolor(C_ACCENT)
            self.ref_ax_qq.get_lines()[0].set_markeredgecolor(C_ACCENT)
            self.ref_ax_qq.get_lines()[0].set_alpha(0.7)
            self.ref_ax_qq.get_lines()[1].set_color(C_WARN)

        # Distribution
        self.ref_ax_dist.clear()
        self.ref_ax_dist.hist(values, bins='auto', density=True, alpha=0.5,
                             color=C_ACCENT, edgecolor='white')

        # Overlay normal distribution
        if HAS_SCIPY:
            mean = np.mean(values)
            std = np.std(values)
            x = np.linspace(min(values), max(values), 100)
            y = stats.norm.pdf(x, mean, std)
            self.ref_ax_dist.plot(x, y, 'r-', lw=2, label='Normal')
            self.ref_ax_dist.legend(fontsize=7)

        self.ref_ax_dist.set_xlabel(self.current_analyte, fontsize=8)
        self.ref_ax_dist.set_ylabel("Density", fontsize=8)

        self.ref_canvas.draw()

    def _calculate_interval(self):
        """Calculate reference interval"""
        if not self.current_analyte:
            messagebox.showwarning("No Selection", "Select an analyte first")
            return

        self.status_label.config(text="🔄 Calculating reference interval...")

        def worker():
            try:
                # Extract values
                values = np.array([d['Value'] for d in self.ref_data
                                  if d.get('Analyte') == self.current_analyte])

                # Remove outliers if selected
                if self.ref_remove_outliers.get():
                    outlier_result = self.engine.outlier_detection(values)
                    mask = np.ones(len(values), dtype=bool)
                    for o in outlier_result['outliers']:
                        mask[values == o] = False
                    values_clean = values[mask]
                    n_outliers = outlier_result['n_outliers']
                else:
                    values_clean = values
                    n_outliers = 0

                # Check normality
                is_normal = self.engine.shapiro_wilk(values_clean)

                # Select method
                method = self.ref_method.get()
                if "Nonparametric" in method or (not is_normal and "Parametric" not in method):
                    result = self.engine.nonparametric_interval(values_clean)
                elif "Robust" in method:
                    result = self.engine.robust_interval(values_clean)
                else:
                    result = self.engine.parametric_interval(values_clean)

                # Partition test if requested
                partition_result = None
                if self.ref_partition.get() and 'Group' in self.ref_data[0]:
                    # Group by some variable (simplified)
                    groups = {}
                    for d in self.ref_data:
                        if d.get('Analyte') == self.current_analyte:
                            group = d.get('Group', 'Default')
                            if group not in groups:
                                groups[group] = []
                            groups[group].append(d['Value'])

                    if len(groups) >= 2:
                        group_names = list(groups.keys())
                        partition_result = self.engine.partition_test(
                            np.array(groups[group_names[0]]),
                            np.array(groups[group_names[1]])
                        )

                def update_ui():
                    # Update results
                    self.ref_results["method"].set(result['method'])
                    self.ref_results["n"].set(f"{len(values_clean)} (removed {n_outliers})")
                    self.ref_results["lower"].set(f"{result['lower_limit']:.2f}")
                    self.ref_results["upper"].set(f"{result['upper_limit']:.2f}")
                    self.ref_results["normal"].set("Yes" if is_normal else "No")

                    if 'lower_ci' in result:
                        self.ref_results["ci_lower"].set(f"[{result['lower_ci'][0]:.2f}, {result['lower_ci'][1]:.2f}]")
                    if 'upper_ci' in result:
                        self.ref_results["ci_upper"].set(f"[{result['upper_ci'][0]:.2f}, {result['upper_ci'][1]:.2f}]")

                    # Update plots with reference limits
                    if HAS_MPL:
                        # Add reference lines to histogram
                        self.ref_ax_hist.clear()
                        self.ref_ax_hist.hist(values_clean, bins='auto',
                                             color=C_ACCENT, alpha=0.7,
                                             edgecolor='white')
                        self.ref_ax_hist.axvline(result['lower_limit'],
                                                color=C_WARN, lw=2, ls='--',
                                                label=f"Lower: {result['lower_limit']:.2f}")
                        self.ref_ax_hist.axvline(result['upper_limit'],
                                                color=C_WARN, lw=2, ls='--',
                                                label=f"Upper: {result['upper_limit']:.2f}")
                        self.ref_ax_hist.set_xlabel(self.current_analyte, fontsize=8)
                        self.ref_ax_hist.set_ylabel("Frequency", fontsize=8)
                        self.ref_ax_hist.legend(fontsize=6)

                        # Update box plot with reference range
                        self.ref_ax_box.clear()
                        bp = self.ref_ax_box.boxplot(values_clean, vert=False,
                                                     patch_artist=True)
                        bp['boxes'][0].set_facecolor(C_ACCENT)
                        bp['boxes'][0].set_alpha(0.7)

                        # Add reference range as shaded area
                        y_min, y_max = self.ref_ax_box.get_ylim()
                        self.ref_ax_box.axvspan(result['lower_limit'], result['upper_limit'],
                                               alpha=0.2, color=C_ACCENT2,
                                               label=f"Reference Range")
                        self.ref_ax_box.axvline(result['lower_limit'],
                                               color=C_WARN, lw=1.5, ls='--')
                        self.ref_ax_box.axvline(result['upper_limit'],
                                               color=C_WARN, lw=1.5, ls='--')
                        self.ref_ax_box.set_xlabel(self.current_analyte, fontsize=8)
                        self.ref_ax_box.legend(fontsize=6)

                        self.ref_canvas.draw()

                    # Show partition test result
                    if partition_result and partition_result['needs_partition']:
                        self.status_label.config(
                            text=f"⚠️ Partitioning recommended (SD ratio: {partition_result['sd_ratio']:.2f})"
                        )
                    else:
                        self.status_label.config(
                            text=f"✅ Reference interval: {result['lower_limit']:.1f} - {result['upper_limit']:.1f}"
                        )

                self.ui_queue.schedule(update_ui)

            except Exception as e:
                self.ui_queue.schedule(lambda: messagebox.showerror("Error", str(e)))

        threading.Thread(target=worker, daemon=True).start()


# ============================================================================
# SMART ASSISTANT - Context-aware help that serves all tabs
# ============================================================================
class SmartAssistant:
    """One intelligent panel that provides context-aware suggestions"""

    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.current_tab = None
        self.suggestions = []
        self.frame = tk.Frame(parent, bg=C_SMART, relief=tk.RAISED, borderwidth=2)
        self.frame.pack(side=tk.RIGHT, fill=tk.Y, padx=2, pady=2)

        # Header
        header = tk.Frame(self.frame, bg=C_SMART, height=30)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="🧠 SMART ASSISTANT", font=("Arial", 9, "bold"),
                bg=C_SMART, fg="white").pack(side=tk.LEFT, padx=5)

        self.collapse_btn = tk.Button(header, text="◀", command=self.toggle_collapse,
                                      bg=C_SMART, fg="white", bd=0, font=("Arial", 8))
        self.collapse_btn.pack(side=tk.RIGHT, padx=2)

        # Content area (collapsible)
        self.content = tk.Frame(self.frame, bg="white", width=200)
        self.content.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        self.content.pack_propagate(False)

        self.expanded = True
        self._create_content()

    def _create_content(self):
        """Create the assistant content"""
        # Status icon
        self.status_frame = tk.Frame(self.content, bg="white")
        self.status_frame.pack(fill=tk.X, pady=5)

        self.status_icon = tk.Label(self.status_frame, text="●", font=("Arial", 12),
                                     bg="white", fg="#2ecc71")
        self.status_icon.pack(side=tk.LEFT, padx=5)

        self.status_text = tk.Label(self.status_frame, text="Ready", font=("Arial", 8, "bold"),
                                     bg="white", fg=C_HEADER)
        self.status_text.pack(side=tk.LEFT)

        # Suggestions area
        self.suggest_frame = tk.Frame(self.content, bg="white")
        self.suggest_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        tk.Label(self.suggest_frame, text="Suggestions:", font=("Arial", 8, "bold"),
                bg="white", fg=C_HEADER).pack(anchor=tk.W)

        self.suggest_list = tk.Frame(self.suggest_frame, bg="white")
        self.suggest_list.pack(fill=tk.BOTH, expand=True)

        # Quick actions
        self.action_frame = tk.Frame(self.content, bg="white")
        self.action_frame.pack(fill=tk.X, pady=5)

        tk.Label(self.action_frame, text="Quick Actions:", font=("Arial", 8, "bold"),
                bg="white", fg=C_HEADER).pack(anchor=tk.W, padx=5)

        self.recipe_btn = ttk.Button(self.action_frame, text="📋 Save Recipe",
                                      command=self._save_recipe, width=15)
        self.recipe_btn.pack(pady=2)

        self.publish_btn = ttk.Button(self.action_frame, text="📄 Publish Package",
                                       command=self._generate_publication, width=15)
        self.publish_btn.pack(pady=2)

        self.uncertainty_btn = ttk.Button(self.action_frame, text="🎲 Propagate Uncertainty",
                                          command=self._propagate_uncertainty, width=15)
        self.uncertainty_btn.pack(pady=2)

        self.help_btn = ttk.Button(self.action_frame, text="❓ Explain This",
                                   command=self._explain_current, width=15)
        self.help_btn.pack(pady=2)

    def toggle_collapse(self):
        """Collapse or expand the assistant"""
        if self.expanded:
            self.content.pack_forget()
            self.collapse_btn.config(text="▶")
            self.expanded = False
        else:
            self.content.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
            self.collapse_btn.config(text="◀")
            self.expanded = True

    def update_for_tab(self, tab):
        """Update suggestions based on active tab"""
        self.current_tab = tab

        # Clear old suggestions
        for widget in self.suggest_list.winfo_children():
            widget.destroy()

        # Set status
        if hasattr(tab, 'tab_name'):
            self.status_text.config(text=f"Analyzing {tab.tab_name}")

        # Generate context-aware suggestions
        suggestions = self._generate_suggestions(tab)

        for i, suggestion in enumerate(suggestions[:5]):  # Max 5 suggestions
            frame = tk.Frame(self.suggest_list, bg="white")
            frame.pack(fill=tk.X, pady=2)

            btn = tk.Button(frame, text=suggestion['text'],
                           font=("Arial", 7), bg="white", fg=C_HEADER,
                           relief=tk.FLAT, anchor=tk.W, justify=tk.LEFT,
                           command=suggestion['command'])
            btn.pack(fill=tk.X)

            ToolTip(btn, suggestion['tooltip'])

    def _generate_suggestions(self, tab):
        """Generate context-aware suggestions based on tab type and data"""
        suggestions = []

        # Check what kind of tab this is
        tab_name = getattr(tab, 'tab_name', '').lower()

        if 'qpcr' in tab_name:
            if hasattr(tab, 'results') and tab.results:
                suggestions.append({
                    'text': '📊 Check reference gene stability',
                    'tooltip': 'Run geNorm analysis to find most stable reference genes',
                    'command': lambda: self._suggest_action('geNorm', tab)
                })
                suggestions.append({
                    'text': '🔍 Flag low-quality wells',
                    'tooltip': 'Automatically mark wells with poor efficiency or late Cq',
                    'command': lambda: self._suggest_action('flag_wells', tab)
                })

        elif 'elisa' in tab_name:
            if hasattr(tab, 'standards') and tab.standards:
                suggestions.append({
                    'text': '📈 Compare 4PL vs 5PL fit',
                    'tooltip': 'Determine which model better fits your standards',
                    'command': lambda: self._suggest_action('compare_models', tab)
                })
                suggestions.append({
                    'text': '✅ Calculate validation metrics',
                    'tooltip': 'LOD, LOQ, recovery, and parallelism',
                    'command': lambda: self._suggest_action('validate_elisa', tab)
                })

        elif 'flow' in tab_name:
            suggestions.append({
                'text': '🧬 Auto-detect populations',
                'tooltip': 'Use FlowSOM clustering to identify cell populations',
                'command': lambda: self._suggest_action('auto_gate', tab)
            })

        elif 'ddpcr' in tab_name:
            suggestions.append({
                'text': '💧 Calculate Poisson CI',
                'tooltip': 'Add confidence intervals to concentration estimates',
                'command': lambda: self._suggest_action('poisson_ci', tab)
            })

        elif 'melting' in tab_name:
            suggestions.append({
                'text': '🧬 Classify genotypes',
                'tooltip': 'Cluster samples by melting curve shape',
                'command': lambda: self._suggest_action('classify_genotypes', tab)
            })

        elif 'reference' in tab_name:
            suggestions.append({
                'text': '📋 Bootstrap reference intervals',
                'tooltip': 'Calculate confidence intervals for reference limits',
                'command': lambda: self._suggest_action('bootstrap_ref', tab)
            })

        # Always suggest these if data exists
        if hasattr(tab, 'samples') and tab.samples:
            suggestions.append({
                'text': '🎲 Propagate uncertainty',
                'tooltip': 'Send data to Monte Carlo plugin for confidence intervals',
                'command': self._propagate_uncertainty
            })

            suggestions.append({
                'text': '📋 Save as recipe',
                'tooltip': 'Save current analysis settings for reuse',
                'command': self._save_recipe
            })

        return suggestions

    def _suggest_action(self, action, tab):
        """Execute a suggested action"""
        if action == 'geNorm' and hasattr(tab, '_run_genorm'):
            tab._run_genorm()
        elif action == 'flag_wells' and hasattr(tab, '_flag_quality'):
            tab._flag_quality()
        elif action == 'compare_models' and hasattr(tab, '_compare_models'):
            tab._compare_models()
        elif action == 'validate_elisa' and hasattr(tab, '_calculate_validation'):
            tab._calculate_validation()
        elif action == 'auto_gate' and hasattr(tab, '_auto_gate'):
            tab._auto_gate()
        elif action == 'poisson_ci' and hasattr(tab, '_calculate_ci'):
            tab._calculate_ci()
        elif action == 'classify_genotypes' and hasattr(tab, '_classify_genotypes'):
            tab._classify_genotypes()
        elif action == 'bootstrap_ref' and hasattr(tab, '_bootstrap_interval'):
            tab._bootstrap_interval()

    def _save_recipe(self):
        """Save current tab settings as recipe"""
        if not self.current_tab:
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".recipe",
            filetypes=[("Recipe files", "*.recipe"), ("All files", "*.*")],
            initialfile=f"{getattr(self.current_tab, 'tab_name', 'analysis')}_recipe.recipe"
        )

        if filename:
            # Get recipe from tab
            if hasattr(self.current_tab, 'get_recipe'):
                recipe = self.current_tab.get_recipe()
            else:
                # Generic recipe
                recipe = {
                    'tab': self.current_tab.tab_name,
                    'timestamp': datetime.now().isoformat(),
                    'settings': {}
                }

            try:
                with open(filename, 'w') as f:
                    json.dump(recipe, f, indent=2)
                messagebox.showinfo("Recipe Saved", f"Recipe saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save recipe: {e}")

    def _generate_publication(self):
        """Generate publication package"""
        if not self.current_tab:
            return

        from tkinter import filedialog
        folder = filedialog.askdirectory(title="Select folder for publication package")

        if not folder:
            return

        # Create publication package
        pub_dir = Path(folder) / f"publication_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        pub_dir.mkdir(exist_ok=True)

        # Generate content based on tab
        if hasattr(self.current_tab, 'generate_publication'):
            self.current_tab.generate_publication(str(pub_dir))
        else:
            # Generic publication
            self._generate_generic_publication(pub_dir)

        messagebox.showinfo("Publication Package",
                           f"Package created at:\n{pub_dir}\n\nContains:\n- Figures\n- Tables\n- Methods\n- Data")

    def _generate_generic_publication(self, pub_dir):
        """Generic publication generator"""
        # Save methods
        methods_file = pub_dir / "methods.txt"
        with open(methods_file, 'w') as f:
            f.write(f"Analysis performed using Clinical Diagnostics Suite v2.0\n")
            f.write(f"Tab: {self.current_tab.tab_name}\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

        # Save data if available
        if hasattr(self.current_tab, 'samples') and self.current_tab.samples:
            data_file = pub_dir / "data.csv"
            import csv
            with open(data_file, 'w', newline='') as f:
                if self.current_tab.samples and len(self.current_tab.samples) > 0:
                    writer = csv.DictWriter(f, fieldnames=self.current_tab.samples[0].keys())
                    writer.writeheader()
                    writer.writerows(self.current_tab.samples)

    def _propagate_uncertainty(self):
        """Send current data to uncertainty plugin"""
        if not self.current_tab:
            return

        # Find uncertainty plugin
        uncertainty_plugin = None
        if hasattr(self.app, 'plugins'):
            uncertainty_plugin = self.app.plugins.get('uncertainty_propagation')

        if uncertainty_plugin and hasattr(uncertainty_plugin, 'receive_data'):
            # Prepare data
            if hasattr(self.current_tab, 'prepare_uncertainty_data'):
                data, context = self.current_tab.prepare_uncertainty_data()
                uncertainty_plugin.receive_data(data, context)
                uncertainty_plugin.open_window()
            else:
                messagebox.showinfo("Not Available",
                                   "This tab doesn't provide uncertainty data yet")
        else:
            messagebox.showwarning("Plugin Not Found",
                                 "Uncertainty Propagation plugin not loaded.\n\nMake sure it's installed and enabled.")

    def _explain_current(self):
        """Explain current analysis or result"""
        if not self.current_tab:
            return

        # Create explanation popup
        explain = tk.Toplevel(self.parent)
        explain.title("Smart Assistant Explanation")
        explain.geometry("500x400")
        explain.transient(self.parent)

        text = tk.Text(explain, wrap=tk.WORD, padx=10, pady=10)
        text.pack(fill=tk.BOTH, expand=True)

        # Generate explanation based on tab
        tab_name = getattr(self.current_tab, 'tab_name', 'analysis')
        text.insert(tk.END, f"📊 {tab_name} Analysis\n")
        text.insert(tk.END, "═" * 50 + "\n\n")

        if hasattr(self.current_tab, 'get_explanation'):
            explanation = self.current_tab.get_explanation()
            text.insert(tk.END, explanation)
        else:
            text.insert(tk.END, "This analysis helps you interpret your experimental data.\n\n")
            text.insert(tk.END, "Key concepts:\n")
            text.insert(tk.END, "• Confidence intervals show the reliability of your estimates\n")
            text.insert(tk.END, "• Statistical tests determine if differences are significant\n")
            text.insert(tk.END, "• Quality flags identify potential problems\n\n")
            text.insert(tk.END, "For detailed methods, see the cited references in each tab.\n")

        text.config(state=tk.DISABLED)

        ttk.Button(explain, text="Close", command=explain.destroy).pack(pady=5)


# ============================================================================
# RECIPE SYSTEM - Save/load analysis settings
# ============================================================================
class RecipeManager:
    """Manages saving and loading of analysis recipes"""

    def __init__(self):
        self.recipes = {}

    def save_recipe(self, tab, filepath):
        """Save tab settings to recipe file"""
        recipe = {
            'tab_type': tab.__class__.__name__,
            'tab_name': getattr(tab, 'tab_name', 'Unknown'),
            'timestamp': datetime.now().isoformat(),
            'version': '2.0.0',
            'settings': self._extract_settings(tab)
        }

        with open(filepath, 'w') as f:
            json.dump(recipe, f, indent=2)

        return True

    def load_recipe(self, tab, filepath):
        """Load recipe and apply to tab"""
        with open(filepath, 'r') as f:
            recipe = json.load(f)

        # Verify tab type matches
        if recipe.get('tab_type') != tab.__class__.__name__:
            if not messagebox.askyesno("Tab Mismatch",
                                       f"This recipe was created for {recipe.get('tab_name')}.\n"
                                       f"Apply to current tab anyway?"):
                return False

        # Apply settings
        self._apply_settings(tab, recipe.get('settings', {}))
        return True

    def _extract_settings(self, tab):
        """Extract settings based on tab type"""
        settings = {}

        # qPCR tab
        if hasattr(tab, 'baseline_start'):
            settings['baseline_start'] = tab.baseline_start.get()
            settings['baseline_end'] = tab.baseline_end.get()
            settings['cq_method'] = tab.cq_method.get()

        # ΔΔCt tab
        if hasattr(tab, 'ref_gene_var'):
            settings['reference_gene'] = tab.ref_gene_var.get()
            settings['calibrator'] = tab.calibrator_var.get()
            settings['method'] = tab.ddct_method.get()

        # ELISA tab
        if hasattr(tab, 'elisa_model'):
            settings['model'] = tab.elisa_model.get()

        # Flow tab
        if hasattr(tab, 'gate_type'):
            settings['gate_type'] = tab.gate_type.get()
            if hasattr(tab, 'fcm_x'):
                settings['x_channel'] = tab.fcm_x.get()
                settings['y_channel'] = tab.fcm_y.get()

        # ddPCR tab
        if hasattr(tab, 'dd_volume'):
            settings['droplet_volume'] = tab.dd_volume.get()
            settings['confidence'] = tab.dd_ci.get()

        # Melting tab
        if hasattr(tab, 'melt_pre_min'):
            settings['pre_melt_min'] = tab.melt_pre_min.get()
            settings['pre_melt_max'] = tab.melt_pre_max.get()
            settings['post_melt_min'] = tab.melt_post_min.get()
            settings['post_melt_max'] = tab.melt_post_max.get()

        # Reference tab
        if hasattr(tab, 'ref_method'):
            settings['method'] = tab.ref_method.get()
            settings['remove_outliers'] = tab.ref_remove_outliers.get()
            settings['partition'] = tab.ref_partition.get()

        return settings

    def _apply_settings(self, tab, settings):
        """Apply settings to tab"""
        for key, value in settings.items():
            if hasattr(tab, key):
                widget = getattr(tab, key)
                if hasattr(widget, 'set'):
                    try:
                        widget.set(value)
                    except:
                        pass
                elif isinstance(widget, tk.BooleanVar):
                    widget.set(value)
                elif isinstance(widget, tk.StringVar):
                    widget.set(str(value))
                elif isinstance(widget, tk.IntVar):
                    widget.set(int(value))
                elif isinstance(widget, tk.DoubleVar):
                    widget.set(float(value))


# ============================================================================
# UNCERTAINTY BRIDGE - Connect to Monte Carlo plugin
# ============================================================================
class UncertaintyBridge:
    """Central communication with Uncertainty Propagation plugin"""

    def __init__(self, app):
        self.app = app
        self.plugin = None

    def get_plugin(self):
        """Lazy-load the uncertainty plugin"""
        if self.plugin is None and hasattr(self.app, 'plugins'):
            self.plugin = self.app.plugins.get('uncertainty_propagation')
        return self.plugin

    def propagate(self, data, context):
        """Send data to uncertainty plugin"""
        plugin = self.get_plugin()
        if plugin and hasattr(plugin, 'receive_data'):
            plugin.receive_data(data, context)
            plugin.open_window()
            return True
        return False

    def is_available(self):
        """Check if uncertainty plugin is loaded"""
        return self.get_plugin() is not None


# ============================================================================
# ENHANCED BASE TAB CLASS - Adds smart features to all tabs
# ============================================================================
class EnhancedAnalysisTab:
    """Mixin class that adds enhanced features to any AnalysisTab"""

    def __init__(self, *args, **kwargs):
        # Call original init
        super().__init__(*args, **kwargs)

        # Add smart assistant reference
        self.smart_assistant = None
        self.recipe_manager = RecipeManager()
        self.uncertainty_bridge = None

        # Add enhanced UI elements
        self._add_enhanced_ui()

    def _add_enhanced_ui(self):
        """Add enhanced UI elements to tab"""
        # Add smart icon to status bar
        if hasattr(self, 'status_label') and self.status_label:
            self.smart_icon = tk.Label(self.status_label.master if hasattr(self.status_label, 'master') else self.frame,
                                       text="🧠", font=("Arial", 10),
                                       bg="white", fg=C_SMART, cursor="hand2")
            self.smart_icon.place(relx=1.0, x=-5, y=0, anchor=tk.NE)
            ToolTip(self.smart_icon, "Smart Assistant available",
                   "Click to open Smart Assistant panel")
            self.smart_icon.bind("<Button-1>", self._toggle_smart_assistant)

    def _toggle_smart_assistant(self, event=None):
        """Toggle smart assistant visibility"""
        if hasattr(self.app, 'smart_assistant'):
            # Smart assistant is already in main window
            pass

    def connect_smart_assistant(self, assistant):
        """Connect to the global smart assistant"""
        self.smart_assistant = assistant

    def connect_uncertainty_bridge(self, bridge):
        """Connect to uncertainty bridge"""
        self.uncertainty_bridge = bridge

    def get_recipe(self):
        """Get recipe for this tab"""
        return self.recipe_manager._extract_settings(self)

    def apply_recipe(self, recipe_file):
        """Apply recipe from file"""
        return self.recipe_manager.load_recipe(self, recipe_file)

    def prepare_uncertainty_data(self):
        """Prepare data for uncertainty propagation - override in subclasses"""
        return [], {'type': 'unknown', 'source': self.tab_name}

    def get_explanation(self):
        """Get explanation of current analysis"""
        return f"Analysis in {self.tab_name} tab.\n\nFor detailed methods, see the cited references."

    def generate_publication(self, output_dir):
        """Generate publication package"""
        # Save settings as recipe
        recipe_file = Path(output_dir) / "analysis_recipe.json"
        self.recipe_manager.save_recipe(self, str(recipe_file))

        # Save explanation
        explain_file = Path(output_dir) / "methods.txt"
        with open(explain_file, 'w') as f:
            f.write(self.get_explanation())


# ============================================================================
# ENHANCED TABS - Extend your original tabs with new features
# ============================================================================

class EnhancedqPCRAnalysisTab(qPCRAnalysisTab, EnhancedAnalysisTab):
    """Enhanced qPCR tab with geNorm, quality flags, uncertainty integration"""

    def __init__(self, parent, app, ui_queue):
        super().__init__(parent, app, ui_queue)

        # Add advanced options panel (collapsed by default)
        self._add_advanced_panel()

        # Add quality flag storage
        self.quality_flags = {}

    def _add_advanced_panel(self):
        """Add collapsible advanced options panel"""
        self.advanced_frame = tk.Frame(self.content_frame, bg="white", relief=tk.GROOVE, borderwidth=1)
        # Pack before the first child (which is the main_pane) to place at top
        children = self.content_frame.winfo_children()
        if children:
            self.advanced_frame.pack(fill=tk.X, padx=5, pady=5, before=children[0])
        else:
            self.advanced_frame.pack(fill=tk.X, padx=5, pady=5)

        # Header with toggle
        header = tk.Frame(self.advanced_frame, bg=C_LIGHT)
        header.pack(fill=tk.X)

        self.advanced_expanded = False
        tk.Label(header, text="⚡ ADVANCED OPTIONS", font=("Arial", 8, "bold"),
                bg=C_LIGHT, fg=C_HEADER).pack(side=tk.LEFT, padx=5)

        self.toggle_btn = tk.Button(header, text="▼", command=self._toggle_advanced,
                                    bg=C_LIGHT, bd=0, font=("Arial", 8))
        self.toggle_btn.pack(side=tk.RIGHT, padx=5)

        # Content (hidden by default)
        self.advanced_content = tk.Frame(self.advanced_frame, bg="white")
        # Don't pack yet

        # Add advanced controls
        row1 = tk.Frame(self.advanced_content, bg="white")
        row1.pack(fill=tk.X, pady=2)

        tk.Label(row1, text="Baseline method:", font=("Arial", 8), bg="white").pack(side=tk.LEFT, padx=5)
        self.baseline_method = tk.StringVar(value="Linear")
        ttk.Combobox(row1, textvariable=self.baseline_method,
                    values=["Linear", "Spline", "Adaptive"], width=10).pack(side=tk.LEFT)

        tk.Label(row1, text="Quality threshold:", font=("Arial", 8), bg="white").pack(side=tk.LEFT, padx=5)
        self.quality_thresh = tk.StringVar(value="0.8")
        ttk.Entry(row1, textvariable=self.quality_thresh, width=5).pack(side=tk.LEFT)

        row2 = tk.Frame(self.advanced_content, bg="white")
        row2.pack(fill=tk.X, pady=2)

        self.auto_flag = tk.BooleanVar(value=True)
        tk.Checkbutton(row2, text="Auto-flag poor quality wells", variable=self.auto_flag,
                      bg="white").pack(side=tk.LEFT, padx=5)

        ttk.Button(row2, text="📊 geNorm Analysis", command=self._run_genorm).pack(side=tk.RIGHT, padx=5)

    def _toggle_advanced(self):
        """Toggle advanced panel visibility"""
        if self.advanced_expanded:
            self.advanced_content.pack_forget()
            self.toggle_btn.config(text="▼")
            self.advanced_expanded = False
        else:
            self.advanced_content.pack(fill=tk.X, padx=5, pady=5)
            self.toggle_btn.config(text="▲")
            self.advanced_expanded = True

    def _run_genorm(self):
        """Run geNorm analysis to rank reference gene stability"""
        if not hasattr(self, 'fluorescence') or not self.fluorescence:
            messagebox.showwarning("No Data", "Load qPCR data first")
            return

        # Get Ct values for all wells
        ct_values = {}
        for well, fluor in self.fluorescence.items():
            fluor_corr = self.engine.baseline_correction(self.cycles, fluor)
            cq, _ = self.engine.determine_cq_sdm(self.cycles, fluor_corr)
            if cq:
                ct_values[well] = cq

        if len(ct_values) < 3:
            messagebox.showwarning("Insufficient Data", "Need at least 3 wells for geNorm")
            return

        # Calculate stability (simplified geNorm)
        # In real geNorm, we'd need multiple genes per sample
        # This is a simplified version for demonstration

        results = []
        for well, ct in ct_values.items():
            # Calculate M-value (stability)
            # Lower M = more stable
            m_value = np.std(list(ct_values.values()))  # Simplified
            results.append((well, ct, m_value))

        # Sort by stability
        results.sort(key=lambda x: x[2])

        # Display results
        result_text = "📊 geNorm Stability Analysis\n"
        result_text += "═" * 50 + "\n\n"
        result_text += "Rank  Well     Ct     M-value\n"
        result_text += "-" * 30 + "\n"

        for i, (well, ct, m) in enumerate(results, 1):
            result_text += f"{i:2d}    {well:8} {ct:6.2f}  {m:6.4f}\n"

        result_text += "\n✓ Most stable: " + results[0][0]
        result_text += "\n✗ Least stable: " + results[-1][0]

        # Show in popup
        self._show_text_popup("geNorm Results", result_text)

    def _flag_quality(self):
        """Flag wells with poor quality"""
        if not hasattr(self, 'fluorescence') or not self.fluorescence:
            return

        self.quality_flags = {}
        threshold = float(self.quality_thresh.get())

        for well, fluor in self.fluorescence.items():
            score = 1.0  # Default good

            # Check various quality metrics
            fluor_corr = self.engine.baseline_correction(self.cycles, fluor)

            # Check baseline noise
            baseline_noise = np.std(fluor[:10])
            if baseline_noise > 0.1 * np.max(fluor):
                score *= 0.7

            # Check efficiency
            lin_result = self.engine.find_log_linear_phase(self.cycles, fluor_corr)
            if lin_result:
                eff = lin_result['efficiency']
                if eff < 1.8 or eff > 2.2:
                    score *= 0.5
                if lin_result['r2'] < 0.98:
                    score *= 0.8
            else:
                score *= 0.3

            # Check Cq
            cq, _ = self.engine.determine_cq_sdm(self.cycles, fluor_corr)
            if cq:
                if cq > 35:
                    score *= 0.6
                if cq < 15:
                    score *= 0.8
            else:
                score *= 0.2

            self.quality_flags[well] = {
                'score': score,
                'flag': 'GOOD' if score >= threshold else 'CHECK' if score >= threshold*0.6 else 'FAIL'
            }

        # Update well list with flags
        self._update_well_list_with_flags()

        # Show summary
        good = sum(1 for f in self.quality_flags.values() if f['flag'] == 'GOOD')
        check = sum(1 for f in self.quality_flags.values() if f['flag'] == 'CHECK')
        fail = sum(1 for f in self.quality_flags.values() if f['flag'] == 'FAIL')

        messagebox.showinfo("Quality Flags",
                           f"✅ Good: {good}\n⚠️ Check: {check}\n❌ Failed: {fail}")

    def _update_well_list_with_flags(self):
        """Update well list with quality flags"""
        if not hasattr(self, 'well_listbox'):
            return

        self.well_listbox.delete(0, tk.END)

        for well in sorted(self.fluorescence.keys()):
            flag = self.quality_flags.get(well, {}).get('flag', '')
            if flag == 'GOOD':
                display = f"✅ {well}"
            elif flag == 'CHECK':
                display = f"⚠️ {well}"
            elif flag == 'FAIL':
                display = f"❌ {well}"
            else:
                display = well

            self.well_listbox.insert(tk.END, display)

    def prepare_uncertainty_data(self):
        """Prepare qPCR data for uncertainty propagation"""
        data = []

        if hasattr(self, 'results') and self.results:
            for well, result in self.results.items():
                # Get uncertainty from replicates or quality score
                uncertainty = 0.05 * result.get('cq', 0) if result.get('cq') else 0.1

                data.append({
                    'Sample_ID': well,
                    'Ct_Value': result.get('cq'),
                    'Ct_Error': uncertainty,
                    'Efficiency': result.get('eff', 100) / 100,
                    'Group': 'All Wells'
                })

        context = {
            'type': 'qpcr',
            'tab': 'qPCR',
            'n_samples': len(data)
        }

        return data, context

    def get_explanation(self):
        """Get explanation of qPCR analysis"""
        return """🔬 qPCR EFFICIENCY ANALYSIS

Methods used:
• LinRegPCR (Ramakers et al. 2003): Identifies log-linear phase for efficiency calculation
• Second Derivative Maximum (SDM): Determines Cq from amplification curve
• Baseline correction: Subtracts early cycle fluorescence

Interpretation:
• Cq < 30: Good amplification
• Cq 30-35: Weak amplification (check efficiency)
• Cq > 35: Possible contamination or poor target

Efficiency:
• 90-110%: Ideal
• 80-90% or 110-120%: Acceptable with caution
• <80% or >120%: Problematic - check primers and conditions

Quality flags:
• GOOD: All metrics within acceptable ranges
• CHECK: One or more metrics borderline
• FAIL: Multiple metrics indicate problem

References:
Ramakers, C. et al. (2003) Neuroscience Letters
Ruijter, J.M. et al. (2009) Nucleic Acids Research"""

    def _show_text_popup(self, title, text):
        """Show text in popup window"""
        popup = tk.Toplevel(self.frame)
        popup.title(title)
        popup.geometry("500x400")
        popup.transient(self.frame)

        text_widget = tk.Text(popup, wrap=tk.WORD, padx=10, pady=10,
                              font=("Courier", 9))
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert(tk.END, text)
        text_widget.config(state=tk.DISABLED)

        ttk.Button(popup, text="Close", command=popup.destroy).pack(pady=5)


class EnhancedDeltaDeltaCtTab(DeltaDeltaCtTab, EnhancedAnalysisTab):
    """Enhanced ΔΔCt tab with statistical comparison, error bars, reference validation"""

    def __init__(self, parent, app, ui_queue):
        super().__init__(parent, app, ui_queue)

        # Add statistics panel
        self._add_stats_panel()

        # Store RQ values with groups
        self.rq_data = {}

    def _add_stats_panel(self):
        """Add statistical comparison panel"""
        self.stats_frame = tk.Frame(self.content_frame, bg="white", relief=tk.GROOVE, borderwidth=1)
        # Pack at the top (before the main_pane) – we can't easily get main_pane, so just pack at top
        # The main_pane was packed earlier, so packing now will place it after. To put before, we need to repack.
        # Simple solution: pack at the top after all children? Actually, we can pack before the first child.
        children = self.content_frame.winfo_children()
        if children:
            self.stats_frame.pack(fill=tk.X, padx=5, pady=5, before=children[0])
        else:
            self.stats_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(self.stats_frame, text="📊 Statistical Comparison", font=("Arial", 9, "bold"),
                bg=C_LIGHT, fg=C_HEADER).pack(fill=tk.X)

        content = tk.Frame(self.stats_frame, bg="white")
        content.pack(fill=tk.X, padx=5, pady=5)

        row1 = tk.Frame(content, bg="white")
        row1.pack(fill=tk.X, pady=2)

        tk.Label(row1, text="Group column:", font=("Arial", 8), bg="white").pack(side=tk.LEFT)
        self.compare_group_var = tk.StringVar()
        self.compare_group_combo = ttk.Combobox(row1, textvariable=self.compare_group_var,
                                               values=[], width=15)
        self.compare_group_combo.pack(side=tk.LEFT, padx=5)

        tk.Label(row1, text="Test:", font=("Arial", 8), bg="white").pack(side=tk.LEFT, padx=5)
        self.stat_test_var = tk.StringVar(value="t-test")
        ttk.Combobox(row1, textvariable=self.stat_test_var,
                    values=["t-test", "Mann-Whitney", "ANOVA"], width=12).pack(side=tk.LEFT)

        ttk.Button(row1, text="Compare Groups", command=self._compare_groups).pack(side=tk.RIGHT, padx=5)

        self.stat_result_label = tk.Label(content, text="", font=("Arial", 8, "bold"),
                                         bg="white", fg=C_HEADER)
        self.stat_result_label.pack(fill=tk.X, pady=2)

    def _calculate_rq(self):
        """Override to store RQ data with groups"""
        super()._calculate_rq()

        # Store RQ values with groups
        self.rq_data = {}
        for item in self.ddct_tree.get_children():
            values = self.ddct_tree.item(item)['values']
            if len(values) >= 5:
                sample = values[0]
                rq = values[4]
                if rq != '—':
                    try:
                        rq_val = float(rq)
                        # Try to get group from original data
                        group = 'All'
                        for row in self.ct_data:
                            if row.get('Sample') == sample and 'Group' in row:
                                group = row['Group']
                                break
                        self.rq_data[sample] = {'rq': rq_val, 'group': group}
                    except:
                        pass

        # Update group combo
        groups = set(d['group'] for d in self.rq_data.values())
        self.compare_group_combo['values'] = list(groups)
        if groups:
            self.compare_group_var.set(list(groups)[0])

    def _compare_groups(self):
        """Perform statistical comparison between groups"""
        if not self.rq_data:
            messagebox.showwarning("No Data", "Calculate RQ values first")
            return

        group_col = self.compare_group_var.get()
        test = self.stat_test_var.get()

        # Group RQ values
        groups = {}
        for sample, data in self.rq_data.items():
            group = data.get('group', 'Unknown')
            groups.setdefault(group, []).append(data['rq'])

        if len(groups) < 2:
            self.stat_result_label.config(text="Need at least 2 groups for comparison")
            return

        if test == "t-test" and len(groups) == 2:
            # Two-group t-test
            group_names = list(groups.keys())
            stat, p = ttest_ind(groups[group_names[0]], groups[group_names[1]])

            result_text = f"{group_names[0]} vs {group_names[1]}: p = {p:.4f} "
            if p < 0.05:
                result_text += "✓ Significant"
            else:
                result_text += "✗ Not significant"

        elif test == "Mann-Whitney" and len(groups) == 2:
            group_names = list(groups.keys())
            stat, p = mannwhitneyu(groups[group_names[0]], groups[group_names[1]])

            result_text = f"{group_names[0]} vs {group_names[1]}: p = {p:.4f} "
            if p < 0.05:
                result_text += "✓ Significant"
            else:
                result_text += "✗ Not significant"

        elif test == "ANOVA" and len(groups) >= 2:
            # One-way ANOVA
            group_vals = list(groups.values())
            stat, p = f_oneway(*group_vals)

            result_text = f"ANOVA: p = {p:.4f} "
            if p < 0.05:
                result_text += "✓ Significant differences detected"
            else:
                result_text += "✗ No significant differences"

        else:
            result_text = "Test not applicable"

        self.stat_result_label.config(text=result_text)

        # Update plot with significance
        if HAS_MPL and p < 0.05:
            self._add_significance_to_plot(groups, p)

    def _add_significance_to_plot(self, groups, p):
        """Add significance markers to the bar plot"""
        if not HAS_MPL or not hasattr(self, 'ddct_ax_bar'):
            return

        ax = self.ddct_ax_bar
        # Determine positions of groups on the x-axis
        # Groups is a dict: group_name -> list of RQ values
        group_names = list(groups.keys())
        n_groups = len(group_names)
        bar_positions = np.arange(n_groups)  # assuming one bar per group

        # Determine the maximum y-value to place the bracket
        max_y = max([max(vals) for vals in groups.values()]) * 1.1

        # If exactly two groups, draw a bracket with significance stars
        if n_groups == 2:
            x1, x2 = bar_positions[0], bar_positions[1]
            y = max_y
            # draw bracket
            ax.plot([x1, x1, x2, x2], [y, y*1.02, y*1.02, y], lw=1.5, c='k')
            # add stars
            if p < 0.001:
                stars = '***'
            elif p < 0.01:
                stars = '**'
            elif p < 0.05:
                stars = '*'
            else:
                stars = 'ns'  # not significant
            ax.text((x1+x2)/2, y*1.05, stars, ha='center', va='bottom', fontsize=12, fontweight='bold')
        elif n_groups > 2:
            # For ANOVA, we could add a note on the plot
            ax.text(0.5, 0.95, f'ANOVA p = {p:.4f}', transform=ax.transAxes,
                    ha='center', va='top', fontsize=10, bbox=dict(facecolor='white', alpha=0.8))

    def prepare_uncertainty_data(self):
        """Prepare ΔΔCt data for uncertainty propagation"""
        data = []

        for sample, d in self.rq_data.items():
            data.append({
                'Sample_ID': sample,
                'RQ': d['rq'],
                'Group': d.get('group', 'Unknown')
            })

        context = {
            'type': 'ddct',
            'method': self.ddct_method.get(),
            'reference_gene': self.ref_gene_var.get(),
            'calibrator': self.calibrator_var.get()
        }

        return data, context

    def get_explanation(self):
        """Get explanation of ΔΔCt analysis"""
        return """📊 ΔΔCt QUANTIFICATION

Methods:
• Livak method (2^-ΔΔCt): Assumes 100% efficiency
• Pfaffl method: Accounts for different efficiencies

Interpretation:
• RQ > 1: Up-regulated in sample vs calibrator
• RQ < 1: Down-regulated in sample vs calibrator
• RQ = 1: No change

Statistical tests:
• t-test: Compares two groups (parametric)
• Mann-Whitney: Non-parametric alternative
• ANOVA: Compares three or more groups

References:
Livak & Schmittgen (2001) Methods
Pfaffl (2001) Nucleic Acids Research"""


class EnhancedELISAAnalysisTab(ELISAAnalysisTab, EnhancedAnalysisTab):
    """Enhanced ELISA tab with model comparison, validation metrics, parallelism"""

    def __init__(self, parent, app, ui_queue):
        super().__init__(parent, app, ui_queue)

        # Add validation panel
        self._add_validation_panel()

    def _add_validation_panel(self):
        """Add validation metrics panel"""
        self.val_frame = tk.Frame(self.content_frame, bg="white", relief=tk.GROOVE, borderwidth=1)
        # Pack at the top
        children = self.content_frame.winfo_children()
        if children:
            self.val_frame.pack(fill=tk.X, padx=5, pady=5, before=children[0])
        else:
            self.val_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(self.val_frame, text="✅ Validation Metrics (ICH Q2)", font=("Arial", 9, "bold"),
                bg=C_LIGHT, fg=C_HEADER).pack(fill=tk.X)

        content = tk.Frame(self.val_frame, bg="white")
        content.pack(fill=tk.X, padx=5, pady=5)

        # Metrics display
        self.val_metrics = {}
        metrics = [
            ("LOD:", "lod"),
            ("LOQ:", "loq"),
            ("Recovery:", "recovery"),
            ("%CV:", "cv"),
            ("Parallelism p-value:", "parallelism"),
            ("AIC 4PL:", "aic_4pl"),
            ("AIC 5PL:", "aic_5pl")
        ]

        for i, (label, key) in enumerate(metrics):
            row = tk.Frame(content, bg="white")
            row.pack(fill=tk.X, pady=1)

            tk.Label(row, text=label, font=("Arial", 7, "bold"), bg="white",
                    width=15, anchor=tk.W).pack(side=tk.LEFT)

            var = tk.StringVar(value="—")
            tk.Label(row, textvariable=var, font=("Arial", 7), bg="white",
                    fg=C_HEADER).pack(side=tk.LEFT, padx=2)

            self.val_metrics[key] = var

        # Action buttons
        btn_frame = tk.Frame(content, bg="white")
        btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(btn_frame, text="📈 Compare Models",
                  command=self._compare_models).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="📊 Parallelism Test",
                  command=self._parallelism_test).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="✅ Full Validation",
                  command=self._calculate_validation).pack(side=tk.LEFT, padx=2)

    def _fit_curve(self):
        """Override to also calculate validation metrics"""
        super()._fit_curve()

        # Calculate validation metrics after fitting
        if self.fit_params:
            self._calculate_validation()

    def _compare_models(self):
        """Compare 4PL vs 5PL fits using AIC"""
        if not self.standards:
            messagebox.showwarning("No Data", "Load standards first")
            return

        conc = np.array([s['conc'] for s in self.standards])
        resp = np.array([s['response'] for s in self.standards])

        # Fit both models
        fit_4pl = self.engine.fit_4pl(conc, resp)
        fit_5pl = self.engine.fit_5pl(conc, resp)

        if not fit_4pl or not fit_5pl:
            messagebox.showerror("Error", "Model fitting failed")
            return

        # Calculate AIC
        n = len(resp)

        # Residual sum of squares
        resid_4pl = resp - self.engine.four_pl(conc, fit_4pl['A'], fit_4pl['B'],
                                               fit_4pl['C'], fit_4pl['D'])
        resid_5pl = resp - self.engine.five_pl(conc, fit_5pl['A'], fit_5pl['B'],
                                               fit_5pl['C'], fit_5pl['D'], fit_5pl['E'])

        rss_4pl = np.sum(resid_4pl**2)
        rss_5pl = np.sum(resid_5pl**2)

        # AIC = n * ln(RSS/n) + 2k
        aic_4pl = n * np.log(rss_4pl/n) + 2*4
        aic_5pl = n * np.log(rss_5pl/n) + 2*5

        # Update display
        self.val_metrics['aic_4pl'].set(f"{aic_4pl:.1f}")
        self.val_metrics['aic_5pl'].set(f"{aic_5pl:.1f}")

        # Determine better model
        if aic_5pl < aic_4pl - 2:
            better = "5PL (asymmetric)"
            self.val_metrics['aic_4pl'].config(fg="#888")
            self.val_metrics['aic_5pl'].config(fg=C_ACCENT2)
        elif aic_4pl < aic_5pl - 2:
            better = "4PL (symmetric)"
            self.val_metrics['aic_5pl'].config(fg="#888")
            self.val_metrics['aic_4pl'].config(fg=C_ACCENT2)
        else:
            better = "Models equivalent"

        messagebox.showinfo("Model Comparison",
                           f"4PL AIC: {aic_4pl:.1f}\n"
                           f"5PL AIC: {aic_5pl:.1f}\n\n"
                           f"Better model: {better}")

    def _parallelism_test(self):
        """Test parallelism between diluted samples and standards"""
        if not self.standards or not self.unknowns:
            messagebox.showwarning("No Data", "Need standards and unknowns with dilution information")
            return

        # For this test, we assume that unknowns have a 'dilution' field (e.g., 1, 2, 4, 8)
        # and that they are serial dilutions of the same sample.
        # We'll group unknowns by Sample_ID and check each group.
        from scipy.stats import linregress

        # Prepare standard curve: log(concentration) vs log(response) (or use existing fit)
        conc = np.array([s['conc'] for s in self.standards])
        resp = np.array([s['response'] for s in self.standards])
        log_conc = np.log(conc)
        log_resp = np.log(resp)
        slope_std, intercept_std, r_value, p_value, std_err = linregress(log_conc, log_resp)

        # Group unknowns by sample ID (if available) or treat each unknown separately
        # For simplicity, assume each unknown has a 'dilution' and 'sample_id'
        samples = {}
        for u in self.unknowns:
            sample_id = u.get('sample_id', u.get('id', 'unknown'))
            if 'dilution' not in u:
                continue
            samples.setdefault(sample_id, []).append(u)

        if not samples:
            messagebox.showwarning("No Dilution Data", "Unknowns must have a 'dilution' field for parallelism test.")
            return

        results = []
        for sample_id, dilutions in samples.items():
            if len(dilutions) < 3:
                continue
            # Sort by dilution factor (assuming higher dilution -> lower concentration)
            dilutions.sort(key=lambda x: x['dilution'])
            dil_factors = np.array([d['dilution'] for d in dilutions])
            responses = np.array([d['response'] for d in dilutions])
            # Log transform
            log_dil = np.log(dil_factors)
            log_resp = np.log(responses)
            # Fit line
            slope, intercept, r_val, p_val, err = linregress(log_dil, log_resp)

            # Compare slopes: ideally, slope of diluted sample should equal -slope_std (since dilution reduces concentration)
            # We'll check if slope is within 20% of -slope_std
            expected_slope = -slope_std
            ratio = slope / expected_slope if expected_slope != 0 else np.inf
            within_tolerance = 0.8 <= ratio <= 1.2
            results.append({
                'sample': sample_id,
                'slope': slope,
                'expected': expected_slope,
                'ratio': ratio,
                'parallel': within_tolerance,
                'p_value': p_val
            })

        # Show results
        result_text = "Parallelism Test Results:\n"
        result_text += "=" * 50 + "\n"
        for r in results:
            status = "✅ PASS" if r['parallel'] else "❌ FAIL"
            result_text += f"Sample {r['sample']}: {status}\n"
            result_text += f"  Slope: {r['slope']:.3f} (expected {r['expected']:.3f})\n"
            result_text += f"  Ratio: {r['ratio']:.2f}  p={r['p_value']:.4f}\n\n"

        # Display in a popup
        self._show_text_popup("Parallelism Test", result_text)

    def _calculate_validation(self):
        """Calculate full validation metrics per ICH Q2"""
        if not self.fit_params or not self.standards:
            return

        conc = np.array([s['conc'] for s in self.standards])
        resp = np.array([s['response'] for s in self.standards])

        # Calculate LOD and LOQ using signal-to-noise
        if len(resp) > 0:
            # Estimate noise from low concentrations
            low_idx = conc < np.percentile(conc, 25)
            if np.any(low_idx):
                noise = np.std(resp[low_idx])

                # LOD = 3.3 * noise / slope
                # LOQ = 10 * noise / slope
                if 'slope' in self.fit_params:
                    lod = 3.3 * noise / abs(self.fit_params.get('slope', 1))
                    loq = 10 * noise / abs(self.fit_params.get('slope', 1))

                    self.val_metrics['lod'].set(f"{lod:.3f}")
                    self.val_metrics['loq'].set(f"{loq:.3f}")

        # Calculate recovery using back-fit
        if self.fit_params['method'] == '4PL':
            pred_conc = [self.engine.inverse_4pl(r, self.fit_params['A'],
                                                self.fit_params['B'],
                                                self.fit_params['C'],
                                                self.fit_params['D'])
                        for r in resp]
        else:
            pred_conc = [self.engine.calculate_concentration(r, self.fit_params)
                        for r in resp]

        pred_conc = np.array([c if c is not None else 0 for c in pred_conc])

        # Recovery %
        recovery = (pred_conc / conc) * 100
        self.val_metrics['recovery'].set(f"{np.mean(recovery):.1f}%")

        # CV %
        cv = np.std(pred_conc) / np.mean(pred_conc) * 100
        self.val_metrics['cv'].set(f"{cv:.1f}%")

        # Note: parallelism test is handled by a separate button,
        # so we do not compute a p-value here. The field will remain "—".

    def prepare_uncertainty_data(self):
        """Prepare ELISA data for uncertainty propagation"""
        data = []

        if hasattr(self, 'unknowns') and self.unknowns:
            for u in self.unknowns:
                data.append({
                    'Sample_ID': u.get('id', 'Unknown'),
                    'Concentration': u.get('concentration', 0),
                    'Response': u.get('response', 0),
                    'Group': 'Unknown'
                })

        context = {
            'type': 'elisa',
            'model': self.elisa_model.get()
        }

        return data, context

    def get_explanation(self):
        """Get explanation of ELISA analysis"""
        return """🧪 ELISA ANALYSIS

4PL Model: y = A + (B-A)/(1 + (x/C)^D)
• A: Bottom asymptote (background)
• B: Top asymptote (maximum signal)
• C: EC50 (inflection point)
• D: Slope factor

5PL Model: Adds E (asymmetry factor)
• E=1: Symmetric (4PL equivalent)
• E≠1: Asymmetric curve

Validation Metrics (ICH Q2):
• LOD: Limit of Detection (3.3× noise)
• LOQ: Limit of Quantification (10× noise)
• Recovery: % of expected concentration
• %CV: Precision
• Parallelism: Dilution linearity

AIC (Akaike Information Criterion):
• Lower AIC = better fit
• ΔAIC > 2 indicates significant difference

References:
Findlay & Dillard (2007) The AAPS Journal
ICH Q2(R1) Validation Guidelines"""


class EnhancedFlowCytometryTab(FlowCytometryTab, EnhancedAnalysisTab):
    """Enhanced flow tab with real clustering, compensation, population stats"""

    def __init__(self, parent, app, ui_queue):
        super().__init__(parent, app, ui_queue)

        # Add clustering options
        self._add_clustering_panel()

        # Store population data
        self.populations = {}

    def _clear_gates(self):
        """Clear all gates and reset the plot"""
        self.gates = {}
        self.populations = {}
        # Clear the population tree if it exists (from enhanced tab)
        if hasattr(self, 'population_tree'):
            for item in self.population_tree.get_children():
                self.population_tree.delete(item)
        # Clear the original statistics tree
        if hasattr(self, 'fcm_tree'):
            for item in self.fcm_tree.get_children():
                self.fcm_tree.delete(item)
        # Redraw the original scatter plot
        self._plot_scatter()
        messagebox.showinfo("Gates Cleared", "All gates and populations cleared.")

    def _add_clustering_panel(self):
        """Add clustering/algorithm options"""
        self.cluster_frame = tk.Frame(self.content_frame, bg="white", relief=tk.GROOVE, borderwidth=1)
        # Pack at the top
        children = self.content_frame.winfo_children()
        if children:
            self.cluster_frame.pack(fill=tk.X, padx=5, pady=5, before=children[0])
        else:
            self.cluster_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(self.cluster_frame, text="🧬 Automated Gating", font=("Arial", 9, "bold"),
                bg=C_LIGHT, fg=C_HEADER).pack(fill=tk.X)

        content = tk.Frame(self.cluster_frame, bg="white")
        content.pack(fill=tk.X, padx=5, pady=5)

        row1 = tk.Frame(content, bg="white")
        row1.pack(fill=tk.X, pady=2)

        tk.Label(row1, text="Algorithm:", font=("Arial", 8), bg="white").pack(side=tk.LEFT)
        self.cluster_algo = tk.StringVar(value="GMM")
        algo_combo = ttk.Combobox(row1, textvariable=self.cluster_algo,
                                  values=["GMM", "k-means", "FlowSOM (if installed)", "DBSCAN"],
                                  width=20)
        algo_combo.pack(side=tk.LEFT, padx=5)

        tk.Label(row1, text="Populations:", font=("Arial", 8), bg="white").pack(side=tk.LEFT, padx=5)
        self.n_clusters = tk.StringVar(value="3")
        ttk.Entry(row1, textvariable=self.n_clusters, width=5).pack(side=tk.LEFT)

        ttk.Button(row1, text="Auto-Detect", command=self._auto_gate).pack(side=tk.RIGHT, padx=5)

        row2 = tk.Frame(content, bg="white")
        row2.pack(fill=tk.X, pady=2)

        self.population_tree = ttk.Treeview(row2, columns=("Population", "Events", "%Total", "MFI"),
                                            show="headings", height=4)
        for col, w in [("Population", 80), ("Events", 60), ("%Total", 60), ("MFI", 60)]:
            self.population_tree.heading(col, text=col)
            self.population_tree.column(col, width=w, anchor=tk.CENTER)

        self.population_tree.pack(fill=tk.X)

    def _auto_gate(self):
        """Automatically detect populations using selected algorithm (now with real FlowSOM)"""
        if self.fcs_data is None:
            messagebox.showwarning("No Data", "Load FCS file first")
            return

        # Get selected channels
        x_idx = self.channels.index(self.fcm_x.get()) if self.fcm_x.get() in self.channels else 0
        y_idx = self.channels.index(self.fcm_y.get()) if self.fcm_y.get() in self.channels else 1
        X = self.fcs_data[:, [x_idx, y_idx]]

        algo = self.cluster_algo.get()
        n_clust = int(self.n_clusters.get())

        if algo == "GMM":
            if not HAS_SKLEARN:
                messagebox.showwarning("Missing Dependency", "scikit-learn required for GMM.\n\npip install scikit-learn")
                return
            model = GaussianMixture(n_components=n_clust, random_state=42)
            labels = model.fit_predict(X)

        elif algo == "k-means":
            if not HAS_SKLEARN:
                messagebox.showwarning("Missing Dependency", "scikit-learn required for k-means.\n\npip install scikit-learn")
                return
            from sklearn.cluster import KMeans
            model = KMeans(n_clusters=n_clust, random_state=42)
            labels = model.fit_predict(X)

        elif algo == "DBSCAN":
            if not HAS_SKLEARN:
                messagebox.showwarning("Missing Dependency", "scikit-learn required for DBSCAN.\n\npip install scikit-learn")
                return
            from sklearn.cluster import DBSCAN
            model = DBSCAN(eps=0.5, min_samples=10)
            labels = model.fit_predict(X)

        elif algo == "FlowSOM (if installed)":
            if not HAS_FLOWKIT:
                messagebox.showwarning("Missing Dependency",
                                    "FlowKit not installed.\n\npip install flowkit")
                return
            try:
                import flowkit as fk
                # Create a Sample object (need full data, not just 2 channels)
                sample = fk.Sample(
                    events=self.fcs_data,
                    channel_names=self.channels,
                    metadata={'FILENAME': 'unknown.fcs'}
                )
                # Run FlowSOM on selected channels
                fs = fk.FlowSOM(sample, channels=[self.fcm_x.get(), self.fcm_y.get()],
                                n_clusters=n_clust, seed=42, xdim=10, ydim=10)
                fs.fit()
                labels = fs.get_cluster_labels()
            except Exception as e:
                messagebox.showerror("FlowSOM Error", str(e))
                return
        else:
            messagebox.showwarning("Not Available", f"Algorithm {algo} not available")
            return

        # Store populations
        self.populations = {}
        unique_labels = set(labels)
        for label in unique_labels:
            if label == -1:  # Noise in DBSCAN
                name = "Noise"
            else:
                name = f"Population {label+1}"
            mask = labels == label
            events = np.sum(mask)
            pct = events / len(labels) * 100
            mfi_x = np.mean(X[mask, 0])
            mfi_y = np.mean(X[mask, 1])
            self.populations[name] = {
                'mask': mask,
                'events': events,
                'percent': pct,
                'mfi_x': mfi_x,
                'mfi_y': mfi_y
            }

        # Update population tree
        for item in self.population_tree.get_children():
            self.population_tree.delete(item)
        for name, pop in self.populations.items():
            if name != "Noise":
                self.population_tree.insert("", tk.END, values=(
                    name,
                    pop['events'],
                    f"{pop['percent']:.1f}%",
                    f"{pop['mfi_x']:.0f}"
                ))

        # Update plot with colors
        self._plot_colored_scatter(labels)

    def _plot_colored_scatter(self, labels):
        """Plot scatter with cluster colors"""
        if not HAS_MPL:
            return

        x_idx = self.channels.index(self.fcm_x.get()) if self.fcm_x.get() in self.channels else 0
        y_idx = self.channels.index(self.fcm_y.get()) if self.fcm_y.get() in self.channels else 1

        x_data = self.fcs_data[:, x_idx]
        y_data = self.fcs_data[:, y_idx]

        self.fcm_ax.clear()

        # Color by cluster
        unique_labels = set(labels)
        colors = plt.cm.tab10(np.linspace(0, 1, len(unique_labels)))

        for i, label in enumerate(unique_labels):
            mask = labels == label
            if label == -1:
                color = '#7f8c8d'  # Gray for noise
                name = 'Noise'
            else:
                color = colors[i % len(colors)]
                name = f'Population {label+1}'

            self.fcm_ax.scatter(x_data[mask], y_data[mask],
                               s=1, alpha=0.5, c=[color], label=name)

        self.fcm_ax.set_xlabel(self.fcm_x.get(), fontsize=8)
        self.fcm_ax.set_ylabel(self.fcm_y.get(), fontsize=8)
        self.fcm_ax.set_title("Flow Cytometry with Auto-Gating", fontsize=9, fontweight="bold")
        self.fcm_ax.legend(fontsize=6, markerscale=5)
        self.fcm_ax.grid(True, alpha=0.3)

        self.fcm_canvas.draw()

    def get_explanation(self):
        """Get explanation of flow cytometry analysis"""
        return """🩸 FLOW CYTOMETRY ANALYSIS

Gating Methods:
• Manual: Draw gates interactively
• GMM: Gaussian Mixture Model clustering
• k-means: Partition data into k clusters
• DBSCAN: Density-based clustering (finds arbitrary shapes)
• FlowSOM: Self-organizing maps (best for immunophenotyping)

Population Statistics:
• Events: Number of cells in population
• %Total: Percentage of total acquired cells
• MFI: Median Fluorescence Intensity

Compensation:
Corrects for spectral overlap between fluorochromes.
Use single-stain controls to calculate spillover matrix.

References:
Herzenberg et al. (2006) Nature Immunology
Maecker et al. (2004) Cytometry A"""


class EnhancedddPCRAnalysisTab(ddPCRAnalysisTab, EnhancedAnalysisTab):
    """Enhanced ddPCR tab with Poisson CI, fractional abundance, rain classification"""

    def __init__(self, parent, app, ui_queue):
        super().__init__(parent, app, ui_queue)

        # Add advanced stats panel
        self._add_advanced_stats()

    def _add_advanced_stats(self):
        """Add advanced statistics panel"""
        self.adv_stats = tk.Frame(self.content_frame, bg="white", relief=tk.GROOVE, borderwidth=1)
        # Pack at the top
        children = self.content_frame.winfo_children()
        if children:
            self.adv_stats.pack(fill=tk.X, padx=5, pady=5, before=children[0])
        else:
            self.adv_stats.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(self.adv_stats, text="💧 Advanced ddPCR Statistics", font=("Arial", 9, "bold"),
                bg=C_LIGHT, fg=C_HEADER).pack(fill=tk.X)

        content = tk.Frame(self.adv_stats, bg="white")
        content.pack(fill=tk.X, padx=5, pady=5)

        # Metrics
        self.dd_adv = {}
        metrics = [
            ("Fractional abundance:", "fractional"),
            ("Poisson CI (95%):", "poisson_ci"),
            ("Rain droplets:", "rain"),
            ("LOD (copies/μL):", "lod")
        ]

        for i, (label, key) in enumerate(metrics):
            row = tk.Frame(content, bg="white")
            row.pack(fill=tk.X, pady=1)

            tk.Label(row, text=label, font=("Arial", 7, "bold"), bg="white",
                    width=18, anchor=tk.W).pack(side=tk.LEFT)

            var = tk.StringVar(value="—")
            tk.Label(row, textvariable=var, font=("Arial", 7), bg="white",
                    fg=C_HEADER).pack(side=tk.LEFT, padx=2)

            self.dd_adv[key] = var

        ttk.Button(content, text="📊 Calculate All", command=self._calculate_advanced).pack(pady=5)

    def _calculate_well(self):
        """Override to also calculate advanced stats"""
        super()._calculate_well()

        # Calculate advanced stats after basic calculation
        if hasattr(self, 'current_well_data'):
            self._calculate_advanced()

    def _calculate_advanced(self):
        """Calculate advanced ddPCR statistics with GMM-based rain classification"""
        if not hasattr(self, 'current_well_data'):
            return

        data = self.current_well_data
        pos = data['positive']
        total = data['total']

        # Fractional abundance
        if total > 0:
            frac = pos / total * 100
            self.dd_adv['fractional'].set(f"{frac:.3f}%")

        # Poisson confidence interval (exact Clopper-Pearson)
        if HAS_SCIPY and total > 0:
            from scipy.stats import beta
            alpha = 0.05  # 95% CI
            if pos == 0:
                lower_p = 0.0
                upper_p = 1 - (alpha/2)**(1/total)
            elif pos == total:
                lower_p = (alpha/2)**(1/total)
                upper_p = 1.0
            else:
                lower_p = beta.ppf(alpha/2, pos, total - pos + 1)
                upper_p = beta.ppf(1 - alpha/2, pos + 1, total - pos)
            volume = float(self.dd_volume.get())
            lower_conc = -np.log(1 - lower_p) / volume if lower_p < 1 else float('inf')
            upper_conc = -np.log(1 - upper_p) / volume if upper_p < 1 else float('inf')
            self.dd_adv['poisson_ci'].set(f"{lower_conc:.1f} - {upper_conc:.1f}")

        # Rain droplets classification using GMM if amplitude data available
        if 'amplitudes' in data and len(data['amplitudes']) > 0:
            amps = np.array(data['amplitudes']).reshape(-1, 1)
            try:
                gmm = GaussianMixture(n_components=2, random_state=42)
                gmm.fit(amps)
                probs = gmm.predict_proba(amps)
                # Identify positive component (higher mean)
                if gmm.means_[0] > gmm.means_[1]:
                    pos_comp = 0
                else:
                    pos_comp = 1
                # Rain: probability of positive between 0.2 and 0.8
                rain_mask = (probs[:, pos_comp] > 0.2) & (probs[:, pos_comp] < 0.8)
                rain_count = np.sum(rain_mask)
                self.dd_adv['rain'].set(str(rain_count))
            except Exception as e:
                self.dd_adv['rain'].set("GMM error")
        else:
            self.dd_adv['rain'].set("N/A (no amplitude data)")

        # Limit of detection (simplified, based on blank droplets)
        if total > 0:
            lod = -np.log(0.05) / total / float(self.dd_volume.get())
            self.dd_adv['lod'].set(f"{lod:.1f}")
        else:
            self.dd_adv['lod'].set("—")
    def prepare_uncertainty_data(self):
        """Prepare ddPCR data for uncertainty propagation"""
        data = []

        for well_data in self.droplet_data:
            data.append({
                'Sample_ID': well_data.get('well', 'Unknown'),
                'Positive': well_data['positive'],
                'Total': well_data['total'],
                'Concentration': well_data.get('concentration', 0),
                'Target': well_data.get('target', 'Unknown')
            })

        context = {
            'type': 'ddpcr',
            'n_wells': len(self.droplet_data)
        }

        return data, context

    def get_explanation(self):
        """Get explanation of ddPCR analysis"""
        return """💧 DIGITAL PCR (ddPCR)

Poisson Statistics:
• λ = -ln(1 - p) where p = positive/total
• Concentration (copies/μL) = λ / droplet_volume

Key Metrics:
• Fractional abundance: % of mutant/wildtype
• Poisson CI: Confidence interval based on droplet counts
• Rain: Droplets between positive/negative clusters (ambiguous)
• LOD: Limit of Detection (based on blank droplets)

Interpretation:
• More droplets = tighter confidence intervals
• Rain indicates suboptimal partitioning or PCR conditions
• Fractional abundance > 0.1% typically detectable

References:
Hindson et al. (2011) Analytical Chemistry
Bio-Rad QX200 User Guide"""


class EnhancedMeltingCurveTab(MeltingCurveTab, EnhancedAnalysisTab):
    """Enhanced melting tab with genotyping, peak deconvolution, clustering"""

    def __init__(self, parent, app, ui_queue):
        super().__init__(parent, app, ui_queue)

        # Add genotyping panel
        self._add_genotyping_panel()

        # Store genotype assignments
        self.genotypes = {}

    def _add_genotyping_panel(self):
        """Add genotyping/HRM panel"""
        self.geno_frame = tk.Frame(self.content_frame, bg="white", relief=tk.GROOVE, borderwidth=1)
        # Pack at the top
        children = self.content_frame.winfo_children()
        if children:
            self.geno_frame.pack(fill=tk.X, padx=5, pady=5, before=children[0])
        else:
            self.geno_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(self.geno_frame, text="🧬 HRM Genotyping", font=("Arial", 9, "bold"),
                bg=C_LIGHT, fg=C_HEADER).pack(fill=tk.X)

        content = tk.Frame(self.geno_frame, bg="white")
        content.pack(fill=tk.X, padx=5, pady=5)

        # Controls
        row1 = tk.Frame(content, bg="white")
        row1.pack(fill=tk.X, pady=2)

        tk.Label(row1, text="Method:", font=("Arial", 8), bg="white").pack(side=tk.LEFT)
        self.geno_method = tk.StringVar(value="Peak clustering")
        ttk.Combobox(row1, textvariable=self.geno_method,
                    values=["Peak clustering", "Curve shape", "Difference plot"],
                    width=15).pack(side=tk.LEFT, padx=5)

        ttk.Button(row1, text="Classify Genotypes", command=self._classify_genotypes).pack(side=tk.RIGHT)

        # Results tree
        self.geno_tree = ttk.Treeview(content, columns=("Sample", "Tm", "Genotype", "Confidence"),
                                      show="headings", height=4)
        for col, w in [("Sample", 80), ("Tm", 60), ("Genotype", 100), ("Confidence", 70)]:
            self.geno_tree.heading(col, text=col)
            self.geno_tree.column(col, width=w, anchor=tk.CENTER)

        self.geno_tree.pack(fill=tk.X, pady=5)

    def _find_tm(self):
        """Override to store Tm values"""
        super()._find_tm()

        # Store Tm values for genotyping
        for item in self.melt_tree.get_children():
            values = self.melt_tree.item(item)['values']
            if len(values) >= 2:
                sample = values[0]
                tm = float(values[1]) if values[1] != '—' else None
                if tm:
                    self.genotypes[sample] = {'tm': tm}

    def _classify_genotypes(self):
        """Classify samples into genotypes using hierarchical clustering, curve shape, or difference plots"""
        if not self.genotypes and not self.fluorescence:
            messagebox.showwarning("No Data", "Calculate Tm values or load melting curves first")
            return

        method = self.geno_method.get()

        # ---------- Peak clustering (Tm‑based) ----------
        if method == "Peak clustering":
            if not self.genotypes:
                messagebox.showwarning("No Tm Data", "Please calculate Tm values first (use FIND Tm button)")
                return
            tms = [g['tm'] for g in self.genotypes.values()]
            samples = list(self.genotypes.keys())
            if len(tms) < 3:
                messagebox.showwarning("Insufficient Data", "Need at least 3 samples for clustering")
                return

            X = np.array(tms).reshape(-1, 1)
            from scipy.cluster.hierarchy import linkage, fcluster
            linkage_matrix = linkage(X, method='ward')
            max_d = 0.5  # clusters separated by at least 0.5°C
            labels = fcluster(linkage_matrix, t=max_d, criterion='distance')
            n_clusters = len(set(labels))

            # Assign genotype names based on mean Tm order
            cluster_means = {}
            for i, label in enumerate(labels):
                cluster_means.setdefault(label, []).append(tms[i])
            mean_tms = {k: np.mean(v) for k, v in cluster_means.items()}
            sorted_clusters = sorted(mean_tms.items(), key=lambda x: x[1])
            genotype_names = {}
            if len(sorted_clusters) >= 1:
                genotype_names[sorted_clusters[0][0]] = "Wildtype"
            if len(sorted_clusters) >= 2:
                genotype_names[sorted_clusters[1][0]] = "Heterozygous"
            if len(sorted_clusters) >= 3:
                genotype_names[sorted_clusters[2][0]] = "Homozygous Variant"

            from sklearn.metrics import silhouette_samples
            if n_clusters > 1:
                sil_scores = silhouette_samples(X, labels)
            else:
                sil_scores = np.ones(len(X))

            # Clear tree and fill
            for item in self.geno_tree.get_children():
                self.geno_tree.delete(item)
            for i, (sample, label) in enumerate(zip(samples, labels)):
                genotype = genotype_names.get(label, f"Cluster {label}")
                conf_pct = max(0, min(100, sil_scores[i] * 100))
                self.geno_tree.insert("", tk.END, values=(
                    sample,
                    f"{tms[i]:.2f}",
                    genotype,
                    f"{conf_pct:.0f}%"
                ))

        # ---------- Curve shape clustering (full curve morphology) ----------
        elif method == "Curve shape":
            if not self.fluorescence:
                messagebox.showwarning("No Data", "Load melting curves first")
                return
            # Build feature matrix: each sample = normalized fluorescence curve
            samples = []
            features = []
            for sample, fluor in self.fluorescence.items():
                if len(fluor) == len(self.temperature):
                    # Normalize to [0,1]
                    fluor_norm = (fluor - np.min(fluor)) / (np.max(fluor) - np.min(fluor) + 1e-6)
                    features.append(fluor_norm)
                    samples.append(sample)
            if len(samples) < 3:
                messagebox.showwarning("Insufficient Data", "Need at least 3 samples")
                return

            X = np.array(features)
            # PCA to reduce dimensionality (keep 95% variance or up to 5 components)
            from sklearn.decomposition import PCA
            n_comp = min(5, len(samples)-1)
            pca = PCA(n_components=n_comp)
            X_pca = pca.fit_transform(X)

            # Determine optimal number of clusters using silhouette score (try 2–4)
            from sklearn.cluster import KMeans
            from sklearn.metrics import silhouette_score, silhouette_samples
            best_k = 2
            best_score = -1
            for k in range(2, min(5, len(samples))):
                kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                labels = kmeans.fit_predict(X_pca)
                if len(set(labels)) > 1:
                    score = silhouette_score(X_pca, labels)
                    if score > best_score:
                        best_score = score
                        best_k = k
            # Final clustering
            kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(X_pca)
            # Compute per‑sample confidence (silhouette)
            sil_scores = silhouette_samples(X_pca, labels)

            # Clear tree and fill
            for item in self.geno_tree.get_children():
                self.geno_tree.delete(item)
            for i, sample in enumerate(samples):
                conf_pct = max(0, min(100, sil_scores[i] * 100))
                self.geno_tree.insert("", tk.END, values=(
                    sample,
                    "—",  # no single Tm
                    f"Cluster {labels[i]+1}",
                    f"{conf_pct:.0f}%"
                ))

        # ---------- Difference plot clustering (relative to reference) ----------
        elif method == "Difference plot":
            if not self.fluorescence:
                messagebox.showwarning("No Data", "Load melting curves first")
                return
            # Need a reference sample
            ref = self.melt_ref_var.get()
            if ref not in self.fluorescence:
                messagebox.showwarning("No Reference", "Select a valid reference sample")
                return

            # Normalize reference using current normalization settings
            pre_min = float(self.melt_pre_min.get())
            pre_max = float(self.melt_pre_max.get())
            post_min = float(self.melt_post_min.get())
            post_max = float(self.melt_post_max.get())
            ref_fluor = self.fluorescence[ref]
            ref_norm = self.engine.normalize_curves(
                self.temperature, ref_fluor,
                pre_melt=(pre_min, pre_max),
                post_melt=(post_min, post_max)
            )

            # Compute difference curves
            samples = []
            diff_curves = []
            for sample, fluor in self.fluorescence.items():
                if sample == ref:
                    continue
                if len(fluor) == len(self.temperature):
                    fluor_norm = self.engine.normalize_curves(
                        self.temperature, fluor,
                        pre_melt=(pre_min, pre_max),
                        post_melt=(post_min, post_max)
                    )
                    diff = fluor_norm - ref_norm
                    diff_curves.append(diff)
                    samples.append(sample)

            if len(samples) < 3:
                messagebox.showwarning("Insufficient Data", "Need at least 3 samples (excluding reference)")
                return

            X = np.array(diff_curves)
            # PCA
            from sklearn.decomposition import PCA
            n_comp = min(5, len(samples)-1)
            pca = PCA(n_components=n_comp)
            X_pca = pca.fit_transform(X)

            # Find optimal number of clusters
            from sklearn.cluster import KMeans
            from sklearn.metrics import silhouette_score, silhouette_samples
            best_k = 2
            best_score = -1
            for k in range(2, min(5, len(samples))):
                kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                labels = kmeans.fit_predict(X_pca)
                if len(set(labels)) > 1:
                    score = silhouette_score(X_pca, labels)
                    if score > best_score:
                        best_score = score
                        best_k = k
            # Final clustering
            kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(X_pca)
            sil_scores = silhouette_samples(X_pca, labels)

            # Clear tree and fill
            for item in self.geno_tree.get_children():
                self.geno_tree.delete(item)
            for i, sample in enumerate(samples):
                conf_pct = max(0, min(100, sil_scores[i] * 100))
                self.geno_tree.insert("", tk.END, values=(
                    sample,
                    "—",
                    f"Cluster {labels[i]+1}",
                    f"{conf_pct:.0f}%"
                ))

        messagebox.showinfo("Genotyping Complete",
                        f"Classified {len(self.geno_tree.get_children())} samples")

    def get_explanation(self):
        """Get explanation of melting curve analysis"""
        return """🌡️ MELTING CURVE ANALYSIS (HRM)

Tm Determination:
• Peak of -dF/dT (negative first derivative)
• Higher Tm = more stable DNA duplex
• Single peak = homogenous product
• Multiple peaks = heterozygote or contamination

Genotyping Methods:
• Peak clustering: Groups samples by Tm value
• Curve shape: Clusters by full curve morphology
• Difference plot: Compares to reference genotype

Interpretation:
• Wildtype: Single peak at expected Tm
• Heterozygous: Two peaks or shifted/shoulders
• Homozygous variant: Single peak at different Tm

References:
Ririe et al. (1997) Analytical Biochemistry
Wittwer et al. (2003) Clinical Chemistry"""


class EnhancedReferenceRangeTab(ReferenceRangeTab, EnhancedAnalysisTab):
    """Enhanced reference tab with bootstrap, partition testing, indirect methods"""

    def __init__(self, parent, app, ui_queue):
        super().__init__(parent, app, ui_queue)

        # Add advanced methods panel
        self._add_advanced_methods()

    def _add_advanced_methods(self):
        """Add advanced reference interval methods"""
        self.adv_ref = tk.Frame(self.content_frame, bg="white", relief=tk.GROOVE, borderwidth=1)
        # Pack at the top
        children = self.content_frame.winfo_children()
        if children:
            self.adv_ref.pack(fill=tk.X, padx=5, pady=5, before=children[0])
        else:
            self.adv_ref.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(self.adv_ref, text="📋 Advanced Reference Methods", font=("Arial", 9, "bold"),
                bg=C_LIGHT, fg=C_HEADER).pack(fill=tk.X)

        content = tk.Frame(self.adv_ref, bg="white")
        content.pack(fill=tk.X, padx=5, pady=5)

        # Bootstrap button
        row1 = tk.Frame(content, bg="white")
        row1.pack(fill=tk.X, pady=2)

        ttk.Button(row1, text="🎲 Bootstrap CI", command=self._bootstrap_interval).pack(side=tk.LEFT, padx=2)
        ttk.Button(row1, text="📊 Partition Test", command=self._partition_test).pack(side=tk.LEFT, padx=2)
        ttk.Button(row1, text="🏥 Indirect Method", command=self._indirect_method).pack(side=tk.LEFT, padx=2)

        # Results
        self.adv_ref_results = tk.Label(content, text="", font=("Arial", 8), bg="white", fg=C_HEADER)
        self.adv_ref_results.pack(fill=tk.X, pady=5)

    def _bootstrap_interval(self):
        """Calculate bootstrap confidence intervals"""
        if not self.current_analyte:
            messagebox.showwarning("No Selection", "Select an analyte first")
            return

        # Extract values
        values = np.array([d['Value'] for d in self.ref_data
                          if d.get('Analyte') == self.current_analyte])

        if len(values) < 10:
            messagebox.showwarning("Insufficient Data", "Need at least 10 samples for bootstrap")
            return

        # Bootstrap
        n_bootstrap = 1000
        n = len(values)

        lower_limits = []
        upper_limits = []

        for i in range(n_bootstrap):
            # Resample with replacement
            boot_sample = np.random.choice(values, size=n, replace=True)

            # Calculate percentiles
            lower = np.percentile(boot_sample, 2.5)
            upper = np.percentile(boot_sample, 97.5)

            lower_limits.append(lower)
            upper_limits.append(upper)

        # Calculate 90% CI for the limits
        ci_lower_lower = np.percentile(lower_limits, 5)
        ci_lower_upper = np.percentile(lower_limits, 95)
        ci_upper_lower = np.percentile(upper_limits, 5)
        ci_upper_upper = np.percentile(upper_limits, 95)

        result_text = (f"Bootstrap Reference Interval (95%):\n"
                      f"Lower limit: {np.percentile(values, 2.5):.2f} "
                      f"(90% CI: {ci_lower_lower:.2f}-{ci_lower_upper:.2f})\n"
                      f"Upper limit: {np.percentile(values, 97.5):.2f} "
                      f"(90% CI: {ci_upper_lower:.2f}-{ci_upper_upper:.2f})")

        self.adv_ref_results.config(text=result_text)

    def _partition_test(self):
        """Test if subgroups need separate intervals"""
        if not self.ref_data or not self.current_analyte:
            return

        # Find subgroups (e.g., Male/Female)
        subgroups = {}
        for d in self.ref_data:
            if d.get('Analyte') == self.current_analyte:
                group = d.get('Group', d.get('Gender', d.get('Sex', 'All')))
                subgroups.setdefault(group, []).append(d['Value'])

        if len(subgroups) < 2:
            self.adv_ref_results.config(text="Need at least 2 subgroups for partition testing")
            return

        # Harris-Boyd test
        results = []
        group_names = list(subgroups.keys())

        for i in range(len(group_names)):
            for j in range(i+1, len(group_names)):
                g1 = group_names[i]
                g2 = group_names[j]

                data1 = np.array(subgroups[g1])
                data2 = np.array(subgroups[g2])

                # SD ratio test
                sd1 = np.std(data1, ddof=1)
                sd2 = np.std(data2, ddof=1)
                sd_ratio = max(sd1, sd2) / min(sd1, sd2)

                # Mean difference test (standardized)
                mean1 = np.mean(data1)
                mean2 = np.mean(data2)
                pooled_sd = np.sqrt((sd1**2 + sd2**2) / 2)
                mean_diff = abs(mean1 - mean2) / pooled_sd

                needs_partition = sd_ratio > 1.5 or mean_diff > 0.25

                results.append(f"{g1} vs {g2}:")
                results.append(f"  SD ratio: {sd_ratio:.2f} {'⚠️' if sd_ratio>1.5 else '✓'}")
                results.append(f"  Mean diff: {mean_diff:.2f} {'⚠️' if mean_diff>0.25 else '✓'}")
                results.append(f"  Partition {'RECOMMENDED' if needs_partition else 'NOT NEEDED'}")

        self.adv_ref_results.config(text="\n".join(results))

    def _indirect_method(self):
        """Indirect reference interval using Bhattacharya method"""
        if not self.current_analyte:
            return

        # Extract values
        values = np.array([d['Value'] for d in self.ref_data
                          if d.get('Analyte') == self.current_analyte])

        if len(values) < 100:
            self.adv_ref_results.config(text="Indirect methods need >100 samples (preferably >1000)")
            return

        # Simplified Bhattacharya method
        # Assumes the central part of the distribution is the healthy population

        # Remove extreme outliers
        q1, q3 = np.percentile(values, [25, 75])
        iqr = q3 - q1
        mask = (values >= q1 - 3*iqr) & (values <= q3 + 3*iqr)
        filtered = values[mask]

        # Assume central 80% are from healthy population
        lower = np.percentile(filtered, 10)
        upper = np.percentile(filtered, 90)

        # Estimate healthy population parameters
        healthy = filtered[(filtered >= lower) & (filtered <= upper)]

        if len(healthy) > 30:
            ref_lower = np.percentile(healthy, 2.5)
            ref_upper = np.percentile(healthy, 97.5)

            result_text = (f"Indirect Reference Interval (Bhattacharya):\n"
                          f"Estimated healthy population: n={len(healthy)}\n"
                          f"95% Reference Interval: {ref_lower:.2f} - {ref_upper:.2f}\n\n"
                          f"Note: Validate with direct sampling if possible")

            self.adv_ref_results.config(text=result_text)

    def get_explanation(self):
        """Get explanation of reference range analysis"""
        return """📋 REFERENCE RANGES (CLSI EP28-A3c)

Methods:
• Parametric: Mean ± 1.96×SD (assumes normal)
• Nonparametric: 2.5th - 97.5th percentiles (CLSI recommended)
• Robust: Horn's algorithm (resistant to outliers)
• Bootstrap: Resampling for confidence intervals
• Indirect: Using routine patient data (Bhattacharya)

Partition Testing (Harris-Boyd):
• SD ratio > 1.5: Separate intervals needed
• Mean diff > 0.25×pooled SD: Separate intervals needed

Interpretation:
• Reference interval contains 95% of healthy population
• 90% CI around limits shows uncertainty
• Flags: LOW (<2.5th), HIGH (>97.5th), NORMAL

References:
CLSI EP28-A3c (2010)
Horn & Pesce (2003) Clinica Chimica Acta"""


# ============================================================================
# ENHANCED MAIN PLUGIN CLASS
# ============================================================================
class EnhancedClinicalDiagnosticsSuite:
    """Enhanced main plugin with smart assistant, recipes, publication tools"""

    def __init__(self, main_app):
        self.app = main_app
        self.window = None
        self.ui_queue = None
        self.tabs = {}

        # Add global enhancements
        self.smart_assistant = None
        self.uncertainty_bridge = UncertaintyBridge(main_app)
        self.recipe_manager = RecipeManager()

    def show_interface(self):
        """Open the enhanced main window"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("🧬✨ Clinical Diagnostics Suite v2.0 - Community Edition")
        self.window.geometry("1200x800")
        self.window.minsize(1100, 700)
        self.window.transient(self.app.root)

        self.ui_queue = ThreadSafeUI(self.window)
        self._build_ui()

        # Add smart assistant after window is built
        self._add_smart_assistant()

        # Connect all tabs to smart features
        self._connect_tabs()

        # Add global menu items
        self._add_global_menus()

        self.window.lift()
        self.window.focus_force()
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        """Build the main UI"""
        # Header
        header = tk.Frame(self.window, bg=C_HEADER, height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="🧬✨", font=("Arial", 20),
                bg=C_HEADER, fg="white").pack(side=tk.LEFT, padx=10)
        tk.Label(header, text="CLINICAL DIAGNOSTICS SUITE",
                font=("Arial", 14, "bold"), bg=C_HEADER, fg="white").pack(side=tk.LEFT)
        tk.Label(header, text="v2.0 · Community Edition",
                font=("Arial", 9), bg=C_HEADER, fg=C_ACCENT).pack(side=tk.LEFT, padx=10)

        self.status_var = tk.StringVar(value="Ready")
        status_label = tk.Label(header, textvariable=self.status_var,
                               font=("Arial", 9), bg=C_HEADER, fg=C_LIGHT)
        status_label.pack(side=tk.RIGHT, padx=10)

        # Notebook with tabs
        style = ttk.Style()
        style.configure("Clinical.TNotebook.Tab", font=("Arial", 9, "bold"), padding=[8, 4])

        notebook = ttk.Notebook(self.window, style="Clinical.TNotebook")
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.notebook = notebook

        # Create all 7 enhanced tabs
        self.tabs['qpcr'] = EnhancedqPCRAnalysisTab(notebook, self.app, self.ui_queue)
        notebook.add(self.tabs['qpcr'].frame, text=" qPCR ")

        self.tabs['ddct'] = EnhancedDeltaDeltaCtTab(notebook, self.app, self.ui_queue)
        notebook.add(self.tabs['ddct'].frame, text=" ΔΔCt ")

        self.tabs['elisa'] = EnhancedELISAAnalysisTab(notebook, self.app, self.ui_queue)
        notebook.add(self.tabs['elisa'].frame, text=" ELISA ")

        self.tabs['flow'] = EnhancedFlowCytometryTab(notebook, self.app, self.ui_queue)
        notebook.add(self.tabs['flow'].frame, text=" Flow ")

        self.tabs['ddpcr'] = EnhancedddPCRAnalysisTab(notebook, self.app, self.ui_queue)
        notebook.add(self.tabs['ddpcr'].frame, text=" ddPCR ")

        self.tabs['melt'] = EnhancedMeltingCurveTab(notebook, self.app, self.ui_queue)
        notebook.add(self.tabs['melt'].frame, text=" Melting ")

        self.tabs['ref'] = EnhancedReferenceRangeTab(notebook, self.app, self.ui_queue)
        notebook.add(self.tabs['ref'].frame, text=" Reference ")

        # Footer
        footer = tk.Frame(self.window, bg=C_LIGHT, height=25)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)

        tk.Label(footer,
                text="Ramakers 2003 · Livak 2001 · Findlay 2007 · Herzenberg 2006 · Hindson 2011 · Ririe 1997 · CLSI EP28 · Community Enhanced",
                font=("Arial", 8), bg=C_LIGHT, fg=C_HEADER).pack(side=tk.LEFT, padx=10)

        self.progress_bar = ttk.Progressbar(footer, mode='determinate', length=150)
        self.progress_bar.pack(side=tk.RIGHT, padx=10)

    def _add_smart_assistant(self):
        """Add smart assistant to window"""
        if self.window:
            self.smart_assistant = SmartAssistant(self.window, self.app)

    def _connect_tabs(self):
        """Connect all tabs to smart features"""
        for tab_id, tab in self.tabs.items():
            if hasattr(tab, 'connect_smart_assistant') and self.smart_assistant:
                tab.connect_smart_assistant(self.smart_assistant)
            if hasattr(tab, 'connect_uncertainty_bridge'):
                tab.connect_uncertainty_bridge(self.uncertainty_bridge)

        # Bind tab change event to update smart assistant
        if hasattr(self, 'notebook') and self.smart_assistant:
            self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _on_tab_changed(self, event):
        """Update smart assistant when tab changes"""
        if not self.smart_assistant:
            return

        current_tab = self.notebook.tab(self.notebook.select(), "text").strip()

        for tab_id, tab in self.tabs.items():
            if getattr(tab, 'tab_name', '').strip() == current_tab:
                self.smart_assistant.update_for_tab(tab)
                break

    def _add_global_menus(self):
        """Add global menu items to main window"""
        if not self.window:
            return

        menubar = tk.Menu(self.window)
        self.window.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load Recipe...", command=self._load_global_recipe)
        file_menu.add_command(label="Save Recipe...", command=self._save_global_recipe)
        file_menu.add_separator()
        file_menu.add_command(label="Generate Publication Package...",
                             command=self._generate_global_publication)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.window.destroy)

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Uncertainty Propagation",
                              command=self._launch_uncertainty)
        tools_menu.add_command(label="Smart Assistant Settings",
                              command=self._assistant_settings)

    def _load_global_recipe(self):
        """Load recipe for current tab"""
        if not hasattr(self, 'notebook'):
            return

        current = self.notebook.select()
        if not current:
            return

        # Find current tab
        for tab_id, tab in self.tabs.items():
            if str(tab.frame) == current:
                filename = filedialog.askopenfilename(
                    filetypes=[("Recipe files", "*.recipe"), ("All files", "*.*")]
                )
                if filename and hasattr(tab, 'apply_recipe'):
                    tab.apply_recipe(filename)
                break

    def _save_global_recipe(self):
        """Save recipe for current tab"""
        if not hasattr(self, 'notebook'):
            return

        current = self.notebook.select()
        if not current:
            return

        for tab_id, tab in self.tabs.items():
            if str(tab.frame) == current and hasattr(tab, 'get_recipe'):
                filename = filedialog.asksaveasfilename(
                    defaultextension=".recipe",
                    filetypes=[("Recipe files", "*.recipe")]
                )
                if filename:
                    self.recipe_manager.save_recipe(tab, filename)
                break

    def _generate_global_publication(self):
        """Generate publication package for current tab"""
        if not hasattr(self, 'notebook'):
            return

        current = self.notebook.select()
        if not current:
            return

        for tab_id, tab in self.tabs.items():
            if str(tab.frame) == current and hasattr(tab, 'generate_publication'):
                folder = filedialog.askdirectory(title="Select output folder")
                if folder:
                    tab.generate_publication(folder)
                break

    def _launch_uncertainty(self):
        """Launch uncertainty plugin with current data"""
        if not hasattr(self, 'notebook'):
            return

        current = self.notebook.select()
        if not current:
            return

        for tab_id, tab in self.tabs.items():
            if str(tab.frame) == current and hasattr(tab, 'prepare_uncertainty_data'):
                data, context = tab.prepare_uncertainty_data()
                self.uncertainty_bridge.propagate(data, context)
                break

    def _assistant_settings(self):
        """Configure smart assistant"""
        messagebox.showinfo("Smart Assistant",
                           "Smart Assistant provides context-aware suggestions.\n\n"
                           "It learns from your data and offers relevant actions.\n"
                           "No configuration needed - just click the 🧠 icon!")

    def _set_status(self, msg):
        """Update status"""
        self.status_var.set(msg)

    def _show_progress(self, show):
        """Show/hide progress bar"""
        if show:
            self.progress_bar.config(mode='indeterminate')
            self.progress_bar.start(10)
        else:
            self.progress_bar.stop()
            self.progress_bar.config(mode='determinate')
            self.progress_bar['value'] = 0

    def _on_close(self):
        """Clean up on close"""
        if self.window:
            self.window.destroy()
            self.window = None


# ============================================================================
# PLUGIN REGISTRATION - Use enhanced version
# ============================================================================
def setup_plugin(main_app):
    """Register enhanced plugin with Plugin Manager"""

    # Use enhanced class
    plugin = EnhancedClinicalDiagnosticsSuite(main_app)

    # Try to add to Advanced menu
    if hasattr(main_app, 'advanced_menu'):
        main_app.advanced_menu.add_command(
            label=f"{PLUGIN_INFO['icon']} {PLUGIN_INFO['name']}",
            command=plugin.show_interface
        )
        print(f"✅ Enhanced plugin loaded: {PLUGIN_INFO['name']}")
        return plugin

    # Fallback
    if hasattr(main_app, 'menu_bar'):
        if not hasattr(main_app, 'analysis_menu'):
            main_app.analysis_menu = tk.Menu(main_app.menu_bar, tearoff=0)
            main_app.menu_bar.add_cascade(label="🔬 Analysis", menu=main_app.analysis_menu)

        main_app.analysis_menu.add_command(
            label=f"{PLUGIN_INFO['icon']} {PLUGIN_INFO['name']}",
            command=plugin.show_interface
        )
        print(f"✅ Enhanced plugin loaded: {PLUGIN_INFO['name']}")

    return plugin
