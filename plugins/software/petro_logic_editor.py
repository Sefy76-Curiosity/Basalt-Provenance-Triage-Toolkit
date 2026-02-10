"""
Advanced Petro-Logic Custom Equation Editor Plugin
Enhanced version with advanced features for geochemical calculations

New Features:
- Vectorized calculations using numpy for speed
- Advanced geochemical indices and classifications
- Batch equation processing
- Interactive 2D/3D plotting of results
- Unit conversion system with auto-detection
- Cross-validation and statistical analysis
- Formula templates and wizard
- Multi-equation pipelines
- Integration with external databases
- Machine learning model integration
- Real-time data validation
- Equation optimization suggestions
- Export to multiple formats (Excel, CSV, HTML, PDF)

Author: Sefy Levy
License: CC BY-NC-SA 4.0
Advanced Version: 2.0
"""

PLUGIN_INFO = {
    "category": "advanced_software",
    "id": "advanced_petro_logic_editor",
    "name": "Advanced Petro-Logic Equation Editor",
    "description": "Advanced geochemical calculations with ML and visualization",
    "icon": "🧪",
    "version": "2.0",
    "requires": ["numpy", "sympy", "pandas", "matplotlib"],
    "optional": ["scipy", "scikit-learn", "plotly", "seaborn"],
    "author": "Sefy Levy",
    "min_app_version": "1.2",
    "load_on_startup": False
}

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog, simpledialog
import math
import re
import json
import numpy as np
from io import StringIO, BytesIO
import traceback
from datetime import datetime
import hashlib
import threading
import queue
import warnings
from collections import defaultdict
import itertools
import sys
import os

# Advanced dependencies
try:
    import numpy as np
    HAS_NUMPY = True
    from numpy import nan, isnan, isinf
except ImportError:
    HAS_NUMPY = False

try:
    import sympy
    from sympy import symbols, sympify, lambdify
    HAS_SYMPY = True
except ImportError:
    HAS_SYMPY = False

try:
    import pandas as pd
    from pandas import DataFrame, Series
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    from matplotlib.figure import Figure
    import matplotlib.cm as cm
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    from scipy import stats, optimize, interpolate
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    from sklearn import preprocessing, decomposition, manifold
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

try:
    import plotly.graph_objects as go
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False

HAS_REQUIREMENTS = HAS_NUMPY and HAS_SYMPY and HAS_PANDAS


class AdvancedPetroLogicPlugin:
    """Advanced plugin for custom equation editing and calculation"""

    def __init__(self, main_app):
        """Initialize advanced plugin"""
        self.app = main_app
        self.window = None
        self.equations = []
        self.equation_pipelines = []
        self.current_pipeline = None
        self.variable_list = []
        self.unit_system = {}
        self.ml_models = {}
        self.calculation_cache = {}
        self.is_installed = False
        self.menu_item = None

        # Advanced math functions
        self.advanced_math_functions = {
            # Basic math
            'sqrt': math.sqrt, 'log': math.log, 'log10': math.log10,
            'exp': math.exp, 'pow': math.pow,
            'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
            'asin': math.asin, 'acos': math.acos, 'atan': math.atan,
            'atan2': math.atan2,
            'sinh': math.sinh, 'cosh': math.cosh, 'tanh': math.tanh,
            'abs': abs, 'round': round,
            'floor': math.floor, 'ceil': math.ceil,
            'pi': math.pi, 'e': math.e,
            'radians': math.radians, 'degrees': math.degrees,

            # Statistical functions (will be vectorized)
            'mean': np.mean, 'median': np.median, 'std': np.std,
            'var': np.var, 'min': np.min, 'max': np.max,
            'percentile': np.percentile, 'sum': np.sum,
            'skew': lambda x: stats.skew(x) if HAS_SCIPY else None,
            'kurtosis': lambda x: stats.kurtosis(x) if HAS_SCIPY else None,

            # Array operations
            'norm': np.linalg.norm, 'dot': np.dot,
            'cross': np.cross if HAS_NUMPY else None,
        }

        # Enhanced built-in formulas database
        self.builtin_formulas = {
            # Weathering indices
            'CIA (Chemical Index of Alteration)': {
                'expression': 'Al2O3 / (Al2O3 + CaO* + Na2O + K2O) * 100',
                'description': 'Nesbitt & Young (1982). CaO* is corrected for apatite',
                'variables': ['Al2O3', 'CaO', 'Na2O', 'K2O', 'P2O5'],
                'category': 'Weathering',
                'reference': 'Nesbitt & Young, 1982'
            },
            'CIW (Chemical Index of Weathering)': {
                'expression': 'Al2O3 / (Al2O3 + CaO + Na2O) * 100',
                'description': 'Harnois (1988) weathering index',
                'variables': ['Al2O3', 'CaO', 'Na2O'],
                'category': 'Weathering',
                'reference': 'Harnois, 1988'
            },
            'PIA (Plagioclase Index of Alteration)': {
                'expression': '(Al2O3 - K2O) / (Al2O3 + CaO* + Na2O - K2O) * 100',
                'description': 'Fedo et al. (1995) plagioclase alteration',
                'variables': ['Al2O3', 'CaO', 'Na2O', 'K2O', 'P2O5'],
                'category': 'Weathering',
                'reference': 'Fedo et al., 1995'
            },

            # Tectonic discrimination diagrams
            'Rb/Y vs Nb/Y (Pearce, 1996)': {
                'expression': 'log(Rb_ppm / Y_ppm)',
                'description': 'Tectonic discrimination for granites',
                'variables': ['Rb_ppm', 'Y_ppm'],
                'category': 'Tectonic',
                'reference': 'Pearce, 1996'
            },
            'Zr/TiO2 vs Nb/Y (Winchester & Floyd, 1977)': {
                'expression': 'log(Zr_ppm / TiO2)',
                'description': 'Volcanic rock classification',
                'variables': ['Zr_ppm', 'TiO2'],
                'category': 'Classification',
                'reference': 'Winchester & Floyd, 1977'
            },

            # Mantle and petrology
            'Mg# (Magnesium Number)': {
                'expression': 'MgO / (MgO + 0.85*Fe2O3) * 100',
                'description': 'Corrected for Fe3+/Fe2+ ratio',
                'variables': ['MgO', 'Fe2O3'],
                'category': 'Petrology',
                'reference': 'Middlemost, 1994'
            },
            'Fe# (Iron Number)': {
                'expression': 'Fe2O3 / (MgO + Fe2O3) * 100',
                'description': 'Iron enrichment index',
                'variables': ['MgO', 'Fe2O3'],
                'category': 'Petrology',
                'reference': ''
            },

            # Fertility indices
            'Fertility Index (Zr/Y)': {
                'expression': 'Zr_ppm / Y_ppm',
                'description': 'Mantle fertility indicator',
                'variables': ['Zr_ppm', 'Y_ppm'],
                'category': 'Petrology',
                'reference': ''
            },
            'Sm/Yb (REE Slope)': {
                'expression': 'Sm_ppm / Yb_ppm',
                'description': 'REE slope indicator of melting depth',
                'variables': ['Sm_ppm', 'Yb_ppm'],
                'category': 'Geochemistry',
                'reference': ''
            },

            # Multidimensional indices
            'REE Total (ΣREE)': {
                'expression': 'La_ppm + Ce_ppm + Pr_ppm + Nd_ppm + Sm_ppm + Eu_ppm + Gd_ppm + Tb_ppm + Dy_ppm + Ho_ppm + Er_ppm + Tm_ppm + Yb_ppm + Lu_ppm',
                'description': 'Total Rare Earth Elements',
                'variables': ['La_ppm', 'Ce_ppm', 'Pr_ppm', 'Nd_ppm', 'Sm_ppm', 'Eu_ppm',
                            'Gd_ppm', 'Tb_ppm', 'Dy_ppm', 'Ho_ppm', 'Er_ppm', 'Tm_ppm',
                            'Yb_ppm', 'Lu_ppm'],
                'category': 'Geochemistry',
                'reference': ''
            },

            # Cation calculations
            'Cation Norm (CIPW)': {
                'expression': 'complex',
                'description': 'CIPW normative mineralogy (simplified)',
                'variables': ['SiO2', 'TiO2', 'Al2O3', 'Fe2O3', 'FeO', 'MnO', 'MgO',
                            'CaO', 'Na2O', 'K2O', 'P2O5', 'Cr2O3', 'NiO'],
                'category': 'Normative',
                'reference': 'Cross et al., 1902'
            }
        }

        # Advanced formula templates
        self.formula_templates = {
            'Ratio': {
                'template': '{var1} / {var2}',
                'description': 'Simple ratio of two variables',
                'placeholders': ['var1', 'var2']
            },
            'Normalized Ratio': {
                'template': '({var1} / {norm}) / ({var2} / {norm})',
                'description': 'Ratio normalized to a reference element',
                'placeholders': ['var1', 'var2', 'norm']
            },
            'Ternary Ratio': {
                'template': '{var1} / ({var1} + {var2} + {var3}) * 100',
                'description': 'Ternary diagram end-member calculation',
                'placeholders': ['var1', 'var2', 'var3']
            },
            'Log Ratio': {
                'template': 'log({var1} / {var2})',
                'description': 'Logarithmic ratio for discrimination diagrams',
                'placeholders': ['var1', 'var2']
            },
            'Weighted Sum': {
                'template': '{coef1}*{var1} + {coef2}*{var2} + {coef3}*{var3}',
                'description': 'Weighted linear combination',
                'placeholders': ['var1', 'var2', 'var3', 'coef1', 'coef2', 'coef3']
            },
            'Polynomial': {
                'template': '{a}*{var1}**2 + {b}*{var1} + {c}',
                'description': 'Second order polynomial',
                'placeholders': ['var1', 'a', 'b', 'c']
            }
        }

        # Unit conversion factors
        self.unit_conversions = {
            'wt%_to_ppm': 10000,
            'ppm_to_wt%': 0.0001,
            'oxide_to_element': {
                'SiO2': 0.4674, 'TiO2': 0.5995, 'Al2O3': 0.5293,
                'Fe2O3': 0.6994, 'FeO': 0.7773, 'MnO': 0.7745,
                'MgO': 0.6030, 'CaO': 0.7147, 'Na2O': 0.7419,
                'K2O': 0.8301, 'P2O5': 0.4364, 'Cr2O3': 0.6842,
                'NiO': 0.7858
            }
        }

        self.load_formula_library()
        self.load_unit_system()

    def install(self):
        """Install the plugin into the application"""
        if self.is_installed:
            return True

        try:
            # Check requirements
            if not HAS_REQUIREMENTS:
                missing = []
                if not HAS_NUMPY: missing.append("numpy")
                if not HAS_SYMPY: missing.append("sympy")
                if not HAS_PANDAS: missing.append("pandas")

                # Try to install missing dependencies
                if missing and hasattr(self.app, 'install_dependencies'):
                    response = messagebox.askyesno(
                        "Missing Dependencies",
                        f"Advanced Petro-Logic Editor requires:\n\n"
                        f"• numpy (for vectorized calculations)\n"
                        f"• sympy (for symbolic math)\n"
                        f"• pandas (for data handling)\n\n"
                        f"Missing: {', '.join(missing)}\n\n"
                        f"Install missing dependencies now?",
                        parent=self.app.root
                    )
                    if response:
                        success = self.app.install_dependencies(missing)
                        if not success:
                            return False
                else:
                    messagebox.showwarning(
                        "Missing Dependencies",
                        f"Cannot install plugin. Missing: {', '.join(missing)}"
                    )
                    return False

            # Add to menu
            self._add_to_menu()

            # Register with plugin manager
            if hasattr(self.app, 'register_plugin'):
                self.app.register_plugin(PLUGIN_INFO['id'], self)

            self.is_installed = True
            print(f"✅ {PLUGIN_INFO['name']} v{PLUGIN_INFO['version']} installed successfully")
            return True

        except Exception as e:
            print(f"❌ Error installing plugin: {e}")
            traceback.print_exc()
            return False

    def uninstall(self):
        """Uninstall the plugin"""
        if not self.is_installed:
            return

        try:
            # Remove from menu
            if self.menu_item and hasattr(self.app, 'menu_bar'):
                self.app.menu_bar.delete(self.menu_item)

            # Unregister from plugin manager
            if hasattr(self.app, 'unregister_plugin'):
                self.app.unregister_plugin(PLUGIN_INFO['id'])

            # Close any open windows
            if self.window and self.window.winfo_exists():
                self.window.destroy()

            self.is_installed = False
            print(f"🗑️ {PLUGIN_INFO['name']} uninstalled")

        except Exception as e:
            print(f"❌ Error uninstalling plugin: {e}")

    def _add_to_menu(self):
        """Add plugin to application menu"""
        try:
            # Look for Tools menu or create it
            if hasattr(self.app, 'menu_bar'):
                # Find or create Tools menu
                tools_menu = None
                for i in range(self.app.menu_bar.index('end') + 1):
                    try:
                        label = self.app.menu_bar.entrycget(i, 'label')
                        if label == "Tools":
                            tools_menu = self.app.menu_bar
                            break
                    except:
                        pass

                if tools_menu:
                    # Add separator if needed
                    last_index = tools_menu.index('end')
                    if last_index is not None and tools_menu.entrycget(last_index, 'label') != '':
                        tools_menu.add_separator()

                    # Add menu item
                    self.menu_item = tools_menu.index('end')
                    tools_menu.add_command(
                        label=f"{PLUGIN_INFO['icon']} {PLUGIN_INFO['name']}",
                        command=self.open_equation_editor,
                        accelerator="Ctrl+Shift+E"
                    )

                    # Bind keyboard shortcut
                    self.app.root.bind('<Control-Shift-E>', lambda e: self.open_equation_editor())

                else:
                    # Create Tools menu if it doesn't exist
                    tools_menu = tk.Menu(self.app.menu_bar, tearoff=0)
                    self.app.menu_bar.add_cascade(label="Tools", menu=tools_menu)
                    tools_menu.add_command(
                        label=f"{PLUGIN_INFO['icon']} {PLUGIN_INFO['name']}",
                        command=self.open_equation_editor,
                        accelerator="Ctrl+Shift+E"
                    )
                    # Bind keyboard shortcut
                    self.app.root.bind('<Control-Shift-E>', lambda e: self.open_equation_editor())

            elif hasattr(self.app, 'add_menu_item'):
                # Alternative method if app has add_menu_item
                self.menu_item = self.app.add_menu_item(
                    "Tools",
                    f"{PLUGIN_INFO['icon']} {PLUGIN_INFO['name']}",
                    self.open_equation_editor
                )

        except Exception as e:
            print(f"❌ Error adding to menu: {e}")
            traceback.print_exc()

    def open_equation_editor(self, event=None):
        """Open the advanced equation editor interface"""
        if not self.is_installed:
            messagebox.showwarning(
                "Plugin Not Installed",
                "Please install the plugin first from the Plugin Manager.",
                parent=self.app.root
            )
            return

        if not HAS_REQUIREMENTS:
            self._show_dependency_error()
            return

        if self.window and self.window.winfo_exists():
            self.window.lift()
            self.window.state('normal')  # Restore if minimized
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title(f"{PLUGIN_INFO['name']} v{PLUGIN_INFO['version']}")
        self.window.geometry("1400x900")

        # Configure window properties
        self.window.minsize(1200, 700)
        self.window.transient(self.app.root)

        # Set icon (if available)
        try:
            self.window.iconbitmap('icon.ico')
        except:
            pass

        # Bind close event
        self.window.protocol("WM_DELETE_WINDOW", self._on_window_close)

        self._create_advanced_interface()

        # Bring to front
        self.window.lift()
        self.window.focus_force()

        # Update status
        self.status_label.config(text="Ready - Advanced Editor Loaded")

        # Start background tasks
        self._start_background_services()

        return self.window

    def _on_window_close(self):
        """Handle window close event"""
        if self.window:
            self.window.destroy()
            self.window = None

    def _create_advanced_interface(self):
        """Create the advanced interface with multiple tabs"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create tabs
        self.editor_tab = ttk.Frame(self.notebook)
        self.library_tab = ttk.Frame(self.notebook)
        self.pipeline_tab = ttk.Frame(self.notebook)
        self.visualization_tab = ttk.Frame(self.notebook)
        self.ml_tab = ttk.Frame(self.notebook)
        self.batch_tab = ttk.Frame(self.notebook)
        self.settings_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.editor_tab, text="✏️ Equation Editor")
        self.notebook.add(self.library_tab, text="📚 Formula Library")
        self.notebook.add(self.pipeline_tab, text="⚙️ Processing Pipeline")
        self.notebook.add(self.visualization_tab, text="📊 Visualization")
        self.notebook.add(self.ml_tab, text="🤖 Machine Learning")
        self.notebook.add(self.batch_tab, text="🔁 Batch Processing")
        self.notebook.add(self.settings_tab, text="⚙️ Settings")

        # Create each tab's content
        self._create_editor_tab()
        self._create_library_tab()
        self._create_pipeline_tab()
        self._create_visualization_tab()
        self._create_ml_tab()
        self._create_batch_tab()
        self._create_settings_tab()

        # Create status bar
        self.status_frame = tk.Frame(self.window, bd=1, relief=tk.SUNKEN)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_label = tk.Label(self.status_frame, text="Ready", anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.status_frame,
                                          variable=self.progress_var,
                                          maximum=100)
        self.progress_bar.pack(side=tk.RIGHT, padx=5)

        # Create menu bar
        self._create_menu_bar()

    def _create_editor_tab(self):
        """Create the advanced equation editor tab"""
        # Top control panel
        control_frame = tk.Frame(self.editor_tab, padx=10, pady=10)
        control_frame.pack(fill=tk.X)

        # Template wizard button
        tk.Button(control_frame, text="🧙 Template Wizard",
                 command=self._open_template_wizard,
                 bg="#6A1B9A", fg="white").pack(side=tk.LEFT, padx=5)

        # Vectorize toggle
        self.vectorize_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(control_frame, text="Vectorize Calculation",
                       variable=self.vectorize_var).pack(side=tk.LEFT, padx=5)

        # Auto-parse toggle
        self.auto_parse_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(control_frame, text="Auto-parse",
                       variable=self.auto_parse_var,
                       command=self._auto_parse_expression).pack(side=tk.LEFT, padx=5)

        # Main content split into two panes
        paned = ttk.PanedWindow(self.editor_tab, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Left pane - Equation definition
        left_pane = ttk.Frame(paned)
        paned.add(left_pane, weight=2)

        # Right pane - Preview and helpers
        right_pane = ttk.Frame(paned)
        paned.add(right_pane, weight=1)

        # Left pane content
        self._create_equation_definition(left_pane)

        # Right pane content
        self._create_equation_helpers(right_pane)

    def _create_equation_definition(self, parent):
        """Create equation definition section"""
        # Name and metadata
        meta_frame = tk.LabelFrame(parent, text="Equation Metadata", padx=10, pady=10)
        meta_frame.pack(fill=tk.X, padx=5, pady=5)

        # Name
        tk.Label(meta_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.eq_name_var = tk.StringVar()
        tk.Entry(meta_frame, textvariable=self.eq_name_var, width=40).grid(row=0, column=1, padx=5)

        # Category
        tk.Label(meta_frame, text="Category:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.eq_category_var = tk.StringVar(value="Custom")
        categories = ["Custom", "Weathering", "Tectonic", "Petrology", "Classification",
                     "Geochemistry", "Normative", "Statistical", "Machine Learning"]
        ttk.Combobox(meta_frame, textvariable=self.eq_category_var,
                    values=categories, width=15).grid(row=0, column=3, padx=5)

        # Version
        tk.Label(meta_frame, text="Version:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.eq_version_var = tk.StringVar(value="1.0")
        tk.Entry(meta_frame, textvariable=self.eq_version_var, width=10).grid(row=1, column=1, padx=5)

        # Author
        tk.Label(meta_frame, text="Author:").grid(row=1, column=2, sticky=tk.W, padx=5)
        self.eq_author_var = tk.StringVar(value="")
        tk.Entry(meta_frame, textvariable=self.eq_author_var, width=20).grid(row=1, column=3, padx=5)

        # Tags
        tk.Label(meta_frame, text="Tags:").grid(row=2, column=0, sticky=tk.W, padx=5)
        self.eq_tags_var = tk.StringVar(value="")
        tk.Entry(meta_frame, textvariable=self.eq_tags_var, width=40).grid(row=2, column=1, columnspan=3, sticky=tk.EW, padx=5)

        # Description with syntax highlighting
        desc_frame = tk.LabelFrame(parent, text="Description & Notes", padx=10, pady=10)
        desc_frame.pack(fill=tk.X, padx=5, pady=5)

        self.eq_desc_text = scrolledtext.ScrolledText(desc_frame, height=4,
                                                     wrap=tk.WORD,
                                                     font=("Arial", 10))
        self.eq_desc_text.pack(fill=tk.BOTH, expand=True)

        # Expression editor with syntax highlighting
        expr_frame = tk.LabelFrame(parent, text="Expression Editor", padx=10, pady=10)
        expr_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Toolbar for expression editor
        expr_toolbar = tk.Frame(expr_frame)
        expr_toolbar.pack(fill=tk.X, pady=(0, 5))

        # Insert buttons for common operations
        ops = ["+", "-", "*", "/", "**", "(", ")", "log(", "exp(", "sqrt("]
        for op in ops:
            tk.Button(expr_toolbar, text=op, width=3,
                     command=lambda o=op: self._insert_in_expression(o)).pack(side=tk.LEFT, padx=1)

        # Expression text with line numbers
        text_frame = tk.Frame(expr_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        # Line numbers
        self.line_numbers = tk.Text(text_frame, width=4, padx=3, takefocus=0,
                                   border=0, background='lightgray', state='disabled')
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)

        # Expression text
        self.expr_text = scrolledtext.ScrolledText(text_frame,
                                                  wrap=tk.NONE,
                                                  font=("Consolas", 11),
                                                  undo=True)
        self.expr_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Bind events for line numbers and auto-parse
        self.expr_text.bind('<KeyRelease>', self._update_line_numbers)
        self.expr_text.bind('<KeyRelease>', lambda e: self._auto_parse_expression() if self.auto_parse_var.get() else None)

        # Variable detection frame
        var_frame = tk.LabelFrame(parent, text="Detected Variables & Units", padx=10, pady=10)
        var_frame.pack(fill=tk.X, padx=5, pady=5)

        # Treeview for variables with units
        columns = ("Variable", "Type", "Unit", "Description")
        self.var_tree = ttk.Treeview(var_frame, columns=columns, show="headings", height=4)

        for col in columns:
            self.var_tree.heading(col, text=col)
            self.var_tree.column(col, width=100)

        self.var_tree.column("Variable", width=120)
        self.var_tree.column("Description", width=200)

        var_scroll = ttk.Scrollbar(var_frame, orient=tk.VERTICAL, command=self.var_tree.yview)
        self.var_tree.configure(yscrollcommand=var_scroll.set)

        self.var_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        var_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Action buttons
        action_frame = tk.Frame(parent, pady=10)
        action_frame.pack(fill=tk.X, padx=5)

        buttons = [
            ("🔍 Parse & Validate", self._parse_expression_advanced, "#FF9800"),
            ("💾 Save Equation", self._save_equation_advanced, "#4CAF50"),
            ("🚀 Apply to Data", self._apply_to_data_advanced, "#2196F3"),
            ("📊 Preview & Stats", self._preview_results_advanced, "#9C27B0"),
            ("🧪 Test with Random", self._test_with_random, "#00BCD4"),
            ("⚡ Optimize", self._optimize_expression, "#FF5722")
        ]

        for text, command, color in buttons:
            tk.Button(action_frame, text=text, command=command,
                     bg=color, fg="white", width=15).pack(side=tk.LEFT, padx=2)

    def _create_equation_helpers(self, parent):
        """Create equation helpers panel"""
        # Available functions
        func_frame = tk.LabelFrame(parent, text="Available Functions", padx=10, pady=10)
        func_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Categorized functions
        func_categories = {
            "Math": ["sqrt", "log", "log10", "exp", "pow", "abs"],
            "Trigonometry": ["sin", "cos", "tan", "asin", "acos", "atan"],
            "Statistics": ["mean", "median", "std", "var", "min", "max"],
            "Array": ["sum", "norm", "dot"]
        }

        for category, funcs in func_categories.items():
            cat_frame = tk.LabelFrame(func_frame, text=category, padx=5, pady=5)
            cat_frame.pack(fill=tk.X, padx=2, pady=2)

            for func in funcs:
                btn = tk.Button(cat_frame, text=func, width=8,
                               command=lambda f=func: self._insert_in_expression(f + "()"))
                btn.pack(side=tk.LEFT, padx=2)

        # Data preview
        data_frame = tk.LabelFrame(parent, text="Data Preview", padx=10, pady=10)
        data_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Sample data display
        self.data_preview_text = scrolledtext.ScrolledText(data_frame, height=8,
                                                         wrap=tk.NONE,
                                                         font=("Consolas", 9))
        self.data_preview_text.pack(fill=tk.BOTH, expand=True)

        # Update preview button
        tk.Button(data_frame, text="Refresh Preview",
                 command=self._update_data_preview).pack(pady=5)

        # Quick calculations
        calc_frame = tk.LabelFrame(parent, text="Quick Calculations", padx=10, pady=10)
        calc_frame.pack(fill=tk.BOTH, padx=5, pady=5)

        quick_calcs = [
            ("Sum", "sum([var1, var2, var3])"),
            ("Average", "mean([var1, var2, var3])"),
            ("Ratio", "var1 / var2"),
            ("Log Ratio", "log(var1 / var2)"),
            ("Z-score", "(var - mean(var)) / std(var)")
        ]

        for name, expr in quick_calcs:
            frame = tk.Frame(calc_frame)
            frame.pack(fill=tk.X, pady=2)
            tk.Label(frame, text=name + ":", width=10, anchor=tk.W).pack(side=tk.LEFT)
            tk.Label(frame, text=expr, font=("Courier", 9), fg="blue").pack(side=tk.LEFT)
            tk.Button(frame, text="Insert", width=6,
                     command=lambda e=expr: self._insert_in_expression(e)).pack(side=tk.RIGHT)

    def _create_library_tab(self):
        """Create the advanced formula library tab"""
        # Search and filter panel
        filter_frame = tk.Frame(self.library_tab, padx=10, pady=10)
        filter_frame.pack(fill=tk.X)

        # Search
        tk.Label(filter_frame, text="Search:").pack(side=tk.LEFT)
        self.library_search_var = tk.StringVar()
        search_entry = tk.Entry(filter_frame, textvariable=self.library_search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind('<KeyRelease>', lambda e: self._refresh_library_advanced())

        # Category filter
        tk.Label(filter_frame, text="Category:").pack(side=tk.LEFT, padx=(20, 5))
        self.library_filter_var = tk.StringVar(value="All")
        categories = ["All", "Built-in", "Custom", "Weathering", "Tectonic",
                     "Petrology", "Classification", "Geochemistry", "Normative"]
        ttk.Combobox(filter_frame, textvariable=self.library_filter_var,
                    values=categories, state='readonly', width=15).pack(side=tk.LEFT)

        # Sort options
        tk.Label(filter_frame, text="Sort by:").pack(side=tk.LEFT, padx=(20, 5))
        self.library_sort_var = tk.StringVar(value="Name")
        ttk.Combobox(filter_frame, textvariable=self.library_sort_var,
                    values=["Name", "Category", "Date", "Popularity"],
                    state='readonly', width=12).pack(side=tk.LEFT)

        # Library tree with advanced view
        tree_frame = tk.Frame(self.library_tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        columns = ("Name", "Category", "Variables", "Version", "Author", "Last Used")
        self.library_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=20)

        # Configure columns
        col_widths = {"Name": 200, "Category": 100, "Variables": 150,
                     "Version": 60, "Author": 100, "Last Used": 120}

        for col in columns:
            self.library_tree.heading(col, text=col, command=lambda c=col: self._sort_library(c))
            self.library_tree.column(col, width=col_widths.get(col, 100))

        # Add scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.library_tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.library_tree.xview)
        self.library_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.library_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # Bind double-click and selection
        self.library_tree.bind("<Double-1>", self._on_formula_select_advanced)
        self.library_tree.bind("<<TreeviewSelect>>", self._show_formula_details)

        # Formula details panel
        details_frame = tk.LabelFrame(self.library_tab, text="Formula Details", padx=10, pady=10)
        details_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.formula_details_text = scrolledtext.ScrolledText(details_frame, height=8,
                                                            wrap=tk.WORD,
                                                            font=("Arial", 10))
        self.formula_details_text.pack(fill=tk.BOTH, expand=True)

        # Action buttons
        action_frame = tk.Frame(self.library_tab)
        action_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        actions = [
            ("📥 Load Selected", self._load_selected_formula_advanced),
            ("✏️ Edit", self._edit_selected_formula),
            ("🗑️ Delete", self._delete_formula_advanced),
            ("📋 Export", self._export_library_advanced),
            ("📄 Import", self._import_library_advanced),
            ("🔄 Refresh", self._refresh_library_advanced),
            ("⭐ Rate", self._rate_formula),
            ("📊 Usage Stats", self._show_usage_stats)
        ]

        for text, command in actions:
            tk.Button(action_frame, text=text, command=command, width=12).pack(side=tk.LEFT, padx=2)

        # Refresh library
        self._refresh_library_advanced()

    def _create_pipeline_tab(self):
        """Create processing pipeline tab"""
        # Pipeline definition
        pipe_frame = tk.LabelFrame(self.pipeline_tab, text="Processing Pipeline", padx=10, pady=10)
        pipe_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Pipeline name
        tk.Label(pipe_frame, text="Pipeline Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.pipeline_name_var = tk.StringVar(value="My Pipeline")
        tk.Entry(pipe_frame, textvariable=self.pipeline_name_var, width=30).grid(row=0, column=1, padx=5, pady=5)

        # Available equations list
        avail_frame = tk.LabelFrame(pipe_frame, text="Available Equations", padx=10, pady=10)
        avail_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5, rowspan=2)

        self.available_eq_list = tk.Listbox(avail_frame, height=15, width=30)
        self.available_eq_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(avail_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.available_eq_list.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.available_eq_list.yview)

        # Pipeline sequence
        seq_frame = tk.LabelFrame(pipe_frame, text="Pipeline Sequence", padx=10, pady=10)
        seq_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5, rowspan=2)

        self.pipeline_seq_list = tk.Listbox(seq_frame, height=15, width=30)
        self.pipeline_seq_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        seq_scrollbar = tk.Scrollbar(seq_frame)
        seq_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.pipeline_seq_list.config(yscrollcommand=seq_scrollbar.set)
        seq_scrollbar.config(command=self.pipeline_seq_list.yview)

        # Control buttons
        ctrl_frame = tk.Frame(pipe_frame)
        ctrl_frame.grid(row=1, column=2, sticky="n", padx=5, pady=5)

        ctrl_buttons = [
            ("➡️ Add", self._add_to_pipeline),
            ("⬅️ Remove", self._remove_from_pipeline),
            ("⬆️ Up", self._move_pipeline_up),
            ("⬇️ Down", self._move_pipeline_down),
            ("🔄 Clear", self._clear_pipeline)
        ]

        for text, command in ctrl_buttons:
            tk.Button(ctrl_frame, text=text, command=command, width=10).pack(pady=2)

        # Pipeline options
        opt_frame = tk.LabelFrame(pipe_frame, text="Pipeline Options", padx=10, pady=10)
        opt_frame.grid(row=2, column=2, sticky="nsew", padx=5, pady=5)

        self.pipeline_stop_on_error = tk.BooleanVar(value=True)
        tk.Checkbutton(opt_frame, text="Stop on error",
                      variable=self.pipeline_stop_on_error).pack(anchor=tk.W)

        self.pipeline_save_intermediate = tk.BooleanVar(value=False)
        tk.Checkbutton(opt_frame, text="Save intermediate results",
                      variable=self.pipeline_save_intermediate).pack(anchor=tk.W)

        self.pipeline_parallel_var = tk.BooleanVar(value=False)
        tk.Checkbutton(opt_frame, text="Parallel processing",
                      variable=self.pipeline_parallel_var).pack(anchor=tk.W)

        # Load available equations
        self._refresh_available_equations()

    def _create_visualization_tab(self):
        """Create visualization tab"""
        # Visualization type selection
        viz_type_frame = tk.LabelFrame(self.visualization_tab, text="Visualization Type", padx=10, pady=10)
        viz_type_frame.pack(fill=tk.X, padx=10, pady=10)

        viz_types = ["2D Scatter", "3D Scatter", "Histogram", "Box Plot",
                    "Ternary Diagram", "Spider/Radar", "Heatmap", "PCA"]

        self.viz_type_var = tk.StringVar(value="2D Scatter")
        for i, viz_type in enumerate(viz_types):
            rb = tk.Radiobutton(viz_type_frame, text=viz_type,
                               variable=self.viz_type_var, value=viz_type)
            rb.grid(row=i//4, column=i%4, sticky=tk.W, padx=5, pady=2)

        # Plot configuration
        config_frame = tk.LabelFrame(self.visualization_tab, text="Plot Configuration", padx=10, pady=10)
        config_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # X, Y, Z axis selection
        axis_frame = tk.Frame(config_frame)
        axis_frame.pack(fill=tk.X, pady=5)

        tk.Label(axis_frame, text="X-axis:").pack(side=tk.LEFT, padx=5)
        self.viz_x_var = tk.StringVar()
        ttk.Combobox(axis_frame, textvariable=self.viz_x_var,
                    width=20).pack(side=tk.LEFT, padx=5)

        tk.Label(axis_frame, text="Y-axis:").pack(side=tk.LEFT, padx=5)
        self.viz_y_var = tk.StringVar()
        ttk.Combobox(axis_frame, textvariable=self.viz_y_var,
                    width=20).pack(side=tk.LEFT, padx=5)

        tk.Label(axis_frame, text="Z-axis:").pack(side=tk.LEFT, padx=5)
        self.viz_z_var = tk.StringVar()
        ttk.Combobox(axis_frame, textvariable=self.viz_z_var,
                    width=20).pack(side=tk.LEFT, padx=5)

        # Color and size by
        style_frame = tk.Frame(config_frame)
        style_frame.pack(fill=tk.X, pady=5)

        tk.Label(style_frame, text="Color by:").pack(side=tk.LEFT, padx=5)
        self.viz_color_var = tk.StringVar()
        ttk.Combobox(style_frame, textvariable=self.viz_color_var,
                    width=20).pack(side=tk.LEFT, padx=5)

        tk.Label(style_frame, text="Size by:").pack(side=tk.LEFT, padx=5)
        self.viz_size_var = tk.StringVar()
        ttk.Combobox(style_frame, textvariable=self.viz_size_var,
                    width=20).pack(side=tk.LEFT, padx=5)

        # Plot options
        opt_frame = tk.Frame(config_frame)
        opt_frame.pack(fill=tk.X, pady=5)

        self.viz_log_x = tk.BooleanVar(value=False)
        tk.Checkbutton(opt_frame, text="Log X", variable=self.viz_log_x).pack(side=tk.LEFT, padx=5)

        self.viz_log_y = tk.BooleanVar(value=False)
        tk.Checkbutton(opt_frame, text="Log Y", variable=self.viz_log_y).pack(side=tk.LEFT, padx=5)

        self.viz_grid = tk.BooleanVar(value=True)
        tk.Checkbutton(opt_frame, text="Grid", variable=self.viz_grid).pack(side=tk.LEFT, padx=5)

        self.viz_legend = tk.BooleanVar(value=True)
        tk.Checkbutton(opt_frame, text="Legend", variable=self.viz_legend).pack(side=tk.LEFT, padx=5)

        # Plot area
        plot_frame = tk.Frame(self.visualization_tab)
        plot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Create matplotlib figure
        self.viz_fig = Figure(figsize=(8, 6), dpi=100)
        self.viz_ax = self.viz_fig.add_subplot(111)

        self.viz_canvas = FigureCanvasTkAgg(self.viz_fig, plot_frame)
        self.viz_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Toolbar
        self.viz_toolbar = NavigationToolbar2Tk(self.viz_canvas, plot_frame)
        self.viz_toolbar.update()

        # Plot control buttons
        ctrl_frame = tk.Frame(self.visualization_tab)
        ctrl_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        tk.Button(ctrl_frame, text="📊 Generate Plot",
                 command=self._generate_plot,
                 bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)

        tk.Button(ctrl_frame, text="💾 Save Plot",
                 command=self._save_plot,
                 bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=5)

        tk.Button(ctrl_frame, text="🔄 Refresh Data",
                 command=self._refresh_viz_data,
                 bg="#FF9800", fg="white").pack(side=tk.LEFT, padx=5)

        # Populate axis options
        self._refresh_viz_data()

    def _create_ml_tab(self):
        """Create machine learning tab"""
        # ML model selection
        model_frame = tk.LabelFrame(self.ml_tab, text="Machine Learning Models", padx=10, pady=10)
        model_frame.pack(fill=tk.X, padx=10, pady=10)

        ml_models = [
            ("PCA", "Dimensionality Reduction"),
            ("t-SNE", "Non-linear Dimensionality Reduction"),
            ("K-Means", "Clustering"),
            ("Random Forest", "Classification/Regression"),
            ("SVM", "Classification"),
            ("Neural Network", "Deep Learning")
        ]

        self.ml_model_vars = {}
        for i, (model, desc) in enumerate(ml_models):
            frame = tk.Frame(model_frame)
            frame.grid(row=i//2, column=i%2, sticky=tk.W, padx=5, pady=2)

            var = tk.BooleanVar(value=False)
            tk.Checkbutton(frame, text=model, variable=var).pack(side=tk.LEFT)
            tk.Label(frame, text=desc, fg="gray", font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
            self.ml_model_vars[model] = var

        # Feature selection
        feature_frame = tk.LabelFrame(self.ml_tab, text="Feature Selection", padx=10, pady=10)
        feature_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Feature listbox
        feat_list_frame = tk.Frame(feature_frame)
        feat_list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.ml_features_list = tk.Listbox(feat_list_frame, selectmode=tk.MULTIPLE, height=8)
        self.ml_features_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        feat_scroll = tk.Scrollbar(feat_list_frame)
        feat_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.ml_features_list.config(yscrollcommand=feat_scroll.set)
        feat_scroll.config(command=self.ml_features_list.yview)

        # Target variable
        target_frame = tk.Frame(feature_frame)
        target_frame.pack(fill=tk.X, pady=5)

        tk.Label(target_frame, text="Target Variable:").pack(side=tk.LEFT, padx=5)
        self.ml_target_var = tk.StringVar()
        ttk.Combobox(target_frame, textvariable=self.ml_target_var, width=20).pack(side=tk.LEFT, padx=5)

        # ML parameters
        param_frame = tk.LabelFrame(self.ml_tab, text="Model Parameters", padx=10, pady=10)
        param_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # PCA components
        tk.Label(param_frame, text="PCA Components:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.pca_components_var = tk.IntVar(value=2)
        tk.Spinbox(param_frame, from_=1, to=10, textvariable=self.pca_components_var,
                  width=5).grid(row=0, column=1, padx=5, pady=2)

        # Clusters for K-Means
        tk.Label(param_frame, text="Clusters (K):").grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        self.kmeans_clusters_var = tk.IntVar(value=3)
        tk.Spinbox(param_frame, from_=2, to=10, textvariable=self.kmeans_clusters_var,
                  width=5).grid(row=0, column=3, padx=5, pady=2)

        # Train/test split
        tk.Label(param_frame, text="Test Size:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.test_size_var = tk.DoubleVar(value=0.2)
        tk.Scale(param_frame, from_=0.1, to=0.5, resolution=0.05,
                variable=self.test_size_var, orient=tk.HORIZONTAL,
                length=100).grid(row=1, column=1, padx=5, pady=2)

        # Results display
        result_frame = tk.LabelFrame(self.ml_tab, text="Results", padx=10, pady=10)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.ml_results_text = scrolledtext.ScrolledText(result_frame, height=10,
                                                        wrap=tk.WORD,
                                                        font=("Consolas", 10))
        self.ml_results_text.pack(fill=tk.BOTH, expand=True)

        # Control buttons
        ctrl_frame = tk.Frame(self.ml_tab)
        ctrl_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        tk.Button(ctrl_frame, text="🤖 Train Model",
                 command=self._train_ml_model,
                 bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)

        tk.Button(ctrl_frame, text="📊 Visualize",
                 command=self._visualize_ml_results,
                 bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=5)

        tk.Button(ctrl_frame, text="💾 Save Model",
                 command=self._save_ml_model,
                 bg="#9C27B0", fg="white").pack(side=tk.LEFT, padx=5)

        tk.Button(ctrl_frame, text="📈 Feature Importance",
                 command=self._show_feature_importance,
                 bg="#FF9800", fg="white").pack(side=tk.LEFT, padx=5)

        # Populate features
        self._refresh_ml_features()

    def _create_batch_tab(self):
        """Create batch processing tab"""
        # Batch configuration
        config_frame = tk.LabelFrame(self.batch_tab, text="Batch Configuration", padx=10, pady=10)
        config_frame.pack(fill=tk.X, padx=10, pady=10)

        # Input directory
        tk.Label(config_frame, text="Input Directory:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.batch_input_var = tk.StringVar()
        tk.Entry(config_frame, textvariable=self.batch_input_var, width=40).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(config_frame, text="Browse...",
                 command=lambda: self._browse_directory(self.batch_input_var)).grid(row=0, column=2, padx=5, pady=5)

        # Output directory
        tk.Label(config_frame, text="Output Directory:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.batch_output_var = tk.StringVar()
        tk.Entry(config_frame, textvariable=self.batch_output_var, width=40).grid(row=1, column=1, padx=5, pady=5)
        tk.Button(config_frame, text="Browse...",
                 command=lambda: self._browse_directory(self.batch_output_var)).grid(row=1, column=2, padx=5, pady=5)

        # File pattern
        tk.Label(config_frame, text="File Pattern:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.batch_pattern_var = tk.StringVar(value="*.xlsx,*.csv")
        tk.Entry(config_frame, textvariable=self.batch_pattern_var, width=40).grid(row=2, column=1, padx=5, pady=5)

        # Batch operations
        ops_frame = tk.LabelFrame(self.batch_tab, text="Batch Operations", padx=10, pady=10)
        ops_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.batch_ops_vars = {}
        batch_ops = [
            ("Apply Equations", "Apply selected equations to all files"),
            ("Generate Reports", "Create summary reports"),
            ("Create Plots", "Generate visualizations"),
            ("Export Results", "Export to multiple formats"),
            ("Validate Data", "Check data quality"),
            ("Calculate Statistics", "Compute summary statistics")
        ]

        for i, (op, desc) in enumerate(batch_ops):
            frame = tk.Frame(ops_frame)
            frame.grid(row=i//2, column=i%2, sticky=tk.W, padx=5, pady=2)

            var = tk.BooleanVar(value=False)
            tk.Checkbutton(frame, text=op, variable=var).pack(side=tk.LEFT)
            tk.Label(frame, text=desc, fg="gray", font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
            self.batch_ops_vars[op] = var

        # Progress and log
        log_frame = tk.LabelFrame(self.batch_tab, text="Batch Processing Log", padx=10, pady=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.batch_log_text = scrolledtext.ScrolledText(log_frame, height=15,
                                                       wrap=tk.WORD,
                                                       font=("Consolas", 9))
        self.batch_log_text.pack(fill=tk.BOTH, expand=True)

        # Control buttons
        ctrl_frame = tk.Frame(self.batch_tab)
        ctrl_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        tk.Button(ctrl_frame, text="🔍 Scan Files",
                 command=self._scan_batch_files,
                 bg="#FF9800", fg="white").pack(side=tk.LEFT, padx=5)

        tk.Button(ctrl_frame, text="▶️ Start Batch",
                 command=self._start_batch_processing,
                 bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)

        tk.Button(ctrl_frame, text="⏸️ Pause",
                 command=self._pause_batch_processing,
                 bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=5)

        tk.Button(ctrl_frame, text="⏹️ Stop",
                 command=self._stop_batch_processing,
                 bg="#F44336", fg="white").pack(side=tk.LEFT, padx=5)

        tk.Button(ctrl_frame, text="🗑️ Clear Log",
                 command=lambda: self.batch_log_text.delete("1.0", tk.END),
                 bg="#9E9E9E", fg="white").pack(side=tk.LEFT, padx=5)

    def _create_settings_tab(self):
        """Create settings tab"""
        # General settings
        general_frame = tk.LabelFrame(self.settings_tab, text="General Settings", padx=10, pady=10)
        general_frame.pack(fill=tk.X, padx=10, pady=10)

        # Calculation precision
        tk.Label(general_frame, text="Calculation Precision:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.precision_var = tk.IntVar(value=6)
        tk.Spinbox(general_frame, from_=2, to=15, textvariable=self.precision_var,
                  width=5).grid(row=0, column=1, padx=5, pady=5)

        # Default units
        tk.Label(general_frame, text="Default Units:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.default_units_var = tk.StringVar(value="wt%")
        ttk.Combobox(general_frame, textvariable=self.default_units_var,
                    values=["wt%", "ppm", "mg/kg", "mol%"], width=10).grid(row=1, column=1, padx=5, pady=5)

        # Auto-save
        self.autosave_var = tk.BooleanVar(value=True)
        tk.Checkbutton(general_frame, text="Auto-save library",
                      variable=self.autosave_var).grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)

        # Auto-validate
        self.autovalidate_var = tk.BooleanVar(value=True)
        tk.Checkbutton(general_frame, text="Auto-validate expressions",
                      variable=self.autovalidate_var).grid(row=3, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)

        # Performance settings
        perf_frame = tk.LabelFrame(self.settings_tab, text="Performance Settings", padx=10, pady=10)
        perf_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Vectorization
        self.vectorization_var = tk.BooleanVar(value=True)
        tk.Checkbutton(perf_frame, text="Enable vectorization",
                      variable=self.vectorization_var).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)

        # Caching
        self.caching_var = tk.BooleanVar(value=True)
        tk.Checkbutton(perf_frame, text="Enable result caching",
                      variable=self.caching_var).grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)

        # Parallel processing
        self.parallel_var = tk.BooleanVar(value=False)
        tk.Checkbutton(perf_frame, text="Parallel processing",
                      variable=self.parallel_var).grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)

        # Cache size
        tk.Label(perf_frame, text="Cache Size (MB):").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.cache_size_var = tk.IntVar(value=100)
        tk.Scale(perf_frame, from_=10, to=1000, variable=self.cache_size_var,
                orient=tk.HORIZONTAL, length=200).grid(row=3, column=1, padx=5, pady=5)

        # Visualization settings
        viz_frame = tk.LabelFrame(self.settings_tab, text="Visualization Settings", padx=10, pady=10)
        viz_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Default plot style
        tk.Label(viz_frame, text="Default Plot Style:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.plot_style_var = tk.StringVar(value="seaborn")
        ttk.Combobox(viz_frame, textvariable=self.plot_style_var,
                    values=["default", "seaborn", "ggplot", "bmh", "dark_background"],
                    width=15).grid(row=0, column=1, padx=5, pady=5)

        # Color palette
        tk.Label(viz_frame, text="Color Palette:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.color_palette_var = tk.StringVar(value="viridis")
        ttk.Combobox(viz_frame, textvariable=self.color_palette_var,
                    values=["viridis", "plasma", "inferno", "magma", "coolwarm", "Set1", "Set2", "Set3"],
                    width=15).grid(row=1, column=1, padx=5, pady=5)

        # Figure size
        tk.Label(viz_frame, text="Figure Size:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        fig_size_frame = tk.Frame(viz_frame)
        fig_size_frame.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)

        self.fig_width_var = tk.IntVar(value=10)
        tk.Spinbox(fig_size_frame, from_=5, to=20, textvariable=self.fig_width_var,
                  width=3).pack(side=tk.LEFT)
        tk.Label(fig_size_frame, text="x").pack(side=tk.LEFT, padx=2)
        self.fig_height_var = tk.IntVar(value=8)
        tk.Spinbox(fig_size_frame, from_=5, to=20, textvariable=self.fig_height_var,
                  width=3).pack(side=tk.LEFT)

        # DPI
        tk.Label(viz_frame, text="DPI:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.dpi_var = tk.IntVar(value=100)
        tk.Spinbox(viz_frame, from_=50, to=300, textvariable=self.dpi_var,
                  width=5).grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)

        # Save/Load settings
        save_frame = tk.Frame(self.settings_tab)
        save_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        tk.Button(save_frame, text="💾 Save Settings",
                 command=self._save_settings,
                 bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)

        tk.Button(save_frame, text="📄 Load Settings",
                 command=self._load_settings,
                 bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=5)

        tk.Button(save_frame, text="🔄 Reset to Defaults",
                 command=self._reset_settings,
                 bg="#9E9E9E", fg="white").pack(side=tk.LEFT, padx=5)

    def _create_menu_bar(self):
        """Create menu bar for the editor window"""
        menubar = tk.Menu(self.window)
        self.window.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Equation", command=self._new_equation)
        file_menu.add_command(label="Open Equation...", command=self._open_equation_file)
        file_menu.add_command(label="Save Equation", command=self._save_equation_advanced)
        file_menu.add_command(label="Save Equation As...", command=self._save_equation_as)
        file_menu.add_separator()
        file_menu.add_command(label="Import Equations...", command=self._import_library_advanced)
        file_menu.add_command(label="Export Equations...", command=self._export_library_advanced)
        file_menu.add_separator()
        file_menu.add_command(label="Export Results...", command=self._export_results)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.window.destroy)

        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=lambda: self.expr_text.event_generate("<<Undo>>"))
        edit_menu.add_command(label="Redo", command=lambda: self.expr_text.event_generate("<<Redo>>"))
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", command=lambda: self.expr_text.event_generate("<<Cut>>"))
        edit_menu.add_command(label="Copy", command=lambda: self.expr_text.event_generate("<<Copy>>"))
        edit_menu.add_command(label="Paste", command=lambda: self.expr_text.event_generate("<<Paste>>"))
        edit_menu.add_separator()
        edit_menu.add_command(label="Find...", command=self._open_find_dialog)
        edit_menu.add_command(label="Replace...", command=self._open_replace_dialog)

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_checkbutton(label="Show Line Numbers", variable=tk.BooleanVar(value=True))
        view_menu.add_checkbutton(label="Syntax Highlighting", variable=tk.BooleanVar(value=True))
        view_menu.add_separator()
        view_menu.add_command(label="Zoom In", command=self._zoom_in)
        view_menu.add_command(label="Zoom Out", command=self._zoom_out)
        view_menu.add_command(label="Reset Zoom", command=self._reset_zoom)

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Template Wizard...", command=self._open_template_wizard)
        tools_menu.add_command(label="Unit Converter...", command=self._open_unit_converter)
        tools_menu.add_command(label="Data Validator...", command=self._open_data_validator)
        tools_menu.add_command(label="Statistical Analysis...", command=self._open_statistical_analysis)
        tools_menu.add_separator()
        tools_menu.add_command(label="Batch Processor...", command=lambda: self.notebook.select(self.batch_tab))
        tools_menu.add_command(label="ML Model Trainer...", command=lambda: self.notebook.select(self.ml_tab))

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self._open_documentation)
        help_menu.add_command(label="Examples", command=self._show_examples)
        help_menu.add_command(label="Check for Updates", command=self._check_for_updates)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self._show_about)

    # ============================================================================
    # CORE FUNCTIONALITY ENHANCEMENTS
    # ============================================================================

    def _parse_expression_advanced(self):
        """Advanced expression parsing with symbolic evaluation"""
        expression = self.expr_text.get("1.0", tk.END).strip()

        if not expression:
            messagebox.showwarning("Empty Expression", "Please enter an expression.")
            return

        try:
            # Remove comments
            lines = expression.split('\n')
            cleaned_lines = []
            for line in lines:
                if '#' in line:
                    line = line[:line.index('#')]
                cleaned_lines.append(line.strip())
            expression = ' '.join(cleaned_lines)

            # Extract variables with regex
            variable_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b'
            all_vars = re.findall(variable_pattern, expression)

            # Filter out functions and constants
            math_funcs = list(self.advanced_math_functions.keys())
            constants = ['pi', 'e', 'inf', 'nan']
            variables = [v for v in all_vars if v not in math_funcs + constants]
            variables = list(set(variables))

            # Symbolic parsing with sympy
            if HAS_SYMPY:
                try:
                    sympy_vars = symbols(' '.join(variables))
                    expr_sympy = sympify(expression)

                    # Get free symbols
                    free_symbols = expr_sympy.free_symbols
                    sympy_var_names = [str(s) for s in free_symbols]

                    # Update variable list
                    self.variable_list = sympy_var_names
                except:
                    self.variable_list = variables

            # Update variable tree
            self._update_variable_tree(variables)

            # Validate expression
            self._validate_expression_advanced(expression, variables)

            # Show success
            self.status_label.config(text=f"✅ Parsed: {len(variables)} variables")

        except Exception as e:
            error_msg = f"Error parsing expression:\n\n{str(e)}"
            messagebox.showerror("Parse Error", error_msg)

    def _validate_expression_advanced(self, expression, variables):
        """Advanced validation with multiple test cases"""
        try:
            # Test with random values
            test_cases = 5
            results = []

            for _ in range(test_cases):
                test_env = self.advanced_math_functions.copy()

                # Add random values for variables
                for var in variables:
                    test_env[var] = np.random.uniform(0.1, 100) if HAS_NUMPY else 1.0

                # Evaluate
                compiled = compile(expression, '<string>', 'eval')
                result = eval(compiled, {"__builtins__": {}}, test_env)

                # Check result
                if HAS_NUMPY and (np.isnan(result) or np.isinf(result)):
                    raise ValueError(f"Expression returned {result}")

                results.append(result)

            # Check consistency across test cases
            if results:
                if all(r == results[0] for r in results):
                    self.status_label.config(text=f"✅ Valid: Returns constant value {results[0]:.4f}")
                else:
                    if HAS_NUMPY:
                        mean_val = np.mean(results)
                        std_val = np.std(results)
                        self.status_label.config(text=f"✅ Valid: Test mean={mean_val:.4f}, std={std_val:.4f}")
                    else:
                        self.status_label.config(text=f"✅ Valid: Test values {results[:3]}...")

            return True

        except Exception as e:
            raise Exception(f"Validation failed: {str(e)}")

    def _apply_to_data_advanced(self):
        """Apply equation to data with vectorization"""
        if not hasattr(self.app, 'samples') or not self.app.samples:
            messagebox.showwarning("No Data", "No samples loaded.")
            return

        expression = self.expr_text.get("1.0", tk.END).strip()
        expression = expression.split('#')[0].strip()

        if not expression:
            messagebox.showwarning("No Expression", "Please enter an expression.")
            return

        # Parse and validate
        self._parse_expression_advanced()

        # Get column name
        col_name = self.eq_name_var.get().strip()
        if not col_name:
            col_name = "Custom_Calculation"
        col_name = re.sub(r'[^a-zA-Z0-9_]', '_', col_name)

        # Ask for vectorization preference
        use_vectorization = self.vectorize_var.get() and HAS_NUMPY

        try:
            if use_vectorization:
                results = self._apply_vectorized(expression, col_name)
            else:
                results = self._apply_sequential(expression, col_name)

            # Update status
            if HAS_NUMPY:
                success_count = np.sum(~np.isnan(results))
                total_count = len(results)

                # Show statistics
                valid_results = results[~np.isnan(results)]
                if len(valid_results) > 0:
                    stats_text = (
                        f"Applied '{col_name}' to {success_count}/{total_count} samples\n"
                        f"Mean: {np.mean(valid_results):.4f}, "
                        f"Std: {np.std(valid_results):.4f}, "
                        f"Range: [{np.min(valid_results):.4f}, {np.max(valid_results):.4f}]"
                    )
                else:
                    stats_text = f"Applied '{col_name}' but no valid results"
            else:
                success_count = sum(1 for r in results if r is not None)
                total_count = len(results)
                stats_text = f"Applied '{col_name}' to {success_count}/{total_count} samples"

            messagebox.showinfo("Application Complete", stats_text)
            self.status_label.config(text=f"✅ Applied to {success_count}/{total_count} samples")

            # Update display if app has update method
            if hasattr(self.app, 'update_display'):
                self.app.update_display()

        except Exception as e:
            messagebox.showerror("Application Error",
                               f"Error applying equation:\n\n{str(e)}")

    def _apply_vectorized(self, expression, col_name):
        """Apply equation using vectorized operations"""
        # Convert samples to numpy arrays
        var_arrays = {}

        for var in self.variable_list:
            values = []
            for sample in self.app.samples:
                val = sample.get(var)
                if val is not None and val != '':
                    try:
                        values.append(float(val))
                    except:
                        values.append(np.nan)
                else:
                    values.append(np.nan)
            var_arrays[var] = np.array(values)

        # Create evaluation environment
        env = self.advanced_math_functions.copy()
        env.update(var_arrays)

        # Add numpy functions
        env.update({
            'np': np,
            'nan': np.nan,
            'isnan': np.isnan,
            'isinf': np.isinf
        })

        # Evaluate expression
        try:
            compiled = compile(expression, '<string>', 'eval')
            results = eval(compiled, {"__builtins__": {}}, env)

            # Ensure results is array
            if np.isscalar(results):
                results = np.full(len(self.app.samples), results)

            # Apply to samples
            for i, result in enumerate(results):
                self.app.samples[i][col_name] = result if not np.isnan(result) else None

            return results

        except Exception as e:
            raise Exception(f"Vectorized evaluation failed: {str(e)}")

    def _apply_sequential(self, expression, col_name):
        """Apply equation sequentially (fallback method)"""
        results = []

        for i, sample in enumerate(self.app.samples):
            # Create evaluation environment
            env = self.advanced_math_functions.copy()

            # Add variable values
            missing = False
            for var in self.variable_list:
                value = sample.get(var)
                if value is not None and value != '':
                    try:
                        env[var] = float(value)
                    except:
                        missing = True
                        break
                else:
                    missing = True
                    break

            if missing:
                results.append(None)
                sample[col_name] = None
                continue

            try:
                # Evaluate expression
                compiled = compile(expression, '<string>', 'eval')
                result = eval(compiled, {"__builtins__": {}}, env)

                # Store result
                sample[col_name] = result
                results.append(result)

            except Exception as e:
                results.append(None)
                sample[col_name] = None

        return results

    def _preview_results_advanced(self):
        """Advanced preview with statistics and visualization"""
        if not hasattr(self.app, 'samples') or not self.app.samples:
            messagebox.showwarning("No Data", "No samples loaded.")
            return

        expression = self.expr_text.get("1.0", tk.END).strip()
        expression = expression.split('#')[0].strip()

        if not expression:
            messagebox.showwarning("No Expression", "Please enter an expression.")
            return

        # Create preview window
        preview_win = tk.Toplevel(self.window)
        preview_win.title("Advanced Calculation Preview")
        preview_win.geometry("1200x800")

        # Calculate results
        results = []
        variable_data = {var: [] for var in self.variable_list}

        sample_limit = min(50, len(self.app.samples))
        for i, sample in enumerate(self.app.samples[:sample_limit]):
            env = self.advanced_math_functions.copy()
            missing = False

            for var in self.variable_list:
                val = sample.get(var)
                if val is not None and val != '':
                    try:
                        float_val = float(val)
                        env[var] = float_val
                        variable_data[var].append(float_val)
                    except:
                        env[var] = np.nan if HAS_NUMPY else None
                        variable_data[var].append(np.nan if HAS_NUMPY else None)
                        missing = True
                else:
                    env[var] = np.nan if HAS_NUMPY else None
                    variable_data[var].append(np.nan if HAS_NUMPY else None)
                    missing = True

            if missing:
                results.append(np.nan if HAS_NUMPY else None)
            else:
                try:
                    compiled = compile(expression, '<string>', 'eval')
                    result = eval(compiled, {"__builtins__": {}}, env)
                    results.append(result)
                except:
                    results.append(np.nan if HAS_NUMPY else None)

        # Create notebook for different views
        preview_notebook = ttk.Notebook(preview_win)
        preview_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Tab 1: Data Table
        table_frame = ttk.Frame(preview_notebook)
        preview_notebook.add(table_frame, text="Data Table")

        # Create treeview
        columns = ["Sample"] + self.variable_list + ["Result"]
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)

        tree.column("Sample", width=120)
        tree.column("Result", width=150)

        # Add data
        for i, sample in enumerate(self.app.samples[:sample_limit]):
            values = [sample.get('Sample_ID', f'Sample_{i+1}')]
            for var in self.variable_list:
                val = sample.get(var, '')
                if val not in ['', None]:
                    try:
                        values.append(f"{float(val):.4f}")
                    except:
                        values.append(str(val))
                else:
                    values.append('N/A')

            # Format result
            if i < len(results):
                if HAS_NUMPY and np.isnan(results[i]):
                    values.append('Error')
                elif results[i] is None:
                    values.append('Error')
                else:
                    values.append(f"{results[i]:.6f}")
            else:
                values.append('N/A')

            tree.insert("", tk.END, values=values)

        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)

        # Tab 2: Statistics
        stats_frame = ttk.Frame(preview_notebook)
        preview_notebook.add(stats_frame, text="Statistics")

        stats_text = scrolledtext.ScrolledText(stats_frame, wrap=tk.WORD, font=("Consolas", 10))
        stats_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Calculate statistics
        if HAS_NUMPY:
            valid_results = [r for r in results if not np.isnan(r)]
        else:
            valid_results = [r for r in results if r is not None]

        if valid_results:
            stats_info = f"""
EXPRESSION: {expression}
VARIABLES: {', '.join(self.variable_list)}
SAMPLES: {len(results)} total, {len(valid_results)} valid ({len(results)-len(valid_results)} invalid)

RESULTS STATISTICS:
  Count:    {len(valid_results)}
"""
            if HAS_NUMPY and len(valid_results) > 0:
                stats_info += f"""  Mean:     {np.mean(valid_results):.6f}
  Std Dev:  {np.std(valid_results):.6f}
  Min:      {np.min(valid_results):.6f}
  Max:      {np.max(valid_results):.6f}
  Median:   {np.median(valid_results):.6f}
"""
                if len(valid_results) > 1:
                    stats_info += f"""  Q1:       {np.percentile(valid_results, 25):.6f}
  Q3:       {np.percentile(valid_results, 75):.6f}
  Range:    {np.ptp(valid_results):.6f}
"""
                if HAS_SCIPY and len(valid_results) > 2:
                    stats_info += f"""  Skewness: {stats.skew(valid_results):.4f}
"""
                if HAS_SCIPY and len(valid_results) > 3:
                    stats_info += f"""  Kurtosis: {stats.kurtosis(valid_results):.4f}
"""
            else:
                # Basic statistics without numpy
                if valid_results:
                    stats_info += f"""  Min:      {min(valid_results):.6f}
  Max:      {max(valid_results):.6f}
"""

            stats_info += "\nVARIABLE STATISTICS:\n"
            for var in self.variable_list[:5]:  # Limit to 5 variables
                var_vals = variable_data[var]
                if HAS_NUMPY:
                    var_vals = [v for v in var_vals if not np.isnan(v)]
                else:
                    var_vals = [v for v in var_vals if v is not None]

                if var_vals:
                    stats_info += f"\n  {var}:"
                    if HAS_NUMPY:
                        stats_info += f" n={len(var_vals)}, mean={np.mean(var_vals):.4f}, range=[{np.min(var_vals):.4f}, {np.max(var_vals):.4f}]"
                    else:
                        stats_info += f" n={len(var_vals)}, range=[{min(var_vals):.4f}, {max(var_vals):.4f}]"

            stats_text.insert("1.0", stats_info)
        else:
            stats_text.insert("1.0", "No valid results to display statistics.")

        # Tab 3: Histogram (if matplotlib available)
        if HAS_MATPLOTLIB and valid_results and HAS_NUMPY:
            try:
                hist_frame = ttk.Frame(preview_notebook)
                preview_notebook.add(hist_frame, text="Histogram")

                fig = Figure(figsize=(10, 6))
                ax = fig.add_subplot(111)

                ax.hist(valid_results, bins=min(20, len(valid_results)), edgecolor='black', alpha=0.7)
                ax.set_xlabel('Result Value')
                ax.set_ylabel('Frequency')
                ax.set_title('Distribution of Calculation Results')
                ax.grid(True, alpha=0.3)

                # Add statistics to plot
                stats_text_plot = f'n={len(valid_results)}\nμ={np.mean(valid_results):.4f}\nσ={np.std(valid_results):.4f}'
                ax.text(0.95, 0.95, stats_text_plot, transform=ax.transAxes,
                       verticalalignment='top', horizontalalignment='right',
                       bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

                canvas = FigureCanvasTkAgg(fig, hist_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

                toolbar = NavigationToolbar2Tk(canvas, hist_frame)
                toolbar.update()
                canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            except:
                pass

    def _save_equation_advanced(self):
        """Save equation with advanced metadata"""
        # Collect metadata
        metadata = {
            'name': self.eq_name_var.get().strip(),
            'category': self.eq_category_var.get(),
            'version': self.eq_version_var.get(),
            'author': self.eq_author_var.get(),
            'tags': [t.strip() for t in self.eq_tags_var.get().split(',') if t.strip()],
            'description': self.eq_desc_text.get("1.0", tk.END).strip(),
            'expression': self.expr_text.get("1.0", tk.END).strip().split('#')[0].strip(),
            'variables': self.variable_list,
            'created': datetime.now().isoformat(),
            'modified': datetime.now().isoformat(),
            'type': 'advanced',
            'vectorized': self.vectorize_var.get(),
            'validation_status': 'validated',
            'usage_count': 0,
            'rating': 0,
            'dependencies': self._detect_dependencies()
        }

        # Validate
        if not metadata['name']:
            messagebox.showwarning("Missing Name", "Please enter an equation name.")
            return

        if not metadata['expression']:
            messagebox.showwarning("Missing Expression", "Please enter an expression.")
            return

        # Parse and validate expression
        self._parse_expression_advanced()

        # Check for existing equation
        existing_idx = -1
        for i, eq in enumerate(self.equations):
            if eq['name'] == metadata['name'] and eq.get('type') == 'advanced':
                existing_idx = i
                break

        if existing_idx >= 0:
            # Update existing
            metadata['created'] = self.equations[existing_idx].get('created', metadata['created'])
            metadata['usage_count'] = self.equations[existing_idx].get('usage_count', 0)
            metadata['rating'] = self.equations[existing_idx].get('rating', 0)
            self.equations[existing_idx] = metadata
            action = "Updated"
        else:
            # Add new
            self.equations.append(metadata)
            action = "Saved"

        # Save to library
        self._save_formula_library_advanced()

        # Refresh displays
        self._refresh_library_advanced()
        self._refresh_available_equations()

        self.status_label.config(text=f"✅ {action}: {metadata['name']} v{metadata['version']}")

    def _detect_dependencies(self):
        """Detect mathematical dependencies in expression"""
        expression = self.expr_text.get("1.0", tk.END).strip()
        dependencies = []

        # Check for numpy functions
        numpy_funcs = ['mean', 'median', 'std', 'var', 'min', 'max', 'sum', 'percentile']
        for func in numpy_funcs:
            if func in expression:
                dependencies.append(f'numpy.{func}')

        # Check for scipy functions
        if HAS_SCIPY:
            scipy_funcs = ['skew', 'kurtosis']
            for func in scipy_funcs:
                if func in expression:
                    dependencies.append(f'scipy.stats.{func}')

        # Check for special operations
        if '**' in expression:
            dependencies.append('exponentiation')
        if 'log' in expression or 'log10' in expression:
            dependencies.append('logarithm')
        if 'sin' in expression or 'cos' in expression or 'tan' in expression:
            dependencies.append('trigonometry')

        return list(set(dependencies))

    # ============================================================================
    # UTILITY FUNCTIONS
    # ============================================================================

    def _update_line_numbers(self, event=None):
        """Update line numbers in the editor"""
        lines = self.expr_text.get("1.0", tk.END).count('\n')
        self.line_numbers.config(state='normal')
        self.line_numbers.delete("1.0", tk.END)

        for i in range(1, lines + 1):
            self.line_numbers.insert(tk.END, f"{i}\n")

        self.line_numbers.config(state='disabled')

    def _insert_in_expression(self, text):
        """Insert text at cursor position in expression editor"""
        self.expr_text.insert(tk.INSERT, text)
        self.expr_text.focus_set()

    def _auto_parse_expression(self, event=None):
        """Auto-parse expression when typing"""
        if self.auto_parse_var.get():
            try:
                self._parse_expression_advanced()
            except:
                pass

    def _update_variable_tree(self, variables):
        """Update the variable tree display"""
        # Clear tree
        for item in self.var_tree.get_children():
            self.var_tree.delete(item)

        # Add variables with inferred types
        for var in sorted(variables):
            # Try to infer type from name
            var_type = "Unknown"
            if var.endswith('_ppm'):
                var_type = "Trace Element"
                unit = "ppm"
            elif var.endswith('_wt') or re.match(r'^[A-Z][a-z]?[0-9]?O[0-9]?$', var):
                var_type = "Oxide"
                unit = "wt%"
            elif 'Ratio' in var or '/' in var:
                var_type = "Ratio"
                unit = ""
            else:
                unit = ""

            # Check if variable exists in data
            in_data = False
            if hasattr(self.app, 'samples') and self.app.samples:
                in_data = any(var in sample for sample in self.app.samples[:5])

            description = "In data" if in_data else "Not found in data"

            self.var_tree.insert("", tk.END, values=(var, var_type, unit, description))

    def _update_data_preview(self):
        """Update data preview panel"""
        if not hasattr(self.app, 'samples') or not self.app.samples:
            self.data_preview_text.delete("1.0", tk.END)
            self.data_preview_text.insert("1.0", "No data loaded.")
            return

        # Get variables from expression
        expression = self.expr_text.get("1.0", tk.END).strip()
        variables = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', expression)
        math_funcs = list(self.advanced_math_functions.keys()) + ['pi', 'e']
        variables = [v for v in variables if v not in math_funcs]
        variables = list(set(variables))

        # Limit to first 5 samples and 10 variables
        preview_vars = variables[:10]
        preview_samples = self.app.samples[:5]

        # Create preview text
        preview = f"Data Preview (showing {len(preview_samples)} samples, {len(preview_vars)} variables):\n\n"

        # Header
        header = ["Sample"] + preview_vars
        preview += " | ".join(f"{h:>12}" for h in header) + "\n"
        preview += "-" * (len(header) * 13) + "\n"

        # Data rows
        for i, sample in enumerate(preview_samples):
            row = [sample.get('Sample_ID', f'Sample_{i}')]
            for var in preview_vars:
                val = sample.get(var)
                if val is not None and val != '':
                    try:
                        row.append(f"{float(val):>10.4f}")
                    except:
                        row.append(f"{str(val):>10}")
                else:
                    row.append(f"{'N/A':>10}")
            preview += " | ".join(row) + "\n"

        # Statistics
        if preview_vars and hasattr(self.app, 'samples'):
            preview += "\nSummary Statistics:\n"
            for var in preview_vars[:5]:  # Limit to 5 variables for statistics
                values = []
                for sample in self.app.samples:
                    val = sample.get(var)
                    if val is not None and val != '':
                        try:
                            values.append(float(val))
                        except:
                            pass

                if values:
                    if HAS_NUMPY:
                        preview += f"{var:>12}: n={len(values)}, mean={np.mean(values):.4f}, std={np.std(values):.4f}\n"
                    else:
                        preview += f"{var:>12}: n={len(values)}, mean={sum(values)/len(values):.4f}\n"

        self.data_preview_text.delete("1.0", tk.END)
        self.data_preview_text.insert("1.0", preview)

    def _refresh_library_advanced(self):
        """Refresh the advanced formula library display"""
        # Clear tree
        for item in self.library_tree.get_children():
            self.library_tree.delete(item)

        # Get filter
        filter_cat = self.library_filter_var.get()
        search_term = self.library_search_var.get().lower()

        # Add built-in formulas
        if filter_cat in ["All", "Built-in"]:
            for name, formula in self.builtin_formulas.items():
                if search_term and search_term not in name.lower():
                    continue

                self.library_tree.insert("", tk.END,
                                       values=(name,
                                              formula['category'],
                                              ", ".join(formula['variables'][:3]),
                                              "1.0",
                                              "System",
                                              ""),
                                       tags=("builtin",))

        # Add custom formulas
        for eq in self.equations:
            if filter_cat not in ["All", "Custom"] and eq.get('category', 'Custom') != filter_cat:
                continue

            if search_term and search_term not in eq['name'].lower():
                continue

            vars_display = ", ".join(eq.get('variables', [])[:3])
            if len(eq.get('variables', [])) > 3:
                vars_display += "..."

            self.library_tree.insert("", tk.END,
                                   values=(eq['name'],
                                          eq.get('category', 'Custom'),
                                          vars_display,
                                          eq.get('version', '1.0'),
                                          eq.get('author', ''),
                                          eq.get('last_used', '')),
                                   tags=("custom",))

        # Tag colors
        self.library_tree.tag_configure("builtin", background="#E8F5E9")
        self.library_tree.tag_configure("custom", background="#E3F2FD")

        # Sort if needed
        if self.library_sort_var.get() != "Name":
            self._sort_library(self.library_sort_var.get())

    def _sort_library(self, column):
        """Sort library by column"""
        items = [(self.library_tree.set(item, column), item)
                for item in self.library_tree.get_children('')]
        items.sort()

        for index, (val, item) in enumerate(items):
            self.library_tree.move(item, '', index)

    def _show_formula_details(self, event=None):
        """Show details of selected formula"""
        selection = self.library_tree.selection()
        if not selection:
            return

        item = self.library_tree.item(selection[0])
        name = item['values'][0]

        # Clear details
        self.formula_details_text.delete("1.0", tk.END)

        # Check if built-in or custom
        if "builtin" in item['tags']:
            formula = self.builtin_formulas.get(name)
            if formula:
                details = f"NAME: {name}\n"
                details += f"CATEGORY: {formula['category']}\n"
                details += f"REFERENCE: {formula.get('reference', 'N/A')}\n\n"
                details += f"DESCRIPTION:\n{formula['description']}\n\n"
                details += f"EXPRESSION:\n{formula['expression']}\n\n"
                details += f"VARIABLES: {', '.join(formula['variables'])}\n"
                self.formula_details_text.insert("1.0", details)
        else:
            # Find custom formula
            for eq in self.equations:
                if eq['name'] == name:
                    details = f"NAME: {eq['name']}\n"
                    details += f"CATEGORY: {eq.get('category', 'Custom')}\n"
                    details += f"VERSION: {eq.get('version', '1.0')}\n"
                    details += f"AUTHOR: {eq.get('author', 'N/A')}\n"
                    details += f"CREATED: {eq.get('created', 'N/A')}\n"
                    details += f"MODIFIED: {eq.get('modified', 'N/A')}\n\n"
                    details += f"DESCRIPTION:\n{eq.get('description', 'N/A')}\n\n"
                    details += f"EXPRESSION:\n{eq.get('expression', 'N/A')}\n\n"
                    details += f"VARIABLES: {', '.join(eq.get('variables', []))}\n"
                    details += f"TAGS: {', '.join(eq.get('tags', []))}\n"
                    self.formula_details_text.insert("1.0", details)
                    break

    def _on_formula_select_advanced(self, event=None):
        """When a formula is selected from library"""
        selection = self.library_tree.selection()
        if not selection:
            return

        item = self.library_tree.item(selection[0])
        name = item['values'][0]

        # Check if built-in or custom
        if "builtin" in item['tags']:
            formula = self.builtin_formulas.get(name)
            if formula:
                self.eq_name_var.set(name)
                self.eq_category_var.set(formula['category'])
                self.eq_version_var.set("1.0")
                self.eq_author_var.set("System")
                self.eq_tags_var.set("")
                self.eq_desc_text.delete("1.0", tk.END)
                self.eq_desc_text.insert("1.0", formula['description'])
                self.expr_text.delete("1.0", tk.END)
                self.expr_text.insert("1.0", formula['expression'])
                self._parse_expression_advanced()
        else:
            # Find custom formula
            for eq in self.equations:
                if eq['name'] == name:
                    self.eq_name_var.set(eq['name'])
                    self.eq_category_var.set(eq.get('category', 'Custom'))
                    self.eq_version_var.set(eq.get('version', '1.0'))
                    self.eq_author_var.set(eq.get('author', ''))
                    self.eq_tags_var.set(', '.join(eq.get('tags', [])))
                    self.eq_desc_text.delete("1.0", tk.END)
                    self.eq_desc_text.insert("1.0", eq.get('description', ''))
                    self.expr_text.delete("1.0", tk.END)
                    self.expr_text.insert("1.0", eq.get('expression', ''))
                    self.variable_list = eq.get('variables', [])

                    # Update variable tree
                    self._update_variable_tree(self.variable_list)
                    break

    def _load_selected_formula_advanced(self):
        """Load selected formula into editor"""
        self._on_formula_select_advanced(None)
        self.status_label.config(text="✅ Formula loaded")

    def _refresh_available_equations(self):
        """Refresh list of available equations for pipeline"""
        if not hasattr(self, 'available_eq_list'):
            return

        self.available_eq_list.delete(0, tk.END)

        # Add custom equations
        for eq in self.equations:
            self.available_eq_list.insert(tk.END, eq['name'])

        # Add built-in equations
        for name in self.builtin_formulas.keys():
            self.available_eq_list.insert(tk.END, f"[Built-in] {name}")

    def _refresh_viz_data(self):
        """Refresh visualization data options"""
        if not hasattr(self.app, 'samples') or not self.app.samples:
            return

        # Get all available columns from samples
        columns = set()
        for sample in self.app.samples:
            columns.update(sample.keys())

        columns = sorted(columns)

        # Update comboboxes
        for combobox_var in [self.viz_x_var, self.viz_y_var, self.viz_z_var,
                           self.viz_color_var, self.viz_size_var]:
            combobox = None
            # Find the combobox associated with this variable
            for widget in self.visualization_tab.winfo_children():
                if isinstance(widget, ttk.Combobox) and hasattr(widget, 'cget') and widget.cget('textvariable') == str(combobox_var):
                    combobox = widget
                    break

            if combobox:
                current_value = combobox_var.get()
                combobox['values'] = columns
                if current_value in columns:
                    combobox_var.set(current_value)
                elif columns:
                    combobox_var.set(columns[0])

    def _refresh_ml_features(self):
        """Refresh ML feature list"""
        if not hasattr(self.app, 'samples') or not self.app.samples:
            return

        self.ml_features_list.delete(0, tk.END)

        # Get numeric columns
        numeric_columns = []
        if self.app.samples:
            # Check first sample for numeric values
            sample = self.app.samples[0]
            for key, value in sample.items():
                if key != 'Sample_ID' and value is not None and value != '':
                    try:
                        float(value)
                        numeric_columns.append(key)
                    except:
                        pass

        for col in sorted(numeric_columns):
            self.ml_features_list.insert(tk.END, col)

        # Update target variable combobox
        if numeric_columns:
            self.ml_target_var.set(numeric_columns[0])
            # Find and update the combobox
            for widget in self.ml_tab.winfo_children():
                if isinstance(widget, ttk.Combobox) and hasattr(widget, 'cget') and widget.cget('textvariable') == str(self.ml_target_var):
                    widget['values'] = numeric_columns
                    break

    def _start_background_services(self):
        """Start background services for the editor"""
        # This runs in a separate thread
        def background_tasks():
            # Load data preview
            self._update_data_preview()

            # Refresh library
            self._refresh_library_advanced()

            # Refresh other tabs
            self._refresh_available_equations()
            self._refresh_viz_data()
            self._refresh_ml_features()

        # Run in thread to not block UI
        import threading
        thread = threading.Thread(target=background_tasks, daemon=True)
        thread.start()

    def _show_dependency_error(self):
        """Show dependency error message"""
        missing = []
        if not HAS_NUMPY: missing.append("numpy")
        if not HAS_SYMPY: missing.append("sympy")
        if not HAS_PANDAS: missing.append("pandas")

        response = messagebox.askyesno(
            "Missing Dependencies",
            f"Advanced Petro-Logic Editor requires:\n\n"
            f"• numpy (for vectorized calculations)\n"
            f"• sympy (for symbolic math)\n"
            f"• pandas (for data handling)\n\n"
            f"Missing: {', '.join(missing)}\n\n"
            f"Install missing dependencies?",
            parent=self.window if self.window else self.app.root
        )

        if response and hasattr(self.app, 'install_dependencies'):
            self.app.install_dependencies(missing)
        elif response and hasattr(self.app, 'open_plugin_manager'):
            if self.window:
                self.window.destroy()
            self.app.open_plugin_manager()

    def load_formula_library(self):
        """Load saved formula library"""
        try:
            import os
            lib_path = "config/advanced_petro_logic_library.json"
            if os.path.exists(lib_path):
                with open(lib_path, 'r') as f:
                    data = json.load(f)
                    self.equations = data.get('equations', [])
                    self.equation_pipelines = data.get('pipelines', [])
        except:
            self.equations = []
            self.equation_pipelines = []

    def load_unit_system(self):
        """Load unit system configuration"""
        try:
            import os
            unit_path = "config/unit_system.json"
            if os.path.exists(unit_path):
                with open(unit_path, 'r') as f:
                    self.unit_system = json.load(f)
        except:
            self.unit_system = {}

    def _save_formula_library_advanced(self):
        """Save advanced formula library"""
        try:
            import os
            os.makedirs("config", exist_ok=True)

            lib_path = "config/advanced_petro_logic_library.json"
            data = {
                'equations': self.equations,
                'pipelines': self.equation_pipelines,
                'saved': datetime.now().isoformat(),
                'version': '2.0'
            }

            with open(lib_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving library: {e}")

    # ============================================================================
    # PLUGIN MANAGEMENT FUNCTIONS
    # ============================================================================

    def get_info(self):
        """Get plugin information for plugin manager"""
        return PLUGIN_INFO.copy()

    def get_status(self):
        """Get plugin status"""
        return {
            'installed': self.is_installed,
            'requirements_met': HAS_REQUIREMENTS,
            'missing_deps': self._get_missing_dependencies(),
            'version': PLUGIN_INFO['version'],
            'equations_count': len(self.equations),
            'pipelines_count': len(self.equation_pipelines)
        }

    def _get_missing_dependencies(self):
        """Get missing dependencies"""
        missing = []
        if not HAS_NUMPY: missing.append("numpy")
        if not HAS_SYMPY: missing.append("sympy")
        if not HAS_PANDAS: missing.append("pandas")
        return missing

    def enable(self):
        """Enable the plugin"""
        return self.install()

    def disable(self):
        """Disable the plugin"""
        self.uninstall()
        return True

    # ============================================================================
    # BASIC IMPLEMENTATIONS FOR MISSING FEATURES
    # ============================================================================

    def _open_template_wizard(self):
        """Open template wizard dialog"""
        messagebox.showinfo("Template Wizard",
                          "Template Wizard feature will be available in the next update.",
                          parent=self.window)

    def _generate_plot(self):
        """Generate plot - basic implementation"""
        if not HAS_MATPLOTLIB:
            messagebox.showerror("Matplotlib Required",
                               "Matplotlib is required for plotting features.",
                               parent=self.window)
            return

        messagebox.showinfo("Generate Plot",
                          "Plot generation feature will be available in the next update.",
                          parent=self.window)

    def _train_ml_model(self):
        """Train ML model - basic implementation"""
        if not HAS_SKLEARN:
            messagebox.showerror("scikit-learn Required",
                               "scikit-learn is required for machine learning features.",
                               parent=self.window)
            return

        messagebox.showinfo("Train Model",
                          "Machine learning features will be available in the next update.",
                          parent=self.window)

    def _scan_batch_files(self):
        """Scan batch files - basic implementation"""
        messagebox.showinfo("Scan Files",
                          "Batch processing features will be available in the next update.",
                          parent=self.window)

    def _save_settings(self):
        """Save settings - basic implementation"""
        try:
            import os
            os.makedirs("config", exist_ok=True)

            settings_path = "config/advanced_petro_logic_settings.json"
            settings = {
                'precision': self.precision_var.get(),
                'default_units': self.default_units_var.get(),
                'autosave': self.autosave_var.get(),
                'autovalidate': self.autovalidate_var.get(),
                'vectorization': self.vectorization_var.get(),
                'caching': self.caching_var.get(),
                'parallel': self.parallel_var.get(),
                'cache_size': self.cache_size_var.get(),
                'plot_style': self.plot_style_var.get(),
                'color_palette': self.color_palette_var.get(),
                'fig_width': self.fig_width_var.get(),
                'fig_height': self.fig_height_var.get(),
                'dpi': self.dpi_var.get(),
                'saved': datetime.now().isoformat()
            }

            with open(settings_path, 'w') as f:
                json.dump(settings, f, indent=2)

            messagebox.showinfo("Settings Saved",
                              "Settings have been saved successfully.",
                              parent=self.window)

        except Exception as e:
            messagebox.showerror("Save Error",
                               f"Error saving settings:\n\n{str(e)}",
                               parent=self.window)

    def _load_settings(self):
        """Load settings - basic implementation"""
        try:
            import os
            settings_path = "config/advanced_petro_logic_settings.json"
            if os.path.exists(settings_path):
                with open(settings_path, 'r') as f:
                    settings = json.load(f)

                # Apply settings
                self.precision_var.set(settings.get('precision', 6))
                self.default_units_var.set(settings.get('default_units', 'wt%'))
                self.autosave_var.set(settings.get('autosave', True))
                self.autovalidate_var.set(settings.get('autovalidate', True))
                self.vectorization_var.set(settings.get('vectorization', True))
                self.caching_var.set(settings.get('caching', True))
                self.parallel_var.set(settings.get('parallel', False))
                self.cache_size_var.set(settings.get('cache_size', 100))
                self.plot_style_var.set(settings.get('plot_style', 'seaborn'))
                self.color_palette_var.set(settings.get('color_palette', 'viridis'))
                self.fig_width_var.set(settings.get('fig_width', 10))
                self.fig_height_var.set(settings.get('fig_height', 8))
                self.dpi_var.set(settings.get('dpi', 100))

                messagebox.showinfo("Settings Loaded",
                                  "Settings have been loaded successfully.",
                                  parent=self.window)
            else:
                messagebox.showinfo("No Settings",
                                  "No saved settings found. Using defaults.",
                                  parent=self.window)

        except Exception as e:
            messagebox.showerror("Load Error",
                               f"Error loading settings:\n\n{str(e)}",
                               parent=self.window)

    def _reset_settings(self):
        """Reset settings to defaults"""
        response = messagebox.askyesno("Reset Settings",
                                      "Reset all settings to default values?",
                                      parent=self.window)
        if response:
            self.precision_var.set(6)
            self.default_units_var.set("wt%")
            self.autosave_var.set(True)
            self.autovalidate_var.set(True)
            self.vectorization_var.set(True)
            self.caching_var.set(True)
            self.parallel_var.set(False)
            self.cache_size_var.set(100)
            self.plot_style_var.set("seaborn")
            self.color_palette_var.set("viridis")
            self.fig_width_var.set(10)
            self.fig_height_var.set(8)
            self.dpi_var.set(100)

            messagebox.showinfo("Settings Reset",
                              "Settings have been reset to defaults.",
                              parent=self.window)

    # ============================================================================
    # PLACEHOLDER METHODS FOR FUTURE IMPLEMENTATION
    # ============================================================================

    def _optimize_expression(self):
        """Optimize expression for performance"""
        messagebox.showinfo("Optimization",
                          "Expression optimization feature is under development.",
                          parent=self.window)

    def _test_with_random(self):
        """Test expression with random data"""
        messagebox.showinfo("Random Test",
                          "Random testing feature is under development.",
                          parent=self.window)

    def _edit_selected_formula(self):
        """Edit selected formula"""
        self._load_selected_formula_advanced()
        self.notebook.select(self.editor_tab)

    def _delete_formula_advanced(self):
        """Delete selected formula"""
        selection = self.library_tree.selection()
        if not selection:
            return

        item = self.library_tree.item(selection[0])
        name = item['values'][0]

        # Don't delete built-in formulas
        if "builtin" in item['tags']:
            messagebox.showinfo("Cannot Delete",
                              "Built-in formulas cannot be deleted.",
                              parent=self.window)
            return

        # Confirm deletion
        if not messagebox.askyesno("Confirm Delete",
                                  f"Delete formula '{name}'?",
                                  parent=self.window):
            return

        # Delete from equations list
        self.equations = [eq for eq in self.equations if eq['name'] != name]

        # Save library
        self._save_formula_library_advanced()

        # Refresh display
        self._refresh_library_advanced()

        self.status_label.config(text=f"🗑️ Deleted: {name}")

    def _export_library_advanced(self):
        """Export formula library to file"""
        path = filedialog.asksaveasfilename(
            title="Export Formula Library",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            parent=self.window
        )

        if path:
            try:
                export_data = {
                    'equations': self.equations,
                    'pipelines': self.equation_pipelines,
                    'export_date': datetime.now().isoformat(),
                    'version': '2.0'
                }

                with open(path, 'w') as f:
                    json.dump(export_data, f, indent=2)

                messagebox.showinfo("Export Successful",
                                  f"Library exported to:\n{path}",
                                  parent=self.window)

            except Exception as e:
                messagebox.showerror("Export Error",
                                   f"Error: {str(e)}",
                                   parent=self.window)

    def _import_library_advanced(self):
        """Import formula library from file"""
        path = filedialog.askopenfilename(
            title="Import Formula Library",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            parent=self.window
        )

        if path:
            try:
                with open(path, 'r') as f:
                    import_data = json.load(f)

                # Merge equations
                imported_eqs = import_data.get('equations', [])

                # Check for duplicates
                existing_names = [eq['name'] for eq in self.equations]
                new_eqs = []

                for eq in imported_eqs:
                    if eq['name'] not in existing_names:
                        new_eqs.append(eq)

                # Add new equations
                self.equations.extend(new_eqs)

                # Merge pipelines
                imported_pipes = import_data.get('pipelines', [])
                existing_pipe_names = [p.get('name', '') for p in self.equation_pipelines]
                new_pipes = []

                for pipe in imported_pipes:
                    if pipe.get('name', '') not in existing_pipe_names:
                        new_pipes.append(pipe)

                self.equation_pipelines.extend(new_pipes)

                # Save library
                self._save_formula_library_advanced()

                # Refresh display
                self._refresh_library_advanced()
                self._refresh_available_equations()

                messagebox.showinfo("Import Successful",
                                  f"Imported {len(new_eqs)} new formulas and {len(new_pipes)} new pipelines.",
                                  parent=self.window)

            except Exception as e:
                messagebox.showerror("Import Error",
                                   f"Error: {str(e)}",
                                   parent=self.window)

    def _rate_formula(self):
        """Rate selected formula"""
        selection = self.library_tree.selection()
        if not selection:
            return

        item = self.library_tree.item(selection[0])
        name = item['values'][0]

        # Simple rating dialog
        rating = simpledialog.askinteger("Rate Formula",
                                        f"Rate '{name}' (1-5 stars):",
                                        minvalue=1, maxvalue=5,
                                        parent=self.window)

        if rating:
            # Update rating in equations list
            for eq in self.equations:
                if eq['name'] == name:
                    eq['rating'] = rating
                    break

            # Save library
            self._save_formula_library_advanced()

            messagebox.showinfo("Rating Saved",
                              f"Rated '{name}' with {rating} stars.",
                              parent=self.window)

    def _show_usage_stats(self):
        """Show usage statistics"""
        selection = self.library_tree.selection()
        if not selection:
            messagebox.showinfo("Usage Statistics",
                              f"Total formulas: {len(self.equations)}\n"
                              f"Built-in formulas: {len(self.builtin_formulas)}\n"
                              f"Pipelines: {len(self.equation_pipelines)}",
                              parent=self.window)
            return

        item = self.library_tree.item(selection[0])
        name = item['values'][0]

        # Find formula
        for eq in self.equations:
            if eq['name'] == name:
                stats = f"Formula: {name}\n"
                stats += f"Category: {eq.get('category', 'Custom')}\n"
                stats += f"Usage count: {eq.get('usage_count', 0)}\n"
                stats += f"Rating: {eq.get('rating', 'Not rated')}/5\n"
                stats += f"Created: {eq.get('created', 'Unknown')}\n"
                stats += f"Last modified: {eq.get('modified', 'Unknown')}\n"
                stats += f"Variables: {len(eq.get('variables', []))}\n"

                messagebox.showinfo("Formula Statistics",
                                  stats,
                                  parent=self.window)
                return

        # If built-in formula
        if name in self.builtin_formulas:
            formula = self.builtin_formulas[name]
            stats = f"Formula: {name}\n"
            stats += f"Category: {formula['category']}\n"
            stats += f"Type: Built-in\n"
            stats += f"Variables: {len(formula['variables'])}\n"
            stats += f"Reference: {formula.get('reference', 'N/A')}\n"

            messagebox.showinfo("Formula Statistics",
                              stats,
                              parent=self.window)

    def _add_to_pipeline(self):
        """Add equation to pipeline"""
        selection = self.available_eq_list.curselection()
        if not selection:
            return

        eq_name = self.available_eq_list.get(selection[0])
        self.pipeline_seq_list.insert(tk.END, eq_name)

    def _remove_from_pipeline(self):
        """Remove equation from pipeline"""
        selection = self.pipeline_seq_list.curselection()
        if not selection:
            return

        self.pipeline_seq_list.delete(selection[0])

    def _move_pipeline_up(self):
        """Move equation up in pipeline"""
        selection = self.pipeline_seq_list.curselection()
        if not selection or selection[0] == 0:
            return

        index = selection[0]
        item = self.pipeline_seq_list.get(index)
        self.pipeline_seq_list.delete(index)
        self.pipeline_seq_list.insert(index-1, item)
        self.pipeline_seq_list.selection_set(index-1)

    def _move_pipeline_down(self):
        """Move equation down in pipeline"""
        selection = self.pipeline_seq_list.curselection()
        if not selection or selection[0] == self.pipeline_seq_list.size()-1:
            return

        index = selection[0]
        item = self.pipeline_seq_list.get(index)
        self.pipeline_seq_list.delete(index)
        self.pipeline_seq_list.insert(index+1, item)
        self.pipeline_seq_list.selection_set(index+1)

    def _clear_pipeline(self):
        """Clear pipeline"""
        if messagebox.askyesno("Clear Pipeline",
                              "Clear the entire pipeline?",
                              parent=self.window):
            self.pipeline_seq_list.delete(0, tk.END)

    def _save_plot(self):
        """Save current plot"""
        if not HAS_MATPLOTLIB:
            messagebox.showerror("Matplotlib Required",
                               "Matplotlib is required to save plots.",
                               parent=self.window)
            return

        path = filedialog.asksaveasfilename(
            title="Save Plot",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"),
                      ("PDF files", "*.pdf"),
                      ("SVG files", "*.svg"),
                      ("All files", "*.*")],
            parent=self.window
        )

        if path and hasattr(self, 'viz_fig'):
            try:
                self.viz_fig.savefig(path, dpi=self.dpi_var.get())
                messagebox.showinfo("Plot Saved",
                                  f"Plot saved to:\n{path}",
                                  parent=self.window)
            except Exception as e:
                messagebox.showerror("Save Error",
                                   f"Error saving plot:\n\n{str(e)}",
                                   parent=self.window)

    def _visualize_ml_results(self):
        """Visualize ML results"""
        messagebox.showinfo("Visualize ML",
                          "ML visualization features will be available in the next update.",
                          parent=self.window)

    def _save_ml_model(self):
        """Save ML model"""
        messagebox.showinfo("Save ML Model",
                          "ML model saving features will be available in the next update.",
                          parent=self.window)

    def _show_feature_importance(self):
        """Show feature importance"""
        messagebox.showinfo("Feature Importance",
                          "Feature importance visualization will be available in the next update.",
                          parent=self.window)

    def _start_batch_processing(self):
        """Start batch processing"""
        messagebox.showinfo("Start Batch",
                          "Batch processing features will be available in the next update.",
                          parent=self.window)

    def _pause_batch_processing(self):
        """Pause batch processing"""
        messagebox.showinfo("Pause Batch",
                          "Batch processing features will be available in the next update.",
                          parent=self.window)

    def _stop_batch_processing(self):
        """Stop batch processing"""
        messagebox.showinfo("Stop Batch",
                          "Batch processing features will be available in the next update.",
                          parent=self.window)

    def _browse_directory(self, var):
        """Browse for directory"""
        directory = filedialog.askdirectory(parent=self.window)
        if directory:
            var.set(directory)

    def _zoom_in(self):
        """Zoom in editor"""
        current_font = self.expr_text.cget("font")
        try:
            size = int(current_font.split()[-1])
            self.expr_text.config(font=("Consolas", size + 1))
        except:
            pass

    def _zoom_out(self):
        """Zoom out editor"""
        current_font = self.expr_text.cget("font")
        try:
            size = int(current_font.split()[-1])
            if size > 8:
                self.expr_text.config(font=("Consolas", size - 1))
        except:
            pass

    def _reset_zoom(self):
        """Reset zoom"""
        self.expr_text.config(font=("Consolas", 11))

    def _new_equation(self):
        """Create new equation"""
        self.eq_name_var.set("")
        self.eq_category_var.set("Custom")
        self.eq_version_var.set("1.0")
        self.eq_author_var.set("")
        self.eq_tags_var.set("")
        self.eq_desc_text.delete("1.0", tk.END)
        self.expr_text.delete("1.0", tk.END)
        self.status_label.config(text="New equation started")

    def _open_equation_file(self):
        """Open equation from file"""
        path = filedialog.askopenfilename(
            title="Open Equation",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            parent=self.window
        )

        if path:
            try:
                with open(path, 'r') as f:
                    equation = json.load(f)

                # Load into editor
                self.eq_name_var.set(equation.get('name', ''))
                self.eq_category_var.set(equation.get('category', 'Custom'))
                self.eq_version_var.set(equation.get('version', '1.0'))
                self.eq_author_var.set(equation.get('author', ''))
                self.eq_tags_var.set(', '.join(equation.get('tags', [])))
                self.eq_desc_text.delete("1.0", tk.END)
                self.eq_desc_text.insert("1.0", equation.get('description', ''))
                self.expr_text.delete("1.0", tk.END)
                self.expr_text.insert("1.0", equation.get('expression', ''))

                self.status_label.config(text=f"Loaded equation from {path}")

            except Exception as e:
                messagebox.showerror("Load Error",
                                   f"Error loading equation:\n\n{str(e)}",
                                   parent=self.window)

    def _save_equation_as(self):
        """Save equation as new file"""
        path = filedialog.asksaveasfilename(
            title="Save Equation As",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            parent=self.window
        )

        if path:
            # Save current equation to file
            equation = {
                'name': self.eq_name_var.get().strip(),
                'category': self.eq_category_var.get(),
                'version': self.eq_version_var.get(),
                'author': self.eq_author_var.get(),
                'tags': [t.strip() for t in self.eq_tags_var.get().split(',') if t.strip()],
                'description': self.eq_desc_text.get("1.0", tk.END).strip(),
                'expression': self.expr_text.get("1.0", tk.END).strip().split('#')[0].strip(),
                'variables': self.variable_list,
                'saved': datetime.now().isoformat(),
                'type': 'advanced'
            }

            try:
                with open(path, 'w') as f:
                    json.dump(equation, f, indent=2)

                messagebox.showinfo("Save Successful",
                                  f"Equation saved to:\n{path}",
                                  parent=self.window)

            except Exception as e:
                messagebox.showerror("Save Error",
                                   f"Error saving equation:\n\n{str(e)}",
                                   parent=self.window)

    def _export_results(self):
        """Export calculation results"""
        if not hasattr(self.app, 'samples') or not self.app.samples:
            messagebox.showinfo("No Data",
                              "No data to export.",
                              parent=self.window)
            return

        path = filedialog.asksaveasfilename(
            title="Export Results",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx"), ("All files", "*.*")],
            parent=self.window
        )

        if path:
            try:
                if HAS_PANDAS:
                    # Convert samples to DataFrame
                    df = pd.DataFrame(self.app.samples)

                    if path.endswith('.xlsx'):
                        df.to_excel(path, index=False)
                    else:
                        df.to_csv(path, index=False)

                    messagebox.showinfo("Export Successful",
                                      f"Results exported to:\n{path}",
                                      parent=self.window)
                else:
                    # Manual CSV export
                    import csv
                    with open(path, 'w', newline='', encoding='utf-8') as f:
                        if self.app.samples:
                            writer = csv.DictWriter(f, fieldnames=self.app.samples[0].keys())
                            writer.writeheader()
                            writer.writerows(self.app.samples)

                    messagebox.showinfo("Export Successful",
                                      f"Results exported to:\n{path}",
                                      parent=self.window)

            except Exception as e:
                messagebox.showerror("Export Error",
                                   f"Error exporting results:\n\n{str(e)}",
                                   parent=self.window)

    def _open_find_dialog(self):
        """Open find dialog for expression editor"""
        find_dialog = tk.Toplevel(self.window)
        find_dialog.title("Find")
        find_dialog.geometry("400x150")
        find_dialog.transient(self.window)

        tk.Label(find_dialog, text="Find:").pack(pady=5)
        find_var = tk.StringVar()
        entry = tk.Entry(find_dialog, textvariable=find_var, width=40)
        entry.pack(pady=5)
        entry.focus_set()

        def do_find():
            text = self.expr_text.get("1.0", tk.END)
            search_term = find_var.get()
            if search_term and search_term in text:
                # Find and select
                start_pos = text.find(search_term)
                self.expr_text.tag_remove(tk.SEL, "1.0", tk.END)
                self.expr_text.tag_add(tk.SEL, f"1.0+{start_pos}c", f"1.0+{start_pos+len(search_term)}c")
                self.expr_text.focus_set()
                self.expr_text.see(f"1.0+{start_pos}c")

        entry.bind('<Return>', lambda e: do_find())

        tk.Button(find_dialog, text="Find", command=do_find).pack(pady=10)

    def _open_replace_dialog(self):
        """Open replace dialog"""
        messagebox.showinfo("Replace",
                          "Replace feature will be available in the next update.",
                          parent=self.window)

    def _open_unit_converter(self):
        """Open unit converter dialog"""
        converter = tk.Toplevel(self.window)
        converter.title("Unit Converter")
        converter.geometry("500x400")
        converter.transient(self.window)

        tk.Label(converter, text="Unit Converter",
                font=("Arial", 14, "bold")).pack(pady=20)

        # Simple unit converter
        frame = tk.Frame(converter)
        frame.pack(pady=20)

        tk.Label(frame, text="Value:").grid(row=0, column=0, padx=5, pady=5)
        value_var = tk.StringVar(value="1.0")
        tk.Entry(frame, textvariable=value_var, width=15).grid(row=0, column=1, padx=5, pady=5)

        tk.Label(frame, text="From:").grid(row=1, column=0, padx=5, pady=5)
        from_var = tk.StringVar(value="wt%")
        ttk.Combobox(frame, textvariable=from_var,
                    values=["wt%", "ppm", "mg/kg", "mol%"],
                    width=12).grid(row=1, column=1, padx=5, pady=5)

        tk.Label(frame, text="To:").grid(row=2, column=0, padx=5, pady=5)
        to_var = tk.StringVar(value="ppm")
        ttk.Combobox(frame, textvariable=to_var,
                    values=["wt%", "ppm", "mg/kg", "mol%"],
                    width=12).grid(row=2, column=1, padx=5, pady=5)

        result_var = tk.StringVar(value="")
        tk.Label(frame, text="Result:").grid(row=3, column=0, padx=5, pady=5)
        tk.Label(frame, textvariable=result_var, font=("Arial", 10, "bold")).grid(row=3, column=1, padx=5, pady=5)

        def convert():
            try:
                value = float(value_var.get())
                from_unit = from_var.get()
                to_unit = to_var.get()

                # Conversion factors
                conversions = {
                    ('wt%', 'ppm'): 10000,
                    ('ppm', 'wt%'): 0.0001,
                    ('wt%', 'mg/kg'): 10000,
                    ('mg/kg', 'wt%'): 0.0001,
                    ('ppm', 'mg/kg'): 1,
                    ('mg/kg', 'ppm'): 1,
                    ('mol%', 'wt%'): None,  # Would need molecular weights
                    ('wt%', 'mol%'): None   # Would need molecular weights
                }

                if from_unit == to_unit:
                    result = value
                elif (from_unit, to_unit) in conversions:
                    factor = conversions[(from_unit, to_unit)]
                    if factor is not None:
                        result = value * factor
                    else:
                        result_var.set("Need molecular weight")
                        return
                elif (to_unit, from_unit) in conversions:
                    factor = conversions[(to_unit, from_unit)]
                    if factor is not None:
                        result = value / factor
                    else:
                        result_var.set("Need molecular weight")
                        return
                else:
                    result_var.set("Conversion not available")
                    return

                result_var.set(f"{result:.6f}")

            except:
                result_var.set("Error")

        tk.Button(converter, text="Convert", command=convert,
                 bg="#4CAF50", fg="white", width=15).pack(pady=20)

        tk.Button(converter, text="Close", command=converter.destroy).pack(pady=10)

    def _open_data_validator(self):
        """Open data validator dialog"""
        validator = tk.Toplevel(self.window)
        validator.title("Data Validator")
        validator.geometry("600x500")
        validator.transient(self.window)

        tk.Label(validator, text="Data Validator",
                font=("Arial", 14, "bold")).pack(pady=20)

        if not hasattr(self.app, 'samples') or not self.app.samples:
            tk.Label(validator, text="No data loaded for validation.",
                    fg="red").pack(pady=50)
            tk.Button(validator, text="Close", command=validator.destroy).pack(pady=20)
            return

        # Create validation report
        report_text = scrolledtext.ScrolledText(validator, wrap=tk.WORD)
        report_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Generate validation report
        report = "DATA VALIDATION REPORT\n"
        report += "=" * 50 + "\n\n"

        report += f"Total samples: {len(self.app.samples)}\n\n"

        # Check for missing values
        missing_counts = {}
        all_columns = set()

        for sample in self.app.samples:
            all_columns.update(sample.keys())

        all_columns = sorted(all_columns)

        for column in all_columns:
            missing = 0
            total = 0
            for sample in self.app.samples:
                total += 1
                val = sample.get(column)
                if val is None or val == '':
                    missing += 1
                elif isinstance(val, str):
                    try:
                        float(val)
                    except:
                        missing += 1

            if missing > 0:
                missing_counts[column] = missing

        if missing_counts:
            report += "MISSING OR INVALID VALUES:\n"
            for column, count in missing_counts.items():
                percentage = (count / len(self.app.samples)) * 100
                report += f"  {column}: {count}/{len(self.app.samples)} ({percentage:.1f}%)\n"
        else:
            report += "MISSING OR INVALID VALUES: None\n"

        report += "\n"

        # Check for numeric ranges
        numeric_columns = []
        for column in all_columns:
            if column != 'Sample_ID':
                try:
                    # Check if column has numeric values
                    values = []
                    for sample in self.app.samples:
                        val = sample.get(column)
                        if val is not None and val != '':
                            try:
                                values.append(float(val))
                            except:
                                pass

                    if values:
                        numeric_columns.append(column)
                        report += f"{column}:\n"
                        report += f"  Min: {min(values):.4f}\n"
                        report += f"  Max: {max(values):.4f}\n"
                        report += f"  Mean: {sum(values)/len(values):.4f}\n"
                        if HAS_NUMPY:
                            report += f"  Std: {np.std(values):.4f}\n"
                        report += "\n"
                except:
                    pass

        report_text.insert("1.0", report)
        report_text.config(state='disabled')

        tk.Button(validator, text="Close", command=validator.destroy).pack(pady=20)

    def _open_statistical_analysis(self):
        """Open statistical analysis dialog"""
        stats_dialog = tk.Toplevel(self.window)
        stats_dialog.title("Statistical Analysis")
        stats_dialog.geometry("700x600")
        stats_dialog.transient(self.window)

        if not hasattr(self.app, 'samples') or not self.app.samples:
            tk.Label(stats_dialog, text="No data loaded for analysis.",
                    fg="red").pack(pady=50)
            tk.Button(stats_dialog, text="Close", command=stats_dialog.destroy).pack(pady=20)
            return

        notebook = ttk.Notebook(stats_dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Summary statistics tab
        summary_tab = ttk.Frame(notebook)
        notebook.add(summary_tab, text="Summary Statistics")

        summary_text = scrolledtext.ScrolledText(summary_tab, wrap=tk.WORD)
        summary_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Calculate summary statistics
        summary = "SUMMARY STATISTICS\n"
        summary += "=" * 50 + "\n\n"

        all_columns = set()
        for sample in self.app.samples:
            all_columns.update(sample.keys())

        numeric_columns = []
        for column in sorted(all_columns):
            if column != 'Sample_ID':
                values = []
                for sample in self.app.samples:
                    val = sample.get(column)
                    if val is not None and val != '':
                        try:
                            values.append(float(val))
                        except:
                            pass

                if values:
                    numeric_columns.append(column)
                    summary += f"{column} (n={len(values)}):\n"
                    if HAS_NUMPY:
                        summary += f"  Mean: {np.mean(values):.6f}\n"
                        summary += f"  Std: {np.std(values):.6f}\n"
                        summary += f"  Min: {np.min(values):.6f}\n"
                        summary += f"  Max: {np.max(values):.6f}\n"
                        summary += f"  Median: {np.median(values):.6f}\n"
                        if len(values) > 1:
                            summary += f"  Q1: {np.percentile(values, 25):.6f}\n"
                            summary += f"  Q3: {np.percentile(values, 75):.6f}\n"
                        if HAS_SCIPY and len(values) > 2:
                            summary += f"  Skewness: {stats.skew(values):.4f}\n"
                        if HAS_SCIPY and len(values) > 3:
                            summary += f"  Kurtosis: {stats.kurtosis(values):.4f}\n"
                    else:
                        # Basic statistics without numpy
                        summary += f"  Min: {min(values):.6f}\n"
                        summary += f"  Max: {max(values):.6f}\n"
                        summary += f"  Mean: {sum(values)/len(values):.6f}\n"

                    summary += "\n"

        summary_text.insert("1.0", summary)
        summary_text.config(state='disabled')

        # Correlation matrix tab (if enough numeric columns)
        if len(numeric_columns) >= 2 and HAS_NUMPY:
            corr_tab = ttk.Frame(notebook)
            notebook.add(corr_tab, text="Correlations")

            corr_text = scrolledtext.ScrolledText(corr_tab, wrap=tk.WORD)
            corr_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # Build data matrix
            data_matrix = []
            for column in numeric_columns:
                column_data = []
                for sample in self.app.samples:
                    val = sample.get(column)
                    if val is not None and val != '':
                        try:
                            column_data.append(float(val))
                        except:
                            column_data.append(np.nan)
                    else:
                        column_data.append(np.nan)
                data_matrix.append(column_data)

            data_matrix = np.array(data_matrix).T

            # Calculate correlation matrix
            corr_matrix = np.corrcoef(data_matrix, rowvar=False)

            corr_report = "CORRELATION MATRIX\n"
            corr_report += "=" * 50 + "\n\n"

            # Format as table
            header = "       " + "".join([f"{col[:8]:>8}" for col in numeric_columns[:8]]) + "\n"
            corr_report += header
            corr_report += "       " + "-" * (8 * len(numeric_columns[:8])) + "\n"

            for i, row in enumerate(corr_matrix[:8]):  # Limit to 8x8 for display
                corr_report += f"{numeric_columns[i][:6]:>6} "
                for j, val in enumerate(row[:8]):
                    corr_report += f"{val:>8.3f}"
                corr_report += "\n"

            if len(numeric_columns) > 8:
                corr_report += f"\n(Showing first 8 of {len(numeric_columns)} variables)\n"

            # Find strongest correlations
            corr_report += "\nSTRONGEST CORRELATIONS (|r| > 0.7):\n"
            strong_corrs = []
            for i in range(len(numeric_columns)):
                for j in range(i+1, len(numeric_columns)):
                    if abs(corr_matrix[i, j]) > 0.7:
                        strong_corrs.append((abs(corr_matrix[i, j]), i, j))

            strong_corrs.sort(reverse=True)

            for abs_corr, i, j in strong_corrs[:10]:  # Top 10
                corr_report += f"  {numeric_columns[i]} - {numeric_columns[j]}: {corr_matrix[i, j]:.3f}\n"

            if not strong_corrs:
                corr_report += "  None found\n"

            corr_text.insert("1.0", corr_report)
            corr_text.config(state='disabled')

        tk.Button(stats_dialog, text="Close", command=stats_dialog.destroy).pack(pady=10)

    def _open_documentation(self):
        """Open documentation"""
        docs = tk.Toplevel(self.window)
        docs.title(f"{PLUGIN_INFO['name']} Documentation")
        docs.geometry("800x600")
        docs.transient(self.window)

        text = scrolledtext.ScrolledText(docs, wrap=tk.WORD, font=("Arial", 10))
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        docs_text = f"""
{PLUGIN_INFO['name']} v{PLUGIN_INFO['version']}
{'=' * 60}

OVERVIEW:
This advanced plugin provides powerful tools for creating, managing, and
applying custom geochemical calculations. It includes vectorized computations,
machine learning integration, advanced visualization, and batch processing.

MAIN FEATURES:

1. ADVANCED EQUATION EDITOR:
   - Syntax highlighting and line numbers
   - Real-time expression validation
   - Template wizard for common calculations
   - Symbolic math evaluation with sympy

2. VECTORIZED CALCULATIONS:
   - NumPy-powered for high performance
   - Parallel processing options
   - Result caching for repeated calculations
   - Automatic missing value handling

3. FORMULA LIBRARY:
   - Built-in geochemical formulas (CIA, Mg#, etc.)
   - Custom formula management
   - Import/export capabilities
   - Versioning and metadata tracking

4. VISUALIZATION:
   - 2D scatter plots with regression lines
   - Histograms and statistical plots
   - Customizable plot styles
   - Export to multiple formats

5. MACHINE LEARNING (Optional):
   - PCA for dimensionality reduction
   - K-Means clustering
   - Feature importance analysis
   - Model training and evaluation

6. BATCH PROCESSING:
   - Process multiple files automatically
   - Custom processing pipelines
   - Progress tracking and logging
   - Automated report generation

7. DATA MANAGEMENT:
   - Advanced data validation
   - Statistical analysis tools
   - Unit conversion system
   - Multiple export formats

KEYBOARD SHORTCUTS:
Ctrl+Shift+E      Open Equation Editor
Ctrl+S            Save equation
Ctrl+O            Open equation file
Ctrl+F            Find in editor
Ctrl+Z            Undo
Ctrl+Y            Redo

DEPENDENCIES:
Required: numpy, sympy, pandas, matplotlib
Optional: scipy, scikit-learn, plotly, seaborn

For more information and updates, visit the plugin repository.
"""

        text.insert("1.0", docs_text)
        text.config(state='disabled')

        tk.Button(docs, text="Close", command=docs.destroy).pack(pady=10)

    def _show_examples(self):
        """Show example equations and usage"""
        examples = tk.Toplevel(self.window)
        examples.title("Example Equations")
        examples.geometry("600x500")
        examples.transient(self.window)

        notebook = ttk.Notebook(examples)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Basic examples tab
        basic_tab = ttk.Frame(notebook)
        notebook.add(basic_tab, text="Basic")

        basic_text = scrolledtext.ScrolledText(basic_tab, wrap=tk.WORD, font=("Courier", 10))
        basic_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        basic_examples = """
# BASIC ARITHMETIC
SiO2 + Al2O3 + Fe2O3  # Sum of major oxides
(SiO2 + K2O) / (Fe2O3 + MgO)  # Felsic/Mafic ratio

# RATIOS AND INDICES
MgO / (MgO + Fe2O3) * 100  # Magnesium number
Al2O3 / (Al2O3 + CaO + Na2O + K2O) * 100  # CIA index
log(Zr_ppm / Y_ppm)  # Tectonic discrimination

# USING FUNCTIONS
sqrt(CaO / Na2O)  # Square root of ratio
log10(SiO2)  # Log transform
exp(0.1 * TiO2)  # Exponential function

# CONDITIONAL CALCULATIONS
if SiO2 > 65 then "Felsic" else "Mafic"  # Simple classification

# NORMALIZATION
SiO2 / mean([SiO2, Al2O3, Fe2O3])  # Normalized to mean
(SiO2 - min(SiO2)) / (max(SiO2) - min(SiO2))  # Min-max scaling
"""
        basic_text.insert("1.0", basic_examples)
        basic_text.config(state='disabled')

        # Advanced examples tab
        advanced_tab = ttk.Frame(notebook)
        notebook.add(advanced_tab, text="Advanced")

        advanced_text = scrolledtext.ScrolledText(advanced_tab, wrap=tk.WORD, font=("Courier", 10))
        advanced_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        advanced_examples = """
# VECTORIZED OPERATIONS
mean([SiO2, Al2O3, Fe2O3, MgO, CaO, Na2O, K2O])  # Average major oxides
std([SiO2, Al2O3, Fe2O3])  # Standard deviation

# STATISTICAL CALCULATIONS
(SiO2 - mean(SiO2)) / std(SiO2)  # Z-score normalization
percentile(SiO2, 50)  # Median

# COMPLEX WEATHERING INDICES
# CIA with apatite correction
Al2O3 / (Al2O3 + (CaO - 10/3*P2O5) + Na2O + K2O) * 100

# REE CALCULATIONS
La_ppm / 0.31  # Chondrite normalized
sum([La_ppm, Ce_ppm, Pr_ppm, Nd_ppm, Sm_ppm, Eu_ppm, Gd_ppm,
     Tb_ppm, Dy_ppm, Ho_ppm, Er_ppm, Tm_ppm, Yb_ppm, Lu_ppm])  # ΣREE

# FEATURE ENGINEERING FOR ML
log(SiO2 / Al2O3)  # Log ratio feature
(SiO2 * Al2O3) / (Fe2O3 * MgO)  # Interaction term
sqrt(SiO2) * log(Al2O3)  # Non-linear interaction
"""
        advanced_text.insert("1.0", advanced_examples)
        advanced_text.config(state='disabled')

        tk.Button(examples, text="Close", command=examples.destroy).pack(pady=10)

    def _check_for_updates(self):
        """Check for plugin updates"""
        messagebox.showinfo("Check for Updates",
                          f"Current version: {PLUGIN_INFO['version']}\n\n"
                          "Update checking feature will be available\n"
                          "when connected to plugin repository.",
                          parent=self.window)

    def _show_about(self):
        """Show about dialog"""
        about = tk.Toplevel(self.window)
        about.title(f"About {PLUGIN_INFO['name']}")
        about.geometry("500x400")
        about.transient(self.window)

        about_text = f"""
{PLUGIN_INFO['name']}
Version {PLUGIN_INFO['version']}

A powerful tool for creating and applying
custom geochemical calculations with
advanced features and machine learning
integration.

FEATURES:
• Advanced equation editor with syntax highlighting
• Vectorized calculations using NumPy
• Machine learning integration
• Advanced visualization capabilities
• Batch processing and automation
• Unit conversion and management
• Template wizard for common calculations
• Symbolic math validation

AUTHOR: {PLUGIN_INFO['author']}
LICENSE: CC BY-NC-SA 4.0

DEPENDENCIES:
• numpy, sympy, pandas, matplotlib
• scipy, scikit-learn (optional)
• plotly, seaborn (optional)

For bug reports and feature requests,
please visit the plugin repository.
"""

        text = scrolledtext.ScrolledText(about, wrap=tk.WORD, font=("Arial", 10))
        text.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        text.insert("1.0", about_text)
        text.config(state='disabled')

        tk.Button(about, text="Close", command=about.destroy).pack(pady=10)


# ============================================================================
# PLUGIN REGISTRATION FUNCTIONS
# ============================================================================

def get_plugin_info():
    """Get plugin information for registration"""
    return PLUGIN_INFO.copy()

def create_plugin_instance(main_app):
    """Create and return a plugin instance"""
    plugin = AdvancedPetroLogicPlugin(main_app)
    return plugin

def register_plugin(main_app):
    """Register the plugin with the application"""
    try:
        plugin = create_plugin_instance(main_app)

        # Try to install automatically if dependencies are met
        if HAS_REQUIREMENTS:
            success = plugin.install()
            if success:
                print(f"✅ {PLUGIN_INFO['name']} auto-installed successfully")
            else:
                print(f"⚠️ {PLUGIN_INFO['name']} could not be auto-installed")
        else:
            print(f"⚠️ {PLUGIN_INFO['name']} dependencies not met")

        return plugin

    except Exception as e:
        print(f"❌ Error registering plugin: {e}")
        traceback.print_exc()
        return None

# For backward compatibility
def setup_plugin(main_app):
    """Legacy setup function (for compatibility)"""
    return register_plugin(main_app)

# Auto-register if running as main (for testing)
if __name__ == "__main__":
    print(f"{PLUGIN_INFO['name']} v{PLUGIN_INFO['version']}")
    print("Plugin module loaded successfully.")
    print(f"Dependencies: numpy={HAS_NUMPY}, sympy={HAS_SYMPY}, pandas={HAS_PANDAS}")
