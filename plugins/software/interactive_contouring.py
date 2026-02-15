"""
Interactive Contouring & Density Estimation Plugin
KDE2D-based contouring for any geochemical data
"""

PLUGIN_INFO = {
    "category": "software",
    "id": "interactive_contouring",
    "name": "Interactive Contouring",
    "description": "Interactive contouring and density estimation for scatter plots",
    "icon": "🗺️",
    "version": "1.0",
    "requires": ["numpy", "scipy", "matplotlib"],
    "author": "Sefy Levy & DeepSeek",

    "item": {
        "type": "plugin",
        "subtype": "visualization",
        "tags": ["contouring", "density", "kde", "scatter"],
        "compatibility": ["main_app_v2+"],
        "dependencies": ["numpy>=1.19.0", "scipy>=1.6.0", "matplotlib>=3.3.0"],
        "settings": {
            "default_kde_bandwidth": "scott",
            "contour_levels": 8,
            "show_points": True
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
import warnings
warnings.filterwarnings('ignore')

class InteractiveContouringPlugin:
    def __init__(self, main_app):
        self.app = main_app
        self.window = None
        self.df = pd.DataFrame()
        self.is_processing = False
        self.progress = None

        # Common suggestions for geochemical elements
        self.ELEMENT_SUGGESTIONS = [
            "SiO2", "TiO2", "Al2O3", "Fe2O3", "MgO", "CaO", "Na2O", "K2O", "P2O5",
            "La", "Ce", "Nd", "Sm", "Eu", "Gd", "Yb", "Lu",
            "Rb", "Sr", "Ba", "Zr", "Nb", "Y", "Cr", "Ni", "V", "Sc"
        ]

        # Contouring methods
        self.CONTOUR_METHODS = {
            "Gaussian KDE": "Gaussian Kernel Density Estimation",
            "2D Histogram": "Histogram-based density estimation",
            "Distance-based": "Nearest neighbor density estimation"
        }

        # Color maps
        self.COLORMAPS = ["viridis", "plasma", "inferno", "magma", "cividis", "coolwarm", "RdYlBu", "Spectral"]

        # Bandwidth options
        self.BANDWIDTH_OPTIONS = ["scott", "silverman", "0.1", "0.2", "0.5", "1.0"]

    def open_window(self):
        """Open the main window"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title(f"{PLUGIN_INFO['icon']} {PLUGIN_INFO['name']} v{PLUGIN_INFO['version']}")
        self.window.geometry("1400x850")
        self._create_ui()

    def _create_ui(self):
        """Create the user interface"""
        # Header
        header = tk.Frame(self.window, bg="#2c3e50")
        header.pack(fill=tk.X)
        tk.Label(header, text="🗺️ Interactive Contouring & Density Estimation",
                font=("Arial", 16, "bold"),
                bg="#2c3e50", fg="white", pady=12).pack()

        # Main container with panes
        main_paned = tk.PanedWindow(self.window, orient=tk.HORIZONTAL, sashwidth=8)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left panel - Controls
        left_panel = tk.Frame(main_paned, bg="#ecf0f1", relief=tk.RAISED, borderwidth=1)
        main_paned.add(left_panel, minsize=400)

        # Right panel - Visualization
        right_panel = tk.Frame(main_paned, bg="white")
        main_paned.add(right_panel, minsize=900)

        self._setup_left_panel(left_panel)
        self._setup_right_panel(right_panel)

    def _setup_left_panel(self, parent):
        """Setup control panel"""
        # Data info
        info_frame = tk.LabelFrame(parent, text="📊 Data Info", padx=10, pady=10, bg="#ecf0f1")
        info_frame.pack(fill=tk.X, padx=10, pady=10)

        self.data_info_label = tk.Label(info_frame, text="No data loaded", bg="#ecf0f1")
        self.data_info_label.pack(anchor=tk.W)

        self.column_info_label = tk.Label(info_frame, text="Columns: 0", bg="#ecf0f1", fg="#7f8c8d")
        self.column_info_label.pack(anchor=tk.W)

        # Axis selection
        axis_frame = tk.LabelFrame(parent, text="🎯 Axis Selection", padx=10, pady=10, bg="#ecf0f1")
        axis_frame.pack(fill=tk.X, padx=10, pady=10)

        # X-axis
        tk.Label(axis_frame, text="X-axis (enter column name):", bg="#ecf0f1").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.x_var = tk.StringVar(value="")
        self.x_entry = ttk.Combobox(axis_frame, textvariable=self.x_var, values=self.ELEMENT_SUGGESTIONS, width=25)
        self.x_entry.grid(row=0, column=1, padx=5, pady=5)
        self.x_entry.config(state="normal")

        # Y-axis
        tk.Label(axis_frame, text="Y-axis (enter column name):", bg="#ecf0f1").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.y_var = tk.StringVar(value="")
        self.y_entry = ttk.Combobox(axis_frame, textvariable=self.y_var, values=self.ELEMENT_SUGGESTIONS, width=25)
        self.y_entry.grid(row=1, column=1, padx=5, pady=5)
        self.y_entry.config(state="normal")

        # Method selection
        method_frame = tk.LabelFrame(parent, text="🔄 Contouring Method", padx=10, pady=10, bg="#ecf0f1")
        method_frame.pack(fill=tk.X, padx=10, pady=10)

        self.method_var = tk.StringVar(value="Gaussian KDE")
        for method in self.CONTOUR_METHODS.keys():
            tk.Radiobutton(method_frame, text=method, variable=self.method_var,
                          value=method, bg="#ecf0f1").pack(anchor=tk.W, pady=2)

        # Parameters
        params_frame = tk.LabelFrame(parent, text="⚙️ Parameters", padx=10, pady=10, bg="#ecf0f1")
        params_frame.pack(fill=tk.X, padx=10, pady=10)

        # Grid size
        tk.Label(params_frame, text="Grid Size:", bg="#ecf0f1").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.grid_var = tk.IntVar(value=100)
        tk.Scale(params_frame, from_=50, to=200, variable=self.grid_var,
                orient=tk.HORIZONTAL, length=150, bg="#ecf0f1").grid(row=0, column=1, padx=5, pady=5)

        # Contour levels
        tk.Label(params_frame, text="Contour Levels:", bg="#ecf0f1").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.levels_var = tk.IntVar(value=8)
        tk.Spinbox(params_frame, from_=3, to=20, textvariable=self.levels_var,
                  width=10).grid(row=1, column=1, padx=5, pady=5)

        # Bandwidth
        tk.Label(params_frame, text="KDE Bandwidth:", bg="#ecf0f1").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.bw_var = tk.StringVar(value="scott")
        bw_combo = ttk.Combobox(params_frame, textvariable=self.bw_var,
                               values=self.BANDWIDTH_OPTIONS, width=10)
        bw_combo.grid(row=2, column=1, padx=5, pady=5)

        # Color map
        tk.Label(params_frame, text="Color Map:", bg="#ecf0f1").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.cmap_var = tk.StringVar(value="viridis")
        cmap_combo = ttk.Combobox(params_frame, textvariable=self.cmap_var,
                                 values=self.COLORMAPS, width=10)
        cmap_combo.grid(row=3, column=1, padx=5, pady=5)

        # Options
        options_frame = tk.Frame(parent, bg="#ecf0f1")
        options_frame.pack(fill=tk.X, padx=10, pady=10)

        self.show_points_var = tk.BooleanVar(value=True)
        tk.Checkbutton(options_frame, text="Show Data Points",
                      variable=self.show_points_var, bg="#ecf0f1").pack(side=tk.LEFT, padx=5)

        self.fill_contours_var = tk.BooleanVar(value=True)
        tk.Checkbutton(options_frame, text="Fill Contours",
                      variable=self.fill_contours_var, bg="#ecf0f1").pack(side=tk.LEFT, padx=5)

        self.show_colorbar_var = tk.BooleanVar(value=True)
        tk.Checkbutton(options_frame, text="Show Color Bar",
                      variable=self.show_colorbar_var, bg="#ecf0f1").pack(side=tk.LEFT, padx=5)

        # Buttons
        button_frame = tk.Frame(parent, bg="#ecf0f1", pady=10)
        button_frame.pack(fill=tk.X, padx=10)

        # Load Data button
        self.load_btn = tk.Button(button_frame, text="📥 Load Data", bg="#3498db", fg="white",
                                 width=15, command=self._load_data)
        self.load_btn.pack(side=tk.LEFT, padx=5)

        # Generate button
        self.generate_btn = tk.Button(button_frame, text="🌀 Generate", bg="#9b59b6", fg="white",
                                     font=("Arial", 10, "bold"), width=15,
                                     command=self._start_generation)
        self.generate_btn.pack(side=tk.LEFT, padx=5)

        # Export button
        self.export_btn = tk.Button(button_frame, text="💾 Export", bg="#2ecc71", fg="white",
                                   width=15, command=self._export_plot)
        self.export_btn.pack(side=tk.LEFT, padx=5)

        # Import button
        self.import_btn = tk.Button(button_frame, text="📤 Import", bg="#e67e22", fg="white",
                                   width=15, command=self._import_to_main)
        self.import_btn.pack(side=tk.LEFT, padx=5)

        # Status
        self.status_label = tk.Label(parent, text="Ready", bg="#ecf0f1", fg="#7f8c8d")
        self.status_label.pack(fill=tk.X, padx=10, pady=5)

        # Progress
        self.progress = ttk.Progressbar(parent, mode='indeterminate')
        self.progress.pack(fill=tk.X, padx=10, pady=5)

    def _setup_right_panel(self, parent):
        """Setup visualization panel"""
        # Notebook
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Plot tab
        plot_tab = tk.Frame(self.notebook)
        self.notebook.add(plot_tab, text="📈 Contour Plot")

        self.figure = plt.Figure(figsize=(10, 7), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, plot_tab)

        # Add toolbar
        toolbar = NavigationToolbar2Tk(self.canvas, plot_tab)
        toolbar.update()

        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Stats tab
        stats_tab = tk.Frame(self.notebook)
        self.notebook.add(stats_tab, text="📊 Statistics")

        self.stats_text = scrolledtext.ScrolledText(stats_tab, wrap=tk.WORD, font=("Courier", 10))
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Data tab
        data_tab = tk.Frame(self.notebook)
        self.notebook.add(data_tab, text="📋 Data")

        # Treeview
        tree_frame = tk.Frame(data_tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")

        self.tree = ttk.Treeview(tree_frame, yscrollcommand=vsb.set,
                                xscrollcommand=hsb.set)
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)

        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Log tab
        log_tab = tk.Frame(self.notebook)
        self.notebook.add(log_tab, text="📝 Log")

        self.log_text = scrolledtext.ScrolledText(log_tab, wrap=tk.WORD, font=("Courier", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _load_data(self):
        """Load data from main app"""
        if not hasattr(self.app, 'samples') or not self.app.samples:
            messagebox.showwarning("No Data", "Please load data in the main application first!")
            return

        try:
            self.df = pd.DataFrame(self.app.samples)

            # Convert numeric columns
            for col in self.df.columns:
                if col not in ['Sample_ID', 'Notes']:
                    try:
                        self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
                    except:
                        pass

            # Update info
            sample_count = len(self.df)
            column_count = len(self.df.columns)

            self.data_info_label.config(text=f"Samples: {sample_count}")
            self.column_info_label.config(text=f"Columns: {column_count}")

            # Update combobox suggestions with actual column names
            numeric_cols = [col for col in self.df.columns if col not in ['Sample_ID', 'Notes']]
            self.x_entry['values'] = numeric_cols[:20] + self.ELEMENT_SUGGESTIONS
            self.y_entry['values'] = numeric_cols[:20] + self.ELEMENT_SUGGESTIONS

            # Auto-select first two numeric columns if empty
            if not self.x_var.get() and len(numeric_cols) > 0:
                self.x_var.set(numeric_cols[0])
            if not self.y_var.get() and len(numeric_cols) > 1:
                self.y_var.set(numeric_cols[1])

            # Update data view
            self._update_data_view()

            self.status_label.config(text=f"Loaded {sample_count} samples", fg="green")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {str(e)}")

    def _start_generation(self):
        """Start contour generation"""
        if self.is_processing:
            return

        if self.df.empty:
            messagebox.showwarning("No Data", "Load data first!")
            return

        x_col = self.x_var.get().strip()
        y_col = self.y_var.get().strip()

        if not x_col or not y_col:
            messagebox.showwarning("Input Error", "Please enter both X and Y axis column names")
            return

        self.is_processing = True
        self.generate_btn.config(state=tk.DISABLED, text="Generating...")
        self.progress.start()
        self.status_label.config(text=f"Generating contours for {x_col} vs {y_col}...", fg="orange")

        # Start thread
        thread = threading.Thread(target=self._generate_contours, args=(x_col, y_col), daemon=True)
        thread.start()

    def _generate_contours(self, x_col, y_col):
        """Generate contours in thread"""
        try:
            # Find the actual data columns (case-insensitive, flexible matching)
            x_data, x_label = self._get_column_data(x_col)
            y_data, y_label = self._get_column_data(y_col)

            if x_data is None:
                self.window.after(0, lambda: messagebox.showerror(
                    "Error", f"Cannot find column: {x_col}\nAvailable: {', '.join(self.df.columns[:15])}"
                ))
                return

            if y_data is None:
                self.window.after(0, lambda: messagebox.showerror(
                    "Error", f"Cannot find column: {y_col}\nAvailable: {', '.join(self.df.columns[:15])}"
                ))
                return

            # Remove NaN values
            valid_mask = ~(pd.isna(x_data) | pd.isna(y_data))
            x_clean = x_data[valid_mask]
            y_clean = y_data[valid_mask]

            if len(x_clean) < 10:
                self.window.after(0, lambda: messagebox.showerror(
                    "Error", f"Need at least 10 valid points (have {len(x_clean)})"
                ))
                return

            # Generate based on method
            method = self.method_var.get()
            if method == "Gaussian KDE":
                result = self._generate_kde(x_clean, y_clean, x_label, y_label)
            elif method == "2D Histogram":
                result = self._generate_histogram(x_clean, y_clean, x_label, y_label)
            else:
                result = self._generate_distance(x_clean, y_clean, x_label, y_label)

            # Update UI
            self.window.after(0, lambda: self._update_results_ui(result))

        except Exception as e:
            self.window.after(0, lambda: messagebox.showerror("Error", f"Generation failed: {str(e)}"))
        finally:
            self.window.after(0, self._reset_processing_ui)

    def _get_column_data(self, col_name):
        """Get column data with flexible matching"""
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

    def _generate_kde(self, x_data, y_data, x_label, y_label):
        """Generate Gaussian KDE contours"""
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
        grid_size = self.grid_var.get()
        x_min, x_max = x_data.min(), x_data.max()
        y_min, y_max = y_data.min(), y_data.max()

        # Add padding
        x_pad = (x_max - x_min) * 0.1
        y_pad = (y_max - y_min) * 0.1

        x_grid = np.linspace(x_min - x_pad, x_max + x_pad, grid_size)
        y_grid = np.linspace(y_min - y_pad, y_max + y_pad, grid_size)
        X, Y = np.meshgrid(x_grid, y_grid)

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
        """Generate 2D histogram contours"""
        grid_size = self.grid_var.get()

        # Create histogram
        H, x_edges, y_edges = np.histogram2d(x_data, y_data, bins=grid_size)

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
        """Generate distance-based contours"""
        grid_size = self.grid_var.get()

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

    def _update_results_ui(self, result):
        """Update UI with results"""
        # Update plot
        self._update_plot(result)

        # Update statistics
        self._update_statistics(result)

        # Add to log
        log_msg = f"[{datetime.now().strftime('%H:%M:%S')}] Generated {result['method']}: {result['x_label']} vs {result['y_label']}\n"
        self.log_text.insert(tk.END, log_msg)
        self.log_text.see(tk.END)

        # Update status
        self.status_label.config(text=f"Generated {result['method']} contours", fg="green")

        # Switch to plot tab
        self.notebook.select(0)

    def _update_plot(self, result):
        """Update the contour plot"""
        self.ax.clear()

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
        cmap = self.cmap_var.get()

        if self.fill_contours_var.get():
            contour = self.ax.contourf(X, Y, Z, levels=levels, cmap=cmap, alpha=0.8)
        else:
            contour = self.ax.contour(X, Y, Z, levels=levels, cmap=cmap, linewidths=2)

        # Colorbar
        if self.show_colorbar_var.get():
            self.figure.colorbar(contour, ax=self.ax, label='Density')

        # Data points
        if self.show_points_var.get():
            self.ax.scatter(x_data, y_data, c='white', edgecolor='black',
                          alpha=0.6, s=30, label='Data Points')

        # Labels and title
        self.ax.set_xlabel(x_label, fontsize=12)
        self.ax.set_ylabel(y_label, fontsize=12)
        self.ax.set_title(f"{method}: {x_label} vs {y_label}\n{len(x_data)} points", fontsize=12)

        # Grid and legend
        self.ax.grid(True, alpha=0.3)
        if self.show_points_var.get():
            self.ax.legend()

        # Redraw
        self.figure.tight_layout()
        self.canvas.draw()

    def _update_statistics(self, result):
        """Update statistics display"""
        x_data = result['x_data']
        y_data = result['y_data']
        x_label = result['x_label']
        y_label = result['y_label']

        stats = f"STATISTICS: {x_label} vs {y_label}\n"
        stats += "=" * 40 + "\n\n"
        stats += f"Data Points: {len(x_data)}\n"
        stats += f"Method: {result['method']}\n\n"

        stats += f"{x_label}:\n"
        stats += f"  Mean: {np.mean(x_data):.3f}\n"
        stats += f"  Std: {np.std(x_data):.3f}\n"
        stats += f"  Min: {np.min(x_data):.3f}\n"
        stats += f"  Max: {np.max(x_data):.3f}\n\n"

        stats += f"{y_label}:\n"
        stats += f"  Mean: {np.mean(y_data):.3f}\n"
        stats += f"  Std: {np.std(y_data):.3f}\n"
        stats += f"  Min: {np.min(y_data):.3f}\n"
        stats += f"  Max: {np.max(y_data):.3f}\n\n"

        # Correlation
        r = np.corrcoef(x_data, y_data)[0, 1]
        stats += f"Correlation (r): {r:.3f}\n"
        stats += f"R-squared: {r**2:.3f}\n"

        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats)

    def _update_data_view(self):
        """Update data treeview"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        if self.df.empty:
            return

        # Show first 8 columns
        columns = ['Sample_ID'] + [col for col in self.df.columns if col not in ['Sample_ID', 'Notes']][:7]
        self.tree["columns"] = columns
        self.tree["show"] = "headings"

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)

        # Add data
        for idx, row in self.df.head(20).iterrows():
            values = [row.get(col, '') for col in columns]
            # Format numbers
            formatted = []
            for val in values:
                if isinstance(val, (int, float)):
                    formatted.append(f"{val:.3f}")
                else:
                    formatted.append(str(val))
            self.tree.insert("", tk.END, values=formatted)

    def _reset_processing_ui(self):
        """Reset UI after processing"""
        self.is_processing = False
        self.generate_btn.config(state=tk.NORMAL, text="🌀 Generate")
        self.progress.stop()

    def _export_plot(self):
        """Export plot to file"""
        if not hasattr(self, 'figure') or len(self.figure.axes) == 0:
            messagebox.showwarning("No Plot", "Generate a plot first!")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[
                ("PNG files", "*.png"),
                ("PDF files", "*.pdf"),
                ("SVG files", "*.svg")
            ]
        )

        if filename:
            try:
                self.figure.savefig(filename, dpi=300, bbox_inches='tight')
                messagebox.showinfo("Success", f"Plot saved to:\n{filename}")

                self.log_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] Exported: {filename}\n")
                self.log_text.see(tk.END)

            except Exception as e:
                messagebox.showerror("Error", f"Export failed: {str(e)}")

    def _import_to_main(self):
        """Import to main app"""
        if self.df.empty:
            messagebox.showwarning("No Data", "Load data first!")
            return

        try:
            # Clear existing
            self.app.samples = []

            # Add samples
            for idx, row in self.df.iterrows():
                sample = {}

                # Add all data
                for col in self.df.columns:
                    val = row[col]
                    if not pd.isna(val):
                        sample[col] = str(val)

                # Required fields
                sample['Sample_ID'] = f"CNTR_{idx:04d}"
                sample['Notes'] = "Contouring analysis"

                self.app.samples.append(sample)

            # Refresh
            if hasattr(self.app, 'refresh_tree'):
                self.app.refresh_tree()

            messagebox.showinfo("Success", f"Imported {len(self.df)} samples")

        except Exception as e:
            messagebox.showerror("Error", f"Import failed: {str(e)}")

def setup_plugin(main_app):
    """Plugin setup"""
    plugin = InteractiveContouringPlugin(main_app)
    return plugin  # ← REMOVE ALL MENU CODE
