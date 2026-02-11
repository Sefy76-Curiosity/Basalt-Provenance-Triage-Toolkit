"""
3D Thin-Section Virtual Microscopy Plugin
Interactive 3D visualization of thin-section data and mineral distributions

Features:
- 3D virtual thin-section viewer
- Mineral distribution mapping
- Texture analysis (grain size, shape, orientation)
- Porosity/void space visualization
- Interactive mineral identification
- Export 3D models (STL, OBJ)
- Cross-polarized/plane-polarized simulation

Author: Sefy Levy
License: CC BY-NC-SA 4.0
"""

PLUGIN_INFO = {
    "category": "visualization",
    "id": "virtual_microscopy",
    "name": "3D Thin-Section Microscopy",
    "description": "Interactive 3D visualization of thin-section data",
    "icon": "🔬",
    "version": "1.0",
    "requires": ["numpy", "matplotlib", "pillow"],
    "author": "Sefy Levy"
}

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import numpy as np
import json
import traceback
from pathlib import Path
from datetime import datetime

# Import matplotlib with tkinter support
try:
    import matplotlib
    matplotlib.use('TkAgg')  # Use Tkinter backend
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    from matplotlib.figure import Figure
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    MATPLOTLIB_ERROR = "matplotlib not found"

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    NUMPY_ERROR = "numpy not found"

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    PIL_ERROR = "PIL/Pillow not found"

HAS_REQUIREMENTS = HAS_NUMPY and HAS_MATPLOTLIB and HAS_PIL


class VirtualMicroscopyPlugin:
    """Plugin for 3D thin-section visualization"""

    def __init__(self, main_app):
        """Initialize plugin"""
        self.app = main_app
        self.window = None
        self.current_section = None
        self.mineral_data = []
        self.texture_data = None

        # Default mineral colors (RGBA)
        self.mineral_colors = {
            'quartz': [0.9, 0.9, 0.9, 1.0],      # White/gray
            'feldspar': [0.8, 0.8, 1.0, 1.0],    # Light blue
            'plagioclase': [0.7, 0.8, 0.9, 1.0], # Blue-gray
            'biotite': [0.2, 0.2, 0.2, 1.0],     # Dark brown/black
            'muscovite': [0.9, 0.9, 0.7, 1.0],   # Pale yellow
            'amphibole': [0.1, 0.5, 0.1, 1.0],   # Dark green
            'pyroxene': [0.3, 0.3, 0.1, 1.0],    # Dark green-brown
            'olivine': [0.2, 0.6, 0.2, 1.0],     # Green
            'apatite': [0.8, 0.4, 0.8, 1.0],     # Purple
            'zircon': [0.9, 0.9, 0.1, 1.0],      # Yellow
            'opaque': [0.1, 0.1, 0.1, 1.0],      # Black
            'calcite': [1.0, 1.0, 0.8, 1.0],     # Pale yellow
            'clay': [0.6, 0.5, 0.4, 1.0],        # Brown
            'void': [0.0, 0.0, 0.0, 0.0],        # Transparent
            'unknown': [0.5, 0.5, 0.5, 1.0]      # Gray
        }

        # Mineral properties
        self.mineral_properties = {
            'quartz': {'hardness': 7, 'birefringence': 0.009, 'relief': 'low'},
            'feldspar': {'hardness': 6, 'birefringence': 0.007, 'relief': 'low'},
            'biotite': {'hardness': 2.5, 'birefringence': 0.040, 'relief': 'moderate'},
            'amphibole': {'hardness': 5.5, 'birefringence': 0.025, 'relief': 'moderate'},
            'pyroxene': {'hardness': 6, 'birefringence': 0.030, 'relief': 'high'},
            'olivine': {'hardness': 6.5, 'birefringence': 0.035, 'relief': 'high'},
        }

        # Initialize matplotlib figure
        self.fig = None
        self.ax = None
        self.canvas = None

    def show(self):
        """Main show method - called by application"""
        self.open_virtual_microscopy()

    def open(self):
        """Alternative open method"""
        self.open_virtual_microscopy()

    def open_virtual_microscopy(self):
        """Open the virtual microscopy interface"""
        if not HAS_REQUIREMENTS:
            missing = []
            if not HAS_NUMPY: missing.append("numpy")
            if not HAS_MATPLOTLIB: missing.append("matplotlib")
            if not HAS_PIL: missing.append("pillow")

            messagebox.showerror(
                "Missing Dependencies",
                f"Virtual Microscopy requires these packages:\n\n"
                f"• numpy\n• matplotlib\n• pillow\n\n"
                f"Missing: {', '.join(missing)}",
                parent=self.app.root if hasattr(self.app, 'root') else None
            )
            return

        # Close existing window if open
        if self.window and self.window.winfo_exists():
            self.window.destroy()

        # Create new window
        self.window = tk.Toplevel()
        self.window.title("3D Thin-Section Virtual Microscopy")
        self.window.geometry("1200x700")

        # Make window stay on top
        if hasattr(self.app, 'root'):
            self.window.transient(self.app.root)

        self._create_interface()

        # Center window
        self._center_window()

        # Bring to front
        self.window.focus_force()
        self.window.lift()

        # Load demo data automatically
        self.window.after(500, self._load_demo_data)

    def _center_window(self):
        """Center window on screen"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')

    def _create_interface(self):
        """Create the main interface"""
        # Create main container
        main_container = tk.Frame(self.window)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Header
        header = tk.Frame(main_container, bg="#2C3E50")
        header.pack(fill=tk.X, pady=(0, 10))

        tk.Label(header,
                text="🔬 3D Thin-Section Virtual Microscopy",
                font=("Arial", 16, "bold"),
                bg="#2C3E50", fg="white",
                pady=10).pack()

        tk.Label(header,
                text="Interactive visualization of mineral distributions and textures",
                font=("Arial", 10),
                bg="#2C3E50", fg="#BDC3C7").pack(pady=(0, 10))

        # Main content area
        content_frame = tk.Frame(main_container)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Left panel - Controls
        left_panel = tk.Frame(content_frame, width=300, relief=tk.RAISED, borderwidth=1)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        left_panel.pack_propagate(False)

        # Right panel - Visualization
        right_panel = tk.Frame(content_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Create panels
        self._create_control_panel(left_panel)
        self._create_visualization_panel(right_panel)

    def _create_control_panel(self, parent):
        """Create the control panel"""
        # Create scrollable frame
        canvas = tk.Canvas(parent)
        scrollbar = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Sample selection
        sample_frame = tk.LabelFrame(scrollable_frame, text="Sample", padx=10, pady=10)
        sample_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Button(sample_frame, text="📁 Load Data",
                 command=self._load_data,
                 width=25).pack(pady=5)

        tk.Button(sample_frame, text="🎲 Generate Demo",
                 command=self._generate_demo,
                 width=25).pack(pady=5)

        tk.Button(sample_frame, text="🗑️ Clear Data",
                 command=self._clear_data,
                 width=25).pack(pady=5)

        # Visualization settings
        viz_frame = tk.LabelFrame(scrollable_frame, text="Visualization", padx=10, pady=10)
        viz_frame.pack(fill=tk.X, padx=5, pady=5)

        # Mineral selection
        tk.Label(viz_frame, text="Show Minerals:").pack(anchor=tk.W)

        self.mineral_vars = {}
        minerals_frame = tk.Frame(viz_frame)
        minerals_frame.pack(fill=tk.X, pady=5)

        minerals = list(self.mineral_colors.keys())
        for mineral in minerals:
            var = tk.BooleanVar(value=True)
            self.mineral_vars[mineral] = var

            frame = tk.Frame(minerals_frame)
            frame.pack(fill=tk.X, pady=1)

            cb = tk.Checkbutton(frame, text=mineral.capitalize(),
                              variable=var, anchor=tk.W)
            cb.pack(side=tk.LEFT)

            # Color preview
            color = self.mineral_colors[mineral]
            preview = tk.Canvas(frame, width=20, height=20,
                               bg=self._rgb_to_hex(color))
            preview.pack(side=tk.RIGHT)

        # Display settings
        tk.Label(viz_frame, text="Point Size:").pack(anchor=tk.W, pady=(10, 0))
        self.size_var = tk.DoubleVar(value=50)
        tk.Scale(viz_frame, from_=10, to=200, orient=tk.HORIZONTAL,
                variable=self.size_var).pack(fill=tk.X, pady=5)

        tk.Label(viz_frame, text="Transparency:").pack(anchor=tk.W)
        self.alpha_var = tk.DoubleVar(value=0.7)
        tk.Scale(viz_frame, from_=0.1, to=1.0, resolution=0.1,
                orient=tk.HORIZONTAL, variable=self.alpha_var).pack(fill=tk.X, pady=5)

        # Analysis tools
        analysis_frame = tk.LabelFrame(scrollable_frame, text="Analysis", padx=10, pady=10)
        analysis_frame.pack(fill=tk.X, padx=5, pady=5)

        tools = [
            ("📊 Show Statistics", self._show_statistics),
            ("📈 Grain Size Analysis", self._analyze_grain_sizes),
            ("🎨 Adjust Colors", self._adjust_colors),
            ("📷 Save Image", self._save_image),
            ("📋 Export Data", self._export_data)
        ]

        for text, cmd in tools:
            tk.Button(analysis_frame, text=text,
                     command=cmd, width=25).pack(pady=2)

        # Status bar at bottom
        self.status_var = tk.StringVar(value="Ready")
        tk.Label(scrollable_frame, textvariable=self.status_var,
                bg="#ECF0F1", fg="#2C3E50",
                font=("Arial", 9)).pack(fill=tk.X, pady=10)

    def _create_visualization_panel(self, parent):
        """Create the visualization panel"""
        # Create matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(10, 8))
        self.canvas = FigureCanvasTkAgg(self.fig, parent)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Add toolbar
        toolbar_frame = tk.Frame(parent)
        toolbar_frame.pack(fill=tk.X, padx=5)
        toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        toolbar.update()

        # Initial empty plot
        self.ax.text(0.5, 0.5, "Load or generate data to visualize",
                    ha='center', va='center', fontsize=12, color='gray',
                    transform=self.ax.transAxes)
        self.ax.set_axis_off()
        self.fig.tight_layout()
        self.canvas.draw()

    def _load_data(self):
        """Load data from file"""
        filetypes = [
            ("JSON files", "*.json"),
            ("CSV files", "*.csv"),
            ("Image files", "*.png *.jpg *.jpeg *.tif *.tiff"),
            ("All files", "*.*")
        ]

        path = filedialog.askopenfilename(
            title="Load Thin-Section Data",
            filetypes=filetypes
        )

        if not path:
            return

        try:
            self.status_var.set(f"Loading {Path(path).name}...")
            self.window.update()

            ext = Path(path).suffix.lower()

            if ext == '.json':
                self._load_json(path)
            elif ext == '.csv':
                self._load_csv(path)
            elif ext in ['.png', '.jpg', '.jpeg', '.tif', '.tiff']:
                self._load_image(path)
            else:
                messagebox.showerror("Error", f"Unsupported file type: {ext}")
                return

            self.status_var.set(f"Loaded: {Path(path).name}")
            self._update_plot()

        except Exception as e:
            messagebox.showerror("Load Error", f"Error loading file:\n{str(e)}")
            self.status_var.set("Load failed")

    def _load_json(self, path):
        """Load JSON data"""
        with open(path, 'r') as f:
            data = json.load(f)

        self.current_section = data.get('section', {})
        self.mineral_data = data.get('minerals', [])
        self.texture_data = data.get('texture', {})

    def _load_csv(self, path):
        """Load CSV data"""
        import pandas as pd
        df = pd.read_csv(path)

        self.mineral_data = []
        for _, row in df.iterrows():
            grain = {
                'type': row.get('Mineral', 'unknown'),
                'x': row.get('X', 0),
                'y': row.get('Y', 0),
                'z': row.get('Z', 0),
                'size': row.get('Size', 1),
                'shape': row.get('Shape', 'equant')
            }
            self.mineral_data.append(grain)

        self.current_section = {
            'width': df['X'].max() if 'X' in df.columns else 100,
            'height': df['Y'].max() if 'Y' in df.columns else 100,
            'depth': df['Z'].max() if 'Z' in df.columns else 10
        }

    def _load_image(self, path):
        """Load and process image"""
        from PIL import Image
        import numpy as np

        img = Image.open(path)
        img_gray = img.convert('L')
        img_array = np.array(img_gray)

        height, width = img_array.shape
        self.mineral_data = []

        # Sample points
        step = max(1, min(width, height) // 50)

        for y in range(0, height, step):
            for x in range(0, width, step):
                pixel_value = img_array[y, x]

                # Simple classification
                if pixel_value > 200:
                    mineral_type = 'quartz'
                elif pixel_value > 150:
                    mineral_type = 'feldspar'
                elif pixel_value > 100:
                    mineral_type = 'biotite'
                else:
                    mineral_type = 'opaque'

                grain = {
                    'type': mineral_type,
                    'x': x,
                    'y': y,
                    'z': 0,
                    'size': step / 2,
                    'shape': 'equant'
                }
                self.mineral_data.append(grain)

        self.current_section = {
            'width': width,
            'height': height,
            'depth': 10
        }

    def _generate_demo(self):
        """Generate demo data"""
        self.status_var.set("Generating demo data...")
        self.window.update()

        np.random.seed(42)

        # Create demo section
        width, height, depth = 100, 100, 10
        self.mineral_data = []

        mineral_types = ['quartz', 'feldspar', 'biotite', 'amphibole', 'opaque', 'void']
        proportions = [0.35, 0.25, 0.15, 0.10, 0.10, 0.05]

        total_grains = 500

        for mineral, proportion in zip(mineral_types, proportions):
            n_grains = int(total_grains * proportion)

            for i in range(n_grains):
                grain = {
                    'type': mineral,
                    'x': np.random.uniform(0, width),
                    'y': np.random.uniform(0, height),
                    'z': np.random.uniform(0, depth),
                    'size': np.random.uniform(1, 8),
                    'shape': 'equant'
                }
                self.mineral_data.append(grain)

        self.current_section = {
            'width': width,
            'height': height,
            'depth': depth,
            'name': 'Demo Granite Thin-Section',
            'rock_type': 'Granite',
            'location': 'Synthetic'
        }

        self.status_var.set("Loaded: Demo Section")
        self._update_plot()

    def _load_demo_data(self):
        """Load demo data on startup"""
        self._generate_demo()

    def _clear_data(self):
        """Clear all data"""
        self.mineral_data = []
        self.current_section = None
        self.status_var.set("Data cleared")
        self._update_plot()

    def _update_plot(self):
        """Update the matplotlib plot"""
        self.ax.clear()

        if not self.mineral_data:
            self.ax.text(0.5, 0.5, "No data loaded",
                        ha='center', va='center', fontsize=12, color='gray',
                        transform=self.ax.transAxes)
            self.ax.set_axis_off()
        else:
            # Filter minerals based on checkboxes
            filtered_data = []
            for grain in self.mineral_data:
                mineral = grain.get('type', 'unknown')
                if mineral in self.mineral_vars and self.mineral_vars[mineral].get():
                    filtered_data.append(grain)

            if not filtered_data:
                self.ax.text(0.5, 0.5, "No minerals selected",
                            ha='center', va='center', fontsize=12, color='gray',
                            transform=self.ax.transAxes)
                self.ax.set_axis_off()
            else:
                # Prepare data for plotting
                x_vals = []
                y_vals = []
                colors = []
                sizes = []

                for grain in filtered_data:
                    x_vals.append(grain['x'])
                    y_vals.append(grain['y'])

                    mineral = grain.get('type', 'unknown')
                    color = self.mineral_colors.get(mineral, [0.5, 0.5, 0.5, 1.0])
                    colors.append(color[:3])  # RGB only

                    # Scale size
                    base_size = grain.get('size', 1)
                    sizes.append(base_size * self.size_var.get())

                # Create scatter plot
                scatter = self.ax.scatter(x_vals, y_vals,
                                         s=sizes,
                                         c=colors,
                                         alpha=self.alpha_var.get(),
                                         edgecolors='black',
                                         linewidths=0.5)

                # Set plot limits
                if self.current_section:
                    self.ax.set_xlim(0, self.current_section.get('width', 100))
                    self.ax.set_ylim(0, self.current_section.get('height', 100))

                self.ax.set_aspect('equal')
                self.ax.set_xlabel('X Position (μm)')
                self.ax.set_ylabel('Y Position (μm)')
                self.ax.set_title('2D Mineral Distribution')

                # Add legend
                unique_minerals = set(g['type'] for g in filtered_data)
                legend_handles = []
                for mineral in sorted(unique_minerals):
                    if mineral in self.mineral_colors:
                        color = self.mineral_colors[mineral]
                        legend_handles.append(plt.Line2D([0], [0],
                                                        marker='o',
                                                        color='w',
                                                        markerfacecolor=color[:3],
                                                        markersize=8,
                                                        label=mineral.capitalize()))

                if legend_handles:
                    self.ax.legend(handles=legend_handles,
                                  loc='upper right',
                                  fontsize='small',
                                  ncol=2)

        self.fig.tight_layout()
        self.canvas.draw()

    def _show_statistics(self):
        """Show statistics dialog"""
        if not self.mineral_data:
            messagebox.showinfo("No Data", "No data loaded.")
            return

        # Create statistics window
        stats_win = tk.Toplevel(self.window)
        stats_win.title("Thin-Section Statistics")
        stats_win.geometry("500x400")

        # Create text widget
        text = scrolledtext.ScrolledText(stats_win, wrap=tk.WORD, font=("Courier", 10))
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Calculate statistics
        mineral_counts = {}
        mineral_sizes = {}

        for grain in self.mineral_data:
            mineral = grain['type']
            size = grain['size']

            if mineral not in mineral_counts:
                mineral_counts[mineral] = 0
                mineral_sizes[mineral] = []

            mineral_counts[mineral] += 1
            mineral_sizes[mineral].append(size)

        # Generate report
        report = []
        report.append("THIN-SECTION STATISTICS")
        report.append("=" * 50)
        report.append("")

        if self.current_section:
            report.append("SECTION INFORMATION:")
            for key, value in self.current_section.items():
                if isinstance(value, (int, float, str)):
                    report.append(f"  {key}: {value}")
            report.append("")

        report.append("MINERAL DISTRIBUTION:")
        report.append("-" * 30)

        total_grains = len(self.mineral_data)
        for mineral, count in sorted(mineral_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_grains) * 100
            size_data = mineral_sizes[mineral]
            avg_size = np.mean(size_data) if size_data else 0

            report.append(f"{mineral.capitalize():12} {count:4d} grains ({percentage:5.1f}%)")
            report.append(f"              Avg size: {avg_size:.2f} μm")

        report.append("")
        report.append(f"Total grains: {total_grains}")

        # Insert report
        text.insert('1.0', '\n'.join(report))
        text.config(state='disabled')

    def _analyze_grain_sizes(self):
        """Analyze grain size distribution"""
        if not self.mineral_data:
            messagebox.showinfo("No Data", "No data loaded.")
            return

        # Extract sizes
        sizes = [g['size'] for g in self.mineral_data if g['type'] != 'void']

        if not sizes:
            messagebox.showinfo("No Grains", "No mineral grains to analyze.")
            return

        # Create analysis window
        analysis_win = tk.Toplevel(self.window)
        analysis_win.title("Grain Size Analysis")
        analysis_win.geometry("600x500")

        # Create matplotlib figure
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6, 8))

        # Histogram
        ax1.hist(sizes, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        ax1.set_xlabel('Grain Size (μm)')
        ax1.set_ylabel('Frequency')
        ax1.set_title('Grain Size Distribution')

        # Add statistics
        mean_size = np.mean(sizes)
        median_size = np.median(sizes)
        std_size = np.std(sizes)

        ax1.axvline(mean_size, color='red', linestyle='--', label=f'Mean: {mean_size:.2f} μm')
        ax1.axvline(median_size, color='green', linestyle='--', label=f'Median: {median_size:.2f} μm')
        ax1.legend()

        # Box plot
        ax2.boxplot(sizes, vert=False)
        ax2.set_xlabel('Grain Size (μm)')
        ax2.set_title('Grain Size Statistics')

        # Add text summary
        stats_text = f"""Statistics:
        Count: {len(sizes)}
        Mean: {mean_size:.2f} μm
        Median: {median_size:.2f} μm
        Std Dev: {std_size:.2f} μm
        Min: {min(sizes):.2f} μm
        Max: {max(sizes):.2f} μm"""

        ax2.text(0.02, 0.95, stats_text, transform=ax2.transAxes,
                fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        fig.tight_layout()

        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, analysis_win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _adjust_colors(self):
        """Adjust mineral colors"""
        color_win = tk.Toplevel(self.window)
        color_win.title("Adjust Mineral Colors")
        color_win.geometry("400x500")

        # Create scrollable frame
        canvas = tk.Canvas(color_win)
        scrollbar = tk.Scrollbar(color_win, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Color pickers for each mineral
        for mineral, color in self.mineral_colors.items():
            frame = tk.Frame(scrollable_frame)
            frame.pack(fill=tk.X, padx=10, pady=5)

            tk.Label(frame, text=mineral.capitalize(), width=15).pack(side=tk.LEFT)

            # Current color preview
            preview = tk.Canvas(frame, width=30, height=30,
                               bg=self._rgb_to_hex(color))
            preview.pack(side=tk.LEFT, padx=5)

            # Color picker button
            tk.Button(frame, text="Change",
                     command=lambda m=mineral, p=preview: self._pick_color(m, p)).pack(side=tk.LEFT)

        # Apply button
        tk.Button(color_win, text="Apply Colors",
                 command=self._apply_colors,
                 bg="#4CAF50", fg="white",
                 font=("Arial", 11, "bold")).pack(pady=10)

    def _pick_color(self, mineral, preview_canvas):
        """Pick color for mineral"""
        from tkinter import colorchooser

        current_color = self.mineral_colors[mineral]
        hex_color = self._rgb_to_hex(current_color)

        color = colorchooser.askcolor(hex_color, title=f"Pick color for {mineral}")
        if color[1]:
            # Update preview
            preview_canvas.config(bg=color[1])
            # Store RGB values (0-255 to 0-1)
            rgb = tuple(int(color[1][i:i+2], 16) / 255.0 for i in (1, 3, 5))
            self.mineral_colors[mineral] = [rgb[0], rgb[1], rgb[2], 1.0]

    def _apply_colors(self):
        """Apply color changes and update plot"""
        self._update_plot()
        messagebox.showinfo("Colors Updated", "Mineral colors have been updated.")

    def _save_image(self):
        """Save current plot as image"""
        if not self.mineral_data:
            messagebox.showwarning("No Data", "No data to save.")
            return

        path = filedialog.asksaveasfilename(
            title="Save Image",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"),
                      ("JPEG files", "*.jpg"),
                      ("PDF files", "*.pdf"),
                      ("All files", "*.*")]
        )

        if path:
            try:
                self.fig.savefig(path, dpi=300, bbox_inches='tight')
                self.status_var.set(f"Image saved: {Path(path).name}")
                messagebox.showinfo("Success", f"Image saved to:\n{path}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Error saving image:\n{str(e)}")

    def _export_data(self):
        """Export data to file"""
        if not self.mineral_data:
            messagebox.showwarning("No Data", "No data to export.")
            return

        path = filedialog.asksaveasfilename(
            title="Export Data",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"),
                      ("CSV files", "*.csv"),
                      ("All files", "*.*")]
        )

        if path:
            try:
                ext = Path(path).suffix.lower()

                if ext == '.json':
                    data = {
                        'section': self.current_section,
                        'minerals': self.mineral_data,
                        'texture': self.texture_data,
                        'export_date': datetime.now().isoformat()
                    }
                    with open(path, 'w') as f:
                        json.dump(data, f, indent=2)

                elif ext == '.csv':
                    import pandas as pd
                    df = pd.DataFrame(self.mineral_data)
                    df.to_csv(path, index=False)

                else:
                    messagebox.showerror("Error", f"Unsupported export format: {ext}")
                    return

                self.status_var.set(f"Data exported: {Path(path).name}")
                messagebox.showinfo("Success", f"Data exported to:\n{path}")

            except Exception as e:
                messagebox.showerror("Export Error", f"Error exporting data:\n{str(e)}")

    def _rgb_to_hex(self, rgb):
        """Convert RGB list to hex color"""
        if len(rgb) >= 3:
            return f'#{int(rgb[0]*255):02x}{int(rgb[1]*255):02x}{int(rgb[2]*255):02x}'
        return '#000000'


# Setup function that the main application calls
def setup_plugin(main_app):
    """Setup function called by main application"""
    plugin = VirtualMicroscopyPlugin(main_app)

    # Add both show and open methods for compatibility
    plugin.show = plugin.open_virtual_microscopy
    plugin.open = plugin.open_virtual_microscopy

    return plugin
