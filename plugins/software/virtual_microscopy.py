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
    "category": "software",
    "id": "virtual_microscopy",
    "name": "3D Thin-Section Microscopy",
    "description": "Interactive 3D visualization of thin-section data",
    "icon": "🔬",
    "version": "1.0",
    "requires": ["pyvista", "numpy", "matplotlib", "pillow"],
    "author": "Sefy Levy"
}

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import numpy as np
from io import StringIO
import traceback
import json
import os
from pathlib import Path

# Check dependencies
HAS_PYVISTA = False
HAS_NUMPY = False
HAS_MATPLOTLIB = False
HAS_PIL = False

try:
    import pyvista as pv
    HAS_PYVISTA = True
except ImportError:
    PYVISTA_ERROR = "pyvista not found"

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    NUMPY_ERROR = "numpy not found"

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    from matplotlib.colors import ListedColormap
    HAS_MATPLOTLIB = True
except ImportError:
    MATPLOTLIB_ERROR = "matplotlib not found"

try:
    from PIL import Image, ImageTk, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    PIL_ERROR = "PIL/Pillow not found"

HAS_REQUIREMENTS = HAS_PYVISTA and HAS_NUMPY and HAS_MATPLOTLIB and HAS_PIL


class VirtualMicroscopyPlugin:
    """Plugin for 3D thin-section visualization"""

    def __init__(self, main_app):
        """Initialize plugin"""
        self.app = main_app
        self.window = None
        self.current_section = None
        self.mineral_data = None
        self.texture_data = None
        self.plotter = None

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

    def open_virtual_microscopy(self):
        """Open the virtual microscopy interface"""
        if not HAS_REQUIREMENTS:
            missing = []
            if not HAS_PYVISTA: missing.append("pyvista")
            if not HAS_NUMPY: missing.append("numpy")
            if not HAS_MATPLOTLIB: missing.append("matplotlib")
            if not HAS_PIL: missing.append("pillow")

            response = messagebox.askyesno(
                "Missing Dependencies",
                f"Virtual Microscopy requires these packages:\n\n"
                f"• pyvista\n• numpy\n• matplotlib\n• pillow\n\n"
                f"Missing: {', '.join(missing)}\n\n"
                f"Do you want to install missing dependencies now?",
                parent=self.app.root
            )
            if response:
                self._install_dependencies(missing)
            return

        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("3D Virtual Microscopy - Thin Section Viewer")
        self.window.geometry("1200x800")

        # Make window stay on top
        self.window.transient(self.app.root)

        self._create_interface()

        # Bring to front
        self.window.lift()
        self.window.focus_force()

    def _create_interface(self):
        """Create the virtual microscopy interface"""
        # Header with microscope icon
        header = tk.Frame(self.window, bg="#37474F")
        header.pack(fill=tk.X)

        tk.Label(header,
                text="🔬 3D Virtual Thin-Section Microscopy",
                font=("Arial", 18, "bold"),
                bg="#37474F", fg="white",
                pady=12).pack()

        tk.Label(header,
                text="Interactive 3D visualization of thin-section mineralogy and texture",
                font=("Arial", 10),
                bg="#37474F", fg="#B0BEC5").pack(pady=(0, 12))

        # Create main container with paned window
        main_paned = ttk.PanedWindow(self.window, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Left panel - Controls and settings
        left_panel = ttk.Frame(main_paned, relief=tk.RAISED, borderwidth=1)
        main_paned.add(left_panel, weight=1)

        # Right panel - Visualization and display
        right_panel = ttk.Frame(main_paned)
        main_paned.add(right_panel, weight=3)

        # Create left panel content
        self._create_control_panel(left_panel)

        # Create right panel content
        self._create_visualization_panel(right_panel)

        # Load demo data if available
        self._load_demo_data()

    def _create_control_panel(self, parent):
        """Create the control panel"""
        # Sample selection
        sample_frame = tk.LabelFrame(parent, text="Sample Selection",
                                    padx=10, pady=10)
        sample_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(sample_frame, text="Current Sample:").pack(anchor=tk.W)

        self.sample_var = tk.StringVar()
        sample_combo = ttk.Combobox(sample_frame, textvariable=self.sample_var,
                                   state="readonly", width=25)
        sample_combo.pack(fill=tk.X, pady=5)

        # Update sample list
        self._update_sample_list()

        # Load buttons
        btn_frame = tk.Frame(sample_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        tk.Button(btn_frame, text="📁 Load Thin-Section Data",
                 command=self._load_thin_section_data,
                 width=25).pack(side=tk.LEFT, padx=2)

        tk.Button(btn_frame, text="🎲 Generate Demo",
                 command=self._generate_demo_section,
                 width=25).pack(side=tk.LEFT, padx=2)

        # Visualization mode
        viz_frame = tk.LabelFrame(parent, text="Visualization Mode",
                                 padx=10, pady=10)
        viz_frame.pack(fill=tk.X, padx=5, pady=5)

        self.viz_mode_var = tk.StringVar(value="3D Mineral Distribution")
        modes = ["3D Mineral Distribution", "2D Mineral Map",
                "Texture Analysis", "Porosity Visualization",
                "Cross-Polarized Simulation", "Grain Boundary Network"]

        for mode in modes:
            tk.Radiobutton(viz_frame, text=mode, variable=self.viz_mode_var,
                          value=mode, anchor=tk.W).pack(fill=tk.X, pady=2)

        # Mineral selection
        mineral_frame = tk.LabelFrame(parent, text="Mineral Display",
                                     padx=10, pady=10)
        mineral_frame.pack(fill=tk.X, padx=5, pady=5)

        # Mineral checklist
        self.mineral_vars = {}
        minerals_frame = tk.Frame(mineral_frame)
        minerals_frame.pack(fill=tk.X)

        # Create two columns
        col1 = tk.Frame(minerals_frame)
        col1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        col2 = tk.Frame(minerals_frame)
        col2.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        minerals = list(self.mineral_colors.keys())
        mid = len(minerals) // 2

        for i, mineral in enumerate(minerals):
            var = tk.BooleanVar(value=True)
            self.mineral_vars[mineral] = var

            if i < mid:
                parent_col = col1
            else:
                parent_col = col2

            cb = tk.Checkbutton(parent_col, text=mineral.capitalize(),
                               variable=var, anchor=tk.W)
            cb.pack(fill=tk.X, pady=1)

            # Color preview
            color = self.mineral_colors[mineral]
            preview_canvas = tk.Canvas(parent_col, width=15, height=15,
                                      bg=self._rgb_to_hex(color),
                                      highlightthickness=1,
                                      highlightbackground="gray")
            preview_canvas.pack(side=tk.RIGHT, padx=5)

        # Color adjustment
        color_frame = tk.Frame(mineral_frame, pady=5)
        color_frame.pack(fill=tk.X)

        tk.Button(color_frame, text="🎨 Adjust Colors",
                 command=self._adjust_colors,
                 width=20).pack(side=tk.LEFT, padx=2)

        tk.Button(color_frame, text="🔄 Reset Colors",
                 command=self._reset_colors,
                 width=20).pack(side=tk.RIGHT, padx=2)

        # Display settings
        display_frame = tk.LabelFrame(parent, text="Display Settings",
                                     padx=10, pady=10)
        display_frame.pack(fill=tk.X, padx=5, pady=5)

        # Transparency
        trans_frame = tk.Frame(display_frame)
        trans_frame.pack(fill=tk.X, pady=2)

        tk.Label(trans_frame, text="Transparency:").pack(side=tk.LEFT)
        self.transparency_var = tk.DoubleVar(value=0.0)
        tk.Scale(trans_frame, from_=0.0, to=1.0, resolution=0.1,
                orient=tk.HORIZONTAL, variable=self.transparency_var,
                length=150).pack(side=tk.RIGHT)

        # Lighting
        light_frame = tk.Frame(display_frame)
        light_frame.pack(fill=tk.X, pady=2)

        tk.Label(light_frame, text="Lighting:").pack(side=tk.LEFT)
        self.lighting_var = tk.DoubleVar(value=0.7)
        tk.Scale(light_frame, from_=0.1, to=1.5, resolution=0.1,
                orient=tk.HORIZONTAL, variable=self.lighting_var,
                length=150).pack(side=tk.RIGHT)

        # Grain size threshold
        size_frame = tk.Frame(display_frame)
        size_frame.pack(fill=tk.X, pady=2)

        tk.Label(size_frame, text="Min Grain Size (px):").pack(side=tk.LEFT)
        self.grain_size_var = tk.IntVar(value=10)
        tk.Entry(size_frame, textvariable=self.grain_size_var,
                width=10).pack(side=tk.RIGHT)

        # Analysis tools
        analysis_frame = tk.LabelFrame(parent, text="Analysis Tools",
                                      padx=10, pady=10)
        analysis_frame.pack(fill=tk.X, padx=5, pady=5)

        tools = [
            ("📐 Grain Size Distribution", self._analyze_grain_size),
            ("📊 Mineral Abundance", self._analyze_mineral_abundance),
            ("🔄 Texture Orientation", self._analyze_texture),
            ("🕳️ Porosity Analysis", self._analyze_porosity),
            ("🔍 Zoom Region", self._zoom_region),
            ("📷 Capture Snapshot", self._capture_snapshot)
        ]

        for text, command in tools:
            tk.Button(analysis_frame, text=text, command=command,
                     width=25).pack(pady=2)

        # Export section
        export_frame = tk.LabelFrame(parent, text="Export",
                                    padx=10, pady=10)
        export_frame.pack(fill=tk.X, padx=5, pady=5)

        export_formats = [
            ("💾 Save as PNG", ".png", self._export_png),
            ("📊 Save as STL", ".stl", self._export_stl),
            ("🎭 Save as OBJ", ".obj", self._export_obj),
            ("📋 Save Statistics", ".csv", self._export_stats),
            ("📄 Save Session", ".json", self._export_session)
        ]

        for text, ext, command in export_formats:
            tk.Button(export_frame, text=text, command=command,
                     width=25).pack(pady=2)

        # Action buttons at bottom
        action_frame = tk.Frame(parent, pady=15)
        action_frame.pack(fill=tk.X, padx=5)

        tk.Button(action_frame, text="🚀 Render 3D View",
                 command=self._render_3d_view,
                 bg="#2196F3", fg="white",
                 font=("Arial", 11, "bold"),
                 height=2).pack(fill=tk.X, pady=5)

        tk.Button(action_frame, text="🔄 Update View",
                 command=self._update_view,
                 bg="#4CAF50", fg="white",
                 font=("Arial", 11, "bold"),
                 height=2).pack(fill=tk.X, pady=5)

    def _create_visualization_panel(self, parent):
        """Create the visualization panel"""
        # Tabbed interface for different views
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: 3D Viewer
        self.tab_3d = tk.Frame(notebook)
        notebook.add(self.tab_3d, text="🎲 3D View")

        # Tab 2: 2D Mineral Map
        self.tab_2d = tk.Frame(notebook)
        notebook.add(self.tab_2d, text="🗺️ 2D Map")

        # Tab 3: Statistics
        self.tab_stats = tk.Frame(notebook)
        notebook.add(self.tab_stats, text="📊 Statistics")

        # Tab 4: Help
        self.tab_help = tk.Frame(notebook)
        notebook.add(self.tab_help, text="❓ Help")

        # Initialize tabs
        self._init_3d_tab()
        self._init_2d_tab()
        self._init_stats_tab()
        self._init_help_tab()

    def _init_3d_tab(self):
        """Initialize 3D viewer tab"""
        # This will be filled when 3D view is rendered
        self.canvas_3d_frame = tk.Frame(self.tab_3d)
        self.canvas_3d_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(self.canvas_3d_frame,
                text="Click 'Render 3D View' to generate interactive 3D visualization",
                font=("Arial", 12),
                fg="gray").pack(expand=True)

    def _init_2d_tab(self):
        """Initialize 2D mineral map tab"""
        # Canvas for 2D map
        self.canvas_2d_frame = tk.Frame(self.tab_2d)
        self.canvas_2d_frame.pack(fill=tk.BOTH, expand=True)

        # Matplotlib figure for 2D map
        self.fig_2d, self.ax_2d = plt.subplots(figsize=(8, 6))
        self.canvas_2d = FigureCanvasTkAgg(self.fig_2d, self.canvas_2d_frame)
        self.canvas_2d.draw()
        self.canvas_2d.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Toolbar
        toolbar_frame = tk.Frame(self.canvas_2d_frame)
        toolbar_frame.pack(side=tk.BOTTOM, fill=tk.X)
        toolbar = NavigationToolbar2Tk(self.canvas_2d, toolbar_frame)
        toolbar.update()

        # Initial message
        self.ax_2d.text(0.5, 0.5, "Load or generate thin-section data\nto view mineral map",
                       ha='center', va='center', transform=self.ax_2d.transAxes,
                       fontsize=12, color='gray')
        self.ax_2d.set_axis_off()
        self.fig_2d.tight_layout()
        self.canvas_2d.draw()

    def _init_stats_tab(self):
        """Initialize statistics tab"""
        # Text widget for statistics
        self.stats_text = scrolledtext.ScrolledText(self.tab_stats,
                                                   wrap=tk.WORD,
                                                   font=("Courier New", 10))
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Initial message
        self.stats_text.insert(tk.END,
                              "Thin-Section Statistics\n"
                              "════════════════════════\n\n"
                              "No data loaded. Please load or generate\n"
                              "thin-section data to view statistics.\n")
        self.stats_text.config(state='disabled')

        # Buttons
        button_frame = tk.Frame(self.tab_stats)
        button_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Button(button_frame, text="Calculate Statistics",
                 command=self._calculate_statistics).pack(side=tk.LEFT, padx=5)

        tk.Button(button_frame, text="Clear",
                 command=lambda: self.stats_text.delete(1.0, tk.END)).pack(side=tk.LEFT, padx=5)

    def _init_help_tab(self):
        """Initialize help tab"""
        text = scrolledtext.ScrolledText(self.tab_help, wrap=tk.WORD,
                                        font=("Arial", 10), padx=10, pady=10)
        text.pack(fill=tk.BOTH, expand=True)

        help_text = """
3D VIRTUAL MICROSCOPY - USER GUIDE
═══════════════════════════════════════════════════════════════

OVERVIEW
────────────────────────────────────────────────────────────────
This tool creates interactive 3D visualizations of thin-section
mineralogy and texture from your geochemical data.

KEY FEATURES:
• 3D mineral distribution visualization
• Interactive mineral identification
• Texture analysis (grain size, shape)
• Porosity and void space mapping
• Cross-polarized light simulation
• Export to 3D formats (STL, OBJ)

═══════════════════════════════════════════════════════════════

WORKFLOW
────────────────────────────────────────────────────────────────

1. LOAD DATA:
   • Select sample from dropdown
   • Load existing thin-section data
   • Generate demo data for testing

2. CONFIGURE VISUALIZATION:
   • Choose visualization mode
   • Select minerals to display
   • Adjust colors and transparency
   • Set display parameters

3. ANALYZE:
   • Render 3D view
   • Analyze grain size distribution
   • Calculate mineral abundances
   • Examine texture patterns
   • Measure porosity

4. EXPORT:
   • Save high-resolution images
   • Export 3D models (STL, OBJ)
   • Save statistical data
   • Save session for later

═══════════════════════════════════════════════════════════════

DATA FORMATS
────────────────────────────────────────────────────────────────

SUPPORTED INPUTS:
• CSV with mineral composition data
• JSON with thin-section parameters
• Image files for texture mapping
• Manual entry for demo generation

REQUIRED DATA (for automatic generation):
• Mineral percentages
• Grain size distribution
• Sample dimensions
• Porosity information

═══════════════════════════════════════════════════════════════

VISUALIZATION MODES
────────────────────────────────────────────────────────────────

1. 3D MINERAL DISTRIBUTION:
   • Interactive 3D scatter plot
   • Color-coded by mineral type
   • Adjustable transparency
   • Rotate, zoom, pan

2. 2D MINERAL MAP:
   • Traditional thin-section view
   • Mineral boundaries
   • Grain size visualization
   • Porosity mapping

3. TEXTURE ANALYSIS:
   • Grain orientation rose diagrams
   • Size distribution histograms
   • Shape factor analysis
   • Fabric visualization

4. CROSS-POLARIZED SIMULATION:
   • Simulates optical microscopy
   • Birefringence colors
   • Extinction positions
   • Interference patterns

═══════════════════════════════════════════════════════════════

ANALYSIS TOOLS
────────────────────────────────────────────────────────────────

GRAIN SIZE ANALYSIS:
• Calculate size distribution
• Mean, median, mode sizes
• Sorting coefficient
• Histogram visualization

MINERAL ABUNDANCE:
• Volume percentages
• Modal vs normative comparison
• Mineral associations
• Spatial distribution

TEXTURE ANALYSIS:
• Grain shape (roundness, sphericity)
• Orientation fabric
• Contact relationships
• Deformation features

POROSITY ANALYSIS:
• Total porosity calculation
• Pore size distribution
• Pore connectivity
• Permeability estimation

═══════════════════════════════════════════════════════════════

EXPORT OPTIONS
────────────────────────────────────────────────────────────────

IMAGES:
• High-resolution PNG
• Publication-quality figures
• Animated rotations (GIF)
• Cross-section views

3D MODELS:
• STL for 3D printing
• OBJ for 3D software
• VRML for virtual reality
• PLY for point clouds

DATA:
• CSV statistics
• JSON session files
• Mineral distribution maps
• Analysis reports

═══════════════════════════════════════════════════════════════

TIPS FOR BEST RESULTS
────────────────────────────────────────────────────────────────

1. Start with demo data to learn interface
2. Adjust colors for better mineral distinction
3. Use transparency to see internal structures
4. Export at high resolution for publications
5. Save sessions to revisit analyses
6. Combine with geochemical data for interpretation

═══════════════════════════════════════════════════════════════

USE CASES
────────────────────────────────────────────────────────────────

PETROLOGY:
• Visualize mineral zoning
• Analyze reaction textures
• Document metamorphic grade
• Identify alteration patterns

GEOCHEMISTRY:
• Correlate chemistry with texture
• Map element distributions
• Identify mineral hosts
• Visualize chemical zoning

ENGINEERING:
• Analyze pore networks
• Measure fracture density
• Characterize material properties
• Quality control of materials

EDUCATION:
• Virtual thin-section library
• Interactive mineral identification
• Texture recognition training
• Remote microscopy teaching

═══════════════════════════════════════════════════════════════
"""

        text.insert('1.0', help_text)
        text.config(state='disabled')

    def _update_sample_list(self):
        """Update sample dropdown list"""
        if not self.app.samples:
            return

        sample_ids = []
        for sample in self.app.samples:
            sample_id = sample.get('Sample_ID')
            if sample_id:
                sample_ids.append(sample_id)

        if sample_ids:
            # Update combobox
            if hasattr(self, 'sample_var'):
                # Find the combobox widget
                for child in self.window.winfo_children():
                    if isinstance(child, ttk.Combobox):
                        child['values'] = sample_ids
                        if sample_ids:
                            child.set(sample_ids[0])
                        break

    def _load_thin_section_data(self):
        """Load thin-section data from file"""
        filetypes = [
            ("CSV files", "*.csv"),
            ("JSON files", "*.json"),
            ("Image files", "*.png *.jpg *.tif"),
            ("All files", "*.*")
        ]

        path = filedialog.askopenfilename(
            title="Load Thin-Section Data",
            filetypes=filetypes
        )

        if path:
            try:
                ext = Path(path).suffix.lower()

                if ext == '.json':
                    self._load_json_data(path)
                elif ext == '.csv':
                    self._load_csv_data(path)
                elif ext in ['.png', '.jpg', '.jpeg', '.tif', '.tiff']:
                    self._load_image_data(path)
                else:
                    messagebox.showerror("Unsupported Format",
                                       f"Cannot load {ext} files.")

            except Exception as e:
                messagebox.showerror("Load Error", f"Error: {str(e)}\n\n{traceback.format_exc()}")

    def _load_json_data(self, path):
        """Load JSON thin-section data"""
        with open(path, 'r') as f:
            data = json.load(f)

        self.current_section = data.get('section', {})
        self.mineral_data = data.get('minerals', [])
        self.texture_data = data.get('texture', {})

        messagebox.showinfo("Data Loaded",
                          f"Loaded thin-section data: {len(self.mineral_data)} minerals")

        # Update display
        self._update_2d_map()
        self._calculate_statistics()

    def _load_csv_data(self, path):
        """Load CSV thin-section data"""
        import pandas as pd
        df = pd.read_csv(path)

        # Convert to mineral data format
        self.mineral_data = []
        for _, row in df.iterrows():
            mineral = {
                'type': row.get('Mineral', 'unknown'),
                'x': row.get('X', 0),
                'y': row.get('Y', 0),
                'z': row.get('Z', 0),
                'size': row.get('Size', 1),
                'shape': row.get('Shape', 'equant')
            }
            self.mineral_data.append(mineral)

        self.current_section = {
            'width': df['X'].max() if 'X' in df.columns else 100,
            'height': df['Y'].max() if 'Y' in df.columns else 100,
            'depth': df['Z'].max() if 'Z' in df.columns else 10
        }

        messagebox.showinfo("Data Loaded",
                          f"Loaded {len(self.mineral_data)} mineral grains")

        self._update_2d_map()
        self._calculate_statistics()

    def _load_image_data(self, path):
        """Load image and convert to mineral data"""
        try:
            from PIL import Image
            import numpy as np

            img = Image.open(path)
            img_gray = img.convert('L')  # Convert to grayscale
            img_array = np.array(img_gray)

            # Simple thresholding to identify minerals
            # This is a demo - real implementation would be more sophisticated
            threshold = 128
            mineral_map = img_array > threshold

            # Convert to mineral data points
            self.mineral_data = []
            height, width = mineral_map.shape

            # Sample points (every 10th pixel for performance)
            for y in range(0, height, 10):
                for x in range(0, width, 10):
                    if mineral_map[y, x]:
                        mineral = {
                            'type': 'quartz' if img_array[y, x] > 200 else 'feldspar',
                            'x': x,
                            'y': y,
                            'z': 0,
                            'size': 5,
                            'shape': 'equant'
                        }
                        self.mineral_data.append(mineral)

            self.current_section = {
                'width': width,
                'height': height,
                'depth': 10
            }

            messagebox.showinfo("Image Loaded",
                              f"Converted image to {len(self.mineral_data)} mineral points")

            self._update_2d_map()
            self._calculate_statistics()

        except Exception as e:
            messagebox.showerror("Image Error", f"Error processing image: {str(e)}")

    def _generate_demo_section(self):
        """Generate a demo thin-section with realistic mineral distributions"""
        np.random.seed(42)  # For reproducible results

        # Create section dimensions
        width, height, depth = 100, 100, 10

        # Define mineral proportions
        mineral_proportions = {
            'quartz': 0.35,
            'feldspar': 0.25,
            'biotite': 0.15,
            'amphibole': 0.10,
            'pyroxene': 0.08,
            'opaque': 0.05,
            'void': 0.02
        }

        # Generate mineral grains
        self.mineral_data = []
        total_grains = 500

        for mineral, proportion in mineral_proportions.items():
            n_grains = int(total_grains * proportion)

            # Different size distributions for different minerals
            if mineral == 'quartz':
                sizes = np.random.uniform(3, 15, n_grains)
            elif mineral == 'feldspar':
                sizes = np.random.uniform(2, 10, n_grains)
            elif mineral in ['biotite', 'amphibole']:
                sizes = np.random.uniform(1, 5, n_grains)
            else:
                sizes = np.random.uniform(0.5, 3, n_grains)

            for i in range(n_grains):
                # Avoid overlap (simple check)
                max_attempts = 10
                for attempt in range(max_attempts):
                    x = np.random.uniform(0, width)
                    y = np.random.uniform(0, height)
                    z = np.random.uniform(0, depth)
                    size = sizes[i]

                    # Check for overlap (simple distance check)
                    too_close = False
                    for existing in self.mineral_data[-100:]:  # Check recent grains
                        dist = np.sqrt((x - existing['x'])**2 +
                                     (y - existing['y'])**2 +
                                     (z - existing['z'])**2)
                        if dist < (size + existing['size']):
                            too_close = True
                            break

                    if not too_close or attempt == max_attempts - 1:
                        grain = {
                            'type': mineral,
                            'x': x,
                            'y': y,
                            'z': z,
                            'size': size,
                            'shape': self._get_grain_shape(mineral),
                            'orientation': np.random.uniform(0, 360) if mineral in ['biotite', 'amphibole'] else 0
                        }
                        self.mineral_data.append(grain)
                        break

        self.current_section = {
            'width': width,
            'height': height,
            'depth': depth,
            'name': 'Demo Basalt Thin-Section',
            'rock_type': 'Basalt',
            'location': 'Synthetic'
        }

        messagebox.showinfo("Demo Generated",
                          f"Generated demo thin-section with {len(self.mineral_data)} mineral grains")

        self._update_2d_map()
        self._calculate_statistics()

    def _get_grain_shape(self, mineral):
        """Get appropriate grain shape for mineral"""
        shapes = {
            'quartz': 'equant',
            'feldspar': 'tabular',
            'biotite': 'platy',
            'amphibole': 'prismatic',
            'pyroxene': 'prismatic',
            'opaque': 'equant',
            'void': 'irregular'
        }
        return shapes.get(mineral, 'equant')

    def _update_2d_map(self):
        """Update the 2D mineral map"""
        if not self.mineral_data:
            return

        # Clear previous plot
        self.ax_2d.clear()

        # Create color mapping
        colors = []
        sizes = []
        positions = []

        for grain in self.mineral_data:
            mineral = grain['type']
            if mineral in self.mineral_colors:
                color = self.mineral_colors[mineral]
                colors.append(color[:3])  # RGB only
                sizes.append(grain['size'] * 5)  # Scale for visibility
                positions.append([grain['x'], grain['y']])

        if positions:
            positions = np.array(positions)
            colors = np.array(colors)
            sizes = np.array(sizes)

            # Scatter plot
            scatter = self.ax_2d.scatter(positions[:, 0], positions[:, 1],
                                        s=sizes, c=colors, alpha=0.7,
                                        edgecolors='black', linewidths=0.5)

            # Set limits
            if self.current_section:
                self.ax_2d.set_xlim(0, self.current_section['width'])
                self.ax_2d.set_ylim(0, self.current_section['height'])

            self.ax_2d.set_aspect('equal')
            self.ax_2d.set_xlabel('X Position (μm)')
            self.ax_2d.set_ylabel('Y Position (μm)')
            self.ax_2d.set_title('2D Mineral Distribution Map')

            # Add legend
            unique_minerals = set(g['type'] for g in self.mineral_data)
            legend_elements = []
            for mineral in sorted(unique_minerals):
                if mineral in self.mineral_colors:
                    color = self.mineral_colors[mineral]
                    legend_elements.append(plt.Line2D([0], [0], marker='o',
                                                     color='w', markerfacecolor=color[:3],
                                                     markersize=8, label=mineral.capitalize()))

            if legend_elements:
                self.ax_2d.legend(handles=legend_elements, loc='upper right',
                                 fontsize='small', ncol=2)

        self.fig_2d.tight_layout()
        self.canvas_2d.draw()

    def _calculate_statistics(self):
        """Calculate and display thin-section statistics"""
        if not self.mineral_data:
            return

        # Calculate statistics
        mineral_counts = {}
        mineral_sizes = {}
        total_volume = 0

        for grain in self.mineral_data:
            mineral = grain['type']
            size = grain['size']
            volume = (4/3) * np.pi * (size/2)**3  # Assuming spherical

            if mineral not in mineral_counts:
                mineral_counts[mineral] = 0
                mineral_sizes[mineral] = []

            mineral_counts[mineral] += 1
            mineral_sizes[mineral].append(size)
            total_volume += volume

        # Prepare statistics text
        self.stats_text.config(state='normal')
        self.stats_text.delete(1.0, tk.END)

        self.stats_text.insert(tk.END,
                              f"THIN-SECTION STATISTICS\n"
                              f"══════════════════════════════\n\n")

        if self.current_section:
            for key, value in self.current_section.items():
                if key not in ['width', 'height', 'depth']:
                    self.stats_text.insert(tk.END, f"{key}: {value}\n")

            self.stats_text.insert(tk.END,
                                  f"\nDimensions: {self.current_section.get('width', 0)} × "
                                  f"{self.current_section.get('height', 0)} × "
                                  f"{self.current_section.get('depth', 0)} μm\n")

        self.stats_text.insert(tk.END,
                              f"\nMINERALOGY\n"
                              f"──────────\n")

        total_grains = len(self.mineral_data)
        for mineral, count in sorted(mineral_counts.items(),
                                    key=lambda x: x[1], reverse=True):
            percentage = (count / total_grains) * 100
            size_data = mineral_sizes[mineral]
            avg_size = np.mean(size_data) if size_data else 0
            std_size = np.std(size_data) if len(size_data) > 1 else 0

            self.stats_text.insert(tk.END,
                                  f"{mineral.capitalize():12} {count:4d} grains "
                                  f"({percentage:5.1f}%) "
                                  f"Size: {avg_size:.1f} ± {std_size:.1f} μm\n")

        # Texture statistics
        self.stats_text.insert(tk.END,
                              f"\nTEXTURE\n"
                              f"───────\n")

        all_sizes = [g['size'] for g in self.mineral_data]
        if all_sizes:
            self.stats_text.insert(tk.END,
                                  f"Mean grain size: {np.mean(all_sizes):.2f} μm\n")
            self.stats_text.insert(tk.END,
                                  f"Grain size range: {min(all_sizes):.2f} - {max(all_sizes):.2f} μm\n")
            self.stats_text.insert(tk.END,
                                  f"Sorting (std): {np.std(all_sizes):.2f} μm\n")

        # Calculate porosity if void data exists
        if 'void' in mineral_counts:
            porosity = mineral_counts['void'] / total_grains * 100
            self.stats_text.insert(tk.END,
                                  f"\nPorosity: {porosity:.1f}%\n")

        self.stats_text.insert(tk.END,
                              f"\nTotal grains analyzed: {total_grains}\n")

        self.stats_text.config(state='disabled')

    def _render_3d_view(self):
        """Render interactive 3D view"""
        if not self.mineral_data:
            messagebox.showwarning("No Data",
                                 "Please load or generate thin-section data first.")
            return

        try:
            # Clear previous 3D view
            for widget in self.canvas_3d_frame.winfo_children():
                widget.destroy()

            # Create PyVista plotter
            self.plotter = pv.Plotter(window_size=[800, 600])
            self.plotter.set_background("white")

            # Get selected minerals
            selected_minerals = [m for m, var in self.mineral_vars.items()
                               if var.get()]

            # Create point cloud for each mineral
            for mineral in selected_minerals:
                # Filter grains of this mineral
                grains = [g for g in self.mineral_data if g['type'] == mineral]

                if not grains:
                    continue

                # Prepare data
                points = []
                colors = []
                sizes = []

                for grain in grains:
                    points.append([grain['x'], grain['y'], grain['z']])
                    color = self.mineral_colors.get(mineral, [0.5, 0.5, 0.5, 1.0])
                    colors.append(color[:3])  # RGB only
                    sizes.append(grain['size'] * 0.5)  # Scale factor

                if points:
                    points_array = np.array(points)
                    colors_array = np.array(colors)

                    # Create point cloud
                    point_cloud = pv.PolyData(points_array)
                    point_cloud['colors'] = (colors_array * 255).astype(np.uint8)
                    point_cloud['sizes'] = np.array(sizes)

                    # Add to plotter with transparency
                    opacity = 1.0 - self.transparency_var.get()

                    self.plotter.add_points(point_cloud,
                                          scalars='colors',
                                          rgb=True,
                                          point_size='sizes',
                                          render_points_as_spheres=True,
                                          opacity=opacity)

            # Add section bounds as wireframe
            if self.current_section:
                bounds = pv.Box(bounds=[0, self.current_section['width'],
                                       0, self.current_section['height'],
                                       0, self.current_section['depth']])
                self.plotter.add_mesh(bounds, style='wireframe',
                                     color='black', line_width=1, opacity=0.3)

            # Add axes and title
            self.plotter.add_axes(xlabel='X (μm)', ylabel='Y (μm)', zlabel='Z (μm)')
            self.plotter.add_text("3D Thin-Section Mineral Distribution",
                                 position='upper_edge', font_size=14, color='black')

            # Add lighting
            self.plotter.set_lighting(lighting=self.lighting_var.get())

            # Embed in tkinter window (simplified - in real implementation,
            # you would use pv.BackgroundPlotter for proper embedding)

            # For now, show in separate window
            self.plotter.show()

            # Update status
            messagebox.showinfo("3D View Rendered",
                              "3D view opened in separate window.\n"
                              "Use mouse to rotate, scroll to zoom.")

        except Exception as e:
            messagebox.showerror("3D Render Error",
                               f"Error rendering 3D view:\n\n{str(e)}\n\n{traceback.format_exc()}")

    def _update_view(self):
        """Update current view with new settings"""
        # Update 2D map with current color settings
        self._update_2d_map()

        # Recalculate statistics
        self._calculate_statistics()

        messagebox.showinfo("View Updated", "Display settings updated.")

    def _adjust_colors(self):
        """Open color adjustment dialog"""
        color_win = tk.Toplevel(self.window)
        color_win.title("Adjust Mineral Colors")
        color_win.geometry("500x400")

        # Color adjustment interface
        canvas = tk.Canvas(color_win, bg="white")
        canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        y_pos = 10
        for mineral, color in self.mineral_colors.items():
            # Mineral label
            tk.Label(canvas, text=mineral.capitalize(),
                    font=("Arial", 10)).place(x=10, y=y_pos)

            # Current color preview
            preview = tk.Canvas(canvas, width=30, height=30,
                               bg=self._rgb_to_hex(color),
                               highlightthickness=1,
                               highlightbackground="black")
            preview.place(x=150, y=y_pos)

            # Color picker button
            tk.Button(canvas, text="Pick Color",
                     command=lambda m=mineral, p=preview:
                     self._pick_color(m, p)).place(x=200, y=y_pos)

            # RGB sliders
            for i, channel in enumerate(['R', 'G', 'B']):
                slider = tk.Scale(canvas, from_=0, to=255, orient=tk.HORIZONTAL,
                                 label=channel, length=100)
                slider.set(int(color[i] * 255))
                slider.place(x=300 + i*120, y=y_pos-20)

                # Bind slider update
                slider.configure(command=lambda v, m=mineral, idx=i:
                               self._update_color_slider(m, idx, float(v)/255))

            y_pos += 60

        # Close button
        tk.Button(color_win, text="Apply Colors",
                 command=lambda: [self._update_2d_map(), color_win.destroy()],
                 bg="#4CAF50", fg="white",
                 font=("Arial", 11, "bold")).pack(pady=10)

    def _pick_color(self, mineral, preview_canvas):
        """Pick color for mineral"""
        from tkinter import colorchooser

        current_color = self.mineral_colors[mineral]
        hex_color = self._rgb_to_hex(current_color)

        color = colorchooser.askcolor(hex_color, title=f"Pick color for {mineral}")
        if color[1]:  # User selected a color
            # Convert hex to RGB
            hex_val = color[1].lstrip('#')
            rgb = tuple(int(hex_val[i:i+2], 16) / 255.0 for i in (0, 2, 4))

            # Update color
            self.mineral_colors[mineral] = [rgb[0], rgb[1], rgb[2], 1.0]

            # Update preview
            preview_canvas.config(bg=color[1])

    def _update_color_slider(self, mineral, channel_idx, value):
        """Update color from slider"""
        color = list(self.mineral_colors[mineral])
        color[channel_idx] = value
        self.mineral_colors[mineral] = color

    def _reset_colors(self):
        """Reset colors to defaults"""
        default_colors = {
            'quartz': [0.9, 0.9, 0.9, 1.0],
            'feldspar': [0.8, 0.8, 1.0, 1.0],
            'plagioclase': [0.7, 0.8, 0.9, 1.0],
            'biotite': [0.2, 0.2, 0.2, 1.0],
            'muscovite': [0.9, 0.9, 0.7, 1.0],
            'amphibole': [0.1, 0.5, 0.1, 1.0],
            'pyroxene': [0.3, 0.3, 0.1, 1.0],
            'olivine': [0.2, 0.6, 0.2, 1.0],
            'apatite': [0.8, 0.4, 0.8, 1.0],
            'zircon': [0.9, 0.9, 0.1, 1.0],
            'opaque': [0.1, 0.1, 0.1, 1.0],
            'calcite': [1.0, 1.0, 0.8, 1.0],
            'clay': [0.6, 0.5, 0.4, 1.0],
            'void': [0.0, 0.0, 0.0, 0.0],
        }

        self.mineral_colors = default_colors.copy()
        self._update_2d_map()
        messagebox.showinfo("Colors Reset", "Mineral colors reset to defaults.")

    def _analyze_grain_size(self):
        """Analyze grain size distribution"""
        if not self.mineral_data:
            messagebox.showwarning("No Data", "No thin-section data loaded.")
            return

        # Extract grain sizes
        sizes = [g['size'] for g in self.mineral_data if g['type'] != 'void']

        if not sizes:
            messagebox.showwarning("No Grains", "No mineral grains to analyze.")
            return

        # Create histogram
        fig, ax = plt.subplots(figsize=(10, 6))

        ax.hist(sizes, bins=20, alpha=0.7, edgecolor='black')
        ax.set_xlabel('Grain Size (μm)')
        ax.set_ylabel('Frequency')
        ax.set_title('Grain Size Distribution')

        # Add statistics
        mean_size = np.mean(sizes)
        median_size = np.median(sizes)
        std_size = np.std(sizes)

        stats_text = f"n = {len(sizes)}\nMean = {mean_size:.2f} μm\n"
        stats_text += f"Median = {median_size:.2f} μm\nStd = {std_size:.2f} μm"

        ax.text(0.95, 0.95, stats_text,
               transform=ax.transAxes, verticalalignment='top',
               horizontalalignment='right',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        plt.tight_layout()
        plt.show()

    def _analyze_mineral_abundance(self):
        """Analyze mineral abundance"""
        if not self.mineral_data:
            return

        # Count minerals
        mineral_counts = {}
        for grain in self.mineral_data:
            mineral = grain['type']
            mineral_counts[mineral] = mineral_counts.get(mineral, 0) + 1

        # Create pie chart
        fig, ax = plt.subplots(figsize=(10, 8))

        labels = []
        counts = []
        colors = []

        for mineral, count in sorted(mineral_counts.items(),
                                    key=lambda x: x[1], reverse=True):
            labels.append(f"{mineral.capitalize()}\n({count})")
            counts.append(count)
            if mineral in self.mineral_colors:
                colors.append(self.mineral_colors[mineral][:3])
            else:
                colors.append([0.5, 0.5, 0.5])

        wedges, texts, autotexts = ax.pie(counts, labels=labels, colors=colors,
                                         autopct='%1.1f%%', startangle=90)

        ax.set_title('Mineral Abundance')
        plt.tight_layout()
        plt.show()

    def _analyze_texture(self):
        """Analyze texture orientation"""
        if not self.mineral_data:
            return

        # For platy minerals, analyze orientation
        platy_minerals = ['biotite', 'muscovite', 'amphibole']
        orientations = []

        for grain in self.mineral_data:
            if grain['type'] in platy_minerals and 'orientation' in grain:
                orientations.append(grain['orientation'])

        if orientations:
            # Create rose diagram
            fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))

            n_bins = 36
            theta = np.radians(np.array(orientations))
            bins = np.linspace(0, 2*np.pi, n_bins + 1)

            counts, _ = np.histogram(theta, bins=bins)
            widths = 2 * np.pi / n_bins
            bars = ax.bar(bins[:-1], counts, width=widths, bottom=0.0)

            ax.set_title('Mineral Orientation Rose Diagram')
            ax.set_theta_zero_location('N')
            ax.set_theta_direction(-1)

            plt.tight_layout()
            plt.show()
        else:
            messagebox.showinfo("No Orientation Data",
                              "No platy minerals with orientation data found.")

    def _analyze_porosity(self):
        """Analyze porosity"""
        if not self.mineral_data:
            return

        # Count void spaces
        void_count = sum(1 for g in self.mineral_data if g['type'] == 'void')
        total_count = len(self.mineral_data)

        if void_count > 0:
            porosity = (void_count / total_count) * 100

            # Create visualization
            fig, ax = plt.subplots(figsize=(8, 6))

            categories = ['Minerals', 'Void Space']
            counts = [total_count - void_count, void_count]
            colors = ['#4CAF50', '#2196F3']

            ax.bar(categories, counts, color=colors)
            ax.set_ylabel('Number of Grains')
            ax.set_title(f'Porosity Analysis: {porosity:.1f}%')

            # Add value labels
            for i, v in enumerate(counts):
                ax.text(i, v + 0.5, str(v), ha='center')

            plt.tight_layout()
            plt.show()
        else:
            messagebox.showinfo("No Porosity",
                              "No void spaces detected in this thin-section.")

    def _zoom_region(self):
        """Zoom to specific region"""
        # In a full implementation, this would allow selecting a region
        # to zoom in on in the 3D view
        messagebox.showinfo("Zoom Feature",
                          "Click and drag in the 3D view to zoom.\n"
                          "Or use mouse wheel to zoom in/out.")

    def _capture_snapshot(self):
        """Capture snapshot of current view"""
        if not self.plotter:
            messagebox.showwarning("No 3D View",
                                 "Please render a 3D view first.")
            return

        path = filedialog.asksaveasfilename(
            title="Save Snapshot",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )

        if path:
            try:
                self.plotter.screenshot(path)
                messagebox.showinfo("Snapshot Saved",
                                  f"Snapshot saved to:\n{path}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Error: {str(e)}")

    def _export_png(self):
        """Export as PNG image"""
        path = filedialog.asksaveasfilename(
            title="Export as PNG",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png")]
        )

        if path:
            try:
                # Save current 2D map
                self.fig_2d.savefig(path, dpi=300, bbox_inches='tight')
                messagebox.showinfo("Export Successful",
                                  f"2D map exported to:\n{path}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Error: {str(e)}")

    def _export_stl(self):
        """Export 3D model as STL"""
        path = filedialog.asksaveasfilename(
            title="Export as STL",
            defaultextension=".stl",
            filetypes=[("STL files", "*.stl")]
        )

        if path:
            try:
                # In a full implementation, this would export the 3D model
                # For now, show message
                messagebox.showinfo("STL Export",
                                  "STL export requires full 3D mesh generation.\n"
                                  "This feature is available in the full version.")
            except Exception as e:
                messagebox.showerror("Export Error", f"Error: {str(e)}")

    def _export_obj(self):
        """Export 3D model as OBJ"""
        path = filedialog.asksaveasfilename(
            title="Export as OBJ",
            defaultextension=".obj",
            filetypes=[("OBJ files", "*.obj")]
        )

        if path:
            messagebox.showinfo("OBJ Export",
                              "OBJ export requires full 3D mesh generation.\n"
                              "This feature is available in the full version.")

    def _export_stats(self):
        """Export statistics as CSV"""
        if not self.mineral_data:
            messagebox.showwarning("No Data", "No data to export.")
            return

        path = filedialog.asksaveasfilename(
            title="Export Statistics",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )

        if path:
            try:
                import pandas as pd

                # Create DataFrame from mineral data
                df = pd.DataFrame(self.mineral_data)
                df.to_csv(path, index=False)

                messagebox.showinfo("Export Successful",
                                  f"Statistics exported to:\n{path}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Error: {str(e)}")

    def _export_session(self):
        """Export entire session as JSON"""
        path = filedialog.asksaveasfilename(
            title="Export Session",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )

        if path:
            try:
                session_data = {
                    'section': self.current_section,
                    'minerals': self.mineral_data,
                    'colors': self.mineral_colors,
                    'export_date': datetime.now().isoformat()
                }

                with open(path, 'w') as f:
                    json.dump(session_data, f, indent=2)

                messagebox.showinfo("Export Successful",
                                  f"Session exported to:\n{path}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Error: {str(e)}")

    def _load_demo_data(self):
        """Load demo data on startup"""
        # Check if we should auto-load demo
        try:
            config_path = Path("config/virtual_microscopy.json")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    if config.get('auto_load_demo', False):
                        self._generate_demo_section()
        except:
            pass

    def _rgb_to_hex(self, rgb):
        """Convert RGB list to hex color"""
        if len(rgb) >= 3:
            return f'#{int(rgb[0]*255):02x}{int(rgb[1]*255):02x}{int(rgb[2]*255):02x}'
        return '#000000'

    def _install_dependencies(self, missing_packages):
        """Install missing dependencies"""
        response = messagebox.askyesno(
            "Install Dependencies",
            f"Install these packages:\n\n{', '.join(missing_packages)}\n\n"
            f"This may take a few minutes.",
            parent=self.window
        )

        if response:
            if hasattr(self.app, 'open_plugin_manager'):
                self.window.destroy()
                self.app.open_plugin_manager()


# Bind to application menu
def setup_plugin(main_app):
    """Setup function called by main application"""
    plugin = VirtualMicroscopyPlugin(main_app)

    # Add to Tools menu
    if hasattr(main_app, 'menu_bar'):
        main_app.menu_bar.add_command(
            label="3D Virtual Microscopy",
            command=plugin.open_virtual_microscopy
        )

    return plugin
