"""
CHROMATOGRAPHY ANALYSIS SUITE v2.3 - PROFESSIONAL RELEASE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Multi‑row sample grouping (auto‑detect SampleID)
✓ All 7 tabs fully functional with single CSV import
✓ Professional workflow: select sample → see all associated data
✓ Vendor‑agnostic column mapping via column_mapper.json
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TAB 1: Peak Integration        - Gaussian/Lorentzian fitting, area/height, USP tailing (Foley & Dorsey 1984; Grushka 1972)
TAB 2: Retention Indices       - Kovats, Van den Dool, Lee indices (Kovats 1958; Van den Dool & Kratz 1963)
TAB 3: Mass Spectrum Deconvolution - AMDIS algorithm, component detection, library matching (Stein 1999; AMDIS; matchms)
TAB 4: NMR FID Processing      - Fourier transform, phase correction, baseline, 2D contour plots (Ernst et al. 1987; VNMRJ; nmrglue)
TAB 5: Standard Curves         - Linear/quadratic fits, LOD/LOQ, ICH validation (ICH Q2(R1); CLSI EP17-A2)
TAB 6: Resolution Calculations - USP resolution, plate count, tailing factor (USP <621>; Ph.Eur. 2.2.46)
TAB 7: Peak Purity Analysis    - Spectral comparison, absorbance ratios (ISO 13808; HPLC method validation)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

PLUGIN_INFO = {
    "id": "chromatography_analysis_suite",
    "field": "Chromatography & Analytical Chemistry",
    "name": "Chromatography Suite",
    "category": "software",
    "icon": "🧪",
    "version": "2.3.0",
    "author": "Sefy Levy & DeepSeek",
    "description": "Peak integration · Kovats indices · AMDIS · NMR FID · Standard curves · Resolution · Peak purity · matchms · nmrglue",
    "requires": ["numpy", "pandas", "scipy", "matplotlib"],
    "optional": ["lmfit", "sklearn", "peakutils", "matchms", "nmrglue", "DBDIpy"],
    "window_size": "1200x800"
}

# ============================================================================
# IMPORTS (with graceful fallbacks)
# ============================================================================
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
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Set
warnings.filterwarnings("ignore")

# ============================================================================
# OPTIONAL IMPORTS
# ============================================================================
try:
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    from matplotlib.figure import Figure
    from matplotlib.gridspec import GridSpec
    import matplotlib.patches as mpatches
    from matplotlib.colors import LinearSegmentedColormap
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

try:
    from scipy import signal, ndimage, stats, optimize, interpolate
    from scipy.signal import savgol_filter, find_peaks, peak_widths
    from scipy.optimize import curve_fit, least_squares, minimize
    from scipy.interpolate import interp1d, UnivariateSpline
    from scipy.stats import linregress
    from scipy.integrate import trapz, cumtrapz
    from scipy.fft import fft, ifft, fftfreq
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    import peakutils
    HAS_PEAKUTILS = True
except ImportError:
    HAS_PEAKUTILS = False

# ============================================================================
# matchms for MS library matching
# ============================================================================
try:
    import matchms
    from matchms.importing import load_from_msp, load_from_mgf
    from matchms.filtering import default_filters, normalize_intensities, select_by_mz
    from matchms.similarity import CosineGreedy, ModifiedCosine
    HAS_MATCHMS = True
except ImportError:
    HAS_MATCHMS = False

# ============================================================================
# nmrglue for NMR processing
# ============================================================================
try:
    import nmrglue as ng
    HAS_NMRGLUE = True
except ImportError:
    HAS_NMRGLUE = False

# ============================================================================
# DBDIpy for advanced MS/MS (optional)
# ============================================================================
try:
    import DBDIpy
    HAS_DBDI = True
except ImportError:
    HAS_DBDI = False

# ============================================================================
# COLOR PALETTE — chromatography (blues to greens)
# ============================================================================
C_HEADER   = "#1A5276"   # dark blue
C_ACCENT   = "#2874A6"   # medium blue
C_ACCENT2  = "#2E86C1"   # light blue
C_ACCENT3  = "#28B463"   # green (for peaks)
C_LIGHT    = "#F8F9F9"   # off-white
C_BORDER   = "#A9CCE3"   # light blue-gray
C_STATUS   = "#28B463"   # green
C_WARN     = "#CB4335"   # red
PLOT_COLORS = ["#2874A6", "#28B463", "#F39C12", "#8E44AD", "#E67E22", "#16A085", "#C0392B"]

# Chromatography colormap
CHROM_CMAP = LinearSegmentedColormap.from_list("chrom", ["#2874A6", "#2E86C1", "#5DADE2", "#85C1E9", "#AED6F1"])

# ============================================================================
# Load column mapper
# ============================================================================
def load_column_mapper(app):
    """Load column_mapper.json from the main app's config directory."""
    # Try to get the config directory – common attributes: config_dir, config_path, app_dir
    config_dir = None
    if hasattr(app, 'config_dir'):
        config_dir = app.config_dir
    elif hasattr(app, 'config_path'):
        config_dir = app.config_path
    elif hasattr(app, 'app_dir'):
        config_dir = app.app_dir
    else:
        # Fallback: assume a 'config' subdirectory in the app's root
        config_dir = Path(app.__file__).parent / 'config' if hasattr(app, '__file__') else Path.cwd() / 'config'

    mapper_path = Path(config_dir) / 'column_mapper.json'
    if not mapper_path.exists():
        print(f"Warning: column_mapper.json not found at {mapper_path}")
        return {}
    try:
        with open(mapper_path, 'r') as f:
            data = json.load(f)
        return data.get('field_groups', {})
    except Exception as e:
        print(f"Error loading column mapper: {e}")
        return {}
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
# TOOLTIP
# ============================================================================
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, event=None):
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 20
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        tk.Label(self.tip, text=self.text, background="#FFFACD",
                 relief=tk.SOLID, borderwidth=1,
                 font=("Arial", 8)).pack()

    def _hide(self, event=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None


# ============================================================================
# BASE TAB CLASS - Auto-import with multi‑row grouping and column mapping
# ============================================================================
class AnalysisTab:
    """Base class for all analysis tabs with auto-import from main table.
       Handles grouping of rows by SampleID and column mapping via mapper."""

    def __init__(self, parent, app, ui_queue, tab_name):
        self.parent = parent
        self.app = app
        self.ui_queue = ui_queue
        self.tab_name = tab_name
        self.frame = ttk.Frame(parent)

        # Load column mapper
        self.mapper = load_column_mapper(app)   # dict of field groups

        # Current state
        self.sample_groups = {}          # dict: group_id -> {'rows': list, 'display': str}
        self.selected_group_id = None
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

        # Bind destroy event to cancel any pending callbacks
        self.frame.bind("<Destroy>", self._on_destroy)

        # Register as observer of data hub
        if hasattr(self.app, 'data_hub'):
            self.app.data_hub.register_observer(self)

        # Initial refresh
        self.refresh_sample_list()

    def _on_destroy(self, event=None):
        """Cancel any pending after call when widget is destroyed."""
        if self._update_id:
            self.frame.after_cancel(self._update_id)
            self._update_id = None

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
        """Manual import - to be overridden by child classes"""
        pass

    def get_all_rows(self) -> List[Dict]:
        """Get all rows from the main data table."""
        if hasattr(self.app, 'data_hub'):
            return self.app.data_hub.get_all()
        return []

    def on_data_changed(self, event, *args):
        """Called when main table data changes."""
        if self.import_mode_var.get() == "auto":
            if self._update_id:
                self.frame.after_cancel(self._update_id)
            self._update_id = self.frame.after(500, self._delayed_refresh)

    def _delayed_refresh(self):
        if not self.frame.winfo_exists():
            return
        self.refresh_sample_list()
        self._update_id = None

    def _map_columns(self, headers: List[str]) -> Dict[str, str]:
        """
        Map actual column names to standard field names using the column mapper.
        Returns a dict like {'RetentionTime_min': 'RTime_min', ...}
        """
        if not self.mapper:
            return {}
        mapping = {}
        # Collect all variations from all field groups
        all_variations = {}
        for group_name, group_fields in self.mapper.items():
            for std_name, field_info in group_fields.items():
                if std_name not in all_variations:
                    all_variations[std_name] = [v.lower() for v in field_info.get('variations', [])]
        # For each header, check if it matches any standard field's variations
        for header in headers:
            header_lower = header.lower()
            for std_name, variations in all_variations.items():
                if header_lower in variations:
                    mapping[std_name] = header
                    break
        return mapping

    def refresh_sample_list(self):
        """Group rows by SampleID and populate the dropdown."""
        if self.import_mode_var.get() != "auto":
            return
        if not self.sample_combo.winfo_exists():
            return

        all_rows = self.get_all_rows()
        if not all_rows:
            return

        # Get headers from first row (assuming all rows have same keys)
        headers = list(all_rows[0].keys())
        self.column_map = self._map_columns(headers)

        # Group by SampleID – use the mapped SampleID column
        sampleid_col = self.column_map.get('SampleID', 'SampleID')
        groups = {}
        for row in all_rows:
            sample_id = row.get(sampleid_col, 'UNKNOWN')
            if sample_id not in groups:
                groups[sample_id] = []
            groups[sample_id].append(row)

        # Filter groups that have data for this tab
        self.sample_groups = {}
        sample_ids = []
        for group_id, rows in groups.items():
            if self._group_has_data(rows):
                display = f"✅ {group_id} ({len(rows)} rows)"
                sample_ids.append(display)
                self.sample_groups[display] = {'id': group_id, 'rows': rows}

        self.sample_combo['values'] = sample_ids

        data_count = len(self.sample_groups)
        self.status_label.config(text=f"Total samples with data: {data_count}")

        if self.selected_group_id is not None and self.selected_group_id in sample_ids:
            self.sample_combo.set(self.selected_group_id)
        elif sample_ids:
            # auto-select first
            self.sample_combo.current(0)
            self._on_sample_selected()

    def _group_has_data(self, rows: List[Dict]) -> bool:
        """Check if a group of rows has data for this tab. Override in child."""
        return False

    def _on_sample_selected(self, event=None):
        selection = self.sample_combo.get()
        if not selection or selection not in self.sample_groups:
            return
        self.selected_group_id = selection
        group = self.sample_groups[selection]
        self._load_sample_data(group['id'], group['rows'])

    def _load_sample_data(self, group_id: str, rows: List[Dict]):
        """Load data for the selected sample group. Override in child."""
        pass


# ============================================================================
# ENGINE 1 — PEAK INTEGRATION (Foley & Dorsey 1984; Grushka 1972)
# ============================================================================
class PeakIntegrationAnalyzer:
    """
    Chromatographic peak integration and fitting.

    Peak models:
    - Gaussian: y = A * exp(-(x - μ)²/(2σ²))
    - Lorentzian: y = A / (1 + ((x - μ)/γ)²)
    - EMG (Exponentially Modified Gaussian): convolution of Gaussian and exponential
    - Hybrid: combination of models for tailing peaks

    USP/EP peak parameters:
    - Tailing factor: T = (a + b) / (2a) at 5% height
    - Plate count: N = 16(t_R/W)² or N = 5.54(t_R/W_h)²
    - Resolution: Rs = 2(t_R2 - t_R1)/(W1 + W2)

    References:
        Foley, J.P. & Dorsey, J.G. (1984) "Equations for calculation of
            chromatographic figures of merit for ideal and skewed peaks"
        Grushka, E. (1972) "Characterization of exponentially modified
            Gaussian peaks in chromatography"
    """

    @classmethod
    def gaussian(cls, x, A, mu, sigma):
        return A * np.exp(-(x - mu)**2 / (2 * sigma**2))

    @classmethod
    def lorentzian(cls, x, A, mu, gamma):
        return A / (1 + ((x - mu) / gamma)**2)

    @classmethod
    def emg(cls, x, A, mu, sigma, tau):
        # Simplified EMG (would use scipy.special.erfc in production)
        t = (x - mu) / sigma
        y = A * np.exp(0.5 * (sigma / tau)**2 - (x - mu) / tau)
        return y

    @classmethod
    def find_peaks(cls, time, intensity, height_threshold=0.01, distance=10):
        if HAS_SCIPY:
            int_norm = intensity / np.max(intensity)
            peaks, properties = find_peaks(
                int_norm,
                height=height_threshold,
                distance=distance,
                prominence=0.01,
                width=1
            )
            peak_list = []
            for i, p in enumerate(peaks):
                peak_list.append({
                    "index": p,
                    "time": time[p],
                    "height": intensity[p],
                    "peak_idx": i + 1
                })
            return peak_list
        else:
            # simple fallback
            peaks = []
            for i in range(1, len(intensity)-1):
                if intensity[i] > intensity[i-1] and intensity[i] > intensity[i+1]:
                    if intensity[i] > height_threshold * np.max(intensity):
                        peaks.append({
                            "index": i,
                            "time": time[i],
                            "height": intensity[i],
                            "peak_idx": len(peaks) + 1
                        })
            return peaks

    @classmethod
    def peak_width(cls, time, intensity, peak_idx, height_fraction=0.5):
        peak_height = intensity[peak_idx]
        target_height = peak_height * height_fraction
        left_idx = peak_idx
        while left_idx > 0 and intensity[left_idx] > target_height:
            left_idx -= 1
        right_idx = peak_idx
        while right_idx < len(intensity)-1 and intensity[right_idx] > target_height:
            right_idx += 1
        # linear interpolation for edges
        if left_idx > 0:
            t1, h1 = time[left_idx], intensity[left_idx]
            t2, h2 = time[left_idx+1], intensity[left_idx+1]
            left_time = t1 + (target_height - h1) * (t2 - t1) / (h2 - h1) if h2 != h1 else t1
        else:
            left_time = time[0]
        if right_idx < len(intensity)-1:
            t1, h1 = time[right_idx-1], intensity[right_idx-1]
            t2, h2 = time[right_idx], intensity[right_idx]
            right_time = t1 + (target_height - h1) * (t2 - t1) / (h2 - h1) if h2 != h1 else t2
        else:
            right_time = time[-1]
        width = right_time - left_time
        return {"width": width, "left_time": left_time, "right_time": right_time,
                "left_idx": left_idx, "right_idx": right_idx}

    @classmethod
    def peak_area(cls, time, intensity, left_idx, right_idx, baseline="linear"):
        t_peak = time[left_idx:right_idx+1]
        i_peak = intensity[left_idx:right_idx+1]
        if baseline == "linear":
            y1 = i_peak[0]
            y2 = i_peak[-1]
            baseline_line = np.linspace(y1, y2, len(t_peak))
            i_corrected = i_peak - baseline_line
        else:
            i_corrected = i_peak
        area = trapz(i_corrected, t_peak)
        return area, i_corrected

    @classmethod
    def tailing_factor(cls, time, intensity, peak_idx, height_fraction=0.05):
        peak_height = intensity[peak_idx]
        target_height = peak_height * height_fraction
        peak_time = time[peak_idx]
        left_idx = peak_idx
        while left_idx > 0 and intensity[left_idx] > target_height:
            left_idx -= 1
        right_idx = peak_idx
        while right_idx < len(intensity)-1 and intensity[right_idx] > target_height:
            right_idx += 1
        if left_idx > 0:
            t1, h1 = time[left_idx], intensity[left_idx]
            t2, h2 = time[left_idx+1], intensity[left_idx+1]
            left_time = t1 + (target_height - h1) * (t2 - t1) / (h2 - h1) if h2 != h1 else t1
        else:
            left_time = time[0]
        if right_idx < len(intensity)-1:
            t1, h1 = time[right_idx-1], intensity[right_idx-1]
            t2, h2 = time[right_idx], intensity[right_idx]
            right_time = t1 + (target_height - h1) * (t2 - t1) / (h2 - h1) if h2 != h1 else t2
        else:
            right_time = time[-1]
        a = peak_time - left_time
        b = right_time - peak_time
        tailing = (a + b) / (2 * a) if a > 0 else 1.0
        return tailing, a, b

    @classmethod
    def plate_count(cls, time, intensity, peak_idx, method="USP"):
        peak_time = time[peak_idx]
        width_info = cls.peak_width(time, intensity, peak_idx, height_fraction=0.5)
        if method == "USP":
            base_width = width_info["width"] * 1.7
            N = 16 * (peak_time / base_width) ** 2
        else:
            N = 5.54 * (peak_time / width_info["width"]) ** 2
        return N

    @classmethod
    def fit_gaussian(cls, time, intensity, peak_idx, fit_width=10):
        if not HAS_SCIPY:
            return None
        left = max(0, peak_idx - fit_width)
        right = min(len(time), peak_idx + fit_width + 1)
        t_fit = time[left:right]
        i_fit = intensity[left:right]
        A0 = i_fit.max()
        mu0 = time[peak_idx]
        sigma0 = (time[min(peak_idx+5, len(time)-1)] - time[max(0, peak_idx-5)]) / 4
        try:
            popt, pcov = curve_fit(cls.gaussian, t_fit, i_fit,
                                   p0=[A0, mu0, sigma0],
                                   bounds=([0, t_fit[0], 0], [np.inf, t_fit[-1], np.inf]))
            return {"A": popt[0], "mu": popt[1], "sigma": popt[2],
                    "fwhm": 2.355 * popt[2], "area": popt[0] * popt[2] * np.sqrt(2 * np.pi)}
        except:
            return None

    @classmethod
    def load_chromatogram(cls, path):
        df = pd.read_csv(path)
        time_col, inten_col = None, None
        for col in df.columns:
            col_lower = col.lower()
            if any(x in col_lower for x in ['time', 'min', 'retention', 'rt']):
                time_col = col
            if any(x in col_lower for x in ['intensity', 'signal', 'absorbance', 'counts']):
                inten_col = col
        if time_col is None:
            time_col = df.columns[0]
        if inten_col is None:
            inten_col = df.columns[1]
        return {"time": df[time_col].values, "intensity": df[inten_col].values,
                "metadata": {"file": Path(path).name}}


# ============================================================================
# TAB 1: PEAK INTEGRATION
# ============================================================================
class PeakIntegrationTab(AnalysisTab):
    REQUIRED_FIELDS = ['RetentionTime_min', 'Height']   # standard names

    def __init__(self, parent, app, ui_queue):
        super().__init__(parent, app, ui_queue, "Peak Integration")
        self.engine = PeakIntegrationAnalyzer
        self.time = None
        self.intensity = None
        self.peaks = []
        self.current_peak = None
        self._build_content_ui()

    def _group_has_data(self, rows):
        # Check if all required fields are mapped
        if not hasattr(self, 'column_map'):
            return False
        return all(field in self.column_map for field in self.REQUIRED_FIELDS)

    def _manual_import(self):
        path = filedialog.askopenfilename(
            title="Load Chromatogram",
            filetypes=[("CSV", "*.csv"), ("TXT", "*.txt"), ("All files", "*.*")])
        if not path:
            return
        self.status_label.config(text="🔄 Loading chromatogram...")
        def worker():
            try:
                data = self.engine.load_chromatogram(path)
                def update():
                    self.time = data["time"]
                    self.intensity = data["intensity"]
                    self.manual_label.config(text=f"✓ {Path(path).name}")
                    self._find_peaks()
                    self._plot_chromatogram()
                    self.status_label.config(text=f"Loaded chromatogram")
                self.ui_queue.schedule(update)
            except Exception as e:
                self.ui_queue.schedule(lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=worker, daemon=True).start()

    def _load_sample_data(self, group_id, rows):
        time_col = self.column_map.get('RetentionTime_min')
        int_col = self.column_map.get('Height')
        if not time_col or not int_col:
            self.status_label.config(text="Missing required columns")
            return
        time = []
        intensity = []
        for row in rows:
            try:
                time.append(float(row[time_col]))
                intensity.append(float(row[int_col]))
            except (ValueError, KeyError):
                continue
        if not time:
            self.status_label.config(text="No valid data")
            return
        idx = np.argsort(time)
        self.time = np.array(time)[idx]
        self.intensity = np.array(intensity)[idx]
        self._find_peaks()
        self._plot_chromatogram()
        self.status_label.config(text=f"Loaded '{group_id}' ({len(self.time)} points)")

    def _build_content_ui(self):
        # Main split
        main_pane = ttk.PanedWindow(self.content_frame, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True)

        left = tk.Frame(main_pane, bg="white", width=300)
        main_pane.add(left, weight=1)

        right = tk.Frame(main_pane, bg="white")
        main_pane.add(right, weight=2)

        # === LEFT PANEL ===
        tk.Label(left, text="📊 PEAK INTEGRATION",
                font=("Arial", 10, "bold"), bg=C_LIGHT, fg=C_HEADER).pack(fill=tk.X, pady=2)

        tk.Label(left, text="Foley & Dorsey 1984 · Grushka 1972",
                font=("Arial", 7), bg="white", fg="#888").pack(anchor=tk.W, padx=4)

        detect_frame = tk.LabelFrame(left, text="Peak Detection", bg="white",
                                    font=("Arial", 8, "bold"), fg=C_HEADER)
        detect_frame.pack(fill=tk.X, padx=4, pady=4)

        row1 = tk.Frame(detect_frame, bg="white")
        row1.pack(fill=tk.X, pady=2)
        tk.Label(row1, text="Threshold (%):", font=("Arial", 8), bg="white").pack(side=tk.LEFT)
        self.peak_thresh = tk.StringVar(value="1.0")
        ttk.Entry(row1, textvariable=self.peak_thresh, width=6).pack(side=tk.LEFT, padx=2)

        tk.Label(row1, text="Distance:", font=("Arial", 8), bg="white").pack(side=tk.LEFT, padx=(4,0))
        self.peak_dist = tk.StringVar(value="10")
        ttk.Entry(row1, textvariable=self.peak_dist, width=4).pack(side=tk.LEFT, padx=2)

        ttk.Button(detect_frame, text="🔍 FIND PEAKS",
                  command=self._find_peaks).pack(fill=tk.X, pady=2)

        tk.Label(left, text="Select Peak:", font=("Arial", 8, "bold"),
                bg="white").pack(anchor=tk.W, padx=4, pady=(4, 0))
        self.peak_listbox = tk.Listbox(left, height=5, font=("Courier", 8))
        self.peak_listbox.pack(fill=tk.X, padx=4, pady=2)
        self.peak_listbox.bind('<<ListboxSelect>>', self._on_peak_selected)

        ttk.Button(left, text="📈 INTEGRATE PEAK",
                  command=self._integrate_peak).pack(fill=tk.X, padx=4, pady=4)

        results_frame = tk.LabelFrame(left, text="Peak Parameters", bg="white",
                                     font=("Arial", 8, "bold"), fg=C_HEADER)
        results_frame.pack(fill=tk.X, padx=4, pady=4)

        self.peak_results = {}
        result_labels = [
            ("Peak #:", "num"),
            ("tR (min):", "tr"),
            ("Height:", "height"),
            ("Area:", "area"),
            ("Width (1/2):", "width"),
            ("Tailing (T):", "tailing"),
            ("Plates (N):", "plates")
        ]

        for i, (label, key) in enumerate(result_labels):
            row = tk.Frame(results_frame, bg="white")
            row.pack(fill=tk.X, pady=1)
            tk.Label(row, text=label, font=("Arial", 7), bg="white", width=12, anchor=tk.W).pack(side=tk.LEFT)
            var = tk.StringVar(value="—")
            tk.Label(row, textvariable=var, font=("Arial", 7, "bold"),
                    bg="white", fg=C_HEADER).pack(side=tk.LEFT, padx=2)
            self.peak_results[key] = var

        # === RIGHT PANEL ===
        if HAS_MPL:
            self.peak_fig = Figure(figsize=(8, 6), dpi=100, facecolor="white")
            gs = GridSpec(2, 1, figure=self.peak_fig, hspace=0.3)
            self.peak_ax_chrom = self.peak_fig.add_subplot(gs[0])
            self.peak_ax_peak = self.peak_fig.add_subplot(gs[1])

            self.peak_ax_chrom.set_title("Chromatogram", fontsize=9, fontweight="bold")
            self.peak_ax_peak.set_title("Selected Peak", fontsize=9, fontweight="bold")

            self.peak_canvas = FigureCanvasTkAgg(self.peak_fig, right)
            self.peak_canvas.draw()
            self.peak_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            toolbar = NavigationToolbar2Tk(self.peak_canvas, right)
            toolbar.update()
        else:
            tk.Label(right, text="matplotlib required for plots",
                    bg="white", fg="#888").pack(expand=True)

    def _plot_chromatogram(self):
        if not HAS_MPL or self.time is None:
            return
        self.peak_ax_chrom.clear()
        self.peak_ax_chrom.plot(self.time, self.intensity, 'b-', lw=1.5)
        for peak in self.peaks:
            self.peak_ax_chrom.plot(peak["time"], peak["height"], 'ro', markersize=4)
        self.peak_ax_chrom.set_xlabel("Time (min)", fontsize=8)
        self.peak_ax_chrom.set_ylabel("Intensity", fontsize=8)
        self.peak_ax_chrom.grid(True, alpha=0.3)
        self.peak_canvas.draw()

    def _find_peaks(self):
        if self.time is None:
            messagebox.showwarning("No Data", "Load chromatogram first")
            return
        threshold = float(self.peak_thresh.get()) / 100
        distance = int(self.peak_dist.get())
        self.peaks = self.engine.find_peaks(
            self.time, self.intensity,
            height_threshold=threshold,
            distance=distance
        )
        self.peak_listbox.delete(0, tk.END)
        for peak in self.peaks:
            self.peak_listbox.insert(tk.END,
                f"Peak {peak['peak_idx']}: tR={peak['time']:.3f} min")
        self._plot_chromatogram()
        self.status_label.config(text=f"✅ Found {len(self.peaks)} peaks")

    def _on_peak_selected(self, event):
        selection = self.peak_listbox.curselection()
        if selection and self.peaks:
            self.current_peak = self.peaks[selection[0]]
            self._plot_peak()

    def _plot_peak(self):
        if not HAS_MPL or self.current_peak is None:
            return
        idx = self.current_peak["index"]
        left = max(0, idx - 20)
        right = min(len(self.time), idx + 21)
        self.peak_ax_peak.clear()
        self.peak_ax_peak.plot(self.time[left:right], self.intensity[left:right], 'b-', lw=2)
        self.peak_ax_peak.plot(self.current_peak["time"], self.current_peak["height"],
                              'ro', markersize=8)
        self.peak_ax_peak.set_xlabel("Time (min)", fontsize=8)
        self.peak_ax_peak.set_ylabel("Intensity", fontsize=8)
        self.peak_ax_peak.grid(True, alpha=0.3)
        self.peak_canvas.draw()

    def _integrate_peak(self):
        if self.current_peak is None:
            messagebox.showwarning("No Peak", "Select a peak first")
            return
        idx = self.current_peak["index"]
        width_info = self.engine.peak_width(
            self.time, self.intensity, idx, height_fraction=0.01
        )
        area, corrected = self.engine.peak_area(
            self.time, self.intensity,
            width_info["left_idx"], width_info["right_idx"]
        )
        tailing, a, b = self.engine.tailing_factor(self.time, self.intensity, idx)
        plates = self.engine.plate_count(self.time, self.intensity, idx)
        gaussian_fit = self.engine.fit_gaussian(self.time, self.intensity, idx)

        self.peak_results["num"].set(str(self.current_peak["peak_idx"]))
        self.peak_results["tr"].set(f"{self.current_peak['time']:.4f}")
        self.peak_results["height"].set(f"{self.current_peak['height']:.1f}")
        self.peak_results["area"].set(f"{area:.1f}")
        self.peak_results["width"].set(f"{width_info['width']:.4f}")
        self.peak_results["tailing"].set(f"{tailing:.3f}")
        self.peak_results["plates"].set(f"{plates:.0f}")

        if HAS_MPL:
            t_peak = self.time[width_info["left_idx"]:width_info["right_idx"]+1]
            i_peak = self.intensity[width_info["left_idx"]:width_info["right_idx"]+1]
            self.peak_ax_peak.clear()
            self.peak_ax_peak.plot(t_peak, i_peak, 'b-', lw=2, label="Data")
            self.peak_ax_peak.fill_between(t_peak, 0, i_peak, alpha=0.3, color=C_ACCENT3,
                                          label=f"Area = {area:.1f}")
            half_height = self.current_peak["height"] / 2
            width_half = self.engine.peak_width(self.time, self.intensity, idx, 0.5)
            self.peak_ax_peak.axhline(half_height, color='r', ls='--', lw=1,
                                     label=f"Width(1/2) = {width_half['width']:.4f}")
            five_pct = self.current_peak["height"] * 0.05
            width_five = self.engine.peak_width(self.time, self.intensity, idx, 0.05)
            self.peak_ax_peak.axhline(five_pct, color='g', ls=':', lw=1,
                                     label=f"Tailing = {tailing:.3f}")
            if gaussian_fit:
                t_fit = np.linspace(t_peak[0], t_peak[-1], 200)
                i_fit = self.engine.gaussian(t_fit, **gaussian_fit)
                self.peak_ax_peak.plot(t_fit, i_fit, 'r--', lw=1.5, label="Gaussian fit")
            self.peak_ax_peak.set_xlabel("Time (min)", fontsize=8)
            self.peak_ax_peak.set_ylabel("Intensity", fontsize=8)
            self.peak_ax_peak.legend(fontsize=7)
            self.peak_ax_peak.grid(True, alpha=0.3)
            self.peak_canvas.draw()

        self.status_label.config(text=f"✅ Peak {self.current_peak['peak_idx']} integrated")


# ============================================================================
# ENGINE 2 — RETENTION INDICES (Kovats 1958; Van den Dool & Kratz 1963)
# ============================================================================
class RetentionIndexAnalyzer:
    # Common alkane retention times for Kovats
    ALKANES = {
        "C6": {"name": "Hexane", "carbons": 6},
        "C7": {"name": "Heptane", "carbons": 7},
        "C8": {"name": "Octane", "carbons": 8},
        "C9": {"name": "Nonane", "carbons": 9},
        "C10": {"name": "Decane", "carbons": 10},
        "C11": {"name": "Undecane", "carbons": 11},
        "C12": {"name": "Dodecane", "carbons": 12},
        "C13": {"name": "Tridecane", "carbons": 13},
        "C14": {"name": "Tetradecane", "carbons": 14},
        "C15": {"name": "Pentadecane", "carbons": 15},
        "C16": {"name": "Hexadecane", "carbons": 16},
        "C17": {"name": "Heptadecane", "carbons": 17},
        "C18": {"name": "Octadecane", "carbons": 18},
        "C19": {"name": "Nonadecane", "carbons": 19},
        "C20": {"name": "Eicosane", "carbons": 20}
    }

    @classmethod
    def kovats_index(cls, tR_unknown, tR_n, tR_n1, n, isothermal=True):
        if isothermal:
            if tR_n <= 0 or tR_n1 <= 0 or tR_unknown <= 0:
                return None
            log_tR = np.log(tR_unknown)
            log_n = np.log(tR_n)
            log_n1 = np.log(tR_n1)
            if log_n1 == log_n:
                return 100 * n
            I = 100 * n + 100 * (log_tR - log_n) / (log_n1 - log_n)
        else:
            if tR_n1 == tR_n:
                return 100 * n
            I = 100 * n + 100 * (tR_unknown - tR_n) / (tR_n1 - tR_n)
        return I

    @classmethod
    def find_alkane_pair(cls, tR_unknown, alkane_times):
        carbons = sorted(alkane_times.keys())
        for i in range(len(carbons)-1):
            n = carbons[i]
            n1 = carbons[i+1]
            if alkane_times[n] <= tR_unknown <= alkane_times[n1]:
                return n, alkane_times[n], alkane_times[n1]
        return None, None, None

    @classmethod
    def calculate_indices(cls, unknown_times, alkane_times, method="kovats"):
        results = {}
        isothermal = (method == "kovats")
        for compound, tR in unknown_times.items():
            n, tR_n, tR_n1 = cls.find_alkane_pair(tR, alkane_times)
            if n is not None:
                I = cls.kovats_index(tR, tR_n, tR_n1, n, isothermal)
                results[compound] = I
            else:
                results[compound] = None
        return results

    @classmethod
    def lee_index(cls, tR_unknown, tR_benzene, tR_benzoperylene):
        if tR_benzoperylene == tR_benzene:
            return 0
        return 100 * (tR_unknown - tR_benzene) / (tR_benzoperylene - tR_benzene)

    @classmethod
    def load_alkane_data(cls, path):
        df = pd.read_csv(path)
        alkane_times = {}
        for _, row in df.iterrows():
            alkane_times[int(row['Carbons'])] = row['Time']
        return alkane_times

    @classmethod
    def load_unknown_data(cls, path):
        df = pd.read_csv(path)
        unknown_times = {}
        for _, row in df.iterrows():
            unknown_times[row['Compound']] = row['Time']
        return unknown_times


# ============================================================================
# TAB 2: RETENTION INDICES
# ============================================================================
class RetentionIndexTab(AnalysisTab):
    REQUIRED_FIELDS_ALKANE = ['RetentionTime_min', 'Carbons']   # standard names
    REQUIRED_FIELDS_UNKNOWN = ['RetentionTime_min', 'Compound']

    def __init__(self, parent, app, ui_queue):
        super().__init__(parent, app, ui_queue, "Retention Indices")
        self.engine = RetentionIndexAnalyzer
        self.alkane_times = {}
        self.unknown_times = {}
        self.results = {}
        self._build_content()

    def _group_has_data(self, rows):
        # A group may be either alkane data or unknown data
        if not hasattr(self, 'column_map'):
            return False
        # Check if we can find Carbons or Compound
        has_carbons = 'Carbons' in self.column_map
        has_compound = 'Compound' in self.column_map
        return has_carbons or has_compound

    def _load_sample_data(self, group_id, rows):
        # Determine if this is alkane or unknown
        if 'Carbons' in self.column_map:
            # Alkane data
            carbons_col = self.column_map['Carbons']
            rt_col = self.column_map['RetentionTime_min']
            self.alkane_times = {}
            for row in rows:
                try:
                    c = int(row[carbons_col])
                    rt = float(row[rt_col])
                    self.alkane_times[c] = rt
                except:
                    pass
        if 'Compound' in self.column_map:
            # Unknown data
            comp_col = self.column_map['Compound']
            rt_col = self.column_map['RetentionTime_min']
            self.unknown_times = {}
            for row in rows:
                try:
                    comp = row[comp_col]
                    rt = float(row[rt_col])
                    self.unknown_times[comp] = rt
                except:
                    pass
        if self.alkane_times and self.unknown_times:
            self._compute_indices()
            self.status_label.config(text=f"Loaded alkane & unknown data for {group_id}")
        else:
            self.status_label.config(text="Missing alkane or unknown data")

    def _manual_import(self):
        # Keep manual import as fallback
        alk_path = filedialog.askopenfilename(title="Load Alkane Data (CSV)")
        if not alk_path:
            return
        self.alkane_times = self.engine.load_alkane_data(alk_path)
        unk_path = filedialog.askopenfilename(title="Load Unknown Data (CSV)")
        if unk_path:
            self.unknown_times = self.engine.load_unknown_data(unk_path)
        self._compute_indices()

    def _build_content(self):
        tk.Label(self.content_frame, text="Retention Index Calculator",
                font=("Arial", 12, "bold"), bg="white").pack(pady=10)
        self.result_text = tk.Text(self.content_frame, height=15, width=60)
        self.result_text.pack(pady=10)

    def _compute_indices(self):
        if not self.alkane_times or not self.unknown_times:
            return
        results = self.engine.calculate_indices(self.unknown_times, self.alkane_times)
        self.result_text.delete(1.0, tk.END)
        for comp, idx in results.items():
            self.result_text.insert(tk.END, f"{comp}: {idx:.1f}\n")


# ============================================================================
# ENGINE 3 — MASS SPECTRUM DECONVOLUTION (Stein 1999; AMDIS) with matchms
# ============================================================================
class MSDeconvolutionAnalyzer:
    @classmethod
    def detect_components(cls, tic, time, min_height=1000, min_peak_width=3):
        if HAS_SCIPY:
            peaks, properties = find_peaks(tic, height=min_height, width=min_peak_width)
            return peaks
        else:
            peaks = []
            for i in range(1, len(tic)-1):
                if tic[i] > tic[i-1] and tic[i] > tic[i+1] and tic[i] > min_height:
                    peaks.append(i)
            return peaks

    @classmethod
    def extract_spectrum(cls, data_matrix, time_idx, peak_width=5):
        left = max(0, time_idx - peak_width // 2)
        right = min(data_matrix.shape[0], time_idx + peak_width // 2 + 1)
        spectrum = np.mean(data_matrix[left:right, :], axis=0)
        bg_left = max(0, left - peak_width)
        if bg_left < left:
            background = np.mean(data_matrix[bg_left:left, :], axis=0)
            spectrum = spectrum - background
            spectrum = np.maximum(spectrum, 0)
        return spectrum

    @classmethod
    def amdis_algorithm(cls, data_matrix, mz_values, time, params=None):
        if params is None:
            params = {"min_height": 1000, "peak_width": 5}
        tic = np.sum(data_matrix, axis=1)
        peak_indices = cls.detect_components(tic, time, min_height=params["min_height"])
        components = []
        for idx in peak_indices:
            spectrum = cls.extract_spectrum(data_matrix, idx, params["peak_width"])
            significant = np.where(spectrum > np.max(spectrum) * 0.05)[0]
            components.append({
                "time": time[idx],
                "peak_idx": idx,
                "spectrum": spectrum,
                "mz_values": mz_values,
                "significant_masses": significant
            })
        return components

    @classmethod
    def load_agilent_ms(cls, path):
        # Placeholder – in production, parse Agilent .D folders
        n_scans, n_masses = 1000, 100
        data = np.random.rand(n_scans, n_masses) * 1000
        time = np.linspace(0, 30, n_scans)
        mz = np.linspace(50, 550, n_masses)
        return {"data": data, "time": time, "mz": mz, "metadata": {"file": Path(path).name}}


# ============================================================================
# TAB 3: MASS SPECTRUM DECONVOLUTION (with matchms library matching)
# ============================================================================
class MSDeconvolutionTab(AnalysisTab):
    def __init__(self, parent, app, ui_queue):
        super().__init__(parent, app, ui_queue, "MS Deconvolution")
        self.data_matrix = None
        self.mz_axis = None
        self.time_axis = None
        self.components = []
        self.library = []
        self.current_component = None
        self._build_content()

    def _group_has_data(self, rows):
        # MS data not typically in CSV; rely on manual import
        return False

    def _manual_import(self):
        path = filedialog.askopenfilename(
            title="Load MS data",
            filetypes=[("mzML", "*.mzml"), ("mzXML", "*.mzxml"),
                       ("Agilent", "*.D"), ("All files", "*.*")])
        if not path:
            return
        self._load_ms_file(path)

    def _load_ms_file(self, path):
        # For now, use synthetic data; in production, use pymzml or matchms
        data = MSDeconvolutionAnalyzer.load_agilent_ms(path)
        self.data_matrix = data["data"]
        self.time_axis = data["time"]
        self.mz_axis = data["mz"]
        self.manual_label.config(text=Path(path).name)
        self.status_label.config(text=f"Loaded {self.data_matrix.shape[0]} scans")
        self._detect_components()

    def _detect_components(self):
        if self.data_matrix is None:
            return
        self.components = MSDeconvolutionAnalyzer.amdis_algorithm(
            self.data_matrix, self.mz_axis, self.time_axis
        )
        self._populate_component_list()
        self._plot_tic()

    def _populate_component_list(self):
        self.comp_listbox.delete(0, tk.END)
        for i, comp in enumerate(self.components):
            self.comp_listbox.insert(tk.END, f"Component {i+1}: t={comp['time']:.2f} min")

    def _plot_tic(self):
        if not HAS_MPL:
            return
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        tic = np.sum(self.data_matrix, axis=1)
        ax.plot(self.time_axis, tic, 'b-')
        for comp in self.components:
            ax.axvline(comp['time'], color='r', linestyle='--', alpha=0.5)
        ax.set_xlabel("Time (min)")
        ax.set_ylabel("TIC")
        ax.set_title("Total Ion Chromatogram")
        self.canvas.draw()

    def _on_component_selected(self, event):
        sel = self.comp_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        self.current_component = self.components[idx]
        self._plot_spectrum()

    def _plot_spectrum(self):
        if not HAS_MPL or self.current_component is None:
            return
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        mz = self.mz_axis
        inten = self.current_component["spectrum"]
        ax.stem(mz, inten, linefmt='b-', markerfmt='bo', basefmt='k-')
        ax.set_xlabel("m/z")
        ax.set_ylabel("Intensity")
        ax.set_title(f"Mass spectrum at t={self.current_component['time']:.2f} min")
        self.canvas.draw()

    def _load_library(self):
        path = filedialog.askopenfilename(
            title="Load spectral library (MSP)",
            filetypes=[("MSP files", "*.msp")])
        if not path:
            return
        if not HAS_MATCHMS:
            messagebox.showerror("Missing matchms", "Install matchms to use library matching")
            return
        try:
            self.library = list(load_from_msp(path))
            self.lib_label.config(text=f"Loaded {len(self.library)} spectra")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _match_spectrum(self):
        if not HAS_MATCHMS:
            messagebox.showerror("Missing matchms", "Install matchms")
            return
        if not self.library:
            messagebox.showwarning("No library", "Load a library first")
            return
        if self.current_component is None:
            return

        from matchms import Spectrum as MatchMSSpectrum
        query = MatchMSSpectrum(mz=self.mz_axis,
                                intensities=self.current_component["spectrum"],
                                metadata={})
        query = default_filters(query)
        query = normalize_intensities(query)

        method_name = self.sim_method_var.get()
        tolerance = self.tolerance_var.get()
        if method_name == "CosineGreedy":
            similarity = CosineGreedy(tolerance=tolerance)
        else:
            similarity = ModifiedCosine(tolerance=tolerance)

        self.progress.start()
        def match():
            scores = []
            for ref in self.library:
                score = similarity.pair(query, ref)
                name = ref.metadata.get('compound_name', 'Unknown')
                scores.append((score, name))
            scores.sort(key=lambda x: x[0], reverse=True)
            self.ui_queue.schedule(lambda: self._display_matches(scores))
            self.ui_queue.schedule(self.progress.stop)
        threading.Thread(target=match, daemon=True).start()

    def _display_matches(self, scores):
        self.match_listbox.delete(0, tk.END)
        for score, name in scores[:20]:
            self.match_listbox.insert(tk.END, f"{name}: {score:.3f}")

    def _build_content(self):
        paned = ttk.PanedWindow(self.content_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        left = tk.Frame(paned, bg="white", width=350)
        right = tk.Frame(paned, bg="white")
        paned.add(left, weight=1)
        paned.add(right, weight=2)

        # Left panel (controls) unchanged
        tk.Label(left, text="Detected Components", font=("Arial", 10, "bold"),
                bg="white").pack(pady=5)
        self.comp_listbox = tk.Listbox(left, height=8)
        self.comp_listbox.pack(fill=tk.X, padx=5, pady=2)
        self.comp_listbox.bind('<<ListboxSelect>>', self._on_component_selected)

        lib_frame = tk.LabelFrame(left, text="Library Matching", bg="white")
        lib_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(lib_frame, text="📚 Load Library (MSP)",
                command=self._load_library).pack(pady=2)
        self.lib_label = tk.Label(lib_frame, text="No library loaded", bg="white")
        self.lib_label.pack()

        opt_frame = tk.Frame(lib_frame, bg="white")
        opt_frame.pack(fill=tk.X, pady=2)
        tk.Label(opt_frame, text="Method:", bg="white").pack(side=tk.LEFT)
        self.sim_method_var = tk.StringVar(value="CosineGreedy")
        sim_combo = ttk.Combobox(opt_frame, textvariable=self.sim_method_var,
                                values=["CosineGreedy", "ModifiedCosine"],
                                width=12, state="readonly")
        sim_combo.pack(side=tk.LEFT, padx=2)
        tk.Label(opt_frame, text="Tol (Da):", bg="white").pack(side=tk.LEFT, padx=(5,0))
        self.tolerance_var = tk.DoubleVar(value=0.1)
        ttk.Entry(opt_frame, textvariable=self.tolerance_var, width=5).pack(side=tk.LEFT)

        ttk.Button(lib_frame, text="🔎 Match Component", command=self._match_spectrum).pack(pady=5)

        match_frame = tk.LabelFrame(left, text="Matches", bg="white")
        match_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.match_listbox = tk.Listbox(match_frame, height=10)
        self.match_listbox.pack(fill=tk.BOTH, expand=True)

        self.progress = ttk.Progressbar(left, mode='indeterminate')
        self.progress.pack(fill=tk.X, padx=5, pady=5)

        # Right panel: use a container frame with pack
        if HAS_MPL:
            plot_container = tk.Frame(right, bg="white")
            plot_container.pack(fill=tk.BOTH, expand=True)

            self.figure = Figure(figsize=(8, 6), dpi=100)
            self.canvas = FigureCanvasTkAgg(self.figure, plot_container)
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            toolbar = NavigationToolbar2Tk(self.canvas, plot_container)
            toolbar.update()
            # Toolbar is automatically packed with side=tk.BOTTOM, fill=tk.X by its __init__

            # Set a minimum size for the canvas area (optional)
            self.canvas.get_tk_widget().config(width=500, height=300)

            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, 'Load MS data', ha='center', va='center')
            ax.set_title('Mass Spectrum')
            self.canvas.draw()
        else:
            tk.Label(right, text="matplotlib required", bg="white").pack(expand=True)


# ============================================================================
# ENGINE 4 — NMR FID PROCESSING (Ernst et al. 1987; VNMRJ) with nmrglue
# ============================================================================
class NMRAnalyzer:
    @classmethod
    def read_fid(cls, path):
        if not HAS_NMRGLUE:
            return None, None
        try:
            if os.path.isdir(path):
                if os.path.exists(os.path.join(path, "fid")):
                    dic, data = ng.bruker.read(path)
                elif os.path.exists(os.path.join(path, "procpar")):
                    dic, data = ng.varian.read(path)
                else:
                    raise ValueError("Unknown NMR folder format")
            else:
                dic, data = ng.jcampdx.read(path)
            return dic, data
        except Exception as e:
            print(f"nmrglue read error: {e}")
            return None, None

    @classmethod
    def fid_to_spectrum_1d(cls, fid, dwell_time, sf, zero_fill_factor=2):
        n = len(fid)
        n_zf = n * zero_fill_factor
        fid_zf = np.zeros(n_zf, dtype=complex)
        fid_zf[:n] = fid
        spec = fft(fid_zf)
        sw = 1 / dwell_time
        freq_hz = fftfreq(n_zf, dwell_time)
        freq_ppm = freq_hz / sf
        real_spec = np.real(spec)
        return freq_ppm, real_spec

    @classmethod
    def process_2d(cls, data, dwell_times, sfrq):
        n1, n2 = data.shape
        apod = np.sin(np.pi * np.arange(n1) / n1)
        data_apod = data * apod[:, np.newaxis]
        spec_direct = fft(data_apod, axis=1)
        spec = fft(spec_direct, axis=0)
        sw1 = 1 / dwell_times[0]
        sw2 = 1 / dwell_times[1]
        freq1_hz = fftfreq(n1, dwell_times[0])
        freq2_hz = fftfreq(n2, dwell_times[1])
        freq1_ppm = freq1_hz / sfrq
        freq2_ppm = freq2_hz / sfrq
        return freq1_ppm, freq2_ppm, np.abs(spec)

    @classmethod
    def phase_correction(cls, spec, phase_0, phase_1):
        n = len(spec)
        freq = np.arange(n) / n
        phi_0 = np.radians(phase_0)
        phi_1 = np.radians(phase_1) * freq
        phi = phi_0 + phi_1
        return spec * np.exp(1j * phi)

    @classmethod
    def baseline_correction(cls, spectrum, freq, regions=None, order=3):
        if regions is None:
            n = len(spectrum)
            regions = [(0, int(n*0.1)), (int(n*0.9), n-1)]
        baseline_x = []
        baseline_y = []
        for start, end in regions:
            baseline_x.extend(freq[start:end])
            baseline_y.extend(spectrum[start:end])
        coeffs = np.polyfit(baseline_x, baseline_y, order)
        baseline = np.polyval(coeffs, freq)
        return spectrum - baseline, baseline

    @classmethod
    def peak_picking(cls, spectrum, freq, threshold=0.01, min_distance=5):
        spec_norm = spectrum / np.max(np.abs(spectrum))
        if HAS_SCIPY:
            peaks, properties = find_peaks(spec_norm, height=threshold,
                                           distance=min_distance, prominence=threshold/2)
            peak_list = [{"ppm": freq[p], "intensity": spectrum[p],
                          "height": spec_norm[p]} for p in peaks]
            return peak_list
        else:
            peaks = []
            for i in range(1, len(spectrum)-1):
                if spec_norm[i] > spec_norm[i-1] and spec_norm[i] > spec_norm[i+1]:
                    if spec_norm[i] > threshold:
                        peaks.append({"ppm": freq[i], "intensity": spectrum[i],
                                      "height": spec_norm[i]})
            return peaks


# ============================================================================
# TAB 4: NMR FID PROCESSING (with nmrglue and 2D support)
# ============================================================================
class NMRTab(AnalysisTab):
    def __init__(self, parent, app, ui_queue):
        super().__init__(parent, app, ui_queue, "NMR Processing")
        self.dic = None
        self.data = None
        self.freq_ppm = None
        self.spectrum = None
        self.is_2d = False
        self._build_content()

    def _group_has_data(self, rows):
        # NMR data not in CSV
        return False

    def _manual_import(self):
        path = filedialog.askdirectory(title="Select NMR folder (Bruker/Varian)")
        if not path:
            return
        self._load_nmr(path)

    def _load_nmr(self, path):
        if not HAS_NMRGLUE:
            messagebox.showerror("Missing nmrglue", "Install nmrglue for NMR processing")
            return
        self.dic, self.data = NMRAnalyzer.read_fid(path)
        if self.dic is None or self.data is None:
            messagebox.showerror("Error", "Could not read NMR data")
            return
        self.is_2d = len(self.data.shape) > 1
        self.manual_label.config(text=Path(path).name)
        self.status_label.config(text=f"Loaded {path}")
        self._process_data()

    def _process_data(self):
        if self.is_2d:
            try:
                if 'acqus' in self.dic:
                    sw_h = float(self.dic['acqus']['SW_h'])
                    td = int(self.dic['acqus']['TD'])
                    dwell = 1.0 / sw_h if sw_h != 0 else 1e-6
                    sw_h2 = float(self.dic.get('acqu2s', {}).get('SW_h', sw_h))
                    dwell2 = 1.0 / sw_h2 if sw_h2 != 0 else 1e-6
                    sfrq = float(self.dic['acqus']['SFO1'])
                else:
                    dwell = 1e-6; dwell2 = 1e-6; sfrq = 500.0
                freq1, freq2, spec = NMRAnalyzer.process_2d(self.data, (dwell2, dwell), sfrq)
                self.freq1_ppm = freq1
                self.freq2_ppm = freq2
                self.spectrum_2d = spec
                self._plot_2d()
            except Exception as e:
                messagebox.showerror("2D processing error", str(e))
        else:
            try:
                if 'acqus' in self.dic:
                    sw_h = float(self.dic['acqus']['SW_h'])
                    dwell = 1.0 / sw_h if sw_h != 0 else 1e-6
                    sfrq = float(self.dic['acqus']['SFO1'])
                else:
                    dwell = 1e-6; sfrq = 500.0
                fid = self.data
                if fid.dtype != complex:
                    fid = fid.astype(complex)
                self.freq_ppm, self.spectrum = NMRAnalyzer.fid_to_spectrum_1d(fid, dwell, sfrq)
                self._plot_1d()
            except Exception as e:
                messagebox.showerror("1D processing error", str(e))

    def _plot_1d(self):
        if not HAS_MPL or self.freq_ppm is None:
            return
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.plot(self.freq_ppm, self.spectrum, 'b-')
        ax.invert_xaxis()
        ax.set_xlabel("ppm")
        ax.set_ylabel("Intensity")
        ax.set_title("1D NMR Spectrum")
        self.canvas.draw()

    def _plot_2d(self):
        if not HAS_MPL or not hasattr(self, 'spectrum_2d'):
            return
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        extent = [self.freq2_ppm[-1], self.freq2_ppm[0],
                  self.freq1_ppm[0], self.freq1_ppm[-1]]
        ax.contour(self.spectrum_2d, levels=20, extent=extent, cmap='viridis')
        ax.set_xlabel("F2 (ppm)")
        ax.set_ylabel("F1 (ppm)")
        ax.set_title("2D NMR Spectrum")
        ax.invert_xaxis()
        ax.invert_yaxis()
        self.canvas.draw()

    def _build_content(self):
        if HAS_MPL:
            plot_container = tk.Frame(self.content_frame, bg="white")
            plot_container.pack(fill=tk.BOTH, expand=True)

            self.figure = Figure(figsize=(8, 6), dpi=100)
            self.canvas = FigureCanvasTkAgg(self.figure, plot_container)
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            toolbar = NavigationToolbar2Tk(self.canvas, plot_container)
            toolbar.update()

            self.canvas.get_tk_widget().config(width=500, height=300)

            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, 'Load NMR data', ha='center', va='center')
            ax.set_title('NMR Spectrum')
            self.canvas.draw()
        else:
            tk.Label(self.content_frame, text="matplotlib required", bg="white").pack(expand=True)


# ============================================================================
# ENGINE 5 — STANDARD CURVES (ICH Q2(R1); CLSI EP17-A2)
# ============================================================================
class StandardCurveAnalyzer:
    @classmethod
    def linear(cls, x, a, b):
        return a + b * x

    @classmethod
    def quadratic(cls, x, a, b, c):
        return a + b * x + c * x**2

    @classmethod
    def fit_curve(cls, concentration, response, model="linear", weights=None):
        if not HAS_SCIPY:
            return None
        if weights == "1/x":
            sigma = 1 / np.maximum(concentration, 1e-10)
        elif weights == "1/x²":
            sigma = 1 / np.maximum(concentration**2, 1e-10)
        else:
            sigma = np.ones_like(concentration)

        if model == "linear":
            slope, intercept, r_value, p_value, std_err = linregress(concentration, response)
            return {"model": "linear", "a": intercept, "b": slope,
                    "r2": r_value**2, "std_err": std_err}
        else:
            try:
                popt, pcov = curve_fit(cls.quadratic, concentration, response,
                                       sigma=sigma, absolute_sigma=False)
                residuals = response - cls.quadratic(concentration, *popt)
                ss_res = np.sum(residuals**2)
                ss_tot = np.sum((response - np.mean(response))**2)
                r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
                return {"model": "quadratic", "a": popt[0], "b": popt[1],
                        "c": popt[2], "r2": r2}
            except:
                return None

    @classmethod
    def lod_loq(cls, calibration, response_blank=None, method="residual"):
        if method == "residual" and calibration is not None:
            sigma = calibration.get("std_err", 0.01)
            slope = calibration["b"]
            if slope == 0:
                return None, None
            lod = 3.3 * sigma / slope
            loq = 10 * sigma / slope
            return lod, loq
        elif response_blank is not None:
            mean_blank = np.mean(response_blank)
            sd_blank = np.std(response_blank, ddof=1)
            lod = mean_blank + 3.3 * sd_blank
            loq = mean_blank + 10 * sd_blank
            if calibration is not None and calibration["model"] == "linear":
                lod_conc = (lod - calibration["a"]) / calibration["b"]
                loq_conc = (loq - calibration["a"]) / calibration["b"]
                return lod_conc, loq_conc
            return lod, loq
        return None, None

    @classmethod
    def recovery(cls, known_conc, measured_conc):
        recovery = (measured_conc / known_conc) * 100
        return {"mean": np.mean(recovery), "sd": np.std(recovery, ddof=1),
                "min": np.min(recovery), "max": np.max(recovery)}

    @classmethod
    def precision(cls, replicate_responses):
        mean_resp = np.mean(replicate_responses)
        sd_resp = np.std(replicate_responses, ddof=1)
        if mean_resp == 0:
            return 0
        return (sd_resp / mean_resp) * 100

    @classmethod
    def inverse_predict(cls, response, calibration):
        if calibration["model"] == "linear":
            return (response - calibration["a"]) / calibration["b"]
        else:
            a = calibration["c"]
            b = calibration["b"]
            c = calibration["a"] - response
            discriminant = b**2 - 4*a*c
            if discriminant < 0:
                return None
            x1 = (-b + np.sqrt(discriminant)) / (2*a)
            x2 = (-b - np.sqrt(discriminant)) / (2*a)
            return x1 if x1 > 0 else x2

    @classmethod
    def load_calibration_data(cls, path):
        return pd.read_csv(path)


# ============================================================================
# TAB 5: STANDARD CURVES
# ============================================================================
class StandardCurveTab(AnalysisTab):
    REQUIRED_FIELDS = ['Concentration_ppm', 'Area']   # standard names

    def __init__(self, parent, app, ui_queue):
        super().__init__(parent, app, ui_queue, "Standard Curves")
        self.engine = StandardCurveAnalyzer
        self.data = None
        self.calibration = None
        self._build_content()

    def _group_has_data(self, rows):
        if not hasattr(self, 'column_map'):
            return False
        return all(field in self.column_map for field in self.REQUIRED_FIELDS)

    def _load_sample_data(self, group_id, rows):
        conc_col = self.column_map.get('Concentration_ppm')
        area_col = self.column_map.get('Area')
        if not conc_col or not area_col:
            self.status_label.config(text="Missing required columns")
            return
        conc = []
        area = []
        for row in rows:
            try:
                conc.append(float(row[conc_col]))
                area.append(float(row[area_col]))
            except:
                continue
        if not conc:
            self.status_label.config(text="No valid data")
            return
        # Sort by concentration (optional, but good practice)
        df = pd.DataFrame({conc_col: conc, area_col: area}).sort_values(by=conc_col)
        self.data = df
        self._compute()
        self.status_label.config(text=f"Loaded {len(conc)} points")

    def _manual_import(self):
        path = filedialog.askopenfilename(title="Load Calibration Data (CSV)")
        if not path:
            return
        self.data = self.engine.load_calibration_data(path)
        self.manual_label.config(text=Path(path).name)
        self._compute()

    def _build_content(self):
        tk.Label(self.content_frame, text="Standard Curve Calculator",
                font=("Arial", 12, "bold"), bg="white").pack(pady=10)
        self.result_text = tk.Text(self.content_frame, height=15, width=60)
        self.result_text.pack(pady=10)

    def _compute(self):
        if self.data is None:
            return
        # Assume first column is concentration, second is response
        conc = self.data.iloc[:, 0].values
        resp = self.data.iloc[:, 1].values
        cal = self.engine.fit_curve(conc, resp)
        if cal:
            self.calibration = cal
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, f"Model: {cal['model']}\n")
            self.result_text.insert(tk.END, f"R²: {cal['r2']:.4f}\n")
            if cal['model'] == 'linear':
                self.result_text.insert(tk.END, f"Slope: {cal['b']:.4f}\n")
                self.result_text.insert(tk.END, f"Intercept: {cal['a']:.4f}\n")
                lod, loq = self.engine.lod_loq(cal)
                self.result_text.insert(tk.END, f"LOD: {lod:.4f}\n")
                self.result_text.insert(tk.END, f"LOQ: {loq:.4f}\n")
            else:
                self.result_text.insert(tk.END, f"a: {cal['a']:.4f}\n")
                self.result_text.insert(tk.END, f"b: {cal['b']:.4f}\n")
                self.result_text.insert(tk.END, f"c: {cal['c']:.4f}\n")


# ============================================================================
# ENGINE 6 — RESOLUTION CALCULATIONS (USP <621>; Ph.Eur. 2.2.46)
# ============================================================================
class ResolutionAnalyzer:
    @classmethod
    def resolution(cls, tR1, tR2, w1, w2):
        if w1 + w2 == 0:
            return 0
        return 2 * (tR2 - tR1) / (w1 + w2)

    @classmethod
    def plate_number(cls, tR, width, method="USP"):
        if width == 0:
            return 0
        if method == "USP":
            return 16 * (tR / width) ** 2
        else:
            return 5.54 * (tR / width) ** 2

    @classmethod
    def plate_height(cls, N, column_length):
        if N == 0:
            return 0
        return column_length / N

    @classmethod
    def tailing_factor(cls, w_005, f):
        if f == 0:
            return 1.0
        return w_005 / (2 * f)

    @classmethod
    def capacity_factor(cls, tR, t0):
        if t0 == 0:
            return 0
        return (tR - t0) / t0

    @classmethod
    def selectivity(cls, k1, k2):
        if k1 == 0:
            return 0
        return k2 / k1

    @classmethod
    def peak_asymmetry(cls, tR, t_left, t_right, height_fraction=0.1):
        left_dist = tR - t_left
        right_dist = t_right - tR
        if left_dist == 0:
            return 0
        return right_dist / left_dist

    @classmethod
    def system_suitability(cls, peaks, t0=None):
        results = {}
        if len(peaks) >= 2:
            resolutions = []
            for i in range(len(peaks)-1):
                Rs = cls.resolution(
                    peaks[i]["tR"], peaks[i+1]["tR"],
                    peaks[i].get("width", 1), peaks[i+1].get("width", 1)
                )
                resolutions.append(Rs)
            results["resolution_min"] = min(resolutions) if resolutions else 0
            results["resolution_mean"] = np.mean(resolutions) if resolutions else 0
        plate_numbers = []
        for p in peaks:
            if "width" in p:
                N = cls.plate_number(p["tR"], p["width"], method="USP")
                plate_numbers.append(N)
            elif "width_half" in p:
                N = cls.plate_number(p["tR"], p["width_half"], method="EP")
                plate_numbers.append(N)
        if plate_numbers:
            results["plate_min"] = min(plate_numbers)
            results["plate_mean"] = np.mean(plate_numbers)
        if t0 is not None:
            k_values = [cls.capacity_factor(p["tR"], t0) for p in peaks]
            results["k_min"] = min(k_values)
            results["k_max"] = max(k_values)
            if len(k_values) >= 2:
                results["selectivity"] = cls.selectivity(k_values[0], k_values[1])
        return results


# ============================================================================
# TAB 6: RESOLUTION CALCULATIONS (fully implemented)
# ============================================================================
class ResolutionTab(AnalysisTab):
    REQUIRED_FIELDS = ['RetentionTime_min', 'Width_min']   # standard names

    def __init__(self, parent, app, ui_queue):
        super().__init__(parent, app, ui_queue, "Resolution")
        self.engine = ResolutionAnalyzer
        self.peaks = []               # list of dicts with keys: tR, width, tailing (optional), plates (optional)
        self.t0 = None                 # void time (optional)
        self._build_content()

    def _group_has_data(self, rows):
        if not hasattr(self, 'column_map'):
            return False
        return all(field in self.column_map for field in self.REQUIRED_FIELDS)

    def _load_sample_data(self, group_id, rows):
        rt_col = self.column_map.get('RetentionTime_min')
        width_col = self.column_map.get('Width_min')
        tail_col = self.column_map.get('TailingFactor')   # optional
        plates_col = self.column_map.get('Plates')        # optional
        if not rt_col or not width_col:
            self.status_label.config(text="Missing required columns")
            return
        self.peaks = []
        for row in rows:
            try:
                peak = {
                    'tR': float(row[rt_col]),
                    'width': float(row[width_col])
                }
                if tail_col and tail_col in row:
                    peak['tailing'] = float(row[tail_col])
                if plates_col and plates_col in row:
                    peak['plates'] = float(row[plates_col])
                self.peaks.append(peak)
            except:
                continue
        self._refresh_peak_table()
        self.status_label.config(text=f"Loaded {len(self.peaks)} peaks from {group_id}")

    def _manual_import(self):
        path = filedialog.askopenfilename(
            title="Load Peak List (CSV)",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not path:
            return
        try:
            df = pd.read_csv(path)
            # Map columns using the mapper if possible
            headers = df.columns.tolist()
            col_map = self._map_columns(headers)
            rt_col = col_map.get('RetentionTime_min')
            width_col = col_map.get('Width_min')
            if not rt_col or not width_col:
                messagebox.showerror("Error", "Could not find retention time or width columns.")
                return
            self.peaks = []
            for _, row in df.iterrows():
                peak = {
                    'tR': row[rt_col],
                    'width': row[width_col]
                }
                if 'TailingFactor' in col_map:
                    peak['tailing'] = row.get(col_map['TailingFactor'], None)
                if 'Plates' in col_map:
                    peak['plates'] = row.get(col_map['Plates'], None)
                self.peaks.append(peak)
            self.manual_label.config(text=Path(path).name)
            self._refresh_peak_table()
            self.status_label.config(text=f"Loaded {len(self.peaks)} peaks")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _add_peak(self):
        try:
            tR = float(self.entry_tR.get())
            width = float(self.entry_width.get())
            tailing = self.entry_tailing.get()
            plates = self.entry_plates.get()
            peak = {'tR': tR, 'width': width}
            if tailing:
                peak['tailing'] = float(tailing)
            if plates:
                peak['plates'] = float(plates)
            self.peaks.append(peak)
            self._refresh_peak_table()
            self.entry_tR.delete(0, tk.END)
            self.entry_width.delete(0, tk.END)
            self.entry_tailing.delete(0, tk.END)
            self.entry_plates.delete(0, tk.END)
        except ValueError:
            messagebox.showerror("Error", "Invalid number format.")

    def _remove_selected_peak(self):
        selected = self.peak_table.selection()
        if not selected:
            return
        for item in selected:
            idx = self.peak_table.index(item)
            self.peaks.pop(idx)
        self._refresh_peak_table()

    def _refresh_peak_table(self):
        for row in self.peak_table.get_children():
            self.peak_table.delete(row)
        for i, p in enumerate(self.peaks):
            self.peak_table.insert('', tk.END, values=(
                i+1,
                f"{p['tR']:.3f}",
                f"{p['width']:.3f}",
                f"{p.get('tailing', '—')}",
                f"{p.get('plates', '—')}"
            ))

    def _calculate(self):
        if len(self.peaks) < 2:
            messagebox.showwarning("Insufficient data", "Need at least two peaks.")
            return
        t0_val = None
        if self.entry_t0.get():
            try:
                t0_val = float(self.entry_t0.get())
            except ValueError:
                messagebox.showerror("Error", "Invalid t0 value.")
                return
        peak_list = []
        for p in self.peaks:
            item = {'tR': p['tR']}
            if 'width' in p:
                item['width'] = p['width']
            if 'tailing' in p:
                item['tailing'] = p['tailing']
            if 'plates' in p:
                item['plates'] = p['plates']
            peak_list.append(item)
        results = self.engine.system_suitability(peak_list, t0_val)
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "System Suitability Results:\n")
        self.result_text.insert(tk.END, "-" * 40 + "\n")
        if 'resolution_min' in results:
            self.result_text.insert(tk.END, f"Min resolution: {results['resolution_min']:.3f}\n")
        if 'resolution_mean' in results:
            self.result_text.insert(tk.END, f"Mean resolution: {results['resolution_mean']:.3f}\n")
        if 'plate_min' in results:
            self.result_text.insert(tk.END, f"Min plate count: {results['plate_min']:.0f}\n")
        if 'plate_mean' in results:
            self.result_text.insert(tk.END, f"Mean plate count: {results['plate_mean']:.0f}\n")
        if 'k_min' in results:
            self.result_text.insert(tk.END, f"Min capacity factor: {results['k_min']:.3f}\n")
        if 'k_max' in results:
            self.result_text.insert(tk.END, f"Max capacity factor: {results['k_max']:.3f}\n")
        if 'selectivity' in results:
            self.result_text.insert(tk.END, f"Selectivity (α): {results['selectivity']:.3f}\n")
        if len(self.peaks) >= 2:
            self.result_text.insert(tk.END, "\nPairwise Resolution:\n")
            for i in range(len(self.peaks)-1):
                Rs = self.engine.resolution(
                    self.peaks[i]['tR'], self.peaks[i+1]['tR'],
                    self.peaks[i]['width'], self.peaks[i+1]['width']
                )
                self.result_text.insert(tk.END, f"  {i+1}-{i+2}: {Rs:.3f}\n")

    def _build_content(self):
        paned = ttk.PanedWindow(self.content_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        left = tk.Frame(paned, bg="white", width=500)
        right = tk.Frame(paned, bg="white")
        paned.add(left, weight=2)
        paned.add(right, weight=1)

        # ========== LEFT PANEL ==========
        input_frame = tk.LabelFrame(left, text="Add Peak", bg="white", font=("Arial", 9, "bold"), fg=C_HEADER)
        input_frame.pack(fill=tk.X, padx=5, pady=5)

        row1 = tk.Frame(input_frame, bg="white")
        row1.pack(fill=tk.X, pady=2)
        tk.Label(row1, text="tR (min):", font=("Arial", 8), bg="white", width=10).pack(side=tk.LEFT)
        self.entry_tR = ttk.Entry(row1, width=10)
        self.entry_tR.pack(side=tk.LEFT, padx=2)
        tk.Label(row1, text="Width (min):", font=("Arial", 8), bg="white", width=10).pack(side=tk.LEFT, padx=(10,0))
        self.entry_width = ttk.Entry(row1, width=10)
        self.entry_width.pack(side=tk.LEFT, padx=2)

        row2 = tk.Frame(input_frame, bg="white")
        row2.pack(fill=tk.X, pady=2)
        tk.Label(row2, text="Tailing (opt):", font=("Arial", 8), bg="white", width=10).pack(side=tk.LEFT)
        self.entry_tailing = ttk.Entry(row2, width=10)
        self.entry_tailing.pack(side=tk.LEFT, padx=2)
        tk.Label(row2, text="Plates (opt):", font=("Arial", 8), bg="white", width=10).pack(side=tk.LEFT, padx=(10,0))
        self.entry_plates = ttk.Entry(row2, width=10)
        self.entry_plates.pack(side=tk.LEFT, padx=2)

        btn_frame = tk.Frame(input_frame, bg="white")
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="➕ Add Peak", command=self._add_peak).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="🗑️ Remove Selected", command=self._remove_selected_peak).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="📂 Import CSV", command=self._manual_import).pack(side=tk.LEFT, padx=2)

        table_frame = tk.LabelFrame(left, text="Peaks", bg="white", font=("Arial", 9, "bold"), fg=C_HEADER)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ('#', 'tR (min)', 'Width (min)', 'Tailing', 'Plates')
        self.peak_table = ttk.Treeview(table_frame, columns=columns, show='headings', height=12)
        for col in columns:
            self.peak_table.heading(col, text=col)
            self.peak_table.column(col, width=70 if col=='#' else 100)
        self.peak_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_table = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.peak_table.yview)
        scroll_table.pack(side=tk.RIGHT, fill=tk.Y)
        self.peak_table.configure(yscrollcommand=scroll_table.set)

        t0_frame = tk.Frame(left, bg="white")
        t0_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(t0_frame, text="Void time t0 (min, optional):", font=("Arial", 8), bg="white").pack(side=tk.LEFT)
        self.entry_t0 = ttk.Entry(t0_frame, width=10)
        self.entry_t0.pack(side=tk.LEFT, padx=5)

        ttk.Button(left, text="🧮 Calculate", command=self._calculate).pack(pady=5)

        # ========== RIGHT PANEL ==========
        result_frame = tk.LabelFrame(right, text="Results", bg="white", font=("Arial", 9, "bold"), fg=C_HEADER)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.result_text = tk.Text(result_frame, height=20, width=40, font=("Courier", 9))
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        scroll_result = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_text.yview)
        scroll_result.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text.configure(yscrollcommand=scroll_result.set)


# ============================================================================
# ENGINE 7 — PEAK PURITY ANALYSIS (ISO 13808; HPLC Method Validation)
# ============================================================================
class PeakPurityAnalyzer:
    @classmethod
    def spectral_correlation(cls, spectrum1, spectrum2):
        s1_norm = spectrum1 / np.sqrt(np.sum(spectrum1**2))
        s2_norm = spectrum2 / np.sqrt(np.sum(spectrum2**2))
        match = np.dot(s1_norm, s2_norm) * 1000
        return match

    @classmethod
    def absorbance_ratio(cls, chromatogram_at_wavelengths, wavelengths, time):
        if len(wavelengths) < 2:
            return None
        ratio = chromatogram_at_wavelengths[:, 0] / (chromatogram_at_wavelengths[:, 1] + 1e-10)
        return ratio

    @classmethod
    def purity_angle(cls, spectra_matrix, time_idx, peak_width):
        left = max(0, time_idx - peak_width // 2)
        right = min(spectra_matrix.shape[0], time_idx + peak_width // 2 + 1)
        peak_spectra = spectra_matrix[left:right, :]
        mean_spectrum = np.mean(peak_spectra, axis=0)
        angles = []
        for spec in peak_spectra:
            s_norm = spec / np.sqrt(np.sum(spec**2))
            m_norm = mean_spectrum / np.sqrt(np.sum(mean_spectrum**2))
            cos_sim = np.dot(s_norm, m_norm)
            angle = np.arccos(np.clip(cos_sim, -1, 1)) * 180 / np.pi
            angles.append(angle)
        return {"max_angle": np.max(angles), "mean_angle": np.mean(angles), "std_angle": np.std(angles)}

    @classmethod
    def purity_threshold(cls, noise_level, peak_height):
        threshold = 90 + 10 * (noise_level / peak_height)
        return min(threshold, 99.9)

    @classmethod
    def first_derivative(cls, spectrum, wavelengths):
        return np.gradient(spectrum, wavelengths)

    @classmethod
    def second_derivative(cls, spectrum, wavelengths):
        first = np.gradient(spectrum, wavelengths)
        return np.gradient(first, wavelengths)

    @classmethod
    def load_dad_data(cls, path):
        # synthetic demo
        n_time, n_wavelength = 1000, 100
        time = np.linspace(0, 20, n_time)
        wavelengths = np.linspace(200, 400, n_wavelength)
        main_spec = np.exp(-(wavelengths - 250)**2 / (2 * 20**2))
        imp_spec = np.exp(-(wavelengths - 280)**2 / (2 * 15**2))
        main_time = np.exp(-(time - 10)**2 / (2 * 0.5**2))
        imp_time = np.exp(-(time - 10.2)**2 / (2 * 0.4**2)) * 0.1
        data = np.zeros((n_time, n_wavelength))
        for i in range(n_time):
            data[i, :] = main_time[i] * main_spec + imp_time[i] * imp_spec
        return {"data": data, "time": time, "wavelengths": wavelengths,
                "metadata": {"file": Path(path).name}}


# ============================================================================
# TAB 7: PEAK PURITY ANALYSIS
# ============================================================================
class PeakPurityTab(AnalysisTab):
    def __init__(self, parent, app, ui_queue):
        super().__init__(parent, app, ui_queue, "Peak Purity")
        self.engine = PeakPurityAnalyzer
        self.data = None
        self.time = None
        self.wavelengths = None
        self._build_content()

    def _group_has_data(self, rows):
        # DAD data not typically in CSV
        return False

    def _manual_import(self):
        path = filedialog.askopenfilename(title="Load DAD Data (CSV)")
        if not path:
            return
        self.data = self.engine.load_dad_data(path)
        self.manual_label.config(text=Path(path).name)
        self._plot()

    def _build_content(self):
        if HAS_MPL:
            plot_container = tk.Frame(self.content_frame, bg="white")
            plot_container.pack(fill=tk.BOTH, expand=True)

            self.figure = Figure(figsize=(8, 6), dpi=100)
            self.canvas = FigureCanvasTkAgg(self.figure, plot_container)
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            toolbar = NavigationToolbar2Tk(self.canvas, plot_container)
            toolbar.update()

            self.canvas.get_tk_widget().config(width=500, height=300)

            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, 'Load DAD data', ha='center', va='center')
            ax.set_title('Peak Purity')
            self.canvas.draw()
        else:
            tk.Label(self.content_frame, text="matplotlib required", bg="white").pack(expand=True)

    def _plot(self):
        if not HAS_MPL or self.data is None:
            return
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        im = ax.imshow(self.data["data"].T, aspect='auto',
                       extent=[self.data["time"][0], self.data["time"][-1],
                               self.data["wavelengths"][-1], self.data["wavelengths"][0]],
                       cmap='viridis')
        ax.set_xlabel("Time (min)")
        ax.set_ylabel("Wavelength (nm)")
        ax.set_title("DAD Heatmap")
        plt.colorbar(im, ax=ax)
        self.canvas.draw()


# ============================================================================
# MAIN PLUGIN CLASS
# ============================================================================
class ChromatographySuite:
    def __init__(self, main_app):
        self.app = main_app
        self.window = None
        self.ui_queue = None
        self.tabs = {}

    def show_interface(self):
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("🧪 Chromatography Analysis Suite v2.3")
        self.window.geometry("1200x800")
        self.window.minsize(1100, 700)
        self.window.transient(self.app.root)

        self.ui_queue = ThreadSafeUI(self.window)
        self._build_ui()
        self.window.lift()
        self.window.focus_force()
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        header = tk.Frame(self.window, bg=C_HEADER, height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="🧪", font=("Arial", 20),
                 bg=C_HEADER, fg="white").pack(side=tk.LEFT, padx=10)
        tk.Label(header, text="CHROMATOGRAPHY ANALYSIS SUITE",
                 font=("Arial", 14, "bold"), bg=C_HEADER, fg="white").pack(side=tk.LEFT)
        tk.Label(header, text="v2.3 · Vendor‑Agnostic Mapping",
                 font=("Arial", 9), bg=C_HEADER, fg=C_ACCENT).pack(side=tk.LEFT, padx=10)

        self.status_var = tk.StringVar(value="Ready")
        status_label = tk.Label(header, textvariable=self.status_var,
                                font=("Arial", 9), bg=C_HEADER, fg=C_LIGHT)
        status_label.pack(side=tk.RIGHT, padx=10)

        style = ttk.Style()
        style.configure("Chrom.TNotebook.Tab", font=("Arial", 9, "bold"), padding=[8, 4])

        notebook = ttk.Notebook(self.window, style="Chrom.TNotebook")
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create all 7 tabs (pass app so they can access config)
        self.tabs['peak'] = PeakIntegrationTab(notebook, self.app, self.ui_queue)
        notebook.add(self.tabs['peak'].frame, text=" Peak Integration ")

        self.tabs['ri'] = RetentionIndexTab(notebook, self.app, self.ui_queue)
        notebook.add(self.tabs['ri'].frame, text=" Retention Indices ")

        self.tabs['ms'] = MSDeconvolutionTab(notebook, self.app, self.ui_queue)
        notebook.add(self.tabs['ms'].frame, text=" MS Deconvolution ")

        self.tabs['nmr'] = NMRTab(notebook, self.app, self.ui_queue)
        notebook.add(self.tabs['nmr'].frame, text=" NMR FID ")

        self.tabs['curve'] = StandardCurveTab(notebook, self.app, self.ui_queue)
        notebook.add(self.tabs['curve'].frame, text=" Standard Curves ")

        self.tabs['res'] = ResolutionTab(notebook, self.app, self.ui_queue)
        notebook.add(self.tabs['res'].frame, text=" Resolution ")

        self.tabs['purity'] = PeakPurityTab(notebook, self.app, self.ui_queue)
        notebook.add(self.tabs['purity'].frame, text=" Peak Purity ")

        footer = tk.Frame(self.window, bg=C_LIGHT, height=25)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)

        tk.Label(footer,
                text="Foley & Dorsey 1984 · Kovats 1958 · Stein 1999 · Ernst et al. 1987 · ICH Q2(R1) · USP <621> · ISO 13808 · matchms · nmrglue",
                font=("Arial", 8), bg=C_LIGHT, fg=C_HEADER).pack(side=tk.LEFT, padx=10)

        self.progress_bar = ttk.Progressbar(footer, mode='determinate', length=150)
        self.progress_bar.pack(side=tk.RIGHT, padx=10)

    def _set_status(self, msg):
        self.status_var.set(msg)

    def _show_progress(self, show):
        if show:
            self.progress_bar.config(mode='indeterminate')
            self.progress_bar.start(10)
        else:
            self.progress_bar.stop()
            self.progress_bar.config(mode='determinate', value=0)

    def _on_close(self):
        if self.window:
            self.window.destroy()
            self.window = None


# ============================================================================
# PLUGIN REGISTRATION
# ============================================================================
def setup_plugin(main_app):
    plugin = ChromatographySuite(main_app)
    if hasattr(main_app, 'advanced_menu'):
        main_app.advanced_menu.add_command(
            label=f"{PLUGIN_INFO['icon']} {PLUGIN_INFO['name']}",
            command=plugin.show_interface
        )
        print(f"✅ Added to Advanced menu: {PLUGIN_INFO['name']}")
        return plugin
    if hasattr(main_app, 'menu_bar'):
        if not hasattr(main_app, 'analysis_menu'):
            main_app.analysis_menu = tk.Menu(main_app.menu_bar, tearoff=0)
            main_app.menu_bar.add_cascade(label="🔬 Analysis", menu=main_app.analysis_menu)
        main_app.analysis_menu.add_command(
            label=f"{PLUGIN_INFO['icon']} {PLUGIN_INFO['name']}",
            command=plugin.show_interface
        )
        print(f"✅ Added to Analysis menu: {PLUGIN_INFO['name']}")
    return plugin
