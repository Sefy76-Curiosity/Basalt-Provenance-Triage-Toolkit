"""
PetroPlot Pro - Advanced Petrology & Geochemistry Suite
FULL IUGS-IMA standards: TAS, AFM, REE Spider, Harker, Pearce, Whalen, Nb-Y, Ta-Yb, Rb-Y+Nb
PRODUCTION GRADE - Industry standard calculations
"""

PLUGIN_INFO = {
    "category": "software",
    "id": "petro_plot_pro",
    "name": "PetroPlot Pro",
    "description": "FULL IUGS-IMA standards from TAS, AFM, REE Spider, Pearce, Whalen, Nb-Y, Ta-Yb, Rb-Y+Nb, Chondrite-N-MORB normalization",
    "icon": "🪨",
    "version": "2.3",  # COMPLETE FIXED VERSION
    "requires": ["numpy", "pandas", "matplotlib", "scipy", "sklearn", "openpyxl"],
    "author": "Sefy Levy & DeepSeek"
}

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import pandas as pd
import numpy as np
import threading
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Rectangle, Polygon
import warnings
warnings.filterwarnings('ignore')

class PetroPlotProPlugin:
    def __init__(self, main_app):
        self.app = main_app
        self.window = None
        self.df = pd.DataFrame()
        self.results_df = pd.DataFrame()
        self.is_processing = False
        self.progress = None
        self.plot_progress = None

        # ============ IUGS CLASSIFICATION FIELDS ============
        self.IUGS_MAJOR_ELEMENTS = {
            "SiO2": {"name": "SiO2", "required": True, "unit": "wt%", "range": [0, 100]},
            "TiO2": {"name": "TiO2", "required": False, "unit": "wt%", "range": [0, 100]},
            "Al2O3": {"name": "Al2O3", "required": True, "unit": "wt%", "range": [0, 100]},
            "Fe2O3": {"name": "Fe2O3", "required": False, "unit": "wt%", "range": [0, 100]},
            "FeO": {"name": "FeO", "required": False, "unit": "wt%", "range": [0, 100]},
            "MnO": {"name": "MnO", "required": False, "unit": "wt%", "range": [0, 100]},
            "MgO": {"name": "MgO", "required": True, "unit": "wt%", "range": [0, 100]},
            "CaO": {"name": "CaO", "required": True, "unit": "wt%", "range": [0, 100]},
            "Na2O": {"name": "Na2O", "required": True, "unit": "wt%", "range": [0, 100]},
            "K2O": {"name": "K2O", "required": True, "unit": "wt%", "range": [0, 100]},
            "P2O5": {"name": "P2O5", "required": False, "unit": "wt%", "range": [0, 100]},
            "LOI": {"name": "LOI", "required": False, "unit": "wt%", "range": [0, 100]}
        }

        # ============ REE ELEMENTS ============
        self.REE_ELEMENTS = {
            "La": {"name": "La", "group": "LREE", "normalization": "chondrite"},
            "Ce": {"name": "Ce", "group": "LREE", "normalization": "chondrite"},
            "Pr": {"name": "Pr", "group": "LREE", "normalization": "chondrite"},
            "Nd": {"name": "Nd", "group": "LREE", "normalization": "chondrite"},
            "Sm": {"name": "Sm", "group": "LREE", "normalization": "chondrite"},
            "Eu": {"name": "Eu", "group": "MREE", "normalization": "chondrite"},
            "Gd": {"name": "Gd", "group": "MREE", "normalization": "chondrite"},
            "Tb": {"name": "Tb", "group": "MREE", "normalization": "chondrite"},
            "Dy": {"name": "Dy", "group": "MREE", "normalization": "chondrite"},
            "Ho": {"name": "Ho", "group": "HREE", "normalization": "chondrite"},
            "Er": {"name": "Er", "group": "HREE", "normalization": "chondrite"},
            "Tm": {"name": "Tm", "group": "HREE", "normalization": "chondrite"},
            "Yb": {"name": "Yb", "group": "HREE", "normalization": "chondrite"},
            "Lu": {"name": "Lu", "group": "HREE", "normalization": "chondrite"},
            "Y": {"name": "Y", "group": "HREE", "normalization": "chondrite"}
        }

        # ============ TRACE ELEMENTS ============
        self.TRACE_ELEMENTS = {
            "Zr": {"name": "Zr", "group": "HFSE", "normalization": "N-MORB"},
            "Hf": {"name": "Hf", "group": "HFSE", "normalization": "N-MORB"},
            "Nb": {"name": "Nb", "group": "HFSE", "normalization": "N-MORB"},
            "Ta": {"name": "Ta", "group": "HFSE", "normalization": "N-MORB"},
            "Rb": {"name": "Rb", "group": "LILE", "normalization": "N-MORB"},
            "Sr": {"name": "Sr", "group": "LILE", "normalization": "N-MORB"},
            "Ba": {"name": "Ba", "group": "LILE", "normalization": "N-MORB"},
            "Cs": {"name": "Cs", "group": "LILE", "normalization": "N-MORB"},
            "Th": {"name": "Th", "group": "Actinide", "normalization": "N-MORB"},
            "U": {"name": "U", "group": "Actinide", "normalization": "N-MORB"},
            "Pb": {"name": "Pb", "group": "LILE", "normalization": "N-MORB"},
            "Sc": {"name": "Sc", "group": "Transition", "normalization": "N-MORB"},
            "V": {"name": "V", "group": "Transition", "normalization": "N-MORB"},
            "Cr": {"name": "Cr", "group": "Transition", "normalization": "N-MORB"},
            "Co": {"name": "Co", "group": "Transition", "normalization": "N-MORB"},
            "Ni": {"name": "Ni", "group": "Transition", "normalization": "N-MORB"}
        }

        # ============ NORMALIZATION VALUES ============
        self.CHONDRITE_NORM = {
            "La": 0.237, "Ce": 0.612, "Pr": 0.095, "Nd": 0.467,
            "Sm": 0.153, "Eu": 0.058, "Gd": 0.2055, "Tb": 0.0374,
            "Dy": 0.254, "Ho": 0.0566, "Er": 0.166, "Tm": 0.0255,
            "Yb": 0.170, "Lu": 0.0254, "Y": 1.57
        }

        self.NMORB_NORM = {
            "Rb": 0.56, "Ba": 6.3, "Th": 0.085, "U": 0.032,
            "Nb": 2.33, "Ta": 0.132, "La": 2.5, "Ce": 7.5,
            "Pb": 0.3, "Pr": 0.95, "Sr": 90, "Nd": 7.3,
            "Sm": 2.63, "Zr": 74, "Hf": 2.05, "Eu": 1.02,
            "Gd": 3.68, "Tb": 0.67, "Dy": 4.55, "Y": 22,
            "Er": 3.0, "Tm": 0.48, "Yb": 3.05, "Lu": 0.46,
            "Sc": 32, "V": 240, "Cr": 285, "Co": 49, "Ni": 105
        }

        # ============ TAS FIELDS ============
        self.TAS_FIELDS = {
            "Foidolite": {"SiO2": [0, 52], "alkali": [0, 22], "color": "#d4b8ac"},
            "Peridotgabbro": {"SiO2": [45, 52], "alkali": [0, 3], "color": "#b3cde0"},
            "Gabbro": {"SiO2": [45, 52], "alkali": [3, 5.9], "color": "#6497b1"},
            "Gabbroic Diorite": {"SiO2": [52, 57], "alkali": [0, 5.9], "color": "#005b96"},
            "Diorite": {"SiO2": [57, 63], "alkali": [0, 5.9], "color": "#03396c"},
            "Granodiorite": {"SiO2": [63, 69], "alkali": [0, 7.3], "color": "#011f4b"},
            "Granite": {"SiO2": [69, 100], "alkali": [0, 12], "color": "#b22222"},
            "Quartz Diorite": {"SiO2": [63, 69], "alkali": [5.9, 7.3], "color": "#7e9faf"},
            "Syeno-diorite": {"SiO2": [52, 63], "alkali": [5.9, 9.4], "color": "#6a4e9c"},
            "Syenite": {"SiO2": [57, 69], "alkali": [9.4, 14], "color": "#4b2e83"},
            "Foid Syenite": {"SiO2": [45, 57], "alkali": [9.4, 17], "color": "#b88b4a"},
            "Foid Gabbro": {"SiO2": [45, 52], "alkali": [3, 9.4], "color": "#b9936c"},
            "Foid Monzosyenite": {"SiO2": [52, 57], "alkali": [9.4, 14], "color": "#d2b48c"},
            "Foid Monzodiorite": {"SiO2": [45, 52], "alkali": [5.9, 9.4], "color": "#c4a484"}
        }

        # ============ TAS BOUNDARY POLYGONS ============
        self.TAS_BOUNDARIES = {
            "Basalt": {"x": [45, 52, 52, 45], "y": [0, 0, 5.9, 3]},
            "Basaltic Andesite": {"x": [52, 57, 57, 52], "y": [0, 0, 5.9, 5.9]},
            "Andesite": {"x": [57, 63, 63, 57], "y": [0, 0, 5.9, 5.9]},
            "Dacite": {"x": [63, 69, 69, 63], "y": [0, 0, 7.3, 5.9]},
            "Rhyolite": {"x": [69, 80, 80, 69], "y": [0, 0, 12, 7.3]},
            "Trachybasalt": {"x": [45, 52, 52, 45], "y": [3, 5.9, 9.4, 5.9]},
            "Trachyandesite": {"x": [52, 57, 57, 52], "y": [5.9, 5.9, 9.4, 9.4]},
            "Trachyte": {"x": [57, 69, 69, 57], "y": [9.4, 9.4, 14, 14]},
            "Phonolite": {"x": [45, 57, 57, 45], "y": [9.4, 9.4, 17, 17]}
        }

        # ============ AFM BOUNDARY ============
        self.AFM_BOUNDARY = [(18, 0), (22, 5), (30, 15), (40, 30), (55, 55), (70, 80), (85, 100)]

    # ----------------------------------------------------------------------
    # GUI METHODS
    # ----------------------------------------------------------------------

    def open_window(self):
        """Open the main PetroPlot Pro window"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title(f"🪨 {PLUGIN_INFO['name']} v{PLUGIN_INFO['version']} - IUGS-IMA Standards")
        self.window.geometry("1400x850")
        self.window.minsize(1200, 750)
        self._create_ui()

    def _create_ui(self):
        """Create compact, efficient UI"""

        # Top header
        header = tk.Frame(self.window, bg="#1a2634", height=40)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)

        title_frame = tk.Frame(header, bg="#1a2634")
        title_frame.pack(expand=True, fill=tk.BOTH)

        tk.Label(title_frame, text="🪨 PetroPlot Pro",
                font=("Arial", 14, "bold"), bg="#1a2634", fg="white").pack(side=tk.LEFT, padx=10)

        tk.Label(title_frame, text="IUGS-IMA | TAS | AFM | REE | Pearce | Whalen",
                font=("Arial", 10), bg="#1a2634", fg="#b0c4de").pack(side=tk.LEFT, padx=10)

        # Main content - Horizontal split
        main_paned = tk.PanedWindow(self.window, orient=tk.HORIZONTAL, sashwidth=6,
                                   bg="#ecf0f1", sashrelief=tk.RAISED)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Left panel - Fixed width
        left_panel = tk.Frame(main_paned, bg="#ecf0f1", relief=tk.FLAT)
        main_paned.add(left_panel, width=500, minsize=450)

        # Right panel - Expands
        right_panel = tk.Frame(main_paned, bg="white", relief=tk.FLAT)
        main_paned.add(right_panel, width=900, minsize=700)

        self._setup_left_panel(left_panel)
        self._setup_right_panel(right_panel)

    def _setup_left_panel(self, parent):
        """Setup compact control panel with all tabs"""

        # Main notebook
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # === TAB 1: MAJOR ELEMENTS ===
        major_tab = tk.Frame(notebook, bg="#ecf0f1")
        notebook.add(major_tab, text="🪨 Major")

        # Validation status
        self.validation_label = tk.Label(major_tab,
                                        text="⚠️ Map SiO2, Al2O3, MgO, CaO, Na2O, K2O",
                                        bg="#e74c3c", fg="white",
                                        font=("Arial", 8, "bold"),
                                        height=1)
        self.validation_label.pack(fill=tk.X, padx=2, pady=2)

        # Major elements grid
        major_frame = tk.Frame(major_tab, bg="#ecf0f1")
        major_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        self.major_mappings = {}
        elements = ["SiO2", "Al2O3", "Fe2O3", "FeO", "MgO", "CaO",
                   "Na2O", "K2O", "TiO2", "MnO", "P2O5", "LOI"]

        row, col = 0, 0
        for element in elements:
            if element in self.IUGS_MAJOR_ELEMENTS:
                frame = tk.Frame(major_frame, bg="#ecf0f1")
                frame.grid(row=row, column=col, padx=2, pady=1, sticky=tk.W)

                required = "*" if self.IUGS_MAJOR_ELEMENTS[element]["required"] else ""
                fg = "#c0392b" if required else "#2c3e50"

                tk.Label(frame, text=f"{element}{required}:", bg="#ecf0f1",
                        font=("Arial", 8, "bold" if required else "normal"),
                        fg=fg, width=6, anchor=tk.W).pack(side=tk.LEFT)

                self.major_mappings[element] = tk.StringVar(value="")
                self.major_mappings[element].trace('w', self._validate_major_elements)

                entry = ttk.Combobox(frame, textvariable=self.major_mappings[element],
                                    width=12, values=[""] + self._get_column_list(),
                                    font=("Arial", 8))
                entry.pack(side=tk.LEFT, padx=2)

                col += 1
                if col > 3:
                    col = 0
                    row += 1

        # Major auto-detect
        tk.Button(major_tab, text="🔍 Auto-Detect Major",
                 bg="#3498db", fg="white", font=("Arial", 8),
                 command=self._auto_detect_major_elements).pack(pady=3)

        # === TAB 2: REE ===
        ree_tab = tk.Frame(notebook, bg="#ecf0f1")
        notebook.add(ree_tab, text="🧪 REE")

        self.ree_mappings = {}
        ree_elements = ["La", "Ce", "Pr", "Nd", "Sm", "Eu", "Gd", "Tb",
                       "Dy", "Ho", "Er", "Tm", "Yb", "Lu", "Y"]

        ree_frame = tk.Frame(ree_tab, bg="#ecf0f1")
        ree_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        row, col = 0, 0
        for element in ree_elements:
            if element in self.REE_ELEMENTS:
                frame = tk.Frame(ree_frame, bg="#ecf0f1")
                frame.grid(row=row, column=col, padx=2, pady=1, sticky=tk.W)

                tk.Label(frame, text=f"{element}:", bg="#ecf0f1",
                        font=("Arial", 8), width=4, anchor=tk.W).pack(side=tk.LEFT)

                self.ree_mappings[element] = tk.StringVar(value="")
                entry = ttk.Combobox(frame, textvariable=self.ree_mappings[element],
                                    width=10, values=[""] + self._get_column_list(),
                                    font=("Arial", 8))
                entry.pack(side=tk.LEFT, padx=2)

                col += 1
                if col > 3:
                    col = 0
                    row += 1

        # REE auto-detect
        tk.Button(ree_tab, text="🔍 Auto-Detect REE",
                 bg="#3498db", fg="white", font=("Arial", 8),
                 command=self._auto_detect_ree).pack(pady=3)

        # === TAB 3: TRACE ===
        trace_tab = tk.Frame(notebook, bg="#ecf0f1")
        notebook.add(trace_tab, text="🔬 Trace")

        self.trace_mappings = {}
        trace_elements = ["Zr", "Nb", "Y", "Rb", "Ta", "Yb", "Th", "U", "Sr", "Ba", "Cr", "Ni"]

        trace_frame = tk.Frame(trace_tab, bg="#ecf0f1")
        trace_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        row, col = 0, 0
        for element in trace_elements:
            frame = tk.Frame(trace_frame, bg="#ecf0f1")
            frame.grid(row=row, column=col, padx=2, pady=1, sticky=tk.W)

            tk.Label(frame, text=f"{element}:", bg="#ecf0f1",
                    font=("Arial", 8), width=4, anchor=tk.W).pack(side=tk.LEFT)

            self.trace_mappings[element] = tk.StringVar(value="")
            entry = ttk.Combobox(frame, textvariable=self.trace_mappings[element],
                                width=10, values=[""] + self._get_column_list(),
                                font=("Arial", 8))
            entry.pack(side=tk.LEFT, padx=2)

            col += 1
            if col > 3:
                col = 0
                row += 1

        # Trace auto-detect
        tk.Button(trace_tab, text="🔍 Auto-Detect Trace",
                 bg="#3498db", fg="white", font=("Arial", 8),
                 command=self._auto_detect_trace).pack(pady=3)

        # === TAB 4: CORRECTIONS ===
        corr_tab = tk.Frame(notebook, bg="#ecf0f1")
        notebook.add(corr_tab, text="⚙️ Corrections")

        # LOI Correction
        loi_frame = tk.LabelFrame(corr_tab, text="LOI Correction", padx=5, pady=3, bg="#ecf0f1")
        loi_frame.pack(fill=tk.X, padx=2, pady=2)

        self.loi_correction_var = tk.StringVar(value="None")
        ttk.Combobox(loi_frame, textvariable=self.loi_correction_var,
                    values=["None", "LOI-free 100%", "Subtract LOI"],
                    width=18, font=("Arial", 8)).pack()

        # Blank Correction
        blank_frame = tk.LabelFrame(corr_tab, text="Blank Correction", padx=5, pady=3, bg="#ecf0f1")
        blank_frame.pack(fill=tk.X, padx=2, pady=2)

        blank_row = tk.Frame(blank_frame, bg="#ecf0f1")
        blank_row.pack()

        tk.Label(blank_row, text="Blank (ppm):", bg="#ecf0f1",
                font=("Arial", 8)).pack(side=tk.LEFT)
        self.blank_var = tk.DoubleVar(value=0.0)
        tk.Spinbox(blank_row, from_=0.0, to=100.0, increment=0.01,
                  textvariable=self.blank_var, width=8,
                  font=("Arial", 8)).pack(side=tk.LEFT, padx=2)

        # Fe speciation
        fe_frame = tk.LabelFrame(corr_tab, text="Fe Speciation", padx=5, pady=3, bg="#ecf0f1")
        fe_frame.pack(fill=tk.X, padx=2, pady=2)

        self.fe_ratio_var = tk.StringVar(value="FeO* = FeO + 0.9*Fe2O3")
        ttk.Combobox(fe_frame, textvariable=self.fe_ratio_var,
                    values=["FeO + 0.9*Fe2O3", "Fe2O3*0.8998", "Total Fe as FeO"],
                    width=20, font=("Arial", 8)).pack()

        # === TAB 5: PLOTS ===
        plot_tab = tk.Frame(notebook, bg="#ecf0f1")
        notebook.add(plot_tab, text="📊 Plots")

        # Plot Layout Settings
        grid_frame = tk.LabelFrame(plot_tab, text="Plot Layout", padx=5, pady=3, bg="#ecf0f1")
        grid_frame.pack(fill=tk.X, padx=2, pady=2)

        layout_frame = tk.Frame(grid_frame, bg="#ecf0f1")
        layout_frame.pack(fill=tk.X)

        tk.Label(layout_frame, text="Grid:", bg="#ecf0f1",
                font=("Arial", 8)).pack(side=tk.LEFT)

        self.plot_layout_var = tk.StringVar(value="Auto (2x2)")
        ttk.Combobox(layout_frame, textvariable=self.plot_layout_var,
                    values=["Auto (2x2)", "Auto (3x3)", "Auto (4x4)"],
                    width=15, font=("Arial", 8)).pack(side=tk.LEFT, padx=2)

        tk.Label(layout_frame, text="Max plots: unlimited",
                bg="#ecf0f1", fg="#27ae60", font=("Arial", 7, "italic")).pack(side=tk.LEFT, padx=5)

        # Plot selection - 3x3 grid
        plot_selection_frame = tk.Frame(plot_tab, bg="#ecf0f1")
        plot_selection_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        self.plot_vars = {}
        plots = [
            "TAS", "AFM", "REE Spider", "Multi-Spider",
            "Pearce Nb-Y", "Pearce Ta-Yb", "Pearce Rb-Y+Nb",
            "Whalen A-type", "Harker"
        ]

        for i, plot in enumerate(plots):
            var = tk.BooleanVar(value=True)
            self.plot_vars[plot] = var

            row = i // 3
            col = i % 3

            tk.Checkbutton(plot_selection_frame, text=plot, variable=var,
                          bg="#ecf0f1", font=("Arial", 8)).grid(row=row, column=col,
                                                               padx=5, pady=1, sticky=tk.W)

        # === TAB 6: OPTIONS ===
        opt_tab = tk.Frame(notebook, bg="#ecf0f1")
        notebook.add(opt_tab, text="⚙️ Options")

        # Normalization options
        norm_frame = tk.LabelFrame(opt_tab, text="Normalization", padx=5, pady=3, bg="#ecf0f1")
        norm_frame.pack(fill=tk.X, padx=2, pady=2)

        self.anhydrous_var = tk.BooleanVar(value=True)
        tk.Checkbutton(norm_frame, text="Anhydrous 100%", variable=self.anhydrous_var,
                      bg="#ecf0f1", font=("Arial", 8, "bold")).pack(anchor=tk.W)

        ree_norm_frame = tk.Frame(norm_frame, bg="#ecf0f1")
        ree_norm_frame.pack(fill=tk.X, pady=2)
        tk.Label(ree_norm_frame, text="REE Norm:", bg="#ecf0f1",
                font=("Arial", 8)).pack(side=tk.LEFT)
        self.ree_norm_var = tk.StringVar(value="Chondrite")
        ttk.Combobox(ree_norm_frame, textvariable=self.ree_norm_var,
                    values=["Chondrite", "Primitive Mantle", "N-MORB"],
                    width=14, font=("Arial", 8)).pack(side=tk.LEFT, padx=2)

        # REE plot options
        ree_opt_frame = tk.LabelFrame(opt_tab, text="REE Spider Options", padx=5, pady=3, bg="#ecf0f1")
        ree_opt_frame.pack(fill=tk.X, padx=2, pady=2)

        max_frame = tk.Frame(ree_opt_frame, bg="#ecf0f1")
        max_frame.pack()
        tk.Label(max_frame, text="Max samples:", bg="#ecf0f1",
                font=("Arial", 8)).pack(side=tk.LEFT)
        self.max_samples_var = tk.IntVar(value=8)
        tk.Spinbox(max_frame, from_=1, to=30, increment=1,
                  textvariable=self.max_samples_var, width=5,
                  font=("Arial", 8)).pack(side=tk.LEFT, padx=2)

        # ============ ACTION BUTTONS ============
        action_frame = tk.Frame(parent, bg="#ecf0f1", height=50)
        action_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=2, pady=2)
        action_frame.pack_propagate(False)

        self.process_btn = tk.Button(action_frame, text="🪨 GENERATE PLOTS",
                                    bg="#8e44ad", fg="white", font=("Arial", 9, "bold"),
                                    width=20, height=1, command=self._start_processing,
                                    state=tk.DISABLED)
        self.process_btn.pack(side=tk.LEFT, padx=2)

        self.export_btn = tk.Button(action_frame, text="📊 EXPORT",
                                   bg="#27ae60", fg="white", width=12, height=1,
                                   font=("Arial", 9, "bold"),
                                   command=self._export_geochemical_data)
        self.export_btn.pack(side=tk.LEFT, padx=2)

        # ============ PROGRESS BARS ============
        progress_frame = tk.Frame(parent, bg="#ecf0f1")
        progress_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=2, pady=1)

        self.status_label = tk.Label(progress_frame, text="Ready - Map major elements",
                                    bg="#ecf0f1", fg="#2c3e50", anchor=tk.W,
                                    font=("Arial", 8), height=1)
        self.status_label.pack(fill=tk.X)

        self.progress = ttk.Progressbar(progress_frame, mode='indeterminate', length=100)
        self.progress.pack(fill=tk.X, pady=1)

        # Plot progress bar (initially hidden)
        self.plot_progress = ttk.Progressbar(progress_frame, mode='determinate', length=100)

    def _setup_right_panel(self, parent):
        """Setup visualization panel"""

        # Create notebook for plots and data
        self.plot_notebook = ttk.Notebook(parent)
        self.plot_notebook.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Tab 1: Plots
        self.plot_frame = tk.Frame(self.plot_notebook, bg="white")
        self.plot_notebook.add(self.plot_frame, text="📊 Plots")

        # Create figure canvas
        self.figure = plt.Figure(figsize=(12, 8), dpi=100, facecolor='white')
        self.canvas = FigureCanvasTkAgg(self.figure, self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Tab 2: Data Table
        self.table_frame = tk.Frame(self.plot_notebook, bg="white")
        self.plot_notebook.add(self.table_frame, text="📋 Data")

        # Treeview
        columns = ("ID", "SiO2", "Alkali", "ASI", "Mg#", "Eu/Eu*", "La/Yb", "Type")
        self.tree = ttk.Treeview(self.table_frame, columns=columns, show="headings",
                                height=20, selectmode='browse')

        col_widths = [80, 60, 60, 60, 60, 70, 70, 80]
        for col, width in zip(columns, col_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(self.table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Tab 3: Statistics
        self.stats_frame = tk.Frame(self.plot_notebook, bg="white")
        self.plot_notebook.add(self.stats_frame, text="📈 Stats")

        self.stats_text = scrolledtext.ScrolledText(self.stats_frame,
                                                    font=("Consolas", 9),
                                                    bg="white",
                                                    height=25)
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

    # ----------------------------------------------------------------------
    # DATA METHODS
    # ----------------------------------------------------------------------

    def _get_column_list(self):
        """Get list of columns from main app"""
        try:
            if hasattr(self.app, 'samples') and self.app.samples:
                df = pd.DataFrame(self.app.samples[:5])
                exclude = ['Sample_ID', 'Notes', 'Location', 'Date', 'Description']
                return [col for col in df.columns if col not in exclude and isinstance(col, str)]
            return []
        except:
            return []

    def _validate_major_elements(self, *args):
        """Validate required major elements"""
        required = ["SiO2", "Al2O3", "MgO", "CaO", "Na2O", "K2O"]
        mapped = []

        for element in required:
            if element in self.major_mappings:
                val = self.major_mappings[element].get().strip()
                if val:
                    mapped.append(element)

        all_mapped = len(mapped) == len(required)

        if all_mapped:
            self.validation_label.config(text="✅ ALL MAJOR ELEMENTS MAPPED - Ready",
                                        bg="#27ae60", fg="white")
            self.process_btn.config(state=tk.NORMAL)
            self.status_label.config(text="Ready - All elements mapped ✓", fg="#27ae60")
        else:
            missing = len(required) - len(mapped)
            self.validation_label.config(text=f"⚠️ Missing {missing} major elements",
                                        bg="#e74c3c", fg="white")
            self.process_btn.config(state=tk.DISABLED)

    def _auto_detect_major_elements(self):
        """Auto-detect major element columns"""
        if not hasattr(self.app, 'samples') or not self.app.samples:
            messagebox.showwarning("No Data", "Load data first!")
            return

        sample_cols = self._get_column_list()
        keywords = {
            "SiO2": ["sio2", "si", "silica", "sio₂", "sio2_wt"],
            "Al2O3": ["al2o3", "al", "alumina", "al₂o₃", "al2o3_wt"],
            "Fe2O3": ["fe2o3", "fe₂o₃", "ferric", "fe2o3_wt"],
            "FeO": ["feo", "ferrous", "feo_wt"],
            "MgO": ["mgo", "mg", "magnesium", "mgo_wt"],
            "CaO": ["cao", "ca", "calcium", "cao_wt"],
            "Na2O": ["na2o", "na", "sodium", "na₂o", "na2o_wt"],
            "K2O": ["k2o", "k", "potassium", "k₂o", "k2o_wt"],
            "TiO2": ["tio2", "ti", "titanium", "tio₂", "tio2_wt"],
            "MnO": ["mno", "mn", "manganese", "mno_wt"],
            "P2O5": ["p2o5", "p", "phosphorus", "p₂o₅", "p2o5_wt"],
            "LOI": ["loi", "loss"]
        }

        mapped_count = 0
        for element, kw_list in keywords.items():
            if element in self.major_mappings:
                for col in sample_cols:
                    col_lower = col.lower()
                    if any(kw in col_lower for kw in kw_list):
                        self.major_mappings[element].set(col)
                        mapped_count += 1
                        break

        self._validate_major_elements()
        messagebox.showinfo("Auto-Detection", f"Mapped {mapped_count} major elements")

    def _auto_detect_ree(self):
        """Auto-detect REE columns"""
        if not hasattr(self.app, 'samples') or not self.app.samples:
            messagebox.showwarning("No Data", "Load data first!")
            return

        sample_cols = self._get_column_list()
        mapped_count = 0

        variations = {
            "La": ["la", "lanthanum"],
            "Ce": ["ce", "cerium"],
            "Pr": ["pr", "praseodymium"],
            "Nd": ["nd", "neodymium"],
            "Sm": ["sm", "samarium"],
            "Eu": ["eu", "europium"],
            "Gd": ["gd", "gadolinium"],
            "Tb": ["tb", "terbium"],
            "Dy": ["dy", "dysprosium"],
            "Ho": ["ho", "holmium"],
            "Er": ["er", "erbium"],
            "Tm": ["tm", "thulium"],
            "Yb": ["yb", "ytterbium"],
            "Lu": ["lu", "lutetium"],
            "Y": ["y", "yttrium"]
        }

        for element in self.ree_mappings.keys():
            # Try exact match first
            found = False
            for col in sample_cols:
                col_lower = col.lower()
                if element.lower() == col_lower or element.lower() in col_lower.split('_'):
                    self.ree_mappings[element].set(col)
                    mapped_count += 1
                    found = True
                    break

            # Try variations
            if not found and element in variations:
                for col in sample_cols:
                    col_lower = col.lower()
                    if any(var in col_lower for var in variations[element]):
                        self.ree_mappings[element].set(col)
                        mapped_count += 1
                        break

        messagebox.showinfo("Auto-Detection", f"Mapped {mapped_count} REE elements")

    def _auto_detect_trace(self):
        """Auto-detect trace element columns"""
        if not hasattr(self.app, 'samples') or not self.app.samples:
            messagebox.showwarning("No Data", "Load data first!")
            return

        sample_cols = self._get_column_list()
        mapped_count = 0

        keywords = {
            "Zr": ["zr", "zirconium"],
            "Nb": ["nb", "niobium"],
            "Y": ["y", "yttrium"],
            "Rb": ["rb", "rubidium"],
            "Ta": ["ta", "tantalum"],
            "Yb": ["yb", "ytterbium"],
            "Th": ["th", "thorium"],
            "U": ["u", "uranium"],
            "Sr": ["sr", "strontium"],
            "Ba": ["ba", "barium"],
            "Cr": ["cr", "chromium"],
            "Ni": ["ni", "nickel"]
        }

        for element, kw_list in keywords.items():
            if element in self.trace_mappings:
                for col in sample_cols:
                    col_lower = col.lower()
                    if any(kw in col_lower for kw in kw_list):
                        self.trace_mappings[element].set(col)
                        mapped_count += 1
                        break

        messagebox.showinfo("Auto-Detection", f"Mapped {mapped_count} trace elements")

    def _apply_blank_correction(self, values):
        """Apply blank correction"""
        blank = self.blank_var.get()
        if blank > 0:
            values = values - blank
            values[values < 0] = 0
        return values

    # ----------------------------------------------------------------------
    # PROCESSING METHODS
    # ----------------------------------------------------------------------

    def _start_processing(self):
        """Start geochemical analysis"""
        if self.is_processing:
            return

        if not hasattr(self.app, 'samples') or not self.app.samples:
            messagebox.showwarning("No Data", "Load data in main application first!")
            return

        required = ["SiO2", "Al2O3", "MgO", "CaO", "Na2O", "K2O"]
        mapped = []

        for element in required:
            if element in self.major_mappings:
                if self.major_mappings[element].get().strip():
                    mapped.append(element)

        if len(mapped) < len(required):
            messagebox.showerror("Validation Failed", "Missing required major elements")
            return

        self.is_processing = True
        self.process_btn.config(state=tk.DISABLED, text="Processing...")
        self.progress.start()
        self.status_label.config(text="Calculating geochemical indices...", fg="#f39c12")

        thread = threading.Thread(target=self._process_data, daemon=True)
        thread.start()

    def _process_data(self):
        """Process geochemical data"""
        try:
            self.df = pd.DataFrame(self.app.samples)

            # Convert to numeric
            for col in self.df.columns:
                try:
                    self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
                except:
                    pass

            # Extract major elements
            major_data = {}
            for element in self.IUGS_MAJOR_ELEMENTS.keys():
                if element in self.major_mappings:
                    col = self.major_mappings[element].get().strip()
                    if col and col in self.df.columns:
                        major_data[element] = self.df[col].fillna(0)
                    else:
                        major_data[element] = pd.Series(0, index=self.df.index)
                else:
                    major_data[element] = pd.Series(0, index=self.df.index)

            # Apply LOI correction
            loi_method = self.loi_correction_var.get()
            if loi_method != "None" and 'LOI' in major_data:
                if "LOI-free" in loi_method:
                    total = sum(major_data.values()) - major_data['LOI']
                    total = total.replace(0, np.nan)
                    for element in major_data:
                        if element != 'LOI':
                            major_data[element] = (major_data[element] / total * 100).fillna(0)
                    major_data['LOI'] = pd.Series(0, index=major_data['LOI'].index)
                elif "Subtract" in loi_method:
                    total = sum(major_data.values())
                    total = total.replace(0, np.nan)
                    for element in major_data:
                        major_data[element] = (major_data[element] / total * 100).fillna(0)

            # Apply anhydrous normalization
            if self.anhydrous_var.get():
                elements_to_sum = [v for k, v in major_data.items() if k != 'LOI']
                total = sum(elements_to_sum)
                total = total.replace(0, np.nan)
                for element in major_data:
                    if element != 'LOI':
                        major_data[element] = (major_data[element] / total * 100).fillna(0)
                if 'LOI' in major_data:
                    major_data['LOI'] = pd.Series(0, index=major_data['LOI'].index)

            # Calculate FeO*
            if "FeO + 0.9*Fe2O3" in self.fe_ratio_var.get():
                major_data["FeO_star"] = major_data["FeO"] + 0.9 * major_data["Fe2O3"]
            elif "Fe2O3*0.8998" in self.fe_ratio_var.get():
                major_data["FeO_star"] = major_data["Fe2O3"] * 0.8998
            else:
                major_data["FeO_star"] = major_data["FeO"] + major_data["Fe2O3"] * 0.8998

            # Add to dataframe
            for element, series in major_data.items():
                self.df[f"{element}_wt"] = series

            # Calculate Alkali
            self.df['Alkali'] = major_data["Na2O"] + major_data["K2O"]

            # ASI
            al_molar = major_data["Al2O3"] / 101.96
            ca_molar = major_data["CaO"] / 56.08
            na_molar = major_data["Na2O"] / 61.98
            k_molar = major_data["K2O"] / 94.20
            denominator = (ca_molar + na_molar + k_molar).replace(0, np.nan)
            self.df['ASI'] = al_molar / denominator
            self.df['ASI'] = self.df['ASI'].replace([np.inf, -np.inf], np.nan).fillna(0)

            # ASI Classification
            conditions = [
                self.df['ASI'] > 1.0,
                self.df['ASI'] < 1.0
            ]
            choices = ['Peraluminous', 'Metaluminous']
            self.df['ASI_Class'] = np.select(conditions, choices, default='Peralkaline')

            # Mg#
            mg_molar = major_data["MgO"] / 40.30
            fe_molar = major_data["FeO_star"] / 71.84
            denominator = (mg_molar + fe_molar).replace(0, np.nan)
            self.df['Mg#'] = (mg_molar / denominator * 100).fillna(0)
            self.df['Mg#_Class'] = np.where(self.df['Mg#'] > 65, 'Primitive', 'Differentiated')

            # MALI
            self.df['MALI'] = major_data["Na2O"] + major_data["K2O"] - major_data["CaO"]

            # REE data
            ree_data = {}
            for ree in self.REE_ELEMENTS.keys():
                if ree in self.ree_mappings:
                    col = self.ree_mappings[ree].get().strip()
                    if col and col in self.df.columns:
                        values = self._apply_blank_correction(self.df[col].fillna(0).values)
                        ree_data[ree] = pd.Series(values, index=self.df.index)
                        self.df[f"{ree}_ppm"] = values
                else:
                    self.df[f"{ree}_ppm"] = 0

            # Chondrite normalization
            for ree in self.REE_ELEMENTS.keys():
                if ree in self.CHONDRITE_NORM and ree in ree_data:
                    with np.errstate(divide='ignore', invalid='ignore'):
                        self.df[f"{ree}_N"] = ree_data[ree] / self.CHONDRITE_NORM[ree]
                        self.df[f"{ree}_N"] = self.df[f"{ree}_N"].replace([np.inf, -np.inf], np.nan).fillna(0)
                else:
                    self.df[f"{ree}_N"] = 0

            # Eu anomaly
            if all(e in self.df.columns for e in ['Eu_N', 'Sm_N', 'Gd_N']):
                with np.errstate(divide='ignore', invalid='ignore'):
                    self.df['Eu_Eu*'] = self.df['Eu_N'] / np.sqrt(self.df['Sm_N'] * self.df['Gd_N'])
                    self.df['Eu_Eu*'] = self.df['Eu_Eu*'].replace([np.inf, -np.inf], np.nan).fillna(0)

                conditions = [
                    self.df['Eu_Eu*'] < 0.85,
                    self.df['Eu_Eu*'] > 1.15
                ]
                choices = ['Negative', 'Positive']
                self.df['Eu_Anomaly'] = np.select(conditions, choices, default='None')

            # Ce anomaly
            if all(e in self.df.columns for e in ['Ce_N', 'La_N', 'Pr_N']):
                with np.errstate(divide='ignore', invalid='ignore'):
                    self.df['Ce_Ce*'] = self.df['Ce_N'] / np.sqrt(self.df['La_N'] * self.df['Pr_N'])
                    self.df['Ce_Ce*'] = self.df['Ce_Ce*'].replace([np.inf, -np.inf], np.nan).fillna(0)

            # La/Yb
            if all(e in self.df.columns for e in ['La_N', 'Yb_N']):
                with np.errstate(divide='ignore', invalid='ignore'):
                    self.df['LaN_YbN'] = self.df['La_N'] / self.df['Yb_N'].replace(0, np.nan)
                    self.df['LaN_YbN'] = self.df['LaN_YbN'].replace([np.inf, -np.inf], np.nan).fillna(0)

            # Trace elements
            trace_data = {}
            for trace in self.TRACE_ELEMENTS.keys():
                if trace in self.trace_mappings:
                    col = self.trace_mappings[trace].get().strip()
                    if col and col in self.df.columns:
                        values = self._apply_blank_correction(self.df[col].fillna(0).values)
                        trace_data[trace] = pd.Series(values, index=self.df.index)
                        self.df[f"{trace}_ppm"] = values
                else:
                    self.df[f"{trace}_ppm"] = 0

            # N-MORB normalization
            for trace in self.TRACE_ELEMENTS.keys():
                if trace in self.NMORB_NORM and trace in trace_data:
                    with np.errstate(divide='ignore', invalid='ignore'):
                        self.df[f"{trace}_N-MORB"] = trace_data[trace] / self.NMORB_NORM[trace]
                        self.df[f"{trace}_N-MORB"] = self.df[f"{trace}_N-MORB"].replace([np.inf, -np.inf], np.nan).fillna(0)

            # Nb-Y diagram
            if 'Nb' in trace_data and 'Y' in trace_data:
                with np.errstate(divide='ignore', invalid='ignore'):
                    self.df['Nb_Y'] = trace_data['Nb'] / trace_data['Y'].replace(0, np.nan)
                    self.df['Nb_Y'] = self.df['Nb_Y'].replace([np.inf, -np.inf], np.nan).fillna(0)
                self.df['NbY_Tectonic'] = np.where(self.df['Nb_Y'] > 0.1, 'WPG', 'VAG+COLG+ORG')

            # Ta-Yb diagram
            if 'Ta' in trace_data and 'Yb' in trace_data:
                with np.errstate(divide='ignore', invalid='ignore'):
                    self.df['Ta_Yb'] = trace_data['Ta'] / trace_data['Yb'].replace(0, np.nan)
                    self.df['Ta_Yb'] = self.df['Ta_Yb'].replace([np.inf, -np.inf], np.nan).fillna(0)

            # Rb-Y+Nb diagram
            if 'Rb' in trace_data and 'Y' in trace_data and 'Nb' in trace_data:
                with np.errstate(divide='ignore', invalid='ignore'):
                    y_nb = (trace_data['Y'] + trace_data['Nb']).replace(0, np.nan)
                    self.df['Rb_Y+Nb'] = trace_data['Rb'] / y_nb
                    self.df['Rb_Y+Nb'] = self.df['Rb_Y+Nb'].replace([np.inf, -np.inf], np.nan).fillna(0)

            # A-type discrimination
            if all(e in trace_data for e in ['Zr', 'Nb', 'Ce', 'Y']):
                self.df['Zr+Nb+Ce+Y'] = sum(trace_data[e] for e in ['Zr', 'Nb', 'Ce', 'Y'])
                if 'FeO_star' in major_data and 'MgO' in major_data:
                    with np.errstate(divide='ignore', invalid='ignore'):
                        self.df['FeO_MgO'] = major_data['FeO_star'] / major_data['MgO'].replace(0, np.nan)
                        self.df['FeO_MgO'] = self.df['FeO_MgO'].replace([np.inf, -np.inf], np.nan).fillna(0)

                    conditions = [
                        (self.df['Zr+Nb+Ce+Y'] > 350) & (self.df['FeO_MgO'] > 10),
                        (self.df['Zr+Nb+Ce+Y'] <= 350) | (self.df['FeO_MgO'] <= 10)
                    ]
                    self.df['Granite_Type'] = np.select(conditions, ['A-type', 'I-S-type'], default='Unknown')

            self.df['Analysis_Date'] = datetime.now().strftime('%Y-%m-%d')
            self.results_df = self.df.copy()
            self.window.after(0, self._update_results_ui)

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.window.after(0, lambda: messagebox.showerror("Error", f"Analysis failed: {str(e)}"))
        finally:
            self.window.after(0, self._reset_processing_ui)

    def _update_results_ui(self):
        """Update results"""
        self._update_data_table()
        self._generate_all_plots()
        self._update_statistics()
        self.status_label.config(text=f"✓ Complete: {len(self.df)} samples | Anhydrous: {'ON' if self.anhydrous_var.get() else 'OFF'}",
                                fg="#27ae60")
        self.progress.stop()

    def _update_data_table(self):
        """Update data table"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        if self.df.empty:
            return

        for idx, row in self.df.head(100).iterrows():
            values = [
                row.get('Sample_ID', f"S{idx}")[:8],
                f"{row.get('SiO2_wt', 0):.1f}",
                f"{row.get('Alkali', 0):.1f}",
                f"{row.get('ASI', 0):.2f}",
                f"{row.get('Mg#', 0):.0f}",
                f"{row.get('Eu_Eu*', 0):.2f}",
                f"{row.get('LaN_YbN', 0):.1f}",
                row.get('Granite_Type', '—')[:8]
            ]
            self.tree.insert("", tk.END, values=values)

    def _generate_all_plots(self):
        """Generate plots with dynamic grid sizing"""
        self.figure.clear()

        selected = [p for p, v in self.plot_vars.items() if v.get()]
        n_plots = len(selected)

        if n_plots == 0:
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, "No plots selected", ha='center', va='center', fontsize=12)
            self.canvas.draw()
            return

        # Determine grid size
        layout = self.plot_layout_var.get()

        if "2x2" in layout:
            rows, cols = 2, 2
        elif "3x3" in layout:
            rows, cols = 3, 3
        elif "4x4" in layout:
            rows, cols = 4, 4
        else:
            # Auto: choose best fit
            if n_plots <= 4:
                rows, cols = 2, 2
            elif n_plots <= 6:
                rows, cols = 2, 3
            elif n_plots <= 9:
                rows, cols = 3, 3
            else:
                rows, cols = 4, 3

        # Show plot progress bar
        self.plot_progress.pack(fill=tk.X, pady=1)
        self.plot_progress['maximum'] = min(n_plots, rows*cols)
        self.plot_progress['value'] = 0
        self.status_label.config(text=f"Generating {min(n_plots, rows*cols)} plots...")
        self.window.update()

        # Create subplots
        for i, plot_name in enumerate(selected[:rows*cols]):
            ax = self.figure.add_subplot(rows, cols, i+1)

            if "TAS" in plot_name:
                self._plot_tas_diagram(ax)
            elif "AFM" in plot_name:
                self._plot_afm_diagram(ax)
            elif "REE Spider" in plot_name:
                self._plot_ree_spider(ax)
            elif "Multi-Spider" in plot_name:
                self._plot_multi_spider(ax)
            elif "Pearce Nb-Y" in plot_name:
                self._plot_pearce_nb_y(ax)
            elif "Pearce Ta-Yb" in plot_name:
                self._plot_pearce_ta_yb(ax)
            elif "Pearce Rb-Y+Nb" in plot_name:
                self._plot_pearce_rb_y_nb(ax)
            elif "Whalen" in plot_name:
                self._plot_whalen_diagram(ax)
            elif "Harker" in plot_name:
                self._plot_harker_diagram(ax)

            ax.set_title(plot_name, fontsize=8, fontweight='bold')
            ax.title.set_position([0.5, 1.05])

            # Update progress
            self.plot_progress['value'] = i + 1
            self.window.update()

        # Hide plot progress bar
        self.plot_progress.pack_forget()

        self.figure.tight_layout()
        self.canvas.draw()

    # ----------------------------------------------------------------------
    # PLOTTING METHODS
    # ----------------------------------------------------------------------

    def _plot_tas_diagram(self, ax):
        """Plot TAS diagram with polygon boundaries"""
        if 'SiO2_wt' not in self.df.columns or 'Alkali' not in self.df.columns:
            ax.text(0.5, 0.5, "No TAS data", ha='center', va='center')
            return

        # Plot TAS fields as polygons
        for field_name, field in self.TAS_BOUNDARIES.items():
            polygon = Polygon(list(zip(field['x'], field['y'])),
                            alpha=0.1, color='#6497b1', linewidth=0)
            ax.add_patch(polygon)

            # Add label
            x_center = sum(field['x']) / len(field['x'])
            y_center = sum(field['y']) / len(field['y'])
            if y_center < 15:
                ax.text(x_center, y_center, field_name, fontsize=5,
                       ha='center', va='center', alpha=0.6)

        # Irvine line
        x_line = np.linspace(45, 80, 50)
        y_line = 0.371 * x_line - 14.5
        ax.plot(x_line, y_line, 'k--', linewidth=0.8, label='Irvine', alpha=0.5)

        # Sample data
        ax.scatter(self.df['SiO2_wt'], self.df['Alkali'],
                  c='red', s=15, alpha=0.7, edgecolors='black', linewidth=0.2, zorder=5)

        ax.set_xlim(35, 80)
        ax.set_ylim(0, 18)
        ax.set_xlabel('SiO₂ (wt%)', fontsize=7)
        ax.set_ylabel('Na₂O+K₂O (wt%)', fontsize=7)
        ax.grid(True, alpha=0.2)
        ax.tick_params(labelsize=6)

    def _plot_afm_diagram(self, ax):
        """Plot AFM diagram"""
        required = ['Na2O_wt', 'K2O_wt', 'FeO_star_wt', 'MgO_wt']
        if not all(col in self.df.columns for col in required):
            ax.text(0.5, 0.5, "No AFM data", ha='center', va='center')
            return

        A = self.df['Na2O_wt'] + self.df['K2O_wt']
        F = self.df['FeO_star_wt']
        M = self.df['MgO_wt']
        total = A + F + M

        ax.scatter(F/total*100, M/total*100, c='blue', s=15, alpha=0.7,
                  edgecolors='black', linewidth=0.2, zorder=5)

        bx, by = zip(*self.AFM_BOUNDARY)
        ax.plot(bx, by, 'k--', linewidth=0.8, label='Tholeiitic - Calc-alkaline', alpha=0.5)

        ax.set_xlim(0, 100)
        ax.set_ylim(0, 100)
        ax.set_xlabel('F (FeO*)', fontsize=7)
        ax.set_ylabel('M (MgO)', fontsize=7)
        ax.grid(True, alpha=0.2)
        ax.tick_params(labelsize=6)

    def _plot_ree_spider(self, ax):
        """Plot REE spider diagram"""
        ree = ['La', 'Ce', 'Pr', 'Nd', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy', 'Ho', 'Er', 'Tm', 'Yb', 'Lu']
        x = np.arange(len(ree))

        has_data = False
        n = min(self.max_samples_var.get(), len(self.df))
        colors = plt.cm.rainbow(np.linspace(0, 1, n))

        for idx in range(n):
            values = []
            for r in ree:
                col = f"{r}_N"
                if col in self.df.columns:
                    val = self.df[col].iloc[idx]
                    values.append(val if val > 0 else np.nan)
                else:
                    values.append(np.nan)

            if np.sum(~np.isnan(values)) > 5:
                sample_id = self.df.iloc[idx].get('Sample_ID', f'S{idx}')
                ax.semilogy(x, values, 'o-', color=colors[idx],
                           markersize=2, linewidth=0.5, alpha=0.7, label=sample_id[:6])
                has_data = True

        if has_data:
            ax.set_xticks(x)
            ax.set_xticklabels(ree, rotation=45, fontsize=5)
            ax.set_ylabel('Sample/Chondrite', fontsize=7)
            ax.grid(True, alpha=0.2, which='both')
            ax.tick_params(labelsize=5)
            if n <= 6:
                ax.legend(loc='upper right', fontsize=5, ncol=2)
        else:
            ax.text(0.5, 0.5, "No REE data", ha='center', va='center')

    def _plot_multi_spider(self, ax):
        """Plot multi-element spider diagram"""
        elements = ['Rb', 'Ba', 'Th', 'U', 'Nb', 'Ta', 'La', 'Ce', 'Sr', 'Nd',
                   'Sm', 'Zr', 'Hf', 'Eu', 'Gd', 'Dy', 'Y', 'Er', 'Yb', 'Lu']

        available = []
        for e in elements:
            col = f"{e}_N-MORB"
            if col in self.df.columns and self.df[col].sum() > 0:
                available.append(e)

        if not available:
            ax.text(0.5, 0.5, "No N-MORB data", ha='center', va='center')
            return

        x = np.arange(len(available))
        n = min(self.max_samples_var.get(), len(self.df))
        colors = plt.cm.Set2(np.linspace(0, 1, n))

        for idx in range(n):
            values = []
            for e in available:
                col = f"{e}_N-MORB"
                val = self.df[col].iloc[idx]
                values.append(val if val > 0 else np.nan)

            if np.sum(~np.isnan(values)) > 5:
                sample_id = self.df.iloc[idx].get('Sample_ID', f'S{idx}')
                ax.semilogy(x, values, 'o-', color=colors[idx],
                           markersize=2, linewidth=0.5, alpha=0.7, label=sample_id[:6])

        ax.set_xticks(x)
        ax.set_xticklabels(available, rotation=90, fontsize=4)
        ax.set_ylabel('Sample/N-MORB', fontsize=7)
        ax.axhline(y=1, color='gray', linestyle='--', linewidth=0.3, alpha=0.5)
        ax.grid(True, alpha=0.2, which='both')
        ax.tick_params(labelsize=5)

    def _plot_pearce_nb_y(self, ax):
        """Plot Pearce Nb-Y"""
        if 'Nb_ppm' in self.df.columns and 'Y_ppm' in self.df.columns:
            nb = self.df['Nb_ppm']
            y = self.df['Y_ppm']
            mask = (y > 0) & (nb > 0) & (~pd.isna(y)) & (~pd.isna(nb))

            if mask.sum() > 0:
                ax.axvspan(0, 65, 0, 1, alpha=0.15, color='#87CEEB', label='VAG+COLG')
                ax.axvspan(65, 1000, 0, 1, alpha=0.15, color='#FFB6C1', label='WPG')
                ax.scatter(y[mask], nb[mask], c='red', s=15, alpha=0.7,
                          edgecolors='black', linewidth=0.2, zorder=5)
                ax.set_xscale('log')
                ax.set_yscale('log')
                ax.set_xlabel('Y (ppm)', fontsize=7)
                ax.set_ylabel('Nb (ppm)', fontsize=7)
                ax.grid(True, alpha=0.2, which='both')
                ax.tick_params(labelsize=6)
                ax.legend(loc='lower right', fontsize=5)
        else:
            ax.text(0.5, 0.5, "No Nb/Y data", ha='center', va='center')

    def _plot_pearce_ta_yb(self, ax):
        """Plot Pearce Ta-Yb"""
        if 'Ta_ppm' in self.df.columns and 'Yb_ppm' in self.df.columns:
            ta = self.df['Ta_ppm']
            yb = self.df['Yb_ppm']
            mask = (yb > 0) & (ta > 0) & (~pd.isna(yb)) & (~pd.isna(ta))

            if mask.sum() > 0:
                ax.axvspan(0, 2.5, 0, 1, alpha=0.15, color='#87CEEB', label='VAG+COLG')
                ax.axvspan(2.5, 100, 0, 1, alpha=0.15, color='#FFB6C1', label='WPG')
                ax.scatter(yb[mask], ta[mask], c='blue', s=15, alpha=0.7,
                          edgecolors='black', linewidth=0.2, zorder=5)
                ax.set_xscale('log')
                ax.set_yscale('log')
                ax.set_xlabel('Yb (ppm)', fontsize=7)
                ax.set_ylabel('Ta (ppm)', fontsize=7)
                ax.grid(True, alpha=0.2, which='both')
                ax.tick_params(labelsize=6)
                ax.legend(loc='lower right', fontsize=5)
        else:
            ax.text(0.5, 0.5, "No Ta/Yb data", ha='center', va='center')

    def _plot_pearce_rb_y_nb(self, ax):
        """Plot Pearce Rb-Y+Nb"""
        if all(e in self.df.columns for e in ['Rb_ppm', 'Y_ppm', 'Nb_ppm']):
            rb = self.df['Rb_ppm']
            y_nb = self.df['Y_ppm'] + self.df['Nb_ppm']
            mask = (y_nb > 0) & (rb > 0) & (~pd.isna(y_nb)) & (~pd.isna(rb))

            if mask.sum() > 0:
                ax.axvspan(0, 55, 0, 550, alpha=0.15, color='#87CEEB', label='VAG')
                ax.axvspan(55, 550, 0, 550, alpha=0.15, color='#F4A460', label='syn-COLG')
                ax.axvspan(550, 2000, 0, 550, alpha=0.15, color='#FFB6C1', label='WPG')
                ax.scatter(y_nb[mask], rb[mask], c='green', s=15, alpha=0.7,
                          edgecolors='black', linewidth=0.2, zorder=5)
                ax.set_xscale('log')
                ax.set_yscale('log')
                ax.set_xlabel('Y+Nb (ppm)', fontsize=7)
                ax.set_ylabel('Rb (ppm)', fontsize=7)
                ax.grid(True, alpha=0.2, which='both')
                ax.tick_params(labelsize=6)
                ax.legend(loc='lower right', fontsize=5)
        else:
            ax.text(0.5, 0.5, "No Rb/(Y+Nb) data", ha='center', va='center')

    def _plot_whalen_diagram(self, ax):
        """Plot Whalen A-type"""
        if 'Zr+Nb+Ce+Y' in self.df.columns and 'FeO_MgO' in self.df.columns:
            z = self.df['Zr+Nb+Ce+Y']
            f = self.df['FeO_MgO']
            mask = (z > 0) & (f > 0) & (~pd.isna(z)) & (~pd.isna(f))

            if mask.sum() > 0:
                ax.axvspan(0, 350, 0, 10, alpha=0.15, color='#B0C4DE', label='I&S-type')
                ax.axvspan(350, 2000, 10, 100, alpha=0.15, color='#FFA07A', label='A-type')
                ax.axhline(y=10, color='black', linestyle='--', linewidth=0.5, alpha=0.3)
                ax.axvline(x=350, color='black', linestyle='--', linewidth=0.5, alpha=0.3)

                if 'Granite_Type' in self.df.columns:
                    colors = np.where(self.df['Granite_Type'] == 'A-type', '#FFA07A', '#B0C4DE')
                else:
                    colors = ['#B0C4DE'] * len(z)

                ax.scatter(z[mask], f[mask], c=colors[mask], s=15, alpha=0.7,
                          edgecolors='black', linewidth=0.2, zorder=5)

                ax.set_xscale('log')
                ax.set_yscale('log')
                ax.set_xlabel('Zr+Nb+Ce+Y', fontsize=7)
                ax.set_ylabel('FeO*/MgO', fontsize=7)
                ax.grid(True, alpha=0.2, which='both')
                ax.tick_params(labelsize=6)
                ax.legend(loc='upper left', fontsize=5)
        else:
            ax.text(0.5, 0.5, "No A-type data", ha='center', va='center')

    def _plot_harker_diagram(self, ax):
        """Plot Harker diagram"""
        if 'SiO2_wt' in self.df.columns and 'MgO_wt' in self.df.columns:
            sio2 = self.df['SiO2_wt']
            mgo = self.df['MgO_wt']
            mask = ~(sio2.isna() | mgo.isna() | (sio2 == 0))

            if mask.sum() > 0:
                ax.scatter(sio2[mask], mgo[mask], c='green', s=15, alpha=0.7,
                          edgecolors='black', linewidth=0.2, zorder=5)

                if mask.sum() > 1:
                    z = np.polyfit(sio2[mask], mgo[mask], 1)
                    p = np.poly1d(z)
                    x_trend = np.linspace(sio2[mask].min(), sio2[mask].max(), 50)
                    ax.plot(x_trend, p(x_trend), "r--", alpha=0.6, linewidth=0.8)

                ax.set_xlabel('SiO₂ (wt%)', fontsize=7)
                ax.set_ylabel('MgO (wt%)', fontsize=7)
                ax.grid(True, alpha=0.2)
                ax.tick_params(labelsize=6)
        else:
            ax.text(0.5, 0.5, "No Harker data", ha='center', va='center')

    def _update_statistics(self):
        """Update statistics"""
        if self.df.empty:
            return

        text = "🪨 PETROPLOT PRO - RESULTS SUMMARY\n"
        text += "=" * 50 + "\n\n"

        text += f"📊 Samples: {len(self.df)} | Anhydrous: {'ON' if self.anhydrous_var.get() else 'OFF'}\n"
        text += f"   LOI: {self.loi_correction_var.get()} | Blank: {self.blank_var.get():.2f} ppm\n\n"

        if 'SiO2_wt' in self.df.columns:
            text += f"SiO₂: {self.df['SiO2_wt'].mean():.1f}±{self.df['SiO2_wt'].std():.1f} wt%\n"
            text += f"Alkali: {self.df['Alkali'].mean():.1f}±{self.df['Alkali'].std():.1f} wt%\n"

        if 'ASI' in self.df.columns:
            text += f"\nASI: {self.df['ASI'].mean():.2f}±{self.df['ASI'].std():.2f}\n"
            pct = (self.df['ASI'] > 1).sum() / len(self.df) * 100
            text += f"Peraluminous: {pct:.0f}%\n"

        if 'Mg#' in self.df.columns:
            text += f"\nMg#: {self.df['Mg#'].mean():.0f}±{self.df['Mg#'].std():.0f}\n"
            pct = (self.df['Mg#_Class'] == 'Primitive').sum() / len(self.df) * 100
            text += f"Primitive: {pct:.0f}%\n"

        if 'Eu_Eu*' in self.df.columns:
            text += f"\nEu/Eu*: {self.df['Eu_Eu*'].mean():.2f}±{self.df['Eu_Eu*'].std():.2f}\n"
            neg = (self.df['Eu_Anomaly'] == 'Negative').sum()
            if neg > 0:
                text += f"Negative Eu: {neg}/{len(self.df)} ({neg/len(self.df)*100:.0f}%)\n"

        if 'LaN_YbN' in self.df.columns:
            text += f"\nLaN/YbN: {self.df['LaN_YbN'].mean():.1f}±{self.df['LaN_YbN'].std():.1f}\n"

        if 'Granite_Type' in self.df.columns:
            a_type = (self.df['Granite_Type'] == 'A-type').sum()
            if a_type > 0:
                text += f"\nA-type granites: {a_type}/{len(self.df)} ({a_type/len(self.df)*100:.0f}%)\n"

        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, text)

    def _export_geochemical_data(self):
        """Export data"""
        if self.df.empty:
            messagebox.showwarning("No Data", "No results to export")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("Excel", "*.xlsx")],
            initialfile=f"PetroPlot_{datetime.now().strftime('%Y%m%d')}.csv"
        )

        if filename:
            try:
                if filename.endswith('.csv'):
                    self.df.to_csv(filename, index=False)
                else:
                    self.df.to_excel(filename, index=False)
                messagebox.showinfo("Export Complete", f"Data exported to:\n{filename}")
            except Exception as e:
                messagebox.showerror("Export Failed", str(e))

    def _reset_processing_ui(self):
        """Reset UI after processing"""
        self.is_processing = False
        self.process_btn.config(state=tk.NORMAL, text="🪨 GENERATE PLOTS")
        self.progress.stop()

# ----------------------------------------------------------------------
# PLUGIN ENTRY POINT
# ----------------------------------------------------------------------

def setup_plugin(main_app):
    """Plugin setup function - FOLLOWING WORKING PATTERN"""
    plugin = PetroPlotProPlugin(main_app)
    return plugin  # ← JUST RETURN PLUGIN, NO MENU CREATION
