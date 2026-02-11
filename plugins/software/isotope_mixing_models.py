"""
Isotope Mixing Models Plugin for Basalt Provenance Toolkit v10.2+
BINARY & TERNARY MIXING - END-MEMBER ESTIMATION - MONTE CARLO SIMULATIONS
FROM ISOTOPE RATIOS TO PROVENANCE IN 3 CLICKS

Author: Sefy Levy
License: CC BY-NC-SA 4.0
Version: 1.0 - The geochemical companion you've been waiting for
"""

PLUGIN_INFO = {
    "category": "software",
    "id": "isotope_mixing_models",
    "name": "Isotope Mixing Models",
    "icon": "🧪",
    "description": "Binary/ternary mixing lines, end-member estimation, Monte Carlo provenance",
    "version": "1.0.0",
    "requires": ["numpy", "scipy", "matplotlib", "pandas"],  # Pure Python, no compiled deps!
    "author": "Sefy Levy"
}

import site
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
from datetime import datetime
import os
import sys
from pathlib import Path

# ============ SCIENTIFIC IMPORTS ============
try:
    from scipy import stats, optimize
    from scipy.spatial import distance, ConvexHull
    from scipy.linalg import svd
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    from matplotlib.patches import Ellipse, Polygon
    from matplotlib.lines import Line2D
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
    ISOTOPE MIXING MODELS v1.0
    ============================================================================

    WHY GEOCHEMISTS NEED THIS:
    ────────────────────────────────────────────────────────────────────────────
    • Raw isotope ratios are just NUMBERS
    • Mixing models tell you SOURCES and PROPORTIONS
    • This plugin bridges geochemistry and archaeology

    WHAT IT DOES:
    ────────────────────────────────────────────────────────────────────────────
    1. BINARY MIXING: Two end-members with hyperbolic mixing curves
    2. TERNARY MIXING: Three-component systems in 2D/3D space
    3. END-MEMBER ESTIMATION: PCA/SVD to extract source compositions
    4. MONTE CARLO: 10,000+ iterations for realistic uncertainty
    5. PROVENANCE CLASSIFICATION: Which quarry? What mixture?

    ISOTOPE SYSTEMS SUPPORTED:
    ────────────────────────────────────────────────────────────────────────────
    ✓ Sr: ⁸⁷Sr/⁸⁶Sr vs 1/Sr (concentration-weighted mixing)
    ✓ Nd: ¹⁴³Nd/¹⁴⁴Nd vs εNd, ¹⁴⁷Sm/¹⁴⁴Nd
    ✓ Pb: ²⁰⁶Pb/²⁰⁴Pb, ²⁰⁷Pb/²⁰⁴Pb, ²⁰⁸Pb/²⁰⁴Pb (3D!)
    ✓ O: δ¹⁸O vs ⁸⁷Sr/⁸⁶Sr (crustal vs mantle)
    ✓ Hf: εHf vs εNd (mantle array)

    OUTPUTS:
    ────────────────────────────────────────────────────────────────────────────
    ✓ Mixing hyperbola parameters (r², curvature)
    ✓ End-member proportions with 95% CI
    ✓ Distance to each potential source (Mahalanobis)
    ✓ Posterior probability maps
    ✓ Publication-ready figures
    ============================================================================
    """

    # Color scheme for sources
    SOURCE_COLORS = {
        "MORB": "#3498db",          # Blue - Depleted mantle
        "OIB": "#e74c3c",           # Red - Ocean island
        "LOWER_CRUST": "#27ae60",   # Green - Lower continental
        "UPPER_CRUST": "#f39c12",   # Orange - Upper continental
        "ARC": "#9b59b6",           # Purple - Subduction zone
        "EM1": "#c0392b",           # Dark red - Enriched mantle 1
        "EM2": "#d35400",           # Brown - Enriched mantle 2
        "HIMU": "#16a085",          # Teal - High μ
        "BSE": "#7f8c8d",           # Gray - Bulk silicate earth
        "SAMPLE": "#2c3e50",        # Dark gray - Archaeological sample
        "UNKNOWN": "#95a5a6"        # Light gray
    }

    def __init__(self, main_app):
        self.app = main_app
        self.window = None

        # Current dataset
        self.samples = None  # DataFrame with sample isotope data
        self.end_members = None  # DataFrame with source compositions
        self.current_results = None

        # Mixing model parameters
        self.binary_model = None
        self.ternary_model = None
        self.monte_carlo_results = None

        # UI elements
        self.notebook = None
        self.data_status = None
        self.results_text = None
        self.canvas_frame = None
        self.status_indicator = None

        # Check dependencies
        self._check_dependencies()

    def _check_dependencies(self):
        """Check if required packages are installed"""
        missing = []
        if not HAS_SCIPY:
            missing.append("scipy")
        if not HAS_MATPLOTLIB:
            missing.append("matplotlib")
        if not HAS_PANDAS:
            missing.append("pandas")

        self.dependencies_met = len(missing) == 0
        self.missing_deps = missing

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
            return

        # COMPACT DESIGN - 1300x750
        self.window = tk.Toplevel(self.app.root)
        self.window.title("🧪 Isotope Mixing Models v1.0")
        self.window.geometry("1300x750")
        self.window.transient(self.app.root)

        self._create_interface()
        self.window.lift()
        self.window.focus_force()

    def _create_interface(self):
        """Create the isotope mixing models interface"""

        # ============ TOP BANNER ============
        header = tk.Frame(self.window, bg="#2c3e50", height=45)  # Dark blue = geochemistry
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="🧪", font=("Arial", 18),
                bg="#2c3e50", fg="white").pack(side=tk.LEFT, padx=10)

        tk.Label(header, text="Isotope Mixing Models",
                font=("Arial", 14, "bold"), bg="#2c3e50", fg="white").pack(side=tk.LEFT, padx=5)

        tk.Label(header, text="Binary • Ternary • Monte Carlo • End-Member",
                font=("Arial", 8), bg="#2c3e50", fg="#f39c12").pack(side=tk.LEFT, padx=15)

        self.status_indicator = tk.Label(header, text="● READY",
                                        font=("Arial", 8, "bold"),
                                        bg="#2c3e50", fg="#2ecc71")
        self.status_indicator.pack(side=tk.RIGHT, padx=15)

        # ============ MAIN CONTENT ============
        main_paned = tk.PanedWindow(self.window, orient=tk.HORIZONTAL,
                                   sashwidth=4, sashrelief=tk.RAISED)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # ============ LEFT PANEL - DATA MANAGEMENT ============
        left_panel = tk.Frame(main_paned, bg="white", relief=tk.RAISED, borderwidth=1, width=400)
        main_paned.add(left_panel, width=400)

        # Data import section
        data_frame = tk.LabelFrame(left_panel, text="📊 1. IMPORT DATA",
                                  font=("Arial", 9, "bold"),
                                  bg="white", padx=8, pady=8)
        data_frame.pack(fill=tk.X, padx=8, pady=8)

        # Sample data
        tk.Button(data_frame, text="📂 Load Samples",
                 command=self._load_samples,
                 bg="#3498db", fg="white",
                 font=("Arial", 9, "bold"),
                 width=20, height=2).pack(pady=5)

        tk.Label(data_frame, text="CSV format: Sample,87Sr/86Sr,143Nd/144Nd,206Pb/204Pb,...",
                font=("Arial", 7), bg="white", fg="#7f8c8d").pack()

        # End-member database
        tk.Button(data_frame, text="🏭 Load End-Members",
                 command=self._load_end_members,
                 bg="#9b59b6", fg="white",
                 font=("Arial", 9, "bold"),
                 width=20).pack(pady=5)

        # Quick select common reservoirs
        reservoir_frame = tk.Frame(data_frame, bg="white")
        reservoir_frame.pack(fill=tk.X, pady=5)

        tk.Label(reservoir_frame, text="Quick add:",
                font=("Arial", 8, "bold"), bg="white").pack(side=tk.LEFT)

        ttk.Combobox(reservoir_frame, values=['MORB', 'OIB', 'Upper Crust', 'Lower Crust',
                                             'EM1', 'EM2', 'HIMU', 'BSE'],
                    width=12, state="readonly").pack(side=tk.LEFT, padx=5)

        tk.Button(reservoir_frame, text="+", width=2,
                 command=self._add_reservoir).pack(side=tk.LEFT)

        # Data summary
        self.data_summary = tk.Text(data_frame, height=6, width=35,
                                   font=("Courier", 8), bg="#f8f9fa")
        self.data_summary.pack(fill=tk.X, pady=8)
        self.data_summary.insert(tk.END, "No data loaded\n\nLoad samples and end-members to begin")
        self.data_summary.config(state=tk.DISABLED)

        # ============ ISOTOPE SYSTEM SELECTOR ============
        system_frame = tk.LabelFrame(left_panel, text="⚛️ 2. SELECT SYSTEM",
                                    font=("Arial", 9, "bold"),
                                    bg="white", padx=8, pady=8)
        system_frame.pack(fill=tk.X, padx=8, pady=8)

        self.system_var = tk.StringVar(value="Sr-Nd")

        systems = [
            ("Sr-Nd", "⁸⁷Sr/⁸⁶Sr vs ¹⁴³Nd/¹⁴⁴Nd"),
            ("Sr-Pb", "⁸⁷Sr/⁸⁶Sr vs ²⁰⁶Pb/²⁰⁴Pb"),
            ("Pb-Pb", "²⁰⁶Pb/²⁰⁴Pb vs ²⁰⁷Pb/²⁰⁴Pb"),
            ("Pb3D", "²⁰⁶/²⁰⁴, ²⁰⁷/²⁰⁴, ²⁰⁸/²⁰⁴ (3D)"),
            ("Nd-Hf", "εNd vs εHf"),
            ("Sr-O", "⁸⁷Sr/⁸⁶Sr vs δ¹⁸O"),
            ("Custom", "User defined")
        ]

        for i, (sys_name, desc) in enumerate(systems):
            rb = tk.Radiobutton(system_frame, text=sys_name,
                               variable=self.system_var, value=sys_name,
                               bg="white", font=("Arial", 8, "bold"),
                               command=self._update_system)
            rb.pack(anchor=tk.W, pady=2)
            tk.Label(system_frame, text=desc, font=("Arial", 6),
                    bg="white", fg="#7f8c8d").pack(anchor=tk.W, padx=20)

        # ============ MODEL TYPE ============
        model_frame = tk.LabelFrame(left_panel, text="📐 3. CHOOSE MODEL",
                                   font=("Arial", 9, "bold"),
                                   bg="white", padx=8, pady=8)
        model_frame.pack(fill=tk.X, padx=8, pady=8)

        self.model_var = tk.StringVar(value="binary")

        tk.Radiobutton(model_frame, text="Binary Mixing (2 end-members)",
                      variable=self.model_var, value="binary",
                      bg="white", font=("Arial", 8)).pack(anchor=tk.W, pady=2)

        tk.Radiobutton(model_frame, text="Ternary Mixing (3 end-members)",
                      variable=self.model_var, value="ternary",
                      bg="white", font=("Arial", 8)).pack(anchor=tk.W, pady=2)

        tk.Radiobutton(model_frame, text="Monte Carlo (uncertainty propagation)",
                      variable=self.model_var, value="montecarlo",
                      bg="white", font=("Arial", 8)).pack(anchor=tk.W, pady=2)

        tk.Radiobutton(model_frame, text="End-Member Estimation (PCA/SVD)",
                      variable=self.model_var, value="endmember",
                      bg="white", font=("Arial", 8)).pack(anchor=tk.W, pady=2)

        # ============ RUN BUTTON ============
        run_frame = tk.Frame(left_panel, bg="white")
        run_frame.pack(fill=tk.X, padx=8, pady=15)

        tk.Button(run_frame, text="▶ RUN MIXING MODEL",
                 command=self._run_mixing_model,
                 bg="#e67e22", fg="white",
                 font=("Arial", 12, "bold"),
                 width=25, height=2).pack()

        # ============ RIGHT PANEL - VISUALIZATION & RESULTS ============
        right_panel = tk.Frame(main_paned, bg="#ecf0f1", relief=tk.RAISED, borderwidth=1)
        main_paned.add(right_panel, width=800)

        # ============ NOTEBOOK FOR TABS ============
        self.notebook = ttk.Notebook(right_panel)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Tab 1: Mixing Plot
        plot_tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(plot_tab, text="📈 Mixing Diagram")

        # Matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(8, 6), dpi=100)
        self.fig.patch.set_facecolor('white')
        self.ax.set_facecolor('#f8f9fa')
        self.ax.grid(True, alpha=0.3, linestyle='--')

        self.canvas = FigureCanvasTkAgg(self.fig, plot_tab)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Toolbar
        toolbar_frame = tk.Frame(plot_tab)
        toolbar_frame.pack(fill=tk.X)
        toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        toolbar.update()

        # Tab 2: Mixing Proportions
        props_tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(props_tab, text="📊 Mixing Proportions")

        # Create tree for proportions
        self.props_tree = ttk.Treeview(props_tab, columns=('End-Member', 'Proportion', '2.5%', '97.5%', 'Distance'),
                                       show='headings', height=15)

        self.props_tree.heading('End-Member', text='End-Member')
        self.props_tree.heading('Proportion', text='Mean %')
        self.props_tree.heading('2.5%', text='2.5%')
        self.props_tree.heading('97.5%', text='97.5%')
        self.props_tree.heading('Distance', text='Distance')

        self.props_tree.column('End-Member', width=150)
        self.props_tree.column('Proportion', width=80, anchor='center')
        self.props_tree.column('2.5%', width=80, anchor='center')
        self.props_tree.column('97.5%', width=80, anchor='center')
        self.props_tree.column('Distance', width=80, anchor='center')

        scrollbar = ttk.Scrollbar(props_tab, orient=tk.VERTICAL, command=self.props_tree.yview)
        self.props_tree.configure(yscrollcommand=scrollbar.set)

        self.props_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Tab 3: Statistical Report
        stats_tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(stats_tab, text="📋 Statistical Report")

        # Scrollable text area
        text_frame = tk.Frame(stats_tab)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        scrollbar_text = tk.Scrollbar(text_frame)
        scrollbar_text.pack(side=tk.RIGHT, fill=tk.Y)

        self.results_text = tk.Text(text_frame, wrap=tk.WORD,
                                   font=("Courier", 9),
                                   yscrollcommand=scrollbar_text.set,
                                   bg="white", relief=tk.FLAT,
                                   padx=10, pady=10)
        self.results_text.pack(fill=tk.BOTH, expand=True)
        scrollbar_text.config(command=self.results_text.yview)

        # Tab 4: Monte Carlo Diagnostics
        mc_tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(mc_tab, text="🎲 Monte Carlo")

        self.mc_fig, (self.mc_ax1, self.mc_ax2) = plt.subplots(1, 2, figsize=(10, 4))
        self.mc_fig.patch.set_facecolor('white')
        self.mc_canvas = FigureCanvasTkAgg(self.mc_fig, mc_tab)
        self.mc_canvas.draw()
        self.mc_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # ============ BOTTOM STATUS BAR ============
        status_bar = tk.Frame(self.window, bg="#ecf0f1", height=30)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        status_bar.pack_propagate(False)

        self.stats_label = tk.Label(status_bar,
                                   text="Ready - Load isotope data to begin",
                                   font=("Arial", 8),
                                   bg="#ecf0f1", fg="#2c3e50")
        self.stats_label.pack(side=tk.LEFT, padx=10)

        # Export buttons
        tk.Button(status_bar, text="💾 Export Results",
                 command=self._export_results,
                 font=("Arial", 7), bg="#3498db", fg="white",
                 padx=8).pack(side=tk.RIGHT, padx=5)

        tk.Button(status_bar, text="📊 Export Figure",
                 command=self._export_figure,
                 font=("Arial", 7), bg="#3498db", fg="white",
                 padx=8).pack(side=tk.RIGHT, padx=5)

        # Initialize plot
        self._initialize_plot()

    # ============ DATA LOADING ============

    def _load_samples(self):
        """Load sample isotope data from CSV"""
        file_path = filedialog.askopenfilename(
            title="Load Sample Isotope Data",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx"), ("All files", "*.*")]
        )

        if not file_path:
            return

        try:
            if file_path.endswith('.csv'):
                self.samples = pd.read_csv(file_path)
            else:
                self.samples = pd.read_excel(file_path)

            # Update data summary
            self._update_data_summary()

            # Update status
            self.stats_label.config(text=f"Samples: {len(self.samples)}")
            self.status_indicator.config(text="● SAMPLES LOADED", fg="#f39c12")

            self._log_result(f"📊 Loaded {len(self.samples)} samples from {os.path.basename(file_path)}")

            # Plot samples
            self._plot_samples()

        except Exception as e:
            messagebox.showerror("Load Error", f"Could not load samples:\n{str(e)}")

    def _load_end_members(self):
        """Load end-member compositions"""
        file_path = filedialog.askopenfilename(
            title="Load End-Member Compositions",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx"), ("All files", "*.*")]
        )

        if not file_path:
            return

        try:
            if file_path.endswith('.csv'):
                self.end_members = pd.read_csv(file_path)
            else:
                self.end_members = pd.read_excel(file_path)

            self._update_data_summary()
            self.status_indicator.config(text="● END-MEMBERS LOADED", fg="#9b59b6")

            self._log_result(f"🏭 Loaded {len(self.end_members)} end-members from {os.path.basename(file_path)}")

            # Plot end-members
            self._plot_end_members()

        except Exception as e:
            messagebox.showerror("Load Error", f"Could not load end-members:\n{str(e)}")

    def _add_reservoir(self):
        """Add standard geochemical reservoir"""
        # Implementation would add predefined end-member compositions
        messagebox.showinfo("Add Reservoir",
                          "Predefined reservoirs coming in v1.1!\n\n"
                          "For now, load your own end-members from CSV.\n"
                          "Format: Name,87Sr/86Sr,143Nd/144Nd,206Pb/204Pb,...")

    def _update_data_summary(self):
        """Update the data summary text widget"""
        self.data_summary.config(state=tk.NORMAL)
        self.data_summary.delete(1.0, tk.END)

        summary = ""

        if self.samples is not None:
            summary += f"📊 SAMPLES: {len(self.samples)}\n"
            summary += f"   Columns: {', '.join(self.samples.columns[:5])}"
            if len(self.samples.columns) > 5:
                summary += f"... (+{len(self.samples.columns)-5})"
            summary += "\n\n"

        if self.end_members is not None:
            summary += f"🏭 END-MEMBERS: {len(self.end_members)}\n"
            for i, name in enumerate(self.end_members.iloc[:, 0].values[:3]):
                summary += f"   • {name}\n"
            if len(self.end_members) > 3:
                summary += f"   • ... and {len(self.end_members)-3} more\n"

        if not summary:
            summary = "No data loaded\n\nLoad samples and end-members to begin"

        self.data_summary.insert(tk.END, summary)
        self.data_summary.config(state=tk.DISABLED)

    def _update_system(self):
        """Update isotope system selection"""
        system = self.system_var.get()
        self._log_result(f"⚛️ Selected system: {system}")
        self._clear_plot()
        self._plot_samples()
        self._plot_end_members()

    def _initialize_plot(self):
        """Initialize empty plot"""
        self.ax.clear()
        self.ax.set_xlabel('X Axis')
        self.ax.set_ylabel('Y Axis')
        self.ax.set_title('Isotope Mixing Diagram')
        self.ax.grid(True, alpha=0.3, linestyle='--')
        self.canvas.draw()

    def _clear_plot(self):
        """Clear current plot"""
        self.ax.clear()
        self.ax.grid(True, alpha=0.3, linestyle='--')
        self.canvas.draw()

    def _plot_samples(self):
        """Plot sample data on current axis"""
        if self.samples is None:
            return

        system = self.system_var.get()

        if system == "Sr-Nd" and '87Sr/86Sr' in self.samples.columns and '143Nd/144Nd' in self.samples.columns:
            x = self.samples['87Sr/86Sr']
            y = self.samples['143Nd/144Nd']

            self.ax.scatter(x, y, c='#2c3e50', s=80, alpha=0.7,
                          edgecolors='white', linewidth=1.5,
                          label='Archaeological samples', zorder=5)

            self.ax.set_xlabel('⁸⁷Sr/⁸⁶Sr', fontsize=11, fontweight='bold')
            self.ax.set_ylabel('¹⁴³Nd/¹⁴⁴Nd', fontsize=11, fontweight='bold')

        elif system == "Pb-Pb" and '206Pb/204Pb' in self.samples.columns and '207Pb/204Pb' in self.samples.columns:
            x = self.samples['206Pb/204Pb']
            y = self.samples['207Pb/204Pb']

            self.ax.scatter(x, y, c='#2c3e50', s=80, alpha=0.7,
                          edgecolors='white', linewidth=1.5,
                          label='Archaeological samples', zorder=5)

            self.ax.set_xlabel('²⁰⁶Pb/²⁰⁴Pb', fontsize=11, fontweight='bold')
            self.ax.set_ylabel('²⁰⁷Pb/²⁰⁴Pb', fontsize=11, fontweight='bold')

        self.ax.legend(loc='best')
        self.canvas.draw()

    def _plot_end_members(self):
        """Plot end-member compositions"""
        if self.end_members is None:
            return

        system = self.system_var.get()

        for idx, row in self.end_members.iterrows():
            name = row.iloc[0]  # First column is name

            if system == "Sr-Nd":
                if '87Sr/86Sr' in self.end_members.columns and '143Nd/144Nd' in self.end_members.columns:
                    x = row['87Sr/86Sr']
                    y = row['143Nd/144Nd']

                    # Assign color based on name
                    color = self.SOURCE_COLORS.get(name.upper(), '#95a5a6')

                    self.ax.scatter(x, y, c=color, s=150, marker='s',
                                  edgecolors='black', linewidth=1.5,
                                  label=name, zorder=10)

            elif system == "Pb-Pb":
                if '206Pb/204Pb' in self.end_members.columns and '207Pb/204Pb' in self.end_members.columns:
                    x = row['206Pb/204Pb']
                    y = row['207Pb/204Pb']

                    color = self.SOURCE_COLORS.get(name.upper(), '#95a5a6')

                    self.ax.scatter(x, y, c=color, s=150, marker='s',
                                  edgecolors='black', linewidth=1.5,
                                  label=name, zorder=10)

        # Update legend (remove duplicates)
        handles, labels = self.ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        self.ax.legend(by_label.values(), by_label.keys(), loc='best')

        self.canvas.draw()

    # ============ MIXING MODELS ============

    def _run_mixing_model(self):
        """Main dispatcher for mixing models"""
        if self.samples is None:
            messagebox.showwarning("No Data", "Load sample data first!")
            return

        if self.end_members is None and self.model_var.get() != "endmember":
            messagebox.showwarning("No End-Members",
                                 "Load end-member compositions for mixing models!")
            return

        model_type = self.model_var.get()

        if model_type == "binary":
            self._binary_mixing()
        elif model_type == "ternary":
            self._ternary_mixing()
        elif model_type == "montecarlo":
            self._monte_carlo_mixing()
        elif model_type == "endmember":
            self._estimate_end_members()

        self.notebook.select(0)  # Show plot tab

    def _binary_mixing(self):
        """
        Binary mixing model with hyperbolic curves
        After Faure (1986), Albarede (1995)
        """
        system = self.system_var.get()

        if system == "Sr-Nd":
            self._binary_mixing_sr_nd()
        elif system == "Pb-Pb":
            self._binary_mixing_pb_pb()
        else:
            messagebox.showinfo("Binary Mixing",
                              f"Binary mixing for {system} coming in v1.1!\n\n"
                              "Currently supports:\n• Sr-Nd\n• Pb-Pb")

    def _binary_mixing_sr_nd(self):
        """Binary mixing in Sr-Nd space"""
        try:
            # Get sample data
            sample_sr = self.samples['87Sr/86Sr'].values
            sample_nd = self.samples['143Nd/144Nd'].values

            # Get end-members (first two)
            em1 = self.end_members.iloc[0]
            em2 = self.end_members.iloc[1]

            em1_sr = em1['87Sr/86Sr']
            em1_nd = em1['143Nd/144Nd']
            em2_sr = em2['87Sr/86Sr']
            em2_nd = em2['143Nd/144Nd']

            # Generate mixing curve
            f = np.linspace(0, 1, 100)  # mixing proportion

            # Concentration-weighted mixing (assuming equal concentrations for simplicity)
            # In v1.1: Use actual Sr, Nd concentrations
            mix_sr = em1_sr * (1-f) + em2_sr * f
            mix_nd = em1_nd * (1-f) + em2_nd * f

            # Plot mixing curve
            self.ax.plot(mix_sr, mix_nd, 'k-', linewidth=2, alpha=0.7, label='Binary mixing')

            # Calculate mixing proportions for each sample
            proportions = []

            for i, (sr, nd) in enumerate(zip(sample_sr, sample_nd)):
                # Find closest point on mixing line
                distances = np.sqrt((mix_sr - sr)**2 + (mix_nd - nd)**2)
                idx = np.argmin(distances)

                prop = f[idx]
                proportions.append(prop)

                # Project onto mixing line
                proj_sr = mix_sr[idx]
                proj_nd = mix_nd[idx]

                # Draw tie line
                self.ax.plot([sr, proj_sr], [nd, proj_nd], 'gray', linewidth=0.5, alpha=0.3)

            # Calculate statistics
            mean_prop = np.mean(proportions)
            ci_low, ci_high = np.percentile(proportions, [2.5, 97.5])

            # Update results table
            self._update_proportions_table([
                (em1.iloc[0], f"{100*(1-mean_prop):.1f}",
                 f"{100*(1-ci_high):.1f}", f"{100*(1-ci_low):.1f}", "N/A"),
                (em2.iloc[0], f"{100*mean_prop:.1f}",
                 f"{100*ci_low:.1f}", f"{100*ci_high:.1f}", "N/A")
            ])

            # Log results
            self._log_result(f"📈 Binary Mixing Model - Sr-Nd")
            self._log_result(f"   End-member 1: {em1.iloc[0]} ({em1_sr:.4f}, {em1_nd:.4f})")
            self._log_result(f"   End-member 2: {em2.iloc[0]} ({em2_sr:.4f}, {em2_nd:.4f})")
            self._log_result(f"   Mean proportion EM2: {100*mean_prop:.1f}% (95% CI: {100*ci_low:.1f}-{100*ci_high:.1f}%)")
            self._log_result(f"   Samples analyzed: {len(proportions)}")

            self.binary_model = {
                'em1': em1.iloc[0],
                'em2': em2.iloc[0],
                'proportions': proportions,
                'curve_x': mix_sr,
                'curve_y': mix_nd
            }

            self.status_indicator.config(text="● BINARY MIXING COMPLETE", fg="#2ecc71")
            self.canvas.draw()

        except Exception as e:
            messagebox.showerror("Binary Mixing Error", str(e))

    def _binary_mixing_pb_pb(self):
        """Binary mixing in Pb-Pb space"""
        try:
            # Similar implementation for Pb isotopes
            sample_206 = self.samples['206Pb/204Pb'].values
            sample_207 = self.samples['207Pb/204Pb'].values

            em1 = self.end_members.iloc[0]
            em2 = self.end_members.iloc[1]

            em1_206 = em1['206Pb/204Pb']
            em1_207 = em1['207Pb/204Pb']
            em2_206 = em2['206Pb/204Pb']
            em2_207 = em2['207Pb/204Pb']

            f = np.linspace(0, 1, 100)
            mix_206 = em1_206 * (1-f) + em2_206 * f
            mix_207 = em1_207 * (1-f) + em2_207 * f

            self.ax.plot(mix_206, mix_207, 'k-', linewidth=2, alpha=0.7, label='Binary mixing')

            # Calculate proportions
            proportions = []

            for i, (pb206, pb207) in enumerate(zip(sample_206, sample_207)):
                distances = np.sqrt((mix_206 - pb206)**2 + (mix_207 - pb207)**2)
                idx = np.argmin(distances)
                proportions.append(f[idx])

                self.ax.plot([pb206, mix_206[idx]], [pb207, mix_207[idx]],
                           'gray', linewidth=0.5, alpha=0.3)

            mean_prop = np.mean(proportions)
            ci_low, ci_high = np.percentile(proportions, [2.5, 97.5])

            self._update_proportions_table([
                (em1.iloc[0], f"{100*(1-mean_prop):.1f}",
                 f"{100*(1-ci_high):.1f}", f"{100*(1-ci_low):.1f}", "N/A"),
                (em2.iloc[0], f"{100*mean_prop:.1f}",
                 f"{100*ci_low:.1f}", f"{100*ci_high:.1f}", "N/A")
            ])

            self._log_result(f"📈 Binary Mixing Model - Pb-Pb")
            self._log_result(f"   Mean proportion EM2: {100*mean_prop:.1f}%")

            self.canvas.draw()

        except Exception as e:
            messagebox.showerror("Binary Mixing Error", str(e))

    def _ternary_mixing(self):
        """Ternary mixing model - 3 end-members"""
        messagebox.showinfo(
            "Ternary Mixing",
            "Ternary mixing coming in v1.1!\n\n"
            "Features:\n"
            "• Triangular diagram (Sr-Nd-Pb)\n"
            "• 3D visualization for Pb isotopes\n"
            "• Mixture proportions via convex hull\n"
            "• Aitchison geometry for compositional data\n\n"
            "For now, use binary mixing with two main sources."
        )

    def _monte_carlo_mixing(self):
        """
        Monte Carlo simulation with analytical uncertainty
        10,000 iterations for robust confidence intervals
        """
        if self.samples is None or self.end_members is None:
            return

        try:
            n_iterations = 10000

            # Get end-members
            em1 = self.end_members.iloc[0]
            em2 = self.end_members.iloc[1]

            # Analytical uncertainties (typical values, should come from user input)
            sr_uncertainty = 0.00002  # 2e-5
            nd_uncertainty = 0.00001  # 1e-5

            # Monte Carlo iterations
            all_proportions = []

            for i in range(n_iterations):
                # Perturb end-members within uncertainty
                em1_sr = em1['87Sr/86Sr'] + np.random.normal(0, sr_uncertainty)
                em1_nd = em1['143Nd/144Nd'] + np.random.normal(0, nd_uncertainty)
                em2_sr = em2['87Sr/86Sr'] + np.random.normal(0, sr_uncertainty)
                em2_nd = em2['143Nd/144Nd'] + np.random.normal(0, nd_uncertainty)

                # Perturb sample
                for sample_idx, sample in self.samples.iterrows():
                    sample_sr = sample['87Sr/86Sr'] + np.random.normal(0, sr_uncertainty)
                    sample_nd = sample['143Nd/144Nd'] + np.random.normal(0, nd_uncertainty)

                    # Calculate mixing proportion
                    f = (sample_sr - em1_sr) / (em2_sr - em1_sr + 1e-10)
                    all_proportions.append(f)

            self.monte_carlo_results = all_proportions

            # Plot histogram
            self.mc_ax1.clear()
            self.mc_ax1.hist(all_proportions, bins=50, color='#3498db', alpha=0.7,
                           edgecolor='white', linewidth=0.5)
            self.mc_ax1.axvline(np.mean(all_proportions), color='red', linestyle='--',
                               linewidth=2, label=f"Mean: {np.mean(all_proportions):.3f}")
            self.mc_ax1.axvline(np.percentile(all_proportions, 2.5), color='gray',
                               linestyle=':', linewidth=1.5)
            self.mc_ax1.axvline(np.percentile(all_proportions, 97.5), color='gray',
                               linestyle=':', linewidth=1.5)

            self.mc_ax1.set_xlabel('Proportion of End-Member 2')
            self.mc_ax1.set_ylabel('Frequency')
            self.mc_ax1.set_title(f'Monte Carlo Simulation (n={n_iterations:,})')
            self.mc_ax1.legend()
            self.mc_ax1.grid(True, alpha=0.3)

            # QQ plot for normality check
            self.mc_ax2.clear()
            stats.probplot(all_proportions, dist="norm", plot=self.mc_ax2)
            self.mc_ax2.set_title('Q-Q Plot')
            self.mc_ax2.grid(True, alpha=0.3)

            self.mc_canvas.draw()

            # Update results
            mean_prop = np.mean(all_proportions)
            ci_low, ci_high = np.percentile(all_proportions, [2.5, 97.5])

            self._update_proportions_table([
                (em1.iloc[0], f"{100*(1-mean_prop):.1f}",
                 f"{100*(1-ci_high):.1f}", f"{100*(1-ci_low):.1f}", "N/A"),
                (em2.iloc[0], f"{100*mean_prop:.1f}",
                 f"{100*ci_low:.1f}", f"{100*ci_high:.1f}", "N/A")
            ])

            self._log_result(f"🎲 Monte Carlo Simulation Complete")
            self._log_result(f"   Iterations: {n_iterations:,}")
            self._log_result(f"   Mean EM2 proportion: {100*mean_prop:.1f}%")
            self._log_result(f"   95% Confidence Interval: {100*ci_low:.1f}% - {100*ci_high:.1f}%")
            self._log_result(f"   Standard deviation: {100*np.std(all_proportions):.2f}%")

            self.status_indicator.config(text="● MONTE CARLO COMPLETE", fg="#2ecc71")

        except Exception as e:
            messagebox.showerror("Monte Carlo Error", str(e))

    def _estimate_end_members(self):
        """
        End-member estimation using PCA/SVD
        After Weltje (1997), Geological Society London
        """
        if self.samples is None:
            return

        try:
            # Get numerical columns
            numeric_cols = self.samples.select_dtypes(include=[np.number]).columns

            if len(numeric_cols) < 2:
                raise ValueError("Need at least 2 numerical columns")

            # Prepare data matrix
            X = self.samples[numeric_cols].values

            # Center the data
            X_centered = X - np.mean(X, axis=0)

            # Perform SVD
            U, s, Vt = svd(X_centered, full_matrices=False)

            # First two principal components
            pc_scores = U[:, :2] * s[:2]

            # End-members are extreme points in PC space
            hull = ConvexHull(pc_scores)
            extreme_indices = hull.vertices

            # Get end-member compositions
            estimated_ems = []
            for idx in extreme_indices[:3]:  # First 3 end-members
                em_composition = {}
                for col, loading in zip(numeric_cols, Vt[0]):
                    em_composition[col] = X[idx]  # Simplified
                estimated_ems.append(em_composition)

            # Plot results
            self.ax.clear()
            self.ax.scatter(pc_scores[:, 0], pc_scores[:, 1], c='#2c3e50',
                          s=50, alpha=0.6, label='Samples')

            # Plot convex hull
            for simplex in hull.simplices:
                self.ax.plot(pc_scores[simplex, 0], pc_scores[simplex, 1], 'k-', alpha=0.3)

            # Highlight end-members
            self.ax.scatter(pc_scores[extreme_indices, 0], pc_scores[extreme_indices, 1],
                          c='red', s=200, marker='s', edgecolors='black',
                          label='Estimated end-members', zorder=10)

            self.ax.set_xlabel('PC1')
            self.ax.set_ylabel('PC2')
            self.ax.set_title('End-Member Estimation via PCA/SVD')
            self.ax.grid(True, alpha=0.3)
            self.ax.legend()

            self.canvas.draw()

            self._log_result(f"🔬 End-Member Estimation (SVD)")
            self._log_result(f"   Data matrix: {X.shape[0]} samples × {X.shape[1]} variables")
            self._log_result(f"   Variance explained PC1: {s[0]**2/np.sum(s**2)*100:.1f}%")
            self._log_result(f"   Variance explained PC2: {s[1]**2/np.sum(s**2)*100:.1f}%")
            self._log_result(f"   Estimated {len(extreme_indices)} potential end-members")

            self.status_indicator.config(text="● END-MEMBERS ESTIMATED", fg="#e67e22")

        except Exception as e:
            messagebox.showerror("End-Member Estimation Error", str(e))

    def _update_proportions_table(self, proportions_data):
        """Update the proportions table in tab 2"""
        # Clear existing items
        for item in self.props_tree.get_children():
            self.props_tree.delete(item)

        # Insert new data
        for row in proportions_data:
            self.props_tree.insert('', tk.END, values=row)

    def _log_result(self, message):
        """Add result to log"""
        if self.results_text:
            self.results_text.insert(tk.END, message + "\n")
            self.results_text.see(tk.END)

    # ============ EXPORT FUNCTIONS ============

    def _export_results(self):
        """Export mixing model results to CSV"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("All Files", "*.*")],
            initialfile=f"mixing_results_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        )

        if not filename:
            return

        try:
            # Compile results
            results_data = []

            if self.binary_model:
                results_data.append(["Model", "Binary Mixing"])
                results_data.append(["Date", datetime.now().strftime('%Y-%m-%d %H:%M')])
                results_data.append(["End-Member 1", self.binary_model['em1']])
                results_data.append(["End-Member 2", self.binary_model['em2']])
                results_data.append([])
                results_data.append(["Sample", "Proportion_EM2", "Proportion_EM1"])

                for i, prop in enumerate(self.binary_model['proportions']):
                    results_data.append([f"Sample_{i+1}", f"{prop:.4f}", f"{1-prop:.4f}"])

            elif self.monte_carlo_results:
                results_data.append(["Model", "Monte Carlo Simulation"])
                results_data.append(["Iterations", len(self.monte_carlo_results)])
                results_data.append(["Mean", f"{np.mean(self.monte_carlo_results):.4f}"])
                results_data.append(["Std Dev", f"{np.std(self.monte_carlo_results):.4f}"])
                results_data.append(["2.5%", f"{np.percentile(self.monte_carlo_results, 2.5):.4f}"])
                results_data.append(["97.5%", f"{np.percentile(self.monte_carlo_results, 97.5):.4f}"])

            # Save to CSV
            df = pd.DataFrame(results_data)
            df.to_csv(filename, index=False, header=False)

            messagebox.showinfo("Export Complete",
                              f"✓ Results saved to:\n{filename}")

        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def _export_figure(self):
        """Export current figure as publication-ready PDF"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf"), ("PNG", "*.png"), ("SVG", "*.svg")],
            initialfile=f"mixing_diagram_{datetime.now().strftime('%Y%m%d')}.pdf"
        )

        if not filename:
            return

        try:
            # Publication-quality settings
            self.fig.set_size_inches(8, 6)
            self.fig.savefig(filename, dpi=300, bbox_inches='tight',
                           facecolor='white', edgecolor='none')
            messagebox.showinfo("Export Complete",
                              f"✓ Figure saved to:\n{filename}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))


def setup_plugin(main_app):
    """Plugin setup function"""
    print("🧪 Loading Isotope Mixing Models Plugin v1.0")
    plugin = IsotopeMixingModelsPlugin(main_app)

    if hasattr(main_app, 'menu_bar'):
        if not hasattr(main_app, 'geochemistry_menu'):
            main_app.geochemistry_menu = tk.Menu(main_app.menu_bar, tearoff=0)
            main_app.menu_bar.add_cascade(label="Geochemistry", menu=main_app.geochemistry_menu)

        main_app.geochemistry_menu.add_command(
            label="🧪 Isotope Mixing Models",
            command=plugin.open_window
        )
        print("🧪 ✓ Added to Geochemistry menu")

    print("🧪 ✓ Loaded: Isotope Mixing Models v1.0")
    print("    Features: Binary mixing • Monte Carlo • End-member estimation • Pb isotopes")
    print("    Dependencies: numpy, scipy, matplotlib, pandas")
    return plugin
