"""
3D Virtual Microscopy Pro - Advanced Thin-Section Analysis
3D visualization, mineral mapping, texture analysis, and petrographic quantification

Author: Sefy Levy
License: CC BY-NC-SA 4.0
Version: 2.1 - Fixed import from data table
"""

PLUGIN_INFO = {
    "category": "software",
    "id": "virtual_microscopy_pro",
    "name": "Virtual Microscopy Pro",
    "description": "3D thin-section analysis, mineral mapping, grain size analysis, petrographic quantification",
    "icon": "🔬",
    "version": "2.1",
    "requires": ["numpy", "matplotlib", "pillow", "scipy"],
    "author": "Sefy Levy"
}

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import numpy as np
import json
import traceback
from pathlib import Path
from datetime import datetime
import os
import threading

# Optional 3D imports
try:
    from mpl_toolkits.mplot3d import Axes3D
    HAS_3D = True
except ImportError:
    HAS_3D = False

# Scientific imports
try:
    import matplotlib
    matplotlib.use('TkAgg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    from matplotlib.patches import Rectangle, Circle, Polygon
    from matplotlib.colors import LinearSegmentedColormap
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    import numpy as np
    from scipy import ndimage, stats
    from scipy.spatial import KDTree, Delaunay, Voronoi, voronoi_plot_2d
    HAS_NUMPY = True
    HAS_SCIPY = True
except ImportError:
    HAS_NUMPY = False
    HAS_SCIPY = False

try:
    from PIL import Image, ImageTk, ImageEnhance, ImageFilter
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

HAS_REQUIREMENTS = HAS_NUMPY and HAS_MATPLOTLIB and HAS_PIL


class VirtualMicroscopyProPlugin:
    """Advanced 3D Virtual Microscopy Plugin with full petrographic analysis"""

    def __init__(self, main_app):
        self.app = main_app
        self.window = None
        self.current_section = None
        self.mineral_data = []
        self.texture_data = {}
        self.grain_boundaries = None
        self.porosity_map = None
        self.mineral_composition = {}
        self.history = []  # Undo functionality
        self.history_index = -1

        # Enhanced mineral database with optical properties
        self.mineral_database = {
            'quartz': {
                'color': [0.9, 0.9, 0.9, 1.0],
                'hardness': 7,
                'birefringence': 0.009,
                'relief': 'low',
                'cleavage': 'none',
                'habit': 'equant',
                'pleochroism': 'none',
                'extinction': 'parallel',
                'twinning': 'none',
                'formula': 'SiO2'
            },
            'plagioclase': {
                'color': [0.8, 0.8, 1.0, 1.0],
                'hardness': 6,
                'birefringence': 0.007,
                'relief': 'low',
                'cleavage': 'two',
                'habit': 'tabular',
                'pleochroism': 'none',
                'extinction': 'albite',
                'twinning': 'polysynthetic',
                'formula': '(Na,Ca)AlSi3O8'
            },
            'k-feldspar': {
                'color': [1.0, 0.9, 0.8, 1.0],
                'hardness': 6,
                'birefringence': 0.007,
                'relief': 'low',
                'cleavage': 'two',
                'habit': 'prismatic',
                'pleochroism': 'none',
                'extinction': 'parallel',
                'twinning': 'carlsbad',
                'formula': 'KAlSi3O8'
            },
            'biotite': {
                'color': [0.2, 0.1, 0.1, 1.0],
                'hardness': 2.5,
                'birefringence': 0.040,
                'relief': 'moderate',
                'cleavage': 'perfect',
                'habit': 'flaky',
                'pleochroism': 'strong',
                'extinction': 'parallel',
                'twinning': 'none',
                'formula': 'K(Mg,Fe)3AlSi3O10(OH)2'
            },
            'muscovite': {
                'color': [0.9, 0.9, 0.7, 1.0],
                'hardness': 2.5,
                'birefringence': 0.035,
                'relief': 'low',
                'cleavage': 'perfect',
                'habit': 'flaky',
                'pleochroism': 'weak',
                'extinction': 'parallel',
                'twinning': 'none',
                'formula': 'KAl2(AlSi3O10)(OH)2'
            },
            'hornblende': {
                'color': [0.1, 0.4, 0.1, 1.0],
                'hardness': 5.5,
                'birefringence': 0.025,
                'relief': 'moderate',
                'cleavage': 'two',
                'habit': 'prismatic',
                'pleochroism': 'strong',
                'extinction': 'oblique',
                'twinning': 'simple',
                'formula': 'Ca2(Mg,Fe,Al)5(Al,Si)8O22(OH)2'
            },
            'augite': {
                'color': [0.2, 0.3, 0.1, 1.0],
                'hardness': 6,
                'birefringence': 0.030,
                'relief': 'high',
                'cleavage': 'two',
                'habit': 'prismatic',
                'pleochroism': 'weak',
                'extinction': 'oblique',
                'twinning': 'simple',
                'formula': '(Ca,Na)(Mg,Fe,Al,Ti)(Si,Al)2O6'
            },
            'olivine': {
                'color': [0.2, 0.6, 0.2, 1.0],
                'hardness': 6.5,
                'birefringence': 0.035,
                'relief': 'high',
                'cleavage': 'poor',
                'habit': 'equant',
                'pleochroism': 'none',
                'extinction': 'parallel',
                'twinning': 'none',
                'formula': '(Mg,Fe)2SiO4'
            },
            'apatite': {
                'color': [0.8, 0.4, 0.8, 1.0],
                'hardness': 5,
                'birefringence': 0.003,
                'relief': 'moderate',
                'cleavage': 'poor',
                'habit': 'prismatic',
                'pleochroism': 'none',
                'extinction': 'parallel',
                'twinning': 'none',
                'formula': 'Ca5(PO4)3(OH,F,Cl)'
            },
            'zircon': {
                'color': [0.9, 0.8, 0.1, 1.0],
                'hardness': 7.5,
                'birefringence': 0.050,
                'relief': 'very high',
                'cleavage': 'poor',
                'habit': 'prismatic',
                'pleochroism': 'weak',
                'extinction': 'parallel',
                'twinning': 'none',
                'formula': 'ZrSiO4'
            },
            'calcite': {
                'color': [1.0, 1.0, 0.9, 1.0],
                'hardness': 3,
                'birefringence': 0.170,
                'relief': 'variable',
                'cleavage': 'perfect',
                'habit': 'rhombohedral',
                'pleochroism': 'none',
                'extinction': 'symmetric',
                'twinning': 'polysynthetic',
                'formula': 'CaCO3'
            },
            'clay': {
                'color': [0.6, 0.5, 0.4, 1.0],
                'hardness': 1,
                'birefringence': 0.020,
                'relief': 'low',
                'cleavage': 'perfect',
                'habit': 'fibrous',
                'pleochroism': 'weak',
                'extinction': 'parallel',
                'twinning': 'none',
                'formula': 'Al2Si2O5(OH)4'
            },
            'opaque': {
                'color': [0.1, 0.1, 0.1, 1.0],
                'hardness': 5,
                'birefringence': 0,
                'relief': 'very high',
                'cleavage': 'none',
                'habit': 'massive',
                'pleochroism': 'none',
                'extinction': 'none',
                'twinning': 'none',
                'formula': 'Fe-Ti oxides'
            },
            'void': {
                'color': [0.0, 0.0, 0.0, 0.0],
                'hardness': 0,
                'birefringence': 0,
                'relief': 'none',
                'cleavage': 'none',
                'habit': 'none',
                'pleochroism': 'none',
                'extinction': 'none',
                'twinning': 'none',
                'formula': 'porosity'
            }
        }

        # Initialize mineral colors from database
        self.mineral_colors = {name: props['color'] for name, props in self.mineral_database.items()}

        # UI elements
        self.fig = None
        self.ax = None
        self.canvas = None
        self.mineral_vars = {}
        self.status_var = None
        self.progress_bar = None

    # ============================================================================
    # SAFE FLOAT UTILITY METHOD - FIXES THE MISSING METHOD ERROR
    # ============================================================================
    def _safe_float(self, value):
        """Safely convert value to float, return None if conversion fails"""
        if value is None or value == '':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    # ============================================================================
    # WINDOW MANAGEMENT
    # ============================================================================
    def open_window(self):
        """Main entry point - opens the virtual microscopy window"""
        if not HAS_REQUIREMENTS:
            missing = []
            if not HAS_NUMPY: missing.append("numpy")
            if not HAS_MATPLOTLIB: missing.append("matplotlib")
            if not HAS_PIL: missing.append("pillow")
            if not HAS_SCIPY: missing.append("scipy")

            messagebox.showerror(
                "Missing Dependencies",
                f"Virtual Microscopy Pro requires:\n\n" +
                "\n".join(f"• {pkg}" for pkg in missing) +
                f"\n\nInstall with:\npip install {' '.join(missing)}"
            )
            return

        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("🔬 Virtual Microscopy Pro v2.1")
        self.window.geometry("1400x800")
        self.window.minsize(1200, 700)
        self.window.transient(self.app.root)

        self._create_interface()
        self._generate_demo_data()
        self.window.lift()
        self.window.focus_force()

    # ============================================================================
    # INTERFACE CREATION
    # ============================================================================
    def _create_interface(self):
        """Create the main interface with modern layout"""
        # Header
        header = tk.Frame(self.window, bg="#2c3e50", height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="🔬", font=("Arial", 24),
                bg="#2c3e50", fg="white").pack(side=tk.LEFT, padx=10)

        tk.Label(header, text="Virtual Microscopy Pro",
                font=("Arial", 18, "bold"),
                bg="#2c3e50", fg="white").pack(side=tk.LEFT, padx=5)

        tk.Label(header, text="3D Thin-Section Analysis | Mineral Mapping | Petrographic Quantification",
                font=("Arial", 10),
                bg="#2c3e50", fg="#b0c4de").pack(side=tk.LEFT, padx=15)

        # Main container with paned windows
        main_paned = tk.PanedWindow(self.window, orient=tk.HORIZONTAL,
                                   sashwidth=6, sashrelief=tk.RAISED)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left panel - Controls
        left_panel = tk.Frame(main_paned, bg="#f5f5f5", relief=tk.RAISED, borderwidth=1)
        main_paned.add(left_panel, width=400, minsize=350)

        # Right panel - Visualization
        right_panel = tk.Frame(main_paned, bg="white", relief=tk.RAISED, borderwidth=1)
        main_paned.add(right_panel, width=950, minsize=800)

        self._setup_control_panel(left_panel)
        self._setup_visualization_panel(right_panel)

        # Status bar
        status_bar = tk.Frame(self.window, bg="#ecf0f1", height=30)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        status_bar.pack_propagate(False)

        self.status_var = tk.StringVar(value="Ready - Load or generate thin-section data")
        tk.Label(status_bar, textvariable=self.status_var,
                font=("Arial", 9), bg="#ecf0f1", fg="#2c3e50").pack(side=tk.LEFT, padx=10)

        self.progress_bar = ttk.Progressbar(status_bar, mode='indeterminate', length=200)
        self.progress_bar.pack(side=tk.RIGHT, padx=10, pady=5)

    def _setup_control_panel(self, parent):
        """Setup comprehensive control panel"""
        # Create notebook for categorized controls
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # === TAB 1: FILE OPERATIONS ===
        file_tab = tk.Frame(notebook, bg="#f5f5f5")
        notebook.add(file_tab, text="📁 File")

        # Data source section
        src_frame = tk.LabelFrame(file_tab, text="Data Source", padx=10, pady=10, bg="#f5f5f5")
        src_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Button(src_frame, text="📥 IMPORT FROM DATA TABLE (MAIN APP)",
                 command=self._import_from_data_table,
                 bg="#27ae60", fg="white", width=30, height=2,
                 font=("Arial", 10, "bold")).pack(pady=5)

        tk.Button(src_frame, text="📂 Load Image (Thin-Section)",
                 command=self._load_image,
                 bg="#3498db", fg="white", width=30).pack(pady=2)

        tk.Button(src_frame, text="📋 Load JSON (Full Analysis)",
                 command=self._load_json,
                 bg="#3498db", fg="white", width=30).pack(pady=2)

        tk.Button(src_frame, text="🎲 Generate Synthetic Section",
                 command=self._generate_demo_data,
                 bg="#9b59b6", fg="white", width=30).pack(pady=5)

        # Export section
        export_frame = tk.LabelFrame(file_tab, text="Export", padx=10, pady=10, bg="#f5f5f5")
        export_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Button(export_frame, text="💾 Save Image",
                 command=self._save_image,
                 bg="#27ae60", fg="white", width=14).pack(side=tk.LEFT, padx=2)

        tk.Button(export_frame, text="📄 Export Report",
                 command=self._export_report,
                 bg="#27ae60", fg="white", width=14).pack(side=tk.LEFT, padx=2)

        tk.Button(export_frame, text="📊 Export Data (JSON)",
                 command=self._export_data,
                 bg="#27ae60", fg="white", width=14).pack(side=tk.LEFT, padx=2)

        # === TAB 2: MINERAL MAPPING ===
        mineral_tab = tk.Frame(notebook, bg="#f5f5f5")
        notebook.add(mineral_tab, text="🧪 Minerals")

        # Mineral selection with color preview
        select_frame = tk.LabelFrame(mineral_tab, text="Show Minerals", padx=10, pady=10, bg="#f5f5f5")
        select_frame.pack(fill=tk.X, padx=5, pady=5)

        # Create scrollable frame for minerals
        canvas = tk.Canvas(select_frame, bg="#f5f5f5", height=300)
        scrollbar = tk.Scrollbar(select_frame, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas, bg="#f5f5f5")

        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        self.mineral_vars = {}
        for mineral in sorted(self.mineral_database.keys()):
            if mineral != 'void':
                var = tk.BooleanVar(value=True)
                self.mineral_vars[mineral] = var

                frame = tk.Frame(scrollable, bg="#f5f5f5")
                frame.pack(fill=tk.X, pady=1)

                cb = tk.Checkbutton(frame, text=mineral.capitalize(),
                                   variable=var, bg="#f5f5f5",
                                   font=("Arial", 9))
                cb.pack(side=tk.LEFT)

                # Color preview
                color = self.mineral_colors.get(mineral, [0.5, 0.5, 0.5])
                hex_color = self._rgb_to_hex(color)
                preview = tk.Canvas(frame, width=20, height=20, bg=hex_color,
                                   highlightthickness=1, highlightbackground="black")
                preview.pack(side=tk.RIGHT, padx=5)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Control buttons
        btn_frame = tk.Frame(mineral_tab, bg="#f5f5f5")
        btn_frame.pack(fill=tk.X, pady=5)

        tk.Button(btn_frame, text="Select All",
                 command=lambda: self._set_all_minerals(True),
                 width=12).pack(side=tk.LEFT, padx=2)

        tk.Button(btn_frame, text="Clear All",
                 command=lambda: self._set_all_minerals(False),
                 width=12).pack(side=tk.LEFT, padx=2)

        tk.Button(btn_frame, text="Apply",
                 command=self._update_plot,
                 bg="#27ae60", fg="white").pack(side=tk.RIGHT, padx=2)

        # === TAB 3: ANALYSIS ===
        analysis_tab = tk.Frame(notebook, bg="#f5f5f5")
        notebook.add(analysis_tab, text="📊 Analysis")

        # Quantitative analysis
        quant_frame = tk.LabelFrame(analysis_tab, text="Quantitative", padx=10, pady=10, bg="#f5f5f5")
        quant_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Button(quant_frame, text="📊 Modal Analysis (%)",
                 command=self._modal_analysis,
                 width=25).pack(pady=2)

        tk.Button(quant_frame, text="📏 Grain Size Distribution",
                 command=self._grain_size_analysis,
                 width=25).pack(pady=2)

        tk.Button(quant_frame, text="🧮 Grain Shape Analysis",
                 command=self._shape_analysis,
                 width=25).pack(pady=2)

        tk.Button(quant_frame, text="🔄 Grain Orientation",
                 command=self._orientation_analysis,
                 width=25).pack(pady=2)

        # Texture analysis
        texture_frame = tk.LabelFrame(analysis_tab, text="Texture", padx=10, pady=10, bg="#f5f5f5")
        texture_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Button(texture_frame, text="🌋 Porosity Analysis",
                 command=self._porosity_analysis,
                 width=25).pack(pady=2)

        tk.Button(texture_frame, text="🔄 Grain Boundary Map",
                 command=self._grain_boundary_analysis,
                 width=25).pack(pady=2)

        tk.Button(texture_frame, text="📈 Fabric Analysis",
                 command=self._fabric_analysis,
                 width=25).pack(pady=2)

        # === TAB 4: VISUALIZATION ===
        viz_tab = tk.Frame(notebook, bg="#f5f5f5")
        notebook.add(viz_tab, text="🎨 Display")

        # Display settings
        disp_frame = tk.LabelFrame(viz_tab, text="Display Settings", padx=10, pady=10, bg="#f5f5f5")
        disp_frame.pack(fill=tk.X, padx=5, pady=5)

        # Point size
        tk.Label(disp_frame, text="Grain Size:", bg="#f5f5f5").pack(anchor=tk.W)
        self.size_var = tk.DoubleVar(value=50)
        tk.Scale(disp_frame, from_=10, to=200, orient=tk.HORIZONTAL,
                variable=self.size_var, command=lambda x: self._update_plot()).pack(fill=tk.X)

        # Transparency
        tk.Label(disp_frame, text="Transparency:", bg="#f5f5f5").pack(anchor=tk.W)
        self.alpha_var = tk.DoubleVar(value=0.7)
        tk.Scale(disp_frame, from_=0.1, to=1.0, resolution=0.1,
                orient=tk.HORIZONTAL, variable=self.alpha_var,
                command=lambda x: self._update_plot()).pack(fill=tk.X)

        # View mode
        view_frame = tk.LabelFrame(viz_tab, text="View Mode", padx=10, pady=10, bg="#f5f5f5")
        view_frame.pack(fill=tk.X, padx=5, pady=5)

        self.view_mode = tk.StringVar(value="2D")
        tk.Radiobutton(view_frame, text="2D Map", variable=self.view_mode,
                      value="2D", bg="#f5f5f5",
                      command=self._update_plot).pack(anchor=tk.W)

        if HAS_3D:
            tk.Radiobutton(view_frame, text="3D Scatter", variable=self.view_mode,
                          value="3D", bg="#f5f5f5",
                          command=self._update_plot).pack(anchor=tk.W)

        # === TAB 5: HELP ===
        help_tab = tk.Frame(notebook, bg="#f5f5f5")
        notebook.add(help_tab, text="❓ Help")

        help_text = scrolledtext.ScrolledText(help_tab, wrap=tk.WORD,
                                             font=("Arial", 9), height=20)
        help_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        help_content = """
VIRTUAL MICROSCOPY PRO v2.1 - USER GUIDE
═══════════════════════════════════════════════════════════

OVERVIEW
───────────────────────────────────────────────────────────
Professional thin-section analysis software with 3D visualization
and quantitative petrographic analysis capabilities.

PRIMARY DATA SOURCE
───────────────────────────────────────────────────────────
📥 IMPORT FROM DATA TABLE (MAIN APP)
  • Uses your geochemical data to generate virtual thin-sections
  • Maps element concentrations (SiO2, Al2O3, etc.) to minerals
  • Uses Latitude/Longitude for sample positioning
  • Scales grain abundance by concentration values
  • Tracks provenance through Sample IDs

FEATURES
───────────────────────────────────────────────────────────

📁 FILE OPERATIONS
  • Import from main app data table (PRIMARY)
  • Load thin-section images (JPG, PNG, TIFF)
  • Load complete JSON analyses
  • Generate synthetic granite sections
  • Export images and data reports

🧪 MINERAL MAPPING
  • Toggle mineral visibility
  • Color-coded mineral identification
  • Database of optical properties
  • Interactive mineral selection

📊 QUANTITATIVE ANALYSIS
  • Modal analysis (% composition)
  • Grain size distribution
  • Shape analysis (circularity, aspect ratio)
  • Grain orientation (rose diagrams)
  • Statistical summaries

🌋 TEXTURE ANALYSIS
  • Porosity calculation
  • Grain boundary mapping
  • Fabric analysis
  • 3D distribution visualization

KEYBOARD SHORTCUTS
───────────────────────────────────────────────────────────
Ctrl+L    Load image
Ctrl+S    Save image
Ctrl+E    Export data
Ctrl+R    Generate demo
F5        Refresh plot
Ctrl+Q    Close window

MINERAL PROPERTIES
───────────────────────────────────────────────────────────
Click "Show Statistics" for detailed mineral information
including hardness, birefringence, cleavage, and optical
characteristics for provenance interpretation.

INTERPRETATION TIPS
───────────────────────────────────────────────────────────
• Grain size distribution → cooling history
• Mineral shape → crystallization order
• Orientation → deformation/fabric
• Porosity → alteration/diagenesis
• Mineral assemblage → rock type/provenance
        """
        help_text.insert('1.0', help_content)
        help_text.config(state=tk.DISABLED)

    def _setup_visualization_panel(self, parent):
        """Setup the visualization panel with matplotlib"""
        # Create figure with subplots
        if HAS_3D:
            self.fig = plt.figure(figsize=(12, 8), dpi=100)
            self.ax = self.fig.add_subplot(111)
        else:
            self.fig, self.ax = plt.subplots(figsize=(12, 8))

        self.fig.patch.set_facecolor('white')
        self.ax.set_facecolor('#f8f9fa')

        self.canvas = FigureCanvasTkAgg(self.fig, parent)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Add toolbar
        toolbar_frame = tk.Frame(parent)
        toolbar_frame.pack(fill=tk.X, padx=5)
        toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        toolbar.update()

        # Initial placeholder
        self.ax.text(0.5, 0.5, "Virtual Microscopy Pro\n\nImport from Data Table or generate data to begin",
                    ha='center', va='center', fontsize=14, color='gray',
                    transform=self.ax.transAxes)
        self.ax.set_axis_off()
        self.canvas.draw()

    # ============================================================================
    # IMPORT FROM DATA TABLE (PRIMARY DATA SOURCE)
    # ============================================================================
    def _import_from_data_table(self):
        """Import data from main app's dynamic table - PRIMARY DATA SOURCE"""
        if not self.app.samples:
            messagebox.showwarning("No Data", "No data in main application table.")
            return

        self.status_var.set("🔄 Importing data from main table...")
        self.progress_bar.start()
        self.window.update()

        try:
            # Clear existing data
            self.mineral_data = []

            # Get all samples
            samples = self.app.samples
            sample_count = len(samples)

            # Get available columns
            if hasattr(self.app, 'active_headers') and self.app.active_headers:
                headers = self.app.active_headers
            else:
                headers = list(samples[0].keys()) if samples else []

            # ============ STEP 1: IDENTIFY COORDINATE COLUMNS ============
            x_col = None
            y_col = None

            for col in headers:
                col_lower = col.lower()
                if any(term in col_lower for term in ['lon', 'long', 'longitude', 'x', 'easting']):
                    x_col = col
                if any(term in col_lower for term in ['lat', 'latitude', 'y', 'northing']):
                    y_col = col

            # ============ STEP 2: IDENTIFY ELEMENT/MINERAL COLUMNS ============
            # Map common element names to mineral types
            element_to_mineral = {
                'si': 'quartz',
                'sio2': 'quartz',
                'sio₂': 'quartz',
                'al': 'plagioclase',
                'al2o3': 'plagioclase',
                'al₂o₃': 'plagioclase',
                'k': 'k-feldspar',
                'k2o': 'k-feldspar',
                'k₂o': 'k-feldspar',
                'na': 'plagioclase',
                'na2o': 'plagioclase',
                'na₂o': 'plagioclase',
                'ca': 'plagioclase',
                'cao': 'plagioclase',
                'cao': 'plagioclase',
                'mg': 'biotite',
                'mgo': 'biotite',
                'mgo': 'biotite',
                'fe': 'biotite',
                'feo': 'biotite',
                'fe2o3': 'biotite',
                'fe₂o₃': 'biotite',
                'ti': 'ilmenite',
                'tio2': 'ilmenite',
                'tio₂': 'ilmenite',
                'mn': 'opaque',
                'mno': 'opaque',
                'p': 'apatite',
                'p2o5': 'apatite',
                'p₂o₅': 'apatite',
                'zr': 'zircon',
                'zro2': 'zircon',
                'zro₂': 'zircon',
                'cr': 'chromite',
                'ni': 'olivine',
                'ba': 'k-feldspar',
                'rb': 'biotite',
                'sr': 'plagioclase',
                'y': 'xenotime',
                'th': 'monazite',
                'u': 'uraninite'
            }

            # Also look for explicit mineral names
            mineral_keywords = {
                'quartz': ['quartz', 'qtz', 'q'],
                'plagioclase': ['plagioclase', 'plag', 'pl'],
                'k-feldspar': ['k-feldspar', 'kfeldspar', 'orthoclase', 'kfs'],
                'biotite': ['biotite', 'bt', 'biot'],
                'muscovite': ['muscovite', 'ms', 'musc'],
                'hornblende': ['hornblende', 'hbl', 'hb'],
                'augite': ['augite', 'aug', 'cpx'],
                'olivine': ['olivine', 'ol'],
                'apatite': ['apatite', 'ap'],
                'zircon': ['zircon', 'zrn'],
                'calcite': ['calcite', 'cc'],
                'clay': ['clay', 'cl'],
                'opaque': ['opaque', 'op', 'oxides', 'mt', 'ilm']
            }

            # Build mapping of data columns to mineral types
            mineral_columns = {}

            # First pass: look for explicit mineral names
            for mineral, keywords in mineral_keywords.items():
                for col in headers:
                    col_lower = col.lower()
                    if any(kw in col_lower for kw in keywords):
                        mineral_columns[mineral] = col
                        break

            # Second pass: look for element names
            for element, mineral in element_to_mineral.items():
                if mineral not in mineral_columns:  # Only if not already mapped
                    for col in headers:
                        col_lower = col.lower()
                        if element in col_lower and ('ppm' in col_lower or 'wt' in col_lower or col_lower.endswith(element)):
                            mineral_columns[mineral] = col
                            break

            # If still no columns found, use trace elements as proxies
            if not mineral_columns:
                trace_proxies = {
                    'Zr': 'zircon',
                    'Cr': 'chromite',
                    'Ni': 'olivine',
                    'Ba': 'k-feldspar',
                    'Sr': 'plagioclase',
                    'Rb': 'biotite',
                    'La': 'monazite',
                    'Ce': 'monazite',
                    'Y': 'xenotime',
                    'V': 'magnetite'
                }

                for trace, mineral in trace_proxies.items():
                    for col in headers:
                        if trace.lower() in col.lower() and 'ppm' in col.lower():
                            mineral_columns[mineral] = col
                            break

            # ============ STEP 3: GENERATE GRAINS FROM DATA ============
            grains_per_sample = max(5, 50 // sample_count) if sample_count > 0 else 10

            for sample_idx, sample in enumerate(samples):
                sample_id = sample.get('Sample_ID', f'Sample_{sample_idx+1:03d}')

                # Get coordinates if available
                if x_col and y_col:
                    x_base = self._safe_float(sample.get(x_col, 0))
                    y_base = self._safe_float(sample.get(y_col, 0))
                    # Scale to reasonable plot size
                    if x_base is not None and y_base is not None:
                        x_base = x_base * 10
                        y_base = y_base * 10
                else:
                    # Arrange in grid if no coordinates
                    grid_cols = 5
                    x_base = (sample_idx % grid_cols) * 40
                    y_base = (sample_idx // grid_cols) * 40

                # Skip if no valid position
                if x_base is None or y_base is None:
                    continue

                # Generate grains for each mineral in this sample
                for mineral, col in mineral_columns.items():
                    value = self._safe_float(sample.get(col, 0))

                    if value and value > 0:
                        # Scale number of grains by concentration
                        # Normalize to 0-100 scale for reasonable grain counts
                        norm_value = min(100, value / 10) if value > 100 else value
                        n_grains = max(1, int(norm_value / 10))

                        for i in range(n_grains):
                            # Create grain with realistic variation
                            grain = {
                                'type': mineral,
                                'x': x_base + np.random.uniform(-15, 15),
                                'y': y_base + np.random.uniform(-15, 15),
                                'z': np.random.uniform(0, 15),
                                'size': np.random.lognormal(2, 0.5) * (norm_value / 50),
                                'aspect_ratio': np.random.uniform(0.3, 1.0) if mineral in ['biotite', 'muscovite'] else np.random.uniform(0.7, 1.3),
                                'angle': np.random.uniform(0, 180),
                                'shape': np.random.choice(['equant', 'tabular', 'prismatic', 'flaky']),
                                'sample_id': sample_id,
                                'concentration': value
                            }
                            self.mineral_data.append(grain)

            if not self.mineral_data:
                self.progress_bar.stop()
                messagebox.showwarning("No Data",
                    "Could not generate mineral data from samples.\n"
                    "Make sure your data has element concentration columns (e.g., SiO2, Al2O3, Zr_ppm, etc.)")
                return

            # ============ STEP 4: CREATE SECTION METADATA ============
            self.current_section = {
                'width': max(g['x'] for g in self.mineral_data) + 50,
                'height': max(g['y'] for g in self.mineral_data) + 50,
                'depth': 20,
                'name': 'Data Table Import',
                'rock_type': 'Unknown (from geochemical data)',
                'location': 'Imported from main app',
                'samples_used': sample_count,
                'minerals_detected': list(set(g['type'] for g in self.mineral_data)),
                'columns_mapped': mineral_columns,
                'import_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            # ============ STEP 5: UPDATE UI ============
            self.progress_bar.stop()

            # Auto-select minerals that have data
            minerals_present = set(g['type'] for g in self.mineral_data)
            for mineral, var in self.mineral_vars.items():
                var.set(mineral in minerals_present)

            self.status_var.set(f"✅ Imported {len(self.mineral_data)} grains from {sample_count} samples")

            # Show import summary
            summary = f"Import Complete!\n\n"
            summary += f"• {len(self.mineral_data)} grains generated\n"
            summary += f"• {sample_count} samples processed\n"
            summary += f"• {len(minerals_present)} mineral types identified\n"
            summary += f"• Coordinates: {'Yes' if x_col and y_col else 'No (grid layout)'}\n\n"
            summary += "Minerals found:\n"
            for mineral in sorted(minerals_present):
                count = sum(1 for g in self.mineral_data if g['type'] == mineral)
                summary += f"  • {mineral.capitalize()}: {count} grains\n"

            messagebox.showinfo("Import Complete", summary)

            self._update_plot()

        except Exception as e:
            self.progress_bar.stop()
            messagebox.showerror("Import Error", f"Failed to import data:\n{str(e)}")
            import traceback
            traceback.print_exc()

    # ============================================================================
    # DATA GENERATION AND LOADING
    # ============================================================================
    def _generate_demo_data(self):
        """Generate realistic synthetic thin-section data"""
        self.status_var.set("Generating synthetic granite thin-section...")
        self.progress_bar.start()
        self.window.update()

        np.random.seed(42)

        # Create section dimensions
        width, height, depth = 200, 200, 20

        # Granite mineral proportions
        mineral_types = ['quartz', 'plagioclase', 'k-feldspar', 'biotite', 'muscovite', 'opaque', 'void']
        proportions = [0.30, 0.35, 0.20, 0.08, 0.03, 0.02, 0.02]

        total_grains = 750
        self.mineral_data = []

        # Generate grains with realistic clustering
        for mineral, prop in zip(mineral_types, proportions):
            n_grains = int(total_grains * prop)

            # Create clusters for certain minerals
            if mineral in ['biotite', 'muscovite']:
                # Mica minerals cluster
                cluster_centers = np.random.uniform(0, width, (n_grains // 10, 2))
                for center in cluster_centers:
                    for _ in range(10):
                        if len(self.mineral_data) >= n_grains:
                            break
                        x = center[0] + np.random.normal(0, 15)
                        y = center[1] + np.random.normal(0, 15)
                        if 0 <= x <= width and 0 <= y <= height:
                            grain = {
                                'type': mineral,
                                'x': x,
                                'y': y,
                                'z': np.random.uniform(0, depth),
                                'size': np.random.lognormal(2, 0.5),
                                'aspect_ratio': np.random.uniform(0.3, 1.0) if mineral in ['biotite', 'muscovite'] else 1.0,
                                'angle': np.random.uniform(0, 180),
                                'shape': 'flaky' if mineral in ['biotite', 'muscovite'] else 'equant'
                            }
                            self.mineral_data.append(grain)
            else:
                # Random distribution for other minerals
                for _ in range(n_grains):
                    grain = {
                        'type': mineral,
                        'x': np.random.uniform(0, width),
                        'y': np.random.uniform(0, height),
                        'z': np.random.uniform(0, depth),
                        'size': np.random.lognormal(2, 0.4),
                        'aspect_ratio': 1.0,
                        'angle': 0,
                        'shape': 'equant'
                    }
                    self.mineral_data.append(grain)

        self.current_section = {
            'width': width,
            'height': height,
            'depth': depth,
            'name': 'Synthetic Granite',
            'rock_type': 'Granite',
            'location': 'Laboratory',
            'magnification': '10x',
            'staining': 'None'
        }

        self.progress_bar.stop()
        self.status_var.set(f"✅ Generated synthetic granite with {len(self.mineral_data)} grains")
        self._update_plot()

    def _load_image(self):
        """Load and process a thin-section image"""
        path = filedialog.askopenfilename(
            title="Load Thin-Section Image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.tif *.tiff *.bmp"),
                ("All files", "*.*")
            ]
        )

        if not path:
            return

        try:
            self.status_var.set("Processing image...")
            self.progress_bar.start()
            self.window.update()

            from PIL import Image
            import numpy as np

            # Load image
            img = Image.open(path)
            img_array = np.array(img)

            # Convert to grayscale if RGB
            if len(img_array.shape) == 3:
                img_gray = np.mean(img_array, axis=2).astype(np.uint8)
            else:
                img_gray = img_array

            height, width = img_gray.shape
            self.mineral_data = []

            # Intelligent sampling based on image features
            step = max(5, min(width, height) // 100)

            # Use simple segmentation
            for y in range(0, height, step):
                for x in range(0, width, step):
                    # Get local region
                    y1 = max(0, y - step//2)
                    y2 = min(height, y + step//2)
                    x1 = max(0, x - step//2)
                    x2 = min(width, x + step//2)

                    region = img_gray[y1:y2, x1:x2]
                    mean_val = np.mean(region)

                    # Classify based on intensity
                    if mean_val > 200:
                        mineral_type = 'quartz'
                    elif mean_val > 170:
                        mineral_type = 'plagioclase'
                    elif mean_val > 140:
                        mineral_type = 'k-feldspar'
                    elif mean_val > 110:
                        mineral_type = 'biotite'
                    elif mean_val > 80:
                        mineral_type = 'amphibole'
                    elif mean_val > 50:
                        mineral_type = 'opaque'
                    else:
                        mineral_type = 'void'

                    # Estimate grain size from local variance
                    local_std = np.std(region)
                    size = max(1, local_std / 10)

                    grain = {
                        'type': mineral_type,
                        'x': x,
                        'y': y,
                        'z': 0,
                        'size': size,
                        'aspect_ratio': 1.0,
                        'angle': 0,
                        'shape': 'equant'
                    }
                    self.mineral_data.append(grain)

            self.current_section = {
                'width': width,
                'height': height,
                'depth': 10,
                'name': Path(path).stem,
                'rock_type': 'Unknown',
                'location': 'Imported',
                'magnification': 'Unknown',
                'source_file': path
            }

            self.progress_bar.stop()
            self.status_var.set(f"✅ Loaded {len(self.mineral_data)} grains from {Path(path).name}")
            self._update_plot()

        except Exception as e:
            self.progress_bar.stop()
            messagebox.showerror("Load Error", f"Failed to load image:\n{str(e)}")

    def _load_json(self):
        """Load JSON analysis file"""
        path = filedialog.askopenfilename(
            title="Load JSON Analysis",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if not path:
            return

        try:
            with open(path, 'r') as f:
                data = json.load(f)

            self.current_section = data.get('section', {})
            self.mineral_data = data.get('minerals', [])
            self.texture_data = data.get('texture', {})

            self.status_var.set(f"✅ Loaded analysis from {Path(path).name}")
            self._update_plot()

        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load JSON:\n{str(e)}")

    # ============================================================================
    # PLOT UPDATING
    # ============================================================================
    def _update_plot(self):
        """Update the visualization with current settings"""
        if not self.mineral_data:
            return

        self.ax.clear()

        # Filter minerals
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
            x_vals = [g['x'] for g in filtered_data]
            y_vals = [g['y'] for g in filtered_data]
            colors = []
            sizes = []

            for grain in filtered_data:
                mineral = grain.get('type', 'unknown')
                color = self.mineral_colors.get(mineral, [0.5, 0.5, 0.5])
                colors.append(color[:3])
                base_size = grain.get('size', 1)
                sizes.append(base_size * self.size_var.get())

            # Create scatter plot
            scatter = self.ax.scatter(x_vals, y_vals,
                                     s=sizes,
                                     c=colors,
                                     alpha=self.alpha_var.get(),
                                     edgecolors='black',
                                     linewidths=0.3)

            # Set plot limits
            if self.current_section:
                self.ax.set_xlim(0, self.current_section.get('width', 200))
                self.ax.set_ylim(0, self.current_section.get('height', 200))

            self.ax.set_aspect('equal')
            self.ax.set_xlabel('X Position (μm)', fontsize=10)
            self.ax.set_ylabel('Y Position (μm)', fontsize=10)

            # Add title with rock type
            if self.current_section:
                rock_type = self.current_section.get('rock_type', 'Unknown')
                name = self.current_section.get('name', 'Thin Section')
                self.ax.set_title(f"{name} - {rock_type}\n{len(filtered_data)} grains displayed",
                                 fontsize=12, fontweight='bold', pad=15)

            # Add legend for minerals present
            unique_minerals = set(g['type'] for g in filtered_data)
            legend_handles = []
            for mineral in sorted(unique_minerals):
                if mineral in self.mineral_colors:
                    color = self.mineral_colors[mineral]
                    handle = plt.Line2D([0], [0], marker='o', color='w',
                                       markerfacecolor=color[:3],
                                       markersize=8, label=mineral.capitalize())
                    legend_handles.append(handle)

            if legend_handles:
                self.ax.legend(handles=legend_handles, loc='upper right',
                              fontsize=8, ncol=2, framealpha=0.9)

            # Add scale bar
            scale_length = 50  # μm
            scale_x = self.ax.get_xlim()[0] + 10
            scale_y = self.ax.get_ylim()[0] + 10
            self.ax.plot([scale_x, scale_x + scale_length], [scale_y, scale_y],
                        'k-', linewidth=3)
            self.ax.text(scale_x + scale_length/2, scale_y - 5,
                        f'{scale_length} μm', ha='center', fontsize=8)

        self.fig.tight_layout()
        self.canvas.draw()

    # ============================================================================
    # ANALYSIS METHODS
    # ============================================================================
    def _modal_analysis(self):
        """Calculate modal mineral percentages"""
        if not self.mineral_data:
            messagebox.showwarning("No Data", "No mineral data to analyze.")
            return

        total_grains = len(self.mineral_data)
        mineral_counts = {}
        mineral_areas = {}

        for grain in self.mineral_data:
            mineral = grain['type']
            size = grain['size']
            area = np.pi * (size/2)**2  # Approximate area

            mineral_counts[mineral] = mineral_counts.get(mineral, 0) + 1
            mineral_areas[mineral] = mineral_areas.get(mineral, 0) + area

        # Create results window
        results_win = tk.Toplevel(self.window)
        results_win.title("Modal Analysis Results")
        results_win.geometry("600x500")

        # Create notebook for different views
        notebook = ttk.Notebook(results_win)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Tab 1: Numbers-based
        num_tab = tk.Frame(notebook)
        notebook.add(num_tab, text="By Grain Count")

        num_text = scrolledtext.ScrolledText(num_tab, wrap=tk.WORD, font=("Courier", 10))
        num_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        report = []
        report.append("MODAL ANALYSIS - BY GRAIN COUNT")
        report.append("=" * 60)
        report.append("")
        report.append(f"{'Mineral':<20} {'Count':<10} {'Percentage':<12}")
        report.append("-" * 42)

        for mineral in sorted(mineral_counts.keys(), key=lambda x: mineral_counts[x], reverse=True):
            count = mineral_counts[mineral]
            pct = (count / total_grains) * 100
            report.append(f"{mineral.capitalize():<20} {count:<10} {pct:>6.2f}%")

        report.append("")
        report.append(f"Total grains: {total_grains}")
        report.append(f"Mineral types: {len(mineral_counts)}")

        num_text.insert('1.0', '\n'.join(report))
        num_text.config(state=tk.DISABLED)

        # Tab 2: Area-based
        area_tab = tk.Frame(notebook)
        notebook.add(area_tab, text="By Area %")

        area_text = scrolledtext.ScrolledText(area_tab, wrap=tk.WORD, font=("Courier", 10))
        area_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        total_area = sum(mineral_areas.values())

        report2 = []
        report2.append("MODAL ANALYSIS - BY AREA %")
        report2.append("=" * 60)
        report2.append("")
        report2.append(f"{'Mineral':<20} {'Area (μm²)':<15} {'Percentage':<12}")
        report2.append("-" * 47)

        for mineral in sorted(mineral_areas.keys(), key=lambda x: mineral_areas[x], reverse=True):
            area = mineral_areas[mineral]
            pct = (area / total_area) * 100
            report2.append(f"{mineral.capitalize():<20} {area:>10.2f}     {pct:>6.2f}%")

        report2.append("")
        report2.append(f"Total area: {total_area:.2f} μm²")

        area_text.insert('1.0', '\n'.join(report2))
        area_text.config(state=tk.DISABLED)

        # Tab 3: Chart
        chart_tab = tk.Frame(notebook)
        notebook.add(chart_tab, text="Chart")

        fig, ax = plt.subplots(figsize=(6, 4))

        minerals = list(mineral_counts.keys())
        counts = list(mineral_counts.values())
        colors = [self.mineral_colors.get(m, [0.5, 0.5, 0.5])[:3] for m in minerals]

        wedges, texts, autotexts = ax.pie(counts, labels=minerals,
                                          autopct='%1.1f%%',
                                          colors=colors,
                                          textprops={'fontsize': 8})
        ax.set_title('Mineral Distribution by Count', fontweight='bold')

        canvas = FigureCanvasTkAgg(fig, chart_tab)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _grain_size_analysis(self):
        """Analyze grain size distribution"""
        if not self.mineral_data:
            messagebox.showwarning("No Data", "No mineral data to analyze.")
            return

        sizes = [g['size'] for g in self.mineral_data if g['type'] != 'void']

        if len(sizes) < 3:
            messagebox.showwarning("Insufficient Data", "Not enough grains for size analysis.")
            return

        # Calculate statistics
        mean_size = np.mean(sizes)
        median_size = np.median(sizes)
        std_size = np.std(sizes)
        min_size = np.min(sizes)
        max_size = np.max(sizes)

        # Create percentile bins
        percentiles = [10, 25, 50, 75, 90]
        perc_values = np.percentile(sizes, percentiles)

        # Create analysis window
        analysis_win = tk.Toplevel(self.window)
        analysis_win.title("Grain Size Analysis")
        analysis_win.geometry("800x600")

        fig, axes = plt.subplots(2, 2, figsize=(10, 8))
        fig.suptitle("Grain Size Distribution Analysis", fontweight='bold', fontsize=14)

        # Histogram
        ax1 = axes[0, 0]
        n, bins, patches = ax1.hist(sizes, bins=20, alpha=0.7,
                                   color='skyblue', edgecolor='black')
        ax1.axvline(mean_size, color='red', linestyle='--',
                   label=f'Mean: {mean_size:.2f} μm')
        ax1.axvline(median_size, color='green', linestyle='--',
                   label=f'Median: {median_size:.2f} μm')
        ax1.set_xlabel('Grain Size (μm)')
        ax1.set_ylabel('Frequency')
        ax1.set_title('Size Distribution')
        ax1.legend(fontsize=8)
        ax1.grid(True, alpha=0.3)

        # Box plot
        ax2 = axes[0, 1]
        ax2.boxplot(sizes, vert=False)
        ax2.set_xlabel('Grain Size (μm)')
        ax2.set_title('Statistical Summary')
        ax2.grid(True, alpha=0.3)

        # Cumulative distribution
        ax3 = axes[1, 0]
        sorted_sizes = np.sort(sizes)
        cumulative = np.arange(1, len(sorted_sizes) + 1) / len(sorted_sizes) * 100
        ax3.plot(sorted_sizes, cumulative, 'b-', linewidth=2)
        ax3.set_xlabel('Grain Size (μm)')
        ax3.set_ylabel('Cumulative (%)')
        ax3.set_title('Cumulative Distribution')
        ax3.grid(True, alpha=0.3)

        # Statistics text
        ax4 = axes[1, 1]
        ax4.axis('off')

        stats_text = f"""GRAIN SIZE STATISTICS

Count:      {len(sizes)}
Mean:       {mean_size:.2f} μm
Median:     {median_size:.2f} μm
Std Dev:    {std_size:.2f} μm
Min:        {min_size:.2f} μm
Max:        {max_size:.2f} μm

PERCENTILES
10%:        {perc_values[0]:.2f} μm
25%:        {perc_values[1]:.2f} μm
50%:        {perc_values[2]:.2f} μm
75%:        {perc_values[3]:.2f} μm
90%:        {perc_values[4]:.2f} μm

INTERPRETATION
{self._interpret_grain_size(mean_size, std_size)}
"""

        ax4.text(0.1, 0.9, stats_text, transform=ax4.transAxes,
                fontsize=9, verticalalignment='top',
                fontfamily='monospace')

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, analysis_win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Add toolbar
        toolbar = NavigationToolbar2Tk(canvas, analysis_win)
        toolbar.update()

    def _shape_analysis(self):
        """Analyze grain shapes"""
        if not self.mineral_data:
            messagebox.showwarning("No Data", "No mineral data to analyze.")
            return

        # Calculate shape parameters for each grain
        shapes = []
        for grain in self.mineral_data:
            if grain['type'] != 'void':
                size = grain['size']
                aspect = grain.get('aspect_ratio', 1.0)
                circularity = 1.0 / aspect if aspect > 1 else aspect

                shapes.append({
                    'mineral': grain['type'],
                    'size': size,
                    'aspect_ratio': aspect,
                    'circularity': circularity,
                    'shape': grain.get('shape', 'equant')
                })

        # Create analysis window
        analysis_win = tk.Toplevel(self.window)
        analysis_win.title("Grain Shape Analysis")
        analysis_win.geometry("800x600")

        fig, axes = plt.subplots(2, 2, figsize=(10, 8))
        fig.suptitle("Grain Shape Analysis", fontweight='bold', fontsize=14)

        # Aspect ratio distribution
        ax1 = axes[0, 0]
        aspects = [s['aspect_ratio'] for s in shapes]
        ax1.hist(aspects, bins=20, alpha=0.7, color='lightgreen', edgecolor='black')
        ax1.set_xlabel('Aspect Ratio')
        ax1.set_ylabel('Frequency')
        ax1.set_title('Aspect Ratio Distribution')
        ax1.grid(True, alpha=0.3)

        # Circularity distribution
        ax2 = axes[0, 1]
        circularities = [s['circularity'] for s in shapes]
        ax2.hist(circularities, bins=20, alpha=0.7, color='lightcoral', edgecolor='black')
        ax2.set_xlabel('Circularity (1 = perfect circle)')
        ax2.set_ylabel('Frequency')
        ax2.set_title('Circularity Distribution')
        ax2.grid(True, alpha=0.3)

        # Shape by mineral type
        ax3 = axes[1, 0]
        mineral_shapes = {}
        for s in shapes:
            mineral = s['mineral']
            if mineral not in mineral_shapes:
                mineral_shapes[mineral] = []
            mineral_shapes[mineral].append(s['aspect_ratio'])

        minerals = list(mineral_shapes.keys())
        positions = np.arange(len(minerals))
        means = [np.mean(mineral_shapes[m]) for m in minerals]
        stds = [np.std(mineral_shapes[m]) for m in minerals]

        ax3.bar(positions, means, yerr=stds, alpha=0.7,
               color='skyblue', edgecolor='black', capsize=5)
        ax3.set_xticks(positions)
        ax3.set_xticklabels([m.capitalize() for m in minerals], rotation=45, ha='right')
        ax3.set_ylabel('Mean Aspect Ratio')
        ax3.set_title('Aspect Ratio by Mineral')
        ax3.grid(True, alpha=0.3)

        # Shape classification
        ax4 = axes[1, 1]
        shape_counts = {}
        for s in shapes:
            shape = s['shape']
            shape_counts[shape] = shape_counts.get(shape, 0) + 1

        shapes_list = list(shape_counts.keys())
        counts = list(shape_counts.values())
        colors = plt.cm.Set3(np.linspace(0, 1, len(shapes_list)))

        ax4.pie(counts, labels=shapes_list, autopct='%1.1f%%',
               colors=colors, textprops={'fontsize': 9})
        ax4.set_title('Shape Classification')

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, analysis_win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        toolbar = NavigationToolbar2Tk(canvas, analysis_win)
        toolbar.update()

    def _orientation_analysis(self):
        """Analyze grain orientations"""
        if not self.mineral_data:
            messagebox.showwarning("No Data", "No mineral data to analyze.")
            return

        # Extract orientation data
        angles = []
        minerals = []
        for grain in self.mineral_data:
            if 'angle' in grain and grain['type'] not in ['void', 'opaque']:
                angles.append(grain['angle'])
                minerals.append(grain['type'])

        if len(angles) < 5:
            messagebox.showwarning("Insufficient Data", "Not enough oriented grains for analysis.")
            return

        # Create analysis window
        analysis_win = tk.Toplevel(self.window)
        analysis_win.title("Grain Orientation Analysis")
        analysis_win.geometry("800x600")

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        fig.suptitle("Grain Orientation Analysis", fontweight='bold', fontsize=14)

        # Rose diagram (histogram of angles)
        ax1 = plt.subplot(121, projection='polar')

        # Convert to radians and create rose
        angles_rad = np.radians(angles)
        nbins = 16
        theta = np.linspace(0, 2*np.pi, nbins+1)
        counts, _ = np.histogram(angles_rad, bins=theta)

        ax1.bar(theta[:-1], counts, width=2*np.pi/nbins,
                alpha=0.7, color='steelblue', edgecolor='black')
        ax1.set_theta_zero_location('N')
        ax1.set_theta_direction(-1)
        ax1.set_title('Grain Orientation', pad=20, fontweight='bold')

        # Statistics
        ax2 = plt.subplot(122)
        ax2.axis('off')

        # Calculate statistics
        mean_angle = np.mean(angles)
        median_angle = np.median(angles)
        std_angle = np.std(angles)

        # Test for uniformity (Rayleigh test)
        R = np.sqrt(np.mean(np.cos(angles_rad))**2 + np.mean(np.sin(angles_rad))**2) * len(angles)
        Rayleigh_Z = R**2 / len(angles)
        p_value = np.exp(-Rayleigh_Z)  # Approximate

        stats_text = f"""ORIENTATION STATISTICS

Mean direction:     {mean_angle:.1f}°
Median direction:   {median_angle:.1f}°
Circular std:       {std_angle:.1f}°

Rayleigh test:
  R = {R:.1f}
  Z = {Rayleigh_Z:.3f}
  p = {p_value:.4f}

INTERPRETATION
{self._interpret_orientation(mean_angle, p_value)}
"""

        ax2.text(0.1, 0.9, stats_text, transform=ax2.transAxes,
                fontsize=10, verticalalignment='top',
                fontfamily='monospace')

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, analysis_win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        toolbar = NavigationToolbar2Tk(canvas, analysis_win)
        toolbar.update()

    def _porosity_analysis(self):
        """Analyze porosity and void space"""
        if not self.mineral_data:
            messagebox.showwarning("No Data", "No mineral data to analyze.")
            return

        # Separate void and non-void grains
        voids = [g for g in self.mineral_data if g['type'] == 'void']
        minerals = [g for g in self.mineral_data if g['type'] != 'void']

        total_grains = len(self.mineral_data)
        void_count = len(voids)
        void_percent = (void_count / total_grains * 100) if total_grains > 0 else 0

        # Calculate void area if size data available
        void_area = sum(np.pi * (g['size']/2)**2 for g in voids)
        mineral_area = sum(np.pi * (g['size']/2)**2 for g in minerals)
        total_area = void_area + mineral_area
        area_porosity = (void_area / total_area * 100) if total_area > 0 else 0

        # Create analysis window
        analysis_win = tk.Toplevel(self.window)
        analysis_win.title("Porosity Analysis")
        analysis_win.geometry("600x500")

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        fig.suptitle("Porosity Analysis", fontweight='bold', fontsize=14)

        # Porosity pie chart
        labels = ['Mineral', 'Void']
        sizes = [len(minerals), len(voids)]
        colors = ['#3498db', '#e74c3c']
        explode = (0, 0.1) if void_count > 0 else (0, 0)

        ax1.pie(sizes, explode=explode, labels=labels, colors=colors,
               autopct='%1.1f%%', shadow=True, startangle=90)
        ax1.set_title('Grain Count Porosity')

        # Porosity statistics
        ax2.axis('off')

        stats_text = f"""POROSITY ANALYSIS

GRAIN COUNT
Total grains:    {total_grains}
Void grains:     {void_count}
Mineral grains:  {len(minerals)}

Number porosity: {void_percent:.2f}%

AREA POROSITY
Void area:      {void_area:.2f} μm²
Mineral area:   {mineral_area:.2f} μm²
Total area:     {total_area:.2f} μm²

Area porosity:  {area_porosity:.2f}%

INTERPRETATION
{self._interpret_porosity(area_porosity)}
"""

        ax2.text(0.1, 0.9, stats_text, transform=ax2.transAxes,
                fontsize=10, verticalalignment='top',
                fontfamily='monospace')

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, analysis_win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        toolbar = NavigationToolbar2Tk(canvas, analysis_win)
        toolbar.update()

    def _grain_boundary_analysis(self):
        """Analyze grain boundaries"""
        if not self.mineral_data:
            messagebox.showwarning("No Data", "No mineral data to analyze.")
            return

        # Create boundary map using Delaunay triangulation
        points = np.array([[g['x'], g['y']] for g in self.mineral_data])
        if len(points) < 4:
            messagebox.showwarning("Insufficient Data", "Need at least 4 points for boundary analysis.")
            return

        tri = Delaunay(points)

        # Create analysis window
        analysis_win = tk.Toplevel(self.window)
        analysis_win.title("Grain Boundary Analysis")
        analysis_win.geometry("700x600")

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        fig.suptitle("Grain Boundary Analysis", fontweight='bold', fontsize=14)

        # Voronoi diagram (grain territories)
        vor = Voronoi(points)

        # Plot Voronoi
        ax1.plot(points[:, 0], points[:, 1], 'o', markersize=3, color='red')
        voronoi_plot_2d(vor, ax=ax1, show_vertices=False, line_colors='blue',
                       line_width=1.5, point_size=2)
        ax1.set_title('Voronoi Diagram (Grain Territories)')
        ax1.set_xlabel('X Position (μm)')
        ax1.set_ylabel('Y Position (μm)')
        ax1.set_aspect('equal')

        # Delaunay triangulation (grain connections)
        ax2.triplot(points[:, 0], points[:, 1], tri.simplices,
                   color='green', alpha=0.5)
        ax2.plot(points[:, 0], points[:, 1], 'o', color='blue', markersize=3)
        ax2.set_title('Delaunay Triangulation (Grain Contacts)')
        ax2.set_xlabel('X Position (μm)')
        ax2.set_ylabel('Y Position (μm)')
        ax2.set_aspect('equal')

        # Calculate boundary statistics
        edges = set()
        for simplex in tri.simplices:
            edges.add(tuple(sorted([simplex[0], simplex[1]])))
            edges.add(tuple(sorted([simplex[1], simplex[2]])))
            edges.add(tuple(sorted([simplex[2], simplex[0]])))

        avg_neighbors = 2 * len(edges) / len(points)
        contact_count = len(edges)

        ax2.text(0.02, 0.98, f"Avg contacts: {avg_neighbors:.2f}\nTotal contacts: {contact_count}",
                transform=ax2.transAxes, fontsize=10,
                verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, analysis_win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        toolbar = NavigationToolbar2Tk(canvas, analysis_win)
        toolbar.update()

    def _fabric_analysis(self):
        """Analyze rock fabric"""
        if not self.mineral_data:
            messagebox.showwarning("No Data", "No mineral data to analyze.")
            return

        try:
            from sklearn.decomposition import PCA
            HAS_SKLEARN = True
        except ImportError:
            HAS_SKLEARN = False

        # Extract positions
        positions = np.array([[g['x'], g['y']] for g in self.mineral_data])

        # Calculate centroid
        centroid = np.mean(positions, axis=0)

        # Calculate principal axes
        if HAS_SKLEARN:
            pca = PCA(n_components=2)
            pca.fit(positions)
            components = pca.components_
            explained_var = pca.explained_variance_ratio_
        else:
            # Manual calculation using covariance matrix
            cov = np.cov(positions.T)
            eigenvals, eigenvecs = np.linalg.eig(cov)
            idx = eigenvals.argsort()[::-1]
            eigenvals = eigenvals[idx]
            eigenvecs = eigenvecs[:, idx]
            components = eigenvecs.T
            explained_var = eigenvals / np.sum(eigenvals)

        # Calculate fabric intensity
        fabric_intensity = (explained_var[0] - explained_var[1]) / (explained_var[0] + explained_var[1])

        # Create analysis window
        analysis_win = tk.Toplevel(self.window)
        analysis_win.title("Fabric Analysis")
        analysis_win.geometry("700x600")

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        fig.suptitle("Fabric Analysis", fontweight='bold', fontsize=14)

        # Plot with principal axes
        ax1.scatter(positions[:, 0], positions[:, 1],
                   alpha=0.5, s=20, color='gray')
        ax1.scatter(centroid[0], centroid[1], color='red', s=100,
                   marker='X', label='Centroid', zorder=5)

        # Draw principal axes
        for i, (comp, var) in enumerate(zip(components, explained_var)):
            scale = 50
            dx, dy = comp * scale
            ax1.arrow(centroid[0], centroid[1], dx, dy,
                     head_width=5, head_length=5,
                     fc='blue' if i == 0 else 'green',
                     ec='blue' if i == 0 else 'green',
                     alpha=0.8, width=1,
                     label=f'PC{i+1} ({var:.1%})')

        ax1.set_title('Grain Distribution with Principal Axes')
        ax1.set_xlabel('X Position (μm)')
        ax1.set_ylabel('Y Position (μm)')
        ax1.set_aspect('equal')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Fabric summary
        ax2.axis('off')

        fabric_type = self._interpret_fabric(fabric_intensity)

        stats_text = f"""FABRIC ANALYSIS

CENTROID
X: {centroid[0]:.2f} μm
Y: {centroid[1]:.2f} μm

PRINCIPAL COMPONENTS
PC1: {explained_var[0]:.1%}
PC2: {explained_var[1]:.1%}
PC1/PC2 ratio: {(explained_var[0]/explained_var[1]):.2f}

FABRIC INTENSITY
{fabric_intensity:.3f}
{fabric_type}

SHAPE PREFERRED ORIENTATION
Direction: {np.degrees(np.arctan2(components[0,1], components[0,0])):.1f}°

INTERPRETATION
{self._interpret_fabric_full(fabric_intensity, explained_var[0]/explained_var[1])}
"""

        ax2.text(0.1, 0.95, stats_text, transform=ax2.transAxes,
                fontsize=10, verticalalignment='top',
                fontfamily='monospace')

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, analysis_win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        toolbar = NavigationToolbar2Tk(canvas, analysis_win)
        toolbar.update()

    # ============================================================================
    # INTERPRETATION HELPERS
    # ============================================================================
    def _interpret_grain_size(self, mean, std):
        """Interpret grain size in petrological context"""
        if mean < 10:
            return "Very fine-grained (aphanitic) - Rapid cooling"
        elif mean < 50:
            return "Fine-grained - Shallow intrusion/volcanic"
        elif mean < 200:
            return "Medium-grained - Hypabyssal"
        elif mean < 500:
            return "Coarse-grained - Plutonic"
        else:
            return "Very coarse-grained - Pegmatitic"

    def _interpret_orientation(self, mean_angle, p_value):
        """Interpret orientation data"""
        if p_value < 0.05:
            if 80 <= mean_angle <= 100 or 260 <= mean_angle <= 280:
                return "Strong vertical alignment - Possible flow fabric"
            elif 170 <= mean_angle <= 190 or 350 <= mean_angle <= 10:
                return "Strong horizontal alignment - Tectonic fabric"
            else:
                return "Strong preferred orientation - Deformation fabric"
        else:
            return "Random orientation - No preferred fabric"

    def _interpret_porosity(self, porosity):
        """Interpret porosity values"""
        if porosity < 1:
            return "Very low porosity - Highly compacted/cemented"
        elif porosity < 5:
            return "Low porosity - Well-consolidated"
        elif porosity < 15:
            return "Moderate porosity - Typical reservoir quality"
        elif porosity < 25:
            return "High porosity - Good reservoir potential"
        else:
            return "Very high porosity - Friable/unconsolidated"

    def _interpret_fabric(self, intensity):
        """Interpret fabric intensity"""
        if intensity < 0.1:
            return "Random fabric (isotropic)"
        elif intensity < 0.3:
            return "Weakly aligned (weak fabric)"
        elif intensity < 0.6:
            return "Moderately aligned (foliated)"
        else:
            return "Strongly aligned (gneissic/lineated)"

    def _interpret_fabric_full(self, intensity, ratio):
        """Full fabric interpretation"""
        if intensity < 0.1:
            return "No preferred orientation - Massive rock"
        elif intensity < 0.3:
            if ratio < 1.5:
                return "Weak planar fabric - Possible magmatic flow"
            else:
                return "Weak linear fabric - Possible deformation"
        elif intensity < 0.6:
            if ratio < 2:
                return "Moderate foliation - Metamorphic fabric"
            else:
                return "Moderate lineation - Tectonic fabric"
        else:
            return "Strong fabric - Highly deformed rock"

    # ============================================================================
    # EXPORT METHODS
    # ============================================================================
    def _save_image(self):
        """Save current plot as image"""
        if not self.mineral_data:
            messagebox.showwarning("No Data", "No data to save.")
            return

        path = filedialog.asksaveasfilename(
            title="Save Image",
            defaultextension=".png",
            filetypes=[
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg"),
                ("PDF files", "*.pdf"),
                ("SVG files", "*.svg"),
                ("All files", "*.*")
            ]
        )

        if path:
            try:
                self.fig.savefig(path, dpi=300, bbox_inches='tight')
                self.status_var.set(f"✅ Image saved: {Path(path).name}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save image:\n{str(e)}")

    def _export_data(self):
        """Export data as JSON"""
        if not self.mineral_data:
            messagebox.showwarning("No Data", "No data to export.")
            return

        path = filedialog.asksaveasfilename(
            title="Export Data",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if path:
            try:
                data = {
                    'section': self.current_section,
                    'minerals': self.mineral_data,
                    'texture': self.texture_data,
                    'export_date': datetime.now().isoformat(),
                    'mineral_database': self.mineral_database,
                    'analysis_summary': self._generate_summary()
                }

                with open(path, 'w') as f:
                    json.dump(data, f, indent=2)

                self.status_var.set(f"✅ Data exported: {Path(path).name}")

            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export data:\n{str(e)}")

    def _export_report(self):
        """Generate and export comprehensive report"""
        if not self.mineral_data:
            messagebox.showwarning("No Data", "No data to export.")
            return

        path = filedialog.asksaveasfilename(
            title="Save Report",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )

        if path:
            try:
                summary = self._generate_summary()
                with open(path, 'w') as f:
                    f.write(summary)
                self.status_var.set(f"✅ Report saved: {Path(path).name}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to save report:\n{str(e)}")

    def _generate_summary(self):
        """Generate text summary of analysis"""
        if not self.mineral_data:
            return "No data available."

        total_grains = len(self.mineral_data)

        # Mineral counts
        mineral_counts = {}
        for grain in self.mineral_data:
            mineral = grain['type']
            mineral_counts[mineral] = mineral_counts.get(mineral, 0) + 1

        # Size statistics
        sizes = [g['size'] for g in self.mineral_data if g['type'] != 'void']
        mean_size = np.mean(sizes) if sizes else 0

        summary = []
        summary.append("=" * 60)
        summary.append("VIRTUAL MICROSCOPY ANALYSIS REPORT")
        summary.append("=" * 60)
        summary.append("")

        if self.current_section:
            summary.append("SECTION INFORMATION:")
            for key, value in self.current_section.items():
                if key not in ['minerals', 'texture']:
                    summary.append(f"  {key}: {value}")
            summary.append("")

        summary.append("MINERAL COMPOSITION:")
        summary.append("-" * 40)
        for mineral, count in sorted(mineral_counts.items(), key=lambda x: x[1], reverse=True):
            pct = (count / total_grains) * 100
            summary.append(f"  {mineral.capitalize():15} {count:4d} grains ({pct:5.1f}%)")
        summary.append("")

        summary.append(f"Total grains: {total_grains}")
        summary.append(f"Mean grain size: {mean_size:.2f} μm")
        summary.append("")

        summary.append("ANALYSIS COMPLETED:")
        summary.append(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary.append("")
        summary.append("=" * 60)

        return '\n'.join(summary)

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def _set_all_minerals(self, value):
        """Set all mineral checkboxes to given value"""
        for var in self.mineral_vars.values():
            var.set(value)
        self._update_plot()

    def _rgb_to_hex(self, rgb):
        """Convert RGB list to hex color"""
        if len(rgb) >= 3:
            r = int(rgb[0] * 255)
            g = int(rgb[1] * 255)
            b = int(rgb[2] * 255)
            return f'#{r:02x}{g:02x}{b:02x}'
        return '#000000'


def setup_plugin(main_app):
    """Plugin setup function"""
    plugin = VirtualMicroscopyProPlugin(main_app)
    return plugin  # ← REMOVE MENU CODE
