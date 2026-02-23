"""
Isotope Mixing Models Plugin v3.0 - Integrated with Scientific Toolkit
BINARY & TERNARY MIXING - END-MEMBER ESTIMATION - MONTE CARLO SIMULATIONS
ADVANCED INVERSION: Least-squares, Bayesian MCMC, REE pattern inversion

FROM ISOTOPE RATIOS TO PROVENANCE IN 3 CLICKS

NOW WITH:
✓ Direct integration with main app data table
✓ Auto-detection of isotope columns (Sr, Nd, Pb, Hf, O)
✓ Industry-standard mixing algorithms (after Faure, Albarede, Vollmer)
✓ FULLY FUNCTIONAL TERNARY MIXING for Pb isotopes and Sr-Nd-Pb systems
✓ Uncertainty propagation with Monte Carlo
✓ Mahalanobis distance for provenance
✓ Publication-ready figures
✓ **LEAST-SQUARES INVERSION** for source composition estimation
✓ **BAYESIAN MCMC INVERSION** with emcee (full posterior distributions)
✓ **REE PATTERN INVERSION** with partition coefficients from magma_modeling.py
"""

PLUGIN_INFO = {
    "category": "software",
    "id": "isotope_mixing_models",
    "name": "Isotope Mixing Models",
    "icon": "🧪",
    "description": "Binary/ternary mixing, end-member estimation, Monte Carlo, Bayesian inversion, REE inversion",
    "version": "3.0.0",
    "requires": ["numpy", "scipy", "matplotlib", "pandas", "emcee"],
    "author": "Sefy Levy"
}

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
from datetime import datetime
from pathlib import Path
import json
import traceback

# ============ SCIENTIFIC IMPORTS ============
try:
    from scipy import stats, optimize
    from scipy.spatial import distance, ConvexHull
    from scipy.linalg import svd
    from scipy.stats import chi2, norm
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    import emcee
    HAS_EMCEE = True
except ImportError:
    HAS_EMCEE = False

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    from matplotlib.patches import Ellipse, Polygon
    from matplotlib.lines import Line2D
    from mpl_toolkits.mplot3d import Axes3D
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


class IsotopeMixingModelsPlugin:
    """
    ============================================================================
    ISOTOPE MIXING MODELS v3.0 - INTEGRATED VERSION WITH ADVANCED INVERSION
    ============================================================================

    INDUSTRY STANDARD FEATURES:
    ────────────────────────────────────────────────────────────────────────────
    • Auto-detects isotope columns from main app data
    • Uses actual sample data from the table (no separate import needed)
    • Implements mixing equations after Faure (1986), Albarede (1995)
    • FULL TERNARY MIXING for Pb isotopes (Vollmer, 1976; Albarede, 1995)
    • Monte Carlo with realistic analytical uncertainties
    • Mahalanobis distance for provenance assignment
    • Confidence ellipses (95%) for end-members
    • Returns results to main app as new columns

    NEW IN v3.0:
    • LEAST-SQUARES INVERSION: Solve for source compositions from sample mixtures
    • BAYESIAN MCMC INVERSION: Full posterior distributions with emcee
    • REE INVERSION: Model REE patterns using partition coefficients
    """

    # Standard isotope ratios with their typical uncertainties
    ISOTOPE_SYSTEMS = {
        'Sr': {
            'ratios': ['87Sr/86Sr', '87Sr_86Sr', 'Sr87_Sr86'],
            'uncertainty': 0.00002,  # 2e-5 absolute
            'display': '⁸⁷Sr/⁸⁶Sr',
            'concentration': ['Sr_ppm', 'Sr']
        },
        'Nd': {
            'ratios': ['143Nd/144Nd', '143Nd_144Nd', 'Nd143_Nd144'],
            'uncertainty': 0.00001,  # 1e-5 absolute
            'display': '¹⁴³Nd/¹⁴⁴Nd',
            'epsilon': 'εNd',
            'concentration': ['Nd_ppm', 'Nd']
        },
        'Pb206_204': {
            'ratios': ['206Pb/204Pb', '206Pb_204Pb', 'Pb206_Pb204'],
            'uncertainty': 0.01,  # 0.01 absolute
            'display': '²⁰⁶Pb/²⁰⁴Pb'
        },
        'Pb207_204': {
            'ratios': ['207Pb/204Pb', '207Pb_204Pb', 'Pb207_Pb204'],
            'uncertainty': 0.01,
            'display': '²⁰⁷Pb/²⁰⁴Pb'
        },
        'Pb208_204': {
            'ratios': ['208Pb/204Pb', '208Pb_204Pb', 'Pb208_Pb204'],
            'uncertainty': 0.01,
            'display': '²⁰⁸Pb/²⁰⁴Pb'
        },
        'Hf': {
            'ratios': ['176Hf/177Hf', '176Hf_177Hf', 'Hf176_Hf177'],
            'uncertainty': 0.00001,
            'display': '¹⁷⁶Hf/¹⁷⁷Hf',
            'epsilon': 'εHf'
        },
        'O': {
            'ratios': ['δ18O', 'd18O', 'O18'],
            'uncertainty': 0.1,  # 0.1 permil
            'display': 'δ¹⁸O (‰)'
        }
    }

    # REE list for inversion
    REE_ELEMENTS = ['La', 'Ce', 'Pr', 'Nd', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy', 'Ho', 'Er', 'Tm', 'Yb', 'Lu']

    # Default partition coefficients (from magma_modeling.py)
    DEFAULT_KDS = {
        'olivine': {'La': 0.0004, 'Ce': 0.0005, 'Nd': 0.001, 'Sm': 0.0013, 'Eu': 0.0016,
                   'Gd': 0.0015, 'Dy': 0.0017, 'Er': 0.0015, 'Yb': 0.0014, 'Lu': 0.0015},
        'clinopyroxene': {'La': 0.056, 'Ce': 0.092, 'Nd': 0.23, 'Sm': 0.445, 'Eu': 0.474,
                         'Gd': 0.583, 'Dy': 0.642, 'Er': 0.583, 'Yb': 0.542, 'Lu': 0.506},
        'orthopyroxene': {'La': 0.002, 'Ce': 0.003, 'Nd': 0.006, 'Sm': 0.01, 'Eu': 0.013,
                         'Gd': 0.016, 'Dy': 0.022, 'Er': 0.03, 'Yb': 0.04, 'Lu': 0.045},
        'garnet': {'La': 0.001, 'Ce': 0.007, 'Nd': 0.055, 'Sm': 0.28, 'Eu': 0.41,
                  'Gd': 1.1, 'Dy': 2.0, 'Er': 3.0, 'Yb': 4.0, 'Lu': 5.0},
        'plagioclase': {'La': 0.12, 'Ce': 0.11, 'Nd': 0.069, 'Sm': 0.052, 'Eu': 0.41,
                       'Gd': 0.034, 'Dy': 0.022, 'Er': 0.013, 'Yb': 0.009, 'Lu': 0.008},
        'amphibole': {'La': 0.27, 'Ce': 0.41, 'Nd': 0.82, 'Sm': 1.3, 'Eu': 1.4,
                     'Gd': 1.6, 'Dy': 1.7, 'Er': 1.5, 'Yb': 1.3, 'Lu': 1.2}
    }

    # Predefined end-member reservoirs (after Zindler & Hart, 1986; Hofmann, 1997)
    END_MEMBERS = {
        'MORB': {
            'name': 'MORB',
            '87Sr/86Sr': 0.7025,
            '143Nd/144Nd': 0.51315,
            '206Pb/204Pb': 18.5,
            '207Pb/204Pb': 15.5,
            '208Pb/204Pb': 38.0,
            'εNd': 10,
            'color': '#3498db',  # Blue
            'reference': 'Depleted MORB mantle (Salters & Stracke, 2004)'
        },
        'OIB': {
            'name': 'OIB',
            '87Sr/86Sr': 0.7035,
            '143Nd/144Nd': 0.51290,
            '206Pb/204Pb': 19.5,
            '207Pb/204Pb': 15.6,
            '208Pb/204Pb': 39.0,
            'εNd': 5,
            'color': '#e74c3c',  # Red
            'reference': 'Average OIB (Hofmann, 1997)'
        },
        'EM1': {
            'name': 'EM1',
            '87Sr/86Sr': 0.7055,
            '143Nd/144Nd': 0.51245,
            '206Pb/204Pb': 17.5,
            '207Pb/204Pb': 15.5,
            '208Pb/204Pb': 38.5,
            'εNd': -5,
            'color': '#c0392b',  # Dark red
            'reference': 'Enriched Mantle 1 (Zindler & Hart, 1986)'
        },
        'EM2': {
            'name': 'EM2',
            '87Sr/86Sr': 0.7080,
            '143Nd/144Nd': 0.51230,
            '206Pb/204Pb': 19.0,
            '207Pb/204Pb': 15.7,
            '208Pb/204Pb': 39.5,
            'εNd': -8,
            'color': '#d35400',  # Brown
            'reference': 'Enriched Mantle 2 (Zindler & Hart, 1986)'
        },
        'HIMU': {
            'name': 'HIMU',
            '87Sr/86Sr': 0.7028,
            '143Nd/144Nd': 0.51285,
            '206Pb/204Pb': 21.0,
            '207Pb/204Pb': 15.8,
            '208Pb/204Pb': 40.5,
            'εNd': 4,
            'color': '#16a085',  # Teal
            'reference': 'High μ (Zindler & Hart, 1986)'
        },
        'UPPER_CRUST': {
            'name': 'Upper Crust',
            '87Sr/86Sr': 0.720,
            '143Nd/144Nd': 0.5120,
            '206Pb/204Pb': 19.5,
            '207Pb/204Pb': 15.8,
            '208Pb/204Pb': 39.5,
            'εNd': -15,
            'color': '#f39c12',  # Orange
            'reference': 'Upper continental crust (Rudnick & Gao, 2003)'
        },
        'LOWER_CRUST': {
            'name': 'Lower Crust',
            '87Sr/86Sr': 0.710,
            '143Nd/144Nd': 0.5115,
            '206Pb/204Pb': 17.5,
            '207Pb/204Pb': 15.4,
            '208Pb/204Pb': 38.0,
            'εNd': -25,
            'color': '#27ae60',  # Green
            'reference': 'Lower continental crust (Rudnick & Gao, 2003)'
        },
        'BSE': {
            'name': 'BSE',
            '87Sr/86Sr': 0.7045,
            '143Nd/144Nd': 0.51265,
            '206Pb/204Pb': 18.0,
            '207Pb/204Pb': 15.5,
            '208Pb/204Pb': 38.3,
            'εNd': 0,
            'color': '#7f8c8d',  # Gray
            'reference': 'Bulk Silicate Earth (McDonough & Sun, 1995)'
        }
    }

    def __init__(self, main_app):
        self.app = main_app
        self.window = None

        # Data from main app
        self.samples = None  # Will be populated from app.samples
        self.available_isotopes = {}  # Auto-detected isotope columns
        self.available_ree = {}  # Auto-detected REE columns

        # End-members
        self.end_members = None  # User-defined or built-in
        self.custom_end_members = []  # User-loaded custom end-members

        # Current results
        self.current_results = {}
        self.mixing_proportions = {}
        self.monte_carlo_results = None
        self.inversion_results = None
        self.mcmc_results = None
        self.ree_inversion_results = None

        # UI elements
        self.notebook = None
        self.data_status = None
        self.results_text = None
        self.canvas_frame = None
        self.status_indicator = None
        self.isotope_listbox = None
        self.x_var = None
        self.y_var = None
        self.z_var = None  # Added for ternary/3D

        # Check dependencies
        self._check_dependencies()

        # Auto-detect isotopes from main app on init
        self._detect_isotopes_from_app()
        self._detect_ree_from_app()

    def _check_dependencies(self):
        """Check if required packages are installed"""
        missing = []
        if not HAS_SCIPY:
            missing.append("scipy")
        if not HAS_MATPLOTLIB:
            missing.append("matplotlib")
        if not HAS_PANDAS:
            missing.append("pandas")
        if not HAS_EMCEE:
            missing.append("emcee (optional for Bayesian inversion)")

        self.dependencies_met = len([m for m in missing if 'optional' not in m]) == 0
        self.missing_deps = missing

    def _detect_isotopes_from_app(self):
        """Auto-detect isotope columns from main app data"""
        if not hasattr(self.app, 'samples') or not self.app.samples:
            return

        # Convert to DataFrame for easier handling
        self.samples = pd.DataFrame(self.app.samples)

        self.available_isotopes = {}

        # Check each column against known isotope patterns
        for col in self.samples.columns:
            col_lower = str(col).lower()

            for system, info in self.ISOTOPE_SYSTEMS.items():
                for pattern in info['ratios']:
                    if pattern.lower() in col_lower or col_lower in pattern.lower():
                        self.available_isotopes[system] = {
                            'column': col,
                            'display': info['display'],
                            'uncertainty': info['uncertainty'],
                            'data': self.samples[col].values
                        }
                        break


    def _detect_ree_from_app(self):
        """Auto-detect REE columns from main app data"""
        if not hasattr(self.app, 'samples') or not self.app.samples:
            return

        self.available_ree = {}

        # Check each column against REE list
        for col in self.samples.columns:
            col_upper = str(col).upper()
            col_lower = str(col).lower()  # ← This was missing!

            for ree in self.REE_ELEMENTS:
                if ree.upper() in col_upper and ('ppm' in col_lower or 'conc' in col_lower or ree.lower() in col_lower):
                    self.available_ree[ree] = {
                        'column': col,
                        'display': f'{ree} (ppm)',
                        'data': self.samples[col].values
                    }
                    break


    def _safe_import_message(self):
        """Show friendly import instructions"""
        if not self.dependencies_met:
            deps = " ".join(self.missing_deps)
            messagebox.showerror(
                "Missing Dependencies",
                f"Isotope Mixing Models requires:\n\n" +
                "\n".join(self.missing_deps) +
                f"\n\nInstall with:\npip install {deps}"
            )
            return False
        return True

    def open_window(self):
        """Open the isotope mixing models window"""
        if not self._safe_import_message():
            return

        if self.window and self.window.winfo_exists():
            self.window.lift()
            # Refresh data from main app
            self._refresh_from_main_app()
            return

        # COMPACT DESIGN - Reduced size from 1500x850 to 1200x700
        self.window = tk.Toplevel(self.app.root)
        self.window.title("🧪 Isotope Mixing Models v3.0")
        self.window.geometry("900x620")
        self.window.transient(self.app.root)

        # Refresh data from main app
        self._refresh_from_main_app()

        self._create_interface()
        self.window.lift()
        self.window.focus_force()

    def _refresh_from_main_app(self):
        """Refresh data from main app (called when window opens)"""
        if hasattr(self.app, 'samples') and self.app.samples:
            self.samples = pd.DataFrame(self.app.samples)
            self._detect_isotopes_from_app()
            self._detect_ree_from_app()

            # Update status if window is open AND widget exists
            if hasattr(self, 'data_status') and self.data_status and self.data_status.winfo_exists():
                self.data_status.config(
                    text=f"📊 {len(self.samples)} samples | {len(self.available_isotopes)} isotope systems | {len(self.available_ree)} REE",
                    fg="#27ae60"
                )

    def _create_interface(self):
        """Create the isotope mixing models interface - COMPACT DESIGN"""

        # ============ TOP BANNER - COMPACT ============
        header = tk.Frame(self.window, bg="#2c3e50", height=35)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="🧪", font=("Arial", 14),
                bg="#2c3e50", fg="white").pack(side=tk.LEFT, padx=8)

        tk.Label(header, text="Isotope Mixing Models v3.0",
                font=("Arial", 11, "bold"), bg="#2c3e50", fg="white").pack(side=tk.LEFT, padx=3)

        tk.Label(header, text="Advanced Inversion",
                font=("Arial", 7), bg="#2c3e50", fg="#f39c12").pack(side=tk.LEFT, padx=8)

        # Refresh button - icon only
        tk.Button(header, text="🔄", command=self._refresh_from_main_app,
                bg="#3498db", fg="white", font=("Arial", 8), width=2).pack(side=tk.RIGHT, padx=5)

        self.status_indicator = tk.Label(header, text="● READY",
                                        font=("Arial", 7, "bold"),
                                        bg="#2c3e50", fg="#2ecc71")
        self.status_indicator.pack(side=tk.RIGHT, padx=8)

        # ============ MAIN CONTENT ============
        main_paned = tk.PanedWindow(self.window, orient=tk.HORIZONTAL,
                                sashwidth=3, sashrelief=tk.RAISED)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # ============ LEFT PANEL - DATA MANAGEMENT ============
        left_panel = tk.Frame(main_paned, bg="white", relief=tk.RAISED, borderwidth=1)
        main_paned.add(left_panel, width=350)

        # ============ DATA STATUS ============
        status_frame = tk.Frame(left_panel, bg="#ecf0f1", relief=tk.SUNKEN, borderwidth=1)
        status_frame.pack(fill=tk.X, padx=5, pady=3)

        self.data_status = tk.Label(status_frame,
                                text=f"📊 {len(self.samples) if self.samples is not None else 0} samples loaded",
                                font=("Arial", 8), bg="#ecf0f1", fg="#2c3e50",
                                pady=2)
        self.data_status.pack()

        # ============ ISOTOPE SELECTOR ============
        isotope_frame = tk.LabelFrame(left_panel, text="⚛️ 1. SELECT ISOTOPE SYSTEM",
                                    font=("Arial", 8, "bold"),
                                    bg="white", padx=5, pady=3)
        isotope_frame.pack(fill=tk.X, padx=5, pady=3)

        # Available isotopes listbox
        list_frame = tk.Frame(isotope_frame)
        list_frame.pack(fill=tk.X, pady=2)

        self.isotope_listbox = tk.Listbox(list_frame, height=3, selectmode=tk.EXTENDED)
        scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=self.isotope_listbox.yview)
        self.isotope_listbox.configure(yscrollcommand=scrollbar.set)

        self.isotope_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Populate with detected isotopes
        for sys_name, info in self.available_isotopes.items():
            self.isotope_listbox.insert(tk.END, f"{info['display']} ({sys_name})")

        if not self.available_isotopes:
            self.isotope_listbox.insert(tk.END, "No isotope data found")
            self.isotope_listbox.insert(tk.END, "Add columns like:")
            self.isotope_listbox.insert(tk.END, "• 87Sr/86Sr")

        # Axis assignment
        axis_frame = tk.Frame(isotope_frame, bg="white")
        axis_frame.pack(fill=tk.X, pady=2)

        # X-axis
        tk.Label(axis_frame, text="X:", bg="white", font=("Arial", 7, "bold")).grid(row=0, column=0, sticky='w', padx=1)
        self.x_var = tk.StringVar()
        x_combo = ttk.Combobox(axis_frame, textvariable=self.x_var,
                            values=[f"{info['display']} ({sys})" for sys, info in self.available_isotopes.items()],
                            width=15)
        x_combo.grid(row=0, column=1, padx=2, pady=1)

        # Y-axis
        tk.Label(axis_frame, text="Y:", bg="white", font=("Arial", 7, "bold")).grid(row=1, column=0, sticky='w', padx=1)
        self.y_var = tk.StringVar()
        y_combo = ttk.Combobox(axis_frame, textvariable=self.y_var,
                            values=[f"{info['display']} ({sys})" for sys, info in self.available_isotopes.items()],
                            width=15)
        y_combo.grid(row=1, column=1, padx=2, pady=1)

        # Z-axis
        tk.Label(axis_frame, text="Z:", bg="white", font=("Arial", 7, "bold")).grid(row=2, column=0, sticky='w', padx=1)
        self.z_var = tk.StringVar()
        z_combo = ttk.Combobox(axis_frame, textvariable=self.z_var,
                            values=["None"] + [f"{info['display']} ({sys})" for sys, info in self.available_isotopes.items()],
                            width=15)
        z_combo.grid(row=2, column=1, padx=2, pady=1)
        self.z_var.set("None")

        # ============ END-MEMBER SELECTION ============
        em_frame = tk.LabelFrame(left_panel, text="🏭 2. END-MEMBERS",
                                font=("Arial", 8, "bold"),
                                bg="white", padx=5, pady=3)
        em_frame.pack(fill=tk.X, padx=5, pady=3)

        # Notebook for end-member sources
        em_notebook = ttk.Notebook(em_frame, height=100)
        em_notebook.pack(fill=tk.X, pady=2)

        # Tab 1: Built-in reservoirs
        builtin_tab = tk.Frame(em_notebook, bg="white")
        em_notebook.add(builtin_tab, text="📚 Built-in")

        builtin_frame = tk.Frame(builtin_tab)
        builtin_frame.pack(fill=tk.BOTH, expand=True)

        self.builtin_listbox = tk.Listbox(builtin_frame, height=3, selectmode=tk.EXTENDED)
        builtin_scroll = tk.Scrollbar(builtin_frame, orient="vertical", command=self.builtin_listbox.yview)
        self.builtin_listbox.configure(yscrollcommand=builtin_scroll.set)

        for name in self.END_MEMBERS.keys():
            self.builtin_listbox.insert(tk.END, name)

        self.builtin_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=1, pady=1)
        builtin_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Tab 2: Custom end-members
        custom_tab = tk.Frame(em_notebook, bg="white")
        em_notebook.add(custom_tab, text="📁 Custom")

        tk.Button(custom_tab, text="📂 Load",
                command=self._load_custom_end_members,
                bg="#9b59b6", fg="white", font=("Arial", 7)).pack(pady=2)

        self.custom_listbox = tk.Listbox(custom_tab, height=2)
        self.custom_listbox.pack(fill=tk.X, padx=1, pady=1)

        # Tab 3: Manual entry with unit hints
        manual_tab = tk.Frame(em_notebook, bg="white")
        em_notebook.add(manual_tab, text="✏️ Manual")

        # Add instruction label
        tk.Label(manual_tab, text="Enter values matching selected axes:",
                font=("Arial", 7, "italic"), fg="#7f8c8d").pack(pady=1)

        manual_frame = tk.Frame(manual_tab)
        manual_frame.pack(pady=2)

        # Compact grid for manual entry
        tk.Label(manual_frame, text="Name:", font=("Arial", 7)).grid(row=0, column=0, sticky='w')
        self.manual_name = tk.Entry(manual_frame, width=10)
        self.manual_name.grid(row=0, column=1, padx=1)

        # Dynamic labels showing current axis selections
        tk.Label(manual_frame, text=f"X ({self.x_var.get() if self.x_var.get() else 'value'}):",
                font=("Arial", 7)).grid(row=1, column=0, sticky='w')
        self.manual_x = tk.Entry(manual_frame, width=10)
        self.manual_x.grid(row=1, column=1, padx=1)

        tk.Label(manual_frame, text=f"Y ({self.y_var.get() if self.y_var.get() else 'value'}):",
                font=("Arial", 7)).grid(row=2, column=0, sticky='w')
        self.manual_y = tk.Entry(manual_frame, width=10)
        self.manual_y.grid(row=2, column=1, padx=1)

        tk.Label(manual_frame, text=f"Z ({self.z_var.get() if self.z_var.get() != 'None' else 'optional'}):",
                font=("Arial", 7)).grid(row=3, column=0, sticky='w')
        self.manual_z = tk.Entry(manual_frame, width=10)
        self.manual_z.grid(row=3, column=1, padx=1)

        tk.Button(manual_tab, text="➕ Add",
                command=self._add_manual_end_member,
                bg="#27ae60", fg="white", font=("Arial", 7)).pack(pady=2)

        # ============ MODEL TYPE ============
        model_frame = tk.LabelFrame(left_panel, text="📐 3. CHOOSE MODEL",
                                font=("Arial", 8, "bold"),
                                bg="white", padx=5, pady=3)
        model_frame.pack(fill=tk.X, padx=5, pady=3)

        self.model_var = tk.StringVar(value="binary")

        # Create radio buttons in two columns for compactness
        left_models = tk.Frame(model_frame, bg="white")
        left_models.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right_models = tk.Frame(model_frame, bg="white")
        right_models.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        models_left = [
            ("binary", "Binary"),
            ("ternary", "Ternary"),
            ("montecarlo", "Monte Carlo"),
            ("mahalanobis", "Mahalanobis")
        ]

        models_right = [
            ("inversion_ls", "LS Inversion"),
            ("inversion_mcmc", "MCMC"),
            ("ree_inversion", "REE Inversion")
        ]

        for value, text in models_left:
            tk.Radiobutton(left_models, text=text,
                        variable=self.model_var, value=value,
                        bg="white", font=("Arial", 7)).pack(anchor=tk.W)

        for value, text in models_right:
            tk.Radiobutton(right_models, text=text,
                        variable=self.model_var, value=value,
                        bg="white", font=("Arial", 7)).pack(anchor=tk.W)

        # ============ INVERSION PARAMETERS ============
        inv_frame = tk.LabelFrame(left_panel, text="⚙️ 4. PARAMETERS",
                                font=("Arial", 8, "bold"),
                                bg="white", padx=5, pady=3)
        inv_frame.pack(fill=tk.X, padx=5, pady=3)

        # Compact grid
        tk.Label(inv_frame, text="Walkers:", bg="white", font=("Arial", 7)).grid(row=0, column=0, sticky='w', pady=1)
        self.mcmc_walkers = tk.Entry(inv_frame, width=6)
        self.mcmc_walkers.insert(0, "32")
        self.mcmc_walkers.grid(row=0, column=1, sticky='w', padx=2)

        tk.Label(inv_frame, text="Steps:", bg="white", font=("Arial", 7)).grid(row=1, column=0, sticky='w', pady=1)
        self.mcmc_steps = tk.Entry(inv_frame, width=6)
        self.mcmc_steps.insert(0, "5000")
        self.mcmc_steps.grid(row=1, column=1, sticky='w', padx=2)

        tk.Label(inv_frame, text="Burn-in:", bg="white", font=("Arial", 7)).grid(row=2, column=0, sticky='w', pady=1)
        self.mcmc_burnin = tk.Entry(inv_frame, width=6)
        self.mcmc_burnin.insert(0, "1000")
        self.mcmc_burnin.grid(row=2, column=1, sticky='w', padx=2)

        # Source Minerals - compact checkbox grid
        tk.Label(inv_frame, text="Minerals:", bg="white", font=("Arial", 7, "bold")).grid(row=3, column=0, columnspan=2, sticky='w', pady=(3,1))

        min_frame = tk.Frame(inv_frame, bg="white")
        min_frame.grid(row=4, column=0, columnspan=2, sticky='w')

        self.source_minerals = {}
        minerals = ['olivine', 'cpx', 'opx', 'garnet', 'plag', 'amph']
        full_names = ['olivine', 'clinopyroxene', 'orthopyroxene', 'garnet', 'plagioclase', 'amphibole']

        row, col = 0, 0
        for i, (abbr, full) in enumerate(zip(minerals, full_names)):
            var = tk.BooleanVar(value=(full in ['clinopyroxene', 'garnet']))
            cb = tk.Checkbutton(min_frame, text=abbr, variable=var, bg="white", font=("Arial", 6))
            cb.grid(row=row, column=col, sticky='w', padx=2)
            self.source_minerals[full] = var
            col += 1
            if col > 2:
                col = 0
                row += 1

        # REE Sample Selection
        tk.Label(inv_frame, text="REE Sample:", bg="white", font=("Arial", 7, "bold")).grid(row=5, column=0, sticky='w', pady=(3,1))
        self.ree_sample_var = tk.StringVar(value="First")
        ree_sample_combo = ttk.Combobox(inv_frame, textvariable=self.ree_sample_var,
                                    values=["First", "Average", "All"],
                                    width=8, state="readonly")
        ree_sample_combo.grid(row=5, column=1, sticky='w', padx=2)

        # ============ RUN BUTTON ============
        run_frame = tk.Frame(left_panel, bg="white")
        run_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Button(run_frame, text="▶ RUN",
                command=self._run_model_dispatcher,
                bg="#e67e22", fg="white",
                font=("Arial", 10, "bold"),
                width=10).pack()

        # ============ SEND BACK TO MAIN APP ============
        send_frame = tk.Frame(left_panel, bg="white")
        send_frame.pack(fill=tk.X, padx=5, pady=2)

        tk.Button(send_frame, text="📤 Send",
                command=self._send_results_to_app,
                bg="#27ae60", fg="white",
                font=("Arial", 7, "bold"),
                width=8).pack()

        # ============ RIGHT PANEL - VISUALIZATION & RESULTS ============
        right_panel = tk.Frame(main_paned, bg="#ecf0f1", relief=tk.RAISED, borderwidth=1)
        main_paned.add(right_panel, width=550)

        # ============ NOTEBOOK FOR TABS ============
        self.notebook = ttk.Notebook(right_panel)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)

        # Tab 1: Mixing Plot
        plot_tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(plot_tab, text="📈 Plot")

        # Matplotlib figure - smaller size
        self.fig = plt.figure(figsize=(6, 4), dpi=80)
        self.fig.patch.set_facecolor('white')

        # Will create axes based on model type (2D or 3D)
        self.ax = None
        self.ax3d = None

        self.canvas = FigureCanvasTkAgg(self.fig, plot_tab)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Compact toolbar
        toolbar_frame = tk.Frame(plot_tab, height=20)
        toolbar_frame.pack(fill=tk.X)
        toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        toolbar.update()

        # Tab 2: Mixing Proportions
        props_tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(props_tab, text="📊 Proportions")

        # Create tree with smaller columns
        self.props_tree = ttk.Treeview(props_tab, columns=('Sample', 'EM1', 'EM2', 'EM3', 'Dist'),
                                    show='headings', height=8)

        self.props_tree.heading('Sample', text='Sample')
        self.props_tree.heading('EM1', text='EM1 %')
        self.props_tree.heading('EM2', text='EM2 %')
        self.props_tree.heading('EM3', text='EM3 %')
        self.props_tree.heading('Dist', text='D')

        for col in ['Sample', 'EM1', 'EM2', 'EM3', 'Dist']:
            self.props_tree.column(col, width=60, anchor='center')

        scrollbar = ttk.Scrollbar(props_tab, orient=tk.VERTICAL, command=self.props_tree.yview)
        self.props_tree.configure(yscrollcommand=scrollbar.set)

        self.props_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=3, pady=3)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Tab 3: Inversion Results
        inv_tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(inv_tab, text="🔍 Inversion")

        self.inv_tree = ttk.Treeview(inv_tab, columns=('Parameter', 'Value', '2.5%', '97.5%', 'Units'),
                                    show='headings', height=8)

        self.inv_tree.heading('Parameter', text='Parameter')
        self.inv_tree.heading('Value', text='Best')
        self.inv_tree.heading('2.5%', text='2.5%')
        self.inv_tree.heading('97.5%', text='97.5%')
        self.inv_tree.heading('Units', text='Units')

        for col in ['Parameter', 'Value', '2.5%', '97.5%', 'Units']:
            self.inv_tree.column(col, width=70, anchor='center')

        inv_scroll = ttk.Scrollbar(inv_tab, orient=tk.VERTICAL, command=self.inv_tree.yview)
        self.inv_tree.configure(yscrollcommand=inv_scroll.set)

        self.inv_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=3, pady=3)
        inv_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Tab 4: REE Patterns
        ree_tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(ree_tab, text="📈 REE")

        self.ree_fig, self.ree_ax = plt.subplots(figsize=(5, 3))
        self.ree_fig.patch.set_facecolor('white')
        self.ree_canvas = FigureCanvasTkAgg(self.ree_fig, ree_tab)
        self.ree_canvas.draw()
        self.ree_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Tab 5: MCMC Diagnostics
        mcmc_tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(mcmc_tab, text="📊 MCMC")

        self.mcmc_fig, (self.mcmc_trace_ax, self.mcmc_corner_ax) = plt.subplots(1, 2, figsize=(6, 2.5))
        self.mcmc_fig.patch.set_facecolor('white')
        self.mcmc_canvas = FigureCanvasTkAgg(self.mcmc_fig, mcmc_tab)
        self.mcmc_canvas.draw()
        self.mcmc_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Tab 6: Statistical Report
        stats_tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(stats_tab, text="📋 Report")

        text_frame = tk.Frame(stats_tab)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)

        scrollbar_text = tk.Scrollbar(text_frame)
        scrollbar_text.pack(side=tk.RIGHT, fill=tk.Y)

        self.results_text = tk.Text(text_frame, wrap=tk.WORD,
                                font=("Courier", 8),
                                yscrollcommand=scrollbar_text.set,
                                bg="white", relief=tk.FLAT,
                                padx=5, pady=5, height=10)
        self.results_text.pack(fill=tk.BOTH, expand=True)
        scrollbar_text.config(command=self.results_text.yview)

        # ============ BOTTOM STATUS BAR ============
        status_bar = tk.Frame(self.window, bg="#ecf0f1", height=25)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        status_bar.pack_propagate(False)

        self.stats_label = tk.Label(status_bar,
                                text="Ready",
                                font=("Arial", 7),
                                bg="#ecf0f1", fg="#2c3e50")
        self.stats_label.pack(side=tk.LEFT, padx=5)

        # Add progress bar
        self.progress_bar = ttk.Progressbar(status_bar, mode='indeterminate', length=100)
        self.progress_bar.pack(side=tk.LEFT, padx=5)

        # Export buttons
        tk.Button(status_bar, text="💾 Export",
                command=self._export_results,
                font=("Arial", 6), bg="#3498db", fg="white",
                padx=4).pack(side=tk.RIGHT, padx=2)

        tk.Button(status_bar, text="📊 Fig",
                command=self._export_figure,
                font=("Arial", 6), bg="#3498db", fg="white",
                padx=4).pack(side=tk.RIGHT, padx=2)

        # Initialize plot
        self._initialize_plot()

    def _show_progress(self, title, message):
        """Show a progress dialog for long operations"""
        progress_window = tk.Toplevel(self.window)
        progress_window.title(title)
        progress_window.geometry("300x100")
        progress_window.transient(self.window)
        progress_window.grab_set()

        # Center on parent
        progress_window.update_idletasks()
        x = self.window.winfo_x() + (self.window.winfo_width() // 2) - 150
        y = self.window.winfo_y() + (self.window.winfo_height() // 2) - 50
        progress_window.geometry(f"+{x}+{y}")

        tk.Label(progress_window, text=message, pady=10).pack()

        progress = ttk.Progressbar(progress_window, mode='indeterminate', length=250)
        progress.pack(pady=10)
        progress.start(10)

        # Add cancel button
        cancel_var = tk.BooleanVar(value=False)

        def cancel():
            cancel_var.set(True)
            progress_window.destroy()

        tk.Button(progress_window, text="Cancel", command=cancel).pack()

        # Force update
        progress_window.update()

        return progress_window, cancel_var

    def _add_manual_end_member(self):
        """Add manually entered end-member with unit checking"""
        name = self.manual_name.get().strip()
        x_val = self.manual_x.get().strip()
        y_val = self.manual_y.get().strip()
        z_val = self.manual_z.get().strip()

        if not name or not x_val or not y_val:
            messagebox.showwarning("Missing Data", "Name, X, and Y values required!")
            return

        try:
            em = {
                'name': name,
                'color': '#9b59b6',  # Purple for custom
                'manual': True
            }

            # Add values with unit verification
            value_warnings = []

            if self.x_var.get():
                sys_name = self.x_var.get().split('(')[-1].rstrip(')')
                if sys_name in self.available_isotopes:
                    col = self.available_isotopes[sys_name]['column']
                    x_float = float(x_val)
                    em[col] = x_float

                    # Quick sanity check based on isotope system
                    if 'Sr' in sys_name and (x_float < 0.7 or x_float > 0.75):
                        value_warnings.append(f"X value {x_float} unusual for Sr isotopes (typical: 0.702-0.720)")
                    elif 'Nd' in sys_name and (x_float < 0.511 or x_float > 0.514):
                        value_warnings.append(f"X value {x_float} unusual for Nd isotopes (typical: 0.511-0.514)")
                    elif 'Pb' in sys_name and (x_float < 15 or x_float > 25):
                        value_warnings.append(f"X value {x_float} unusual for Pb isotopes (typical: 15-22)")

            if self.y_var.get():
                sys_name = self.y_var.get().split('(')[-1].rstrip(')')
                if sys_name in self.available_isotopes:
                    col = self.available_isotopes[sys_name]['column']
                    y_float = float(y_val)
                    em[col] = y_float

                    # Similar checks for Y
                    if 'Sr' in sys_name and (y_float < 0.7 or y_float > 0.75):
                        value_warnings.append(f"Y value {y_float} unusual for Sr isotopes")
                    elif 'Nd' in sys_name and (y_float < 0.511 or y_float > 0.514):
                        value_warnings.append(f"Y value {y_float} unusual for Nd isotopes")

            if z_val and self.z_var.get() != "None":
                sys_name = self.z_var.get().split('(')[-1].rstrip(')')
                if sys_name in self.available_isotopes:
                    col = self.available_isotopes[sys_name]['column']
                    z_float = float(z_val)
                    em[col] = z_float

            # Show warnings if any
            if value_warnings:
                if not messagebox.askyesno("Value Verification",
                                        "\n".join(value_warnings) +
                                        "\n\nAdd anyway?"):
                    return

            # Add to custom list
            self.custom_end_members.append(em)
            self.custom_listbox.insert(tk.END, name)

            # Clear entries
            self.manual_name.delete(0, tk.END)
            self.manual_x.delete(0, tk.END)
            self.manual_y.delete(0, tk.END)
            self.manual_z.delete(0, tk.END)

            self._log_result(f"➕ Added manual end-member: {name} with values X={x_val}, Y={y_val}")

        except ValueError as e:
            messagebox.showerror("Invalid Number", f"Please enter numeric values: {str(e)}")

    def _load_custom_end_members(self):
        """Load custom end-members from CSV"""
        path = filedialog.askopenfilename(
            title="Load End-Member Compositions",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")]
        )

        if not path:
            return

        try:
            if path.endswith('.csv'):
                df = pd.read_csv(path)
            else:
                df = pd.read_excel(path)

            # Store in custom list
            self.custom_end_members = df.to_dict('records')

            # Update listbox
            self.custom_listbox.delete(0, tk.END)
            for i, em in enumerate(self.custom_end_members[:5]):
                name = em.get('Name', em.get('name', f"EM{i+1}"))
                self.custom_listbox.insert(tk.END, name)

            self._log_result(f"📁 Loaded {len(self.custom_end_members)} custom end-members")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load: {str(e)}")

    def _get_selected_end_members(self):
        """Get list of selected end-members from UI"""
        end_members = []

        # Get built-in selections
        builtin_sel = self.builtin_listbox.curselection()
        for idx in builtin_sel:
            name = self.builtin_listbox.get(idx)
            if name in self.END_MEMBERS:
                end_members.append(self.END_MEMBERS[name])

        # Get custom selections
        custom_sel = self.custom_listbox.curselection()
        for idx in custom_sel:
            if idx < len(self.custom_end_members):
                end_members.append(self.custom_end_members[idx])

        return end_members

    def _get_em_value(self, em, col_name):
        """Retrieve an isotope value from an end-member dict by column name, with fallbacks."""
        for key in [col_name, col_name.replace('/', '_'), col_name.split('/')[0]]:
            if key in em:
                return em[key]
        # Fallback: return first numeric value
        for v in em.values():
            if isinstance(v, (int, float)):
                return v
        return None

    def _initialize_plot(self):
        """Initialize empty plot"""
        self.fig.clear()
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel('X Axis')
        self.ax.set_ylabel('Y Axis')
        self.ax.set_title('Isotope Mixing Diagram')
        self.ax.grid(True, alpha=0.3, linestyle='--')
        self.canvas.draw()

    def _run_model_dispatcher(self):
        """Main dispatcher for mixing models and inversion"""
        if self.samples is None or len(self.samples) == 0:
            messagebox.showwarning("No Data", "No samples in main app!")
            return

        model_type = self.model_var.get()

        if model_type in ["binary", "ternary", "montecarlo", "mahalanobis"]:
            self._run_mixing_model()
        elif model_type == "inversion_ls":
            self._least_squares_inversion()
        elif model_type == "inversion_mcmc":
            self._bayesian_mcmc_inversion()
        elif model_type == "ree_inversion":
            self._ree_pattern_inversion()

    def _run_mixing_model(self):
        """Run standard mixing models (existing code)"""
        # Get selected isotopes
        if not self.x_var.get() or not self.y_var.get():
            messagebox.showwarning("Select Isotopes", "Choose X and Y axes first!")
            return

        # Parse isotope selections
        x_system = self.x_var.get().split('(')[-1].rstrip(')')
        y_system = self.y_var.get().split('(')[-1].rstrip(')')

        if x_system not in self.available_isotopes or y_system not in self.available_isotopes:
            messagebox.showerror("Error", "Invalid isotope selection")
            return

        # Parse Z if selected
        z_system = None
        if self.z_var.get() != "None":
            z_system = self.z_var.get().split('(')[-1].rstrip(')')
            if z_system not in self.available_isotopes:
                messagebox.showerror("Error", "Invalid Z isotope selection")
                return

        # Get end-members
        end_members = self._get_selected_end_members()
        if len(end_members) < 2:
            messagebox.showwarning("Select End-Members", "Select at least 2 end-members!")
            return

        model_type = self.model_var.get()

        if model_type == "binary" and len(end_members) >= 2:
            self._binary_mixing(x_system, y_system, end_members[:2])
        elif model_type == "ternary" and len(end_members) >= 3:
            if z_system:
                self._ternary_mixing_3d(x_system, y_system, z_system, end_members[:3])
            else:
                self._ternary_mixing_2d(x_system, y_system, end_members[:3])
        elif model_type == "montecarlo":
            self._monte_carlo_mixing(x_system, y_system, end_members[:2])
        elif model_type == "mahalanobis":
            self._mahalanobis_provenance(x_system, y_system, end_members)

        self.notebook.select(0)  # Show plot tab

    # ============ EXISTING MIXING METHODS ============

    def _binary_mixing(self, x_sys, y_sys, end_members):
        """Binary mixing model (existing implementation)"""
        try:
            # Get data
            x_col = self.available_isotopes[x_sys]['column']
            y_col = self.available_isotopes[y_sys]['column']

            x_data = self.samples[x_col].values
            y_data = self.samples[y_col].values

            # Get end-member compositions
            em1 = end_members[0]
            em2 = end_members[1]

            # Extract isotope values
            em1_x = self._get_em_value(em1, x_col)
            em1_y = self._get_em_value(em1, y_col)
            em2_x = self._get_em_value(em2, x_col)
            em2_y = self._get_em_value(em2, y_col)

            if None in [em1_x, em1_y, em2_x, em2_y]:
                messagebox.showerror("Error", "End-members missing required isotope ratios")
                return

            # Clear plot and set up 2D axes
            self.fig.clear()
            self.ax = self.fig.add_subplot(111)

            # Plot end-members
            self.ax.scatter([em1_x], [em1_y], s=150, c='red', marker='s',  # Reduced size
                          edgecolors='black', linewidth=1.5, zorder=10, label=em1.get('name', 'EM1'))
            self.ax.scatter([em2_x], [em2_y], s=150, c='blue', marker='s',
                          edgecolors='black', linewidth=1.5, zorder=10, label=em2.get('name', 'EM2'))

            # Generate mixing curve
            f = np.linspace(0, 1, 100)

            # Binary mixing equation (after Faure, 1986)
            # For isotope ratios, mixing is linear in isotope space
            mix_x = em1_x * (1-f) + em2_x * f
            mix_y = em1_y * (1-f) + em2_y * f

            # Plot mixing curve
            self.ax.plot(mix_x, mix_y, 'k-', linewidth=1.5, alpha=0.8, label='Binary mixing line')

            # Plot samples
            self.ax.scatter(x_data, y_data, c='#2c3e50', s=60, alpha=0.7,  # Reduced size
                          edgecolors='white', linewidth=1,
                          label='Samples', zorder=5)

            # Calculate mixing proportions for each sample
            proportions = []
            mahalanobis_distances = []

            for i, (x, y) in enumerate(zip(x_data, y_data)):
                # Find closest point on mixing line
                distances = np.sqrt((mix_x - x)**2 + (mix_y - y)**2)
                idx = np.argmin(distances)

                prop = f[idx]
                proportions.append(prop)

                # Calculate Mahalanobis distance (simplified)
                cov = np.cov([x_data, y_data])
                try:
                    inv_cov = np.linalg.inv(cov + np.eye(2)*1e-6)
                    point = np.array([x, y])
                    line_point = np.array([mix_x[idx], mix_y[idx]])
                    diff = point - line_point
                    m_dist = np.sqrt(diff @ inv_cov @ diff)
                    mahalanobis_distances.append(m_dist)
                except:
                    mahalanobis_distances.append(0)

                # Draw tie line
                self.ax.plot([x, mix_x[idx]], [y, mix_y[idx]],
                           'gray', linewidth=0.3, alpha=0.2)  # Thinner lines

            # Store results
            self.current_results = {
                'model': 'binary',
                'x_system': x_sys,
                'y_system': y_sys,
                'em1': em1,
                'em2': em2,
                'proportions': proportions,
                'mahalanobis': mahalanobis_distances
            }

            # Update proportions table
            self.props_tree.delete(*self.props_tree.get_children())
            for i, (prop, m_dist) in enumerate(zip(proportions, mahalanobis_distances)):
                sample_id = self.samples.iloc[i].get('Sample_ID', f"Sample_{i+1}")
                self.props_tree.insert('', tk.END, values=(
                    sample_id,
                    f"{100*(1-prop):.1f}",
                    f"{100*prop:.1f}",
                    "-",
                    f"{m_dist:.2f}"
                ))

            # Log results
            self._log_result(f"📈 Binary Mixing Model Results")
            self._log_result(f"   End-member 1: {em1.get('name', 'EM1')} ({em1_x:.4f}, {em1_y:.4f})")
            self._log_result(f"   End-member 2: {em2.get('name', 'EM2')} ({em2_x:.4f}, {em2_y:.4f})")
            self._log_result(f"   Mean proportion EM2: {100*np.mean(proportions):.1f}%")
            self._log_result(f"   Range: {100*np.min(proportions):.1f}% - {100*np.max(proportions):.1f}%")
            self._log_result(f"   Samples analyzed: {len(proportions)}")

            # Format plot
            self.ax.set_xlabel(self.available_isotopes[x_sys]['display'])
            self.ax.set_ylabel(self.available_isotopes[y_sys]['display'])
            self.ax.set_title('Binary Mixing Model')
            self.ax.grid(True, alpha=0.3, linestyle='--')
            self.ax.legend(loc='best', fontsize=8)  # Smaller legend

            self.canvas.draw()
            self.status_indicator.config(text="● BINARY MIXING COMPLETE", fg="#2ecc71")

        except Exception as e:
            messagebox.showerror("Error", str(e))
            traceback.print_exc()

    def _ternary_mixing_2d(self, x_sys, y_sys, end_members):
        """Ternary mixing in 2D (existing implementation)"""
        try:
            # Get data
            x_col = self.available_isotopes[x_sys]['column']
            y_col = self.available_isotopes[y_sys]['column']

            x_data = self.samples[x_col].values
            y_data = self.samples[y_col].values

            # Get end-member compositions
            ems = end_members[:3]
            em_names = [em.get('name', f'EM{i+1}') for i, em in enumerate(ems)]
            colors = [em.get('color', f'C{i}') for i, em in enumerate(ems)]

            # Extract values
            em_values = []
            for em in ems:
                em_x = self._get_em_value(em, x_col)
                em_y = self._get_em_value(em, y_col)
                if em_x is None or em_y is None:
                    messagebox.showerror("Error", f"End-member {em.get('name', 'unknown')} missing required isotope ratios")
                    return
                em_values.append((em_x, em_y))

            # Clear plot and set up 2D axes
            self.fig.clear()
            self.ax = self.fig.add_subplot(111)

            # Plot end-members
            for i, ((em_x, em_y), name, color) in enumerate(zip(em_values, em_names, colors)):
                self.ax.scatter(em_x, em_y, s=150, c=color, marker='s',  # Reduced size
                              edgecolors='black', linewidth=1.5, zorder=10, label=name)

            # Generate ternary mixing field (convex hull of end-members)
            points = np.array(em_values)
            hull = ConvexHull(points)

            # Plot mixing field (triangle)
            triangle = Polygon(points[hull.vertices], alpha=0.1, color='gray',
                             label='Ternary mixing space')
            self.ax.add_patch(triangle)

            # Plot samples
            scatter = self.ax.scatter(x_data, y_data, c='#2c3e50', s=60, alpha=0.7,  # Reduced size
                                     edgecolors='white', linewidth=1,
                                     label='Samples', zorder=5)

            # Calculate ternary mixing proportions for each sample
            # Using barycentric coordinates
            proportions = []
            for x, y in zip(x_data, y_data):
                # Convert to barycentric coordinates
                # Method: solve for weights w1, w2, w3 such that:
                # x = w1*x1 + w2*x2 + w3*x3
                # y = w1*y1 + w2*y2 + w3*y3
                # w1 + w2 + w3 = 1
                A = np.array([
                    [em_values[0][0], em_values[1][0], em_values[2][0]],
                    [em_values[0][1], em_values[1][1], em_values[2][1]],
                    [1, 1, 1]
                ])
                b = np.array([x, y, 1])

                try:
                    w = np.linalg.solve(A, b)
                    # Clip to [0,1] and renormalize
                    w = np.clip(w, 0, 1)
                    w = w / np.sum(w)
                    proportions.append(w)
                except:
                    proportions.append([1/3, 1/3, 1/3])

                # Draw tie lines to vertices (optional - would clutter)
                # for (em_x, em_y) in em_values:
                #     self.ax.plot([x, em_x], [y, em_y], 'gray', linewidth=0.3, alpha=0.2)

            # Store results
            self.current_results = {
                'model': 'ternary',
                'x_system': x_sys,
                'y_system': y_sys,
                'ems': ems,
                'proportions': proportions
            }

            # Update proportions table
            self.props_tree.delete(*self.props_tree.get_children())
            for i, w in enumerate(proportions):
                sample_id = self.samples.iloc[i].get('Sample_ID', f"Sample_{i+1}")
                self.props_tree.insert('', tk.END, values=(
                    sample_id,
                    f"{100*w[0]:.1f}",
                    f"{100*w[1]:.1f}",
                    f"{100*w[2]:.1f}",
                    "-"
                ))

            # Log results
            self._log_result(f"🔺 Ternary Mixing Model Results (2D)")
            self._log_result(f"   End-members: {', '.join(em_names)}")
            self._log_result(f"   Mean proportions: EM1={100*np.mean([w[0] for w in proportions]):.1f}%, "
                           f"EM2={100*np.mean([w[1] for w in proportions]):.1f}%, "
                           f"EM3={100*np.mean([w[2] for w in proportions]):.1f}%")
            self._log_result(f"   Samples analyzed: {len(proportions)}")

            # Format plot
            self.ax.set_xlabel(self.available_isotopes[x_sys]['display'])
            self.ax.set_ylabel(self.available_isotopes[y_sys]['display'])
            self.ax.set_title('Ternary Mixing Model (2D)')
            self.ax.grid(True, alpha=0.3, linestyle='--')
            self.ax.legend(loc='best', fontsize=8)

            self.canvas.draw()
            self.status_indicator.config(text="● TERNARY MIXING COMPLETE", fg="#2ecc71")

        except Exception as e:
            messagebox.showerror("Ternary Mixing Error", str(e))
            traceback.print_exc()

    def _ternary_mixing_3d(self, x_sys, y_sys, z_sys, end_members):
        """Ternary mixing in 3D (existing implementation)"""
        try:
            # Get data
            x_col = self.available_isotopes[x_sys]['column']
            y_col = self.available_isotopes[y_sys]['column']
            z_col = self.available_isotopes[z_sys]['column']

            x_data = self.samples[x_col].values
            y_data = self.samples[y_col].values
            z_data = self.samples[z_col].values

            # Get end-member compositions
            ems = end_members[:3]
            em_names = [em.get('name', f'EM{i+1}') for i, em in enumerate(ems)]
            colors = [em.get('color', f'C{i}') for i, em in enumerate(ems)]

            # Extract values
            em_values = []
            for em in ems:
                em_x = self._get_em_value(em, x_col)
                em_y = self._get_em_value(em, y_col)
                em_z = self._get_em_value(em, z_col)

                if None in [em_x, em_y, em_z]:
                    messagebox.showerror("Error", f"End-member {em.get('name', 'unknown')} missing required isotope ratios")
                    return
                em_values.append((em_x, em_y, em_z))

            # Clear plot and set up 3D axes
            self.fig.clear()
            self.ax3d = self.fig.add_subplot(111, projection='3d')

            # Plot end-members
            for i, ((em_x, em_y, em_z), name, color) in enumerate(zip(em_values, em_names, colors)):
                self.ax3d.scatter([em_x], [em_y], [em_z], s=150, c=color, marker='s',  # Reduced size
                                edgecolors='black', linewidth=1.5, depthshade=False,
                                label=name)

            # Plot mixing lines (edges of ternary tetrahedron)
            edges = [(0,1), (1,2), (2,0)]
            for i, j in edges:
                self.ax3d.plot([em_values[i][0], em_values[j][0]],
                              [em_values[i][1], em_values[j][1]],
                              [em_values[i][2], em_values[j][2]],
                              'k-', linewidth=1, alpha=0.5)  # Thinner lines

            # Plot samples
            self.ax3d.scatter(x_data, y_data, z_data, c='#2c3e50', s=50, alpha=0.7,  # Reduced size
                            edgecolors='white', linewidth=1,
                            label='Samples', depthshade=False)

            # Calculate ternary mixing proportions in 3D
            # Using barycentric coordinates in 3D
            proportions = []
            for x, y, z in zip(x_data, y_data, z_data):
                # Solve for weights
                A = np.array([
                    [em_values[0][0], em_values[1][0], em_values[2][0]],
                    [em_values[0][1], em_values[1][1], em_values[2][1]],
                    [em_values[0][2], em_values[1][2], em_values[2][2]]
                ])
                b = np.array([x, y, z])

                try:
                    w = np.linalg.solve(A, b)
                    # Clip to [0,1] and ensure sum to 1
                    w = np.clip(w, 0, 1)
                    w = w / np.sum(w)
                    proportions.append(w)
                except:
                    proportions.append([1/3, 1/3, 1/3])

            # Store results
            self.current_results = {
                'model': 'ternary_3d',
                'x_system': x_sys,
                'y_system': y_sys,
                'z_system': z_sys,
                'ems': ems,
                'proportions': proportions
            }

            # Update proportions table
            self.props_tree.delete(*self.props_tree.get_children())
            for i, w in enumerate(proportions):
                sample_id = self.samples.iloc[i].get('Sample_ID', f"Sample_{i+1}")
                self.props_tree.insert('', tk.END, values=(
                    sample_id,
                    f"{100*w[0]:.1f}",
                    f"{100*w[1]:.1f}",
                    f"{100*w[2]:.1f}",
                    "-"
                ))

            # Log results
            self._log_result(f"🔺 Ternary Mixing Model Results (3D)")
            self._log_result(f"   End-members: {', '.join(em_names)}")
            self._log_result(f"   Mean proportions: EM1={100*np.mean([w[0] for w in proportions]):.1f}%, "
                           f"EM2={100*np.mean([w[1] for w in proportions]):.1f}%, "
                           f"EM3={100*np.mean([w[2] for w in proportions]):.1f}%")
            self._log_result(f"   Samples analyzed: {len(proportions)}")

            # Format plot
            self.ax3d.set_xlabel(self.available_isotopes[x_sys]['display'])
            self.ax3d.set_ylabel(self.available_isotopes[y_sys]['display'])
            self.ax3d.set_zlabel(self.available_isotopes[z_sys]['display'])
            self.ax3d.set_title('Ternary Mixing Model (3D)')
            self.ax3d.legend(loc='best', fontsize=8)

            # Adjust view
            self.ax3d.view_init(elev=20, azim=-45)

            self.canvas.draw()
            self.status_indicator.config(text="● 3D TERNARY MIXING COMPLETE", fg="#2ecc71")

        except Exception as e:
            messagebox.showerror("3D Ternary Mixing Error", str(e))
            traceback.print_exc()

    def _monte_carlo_mixing(self, x_sys, y_sys, end_members):
        """Monte Carlo simulation with progress bar"""
        try:
            n_iterations = 10000
            batch_size = 100  # Update progress every 100 iterations

            # Get data
            x_col = self.available_isotopes[x_sys]['column']
            y_col = self.available_isotopes[y_sys]['column']
            x_data = self.samples[x_col].values
            y_data = self.samples[y_col].values

            # Get uncertainties
            x_unc = self.available_isotopes[x_sys]['uncertainty']
            y_unc = self.available_isotopes[y_sys]['uncertainty']

            # Get end-members
            em1 = end_members[0]
            em2 = end_members[1]

            # Extract end-member values
            em1_x = self._get_em_value(em1, x_col)
            em1_y = self._get_em_value(em1, y_col)
            em2_x = self._get_em_value(em2, x_col)
            em2_y = self._get_em_value(em2, y_col)

            if None in [em1_x, em1_y, em2_x, em2_y]:
                messagebox.showerror("Error",
                    "End-members missing required isotope ratios.\n"
                    "Please check end-member values or use different end-members.")
                return

            # Show progress window
            progress_window, cancel_var = self._show_progress(
                "Monte Carlo Simulation",
                f"Running {n_iterations:,} iterations..."
            )

            # Monte Carlo iterations with progress updates
            all_proportions = []

            # Start progress bar in status bar
            self.progress_bar.start(10)
            self.stats_label.config(text="Running Monte Carlo...")

            for i in range(n_iterations):
                # Check if cancelled
                if cancel_var.get():
                    self._log_result("❌ Monte Carlo cancelled by user")
                    progress_window.destroy()
                    self.progress_bar.stop()
                    self.stats_label.config(text="Cancelled")
                    return

                # Perturb end-members within uncertainty
                em1_x_pert = em1_x + np.random.normal(0, x_unc)
                em1_y_pert = em1_y + np.random.normal(0, y_unc)
                em2_x_pert = em2_x + np.random.normal(0, x_unc)
                em2_y_pert = em2_y + np.random.normal(0, y_unc)

                # For each sample
                for j in range(len(x_data)):
                    # Perturb sample
                    x_pert = x_data[j] + np.random.normal(0, x_unc)
                    y_pert = y_data[j] + np.random.normal(0, y_unc)

                    # Calculate mixing proportion
                    vec_x = em2_x_pert - em1_x_pert
                    vec_y = em2_y_pert - em1_y_pert

                    sample_vec_x = x_pert - em1_x_pert
                    sample_vec_y = y_pert - em1_y_pert

                    dot_product = sample_vec_x*vec_x + sample_vec_y*vec_y
                    norm_sq = vec_x*vec_x + vec_y*vec_y

                    if norm_sq > 0:
                        f = dot_product / norm_sq
                        f = np.clip(f, 0, 1)
                        all_proportions.append(f)

                # Update progress periodically
                if (i + 1) % batch_size == 0:
                    progress = (i + 1) / n_iterations * 100
                    self.stats_label.config(text=f"Monte Carlo: {progress:.1f}%")
                    progress_window.update()

            # Close progress window
            progress_window.destroy()
            self.progress_bar.stop()
            self.stats_label.config(text="Processing results...")

            self.monte_carlo_results = all_proportions

            # Create figure for Monte Carlo results
            self.fig.clear()
            ax1 = self.fig.add_subplot(1, 2, 1)
            ax2 = self.fig.add_subplot(1, 2, 2)

            # Histogram
            ax1.hist(all_proportions, bins=50, color='#3498db', alpha=0.7,
                edgecolor='white', linewidth=0.5)
            ax1.axvline(np.mean(all_proportions), color='red', linestyle='--',
                    linewidth=2, label=f"Mean: {np.mean(all_proportions):.3f}")
            ax1.axvline(np.percentile(all_proportions, 2.5), color='gray',
                    linestyle=':', linewidth=1.5)
            ax1.axvline(np.percentile(all_proportions, 97.5), color='gray',
                    linestyle=':', linewidth=1.5)

            ax1.set_xlabel('Proportion of EM2')
            ax1.set_ylabel('Frequency')
            ax1.set_title(f'Monte Carlo (n={n_iterations:,})')
            ax1.legend(fontsize=7)
            ax1.grid(True, alpha=0.3)

            # Q-Q plot
            stats.probplot(all_proportions, dist="norm", plot=ax2)
            ax2.set_title('Q-Q Plot')
            ax2.grid(True, alpha=0.3)

            self.fig.tight_layout()
            self.canvas.draw()

            # Statistics
            mean_prop = np.mean(all_proportions)
            std_prop = np.std(all_proportions)
            ci_low, ci_high = np.percentile(all_proportions, [2.5, 97.5])

            self._log_result(f"🎲 Monte Carlo Simulation")
            self._log_result(f"   Iterations: {n_iterations:,}")
            self._log_result(f"   Mean EM2 proportion: {100*mean_prop:.1f}%")
            self._log_result(f"   Standard deviation: {100*std_prop:.2f}%")
            self._log_result(f"   95% CI: [{100*ci_low:.1f}%, {100*ci_high:.1f}%]")
            self._log_result(f"   2σ range: {100*(ci_high-ci_low):.1f}%")

            self.status_indicator.config(text="● MONTE CARLO COMPLETE", fg="#2ecc71")
            self.stats_label.config(text="Ready")

        except Exception as e:
            messagebox.showerror("Monte Carlo Error", str(e))
            traceback.print_exc()
            if hasattr(self, 'progress_bar'):
                self.progress_bar.stop()
            self.stats_label.config(text="Error")

    def _mahalanobis_provenance(self, x_sys, y_sys, end_members):
        """Mahalanobis distance for provenance with improved covariance estimation"""
        try:
            # Get data
            x_col = self.available_isotopes[x_sys]['column']
            y_col = self.available_isotopes[y_sys]['column']
            x_data = self.samples[x_col].values
            y_data = self.samples[y_col].values

            # Ask user if they want to use per-end-member covariance
            use_global = messagebox.askyesno(
                "Covariance Method",
                "Use global data covariance for all end-members?\n"
                "Yes = Global covariance (simpler)\n"
                "No = Calculate separate covariance for each end-member (needs group assignments)",
                parent=self.window
            )

            # Clear plot
            self.fig.clear()
            self.ax = self.fig.add_subplot(111)

            # Plot samples
            self.ax.scatter(x_data, y_data, c='#2c3e50', s=60, alpha=0.7,
                        edgecolors='white', linewidth=1, label='Samples', zorder=5)

            # Calculate global covariance if needed
            if use_global:
                data = np.vstack([x_data, y_data]).T
                cov = np.cov(data.T)
                cov += np.eye(2) * 1e-10  # Regularization
                inv_cov = np.linalg.inv(cov)
                chi2_val = chi2.ppf(0.95, df=2)

            # Confidence ellipses for each end-member
            for i, em in enumerate(end_members):
                # Get end-member composition
                em_x = self._get_em_value(em, x_col)
                em_y = self._get_em_value(em, y_col)

                if em_x is None or em_y is None:
                    self._log_result(f"⚠️ End-member {em.get('name', 'unknown')} missing values, skipping")
                    continue

                # Calculate Mahalanobis distances
                distances = []

                if not use_global:
                    # For per-end-member covariance, we need to identify samples belonging to this group
                    # This is a simplified approach - you might want to add group assignment in UI
                    # For now, use all samples with small weights based on proximity
                    weights = np.exp(-((x_data - em_x)**2 + (y_data - em_y)**2) / (2 * np.std(x_data)**2))
                    weights = weights / np.sum(weights)

                    # Weighted covariance
                    data = np.vstack([x_data, y_data]).T
                    mean = np.array([em_x, em_y])
                    cov = np.zeros((2, 2))
                    for j, (x, y) in enumerate(data):
                        diff = np.array([x - mean[0], y - mean[1]]).reshape(-1, 1)
                        cov += weights[j] * (diff @ diff.T)
                    cov += np.eye(2) * 1e-10
                    inv_cov = np.linalg.inv(cov)
                    chi2_val = chi2.ppf(0.95, df=2)

                # Calculate distances for all samples
                for x, y in zip(x_data, y_data):
                    diff = np.array([x - em_x, y - em_y])
                    m_dist = np.sqrt(diff @ inv_cov @ diff)
                    distances.append(m_dist)

                # Plot end-member
                color = em.get('color', f'C{i}')
                self.ax.scatter(em_x, em_y, s=150, c=color, marker='s',
                            edgecolors='black', linewidth=1.5,
                            label=em.get('name', f'EM{i+1}'), zorder=10)

                # Draw 95% confidence ellipse

                # Calculate ellipse parameters
                eigenvalues, eigenvectors = np.linalg.eigh(cov)

                # Sort eigenvalues
                order = eigenvalues.argsort()[::-1]
                eigenvalues = eigenvalues[order]
                eigenvectors = eigenvectors[:, order]

                # Ellipse parameters
                angle = np.degrees(np.arctan2(eigenvectors[1, 0], eigenvectors[0, 0]))
                width = 2 * np.sqrt(chi2_val * eigenvalues[0])
                height = 2 * np.sqrt(chi2_val * eigenvalues[1])

                ellipse = Ellipse(xy=(em_x, em_y), width=width, height=height,
                                angle=angle, alpha=0.2, color=color,
                                label=f'95% CI {em.get("name", "")}')
                self.ax.add_patch(ellipse)

                # Store distances
                self.current_results[f'mahalanobis_em{i+1}'] = distances

                # Log some statistics
                self._log_result(f"   {em.get('name', f'EM{i+1}')}: "
                            f"Mean D={np.mean(distances):.2f}, "
                            f"Max D={np.max(distances):.2f}")

            self.ax.set_xlabel(self.available_isotopes[x_sys]['display'])
            self.ax.set_ylabel(self.available_isotopes[y_sys]['display'])
            self.ax.set_title('Mahalanobis Distance Provenance')
            self.ax.grid(True, alpha=0.3)
            self.ax.legend(loc='best', fontsize=8)

            self.canvas.draw()

            self._log_result(f"📐 Mahalanobis Distance Analysis")
            self._log_result(f"   Method: {'Global' if use_global else 'Per-end-member'} covariance")
            if use_global:
                self._log_result(f"   Data covariance matrix:")
                self._log_result(f"     [{cov[0,0]:.6f} {cov[0,1]:.6f}]")
                self._log_result(f"     [{cov[1,0]:.6f} {cov[1,1]:.6f}]")
            self._log_result(f"   χ²(95%, df=2) = {chi2_val:.2f}")

            self.status_indicator.config(text="● MAHALANOBIS COMPLETE", fg="#2ecc71")

        except Exception as e:
            messagebox.showerror("Mahalanobis Error", str(e))
            traceback.print_exc()

    # ============ NEW INVERSION METHODS ============

    def _least_squares_inversion(self):
        """
        Least-squares inversion to solve for source compositions
        Given a set of samples that are mixtures, find the best-fit end-members
        With per-isotope bounds for better accuracy
        """
        try:
            # Get selected isotopes (at least 2)
            selected = self.isotope_listbox.curselection()
            if len(selected) < 2:
                messagebox.showwarning("Select Isotopes", "Select at least 2 isotope systems for inversion!")
                return

            # Show progress
            self.progress_bar.start(10)
            self.stats_label.config(text="LS Inversion running...")

            # Get isotope data
            isotope_names = []
            data_matrix = []
            uncertainties = []

            for idx in selected:
                sys_name = list(self.available_isotopes.keys())[idx]
                col = self.available_isotopes[sys_name]['column']
                data = self.samples[col].values
                unc = self.available_isotopes[sys_name]['uncertainty']

                isotope_names.append(sys_name)
                data_matrix.append(data)
                uncertainties.append(unc)

            data_matrix = np.array(data_matrix).T  # samples x isotopes
            n_samples, n_isotopes = data_matrix.shape

            # Assume we want to find 2 end-members
            n_endmembers = 2

            # Set up optimization: find end-members that minimize residuals
            def objective(params):
                # params: flattened [em1_values, em2_values, mixing_proportions]
                em1 = params[:n_isotopes]
                em2 = params[n_isotopes:2*n_isotopes]
                props = params[2*n_isotopes:]

                # Reshape props for each sample
                props = props.reshape(n_samples, n_endmembers-1)

                # Calculate predicted values for each sample
                # For binary mixing: pred = (1-f)*em1 + f*em2
                residuals = 0
                for i in range(n_samples):
                    f = props[i, 0]
                    f = np.clip(f, 0, 1)  # Constrain to [0,1]
                    pred = (1-f)*em1 + f*em2

                    # Weighted residuals
                    weights = 1.0 / np.array(uncertainties)
                    diff = (data_matrix[i] - pred) * weights
                    residuals += np.sum(diff**2)

                return residuals

            # Initial guess
            x0 = np.zeros(n_isotopes * 2 + n_samples)

            # Initial end-members: min and max of data
            x0[:n_isotopes] = np.min(data_matrix, axis=0)
            x0[n_isotopes:2*n_isotopes] = np.max(data_matrix, axis=0)

            # Initial proportions: 0.5 for all samples
            x0[2*n_isotopes:] = 0.5

            # Calculate per-isotope min/max for better bounds
            isotope_mins = np.min(data_matrix, axis=0)
            isotope_maxs = np.max(data_matrix, axis=0)

            # Bounds with per-isotope scaling
            bounds_low = []
            bounds_high = []

            # End-member bounds - per isotope with individual scaling
            for i in range(n_isotopes):  # EM1
                bounds_low.append(isotope_mins[i] * 0.9)
                bounds_high.append(isotope_maxs[i] * 1.1)

            for i in range(n_isotopes):  # EM2
                bounds_low.append(isotope_mins[i] * 0.9)
                bounds_high.append(isotope_maxs[i] * 1.1)

            # Proportion bounds [0,1]
            for i in range(n_samples):
                bounds_low.append(0.0)
                bounds_high.append(1.0)

            # Run optimization
            self._log_result("🔍 Running least-squares inversion...")
            result = optimize.minimize(
                objective, x0, method='L-BFGS-B',
                bounds=list(zip(bounds_low, bounds_high)),
                options={'maxiter': 1000, 'disp': False}
            )

            self.progress_bar.stop()
            self.stats_label.config(text="Ready")

            # Extract results
            em1_inv = result.x[:n_isotopes]
            em2_inv = result.x[n_isotopes:2*n_isotopes]
            props_inv = result.x[2*n_isotopes:]
            props_inv = np.clip(props_inv, 0, 1)

            # Store results
            self.inversion_results = {
                'type': 'least_squares',
                'isotopes': isotope_names,
                'em1': em1_inv,
                'em2': em2_inv,
                'proportions': props_inv,
                'residual': result.fun,
                'success': result.success
            }

            # Update inversion tree
            self.inv_tree.delete(*self.inv_tree.get_children())

            self.inv_tree.insert('', tk.END, values=('Residual', f"{result.fun:.4f}", '-', '-', 'χ²'))
            self.inv_tree.insert('', tk.END, values=('Success', str(result.success), '-', '-', ''))
            self.inv_tree.insert('', tk.END, values=('', '', '', '', ''))

            # End-member 1
            self.inv_tree.insert('', tk.END, values=('END-MEMBER 1', '', '', '', ''))
            for i, (iso, val) in enumerate(zip(isotope_names, em1_inv)):
                self.inv_tree.insert('', tk.END, values=(iso, f"{val:.4f}", '-', '-', ''))

            self.inv_tree.insert('', tk.END, values=('', '', '', '', ''))

            # End-member 2
            self.inv_tree.insert('', tk.END, values=('END-MEMBER 2', '', '', '', ''))
            for i, (iso, val) in enumerate(zip(isotope_names, em2_inv)):
                self.inv_tree.insert('', tk.END, values=(iso, f"{val:.4f}", '-', '-', ''))

            # Plot results
            if n_isotopes >= 2:
                self.fig.clear()
                self.ax = self.fig.add_subplot(111)

                # Plot data
                self.ax.scatter(data_matrix[:, 0], data_matrix[:, 1],
                            c='#2c3e50', s=60, alpha=0.7,
                            edgecolors='white', linewidth=1, label='Samples')

                # Plot inverted end-members
                self.ax.scatter([em1_inv[0]], [em1_inv[1]], s=150, c='red', marker='s',
                            edgecolors='black', linewidth=1.5, label='Inverted EM1')
                self.ax.scatter([em2_inv[0]], [em2_inv[1]], s=150, c='blue', marker='s',
                            edgecolors='black', linewidth=1.5, label='Inverted EM2')

                # Draw mixing lines to each sample
                for i, (x, y) in enumerate(data_matrix):
                    f = props_inv[i]
                    pred_x = (1-f)*em1_inv[0] + f*em2_inv[0]
                    pred_y = (1-f)*em1_inv[1] + f*em2_inv[1]
                    self.ax.plot([x, pred_x], [y, pred_y], 'gray', linewidth=0.3, alpha=0.2)

                self.ax.set_xlabel(isotope_names[0])
                self.ax.set_ylabel(isotope_names[1])
                self.ax.set_title('Least-Squares Inversion Results')
                self.ax.grid(True, alpha=0.3)
                self.ax.legend(loc='best', fontsize=8)

                self.canvas.draw()

            # Log results
            self._log_result(f"\n🔍 LEAST-SQUARES INVERSION COMPLETE")
            self._log_result(f"   Final residual: {result.fun:.4f}")
            self._log_result(f"   Inverted EM1: {', '.join([f'{v:.4f}' for v in em1_inv])}")
            self._log_result(f"   Inverted EM2: {', '.join([f'{v:.4f}' for v in em2_inv])}")
            self._log_result(f"   Mean mixing proportion: {np.mean(props_inv)*100:.1f}%")

            # Log per-isotope bounds for verification
            self._log_result(f"   Per-isotope bounds used:")
            for i, iso in enumerate(isotope_names):
                self._log_result(f"     {iso}: [{isotope_mins[i]*0.9:.4f}, {isotope_maxs[i]*1.1:.4f}]")

            self.status_indicator.config(text="● LEAST-SQUARES INVERSION COMPLETE", fg="#2ecc71")
            self.notebook.select(2)  # Show inversion tab

        except Exception as e:
            messagebox.showerror("Inversion Error", str(e))
            traceback.print_exc()
            if hasattr(self, 'progress_bar'):
                self.progress_bar.stop()
            self.stats_label.config(text="Error")

    def _bayesian_mcmc_inversion(self):
        """
        Bayesian inversion using MCMC (emcee)
        Full posterior distribution of end-member compositions
        With robust initialization to avoid singular matrices
        """
        if not HAS_EMCEE:
            messagebox.showerror("Missing Dependency",
                            "emcee is required for Bayesian inversion.\n"
                            "Install with: pip install emcee")
            return

        try:
            # Get selected isotopes
            selected = self.isotope_listbox.curselection()
            if len(selected) < 2:
                messagebox.showwarning("Select Isotopes", "Select at least 2 isotope systems!")
                return

            # Get MCMC parameters
            n_walkers = int(self.mcmc_walkers.get())
            n_steps = int(self.mcmc_steps.get())
            n_burnin = int(self.mcmc_burnin.get())

            # Show progress window
            progress_window, cancel_var = self._show_progress(
                "MCMC Inversion",
                f"Initializing {n_walkers} walkers..."
            )

            # Get isotope data
            isotope_names = []
            data_matrix = []
            uncertainties = []

            for idx in selected:
                sys_name = list(self.available_isotopes.keys())[idx]
                col = self.available_isotopes[sys_name]['column']
                data = self.samples[col].values
                unc = self.available_isotopes[sys_name]['uncertainty']

                isotope_names.append(sys_name)
                data_matrix.append(data)
                uncertainties.append(unc)

            data_matrix = np.array(data_matrix).T
            n_samples, n_isotopes = data_matrix.shape

            # Calculate dimension of parameter space
            ndim = 2 * n_isotopes + n_samples

            self._log_result(f"\n📊 Running Bayesian MCMC inversion with {n_walkers} walkers...")
            self._log_result(f"   Parameter dimensions: {ndim}")
            self._log_result(f"   Samples: {n_samples}, Isotopes: {n_isotopes}")
            self.progress_bar.start(10)
            self.stats_label.config(text="MCMC: Initializing...")

            # Define log probability function with cancel check
            def log_probability(params):
                # Check if cancelled
                if cancel_var.get():
                    return -np.inf

                # params: [em1_values..., em2_values..., mixing_proportions...]
                em1 = params[:n_isotopes]
                em2 = params[n_isotopes:2*n_isotopes]
                props = params[2*n_isotopes:]

                # Priors
                # End-members should be within reasonable range
                data_min = np.min(data_matrix, axis=0)
                data_max = np.max(data_matrix, axis=0)
                data_range = data_max - data_min

                # Allow a bit of extrapolation but not too much
                if np.any(em1 < data_min - 0.5 * data_range) or \
                np.any(em1 > data_max + 0.5 * data_range):
                    return -np.inf
                if np.any(em2 < data_min - 0.5 * data_range) or \
                np.any(em2 > data_max + 0.5 * data_range):
                    return -np.inf

                # Proportions must be between 0 and 1
                if np.any(props < 0) or np.any(props > 1):
                    return -np.inf

                # Likelihood
                log_like = 0
                for i in range(n_samples):
                    f = props[i]
                    pred = (1-f)*em1 + f*em2

                    # Gaussian likelihood with uncertainties
                    for j in range(n_isotopes):
                        sigma = uncertainties[j]
                        diff = data_matrix[i, j] - pred[j]
                        log_like += -0.5 * (diff / sigma)**2

                return log_like

            # Get data statistics for initialization
            data_min = np.min(data_matrix, axis=0)
            data_max = np.max(data_matrix, axis=0)
            data_mean = np.mean(data_matrix, axis=0)
            data_std = np.std(data_matrix, axis=0)

            # Use a simpler initialization strategy
            # Instead of trying to create perfectly spaced walkers,
            # we'll create them with random perturbations around reasonable starting points

            # Starting points: use the 10th, 50th, and 90th percentiles
            p10 = np.percentile(data_matrix, 10, axis=0)
            p50 = np.percentile(data_matrix, 50, axis=0)
            p90 = np.percentile(data_matrix, 90, axis=0)

            # For proportions, start with a reasonable distribution
            props_init = np.random.uniform(0.3, 0.7, n_samples)

            # Create initial positions with large random spread
            pos = []

            # Scale for perturbations - use a fraction of the data range
            scale = (data_max - data_min) * 0.2

            for i in range(n_walkers):
                # Randomly choose which end-member combination to start from
                choice = np.random.randint(0, 3)

                if choice == 0:
                    # EM1 low, EM2 high
                    em1_base = p10
                    em2_base = p90
                elif choice == 1:
                    # Both around median but with offset
                    em1_base = p50 - scale * 0.5
                    em2_base = p50 + scale * 0.5
                else:
                    # EM1 moderate, EM2 very high
                    em1_base = p50
                    em2_base = p90 + scale * 0.3

                # Add random noise to each base
                em1 = em1_base + np.random.normal(0, scale * 0.1, n_isotopes)
                em2 = em2_base + np.random.normal(0, scale * 0.1, n_isotopes)

                # Ensure values are within reasonable bounds
                em1 = np.clip(em1, data_min - scale, data_max + scale)
                em2 = np.clip(em2, data_min - scale, data_max + scale)

                # Proportions with random variation
                props = props_init + np.random.normal(0, 0.15, n_samples)
                props = np.clip(props, 0.05, 0.95)

                pos.append(np.concatenate([em1, em2, props]))

            pos = np.array(pos)

            # Add significant jitter to ensure linear independence
            pos += np.random.normal(0, 1e-4, pos.shape)

            # Create sampler with a larger moves scale if needed
            # Use a stretch move which is more robust
            moves = emcee.moves.StretchMove(a=2.0)
            sampler = emcee.EnsembleSampler(n_walkers, ndim, log_probability, moves=moves)

            # Check if we need to reduce dimensionality
            if ndim > n_walkers:
                self._log_result(f"⚠️ WARNING: Number of parameters ({ndim}) exceeds number of walkers ({n_walkers})")
                self._log_result(f"   This can cause numerical issues. Consider increasing walkers or reducing parameters.")

                # Try a different move if possible
                if hasattr(emcee.moves, 'DEMove'):
                    moves = emcee.moves.DEMove()
                    sampler = emcee.EnsembleSampler(n_walkers, ndim, log_probability, moves=moves)

            # Burn-in phase - use run_mcmc directly instead of iterating for first attempt
            self._log_result(f"   Burn-in phase ({n_burnin} steps)...")
            self.stats_label.config(text=f"MCMC: Burn-in (0/{n_burnin})")

            try:
                # Run burn-in directly
                state = sampler.run_mcmc(pos, n_burnin, progress=False)
                pos = state.coords

                # Check if we had any successes
                if np.all(np.isnan(sampler.get_log_prob())):
                    raise ValueError("All walkers have invalid log probabilities")

            except Exception as e:
                self._log_result(f"   Initial burn-in failed: {str(e)[:100]}")
                self._log_result(f"   Trying alternative initialization...")

                # Alternative: use a much simpler approach with fewer parameters
                # Reduce the problem by fixing proportions for burn-in
                self._log_result(f"   Attempting burn-in with fixed proportions...")

                # For burn-in, we'll only vary the end-members
                ndim_reduced = 2 * n_isotopes
                pos_reduced = pos[:, :ndim_reduced]

                def log_probability_reduced(params_reduced):
                    # Fix proportions at initial values
                    em1 = params_reduced[:n_isotopes]
                    em2 = params_reduced[n_isotopes:]
                    props = props_init  # Use the initial proportions

                    # Check bounds
                    if np.any(em1 < data_min - 2*scale) or np.any(em1 > data_max + 2*scale):
                        return -np.inf
                    if np.any(em2 < data_min - 2*scale) or np.any(em2 > data_max + 2*scale):
                        return -np.inf

                    # Likelihood
                    log_like = 0
                    for i in range(n_samples):
                        f = props[i]
                        pred = (1-f)*em1 + f*em2
                        for j in range(n_isotopes):
                            sigma = uncertainties[j]
                            diff = data_matrix[i, j] - pred[j]
                            log_like += -0.5 * (diff / sigma)**2
                    return log_like

                # Create new sampler with reduced dimensions
                sampler_reduced = emcee.EnsembleSampler(n_walkers, ndim_reduced, log_probability_reduced)

                # Run burn-in on reduced space
                try:
                    state_reduced = sampler_reduced.run_mcmc(pos_reduced, n_burnin // 2, progress=False)
                    pos_reduced = state_reduced.coords

                    # Now expand back to full space by adding proportions
                    pos_full = []
                    for i in range(n_walkers):
                        pos_full.append(np.concatenate([pos_reduced[i], props_init]))
                    pos = np.array(pos_full)

                    # Add some noise to proportions
                    pos[:, ndim_reduced:] += np.random.normal(0, 0.05, (n_walkers, n_samples))
                    pos[:, ndim_reduced:] = np.clip(pos[:, ndim_reduced:], 0.05, 0.95)

                    # Create final sampler
                    sampler = emcee.EnsembleSampler(n_walkers, ndim, log_probability, moves=moves)

                    # Run a short burn-in with full parameters
                    self._log_result(f"   Final burn-in with full parameters...")
                    state = sampler.run_mcmc(pos, n_burnin // 2, progress=False)
                    pos = state.coords

                except Exception as e2:
                    self._log_result(f"   Reduced burn-in also failed: {str(e2)[:100]}")
                    self._log_result(f"   Using simple random initialization with very large spread")

                    # Last resort: huge random spread
                    pos = []
                    for i in range(n_walkers):
                        em1 = data_mean + np.random.normal(0, data_std * 3, n_isotopes)
                        em2 = data_mean + np.random.normal(0, data_std * 3, n_isotopes)
                        props = np.random.uniform(0.1, 0.9, n_samples)
                        pos.append(np.concatenate([em1, em2, props]))
                    pos = np.array(pos)

                    # Try one more time
                    sampler = emcee.EnsembleSampler(n_walkers, ndim, log_probability, moves=moves)
                    try:
                        state = sampler.run_mcmc(pos, n_burnin, progress=False)
                        pos = state.coords
                    except:
                        self._log_result(f"❌ Cannot find valid initialization. Try different data or parameters.")
                        progress_window.destroy()
                        self.progress_bar.stop()
                        messagebox.showerror("MCMC Error",
                                        "Cannot initialize MCMC. Try:\n"
                                        "1. Use fewer isotope systems\n"
                                        "2. Increase number of walkers\n"
                                        "3. Check if data has sufficient variation")
                        return

            sampler.reset()

            # Production run with progress
            self._log_result(f"   Production run ({n_steps} steps)...")
            self.stats_label.config(text=f"MCMC: Production (0/{n_steps})")

            for i, sample in enumerate(sampler.sample(pos, iterations=n_steps, progress=False)):
                # Check if cancelled
                if cancel_var.get():
                    progress_window.destroy()
                    self.progress_bar.stop()
                    self._log_result("❌ MCMC cancelled during production")
                    self.stats_label.config(text="Cancelled")
                    return

                # Update progress every 100 steps
                if (i + 1) % 100 == 0:
                    progress = (i + 1) / n_steps * 100
                    self.stats_label.config(text=f"MCMC: Production {progress:.1f}%")
                    self.window.update()

            # Close progress window
            progress_window.destroy()
            self.stats_label.config(text="Processing results...")

            # Extract samples
            samples = sampler.get_chain(flat=True, discard=0)

            # Check if we got valid samples
            if len(samples) == 0:
                self._log_result("❌ No valid samples generated")
                self.progress_bar.stop()
                return

            # Compute statistics
            em1_samples = samples[:, :n_isotopes]
            em2_samples = samples[:, n_isotopes:2*n_isotopes]
            props_samples = samples[:, 2*n_isotopes:]

            em1_median = np.median(em1_samples, axis=0)
            em1_low = np.percentile(em1_samples, 2.5, axis=0)
            em1_high = np.percentile(em1_samples, 97.5, axis=0)

            em2_median = np.median(em2_samples, axis=0)
            em2_low = np.percentile(em2_samples, 2.5, axis=0)
            em2_high = np.percentile(em2_samples, 97.5, axis=0)

            # Store results
            self.mcmc_results = {
                'sampler': sampler,
                'samples': samples,
                'isotopes': isotope_names,
                'em1': em1_median,
                'em1_ci': (em1_low, em1_high),
                'em2': em2_median,
                'em2_ci': (em2_low, em2_high),
                'n_isotopes': n_isotopes
            }

            # Update inversion tree
            self.inv_tree.delete(*self.inv_tree.get_children())

            # End-member 1
            self.inv_tree.insert('', tk.END, values=('END-MEMBER 1', 'Median', '2.5%', '97.5%', ''))
            for i, iso in enumerate(isotope_names):
                self.inv_tree.insert('', tk.END, values=(
                    iso,
                    f"{em1_median[i]:.4f}",
                    f"{em1_low[i]:.4f}",
                    f"{em1_high[i]:.4f}",
                    ''
                ))

            self.inv_tree.insert('', tk.END, values=('', '', '', '', ''))

            # End-member 2
            self.inv_tree.insert('', tk.END, values=('END-MEMBER 2', 'Median', '2.5%', '97.5%', ''))
            for i, iso in enumerate(isotope_names):
                self.inv_tree.insert('', tk.END, values=(
                    iso,
                    f"{em2_median[i]:.4f}",
                    f"{em2_low[i]:.4f}",
                    f"{em2_high[i]:.4f}",
                    ''
                ))

            # Plot trace and corner
            self.mcmc_trace_ax.clear()
            self.mcmc_corner_ax.clear()

            # Trace plot for first parameter
            trace = sampler.get_chain()
            self.mcmc_trace_ax.plot(trace[:, :, 0], alpha=0.5, linewidth=0.5)
            self.mcmc_trace_ax.set_xlabel('Step')
            self.mcmc_trace_ax.set_ylabel(f'{isotope_names[0]} (EM1)')
            self.mcmc_trace_ax.set_title('MCMC Trace')
            self.mcmc_trace_ax.grid(True, alpha=0.3)

            # Corner plot (simplified - 2D histogram)
            if n_isotopes >= 1:
                self.mcmc_corner_ax.hexbin(em1_samples[:, 0], em2_samples[:, 0],
                                        gridsize=50, cmap='viridis')
                self.mcmc_corner_ax.set_xlabel(f'EM1 {isotope_names[0]}')
                self.mcmc_corner_ax.set_ylabel(f'EM2 {isotope_names[0]}')
                self.mcmc_corner_ax.set_title('Posterior (EM1 vs EM2)')
                self.mcmc_corner_ax.grid(True, alpha=0.3)

            self.mcmc_canvas.draw()
            self.progress_bar.stop()

            # Log results
            self._log_result(f"\n📊 BAYESIAN MCMC INVERSION COMPLETE")
            self._log_result(f"   Walkers: {n_walkers}, Steps: {n_steps}, Burn-in: {n_burnin}")
            self._log_result(f"   Total samples: {samples.shape[0]:,}")
            self._log_result(f"   Acceptance fraction: {np.mean(sampler.acceptance_fraction):.2f}")

            try:
                tau = sampler.get_autocorr_time(tol=0)
                self._log_result(f"   Autocorrelation time: {tau}")
            except:
                self._log_result(f"   Autocorrelation time: Could not compute")

            self.status_indicator.config(text="● MCMC INVERSION COMPLETE", fg="#2ecc71")
            self.stats_label.config(text="Ready")
            self.notebook.select(4)  # Show MCMC diagnostics tab

        except Exception as e:
            messagebox.showerror("MCMC Error", str(e))
            traceback.print_exc()
            if hasattr(self, 'progress_bar'):
                self.progress_bar.stop()
            self.stats_label.config(text="Error")

    def _ree_pattern_inversion(self):
        """
        REE pattern inversion to estimate source mineralogy and melt fraction
        With sample selection option
        """
        try:
            # Check if REE data available
            if len(self.available_ree) < 5:
                messagebox.showwarning("Insufficient REE Data",
                                    "Need at least 5 REE elements for inversion!\n"
                                    "Expected columns: La, Ce, Nd, Sm, Eu, Gd, Dy, Er, Yb, Lu (ppm)")
                return

            # Get sample selection mode
            sample_mode = self.ree_sample_var.get()

            # Get REE data - ensure numeric conversion
            ree_elements = []
            ree_data = []

            for ree in self.REE_ELEMENTS:
                if ree in self.available_ree:
                    col = self.available_ree[ree]['column']
                    ree_elements.append(ree)
                    # Convert to float, handling any string values
                    try:
                        values = pd.to_numeric(self.samples[col].values, errors='coerce')
                        ree_data.append(values)
                    except:
                        messagebox.showerror("Error", f"Column {col} contains non-numeric data")
                        return

            ree_data = np.array(ree_data).T  # samples x REE
            n_samples = ree_data.shape[0]
            n_ree = len(ree_elements)

            # Check for NaN values
            if np.any(np.isnan(ree_data)):
                messagebox.showwarning("Warning",
                    "Some REE data contains missing values. Please check your data.")
                # Replace NaN with column mean
                for j in range(ree_data.shape[1]):
                    col_mean = np.nanmean(ree_data[:, j])
                    ree_data[:, j] = np.nan_to_num(ree_data[:, j], nan=col_mean)

            # Normalize to chondrite (McDonough & Sun, 1995)
            CHONDRITE = {
                'La': 0.237, 'Ce': 0.613, 'Pr': 0.0928, 'Nd': 0.457, 'Sm': 0.148,
                'Eu': 0.0563, 'Gd': 0.199, 'Tb': 0.0361, 'Dy': 0.246, 'Ho': 0.0546,
                'Er': 0.160, 'Tm': 0.0247, 'Yb': 0.161, 'Lu': 0.0246
            }

            ree_norm = np.zeros_like(ree_data)
            for i, ree in enumerate(ree_elements):
                if ree in CHONDRITE:
                    ree_norm[:, i] = ree_data[:, i] / CHONDRITE[ree]
                else:
                    # If not in chondrite list, use a default normalization
                    ree_norm[:, i] = ree_data[:, i] / np.nanmean(ree_data[:, i])

            # Get selected source minerals
            active_minerals = [m for m, var in self.source_minerals.items() if var.get()]
            if not active_minerals:
                messagebox.showwarning("Select Minerals", "Select at least one source mineral!")
                return

            # Build bulk partition coefficients for each REE
            def bulk_D(F, mineral_props):
                """Calculate bulk partition coefficients for given melt fraction F"""
                D_bulk = np.zeros(n_ree)
                for i, ree in enumerate(ree_elements):
                    D_sum = 0
                    for j, mineral in enumerate(active_minerals):
                        if ree in self.DEFAULT_KDS[mineral]:
                            D_sum += mineral_props[j] * self.DEFAULT_KDS[mineral][ree]
                    D_bulk[i] = D_sum
                return D_bulk

            # Select target REE pattern based on mode
            if sample_mode == "First":
                target_pattern = ree_norm[0]
                target_label = "Sample 1"
            elif sample_mode == "Average":
                target_pattern = np.mean(ree_norm, axis=0)
                target_label = "Average"
            else:  # "All" - we'll fit to all samples simultaneously
                target_pattern = ree_norm
                target_label = "All Samples"

            # Objective function for inversion
            def objective(params):
                # params: [F (melt fraction), mineral_props..., source_enrichment]
                F = params[0]
                n_minerals = len(active_minerals)
                mineral_props = params[1:1+n_minerals]
                source_enrich = params[-1]

                # Constraints
                if F <= 0 or F >= 1:
                    return 1e10
                if np.any(mineral_props < 0) or np.any(mineral_props > 1):
                    return 1e10
                if np.abs(np.sum(mineral_props) - 1) > 0.01:
                    return 1e10
                if source_enrich <= 0:
                    return 1e10

                # Calculate predicted REE pattern
                D = bulk_D(F, mineral_props)
                pred = source_enrich / (D + F*(1-D))

                # Calculate residual based on mode
                if sample_mode == "All":
                    # Sum residuals across all samples
                    residual = 0
                    for sample_idx in range(min(n_samples, 10)):  # Limit to first 10 for speed
                        diff = ree_norm[sample_idx] - pred
                        residual += np.sum(diff**2)
                else:
                    # Single pattern
                    diff = target_pattern - pred
                    residual = np.sum(diff**2)

                return residual

            # Initial guess
            n_minerals = len(active_minerals)
            x0 = [0.05] + [1.0/n_minerals] * n_minerals + [10.0]

            # Bounds
            bounds = [(0.001, 0.3)]
            for i in range(n_minerals):
                bounds.append((0, 1))
            bounds.append((1, 100))

            # Show progress
            self._log_result(f"\n📈 Running REE pattern inversion for {target_label}...")
            self.progress_bar.start(10)
            self.stats_label.config(text="REE Inversion...")

            # Run optimization
            result = optimize.minimize(
                objective, x0, method='L-BFGS-B',
                bounds=bounds,
                options={'maxiter': 1000}
            )

            self.progress_bar.stop()

            if not result.success:
                self._log_result(f"   ⚠️ Optimization did not fully converge: {result.message}")

            # Extract results
            F_opt = result.x[0]
            mineral_props_opt = result.x[1:1+n_minerals]
            source_enrich_opt = result.x[-1]

            # Normalize mineral proportions
            if np.sum(mineral_props_opt) > 0:
                mineral_props_opt = mineral_props_opt / np.sum(mineral_props_opt)

            # Store results
            self.ree_inversion_results = {
                'melt_fraction': F_opt,
                'minerals': active_minerals,
                'mineral_props': mineral_props_opt,
                'source_enrichment': source_enrich_opt,
                'residual': result.fun,
                'target': target_label
            }

            # Update inversion tree
            self.inv_tree.delete(*self.inv_tree.get_children())

            self.inv_tree.insert('', tk.END, values=('Target', target_label, '-', '-', ''))
            self.inv_tree.insert('', tk.END, values=('Melt Fraction (F)', f"{F_opt:.3f}", '-', '-', ''))
            self.inv_tree.insert('', tk.END, values=('Source Enrichment', f"{source_enrich_opt:.1f}", '-', '-', 'x chondrite'))
            self.inv_tree.insert('', tk.END, values=('Residual', f"{result.fun:.4f}", '-', '-', 'χ²'))
            self.inv_tree.insert('', tk.END, values=('', '', '', '', ''))

            self.inv_tree.insert('', tk.END, values=('MINERAL PROPORTIONS', '', '', '', ''))
            for mineral, prop in zip(active_minerals, mineral_props_opt):
                self.inv_tree.insert('', tk.END, values=(mineral, f"{prop*100:.1f}%", '-', '-', ''))

            # Plot REE patterns
            self.ree_ax.clear()

            # Plot sample REE patterns
            if sample_mode == "All":
                # Plot first 5 samples
                for i in range(min(n_samples, 5)):
                    self.ree_ax.plot(ree_elements, ree_norm[i], 'o-', alpha=0.3,
                                color='gray', linewidth=0.5, markersize=2)
                # Plot target average
                target_plot = np.mean(ree_norm[:min(n_samples, 10)], axis=0)
                self.ree_ax.plot(ree_elements, target_plot, 'o-', alpha=0.8,
                            color='blue', linewidth=2, markersize=6,
                            label=f'Average (n={min(n_samples, 10)})')
            else:
                # Plot all samples in background
                for i in range(min(n_samples, 10)):
                    if i == 0 and sample_mode == "First":
                        continue  # Skip first if we're plotting it separately
                    self.ree_ax.plot(ree_elements, ree_norm[i], 'o-', alpha=0.2,
                                color='gray', linewidth=0.5, markersize=2)
                # Plot selected sample
                self.ree_ax.plot(ree_elements, target_pattern, 'o-', alpha=0.8,
                            color='blue', linewidth=2, markersize=6,
                            label=f'Target: {target_label}')

            # Plot modeled pattern
            D_opt = bulk_D(F_opt, mineral_props_opt)
            pred_ree = source_enrich_opt / (D_opt + F_opt*(1-D_opt))
            self.ree_ax.plot(ree_elements, pred_ree, 'k--', linewidth=2,
                        label=f'Model (F={F_opt:.3f})', zorder=10)

            self.ree_ax.set_xlabel('REE Element')
            self.ree_ax.set_ylabel('REE / Chondrite')
            self.ree_ax.set_title(f'REE Pattern Inversion - {target_label}')
            self.ree_ax.set_yscale('log')
            self.ree_ax.grid(True, alpha=0.3, which='both')
            self.ree_ax.legend(loc='best', fontsize=7)

            # Add mineralogy text
            mineral_text = '\n'.join([f'{m}: {p*100:.1f}%' for m, p in zip(active_minerals, mineral_props_opt)])
            self.ree_ax.text(0.02, 0.98, f'Melt fraction: {F_opt:.3f}\n{mineral_text}',
                        transform=self.ree_ax.transAxes, verticalalignment='top', fontsize=7,
                        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

            self.ree_canvas.draw()

            # Log results
            self._log_result(f"\n📈 REE PATTERN INVERSION COMPLETE")
            self._log_result(f"   Target: {target_label}")
            self._log_result(f"   Melt fraction: {F_opt:.3f} ({F_opt*100:.1f}%)")
            self._log_result(f"   Source enrichment: {source_enrich_opt:.1f}x chondrite")
            self._log_result(f"   Mineralogy:")
            for mineral, prop in zip(active_minerals, mineral_props_opt):
                self._log_result(f"     {mineral}: {prop*100:.1f}%")
            self._log_result(f"   Final residual: {result.fun:.4f}")

            self.status_indicator.config(text="● REE INVERSION COMPLETE", fg="#2ecc71")
            self.stats_label.config(text="Ready")
            self.notebook.select(3)  # Show REE tab

        except Exception as e:
            messagebox.showerror("REE Inversion Error", str(e))
            traceback.print_exc()
            if hasattr(self, 'progress_bar'):
                self.progress_bar.stop()
            self.stats_label.config(text="Error")

    def _send_results_to_app(self):
        """Send mixing/inversion results back to main app as new columns"""
        if not self.current_results and not self.inversion_results and not self.ree_inversion_results:
            messagebox.showwarning("No Results", "Run a model first!")
            return

        try:
            updates = []

            # Mixing model results
            if self.current_results:
                if self.current_results['model'] == 'binary':
                    proportions = self.current_results['proportions']
                    mahal = self.current_results.get('mahalanobis', [0]*len(proportions))

                    for i, (prop, m_dist) in enumerate(zip(proportions, mahal)):
                        if i < len(self.app.samples):
                            update = {
                                'Sample_ID': self.app.samples[i].get('Sample_ID', f"Sample_{i+1}"),
                                'EM1_Proportion': f"{100*(1-prop):.1f}",
                                'EM2_Proportion': f"{100*prop:.1f}",
                                'Mahalanobis_Distance': f"{m_dist:.2f}",
                                'Mixing_Model': 'Binary'
                            }
                            updates.append(update)

                elif self.current_results['model'] in ['ternary', 'ternary_3d']:
                    proportions = self.current_results['proportions']
                    for i, w in enumerate(proportions):
                        if i < len(self.app.samples):
                            update = {
                                'Sample_ID': self.app.samples[i].get('Sample_ID', f"Sample_{i+1}"),
                                'EM1_Proportion': f"{100*w[0]:.1f}",
                                'EM2_Proportion': f"{100*w[1]:.1f}",
                                'EM3_Proportion': f"{100*w[2]:.1f}",
                                'Mixing_Model': 'Ternary'
                            }
                            updates.append(update)

            # Inversion results
            if self.inversion_results:
                if self.inversion_results['type'] == 'least_squares':
                    update = {
                        'Sample_ID': 'INVERSION_SUMMARY',
                        'Inversion_Type': 'Least Squares',
                        'Residual': f"{self.inversion_results['residual']:.4f}",
                        'EM1_Values': ', '.join([f"{v:.4f}" for v in self.inversion_results['em1']]),
                        'EM2_Values': ', '.join([f"{v:.4f}" for v in self.inversion_results['em2']])
                    }
                    updates.append(update)

            # REE inversion results
            if self.ree_inversion_results:
                mineral_str = ', '.join([f"{m}:{p*100:.1f}%"
                                       for m, p in zip(self.ree_inversion_results['minerals'],
                                                      self.ree_inversion_results['mineral_props'])])
                update = {
                    'Sample_ID': 'REE_INVERSION',
                    'Melt_Fraction': f"{self.ree_inversion_results['melt_fraction']:.3f}",
                    'Source_Enrichment': f"{self.ree_inversion_results['source_enrichment']:.1f}",
                    'Mineralogy': mineral_str,
                    'Residual': f"{self.ree_inversion_results['residual']:.4f}"
                }
                updates.append(update)

            # Send to main app
            if updates:
                self.app.import_data_from_plugin(updates)
                messagebox.showinfo("Success",
                                   f"✅ Added {len(updates)} records to main app\n"
                                   "Check new columns in the main table")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to send results: {str(e)}")

    def _log_result(self, message):
        """Add result to log"""
        if self.results_text:
            self.results_text.insert(tk.END, message + "\n")
            self.results_text.see(tk.END)

    def _export_results(self):
        """Export results to CSV"""
        if not self.current_results and not self.inversion_results and not self.ree_inversion_results:
            messagebox.showwarning("No Results", "Run a model first!")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile=f"results_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        )

        if not filename:
            return

        try:
            # Compile results based on what's available
            if self.ree_inversion_results:
                df = pd.DataFrame({
                    'Parameter': ['Melt Fraction', 'Source Enrichment', 'Residual'] +
                                [f'Mineral: {m}' for m in self.ree_inversion_results['minerals']],
                    'Value': [self.ree_inversion_results['melt_fraction'],
                             self.ree_inversion_results['source_enrichment'],
                             self.ree_inversion_results['residual']] +
                            [f"{p*100:.1f}%" for p in self.ree_inversion_results['mineral_props']]
                })
                df.to_csv(filename, index=False)

            elif self.inversion_results:
                if self.inversion_results['type'] == 'least_squares':
                    df = pd.DataFrame({
                        'Isotope': self.inversion_results['isotopes'],
                        'EM1': self.inversion_results['em1'],
                        'EM2': self.inversion_results['em2']
                    })
                    df.to_csv(filename, index=False)

            elif self.current_results:
                if self.current_results['model'] == 'binary':
                    df = pd.DataFrame({
                        'Sample_ID': [self.samples.iloc[i].get('Sample_ID', f"Sample_{i+1}")
                                    for i in range(len(self.current_results['proportions']))],
                        'EM1_Proportion': [100*(1-p) for p in self.current_results['proportions']],
                        'EM2_Proportion': [100*p for p in self.current_results['proportions']],
                        'Mahalanobis': self.current_results.get('mahalanobis', [0]*len(self.current_results['proportions']))
                    })
                    df.to_csv(filename, index=False)

            messagebox.showinfo("Export Complete", f"Results saved to:\n{filename}")

        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def _export_figure(self):
        """Export current figure"""
        # Determine which figure to export based on selected tab
        current_tab = self.notebook.index(self.notebook.select())

        if current_tab == 3:  # REE tab
            fig = self.ree_fig
        elif current_tab == 4:  # MCMC tab
            fig = self.mcmc_fig
        else:  # Main plot tab
            fig = self.fig

        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf"), ("PNG", "*.png"), ("SVG", "*.svg")],
            initialfile=f"figure_{datetime.now().strftime('%Y%m%d')}.pdf"
        )

        if not filename:
            return

        try:
            fig.savefig(filename, dpi=300, bbox_inches='tight')
            messagebox.showinfo("Export Complete", f"Figure saved to:\n{filename}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))


def setup_plugin(main_app):
    """Plugin setup function"""
    plugin = IsotopeMixingModelsPlugin(main_app)
    return plugin
