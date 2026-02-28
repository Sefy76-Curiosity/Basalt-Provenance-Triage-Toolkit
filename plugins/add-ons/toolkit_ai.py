"""
Toolkit AI Assistant v2.2 — Plugin-Aware Deep Knowledge System
===================================================
Now with plugin recommendations, auto-installation, and intelligent usage!
Can suggest relevant plugins based on your data and workflow.

New Features:
  • Plugin recommendation engine
  • One-click installation from store
  • Automatic dependency handling
  • Smart plugin suggestions based on data type
  • Integration with Plugin Manager v3.0
"""

import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import threading
import json
import sqlite3
import ast
import importlib.util
from pathlib import Path
from collections import defaultdict
import time
from datetime import datetime
import re
import hashlib
import queue
import urllib.request
import urllib.error
import tempfile
import os
import sys
import subprocess
from typing import Optional, Dict, List, Tuple, Any

# Try to import Plugin Manager if available
try:
    import importlib
    plugin_manager = importlib.import_module('plugins.add-ons.plugin_manager')
    PluginManager = plugin_manager.PluginManager
    HAS_PLUGIN_MANAGER = True
except ImportError:
    HAS_PLUGIN_MANAGER = False

# ─────────────────────────────────────────────────────────────────────────────
PLUGIN_INFO = {
    'id':          'toolkit_ai',
    'name':        'Toolkit AI',
    'category':    'add-ons',
    'icon':        '🧠',
    'version':     '2.2',
    'requires':    [],
    'description': 'Deep-knowledge AI assistant — recommends and installs plugins for you!',
}
# ─────────────────────────────────────────────────────────────────────────────
# BUILT-IN TOOLKIT KNOWLEDGE
# ─────────────────────────────────────────────────────────────────────────────

_TOOLKIT_STRUCTURE = """
The Scientific Toolkit is a multi-panel desktop application built with Python and ttkbootstrap.

PANELS:
  Left Panel   — Import data (CSV, Excel), add samples manually, launch hardware devices.
  Center Panel — Main data table with pagination, search, filter, plots, and plugin tabs.
  Right Panel  — Classification HUD (v2) + field-specific analysis panels (v3.0).
                 Switches automatically when data type is detected.

ENGINES:
  Classification Engine — Applies geochemical/scientific classification schemes to samples.
  Protocol Engine       — Runs measurement protocols for hardware instruments.

DATA FLOW:
  Hardware/Import → DataHub → Observers notified → Center + Right panels update.
  DataHub is the single source of truth for all sample data.

CLASSIFICATION WORKFLOW:
  1. Import or collect data into the table.
  2. In the right panel, select a classification scheme from the dropdown.
  3. Click Apply to classify all rows (or selected rows only).
  4. Results appear in the HUD and colour-code the table.
  5. Double-click any row for full classification detail.
  6. Use "Run All Schemes" to run every available scheme at once.

FIELD PANELS (v3.0):
  When data is loaded, the right panel detects its type and offers to switch to
  a specialised panel. 16 scientific domains are supported. Use the ← Back
  button to return to the classification HUD at any time.
"""

# Hardware plugin id → field panel id mapping
_HW_TO_FIELD = {
    "archaeology_archaeometry_unified_suite":     "archaeology",
    "barcode_scanner_unified_suite":              "archaeology",   # museum collections
    "chromatography_analytical_unified_suite":    "chromatography",
    "clinical_molecular_diagnostics_suite":       "molecular",
    "electrochemistry_unified_suite":             "electrochem",
    "elemental_geochemistry_unified_suite":       "geochemistry",
    "geophysics_unified_suite":                   "geophysics",
    "materials_characterization_unified_suite":   "materials",
    "meteorology_environmental_unified_suite":    "meteorology",
    "molecular_biology_unified_suite":            "molecular",
    "physical_properties_unified_suite":          "physics",
    "physics_test_and_measurement_suite":         "physics",
    "solution_chemistry_unified_suite":           "solution",
    "spectroscopy_unified_suite":                 "spectroscopy",
    "thermal_analysis_calorimetry_unified_suite": "materials",
    "zooarchaeology_unified_suite":               "zooarch",
}

# Field panel id → human description
_FIELD_DESCRIPTIONS = {
    "geochemistry":   "Major and trace element geochemistry. Summarises oxide totals, "
                      "computes Mg#, FeOt, and alkali sums.",
    "geochronology":  "Radiometric dating data. Handles U-Pb, Ar-Ar, and similar systems.",
    "petrology":      "Modal/normative mineralogy and petrogenetic diagrams.",
    "structural":     "Structural measurements: strike, dip, plunge, trend, azimuth.",
    "geophysics":     "Geophysical surveys: seismic, gravity, magnetics, ERT.",
    "spatial":        "GIS and spatial data: latitude/longitude, UTM, easting/northing.",
    "archaeology":    "Lithic and artifact morphometrics, museum catalogue data.",
    "zooarch":        "Zooarchaeological assemblage: NISP, MNI, taxon, element.",
    "spectroscopy":   "Spectral data: wavelength/wavenumber vs intensity (FTIR, Raman, UV-Vis).",
    "chromatography": "Chromatography: retention time, peak area, m/z, abundance.",
    "electrochem":    "Electrochemical measurements: potential, current, impedance, scan rate.",
    "materials":      "Materials characterisation: stress, strain, hardness, modulus.",
    "solution":       "Water/solution chemistry: pH, conductivity, TDS, alkalinity.",
    "molecular":      "Molecular biology / clinical: Ct, Cq, melt temperature, qPCR.",
    "meteorology":    "Meteorological data: temperature, humidity, pressure, wind, rainfall.",
    "physics":        "Physics and test/measurement: time-series, FFT, signal, voltage.",
}

# Plugin categories and their typical use cases
_PLUGIN_RECOMMENDATIONS = {
    "Geology & Geochemistry": [
        ("compositional_stats_pro", "📊 Compositional Data Analysis",
         "For Aitchison geometry, CLR transforms, and compositional statistics"),
        ("geochemical_explorer", "🔬 Geochemical Explorer",
         "PCA, LDA, clustering for geochemical fingerprinting"),
        ("advanced_normative_calculations", "⚖️ Normative Calculator",
         "CIPW norms and mineral modes from bulk chemistry"),
        ("thermobarometry_suite", "🌡️ Thermobarometry",
         "P-T calculations from mineral compositions"),
        ("petrogenetic_modeling_suite", "🔥 Petrogenetic Modeling",
         "AFC, fractional crystallization, partial melting models"),
    ],
    "Archaeology & Archaeometry": [
        ("museum_import", "🏛️ Museum Database",
         "Import artifacts from 15+ museums worldwide"),
        ("lithic_morphometrics", "🪨 Lithic Analysis",
         "Artifact outline extraction, edge damage quantification"),
        ("archaeometry_analysis_suite_ultimate", "🔬 Archaeometry Suite",
         "XRD, SEM-EDS, micro-CT, OSL, GPR analysis"),
        ("report_generator", "📄 Report Generator",
         "Auto-generate excavation reports and IAA submissions"),
        ("photo_manager", "📸 Photo Manager",
         "Link and organize field photographs with samples"),
    ],
    "Spectroscopy": [
        ("spectral_toolbox", "📈 Spectral Toolbox",
         "Peak detection, baseline correction, smoothing, derivatives"),
        ("spectroscopy_analysis_suite", "🔬 Spectroscopy Suite",
         "Library search, calibration, MCR-ALS analysis"),
    ],
    "GIS & Spatial Science": [
        ("quartz_gis_pro", "🗺️ Quartz GIS",
         "Complete GIS for archaeologists - measure, viewshed, QGIS export"),
        ("gis_3d_viewer_pro", "🌍 3D GIS Viewer",
         "2D maps, 3D terrain, SRTM data, web maps"),
        ("spatial_kriging", "📊 Spatial Kriging",
         "Variogram analysis, interpolation, contouring"),
        ("google_earth_pro", "🌎 Google Earth Pro",
         "3D visualization with geochemical extrusion"),
    ],
    "Geophysics": [
        ("geophysics_analysis_suite", "🌋 Geophysics Suite",
         "Seismic, ERT, gravity, magnetics, GPR processing"),
    ],
    "Zooarchaeology": [
        ("zooarchaeology_analysis_suite", "🦴 Zooarchaeology Suite",
         "NISP/MNI, age-at-death, taphonomy, 3D morphometrics"),
    ],
    "Chromatography & Analytical Chemistry": [
        ("chromatography_analysis_suite", "🧪 Chromatography Suite",
         "Peak integration, Kovats indices, AMDIS, standard curves"),
    ],
    "Electrochemistry": [
        ("electrochemistry_analysis_suite", "⚡ Electrochemistry Suite",
         "CV, EIS, Tafel, battery analysis, chrono methods"),
    ],
    "Materials Science": [
        ("materials_science_analysis_suite", "🧱 Materials Science",
         "Tensile, nanoindentation, BET, rheology, DMA"),
    ],
    "Molecular Biology & Clinical Diagnostics": [
        ("clinical_diagnostics_analysis_suite", "🧬 Clinical Suite",
         "qPCR, ΔΔCt, ELISA, flow cytometry, ddPCR"),
        ("molecular_biology_suite", "🔬 Molecular Biology",
         "Cell counting, colony counter, fluorescence analysis"),
    ],
    "General": [
        ("pca_lda_explorer", "📊 PCA/LDA Explorer",
         "Complete multivariate statistics with visualizations"),
        ("uncertainty_propagation", "🎲 Uncertainty Propagation",
         "Monte Carlo methods, confidence ellipses, error propagation"),
        ("publication_layouts", "📑 Publication Layouts",
         "Professional multi-panel figure designer"),
        ("dataprep_pro", "🧹 DataPrep Pro",
         "Outlier detection, missing imputation, robust normalization"),
        ("batch_processor", "📁 Batch Processor",
         "Process multiple CSV files at once"),
        ("scripting_console", "🐍 Python Console",
         "Interactive Python console with data access"),
    ],
}

# Plugin dependencies mapping
_PLUGIN_DEPENDENCIES = {
    "compositional_stats_pro": ["numpy", "scipy", "scikit-learn", "matplotlib"],
    "geochemical_explorer": ["numpy", "scipy", "matplotlib", "pandas", "scikit-learn"],
    "advanced_normative_calculations": ["pandas", "numpy", "scipy", "matplotlib"],
    "thermobarometry_suite": ["numpy", "scipy", "matplotlib", "pandas"],
    "petrogenetic_modeling_suite": ["numpy", "scipy", "matplotlib", "pandas"],
    "museum_import": ["requests", "bs4"],
    "lithic_morphometrics": ["opencv-python", "scikit-image", "numpy", "scipy", "matplotlib"],
    "archaeometry_analysis_suite_ultimate": ["numpy", "pandas", "scipy", "matplotlib", "pillow"],
    "report_generator": ["python-docx"],
    "photo_manager": ["pillow"],
    "spectral_toolbox": ["numpy", "scipy", "pybaselines", "lmfit", "matplotlib"],
    "spectroscopy_analysis_suite": ["numpy", "pandas", "scipy", "matplotlib"],
    "quartz_gis_pro": ["geopandas", "shapely", "pyproj", "matplotlib", "contextily"],
    "gis_3d_viewer_pro": ["matplotlib", "numpy", "scipy", "requests"],
    "spatial_kriging": ["numpy", "scipy", "matplotlib"],
    "google_earth_pro": ["simplekml", "numpy", "scipy", "pillow"],
    "geophysics_analysis_suite": ["numpy", "pandas", "scipy", "matplotlib"],
    "zooarchaeology_analysis_suite": ["numpy", "pandas", "scipy", "matplotlib"],
    "chromatography_analysis_suite": ["numpy", "pandas", "scipy", "matplotlib"],
    "electrochemistry_analysis_suite": ["numpy", "pandas", "scipy", "matplotlib"],
    "materials_science_analysis_suite": ["numpy", "pandas", "scipy", "matplotlib"],
    "clinical_diagnostics_analysis_suite": ["numpy", "pandas", "scipy", "matplotlib"],
    "molecular_biology_suite": ["numpy", "pandas", "scipy", "matplotlib"],
    "pca_lda_explorer": ["scikit-learn", "matplotlib", "numpy", "pandas", "scipy", "seaborn"],
    "uncertainty_propagation": ["numpy", "scipy", "matplotlib"],
    "publication_layouts": ["matplotlib", "numpy", "pillow", "seaborn"],
    "dataprep_pro": ["numpy", "pandas", "scipy", "scikit-learn"],
    "batch_processor": ["pandas", "numpy"],
    "scripting_console": ["tkinter"],
}

# Store URL for plugin index
_PLUGIN_STORE_URL = "https://gitlab.com/sefy76/scientific-toolkit/-/raw/main/plugins/plugins.json?ref_type=heads"


# ─────────────────────────────────────────────────────────────────────────────
# KNOWLEDGE BASE
# ─────────────────────────────────────────────────────────────────────────────

class KnowledgeBase:
    """
    Scans the toolkit at startup and builds an in-memory knowledge index.
    Uses disk caching to avoid rescans on every startup.
    Never crashes — every read is wrapped in try/except.
    """

    def __init__(self, app):
        self.app = app
        self.plugins   = {}    # plugin_id → {name, field, description, icon, category, path}
        self.schemes   = {}    # scheme_id → {name, description, fields_needed, classifications}
        self.elements  = {}    # element standard name → {display_name, variations, group}
        self.errors    = []    # non-fatal scan errors for diagnostics

        # Cache settings
        self.cache_file = Path("config/ai_knowledge_cache.json")
        self.cache_ttl = 3600  # 1 hour

        # Try loading from cache first
        if not self._load_from_cache():
            # Full scan if cache missing/expired
            self._scan_plugins()
            self._scan_schemes()
            self._load_elements()
            self._save_to_cache()

    def _load_from_cache(self):
        """Load knowledge from cache if it exists and is fresh."""
        if not self.cache_file.exists():
            return False

        try:
            # Check cache age
            mtime = self.cache_file.stat().st_mtime
            if time.time() - mtime > self.cache_ttl:
                return False  # Cache expired

            # Load cached data
            cached = json.loads(self.cache_file.read_text(encoding="utf-8"))
            self.plugins = cached.get('plugins', {})
            self.schemes = cached.get('schemes', {})
            self.elements = cached.get('elements', {})
            self.errors = cached.get('errors', [])

            return True

        except Exception as e:
            self.errors.append(f"Cache load error: {e}")
            return False

    def _save_to_cache(self):
        """Save current knowledge to cache file."""
        try:
            # Ensure config directory exists
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)

            cache = {
                'plugins': self.plugins,
                'schemes': self.schemes,
                'elements': self.elements,
                'errors': self.errors,
                'timestamp': time.time()
            }
            self.cache_file.write_text(
                json.dumps(cache, indent=2, default=str),
                encoding="utf-8"
            )
        except Exception as e:
            self.errors.append(f"Cache save error: {e}")

    # ── Plugin scanning ───────────────────────────────────────────────────────

    def _scan_plugins(self):
        base = Path("plugins")
        for category in ["hardware", "software", "add-ons"]:
            pdir = base / category
            if not pdir.exists():
                continue
            for py_file in pdir.glob("*.py"):
                if py_file.stem in ("__init__", "plugin_manager"):
                    continue
                self._read_plugin_file(py_file, category)

    def _read_plugin_file(self, path, category):
        """Extract PLUGIN_INFO from a plugin file without importing it."""
        try:
            src = path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(src)
            for node in ast.walk(tree):
                if (isinstance(node, ast.Assign)
                        and any(
                            isinstance(t, ast.Name) and t.id == "PLUGIN_INFO"
                            for t in node.targets
                        )):
                    info = ast.literal_eval(node.value)
                    pid  = info.get("id", path.stem)
                    self.plugins[pid] = {
                        "id":          pid,
                        "name":        info.get("name",        path.stem),
                        "description": info.get("description", ""),
                        "icon":        info.get("icon",        "🔧"),
                        "field":       info.get("field",       ""),
                        "category":    category,
                        "path":        str(path),
                        "stem":        path.stem,
                    }
                    return
            # No PLUGIN_INFO found — still register with minimal info
            self.plugins[path.stem] = {
                "id": path.stem, "name": path.stem, "description": "",
                "icon": "🔧", "field": "", "category": category,
                "path": str(path), "stem": path.stem,
            }
        except Exception as e:
            self.errors.append(f"scan {path.name}: {e}")

    # ── Scheme scanning ───────────────────────────────────────────────────────

    def _scan_schemes(self):
        """Read classification scheme JSON files from engines/ directory."""
        # Primary location
        for search_dir in [Path("engines/classification"), Path("engines")]:
            if not search_dir.exists():
                continue
            for jf in search_dir.glob("*.json"):
                self._read_scheme_file(jf)

        # Also pull from live engine if available
        if hasattr(self.app, "classification_engine"):
            try:
                for s in self.app.classification_engine.get_available_schemes():
                    sid = s.get("id", "")
                    if sid and sid not in self.schemes:
                        self.schemes[sid] = {
                            "id":              sid,
                            "name":            s.get("name", sid),
                            "description":     s.get("description", ""),
                            "fields_needed":   s.get("required_fields", []),
                            "classifications": [],
                            "icon":            s.get("icon", "📊"),
                        }
            except Exception as e:
                self.errors.append(f"scheme engine scan: {e}")

    def _read_scheme_file(self, path):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            # Handle both single-scheme and multi-scheme JSON
            schemes = data if isinstance(data, list) else [data]
            for s in schemes:
                sid = s.get("id") or s.get("name", path.stem)
                # Gather unique classification labels
                labels = set()
                for field_data in s.get("classifications", {}).values():
                    if isinstance(field_data, dict):
                        labels.update(field_data.keys())
                    elif isinstance(field_data, list):
                        labels.update(field_data)
                self.schemes[sid] = {
                    "id":              sid,
                    "name":            s.get("name",         sid),
                    "description":     s.get("description",  ""),
                    "fields_needed":   s.get("required_fields",
                                            s.get("fields", [])),
                    "classifications": sorted(labels),
                    "icon":            s.get("icon", "📊"),
                    "source_file":     path.name,
                }
        except Exception as e:
            self.errors.append(f"scheme file {path.name}: {e}")

    # ── Element knowledge ─────────────────────────────────────────────────────

    def _load_elements(self):
        """Load chemical element knowledge from app or config file."""
        # Try from app (already loaded)
        if hasattr(self.app, "chemical_elements") and self.app.chemical_elements:
            for std_name, info in self.app.chemical_elements.items():
                self.elements[std_name] = info
            return
        # Fallback: read directly
        try:
            path = Path("config/chemical_elements.json")
            if path.exists():
                data = json.loads(path.read_text(encoding="utf-8"))
                for std_name, info in data.get("elements", {}).items():
                    self.elements[std_name] = info
        except Exception as e:
            self.errors.append(f"elements: {e}")

    # ── Query helpers ─────────────────────────────────────────────────────────

    def find_plugin(self, query):
        """Fuzzy-find a plugin by name, id, or field. Returns best match or None."""
        q = query.lower()
        # Exact id match
        if q in self.plugins:
            return self.plugins[q]
        # Name / description contains
        best = None
        for p in self.plugins.values():
            if (q in p["name"].lower()
                    or q in p["description"].lower()
                    or q in p["stem"].lower()
                    or q in p["field"].lower()):
                best = p
                break
        return best

    def find_scheme(self, query):
        """Fuzzy-find a classification scheme. Returns best match or None."""
        q = query.lower()
        if q in self.schemes:
            return self.schemes[q]
        for s in self.schemes.values():
            if (q in s["name"].lower()
                    or q in s["id"].lower()
                    or q in s.get("description", "").lower()):
                return s
        return None

    def find_element(self, query):
        """Look up a chemical element or oxide."""
        q = query.upper().replace(" ", "")
        # Direct match on standard name
        if q in self.elements:
            return self.elements[q]
        # Match on variations
        for std, info in self.elements.items():
            if q in [v.upper() for v in info.get("variations", [])]:
                return {**info, "_standard": std}
        return None

    def get_all_scheme_names(self):
        """Return list of all scheme names for autocomplete."""
        return [s["name"] for s in self.schemes.values()]

    def get_all_plugin_names(self):
        """Return list of all plugin names for autocomplete."""
        return [p["name"] for p in self.plugins.values()]

    def summary(self):
        """Return a one-line knowledge summary."""
        return (f"{len(self.plugins)} plugins, "
                f"{len(self.schemes)} classification schemes, "
                f"{len(self.elements)} chemical elements/oxides indexed.")


# ─────────────────────────────────────────────────────────────────────────────
# CONTEXT ENGINE
# ─────────────────────────────────────────────────────────────────────────────

class ContextEngine:
    """
    Reads the current live state of the application.
    Never modifies anything — read-only.
    """

    def __init__(self, app):
        self.app = app

    def get_data_context(self):
        """Return rich summary of currently loaded data."""
        samples = self.app.data_hub.get_all() if hasattr(self.app, "data_hub") else []
        if not samples:
            return {"loaded": False, "count": 0}

        # Gather all columns
        columns = {}
        for s in samples:
            for k, v in s.items():
                if k not in columns:
                    columns[k] = []
                try:
                    columns[k].append(float(v))
                except (ValueError, TypeError):
                    pass   # non-numeric — skip for stats

        stats = {}
        missing_counts = {}
        for col, vals in columns.items():
            missing = sum(1 for s in samples if not s.get(col)
                          or str(s.get(col, "")).strip() in ("", "None", "nan"))
            missing_counts[col] = missing
            if vals:
                stats[col] = {
                    "mean":    round(sum(vals) / len(vals), 4),
                    "min":     round(min(vals), 4),
                    "max":     round(max(vals), 4),
                    "n":       len(vals),
                    "missing": missing,
                }

        return {
            "loaded":   True,
            "count":    len(samples),
            "columns":  list(columns.keys()),
            "stats":    stats,
            "missing":  missing_counts,
            "sample_id_col": "Sample_ID" if "Sample_ID" in columns else None,
        }

    def get_classification_context(self):
        """Return current classification results if any."""
        right = getattr(self.app, "right", None)
        if not right:
            return {"has_results": False}

        results  = getattr(right, "classification_results", [])
        all_mode = getattr(right, "all_mode", False)
        scheme   = getattr(right, "scheme_var",
                           type("_", (), {"get": lambda s: ""})()).get()

        classified = [r for r in results if r]
        if not classified:
            return {"has_results": False}

        # Count classifications
        class_counts = defaultdict(int)
        conf_vals    = []
        for r in classified:
            cls  = r.get("classification", "UNCLASSIFIED")
            conf = r.get("confidence", 0.0)
            class_counts[cls] += 1
            conf_vals.append(conf)

        avg_conf = round(sum(conf_vals) / len(conf_vals), 3) if conf_vals else 0

        return {
            "has_results":   True,
            "scheme":        scheme,
            "all_mode":      all_mode,
            "classified":    len(classified),
            "class_counts":  dict(class_counts),
            "avg_confidence":avg_conf,
            "flagged":       sum(1 for r in classified if r.get("flag_for_review")),
        }

    def get_active_panel(self):
        right = getattr(self.app, "right", None)
        if not right:
            return "classification"
        return getattr(right, "_current_field_panel", "classification")

    def get_enabled_plugins(self):
        enabled = getattr(self.app, "enabled_plugins", {})
        return [k for k, v in enabled.items() if v]

    def get_available_schemes(self):
        right = getattr(self.app, "right", None)
        if not right:
            return []
        scheme_list = getattr(right, "scheme_list", [])
        return [(display, sid) for display, sid in scheme_list
                if sid != "__ALL__"]

    def detect_data_type(self):
        """Detect what kind of scientific data is loaded."""
        ctx = self.get_data_context()
        if not ctx["loaded"]:
            return None
        cols = {c.lower() for c in ctx["columns"]}

        checks = [
            ("geochemistry",   ["sio2", "tio2", "al2o3", "fe2o3", "mgo", "cao"]),
            ("spectroscopy",   ["wavelength", "wavenumber", "absorbance", "raman", "ftir"]),
            ("geochronology",  ["pb206", "pb207", "u238", "ar40", "ar39", "age"]),
            ("structural",     ["strike", "dip", "plunge", "azimuth", "bearing"]),
            ("spatial",        ["latitude", "longitude", "easting", "northing"]),
            ("solution",       ["ph", "conductivity", "alkalinity", "tds"]),
            ("zooarch",        ["nisp", "mni", "taxon", "element"]),
            ("molecular",      ["ct", "cq", "melt_temp", "qpcr"]),
            ("meteorology",    ["humidity", "rainfall", "wind_speed", "dew"]),
            ("chromatography", ["retention_time", "peak_area", "abundance"]),
            ("materials",      ["stress", "strain", "modulus", "hardness"]),
            ("electrochem",    ["potential", "scan_rate", "impedance"]),
        ]
        best_field, best_score = None, 0
        for field, frags in checks:
            score = sum(1 for f in frags if any(f in c for c in cols))
            if score > best_score:
                best_score, best_field = score, field
        return best_field if best_score >= 2 else "general"


# ─────────────────────────────────────────────────────────────────────────────
# ACTION EXECUTOR
# ─────────────────────────────────────────────────────────────────────────────

class ActionExecutor:
    """
    Executes actions in the toolkit on the user's behalf.
    Always confirms with the user before doing anything.
    """

    def __init__(self, app, ui_callback):
        self.app         = app
        self.ui_callback = ui_callback   # function(text, tag) to write to chat

    def _confirm(self, prompt_text):
        return messagebox.askyesno(
            "Toolkit AI — Confirm Action", prompt_text,
            parent=self.app.root
        )

    def run_classification(self, scheme_display=None):
        """Run a classification scheme on the loaded data."""
        right = getattr(self.app, "right", None)
        if not right:
            return "⚠️ Classification panel is not available."

        if not self.app.data_hub.get_all():
            return "⚠️ No data loaded. Import a file first."

        # Find the scheme in the dropdown
        if scheme_display:
            scheme_list = getattr(right, "scheme_list", [])
            match = None
            for display, sid in scheme_list:
                if (scheme_display.lower() in display.lower()
                        or scheme_display.lower() in sid.lower()):
                    match = display
                    break
            if not match:
                available = [d for d, _ in scheme_list if _ != "__ALL__"]
                return (f"⚠️ Scheme '{scheme_display}' not found.\n"
                        f"Available: {', '.join(available[:8])}")
            right.scheme_var.set(match)

        scheme_name = right.scheme_var.get() or "current scheme"
        if not self._confirm(f"Run '{scheme_name}' on all loaded data?"):
            return "Action cancelled."

        try:
            right._run_classification()
            return f"✅ Running '{scheme_name}'. Results will appear in the HUD."
        except Exception as e:
            return f"⚠️ Classification failed: {e}"

    def run_classification_with_progress(self, scheme_display=None):
        """Run classification with a progress bar."""
        right = getattr(self.app, "right", None)
        if not right:
            return "⚠️ Classification panel is not available."

        if not self.app.data_hub.get_all():
            return "⚠️ No data loaded. Import a file first."

        # Show progress window
        progress_win = tk.Toplevel(self.app.root)
        progress_win.title("Running Classification")
        progress_win.geometry("300x100")
        progress_win.transient(self.app.root)
        progress_win.grab_set()

        ttk.Label(progress_win, text=f"Running classification...").pack(pady=10)
        progress = ttk.Progressbar(progress_win, mode='indeterminate')
        progress.pack(fill=tk.X, padx=20, pady=10)
        progress.start(10)

        def run():
            try:
                result = self.run_classification(scheme_display)
                progress_win.after(0, progress_win.destroy)
                self.ui_callback(f"🧠 {result}\n", "assistant")
            except Exception as e:
                progress_win.after(0, progress_win.destroy)
                self.ui_callback(f"⚠️ Error: {e}\n", "warn")

        threading.Thread(target=run, daemon=True).start()
        return "⏳ Starting classification (check progress window)..."

    def switch_field_panel(self, field_id):
        """Switch the right panel to a field-specific panel."""
        right = getattr(self.app, "right", None)
        if not right:
            return "⚠️ Right panel not available."

        field_name = _FIELD_DESCRIPTIONS.get(field_id, field_id).split(".")[0]
        if not self._confirm(f"Switch right panel to '{field_id}'?"):
            return "Action cancelled."
        try:
            right._load_field_panel(field_id)
            return f"✅ Switched to {field_id} panel."
        except Exception as e:
            return f"⚠️ Could not switch panel: {e}"

    def open_plugin(self, plugin_id, plugin_name):
        """Open a software or hardware plugin window."""
        # Software plugins
        loaded = getattr(self.app, "_loaded_plugin_info", {})
        if plugin_id in loaded:
            if not self._confirm(f"Open '{plugin_name}'?"):
                return "Action cancelled."
            try:
                loaded[plugin_id]["command"]()
                return f"✅ Opened {plugin_name}."
            except Exception as e:
                return f"⚠️ Could not open plugin: {e}"

        # Hardware plugins
        hw = getattr(self.app, "hardware_plugins", {})
        if plugin_id in hw:
            if not self._confirm(f"Open hardware plugin '{plugin_name}'?"):
                return "Action cancelled."
            try:
                hw[plugin_id]["instance"].open_window()
                return f"✅ Opened {plugin_name}."
            except Exception as e:
                return f"⚠️ Could not open hardware plugin: {e}"

        return f"⚠️ Plugin '{plugin_name}' is not currently loaded/enabled."

    def run_all_schemes(self):
        """Run all classification schemes at once."""
        right = getattr(self.app, "right", None)
        if not right:
            return "⚠️ Right panel not available."
        if not self.app.data_hub.get_all():
            return "⚠️ No data loaded."
        n = self.app.data_hub.row_count()
        if not self._confirm(
                f"Run ALL classification schemes on {n} sample(s)?\n"
                "This may take a moment."):
            return "Action cancelled."
        try:
            right.scheme_var.set("🔁 Run All Schemes")
            right._run_classification()
            return "✅ Running all schemes. Results will appear in the HUD."
        except Exception as e:
            return f"⚠️ Failed: {e}"


# ─────────────────────────────────────────────────────────────────────────────
# INTENT PARSER
# ─────────────────────────────────────────────────────────────────────────────

class IntentParser:
    """
    Parses a natural-language prompt into an intent + entities.
    Returns dict: {intent, entity, raw}
    """

    def __init__(self):
        # Intent patterns — order matters (more specific first)
        self._PATTERNS = [
            # Actions
            ("online_search", [
                r"search (?:online|the web) for (.+)",
                r"look up (.+) online",
                r"what does the internet say about (.+)",
                r"what's new about (.+)",
                r"latest (?:research|findings) on (.+)",
            ]),
            ("run_all",       [r"run all", r"all schemes", r"classify with all"]),
            ("run_scheme",    [r"run (.+)", r"classify with (.+)", r"apply (.+) scheme",
                               r"use (.+) classification", r"(.+) classification",
                               r"classify (?:my|the) data (?:with|using) (.+)",
                               r"help me classify (?:with|using) (.+)",
                               r"can you (?:run|apply) (.+) (?:scheme|classification)"]),
            ("open_plugin",   [r"open (.+)", r"launch (.+)", r"start (.+)",
                               r"show me (.+) plugin"]),
            ("switch_panel",  [r"switch to (.+) panel", r"go to (.+) panel",
                               r"use (.+) panel", r"(.+) panel please"]),
            # Explanations
            ("explain_class", [r"what is (.+)", r"what does (.+) mean",
                               r"explain (.+)", r"tell me about (.+)",
                               r"what('s| is) (.+)\?", r"what('s| is) the meaning of (.+)",
                               r"define (.+)", r"what does (.+) (?:mean|stand for)"]),
            ("explain_element",[r"what is (.+)\?", r"tell me about (.+) element",
                                r"what does (.+) stand for"]),
            # Data queries
            ("analyze_data",  [r"analyz", r"what('s| is) in my data",
                               r"summarize", r"summary", r"describe my data",
                               r"what can you tell me about (?:my|the) data",
                               r"give me (?:an |)overview of (?:my|the) data",
                               r"analyze (?:my|the) (?:dataset|samples)"]),
            ("validate_data", [r"check my data", r"any (problems|issues|errors)",
                               r"data quality", r"validate", r"what('s)? wrong"]),
            ("statistics",    [r"statistics", r"stats", r"usage", r"what have you learned",
                               r"how many"]),
            ("list_schemes",  [r"list.*(scheme|classification)", r"what schemes",
                               r"available scheme", r"which (scheme|classification)"]),
            ("list_plugins",  [r"list.*plugin", r"what plugin", r"available plugin",
                               r"what tool", r"show.*plugin"]),
            ("current_data",  [r"current data", r"loaded data", r"my data",
                               r"what data", r"how many sample"]),
            ("suggest_next",  [r"what should i", r"next step", r"what('s)? next",
                               r"suggest", r"recommend", r"what to do"]),
            ("workflow",      [r"how do i", r"how to", r"workflow", r"getting started"]),
            ("status",        [r"status", r"active panel", r"current panel",
                               r"what('s)? running"]),
            ("help",          [r"help", r"what can you do", r"capabilities"]),
            ("export_learning", [r"export learning", r"export data", r"save my history",
                                r"backup ai", r"export conversations"]),

            # NEW PLUGIN RECOMMENDATION PATTERNS
            ("recommend_plugins", [
                r"recommend (?:some |)plugins",
                r"suggest (?:some |)plugins",
                r"what plugins (?:should I use|are good)",
                r"plugin recommendations",
                r"any (?:good|useful) plugins",
            ]),
            ("recommend_workflow", [
                r"recommend plugins for (.+)",
                r"suggest plugins for (.+)",
                r"what plugins (?:for|to use for) (.+)",
                r"plugins? for (.+)",
                r"tools for (.+)",
            ]),
            ("install_plugin", [
                r"install (.+)",
                r"download (.+) plugin",
                r"get (.+) (?:plugin|tool)",
                r"add (.+) plugin",
            ]),
            ("enable_plugin", [
                r"enable (.+)",
                r"turn on (.+) plugin",
                r"activate (.+)",
            ]),
            ("list_store", [
                r"list (?:store|available) plugins",
                r"what('s| is) (?:in|on) the store",
                r"show (?:store|available) plugins",
                r"browse (?:store|plugins)",
            ]),
            ("plugin_status", [
                r"what plugins (?:are|do I have) (?:installed|enabled)",
                r"list (?:my |)installed plugins",
                r"show (?:my |)enabled plugins",
                r"check (?:installed|enabled) plugins",
            ]),
        ]

    def parse(self, prompt):
        pl = prompt.lower().strip()
        for intent, patterns in self._PATTERNS:
            for pat in patterns:
                m = re.search(pat, pl)
                if m:
                    entity = m.group(1).strip() if m.lastindex else None
                    return {"intent": intent, "entity": entity, "raw": prompt}
        return {"intent": "unknown", "entity": None, "raw": prompt}


# ─────────────────────────────────────────────────────────────────────────────
# AUTOCOMPLETE ENTRY
# ─────────────────────────────────────────────────────────────────────────────

class AutocompleteEntry(ttk.Entry):
    """Entry widget with autocomplete suggestions."""

    def __init__(self, master, knowledge_base, **kwargs):
        super().__init__(master, **kwargs)
        self.kb = knowledge_base
        self._listbox = None
        self._suggestions = []

        # Common commands for autocomplete
        self.commands = [
            "analyze my data",
            "check my data for problems",
            "list classification schemes",
            "list plugins",
            "run all schemes",
            "what should I do next",
            "switch to geochemistry panel",
            "switch to spectroscopy panel",
            "run TAS",
            "what is MORB?",
            "what does SiO2 mean?",
            "export learning data",
            "help",
            "status",
            # NEW COMMANDS
            "recommend plugins",
            "plugins for petrology",
            "install compositional_stats_pro",
            "enable pca_lda_explorer",
            "list store",
            "what plugins do I have",
        ]

        self.bind('<KeyRelease>', self._on_keyrelease)
        self.bind('<FocusOut>', self._on_focusout)

    def _on_keyrelease(self, event):
        if event.keysym in ('Return', 'Escape', 'Up', 'Down', 'Tab'):
            return
        self._show_completions()

    def _on_focusout(self, event):
        # Delay hiding to allow click on listbox
        self.after(200, self._hide_completions)

    def _show_completions(self):
        current = self.get().lower()
        if not current or len(current) < 2:
            self._hide_completions()
            return

        # Collect suggestions
        suggestions = set()

        # Add static commands
        for cmd in self.commands:
            if current in cmd.lower():
                suggestions.add(cmd)

        # Add scheme names
        for scheme in self.kb.schemes.values():
            if current in scheme['name'].lower():
                suggestions.add(f"run {scheme['name']}")

        # Add plugin names
        for plugin in self.kb.plugins.values():
            if current in plugin['name'].lower():
                suggestions.add(f"open {plugin['name']}")

        # Add element symbols
        for element in self.kb.elements:
            if current in element.lower():
                suggestions.add(f"what is {element}?")

        self._suggestions = sorted(list(suggestions))[:8]  # Limit to 8 suggestions

        if self._suggestions:
            self._show_dropdown()
        else:
            self._hide_completions()

    def _show_dropdown(self):
        if self._listbox:
            self._hide_completions()

        # Create listbox
        self._listbox = tk.Listbox(
            self.master,
            height=min(6, len(self._suggestions)),
            bg="#2b2b2b",
            fg="#cdd6f4",
            selectbackground="#89b4fa",
            selectforeground="#1e1e2e",
            font=("Segoe UI", 9),
            relief=tk.FLAT
        )

        # Position below entry
        x = self.winfo_x()
        y = self.winfo_y() + self.winfo_height()
        self._listbox.place(x=x, y=y, width=self.winfo_width())

        # Add items
        for suggestion in self._suggestions:
            self._listbox.insert(tk.END, suggestion)

        # Bindings
        self._listbox.bind('<ButtonRelease-1>', self._on_select)
        self._listbox.bind('<Return>', self._on_select)
        self._listbox.bind('<Escape>', lambda e: self._hide_completions())

    def _hide_completions(self):
        if self._listbox:
            self._listbox.destroy()
            self._listbox = None

    def _on_select(self, event):
        if not self._listbox:
            return
        selection = self._listbox.curselection()
        if selection:
            text = self._listbox.get(selection[0])
            self.delete(0, tk.END)
            self.insert(0, text)
            self.icursor(tk.END)
            self.event_generate('<Return>')  # Trigger send
        self._hide_completions()


# ─────────────────────────────────────────────────────────────────────────────
# PLUGIN RECOMMENDER
# ─────────────────────────────────────────────────────────────────────────────

class PluginRecommender:
    """
    Recommends and installs plugins based on user's data and workflow.
    """

    def __init__(self, app, ai_plugin):
        self.app = app
        self.ai = ai_plugin
        self.store_index = None
        self.store_fetched = False
        self._fetch_lock = threading.Lock()

    def fetch_store_index(self, force=False):
        """Fetch the plugin store index."""
        if self.store_fetched and not force:
            return self.store_index is not None

        with self._fetch_lock:
            try:
                with urllib.request.urlopen(_PLUGIN_STORE_URL, timeout=10) as resp:
                    self.store_index = json.loads(resp.read().decode("utf-8"))
                    self.store_fetched = True
                    return True
            except Exception as e:
                print(f"Failed to fetch plugin store: {e}")
                self.store_fetched = False
                return False

    def get_installed_plugins(self) -> set:
        """Return set of installed plugin IDs."""
        installed = set()

        # Check all categories for installed plugins
        categories = ["add-ons", "software", "hardware"]
        for cat in categories:
            folder = Path(f"plugins/{cat}")
            if folder.exists():
                for py_file in folder.glob("*.py"):
                    if py_file.stem not in ["__init__", "plugin_manager"]:
                        installed.add(py_file.stem)
        return installed

    def get_enabled_plugins(self) -> set:
        """Return set of enabled plugin IDs."""
        enabled_file = Path("config/enabled_plugins.json")
        if enabled_file.exists():
            try:
                with open(enabled_file) as f:
                    enabled = json.load(f)
                return {pid for pid, state in enabled.items() if state}
            except:
                pass
        return set()

    def get_plugin_info(self, plugin_id: str) -> Optional[Dict]:
        """Get plugin info from store or local installation."""
        # First check if it's in store index
        if self.store_index:
            for plugin in self.store_index:
                if plugin["id"] == plugin_id:
                    return plugin

        # Then check local
        categories = ["add-ons", "software", "hardware"]
        for cat in categories:
            folder = Path(f"plugins/{cat}")
            if folder.exists():
                py_file = folder / f"{plugin_id}.py"
                if py_file.exists():
                    try:
                        with open(py_file, "r", encoding="utf-8") as f:
                            tree = ast.parse(f.read())
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Assign):
                                for target in node.targets:
                                    if isinstance(target, ast.Name) and target.id == "PLUGIN_INFO":
                                        return ast.literal_eval(node.value)
                    except:
                        pass
        return None

    def recommend_for_data_type(self, data_type: str, max_recommendations: int = 5) -> List[Dict]:
        """Recommend plugins based on detected data type."""
        installed = self.get_installed_plugins()
        enabled = self.get_enabled_plugins()

        # Map data types to plugin categories
        type_to_category = {
            "geochemistry": "Geology & Geochemistry",
            "geochronology": "Geochronology & Dating",
            "petrology": "Petrology & Mineralogy",
            "structural": "Structural Geology",
            "geophysics": "Geophysics",
            "spatial": "GIS & Spatial Science",
            "archaeology": "Archaeology & Archaeometry",
            "zooarch": "Zooarchaeology",
            "spectroscopy": "Spectroscopy",
            "chromatography": "Chromatography & Analytical Chemistry",
            "electrochem": "Electrochemistry",
            "materials": "Materials Science",
            "solution": "Solution Chemistry",
            "molecular": "Molecular Biology & Clinical Diagnostics",
            "meteorology": "Meteorology & Environmental Science",
            "physics": "Physics & Test/Measurement",
            "general": "General",
        }

        category = type_to_category.get(data_type, "General")
        recommendations = []

        # Get recommendations for this category
        if category in _PLUGIN_RECOMMENDATIONS:
            for pid, name, desc in _PLUGIN_RECOMMENDATIONS[category]:
                if pid not in installed:
                    plugin_info = self.get_plugin_info(pid)
                    if plugin_info:
                        recommendations.append({
                            "id": pid,
                            "name": name,
                            "description": desc,
                            "category": category,
                            "installed": False,
                            "enabled": False,
                            "info": plugin_info,
                            "requires": _PLUGIN_DEPENDENCIES.get(pid, []),
                        })
                elif pid not in enabled:
                    recommendations.append({
                        "id": pid,
                        "name": name,
                        "description": desc,
                        "category": category,
                        "installed": True,
                        "enabled": False,
                        "requires": _PLUGIN_DEPENDENCIES.get(pid, []),
                    })

        return recommendations[:max_recommendations]

    def suggest_plugins_for_workflow(self, workflow: str) -> List[Dict]:
        """Suggest plugins for specific workflows."""
        workflow_plugins = {
            "petrology": ["advanced_normative_calculations", "thermobarometry_suite",
                         "petrogenetic_modeling_suite", "virtual_microscopy_pro"],
            "provenance": ["literature_comparison", "pca_lda_explorer", "geochemical_explorer"],
            "dating": ["dating_integration", "geochronology_suite", "isotope_mixing_models"],
            "mapping": ["quartz_gis_pro", "gis_3d_viewer_pro", "google_earth_pro",
                       "spatial_kriging", "interactive_contouring"],
            "publication": ["publication_layouts", "advanced_export", "report_generator"],
            "quality_control": ["dataprep_pro", "uncertainty_propagation", "data_validation_filter"],
            "multivariate": ["pca_lda_explorer", "geochemical_explorer"],
            "spectral": ["spectral_toolbox", "spectroscopy_analysis_suite"],
            "chromatography": ["chromatography_analysis_suite"],
            "electrochemistry": ["electrochemistry_analysis_suite"],
            "materials": ["materials_science_analysis_suite"],
            "clinical": ["clinical_diagnostics_analysis_suite", "molecular_biology_suite"],
            "archaeology": ["museum_import", "lithic_morphometrics", "photo_manager"],
        }

        installed = self.get_installed_plugins()
        suggestions = []

        workflow_lower = workflow.lower()
        for key, plugin_list in workflow_plugins.items():
            if key in workflow_lower:
                for pid in plugin_list:
                    if pid not in installed:
                        plugin_info = self.get_plugin_info(pid)
                        if plugin_info:
                            suggestions.append({
                                "id": pid,
                                "name": plugin_info.get("name", pid),
                                "description": plugin_info.get("description", ""),
                                "installed": False,
                                "enabled": False,
                                "info": plugin_info,
                                "requires": _PLUGIN_DEPENDENCIES.get(pid, []),
                            })

        return suggestions[:8]

    def install_plugin(self, plugin_id: str, callback=None):
        """Install a plugin from the store."""
        if not self.store_index and not self.fetch_store_index():
            return "❌ Cannot fetch plugin store. Check your internet connection."

        # Find plugin in store
        plugin_info = None
        for p in self.store_index:
            if p["id"] == plugin_id:
                plugin_info = p
                break

        if not plugin_info:
            return f"❌ Plugin '{plugin_id}' not found in store."

        # Check if already installed
        installed = self.get_installed_plugins()
        if plugin_id in installed:
            return f"ℹ️ Plugin '{plugin_info.get('name', plugin_id)}' is already installed."

        # Install with progress
        return self._perform_installation(plugin_info, callback)

    def _perform_installation(self, plugin_info: Dict, callback=None) -> str:
        """Perform the actual installation."""
        pid = plugin_info["id"]
        category = plugin_info.get("category", "add-ons")
        download_url = plugin_info.get("download_url", "")

        if not download_url:
            return f"❌ No download URL for '{pid}'."

        folder_map = {
            "add-ons": Path("plugins/add-ons"),
            "software": Path("plugins/software"),
            "hardware": Path("plugins/hardware"),
        }

        target_folder = folder_map.get(category)
        if not target_folder:
            return f"❌ Unknown category: {category}"

        target_folder.mkdir(parents=True, exist_ok=True)
        target_file = target_folder / f"{pid}.py"

        # Create progress window
        progress_win = tk.Toplevel(self.app.root)
        progress_win.title(f"Installing {plugin_info.get('name', pid)}")
        progress_win.geometry("400x150")
        progress_win.transient(self.app.root)

        ttk.Label(progress_win,
                 text=f"Installing {plugin_info.get('name', pid)}...",
                 font=("Arial", 10, "bold")).pack(pady=10)

        status_var = tk.StringVar(value="Downloading...")
        ttk.Label(progress_win, textvariable=status_var).pack()

        progress = ttk.Progressbar(progress_win, mode='indeterminate')
        progress.pack(fill=tk.X, padx=20, pady=10)
        progress.start(10)

        def download():
            try:
                with urllib.request.urlopen(download_url, timeout=30) as resp:
                    with tempfile.NamedTemporaryFile(
                            mode="wb", delete=False,
                            dir=target_folder, suffix=".tmp") as tmp:
                        total_size = int(resp.headers.get("Content-Length", 0))
                        downloaded = 0

                        while True:
                            chunk = resp.read(8192)
                            if not chunk:
                                break
                            tmp.write(chunk)
                            downloaded += len(chunk)

                            if total_size:
                                pct = int(100 * downloaded / total_size)
                                progress_win.after(0, lambda p=pct:
                                    status_var.set(f"Downloaded {p}%"))

                        tmp_path = tmp.name

                os.replace(tmp_path, target_file)

                # Check dependencies
                requires = plugin_info.get("requires", [])
                if requires:
                    progress_win.after(0, lambda: status_var.set("Checking dependencies..."))
                    missing = self._check_dependencies(requires)
                    if missing:
                        def ask_install_deps():
                            if messagebox.askyesno(
                                "Missing Dependencies",
                                f"Plugin requires: {', '.join(missing)}\nInstall now?",
                                parent=progress_win):
                                self._install_dependencies(missing, progress_win)

                        progress_win.after(0, ask_install_deps)

                progress_win.after(0, progress_win.destroy)

                # Auto-enable the plugin
                self._enable_plugin(pid)

                if callback:
                    self.app.root.after(0, callback)

                return f"✅ Successfully installed {plugin_info.get('name', pid)}"

            except Exception as e:
                progress_win.after(0, progress_win.destroy)
                return f"❌ Installation failed: {e}"

        threading.Thread(target=download, daemon=True).start()
        return f"⏳ Installing {plugin_info.get('name', pid)}..."

    def _check_dependencies(self, requires: List[str]) -> List[str]:
        """Check which dependencies are missing."""
        import_mapping = {
            "google-generativeai": "google.generativeai",
            "opencv-python": "cv2",
            "opencv-contrib-python": "cv2",
            "pillow": "PIL",
            "scikit-learn": "sklearn",
            "scikit-image": "skimage",
            "python-docx": "docx",
        }

        missing = []
        for pkg in requires:
            if pkg == "ctypes":
                continue
            import_name = import_mapping.get(pkg, pkg)
            try:
                if importlib.util.find_spec(import_name) is None:
                    missing.append(pkg)
            except:
                missing.append(pkg)

        return missing

    def _install_dependencies(self, packages: List[str], parent_win):
        """Install Python dependencies via pip."""
        dep_win = tk.Toplevel(parent_win)
        dep_win.title("Installing Dependencies")
        dep_win.geometry("600x300")

        text = tk.Text(dep_win, wrap=tk.WORD, font=("Consolas", 9))
        scroll = ttk.Scrollbar(dep_win, orient=VERTICAL, command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        text.pack(side=LEFT, fill=BOTH, expand=True, padx=5, pady=5)
        scroll.pack(side=RIGHT, fill=Y)

        def run_pip():
            text.insert(tk.END, f"$ pip install {' '.join(packages)}\n\n")
            proc = subprocess.Popen(
                [sys.executable, "-m", "pip", "install"] + packages,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1
            )
            for line in proc.stdout:
                text.insert(tk.END, line)
                text.see(tk.END)
            proc.wait()

            if proc.returncode == 0:
                text.insert(tk.END, "\n✅ Dependencies installed successfully!\n")
                text.insert(tk.END, "Closing in 2 seconds...\n")
                dep_win.after(2000, dep_win.destroy)
            else:
                text.insert(tk.END, f"\n❌ Installation failed (code {proc.returncode})\n")

        threading.Thread(target=run_pip, daemon=True).start()

    def _enable_plugin(self, plugin_id: str):
        """Enable a plugin in the enabled_plugins.json."""
        enabled_file = Path("config/enabled_plugins.json")

        if enabled_file.exists():
            try:
                with open(enabled_file) as f:
                    enabled = json.load(f)
            except:
                enabled = {}
        else:
            enabled = {}

        enabled[plugin_id] = True

        temp = enabled_file.with_suffix(".tmp")
        with open(temp, "w") as f:
            json.dump(enabled, f, indent=2)
        temp.replace(enabled_file)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN AI PLUGIN CLASS
# ─────────────────────────────────────────────────────────────────────────────

class ToolkitAIPlugin:
    """Main plugin class — now with plugin recommendations!"""

    def __init__(self, main_app):
        self.app     = main_app
        self.name    = "Toolkit AI"
        self.version = "2.2"
        self.app.toolkit_ai = self

        # Thread safety
        self._thread_lock = threading.Lock()
        self._db_queue = queue.Queue()
        self.running = True

        # State
        self.enabled = True
        self.data_dir = Path("config/ai_learning")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Config + DB
        self.config = self._load_config()
        self._init_database()

        # Background threads
        self.learning_queue = []  # Initialize learning queue
        self._last_cleanup = time.time()  # Add this for cleanup tracking
        self._cleanup_interval = 300  # 5 minutes

        self._start_learning_thread()
        self._start_db_worker_thread()

        # Build knowledge base
        self.kb      = KnowledgeBase(main_app)
        self.ctx     = ContextEngine(main_app)
        self.intent  = IntentParser()

        # Plugin recommender (NEW)
        self.recommender = PluginRecommender(main_app, self)

        # UI elements (set in create_tab)
        self.chat_output  = None
        self.chat_input   = None
        self.question_var = None
        self._action_exec = None

        # Conversation memory: list of (role, text) last 20
        self._history = []

        # Fetch store index in background
        self._start_store_fetch()

    def _start_store_fetch(self):
        """Fetch plugin store index in background."""
        def fetch():
            self.recommender.fetch_store_index()
        threading.Thread(target=fetch, daemon=True).start()

    # ─────────────────────────────────────────────────────────────────────────
    # CONFIG & DATABASE
    # ─────────────────────────────────────────────────────────────────────────

    def _load_config(self):
        f = self.data_dir / "config.json"
        if f.exists():
            try:
                with open(f) as fp:
                    return json.load(fp)
            except:
                pass
        return {"enabled": True, "learning_level": "balanced",
                "suggestions_enabled": True, "auto_learn": True}

    def _save_config(self):
        try:
            with open(self.data_dir / "config.json", "w") as fp:
                json.dump(self.config, fp, indent=2)
        except Exception as e:
            print(f"AI config save error: {e}")

    def _init_database(self):
        """Initialize database with thread-safe settings."""
        self.conn = sqlite3.connect(
            self.data_dir / "learning.db",
            check_same_thread=False,  # Required for multi-threaded access
            timeout=10  # Timeout for locked database
        )
        c = self.conn.cursor()

        c.execute('''CREATE TABLE IF NOT EXISTS data_preferences
                     (data_type TEXT, panel_id TEXT, use_count INTEGER DEFAULT 0,
                      PRIMARY KEY (data_type, panel_id))''')
        c.execute('''CREATE TABLE IF NOT EXISTS actions
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                      action_type TEXT, details TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS components
                     (name TEXT PRIMARY KEY, usage_count INTEGER DEFAULT 0,
                      last_used DATETIME)''')
        c.execute('''CREATE TABLE IF NOT EXISTS conversations
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                      role TEXT, message TEXT)''')

        # Index for faster queries
        c.execute('''CREATE INDEX IF NOT EXISTS idx_conversations_timestamp
                     ON conversations(timestamp)''')

        self.conn.commit()

    def _start_learning_thread(self):
        """Start background learning thread."""
        self._learning_thread = threading.Thread(
            target=self._background_learner,
            daemon=True
        )
        self._learning_thread.start()

    def _start_db_worker_thread(self):
        """Start database worker thread for async operations."""
        self._db_thread = threading.Thread(
            target=self._db_worker,
            daemon=True
        )
        self._db_thread.start()

    def _db_worker(self):
        """Process database operations asynchronously."""
        while self.running:
            try:
                # Get operation from queue with timeout
                op = self._db_queue.get(timeout=1)
                if op is None:
                    continue

                with self._thread_lock:
                    cursor = self.conn.cursor()
                    try:
                        if op['type'] == 'insert_action':
                            cursor.execute(
                                "INSERT INTO actions (action_type, details) VALUES (?,?)",
                                (op['action_type'], json.dumps(op.get('details', {})))
                            )
                        elif op['type'] == 'update_component':
                            cursor.execute(
                                '''INSERT INTO components (name, usage_count, last_used)
                                   VALUES (?,1,CURRENT_TIMESTAMP)
                                   ON CONFLICT(name) DO UPDATE SET
                                       usage_count=usage_count+1,
                                       last_used=CURRENT_TIMESTAMP''',
                                (op['component'],)
                            )
                        elif op['type'] == 'insert_conversation':
                            cursor.execute(
                                "INSERT INTO conversations (role, message) VALUES (?,?)",
                                (op['role'], op['message'])
                            )
                        elif op['type'] == 'update_preference':
                            cursor.execute(
                                '''INSERT INTO data_preferences (data_type, panel_id, use_count)
                                   VALUES (?,?,1)
                                   ON CONFLICT(data_type, panel_id) DO UPDATE SET
                                       use_count=use_count+1''',
                                (op['data_type'], op['panel_id'])
                            )
                        self.conn.commit()
                    except Exception as e:
                        print(f"DB worker error: {e}")
                        self.conn.rollback()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"DB worker error: {e}")
                time.sleep(1)

    def _background_learner(self):
        """Background thread for learning tasks."""
        while self.running and self.enabled:
            try:
                now = time.time()

                # Periodic cleanup
                if now - self._last_cleanup > self._cleanup_interval:
                    self._cleanup_old_data()
                    self._last_cleanup = now

                # Process learning queue
                if hasattr(self, 'learning_queue') and self.learning_queue:
                    if self.config.get("auto_learn", True):
                        with self._thread_lock:
                            batch = self.learning_queue[:10]
                            self.learning_queue = self.learning_queue[10:]
                            for action in batch:
                                self._db_queue.put({
                                    'type': 'insert_action',
                                    'action_type': action["type"],
                                    'details': action.get("details", {})
                                })
                                if action.get("component"):
                                    self._db_queue.put({
                                        'type': 'update_component',
                                        'component': action["component"]
                                    })
                time.sleep(2)

            except Exception as e:
                print(f"AI learning error: {e}")
                time.sleep(5)

    def _cleanup_old_data(self):
        """Remove old conversation history to prevent DB bloat."""
        try:
            with self._thread_lock:
                cursor = self.conn.cursor()
                # Keep last 1000 conversations, delete older
                cursor.execute("""
                    DELETE FROM conversations
                    WHERE id NOT IN (
                        SELECT id FROM conversations
                        ORDER BY timestamp DESC
                        LIMIT 1000
                    )
                """)
                self.conn.commit()
        except Exception as e:
            print(f"Cleanup error: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # PUBLIC API
    # ─────────────────────────────────────────────────────────────────────────

    def record_action(self, action_type, component=None, details=None):
        if not self.enabled or not self.config.get("auto_learn", True):
            return
        if not hasattr(self, 'learning_queue'):
            self.learning_queue = []
        self.learning_queue.append({
            "type": action_type, "component": component,
            "details": details or {}, "time": time.time()})

    def record_panel_choice(self, data_type, panel_id):
        if not self.enabled:
            return
        self._db_queue.put({
            'type': 'update_preference',
            'data_type': data_type,
            'panel_id': panel_id
        })

    def suggest_panel(self, data_type):
        with self._thread_lock:
            c = self.conn.cursor()
            c.execute(
                '''SELECT panel_id, use_count FROM data_preferences
                   WHERE data_type=? ORDER BY use_count DESC LIMIT 1''',
                (data_type,))
            r = c.fetchone()
        return r[0] if r else None

    def export_learning_data(self, filepath=None):
        """Export anonymized learning data for backup or analysis."""
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = self.data_dir / f"ai_export_{timestamp}.json"

        data = {
            'actions': [],
            'preferences': [],
            'conversations': [],
            'export_date': datetime.now().isoformat(),
            'version': self.version
        }

        with self._thread_lock:
            c = self.conn.cursor()

            # Export actions
            c.execute("SELECT action_type, details, timestamp FROM actions ORDER BY timestamp")
            for row in c.fetchall():
                data['actions'].append({
                    'type': row[0],
                    'details': json.loads(row[1]) if row[1] else {},
                    'timestamp': row[2]
                })

            # Export preferences
            c.execute("SELECT data_type, panel_id, use_count FROM data_preferences")
            data['preferences'] = [
                {'data_type': row[0], 'panel': row[1], 'count': row[2]}
                for row in c.fetchall()
            ]

            # Export conversations (last 500)
            c.execute("""
                SELECT role, message, timestamp FROM conversations
                ORDER BY timestamp DESC LIMIT 500
            """)
            data['conversations'] = [
                {'role': row[0], 'message': row[1], 'timestamp': row[2]}
                for row in c.fetchall()
            ]

        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)

        return str(filepath)

    # ─────────────────────────────────────────────────────────────────────────
    # UI
    # ─────────────────────────────────────────────────────────────────────────

    def create_tab(self, parent):
        """Called by center panel to build the AI tab."""
        try:
            # Lazy-create action executor
            self._action_exec = ActionExecutor(
                self.app,
                lambda text, tag: self._append(text, tag))

            frame = ttk.Frame(parent, bootstyle="dark")
            frame.pack(fill=tk.BOTH, expand=True)

            # ── Top info bar ──────────────────────────────────────────────────
            info_bar = ttk.Frame(frame, bootstyle="secondary")
            info_bar.pack(fill=tk.X, padx=4, pady=(4, 0))
            self._status_lbl = ttk.Label(
                info_bar,
                text=f"🧠 Toolkit AI v2.2  •  {self.kb.summary()}",
                font=("Segoe UI", 8),
                bootstyle="inverse-secondary",
            )
            self._status_lbl.pack(side=tk.LEFT, padx=6, pady=2)

            # Export button
            ttk.Button(
                info_bar,
                text="📤 Export",
                command=self._export_dialog,
                bootstyle="secondary-link",
                width=8
            ).pack(side=tk.RIGHT, padx=4, pady=2)

            # ── Chat output ───────────────────────────────────────────────────
            chat_frame = ttk.Frame(frame, bootstyle="dark")
            chat_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

            self.chat_output = tk.Text(
                chat_frame,
                wrap=tk.WORD,
                font=("Segoe UI", 10),
                bg="#1e1e2e",
                fg="#cdd6f4",
                relief=tk.FLAT,
                padx=10, pady=10,
                state=tk.NORMAL,
            )
            sb = ttk.Scrollbar(
                chat_frame, orient="vertical",
                command=self.chat_output.yview,
                bootstyle="dark-round")
            self.chat_output.configure(yscrollcommand=sb.set)
            self.chat_output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            sb.pack(side=tk.RIGHT, fill=tk.Y)

            # Text tags
            self.chat_output.tag_configure(
                "user",      foreground="#89dceb",
                font=("Segoe UI", 10, "bold"))
            self.chat_output.tag_configure(
                "assistant", foreground="#cba6f7",
                font=("Segoe UI", 10))
            self.chat_output.tag_configure(
                "action",    foreground="#a6e3a1",
                font=("Segoe UI", 10, "italic"))
            self.chat_output.tag_configure(
                "system",    foreground="#6c7086",
                font=("Segoe UI", 9, "italic"))
            self.chat_output.tag_configure(
                "header",    foreground="#f38ba8",
                font=("Segoe UI", 10, "bold"))
            self.chat_output.tag_configure(
                "warn",      foreground="#fab387",
                font=("Segoe UI", 10))

            # ── Quick-action buttons ──────────────────────────────────────────
            quick_frame = ttk.Frame(frame, bootstyle="dark")
            quick_frame.pack(fill=tk.X, padx=4, pady=(0, 2))

            quick_btns = [
                ("📊 Data",         "analyze my data"),
                ("✅ Validate",     "check my data for problems"),
                ("🔍 Schemes",      "list classification schemes"),
                ("🧩 Plugins",      "list available plugins"),
                ("🔌 Recommend",    "recommend plugins"),  # NEW
                ("💡 Next Step",    "what should I do next?"),
            ]
            for label, query in quick_btns:
                ttk.Button(
                    quick_frame, text=label, width=10,
                    command=lambda q=query: self._quick_ask(q),
                    bootstyle="secondary-outline",
                ).pack(side=tk.LEFT, padx=2, pady=2)

            # ── Input row ─────────────────────────────────────────────────────
            input_frame = ttk.Frame(frame, bootstyle="dark")
            input_frame.pack(fill=tk.X, padx=4, pady=(0, 4))

            self.question_var = tk.StringVar()

            # Use autocomplete entry
            self.chat_input = AutocompleteEntry(
                input_frame,
                knowledge_base=self.kb,
                textvariable=self.question_var,
                font=("Segoe UI", 10),
                bootstyle="light",
            )

            # Add placeholder
            self.chat_input.insert(0, "Ask me something... (e.g., 'recommend plugins')")
            self.chat_input.bind('<FocusIn>', self._clear_placeholder)
            self.chat_input.bind('<FocusOut>', self._set_placeholder)
            self.chat_input.bind('<Key>', self._clear_placeholder)  # Add this line
            self.chat_input.bind("<Return>", lambda e: self._send_message())

            self.chat_input.pack(
                side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))

            ttk.Button(
                input_frame, text="Send",
                command=self._send_message,
                bootstyle="primary", width=8,
            ).pack(side=tk.RIGHT, padx=(0, 2))

            ttk.Button(
                input_frame, text="⚙️",
                command=self.show_settings,
                bootstyle="secondary", width=3,
            ).pack(side=tk.RIGHT, padx=2)

            self._display_welcome()

        except Exception as e:
            import traceback; traceback.print_exc()
            ttk.Label(parent, text=f"AI load error: {e}",
                      foreground="red").pack(padx=20, pady=20)

    def _clear_placeholder(self, event=None):
        current = self.chat_input.get()
        if current == "Ask me something... (e.g., 'recommend plugins')":
            self.chat_input.delete(0, tk.END)

    def _set_placeholder(self, event):
        if not self.chat_input.get():
            self.chat_input.insert(0, "Ask me something... (e.g., 'recommend plugins')")

    def _display_welcome(self):
        if not self.chat_output:
            return

        self._append("🧠 Toolkit AI v2.2 — Plugin-Aware Deep Knowledge Assistant\n", "header")
        self._append("─" * 52 + "\n", "system")

        # What I know
        self._append(f"📚 Knowledge: {self.kb.summary()}\n", "system")

        # Plugin store status
        if self.recommender.store_fetched:
            store_count = len(self.recommender.store_index) if self.recommender.store_index else 0
            self._append(f"📦 Store: {store_count} plugins available\n", "system")
        else:
            self._append("📦 Store: fetching in background...\n", "system")

        # Scan warnings
        if self.kb.errors:
            self._append(f"⚠️  {len(self.kb.errors)} minor scan issue(s) (non-critical)\n", "warn")

        # Current data
        dc = self.ctx.get_data_context()
        if dc["loaded"]:
            dtype = self.ctx.detect_data_type()
            self._append(
                f"📊 Data loaded: {dc['count']} samples, "
                f"{len(dc['columns'])} columns"
                + (f" — detected as {dtype}" if dtype else "") + "\n",
                "system")

            # Show plugin recommendations hint
            self._append(
                f"💡 Type 'recommend plugins' for {dtype}-specific tool suggestions!\n",
                "assistant")
        else:
            self._append("📊 No data loaded yet. Import a file to begin.\n", "system")

        self._append("\nTry asking me:\n", "assistant")
        examples = [
            "  • 'Analyze my data'",
            "  • 'Recommend plugins' (NEW!)",
            "  • 'Plugins for petrology'",
            "  • 'Install compositional_stats_pro'",
            "  • 'What classification schemes are available?'",
            "  • 'Run TAS classification'",
            "  • 'What is MORB?'",
            "  • 'What plugins do I have?'",
            "  • 'Switch to geochemistry panel'",
        ]
        self._append("\n".join(examples) + "\n\n", "system")

    def _append(self, text, tag="assistant"):
        if not self.chat_output:
            return
        self.chat_output.insert(tk.END, text, tag)
        self.chat_output.see(tk.END)

    def _quick_ask(self, query):
        self.question_var.set(query)
        self._send_message()

    def _send_message(self, event=None):
        if not self.chat_output or not self.chat_input:
            return
        question = self.question_var.get().strip()

        # Check for placeholder
        if not question or question == "Ask me something... (e.g., 'recommend plugins')":
            return

        self.question_var.set("")
        self._set_placeholder(None)  # Restore placeholder

        self._append(f"\n👤 You: {question}\n", "user")
        self._append("🧠 Thinking...\n", "system")
        self.chat_output.update()

        # Process in thread to keep UI responsive
        def _run():
            try:
                response = self.query(question)
            except Exception as e:
                response = f"⚠️ Error: {e}"
            self.chat_output.after(0, self._finish_response, response, question)

        threading.Thread(target=_run, daemon=True).start()

    def _finish_response(self, response, question):
        # Remove "Thinking..." line
        try:
            start = self.chat_output.search(
                "🧠 Thinking...\n", "1.0", tk.END)
            if start:
                end = f"{start}+{len('🧠 Thinking...') + 1}c"
                self.chat_output.delete(start, end)
        except:
            pass
        self._append(f"🧠 {response}\n", "assistant")
        self._log_conversation("user", question)
        self._log_conversation("assistant", response)

    def _log_conversation(self, role, message):
        try:
            self._db_queue.put({
                'type': 'insert_conversation',
                'role': role,
                'message': message[:500]  # Limit message length
            })
        except:
            pass
        self._history.append((role, message))
        if len(self._history) > 20:
            self._history = self._history[-20:]

    def _export_dialog(self):
        """Show export dialog."""
        from tkinter import filedialog

        filename = filedialog.asksaveasfilename(
            title="Export AI Learning Data",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=str(self.data_dir),
            initialfile=f"ai_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        if filename:
            try:
                exported_file = self.export_learning_data(filename)
                self._append(f"✅ Data exported to: {exported_file}\n", "system")
            except Exception as e:
                self._append(f"⚠️ Export failed: {e}\n", "warn")

    # ─────────────────────────────────────────────────────────────────────────
    # MAIN QUERY ENTRY POINT
    # ─────────────────────────────────────────────────────────────────────────

    def query(self, prompt):
        """Updated query method with new intents."""
        if not self.enabled:
            return "Toolkit AI is disabled. Enable it in ⚙️ Settings."

        parsed = self.intent.parse(prompt)
        intent = parsed["intent"]
        entity = parsed["entity"]

        # Record query for learning
        self.record_action("ai_query", details={"intent": intent, "prompt": prompt[:80]})

        dispatch = {
            # Existing handlers
            "help":           self._resp_help,
            "analyze_data":   self._resp_analyze_data,
            "validate_data":  self._resp_validate_data,
            "current_data":   self._resp_current_data,
            "statistics":     self._resp_statistics,
            "list_schemes":   self._resp_list_schemes,
            "list_plugins":   self._resp_list_plugins,
            "explain_class":  lambda: self._resp_explain(entity),
            "explain_element":lambda: self._resp_explain_element(entity),
            "run_scheme":     lambda: self._resp_run_scheme(entity),
            "run_all":        self._resp_run_all,
            "open_plugin":    lambda: self._resp_open_plugin(entity),
            "switch_panel":   lambda: self._resp_switch_panel(entity),
            "suggest_next":   self._resp_suggest_next,
            "workflow":       self._resp_workflow,
            "status":         self._resp_status,
            "export_learning": self._resp_export_learning,
            "online_search":  lambda: self._resp_online_search(entity),

            # NEW plugin recommendation handlers
            "recommend_plugins": self._resp_recommend_plugins,
            "recommend_workflow": lambda: self._resp_recommend_for_workflow(entity),
            "install_plugin": lambda: self._resp_install_plugin(entity),
            "enable_plugin": lambda: self._resp_enable_plugin(entity),
            "list_store": self._resp_list_store,
            "plugin_status": self._resp_plugin_status,
        }

        handler = dispatch.get(intent)
        if handler:
            return handler()
        return self._resp_fallback(prompt)

    # ─────────────────────────────────────────────────────────────────────────
    # NEW RESPONSE GENERATORS FOR PLUGIN RECOMMENDATIONS
    # ─────────────────────────────────────────────────────────────────────────

    def _resp_recommend_plugins(self, entity=None):
        """Recommend plugins based on current context."""
        dc = self.ctx.get_data_context()

        if not dc["loaded"]:
            # No data loaded - suggest general plugins
            recommendations = []
            for category, plugins in list(_PLUGIN_RECOMMENDATIONS.items())[:3]:
                for pid, name, desc in plugins[:2]:
                    recommendations.append(f"  • {name}: {desc}")

            lines = [
                "🔌 Plugin Recommendations (General):",
                "I notice you don't have data loaded yet. Here are some useful plugins:",
                "",
                "\n".join(recommendations[:6]),
                "",
                "To get personalized recommendations, load your data first!",
                "",
                "Try: 'recommend plugins for petrology' or 'what plugins for mapping?'"
            ]
            return "\n".join(lines)

        # Get recommendations based on data type
        dtype = self.ctx.detect_data_type()
        recommendations = self.recommender.recommend_for_data_type(dtype, max_recommendations=8)

        if not recommendations:
            return f"📦 No specific plugin recommendations for {dtype} data at this time."

        lines = [
            f"🔌 Plugin Recommendations for {dtype.upper()} data:",
            ""
        ]

        for rec in recommendations:
            status = "📦" if not rec["installed"] else "✅" if rec["enabled"] else "⚠️"
            status_text = " (not installed)" if not rec["installed"] else " (disabled)" if not rec["enabled"] else ""

            lines.append(f"{status} {rec['name']}{status_text}")
            lines.append(f"   {rec['description']}")

            if not rec["installed"]:
                lines.append(f"   → Type: 'install {rec['id']}' to add this plugin")
            elif not rec["enabled"]:
                lines.append(f"   → Enable in Plugin Manager (Tools → Plugin Manager)")

            if rec.get("requires"):
                lines.append(f"   📚 Requires: {', '.join(rec['requires'])}")

            lines.append("")

        lines.append("💡 Tip: You can also ask 'recommend plugins for [workflow]'")
        return "\n".join(lines)

    def _resp_recommend_for_workflow(self, entity):
        """Recommend plugins for a specific workflow."""
        if not entity:
            return ("Which workflow? Examples:\n"
                   "  • 'recommend plugins for petrology'\n"
                   "  • 'what plugins for mapping?'\n"
                   "  • 'suggest tools for dating'\n"
                   "  • 'plugins for provenance studies'")

        suggestions = self.recommender.suggest_plugins_for_workflow(entity)

        if not suggestions:
            return (f"I don't have specific recommendations for '{entity}'.\n"
                   "Try: petrology, provenance, dating, mapping, publication, "
                   "quality control, multivariate, spectral, chromatography, "
                   "electrochemistry, materials, clinical, archaeology")

        lines = [
            f"🔌 Plugin Recommendations for {entity.upper()}:",
            ""
        ]

        for rec in suggestions:
            status = "📦" if not rec["installed"] else "✅" if rec["enabled"] else "⚠️"
            status_text = " (not installed)" if not rec["installed"] else " (disabled)" if not rec["enabled"] else ""

            lines.append(f"{status} {rec.get('name', rec['id'])}{status_text}")
            if rec.get('description'):
                lines.append(f"   {rec['description']}")

            if not rec["installed"]:
                lines.append(f"   → Type: 'install {rec['id']}' to add this plugin")

            lines.append("")

        return "\n".join(lines)

    def _resp_install_plugin(self, entity):
        """Install a plugin from the store."""
        if not entity:
            return ("Which plugin would you like to install?\n"
                   "Example: 'install compositional_stats_pro' or "
                   "'install lithic_morphometrics'\n\n"
                   "You can also ask: 'recommend plugins' to see suggestions.")

        # Clean up the entity - might be quoted or have extra words
        plugin_id = entity.strip().strip('"\'').lower().replace(" ", "_")

        # Check if it's already installed
        installed = self.recommender.get_installed_plugins()
        if plugin_id in installed:
            return f"ℹ️ Plugin '{plugin_id}' is already installed. Use 'enable {plugin_id}' if it's disabled."

        # Confirm installation
        if not messagebox.askyesno(
            "Confirm Installation",
            f"Install plugin '{plugin_id}' from the store?\n\n"
            "This will download and install the plugin.",
            parent=self.app.root):
            return "Installation cancelled."

        # Install
        result = self.recommender.install_plugin(
            plugin_id,
            callback=lambda: self._refresh_after_install(plugin_id)
        )

        return result

    def _resp_enable_plugin(self, entity):
        """Enable a plugin (if installed but disabled)."""
        if not entity:
            return "Which plugin would you like to enable? Example: 'enable compositional_stats_pro'"

        plugin_id = entity.strip().strip('"\'').lower().replace(" ", "_")

        # Check if installed
        installed = self.recommender.get_installed_plugins()
        if plugin_id not in installed:
            return f"❌ Plugin '{plugin_id}' is not installed. Try 'install {plugin_id}' first."

        # Check if already enabled
        enabled = self.recommender.get_enabled_plugins()
        if plugin_id in enabled:
            return f"✅ Plugin '{plugin_id}' is already enabled."

        # Enable
        enabled_file = Path("config/enabled_plugins.json")
        if enabled_file.exists():
            try:
                with open(enabled_file) as f:
                    enabled_dict = json.load(f)
            except:
                enabled_dict = {}
        else:
            enabled_dict = {}

        enabled_dict[plugin_id] = True

        temp = enabled_file.with_suffix(".tmp")
        with open(temp, "w") as f:
            json.dump(enabled_dict, f, indent=2)
        temp.replace(enabled_file)

        # Reload plugins in main app
        if hasattr(self.app, "_load_plugins"):
            self.app._load_plugins()

        return f"✅ Plugin '{plugin_id}' enabled successfully!"

    def _resp_list_store(self, entity=None):
        """List available plugins in the store."""
        if not self.recommender.fetch_store_index():
            return "❌ Cannot fetch plugin store. Check your internet connection."

        if not self.recommender.store_index:
            return "No plugins found in store."

        # Group by category
        by_category = defaultdict(list)
        for plugin in self.recommender.store_index:
            category = plugin.get("category", "add-ons")
            by_category[category].append(plugin)

        installed = self.recommender.get_installed_plugins()

        lines = ["📦 Plugin Store Available Plugins:\n"]

        for category in ["add-ons", "software", "hardware"]:
            plugins = by_category.get(category, [])
            if not plugins:
                continue

            lines.append(f"{category.upper()}:")
            for plugin in plugins[:8]:  # Limit per category
                pid = plugin["id"]
                status = "✅" if pid in installed else "📦"
                lines.append(f"  {status} {plugin.get('name', pid)} v{plugin.get('version', '?')}")

            if len(plugins) > 8:
                lines.append(f"  ... and {len(plugins) - 8} more")
            lines.append("")

        lines.append("To install: 'install [plugin_id]'")
        lines.append("To see recommendations: 'recommend plugins'")

        return "\n".join(lines)

    def _resp_plugin_status(self):
        """Show status of installed/enabled plugins."""
        installed = self.recommender.get_installed_plugins()
        enabled = self.recommender.get_enabled_plugins()

        if not installed:
            return "No plugins installed. Try 'recommend plugins' or 'list store'."

        lines = [
            f"🔌 Plugin Status:",
            f"  Installed: {len(installed)}",
            f"  Enabled:   {len(enabled)}",
            ""
        ]

        # Group by category
        by_category = defaultdict(list)
        for pid in installed:
            info = self.recommender.get_plugin_info(pid)
            if info:
                category = info.get("category", "unknown")
                by_category[category].append((pid, info, pid in enabled))

        for category in ["add-ons", "software", "hardware"]:
            plugins = by_category.get(category, [])
            if not plugins:
                continue

            lines.append(f"{category.upper()}:")
            for pid, info, is_enabled in sorted(plugins):
                status = "✅" if is_enabled else "⭕"
                name = info.get("name", pid)
                lines.append(f"  {status} {name}")
            lines.append("")

        lines.append("To enable a plugin: 'enable [plugin_id]'")
        lines.append("To get recommendations: 'recommend plugins'")

        return "\n".join(lines)

    def _refresh_after_install(self, plugin_id):
        """Refresh UI after plugin installation."""
        # Update knowledge base
        self.kb = KnowledgeBase(self.app)

        # Update status label
        if hasattr(self, '_status_lbl'):
            self._status_lbl.config(text=f"🧠 Toolkit AI v2.2  •  {self.kb.summary()}")

        # Refresh plugin manager if open
        for child in self.app.root.winfo_children():
            if isinstance(child, tk.Toplevel) and "Plugin Manager" in child.title():
                child.destroy()
                # Optionally reopen
                # self.app.open_plugin_manager()

        self._append(f"✅ Plugin installed! You can now use it. Type 'help' to see new commands.\n", "system")

    # ─────────────────────────────────────────────────────────────────────────
    # EXISTING RESPONSE GENERATORS
    # ─────────────────────────────────────────────────────────────────────────

    def _resp_help(self):
        """Updated help with plugin commands."""
        return (
            "Toolkit AI v2.2 — What I can do:\n\n"
            "🔬 DATA ANALYSIS\n"
            "  • 'Analyze my data' — full column statistics\n"
            "  • 'Check my data for problems' — validation\n"
            "  • 'What data do I have?' — quick summary\n\n"
            "🏷️ CLASSIFICATION\n"
            "  • 'List classification schemes' — see all available\n"
            "  • 'Run TAS' — run a specific scheme\n"
            "  • 'Run all schemes' — run everything at once\n"
            "  • 'What is MORB?' — explain a classification\n\n"
            "🔌 PLUGIN RECOMMENDATIONS (NEW!)\n"
            "  • 'Recommend plugins' — get suggestions for your data\n"
            "  • 'Plugins for petrology' — workflow-specific suggestions\n"
            "  • 'List store' — see all available plugins\n"
            "  • 'Install compositional_stats_pro' — install a plugin\n"
            "  • 'Enable pca_lda_explorer' — enable installed plugin\n"
            "  • 'What plugins do I have?' — check installed status\n\n"
            "🧩 PLUGINS & PANELS\n"
            "  • 'List plugins' — see all installed tools\n"
            "  • 'Open spectroscopy' — launch a plugin\n"
            "  • 'Switch to geochemistry panel' — change right panel\n\n"
            "📚 KNOWLEDGE\n"
            "  • 'What does SiO2 mean?' — element/oxide info\n"
            "  • 'How do I classify my data?' — workflow guidance\n"
            "  • 'What should I do next?' — intelligent next step\n\n"
            "📤 EXPORT\n"
            "  • 'Export learning data' — backup your AI's knowledge\n\n"
            "⚙️ Click the gear icon to configure learning settings."
        )

    def _resp_current_data(self):
        dc = self.ctx.get_data_context()
        if not dc["loaded"]:
            return "📊 No data loaded. Use File → Import CSV or the Import button in the left panel."

        dtype = self.ctx.detect_data_type()
        lines = [
            f"📊 Current Data Summary",
            f"  Samples:  {dc['count']}",
            f"  Columns:  {len(dc['columns'])}",
            f"  Type:     {dtype or 'unknown'}",
            f"  Columns:  {', '.join(dc['columns'][:8])}"
            + (" …and more" if len(dc['columns']) > 8 else ""),
        ]

        # Classification state
        cc = self.ctx.get_classification_context()
        if cc["has_results"]:
            lines.append(f"\n🏷️ Classification Results")
            lines.append(f"  Scheme:  {cc['scheme']}")
            lines.append(f"  Classified:  {cc['classified']} samples")
            lines.append(f"  Avg confidence:  {cc['avg_confidence']:.1%}")
            if cc["flagged"]:
                lines.append(f"  ⚠️ Flagged for review:  {cc['flagged']}")

        return "\n".join(lines)

    def _resp_analyze_data(self):
        dc = self.ctx.get_data_context()
        if not dc["loaded"]:
            return "📊 No data loaded. Import a file first."

        dtype = self.ctx.detect_data_type()
        stats = dc["stats"]
        lines = [
            f"📊 Data Analysis — {dc['count']} samples",
            f"   Detected type: {dtype or 'general'}",
            "",
            "Column Statistics (numeric):",
        ]

        numeric_cols = [(col, s) for col, s in stats.items()
                        if col != "Sample_ID"]
        if not numeric_cols:
            lines.append("  No numeric columns found.")
        else:
            for col, s in numeric_cols[:15]:
                missing_str = (f", {s['missing']} missing"
                               if s["missing"] else "")
                lines.append(
                    f"  {col:<20} mean={s['mean']:.3g}  "
                    f"min={s['min']:.3g}  max={s['max']:.3g}  "
                    f"n={s['n']}{missing_str}")

            if len(numeric_cols) > 15:
                lines.append(f"  … and {len(numeric_cols) - 15} more columns")

        # Suggest a scheme
        suggested = self._suggest_scheme_for_type(dtype)
        if suggested:
            lines.append(f"\n💡 Suggested scheme: {suggested['name']}")
            if suggested.get("fields_needed"):
                lines.append(
                    f"   Requires: {', '.join(suggested['fields_needed'][:6])}")

        return "\n".join(lines)

    def _resp_online_search(self, query):
        """Search online and return results in chat."""
        if not query:
            return "What would you like me to search for?"

        # Quick internet check
        import socket
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=2)
        except OSError:
            return "🌐 No internet connection. I'm in offline mode."

        try:
            import urllib.parse
            import urllib.request
            import json

            # Use DuckDuckGo API (no key needed)
            encoded = urllib.parse.quote(query)
            url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1"

            with urllib.request.urlopen(url, timeout=5) as resp:
                data = json.loads(resp.read().decode())

            # Extract answer
            if data.get('Abstract'):
                return f"🌐 **{query}**\n{data['Abstract'][:500]}..."
            elif data.get('Answer'):
                return f"🌐 **{query}**\n{data['Answer']}"
            elif data.get('RelatedTopics') and len(data['RelatedTopics']) > 0:
                topic = data['RelatedTopics'][0]
                text = topic.get('Text', '') if isinstance(topic, dict) else str(topic)
                return f"🌐 **Related to {query}**\n{text[:500]}..."
            else:
                return f"🌐 No direct answer found for '{query}'. Try a more specific search."

        except Exception as e:
            return f"🌐 Search failed: {e}"

    def _resp_validate_data(self):
        dc = self.ctx.get_data_context()
        if not dc["loaded"]:
            return "📊 No data loaded."

        samples = self.app.data_hub.get_all()
        issues  = []
        stats   = dc["stats"]

        # Check: missing values
        heavy_missing = [(col, s["missing"])
                         for col, s in stats.items()
                         if s["missing"] > dc["count"] * 0.2]
        if heavy_missing:
            for col, n in heavy_missing[:5]:
                issues.append(
                    f"⚠️  '{col}' has {n}/{dc['count']} missing values "
                    f"({n/dc['count']:.0%})")

        # Check: negative values in oxide columns (should be ≥ 0)
        oxide_cols = [col for col in stats
                      if any(ox in col.lower()
                             for ox in ["sio2","tio2","al2o3","fe2o3",
                                        "mgo","cao","na2o","k2o","p2o5"])]
        for col in oxide_cols:
            s = stats[col]
            if s["min"] < 0:
                issues.append(f"❌  '{col}' has negative values (min={s['min']})")

        # Check: oxide totals if geochemistry
        dtype = self.ctx.detect_data_type()
        if dtype == "geochemistry":
            major_oxides = ["SiO2","TiO2","Al2O3","Fe2O3","FeO","MgO",
                            "CaO","Na2O","K2O","P2O5","MnO"]
            present = [col for col in major_oxides if col in stats]
            if len(present) >= 5:
                # Spot-check first 5 samples
                bad_totals = 0
                for s in samples[:20]:
                    total = sum(
                        float(s.get(col, 0) or 0)
                        for col in present
                        if s.get(col) not in (None, "", "nan"))
                    if total > 0 and not (90 <= total <= 105):
                        bad_totals += 1
                if bad_totals > 0:
                    issues.append(
                        f"⚠️  {bad_totals}/20 samples have oxide totals "
                        f"outside 90–105% range")

        # Check: duplicate Sample_IDs
        if "Sample_ID" in dc["columns"]:
            ids = [s.get("Sample_ID", "") for s in samples]
            dupes = len(ids) - len(set(ids))
            if dupes > 0:
                issues.append(
                    f"⚠️  {dupes} duplicate Sample_ID value(s) found")

        if not issues:
            return (f"✅ Data looks clean.\n"
                    f"   {dc['count']} samples, {len(dc['columns'])} columns, "
                    f"no obvious issues detected.")
        return "Data Validation Results:\n\n" + "\n".join(issues)

    def _resp_statistics(self):
        with self._thread_lock:
            c = self.conn.cursor()
            c.execute("SELECT COUNT(*) FROM actions")
            total = c.fetchone()[0]
            c.execute(
                "SELECT name, usage_count FROM components "
                "ORDER BY usage_count DESC LIMIT 5")
            top = c.fetchall()
            c.execute(
                "SELECT data_type, panel_id, use_count FROM data_preferences "
                "ORDER BY use_count DESC LIMIT 5")
            prefs = c.fetchall()
            c.execute("SELECT COUNT(*) FROM conversations")
            conv_count = c.fetchone()[0]

        lines = [
            "📈 Learning Statistics",
            f"  Actions recorded:  {total}",
            f"  Conversations:     {conv_count}",
            f"  Knowledge base:    {self.kb.summary()}",
        ]
        if top:
            lines.append("\nMost-used components:")
            for name, count in top:
                lines.append(f"  • {name}: {count}×")
        if prefs:
            lines.append("\nLearned data preferences:")
            for dtype, panel, count in prefs:
                lines.append(f"  • {dtype} → {panel} ({count}×)")
        return "\n".join(lines)

    def _resp_list_schemes(self):
        schemes = self.ctx.get_available_schemes()
        if not schemes:
            # Fall back to knowledge base
            kb_schemes = list(self.kb.schemes.values())
            if not kb_schemes:
                return ("No classification schemes found. "
                        "Check that the classification engine is loaded.")
            lines = [f"📋 {len(kb_schemes)} schemes in knowledge base:\n"]
            for s in kb_schemes[:20]:
                lines.append(
                    f"  {s.get('icon','📊')} {s['name']}"
                    + (f" — {s['description'][:50]}"
                       if s.get("description") else ""))
            if len(kb_schemes) > 20:
                lines.append(f"  … and {len(kb_schemes)-20} more")
            return "\n".join(lines)

        lines = [f"📋 {len(schemes)} classification schemes available:\n"]
        for display, sid in schemes[:25]:
            lines.append(f"  {display}")
        if len(schemes) > 25:
            lines.append(f"  … and {len(schemes)-25} more")
        lines.append(
            '\nTo run one: type "run [scheme name]" or select from the '
            'right panel dropdown.')
        return "\n".join(lines)

    def _resp_list_plugins(self):
        all_plugins = self.kb.plugins
        enabled     = set(self.ctx.get_enabled_plugins())

        by_cat = defaultdict(list)
        for p in all_plugins.values():
            by_cat[p["category"]].append(p)

        lines = [f"🧩 {len(all_plugins)} plugins found:\n"]
        for cat in ["hardware", "software", "add-ons"]:
            ps = by_cat.get(cat, [])
            if not ps:
                continue
            lines.append(
                f"{cat.upper()} ({len(ps)}):")
            for p in sorted(ps, key=lambda x: x["name"]):
                status = "✅" if p["id"] in enabled else "○"
                lines.append(
                    f"  {status} {p['icon']} {p['name']}"
                    + (f" — {p['description'][:45]}"
                       if p.get("description") else ""))
        lines.append(
            "\n✅ = enabled   ○ = installed but not enabled\n"
            "Enable/disable in Tools → Plugin Manager.")
        return "\n".join(lines)

    def _resp_explain(self, entity):
        if not entity:
            return "What would you like me to explain? e.g. 'What is MORB?'"

        # 1. Check if it's a classification from current results
        cc = self.ctx.get_classification_context()
        if cc["has_results"] and entity.upper() in [
                k.upper() for k in cc["class_counts"]]:
            count = cc["class_counts"].get(entity.upper(),
                    cc["class_counts"].get(entity, 0))
            scheme_info = self.kb.find_scheme(cc["scheme"])
            lines = [
                f"🏷️ Classification: {entity.upper()}",
                f"   Found in {count} of {cc['classified']} samples.",
                f"   Scheme: {cc['scheme']}",
            ]
            if scheme_info and scheme_info.get("description"):
                lines.append(f"   Scheme description: {scheme_info['description']}")
            return "\n".join(lines)

        # 2. Check knowledge base schemes — is it a scheme name?
        scheme = self.kb.find_scheme(entity)
        if scheme:
            lines = [
                f"📊 Classification Scheme: {scheme['name']}",
                f"   ID: {scheme['id']}",
            ]
            if scheme.get("description"):
                lines.append(f"   {scheme['description']}")
            if scheme.get("fields_needed"):
                lines.append(
                    f"   Requires: {', '.join(scheme['fields_needed'][:8])}")
            if scheme.get("classifications"):
                cls_list = scheme["classifications"][:10]
                lines.append(
                    f"   Classifications: {', '.join(cls_list)}"
                    + (" …" if len(scheme["classifications"]) > 10 else ""))
            return "\n".join(lines)

        # 3. Check if it's an element/oxide
        el = self.kb.find_element(entity)
        if el:
            return self._format_element(entity, el)

        # 4. Check if it's a plugin name
        plugin = self.kb.find_plugin(entity)
        if plugin:
            lines = [
                f"{plugin['icon']} Plugin: {plugin['name']}",
                f"   Category: {plugin['category']}",
            ]
            if plugin.get("description"):
                lines.append(f"   {plugin['description']}")
            if plugin.get("field"):
                lines.append(f"   Scientific field: {plugin['field']}")
            return "\n".join(lines)

        # 5. Check field panel descriptions
        entity_lower = entity.lower()
        for fid, desc in _FIELD_DESCRIPTIONS.items():
            if entity_lower in fid or fid in entity_lower:
                return f"📐 Field Panel — {fid}:\n   {desc}"

        # 6. Known geochemical/petrology terms
        known_terms = {
            "morb":  "Mid-Ocean Ridge Basalt. Tholeiitic basalts erupted at "
                     "divergent plate boundaries. Characterised by depleted "
                     "incompatible element patterns, low K2O/TiO2, flat REE.",
            "oib":   "Ocean Island Basalt. Intraplate basalts from hot-spot "
                     "volcanism (e.g. Hawaii). Enriched incompatible elements, "
                     "high TiO2 and Nb/Y.",
            "iab":   "Island Arc Basalt. Subduction-zone magmatism. Enriched "
                     "in LILE (Ba, K, Sr), depleted in HFSE (Nb, Ta, Ti).",
            "cab":   "Continental Arc Basalt. Similar to IAB but with stronger "
                     "crustal contamination signature.",
            "boninite": "High-Mg andesite found in fore-arc settings. Very low "
                        "TiO2 (<0.5 wt%), high MgO (>8%), and high SiO2.",
            "komatiite":"Ultramafic volcanic rock. Very high MgO (>18 wt%), "
                        "low SiO2, spinifex texture. Common in Archaean.",
            "tas":   "Total Alkali-Silica diagram (Le Bas et al. 1986). "
                     "Classifies volcanic rocks by Na2O+K2O vs SiO2.",
            "afm":   "AFM diagram (Alkali-FeO*-MgO). Discriminates tholeiitic "
                     "from calc-alkaline differentiation trends.",
            "nisp":  "Number of Identified Specimens. Count of all identified "
                     "animal bone fragments in a zooarchaeological assemblage.",
            "mni":   "Minimum Number of Individuals. The minimum number of "
                     "animals represented by the skeletal elements recovered.",
        }
        el_lower = entity.lower().replace("'s", "").strip()
        for term, explanation in known_terms.items():
            if term in el_lower or el_lower in term:
                return f"📖 {entity.upper()}\n   {explanation}"

        return (f"I don't have specific information about '{entity}'.\n"
                "Try asking about a classification name (e.g. 'MORB'), "
                "a scheme (e.g. 'TAS'), an element (e.g. 'SiO2'), "
                "or a plugin name.")

    def _resp_explain_element(self, entity):
        if not entity:
            return "Which element or oxide? e.g. 'What is SiO2?'"
        el = self.kb.find_element(entity)
        if el:
            return self._format_element(entity, el)
        return self._resp_explain(entity)

    def _format_element(self, query, el):
        lines = [
            f"⚗️ {el.get('display_name', query)}",
        ]
        if el.get("description"):
            lines.append(f"   {el['description']}")
        if el.get("variations"):
            lines.append(
                f"   Also written as: {', '.join(el['variations'][:6])}")
        if el.get("group"):
            lines.append(f"   Group: {el['group']}")
        return "\n".join(lines)

    def _resp_run_scheme(self, entity):
        if not self._action_exec:
            return "Action executor not ready."
        if entity and entity.strip().lower() in ("all", "all schemes"):
            return self._resp_run_all()
        # Use progress version
        return self._action_exec.run_classification_with_progress(entity)

    def _resp_run_all(self):
        if not self._action_exec:
            return "Action executor not ready."
        return self._action_exec.run_all_schemes()

    def _resp_open_plugin(self, entity):
        if not entity:
            return ("Which plugin? e.g. 'Open spectroscopy'.\n"
                    "Type 'list plugins' to see what's available.")
        if not self._action_exec:
            return "Action executor not ready."
        plugin = self.kb.find_plugin(entity)
        if not plugin:
            return (f"I don't know a plugin called '{entity}'.\n"
                    "Type 'list plugins' to see what's installed.")
        return self._action_exec.open_plugin(plugin["id"], plugin["name"])

    def _resp_switch_panel(self, entity):
        if not entity:
            return ("Which panel? e.g. 'Switch to geochemistry panel'.\n"
                    "Available: " + ", ".join(_FIELD_DESCRIPTIONS.keys()))
        if not self._action_exec:
            return "Action executor not ready."
        # Find matching field id
        el = entity.lower().strip()
        matched = None
        for fid in _FIELD_DESCRIPTIONS:
            if el in fid or fid in el:
                matched = fid
                break
        if not matched:
            return (f"I don't know a field panel called '{entity}'.\n"
                    "Available: " + ", ".join(_FIELD_DESCRIPTIONS.keys()))
        return self._action_exec.switch_field_panel(matched)

    def _resp_suggest_next(self):
        dc = self.ctx.get_data_context()
        if not dc["loaded"]:
            return ("💡 Next step: Import your data.\n"
                    "Use File → Import CSV or the Import button in the left panel.")

        cc = self.ctx.get_classification_context()
        dtype = self.ctx.detect_data_type()
        suggested = self._suggest_scheme_for_type(dtype)

        steps = []
        if not cc["has_results"]:
            if suggested:
                steps.append(
                    f"1. Run the '{suggested['name']}' classification scheme "
                    f"(it matches your {dtype} data).")
            else:
                steps.append(
                    "1. Run a classification scheme from the right panel "
                    "to understand your data.")
            steps.append(
                "2. Or type 'run all schemes' to try every scheme at once.")
        else:
            steps.append(
                f"1. You've classified {cc['classified']} samples with "
                f"'{cc['scheme']}'. Avg confidence: {cc['avg_confidence']:.1%}.")
            if cc["flagged"]:
                steps.append(
                    f"2. ⚠️ {cc['flagged']} samples are flagged for review — "
                    "double-click them in the HUD.")
            steps.append(
                "3. Export results: File → Export CSV.")
            if dtype and dtype in _FIELD_DESCRIPTIONS:
                steps.append(
                    f"4. Switch to the {dtype} field panel for specialised "
                    "statistics (say 'switch to {dtype} panel').")

            # Add plugin recommendation step
            steps.append(
                f"5. Type 'recommend plugins' to find tools that can help with {dtype} analysis.")

        return "💡 Suggested next steps:\n\n" + "\n".join(steps)

    def _resp_workflow(self):
        return (
            "📋 Standard Scientific Toolkit Workflow:\n\n"
            "1. IMPORT  — File → Import CSV/Excel (or left panel)\n"
            "2. REVIEW  — Check the data table (center panel)\n"
            "3. VALIDATE — Ask me: 'check my data for problems'\n"
            "4. CLASSIFY — Right panel → select scheme → Apply\n"
            "   Or say: 'run TAS' / 'run all schemes'\n"
            "5. EXPLORE — Double-click a row for detailed results\n"
            "6. ANALYSE — Use Advanced menu plugins for deeper work\n"
            "   💡 Tip: Ask 'recommend plugins' for suggestions!\n"
            "7. EXPORT  — File → Export CSV\n\n"
            "💡 Tip: The right panel auto-detects your data type "
            "and suggests switching to a specialised field panel."
        )

    def _resp_status(self):
        panel  = self.ctx.get_active_panel()
        engine = getattr(self.app, "current_engine_name", "classification")
        dc     = self.ctx.get_data_context()
        cc     = self.ctx.get_classification_context()
        lines  = [
            "📡 Toolkit Status",
            f"  Engine:       {engine}",
            f"  Right panel:  {panel}",
            f"  Data:         {dc['count']} samples" if dc["loaded"]
                             else "  Data:         none loaded",
        ]
        if cc["has_results"]:
            lines.append(f"  Last scheme:  {cc['scheme']}")
            lines.append(f"  Results:      {cc['classified']} classified")
        enabled_count = len(self.ctx.get_enabled_plugins())
        lines.append(f"  Enabled plugins: {enabled_count}")
        return "\n".join(lines)

    def _resp_export_learning(self):
        """Handle export learning request."""
        try:
            filename = self.export_learning_data()
            return f"✅ Learning data exported to:\n{filename}"
        except Exception as e:
            return f"⚠️ Export failed: {e}"

    def _resp_fallback(self, prompt):
        # Check for element/oxide pattern directly
        match = re.search(r"([A-Za-z][a-z]?[0-9]?[A-Za-z0-9]*)\??$", prompt)
        if match:
            token = match.group(1)
            el = self.kb.find_element(token)
            if el:
                return self._format_element(token, el)

        return (
            f"I'm not sure how to answer: '{prompt[:60]}'\n\n"
            "Here are things I understand:\n"
            "  'analyze my data'  •  'validate data'  •  'list schemes'\n"
            "  'run [scheme]'  •  'what is [term]'  •  'open [plugin]'\n"
            "  'switch to [field] panel'  •  'what should I do next?'\n"
            "  'recommend plugins'  •  'install [plugin]'  •  'list store'\n"
            "  'export learning data'  •  'help'\n\n"
            "Type 'help' for the full guide."
        )

    # ─────────────────────────────────────────────────────────────────────────
    # INTERNAL HELPERS
    # ─────────────────────────────────────────────────────────────────────────

    def _suggest_scheme_for_type(self, dtype):
        """Return the best KB scheme for a detected data type."""
        if not dtype:
            return None
        type_hints = {
            "geochemistry":   ["tas", "winchester", "afm", "tectonic"],
            "spectroscopy":   ["spectral", "raman", "ftir"],
            "structural":     ["structural", "stereonet"],
            "solution":       ["water", "piper", "wqi"],
            "molecular":      ["qpcr", "clinical"],
            "zooarch":        ["zooarch", "faunal"],
        }
        hints = type_hints.get(dtype, [dtype])
        for hint in hints:
            for s in self.kb.schemes.values():
                if hint in s["id"].lower() or hint in s["name"].lower():
                    return s
        return None

    # ─────────────────────────────────────────────────────────────────────────
    # SETTINGS DIALOG
    # ─────────────────────────────────────────────────────────────────────────

    def show_settings(self):
        dlg = tk.Toplevel(self.app.root)
        dlg.title("🧠 Toolkit AI v2.2 — Settings")
        dlg.geometry("560x520")
        dlg.transient(self.app.root)
        dlg.grab_set()

        main = ttk.Frame(dlg, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="Toolkit AI v2.2 Configuration",
                  font=("Segoe UI", 12, "bold")).pack(pady=(0, 12))

        # Status
        sf = ttk.LabelFrame(main, text="Status", padding=10)
        sf.pack(fill=tk.X, pady=4)
        self.enable_var = tk.BooleanVar(value=self.enabled)
        ttk.Checkbutton(sf, text="Enable AI Assistant",
                        variable=self.enable_var,
                        command=self._toggle_enable).pack(anchor=tk.W)
        ttk.Label(sf, text=f"Knowledge: {self.kb.summary()}",
                  font=("Segoe UI", 8)).pack(anchor=tk.W, pady=(4, 0))
        if self.kb.errors:
            ttk.Label(sf, text=f"⚠️ {len(self.kb.errors)} scan issue(s)",
                      foreground="orange",
                      font=("Segoe UI", 8)).pack(anchor=tk.W)

        # Learning
        lf = ttk.LabelFrame(main, text="Learning", padding=10)
        lf.pack(fill=tk.X, pady=8)
        self.auto_learn_var = tk.BooleanVar(
            value=self.config.get("auto_learn", True))
        ttk.Checkbutton(lf, text="Auto-learn from actions",
                        variable=self.auto_learn_var,
                        command=self._update_config).pack(anchor=tk.W)
        self.suggestions_var = tk.BooleanVar(
            value=self.config.get("suggestions_enabled", True))
        ttk.Checkbutton(lf, text="Show suggestions",
                        variable=self.suggestions_var,
                        command=self._update_config).pack(anchor=tk.W)

        # Stats
        stf = ttk.LabelFrame(main, text="Statistics", padding=10)
        stf.pack(fill=tk.BOTH, expand=True, pady=4)

        with self._thread_lock:
            c = self.conn.cursor()
            c.execute("SELECT COUNT(*) FROM actions");      ac = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM components");   cc = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM conversations");cv = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM data_preferences"); pc = c.fetchone()[0]

        for text in [
            f"Actions recorded:   {ac}",
            f"Components tracked: {cc}",
            f"Conversations:      {cv}",
            f"Data preferences:   {pc}",
        ]:
            ttk.Label(stf, text=text,
                      font=("Segoe UI", 9)).pack(anchor=tk.W)

        # Buttons
        bf = ttk.Frame(main)
        bf.pack(fill=tk.X, pady=12)

        def clear_all():
            if messagebox.askyesno(
                    "Clear All AI Data",
                    "Delete all learning data and conversation history?\n"
                    "This cannot be undone.",
                    parent=dlg):
                with self._thread_lock:
                    cur = self.conn.cursor()
                    for tbl in ("actions", "components",
                                "data_preferences", "conversations"):
                        cur.execute(f"DELETE FROM {tbl}")
                    self.conn.commit()
                self._history.clear()
                messagebox.showinfo("Done", "All AI data cleared.", parent=dlg)
                dlg.destroy()
                self.show_settings()

        def export_now():
            try:
                filename = self.export_learning_data()
                messagebox.showinfo(
                    "Export Complete",
                    f"Data exported to:\n{filename}",
                    parent=dlg
                )
            except Exception as e:
                messagebox.showerror(
                    "Export Failed",
                    str(e),
                    parent=dlg
                )

        ttk.Button(bf, text="Export Data",
                   command=export_now, width=12).pack(side=tk.LEFT, padx=4)
        ttk.Button(bf, text="Clear Data",
                   command=clear_all, width=12).pack(side=tk.LEFT, padx=4)
        ttk.Button(bf, text="Close",
                   command=dlg.destroy, width=12).pack(side=tk.RIGHT, padx=4)

    def _update_config(self):
        self.config["auto_learn"]          = self.auto_learn_var.get()
        self.config["suggestions_enabled"] = self.suggestions_var.get()
        self._save_config()

    def _toggle_enable(self):
        self.enabled            = self.enable_var.get()
        self.config["enabled"]  = self.enabled
        self._save_config()

    # ─────────────────────────────────────────────────────────────────────────
    # STATUS
    # ─────────────────────────────────────────────────────────────────────────

    def get_status(self):
        if not self.enabled:
            return "🧠 Toolkit AI (disabled)"
        with self._thread_lock:
            c = self.conn.cursor()
            c.execute("SELECT COUNT(*) FROM actions")
            n = c.fetchone()[0]
        return f"🧠 Toolkit AI v2.2 ({self.kb.summary().split(',')[0]})"


# ─────────────────────────────────────────────────────────────────────────────
# PLUGIN REGISTRATION
# ─────────────────────────────────────────────────────────────────────────────

def register_plugin(main_app):
    return ToolkitAIPlugin(main_app)
