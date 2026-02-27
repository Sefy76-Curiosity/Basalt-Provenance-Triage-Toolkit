"""
Plugin Manager v3.0 - ttkbootstrap Edition
Author: Sefy Levy

3 TABS · FIELD GROUPING · COLLAPSIBLE SECTIONS · SOURCE BADGES · SMART TOGGLE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🖥  LOCAL   — user's own file, never deleted by Plugin Manager
☁️  STORE   — downloaded from GitLab/GitHub, can be updated/deleted
🔄  L+S     — local file exists AND also on store (user owns file, safe)
✓  CHECK   → Enable + Add to field submenu under Advanced
✗  UNCHECK → Disable + remove from menu instantly
⚡  Smart button: ENABLE N / DISABLE N
🛡️  SHA-256 verification for downloaded plugins
⚙️  Missing dependencies detected and installed on demand
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Requires: pip install ttkbootstrap
"""

PLUGIN_MANAGER_INFO = {
    "id": "plugin_manager",
    "name": "🔌 Plugin Manager",
    "version": "3.0",
    "author": "Sefy Levy"
}

import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
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
from typing import Optional, Dict, List, Tuple

# ── Logging ───────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(Path("config") / "plugin_manager.log")]
)
logger = logging.getLogger("PluginManager")

try:
    from packaging.version import Version
    HAS_PACKAGING = True
except ImportError:
    HAS_PACKAGING = False

# ── Field definitions (order matters — determines menu order) ──────────
SCIENTIFIC_FIELDS = [
    ("🪨", "Geology & Geochemistry"),
    ("⏳", "Geochronology & Dating"),
    ("🔥", "Petrology & Mineralogy"),
    ("📐", "Structural Geology"),
    ("🌍", "Geophysics"),
    ("🗺️", "GIS & Spatial Science"),
    ("🏺", "Archaeology & Archaeometry"),
    ("🦴", "Zooarchaeology"),
    ("🔬", "Spectroscopy"),
    ("⚗️", "Chromatography & Analytical Chemistry"),
    ("⚡", "Electrochemistry"),
    ("🧱", "Materials Science"),
    ("🌡️", "Thermal Analysis"),
    ("💧", "Solution Chemistry"),
    ("🧬", "Molecular Biology & Clinical Diagnostics"),
    ("🌤️", "Meteorology & Environmental Science"),
    ("📡", "Physics & Test/Measurement"),
    ("📦", "General"),
]

FIELD_ICON = {name: icon for icon, name in SCIENTIFIC_FIELDS}

# ── Fallback field mapping (plugin_id → field) ────────────────────────
# Used when a plugin doesn't yet have a "field" key in its PLUGIN_INFO.
# As plugins get updated to include "field", this mapping becomes unused.
FIELD_MAPPING: Dict[str, str] = {
    # Geology & Geochemistry
    "advanced_normalization":           "Geology & Geochemistry",
    "advanced_normative_calculations":  "Geology & Geochemistry",
    "ague_hg_mobility":                 "Geology & Geochemistry",
    "compositional_stats_pro":          "Geology & Geochemistry",
    "geochem_advanced":                 "Geology & Geochemistry",
    "geochemical_explorer":             "Geology & Geochemistry",
    "interactive_contouring":           "Geology & Geochemistry",
    "literature_comparison":            "Geology & Geochemistry",
    "physical_properties_suite":        "Geology & Geochemistry",
    # Geochronology & Dating
    "dating_integration":               "Geochronology & Dating",
    "geochronology_suite":              "Geochronology & Dating",
    "isotope_mixing_models":            "Geochronology & Dating",
    "laicpms_pro":                      "Geochronology & Dating",
    # Petrology & Mineralogy
    "petrogenetic_modeling_suite":      "Petrology & Mineralogy",
    "thermobarometry_suite":            "Petrology & Mineralogy",
    "virtual_microscopy_pro":           "Petrology & Mineralogy",
    # Structural Geology
    "structural_suite":                 "Structural Geology",
    # Geophysics
    "geophysics_analysis_suite":        "Geophysics",
    # GIS & Spatial Science
    "gis_3d_viewer_pro":                "GIS & Spatial Science",
    "google_earth_pro":                 "GIS & Spatial Science",
    "quartz_gis_pro":                   "GIS & Spatial Science",
    "spatial_kriging":                  "GIS & Spatial Science",
    # Archaeology & Archaeometry
    "archaeology_archaeometry_software_suite": "Archaeology & Archaeometry",
    "lithic_morphometrics":             "Archaeology & Archaeometry",
    "museum_import":                    "Archaeology & Archaeometry",
    "report_generator":                 "Archaeology & Archaeometry",
    # Zooarchaeology
    "zooarchaeology_analysis_suite":    "Zooarchaeology",
    # Spectroscopy
    "spectral_toolbox":                 "Spectroscopy",
    "spectroscopy_analysis_suite":      "Spectroscopy",
    # Chromatography
    "chromatography_analysis_suite":    "Chromatography & Analytical Chemistry",
    # Electrochemistry
    "electrochemistry_analysis_suite":  "Electrochemistry",
    # Materials Science
    "materials_science_analysis_suite": "Materials Science",
    # Thermal Analysis
    "thermal_analysis_suite":           "Thermal Analysis",
    # Solution Chemistry
    "solution_chemistry_suite":         "Solution Chemistry",
    # Molecular Biology & Clinical Diagnostics
    "clinical_diagnostics_analysis_suite": "Molecular Biology & Clinical Diagnostics",
    "molecular_biology_suite":          "Molecular Biology & Clinical Diagnostics",
    # Meteorology & Environmental Science
    "meteorology_analysis_suite":       "Meteorology & Environmental Science",
    # Physics & Test/Measurement
    "physics_test_measurement_suite":   "Physics & Test/Measurement",
    # General (utilities, cross-field tools)
    "advanced_export":                  "General",
    "barcode_scanner_suite":            "General",
    "data_validation_filter":           "General",
    "dataprep_pro":                     "General",
    "demo_data_generator":              "General",
    "pca_lda_explorer":                 "General",
    "photo_manager":                    "General",
    "publication_layouts":              "General",
    "scripting_console":                "General",
    "uncertainty_propagation":          "General",
}


def get_plugin_field(plugin_id: str, plugin_info: dict) -> str:
    """
    Resolve the scientific field for a plugin.
    Priority: PLUGIN_INFO['field'] > FIELD_MAPPING > 'General'
    """
    return (
        plugin_info.get("field")
        or FIELD_MAPPING.get(plugin_id)
        or "General"
    )


class PluginManager(tk.Toplevel):

    WINDOW_SIZE = "760x600"
    MIN_SIZE    = (680, 500)
    STATE_FILE  = Path("config") / "plugin_manager_state.json"

    # pip → importlib name
    IMPORT_MAPPING = {
        "google-generativeai":    "google.generativeai",
        "numpy":                  "numpy",
        "pandas":                 "pandas",
        "matplotlib":             "matplotlib",
        "scipy":                  "scipy",
        "scikit-learn":           "sklearn",
        "scikit-image":           "skimage",
        "opencv-python":          "cv2",
        "opencv-contrib-python":  "cv2",
        "pyserial":               "serial",
        "pillow":                 "PIL",
        "ctypes":                 "ctypes",
        "umap-learn":             "umap",
        "python-docx":            "docx",
        "simplekml":              "simplekml",
        "pyvista":                "pyvista",
        "geopandas":              "geopandas",
        "pynmea2":                "pynmea2",
        "watchdog":               "watchdog",
        "pythonnet":              "clr",
        "earthengine-api":        "ee",
        "pybaselines":            "pybaselines",
        "lmfit":                  "lmfit",
        "contextily":             "contextily",
        "shapely":                "shapely",
        "pyproj":                 "pyproj",
        "descartes":              "descartes",
        "mapclassify":            "mapclassify",
        "rasterio":               "rasterio",
        "rioxarray":              "rioxarray",
        "osmnx":                  "osmnx",
        "trimesh":                "trimesh",
        "emcee":                  "emcee",
        "corner":                 "corner",
        "joblib":                 "joblib",
        "openpyxl":               "openpyxl",
        "pyrolite":               "pyrolite",
        "seaborn":                "seaborn",
        "missingno":              "missingno",
        "bs4":                    "bs4",
        "requests":               "requests",
        "anthropic":              "anthropic",
        "openai":                 "openai",
    }

    STORE_SOURCES = [
        {
            "name":      "GitLab",
            "index_url": "https://gitlab.com/sefy76/scientific-toolkit/-/raw/main/plugins/plugins.json?ref_type=heads",
            "base_url":  "https://gitlab.com/sefy76/scientific-toolkit/-/raw/main/plugins/",
            "priority":  1,
            "last_success":      None,
            "avg_response_time": None,
        },
        {
            "name":      "GitHub",
            "index_url": "https://raw.githubusercontent.com/Sefy76-Curiosity/Basalt-Provenance-Triage-Toolkit/refs/heads/main/plugins/plugins.json",
            "base_url":  "https://github.com/Sefy76-Curiosity/Basalt-Provenance-Triage-Toolkit/tree/main/plugins",
            "priority":  2,
            "last_success":      None,
            "avg_response_time": None,
        },
    ]

    # ── Init ──────────────────────────────────────────────────────────
    def __init__(self, parent_app):
        super().__init__(parent_app.root)
        self.app           = parent_app
        self.current_canvas = None

        self.bind_all("<MouseWheel>", self._on_global_mousewheel)
        self.bind_all("<Button-4>",   self._on_global_mousewheel)
        self.bind_all("<Button-5>",   self._on_global_mousewheel)

        self.title("🔌 Plugin Manager v3.0")
        self.geometry(self.WINDOW_SIZE)
        self.minsize(*self.MIN_SIZE)
        self.transient(parent_app.root)

        # Config / registry
        self.config_dir = Path("config")
        self.config_dir.mkdir(exist_ok=True)
        self.enabled_file    = self.config_dir / "enabled_plugins.json"
        self.downloaded_file = self.config_dir / "downloaded_plugins.json"
        self.downloaded_plugins: set = self._load_downloaded()

        # Persisted UI state
        self._ui_state = self._load_ui_state()
        # Dict[field_name, bool] — True = collapsed
        self._field_collapsed: Dict[str, bool] = self._ui_state.get("field_collapsed", {})

        # Local plugins
        self.local_plugins_by_category: Dict[str, List[Dict]] = self._discover_all()
        self._ensure_local_index()
        self.enabled_plugins: Dict[str, bool] = self._load_enabled()
        self.plugin_vars:  Dict[str, tk.BooleanVar] = {}
        self.plugin_rows:  Dict[str, tk.Frame]      = {}

        # Remote plugins
        self.remote_plugins_by_category: Dict[str, List[Dict]] = {
            "add-ons": [], "software": [], "hardware": []
        }
        self.remote_fetched      = False
        self.remote_fetch_failed = False
        self.active_source       = None
        self._fetch_lock         = threading.Lock()
        self._fetching           = False

        # Per-plugin source tracking (pid → source name used for download)
        self._plugin_source: Dict[str, str] = self._ui_state.get("plugin_source", {})

        self._build_ui()
        self._update_button_state()
        self._center_window()
        self._safe_grab()
        self._fetch_remote_index()

        # Save state on close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        self._save_ui_state()
        self.destroy()

    def _safe_grab(self):
        try:
            self.grab_set()
        except tk.TclError:
            pass

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

    # ── State persistence ─────────────────────────────────────────────
    def _load_ui_state(self) -> dict:
        try:
            if self.STATE_FILE.exists():
                with open(self.STATE_FILE) as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def _save_ui_state(self):
        try:
            state = {
                "field_collapsed": self._field_collapsed,
                "plugin_source":   self._plugin_source,
            }
            temp = self.STATE_FILE.with_suffix(".tmp")
            with open(temp, "w") as f:
                json.dump(state, f, indent=2)
            temp.replace(self.STATE_FILE)
        except Exception:
            pass

    # ── Discovery ─────────────────────────────────────────────────────
    def _discover_all(self) -> Dict[str, List[Dict]]:
        categories = {"add-ons": [], "software": [], "hardware": []}
        folder_map = {
            "add-ons":  Path("plugins/add-ons"),
            "software": Path("plugins/software"),
            "hardware": Path("plugins/hardware"),
        }
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
                    categories[category].append({
                        "id":          py_file.stem,
                        "name":        py_file.stem.replace("_", " ").title(),
                        "category":    category,
                        "icon":        "📦",
                        "version":     "?",
                        "requires":    [],
                        "description": "Local plugin (metadata could not be read)",
                        "path":        str(py_file),
                        "module":      py_file.stem,
                        "broken":      True,
                    })
        return categories

    def _extract_info(self, py_file: Path, default_category: str) -> Optional[Dict]:
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == "PLUGIN_INFO":
                            info = ast.literal_eval(node.value)
                            info["category"] = default_category
                            info["path"]     = str(py_file)
                            info["module"]   = py_file.stem
                            return info
        except Exception:
            pass
        return None

    # ── Source classification ─────────────────────────────────────────
    def _get_source_type(self, pid: str, has_local: bool, has_remote: bool) -> str:
        """
        Returns:
          'store'   — downloaded by Plugin Manager (in downloaded_plugins)
          'local'   — user's own file, not downloaded by PM
          'both'    — user's own file AND also exists on store
        """
        is_downloaded = pid in self.downloaded_plugins
        if is_downloaded:
            return "store"
        if has_local and has_remote:
            return "both"
        return "local"

    def _source_badge(self, source_type: str) -> str:
        return {"store": "☁️", "local": "🖥", "both": "🔄"}.get(source_type, "🖥")

    # ── Remote fetch ──────────────────────────────────────────────────
    def _fetch_remote_index(self):
        with self._fetch_lock:
            if self._fetching:
                return
            self._fetching = True
            self.remote_fetch_failed = False

        self.app.root.after(0, lambda: self.app.center.set_status(
            "📡 Fetching remote plugins...", "processing"))

        def fetch():
            import concurrent.futures
            source_statuses    = []
            successful_results = []

            with concurrent.futures.ThreadPoolExecutor(
                    max_workers=len(self.STORE_SOURCES)) as executor:
                future_to_source = {
                    executor.submit(self._test_source, src): src
                    for src in self.STORE_SOURCES
                }
                for future in concurrent.futures.as_completed(future_to_source):
                    src  = future_to_source[future]
                    name = src["name"]
                    try:
                        result = future.result(timeout=15)
                        if result:
                            successful_results.append(result)
                            source_statuses.append((name, "success", "responded"))
                            self.app.root.after(0, lambda n=name:
                                self.app.center.set_status(f"✅ {n} responded", "success"))
                        else:
                            source_statuses.append((name, "warning", "no data"))
                    except Exception as e:
                        source_statuses.append((name, "error", str(e)[:50]))
                        self.app.root.after(0, lambda n=name:
                            self.app.center.set_status(f"❌ {n} failed", "error"))

            summary_lines = [
                f"{'✅' if s=='success' else '⚠️' if s=='warning' else '❌'} {n}: {m}"
                for n, s, m in source_statuses
            ]

            if not successful_results:
                self.remote_fetch_failed = True
                self.after(0, lambda: self.status_var.set("🌐 Store unavailable"))
                self.app.root.after(0, lambda: self.app.center.show_warning(
                    "plugin_fetch", "All sources failed:\n" + "\n".join(summary_lines)))
                self.app.root.after(0, lambda: self.app.center.set_status(
                    "Store unavailable", "warning"))
                with self._fetch_lock:
                    self._fetching = False
                return

            best = self._select_best_source(successful_results)
            self.active_source = best["source"]

            # Show both source versions in status if they differ
            versions = {r["name"]: r["version"] for r in successful_results}
            version_info = "  |  ".join(
                f"{n} v{'.'.join(str(x) for x in v)}"
                for n, v in versions.items()
            )
            self.after(0, lambda: self.source_var.set(f"📡 {version_info}"))

            for cat in self.remote_plugins_by_category:
                self.remote_plugins_by_category[cat] = [
                    p for p in best["data"] if p.get("category") == cat
                ]

            self.remote_fetched = True
            self.after(0, self._refresh_current_tab)

            self.app.root.after(0, lambda: self.app.center.show_warning(
                "plugin_fetch", "Source results:\n" + "\n".join(summary_lines)))
            self.app.root.after(0, lambda: self.app.center.set_status("Ready"))

            with self._fetch_lock:
                self._fetching = False

        threading.Thread(target=fetch, daemon=True).start()

    def _test_source(self, source):
        import time
        start = time.time()
        sep = "&" if "?" in source["index_url"] else "?"
        url = source["index_url"] + sep + "nocache=" + str(random.random())
        with urllib.request.urlopen(url, timeout=10) as resp:
            data       = resp.read().decode("utf-8")
            all_remote = json.loads(data)
            return {
                "name":          source["name"],
                "data":          all_remote,
                "response_time": time.time() - start,
                "version":       self._get_index_version(all_remote),
                "priority":      source["priority"],
                "source":        source,
            }

    def _get_index_version(self, data):
        versions = []
        for plugin in data:
            try:
                ver_tuple = tuple(int(x) for x in plugin.get("version","0.0.0").split("."))
                versions.append(ver_tuple)
            except Exception:
                pass
        return max(versions) if versions else (0, 0, 0)

    def _select_best_source(self, results):
        return sorted(
            results,
            key=lambda r: (-self._version_to_int(r["version"]),
                           r["response_time"], r["priority"])
        )[0]

    def _version_to_int(self, vt):
        if len(vt) >= 3: return vt[0]*1_000_000 + vt[1]*1_000 + vt[2]
        if len(vt) == 2: return vt[0]*1_000_000 + vt[1]*1_000
        if len(vt) == 1: return vt[0]*1_000_000
        return 0

    # ── State management ──────────────────────────────────────────────
    def _load_enabled(self) -> Dict[str, bool]:
        if self.enabled_file.exists():
            try:
                with open(self.enabled_file) as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_enabled(self) -> Dict[str, bool]:
        enabled = dict(self.enabled_plugins)
        enabled.update({pid: var.get() for pid, var in self.plugin_vars.items()})
        temp = self.enabled_file.with_suffix(".tmp")
        try:
            with open(temp, "w") as f:
                json.dump(enabled, f, indent=2)
            temp.replace(self.enabled_file)
        except Exception:
            pass
        return enabled

    def _load_downloaded(self) -> set:
        if self.downloaded_file.exists():
            try:
                with open(self.downloaded_file) as f:
                    return set(json.load(f))
            except Exception:
                return set()
        return set()

    def _save_downloaded(self):
        temp = self.downloaded_file.with_suffix(".tmp")
        try:
            with open(temp, "w") as f:
                json.dump(list(self.downloaded_plugins), f, indent=2)
            temp.replace(self.downloaded_file)
        except Exception:
            pass

    # ── Dependency check ──────────────────────────────────────────────
    def _check_deps(self, requires: List[str]) -> Tuple[bool, List[str]]:
        if not requires:
            return True, []
        missing = []
        for pkg in requires:
            if pkg == "ctypes":
                continue
            import_name = self.IMPORT_MAPPING.get(pkg, pkg)
            try:
                if importlib.util.find_spec(import_name) is None:
                    missing.append(pkg)
            except Exception:
                missing.append(pkg)
        return len(missing) == 0, missing

    def _install_deps(self, plugin_name: str, packages: List[str]):
        win = tk.Toplevel(self)
        win.title(f"📦 Installing: {plugin_name}")
        win.geometry("620x420")
        win.transient(self)

        hdr = tk.Frame(win, bg="#3498db", height=32)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        tk.Label(hdr, text=f"pip install {' '.join(packages)}",
                 font=("Consolas", 9), bg="#3498db", fg="white").pack(pady=6)

        text   = tk.Text(win, wrap=tk.WORD, font=("Consolas", 9),
                         bg="#1e1e1e", fg="#d4d4d4")
        scroll = ttk.Scrollbar(win, orient=VERTICAL, command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=5)

        import queue as _queue

        def run():
            q    = _queue.Queue()
            done = [False]

            def poll():
                try:
                    while True:
                        line = q.get_nowait()
                        text.insert(tk.END, line)
                        text.see(tk.END)
                except _queue.Empty:
                    pass
                if not done[0]:
                    win.after(50, poll)

            win.after(50, poll)
            q.put(f"$ pip install {' '.join(packages)}\n\n")
            proc = subprocess.Popen(
                [sys.executable, "-m", "pip", "install"] + packages,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1,
            )
            for line in proc.stdout:
                q.put(line)
            proc.wait()
            done[0] = True

            if proc.returncode == 0:
                q.put("\n✅ SUCCESS! Dependencies installed.\n")
                q.put("Closing in 2 seconds...\n")
                win.after(2000, win.destroy)
                self.after(0, self._refresh_current_tab)
            else:
                q.put(f"\n❌ FAILED (code {proc.returncode})\n")

        threading.Thread(target=run, daemon=True).start()

    # ── UI ────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Header
        hdr = ttk.Frame(self, bootstyle=DARK, padding=(12, 7))
        hdr.pack(fill=X)
        ttk.Label(hdr, text="🔌  PLUGIN MANAGER  v3.0",
                  font=("Arial", 12, "bold"),
                  bootstyle="inverse-dark").pack(side=LEFT)

        # Notebook
        self.notebook = ttk.Notebook(self, bootstyle=PRIMARY)
        self.notebook.pack(fill=BOTH, expand=True, padx=8, pady=(6, 0))

        self.tab_frames: Dict[str, ttk.Frame] = {}
        for cat, label in [
            ("add-ons",  "🎨  Add-Ons"),
            ("software", "📦  Software"),
            ("hardware", "🔌  Hardware"),
        ]:
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=f"  {label}  ")
            self.tab_frames[cat] = frame

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        # Footer
        ftr = ttk.Frame(self, bootstyle=SECONDARY, padding=(12, 7))
        ftr.pack(fill=X, side=BOTTOM)

        self.status_var = tk.StringVar(value="⚡ Ready")
        ttk.Label(ftr, textvariable=self.status_var,
                  bootstyle="inverse-secondary",
                  font=("Arial", 9)).pack(side=LEFT)

        self.source_var = tk.StringVar(value="")
        ttk.Label(ftr, textvariable=self.source_var,
                  bootstyle="inverse-secondary",
                  font=("Arial", 8)).pack(side=LEFT, padx=(12, 0))

        # Legend
        for badge, label in [("🖥", "Local"), ("☁️", "Store"), ("🔄", "Both")]:
            ttk.Label(ftr, text=f"{badge} {label}",
                      bootstyle="inverse-secondary",
                      font=("Arial", 8)).pack(side=LEFT, padx=(10, 0))

        self.action_btn = ttk.Button(
            ftr, text="✅ APPLY CHANGES",
            bootstyle=SUCCESS, width=20,
            command=self._apply,
        )
        self.action_btn.pack(side=RIGHT)

        # Populate first tab
        self._populate_tab("add-ons")

    # ── Tab handling ──────────────────────────────────────────────────
    def _on_tab_changed(self, event):
        self.current_canvas = None
        self._populate_tab(self._get_current_category())

    def _get_current_category(self) -> str:
        idx = self.notebook.index(self.notebook.select())
        return ["add-ons", "software", "hardware"][idx]

    def _refresh_current_tab(self):
        self._populate_tab(self._get_current_category())

    def _refresh_category(self, category: str):
        self._populate_tab(category)

    def _populate_tab(self, category: str):
        frame = self.tab_frames[category]
        for w in frame.winfo_children():
            w.destroy()
        self.current_canvas = None

        merged = self._get_merged_plugins(category)

        if not merged:
            ttk.Label(frame, text="✨ No plugins found",
                      font=("Arial", 11),
                      bootstyle=SECONDARY).pack(expand=True)
            return

        if category == "software":
            self._populate_software_grouped(frame, merged)
        else:
            self._populate_flat(frame, merged)

    # ── Flat list (add-ons / hardware) ────────────────────────────────
    def _populate_flat(self, frame, merged: List[Dict]):
        merged.sort(key=lambda p: (p["local"] or p["remote"]).get("name", p["id"]).lower())

        canvas    = tk.Canvas(frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame, orient=VERTICAL,
                                   command=canvas.yview, bootstyle=ROUND)
        scroll_frame = ttk.Frame(canvas)

        scroll_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        win_id = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win_id, width=e.width - 4))
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=RIGHT, fill=Y)
        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        self.current_canvas = canvas

        for plugin in merged:
            self._create_row(scroll_frame, plugin)

    # ── Grouped collapsible (software) ────────────────────────────────
    def _populate_software_grouped(self, frame, merged: List[Dict]):
        # Group plugins by field
        field_groups: Dict[str, List[Dict]] = {}
        for plugin in merged:
            info = plugin["local"] or plugin["remote"]
            pid  = plugin["id"]
            field = get_plugin_field(pid, info)
            field_groups.setdefault(field, []).append(plugin)

        # Sort each group alphabetically
        for field in field_groups:
            field_groups[field].sort(
                key=lambda p: (p["local"] or p["remote"]).get("name", p["id"]).lower())

        # Scrollable outer canvas
        canvas    = tk.Canvas(frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame, orient=VERTICAL,
                                   command=canvas.yview, bootstyle=ROUND)
        outer = ttk.Frame(canvas)

        outer.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        win_id = canvas.create_window((0, 0), window=outer, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win_id, width=e.width - 4))
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=RIGHT, fill=Y)
        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        self.current_canvas = canvas

        # Build sections in SCIENTIFIC_FIELDS order, then any extras
        ordered_fields = [name for _, name in SCIENTIFIC_FIELDS if name in field_groups]
        extra_fields   = [f for f in field_groups if f not in ordered_fields]
        for field in ordered_fields + extra_fields:
            self._create_field_section(outer, field, field_groups[field])

    def _create_field_section(self, parent, field: str, plugins: List[Dict]):
        icon      = FIELD_ICON.get(field, "📦")
        collapsed = self._field_collapsed.get(field, False)
        count     = len(plugins)

        # Section container
        section = ttk.Frame(parent)
        section.pack(fill=X, padx=4, pady=(4, 0))

        # Header row (always visible)
        header = ttk.Frame(section, bootstyle=SECONDARY)
        header.pack(fill=X)

        arrow_var = tk.StringVar(value="▶" if collapsed else "▼")

        arrow_btn = ttk.Button(
            header,
            textvariable=arrow_var,
            bootstyle=(SECONDARY, OUTLINE),
            width=3,
        )
        arrow_btn.pack(side=LEFT, padx=(4, 0), pady=2)

        ttk.Label(
            header,
            text=f"  {icon}  {field}",
            font=("Arial", 10, "bold"),
            bootstyle="inverse-secondary",
        ).pack(side=LEFT, pady=4, padx=4)

        ttk.Label(
            header,
            text=f"({count} plugin{'s' if count != 1 else ''})",
            font=("Arial", 8),
            bootstyle="inverse-secondary",
        ).pack(side=LEFT, pady=4)

        # Content frame (plugin rows)
        content = ttk.Frame(section)
        if not collapsed:
            content.pack(fill=X, padx=8, pady=(0, 4))

        def toggle():
            is_now_collapsed = content.winfo_ismapped()
            self._field_collapsed[field] = is_now_collapsed
            if is_now_collapsed:
                content.pack_forget()
                arrow_var.set("▶")
            else:
                content.pack(fill=X, padx=8, pady=(0, 4))
                arrow_var.set("▼")
            # Scroll region update
            parent.update_idletasks()
            canvas = self.current_canvas
            if canvas:
                canvas.configure(scrollregion=canvas.bbox("all"))

        arrow_btn.configure(command=toggle)
        header.bind("<Button-1>", lambda e: toggle())

        ttk.Separator(section).pack(fill=X)

        # Add plugin rows to content
        for plugin in plugins:
            self._create_row(content, plugin)

    # ── Plugin row ────────────────────────────────────────────────────
    def _create_row(self, parent, plugin: Dict):
        local_info  = plugin["local"]
        remote_info = plugin["remote"]
        pid         = plugin["id"]

        if local_info:
            name        = local_info.get("name", pid)
            icon        = local_info.get("icon", "📦")
            version     = local_info.get("version", "0.0.0")
            author      = local_info.get("author", "Unknown")
            description = local_info.get("description", "")
            requires    = local_info.get("requires", [])
            is_broken   = local_info.get("broken", False)
        else:
            name        = remote_info.get("name", pid)
            icon        = remote_info.get("icon", "📦")
            version     = remote_info.get("version", "0.0.0")
            author      = remote_info.get("author", "Unknown")
            description = remote_info.get("description", "")
            requires    = remote_info.get("requires", [])
            is_broken   = False

        remote_version = remote_info.get("version") if remote_info else None
        source_type    = self._get_source_type(pid, local_info is not None, remote_info is not None)
        badge          = self._source_badge(source_type)

        # Row
        row = ttk.Frame(parent, padding=(6, 4))
        row.pack(fill=X, padx=2, pady=1)
        ttk.Separator(parent).pack(fill=X, padx=2)

        # Left: info
        content = ttk.Frame(row)
        content.pack(side=LEFT, fill=BOTH, expand=True)

        # Title — badge + name + version
        title = f"{badge} {icon} {name}"
        if local_info and remote_version and remote_version != version:
            title += f"  v{version}  (store v{remote_version})"
        elif version not in ("0.0.0", "?", ""):
            title += f"  v{version}"
        if is_broken:
            title = f"⚠️ {title}  (broken)"

        ttk.Label(content, text=title,
                  font=("Arial", 10, "bold"),
                  bootstyle=(DANGER if is_broken else DEFAULT)
                  ).pack(anchor=W)

        if description:
            ttk.Label(content, text=description,
                      font=("Arial", 8), bootstyle=SECONDARY,
                      wraplength=400, justify=LEFT
                      ).pack(anchor=W, pady=(2, 0))

        if author and author != "Unknown":
            ttk.Label(content, text=f"by {author}",
                      font=("Arial", 7), bootstyle=SECONDARY
                      ).pack(anchor=W)

        # Right: actions
        actions = ttk.Frame(row)
        actions.pack(side=RIGHT, padx=(10, 0), fill=Y, anchor=N)

        # Dep warning
        if requires:
            met, missing = self._check_deps(requires)
            if not met:
                ttk.Button(
                    actions, text="⚠️ Deps",
                    bootstyle=(WARNING, OUTLINE), width=11,
                    command=lambda m=list(missing), n=name: self._install_deps(n, m),
                ).pack(pady=1, fill=X)

        if local_info and not is_broken:
            # Enable toggle
            var = tk.BooleanVar(value=self.enabled_plugins.get(pid, False))
            var.trace("w", lambda *_: self._update_button_state())
            self.plugin_vars[pid] = var

            ttk.Checkbutton(
                actions, text="Enable",
                variable=var, bootstyle=SUCCESS,
            ).pack(pady=1, fill=X)

            # Update button — only for store or both
            if (source_type in ("store", "both") and
                    remote_version and self._is_newer(remote_version, version)):
                ttk.Button(
                    actions, text="⬆ UPDATE",
                    bootstyle=(WARNING, OUTLINE), width=11,
                    command=lambda ri=remote_info: self._install_from_store(ri, update=True),
                ).pack(pady=1, fill=X)

            # Uninstall
            ttk.Button(
                actions, text="🗑 Uninstall",
                bootstyle=(DANGER, OUTLINE), width=11,
                command=lambda p=pid, li=local_info, st=source_type:
                    self._uninstall_plugin(p, li, st),
            ).pack(pady=1, fill=X)

        elif local_info and is_broken:
            ttk.Label(actions, text="⚠️ Broken", bootstyle=DANGER).pack(pady=1)
            ttk.Button(
                actions, text="🗑 Uninstall",
                bootstyle=(DANGER, OUTLINE), width=11,
                command=lambda p=pid, li=local_info, st=source_type:
                    self._uninstall_plugin(p, li, st),
            ).pack(pady=1, fill=X)

        elif remote_info:
            ttk.Button(
                actions, text="⬇ INSTALL",
                bootstyle=(INFO, OUTLINE), width=11,
                command=lambda ri=remote_info: self._install_from_store(ri),
            ).pack(pady=1, fill=X)

    # ── Smart apply button ────────────────────────────────────────────
    def _update_button_state(self):
        to_enable = to_disable = 0
        for pid, var in self.plugin_vars.items():
            was = self.enabled_plugins.get(pid, False)
            now = var.get()
            if now and not was:   to_enable  += 1
            elif not now and was: to_disable += 1

        if to_enable > 0 and to_disable > 0:
            self.action_btn.configure(
                text=f"⚡ APPLY  ({to_enable}↑ / {to_disable}↓)",
                bootstyle=WARNING)
        elif to_enable > 0:
            self.action_btn.configure(
                text=f"✅ ENABLE {to_enable}", bootstyle=SUCCESS)
        elif to_disable > 0:
            self.action_btn.configure(
                text=f"🔥 DISABLE {to_disable}", bootstyle=DANGER)
        else:
            self.action_btn.configure(
                text="✅ APPLY CHANGES", bootstyle=SUCCESS)

    # ── Menu removal ──────────────────────────────────────────────────
    def _remove_from_menu(self, plugin_id: str, info: dict):
        category = info.get("category", "")
        name     = info.get("name", plugin_id)
        icon     = info.get("icon", "🔌")

        if category == "hardware":
            if hasattr(self.app, "left") and hasattr(self.app.left, "remove_hardware_button"):
                self.app.left.remove_hardware_button(name, icon)
            if hasattr(self.app, "hardware_plugins"):
                self.app.hardware_plugins.pop(plugin_id, None)
            return

        if hasattr(self.app, "advanced_menu"):
            menu = self.app.advanced_menu
            try:
                for i in range(menu.index("end"), -1, -1):
                    try:
                        label = menu.entrycget(i, "label")
                        if name in label or plugin_id in label:
                            menu.delete(i)
                    except Exception:
                        continue
            except Exception:
                pass

    # ── Apply ─────────────────────────────────────────────────────────
    def _apply(self):
        changes = 0

        plugins_to_enable = [
            pid for pid, var in self.plugin_vars.items()
            if var.get() and not self.enabled_plugins.get(pid, False)
        ]
        if plugins_to_enable:
            missing_all = []
            for pid in plugins_to_enable:
                info = next((p for cat in self.local_plugins_by_category.values()
                             for p in cat if p["id"] == pid), None)
                if info and info.get("requires"):
                    met, missing = self._check_deps(info["requires"])
                    if not met:
                        missing_all.append((info.get("name", pid), missing))

            if missing_all:
                msg = "Missing dependencies:\n"
                for name, missing in missing_all:
                    msg += f"• {name}: {', '.join(missing)}\n"
                msg += "\nInstall now?"
                if messagebox.askyesno("Missing Dependencies", msg, parent=self):
                    all_pkgs = {pkg for _, miss in missing_all for pkg in miss}
                    self._install_deps("Dependencies", list(all_pkgs))

        for pid, var in self.plugin_vars.items():
            was = self.enabled_plugins.get(pid, False)
            now = var.get()
            if now != was:
                changes += 1
                self.enabled_plugins[pid] = now
                if not now:
                    info = next((p for cat in self.local_plugins_by_category.values()
                                 for p in cat if p["id"] == pid), None)
                    if info:
                        self._remove_from_menu(pid, info)

        self._save_enabled()
        self._save_ui_state()

        if hasattr(self.app, "_load_plugins"):
            self.app._load_plugins()

        if changes > 0:
            self.status_var.set(f"✅ Applied {changes} changes")
            self.action_btn.configure(text="✅ DONE", bootstyle=SUCCESS)
            self.after(1500, self._on_close)
        else:
            self.status_var.set("⚡ No changes")
            self.after(500, self._on_close)

    # ── Merge logic ───────────────────────────────────────────────────
    def _get_merged_plugins(self, category: str) -> List[Dict]:
        local_dict  = {p["id"]: p for p in self.local_plugins_by_category.get(category, [])}
        remote_dict = {p["id"]: p for p in self.remote_plugins_by_category.get(category, [])}

        merged = []
        for pid, info in local_dict.items():
            merged.append({"id": pid, "local": info,
                           "remote": remote_dict.get(pid), "type": "local"})
        for pid, info in remote_dict.items():
            if pid not in local_dict:
                merged.append({"id": pid, "local": None,
                               "remote": info, "type": "remote"})
        return merged

    # ── Version compare ───────────────────────────────────────────────
    def _is_newer(self, remote: str, local: str) -> bool:
        if HAS_PACKAGING:
            try:
                return Version(remote) > Version(local)
            except Exception:
                return remote > local
        try:
            r = [int(x) for x in remote.split(".")]
            l = [int(x) for x in local.split(".")]
            n = max(len(r), len(l))
            r += [0] * (n - len(r))
            l += [0] * (n - len(l))
            return r > l
        except Exception:
            return remote > local

    # ── Local index ───────────────────────────────────────────────────
    def _ensure_local_index(self):
        index_path      = Path("plugins/plugins.json")
        current_plugins = []
        folder_map = {
            "add-ons":  Path("plugins/add-ons"),
            "software": Path("plugins/software"),
            "hardware": Path("plugins/hardware"),
        }
        for category, folder in folder_map.items():
            if not folder.exists():
                continue
            for py_file in folder.glob("*.py"):
                if py_file.stem in ["__init__", "plugin_manager"]:
                    continue
                info = self._extract_info(py_file, category)
                if info:
                    dl_url = (
                        f"https://gitlab.com/sefy76/scientific-toolkit/-/raw/main/"
                        f"plugins/{category}/{py_file.name}?ref_type=heads"
                    )
                    current_plugins.append({
                        "id":           info["id"],
                        "name":         info.get("name", info["id"]),
                        "version":      info.get("version", "0.0.1"),
                        "description":  info.get("description", ""),
                        "author":       info.get("author", "Unknown"),
                        "category":     category,
                        "field":        get_plugin_field(info["id"], info),
                        "icon":         info.get("icon", "📦"),
                        "requires":     info.get("requires", []),
                        "download_url": dl_url,
                    })

        needs_update = True
        if index_path.exists():
            try:
                with open(index_path, "r") as f:
                    existing = json.load(f)
                if {p["id"] for p in existing} == {p["id"] for p in current_plugins}:
                    needs_update = False
            except Exception:
                pass

        if needs_update:
            with open(index_path, "w", encoding="utf-8") as f:
                json.dump(current_plugins, f, indent=2)

    # ── Install / Update / Uninstall ──────────────────────────────────
    def _install_from_store(self, info: Dict, update: bool = False):
        pid             = info["id"]
        category        = info.get("category", "add-ons")
        download_url    = info.get("download_url", "")
        expected_sha256 = info.get("sha256")
        requires        = info.get("requires", [])
        source_name     = info.get("_source_name", "store")

        if not download_url:
            messagebox.showerror("Error", "No download URL for this plugin.")
            return

        folder_map = {
            "add-ons":  Path("plugins/add-ons"),
            "software": Path("plugins/software"),
            "hardware": Path("plugins/hardware"),
        }
        target_folder = folder_map.get(category)
        if not target_folder:
            messagebox.showerror("Error", f"Unknown category: {category}")
            return
        target_folder.mkdir(parents=True, exist_ok=True)
        target_file = target_folder / f"{pid}.py"

        action   = "Updating" if update else "Installing"
        progress = tk.Toplevel(self)
        progress.title(f"{action} {info.get('name', pid)}")
        progress.geometry("420x130")
        progress.resizable(False, False)
        progress.transient(self)

        ttk.Label(progress,
                  text=f"{action}  {info.get('name', pid)}…",
                  font=("Arial", 10, "bold")).pack(pady=(14, 4))
        dl_status = tk.StringVar(value="Connecting…")
        ttk.Label(progress, textvariable=dl_status,
                  font=("Arial", 8), bootstyle=SECONDARY).pack()
        pbar = ttk.Progressbar(progress, bootstyle=(SUCCESS, STRIPED),
                                mode="indeterminate", length=360)
        pbar.pack(pady=8)
        pbar.start(10)

        def download():
            try:
                with urllib.request.urlopen(download_url, timeout=15) as resp:
                    with tempfile.NamedTemporaryFile(
                            mode="wb", delete=False,
                            dir=target_folder, suffix=".tmp") as tmp:
                        sha256     = hashlib.sha256()
                        total_size = int(resp.headers.get("Content-Length", 0))
                        downloaded = 0
                        while True:
                            chunk = resp.read(8192)
                            if not chunk:
                                break
                            tmp.write(chunk)
                            sha256.update(chunk)
                            downloaded += len(chunk)
                            if total_size:
                                pct = int(100 * downloaded / total_size)
                                progress.after(0, lambda p=pct:
                                    dl_status.set(f"Downloaded {p}%"))
                            else:
                                progress.after(0, lambda d=downloaded:
                                    dl_status.set(f"Downloaded {d} bytes"))
                        tmp_path = tmp.name

                if expected_sha256:
                    if sha256.hexdigest().lower() != expected_sha256.lower():
                        os.unlink(tmp_path)
                        self.after(0, lambda: messagebox.showerror(
                            "Security Error", "SHA-256 hash mismatch"))
                        return

                os.replace(tmp_path, target_file)
                self.after(0, progress.destroy)

                if requires:
                    met, missing = self._check_deps(requires)
                    if not met:
                        def ask_install():
                            if messagebox.askyesno("Missing Dependencies",
                                    f"Plugin requires: {', '.join(missing)}\nInstall now?",
                                    parent=self):
                                self._install_deps(info.get("name", pid), missing)
                        self.after(0, ask_install)

                self.enabled_plugins[pid]  = True
                self.downloaded_plugins.add(pid)
                self._plugin_source[pid]   = source_name
                self._save_downloaded()
                temp_enabled = self.enabled_file.with_suffix(".tmp")
                with open(temp_enabled, "w") as f:
                    json.dump(self.enabled_plugins, f, indent=2)
                temp_enabled.replace(self.enabled_file)

                self.local_plugins_by_category = self._discover_all()
                self.after(0, lambda cat=category: self._refresh_category(cat))

                if hasattr(self.app, "_load_plugins"):
                    self.app.after(0, self.app._load_plugins)

            except Exception as e:
                self.after(0, progress.destroy)
                self.after(0, lambda: messagebox.showerror("Installation Failed", str(e)))

        threading.Thread(target=download, daemon=True).start()

    def _uninstall_plugin(self, pid: str, info: Dict, source_type: str = "local"):
        name = info.get("name", pid)

        # Confirmation message differs by source type
        if source_type == "store":
            confirm = f"Uninstall '{name}'?\n\nThis will DELETE the plugin file."
        elif source_type == "both":
            confirm = (
                f"Remove '{name}' from the plugin list?\n\n"
                f"This is your own local file that also exists on the store.\n"
                f"The .py file will NOT be deleted — you can reinstall from the store anytime."
            )
        else:  # local
            confirm = (
                f"Remove '{name}' from the plugin list?\n\n"
                f"This is a locally developed plugin.\n"
                f"The .py file will NOT be deleted."
            )

        if not messagebox.askyesno("Confirm Uninstall", confirm):
            return

        path = info.get("path")
        try:
            # Only delete the file if it was installed from the store
            if source_type == "store":
                if not path or not Path(path).exists():
                    messagebox.showerror("Error", "File not found")
                    return
                Path(path).unlink()
                self.downloaded_plugins.discard(pid)
                self._plugin_source.pop(pid, None)
                self._save_downloaded()

            if pid in self.enabled_plugins:
                del self.enabled_plugins[pid]
                self._save_enabled()

            for cat in self.local_plugins_by_category:
                self.local_plugins_by_category[cat] = [
                    p for p in self.local_plugins_by_category[cat] if p["id"] != pid
                ]

            self._refresh_current_tab()

        except Exception as e:
            messagebox.showerror("Error", f"Could not uninstall: {e}")

    # ── Helpers ───────────────────────────────────────────────────────
    def _center_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth()  // 2) - (self.winfo_width()  // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")


def setup_plugin(main_app):
    return PluginManager(main_app)
