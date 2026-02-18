"""
Spatial Interpolation & Density Estimation Plugin
Professional geostatistical interpolation with optimized performance + KDE contouring
"""

PLUGIN_INFO = {
    "category": "software",
    "id": "spatial_kriging",
    "name": "Spatial Kriging & Density",
    "description": "Industry-standard spatial interpolation with variogram analysis + KDE contouring",
    "icon": "🗺️",
    "version": "3.2",
    "requires": ["numpy", "scipy", "matplotlib"],
    "author": "Sefy Levy & DeepSeek",

    "item": {
        "type": "plugin",
        "subtype": "spatial_analysis",
        "tags": ["kriging", "geostatistics", "variogram", "provenance", "contouring", "density", "kde"],
        "compatibility": ["main_app_v2+"],
        "dependencies": ["numpy>=1.19.0", "scipy>=1.6.0", "matplotlib>=3.3.0"],
        "settings": {
            "default_method": "ordinary_kriging",
            "auto_fit_variogram": True,
            "default_kde_bandwidth": "scott",
            "contour_levels": 8
        }
    }
}

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import pandas as pd
import numpy as np
import threading
import time
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from scipy.stats import gaussian_kde
from scipy.ndimage import gaussian_filter
from scipy.spatial.distance import pdist
from scipy.optimize import curve_fit
from scipy.linalg import solve
from scipy.spatial import cKDTree
import warnings
warnings.filterwarnings('ignore')

class SpatialKrigingPlugin:
    def __init__(self, main_app):
        self.app = main_app
        self.window = None
        self.df = pd.DataFrame()
        self.is_processing = False
        self.cancelled = False
        self.progress = None
        self.aspect_ratio = 1.0
        self.sample_coords = None
        self.interpolation_result = None
        self.density_result = None

        # Industry-standard interpolation methods
        self.INTERPOLATION_METHODS = {
            "Ordinary Kriging": "Best linear unbiased estimator with variogram",
            "Inverse Distance Weighting": "Distance-weighted average"
        }

        # Contouring methods from interactive_contouring
        self.CONTOUR_METHODS = {
            "Gaussian KDE": "Gaussian Kernel Density Estimation",
            "2D Histogram": "Histogram-based density estimation",
            "Distance-based": "Nearest neighbor density estimation"
        }

        # Variogram models
        self.VARIOGRAM_MODELS = {
            "Spherical": "γ(h) = n + s * (1.5*(h/a) - 0.5*(h/a)³) for h ≤ a, else n + s",
            "Exponential": "γ(h) = n + s * (1 - exp(-3h/a))",
            "Gaussian": "γ(h) = n + s * (1 - exp(-3h²/a²))"
        }

        # Color maps
        self.COLORMAPS = ["viridis", "plasma", "inferno", "magma", "cividis", "coolwarm", "RdYlBu", "Spectral"]

        # Common suggestions for geochemical elements
        self.ELEMENT_SUGGESTIONS = [
            "SiO2", "TiO2", "Al2O3", "Fe2O3", "MgO", "CaO", "Na2O", "K2O", "P2O5",
            "La", "Ce", "Nd", "Sm", "Eu", "Gd", "Yb", "Lu",
            "Rb", "Sr", "Ba", "Zr", "Nb", "Y", "Cr", "Ni", "V", "Sc"
        ]

        # Bandwidth options
        self.BANDWIDTH_OPTIONS = ["scott", "silverman", "0.1", "0.2", "0.5", "1.0"]

        # Default parameters
        self.DEFAULT_PARAMS = {
            "idw_power": 2.0,
            "search_radius": 200.0,
            "min_neighbors": 5,
            "sill": 1.0,
            "range_val": 100.0,
            "nugget": 0.1
        }

        # ============ INITIALIZE ALL VARIABLES ============
        # Interpolation variables
        self.lon_var = tk.StringVar(value="")
        self.lat_var = tk.StringVar(value="")
        self.value_var = tk.StringVar(value="")
        self.method_var = tk.StringVar(value="Ordinary Kriging")
        self.grid_size_var = tk.IntVar(value=80)
        self.cmap_var = tk.StringVar(value="viridis")
        self.preserve_aspect_var = tk.BooleanVar(value=True)
        self.show_samples_var = tk.BooleanVar(value=True)
        self.auto_fit_var = tk.BooleanVar(value=True)

        # Kriging specific
        self.variogram_var = tk.StringVar(value="Spherical")
        self.nugget_var = tk.DoubleVar(value=self.DEFAULT_PARAMS["nugget"])
        self.sill_var = tk.DoubleVar(value=self.DEFAULT_PARAMS["sill"])
        self.range_var = tk.DoubleVar(value=self.DEFAULT_PARAMS["range_val"])
        self.min_neighbors_var = tk.IntVar(value=self.DEFAULT_PARAMS["min_neighbors"])

        # IDW specific
        self.idw_power_var = tk.DoubleVar(value=self.DEFAULT_PARAMS["idw_power"])
        self.search_radius_var = tk.DoubleVar(value=self.DEFAULT_PARAMS["search_radius"])

        # Density variables
        self.density_x_var = tk.StringVar(value="")
        self.density_y_var = tk.StringVar(value="")
        self.density_method_var = tk.StringVar(value="Gaussian KDE")
        self.density_grid_var = tk.IntVar(value=100)
        self.levels_var = tk.IntVar(value=8)
        self.bw_var = tk.StringVar(value="scott")
        self.density_cmap_var = tk.StringVar(value="viridis")
        self.show_points_var = tk.BooleanVar(value=True)
        self.fill_contours_var = tk.BooleanVar(value=True)
        self.show_colorbar_var = tk.BooleanVar(value=True)

        # UI elements (will be set during UI creation)
        self.lon_combo = None
        self.lat_combo = None
        self.value_combo = None
        self.density_x_combo = None
        self.density_y_combo = None
        self.params_frame = None

    def open_window(self):
        """Open compact main window with density tab"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title(f"{PLUGIN_INFO['icon']} {PLUGIN_INFO['name']} v{PLUGIN_INFO['version']}")
        self.window.geometry("1150x700")
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

        self._create_ui()
        self.window.after(100, self._import_from_main)

    def _on_close(self):
        """Handle window closing safely"""
        if self.is_processing:
            if messagebox.askyesno("Cancel", "Interpolation in progress. Cancel and close?"):
                self.cancelled = True
                self.is_processing = False
                if self.progress:
                    self.progress.stop()
                time.sleep(0.1)
        self.window.destroy()

    def _create_ui(self):
        """Create compact user interface with density tab"""
        # Header
        header = tk.Frame(self.window, bg="#2c3e50")
        header.pack(fill=tk.X)
        tk.Label(header, text="📍 Professional Spatial Analysis & Density",
                font=("Arial", 14, "bold"),
                bg="#2c3e50", fg="white", pady=10).pack()

        # Main container
        main_paned = tk.PanedWindow(self.window, orient=tk.HORIZONTAL, sashwidth=6)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)

        # Left panel - Controls
        left_panel = tk.Frame(main_paned, bg="#ecf0f1", relief=tk.RAISED, borderwidth=1)
        main_paned.add(left_panel, minsize=360)

        # Right panel - Results with notebook
        right_panel = tk.Frame(main_paned, bg="white")
        main_paned.add(right_panel, minsize=750)

        # Create notebook for right panel (Map, Variogram, Stats, Density)
        style = ttk.Style()
        style.configure("TNotebook.Tab", font=("Arial", 9))

        self.notebook = ttk.Notebook(right_panel)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)

        # Map tab (for interpolation)
        map_tab = tk.Frame(self.notebook)
        self.notebook.add(map_tab, text="🗺️ Map")

        self.figure = plt.Figure(figsize=(8, 5), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, map_tab)

        toolbar = NavigationToolbar2Tk(self.canvas, map_tab)
        toolbar.update()

        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=3, pady=3)

        # Variogram tab
        vario_tab = tk.Frame(self.notebook)
        self.notebook.add(vario_tab, text="📈 Variogram")

        self.vario_figure = plt.Figure(figsize=(8, 3), dpi=100)
        self.vario_ax = self.vario_figure.add_subplot(111)
        self.vario_canvas = FigureCanvasTkAgg(self.vario_figure, vario_tab)
        self.vario_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=3, pady=3)

        # Statistics tab
        stats_tab = tk.Frame(self.notebook)
        self.notebook.add(stats_tab, text="📊 Stats")

        self.stats_text = scrolledtext.ScrolledText(stats_tab, wrap=tk.WORD,
                                                   font=("Courier", 9), height=15)
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)

        # NEW: Density tab (from interactive_contouring)
        density_tab = tk.Frame(self.notebook)
        self.notebook.add(density_tab, text="🗺️ Density Contours")

        self.density_figure = plt.Figure(figsize=(8, 5), dpi=100)
        self.density_ax = self.density_figure.add_subplot(111)
        self.density_canvas = FigureCanvasTkAgg(self.density_figure, density_tab)

        density_toolbar = NavigationToolbar2Tk(self.density_canvas, density_tab)
        density_toolbar.update()

        self.density_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=3, pady=3)

        # Log tab (from contouring)
        log_tab = tk.Frame(self.notebook)
        self.notebook.add(log_tab, text="📝 Log")

        self.log_text = scrolledtext.ScrolledText(log_tab, wrap=tk.WORD, font=("Courier", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)

        self._setup_left_panel(left_panel)

    def _setup_left_panel(self, parent):
        """Setup compact control panel with both interpolation and density controls"""
        # Data info
        info_frame = tk.LabelFrame(parent, text="📊 Data", padx=8, pady=8, bg="#ecf0f1")
        info_frame.pack(fill=tk.X, padx=8, pady=8)

        self.data_info_label = tk.Label(info_frame, text="No data loaded", bg="#ecf0f1", font=("Arial", 9))
        self.data_info_label.pack(anchor=tk.W)

        # Main notebook for control modes
        self.control_notebook = ttk.Notebook(parent)
        self.control_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)

        # Tab 1: Interpolation controls
        interp_frame = tk.Frame(self.control_notebook, bg="#ecf0f1")
        self.control_notebook.add(interp_frame, text="📍 Interpolation")
        self._setup_interpolation_controls(interp_frame)

        # Tab 2: Density/Contour controls (from interactive_contouring)
        density_frame = tk.Frame(self.control_notebook, bg="#ecf0f1")
        self.control_notebook.add(density_frame, text="🗺️ Density Contours")
        self._setup_density_controls(density_frame)

        # Common buttons at bottom
        button_frame = tk.Frame(parent, bg="#ecf0f1", pady=8)
        button_frame.pack(fill=tk.X, padx=8)

        row1_frame = tk.Frame(button_frame, bg="#ecf0f1")
        row1_frame.pack(fill=tk.X, pady=2)

        self.load_btn = tk.Button(row1_frame, text="📥 Load", bg="#3498db", fg="white",
                                 width=10, font=("Arial", 9), command=self._import_from_main)
        self.load_btn.pack(side=tk.LEFT, padx=2)

        self.interpolate_btn = tk.Button(row1_frame, text="📍 Run Interp", bg="#9b59b6", fg="white",
                                        width=12, font=("Arial", 9), command=self._start_interpolation)
        self.interpolate_btn.pack(side=tk.LEFT, padx=2)

        self.density_btn = tk.Button(row1_frame, text="🗺️ Run Density", bg="#e67e22", fg="white",
                                    width=12, font=("Arial", 9), command=self._start_density)
        self.density_btn.pack(side=tk.LEFT, padx=2)

        row2_frame = tk.Frame(button_frame, bg="#ecf0f1")
        row2_frame.pack(fill=tk.X, pady=2)

        self.export_btn = tk.Button(row2_frame, text="💾 Export", bg="#2ecc71", fg="white",
                                   width=10, font=("Arial", 9), command=self._export_results)
        self.export_btn.pack(side=tk.LEFT, padx=2)

        self.import_btn = tk.Button(row2_frame, text="📤 Import", bg="#e67e22", fg="white",
                                   width=10, font=("Arial", 9), command=self._import_from_main)
        self.import_btn.pack(side=tk.LEFT, padx=2)

        # Status
        self.status_label = tk.Label(parent, text="Ready", bg="#ecf0f1",
                                    fg="#7f8c8d", font=("Arial", 9))
        self.status_label.pack(fill=tk.X, padx=8, pady=(8, 3))

        # Progress
        self.progress = ttk.Progressbar(parent, mode='determinate', length=100)
        self.progress.pack(fill=tk.X, padx=8, pady=3)

    def _setup_interpolation_controls(self, parent):
        """Setup interpolation-specific controls - compact version"""
        # Coordinate selection - compact
        coord_frame = tk.LabelFrame(parent, text="🌍 Coordinates", padx=5, pady=3, bg="#ecf0f1")
        coord_frame.pack(fill=tk.X, padx=3, pady=2)

        tk.Label(coord_frame, text="X:", bg="#ecf0f1", font=("Arial", 8)).grid(row=0, column=0, sticky=tk.W, pady=1)
        # REMOVE the line below - it's already created in __init__
        # self.lon_var = tk.StringVar(value="")
        self.lon_combo = ttk.Combobox(coord_frame, textvariable=self.lon_var, width=15, font=("Arial", 8))
        self.lon_combo.grid(row=0, column=1, padx=2, pady=1, sticky="ew")

        tk.Label(coord_frame, text="Y:", bg="#ecf0f1", font=("Arial", 8)).grid(row=1, column=0, sticky=tk.W, pady=1)
        # REMOVE
        # self.lat_var = tk.StringVar(value="")
        self.lat_combo = ttk.Combobox(coord_frame, textvariable=self.lat_var, width=15, font=("Arial", 8))
        self.lat_combo.grid(row=1, column=1, padx=2, pady=1, sticky="ew")

        tk.Label(coord_frame, text="Value:", bg="#ecf0f1", font=("Arial", 8)).grid(row=2, column=0, sticky=tk.W, pady=1)
        # REMOVE
        # self.value_var = tk.StringVar(value="")
        self.value_combo = ttk.Combobox(coord_frame, textvariable=self.value_var, width=15, font=("Arial", 8))
        self.value_combo.grid(row=2, column=1, padx=2, pady=1, sticky="ew")

        coord_frame.columnconfigure(1, weight=1)

        # Method selection - compact
        method_frame = tk.LabelFrame(parent, text="🔄 Method", padx=5, pady=3, bg="#ecf0f1")
        method_frame.pack(fill=tk.X, padx=3, pady=2)

        # REMOVE - already set in __init__
        # self.method_var = tk.StringVar(value="Ordinary Kriging")
        for method in self.INTERPOLATION_METHODS.keys():
            tk.Radiobutton(method_frame, text=method, variable=self.method_var,
                        value=method, bg="#ecf0f1", font=("Arial", 8),
                        command=self._update_method_params).pack(anchor=tk.W, pady=0)

        # Parameters frame
        self.params_frame = tk.LabelFrame(parent, text="⚙️ Params", padx=5, pady=3, bg="#ecf0f1")
        self.params_frame.pack(fill=tk.X, padx=3, pady=2)
        self._setup_kriging_params()

        # Grid settings - compact
        grid_frame = tk.LabelFrame(parent, text="📐 Grid", padx=5, pady=3, bg="#ecf0f1")
        grid_frame.pack(fill=tk.X, padx=3, pady=2)

        # Two-column layout for grid settings
        inner = tk.Frame(grid_frame, bg="#ecf0f1")
        inner.pack(fill=tk.X)

        tk.Label(inner, text="Cells:", bg="#ecf0f1", font=("Arial", 8)).grid(row=0, column=0, sticky=tk.W, pady=1)
        # REMOVE - already set
        # self.grid_size_var = tk.IntVar(value=80)
        tk.Spinbox(inner, from_=30, to=200, textvariable=self.grid_size_var,
                width=6, font=("Arial", 8)).grid(row=0, column=1, padx=2, pady=1, sticky="w")

        tk.Label(inner, text="Cmap:", bg="#ecf0f1", font=("Arial", 8)).grid(row=1, column=0, sticky=tk.W, pady=1)
        # REMOVE - already set
        # self.cmap_var = tk.StringVar(value="viridis")
        ttk.Combobox(inner, textvariable=self.cmap_var,
                    values=self.COLORMAPS, width=8, font=("Arial", 8)).grid(row=1, column=1, padx=2, pady=1, sticky="w")

        # Checkboxes in a single row
        check_frame = tk.Frame(grid_frame, bg="#ecf0f1")
        check_frame.pack(fill=tk.X)

        # REMOVE - already set
        # self.preserve_aspect_var = tk.BooleanVar(value=True)
        tk.Checkbutton(check_frame, text="Aspect", variable=self.preserve_aspect_var,
                    bg="#ecf0f1", font=("Arial", 7)).pack(side=tk.LEFT, padx=1)

        # self.show_samples_var = tk.BooleanVar(value=True)
        tk.Checkbutton(check_frame, text="Points", variable=self.show_samples_var,
                    bg="#ecf0f1", font=("Arial", 7)).pack(side=tk.LEFT, padx=1)

        # self.auto_fit_var = tk.BooleanVar(value=True)
        tk.Checkbutton(check_frame, text="Auto-fit", variable=self.auto_fit_var,
                    bg="#ecf0f1", font=("Arial", 7)).pack(side=tk.LEFT, padx=1)

    def _setup_density_controls(self, parent):
        """Setup density/contour controls - compact version"""
        # Axis selection
        axis_frame = tk.LabelFrame(parent, text="🎯 Axis", padx=5, pady=3, bg="#ecf0f1")
        axis_frame.pack(fill=tk.X, padx=3, pady=2)

        tk.Label(axis_frame, text="X:", bg="#ecf0f1", font=("Arial", 8)).grid(row=0, column=0, sticky=tk.W, pady=1)
        self.density_x_var = tk.StringVar(value="")
        self.density_x_combo = ttk.Combobox(axis_frame, textvariable=self.density_x_var,
                                        values=self.ELEMENT_SUGGESTIONS, width=15, font=("Arial", 8))
        self.density_x_combo.grid(row=0, column=1, padx=2, pady=1)

        tk.Label(axis_frame, text="Y:", bg="#ecf0f1", font=("Arial", 8)).grid(row=1, column=0, sticky=tk.W, pady=1)
        self.density_y_var = tk.StringVar(value="")
        self.density_y_combo = ttk.Combobox(axis_frame, textvariable=self.density_y_var,
                                        values=self.ELEMENT_SUGGESTIONS, width=15, font=("Arial", 8))
        self.density_y_combo.grid(row=1, column=1, padx=2, pady=1)

        # Method
        method_frame = tk.LabelFrame(parent, text="🔄 Method", padx=5, pady=3, bg="#ecf0f1")
        method_frame.pack(fill=tk.X, padx=3, pady=2)

        self.density_method_var = tk.StringVar(value="Gaussian KDE")
        row = 0
        for method in self.CONTOUR_METHODS.keys():
            tk.Radiobutton(method_frame, text=method[:12], variable=self.density_method_var,
                        value=method, bg="#ecf0f1", font=("Arial", 7)).grid(row=row, column=0, sticky=tk.W, pady=0)
            row += 1

        # Parameters in a single line
        params_frame = tk.LabelFrame(parent, text="⚙️ Params", padx=5, pady=3, bg="#ecf0f1")
        params_frame.pack(fill=tk.X, padx=3, pady=2)

        # Grid size with scale
        size_frame = tk.Frame(params_frame, bg="#ecf0f1")
        size_frame.pack(fill=tk.X)
        tk.Label(size_frame, text="Grid:", bg="#ecf0f1", font=("Arial", 8)).pack(side=tk.LEFT)
        self.density_grid_var = tk.IntVar(value=100)
        tk.Scale(size_frame, from_=50, to=200, variable=self.density_grid_var,
                orient=tk.HORIZONTAL, length=120, bg="#ecf0f1", showvalue=0).pack(side=tk.LEFT, padx=2)
        tk.Label(size_frame, textvariable=self.density_grid_var, bg="#ecf0f1", font=("Arial", 7), width=3).pack(side=tk.LEFT)

        # Second row of params
        param_row = tk.Frame(params_frame, bg="#ecf0f1")
        param_row.pack(fill=tk.X)

        tk.Label(param_row, text="Levels:", bg="#ecf0f1", font=("Arial", 8)).pack(side=tk.LEFT)
        self.levels_var = tk.IntVar(value=8)
        tk.Spinbox(param_row, from_=3, to=20, textvariable=self.levels_var,
                width=3, font=("Arial", 8)).pack(side=tk.LEFT, padx=2)

        tk.Label(param_row, text="BW:", bg="#ecf0f1", font=("Arial", 8)).pack(side=tk.LEFT, padx=(5,0))
        self.bw_var = tk.StringVar(value="scott")
        ttk.Combobox(param_row, textvariable=self.bw_var,
                    values=self.BANDWIDTH_OPTIONS, width=6, font=("Arial", 8)).pack(side=tk.LEFT, padx=2)

        tk.Label(param_row, text="Cmap:", bg="#ecf0f1", font=("Arial", 8)).pack(side=tk.LEFT, padx=(5,0))
        self.density_cmap_var = tk.StringVar(value="viridis")
        ttk.Combobox(param_row, textvariable=self.density_cmap_var,
                    values=self.COLORMAPS, width=6, font=("Arial", 8)).pack(side=tk.LEFT, padx=2)

        # Display options in one row
        display_frame = tk.Frame(parent, bg="#ecf0f1")
        display_frame.pack(fill=tk.X, padx=3, pady=1)

        self.show_points_var = tk.BooleanVar(value=True)
        tk.Checkbutton(display_frame, text="Points", variable=self.show_points_var,
                    bg="#ecf0f1", font=("Arial", 7)).pack(side=tk.LEFT, padx=1)

        self.fill_contours_var = tk.BooleanVar(value=True)
        tk.Checkbutton(display_frame, text="Fill", variable=self.fill_contours_var,
                    bg="#ecf0f1", font=("Arial", 7)).pack(side=tk.LEFT, padx=1)

        self.show_colorbar_var = tk.BooleanVar(value=True)
        tk.Checkbutton(display_frame, text="Colorbar", variable=self.show_colorbar_var,
                    bg="#ecf0f1", font=("Arial", 7)).pack(side=tk.LEFT, padx=1)

    def _setup_kriging_params(self):
        """Setup kriging parameters - compact grid layout"""
        for widget in self.params_frame.winfo_children():
            widget.destroy()

        # Create a grid for parameters
        params = [
            ("Model:", self.variogram_var, list(self.VARIOGRAM_MODELS.keys()), 8),
            ("Nugget:", self.nugget_var, None, 6),
            ("Sill:", self.sill_var, None, 6),
            ("Range:", self.range_var, None, 6),
            ("Min nbr:", self.min_neighbors_var, None, 6)
        ]

        row = 0
        col = 0
        for label, var, values, width in params:
            # Label
            tk.Label(self.params_frame, text=label, bg="#ecf0f1", font=("Arial", 8)).grid(
                row=row, column=col*2, sticky=tk.W, padx=(2,0), pady=1)

            # Value widget
            if values:  # Combobox
                widget = ttk.Combobox(self.params_frame, textvariable=var,
                                    values=values, width=width, font=("Arial", 8))
            elif isinstance(var, tk.DoubleVar):  # Double spinbox
                widget = tk.Spinbox(self.params_frame, from_=0.0, to=100.0, increment=0.1,
                                textvariable=var, width=width, font=("Arial", 8))
            else:  # Int spinbox
                widget = tk.Spinbox(self.params_frame, from_=1, to=20,
                                textvariable=var, width=width, font=("Arial", 8))

            widget.grid(row=row, column=col*2+1, padx=2, pady=1, sticky="w")

            col += 1
            if col > 1:  # Two columns
                col = 0
                row += 1

    def _setup_idw_params(self):
        """Setup IDW parameters"""
        for widget in self.params_frame.winfo_children():
            widget.destroy()

        tk.Label(self.params_frame, text="Power:", bg="#ecf0f1", font=("Arial", 9)).grid(row=0, column=0, sticky=tk.W, pady=2)
        self.idw_power_var = tk.DoubleVar(value=self.DEFAULT_PARAMS["idw_power"])
        tk.Spinbox(self.params_frame, from_=0.5, to=5.0, increment=0.5,
                  textvariable=self.idw_power_var, width=10, font=("Arial", 9)).grid(row=0, column=1, padx=3, pady=2)

        tk.Label(self.params_frame, text="Min neighbors:", bg="#ecf0f1", font=("Arial", 9)).grid(row=1, column=0, sticky=tk.W, pady=2)
        self.min_neighbors_var = tk.IntVar(value=self.DEFAULT_PARAMS["min_neighbors"])
        tk.Spinbox(self.params_frame, from_=1, to=20, textvariable=self.min_neighbors_var,
                  width=10, font=("Arial", 9)).grid(row=1, column=1, padx=3, pady=2)

        tk.Label(self.params_frame, text="Search radius:", bg="#ecf0f1", font=("Arial", 9)).grid(row=2, column=0, sticky=tk.W, pady=2)
        self.search_radius_var = tk.DoubleVar(value=self.DEFAULT_PARAMS["search_radius"])
        tk.Spinbox(self.params_frame, from_=10.0, to=1000.0, increment=50.0,
                  textvariable=self.search_radius_var, width=10, font=("Arial", 9)).grid(row=2, column=1, padx=3, pady=2)

    def _update_method_params(self):
        """Update parameters based on method"""
        if "Kriging" in self.method_var.get():
            self._setup_kriging_params()
        else:
            self._setup_idw_params()



    def _validate_inputs(self):
        """Validate all inputs before processing"""
        errors = []

        lon_col = self.lon_var.get().strip()
        lat_col = self.lat_var.get().strip()
        value_col = self.value_var.get().strip()

        if not lon_col:
            errors.append("Select X column")
        if not lat_col:
            errors.append("Select Y column")
        if not value_col:
            errors.append("Select value column")

        if errors:
            return "\n".join(errors)

        # Check columns exist
        if lon_col not in self.df.columns:
            return f"X column '{lon_col}' not found"
        if lat_col not in self.df.columns:
            return f"Y column '{lat_col}' not found"
        if value_col not in self.df.columns:
            return f"Value column '{value_col}' not found"

        # CRITICAL: Check X and Y are different
        if lon_col == lat_col:
            return "X and Y cannot be the same column"

        # Check for valid data
        valid_mask = ~(self.df[lon_col].isna() | self.df[lat_col].isna() | self.df[value_col].isna())
        valid_count = valid_mask.sum()

        if valid_count < 5:
            return f"Need at least 5 valid points (have {valid_count})"

        return None

    def _validate_density_inputs(self):
        """Validate density inputs"""
        x_col = self.density_x_var.get().strip()
        y_col = self.density_y_var.get().strip()

        if not x_col or not y_col:
            return "Select both X and Y columns"

        # Check columns exist
        x_found, _ = self._get_column_data(x_col)
        y_found, _ = self._get_column_data(y_col)

        if x_found is None:
            return f"Column '{x_col}' not found"
        if y_found is None:
            return f"Column '{y_col}' not found"

        # Get valid data
        x_data, _ = self._get_column_data(x_col)
        y_data, _ = self._get_column_data(y_col)

        if x_data is None or y_data is None:
            return "Could not find valid data columns"

        valid_mask = ~(pd.isna(x_data) | pd.isna(y_data))
        valid_count = valid_mask.sum()

        if valid_count < 10:
            return f"Need at least 10 valid points (have {valid_count})"

        return None

    def _get_column_data(self, col_name):
        """Get column data with flexible matching (from interactive_contouring)"""
        # Try exact match
        if col_name in self.df.columns:
            return self.df[col_name].values, col_name

        # Try case-insensitive match
        for col in self.df.columns:
            if col.lower() == col_name.lower():
                return self.df[col].values, col

        # Try partial match
        for col in self.df.columns:
            if col_name.lower() in col.lower():
                return self.df[col].values, col

        # Try without common suffixes
        base_name = col_name.rstrip('_0123456789()% ')
        for col in self.df.columns:
            if base_name.lower() in col.lower():
                return self.df[col].values, col

        return None, col_name

    def _start_interpolation(self):
        """Start interpolation with performance warnings"""
        if self.is_processing:
            return

        error = self._validate_inputs()
        if error:
            messagebox.showerror("Input Error", error)
            return

        # Performance warning for large datasets
        sample_count = len(self.df)
        grid_size = self.grid_size_var.get()

        if sample_count > 300 and "Kriging" in self.method_var.get():
            est_time = (sample_count * grid_size**2) / 50000
            warning = (
                f"Performance Warning\n\n"
                f"Samples: {sample_count}\n"
                f"Grid: {grid_size}×{grid_size}\n"
                f"Estimated time: {est_time:.1f} minutes\n\n"
                f"Consider:\n"
                f"• Reduce grid size (current: {grid_size})\n"
                f"• Use IDW method (faster)\n"
                f"• Use fewer samples\n\n"
                f"Continue with kriging?"
            )

            if not messagebox.askyesno("Warning", warning):
                return

        self.is_processing = True
        self.cancelled = False
        self.interpolate_btn.config(state=tk.DISABLED, text="Running...")
        self.progress['value'] = 0
        self.status_label.config(text="Starting interpolation...", fg="orange")

        thread = threading.Thread(target=self._run_interpolation, daemon=True)
        thread.start()

    def _start_density(self):
        """Start density contour generation (from interactive_contouring)"""
        if self.is_processing:
            return

        error = self._validate_density_inputs()
        if error:
            messagebox.showerror("Input Error", error)
            return

        self.is_processing = True
        self.cancelled = False
        self.density_btn.config(state=tk.DISABLED, text="Running...")
        self.progress['value'] = 0
        self.status_label.config(text="Generating density contours...", fg="orange")

        thread = threading.Thread(target=self._run_density, daemon=True)
        thread.start()

    def _run_interpolation(self):
        """Run interpolation in thread"""
        try:
            # Get data
            lon_col = self.lon_var.get()
            lat_col = self.lat_var.get()
            value_col = self.value_var.get()

            x = self.df[lon_col].values
            y = self.df[lat_col].values
            z = self.df[value_col].values

            # Remove NaN
            valid = ~(np.isnan(x) | np.isnan(y) | np.isnan(z))
            x = x[valid]
            y = y[valid]
            z = z[valid]

            # Run method
            method = self.method_var.get()
            # Create grid (needed for IDW)
            grid_size = self.grid_size_var.get()
            x_min, x_max = x.min(), x.max()
            y_min, y_max = y.min(), y.max()
            xi = np.linspace(x_min, x_max, grid_size)
            yi = np.linspace(y_min, y_max, grid_size)
            XI, YI = np.meshgrid(xi, yi)
            if "Kriging" in method:
                result = self._run_optimized_kriging(x, y, z, lon_col, lat_col, value_col)
            else:
                # IDW
                result = self._run_optimized_idw(x, y, z, XI, YI, lon_col, lat_col, value_col)

            if self.cancelled:
                return

            # Update UI
            self.window.after(0, lambda: self._update_interpolation_results(result))

        except Exception as e:
            if not self.cancelled:
                self.window.after(0, lambda: messagebox.showerror("Error", f"Failed: {str(e)}"))
        finally:
            self.window.after(0, self._reset_processing_ui)

    def _run_density(self):
        """Run density contour generation (from interactive_contouring)"""
        try:
            x_col = self.density_x_var.get()
            y_col = self.density_y_var.get()

            # Get column data with flexible matching
            x_data, x_label = self._get_column_data(x_col)
            y_data, y_label = self._get_column_data(y_col)

            # Remove NaN values
            valid_mask = ~(pd.isna(x_data) | pd.isna(y_data))
            x_clean = x_data[valid_mask]
            y_clean = y_data[valid_mask]

            self._update_progress(20, f"Generating with {len(x_clean)} points...")

            # Generate based on method
            method = self.density_method_var.get()
            if method == "Gaussian KDE":
                result = self._generate_kde(x_clean, y_clean, x_label, y_label)
            elif method == "2D Histogram":
                result = self._generate_histogram(x_clean, y_clean, x_label, y_label)
            else:
                result = self._generate_distance(x_clean, y_clean, x_label, y_label)

            if self.cancelled:
                return

            # Update UI
            self.window.after(0, lambda: self._update_density_results(result))

        except Exception as e:
            if not self.cancelled:
                self.window.after(0, lambda: messagebox.showerror("Error", f"Density failed: {str(e)}"))
        finally:
            self.window.after(0, self._reset_processing_ui)

    def _generate_kde(self, x_data, y_data, x_label, y_label):
        """Generate Gaussian KDE contours (from interactive_contouring)"""
        self._update_progress(30, "Computing KDE...")

        # Prepare data
        values = np.vstack([x_data, y_data])

        # Set bandwidth
        bw = self.bw_var.get()
        if bw in ["scott", "silverman"]:
            bandwidth = bw
        else:
            try:
                bandwidth = float(bw)
            except:
                bandwidth = "scott"

        # Create KDE
        try:
            kde = gaussian_kde(values, bw_method=bandwidth)
        except:
            kde = gaussian_kde(values)

        # Create grid
        grid_size = self.density_grid_var.get()
        x_min, x_max = x_data.min(), x_data.max()
        y_min, y_max = y_data.min(), y_data.max()

        # Add padding
        x_pad = (x_max - x_min) * 0.1
        y_pad = (y_max - y_min) * 0.1

        x_grid = np.linspace(x_min - x_pad, x_max + x_pad, grid_size)
        y_grid = np.linspace(y_min - y_pad, y_max + y_pad, grid_size)
        X, Y = np.meshgrid(x_grid, y_grid)

        self._update_progress(60, "Evaluating density...")

        # Evaluate
        positions = np.vstack([X.ravel(), Y.ravel()])
        Z = kde(positions).reshape(X.shape)

        return {
            'X': X, 'Y': Y, 'Z': Z,
            'x_data': x_data, 'y_data': y_data,
            'x_label': x_label, 'y_label': y_label,
            'method': 'Gaussian KDE'
        }

    def _generate_histogram(self, x_data, y_data, x_label, y_label):
        """Generate 2D histogram contours (from interactive_contouring)"""
        self._update_progress(30, "Creating 2D histogram...")

        grid_size = self.density_grid_var.get()

        # Create histogram
        H, x_edges, y_edges = np.histogram2d(x_data, y_data, bins=grid_size)

        self._update_progress(60, "Smoothing...")

        # Smooth
        H_smooth = gaussian_filter(H.T, sigma=1.0)

        # Create grid
        X, Y = np.meshgrid(x_edges[:-1], y_edges[:-1])
        Z = H_smooth

        return {
            'X': X, 'Y': Y, 'Z': Z,
            'x_data': x_data, 'y_data': y_data,
            'x_label': x_label, 'y_label': y_label,
            'method': '2D Histogram'
        }

    def _generate_distance(self, x_data, y_data, x_label, y_label):
        """Generate distance-based contours (from interactive_contouring)"""
        self._update_progress(30, "Computing distance-based density...")

        grid_size = self.density_grid_var.get()

        # Create grid
        x_min, x_max = x_data.min(), x_data.max()
        y_min, y_max = y_data.min(), y_data.max()
        x_pad = (x_max - x_min) * 0.1
        y_pad = (y_max - y_min) * 0.1

        x_grid = np.linspace(x_min - x_pad, x_max + x_pad, grid_size)
        y_grid = np.linspace(y_min - y_pad, y_max + y_pad, grid_size)
        X, Y = np.meshgrid(x_grid, y_grid)

        # Distance-based density
        Z = np.zeros_like(X)
        for i in range(len(x_data)):
            if i % 100 == 0:
                self._update_progress(50 + int(40 * i / len(x_data)), f"Processing point {i}/{len(x_data)}")
            dist = np.sqrt((X - x_data[i])**2 + (Y - y_data[i])**2)
            Z += np.exp(-dist**2 / (2 * (x_pad/2)**2))

        # Normalize
        Z = Z / Z.max() if Z.max() > 0 else Z

        return {
            'X': X, 'Y': Y, 'Z': Z,
            'x_data': x_data, 'y_data': y_data,
            'x_label': x_label, 'y_label': y_label,
            'method': 'Distance-based'
        }

    def _run_optimized_idw(self, x, y, z, X_grid, Y_grid, x_label, y_label, z_label):
        """Optimized Inverse Distance Weighting interpolation"""
        self._update_progress(10, "Creating grid...")

        # Get parameters
        power = self.idw_power_var.get()
        min_neighbors = self.min_neighbors_var.get()
        search_radius = self.search_radius_var.get()

        self._update_progress(30, "Building search tree...")

        # Build KD-tree for fast searches
        tree = cKDTree(np.column_stack([x, y]))

        self._update_progress(50, "Performing IDW interpolation...")

        # Initialize grid
        grid_y, grid_x = X_grid.shape
        ZI = np.full((grid_y, grid_x), np.nan)

        # Process grid points
        total_points = grid_x * grid_y
        processed = 0

        for i in range(grid_y):
            for j in range(grid_x):
                if self.cancelled:
                    return None

                # Find nearest neighbors
                point = np.array([[X_grid[i, j], Y_grid[i, j]]])
                distances, indices = tree.query(point,
                                               k=min(15, len(x)),
                                               distance_upper_bound=search_radius)

                # Get valid neighbors
                valid = distances[0] < np.inf
                if np.sum(valid) >= min_neighbors:
                    z_near = z[indices[0][valid]]
                    d_near = distances[0][valid]

                    # IDW weights
                    weights = 1.0 / (d_near**power + 1e-10)
                    ZI[i, j] = np.sum(weights * z_near) / np.sum(weights)

                processed += 1
                if processed % 100 == 0:
                    progress = 50 + 45 * (processed / total_points)
                    self._update_progress(int(progress), f"Processed {processed}/{total_points}")

        self._update_progress(95, "Finalizing...")

        return {
            'X': X_grid, 'Y': Y_grid, 'Z': ZI,
            'x_samples': x, 'y_samples': y, 'z_samples': z,
            'x_label': x_label, 'y_label': y_label, 'z_label': z_label,
            'method': 'Inverse Distance Weighting',
            'params': f'power={power}, search_radius={search_radius}'
        }

    def _run_optimized_kriging(self, x, y, z, x_label, y_label, z_label):
        """Optimized Ordinary Kriging implementation"""
        self._update_progress(10, "Calculating variogram...")

        # Calculate experimental variogram
        coords = np.column_stack([x, y])
        distances = pdist(coords)
        z_diff = pdist(z[:, None], metric=lambda u, v: 0.5 * (u - v)**2)

        # Bin distances
        max_dist = np.max(distances)
        n_bins = 15
        bin_edges = np.linspace(0, max_dist, n_bins + 1)

        exp_gamma = np.zeros(n_bins)
        exp_h = np.zeros(n_bins)

        for i in range(n_bins):
            mask = (distances >= bin_edges[i]) & (distances < bin_edges[i + 1])
            if np.sum(mask) > 0:
                exp_gamma[i] = np.mean(z_diff[mask])
                exp_h[i] = np.mean(distances[mask])

        # Remove empty bins
        valid = exp_h > 0
        exp_h = exp_h[valid]
        exp_gamma = exp_gamma[valid]

        if self.cancelled:
            return None

        self._update_progress(30, "Fitting variogram...")

        # Fit variogram if auto-fit enabled
        if self.auto_fit_var.get() and len(exp_h) > 3:
            try:
                nugget_fit, sill_fit, range_fit = self._fit_variogram(exp_h, exp_gamma)
                self.nugget_var.set(round(nugget_fit, 3))
                self.sill_var.set(round(sill_fit, 3))
                self.range_var.set(round(range_fit, 2))
            except:
                nugget_fit = self.nugget_var.get()
                sill_fit = self.sill_var.get()
                range_fit = self.range_var.get()
        else:
            nugget_fit = self.nugget_var.get()
            sill_fit = self.sill_var.get()
            range_fit = self.range_var.get()

        if self.cancelled:
            return None

        self._update_progress(50, "Creating grid...")

        # Create grid with aspect ratio preservation
        grid_x = self.grid_size_var.get()
        if self.preserve_aspect_var.get() and hasattr(self, 'aspect_ratio') and self.aspect_ratio > 0:
            grid_y = int(grid_x / self.aspect_ratio)
            if grid_y < 20:  # Minimum grid size
                grid_y = 20
            elif grid_y > 200:  # Maximum grid size
                grid_y = 200
        else:
            grid_y = grid_x

        x_min, x_max = x.min(), x.max()
        y_min, y_max = y.min(), y.max()

        # Add padding
        x_pad = (x_max - x_min) * 0.05
        y_pad = (y_max - y_min) * 0.05

        xi = np.linspace(x_min - x_pad, x_max + x_pad, grid_x)
        yi = np.linspace(y_min - y_pad, y_max + y_pad, grid_y)
        XI, YI = np.meshgrid(xi, yi)

        self._update_progress(60, "Building search tree...")

        # Build KD-tree for fast searches
        tree = cKDTree(np.column_stack([x, y]))

        # Search radius
        search_radius = range_fit * 2.0
        min_neighbors = self.min_neighbors_var.get()

        self._update_progress(70, "Performing kriging...")

        # Process in blocks for optimization
        ZI = np.full((grid_y, grid_x), np.nan)
        block_size = 20

        for i in range(0, grid_y, block_size):
            for j in range(0, grid_x, block_size):
                if self.cancelled:
                    return None

                # Get block bounds
                i_end = min(i + block_size, grid_y)
                j_end = min(j + block_size, grid_x)

                # Get all grid points in block
                block_points = []
                for ii in range(i, i_end):
                    for jj in range(j, j_end):
                        block_points.append([XI[ii, jj], YI[ii, jj]])

                if not block_points:
                    continue

                block_points = np.array(block_points)

                # Find neighbors for all points in block
                distances, indices = tree.query(block_points,
                                               k=min(15, len(x)),
                                               distance_upper_bound=search_radius)

                # Process each point in block
                point_idx = 0
                for ii in range(i, i_end):
                    for jj in range(j, j_end):
                        dist = distances[point_idx]
                        idx = indices[point_idx]
                        valid = dist < np.inf

                        if np.sum(valid) >= min_neighbors:
                            # Get valid neighbors
                            x_near = x[idx[valid]]
                            y_near = y[idx[valid]]
                            z_near = z[idx[valid]]
                            d_near = dist[valid]

                            # Kriging interpolation
                            ZI[ii, jj] = self._kriging_point(x_near, y_near, z_near, d_near,
                                                            nugget_fit, sill_fit, range_fit)

                        point_idx += 1

                # Update progress
                progress = 70 + 25 * ((i * grid_x + j) / (grid_y * grid_x))
                self._update_progress(int(progress), f"Processing block {i//block_size + 1}/{grid_y//block_size + 1}")

        self._update_progress(95, "Finalizing...")

        return {
            'X': XI, 'Y': YI, 'Z': ZI,
            'x_samples': x, 'y_samples': y, 'z_samples': z,
            'x_label': x_label, 'y_label': y_label, 'z_label': z_label,
            'method': 'Ordinary Kriging',
            'variogram': {
                'model': self.variogram_var.get(),
                'nugget': nugget_fit,
                'sill': sill_fit,
                'range': range_fit
            },
            'experimental_h': exp_h,
            'experimental_gamma': exp_gamma
        }

    def _fit_variogram(self, h, gamma):
        """Fit variogram model to experimental data"""
        model = self.variogram_var.get()

        if model == "Spherical":
            def func(h, nugget, sill, range_val):
                h = np.asarray(h)
                gamma = np.full_like(h, nugget + sill)
                mask = h <= range_val
                gamma[mask] = nugget + sill * (1.5 * (h[mask]/range_val) - 0.5 * (h[mask]/range_val)**3)
                return gamma
        elif model == "Exponential":
            def func(h, nugget, sill, range_val):
                return nugget + sill * (1 - np.exp(-3 * h / range_val))
        else:  # Gaussian
            def func(h, nugget, sill, range_val):
                return nugget + sill * (1 - np.exp(-3 * (h / range_val)**2))

        # Initial guess
        p0 = [np.min(gamma), np.max(gamma) - np.min(gamma), np.max(h)/2]
        bounds = ([0, 0, 0], [np.inf, np.inf, np.max(h)])

        try:
            popt, _ = curve_fit(func, h, gamma, p0=p0, bounds=bounds, maxfev=5000)
            return popt
        except:
            return p0

    def _kriging_point(self, x_near, y_near, z_near, d_near, nugget, sill, range_val):
        """Kriging interpolation for a single point"""
        n = len(x_near)

        # Create kriging matrix
        C = np.zeros((n + 1, n + 1))

        # Calculate distances between samples
        for k in range(n):
            for l in range(n):
                dist = np.sqrt((x_near[k] - x_near[l])**2 + (y_near[k] - y_near[l])**2)
                h = dist / range_val
                if h <= 1:
                    C[k, l] = nugget + sill * (1.5 * h - 0.5 * h**3)
                else:
                    C[k, l] = nugget + sill

        # Lagrange multiplier
        C[:n, n] = 1
        C[n, :n] = 1

        # Right-hand side
        b = np.zeros(n + 1)
        h_near = d_near / range_val
        mask = h_near <= 1
        b[:n][mask] = nugget + sill * (1.5 * h_near[mask] - 0.5 * h_near[mask]**3)
        b[:n][~mask] = nugget + sill
        b[n] = 1

        try:
            weights = solve(C, b)
            return np.sum(weights[:n] * z_near)
        except:
            # Fallback to IDW
            weights = 1.0 / (d_near**2 + 1e-10)
            return np.sum(weights * z_near) / np.sum(weights)

    def _update_progress(self, value, message):
        """Update progress bar and label"""
        if not self.cancelled:
            self.window.after(0, lambda: self.progress.configure(value=value))
            self.window.after(0, lambda: self.status_label.config(text=message, fg="orange"))

    def _update_interpolation_results(self, result):
        """Update UI with interpolation results"""
        if result is None or self.cancelled:
            return

        self.interpolation_result = result  # Store result

        # Update map
        self._update_map(result)

        # Update variogram plot
        if 'experimental_h' in result:
            self._update_variogram_plot(result)

        # Update statistics
        self._update_statistics(result)

        self.status_label.config(text=f"Completed {result['method']}", fg="green")
        self.notebook.select(0)

        # Log
        self._log(f"[{datetime.now().strftime('%H:%M:%S')}] Completed {result['method']}")

    def _update_density_results(self, result):
        """Update UI with density results"""
        if result is None or self.cancelled:
            return

        self.density_result = result  # Store result

        # Update density plot
        self._update_density_plot(result)

        self.status_label.config(text=f"Completed {result['method']}", fg="green")
        self.notebook.select(3)  # Density tab index

        # Log
        self._log(f"[{datetime.now().strftime('%H:%M:%S')}] Generated {result['method']}: {result['x_label']} vs {result['y_label']}")

    def _update_map(self, result):
        """Update the interpolation map"""
        self.ax.clear()

        X = result['X']
        Y = result['Y']
        Z = result['Z']
        x_samples = result['x_samples']
        y_samples = result['y_samples']
        z_samples = result['z_samples']
        x_label = result['x_label']
        y_label = result['y_label']
        z_label = result['z_label']
        method = result['method']

        # Plot interpolation
        cmap = self.cmap_var.get()
        im = self.ax.imshow(Z, extent=[X.min(), X.max(), Y.min(), Y.max()],
                           origin='lower', cmap=cmap, alpha=0.8, aspect='auto')

        if self.show_samples_var.get():
            scatter = self.ax.scatter(x_samples, y_samples, c=z_samples,
                           cmap=cmap, edgecolor='black', s=30, alpha=0.8)

        self.figure.colorbar(im, ax=self.ax, label=z_label)

        self.ax.set_xlabel(x_label)
        self.ax.set_ylabel(y_label)
        self.ax.set_title(f"{method}: {z_label}")
        self.ax.grid(True, alpha=0.3)

        self.figure.tight_layout()
        self.canvas.draw()

    def _update_density_plot(self, result):
        """Update the density contour plot (from interactive_contouring)"""
        self.density_ax.clear()

        X = result['X']
        Y = result['Y']
        Z = result['Z']
        x_data = result['x_data']
        y_data = result['y_data']
        x_label = result['x_label']
        y_label = result['y_label']
        method = result['method']

        # Create contours
        levels = self.levels_var.get()
        cmap = self.density_cmap_var.get()

        if self.fill_contours_var.get():
            contour = self.density_ax.contourf(X, Y, Z, levels=levels, cmap=cmap, alpha=0.8)
        else:
            contour = self.density_ax.contour(X, Y, Z, levels=levels, cmap=cmap, linewidths=2)

        # Colorbar
        if self.show_colorbar_var.get():
            self.density_figure.colorbar(contour, ax=self.density_ax, label='Density')

        # Data points
        if self.show_points_var.get():
            self.density_ax.scatter(x_data, y_data, c='white', edgecolor='black',
                          alpha=0.6, s=30, label='Data Points')

        # Labels and title
        self.density_ax.set_xlabel(x_label, fontsize=10)
        self.density_ax.set_ylabel(y_label, fontsize=10)
        self.density_ax.set_title(f"{method}: {x_label} vs {y_label}\n{len(x_data)} points", fontsize=10)

        # Grid and legend
        self.density_ax.grid(True, alpha=0.3)
        if self.show_points_var.get():
            self.density_ax.legend()

        # Redraw
        self.density_figure.tight_layout()
        self.density_canvas.draw()

    def _update_variogram_plot(self, result):
        """Update variogram plot"""
        self.vario_ax.clear()

        if 'experimental_h' in result and 'experimental_gamma' in result:
            h = result['experimental_h']
            gamma = result['experimental_gamma']
            vario = result['variogram']

            self.vario_ax.scatter(h, gamma, color='blue', s=20, label='Experimental')

            # Plot fitted model
            h_model = np.linspace(0, np.max(h) * 1.2, 100)
            model = vario['model']
            nugget = vario['nugget']
            sill = vario['sill']
            range_val = vario['range']

            if model == "Spherical":
                mask = h_model <= range_val
                gamma_model = np.full_like(h_model, nugget + sill)
                gamma_model[mask] = nugget + sill * (1.5 * (h_model[mask]/range_val) - 0.5 * (h_model[mask]/range_val)**3)
            elif model == "Exponential":
                gamma_model = nugget + sill * (1 - np.exp(-3 * h_model / range_val))
            else:  # Gaussian
                gamma_model = nugget + sill * (1 - np.exp(-3 * (h_model / range_val)**2))

            self.vario_ax.plot(h_model, gamma_model, 'r-', linewidth=2, label='Fitted')

            self.vario_ax.set_xlabel('Distance (h)')
            self.vario_ax.set_ylabel('Semivariance γ(h)')
            self.vario_ax.set_title(f'Variogram: {model} model')
            self.vario_ax.legend()
            self.vario_ax.grid(True, alpha=0.3)

        self.vario_figure.tight_layout()
        self.vario_canvas.draw()

    def _update_statistics(self, result):
        """Update statistics display"""
        z_samples = result['z_samples']
        Z = result['Z']
        z_label = result['z_label']

        stats = f"STATISTICS: {z_label}\n"
        stats += "=" * 40 + "\n\n"
        stats += f"Method: {result['method']}\n"
        stats += f"Samples: {len(z_samples)}\n"
        stats += f"Grid: {Z.shape[1]}×{Z.shape[0]}\n\n"

        stats += f"SAMPLE DATA:\n"
        stats += f"  Mean: {np.mean(z_samples):.3f}\n"
        stats += f"  Std: {np.std(z_samples):.3f}\n"
        stats += f"  Min: {np.min(z_samples):.3f}\n"
        stats += f"  Max: {np.max(z_samples):.3f}\n\n"

        stats += f"INTERPOLATED GRID:\n"
        stats += f"  Mean: {np.nanmean(Z):.3f}\n"
        stats += f"  Std: {np.nanstd(Z):.3f}\n"
        stats += f"  Min: {np.nanmin(Z):.3f}\n"
        stats += f"  Max: {np.nanmax(Z):.3f}\n"

        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats)

    def _reset_processing_ui(self):
        """Reset UI after processing"""
        self.is_processing = False
        self.interpolate_btn.config(state=tk.NORMAL, text="📍 Run Interp")
        self.density_btn.config(state=tk.NORMAL, text="🗺️ Run Density")
        self.progress['value'] = 0

    def _log(self, message):
        """Add message to log"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def _import_from_main(self):
        """Import data from main app into plugin for analysis"""
        if not hasattr(self.app, 'samples') or not self.app.samples:
            messagebox.showwarning("No Data", "No data in main application!")
            return

        try:
            # Convert main app samples to DataFrame
            self.df = pd.DataFrame(self.app.samples)

            sample_count = len(self.df)
            self.status_label.config(text=f"✅ Imported {sample_count} samples from main app", fg="green")

            # Update data info
            self.data_info_label.config(text=f"Samples: {sample_count}")

            # Convert numeric columns
            numeric_cols = []
            for col in self.df.columns:
                try:
                    self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
                    if not self.df[col].isna().all():
                        numeric_cols.append(col)
                except:
                    pass

            # Update all comboboxes with available columns
            all_columns = list(self.df.columns)

            # Interpolation combos
            self.lon_combo['values'] = all_columns
            self.lat_combo['values'] = all_columns
            self.value_combo['values'] = numeric_cols  # Only numeric for value

            # Density combos - include all columns + element suggestions
            density_options = list(set(all_columns[:20] + self.ELEMENT_SUGGESTIONS))
            self.density_x_combo['values'] = density_options
            self.density_y_combo['values'] = density_options

            # Auto-select first two numeric columns for density if empty
            if len(numeric_cols) > 0 and not self.density_x_var.get():
                self.density_x_var.set(numeric_cols[0])
            if len(numeric_cols) > 1 and not self.density_y_var.get():
                self.density_y_var.set(numeric_cols[1])

            # Auto-detect coordinate columns for interpolation
            for col in numeric_cols:
                col_lower = col.lower()
                if any(term in col_lower for term in ['lon', 'long', 'x', 'easting']):
                    if not self.lon_var.get():
                        self.lon_var.set(col)
                if any(term in col_lower for term in ['lat', 'y', 'northing']):
                    if not self.lat_var.get():
                        self.lat_var.set(col)

            # Auto-select first numeric column for value if not set
            if numeric_cols and not self.value_var.get():
                self.value_var.set(numeric_cols[0])

            # Calculate aspect ratio if both coordinates are selected
            if self.lon_var.get() and self.lat_var.get():
                lon_col = self.lon_var.get()
                lat_col = self.lat_var.get()

                if lon_col in self.df.columns and lat_col in self.df.columns:
                    valid = ~(self.df[lon_col].isna() | self.df[lat_col].isna())
                    if valid.sum() > 1:
                        x_vals = self.df[lon_col][valid].values
                        y_vals = self.df[lat_col][valid].values

                        x_range = x_vals.max() - x_vals.min()
                        y_range = y_vals.max() - y_vals.min()

                        if x_range > 0 and y_range > 0:
                            self.aspect_ratio = x_range / y_range
                            self.sample_coords = np.column_stack([x_vals, y_vals])

            # Enable buttons
            if self.lon_var.get() and self.lat_var.get() and self.value_var.get():
                self.interpolate_btn.config(state=tk.NORMAL)

            if self.density_x_var.get() and self.density_y_var.get():
                self.density_btn.config(state=tk.NORMAL)

            # Log the import
            self._log(f"[{datetime.now().strftime('%H:%M:%S')}] Imported {sample_count} samples from main app")

            # Show success
            messagebox.showinfo("Success", f"✅ Imported {sample_count} samples from main app")

        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Failed to import data:\n{str(e)}")

    def _export_results(self):
        """Export results"""
        if not hasattr(self, 'figure'):
            messagebox.showwarning("No Results", "Run analysis first!")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[
                ("PNG files", "*.png"),
                ("PDF files", "*.pdf")
            ]
        )

        if filename:
            try:
                # Export current tab
                current_tab = self.notebook.index(self.notebook.select())
                if current_tab == 0:  # Map tab
                    self.figure.savefig(filename, dpi=300, bbox_inches='tight')
                elif current_tab == 1:  # Variogram tab
                    self.vario_figure.savefig(filename, dpi=300, bbox_inches='tight')
                elif current_tab == 3:  # Density tab
                    self.density_figure.savefig(filename, dpi=300, bbox_inches='tight')

                messagebox.showinfo("Success", f"Exported to:\n{filename}")
                self._log(f"[{datetime.now().strftime('%H:%M:%S')}] Exported: {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Export failed: {str(e)}")

def setup_plugin(main_app):
    """Plugin setup"""
    plugin = SpatialKrigingPlugin(main_app)
    return plugin
