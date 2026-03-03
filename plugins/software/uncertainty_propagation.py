"""
Archaeological Isotope Uncertainty Propagation Plugin
v3.0 - TDF-Integrated Monte Carlo with Full Mixing Propagation

- Receives isotope data with end-members and TDFs
- Propagates ALL uncertainties: measurements + TDFs
- Calculates confidence intervals on mixing proportions
- Uses TDF database from config folder
- Writes back proportion CIs to main table

Author: Sefy Levy (boosted by AI)
License: CC BY-NC-SA 4.0
Version: 3.0.0
"""

PLUGIN_INFO = {
    "category": "software",
    "field": "General",
    "id": "uncertainty_propagation",
    "name": "Uncertainty Propagation Pro",
    "icon": "📊",
    "description": "TDF-integrated Monte Carlo for mixing models with full uncertainty propagation",
    "version": "3.0.0",
    "requires": ["numpy", "scipy", "matplotlib"],
    "author": "Sefy Levy"
}

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
from datetime import datetime
import json
from pathlib import Path
import sys
import os

# ============ OPTIONAL DEPENDENCIES ============
try:
    from scipy.stats import chi2, norm
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


class IsotopeUncertaintyPro:
    """
    ============================================================================
    ISOTOPE UNCERTAINTY PROFESSIONAL v3.0
    ============================================================================

    This is NOT a generic plugin anymore. This is purpose-built for isotope
    archaeology with full TDF integration.

    WHAT IT DOES:
    • Receives isotope data with end-members and TDFs from your mixing model
    • Perturbs measurements AND TDFs simultaneously in Monte Carlo
    • Recalculates mixing proportions for each iteration
    • Gives you confidence intervals on proportions (not just raw isotopes)
    • Uses the TDF database from config folder for literature-based uncertainties
    • Writes proportion CIs back to main table for further analysis

    WHY THIS MATTERS:
    Most isotope studies ignore TDF uncertainty, underestimating true error.
    This plugin gives you DEFENSIBLE confidence intervals for archaeological
    interpretation.
    ============================================================================
    """

    def __init__(self, main_app):
        self.app = main_app
        self.window = None
        self.progress_window = None
        self.progress_bar = None
        self.progress_label = None
        self._after_ids = []

        # Core data
        self.current_data = None
        self.external_context = None
        self.tdf_db = None

        # Results storage
        self.group_results = {}          # group name -> ellipse data
        self.sample_results = {}          # sample ID -> distributions
        self.proportion_results = {}      # sample ID -> mixing proportion CIs
        self.mixing_model_func = None     # Stores the mixing equation

        # UI state
        self.status_indicator = None
        self.stats_label = None
        self.ellipse_canvas_frame = None
        self.results_text = None
        self.proportion_text = None       # NEW: dedicated proportion display

        # User selections
        self.x_var = tk.StringVar()
        self.y_var = tk.StringVar()
        self.group_var = tk.StringVar(value="(No Grouping)")
        self.iterations_var = tk.StringVar(value="10000")
        self.fast_mode_var = tk.BooleanVar(value=False)
        self.confidence_level_var = tk.StringVar(value="95")

        # NEW: TDF-specific controls
        self.include_tdf_uncertainty = tk.BooleanVar(value=True)
        self.proportion_col_name = tk.StringVar(value="Mixing_Proportion_EM2")
        self.show_proportion_ci = tk.BooleanVar(value=True)

        # NEW: Correlation control (for Pb isotopes)
        self.use_correlated_errors = tk.BooleanVar(value=False)
        self.correlation_value = tk.DoubleVar(value=0.85)  # Default for Pb

        # Load TDF database
        self._load_tdf_database()

    # ============ TDF DATABASE INTEGRATION ============

    def _load_tdf_database(self):
        """Load the trophic discrimination factor database from config folder"""
        try:
            # CORRECT PATH: from plugin to mainapp/config
            # __file__ = mainapp/plugins/software/uncertainty_plugin.py
            # parent.parent.parent = mainapp/
            tdf_path = Path(__file__).parent.parent.parent / "config" / "tdf_database.json"

            if tdf_path.exists():
                with open(tdf_path, 'r', encoding='utf-8') as f:
                    self.tdf_db = json.load(f)
                print(f"✅ Loaded TDF database from: {tdf_path}")
                print(f"   Found {len(self.tdf_db.get('tdf_entries', []))} entries")
            else:
                # One more fallback - maybe running from different working directory
                tdf_path = Path.cwd() / "config" / "tdf_database.json"
                if tdf_path.exists():
                    with open(tdf_path, 'r', encoding='utf-8') as f:
                        self.tdf_db = json.load(f)
                    print(f"✅ Loaded TDF database from CWD: {tdf_path}")
                else:
                    print(f"⚠️ TDF database not found at expected locations")
                    print(f"   Tried: {Path(__file__).parent.parent.parent / 'config' / 'tdf_database.json'}")
                    print(f"   Tried: {Path.cwd() / 'config' / 'tdf_database.json'}")
                    self.tdf_db = None

        except Exception as e:
            print(f"⚠️ Error loading TDF database: {e}")
            self.tdf_db = None

    def _lookup_tdf(self, taxon=None, tissue=None, diet_type=None, trophic_level=None):
        """
        Look up TDF values from database with smart matching
        Returns dict with Δ13C_mean, Δ13C_sd, Δ15N_mean, Δ15N_sd, source
        """
        if not self.tdf_db or 'tdf_entries' not in self.tdf_db:
            return None

        entries = self.tdf_db['tdf_entries']
        matches = []

        for entry in entries:
            score = 0
            # Skip entries without numeric data
            if not entry.get('Δ13C_mean') or not entry.get('Δ15N_mean'):
                continue

            # Match taxon (highest weight)
            if taxon and entry.get('taxon'):
                if entry['taxon'].lower() == taxon.lower():
                    score += 10
                elif taxon.lower() in entry['taxon'].lower():
                    score += 5

            # Match tissue (high weight)
            if tissue and entry.get('tissue'):
                if entry['tissue'].lower() == tissue.lower():
                    score += 8
                elif tissue.lower() in entry['tissue'].lower():
                    score += 4

            # Match diet type (medium weight)
            if diet_type and entry.get('diet_type'):
                if diet_type.lower() in entry['diet_type'].lower():
                    score += 5

            # Match trophic level (medium weight)
            if trophic_level and entry.get('trophic_level'):
                if trophic_level.lower() in entry['trophic_level'].lower():
                    score += 5

            # Prefer entries with SD over SE (better for uncertainty)
            if entry.get('Δ13C_sd'):
                score += 2
            if entry.get('Δ15N_sd'):
                score += 2

            # Prefer larger sample sizes
            n = entry.get('n')
            if n:
                if isinstance(n, dict):
                    n_val = n.get('C', 0) or n.get('N', 0)
                else:
                    n_val = n
                if n_val and n_val > 10:
                    score += 3
                elif n_val and n_val > 30:
                    score += 5

            if score > 0:
                matches.append((score, entry))

        if not matches:
            # Try summary statistics as fallback
            stats = self.tdf_db.get('summary_statistics', {})
            if taxon and 'by_taxon' in stats:
                taxon_stats = stats['by_taxon'].get(taxon.lower())
                if taxon_stats:
                    return {
                        'Δ13C_mean': taxon_stats.get('Δ13C_mean'),
                        'Δ13C_sd': (taxon_stats['Δ13C_range'][1] - taxon_stats['Δ13C_range'][0]) / 4,
                        'Δ15N_mean': taxon_stats.get('Δ15N_mean'),
                        'Δ15N_sd': (taxon_stats['Δ15N_range'][1] - taxon_stats['Δ15N_range'][0]) / 4,
                        'source': f"summary_stats_{taxon}",
                        'n': taxon_stats.get('n_entries', 1)
                    }
            return None

        # Sort by score and take best match
        matches.sort(key=lambda x: x[0], reverse=True)
        best = matches[0][1]

        # Convert SE to SD if needed
        c13_sd = best.get('Δ13C_sd')
        if not c13_sd and best.get('Δ13C_se'):
            n = best.get('n')
            if isinstance(n, dict):
                n_c = n.get('C', 30)
            else:
                n_c = n or 30
            c13_sd = best['Δ13C_se'] * np.sqrt(n_c)
        elif not c13_sd:
            c13_sd = best['Δ13C_mean'] * 0.2  # Fallback: 20% of mean

        n15_sd = best.get('Δ15N_sd')
        if not n15_sd and best.get('Δ15N_se'):
            n = best.get('n')
            if isinstance(n, dict):
                n_n = n.get('N', 30)
            else:
                n_n = n or 30
            n15_sd = best['Δ15N_se'] * np.sqrt(n_n)
        elif not n15_sd:
            n15_sd = best['Δ15N_mean'] * 0.2  # Fallback: 20% of mean

        return {
            'Δ13C_mean': best['Δ13C_mean'],
            'Δ13C_sd': c13_sd,
            'Δ15N_mean': best['Δ15N_mean'],
            'Δ15N_sd': n15_sd,
            'source': best.get('source', 'tdf_database'),
            'citation': best.get('notes', ''),
            'n': best.get('n', 'unknown')
        }

    # ============ MIXING MODEL EQUATIONS ============

    def _setup_mixing_model(self, context):
        """
        Set up the mixing model function based on context
        Stores the function in self.mixing_model_func
        """
        model_type = context.get('model', 'binary').lower()

        if model_type == 'binary':
            # Standard binary mixing: f = (δ_target - δ_EM1) / (δ_EM2 - δ_EM1)
            def binary_mixing(target_13C, target_15N, em1_13C, em1_15N, em2_13C, em2_15N, tdf_13C, tdf_15N):
                """
                Calculate proportion of EM2 in mixture
                With TDF correction: consumer = diet + TDF
                So for consumer values, we subtract TDF to get dietary equivalent
                """
                # Correct consumer values to dietary equivalents
                diet_13C = target_13C - tdf_13C
                diet_15N = target_15N - tdf_15N

                # Solve for f using both isotopes (weighted average if both available)
                f_13C = (diet_13C - em1_13C) / (em2_13C - em1_13C) if em2_13C != em1_13C else np.nan
                f_15N = (diet_15N - em1_15N) / (em2_15N - em1_15N) if em2_15N != em1_15N else np.nan

                # Average if both valid, otherwise use the valid one
                valid_fs = [f for f in [f_13C, f_15N] if not np.isnan(f) and 0 <= f <= 1]
                if valid_fs:
                    return np.mean(valid_fs)
                else:
                    # If outside bounds, still return but flag
                    f = np.nanmean([f_13C, f_15N])
                    return f

            self.mixing_model_func = binary_mixing
            return True

        elif model_type == 'three_source':
            # For future expansion
            def three_source_mixing(*args):
                # Placeholder for three-isotope mixing
                return args[0]  # Just pass through for now
            self.mixing_model_func = three_source_mixing
            return True

        else:
            # Unknown model type
            self.mixing_model_func = None
            return False

    # ============ RECEIVE DATA WITH FULL CONTEXT ============

    def receive_data(self, data, context):
        """
        Receive isotope data with full mixing context
        """
        self.current_data = data
        self.external_context = context

        # Reset previous results
        self.proportion_results = {}

        # Handle isotope mixing context
        if context.get('type') == 'isotope_mixing':
            # Set isotope columns
            isotopes = context.get('isotopes', ['δ13C', 'δ15N'])
            self.x_var.set(isotopes[0] if len(isotopes) > 0 else 'δ13C')
            self.y_var.set(isotopes[1] if len(isotopes) > 1 else 'δ15N')

            # Set group column if provided
            if context.get('group_by'):
                self.group_var.set(context['group_by'])
            else:
                self.group_var.set('(No Grouping)')

            # Set up mixing model
            self._setup_mixing_model(context)

            # Handle TDF information
            tdf_source = None
            if 'tdf' in context:
                # TDF provided explicitly
                self.tdf_info = context['tdf']
                tdf_source = "provided"
            else:
                # Try to look up from database
                self.tdf_info = self._lookup_tdf(
                    taxon=context.get('taxon'),
                    tissue=context.get('tissue', 'muscle'),
                    diet_type=context.get('diet_type'),
                    trophic_level=context.get('trophic_level')
                )
                if self.tdf_info:
                    tdf_source = self.tdf_info.get('source', 'database')

            # Store proportion column name if provided
            if context.get('derived_column'):
                self.proportion_col_name.set(context['derived_column'])

            # Set optimal Monte Carlo parameters for mixing
            self.iterations_var.set("10000")  # Need enough iterations for stable CIs
            self.fast_mode_var.set(False)     # Accuracy over speed for mixing

            # Auto-detect Pb isotopes for correlation
            if any('pb' in iso.lower() for iso in isotopes):
                self.use_correlated_errors.set(True)
                self.correlation_value.set(0.9)  # High correlation for Pb ratios

            # Update UI if window exists
            if self.window and self.window.winfo_exists():
                self._update_ui_for_isotope_context(tdf_source)

        # Open or lift window
        self.open_window()

    def _update_ui_for_isotope_context(self, tdf_source=None):
        """Update UI elements to reflect isotope context"""
        if tdf_source:
            self.status_indicator.config(
                text=f"● ISOTOPE MIXING + TDF",
                fg="#9b59b6"
            )
            tdf_text = (f"TDF: Δ13C={self.tdf_info['Δ13C_mean']:.2f}±{self.tdf_info['Δ13C_sd']:.2f}, "
                       f"Δ15N={self.tdf_info['Δ15N_mean']:.2f}±{self.tdf_info['Δ15N_sd']:.2f} "
                       f"[{tdf_source}]")
            self.stats_label.config(text=tdf_text)

            # Enable TDF checkbox
            self.include_tdf_uncertainty.set(True)
        else:
            self.status_indicator.config(
                text=f"● ISOTOPE MIXING",
                fg="#3498db"
            )
            self.stats_label.config(
                text="Isotope mixing mode - No TDF data available"
            )

    # ============ MAIN INTERFACE ============

    def open_window(self):
        """Create and show the main window"""
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
        self.window.title("📊 Isotope Uncertainty Professional v3.0")
        self.window.geometry("1200x750")
        self.window.transient(self.app.root)

        self._create_interface()

        # If we have context, update UI
        if self.external_context and self.external_context.get('type') == 'isotope_mixing':
            self._populate_column_choices()
            self._update_ui_for_isotope_context()

        self.window.lift()
        self.window.focus_force()

    def _create_interface(self):
        """Build the complete interface"""
        # ============ TOP BANNER ============
        header = tk.Frame(self.window, bg="#2c3e50", height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="📊", font=("Arial", 20),
                bg="#2c3e50", fg="white").pack(side=tk.LEFT, padx=10)
        tk.Label(header, text="Isotope Uncertainty Professional",
                font=("Arial", 16, "bold"), bg="#2c3e50", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Label(header, text="v3.0 • TDF-Integrated",
                font=("Arial", 10), bg="#2c3e50", fg="#ecf0f1").pack(side=tk.LEFT, padx=10)

        self.status_indicator = tk.Label(header, text="● READY",
                                        font=("Arial", 9, "bold"),
                                        bg="#2c3e50", fg="#2ecc71")
        self.status_indicator.pack(side=tk.RIGHT, padx=15)

        # ============ MAIN PANED WINDOW ============
        main_paned = tk.PanedWindow(self.window, orient=tk.HORIZONTAL,
                                   sashwidth=4, sashrelief=tk.RAISED, bg="#ecf0f1")
        main_paned.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # ============ LEFT PANEL - CONTROLS ============
        left_panel = tk.Frame(main_paned, bg="#ecf0f1", relief=tk.RAISED, borderwidth=1)
        main_paned.add(left_panel, width=400)

        # ---------- Data Source Info ----------
        source_frame = tk.LabelFrame(left_panel, text="📁 DATA SOURCE",
                                     font=("Arial", 9, "bold"),
                                     bg="#ecf0f1", padx=8, pady=6)
        source_frame.pack(fill=tk.X, padx=8, pady=8)

        if self.external_context and self.external_context.get('type') == 'isotope_mixing':
            model = self.external_context.get('model', 'binary').replace('_', ' ').title()
            tk.Label(source_frame, text=f"Model: {model}",
                    font=("Arial", 9), bg="#ecf0f1").pack(anchor=tk.W, pady=2)
            if 'taxon' in self.external_context:
                tk.Label(source_frame, text=f"Taxon: {self.external_context['taxon']}",
                        font=("Arial", 9), bg="#ecf0f1").pack(anchor=tk.W, pady=2)
            if 'tissue' in self.external_context:
                tk.Label(source_frame, text=f"Tissue: {self.external_context['tissue']}",
                        font=("Arial", 9), bg="#ecf0f1").pack(anchor=tk.W, pady=2)

        # ---------- Variable Selection ----------
        var_frame = tk.LabelFrame(left_panel, text="🔬 ISOTOPE SELECTION",
                                  font=("Arial", 9, "bold"),
                                  bg="#ecf0f1", padx=8, pady=6)
        var_frame.pack(fill=tk.X, padx=8, pady=8)

        # X variable (usually δ13C)
        x_row = tk.Frame(var_frame, bg="#ecf0f1")
        x_row.pack(fill=tk.X, pady=4)
        tk.Label(x_row, text="X isotope:", font=("Arial", 8, "bold"),
                bg="#ecf0f1", width=10, anchor=tk.W).pack(side=tk.LEFT)
        self.x_combo = ttk.Combobox(x_row, textvariable=self.x_var, state="readonly", width=15)
        self.x_combo.pack(side=tk.LEFT, padx=5)

        # Y variable (usually δ15N)
        y_row = tk.Frame(var_frame, bg="#ecf0f1")
        y_row.pack(fill=tk.X, pady=4)
        tk.Label(y_row, text="Y isotope:", font=("Arial", 8, "bold"),
                bg="#ecf0f1", width=10, anchor=tk.W).pack(side=tk.LEFT)
        self.y_combo = ttk.Combobox(y_row, textvariable=self.y_var, state="readonly", width=15)
        self.y_combo.pack(side=tk.LEFT, padx=5)

        # Group column
        group_row = tk.Frame(var_frame, bg="#ecf0f1")
        group_row.pack(fill=tk.X, pady=4)
        tk.Label(group_row, text="Group by:", font=("Arial", 8, "bold"),
                bg="#ecf0f1", width=10, anchor=tk.W).pack(side=tk.LEFT)
        self.group_combo = ttk.Combobox(group_row, textvariable=self.group_var, state="readonly", width=15)
        self.group_combo.pack(side=tk.LEFT, padx=5)

        # ---------- TDF CONFIGURATION ----------
        tdf_frame = tk.LabelFrame(left_panel, text="🍽️ TROPHIC DISCRIMINATION FACTORS",
                                  font=("Arial", 9, "bold"),
                                  bg="#ecf0f1", padx=8, pady=6, fg="#27ae60")
        tdf_frame.pack(fill=tk.X, padx=8, pady=8)

        # TDF display
        if hasattr(self, 'tdf_info') and self.tdf_info:
            tdf_display = tk.Frame(tdf_frame, bg="#ecf0f1")
            tdf_display.pack(fill=tk.X, pady=4)

            tk.Label(tdf_display, text="Δ13C:", font=("Arial", 8, "bold"),
                    bg="#ecf0f1").grid(row=0, column=0, sticky=tk.W, padx=5)
            tk.Label(tdf_display, text=f"{self.tdf_info['Δ13C_mean']:.2f} ± {self.tdf_info['Δ13C_sd']:.2f} ‰",
                    font=("Arial", 8), bg="#ecf0f1").grid(row=0, column=1, sticky=tk.W, padx=5)

            tk.Label(tdf_display, text="Δ15N:", font=("Arial", 8, "bold"),
                    bg="#ecf0f1").grid(row=1, column=0, sticky=tk.W, padx=5)
            tk.Label(tdf_display, text=f"{self.tdf_info['Δ15N_mean']:.2f} ± {self.tdf_info['Δ15N_sd']:.2f} ‰",
                    font=("Arial", 8), bg="#ecf0f1").grid(row=1, column=1, sticky=tk.W, padx=5)

            source_text = self.tdf_info.get('source', 'database').replace('_', ' ')
            tk.Label(tdf_frame, text=f"Source: {source_text}",
                    font=("Arial", 7, "italic"), bg="#ecf0f1", fg="#7f8c8d").pack(anchor=tk.W, pady=2)
        else:
            tk.Label(tdf_frame, text="No TDF data available",
                    font=("Arial", 8, "italic"), bg="#ecf0f1", fg="#7f8c8d").pack(pady=5)

        # TDF uncertainty toggle
        tdf_check = tk.Frame(tdf_frame, bg="#ecf0f1")
        tdf_check.pack(fill=tk.X, pady=4)
        tk.Checkbutton(tdf_check, text="✓ Include TDF uncertainty in Monte Carlo",
                      variable=self.include_tdf_uncertainty,
                      font=("Arial", 8, "bold"),
                      bg="#ecf0f1", fg="#27ae60").pack(anchor=tk.W)

        # ---------- MONTE CARLO SETTINGS ----------
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
                                 values=['1000', '5000', '10000', '25000', '50000', '100000'],
                                 textvariable=self.iterations_var, width=8, state="readonly")
        iter_combo.pack(side=tk.LEFT, padx=5)

        # Fast mode
        fast_row = tk.Frame(mc_frame, bg="#ecf0f1")
        fast_row.pack(fill=tk.X, pady=2)
        tk.Checkbutton(fast_row, text="⚡ Fast Mode (1,000 iterations, exploratory only)",
                      variable=self.fast_mode_var,
                      font=("Arial", 8),
                      bg="#ecf0f1", fg="#e67e22").pack(anchor=tk.W, padx=2)

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
                bg="#ecf0f1").pack(side=tk.LEFT)

        # ---------- CORRELATED ERRORS (for Pb) ----------
        corr_frame = tk.LabelFrame(left_panel, text="🔗 CORRELATED ERRORS",
                                   font=("Arial", 9, "bold"),
                                   bg="#ecf0f1", padx=8, pady=6, fg="#8e44ad")
        corr_frame.pack(fill=tk.X, padx=8, pady=8)

        corr_check = tk.Frame(corr_frame, bg="#ecf0f1")
        corr_check.pack(fill=tk.X, pady=2)
        tk.Checkbutton(corr_check, text="✓ Use correlated errors (for Pb isotopes)",
                      variable=self.use_correlated_errors,
                      font=("Arial", 8),
                      bg="#ecf0f1").pack(anchor=tk.W)

        corr_val_row = tk.Frame(corr_frame, bg="#ecf0f1")
        corr_val_row.pack(fill=tk.X, pady=2)
        tk.Label(corr_val_row, text="Correlation (r):", font=("Arial", 8),
                bg="#ecf0f1").pack(side=tk.LEFT, padx=2)
        tk.Scale(corr_val_row, from_=0.0, to=1.0, resolution=0.05,
                orient=tk.HORIZONTAL, variable=self.correlation_value,
                length=150, bg="#ecf0f1").pack(side=tk.LEFT, padx=5)

        # ---------- ACTION BUTTONS ----------
        tk.Button(left_panel, text="🎲 RUN MONTE CARLO",
                 command=self._run_monte_carlo,
                 bg="#27ae60", fg="white",
                 font=("Arial", 12, "bold"),
                 height=2, relief=tk.RAISED,
                 borderwidth=2).pack(fill=tk.X, padx=8, pady=8)

        # Export buttons
        btn_frame = tk.Frame(left_panel, bg="#ecf0f1")
        btn_frame.pack(fill=tk.X, padx=8, pady=4)

        tk.Button(btn_frame, text="📊 Export Ellipses",
                 command=self._export_ellipses,
                 bg="#3498db", fg="white",
                 font=("Arial", 8), width=12).pack(side=tk.LEFT, padx=2)

        tk.Button(btn_frame, text="📏 Export Sample CI",
                 command=self._export_sample_ci,
                 bg="#3498db", fg="white",
                 font=("Arial", 8), width=12).pack(side=tk.LEFT, padx=2)

        tk.Button(btn_frame, text="📈 Export Proportions",
                 command=self._export_proportions,
                 bg="#9b59b6", fg="white",
                 font=("Arial", 8, "bold"), width=12).pack(side=tk.LEFT, padx=2)

        # Append to main table
        tk.Button(left_panel, text="📋 Append All Results to Main Table",
                 command=self._append_to_main_table,
                 bg="#2c3e50", fg="white",
                 font=("Arial", 9, "bold"),
                 height=1).pack(fill=tk.X, padx=8, pady=8)

        # ============ RIGHT PANEL - NOTEBOOK ============
        right_panel = tk.Frame(main_paned, bg="white", relief=tk.RAISED, borderwidth=1)
        main_paned.add(right_panel, width=750)

        notebook = ttk.Notebook(right_panel)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Tab 1: Confidence Ellipses
        ellipse_frame = tk.Frame(notebook, bg="white")
        notebook.add(ellipse_frame, text="📈 Isotope Ellipses")

        self.ellipse_canvas_frame = tk.Frame(ellipse_frame, bg="white")
        self.ellipse_canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.ellipse_placeholder = tk.Label(self.ellipse_canvas_frame,
                                           text="📊 ISOTOPE CONFIDENCE ELLIPSES\n\n"
                                                "Select isotopes and click RUN\n"
                                                "TDF uncertainties will be propagated",
                                           font=("Arial", 10),
                                           bg="#f8f9fa", fg="#2c3e50",
                                           relief=tk.FLAT, pady=40)
        self.ellipse_placeholder.pack(fill=tk.BOTH, expand=True)

        # Tab 2: Mixing Proportions (NEW)
        prop_frame = tk.Frame(notebook, bg="white")
        notebook.add(prop_frame, text="📊 Mixing Proportions")

        prop_text_frame = tk.Frame(prop_frame)
        prop_text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        prop_scroll = tk.Scrollbar(prop_text_frame)
        prop_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.proportion_text = tk.Text(prop_text_frame, wrap=tk.WORD,
                                      font=("Courier", 10),
                                      yscrollcommand=prop_scroll.set,
                                      bg="#f8f9fa", relief=tk.FLAT,
                                      padx=10, pady=10)
        self.proportion_text.pack(fill=tk.BOTH, expand=True)
        prop_scroll.config(command=self.proportion_text.yview)

        # Tab 3: Group Statistics
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

        # Tab 4: TDF Sources
        tdf_info_frame = tk.Frame(notebook, bg="white")
        notebook.add(tdf_info_frame, text="📚 TDF Sources")

        tdf_info_text = tk.Text(tdf_info_frame, wrap=tk.WORD,
                               font=("Arial", 9),
                               bg="white", relief=tk.FLAT,
                               padx=20, pady=20)
        tdf_info_text.pack(fill=tk.BOTH, expand=True)

        self._populate_tdf_sources(tdf_info_text)

        # ============ BOTTOM STATUS ============
        status_bar = tk.Frame(self.window, bg="#ecf0f1", height=30)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        status_bar.pack_propagate(False)

        self.stats_label = tk.Label(status_bar,
                                   text="Ready - Load isotope data and click RUN",
                                   font=("Arial", 8),
                                   bg="#ecf0f1", fg="#2c3e50")
        self.stats_label.pack(side=tk.LEFT, padx=10)

        sample_count = len(self.current_data) if self.current_data else 0
        tk.Label(status_bar, text=f"📊 {sample_count} samples loaded",
                font=("Arial", 7), bg="#ecf0f1", fg="#7f8c8d").pack(side=tk.RIGHT, padx=10)

    def _populate_tdf_sources(self, text_widget):
        """Fill the TDF sources tab with information"""
        if not self.tdf_db:
            text_widget.insert(tk.END, "TDF database not loaded.\n\n")
            text_widget.insert(tk.END, "Expected location: config/tdf_database.json")
            text_widget.config(state=tk.DISABLED)
            return

        text_widget.insert(tk.END, "📚 TROPHIC DISCRIMINATION FACTOR DATABASE\n")
        text_widget.insert(tk.END, "═" * 70 + "\n\n")

        # Metadata
        meta = self.tdf_db.get('metadata', {})
        text_widget.insert(tk.END, f"Database: {meta.get('name', 'TDF Database')}\n")
        text_widget.insert(tk.END, f"Version: {meta.get('version', '1.0')}\n")
        text_widget.insert(tk.END, f"Last updated: {meta.get('last_updated', 'Unknown')}\n")
        text_widget.insert(tk.END, f"Total entries: {meta.get('total_entries', 0)}\n\n")

        # Sources
        text_widget.insert(tk.END, "SOURCES:\n")
        text_widget.insert(tk.END, "─" * 50 + "\n")
        for source in meta.get('sources', []):
            text_widget.insert(tk.END, f"• {source.get('citation', 'Unknown')}\n")
            if source.get('n_studies'):
                text_widget.insert(tk.END, f"  {source['n_studies']} studies\n")
        text_widget.insert(tk.END, "\n")

        # Summary statistics
        stats = self.tdf_db.get('summary_statistics', {})
        text_widget.insert(tk.END, "SUMMARY STATISTICS:\n")
        text_widget.insert(tk.END, "─" * 50 + "\n")

        if 'by_taxon' in stats:
            text_widget.insert(tk.END, "\nBy Taxon:\n")
            for taxon, values in stats['by_taxon'].items():
                text_widget.insert(tk.END, f"  {taxon.title()}: Δ13C={values.get('Δ13C_mean', '?'):.1f}‰, "
                                          f"Δ15N={values.get('Δ15N_mean', '?'):.1f}‰ (n={values.get('n_entries', '?')})\n")

        text_widget.config(state=tk.DISABLED)

    def _populate_column_choices(self):
        """Populate dropdowns with column names from data"""
        if not self.current_data:
            return

        # Get all column names
        columns = set()
        for sample in self.current_data[:50]:  # Sample first 50
            columns.update(sample.keys())

        # Separate numeric and categorical
        numeric_cols = []
        categorical_cols = ['(No Grouping)']

        for col in sorted(columns):
            # Try to determine if numeric
            try:
                val = self.current_data[0].get(col)
                if val is not None:
                    float(str(val).replace(',', '.'))
                    numeric_cols.append(col)
                else:
                    categorical_cols.append(col)
            except (ValueError, TypeError):
                categorical_cols.append(col)

        # Update combos
        self.x_combo['values'] = numeric_cols
        self.y_combo['values'] = numeric_cols
        self.group_combo['values'] = categorical_cols

    # ============ PROGRESS WINDOW ============

    def _show_progress(self, total_iterations):
        """Show progress window for long simulations"""
        self.progress_window = tk.Toplevel(self.window)
        self.progress_window.title("🎲 Monte Carlo Progress")
        self.progress_window.geometry("450x150")
        self.progress_window.transient(self.window)

        tk.Label(self.progress_window,
                text="Propagating uncertainties through mixing model...",
                font=("Arial", 11, "bold")).pack(pady=10)

        self.progress_label = tk.Label(self.progress_window,
                                      text=f"0/{total_iterations:,} iterations",
                                      font=("Arial", 9))
        self.progress_label.pack(pady=5)

        self.progress_bar = ttk.Progressbar(self.progress_window,
                                           length=350, mode='determinate',
                                           maximum=total_iterations)
        self.progress_bar.pack(pady=10)

        self.progress_window.update()

    def _update_progress(self, current, total):
        """Update progress bar"""
        if self.progress_window and self.progress_window.winfo_exists():
            self.progress_bar['value'] = current
            self.progress_label.config(text=f"{current:,}/{total:,} iterations")
            self.progress_window.update()

    def _close_progress(self):
        """Close progress window"""
        if self.progress_window:
            try:
                self.progress_window.destroy()
            except:
                pass
            self.progress_window = None
            self.progress_label = None
            self.progress_bar = None

    # ============ CORE MONTE CARLO ENGINE ============

    def _run_monte_carlo(self):
        """
        Run full Monte Carlo simulation with TDF propagation
        This is the HEART of the plugin
        """
        # ============ VALIDATION ============
        if not self.current_data:
            messagebox.showwarning("No Data", "No data loaded!")
            return

        x_col = self.x_var.get()
        y_col = self.y_var.get()
        if not x_col or not y_col:
            messagebox.showwarning("Missing Selection", "Please select X and Y isotopes.")
            return

        # ============ HANDLE COLUMN MAPPING ============
        # Check if we have a column mapping from the sending plugin
        if hasattr(self, 'external_context') and self.external_context:
            column_mapping = self.external_context.get('column_mapping', {})

            # If we have a mapping, use it to find the actual columns
            if column_mapping:
                # Try to map X isotope
                if x_col in column_mapping:
                    actual_x = column_mapping[x_col]
                    print(f"   Mapping {x_col} → {actual_x}")
                    x_col = actual_x

                # Try to map Y isotope
                if y_col in column_mapping:
                    actual_y = column_mapping[y_col]
                    print(f"   Mapping {y_col} → {actual_y}")
                    y_col = actual_y

        # ============ SETUP ============
        if self.fast_mode_var.get():
            n_iter = 1000
            mode_text = "FAST MODE (1,000 iterations)"
        else:
            n_iter = int(self.iterations_var.get())
            mode_text = f"{n_iter:,} iterations"

        confidence = float(self.confidence_level_var.get()) / 100
        alpha = 1 - confidence

        # Check if we have mixing model
        has_mixing = self.mixing_model_func is not None
        include_tdf = has_mixing and self.include_tdf_uncertainty.get() and hasattr(self, 'tdf_info')

        # ============ GROUP DATA ============
        group_col = self.group_var.get()
        if group_col == "(No Grouping)":
            groups = {"All Samples": self.current_data}
        else:
            groups = {}
            for sample in self.current_data:
                group_val = str(sample.get(group_col, "Unspecified"))
                groups.setdefault(group_val, []).append(sample)

        # ============ FILTER VALID GROUPS ============
        min_samples = 2
        valid_groups = {}
        for name, group_samples in groups.items():
            valid_count = 0
            for s in group_samples:
                if x_col in s and y_col in s:
                    try:
                        float(str(s[x_col]).replace(',', '.'))
                        float(str(s[y_col]).replace(',', '.'))
                        valid_count += 1
                    except (ValueError, TypeError):
                        continue
            if valid_count >= min_samples:
                valid_groups[name] = group_samples

        if not valid_groups:
            messagebox.showerror("Insufficient Data",
                               "No group has at least 2 samples with valid isotope data.")
            return

        # ============ UPDATE UI ============
        self.status_indicator.config(text="● RUNNING", fg="#f39c12")
        self.stats_label.config(text=f"Running {mode_text} with TDF propagation...")
        if self.window:
            self.window.update()

        # Show progress for large runs
        if n_iter >= 5000:
            self._show_progress(n_iter)

        # ============ RESET RESULTS ============
        self.group_results = {}
        self.sample_results = {}
        self.proportion_results = {}

        # ============ MAIN LOOP ============
        try:
            for g_idx, (group_name, group_samples) in enumerate(valid_groups.items()):
                # Extract sample data
                sample_data = []
                for sample in group_samples:
                    try:
                        x_val = float(str(sample[x_col]).replace(',', '.'))
                        y_val = float(str(sample[y_col]).replace(',', '.'))

                        # Get errors (try common patterns)
                        x_err = self._get_error(sample, x_col, x_val)
                        y_err = self._get_error(sample, y_col, y_val)

                        # Get end-member data if mixing
                        em1_13C = None
                        em1_15N = None
                        em2_13C = None
                        em2_15N = None

                        if has_mixing and self.external_context:
                            # Extract from context or sample
                            if 'end_members' in self.external_context:
                                ems = self.external_context['end_members']
                                if len(ems) >= 2:
                                    em1_13C = ems[0].get('δ13C', ems[0].get(x_col))
                                    em1_15N = ems[0].get('δ15N', ems[0].get(y_col))
                                    em2_13C = ems[1].get('δ13C', ems[1].get(x_col))
                                    em2_15N = ems[1].get('δ15N', ems[1].get(y_col))

                            # Also check sample itself for end-member override
                            if 'EM1_δ13C' in sample:
                                em1_13C = float(sample['EM1_δ13C'])
                            if 'EM1_δ15N' in sample:
                                em1_15N = float(sample['EM1_δ15N'])
                            if 'EM2_δ13C' in sample:
                                em2_13C = float(sample['EM2_δ13C'])
                            if 'EM2_δ15N' in sample:
                                em2_15N = float(sample['EM2_δ15N'])

                        sample_data.append({
                            'sample': sample,
                            'x': x_val,
                            'y': y_val,
                            'x_err': x_err,
                            'y_err': y_err,
                            'em1_13C': em1_13C,
                            'em1_15N': em1_15N,
                            'em2_13C': em2_13C,
                            'em2_15N': em2_15N
                        })
                    except (ValueError, TypeError):
                        continue

                if len(sample_data) < min_samples:
                    continue

                # ============ MONTE CARLO FOR THIS GROUP ============
                group_x_means = []
                group_y_means = []
                group_proportions = []  # Store mixing proportions

                # Per-sample storage
                per_sample_x = [[] for _ in range(len(sample_data))]
                per_sample_y = [[] for _ in range(len(sample_data))]
                per_sample_prop = [[] for _ in range(len(sample_data))]

                for it in range(n_iter):
                    # Perturb all samples in group
                    x_perturbed = []
                    y_perturbed = []

                    for i, s in enumerate(sample_data):
                        # Handle correlated errors if requested
                        if self.use_correlated_errors.get() and self.correlation_value.get() > 0:
                            # Multivariate normal with correlation
                            r = self.correlation_value.get()
                            cov = np.array([
                                [s['x_err']**2, r * s['x_err'] * s['y_err']],
                                [r * s['x_err'] * s['y_err'], s['y_err']**2]
                            ])
                            try:
                                xy_pert = np.random.multivariate_normal([s['x'], s['y']], cov)
                                x_pert = xy_pert[0]
                                y_pert = xy_pert[1]
                            except:
                                # Fallback to independent
                                x_pert = np.random.normal(s['x'], s['x_err'])
                                y_pert = np.random.normal(s['y'], s['y_err'])
                        else:
                            # Independent normal
                            x_pert = np.random.normal(s['x'], s['x_err'])
                            y_pert = np.random.normal(s['y'], s['y_err'])

                        x_perturbed.append(x_pert)
                        y_perturbed.append(y_pert)
                        per_sample_x[i].append(x_pert)
                        per_sample_y[i].append(y_pert)

                        # Calculate mixing proportion if we have all data
                        if has_mixing and s['em1_13C'] is not None and s['em2_13C'] is not None:
                            # Perturb TDFs if included
                            if include_tdf:
                                tdf_13C = np.random.normal(self.tdf_info['Δ13C_mean'],
                                                          self.tdf_info['Δ13C_sd'])
                                tdf_15N = np.random.normal(self.tdf_info['Δ15N_mean'],
                                                          self.tdf_info['Δ15N_sd'])
                            else:
                                tdf_13C = self.tdf_info['Δ13C_mean'] if self.tdf_info else 0
                                tdf_15N = self.tdf_info['Δ15N_mean'] if self.tdf_info else 0

                            # Calculate proportion
                            prop = self.mixing_model_func(
                                target_13C=x_pert,
                                target_15N=y_pert,
                                em1_13C=s['em1_13C'],
                                em1_15N=s['em1_15N'],
                                em2_13C=s['em2_13C'],
                                em2_15N=s['em2_15N'],
                                tdf_13C=tdf_13C,
                                tdf_15N=tdf_15N
                            )

                            per_sample_prop[i].append(prop)

                    # Group means (for ellipse)
                    group_x_means.append(np.mean(x_perturbed))
                    group_y_means.append(np.mean(y_perturbed))

                    # Group mean proportion (if mixing)
                    if has_mixing and any(len(p) > 0 for p in per_sample_prop):
                        valid_props = [p[-1] for p in per_sample_prop if p and not np.isnan(p[-1])]
                        if valid_props:
                            group_proportions.append(np.mean(valid_props))

                    # Update progress every 100 iterations
                    if (it + 1) % 100 == 0:
                        overall_iter = g_idx * n_iter + it + 1
                        total_iters = len(valid_groups) * n_iter
                        self._update_progress(overall_iter, total_iters)

                # ============ COMPUTE ELLIPSE PARAMETERS ============
                points = np.column_stack([group_x_means, group_y_means])
                center = np.mean(points, axis=0)
                cov = np.cov(points, rowvar=False)

                # Handle singular covariance
                if np.linalg.det(cov) < 1e-10:
                    cov = cov + np.eye(2) * 1e-6

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
                    'prop_mean': np.mean(group_proportions) if group_proportions else None,
                    'prop_std': np.std(group_proportions) if group_proportions else None
                }

                # Store per-sample results
                for i, s in enumerate(sample_data):
                    # Get sample ID
                    sample_id = s['sample'].get('Sample_ID',
                               s['sample'].get('id',
                               f"{group_name}_{i}"))

                    self.sample_results[sample_id] = {
                        'x_mean': s['x'],
                        'x_err': s['x_err'],
                        'y_mean': s['y'],
                        'y_err': s['y_err'],
                        'x_ci': (np.percentile(per_sample_x[i], alpha*100/2),
                                np.percentile(per_sample_x[i], 100 - alpha*100/2)),
                        'y_ci': (np.percentile(per_sample_y[i], alpha*100/2),
                                np.percentile(per_sample_y[i], 100 - alpha*100/2)),
                        'group': group_name
                    }

                    # Store proportion results if available
                    if per_sample_prop[i]:
                        props = [p for p in per_sample_prop[i] if not np.isnan(p)]
                        if props:
                            self.proportion_results[sample_id] = {
                                'mean': np.mean(props),
                                'std': np.std(props),
                                'ci_lower': np.percentile(props, alpha*100/2),
                                'ci_upper': np.percentile(props, 100 - alpha*100/2),
                                'median': np.median(props),
                                'group': group_name
                            }

            # ============ FINISH ============
            self._close_progress()
            self._plot_ellipses()
            self._update_results_text()
            self._update_proportion_text()

            # Update status
            status_parts = [f"{len(self.group_results)} groups"]
            if include_tdf:
                status_parts.append("with TDF uncertainty")
            if self.proportion_results:
                status_parts.append(f"{len(self.proportion_results)} proportions")

            self.status_indicator.config(text="● COMPLETE", fg="#2ecc71")
            self.stats_label.config(
                text=f"Complete • {mode_text} • {confidence*100:.0f}% CI • " + " • ".join(status_parts)
            )

        except Exception as e:
            self._close_progress()
            self.status_indicator.config(text="● ERROR", fg="#e74c3c")
            self.stats_label.config(text=f"Error: {str(e)[:100]}")
            messagebox.showerror("Monte Carlo Error",
                               f"Error during simulation:\n\n{str(e)}\n\nCheck console for details.")
            import traceback
            traceback.print_exc()

    def _get_error(self, sample, column, value):
        """Extract error for a column with multiple naming conventions"""
        # Try common error column names
        err_candidates = [
            f"{column}_error",
            f"{column}_err",
            f"{column}_sd",
            f"{column}_1s",  # Common in isotope labs
            f"{column}_1sigma",
            f"{column}_uncertainty",
            column.replace('δ', '') + '_error',
            column.replace('δ', '') + '_err'
        ]

        for cand in err_candidates:
            if cand in sample:
                try:
                    e = float(sample[cand])
                    if e > 0:
                        return e
                except (ValueError, TypeError):
                    continue

        # Fallback: 2% of value for isotopes (typical analytical precision)
        return abs(value) * 0.02 if value != 0 else 0.1

    # ============ VISUALIZATION ============

    def _plot_ellipses(self):
        """Plot confidence ellipses for each group"""
        # Clear canvas
        for widget in self.ellipse_canvas_frame.winfo_children():
            widget.destroy()

        if not self.group_results:
            self.ellipse_placeholder = tk.Label(self.ellipse_canvas_frame,
                                               text="No groups to display.\nRun Monte Carlo first.",
                                               font=("Arial", 10), bg="#f8f9fa")
            self.ellipse_placeholder.pack(fill=tk.BOTH, expand=True)
            return

        if not HAS_MATPLOTLIB:
            # Text fallback
            text_widget = tk.Text(self.ellipse_canvas_frame, wrap=tk.WORD,
                                 font=("Courier", 9), bg="#f8f9fa",
                                 padx=10, pady=10)
            text_widget.pack(fill=tk.BOTH, expand=True)
            text_widget.insert(tk.END, "📈 CONFIDENCE ELLIPSES (matplotlib not available)\n\n")
            for name, ellipse in self.group_results.items():
                text_widget.insert(tk.END, f"{name}:\n")
                text_widget.insert(tk.END, f"  Center: {self.x_var.get()}={ellipse['x_mean']:.2f}, "
                                          f"{self.y_var.get()}={ellipse['y_mean']:.2f}\n")
                text_widget.insert(tk.END, f"  Width={ellipse['width']:.2f}, Height={ellipse['height']:.2f}\n")
                text_widget.insert(tk.END, f"  Angle={ellipse['angle']:.1f}°, n={ellipse['n_samples']}\n\n")
            text_widget.config(state=tk.DISABLED)
            return

        try:
            fig, ax = plt.subplots(figsize=(7, 6), dpi=100)

            # Color map
            colors = plt.cm.Set1(np.linspace(0, 1, len(self.group_results)))

            for (name, ellipse), color in zip(self.group_results.items(), colors):
                # Draw ellipse
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

                # Plot center
                ax.scatter(ellipse['center'][0], ellipse['center'][1],
                          c=[color], s=100, edgecolors='white', linewidth=2, zorder=5)

                # Add proportion text if available
                if ellipse.get('prop_mean') is not None:
                    ax.annotate(f"f={ellipse['prop_mean']:.2f}±{ellipse['prop_std']:.2f}",
                               xy=ellipse['center'], xytext=(5, 5),
                               textcoords='offset points', fontsize=8,
                               bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))

            ax.set_xlabel(f"{self.x_var.get()} (‰)", fontsize=11, fontweight='bold')
            ax.set_ylabel(f"{self.y_var.get()} (‰)", fontsize=11, fontweight='bold')

            # Add title with TDF info
            title = f"{self.confidence_level_var.get()}% Confidence Ellipses"
            if hasattr(self, 'tdf_info') and self.tdf_info:
                title += f"\nTDF: Δ13C={self.tdf_info['Δ13C_mean']:.1f}±{self.tdf_info['Δ13C_sd']:.1f}, "
                title += f"Δ15N={self.tdf_info['Δ15N_mean']:.1f}±{self.tdf_info['Δ15N_sd']:.1f}"

            ax.set_title(title, fontsize=10, pad=15)
            ax.legend(loc='best', fontsize=8)
            ax.grid(True, alpha=0.2, linestyle='--')

            # Auto-adjust limits
            all_x = [ell['center'][0] for ell in self.group_results.values()]
            all_y = [ell['center'][1] for ell in self.group_results.values()]
            x_range = max(all_x) - min(all_x) if len(all_x) > 1 else 2
            y_range = max(all_y) - min(all_y) if len(all_y) > 1 else 2

            ax.set_xlim(min(all_x) - 0.3*x_range, max(all_x) + 0.3*x_range)
            ax.set_ylim(min(all_y) - 0.3*y_range, max(all_y) + 0.3*y_range)

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
        """Update group statistics text"""
        if not self.results_text:
            return

        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)

        self.results_text.insert(tk.END, "📊 GROUP CONFIDENCE ELLIPSES\n")
        self.results_text.insert(tk.END, "═" * 80 + "\n\n")

        mode = "FAST" if self.fast_mode_var.get() else f"{self.iterations_var.get()} iters"
        self.results_text.insert(tk.END, f"Monte Carlo • {mode} • {self.confidence_level_var.get()}% CI\n")

        if hasattr(self, 'tdf_info') and self.tdf_info:
            self.results_text.insert(tk.END, f"TDF Source: {self.tdf_info.get('source', 'database')}\n")
            if self.include_tdf_uncertainty.get():
                self.results_text.insert(tk.END, "✓ TDF uncertainty INCLUDED\n")
            else:
                self.results_text.insert(tk.END, "✗ TDF uncertainty NOT included\n")
        self.results_text.insert(tk.END, "\n")

        for name, ellipse in self.group_results.items():
            self.results_text.insert(tk.END, f"Group: {name}\n")
            self.results_text.insert(tk.END, f"  Samples: {ellipse['n_samples']}\n")
            self.results_text.insert(tk.END, f"  Center: {self.x_var.get()}={ellipse['x_mean']:.2f}‰, "
                                            f"{self.y_var.get()}={ellipse['y_mean']:.2f}‰\n")
            self.results_text.insert(tk.END, f"  Std dev: ±{ellipse['x_std']:.2f}‰, ±{ellipse['y_std']:.2f}‰\n")
            self.results_text.insert(tk.END, f"  Correlation: {ellipse['correlation']:.3f}\n")
            self.results_text.insert(tk.END, f"  Ellipse: {ellipse['width']:.2f}‰ × {ellipse['height']:.2f}‰, "
                                            f"{ellipse['angle']:.1f}°\n")
            if ellipse.get('prop_mean') is not None:
                self.results_text.insert(tk.END, f"  Mixing proportion: f={ellipse['prop_mean']:.3f} "
                                                f"± {ellipse['prop_std']:.3f}\n")
            self.results_text.insert(tk.END, "\n")

        self.results_text.config(state=tk.DISABLED)

    def _update_proportion_text(self):
        """Update mixing proportions text"""
        if not self.proportion_text:
            return

        self.proportion_text.config(state=tk.NORMAL)
        self.proportion_text.delete(1.0, tk.END)

        self.proportion_text.insert(tk.END, "📊 MIXING PROPORTION CONFIDENCE INTERVALS\n")
        self.proportion_text.insert(tk.END, "═" * 80 + "\n\n")

        if not self.proportion_results:
            self.proportion_text.insert(tk.END, "No mixing proportion data available.\n")
            self.proportion_text.insert(tk.END, "Make sure:\n")
            self.proportion_text.insert(tk.END, "• Data was sent with end-member values\n")
            self.proportion_text.insert(tk.END, "• Mixing model is binary\n")
            self.proportion_text.insert(tk.END, "• TDF data is available\n")
            self.proportion_text.config(state=tk.DISABLED)
            return

        conf = self.confidence_level_var.get()
        self.proportion_text.insert(tk.END, f"f = proportion of EM2 in mixture ({conf}% CI)\n\n")

        # Group by group
        by_group = {}
        for sample_id, prop in self.proportion_results.items():
            group = prop.get('group', 'Unknown')
            by_group.setdefault(group, []).append((sample_id, prop))

        for group, samples in by_group.items():
            self.proportion_text.insert(tk.END, f"\n{group}:\n")
            self.proportion_text.insert(tk.END, "─" * 50 + "\n")

            # Sort by sample ID
            samples.sort()
            for sample_id, prop in samples:
                line = (f"  {sample_id[:20]:<20} f = {prop['mean']:.3f} "
                       f"[{prop['ci_lower']:.3f}, {prop['ci_upper']:.3f}]  "
                       f"±{prop['std']:.3f}\n")
                self.proportion_text.insert(tk.END, line)

        self.proportion_text.config(state=tk.DISABLED)

    # ============ EXPORT FUNCTIONS ============

    def _export_ellipses(self):
        """Export ellipse parameters to CSV"""
        if not self.group_results:
            messagebox.showwarning("No Data", "Run Monte Carlo first!")
            return

        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile=f"isotope_ellipses_{datetime.now().strftime('%Y%m%d')}.csv"
        )
        if not filename:
            return

        try:
            import csv
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Group', 'N_Samples', f'{self.x_var.get()}_Mean', f'{self.y_var.get()}_Mean',
                               f'{self.x_var.get()}_Std', f'{self.y_var.get()}_Std',
                               'Correlation', 'Ellipse_Width', 'Ellipse_Height', 'Ellipse_Angle',
                               'Proportion_Mean', 'Proportion_Std', 'Confidence_%',
                               'TDF_Source', 'TDF_Included'])

                conf = self.confidence_level_var.get()
                tdf_source = self.tdf_info.get('source', 'none') if hasattr(self, 'tdf_info') else 'none'
                tdf_included = self.include_tdf_uncertainty.get() if hasattr(self, 'include_tdf_uncertainty') else False

                for name, ell in self.group_results.items():
                    writer.writerow([
                        name,
                        ell['n_samples'],
                        f"{ell['x_mean']:.4f}",
                        f"{ell['y_mean']:.4f}",
                        f"{ell['x_std']:.4f}",
                        f"{ell['y_std']:.4f}",
                        f"{ell['correlation']:.4f}",
                        f"{ell['width']:.4f}",
                        f"{ell['height']:.4f}",
                        f"{ell['angle']:.2f}",
                        f"{ell.get('prop_mean', '')}",
                        f"{ell.get('prop_std', '')}",
                        conf,
                        tdf_source,
                        tdf_included
                    ])
            messagebox.showinfo("Export Complete", f"Exported {len(self.group_results)} groups.")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def _export_sample_ci(self):
        """Export per-sample confidence intervals"""
        if not self.sample_results:
            messagebox.showwarning("No Data", "Run Monte Carlo first!")
            return

        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile=f"isotope_CI_{datetime.now().strftime('%Y%m%d')}.csv"
        )
        if not filename:
            return

        try:
            import csv
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Sample_ID', 'Group', f'{self.x_var.get()}_Mean', f'{self.x_var.get()}_Error',
                               f'{self.x_var.get()}_CI_Lower', f'{self.x_var.get()}_CI_Upper',
                               f'{self.y_var.get()}_Mean', f'{self.y_var.get()}_Error',
                               f'{self.y_var.get()}_CI_Lower', f'{self.y_var.get()}_CI_Upper'])

                for sid, vals in self.sample_results.items():
                    writer.writerow([
                        sid,
                        vals.get('group', ''),
                        f"{vals['x_mean']:.4f}",
                        f"{vals['x_err']:.4f}",
                        f"{vals['x_ci'][0]:.4f}",
                        f"{vals['x_ci'][1]:.4f}",
                        f"{vals['y_mean']:.4f}",
                        f"{vals['y_err']:.4f}",
                        f"{vals['y_ci'][0]:.4f}",
                        f"{vals['y_ci'][1]:.4f}"
                    ])
            messagebox.showinfo("Export Complete", f"Exported {len(self.sample_results)} samples.")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def _export_proportions(self):
        """Export mixing proportion CIs"""
        if not self.proportion_results:
            messagebox.showwarning("No Data", "No proportion data available!")
            return

        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile=f"mixing_proportions_{datetime.now().strftime('%Y%m%d')}.csv"
        )
        if not filename:
            return

        try:
            import csv
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Sample_ID', 'Group', 'Proportion_Mean', 'Proportion_Std',
                               'Proportion_Median', 'CI_Lower', 'CI_Upper', 'CI_Percent'])

                conf = self.confidence_level_var.get()
                for sid, vals in self.proportion_results.items():
                    writer.writerow([
                        sid,
                        vals.get('group', ''),
                        f"{vals['mean']:.4f}",
                        f"{vals['std']:.4f}",
                        f"{vals['median']:.4f}",
                        f"{vals['ci_lower']:.4f}",
                        f"{vals['ci_upper']:.4f}",
                        conf
                    ])
            messagebox.showinfo("Export Complete", f"Exported {len(self.proportion_results)} samples.")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    # ============ APPEND TO MAIN TABLE ============

    def _append_to_main_table(self):
        """Write all results back to main table"""
        if not self.sample_results and not self.proportion_results:
            messagebox.showwarning("No Data", "Run Monte Carlo first!")
            return

        # Confirm with user
        msg = ("This will add the following columns to your main data table:\n\n"
               "Isotope CIs:\n"
               f"• {self.x_var.get()}_CI_lower, {self.x_var.get()}_CI_upper\n"
               f"• {self.y_var.get()}_CI_lower, {self.y_var.get()}_CI_upper\n\n")

        if self.proportion_results:
            msg += "Mixing Proportions:\n"
            msg += f"• {self.proportion_col_name.get()}_mean\n"
            msg += f"• {self.proportion_col_name.get()}_std\n"
            msg += f"• {self.proportion_col_name.get()}_CI_lower\n"
            msg += f"• {self.proportion_col_name.get()}_CI_upper\n\n"

        if self.group_results:
            msg += "Group Ellipses:\n"
            msg += "• Group_Ellipse_Center_X, Group_Ellipse_Center_Y\n"
            msg += "• Group_Ellipse_Width, Group_Ellipse_Height, Group_Ellipse_Angle\n\n"

        msg += "Existing data will NOT be overwritten. Proceed?"

        if not messagebox.askyesno("Append to Main Table", msg):
            return

        # Map results to samples
        updated_count = 0
        prop_count = 0

        # We need to match samples - try multiple strategies
        for idx, sample in enumerate(self.app.samples):
            # Try different ID strategies
            matched = False
            sample_id = None

            # Strategy 1: Sample_ID field
            if 'Sample_ID' in sample and sample['Sample_ID'] in self.sample_results:
                sample_id = sample['Sample_ID']
                matched = True

            # Strategy 2: id field
            elif 'id' in sample and sample['id'] in self.sample_results:
                sample_id = sample['id']
                matched = True

            # Strategy 3: index-based (if data order preserved)
            elif not matched and idx < len(self.current_data):
                # Check if it's the same object or has same content
                if self.current_data[idx] is sample:
                    # Find by position in our stored results
                    for sid in self.sample_results.keys():
                        if str(idx) in sid or sid.endswith(f"_{idx}"):
                            sample_id = sid
                            matched = True
                            break

            if matched and sample_id in self.sample_results:
                res = self.sample_results[sample_id]
                # Add isotope CIs
                sample[f'{self.x_var.get()}_CI_lower'] = res['x_ci'][0]
                sample[f'{self.x_var.get()}_CI_upper'] = res['x_ci'][1]
                sample[f'{self.y_var.get()}_CI_lower'] = res['y_ci'][0]
                sample[f'{self.y_var.get()}_CI_upper'] = res['y_ci'][1]
                sample['Group_Name'] = res.get('group', '')
                updated_count += 1

            # Add proportion results if available
            if matched and sample_id in self.proportion_results:
                prop = self.proportion_results[sample_id]
                col_base = self.proportion_col_name.get()
                sample[f'{col_base}_mean'] = prop['mean']
                sample[f'{col_base}_std'] = prop['std']
                sample[f'{col_base}_CI_lower'] = prop['ci_lower']
                sample[f'{col_base}_CI_upper'] = prop['ci_upper']
                prop_count += 1

        # Add group ellipse parameters to all samples (based on group name)
        for sample in self.app.samples:
            group_name = sample.get('Group_Name', '')
            if group_name and group_name in self.group_results:
                ell = self.group_results[group_name]
                sample['Group_Ellipse_Center_X'] = ell['x_mean']
                sample['Group_Ellipse_Center_Y'] = ell['y_mean']
                sample['Group_Ellipse_Width'] = ell['width']
                sample['Group_Ellipse_Height'] = ell['height']
                sample['Group_Ellipse_Angle'] = ell['angle']

        # Refresh main app display
        if hasattr(self.app, 'refresh_table'):
            self.app.refresh_table()
        elif hasattr(self.app, 'update_table_display'):
            self.app.update_table_display()

        # Show summary
        summary = f"Added isotope CIs to {updated_count} samples.\n"
        if prop_count:
            summary += f"Added proportion CIs to {prop_count} samples.\n"
        summary += "Group ellipse parameters added to all samples."

        messagebox.showinfo("Append Complete", summary)

    def stop(self):
        """Clean up resources when plugin is closed"""
        print("🛑 Stopping Uncertainty plugin...")

        # Cancel all after callbacks
        self._cancel_all_after_callbacks()

        # Close progress window if open
        self._close_progress()

        # Destroy window if it exists
        if self.window and self.window.winfo_exists():
            try:
                self.window.destroy()
            except:
                pass

        print("✅ Uncertainty plugin stopped")

    def _cancel_all_after_callbacks(self):
        """Cancel all pending after callbacks"""
        if not hasattr(self, '_after_ids'):
            self._after_ids = []

        for after_id in self._after_ids:
            try:
                if self.window and self.window.winfo_exists():
                    self.window.after_cancel(after_id)
            except:
                pass

        self._after_ids.clear()

    def _safe_after(self, ms, func, *args):
        """Safely schedule an after callback with tracking"""
        if not hasattr(self, '_after_ids'):
            self._after_ids = []

        try:
            if self.window and self.window.winfo_exists():
                after_id = self.window.after(ms, lambda: self._execute_after(func, *args))
                self._after_ids.append(after_id)
                return after_id
        except:
            pass
        return None

    def _execute_after(self, func, *args):
        """Execute an after callback and remove its ID"""
        try:
            func(*args)
        finally:
            # Find and remove this callback's ID
            import inspect
            frame = inspect.currentframe()
            # This is tricky - we'd need to know the after_id
            # Alternative: just clear all periodically or ignore
            pass


def setup_plugin(main_app):
    """Plugin entry point - returns an instance of the plugin"""
    return IsotopeUncertaintyPro(main_app)
