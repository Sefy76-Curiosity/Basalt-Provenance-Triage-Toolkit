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
    level=logging.WARNING,  # Changed to WARNING for cleaner output
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path("config") / "plugin_manager.log"),
        # Removed StreamHandler to prevent console clutter
    ]
)
logger = logging.getLogger("PluginManager")

# Try to import packaging for robust version comparison
try:
    from packaging.version import Version
    HAS_PACKAGING = True
except ImportError:
    HAS_PACKAGING = False
    # Silent fail - no warning to users


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

    STORE_SOURCES = [
        {
            "name": "GitLab",
            "index_url": "https://gitlab.com/sefy76/scientific-toolkit/-/raw/main/plugins/plugins.json?ref_type=heads",
            "base_url": "https://gitlab.com/sefy76/scientific-toolkit/-/raw/main/plugins/",
            "priority": 1,
            "last_success": None,
            "avg_response_time": None
        },
        {
            "name": "GitHub",
            "index_url": "https://raw.githubusercontent.com/Sefy76-Curiosity/Basalt-Provenance-Triage-Toolkit/refs/heads/main/plugins/plugins.json",
            "base_url": "https://github.com/Sefy76-Curiosity/Basalt-Provenance-Triage-Toolkit/tree/main/plugins",
            "priority": 2,
            "last_success": None,
            "avg_response_time": None
        }
    ]

    def __init__(self, parent_app):
        super().__init__(parent_app.root)
        self.app = parent_app
        self.current_canvas = None
        self.bind_all("<MouseWheel>", self._on_global_mousewheel)
        self.bind_all("<Button-4>", self._on_global_mousewheel)
        self.bind_all("<Button-5>", self._on_global_mousewheel)

        self.title("🔌 Plugin Manager v2.0")
        self.geometry(self.WINDOW_SIZE)
        self.minsize(*self.MIN_SIZE)
        self.transient(parent_app.root)

        # Ensure config directory exists
        self.config_dir = Path("config")
        self.config_dir.mkdir(exist_ok=True)

        # Plugin registry files
        self.enabled_file = self.config_dir / "enabled_plugins.json"
        self.downloaded_file = self.config_dir / "downloaded_plugins.json"
        self.downloaded_plugins: set = self._load_downloaded()

        # Local plugins
        self.local_plugins_by_category: Dict[str, List[Dict]] = self._discover_all()
        self._ensure_local_index()
        self.enabled_plugins: Dict[str, bool] = self._load_enabled()
        self.plugin_vars: Dict[str, tk.BooleanVar] = {}
        self.plugin_rows: Dict[str, tk.Frame] = {}

        # Remote plugins
        self.remote_plugins_by_category: Dict[str, List[Dict]] = {"add-ons": [], "software": [], "hardware": []}
        self.remote_fetched = False
        self.remote_fetch_failed = False
        self.active_source = None
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
        except tk.TclError:
            pass  # Silently fail - window is still usable

    def _on_global_mousewheel(self, event):
        if self.current_canvas:
            if event.delta:
                self.current_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            else:
                if event.num == 4:
                    self.current_canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    self.current_canvas.yview_scroll(1, "units")
        return "break"

    # ────────────────────────────────────────────────────────────
    # DISCOVERY
    # ────────────────────────────────────────────────────────────
    def _discover_all(self) -> Dict[str, List[Dict]]:
        """Scan folders and extract PLUGIN_INFO, with fallback for broken plugins."""
        categories = {"add-ons": [], "software": [], "hardware": []}
        folder_map = {
            "add-ons": Path("plugins/add-ons"),
            "software": Path("plugins/software"),
            "hardware": Path("plugins/hardware")
        }
        print(f"Scanning folders: {[str(folder) for folder in folder_map.values()]}")

        for category, folder in folder_map.items():
            if not folder.exists():
                folder.mkdir(parents=True, exist_ok=True)
                continue

            for py_file in folder.glob("*.py"):
                if py_file.stem in ["__init__", "plugin_manager"]:
                    continue

                info = self._extract_info(py_file, category)
                if info:
                    categories[category].append(info)
                else:
                    # Add fallback entry for broken plugins
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
        except Exception:
            pass
        return None

    # ────────────────────────────────────────────────────────────
    # REMOTE INDEX FETCH
    # ────────────────────────────────────────────────────────────
    def _fetch_remote_index(self):
        """Fetch remote plugin index from multiple sources with smart selection."""
        with self._fetch_lock:
            if self._fetching:
                return
            self._fetching = True
            self.remote_fetch_failed = False

        self.app.root.after(0, lambda: self.app.center.set_status("📡 Fetching remote plugins...", "processing"))

        def fetch():
            import concurrent.futures
            source_statuses = []          # (name, status, message) for summary
            successful_results = []       # actual data from successful sources

            self.app.root.after(0, lambda: self.app.center.set_status(f"Testing {len(self.STORE_SOURCES)} sources...", "processing"))

            with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.STORE_SOURCES)) as executor:
                future_to_source = {
                    executor.submit(self._test_source, source): source
                    for source in self.STORE_SOURCES
                }

                for future in concurrent.futures.as_completed(future_to_source):
                    source = future_to_source[future]
                    name = source['name']
                    try:
                        self.app.root.after(0, lambda n=name: self.app.center.set_status(f"Testing {n}...", "processing"))
                        result = future.result(timeout=15)
                        if result:
                            successful_results.append(result)
                            source_statuses.append((name, "success", "responded"))
                            self.app.root.after(0, lambda n=name: self.app.center.set_status(f"✅ {n} responded", "success"))
                        else:
                            source_statuses.append((name, "warning", "returned no data"))
                            self.app.root.after(0, lambda n=name: self.app.center.set_status(f"⚠️ {n} returned no data", "warning"))
                    except Exception as e:
                        source_statuses.append((name, "error", str(e)[:50]))
                        self.app.root.after(0, lambda n=name: self.app.center.set_status(f"❌ {n} failed", "error"))

            # Build summary for the user
            summary_lines = []
            for name, status, msg in source_statuses:
                icon = "✅" if status == "success" else "⚠️" if status == "warning" else "❌"
                summary_lines.append(f"{icon} {name}: {msg}")

            if not successful_results:
                # No successful source
                self.remote_fetch_failed = True
                self.after(0, lambda: self.status_var.set("🌐 Store unavailable"))
                summary = "All sources failed:\n" + "\n".join(summary_lines)
                self.app.root.after(0, lambda: self.app.center.show_warning('plugin_fetch', summary))
                self.app.root.after(0, lambda: self.app.center.set_status("Store unavailable", "warning"))
                with self._fetch_lock:
                    self._fetching = False
                return

            # Select best source from successful ones
            best_result = self._select_best_source(successful_results)
            all_remote = best_result['data']
            self.active_source = best_result['source']

            # Update source indicator in plugin manager footer
            self.after(0, lambda: self.source_var.set(f"📡 {best_result['name']}"))
            self.app.root.after(0, lambda n=best_result['name']: self.app.center.set_status(f"Using {n}", "success"))

            # Process by category
            for cat in self.remote_plugins_by_category:
                self.remote_plugins_by_category[cat] = [
                    p for p in all_remote if p.get('category') == cat
                ]

            self.remote_fetched = True
            self.after(0, lambda: self._refresh_category(self.category_var.get()))

            # Show summary (including any warnings) and reset main status
            summary = "Source results:\n" + "\n".join(summary_lines)
            self.app.root.after(0, lambda: self.app.center.show_warning('plugin_fetch', summary))
            self.app.root.after(0, lambda: self.app.center.set_status("Ready"))

            with self._fetch_lock:
                self._fetching = False

        threading.Thread(target=fetch, daemon=True).start()

    def _test_source(self, source):
        """Test a single source and return results with timing and data."""
        import time
        start_time = time.time()
        sep = "&" if "?" in source["index_url"] else "?"
        url = source["index_url"] + sep + "nocache=" + str(random.random())

        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                data = response.read().decode('utf-8')
                all_remote = json.loads(data)
                response_time = time.time() - start_time

                return {
                    'name': source['name'],
                    'data': all_remote,
                    'response_time': response_time,
                    'version': self._get_index_version(all_remote),
                    'priority': source['priority'],
                    'source': source
                }
        except Exception:
            raise

    def _get_index_version(self, data):
        """Extract highest plugin version from index."""
        versions = []
        for plugin in data:
            try:
                ver = plugin.get('version', '0.0.0')
                ver_tuple = tuple(int(x) for x in ver.split('.'))
                versions.append(ver_tuple)
            except:
                pass
        return max(versions) if versions else (0, 0, 0)

    def _select_best_source(self, results):
        """Smart selection: newest, then fastest, then priority."""
        return sorted(
            results,
            key=lambda r: (
                -self._version_to_int(r['version']),
                r['response_time'],
                r['priority']
            )
        )[0]

    def _version_to_int(self, version_tuple):
        """Convert version tuple to sortable integer."""
        if len(version_tuple) == 3:
            return version_tuple[0]*1000000 + version_tuple[1]*1000 + version_tuple[2]
        elif len(version_tuple) == 2:
            return version_tuple[0]*1000000 + version_tuple[1]*1000
        elif len(version_tuple) == 1:
            return version_tuple[0]*1000000
        return 0

    # ────────────────────────────────────────────────────────────
    # STATE MANAGEMENT
    # ────────────────────────────────────────────────────────────
    def _load_enabled(self) -> Dict[str, bool]:
        if self.enabled_file.exists():
            try:
                with open(self.enabled_file) as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_enabled(self) -> Dict[str, bool]:
        # Start from the full known state so plugins in unvisited tabs aren't wiped
        enabled = dict(self.enabled_plugins)
        # Overlay with current UI checkbox states (only tabs that were actually visited)
        enabled.update({pid: var.get() for pid, var in self.plugin_vars.items()})
        temp = self.enabled_file.with_suffix(".tmp")
        try:
            with open(temp, 'w') as f:
                json.dump(enabled, f, indent=2)
            temp.replace(self.enabled_file)
        except Exception:
            pass
        return enabled

    def _load_downloaded(self) -> set:
        """Load the set of plugin IDs that were installed from the store."""
        if self.downloaded_file.exists():
            try:
                with open(self.downloaded_file) as f:
                    return set(json.load(f))
            except Exception:
                return set()
        return set()

    def _save_downloaded(self):
        """Persist the downloaded plugin ID set."""
        temp = self.downloaded_file.with_suffix(".tmp")
        try:
            with open(temp, 'w') as f:
                json.dump(list(self.downloaded_plugins), f, indent=2)
            temp.replace(self.downloaded_file)
        except Exception:
            pass

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
        """Spawn pip install in a non-blocking window."""
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

        import queue as _queue

        def run():
            output_queue = _queue.Queue()
            done_event = [False]

            def poll():
                try:
                    while True:
                        line = output_queue.get_nowait()
                        text.insert(tk.END, line)
                        text.see(tk.END)
                except _queue.Empty:
                    pass
                if not done_event[0]:
                    win.after(50, poll)

            win.after(50, poll)

            def _append(s):
                output_queue.put(s)

            _append(f"$ pip install {' '.join(packages)}\n\n")
            proc = subprocess.Popen(
                [sys.executable, "-m", "pip", "install"] + packages,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            for line in proc.stdout:
                _append(line)
            proc.wait()
            done_event[0] = True

            if proc.returncode == 0:
                _append("\n✅ SUCCESS! Dependencies installed.\n")
                _append("Closing window in 2 seconds...\n")
                win.after(2000, win.destroy)
                self.after(0, lambda: self._refresh_category(self.category_var.get()))
            else:
                _append(f"\n❌ FAILED (code {proc.returncode})\n")

        threading.Thread(target=run, daemon=True).start()

    # ────────────────────────────────────────────────────────────
    # UI
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

        # Left side - status and source
        left_frame = tk.Frame(footer, bg=self.COLORS["footer_bg"])
        left_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.status_var = tk.StringVar(value="⚡ Ready")
        status = tk.Label(left_frame, textvariable=self.status_var,
                        font=self.FONTS["status"], bg=self.COLORS["footer_bg"], fg=self.COLORS["footer_fg"])
        status.pack(side=tk.LEFT, padx=15)

        # Source indicator
        self.source_var = tk.StringVar(value="")
        source_label = tk.Label(left_frame, textvariable=self.source_var,
                            font=("Arial", 8), bg=self.COLORS["footer_bg"], fg="#7f8c8d")
        source_label.pack(side=tk.LEFT, padx=5)

        # Right side - action button
        self.action_btn = tk.Button(footer, text="✅ APPLY CHANGES",
                                font=self.FONTS["tab"],
                                bg=self.COLORS["success"], fg="white",
                                padx=25, pady=8,
                                command=self._apply)
        self.action_btn.pack(side=tk.RIGHT, padx=15, pady=8)

    def _switch_category(self, category: str):
        """Switch between categories and repopulate the view."""
        self.category_var.set(category)
        self.current_canvas = None

        # Update button colors
        self.btn_addons.config(
            bg=self.COLORS["header_bg"] if category == "add-ons" else self.COLORS["tab_bg"],
            fg=self.COLORS["tab_fg_active"] if category == "add-ons" else self.COLORS["tab_fg_inactive"]
        )
        self.btn_software.config(
            bg=self.COLORS["header_bg"] if category == "software" else self.COLORS["tab_bg"],
            fg=self.COLORS["tab_fg_active"] if category == "software" else self.COLORS["tab_fg_inactive"]
        )
        self.btn_hardware.config(
            bg=self.COLORS["header_bg"] if category == "hardware" else self.COLORS["tab_bg"],
            fg=self.COLORS["tab_fg_active"] if category == "hardware" else self.COLORS["tab_fg_inactive"]
        )

        # Show selected frame
        for cat, frame in self.frames.items():
            if cat == category:
                for widget in frame.winfo_children():
                    widget.destroy()
                self._populate_merged_category(frame, category)
                frame.pack(fill=tk.BOTH, expand=True)
            else:
                frame.pack_forget()

    def _refresh_category(self, category: str):
        """Rebuild the current category view."""
        self._switch_category(category)

    def _get_merged_plugins(self, category: str) -> List[Dict]:
        """Combine local and remote plugins for a category."""
        local_dict = {p['id']: p for p in self.local_plugins_by_category.get(category, [])}
        remote_dict = {p['id']: p for p in self.remote_plugins_by_category.get(category, [])}

        merged = []
        # Add local plugins
        for pid, info in local_dict.items():
            merged.append({
                'id': pid,
                'local': info,
                'remote': remote_dict.get(pid),
                'type': 'local'
            })

        # Add remote-only plugins
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
        """Populate a category with merged plugins."""
        merged = self._get_merged_plugins(category)

        # Sort alphabetically by plugin name (case‑insensitive)
        def get_name(p):
            info = p['local'] or p['remote']
            return info.get('name', p['id']).lower()
        merged.sort(key=get_name)

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
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw", width=canvas.winfo_width() - 20)

        def _on_canvas_configure(event):
            canvas.itemconfig(1, width=event.width - 20)
        canvas.bind("<Configure>", _on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.current_canvas = canvas

        # Create rows
        for plugin in merged:
            self._create_unified_row(scroll_frame, plugin)

    def _create_unified_row(self, parent, plugin: Dict):
        """Create a compact, wrapped row for a plugin with left-aligned text."""
        local_info = plugin['local']
        remote_info = plugin['remote']
        pid = plugin['id']

        # Get display info
        if local_info:
            name = local_info.get('name', pid)
            icon = local_info.get('icon', '📦')
            version = local_info.get('version', '0.0.0')
            author = local_info.get('author', 'Unknown')
            description = local_info.get('description', '')
            requires = local_info.get('requires', [])
            is_broken = local_info.get('broken', False)
        else:
            name = remote_info.get('name', pid)
            icon = remote_info.get('icon', '📦')
            version = remote_info.get('version', '0.0.0')
            author = remote_info.get('author', 'Unknown')
            description = remote_info.get('description', '')
            requires = remote_info.get('requires', [])
            is_broken = False

        remote_version = remote_info.get('version') if remote_info else None

        # Main row frame
        row = tk.Frame(parent, bg=self.COLORS["content_bg"], relief=tk.GROOVE, borderwidth=1)
        row.pack(fill=tk.X, padx=3, pady=2, expand=False)

        # Left content area (takes remaining space)
        content = tk.Frame(row, bg=self.COLORS["content_bg"])
        content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Title with icon and version - LEFT ALIGNED
        title_frame = tk.Frame(content, bg=self.COLORS["content_bg"])
        title_frame.pack(fill=tk.X)

        title_text = f"{icon} {name}"
        if local_info and remote_version:
            title_text += f"  v{version} (remote v{remote_version})"
        elif version != '0.0.0':
            title_text += f"  v{version}"

        if is_broken:
            title_text = f"⚠️ {title_text} (broken)"

        tk.Label(title_frame, text=title_text, font=self.FONTS["plugin_title"],
                bg=self.COLORS["content_bg"], anchor="w").pack(anchor="w")

        # Description (wrapped) - PERFECT LEFT ALIGNMENT WITH TITLE
        if description:
            # Use Label with wraplength for consistent left alignment
            desc_label = tk.Label(content, text=description,
                                font=self.FONTS["plugin_desc"],
                                bg=self.COLORS["content_bg"], fg="#5e6c84",
                                wraplength=350, justify=tk.LEFT, anchor="w")
            desc_label.pack(anchor="w", pady=(2,0))

        # Author (small) - LEFT ALIGNED
        if author != 'Unknown':
            tk.Label(content, text=f"by {author}", font=self.FONTS["plugin_meta"],
                    fg="#7f8c8d", bg=self.COLORS["content_bg"],
                    anchor="w").pack(anchor="w")

        # Right action buttons frame
        actions = tk.Frame(row, bg=self.COLORS["content_bg"])
        actions.pack(side=tk.RIGHT, padx=5, pady=5, fill=tk.Y)

        # Dependency status (compact)
        if requires:
            met, missing = self._check_deps(requires)
            if not met:
                deps_btn = tk.Button(actions, text=f"⚠️ Deps", font=self.FONTS["button"],
                                    bg=self.COLORS["warning"], fg="white",
                                    command=lambda: self._install_deps(name, missing))
                deps_btn.pack(side=tk.TOP, pady=1, fill=tk.X)

        # Main action buttons based on plugin state
        if local_info and not is_broken:
            # Enable checkbox
            var = tk.BooleanVar(value=self.enabled_plugins.get(pid, False))
            var.trace('w', lambda *args: self._update_button_state())
            self.plugin_vars[pid] = var
            cb = tk.Checkbutton(actions, text="Enable", variable=var,
                                font=self.FONTS["button"], bg=self.COLORS["content_bg"])
            cb.pack(side=tk.TOP, pady=1, fill=tk.X)

            # Update button if newer version available
            if remote_version and self._is_newer(remote_version, version):
                update_btn = tk.Button(actions, text="UPDATE", font=self.FONTS["button"],
                                        bg=self.COLORS["warning"], fg="white",
                                        command=lambda: self._install_from_store(remote_info, update=True))
                update_btn.pack(side=tk.TOP, pady=1, fill=tk.X)

            # Uninstall button
            uninstall_btn = tk.Button(actions, text="🗑️ Uninstall", font=self.FONTS["button"],
                                        bg=self.COLORS["danger"], fg="white",
                                        command=lambda: self._uninstall_plugin(pid, local_info))
            uninstall_btn.pack(side=tk.TOP, pady=1, fill=tk.X)

        elif local_info and is_broken:
            # Broken plugin - show warning and uninstall only
            tk.Label(actions, text="⚠️ Broken", font=self.FONTS["button"],
                    fg=self.COLORS["danger"], bg=self.COLORS["content_bg"]).pack(side=tk.TOP, pady=1)
            uninstall_btn = tk.Button(actions, text="🗑️ Uninstall", font=self.FONTS["button"],
                                        bg=self.COLORS["danger"], fg="white",
                                        command=lambda: self._uninstall_plugin(pid, local_info))
            uninstall_btn.pack(side=tk.TOP, pady=1, fill=tk.X)

        elif remote_info:
            # Remote only - show Install button
            install_btn = tk.Button(actions, text="INSTALL", font=self.FONTS["button"],
                                    bg=self.COLORS["info"], fg="white",
                                    command=lambda: self._install_from_store(remote_info))
            install_btn.pack(side=tk.TOP, pady=1, fill=tk.X)

    def _is_newer(self, remote_version: str, local_version: str) -> bool:
        """Compare two version strings."""
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
        """Generate plugins.json from local plugins if needed."""
        index_path = Path("plugins/plugins.json")
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

        needs_update = True
        if index_path.exists():
            try:
                with open(index_path, 'r') as f:
                    existing = json.load(f)
                existing_ids = {p['id'] for p in existing}
                current_ids = {p['id'] for p in current_plugins}
                if existing_ids == current_ids:
                    needs_update = False
            except:
                pass

        if needs_update:
            with open(index_path, 'w', encoding='utf-8') as f:
                json.dump(current_plugins, f, indent=2)

    # ────────────────────────────────────────────────────────────
    # INSTALL / UPDATE / UNINSTALL
    # ────────────────────────────────────────────────────────────
    def _install_from_store(self, info: Dict, update: bool = False):
        """Download and install a plugin from the store."""
        pid = info['id']
        category = info.get('category', 'add-ons')
        download_url = info.get('download_url', '')
        expected_sha256 = info.get('sha256')
        requires = info.get('requires', [])

        if not download_url:
            messagebox.showerror("Error", "No download URL for this plugin.")
            return

        folder_map = {
            'add-ons': Path("plugins/add-ons"),
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
                progress.after(0, lambda: status.config(text="Connecting..."))
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
                                progress.after(0, lambda p=percent: status.config(text=f"Downloaded {p}%"))
                            else:
                                progress.after(0, lambda d=downloaded: status.config(text=f"Downloaded {d} bytes"))
                        tmp_path = tmp.name

                if expected_sha256:
                    file_hash = sha256.hexdigest()
                    if file_hash.lower() != expected_sha256.lower():
                        os.unlink(tmp_path)
                        self.after(0, lambda: messagebox.showerror("Security Error", "Hash mismatch"))
                        return

                os.replace(tmp_path, target_file)

                self.after(0, progress.destroy)

                # Check dependencies
                if requires:
                    met, missing = self._check_deps(requires)
                    if not met:
                        def ask_install():
                            msg = f"Plugin requires: {', '.join(missing)}\nInstall now?"
                            if messagebox.askyesno("Missing Dependencies", msg, parent=self):
                                self._install_deps(info.get('name', pid), missing)
                        self.after(0, ask_install)

                # Auto-enable and mark as downloaded from store
                self.enabled_plugins[pid] = True
                self.downloaded_plugins.add(pid)
                self._save_downloaded()
                temp_enabled = self.enabled_file.with_suffix(".tmp")
                with open(temp_enabled, 'w') as f:
                    json.dump(self.enabled_plugins, f, indent=2)
                temp_enabled.replace(self.enabled_file)

                # Refresh
                self.local_plugins_by_category = self._discover_all()
                self.after(0, lambda: self._refresh_category(self.category_var.get()))

                if hasattr(self.app, '_load_plugins'):
                    self.app.after(0, self.app._load_plugins)

            except Exception as e:
                self.after(0, progress.destroy)
                self.after(0, lambda: messagebox.showerror("Installation Failed", str(e)))

        threading.Thread(target=download, daemon=True).start()

    def _uninstall_plugin(self, pid: str, info: Dict):
        """Remove a plugin. Only deletes the file if it was installed from the store."""
        name = info.get('name', pid)
        is_downloaded = pid in self.downloaded_plugins

        if is_downloaded:
            confirm_msg = f"Uninstall '{name}'?\n\nThis will delete the plugin file."
        else:
            confirm_msg = (
                f"Remove '{name}' from the plugin list?\n\n"
                f"This is a locally developed plugin — the .py file will NOT be deleted."
            )

        if not messagebox.askyesno("Confirm Uninstall", confirm_msg):
            return

        path = info.get('path')

        try:
            if is_downloaded:
                if not path or not Path(path).exists():
                    messagebox.showerror("Error", "File not found")
                    return
                Path(path).unlink()
                self.downloaded_plugins.discard(pid)
                self._save_downloaded()

            if pid in self.enabled_plugins:
                del self.enabled_plugins[pid]
                self._save_enabled()

            for cat in self.local_plugins_by_category:
                self.local_plugins_by_category[cat] = [p for p in self.local_plugins_by_category[cat] if p['id'] != pid]

            self._refresh_category(self.category_var.get())

        except Exception as e:
            messagebox.showerror("Error", f"Could not uninstall: {e}")

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
            self.action_btn.config(text=f"⚡ APPLY ({to_enable}/{to_disable})", bg=self.COLORS["warning"])
        elif to_enable > 0:
            self.action_btn.config(text=f"✅ ENABLE {to_enable}", bg=self.COLORS["success"])
        elif to_disable > 0:
            self.action_btn.config(text=f"🔥 DISABLE {to_disable}", bg=self.COLORS["danger"])
        else:
            self.action_btn.config(text="✅ APPLY", bg=self.COLORS["success"])

    def _remove_from_menu(self, plugin_id: str, info: dict):
        """Remove plugin from menu system and/or hardware sidebar."""
        category = info.get('category', '')
        name = info.get('name', plugin_id)
        icon = info.get('icon', '🔌')

        # Hardware plugins live in the sidebar, not a dropdown menu
        if category == 'hardware':
            if hasattr(self.app, 'left') and hasattr(self.app.left, 'remove_hardware_button'):
                self.app.left.remove_hardware_button(name, icon)
            # Also remove from the app's hardware_plugins registry
            if hasattr(self.app, 'hardware_plugins'):
                self.app.hardware_plugins.pop(plugin_id, None)
            return

        # Software / add-on plugins live in dropdown menus
        menus_to_check = []
        if hasattr(self.app, 'advanced_menu'):
            menus_to_check.append(('Advanced', self.app.advanced_menu))

        for menu_name, menu in menus_to_check:
            try:
                last = menu.index('end')
                for i in range(last, -1, -1):
                    try:
                        label = menu.entrycget(i, 'label')
                        if name in label or plugin_id in label:
                            menu.delete(i)
                    except:
                        continue
            except:
                pass

    def _apply(self):
        """Apply enable/disable changes."""
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
                msg = "Missing dependencies:\n"
                for name, missing in missing_all:
                    msg += f"• {name}: {', '.join(missing)}\n"
                msg += "\nInstall now?"
                if messagebox.askyesno("Missing Dependencies", msg, parent=self):
                    all_packages = set()
                    for _, missing in missing_all:
                        all_packages.update(missing)
                    self._install_deps("Dependencies", list(all_packages))

        # Toggle states
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

                if info and not is_enabled:
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
