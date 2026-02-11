"""
Spatial Interpolation & Kriging Plugin
Professional geostatistical interpolation with optimized performance
"""

PLUGIN_INFO = {
    "category": "software",
    "id": "spatial_kriging",
    "name": "Spatial Kriging",
    "description": "Industry-standard spatial interpolation with variogram analysis",
    "icon": "📍",
    "version": "3.1",
    "requires": ["numpy", "scipy", "matplotlib"],
    "author": "Sefy Levy & DeepSeek",

    "item": {
        "type": "plugin",
        "subtype": "spatial_analysis",
        "tags": ["kriging", "geostatistics", "variogram", "provenance"],
        "compatibility": ["main_app_v2+"],
        "dependencies": ["numpy>=1.19.0", "scipy>=1.6.0", "matplotlib>=3.3.0"],
        "settings": {
            "default_method": "ordinary_kriging",
            "auto_fit_variogram": True
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

        # Industry-standard methods
        self.INTERPOLATION_METHODS = {
            "Ordinary Kriging": "Best linear unbiased estimator with variogram",
            "Inverse Distance Weighting": "Distance-weighted average"
        }

        # Variogram models
        self.VARIOGRAM_MODELS = {
            "Spherical": "γ(h) = n + s * (1.5*(h/a) - 0.5*(h/a)³) for h ≤ a, else n + s",
            "Exponential": "γ(h) = n + s * (1 - exp(-3h/a))",
            "Gaussian": "γ(h) = n + s * (1 - exp(-3h²/a²))"
        }

        # Color maps
        self.COLORMAPS = ["viridis", "plasma", "YlOrRd", "RdYlBu", "Spectral"]

        # Default parameters
        self.DEFAULT_PARAMS = {
            "idw_power": 2.0,
            "search_radius": 200.0,
            "min_neighbors": 5,
            "sill": 1.0,
            "range_val": 100.0,
            "nugget": 0.1
        }

    def open_window(self):
        """Open compact main window"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title(f"{PLUGIN_INFO['icon']} {PLUGIN_INFO['name']} v{PLUGIN_INFO['version']}")
        self.window.geometry("1150x700")
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

        self._create_ui()

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
        """Create compact user interface"""
        # Header
        header = tk.Frame(self.window, bg="#2c3e50")
        header.pack(fill=tk.X)
        tk.Label(header, text="📍 Professional Spatial Interpolation",
                font=("Arial", 14, "bold"),
                bg="#2c3e50", fg="white", pady=10).pack()

        # Main container
        main_paned = tk.PanedWindow(self.window, orient=tk.HORIZONTAL, sashwidth=6)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)

        # Left panel
        left_panel = tk.Frame(main_paned, bg="#ecf0f1", relief=tk.RAISED, borderwidth=1)
        main_paned.add(left_panel, minsize=360)

        # Right panel
        right_panel = tk.Frame(main_paned, bg="white")
        main_paned.add(right_panel, minsize=750)

        self._setup_left_panel(left_panel)
        self._setup_right_panel(right_panel)

    def _setup_left_panel(self, parent):
        """Setup compact control panel"""
        # Data info
        info_frame = tk.LabelFrame(parent, text="📊 Data", padx=8, pady=8, bg="#ecf0f1")
        info_frame.pack(fill=tk.X, padx=8, pady=8)

        self.data_info_label = tk.Label(info_frame, text="No data loaded", bg="#ecf0f1", font=("Arial", 9))
        self.data_info_label.pack(anchor=tk.W)

        # Coordinate selection
        coord_frame = tk.LabelFrame(parent, text="🌍 Coordinates", padx=8, pady=8, bg="#ecf0f1")
        coord_frame.pack(fill=tk.X, padx=8, pady=8)

        tk.Label(coord_frame, text="X column:", bg="#ecf0f1", font=("Arial", 9)).grid(row=0, column=0, sticky=tk.W, pady=3)
        self.lon_var = tk.StringVar(value="")
        self.lon_combo = ttk.Combobox(coord_frame, textvariable=self.lon_var, width=18, font=("Arial", 9))
        self.lon_combo.grid(row=0, column=1, padx=3, pady=3)

        tk.Label(coord_frame, text="Y column:", bg="#ecf0f1", font=("Arial", 9)).grid(row=1, column=0, sticky=tk.W, pady=3)
        self.lat_var = tk.StringVar(value="")
        self.lat_combo = ttk.Combobox(coord_frame, textvariable=self.lat_var, width=18, font=("Arial", 9))
        self.lat_combo.grid(row=1, column=1, padx=3, pady=3)

        tk.Label(coord_frame, text="Value column:", bg="#ecf0f1", font=("Arial", 9)).grid(row=2, column=0, sticky=tk.W, pady=3)
        self.value_var = tk.StringVar(value="")
        self.value_combo = ttk.Combobox(coord_frame, textvariable=self.value_var, width=18, font=("Arial", 9))
        self.value_combo.grid(row=2, column=1, padx=3, pady=3)

        # Method selection
        method_frame = tk.LabelFrame(parent, text="🔄 Method", padx=8, pady=8, bg="#ecf0f1")
        method_frame.pack(fill=tk.X, padx=8, pady=8)

        self.method_var = tk.StringVar(value="Ordinary Kriging")
        for method in self.INTERPOLATION_METHODS.keys():
            tk.Radiobutton(method_frame, text=method, variable=self.method_var,
                          value=method, bg="#ecf0f1", font=("Arial", 9),
                          command=self._update_method_params).pack(anchor=tk.W, pady=1)

        # Parameters frame
        self.params_frame = tk.LabelFrame(parent, text="⚙️ Parameters", padx=8, pady=8, bg="#ecf0f1")
        self.params_frame.pack(fill=tk.X, padx=8, pady=8)
        self._setup_kriging_params()

        # Grid settings
        grid_frame = tk.LabelFrame(parent, text="📐 Grid", padx=8, pady=8, bg="#ecf0f1")
        grid_frame.pack(fill=tk.X, padx=8, pady=8)

        tk.Label(grid_frame, text="Grid cells:", bg="#ecf0f1", font=("Arial", 9)).grid(row=0, column=0, sticky=tk.W, pady=3)
        self.grid_size_var = tk.IntVar(value=80)
        tk.Spinbox(grid_frame, from_=30, to=200, textvariable=self.grid_size_var,
                  width=10, font=("Arial", 9)).grid(row=0, column=1, padx=3, pady=3)

        # Aspect ratio checkbox
        self.preserve_aspect_var = tk.BooleanVar(value=True)
        tk.Checkbutton(grid_frame, text="Preserve aspect ratio",
                      variable=self.preserve_aspect_var, bg="#ecf0f1", font=("Arial", 9)
                      ).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=3)

        tk.Label(grid_frame, text="Color map:", bg="#ecf0f1", font=("Arial", 9)).grid(row=2, column=0, sticky=tk.W, pady=3)
        self.cmap_var = tk.StringVar(value="viridis")
        ttk.Combobox(grid_frame, textvariable=self.cmap_var,
                    values=self.COLORMAPS, width=12, font=("Arial", 9)).grid(row=2, column=1, padx=3, pady=3)

        # Options
        options_frame = tk.Frame(parent, bg="#ecf0f1")
        options_frame.pack(fill=tk.X, padx=8, pady=8)

        self.show_samples_var = tk.BooleanVar(value=True)
        tk.Checkbutton(options_frame, text="Show points", variable=self.show_samples_var,
                      bg="#ecf0f1", font=("Arial", 9)).pack(side=tk.LEFT, padx=3)

        self.auto_fit_var = tk.BooleanVar(value=True)
        tk.Checkbutton(options_frame, text="Auto-fit", variable=self.auto_fit_var,
                      bg="#ecf0f1", font=("Arial", 9)).pack(side=tk.LEFT, padx=3)

        # Buttons
        button_frame = tk.Frame(parent, bg="#ecf0f1", pady=8)
        button_frame.pack(fill=tk.X, padx=8)

        row1_frame = tk.Frame(button_frame, bg="#ecf0f1")
        row1_frame.pack(fill=tk.X, pady=2)

        self.load_btn = tk.Button(row1_frame, text="📥 Load", bg="#3498db", fg="white",
                                 width=10, font=("Arial", 9), command=self._load_data)
        self.load_btn.pack(side=tk.LEFT, padx=2)

        self.interpolate_btn = tk.Button(row1_frame, text="📍 Run", bg="#9b59b6", fg="white",
                                        width=10, font=("Arial", 9), command=self._start_interpolation)
        self.interpolate_btn.pack(side=tk.LEFT, padx=2)

        row2_frame = tk.Frame(button_frame, bg="#ecf0f1")
        row2_frame.pack(fill=tk.X, pady=2)

        self.export_btn = tk.Button(row2_frame, text="💾 Export", bg="#2ecc71", fg="white",
                                   width=10, font=("Arial", 9), command=self._export_results)
        self.export_btn.pack(side=tk.LEFT, padx=2)

        self.import_btn = tk.Button(row2_frame, text="📤 Import", bg="#e67e22", fg="white",
                                   width=10, font=("Arial", 9), command=self._safe_import)
        self.import_btn.pack(side=tk.LEFT, padx=2)

        # Status
        self.status_label = tk.Label(parent, text="Ready", bg="#ecf0f1",
                                    fg="#7f8c8d", font=("Arial", 9))
        self.status_label.pack(fill=tk.X, padx=8, pady=(8, 3))

        # Progress
        self.progress = ttk.Progressbar(parent, mode='determinate', length=100)
        self.progress.pack(fill=tk.X, padx=8, pady=3)

    def _setup_kriging_params(self):
        """Setup kriging parameters"""
        for widget in self.params_frame.winfo_children():
            widget.destroy()

        tk.Label(self.params_frame, text="Model:", bg="#ecf0f1", font=("Arial", 9)).grid(row=0, column=0, sticky=tk.W, pady=2)
        self.variogram_var = tk.StringVar(value="Spherical")
        ttk.Combobox(self.params_frame, textvariable=self.variogram_var,
                    values=list(self.VARIOGRAM_MODELS.keys()), width=12, font=("Arial", 9)).grid(row=0, column=1, padx=3, pady=2)

        tk.Label(self.params_frame, text="Nugget:", bg="#ecf0f1", font=("Arial", 9)).grid(row=1, column=0, sticky=tk.W, pady=2)
        self.nugget_var = tk.DoubleVar(value=self.DEFAULT_PARAMS["nugget"])
        tk.Spinbox(self.params_frame, from_=0.0, to=10.0, increment=0.1,
                  textvariable=self.nugget_var, width=10, font=("Arial", 9)).grid(row=1, column=1, padx=3, pady=2)

        tk.Label(self.params_frame, text="Sill:", bg="#ecf0f1", font=("Arial", 9)).grid(row=2, column=0, sticky=tk.W, pady=2)
        self.sill_var = tk.DoubleVar(value=self.DEFAULT_PARAMS["sill"])
        tk.Spinbox(self.params_frame, from_=0.01, to=100.0, increment=0.5,
                  textvariable=self.sill_var, width=10, font=("Arial", 9)).grid(row=2, column=1, padx=3, pady=2)

        tk.Label(self.params_frame, text="Range:", bg="#ecf0f1", font=("Arial", 9)).grid(row=3, column=0, sticky=tk.W, pady=2)
        self.range_var = tk.DoubleVar(value=self.DEFAULT_PARAMS["range_val"])
        tk.Spinbox(self.params_frame, from_=10.0, to=1000.0, increment=10.0,
                  textvariable=self.range_var, width=10, font=("Arial", 9)).grid(row=3, column=1, padx=3, pady=2)

        tk.Label(self.params_frame, text="Min neighbors:", bg="#ecf0f1", font=("Arial", 9)).grid(row=4, column=0, sticky=tk.W, pady=2)
        self.min_neighbors_var = tk.IntVar(value=self.DEFAULT_PARAMS["min_neighbors"])
        tk.Spinbox(self.params_frame, from_=1, to=20, textvariable=self.min_neighbors_var,
                  width=10, font=("Arial", 9)).grid(row=4, column=1, padx=3, pady=2)

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

    def _setup_right_panel(self, parent):
        """Setup results panel"""
        style = ttk.Style()
        style.configure("TNotebook.Tab", font=("Arial", 9))

        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)

        # Map tab
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

    def _load_data(self):
        """Load data from main app"""
        if not hasattr(self.app, 'samples') or not self.app.samples:
            messagebox.showwarning("No Data", "Load data in main app first!")
            return

        try:
            self.df = pd.DataFrame(self.app.samples)

            # Convert numeric columns
            numeric_cols = []
            for col in self.df.columns:
                if col not in ['Sample_ID', 'Notes']:
                    try:
                        self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
                        if not self.df[col].isna().all():
                            numeric_cols.append(col)
                    except:
                        pass

            # Update info
            sample_count = len(self.df)
            self.data_info_label.config(text=f"Samples: {sample_count}")

            # Auto-detect columns
            for col in numeric_cols:
                col_lower = col.lower()
                if any(term in col_lower for term in ['lon', 'long', 'x', 'easting']):
                    if not self.lon_var.get():
                        self.lon_var.set(col)
                if any(term in col_lower for term in ['lat', 'y', 'northing']):
                    if not self.lat_var.get():
                        self.lat_var.set(col)

            # Update comboboxes
            self.lon_combo['values'] = numeric_cols
            self.lat_combo['values'] = numeric_cols
            self.value_combo['values'] = numeric_cols[:10]

            if not self.value_var.get() and numeric_cols:
                self.value_var.set(numeric_cols[0])

            # Calculate aspect ratio for grid
            if self.lon_var.get() and self.lat_var.get():
                self.sample_coords = np.column_stack((
                    self.df[self.lon_var.get()].values,
                    self.df[self.lat_var.get()].values
                ))

                if lon_col in self.df.columns and lat_col in self.df.columns:
                    x_min, x_max = self.df[lon_col].min(), self.df[lon_col].max()
                    y_min, y_max = self.df[lat_col].min(), self.df[lat_col].max()

                    x_range = x_max - x_min
                    y_range = y_max - y_min

                    if x_range > 0 and y_range > 0:
                        self.aspect_ratio = x_range / y_range


            self.status_label.config(text=f"Loaded {sample_count} samples", fg="green")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load: {str(e)}")

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
        self.status_label.config(text="Starting...", fg="orange")

        thread = threading.Thread(target=self._run_interpolation, daemon=True)
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
                result = self._run_optimized_idw(XI, YI, z, lon_col, lat_col, value_col)

            if self.cancelled:
                return

            # Update UI
            self.window.after(0, lambda: self._update_results_ui(result))

        except Exception as e:
            if not self.cancelled:
                self.window.after(0, lambda: messagebox.showerror("Error", f"Failed: {str(e)}"))
        finally:
            self.window.after(0, self._reset_processing_ui)
        def _run_optimized_idw(self, x_grid, y_grid, values, power=2.0, max_distance=0.0, n_neighbors=12):
            """
            Optimized Inverse Distance Weighting (IDW) interpolation.
            Industry standard parameters + performance optimizations.

            Parameters:
            - x_grid, y_grid: meshgrid coordinates for output grid (np arrays)
            - values: array of known values at sample locations
            - power: distance weighting exponent (2.0 = standard, 1.0–3.0 common)
            - max_distance: cutoff radius (0 = no cutoff)
            - n_neighbors: max neighbors to consider (12–20 typical balance)

            Returns:
            - interpolated grid (same shape as x_grid/y_grid)
            """
            # Flatten grid for easier calculation
            grid_points = np.column_stack((x_grid.ravel(), y_grid.ravel()))

            # Build KD-tree once for fast neighbor search
            tree = cKDTree(self.sample_coords)

            # Query nearest neighbors for all grid points at once
            distances, indices = tree.query(grid_points, k=n_neighbors, distance_upper_bound=max_distance if max_distance > 0 else np.inf)

            # Prepare output array
            interpolated = np.full(grid_points.shape[0], np.nan)

            # IDW calculation per grid point
            for i in range(len(grid_points)):
                dists = distances[i]
                idxs = indices[i]

                # Remove invalid neighbors (distance = inf)
                valid_mask = np.isfinite(dists)
                if not np.any(valid_mask):
                    continue  # no neighbors within cutoff

                valid_dists = dists[valid_mask]
                valid_vals = values[idxs[valid_mask]]

                # Avoid division by zero
                weights = 1.0 / (valid_dists ** power + 1e-12)  # small epsilon

                # Weighted average
                interpolated[i] = np.sum(weights * valid_vals) / np.sum(weights)

            # Reshape back to grid
            return interpolated.reshape(x_grid.shape)

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

    def _run_optimized_idw(self, x, y, z, x_label, y_label, z_label):
        """COMPLETE Inverse Distance Weighting implementation"""
        self._update_progress(10, "Creating grid...")

        # Get parameters
        power = self.idw_power_var.get()
        min_neighbors = self.min_neighbors_var.get()
        search_radius = self.search_radius_var.get()

        # Create grid with aspect ratio preservation
        grid_x = self.grid_size_var.get()
        if self.preserve_aspect_var.get() and hasattr(self, 'aspect_ratio') and self.aspect_ratio > 0:
            grid_y = int(grid_x / self.aspect_ratio)
            if grid_y < 20:
                grid_y = 20
            elif grid_y > 200:
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

        self._update_progress(30, "Building search tree...")

        # Build KD-tree for fast searches
        tree = cKDTree(np.column_stack([x, y]))

        self._update_progress(50, "Performing IDW interpolation...")

        # Initialize grid
        ZI = np.full((grid_y, grid_x), np.nan)

        # Process grid points
        total_points = grid_x * grid_y
        processed = 0

        for i in range(grid_y):
            for j in range(grid_x):
                if self.cancelled:
                    return None

                # Find nearest neighbors
                point = np.array([[XI[i, j], YI[i, j]]])
                distances, indices = tree.query(point,
                                               k=min(10, len(x)),
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
            'X': XI, 'Y': YI, 'Z': ZI,
            'x_samples': x, 'y_samples': y, 'z_samples': z,
            'x_label': x_label, 'y_label': y_label, 'z_label': z_label,
            'method': 'Inverse Distance Weighting',
            'params': f'power={power}, search_radius={search_radius}'
        }

    def _update_progress(self, value, message):
        """Update progress bar and label"""
        if not self.cancelled:
            self.window.after(0, lambda: self.progress.configure(value=value))
            self.window.after(0, lambda: self.status_label.config(text=message, fg="orange"))

    def _update_results_ui(self, result):
        """Update UI with results"""
        if result is None or self.cancelled:
            return

        # Update map
        self._update_map(result)

        # Update variogram plot
        if 'experimental_h' in result:
            self._update_variogram_plot(result)

        # Update statistics
        self._update_statistics(result)

        self.status_label.config(text=f"Completed {result['method']}", fg="green")
        self.notebook.select(0)

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
            self.ax.scatter(x_samples, y_samples, c=z_samples,
                           cmap=cmap, edgecolor='black', s=30, alpha=0.8)

        self.figure.colorbar(im, ax=self.ax, label=z_label)

        self.ax.set_xlabel(x_label)
        self.ax.set_ylabel(y_label)
        self.ax.set_title(f"{method}: {z_label}")
        self.ax.grid(True, alpha=0.3)

        self.figure.tight_layout()
        self.canvas.draw()

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
        self.interpolate_btn.config(state=tk.NORMAL, text="📍 Run")
        self.progress['value'] = 0

    def _safe_import(self):
        """Safe import with options"""
        if self.df.empty:
            messagebox.showwarning("No Data", "Load data first!")
            return

        if not hasattr(self.app, 'samples'):
            messagebox.showerror("Error", "Main app not accessible")
            return

        if not self.app.samples:
            # No existing data
            self._import_replace()
        else:
            response = messagebox.askyesnocancel(
                "Import Options",
                "Existing data found:\n\n"
                "• Yes = Append to existing (preserve metadata)\n"
                "• No = Replace existing\n"
                "• Cancel = Do nothing"
            )

            if response is None:
                return
            elif response:
                self._import_append()
            else:
                self._import_replace()

    def _import_append(self):
        """Append data while preserving original metadata"""
        original_samples = self.app.samples.copy()
        interpolation_method = self.method_var.get()
        value_column = self.value_var.get()

        # Clear existing samples
        self.app.samples = original_samples

        # Add interpolated samples with metadata
        for idx, row in self.df.iterrows():
            sample = {}

            # Add all original data
            for col in self.df.columns:
                val = row[col]
                if not pd.isna(val):
                    sample[col] = str(val)

            # Add interpolation metadata WITHOUT overwriting Notes
            sample['Interpolation_Method'] = interpolation_method
            sample['Interpolated_Variable'] = value_column
            sample['Interpolation_Date'] = datetime.now().strftime("%Y-%m-%d")

            # Preserve original Sample_ID if it exists, otherwise create new
            if 'Sample_ID' in sample:
                original_id = sample['Sample_ID']
                sample['Sample_ID'] = f"{original_id}_INT{idx:03d}"
            else:
                sample['Sample_ID'] = f"INT_{len(self.app.samples):04d}"

            # Only add Notes if not already present
            if 'Notes' not in sample:
                sample['Notes'] = f"Spatial interpolation ({interpolation_method})"
            else:
                # Append to existing Notes
                existing_notes = sample['Notes']
                sample['Notes'] = f"{existing_notes} | Interp: {interpolation_method}"

            self.app.samples.append(sample)

        # Refresh main app
        if hasattr(self.app, 'refresh_tree'):
            self.app.refresh_tree()

        added_count = len(self.df)
        total_count = len(self.app.samples)
        messagebox.showinfo("Success", f"Appended {added_count} samples\nTotal: {total_count}")

    def _import_replace(self):
        """Replace data after confirmation"""
        if not messagebox.askyesno("Confirm Replace",
                                  f"Replace {len(self.app.samples)} existing samples?\n\n"
                                  "This cannot be undone!"):
            return

        interpolation_method = self.method_var.get()
        value_column = self.value_var.get()

        # Clear existing
        self.app.samples = []

        # Add interpolated samples with metadata
        for idx, row in self.df.iterrows():
            sample = {}

            # Add all data
            for col in self.df.columns:
                val = row[col]
                if not pd.isna(val):
                    sample[col] = str(val)

            # Add interpolation metadata
            sample['Interpolation_Method'] = interpolation_method
            sample['Interpolated_Variable'] = value_column
            sample['Interpolation_Date'] = datetime.now().strftime("%Y-%m-%d")

            # Create unique Sample_ID
            sample['Sample_ID'] = f"INT_{idx:04d}"

            # Add informative Notes
            sample['Notes'] = f"Spatial interpolation ({interpolation_method}) of {value_column}"

            self.app.samples.append(sample)

        # Refresh main app
        if hasattr(self.app, 'refresh_tree'):
            self.app.refresh_tree()

        messagebox.showinfo("Success", f"Imported {len(self.df)} interpolated samples")

    def _export_results(self):
        """Export results"""
        if not hasattr(self, 'figure'):
            messagebox.showwarning("No Results", "Run interpolation first!")
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
                self.figure.savefig(filename, dpi=300, bbox_inches='tight')
                messagebox.showinfo("Success", f"Exported to:\n{filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Export failed: {str(e)}")

def setup_plugin(main_app):
    """Plugin setup"""
    plugin = SpatialKrigingPlugin(main_app)

    if hasattr(main_app, 'menu_bar'):
        if not hasattr(main_app, 'advanced_menu'):
            main_app.advanced_menu = tk.Menu(main_app.menu_bar, tearoff=0)
            main_app.menu_bar.add_cascade(label="Advanced", menu=main_app.advanced_menu)

        main_app.advanced_menu.add_command(
            label=f"{PLUGIN_INFO['icon']} {PLUGIN_INFO['name']}",
            command=plugin.open_window
        )

    return plugin
