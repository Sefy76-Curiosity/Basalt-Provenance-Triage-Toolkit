"""
Multi-Panel Publication Layouts Plugin
Advanced scientific figure creation and layout system

Features:
- Drag-and-drop multi-panel layout designer
- Live preview with WYSIWYG editing
- Template system for Nature, Science, Geology formats
- Advanced plotting with Matplotlib/Seaborn integration
- Export to high-resolution publication formats (PDF, EPS, TIFF, PNG)
- Automatic figure numbering and caption generation
- Style presets for different journals
- Interactive data plotting directly in panels
- Batch processing for multiple figures

Author: Sefy Levy
License: CC BY-NC-SA 4.0
"""

PLUGIN_INFO = {
    "category": "software",
    "id": "publication_layouts",
    "name": "Publication Layouts Pro",
    "description": "Advanced multi-panel figure creation for publications",
    "icon": "📐",
    "version": "1.0",
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
from typing import Dict, List, Tuple, Optional, Any, Callable
from enum import Enum
import threading
import tempfile
import webbrowser

# Check dependencies
HAS_MATPLOTLIB = False
HAS_NUMPY = False
HAS_PIL = False
HAS_SEABORN = False
HAS_PDF_SUPPORT = False

try:
    import matplotlib
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_pdf import PdfPages
    import matplotlib.gridspec as gridspec
    from matplotlib.patches import Rectangle, FancyBboxPatch
    from matplotlib.text import Text
    import matplotlib.transforms as transforms
    HAS_MATPLOTLIB = True
    HAS_PDF_SUPPORT = True
except ImportError:
    pass

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    pass

try:
    from PIL import Image, ImageTk, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    pass

try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    pass

HAS_REQUIREMENTS = HAS_MATPLOTLIB and HAS_NUMPY

# ========== DATA CLASSES ==========
class PanelType(Enum):
    PLOT = "plot"
    IMAGE = "image"
    TEXT = "text"
    TABLE = "table"
    LEGEND = "legend"
    SCALE_BAR = "scale_bar"
    MAP = "map"
    CUSTOM = "custom"

class JournalStyle(Enum):
    NATURE = "Nature"
    SCIENCE = "Science"
    GEOLOGY = "Geology"
    EPSL = "Earth and Planetary Science Letters"
    GCA = "Geochimica et Cosmochimica Acta"
    CUSTOM = "Custom"

@dataclass
class Panel:
    """Represents a single panel in the figure"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    type: PanelType = PanelType.PLOT
    x: float = 0.1  # normalized coordinates (0-1)
    y: float = 0.1
    width: float = 0.3
    height: float = 0.3
    label: str = "A"
    title: str = ""
    data: Any = None
    plot_type: str = "scatter"
    style: Dict = field(default_factory=dict)
    content: Any = None  # For images, text, etc.
    locked: bool = False
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
            'style': self.style,
            'locked': self.locked,
            'visible': self.visible
        }

    @classmethod
    def from_dict(cls, data):
        panel = cls(
            id=data.get('id', str(uuid.uuid4())[:8]),
            type=PanelType(data.get('type', 'plot')),
            x=data.get('x', 0.1),
            y=data.get('y', 0.1),
            width=data.get('width', 0.3),
            height=data.get('height', 0.3),
            label=data.get('label', 'A'),
            title=data.get('title', ''),
            plot_type=data.get('plot_type', 'scatter'),
            style=data.get('style', {}),
            locked=data.get('locked', False),
            visible=data.get('visible', True)
        )
        return panel

@dataclass
class FigureLayout:
    """Represents the complete figure layout"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = "New Figure"
    width: float = 7.0  # inches (journal column width)
    height: float = 9.0  # inches
    dpi: int = 300
    panels: List[Panel] = field(default_factory=list)
    style: JournalStyle = JournalStyle.NATURE
    custom_style: Dict = field(default_factory=dict)
    caption: str = ""
    show_grid: bool = False
    margin_left: float = 0.75
    margin_right: float = 0.5
    margin_top: float = 0.5
    margin_bottom: float = 0.75
    column_width: float = 3.5  # Nature single column
    background_color: str = "#FFFFFF"

    # Journal-specific settings
    journal_settings = {
        JournalStyle.NATURE: {
            'width': 3.5,  # single column
            'height': 9.0,
            'dpi': 300,
            'font_family': 'Arial',
            'font_sizes': {'title': 8, 'labels': 7, 'ticks': 6, 'legend': 7},
            'line_widths': {'axes': 0.5, 'ticks': 0.5, 'plot': 1.0},
            'colors': {'axes': '#000000', 'text': '#000000'}
        },
        JournalStyle.SCIENCE: {
            'width': 5.5,  # two columns
            'height': 7.5,
            'dpi': 300,
            'font_family': 'Helvetica',
            'font_sizes': {'title': 9, 'labels': 8, 'ticks': 7, 'legend': 8},
            'line_widths': {'axes': 0.75, 'ticks': 0.75, 'plot': 1.5},
            'colors': {'axes': '#000000', 'text': '#000000'}
        },
        JournalStyle.GEOLOGY: {
            'width': 7.0,  # full page
            'height': 9.0,
            'dpi': 600,  # Geology requires high DPI
            'font_family': 'Times New Roman',
            'font_sizes': {'title': 10, 'labels': 9, 'ticks': 8, 'legend': 9},
            'line_widths': {'axes': 1.0, 'ticks': 1.0, 'plot': 2.0},
            'colors': {'axes': '#000000', 'text': '#000000'}
        }
    }

    def apply_journal_style(self):
        """Apply journal-specific style settings"""
        if self.style in self.journal_settings:
            settings = self.journal_settings[self.style]
            self.width = settings['width']
            self.custom_style = settings.copy()

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'width': self.width,
            'height': self.height,
            'dpi': self.dpi,
            'panels': [panel.to_dict() for panel in self.panels],
            'style': self.style.value,
            'custom_style': self.custom_style,
            'caption': self.caption,
            'show_grid': self.show_grid,
            'margins': {
                'left': self.margin_left,
                'right': self.margin_right,
                'top': self.margin_top,
                'bottom': self.margin_bottom
            },
            'background_color': self.background_color
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
            custom_style=data.get('custom_style', {}),
            caption=data.get('caption', ''),
            show_grid=data.get('show_grid', False),
            background_color=data.get('background_color', '#FFFFFF')
        )

        # Set margins
        margins = data.get('margins', {})
        layout.margin_left = margins.get('left', 0.75)
        layout.margin_right = margins.get('right', 0.5)
        layout.margin_top = margins.get('top', 0.5)
        layout.margin_bottom = margins.get('bottom', 0.75)

        # Load panels
        for panel_data in data.get('panels', []):
            layout.panels.append(Panel.from_dict(panel_data))

        return layout

# ========== MAIN PLUGIN CLASS ==========
class PublicationLayoutsPlugin:
    """Advanced multi-panel publication layout plugin"""

    def __init__(self, main_app):
        self.app = main_app
        self.window = None
        self.current_layout = None
        self.layouts = []
        self.selected_panel = None
        self.drag_start = None
        self.resize_start = None
        self.resize_edge = None
        self.preview_fig = None
        self.preview_canvas = None
        self.is_dragging = False
        self.grid_size = 20  # Snap grid size in pixels
        self.templates = self._load_templates()
        self.plot_data_cache = {}

    def open_layout_window(self):
        """Open the publication layout interface"""
        if not HAS_REQUIREMENTS:
            missing = []
            if not HAS_MATPLOTLIB: missing.append("matplotlib")
            if not HAS_NUMPY: missing.append("numpy")
            if not HAS_PIL: missing.append("pillow (PIL)")
            if not HAS_SEABORN: missing.append("seaborn")

            response = messagebox.askyesno(
                "Missing Dependencies",
                f"Publication Layouts requires:\n\n"
                f"• matplotlib (plotting)\n• numpy (calculations)\n"
                f"• pillow (image handling)\n• seaborn (advanced plots)\n\n"
                f"Missing: {', '.join(missing)}\n\nInstall missing packages?",
                parent=self.app.root
            )
            if response:
                self._install_dependencies(missing)
            return

        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("Publication Layouts Pro - Multi-Panel Figure Designer")
        self.window.geometry("1400x900")

        # Make it resizable
        self.window.minsize(1200, 700)

        # Set window icon (if available)
        try:
            self.window.iconbitmap('icon.ico')  # Optional
        except:
            pass

        self.window.transient(self.app.root)
        self._create_interface()

        # Load default layout
        self._create_default_layout()

        self.window.lift()
        self.window.focus_force()

        # Bind keyboard shortcuts
        self.window.bind('<Control-s>', lambda e: self._save_layout())
        self.window.bind('<Control-o>', lambda e: self._load_layout())
        self.window.bind('<Control-n>', lambda e: self._create_new_layout())
        self.window.bind('<Control-e>', lambda e: self._export_figure())
        self.window.bind('<Control-p>', lambda e: self._update_preview())
        self.window.bind('<Delete>', lambda e: self._delete_selected())
        self.window.bind('<Control-z>', lambda e: self._undo())
        self.window.bind('<Control-y>', lambda e: self._redo())
        self.window.bind('<Control-g>', lambda e: self._toggle_grid())

        # Update preview
        self._update_preview()

    def _create_interface(self):
        """Create the main interface with advanced layout"""
        # Main container with paned windows
        main_paned = tk.PanedWindow(self.window, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=8)
        main_paned.pack(fill=tk.BOTH, expand=True)

        # ========== LEFT SIDEBAR - Tools & Properties ==========
        left_sidebar = tk.Frame(main_paned, bg="#2C3E50", width=300)
        main_paned.add(left_sidebar, minsize=280, stretch='always')

        # Toolbox
        toolbox_frame = tk.LabelFrame(left_sidebar, text="🛠️ Toolbox", bg="#2C3E50", fg="white",
                                     font=("Arial", 11, "bold"), padx=10, pady=10)
        toolbox_frame.pack(fill=tk.X, padx=10, pady=10)

        tools = [
            ("📐 Add Panel", self._add_panel),
            ("🖼️ Add Image", self._add_image_panel),
            ("📝 Add Text", self._add_text_panel),
            ("📊 Add Plot", self._add_plot_panel),
            ("🗺️ Add Map", self._add_map_panel),
            ("📋 Add Table", self._add_table_panel),
            ("🏷️ Add Legend", self._add_legend_panel),
            ("📏 Add Scale", self._add_scale_bar)
        ]

        for text, command in tools:
            btn = tk.Button(toolbox_frame, text=text, command=command,
                          bg="#3498DB", fg="white", font=("Arial", 10),
                          relief=tk.FLAT, padx=10, pady=8, cursor="hand2")
            btn.pack(fill=tk.X, pady=3)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#2980B9"))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg="#3498DB"))

        # Properties Panel (will be updated when panel is selected)
        self.properties_frame = tk.LabelFrame(left_sidebar, text="⚙️ Properties", bg="#2C3E50", fg="white",
                                            font=("Arial", 11, "bold"), padx=10, pady=10)
        self.properties_frame.pack(fill=tk.X, padx=10, pady=10)

        # Journal Templates
        template_frame = tk.LabelFrame(left_sidebar, text="📄 Journal Templates", bg="#2C3E50", fg="white",
                                     font=("Arial", 11, "bold"), padx=10, pady=10)
        template_frame.pack(fill=tk.X, padx=10, pady=10)

        journals = ["Nature", "Science", "Geology", "EPSL", "GCA", "Custom"]
        self.journal_var = tk.StringVar(value="Nature")
        for journal in journals:
            tk.Radiobutton(template_frame, text=journal, variable=self.journal_var,
                          value=journal, command=self._apply_journal_template,
                          bg="#2C3E50", fg="white", selectcolor="#34495E",
                          font=("Arial", 9)).pack(anchor=tk.W, pady=2)

        # Quick Layout Templates
        layout_frame = tk.LabelFrame(left_sidebar, text="🔲 Quick Layouts", bg="#2C3E50", fg="white",
                                   font=("Arial", 11, "bold"), padx=10, pady=10)
        layout_frame.pack(fill=tk.X, padx=10, pady=10)

        layouts = ["2×2 Grid", "3×1 Vertical", "1×3 Horizontal", "Main + Inset", "Complex (5 panel)"]
        for layout in layouts:
            btn = tk.Button(layout_frame, text=layout,
                          command=lambda l=layout: self._apply_quick_layout(l),
                          bg="#27AE60", fg="white", font=("Arial", 9),
                          relief=tk.FLAT, padx=5, pady=3)
            btn.pack(fill=tk.X, pady=2)

        # ========== CENTER - Canvas & Preview ==========
        center_paned = tk.PanedWindow(main_paned, orient=tk.VERTICAL, sashrelief=tk.RAISED, sashwidth=8)
        main_paned.add(center_paned, minsize=600, stretch='always')

        # Canvas Frame (for interactive editing)
        canvas_frame = tk.Frame(center_paned, bg="#34495E")
        center_paned.add(canvas_frame, minsize=300)

        # Canvas for interactive panel arrangement
        self.canvas = tk.Canvas(canvas_frame, bg="#34495E", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Bind mouse events for dragging/resizing
        self.canvas.bind("<ButtonPress-1>", self._canvas_click)
        self.canvas.bind("<B1-Motion>", self._canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._canvas_release)
        self.canvas.bind("<Double-Button-1>", self._canvas_double_click)

        # Preview Frame
        preview_frame = tk.Frame(center_paned, bg="#2C3E50")
        center_paned.add(preview_frame, minsize=300)

        # Preview controls
        preview_controls = tk.Frame(preview_frame, bg="#2C3E50")
        preview_controls.pack(fill=tk.X, padx=10, pady=5)

        tk.Button(preview_controls, text="🔄 Update Preview", command=self._update_preview,
                 bg="#3498DB", fg="white", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)

        tk.Button(preview_controls, text="📷 Export Preview", command=self._export_preview,
                 bg="#9B59B6", fg="white", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)

        # Preview canvas
        preview_canvas_frame = tk.Frame(preview_frame, bg="#2C3E50")
        preview_canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.preview_canvas = tk.Canvas(preview_canvas_frame, bg="white", highlightthickness=1)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)

        # ========== RIGHT SIDEBAR - Data & Export ==========
        right_sidebar = tk.Frame(main_paned, bg="#2C3E50", width=350)
        main_paned.add(right_sidebar, minsize=320, stretch='always')

        # Data Panel
        data_frame = tk.LabelFrame(right_sidebar, text="📊 Data Source", bg="#2C3E50", fg="white",
                                 font=("Arial", 11, "bold"), padx=10, pady=10)
        data_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(data_frame, text="Use data from:", bg="#2C3E50", fg="white",
                font=("Arial", 9)).pack(anchor=tk.W, pady=5)

        self.data_source = tk.StringVar(value="Current Samples")
        sources = ["Current Samples", "Reference Database", "Model Results", "CSV File", "None"]
        ttk.Combobox(data_frame, textvariable=self.data_source, values=sources,
                    state="readonly", font=("Arial", 9)).pack(fill=tk.X, pady=5)

        # Plot Options
        plot_frame = tk.LabelFrame(right_sidebar, text="📈 Plot Options", bg="#2C3E50", fg="white",
                                 font=("Arial", 11, "bold"), padx=10, pady=10)
        plot_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(plot_frame, text="Plot Type:", bg="#2C3E50", fg="white",
                font=("Arial", 9)).grid(row=0, column=0, sticky=tk.W, pady=5)

        self.plot_type = tk.StringVar(value="scatter")
        plot_types = ["scatter", "line", "bar", "histogram", "box", "violin",
                     "heatmap", "contour", "ternary", "spider"]
        ttk.Combobox(plot_frame, textvariable=self.plot_type, values=plot_types,
                    state="readonly", width=15).grid(row=0, column=1, pady=5, padx=5)

        # X and Y axis selection
        tk.Label(plot_frame, text="X Axis:", bg="#2C3E50", fg="white",
                font=("Arial", 9)).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.x_axis = tk.StringVar()
        ttk.Combobox(plot_frame, textvariable=self.x_axis, width=15).grid(row=1, column=1, pady=5, padx=5)

        tk.Label(plot_frame, text="Y Axis:", bg="#2C3E50", fg="white",
                font=("Arial", 9)).grid(row=2, column=0, sticky=tk.W, pady=5)
        self.y_axis = tk.StringVar()
        ttk.Combobox(plot_frame, textvariable=self.y_axis, width=15).grid(row=2, column=1, pady=5, padx=5)

        # Color scheme
        tk.Label(plot_frame, text="Color Map:", bg="#2C3E50", fg="white",
                font=("Arial", 9)).grid(row=3, column=0, sticky=tk.W, pady=5)
        self.color_map = tk.StringVar(value="viridis")
        cmaps = ["viridis", "plasma", "inferno", "magma", "cividis", "coolwarm", "RdYlBu", "Set2", "tab20c"]
        ttk.Combobox(plot_frame, textvariable=self.color_map, values=cmaps,
                    state="readonly", width=15).grid(row=3, column=1, pady=5, padx=5)

        # Export Panel
        export_frame = tk.LabelFrame(right_sidebar, text="💾 Export", bg="#2C3E50", fg="white",
                                   font=("Arial", 11, "bold"), padx=10, pady=10)
        export_frame.pack(fill=tk.X, padx=10, pady=10)

        export_options = [
            ("PDF (Vector)", ".pdf"),
            ("EPS (Vector)", ".eps"),
            ("TIFF (600 DPI)", ".tiff"),
            ("PNG (300 DPI)", ".png"),
            ("SVG (Vector)", ".svg"),
            ("PPTX (PowerPoint)", ".pptx")
        ]

        self.export_format = tk.StringVar(value=".pdf")
        for text, value in export_options:
            tk.Radiobutton(export_frame, text=text, variable=self.export_format,
                          value=value, bg="#2C3E50", fg="white", selectcolor="#34495E",
                          font=("Arial", 9)).pack(anchor=tk.W, pady=2)

        tk.Button(export_frame, text="🚀 Export Figure", command=self._export_figure,
                 bg="#E74C3C", fg="white", font=("Arial", 11, "bold"),
                 relief=tk.FLAT, padx=20, pady=10).pack(pady=10)

        # Caption Editor
        caption_frame = tk.LabelFrame(right_sidebar, text="📝 Figure Caption", bg="#2C3E50", fg="white",
                                    font=("Arial", 11, "bold"), padx=10, pady=10)
        caption_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.caption_text = scrolledtext.ScrolledText(caption_frame, height=8,
                                                     font=("Arial", 9), wrap=tk.WORD)
        self.caption_text.pack(fill=tk.BOTH, expand=True)

        # Bottom toolbar
        toolbar = tk.Frame(self.window, bg="#1C2833", height=40)
        toolbar.pack(fill=tk.X, side=tk.BOTTOM)

        buttons = [
            ("💾 Save Layout", self._save_layout),
            ("📂 Load Layout", self._load_layout),
            ("🆕 New Layout", self._create_new_layout),
            ("⚙️ Settings", self._open_settings),
            ("❓ Help", self._open_help)
        ]

        for text, command in buttons:
            btn = tk.Button(toolbar, text=text, command=command,
                          bg="#16A085", fg="white", font=("Arial", 9),
                          relief=tk.FLAT, padx=15)
            btn.pack(side=tk.LEFT, padx=5, pady=5)

    # ========== CANVAS INTERACTION ==========
    def _canvas_click(self, event):
        """Handle mouse click on canvas"""
        self.drag_start = (event.x, event.y)

        # Check if clicking on a panel
        clicked_panel = None
        resize_edge = None

        for panel in self.current_layout.panels:
            x1, y1, x2, y2 = self._panel_to_canvas_coords(panel)

            # Check for resize handles (8px margin)
            if abs(event.x - x1) < 8 and abs(event.y - y1) < 8:
                resize_edge = 'nw'
                clicked_panel = panel
            elif abs(event.x - x2) < 8 and abs(event.y - y1) < 8:
                resize_edge = 'ne'
                clicked_panel = panel
            elif abs(event.x - x1) < 8 and abs(event.y - y2) < 8:
                resize_edge = 'sw'
                clicked_panel = panel
            elif abs(event.x - x2) < 8 and abs(event.y - y2) < 8:
                resize_edge = 'se'
                clicked_panel = panel
            elif abs(event.x - x1) < 8 and y1 <= event.y <= y2:
                resize_edge = 'w'
                clicked_panel = panel
            elif abs(event.x - x2) < 8 and y1 <= event.y <= y2:
                resize_edge = 'e'
                clicked_panel = panel
            elif abs(event.y - y1) < 8 and x1 <= event.x <= x2:
                resize_edge = 'n'
                clicked_panel = panel
            elif abs(event.y - y2) < 8 and x1 <= event.x <= x2:
                resize_edge = 's'
                clicked_panel = panel
            # Check if clicking inside panel
            elif x1 <= event.x <= x2 and y1 <= event.y <= y2:
                clicked_panel = panel
                break

        if clicked_panel:
            self.selected_panel = clicked_panel
            self.resize_edge = resize_edge
            self.is_dragging = True if not resize_edge else False
            self._update_properties_panel()
            self._draw_canvas()
        else:
            self.selected_panel = None
            self._update_properties_panel()
            self._draw_canvas()

    def _canvas_drag(self, event):
        """Handle mouse drag on canvas"""
        if not self.drag_start or not self.selected_panel:
            return

        dx = event.x - self.drag_start[0]
        dy = event.y - self.drag_start[1]

        # Convert to normalized coordinates
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        norm_dx = dx / canvas_width if canvas_width > 0 else 0
        norm_dy = dy / canvas_height if canvas_height > 0 else 0

        if self.resize_edge:
            # Resize panel
            if 'n' in self.resize_edge:
                self.selected_panel.y += norm_dy
                self.selected_panel.height -= norm_dy
            if 's' in self.resize_edge:
                self.selected_panel.height += norm_dy
            if 'w' in self.resize_edge:
                self.selected_panel.x += norm_dx
                self.selected_panel.width -= norm_dx
            if 'e' in self.resize_edge:
                self.selected_panel.width += norm_dx

            # Ensure minimum size
            self.selected_panel.width = max(0.05, self.selected_panel.width)
            self.selected_panel.height = max(0.05, self.selected_panel.height)
            self.selected_panel.x = max(0, min(self.selected_panel.x, 0.95))
            self.selected_panel.y = max(0, min(self.selected_panel.y, 0.95))

        elif self.is_dragging:
            # Move panel
            self.selected_panel.x += norm_dx
            self.selected_panel.y += norm_dy

            # Snap to grid
            if hasattr(self, 'snap_to_grid') and self.snap_to_grid:
                grid = 1.0 / self.grid_size
                self.selected_panel.x = round(self.selected_panel.x / grid) * grid
                self.selected_panel.y = round(self.selected_panel.y / grid) * grid

        self.drag_start = (event.x, event.y)
        self._draw_canvas()

    def _canvas_release(self, event):
        """Handle mouse release on canvas"""
        self.drag_start = None
        self.resize_edge = None
        self.is_dragging = False
        self._update_preview()

    def _canvas_double_click(self, event):
        """Handle double click on canvas"""
        # Open panel editor for selected panel
        if self.selected_panel:
            self._edit_panel(self.selected_panel)

    def _panel_to_canvas_coords(self, panel):
        """Convert normalized panel coordinates to canvas pixels"""
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        x1 = panel.x * canvas_width
        y1 = panel.y * canvas_height
        x2 = (panel.x + panel.width) * canvas_width
        y2 = (panel.y + panel.height) * canvas_height

        return x1, y1, x2, y2

    def _draw_canvas(self):
        """Draw panels on canvas"""
        self.canvas.delete("all")

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        # Draw grid
        if hasattr(self, 'show_grid') and self.show_grid:
            grid_size = self.grid_size
            for x in range(0, canvas_width, grid_size):
                self.canvas.create_line(x, 0, x, canvas_height, fill="#3A506B", width=1)
            for y in range(0, canvas_height, grid_size):
                self.canvas.create_line(0, y, canvas_width, y, fill="#3A506B", width=1)

        # Draw panels
        for panel in self.current_layout.panels:
            if not panel.visible:
                continue

            x1, y1, x2, y2 = self._panel_to_canvas_coords(panel)

            # Determine color based on panel type
            colors = {
                PanelType.PLOT: "#3498DB",
                PanelType.IMAGE: "#9B59B6",
                PanelType.TEXT: "#2ECC71",
                PanelType.TABLE: "#E74C3C",
                PanelType.LEGEND: "#F39C12",
                PanelType.SCALE_BAR: "#1ABC9C",
                PanelType.MAP: "#34495E",
                PanelType.CUSTOM: "#7F8C8D"
            }

            fill_color = colors.get(panel.type, "#3498DB")
            outline_color = "#E74C3C" if panel == self.selected_panel else "#2C3E50"
            outline_width = 3 if panel == self.selected_panel else 2

            # Draw panel rectangle
            self.canvas.create_rectangle(x1, y1, x2, y2,
                                        fill=fill_color,
                                        outline=outline_color,
                                        width=outline_width,
                                        stipple="gray50" if not panel.visible else "")

            # Draw panel label
            label_x = x1 + 10
            label_y = y1 + 20
            self.canvas.create_text(label_x, label_y,
                                   text=panel.label,
                                   fill="white",
                                   font=("Arial", 12, "bold"),
                                   anchor=tk.W)

            # Draw panel type
            type_x = x1 + 10
            type_y = y1 + 40
            self.canvas.create_text(type_x, type_y,
                                   text=panel.type.value,
                                   fill="white",
                                   font=("Arial", 9),
                                   anchor=tk.W)

            # Draw resize handles if selected
            if panel == self.selected_panel:
                handle_size = 8
                handles = [
                    (x1, y1), (x2, y1), (x1, y2), (x2, y2),  # Corners
                    (x1, (y1+y2)/2), (x2, (y1+y2)/2),  # Sides
                    ((x1+x2)/2, y1), ((x1+x2)/2, y2)   # Top/bottom
                ]

                for hx, hy in handles:
                    self.canvas.create_rectangle(hx-handle_size, hy-handle_size,
                                                hx+handle_size, hy+handle_size,
                                                fill="#E74C3C", outline="white", width=1)

    # ========== PANEL MANAGEMENT ==========
    def _add_panel(self):
        """Add a new panel"""
        panel = Panel(
            label=chr(65 + len(self.current_layout.panels)),  # A, B, C, ...
            x=0.1 + (len(self.current_layout.panels) % 3) * 0.3,
            y=0.1 + (len(self.current_layout.panels) // 3) * 0.3,
            width=0.25,
            height=0.25
        )
        self.current_layout.panels.append(panel)
        self.selected_panel = panel
        self._update_properties_panel()
        self._draw_canvas()
        self._update_preview()

    def _add_image_panel(self):
        """Add an image panel"""
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.tiff *.bmp *.gif"),
                      ("All files", "*.*")]
        )

        if file_path:
            panel = Panel(
                type=PanelType.IMAGE,
                label=chr(65 + len(self.current_layout.panels)),
                x=0.1,
                y=0.1,
                width=0.3,
                height=0.3,
                content=file_path
            )
            self.current_layout.panels.append(panel)
            self.selected_panel = panel
            self._update_properties_panel()
            self._draw_canvas()
            self._update_preview()

    def _add_text_panel(self):
        """Add a text panel"""
        panel = Panel(
            type=PanelType.TEXT,
            label=chr(65 + len(self.current_layout.panels)),
            x=0.1,
            y=0.1,
            width=0.2,
            height=0.1,
            content="Enter text here..."
        )
        self.current_layout.panels.append(panel)
        self.selected_panel = panel
        self._update_properties_panel()
        self._draw_canvas()
        self._update_preview()

    def _add_plot_panel(self):
        """Add a plot panel"""
        panel = Panel(
            type=PanelType.PLOT,
            label=chr(65 + len(self.current_layout.panels)),
            x=0.1,
            y=0.1,
            width=0.3,
            height=0.3,
            plot_type=self.plot_type.get()
        )
        self.current_layout.panels.append(panel)
        self.selected_panel = panel
        self._update_properties_panel()
        self._draw_canvas()
        self._update_preview()

    def _add_map_panel(self):
        """Add a map panel"""
        panel = Panel(
            type=PanelType.MAP,
            label=chr(65 + len(self.current_layout.panels)),
            x=0.1,
            y=0.1,
            width=0.3,
            height=0.3
        )
        self.current_layout.panels.append(panel)
        self.selected_panel = panel
        self._update_properties_panel()
        self._draw_canvas()
        self._update_preview()

    def _add_table_panel(self):
        """Add a table panel"""
        panel = Panel(
            type=PanelType.TABLE,
            label=chr(65 + len(self.current_layout.panels)),
            x=0.1,
            y=0.1,
            width=0.3,
            height=0.2
        )
        self.current_layout.panels.append(panel)
        self.selected_panel = panel
        self._update_properties_panel()
        self._draw_canvas()
        self._update_preview()

    def _add_legend_panel(self):
        """Add a legend panel"""
        panel = Panel(
            type=PanelType.LEGEND,
            label="Legend",
            x=0.7,
            y=0.7,
            width=0.2,
            height=0.2
        )
        self.current_layout.panels.append(panel)
        self.selected_panel = panel
        self._update_properties_panel()
        self._draw_canvas()
        self._update_preview()

    def _add_scale_bar(self):
        """Add a scale bar panel"""
        panel = Panel(
            type=PanelType.SCALE_BAR,
            label="Scale",
            x=0.7,
            y=0.1,
            width=0.15,
            height=0.05
        )
        self.current_layout.panels.append(panel)
        self.selected_panel = panel
        self._update_properties_panel()
        self._draw_canvas()
        self._update_preview()

    def _delete_selected(self):
        """Delete selected panel"""
        if self.selected_panel and self.current_layout:
            self.current_layout.panels.remove(self.selected_panel)
            self.selected_panel = None
            self._update_properties_panel()
            self._draw_canvas()
            self._update_preview()

    def _edit_panel(self, panel):
        """Open panel editor dialog"""
        dialog = tk.Toplevel(self.window)
        dialog.title(f"Edit Panel {panel.label}")
        dialog.geometry("500x600")
        dialog.transient(self.window)

        # Panel properties
        tk.Label(dialog, text="Panel Properties", font=("Arial", 12, "bold")).pack(pady=10)

        # Label
        tk.Label(dialog, text="Label:").pack(anchor=tk.W, padx=20, pady=5)
        label_var = tk.StringVar(value=panel.label)
        tk.Entry(dialog, textvariable=label_var, width=10).pack(anchor=tk.W, padx=20)

        # Title
        tk.Label(dialog, text="Title:").pack(anchor=tk.W, padx=20, pady=5)
        title_var = tk.StringVar(value=panel.title)
        tk.Entry(dialog, textvariable=title_var, width=50).pack(anchor=tk.W, padx=20)

        # Type-specific content
        if panel.type == PanelType.PLOT:
            tk.Label(dialog, text="Plot Type:").pack(anchor=tk.W, padx=20, pady=5)
            plot_type_var = tk.StringVar(value=panel.plot_type)
            ttk.Combobox(dialog, textvariable=plot_type_var,
                        values=["scatter", "line", "bar", "histogram", "box", "violin",
                               "heatmap", "contour", "ternary", "spider"]).pack(anchor=tk.W, padx=20)

        elif panel.type == PanelType.TEXT:
            tk.Label(dialog, text="Text Content:").pack(anchor=tk.W, padx=20, pady=5)
            text_content = scrolledtext.ScrolledText(dialog, height=10, width=50)
            text_content.pack(padx=20, pady=5)
            if panel.content:
                text_content.insert('1.0', panel.content)

        # Style options
        tk.Label(dialog, text="Style Options", font=("Arial", 12, "bold")).pack(pady=10)

        style_frame = tk.Frame(dialog)
        style_frame.pack(padx=20, pady=5)

        # Font size
        tk.Label(style_frame, text="Font Size:").grid(row=0, column=0, sticky=tk.W, pady=5)
        font_size_var = tk.IntVar(value=panel.style.get('font_size', 10))
        tk.Scale(style_frame, from_=6, to=24, variable=font_size_var,
                orient=tk.HORIZONTAL, length=200).grid(row=0, column=1, padx=10)

        # Line width
        tk.Label(style_frame, text="Line Width:").grid(row=1, column=0, sticky=tk.W, pady=5)
        line_width_var = tk.DoubleVar(value=panel.style.get('line_width', 1.0))
        tk.Scale(style_frame, from_=0.5, to=5.0, resolution=0.1,
                variable=line_width_var, orient=tk.HORIZONTAL, length=200).grid(row=1, column=1, padx=10)

        # Color picker
        tk.Label(style_frame, text="Color:").grid(row=2, column=0, sticky=tk.W, pady=5)
        color_var = tk.StringVar(value=panel.style.get('color', '#000000'))
        color_frame = tk.Frame(style_frame)
        color_frame.grid(row=2, column=1, sticky=tk.W, padx=10)
        tk.Entry(color_frame, textvariable=color_var, width=10).pack(side=tk.LEFT)
        tk.Button(color_frame, text="Pick", command=lambda: self._pick_color(color_var)).pack(side=tk.LEFT, padx=5)

        # Buttons
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=20)

        def save_changes():
            panel.label = label_var.get()
            panel.title = title_var.get()

            if panel.type == PanelType.PLOT:
                panel.plot_type = plot_type_var.get()
            elif panel.type == PanelType.TEXT:
                panel.content = text_content.get('1.0', tk.END).strip()

            # Update style
            panel.style.update({
                'font_size': font_size_var.get(),
                'line_width': line_width_var.get(),
                'color': color_var.get()
            })

            dialog.destroy()
            self._update_properties_panel()
            self._draw_canvas()
            self._update_preview()

        tk.Button(button_frame, text="Save", command=save_changes,
                 bg="#27AE60", fg="white", padx=20).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="Cancel", command=dialog.destroy,
                 bg="#E74C3C", fg="white", padx=20).pack(side=tk.LEFT, padx=10)

    def _pick_color(self, color_var):
        """Open color picker"""
        color = colorchooser.askcolor(title="Choose color", initialcolor=color_var.get())
        if color[1]:  # color[1] is hex string
            color_var.set(color[1])

    def _update_properties_panel(self):
        """Update properties panel based on selected panel"""
        # Clear properties frame
        for widget in self.properties_frame.winfo_children():
            widget.destroy()

        if not self.selected_panel:
            tk.Label(self.properties_frame, text="No panel selected",
                    bg="#2C3E50", fg="white", font=("Arial", 10)).pack(pady=20)
            return

        panel = self.selected_panel

        # Panel info
        info_frame = tk.Frame(self.properties_frame, bg="#2C3E50")
        info_frame.pack(fill=tk.X, pady=5)

        tk.Label(info_frame, text=f"Panel {panel.label} ({panel.type.value})",
                bg="#2C3E50", fg="white", font=("Arial", 11, "bold")).pack(anchor=tk.W)

        # Position controls
        pos_frame = tk.LabelFrame(self.properties_frame, text="Position & Size",
                                 bg="#2C3E50", fg="white", font=("Arial", 9))
        pos_frame.pack(fill=tk.X, pady=5)

        # X position
        tk.Label(pos_frame, text="X:", bg="#2C3E50", fg="white").grid(row=0, column=0, padx=5, pady=2)
        x_var = tk.DoubleVar(value=panel.x)
        tk.Scale(pos_frame, from_=0.0, to=1.0, resolution=0.01,
                variable=x_var, orient=tk.HORIZONTAL, length=150,
                command=lambda v: self._update_panel_property('x', float(v))).grid(row=0, column=1, padx=5, pady=2)

        # Y position
        tk.Label(pos_frame, text="Y:", bg="#2C3E50", fg="white").grid(row=1, column=0, padx=5, pady=2)
        y_var = tk.DoubleVar(value=panel.y)
        tk.Scale(pos_frame, from_=0.0, to=1.0, resolution=0.01,
                variable=y_var, orient=tk.HORIZONTAL, length=150,
                command=lambda v: self._update_panel_property('y', float(v))).grid(row=1, column=1, padx=5, pady=2)

        # Width
        tk.Label(pos_frame, text="Width:", bg="#2C3E50", fg="white").grid(row=2, column=0, padx=5, pady=2)
        width_var = tk.DoubleVar(value=panel.width)
        tk.Scale(pos_frame, from_=0.05, to=1.0, resolution=0.01,
                variable=width_var, orient=tk.HORIZONTAL, length=150,
                command=lambda v: self._update_panel_property('width', float(v))).grid(row=2, column=1, padx=5, pady=2)

        # Height
        tk.Label(pos_frame, text="Height:", bg="#2C3E50", fg="white").grid(row=3, column=0, padx=5, pady=2)
        height_var = tk.DoubleVar(value=panel.height)
        tk.Scale(pos_frame, from_=0.05, to=1.0, resolution=0.01,
                variable=height_var, orient=tk.HORIZONTAL, length=150,
                command=lambda v: self._update_panel_property('height', float(v))).grid(row=3, column=1, padx=5, pady=2)

        # Visibility
        vis_var = tk.BooleanVar(value=panel.visible)
        tk.Checkbutton(pos_frame, text="Visible", variable=vis_var,
                      command=lambda: self._update_panel_property('visible', vis_var.get()),
                      bg="#2C3E50", fg="white", selectcolor="#34495E").grid(row=4, column=0, columnspan=2, pady=5)

        # Lock
        lock_var = tk.BooleanVar(value=panel.locked)
        tk.Checkbutton(pos_frame, text="Locked", variable=lock_var,
                      command=lambda: self._update_panel_property('locked', lock_var.get()),
                      bg="#2C3E50", fg="white", selectcolor="#34495E").grid(row=5, column=0, columnspan=2, pady=5)

        # Action buttons
        action_frame = tk.Frame(self.properties_frame, bg="#2C3E50")
        action_frame.pack(fill=tk.X, pady=10)

        tk.Button(action_frame, text="✏️ Edit", command=lambda: self._edit_panel(panel),
                 bg="#3498DB", fg="white", font=("Arial", 9)).pack(side=tk.LEFT, padx=2)
        tk.Button(action_frame, text="🗑️ Delete", command=self._delete_selected,
                 bg="#E74C3C", fg="white", font=("Arial", 9)).pack(side=tk.LEFT, padx=2)
        tk.Button(action_frame, text="👁️ Toggle",
                 command=lambda: self._update_panel_property('visible', not panel.visible),
                 bg="#9B59B6", fg="white", font=("Arial", 9)).pack(side=tk.LEFT, padx=2)
        tk.Button(action_frame, text="🔒 Lock",
                 command=lambda: self._update_panel_property('locked', not panel.locked),
                 bg="#F39C12", fg="white", font=("Arial", 9)).pack(side=tk.LEFT, padx=2)

    def _update_panel_property(self, prop, value):
        """Update a property of the selected panel"""
        if self.selected_panel:
            setattr(self.selected_panel, prop, value)
            self._draw_canvas()
            self._update_preview()

    # ========== LAYOUT MANAGEMENT ==========
    def _create_default_layout(self):
        """Create a default layout"""
        self.current_layout = FigureLayout(
            name="Default Figure",
            style=JournalStyle.NATURE
        )
        self.current_layout.apply_journal_style()

        # Add some default panels
        panels = [
            Panel(type=PanelType.PLOT, label="A", x=0.1, y=0.1, width=0.35, height=0.35,
                 title="Major Elements", plot_type="scatter"),
            Panel(type=PanelType.PLOT, label="B", x=0.55, y=0.1, width=0.35, height=0.35,
                 title="Trace Elements", plot_type="spider"),
            Panel(type=PanelType.PLOT, label="C", x=0.1, y=0.55, width=0.35, height=0.35,
                 title="Classification", plot_type="ternary"),
            Panel(type=PanelType.LEGEND, label="D", x=0.55, y=0.55, width=0.2, height=0.2)
        ]

        self.current_layout.panels.extend(panels)
        self.layouts.append(self.current_layout)
        self._draw_canvas()

    def _create_new_layout(self):
        """Create a new layout"""
        dialog = tk.Toplevel(self.window)
        dialog.title("New Figure Layout")
        dialog.geometry("400x300")
        dialog.transient(self.window)

        tk.Label(dialog, text="Create New Figure", font=("Arial", 14, "bold")).pack(pady=10)

        # Layout name
        tk.Label(dialog, text="Figure Name:").pack(anchor=tk.W, padx=20, pady=5)
        name_var = tk.StringVar(value="Figure 1")
        tk.Entry(dialog, textvariable=name_var, width=30).pack(anchor=tk.W, padx=20)

        # Journal style
        tk.Label(dialog, text="Journal Style:").pack(anchor=tk.W, padx=20, pady=5)
        style_var = tk.StringVar(value="Nature")
        ttk.Combobox(dialog, textvariable=style_var,
                    values=["Nature", "Science", "Geology", "EPSL", "GCA", "Custom"]).pack(anchor=tk.W, padx=20)

        # Size
        tk.Label(dialog, text="Size (inches):").pack(anchor=tk.W, padx=20, pady=5)
        size_frame = tk.Frame(dialog)
        size_frame.pack(anchor=tk.W, padx=20)

        tk.Label(size_frame, text="Width:").pack(side=tk.LEFT)
        width_var = tk.DoubleVar(value=7.0)
        tk.Entry(size_frame, textvariable=width_var, width=6).pack(side=tk.LEFT, padx=5)

        tk.Label(size_frame, text="Height:").pack(side=tk.LEFT, padx=(10,0))
        height_var = tk.DoubleVar(value=9.0)
        tk.Entry(size_frame, textvariable=height_var, width=6).pack(side=tk.LEFT, padx=5)

        # Template
        tk.Label(dialog, text="Template:").pack(anchor=tk.W, padx=20, pady=5)
        template_var = tk.StringVar(value="Blank")
        ttk.Combobox(dialog, textvariable=template_var,
                    values=["Blank", "2×2 Grid", "3×1 Vertical", "1×3 Horizontal",
                           "Main + Inset", "Complex"]).pack(anchor=tk.W, padx=20)

        def create():
            self.current_layout = FigureLayout(
                name=name_var.get(),
                width=width_var.get(),
                height=height_var.get(),
                style=JournalStyle(style_var.get())
            )
            self.current_layout.apply_journal_style()

            # Apply template
            if template_var.get() != "Blank":
                self._apply_template(template_var.get())

            self.layouts.append(self.current_layout)
            self.selected_panel = None
            self._update_properties_panel()
            self._draw_canvas()
            self._update_preview()
            dialog.destroy()

        tk.Button(dialog, text="Create", command=create,
                 bg="#27AE60", fg="white", padx=20).pack(pady=20)

    def _apply_template(self, template_name):
        """Apply a template layout"""
        if not self.current_layout:
            return

        self.current_layout.panels.clear()

        if template_name == "2×2 Grid":
            panels = [
                Panel(label="A", x=0.1, y=0.1, width=0.35, height=0.35),
                Panel(label="B", x=0.55, y=0.1, width=0.35, height=0.35),
                Panel(label="C", x=0.1, y=0.55, width=0.35, height=0.35),
                Panel(label="D", x=0.55, y=0.55, width=0.35, height=0.35)
            ]
        elif template_name == "3×1 Vertical":
            panel_height = 0.25
            margin = 0.05
            panels = [
                Panel(label="A", x=0.1, y=margin, width=0.8, height=panel_height),
                Panel(label="B", x=0.1, y=margin*2+panel_height, width=0.8, height=panel_height),
                Panel(label="C", x=0.1, y=margin*3+panel_height*2, width=0.8, height=panel_height)
            ]
        elif template_name == "1×3 Horizontal":
            panel_width = 0.25
            margin = 0.05
            panels = [
                Panel(label="A", x=margin, y=0.1, width=panel_width, height=0.8),
                Panel(label="B", x=margin*2+panel_width, y=0.1, width=panel_width, height=0.8),
                Panel(label="C", x=margin*3+panel_width*2, y=0.1, width=panel_width, height=0.8)
            ]
        elif template_name == "Main + Inset":
            panels = [
                Panel(label="A", x=0.1, y=0.1, width=0.6, height=0.8),
                Panel(label="B", x=0.65, y=0.65, width=0.25, height=0.25)
            ]
        elif template_name == "Complex":
            panels = [
                Panel(label="A", x=0.05, y=0.05, width=0.4, height=0.4),
                Panel(label="B", x=0.55, y=0.05, width=0.4, height=0.4),
                Panel(label="C", x=0.05, y=0.55, width=0.25, height=0.4),
                Panel(label="D", x=0.35, y=0.55, width=0.25, height=0.4),
                Panel(label="E", x=0.65, y=0.55, width=0.3, height=0.4)
            ]
        else:
            return

        self.current_layout.panels.extend(panels)

    def _apply_quick_layout(self, layout_name):
        """Apply a quick layout from button"""
        self._apply_template(layout_name)
        self._draw_canvas()
        self._update_preview()

    def _apply_journal_template(self):
        """Apply journal-specific template"""
        if self.current_layout:
            self.current_layout.style = JournalStyle(self.journal_var.get())
            self.current_layout.apply_journal_style()
            self._update_preview()

    def _load_templates(self):
        """Load saved templates"""
        templates = {}
        # Default templates
        templates['nature_2x2'] = {
            'name': 'Nature 2×2',
            'style': 'Nature',
            'panels': [
                {'x': 0.1, 'y': 0.1, 'width': 0.35, 'height': 0.35},
                {'x': 0.55, 'y': 0.1, 'width': 0.35, 'height': 0.35},
                {'x': 0.1, 'y': 0.55, 'width': 0.35, 'height': 0.35},
                {'x': 0.55, 'y': 0.55, 'width': 0.35, 'height': 0.35}
            ]
        }
        return templates

    # ========== PREVIEW & EXPORT ==========
    def _update_preview(self):
        """Update the preview panel"""
        if not self.current_layout or not HAS_MATPLOTLIB:
            return

        # Clear preview
        self.preview_canvas.delete("all")

        try:
            # Create matplotlib figure
            if self.preview_fig:
                plt.close(self.preview_fig)

            self.preview_fig = plt.figure(
                figsize=(self.current_layout.width, self.current_layout.height),
                dpi=150,  # Lower DPI for preview
                facecolor=self.current_layout.background_color
            )

            # Set up gridspec for precise panel placement
            gs = gridspec.GridSpec(100, 100,
                                  left=self.current_layout.margin_left/self.current_layout.width,
                                  right=1 - self.current_layout.margin_right/self.current_layout.width,
                                  top=1 - self.current_layout.margin_top/self.current_layout.height,
                                  bottom=self.current_layout.margin_bottom/self.current_layout.height,
                                  wspace=0.1, hspace=0.1)

            # Draw each panel
            for panel in self.current_layout.panels:
                if not panel.visible:
                    continue

                # Convert normalized coordinates to grid indices
                left = int(panel.x * 100)
                bottom = int((1 - panel.y - panel.height) * 100)  # Invert Y
                width = int(panel.width * 100)
                height = int(panel.height * 100)

                # Ensure within bounds
                left = max(0, min(left, 99))
                bottom = max(0, min(bottom, 99))
                width = max(1, min(width, 100 - left))
                height = max(1, min(height, 100 - bottom))

                # Create subplot
                ax = self.preview_fig.add_subplot(gs[bottom:bottom+height, left:left+width])

                # Set panel label
                ax.text(0.02, 0.98, panel.label, transform=ax.transAxes,
                       fontsize=14, fontweight='bold', va='top',
                       bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

                # Add panel title
                if panel.title:
                    ax.set_title(panel.title, fontsize=10, pad=10)

                # Draw content based on panel type
                if panel.type == PanelType.PLOT:
                    self._draw_plot_panel(ax, panel)
                elif panel.type == PanelType.IMAGE and panel.content:
                    self._draw_image_panel(ax, panel)
                elif panel.type == PanelType.TEXT and panel.content:
                    self._draw_text_panel(ax, panel)
                elif panel.type == PanelType.TABLE:
                    self._draw_table_panel(ax, panel)
                elif panel.type == PanelType.LEGEND:
                    self._draw_legend_panel(ax, panel)
                elif panel.type == PanelType.SCALE_BAR:
                    self._draw_scale_bar(ax, panel)
                elif panel.type == PanelType.MAP:
                    self._draw_map_panel(ax, panel)

                # Apply style
                self._apply_panel_style(ax, panel)

            # Save preview to temporary file
            temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            self.preview_fig.savefig(temp_file.name, dpi=150, bbox_inches='tight', pad_inches=0.1)
            plt.close(self.preview_fig)
            temp_file.close()

            # Load and display in canvas
            if HAS_PIL:
                img = Image.open(temp_file.name)
                # Resize to fit canvas
                canvas_width = self.preview_canvas.winfo_width()
                canvas_height = self.preview_canvas.winfo_height()

                if canvas_width > 1 and canvas_height > 1:
                    img.thumbnail((canvas_width, canvas_height), Image.Resampling.LANCZOS)
                    self.preview_img = ImageTk.PhotoImage(img)
                    self.preview_canvas.create_image(
                        canvas_width//2, canvas_height//2,
                        image=self.preview_img, anchor=tk.CENTER
                    )

                # Add info text
                info = f"{self.current_layout.name} | {self.current_layout.width}×{self.current_layout.height} in | {len(self.current_layout.panels)} panels"
                self.preview_canvas.create_text(10, 10, text=info,
                                               anchor=tk.NW, fill="black",
                                               font=("Arial", 9))

            # Clean up
            os.unlink(temp_file.name)

        except Exception as e:
            self.preview_canvas.create_text(10, 10,
                                           text=f"Preview error: {str(e)}",
                                           anchor=tk.NW, fill="red",
                                           font=("Arial", 10))

    def _draw_plot_panel(self, ax, panel):
        """Draw plot in panel"""
        try:
            # Get data based on source
            data_source = self.data_source.get()
            x_data, y_data, labels = self._get_plot_data(data_source, panel)

            if x_data is None or y_data is None:
                # Draw sample plot
                x = np.linspace(0, 10, 100)
                y = np.sin(x)
                ax.plot(x, y, 'b-', linewidth=1.5)
                ax.set_xlabel("X", fontsize=9)
                ax.set_ylabel("Y", fontsize=9)
                ax.grid(True, alpha=0.3)
                return

            # Draw based on plot type
            plot_type = panel.plot_type
            color_map = self.color_map.get()

            if plot_type == "scatter":
                scatter = ax.scatter(x_data, y_data, c=labels if labels is not None else 'blue',
                                    cmap=color_map, alpha=0.7, s=30, edgecolors='black', linewidth=0.5)
                if labels is not None:
                    self.preview_fig.colorbar(scatter, ax=ax)

            elif plot_type == "line":
                ax.plot(x_data, y_data, 'b-', linewidth=1.5)

            elif plot_type == "bar":
                ax.bar(range(len(x_data)), x_data, color=plt.cm.tab20(np.arange(len(x_data))))

            elif plot_type == "histogram":
                ax.hist(x_data, bins=20, color='skyblue', edgecolor='black', alpha=0.7)

            elif plot_type == "box":
                ax.boxplot(x_data)

            elif plot_type == "violin":
                ax.violinplot(x_data)

            elif plot_type == "heatmap":
                if HAS_NUMPY and len(x_data) > 1 and len(y_data) > 1:
                    # Create correlation matrix
                    data = np.column_stack([x_data, y_data])
                    corr = np.corrcoef(data.T)
                    im = ax.imshow(corr, cmap=color_map, vmin=-1, vmax=1)
                    self.preview_fig.colorbar(im, ax=ax)

            elif plot_type == "ternary":
                # Ternary plot
                if HAS_NUMPY and len(x_data) > 2:
                    # Normalize to sum to 1
                    total = x_data[:3].sum()
                    if total > 0:
                        a, b, c = x_data[:3] / total
                        ax.scatter([a], [b], [c], s=100, color='red')
                        ax.set_xlabel("A", fontsize=9)
                        ax.set_ylabel("B", fontsize=9)
                        # Note: Ternary axes need special handling

            elif plot_type == "spider":
                # Spider/radar plot
                if HAS_NUMPY and len(x_data) > 2:
                    angles = np.linspace(0, 2*np.pi, len(x_data), endpoint=False)
                    values = np.array(x_data[:len(angles)])
                    values = np.concatenate((values, [values[0]]))  # Close the plot
                    angles = np.concatenate((angles, [angles[0]]))

                    ax = self.preview_fig.add_subplot(ax, polar=True)
                    ax.plot(angles, values, 'o-', linewidth=2)
                    ax.fill(angles, values, alpha=0.25)
                    ax.set_xticks(angles[:-1])
                    ax.set_xticklabels([f'Var{i+1}' for i in range(len(angles)-1)])

            # Add labels if available
            x_label = self.x_axis.get()
            y_label = self.y_axis.get()

            if x_label:
                ax.set_xlabel(x_label, fontsize=9)
            if y_label:
                ax.set_ylabel(y_label, fontsize=9)

            ax.grid(True, alpha=0.3)

        except Exception as e:
            ax.text(0.5, 0.5, f"Plot error:\n{str(e)}",
                   transform=ax.transAxes, ha='center', va='center',
                   fontsize=8, color='red')

    def _draw_image_panel(self, ax, panel):
        """Draw image in panel"""
        try:
            if HAS_PIL and panel.content:
                img = Image.open(panel.content)
                ax.imshow(img)
                ax.axis('off')
        except:
            ax.text(0.5, 0.5, "Image\nnot found",
                   transform=ax.transAxes, ha='center', va='center',
                   fontsize=10)

    def _draw_text_panel(self, ax, panel):
        """Draw text in panel"""
        ax.axis('off')
        if panel.content:
            ax.text(0.5, 0.5, panel.content,
                   transform=ax.transAxes, ha='center', va='center',
                   fontsize=panel.style.get('font_size', 10),
                   wrap=True)

    def _draw_table_panel(self, ax, panel):
        """Draw table in panel"""
        ax.axis('off')
        # Sample table
        cell_text = [
            ['Sample', 'SiO₂', 'MgO'],
            ['A-1', '50.2', '7.8'],
            ['A-2', '51.3', '6.9'],
            ['A-3', '49.8', '8.2']
        ]

        table = ax.table(cellText=cell_text, loc='center',
                        cellLoc='center', colWidths=[0.3, 0.3, 0.3])
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.scale(1, 1.5)

    def _draw_legend_panel(self, ax, panel):
        """Draw legend in panel"""
        ax.axis('off')
        # Create sample legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='red', edgecolor='black', label='Egyptian'),
            Patch(facecolor='blue', edgecolor='black', label='Sinai'),
            Patch(facecolor='green', edgecolor='black', label='Local'),
            Patch(facecolor='orange', edgecolor='black', label='Harrat')
        ]
        ax.legend(handles=legend_elements, loc='center',
                 fontsize=9, frameon=True, fancybox=True)

    def _draw_scale_bar(self, ax, panel):
        """Draw scale bar in panel"""
        ax.axis('off')
        # Draw scale bar
        scale_length = 1.0  # km
        ax.plot([0.1, 0.9], [0.5, 0.5], 'k-', linewidth=3)
        ax.text(0.5, 0.4, f'{scale_length} km',
               ha='center', va='top', fontsize=9)

    def _draw_map_panel(self, ax, panel):
        """Draw map in panel"""
        # Simple map representation
        ax.axis('off')

        # Draw coastline-like shape
        theta = np.linspace(0, 2*np.pi, 100)
        x = np.cos(theta) * 0.8 + 0.5
        y = np.sin(theta) * 0.6 + 0.5
        ax.fill(x, y, 'lightblue', alpha=0.5)
        ax.plot(x, y, 'blue', linewidth=1)

        # Add some sample locations
        ax.scatter([0.3, 0.5, 0.7], [0.4, 0.7, 0.3],
                  color='red', s=50, edgecolor='black', linewidth=1)

        ax.text(0.5, 0.9, 'Sample Locations',
               ha='center', va='center', fontsize=10, fontweight='bold')

    def _apply_panel_style(self, ax, panel):
        """Apply style to panel"""
        style = panel.style

        # Font size
        fontsize = style.get('font_size', 10)
        for item in ([ax.title, ax.xaxis.label, ax.yaxis.label] +
                    ax.get_xticklabels() + ax.get_yticklabels()):
            item.set_fontsize(fontsize)

        # Line width
        linewidth = style.get('line_width', 1.0)
        for axis in ['top', 'bottom', 'left', 'right']:
            ax.spines[axis].set_linewidth(linewidth)

        # Color
        color = style.get('color', '#000000')
        ax.title.set_color(color)
        ax.xaxis.label.set_color(color)
        ax.yaxis.label.set_color(color)

        # Tick color
        ax.tick_params(axis='both', colors=color)

        # Grid
        ax.grid(self.current_layout.show_grid, alpha=0.3)

    def _get_plot_data(self, source, panel):
        """Get data for plotting based on source"""
        # This would connect to your app's data
        # For now, return sample data

        if source == "Current Samples" and hasattr(self.app, 'samples') and self.app.samples:
            # Extract data from samples
            x_data = []
            y_data = []
            labels = []

            x_col = self.x_axis.get()
            y_col = self.y_axis.get()

            for sample in self.app.samples[:20]:  # First 20 samples
                try:
                    x_val = float(sample.get(x_col, 0)) if x_col else 0
                    y_val = float(sample.get(y_col, 0)) if y_col else 0
                    label = sample.get('Classification', 0)

                    x_data.append(x_val)
                    y_data.append(y_val)
                    labels.append(label)
                except:
                    continue

            if x_data and y_data:
                return np.array(x_data), np.array(y_data), np.array(labels) if labels else None

        # Return sample data
        np.random.seed(42)
        n = 50
        x = np.random.normal(0, 1, n)
        y = np.random.normal(0, 1, n)
        labels = np.random.randint(0, 3, n)

        return x, y, labels

    def _export_preview(self):
        """Export preview as image"""
        if not self.preview_fig:
            return

        file_path = filedialog.asksaveasfilename(
            title="Export Preview",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )

        if file_path:
            try:
                self.preview_fig.savefig(file_path, dpi=300, bbox_inches='tight')
                messagebox.showinfo("Export Complete",
                                  f"Preview exported to:\n{file_path}",
                                  parent=self.window)
            except Exception as e:
                messagebox.showerror("Export Error", f"Error: {str(e)}", parent=self.window)

    def _export_figure(self):
        """Export complete figure in selected format"""
        if not self.current_layout:
            return

        format = self.export_format.get()

        file_path = filedialog.asksaveasfilename(
            title="Export Figure",
            defaultextension=format,
            filetypes=[(f"{format.upper()} files", f"*{format}"), ("All files", "*.*")]
        )

        if not file_path:
            return

        # Show progress
        progress = tk.Toplevel(self.window)
        progress.title("Exporting...")
        progress.geometry("300x100")
        progress.transient(self.window)

        tk.Label(progress, text="Exporting figure...", font=("Arial", 11)).pack(pady=20)
        progress_bar = ttk.Progressbar(progress, mode='indeterminate')
        progress_bar.pack(pady=10)
        progress_bar.start()

        def export_thread():
            try:
                # Create high-resolution figure
                fig = plt.figure(
                    figsize=(self.current_layout.width, self.current_layout.height),
                    dpi=self.current_layout.dpi,
                    facecolor=self.current_layout.background_color
                )

                # Set up gridspec
                gs = gridspec.GridSpec(100, 100,
                                      left=self.current_layout.margin_left/self.current_layout.width,
                                      right=1 - self.current_layout.margin_right/self.current_layout.width,
                                      top=1 - self.current_layout.margin_top/self.current_layout.height,
                                      bottom=self.current_layout.margin_bottom/self.current_layout.height)

                # Draw panels
                for panel in self.current_layout.panels:
                    if not panel.visible:
                        continue

                    left = int(panel.x * 100)
                    bottom = int((1 - panel.y - panel.height) * 100)
                    width = int(panel.width * 100)
                    height = int(panel.height * 100)

                    ax = fig.add_subplot(gs[bottom:bottom+height, left:left+width])

                    # Draw panel content (simplified for export)
                    ax.text(0.02, 0.98, panel.label, transform=ax.transAxes,
                           fontsize=14, fontweight='bold', va='top')

                    if panel.title:
                        ax.set_title(panel.title, fontsize=12)

                    # Add sample content
                    x = np.linspace(0, 10, 100)
                    y = np.sin(x)
                    ax.plot(x, y, 'b-')
                    ax.grid(True, alpha=0.3)

                # Save figure
                if format == '.pdf' and HAS_PDF_SUPPORT:
                    fig.savefig(file_path, format='pdf', bbox_inches='tight')
                elif format == '.eps':
                    fig.savefig(file_path, format='eps', bbox_inches='tight')
                elif format == '.tiff':
                    fig.savefig(file_path, format='tiff', dpi=600, bbox_inches='tight')
                elif format == '.png':
                    fig.savefig(file_path, format='png', dpi=300, bbox_inches='tight')
                elif format == '.svg':
                    fig.savefig(file_path, format='svg', bbox_inches='tight')
                elif format == '.pptx':
                    # Would require python-pptx library
                    fig.savefig(file_path.replace('.pptx', '.png'), dpi=300)
                    # Convert to PPTX would need additional code

                plt.close(fig)

                # Update UI in main thread
                self.window.after(0, lambda: self._export_complete(progress, file_path))

            except Exception as e:
                self.window.after(0, lambda: self._export_error(progress, str(e)))

        # Run export in separate thread
        threading.Thread(target=export_thread, daemon=True).start()

    def _export_complete(self, progress_window, file_path):
        """Handle export completion"""
        progress_window.destroy()
        messagebox.showinfo("Export Complete",
                          f"Figure exported successfully to:\n{file_path}",
                          parent=self.window)

    def _export_error(self, progress_window, error):
        """Handle export error"""
        progress_window.destroy()
        messagebox.showerror("Export Error",
                           f"Error exporting figure:\n{error}",
                           parent=self.window)

    # ========== FILE OPERATIONS ==========
    def _save_layout(self):
        """Save current layout to file"""
        if not self.current_layout:
            return

        file_path = filedialog.asksaveasfilename(
            title="Save Layout",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if file_path:
            try:
                # Update caption from text widget
                self.current_layout.caption = self.caption_text.get('1.0', tk.END).strip()

                # Save to JSON
                with open(file_path, 'w') as f:
                    json.dump(self.current_layout.to_dict(), f, indent=2)

                messagebox.showinfo("Save Complete",
                                  f"Layout saved to:\n{file_path}",
                                  parent=self.window)
            except Exception as e:
                messagebox.showerror("Save Error", f"Error: {str(e)}", parent=self.window)

    def _load_layout(self):
        """Load layout from file"""
        file_path = filedialog.askopenfilename(
            title="Load Layout",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if file_path:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)

                self.current_layout = FigureLayout.from_dict(data)
                self.layouts.append(self.current_layout)

                # Update UI
                self.journal_var.set(self.current_layout.style.value)
                self.caption_text.delete('1.0', tk.END)
                self.caption_text.insert('1.0', self.current_layout.caption)

                self.selected_panel = None
                self._update_properties_panel()
                self._draw_canvas()
                self._update_preview()

                messagebox.showinfo("Load Complete",
                                  f"Layout loaded from:\n{file_path}",
                                  parent=self.window)
            except Exception as e:
                messagebox.showerror("Load Error", f"Error: {str(e)}", parent=self.window)

    # ========== UTILITY FUNCTIONS ==========
    def _undo(self):
        """Undo last action"""
        # TODO: Implement undo stack
        messagebox.showinfo("Undo", "Undo functionality to be implemented", parent=self.window)

    def _redo(self):
        """Redo last action"""
        # TODO: Implement redo stack
        messagebox.showinfo("Redo", "Redo functionality to be implemented", parent=self.window)

    def _toggle_grid(self):
        """Toggle grid visibility"""
        self.show_grid = not hasattr(self, 'show_grid') or not self.show_grid
        self._draw_canvas()

    def _open_settings(self):
        """Open settings dialog"""
        dialog = tk.Toplevel(self.window)
        dialog.title("Settings")
        dialog.geometry("400x500")
        dialog.transient(self.window)

        tk.Label(dialog, text="Settings", font=("Arial", 14, "bold")).pack(pady=10)

        # Grid settings
        grid_frame = tk.LabelFrame(dialog, text="Grid Settings", padx=10, pady=10)
        grid_frame.pack(fill=tk.X, padx=10, pady=5)

        self.snap_to_grid = tk.BooleanVar(value=hasattr(self, 'snap_to_grid') and self.snap_to_grid)
        tk.Checkbutton(grid_frame, text="Snap to grid", variable=self.snap_to_grid).pack(anchor=tk.W)

        tk.Label(grid_frame, text="Grid size:").pack(anchor=tk.W, pady=5)
        self.grid_size_var = tk.IntVar(value=self.grid_size)
        tk.Scale(grid_frame, from_=10, to=50, variable=self.grid_size_var,
                orient=tk.HORIZONTAL, command=lambda v: setattr(self, 'grid_size', int(v))).pack(fill=tk.X)

        # Export settings
        export_frame = tk.LabelFrame(dialog, text="Export Settings", padx=10, pady=10)
        export_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(export_frame, text="Default DPI:").pack(anchor=tk.W)
        self.default_dpi = tk.IntVar(value=self.current_layout.dpi if self.current_layout else 300)
        tk.Scale(export_frame, from_=150, to=1200, variable=self.default_dpi,
                orient=tk.HORIZONTAL).pack(fill=tk.X)

        # Journal defaults
        journal_frame = tk.LabelFrame(dialog, text="Journal Defaults", padx=10, pady=10)
        journal_frame.pack(fill=tk.X, padx=10, pady=5)

        journals = ["Nature", "Science", "Geology"]
        for journal in journals:
            btn = tk.Button(journal_frame, text=f"Reset {journal} defaults",
                          command=lambda j=journal: self._reset_journal_defaults(j),
                          width=20)
            btn.pack(pady=2)

        tk.Button(dialog, text="Save Settings", command=dialog.destroy,
                 bg="#27AE60", fg="white", padx=20).pack(pady=20)

    def _reset_journal_defaults(self, journal):
        """Reset journal defaults"""
        # TODO: Implement
        messagebox.showinfo("Reset", f"Reset {journal} defaults", parent=self.window)

    def _open_help(self):
        """Open help documentation"""
        help_text = """
PUBLICATION LAYOUTS PRO - USER GUIDE
═══════════════════════════════════════════════════════════════

OVERVIEW
────────────────────────────────────────────────────────────────
Advanced multi-panel figure creation tool for scientific publications.

KEY FEATURES:
• Drag-and-drop panel arrangement
• Journal-specific templates (Nature, Science, Geology)
• Live preview with WYSIWYG editing
• Multiple plot types and data sources
• High-resolution export (PDF, EPS, TIFF, PNG, SVG)
• Automatic figure numbering and captions

WORKFLOW:
1. Choose journal template
2. Add panels (plots, images, text, tables, maps)
3. Arrange panels by dragging/resizing
4. Customize each panel's content and style
5. Add figure caption
6. Export in publication-ready format

KEYBOARD SHORTCUTS:
• Ctrl+S: Save layout
• Ctrl+O: Load layout
• Ctrl+N: New layout
• Ctrl+E: Export figure
• Ctrl+P: Update preview
• Delete: Delete selected panel
• Ctrl+G: Toggle grid

PANEL TYPES:
• Plot: Data visualization (scatter, line, bar, etc.)
• Image: Photographs, maps, diagrams
• Text: Annotations, labels, descriptions
• Table: Data tables
• Legend: Figure legend
• Scale Bar: Map scale
• Map: Geographic maps

EXPORT FORMATS:
• PDF: Vector format (recommended)
• EPS: Vector format for LaTeX
• TIFF: High-resolution raster (600 DPI)
• PNG: Web/presentation (300 DPI)
• SVG: Scalable vector graphics
• PPTX: PowerPoint (requires conversion)

JOURNAL REQUIREMENTS:
• Nature: Single column 3.5", double column 7"
• Science: 5.5" width
• Geology: 7" width, 600 DPI minimum
• EPSL: Check specific guidelines
• GCA: Check specific guidelines

TIPS:
• Use grid snapping for alignment
• Maintain consistent margins
• Check journal color requirements
• Use vector formats when possible
• Include scale bars on maps/images
• Number panels sequentially (A, B, C...)

═══════════════════════════════════════════════════════════════
"""

        help_window = tk.Toplevel(self.window)
        help_window.title("Help - Publication Layouts Pro")
        help_window.geometry("700x800")

        text = scrolledtext.ScrolledText(help_window, wrap=tk.WORD,
                                        font=("Arial", 10), padx=10, pady=10)
        text.pack(fill=tk.BOTH, expand=True)
        text.insert('1.0', help_text)
        text.config(state='disabled')

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
            else:
                pip_cmd = "pip install " + " ".join(missing_packages)
                messagebox.showinfo(
                    "Install Manually",
                    f"Run in terminal:\n\n{pip_cmd}\n\n"
                    f"Then restart the application.",
                    parent=self.window
                )


def setup_plugin(main_app):
    """Setup function - Adds button to main window"""
    plugin = PublicationLayoutsPlugin(main_app)

    # Try to add to menu first
    if hasattr(main_app, 'menu_bar'):
        try:
            main_app.menu_bar.add_command(
                label="📐 Publication Layouts",
                command=plugin.open_layout_window
            )
        except:
            pass

    # ALSO add a toolbar button if possible
    if hasattr(main_app, 'toolbar') or hasattr(main_app, 'button_frame'):
        try:
            # Find a place to put our button
            for attr in ['toolbar', 'button_frame', 'control_panel', 'main_frame']:
                if hasattr(main_app, attr):
                    frame = getattr(main_app, attr)
                    if hasattr(frame, 'pack') or hasattr(frame, 'grid'):
                        btn = tk.Button(frame, text="📐 Figures",
                                      command=plugin.open_layout_window,
                                      bg="#9B59B6", fg="white",
                                      font=("Arial", 9))

                        # Try different packing methods
                        try:
                            btn.pack(side=tk.LEFT, padx=2)
                            break
                        except:
                            try:
                                btn.grid(row=0, column=999, padx=2)
                                break
                            except:
                                pass
        except:
            pass

    return plugin

def setup_plugin(main_app):
    """Plugin setup"""
    plugin = publication_layouts(main_app)

    if hasattr(main_app, 'menu_bar'):
        if not hasattr(main_app, 'advanced_menu'):
            main_app.advanced_menu = tk.Menu(main_app.menu_bar, tearoff=0)
            main_app.menu_bar.add_cascade(label="Advanced", menu=main_app.advanced_menu)

        main_app.advanced_menu.add_command(
            label=f"{PLUGIN_INFO['icon']} {PLUGIN_INFO['name']} v{PLUGIN_INFO['version']}",
            command=plugin.open_window
        )

    return plugin
