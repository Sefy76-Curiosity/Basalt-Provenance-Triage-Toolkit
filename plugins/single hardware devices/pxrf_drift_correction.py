"""
pXRF Drift Correction Plugin for Basalt Provenance Toolkit v10.2+
TIME-SERIES CORRECTION - QC STANDARD TRACKING - INSTRUMENT DRIFT MODELING
Because your pXRF isn't stable and pretending it is doesn't help anyone.

Author: Sefy Levy
License: CC BY-NC-SA 4.0
Version: 1.0 - The one everyone's been asking for
"""

PLUGIN_INFO = {
    "category": "hardware",  # ← This is HARDWARE integration!
    "id": "pxrf_drift_correction",
    "name": "pXRF Drift Corrector",
    "icon": "📉",
    "description": "Track QC standards, model instrument drift, correct time-series data - because pXRF isn't stable!",
    "version": "1.0",
    "requires": ["numpy", "scipy", "pandas", "matplotlib"],
    "author": "Sefy Levy"
}

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os
import sys
from pathlib import Path

try:
    from scipy import stats
    from scipy.optimize import curve_fit
    from scipy.signal import savgol_filter
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    import matplotlib.dates as mdates
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


class PXRFDriftCorrectionPlugin:
    """
    ============================================================================
    pXRF DRIFT CORRECTION v1.0
    ============================================================================

    THE PROBLEM:
    ────────────────────────────────────────────────────────────────────────────
    pXRF instruments DRIFT over time:
    • Tube aging → decreasing intensity
    • Temperature changes → gain drift
    • Detector degradation → resolution loss
    • Count time variations → precision changes

    If you ran samples over 3 days, Day 1 and Day 3 are NOT directly comparable.

    THE SOLUTION:
    ────────────────────────────────────────────────────────────────────────────
    1. Track QC standards throughout your run
    2. Model the drift as a function of time
    3. Apply correction factor to all samples
    4. Validate with post-correction QC

    OUTPUTS:
    ────────────────────────────────────────────────────────────────────────────
    ✓ Drift-corrected concentrations (ppm)
    ✓ Correction factors per element
    ✓ Diagnostic plots (before/after)
    ✓ QC recovery percentages
    ✓ Exported clean dataset with "_drift_corrected" suffix
    ============================================================================
    """

    # Known reference standards and their certified values
    CERTIFIED_REFERENCE_MATERIALS = {
        "NIST 2710a": {
            "name": "Montana Soil (Highly Elevated)",
            "Zr": 324, "Nb": 19, "Pb": 5532, "Zn": 2952, "Cu": 3420,
            "Fe": 3.92, "Mn": 1.53, "As": 1540, "Cd": 101.1,
            "source": "NIST SRM 2710a",
            "certified": "2018"
        },
        "NIST 2780": {
            "name": "Hard Rock Mine Waste",
            "Zr": 230, "Nb": 14, "Pb": 208, "Zn": 238, "Cu": 114,
            "Fe": 4.16, "Mn": 0.17, "As": 57, "Cd": 1.2,
            "source": "NIST SRM 2780",
            "certified": "2019"
        },
        "NIST 2709a": {
            "name": "San Joaquin Soil",
            "Zr": 160, "Nb": 11, "Pb": 18.9, "Zn": 106, "Cu": 33.9,
            "Fe": 3.36, "Mn": 0.53, "As": 11.3, "Cd": 0.45,
            "source": "NIST SRM 2709a",
            "certified": "2018"
        },
        "BHVO-2": {
            "name": "Hawaiian Basalt",
            "Zr": 172, "Nb": 18, "Ba": 130, "Rb": 9.8, "Sr": 389,
            "Cr": 280, "Ni": 120, "Fe": 8.63, "Ti": 1.63,
            "source": "USGS BHVO-2",
            "certified": "2017"
        },
        "BCR-2": {
            "name": "Columbia River Basalt",
            "Zr": 188, "Nb": 12.5, "Ba": 683, "Rb": 47, "Sr": 346,
            "Cr": 16, "Ni": 13, "Fe": 9.65, "Ti": 1.35,
            "source": "USGS BCR-2",
            "certified": "2016"
        },
        "AGV-2": {
            "name": "Andesite",
            "Zr": 230, "Nb": 15, "Ba": 1130, "Rb": 68.6, "Sr": 662,
            "Cr": 13, "Ni": 19, "Fe": 4.72, "Ti": 0.63,
            "source": "USGS AGV-2",
            "certified": "2016"
        }
    }

    def __init__(self, main_app):
        self.app = main_app
        self.window = None

        # Drift correction data
        self.raw_data = None
        self.qc_data = None
        self.sample_data = None
        self.drift_models = {}  # element -> model function
        self.correction_factors = {}  # element -> {time: factor}
        self.corrected_data = None

        # QC tracking
        self.detected_standards = []  # auto-detected QC samples
        self.selected_standard = None
        self.certified_values = None

        # UI elements
        self.notebook = None
        self.status_indicator = None
        self.stats_label = None
        self.qc_tree = None
        self.plot_frame = None
        self.results_text = None

    def open_window(self):
        """Open the pXRF drift correction window"""
        if not HAS_SCIPY:
            messagebox.showerror(
                "Missing Dependency",
                "pXRF Drift Correction requires scipy:\n\n"
                "pip install scipy"
            )
            return

        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        # WIDE DESIGN - 1300x800 (need space for plots)
        self.window = tk.Toplevel(self.app.root)
        self.window.title("📉 pXRF Drift Corrector v1.0")
        self.window.geometry("1300x800")
        self.window.transient(self.app.root)

        self._create_interface()
        self.window.lift()
        self.window.focus_force()

    def _create_interface(self):
        """Create the drift correction interface"""

        # ============ TOP BANNER ============
        header = tk.Frame(self.window, bg="#c0392b", height=50)  # Red = warning/instrument
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="📉", font=("Arial", 20),
                bg="#c0392b", fg="white").pack(side=tk.LEFT, padx=10)

        tk.Label(header, text="pXRF Drift Corrector",
                font=("Arial", 16, "bold"), bg="#c0392b", fg="white").pack(side=tk.LEFT, padx=5)

        tk.Label(header, text="Time-series correction • QC tracking • Instrument drift modeling",
                font=("Arial", 9), bg="#c0392b", fg="#f39c12").pack(side=tk.LEFT, padx=15)

        self.status_indicator = tk.Label(header, text="● READY",
                                        font=("Arial", 9, "bold"),
                                        bg="#c0392b", fg="#2ecc71")
        self.status_indicator.pack(side=tk.RIGHT, padx=15)

        # ============ MAIN NOTEBOOK ============
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ============ TAB 1: DATA IMPORT & QC DETECTION ============
        self._create_import_tab()

        # ============ TAB 2: DRIFT MODELING ============
        self._create_modeling_tab()

        # ============ TAB 3: CORRECTION & EXPORT ============
        self._create_correction_tab()

        # ============ TAB 4: HELP & DOCS ============
        self._create_help_tab()

        # ============ BOTTOM STATUS BAR ============
        status_bar = tk.Frame(self.window, bg="#ecf0f1", height=35)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        status_bar.pack_propagate(False)

        self.stats_label = tk.Label(status_bar,
                                   text="Ready - Import pXRF time-series data to begin",
                                   font=("Arial", 9),
                                   bg="#ecf0f1", fg="#2c3e50")
        self.stats_label.pack(side=tk.LEFT, padx=10)

        # Quick status indicators
        self.data_status_label = tk.Label(status_bar, text="📊 No data loaded",
                                         font=("Arial", 8, "bold"),
                                         bg="#ecf0f1", fg="#e74c3c")
        self.data_status_label.pack(side=tk.RIGHT, padx=15)

        self.qc_status_label = tk.Label(status_bar, text="🔬 No QC detected",
                                       font=("Arial", 8, "bold"),
                                       bg="#ecf0f1", fg="#e74c3c")
        self.qc_status_label.pack(side=tk.RIGHT, padx=15)

    def _create_import_tab(self):
        """Tab 1: Import data and auto-detect QC standards"""
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="📂 1. IMPORT & QC DETECTION")

        # Split into left/right
        paned = tk.PanedWindow(tab, orient=tk.HORIZONTAL, sashwidth=6)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ============ LEFT PANEL - IMPORT CONTROLS ============
        left = tk.Frame(paned, bg="#f8f9fa", relief=tk.RAISED, borderwidth=1)
        paned.add(left, width=400)

        # Import section
        import_frame = tk.LabelFrame(left, text="📤 IMPORT TIME-SERIES DATA",
                                    font=("Arial", 10, "bold"),
                                    bg="#f8f9fa", padx=10, pady=10)
        import_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(import_frame,
                text="Import your pXRF run data with timestamps:",
                font=("Arial", 9), bg="#f8f9fa", wraplength=350,
                justify=tk.LEFT).pack(anchor=tk.W, pady=5)

        # Format requirements
        format_frame = tk.Frame(import_frame, bg="#e9ecef", relief=tk.GROOVE, borderwidth=1)
        format_frame.pack(fill=tk.X, pady=10)

        tk.Label(format_frame, text="✅ REQUIRED COLUMNS:",
                font=("Arial", 8, "bold"), bg="#e9ecef").pack(anchor=tk.W, padx=5, pady=2)
        tk.Label(format_frame, text="• Timestamp (datetime)\n• Sample_ID\n• Element columns (Zr_ppm, etc.)",
                font=("Arial", 8), bg="#e9ecef", justify=tk.LEFT).pack(anchor=tk.W, padx=20, pady=2)

        tk.Label(format_frame, text="🔬 OPTIONAL QC DETECTION:",
                font=("Arial", 8, "bold"), bg="#e9ecef").pack(anchor=tk.W, padx=5, pady=2)
        tk.Label(format_frame, text="• QC standards in Sample_ID (e.g., 'NIST2710a', 'BHVO-2')\n• Or separate QC file",
                font=("Arial", 8), bg="#e9ecef", justify=tk.LEFT).pack(anchor=tk.W, padx=20, pady=2)

        # Import buttons
        btn_frame = tk.Frame(import_frame, bg="#f8f9fa")
        btn_frame.pack(fill=tk.X, pady=10)

        tk.Button(btn_frame, text="📂 Import CSV/Excel",
                 command=self._import_timeseries,
                 bg="#3498db", fg="white",
                 font=("Arial", 10, "bold"),
                 width=20, height=2).pack(pady=5)

        tk.Button(btn_frame, text="📋 Import from Current Samples",
                 command=self._import_from_main,
                 bg="#2ecc71", fg="white",
                 font=("Arial", 9),
                 width=20).pack(pady=2)

        # QC Standard selection
        qc_frame = tk.LabelFrame(left, text="🔬 QC STANDARD SELECTION",
                                font=("Arial", 10, "bold"),
                                bg="#f8f9fa", padx=10, pady=10)
        qc_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(qc_frame, text="Select certified reference material:",
                font=("Arial", 9), bg="#f8f9fa").pack(anchor=tk.W, pady=5)

        self.qc_standard_var = tk.StringVar()
        qc_combo = ttk.Combobox(qc_frame,
                               textvariable=self.qc_standard_var,
                               values=list(self.CERTIFIED_REFERENCE_MATERIALS.keys()),
                               state="readonly", width=30)
        qc_combo.pack(anchor=tk.W, pady=5)
        qc_combo.bind('<<ComboboxSelected>>', self._on_qc_standard_selected)

        # Certified values display
        self.certified_frame = tk.Frame(qc_frame, bg="#e9ecef", relief=tk.GROOVE, borderwidth=1)
        self.certified_frame.pack(fill=tk.X, pady=10)

        self.certified_text = tk.Text(self.certified_frame, height=6, width=40,
                                     font=("Courier", 8), bg="#e9ecef",
                                     relief=tk.FLAT, padx=5, pady=5)
        self.certified_text.pack(fill=tk.BOTH, expand=True)
        self.certified_text.insert(tk.END, "Select a QC standard to view certified values")
        self.certified_text.config(state=tk.DISABLED)

        # Auto-detect button
        tk.Button(qc_frame, text="🔍 Auto-Detect QC Samples in Data",
                 command=self._auto_detect_qc,
                 bg="#9b59b6", fg="white",
                 font=("Arial", 9, "bold"),
                 width=30).pack(pady=10)

        # ============ RIGHT PANEL - DATA PREVIEW ============
        right = tk.Frame(paned, bg="white")
        paned.add(right, width=700)

        # QC Standards detected
        preview_frame = tk.LabelFrame(right, text="📋 DETECTED QC STANDARDS",
                                     font=("Arial", 10, "bold"),
                                     bg="white", padx=10, pady=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Treeview for QC samples
        tree_frame = tk.Frame(preview_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        scroll_y = tk.Scrollbar(tree_frame)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x = tk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.qc_tree = ttk.Treeview(tree_frame,
                                   columns=('Timestamp', 'Sample_ID', 'Zr', 'Nb', 'Cr', 'Ni', 'Ba'),
                                   show='headings',
                                   yscrollcommand=scroll_y.set,
                                   xscrollcommand=scroll_x.set)
        scroll_y.config(command=self.qc_tree.yview)
        scroll_x.config(command=self.qc_tree.xview)

        # Define headings
        self.qc_tree.heading('Timestamp', text='Timestamp')
        self.qc_tree.heading('Sample_ID', text='Sample ID')
        self.qc_tree.heading('Zr', text='Zr (ppm)')
        self.qc_tree.heading('Nb', text='Nb (ppm)')
        self.qc_tree.heading('Cr', text='Cr (ppm)')
        self.qc_tree.heading('Ni', text='Ni (ppm)')
        self.qc_tree.heading('Ba', text='Ba (ppm)')

        self.qc_tree.column('Timestamp', width=150)
        self.qc_tree.column('Sample_ID', width=150)
        self.qc_tree.column('Zr', width=80)
        self.qc_tree.column('Nb', width=80)
        self.qc_tree.column('Cr', width=80)
        self.qc_tree.column('Ni', width=80)
        self.qc_tree.column('Ba', width=80)

        self.qc_tree.pack(fill=tk.BOTH, expand=True)

        # Sample data preview tab
        sample_preview_frame = tk.LabelFrame(right, text="🧪 SAMPLE DATA PREVIEW",
                                            font=("Arial", 10, "bold"),
                                            bg="white", padx=10, pady=10)
        sample_preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.sample_preview_text = tk.Text(sample_preview_frame, height=8,
                                          font=("Courier", 9),
                                          bg="#f8f9fa", wrap=tk.NONE)
        sample_scroll = tk.Scrollbar(sample_preview_frame, orient=tk.HORIZONTAL,
                                    command=self.sample_preview_text.xview)
        self.sample_preview_text.config(xscrollcommand=sample_scroll.set)

        self.sample_preview_text.pack(fill=tk.BOTH, expand=True)
        sample_scroll.pack(fill=tk.X)

        self.sample_preview_text.insert(tk.END, "No data loaded. Import time-series data to begin.")
        self.sample_preview_text.config(state=tk.DISABLED)

    def _create_modeling_tab(self):
        """Tab 2: Drift modeling and visualization"""
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="📈 2. DRIFT MODELING")

        # Control panel at top
        control_frame = tk.Frame(tab, bg="#f8f9fa", relief=tk.RAISED, borderwidth=1, height=80)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        control_frame.pack_propagate(False)

        # Model selection
        tk.Label(control_frame, text="Drift Model:",
                font=("Arial", 10, "bold"), bg="#f8f9fa").pack(side=tk.LEFT, padx=10)

        self.model_var = tk.StringVar(value="polynomial")
        model_combo = ttk.Combobox(control_frame,
                                  textvariable=self.model_var,
                                  values=['linear', 'polynomial', 'exponential', 'loess'],
                                  state="readonly", width=15)
        model_combo.pack(side=tk.LEFT, padx=5)

        tk.Label(control_frame, text="Polynomial degree:",
                font=("Arial", 9), bg="#f8f9fa").pack(side=tk.LEFT, padx=20)

        self.degree_var = tk.IntVar(value=2)
        degree_spin = tk.Spinbox(control_frame, from_=1, to=5, width=5,
                                textvariable=self.degree_var)
        degree_spin.pack(side=tk.LEFT, padx=5)

        tk.Label(control_frame, text="Element:",
                font=("Arial", 10, "bold"), bg="#f8f9fa").pack(side=tk.LEFT, padx=20)

        self.element_var = tk.StringVar(value="Zr")
        element_combo = ttk.Combobox(control_frame,
                                    textvariable=self.element_var,
                                    values=['Zr', 'Nb', 'Cr', 'Ni', 'Ba', 'Rb', 'Sr'],
                                    state="readonly", width=8)
        element_combo.pack(side=tk.LEFT, padx=5)

        tk.Button(control_frame, text="📈 Model Drift",
                 command=self._model_drift,
                 bg="#e67e22", fg="white",
                 font=("Arial", 10, "bold"),
                 width=15).pack(side=tk.RIGHT, padx=10)

        # Main content area - plots
        plot_container = tk.Frame(tab, bg="white")
        plot_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create matplotlib figure
        self.drift_figure = Figure(figsize=(12, 8), dpi=100, facecolor='white')

        # Subplots
        self.drift_ax1 = self.drift_figure.add_subplot(221)  # QC measurements + drift model
        self.drift_ax2 = self.drift_figure.add_subplot(222)  # Correction factors
        self.drift_ax3 = self.drift_figure.add_subplot(223)  # Sample measurements before/after
        self.drift_ax4 = self.drift_figure.add_subplot(224)  # QC recovery

        self.drift_figure.tight_layout(pad=3.0)

        self.drift_canvas = FigureCanvasTkAgg(self.drift_figure, master=plot_container)
        self.drift_canvas.draw()
        self.drift_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Placeholder text
        self.drift_ax1.text(0.5, 0.5, 'Import QC data and select standard\nto model drift',
                          ha='center', va='center', transform=self.drift_ax1.transAxes)
        self.drift_ax1.set_title('QC Drift Modeling')
        self.drift_ax2.text(0.5, 0.5, 'Run drift model\nto generate correction factors',
                          ha='center', va='center', transform=self.drift_ax2.transAxes)
        self.drift_ax2.set_title('Correction Factors')
        self.drift_ax3.text(0.5, 0.5, 'Apply correction\nto sample data',
                          ha='center', va='center', transform=self.drift_ax3.transAxes)
        self.drift_ax3.set_title('Sample Correction')
        self.drift_ax4.text(0.5, 0.5, 'Validate with\nQC recovery',
                          ha='center', va='center', transform=self.drift_ax4.transAxes)
        self.drift_ax4.set_title('QC Recovery')

        self.drift_canvas.draw()

    def _create_correction_tab(self):
        """Tab 3: Apply correction and export"""
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="✅ 3. CORRECT & EXPORT")

        # Split into left/right
        paned = tk.PanedWindow(tab, orient=tk.HORIZONTAL, sashwidth=6)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ============ LEFT PANEL - CORRECTION CONTROLS ============
        left = tk.Frame(paned, bg="#f8f9fa", relief=tk.RAISED, borderwidth=1)
        paned.add(left, width=400)

        # Apply correction
        apply_frame = tk.LabelFrame(left, text="✅ APPLY CORRECTION",
                                   font=("Arial", 10, "bold"),
                                   bg="#f8f9fa", padx=10, pady=10)
        apply_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(apply_frame,
                text="Apply drift correction to all samples:",
                font=("Arial", 9), bg="#f8f9fa").pack(anchor=tk.W, pady=5)

        # Correction options
        self.correction_method_var = tk.StringVar(value="multiplicative")

        tk.Radiobutton(apply_frame, text="Multiplicative (ratio to baseline)",
                      variable=self.correction_method_var, value="multiplicative",
                      bg="#f8f9fa").pack(anchor=tk.W, pady=2)
        tk.Radiobutton(apply_frame, text="Additive (difference from baseline)",
                      variable=self.correction_method_var, value="additive",
                      bg="#f8f9fa").pack(anchor=tk.W, pady=2)
        tk.Radiobutton(apply_frame, text="Polynomial regression",
                      variable=self.correction_method_var, value="polynomial",
                      bg="#f8f9fa").pack(anchor=tk.W, pady=2)

        tk.Label(apply_frame, text="Baseline time:",
                font=("Arial", 9, "bold"), bg="#f8f9fa").pack(anchor=tk.W, pady=(10, 2))

        self.baseline_var = tk.StringVar(value="first")
        baseline_combo = ttk.Combobox(apply_frame,
                                     textvariable=self.baseline_var,
                                     values=['first', 'median', 'certified'],
                                     state="readonly", width=15)
        baseline_combo.pack(anchor=tk.W, pady=2)

        tk.Button(apply_frame, text="✅ APPLY CORRECTION",
                 command=self._apply_correction,
                 bg="#27ae60", fg="white",
                 font=("Arial", 11, "bold"),
                 width=25, height=2).pack(pady=20)

        # Export options
        export_frame = tk.LabelFrame(left, text="💾 EXPORT CORRECTED DATA",
                                    font=("Arial", 10, "bold"),
                                    bg="#f8f9fa", padx=10, pady=10)
        export_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(export_frame, text="Export options:",
                font=("Arial", 9), bg="#f8f9fa").pack(anchor=tk.W, pady=5)

        self.export_samples_var = tk.BooleanVar(value=True)
        tk.Checkbutton(export_frame, text="Export corrected samples",
                      variable=self.export_samples_var,
                      bg="#f8f9fa").pack(anchor=tk.W, pady=2)

        self.export_qc_var = tk.BooleanVar(value=True)
        tk.Checkbutton(export_frame, text="Export QC recovery report",
                      variable=self.export_qc_var,
                      bg="#f8f9fa").pack(anchor=tk.W, pady=2)

        self.export_plots_var = tk.BooleanVar(value=True)
        tk.Checkbutton(export_frame, text="Export drift plots",
                      variable=self.export_plots_var,
                      bg="#f8f9fa").pack(anchor=tk.W, pady=2)

        tk.Button(export_frame, text="💾 EXPORT CSV",
                 command=self._export_corrected,
                 bg="#3498db", fg="white",
                 font=("Arial", 10, "bold"),
                 width=20).pack(pady=10)

        # ============ RIGHT PANEL - RESULTS PREVIEW ============
        right = tk.Frame(paned, bg="white")
        paned.add(right, width=700)

        # Correction results
        results_frame = tk.LabelFrame(right, text="📊 CORRECTION RESULTS",
                                     font=("Arial", 10, "bold"),
                                     bg="white", padx=10, pady=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Treeview for corrected samples
        tree_frame = tk.Frame(results_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        scroll_y = tk.Scrollbar(tree_frame)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x = tk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.corrected_tree = ttk.Treeview(tree_frame,
                                          columns=('Sample_ID', 'Element', 'Raw', 'Corrected', 'Factor', 'QC_Recovery'),
                                          show='headings',
                                          yscrollcommand=scroll_y.set,
                                          xscrollcommand=scroll_x.set)
        scroll_y.config(command=self.corrected_tree.yview)
        scroll_x.config(command=self.corrected_tree.xview)

        self.corrected_tree.heading('Sample_ID', text='Sample ID')
        self.corrected_tree.heading('Element', text='Element')
        self.corrected_tree.heading('Raw', text='Raw (ppm)')
        self.corrected_tree.heading('Corrected', text='Corrected (ppm)')
        self.corrected_tree.heading('Factor', text='Correction Factor')
        self.corrected_tree.heading('QC_Recovery', text='QC Recovery %')

        self.corrected_tree.column('Sample_ID', width=150)
        self.corrected_tree.column('Element', width=80)
        self.corrected_tree.column('Raw', width=100)
        self.corrected_tree.column('Corrected', width=100)
        self.corrected_tree.column('Factor', width=100)
        self.corrected_tree.column('QC_Recovery', width=100)

        self.corrected_tree.pack(fill=tk.BOTH, expand=True)

        # Summary statistics
        summary_frame = tk.Frame(results_frame, bg="#e9ecef", relief=tk.GROOVE, borderwidth=1)
        summary_frame.pack(fill=tk.X, pady=10)

        self.summary_text = tk.Text(summary_frame, height=6,
                                   font=("Courier", 9),
                                   bg="#e9ecef", relief=tk.FLAT,
                                   padx=10, pady=10)
        self.summary_text.pack(fill=tk.BOTH, expand=True)
        self.summary_text.insert(tk.END, "Apply correction to see summary statistics")
        self.summary_text.config(state=tk.DISABLED)

    def _create_help_tab(self):
        """Tab 4: Help and documentation"""
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="❓ HELP & DOCS")

        help_text = tk.Text(tab, wrap=tk.WORD,
                           font=("Arial", 10),
                           bg="white", padx=20, pady=20)
        help_text.pack(fill=tk.BOTH, expand=True)

        documentation = """
📉 pXRF DRIFT CORRECTION - USER GUIDE
═══════════════════════════════════════════════════════════════════════════

WHAT IS DRIFT?
───────────────────────────────────────────────────────────────────────────
pXRF instruments are NOT stable over time. Common drift sources:

• X-ray tube aging → DECREASING intensity over weeks/months
• Temperature changes → GAIN drift during daily operation
• Detector degradation → RESOLUTION loss over years
• Count time variations → PRECISION changes

If you measured samples on Monday and Friday, they are NOT directly comparable.
This plugin fixes that.

───────────────────────────────────────────────────────────────────────────

WORKFLOW
───────────────────────────────────────────────────────────────────────────

1️⃣ IMPORT DATA
   • CSV/Excel with Timestamp column (ISO format: 2026-02-11 14:30:00)
   • Sample_ID column (QC standards + unknowns)
   • Element columns (Zr_ppm, Nb_ppm, etc.)

2️⃣ SELECT QC STANDARD
   • Choose certified reference material (NIST 2710a, BHVO-2, etc.)
   • Auto-detect QC measurements from your Sample_ID column
   • Plugin will find all measurements of that standard

3️⃣ MODEL DRIFT
   • Plot QC measurements vs time
   • Fit drift model (linear, polynomial, exponential, LOESS)
   • Calculate correction factors for each element

4️⃣ APPLY CORRECTION
   • Choose baseline (first measurement, median, certified value)
   • Apply correction to all samples
   • Validate with QC recovery (should be 100% ± 5%)

5️⃣ EXPORT
   • Drift-corrected concentrations
   • QC recovery report
   • Diagnostic plots for publication

───────────────────────────────────────────────────────────────────────────

DRIFT MODELS EXPLAINED
───────────────────────────────────────────────────────────────────────────

📈 LINEAR: f(t) = a·t + b
   • Simple, stable, recommended for short runs (<1 day)
   • Assumes constant drift rate

📊 POLYNOMIAL: f(t) = a·t² + b·t + c
   • Flexible, captures non-linear drift
   • Degree 2-3 recommended (higher = overfitting)

📉 EXPONENTIAL: f(t) = a·exp(b·t) + c
   • Tube aging decay curve
   • Use for long-term drift (weeks/months)

🔄 LOESS: Locally weighted regression
   • Non-parametric, follows data shape
   • Use when drift pattern is complex

───────────────────────────────────────────────────────────────────────────

CERTIFIED REFERENCE MATERIALS
───────────────────────────────────────────────────────────────────────────

🔬 NIST 2710a - Montana Soil (Highly Elevated)
   • High trace elements, excellent for pXRF
   • Zr: 324 ppm, Nb: 19 ppm, Pb: 5532 ppm

🔬 BHVO-2 - Hawaiian Basalt
   • Your actual rock matrix!
   • Zr: 172 ppm, Nb: 18 ppm, Cr: 280 ppm

🔬 BCR-2 - Columbia River Basalt
   • Another basalt standard
   • Zr: 188 ppm, Nb: 12.5 ppm, Ba: 683 ppm

⚠️ Always use matrix-matched standards when possible!

───────────────────────────────────────────────────────────────────────────

INTERPRETING RESULTS
───────────────────────────────────────────────────────────────────────────

✅ GOOD CORRECTION:
   • QC recovery: 95-105%
   • Correction factors: 0.9-1.1
   • Smooth drift pattern
   • Visual improvement in time-series

⚠️ WARNING SIGNS:
   • QC recovery <90% or >110%
   • Erratic drift pattern
   • Correction factors >1.2 or <0.8
   • Different elements drift differently

🛠️ TROUBLESHOOTING:
   • Not enough QC measurements? Need at least 3
   • No timestamp column? Add ISO format datetime
   • Wrong standard? Use matrix-matched reference
   • Severe drift? Try polynomial/exponential model

───────────────────────────────────────────────────────────────────────────

PUBLICATION NOTES
───────────────────────────────────────────────────────────────────────────

When reporting drift-corrected pXRF data, include:

1. "All measurements were drift-corrected using repeated analyses of
   [standard name] throughout the analytical session."

2. "Drift was modeled using [linear/polynomial/exponential/LOESS]
   regression, and correction factors were applied multiplicatively."

3. "Average QC recovery after correction was [XX]% (range YY-ZZ%)."

4. "Uncertainties are reported as ±1σ, propagated from counting statistics
   and drift correction uncertainty."

───────────────────────────────────────────────────────────────────────────

CITATION
───────────────────────────────────────────────────────────────────────────

If you use this plugin in published research, please cite:

Levy, S. (2026). pXRF Drift Correction Plugin for Basalt Provenance
Triage Toolkit. Zenodo. https://doi.org/10.5281/zenodo.18499130

───────────────────────────────────────────────────────────────────────────
"""
        help_text.insert(tk.END, documentation)
        help_text.config(state=tk.DISABLED)

    def _import_timeseries(self):
        """Import time-series CSV/Excel with timestamps"""
        file_path = filedialog.askopenfilename(
            title="Import pXRF Time-Series Data",
            filetypes=[
                ("CSV files", "*.csv"),
                ("Excel files", "*.xlsx *.xls"),
                ("All files", "*.*")
            ]
        )

        if not file_path:
            return

        try:
            # Load based on extension
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)

            # Try to parse timestamp column
            timestamp_col = None
            for col in df.columns:
                if 'time' in col.lower() or 'date' in col.lower() or 'timestamp' in col.lower():
                    timestamp_col = col
                    break

            if timestamp_col is None:
                messagebox.showerror("No Timestamp Column",
                                   "Could not find timestamp column.\n\n"
                                   "Please ensure your data has a column with:\n"
                                   "• 'Timestamp', 'DateTime', 'Time', or 'Date'\n"
                                   "• ISO format (2026-02-11 14:30:00)")
                return

            # Convert to datetime
            df['DateTime'] = pd.to_datetime(df[timestamp_col])
            df = df.sort_values('DateTime')

            # Store data
            self.raw_data = df

            # Update preview
            self._update_data_preview()

            # Auto-detect QC
            self._auto_detect_qc()

            # Update status
            self.data_status_label.config(text=f"📊 {len(df)} samples loaded",
                                        fg="#27ae60")
            self.stats_label.config(text=f"Loaded: {os.path.basename(file_path)} • {len(df)} measurements")

            self._log("✅ Imported time-series data", tab=3)
            self._log(f"   File: {os.path.basename(file_path)}", tab=3)
            self._log(f"   Samples: {len(df)}", tab=3)
            self._log(f"   Time range: {df['DateTime'].min()} to {df['DateTime'].max()}", tab=3)

        except Exception as e:
            messagebox.showerror("Import Error", f"Could not load file:\n\n{str(e)}")

    def _import_from_main(self):
        """Import samples from main app (assume they have timestamps)"""
        if not self.app.samples:
            messagebox.showwarning("No Data", "No samples in main application!")
            return

        try:
            # Convert to DataFrame
            df = pd.DataFrame(self.app.samples)

            # Try to find/create timestamp
            if 'Timestamp' not in df.columns and 'DateTime' not in df.columns:
                # Try to parse from other columns
                for col in df.columns:
                    if 'time' in col.lower() or 'date' in col.lower():
                        try:
                            df['DateTime'] = pd.to_datetime(df[col])
                            break
                        except:
                            continue
                else:
                    # Create sequential timestamps
                    now = datetime.now()
                    df['DateTime'] = [now + timedelta(minutes=i) for i in range(len(df))]
                    self._log("⚠ No timestamps found - created sequential timestamps", tab=3)

            self.raw_data = df
            self._update_data_preview()
            self._auto_detect_qc()

            self.data_status_label.config(text=f"📊 {len(df)} samples loaded", fg="#27ae60")

        except Exception as e:
            messagebox.showerror("Import Error", str(e))

    def _update_data_preview(self):
        """Update data preview panes"""
        if self.raw_data is None:
            return

        # Update QC tree
        if hasattr(self, 'qc_tree') and self.qc_data is not None:
            for item in self.qc_tree.get_children():
                self.qc_tree.delete(item)

            for _, row in self.qc_data.iterrows():
                self.qc_tree.insert('', tk.END, values=(
                    row.get('DateTime', ''),
                    row.get('Sample_ID', ''),
                    f"{row.get('Zr_ppm', 0):.1f}",
                    f"{row.get('Nb_ppm', 0):.1f}",
                    f"{row.get('Cr_ppm', 0):.1f}",
                    f"{row.get('Ni_ppm', 0):.1f}",
                    f"{row.get('Ba_ppm', 0):.1f}"
                ))

        # Update sample preview
        if hasattr(self, 'sample_preview_text'):
            self.sample_preview_text.config(state=tk.NORMAL)
            self.sample_preview_text.delete(1.0, tk.END)

            # Show first 20 rows
            preview_df = self.raw_data.head(20)
            self.sample_preview_text.insert(tk.END, preview_df.to_string())

            if len(self.raw_data) > 20:
                self.sample_preview_text.insert(tk.END, f"\n\n... and {len(self.raw_data) - 20} more rows")

            self.sample_preview_text.config(state=tk.DISABLED)

    def _auto_detect_qc(self):
        """Auto-detect QC standards in Sample_ID column"""
        if self.raw_data is None:
            return

        # Try to find Sample_ID column
        sample_col = None
        for col in self.raw_data.columns:
            if 'sample' in col.lower() or 'id' in col.lower():
                sample_col = col
                break

        if sample_col is None:
            return

        # Check each QC standard
        detected = []
        for std_name in self.CERTIFIED_REFERENCE_MATERIALS.keys():
            # Try different naming patterns
            patterns = [
                std_name,
                std_name.replace(' ', ''),
                std_name.replace('-', ''),
                std_name.lower(),
                std_name.upper()
            ]

            mask = False
            for pattern in patterns:
                mask = mask | self.raw_data[sample_col].astype(str).str.contains(pattern, case=False, na=False)

            if mask.any():
                qc_rows = self.raw_data[mask].copy()
                detected.append({
                    'standard': std_name,
                    'count': len(qc_rows),
                    'data': qc_rows
                })

        if detected:
            # Use the most frequently detected standard
            detected.sort(key=lambda x: x['count'], reverse=True)
            best = detected[0]

            self.selected_standard = best['standard']
            self.qc_data = best['data']
            self.qc_standard_var.set(best['standard'])

            # Update UI
            self._update_data_preview()
            self._on_qc_standard_selected()

            self.qc_status_label.config(text=f"🔬 QC: {best['standard']} ({best['count']} measurements)",
                                       fg="#27ae60")

            self._log(f"✅ Auto-detected QC standard: {best['standard']}", tab=3)
            self._log(f"   Found {best['count']} measurements", tab=3)
        else:
            self.qc_status_label.config(text="🔬 No QC detected - select manually", fg="#e67e22")
            self._log("⚠ No QC standards auto-detected - select manually", tab=3)

    def _on_qc_standard_selected(self, event=None):
        """Update certified values display when QC standard is selected"""
        std_name = self.qc_standard_var.get()
        if not std_name:
            return

        std = self.CERTIFIED_REFERENCE_MATERIALS.get(std_name, {})

        # Update certified values text
        self.certified_text.config(state=tk.NORMAL)
        self.certified_text.delete(1.0, tk.END)

        text = f"📋 {std_name}: {std.get('name', '')}\n"
        text += f"   Source: {std.get('source', '')} ({std.get('certified', '')})\n\n"
        text += "   Certified Values:\n"

        for elem in ['Zr', 'Nb', 'Cr', 'Ni', 'Ba', 'Rb', 'Sr', 'Pb', 'Zn', 'Cu', 'Fe', 'Mn']:
            if elem in std:
                text += f"   {elem}: {std[elem]} ppm\n"

        self.certified_text.insert(tk.END, text)
        self.certified_text.config(state=tk.DISABLED)

        self.certified_values = std

    def _model_drift(self):
        """Model drift from QC measurements"""
        if self.qc_data is None or self.certified_values is None:
            messagebox.showwarning("No QC Data",
                                 "Select a QC standard with measurements first!")
            return

        element = self.element_var.get()
        if element not in self.certified_values:
            messagebox.showwarning("Element Not Certified",
                                 f"{element} is not certified for {self.selected_standard}")
            return

        # Get QC measurements
        times = self.qc_data['DateTime'].astype(np.int64) / 1e9  # Convert to seconds
        times_norm = (times - times.min()) / (times.max() - times.min() + 1)  # Normalize to [0,1]

        # Get measured values
        elem_col = None
        for col in self.qc_data.columns:
            if element in col and ('ppm' in col or element == col):
                elem_col = col
                break

        if elem_col is None:
            messagebox.showerror("Element Not Found",
                               f"Could not find {element} data in QC measurements")
            return

        measured = self.qc_data[elem_col].values.astype(float)
        certified = self.certified_values[element]

        # Calculate recovery
        recovery = measured / certified

        # Fit drift model
        model_type = self.model_var.get()
        degree = self.degree_var.get()

        x_plot = np.linspace(0, 1, 100)

        try:
            if model_type == 'linear':
                coeffs = np.polyfit(times_norm, recovery, 1)
                model = np.poly1d(coeffs)
                model_vals = model(x_plot)
                model_name = f'Linear: y = {coeffs[0]:.4f}t + {coeffs[1]:.4f}'

            elif model_type == 'polynomial':
                coeffs = np.polyfit(times_norm, recovery, degree)
                model = np.poly1d(coeffs)
                model_vals = model(x_plot)
                model_name = f'Polynomial (deg={degree})'

            elif model_type == 'exponential':
                def exp_func(t, a, b, c):
                    return a * np.exp(b * t) + c

                popt, _ = curve_fit(exp_func, times_norm, recovery,
                                   p0=[1, 0, 0], maxfev=5000)
                model_vals = exp_func(x_plot, *popt)
                model_name = f'Exponential: y = {popt[0]:.4f}·exp({popt[1]:.4f}t) + {popt[2]:.4f}'

            elif model_type == 'loess':
                from scipy.interpolate import UnivariateSpline
                model = UnivariateSpline(times_norm, recovery, s=0.01)
                model_vals = model(x_plot)
                model_name = 'LOESS (smooth spline)'

            # Store model
            self.drift_models[element] = {
                'type': model_type,
                'function': model if model_type != 'exponential' else lambda t: exp_func(t, *popt),
                'params': coeffs if model_type != 'exponential' else popt,
                'certified': certified,
                'times_norm': times_norm,
                'recovery': recovery,
                'x_plot': x_plot,
                'model_vals': model_vals,
                'model_name': model_name
            }

            # Update plot
            self._update_drift_plot(element)

            self._log(f"📈 Modeled {element} drift: {model_name}", tab=3)
            self._log(f"   Recovery range: {recovery.min()*100:.1f}% - {recovery.max()*100:.1f}%", tab=3)

        except Exception as e:
            messagebox.showerror("Modeling Error", f"Could not fit drift model:\n\n{str(e)}")

    def _update_drift_plot(self, element):
        """Update drift modeling plots"""
        if element not in self.drift_models:
            return

        model = self.drift_models[element]

        # Clear axes
        self.drift_ax1.clear()
        self.drift_ax2.clear()
        self.drift_ax3.clear()
        self.drift_ax4.clear()

        # Plot 1: QC measurements and drift model
        times_hours = model['times_norm'] * (self.qc_data['DateTime'].max() - self.qc_data['DateTime'].min()).total_seconds() / 3600
        x_hours = model['x_plot'] * (self.qc_data['DateTime'].max() - self.qc_data['DateTime'].min()).total_seconds() / 3600

        self.drift_ax1.scatter(times_hours, model['recovery'] * 100,
                              c='blue', s=50, alpha=0.7, label='QC Measurements')
        self.drift_ax1.plot(x_hours, model['model_vals'] * 100,
                           'r-', linewidth=2, label=model['model_name'])
        self.drift_ax1.axhline(y=100, color='gray', linestyle='--', alpha=0.5, label='Certified')
        self.drift_ax1.set_xlabel('Time (hours)')
        self.drift_ax1.set_ylabel('Recovery (%)')
        self.drift_ax1.set_title(f'{element} Drift - {self.selected_standard}')
        self.drift_ax1.legend()
        self.drift_ax1.grid(True, alpha=0.3)

        # Plot 2: Correction factors
        correction = 1 / model['model_vals']
        self.drift_ax2.plot(x_hours, correction, 'g-', linewidth=2)
        self.drift_ax2.axhline(y=1, color='gray', linestyle='--', alpha=0.5)
        self.drift_ax2.set_xlabel('Time (hours)')
        self.drift_ax2.set_ylabel('Correction Factor')
        self.drift_ax2.set_title(f'{element} Correction Factors')
        self.drift_ax2.grid(True, alpha=0.3)

        # Plot 3: Sample data preview (if available)
        if self.raw_data is not None and 'DateTime' in self.raw_data.columns:
            sample_mask = True
            if self.qc_data is not None:
                # Exclude QC samples
                qc_times = self.qc_data['DateTime'].values
                sample_mask = ~self.raw_data['DateTime'].isin(qc_times)

            sample_times = self.raw_data.loc[sample_mask, 'DateTime']
            if len(sample_times) > 0:
                sample_times_norm = (sample_times.astype(np.int64) / 1e9 - self.qc_data['DateTime'].astype(np.int64).min() / 1e9) / \
                                  (self.qc_data['DateTime'].astype(np.int64).max() - self.qc_data['DateTime'].astype(np.int64).min()).total_seconds()

                # Get sample values for this element
                if elem_col in self.raw_data.columns:
                    sample_vals = self.raw_data.loc[sample_mask, elem_col].values

                    # Apply correction
                    sample_times_norm_clipped = np.clip(sample_times_norm, 0, 1)
                    if model['type'] == 'exponential':
                        sample_correction = 1 / model['function'](sample_times_norm_clipped)
                    else:
                        sample_correction = 1 / model['function'](sample_times_norm_clipped)

                    corrected_vals = sample_vals * sample_correction

                    # Plot
                    sample_times_hours = sample_times_norm * (self.qc_data['DateTime'].max() - self.qc_data['DateTime'].min()).total_seconds() / 3600
                    self.drift_ax3.scatter(sample_times_hours, sample_vals,
                                          c='red', s=20, alpha=0.5, label='Raw')
                    self.drift_ax3.scatter(sample_times_hours, corrected_vals,
                                          c='green', s=20, alpha=0.5, label='Corrected')
                    self.drift_ax3.set_xlabel('Time (hours)')
                    self.drift_ax3.set_ylabel(f'{element} (ppm)')
                    self.drift_ax3.set_title(f'Sample {element} - Before/After')
                    self.drift_ax3.legend()
                    self.drift_ax3.grid(True, alpha=0.3)

        # Plot 4: QC recovery validation
        if 'recovery' in model:
            recovery_pct = model['recovery'] * 100
            model_recovery = model['model_vals'] * 100

            self.drift_ax4.scatter(times_hours, recovery_pct,
                                  c='blue', s=50, alpha=0.7, label='Measured')
            self.drift_ax4.plot(x_hours, model_recovery, 'r-', linewidth=2, label='Model')
            self.drift_ax4.axhline(y=100, color='gray', linestyle='--', alpha=0.5)
            self.drift_ax4.axhline(y=95, color='green', linestyle=':', alpha=0.3)
            self.drift_ax4.axhline(y=105, color='green', linestyle=':', alpha=0.3)
            self.drift_ax4.set_xlabel('Time (hours)')
            self.drift_ax4.set_ylabel('Recovery (%)')
            self.drift_ax4.set_title('QC Recovery Validation')
            self.drift_ax4.legend()
            self.drift_ax4.grid(True, alpha=0.3)

        self.drift_figure.tight_layout()
        self.drift_canvas.draw()

    def _apply_correction(self):
        """Apply drift correction to all samples"""
        if not self.drift_models:
            messagebox.showwarning("No Drift Model",
                                 "Model drift first for at least one element!")
            return

        if self.raw_data is None:
            return

        try:
            corrected_df = self.raw_data.copy()

            # Create columns for corrected values
            for element, model in self.drift_models.items():
                # Find element column
                elem_col = None
                for col in corrected_df.columns:
                    if element in col and ('ppm' in col or element == col):
                        elem_col = col
                        break

                if elem_col is None:
                    continue

                # Get timestamps for all samples
                times = corrected_df['DateTime'].astype(np.int64) / 1e9
                qc_min = self.qc_data['DateTime'].astype(np.int64).min() / 1e9
                qc_range = (self.qc_data['DateTime'].max() - self.qc_data['DateTime'].min()).total_seconds()

                times_norm = (times - qc_min) / qc_range
                times_norm = np.clip(times_norm, 0, 1)

                # Calculate correction factors
                if model['type'] == 'exponential':
                    correction = 1 / model['function'](times_norm)
                else:
                    correction = 1 / model['function'](times_norm)

                # Apply correction
                corrected_vals = corrected_df[elem_col].astype(float) * correction

                # Store
                corrected_df[f'{elem_col}_drift_corrected'] = corrected_vals
                corrected_df[f'{elem_col}_correction_factor'] = correction

            self.corrected_data = corrected_df

            # Update results table
            self._update_correction_results()

            self._log("✅ Applied drift correction to all samples", tab=3)
            self._log(f"   Corrected elements: {list(self.drift_models.keys())}", tab=3)

        except Exception as e:
            messagebox.showerror("Correction Error", str(e))

    def _update_correction_results(self):
        """Update correction results table"""
        if self.corrected_data is None:
            return

        # Clear tree
        for item in self.corrected_tree.get_children():
            self.corrected_tree.delete(item)

        # Show first 50 samples
        count = 0
        for idx, row in self.corrected_data.iterrows():
            if count >= 50:
                break

            sample_id = row.get('Sample_ID', f'Sample_{idx}')

            for element in self.drift_models.keys():
                elem_col = None
                for col in self.corrected_data.columns:
                    if element in col and ('ppm' in col or element == col) and '_corrected' not in col:
                        elem_col = col
                        break

                if elem_col is None:
                    continue

                raw_val = row.get(elem_col, 0)
                corr_col = f'{elem_col}_drift_corrected'
                factor_col = f'{elem_col}_correction_factor'

                if corr_col in row and factor_col in row:
                    corrected_val = row[corr_col]
                    factor = row[factor_col]

                    # Calculate QC recovery if this is a QC sample
                    qc_recovery = ""
                    if self.qc_data is not None and sample_id in self.qc_data['Sample_ID'].values:
                        if element in self.certified_values:
                            certified = self.certified_values[element]
                            recovery = (corrected_val / certified) * 100
                            qc_recovery = f"{recovery:.1f}%"

                    self.corrected_tree.insert('', tk.END, values=(
                        sample_id,
                        element,
                        f"{float(raw_val):.1f}",
                        f"{float(corrected_val):.1f}",
                        f"{float(factor):.3f}",
                        qc_recovery
                    ))

            count += 1

        # Update summary statistics
        self.summary_text.config(state=tk.NORMAL)
        self.summary_text.delete(1.0, tk.END)

        summary = "📊 CORRECTION SUMMARY\n"
        summary += "═" * 50 + "\n\n"

        for element, model in self.drift_models.items():
            summary += f"{element}:\n"
            summary += f"  • Model: {model['model_name']}\n"
            summary += f"  • Certified: {model['certified']} ppm\n"
            summary += f"  • Drift range: {model['recovery'].min()*100:.1f}% - {model['recovery'].max()*100:.1f}%\n"

            # Calculate mean correction factor
            if self.corrected_data is not None:
                factor_col = f'{element}_ppm_correction_factor'
                if factor_col in self.corrected_data.columns:
                    mean_factor = self.corrected_data[factor_col].mean()
                    summary += f"  • Mean correction: {mean_factor:.3f}\n"

            summary += "\n"

        self.summary_text.insert(tk.END, summary)
        self.summary_text.config(state=tk.DISABLED)

    def _export_corrected(self):
        """Export corrected data"""
        if self.corrected_data is None:
            messagebox.showwarning("No Data", "Apply correction first!")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("All Files", "*.*")],
            initialfile=f"pxrf_drift_corrected_{datetime.now().strftime('%Y%m%d')}.csv"
        )

        if not filename:
            return

        try:
            # Select columns to export
            export_cols = []

            # Always include identifiers
            for col in ['Sample_ID', 'DateTime']:
                if col in self.corrected_data.columns:
                    export_cols.append(col)

            # Include raw and corrected values
            for element in self.drift_models.keys():
                elem_col = None
                for col in self.corrected_data.columns:
                    if element in col and ('ppm' in col or element == col) and '_corrected' not in col and '_factor' not in col:
                        elem_col = col
                        break

                if elem_col:
                    export_cols.append(elem_col)
                    export_cols.append(f'{elem_col}_drift_corrected')
                    export_cols.append(f'{elem_col}_correction_factor')

            # Export
            self.corrected_data[export_cols].to_csv(filename, index=False)

            self._log(f"💾 Exported corrected data: {filename}", tab=3)

            messagebox.showinfo("Export Complete",
                              f"✅ Drift-corrected data exported!\n\n"
                              f"File: {os.path.basename(filename)}\n"
                              f"Samples: {len(self.corrected_data)}\n"
                              f"Elements corrected: {len(self.drift_models)}\n\n"
                              f"Columns:\n"
                              f"• Raw concentrations\n"
                              f"• Drift-corrected concentrations\n"
                              f"• Correction factors")

        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def _log(self, message, tab=0):
        """Log message to console and status"""
        print(f"📉 {message}")
        if hasattr(self, 'stats_label'):
            self.stats_label.config(text=message[:80])


def setup_plugin(main_app):
    """Plugin setup function"""
    print("📉 Loading pXRF Drift Correction Plugin v1.0")
    plugin = PXRFDriftCorrectionPlugin(main_app)

    if hasattr(main_app, 'menu_bar'):
        if not hasattr(main_app, 'hardware_menu'):
            main_app.hardware_menu = tk.Menu(main_app.menu_bar, tearoff=0)
            main_app.menu_bar.add_cascade(label="Hardware", menu=main_app.hardware_menu)

        main_app.hardware_menu.add_command(
            label="📉 pXRF Drift Corrector",
            command=plugin.open_window
        )

    return plugin
