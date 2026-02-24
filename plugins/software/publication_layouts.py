"""
Publication Layouts Pro v2.0 - Multi-Panel Figure Designer
Professional publication-ready figure creation with main app integration

NOW WITH:
✓ Modern tabbed interface (like PCA+LDA Explorer)
✓ Auto-loads data from main app on open
✓ Column detection for numeric/categorical data
✓ Drag-and-drop panel designer with snap-to-grid
✓ Journal templates (Nature, Science, Geology, AGU, Elsevier)
✓ 20+ plot types with interactive configuration
✓ Style management with real-time preview
✓ Export to PNG, PDF, SVG, EPS, TIFF with journal DPI
✓ Layout configuration manager
"""

PLUGIN_INFO = {
    "category": "software",
    "id": "publication_layouts",
    "name": "Publication Layouts Pro",
    "description": "Professional multi-panel figure designer with main app integration",
    "icon": "📐",
    "version": "2.0.0",
    "requires": ["matplotlib", "numpy", "pillow", "seaborn"],
    "author": "Sefy Levy & DeepSeek"
}

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog, colorchooser
import json
import os
import math
import uuid
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum
from datetime import datetime
import tempfile

# Scientific imports
try:
    import matplotlib
    matplotlib.use('TkAgg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_pdf import PdfPages
    import matplotlib.gridspec as gridspec
    from matplotlib.patches import Rectangle
    HAS_MATPLOTLIB = True
    HAS_PDF = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False

HAS_REQUIREMENTS = HAS_MATPLOTLIB and HAS_NUMPY


# ============================================================================
# DATA CLASSES
# ============================================================================
class PanelType(Enum):
    PLOT = "plot"
    IMAGE = "image"
    TEXT = "text"
    TABLE = "table"
    LEGEND = "legend"

class JournalStyle(Enum):
    NATURE = "Nature"
    SCIENCE = "Science"
    GEOLOGY = "Geology"
    EPSL = "EPSL"
    AGU = "AGU"
    ELSEVIER = "Elsevier"
    CUSTOM = "Custom"


@dataclass
class Panel:
    """Represents a single panel in the figure"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    type: PanelType = PanelType.PLOT
    x: float = 0.1  # normalized coordinates (0-1)
    y: float = 0.1
    width: float = 0.35
    height: float = 0.35
    label: str = "A"
    title: str = ""
    plot_type: str = "scatter"
    x_col: str = ""
    y_col: str = ""
    color_col: str = ""
    size_col: str = ""
    style: Dict = field(default_factory=dict)
    visible: bool = True

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type.value,
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'label': self.label,
            'title': self.title,
            'plot_type': self.plot_type,
            'x_col': self.x_col,
            'y_col': self.y_col,
            'color_col': self.color_col,
            'size_col': self.size_col,
            'style': self.style,
            'visible': self.visible
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data.get('id', str(uuid.uuid4())[:8]),
            type=PanelType(data.get('type', 'plot')),
            x=data.get('x', 0.1),
            y=data.get('y', 0.1),
            width=data.get('width', 0.35),
            height=data.get('height', 0.35),
            label=data.get('label', 'A'),
            title=data.get('title', ''),
            plot_type=data.get('plot_type', 'scatter'),
            x_col=data.get('x_col', ''),
            y_col=data.get('y_col', ''),
            color_col=data.get('color_col', ''),
            size_col=data.get('size_col', ''),
            style=data.get('style', {}),
            visible=data.get('visible', True)
        )


@dataclass
class FigureLayout:
    """Represents the complete figure layout"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = "New Figure"
    width: float = 7.0  # inches
    height: float = 9.0
    dpi: int = 300
    panels: List[Panel] = field(default_factory=list)
    style: JournalStyle = JournalStyle.NATURE
    caption: str = ""
    background_color: str = "#FFFFFF"
    font_family: str = "Arial"
    font_sizes: Dict = field(default_factory=lambda: {
        'title': 10, 'label': 8, 'tick': 7, 'legend': 7
    })

    # Journal presets
    JOURNAL_PRESETS = {
        JournalStyle.NATURE: {
            'width': 3.5, 'height': 9.0, 'dpi': 300,
            'font_family': 'Arial',
            'font_sizes': {'title': 8, 'label': 7, 'tick': 6, 'legend': 7}
        },
        JournalStyle.SCIENCE: {
            'width': 5.5, 'height': 7.5, 'dpi': 300,
            'font_family': 'Helvetica',
            'font_sizes': {'title': 9, 'label': 8, 'tick': 7, 'legend': 8}
        },
        JournalStyle.GEOLOGY: {
            'width': 7.0, 'height': 9.0, 'dpi': 600,
            'font_family': 'Times New Roman',
            'font_sizes': {'title': 10, 'label': 9, 'tick': 8, 'legend': 9}
        },
        JournalStyle.EPSL: {
            'width': 7.5, 'height': 9.5, 'dpi': 300,
            'font_family': 'Arial',
            'font_sizes': {'title': 9, 'label': 8, 'tick': 7, 'legend': 8}
        },
        JournalStyle.AGU: {
            'width': 7.0, 'height': 8.5, 'dpi': 600,
            'font_family': 'Times New Roman',
            'font_sizes': {'title': 9, 'label': 8, 'tick': 7, 'legend': 8}
        },
        JournalStyle.ELSEVIER: {
            'width': 6.5, 'height': 8.0, 'dpi': 300,
            'font_family': 'Arial',
            'font_sizes': {'title': 9, 'label': 8, 'tick': 7, 'legend': 8}
        }
    }

    def apply_journal_style(self):
        """Apply journal-specific style settings"""
        if self.style in self.JOURNAL_PRESETS:
            preset = self.JOURNAL_PRESETS[self.style]
            self.width = preset['width']
            self.dpi = preset['dpi']
            self.font_family = preset['font_family']
            self.font_sizes = preset['font_sizes'].copy()

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'width': self.width,
            'height': self.height,
            'dpi': self.dpi,
            'panels': [p.to_dict() for p in self.panels],
            'style': self.style.value,
            'caption': self.caption,
            'background_color': self.background_color,
            'font_family': self.font_family,
            'font_sizes': self.font_sizes
        }

    @classmethod
    def from_dict(cls, data):
        layout = cls(
            id=data.get('id', str(uuid.uuid4())[:8]),
            name=data.get('name', 'New Figure'),
            width=data.get('width', 7.0),
            height=data.get('height', 9.0),
            dpi=data.get('dpi', 300),
            style=JournalStyle(data.get('style', 'Nature')),
            caption=data.get('caption', ''),
            background_color=data.get('background_color', '#FFFFFF'),
            font_family=data.get('font_family', 'Arial'),
            font_sizes=data.get('font_sizes', {'title': 10, 'label': 8, 'tick': 7, 'legend': 7})
        )
        for pdata in data.get('panels', []):
            layout.panels.append(Panel.from_dict(pdata))
        return layout


# ============================================================================
# MAIN PLUGIN CLASS
# ============================================================================
class PublicationLayoutsPlugin:
    """Professional multi-panel publication figure designer"""

    PLOT_TYPES = [
        "scatter", "line", "bar", "histogram", "boxplot",
        "violin", "heatmap", "contour", "density", "hexbin",
        "errorbar", "fill_between", "stackplot", "stem",
        "step", "ecdf", "kde", "pairplot", "jointplot"
    ]

    def __init__(self, main_app):
        self.app = main_app
        self.window = None

        # Data from main app
        self.df = None
        self.numeric_cols = []
        self.categorical_cols = []

        # Layout management
        self.current_layout = FigureLayout()
        self.layouts = []
        self.selected_panel = None
        self.drag_start = None
        self.resize_start = None
        self.grid_size = 20  # pixels
        self.zoom_level = 1.0

        # UI elements
        self.notebook = None
        self.preview_fig = None
        self.preview_ax = None
        self.preview_canvas = None
        self.panel_listbox = None
        self.status_var = None
        self.progress = None

        # Load saved layouts
        self._load_saved_layouts()

    # ============================================================================
    # DATA INTEGRATION - AUTO LOADS FROM MAIN APP
    # ============================================================================
    def _refresh_data(self):
        """Auto-load data from main app on window open"""
        if not hasattr(self.app, 'samples') or not self.app.samples:
            self.df = None
            self.numeric_cols = []
            self.categorical_cols = []
            return False

        import pandas as pd
        self.df = pd.DataFrame(self.app.samples)
        print(f"📊 Loaded {len(self.df)} samples from main app")

        # Detect column types
        self.numeric_cols = []
        self.categorical_cols = []

        for col in self.df.columns:
            try:
                # Try to convert to numeric
                pd.to_numeric(self.df[col])
                self.numeric_cols.append(col)
            except:
                # Categorical/text column
                self.categorical_cols.append(col)

        print(f"📈 Numeric columns: {len(self.numeric_cols)}")
        print(f"📊 Categorical columns: {len(self.categorical_cols)}")

        return True

    # ============================================================================
    # LAYOUT MANAGEMENT
    # ============================================================================
    def _create_default_layout(self):
        """Create default layout with 2x2 panels"""
        self.current_layout = FigureLayout(name="New Figure")
        labels = ['A', 'B', 'C', 'D']
        positions = [
            (0.1, 0.55, 0.35, 0.35),
            (0.55, 0.55, 0.35, 0.35),
            (0.1, 0.1, 0.35, 0.35),
            (0.55, 0.1, 0.35, 0.35)
        ]

        for i, ((x, y, w, h), label) in enumerate(zip(positions, labels[:4])):
            panel = Panel(
                id=f"panel_{i}",
                x=x, y=y, width=w, height=h,
                label=label,
                plot_type="scatter"
            )
            self.current_layout.panels.append(panel)

        self._update_panel_list()
        self._update_preview()

    def _load_saved_layouts(self):
        """Load saved layouts from config file"""
        config_dir = Path("config/publication_layouts")
        config_dir.mkdir(parents=True, exist_ok=True)

        layout_file = config_dir / "saved_layouts.json"
        if layout_file.exists():
            try:
                with open(layout_file, 'r') as f:
                    data = json.load(f)
                    for layout_data in data.get('layouts', []):
                        self.layouts.append(FigureLayout.from_dict(layout_data))
            except:
                pass

    def _save_layouts(self):
        """Save layouts to config file"""
        config_dir = Path("config/publication_layouts")
        config_dir.mkdir(parents=True, exist_ok=True)

        layout_file = config_dir / "saved_layouts.json"
        try:
            data = {'layouts': [l.to_dict() for l in self.layouts]}
            with open(layout_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving layouts: {e}")

    # ============================================================================
    # UI CONSTRUCTION - MODERN TABBED INTERFACE
    # ============================================================================
    def open_window(self):
        """Open the publication layout interface"""
        if not HAS_REQUIREMENTS:
            missing = []
            if not HAS_MATPLOTLIB: missing.append("matplotlib")
            if not HAS_NUMPY: missing.append("numpy")
            messagebox.showerror("Missing Dependencies",
                            f"Requires:\n" + "\n".join(missing))
            return

        if self.window and self.window.winfo_exists():
            self.window.lift()
            self._refresh_data()
            self._update_preview()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("📐 Publication Layouts Pro v2.0")
        self.window.geometry("1000x650")  # ← MUCH SMALLER (was 1400x850)
        self.window.minsize(900, 600)     # ← Smaller minimum size

        # AUTO-LOAD DATA FROM MAIN APP
        self._refresh_data()

        self._create_interface()
        self._create_default_layout()

        self.window.transient(self.app.root)
        self.window.lift()
        self.window.focus_force()

        # Keyboard shortcuts
        self.window.bind('<Control-s>', lambda e: self._save_current_layout())
        self.window.bind('<Control-o>', lambda e: self._load_layout_dialog())
        self.window.bind('<Control-n>', lambda e: self._create_default_layout())
        self.window.bind('<Control-e>', lambda e: self._export_figure())
        self.window.bind('<Control-p>', lambda e: self._update_preview())
        self.window.bind('<Delete>', lambda e: self._delete_selected_panel())
        self.window.bind('<Control-z>', lambda e: self._undo())
        self.window.bind('<Control-y>', lambda e: self._redo())
        self.window.bind('<Control-g>', lambda e: self._toggle_grid())

    def _create_interface(self):
        """Create modern tabbed interface"""
        # ============ HEADER ============
        header = tk.Frame(self.window, bg="#2c3e50", height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="📐", font=("Arial", 20),
                bg="#2c3e50", fg="white").pack(side=tk.LEFT, padx=10)

        tk.Label(header, text="Publication Layouts Pro",
                font=("Arial", 16, "bold"),
                bg="#2c3e50", fg="white").pack(side=tk.LEFT, padx=5)

        tk.Label(header, text="v2.0 - Multi-Panel Figure Designer",
                font=("Arial", 9),
                bg="#2c3e50", fg="#f1c40f").pack(side=tk.LEFT, padx=10)

        # Layout name
        self.name_var = tk.StringVar(value="New Figure")
        name_entry = tk.Entry(header, textvariable=self.name_var,
                            font=("Arial", 9), width=20)
        name_entry.pack(side=tk.RIGHT, padx=5)

        tk.Label(header, text="Figure:", bg="#2c3e50", fg="white",
                font=("Arial", 9)).pack(side=tk.RIGHT, padx=2)

        # ============ MAIN PANED WINDOW ============
        main_paned = tk.PanedWindow(self.window, orient=tk.HORIZONTAL, sashwidth=6)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left panel - Controls (WIDER - 550px)
        left = tk.Frame(main_paned, bg="#f5f5f5", width=450)  # Smaller
        main_paned.add(left, width=450, minsize=400)

        # Right panel - Preview (SMALLER - 350px)
        right = tk.Frame(main_paned, bg="white", width=200)   # Much smaller
        main_paned.add(right, width=200, minsize=150)

        # ============ LEFT PANEL - NOTEBOOK TABS ============
        self.notebook = ttk.Notebook(left)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # TAB 1: PANELS
        tab1 = ttk.Frame(self.notebook)
        self.notebook.add(tab1, text="📦 Panels")
        self._build_panels_tab(tab1)

        # TAB 2: LAYOUT
        tab2 = ttk.Frame(self.notebook)
        self.notebook.add(tab2, text="📐 Layout")
        self._build_layout_tab(tab2)

        # TAB 3: TEMPLATES
        tab3 = ttk.Frame(self.notebook)
        self.notebook.add(tab3, text="📋 Templates")
        self._build_templates_tab(tab3)

        # TAB 4: DATA
        tab4 = ttk.Frame(self.notebook)
        self.notebook.add(tab4, text="📊 Data")
        self._build_data_tab(tab4)

        # TAB 5: STYLE
        tab5 = ttk.Frame(self.notebook)
        self.notebook.add(tab5, text="🎨 Style")
        self._build_style_tab(tab5)

        # ============ RIGHT PANEL - PREVIEW (SMALL) ============
        self._setup_preview(right)

        # ============ STATUS BAR ============
        status = tk.Frame(self.window, bg="#34495e", height=30)
        status.pack(fill=tk.X, side=tk.BOTTOM)
        status.pack_propagate(False)

        self.status_var = tk.StringVar(value="Ready - Drag panels to position")
        tk.Label(status, textvariable=self.status_var,
                font=("Arial", 9), bg="#34495e", fg="white").pack(side=tk.LEFT, padx=10)

        self.coord_var = tk.StringVar(value="")
        tk.Label(status, textvariable=self.coord_var,
                font=("Arial", 9), bg="#34495e", fg="white").pack(side=tk.LEFT, padx=20)

        self.progress = ttk.Progressbar(status, mode='indeterminate', length=150)
        self.progress.pack(side=tk.RIGHT, padx=10)

        # Export button
        tk.Button(status, text="📤 Export Figure",
                command=self._export_figure,
                bg="#27ae60", fg="white", font=("Arial", 8, "bold"),
                padx=10).pack(side=tk.RIGHT, padx=5)


    def _setup_preview(self, parent):
        """Setup the preview canvas - COMPACT"""
        # Canvas for preview - MUCH SMALLER
        self.preview_fig = Figure(figsize=(2.2, 2.8), dpi=85)  # Tiny!
        self.preview_fig.patch.set_facecolor('white')
        self.preview_ax = self.preview_fig.add_axes([0, 0, 1, 1])
        self.preview_ax.set_xlim(0, 1)
        self.preview_ax.set_ylim(0, 1)
        self.preview_ax.set_axis_off()

        self.preview_canvas = FigureCanvasTkAgg(self.preview_fig, parent)
        self.preview_canvas.draw()
        self.preview_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        # Minimal toolbar (compact)
        toolbar_frame = tk.Frame(parent, height=22)
        toolbar_frame.pack(fill=tk.X)
        toolbar_frame.pack_propagate(False)
        toolbar = NavigationToolbar2Tk(self.preview_canvas, toolbar_frame)
        toolbar.update()

    # ============================================================================
    # TAB 1: PANELS
    # ============================================================================
    def _build_panels_tab(self, parent):
        """Build panels management tab"""
        # Add new panel
        add_frame = tk.LabelFrame(parent, text="Add New Panel", padx=5, pady=5)
        add_frame.pack(fill=tk.X, padx=5, pady=5)

        self.panel_type_var = tk.StringVar(value="plot")
        types = [("Plot", "plot"), ("Image", "image"), ("Text", "text"),
                ("Table", "table"), ("Legend", "legend")]

        # Create a frame for radio buttons that uses grid
        radio_frame = tk.Frame(add_frame)
        radio_frame.pack(fill=tk.X, pady=5)

        for i, (label, value) in enumerate(types):
            tk.Radiobutton(radio_frame, text=label, variable=self.panel_type_var,
                        value=value).grid(row=i//3, column=i%3, sticky=tk.W, padx=2)

        # Button uses pack in add_frame (different parent)
        tk.Button(add_frame, text="➕ Add Panel", command=self._add_panel,
                bg="#3498db", fg="white").pack(pady=5)

        # Panel list
        list_frame = tk.LabelFrame(parent, text="Current Panels", padx=5, pady=5)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.panel_listbox = tk.Listbox(list_frame, height=10)
        scrollbar = tk.Scrollbar(list_frame, command=self.panel_listbox.yview)
        self.panel_listbox.configure(yscrollcommand=scrollbar.set)

        self.panel_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.panel_listbox.bind('<<ListboxSelect>>', self._on_panel_select)

        # Panel controls
        ctrl_frame = tk.Frame(list_frame)
        ctrl_frame.pack(fill=tk.X, pady=5)

        tk.Button(ctrl_frame, text="✏️ Edit", command=self._edit_panel_properties,
                width=8).pack(side=tk.LEFT, padx=2)
        tk.Button(ctrl_frame, text="🗑️ Delete", command=self._delete_selected_panel,
                width=8).pack(side=tk.LEFT, padx=2)
        tk.Button(ctrl_frame, text="▲ Up", command=self._move_panel_up,
                width=5).pack(side=tk.LEFT, padx=2)
        tk.Button(ctrl_frame, text="▼ Down", command=self._move_panel_down,
                width=5).pack(side=tk.LEFT, padx=2)

    # ============================================================================
    # TAB 2: LAYOUT
    # ============================================================================
    def _build_layout_tab(self, parent):
        """Build layout settings tab"""
        # Journal style
        style_frame = tk.LabelFrame(parent, text="Journal Style", padx=5, pady=5)
        style_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(style_frame, text="Template:").grid(row=0, column=0, sticky=tk.W)
        self.journal_var = tk.StringVar(value="Nature")
        journals = ["Nature", "Science", "Geology", "EPSL", "AGU", "Elsevier", "Custom"]
        journal_combo = ttk.Combobox(style_frame, textvariable=self.journal_var,
                                     values=journals, state="readonly", width=15)
        journal_combo.grid(row=0, column=1, padx=5, pady=2)
        journal_combo.bind('<<ComboboxSelected>>', lambda e: self._apply_journal_style())

        # Dimensions
        dim_frame = tk.LabelFrame(parent, text="Figure Dimensions", padx=5, pady=5)
        dim_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(dim_frame, text="Width (in):").grid(row=0, column=0, sticky=tk.W)
        self.width_var = tk.DoubleVar(value=7.0)
        tk.Spinbox(dim_frame, from_=1, to=20, textvariable=self.width_var,
                  width=8, command=self._update_preview).grid(row=0, column=1)

        tk.Label(dim_frame, text="Height (in):").grid(row=1, column=0, sticky=tk.W)
        self.height_var = tk.DoubleVar(value=9.0)
        tk.Spinbox(dim_frame, from_=1, to=20, textvariable=self.height_var,
                  width=8, command=self._update_preview).grid(row=1, column=1)

        tk.Label(dim_frame, text="DPI:").grid(row=2, column=0, sticky=tk.W)
        self.dpi_var = tk.IntVar(value=300)
        dpi_combo = ttk.Combobox(dim_frame, textvariable=self.dpi_var,
                                 values=[150, 300, 600, 1200], width=6)
        dpi_combo.grid(row=2, column=1, padx=5)

        # Grid settings
        grid_frame = tk.LabelFrame(parent, text="Grid & Snapping", padx=5, pady=5)
        grid_frame.pack(fill=tk.X, padx=5, pady=5)

        self.snap_var = tk.BooleanVar(value=True)
        tk.Checkbutton(grid_frame, text="Snap to grid", variable=self.snap_var,
                      command=self._update_preview).pack(anchor=tk.W)

        self.show_grid_var = tk.BooleanVar(value=False)
        tk.Checkbutton(grid_frame, text="Show grid", variable=self.show_grid_var,
                      command=self._update_preview).pack(anchor=tk.W)

        tk.Label(grid_frame, text="Grid size (px):").pack(anchor=tk.W)
        self.grid_size_var = tk.IntVar(value=20)
        tk.Scale(grid_frame, from_=5, to=50, orient=tk.HORIZONTAL,
                variable=self.grid_size_var, command=lambda x: self._update_preview()).pack(fill=tk.X)

        # Zoom
        zoom_frame = tk.LabelFrame(parent, text="Preview Zoom", padx=5, pady=5)
        zoom_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(zoom_frame, text="Zoom:").pack(anchor=tk.W)
        self.zoom_var = tk.DoubleVar(value=1.0)
        tk.Scale(zoom_frame, from_=0.5, to=2.0, resolution=0.1,
                orient=tk.HORIZONTAL, variable=self.zoom_var,
                command=lambda x: self._update_preview()).pack(fill=tk.X)

    # ============================================================================
    # TAB 3: TEMPLATES
    # ============================================================================
    def _build_templates_tab(self, parent):
        """Build templates tab"""
        # Predefined templates
        preset_frame = tk.LabelFrame(parent, text="Predefined Templates", padx=5, pady=5)
        preset_frame.pack(fill=tk.X, padx=5, pady=5)

        templates = [
            ("2×2 Grid", "grid_2x2"),
            ("3×3 Grid", "grid_3x3"),
            ("Main + Sidebar", "main_sidebar"),
            ("Stacked", "stacked"),
            ("Nature 2×2", "nature_2x2"),
            ("Science Cover", "science_cover")
        ]

        for i, (label, value) in enumerate(templates):
            btn = tk.Button(preset_frame, text=label, width=15,
                          command=lambda v=value: self._apply_template(v))
            btn.grid(row=i//2, column=i%2, padx=2, pady=2)

        # Custom templates
        custom_frame = tk.LabelFrame(parent, text="Your Templates", padx=5, pady=5)
        custom_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.template_listbox = tk.Listbox(custom_frame, height=8)
        self.template_listbox.pack(fill=tk.BOTH, expand=True, pady=5)

        # Load saved templates from layouts
        for layout in self.layouts:
            self.template_listbox.insert(tk.END, layout.name)

        btn_frame = tk.Frame(custom_frame)
        btn_frame.pack(fill=tk.X)

        tk.Button(btn_frame, text="💾 Save Current", command=self._save_as_template,
                 bg="#27ae60", fg="white").pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="📂 Load", command=self._load_template,
                 bg="#3498db", fg="white").pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="🗑️ Delete", command=self._delete_template,
                 bg="#e74c3c", fg="white").pack(side=tk.LEFT, padx=2)

    # ============================================================================
    # TAB 4: DATA
    # ============================================================================
    def _build_data_tab(self, parent):
        """Build data integration tab"""
        # Data source
        source_frame = tk.LabelFrame(parent, text="Data Source", padx=5, pady=5)
        source_frame.pack(fill=tk.X, padx=5, pady=5)

        data_status = "✅ Loaded" if self.df is not None else "❌ No data"
        tk.Label(source_frame, text=f"Main app: {data_status}",
                font=("Arial", 9, "bold")).pack(anchor=tk.W)

        if self.df is not None:
            tk.Label(source_frame, text=f"Samples: {len(self.df)}",
                    font=("Arial", 8)).pack(anchor=tk.W)

        tk.Button(source_frame, text="🔄 Refresh Data",
                 command=self._refresh_data_from_app,
                 bg="#3498db", fg="white").pack(pady=5)

        # Column lists
        col_frame = tk.LabelFrame(parent, text="Available Columns", padx=5, pady=5)
        col_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Numeric columns
        tk.Label(col_frame, text="Numeric (for axes):",
                font=("Arial", 8, "bold")).pack(anchor=tk.W)

        self.numeric_listbox = tk.Listbox(col_frame, height=6)
        scroll_num = tk.Scrollbar(col_frame, command=self.numeric_listbox.yview)
        self.numeric_listbox.configure(yscrollcommand=scroll_num.set)

        for col in self.numeric_cols:
            self.numeric_listbox.insert(tk.END, col)

        self.numeric_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        scroll_num.pack(side=tk.RIGHT, fill=tk.Y)

        # Categorical columns
        tk.Label(col_frame, text="Categorical (for groups):",
                font=("Arial", 8, "bold")).pack(anchor=tk.W, pady=(10,0))

        self.cat_listbox = tk.Listbox(col_frame, height=4)
        scroll_cat = tk.Scrollbar(col_frame, command=self.cat_listbox.yview)
        self.cat_listbox.configure(yscrollcommand=scroll_cat.set)

        for col in self.categorical_cols:
            self.cat_listbox.insert(tk.END, col)

        self.cat_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        scroll_cat.pack(side=tk.RIGHT, fill=tk.Y)

    # ============================================================================
    # TAB 5: STYLE
    # ============================================================================
    def _build_style_tab(self, parent):
        """Build style settings tab"""
        # Font settings
        font_frame = tk.LabelFrame(parent, text="Fonts", padx=5, pady=5)
        font_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(font_frame, text="Family:").grid(row=0, column=0, sticky=tk.W)
        self.font_family_var = tk.StringVar(value="Arial")
        fonts = ["Arial", "Helvetica", "Times New Roman", "Courier", "Verdana"]
        ttk.Combobox(font_frame, textvariable=self.font_family_var,
                    values=fonts, width=15).grid(row=0, column=1, padx=5)

        tk.Label(font_frame, text="Title size:").grid(row=1, column=0, sticky=tk.W)
        self.title_size_var = tk.IntVar(value=10)
        tk.Spinbox(font_frame, from_=6, to=20, textvariable=self.title_size_var,
                  width=5).grid(row=1, column=1, padx=5)

        tk.Label(font_frame, text="Label size:").grid(row=2, column=0, sticky=tk.W)
        self.label_size_var = tk.IntVar(value=8)
        tk.Spinbox(font_frame, from_=6, to=20, textvariable=self.label_size_var,
                  width=5).grid(row=2, column=1, padx=5)

        # Colors
        color_frame = tk.LabelFrame(parent, text="Colors", padx=5, pady=5)
        color_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(color_frame, text="Background:").grid(row=0, column=0, sticky=tk.W)
        self.bg_color_var = tk.StringVar(value="#FFFFFF")
        bg_btn = tk.Button(color_frame, bg=self.bg_color_var.get(), width=3,
                          command=self._choose_bg_color)
        bg_btn.grid(row=0, column=1, padx=5)

        # Colormap
        tk.Label(color_frame, text="Colormap:").grid(row=1, column=0, sticky=tk.W)
        self.cmap_var = tk.StringVar(value="viridis")
        cmaps = ["viridis", "plasma", "inferno", "magma", "coolwarm", "RdYlBu", "tab10"]
        ttk.Combobox(color_frame, textvariable=self.cmap_var,
                    values=cmaps, width=10).grid(row=1, column=1, padx=5)

        # Line settings
        line_frame = tk.LabelFrame(parent, text="Lines", padx=5, pady=5)
        line_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(line_frame, text="Line width:").pack(anchor=tk.W)
        self.line_width_var = tk.DoubleVar(value=1.0)
        tk.Scale(line_frame, from_=0.5, to=3.0, resolution=0.5,
                orient=tk.HORIZONTAL, variable=self.line_width_var,
                command=lambda x: self._update_preview()).pack(fill=tk.X)

        # Apply button
        tk.Button(parent, text="🎨 Apply Style", command=self._apply_style,
                 bg="#27ae60", fg="white").pack(pady=10)

    # ============================================================================
    # PREVIEW SETUP
    # ============================================================================
    def _setup_preview(self, parent):
        """Setup the preview canvas"""
        # Canvas for preview
        self.preview_fig = Figure(figsize=(7, 9), dpi=100)
        self.preview_fig.patch.set_facecolor('white')
        self.preview_ax = self.preview_fig.add_axes([0, 0, 1, 1])
        self.preview_ax.set_xlim(0, 1)
        self.preview_ax.set_ylim(0, 1)
        self.preview_ax.set_axis_off()

        self.preview_canvas = FigureCanvasTkAgg(self.preview_fig, parent)
        self.preview_canvas.draw()
        self.preview_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Toolbar
        toolbar_frame = tk.Frame(parent)
        toolbar_frame.pack(fill=tk.X)
        toolbar = NavigationToolbar2Tk(self.preview_canvas, toolbar_frame)
        toolbar.update()

        # Bind mouse events
        self.preview_canvas.mpl_connect('button_press_event', self._on_canvas_click)
        self.preview_canvas.mpl_connect('motion_notify_event', self._on_canvas_move)
        self.preview_canvas.mpl_connect('button_release_event', self._on_canvas_release)

    # ============================================================================
    # PANEL PROPERTIES DIALOG
    # ============================================================================
    def _edit_panel_properties(self):
        """Show comprehensive panel properties dialog"""
        if not self.selected_panel:
            messagebox.showwarning("No Selection", "Select a panel first")
            return

        panel = self.selected_panel

        dialog = tk.Toplevel(self.window)
        dialog.title(f"Panel Properties: {panel.label}")
        dialog.geometry("600x500")
        dialog.transient(self.window)

        # Notebook for tabs
        notebook = ttk.Notebook(dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # TAB 1: BASIC
        basic_tab = tk.Frame(notebook)
        notebook.add(basic_tab, text="Basic")
        self._build_panel_basic_tab(basic_tab, panel)

        # TAB 2: AXES
        axes_tab = tk.Frame(notebook)
        notebook.add(axes_tab, text="Axes")
        self._build_panel_axes_tab(axes_tab, panel)

        # TAB 3: STYLE
        style_tab = tk.Frame(notebook)
        notebook.add(style_tab, text="Style")
        self._build_panel_style_tab(style_tab, panel)

        # TAB 4: DATA
        data_tab = tk.Frame(notebook)
        notebook.add(data_tab, text="Data")
        self._build_panel_data_tab(data_tab, panel)

        # TAB 5: ANNOTATIONS
        annot_tab = tk.Frame(notebook)
        notebook.add(annot_tab, text="Annotations")
        self._build_panel_annot_tab(annot_tab, panel)

        # Buttons
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Apply", command=lambda: self._apply_panel_changes(dialog, panel),
                 bg="#27ae60", fg="white", width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Cancel", command=dialog.destroy,
                 width=10).pack(side=tk.LEFT, padx=5)

    def _build_panel_basic_tab(self, parent, panel):
        """Basic panel properties"""
        frame = tk.Frame(parent, padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Label
        tk.Label(frame, text="Panel Label:").grid(row=0, column=0, sticky=tk.W, pady=5)
        label_var = tk.StringVar(value=panel.label)
        tk.Entry(frame, textvariable=label_var, width=5).grid(row=0, column=1, sticky=tk.W)

        # Title
        tk.Label(frame, text="Title:").grid(row=1, column=0, sticky=tk.W, pady=5)
        title_var = tk.StringVar(value=panel.title)
        tk.Entry(frame, textvariable=title_var, width=30).grid(row=1, column=1, columnspan=2)

        # Plot type
        tk.Label(frame, text="Plot Type:").grid(row=2, column=0, sticky=tk.W, pady=5)
        plot_var = tk.StringVar(value=panel.plot_type)
        plot_combo = ttk.Combobox(frame, textvariable=plot_var,
                                  values=self.PLOT_TYPES, width=15)
        plot_combo.grid(row=2, column=1, sticky=tk.W)

        # Store variables
        panel._temp_vars = {'label': label_var, 'title': title_var, 'plot_type': plot_var}

    def _build_panel_axes_tab(self, parent, panel):
        """Axes properties"""
        frame = tk.Frame(parent, padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # X axis
        tk.Label(frame, text="X Axis:", font=("Arial", 9, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5)

        tk.Label(frame, text="Label:").grid(row=1, column=0, sticky=tk.W, padx=10)
        xlabel_var = tk.StringVar(value=panel.style.get('xlabel', ''))
        tk.Entry(frame, textvariable=xlabel_var, width=20).grid(row=1, column=1)

        tk.Label(frame, text="Min:").grid(row=2, column=0, sticky=tk.W, padx=10)
        xmin_var = tk.StringVar(value=panel.style.get('xmin', ''))
        tk.Entry(frame, textvariable=xmin_var, width=10).grid(row=2, column=1, sticky=tk.W)

        tk.Label(frame, text="Max:").grid(row=2, column=2, sticky=tk.W, padx=5)
        xmax_var = tk.StringVar(value=panel.style.get('xmax', ''))
        tk.Entry(frame, textvariable=xmax_var, width=10).grid(row=2, column=3)

        # Y axis
        tk.Label(frame, text="Y Axis:", font=("Arial", 9, "bold")).grid(row=3, column=0, sticky=tk.W, pady=(15,5))

        tk.Label(frame, text="Label:").grid(row=4, column=0, sticky=tk.W, padx=10)
        ylabel_var = tk.StringVar(value=panel.style.get('ylabel', ''))
        tk.Entry(frame, textvariable=ylabel_var, width=20).grid(row=4, column=1)

        tk.Label(frame, text="Min:").grid(row=5, column=0, sticky=tk.W, padx=10)
        ymin_var = tk.StringVar(value=panel.style.get('ymin', ''))
        tk.Entry(frame, textvariable=ymin_var, width=10).grid(row=5, column=1)

        tk.Label(frame, text="Max:").grid(row=5, column=2, sticky=tk.W, padx=5)
        ymax_var = tk.StringVar(value=panel.style.get('ymax', ''))
        tk.Entry(frame, textvariable=ymax_var, width=10).grid(row=5, column=3)

        # Scale options
        tk.Label(frame, text="Scale:").grid(row=6, column=0, sticky=tk.W, pady=5)
        xlog_var = tk.BooleanVar(value=panel.style.get('xlog', False))
        tk.Checkbutton(frame, text="X log", variable=xlog_var).grid(row=6, column=1, sticky=tk.W)
        ylog_var = tk.BooleanVar(value=panel.style.get('ylog', False))
        tk.Checkbutton(frame, text="Y log", variable=ylog_var).grid(row=6, column=2, sticky=tk.W)

        # Grid
        grid_var = tk.BooleanVar(value=panel.style.get('grid', True))
        tk.Checkbutton(frame, text="Show grid", variable=grid_var).grid(row=7, column=1, sticky=tk.W)

        panel._temp_vars.update({
            'xlabel': xlabel_var, 'xmin': xmin_var, 'xmax': xmax_var,
            'ylabel': ylabel_var, 'ymin': ymin_var, 'ymax': ymax_var,
            'xlog': xlog_var, 'ylog': ylog_var, 'grid': grid_var
        })

    def _build_panel_style_tab(self, parent, panel):
        """Style properties"""
        frame = tk.Frame(parent, padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Color
        tk.Label(frame, text="Color:").grid(row=0, column=0, sticky=tk.W, pady=5)
        color_var = tk.StringVar(value=panel.style.get('color', '#3498db'))
        color_btn = tk.Button(frame, bg=color_var.get(), width=3,
                            command=lambda: self._choose_color(color_var))
        color_btn.grid(row=0, column=1, sticky=tk.W)

        # Marker
        tk.Label(frame, text="Marker:").grid(row=1, column=0, sticky=tk.W, pady=5)
        marker_var = tk.StringVar(value=panel.style.get('marker', 'o'))
        markers = ['o', 's', '^', 'D', 'v', '<', '>', 'p', '*', 'h']
        ttk.Combobox(frame, textvariable=marker_var, values=markers, width=8).grid(row=1, column=1)

        # Size
        tk.Label(frame, text="Marker Size:").grid(row=2, column=0, sticky=tk.W, pady=5)
        size_var = tk.DoubleVar(value=panel.style.get('size', 20))
        tk.Scale(frame, from_=5, to=100, orient=tk.HORIZONTAL,
                variable=size_var, length=150).grid(row=2, column=1)

        # Line style
        tk.Label(frame, text="Line Style:").grid(row=3, column=0, sticky=tk.W, pady=5)
        line_var = tk.StringVar(value=panel.style.get('linestyle', '-'))
        lines = ['-', '--', '-.', ':']
        ttk.Combobox(frame, textvariable=line_var, values=lines, width=8).grid(row=3, column=1)

        # Alpha
        tk.Label(frame, text="Opacity:").grid(row=4, column=0, sticky=tk.W, pady=5)
        alpha_var = tk.DoubleVar(value=panel.style.get('alpha', 0.8))
        tk.Scale(frame, from_=0.1, to=1.0, resolution=0.1,
                orient=tk.HORIZONTAL, variable=alpha_var, length=150).grid(row=4, column=1)

        panel._temp_vars.update({
            'color': color_var, 'marker': marker_var, 'size': size_var,
            'linestyle': line_var, 'alpha': alpha_var
        })

    def _build_panel_data_tab(self, parent, panel):
        """Data mapping properties"""
        frame = tk.Frame(parent, padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # X column
        tk.Label(frame, text="X Data:").grid(row=0, column=0, sticky=tk.W, pady=5)
        xcol_var = tk.StringVar(value=panel.x_col)
        xcol_combo = ttk.Combobox(frame, textvariable=xcol_var,
                                 values=self.numeric_cols, width=20)
        xcol_combo.grid(row=0, column=1)

        # Y column
        tk.Label(frame, text="Y Data:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ycol_var = tk.StringVar(value=panel.y_col)
        ycol_combo = ttk.Combobox(frame, textvariable=ycol_var,
                                 values=self.numeric_cols, width=20)
        ycol_combo.grid(row=1, column=1)

        # Color column
        tk.Label(frame, text="Color by:").grid(row=2, column=0, sticky=tk.W, pady=5)
        colorcol_var = tk.StringVar(value=panel.color_col)
        colorcol_combo = ttk.Combobox(frame, textvariable=colorcol_var,
                                     values=self.categorical_cols, width=20)
        colorcol_combo.grid(row=2, column=1)

        # Size column
        tk.Label(frame, text="Size by:").grid(row=3, column=0, sticky=tk.W, pady=5)
        sizecol_var = tk.StringVar(value=panel.size_col)
        sizecol_combo = ttk.Combobox(frame, textvariable=sizecol_var,
                                    values=self.numeric_cols, width=20)
        sizecol_combo.grid(row=3, column=1)

        panel._temp_vars.update({
            'xcol': xcol_var, 'ycol': ycol_var,
            'colorcol': colorcol_var, 'sizecol': sizecol_var
        })

    def _build_panel_annot_tab(self, parent, panel):
        """Annotations properties"""
        frame = tk.Frame(parent, padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Text annotations
        tk.Label(frame, text="Text Annotations:").pack(anchor=tk.W)

        text_frame = tk.Frame(frame)
        text_frame.pack(fill=tk.X, pady=5)

        self.annot_text = tk.Text(frame, height=5, width=50)
        self.annot_text.pack(fill=tk.X, pady=5)

        # Add current annotations if any
        if 'annotations' in panel.style:
            for annot in panel.style['annotations']:
                self.annot_text.insert(tk.END, annot + '\n')

        tk.Label(frame, text="(One annotation per line)").pack(anchor=tk.W)

    def _apply_panel_changes(self, dialog, panel):
        """Apply panel property changes"""
        # Basic
        panel.label = panel._temp_vars['label'].get()
        panel.title = panel._temp_vars['title'].get()
        panel.plot_type = panel._temp_vars['plot_type'].get()

        # Axes
        panel.style['xlabel'] = panel._temp_vars['xlabel'].get()
        panel.style['xmin'] = panel._temp_vars['xmin'].get()
        panel.style['xmax'] = panel._temp_vars['xmax'].get()
        panel.style['ylabel'] = panel._temp_vars['ylabel'].get()
        panel.style['ymin'] = panel._temp_vars['ymin'].get()
        panel.style['ymax'] = panel._temp_vars['ymax'].get()
        panel.style['xlog'] = panel._temp_vars['xlog'].get()
        panel.style['ylog'] = panel._temp_vars['ylog'].get()
        panel.style['grid'] = panel._temp_vars['grid'].get()

        # Style
        panel.style['color'] = panel._temp_vars['color'].get()
        panel.style['marker'] = panel._temp_vars['marker'].get()
        panel.style['size'] = panel._temp_vars['size'].get()
        panel.style['linestyle'] = panel._temp_vars['linestyle'].get()
        panel.style['alpha'] = panel._temp_vars['alpha'].get()

        # Data
        panel.x_col = panel._temp_vars['xcol'].get()
        panel.y_col = panel._temp_vars['ycol'].get()
        panel.color_col = panel._temp_vars['colorcol'].get()
        panel.size_col = panel._temp_vars['sizecol'].get()

        # Annotations
        annotations = self.annot_text.get("1.0", tk.END).strip().split('\n')
        if annotations and annotations[0]:
            panel.style['annotations'] = [a for a in annotations if a.strip()]

        dialog.destroy()
        self._update_panel_list()
        self._update_preview()

    # ============================================================================
    # INTERACTIVE FUNCTIONS
    # ============================================================================
    def _on_canvas_click(self, event):
        """Handle mouse click on preview"""
        if event.xdata is None or event.ydata is None:
            return

        x, y = event.xdata, event.ydata

        # Check if clicking on a panel
        for panel in reversed(self.current_layout.panels):
            if (panel.x <= x <= panel.x + panel.width and
                panel.y <= y <= panel.y + panel.height):
                self.selected_panel = panel
                self._update_panel_list()
                self._update_preview()
                self.drag_start = (x, y)
                self.status_var.set(f"Selected panel {panel.label}")
                return

        # Click on empty space - deselect
        self.selected_panel = None
        self._update_panel_list()
        self._update_preview()

    def _on_canvas_move(self, event):
        """Handle mouse movement"""
        if event.xdata is None or event.ydata is None:
            return

        x, y = event.xdata, event.ydata
        self.coord_var.set(f"x: {x:.3f}, y: {y:.3f}")

        # Dragging
        if self.drag_start and self.selected_panel:
            dx = x - self.drag_start[0]
            dy = y - self.drag_start[1]

            # Move panel
            new_x = self.selected_panel.x + dx
            new_y = self.selected_panel.y + dy

            # Constrain to figure bounds
            new_x = max(0, min(1 - self.selected_panel.width, new_x))
            new_y = max(0, min(1 - self.selected_panel.height, new_y))

            # Snap to grid
            if self.snap_var.get():
                grid = self.grid_size_var.get() / 1000  # Convert to normalized
                new_x = round(new_x / grid) * grid
                new_y = round(new_y / grid) * grid

            self.selected_panel.x = new_x
            self.selected_panel.y = new_y
            self.drag_start = (x, y)

            self._update_preview()

    def _on_canvas_release(self, event):
        """Handle mouse release"""
        self.drag_start = None
        self._update_preview()

    def _add_panel(self):
        """Add new panel"""
        panel_type = self.panel_type_var.get()

        # Find next label
        used_labels = set(p.label for p in self.current_layout.panels)
        next_label = 'A'
        for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            if c not in used_labels:
                next_label = c
                break

        # Default position
        x = 0.1
        y = 0.1
        if self.current_layout.panels:
            # Offset from last panel
            last = self.current_layout.panels[-1]
            x = min(0.6, last.x + 0.1)
            y = min(0.6, last.y + 0.1)

        panel = Panel(
            type=PanelType(panel_type),
            x=x, y=y, width=0.3, height=0.3,
            label=next_label
        )
        self.current_layout.panels.append(panel)
        self._update_panel_list()
        self._update_preview()

    def _delete_selected_panel(self):
        """Delete selected panel"""
        if self.selected_panel and self.selected_panel in self.current_layout.panels:
            self.current_layout.panels.remove(self.selected_panel)
            self.selected_panel = None
            self._update_panel_list()
            self._update_preview()

    def _update_panel_list(self):
        """Update panel listbox"""
        self.panel_listbox.delete(0, tk.END)

        for i, panel in enumerate(self.current_layout.panels):
            display = f"{panel.label}: {panel.plot_type}"
            if panel.title:
                display += f" - {panel.title[:20]}"
            self.panel_listbox.insert(tk.END, display)

            if panel == self.selected_panel:
                self.panel_listbox.selection_set(i)

    def _on_panel_select(self, event):
        """Handle panel selection from listbox"""
        selection = self.panel_listbox.curselection()
        if selection:
            idx = selection[0]
            if idx < len(self.current_layout.panels):
                self.selected_panel = self.current_layout.panels[idx]
                self._update_preview()

    def _move_panel_up(self):
        """Move panel up in Z-order"""
        if self.selected_panel and self.selected_panel in self.current_layout.panels:
            idx = self.current_layout.panels.index(self.selected_panel)
            if idx > 0:
                self.current_layout.panels.insert(idx-1,
                    self.current_layout.panels.pop(idx))
                self._update_panel_list()
                self._update_preview()

    def _move_panel_down(self):
        """Move panel down in Z-order"""
        if self.selected_panel and self.selected_panel in self.current_layout.panels:
            idx = self.current_layout.panels.index(self.selected_panel)
            if idx < len(self.current_layout.panels) - 1:
                self.current_layout.panels.insert(idx+1,
                    self.current_layout.panels.pop(idx))
                self._update_panel_list()
                self._update_preview()

    # ============================================================================
    # PREVIEW UPDATE
    # ============================================================================
    def _update_preview(self):
        """Update the preview canvas"""
        self.preview_ax.clear()
        self.preview_ax.set_xlim(0, 1)
        self.preview_ax.set_ylim(0, 1)

        # Update figure size
        width = self.width_var.get()
        height = self.height_var.get()
        zoom = self.zoom_var.get()
        self.preview_fig.set_size_inches(width * zoom, height * zoom)

        # Draw background
        self.preview_ax.add_patch(Rectangle((0, 0), 1, 1,
                                           facecolor=self.bg_color_var.get(),
                                           edgecolor='black', linewidth=1))

        # Draw grid
        if self.show_grid_var.get():
            grid = self.grid_size_var.get() / 1000
            for i in range(int(1/grid) + 1):
                x = i * grid
                self.preview_ax.axvline(x, color='#cccccc', linewidth=0.5, alpha=0.5)
                self.preview_ax.axhline(x, color='#cccccc', linewidth=0.5, alpha=0.5)

        # Draw panels
        for panel in self.current_layout.panels:
            if not panel.visible:
                continue

            # Panel rectangle
            edgecolor = 'red' if panel == self.selected_panel else 'black'
            linewidth = 2 if panel == self.selected_panel else 1

            rect = Rectangle((panel.x, panel.y), panel.width, panel.height,
                           facecolor='white', edgecolor=edgecolor,
                           linewidth=linewidth, alpha=0.9)
            self.preview_ax.add_patch(rect)

            # Panel label
            self.preview_ax.text(panel.x + 0.01, panel.y + panel.height - 0.02,
                               panel.label, fontsize=10, fontweight='bold',
                               verticalalignment='top')

            # Panel title
            if panel.title:
                self.preview_ax.text(panel.x + panel.width/2,
                                   panel.y + panel.height - 0.02,
                                   panel.title, fontsize=8,
                                   ha='center', va='top')

            # Plot type indicator
            self.preview_ax.text(panel.x + 0.01, panel.y + 0.01,
                               panel.plot_type, fontsize=6, color='gray',
                               va='bottom')

        self.preview_ax.set_axis_off()
        self.preview_canvas.draw()

    # ============================================================================
    # UTILITY FUNCTIONS
    # ============================================================================
    def _choose_color(self, var):
        """Open color chooser"""
        color = colorchooser.askcolor(title="Choose Color", parent=self.window)
        if color[1]:
            var.set(color[1])

    def _choose_bg_color(self):
        """Choose background color"""
        color = colorchooser.askcolor(title="Background Color", parent=self.window)
        if color[1]:
            self.bg_color_var.set(color[1])
            self._update_preview()

    def _apply_style(self):
        """Apply style settings"""
        self.current_layout.font_family = self.font_family_var.get()
        self.current_layout.font_sizes['title'] = self.title_size_var.get()
        self.current_layout.font_sizes['label'] = self.label_size_var.get()
        self.current_layout.background_color = self.bg_color_var.get()
        self._update_preview()

    def _apply_journal_style(self):
        """Apply journal style template"""
        journal = self.journal_var.get()
        self.current_layout.style = JournalStyle(journal)
        self.current_layout.apply_journal_style()

        # Update UI
        self.width_var.set(self.current_layout.width)
        self.height_var.set(self.current_layout.height)
        self.dpi_var.set(self.current_layout.dpi)
        self.font_family_var.set(self.current_layout.font_family)
        self.title_size_var.set(self.current_layout.font_sizes['title'])
        self.label_size_var.set(self.current_layout.font_sizes['label'])

        self._update_preview()

    def _refresh_data_from_app(self):
        """Refresh data from main app"""
        self._refresh_data()

        # Update column listboxes
        self.numeric_listbox.delete(0, tk.END)
        for col in self.numeric_cols:
            self.numeric_listbox.insert(tk.END, col)

        self.cat_listbox.delete(0, tk.END)
        for col in self.categorical_cols:
            self.cat_listbox.insert(tk.END, col)

        self.status_var.set(f"✅ Refreshed data: {len(self.df)} samples")

    # ============================================================================
    # TEMPLATE FUNCTIONS
    # ============================================================================
    def _apply_template(self, template_name):
        """Apply predefined template"""
        if template_name == "grid_2x2":
            self.current_layout.panels = []
            labels = ['A', 'B', 'C', 'D']
            positions = [
                (0.1, 0.55, 0.35, 0.35),
                (0.55, 0.55, 0.35, 0.35),
                (0.1, 0.1, 0.35, 0.35),
                (0.55, 0.1, 0.35, 0.35)
            ]
            for i, ((x, y, w, h), label) in enumerate(zip(positions, labels)):
                panel = Panel(x=x, y=y, width=w, height=h, label=label)
                self.current_layout.panels.append(panel)

        elif template_name == "main_sidebar":
            self.current_layout.panels = [
                Panel(x=0.1, y=0.1, width=0.55, height=0.8, label='A'),
                Panel(x=0.7, y=0.1, width=0.25, height=0.35, label='B'),
                Panel(x=0.7, y=0.5, width=0.25, height=0.4, label='C')
            ]

        self._update_panel_list()
        self._update_preview()

    def _save_as_template(self):
        """Save current layout as template"""
        name = tk.simpledialog.askstring("Template Name", "Enter template name:",
                                        parent=self.window)
        if name:
            self.current_layout.name = name
            self.layouts.append(self.current_layout)
            self.template_listbox.insert(tk.END, name)
            self._save_layouts()
            self.status_var.set(f"✅ Saved '{name}' as template")

    def _load_template(self):
        """Load selected template"""
        selection = self.template_listbox.curselection()
        if selection:
            idx = selection[0]
            if idx < len(self.layouts):
                self.current_layout = self.layouts[idx]
                self.name_var.set(self.current_layout.name)
                self._update_panel_list()
                self._update_preview()
                self.status_var.set(f"✅ Loaded '{self.current_layout.name}'")

    def _delete_template(self):
        """Delete selected template"""
        selection = self.template_listbox.curselection()
        if selection:
            idx = selection[0]
            if idx < len(self.layouts):
                name = self.layouts[idx].name
                if messagebox.askyesno("Confirm", f"Delete '{name}'?"):
                    self.layouts.pop(idx)
                    self.template_listbox.delete(idx)
                    self._save_layouts()
                    self.status_var.set(f"🗑️ Deleted '{name}'")

    # ============================================================================
    # SAVE/LOAD
    # ============================================================================
    def _save_current_layout(self):
        """Save current layout"""
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("Layout files", "*.json"), ("All files", "*.*")]
        )
        if path:
            try:
                self.current_layout.name = self.name_var.get()
                with open(path, 'w') as f:
                    json.dump(self.current_layout.to_dict(), f, indent=2)
                self.status_var.set(f"✅ Saved to {Path(path).name}")
            except Exception as e:
                messagebox.showerror("Error", f"Save failed: {e}")

    def _load_layout_dialog(self):
        """Load layout from file"""
        path = filedialog.askopenfilename(
            filetypes=[("Layout files", "*.json"), ("All files", "*.*")]
        )
        if path:
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                self.current_layout = FigureLayout.from_dict(data)
                self.name_var.set(self.current_layout.name)
                self._update_panel_list()
                self._update_preview()
                self.status_var.set(f"✅ Loaded {Path(path).name}")
            except Exception as e:
                messagebox.showerror("Error", f"Load failed: {e}")

    # ============================================================================
    # EXPORT
    # ============================================================================
    def _export_figure(self):
        """Export figure to file"""
        if not self.current_layout.panels:
            messagebox.showwarning("No Panels", "Add panels before exporting")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[
                ("PNG", "*.png"), ("PDF", "*.pdf"),
                ("SVG", "*.svg"), ("EPS", "*.eps"), ("TIFF", "*.tiff")
            ]
        )
        if not path:
            return

        try:
            self.progress.start()
            self.status_var.set("Rendering figure...")

            # Create figure with correct dimensions
            dpi = self.dpi_var.get()
            width = self.width_var.get()
            height = self.height_var.get()

            fig = plt.figure(figsize=(width, height), dpi=dpi)
            fig.patch.set_facecolor(self.bg_color_var.get())

            # Calculate margins
            margin_left = 0.05
            margin_right = 0.05
            margin_top = 0.05
            margin_bottom = 0.05

            # Add each panel
            for i, panel in enumerate(self.current_layout.panels):
                if not panel.visible:
                    continue

                # Convert normalized coordinates to figure coordinates
                left = panel.x * (1 - margin_left - margin_right) + margin_left
                bottom = panel.y * (1 - margin_bottom - margin_top) + margin_bottom
                width_panel = panel.width * (1 - margin_left - margin_right)
                height_panel = panel.height * (1 - margin_bottom - margin_top)

                # Create subplot
                ax = fig.add_axes([left, bottom, width_panel, height_panel])

                # Set title and labels
                if panel.title:
                    ax.set_title(panel.title, fontsize=self.title_size_var.get())

                # Apply style
                ax.tick_params(labelsize=self.current_layout.font_sizes.get('tick', 7))

                if panel.style.get('grid', True):
                    ax.grid(True, alpha=0.3)

                # Add sample data for preview
                if self.df is not None and panel.x_col and panel.y_col:
                    x_data = self.df[panel.x_col]
                    y_data = self.df[panel.y_col]

                    if panel.plot_type == "scatter":
                        ax.scatter(x_data, y_data,
                                 alpha=panel.style.get('alpha', 0.8),
                                 s=panel.style.get('size', 20))
                    elif panel.plot_type == "line":
                        ax.plot(x_data, y_data,
                              linewidth=panel.style.get('size', 1) / 10)
                    elif panel.plot_type == "histogram":
                        ax.hist(x_data, bins=20, alpha=0.7)
                    elif panel.plot_type == "boxplot":
                        ax.boxplot(y_data)
                    elif panel.plot_type == "bar":
                        ax.bar(range(len(x_data)), x_data)

                # Panel label
                ax.text(-0.1, 1.05, panel.label, transform=ax.transAxes,
                       fontsize=12, fontweight='bold', va='top')

            # Save
            fig.savefig(path, dpi=dpi, bbox_inches='tight')
            plt.close(fig)

            self.progress.stop()
            self.status_var.set(f"✅ Exported to {Path(path).name}")

        except Exception as e:
            self.progress.stop()
            messagebox.showerror("Export Error", f"Failed to export: {e}")

    # ============================================================================
    # UTILITIES
    # ============================================================================
    def _toggle_grid(self):
        """Toggle grid visibility"""
        self.show_grid_var.set(not self.show_grid_var.get())
        self._update_preview()

    def _undo(self):
        """Undo last action (placeholder)"""
        self.status_var.set("Undo not implemented")

    def _redo(self):
        """Redo last action (placeholder)"""
        self.status_var.set("Redo not implemented")


# ============================================================================
# PLUGIN SETUP - SINGLE FUNCTION
# ============================================================================
def setup_plugin(main_app):
    """Plugin setup function"""
    plugin = PublicationLayoutsPlugin(main_app)
    return plugin
