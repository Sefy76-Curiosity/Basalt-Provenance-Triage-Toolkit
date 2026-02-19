#!/usr/bin/env python3
"""
Scientific Toolkit v2.0 - WITH WORKING SPLASH SCREEN AND FIXED DELETE METHOD
"""
APP_INFO = {
    "id": "scientific_toolkit",
    "name": "Scientific Toolkit",
    "version": "2.0.0",  # Current version
    "author": "Sefy Levy",
    "description": "Scientific data analysis platform",
    "min_plugins_version": "2.0",  # Optional: plugin manager compatibility
}
import engines
import engines.classification_engine
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import importlib.util
import sys, traceback
def excepthook(exc_type, exc_value, exc_traceback):
    with open('error.log', 'a') as f:
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
    sys.__excepthook__(exc_type, exc_value, exc_traceback)  # also show it normally
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

# Enhanced features (organized in features/ folder)
from features.tooltip_manager import ToolTipManager
from features.recent_files_manager import RecentFilesManager
from features.macro_recorder import MacroRecorder, MacroManagerDialog
from features.project_manager import ProjectManager
from features.script_exporter import ScriptExporter
from features.auto_save import AutoSaveManager
from features.settings_manager import SettingsManager, SettingsDialog

# ============ DEPENDENCY CHECKER ============
def check_and_install_dependencies():
    """Check for required packages and offer to install missing ones"""

    # Import needed modules for the installer
    from tkinter import scrolledtext  # <--- ADD THIS LINE
    import subprocess
    import threading

    REQUIRED_PACKAGES = [
        # ============ FILE FORMAT SUPPORT ============
        {
            'import_name': 'pandas',
            'pip_name': 'pandas',
            'reason': 'Required for Excel and LibreOffice ODS file import'
        },
        {
            'import_name': 'odf',
            'pip_name': 'odfpy',
            'reason': 'Required for LibreOffice ODS file import'
        },
        {
            'import_name': 'openpyxl',
            'pip_name': 'openpyxl',
            'reason': 'Required for modern Excel files (.xlsx)'
        },
        {
            'import_name': 'xlrd',
            'pip_name': 'xlrd',
            'reason': 'Required for older Excel files (.xls)'
        },

        # ============ DATA PROCESSING ============
        {
            'import_name': 'numpy',
            'pip_name': 'numpy',
            'reason': 'Required for numerical operations in classification engine'
        },

        # ============ VERSION COMPARISON ============
        {
            'import_name': 'packaging',
            'pip_name': 'packaging',
            'reason': 'Required for version comparison in plugin manager'
        }
    ]

    missing_packages = []

    # Check each package
    for package in REQUIRED_PACKAGES:
        try:
            __import__(package['import_name'])
            print(f"✅ Found {package['import_name']}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ Missing {package['import_name']}")

    if not missing_packages:
        return True  # All packages found

    # Create a simple Tk window for the prompt
    import subprocess
    import threading

    root = tk.Tk()
    root.withdraw()  # Hide the main window

    # Build message
    package_list = "\n".join([f"  • {p['pip_name']} - {p['reason']}" for p in missing_packages])

    message = (
        "The following required packages are missing:\n\n"
        f"{package_list}\n\n"
        "Would you like to install them now?\n\n"
        "This will run: pip install " + " ".join([p['pip_name'] for p in missing_packages])
    )

    response = messagebox.askyesno(
        "Missing Dependencies",
        message,
        parent=root
    )

    if response:
        # User wants to install - destroy the prompt window
        root.destroy()

        # Create installation window
        install_root = tk.Tk()
        install_root.title("Installing Dependencies")
        install_root.geometry("600x400")

        # Center the window
        ws = install_root.winfo_screenwidth()
        hs = install_root.winfo_screenheight()
        x = (ws//2) - (600//2)
        y = (hs//2) - (400//2)
        install_root.geometry(f"+{x}+{y}")

        # Make window non-resizable
        install_root.resizable(False, False)

        # UI elements
        tk.Label(install_root, text="📦 Installing Packages",
                font=("Segoe UI", 14, "bold")).pack(pady=20)

        status_var = tk.StringVar(value="Preparing installation...")
        tk.Label(install_root, textvariable=status_var,
                font=("Segoe UI", 10)).pack(pady=10)

        progress = ttk.Progressbar(install_root, mode='indeterminate', length=500)
        progress.pack(pady=10)
        progress.start(10)

        # Create frame for text with scrollbar
        text_frame = ttk.Frame(install_root)
        text_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        output_text = scrolledtext.ScrolledText(text_frame, height=12, width=70, font=("Courier", 9))
        output_text.pack(fill=tk.BOTH, expand=True)

        # Variable to track installation completion
        installation_complete = False

        # Function to close window properly
        def safe_close():
            if installation_complete:
                install_root.destroy()
            else:
                messagebox.showinfo("Please Wait", "Installation is still in progress. Please wait for it to complete.")

        # Add close button (initially disabled, enabled when done)
        close_btn = ttk.Button(install_root, text="Close", state=tk.DISABLED, command=safe_close)
        close_btn.pack(pady=10)

        # Function to run installation in background
        def run_installation():
            nonlocal installation_complete
            packages_to_install = [p['pip_name'] for p in missing_packages]
            all_success = True

            for i, package in enumerate(packages_to_install):
                # Update status in main thread
                install_root.after(0, lambda p=package, idx=i: status_var.set(f"Installing {p} ({idx+1}/{len(packages_to_install)})..."))
                install_root.after(0, lambda p=package: output_text.insert(tk.END, f"\nInstalling {package}...\n"))
                install_root.after(0, lambda: output_text.see(tk.END))

                try:
                    result = subprocess.run(
                        [sys.executable, "-m", "pip", "install", package],
                        capture_output=True,
                        text=True,
                        timeout=120
                    )

                    if result.returncode == 0:
                        install_root.after(0, lambda p=package: output_text.insert(tk.END, f"✅ Successfully installed {p}\n"))
                    else:
                        install_root.after(0, lambda p=package, e=result.stderr: output_text.insert(tk.END, f"❌ Failed to install {p}\nError: {e}\n"))
                        all_success = False
                except Exception as e:
                    install_root.after(0, lambda p=package, err=str(e): output_text.insert(tk.END, f"❌ Error installing {p}: {err}\n"))
                    all_success = False

                install_root.after(0, lambda: output_text.see(tk.END))

            # Installation complete - update UI
            install_root.after(0, progress.stop)

            if all_success:
                install_root.after(0, lambda: status_var.set("✅ All packages installed successfully!"))
                install_root.after(0, lambda: output_text.insert(tk.END, "\n\n✅ Installation complete! The application will now start.\n"))
                 # Auto-close after 2 seconds
                install_root.after(2000, install_root.destroy)
            else:
                install_root.after(0, lambda: status_var.set("⚠️ Some packages failed to install"))
                install_root.after(0, lambda: output_text.insert(tk.END, "\n\n⚠️ Some packages failed to install.\n"))
                install_root.after(0, lambda: output_text.insert(tk.END, "You may need to install them manually:\n"))
                install_root.after(0, lambda: output_text.insert(tk.END, f"pip install {' '.join(packages_to_install)}\n"))

            # Mark installation as complete and enable close button
            installation_complete = True
            install_root.after(0, lambda: close_btn.config(state=tk.NORMAL, text="Continue to Application"))

        # Start installation in background thread
        install_thread = threading.Thread(target=run_installation, daemon=True)
        install_thread.start()

        # Run the installation window
        install_root.mainloop()

        # After window closes, re-check imports
        try:
            for package in missing_packages:
                __import__(package['import_name'])
            return True
        except ImportError:
            return False
    else:
        # User declined installation
        root.destroy()
        response = messagebox.askyesno(
            "Continue Without Dependencies?",
            "Some features (Excel and LibreOffice import) will not be available.\n\n"
            "Do you want to continue anyway?"
        )
        return response  # True if they want to continue, False if they want to exit

# ============ FIX POPUP WINDOWS ============

# We'll store the root reference later
_messagebox_root = None

def set_messagebox_parent(root_window):
    """Call this after creating the root window"""
    global _messagebox_root
    _messagebox_root = root_window

# Store original functions
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

# Apply patches
messagebox.showinfo = patched_showinfo
messagebox.showwarning = patched_showwarning
messagebox.showerror = patched_showerror
messagebox.askyesno = patched_askyesno
messagebox.askokcancel = patched_askokcancel
messagebox.askretrycancel = patched_askretrycancel
messagebox.askyesnocancel = patched_askyesnocancel
# ===========================================


# ============ SPLASH SCREEN ============
class SplashScreen:
    def __init__(self, root):
        self.root = root
        self.root.overrideredirect(True)
        w, h = 500, 300
        ws = self.root.winfo_screenwidth()
        hs = self.root.winfo_screenheight()
        x = (ws//2) - (w//2)
        y = (hs//2) - (h//2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.configure(bg='#2c3e50')

        main = tk.Frame(self.root, bg='#2c3e50', padx=30, pady=30)
        main.pack(fill=tk.BOTH, expand=True)

        tk.Label(main, text="🔬", font=("Segoe UI", 48),
                bg='#2c3e50', fg='#3498db').pack(pady=(0, 10))
        tk.Label(main, text="Scientific Toolkit",
                font=("Segoe UI", 18, "bold"),
                bg='#2c3e50', fg='white').pack()

        self.msg_var = tk.StringVar(value="Loading components...")
        tk.Label(main, textvariable=self.msg_var,
                font=("Segoe UI", 10),
                bg='#2c3e50', fg='#bdc3c7').pack(pady=(0, 20))

        self.progress = ttk.Progressbar(main, mode='indeterminate', length=400)
        self.progress.pack(pady=10)
        self.progress.start(10)

        tk.Label(main, text="v2.0",
                font=("Segoe UI", 8),
                bg='#2c3e50', fg='#7f8c8d').pack(side=tk.BOTTOM, pady=(20, 0))

        self.root.update()

    def set_message(self, message):
        """Update the message"""
        self.msg_var.set(message)
        self.root.update_idletasks()

    def close(self):
        """Close splash screen"""
        self.root.destroy()


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
            if engine_name == 'protocol':
                data_folder = self.engines_dir / "protocols"
            else:
                data_folder = self.engines_dir / engine_name

            if not data_folder.exists():
                data_folder.mkdir(exist_ok=True)

            self.available_engines[engine_name] = {
                'path': engine_file,
                'name': engine_name,
                'loaded': False,
                'instance': None,
                'data_folder': data_folder
            }
            print(f"✅ Found engine: {engine_name}")

    def load_engine(self, engine_name):
        if engine_name not in self.available_engines:
            return None

        engine_info = self.available_engines[engine_name]
        if engine_info['loaded']:
            return engine_info['instance']

        try:
            spec = importlib.util.spec_from_file_location(engine_name, engine_info['path'])
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            class_name = f"{engine_name.capitalize()}Engine"
            engine_class = getattr(module, class_name, None)

            if engine_class:
                instance = engine_class(str(engine_info['data_folder']))
                engine_info['loaded'] = True
                engine_info['instance'] = instance
                print(f"✅ Loaded engine: {engine_name}")
                return instance
        except Exception as e:
            print(f"❌ Failed to load engine {engine_name}: {e}")
        return None

    def get_available_engines(self):
        return list(self.available_engines.keys())


# ============ COLOR MANAGER ============
class ColorManager:
    def __init__(self, config_dir):
        self.config_dir = Path(config_dir)
        self.colors = self._load_colors()

    def _load_colors(self):
        color_file = self.config_dir / "scatter_colors.json"
        default = {
            "classification_colors": {},
            "default_colors": {"background": "#ffffff", "foreground": "#000000"}
        }
        if color_file.exists():
            try:
                with open(color_file, 'r') as f:
                    return json.load(f)
            except:
                return default
        return default

    def get_foreground(self, classification):
        if not classification:
            return self.colors["default_colors"]["foreground"]
        colors = self.colors.get("classification_colors", {}).get(classification)
        if colors:
            return colors.get("foreground", self.colors["default_colors"]["foreground"])
        return self.colors["default_colors"]["foreground"]

    def get_background(self, classification):
        if not classification:
            return self.colors["default_colors"]["background"]
        colors = self.colors.get("classification_colors", {}).get(classification)
        if colors:
            return colors.get("background", self.colors["default_colors"]["background"])
        return self.colors["default_colors"]["background"]

    def get_all_classifications(self):
        return list(self.colors.get("classification_colors", {}).keys())


# ============ SCIENTIFIC TOOLKIT ============
class ScientificToolkit:
    def __init__(self, root):
        self.root = root
        self.root.title("Scientific Toolkit")
        self.root.geometry("1400x850")

        # ============ ENGINE DETECTION ============
        self.engine_manager = EngineManager()
        self.classification_engine = None
        self.protocol_engine = None
        self._load_initial_engines()

        # ============ LOAD MASTER CONFIG ============
        self.config_dir = Path("config")
        self._load_chemical_elements()
        self.color_manager = ColorManager(self.config_dir)

        # ============ CORE ============
        self.data_hub = DataHub()
        self.samples = self.data_hub.get_all()
        self.menu_bar = None
        self.advanced_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.current_engine_name = 'classification'
        self.current_engine = None

        # ============ SETTINGS MANAGER (MUST LOAD FIRST) ============
        self.settings = SettingsManager(self)

        # ============ ENHANCED FEATURES (RESPECT SETTINGS) ============
        self.tooltip_manager = ToolTipManager()

        # Recent Files - with settings
        max_recent = self.settings.get('recent_files', 'max_files')
        self.recent_files = RecentFilesManager(max_recent=max_recent)

        # Macro Recorder - with settings
        if self.settings.get('macro_recorder', 'enabled'):
            self.macro_recorder = MacroRecorder(self)
        else:
            self.macro_recorder = None

        # Project Manager - always enabled but with settings
        self.project_manager = ProjectManager(self)

        # Script Exporter - with settings
        if self.settings.get('script_exporter', 'enabled'):
            self.script_exporter = ScriptExporter(self)
        else:
            self.script_exporter = None

        # Auto-Save - with settings
        if self.settings.get('auto_save', 'enabled'):
            interval = self.settings.get('auto_save', 'interval')
            self.auto_save = AutoSaveManager(self, auto_save_interval=interval)
        else:
            self.auto_save = None

        # ============ PLUGIN TRACKING ============
        self.enabled_plugins = self._load_enabled_plugins()
        self.hardware_plugins = {}
        self._added_plugins = set()
        self.plot_plugin_types = []
        self._loaded_plugin_info = {}

        # ============ BUILD UI ============
        self._create_menu_structure()
        self._create_panels()
        self._build_bottom_controls()
        self._load_plugins()
        self._refresh_engine_menu()

        # ============ CONNECT ============
        self.data_hub.register_observer(self.center)
        self.data_hub.register_observer(self.right)
        self._update_status("Ready")

        # ============ ADD TOOLTIPS ============
        if self.settings.get('tooltips', 'enabled'):
            self.root.after(500, self._add_tooltips_to_panels)

        # ============ APPLY OTHER SETTINGS ============
        self._apply_ui_settings()

        # ============ SETUP CLOSE HANDLER ============
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _load_initial_engines(self):
        """Load initial engines on startup"""
        engines = self.engine_manager.get_available_engines()
        if 'classification' in engines:
            self.classification_engine = self.engine_manager.load_engine('classification')
        if 'protocol' in engines:
            self.protocol_engine = self.engine_manager.load_engine('protocol')

    def _load_chemical_elements(self):
        """SINGLE source of truth for all column mappings"""
        elements_file = self.config_dir / "chemical_elements.json"
        if elements_file.exists():
            try:
                with open(elements_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.chemical_elements = data.get("elements", {})
                    self.ui_groups = data.get("ui_groups", {})

                    self.element_reverse_map = {}
                    for elem, info in self.chemical_elements.items():
                        standard = info["standard"]
                        for var in info["variations"]:
                            self.element_reverse_map[var] = standard

                    print(f"✅ Loaded {len(self.chemical_elements)} chemical elements")
            except Exception as e:
                print(f"⚠️ Error loading chemical elements: {e}")
                self.chemical_elements = {}
                self.element_reverse_map = {}
        else:
            print(f"⚠️ chemical_elements.json not found - column normalization disabled")
            self.chemical_elements = {}
            self.element_reverse_map = {}

    def _apply_ui_settings(self):
        """Apply UI settings after panels are created"""
        # Update unsaved indicator based on settings
        if hasattr(self, 'unsaved_indicator'):
            show_indicator = self.settings.get('ui', 'show_unsaved_indicator')
            if not show_indicator:
                self.unsaved_indicator.config(text="")

        # Apply tooltip delay
        if self.settings.get('tooltips', 'enabled') and hasattr(self, 'tooltip_manager'):
            delay = self.settings.get('tooltips', 'delay')
            # ToolTipManager would need to be updated to support delay changes
            # For now, just store the setting

    def _on_closing(self):
        """Handle window closing - do a final auto-save if needed"""
        # Update last session info
        if hasattr(self, 'settings'):
            self.settings.update_last_session(
                window_geometry=self.root.geometry(),
                last_project=self.project_manager.current_project_file
            )

        # Check for unsaved changes
        if self.data_hub.has_unsaved_changes():
            response = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Would you like to save before exiting?\n\n"
                "Yes: Save now\n"
                "No: Exit without saving\n"
                "Cancel: Stay in application"
            )

            if response is None:  # Cancel
                return
            elif response:  # Yes
                if not self.project_manager.save_project():
                    # User cancelled save
                    return

        # Stop auto-save thread
        if hasattr(self, 'auto_save') and self.auto_save:
            self.auto_save.stop()

        self.root.destroy()

    def _open_settings(self):
        """Open the settings dialog"""
        SettingsDialog(self.root, self.settings)

        # Re-apply settings after dialog closes
        self._reapply_settings()

    def _reapply_settings(self):
        """Reapply settings after changes"""
        # Update recent files max
        if hasattr(self, 'recent_files'):
            max_files = self.settings.get('recent_files', 'max_files')
            self.recent_files.max_recent = max_files

        # Update tooltips
        if hasattr(self, 'tooltip_manager'):
            if self.settings.get('tooltips', 'enabled'):
                self.root.after(500, self._add_tooltips_to_panels)
            else:
                self.tooltip_manager.clear_all()

        # Update unsaved indicator
        if hasattr(self, 'unsaved_indicator'):
            show_indicator = self.settings.get('ui', 'show_unsaved_indicator')
            if show_indicator:
                self.unsaved_indicator.config(text="●" if self.data_hub.has_unsaved_changes() else "○")
            else:
                self.unsaved_indicator.config(text="")

        # Update macro menu states
        self._update_macro_menu_state()

    def _update_macro_menu_state(self):
        """Enable/disable macro menu based on settings"""
        if not hasattr(self, 'workflow_menu'):
            return

        macro_enabled = self.settings.get('macro_recorder', 'enabled')
        state = tk.NORMAL if macro_enabled else tk.DISABLED

        try:
            self.workflow_menu.entryconfig(0, state=state)  # Start Recording
            self.workflow_menu.entryconfig(1, state=state)  # Stop Recording
            self.workflow_menu.entryconfig(3, state=state)  # Manage Macros
        except:
            pass

    def _get_plugin_category(self, plugin_info):
        """Determine plugin category based on keywords and name"""
        name = plugin_info.get('name', '').lower()
        desc = plugin_info.get('description', '').lower()
        plugin_id = plugin_info.get('id', '').lower()

        search_text = f"{name} {desc} {plugin_id}"

        categories = [
            {
                'name': '🧪 Geochemistry',
                'keywords': [
                    'geochem', 'normalization', 'normative', 'hg', 'mobility',
                    'element', 'trace', 'major', 'oxide', 'la-icp-ms', 'laicpms',
                    'icp', 'spectral', 'geoexplorer', 'geochemical', 'xrf', 'pxrf',
                    'lucas-tooth', 'compton', 'matrix correction', 'blank correction'
                ]
            },
            {
                'name': '📊 Statistical Analysis',
                'keywords': [
                    'statistical', 'compositional', 'composition', 'validation',
                    'spss', 'uncertainty', 'propagation', 'wizard', 'stats',
                    'anova', 'pca', 'cluster', 'discriminant', 'data validation',
                    'uncertainty propagation', 'compositional data', 'aitchison',
                    'correlation', 'descriptive', 'multivariate', 'factor analysis'
                ]
            },
            {
                'name': '🤖 Machine Learning',
                'keywords': [
                    'machine learning', 'ml', 'literature comparison', 'prediction',
                    'classifier', 'learning', 'ai', 'artificial intelligence',
                    'literature', 'random forest', 'svm', 'knn', 'neural',
                    'classification', 'regression', 'feature importance'
                ]
            },
            {
                'name': '📈 Visualization',
                'keywords': [
                    'visualization', 'plot', 'diagram', 'spider', 'ternary',
                    'contour', 'kriging', 'discrimination', 'petroplot', 'mapping',
                    'contouring', 'spatial', 'google earth', 'export', 'map',
                    'scatter', 'graph', 'chart', 'spider diagram', 'ternary diagram',
                    'discrimination diagram', 'petroplot pro'
                ]
            },
            {
                'name': '⏳ Dating & Geochronology',
                'keywords': [
                    'dating', 'chronological', 'isotope', 'mixing',
                    'upb', 'age', 'geochronology', 'radiometric', 'isotope mixing',
                    'u-pb', 'la-icp-ms', 'concordia', 'calibration', 'intcal'
                ]
            },
            {
                'name': '🪨 Petrology & Mineralogy',
                'keywords': [
                    'petrology', 'lithic', 'morphometrics', 'magma', 'melts',
                    'microscopy', 'mineral', 'thin section', 'virtual microscopy',
                    'magma modeling', 'rock', 'crystal', 'petro', 'crystallization',
                    'phase diagram', 'trace element modeling', 'ree pattern'
                ]
            },
            {
                'name': '🔧 Utilities',
                'keywords': [
                    'utility', 'filter', 'photo', 'layout', 'report',
                    'toolbox', 'manager', 'advanced filter', 'photo manager',
                    'publication layout', 'report generator', '3d gis', 'gis',
                    'museum', 'database', 'import', 'export', 'kml', 'google earth',
                    'batch', 'processor', 'viewer', 'plotter'
                ]
            }
        ]

        for category in categories:
            if any(keyword in search_text for keyword in category['keywords']):
                print(f"  → Categorized '{name}' as {category['name']}")
                return category['name']

        print(f"  → No category match for '{name}', using '📁 Other'")
        return '📁 Other'

    def _rebuild_advanced_menu(self):
        """Rebuild the Advanced menu with categorized submenus"""
        # Clear existing items completely
        self.advanced_menu.delete(0, tk.END)

        if not self._loaded_plugin_info:
            self.advanced_menu.add_command(label="No plugins loaded", state=tk.DISABLED)
            return

        # Group plugins by category
        plugins_by_category = defaultdict(list)

        for plugin_id, plugin_info in self._loaded_plugin_info.items():
            category = self._get_plugin_category(plugin_info)
            plugins_by_category[category].append({
                'name': plugin_info.get('name', plugin_id),
                'icon': plugin_info.get('icon', '🔧'),
                'command': plugin_info['command'],
                'id': plugin_id
            })

        # Sort categories
        sorted_categories = sorted(
            plugins_by_category.keys(),
            key=lambda x: x.split(' ', 1)[-1] if ' ' in x else x
        )

        # Add each category as a submenu
        for category in sorted_categories:
            if not plugins_by_category[category]:
                continue

            submenu = tk.Menu(self.advanced_menu, tearoff=0)

            # Sort plugins within category by name
            sorted_plugins = sorted(
                plugins_by_category[category],
                key=lambda x: x['name'].lower()
            )

            for plugin in sorted_plugins:
                label = plugin['name']
                if plugin['icon']:
                    label = f"{plugin['icon']} {label}"

                submenu.add_command(
                    label=label,
                    command=plugin['command']
                )

            self.advanced_menu.add_cascade(label=category, menu=submenu)

        # Add separator and refresh option if we have categories
        if sorted_categories:
            self.advanced_menu.add_separator()
            self.advanced_menu.add_command(
                label="🔄 Refresh Categories",
                command=self._rebuild_advanced_menu
            )

    def _load_enabled_plugins(self):
        config_file = Path("config/enabled_plugins.json")
        if config_file.exists():
            try:
                with open(config_file) as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def normalize_columns(self, row_dict):
        """Master column normalizer - uses chemical_elements.json"""
        normalized = {}
        notes_parts = []
        seen_standards = set()

        if 'Sample_ID' in row_dict:
            normalized['Sample_ID'] = str(row_dict['Sample_ID']).strip()
        else:
            found = False
            for key, value in row_dict.items():
                if key in self.element_reverse_map and self.element_reverse_map[key] == 'Sample_ID':
                    normalized['Sample_ID'] = str(value).strip()
                    found = True
                    break
            if not found:
                normalized['Sample_ID'] = f"SAMPLE_{len(self.samples)+1:04d}"

        print(f"\n🔍 RAW COLUMNS: {list(row_dict.keys())}")

        for key, value in row_dict.items():
            if key == 'Sample_ID' or value is None or str(value).strip() == '':
                continue

            clean_key = str(key).strip()
            clean_val = str(value).strip()

            if clean_key in self.element_reverse_map:
                standard = self.element_reverse_map[clean_key]
                if standard not in seen_standards:
                    try:
                        num_val = float(clean_val.replace(',', ''))
                        normalized[standard] = num_val
                    except ValueError:
                        normalized[standard] = clean_val
                    seen_standards.add(standard)
                    print(f"  ✓ MAPPED: '{clean_key}' → '{standard}' = {clean_val}")
                else:
                    print(f"  ⚠ DUPLICATE: '{clean_key}' → '{standard}' (skipped)")
            else:
                notes_parts.append(f"{clean_key}: {clean_val}")
                print(f"  ? UNKNOWN: '{clean_key}' = {clean_val}")

        if 'Notes' in row_dict and row_dict['Notes']:
            existing = str(row_dict['Notes']).strip()
            if existing and existing.lower() != 'nan':
                notes_parts.insert(0, existing)

        normalized['Notes'] = ' | '.join(notes_parts) if notes_parts else ''
        print(f"  ✅ FINAL STANDARDS: {list(normalized.keys())}\n")
        return normalized

    def validate_plugin_data(self, data_rows):
        """Validate and normalize data from plugins"""
        if not data_rows:
            return []

        print(f"\n📥 Importing {len(data_rows)} rows from plugin...")
        filtered_rows = []

        for row in data_rows:
            # Use the left panel's normalization
            if hasattr(self.left, 'normalize_column_name') and hasattr(self.left, 'column_mappings'):
                clean_row = {}
                notes_parts = []
                seen_standards = set()

                for k, v in row.items():
                    if not k or not k.strip():
                        continue

                    normalized_key = self.left.normalize_column_name(k, self.left.column_mappings)
                    clean_val = str(v).strip() if v else ''

                    if normalized_key == 'Sample_ID':
                        if normalized_key not in seen_standards:
                            clean_row[normalized_key] = clean_val
                            seen_standards.add(normalized_key)

                    elif normalized_key in self.left.column_mappings.values():
                        if normalized_key not in seen_standards:
                            try:
                                num_val = float(clean_val.replace(',', ''))
                                clean_row[normalized_key] = num_val
                            except ValueError:
                                clean_row[normalized_key] = clean_val
                            seen_standards.add(normalized_key)

                    else:
                        notes_parts.append(f"{k}: {clean_val}")

                if notes_parts:
                    clean_row['Notes'] = ' | '.join(notes_parts)

                if clean_row:
                    filtered_rows.append(clean_row)
            else:
                # Fallback to simple passthrough
                filtered_rows.append(row)

        print(f"✅ Imported {len(filtered_rows)} rows")
        return filtered_rows

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

        # ============ FILE MENU ============
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)

        # Project operations
        self.file_menu.add_command(label="🆕 New Project (Ctrl+N)",
                                   command=self.project_manager.new_project,
                                   accelerator="Ctrl+N")
        self.file_menu.add_command(label="💾 Save Project (Ctrl+S)",
                                   command=self.project_manager.save_project,
                                   accelerator="Ctrl+S")
        self.file_menu.add_command(label="📂 Open Project (Ctrl+O)",
                                   command=self.project_manager.load_project,
                                   accelerator="Ctrl+O")
        self.file_menu.add_separator()

        # Import/Export data
        self.file_menu.add_command(label="Import CSV... (Ctrl+I)",
                                   command=lambda: self._import_with_macro(),
                                   accelerator="Ctrl+I")
        self.file_menu.add_command(label="Import Excel...",
                                   command=lambda: self._import_with_macro())
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Export CSV... (Ctrl+E)",
                                   command=self._export_csv,
                                   accelerator="Ctrl+E")
        self.file_menu.add_command(label="🐍 Export to Python/R Script",
                                   command=self.script_exporter.export_current_workflow if self.script_exporter else lambda: messagebox.showinfo("Feature Disabled", "Script Exporter is disabled"))
        self.file_menu.add_separator()

        # Recent files submenu
        self.recent_menu = tk.Menu(self.file_menu, tearoff=0)
        self.file_menu.add_cascade(label="📜 Recent Files", menu=self.recent_menu)
        self._update_recent_files_menu()

        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit (Ctrl+Q)",
                                   command=self._on_closing,
                                   accelerator="Ctrl+Q")

        # ============ EDIT MENU ============
        self.edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Edit", menu=self.edit_menu)
        self.edit_menu.add_command(label="Delete Selected (Del)",
                                   command=self._delete_selected,
                                   accelerator="Del")
        self.edit_menu.add_command(label="Select All (Ctrl+A)",
                                   command=self._select_all,
                                   accelerator="Ctrl+A")
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Find... (Ctrl+F)",
                                   command=self._focus_search,
                                   accelerator="Ctrl+F")

        # ============ WORKFLOW MENU ============
        self.workflow_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Workflow", menu=self.workflow_menu)

        macro_enabled = self.settings.get('macro_recorder', 'enabled')
        macro_state = tk.NORMAL if macro_enabled else tk.DISABLED

        self.workflow_menu.add_command(label="🔴 Start Recording (Ctrl+R)",
                                      command=self._start_macro_recording,
                                      accelerator="Ctrl+R",
                                      state=macro_state)
        self.workflow_menu.add_command(label="⏸️ Stop Recording (Ctrl+T)",
                                      command=self._stop_macro_recording,
                                      accelerator="Ctrl+T",
                                      state=macro_state)
        self.workflow_menu.add_separator()
        self.workflow_menu.add_command(label="📋 Manage Macros (Ctrl+M)",
                                      command=self._open_macro_manager,
                                      accelerator="Ctrl+M",
                                      state=macro_state)

        # ============ TOOLS MENU ============
        self.tools_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Tools", menu=self.tools_menu)
        self.tools_menu.add_command(label="Plugin Manager", command=self._open_plugin_manager)
        self.tools_menu.add_separator()
        self.engine_menu = tk.Menu(self.tools_menu, tearoff=0)
        self.tools_menu.add_cascade(label="🔧 Switch Engine", menu=self.engine_menu)
        self.tools_menu.add_separator()
        self.tools_menu.add_command(label="⚙️ Settings", command=self._open_settings)

        # ============ HELP MENU ============
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.help_menu.add_command(label="Allowed Columns", command=self.show_allowed_columns)
        self.help_menu.add_command(label="⌨️ Keyboard Shortcuts", command=self._show_keyboard_shortcuts)
        self.help_menu.add_separator()
        self.help_menu.add_command(label="⚠️ Disclaimer", command=self.show_disclaimer)
        self.help_menu.add_command(label="About", command=self.show_about)
        self.help_menu.add_command(label="🔄 Check for Updates",
                                command=self._check_for_updates)
        self.help_menu.add_separator()
        self.help_menu.add_command(label="❤️ Support the Project", command=self.show_support)

        # Advanced menu will be added later if plugins exist
        # Don't add it to menu bar yet

        # Setup keyboard shortcuts
        self._setup_keyboard_shortcuts()

    def _check_for_updates(self):
        from features.update_checker import HTTPUpdateChecker
        # Pass the local version explicitly
        checker = HTTPUpdateChecker(self, local_version=APP_INFO["version"])
        checker.check()

    def _export_csv(self):
        """Export data to CSV"""
        samples = self.data_hub.get_all()
        if not samples:
            if hasattr(self.center, 'show_warning'):
                self.center.show_warning('export', "No data to export")
            messagebox.showwarning("No Data", "No data to export")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if not path:
            return

        try:
            total_samples = len(samples)
            if hasattr(self.center, 'show_progress'):
                self.center.show_progress('export', 0, total_samples, "Preparing export...")

            # Record macro action
            if self.macro_recorder:
                self.macro_recorder.record_action('export_csv', filepath=path)

            if hasattr(self.center, 'show_progress'):
                self.center.show_progress('export', 1, total_samples, "Writing file...")

            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.data_hub.get_column_names())
                writer.writeheader()
                writer.writerows(samples)

            self.data_hub.mark_saved()
            if hasattr(self.center, 'show_operation_complete'):
                self.center.show_operation_complete('export', f"{total_samples} rows exported")
            messagebox.showinfo("Success", f"Exported {total_samples} rows to {path}")

        except Exception as e:
            if hasattr(self.center, 'show_error'):
                self.center.show_error('export', str(e))
            messagebox.showerror("Export Error", str(e))

    def _open_plugin_manager(self):
        try:
            from plugins.plugin_manager import PluginManager
            PluginManager(self)
        except ImportError as e:
            messagebox.showerror("Error", f"Plugin Manager not found: {e}")

    def _update_status(self, message):
        print(f"Status: {message}")
        self.root.update_idletasks()

    def _create_panels(self):
        self.main = ttk.Frame(self.root)
        self.main.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.main_pane = ttk.PanedWindow(self.main, orient=tk.HORIZONTAL)
        self.main_pane.pack(fill=tk.BOTH, expand=True)

        self.left = LeftPanel(self.main_pane, self)
        self.main_pane.add(self.left.frame, weight=1)

        self.center = CenterPanel(self.main_pane, self)
        self.main_pane.add(self.center.frame, weight=8)

        self.right = RightPanel(self.main_pane, self)
        self.main_pane.add(self.right.frame, weight=1)

    # ============ DELETE SELECTED METHOD ============
    def _delete_selected(self):
        """Delete selected rows"""
        selected = self.center.get_selected_indices()
        if selected and messagebox.askyesno("Confirm", f"Delete {len(selected)} selected row(s)?"):
            self.data_hub.delete_rows(selected)
            self.samples = self.data_hub.get_all()

    def auto_size_columns(self, tree, samples, force=False):
        """Auto-size columns based on content"""
        if not samples or not tree.get_children():
            return
        columns = tree["columns"]
        for col in columns:
            if col == "☐":
                tree.column(col, width=30)
                continue
            max_width = len(str(col)) * 8
            for item in tree.get_children()[:50]:
                values = tree.item(item, "values")
                col_idx = columns.index(col)
                if col_idx < len(values):
                    text = str(values[col_idx])
                    width = len(text) * 7
                    if width > max_width:
                        max_width = width
            tree.column(col, width=min(max(80, max_width), 300))

    def _build_bottom_controls(self):
        """Build bottom controls with clickable status bar in the middle"""
        bottom = ttk.Frame(self.root, relief=tk.SUNKEN, borderwidth=1)
        bottom.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=5)

        # Left side: Navigation
        nav = ttk.Frame(bottom)
        nav.pack(side=tk.LEFT, padx=5, pady=2)

        self.prev_btn = ttk.Button(nav, text="◀ Prev", command=self.center.prev_page, width=8)
        self.prev_btn.pack(side=tk.LEFT, padx=2)
        self.page_label = tk.Label(nav, text="Page 1 of 1")
        self.page_label.pack(side=tk.LEFT, padx=10)
        self.next_btn = ttk.Button(nav, text="Next ▶", command=self.center.next_page, width=8)
        self.next_btn.pack(side=tk.LEFT, padx=2)
        self.total_label = tk.Label(nav, text="Total: 0 rows")
        self.total_label.pack(side=tk.LEFT, padx=10)

        # Center: Clickable Status Bar
        status_frame = ttk.Frame(bottom, relief=tk.SUNKEN, borderwidth=1)
        status_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=2)

        # Make it look clickable with a hand cursor and slight background on hover
        self.status_label = tk.Label(status_frame, textvariable=self.center.status_var,
                                    font=("TkDefaultFont", 8), anchor=tk.W,
                                    bg='#f0f0f0', cursor="hand2", relief=tk.FLAT)
        self.status_label.pack(fill=tk.X, padx=4, pady=2)

        # Bind click event
        self.status_label.bind("<Button-1>", lambda e: self._show_status_details())

        # Hover effects
        self.status_label.bind("<Enter>", lambda e: self.status_label.config(bg='#e0e0e0'))
        self.status_label.bind("<Leave>", lambda e: self.status_label.config(bg='#f0f0f0'))

        # Right side: Selection controls
        sel = ttk.Frame(bottom)
        sel.pack(side=tk.RIGHT, padx=5, pady=2)

        # Add unsaved changes indicator
        self.unsaved_indicator = tk.Label(sel, text="", font=("Arial", 10),
                                        fg="orange", width=2)
        self.unsaved_indicator.pack(side=tk.LEFT, padx=2)

        ttk.Button(sel, text="Select All", command=self.center.select_all, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(sel, text="Deselect", command=self.center.deselect_all, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(sel, text="🗑️ Delete", command=self._delete_selected, width=8).pack(side=tk.LEFT, padx=2)
        self.sel_label = tk.Label(sel, text="Selected: 0", font=("Arial", 9, "bold"))
        self.sel_label.pack(side=tk.LEFT, padx=10)

        # Start a periodic check for unsaved changes
        self._check_unsaved_changes()

    def _check_unsaved_changes(self):
        """Periodically check for unsaved changes and update indicator"""
        if hasattr(self, 'data_hub') and hasattr(self, 'unsaved_indicator'):
            if self.data_hub.has_unsaved_changes():
                self.unsaved_indicator.config(text="●", fg="orange")
                # Also update tooltip
                if hasattr(self, 'tooltip_manager'):
                    self.tooltip_manager.add(self.unsaved_indicator,
                                            "Unsaved changes - save your work!")
            else:
                self.unsaved_indicator.config(text="○", fg="gray")

        # Check again in 2 seconds
        self.root.after(2000, self._check_unsaved_changes)

    def _show_status_details(self):
        if not hasattr(self.center, 'last_operation'):
            return

        op = self.center.last_operation
        op_type = op.get('type')

        if op_type == 'update_error':
            messagebox.showerror("Update Error", op.get('error', 'Unknown error'))

        elif op_type == 'update_available':
            response = messagebox.askyesno(
                "Update Available",
                f"Version {op['new_version']} is available (from {op['source']}).\n\nDo you want to download it now?"
            )
            if response:
                self._check_for_updates()   # This will run again and set app_update

        elif op_type == 'app_update':
            from features.update_checker import HTTPUpdateChecker
            checker = HTTPUpdateChecker(self, local_version=APP_INFO["version"])
            checker.show_update_dialog(
                changed_files=op['changed'],
                new_commit=op['new_commit'],
                new_version=op['new_version']
            )

        else:
            current_status = self.center.status_var.get()
            if current_status and current_status != "Ready":
                messagebox.showinfo("Status", current_status)

    def update_pagination(self, current_page, total_pages, total_rows):
        self.current_page = current_page
        self.total_pages = total_pages
        self.total_rows = total_rows
        self.page_label.config(text=f"Page {current_page + 1} of {total_pages}")
        self.total_label.config(text=f"Total: {total_rows} rows")
        self.prev_btn.state(["!disabled" if current_page > 0 else "disabled"])
        self.next_btn.state(["!disabled" if current_page < total_pages - 1 else "disabled"])

    def update_selection(self, count):
        self.sel_label.config(text=f"Selected: {count}")

    def _refresh_engine_menu(self):
        """Refresh the engine menu without duplicating items"""
        # Clear existing items
        self.engine_menu.delete(0, tk.END)

        engines = self.engine_manager.get_available_engines()
        if not engines:
            self.engine_menu.add_command(label="No engines found", state="disabled")
            return

        for engine_name in sorted(engines):
            is_current = (engine_name == self.current_engine_name)
            self.engine_menu.add_command(
                label=f"{'✓ ' if is_current else '  '}{engine_name.capitalize()} Engine",
                command=lambda e=engine_name: self._switch_engine(e)
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
                self._update_status(f"✅ Switched to {engine_name} engine")
                self._refresh_engine_menu()
            else:
                messagebox.showerror("Error", f"Failed to load {engine_name} engine")
        except Exception as e:
            messagebox.showerror("Error", f"Engine switch failed: {e}")

    def _load_plugins(self):
        import json
        from pathlib import Path

        config_file = Path("config/enabled_plugins.json")
        if config_file.exists():
            try:
                with open(config_file) as f:
                    self.enabled_plugins = json.load(f)
            except:
                self.enabled_plugins = {}
        else:
            self.enabled_plugins = {}

        # Hardware plugins (unchanged)
        hw_dir = Path("plugins/hardware")

        # Clear previously loaded hardware plugins from sidebar and registry
        if hasattr(self, 'left') and hasattr(self.left, 'remove_hardware_button'):
            for pid, entry in list(self.hardware_plugins.items()):
                info = entry.get('info', {})
                self.left.remove_hardware_button(
                    name=info.get('name', pid),
                    icon=info.get('icon', '🔌')
                )
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
                        plugin_instance = None
                        if hasattr(module, 'register_plugin'):
                            plugin_instance = module.register_plugin(self)
                        elif hasattr(module, 'setup_plugin'):
                            plugin_instance = module.setup_plugin(self)
                        if plugin_instance:
                            self.hardware_plugins[plugin_id] = {
                                'instance': plugin_instance,
                                'info': info,
                                'file': py_file
                            }
                            if hasattr(self, 'left'):
                                self.left.add_hardware_button(
                                    name=info.get('name', plugin_id),
                                    icon=info.get('icon', '🔌'),
                                    command=plugin_instance.open_window
                                )
                except Exception as e:
                    print(f"❌ Failed to load {py_file.name}: {e}")

        # Software / add‑ons (unchanged)
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

                    if hasattr(module, 'PLOT_TYPES'):
                        plot_types = module.PLOT_TYPES
                        if isinstance(plot_types, dict):
                            for name, func in plot_types.items():
                                if name not in [p[0] for p in self.plot_plugin_types]:
                                    self.plot_plugin_types.append((name, func))

                    if hasattr(module, 'PLUGIN_INFO'):
                        info = module.PLUGIN_INFO
                        plugin_instance = None
                        if hasattr(module, 'register_plugin'):
                            plugin_instance = module.register_plugin(self)
                        elif hasattr(module, 'setup_plugin'):
                            plugin_instance = module.setup_plugin(self)

                        if plugin_instance:
                            software_loaded = True

                            # ============ NEW: TAB PLUGINS (highest priority) ============
                            # Check if plugin wants its own tab - if so, add it and skip everything else
                            if hasattr(plugin_instance, 'create_tab'):
                                # Skip if it's a console plugin (they have console in category or id)
                                plugin_category = info.get('category', '')
                                plugin_id = info.get('id', '')

                                if 'console' in plugin_category or 'console' in plugin_id:
                                    # Don't add as tab plugin - consoles are handled separately
                                    print(f"⌨️ Console plugin detected: {plugin_id} - will be added to console dropdown")
                                    # Don't do anything here - the register_plugin will call add_console_plugin
                                else:
                                    # Regular tab plugin
                                    print(f"📑 Adding tab plugin: {plugin_name}")
                                    if hasattr(self.center, 'add_tab_plugin'):
                                        self.center.add_tab_plugin(...)
                                    continue

                            # ============ EXISTING CODE - COMPLETELY UNCHANGED ============
                            if plugin_id not in self._added_plugins:
                                self._add_to_advanced_menu(info, plugin_instance)
                                self._added_plugins.add(plugin_id)

                            plugin_name = info.get('name', '').lower()
                            plugin_id_lower = plugin_id.lower()
                            plugin_desc = info.get('description', '').lower()
                            ai_keywords = ['ai', 'assistant', 'chat', 'gemini', 'claude',
                                        'grok', 'deepseek', 'ollama', 'copilot', 'chatgpt']
                            is_ai = any(kw in plugin_name or kw in plugin_id_lower or kw in plugin_desc
                                    for kw in ai_keywords)
                            if is_ai and hasattr(plugin_instance, 'query'):
                                if hasattr(self.center, 'add_ai_plugin'):
                                    self.center.add_ai_plugin(
                                        plugin_name=info.get('name', plugin_id),
                                        plugin_icon=info.get('icon', '🤖'),
                                        plugin_instance=plugin_instance
                                    )
                except Exception as e:
                    print(f"❌ Failed to load {py_file.name}: {e}")

        if self.plot_plugin_types:
            self.center.update_plot_types(self.plot_plugin_types)

        # ============ FIXED MENU ORDER ============
        # Determine indices of existing menus
        tools_index = None
        help_index = None
        advanced_exists = False
        help_exists = False

        try:
            for i in range(self.menu_bar.index("end") + 1):
                try:
                    label = self.menu_bar.entrycget(i, "label")
                    if label == "Tools":
                        tools_index = i
                    elif label == "Help":
                        help_exists = True
                        help_index = i
                    elif label == "Advanced":
                        advanced_exists = True
                except:
                    pass
        except:
            pass

        # Rebuild Advanced menu if there are plugins
        if software_loaded and self._loaded_plugin_info:
            self.advanced_menu.delete(0, tk.END)
            self._rebuild_advanced_menu()

            if not advanced_exists:
                # Insert after Tools (preferred) or before Help, or append
                if tools_index is not None:
                    self.menu_bar.insert_cascade(tools_index + 1, label="Advanced", menu=self.advanced_menu)
                elif help_exists:
                    self.menu_bar.insert_cascade(help_index, label="Advanced", menu=self.advanced_menu)
                else:
                    self.menu_bar.add_cascade(label="Advanced", menu=self.advanced_menu)
        else:
            # No plugins – optionally keep Advanced (if it exists) or do nothing
            # We keep it to preserve position (commented deletion)
            pass

        # Add Help menu if it doesn't exist yet
        if not help_exists:
            self.menu_bar.add_cascade(label="Help", menu=self.help_menu)

    def _add_to_advanced_menu(self, info, plugin_instance):
        plugin_id = info.get('id', '')
        if plugin_id in self._added_plugins:
            return

        name = info.get('name', 'Unknown')
        icon = info.get('icon', '🔧')

        open_method = None
        if hasattr(plugin_instance, 'open_window'):
            open_method = plugin_instance.open_window
        elif hasattr(plugin_instance, 'show_interface'):
            open_method = plugin_instance.show_interface

        if open_method:
            self._loaded_plugin_info[plugin_id] = {
                'name': name,
                'icon': icon,
                'command': open_method,
                'id': plugin_id,
                'description': info.get('description', ''),
                'category': info.get('menu_category', '')
            }
            self._added_plugins.add(plugin_id)

            print(f"📦 Loaded plugin: {name} (ID: {plugin_id})")
            print(f"   Description: {info.get('description', '')[:50]}...")

    # ============ ENHANCED FEATURES METHODS ============

    def _setup_keyboard_shortcuts(self):
        """Setup all keyboard shortcuts"""
        # File operations
        self.root.bind('<Control-n>', lambda e: self.project_manager.new_project())
        self.root.bind('<Control-o>', lambda e: self.project_manager.load_project())
        self.root.bind('<Control-s>', lambda e: self.project_manager.save_project())
        self.root.bind('<Control-i>', lambda e: self._import_with_macro())
        self.root.bind('<Control-e>', lambda e: self._export_csv())
        self.root.bind('<Control-q>', lambda e: self._on_closing())

        # Edit operations
        self.root.bind('<Delete>', lambda e: self._delete_selected())
        self.root.bind('<Control-a>', lambda e: self._select_all())
        self.root.bind('<Control-f>', lambda e: self._focus_search())

        # Workflow/Macro operations
        if self.macro_recorder:
            self.root.bind('<Control-r>', lambda e: self._start_macro_recording())
            self.root.bind('<Control-t>', lambda e: self._stop_macro_recording())
            self.root.bind('<Control-m>', lambda e: self._open_macro_manager())

        # Function keys
        self.root.bind('<F1>', lambda e: self._show_keyboard_shortcuts())
        self.root.bind('<F5>', lambda e: self._refresh_all())

    def _import_with_macro(self):
        """Import file and record to macro if recording"""
        filepath = filedialog.askopenfilename(
            filetypes=[
                ("All supported files", "*.csv *.xlsx *.xls"),
                ("CSV files", "*.csv"),
                ("Excel files", "*.xlsx *.xls"),
                ("All files", "*.*")
            ]
        )

        if filepath:
            # Record action
            if self.macro_recorder:
                self.macro_recorder.record_action('import_file', filepath=filepath)

            # Add to recent files
            self.recent_files.add(filepath)
            self._update_recent_files_menu()

            # Perform import
            self.left.import_csv(filepath)

    def _update_recent_files_menu(self):
        """Update the recent files menu"""
        self.recent_menu.delete(0, tk.END)

        items = self.recent_files.get_menu_items()

        if items:
            for item in items:
                self.recent_menu.add_command(
                    label=item['label'],
                    command=lambda p=item['path']: self._open_recent_file(p)
                )

            self.recent_menu.add_separator()
            self.recent_menu.add_command(
                label="Clear Recent Files",
                command=self._clear_recent_files
            )
        else:
            self.recent_menu.add_command(label="(No recent files)", state=tk.DISABLED)

    def _open_recent_file(self, filepath):
        """Open a recent file"""
        if self.macro_recorder:
            self.macro_recorder.record_action('import_file', filepath=filepath)
        self.left.import_csv(filepath)

    def _clear_recent_files(self):
        """Clear recent files list"""
        if messagebox.askyesno("Clear Recent Files", "Clear all recent files?"):
            self.recent_files.clear()
            self._update_recent_files_menu()

    def _select_all(self):
        """Select all rows in the table"""
        if hasattr(self, 'center') and hasattr(self.center, 'tree'):
            for item in self.center.tree.get_children():
                self.center.tree.selection_add(item)

    def _focus_search(self):
        """Focus the search box"""
        if hasattr(self, 'center'):
            # Find the search entry widget
            for widget in self.center.table_tab.winfo_children():
                if isinstance(widget, ttk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Entry):
                            child.focus_set()
                            child.select_range(0, tk.END)
                            return

    def _refresh_all(self):
        """Refresh all UI components"""
        self.data_hub.notify_observers()
        messagebox.showinfo("Refresh", "All panels refreshed")

    def _start_macro_recording(self):
        """Start recording a macro"""
        if not self.settings.get('macro_recorder', 'enabled') or not self.macro_recorder:
            messagebox.showinfo("Feature Disabled",
                            "Macro Recorder is disabled. Enable it in Tools → Settings")
            return
        self.macro_recorder.start_recording()
        self.workflow_menu.entryconfig(0, label="🔴 Recording... (Ctrl+T to stop)")
        messagebox.showinfo("Recording", "Macro recording started!\n\nPerform your workflow, then press Ctrl+T to stop.")

    def _stop_macro_recording(self):
        """Stop recording and save macro"""
        if not self.macro_recorder or not self.macro_recorder.is_recording:
            messagebox.showwarning("Not Recording", "No macro is currently being recorded")
            return

        macro = self.macro_recorder.stop_recording()
        self.workflow_menu.entryconfig(0, label="🔴 Start Recording (Ctrl+R)")

        if not macro:
            messagebox.showinfo("Empty Macro", "No actions were recorded")
            return

        # Ask for macro name
        dialog = tk.Toplevel(self.root)
        dialog.title("Save Macro")
        dialog.geometry("400x150")
        dialog.transient(self.root)

        ttk.Label(dialog, text="Macro Name:", font=("TkDefaultFont", 10)).pack(pady=(20, 5))

        name_var = tk.StringVar(value=f"Workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        entry = ttk.Entry(dialog, textvariable=name_var, width=40)
        entry.pack(pady=5)
        entry.focus_set()
        entry.select_range(0, tk.END)

        def save():
            name = name_var.get().strip()
            if name:
                self.macro_recorder.save_macro(name, macro)
                dialog.destroy()

        ttk.Button(dialog, text="Save", command=save).pack(pady=10)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack()

        dialog.bind('<Return>', lambda e: save())

    def _open_macro_manager(self):
        """Open the macro manager dialog"""
        if not self.settings.get('macro_recorder', 'enabled') or not self.macro_recorder:
            messagebox.showinfo("Feature Disabled",
                            "Macro Recorder is disabled. Enable it in Tools → Settings")
            return
        MacroManagerDialog(self.root, self.macro_recorder)

    def _show_keyboard_shortcuts(self):
        """Show keyboard shortcuts help"""
        dialog = tk.Toplevel(self.root)
        dialog.title("⌨️ Keyboard Shortcuts")
        dialog.geometry("500x600")
        dialog.transient(self.root)

        main = ttk.Frame(dialog, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="Keyboard Shortcuts",
                 font=("TkDefaultFont", 14, "bold")).pack(pady=(0, 20))

        # Create scrolled text
        from tkinter import scrolledtext
        text = scrolledtext.ScrolledText(main, wrap=tk.WORD, font=("Courier", 10))
        text.pack(fill=tk.BOTH, expand=True)

        shortcuts = """
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
        """

        text.insert(tk.END, shortcuts.strip())
        text.config(state=tk.DISABLED)

        ttk.Button(main, text="Close", command=dialog.destroy).pack(pady=(10, 0))

    def _add_tooltips_to_panels(self):
        """Add tooltips to all UI elements"""
        if not hasattr(self, 'tooltip_manager'):
            return

        # Left panel tooltips
        if hasattr(self, 'left'):
            if hasattr(self.left, 'import_btn'):
                self.tooltip_manager.add(
                    self.left.import_btn,
                    "Import data from CSV or Excel files\nSupports automatic column mapping"
                )
            if hasattr(self.left, 'add_btn'):
                self.tooltip_manager.add(
                    self.left.add_btn,
                    "Add a new sample manually\nPress Enter in Notes field to add quickly"
                )

        # Center panel tooltips
        if hasattr(self, 'center'):
            if hasattr(self.center, 'plot_btn'):
                self.tooltip_manager.add(
                    self.center.plot_btn,
                    "Generate visualization using selected plot type"
                )

        # Right panel tooltips
        if hasattr(self, 'right'):
            if hasattr(self.right, 'apply_btn'):
                self.tooltip_manager.add(
                    self.right.apply_btn,
                    "Apply selected classification scheme\nResults will appear in Classification column"
                )

    def show_allowed_columns(self):
        from tkinter import scrolledtext

        win = tk.Toplevel(self.root)
        win.title("🔬 Standardized Columns")
        win.geometry("600x500")

        text = scrolledtext.ScrolledText(win, wrap=tk.WORD, font=("Courier", 9))
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        text.insert(tk.END, "STANDARDIZED COLUMN NAMES\n")
        text.insert(tk.END, "="*50 + "\n\n")
        text.insert(tk.END, f"Source: chemical_elements.json\n\n")

        groups = getattr(self, 'ui_groups', {})
        if not groups:
            text.insert(tk.END, "No groups defined in chemical_elements.json")
        else:
            for group_name, columns in groups.items():
                text.insert(tk.END, f"\n{group_name}:\n", "group")
                text.insert(tk.END, "-"*30 + "\n")
                for col in sorted(columns):
                    display = col
                    for info in self.chemical_elements.values():
                        if info["standard"] == col:
                            display = info.get("display_name", col)
                            break
                    text.insert(tk.END, f"  • {display}\n")

        text.tag_config("group", foreground="blue", font=("Courier", 9, "bold"))
        text.config(state=tk.DISABLED)

    def show_disclaimer(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("⚠️ Important Disclaimer")
        dialog.transient(self.root)

        title_frame = ttk.Frame(dialog)
        title_frame.pack(pady=20)
        ttk.Label(title_frame, text="⚠️", font=("Arial", 48)).pack()
        ttk.Label(title_frame, text="IMPORTANT DISCLAIMER", font=("Arial", 16, "bold")).pack(pady=10)

        text_frame = ttk.Frame(dialog)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)

        disclaimer_text = """This software is intended for RESEARCH and EDUCATIONAL use only.

Key Points:

• Automated classifications and analyses are based on published
  scientific thresholds and established research methodologies.

• Results MUST be verified by qualified specialists before being
  used in formal scientific conclusions.

• All classifications should be validated against published
  reference data and expert interpretation.

• This tool is designed to assist researchers in data analysis,
  not to replace expert judgment.

• The developer(s) assume no responsibility for conclusions
  drawn from automated analyses without proper expert validation.

By using this software, you acknowledge that you understand these
limitations and will use the results appropriately."""

        text_widget = tk.Text(text_frame, wrap=tk.WORD, font=("Arial", 10),
                              height=15, width=60, bg="#fff9e6",
                              relief=tk.SOLID, borderwidth=2)
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert("1.0", disclaimer_text)
        text_widget.config(state=tk.DISABLED)

        bottom_frame = ttk.Frame(dialog)
        bottom_frame.pack(pady=20)
        ttk.Button(bottom_frame, text="OK", command=dialog.destroy, width=15).pack()

        dialog.update_idletasks()
        width = text_widget.winfo_reqwidth() + 60
        height = text_widget.winfo_reqheight() + 150
        dialog.geometry(f"{width}x{height}")
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"+{x}+{y}")
        dialog.lift()
        dialog.focus_force()

    def show_about(self):
        about_win = tk.Toplevel(self.root)
        about_win.title("About Scientific Toolkit")
        about_win.geometry("640x660")
        about_win.resizable(True, True)
        about_win.transient(self.root)

        main = tk.Frame(about_win, padx=28, pady=12)
        main.pack(fill=tk.BOTH, expand=True)

        tk.Label(main, text="Scientific Toolkit v2.0",
                font=("TkDefaultFont", 15, "bold")).pack(pady=(0,3))
        tk.Label(main, text="(Based on Basalt Provenance Triage Toolkit v10.2)",
                font=("TkDefaultFont", 9, "italic")).pack(pady=(0,3))
        tk.Label(main, text="© 2026 Sefy Levy  •  All Rights Reserved",
                font=("TkDefaultFont", 9)).pack(pady=0)

        email = tk.Label(main, text="sefy76@gmail.com", fg="blue", cursor="hand2",
                        font=("TkDefaultFont", 9))
        email.pack(pady=0)
        email.bind("<Button-1>", lambda e: webbrowser.open("mailto:sefy76@gmail.com"))

        tk.Label(main, text="DOI: https://doi.org/10.5281/zenodo.18499129",
                fg="blue", cursor="hand2", font=("TkDefaultFont", 9)).pack(pady=0)

        tk.Label(main, text="CC BY-NC-SA 4.0 — Non-commercial research & education use",
                font=("TkDefaultFont", 9, "italic")).pack(pady=(6,4))

        tk.Label(main, text="A unified platform for scientific data analysis with plugin architecture",
                font=("TkDefaultFont", 10), wraplength=580, justify="center").pack(pady=(0,8))

        dedication_box = tk.LabelFrame(main, padx=20, pady=8,
                                    relief="groove", borderwidth=2)
        dedication_box.pack(pady=8, padx=40, fill=tk.X)

        tk.Label(dedication_box, text="Dedicated to my beloved",
                font=("TkDefaultFont", 10, "bold")).pack(pady=(0,3))
        tk.Label(dedication_box, text="Camila Portes Salles",
                font=("TkDefaultFont", 11, "italic"), fg="#8B0000").pack(pady=0)
        tk.Label(dedication_box, text="Special thanks to my sister",
                font=("TkDefaultFont", 9, "bold")).pack(pady=(6,2))
        tk.Label(dedication_box, text="Or Levy",
                font=("TkDefaultFont", 10, "italic")).pack(pady=0)
        tk.Label(dedication_box, text="In loving memory of my mother",
                font=("TkDefaultFont", 9)).pack(pady=(6,2))
        tk.Label(dedication_box, text="Chaya Levy",
                font=("TkDefaultFont", 10, "italic")).pack(pady=0)

        tk.Label(main, text="Development: Sefy Levy (2026)",
                font=("TkDefaultFont", 9)).pack(pady=(10,2))
        tk.Label(main, text="Implementation with generous help from:",
                font=("TkDefaultFont", 9)).pack(pady=0)
        tk.Label(main, text="Gemini • Copilot • ChatGPT • Claude • DeepSeek • Mistral • Grok",
                font=("TkDefaultFont", 9, "italic")).pack(pady=0)

        tk.Label(main, text="If used in research — please cite:",
                font=("TkDefaultFont", 9, "bold")).pack(pady=(10,2))

        citation = ("Levy, S. (2026). Scientific Toolkit v2.0.\n"
                   "Based on Basalt Provenance Triage Toolkit v10.2.\n"
                   "https://doi.org/10.5281/zenodo.18499129")
        tk.Label(main, text=citation, font=("TkDefaultFont", 9), justify="center").pack(pady=0)

        tk.Button(main, text="Close", width=12, command=about_win.destroy).pack(pady=(10,0))

    def show_support(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Support Scientific Toolkit")
        dialog.transient(self.root)

        main = ttk.Frame(dialog, padding=25)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="Support the Project",
                font=("TkDefaultFont", 16, "bold")).pack(pady=(0, 8))
        ttk.Label(main, text="Scientific Toolkit v2.0",
                font=("TkDefaultFont", 11)).pack()
        ttk.Label(main, text="Based on Basalt Provenance Triage Toolkit v10.2",
                font=("TkDefaultFont", 9, "italic")).pack(pady=2)
        ttk.Label(main, text="Created by Sefy Levy • 2026",
                font=("TkDefaultFont", 10)).pack(pady=4)

        email_link = ttk.Label(main, text="sefy76@gmail.com",
                            foreground="blue", cursor="hand2",
                            font=("TkDefaultFont", 9))
        email_link.pack(pady=2)
        email_link.bind("<Button-1>", lambda e: webbrowser.open("mailto:sefy76@gmail.com"))

        ttk.Label(main, text="This tool is 100% free and open-source (CC BY-NC-SA 4.0)\n"
                            "for research and educational use.",
                font=("TkDefaultFont", 9), justify="center", wraplength=400).pack(pady=(12, 20))

        ttk.Separator(main, orient="horizontal").pack(fill=tk.X, pady=15)

        ttk.Label(main, text="If this tool has saved you time,\n"
                            "helped with your research, or contributed to your work,\n"
                            "any support is deeply appreciated and goes straight back\n"
                            "into keeping it free and improving it.",
                font=("TkDefaultFont", 10), justify="center",
                wraplength=400, anchor="center").pack(pady=(0, 20))

        donate_frame = ttk.LabelFrame(main, text="Ways to Support", padding=15)
        donate_frame.pack(fill=tk.X, pady=10)

        def open_link(url):
            webbrowser.open(url)

        buttons = [
            ("Ko-fi – Buy me a coffee ☕", "https://ko-fi.com/sefy76"),
            ("PayPal.me – Quick one-time donation", "https://paypal.me/sefy76"),
            ("Liberapay – Recurring support (0% platform fee)", "https://liberapay.com/sefy76"),
        ]

        for text, url in buttons:
            btn = ttk.Button(donate_frame, text=text,
                            command=lambda u=url: open_link(u))
            btn.pack(fill=tk.X, pady=4)

        ttk.Separator(main, orient="horizontal").pack(fill=tk.X, pady=20)
        ttk.Label(main, text="Thank you for believing in open scientific tools.",
                font=("TkDefaultFont", 9, "italic")).pack(pady=(0, 15))
        ttk.Button(main, text="Close", command=dialog.destroy).pack(pady=10)

        dialog.update_idletasks()
        width = main.winfo_reqwidth() + 40
        height = main.winfo_reqheight() + 40
        dialog.geometry(f"{width}x{height}")
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"+{x}+{y}")


# ============ MAIN ============
def main():
    """Main entry point with splash screen - SINGLE TKINTER INSTANCE"""
    # Create the main root window but keep it hidden

    # Check dependencies first
    if not check_and_install_dependencies():
        # User chose to exit
        return
    root = tk.Tk()
    root.withdraw()

    # Set the messagebox parent
    set_messagebox_parent(root)

    # Create splash as a Toplevel of the main root
    splash = tk.Toplevel(root)
    splash.overrideredirect(True)

    # Center the splash
    w, h = 500, 300
    ws = splash.winfo_screenwidth()
    hs = splash.winfo_screenheight()
    x = (ws//2) - (w//2)
    y = (hs//2) - (h//2)
    splash.geometry(f"{w}x{h}+{x}+{y}")
    splash.configure(bg='#2c3e50')

    # Add splash content
    main_frame = tk.Frame(splash, bg='#2c3e50', padx=30, pady=30)
    main_frame.pack(fill=tk.BOTH, expand=True)

    tk.Label(main_frame, text="🔬", font=("Segoe UI", 48),
            bg='#2c3e50', fg='#3498db').pack(pady=(0, 10))
    tk.Label(main_frame, text="Scientific Toolkit",
            font=("Segoe UI", 18, "bold"),
            bg='#2c3e50', fg='white').pack()

    # Progress indicators
    msg_var = tk.StringVar(value="Loading components...")
    tk.Label(main_frame, textvariable=msg_var,
            font=("Segoe UI", 10),
            bg='#2c3e50', fg='#bdc3c7').pack(pady=(0, 20))

    # Use determinate progress bar with steps
    progress = ttk.Progressbar(main_frame, mode='determinate', length=400)
    progress.pack(pady=10)

    percent_var = tk.StringVar(value="0%")
    tk.Label(main_frame, textvariable=percent_var,
            font=("Segoe UI", 10, "bold"),
            bg='#2c3e50', fg='#3498db').pack()

    tk.Label(main_frame, text="v2.0",
            font=("Segoe UI", 8),
            bg='#2c3e50', fg='#7f8c8d').pack(side=tk.BOTTOM, pady=(20, 0))

    splash.update()

    # Create app with progress updates
    def create_app_with_progress():
        # Step 1: Engines
        msg_var.set("Loading engines...")
        progress['value'] = 10
        percent_var.set("10%")
        splash.update()

        # Step 2: Config
        msg_var.set("Loading configuration...")
        progress['value'] = 25
        percent_var.set("25%")
        splash.update()

        # Step 3: Create app (this will do most of the work)
        app = ScientificToolkit(root)

        # Step 4: Almost done
        msg_var.set("Finalizing...")
        progress['value'] = 90
        percent_var.set("90%")
        splash.update()

        # Step 5: Ready
        msg_var.set("Ready!")
        progress['value'] = 100
        percent_var.set("100%")
        splash.update()

        # Close splash and show main window
        splash.after(300, lambda: finish_loading(splash, root))

    # Start the app creation
    root.after(100, create_app_with_progress)

    # Start main loop
    root.mainloop()

def finish_loading(splash, root):
    """Close splash and show main window"""
    splash.destroy()
    root.deiconify()

if __name__ == "__main__":
    main()
