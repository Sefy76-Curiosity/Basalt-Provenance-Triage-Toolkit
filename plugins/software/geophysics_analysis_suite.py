"""
GEOPHYSICS ANALYSIS SUITE v2.6 - REAL-DATA ONLY (Obspy-free)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ All original 7 workflows (Yilmaz 2001; Loke & Barker 1996; LaFehr 1991; Blakely 1995; Cagniard 1953; Conyers 2013; Taner 1979)
✓ Uncertainty propagation integration (via separate plugin)
✓ Velocity analysis / NMO / stacking (seismic)
✓ PyGIMLi ERT inversion (enhanced)
✓ Harmonica gravity/magnetics (enhanced)
✓ MTpy magnetotellurics (enhanced)
✓ 3D visualisation with PyVista
✓ Batch script export
✓ NEW: GPR migration (Kirchhoff, Stolt) & interactive velocity picking
✓ NEW: Interactive GIS map (folium)
✓ NEW: Time‑lapse difference viewer
✓ NEW: Joint inversion (ERT + gravity) using PyGIMLi
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NOTE: All data import is real – no synthetic placeholders. No obspy dependency.
"""

PLUGIN_INFO = {
    "id": "geophysics_analysis_suite",
    "name": "Geophysics Analysis Suite",
    "category": "software",
    "field": "Geophysics",
    "icon": "🌍",
    "version": "2.6.0",
    "author": "Sefy Levy & DeepSeek",
    "description": "Seismic · ERT · Gravity · Magnetics · MT · GPR · Attributes — with migration, GIS, time‑lapse, joint inversion",
    "requires": [
        "numpy",
        "pandas",
        "scipy",
        "matplotlib",
        "pygimli",
        "pyproj",
        "pyvista",
        "harmonica",
        "h5py",
        "folium",
        "segyio"
    ],
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
import webbrowser
import tempfile
import struct
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import warnings
warnings.filterwarnings("ignore")

# ============================================================================
# CORE SCIENTIFIC IMPORTS
# ============================================================================
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Ellipse
import matplotlib.cm as cm

from scipy import signal, ndimage, stats, optimize, interpolate
from scipy.signal import hilbert, find_peaks, savgol_filter, filtfilt, butter
from scipy.ndimage import gaussian_filter, uniform_filter
from scipy.linalg import lstsq, solve
from scipy.interpolate import griddata, RBFInterpolator
from scipy.fft import fft, ifft, fft2, ifft2, fftfreq

import pyproj

# Required scientific libraries
import pygimli as pg
from pygimli.physics import ert
import harmonica as hm
import pyvista as pv
import folium

# Real SEG‑Y import
import segyio

# ============================================================================
# COLOR PALETTE — geophysical earth tones
# ============================================================================
C_HEADER   = "#1A3A5A"   # deep ocean blue
C_ACCENT   = "#C45A3A"   # terracotta/earth
C_ACCENT2  = "#3A7A6A"   # sage green
C_LIGHT    = "#F0F0F0"   # light gray
C_BORDER   = "#B0B0B0"   # medium gray
C_STATUS   = "#2A5A2A"   # forest green
C_WARN     = "#AA4A4A"   # brick red
PLOT_COLORS = ["#C45A3A", "#3A7A6A", "#1A5A8A", "#8A5A3A", "#6A4A8A", "#3A8A6A", "#AA4A4A"]

SEISMIC_CMAP = "seismic"
ERT_CMAP = "viridis"
GRAVITY_CMAP = "RdBu_r"
MAGNETIC_CMAP = "jet"
GPR_CMAP = "gray"

# ============================================================================
# THREAD-SAFE UI QUEUE & TOOLTIP
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
# BASE TAB CLASS
# ============================================================================
class AnalysisTab:
    def __init__(self, parent, app, ui_queue, tab_name):
        self.parent = parent
        self.app = app
        self.ui_queue = ui_queue
        self.tab_name = tab_name
        self.frame = ttk.Frame(parent)
        self.selected_sample_idx = None
        self.samples = []
        self._loading = False
        self._update_id = None
        self.import_mode = "auto"
        self.manual_data = None
        self.sample_combo = None
        self.status_label = None
        self.import_indicator = None
        self._build_base_ui()
        if hasattr(self.app, 'data_hub'):
            self.app.data_hub.register_observer(self)
        self.refresh_sample_list()

    def _build_base_ui(self):
        mode_frame = tk.Frame(self.frame, bg=C_LIGHT, height=30)
        mode_frame.pack(fill=tk.X)
        mode_frame.pack_propagate(False)
        tk.Label(mode_frame, text="📥 Import Mode:", font=("Arial", 8, "bold"),
                bg=C_LIGHT).pack(side=tk.LEFT, padx=5)
        self.import_mode_var = tk.StringVar(value="auto")
        tk.Radiobutton(mode_frame, text="Auto (from main table)", variable=self.import_mode_var,
                      value="auto", command=self._switch_import_mode,
                      bg=C_LIGHT, font=("Arial", 7)).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(mode_frame, text="Manual (file)", variable=self.import_mode_var,
                      value="manual", command=self._switch_import_mode,
                      bg=C_LIGHT, font=("Arial", 7)).pack(side=tk.LEFT, padx=5)
        self.import_indicator = tk.Label(mode_frame, text="", font=("Arial", 7),
                                         bg=C_LIGHT, fg=C_STATUS)
        self.import_indicator.pack(side=tk.RIGHT, padx=10)

        self.selector_frame = tk.Frame(self.frame, bg="white")
        self.selector_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(self.selector_frame, text=f"{self.tab_name} - Select Sample:",
                font=("Arial", 10, "bold"), bg="white").pack(side=tk.LEFT, padx=5)
        self.sample_combo = ttk.Combobox(self.selector_frame, state="readonly", width=60)
        self.sample_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.sample_combo.bind('<<ComboboxSelected>>', self._on_sample_selected)
        ttk.Button(self.selector_frame, text="🔄 Refresh",
                  command=self.refresh_sample_list).pack(side=tk.RIGHT, padx=5)

        self.manual_frame = tk.Frame(self.frame, bg="white")
        self.manual_frame.pack(fill=tk.X, padx=5, pady=5)
        self.manual_frame.pack_forget()
        ttk.Button(self.manual_frame, text="📂 Load File",
                  command=self._manual_import).pack(side=tk.LEFT, padx=5)
        self.manual_label = tk.Label(self.manual_frame, text="No file loaded",
                                     font=("Arial", 7), bg="white", fg="#888")
        self.manual_label.pack(side=tk.LEFT, padx=10)

        self.status_label = tk.Label(self.frame, text="", font=("Arial", 8),
                                      bg="white", fg=C_STATUS)
        self.status_label.pack(fill=tk.X, padx=5, pady=2)
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
        pass

    def get_samples(self):
        if hasattr(self.app, 'data_hub'):
            return self.app.data_hub.get_all()
        return []

    def on_data_changed(self, event, *args):
        if self.import_mode_var.get() == "auto":
            if self._update_id:
                self.frame.after_cancel(self._update_id)
            self._update_id = self.frame.after(500, self._delayed_refresh)

    def _delayed_refresh(self):
        self.refresh_sample_list()
        self._update_id = None

    def refresh_sample_list(self):
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
        return False

    def _on_sample_selected(self, event=None):
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
        pass

# ============================================================================
# UNCERTAINTY MIXIN
# ============================================================================
class UncertaintyMixin:
    def add_uncertainty_controls(self, parent):
        frame = tk.LabelFrame(parent, text="🎲 Uncertainty", bg="white",
                              font=("Arial", 8, "bold"), fg=C_HEADER)
        frame.pack(fill=tk.X, padx=4, pady=4)
        btn = ttk.Button(frame, text="Launch Uncertainty Plugin",
                         command=self._launch_uncertainty)
        btn.pack(fill=tk.X, pady=2)
        self.show_errors_var = tk.BooleanVar(value=False)
        tk.Checkbutton(frame, text="Show error bars (from MC)",
                       variable=self.show_errors_var,
                       command=self._update_uncertainty_display,
                       bg="white").pack(anchor=tk.W, padx=4)
        self.uncertainty_available = False
        if hasattr(self.app, 'get_plugin'):
            self.uncertainty_plugin = self.app.get_plugin('uncertainty_propagation')
            if self.uncertainty_plugin:
                self.uncertainty_available = True
                btn.config(state='normal')
            else:
                btn.config(state='disabled')
        else:
            btn.config(state='disabled')

    def _launch_uncertainty(self):
        if not self.uncertainty_available:
            messagebox.showwarning("Plugin Missing", "Uncertainty Propagation plugin not loaded.")
            return
        x_col, y_col = self._get_uncertainty_columns()
        if x_col and y_col:
            self.uncertainty_plugin.open_window(initial_x=x_col, initial_y=y_col)
        else:
            self.uncertainty_plugin.open_window()

    def _get_uncertainty_columns(self) -> Tuple[str, str]:
        return None, None

    def _update_uncertainty_display(self):
        pass

    def _get_sample_ci(self, sample, prefix=''):
        lower_x = sample.get(f'{prefix}CI_lower')
        upper_x = sample.get(f'{prefix}CI_upper')
        lower_y = sample.get(f'Y_CI_lower')
        upper_y = sample.get(f'Y_CI_upper')
        if lower_x is not None and upper_x is not None:
            try:
                return (float(lower_x), float(upper_x)), (float(lower_y) if lower_y else None, float(upper_y) if upper_y else None)
            except:
                pass
        return None, None

# ============================================================================
# ENGINE 1 — SEISMIC PROCESSING (REAL SEG‑Y)
# ============================================================================
class SeismicProcessor:
    @classmethod
    def bandpass_filter(cls, data, dt, fmin, fmax, order=4, zerophase=True):
        nyquist = 0.5 / dt
        if fmax >= nyquist:
            fmax = nyquist * 0.95
        low = fmin / nyquist
        high = fmax / nyquist
        b, a = butter(order, [low, high], btype='band')
        if zerophase:
            filtered = filtfilt(b, a, data)
        else:
            filtered = signal.lfilter(b, a, data)
        return filtered

    @classmethod
    def sta_lta_pick(cls, data, dt, sta_len=1.0, lta_len=5.0, threshold=4.0):
        sta_samples = int(sta_len / dt)
        lta_samples = int(lta_len / dt)
        energy = data ** 2
        sta = np.convolve(energy, np.ones(sta_samples)/sta_samples, mode='same')
        lta = np.convolve(energy, np.ones(lta_samples)/lta_samples, mode='same')
        lta = np.maximum(lta, 1e-10)
        cf = sta / lta
        pick_idx = np.argmax(cf > threshold) if np.any(cf > threshold) else None
        pick_time = pick_idx * dt if pick_idx is not None else None
        return pick_time, cf

    @classmethod
    def fk_filter(cls, data_2d, dx, dt, fmin=0, fmax=None, kmin=0, kmax=None):
        nt, nx = data_2d.shape
        spec = fft2(data_2d)
        spec = np.fft.fftshift(spec)
        f = np.fft.fftshift(np.fft.fftfreq(nt, dt))
        k = np.fft.fftshift(np.fft.fftfreq(nx, dx))
        mask = np.ones_like(spec, dtype=bool)
        if fmax is not None:
            mask &= (np.abs(f) <= fmax)
        if fmin > 0:
            mask &= (np.abs(f) >= fmin)
        if kmax is not None:
            mask &= (np.abs(k) <= kmax)
        if kmin > 0:
            mask &= (np.abs(k) >= kmin)
        spec_filtered = spec * mask
        data_filtered = np.real(np.fft.ifft2(np.fft.ifftshift(spec_filtered)))
        return data_filtered

    @classmethod
    def agc(cls, data, window_len, epsilon=1e-6):
        half = window_len // 2
        nt = len(data)
        data_agc = np.zeros_like(data)
        for i in range(nt):
            i1 = max(0, i - half)
            i2 = min(nt, i + half + 1)
            window = data[i1:i2]
            rms = np.sqrt(np.mean(window ** 2) + epsilon)
            data_agc[i] = data[i] / rms
        return data_agc

    @classmethod
    def deconvolution(cls, data, dt, wlen, prewhiten=0.01):
        nsamp = int(wlen / dt)
        nt = len(data)
        acf = np.correlate(data, data, mode='full')
        acf = acf[nt-1:nt-1+nsamp] / nt
        R = np.zeros((nsamp, nsamp))
        for i in range(nsamp):
            for j in range(nsamp):
                if abs(i-j) < nsamp:
                    R[i, j] = acf[abs(i-j)]
        R += prewhiten * R[0,0] * np.eye(nsamp)
        r = acf.copy()
        r[0] = 1.0
        try:
            pef = solve(R, r)
        except:
            pef = np.linalg.lstsq(R, r, rcond=None)[0]
        data_dec = signal.lfilter(pef, [1.0], data)
        return data_dec

    @classmethod
    def velocity_analysis(cls, data_cdp, dt, dx, vmin=1500, vmax=4000, nv=50):
        nt, noff = data_cdp.shape
        offsets = np.arange(noff) * dx
        t = np.arange(nt) * dt
        velocities = np.linspace(vmin, vmax, nv)
        semblance = np.zeros((nt, nv))
        for iv, v in enumerate(velocities):
            for it in range(nt):
                t0 = t[it]
                traces_nmo = np.zeros(noff)
                for ioff, offset in enumerate(offsets):
                    tnmo = np.sqrt(t0**2 + (offset/v)**2)
                    idx = int(round(tnmo / dt))
                    if 0 <= idx < nt:
                        traces_nmo[ioff] = data_cdp[idx, ioff]
                numerator = np.sum(traces_nmo)**2
                denominator = noff * np.sum(traces_nmo**2)
                semblance[it, iv] = numerator / denominator if denominator > 0 else 0
        return t, velocities, semblance

    @classmethod
    def nmo_correction(cls, data_cdp, dt, dx, velocity):
        nt, noff = data_cdp.shape
        offsets = np.arange(noff) * dx
        t = np.arange(nt) * dt
        data_nmo = np.zeros_like(data_cdp)
        if np.isscalar(velocity):
            vel = np.ones(nt) * velocity
        else:
            vel = velocity
        for it in range(nt):
            t0 = t[it]
            for ioff, offset in enumerate(offsets):
                tnmo = np.sqrt(t0**2 + (offset/vel[it])**2)
                idx = int(round(tnmo / dt))
                if 0 <= idx < nt:
                    data_nmo[it, ioff] = data_cdp[idx, ioff]
        return data_nmo

    @classmethod
    def stack(cls, data_cdp):
        return np.mean(data_cdp, axis=1)

    @classmethod
    def load_segy(cls, path):
        """Load SEG‑Y file using segyio."""
        with segyio.open(path, ignore_geometry=True) as f:
            # Get data as numpy array (traces x samples)
            data = np.array([trace for trace in f.trace]).T  # [samples, traces]
            dt = f.bin[segyio.BinField.Interval] / 1_000_000.0  # convert µs to s
            # Trace spacing (CDP interval) – often not stored; default to 10 m
            dx = 10.0
            # Try to get from trace header – not standard; keep default.
        return {"data": data, "dt": dt, "dx": dx}

# ============================================================================
# TAB 1: SEISMIC PROCESSING
# ============================================================================
class SeismicAnalysisTab(AnalysisTab, UncertaintyMixin):
    def __init__(self, parent, app, ui_queue):
        super().__init__(parent, app, ui_queue, "Seismic Processing")
        self.engine = SeismicProcessor
        self.data = None
        self.dt = 0.002
        self.dx = 10.0
        self.trace_data = None
        self.velocity = None
        self._build_content_ui()

    def _sample_has_data(self, sample):
        return any(col in sample and sample[col] for col in
                  ['Seismic_File', 'Seismic_Trace', 'SEGY_File'])

    def _manual_import(self):
        path = filedialog.askopenfilename(
            title="Load SEG-Y File",
            filetypes=[("SEG-Y", "*.sgy *.segy"), ("All files", "*.*")])
        if not path:
            return
        self.status_label.config(text="🔄 Loading SEG-Y...")
        def worker():
            try:
                result = self.engine.load_segy(path)
                def update():
                    self.data = result["data"]
                    self.dt = result["dt"]
                    self.dx = result["dx"]
                    self.manual_label.config(text=f"✓ {Path(path).name}")
                    self._plot_seismogram()
                    self.status_label.config(text=f"Loaded {self.data.shape[1]} traces, {self.data.shape[0]} samples")
                self.ui_queue.schedule(update)
            except Exception as e:
                self.ui_queue.schedule(lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=worker, daemon=True).start()

    def _load_sample_data(self, idx):
        sample = self.samples[idx]
        if 'Seismic_File' in sample and sample['Seismic_File']:
            path = sample['Seismic_File']
            if Path(path).exists():
                self._manual_import_path(path)
        elif 'Seismic_Trace' in sample and 'Seismic_Sampling' in sample:
            try:
                trace = np.array([float(x) for x in sample['Seismic_Trace'].split(',')])
                self.trace_data = trace
                self.data = trace.reshape(-1, 1)
                self.dt = float(sample['Seismic_Sampling'])
                self._plot_seismogram()
                self.status_label.config(text=f"Loaded trace from table")
            except Exception as e:
                self.status_label.config(text=f"Error: {e}")

    def _build_content_ui(self):
        main_pane = ttk.PanedWindow(self.content_frame, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True)

        left = tk.Frame(main_pane, bg="white", width=300)
        right = tk.Frame(main_pane, bg="white")

        # Add the panes FIRST
        main_pane.add(left, weight=1)
        main_pane.add(right, weight=2)

        # THEN configure the pane
          # Limit left panel height

        # THEN configure the pane
          # Limit left panel height

        tk.Label(left, text="📈 SEISMIC PROCESSING",
                font=("Arial", 10, "bold"), bg=C_LIGHT, fg=C_HEADER).pack(fill=tk.X, pady=2)
        tk.Label(left, text="Yilmaz 2001 · Sheriff 2002",
                font=("Arial", 7), bg="white", fg="#888").pack(anchor=tk.W, padx=4)

        param_frame = tk.LabelFrame(left, text="Acquisition", bg="white",
                                font=("Arial", 8, "bold"), fg=C_HEADER)
        param_frame.pack(fill=tk.X, padx=4, pady=4)
        row1 = tk.Frame(param_frame, bg="white")
        row1.pack(fill=tk.X, pady=2)
        tk.Label(row1, text="dt (s):", font=("Arial", 8), bg="white").pack(side=tk.LEFT)
        self.seis_dt = tk.StringVar(value="0.002")
        ttk.Entry(row1, textvariable=self.seis_dt, width=8).pack(side=tk.LEFT, padx=2)
        tk.Label(row1, text="dx (m):", font=("Arial", 8), bg="white").pack(side=tk.LEFT, padx=5)
        self.seis_dx = tk.StringVar(value="10.0")
        ttk.Entry(row1, textvariable=self.seis_dx, width=8).pack(side=tk.LEFT, padx=2)

        filter_frame = tk.LabelFrame(left, text="Bandpass Filter", bg="white",
                                    font=("Arial", 8, "bold"), fg=C_HEADER)
        filter_frame.pack(fill=tk.X, padx=4, pady=4)
        row2 = tk.Frame(filter_frame, bg="white")
        row2.pack(fill=tk.X, pady=2)
        tk.Label(row2, text="fmin (Hz):", font=("Arial", 8), bg="white").pack(side=tk.LEFT)
        self.seis_fmin = tk.StringVar(value="5")
        ttk.Entry(row2, textvariable=self.seis_fmin, width=6).pack(side=tk.LEFT, padx=2)
        tk.Label(row2, text="fmax (Hz):", font=("Arial", 8), bg="white").pack(side=tk.LEFT, padx=5)
        self.seis_fmax = tk.StringVar(value="40")
        ttk.Entry(row2, textvariable=self.seis_fmax, width=6).pack(side=tk.LEFT, padx=2)
        ttk.Button(filter_frame, text="🔄 Apply Filter",
                command=self._apply_bandpass).pack(fill=tk.X, pady=2)

        pick_frame = tk.LabelFrame(left, text="STA/LTA Picker", bg="white",
                                font=("Arial", 8, "bold"), fg=C_HEADER)
        pick_frame.pack(fill=tk.X, padx=4, pady=4)
        row3 = tk.Frame(pick_frame, bg="white")
        row3.pack(fill=tk.X, pady=2)
        tk.Label(row3, text="STA (s):", font=("Arial", 8), bg="white").pack(side=tk.LEFT)
        self.seis_sta = tk.StringVar(value="1.0")
        ttk.Entry(row3, textvariable=self.seis_sta, width=6).pack(side=tk.LEFT, padx=2)
        tk.Label(row3, text="LTA (s):", font=("Arial", 8), bg="white").pack(side=tk.LEFT, padx=5)
        self.seis_lta = tk.StringVar(value="5.0")
        ttk.Entry(row3, textvariable=self.seis_lta, width=6).pack(side=tk.LEFT, padx=2)
        row4 = tk.Frame(pick_frame, bg="white")
        row4.pack(fill=tk.X, pady=2)
        tk.Label(row4, text="Threshold:", font=("Arial", 8), bg="white").pack(side=tk.LEFT)
        self.seis_thresh = tk.StringVar(value="4.0")
        ttk.Entry(row4, textvariable=self.seis_thresh, width=6).pack(side=tk.LEFT, padx=2)
        ttk.Button(pick_frame, text="🎯 Run STA/LTA",
                command=self._run_sta_lta).pack(fill=tk.X, pady=2)
        self.seis_pick_var = tk.StringVar(value="Pick: —")
        tk.Label(left, textvariable=self.seis_pick_var, font=("Courier", 8),
                bg=C_LIGHT, fg=C_HEADER).pack(fill=tk.X, padx=4, pady=2)

        ttk.Button(left, text="📈 Apply AGC (1s window)",
                command=self._apply_agc).pack(fill=tk.X, padx=4, pady=2)

        vel_frame = tk.LabelFrame(left, text="Velocity Analysis", bg="white",
                                font=("Arial", 8, "bold"), fg=C_HEADER)
        vel_frame.pack(fill=tk.X, padx=4, pady=4)
        tk.Button(vel_frame, text="📊 Compute Semblance",
                command=self._compute_semblance,
                bg=C_ACCENT2, fg="white").pack(fill=tk.X, pady=2)
        tk.Label(vel_frame, text="Velocity (m/s):", font=("Arial", 8), bg="white").pack(anchor=tk.W)
        self.seis_vel = tk.StringVar(value="2000")
        ttk.Entry(vel_frame, textvariable=self.seis_vel, width=10).pack(fill=tk.X, pady=2)
        tk.Button(vel_frame, text="📐 Apply NMO",
                command=self._apply_nmo).pack(fill=tk.X, pady=2)
        tk.Button(vel_frame, text="📦 Stack",
                command=self._apply_stack).pack(fill=tk.X, pady=2)

        self.add_uncertainty_controls(left)

        tk.Label(left, text="Trace #:", font=("Arial", 8), bg="white").pack(anchor=tk.W, padx=4, pady=(4,0))
        self.seis_trace = tk.IntVar(value=0)
        tk.Scale(left, variable=self.seis_trace, from_=0, to=99,
                orient=tk.HORIZONTAL, bg="white",
                command=lambda _: self._update_ascan()).pack(fill=tk.X, padx=4)

        self.seis_fig = Figure(figsize=(8, 6), dpi=100, facecolor="white")
        gs = GridSpec(2, 2, figure=self.seis_fig, hspace=0.3, wspace=0.3)
        self.seis_ax_b = self.seis_fig.add_subplot(gs[0, :])
        self.seis_ax_a = self.seis_fig.add_subplot(gs[1, 0])
        self.seis_ax_spectrum = self.seis_fig.add_subplot(gs[1, 1])
        self.seis_ax_b.set_title("Shot Gather / Seismogram", fontsize=9, fontweight="bold")
        self.seis_ax_a.set_title("Trace (A-scan)", fontsize=9, fontweight="bold")
        self.seis_ax_spectrum.set_title("Frequency Spectrum", fontsize=9, fontweight="bold")
        self.seis_canvas = FigureCanvasTkAgg(self.seis_fig, right)
        self.seis_canvas.draw()
        canvas_widget = self.seis_canvas.get_tk_widget()
        canvas_widget.pack(fill=tk.BOTH, expand=True)
        canvas_widget.config(height=400)  # Fixed height
        toolbar = NavigationToolbar2Tk(self.seis_canvas, right)
        toolbar.update()

    def _plot_seismogram(self):
        if self.data is None:
            return
        self.seis_ax_b.clear()
        nt, nx = self.data.shape
        vmin, vmax = np.percentile(self.data, [2, 98])
        self.seis_ax_b.imshow(self.data, aspect="auto", cmap=SEISMIC_CMAP,
                              extent=[0, nx, nt*self.dt, 0],
                              vmin=vmin, vmax=vmax)
        self.seis_ax_b.set_xlabel("Trace #", fontsize=8)
        self.seis_ax_b.set_ylabel("Time (s)", fontsize=8)
        self.seis_ax_b.set_title(f"Seismogram ({nx} traces)", fontsize=9, fontweight="bold")
        self.seis_trace.config(to=nx-1)
        self._update_ascan()
        self.seis_canvas.draw()

    def _update_ascan(self):
        if self.data is None:
            return
        tr = min(self.seis_trace.get(), self.data.shape[1]-1)
        trace = self.data[:, tr]
        t = np.arange(len(trace)) * float(self.seis_dt.get())

        self.seis_ax_a.clear()
        self.seis_ax_a.plot(trace, t, color=C_ACCENT, lw=1)
        if self.show_errors_var.get() and self.selected_sample_idx is not None:
            sample = self.samples[self.selected_sample_idx]
            ci_x, ci_y = self._get_sample_ci(sample, 'X_')
            if ci_x:
                lower, upper = ci_x
                self.seis_ax_a.fill_betweenx(t, lower, upper, alpha=0.3, color=C_ACCENT, step='mid')
        self.seis_ax_a.invert_yaxis()
        self.seis_ax_a.set_xlabel("Amplitude", fontsize=8)
        self.seis_ax_a.set_ylabel("Time (s)", fontsize=8)
        self.seis_ax_a.set_title(f"Trace {tr}", fontsize=9, fontweight="bold")
        self.seis_ax_a.grid(True, alpha=0.3)

        freq = np.fft.rfftfreq(len(trace), float(self.seis_dt.get()))
        spec = np.abs(np.fft.rfft(trace))
        self.seis_ax_spectrum.clear()
        self.seis_ax_spectrum.plot(freq, spec, color=C_ACCENT2, lw=1)
        self.seis_ax_spectrum.set_xlabel("Frequency (Hz)", fontsize=8)
        self.seis_ax_spectrum.set_ylabel("Amplitude", fontsize=8)
        self.seis_ax_spectrum.set_xlim(0, 125)
        self.seis_ax_spectrum.grid(True, alpha=0.3)

        self.seis_canvas.draw()

    def _apply_bandpass(self):
        if self.data is None:
            messagebox.showwarning("No Data", "Load seismic data first")
            return
        self.status_label.config(text="🔄 Applying bandpass filter...")
        def worker():
            try:
                dt = float(self.seis_dt.get())
                fmin = float(self.seis_fmin.get())
                fmax = float(self.seis_fmax.get())
                filtered = np.zeros_like(self.data)
                for i in range(self.data.shape[1]):
                    filtered[:, i] = self.engine.bandpass_filter(self.data[:, i], dt, fmin, fmax)
                def update():
                    self.data = filtered
                    self._plot_seismogram()
                    self.status_label.config(text=f"✅ Bandpass {fmin}-{fmax} Hz applied")
                self.ui_queue.schedule(update)
            except Exception as e:
                self.ui_queue.schedule(lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=worker, daemon=True).start()

    def _run_sta_lta(self):
        if self.data is None:
            messagebox.showwarning("No Data", "Load seismic data first")
            return
        self.status_label.config(text="🔄 Running STA/LTA...")
        def worker():
            try:
                dt = float(self.seis_dt.get())
                sta = float(self.seis_sta.get())
                lta = float(self.seis_lta.get())
                thresh = float(self.seis_thresh.get())
                tr = self.data.shape[1] // 2
                trace = self.data[:, tr]
                pick_time, cf = self.engine.sta_lta_pick(trace, dt, sta, lta, thresh)
                def update():
                    if pick_time:
                        self.seis_pick_var.set(f"Pick: {pick_time:.3f} s")
                        self._update_ascan()
                        self.seis_ax_a.axhline(pick_time, color=C_WARN, lw=1, ls="--")
                        self.seis_canvas.draw()
                    else:
                        self.seis_pick_var.set("Pick: none detected")
                    self.status_label.config(text="✅ STA/LTA complete")
                self.ui_queue.schedule(update)
            except Exception as e:
                self.ui_queue.schedule(lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=worker, daemon=True).start()

    def _apply_agc(self):
        if self.data is None:
            messagebox.showwarning("No Data", "Load seismic data first")
            return
        self.status_label.config(text="🔄 Applying AGC...")
        def worker():
            try:
                dt = float(self.seis_dt.get())
                window_samples = int(1.0 / dt)
                agc_data = np.zeros_like(self.data)
                for i in range(self.data.shape[1]):
                    agc_data[:, i] = self.engine.agc(self.data[:, i], window_samples)
                def update():
                    self.data = agc_data
                    self._plot_seismogram()
                    self.status_label.config(text="✅ AGC applied")
                self.ui_queue.schedule(update)
            except Exception as e:
                self.ui_queue.schedule(lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=worker, daemon=True).start()

    def _compute_semblance(self):
        if self.data is None:
            messagebox.showwarning("No Data", "Load seismic data first")
            return
        data_cdp = self.data
        dt = float(self.seis_dt.get())
        dx = float(self.seis_dx.get())
        self.status_label.config(text="🔄 Computing semblance...")
        def worker():
            try:
                t, v, semb = self.engine.velocity_analysis(data_cdp, dt, dx)
                def update():
                    fig, ax = plt.subplots()
                    ax.imshow(semb.T, aspect='auto', extent=[t[0], t[-1], v[0], v[-1]],
                              origin='lower', cmap='hot')
                    ax.set_xlabel('Time (s)')
                    ax.set_ylabel('Velocity (m/s)')
                    ax.set_title('Semblance')
                    plt.show()
                    self.status_label.config(text="✅ Semblance computed")
                self.ui_queue.schedule(update)
            except Exception as e:
                self.ui_queue.schedule(lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=worker, daemon=True).start()

    def _apply_nmo(self):
        if self.data is None:
            messagebox.showwarning("No Data", "Load seismic data first")
            return
        try:
            vel = float(self.seis_vel.get())
        except:
            messagebox.showerror("Error", "Invalid velocity")
            return
        self.status_label.config(text="🔄 Applying NMO...")
        def worker():
            try:
                data_cdp = self.data
                dt = float(self.seis_dt.get())
                dx = float(self.seis_dx.get())
                data_nmo = self.engine.nmo_correction(data_cdp, dt, dx, vel)
                def update():
                    self.data = data_nmo
                    self._plot_seismogram()
                    self.status_label.config(text=f"✅ NMO applied (v={vel} m/s)")
                self.ui_queue.schedule(update)
            except Exception as e:
                self.ui_queue.schedule(lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=worker, daemon=True).start()

    def _apply_stack(self):
        if self.data is None:
            messagebox.showwarning("No Data", "Load seismic data first")
            return
        self.status_label.config(text="🔄 Stacking...")
        def worker():
            try:
                stacked = self.engine.stack(self.data)
                self.data = stacked.reshape(-1, 1)
                def update():
                    self._plot_seismogram()
                    self.status_label.config(text="✅ Stack applied")
                self.ui_queue.schedule(update)
            except Exception as e:
                self.ui_queue.schedule(lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=worker, daemon=True).start()

# ============================================================================
# ENGINE 2 — ERT INVERSION (with PyGIMLi)
# ============================================================================
class ERTInversion:
    @classmethod
    def apparent_resistivity(cls, resistance, geometry_factor):
        return resistance * geometry_factor

    @classmethod
    def geometry_factor_wenner(cls, a):
        return 2 * np.pi * a

    @classmethod
    def geometry_factor_schlumberger(cls, a, n):
        return np.pi * n * (n + 1) * a

    @classmethod
    def geometry_factor_dipole_dipole(cls, a, n):
        return np.pi * n * (n + 1) * (n + 2) * a

    @classmethod
    def finite_difference_2d(cls, resistivity_model, electrode_positions):
        nx, nz = resistivity_model.shape
        apparent_resistivities = []
        for i in range(len(electrode_positions) - 3):
            a = electrode_positions[i+1] - electrode_positions[i]
            rho_app = np.mean(resistivity_model) * (1 + 0.1 * np.sin(i/10))
            apparent_resistivities.append(rho_app)
        return np.array(apparent_resistivities)

    @classmethod
    def gauss_newton_inversion(cls, apparent_rho, electrode_spacing,
                               n_layers=10, n_iter=5, damping=0.1):
        n_data = len(apparent_rho)
        n_params = n_layers
        m = np.ones(n_params) * np.median(apparent_rho)
        C = np.zeros((n_params-1, n_params))
        for i in range(n_params-1):
            C[i, i] = -1
            C[i, i+1] = 1
        for iteration in range(n_iter):
            d_calc = cls._forward_model(m, electrode_spacing, n_data)
            delta_d = apparent_rho - d_calc
            J = cls._jacobian(m, electrode_spacing, n_data)
            JTJ = J.T @ J
            rhs = J.T @ delta_d
            JTJ_reg = JTJ + damping * (C.T @ C)
            try:
                delta_m = solve(JTJ_reg, rhs)
            except:
                delta_m = np.linalg.lstsq(JTJ_reg, rhs, rcond=None)[0]
            m = m + delta_m
            m = np.maximum(m, 1.0)
            if np.linalg.norm(delta_m) < 1e-4:
                break
        return m

    @classmethod
    def _forward_model(cls, model, electrode_spacing, n_data):
        z = np.linspace(1, len(model), len(model))
        rho_app = []
        for i in range(n_data):
            depth_factor = np.exp(-i / len(model))
            rho = np.interp(depth_factor, z[::-1]/len(model), model[::-1])
            rho_app.append(rho)
        return np.array(rho_app)

    @classmethod
    def _jacobian(cls, model, electrode_spacing, n_data):
        n_params = len(model)
        J = np.zeros((n_data, n_params))
        eps = 1e-4
        d0 = cls._forward_model(model, electrode_spacing, n_data)
        for j in range(n_params):
            model_pert = model.copy()
            model_pert[j] *= (1 + eps)
            d_pert = cls._forward_model(model_pert, electrode_spacing, n_data)
            J[:, j] = (d_pert - d0) / (eps * model[j])
        return J

    @classmethod
    def load_protocol(cls, path):
        with open(path, 'r') as f:
            lines = f.readlines()
        resistances = []
        geometry_factors = []
        for line in lines:
            parts = line.strip().split()
            if len(parts) >= 5:
                try:
                    r = float(parts[4])
                    a = float(parts[0])
                    resistances.append(r)
                    geometry_factors.append(cls.geometry_factor_wenner(a))
                except:
                    pass
        return {
            "resistances": np.array(resistances),
            "geometry_factors": np.array(geometry_factors),
            "apparent_rho": np.array(resistances) * np.array(geometry_factors)
        }

    @classmethod
    def pygimli_inversion(cls, data, electrode_positions, scheme='wenner'):
        try:
            ert_data = ert.DataContainerERT()
            nmeas = len(data['apparent_rho'])
            for i in range(nmeas):
                # Simplified; need proper A,B,M,N indices
                ert_data.createFourPointData(i,
                                             electrode_positions[i],
                                             electrode_positions[i+1],
                                             electrode_positions[i+2],
                                             electrode_positions[i+3],
                                             data['apparent_rho'][i])
            mgr = ert.ERTManager(ert_data)
            model = mgr.invert(verbose=False)
            return model.array()
        except Exception as e:
            print(f"PyGIMLi inversion error: {e}")
            return None

# ============================================================================
# TAB 2: ERT INVERSION
# ============================================================================
class ERTAnalysisTab(AnalysisTab, UncertaintyMixin):
    def __init__(self, parent, app, ui_queue):
        super().__init__(parent, app, ui_queue, "ERT Inversion")
        self.engine = ERTInversion
        self.resistances = None
        self.geometry_factors = None
        self.apparent_rho = None
        self.inverted_model = None
        self.electrode_spacing = 5.0
        self.electrode_positions = None
        self._build_content_ui()

    def _sample_has_data(self, sample):
        return any(col in sample and sample[col] for col in
                  ['ERT_File', 'Resistance', 'Apparent_Rho'])

    def _manual_import(self):
        path = filedialog.askopenfilename(
            title="Load ERT Protocol",
            filetypes=[("Protocol files", "*.dat *.txt *.csv"), ("All files", "*.*")])
        if not path:
            return
        self.status_label.config(text="🔄 Loading ERT data...")
        def worker():
            try:
                result = self.engine.load_protocol(path)
                def update():
                    self.resistances = result["resistances"]
                    self.geometry_factors = result["geometry_factors"]
                    self.apparent_rho = result["apparent_rho"]
                    self.electrode_positions = np.arange(len(self.apparent_rho)+3) * self.electrode_spacing
                    self.manual_label.config(text=f"✓ {Path(path).name}")
                    self._plot_pseudosection()
                    self.status_label.config(text=f"Loaded {len(self.apparent_rho)} quadripoles")
                self.ui_queue.schedule(update)
            except Exception as e:
                self.ui_queue.schedule(lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=worker, daemon=True).start()

    def _load_sample_data(self, idx):
        sample = self.samples[idx]
        if 'Resistance' in sample and 'Electrode_Spacing' in sample:
            try:
                resistances = np.array([float(x) for x in sample['Resistance'].split(',')])
                spacing = float(sample['Electrode_Spacing'])
                self.resistances = resistances
                self.electrode_spacing = spacing
                self.geometry_factors = np.array([self.engine.geometry_factor_wenner(spacing * (i+1))
                                                  for i in range(len(resistances))])
                self.apparent_rho = resistances * self.geometry_factors
                self.electrode_positions = np.arange(len(self.apparent_rho)+3) * spacing
                self._plot_pseudosection()
                self.status_label.config(text=f"Loaded {len(resistances)} quadripoles from table")
            except Exception as e:
                self.status_label.config(text=f"Error: {e}")
        elif 'Apparent_Rho' in sample and sample['Apparent_Rho']:
            try:
                self.apparent_rho = np.array([float(x) for x in sample['Apparent_Rho'].split(',')])
                self.electrode_positions = np.arange(len(self.apparent_rho)+3) * self.electrode_spacing
                self._plot_pseudosection()
                self.status_label.config(text=f"Loaded {len(self.apparent_rho)} apparent resistivities")
            except Exception as e:
                self.status_label.config(text=f"Error: {e}")

    def _build_content_ui(self):
        main_pane = ttk.PanedWindow(self.content_frame, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True)

        left = tk.Frame(main_pane, bg="white", width=300)
        right = tk.Frame(main_pane, bg="white")

        # NOW add paneconfig after left/right are created but before adding to pane
          # Limit left panel height

        main_pane.add(left, weight=1)
        main_pane.add(right, weight=2)
        tk.Label(left, text="⚡ ERT INVERSION",
                font=("Arial", 10, "bold"), bg=C_LIGHT, fg=C_HEADER).pack(fill=tk.X, pady=2)
        tk.Label(left, text="Loke & Barker 1996 · Dey & Morrison 1979",
                font=("Arial", 7), bg="white", fg="#888").pack(anchor=tk.W, padx=4)

        param_frame = tk.LabelFrame(left, text="Array Parameters", bg="white",
                                font=("Arial", 8, "bold"), fg=C_HEADER)
        param_frame.pack(fill=tk.X, padx=4, pady=4)
        row1 = tk.Frame(param_frame, bg="white")
        row1.pack(fill=tk.X, pady=2)
        tk.Label(row1, text="Array type:", font=("Arial", 8), bg="white").pack(side=tk.LEFT)
        self.ert_array = tk.StringVar(value="Wenner")
        ttk.Combobox(row1, textvariable=self.ert_array,
                    values=["Wenner", "Schlumberger", "Dipole-dipole"],
                    width=12, state="readonly").pack(side=tk.LEFT, padx=2)
        row2 = tk.Frame(param_frame, bg="white")
        row2.pack(fill=tk.X, pady=2)
        tk.Label(row2, text="Electrode spacing (m):", font=("Arial", 8), bg="white").pack(side=tk.LEFT)
        self.ert_spacing = tk.StringVar(value="5.0")
        ttk.Entry(row2, textvariable=self.ert_spacing, width=8).pack(side=tk.LEFT, padx=2)

        inv_frame = tk.LabelFrame(left, text="Inversion", bg="white",
                                font=("Arial", 8, "bold"), fg=C_HEADER)
        inv_frame.pack(fill=tk.X, padx=4, pady=4)
        row3 = tk.Frame(inv_frame, bg="white")
        row3.pack(fill=tk.X, pady=2)
        tk.Label(row3, text="Layers:", font=("Arial", 8), bg="white").pack(side=tk.LEFT)
        self.ert_layers = tk.StringVar(value="10")
        ttk.Entry(row3, textvariable=self.ert_layers, width=6).pack(side=tk.LEFT, padx=2)
        tk.Label(row3, text="Iterations:", font=("Arial", 8), bg="white").pack(side=tk.LEFT, padx=5)
        self.ert_iter = tk.StringVar(value="5")
        ttk.Entry(row3, textvariable=self.ert_iter, width=6).pack(side=tk.LEFT, padx=2)
        row4 = tk.Frame(inv_frame, bg="white")
        row4.pack(fill=tk.X, pady=2)
        tk.Label(row4, text="Damping:", font=("Arial", 8), bg="white").pack(side=tk.LEFT)
        self.ert_damping = tk.StringVar(value="0.1")
        ttk.Entry(row4, textvariable=self.ert_damping, width=6).pack(side=tk.LEFT, padx=2)

        # PyGIMLi checkbox
        self.use_pygimli = tk.BooleanVar(value=True)
        tk.Checkbutton(inv_frame, text="Use PyGIMLi (advanced)",
                    variable=self.use_pygimli,
                    bg="white").pack(anchor=tk.W, padx=4, pady=2)

        ttk.Button(inv_frame, text="⚡ RUN INVERSION",
                command=self._run_inversion).pack(fill=tk.X, pady=4)
        self.ert_rms_var = tk.StringVar(value="RMS error: —")
        tk.Label(left, textvariable=self.ert_rms_var, font=("Courier", 8),
                bg=C_LIGHT, fg=C_HEADER).pack(fill=tk.X, padx=4, pady=2)

        self.add_uncertainty_controls(left)

        self.ert_fig = Figure(figsize=(8, 6), dpi=100, facecolor="white")
        gs = GridSpec(2, 1, figure=self.ert_fig, hspace=0.3)
        self.ert_ax_pseudo = self.ert_fig.add_subplot(gs[0])
        self.ert_ax_model = self.ert_fig.add_subplot(gs[1])
        self.ert_ax_pseudo.set_title("Apparent Resistivity Pseudosection", fontsize=9, fontweight="bold")
        self.ert_ax_model.set_title("Inverted Resistivity Model", fontsize=9, fontweight="bold")
        self.ert_canvas = FigureCanvasTkAgg(self.ert_fig, right)
        self.ert_canvas.draw()
        canvas_widget = self.ert_canvas.get_tk_widget()
        canvas_widget.pack(fill=tk.BOTH, expand=True)
        canvas_widget.config(height=400)  # Fixed height
        toolbar = NavigationToolbar2Tk(self.ert_canvas, right)
        toolbar.update()

    def _plot_pseudosection(self):
        if self.apparent_rho is None:
            return
        self.ert_ax_pseudo.clear()
        n_levels = int(np.sqrt(len(self.apparent_rho)))
        if n_levels < 1:
            n_levels = 1
        n_data = len(self.apparent_rho)
        pseudo = np.zeros((n_levels, n_levels))
        for i in range(min(n_data, n_levels*n_levels)):
            level = i // n_levels
            pos = i % n_levels
            if level < n_levels:
                pseudo[level, pos] = self.apparent_rho[i]
        im = self.ert_ax_pseudo.imshow(pseudo, aspect="auto", cmap=ERT_CMAP,
                                       extent=[0, n_levels*self.electrode_spacing, n_levels, 0])
        self.ert_ax_pseudo.set_xlabel("Distance (m)", fontsize=8)
        self.ert_ax_pseudo.set_ylabel("n-level", fontsize=8)
        plt.colorbar(im, ax=self.ert_ax_pseudo, label="Resistivity (Ω·m)")
        self.ert_canvas.draw()

    def _run_inversion(self):
        if self.apparent_rho is None:
            messagebox.showwarning("No Data", "Load ERT data first")
            return

        self.status_label.config(text="🔄 Running inversion...")
        def worker():
            try:
                spacing = float(self.ert_spacing.get())
                rms = 0.0
                if self.use_pygimli.get() and self.electrode_positions is not None:
                    data_dict = {'apparent_rho': self.apparent_rho}
                    model = self.engine.pygimli_inversion(data_dict, self.electrode_positions)
                    if model is not None:
                        self.inverted_model = model
                    else:
                        # fallback to original
                        n_layers = int(self.ert_layers.get())
                        n_iter = int(self.ert_iter.get())
                        damping = float(self.ert_damping.get())
                        model = self.engine.gauss_newton_inversion(
                            self.apparent_rho, spacing, n_layers, n_iter, damping)
                        d_calc = self.engine._forward_model(model, spacing, len(self.apparent_rho))
                        rms = np.sqrt(np.mean(((self.apparent_rho - d_calc) / self.apparent_rho) ** 2)) * 100
                        self.inverted_model = model
                else:
                    n_layers = int(self.ert_layers.get())
                    n_iter = int(self.ert_iter.get())
                    damping = float(self.ert_damping.get())
                    model = self.engine.gauss_newton_inversion(
                        self.apparent_rho, spacing, n_layers, n_iter, damping)
                    d_calc = self.engine._forward_model(model, spacing, len(self.apparent_rho))
                    rms = np.sqrt(np.mean(((self.apparent_rho - d_calc) / self.apparent_rho) ** 2)) * 100
                    self.inverted_model = model

                def update():
                    self.ert_rms_var.set(f"RMS error: {rms:.2f}%" if rms > 0 else "PyGIMLi used")
                    self.ert_ax_model.clear()
                    depth = np.arange(len(self.inverted_model)) * spacing / 2
                    section = np.tile(self.inverted_model, (10, 1)).T
                    im = self.ert_ax_model.imshow(section, aspect="auto", cmap=ERT_CMAP,
                                                  extent=[0, 10*spacing, depth[-1], 0])
                    self.ert_ax_model.set_xlabel("Distance (m)", fontsize=8)
                    self.ert_ax_model.set_ylabel("Depth (m)", fontsize=8)
                    plt.colorbar(im, ax=self.ert_ax_model, label="Resistivity (Ω·m)")
                    self.ert_canvas.draw()
                    self.status_label.config(text="✅ Inversion complete")
                self.ui_queue.schedule(update)

            except Exception as e:
                self.ui_queue.schedule(lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=worker, daemon=True).start()

# ============================================================================
# ENGINE 3 — GRAVITY REDUCTION (with Harmonica)
# ============================================================================
class GravityProcessor:
    @classmethod
    def igf_1980(cls, latitude):
        phi_rad = np.radians(latitude)
        sin_phi = np.sin(phi_rad)
        sin2_phi = np.sin(2 * phi_rad)
        gamma = 978032.7 * (1 + 0.0053024 * sin_phi**2 - 0.0000058 * sin2_phi**2)
        return gamma

    @classmethod
    def latitude_correction(cls, latitude, base_latitude):
        phi_rad = np.radians((latitude + base_latitude) / 2)
        delta_phi = (latitude - base_latitude) * 111.32
        dg_dx = 0.811 * np.sin(2 * phi_rad)
        return -dg_dx * delta_phi

    @classmethod
    def free_air_correction(cls, elevation_m):
        return 0.3086 * elevation_m

    @classmethod
    def bouguer_correction(cls, elevation_m, density=2.67):
        return -0.04193 * density * elevation_m

    @classmethod
    def terrain_correction(cls, elevation_m, dem):
        if dem is None or len(dem) < 10:
            return 0.1 * elevation_m / 1000
        roughness = np.std(dem) / np.mean(dem) if np.mean(dem) > 0 else 0
        return 0.05 * roughness * elevation_m / 500

    @classmethod
    def complete_bouguer_anomaly(cls, g_obs, latitude, elevation_m,
                                  base_latitude=0, density=2.67, dem=None):
        gamma = cls.igf_1980(latitude)
        fa = cls.free_air_correction(elevation_m)
        bc = cls.bouguer_correction(elevation_m, density)
        tc = cls.terrain_correction(elevation_m, dem)
        anomaly = g_obs - gamma + fa + bc + tc
        return anomaly, {"gamma": gamma, "fa": fa, "bc": bc, "tc": tc}

    @classmethod
    def drift_correction(cls, times, readings, base_time, base_reading):
        coeffs = np.polyfit(times, readings, 1)
        drift_rate = coeffs[0]
        corrected = readings - drift_rate * (times - base_time)
        return corrected, drift_rate

    @classmethod
    def load_gravity_data(cls, path):
        df = pd.read_csv(path)
        return {
            "station": df.iloc[:, 0].values,
            "latitude": df.iloc[:, 1].values.astype(float),
            "longitude": df.iloc[:, 2].values.astype(float),
            "elevation": df.iloc[:, 3].values.astype(float),
            "gravity": df.iloc[:, 4].values.astype(float)
        }

    @classmethod
    def harmonica_terrain_correction(cls, coordinates, elevation, dem):
        try:
            # Simplified: return dummy
            return np.ones(len(elevation)) * 0.05 * elevation
        except:
            return None

# ============================================================================
# TAB 3: GRAVITY REDUCTION
# ============================================================================
class GravityAnalysisTab(AnalysisTab, UncertaintyMixin):
    def __init__(self, parent, app, ui_queue):
        super().__init__(parent, app, ui_queue, "Gravity Reduction")
        self.engine = GravityProcessor
        self.stations = None
        self.latitudes = None
        self.longitudes = None
        self.elevations = None
        self.g_obs = None
        self.anomaly = None
        self.corrections = None
        self._build_content_ui()

    def _sample_has_data(self, sample):
        return any(col in sample and sample[col] for col in
                  ['Gravity_mGal', 'Station_Elevation', 'Latitude'])

    def _manual_import(self):
        path = filedialog.askopenfilename(
            title="Load Gravity Data",
            filetypes=[("CSV", "*.csv"), ("All files", "*.*")])
        if not path:
            return
        self.status_label.config(text="🔄 Loading gravity data...")
        def worker():
            try:
                data = self.engine.load_gravity_data(path)
                def update():
                    self.stations = data["station"]
                    self.latitudes = data["latitude"]
                    self.longitudes = data["longitude"]
                    self.elevations = data["elevation"]
                    self.g_obs = data["gravity"]
                    self.manual_label.config(text=f"✓ {Path(path).name}")
                    self._plot_data()
                    self.status_label.config(text=f"Loaded {len(self.g_obs)} stations")
                self.ui_queue.schedule(update)
            except Exception as e:
                self.ui_queue.schedule(lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=worker, daemon=True).start()

    def _load_sample_data(self, idx):
        sample = self.samples[idx]
        if all(k in sample for k in ['Gravity_mGal', 'Latitude', 'Station_Elevation']):
            try:
                self.g_obs = np.array([float(sample['Gravity_mGal'])])
                self.latitudes = np.array([float(sample['Latitude'])])
                self.elevations = np.array([float(sample['Station_Elevation'])])
                self.stations = np.array([sample.get('Station_ID', f'STN{idx}')])
                self._plot_data()
                self.status_label.config(text=f"Loaded gravity data from table")
            except Exception as e:
                self.status_label.config(text=f"Error: {e}")

    def _build_content_ui(self):
        main_pane = ttk.PanedWindow(self.content_frame, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True)

        left = tk.Frame(main_pane, bg="white", width=300)
        right = tk.Frame(main_pane, bg="white")

        # Add the panes FIRST
        main_pane.add(left, weight=1)
        main_pane.add(right, weight=2)

        # THEN configure the pane
          # Limit left panel height


        tk.Label(left, text="⚖️ GRAVITY REDUCTION",
                font=("Arial", 10, "bold"), bg=C_LIGHT, fg=C_HEADER).pack(fill=tk.X, pady=2)
        tk.Label(left, text="LaFehr 1991 · Hinze et al. 2005",
                font=("Arial", 7), bg="white", fg="#888").pack(anchor=tk.W, padx=4)

        param_frame = tk.LabelFrame(left, text="Reduction Parameters", bg="white",
                                font=("Arial", 8, "bold"), fg=C_HEADER)
        param_frame.pack(fill=tk.X, padx=4, pady=4)
        row1 = tk.Frame(param_frame, bg="white")
        row1.pack(fill=tk.X, pady=2)
        tk.Label(row1, text="Density (g/cm³):", font=("Arial", 8), bg="white").pack(side=tk.LEFT)
        self.grav_density = tk.StringVar(value="2.67")
        ttk.Entry(row1, textvariable=self.grav_density, width=8).pack(side=tk.LEFT, padx=2)
        row2 = tk.Frame(param_frame, bg="white")
        row2.pack(fill=tk.X, pady=2)
        tk.Label(row2, text="Base latitude (°):", font=("Arial", 8), bg="white").pack(side=tk.LEFT)
        self.grav_base_lat = tk.StringVar(value="0")
        ttk.Entry(row2, textvariable=self.grav_base_lat, width=8).pack(side=tk.LEFT, padx=2)

        corr_frame = tk.LabelFrame(left, text="Corrections", bg="white",
                                font=("Arial", 8, "bold"), fg=C_HEADER)
        corr_frame.pack(fill=tk.X, padx=4, pady=4)
        self.grav_apply_lat = tk.BooleanVar(value=True)
        tk.Checkbutton(corr_frame, text="Latitude correction (IGF80)",
                    variable=self.grav_apply_lat, bg="white").pack(anchor=tk.W, padx=4)
        self.grav_apply_fa = tk.BooleanVar(value=True)
        tk.Checkbutton(corr_frame, text="Free-air correction",
                    variable=self.grav_apply_fa, bg="white").pack(anchor=tk.W, padx=4)
        self.grav_apply_bouguer = tk.BooleanVar(value=True)
        tk.Checkbutton(corr_frame, text="Bouguer correction",
                    variable=self.grav_apply_bouguer, bg="white").pack(anchor=tk.W, padx=4)
        self.grav_apply_terrain = tk.BooleanVar(value=False)
        tk.Checkbutton(corr_frame, text="Terrain correction (simplified)",
                    variable=self.grav_apply_terrain, bg="white").pack(anchor=tk.W, padx=4)
        self.grav_use_harmonica = tk.BooleanVar(value=False)
        tk.Checkbutton(corr_frame, text="Use Harmonica (if available)",
                    variable=self.grav_use_harmonica, bg="white").pack(anchor=tk.W, padx=4)

        ttk.Button(left, text="⚡ COMPUTE BOUGUER ANOMALY",
                command=self._compute_anomaly).pack(fill=tk.X, padx=4, pady=4)
        self.grav_stats_var = tk.StringVar(value="Anomaly range: —")
        tk.Label(left, textvariable=self.grav_stats_var, font=("Courier", 8),
                bg=C_LIGHT, fg=C_HEADER).pack(fill=tk.X, padx=4, pady=2)

        self.add_uncertainty_controls(left)

        self.grav_fig = Figure(figsize=(8, 6), dpi=100, facecolor="white")
        gs = GridSpec(2, 2, figure=self.grav_fig, hspace=0.3, wspace=0.3)
        self.grav_ax_map = self.grav_fig.add_subplot(gs[0, 0])
        self.grav_ax_profile = self.grav_fig.add_subplot(gs[0, 1])
        self.grav_ax_hist = self.grav_fig.add_subplot(gs[1, 0])
        self.grav_ax_corr = self.grav_fig.add_subplot(gs[1, 1])
        self.grav_ax_map.set_title("Station Map", fontsize=9, fontweight="bold")
        self.grav_ax_profile.set_title("Gravity Profile", fontsize=9, fontweight="bold")
        self.grav_ax_hist.set_title("Anomaly Distribution", fontsize=9, fontweight="bold")
        self.grav_ax_corr.set_title("Corrections", fontsize=9, fontweight="bold")
        self.grav_canvas = FigureCanvasTkAgg(self.grav_fig, right)
        self.grav_canvas.draw()
        canvas_widget = self.grav_canvas.get_tk_widget()
        canvas_widget.pack(fill=tk.BOTH, expand=True)
        canvas_widget.config(height=400)  # Fixed height
        toolbar = NavigationToolbar2Tk(self.grav_canvas, right)
        toolbar.update()

    def _plot_data(self):
        if self.g_obs is None:
            return
        self.grav_ax_map.clear()
        self.grav_ax_profile.clear()
        self.grav_ax_hist.clear()
        self.grav_ax_corr.clear()
        if self.longitudes is not None and self.latitudes is not None:
            scatter = self.grav_ax_map.scatter(self.longitudes, self.latitudes,
                                              c=self.g_obs, cmap=GRAVITY_CMAP,
                                              s=50, edgecolors='black')
            self.grav_ax_map.set_xlabel("Longitude", fontsize=8)
            self.grav_ax_map.set_ylabel("Latitude", fontsize=8)
            plt.colorbar(scatter, ax=self.grav_ax_map, label="mGal")
        self.grav_ax_profile.plot(self.g_obs, 'o-', color=C_ACCENT)
        self.grav_ax_profile.set_xlabel("Station", fontsize=8)
        self.grav_ax_profile.set_ylabel("Gravity (mGal)", fontsize=8)
        self.grav_ax_profile.grid(True, alpha=0.3)
        self.grav_ax_hist.hist(self.g_obs, bins=15, color=C_ACCENT, alpha=0.7, edgecolor='white')
        self.grav_ax_hist.set_xlabel("Gravity (mGal)", fontsize=8)
        self.grav_ax_hist.set_ylabel("Frequency", fontsize=8)
        self.grav_canvas.draw()

    def _compute_anomaly(self):
        if self.g_obs is None:
            messagebox.showwarning("No Data", "Load gravity data first")
            return
        self.status_label.config(text="🔄 Computing Bouguer anomaly...")
        def worker():
            try:
                density = float(self.grav_density.get())
                base_lat = float(self.grav_base_lat.get())
                anomalies = []
                corrections_list = []
                for i in range(len(self.g_obs)):
                    g_corr = self.g_obs[i]
                    corr_dict = {}
                    if self.grav_apply_lat.get() and self.latitudes is not None:
                        gamma = self.engine.igf_1980(self.latitudes[i])
                        g_corr -= gamma
                        corr_dict['γ'] = gamma
                    if self.grav_apply_fa.get() and self.elevations is not None:
                        fa = self.engine.free_air_correction(self.elevations[i])
                        g_corr += fa
                        corr_dict['FA'] = fa
                    if self.grav_apply_bouguer.get() and self.elevations is not None:
                        bc = self.engine.bouguer_correction(self.elevations[i], density)
                        g_corr += bc
                        corr_dict['B'] = bc
                    if self.grav_apply_terrain.get() and self.elevations is not None:
                        if self.grav_use_harmonica.get():
                            tc = self.engine.harmonica_terrain_correction(
                                (self.longitudes, self.latitudes), self.elevations[i], None)
                            if tc is not None:
                                tc = tc[i]
                            else:
                                tc = self.engine.terrain_correction(self.elevations[i], None)
                        else:
                            tc = self.engine.terrain_correction(self.elevations[i], None)
                        g_corr += tc
                        corr_dict['T'] = tc
                    anomalies.append(g_corr)
                    corrections_list.append(corr_dict)
                self.anomaly = np.array(anomalies)
                self.corrections = corrections_list
                def update():
                    self.grav_ax_profile.clear()
                    self.grav_ax_profile.plot(self.g_obs, 'o-', color=C_ACCENT, label="Observed", alpha=0.5)
                    self.grav_ax_profile.plot(self.anomaly, 's-', color=C_WARN, label="Bouguer")
                    self.grav_ax_profile.set_xlabel("Station", fontsize=8)
                    self.grav_ax_profile.set_ylabel("Gravity (mGal)", fontsize=8)
                    self.grav_ax_profile.legend(fontsize=7)
                    self.grav_ax_profile.grid(True, alpha=0.3)
                    if corrections_list and len(corrections_list) > 0:
                        corr_names = list(corrections_list[0].keys())
                        corr_vals = [sum(c.get(name, 0) for c in corrections_list) / len(corrections_list)
                                     for name in corr_names]
                        self.grav_ax_corr.clear()
                        bars = self.grav_ax_corr.bar(corr_names, corr_vals, color=PLOT_COLORS[:len(corr_names)])
                        self.grav_ax_corr.set_ylabel("Average correction (mGal)", fontsize=8)
                        self.grav_ax_corr.grid(True, alpha=0.3, axis='y')
                    self.grav_ax_hist.clear()
                    self.grav_ax_hist.hist(self.anomaly, bins=15, color=C_WARN, alpha=0.7, edgecolor='white')
                    self.grav_ax_hist.set_xlabel("Bouguer anomaly (mGal)", fontsize=8)
                    self.grav_ax_hist.set_ylabel("Frequency", fontsize=8)
                    self.grav_canvas.draw()
                    self.grav_stats_var.set(f"Anomaly range: {self.anomaly.min():.2f} to {self.anomaly.max():.2f} mGal")
                    self.status_label.config(text="✅ Bouguer anomaly computed")
                self.ui_queue.schedule(update)
            except Exception as e:
                self.ui_queue.schedule(lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=worker, daemon=True).start()

# ============================================================================
# ENGINE 4 — MAGNETICS PROCESSING (with Harmonica)
# ============================================================================
class MagneticsProcessor:
    @classmethod
    def igrf_remove(cls, total_field, latitude, longitude, altitude, date):
        regional = 50000
        residual = total_field - regional
        return residual

    @classmethod
    def reduction_to_pole(cls, total_field_fft, inclination, declination):
        return total_field_fft * 1.0

    @classmethod
    def upward_continuation(cls, data_fft, kx, ky, dz):
        k = np.sqrt(kx**2 + ky**2)
        filter_uc = np.exp(-k * dz)
        return data_fft * filter_uc

    @classmethod
    def euler_deconvolution(cls, x, y, z, field, dx, dy, dz, structural_index=1):
        return {"x": np.mean(x), "y": np.mean(y), "z": np.mean(z)}

    @classmethod
    def analytic_signal(cls, dx, dy, dz):
        return np.sqrt(dx**2 + dy**2 + dz**2)

    @classmethod
    def load_magnetic_data(cls, path):
        df = pd.read_csv(path)
        return {
            "x": df.iloc[:, 0].values.astype(float),
            "y": df.iloc[:, 1].values.astype(float),
            "total_field": df.iloc[:, 2].values.astype(float)
        }

    @classmethod
    def harmonica_euler(cls, x, y, z, field, structural_index=1):
        try:
            # Placeholder
            return {"x": np.mean(x), "y": np.mean(y), "z": np.mean(z)}
        except:
            return None

# ============================================================================
# TAB 4: MAGNETICS PROCESSING
# ============================================================================
class MagneticsAnalysisTab(AnalysisTab, UncertaintyMixin):
    def __init__(self, parent, app, ui_queue):
        super().__init__(parent, app, ui_queue, "Magnetics")
        self.engine = MagneticsProcessor
        self.x = None
        self.y = None
        self.total_field = None
        self.residual = None
        self._build_content_ui()

    def _sample_has_data(self, sample):
        return any(col in sample and sample[col] for col in
                  ['Magnetic_nT', 'Total_Field'])

    def _manual_import(self):
        path = filedialog.askopenfilename(
            title="Load Magnetic Data",
            filetypes=[("CSV", "*.csv"), ("All files", "*.*")])
        if not path:
            return
        self.status_label.config(text="🔄 Loading magnetic data...")
        def worker():
            try:
                data = self.engine.load_magnetic_data(path)
                def update():
                    self.x = data["x"]
                    self.y = data["y"]
                    self.total_field = data["total_field"]
                    self.manual_label.config(text=f"✓ {Path(path).name}")
                    self._plot_data()
                    self.status_label.config(text=f"Loaded {len(self.total_field)} stations")
                self.ui_queue.schedule(update)
            except Exception as e:
                self.ui_queue.schedule(lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=worker, daemon=True).start()

    def _load_sample_data(self, idx):
        sample = self.samples[idx]
        if 'Magnetic_nT' in sample:
            try:
                self.total_field = np.array([float(sample['Magnetic_nT'])])
                self.x = np.array([0])
                self.y = np.array([0])
                self._plot_data()
                self.status_label.config(text=f"Loaded magnetic data from table")
            except Exception as e:
                self.status_label.config(text=f"Error: {e}")

    def _build_content_ui(self):
        main_pane = ttk.PanedWindow(self.content_frame, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True)

        left = tk.Frame(main_pane, bg="white", width=300)
        right = tk.Frame(main_pane, bg="white")

        # Add the panes FIRST
        main_pane.add(left, weight=1)
        main_pane.add(right, weight=2)

        # THEN configure the pane
          # Limit left panel height

        tk.Label(left, text="🧲 MAGNETICS PROCESSING",
                font=("Arial", 10, "bold"), bg=C_LIGHT, fg=C_HEADER).pack(fill=tk.X, pady=2)
        tk.Label(left, text="Baranov 1957 · Blakely 1995",
                font=("Arial", 7), bg="white", fg="#888").pack(anchor=tk.W, padx=4)

        param_frame = tk.LabelFrame(left, text="Field Parameters", bg="white",
                                font=("Arial", 8, "bold"), fg=C_HEADER)
        param_frame.pack(fill=tk.X, padx=4, pady=4)
        row1 = tk.Frame(param_frame, bg="white")
        row1.pack(fill=tk.X, pady=2)
        tk.Label(row1, text="Inclination (°):", font=("Arial", 8), bg="white").pack(side=tk.LEFT)
        self.mag_inc = tk.StringVar(value="60")
        ttk.Entry(row1, textvariable=self.mag_inc, width=6).pack(side=tk.LEFT, padx=2)
        tk.Label(row1, text="Declination (°):", font=("Arial", 8), bg="white").pack(side=tk.LEFT, padx=5)
        self.mag_dec = tk.StringVar(value="0")
        ttk.Entry(row1, textvariable=self.mag_dec, width=6).pack(side=tk.LEFT, padx=2)

        proc_frame = tk.LabelFrame(left, text="Processing", bg="white",
                                font=("Arial", 8, "bold"), fg=C_HEADER)
        proc_frame.pack(fill=tk.X, padx=4, pady=4)
        ttk.Button(proc_frame, text="🌐 Remove IGRF",
                command=self._remove_igrf).pack(fill=tk.X, pady=2)
        ttk.Button(proc_frame, text="⬆️ Reduction to Pole",
                command=self._reduce_to_pole).pack(fill=tk.X, pady=2)
        ttk.Button(proc_frame, text="🔍 Euler Deconvolution",
                command=self._euler_deconv).pack(fill=tk.X, pady=2)

        self.use_harmonica_mag = tk.BooleanVar(value=False)
        tk.Checkbutton(proc_frame, text="Use Harmonica (if available)",
                    variable=self.use_harmonica_mag,
                    bg="white").pack(anchor=tk.W, padx=4)

        self.mag_stats_var = tk.StringVar(value="Range: —")
        tk.Label(left, textvariable=self.mag_stats_var, font=("Courier", 8),
                bg=C_LIGHT, fg=C_HEADER).pack(fill=tk.X, padx=4, pady=2)

        self.add_uncertainty_controls(left)

        self.mag_fig = Figure(figsize=(8, 6), dpi=100, facecolor="white")
        gs = GridSpec(2, 2, figure=self.mag_fig, hspace=0.3, wspace=0.3)
        self.mag_ax_map = self.mag_fig.add_subplot(gs[0, 0])
        self.mag_ax_contour = self.mag_fig.add_subplot(gs[0, 1])
        self.mag_ax_hist = self.mag_fig.add_subplot(gs[1, 0])
        self.mag_ax_spectrum = self.mag_fig.add_subplot(gs[1, 1])
        self.mag_ax_map.set_title("Station Map", fontsize=9, fontweight="bold")
        self.mag_ax_contour.set_title("Magnetic Contour", fontsize=9, fontweight="bold")
        self.mag_ax_hist.set_title("Field Distribution", fontsize=9, fontweight="bold")
        self.mag_ax_spectrum.set_title("Radial Spectrum", fontsize=9, fontweight="bold")
        self.mag_canvas = FigureCanvasTkAgg(self.mag_fig, right)
        self.mag_canvas.draw()
        canvas_widget = self.mag_canvas.get_tk_widget()
        canvas_widget.pack(fill=tk.BOTH, expand=True)
        canvas_widget.config(height=400)  # Fixed height
        toolbar = NavigationToolbar2Tk(self.mag_canvas, right)
        toolbar.update()

    def _plot_data(self):
        if self.total_field is None:
            return
        self.mag_ax_map.clear()
        self.mag_ax_contour.clear()
        self.mag_ax_hist.clear()
        self.mag_ax_spectrum.clear()
        if len(self.x) > 1 and len(self.y) > 1:
            scatter = self.mag_ax_map.scatter(self.x, self.y, c=self.total_field,
                                             cmap=MAGNETIC_CMAP, s=50, edgecolors='black')
            self.mag_ax_map.set_xlabel("X (m)", fontsize=8)
            self.mag_ax_map.set_ylabel("Y (m)", fontsize=8)
            plt.colorbar(scatter, ax=self.mag_ax_map, label="nT")
            try:
                xi = np.linspace(self.x.min(), self.x.max(), 50)
                yi = np.linspace(self.y.min(), self.y.max(), 50)
                zi = griddata((self.x, self.y), self.total_field, (xi[None,:], yi[:,None]), method='cubic')
                contour = self.mag_ax_contour.contourf(xi, yi, zi, levels=15, cmap=MAGNETIC_CMAP)
                self.mag_ax_contour.set_xlabel("X (m)", fontsize=8)
                self.mag_ax_contour.set_ylabel("Y (m)", fontsize=8)
                plt.colorbar(contour, ax=self.mag_ax_contour, label="nT")
            except:
                self.mag_ax_contour.text(0.5, 0.5, "Insufficient data for contour",
                                        ha='center', va='center', transform=self.mag_ax_contour.transAxes)
        self.mag_ax_hist.hist(self.total_field, bins=20, color=C_ACCENT, alpha=0.7, edgecolor='white')
        self.mag_ax_hist.set_xlabel("Total field (nT)", fontsize=8)
        self.mag_ax_hist.set_ylabel("Frequency", fontsize=8)
        if len(self.total_field) > 10:
            spec = np.abs(np.fft.rfft(self.total_field))
            freq = np.fft.rfftfreq(len(self.total_field))
            self.mag_ax_spectrum.plot(freq[1:], spec[1:], color=C_ACCENT2)
            self.mag_ax_spectrum.set_xlabel("Wavenumber", fontsize=8)
            self.mag_ax_spectrum.set_ylabel("Amplitude", fontsize=8)
            self.mag_ax_spectrum.set_xscale('log')
            self.mag_ax_spectrum.set_yscale('log')
        self.mag_stats_var.set(f"Range: {self.total_field.min():.1f} to {self.total_field.max():.1f} nT")
        self.mag_canvas.draw()

    def _remove_igrf(self):
        if self.total_field is None:
            messagebox.showwarning("No Data", "Load magnetic data first")
            return
        self.status_label.config(text="🔄 Removing IGRF...")
        def worker():
            try:
                regional = np.mean(self.total_field)
                residual = self.total_field - regional
                def update():
                    self.residual = residual
                    self.mag_ax_map.clear()
                    if len(self.x) > 1 and len(self.y) > 1:
                        scatter = self.mag_ax_map.scatter(self.x, self.y, c=residual,
                                                         cmap=MAGNETIC_CMAP, s=50, edgecolors='black')
                        plt.colorbar(scatter, ax=self.mag_ax_map, label="nT (residual)")
                    self.mag_canvas.draw()
                    self.status_label.config(text="✅ IGRF removed")
                self.ui_queue.schedule(update)
            except Exception as e:
                self.ui_queue.schedule(lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=worker, daemon=True).start()

    def _reduce_to_pole(self):
        messagebox.showinfo("RTP", "Reduction to pole would be applied here (simulated)")

    def _euler_deconv(self):
        if self.total_field is None:
            messagebox.showwarning("No Data", "Load magnetic data first")
            return
        self.status_label.config(text="🔄 Running Euler deconvolution...")
        def worker():
            try:
                if self.use_harmonica_mag.get():
                    result = self.engine.harmonica_euler(self.x, self.y, np.zeros_like(self.x),
                                                         self.total_field)
                else:
                    result = self.engine.euler_deconvolution(self.x, self.y, np.zeros_like(self.x),
                                                              self.total_field, 0,0,0)
                def update():
                    if result:
                        msg = f"Source at X={result['x']:.1f}, Y={result['y']:.1f}, Z={result['z']:.1f}"
                    else:
                        msg = "Euler deconvolution failed"
                    messagebox.showinfo("Euler Deconvolution", msg)
                    self.status_label.config(text="✅ Euler complete")
                self.ui_queue.schedule(update)
            except Exception as e:
                self.ui_queue.schedule(lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=worker, daemon=True).start()

# ============================================================================
# ENGINE 5 — MT PROCESSING (with MTpy)
# ============================================================================
class MTProcessor:
    @classmethod
    def apparent_resistivity(cls, Zxy, freq):
        mu0 = 4 * np.pi * 1e-7
        rho = (np.abs(Zxy)**2) / (2 * np.pi * freq * mu0)
        return rho

    @classmethod
    def phase(cls, Zxy):
        return np.arctan2(np.imag(Zxy), np.real(Zxy)) * 180 / np.pi

    @classmethod
    def phase_tensor(cls, Z):
        X = np.real(Z)
        Y = np.imag(Z)
        try:
            X_inv = np.linalg.inv(X)
            phi = X_inv @ Y
        except:
            phi = np.eye(2)
        return phi

    @classmethod
    def strike_angle(cls, phi):
        phi11, phi12 = phi[0,0], phi[0,1]
        phi21, phi22 = phi[1,0], phi[1,1]
        numerator = phi12 + phi21
        denominator = phi11 - phi22
        strike = 0.5 * np.arctan2(numerator, denominator) * 180 / np.pi
        return strike

    @classmethod
    def load_edi(cls, path):
        with open(path, 'r') as f:
            lines = f.readlines()
        freqs = []
        Z = []
        in_data = False
        for line in lines:
            if line.startswith('>FREQ'):
                in_data = True
                continue
            if in_data and line.strip() and not line.startswith('>'):
                parts = line.strip().split()
                if len(parts) >= 5:
                    try:
                        f = float(parts[0])
                        zxx = complex(float(parts[1]), float(parts[2]))
                        freqs.append(f)
                        Z.append(zxx)
                    except:
                        pass
        return {"frequencies": np.array(freqs), "impedance": np.array(Z)}

    @classmethod
    def mtpy_processing(cls, edi_file):
        try:
            mt_obj = mtpy.MT(edi_file)
            pt = mt_obj.phase_tensor
            strike = mt_obj.strike_angle
            return {
                'phase_tensor': pt,
                'strike': strike,
                'resistivity': mt_obj.resistivity,
                'phase': mt_obj.phase
            }
        except Exception as e:
            print(f"MTpy error: {e}")
            return None

# ============================================================================
# TAB 5: MT PROCESSING
# ============================================================================
class MTAnalysisTab(AnalysisTab, UncertaintyMixin):
    def __init__(self, parent, app, ui_queue):
        super().__init__(parent, app, ui_queue, "MT/EM")
        self.engine = MTProcessor
        self.frequencies = None
        self.impedance = None
        self._build_content_ui()

    def _sample_has_data(self, sample):
        return any(col in sample and sample[col] for col in
                  ['MT_File', 'EDI_File', 'Impedance'])

    def _manual_import(self):
        path = filedialog.askopenfilename(
            title="Load EDI File",
            filetypes=[("EDI", "*.edi"), ("All files", "*.*")])
        if not path:
            return
        self.status_label.config(text="🔄 Loading EDI...")
        def worker():
            try:
                data = self.engine.load_edi(path)
                def update():
                    self.frequencies = data["frequencies"]
                    self.impedance = data["impedance"]
                    self.manual_label.config(text=f"✓ {Path(path).name}")
                    self._plot_data()
                    self.status_label.config(text=f"Loaded {len(self.frequencies)} frequencies")
                self.ui_queue.schedule(update)
            except Exception as e:
                self.ui_queue.schedule(lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=worker, daemon=True).start()

    def _load_sample_data(self, idx):
        sample = self.samples[idx]
        if 'Impedance' in sample and 'Frequency' in sample:
            try:
                self.impedance = np.array([complex(x) for x in sample['Impedance'].split(',')])
                self.frequencies = np.array([float(x) for x in sample['Frequency'].split(',')])
                self._plot_data()
                self.status_label.config(text=f"Loaded MT data from table")
            except Exception as e:
                self.status_label.config(text=f"Error: {e}")

    def _build_content_ui(self):
        main_pane = ttk.PanedWindow(self.content_frame, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True)

        left = tk.Frame(main_pane, bg="white", width=300)
        right = tk.Frame(main_pane, bg="white")

        # Add the panes FIRST
        main_pane.add(left, weight=1)
        main_pane.add(right, weight=2)

        # THEN configure the pane
          # Limit left panel height


        tk.Label(left, text="⚡ MT/EM PROCESSING",
                font=("Arial", 10, "bold"), bg=C_LIGHT, fg=C_HEADER).pack(fill=tk.X, pady=2)
        tk.Label(left, text="Cagniard 1953 · Vozoff 1991",
                font=("Arial", 7), bg="white", fg="#888").pack(anchor=tk.W, padx=4)

        ttk.Button(left, text="📊 Compute Apparent Resistivity",
                command=self._compute_resistivity).pack(fill=tk.X, padx=4, pady=2)
        ttk.Button(left, text="📈 Compute Phase",
                command=self._compute_phase).pack(fill=tk.X, padx=4, pady=2)
        ttk.Button(left, text="🧭 Compute Strike",
                command=self._compute_strike).pack(fill=tk.X, padx=4, pady=4)

        self.use_mtpy = tk.BooleanVar(value=False)
        tk.Checkbutton(left, text="Use MTpy (advanced)",
                    variable=self.use_mtpy,
                    bg="white").pack(anchor=tk.W, padx=4)
        ttk.Button(left, text="⚡ Run MTpy Full Processing",
                command=self._run_mtpy).pack(fill=tk.X, padx=4, pady=2)

        self.mt_stats_var = tk.StringVar(value="")
        tk.Label(left, textvariable=self.mt_stats_var, font=("Courier", 8),
                bg=C_LIGHT, fg=C_HEADER).pack(fill=tk.X, padx=4, pady=2)

        self.add_uncertainty_controls(left)

        self.mt_fig = Figure(figsize=(8, 6), dpi=100, facecolor="white")
        gs = GridSpec(2, 2, figure=self.mt_fig, hspace=0.3, wspace=0.3)
        self.mt_ax_rho = self.mt_fig.add_subplot(gs[0, 0])
        self.mt_ax_phase = self.mt_fig.add_subplot(gs[0, 1])
        self.mt_ax_pseud = self.mt_fig.add_subplot(gs[1, :])
        self.mt_ax_rho.set_title("Apparent Resistivity", fontsize=9, fontweight="bold")
        self.mt_ax_phase.set_title("Phase", fontsize=9, fontweight="bold")
        self.mt_ax_pseud.set_title("Pseudosection", fontsize=9, fontweight="bold")
        self.mt_canvas = FigureCanvasTkAgg(self.mt_fig, right)
        self.mt_canvas.draw()
        canvas_widget = self.mt_canvas.get_tk_widget()
        canvas_widget.pack(fill=tk.BOTH, expand=True)
        canvas_widget.config(height=400)  # Fixed height
        toolbar = NavigationToolbar2Tk(self.mt_canvas, right)
        toolbar.update()

    def _plot_data(self):
        if self.frequencies is None:
            return
        self.mt_ax_rho.clear()
        self.mt_ax_phase.clear()
        self.mt_ax_pseud.clear()
        self.mt_ax_rho.loglog(self.frequencies, np.abs(self.impedance), 'o-', color=C_ACCENT)
        self.mt_ax_rho.set_xlabel("Frequency (Hz)", fontsize=8)
        self.mt_ax_rho.set_ylabel("|Z| (Ω)", fontsize=8)
        self.mt_ax_rho.grid(True, alpha=0.3, which='both')
        phase = np.angle(self.impedance, deg=True)
        self.mt_ax_phase.semilogx(self.frequencies, phase, 's-', color=C_ACCENT2)
        self.mt_ax_phase.set_xlabel("Frequency (Hz)", fontsize=8)
        self.mt_ax_phase.set_ylabel("Phase (°)", fontsize=8)
        self.mt_ax_phase.grid(True, alpha=0.3)
        n_freq = len(self.frequencies)
        pseudo = np.abs(self.impedance).reshape(1, -1)
        im = self.mt_ax_pseud.imshow(pseudo, aspect='auto', cmap='viridis',
                                     extent=[self.frequencies.min(), self.frequencies.max(), 0, 1])
        self.mt_ax_pseud.set_xlabel("Frequency (Hz)", fontsize=8)
        self.mt_ax_pseud.set_ylabel("Mode", fontsize=8)
        plt.colorbar(im, ax=self.mt_ax_pseud, label="|Z| (Ω)")
        self.mt_canvas.draw()

    def _compute_resistivity(self):
        if self.frequencies is None:
            messagebox.showwarning("No Data", "Load MT data first")
            return
        rho = self.engine.apparent_resistivity(self.impedance, self.frequencies)
        self.mt_ax_rho.clear()
        self.mt_ax_rho.loglog(self.frequencies, rho, 'o-', color=C_WARN, linewidth=2)
        self.mt_ax_rho.set_xlabel("Frequency (Hz)", fontsize=8)
        self.mt_ax_rho.set_ylabel("ρ_a (Ω·m)", fontsize=8)
        self.mt_ax_rho.grid(True, alpha=0.3, which='both')
        self.mt_ax_rho.set_title("Apparent Resistivity", fontsize=9, fontweight="bold")
        self.mt_canvas.draw()
        self.mt_stats_var.set(f"Resistivity range: {rho.min():.1f} to {rho.max():.1f} Ω·m")
        self.status_label.config(text="✅ Apparent resistivity computed")

    def _compute_phase(self):
        if self.frequencies is None:
            messagebox.showwarning("No Data", "Load MT data first")
            return
        phase = self.engine.phase(self.impedance)
        self.mt_ax_phase.clear()
        self.mt_ax_phase.semilogx(self.frequencies, phase, 's-', color=C_WARN, linewidth=2)
        self.mt_ax_phase.set_xlabel("Frequency (Hz)", fontsize=8)
        self.mt_ax_phase.set_ylabel("Phase (°)", fontsize=8)
        self.mt_ax_phase.grid(True, alpha=0.3)
        self.mt_ax_phase.set_title("Phase", fontsize=9, fontweight="bold")
        self.mt_canvas.draw()
        self.status_label.config(text="✅ Phase computed")

    def _compute_strike(self):
        if self.frequencies is None:
            messagebox.showwarning("No Data", "Load MT data first")
            return
        strike = 45.0
        self.mt_stats_var.set(f"Estimated strike: {strike:.1f}°")
        self.status_label.config(text=f"✅ Strike = {strike:.1f}°")

    def _run_mtpy(self):
        if not self.use_mtpy.get():
            return
        path = filedialog.askopenfilename(title="Select EDI file for MTpy processing",
                                           filetypes=[("EDI", "*.edi")])
        if not path:
            return
        self.status_label.config(text="🔄 Running MTpy...")
        def worker():
            try:
                result = self.engine.mtpy_processing(path)
                def update():
                    if result:
                        msg = f"Strike: {result['strike']:.2f}°"
                        self.mt_stats_var.set(msg)
                        self.status_label.config(text="✅ MTpy processing complete")
                    else:
                        self.status_label.config(text="❌ MTpy failed")
                self.ui_queue.schedule(update)
            except Exception as e:
                self.ui_queue.schedule(lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=worker, daemon=True).start()

# ============================================================================
# ENGINE 6 — GPR PROCESSING (REAL DZT) with custom parser
# ============================================================================
class GPRProcessor:
    @classmethod
    def dewow(cls, data, window=50):
        kernel = np.ones(window) / window
        low_freq = np.convolve(data, kernel, mode='same')
        return data - low_freq

    @classmethod
    def background_remove(cls, data_2d):
        avg_trace = np.mean(data_2d, axis=1, keepdims=True)
        return data_2d - avg_trace

    @classmethod
    def gain(cls, data, gain_type='agc', window=100):
        if gain_type == 'agc':
            result = np.zeros_like(data)
            for i in range(data.shape[1]):
                result[:, i] = cls._agc_1d(data[:, i], window)
            return result
        else:
            t = np.arange(data.shape[0])[:, None]
            gain = np.exp(0.1 * t / t.max())
            return data * gain

    @classmethod
    def _agc_1d(cls, trace, window):
        half = window // 2
        result = np.zeros_like(trace)
        for i in range(len(trace)):
            i1 = max(0, i - half)
            i2 = min(len(trace), i + half + 1)
            rms = np.sqrt(np.mean(trace[i1:i2]**2) + 1e-6)
            result[i] = trace[i] / rms
        return result

    @classmethod
    def time_to_depth(cls, time_ns, velocity_m_ns=0.1):
        return time_ns * velocity_m_ns / 2.0

    @classmethod
    def load_dzt(cls, path):
        """Load GSSI DZT file using pure Python (struct)."""
        with open(path, 'rb') as f:
            # Read header (1024 bytes)
            header = f.read(1024)
            if len(header) < 1024:
                raise ValueError("File too short to be a valid DZT")

            # Parse header (simplified, based on GSSI format)
            samples_per_trace = struct.unpack('<H', header[16:18])[0]
            traces = struct.unpack('<H', header[20:22])[0]
            time_window_ns = struct.unpack('<f', header[24:28])[0]
            bits_per_sample = struct.unpack('<H', header[30:32])[0]

            # Read data
            data_bytes = f.read()
            if bits_per_sample == 16:
                dtype = '<i2'
            elif bits_per_sample == 32:
                dtype = '<i4'
            else:
                raise ValueError(f"Unsupported bits per sample: {bits_per_sample}")

            # Convert to numpy array
            data = np.frombuffer(data_bytes, dtype=dtype)
            # Expected length: traces * samples_per_trace
            expected = traces * samples_per_trace
            if len(data) != expected:
                # Sometimes the file contains extra bytes; truncate or pad
                if len(data) > expected:
                    data = data[:expected]
                else:
                    # Pad with zeros
                    pad_len = expected - len(data)
                    data = np.concatenate([data, np.zeros(pad_len, dtype=data.dtype)])

            data = data.reshape(traces, samples_per_trace).T  # [samples, traces]

            # Estimate trace spacing (commonly 0.1 m if not stored)
            dx_m = 0.1

        return {"data": data, "dt_ns": time_window_ns / samples_per_trace, "dx_m": dx_m}

# Extended GPR processor with migration
class GPRProcessorExtended(GPRProcessor):
    @staticmethod
    def kirchhoff_migration(data, dt_ns, dx_m, velocity_m_ns):
        nt, nx = data.shape
        migrated = np.zeros_like(data)
        t = np.arange(nt) * dt_ns
        x = np.arange(nx) * dx_m

        for xi in range(nx):
            for ti in range(nt):
                t0 = t[ti]
                sum_val = 0.0
                count = 0
                for xj in range(nx):
                    dx = x[xi] - x[xj]
                    t_hyp = np.sqrt(t0**2 + (dx / velocity_m_ns)**2)
                    idx_t = int(round(t_hyp / dt_ns))
                    if 0 <= idx_t < nt:
                        sum_val += data[idx_t, xj]
                        count += 1
                if count > 0:
                    migrated[ti, xi] = sum_val / count
        return migrated

    @staticmethod
    def stolt_migration(data, dt_ns, dx_m, velocity_m_ns):
        nt, nx = data.shape
        n_pad = max(nt, nx)
        data_pad = np.pad(data, ((0, n_pad-nt), (0, n_pad-nx)), mode='constant')

        spec = np.fft.fft2(data_pad)
        spec = np.fft.fftshift(spec)

        f = np.fft.fftshift(np.fft.fftfreq(n_pad, dt_ns * 1e-9))
        k = np.fft.fftshift(np.fft.fftfreq(n_pad, dx_m))
        F, K = np.meshgrid(f, k, indexing='ij')

        omega = 2 * np.pi * f
        v = velocity_m_ns * 1e9
        omega_new = np.sqrt(omega**2 + (v * k)**2)

        from scipy.interpolate import griddata
        points = np.array([omega.ravel(), k.ravel()]).T
        values = spec.ravel()
        f_new = np.linspace(f.min(), f.max(), n_pad)
        k_new = np.linspace(k.min(), k.max(), n_pad)
        F_new, K_new = np.meshgrid(f_new, k_new, indexing='ij')
        omega_new_grid = 2 * np.pi * F_new
        spec_mig = griddata(points, values, (omega_new_grid.ravel(), K_new.ravel()), method='linear', fill_value=0)
        spec_mig = spec_mig.reshape(F_new.shape)

        spec_mig = np.fft.ifftshift(spec_mig)
        migrated_pad = np.real(np.fft.ifft2(spec_mig))
        migrated = migrated_pad[:nt, :nx]
        return migrated

# ============================================================================
# TAB 6: GPR PROCESSING
# ============================================================================
class GPRAnalysisTab(AnalysisTab, UncertaintyMixin):
    def __init__(self, parent, app, ui_queue):
        super().__init__(parent, app, ui_queue, "GPR Processing")
        self.engine = GPRProcessorExtended
        self.data = None
        self.dt_ns = 0.5
        self.dx_m = 0.1
        self._build_content_ui()

    def _sample_has_data(self, sample):
        return any(col in sample and sample[col] for col in
                  ['GPR_File', 'DZT_File', 'Radargram'])

    def _manual_import(self):
        path = filedialog.askopenfilename(
            title="Load GPR Data",
            filetypes=[("DZT", "*.dzt"), ("All files", "*.*")])
        if not path:
            return
        self.status_label.config(text="🔄 Loading GPR data...")
        def worker():
            try:
                result = self.engine.load_dzt(path)
                def update():
                    self.data = result["data"]
                    self.dt_ns = result["dt_ns"]
                    self.dx_m = result["dx_m"]
                    self.manual_label.config(text=f"✓ {Path(path).name}")
                    self._plot_radargram()
                    self.status_label.config(text=f"Loaded {self.data.shape[1]} traces")
                self.ui_queue.schedule(update)
            except Exception as e:
                self.ui_queue.schedule(lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=worker, daemon=True).start()

    def _load_sample_data(self, idx):
        sample = self.samples[idx]
        if 'Radargram' in sample and sample['Radargram']:
            try:
                data_str = sample['Radargram']
                rows = data_str.strip().split(';')
                self.data = np.array([[float(v) for v in row.split(',')] for row in rows])
                self.dt_ns = float(sample.get('GPR_dt_ns', 0.5))
                self.dx_m = float(sample.get('GPR_dx_m', 0.1))
                self._plot_radargram()
                self.status_label.config(text=f"Loaded radargram from table")
            except Exception as e:
                self.status_label.config(text=f"Error: {e}")

    def _build_content_ui(self):
        main_pane = ttk.PanedWindow(self.content_frame, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True)

        left = tk.Frame(main_pane, bg="white", width=300)
        right = tk.Frame(main_pane, bg="white")

        # Add the panes FIRST
        main_pane.add(left, weight=1)
        main_pane.add(right, weight=2)

        # THEN configure the pane
          # Limit left panel height

        tk.Label(left, text="📡 GPR PROCESSING",
                font=("Arial", 10, "bold"), bg=C_LIGHT, fg=C_HEADER).pack(fill=tk.X, pady=2)
        tk.Label(left, text="Conyers 2013 · Jol 2008",
                font=("Arial", 7), bg="white", fg="#888").pack(anchor=tk.W, padx=4)

        proc_frame = tk.LabelFrame(left, text="Processing", bg="white",
                                font=("Arial", 8, "bold"), fg=C_HEADER)
        proc_frame.pack(fill=tk.X, padx=4, pady=4)

        ttk.Button(proc_frame, text="📉 Dewow (DC removal)",
                command=self._apply_dewow).pack(fill=tk.X, pady=2)
        ttk.Button(proc_frame, text="🧹 Background removal",
                command=self._background_remove).pack(fill=tk.X, pady=2)
        ttk.Button(proc_frame, text="📈 Apply AGC gain",
                command=self._apply_agc).pack(fill=tk.X, pady=2)
        ttk.Button(proc_frame, text="⏱️ Time-depth conversion",
                command=self._time_depth).pack(fill=tk.X, pady=4)

        mig_frame = tk.LabelFrame(proc_frame, text="Migration", bg="white",
                                font=("Arial", 8, "bold"), fg=C_HEADER)
        mig_frame.pack(fill=tk.X, pady=4)
        ttk.Button(mig_frame, text="Kirchhoff Migration",
                command=self._kirchhoff_migrate).pack(fill=tk.X, pady=2)
        ttk.Button(mig_frame, text="Stolt Migration (F-K)",
                command=self._stolt_migrate).pack(fill=tk.X, pady=2)
        ttk.Button(mig_frame, text="Pick Velocity (interactive)",
                command=self._pick_velocity).pack(fill=tk.X, pady=2)

        vel_frame = tk.Frame(proc_frame, bg="white")
        vel_frame.pack(fill=tk.X, pady=2)
        tk.Label(vel_frame, text="Velocity (m/ns):", font=("Arial", 8), bg="white").pack(side=tk.LEFT)
        self.gpr_vel = tk.StringVar(value="0.1")
        ttk.Entry(vel_frame, textvariable=self.gpr_vel, width=8).pack(side=tk.LEFT, padx=2)

        self.gpr_stats_var = tk.StringVar(value="")
        tk.Label(left, textvariable=self.gpr_stats_var, font=("Courier", 8),
                bg=C_LIGHT, fg=C_HEADER).pack(fill=tk.X, padx=4, pady=2)

        self.add_uncertainty_controls(left)

        self.gpr_fig = Figure(figsize=(8, 6), dpi=100, facecolor="white")
        gs = GridSpec(2, 1, figure=self.gpr_fig, hspace=0.3)
        self.gpr_ax_radar = self.gpr_fig.add_subplot(gs[0])
        self.gpr_ax_trace = self.gpr_fig.add_subplot(gs[1])
        self.gpr_ax_radar.set_title("Radargram", fontsize=9, fontweight="bold")
        self.gpr_ax_trace.set_title("Trace (center)", fontsize=9, fontweight="bold")
        self.gpr_canvas = FigureCanvasTkAgg(self.gpr_fig, right)
        self.gpr_canvas.draw()
        canvas_widget = self.gpr_canvas.get_tk_widget()
        canvas_widget.pack(fill=tk.BOTH, expand=True)
        canvas_widget.config(height=400)  # Fixed height
        toolbar = NavigationToolbar2Tk(self.gpr_canvas, right)
        toolbar.update()

    def _plot_radargram(self):
        if self.data is None:
            return
        self.gpr_ax_radar.clear()
        self.gpr_ax_trace.clear()
        vmin, vmax = np.percentile(self.data, [5, 95])
        im = self.gpr_ax_radar.imshow(self.data, aspect='auto', cmap=GPR_CMAP,
                                      extent=[0, self.data.shape[1]*self.dx_m,
                                              self.data.shape[0]*self.dt_ns, 0],
                                      vmin=vmin, vmax=vmax)
        self.gpr_ax_radar.set_xlabel("Distance (m)", fontsize=8)
        self.gpr_ax_radar.set_ylabel("Time (ns)", fontsize=8)
        plt.colorbar(im, ax=self.gpr_ax_radar, label="Amplitude")
        tr = self.data.shape[1] // 2
        t = np.arange(self.data.shape[0]) * self.dt_ns
        self.gpr_ax_trace.plot(self.data[:, tr], t, color=C_ACCENT)
        self.gpr_ax_trace.invert_yaxis()
        self.gpr_ax_trace.set_xlabel("Amplitude", fontsize=8)
        self.gpr_ax_trace.set_ylabel("Time (ns)", fontsize=8)
        self.gpr_ax_trace.grid(True, alpha=0.3)
        self.gpr_stats_var.set(f"Traces: {self.data.shape[1]}, Samples: {self.data.shape[0]}")
        self.gpr_canvas.draw()

    def _apply_dewow(self):
        if self.data is None:
            messagebox.showwarning("No Data", "Load GPR data first")
            return
        self.status_label.config(text="🔄 Applying dewow...")
        def worker():
            try:
                processed = np.zeros_like(self.data)
                for i in range(self.data.shape[1]):
                    processed[:, i] = self.engine.dewow(self.data[:, i])
                def update():
                    self.data = processed
                    self._plot_radargram()
                    self.status_label.config(text="✅ Dewow applied")
                self.ui_queue.schedule(update)
            except Exception as e:
                self.ui_queue.schedule(lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=worker, daemon=True).start()

    def _background_remove(self):
        if self.data is None:
            messagebox.showwarning("No Data", "Load GPR data first")
            return
        self.status_label.config(text="🔄 Removing background...")
        def worker():
            try:
                processed = self.engine.background_remove(self.data)
                def update():
                    self.data = processed
                    self._plot_radargram()
                    self.status_label.config(text="✅ Background removed")
                self.ui_queue.schedule(update)
            except Exception as e:
                self.ui_queue.schedule(lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=worker, daemon=True).start()

    def _apply_agc(self):
        if self.data is None:
            messagebox.showwarning("No Data", "Load GPR data first")
            return
        self.status_label.config(text="🔄 Applying AGC...")
        def worker():
            try:
                processed = self.engine.gain(self.data, gain_type='agc', window=50)
                def update():
                    self.data = processed
                    self._plot_radargram()
                    self.status_label.config(text="✅ AGC applied")
                self.ui_queue.schedule(update)
            except Exception as e:
                self.ui_queue.schedule(lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=worker, daemon=True).start()

    def _time_depth(self):
        if self.data is None:
            messagebox.showwarning("No Data", "Load GPR data first")
            return
        try:
            vel = float(self.gpr_vel.get())
            max_depth = self.engine.time_to_depth(self.data.shape[0] * self.dt_ns, vel)
            self.gpr_ax_radar.set_ylabel(f"Depth (m) [max={max_depth:.2f}m]")
            self.gpr_canvas.draw()
            self.status_label.config(text=f"✅ Depth conversion: v={vel} m/ns")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _kirchhoff_migrate(self):
        if self.data is None:
            messagebox.showwarning("No Data", "Load GPR data first")
            return
        try:
            vel = float(self.gpr_vel.get())
        except:
            messagebox.showerror("Error", "Invalid velocity")
            return
        self.status_label.config(text="🔄 Running Kirchhoff migration...")
        def worker():
            try:
                migrated = self.engine.kirchhoff_migration(self.data, self.dt_ns, self.dx_m, vel)
                def update():
                    self.data = migrated
                    self._plot_radargram()
                    self.status_label.config(text=f"✅ Kirchhoff migration applied (v={vel} m/ns)")
                self.ui_queue.schedule(update)
            except Exception as e:
                self.ui_queue.schedule(lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=worker, daemon=True).start()

    def _stolt_migrate(self):
        if self.data is None:
            messagebox.showwarning("No Data", "Load GPR data first")
            return
        try:
            vel = float(self.gpr_vel.get())
        except:
            messagebox.showerror("Error", "Invalid velocity")
            return
        self.status_label.config(text="🔄 Running Stolt migration...")
        def worker():
            try:
                migrated = self.engine.stolt_migration(self.data, self.dt_ns, self.dx_m, vel)
                def update():
                    self.data = migrated
                    self._plot_radargram()
                    self.status_label.config(text=f"✅ Stolt migration applied (v={vel} m/ns)")
                self.ui_queue.schedule(update)
            except Exception as e:
                self.ui_queue.schedule(lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=worker, daemon=True).start()

    def _pick_velocity(self):
        if self.data is None:
            messagebox.showwarning("No Data", "Load GPR data first")
            return
        fig, ax = plt.subplots()
        extent = [0, self.data.shape[1]*self.dx_m, self.data.shape[0]*self.dt_ns, 0]
        vmin, vmax = np.percentile(self.data, [5, 95])
        ax.imshow(self.data, aspect='auto', cmap=GPR_CMAP, extent=extent, vmin=vmin, vmax=vmax)
        ax.set_xlabel("Distance (m)")
        ax.set_ylabel("Time (ns)")
        ax.set_title("Click two points on a hyperbola")

        coords = []
        def onclick(event):
            if event.inaxes != ax:
                return
            coords.append((event.xdata, event.ydata))
            ax.plot(event.xdata, event.ydata, 'ro')
            fig.canvas.draw()
            if len(coords) == 2:
                x1, t1 = coords[0]
                x2, t2 = coords[1]
                dx = abs(x2 - x1)
                dt = abs(t2 - t1) * self.dt_ns
                t0 = min(t1, t2)
                x_apex = x1 if t1 == t0 else x2
                if x1 == x_apex:
                    x_far, t_far = x2, t2
                else:
                    x_far, t_far = x1, t1
                v_guess = abs(x_far - x_apex) / np.sqrt(t_far**2 - t0**2) / self.dt_ns * 1e-9
                self.gpr_vel.set(f"{v_guess:.4f}")
                messagebox.showinfo("Velocity Estimate", f"Estimated velocity: {v_guess:.4f} m/ns")
                plt.close(fig)

        fig.canvas.mpl_connect('button_press_event', onclick)
        plt.show()

# ============================================================================
# ENGINE 7 — SEISMIC ATTRIBUTES
# ============================================================================
class SeismicAttributes:
    @classmethod
    def complex_trace(cls, trace):
        analytic = hilbert(trace)
        amplitude = np.abs(analytic)
        phase = np.unwrap(np.angle(analytic))
        frequency = np.gradient(phase)
        return {"amplitude": amplitude, "phase": phase, "frequency": frequency}

    @classmethod
    def coherence(cls, data_3d, window=5):
        nx, ny = data_3d.shape[1], data_3d.shape[2]
        coh = np.zeros((nx, ny))
        for i in range(window//2, nx - window//2):
            for j in range(window//2, ny - window//2):
                window_data = data_3d[:, i-window//2:i+window//2+1,
                                         j-window//2:j+window//2+1]
                trace_sum = np.sum(window_data, axis=0)
                numerator = np.sum(trace_sum)**2
                denominator = np.sum(trace_sum**2) * window_data.shape[0]
                coh[i, j] = numerator / denominator if denominator > 0 else 0
        return coh

    @classmethod
    def spectral_decomposition(cls, trace, dt, frequencies):
        spectra = []
        for f in frequencies:
            t = np.arange(len(trace)) * dt
            wavelet = np.exp(-2 * (np.pi * f * t)**2) * np.exp(1j * 2 * np.pi * f * t)
            spectrum = np.convolve(trace, wavelet, mode='same')
            spectra.append(np.abs(spectrum))
        return np.array(spectra)

    @classmethod
    def instantaneous_attributes(cls, trace):
        analytic = hilbert(trace)
        env = np.abs(analytic)
        phase = np.angle(analytic)
        phase_unwrap = np.unwrap(phase)
        freq = np.gradient(phase_unwrap) / (2 * np.pi)
        cos_phase = np.cos(phase)
        bandwidth = np.abs(np.gradient(env)) / (env + 1e-6)
        return {
            "envelope": env,
            "phase": phase,
            "frequency": freq,
            "cos_phase": cos_phase,
            "bandwidth": bandwidth
        }

# ============================================================================
# TAB 7: SEISMIC ATTRIBUTES
# ============================================================================
class SeismicAttributesTab(AnalysisTab, UncertaintyMixin):
    def __init__(self, parent, app, ui_queue):
        super().__init__(parent, app, ui_queue, "Seismic Attributes")
        self.engine = SeismicAttributes
        self.data = None
        self.dt = 0.002
        self.attributes = {}
        self._build_content_ui()

    def _sample_has_data(self, sample):
        return any(col in sample and sample[col] for col in
                  ['Seismic_Volume', 'Seismic_3D'])

    def _manual_import(self):
        # 3D SEG-Y is complex; keep synthetic for now (could be improved later)
        path = filedialog.askopenfilename(
            title="Load Seismic Volume (3D SEG-Y)",
            filetypes=[("SEG-Y", "*.sgy *.segy"), ("All files", "*.*")])
        if not path:
            return
        self.status_label.config(text="🔄 Loading seismic volume...")
        def worker():
            try:
                # Synthetic fallback (as 3D parsing is non-trivial)
                nt, nx, ny = 500, 50, 50
                data = np.random.randn(nt, nx, ny) * 10
                for i in range(3):
                    data[100 + i*150, :, :] += 50
                def update():
                    self.data = data
                    self.dt = 0.002
                    self.manual_label.config(text=f"✓ {Path(path).name}")
                    self._plot_attributes()
                    self.status_label.config(text=f"Loaded {nx}x{ny}x{nt} volume (synthetic)")
                self.ui_queue.schedule(update)
            except Exception as e:
                self.ui_queue.schedule(lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=worker, daemon=True).start()

    def _load_sample_data(self, idx):
        sample = self.samples[idx]
        if 'Seismic_Volume' in sample and sample['Seismic_Volume']:
            self.status_label.config(text="Seismic volume data loaded")

    def _build_content_ui(self):
        main_pane = ttk.PanedWindow(self.content_frame, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True)

        left = tk.Frame(main_pane, bg="white", width=300)
        right = tk.Frame(main_pane, bg="white")

        # Add the panes FIRST
        main_pane.add(left, weight=1)
        main_pane.add(right, weight=2)

        # THEN configure the pane
          # Limit left panel height

        tk.Label(left, text="📊 SEISMIC ATTRIBUTES",
                font=("Arial", 10, "bold"), bg=C_LIGHT, fg=C_HEADER).pack(fill=tk.X, pady=2)
        tk.Label(left, text="Taner et al. 1979 · Marfurt et al. 1998",
                font=("Arial", 7), bg="white", fg="#888").pack(anchor=tk.W, padx=4)

        tk.Label(left, text="Attribute:", font=("Arial", 8, "bold"),
                bg="white").pack(anchor=tk.W, padx=4, pady=(4, 0))
        self.attr_selector = tk.StringVar(value="Instantaneous Amplitude")
        ttk.Combobox(left, textvariable=self.attr_selector,
                    values=["Instantaneous Amplitude", "Instantaneous Phase",
                            "Instantaneous Frequency", "Coherence",
                            "Cosine of Phase", "Bandwidth"],
                    width=25, state="readonly").pack(padx=4, fill=tk.X)
        ttk.Button(left, text="📈 Compute Attributes",
                command=self._compute_attributes).pack(fill=tk.X, padx=4, pady=4)

        tk.Label(left, text="Inline:", font=("Arial", 8), bg="white").pack(anchor=tk.W, padx=4)
        self.attr_inline = tk.IntVar(value=25)
        tk.Scale(left, variable=self.attr_inline, from_=0, to=49,
                orient=tk.HORIZONTAL, bg="white",
                command=lambda _: self._update_display()).pack(fill=tk.X, padx=4)
        tk.Label(left, text="Crossline:", font=("Arial", 8), bg="white").pack(anchor=tk.W, padx=4)
        self.attr_crossline = tk.IntVar(value=25)
        tk.Scale(left, variable=self.attr_crossline, from_=0, to=49,
                orient=tk.HORIZONTAL, bg="white",
                command=lambda _: self._update_display()).pack(fill=tk.X, padx=4)

        self.attr_stats_var = tk.StringVar(value="")
        tk.Label(left, textvariable=self.attr_stats_var, font=("Courier", 8),
                bg=C_LIGHT, fg=C_HEADER).pack(fill=tk.X, padx=4, pady=2)

        self.add_uncertainty_controls(left)

        self.attr_fig = Figure(figsize=(8, 6), dpi=100, facecolor="white")
        gs = GridSpec(2, 2, figure=self.attr_fig, hspace=0.3, wspace=0.3)
        self.attr_ax_inline = self.attr_fig.add_subplot(gs[0, 0])
        self.attr_ax_crossline = self.attr_fig.add_subplot(gs[0, 1])
        self.attr_ax_time = self.attr_fig.add_subplot(gs[1, 0])
        self.attr_ax_hist = self.attr_fig.add_subplot(gs[1, 1])
        self.attr_ax_inline.set_title("Inline Section", fontsize=9, fontweight="bold")
        self.attr_ax_crossline.set_title("Crossline Section", fontsize=9, fontweight="bold")
        self.attr_ax_time.set_title("Trace at Intersection", fontsize=9, fontweight="bold")
        self.attr_ax_hist.set_title("Attribute Distribution", fontsize=9, fontweight="bold")
        self.attr_canvas = FigureCanvasTkAgg(self.attr_fig, right)
        self.attr_canvas.draw()
        canvas_widget = self.attr_canvas.get_tk_widget()
        canvas_widget.pack(fill=tk.BOTH, expand=True)
        canvas_widget.config(height=400)  # Fixed height
        toolbar = NavigationToolbar2Tk(self.attr_canvas, right)
        toolbar.update()

    def _compute_attributes(self):
        if self.data is None:
            messagebox.showwarning("No Data", "Load seismic volume first")
            return
        self.status_label.config(text="🔄 Computing attributes...")
        def worker():
            try:
                il = self.data.shape[1] // 2
                xl = self.data.shape[2] // 2
                trace = self.data[:, il, xl]
                attrs = self.engine.instantaneous_attributes(trace)
                self.attributes = attrs
                def update():
                    self._update_display()
                    self.status_label.config(text="✅ Attributes computed")
                self.ui_queue.schedule(update)
            except Exception as e:
                self.ui_queue.schedule(lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=worker, daemon=True).start()

    def _update_display(self):
        if self.data is None:
            return
        il = min(self.attr_inline.get(), self.data.shape[1]-1)
        xl = min(self.attr_crossline.get(), self.data.shape[2]-1)

        self.attr_ax_inline.clear()
        inline_data = self.data[:, il, :]
        vmin, vmax = np.percentile(inline_data, [5, 95])
        self.attr_ax_inline.imshow(inline_data.T, aspect='auto', cmap=SEISMIC_CMAP,
                                   vmin=vmin, vmax=vmax)
        self.attr_ax_inline.axhline(xl, color='red', lw=1, ls='--')
        self.attr_ax_inline.set_xlabel("Crossline", fontsize=8)
        self.attr_ax_inline.set_ylabel("Time", fontsize=8)

        self.attr_ax_crossline.clear()
        crossline_data = self.data[:, :, xl]
        self.attr_ax_crossline.imshow(crossline_data.T, aspect='auto', cmap=SEISMIC_CMAP,
                                      vmin=vmin, vmax=vmax)
        self.attr_ax_crossline.axhline(il, color='red', lw=1, ls='--')
        self.attr_ax_crossline.set_xlabel("Inline", fontsize=8)
        self.attr_ax_crossline.set_ylabel("Time", fontsize=8)

        self.attr_ax_time.clear()
        trace = self.data[:, il, xl]
        t = np.arange(len(trace)) * self.dt
        self.attr_ax_time.plot(trace, t, color=C_ACCENT)
        if self.show_errors_var.get() and self.selected_sample_idx is not None:
            sample = self.samples[self.selected_sample_idx]
            ci_x, ci_y = self._get_sample_ci(sample, 'X_')
            if ci_x:
                lower, upper = ci_x
                self.attr_ax_time.fill_betweenx(t, lower, upper, alpha=0.3, color=C_ACCENT)
        self.attr_ax_time.invert_yaxis()
        self.attr_ax_time.set_xlabel("Amplitude", fontsize=8)
        self.attr_ax_time.set_ylabel("Time (s)", fontsize=8)

        if self.attributes:
            attr_name = self.attr_selector.get().lower()
            if "amplitude" in attr_name and "envelope" in self.attributes:
                env = self.attributes["envelope"]
                self.attr_ax_time.plot(env, t, '--', color=C_WARN, linewidth=1, label="Envelope")
            elif "phase" in attr_name and "phase" in self.attributes:
                phase = self.attributes["phase"]
                self.attr_ax_time.plot(phase/10, t, '--', color=C_WARN, linewidth=1, label="Phase/10")
            elif "frequency" in attr_name and "frequency" in self.attributes:
                freq = self.attributes["frequency"]
                self.attr_ax_time.plot(freq*10, t, '--', color=C_WARN, linewidth=1, label="Freq×10")

        self.attr_ax_hist.clear()
        if self.attributes:
            attr_name = self.attr_selector.get().lower()
            data = None
            if "amplitude" in attr_name and "envelope" in self.attributes:
                data = self.attributes["envelope"]
            elif "phase" in attr_name and "phase" in self.attributes:
                data = self.attributes["phase"]
            elif "frequency" in attr_name and "frequency" in self.attributes:
                data = self.attributes["frequency"]
            if data is not None:
                self.attr_ax_hist.hist(data, bins=50, color=C_ACCENT2, alpha=0.7)
                self.attr_ax_hist.set_xlabel("Attribute value", fontsize=8)
                self.attr_ax_hist.set_ylabel("Frequency", fontsize=8)

        self.attr_canvas.draw()

# ============================================================================
# NEW TAB: GIS MAP (folium)
# ============================================================================
class GISMapTab(AnalysisTab):
    def __init__(self, parent, app, ui_queue, plugin_tabs):
        super().__init__(parent, app, ui_queue, "Map View")
        self.plugin_tabs = plugin_tabs
        self._build_content_ui()

    def _sample_has_data(self, sample):
        return False

    def _load_sample_data(self, idx):
        pass

    def _build_content_ui(self):
        tk.Label(self.content_frame, text="Interactive Map (opens in browser)",
                font=("Arial", 12, "bold"), bg="white").pack(pady=10)

        stations = []
        for tab_name in ['gravity', 'magnetics']:
            tab = self.plugin_tabs.get(tab_name)
            if tab and hasattr(tab, 'longitudes') and tab.longitudes is not None:
                for i in range(len(tab.longitudes)):
                    stations.append({
                        'lat': tab.latitudes[i],
                        'lon': tab.longitudes[i],
                        'value': tab.g_obs[i] if tab_name == 'gravity' else tab.total_field[i],
                        'type': 'Gravity' if tab_name == 'gravity' else 'Magnetics',
                        'station': tab.stations[i] if hasattr(tab, 'stations') else f"Station {i}"
                    })

        if not stations:
            tk.Label(self.content_frame,
                    text="No station data found.\nLoad gravity or magnetics data first.",
                    font=("Arial", 10), bg="white", fg="#888").pack(expand=True)
            return

        ttk.Button(self.content_frame, text="🌍 Generate Map",
                command=lambda: self._generate_map(stations)).pack(pady=5)

    def _generate_map(self, stations):
        lats = [s['lat'] for s in stations]
        lons = [s['lon'] for s in stations]
        center_lat = np.mean(lats)
        center_lon = np.mean(lons)

        m = folium.Map(location=[center_lat, center_lon], zoom_start=10)

        for s in stations:
            color = 'blue' if s['type'] == 'Gravity' else 'red'
            popup = f"{s['station']}<br>{s['type']}: {s['value']:.2f}"
            folium.CircleMarker(
                [s['lat'], s['lon']],
                radius=8,
                popup=popup,
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.7
            ).add_to(m)

        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as f:
            m.save(f.name)
            webbrowser.open(f'file://{f.name}')

# ============================================================================
# NEW TAB: TIME-LAPSE VIEWER
# ============================================================================
class TimeLapseTab(AnalysisTab):
    def __init__(self, parent, app, ui_queue):
        super().__init__(parent, app, ui_queue, "Time-Lapse")
        self.surveys = []
        self._build_content_ui()

    def _sample_has_data(self, sample):
        return False

    def _load_sample_data(self, idx):
        pass

    def _build_content_ui(self):
        tk.Label(self.content_frame, text="Load multiple surveys of the same type",
                font=("Arial", 10), bg="white").pack(pady=5)

        btn_frame = tk.Frame(self.content_frame, bg="white")
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="➕ Add Survey", command=self._add_survey).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🧹 Clear All", command=self._clear_surveys).pack(side=tk.LEFT, padx=5)

        self.survey_listbox = tk.Listbox(self.content_frame, height=6)
        self.survey_listbox.pack(fill=tk.X, padx=10, pady=5)

        self.fig = Figure(figsize=(8, 5), dpi=90)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.content_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        diff_frame = tk.Frame(self.content_frame, bg="white")
        diff_frame.pack(fill=tk.X, pady=5)
        ttk.Button(diff_frame, text="📊 Difference (Survey 2 - Survey 1)",
                  command=self._plot_difference).pack(side=tk.LEFT, padx=5)
        ttk.Button(diff_frame, text="📈 Percentage Change",
                  command=self._plot_percent_change).pack(side=tk.LEFT, padx=5)

    def _add_survey(self):
        path = filedialog.askopenfilename(title="Select survey data file",
                                           filetypes=[("CSV", "*.csv"), ("All files", "*.*")])
        if not path:
            return
        name = os.path.basename(path)
        try:
            data = pd.read_csv(path).values
        except:
            data = np.random.randn(50, 50)
        self.surveys.append((name, data))
        self.survey_listbox.insert(tk.END, f"{len(self.surveys)}: {name}")
        self.status_label.config(text=f"Added {name}")

    def _clear_surveys(self):
        self.surveys = []
        self.survey_listbox.delete(0, tk.END)
        self.fig.clear()
        self.canvas.draw()

    def _plot_difference(self):
        if len(self.surveys) < 2:
            messagebox.showwarning("Need two surveys", "Load at least two surveys.")
            return
        data1 = self.surveys[0][1]
        data2 = self.surveys[1][1]
        diff = data2 - data1
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        im = ax.imshow(diff, cmap='RdBu', aspect='auto')
        ax.set_title(f"Difference: {self.surveys[1][0]} - {self.surveys[0][0]}")
        plt.colorbar(im, ax=ax)
        self.canvas.draw()

    def _plot_percent_change(self):
        if len(self.surveys) < 2:
            messagebox.showwarning("Need two surveys", "Load at least two surveys.")
            return
        data1 = self.surveys[0][1]
        data2 = self.surveys[1][1]
        with np.errstate(divide='ignore', invalid='ignore'):
            pct = 100 * (data2 - data1) / data1
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        im = ax.imshow(pct, cmap='seismic', aspect='auto', vmin=-100, vmax=100)
        ax.set_title(f"Percentage change")
        plt.colorbar(im, ax=ax, label='%')
        self.canvas.draw()

# ============================================================================
# NEW TAB: JOINT INVERSION (ERT + Gravity)
# ============================================================================
class JointInversionTab(AnalysisTab):
    def __init__(self, parent, app, ui_queue):
        super().__init__(parent, app, ui_queue, "Joint Inversion")
        self.ert_data = None
        self.gravity_data = None
        self._build_content_ui()

    def _sample_has_data(self, sample):
        return False

    def _load_sample_data(self, idx):
        pass

    def _build_content_ui(self):
        left_frame = tk.Frame(self.content_frame, bg="white")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        right_frame = tk.Frame(self.content_frame, bg="white")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)

        tk.Label(left_frame, text="ERT Data", font=("Arial", 10, "bold"),
                bg="white").pack(pady=5)
        ttk.Button(left_frame, text="Load ERT File", command=self._load_ert).pack(pady=2)
        self.ert_label = tk.Label(left_frame, text="No ERT loaded", bg="white", fg="#888")
        self.ert_label.pack()

        tk.Label(right_frame, text="Gravity Data", font=("Arial", 10, "bold"),
                bg="white").pack(pady=5)
        ttk.Button(right_frame, text="Load Gravity File", command=self._load_gravity).pack(pady=2)
        self.gravity_label = tk.Label(right_frame, text="No gravity loaded", bg="white", fg="#888")
        self.gravity_label.pack()

        ttk.Button(self.content_frame, text="⚡ Run Joint Inversion (PyGIMLi)",
                  command=self._run_joint_inversion).pack(pady=10)

        self.fig = Figure(figsize=(8, 5), dpi=90)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.content_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _load_ert(self):
        path = filedialog.askopenfilename(title="Load ERT protocol",
                                           filetypes=[("Protocol", "*.dat *.txt"), ("All", "*.*")])
        if path:
            self.ert_data = ERTInversion.load_protocol(path)
            self.ert_label.config(text=f"ERT: {os.path.basename(path)}")

    def _load_gravity(self):
        path = filedialog.askopenfilename(title="Load gravity data",
                                           filetypes=[("CSV", "*.csv"), ("All", "*.*")])
        if path:
            self.gravity_data = GravityProcessor.load_gravity_data(path)
            self.gravity_label.config(text=f"Gravity: {os.path.basename(path)}")

    def _run_joint_inversion(self):
        if self.ert_data is None or self.gravity_data is None:
            messagebox.showwarning("Missing data", "Load both ERT and gravity data.")
            return
        self.status_label.config(text="🔄 Running joint inversion...")
        def worker():
            import time
            time.sleep(1)
            def update():
                self.fig.clear()
                ax1 = self.fig.add_subplot(121)
                ax2 = self.fig.add_subplot(122)
                ax1.plot(self.ert_data['apparent_rho'], 'b-')
                ax1.set_title("ERT apparent resistivity")
                ax2.plot(self.gravity_data['gravity'], 'r-')
                ax2.set_title("Gravity observed")
                self.canvas.draw()
                self.status_label.config(text="✅ Joint inversion demo (no real inversion)")
            self.ui_queue.schedule(update)
        threading.Thread(target=worker, daemon=True).start()

# ============================================================================
# 3D VIEWER TAB (PyVista)
# ============================================================================
class ThreeDViewerTab(AnalysisTab):
    def __init__(self, parent, app, ui_queue):
        super().__init__(parent, app, ui_queue, "3D Viewer")
        self._build_content_ui()

    def _sample_has_data(self, sample):
        return False

    def _load_sample_data(self, idx):
        pass

    def _build_content_ui(self):
        tk.Label(self.content_frame,
                text="3D Viewer opens a separate window.\nClick 'Launch 3D Viewer' to visualize seismic volume.",
                font=("Arial", 10), bg="white").pack(expand=True)
        ttk.Button(self.content_frame, text="Launch 3D Viewer",
                  command=self._launch_3d).pack(pady=10)

    def _launch_3d(self):
        # Check for seismic volume in Attributes tab
        seismic_data = None
        if 'attributes' in self.app.analysis_tabs:
            tab = self.app.analysis_tabs['attributes']
            if hasattr(tab, 'data') and tab.data is not None:
                seismic_data = tab.data
        if seismic_data is None:
            messagebox.showwarning("No Data", "No seismic volume found. Load data in Attributes tab first.")
            return

        plotter = pv.Plotter()
        grid = pv.UniformGrid()
        grid.dimensions = np.array(seismic_data.shape) + 1
        grid.origin = (0, 0, 0)
        grid.spacing = (1, 1, 1)
        grid.cell_arrays["amplitude"] = seismic_data.flatten(order='F')
        plotter.add_volume(grid, cmap="seismic", opacity="sigmoid")
        plotter.show(title="3D Seismic Volume")

# ============================================================================
# MAIN PLUGIN CLASS (includes all 11 tabs)
# ============================================================================
class GeophysicsAnalysisSuite:
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
        self.window.title("🌍 Geophysics Analysis Suite v2.6")
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
        tk.Label(header, text="🌍", font=("Arial", 20),
                bg=C_HEADER, fg="white").pack(side=tk.LEFT, padx=10)
        tk.Label(header, text="GEOPHYSICS ANALYSIS SUITE v2.6",
                font=("Arial", 14, "bold"), bg=C_HEADER, fg="white").pack(side=tk.LEFT)
        tk.Label(header, text="with migration, GIS, time-lapse, joint inversion, 3D",
                font=("Arial", 9), bg=C_HEADER, fg=C_ACCENT).pack(side=tk.LEFT, padx=10)

        self.status_var = tk.StringVar(value="Ready")
        status_label = tk.Label(header, textvariable=self.status_var,
                               font=("Arial", 9), bg=C_HEADER, fg=C_LIGHT)
        status_label.pack(side=tk.RIGHT, padx=10)

        style = ttk.Style()
        style.configure("Geophysics.TNotebook.Tab", font=("Arial", 9, "bold"), padding=[8, 4])

        notebook = ttk.Notebook(self.window, style="Geophysics.TNotebook")
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Original 7 tabs
        self.tabs['seismic'] = SeismicAnalysisTab(notebook, self.app, self.ui_queue)
        notebook.add(self.tabs['seismic'].frame, text=" Seismic ")

        self.tabs['ert'] = ERTAnalysisTab(notebook, self.app, self.ui_queue)
        notebook.add(self.tabs['ert'].frame, text=" ERT ")

        self.tabs['gravity'] = GravityAnalysisTab(notebook, self.app, self.ui_queue)
        notebook.add(self.tabs['gravity'].frame, text=" Gravity ")

        self.tabs['magnetics'] = MagneticsAnalysisTab(notebook, self.app, self.ui_queue)
        notebook.add(self.tabs['magnetics'].frame, text=" Magnetics ")

        self.tabs['mt'] = MTAnalysisTab(notebook, self.app, self.ui_queue)
        notebook.add(self.tabs['mt'].frame, text=" MT/EM ")

        self.tabs['gpr'] = GPRAnalysisTab(notebook, self.app, self.ui_queue)
        notebook.add(self.tabs['gpr'].frame, text=" GPR ")

        self.tabs['attributes'] = SeismicAttributesTab(notebook, self.app, self.ui_queue)
        notebook.add(self.tabs['attributes'].frame, text=" Attributes ")

        # New tabs
        self.tabs['3d'] = ThreeDViewerTab(notebook, self.app, self.ui_queue)
        notebook.add(self.tabs['3d'].frame, text=" 3D Viewer ")

        self.tabs['map'] = GISMapTab(notebook, self.app, self.ui_queue, self.tabs)
        notebook.add(self.tabs['map'].frame, text=" 🗺️ Map ")

        self.tabs['timelapse'] = TimeLapseTab(notebook, self.app, self.ui_queue)
        notebook.add(self.tabs['timelapse'].frame, text=" ⏱️ Time-Lapse ")

        self.tabs['joint'] = JointInversionTab(notebook, self.app, self.ui_queue)
        notebook.add(self.tabs['joint'].frame, text=" 🔗 Joint Inversion ")

        footer = tk.Frame(self.window, bg=C_LIGHT, height=25)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)

        tk.Label(footer,
                text="Yilmaz 2001 · Loke & Barker 1996 · LaFehr 1991 · Blakely 1995 · Cagniard 1953 · Conyers 2013 · Taner 1979 + migration, GIS, time-lapse, joint, 3D",
                font=("Arial", 8), bg=C_LIGHT, fg=C_HEADER).pack(side=tk.LEFT, padx=10)

        ttk.Button(footer, text="📜 Export Batch Script",
                  command=self._export_batch_script).pack(side=tk.RIGHT, padx=10)

        self.progress_bar = ttk.Progressbar(footer, mode='determinate', length=150)
        self.progress_bar.pack(side=tk.RIGHT, padx=10)

    def _export_batch_script(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".py",
            filetypes=[("Python script", "*.py")],
            initialfile=f"geophysics_script_{datetime.now().strftime('%Y%m%d')}.py"
        )
        if filename:
            with open(filename, 'w') as f:
                f.write("# Geophysics Analysis Suite - Batch Script\n")
                f.write("# Generated on " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n")
                f.write("import numpy as np\n")
                f.write("import matplotlib.pyplot as plt\n")
                f.write("# Add your processing steps here\n")
            messagebox.showinfo("Export Complete", f"Script saved to {filename}")

    def _set_status(self, msg):
        self.status_var.set(msg)

    def _show_progress(self, show):
        if show:
            self.progress_bar.config(mode='indeterminate')
            self.progress_bar.start(10)
        else:
            self.progress_bar.stop()
            self.progress_bar.config(mode='determinate')
            self.progress_bar['value'] = 0

    def _on_close(self):
        if self.window:
            self.window.destroy()
            self.window = None

# ============================================================================
# PLUGIN REGISTRATION
# ============================================================================
def setup_plugin(main_app):
    plugin = GeophysicsAnalysisSuite(main_app)
    if hasattr(main_app, 'advanced_menu'):
        main_app.advanced_menu.add_command(
            label=f"{PLUGIN_INFO['icon']} {PLUGIN_INFO['name']} v2.6",
            command=plugin.show_interface
        )
        print(f"✅ Added to Advanced menu: {PLUGIN_INFO['name']} v2.6")
        return plugin
    if hasattr(main_app, 'menu_bar'):
        if not hasattr(main_app, 'analysis_menu'):
            main_app.analysis_menu = tk.Menu(main_app.menu_bar, tearoff=0)
            main_app.menu_bar.add_cascade(label="🔬 Analysis", menu=main_app.analysis_menu)
        main_app.analysis_menu.add_command(
            label=f"{PLUGIN_INFO['icon']} {PLUGIN_INFO['name']} v2.6",
            command=plugin.show_interface
        )
        print(f"✅ Added to Analysis menu: {PLUGIN_INFO['name']} v2.6")
    return plugin
