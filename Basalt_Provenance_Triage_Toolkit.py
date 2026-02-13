#!/usr/bin/env python3
"""
Basalt Provenance Triage Toolkit
Version 10.2 (REVOLUTIONARY UPDATE - Dynamic Classification + Hardware Integration!)

DOI:          https://doi.org/10.5281/zenodo.18499129
License:      CC BY-NC-SA 4.0  (non-commercial research & education use only)
Author:       Sefy Levy
Contact:      sefy76@gmail.com

This software is free for archaeological and geochemical research.
Commercial use requires written permission.

If used in publications, please cite:

Levy, S. (2026). Basalt Provenance Triage Toolkit (Version 10.2).
Zenodo. https://doi.org/10.5281/zenodo.18499129

NEW IN v10.2:
- 14 Dynamic Classification Schemes (JSON-based, user-extensible!)
- 4 Hardware Device Plugins (pXRF, Digital Caliper, GPS, File Monitor)
- 29+ Supported Hardware Models (Thermo, Bruker, Olympus, SciAps, etc.)
- Industry-standard citations (Hartung, Pearce, Nesbitt, Papike, etc.)
- Covers 11+ scientific disciplines!
"""

import csv
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional, Dict, Any, List, Tuple
import sys
import argparse
import os
import json
import time
import statistics
from datetime import datetime, timedelta
import base64
from io import BytesIO
import threading  # For async API requests
from urllib.parse import quote, urlencode
from xml.etree import ElementTree as ET
from html.parser import HTMLParser
import re  # Added for optimization
import copy  # Added for optimization
import webbrowser  # Added for optimization
from collections import Counter  # Added for optimization

# ────────────────────────────────────────────────
# Embedded Application Icon
# ────────────────────────────────────────────────
ICON_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAQAAAAEACAIAAADTED8xAAAI60lEQVR4nO3dv2odRxTH8VHI4xj8BHFhNwFBEKR1Y0iX50kXcKM2IAICN3GTJ8gbpRh5tN5/d3Z3zsyc+X0/hQm2dKUk5ze/s3fle+/evHsIgKofWn8DQEsEANIIAKQRAEgjAJBGACCNAEAaAYA0AgBpBADSCACkEQBIIwCQRgAgjQBAGgGANAIAaQQA0ggApBEASCMAkEYAII0AQBoBgDQCAGkEANIIAKQRAEgjAJBGACCNAEAaAYA0AgBpBADSCACkEQBIIwCQRgAgjQBAGgFo7Ndffmr9LUgjAC3F6ScDDd3xTvFNrA79X3//W/87EUcDNLB15FMF9dEAVS1H/Pmf/+4/vJ39JlVQDQ1Qz+r0p1/3PxJGaIAatkZ/hiqojwYwlzn9q79PFVijAQzlj/4MVVANDWDl9PSvfiRVYIQGMDGb1/zRn5lVAT1QHAEo7MrBv4p1yBQrUEnFp3/1EViHCqIByrAY/RmqwAINUECF6V99TKrgOhrgkjqjP0MVFEQDnNdk+le/ClVwGg1wUqknOq/gSdLrCMBhrQ7+VaxDF7ECHdPV9K9+ddahQ5o1gOn/J4tTsLfRn6EKzqEBsnQ+/YEqOItrgBv6H/0ZquAQGmCPu+kPVMFBNMA6j6M/QxXkoAFWDDD9gSrIQwPM9XCHqyzul+0gAK/GOPhXsQ5tYQV6MfD0B9ahbTTA4KM/QxXMqDeA1PQHqmBBtwHURn+GKohEG0B8+gNV8I1cAzD6M+JVoNUATP+SeBUINcB4d7jK0rxfJhEADv5MguvQ+CsQ059PcB0auQEY/dN0qmDYBmD6r9CpggEbwNfof/r48+fHL62/i03DV8FoDeBu+tOvfRq+CoZqAEdPdK4OvaMqGKYHBgmAx4M/hPD0/DX+w8P9+/gPjjIQhojBCAFwNP3Tgz9Nf5QyEDqOwXgZ8B0AR6Mf1g7+JaqgMscXweNN//RPuTKuw2UDOB39cGv6ExfrUBiiCvwFwOn0Z47+FOtQBZ4C4HT0w6npj6gCa2O+OnTzYFw5+JeoAjuOL4K7VXb6g58r4+bnzgluVqBpY3T7H7rI2rPFxTo07QEaQMv04C8+/bOH7bkKfPmx9TcwAtODf+bp+WusgvhFu60CL2iAq6wP/iWqoCACcEnx6918ZKAIVqCTaq49W1iHrqMBzqi/9mxhHbqIBjimh4N/iSo4jfsABzTc+DNZ3zNe3u4tqMl9A1agXP1Pf+DK+Dga4LY+154dDe8Zcyd4NP1c7+bjyjgfF8Gb3B38M1wZ56AB1nk8+JeogpsIwAoX17v5yMAOVqDveF97trAObSEAr6od/L//9mnrj/7487PRF43/UikGZCAiACHUOvh35n75MUZJoApmCECNg382+o9Pz1sf+fHhfvopFjGgCqYIwAuj6Z+O/s7cLz8mJsE0BtP7ZbJ4FshQmv7Hp+ec6Z+afkrO7oRzCICV6fSffhAyYI0AmIjzeuLgX0oPQgYsEIDy0vQXfEwyYIQAFGYx/REZsEAASqoznWSgIAJQnsXxb/3IsghAMXbLzxSLUFnNboRdeXXom38ztdsXD0VvaIAy6hz/ESVQULMGOPoXRnt4VQiMhwaANAJQQM39J2ILKoUAQBoBgDQCAGkEANIIAKTxVyJxwKFXhz56s59XhwZqowFwwM178Lw6tKL4qg3pFU0qiF/L7lW0dBAASCMAkEYAyqi5BbH/FEQAII0AFFOnBDj+yyIA5dlloOYTTSIIQEl1DmaO/4IIQGF2ixDLjwUCUJ5FBph+IwTARMrA9RikB2H6LRAAK2ler2QgfS7Tb4QAGJpm4GgMpp/C9Nvhp0FfPNy/t3iXpDi78eUb0kDnvEfY9NMt8P5I0d2bdw+tv4cspi+M1c+7RCZ1Rr/4O+S5+3FoGiCEb3MQY2BUBWEy003eJzhK0y/+5pAJAXj1+fFLykCwrIImO73pwe8XAfhOnSqoj4N/C88CrUhTMsaVItO/gwCsm2bAbwym3zzTv4oVaJP3dYjRz0ED3OCxCjj489EAt/mqAkb/EBogl4srY6b/KAJwQM/rEGvPOaxAx/S5DjH6p9EAZ/RTBRz8F/HDcJekn6JrUgX1R//Qq0MfxatD+9PwypiDvwgaoIA6P02d9Pxjbfw4tKKaV8Yc/GWxAhVjfWXM9a4FGqAkuypg9I24bID7D29Nn464qPiVsYvp7/x/yhY3F8Fh7U3XersanipyZdzz9e7UcvRdXAEHXwGInMbgRAa8HPyz3/Ey+pG/AAS3GQjZMeDgr8ZlACKnMbiZAQ7+mlxeBEfL/+I9X4RlXhkz/ZU5boDEURXsrEMu1p6RRj8aIQDBVQbC2jrEwd/KIAGIZjFwkYEpR9M/wOhHQwUguK0CR6MfBpr+4PoieJXHK2Omv6HRGiDxVQUdGn70o9EaIPFVBb0Rmf4wcAMkVMEhOqMfDdsACVWQT236g0IDJI6eJG1i1Cc69wkFILAObRA8+JPxV6Ap1qEl5ekPag2QUAVBfvQjrQZIqAKmPxJtgESwChj9KdEGSNSqgOmfUW+AZPgqYPRXqTdAMnYVMP1baIC58e6Xad7hykQAVgyzDnHw38QKtGKMdYjpz0ED7HFaBYx+Phpgj8cqYPoPoQGyuKgCRv8EGiBL/1XA9J9DAxzTYRUw+lfQAMf0VgVM/0U0wEk93C/jDtd1BOC8husQB38prEDntVqHmP6CaIACqlUBo18cDVBAnSpg+i3QACUZVQGjb4cGKMmiCph+UzSAiVJPkvJEpzUCYOXiOsTBXwcrkJUr6xDTXw0NYO5QFTD6ldEA5vKrgOmvjwaoZ6cKGP1WaIB6tqqA6W+IBmhgWQUJo18ZDdDA1pQz/fXRAC2lKmD0W6EBWopzz/Q3RANAGg0AaQQA0ggApBEASCMAkEYAII0AQBoBgDQCAGkEANIIAKQRAEgjAJBGACCNAEAaAYA0AgBpBADSCACkEQBIIwCQRgAgjQBAGgGANAIAaQQA0ggApBEASCMAkEYAII0AQBoBgDQCAGkEANIIAKQRAEgjAJBGACDtf0aWDPRBI8inAAAAAElFTkSuQmCC"

# ────────────────────────────────────────────────
# UNIFIED ELEMENT LOOKUP - FIX FOR ISSUE #1
# ────────────────────────────────────────────────

def get_element_value(row: Dict[str, Any], element_name: str) -> Optional[float]:
    """
    Unified element lookup that handles ALL column name variations.
    """
    if not row or not element_name:
        return None

    element_lower = element_name.lower()

    # Define ALL possible key variations to check
    key_variations = []

    # Special handling for wall thickness
    if "wall" in element_lower or "thickness" in element_lower:
        key_variations = [
            "Wall_Thickness_mm", "Wall_Thickness", "wall_thickness_mm",
            "wall_thickness", "Thickness_mm", "thickness_mm",
            "Thickness", "thickness", "Wall_mm", "wall_mm"
        ]
    else:
        # For trace elements
        base_name = element_lower.replace("_ppm", "").replace("ppm", "").strip()

        # Check in this priority order:
        key_variations = [
            f"{base_name}",           # 1. Raw element (e.g., "Zr")
            f"{base_name.upper()}",   # 2. Uppercase (e.g., "ZR")
            f"{base_name}_ppm",       # 3. With _ppm suffix
            f"{base_name.upper()}_PPM", # 4. Uppercase with _ppm
            f"pxrf_{base_name}_ppm",  # 5. pXRF variant
            f"pxrf_{base_name}",      # 6. pXRF without suffix
            f"{base_name}ppm",        # 7. No underscore
            f"{base_name} ppm"        # 8. With space
        ]

    # Try ALL variations
    for key in key_variations:
        value = row.get(key)
        if value is not None and value != "":
            result = safe_float(value)
            if result is not None:
                return result

    # Last resort: check any key containing the element name
    if element_lower not in ["wall", "thickness"]:
        for key, value in row.items():
            if key and element_lower in key.lower():
                result = safe_float(value)
                if result is not None:
                    return result

    return None


def get_ratio_value(row: Dict[str, Any], num_element: str, den_element: str) -> Optional[float]:
    """
    FIXED: Safe ratio calculation with comprehensive error handling.
    Returns None if either value is missing or denominator is zero.
    """
    num = get_element_value(row, num_element)
    den = get_element_value(row, den_element)

    if num is None:
        print(f"DEBUG: Missing numerator {num_element} for ratio calculation")
        return None
    if den is None:
        print(f"DEBUG: Missing denominator {den_element} for ratio calculation")
        return None
    if den == 0:
        print(f"DEBUG: Zero denominator {den_element} for ratio calculation")
        return None

    return num / den

# ────────────────────────────────────────────────
# FIXED CLASSIFICATION SYNC FUNCTION
# ────────────────────────────────────────────────
def get_consistent_classification(row: Dict[str, Any]) -> str:
    """
    FIX FOR ISSUE #5: Read classification consistently across the app.
    Single source of truth for reading classification from any row.
    """
    if not row:
        return "UNCLASSIFIED"

    # Check keys in priority order (same as HUD and plot)
    classification = (row.get('Final_Classification') or
                     row.get('Primary_Class') or
                     row.get('Auto_Classification') or
                     row.get('Classification') or
                     "UNCLASSIFIED")

    return str(classification).strip()


SCATTER_COLORS = {
    "EGYPTIAN (HADDADIN FLOW)": "blue",
    "EGYPTIAN (ALKALINE / EXOTIC)": "red",
    "SINAI / TRANSITIONAL": "goldenrod",
    "SINAI OPHIOLITIC": "orange",
    "LOCAL LEVANTINE": "green",

    "REVIEW REQUIRED": "gray",
    "UNCLASSIFIED": "darkgray",
    "INSUFFICIENT_DATA": "lightgray",

    "RESEARCH GRADE (RSD < 3%)": "green",
    "SCREENING GRADE (3-7%)": "goldenrod",
    "NON-QUANTIFIABLE (RSD > 7%)": "red",
    "NO ERROR DATA": "gray"
}
# ────────────────────────────────────────────────
# CLASSIFICATION SYNC FUNCTION - FIX FOR ISSUE #5
# ────────────────────────────────────────────────

def sync_classification_keys(row: Dict[str, Any], classification: str) -> None:
    """
    FIX FOR ISSUE #5: Write classification to ALL keys consistently.
    Ensures table, HUD, and plot all see the same result.
    """
    if not row or not classification:
        return

    clean_classification = str(classification).strip().upper()

    # Write to ALL classification keys
    all_class_keys = [
        "Final_Classification",    # Primary key for UI
        "Primary_Class",           # Engine result
        "Auto_Classification",     # Legacy auto-class
        "Classification",          # Generic fallback
    ]

    for key in all_class_keys:
        row[key] = clean_classification

    # Also sync color
    color = get_color_for_label(clean_classification)
    row["Display_Color"] = color
    row["Auto_Classification_Color"] = color
def get_color_for_label(label: str) -> str:
    """Returns the correct color regardless of text casing or extra spaces."""
    if not label: return "gray"
    # Normalize: Uppercase and strip whitespace
    clean_label = str(label).upper().strip()

    # Check map
    for key, color in SCATTER_COLORS.items():
        if key.upper().strip() == clean_label:
            return color
    return "gray"
# ────────────────────────────────────────────────
# Backend detection (GUI only)
# ────────────────────────────────────────────────
HAS_MATPLOTLIB = False
HAS_PILLOW     = False
HAS_PANDAS     = False
HAS_REQUESTS   = False
# ────────────────────────────────────────────────
# First-run dependency warning
# ────────────────────────────────────────────────
SHOW_DEPENDENCY_WARNING = True
SETTINGS_FILE = "basalt_settings.json"

plt = None
FigureCanvasTkAgg = None
Image = ImageDraw = ImageTk = None

# Check for pandas (needed for Excel import)
try:
    import pandas as pd
    HAS_PANDAS = True
    print("✓ Excel support: pandas available")
except ImportError:
    print("ℹ pandas not available (Excel import disabled)")
    pass

# Check for requests (needed for museum APIs)
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    print("ℹ requests not available (museum import disabled)")
    pass

# Check for plugin system
HAS_PLUGIN_SYSTEM = False
try:
    from pathlib import Path
    import importlib.util
    from plugins.plugin_manager import PluginManager
    HAS_PLUGIN_SYSTEM = True
    print("✓ Plugin system available")
except ImportError:
    print("ℹ Plugin system not available (plugins folder not found)")
    pass

# Check for classification engine (v10.2)
HAS_CLASSIFICATION_ENGINE = False
try:
    from classification_engine import ClassificationEngine
    HAS_CLASSIFICATION_ENGINE = True
    print("✓ Classification engine available (v10.2)")
except ImportError:
    print("ℹ Classification engine not available (using legacy classification)")
    pass

if len(sys.argv) == 1 or "gui" in sys.argv:  # load GUI libs only when needed
    # Try matplotlib first (best quality)
    try:
        import matplotlib
        matplotlib.use('TkAgg')
        import matplotlib.pyplot as _plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg as _FigureCanvasTkAgg

        test_fig = _plt.figure(figsize=(1, 1), dpi=72)
        _plt.close(test_fig)

        plt = _plt
        FigureCanvasTkAgg = _FigureCanvasTkAgg
        HAS_MATPLOTLIB = True
        print("✓ Plotting backend: matplotlib (best quality)")
    except Exception as e:
        print(f"ℹ matplotlib not available: {e}")
        pass

    # Try Pillow (always check, even if matplotlib works - user might prefer it)
    try:
        from PIL import Image as _Image, ImageDraw as _ImageDraw
        Image = _Image
        ImageDraw = _ImageDraw

        # Try ImageTk separately as it may not be available
        try:
            from PIL import ImageTk as _ImageTk
            ImageTk = _ImageTk
            HAS_PILLOW = True
            if not HAS_MATPLOTLIB:
                print("✓ Plotting backend: Pillow (good quality)")
            else:
                print("✓ Pillow available as alternative backend")
        except ImportError as e:
            # Pillow is installed but ImageTk isn't working
            print(f"ℹ Pillow found but ImageTk not available: {e}")
            ImageTk = None
            HAS_PILLOW = False
    except Exception as e:
        print(f"ℹ Pillow not available: {e}")
        pass

# ────────────────────────────────────────────────
# CONFIGURABLE PARAMETERS
# ────────────────────────────────────────────────
HADDADIN_ZRNB_MIN = 7.0
HADDADIN_ZRNB_MAX = 12.0
HADDADIN_BA_MIN   = 240.0
HADDADIN_BA_MAX   = 300.0
HADDADIN_CRNI_MIN = 1.1
HADDADIN_CRNI_MAX = 1.6

ALKALINE_ZRNB_THRESHOLD = 22.0
ALKALINE_BA_THRESHOLD   = 350.0

SINAI_ZRNB_MIN = 15.0
SINAI_ZRNB_MAX = 22.0

OPHIOLITIC_ZRNB_MIN = 20.0
OPHIOLITIC_CRNI_MIN = 1.8
OPHIOLITIC_CRNI_MAX = 2.3
OPHIOLITIC_BA_MAX   = 150.0
OPHIOLITIC_RB_MAX   = 30.0

LEVANTINE_CRNI_THRESHOLD = 2.5
THIN_WALL_THRESHOLD_MM   = 4.0
THICK_WALL_THRESHOLD_MM  = 4.5

ROWS_PER_PAGE = 50

# v9.1 Constants
THREAD_JOIN_TIMEOUT = 2.0  # seconds to wait for thread shutdown
AUTO_SAVE_INTERVAL = 300   # seconds (5 minutes)
MAX_UNDO_STACK = 50        # maximum undo history size

# ═══════════════════════════════════════════
# v9.0 ENHANCEMENTS - Themes and UI
# ═══════════════════════════════════════════

THEMES = {
    "Light": {
        "colors": {
            "EGYPTIAN (HADDADIN FLOW)": "#cce5ff",
            "EGYPTIAN (ALKALINE / EXOTIC)": "#f8d7da",
            "SINAI / TRANSITIONAL": "#fff3cd",
            "SINAI OPHIOLITIC": "#ffe5b4",
            "LOCAL LEVANTINE": "#d4edda",
            "REVIEW REQUIRED": "#e2e3e5",
        }
    },
    "Dark": {
        "colors": {
            "EGYPTIAN (HADDADIN FLOW)": "#1a3d5c",
            "EGYPTIAN (ALKALINE / EXOTIC)": "#5c1a1a",
            "SINAI / TRANSITIONAL": "#5c4d1a",
            "SINAI OPHIOLITIC": "#5c3d1a",
            "LOCAL LEVANTINE": "#1a5c2b",
            "REVIEW REQUIRED": "#3d3d3d",
        }
    }
}

STATUS_TIPS = [
    "💡 Tip: Double-click any row to edit",
    "💡 Tip: Use Ctrl+C to classify all",
    "💡 Tip: Right-click for quick actions",
    "💡 Tip: Ctrl+Shift+C copies to clipboard",
]

TOOLTIPS = {
    "import_csv": "Import samples from CSV",
    "export_csv": "Export to CSV (Ctrl+E)",
    "classify_all": "Auto-classify all (Ctrl+C)",
}


# ────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────
def safe_float(value: Any) -> Optional[float]:
    if not value:
        return None
    try:
        return float(str(value).strip())
    except (ValueError, TypeError):
        return None


# ────────────────────────────────────────────────
# OXIDE CONVERSION FUNCTIONS
# ────────────────────────────────────────────────

OXIDE_TO_ELEMENT = {
    "SiO2": {"Si": 0.4674},
    "TiO2": {"Ti": 0.5995},
    "Al2O3": {"Al": 0.5292},
    "Fe2O3": {"Fe": 0.6994},
    "FeO": {"Fe": 0.7773},
    "MnO": {"Mn": 0.7745},
    "MgO": {"Mg": 0.6030},
    "CaO": {"Ca": 0.7147},
    "Na2O": {"Na": 0.7419},
    "K2O": {"K": 0.8301},
    "P2O5": {"P": 0.4364},
    "Cr2O3": {"Cr": 0.6842},
    "NiO": {"Ni": 0.7858},
}

ELEMENT_TO_OXIDE = {
    "Si": {"SiO2": 2.1393},
    "Ti": {"TiO2": 1.6681},
    "Al": {"Al2O3": 1.8895},
    "Fe": {"Fe2O3": 1.4297, "FeO": 1.2865},
    "Mn": {"MnO": 1.2912},
    "Mg": {"MgO": 1.6582},
    "Ca": {"CaO": 1.3992},
    "Na": {"Na2O": 1.3480},
    "K": {"K2O": 1.2046},
    "P": {"P2O5": 2.2914},
    "Cr": {"Cr2O3": 1.4615},
    "Ni": {"NiO": 1.2725},
}

MAJOR_ELEMENTS = ["SiO2", "TiO2", "Al2O3", "Fe2O3", "MnO", "MgO", "CaO", "Na2O", "K2O", "P2O5"]

# ────────────────────────────────────────────────
# ALTERATION & WEATHERING WARNINGS
# ────────────────────────────────────────────────

def check_alteration_warnings(row: Dict[str, Any]) -> List[str]:
    """
    Check for indicators of chemical alteration or weathering.
    Returns list of warning messages.
    """
    warnings = []

    # Get values
    rb = safe_float(row.get("Rb_ppm"))
    ba = safe_float(row.get("Ba_ppm"))
    zr = safe_float(row.get("Zr_ppm"))
    nb = safe_float(row.get("Nb_ppm"))
    cr = safe_float(row.get("Cr_ppm"))
    ni = safe_float(row.get("Ni_ppm"))

    # Calculate ratios
    ba_rb = safe_ratio(ba, rb)
    zr_nb = safe_ratio(zr, nb)

    # Check for alteration indicators

    # 1. Extremely low Rb (mobile during weathering)
    if rb is not None and rb < 3:
        warnings.append("⚠️ Very low Rb (<3 ppm) - possible Rb loss during weathering")

    # 2. Very high Ba/Rb ratio (Rb loss)
    if ba_rb is not None and ba_rb > 100:
        warnings.append("⚠️ Very high Ba/Rb (>100) - check for Rb loss or Ba enrichment")

    # 3. Extremely low Zr/Nb (unusual for basalts)
    if zr_nb is not None and zr_nb < 3:
        warnings.append("⚠️ Very low Zr/Nb (<3) - unusual ratio, verify measurements")

    # 4. Extremely high Zr/Nb (potential alteration or mixing)
    if zr_nb is not None and zr_nb > 40:
        warnings.append("⚠️ Very high Zr/Nb (>40) - check for mixing or alteration")

    # 5. Very low Ba (mobile during alteration)
    if ba is not None and ba < 50:
        warnings.append("⚠️ Very low Ba (<50 ppm) - possible Ba loss during alteration")

    # 6. Extremely high Ba (secondary enrichment)
    if ba is not None and ba > 2000:
        warnings.append("⚠️ Very high Ba (>2000 ppm) - check for secondary enrichment")

    # 7. Very low Cr and Ni together (potential weathering)
    if cr is not None and ni is not None:
        if cr < 20 and ni < 10:
            warnings.append("⚠️ Very low Cr+Ni - check sample integrity")

    return warnings

# ────────────────────────────────────────────────
# Batch Processing for CSV Files
# ────────────────────────────────────────────────
def batch_process_csv(input_path: str, output_path: str, scheme_id: str = 'regional_triage'):
    """
    Universal batch processor - uses the dynamic classification engine.
    Optionally specify a scheme_id; defaults to 'regional_triage'.
    """
    # Late import to avoid circular dependency and keep optional
    from classification_engine import ClassificationEngine

    samples = []
    imported = 0
    skipped = 0

    try:
        engine = ClassificationEngine()          # ✅ Instantiate the engine
        with open(input_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                row = {k.strip(): v.strip() for k, v in r.items() if v.strip()}

                if not row.get("Sample_ID"):
                    skipped += 1
                    continue

                # Basic numeric validation (same as before)
                valid = True
                numeric_fields = ["Wall_Thickness_mm", "Zr_ppm", "Nb_ppm",
                                  "Ba_ppm", "Rb_ppm", "Cr_ppm", "Ni_ppm"]
                for field in numeric_fields:
                    if row.get(field) and safe_float(row[field]) is None:
                        valid = False
                        break

                if valid:
                    # --------------------------------------------------------
                    # 1. CLASSIFY using the engine (adds Zr_Nb_Ratio, Cr_Ni_Ratio)
                    # --------------------------------------------------------
                    classification, confidence, color = engine.classify_sample(row, scheme_id)

                    # --------------------------------------------------------
                    # 2. COMPUTE Ba/Rb ratio (engine does not compute it)
                    # --------------------------------------------------------
                    ba = safe_float(row.get("Ba_ppm"))
                    rb = safe_float(row.get("Rb_ppm"))
                    ba_rb = None
                    if ba is not None and rb is not None and rb != 0:
                        ba_rb = ba / rb

                    # --------------------------------------------------------
                    # 3. SAFELY retrieve Zr/Nb & Cr/Ni (already computed by engine)
                    # --------------------------------------------------------
                    zr_nb = row.get("Zr_Nb_Ratio")
                    cr_ni = row.get("Cr_Ni_Ratio")

                    # Format ratios for display (3 decimals)
                    row.update({
                        "Zr_Nb_Ratio": f"{zr_nb:.3f}" if isinstance(zr_nb, (int, float)) else "",
                        "Cr_Ni_Ratio": f"{cr_ni:.3f}" if isinstance(cr_ni, (int, float)) else "",
                        "Ba_Rb_Ratio": f"{ba_rb:.3f}" if ba_rb is not None else "",
                        "Auto_Classification": classification,
                        "Auto_Confidence": confidence,
                        "Flag_For_Review": "YES" if classification == "REVIEW REQUIRED" else "NO",
                    })

                    # --------------------------------------------------------
                    # 4. Sync with legacy classification fields (optional)
                    # --------------------------------------------------------
                    if not row.get("Final_Classification"):
                        row["Final_Classification"] = classification
                        row["Confidence_1_to_5"] = confidence

                    samples.append(row)
                    imported += 1
                else:
                    skipped += 1

        if not samples:
            print(f"No valid rows in {input_path}")
            return

        # Dynamic headers – use keys from first sample (preserves all columns)
        output_headers = list(samples[0].keys())
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=output_headers, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(samples)

        print(f"✓ {imported} rows processed, {skipped} skipped → {output_path}")

    except Exception as e:
        print(f"✗ Batch failed on {input_path}: {e}")

class BasaltTriageApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.active_scheme_id = None
        self.sample_id_to_index = {}
        self.filter_cache = None
        self.last_filter_state = ("", "All")
        self.selected_rows = set() # Ensure this is a set for O(1) speed
        # Load dependency warning preference
        global SHOW_DEPENDENCY_WARNING
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r') as f:
                    settings = json.load(f)
                    SHOW_DEPENDENCY_WARNING = settings.get("show_dependency_warning", True)
        except:
            pass

        self.root.title("Basalt Provenance Triage Toolkit")
        self.root.geometry("1450x850") # Slightly wider to accommodate the Split View

        # DATA STORAGE
        self.samples: List[Dict[str, Any]] = []
        self.filtered_samples: List[Dict[str, Any]] = []

        # v11.0 RESULT TRACKING (The "Right Side" Data)
        # This keeps classification results separate from your raw CSV data
        self.classification_results: Dict[str, Dict[str, Any]] = {}

        self.current_page = 0
        self.first_plot_shown = False

        # Undo history
        self.undo_stack: List[List[Dict[str, Any]]] = []
        self.max_undo = 10

        # Autosave and crash recovery
        self.current_theme = "Light"
        self.sound_enabled = True
        self.auto_save_enabled = True
        self.auto_save_interval = 5
        self.last_save_time = time.time()
        self.unsaved_changes = False
        self.current_project_path = None
        self.recovery_file = os.path.join(os.path.expanduser("~"), ".basalt_recovery.json")
        self.achievements = {"samples_classified": 0, "samples_added": 0, "projects_saved": 0}
        self.current_tip_index = 0
        self.tip_rotation_time = 10000

        # Recent files
        self.recent_files: List[str] = []
        self.max_recent = 5
        self._load_recent_files()

        self.plot_image_ref = None
        self._matplotlib_figure = None
        self._matplotlib_canvas = None
        self._pillow_image = None
        self.backend_status_label = None
        self.preferred_backend = tk.StringVar(value="Auto")

        # Track current classification scheme
        self.current_classification_scheme_id = 'regional_triage'
        self.current_classification_scheme_info = None

        # Search/filter
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *args: self._apply_filter())
        self.filter_class_var = tk.StringVar(value="All")

        # Check for crash recovery
        self._check_crash_recovery()

        # UI BUILDING (This will now build the PanedWindow)
        self._build_ui()

        # Progress bar
        self.progress_frame = ttk.Frame(self.root, relief="raised", borderwidth=1)
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            variable=self.progress_var,
            maximum=100,
            mode='determinate'
        )
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=2)
        self.progress_label = ttk.Label(self.progress_frame, text="")
        self.progress_label.pack(side=tk.RIGHT, padx=5)
        self.progress_frame.pack_forget()

        # Store menubar reference
        try:
            self.menubar = self.root.nametowidget(self.root.cget('menu'))
        except:
            self.menubar = None

        # Load plugins
        self._load_plugins()

        self._update_status("Ready")

    def _open_hardware_plugin(self, plugin_id):
        """Dynamically open a hardware plugin"""
        try:
            if not hasattr(self, 'hardware_plugins') or plugin_id not in self.hardware_plugins:
                messagebox.showerror("Error", f"Plugin {plugin_id} not found")
                return

            plugin_data = self.hardware_plugins[plugin_id]
            plugin_file = plugin_data['file']
            display_name = plugin_data['display_name']

            import importlib.util

            # Load the module
            spec = importlib.util.spec_from_file_location(plugin_id, plugin_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            plugin_instance = None

            # METHOD 1: Try register_plugin() function (YOUR PLUGINS HAVE THIS!)
            if hasattr(module, 'register_plugin'):
                try:
                    plugin_instance = module.register_plugin(self)
                except Exception as e:
                    print(f"register_plugin() failed: {e}")

            # METHOD 2: Try to find and instantiate plugin class
            if not plugin_instance:
                # Look for classes ending with "Plugin"
                for attr_name in dir(module):
                    if not attr_name.startswith('_') and attr_name.endswith('Plugin'):
                        try:
                            plugin_class = getattr(module, attr_name)
                            # Try to instantiate
                            try:
                                plugin_instance = plugin_class(self)
                                break
                            except TypeError:
                                try:
                                    plugin_instance = plugin_class()
                                    break
                                except:
                                    continue
                        except:
                            continue

            if not plugin_instance:
                messagebox.showerror("Error",
                    f"Could not create plugin instance for {display_name}\n"
                    f"Plugin should have register_plugin() function or Plugin class")
                return

            # Try to open the plugin - try common method names
            open_methods = ['show', 'show_interface', 'open', 'start', 'run', 'main']

            for method_name in open_methods:
                if hasattr(plugin_instance, method_name):
                    try:
                        getattr(plugin_instance, method_name)()
                        return
                    except Exception as e:
                        print(f"Method {method_name} failed: {e}")
                        continue

            # If we get here, try any method that sounds like it opens something
            for attr_name in dir(plugin_instance):
                if not attr_name.startswith('_'):
                    if any(keyword in attr_name.lower() for keyword in ['show', 'open', 'start', 'run']):
                        attr = getattr(plugin_instance, attr_name)
                        if callable(attr):
                            try:
                                attr()
                                return
                            except:
                                continue

            messagebox.showinfo("Plugin Loaded",
                f"Plugin {display_name} loaded but no open method found.\n"
                f"Check plugin code for show() or similar method.")

        except Exception as e:
            messagebox.showerror("Plugin Error",
                f"Failed to open {display_name}:\n{str(e)}")

    # Hardware Plugins Complete Then your other methods continue here (like _build_ui, etc.)

        # Start autosave timer
        self._schedule_autosave()

        # Handle clean exit
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def setup_dynamic_columns(self, column_names: List[str]):
        """
        Dynamically configure the treeview columns.
        Ensures the checkbox column is always the first column.
        """
        # Build new column list – checkbox must be first
        new_columns = ["☐"]
        # Add all other columns, avoiding duplicates
        for col in column_names:
            if col != "☐" and col not in new_columns:
                new_columns.append(col)

        # Update the treeview columns
        self.tree["columns"] = new_columns
        self.tree["displaycolumns"] = new_columns

        # Hide the default ghost column #0
        self.tree.column("#0", width=0, stretch=tk.NO)

        # Create headers for all columns
        for col in new_columns:
            if col == "☐":
                # Checkbox column: no heading, narrow width
                self.tree.heading(col, text="", anchor=tk.CENTER)
                self.tree.column(col, width=30, anchor=tk.CENTER, stretch=False)
            else:
                # Regular data column
                display_name = col.replace("_", " ")
                self.tree.heading(col, text=display_name, anchor=tk.CENTER)
                self.tree.column(col, width=110, anchor=tk.CENTER)

        # Store active headers for later use
        self.active_headers = new_columns[1:]  # exclude the checkbox column

    def _build_ui(self):
        # ─────────────────────────────────────────────────────────────────
        # 1. MENU BAR – exactly as you wrote it (preserved)
        # ─────────────────────────────────────────────────────────────────
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Import pXRF (Ctrl+I)", command=self.import_csv)
        file_menu.add_command(label="Export pXRF (Ctrl+S)", command=self.export_csv)
        file_menu.add_command(label="Export Pub Table", command=self.export_publication_table)
        file_menu.add_separator()
        file_menu.add_command(label="Save Project...", command=self.save_project)
        file_menu.add_command(label="Load Project...", command=self.load_project)
        file_menu.add_separator()

        # Recent files submenu
        self.recent_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Recent Files", menu=self.recent_menu)
        self._update_recent_menu()

        file_menu.add_separator()
        file_menu.add_command(label="Load Config", command=self.load_config)
        file_menu.add_command(label="Save Config", command=self.save_config)
        file_menu.add_separator()
        file_menu.add_command(label="Quit (Ctrl+Q)", command=self.root.quit)

        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo (Ctrl+Z)", command=self.undo_last)
        edit_menu.add_command(label="Duplicate Selected (Ctrl+D)", command=self.duplicate_selected)
        edit_menu.add_separator()
        edit_menu.add_command(label="Classify All (Ctrl+C)", command=lambda: self.classify_all_with_scheme('regional_triage'))
        edit_menu.add_command(label="Clear All", command=self.clear_all)

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Data Table", command=lambda: self.notebook.select(0))
        view_menu.add_command(label="Scatter Plots", command=self.show_plot_tab)
        view_menu.add_separator()
        view_menu.add_command(label="Statistics Summary (Ctrl+T)", command=self.show_statistics)
        view_menu.add_command(label="Threshold Visualization", command=self._show_threshold_table)

        # Analysis menu
        analysis_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Analysis", menu=analysis_menu)
        analysis_menu.add_command(label="📊 Unit Converter (ppm ↔ wt%)", command=self._open_unit_converter)
        analysis_menu.add_command(label="🔢 Normalize Major Elements to 100%", command=self._normalize_major_elements)
        analysis_menu.add_separator()
        analysis_menu.add_command(label="⚠️ Detection Limit (BDL) Handler", command=self._open_bdl_handler)
        analysis_menu.add_command(label="📈 Calculate Error Propagation", command=self._calculate_error_propagation)
        analysis_menu.add_separator()
        analysis_menu.add_command(label="🔍 Sample Validation Report", command=self._show_validation_report)
        analysis_menu.add_command(label="⚖️ Compare Two Samples", command=self._compare_samples)

        # Plots menu
        plots_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Plots", menu=plots_menu)
        plots_menu.add_command(label="⭐ TAS Diagram (Total Alkali-Silica)",
                            command=self._show_tas_diagram,
                            font=("Arial", 10, "bold"))
        plots_menu.add_command(label="🕷️ Spider Diagram (Normalized)", command=self._show_spider_diagram)
        plots_menu.add_separator()
        plots_menu.add_command(label="📊 Pearce Discrimination Diagrams", command=self._show_pearce_diagrams)
        plots_menu.add_command(label="📈 Harker Variation Diagrams", command=self._show_harker_diagrams)
        plots_menu.add_separator()
        plots_menu.add_command(label="☢️ Sr-Nd Isotope Plot", command=self._show_srnd_isotope_plot)
        plots_menu.add_command(label="☢️ Pb Isotope Plots", command=self._show_pb_isotope_plots)
        plots_menu.add_separator()
        plots_menu.add_command(label="🔵 Custom Binary Plot", command=self.show_plot_tab)
        plots_menu.add_separator()
        plots_menu.add_command(label="💾 Save All Plots", command=self.save_all_plots)

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Generate Demo Data (Ctrl+G)", command=self._call_demo_generator)
        tools_menu.add_separator()
        tools_menu.add_command(label="Load Reference Dataset", command=self._load_reference_dataset)
        tools_menu.add_separator()
        tools_menu.add_command(label="Export Classification Summary", command=self._export_classification_summary)
        tools_menu.add_command(label="Batch Process Directory", command=self._call_batch_processor)
        tools_menu.add_separator()
        tools_menu.add_command(label="Geological Context Guide", command=self._show_geological_context)
        tools_menu.add_separator()
        tools_menu.add_command(label="🔌 Plugin Manager", command=self._open_plugin_manager)

        # Classify All menu (dynamic)
        classify_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Classify All", menu=classify_menu)

        if HAS_CLASSIFICATION_ENGINE:
            try:
                engine = ClassificationEngine()
                schemes = engine.get_available_schemes()
                if not schemes:
                    classify_menu.add_command(label="No schemes found", state="disabled")
                else:
                    main_scheme = None
                    rest_schemes = []
                    for scheme in schemes:
                        if scheme['id'] == 'regional_triage':
                            main_scheme = scheme
                        else:
                            rest_schemes.append(scheme)
                    rest_schemes.sort(key=lambda s: s.get('name', '').lower())
                    if main_scheme:
                        icon = main_scheme.get('icon', '🪨')
                        name = main_scheme.get('name', 'Basalt Provenance')
                        msid = main_scheme['id']
                        classify_menu.add_command(
                            label=f"{icon} {name}",
                            command=lambda s=msid: self.classify_all_with_scheme(s)
                        )
                    if rest_schemes:
                        classify_menu.add_separator()
                    for scheme in rest_schemes:
                        icon = scheme.get('icon', '📊')
                        name = scheme.get('name', 'Unnamed')
                        current_sid = scheme['id']
                        classify_menu.add_command(
                            label=f"{icon} {name}",
                            command=lambda s=current_sid: self.classify_all_with_scheme(s)
                        )
            except Exception as e:
                classify_menu.add_command(label=f"Error loading: {str(e)}", state="disabled")
        else:
            classify_menu.add_command(label="Engine not available", state="disabled")

        # Advanced menu (software plugins)
        advanced_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Advanced", menu=advanced_menu)
        self.advanced_menu = advanced_menu

        # Hardware menu
        hardware_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Hardware", menu=hardware_menu)

        if HAS_PLUGIN_SYSTEM:
            try:
                from pathlib import Path
                import importlib.util
                import json
                enabled_plugins = {}
                config_file = Path("config/enabled_plugins.json")
                if config_file.exists():
                    with open(config_file) as f:
                        enabled_plugins = json.load(f)
                hardware_dir = Path("plugins/hardware")
                if not hardware_dir.exists():
                    hardware_menu.add_command(label="No hardware plugins folder", state="disabled")
                else:
                    plugin_files = list(hardware_dir.glob("*.py"))
                    hardware_plugins_found = False
                    self.hardware_plugins = {}
                    for plugin_file in sorted(plugin_files):
                        if plugin_file.stem in ["__init__", "plugin_manager"]:
                            continue
                        plugin_id = plugin_file.stem
                        if not enabled_plugins.get(plugin_id, False):
                            continue
                        try:
                            spec = importlib.util.spec_from_file_location(plugin_id, plugin_file)
                            module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(module)
                            if hasattr(module, 'PLUGIN_INFO'):
                                info = module.PLUGIN_INFO
                                category = info.get('category', '').lower()
                                if category != 'hardware':
                                    continue
                                display_name = info.get('name', plugin_id.replace('_', ' ').title())
                                icon = info.get('icon', '🔌')
                                self.hardware_plugins[plugin_id] = {
                                    'file': plugin_file,
                                    'info': info,
                                    'display_name': display_name,
                                    'icon': icon
                                }
                                hardware_menu.add_command(
                                    label=f"{icon} {display_name}",
                                    command=lambda pid=plugin_id: self._open_hardware_plugin(pid)
                                )
                                hardware_plugins_found = True
                            else:
                                display_name = plugin_id.replace('_', ' ').title()
                                self.hardware_plugins[plugin_id] = {
                                    'file': plugin_file,
                                    'info': None,
                                    'display_name': display_name,
                                    'icon': '🔌'
                                }
                                hardware_menu.add_command(
                                    label=f"🔌 {display_name}",
                                    command=lambda pid=plugin_id: self._open_hardware_plugin(pid)
                                )
                                hardware_plugins_found = True
                        except Exception:
                            continue
                    if not hardware_plugins_found:
                        hardware_menu.add_command(label="No enabled hardware plugins", state="disabled")
            except Exception:
                hardware_menu.add_command(label="Error loading plugins", state="disabled")
        else:
            hardware_menu.add_command(label="Plugin system not available", state="disabled")

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Classification Rules (F1)", command=self.show_help)
        help_menu.add_separator()
        help_menu.add_command(label="⚠️ Disclaimer", command=self.show_disclaimer)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_separator()
        help_menu.add_command(label="License & Usage", command=self.show_license_usage)
        help_menu.add_separator()
        help_menu.add_command(label="Support the Project 💙", command=self.show_support)

        # ─────────────────────────────────────────────────────────────────
        # 2. KEYBOARD SHORTCUTS (preserved)
        # ─────────────────────────────────────────────────────────────────
        self.root.bind("<Control-i>", lambda e: self.import_csv())
        self.root.bind("<Control-s>", lambda e: self.export_csv())
        self.root.bind("<Control-c>", lambda e: self.classify_all_with_scheme('regional_triage'))
        self.root.bind("<Control-d>", lambda e: self.duplicate_selected())
        self.root.bind("<Control-z>", lambda e: self.undo_last())
        self.root.bind("<Control-t>", lambda e: self.show_statistics())
        self.root.bind("<Control-r>", lambda e: self.refresh_plot())
        self.root.bind("<Control-q>", lambda e: self._on_closing())
        self.root.bind("<Control-g>", lambda e: self._call_demo_generator())
        self.root.bind("<Control-l>", lambda e: self._clear_filter())
        self.root.bind("<F1>", lambda e: self.show_help())
        self.root.bind("<F5>", lambda e: self._apply_filter())
        self.root.bind("<Prior>", lambda e: self._prev_page())
        self.root.bind("<Next>", lambda e: self._next_page())

        # ─────────────────────────────────────────────────────────────────
        # 3. TOOLBAR (preserved)
        # ─────────────────────────────────────────────────────────────────
        toolbar = ttk.Frame(self.root, relief="raised", borderwidth=1)
        toolbar.pack(side=tk.TOP, fill=tk.X, pady=6, padx=6)

        buttons = [
            ("Import pXRF", self.import_csv),
            ("Export pXRF", self.export_csv),
            ("Add Sample", self.add_sample_from_form),
            ("Statistics", self.show_statistics),
            ("Export Pub Table", self.export_publication_table),
            ("Clear All", self.clear_all),
        ]
        for text, cmd in buttons:
            ttk.Button(toolbar, text=text, command=cmd).pack(side=tk.LEFT, padx=4)

        # ─────────────────────────────────────────────────────────────────
        # 4. MAIN LAYOUT – Vertical: TOP (PanedWindow) + BOTTOM (Controls)
        # ─────────────────────────────────────────────────────────────────
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)

        # ----- 4.1 Top area: Horizontal PanedWindow (Left Table Area + Right HUD) -----
        self.main_pane = ttk.PanedWindow(main_container, orient=tk.HORIZONTAL)
        self.main_pane.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=2, pady=2)

        # ----- 4.2 Bottom area: Controls (Previous/Next, Selection) -----
        self.bottom_controls = ttk.Frame(main_container)
        self.bottom_controls.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))

        # Build the bottom controls (navigation + selection)
        self._build_bottom_controls()

        # ─────────────────────────────────────────────────────────────────
        # 5. LEFT SIDE – Notebook (tabs only) + Content Area
        # ─────────────────────────────────────────────────────────────────
        self.left_container = ttk.Frame(self.main_pane)
        self.main_pane.add(self.left_container, weight=4)   # expands horizontally

        # ----- 5.1 Notebook – acts ONLY as a tab bar (height=1 hides content) -----
        self.notebook = ttk.Notebook(self.left_container, height=1)
        self.notebook.pack(side=tk.TOP, fill=tk.X, expand=False)

        dummy1 = ttk.Frame(self.notebook)
        dummy2 = ttk.Frame(self.notebook)
        self.notebook.add(dummy1, text="Data Table")
        self.notebook.add(dummy2, text="Scatter Plot")

        # ----- 5.2 Content area – holds the actual table and plot frames -----
        self.content_area = ttk.Frame(self.left_container)
        self.content_area.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(2, 0))

        self.table_tab = ttk.Frame(self.content_area)
        self.plot_tab  = ttk.Frame(self.content_area)

        self._build_table_tab()   # no pagination controls inside
        self._build_plot_tab()

        self.table_tab.pack(fill=tk.BOTH, expand=True)
        self.plot_tab.pack_forget()

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        # ─────────────────────────────────────────────────────────────────
        # 6. RIGHT SIDE – Classification HUD (FIXED WIDTH)
        # ─────────────────────────────────────────────────────────────────
        self.right_hud = ttk.LabelFrame(self.main_pane, text=" 🎯 Classification HUD ", padding=5)
        self.main_pane.add(self.right_hud, weight=0)   # weight=0 → does NOT expand

        # Set a fixed width that exactly fits the columns + scrollbar
        self.right_hud.config(width=330)

        # ----- 6.1 HUD Treeview (no controls inside) -----
        hud_inner = ttk.Frame(self.right_hud)
        hud_inner.pack(fill=tk.BOTH, expand=True)

        # Grid layout: row0 = spacer, row1 = tree
        hud_inner.grid_rowconfigure(0, weight=0)
        hud_inner.grid_rowconfigure(1, weight=1)   # tree expands vertically
        hud_inner.grid_columnconfigure(0, weight=1)
        hud_inner.grid_columnconfigure(1, weight=0)

        # Spacer for vertical alignment (tweak this number to align headers)
        self.hud_spacer = tk.Frame(hud_inner, height=38)   # <-- ADJUST THIS NUMBER
        self.hud_spacer.grid(row=0, column=0, columnspan=2, sticky="ew")

        # HUD Treeview
        hud_cols = ("Sample", "Result", "QC")
        self.hud_tree = ttk.Treeview(
            hud_inner,
            columns=hud_cols,
            show='headings',
            height=26
        )
        self.hud_tree.heading("Sample", text="ID")
        self.hud_tree.heading("Result", text="Classification")
        self.hud_tree.heading("QC", text="Status")
        self.hud_tree.column("Sample", width=70, anchor="center")
        self.hud_tree.column("Result", width=130, anchor="w")
        self.hud_tree.column("QC", width=80, anchor="center")

        self.hud_vsb = ttk.Scrollbar(hud_inner, orient="vertical", command=self.hud_tree.yview)
        self.hud_tree.configure(yscrollcommand=self.hud_vsb.set)

        self.hud_tree.grid(row=1, column=0, sticky="nsew")
        self.hud_vsb.grid(row=1, column=1, sticky="ns")

        self._scroll_sync_active = False

        # ─────────────────────────────────────────────────────────────────
        # 7. POST‑SETUP TASKS
        # ─────────────────────────────────────────────────────────────────
        try:
            self.menubar = self.root.nametowidget(self.root.cget('menu'))
        except:
            self.menubar = None

        self._load_plugins()
        self._setup_scroll_sync()

        self._update_status("Ready")

    def _build_table_tab(self):
        """
        Build the table view and report view inside the table tab.
        Pagination/selection controls are in the bottom bar.
        """
        # ----- Main table view (shown by default) -----
        self.main_table_view = ttk.Frame(self.table_tab)
        self.main_table_view.pack(fill=tk.BOTH, expand=True)

        # Build form on the left
        form = ttk.LabelFrame(self.main_table_view, text="Quick Entry", padding=6)
        form.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 6))

        self.entry_vars = {}
        fields = ["Sample_ID", "Notes"]

        for i, field in enumerate(fields):
            ttk.Label(form, text=f"{field}:", font=("TkDefaultFont", 8)).grid(
                row=i, column=0, sticky="w", pady=1, padx=2)
            var = tk.StringVar()
            self.entry_vars[field] = var
            ttk.Entry(form, textvariable=var, width=18, font=("TkDefaultFont", 8)).grid(
                row=i, column=1, pady=1, padx=2, sticky="ew")

        ttk.Button(form, text="Add Row", command=self.add_sample_from_form)\
            .grid(row=len(fields), column=0, columnspan=2, pady=6, padx=2, sticky="ew")

        # Table frame on the right
        table_frame = ttk.Frame(self.main_table_view)
        table_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Search and Filter controls
        search_frame = ttk.Frame(table_frame)
        search_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 5))

        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(search_frame, textvariable=self.search_var, width=30).pack(side=tk.LEFT, padx=5)

        ttk.Label(search_frame, text="Filter:").pack(side=tk.LEFT, padx=(15, 5))

        self.filter_options = ["All", "UNCLASSIFIED", "REVIEW REQUIRED"]
        self.filter_menu = ttk.OptionMenu(search_frame, self.filter_class_var, "All", *self.filter_options,
                                    command=lambda x: self._apply_filter())
        self.filter_menu.pack(side=tk.LEFT, padx=5)

        ttk.Button(search_frame, text="Clear Filter", command=self._clear_filter).pack(side=tk.LEFT, padx=5)

        # Treeview – includes checkbox column
        initial_cols = ["☐", "Sample_ID", "Notes"]
        self.tree = ttk.Treeview(table_frame, columns=initial_cols, show="headings", height=26)

        # Configure color tags
        self._configure_table_tags()

        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.vsb = vsb
        self.hsb = hsb

        self.tree.grid(row=1, column=0, sticky="nsew")
        vsb.grid(row=1, column=1, sticky="ns")
        hsb.grid(row=2, column=0, sticky="ew")

        table_frame.rowconfigure(1, weight=1)
        table_frame.columnconfigure(0, weight=1)

        # Apply dynamic headers – preserves checkbox column
        self.setup_dynamic_columns(initial_cols)

        # Binds
        self.tree.bind("<Button-1>", self._on_table_click)
        self.tree.bind("<Double-1>", self._on_row_double_click)
        self.tree.bind("<Button-3>", self._show_context_menu)
        self.tree.bind("<Button-2>", self._show_context_menu)

        # ----- Report view (hidden by default) -----
        self.report_view = ttk.Frame(self.table_tab)
        # Do NOT pack it yet – it starts hidden

    def _build_bottom_controls(self):
        """
        Build the bottom control bar (Previous/Next, Select All, etc.)
        This appears below both the table and the HUD.
        """
        # Left side: navigation
        nav_frame = ttk.Frame(self.bottom_controls)
        nav_frame.pack(side=tk.LEFT, padx=5, pady=5)

        self.prev_btn = ttk.Button(nav_frame, text="Previous", command=self._prev_page, width=10)
        self.prev_btn.pack(side=tk.LEFT, padx=2)

        self.page_label = tk.Label(nav_frame, text="Page 1 of 1", font=("TkDefaultFont", 9))
        self.page_label.pack(side=tk.LEFT, padx=8)

        self.next_btn = ttk.Button(nav_frame, text="Next", command=self._next_page, width=10)
        self.next_btn.pack(side=tk.LEFT, padx=2)

        # Right side: selection controls
        sel_frame = ttk.Frame(self.bottom_controls)
        sel_frame.pack(side=tk.RIGHT, padx=5, pady=5)

        ttk.Button(sel_frame, text="Select All", command=self._select_all_rows, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(sel_frame, text="Deselect All", command=self._deselect_all_rows, width=12).pack(side=tk.LEFT, padx=2)
        ttk.Button(sel_frame, text="🗑️ Delete Selected", command=self._delete_selected_rows, width=14).pack(side=tk.LEFT, padx=2)

        self.selection_label = tk.Label(sel_frame, text="Selected: 0", font=("TkDefaultFont", 9, "bold"))
        self.selection_label.pack(side=tk.LEFT, padx=8)

    def _on_tab_changed(self, event):
        """Show/hide table and plot frames based on selected notebook tab."""
        tab_id = self.notebook.index(self.notebook.select())
        if tab_id == 0:   # Data Table tab
            self.plot_tab.pack_forget()
            self.table_tab.pack(fill=tk.BOTH, expand=True)
            self._update_plot_warning()
        else:             # Scatter Plot tab
            self.table_tab.pack_forget()
            self.plot_tab.pack(fill=tk.BOTH, expand=True)
            self._update_plot_warning()
            if not self.first_plot_shown and self.samples:
                self.refresh_plot()
                self.first_plot_shown = True

    def _update_hud_offset(self, event=None):
        """
        Dynamically adjust the top spacer height so that the first row of the HUD
        aligns exactly with the first row of the main table.
        """
        if not hasattr(self, 'tree') or not hasattr(self, 'hud_spacer'):
            return

        children = self.tree.get_children()
        if not children:
            return

        try:
            table_top_y = self.tree.winfo_rooty()
            hud_top_y = self.hud_tree.winfo_rooty()
            diff = table_top_y - hud_top_y - 20   # ← adjust the +0 up/down to fine‑tune

            if diff != self.hud_spacer.winfo_height():
                self.hud_spacer.config(height=max(20, diff))
                self.hud_spacer.update_idletasks()
        except Exception:
            pass

    def _update_plot_warning(self):
        """Update the plot backend warning with colored messages"""
        if HAS_MATPLOTLIB:
            msg = "Advanced Plotting Available"
            color = "green"
        elif HAS_PILLOW:
            msg = "Pillow plotting available (install matplotlib for advanced features)"
            color = "blue"
        else:
            msg = "No plotting library detected (install matplotlib or Pillow)"
            color = "red"

        # Update the main info label at the top with color
        if hasattr(self, 'plot_info_label'):
            self.plot_info_var.set(msg)
            self.plot_info_label.config(fg=color)

        # Update the status label in the corner
        if self.backend_status_label:
            corner_msg = "matplotlib" if HAS_MATPLOTLIB else ("Pillow" if HAS_PILLOW else "Basic Tk")
            self.backend_status_label.config(text=corner_msg, fg=color)

    def _setup_scroll_sync(self):
        """
        Synchronise scrolling between the main table and HUD.
        Uses scrollbar commands only – no fighting, no loops.
        """
        if hasattr(self, '_scroll_sync_configured') and self._scroll_sync_configured:
            return

        self._scroll_sync_configured = True
        self._is_syncing_scroll = False

        if not hasattr(self, 'vsb') or not hasattr(self, 'hud_vsb'):
            return

        # Store the original scrollbar set methods
        self._tree_scroll_set = self.vsb.set
        self._hud_scroll_set = self.hud_vsb.set

        def sync_tree_to_hud(*args):
            """Main table scrolled → update HUD to same fraction."""
            if self._is_syncing_scroll:
                return

            # Update the table's scrollbar position
            self._tree_scroll_set(*args)

            # Get the current view fraction from the table
            first, last = self.tree.yview()

            # Update HUD without triggering its own callback
            self._is_syncing_scroll = True
            self.hud_tree.yview_moveto(first)
            # Also update the HUD scrollbar thumb position
            self._hud_scroll_set(first, last)
            self._is_syncing_scroll = False

        def sync_hud_to_tree(*args):
            """HUD scrolled → update main table to same fraction."""
            if self._is_syncing_scroll:
                return

            self._hud_scroll_set(*args)

            first, last = self.hud_tree.yview()

            self._is_syncing_scroll = True
            self.tree.yview_moveto(first)
            self._tree_scroll_set(first, last)
            self._is_syncing_scroll = False

        # Set the yscrollcommand to our wrappers – this is the ONLY sync mechanism
        self.tree.configure(yscrollcommand=sync_tree_to_hud)
        self.hud_tree.configure(yscrollcommand=sync_hud_to_tree)

        # ----- Mouse wheel – let Tkinter handle normally, no custom bindings needed -----
        # Remove any existing custom mouse wheel bindings
        self.tree.unbind("<MouseWheel>")
        self.tree.unbind("<Button-4>")
        self.tree.unbind("<Button-5>")
        self.hud_tree.unbind("<MouseWheel>")
        self.hud_tree.unbind("<Button-4>")
        self.hud_tree.unbind("<Button-5>")

        def sync_hud_to_tree(*args):
            """HUD scrolled → update main table to same relative position."""
            if self._is_syncing_scroll:
                return

            self._hud_scroll_set(*args)

            hud_children = self.hud_tree.get_children()
            if not hud_children:
                return

            try:
                top_item = self.hud_tree.identify_row(0)
                if top_item and top_item in hud_children:
                    top_index = hud_children.index(top_item)
                    total_rows = len(hud_children)
                    fraction = top_index / total_rows if total_rows > 0 else 0.0

                    self._is_syncing_scroll = True
                    self.tree.yview_moveto(fraction)
                    tree_first, tree_last = self.tree.yview()
                    self._tree_scroll_set(tree_first, tree_last)
                    self._is_syncing_scroll = False
            except Exception:
                pass

        # Set the yscrollcommand to our wrappers
        self.tree.configure(yscrollcommand=sync_tree_to_hud)
        self.hud_tree.configure(yscrollcommand=sync_hud_to_tree)

        # Bind mouse wheel events for instant sync
        def on_tree_mousewheel(event):
            self.tree.yview_scroll(int(-1 * (event.delta / 120)), "units")
            sync_tree_to_hud(*self.tree.yview())
            return "break"

        def on_hud_mousewheel(event):
            self.hud_tree.yview_scroll(int(-1 * (event.delta / 120)), "units")
            sync_hud_to_tree(*self.hud_tree.yview())
            return "break"

        self.tree.bind("<MouseWheel>", on_tree_mousewheel)
        self.hud_tree.bind("<MouseWheel>", on_hud_mousewheel)

        # Linux button events
        self.tree.bind("<Button-4>", lambda e: on_tree_mousewheel(e))
        self.tree.bind("<Button-5>", lambda e: on_tree_mousewheel(e))
        self.hud_tree.bind("<Button-4>", lambda e: on_hud_mousewheel(e))
        self.hud_tree.bind("<Button-5>", lambda e: on_hud_mousewheel(e))

    def _show_report_view(self):
        """Switch from table view to report view."""
        self.main_table_view.pack_forget()
        self.report_view.pack(fill=tk.BOTH, expand=True)

    def _hide_report_view(self):
        """Switch from report view back to table view."""
        self.report_view.pack_forget()
        self.main_table_view.pack(fill=tk.BOTH, expand=True)

    def _prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self._refresh_table_page()

    def _next_page(self):
        max_page = (len(self.samples) - 1) // ROWS_PER_PAGE
        if self.current_page < max_page:
            self.current_page += 1
            self._refresh_table_page()


    def _build_plot_tab(self):
        # ... (keep the top bar code you have)
        top = ttk.Frame(self.plot_tab)
        top.pack(side=tk.TOP, fill=tk.X, pady=4, padx=4)

        # (keep your labels and buttons)
        # ...

        # THE FIX: Use tk.Frame instead of ttk.Frame for the plot area
        # This prevents the "white void" on Linux
        self.plot_area = tk.Frame(self.plot_tab, bg="white", relief="sunken", borderwidth=1)
        self.plot_area.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # Move the status label to the 'top' frame instead of 'place' inside the plot
        self.backend_status_label = tk.Label(top, text="", fg="blue", font=("TkDefaultFont", 8, "italic"))
        self.backend_status_label.pack(side=tk.RIGHT, padx=10)

        # Info label
        self.plot_info_var = tk.StringVar(value="Click 'Generate Plot' to create visualization")
        self.plot_info_label = tk.Label(top, textvariable=self.plot_info_var, font=("TkDefaultFont", 10, "bold"))
        self.plot_info_label.pack(side=tk.LEFT, padx=4)

        # Backend selector
        backend_frame = ttk.Frame(top)
        backend_frame.pack(side=tk.LEFT, padx=20)
        ttk.Label(backend_frame, text="Plotting Engine:").pack(side=tk.LEFT, padx=(0, 5))

        backend_options = ["Auto"]
        if HAS_MATPLOTLIB: backend_options.append("Matplotlib")
        if HAS_PILLOW: backend_options.append("Pillow")
        backend_options.append("Basic Tk")

        self.backend_dropdown = ttk.OptionMenu(backend_frame, self.preferred_backend, "Auto", *backend_options, command=self._on_backend_changed)
        self.backend_dropdown.pack(side=tk.LEFT)

        # Buttons
        button_frame = ttk.Frame(top)
        button_frame.pack(side=tk.RIGHT)
        ttk.Button(button_frame, text="Generate Plot", command=self.refresh_plot).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Save Plot", command=self.save_plot).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Clear Plot", command=self.clear_plot).pack(side=tk.LEFT, padx=2)

        # --- THE FIX STARTS HERE ---
        # Create a container frame that holds BOTH the plot and the status bar
        container = ttk.Frame(self.plot_tab)
        container.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # 1. The actual Plot Area (Now purely for the plot)
        self.plot_area = tk.Frame(container, bg="white", relief="sunken", borderwidth=1)
        self.plot_area.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # 2. Separate Status Bar (So it doesn't overlap the Matplotlib canvas)
        status_bar = tk.Frame(container)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.backend_status_label = tk.Label(status_bar, text="", fg="gray", font=("TkDefaultFont", 8, "italic"))
        self.backend_status_label.pack(side=tk.RIGHT)

    # ────────────────────────────────────────────────
    # Table actions
    # ────────────────────────────────────────────────
    def _get_row_values(self, row: Dict[str, Any]) -> Tuple:
        """FIXED: Optimized O(1) lookup that ensures classification results appear in the table."""
        # 1. Checkbox state (Simple check, no expensive index lookup)
        sample_id = row.get("Sample_ID", "N/A")
        checkbox = "☑" if sample_id in self.selected_rows else "☐"

        # 2. Get active columns from the widget
        current_columns = self.tree["columns"]

        row_data = []
        for col in current_columns:
            if col == "☐":
                row_data.append(checkbox)
            elif col in ["Zr_Nb_Ratio", "Cr_Ni_Ratio", "Ba_Rb_Ratio"]:
                # Format numeric ratios to 3 decimal places for display
                val = row.get(col)
                row_data.append(f"{val:.3f}" if isinstance(val, (int, float)) else str(val or ""))
            else:
                # Get anything else (Classification, Sample_ID, etc.)
                row_data.append(str(row.get(col, "")))

        return tuple(row_data)

    def _insert_row(self, row: Dict[str, Any]):
        tag = row.get("Final_Classification") or row.get("Auto_Classification") or "REVIEW REQUIRED"
        sample_id = row.get("Sample_ID", "")
        self.tree.insert("", "end", iid=sample_id, values=self._get_row_values(row), tags=(tag,))


    def add_sample_from_form(self):
        row = {field: var.get().strip() for field, var in self.entry_vars.items()}
        if not row.get("Sample_ID"):
            messagebox.showerror("Error", "Sample_ID is required.")
            return
        numeric_fields = ["Wall_Thickness_mm", "Zr_ppm", "Nb_ppm", "Ba_ppm", "Rb_ppm", "Cr_ppm", "Ni_ppm"]
        for field in numeric_fields:
            if row[field] and safe_float(row[field]) is None:
                messagebox.showerror("Error", f"{field} must be numeric.")
                return
        self._save_undo()
        self.samples.append(row)
        self._apply_filter()  # Use filter instead of refresh
        # FIX FOR ISSUE #2: Sync HUD when adding new sample
        if hasattr(self, 'hud_tree'):
            self._update_hud_results(None)

        self._clear_form()
        self._mark_unsaved_changes()
        self._update_status(f"Added {row['Sample_ID']}")

    def _clear_form(self):
        for var in self.entry_vars.values():
            var.set("")

    def refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        self._refresh_table_page()

    # ============================================================
    # SMART IMPORT SYSTEM - FIXED!
    # ============================================================

    def _smart_column_mapper(self, columns):
        """
        Intelligently map various column name formats to standard names.
        Maps to the exact column names the table expects.
        Now handles: trace elements, major elements, isotopes, errors, BDL flags, QA/QC
        """
        column_map = {}

        # Define comprehensive mapping - MUST match DISPLAY_COLUMNS format!
        # Order matters: more specific patterns first
        targets = {
            # Core identification
            'Sample_ID': ['sample_name', 'sample_id', 'sampleid', 'lab_no', 'field_no', 'field_number', '^sample$', '^no$', '^id$'],
            'Museum_Code': ['museum_code', 'museum_no', 'accession', 'accession_no', 'museum_id'],
            'Photo_Path': ['photo_path', 'photo', 'image_path', 'photo_url'],
            'Lithology': ['lithology', 'rock_type', 'rock', 'composition'],
            
            # Core trace elements (ppm)
            'Cr_ppm': ['pxrf_cr_ppm', 'cr_ppm', 'crppm', '^cr$', 'chromium'],
            'Ni_ppm': ['pxrf_ni_ppm', 'ni_ppm', 'nippm', '^ni$', 'nickel'],
            'Zr_ppm': ['pxrf_zr_ppm', 'zr_ppm', 'zrppm', '^zr$', 'zirconium'],
            'Nb_ppm': ['pxrf_nb_ppm', 'nb_ppm', 'nbppm', '^nb$', 'niobium'],
            'Ba_ppm': ['pxrf_ba_ppm', 'ba_ppm', 'bappm', '^ba$', 'barium'],
            'Rb_ppm': ['pxrf_rb_ppm', 'rb_ppm', 'rbppm', '^rb$', 'rubidium'],
            'Sr_ppm': ['pxrf_sr_ppm', 'sr_ppm', 'srppm', '^sr$', 'strontium'],
            'Y_ppm': ['pxrf_y_ppm', 'y_ppm', 'yppm', '^y$', 'yttrium'],
            'Zn_ppm': ['pxrf_zn_ppm', 'zn_ppm', 'znppm', '^zn$', 'zinc'],
            'Cu_ppm': ['pxrf_cu_ppm', 'cu_ppm', 'cuppm', '^cu$', 'copper'],
            
            # Additional trace elements
            'V_ppm': ['v_ppm', 'vppm', '^v$', 'vanadium'],
            'Sc_ppm': ['sc_ppm', 'scppm', '^sc$', 'scandium'],
            'Co_ppm': ['co_ppm', 'coppm', '^co$', 'cobalt'],
            'Ga_ppm': ['ga_ppm', 'gappm', '^ga$', 'gallium'],
            'Th_ppm': ['th_ppm', 'thppm', '^th$', 'thorium'],
            'U_ppm': ['u_ppm', 'uppm', '^u$', 'uranium'],
            'Pb_ppm': ['pb_ppm', 'pbppm', '^pb$', 'lead'],
            
            # REE elements
            'La_ppm': ['la_ppm', 'lappm', '^la$', 'lanthanum'],
            'Ce_ppm': ['ce_ppm', 'ceppm', '^ce$', 'cerium'],
            'Nd_ppm': ['nd_ppm', 'ndppm', '^nd$', 'neodymium'],
            'Sm_ppm': ['sm_ppm', 'smppm', '^sm$', 'samarium'],
            'Eu_ppm': ['eu_ppm', 'euppm', '^eu$', 'europium'],
            'Gd_ppm': ['gd_ppm', 'gdppm', '^gd$', 'gadolinium'],
            'Dy_ppm': ['dy_ppm', 'dyppm', '^dy$', 'dysprosium'],
            'Er_ppm': ['er_ppm', 'erppm', '^er$', 'erbium'],
            'Yb_ppm': ['yb_ppm', 'ybppm', '^yb$', 'ytterbium'],
            'Lu_ppm': ['lu_ppm', 'luppm', '^lu$', 'lutetium'],
            
            # Major elements (wt%)
            'SiO2': ['sio2', 'sio2_wt%', 'sio2wt%', 'silica', 'si_o2', 'si02', 'sio₂'],
            'TiO2': ['tio2', 'tio2_wt%', 'tio2wt%', 'titania', 'ti_o2'],
            'Al2O3': ['al2o3', 'al2o3_wt%', 'al2o3wt%', 'alumina', 'al_2o3'],
            'Fe2O3': ['fe2o3', 'fe2o3_wt%', 'fe2o3wt%', 'feo_t', 'feot', 'iron', 'fe_2o3'],
            'FeO': ['feo', 'feo_wt%', 'feowt%', 'fe_o'],
            'MnO': ['mno', 'mno_wt%', 'mnowt%', 'manganese', 'mn_o'],
            'MgO': ['mgo', 'mgo_wt%', 'mgowt%', 'magnesia', 'mg_o'],
            'CaO': ['cao', 'cao_wt%', 'caowt%', 'lime', 'ca_o'],
            'Na2O': ['na2o', 'na2o_wt%', 'na2owt%', 'soda', 'na_2o'],
            'K2O': ['k2o', 'k2o_wt%', 'k2owt%', 'potash', 'k_2o'],
            'P2O5': ['p2o5', 'p2o5_wt%', 'p2o5wt%', 'phosphate', 'p_2o5'],
            'LOI': ['loi', 'loss_on_ignition', 'volatile'],
            'Total': ['total', 'sum', 'total_wt%'],
            
            # Isotopes
            '87Sr_86Sr': ['87sr_86sr', '87sr/86sr', 'sr_isotope', 'sr87_86'],
            '143Nd_144Nd': ['143nd_144nd', '143nd/144nd', 'nd_isotope', 'nd143_144'],
            '206Pb_204Pb': ['206pb_204pb', '206pb/204pb', 'pb206_204'],
            '207Pb_204Pb': ['207pb_204pb', '207pb/204pb', 'pb207_204'],
            '208Pb_204Pb': ['208pb_204pb', '208pb/204pb', 'pb208_204'],
            'δ18O': ['d18o', 'delta18o', 'oxygen_isotope', 'o18'],
            
            # Error columns (trace elements)
            'Zr_ppm_error': ['zr_ppm_error', 'zr_error', 'zr_std', 'zr_uncertainty'],
            'Nb_ppm_error': ['nb_ppm_error', 'nb_error', 'nb_std', 'nb_uncertainty'],
            'Ba_ppm_error': ['ba_ppm_error', 'ba_error', 'ba_std', 'ba_uncertainty'],
            'Rb_ppm_error': ['rb_ppm_error', 'rb_error', 'rb_std', 'rb_uncertainty'],
            'Cr_ppm_error': ['cr_ppm_error', 'cr_error', 'cr_std', 'cr_uncertainty'],
            'Ni_ppm_error': ['ni_ppm_error', 'ni_error', 'ni_std', 'ni_uncertainty'],
            'Sr_ppm_error': ['sr_ppm_error', 'sr_error', 'sr_std', 'sr_uncertainty'],
            'Y_ppm_error': ['y_ppm_error', 'y_error', 'y_std', 'y_uncertainty'],
            
            # Error columns (major elements)
            'SiO2_error': ['sio2_error', 'sio2_std', 'sio2_uncertainty'],
            'TiO2_error': ['tio2_error', 'tio2_std', 'tio2_uncertainty'],
            'Al2O3_error': ['al2o3_error', 'al2o3_std', 'al2o3_uncertainty'],
            'Fe2O3_error': ['fe2o3_error', 'fe2o3_std', 'fe2o3_uncertainty'],
            'MgO_error': ['mgo_error', 'mgo_std', 'mgo_uncertainty'],
            'CaO_error': ['cao_error', 'cao_std', 'cao_uncertainty'],
            'Na2O_error': ['na2o_error', 'na2o_std', 'na2o_uncertainty'],
            'K2O_error': ['k2o_error', 'k2o_std', 'k2o_uncertainty'],
            'P2O5_error': ['p2o5_error', 'p2o5_std', 'p2o5_uncertainty'],
            
            # Error columns (isotopes)
            '87Sr_86Sr_error': ['87sr_86sr_error', '87sr_86sr_2se', 'sr_isotope_error'],
            '143Nd_144Nd_error': ['143nd_144nd_error', '143nd_144nd_2se', 'nd_isotope_error'],
            '206Pb_204Pb_error': ['206pb_204pb_error', '206pb_204pb_2se'],
            '207Pb_204Pb_error': ['207pb_204pb_error', '207pb_204pb_2se'],
            '208Pb_204Pb_error': ['208pb_204pb_error', '208pb_204pb_2se'],
            'δ18O_error': ['d18o_error', 'delta18o_error', 'o18_error'],
            
            # BDL flags
            'Zr_BDL': ['zr_bdl', 'zr_below_detection'],
            'Nb_BDL': ['nb_bdl', 'nb_below_detection'],
            'Ba_BDL': ['ba_bdl', 'ba_below_detection'],
            'Rb_BDL': ['rb_bdl', 'rb_below_detection'],
            'Cr_BDL': ['cr_bdl', 'cr_below_detection'],
            'Ni_BDL': ['ni_bdl', 'ni_below_detection'],
            
            # QA/QC metadata
            'QC_Sample_Type': ['qc_sample_type', 'sample_type', 'qc_type', 'standard'],
            'Instrument_Model': ['instrument_model', 'instrument', 'analyzer', 'device'],
            'Measurement_Time_sec': ['measurement_time', 'count_time', 'integration_time'],
            'Data_Quality_Flag': ['data_quality', 'quality_flag', 'qc_flag'],
            
            # Archaeological context
            'Wall_Thickness_mm': ['wall_thickness', 'thickness', 'wall', 'wall_mm'],
            'Vessel_Form': ['vessel_form', 'form', 'type', 'vessel_type'],
            'Archaeological_Period': ['period', 'archaeological_period', 'chronology', 'date'],
            'Findspot': ['findspot', 'provenance', 'location', 'find_location'],
            'Excavation_ID': ['excavation_id', 'excavation', 'site_code', 'context'],
            
            # Geographic data (expanded for better compatibility)
            'Latitude': ['latitude', 'lat', 'y_coord', 'lat_dd', 'lat_decimal', 
                        'latitude_dd', 'latitude_decimal', 'gps_lat', 'gps_latitude',
                        'coord_n', 'north', 'northing', 'y', 'lat_deg'],
            'Longitude': ['longitude', 'long', 'lon', 'x_coord', 'long_dd', 'lon_dd',
                         'longitude_dd', 'longitude_decimal', 'lon_decimal', 'gps_long',
                         'gps_longitude', 'coord_e', 'east', 'easting', 'x', 'long_deg'],
            'Elevation': ['elevation', 'altitude', 'elev', 'z_coord', 'height', 'alt',
                         'elevation_m', 'altitude_m', 'z', 'elev_m'],
        }

        for col in columns:
            if not col:  # Skip None/empty columns
                continue
                
            col_clean = str(col).lower().strip().replace(' ', '').replace('(', '').replace(')', '').replace('-', '_').replace('%', '')

            # Check against each target - prioritize exact matches
            for target, variants in targets.items():
                matched = False
                for variant in variants:
                    if variant.startswith('^') and variant.endswith('$'):
                        # Exact match (strip the ^ and $)
                        pattern = variant[1:-1]
                        if col_clean == pattern:
                            column_map[col] = target
                            matched = True
                            break
                    else:
                        # Contains match
                        if variant in col_clean:
                            column_map[col] = target
                            matched = True
                            break
                if matched:
                    break

        return column_map

    def _find_data_start_row(self, rows):
        """Find where actual data starts by detecting header row"""
        for idx, row in enumerate(rows):
            # Convert to string and check
            row_str = [str(cell).lower() if cell is not None else '' for cell in row]

            # Skip rows with very long text (citations, descriptions)
            has_long_text = any(len(cell) > 100 for cell in row_str)
            if has_long_text:
                continue

            # Look for header indicators
            has_ppm = any('ppm' in cell for cell in row_str)
            has_sample = any('sample' in cell or 'id' in cell or 'lab' in cell for cell in row_str)
            has_elements = sum(1 for el in ['cr', 'ni', 'zr', 'nb', 'ba', 'rb', 'si', 'ti', 'al', 'fe', 'mg', 'ca']
                             if any(el == cell or el in cell.split('_') for cell in row_str))

            # Count non-empty cells (should have many columns for a header row)
            non_empty = sum(1 for cell in row_str if cell and cell != 'nan')

            # Header row should have:
            # - Multiple elements OR sample + elements
            # - Multiple non-empty columns (at least 5)
            # - No extremely long text
            if non_empty >= 5 and (has_elements >= 3 or (has_sample and has_elements >= 2)):
                return idx

        return 0  # Default to first row

    def _is_units_row(self, row):
        """Check if a row contains units instead of data"""
        row_str = [str(cell).lower().strip() if cell is not None else '' for cell in row]

        # Common unit indicators
        unit_keywords = ['ppm', 'ppb', 'ppt', 'wt%', 'wt.%', 'wt %', 'percent', '%',
                        'mg/kg', 'µg/g', 'ug/g', 'mg/l', 'µg/l', 'ug/l',
                        'no.', 'unit', 'units', 'na', 'nan']

        # Also check for common header-like text that indicates units row
        header_like = ['no', 'no.', 'number']

        # Count how many cells contain unit keywords or are header-like
        unit_count = sum(1 for cell in row_str
                        if any(uk in cell for uk in unit_keywords) or cell in header_like)

        # Count numeric cells (actual data rows have numbers)
        try:
            numeric_count = sum(1 for cell in row if cell is not None and
                              isinstance(cell, (int, float)) or
                              (isinstance(cell, str) and cell.replace('.', '').replace('-', '').isdigit()))
        except:
            numeric_count = 0

        # Get non-empty cells
        non_empty = sum(1 for cell in row_str if cell and cell not in ['nan', 'none', ''])

        # If more than 20% contain units and less than 30% are numbers, it's a units row
        if non_empty > 0:
            unit_ratio = unit_count / non_empty
            numeric_ratio = numeric_count / len(row) if row else 0

            if unit_ratio > 0.2 and numeric_ratio < 0.3:
                return True

        return False

    def _parse_value(self, value):
        """Parse a value, handling negatives (below detection limit) and errors"""
        if value is None or value == '':
            return ''

        try:
            val_str = str(value).strip()
            if val_str == '' or val_str.lower() in ['nan', 'n/a', '-', 'null', 'none']:
                return ''

            # Handle negative values (below detection limit)
            val_float = float(val_str.replace(',', ''))
            if val_float < 0:
                return ''  # Below detection limit = empty

            return str(val_float)
        except:
            return str(value)  # Return as-is if can't parse

    def import_csv(self):
        path = filedialog.askopenfilename(
            title="Import Dataset",
            filetypes=[("Data files", "*.csv *.xlsx *.xls"), ("All files", "*.*")]
        )
        if not path:
            return

        try:
            # 1. Load file into new_samples + headers
            if path.lower().endswith(('.xlsx', '.xls')):
                df = pd.read_excel(path)
                headers = df.columns.tolist()
                new_samples = df.to_dict(orient='records')
            else:
                with open(path, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    headers = reader.fieldnames
                    new_samples = [row for row in reader]

            # 2. Clear table + internal data BEFORE changing columns
            self.tree.delete(*self.tree.get_children())
            self.samples = []
            self.root.update()

            # 3. Build dynamic columns from imported headers
            # No forced columns, no fixed schema
            self.setup_dynamic_columns(headers)
            self.root.update()

            # 4. Insert rows using the dynamic headers
            for row in new_samples:
                clean_row = {k: self._parse_value(v) for k, v in row.items()}
                self.samples.append(clean_row)

            # 5. Refresh table
            self.current_page = 0
            self.refresh_tree()

            # 6. HUD refresh (optional)
            if hasattr(self, 'hud_tree'):
                self._update_hud_results([])  # empty HUD until classification

            messagebox.showinfo("Success", f"Imported {len(self.samples)} rows.")

        except Exception as e:
            messagebox.showerror("Import Error", f"Crashed during import:\n{str(e)}")

    # ────────────────────────────────────────────────
    # NEW: Direct plugin import - bypasses file system
    # ────────────────────────────────────────────────
    def import_data_from_plugin(self, data_rows: List[Dict[str, Any]]):
        """
        Direct import for plugins - bypasses file system.
        Uses the SAME dynamic table engine as CSV import.
        """
        if not data_rows:
            return

        self._save_undo()  # Add undo support!

        # Same as CSV import but without the file reading step
        headers = list(data_rows[0].keys())
        self.setup_dynamic_columns(headers)

        for row in data_rows:
            clean_row = {k: self._parse_value(v) for k, v in row.items()}
            self.samples.append(clean_row)

        self.current_page = 0
        self.refresh_tree()
        self._update_status(f"Imported {len(data_rows)} samples from plugin")
        self._mark_unsaved_changes()

    def _clear_hud(self):
        """Clears all entries from the right-side classification sidebar"""
        if hasattr(self, 'hud_tree'):
            for item in self.hud_tree.get_children():
                self.hud_tree.delete(item)

    def _update_hud_results(self, filtered_indices=None):
        """
        Update the HUD with the currently filtered samples.
        If filtered_indices is None, use the full samples list.
        """
        self._clear_hud()

        # Determine which samples to show in HUD
        if filtered_indices is None:
            # Use all samples (fallback)
            display_list = self.samples
        else:
            # Use only filtered indices
            display_list = [self.samples[i] for i in filtered_indices]

        for sample in display_list:
            sample_id = sample.get('Sample_ID', sample.get('id', 'N/A'))
            classification = get_consistent_classification(sample)

            is_flagged = sample.get('Flag_For_Review') == 'YES' or sample.get('flag') == 'YES'
            if is_flagged or classification == "REVIEW REQUIRED":
                status = "⚠ REVIEW"
            elif classification == "UNCLASSIFIED":
                status = "..."
            else:
                status = "✓ OK"

            item_id = self.hud_tree.insert("", "end", values=(sample_id, classification, status))
            hex_color = SCATTER_COLORS.get(classification, "gray")
            self.hud_tree.tag_configure(classification, foreground=hex_color)
            self.hud_tree.item(item_id, tags=(classification,))

    def _configure_table_tags(self):
        """
        Configure the main Treeview tags with background colors.
        Uses SCATTER_COLORS mapping – normalizes keys to UPPERCASE.
        Call this after the tree is created and after any classification run.
        """
        if not hasattr(self, 'tree'):
            return

        # ─────────────────────────────────────────────────────────
        # 1. Configure all standard classification colors
        # ─────────────────────────────────────────────────────────
        for label, color in SCATTER_COLORS.items():
            # Normalise to uppercase – matches what sync_classification_keys() stores
            tag_name = label.strip().upper()
            try:
                self.tree.tag_configure(tag_name, background=color)
            except Exception:
                # Skip invalid colors (e.g. 'blue' is fine, but any tkinter color works)
                pass

        # ─────────────────────────────────────────────────────────
        # 2. Configure essential fallback tags
        # ─────────────────────────────────────────────────────────
        self.tree.tag_configure("UNCLASSIFIED", background="lightgray")
        self.tree.tag_configure("REVIEW REQUIRED", background="gray")
        self.tree.tag_configure("INSUFFICIENT_DATA", background="lightgray")
        self.tree.tag_configure("NO_ERROR_DATA", background="lightgray")

    def classify_all_with_scheme(self, scheme_id=None):
        if scheme_id is None: scheme_id = 'regional_triage'

        if not self.samples:
            print("DEBUG: No samples found in self.samples.")
            return

        try:
            engine = ClassificationEngine()

            # 1. Prepare Data
            prepared_list = []
            for row in self.samples:
                # Create a clean dictionary where keys have no whitespace or suffix
                clean_row = {}

                # FIRST: Copy all original data (skip empty values)
                for key, value in row.items():
                    if value is None or value == "":
                        continue
                    clean_key = str(key).strip()
                    # Don't replace _ppm yet
                    clean_row[clean_key] = value

                # SECOND: Ensure we have base element names (without _ppm)
                # This is for the coordinate math later
                for key in list(clean_row.keys()):
                    if key.endswith('_ppm'):
                        base_key = key.replace('_ppm', '')
                        if base_key not in clean_row:
                            # Copy value from _ppm to base
                            clean_row[base_key] = clean_row[key]

                # THIRD: Ensure _ppm versions exist for the engine
                # The engine's JSON rules look for "Zr_ppm", not "Zr"
                critical_elements = ['Zr', 'Nb', 'Ba', 'Rb', 'Cr', 'Ni']
                for elem in critical_elements:
                    if elem in clean_row and f"{elem}_ppm" not in clean_row:
                        clean_row[f"{elem}_ppm"] = clean_row[elem]

                # Standardize Wall Thickness
                if 'Wall_Thickness_mm' not in clean_row:
                    clean_row['Wall_Thickness_mm'] = 3.5

                prepared_list.append(clean_row)

            # 2. Execute Engine
            classified_output = engine.classify_all_samples(prepared_list, scheme_id)

            # DEBUG: Check EVERY sample
            unclassified_indices = []
            for i, res in enumerate(classified_output):
                classification = res.get('Classification', 'NO_CLASSIFICATION')
                sample_id = prepared_list[i].get('Sample_ID', f'Sample_{i}')

                if classification in ['UNCLASSIFIED', 'INSUFFICIENT_DATA', 'INVALID_SAMPLE']:
                    unclassified_indices.append(i)
                    print(f"UNCLASSIFIED: Sample {i} ({sample_id}) -> {classification}")
                    # Show its values
                    data = prepared_list[i]
                    print(f"  Zr_ppm: {data.get('Zr_ppm')}, Nb_ppm: {data.get('Nb_ppm')}")
                    print(f"  Ba_ppm: {data.get('Ba_ppm')}, Rb_ppm: {data.get('Rb_ppm')}")
                    print(f"  Cr_ppm: {data.get('Cr_ppm')}, Ni_ppm: {data.get('Ni_ppm')}")
                    print(f"  Wall: {data.get('Wall_Thickness_mm')}")

            print(f"\nDEBUG: {len(unclassified_indices)} samples unclassified: {unclassified_indices}")

            # 3. Data Sync & Coordinate Calculation
            print(f"DEBUG: Processing {len(classified_output)} engine results against {len(self.samples)} UI samples")
            processed_count = 0
            for i, res in enumerate(classified_output):
                # DEBUG: Show ALL keys in engine result
                print(f"\nDEBUG Sample {i}:")
                print(f"  All keys in engine result: {list(res.keys())}")
                print(f"  'Classification' value: {res.get('Classification')}")
                print(f"  'Auto_Classification' value: {res.get('Auto_Classification')}")

                # FIX: Engine uses 'Auto_Classification' not 'Classification'
                val = get_consistent_classification(res)
                final_val = str(val).upper().strip()
                print(f"  Using value: {final_val}")

                # Sync classification to UI
                sync_classification_keys(self.samples[i], final_val)
                processed_count += 1

                # COORDINATE MATH
                s_data = prepared_list[i]
                print(f"  Data keys for math: {[k for k in s_data.keys() if k in ['Zr', 'Nb', 'Cr', 'Ni', 'Zr_ppm', 'Nb_ppm', 'Cr_ppm', 'Ni_ppm']]}")

                # Get values with proper fallback
                zr_str = s_data.get("Zr") or s_data.get("Zr_ppm") or "0"
                nb_str = s_data.get("Nb") or s_data.get("Nb_ppm") or "1"
                cr_str = s_data.get("Cr") or s_data.get("Cr_ppm") or "0"
                ni_str = s_data.get("Ni") or s_data.get("Ni_ppm") or "1"

                print(f"  Raw values -> Zr:{zr_str}, Nb:{nb_str}, Cr:{cr_str}, Ni:{ni_str}")

                # Convert with error handling
                try:
                    zr = float(zr_str)
                    nb = float(nb_str)
                    cr = float(cr_str)
                    ni = float(ni_str)
                except (ValueError, TypeError) as e:
                    print(f"  ERROR converting to float: {e}")
                    zr, nb, cr, ni = 0.0, 1.0, 0.0, 1.0

                # Prevent division by zero
                nb_val = nb if nb != 0 else 1.0
                ni_val = ni if ni != 0 else 1.0

                self.samples[i]["Zr_Nb_Ratio"] = zr / nb_val
                self.samples[i]["Cr_Ni_Ratio"] = cr / ni_val
                print(f"  Calculated ratios -> Zr/Nb: {zr/nb_val:.3f}, Cr/Ni: {cr/ni_val:.3f}")

                # Color assignment
                color = get_color_for_label(final_val)
                self.samples[i]["Display_Color"] = color
                print(f"  Assigned color: {color}")

            print(f"\nDEBUG: Processed {processed_count} samples")

            # 4. Filter Reset
            self.filtered_samples = None

            # 5. UI Refresh
            if hasattr(self, '_update_hud_results'):
                self._update_hud_results(None)

            self.refresh_tree()
            self.refresh_plot()

            # FINAL DATA VERIFICATION
            print(f"\nDEBUG FINAL: Sample 0")
            print(f"  Final classification: {get_consistent_classification(self.samples[0])}")
            print(f"  Zr/Nb ratio: {self.samples[0].get('Zr_Nb_Ratio')}")
            print(f"  Display color: {self.samples[0].get('Display_Color')}")
            print(f"  All classification keys:")
            for key in ['Final_Classification', 'Primary_Class', 'Auto_Classification', 'Classification']:
                print(f"    {key}: {self.samples[0].get(key)}")

        except Exception as e:
            import traceback
            print(f"DEBUG ERROR: {e}")
            traceback.print_exc()
    def export_csv(self):
        if not self.samples:
            messagebox.showinfo("Info", "Nothing to export.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )
        if not path: return

        try:
            # Use the currently active headers from the UI (ignoring the checkbox)
            current_cols = [c for c in self.tree["columns"] if c != "☐"]

            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=current_cols, extrasaction="ignore")
                writer.writeheader()
                for row in self.samples:
                    writer.writerow(row)

            messagebox.showinfo("Success", f"Exported to {path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {str(e)}")

    def export_publication_table(self):
        if not self.samples:
            messagebox.showinfo("Info", "Nothing to export.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Save publication-ready table"
        )
        if not path:
            return

        pub_fields = ["Sample_ID", "Zr_Nb_Ratio", "Cr_Ni_Ratio", "Ba_Rb_Ratio",
                      "Final_Classification", "Confidence_1_to_5"]

        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(pub_fields)
                for row in self.samples:
                    writer.writerow([row.get(k, "") for k in pub_fields])

                writer.writerow([])
                writer.writerow(["Color Key"])
                writer.writerow(["EGYPTIAN (HADDADIN FLOW)", "Blue"])
                writer.writerow(["EGYPTIAN (ALKALINE / EXOTIC)", "Red"])
                writer.writerow(["SINAI / TRANSITIONAL", "Yellow"])
                writer.writerow(["SINAI OPHIOLITIC", "Orange"])
                writer.writerow(["LOCAL LEVANTINE", "Green"])
                writer.writerow(["REVIEW REQUIRED", "Gray"])

                writer.writerow([])
                writer.writerow(["References"])
                writer.writerow(["Hartung 2017 — Haddadin Flow baseline"])
                writer.writerow(["Philip & Williams-Thorpe 2001 — Egyptian vs Levantine basalt"])
                writer.writerow(["Williams-Thorpe & Thorpe 1993 — Sinai and Levantine basalts"])
                writer.writerow(["Rosenberg et al. 2016 — Levantine basalt baselines"])

            messagebox.showinfo("Success", f"Publication table exported to {path}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def clear_all(self):
        if messagebox.askyesno("Confirm", "Clear all samples?"):
            self.samples.clear()
            self.refresh_tree()
            self._update_status("Cleared")

        def _delete_samples_by_indices(self, indices_to_delete):
            """
            Delete samples by their position in self.samples and refresh the UI.
            indices_to_delete : iterable of integers (row indices)
            """
            if not indices_to_delete:
                return

            self._save_undo()

            # Delete from highest index to lowest to avoid shifting
            for idx in sorted(set(indices_to_delete), reverse=True):
                if 0 <= idx < len(self.samples):
                    del self.samples[idx]

            # Clear all selection states
            self.selected_rows.clear()
            self._refresh_table_page()

            if hasattr(self, 'hud_tree'):
                self._update_hud_results(None)

            self._mark_unsaved_changes()
            self._update_selection_count()

    def _delete_selected_rows(self):
        if not self.selected_rows:
            messagebox.showinfo("No Selection", "Please select at least one row to delete.")
            return
        count = len(self.selected_rows)
        if not messagebox.askyesno("Confirm Delete",
                                f"Delete {count} selected sample(s)?\n\nThis cannot be undone."):
            return
        self._delete_samples_by_indices(self.selected_rows)
    # ────────────────────────────────────────────────
    # Plot tab logic
    # ────────────────────────────────────────────────
    def show_plot_tab(self):
        if HAS_MATPLOTLIB:
            self.plot_info_var.set("Backend: matplotlib (best available).")
        elif HAS_PILLOW:
            self.plot_info_var.set("Matplotlib not available → using Pillow backend.")
        else:
            self.plot_info_var.set("No advanced plotting → using basic Tk canvas.")

        self.refresh_plot()
        self.notebook.select(self.plot_tab)

    def _on_backend_changed(self, selection):
        """Handle backend selection change"""
        backend = self.preferred_backend.get()
        backend_map = {
            "Auto": "automatic selection",
            "Matplotlib": "matplotlib (best quality)",
            "Pillow": "Pillow (good quality)",
            "Basic Tk": "basic Tk (simple)"
        }
        self.plot_info_var.set(f"Backend: {backend_map.get(backend, backend)} - Click 'Generate Plot' to see")
        if hasattr(self, 'plot_image_ref') and self.plot_image_ref:
            self.clear_plot()

    def refresh_plot(self):
        """FIXED: Generate scatter plot with synchronized data from all sources."""
        try:
            # 1. Clear UI
            for w in self.plot_area.winfo_children():
                if w != self.backend_status_label:
                    w.destroy()

            xs, ys, colors, labels = [], [], [], []

            # 2. Extract Data with unified key lookup
            for row in self.samples:
                try:
                    # USE UNIFIED LOOKUP FUNCTIONS - FIX FOR ISSUE #1
                    zr = get_element_value(row, "Zr")
                    nb = get_element_value(row, "Nb")
                    cr = get_element_value(row, "Cr")
                    ni = get_element_value(row, "Ni")

                    if None in (zr, nb, cr, ni) or nb == 0 or ni == 0:
                        continue

                    zrnb = zr / nb
                    crni = cr / ni

                    classification = get_consistent_classification(row)

                    # UNIFIED COLOR LOOKUP
                    color = row.get('Display_Color') or row.get('Auto_Classification_Color')
                    if not color:
                        color = get_color_for_label(classification) # Using our case-insensitive helper

                    xs.append(zrnb)
                    ys.append(crni)
                    colors.append(color)
                    labels.append(str(row.get("Sample_ID", "?")))

                except Exception as e:
                    print(f"Plot error for sample {row.get('Sample_ID', '?')}: {e}")
                    continue

            if not xs:
                self.plot_info_var.set("No valid plot data. Check Zr, Nb, Cr, Ni values.")
                return

            # 3. Render
            preferred = self.preferred_backend.get()
            if preferred == "Matplotlib" and HAS_MATPLOTLIB:
                self._plot_with_matplotlib(xs, ys, labels, colors)
            else:
                self._plot_with_tk(xs, ys, labels, colors)

        except Exception as e:
            print(f"ERROR in refresh_plot: {e}")

    def clear_plot(self):
        """Clear the plot area and reset status"""
        for w in self.plot_area.winfo_children():
            w.destroy()
        self.plot_image_ref = None
        self._matplotlib_figure = None
        self._pillow_image = None

        self.backend_status_label = tk.Label(self.plot_area, text="", fg="black", bg="white",
                                             font=("TkDefaultFont", 8, "italic"))
        self.backend_status_label.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-5)
        self._update_plot_warning()

    def _plot_with_matplotlib(self, xs, ys, labels, colors):
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        import tkinter as tk

        try:
            # 1. DESTROY EVERYTHING in the plot area to be sure
            for widget in self.plot_area.winfo_children():
                widget.destroy()

            # 2. Force the container to be visible (Grey background test)
            self.plot_area.configure(bg="lightgray")

            # 3. Create Figure
            fig = plt.figure(figsize=(5, 4))
            ax = fig.add_subplot(111)

            # 4. Draw - Force 'blue' to be a standard hex if 'blue' fails
            # But we will trust 'blue' for now as it's standard.
            ax.scatter(xs, ys, c=colors, s=200, edgecolors='black', zorder=5)

            for i, txt in enumerate(labels):
                ax.annotate(txt, (xs[i], ys[i]), xytext=(5,5), textcoords='offset points')

            ax.set_title("PROVENANCE PLOT - LIVE DATA")
            ax.set_xlabel("Zr/Nb")
            ax.set_ylabel("Cr/Ni")

            # 5. PACKING - This is usually where the 'white void' happens
            # 1. Standard Canvas Setup
            canvas = FigureCanvasTkAgg(fig, master=self.plot_area)
            canvas_widget = canvas.get_tk_widget()

            # 2. THE HAMMER: Force placement and visibility
            canvas_widget.place(relx=0, rely=0, relwidth=1, relheight=1) # Force it to fill the box
            canvas_widget.lift() # Pull it to the very front of the UI stack

            # 3. Force the Backend to talk to the GPU
            canvas.draw()

            # 4. Force the UI to recalculate size
            self.plot_area.update_idletasks()

            # 5. Backup: If using an old Tkinter version, it might need this:
            self.plot_area.config(width=500, height=400)

            self._matplotlib_figure = fig
            print("UI SYSTEM: Geometry forced. If you still see nothing, the container is invisible.")

        except Exception as e:
            print(f"UI ERROR: {e}")

    def _plot_with_pillow(self, xs, ys, labels, colors):
        width, height = 900, 600
        margin = 80
        img = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(img)

        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        if max_x == min_x: max_x += 1
        if max_y == min_y: max_y += 1

        def tx(x): return margin + (x - min_x) / (max_x - min_x) * (width - 2 * margin)
        def ty(y): return height - margin - (y - min_y) / (max_y - min_y) * (height - 2 * margin)

        draw.line((margin, margin, margin, height - margin), fill="black", width=2)
        draw.line((margin, height - margin, width - margin, height - margin), fill="black", width=2)

        for x, y, lab, col in zip(xs, ys, labels, colors):
            px, py = tx(x), ty(y)
            r = 5
            draw.ellipse((px - r, py - r, px + r, py + r), fill=col, outline="black")
            draw.text((px + 4, py - 4), lab, fill="black")

        self._pillow_image = img
        tk_img = ImageTk.PhotoImage(img)
        self.plot_image_ref = tk_img
        lbl = ttk.Label(self.plot_area, image=tk_img)
        lbl.pack(fill=tk.BOTH, expand=True)

    def _plot_with_tk(self, xs, ys, labels, colors):
        width, height = 900, 600
        margin = 80
        canvas = tk.Canvas(self.plot_area, bg="white")
        canvas.pack(fill=tk.BOTH, expand=True)

        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        if max_x == min_x: max_x += 1
        if max_y == min_y: max_y += 1

        def tx(x): return margin + (x - min_x) / (max_x - min_x) * (width - 2 * margin)
        def ty(y): return height - margin - (y - min_y) / (max_y - min_y) * (height - 2 * margin)

        canvas.config(width=width, height=height)
        canvas.create_line(margin, margin, margin, height - margin, width=2)
        canvas.create_line(margin, height - margin, width - margin, height - margin, width=2)

        for x, y, lab, col in zip(xs, ys, labels, colors):
            px, py = tx(x), ty(y)
            r = 5
            canvas.create_oval(px - r, py - r, px + r, py + r, fill=col, outline="black")
            canvas.create_text(px + 8, py - 4, text=lab, anchor="w", font=("TkDefaultFont", 8))

    def save_plot(self):
        from tkinter import filedialog, messagebox
        if self._matplotlib_figure is not None:
            path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
            if path: self._matplotlib_figure.savefig(path, dpi=300)
        elif hasattr(self, '_pillow_image') and self._pillow_image:
            path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
            if path: self._pillow_image.save(path)

    def show_help(self):
        """Show classification rules and parameters in a help window"""
        help_win = tk.Toplevel(self.root)
        help_win.title("Help - Classification Rules")
        help_win.geometry("700x600")

        text = tk.Text(help_win, wrap="word", font=("TkDefaultFont", 10), padx=20, pady=20)
        scrollbar = ttk.Scrollbar(help_win, command=text.yview)
        text.config(yscrollcommand=scrollbar.set)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        help_text = """BASALT PROVENANCE CLASSIFICATION RULES

═══════════════════════════════════════════════════════════

EGYPTIAN (HADDADIN FLOW):
  • Zr/Nb ratio: {haddadin_zrnb_min} - {haddadin_zrnb_max}
  • Ba (ppm): {haddadin_ba_min} - {haddadin_ba_max}
  • Cr/Ni ratio: {haddadin_crni_min} - {haddadin_crni_max}
  • Wall thickness: < {thin_wall} mm

  Reference: Hartung 2017 — Haddadin Flow baseline

─────────────────────────────────────────────────────────

EGYPTIAN (ALKALINE / EXOTIC):
  • Zr/Nb ratio: > {alkaline_zrnb}
  • Ba (ppm): > {alkaline_ba}
  • Wall thickness: < {thin_wall} mm

  Reference: Philip & Williams-Thorpe 2001

─────────────────────────────────────────────────────────

SINAI OPHIOLITIC:
  • Zr/Nb ratio: ≥ {ophiolitic_zrnb}
  • Cr/Ni ratio: {ophiolitic_crni_min} - {ophiolitic_crni_max}
  • Ba (ppm): ≤ {ophiolitic_ba}
  • Rb (ppm): ≤ {ophiolitic_rb}

  Reference: Williams-Thorpe & Thorpe 1993

─────────────────────────────────────────────────────────

SINAI / TRANSITIONAL:
  • Zr/Nb ratio: {sinai_zrnb_min} - {sinai_zrnb_max}

  Reference: Williams-Thorpe & Thorpe 1993

─────────────────────────────────────────────────────────

LOCAL LEVANTINE:
  • Zr/Nb ratio: < 15
  • Cr/Ni ratio: > {levantine_crni}
  • Ba (ppm): < 200
  • Wall thickness: > {thick_wall} mm

  Reference: Rosenberg et al. 2016

═══════════════════════════════════════════════════════════

KEYBOARD SHORTCUTS:
  Ctrl+I   Import pXRF
  Ctrl+S   Export pXRF
  Ctrl+C   Classify All
  Ctrl+D   Generate Demo Data
  Ctrl+T   Show Statistics
  Ctrl+R   Refresh Plot
  Ctrl+Q   Quit
  F1       This Help

═══════════════════════════════════════════════════════════
""".format(
            haddadin_zrnb_min=HADDADIN_ZRNB_MIN,
            haddadin_zrnb_max=HADDADIN_ZRNB_MAX,
            haddadin_ba_min=HADDADIN_BA_MIN,
            haddadin_ba_max=HADDADIN_BA_MAX,
            haddadin_crni_min=HADDADIN_CRNI_MIN,
            haddadin_crni_max=HADDADIN_CRNI_MAX,
            alkaline_zrnb=ALKALINE_ZRNB_THRESHOLD,
            alkaline_ba=ALKALINE_BA_THRESHOLD,
            ophiolitic_zrnb=OPHIOLITIC_ZRNB_MIN,
            ophiolitic_crni_min=OPHIOLITIC_CRNI_MIN,
            ophiolitic_crni_max=OPHIOLITIC_CRNI_MAX,
            ophiolitic_ba=OPHIOLITIC_BA_MAX,
            ophiolitic_rb=OPHIOLITIC_RB_MAX,
            sinai_zrnb_min=SINAI_ZRNB_MIN,
            sinai_zrnb_max=SINAI_ZRNB_MAX,
            levantine_crni=LEVANTINE_CRNI_THRESHOLD,
            thin_wall=THIN_WALL_THRESHOLD_MM,
            thick_wall=THICK_WALL_THRESHOLD_MM
        )

        text.insert("1.0", help_text)
        text.config(state="disabled")

    def show_about(self):
        """Tightest spacing: line-after-line flow, zero pady on normal lines"""
        about_win = tk.Toplevel(self.root)
        about_win.title("About Basalt Provenance Triage Toolkit")
        about_win.geometry("640x660")  # even shorter now
        about_win.resizable(True, True)

        main = tk.Frame(about_win, padx=28, pady=12)
        main.pack(fill=tk.BOTH, expand=True)

        # Title block — no waste
        tk.Label(main, text="Basalt Provenance Triage Toolkit v10.2",
                 font=("TkDefaultFont", 15, "bold")).pack(pady=(0,3))
        tk.Label(main, text="© 2026 Sefy Levy  •  All Rights Reserved",
                 font=("TkDefaultFont", 9)).pack(pady=0)

        email = tk.Label(main, text="sefy76@gmail.com", fg="blue", cursor="hand2",
                         font=("TkDefaultFont", 9))
        email.pack(pady=0)
        email.bind("<Button-1>", lambda e: webbrowser.open("mailto:sefy76@gmail.com"))

        tk.Label(main, text="DOI: https://doi.org/10.5281/zenodo.18499129",
                 fg="blue", cursor="hand2", font=("TkDefaultFont", 9)).pack(pady=0)

        # License → description: minimal separation
        tk.Label(main, text="CC BY-NC-SA 4.0 — Non-commercial research & education use",
                 font=("TkDefaultFont", 9, "italic")).pack(pady=(6,4))

        tk.Label(main, text="Geochemical provenance triage for Levantine & Egyptian basalt artifacts",
                 font=("TkDefaultFont", 10), wraplength=580, justify="center").pack(pady=(0,8))

        # ── Dedication Box – ultra-tight internal flow ───────────
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

        # ── Credits – no gaps between lines ──────────────────────
        tk.Label(main, text="Classification methodology: Sefy Levy (2026)",
                 font=("TkDefaultFont", 9)).pack(pady=(10,2))

        tk.Label(main, text="Implementation with generous help from:",
                 font=("TkDefaultFont", 9)).pack(pady=0)
        tk.Label(main, text="Gemini • Copilot • ChatGPT • Claude • DeepSeek • Mistral • Grok",
                 font=("TkDefaultFont", 9, "italic")).pack(pady=0)

        # ── Scientific foundations – tight centered lines ────────
        science_frame = tk.Frame(main)
        science_frame.pack(pady=(12,6), fill=tk.X)

        tk.Label(science_frame, text="Scientific foundations",
                 font=("TkDefaultFont", 10, "bold")).pack(pady=(0,3))

        refs = [
            "Hartung, J. (2017) — Egyptian basalt provenance methodology",
            "Philip, G. & Williams-Thorpe, O. (2001) — Archaeological basalt sourcing",
            "Williams-Thorpe, O. & Thorpe, R. S. (1993) — Geochemical characterization",
            "Rosenberg, D. et al. (2016) — Basalt vessels and groundstone tools",
        ]

        for ref in refs:
            tk.Label(science_frame, text=ref, font=("TkDefaultFont", 9),
                     wraplength=560, justify="center").pack(pady=0)

        # Citation – tight
        tk.Label(main, text="If used in research — please cite:",
                 font=("TkDefaultFont", 9, "bold")).pack(pady=(10,2))

        citation = (
            "Levy, S. (2026). Basalt Provenance Triage Toolkit v10.1.\n"
            "Zenodo. https://doi.org/10.5281/zenodo.18499129"
        )
        tk.Label(main, text=citation, font=("TkDefaultFont", 9), justify="center").pack(pady=0)

        # Close button
        tk.Button(main, text="Close", width=12, command=about_win.destroy).pack(pady=(10,0))

    def show_support(self):
        """Dedicated Support / Donation dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Support Basalt Provenance Triage Toolkit")
        dialog.geometry("520x520")
        dialog.resizable(False, False)

        # Center on screen
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (520 // 2)
        y = (dialog.winfo_screenheight() // 2) - (520 // 2)
        dialog.geometry(f"520x520+{x}+{y}")

        main = ttk.Frame(dialog, padding=25)
        main.pack(fill=tk.BOTH, expand=True)

        # Header
        ttk.Label(main, text="Support the Project",
                 font=("TkDefaultFont", 16, "bold")).pack(pady=(0, 8))

        ttk.Label(main, text="Basalt Provenance Triage Toolkit v10.2",
                 font=("TkDefaultFont", 11)).pack()

        ttk.Label(main, text="Created by Sefy Levy • 2026",
                 font=("TkDefaultFont", 10)).pack(pady=4)

        ttk.Label(main, text="sefy76@gmail.com",
                 foreground="blue", cursor="hand2").pack(pady=2)

        ttk.Label(main, text="This tool is 100% free and open-source (CC BY-NC-SA 4.0)\n"
                            "for research and educational use.",
                 font=("TkDefaultFont", 9), justify="center").pack(pady=(12, 20))

        ttk.Separator(main, orient="horizontal").pack(fill=tk.X, pady=15)

        # Main message - centered and wrapped properly
        ttk.Label(main, text="If this tool has saved you time,\n"
                            "helped triage samples, or contributed to your research,\n"
                            "any support is deeply appreciated and goes straight back into keeping it free and improving it.",
                 font=("TkDefaultFont", 10),
                 justify="center",          # centers text lines
                 wraplength=450,            # ← forces wrapping at ~450px so it doesn't stretch too wide
                 anchor="center").pack(     # ← centers the whole label widget horizontally
                 pady=(0, 20))

        # Donation buttons in a nice frame
        donate_frame = ttk.LabelFrame(main, text="Ways to Support", padding=15)
        donate_frame.pack(fill=tk.X, pady=10)

        def open_link(url):
            import webbrowser
            webbrowser.open(url)

        # ←←← Replace these URLs with your real ones ↓↓↓
        buttons = [
            ("Ko-fi – Buy me a coffee ☕", "https://ko-fi.com/sefy76"),
            ("PayPal.me – Quick one-time donation", "https://paypal.me/sefy76"),
            ("PayPal direct to sefy76@gmail.com", "https://www.paypal.com/donate/?business=sefy76@gmail.com&item_name=Support+Basalt+Provenance+Triage+Toolkit"),
            ("Liberapay – Recurring support (0% platform fee)", "https://liberapay.com/sefy76"),
        ]

        for text, url in buttons:
            btn = ttk.Button(donate_frame, text=text,
                            command=lambda u=url: open_link(u))
            btn.pack(fill=tk.X, pady=4)

        ttk.Separator(main, orient="horizontal").pack(fill=tk.X, pady=20)

        ttk.Label(main, text="Thank you for believing in open archaeological tools.",
                 font=("TkDefaultFont", 9, "italic")).pack(pady=(0, 15))

        ttk.Button(main, text="Close", command=dialog.destroy).pack(pady=10)

    def _open_url(self, url):
        """Open URL in default browser or email client"""
        try:
            webbrowser.open(url)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open link:\n{url}\n\nError: {str(e)}")

    def show_statistics(self):
        """Show statistical summary inline in the table area"""
        if not self.samples:
            messagebox.showinfo("No Data", "No samples to analyze.")
            return

        # Switch to the Data Table tab (index 0)
        self.notebook.select(0)
        # Show the report view inside the table tab
        self._show_report_view()

        # Clear any existing content in report view
        for widget in self.report_view.winfo_children():
            widget.destroy()

        # Create header with back button
        header = ttk.Frame(self.report_view)
        header.pack(fill=tk.X, pady=(0, 10), padx=10)

        ttk.Button(header, text="← Back to Table", command=self._hide_report_view,
                style="Accent.TButton").pack(side=tk.LEFT)
        ttk.Label(header, text="Statistical Summary",
                font=("Arial", 14, "bold")).pack(side=tk.LEFT, padx=20)

        # Create text widget for statistics
        text_frame = ttk.Frame(self.report_view)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        text = tk.Text(text_frame, wrap="word", font=("Courier", 9), padx=15, pady=15)
        scrollbar = ttk.Scrollbar(text_frame, command=text.yview)
        text.config(yscrollcommand=scrollbar.set)

        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Group by classification
        from collections import defaultdict
        groups = defaultdict(list)
        for sample in self.samples:
            cls = get_consistent_classification(sample)
            groups[cls].append(sample)

        text.insert("end", "STATISTICAL SUMMARY BY CLASSIFICATION\n")
        text.insert("end", "═" * 85 + "\n\n")

        for cls in sorted(groups.keys()):
            samples_list = groups[cls]
            text.insert("end", f"{cls} ({len(samples_list)} samples)\n")
            text.insert("end", "─" * 85 + "\n")

            # Calculate statistics for each field
            fields = ["Zr_ppm", "Nb_ppm", "Ba_ppm", "Rb_ppm", "Cr_ppm", "Ni_ppm",
                    "Zr_Nb_Ratio", "Cr_Ni_Ratio", "Ba_Rb_Ratio"]

            for field in fields:
                values = [safe_float(s.get(field)) for s in samples_list]
                values = [v for v in values if v is not None]

                if values:
                    mean = statistics.mean(values)
                    median = statistics.median(values)
                    std = statistics.stdev(values) if len(values) > 1 else 0.0
                    min_val = min(values)
                    max_val = max(values)

                    text.insert("end", f"  {field:15s}: ")
                    text.insert("end", f"mean={mean:8.2f}  median={median:8.2f}  ")
                    text.insert("end", f"std={std:7.2f}  range=[{min_val:.1f}, {max_val:.1f}]\n")

            text.insert("end", "\n")

        text.config(state="disabled")

    def save_all_plots(self):
        """Save all plot variations to a directory"""
        directory = filedialog.askdirectory(title="Select directory to save plots")
        if not directory:
            return

        if not self.samples:
            messagebox.showinfo("No Data", "No samples to plot.")
            return

        saved_count = 0

        # Define multiple plot combinations
        plot_configs = [
            ("Zr_Nb_vs_Cr_Ni", "Zr_Nb_Ratio", "Cr_Ni_Ratio"),
            ("Zr_Nb_vs_Ba", "Zr_Nb_Ratio", "Ba_ppm"),
            ("Zr_Nb_vs_Ba_Rb", "Zr_Nb_Ratio", "Ba_Rb_Ratio"),
            ("Cr_Ni_vs_Ba", "Cr_Ni_Ratio", "Ba_ppm"),
        ]

        for filename, x_field, y_field in plot_configs:
            try:
                # Extract data
                xs, ys, labels, colors = [], [], [], []
                for row in self.samples:
                    x = safe_float(row.get(x_field))
                    y = safe_float(row.get(y_field))

                    if x is not None and y is not None:
                        xs.append(x)
                        ys.append(y)
                        labels.append(row.get("Sample_ID", "?"))

                        # Use the color we saved in Block 1
                        c = row.get("Display_Color") or row.get("Auto_Classification_Color") or "gray"
                        colors.append(c)

                # FIX: Stop looking up the color again! Just use the one already saved.
                # This ensures Block 6 shows the exact same 'blue' as Block 5.
                c = row.get("Display_Color") or row.get("Auto_Classification_Color") or "gray"
                colors.append(c)

                if not xs:
                    continue

                # Create plot with matplotlib if available
                if HAS_MATPLOTLIB:
                    fig, ax = plt.subplots(figsize=(10, 7), dpi=150)
                    ax.scatter(xs, ys, c=colors, edgecolors="black", s=60, alpha=0.7)

                    for x, y, lab in zip(xs, ys, labels):
                        ax.text(x, y, lab, fontsize=7, ha="right", va="bottom")

                    ax.set_xlabel(x_field.replace("_", " / "))
                    ax.set_ylabel(y_field.replace("_", " / "))
                    ax.set_title(f"{x_field} vs {y_field}")
                    ax.grid(True, alpha=0.3)

                    # Add legend
                    from matplotlib.lines import Line2D
                    legend_elements = [Line2D([0], [0], marker='o', color='w',
                                             markerfacecolor=col, markersize=10, label=cls)
                                     for cls, col in SCATTER_COLORS.items()]
                    ax.legend(handles=legend_elements, loc='best', fontsize=8)

                    plt.tight_layout()
                    filepath = f"{directory}/{filename}.png"
                    fig.savefig(filepath, dpi=300, bbox_inches='tight')
                    plt.close(fig)
                    saved_count += 1

            except Exception as e:
                print(f"Error saving {filename}: {e}")

        if saved_count > 0:
            messagebox.showinfo("Success", f"Saved {saved_count} plots to:\n{directory}")
        else:
            messagebox.showwarning("Warning", "No plots could be saved. Check that matplotlib is installed.")

    def load_config(self):
        """Load classification parameters from JSON file"""
        path = filedialog.askopenfilename(
            title="Load Configuration",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not path:
            return

        try:
            with open(path, 'r') as f:
                config = json.load(f)

            # Update global parameters
            global HADDADIN_ZRNB_MIN, HADDADIN_ZRNB_MAX, HADDADIN_BA_MIN, HADDADIN_BA_MAX
            global HADDADIN_CRNI_MIN, HADDADIN_CRNI_MAX, ALKALINE_ZRNB_THRESHOLD
            global ALKALINE_BA_THRESHOLD, SINAI_ZRNB_MIN, SINAI_ZRNB_MAX
            global OPHIOLITIC_ZRNB_MIN, OPHIOLITIC_CRNI_MIN, OPHIOLITIC_CRNI_MAX
            global OPHIOLITIC_BA_MAX, OPHIOLITIC_RB_MAX, LEVANTINE_CRNI_THRESHOLD
            global THIN_WALL_THRESHOLD_MM, THICK_WALL_THRESHOLD_MM

            HADDADIN_ZRNB_MIN = config.get("HADDADIN_ZRNB_MIN", HADDADIN_ZRNB_MIN)
            HADDADIN_ZRNB_MAX = config.get("HADDADIN_ZRNB_MAX", HADDADIN_ZRNB_MAX)
            HADDADIN_BA_MIN = config.get("HADDADIN_BA_MIN", HADDADIN_BA_MIN)
            HADDADIN_BA_MAX = config.get("HADDADIN_BA_MAX", HADDADIN_BA_MAX)
            HADDADIN_CRNI_MIN = config.get("HADDADIN_CRNI_MIN", HADDADIN_CRNI_MIN)
            HADDADIN_CRNI_MAX = config.get("HADDADIN_CRNI_MAX", HADDADIN_CRNI_MAX)
            ALKALINE_ZRNB_THRESHOLD = config.get("ALKALINE_ZRNB_THRESHOLD", ALKALINE_ZRNB_THRESHOLD)
            ALKALINE_BA_THRESHOLD = config.get("ALKALINE_BA_THRESHOLD", ALKALINE_BA_THRESHOLD)
            SINAI_ZRNB_MIN = config.get("SINAI_ZRNB_MIN", SINAI_ZRNB_MIN)
            SINAI_ZRNB_MAX = config.get("SINAI_ZRNB_MAX", SINAI_ZRNB_MAX)
            OPHIOLITIC_ZRNB_MIN = config.get("OPHIOLITIC_ZRNB_MIN", OPHIOLITIC_ZRNB_MIN)
            OPHIOLITIC_CRNI_MIN = config.get("OPHIOLITIC_CRNI_MIN", OPHIOLITIC_CRNI_MIN)
            OPHIOLITIC_CRNI_MAX = config.get("OPHIOLITIC_CRNI_MAX", OPHIOLITIC_CRNI_MAX)
            OPHIOLITIC_BA_MAX = config.get("OPHIOLITIC_BA_MAX", OPHIOLITIC_BA_MAX)
            OPHIOLITIC_RB_MAX = config.get("OPHIOLITIC_RB_MAX", OPHIOLITIC_RB_MAX)
            LEVANTINE_CRNI_THRESHOLD = config.get("LEVANTINE_CRNI_THRESHOLD", LEVANTINE_CRNI_THRESHOLD)
            THIN_WALL_THRESHOLD_MM = config.get("THIN_WALL_THRESHOLD_MM", THIN_WALL_THRESHOLD_MM)
            THICK_WALL_THRESHOLD_MM = config.get("THICK_WALL_THRESHOLD_MM", THICK_WALL_THRESHOLD_MM)

            messagebox.showinfo("Success", f"Configuration loaded from:\n{path}\n\nRe-run 'Classify All' to apply new thresholds.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load config:\n{str(e)}")

    def save_config(self):
        """Save current classification parameters to JSON file"""
        path = filedialog.asksaveasfilename(
            title="Save Configuration",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not path:
            return

        try:
            config = {
                "HADDADIN_ZRNB_MIN": HADDADIN_ZRNB_MIN,
                "HADDADIN_ZRNB_MAX": HADDADIN_ZRNB_MAX,
                "HADDADIN_BA_MIN": HADDADIN_BA_MIN,
                "HADDADIN_BA_MAX": HADDADIN_BA_MAX,
                "HADDADIN_CRNI_MIN": HADDADIN_CRNI_MIN,
                "HADDADIN_CRNI_MAX": HADDADIN_CRNI_MAX,
                "ALKALINE_ZRNB_THRESHOLD": ALKALINE_ZRNB_THRESHOLD,
                "ALKALINE_BA_THRESHOLD": ALKALINE_BA_THRESHOLD,
                "SINAI_ZRNB_MIN": SINAI_ZRNB_MIN,
                "SINAI_ZRNB_MAX": SINAI_ZRNB_MAX,
                "OPHIOLITIC_ZRNB_MIN": OPHIOLITIC_ZRNB_MIN,
                "OPHIOLITIC_CRNI_MIN": OPHIOLITIC_CRNI_MIN,
                "OPHIOLITIC_CRNI_MAX": OPHIOLITIC_CRNI_MAX,
                "OPHIOLITIC_BA_MAX": OPHIOLITIC_BA_MAX,
                "OPHIOLITIC_RB_MAX": OPHIOLITIC_RB_MAX,
                "LEVANTINE_CRNI_THRESHOLD": LEVANTINE_CRNI_THRESHOLD,
                "THIN_WALL_THRESHOLD_MM": THIN_WALL_THRESHOLD_MM,
                "THICK_WALL_THRESHOLD_MM": THICK_WALL_THRESHOLD_MM,
            }

            with open(path, 'w') as f:
                json.dump(config, f, indent=4)

            messagebox.showinfo("Success", f"Configuration saved to:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config:\n{str(e)}")

    def batch_process_directory(self):
        """Process all CSV files in a directory"""
        input_dir = filedialog.askdirectory(title="Select input directory with CSV files")
        if not input_dir:
            return

        output_dir = filedialog.askdirectory(title="Select output directory for processed files")
        if not output_dir:
            return

        import glob

        csv_files = glob.glob(os.path.join(input_dir, "*.csv"))
        if not csv_files:
            messagebox.showinfo("No Files", f"No CSV files found in:\n{input_dir}")
            return

        processed = 0
        errors = []

        progress_win = tk.Toplevel(self.root)
        progress_win.title("Batch Processing")
        progress_win.geometry("400x150")

        tk.Label(progress_win, text="Processing CSV files...").pack(pady=10)
        progress_var = tk.StringVar(value="0 / 0")
        tk.Label(progress_win, textvariable=progress_var).pack()
        progress_bar = ttk.Progressbar(progress_win, length=300, mode='determinate')
        progress_bar.pack(pady=20)
        progress_bar['maximum'] = len(csv_files)

        for i, csv_file in enumerate(csv_files):
            try:
                # Call the batch_process_csv function
                basename = os.path.basename(csv_file)
                output_path = os.path.join(output_dir, f"classified_{basename}")
                batch_process_csv(csv_file, output_path)
                processed += 1
            except Exception as e:
                errors.append(f"{os.path.basename(csv_file)}: {str(e)}")

            progress_var.set(f"{i+1} / {len(csv_files)}")
            progress_bar['value'] = i + 1
            progress_win.update()

        progress_win.destroy()

        msg = f"Batch processing complete!\n\nProcessed: {processed} files"
        if errors:
            msg += f"\nErrors: {len(errors)}\n\n" + "\n".join(errors[:5])
            if len(errors) > 5:
                msg += f"\n... and {len(errors)-5} more"

        messagebox.showinfo("Batch Complete", msg)

    # ════════════════════════════════════════════════════════════════════
    # NEW FEATURES - Search, Filter, Sort, Undo, Recent Files, etc.
    # ════════════════════════════════════════════════════════════════════

    def _apply_filter(self):
        """OPTIMIZED: High-speed filtering using index caching."""
        search_term = self.search_var.get().lower()
        class_filter = self.filter_class_var.get()

        # 1. Check if the filter hasn't changed (Cache hit)
        current_state = (search_term, class_filter)
        if self.filter_cache is not None and self.last_filter_state == current_state:
            self.current_page = 0
            self._refresh_table_page()
            self.last_filter_state = current_state
            self.current_page = 0
            self._refresh_table_page()

            # FIX FOR ISSUE #2: Sync HUD with filtered results
            if hasattr(self, 'hud_tree'):
                # Show ALL samples in HUD (not filtered)
                self._update_hud_results(None)
            return

        # 2. Rebuild Filtered List
        self.filter_cache = []
        for idx, row in enumerate(self.samples):
            # Text Search
            id_match = search_term in str(row.get("Sample_ID", "")).lower()
            note_match = search_term in str(row.get("Notes", "")).lower()

            # Classification Search
            cls = get_consistent_classification(row)
            cls_match = (class_filter == "All" or cls == class_filter)

            if (id_match or note_match) and cls_match:
                self.filter_cache.append(idx) # Store the INDEX, not the row

        self.last_filter_state = current_state
        self.current_page = 0
        self._refresh_table_page()

    def _refresh_table_page(self):
            """OPTIMIZED: Draws only the visible page using cached indices."""
            self.tree.delete(*self.tree.get_children())

            display_indices = self.filter_cache if self.filter_cache is not None else list(range(len(self.samples)))

            start = self.current_page * ROWS_PER_PAGE
            end = start + ROWS_PER_PAGE

            for idx in display_indices[start:end]:
                if idx < len(self.samples):
                    self._insert_row_with_index(self.samples[idx], idx)

            total_pages = max(1, (len(display_indices) + ROWS_PER_PAGE - 1) // ROWS_PER_PAGE)
            if hasattr(self, 'page_label'):
                self.page_label.config(text=f"Page {self.current_page + 1} of {total_pages}")

            # ⚠️ ADD THIS – update pagination button states
            if hasattr(self, 'prev_btn') and hasattr(self, 'next_btn'):
                self.prev_btn.state(["!disabled" if self.current_page > 0 else "disabled"])
                self.next_btn.state(["!disabled" if self.current_page < total_pages - 1 else "disabled"])

    def _insert_row_with_index(self, row: Dict[str, Any], row_idx: int):
        """Ultra-fast row insertion using pre-calculated index."""
        # 1. Checkbox logic (O(1) lookup)
        checkbox = "☑" if row_idx in self.selected_rows else "☐"

        # 2. Get active headers
        current_cols = list(self.tree["columns"])
        row_data = []

        for col in current_cols:
            if col == "☐":
                row_data.append(checkbox)
            elif col in ["Zr_Nb_Ratio", "Cr_Ni_Ratio"]:
                val = row.get(col, "")
                row_data.append(f"{val:.3f}" if isinstance(val, (int, float)) else val)
            else:
                row_data.append(str(row.get(col, "")))

        # 3. Get tag (Color)
        tag = get_consistent_classification(row).upper()

        # 4. Insert - IID set to row index for reliable deletion
        self.tree.insert("", "end", iid=str(row_idx), values=tuple(row_data), tags=(tag,))


    def _update_filter_options(self):
        """Rebuilds the filter dropdown with unique results from the data."""
        if not hasattr(self, 'filter_class_var'): return

        unique_classes = set()
        for s in self.samples:
            cls = s.get("Auto_Classification")
            if cls: unique_classes.add(cls)

        new_options = ["All"] + sorted(list(unique_classes))

        # Update the OptionMenu (if your UI uses a standard ttk.OptionMenu)
        if hasattr(self, 'filter_menu'):
            menu = self.filter_menu["menu"]
            menu.delete(0, "end")
            for string in new_options:
                menu.add_command(label=string, command=lambda v=string: self.filter_class_var.set(v))

    def _clear_filter(self):
        """Clear all filters"""
        self.search_var.set("")
        self.filter_class_var.set("All")
        self.filtered_samples = self.samples
        self.current_page = 0
        self._refresh_table_page()
        self._update_status("Ready")

    def _sort_column(self, col):
        """Sort table by clicking column header"""
        data_to_sort = self.filtered_samples if self.filtered_samples else self.samples

        # Try numeric sort first, fall back to string sort
        try:
            data_to_sort.sort(key=lambda x: safe_float(x.get(col, "")) or float('inf'))
        except:
            data_to_sort.sort(key=lambda x: str(x.get(col, "")))

        if self.filtered_samples:
            self.filtered_samples = data_to_sort
        else:
            self.samples = data_to_sort

        self.current_page = 0
        self._refresh_table_page()

    def duplicate_selected(self):
        """Duplicate the currently selected row"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Please select a sample to duplicate.")
            return

        item = selection[0]
        values = self.tree.item(item, "values")

        # Correct: Sample_ID is always column 0
        sample_id = values[0]

        original = None
        for row in self.samples:
            if row.get("Sample_ID") == sample_id:
                original = row
                break

        if not original:
            return

        duplicate = copy.deepcopy(original)
        duplicate["Sample_ID"] = f"{duplicate['Sample_ID']}_copy"

        self._save_undo()
        self.samples.append(duplicate)
        self._apply_filter()
        self._update_status(f"Duplicated {sample_id}")

    def undo_last(self):
        """Undo last action"""
        if not self.undo_stack:
            messagebox.showinfo("Info", "Nothing to undo.")
            return

        self.samples = self.undo_stack.pop()
        self._apply_filter()
        self._update_status("Undo successful")

    def _save_undo(self):
        """Save current state to undo stack"""
        if len(self.undo_stack) >= MAX_UNDO_STACK:
            self.undo_stack.pop(0)
        self.undo_stack.append(copy.deepcopy(self.samples))

    def _on_row_double_click(self, event):
        """Edit sample when double-clicking a row (uses row index from tree iid)."""
        selection = self.tree.selection()
        if not selection:
            return

        item = selection[0]

        # Get row index from tree item ID (iid = str(row_idx))
        try:
            row_idx = int(item)
        except ValueError:
            messagebox.showerror("Error", "Cannot identify row index.")
            return

        if not (0 <= row_idx < len(self.samples)):
            return

        sample = self.samples[row_idx]
        sample_id = sample.get("Sample_ID", f"Row {row_idx}")

        # Create edit dialog
        edit_win = tk.Toplevel(self.root)
        edit_win.title(f"Edit Sample: {sample_id}")
        edit_win.geometry("500x700")

        main_frame = ttk.Frame(edit_win, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create entry fields for all columns
        entry_vars = {}
        row_num = 0
        current_cols = list(self.tree["columns"])

        for col in current_cols:
            if col == "☐":  # Skip checkbox column
                continue
            ttk.Label(main_frame, text=f"{col}:").grid(
                row=row_num, column=0, sticky="w", pady=5, padx=5
            )
            var = tk.StringVar(value=str(sample.get(col, "")))
            entry = ttk.Entry(main_frame, textvariable=var, width=40)
            entry.grid(row=row_num, column=1, pady=5, padx=5, sticky="ew")
            entry_vars[col] = var
            row_num += 1

        main_frame.columnconfigure(1, weight=1)

        # Show alteration warnings if any
        warnings = sample.get("Alteration_Warnings", "")
        if warnings:
            row_num += 1
            ttk.Separator(main_frame, orient=tk.HORIZONTAL).grid(
                row=row_num, column=0, columnspan=2, sticky="ew", pady=10
            )
            row_num += 1

            warning_frame = ttk.Frame(main_frame)
            warning_frame.grid(row=row_num, column=0, columnspan=2, sticky="ew", pady=10)

            ttk.Label(
                warning_frame,
                text="⚠️ ALTERATION WARNINGS:",
                font=("Arial", 10, "bold"),
                foreground="orange",
            ).pack(anchor="w")

            warning_text = tk.Text(
                warning_frame,
                height=4,
                wrap=tk.WORD,
                bg="#fff3cd",
                fg="#856404",
                font=("Arial", 9),
            )
            warning_text.pack(fill=tk.BOTH, expand=True, pady=5)
            warning_text.insert("1.0", warnings.replace(" | ", "\n"))
            warning_text.config(state=tk.DISABLED)

            row_num += 1

        # ─────────────────────────────────────────────────────────────────
        # Save changes – updates the sample dict and refreshes the table
        # ─────────────────────────────────────────────────────────────────
        def save_changes():
            self._save_undo()
            for col, var in entry_vars.items():
                sample[col] = var.get()
            self._apply_filter()
            edit_win.destroy()
            self._update_status(f"Updated {sample_id}")

        # ─────────────────────────────────────────────────────────────────
        # Delete sample – uses the new index‑based deletion
        # ─────────────────────────────────────────────────────────────────
        def delete_sample():
            if messagebox.askyesno("Confirm Delete", f"Delete sample {sample_id}?"):
                self._delete_samples_by_indices([row_idx])
                edit_win.destroy()

        # ─────────────────────────────────────────────────────────────────
        # Explain classification – shows detailed geochemical reasoning
        # ─────────────────────────────────────────────────────────────────
        def explain_classification():
            explanation = self._explain_classification_logic(sample)
            explain_win = tk.Toplevel(edit_win)
            explain_win.title(f"Classification Explanation: {sample_id}")
            explain_win.geometry("600x500")

            header_frame = ttk.Frame(explain_win, padding=10)
            header_frame.pack(fill=tk.X)
            ttk.Label(
                header_frame, text="Why This Classification?",
                font=("Arial", 14, "bold")
            ).pack()
            ttk.Label(header_frame, text=sample_id, font=("Arial", 10)).pack()

            text_frame = ttk.Frame(explain_win, padding=10)
            text_frame.pack(fill=tk.BOTH, expand=True)

            text = tk.Text(
                text_frame,
                wrap=tk.WORD,
                padx=10,
                pady=10,
                font=("Arial", 10)
            )
            scrollbar = ttk.Scrollbar(text_frame, command=text.yview)
            text.config(yscrollcommand=scrollbar.set)
            text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            text.insert("1.0", explanation)
            text.config(state=tk.DISABLED)

            ttk.Button(explain_win, text="Close", command=explain_win.destroy).pack(pady=10)

        # ─────────────────────────────────────────────────────────────────
        # Buttons at the bottom of the edit dialog
        # ─────────────────────────────────────────────────────────────────
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row_num, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="Save Changes", command=save_changes).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="💡 Explain Classification", command=explain_classification).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete Sample", command=delete_sample).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=edit_win.destroy).pack(side=tk.LEFT, padx=5)

    def _explain_classification_logic(self, sample):
        """Generate plain-language explanation of classification"""
        try:
            # Get values
            zr = safe_float(sample.get("Zr_ppm", ""))
            nb = safe_float(sample.get("Nb_ppm", ""))
            ba = safe_float(sample.get("Ba_ppm", ""))
            rb = safe_float(sample.get("Rb_ppm", ""))
            cr = safe_float(sample.get("Cr_ppm", ""))
            ni = safe_float(sample.get("Ni_ppm", ""))
            wall = safe_float(sample.get("Wall_Thickness_mm", ""))

            # Calculate ratios
            zr_nb = zr / nb if (zr and nb and nb != 0) else None
            cr_ni = cr / ni if (cr and ni and ni != 0) else None
            ba_rb = ba / rb if (ba and rb and rb != 0) else None

            classification = get_consistent_classification(sample)
            confidence = sample.get("Auto_Confidence", "")

            explanation = []
            explanation.append(f"Sample: {sample.get('Sample_ID', 'Unknown')}\n")
            explanation.append("=" * 60 + "\n\n")

            # Show current classification
            if classification:
                explanation.append(f"CLASSIFICATION: {classification}\n")
                explanation.append(f"CONFIDENCE: {confidence}\n\n")
            else:
                explanation.append("CLASSIFICATION: Not yet classified\n\n")

            explanation.append("GEOCHEMICAL DATA:\n")
            explanation.append("-" * 60 + "\n")
            explanation.append(f"  Zr (Zirconium):  {zr if zr else 'MISSING'} ppm\n")
            explanation.append(f"  Nb (Niobium):    {nb if nb else 'MISSING'} ppm\n")
            explanation.append(f"  Ba (Barium):     {ba if ba else 'MISSING'} ppm\n")
            explanation.append(f"  Rb (Rubidium):   {rb if rb else 'MISSING'} ppm\n")
            explanation.append(f"  Cr (Chromium):   {cr if cr else 'MISSING'} ppm\n")
            explanation.append(f"  Ni (Nickel):     {ni if ni else 'MISSING'} ppm\n")
            explanation.append(f"  Wall Thickness:  {wall if wall else 'MISSING'} mm\n\n")

            explanation.append("RATIOS:\n")
            explanation.append("-" * 60 + "\n")
            if zr_nb:
                explanation.append(f"  Zr/Nb = {zr_nb:.2f}\n")
            else:
                explanation.append(f"  Zr/Nb = CANNOT CALCULATE (missing data)\n")

            if cr_ni:
                explanation.append(f"  Cr/Ni = {cr_ni:.2f}\n")
            else:
                explanation.append(f"  Cr/Ni = CANNOT CALCULATE (missing data)\n")

            if ba_rb:
                explanation.append(f"  Ba/Rb = {ba_rb:.2f}\n\n")
            else:
                explanation.append(f"  Ba/Rb = CANNOT CALCULATE (missing data)\n\n")

            # Explain the classification logic
            explanation.append("CLASSIFICATION LOGIC:\n")
            explanation.append("=" * 60 + "\n\n")

            if not (zr and nb and ba and rb and cr and ni):
                explanation.append("❌ Cannot classify - missing required data\n\n")
                explanation.append("Required for classification:\n")
                if not zr: explanation.append("  • Zr (Zirconium)\n")
                if not nb: explanation.append("  • Nb (Niobium)\n")
                if not ba: explanation.append("  • Ba (Barium)\n")
                if not rb: explanation.append("  • Rb (Rubidium)\n")
                if not cr: explanation.append("  • Cr (Chromium)\n")
                if not ni: explanation.append("  • Ni (Nickel)\n")
                return "".join(explanation)

            # Step through the decision tree
            explanation.append("Decision tree:\n\n")

            # Check EGYPTIAN (HADDADIN)
            explanation.append("1. Checking EGYPTIAN (HADDADIN FLOW):\n")
            haddadin_checks = []
            if HADDADIN_ZRNB_MIN <= zr_nb <= HADDADIN_ZRNB_MAX:
                haddadin_checks.append(f"  ✓ Zr/Nb = {zr_nb:.2f} is in range [{HADDADIN_ZRNB_MIN}, {HADDADIN_ZRNB_MAX}]")
            else:
                haddadin_checks.append(f"  ✗ Zr/Nb = {zr_nb:.2f} is NOT in range [{HADDADIN_ZRNB_MIN}, {HADDADIN_ZRNB_MAX}]")

            if HADDADIN_BA_MIN <= ba <= HADDADIN_BA_MAX:
                haddadin_checks.append(f"  ✓ Ba = {ba:.0f} ppm is in range [{HADDADIN_BA_MIN}, {HADDADIN_BA_MAX}]")
            else:
                haddadin_checks.append(f"  ✗ Ba = {ba:.0f} ppm is NOT in range [{HADDADIN_BA_MIN}, {HADDADIN_BA_MAX}]")

            if HADDADIN_CRNI_MIN <= cr_ni <= HADDADIN_CRNI_MAX:
                haddadin_checks.append(f"  ✓ Cr/Ni = {cr_ni:.2f} is in range [{HADDADIN_CRNI_MIN}, {HADDADIN_CRNI_MAX}]")
            else:
                haddadin_checks.append(f"  ✗ Cr/Ni = {cr_ni:.2f} is NOT in range [{HADDADIN_CRNI_MIN}, {HADDADIN_CRNI_MAX}]")

            if wall and wall < 4.0:
                haddadin_checks.append(f"  ✓ Wall thickness = {wall:.1f} mm (< 4.0 mm indicates vessel)")
            elif wall:
                haddadin_checks.append(f"  ✗ Wall thickness = {wall:.1f} mm (≥ 4.0 mm suggests bowl/tool)")

            explanation.extend([c + "\n" for c in haddadin_checks])

            passed_haddadin = all("✓" in c for c in haddadin_checks[:3])  # First 3 are required
            if passed_haddadin:
                explanation.append(f"\n  → MATCH: This sample fits EGYPTIAN (HADDADIN FLOW)\n\n")
            else:
                explanation.append(f"\n  → No match, checking next...\n\n")

            # Check SINAI OPHIOLITIC
            if not passed_haddadin:
                explanation.append("2. Checking SINAI OPHIOLITIC:\n")
                if zr_nb >= OPHIOLITIC_ZRNB_MIN:
                    explanation.append(f"  ✓ Zr/Nb = {zr_nb:.2f} ≥ {OPHIOLITIC_ZRNB_MIN}\n")
                else:
                    explanation.append(f"  ✗ Zr/Nb = {zr_nb:.2f} < {OPHIOLITIC_ZRNB_MIN}\n")

                if OPHIOLITIC_CRNI_MIN <= cr_ni <= OPHIOLITIC_CRNI_MAX:
                    explanation.append(f"  ✓ Cr/Ni = {cr_ni:.2f} in range [{OPHIOLITIC_CRNI_MIN}, {OPHIOLITIC_CRNI_MAX}]\n")
                else:
                    explanation.append(f"  ✗ Cr/Ni = {cr_ni:.2f} NOT in range [{OPHIOLITIC_CRNI_MIN}, {OPHIOLITIC_CRNI_MAX}]\n")

                if ba <= OPHIOLITIC_BA_MAX:
                    explanation.append(f"  ✓ Ba = {ba:.0f} ppm ≤ {OPHIOLITIC_BA_MAX}\n")
                else:
                    explanation.append(f"  ✗ Ba = {ba:.0f} ppm > {OPHIOLITIC_BA_MAX}\n")

                if (zr_nb >= OPHIOLITIC_ZRNB_MIN and
                    OPHIOLITIC_CRNI_MIN <= cr_ni <= OPHIOLITIC_CRNI_MAX and
                    ba <= OPHIOLITIC_BA_MAX):
                    explanation.append(f"\n  → MATCH: SINAI OPHIOLITIC\n\n")
                else:
                    explanation.append(f"\n  → No match, checking next...\n\n")

            # Add more classification branches as needed...
            explanation.append("\nNOTE: This shows the main decision branches.\n")
            explanation.append("The actual classification considers all criteria systematically.\n\n")

            # Add ratio interpretation guide
            explanation.append("RATIO INTERPRETATION GUIDE:\n")
            explanation.append("=" * 60 + "\n\n")

            if zr_nb:
                explanation.append(f"Zr/Nb = {zr_nb:.2f}\n")
                if zr_nb < 5:
                    explanation.append("  → Very low - unusual, check measurements\n")
                elif zr_nb < 10:
                    explanation.append("  → Low - enriched mantle source\n")
                    explanation.append("  → Typical of some Egyptian/alkaline basalts\n")
                elif zr_nb < 20:
                    explanation.append("  → Moderate - transitional mantle signature\n")
                    explanation.append("  → Could be Levantine or mixed sources\n")
                elif zr_nb < 30:
                    explanation.append("  → High - depleted mantle/oceanic signature\n")
                    explanation.append("  → Typical of ophiolitic basalts\n")
                else:
                    explanation.append("  → Very high - strongly depleted source\n")
                    explanation.append("  → Check for alteration or mixing\n")
                explanation.append("\n")

            if cr_ni:
                explanation.append(f"Cr/Ni = {cr_ni:.2f}\n")
                if cr_ni < 0.5:
                    explanation.append("  → Very low - fractionated/evolved\n")
                elif cr_ni < 1.5:
                    explanation.append("  → Low-moderate - typical basaltic composition\n")
                elif cr_ni < 3.0:
                    explanation.append("  → High - mantle-derived signature\n")
                    explanation.append("  → Consistent with ophiolitic sources\n")
                else:
                    explanation.append("  → Very high - primitive/ultramafic\n")
                explanation.append("\n")

            if ba_rb:
                explanation.append(f"Ba/Rb = {ba_rb:.2f}\n")
                if ba_rb < 5:
                    explanation.append("  → Very low - unusual, check for weathering\n")
                elif ba_rb < 15:
                    explanation.append("  → Low-moderate - typical range\n")
                elif ba_rb < 50:
                    explanation.append("  → Moderate-high - enriched source\n")
                else:
                    explanation.append("  → Very high - possible Rb loss during alteration\n")
                explanation.append("\n")

            explanation.append("WHAT THIS MEANS:\n")
            explanation.append("-" * 60 + "\n")
            if classification == "EGYPTIAN (HADDADIN FLOW)":
                explanation.append("This basalt likely comes from Egypt's Haddadin flow.\n")
                explanation.append("• Moderate Zr/Nb indicates specific mantle source\n")
                explanation.append("• Ba content typical of this flow\n")
                explanation.append("• Cr/Ni ratio consistent with known samples\n")
            elif classification == "SINAI OPHIOLITIC":
                explanation.append("This basalt has ophiolitic signatures from Sinai.\n")
                explanation.append("• High Zr/Nb typical of oceanic crust\n")
                explanation.append("• High Cr/Ni indicates mantle origin\n")
                explanation.append("• Low Ba consistent with depleted source\n")
            elif classification == "LOCAL LEVANTINE":
                explanation.append("This basalt is likely from local Levantine sources.\n")
                explanation.append("• Geochemistry doesn't match Egyptian/Sinai\n")
                explanation.append("• Consistent with regional basalt flows\n")

            return "".join(explanation)

        except Exception as e:
            return f"Error generating explanation: {str(e)}"

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row_num, column=0, columnspan=2, pady=20)
        ttk.Button(button_frame, text="Save Changes", command=save_changes).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="💡 Explain Classification", command=explain_classification).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete Sample", command=delete_sample).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=edit_win.destroy).pack(side=tk.LEFT, padx=5)

    def save_project(self):
        """Save entire project (samples + settings) to JSON"""
        path = filedialog.asksaveasfilename(
            defaultextension=".bpt",
            filetypes=[("Basalt Project", "*.bpt"), ("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Project"
        )
        if not path:
            return

        try:
            project_data = {
                "version": "9.2",
                "samples": self.samples,
                "parameters": {
                    "HADDADIN_ZRNB_MIN": HADDADIN_ZRNB_MIN,
                    "HADDADIN_ZRNB_MAX": HADDADIN_ZRNB_MAX,
                    "HADDADIN_BA_MIN": HADDADIN_BA_MIN,
                    "HADDADIN_BA_MAX": HADDADIN_BA_MAX,
                    "HADDADIN_CRNI_MIN": HADDADIN_CRNI_MIN,
                    "HADDADIN_CRNI_MAX": HADDADIN_CRNI_MAX,
                    "ALKALINE_ZRNB_THRESHOLD": ALKALINE_ZRNB_THRESHOLD,
                    "ALKALINE_BA_THRESHOLD": ALKALINE_BA_THRESHOLD,
                    "SINAI_ZRNB_MIN": SINAI_ZRNB_MIN,
                    "SINAI_ZRNB_MAX": SINAI_ZRNB_MAX,
                    "OPHIOLITIC_ZRNB_MIN": OPHIOLITIC_ZRNB_MIN,
                    "OPHIOLITIC_CRNI_MIN": OPHIOLITIC_CRNI_MIN,
                    "OPHIOLITIC_CRNI_MAX": OPHIOLITIC_CRNI_MAX,
                    "OPHIOLITIC_BA_MAX": OPHIOLITIC_BA_MAX,
                    "OPHIOLITIC_RB_MAX": OPHIOLITIC_RB_MAX,
                    "LEVANTINE_CRNI_THRESHOLD": LEVANTINE_CRNI_THRESHOLD,
                    "THIN_WALL_THRESHOLD_MM": THIN_WALL_THRESHOLD_MM,
                    "THICK_WALL_THRESHOLD_MM": THICK_WALL_THRESHOLD_MM,
                }
            }

            with open(path, 'w') as f:
                json.dump(project_data, f, indent=2)

            self.current_project_path = path  # Track for autosave
            self.unsaved_changes = False  # Clear unsaved flag
            self._add_recent_file(path)
            messagebox.showinfo("Success", f"Project saved to:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save project:\n{str(e)}")

    def load_project(self):
        """Load project from JSON file"""
        path = filedialog.askopenfilename(
            filetypes=[("Basalt Project", "*.bpt"), ("JSON files", "*.json"), ("All files", "*.*")],
            title="Load Project"
        )
        if not path:
            return

        try:
            with open(path, 'r') as f:
                project_data = json.load(f)

            # Load samples
            self.samples = project_data.get("samples", [])

            # Load parameters if present
            if "parameters" in project_data:
                params = project_data["parameters"]
                # Update global parameters
                global HADDADIN_ZRNB_MIN, HADDADIN_ZRNB_MAX, HADDADIN_BA_MIN, HADDADIN_BA_MAX
                global HADDADIN_CRNI_MIN, HADDADIN_CRNI_MAX, ALKALINE_ZRNB_THRESHOLD
                global ALKALINE_BA_THRESHOLD, SINAI_ZRNB_MIN, SINAI_ZRNB_MAX
                global OPHIOLITIC_ZRNB_MIN, OPHIOLITIC_CRNI_MIN, OPHIOLITIC_CRNI_MAX
                global OPHIOLITIC_BA_MAX, OPHIOLITIC_RB_MAX, LEVANTINE_CRNI_THRESHOLD
                global THIN_WALL_THRESHOLD_MM, THICK_WALL_THRESHOLD_MM

                for key, value in params.items():
                    globals()[key] = value

            self.current_project_path = path  # Track for autosave
            self.unsaved_changes = False  # Clear unsaved flag
            self._add_recent_file(path)
            self._clear_filter()
            self._update_status(f"Loaded {len(self.samples)} samples from project")
            messagebox.showinfo("Success", f"Project loaded:\n{len(self.samples)} samples")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load project:\n{str(e)}")

    def _load_recent_files(self):
        """Load recent files list from config"""
        try:
            if os.path.exists("recent_files.json"):
                with open("recent_files.json", 'r') as f:
                    self.recent_files = json.load(f)
        except:
            self.recent_files = []

    def _save_recent_files(self):
        """Save recent files list to config"""
        try:
            with open("recent_files.json", 'w') as f:
                json.dump(self.recent_files, f)
        except:
            pass

    def _add_recent_file(self, path):
        """Add a file to recent files list"""
        if path in self.recent_files:
            self.recent_files.remove(path)
        self.recent_files.insert(0, path)
        self.recent_files = self.recent_files[:self.max_recent]
        self._save_recent_files()
        self._update_recent_menu()

    def _update_recent_menu(self):
        """Update the Recent Files menu"""
        self.recent_menu.delete(0, tk.END)

        if not self.recent_files:
            self.recent_menu.add_command(label="(No recent files)", state="disabled")
        else:
            for i, path in enumerate(self.recent_files):
                if os.path.exists(path):
                    filename = os.path.basename(path)
                    self.recent_menu.add_command(
                        label=f"{i+1}. {filename}",
                        command=lambda p=path: self._open_recent_file(p)
                    )

    def _open_recent_file(self, path):
        """Open a recent file"""
        if path.endswith(('.bpt', '.json')):
            # It's a project file
            try:
                with open(path, 'r') as f:
                    project_data = json.load(f)
                raw = project_data.get("samples", [])
                # Hard validation: keep only dicts, log the rest
                cleaned = []
                for i, row in enumerate(raw):
                    if isinstance(row, dict):
                        cleaned.append(row)
                    else:
                        print(f"[CORRUPTED ROW REMOVED] index={i}, type={type(row)}, value={row}")
                self.samples = cleaned

                self._clear_filter()
                self._update_status(f"Loaded {len(self.samples)} samples (corrupted rows removed)")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to load:\n{str(e)}")

        else:
            messagebox.showinfo("Info", "Please use Import pXRF for data files")

    # ═══════════════════════════════════
    # ENHANCED METHODS (v9.0)
    # ═══════════════════════════════════

    def _update_status(self, message):
        """Update status bar"""
        if hasattr(self, 'status_var'):
            self.status_var.set(message)
        self.root.update_idletasks()

    def _play_sound(self):
        """Play a sound effect"""
        if not hasattr(self, 'sound_enabled'):
            return
        if self.sound_enabled:
            try:
                self.root.bell()
            except:
                pass

    def _apply_theme(self):
        """Apply current theme"""
        theme = THEMES.get(self.current_theme, THEMES["Light"])
        # Update COLOR_MAP if it exists, or update SCATTER_COLORS directly
        for cls, color in theme.get("colors", {}).items():
            SCATTER_COLORS[cls] = color

        self._apply_filter()  # Refresh the display with new colors
        self._update_status(f"Theme applied: {self.current_theme}")

    # REMOVED DUPLICATE _on_closing METHOD
    def show_license_usage(self):
        """Show friendly License & Usage dialog with dynamic sizing"""
        dialog = tk.Toplevel(self.root)
        dialog.title("License & Usage")

        # Main container with padding
        main_frame = ttk.Frame(dialog, padding=25)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Scrollable text area
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        text_widget = tk.Text(text_frame, wrap="word", font=("TkDefaultFont", 10))
        scrollbar = ttk.Scrollbar(text_frame, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)

        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # The license text
        license_text = """## License & Usage

**Basalt Provenance Triage Toolkit** is released under the
**Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)** license.

### You are free to:
- Use the software for research, education, archaeological fieldwork, museum cataloguing, teaching, or any non-commercial purpose
- Modify the code for your own non-commercial projects
- Share copies or modified versions (with proper attribution and under the same license)

### Especially encouraged:
Academic researchers, university groups, museums, heritage organizations, non-profit institutions, PhD students, independent scholars, and archaeological field projects are warmly invited and encouraged to use, adapt, and build upon this tool — free of charge and with my full support.

If this toolkit helps you triage basalt samples, prepare a publication, teach a course, document a collection, or support cultural heritage work, that is exactly why it exists.

### You must:
- Give appropriate credit to the original author (Sefy Levy)
- Provide a link to the license
- Indicate if changes were made
- Release any derivative works under the same CC BY-NC-SA 4.0 license

### You may not:
- Use the software (or any substantial part of it) for commercial purposes
- Sell it, offer it as part of a paid service, integrate it into commercial software/products, or charge money for access to it
- Apply for patents on this software, its methodology, or substantially similar implementations

Commercial use of any kind requires explicit written permission from the author (sefy76@gmail.com).
I am generally open to discussing academic–industry collaborations or licensed commercial applications — just reach out.

Full license text: https://creativecommons.org/licenses/by-nc-sa/4.0/

Thank you for respecting these terms — and thank you for using and supporting open tools in archaeology and cultural heritage.
"""

        text_widget.insert("1.0", license_text)
        text_widget.config(state="disabled")

        # Close button
        ttk.Button(main_frame, text="Close", command=dialog.destroy).pack(pady=15)

        # Dynamic sizing
        dialog.update_idletasks()

        req_width = main_frame.winfo_reqwidth() + 60
        req_height = main_frame.winfo_reqheight() + 80

        width = min(max(req_width, 500), 900)
        height = min(max(req_height, 400), 800)

        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)

        dialog.geometry(f"{width}x{height}+{x}+{y}")
    def show_disclaimer(self):
        """Show important disclaimer (v9.1)"""
        dialog = tk.Toplevel(self.root)
        dialog.title("⚠️ Important Disclaimer")
        dialog.geometry("650x450")
        dialog.transient(self.root)

        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (650 // 2)
        y = (dialog.winfo_screenheight() // 2) - (450 // 2)
        dialog.geometry(f"650x450+{x}+{y}")

        # Warning icon and title
        title_frame = ttk.Frame(dialog)
        title_frame.pack(pady=20)

        ttk.Label(
            title_frame,
            text="⚠️",
            font=("Arial", 48)
        ).pack()

        ttk.Label(
            title_frame,
            text="IMPORTANT DISCLAIMER",
            font=("Arial", 16, "bold")
        ).pack(pady=10)

        # Disclaimer text
        text_frame = ttk.Frame(dialog)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)

        disclaimer_text = """This software is intended for RESEARCH and EDUCATIONAL use only.

Key Points:

• Automated classifications are based on published geochemical
  thresholds and established archaeological research.

• Results MUST be verified by qualified specialists before being
  used in formal archaeological or geological conclusions.

• All classifications should be validated against published
  reference data and expert interpretation.

• This tool is designed to assist researchers in triaging samples,
  not to replace expert analysis.

• The developer(s) assume no responsibility for conclusions
  drawn from automated classifications without proper expert
  validation.

Scientific Basis:
Based on research by Hartung (2017), Philip & Williams-Thorpe (2001),
Williams-Thorpe & Thorpe (1993), and Rosenberg et al. (2016).

By using this software, you acknowledge that you understand these
limitations and will use the results appropriately.
"""

        text_widget = tk.Text(
            text_frame,
            wrap=tk.WORD,
            font=("Arial", 10),
            height=15,
            bg="#fff9e6",
            relief=tk.SOLID,
            borderwidth=2
        )
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert("1.0", disclaimer_text)
        text_widget.config(state=tk.DISABLED)

        # OK button
        bottom_frame = ttk.Frame(dialog)
        bottom_frame.pack(pady=20)

        ttk.Button(
            bottom_frame,
            text="OK",
            command=dialog.destroy,
            width=15
        ).pack(pady=5)

        dialog.lift()
        dialog.focus_force()

    def _show_tutorial(self):
        """Show interactive tutorial"""
        tutorial_steps = [
            {
                "title": "Welcome to Basalt Provenance Triage Toolkit",
                "text": "This tutorial will guide you through the main features of the application.\n\nClick 'Next' to continue."
            },
            {
                "title": "Step 1: Import Data",
                "text": "Click 'Import pXRF' to load your sample data.\n\nSupported formats: CSV, Excel (XLSX/XLS) with columns for Sample_ID, Wall_Thickness_mm, Zr_ppm, Nb_ppm, Ba_ppm, Rb_ppm, Cr_ppm, Ni_ppm."
            },
            {
                "title": "Step 2: Classify Samples",
                "text": "Click 'Classify All' or press Ctrl+C to automatically classify all samples based on their geochemical signatures.\n\nThe algorithm uses established criteria from published research to determine provenance."
            },
            {
                "title": "Step 3: Review Results",
                "text": "Check the Auto_Classification column to see the results.\n\nGreen background = high confidence\nYellow/Orange = medium confidence\nRed = needs review\n\nYou can double-click any row to edit it manually."
            },
            {
                "title": "Step 4: Filter and Search",
                "text": "Use the filter controls to find specific samples:\n\n• Filter by Sample ID\n• Filter by Classification\n• Filter by Review Flag\n\nPress Enter or click 'Apply Filter' to search."
            },
            {
                "title": "Step 5: Export Results",
                "text": "When you're done:\n\n• Click 'Export pXRF' to save results\n• Click 'Save Project' to save everything including your custom edits\n• Use Ctrl+Shift+C to copy to clipboard for Excel"
            },
            {
                "title": "Advanced Features",
                "text": "Explore more features:\n\n• View → Histogram: See data distribution\n• Tools → Missing Data Report: Find incomplete samples\n• Tools → Outlier Detection: Statistical analysis\n• Right-click on samples: Quick actions menu\n• Select multiple rows + Ctrl+B: Bulk edit"
            },
            {
                "title": "Keyboard Shortcuts",
                "text": "Speed up your workflow:\n\n• Ctrl+I: Import pXRF\n• Ctrl+S: Export pXRF\n• Ctrl+C: Classify All\n• Ctrl+Z/Y: Undo/Redo\n• Ctrl+F: Quick Filter\n• Ctrl+B: Bulk Edit\n• Page Up/Down: Navigate pages"
            },
            {
                "title": "Tutorial Complete!",
                "text": "You're ready to start analyzing basalt samples!\n\nRemember:\n• Auto-save runs every 5 minutes\n• Daily backups are created automatically\n• Hover over buttons for tooltips\n• Check the status bar for helpful tips\n\nGood luck with your research! 🎓"
            }
        ]

        current_step = [0]

        dialog = tk.Toplevel(self.root)
        dialog.title("Interactive Tutorial")
        dialog.geometry("600x400")
        dialog.transient(self.root)

        title_label = ttk.Label(dialog, text="", font=("Arial", 14, "bold"))
        title_label.pack(pady=20)

        text_widget = tk.Text(dialog, wrap=tk.WORD, font=("Arial", 11), height=12)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)

        prev_btn = ttk.Button(button_frame, text="◀ Previous", state=tk.DISABLED)
        prev_btn.pack(side=tk.LEFT, padx=5)

        next_btn = ttk.Button(button_frame, text="Next ▶")
        next_btn.pack(side=tk.LEFT, padx=5)

        close_btn = ttk.Button(button_frame, text="Close", command=dialog.destroy)
        close_btn.pack(side=tk.LEFT, padx=5)

        progress_label = ttk.Label(dialog, text="")
        progress_label.pack(pady=5)

        def show_step():
            step = tutorial_steps[current_step[0]]
            title_label.config(text=step["title"])
            text_widget.delete("1.0", tk.END)
            text_widget.insert("1.0", step["text"])
            text_widget.config(state=tk.DISABLED)

            progress_label.config(text=f"Step {current_step[0] + 1} of {len(tutorial_steps)}")

            prev_btn.config(state=tk.NORMAL if current_step[0] > 0 else tk.DISABLED)
            next_btn.config(
                text="Finish ✓" if current_step[0] == len(tutorial_steps) - 1 else "Next ▶"
            )

        def next_step():
            if current_step[0] < len(tutorial_steps) - 1:
                current_step[0] += 1
                show_step()
            else:
                dialog.destroy()

        def prev_step():
            if current_step[0] > 0:
                current_step[0] -= 1
                show_step()

        prev_btn.config(command=prev_step)
        next_btn.config(command=next_step)

        show_step()

    # ════════════════════════════════════════════════════════════════════
    # NEW v9.2 FEATURES
    # ════════════════════════════════════════════════════════════════════

    def _check_crash_recovery(self):
        """Check if there's a recovery file from a crash"""
        if os.path.exists(self.recovery_file):
            try:
                response = messagebox.askyesno(
                    "Crash Recovery",
                    "It looks like the application didn't close properly last time.\n\n"
                    "Would you like to recover your unsaved work?"
                )
                if response:
                    with open(self.recovery_file, 'r') as f:
                        data = json.load(f)
                        self.samples = data.get('samples', [])
                        messagebox.showinfo("Recovery", f"Recovered {len(self.samples)} samples.")

                # Delete recovery file after attempting recovery
                os.remove(self.recovery_file)
            except Exception as e:
                messagebox.showerror("Recovery Error", f"Could not recover data:\n{str(e)}")
                try:
                    os.remove(self.recovery_file)
                except:
                    pass

    def _save_recovery_file(self):
        """Save current state to recovery file"""
        try:
            if self.samples:  # Only save if there's data
                with open(self.recovery_file, 'w') as f:
                    json.dump({'samples': self.samples}, f)
        except Exception as e:
            print(f"Recovery file save failed: {e}")

    def _schedule_autosave(self):
        """Schedule periodic autosave (poll every 30 seconds)"""
        if self.auto_save_enabled:
            current_time = time.time()
            if current_time - self.last_save_time > (self.auto_save_interval * 60):
                self._perform_autosave()
                self.last_save_time = current_time
        self.root.after(30000, self._schedule_autosave)

    def _perform_autosave(self):
        """Perform autosave operation"""
        if self.unsaved_changes and self.samples:
            # Save recovery file
            self._save_recovery_file()

            # If there's a current project, auto-save to it
            if self.current_project_path:
                try:
                    with open(self.current_project_path, 'w') as f:
                        json.dump(self.samples, f, indent=2)
                    self._update_status(f"Auto-saved to {os.path.basename(self.current_project_path)}")
                except Exception as e:
                    print(f"Autosave failed: {e}")

    def _on_closing(self):
        """Handle clean application exit"""
        if self.unsaved_changes:
            response = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before exiting?"
            )
            if response is None:  # Cancel
                return
            elif response:  # Yes
                self.save_project()

        # Delete recovery file on clean exit
        try:
            if os.path.exists(self.recovery_file):
                os.remove(self.recovery_file)
        except:
            pass

        self.root.destroy()

    def _mark_unsaved_changes(self):
        """Mark that there are unsaved changes"""
        self.unsaved_changes = True
        self._save_recovery_file()  # Save to recovery file immediately

    def _show_context_menu(self, event):
        """Show right-click context menu on table rows"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)

            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label="Edit Sample", command=lambda: self._on_row_double_click(None))   # FIXED
            menu.add_command(label="Duplicate Sample", command=self.duplicate_selected)
            menu.add_command(label="Delete Sample", command=self._delete_selected)
            menu.add_separator()
            menu.add_command(label="Classify This Row", command=self._classify_selected)
            menu.add_command(label="Flag for Review", command=self._flag_selected)
            menu.add_separator()
            menu.add_command(label="Copy Sample ID", command=self._copy_sample_id)

            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()

    def _delete_selected(self):
        """Delete the single currently selected sample (right‑click)."""
        selection = self.tree.selection()
        if not selection:
            return

        # The tree item ID is the row index (as string) – thanks to iid=str(row_idx)
        try:
            row_idx = int(selection[0])
        except ValueError:
            messagebox.showerror("Error", "Cannot identify row index.")
            return

        if not (0 <= row_idx < len(self.samples)):
            return

        sample_id = self.samples[row_idx].get("Sample_ID", f"Row {row_idx}")
        if not messagebox.askyesno("Confirm Delete", f"Delete sample {sample_id}?"):
            return

        self._delete_samples_by_indices([row_idx])
    def _delete_samples_by_indices(self, indices_to_delete):
        """
        Delete samples by their position in self.samples and refresh the UI.
        indices_to_delete : iterable of integers (row indices)
        """
        if not indices_to_delete:
            return

        self._save_undo()

        # Delete from highest index to lowest to avoid shifting
        for idx in sorted(set(indices_to_delete), reverse=True):
            if 0 <= idx < len(self.samples):
                del self.samples[idx]

        # Clear all selection states
        self.selected_rows.clear()
        self._refresh_table_page()

        if hasattr(self, 'hud_tree'):
            self._update_hud_results(None)

        self._mark_unsaved_changes()
        self._update_selection_count()

    def _classify_selected(self):
        """Classify only the selected row(s) using the dynamic classification engine."""
        selection = self.tree.selection()
        if not selection:
            return

        # --- Ensure we have a classification engine ---
        if not hasattr(self, 'engine'):
            from classification_engine import ClassificationEngine
            self.engine = ClassificationEngine()

        # Use the currently active scheme, or fall back to regional_triage
        scheme_id = getattr(self, 'active_scheme_id', 'regional_triage')

        for item in selection:
            values = self.tree.item(item, "values")
            # Column order: [checkbox, Sample_ID, ...] → Sample_ID is at index 1
            sample_id = values[1] if len(values) > 1 else None

            for sample in self.samples:
                if sample.get("Sample_ID") == sample_id:
                    # ------------------------------------------------------------
                    # 1. CLASSIFY using the engine
                    # ------------------------------------------------------------
                    classification, confidence, color = self.engine.classify_sample(sample, scheme_id)

                    # ------------------------------------------------------------
                    # 2. COMPUTE Ba/Rb ratio (engine does not compute it)
                    # ------------------------------------------------------------
                    ba = safe_float(sample.get("Ba_ppm"))
                    rb = safe_float(sample.get("Rb_ppm"))
                    ba_rb = None
                    if ba is not None and rb is not None and rb != 0:
                        ba_rb = ba / rb

                    # ------------------------------------------------------------
                    # 3. RETRIEVE ratios already stored by the engine
                    # ------------------------------------------------------------
                    zr_nb = sample.get("Zr_Nb_Ratio")
                    cr_ni = sample.get("Cr_Ni_Ratio")

                    # ------------------------------------------------------------
                    # 4. UPDATE the sample dictionary
                    # ------------------------------------------------------------
                    sample["Zr_Nb_Ratio"] = f"{zr_nb:.3f}" if isinstance(zr_nb, (int, float)) else ""
                    sample["Cr_Ni_Ratio"] = f"{cr_ni:.3f}" if isinstance(cr_ni, (int, float)) else ""
                    sample["Ba_Rb_Ratio"] = f"{ba_rb:.3f}" if ba_rb is not None else ""

                    sample["Auto_Classification"] = classification
                    sample["Auto_Confidence"] = confidence
                    sample["Flag_For_Review"] = "YES" if classification == "REVIEW REQUIRED" else "NO"

                    # ------------------------------------------------------------
                    # 5. SYNCHRONISE all classification keys (fix for Issue #5)
                    # ------------------------------------------------------------
                    sync_classification_keys(sample, classification)

                    break   # sample found, stop inner loop

        # ------------------------------------------------------------
        # 6. REFRESH UI
        # ------------------------------------------------------------
        self._refresh_table_page()
        self._mark_unsaved_changes()
        self._update_status("Selected sample(s) classified")

    def _flag_selected(self):
        """Toggle flag for review on selected sample(s)"""
        selection = self.tree.selection()
        if not selection:
            return

        for item in selection:
            values = self.tree.item(item, "values")
            sample_id = values[1]

            for sample in self.samples:
                if sample.get("Sample_ID") == sample_id:
                    current_flag = sample.get("Flag_For_Review", "")
                    sample["Flag_For_Review"] = "" if current_flag else "YES"
                    break

        self._refresh_table_page()
        self._mark_unsaved_changes()
        self._update_status("Flag toggled")

    def _copy_sample_id(self):
        """Copy sample ID to clipboard"""
        selection = self.tree.selection()
        if selection:
            values = self.tree.item(selection[0], "values")
            sample_id = values[1]  # Index 1 because checkbox is at 0
            self.root.clipboard_clear()
            self.root.clipboard_append(sample_id)
            self._update_status(f"Copied: {sample_id}")

    # ────────────────────────────────────────────────
    # Checkbox Selection Methods
    # ────────────────────────────────────────────────
    def _on_table_click(self, event):
        """Handle left‑click: toggle checkbox on column #1, always allow default selection."""
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            item = self.tree.identify_row(event.y)
            # If it's the checkbox column, toggle the checkbox
            if column == "#1" and item:
                self._toggle_row_selection(item)
                # DO NOT return "break" – let the default selection happen

    def _toggle_row_selection(self, item_id):
        """Toggle checkbox symbol in the tree WITHOUT refreshing the whole table."""
        try:
            row_idx = int(item_id)
            # Toggle the set
            if row_idx in self.selected_rows:
                self.selected_rows.remove(row_idx)
                checkbox = "☐"
            else:
                self.selected_rows.add(row_idx)
                checkbox = "☑"

            # Update only the first column's value for this item
            current_vals = list(self.tree.item(item_id, "values"))
            if current_vals:
                current_vals[0] = checkbox          # first column is the checkbox symbol
                self.tree.item(item_id, values=tuple(current_vals))

            self._update_selection_count()
        except Exception:
            # If anything fails (e.g., item_id not numeric), do nothing
            pass

    def _select_all_rows(self):
        """Select all rows across ALL pages"""
        display_samples = self.filtered_samples if self.filtered_samples else self.samples

        # Select ALL samples in the displayed set (across all pages)
        for i in range(len(self.samples)):
            row = self.samples[i]
            if row in display_samples:
                self.selected_rows.add(i)

        self._refresh_table_page()
        self._update_selection_count()

        # Show confirmation message
        total = len(self.selected_rows)
        if self.filtered_samples:
            messagebox.showinfo("Select All",
                f"Selected all {total} filtered samples across all pages.")
        else:
            messagebox.showinfo("Select All",
                f"Selected all {total} samples across all pages.")

    def _deselect_all_rows(self):
        """Deselect all rows"""
        self.selected_rows.clear()
        self._refresh_table_page()
        self._update_selection_count()

    def _update_selection_count(self):
        """Update the selection counter label"""
        count = len(self.selected_rows)
        self.selection_label.config(text=f"Selected: {count}")

    def _delete_selected(self):
        selection = self.tree.selection()
        if not selection:
            return
        try:
            row_idx = int(selection[0])
        except ValueError:
            messagebox.showerror("Error", "Cannot identify row index.")
            return
        if not (0 <= row_idx < len(self.samples)):
            return
        sample_id = self.samples[row_idx].get("Sample_ID", f"Row {row_idx}")
        if not messagebox.askyesno("Confirm Delete", f"Delete sample {sample_id}?"):
            return
        self._delete_samples_by_indices([row_idx])

    def _create_validation_table(self, parent, title, data, column_config):
        """
        Unified table builder for validation reports.

        Parameters:
            parent      : parent widget (ttk.Frame)
            title       : string displayed above the table
            data        : list of tuples, each tuple = one row
            column_config: dict {col_id: {'heading': str, 'width': int}}
        """
        # Title label
        ttk.Label(parent, text=title, font=("Arial", 11, "bold")).pack(pady=10)

        # Container frame
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Treeview
        columns = list(column_config.keys())
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings")

        # Configure columns
        for col_id, cfg in column_config.items():
            tree.heading(col_id, text=cfg['heading'])
            tree.column(col_id, width=cfg['width'])

        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        # Insert data
        for row in data:
            tree.insert("", tk.END, values=row)

        # Layout
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        return tree  # (optional – you don't need it now)
    # ────────────────────────────────────────────────

    def _show_validation_report(self):
        """Show comprehensive sample validation report inline"""
        if not self.samples:
            messagebox.showinfo("No Data", "No samples to validate")
            return

        # Switch to report view
        self.notebook.select(self.table_tab)
        self._show_report_view()

        # Clear report view
        for widget in self.report_view.winfo_children():
            widget.destroy()

        # Header
        header = ttk.Frame(self.report_view)
        header.pack(fill=tk.X, pady=(0, 10), padx=10)

        ttk.Button(header, text="← Back to Table",
                  command=self._hide_report_view).pack(side=tk.LEFT)
        ttk.Label(header, text="Sample Validation Report",
                 font=("Arial", 14, "bold")).pack(side=tk.LEFT, padx=20)

        # Create notebook for different validation types
        notebook = ttk.Notebook(self.report_view)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Tab 1: Missing Data
        missing_frame = ttk.Frame(notebook)
        notebook.add(missing_frame, text="Missing Data")
        self._create_missing_data_tab(missing_frame)

        # Tab 2: Out of Range
        range_frame = ttk.Frame(notebook)
        notebook.add(range_frame, text="Out of Range")
        self._create_out_of_range_tab(range_frame)

        # Tab 3: Flagged for Review
        flagged_frame = ttk.Frame(notebook)
        notebook.add(flagged_frame, text="Flagged Samples")
        self._create_flagged_tab(flagged_frame)

    def _create_missing_data_tab(self, parent):
        # --- Data preparation (unchanged) ---
        critical_fields = ["Wall_Thickness_mm", "Zr_ppm", "Nb_ppm", "Ba_ppm", "Cr_ppm", "Ni_ppm"]
        missing_samples = []
        for sample in self.samples:
            missing = []
            for field in critical_fields:
                if not sample.get(field) or safe_float(sample.get(field)) is None:
                    missing.append(field)
            if missing:
                missing_samples.append((sample.get("Sample_ID"), ", ".join(missing)))

        title = f"Samples with missing data: {len(missing_samples)} of {len(self.samples)}"
        column_config = {
            "ID": {"heading": "Sample ID", "width": 150},
            "Missing": {"heading": "Missing Fields", "width": 400}
        }
        self._create_validation_table(parent, title, missing_samples, column_config)

    def _create_out_of_range_tab(self, parent):
        # --- Data preparation (unchanged) ---
        ranges = {
            "Zr_ppm": (0, 500),
            "Nb_ppm": (0, 100),
            "Ba_ppm": (0, 2000),
            "Cr_ppm": (0, 1000),
            "Ni_ppm": (0, 500),
            "Wall_Thickness_mm": (0, 50)
        }
        out_of_range = []
        for sample in self.samples:
            issues = []
            for field, (min_val, max_val) in ranges.items():
                value = safe_float(sample.get(field))
                if value is not None and (value < min_val or value > max_val):
                    issues.append(f"{field}: {value:.1f} (expected {min_val}-{max_val})")
            if issues:
                out_of_range.append((sample.get("Sample_ID"), "; ".join(issues)))

        title = f"Samples with out-of-range values: {len(out_of_range)} of {len(self.samples)}"
        column_config = {
            "ID": {"heading": "Sample ID", "width": 150},
            "Issues": {"heading": "Out of Range Values", "width": 400}
        }
        self._create_validation_table(parent, title, out_of_range, column_config)

    def _create_flagged_tab(self, parent):
        # --- Data preparation (unchanged) ---
        flagged = []
        for s in self.samples:
            if s.get("Flag_For_Review") == "YES":
                flagged.append((
                    s.get("Sample_ID", ""),
                    s.get("Auto_Classification", ""),
                    s.get("Notes", "")
                ))

        title = f"Samples flagged for review: {len(flagged)}"
        column_config = {
            "ID": {"heading": "Sample ID", "width": 150},
            "Classification": {"heading": "Classification", "width": 200},
            "Notes": {"heading": "Notes", "width": 300}
        }
        self._create_validation_table(parent, title, flagged, column_config)

    def _compare_samples(self):
        """Compare two selected samples side-by-side"""
        selection = self.tree.selection()
        if len(selection) != 2:
            messagebox.showinfo("Select Two Samples",
                              "Please select exactly two samples to compare.\n\n"
                              "Hold Ctrl and click to select multiple samples.")
            return

        # Get both samples
        samples = []
        for item in selection:
            values = self.tree.item(item, "values")
            sample_id = values[1]
            for s in self.samples:
                if s.get("Sample_ID") == sample_id:
                    samples.append(s)
                    break

        if len(samples) != 2:
            return

        # Create comparison dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Compare Two Samples")
        dialog.geometry("800x600")

        # Header
        header = ttk.Frame(dialog)
        header.pack(fill=tk.X, pady=10, padx=10)

        ttk.Label(header, text=samples[0].get("Sample_ID", "Sample 1"),
                 font=("Arial", 12, "bold")).pack(side=tk.LEFT, expand=True)
        ttk.Label(header, text="vs", font=("Arial", 10)).pack(side=tk.LEFT, padx=20)
        ttk.Label(header, text=samples[1].get("Sample_ID", "Sample 2"),
                 font=("Arial", 12, "bold")).pack(side=tk.LEFT, expand=True)

        # Create comparison table
        tree_frame = ttk.Frame(dialog)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        tree = ttk.Treeview(tree_frame, columns=("Field", "Sample1", "Sample2", "Diff"), show="headings")
        tree.heading("Field", text="Field")
        tree.heading("Sample1", text=samples[0].get("Sample_ID", "Sample 1"))
        tree.heading("Sample2", text=samples[1].get("Sample_ID", "Sample 2"))
        tree.heading("Diff", text="Difference")

        tree.column("Field", width=150)
        tree.column("Sample1", width=150)
        tree.column("Sample2", width=150)
        tree.column("Diff", width=150)

        scrollbar = ttk.Scrollbar(tree_frame, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        # Compare fields
        compare_fields = [
            "Wall_Thickness_mm", "Zr_ppm", "Nb_ppm", "Ba_ppm", "Rb_ppm",
            "Cr_ppm", "Ni_ppm", "Zr_Nb_Ratio", "Cr_Ni_Ratio", "Ba_Rb_Ratio",
            "Auto_Classification", "Auto_Confidence"
        ]

        for field in compare_fields:
            val1 = samples[0].get(field, "")
            val2 = samples[1].get(field, "")

            # Calculate difference for numeric fields
            diff = ""
            num1 = safe_float(val1)
            num2 = safe_float(val2)
            if num1 is not None and num2 is not None:
                difference = num2 - num1
                diff = f"{difference:+.2f}"
            elif val1 != val2:
                diff = "Different"

            tree.insert("", tk.END, values=(field, val1, val2, diff))

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Close button
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)

    def _show_threshold_table(self):
        """Show threshold visualization table inline in the table area"""
        # Switch to the Data Table tab first
        self.notebook.select(self.table_tab)

        # Switch to report view
        self._show_report_view()

        # Clear any existing content in report view
        for widget in self.report_view.winfo_children():
            widget.destroy()

        # Create header with back button
        header = ttk.Frame(self.report_view)
        header.pack(fill=tk.X, pady=(0, 10), padx=10)

        ttk.Button(header, text="← Back to Table", command=self._hide_report_view,
                  style="Accent.TButton").pack(side=tk.LEFT)
        ttk.Label(header, text="Classification Threshold Reference",
                 font=("Arial", 14, "bold")).pack(side=tk.LEFT, padx=20)

        # Create text widget with thresholds
        text_frame = ttk.Frame(self.report_view)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        text = tk.Text(text_frame, wrap="word", font=("Courier", 10), padx=10, pady=10)
        scrollbar = ttk.Scrollbar(text_frame, command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)

        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Add threshold information
        text.insert("end", "CLASSIFICATION THRESHOLDS\n")
        text.insert("end", "═" * 80 + "\n\n")

        text.insert("end", "EGYPTIAN (HADDADIN FLOW)\n")
        text.insert("end", "─" * 80 + "\n")
        text.insert("end", f"  Zr/Nb Ratio:      {HADDADIN_ZRNB_MIN:.2f} - {HADDADIN_ZRNB_MAX:.2f}\n")
        text.insert("end", f"  Ba (ppm):         {HADDADIN_BA_MIN:.0f} - {HADDADIN_BA_MAX:.0f}\n")
        text.insert("end", f"  Cr/Ni Ratio:      {HADDADIN_CRNI_MIN:.2f} - {HADDADIN_CRNI_MAX:.2f}\n")
        text.insert("end", f"  Wall Thickness:   < {THIN_WALL_THRESHOLD_MM:.1f} mm\n\n")

        text.insert("end", "EGYPTIAN (ALKALINE / EXOTIC)\n")
        text.insert("end", "─" * 80 + "\n")
        text.insert("end", f"  Zr/Nb Ratio:      < {ALKALINE_ZRNB_THRESHOLD:.2f}\n")
        text.insert("end", f"  Ba (ppm):         > {ALKALINE_BA_THRESHOLD:.0f}\n")
        text.insert("end", f"  Wall Thickness:   < {THIN_WALL_THRESHOLD_MM:.1f} mm\n\n")

        text.insert("end", "SINAI OPHIOLITIC\n")
        text.insert("end", "─" * 80 + "\n")
        text.insert("end", f"  Zr/Nb Ratio:      {OPHIOLITIC_ZRNB_MIN:.2f} - {float('inf')}\n")
        text.insert("end", f"  Cr/Ni Ratio:      {OPHIOLITIC_CRNI_MIN:.2f} - {OPHIOLITIC_CRNI_MAX:.2f}\n")
        text.insert("end", f"  Ba (ppm):         < {OPHIOLITIC_BA_MAX:.0f}\n")
        text.insert("end", f"  Rb (ppm):         < {OPHIOLITIC_RB_MAX:.0f}\n")
        text.insert("end", f"  Wall Thickness:   > {THICK_WALL_THRESHOLD_MM:.1f} mm\n\n")

        text.insert("end", "SINAI / TRANSITIONAL\n")
        text.insert("end", "─" * 80 + "\n")
        text.insert("end", f"  Zr/Nb Ratio:      {SINAI_ZRNB_MIN:.2f} - {SINAI_ZRNB_MAX:.2f}\n")
        text.insert("end", f"  Wall Thickness:   > {THICK_WALL_THRESHOLD_MM:.1f} mm\n\n")

        text.insert("end", "LOCAL LEVANTINE\n")
        text.insert("end", "─" * 80 + "\n")
        text.insert("end", f"  Cr/Ni Ratio:      > {LEVANTINE_CRNI_THRESHOLD:.2f}\n")
        text.insert("end", f"  Wall Thickness:   > {THICK_WALL_THRESHOLD_MM:.1f} mm\n\n")

        text.config(state="disabled")

    def _export_classification_summary(self):
        """Export classification summary to text file"""
        if not self.samples:
            messagebox.showinfo("No Data", "No samples to summarize")
            return

        path = filedialog.asksaveasfilename(
            title="Export Classification Summary",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )

        if not path:
            return

        try:
            with open(path, 'w') as f:
                f.write("BASALT PROVENANCE CLASSIFICATION SUMMARY\n")
                f.write("=" * 70 + "\n\n")
                f.write(f"Total Samples: {len(self.samples)}\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                # Count by classification
                from collections import Counter
                classifications = [s.get("Final_Classification") or s.get("Auto_Classification", "UNKNOWN")
                                 for s in self.samples]
                counts = Counter(classifications)

                f.write("CLASSIFICATION BREAKDOWN\n")
                f.write("-" * 70 + "\n")
                for cls, count in sorted(counts.items()):
                    pct = (count / len(self.samples)) * 100
                    f.write(f"{cls:40s}: {count:4d} ({pct:5.1f}%)\n")

                f.write("\n")

                # Flagged samples
                flagged = [s for s in self.samples if s.get("Flag_For_Review") == "YES"]
                f.write(f"Flagged for Review: {len(flagged)}\n\n")

                # Average ratios
                zr_nb_values = [safe_float(s.get("Zr_Nb_Ratio")) for s in self.samples]
                zr_nb_values = [v for v in zr_nb_values if v is not None]

                cr_ni_values = [safe_float(s.get("Cr_Ni_Ratio")) for s in self.samples]
                cr_ni_values = [v for v in cr_ni_values if v is not None]

                if zr_nb_values:
                    f.write(f"Average Zr/Nb Ratio: {statistics.mean(zr_nb_values):.2f}\n")
                if cr_ni_values:
                    f.write(f"Average Cr/Ni Ratio: {statistics.mean(cr_ni_values):.2f}\n")

            messagebox.showinfo("Success", f"Summary exported to:\n{path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export:\n{str(e)}")

    def _show_geological_context(self):
        """Show geological context guide for each basalt province"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Geological Context Guide")
        dialog.geometry("900x700")

        ttk.Label(dialog, text="Regional Basalt Provinces - Geological Context",
                 font=("Arial", 14, "bold")).pack(pady=10)

        # Create notebook for different regions
        notebook = ttk.Notebook(dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Define geological contexts
        contexts = {
            "Egyptian (Haddadin)": {
                "title": "Egyptian Basalts - Haddadin Flow",
                "location": "Northern Egypt, Nile Delta region",
                "age": "Oligocene (~30 Ma)",
                "tectonic": "Continental flood basalt, associated with rifting",
                "chemistry": """
Characteristic Geochemistry:
• Zr/Nb: 4.5-6.5 (tholeiitic affinity)
• Ba: 200-600 ppm (moderate incompatible element enrichment)
• Cr/Ni: 1.8-2.8 (moderate fractionation)
• Wall thickness: Typically <8 mm (thin-walled vessels)

Petrogenesis:
Derived from depleted to slightly enriched mantle sources.
Lower degrees of partial melting compared to ophiolitic basalts.
Shows continental flood basalt characteristics.

Archaeological Significance:
Major source for Egyptian basalt vessels exported throughout
the Levant during Bronze Age. Diagnostic thin-wall vessels.
                """,
                "references": "Hartung (2017), Philip & Williams-Thorpe (2001)"
            },
            "Egyptian (Alkaline)": {
                "title": "Egyptian Basalts - Alkaline / Exotic",
                "location": "Various Egyptian provinces",
                "age": "Oligocene to Recent",
                "tectonic": "Alkaline volcanism, often associated with rifting",
                "chemistry": """
Characteristic Geochemistry:
• Zr/Nb: <4.5 (alkaline affinity)
• Ba: >600 ppm (high incompatible element enrichment)
• Generally OIB-like signatures

Petrogenesis:
Low degree partial melts from enriched mantle sources.
Strong alkaline affinity. May include phonolitic compositions.
Represents more exotic Egyptian sources.

Archaeological Significance:
Less common in archaeological assemblages. When present,
indicates specialized trade networks or specific quarry sites.
                """,
                "references": "Geological Survey of Israel"
            },
            "Sinai Ophiolitic": {
                "title": "Sinai Ophiolitic Basalts",
                "location": "Southern Sinai Peninsula",
                "age": "Cretaceous (~100 Ma, obducted)",
                "tectonic": "Oceanic crust, obducted ophiolite complex",
                "chemistry": """
Characteristic Geochemistry:
• Zr/Nb: >6.5 (highly depleted, MORB-like)
• Cr/Ni: 2.0-3.5 (high, reflects mantle depletion)
• Ba: <200 ppm (very low incompatible elements)
• Rb: <10 ppm (extremely depleted)
• Wall thickness: >8 mm (thick-walled vessels)

Petrogenesis:
Typical mid-ocean ridge basalt (MORB) chemistry.
High degree partial melting of depleted mantle.
Part of Semail-type ophiolite sequences.

Tectonic Context:
Represents ancient oceanic crust obducted during
Cretaceous collision. Not contemporaneous volcanism.

Archaeological Significance:
Distinctive thick-walled vessels. Major source for Levantine
assemblages. High Cr and Ni diagnostic of ultramafic sources.
                """,
                "references": "Coleman (1977), Egyptian Geological Survey"
            },
            "Sinai Transitional": {
                "title": "Sinai / Transitional Basalts",
                "location": "Sinai Peninsula, transitional zones",
                "age": "Variable",
                "tectonic": "Mixed oceanic-continental signatures",
                "chemistry": """
Characteristic Geochemistry:
• Zr/Nb: 5.5-6.5 (intermediate)
• Shows mixed MORB and continental signatures
• Wall thickness: >8 mm

Petrogenesis:
Transitional between pure ophiolitic and continental sources.
May represent:
- Contaminated ophiolitic sources
- Back-arc basin basalts
- Continental margin volcanism

Archaeological Significance:
Represents Sinai sources that don't fit pure ophiolitic
chemistry. Still produces thick-walled vessels.
                """,
                "references": "Egyptian Geological Survey"
            },
            "Local Levantine": {
                "title": "Local Levantine Basalts",
                "location": "Golan Heights, Galilee, Hula Basin, Northern Israel",
                "age": "Pliocene to Recent (<5 Ma)",
                "tectonic": "Continental intraplate volcanism, Dead Sea Transform",
                "chemistry": """
Characteristic Geochemistry:
• Cr/Ni: >3.5 (very high, distinctive)
• Variable Zr/Nb depending on specific source
• Wall thickness: >8 mm

Regional Variations:
GOLAN HEIGHTS:
- Extensive Pliocene-Pleistocene basalt flows
- Multiple chemical subtypes
- Source: Mor, D. stratigraphic studies

GALILEE / HULA:
- Quaternary volcanism
- Associated with Dead Sea Transform
- Local quarrying documented

Petrogenesis:
Continental intraplate volcanism. High Cr/Ni suggests
interaction with lithospheric mantle or crustal contamination.
Not related to ophiolitic processes.

Archaeological Significance:
Locally available sources. High Cr/Ni is diagnostic.
Thick-walled vessels. Important for understanding
local vs. imported assemblages.
                """,
                "references": "Mor (1993), Weinstein-Evron, GSI maps"
            },
            "Harrat Ash Shaam": {
                "title": "Harrat Ash Shaam (Jordanian) Basalts",
                "location": "Jordan, NE basalt plateaus",
                "age": "Miocene to Recent",
                "tectonic": "Continental intraplate, Arabian Plate volcanism",
                "chemistry": """
Characteristic Geochemistry:
• Geochemically similar to some Levantine sources
• Variable alkalinity
• Can overlap with "exotic" classifications

Petrogenesis:
Part of extensive Arabian Plate volcanism.
Multiple episodes of eruption.
Complex mantle source evolution.

Current Status in Toolkit:
Not separately classified - may appear as:
- "Egyptian Alkaline" (if highly alkaline)
- "Local Levantine" (if high Cr/Ni)
- "Review Required" (if ambiguous)

Archaeological Significance:
Important potential source for eastern Levantine sites.
May require isotopic analysis for definitive identification.
Chemical overlap with other sources is a known issue.

Future Enhancement:
Could be added as separate category with additional
geochemical constraints or isotopic data.
                """,
                "references": "Shaw et al., Ilani et al., Jordanian surveys"
            }
        }

        # Create tabs for each region
        for region, data in contexts.items():
            frame = ttk.Frame(notebook)
            notebook.add(frame, text=region)

            # Create scrollable text
            text_frame = ttk.Frame(frame)
            text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            text = tk.Text(text_frame, wrap="word", font=("Arial", 10), padx=10, pady=10)
            scrollbar = ttk.Scrollbar(text_frame, command=text.yview)
            text.configure(yscrollcommand=scrollbar.set)

            text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            # Add content
            text.insert("end", f"{data['title']}\n", "title")
            text.insert("end", "=" * 70 + "\n\n")
            text.insert("end", f"Location: {data['location']}\n", "bold")
            text.insert("end", f"Age: {data['age']}\n", "bold")
            text.insert("end", f"Tectonic Setting: {data['tectonic']}\n\n", "bold")
            text.insert("end", data['chemistry'])
            text.insert("end", f"\n\nKey References: {data['references']}\n", "refs")

            # Configure tags
            text.tag_config("title", font=("Arial", 12, "bold"))
            text.tag_config("bold", font=("Arial", 10, "bold"))
            text.tag_config("refs", font=("Arial", 9, "italic"), foreground="blue")

            text.config(state="disabled")

        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)

    
    # ════════════════════════════════════════════════════════════════════
    # NEW FEATURES: Unit Conversion, Isotopes, Maps
    # ════════════════════════════════════════════════════════════════════


    def _load_reference_dataset(self):
        """Load a reference dataset for comparison"""
        path = filedialog.askopenfilename(
            title="Load Reference Dataset",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if not path:
            return

        try:
            reference_samples = []

            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    reference_samples.append(row)

            if not reference_samples:
                messagebox.showinfo("Empty File", "The reference dataset is empty.")
                return

            # Show reference comparison dialog
            self._show_reference_comparison(reference_samples, path)

        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load reference dataset:\n{str(e)}")

    def _show_reference_comparison(self, reference_samples, ref_path):
        """Show comparison between current samples and reference dataset"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Reference Dataset Comparison")
        dialog.geometry("1000x700")

        # Header
        header = ttk.Frame(dialog)
        header.pack(fill=tk.X, pady=10, padx=10)

        ttk.Label(header, text="Reference Dataset Comparison",
                 font=("Arial", 14, "bold")).pack()
        ttk.Label(header, text=f"Reference: {os.path.basename(ref_path)}",
                 font=("Arial", 10)).pack()
        ttk.Label(header, text=f"Your Dataset: {len(self.samples)} samples | Reference: {len(reference_samples)} samples",
                 font=("Arial", 9)).pack(pady=5)

        # Create notebook for different comparison views
        notebook = ttk.Notebook(dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Tab 1: Statistical Comparison
        stats_frame = ttk.Frame(notebook)
        notebook.add(stats_frame, text="Statistical Comparison")
        self._create_stats_comparison_tab(stats_frame, reference_samples)

        # Tab 2: Ratio Distribution
        ratio_frame = ttk.Frame(notebook)
        notebook.add(ratio_frame, text="Ratio Distributions")
        self._create_ratio_comparison_tab(ratio_frame, reference_samples)

        # Tab 3: Classification Match
        match_frame = ttk.Frame(notebook)
        notebook.add(match_frame, text="Classification Match")
        self._create_match_comparison_tab(match_frame, reference_samples)

        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)

    def _create_stats_comparison_tab(self, parent, reference_samples):
        """Create statistical comparison tab"""
        text_frame = ttk.Frame(parent)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        text = tk.Text(text_frame, wrap="word", font=("Courier", 9), padx=10, pady=10)
        scrollbar = ttk.Scrollbar(text_frame, command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)

        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Compare statistics
        text.insert("end", "STATISTICAL COMPARISON\n")
        text.insert("end", "=" * 80 + "\n\n")

        fields = ["Zr_ppm", "Nb_ppm", "Ba_ppm", "Cr_ppm", "Ni_ppm",
                 "Zr_Nb_Ratio", "Cr_Ni_Ratio"]

        for field in fields:
            # Your dataset
            your_values = [safe_float(s.get(field)) for s in self.samples]
            your_values = [v for v in your_values if v is not None]

            # Reference dataset
            ref_values = [safe_float(s.get(field)) for s in reference_samples]
            ref_values = [v for v in ref_values if v is not None]

            if your_values and ref_values:
                text.insert("end", f"{field}\n")
                text.insert("end", "-" * 80 + "\n")
                text.insert("end", f"  Your Dataset:  mean={statistics.mean(your_values):8.2f}  ")
                text.insert("end", f"median={statistics.median(your_values):8.2f}  ")
                text.insert("end", f"std={statistics.stdev(your_values):7.2f}\n")
                text.insert("end", f"  Reference:     mean={statistics.mean(ref_values):8.2f}  ")
                text.insert("end", f"median={statistics.median(ref_values):8.2f}  ")
                text.insert("end", f"std={statistics.stdev(ref_values):7.2f}\n\n")

        text.config(state="disabled")

    def _create_ratio_comparison_tab(self, parent, reference_samples):
        """Create ratio distribution comparison"""
        ttk.Label(parent, text="Visual comparison of Zr/Nb and Cr/Ni distributions",
                 font=("Arial", 11, "bold")).pack(pady=10)

        text_frame = ttk.Frame(parent)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        text = tk.Text(text_frame, wrap="word", font=("Courier", 9))
        scrollbar = ttk.Scrollbar(text_frame, command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)

        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Simple text-based distribution
        text.insert("end", "ZR/NB RATIO DISTRIBUTION\n")
        text.insert("end", "=" * 60 + "\n\n")

        your_zrnb = [safe_float(s.get("Zr_Nb_Ratio")) for s in self.samples]
        your_zrnb = [v for v in your_zrnb if v is not None]

        ref_zrnb = [safe_float(s.get("Zr_Nb_Ratio")) for s in reference_samples]
        ref_zrnb = [v for v in ref_zrnb if v is not None]

        if your_zrnb:
            text.insert("end", f"Your Dataset: {len(your_zrnb)} samples\n")
            text.insert("end", f"Range: {min(your_zrnb):.2f} - {max(your_zrnb):.2f}\n\n")

        if ref_zrnb:
            text.insert("end", f"Reference: {len(ref_zrnb)} samples\n")
            text.insert("end", f"Range: {min(ref_zrnb):.2f} - {max(ref_zrnb):.2f}\n\n")

        text.insert("end", "\nCR/NI RATIO DISTRIBUTION\n")
        text.insert("end", "=" * 60 + "\n\n")

        your_crni = [safe_float(s.get("Cr_Ni_Ratio")) for s in self.samples]
        your_crni = [v for v in your_crni if v is not None]

        ref_crni = [safe_float(s.get("Cr_Ni_Ratio")) for s in reference_samples]
        ref_crni = [v for v in ref_crni if v is not None]

        if your_crni:
            text.insert("end", f"Your Dataset: {len(your_crni)} samples\n")
            text.insert("end", f"Range: {min(your_crni):.2f} - {max(your_crni):.2f}\n\n")

        if ref_crni:
            text.insert("end", f"Reference: {len(ref_crni)} samples\n")
            text.insert("end", f"Range: {min(ref_crni):.2f} - {max(ref_crni):.2f}\n")

        text.config(state="disabled")

    def _create_match_comparison_tab(self, parent, reference_samples):
        """Create classification match comparison"""
        ttk.Label(parent, text="Classification agreement between datasets",
                 font=("Arial", 11, "bold")).pack(pady=10)

        text_frame = ttk.Frame(parent)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        text = tk.Text(text_frame, wrap="word", font=("Courier", 9))
        scrollbar = ttk.Scrollbar(text_frame, command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)

        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Compare classification distributions

        your_classes = [get_consistent_classification(s) for s in self.samples]
        ref_classes = [get_consistent_classification(s) for s in reference_samples]

        your_counts = Counter(your_classes)
        ref_counts = Counter(ref_classes)

        text.insert("end", "CLASSIFICATION DISTRIBUTION\n")
        text.insert("end", "=" * 70 + "\n\n")

        all_classes = set(your_counts.keys()) | set(ref_counts.keys())

        text.insert("end", f"{'Classification':<40} {'Your Data':>12} {'Reference':>12}\n")
        text.insert("end", "-" * 70 + "\n")

        for cls in sorted(all_classes):
            your_count = your_counts.get(cls, 0)
            ref_count = ref_counts.get(cls, 0)
            your_pct = (your_count / len(self.samples) * 100) if self.samples else 0
            ref_pct = (ref_count / len(reference_samples) * 100) if reference_samples else 0

            text.insert("end", f"{cls:<40} {your_count:4d} ({your_pct:4.1f}%)  ")
            text.insert("end", f"{ref_count:4d} ({ref_pct:4.1f}%)\n")

        text.config(state="disabled")

# ────────────────────────────────────────────────
# Museum Import Dialog
# ────────────────────────────────────────────────


    
    # ═══════════════════════════════════════════════════════════════════════════════
    # CORE PROFESSIONAL FEATURES - v10.2 PROFESSIONAL EDITION
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def _show_tas_diagram(self):
        """TAS Diagram - Total Alkali vs Silica (IUGS Classification)"""
        # Check for matplotlib
        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
            from matplotlib.patches import Polygon
        except ImportError:
            messagebox.showerror(
                "Missing Dependency",
                "TAS Diagram requires matplotlib.\n\n"
                "Install with: pip install matplotlib"
            )
            return
        
        # Get samples with major element data
        samples_with_data = [s for s in self.samples 
                            if self._has_major_elements(s, ['SiO2', 'Na2O', 'K2O'])]
        
        if not samples_with_data:
            messagebox.showwarning(
                "No Major Element Data",
                "No samples have SiO2, Na2O, and K2O data.\n\n"
                "TAS diagram requires major element wt% data."
            )
            return
        
        # Create TAS window
        tas_window = tk.Toplevel(self.root)
        tas_window.title("TAS Diagram - Total Alkali vs Silica")
        tas_window.geometry("1000x800")
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Draw TAS classification fields
        self._draw_tas_fields(ax)
        
        # Plot samples
        sio2_values = []
        alkali_values = []
        colors = []
        sample_ids = []
        
        for sample in samples_with_data:
            sio2 = safe_float(sample.get('SiO2', ''))
            na2o = safe_float(sample.get('Na2O', ''))
            k2o = safe_float(sample.get('K2O', ''))
            
            if sio2 and na2o is not None and k2o is not None:
                total_alkali = na2o + k2o
                sio2_values.append(sio2)
                alkali_values.append(total_alkali)
                sample_ids.append(sample.get('Sample_ID', 'Unknown'))
                
                # Color by classification
                classification = get_consistent_classification(sample)
                color_map = {
                    "EGYPTIAN (HADDADIN FLOW)": "blue",
                    "EGYPTIAN (ALKALINE / EXOTIC)": "red",
                    "SINAI / TRANSITIONAL": "gold",
                    "SINAI OPHIOLITIC": "orange",
                    "LOCAL LEVANTINE": "green",
                    "HARRAT ASH SHAAM": "purple",
                }
                colors.append(color_map.get(classification, "gray"))
        
        # Plot
        scatter = ax.scatter(sio2_values, alkali_values, 
                           c=colors, s=100, alpha=0.7, 
                           edgecolors='black', linewidths=0.5, zorder=3)
        
        # Labels
        ax.set_xlabel('SiO₂ (wt%)', fontsize=13, fontweight='bold')
        ax.set_ylabel('Na₂O + K₂O (wt%)', fontsize=13, fontweight='bold')
        ax.set_title('TAS Diagram - Total Alkali vs Silica\n(IUGS Classification)', 
                    fontsize=15, fontweight='bold', pad=20)
        ax.set_xlim(35, 80)
        ax.set_ylim(0, 16)
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Sample count
        ax.text(0.02, 0.98, f'n = {len(sio2_values)} samples', 
               transform=ax.transAxes, fontsize=11,
               verticalalignment='top', 
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        
        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, tas_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add toolbar
        toolbar_frame = tk.Frame(tas_window)
        toolbar_frame.pack(side=tk.BOTTOM, fill=tk.X)
        toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
        toolbar.update()
    
    def _draw_tas_fields(self, ax):
        """Draw TAS classification field boundaries (Le Bas et al., 1986)"""
        # Alkaline vs Sub-alkaline dividing line
        alkaline_line_x = [39, 40, 43, 45, 48.4, 52.5, 57.6, 63, 69, 77]
        alkaline_line_y = [0, 0.4, 2, 2.8, 4, 5, 6, 7, 8, 8]
        ax.plot(alkaline_line_x, alkaline_line_y, 'k--', linewidth=1.5, alpha=0.7)
        
        # Field labels
        ax.text(46, 2, 'Basalt', fontsize=10, ha='center', 
               bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
        ax.text(54.5, 3, 'Basaltic\nAndesite', fontsize=9, ha='center',
               bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.5))
        ax.text(60, 3.5, 'Andesite', fontsize=10, ha='center',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        ax.text(43, 6.5, 'Trachy-\nbasalt', fontsize=8, ha='center')
        ax.text(49, 8, 'Basaltic\nTrachyandesite', fontsize=7, ha='center')
        ax.text(55, 9, 'Trachyandesite', fontsize=8, ha='center')
        ax.text(43, 10, 'Tephrite\nBasanite', fontsize=8, ha='center')
        ax.text(49, 12, 'Phonotephrite', fontsize=8, ha='center')
        ax.text(41, 0.5, 'Picrobasalt', fontsize=7, ha='center', style='italic')
    
    def _show_spider_diagram(self):
        """Spider Diagram - Normalized multi-element plot"""
        # Check for matplotlib
        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
        except ImportError:
            messagebox.showerror(
                "Missing Dependency",
                "Spider Diagram requires matplotlib.\n\n"
                "Install with: pip install matplotlib"
            )
            return
        
        if not self.samples:
            messagebox.showwarning("No Data", "No samples to plot.")
            return
        
        # Create window
        spider_window = tk.Toplevel(self.root)
        spider_window.title("Spider Diagram - Normalized Multi-Element Plot")
        spider_window.geometry("1200x700")
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 7))
        
        # Primitive Mantle normalization values (McDonough & Sun, 1995)
        pm_values = {
            'Rb': 0.6,
            'Ba': 6.6,
            'Th': 0.085,
            'U': 0.021,
            'K': 240,
            'Nb': 0.658,
            'La': 0.648,
            'Ce': 1.675,
            'Sr': 19.9,
            'Nd': 1.250,
            'P': 90,
            'Zr': 10.5,
            'Ti': 1205,
            'Y': 4.3
        }
        
        elements = ['Rb', 'Ba', 'Nb', 'La', 'Ce', 'Sr', 'Nd', 'Zr', 'Ti', 'Y']
        x_positions = list(range(len(elements)))
        
        # Plot each sample
        for sample in self.samples[:20]:  # Limit to 20 samples for clarity
            values = []
            for elem in elements:
                val = safe_float(sample.get(f'{elem}_ppm', ''))
                if val and elem in pm_values:
                    normalized = val / pm_values[elem]
                    values.append(normalized)
                else:
                    values.append(None)
            
            if any(v is not None for v in values):
                classification = get_consistent_classification(sample)
                color_map = {
                    "EGYPTIAN (HADDADIN FLOW)": "blue",
                    "EGYPTIAN (ALKALINE / EXOTIC)": "red",
                    "SINAI / TRANSITIONAL": "gold",
                    "SINAI OPHIOLITIC": "orange",
                    "LOCAL LEVANTINE": "green",
                    "HARRAT ASH SHAAM": "purple",
                }
                color = color_map.get(classification, "gray")
                
                ax.plot(x_positions, values, marker='o', linewidth=2, 
                       color=color, alpha=0.6, markersize=8)
        
        ax.set_xticks(x_positions)
        ax.set_xticklabels(elements, fontsize=11)
        ax.set_ylabel('Sample / Primitive Mantle', fontsize=12, fontweight='bold')
        ax.set_title('Spider Diagram - Primitive Mantle Normalized', 
                    fontsize=14, fontweight='bold', pad=15)
        ax.set_yscale('log')
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_ylim(0.1, 1000)
        
        plt.tight_layout()
        
        # Embed
        canvas = FigureCanvasTkAgg(fig, spider_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        toolbar_frame = tk.Frame(spider_window)
        toolbar_frame.pack(side=tk.BOTTOM, fill=tk.X)
        toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
        toolbar.update()
    
    def _show_pearce_diagrams(self):
        """Show Pearce discrimination diagrams"""
        messagebox.showinfo(
            "Pearce Diagrams",
            "Pearce discrimination diagrams are available in the\n"
            "Discrimination Diagrams plugin.\n\n"
            "Install the plugin from Tools → Manage Plugins"
        )
    
    def _show_harker_diagrams(self):
        """Harker variation diagrams (major elements vs SiO2)"""
        # Check for matplotlib
        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
        except ImportError:
            messagebox.showerror(
                "Missing Dependency",
                "Harker Diagrams require matplotlib.\n\n"
                "Install with: pip install matplotlib"
            )
            return
        
        samples_with_data = [s for s in self.samples 
                            if self._has_major_elements(s, ['SiO2'])]
        
        if not samples_with_data:
            messagebox.showwarning("No Data", "No samples with major element data.")
            return
        
        # Create window
        harker_window = tk.Toplevel(self.root)
        harker_window.title("Harker Variation Diagrams")
        harker_window.geometry("1200x900")
        
        # Create 2x3 subplot
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        axes = axes.flatten()
        
        elements = ['TiO2', 'Al2O3', 'Fe2O3', 'MgO', 'CaO', 'Na2O']
        
        for idx, element in enumerate(elements):
            ax = axes[idx]
            sio2_vals = []
            elem_vals = []
            colors = []
            
            for sample in samples_with_data:
                sio2 = safe_float(sample.get('SiO2', ''))
                elem = safe_float(sample.get(element, ''))
                
                if sio2 and elem is not None:
                    sio2_vals.append(sio2)
                    elem_vals.append(elem)
                    
                    classification = get_consistent_classification(sample)
                    color_map = {
                        "EGYPTIAN (HADDADIN FLOW)": "blue",
                        "EGYPTIAN (ALKALINE / EXOTIC)": "red",
                        "SINAI / TRANSITIONAL": "gold",
                        "SINAI OPHIOLITIC": "orange",
                        "LOCAL LEVANTINE": "green",
                        "HARRAT ASH SHAAM": "purple",
                    }
                    colors.append(color_map.get(classification, "gray"))
            
            if sio2_vals:
                ax.scatter(sio2_vals, elem_vals, c=colors, s=80, alpha=0.6, 
                          edgecolors='black', linewidths=0.5)
            
            ax.set_xlabel('SiO₂ (wt%)', fontsize=10, fontweight='bold')
            ax.set_ylabel(f'{element} (wt%)', fontsize=10, fontweight='bold')
            ax.set_title(f'{element} vs SiO₂', fontsize=11, fontweight='bold')
            ax.grid(True, alpha=0.3)
        
        fig.suptitle('Harker Variation Diagrams', fontsize=16, fontweight='bold', y=0.995)
        plt.tight_layout()
        
        # Embed
        canvas = FigureCanvasTkAgg(fig, harker_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        toolbar_frame = tk.Frame(harker_window)
        toolbar_frame.pack(side=tk.BOTTOM, fill=tk.X)
        toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
        toolbar.update()
    
    def _show_srnd_isotope_plot(self):
        """Sr-Nd Isotope Plot - 87Sr/86Sr vs 143Nd/144Nd"""
        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
        except ImportError:
            messagebox.showerror(
                "Missing Dependency",
                "Isotope plots require matplotlib.\n\n"
                "Install with: pip install matplotlib"
            )
            return
        
        # Get samples with Sr-Nd isotope data
        samples_with_data = []
        for s in self.samples:
            sr = safe_float(s.get('87Sr_86Sr', ''))
            nd = safe_float(s.get('143Nd_144Nd', ''))
            if sr and nd:
                samples_with_data.append(s)
        
        if not samples_with_data:
            messagebox.showwarning(
                "No Isotope Data",
                "No samples have Sr-Nd isotope data.\n\n"
                "Required columns: 87Sr_86Sr, 143Nd_144Nd"
            )
            return
        
        # Create window
        isotope_window = tk.Toplevel(self.root)
        isotope_window.title("Sr-Nd Isotope Systematics")
        isotope_window.geometry("1000x800")
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Extract data
        sr87_86 = []
        nd143_144 = []
        colors = []
        sample_ids = []
        
        for sample in samples_with_data:
            sr = safe_float(sample.get('87Sr_86Sr', ''))
            nd = safe_float(sample.get('143Nd_144Nd', ''))
            
            sr87_86.append(sr)
            nd143_144.append(nd)
            sample_ids.append(sample.get('Sample_ID', 'Unknown'))
            
            classification = get_consistent_classification(sample)
            color_map = {
                "EGYPTIAN (HADDADIN FLOW)": "blue",
                "EGYPTIAN (ALKALINE / EXOTIC)": "red",
                "SINAI / TRANSITIONAL": "gold",
                "SINAI OPHIOLITIC": "orange",
                "LOCAL LEVANTINE": "green",
                "HARRAT ASH SHAAM": "purple",
            }
            colors.append(color_map.get(classification, "gray"))
        
        # Plot samples
        ax.scatter(sr87_86, nd143_144, c=colors, s=120, alpha=0.7,
                  edgecolors='black', linewidths=0.8, zorder=3)
        
        # Add error bars if available
        sr_errors = [safe_float(s.get('87Sr_86Sr_error', '')) or 0 for s in samples_with_data]
        nd_errors = [safe_float(s.get('143Nd_144Nd_error', '')) or 0 for s in samples_with_data]
        
        if any(sr_errors) or any(nd_errors):
            ax.errorbar(sr87_86, nd143_144, xerr=sr_errors, yerr=nd_errors,
                       fmt='none', ecolor='gray', alpha=0.5, zorder=2)
        
        # Reference fields (common mantle reservoirs)
        # MORB field
        ax.text(0.7025, 0.51305, 'MORB', fontsize=9, ha='center',
               bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
        
        # OIB field  
        ax.text(0.7035, 0.51295, 'OIB', fontsize=9, ha='center',
               bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))
        
        # Labels
        ax.set_xlabel('⁸⁷Sr/⁸⁶Sr', fontsize=13, fontweight='bold')
        ax.set_ylabel('¹⁴³Nd/¹⁴⁴Nd', fontsize=13, fontweight='bold')
        ax.set_title('Sr-Nd Isotope Systematics\nMantle Source Signatures', 
                    fontsize=14, fontweight='bold', pad=20)
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Sample count
        ax.text(0.02, 0.98, f'n = {len(samples_with_data)} samples', 
               transform=ax.transAxes, fontsize=10,
               verticalalignment='top', 
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        
        # Embed
        canvas = FigureCanvasTkAgg(fig, isotope_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        toolbar_frame = tk.Frame(isotope_window)
        toolbar_frame.pack(side=tk.BOTTOM, fill=tk.X)
        toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
        toolbar.update()
    
    def _show_pb_isotope_plots(self):
        """Pb Isotope Plots - 206Pb/204Pb vs 207Pb/204Pb and 208Pb/204Pb"""
        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
        except ImportError:
            messagebox.showerror(
                "Missing Dependency",
                "Isotope plots require matplotlib.\n\n"
                "Install with: pip install matplotlib"
            )
            return
        
        # Get samples with Pb isotope data
        samples_with_data = []
        for s in self.samples:
            pb206 = safe_float(s.get('206Pb_204Pb', ''))
            pb207 = safe_float(s.get('207Pb_204Pb', ''))
            pb208 = safe_float(s.get('208Pb_204Pb', ''))
            if pb206 and (pb207 or pb208):
                samples_with_data.append(s)
        
        if not samples_with_data:
            messagebox.showwarning(
                "No Pb Isotope Data",
                "No samples have Pb isotope data.\n\n"
                "Required: 206Pb_204Pb plus 207Pb_204Pb or 208Pb_204Pb"
            )
            return
        
        # Create window
        isotope_window = tk.Toplevel(self.root)
        isotope_window.title("Pb Isotope Systematics")
        isotope_window.geometry("1400x700")
        
        # Create 2 subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Extract data
        pb206_204 = []
        pb207_204 = []
        pb208_204 = []
        colors = []
        
        for sample in samples_with_data:
            pb206 = safe_float(sample.get('206Pb_204Pb', ''))
            pb207 = safe_float(sample.get('207Pb_204Pb', ''))
            pb208 = safe_float(sample.get('208Pb_204Pb', ''))
            
            if pb206:
                pb206_204.append(pb206)
                pb207_204.append(pb207 if pb207 else None)
                pb208_204.append(pb208 if pb208 else None)
                
                classification = get_consistent_classification(sample)
                color_map = {
                    "EGYPTIAN (HADDADIN FLOW)": "blue",
                    "EGYPTIAN (ALKALINE / EXOTIC)": "red",
                    "SINAI / TRANSITIONAL": "gold",
                    "SINAI OPHIOLITIC": "orange",
                    "LOCAL LEVANTINE": "green",
                    "HARRAT ASH SHAAM": "purple",
                }
                colors.append(color_map.get(classification, "gray"))
        
        # Plot 1: 206Pb/204Pb vs 207Pb/204Pb
        valid_207 = [(x, y, c) for x, y, c in zip(pb206_204, pb207_204, colors) if y is not None]
        if valid_207:
            x_vals, y_vals, c_vals = zip(*valid_207)
            ax1.scatter(x_vals, y_vals, c=c_vals, s=120, alpha=0.7,
                       edgecolors='black', linewidths=0.8)
            ax1.set_xlabel('²⁰⁶Pb/²⁰⁴Pb', fontsize=12, fontweight='bold')
            ax1.set_ylabel('²⁰⁷Pb/²⁰⁴Pb', fontsize=12, fontweight='bold')
            ax1.set_title('²⁰⁶Pb/²⁰⁴Pb vs ²⁰⁷Pb/²⁰⁴Pb', fontsize=13, fontweight='bold')
            ax1.grid(True, alpha=0.3, linestyle='--')
            ax1.text(0.02, 0.98, f'n = {len(valid_207)}', 
                    transform=ax1.transAxes, fontsize=10,
                    verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        else:
            ax1.text(0.5, 0.5, 'No ²⁰⁷Pb/²⁰⁴Pb data', 
                    transform=ax1.transAxes, ha='center', va='center',
                    fontsize=12, color='gray')
        
        # Plot 2: 206Pb/204Pb vs 208Pb/204Pb
        valid_208 = [(x, y, c) for x, y, c in zip(pb206_204, pb208_204, colors) if y is not None]
        if valid_208:
            x_vals, y_vals, c_vals = zip(*valid_208)
            ax2.scatter(x_vals, y_vals, c=c_vals, s=120, alpha=0.7,
                       edgecolors='black', linewidths=0.8)
            ax2.set_xlabel('²⁰⁶Pb/²⁰⁴Pb', fontsize=12, fontweight='bold')
            ax2.set_ylabel('²⁰⁸Pb/²⁰⁴Pb', fontsize=12, fontweight='bold')
            ax2.set_title('²⁰⁶Pb/²⁰⁴Pb vs ²⁰⁸Pb/²⁰⁴Pb', fontsize=13, fontweight='bold')
            ax2.grid(True, alpha=0.3, linestyle='--')
            ax2.text(0.02, 0.98, f'n = {len(valid_208)}', 
                    transform=ax2.transAxes, fontsize=10,
                    verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        else:
            ax2.text(0.5, 0.5, 'No ²⁰⁸Pb/²⁰⁴Pb data', 
                    transform=ax2.transAxes, ha='center', va='center',
                    fontsize=12, color='gray')
        
        fig.suptitle('Pb Isotope Systematics - Mantle Source Signatures', 
                    fontsize=15, fontweight='bold', y=0.98)
        plt.tight_layout()
        
        # Embed
        canvas = FigureCanvasTkAgg(fig, isotope_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        toolbar_frame = tk.Frame(isotope_window)
        toolbar_frame.pack(side=tk.BOTTOM, fill=tk.X)
        toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
        toolbar.update()
    
    def _open_unit_converter(self):
        """Unit Converter - ppm ↔ wt% with oxide factors"""
        converter_window = tk.Toplevel(self.root)
        converter_window.title("Unit Converter - ppm ↔ wt%")
        converter_window.geometry("700x600")
        
        # Title
        title_frame = tk.Frame(converter_window, bg='#2196F3', height=60)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        tk.Label(title_frame, text="🔄 Unit Converter", 
                font=("Arial", 16, "bold"), bg='#2196F3', fg='white').pack(pady=15)
        
        # Content
        content = tk.Frame(converter_window)
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(content, text="Convert all trace elements:", 
                font=("Arial", 11, "bold")).pack(anchor=tk.W, pady=5)
        
        tk.Label(content, text="ppm → wt% using proper oxide factors (e.g., ZrO₂, Nb₂O₅)", 
                font=("Arial", 9), fg='gray').pack(anchor=tk.W)
        
        # Options
        options_frame = tk.Frame(content)
        options_frame.pack(pady=20, fill=tk.X)
        
        conversion_var = tk.StringVar(value="ppm_to_wt")
        
        tk.Radiobutton(options_frame, text="Convert ppm → wt% (for publication)", 
                      variable=conversion_var, value="ppm_to_wt",
                      font=("Arial", 10)).pack(anchor=tk.W, pady=5)
        tk.Radiobutton(options_frame, text="Convert wt% → ppm", 
                      variable=conversion_var, value="wt_to_ppm",
                      font=("Arial", 10)).pack(anchor=tk.W, pady=5)
        
        # Info box
        info_frame = tk.Frame(content, relief=tk.RIDGE, borderwidth=2, bg='#E3F2FD')
        info_frame.pack(fill=tk.BOTH, expand=True, pady=15)
        
        info_text = """
Oxide Conversion Factors Used:

• Zr  → ZrO₂  (×1.3508)
• Nb  → Nb₂O₅ (×1.4305)
• Ti  → TiO₂  (×1.6688)
• Fe  → Fe₂O₃ (×1.4297)
• Ba  → BaO   (×1.1165)
• Sr  → SrO   (×1.1826)
• Rb  → Rb₂O  (×1.0936)

Example: 10,000 ppm Zr = 1.35 wt% ZrO₂
        """
        
        tk.Label(info_frame, text=info_text, font=("Courier", 9), 
                bg='#E3F2FD', justify=tk.LEFT).pack(padx=15, pady=15)
        
        # Buttons
        button_frame = tk.Frame(content)
        button_frame.pack(pady=15)
        
        def perform_conversion():
            direction = conversion_var.get()
            
            # Oxide factors
            oxide_factors = {
                'Zr': 1.3508, 'Nb': 1.4305, 'Ti': 1.6688, 'Fe': 1.4297,
                'Ba': 1.1165, 'Sr': 1.1826, 'Rb': 1.0936, 'Cr': 1.4616,
                'Ni': 1.2726, 'Y': 1.2699
            }
            
            converted_count = 0
            
            for sample in self.samples:
                for elem in ['Zr', 'Nb', 'Ba', 'Rb', 'Cr', 'Ni']:
                    ppm_key = f'{elem}_ppm'
                    wt_key = f'{elem}_wt%'
                    
                    if direction == "ppm_to_wt":
                        ppm_val = safe_float(sample.get(ppm_key, ''))
                        if ppm_val:
                            wt_val = (ppm_val / 10000) * oxide_factors.get(elem, 1.0)
                            sample[wt_key] = f"{wt_val:.4f}"
                            converted_count += 1
                    else:  # wt_to_ppm
                        wt_val = safe_float(sample.get(wt_key, ''))
                        if wt_val:
                            ppm_val = (wt_val / oxide_factors.get(elem, 1.0)) * 10000
                            sample[ppm_key] = f"{ppm_val:.1f}"
                            converted_count += 1
            
            self._refresh_table_page()
            self._mark_unsaved_changes()
            
            messagebox.showinfo(
                "Conversion Complete",
                f"Converted {converted_count} values.\n\n"
                f"Direction: {'ppm → wt%' if direction == 'ppm_to_wt' else 'wt% → ppm'}"
            )
            converter_window.destroy()
        
        tk.Button(button_frame, text="✓ Convert", command=perform_conversion,
                 bg="#4CAF50", fg="white", font=("Arial", 11, "bold"),
                 width=15, height=2).pack(side=tk.LEFT, padx=10)
        
        tk.Button(button_frame, text="Cancel", command=converter_window.destroy,
                 width=15, height=2).pack(side=tk.LEFT, padx=10)
    
    def _normalize_major_elements(self):
        """Normalize major elements to 100% (volatile-free basis)"""
        samples_with_data = [s for s in self.samples 
                            if self._has_major_elements(s, ['SiO2'])]
        
        if not samples_with_data:
            messagebox.showwarning(
                "No Major Element Data",
                "No samples have major element data to normalize."
            )
            return
        
        major_elements = ['SiO2', 'TiO2', 'Al2O3', 'Fe2O3', 'MgO', 'CaO', 'Na2O', 'K2O', 'P2O5']
        normalized_count = 0
        
        for sample in samples_with_data:
            total = 0.0
            values = {}
            
            # Sum major elements
            for elem in major_elements:
                val = safe_float(sample.get(elem, ''))
                if val:
                    values[elem] = val
                    total += val
            
            # Normalize to 100%
            if total > 0 and len(values) >= 3:  # Need at least 3 elements
                for elem, val in values.items():
                    normalized = (val / total) * 100.0
                    sample[f'{elem}_normalized'] = f"{normalized:.2f}"
                
                sample['Normalized_Total'] = "100.00"
                normalized_count += 1
        
        self._refresh_table_page()
        self._mark_unsaved_changes()
        
        messagebox.showinfo(
            "Normalization Complete",
            f"Normalized {normalized_count} samples to 100% (volatile-free).\n\n"
            "New columns created: SiO2_normalized, TiO2_normalized, etc."
        )
    
    def _open_bdl_handler(self):
        """Below Detection Limit (BDL) Handler"""
        bdl_window = tk.Toplevel(self.root)
        bdl_window.title("BDL Handler - Below Detection Limit")
        bdl_window.geometry("800x700")
        
        # Title
        title_frame = tk.Frame(bdl_window, bg='#FF9800', height=60)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        tk.Label(title_frame, text="⚠️ Detection Limit Handler", 
                font=("Arial", 16, "bold"), bg='#FF9800', fg='white').pack(pady=15)
        
        content = tk.Frame(bdl_window)
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(content, text="Handle values below detection limit (BDL)", 
                font=("Arial", 11, "bold")).pack(anchor=tk.W, pady=5)
        
        tk.Label(content, text="For values flagged as BDL, choose substitution method:", 
                font=("Arial", 9), fg='gray').pack(anchor=tk.W, pady=5)
        
        # Method selection
        method_frame = tk.LabelFrame(content, text="Substitution Method", font=("Arial", 10, "bold"))
        method_frame.pack(fill=tk.X, pady=15)
        
        method_var = tk.StringVar(value="dl_half")
        
        tk.Radiobutton(method_frame, text="DL/2 (most common - use half the detection limit)", 
                      variable=method_var, value="dl_half",
                      font=("Arial", 9)).pack(anchor=tk.W, padx=10, pady=5)
        
        tk.Radiobutton(method_frame, text="DL/√2 (more conservative)", 
                      variable=method_var, value="dl_sqrt2",
                      font=("Arial", 9)).pack(anchor=tk.W, padx=10, pady=5)
        
        tk.Radiobutton(method_frame, text="0 (zero substitution)", 
                      variable=method_var, value="zero",
                      font=("Arial", 9)).pack(anchor=tk.W, padx=10, pady=5)
        
        tk.Radiobutton(method_frame, text="Flag only (don't substitute)", 
                      variable=method_var, value="flag_only",
                      font=("Arial", 9)).pack(anchor=tk.W, padx=10, pady=5)
        
        # Detection limits input
        dl_frame = tk.LabelFrame(content, text="Detection Limits (ppm)", font=("Arial", 10, "bold"))
        dl_frame.pack(fill=tk.X, pady=15)
        
        dl_entries = {}
        elements = ['Zr', 'Nb', 'Ba', 'Rb', 'Cr', 'Ni']
        
        for idx, elem in enumerate(elements):
            row_frame = tk.Frame(dl_frame)
            row_frame.pack(fill=tk.X, padx=10, pady=3)
            
            tk.Label(row_frame, text=f"{elem}:", width=5, anchor=tk.W).pack(side=tk.LEFT)
            entry = tk.Entry(row_frame, width=10)
            entry.pack(side=tk.LEFT, padx=5)
            entry.insert(0, "5")  # Default DL
            dl_entries[elem] = entry
            
            tk.Label(row_frame, text="ppm", fg='gray').pack(side=tk.LEFT)
        
        # Summary
        summary_frame = tk.Frame(content, relief=tk.RIDGE, borderwidth=2, bg='#FFF3E0')
        summary_frame.pack(fill=tk.BOTH, expand=True, pady=15)
        
        summary_text = """
What This Does:

1. Scans all samples for values below detection limit
2. Applies chosen substitution method
3. Marks samples with BDL flag for transparency
4. Prevents BDL values from skewing ratio calculations

Scientific Note:
Zero substitution can bias results low. DL/2 is the
most commonly accepted method in geochemistry.
        """
        
        tk.Label(summary_frame, text=summary_text, font=("Arial", 9), 
                bg='#FFF3E0', justify=tk.LEFT).pack(padx=15, pady=10)
        
        # Buttons
        button_frame = tk.Frame(content)
        button_frame.pack(pady=10)
        
        def apply_bdl_handling():
            method = method_var.get()
            import math
            
            processed = 0
            
            for sample in self.samples:
                for elem in elements:
                    ppm_key = f'{elem}_ppm'
                    bdl_key = f'{elem}_BDL'
                    
                    val = safe_float(sample.get(ppm_key, ''))
                    dl = safe_float(dl_entries[elem].get())
                    
                    if val is not None and dl and val < dl:
                        sample[bdl_key] = "YES"
                        
                        if method == "dl_half":
                            sample[ppm_key] = str(dl / 2)
                        elif method == "dl_sqrt2":
                            sample[ppm_key] = str(dl / math.sqrt(2))
                        elif method == "zero":
                            sample[ppm_key] = "0"
                        # flag_only: don't change value
                        
                        processed += 1
            
            self._refresh_table_page()
            self._mark_unsaved_changes()
            
            messagebox.showinfo(
                "BDL Processing Complete",
                f"Processed {processed} values below detection limit.\n\n"
                f"Method: {method}\n"
                "All affected samples flagged with BDL marker."
            )
            bdl_window.destroy()
        
        tk.Button(button_frame, text="✓ Apply", command=apply_bdl_handling,
                 bg="#4CAF50", fg="white", font=("Arial", 11, "bold"),
                 width=15, height=2).pack(side=tk.LEFT, padx=10)
        
        tk.Button(button_frame, text="Cancel", command=bdl_window.destroy,
                 width=15, height=2).pack(side=tk.LEFT, padx=10)
    
    def _calculate_error_propagation(self):
        """Calculate error propagation for ratios"""
        import math
        
        samples_with_errors = [s for s in self.samples 
                              if safe_float(s.get('Zr_ppm_error')) or 
                                 safe_float(s.get('Nb_ppm_error'))]
        
        if not samples_with_errors:
            messagebox.showinfo(
                "No Error Data",
                "No samples have error/uncertainty values.\n\n"
                "Add ±error columns (e.g., Zr_ppm_error) to calculate propagated errors."
            )
            return
        
        calculated = 0
        
        for sample in samples_with_errors:
            # Zr/Nb ratio error
            zr = safe_float(sample.get('Zr_ppm', ''))
            nb = safe_float(sample.get('Nb_ppm', ''))
            zr_err = safe_float(sample.get('Zr_ppm_error', ''))
            nb_err = safe_float(sample.get('Nb_ppm_error', ''))
            
            if zr and nb and zr_err and nb_err and nb != 0:
                ratio = zr / nb
                # Error propagation for division: σ(A/B) = (A/B) * √[(σA/A)² + (σB/B)²]
                relative_error = math.sqrt((zr_err/zr)**2 + (nb_err/nb)**2)
                ratio_error = ratio * relative_error
                sample['Zr_Nb_Ratio_error'] = f"{ratio_error:.2f}"
                calculated += 1
            
            # Cr/Ni ratio error
            cr = safe_float(sample.get('Cr_ppm', ''))
            ni = safe_float(sample.get('Ni_ppm', ''))
            cr_err = safe_float(sample.get('Cr_ppm_error', ''))
            ni_err = safe_float(sample.get('Ni_ppm_error', ''))
            
            if cr and ni and cr_err and ni_err and ni != 0:
                ratio = cr / ni
                relative_error = math.sqrt((cr_err/cr)**2 + (ni_err/ni)**2)
                ratio_error = ratio * relative_error
                sample['Cr_Ni_Ratio_error'] = f"{ratio_error:.2f}"
                calculated += 1
        
        self._refresh_table_page()
        self._mark_unsaved_changes()
        
        messagebox.showinfo(
            "Error Propagation Complete",
            f"Calculated propagated errors for {calculated} ratios.\n\n"
            "New columns: Zr_Nb_Ratio_error, Cr_Ni_Ratio_error\n\n"
            "Formula used: σ(A/B) = (A/B) × √[(σA/A)² + (σB/B)²]"
        )
    
    def _has_major_elements(self, sample, required_elements):
        """Check if sample has required major element data"""
        for elem in required_elements:
            if not safe_float(sample.get(elem, '')):
                return False
        return True
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # PLUGIN SYSTEM METHODS
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def _show_progress(self, message, value=0):
        """Show progress bar with message"""
        self.progress_label.config(text=message)
        self.progress_var.set(value)
        self.progress_frame.pack(side=tk.BOTTOM, fill=tk.X, before=self.notebook.master)
        self.root.update_idletasks()
    
    def _update_progress(self, value, message=None):
        """Update progress bar"""
        self.progress_var.set(value)
        if message:
            self.progress_label.config(text=message)
        self.root.update_idletasks()
    
    def _hide_progress(self):
        """Hide progress bar"""
        self.progress_frame.pack_forget()
        self.progress_var.set(0)
        self.progress_label.config(text="")
    
    def _open_plugin_manager(self):
        """Open plugin manager dialog"""
        if HAS_PLUGIN_SYSTEM and 'PluginManager' in globals():
            from plugins.plugin_manager import PluginManager
            PluginManager(self)
        else:
            self._show_plugin_help()
    
    def _show_plugin_help(self):
        """Show help when plugins not available"""
        messagebox.showinfo(
            "Plugin System Not Found",
            "The plugins folder was not found.\n\n"
            "Plugins are OPTIONAL - your app works fine without them!\n\n"
            "To enable advanced features:\n"
            "1. Download the plugins package\n"
            "2. Extract the 'plugins' folder\n"
            "3. Place it next to this file\n"
            "4. Restart the application\n\n"
            "Advanced features include:\n"
            "• Statistical Analysis (PCA, DFA)\n"
            "• Report Generator\n"
            "• Photo Manager\n"
            "• Literature Comparison\n"
            "• And more...\n\n"
            "Main app works perfectly without plugins!"
        )
    
    def _check_plugin_folder(self):
        """Check if plugins folder exists and is valid"""
        from pathlib import Path
        plugin_dir = Path("plugins")
        if not plugin_dir.exists():
            return False
        if not (plugin_dir / "__init__.py").exists():
            return False
        return True
    
    def _discover_plugins(self):
        """Discover all available plugins dynamically from subfolders"""
        if not self._check_plugin_folder():
            return {}
        
        from pathlib import Path
        import importlib.util
        
        discovered = {}
        
        # Scan THREE subfolders
        plugin_folders = [
            Path("plugins/add-ons"),
            Path("plugins/software"),
            Path("plugins/hardware")
        ]
        
        for plugin_dir in plugin_folders:
            if not plugin_dir.exists():
                continue
            
            for py_file in plugin_dir.glob("*.py"):
                # Skip special files
                if py_file.stem in ["__init__", "plugin_manager"]:
                    continue
                
                try:
                    # Import module
                    spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Check for PLUGIN_INFO
                    if hasattr(module, 'PLUGIN_INFO'):
                        info = module.PLUGIN_INFO
                        discovered[info['id']] = {
                            'module': module,
                            'info': info,
                            'path': py_file
                        }
                except Exception as e:
                    print(f"Warning: Could not load plugin {py_file.stem}: {e}")
        
        return discovered
    
    def _load_plugins(self):
        """Load enabled plugins from config - Only SOFTWARE goes to Advanced menu"""
        if not HAS_PLUGIN_SYSTEM:
            return

        if not self._check_plugin_folder():
            return

        from pathlib import Path
        import json

        # Load enabled plugins from config
        config_file = Path("config/enabled_plugins.json")
        if not config_file.exists():
            return

        try:
            with open(config_file) as f:
                enabled_plugins = json.load(f)
        except Exception as e:
            return

        # Check if any enabled
        if not any(enabled_plugins.values()):
            return

        # Discover available plugins
        available_plugins = self._discover_plugins()

        # Clear Advanced menu first (if it exists)
        if hasattr(self, 'advanced_menu'):
            self.advanced_menu.delete(0, tk.END)
        else:
            # Create Advanced menu
            self.advanced_menu = tk.Menu(self.menubar, tearoff=0)
            self.menubar.add_cascade(label="Advanced", menu=self.advanced_menu)

        # Track if we added anything
        added_count = 0

        # Load each enabled plugin
        for plugin_id, is_enabled in enabled_plugins.items():
            if is_enabled and plugin_id in available_plugins:
                plugin_data = available_plugins[plugin_id]
                info = plugin_data['info']

                # Only SOFTWARE plugins go to Advanced menu
                category = info.get('category', '').lower()

                if category == 'software':
                    if self._load_single_plugin_to_menu(plugin_data, self.advanced_menu):
                        added_count += 1
                # All other categories (hardware, add-ons, unknown) silently skipped

        # If nothing was added, show disabled menu item
        if added_count == 0:
            self.advanced_menu.add_command(label="No enabled software plugins", state="disabled")

    def _load_single_plugin_to_menu(self, plugin_data, menu):
        """Load a single plugin and add it to the specified menu"""
        try:
            module = plugin_data['module']
            info = plugin_data['info']
            plugin_id = info['id']

            # Get plugin class (assumes class name matches: NamePlugin)
            class_name = ''.join(word.capitalize() for word in plugin_id.split('_')) + 'Plugin'

            if hasattr(module, class_name):
                plugin_class = getattr(module, class_name)
                plugin_instance = plugin_class(self)

                # Store instance
                setattr(self, f"{plugin_id}_plugin", plugin_instance)

                # Create menu label with icon
                menu_label = f"{info.get('icon', '📦')} {info['name']}..."

                # Find the open method
                open_method = None

                # Try different method names
                if hasattr(plugin_instance, 'show'):
                    open_method = plugin_instance.show
                elif hasattr(plugin_instance, 'show_interface'):
                    open_method = plugin_instance.show_interface
                elif hasattr(plugin_instance, f"open_{plugin_id}_window"):
                    open_method = getattr(plugin_instance, f"open_{plugin_id}_window")
                elif any(m.startswith('show_') for m in dir(plugin_instance)):
                    for method_name in dir(plugin_instance):
                        if method_name.startswith('show_') and not method_name.startswith('show__'):
                            open_method = getattr(plugin_instance, method_name)
                            break
                elif any(m.startswith('open_') and m.endswith('_window') for m in dir(plugin_instance)):
                    for method_name in dir(plugin_instance):
                        if method_name.startswith('open_') and method_name.endswith('_window'):
                            open_method = getattr(plugin_instance, method_name)
                            break

                if open_method:
                    menu.add_command(label=menu_label, command=open_method)
                    return True
                return False
            else:
                return False

        except Exception as e:
            return False

    def _call_demo_generator(self):
        """Call demo data generator add-on"""
        if hasattr(self, 'demo_data_generator_plugin'):
            self.demo_data_generator_plugin.show()
        else:
            messagebox.showinfo("Add-on Required",
                "Demo Data Generator add-on not enabled.\n\n"
                "Enable it in Tools → Manage Plugins")
    
    def _call_batch_processor(self):
        """Call batch processor add-on"""
        if hasattr(self, 'batch_processor_plugin'):
            self.batch_processor_plugin.show()
        else:
            messagebox.showinfo("Add-on Required",
                "Batch Processor add-on not enabled.\n\n"
                "Enable it in Tools → Manage Plugins")
    

# ────────────────────────────────────────────────
# Main entry point
# ────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()

    # Set custom icon from embedded base64 data
    try:
        if HAS_PILLOW and Image and ImageTk:
            icon_data = base64.b64decode(ICON_BASE64)
            icon_img = Image.open(BytesIO(icon_data))
            icon_photo = ImageTk.PhotoImage(icon_img)
            root.iconphoto(True, icon_photo)
    except Exception as e:
        # If icon loading fails, just continue with default icon
        pass

    app = BasaltTriageApp(root)
    root.mainloop()
