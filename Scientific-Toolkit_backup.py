#!/usr/bin/env python3
"""
Scientific Toolkit v2.0 - COMPATIBLE WITH EXISTING PLUGINS
"""

import tkinter as tk
from tkinter import ttk, messagebox
import importlib.util
import sys
import json
import webbrowser
import time
import csv
from pathlib import Path
from collections import defaultdict
import re

from data_hub import DataHub
from ui.left_panel import LeftPanel
from ui.center_panel import CenterPanel
from ui.right_panel import RightPanel


# ============ SPLASH SCREEN ============
class SplashScreen:
    def __init__(self):
        self.root = tk.Tk()
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
        tk.Label(main, text="Loading components...",
                font=("Segoe UI", 10),
                bg='#2c3e50', fg='#bdc3c7').pack(pady=(0, 20))

        self.progress = ttk.Progressbar(main, mode='determinate', length=400)
        self.progress.pack(pady=10)

        self.percent_var = tk.StringVar(value="0%")
        tk.Label(main, textvariable=self.percent_var,
                font=("Segoe UI", 10, "bold"),
                bg='#2c3e50', fg='#3498db').pack()

        self.msg_var = tk.StringVar(value="Initializing...")
        tk.Label(main, textvariable=self.msg_var,
                font=("Segoe UI", 9),
                bg='#2c3e50', fg='#ecf0f1').pack(pady=(10, 5))

        tk.Label(main, text="v2.0",
                font=("Segoe UI", 8),
                bg='#2c3e50', fg='#7f8c8d').pack(side=tk.BOTTOM, pady=(20, 0))
        self.root.update()

    def set_progress(self, percent, message):
        self.progress['value'] = percent
        self.percent_var.set(f"{percent}%")
        self.msg_var.set(message)
        self.root.update_idletasks()

    def close(self):
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
        self._load_chemical_elements()  # ← SINGLE SOURCE OF TRUTH
        self.color_manager = ColorManager(self.config_dir)

        # ============ CORE ============
        self.data_hub = DataHub()
        self.samples = self.data_hub.get_all()
        self.menu_bar = None
        self.advanced_menu = None
        self.current_engine_name = 'classification'
        self.current_engine = None

        # ============ PLUGIN TRACKING ============
        self.enabled_plugins = self._load_enabled_plugins()
        self.hardware_plugins = {}
        self._added_plugins = set()
        self.plot_plugin_types = []
        self._loaded_plugin_info = {}  # Stores plugin info for categorization

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

        # ============ Automatic Menu categories ============

    def _get_plugin_category(self, plugin_info):
        """Determine plugin category based on keywords and name - PRECISION VERSION"""
        name = plugin_info.get('name', '').lower()
        desc = plugin_info.get('description', '').lower()
        plugin_id = plugin_info.get('id', '').lower()

        # Combine all text for searching
        search_text = f"{name} {desc} {plugin_id}"

        # ============ EXCLUSIVE CATEGORIES WITH SPECIFIC KEYWORDS ============
        categories = [
            {
                'name': '🧪 Geochemistry',
                'keywords': [
                    'geochem', 'normalization', 'normative', 'hg', 'mobility',
                    'element', 'trace', 'major', 'oxide', 'la-icp-ms', 'laicpms',
                    'icp', 'spectral', 'geoexplorer', 'geochemical', 'xrf', 'pXRF',
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

        # Check each category
        for category in categories:
            if any(keyword in search_text for keyword in category['keywords']):
                print(f"  → Categorized '{name}' as {category['name']}")
                return category['name']

        # Default category
        print(f"  → No category match for '{name}', using '📁 Other'")
        return '📁 Other'

    def _rebuild_advanced_menu(self):
        """Rebuild the Advanced menu with categorized submenus - ALPHABETICALLY SORTED"""
        # Clear existing advanced menu
        self.advanced_menu.delete(0, tk.END)

        # Group plugins by category
        plugins_by_category = defaultdict(list)

        # Go through all loaded plugins and categorize them
        for plugin_id, plugin_info in self._loaded_plugin_info.items():
            category = self._get_plugin_category(plugin_info)
            plugins_by_category[category].append({
                'name': plugin_info.get('name', plugin_id),
                'icon': plugin_info.get('icon', '🔧'),
                'command': plugin_info['command'],
                'id': plugin_id
            })

        # ============ ALPHABETICAL SORTING ============
        # Sort categories alphabetically (ignoring emojis)
        sorted_categories = sorted(
            plugins_by_category.keys(),
            key=lambda x: x.split(' ', 1)[-1] if ' ' in x else x  # Sort by text after emoji
        )

        for category in sorted_categories:
            # Skip empty categories
            if not plugins_by_category[category]:
                continue

            # Create submenu for this category
            submenu = tk.Menu(self.advanced_menu, tearoff=0)
            self.advanced_menu.add_cascade(label=category, menu=submenu)

            # ============ ALPHABETICAL SORTING OF PLUGINS ============
            # Sort plugins by name within category
            sorted_plugins = sorted(
                plugins_by_category[category],
                key=lambda x: x['name'].lower()  # Case-insensitive sort
            )

            # Add plugins to submenu
            for plugin in sorted_plugins:
                label = plugin['name']
                if plugin['icon']:
                    label = f"{plugin['icon']} {label}"

                submenu.add_command(
                    label=label,
                    command=plugin['command']
                )

        # Optional: Add a separator and "Refresh" option at the bottom
        if sorted_categories:
            self.advanced_menu.add_separator()
            self.advanced_menu.add_command(
                label="🔄 Refresh Categories",
                command=self._rebuild_advanced_menu
            )
    # ============ ENGINE INIT ============
    def _load_initial_engines(self):
        engines = self.engine_manager.get_available_engines()
        if 'classification' in engines:
            self.classification_engine = self.engine_manager.load_engine('classification')
        if 'protocol' in engines:
            self.protocol_engine = self.engine_manager.load_engine('protocol')

    # ============ MASTER CONFIG ============
    def _load_chemical_elements(self):
        """SINGLE source of truth for all column mappings"""
        elements_file = self.config_dir / "chemical_elements.json"
        if elements_file.exists():
            try:
                with open(elements_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.chemical_elements = data.get("elements", {})
                    self.ui_groups = data.get("ui_groups", {})

                    # Build reverse lookup
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

    def _load_enabled_plugins(self):
        config_file = Path("config/enabled_plugins.json")
        if config_file.exists():
            try:
                with open(config_file) as f:
                    return json.load(f)
            except:
                return {}
        return {}

    # ============ COLUMN NORMALIZATION ============
    def normalize_columns(self, row_dict):
        """Master column normalizer - uses chemical_elements.json"""
        normalized = {}
        notes_parts = []
        seen_standards = set()

        # Handle Sample_ID
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

        # DEBUG: Print raw columns
        print(f"\n🔍 RAW COLUMNS: {list(row_dict.keys())}")

        # Process all other columns
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

        # Handle Notes
        if 'Notes' in row_dict and row_dict['Notes']:
            existing = str(row_dict['Notes']).strip()
            if existing and existing.lower() != 'nan':
                notes_parts.insert(0, existing)

        normalized['Notes'] = ' | '.join(notes_parts) if notes_parts else ''
        print(f"  ✅ FINAL STANDARDS: {list(normalized.keys())}\n")
        return normalized

    def validate_plugin_data(self, data_rows):
        """Import and normalize data from plugins/CSV"""
        if not data_rows:
            return []

        print(f"\n📥 Importing {len(data_rows)} rows...")
        filtered_rows = []

        for row in data_rows:
            normalized = self.normalize_columns(row)
            filtered_rows.append(normalized)

        print(f"✅ Imported {len(filtered_rows)} rows")
        return filtered_rows

    def import_data_from_plugin(self, data_rows):
        """Plugins call this to import data"""
        if not data_rows:
            return
        filtered = self.validate_plugin_data(data_rows)
        if filtered:
            self.data_hub.add_samples(filtered)
            self.samples = self.data_hub.get_all()

    # ============ MENU ============
    def _create_menu_structure(self):
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Import CSV...", command=lambda: self.left.import_csv())
        self.file_menu.add_command(label="Import Excel...", command=lambda: self.left.import_csv())
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Export CSV...", command=self._export_csv)
        self.file_menu.add_command(label="Exit", command=self.root.quit)

        self.tools_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Tools", menu=self.tools_menu)
        self.tools_menu.add_command(label="Plugin Manager", command=self._open_plugin_manager)

        self.engine_menu = tk.Menu(self.tools_menu, tearoff=0)
        self.tools_menu.add_cascade(label="🔧 Switch Engine", menu=self.engine_menu)

        self.advanced_menu = tk.Menu(self.menu_bar, tearoff=0)

        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.help_menu.add_command(label="Allowed Columns", command=self.show_allowed_columns)
        self.help_menu.add_separator()
        self.help_menu.add_command(label="⚠️ Disclaimer", command=self.show_disclaimer)
        self.help_menu.add_command(label="About", command=self.show_about)
        self.help_menu.add_command(label="❤️ Support the Project", command=self.show_support)

    def _export_csv(self):
        samples = self.data_hub.get_all()
        if not samples:
            messagebox.showwarning("No Data", "No data to export")
            return
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if path:
            try:
                with open(path, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=self.data_hub.get_column_names())
                    writer.writeheader()
                    writer.writerows(samples)
                messagebox.showinfo("Success", f"Exported {len(samples)} rows")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _open_plugin_manager(self):
        try:
            from plugins.plugin_manager import PluginManager
            PluginManager(self)
        except ImportError as e:
            messagebox.showerror("Error", f"Plugin Manager not found: {e}")

    def _update_status(self, message):
        print(f"Status: {message}")
        self.root.update_idletasks()

    # ============ UI ============
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

    def _build_bottom_controls(self):
        bottom = ttk.Frame(self.root, relief=tk.SUNKEN, borderwidth=1)
        bottom.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=5)

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

        sel = ttk.Frame(bottom)
        sel.pack(side=tk.RIGHT, padx=5, pady=2)

        ttk.Button(sel, text="Select All", command=self.center.select_all, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(sel, text="Deselect", command=self.center.deselect_all, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(sel, text="🗑️ Delete", command=self._delete_selected, width=8).pack(side=tk.LEFT, padx=2)
        self.sel_label = tk.Label(sel, text="Selected: 0", font=("Arial", 9, "bold"))
        self.sel_label.pack(side=tk.LEFT, padx=10)

    def _delete_selected(self):
        selected = self.center.get_selected_indices()
        if selected and messagebox.askyesno("Confirm", f"Delete {len(selected)} selected row(s)?"):
            self.data_hub.delete_rows(selected)
            self.samples = self.data_hub.get_all()

    def auto_size_columns(self, tree, samples, force=False):  # Add force parameter with default value
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

    # ============ ENGINE MANAGEMENT ============
    def _refresh_engine_menu(self):
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

    # ============ PLUGIN LOADING ============
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

        # Hardware plugins
        hw_dir = Path("plugins/hardware")
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

        # Software plugins
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
                            if plugin_id not in self._added_plugins:
                                self._add_to_advanced_menu(info, plugin_instance)
                                self._added_plugins.add(plugin_id)

                            # AI plugins
                            plugin_name = info.get('name', '').lower()
                            plugin_id_lower = plugin_id.lower()
                            plugin_desc = info.get('description', '').lower()
                            ai_keywords = ['ai', 'assistant', 'chat', 'gemini', 'claude',
                                         'grok', 'deepseek', 'ollama', 'copilot', 'chatgpt']
                            is_ai = any(kw in plugin_name or kw in plugin_id_lower or kw in plugin_desc
                                      for kw in ai_keywords)
                            if is_ai and hasattr(plugin_instance, 'query'):
                                self.center.add_ai_plugin(
                                    plugin_name=info.get('name', plugin_id),
                                    plugin_icon=info.get('icon', '🤖'),
                                    plugin_instance=plugin_instance
                                )
                except Exception as e:
                    print(f"❌ Failed to load {py_file.name}: {e}")

        if self.plot_plugin_types:
            self.center.update_plot_types(self.plot_plugin_types)

        if software_loaded and self._loaded_plugin_info:
            # Rebuild the advanced menu with categories
            self._rebuild_advanced_menu()
            self.menu_bar.add_cascade(label="Advanced", menu=self.advanced_menu)
        self.menu_bar.add_cascade(label="Help", menu=self.help_menu)

    def _debug_show_categorization(self):
        """Show how plugins were categorized"""
        print("\n" + "="*60)
        print("PLUGIN CATEGORIZATION RESULTS")
        print("="*60)

        # Group by category
        by_category = defaultdict(list)
        for plugin_id, info in self._loaded_plugin_info.items():
            category = self._get_plugin_category(info)
            by_category[category].append(info['name'])

        for category, plugins in sorted(by_category.items()):
            print(f"\n{category}:")
            for plugin in sorted(plugins):
                print(f"  • {plugin}")

        print("="*60)

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
            # Store plugin info for later categorization
            self._loaded_plugin_info[plugin_id] = {
                'name': name,
                'icon': icon,
                'command': open_method,
                'id': plugin_id,
                'description': info.get('description', ''),
                'category': info.get('menu_category', '')  # Optional: plugin can specify its own category
            }
            self._added_plugins.add(plugin_id)

            # DEBUG: Print plugin info
            print(f"📦 Loaded plugin: {name} (ID: {plugin_id})")
            print(f"   Description: {info.get('description', '')[:50]}...")

    # ============ DIALOGS ============
    def show_allowed_columns(self):
        """Display standardized columns from chemical_elements.json"""
        from tkinter import scrolledtext

        win = tk.Toplevel(self.root)
        win.title("🔬 Standardized Columns")
        win.geometry("600x500")

        text = scrolledtext.ScrolledText(win, wrap=tk.WORD, font=("Courier", 9))
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        text.insert(tk.END, "STANDARDIZED COLUMN NAMES\n")
        text.insert(tk.END, "="*50 + "\n\n")
        text.insert(tk.END, f"Source: chemical_elements.json\n\n")

        # Group by ui_groups from the JSON
        groups = getattr(self, 'ui_groups', {})
        if not groups:
            text.insert(tk.END, "No groups defined in chemical_elements.json")
        else:
            for group_name, columns in groups.items():
                text.insert(tk.END, f"\n{group_name}:\n", "group")
                text.insert(tk.END, "-"*30 + "\n")
                for col in sorted(columns):
                    # Find display name
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
# ============ MODIFIED MAIN ============
def main():
    # Create main root
    root = tk.Tk()
    root.withdraw()  # Hide it

    # Create splash as Toplevel
    splash = tk.Toplevel(root)
    splash.overrideredirect(True)

    # Center the splash screen
    w, h = 500, 300
    ws = splash.winfo_screenwidth()
    hs = splash.winfo_screenheight()
    x = (ws//2) - (w//2)
    y = (hs//2) - (h//2)
    splash.geometry(f"{w}x{h}+{x}+{y}")
    splash.configure(bg='#2c3e50')

    # Add content
    main_frame = tk.Frame(splash, bg='#2c3e50', padx=30, pady=30)
    main_frame.pack(fill=tk.BOTH, expand=True)

    tk.Label(main_frame, text="🔬", font=("Segoe UI", 48),
            bg='#2c3e50', fg='#3498db').pack(pady=(0, 10))
    tk.Label(main_frame, text="Scientific Toolkit",
            font=("Segoe UI", 18, "bold"),
            bg='#2c3e50', fg='white').pack()
    tk.Label(main_frame, text="Loading...",
            font=("Segoe UI", 10),
            bg='#2c3e50', fg='#bdc3c7').pack(pady=(0, 20))

    progress = ttk.Progressbar(main_frame, mode='indeterminate', length=400)
    progress.pack(pady=10)
    progress.start(10)

    splash.update()

    # Create application (this loads everything)
    app = ScientificToolkit(root)

    # Close splash and show main window
    progress.stop()
    splash.destroy()
    root.deiconify()

    # Start main loop
    root.mainloop()

if __name__ == "__main__":
    main()
