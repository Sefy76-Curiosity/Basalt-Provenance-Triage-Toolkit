"""
Plugin Manager v2.0 - Unified Store with Remote & Local Merged View
Author: Sefy Levy

3 TABS · 3 CATEGORIES · SMART TOGGLE · REAL REMOVAL · SECURE INSTALL · UNINSTALL · REMOTE STORE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ CHECK → Enable + Add to menu
✗ UNCHECK → Disable + REMOVE FROM MENU instantly
⚡ Smart button: ENABLE N / DISABLE N
🛡️ SHA‑256 verification for downloaded plugins (if provided)
🗑️ Uninstall button deletes the local file completely
⚙️ Missing dependencies are detected and installed on demand
🌐 Remote plugins appear with INSTALL / UPDATE buttons
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

PLUGIN_MANAGER_INFO = {
    "id": "plugin_manager",
    "name": "🔌 Plugin Manager",
    "version": "2.0",
    "author": "Sefy Levy"
}

import tkinter as tk
from tkinter import ttk, messagebox
import json
import subprocess
import threading
import importlib.util
import ast
import sys
from pathlib import Path
import urllib.request
import urllib.error
import hashlib
import logging
import tempfile
import random
import os
from typing import Optional, Dict, List, Any, Tuple

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path("config") / "plugin_manager.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("PluginManager")

# Try to import packaging for robust version comparison
try:
    from packaging.version import Version
    HAS_PACKAGING = True
except ImportError:
    HAS_PACKAGING = False
    logger.warning("packaging not installed; using simple version comparison")


class PluginManager(tk.Toplevel):
    # --- Constants ---
    WINDOW_SIZE = "620x500"
    MIN_SIZE = (580, 450)
    COLORS = {
        "header_bg": "#2c3e50",
        "tab_bg": "#34495e",
        "tab_fg_active": "white",
        "tab_fg_inactive": "#bdc3c7",
        "content_bg": "white",
        "footer_bg": "#ecf0f1",
        "footer_fg": "#7f8c8d",
        "success": "#27ae60",
        "warning": "#e67e22",
        "danger": "#e74c3c",
        "info": "#3498db",
        "install_deps": "#f39c12",
    }
    FONTS = {
        "header": ("Arial", 12, "bold"),
        "tab": ("Arial", 11, "bold"),
        "plugin_title": ("Arial", 10, "bold"),
        "plugin_desc": ("Arial", 8),
        "plugin_meta": ("Arial", 7),
        "button": ("Arial", 8, "bold"),
        "status": ("Arial", 9),
    }
    PADDING = {"small": 2, "medium": 5, "large": 10}

    # Comprehensive import name → pip package name
    IMPORT_MAPPING = {
        "google-generativeai": "google.generativeai",
        "numpy": "numpy",
        "pandas": "pandas",
        "matplotlib": "matplotlib",
        "scipy": "scipy",
        "scikit-learn": "sklearn",
        "scikit-image": "skimage",
        "opencv-python": "cv2",
        "opencv-contrib-python": "cv2",
        "pyserial": "serial",
        "pillow": "PIL",
        "ctypes": "ctypes",
        "umap-learn": "umap",
        "python-docx": "docx",
        "simplekml": "simplekml",
        "pyvista": "pyvista",
        "geopandas": "geopandas",
        "pynmea2": "pynmea2",
        "watchdog": "watchdog",
        "pythonnet": "clr",
        "earthengine-api": "ee",
        "pybaselines": "pybaselines",
        "lmfit": "lmfit",
        "contextily": "contextily",
        "shapely": "shapely",
        "pyproj": "pyproj",
        "descartes": "descartes",
        "mapclassify": "mapclassify",
        "rasterio": "rasterio",
        "rioxarray": "rioxarray",
        "osmnx": "osmnx",
        "trimesh": "trimesh",
        "emcee": "emcee",
        "corner": "corner",
        "joblib": "joblib",
        "openpyxl": "openpyxl",
        "pyrolite": "pyrolite",
        "seaborn": "seaborn",
        "missingno": "missingno",
        "bs4": "bs4",
        "requests": "requests",
        "anthropic": "anthropic",
        "openai": "openai",
    }

    STORE_INDEX_URL = "https://gitlab.com/sefy76/scientific-toolkit/-/raw/main/plugins/plugins.json?ref_type=heads&nocache=" + str(random.random())

    def __init__(self, parent_app):
        super().__init__(parent_app.root)
        self.app = parent_app

        self.title("🔌 Plugin Manager v2.0")
        self.geometry(self.WINDOW_SIZE)
        self.minsize(*self.MIN_SIZE)
        self.transient(parent_app.root)

        # Ensure config directory exists
        self.config_dir = Path("config")
        self.config_dir.mkdir(exist_ok=True)

        # Plugin registry files
        self.enabled_file = self.config_dir / "enabled_plugins.json"

        # Local plugins
        self.local_plugins_by_category: Dict[str, List[Dict]] = self._discover_all()
        self._ensure_local_index()
        self.enabled_plugins: Dict[str, bool] = self._load_enabled()
        self.plugin_vars: Dict[str, tk.BooleanVar] = {}      # only for local plugins
        self.plugin_rows: Dict[str, tk.Frame] = {}

        # Remote plugins (will be fetched)
        self.remote_plugins_by_category: Dict[str, List[Dict]] = {"add-ons": [], "software": [], "hardware": []}
        self.remote_fetched = False
        self.remote_fetch_failed = False
        self._fetch_lock = threading.Lock()
        self._fetching = False

        self._build_ui()
        self._update_button_state()
        self._center_window()
        self._safe_grab()

        # Start fetching remote index in background
        self._fetch_remote_index()

    def _safe_grab(self):
        """Attempt to set grab, but don't crash if another window has it."""
        try:
            self.grab_set()
        except tk.TclError as e:
            logger.warning(f"Could not set grab: {e} – another window may be modal.")

    # ────────────────────────────────────────────────────────────
    # DISCOVERY · READ ONLY · NO MENU CREATION
    # ────────────────────────────────────────────────────────────
    def _discover_all(self) -> Dict[str, List[Dict]]:
        categories = {"add-ons": [], "software": [], "hardware": []}
        folder_map = {
            "add-ons": Path("plugins/add-ons"),
            "software": Path("plugins/software"),
            "hardware": Path("plugins/hardware")
        }
        for category, folder in folder_map.items():
            if not folder.exists():
                folder.mkdir(parents=True, exist_ok=True)
                continue
            print(f"\n🔍 Scanning {folder}...")
            for py_file in folder.glob("*.py"):
                if py_file.stem in ["__init__", "plugin_manager"]:
                    continue
                print(f"  📄 Found: {py_file.name}")
                info = self._extract_info(py_file, category)
                if info:
                    categories[category].append(info)
                    print(f"    ✅ Extracted: {info.get('name')}")
                else:
                    print(f"    ❌ EXTRACTION FAILED for {py_file.name}")
                    # Add fallback entry
                    categories[category].append({
                        'id': py_file.stem,
                        'name': py_file.stem.replace('_', ' ').title(),
                        'category': category,
                        'icon': '📦',
                        'version': '?',
                        'requires': [],
                        'description': 'Local plugin (metadata could not be read)',
                        'path': str(py_file),
                        'module': py_file.stem,
                        'broken': True
                    })
        return categories

    def _extract_info(self, py_file: Path, default_category: str) -> Optional[Dict]:
        """Extract PLUGIN_INFO via import (preferred) or AST fallback."""
        # Method 1: Import (preferred)
        try:
            spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, 'PLUGIN_INFO'):
                info = module.PLUGIN_INFO.copy()
                info['category'] = default_category
                info['path'] = str(py_file)
                info['module'] = py_file.stem
                return info
        except Exception as e:
            logger.debug(f"Import failed for {py_file}: {e}")

        # Method 2: AST fallback
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == 'PLUGIN_INFO':
                            info = ast.literal_eval(node.value)
                            info['category'] = default_category
                            info['path'] = str(py_file)
                            info['module'] = py_file.stem
                            return info
        except Exception as e:
            logger.debug(f"AST parse failed for {py_file}: {e}")

        return None

    # ────────────────────────────────────────────────────────────
    # REMOTE INDEX FETCH (thread-safe)
    # ────────────────────────────────────────────────────────────
    def _fetch_remote_index(self):
        """Fetch remote plugin index in background."""
        with self._fetch_lock:
            if self._fetching:
                return
            self._fetching = True
            self.remote_fetch_failed = False

        def fetch():
            try:
                logger.info("Fetching remote plugin index...")
                with urllib.request.urlopen(self.STORE_INDEX_URL, timeout=10) as response:
                    data = response.read().decode('utf-8')
                    all_remote = json.loads(data)
                # Organise by category, excluding the plugin manager itself
                for cat in self.remote_plugins_by_category:
                    self.remote_plugins_by_category[cat] = [
                        p for p in all_remote if p.get('category') == cat and p.get('id') != 'plugin_manager'
                    ]
                self.remote_fetched = True
                logger.info(f"Fetched {len(all_remote)} remote plugins")
                self.after(0, lambda: self._refresh_category(self.category_var.get()))
            except Exception as e:
                logger.error(f"Failed to fetch remote index: {e}")
                self.remote_fetch_failed = True
                self.after(0, lambda: self.status_var.set("🌐 Remote store unavailable"))
            finally:
                with self._fetch_lock:
                    self._fetching = False

        threading.Thread(target=fetch, daemon=True).start()

    # ────────────────────────────────────────────────────────────
    # STATE MANAGEMENT
    # ────────────────────────────────────────────────────────────
    def _load_enabled(self) -> Dict[str, bool]:
        if self.enabled_file.exists():
            try:
                with open(self.enabled_file) as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load enabled plugins: {e}")
                return {}
        return {}

    def _save_enabled(self) -> Dict[str, bool]:
        enabled = {pid: var.get() for pid, var in self.plugin_vars.items()}
        # Atomic write to temp file
        temp = self.enabled_file.with_suffix(".tmp")
        try:
            with open(temp, 'w') as f:
                json.dump(enabled, f, indent=2)
            temp.replace(self.enabled_file)
        except Exception as e:
            logger.error(f"Failed to save enabled plugins: {e}")
        return enabled

    # ────────────────────────────────────────────────────────────
    # DEPENDENCY CHECK
    # ────────────────────────────────────────────────────────────
    def _check_deps(self, requires: List[str]) -> Tuple[bool, List[str]]:
        if not requires:
            return True, []
        missing = []
        for pkg in requires:
            if pkg == 'ctypes':
                continue
            import_name = self.IMPORT_MAPPING.get(pkg, pkg)
            try:
                if importlib.util.find_spec(import_name) is None:
                    missing.append(pkg)
            except Exception:
                missing.append(pkg)
        return len(missing) == 0, missing

    def _install_deps(self, plugin_name: str, packages: List[str]):
        """Spawn pip install in a non-blocking window, then refresh category."""
        win = tk.Toplevel(self)
        win.title(f"📦 Installing: {plugin_name}")
        win.geometry("600x400")
        win.transient(self)

        header = tk.Frame(win, bg=self.COLORS["info"], height=32)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text=f"pip install {' '.join(packages)}",
                font=("Consolas", 9), bg=self.COLORS["info"], fg="white").pack(pady=6)

        text = tk.Text(win, wrap=tk.WORD, font=("Consolas", 9),
                      bg="#1e1e1e", fg="#d4d4d4")
        scroll = tk.Scrollbar(win, command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=5)

        def run():
            text.insert(tk.END, f"$ pip install {' '.join(packages)}\n\n")
            proc = subprocess.Popen(
                [sys.executable, "-m", "pip", "install"] + packages,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            for line in proc.stdout:
                text.insert(tk.END, line)
                text.see(tk.END)
                win.update()
            proc.wait()
            if proc.returncode == 0:
                text.insert(tk.END, "\n✅ SUCCESS! Dependencies installed.\n")
                text.insert(tk.END, "Refreshing view...\n")
                self.after(0, lambda: self._refresh_category(self.category_var.get()))
            else:
                text.insert(tk.END, f"\n❌ FAILED (code {proc.returncode})\n")

        threading.Thread(target=run, daemon=True).start()

    # ────────────────────────────────────────────────────────────
    # UI · 3 TABS · UNIFIED LOCAL + REMOTE
    # ────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=self.COLORS["header_bg"], height=40)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text="🔌", font=("Arial", 16),
                bg=self.COLORS["header_bg"], fg="white").pack(side=tk.LEFT, padx=10)
        tk.Label(header, text="PLUGIN MANAGER v2.0", font=self.FONTS["header"],
                bg=self.COLORS["header_bg"], fg="white").pack(side=tk.LEFT, padx=5)

        # Tabs
        tab_frame = tk.Frame(self, bg=self.COLORS["tab_bg"], height=45)
        tab_frame.pack(fill=tk.X)
        tab_frame.pack_propagate(False)
        tab_frame.columnconfigure(0, weight=1)
        tab_frame.columnconfigure(1, weight=1)
        tab_frame.columnconfigure(2, weight=1)

        self.category_var = tk.StringVar(value="add-ons")

        self.btn_addons = tk.Button(tab_frame, text="🎨 ADD-ONS",
                                   font=self.FONTS["tab"],
                                   bg=self.COLORS["header_bg"], fg=self.COLORS["tab_fg_active"],
                                   relief=tk.FLAT,
                                   command=lambda: self._switch_category("add-ons"))
        self.btn_addons.grid(row=0, column=0, sticky="nsew", padx=1, pady=2)

        self.btn_software = tk.Button(tab_frame, text="📦 SOFTWARE",
                                     font=self.FONTS["tab"],
                                     bg=self.COLORS["tab_bg"], fg=self.COLORS["tab_fg_inactive"],
                                     relief=tk.FLAT,
                                     command=lambda: self._switch_category("software"))
        self.btn_software.grid(row=0, column=1, sticky="nsew", padx=1, pady=2)

        self.btn_hardware = tk.Button(tab_frame, text="🔌 HARDWARE",
                                     font=self.FONTS["tab"],
                                     bg=self.COLORS["tab_bg"], fg=self.COLORS["tab_fg_inactive"],
                                     relief=tk.FLAT,
                                     command=lambda: self._switch_category("hardware"))
        self.btn_hardware.grid(row=0, column=2, sticky="nsew", padx=1, pady=2)

        # Content area
        self.content_frame = tk.Frame(self, bg=self.COLORS["content_bg"])
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Frames for each category
        self.frames = {
            "add-ons": tk.Frame(self.content_frame, bg=self.COLORS["content_bg"]),
            "software": tk.Frame(self.content_frame, bg=self.COLORS["content_bg"]),
            "hardware": tk.Frame(self.content_frame, bg=self.COLORS["content_bg"])
        }

        # Show default category
        self._switch_category("add-ons")

        # Footer
        footer = tk.Frame(self, bg=self.COLORS["footer_bg"], height=55)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)
        self.status_var = tk.StringVar(value="⚡ Ready")
        status = tk.Label(footer, textvariable=self.status_var,
                         font=self.FONTS["status"], bg=self.COLORS["footer_bg"], fg=self.COLORS["footer_fg"])
        status.pack(side=tk.LEFT, padx=15)
        self.action_btn = tk.Button(footer, text="✅ APPLY CHANGES",
                                   font=self.FONTS["tab"],
                                   bg=self.COLORS["success"], fg="white",
                                   padx=25, pady=8,
                                   command=self._apply)
        self.action_btn.pack(side=tk.RIGHT, padx=15, pady=8)

    def _switch_category(self, category: str):
        """Switch between categories - repopulates the view with merged local+remote."""
        self.category_var.set(category)
        # Update button colors
        self.btn_addons.config(bg=self.COLORS["header_bg"] if category == "add-ons" else self.COLORS["tab_bg"],
                              fg=self.COLORS["tab_fg_active"] if category == "add-ons" else self.COLORS["tab_fg_inactive"])
        self.btn_software.config(bg=self.COLORS["header_bg"] if category == "software" else self.COLORS["tab_bg"],
                                fg=self.COLORS["tab_fg_active"] if category == "software" else self.COLORS["tab_fg_inactive"])
        self.btn_hardware.config(bg=self.COLORS["header_bg"] if category == "hardware" else self.COLORS["tab_bg"],
                                fg=self.COLORS["tab_fg_active"] if category == "hardware" else self.COLORS["tab_fg_inactive"])

        # Hide all frames, then show and repopulate the selected one
        for cat, frame in self.frames.items():
            if cat == category:
                # Clear the frame and repopulate
                for widget in frame.winfo_children():
                    widget.destroy()
                self._populate_merged_category(frame, category)
                frame.pack(fill=tk.BOTH, expand=True)
            else:
                frame.pack_forget()

    def _refresh_category(self, category: str):
        """Rebuild the view for a specific category (used after updates)."""
        self._switch_category(category)

    def _get_merged_plugins(self, category: str) -> List[Dict]:
        """Combine local and remote plugins for a category."""
        local_dict = {p['id']: p for p in self.local_plugins_by_category.get(category, [])}
        remote_dict = {p['id']: p for p in self.remote_plugins_by_category.get(category, [])}

        print(f"\n=== DEBUG {category} ===")
        print(f"Local plugins ({len(local_dict)}): {sorted(local_dict.keys())}")
        print(f"Remote plugins ({len(remote_dict)}): {sorted(remote_dict.keys())}")

        # Check a specific problematic plugin
        test_plugins = ['geoplot_pro', 'ague_hg_mobility', 'quartz_gis_pro']
        for pid in test_plugins:
            in_local = pid in local_dict
            in_remote = pid in remote_dict
            print(f"\n🔍 Checking {pid}:")
            print(f"  - In local: {in_local}")
            print(f"  - In remote: {in_remote}")

            if in_local:
                local_info = local_dict[pid]
                print(f"  - Local version: {local_info.get('version')}")
                print(f"  - Local category: {local_info.get('category')}")
            if in_remote:
                remote_info = remote_dict[pid]
                print(f"  - Remote version: {remote_info.get('version')}")
                print(f"  - Remote category: {remote_info.get('category')}")

        merged = []
        for pid, info in local_dict.items():
            merged.append({
                'id': pid,
                'local': info,
                'remote': remote_dict.get(pid),
                'type': 'local'
            })

        for pid, info in remote_dict.items():
            if pid not in local_dict:
                merged.append({
                    'id': pid,
                    'local': None,
                    'remote': info,
                    'type': 'remote'
                })

        return merged

    def _populate_merged_category(self, parent, category: str):
        """Populate a category frame with merged local+remote plugins."""
        merged = self._get_merged_plugins(category)
        if not merged:
            empty = tk.Frame(parent, bg=self.COLORS["content_bg"])
            empty.pack(fill=tk.BOTH, expand=True)
            tk.Label(empty, text="✨ No plugins found",
                    font=("Arial", 11), bg=self.COLORS["content_bg"], fg="#95a5a6").pack(expand=True)
            return

        # Canvas + Scrollbar
        canvas = tk.Canvas(parent, bg=self.COLORS["content_bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=self.COLORS["content_bg"])

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw", width=canvas.winfo_width())

        def _on_canvas_configure(event):
            canvas.itemconfig(1, width=event.width)
        canvas.bind("<Configure>", _on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)

        # Mouse wheel
        def _on_mousewheel(event):
            if event.delta:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            else:
                if event.num == 4:
                    canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    canvas.yview_scroll(1, "units")
        def _on_enter(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            canvas.bind_all("<Button-4>", _on_mousewheel)
            canvas.bind_all("<Button-5>", _on_mousewheel)
        def _on_leave(event):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")
        canvas.bind("<Enter>", _on_enter)
        canvas.bind("<Leave>", _on_leave)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create rows
        for plugin in merged:
            self._create_unified_row(scroll_frame, plugin)

    def _create_unified_row(self, parent, plugin: Dict):
        """Create a single row for a plugin (may be local, remote, or both)."""
        local_info = plugin['local']
        remote_info = plugin['remote']
        pid = plugin['id']

        # Determine display name, icon, etc.
        if local_info:
            name = local_info.get('name', pid)
            icon = local_info.get('icon', '📦')
            local_version = local_info.get('version', '0.0.0')
            author = local_info.get('author', 'Unknown')
            description = local_info.get('description', '')
            requires = local_info.get('requires', [])
            is_broken = local_info.get('broken', False)
        else:
            name = remote_info.get('name', pid)
            icon = remote_info.get('icon', '📦')
            local_version = None
            author = remote_info.get('author', 'Unknown')
            description = remote_info.get('description', '')
            requires = remote_info.get('requires', [])
            is_broken = False

        remote_version = remote_info.get('version') if remote_info else None

        # Row container
        row = tk.Frame(parent, bg=self.COLORS["content_bg"], relief=tk.GROOVE, borderwidth=1)
        row.pack(fill=tk.X, padx=3, pady=2)
        self.plugin_rows[pid] = row

        # Left side (main info)
        left = tk.Frame(row, bg=self.COLORS["content_bg"])
        left.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8, pady=6)

        # Title with version(s)
        if local_info and remote_version:
            title_text = f"{icon} {name}  v{local_version}  (remote v{remote_version})"
        elif local_info:
            title_text = f"{icon} {name}  v{local_version}"
        elif remote_version:
            title_text = f"{icon} {name}  v{remote_version}"
        else:
            title_text = f"{icon} {name}"

        if is_broken:
            title_text = f"⚠️ {title_text} (broken)"

        tk.Label(left, text=title_text, font=self.FONTS["plugin_title"],
                 bg=self.COLORS["content_bg"], anchor="w").pack(anchor=tk.W)

        # Description
        if description:
            tk.Label(left, text=f"  {description}", font=self.FONTS["plugin_desc"],
                     fg="#5e6c84", bg=self.COLORS["content_bg"], anchor="w").pack(anchor=tk.W)

        # Author
        tk.Label(left, text=f"  by {author}", font=self.FONTS["plugin_meta"],
                 fg="#7f8c8d", bg=self.COLORS["content_bg"], anchor="w").pack(anchor=tk.W)

        # Dependencies (right side)
        if requires:
            deps_frame = tk.Frame(row, bg=self.COLORS["content_bg"])
            deps_frame.pack(side=tk.RIGHT, padx=10)

            met, missing = self._check_deps(requires)

            if met:
                tk.Label(deps_frame, text="✓✓", font=("Arial", 9),
                        fg=self.COLORS["success"], bg=self.COLORS["content_bg"]).pack(side=tk.LEFT, padx=2)
                deps_text = ", ".join(requires[:2])
                if len(requires) > 2:
                    deps_text += f" +{len(requires)-2}"
                tk.Label(deps_frame, text=deps_text,
                        font=self.FONTS["plugin_meta"], fg=self.COLORS["success"],
                        bg=self.COLORS["content_bg"]).pack(side=tk.LEFT)
            else:
                tk.Label(deps_frame, text="⚠️", font=("Arial", 9),
                        fg=self.COLORS["warning"], bg=self.COLORS["content_bg"]).pack(side=tk.LEFT, padx=2)
                tk.Label(deps_frame, text=f"missing: {missing[0]}",
                        font=self.FONTS["plugin_meta"], fg=self.COLORS["warning"],
                        bg=self.COLORS["content_bg"]).pack(side=tk.LEFT)

                btn = tk.Button(deps_frame, text="INSTALL DEPS",
                               font=self.FONTS["button"],
                               bg=self.COLORS["install_deps"], fg="white",
                               padx=6, pady=0,
                               command=lambda pname=name, pkgs=missing: self._install_deps(pname, pkgs))
                btn.pack(side=tk.LEFT, padx=5)

        # Rightmost actions
        action_frame = tk.Frame(row, bg=self.COLORS["content_bg"])
        action_frame.pack(side=tk.RIGHT, padx=10)

        if local_info:
            # Local plugin: add checkbox for enable/disable
            if not is_broken:
                var = tk.BooleanVar(value=self.enabled_plugins.get(pid, False))
                var.trace('w', lambda *args: self._update_button_state())
                self.plugin_vars[pid] = var
                cb = tk.Checkbutton(action_frame, text="", variable=var,
                                   bg=self.COLORS["content_bg"])
                cb.pack(side=tk.LEFT, padx=2)

                # If remote version exists and is newer, show Update button
                if remote_version and self._is_newer(remote_version, local_version):
                    update_btn = tk.Button(action_frame, text="UPDATE", font=self.FONTS["button"],
                                           bg=self.COLORS["warning"], fg="white", padx=8, pady=0,
                                           command=lambda: self._install_from_store(remote_info, update=True))
                    update_btn.pack(side=tk.LEFT, padx=5)
                else:
                    tk.Label(action_frame, text="✓ INSTALLED", font=self.FONTS["button"],
                             fg=self.COLORS["success"], bg=self.COLORS["content_bg"]).pack(side=tk.LEFT, padx=5)
            else:
                # Broken plugin: show warning instead of checkbox
                tk.Label(action_frame, text="⚠️ Broken", font=self.FONTS["button"],
                         fg=self.COLORS["danger"], bg=self.COLORS["content_bg"]).pack(side=tk.LEFT, padx=5)

            # Uninstall button (always show for local plugins, even broken ones)
            uninstall_btn = tk.Button(action_frame, text="🗑️", font=self.FONTS["button"],
                                      bg=self.COLORS["danger"], fg="white", padx=8, pady=0,
                                      command=lambda p=pid, i=local_info: self._uninstall_plugin(p, i))
            uninstall_btn.pack(side=tk.LEFT, padx=5)

        else:
            # Remote only: show Install button
            if remote_info:
                install_btn = tk.Button(action_frame, text="INSTALL", font=self.FONTS["button"],
                                        bg=self.COLORS["info"], fg="white", padx=10, pady=2,
                                        command=lambda: self._install_from_store(remote_info))
                install_btn.pack(side=tk.LEFT, padx=5)

    def _is_newer(self, remote_version: str, local_version: str) -> bool:
        """Compare two version strings using packaging if available."""
        if HAS_PACKAGING:
            try:
                return Version(remote_version) > Version(local_version)
            except Exception:
                return remote_version > local_version
        else:
            try:
                r_parts = [int(x) for x in remote_version.split('.')]
                l_parts = [int(x) for x in local_version.split('.')]
                max_len = max(len(r_parts), len(l_parts))
                r_parts += [0] * (max_len - len(r_parts))
                l_parts += [0] * (max_len - len(l_parts))
                return r_parts > l_parts
            except:
                return remote_version > local_version

    def _ensure_local_index(self):
        """Generate plugins.json from local plugins if it doesn't exist or is incomplete."""
        index_path = Path("plugins/plugins.json")

        # Get current local plugins
        current_plugins = []
        folder_map = {
            "add-ons": Path("plugins/add-ons"),
            "software": Path("plugins/software"),
            "hardware": Path("plugins/hardware")
        }

        for category, folder in folder_map.items():
            if not folder.exists():
                continue
            for py_file in folder.glob("*.py"):
                if py_file.stem in ["__init__", "plugin_manager"]:
                    continue
                info = self._extract_info(py_file, category)
                if info:
                    download_url = f"https://gitlab.com/sefy76/scientific-toolkit/-/raw/main/plugins/{category}/{py_file.name}?ref_type=heads"
                    current_plugins.append({
                        'id': info['id'],
                        'name': info.get('name', info['id']),
                        'version': info.get('version', '0.0.1'),
                        'description': info.get('description', ''),
                        'author': info.get('author', 'Unknown'),
                        'category': category,
                        'icon': info.get('icon', '📦'),
                        'requires': info.get('requires', []),
                        'download_url': download_url
                    })

        # Check if index needs updating
        needs_update = True
        if index_path.exists():
            try:
                with open(index_path, 'r') as f:
                    existing = json.load(f)
                # Simple check: if counts differ, update
                if len(existing) == len(current_plugins):
                    needs_update = False
            except:
                pass

        if needs_update:
            with open(index_path, 'w', encoding='utf-8') as f:
                json.dump(current_plugins, f, indent=2)
            logger.info(f"📝 Generated/updated plugins.json with {len(current_plugins)} plugins")

    # ────────────────────────────────────────────────────────────
    # INSTALL / UPDATE / UNINSTALL
    # ────────────────────────────────────────────────────────────
    def _install_from_store(self, info: Dict, update: bool = False):
        """Download and install a plugin from the store. If update=True, overwrite existing."""
        pid = info['id']
        category = info.get('category', 'add-on')
        download_url = info.get('download_url', '')
        expected_sha256 = info.get('sha256')
        requires = info.get('requires', [])
        if not download_url:
            messagebox.showerror("Error", "No download URL for this plugin.")
            return

        folder_map = {
            'add-on': Path("plugins/add-ons"),
            'software': Path("plugins/software"),
            'hardware': Path("plugins/hardware")
        }
        target_folder = folder_map.get(category)
        if not target_folder:
            messagebox.showerror("Error", f"Unknown category: {category}")
            return
        target_folder.mkdir(parents=True, exist_ok=True)
        target_file = target_folder / f"{pid}.py"

        action = "Updating" if update else "Installing"
        progress = tk.Toplevel(self)
        progress.title(f"{action} {info.get('name', pid)}")
        progress.geometry("400x150")
        progress.transient(self)
        tk.Label(progress, text=f"{action} {info.get('name', pid)}...",
                 font=("Arial", 10)).pack(pady=10)
        status = tk.Label(progress, text="", font=("Arial", 8))
        status.pack()

        def download():
            try:
                status.config(text="Connecting...")
                with urllib.request.urlopen(download_url, timeout=15) as response:
                    with tempfile.NamedTemporaryFile(mode='wb', delete=False, dir=target_folder, suffix='.tmp') as tmp:
                        sha256 = hashlib.sha256()
                        total_size = int(response.headers.get('Content-Length', 0))
                        downloaded = 0
                        chunk_size = 8192
                        while True:
                            chunk = response.read(chunk_size)
                            if not chunk:
                                break
                            tmp.write(chunk)
                            sha256.update(chunk)
                            downloaded += len(chunk)
                            if total_size:
                                percent = int(100 * downloaded / total_size)
                                status.config(text=f"Downloaded {percent}%")
                            else:
                                status.config(text=f"Downloaded {downloaded} bytes")
                            progress.update()
                        tmp_path = tmp.name

                # Verify SHA‑256 if provided
                if expected_sha256:
                    file_hash = sha256.hexdigest()
                    if file_hash.lower() != expected_sha256.lower():
                        os.unlink(tmp_path)
                        self.after(0, lambda: messagebox.showerror(
                            "Security Error",
                            f"SHA‑256 hash mismatch!\nExpected: {expected_sha256}\nGot: {file_hash}\n\nInstallation aborted."
                        ))
                        return

                os.replace(tmp_path, target_file)
                logger.info(f"{action} successful: {target_file}")

                self.after(0, progress.destroy)

                # Check dependencies after download
                if requires:
                    met, missing = self._check_deps(requires)
                    if not met:
                        def ask_install():
                            msg = (f"Plugin '{info.get('name', pid)}' requires the following packages:\n"
                                   f"{', '.join(missing)}\n\n"
                                   "Do you want to install them now?")
                            if messagebox.askyesno("Missing Dependencies", msg, parent=self):
                                self._install_deps(info.get('name', pid), missing)
                        self.after(0, ask_install)

                # Automatically enable the plugin
                self.enabled_plugins[pid] = True
                temp_enabled = self.enabled_file.with_suffix(".tmp")
                with open(temp_enabled, 'w') as f:
                    json.dump(self.enabled_plugins, f, indent=2)
                temp_enabled.replace(self.enabled_file)

                # Refresh local plugins list and UI
                self.local_plugins_by_category = self._discover_all()
                self.after(0, lambda: self._refresh_category(self.category_var.get()))

                # Load the newly enabled plugin in the main app
                if hasattr(self.app, '_load_plugins'):
                    self.app.after(0, self.app._load_plugins)

            except Exception as e:
                logger.exception(f"Installation failed for {pid}")
                self.after(0, progress.destroy)
                self.after(0, lambda: messagebox.showerror("Installation Failed", f"Error downloading plugin:\n{e}"))

        threading.Thread(target=download, daemon=True).start()

    def _uninstall_plugin(self, pid: str, info: Dict):
        """Delete the local plugin file after confirmation."""
        name = info.get('name', pid)
        if not messagebox.askyesno("Confirm Uninstall", f"Are you sure you want to uninstall '{name}'?\nThe .py file will be permanently deleted."):
            return

        path = info.get('path')
        if not path or not Path(path).exists():
            messagebox.showerror("Error", "File not found")
            return

        try:
            Path(path).unlink()
            logger.info(f"Uninstalled {path}")

            # Remove from enabled list if present
            if pid in self.enabled_plugins:
                del self.enabled_plugins[pid]
                self._save_enabled()

            # Remove from local plugins list
            for cat in self.local_plugins_by_category:
                self.local_plugins_by_category[cat] = [p for p in self.local_plugins_by_category[cat] if p['id'] != pid]

            # Refresh the current view
            self._refresh_category(self.category_var.get())
            messagebox.showinfo("Success", f"Plugin '{name}' uninstalled.")

        except Exception as e:
            logger.exception(f"Failed to delete {path}")
            messagebox.showerror("Error", f"Could not delete file:\n{e}")

    # ────────────────────────────────────────────────────────────
    # SMART BUTTON & MENU REMOVAL
    # ────────────────────────────────────────────────────────────
    def _update_button_state(self):
        to_enable = 0
        to_disable = 0
        for pid, var in self.plugin_vars.items():
            was_enabled = self.enabled_plugins.get(pid, False)
            is_enabled = var.get()
            if is_enabled and not was_enabled:
                to_enable += 1
            elif not is_enabled and was_enabled:
                to_disable += 1
        if to_enable > 0 and to_disable > 0:
            self.action_btn.config(text=f"⚡ APPLY ({to_enable} ENABLE / {to_disable} DISABLE)", bg=self.COLORS["warning"])
        elif to_enable > 0:
            self.action_btn.config(text=f"✅ ENABLE {to_enable}", bg=self.COLORS["success"])
        elif to_disable > 0:
            self.action_btn.config(text=f"🔥 DISABLE {to_disable}", bg=self.COLORS["danger"])
        else:
            self.action_btn.config(text="✅ APPLY CHANGES", bg=self.COLORS["success"])

    def _remove_from_menu(self, plugin_id: str, info: dict):
        """
        Delete plugin from menu system.
        Note: This relies on hard‑coded menu names in the parent app.
        If the parent app's structure changes, this will need updating.
        """
        category = info.get('category', '')
        name = info.get('name', plugin_id)
        logger.info(f"Removing: {name} from menus")

        menus_to_check = []
        if hasattr(self.app, 'advanced_menu'):
            menus_to_check.append(('Advanced', self.app.advanced_menu))
        if category == 'hardware':
            for menu_name in ['xrf_menu', 'chemistry_menu', 'mineralogy_menu']:
                if hasattr(self.app, menu_name):
                    menus_to_check.append((menu_name, getattr(self.app, menu_name)))

        for menu_name, menu in menus_to_check:
            try:
                last = menu.index('end')
                for i in range(last, -1, -1):
                    try:
                        label = menu.entrycget(i, 'label')
                        if name in label or plugin_id in label:
                            menu.delete(i)
                            logger.debug(f"Removed from {menu_name} menu")
                    except:
                        continue
            except:
                pass

    def _apply(self):
        """Apply changes: enable/disable plugins, update menus."""
        changes = 0

        # Check dependencies for plugins being enabled
        plugins_to_enable = []
        for pid, var in self.plugin_vars.items():
            if var.get() and not self.enabled_plugins.get(pid, False):
                plugins_to_enable.append(pid)

        if plugins_to_enable:
            missing_all = []
            for pid in plugins_to_enable:
                info = None
                for cat in self.local_plugins_by_category.values():
                    for p in cat:
                        if p['id'] == pid:
                            info = p
                            break
                    if info:
                        break
                if info and info.get('requires'):
                    met, missing = self._check_deps(info['requires'])
                    if not met:
                        missing_all.append((info.get('name', pid), missing))

            if missing_all:
                msg = "The following plugins have missing dependencies:\n\n"
                for name, missing in missing_all:
                    msg += f"• {name}: missing {', '.join(missing)}\n"
                msg += "\nDo you want to install them now?\n(Yes = install, then enable; No = enable anyway; Cancel = abort)"
                response = messagebox.askyesnocancel("Missing Dependencies", msg, parent=self)
                if response is None:
                    return
                elif response:
                    all_packages = set()
                    for _, missing in missing_all:
                        all_packages.update(missing)
                    self._install_deps("Dependencies", list(all_packages))

        # Proceed with toggling states
        for pid, var in self.plugin_vars.items():
            was_enabled = self.enabled_plugins.get(pid, False)
            is_enabled = var.get()
            if is_enabled != was_enabled:
                changes += 1
                self.enabled_plugins[pid] = is_enabled

                info = None
                for cat in self.local_plugins_by_category.values():
                    for p in cat:
                        if p['id'] == pid:
                            info = p
                            break
                    if info:
                        break

                if info:
                    if is_enabled:
                        logger.info(f"Enabling: {info.get('name', pid)}")
                    else:
                        self._remove_from_menu(pid, info)

        self._save_enabled()

        if hasattr(self.app, '_load_plugins'):
            self.app._load_plugins()

        if changes > 0:
            self.status_var.set(f"✅ Applied {changes} changes")
            self.action_btn.config(text="✅ DONE", bg=self.COLORS["success"])
            self.after(1500, self.destroy)
        else:
            self.status_var.set("⚡ No changes")
            self.after(500, self.destroy)

    def _center_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")


def setup_plugin(main_app):
    return PluginManager(main_app)
