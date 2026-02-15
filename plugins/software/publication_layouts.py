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

    def open_window(self):  # ← RENAMED from open_layout_window to match standard pattern
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

    # ... [ALL THE REST OF YOUR EXISTING METHODS REMAIN EXACTLY THE SAME] ...
    # (I'm truncating here for space, but keep all methods from _create_interface through _install_dependencies)

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

# ========== SINGLE SETUP FUNCTION (FIXED) ==========
def setup_plugin(main_app):
    """SINGLE setup function - FOLLOWS WORKING PATTERN"""
    plugin = PublicationLayoutsPlugin(main_app)
    return plugin  # ← JUST RETURN PLUGIN, NO MENU CREATION
