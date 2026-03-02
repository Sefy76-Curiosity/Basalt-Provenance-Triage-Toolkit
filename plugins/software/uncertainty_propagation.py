"""
Generic Monte Carlo Uncertainty Propagation Plugin
v2.1 - Now with "Append to Main Table" feature
- Writes per‑sample confidence intervals and group ellipse parameters back to the main table
- User‑controlled, not automatic

Author: Sefy Levy (adapted for generic use)
License: CC BY-NC-SA 4.0
Version: 2.1.0
"""

PLUGIN_INFO = {
    "category": "software",
    "field": "General",
    "id": "uncertainty_propagation",
    "name": "Uncertainty Propagation",
    "icon": "🎲",
    "description": "Monte Carlo confidence ellipses & error propagation – now with table write‑back",
    "version": "2.1.0",
    "requires": ["numpy", "scipy", "matplotlib"],
    "author": "Sefy Levy"
}

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
from datetime import datetime
import sys
import os
from pathlib import Path

# ============ OPTIONAL DEPENDENCIES ============
try:
    from scipy.stats import chi2
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.patches import Ellipse
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


class GenericUncertaintyPlugin:
    """
    ============================================================================
    GENERIC MONTE CARLO UNCERTAINTY v2.1
    ============================================================================

    - Select any two numeric columns (X, Y) and an optional group column.
    - Monte Carlo perturbs each sample according to its analytical error.
    - For each group, computes the distribution of the group mean in X‑Y space.
    - Plots confidence ellipses (default 95%) showing where the true population
      mean lies.
    - Exports ellipse parameters and per‑sample confidence intervals.
    - NEW: Append results back to the main application table.
    ============================================================================
    """

    def __init__(self, main_app):
        self.app = main_app
        self.window = None
        self.progress_window = None
        self.progress_bar = None
        self.progress_label = None

        # Monte Carlo results
        self.group_results = {}          # group name -> ellipse data
        self.sample_results = {}          # sample ID -> perturbed distributions

        # UI elements
        self.status_indicator = None
        self.stats_label = None
        self.ellipse_canvas_frame = None
        self.results_text = None

        # User selections
        self.x_var = tk.StringVar()
        self.y_var = tk.StringVar()
        self.group_var = tk.StringVar(value="(No Grouping)")
        self.iterations_var = tk.StringVar(value="10000")
        self.fast_mode_var = tk.BooleanVar(value=False)
        self.confidence_level_var = tk.StringVar(value="95")

    # ============ NEW: RECEIVE DATA FROM OTHER PLUGINS ============
    def receive_data(self, data, context):
        """
        Receive data from another plugin (like Analysis Suite) for uncertainty analysis.

        Args:
            data: List of dictionaries with sample data
            context: Dict with metadata about the source
                e.g., {'type': 'gap_filling', 'variable': 'Temperature', 'method': 'MICE'}
        """
        self.external_data = data
        self.external_context = context

        # Auto-configure based on context
        if context.get('type') == 'gap_filling':
            # For time series, set X as time index, Y as variable
            self.x_var.set("Time")
            self.y_var.set(context.get('variable', 'Value'))
            self.group_var.set('(No Grouping)')  # Disable grouping for time series

            # Maybe suggest different defaults for time series
            if context.get('n_points', 0) > 100:
                self.fast_mode_var.set(True)  # Auto-enable fast mode for large datasets

        elif context.get('type') == 'aqi':
            # For AQI, set X as pollutant, Y as AQI
            self.x_var.set(context.get('pollutant', 'Pollutant'))
            self.y_var.set('AQI')

        elif context.get('type') == 'wind_rose':
            # For wind, set X as speed, Y as direction
            self.x_var.set('Wind_Speed')
            self.y_var.set('Wind_Direction')

        # Update UI if window is already open
        if self.window and self.window.winfo_exists():
            self._populate_column_choices()
            self.status_indicator.config(text="● EXTERNAL DATA", fg="#9b59b6")
            self.stats_label.config(text=f"Loaded: {context.get('type', 'data')} from Analysis Suite")

        # Open window
        self.open_window()

    # ============ ELEMENT EXTRACTION WITH SAFE DEFAULTS ============
    def _get_value_and_error(self, sample, column):
        """Extract a numeric value and its associated error from a sample."""
        # Value
        val = None
        val_key = None
        for key in sample:
            if key.lower() == column.lower():
                val_key = key
                try:
                    val = float(sample[key] or 0)
                except (ValueError, TypeError):
                    val = None
                break
        if val is None:
            return None, None, False

        # Error: try common error column names
        err = None
        err_candidates = [
            f"{val_key}_error",
            f"{val_key}_err",
            f"{val_key}_std",
            f"{val_key}_1sigma",
            f"{val_key}_uncertainty",
            column + "_error",
            column + "_err"
        ]
        for cand in err_candidates:
            if cand in sample:
                try:
                    e = float(sample[cand] or 0)
                    if e > 0:
                        err = e
                        break
                except (ValueError, TypeError):
                    continue

        # Fallback: 5% of value
        if err is None:
            err = val * 0.05
            return val, err, True   # True = estimated
        else:
            return val, err, False

    def _has_error_data(self, column):
        """Check if any sample has explicit error for a given column."""
        if not self.app.samples:
            return False
        for sample in self.app.samples[:20]:
            val, err, estimated = self._get_value_and_error(sample, column)
            if not estimated and err is not None:
                return True
        return False

    # ============ PROGRESS WINDOW ============
    def _show_progress(self, total_groups, iterations):
        self.progress_window = tk.Toplevel(self.window)
        self.progress_window.title("🎲 Monte Carlo Progress")
        self.progress_window.geometry("400x150")
        self.progress_window.transient(self.window)

        tk.Label(self.progress_window,
                text="Running Monte Carlo Simulation...",
                font=("Arial", 11, "bold")).pack(pady=10)

        self.progress_label = tk.Label(self.progress_window,
                                      text=f"Processing group 1/{total_groups}",
                                      font=("Arial", 9))
        self.progress_label.pack(pady=5)

        self.progress_bar = ttk.Progressbar(self.progress_window,
                                           length=300, mode='determinate')
        self.progress_bar.pack(pady=10)
        self.progress_bar['maximum'] = total_groups * (iterations / 1000)  # update every 1000 iters

        self.progress_window.update()

    def _update_progress(self, group_idx, total_groups, iter_count):
        if self.progress_window is None or self.progress_label is None or self.progress_bar is None:
            return
        try:
            if self.progress_label.winfo_exists():
                self.progress_label.config(
                    text=f"Group {group_idx+1}/{total_groups} - {iter_count:,} iterations"
                )
            if self.progress_bar.winfo_exists():
                self.progress_bar['value'] = (group_idx * (self.progress_bar['maximum'] / total_groups) +
                                             (iter_count / 1000))
            self.progress_window.update()
        except (tk.TclError, AttributeError):
            self.progress_window = None

    def _close_progress(self):
        if self.progress_window:
            try:
                self.progress_window.destroy()
            except:
                pass
            self.progress_window = None
            self.progress_label = None
            self.progress_bar = None

    # ============ MAIN INTERFACE ============
    def open_window(self):
        if not HAS_SCIPY:
            messagebox.showerror(
                "Missing Dependency",
                "This plugin requires scipy:\n\npip install scipy"
            )
            return

        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("🎲 Generic Monte Carlo Uncertainty v2.1")
        self.window.geometry("1000x650")
        self.window.transient(self.app.root)

        self._create_interface()
        self._populate_column_choices()
        self.window.lift()
        self.window.focus_force()

    def _populate_column_choices(self):
        """Scan samples for numeric columns and group candidates."""
        # Use external data if available
        if self.external_data is not None:
            samples = self.external_data
            self.current_data = self.external_data
        else:
            samples = self.app.samples
            self.current_data = self.app.samples

        if not samples:
            return

        numeric_cols = set()
        categorical_cols = set()

        for sample in samples[:100]:  # sample a subset
            for key, value in sample.items():
                if key in ['Sample_ID', 'ExperimentID', 'Device', 'Channel', 'Group', 'Time']:
                    categorical_cols.add(key)
                else:
                    # Try to convert to float
                    try:
                        float(str(value).replace(',', '.'))
                        numeric_cols.add(key)
                    except (ValueError, TypeError):
                        pass

        # Update combo boxes
        self.x_combo['values'] = sorted(numeric_cols)
        self.y_combo['values'] = sorted(numeric_cols)

        # If we have external context, maybe disable group selection
        if self.external_context and self.external_context.get('type') == 'gap_filling':
            group_choices = ['(No Grouping)']
            self.group_combo.config(state='disabled')
        else:
            group_choices = ['(No Grouping)'] + sorted(categorical_cols)
            self.group_combo.config(state='readonly')

        self.group_combo['values'] = group_choices

        if numeric_cols:
            first = sorted(numeric_cols)[0]
            # Don't override if already set by context
            if not self.x_var.get():
                self.x_var.set(first)
            if not self.y_var.get() and len(numeric_cols) > 1:
                self.y_var.set(sorted(numeric_cols)[1])
            elif not self.y_var.get():
                self.y_var.set(first)

        if not self.group_var.get():
            self.group_var.set('(No Grouping)')

    def _create_interface(self):
        # ============ TOP BANNER ============
        header = tk.Frame(self.window, bg="#3498db", height=45)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="🎲", font=("Arial", 18),
                bg="#3498db", fg="white").pack(side=tk.LEFT, padx=10)
        tk.Label(header, text="Generic Monte Carlo Uncertainty",
                font=("Arial", 14, "bold"), bg="#3498db", fg="white").pack(side=tk.LEFT, padx=5)

        self.status_indicator = tk.Label(header, text="● READY",
                                        font=("Arial", 8, "bold"),
                                        bg="#3498db", fg="#2ecc71")
        self.status_indicator.pack(side=tk.RIGHT, padx=15)

        # ============ MAIN CONTENT ============
        main_paned = tk.PanedWindow(self.window, orient=tk.HORIZONTAL,
                                   sashwidth=4, sashrelief=tk.RAISED)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # ============ LEFT PANEL - CONTROLS ============
        left_panel = tk.Frame(main_paned, bg="#ecf0f1", relief=tk.RAISED, borderwidth=1)
        main_paned.add(left_panel, width=350)

        # ---------- Variable Selection ----------
        var_frame = tk.LabelFrame(left_panel, text="📊 VARIABLE SELECTION",
                                  font=("Arial", 9, "bold"),
                                  bg="#ecf0f1", padx=8, pady=6)
        var_frame.pack(fill=tk.X, padx=8, pady=8)

        # X variable
        x_row = tk.Frame(var_frame, bg="#ecf0f1")
        x_row.pack(fill=tk.X, pady=4)
        tk.Label(x_row, text="X variable:", font=("Arial", 8, "bold"),
                bg="#ecf0f1", width=12, anchor=tk.W).pack(side=tk.LEFT)
        self.x_combo = ttk.Combobox(x_row, textvariable=self.x_var, state="readonly", width=15)
        self.x_combo.pack(side=tk.LEFT, padx=5)

        # Y variable
        y_row = tk.Frame(var_frame, bg="#ecf0f1")
        y_row.pack(fill=tk.X, pady=4)
        tk.Label(y_row, text="Y variable:", font=("Arial", 8, "bold"),
                bg="#ecf0f1", width=12, anchor=tk.W).pack(side=tk.LEFT)
        self.y_combo = ttk.Combobox(y_row, textvariable=self.y_var, state="readonly", width=15)
        self.y_combo.pack(side=tk.LEFT, padx=5)

        # Group column
        group_row = tk.Frame(var_frame, bg="#ecf0f1")
        group_row.pack(fill=tk.X, pady=4)
        tk.Label(group_row, text="Group by:", font=("Arial", 8, "bold"),
                bg="#ecf0f1", width=12, anchor=tk.W).pack(side=tk.LEFT)
        self.group_combo = ttk.Combobox(group_row, textvariable=self.group_var, state="readonly", width=15)
        self.group_combo.pack(side=tk.LEFT, padx=5)

        # Error info
        err_info = tk.Frame(var_frame, bg="#ecf0f1")
        err_info.pack(fill=tk.X, pady=6)
        tk.Label(err_info, text="Error estimation: 5% of value if no explicit error column",
                font=("Arial", 7, "italic"), bg="#ecf0f1", fg="#7f8c8d").pack(anchor=tk.W)

        # ---------- Monte Carlo Settings ----------
        mc_frame = tk.LabelFrame(left_panel, text="🎲 MONTE CARLO SETTINGS",
                                font=("Arial", 9, "bold"),
                                bg="#ecf0f1", padx=8, pady=6)
        mc_frame.pack(fill=tk.X, padx=8, pady=8)

        # Iterations
        iter_row = tk.Frame(mc_frame, bg="#ecf0f1")
        iter_row.pack(fill=tk.X, pady=4)
        tk.Label(iter_row, text="Iterations:", font=("Arial", 8, "bold"),
                bg="#ecf0f1").pack(side=tk.LEFT, padx=2)
        iter_combo = ttk.Combobox(iter_row,
                                 values=['1000', '5000', '10000', '25000', '50000'],
                                 textvariable=self.iterations_var, width=8, state="readonly")
        iter_combo.pack(side=tk.LEFT, padx=5)

        # Fast mode
        fast_row = tk.Frame(mc_frame, bg="#ecf0f1")
        fast_row.pack(fill=tk.X, pady=2)
        tk.Checkbutton(fast_row, text="⚡ Fast Mode (1,000 iterations, ~10x faster)",
                      variable=self.fast_mode_var,
                      font=("Arial", 8, "bold"),
                      bg="#ecf0f1", fg="#e67e22").pack(anchor=tk.W, padx=2)
        tk.Label(fast_row, text="   Recommended for >100 samples",
                font=("Arial", 7, "italic"), bg="#ecf0f1", fg="#7f8c8d").pack(anchor=tk.W, padx=20)

        # Confidence level
        conf_row = tk.Frame(mc_frame, bg="#ecf0f1")
        conf_row.pack(fill=tk.X, pady=4)
        tk.Label(conf_row, text="Confidence:", font=("Arial", 8, "bold"),
                bg="#ecf0f1").pack(side=tk.LEFT, padx=2)
        conf_combo = ttk.Combobox(conf_row,
                                 values=['90', '95', '99'],
                                 textvariable=self.confidence_level_var, width=6, state="readonly")
        conf_combo.pack(side=tk.LEFT, padx=5)
        tk.Label(conf_row, text="% CI", font=("Arial", 8),
                bg="#ecf0f1").pack(side=tk.LEFT, padx=2)

        # Distribution (keep as normal only for simplicity)
        dist_row = tk.Frame(mc_frame, bg="#ecf0f1")
        dist_row.pack(fill=tk.X, pady=4)
        tk.Label(dist_row, text="Distribution:", font=("Arial", 8, "bold"),
                bg="#ecf0f1").pack(side=tk.LEFT, padx=2)
        tk.Label(dist_row, text="Normal", font=("Arial", 8),
                bg="#ecf0f1", fg="#2c3e50").pack(side=tk.LEFT, padx=5)

        # ---------- Action Buttons ----------
        tk.Button(left_panel, text="🎲 RUN MONTE CARLO",
                 command=self._run_monte_carlo,
                 bg="#3498db", fg="white",
                 font=("Arial", 12, "bold"),
                 height=2, relief=tk.RAISED,
                 borderwidth=2).pack(fill=tk.X, padx=8, pady=8)

        # Export and Write-back buttons row
        button_row1 = tk.Frame(left_panel, bg="#ecf0f1")
        button_row1.pack(fill=tk.X, padx=8, pady=4)

        tk.Button(button_row1, text="📊 Export Ellipses",
                 command=self._export_ellipses,
                 bg="#27ae60", fg="white",
                 font=("Arial", 8), width=16).pack(side=tk.LEFT, padx=2)

        tk.Button(button_row1, text="📏 Export Sample CI",
                 command=self._export_sample_ci,
                 bg="#27ae60", fg="white",
                 font=("Arial", 8), width=16).pack(side=tk.RIGHT, padx=2)

        # NEW: Append to Main Table button
        button_row2 = tk.Frame(left_panel, bg="#ecf0f1")
        button_row2.pack(fill=tk.X, padx=8, pady=4)

        tk.Button(button_row2, text="📋 Append to Main Table",
                 command=self._append_to_main_table,
                 bg="#9b59b6", fg="white",
                 font=("Arial", 8, "bold"),
                 width=35).pack(pady=2)

        # ============ RIGHT PANEL - RESULTS ============
        right_panel = tk.Frame(main_paned, bg="white", relief=tk.RAISED, borderwidth=1)
        main_paned.add(right_panel, width=600)

        # Notebook for multiple result views
        notebook = ttk.Notebook(right_panel)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Tab 1: Confidence Ellipses
        ellipse_frame = tk.Frame(notebook, bg="white")
        notebook.add(ellipse_frame, text="📈 Confidence Ellipses")

        self.ellipse_canvas_frame = tk.Frame(ellipse_frame, bg="white")
        self.ellipse_canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.ellipse_placeholder = tk.Label(self.ellipse_canvas_frame,
                                           text="🎲 CONFIDENCE ELLIPSES\n\n"
                                                "Select variables and click RUN",
                                           font=("Arial", 10),
                                           bg="#f8f9fa", fg="#2c3e50",
                                           relief=tk.FLAT, pady=40)
        self.ellipse_placeholder.pack(fill=tk.BOTH, expand=True)

        # Tab 2: Numerical Results
        results_frame = tk.Frame(notebook, bg="white")
        notebook.add(results_frame, text="📋 Group Statistics")

        results_text_frame = tk.Frame(results_frame)
        results_text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        results_scroll = tk.Scrollbar(results_text_frame)
        results_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.results_text = tk.Text(results_text_frame, wrap=tk.WORD,
                                   font=("Courier", 9),
                                   yscrollcommand=results_scroll.set,
                                   bg="#f8f9fa", relief=tk.FLAT,
                                   padx=10, pady=10)
        self.results_text.pack(fill=tk.BOTH, expand=True)
        results_scroll.config(command=self.results_text.yview)

        # Tab 3: How to Interpret
        info_frame = tk.Frame(notebook, bg="white")
        notebook.add(info_frame, text="ℹ️ Help")

        info_text = tk.Text(info_frame, wrap=tk.WORD,
                           font=("Arial", 10),
                           bg="white", relief=tk.FLAT,
                           padx=20, pady=20)
        info_text.pack(fill=tk.BOTH, expand=True)

        explanation = """🎲 GENERIC MONTE CARLO UNCERTAINTY v2.1
═══════════════════════════════════════════════════════

HOW IT WORKS
───────────────────────────────────────────────────────
1. Select two numeric columns (X and Y) from your data.
2. Optionally choose a grouping column (e.g., Experiment, Device).
3. For each group, Monte Carlo:
   • Perturbs every sample's X and Y values according to their errors
     (errors are taken from _error/_std columns or estimated as 5%).
   • For each iteration, computes the group mean (X̄, Ȳ).
   • After many iterations, we have a cloud of possible group means.
4. A 95% confidence ellipse is drawn around this cloud.
   → The true population mean lies inside the ellipse with 95% confidence.

INTERPRETATION
───────────────────────────────────────────────────────
• Non‑overlapping ellipses → groups are STATISTICALLY DISTINCT.
• Overlapping ellipses → means are NOT significantly different.
• Ellipse size reflects uncertainty (more samples → smaller ellipse).

EXPORT
───────────────────────────────────────────────────────
• Export ellipses as CSV (group parameters).
• Export sample confidence intervals (per‑sample CIs).

APPEND TO MAIN TABLE (NEW)
───────────────────────────────────────────────────────
• Writes per‑sample confidence intervals back to the main data table.
• Also adds group ellipse parameters and group name to each sample.
• Use this to integrate uncertainty results into your main workflow.
"""
        info_text.insert('1.0', explanation)
        info_text.config(state=tk.DISABLED)

        # ============ BOTTOM STATUS BAR ============
        status_bar = tk.Frame(self.window, bg="#ecf0f1", height=30)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        status_bar.pack_propagate(False)

        self.stats_label = tk.Label(status_bar,
                                   text="Ready - Select variables and click RUN",
                                   font=("Arial", 8),
                                   bg="#ecf0f1", fg="#2c3e50")
        self.stats_label.pack(side=tk.LEFT, padx=10)

        sample_count = len(self.app.samples) if self.app.samples else 0
        tk.Label(status_bar, text=f"📊 {sample_count} samples loaded",
                font=("Arial", 7), bg="#ecf0f1", fg="#7f8c8d").pack(side=tk.RIGHT, padx=10)

    # ============ MONTE CARLO ENGINE ============
    def _run_monte_carlo(self):
        """Run Monte Carlo simulation on current data source (internal or external)."""
        # ============ DETERMINE DATA SOURCE ============
        if self.external_data is not None:
            samples = self.external_data
            source_type = "external"
        else:
            if not self.app.samples:
                messagebox.showwarning("No Data", "Load samples first!")
                return
            samples = self.app.samples
            source_type = "internal"

        # ============ VALIDATE SELECTIONS ============
        x_col = self.x_var.get()
        y_col = self.y_var.get()
        if not x_col or not y_col:
            messagebox.showwarning("Missing Selection", "Please select X and Y columns.")
            return

        # ============ MONTE CARLO SETTINGS ============
        if self.fast_mode_var.get():
            n_iter = 1000
            mode_text = "FAST MODE (1,000 iterations)"
        else:
            n_iter = int(self.iterations_var.get())
            mode_text = f"{n_iter:,} iterations"

        confidence = float(self.confidence_level_var.get()) / 100

        # ============ GROUP SAMPLES ============
        group_col = self.group_var.get()
        if group_col == "(No Grouping)":
            groups = {"All Samples": samples}
        else:
            groups = {}
            for sample in samples:
                group_val = str(sample.get(group_col, "Unspecified"))
                groups.setdefault(group_val, []).append(sample)

        # ============ FILTER VALID GROUPS ============
        min_samples = 2
        valid_groups = {}
        for name, group_samples in groups.items():
            # Count samples with valid X and Y
            valid_count = 0
            for s in group_samples:
                x_val, _, _ = self._get_value_and_error(s, x_col)
                y_val, _, _ = self._get_value_and_error(s, y_col)
                if x_val is not None and y_val is not None:
                    valid_count += 1
            if valid_count >= min_samples:
                valid_groups[name] = group_samples

        if not valid_groups:
            messagebox.showerror("Insufficient Data",
                               "No group has at least 2 samples with valid X,Y data.")
            return

        # ============ UPDATE UI ============
        source_display = "📤 External" if source_type == "external" else "📥 Main Table"
        self.status_indicator.config(text="● RUNNING", fg="#f39c12")
        self.stats_label.config(text=f"{source_display} • Running {mode_text}...")
        self.window.update()

        # Show progress window for large jobs
        if len(valid_groups) > 5 or n_iter >= 10000:
            self._show_progress(len(valid_groups), n_iter)

        # ============ RESET RESULTS ============
        self.group_results = {}
        self.sample_results = {}

        try:
            # ============ PROCESS EACH GROUP ============
            for g_idx, (group_name, group_samples) in enumerate(valid_groups.items()):
                # Prepare data: for each sample, get X, Y, and errors
                sample_data = []
                for sample in group_samples:
                    x_val, x_err, x_est = self._get_value_and_error(sample, x_col)
                    y_val, y_err, y_est = self._get_value_and_error(sample, y_col)
                    if x_val is not None and y_val is not None:
                        sample_data.append({
                            'sample': sample,
                            'x': x_val,
                            'y': y_val,
                            'x_err': x_err,
                            'y_err': y_err,
                            'x_est': x_est,  # Flag if error was estimated
                            'y_est': y_est
                        })

                if len(sample_data) < min_samples:
                    continue

                # Monte Carlo for this group
                group_x_means = []
                group_y_means = []
                # Store per‑sample perturbed values for CI calculation
                per_sample_x = [[] for _ in range(len(sample_data))]
                per_sample_y = [[] for _ in range(len(sample_data))]

                for it in range(n_iter):
                    # Perturb each sample
                    x_perturbed = []
                    y_perturbed = []
                    for i, s in enumerate(sample_data):
                        x_pert = np.random.normal(s['x'], s['x_err'])
                        y_pert = np.random.normal(s['y'], s['y_err'])
                        x_perturbed.append(x_pert)
                        y_perturbed.append(y_pert)
                        per_sample_x[i].append(x_pert)
                        per_sample_y[i].append(y_pert)

                    # Group mean
                    group_x_means.append(np.mean(x_perturbed))
                    group_y_means.append(np.mean(y_perturbed))

                    if (it + 1) % 1000 == 0:
                        self._update_progress(g_idx, len(valid_groups), it + 1)

                # ============ COMPUTE ELLIPSE PARAMETERS ============
                points = np.column_stack([group_x_means, group_y_means])
                center = np.mean(points, axis=0)
                cov = np.cov(points, rowvar=False)
                chi2_val = chi2.ppf(confidence, df=2)

                eigenvalues, eigenvectors = np.linalg.eigh(cov)
                order = eigenvalues.argsort()[::-1]
                eigenvalues = eigenvalues[order]
                eigenvectors = eigenvectors[:, order]

                width = 2 * np.sqrt(chi2_val * eigenvalues[0])
                height = 2 * np.sqrt(chi2_val * eigenvalues[1])
                angle = np.degrees(np.arctan2(eigenvectors[1, 0], eigenvectors[0, 0]))

                # Store group results
                self.group_results[group_name] = {
                    'center': center,
                    'cov': cov,
                    'width': width,
                    'height': height,
                    'angle': angle,
                    'n_samples': len(sample_data),
                    'x_mean': center[0],
                    'y_mean': center[1],
                    'x_std': np.sqrt(cov[0,0]),
                    'y_std': np.sqrt(cov[1,1]),
                    'correlation': cov[0,1] / (np.sqrt(cov[0,0]*cov[1,1])) if cov[0,0]*cov[1,1] > 0 else 0,
                    'estimated_errors': any(s['x_est'] or s['y_est'] for s in sample_data)
                }

                # Store per‑sample distributions with CIs
                for i, s in enumerate(sample_data):
                    # Try to get a meaningful sample ID
                    sample_id = s['sample'].get('Sample_ID', None)
                    if not sample_id:
                        sample_id = s['sample'].get('id', None)
                    if not sample_id:
                        sample_id = f"{group_name}_{i}"

                    self.sample_results[sample_id] = {
                        'x_mean': s['x'],
                        'x_err': s['x_err'],
                        'y_mean': s['y'],
                        'y_err': s['y_err'],
                        'x_ci': (np.percentile(per_sample_x[i], (1-confidence)*100/2),
                                 np.percentile(per_sample_x[i], 100 - (1-confidence)*100/2)),
                        'y_ci': (np.percentile(per_sample_y[i], (1-confidence)*100/2),
                                 np.percentile(per_sample_y[i], 100 - (1-confidence)*100/2)),
                        'group': group_name,
                        'estimated_x': s['x_est'],
                        'estimated_y': s['y_est']
                    }

            # ============ CLEANUP AND DISPLAY ============
            self._close_progress()
            self._plot_ellipses()
            self._update_results_text()

            # Show source in status
            source_tag = "EXTERNAL" if source_type == "external" else "MAIN TABLE"
            error_note = " (some errors estimated)" if any(
                g.get('estimated_errors', False) for g in self.group_results.values()
            ) else ""

            self.status_indicator.config(text=f"● {source_tag}", fg="#2ecc71")
            self.stats_label.config(
                text=f"{source_tag} • {mode_text} • {len(self.group_results)} groups • {confidence*100:.0f}% CI{error_note}"
            )

        except Exception as e:
            self._close_progress()
            self.status_indicator.config(text="● ERROR", fg="#e74c3c")
            self.stats_label.config(text=f"Error: {str(e)[:50]}")
            messagebox.showerror("Monte Carlo Error", str(e))
            import traceback
            traceback.print_exc()

    def _plot_ellipses(self):
        """Plot confidence ellipses for each group."""
        for widget in self.ellipse_canvas_frame.winfo_children():
            widget.destroy()

        if not self.group_results:
            self.ellipse_placeholder = tk.Label(self.ellipse_canvas_frame,
                                               text="No groups to display.\nRun Monte Carlo first.",
                                               font=("Arial", 10), bg="#f8f9fa")
            self.ellipse_placeholder.pack(fill=tk.BOTH, expand=True)
            return

        if not HAS_MATPLOTLIB:
            text_widget = tk.Text(self.ellipse_canvas_frame, wrap=tk.WORD,
                                 font=("Courier", 9), bg="#f8f9fa",
                                 padx=10, pady=10)
            text_widget.pack(fill=tk.BOTH, expand=True)
            text_widget.insert(tk.END, "📈 CONFIDENCE ELLIPSES (matplotlib not available)\n\n")
            for name, ellipse in self.group_results.items():
                text_widget.insert(tk.END, f"{name}:\n")
                text_widget.insert(tk.END, f"  Center: X={ellipse['x_mean']:.3f}, Y={ellipse['y_mean']:.3f}\n")
                text_widget.insert(tk.END, f"  Width={ellipse['width']:.3f}, Height={ellipse['height']:.3f}\n")
                text_widget.insert(tk.END, f"  Angle={ellipse['angle']:.1f}°, n={ellipse['n_samples']}\n\n")
            text_widget.config(state=tk.DISABLED)
            return

        try:
            fig, ax = plt.subplots(figsize=(6.5, 5.5), dpi=100)

            colors = plt.cm.tab10(np.linspace(0, 1, len(self.group_results)))

            for (name, ellipse), color in zip(self.group_results.items(), colors):
                ell = Ellipse(
                    xy=ellipse['center'],
                    width=ellipse['width'],
                    height=ellipse['height'],
                    angle=ellipse['angle'],
                    facecolor=color,
                    alpha=0.15,
                    edgecolor=color,
                    linewidth=2,
                    label=f"{name} (n={ellipse['n_samples']})"
                )
                ax.add_patch(ell)
                ax.scatter(ellipse['center'][0], ellipse['center'][1],
                          c=[color], s=100, edgecolors='white', linewidth=2, zorder=5)

            ax.set_xlabel(self.x_var.get(), fontsize=11, fontweight='bold')
            ax.set_ylabel(self.y_var.get(), fontsize=11, fontweight='bold')
            ax.set_title(f"{self.confidence_level_var.get()}% Confidence Ellipses\nPopulation means",
                        fontsize=11, fontweight='bold', pad=15)

            ax.legend(loc='best', fontsize=8)
            ax.grid(True, alpha=0.2, linestyle='--')

            plt.tight_layout()

            canvas = FigureCanvasTkAgg(fig, self.ellipse_canvas_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        except Exception as e:
            error_label = tk.Label(self.ellipse_canvas_frame,
                                  text=f"⚠️ Plot error: {str(e)[:100]}",
                                  font=("Arial", 9), fg="#e74c3c")
            error_label.pack(fill=tk.BOTH, expand=True)

    def _update_results_text(self):
        """Display numerical results in the text widget."""
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)

        self.results_text.insert(tk.END, "📊 GROUP CONFIDENCE ELLIPSES\n")
        self.results_text.insert(tk.END, "═" * 70 + "\n\n")

        mode = "FAST" if self.fast_mode_var.get() else f"{self.iterations_var.get()} iters"
        self.results_text.insert(tk.END, f"Monte Carlo • {mode} • {self.confidence_level_var.get()}% CI\n\n")

        for name, ellipse in self.group_results.items():
            self.results_text.insert(tk.END, f"Group: {name}\n")
            self.results_text.insert(tk.END, f"  Samples: {ellipse['n_samples']}\n")
            self.results_text.insert(tk.END, f"  Center: X={ellipse['x_mean']:.4f}, Y={ellipse['y_mean']:.4f}\n")
            self.results_text.insert(tk.END, f"  Std dev: X±{ellipse['x_std']:.4f}, Y±{ellipse['y_std']:.4f}\n")
            self.results_text.insert(tk.END, f"  Correlation: {ellipse['correlation']:.3f}\n")
            self.results_text.insert(tk.END, f"  Ellipse: width={ellipse['width']:.4f}, height={ellipse['height']:.4f}, angle={ellipse['angle']:.1f}°\n\n")

        self.results_text.config(state=tk.DISABLED)

    # ============ EXPORT FUNCTIONS ============
    def _export_ellipses(self):
        """Export ellipse parameters to CSV."""
        if not self.group_results:
            messagebox.showwarning("No Data", "Run Monte Carlo first!")
            return

        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile=f"ellipses_{datetime.now().strftime('%Y%m%d')}.csv"
        )
        if not filename:
            return

        try:
            import csv
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Group', 'N_Samples', 'X_Mean', 'Y_Mean', 'X_Std', 'Y_Std',
                                 'Correlation', 'Ellipse_Width', 'Ellipse_Height', 'Ellipse_Angle',
                                 'Confidence_%'])
                conf = self.confidence_level_var.get()
                for name, ell in self.group_results.items():
                    writer.writerow([
                        name,
                        ell['n_samples'],
                        f"{ell['x_mean']:.6f}",
                        f"{ell['y_mean']:.6f}",
                        f"{ell['x_std']:.6f}",
                        f"{ell['y_std']:.6f}",
                        f"{ell['correlation']:.6f}",
                        f"{ell['width']:.6f}",
                        f"{ell['height']:.6f}",
                        f"{ell['angle']:.6f}",
                        conf
                    ])
            messagebox.showinfo("Export Complete", f"Exported {len(self.group_results)} groups.")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def _export_sample_ci(self):
        """Export per‑sample confidence intervals to CSV."""
        if not self.sample_results:
            messagebox.showwarning("No Data", "Run Monte Carlo first!")
            return

        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile=f"sample_CI_{datetime.now().strftime('%Y%m%d')}.csv"
        )
        if not filename:
            return

        try:
            import csv
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Sample_ID', 'Group', 'X_Mean', 'X_Error', 'X_CI_Lower', 'X_CI_Upper',
                                 'Y_Mean', 'Y_Error', 'Y_CI_Lower', 'Y_CI_Upper'])
                for sid, vals in self.sample_results.items():
                    writer.writerow([
                        sid,
                        vals.get('group', ''),
                        f"{vals['x_mean']:.6f}",
                        f"{vals['x_err']:.6f}",
                        f"{vals['x_ci'][0]:.6f}",
                        f"{vals['x_ci'][1]:.6f}",
                        f"{vals['y_mean']:.6f}",
                        f"{vals['y_err']:.6f}",
                        f"{vals['y_ci'][0]:.6f}",
                        f"{vals['y_ci'][1]:.6f}"
                    ])
            messagebox.showinfo("Export Complete", f"Exported {len(self.sample_results)} samples.")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    # ============ NEW: APPEND TO MAIN TABLE ============
    def _append_to_main_table(self):
        """Write Monte Carlo results back to the main application's samples."""
        if not self.sample_results:
            messagebox.showwarning("No Data", "Run Monte Carlo first!")
            return

        # Confirm with user
        if not messagebox.askyesno(
            "Append to Main Table",
            f"This will add the following columns to your main data table:\n"
            f"• X_CI_lower, X_CI_upper\n"
            f"• Y_CI_lower, Y_CI_upper\n"
            f"• Group_Name\n"
            f"• Group_Ellipse_Center_X, Group_Ellipse_Center_Y\n"
            f"• Group_Ellipse_Width, Group_Ellipse_Height, Group_Ellipse_Angle\n\n"
            f"Existing data will NOT be overwritten. Proceed?"
        ):
            return

        # Map sample IDs to results
        # We need to identify each sample in self.app.samples uniquely.
        # The plugin stores results by Sample_ID. If multiple samples have the same ID, this will overwrite.
        # We'll use the sample's position in the list as fallback, but best practice: use a unique key.
        # Here we assume Sample_ID is unique. If not, we may need to enhance.
        updated_count = 0
        for sample in self.app.samples:
            sample_id = sample.get('Sample_ID', None)
            if sample_id and sample_id in self.sample_results:
                res = self.sample_results[sample_id]
                # Add confidence intervals
                sample['X_CI_lower'] = res['x_ci'][0]
                sample['X_CI_upper'] = res['x_ci'][1]
                sample['Y_CI_lower'] = res['y_ci'][0]
                sample['Y_CI_upper'] = res['y_ci'][1]
                # Add group name
                sample['Group_Name'] = res.get('group', '')
                updated_count += 1

        # Also add group ellipse parameters to each sample (based on its group)
        # We need to know which group each sample belongs to. We stored 'group' in sample_results.
        # For samples that were not in any group (e.g., insufficient data), we skip.
        for sample in self.app.samples:
            group_name = sample.get('Group_Name', '')
            if group_name and group_name in self.group_results:
                ell = self.group_results[group_name]
                sample['Group_Ellipse_Center_X'] = ell['x_mean']
                sample['Group_Ellipse_Center_Y'] = ell['y_mean']
                sample['Group_Ellipse_Width'] = ell['width']
                sample['Group_Ellipse_Height'] = ell['height']
                sample['Group_Ellipse_Angle'] = ell['angle']
            else:
                # Optionally set to empty
                sample['Group_Ellipse_Center_X'] = ''
                sample['Group_Ellipse_Center_Y'] = ''
                sample['Group_Ellipse_Width'] = ''
                sample['Group_Ellipse_Height'] = ''
                sample['Group_Ellipse_Angle'] = ''

        # Notify main app that data has changed (if it has a refresh method)
        if hasattr(self.app, 'refresh_table'):
            self.app.refresh_table()
        elif hasattr(self.app, 'update_table_display'):
            self.app.update_table_display()
        # If no refresh method, at least print a message
        else:
            print("Main table updated. Please refresh manually if needed.")

        messagebox.showinfo(
            "Append Complete",
            f"Added uncertainty columns to {updated_count} samples.\n"
            f"Group ellipse parameters added to all samples."
        )


def setup_plugin(main_app):
    """Plugin entry point."""
    return GenericUncertaintyPlugin(main_app)
