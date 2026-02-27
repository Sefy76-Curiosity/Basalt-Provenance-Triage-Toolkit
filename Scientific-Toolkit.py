#!/usr/bin/env python3
"""
Scientific Toolkit v2.0 - ttkbootstrap Edition
Fully converted to use ttkbootstrap for consistent theming
"""
APP_INFO = {
    "id": "scientific_toolkit",
    "name": "Scientific Toolkit",
    "version": "2.0.0",
    "author": "Sefy Levy",
    "description": "Scientific data analysis platform",
    "min_plugins_version": "2.0",
}

# ============ DEPENDENCY CHECKER (SINGLE VERSION) ============
import subprocess
import sys
import importlib.util
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
import threading
import os
from pathlib import Path
import ast

def scan_plugin_imports(plugin_dir):
    """Scan a plugin directory for imports and return detected dependencies"""
    plugin_deps = {}

    if not plugin_dir.exists():
        return plugin_deps

    # Common mappings from import name to pip package name
    IMPORT_TO_PIP = {
        'ttkbootstrap': 'ttkbootstrap',
        'pandas': 'pandas',
        'odf': 'odfpy',
        'openpyxl': 'openpyxl',
        'xlrd': 'xlrd',
        'numpy': 'numpy',
        'packaging': 'packaging',
        'pyvisa': 'PyVISA',
        'PIL': 'pillow',
        'matplotlib': 'matplotlib',
        'sklearn': 'scikit-learn',
        'scipy': 'scipy',
        'yaml': 'pyyaml',
        'bs4': 'beautifulsoup4',
        'requests': 'requests',
        'serial': 'pyserial',
        'flask': 'flask',
        'dash': 'dash',
        'plotly': 'plotly',
        'seaborn': 'seaborn',
        'statsmodels': 'statsmodels',
        'sympy': 'sympy',
        'xlwings': 'xlwings',
        'reportlab': 'reportlab',
        'pdfkit': 'pdfkit',
        'markdown': 'markdown',
        'jinja2': 'jinja2',
    }

    # Scan each Python file in the plugin directory
    for py_file in plugin_dir.glob("*.py"):
        if py_file.stem in ["__init__", "plugin_manager"]:
            continue

        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())

            plugin_imports = set()

            for node in ast.walk(tree):
                # Handle: import x, y
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        base_import = alias.name.split('.')[0]
                        plugin_imports.add(base_import)

                # Handle: from x import y
                elif isinstance(node, ast.ImportFrom) and node.module:
                    base_import = node.module.split('.')[0]
                    plugin_imports.add(base_import)

            # Check which imports are missing
            missing_for_plugin = []
            for imp in plugin_imports:
                # Skip standard library
                if imp in sys.builtin_module_names:
                    continue

                # Check if it's a third-party package
                spec = importlib.util.find_spec(imp)
                if spec is None and imp in IMPORT_TO_PIP:
                    missing_for_plugin.append({
                        'import_name': imp,
                        'pip_name': IMPORT_TO_PIP[imp],
                        'reason': f'Required by plugin: {py_file.stem}'
                    })

            if missing_for_plugin:
                plugin_deps[py_file.stem] = missing_for_plugin

        except Exception as e:
            print(f"Error scanning {py_file}: {e}")

    return plugin_deps

def check_main_app_dependencies():
    """Check for main app required packages"""
    MAIN_APP_PACKAGES = [
        {'import_name': 'ttkbootstrap', 'pip_name': 'ttkbootstrap',
         'reason': 'Required for modern themed UI'},
        {'import_name': 'pandas', 'pip_name': 'pandas',
         'reason': 'Required for Excel and LibreOffice ODS file import'},
        {'import_name': 'odf', 'pip_name': 'odfpy',
         'reason': 'Required for LibreOffice ODS file import'},
        {'import_name': 'openpyxl', 'pip_name': 'openpyxl',
         'reason': 'Required for modern Excel files (.xlsx)'},
        {'import_name': 'xlrd', 'pip_name': 'xlrd',
         'reason': 'Required for older Excel files (.xls)'},
        {'import_name': 'numpy', 'pip_name': 'numpy',
         'reason': 'Required for numerical operations'},
        {'import_name': 'packaging', 'pip_name': 'packaging',
         'reason': 'Required for version comparison'},
        {'import_name': 'pyvisa', 'pip_name': 'PyVISA',
         'reason': 'Required for hardware communication'},
    ]

    missing = []
    for package in MAIN_APP_PACKAGES:
        spec = importlib.util.find_spec(package['import_name'])
        if spec is None:
            missing.append(package)

    return missing

def install_packages(missing_packages, title="Installing Dependencies", auto_continue=True):
    """Install missing packages with progress dialog"""
    if not missing_packages:
        return True

    install_root = tk.Tk()
    install_root.title(title)
    install_root.geometry("600x400")

    # Center window
    ws = install_root.winfo_screenwidth()
    hs = install_root.winfo_screenheight()
    x = (ws//2) - (600//2)
    y = (hs//2) - (400//2)
    install_root.geometry(f"+{x}+{y}")
    install_root.resizable(False, False)

    # Header
    tk.Label(install_root, text=f"📦 {title}",
             font=("Segoe UI", 14, "bold")).pack(pady=20)

    status_var = tk.StringVar(value="Preparing installation...")
    tk.Label(install_root, textvariable=status_var,
             font=("Segoe UI", 10)).pack(pady=10)

    # Progress bar
    progress = ttk.Progressbar(install_root, mode='indeterminate', length=500)
    progress.pack(pady=10)
    progress.start(10)

    # Output text area
    text_frame = tk.Frame(install_root)
    text_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

    output_text = scrolledtext.ScrolledText(text_frame, height=12, width=70, font=("Courier", 9))
    output_text.pack(fill=tk.BOTH, expand=True)

    # Status message
    status_message = tk.Label(install_root, text="", font=("Segoe UI", 9), fg="green")
    status_message.pack(pady=5)

    installation_complete = False
    all_success = False

    def auto_continue_msg():
        if auto_continue:
            status_message.config(text="✓ Installation complete! Continuing...")
            install_root.after(1500, install_root.destroy)

    def run_installation():
        nonlocal installation_complete, all_success
        packages_to_install = list({p['pip_name']: p for p in missing_packages}.values())
        all_success = True

        install_root.after(0, lambda: output_text.insert(tk.END,
            f"Starting installation of {len(packages_to_install)} packages...\n\n"))

        for i, package in enumerate(packages_to_install):
            def update_status(pkg, idx):
                status_var.set(f"Installing {pkg['pip_name']} ({idx+1}/{len(packages_to_install)})...")
                output_text.insert(tk.END, f"\n[{idx+1}/{len(packages_to_install)}] Installing {pkg['pip_name']}...\n")
                output_text.see(tk.END)

            install_root.after(0, lambda p=package, idx=i: update_status(p, idx))

            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", package['pip_name'], "--quiet"],
                    capture_output=True, text=True, timeout=120
                )

                if result.returncode == 0:
                    install_root.after(0, lambda p=package: output_text.insert(tk.END,
                        f"  ✅ Successfully installed {p['pip_name']}\n"))
                else:
                    error_msg = result.stderr[:200] + "..." if len(result.stderr) > 200 else result.stderr
                    install_root.after(0, lambda p=package, e=error_msg: output_text.insert(tk.END,
                        f"  ❌ Failed to install {p['pip_name']}\n     Error: {e}\n"))
                    all_success = False
            except Exception as e:
                install_root.after(0, lambda p=package, err=str(e): output_text.insert(tk.END,
                    f"  ❌ Error installing {p['pip_name']}: {err}\n"))
                all_success = False

            install_root.after(0, lambda: output_text.see(tk.END))

        install_root.after(0, progress.stop)

        if all_success:
            install_root.after(0, lambda: status_var.set("✅ All packages installed successfully!"))
            install_root.after(0, lambda: output_text.insert(tk.END,
                "\n\n" + "="*50 + "\n✅ ALL PACKAGES INSTALLED SUCCESSFULLY!\n" + "="*50 + "\n"))
            install_root.after(0, auto_continue_msg)
        else:
            install_root.after(0, lambda: status_var.set("⚠️ Some packages failed to install"))
            install_root.after(0, lambda: output_text.insert(tk.END,
                "\n\n" + "="*50 + "\n⚠️ SOME PACKAGES FAILED TO INSTALL\n" + "="*50 + "\n"))
            if auto_continue:
                install_root.after(3000, install_root.destroy)

        installation_complete = True

    threading.Thread(target=run_installation, daemon=True).start()

    def on_closing():
        install_root.destroy()

    install_root.protocol("WM_DELETE_WINDOW", on_closing)
    install_root.mainloop()

    return all_success

def check_and_install_all_dependencies():
    """Main dependency checker - handles main app and plugins"""
    # Step 1: Check main app dependencies
    print("Checking main application dependencies...")
    main_missing = check_main_app_dependencies()

    if main_missing:
        print(f"Found {len(main_missing)} missing main app packages")
        if not install_packages(main_missing, "Installing Main App Dependencies"):
            response = messagebox.askyesno(
                "Installation Issues",
                "Some main app packages failed to install.\n\nContinue anyway?"
            )
            if not response:
                return False
    else:
        print("All main app dependencies satisfied")

    # Step 2: Scan plugins for additional dependencies
    print("Scanning plugins for additional dependencies...")

    plugins_base = Path(__file__).parent / "plugins"
    all_plugin_deps = {}

    # Scan each plugin directory
    for plugin_type in ['hardware', 'software', 'add-ons']:
        plugin_dir = plugins_base / plugin_type
        if plugin_dir.exists():
            deps = scan_plugin_imports(plugin_dir)
            if deps:
                all_plugin_deps[plugin_type] = deps

    # Step 3: If plugins need dependencies, ask user
    if all_plugin_deps:
        # Build summary message
        summary = "The following plugins require additional packages:\n\n"
        total_plugins = 0
        all_needed_packages = []

        for plugin_type, plugins in all_plugin_deps.items():
            summary += f"\n📁 {plugin_type.upper()}:\n"
            for plugin_name, deps in plugins.items():
                total_plugins += 1
                packages = [d['pip_name'] for d in deps]
                summary += f"  • {plugin_name} needs: {', '.join(packages)}\n"
                all_needed_packages.extend(deps)

        # Remove duplicates
        unique_needed = list({p['pip_name']: p for p in all_needed_packages}.values())

        summary += f"\nTotal: {total_plugins} plugins need {len(unique_needed)} additional packages"

        # Ask user
        response = messagebox.askyesno(
            "Plugin Dependencies Found",
            summary + "\n\nWould you like to install these packages now?\n\n"
            "Yes: Install now\n"
            "No: Continue without installing (plugins may not work properly)"
        )

        if response:
            install_packages(unique_needed, "Installing Plugin Dependencies")

    # Step 4: Final verification and cleanup
    importlib.invalidate_caches()

    # One final check for critical packages
    critical_missing = []
    for critical in ['ttkbootstrap', 'numpy']:
        if importlib.util.find_spec(critical) is None:
            critical_missing.append(critical)

    if critical_missing:
        messagebox.showerror(
            "Critical Packages Missing",
            f"Critical packages are still missing: {', '.join(critical_missing)}\n\n"
            "The application cannot run without these.\n"
            "Please install them manually: pip install " + " ".join(critical_missing)
        )
        return False

    return True

# Run dependency check before any third-party imports
if not check_and_install_all_dependencies():
    sys.exit(1)

# Clear any import caches to ensure fresh imports after installation
importlib.invalidate_caches()

# Now safe to import third-party packages
import engines
import engines.classification_engine
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import sys, traceback


def excepthook(exc_type, exc_value, exc_traceback):
    with open('error.log', 'a') as f:
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
    sys.__excepthook__(exc_type, exc_value, exc_traceback)
sys.excepthook = excepthook

import json
import webbrowser
import csv
from pathlib import Path
from collections import defaultdict
from datetime import datetime

from data_hub import DataHub
from ui.left_panel import LeftPanel
from ui.center_panel import CenterPanel
from ui.right_panel import RightPanel

from features.tooltip_manager import ToolTipManager
from features.recent_files_manager import RecentFilesManager
from features.macro_recorder import MacroRecorder, MacroManagerDialog
from features.project_manager import ProjectManager
from features.script_exporter import ScriptExporter
from features.auto_save import AutoSaveManager
from features.settings_manager import SettingsManager, SettingsDialog

# ============ MESSAGEBOX PARENT PATCH ============
_messagebox_root = None

def set_messagebox_parent(root_window):
    global _messagebox_root
    _messagebox_root = root_window

original_showinfo = messagebox.showinfo
original_showwarning = messagebox.showwarning
original_showerror = messagebox.showerror
original_askyesno = messagebox.askyesno
original_askokcancel = messagebox.askokcancel
original_askretrycancel = messagebox.askretrycancel
original_askyesnocancel = messagebox.askyesnocancel

def patched_showinfo(title, message, **kwargs):
    if 'parent' not in kwargs and _messagebox_root:
        kwargs['parent'] = _messagebox_root
    return original_showinfo(title, message, **kwargs)

def patched_showwarning(title, message, **kwargs):
    if 'parent' not in kwargs and _messagebox_root:
        kwargs['parent'] = _messagebox_root
    return original_showwarning(title, message, **kwargs)

def patched_showerror(title, message, **kwargs):
    if 'parent' not in kwargs and _messagebox_root:
        kwargs['parent'] = _messagebox_root
    return original_showerror(title, message, **kwargs)

def patched_askyesno(title, message, **kwargs):
    if 'parent' not in kwargs and _messagebox_root:
        kwargs['parent'] = _messagebox_root
    return original_askyesno(title, message, **kwargs)

def patched_askokcancel(title, message, **kwargs):
    if 'parent' not in kwargs and _messagebox_root:
        kwargs['parent'] = _messagebox_root
    return original_askokcancel(title, message, **kwargs)

def patched_askretrycancel(title, message, **kwargs):
    if 'parent' not in kwargs and _messagebox_root:
        kwargs['parent'] = _messagebox_root
    return original_askretrycancel(title, message, **kwargs)

def patched_askyesnocancel(title, message, **kwargs):
    if 'parent' not in kwargs and _messagebox_root:
        kwargs['parent'] = _messagebox_root
    return original_askyesnocancel(title, message, **kwargs)

messagebox.showinfo = patched_showinfo
messagebox.showwarning = patched_showwarning
messagebox.showerror = patched_showerror
messagebox.askyesno = patched_askyesno
messagebox.askokcancel = patched_askokcancel
messagebox.askretrycancel = patched_askretrycancel
messagebox.askyesnocancel = patched_askyesnocancel

# ============ ENGINE MANAGER ============
class EngineManager:
    def __init__(self):
        self.engines_dir = Path("engines")
        self.available_engines = {}
        self._discover_engines()

    def _discover_engines(self):
        if not self.engines_dir.exists():
            self.engines_dir.mkdir(parents=True, exist_ok=True)
            return

        for engine_file in self.engines_dir.glob("*_engine.py"):
            engine_name = engine_file.stem.replace('_engine', '')
            data_folder = self.engines_dir / ("protocols" if engine_name == 'protocol' else engine_name)
            data_folder.mkdir(exist_ok=True)

            self.available_engines[engine_name] = {
                'path': engine_file, 'name': engine_name,
                'loaded': False, 'instance': None, 'data_folder': data_folder
            }

    def load_engine(self, engine_name):
        if engine_name not in self.available_engines:
            return None
        info = self.available_engines[engine_name]
        if info['loaded']:
            return info['instance']
        try:
            spec = importlib.util.spec_from_file_location(engine_name, info['path'])
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            cls = getattr(module, f"{engine_name.capitalize()}Engine", None)
            if cls:
                inst = cls(str(info['data_folder']))
                info['loaded'] = True
                info['instance'] = inst
                return inst
        except Exception as e:
            pass
        return None

    def get_available_engines(self):
        return list(self.available_engines.keys())

# ============ COLOR MANAGER ============
class ColorManager:
    def __init__(self, config_dir):
        self.config_dir = Path(config_dir)
        self.colors = self._load_colors()

    def _load_colors(self):
        f = self.config_dir / "scatter_colors.json"
        default = {
            "classification_colors": {},
            "default_colors": {"background": "#2b2b2b", "foreground": "#ffffff"}
        }
        if f.exists():
            try:
                with open(f) as fh:
                    return json.load(fh)
            except:
                return default
        return default

    def get_foreground(self, classification):
        c = self.colors.get("classification_colors", {}).get(classification)
        return c.get("foreground", self.colors["default_colors"]["foreground"]) if c else self.colors["default_colors"]["foreground"]

    def get_background(self, classification):
        c = self.colors.get("classification_colors", {}).get(classification)
        return c.get("background", self.colors["default_colors"]["background"]) if c else self.colors["default_colors"]["background"]

    def get_all_classifications(self):
        return list(self.colors.get("classification_colors", {}).keys())

# ============ SCIENTIFIC TOOLKIT ============
class ScientificToolkit:
    def __init__(self, root):
        self.root = root
        self.root.title("Scientific Toolkit")
        self.root.geometry("1400x850")
        self.settings = SettingsManager(self)
        self._is_closing = False

        # Apply theme: ui.theme takes priority; fall back to theme.name
        saved_theme = self.settings.get('ui', 'theme') or self.settings.get('theme', 'name')
        try:
            self.root.style.theme_use(saved_theme)
        except Exception:
            pass

        self.engine_manager = EngineManager()
        self.classification_engine = None
        self.protocol_engine = None
        self._load_initial_engines()

        self.config_dir = Path("config")
        self._load_chemical_elements()
        self.color_manager = ColorManager(self.config_dir)

        self.data_hub = DataHub()
        self.samples = self.data_hub.get_all()
        self.menu_bar = None
        self.current_engine_name = 'classification'
        self.current_engine = None

        self.tooltip_manager = ToolTipManager()

        max_recent = self.settings.get('recent_files', 'max_files')
        self.recent_files = RecentFilesManager(max_recent=max_recent)

        self.macro_recorder = MacroRecorder(self) if self.settings.get('macro_recorder', 'enabled') else None
        self.project_manager = ProjectManager(self)
        self.script_exporter = ScriptExporter(self) if self.settings.get('script_exporter', 'enabled') else None

        if self.settings.get('auto_save', 'enabled'):
            self.auto_save = AutoSaveManager(self, auto_save_interval=self.settings.get('auto_save', 'interval'))
        else:
            self.auto_save = None

        self.enabled_plugins = self._load_enabled_plugins()
        self.hardware_plugins = {}
        self._added_plugins = set()
        self.plot_plugin_types = []
        self._loaded_plugin_info = {}

        self._create_menu_structure()
        self._create_panels()
        self._build_bottom_controls()
        self._load_plugins()
        self._refresh_engine_menu()

        self.data_hub.register_observer(self.center)
        self.data_hub.register_observer(self.right)

        if self.settings.get('tooltips', 'enabled'):
            self.root.after(500, self._add_tooltips_to_panels)

        self._apply_ui_settings()
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _load_initial_engines(self):
        engines = self.engine_manager.get_available_engines()
        if 'classification' in engines:
            self.classification_engine = self.engine_manager.load_engine('classification')
        if 'protocol' in engines:
            self.protocol_engine = self.engine_manager.load_engine('protocol')

    def _load_chemical_elements(self):
        elements_file = self.config_dir / "chemical_elements.json"
        if elements_file.exists():
            try:
                with open(elements_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.chemical_elements = data.get("elements", {})
                    self.ui_groups = data.get("ui_groups", {})
                    self.element_reverse_map = {}
                    for info in self.chemical_elements.values():
                        for var in info["variations"]:
                            self.element_reverse_map[var] = info["standard"]
            except Exception as e:
                self.chemical_elements = {}
                self.element_reverse_map = {}
        else:
            self.chemical_elements = {}
            self.element_reverse_map = {}

    def _apply_ui_settings(self):
        if hasattr(self, 'unsaved_indicator') and not self.settings.get('ui', 'show_unsaved_indicator'):
            self.unsaved_indicator.configure(text="")

    def _on_closing(self):
        """Handle application closing"""
        self._is_closing = True  # Set flag first

        if hasattr(self, 'data_hub') and self.data_hub.has_unsaved_changes():
            response = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes.\n\nYes: Save now\nNo: Exit without saving\nCancel: Stay"
            )
            if response is None:
                self._is_closing = False  # Reset flag if staying
                return
            elif response:
                if not self.project_manager.save_project():
                    self._is_closing = False  # Reset flag if save cancelled
                    return

        # Stop auto-save if it exists
        if hasattr(self, 'auto_save') and self.auto_save:
            self.auto_save.stop()

        # Destroy the window
        self.root.destroy()

    def _open_settings(self):
        dialog = SettingsDialog(self.root, self.settings)
        self.root.wait_window(dialog.window)
        self._reapply_settings()

    def _reapply_settings(self):
        # Recent files — always exists, just sync the max count
        if hasattr(self, 'recent_files'):
            self.recent_files.max_recent = self.settings.get('recent_files', 'max_files')

        # Auto-save — create or destroy the manager object
        if self.settings.get('auto_save', 'enabled'):
            if not self.auto_save:
                self.auto_save = AutoSaveManager(
                    self, auto_save_interval=self.settings.get('auto_save', 'interval')
                )
            else:
                self.auto_save.auto_save_interval = self.settings.get('auto_save', 'interval')
        else:
            if self.auto_save:
                self.auto_save.stop()
                self.auto_save = None

        # Macro recorder — create or destroy the recorder object
        if self.settings.get('macro_recorder', 'enabled'):
            if not self.macro_recorder:
                self.macro_recorder = MacroRecorder(self)
        else:
            self.macro_recorder = None

        # Script exporter — create or destroy, then rewire the menu command
        if self.settings.get('script_exporter', 'enabled'):
            if not self.script_exporter:
                self.script_exporter = ScriptExporter(self)
        else:
            self.script_exporter = None
        try:
            cmd = (self.script_exporter.export_current_workflow if self.script_exporter
                   else lambda: messagebox.showinfo("Feature Disabled", "Script Exporter is disabled in Settings"))
            self.file_menu.entryconfig("🐍 Export to Python/R Script", command=cmd)
        except Exception:
            pass

        # Tooltips
        if self.settings.get('tooltips', 'enabled'):
            self.root.after(500, self._add_tooltips_to_panels)
        else:
            self.tooltip_manager.clear_all()

        # Sync all menu states
        self._update_macro_menu_state()

    def _update_macro_menu_state(self):
        if not hasattr(self, 'workflow_menu'):
            return
        state = tk.NORMAL if self.settings.get('macro_recorder', 'enabled') else tk.DISABLED
        try:
            self.workflow_menu.entryconfig(0, state=state)
            self.workflow_menu.entryconfig(1, state=state)
            self.workflow_menu.entryconfig(3, state=state)
        except:
            pass

    # ── FIELD ORDER AND ICONS ─────────────────────────────────────────
    # Canonical list — determines submenu order under Advanced.
    # Only fields that have at least one enabled plugin appear in the menu.
    _FIELD_ORDER = [
        "Geology & Geochemistry",
        "Geochronology & Dating",
        "Petrology & Mineralogy",
        "Structural Geology",
        "Geophysics",
        "GIS & Spatial Science",
        "Archaeology & Archaeometry",
        "Zooarchaeology",
        "Spectroscopy",
        "Chromatography & Analytical Chemistry",
        "Electrochemistry",
        "Materials Science",
        "Thermal Analysis",
        "Solution Chemistry",
        "Molecular Biology & Clinical Diagnostics",
        "Meteorology & Environmental Science",
        "Physics & Test/Measurement",
        "General",
    ]

    _FIELD_ICONS = {
        "Geology & Geochemistry":                   "🪨",
        "Geochronology & Dating":                   "⏳",
        "Petrology & Mineralogy":                   "🔥",
        "Structural Geology":                       "📐",
        "Geophysics":                               "🌍",
        "GIS & Spatial Science":                    "🗺️",
        "Archaeology & Archaeometry":               "🏺",
        "Zooarchaeology":                           "🦴",
        "Spectroscopy":                             "🔬",
        "Chromatography & Analytical Chemistry":    "⚗️",
        "Electrochemistry":                         "⚡",
        "Materials Science":                        "🧱",
        "Thermal Analysis":                         "🌡️",
        "Solution Chemistry":                       "💧",
        "Molecular Biology & Clinical Diagnostics": "🧬",
        "Meteorology & Environmental Science":      "🌤️",
        "Physics & Test/Measurement":               "📡",
        "General":                                  "📦",
    }

    def _get_plugin_category(self, plugin_info):
        """
        Resolve the scientific field for a plugin, used as the Advanced submenu name.

        Priority:
          1. PLUGIN_INFO['field']      — new plugins declare their field explicitly
          2. PLUGIN_INFO['menu_category'] — legacy key, kept for backward compat
          3. Keyword matching on name/description/id — catches all old plugins
          4. 'General'                 — final fallback
        """
        # 1. Explicit field (new-style plugins)
        if plugin_info.get('field'):
            return plugin_info['field']

        # 2. Legacy menu_category key (backward compat)
        if plugin_info.get('menu_category'):
            return plugin_info['menu_category']

        # 3. Keyword matching — covers all existing plugins without 'field'
        search_text = " ".join([
            plugin_info.get('name', '').lower(),
            plugin_info.get('description', '').lower(),
            plugin_info.get('id', '').lower()
        ])
        categories = [
            ("Geology & Geochemistry", [
                'geochem', 'normalization', 'normative', 'element', 'trace',
                'major', 'oxide', 'icp', 'xrf', 'pxrf', 'hg mobility', 'ague',
                'compositional', 'geochemical explorer',
            ]),
            ("Geochronology & Dating", [
                'dating', 'geochronology', 'radiometric', 'u-pb', 'concordia',
                'laicpms', 'la-icp', 'isotope mixing', 'geochronology',
            ]),
            ("Petrology & Mineralogy", [
                'petrology', 'petrogenetic', 'magma', 'mineral', 'thin section',
                'microscopy', 'thermobarom', 'cipw', 'niggli', 'rock',
            ]),
            ("Structural Geology", [
                'structural', 'stereonet', 'rose diagram',
            ]),
            ("Geophysics", [
                'geophysics', 'seismic', 'gravity', 'magnetics', 'ert',
                'electromagnetic',
            ]),
            ("GIS & Spatial Science", [
                'gis', 'spatial', 'kriging', 'google earth', 'quartz gis',
                '3d viewer', 'contouring',
            ]),
            ("Archaeology & Archaeometry", [
                'archaeo', 'lithic', 'museum', 'excavation', 'report generator',
                'morphometrics',
            ]),
            ("Zooarchaeology", [
                'zooarch', 'nisp', 'mni', 'taphon', 'faunal', 'bone',
            ]),
            ("Spectroscopy", [
                'spectroscopy', 'spectral', 'ftir', 'raman', 'uv-vis',
            ]),
            ("Chromatography & Analytical Chemistry", [
                'chromatography', 'hplc', 'gc-ms', 'kovats', 'peak integration', 'nmr',
            ]),
            ("Electrochemistry", [
                'electrochemistry', 'cyclic voltamm', 'eis', 'tafel', 'battery', 'rde',
            ]),
            ("Materials Science", [
                'materials', 'nanoindent', 'bet surface', 'dls', 'rheology', 'tensile',
            ]),
            ("Thermal Analysis", [
                'thermal analysis', 'dsc', 'tga', 'dma', 'calorimetry', 'lfa',
            ]),
            ("Solution Chemistry", [
                'solution chemistry', 'speciation', 'piper', 'stiff', 'wqi', 'water quality',
            ]),
            ("Molecular Biology & Clinical Diagnostics", [
                'molecular biology', 'qpcr', 'elisa', 'flow cytometry', 'pcr', 'clinical',
            ]),
            ("Meteorology & Environmental Science", [
                'meteorology', 'weather', 'aqi', 'wind rose', 'solar radiation',
                'evapotranspiration',
            ]),
            ("Physics & Test/Measurement", [
                'physics', 'oscilloscope', 'dmm', 'function generator', 'lcr',
                'test measurement',
            ]),
        ]
        for name, keywords in categories:
            if any(k in search_text for k in keywords):
                return name

        # 4. Final fallback
        return 'General'

    def _rebuild_advanced_menu(self):
        """
        Rebuild the Advanced menu grouping enabled software plugins by scientific field.
        Only creates submenus for fields that actually have plugins.
        Source badge: ☁️ for store-downloaded, 🖥 for local.
        """
        self.advanced_menu.delete(0, tk.END)

        if not self._loaded_plugin_info:
            self.advanced_menu.add_command(label="No plugins loaded", state=tk.DISABLED)
            return

        # Load downloaded set for source badge
        downloaded: set = set()
        dl_file = Path("config/downloaded_plugins.json")
        if dl_file.exists():
            try:
                with open(dl_file) as f:
                    downloaded = set(json.load(f))
            except Exception:
                pass

        # Group plugins by field
        by_field = defaultdict(list)
        for pid, info in self._loaded_plugin_info.items():
            field = info.get('field', 'General')
            by_field[field].append(info)

        # Build submenus in canonical order; any unknown fields go at the end
        ordered = [f for f in self._FIELD_ORDER if f in by_field]
        extras  = sorted(f for f in by_field if f not in self._FIELD_ORDER)

        for field in ordered + extras:
            plugins = sorted(by_field[field], key=lambda x: x['name'].lower())
            icon    = self._FIELD_ICONS.get(field, "📦")
            sub     = tk.Menu(self.advanced_menu, tearoff=0)

            for info in plugins:
                pid          = info['id']
                badge        = "☁️" if pid in downloaded else "🖥"
                plugin_icon  = info.get('icon', '🔧')
                label        = f"{badge} {plugin_icon} {info['name']}"
                sub.add_command(label=label, command=info['command'])

            self.advanced_menu.add_cascade(label=f"{icon}  {field}", menu=sub)

        self.advanced_menu.add_separator()
        self.advanced_menu.add_command(
            label="🔄 Refresh", command=self._rebuild_advanced_menu)

    def _load_enabled_plugins(self):
        f = Path("config/enabled_plugins.json")
        if f.exists():
            try:
                with open(f) as fh:
                    return json.load(fh)
            except:
                pass
        return {}

    def validate_plugin_data(self, data_rows):
        if not data_rows:
            return []
        filtered = []
        for row in data_rows:
            if hasattr(self.left, 'normalize_column_name') and hasattr(self.left, 'column_mappings'):
                clean_row = {}
                notes_parts = []
                seen = set()
                for k, v in row.items():
                    if not k or not k.strip():
                        continue
                    nk = self.left.normalize_column_name(k, self.left.column_mappings)
                    cv = str(v).strip() if v else ''
                    if nk == 'Sample_ID' and nk not in seen:
                        clean_row[nk] = cv
                        seen.add(nk)
                    elif nk in self.left.column_mappings.values() and nk not in seen:
                        try:
                            clean_row[nk] = float(cv.replace(',', ''))
                        except ValueError:
                            clean_row[nk] = cv
                        seen.add(nk)
                    else:
                        notes_parts.append(f"{k}: {cv}")
                if notes_parts:
                    clean_row['Notes'] = ' | '.join(notes_parts)
                if clean_row:
                    filtered.append(clean_row)
            else:
                filtered.append(row)
        return filtered

    def import_data_from_plugin(self, data_rows):
        if not data_rows:
            return
        filtered = self.validate_plugin_data(data_rows)
        if filtered:
            self.data_hub.add_samples(filtered)
            self.samples = self.data_hub.get_all()

    def _create_menu_structure(self):
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)
        self.advanced_menu = tk.Menu(self.menu_bar, tearoff=0)

        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="🆕 New Project (Ctrl+N)", command=self.project_manager.new_project, accelerator="Ctrl+N")
        self.file_menu.add_command(label="💾 Save Project (Ctrl+S)", command=self.project_manager.save_project, accelerator="Ctrl+S")
        self.file_menu.add_command(label="📂 Open Project (Ctrl+O)", command=self.project_manager.load_project, accelerator="Ctrl+O")
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Import CSV... (Ctrl+I)", command=lambda: self._import_with_macro(), accelerator="Ctrl+I")
        self.file_menu.add_command(label="Import Excel...", command=lambda: self._import_with_macro())
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Export CSV... (Ctrl+E)", command=self._export_csv, accelerator="Ctrl+E")
        self.file_menu.add_command(label="🐍 Export to Python/R Script",
            command=lambda: self.script_exporter.export_current_workflow() if self.script_exporter
            else lambda: messagebox.showinfo("Feature Disabled", "Script Exporter is disabled in Settings"))
        self.file_menu.add_separator()
        self.recent_menu = tk.Menu(self.file_menu, tearoff=0)
        self.file_menu.add_cascade(label="📜 Recent Files", menu=self.recent_menu)
        self._update_recent_files_menu()
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit (Ctrl+Q)", command=self._on_closing, accelerator="Ctrl+Q")

        self.edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Edit", menu=self.edit_menu)
        self.edit_menu.add_command(label="Delete Selected (Del)", command=self._delete_selected, accelerator="Del")
        self.edit_menu.add_command(label="Select All (Ctrl+A)", command=self._select_all, accelerator="Ctrl+A")
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Find... (Ctrl+F)", command=self._focus_search, accelerator="Ctrl+F")

        self.workflow_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Workflow", menu=self.workflow_menu)
        macro_state = tk.NORMAL if self.settings.get('macro_recorder', 'enabled') else tk.DISABLED
        self.workflow_menu.add_command(label="🔴 Start Recording (Ctrl+R)", command=self._start_macro_recording, accelerator="Ctrl+R", state=macro_state)
        self.workflow_menu.add_command(label="⏸️ Stop Recording (Ctrl+T)", command=self._stop_macro_recording, accelerator="Ctrl+T", state=macro_state)
        self.workflow_menu.add_separator()
        self.workflow_menu.add_command(label="📋 Manage Macros (Ctrl+M)", command=self._open_macro_manager, accelerator="Ctrl+M", state=macro_state)

        self.tools_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Tools", menu=self.tools_menu)
        self.tools_menu.add_command(label="Plugin Manager", command=self._open_plugin_manager)
        self.tools_menu.add_separator()
        self.engine_menu = tk.Menu(self.tools_menu, tearoff=0)
        self.tools_menu.add_cascade(label="🔧 Switch Engine", menu=self.engine_menu)
        self.tools_menu.add_separator()
        self.tools_menu.add_command(label="⚙️ Settings", command=self._open_settings)

        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.help_menu.add_command(label="Allowed Columns", command=self.show_allowed_columns)
        self.help_menu.add_command(label="⌨️ Keyboard Shortcuts", command=self._show_keyboard_shortcuts)
        self.help_menu.add_separator()
        self.help_menu.add_command(label="⚠️ Disclaimer", command=self.show_disclaimer)
        self.help_menu.add_command(label="About", command=self.show_about)
        self.help_menu.add_command(label="🔄 Check for Updates", command=self._check_for_updates)
        self.help_menu.add_separator()
        self.help_menu.add_command(label="❤️ Support the Project", command=self.show_support)

        self._setup_keyboard_shortcuts()

    def _check_for_updates(self):
        from features.update_checker import HTTPUpdateChecker
        HTTPUpdateChecker(self, local_version=APP_INFO["version"]).check()

    def _export_csv(self):
        samples = self.data_hub.get_all()
        if not samples:
            messagebox.showwarning("No Data", "No data to export")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not path:
            return
        try:
            if self.macro_recorder:
                self.macro_recorder.record_action('export_csv', filepath=path)
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.data_hub.get_column_names())
                writer.writeheader()
                writer.writerows(samples)
            self.data_hub.mark_saved()
            messagebox.showinfo("Success", f"Exported {len(samples)} rows to {path}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def _open_plugin_manager(self):
        self.center.set_status("Opening Plugin Manager...", "processing")
        try:
            from plugins.plugin_manager import PluginManager
            pm = PluginManager(self)
            pm.protocol("WM_DELETE_WINDOW", lambda: (pm.destroy(), self.center.set_status("Ready")))
        except ImportError as e:
            self.center.set_status("Plugin Manager not found", "error")
            messagebox.showerror("Error", f"Plugin Manager not found: {e}")

    def _create_panels(self):
        self.main = ttk.Frame(self.root)
        self.main.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.main_pane = ttk.Panedwindow(self.main, orient=tk.HORIZONTAL)
        self.main_pane.pack(fill=tk.BOTH, expand=True)

        self.left = LeftPanel(self.main_pane, self)
        self.main_pane.add(self.left.frame, weight=2)

        self.center = CenterPanel(self.main_pane, self)
        self.main_pane.add(self.center.frame, weight=8)

        self.right = RightPanel(self.main_pane, self)
        self.main_pane.add(self.right.frame, weight=1)

    def _toggle_select_all(self):
        total = self.data_hub.row_count()
        all_selected = len(self.center.selected_rows) == total and total > 0
        if all_selected:
            self.center.deselect_all()
            self.select_toggle_btn.configure(text="Select All")
        else:
            self.center.select_all()
            self.select_toggle_btn.configure(text="Deselect All")

    def _delete_selected(self):
        selected = self.center.get_selected_indices()
        if selected and messagebox.askyesno("Confirm", f"Delete {len(selected)} selected row(s)?"):
            self.data_hub.delete_rows(selected)
            self.samples = self.data_hub.get_all()
            if hasattr(self, 'select_toggle_btn'):
                self.select_toggle_btn.configure(text="Select All")

    def auto_size_columns(self, tree, samples, force=False):
        if not samples or not tree.get_children():
            return
        for col in tree["columns"]:
            if col == "☐":
                tree.column(col, width=30)
                continue
            max_width = len(str(col)) * 8
            for item in list(tree.get_children())[:50]:
                values = tree.item(item, "values")
                idx = list(tree["columns"]).index(col)
                if idx < len(values):
                    max_width = max(max_width, len(str(values[idx])) * 7)
            tree.column(col, width=min(max(80, max_width), 300))

    def _build_bottom_controls(self):
        bottom = ttk.Frame(self.root, bootstyle="dark")
        bottom.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=(0, 5))

        nav = ttk.Frame(bottom, bootstyle="dark")
        nav.pack(side=tk.LEFT, padx=6, pady=4)

        self.prev_btn = ttk.Button(nav, text="◀ Prev", command=self.center.prev_page,
                                   bootstyle="secondary-outline", width=8)
        self.prev_btn.pack(side=tk.LEFT, padx=2)

        self.page_label = ttk.Label(nav, text="Page 1 of 1", bootstyle="light", width=12)
        self.page_label.pack(side=tk.LEFT, padx=8)

        self.next_btn = ttk.Button(nav, text="Next ▶", command=self.center.next_page,
                                   bootstyle="secondary-outline", width=8)
        self.next_btn.pack(side=tk.LEFT, padx=2)

        self.total_label = ttk.Label(nav, text="Total: 0 rows", bootstyle="light", width=14)
        self.total_label.pack(side=tk.LEFT, padx=10)

        status_frame = ttk.Frame(bottom, bootstyle="dark")
        status_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=4)

        self.status_label = ttk.Label(
            status_frame, textvariable=self.center.status_var,
            anchor=tk.W, cursor="hand2", bootstyle="light"
        )
        self.status_label.pack(fill=tk.X, padx=4, pady=2)
        self.status_label.bind("<Button-1>", lambda e: self._show_status_details())

        sel = ttk.Frame(bottom, bootstyle="dark")
        sel.pack(side=tk.RIGHT, padx=6, pady=4)

        self.unsaved_indicator = ttk.Label(sel, text="", bootstyle="danger", width=2)
        self.unsaved_indicator.pack(side=tk.LEFT, padx=2)

        self.select_toggle_btn = ttk.Button(
            sel, text="Select All", command=self._toggle_select_all,
            bootstyle="primary", width=10
        )
        self.select_toggle_btn.pack(side=tk.LEFT, padx=3)

        ttk.Button(
            sel, text="🗑️ Delete", command=self._delete_selected,
            bootstyle="danger", width=8
        ).pack(side=tk.LEFT, padx=3)

        self.sel_label = ttk.Label(sel, text="Selected: 0", bootstyle="light", width=12)
        self.sel_label.pack(side=tk.LEFT, padx=8)

        self._check_unsaved_changes()

    def _check_unsaved_changes(self):
        """Check for unsaved changes and update indicator"""
        # Don't schedule next check if we're closing
        if self._is_closing:
            return

        if hasattr(self, 'data_hub') and hasattr(self, 'unsaved_indicator'):
            if self.data_hub.has_unsaved_changes():
                self.unsaved_indicator.configure(text="●", bootstyle="danger")
            else:
                self.unsaved_indicator.configure(text="○", bootstyle="secondary")

        # Only schedule next check if we're not closing
        if not self._is_closing:
            self.root.after(2000, self._check_unsaved_changes)

    def _show_status_details(self):
        if not hasattr(self.center, 'last_operation'):
            return
        op = self.center.last_operation
        t = op.get('type')
        if t == 'plugin_fetch':
            messagebox.showinfo("Plugin Fetch Details", op.get('warning', 'No details'))
        elif t == 'update_error':
            messagebox.showerror("Update Error", op.get('error', 'Unknown error'))
        elif t == 'update_available':
            if messagebox.askyesno("Update Available",
                f"Version {op['new_version']} is available.\n\nDownload now?"):
                self._check_for_updates()
        elif t == 'app_update':
            from features.update_checker import HTTPUpdateChecker
            HTTPUpdateChecker(self, local_version=APP_INFO["version"]).show_update_dialog(
                changed_files=op['changed'], new_commit=op['new_commit'], new_version=op['new_version'])
        else:
            current = self.center.status_var.get()
            if current and current != "Ready":
                messagebox.showinfo("Status", current)

    def update_pagination(self, current_page, total_pages, total_rows):
        self.current_page = current_page
        self.total_pages = total_pages
        self.page_label.configure(text=f"Page {current_page + 1} of {total_pages}")
        self.total_label.configure(text=f"Total: {total_rows} rows")
        self.prev_btn.configure(state=tk.NORMAL if current_page > 0 else tk.DISABLED)
        self.next_btn.configure(state=tk.NORMAL if current_page < total_pages - 1 else tk.DISABLED)

    def update_selection(self, count):
        self.sel_label.configure(text=f"Selected: {count}")
        if hasattr(self, 'select_toggle_btn'):
            total = self.data_hub.row_count()
            self.select_toggle_btn.configure(
                text="Deselect All" if count == total and total > 0 else "Select All")

    def _refresh_engine_menu(self):
        self.engine_menu.delete(0, tk.END)
        engines = self.engine_manager.get_available_engines()
        if not engines:
            self.engine_menu.add_command(label="No engines found", state="disabled")
            return
        for name in sorted(engines):
            self.engine_menu.add_command(
                label=f"{'✓ ' if name == self.current_engine_name else '  '}{name.capitalize()} Engine",
                command=lambda e=name: self._switch_engine(e)
            )
        self.engine_menu.add_separator()
        self.engine_menu.add_command(label="⟲ Refresh", command=self._refresh_engine_menu)

    def _switch_engine(self, engine_name):
        try:
            engine = self.engine_manager.load_engine(engine_name)
            if engine:
                self.classification_engine = engine
                self.current_engine = engine
                self.current_engine_name = engine_name
                if engine_name == 'protocol':
                    self.protocol_engine = engine
                if hasattr(self, 'right'):
                    self.right.refresh_for_engine(engine_name)
                self._refresh_engine_menu()
            else:
                messagebox.showerror("Error", f"Failed to load {engine_name} engine")
        except Exception as e:
            messagebox.showerror("Error", f"Engine switch failed: {e}")

    def _load_plugins(self):
        config_file = Path("config/enabled_plugins.json")
        if config_file.exists():
            try:
                with open(config_file) as f:
                    self.enabled_plugins = json.load(f)
            except:
                self.enabled_plugins = {}

        hw_dir = Path("plugins/hardware")
        if hasattr(self, 'left') and hasattr(self.left, 'remove_hardware_button'):
            for pid, entry in list(self.hardware_plugins.items()):
                info = entry.get('info', {})
                self.left.remove_hardware_button(name=info.get('name', pid), icon=info.get('icon', '🔌'))
        self.hardware_plugins = {}

        if hw_dir.exists():
            for py_file in hw_dir.glob("*.py"):
                if py_file.stem in ["__init__", "plugin_manager"]:
                    continue
                plugin_id = py_file.stem
                if not self.enabled_plugins.get(plugin_id, False):
                    continue
                try:
                    spec = importlib.util.spec_from_file_location(plugin_id, py_file)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    if hasattr(module, 'PLUGIN_INFO'):
                        info = module.PLUGIN_INFO
                        inst = None
                        if hasattr(module, 'register_plugin'):
                            inst = module.register_plugin(self)
                        elif hasattr(module, 'setup_plugin'):
                            inst = module.setup_plugin(self)
                        if inst:
                            self.hardware_plugins[plugin_id] = {'instance': inst, 'info': info, 'file': py_file}
                            if hasattr(self, 'left'):
                                self.left.add_hardware_button(
                                    name=info.get('name', plugin_id),
                                    icon=info.get('icon', '🔌'),
                                    command=inst.open_window
                                )
                except Exception as e:
                    pass

        software_dirs = [Path("plugins/software"), Path("plugins/add-ons")]
        software_loaded = False

        for software_dir in software_dirs:
            if not software_dir.exists():
                continue
            for py_file in software_dir.glob("*.py"):
                if py_file.stem in ["__init__", "plugin_manager"]:
                    continue
                plugin_id = py_file.stem
                if not self.enabled_plugins.get(plugin_id, False):
                    continue
                try:
                    spec = importlib.util.spec_from_file_location(plugin_id, py_file)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    if hasattr(module, 'PLOT_TYPES') and isinstance(module.PLOT_TYPES, dict):
                        for name, func in module.PLOT_TYPES.items():
                            if name not in [p[0] for p in self.plot_plugin_types]:
                                self.plot_plugin_types.append((name, func))
                    if hasattr(module, 'PLUGIN_INFO'):
                        info = module.PLUGIN_INFO
                        inst = None
                        if hasattr(module, 'register_plugin'):
                            inst = module.register_plugin(self)
                        elif hasattr(module, 'setup_plugin'):
                            inst = module.setup_plugin(self)
                        if inst:
                            software_loaded = True
                            if hasattr(inst, 'create_tab'):
                                if 'console' not in info.get('category', '') and 'console' not in plugin_id:
                                    if hasattr(self.center, 'add_tab_plugin'):
                                        self.center.add_tab_plugin(plugin_id, info.get('name', plugin_id), info.get('icon', '🔧'), inst)
                                    continue
                            if plugin_id not in self._added_plugins:
                                self._add_to_advanced_menu(info, inst)
                                self._added_plugins.add(plugin_id)
                            plugin_name = info.get('name', '').lower()
                            plugin_desc = info.get('description', '').lower()
                            ai_kw = ['ai','assistant','chat','gemini','claude','grok','deepseek','ollama','copilot','chatgpt']
                            if any(kw in plugin_name or kw in plugin_id.lower() or kw in plugin_desc for kw in ai_kw):
                                if hasattr(inst, 'query') and hasattr(self.center, 'add_ai_plugin'):
                                    self.center.add_ai_plugin(plugin_name=info.get('name', plugin_id),
                                                               plugin_icon=info.get('icon', '🤖'),
                                                               plugin_instance=inst)
                except Exception as e:
                    pass

        if self.plot_plugin_types:
            self.center.update_plot_types(self.plot_plugin_types)

        tools_index = help_index = None
        advanced_exists = help_exists = False
        try:
            for i in range(self.menu_bar.index("end") + 1):
                try:
                    label = self.menu_bar.entrycget(i, "label")
                    if label == "Tools":     tools_index = i
                    elif label == "Help":    help_exists = True; help_index = i
                    elif label == "Advanced": advanced_exists = True
                except: pass
        except: pass

        if software_loaded and self._loaded_plugin_info:
            self._rebuild_advanced_menu()
            if not advanced_exists:
                if tools_index is not None:
                    self.menu_bar.insert_cascade(tools_index + 1, label="Advanced", menu=self.advanced_menu)
                elif help_exists:
                    self.menu_bar.insert_cascade(help_index, label="Advanced", menu=self.advanced_menu)
                else:
                    self.menu_bar.add_cascade(label="Advanced", menu=self.advanced_menu)

        if not help_exists:
            self.menu_bar.add_cascade(label="Help", menu=self.help_menu)

    def _add_to_advanced_menu(self, info, inst):
        """
        Register a plugin for the Advanced menu.
        Resolves its scientific field via _get_plugin_category which reads:
          PLUGIN_INFO['field'] first, then 'menu_category', then keyword matching.
        Old plugins without any of those keys still land in the right submenu.
        """
        plugin_id = info.get('id', '')
        if plugin_id in self._added_plugins:
            return
        open_method = getattr(inst, 'open_window', None) or getattr(inst, 'show_interface', None)
        if open_method:
            field = self._get_plugin_category(info)
            self._loaded_plugin_info[plugin_id] = {
                'name':        info.get('name', 'Unknown'),
                'icon':        info.get('icon', '🔧'),
                'command':     open_method,
                'id':          plugin_id,
                'description': info.get('description', ''),
                'field':       field,
            }
            self._added_plugins.add(plugin_id)

    def _setup_keyboard_shortcuts(self):
        self.root.bind('<Control-n>', lambda e: self.project_manager.new_project())
        self.root.bind('<Control-o>', lambda e: self.project_manager.load_project())
        self.root.bind('<Control-s>', lambda e: self.project_manager.save_project())
        self.root.bind('<Control-i>', lambda e: self._import_with_macro())
        self.root.bind('<Control-e>', lambda e: self._export_csv())
        self.root.bind('<Control-q>', lambda e: self._on_closing())
        self.root.bind('<Delete>', lambda e: self._delete_selected())
        self.root.bind('<Control-a>', lambda e: self._select_all())
        self.root.bind('<Control-f>', lambda e: self._focus_search())
        if self.macro_recorder:
            self.root.bind('<Control-r>', lambda e: self._start_macro_recording())
            self.root.bind('<Control-t>', lambda e: self._stop_macro_recording())
            self.root.bind('<Control-m>', lambda e: self._open_macro_manager())
        self.root.bind('<F1>', lambda e: self._show_keyboard_shortcuts())
        self.root.bind('<F5>', lambda e: self._refresh_all())

    def _import_with_macro(self):
        filepath = filedialog.askopenfilename(filetypes=[
            ("All supported files", "*.csv *.xlsx *.xls"),
            ("CSV files", "*.csv"), ("Excel files", "*.xlsx *.xls"), ("All files", "*.*")
        ])
        if filepath:
            if self.macro_recorder:
                self.macro_recorder.record_action('import_file', filepath=filepath)
            self.recent_files.add(filepath)
            self._update_recent_files_menu()
            self.left.import_csv(filepath)

    def _update_recent_files_menu(self):
        self.recent_menu.delete(0, tk.END)
        items = self.recent_files.get_menu_items()
        if items:
            for item in items:
                self.recent_menu.add_command(label=item['label'],
                    command=lambda p=item['path']: self._open_recent_file(p))
            self.recent_menu.add_separator()
            self.recent_menu.add_command(label="Clear Recent Files", command=self._clear_recent_files)
        else:
            self.recent_menu.add_command(label="(No recent files)", state=tk.DISABLED)

    def _open_recent_file(self, filepath):
        if self.macro_recorder:
            self.macro_recorder.record_action('import_file', filepath=filepath)
        self.left.import_csv(filepath)

    def _clear_recent_files(self):
        if messagebox.askyesno("Clear Recent Files", "Clear all recent files?"):
            self.recent_files.clear()
            self._update_recent_files_menu()

    def _select_all(self):
        if hasattr(self, 'center') and hasattr(self.center, 'tree'):
            for item in self.center.tree.get_children():
                self.center.tree.selection_add(item)

    def _focus_search(self):
        if hasattr(self, 'center') and hasattr(self.center, 'search_entry'):
            self.center.search_entry.focus_set()

    def _refresh_all(self):
        self.data_hub.notify_observers()

    def _start_macro_recording(self):
        if not self.settings.get('macro_recorder', 'enabled') or not self.macro_recorder:
            messagebox.showinfo("Feature Disabled", "Macro Recorder is disabled.")
            return
        self.macro_recorder.start_recording()
        self.workflow_menu.entryconfig(0, label="🔴 Recording... (Ctrl+T to stop)")
        messagebox.showinfo("Recording", "Macro recording started!")

    def _stop_macro_recording(self):
        if not self.macro_recorder or not self.macro_recorder.is_recording:
            messagebox.showwarning("Not Recording", "No macro is currently being recorded")
            return
        macro = self.macro_recorder.stop_recording()
        self.workflow_menu.entryconfig(0, label="🔴 Start Recording (Ctrl+R)")
        if not macro:
            messagebox.showinfo("Empty Macro", "No actions were recorded")
            return
        dialog = ttk.Toplevel(self.root)
        dialog.title("Save Macro")
        dialog.geometry("400x160")
        dialog.transient(self.root)
        ttk.Label(dialog, text="Macro Name:", bootstyle="light").pack(pady=(20, 5))
        name_var = tk.StringVar(value=f"Workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        entry = ttk.Entry(dialog, textvariable=name_var, width=40, bootstyle="light")
        entry.pack(pady=5)
        entry.focus_set()
        def save():
            name = name_var.get().strip()
            if name:
                self.macro_recorder.save_macro(name, macro)
                dialog.destroy()
        ttk.Button(dialog, text="Save", command=save, bootstyle="primary").pack(pady=8)
        dialog.bind('<Return>', lambda e: save())

    def _open_macro_manager(self):
        if not self.settings.get('macro_recorder', 'enabled') or not self.macro_recorder:
            messagebox.showinfo("Feature Disabled", "Macro Recorder is disabled.")
            return
        MacroManagerDialog(self.root, self.macro_recorder)

    def _show_keyboard_shortcuts(self):
        win = ttk.Toplevel(self.root)
        win.title("⌨️ Keyboard Shortcuts")
        win.geometry("520x580")
        ttk.Label(win, text="Keyboard Shortcuts",
                  font=("Segoe UI", 14, "bold"), bootstyle="light").pack(pady=(20, 10))
        from tkinter.scrolledtext import ScrolledText
        text = ScrolledText(win, wrap=tk.WORD, font=("Courier", 10),
                            relief=tk.FLAT, bd=0)
        text.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        text.insert(tk.END, """
FILE OPERATIONS
═══════════════════════════════════════════════════
Ctrl+N          New Project
Ctrl+O          Open Project
Ctrl+S          Save Project
Ctrl+I          Import Data
Ctrl+E          Export CSV
Ctrl+Q          Quit

EDIT OPERATIONS
═══════════════════════════════════════════════════
Delete          Delete Selected Rows
Ctrl+A          Select All
Ctrl+F          Find/Search

WORKFLOW/MACROS
═══════════════════════════════════════════════════
Ctrl+R          Start Recording Macro
Ctrl+T          Stop Recording Macro
Ctrl+M          Manage Macros

OTHER
═══════════════════════════════════════════════════
F1              Show This Help
F5              Refresh All Panels

MOUSE
═══════════════════════════════════════════════════
Double-Click    Show Sample Details
Right-Click     Context Menu (Edit, Copy, Delete)
        """.strip())
        text.configure(state=tk.DISABLED)
        ttk.Button(win, text="Close", command=win.destroy, bootstyle="secondary").pack(pady=12)

    def _add_tooltips_to_panels(self):
        if not hasattr(self, 'tooltip_manager'):
            return
        if hasattr(self, 'left'):
            if hasattr(self.left, 'import_btn'):
                self.tooltip_manager.add(self.left.import_btn, "Import data from CSV or Excel files")
            if hasattr(self.left, 'add_btn'):
                self.tooltip_manager.add(self.left.add_btn, "Add a new sample manually")
        if hasattr(self, 'center') and hasattr(self.center, 'plot_btn'):
            self.tooltip_manager.add(self.center.plot_btn, "Generate visualization")
        if hasattr(self, 'right') and hasattr(self.right, 'apply_btn'):
            self.tooltip_manager.add(self.right.apply_btn, "Apply selected classification scheme")

    def show_allowed_columns(self):
        from tkinter.scrolledtext import ScrolledText
        win = ttk.Toplevel(self.root)
        win.title("🔬 Standardized Columns")
        win.geometry("620x520")
        text = ScrolledText(win, wrap=tk.WORD, font=("Courier", 10), relief=tk.FLAT)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text.insert(tk.END, "STANDARDIZED COLUMN NAMES\n" + "="*50 + "\n\nSource: chemical_elements.json\n\n")
        for group_name, columns in getattr(self, 'ui_groups', {}).items():
            text.insert(tk.END, f"\n{group_name}:\n" + "-"*30 + "\n")
            for col in sorted(columns):
                display = col
                for info in self.chemical_elements.values():
                    if info["standard"] == col:
                        display = info.get("display_name", col)
                        break
                text.insert(tk.END, f"  • {display}\n")
        text.configure(state=tk.DISABLED)

    def show_disclaimer(self):
        win = ttk.Toplevel(self.root)
        win.title("⚠️ Important Disclaimer")
        win.transient(self.root)
        frm = ttk.Frame(win, padding=20)
        frm.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frm, text="⚠️", font=("Segoe UI", 40), bootstyle="warning").pack()
        ttk.Label(frm, text="IMPORTANT DISCLAIMER",
                  font=("Segoe UI", 14, "bold"), bootstyle="warning").pack(pady=8)
        style = ttk.Style.get_instance()
        _bg = style.colors.get('dark') if hasattr(style, 'colors') else "#2b2b2b"
        _fg = style.colors.get('light') if hasattr(style, 'colors') else "#dddddd"
        text = tk.Text(frm, wrap=tk.WORD, font=("Segoe UI", 10), height=14, width=60,
                       bg=_bg, fg=_fg, relief=tk.FLAT, padx=10, pady=10)
        text.pack(fill=tk.BOTH, expand=True)
        text.insert("1.0", (
            "This software is intended for RESEARCH and EDUCATIONAL use only.\n\n"
            "• Automated classifications are based on published scientific thresholds.\n\n"
            "• Results MUST be verified by qualified specialists before use in formal conclusions.\n\n"
            "• All classifications should be validated against published reference data.\n\n"
            "• This tool assists analysis — it does not replace expert judgment.\n\n"
            "• Developers assume no responsibility for conclusions without expert validation.\n\n"
            "By using this software, you acknowledge these limitations."
        ))
        text.configure(state=tk.DISABLED)
        ttk.Button(frm, text="OK", command=win.destroy,
                   bootstyle="warning-outline", width=12).pack(pady=12)
        win.update_idletasks()
        w, h = win.winfo_reqwidth() + 40, win.winfo_reqheight() + 40
        win.geometry(f"{w}x{h}+{(win.winfo_screenwidth()-w)//2}+{(win.winfo_screenheight()-h)//2}")

    def show_about(self):
        win = ttk.Toplevel(self.root)
        win.title("About Scientific Toolkit")
        win.geometry("660x680")
        win.transient(self.root)

        canvas = tk.Canvas(win, bg="#1c1c1c", highlightthickness=0)
        scrollbar = ttk.Scrollbar(win, orient="vertical", command=canvas.yview)
        frm = ttk.Frame(canvas, padding=24)

        frm.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=frm, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Label(frm, text="Scientific Toolkit v2.0",
                  font=("Segoe UI", 16, "bold"), bootstyle="light").pack(pady=(0, 3))
        ttk.Label(frm, text="(Based on Basalt Provenance Triage Toolkit v10.2)",
                  font=("Segoe UI", 9, "italic"), bootstyle="secondary").pack()
        ttk.Label(frm, text="© 2026 Sefy Levy  •  All Rights Reserved",
                  bootstyle="secondary").pack(pady=2)
        email = ttk.Label(frm, text="sefy76@gmail.com", bootstyle="info", cursor="hand2")
        email.pack()
        email.bind("<Button-1>", lambda e: webbrowser.open("mailto:sefy76@gmail.com"))
        ttk.Label(frm, text="DOI: https://doi.org/10.5281/zenodo.18727756",
                  bootstyle="info", cursor="hand2").pack()
        ttk.Label(frm, text="CC BY-NC-SA 4.0 — Non-commercial research & education use",
                  font=("Segoe UI", 9, "italic"), bootstyle="secondary").pack(pady=(6, 4))
        ttk.Label(frm, text="A unified platform for scientific data analysis with plugin architecture",
                  wraplength=580, justify="center", bootstyle="light").pack(pady=(0, 8))

        ded = ttk.LabelFrame(frm, text="Dedication", padding=16, bootstyle="secondary")
        ded.pack(pady=8, padx=20, fill=tk.X)
        ttk.Label(ded, text="Dedicated to my beloved", font=("Segoe UI", 10, "bold")).pack(pady=(0, 2))
        ttk.Label(ded, text="Camila Portes Salles",
                  font=("Segoe UI", 12, "italic"), bootstyle="danger").pack()
        ttk.Label(ded, text="Special thanks to my sister",
                  font=("Segoe UI", 9, "bold")).pack(pady=(8, 2))
        ttk.Label(ded, text="Or Levy", font=("Segoe UI", 10, "italic")).pack()
        ttk.Label(ded, text="In loving memory of my mother").pack(pady=(8, 2))
        ttk.Label(ded, text="Chaya Levy", font=("Segoe UI", 10, "italic")).pack()

        ttk.Label(frm, text="Development: Sefy Levy (2026)", bootstyle="secondary").pack(pady=(12, 2))
        ttk.Label(frm, text="Implementation with generous help from:").pack()
        ttk.Label(frm, text="Gemini • Copilot • ChatGPT • Claude • DeepSeek • Mistral • Grok",
                  font=("Segoe UI", 9, "italic"), bootstyle="secondary").pack()
        ttk.Label(frm, text="If used in research — please cite:",
                  font=("Segoe UI", 9, "bold")).pack(pady=(12, 2))
        ttk.Label(frm,
                  text="Levy, S. (2026). Scientific Toolkit v2.0.\n"
                       "Based on Basalt Provenance Triage Toolkit v10.2.\n"
                       "https://doi.org/10.5281/zenodo.18727756",
                  justify="center", bootstyle="secondary").pack()
        ttk.Button(frm, text="Close", command=win.destroy,
                   bootstyle="secondary-outline", width=12).pack(pady=(16, 0))

    def show_support(self):
        win = ttk.Toplevel(self.root)
        win.title("Support Scientific Toolkit")
        win.transient(self.root)
        frm = ttk.Frame(win, padding=25)
        frm.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frm, text="Support the Project",
                  font=("Segoe UI", 16, "bold"), bootstyle="light").pack(pady=(0, 6))
        ttk.Label(frm, text="Scientific Toolkit v2.0").pack()
        ttk.Label(frm, text="Based on Basalt Provenance Triage Toolkit v10.2",
                  font=("Segoe UI", 9, "italic"), bootstyle="secondary").pack(pady=2)
        ttk.Label(frm, text="Created by Sefy Levy • 2026").pack(pady=4)

        email_link = ttk.Label(frm, text="sefy76@gmail.com", bootstyle="info", cursor="hand2")
        email_link.pack(pady=2)
        email_link.bind("<Button-1>", lambda e: webbrowser.open("mailto:sefy76@gmail.com"))

        ttk.Label(frm, text="This tool is 100% free and open-source (CC BY-NC-SA 4.0)\nfor research and educational use.",
                  justify="center", wraplength=400, bootstyle="secondary").pack(pady=(12, 16))
        ttk.Separator(frm, bootstyle="secondary").pack(fill=tk.X, pady=10)
        ttk.Label(frm,
                  text="If this tool has saved you time, helped with your research,\n"
                       "any support is deeply appreciated.",
                  justify="center", wraplength=400).pack(pady=(0, 16))

        donate_frame = ttk.LabelFrame(frm, text="Ways to Support", padding=14, bootstyle="secondary")
        donate_frame.pack(fill=tk.X, pady=8, padx=10)

        for label, url in [
            ("☕ Ko-fi – Buy me a coffee", "https://ko-fi.com/sefy76"),
            ("💳 PayPal.me – Quick one-time donation", "https://paypal.me/sefy76"),
            ("🔁 Liberapay – Recurring (0% fee)", "https://liberapay.com/sefy76"),
        ]:
            ttk.Button(donate_frame, text=label,
                       command=lambda u=url: webbrowser.open(u),
                       bootstyle="info-outline").pack(fill=tk.X, pady=4, padx=8)

        ttk.Separator(frm, bootstyle="secondary").pack(fill=tk.X, pady=14)
        ttk.Label(frm, text="Thank you for believing in open scientific tools.",
                  font=("Segoe UI", 9, "italic"), bootstyle="secondary").pack(pady=(0, 8))
        ttk.Button(frm, text="Close", command=win.destroy,
                   bootstyle="secondary-outline").pack(pady=6)

        win.update_idletasks()
        w, h = frm.winfo_reqwidth() + 50, frm.winfo_reqheight() + 50
        win.geometry(f"{w}x{h}+{(win.winfo_screenwidth()-w)//2}+{(win.winfo_screenheight()-h)//2}")

# ============ MAIN ============
def main():
    # Run the unified dependency checker (already ran at import)
    root = ttk.Window(themename="darkly")
    root.withdraw()
    set_messagebox_parent(root)

    splash = tk.Toplevel(root)
    splash.overrideredirect(True)
    w, h = 500, 300
    ws, hs = splash.winfo_screenwidth(), splash.winfo_screenheight()
    splash.geometry(f"{w}x{h}+{(ws-w)//2}+{(hs-h)//2}")
    splash.configure(bg='#2c3e50')  # intentional branded splash color

    main_frame = tk.Frame(splash, bg='#2c3e50', padx=30, pady=30)
    main_frame.pack(fill=tk.BOTH, expand=True)

    tk.Label(main_frame, text="🔬", font=("Segoe UI", 48),
             bg='#2c3e50', fg='#3498db').pack(pady=(0, 10))
    tk.Label(main_frame, text="Scientific Toolkit",
             font=("Segoe UI", 18, "bold"),
             bg='#2c3e50', fg='white').pack()

    msg_var = tk.StringVar(value="Loading components...")
    tk.Label(main_frame, textvariable=msg_var,
             font=("Segoe UI", 10),
             bg='#2c3e50', fg='#bdc3c7').pack(pady=(0, 20))

    progress = ttk.Progressbar(main_frame, mode='determinate', length=400, bootstyle="info-striped")
    progress.pack(pady=10)

    percent_var = tk.StringVar(value="0%")
    tk.Label(main_frame, textvariable=percent_var,
             font=("Segoe UI", 10, "bold"),
             bg='#2c3e50', fg='#3498db').pack()

    tk.Label(main_frame, text="v2.0",
             font=("Segoe UI", 8),
             bg='#2c3e50', fg='#7f8c8d').pack(side=tk.BOTTOM, pady=(20, 0))

    splash.update()

    def create_app():
        steps = [
            (10, "Loading engines..."),
            (25, "Loading configuration..."),
            (55, "Building interface..."),
            (80, "Loading plugins..."),
            (95, "Finalizing..."),
            (100, "Ready!")
        ]

        for value, message in steps:
            msg_var.set(message)
            progress['value'] = value
            percent_var.set(f"{value}%")
            splash.update()

        app = ScientificToolkit(root)

        splash.after(300, lambda: (splash.destroy(), root.deiconify()))

    root.after(100, create_app)
    root.mainloop()

if __name__ == "__main__":
    main()
