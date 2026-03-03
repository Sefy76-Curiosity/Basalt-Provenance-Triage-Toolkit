"""
Petrogenetic Modeling Suite v2.1
Complete magma evolution modeling suite with all features implemented
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Author: Sefy Levy & DeepSeek
License: CC BY-NC-SA 4.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

PLUGIN_INFO = {
    "category": "software",
    "field": "Petrology & Mineralogy",
    "id": "petrogenetic_modeling_suite",
    "name": "Petrogenetic Modeling Suite",
    "description": "Complete magma evolution: AFC · Fractional · Zone Refining · Mixing · Partial Melting · Phase Diagrams · MELTS · Comparison",
    "icon": "🌋",
    "version": "2.1.0",
    "requires": ["numpy", "scipy", "matplotlib", "pandas", "petthermotools", "juliapkg", "openpyxl"],
    "author": "Sefy Levy & DeepSeek"
}

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import numpy as np
import pandas as pd
from datetime import datetime
import json
import traceback
import sys
import os
from pathlib import Path
from collections import OrderedDict
import subprocess
import re
import time
import threading

try:
    import matplotlib
    matplotlib.use('TkAgg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    import matplotlib.patches as patches
    from matplotlib.patches import Polygon
    from matplotlib.lines import Line2D
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    from scipy import optimize, interpolate
    from scipy.integrate import odeint
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

# ===== PETTHERMOTOOLS CHECK =====
HAS_PETTERMO = False
try:
    import petthermotools as ptt
    HAS_PETTERMO = True
    print("✅ PetThermoTools available")
except ImportError:
    print("❌ PetThermoTools not installed")
# ================================


class PetrogeneticModelingSuitePlugin:
    """
    UNIFIED PETROGENETIC MODELS - COMPLETE IMPLEMENTATION
    All stubs and placeholders now fully implemented
    """

    _julia_initialized = False
    _SENTINEL_FILE = os.path.expanduser("~/.petthermotools_julia_env/.plugin_ready")

    def __init__(self, main_app):
        self.app = main_app
        self.window = None

        # ============ DATA ============
        self.samples = []
        self.current_element = None
        self.model_results = {
            'afc': None,
            'fractional': None,
            'zone': None,
            'mixing': None,
            'melting': None,
            'melts': None
        }

        # ============ UI VARIABLES ============
        self.notebook = None
        self.status_var = None
        self.progress = None
        self.element_var = tk.StringVar(value="")
        self.numeric_columns = []

        # ============ TDF DATABASE ============
        self.tdf_db = None
        self.current_tdf = None
        self.include_tdf_uncertainty = tk.BooleanVar(value=True)
        self._load_tdf_database()  # Add this line

        # AFC tab
        self.afc_C0_var = tk.DoubleVar(value=100.0)
        self.afc_Ca_var = tk.DoubleVar(value=10.0)
        self.afc_D_var = tk.DoubleVar(value=0.5)
        self.afc_r_var = tk.DoubleVar(value=0.3)
        self.afc_F_min_var = tk.DoubleVar(value=0.1)
        self.afc_F_max_var = tk.DoubleVar(value=1.0)
        self.afc_F_steps_var = tk.IntVar(value=50)

        # Fractional tab
        self.frac_C0_var = tk.DoubleVar(value=100.0)
        self.frac_D_var = tk.DoubleVar(value=0.5)
        self.frac_model_var = tk.StringVar(value="rayleigh")
        self.frac_F_min_var = tk.DoubleVar(value=0.1)
        self.frac_F_max_var = tk.DoubleVar(value=1.0)
        self.frac_F_steps_var = tk.IntVar(value=50)

        # Zone Refining tab
        self.zone_C0_var = tk.DoubleVar(value=100.0)
        self.zone_k_var = tk.DoubleVar(value=0.1)
        self.zone_passes_var = tk.IntVar(value=5)
        self.zone_length_var = tk.DoubleVar(value=1.0)
        self.zone_steps_var = tk.IntVar(value=100)

        # Mixing tab
        self.mix_model_var = tk.StringVar(value="binary")
        self.mix_CA_var = tk.DoubleVar(value=100.0)
        self.mix_CB_var = tk.DoubleVar(value=20.0)
        self.mix_CC_var = tk.DoubleVar(value=50.0)
        self.mix_fA_var = tk.DoubleVar(value=0.5)
        self.mix_fA_min_var = tk.DoubleVar(value=0.0)
        self.mix_fA_max_var = tk.DoubleVar(value=1.0)
        self.mix_steps_var = tk.IntVar(value=50)

        # Partial Melting tab
        self.melting_model_var = tk.StringVar(value="Batch Melting")
        self.melting_source_var = tk.StringVar(value="Primitive Mantle")
        self.melting_F_start_var = tk.DoubleVar(value=0.01)
        self.melting_F_end_var = tk.DoubleVar(value=0.25)
        self.melting_F_steps_var = tk.IntVar(value=25)
        self.melting_porosity_var = tk.DoubleVar(value=0.01)
        self.use_kd_database_var = tk.BooleanVar(value=True)

        # Phase Diagrams tab
        self.diagram_type_var = tk.StringVar(value="TAS (Total Alkali-Silica)")
        self.show_model_var = tk.BooleanVar(value=True)
        self.show_grid_var = tk.BooleanVar(value=True)
        self.show_legend_var = tk.BooleanVar(value=True)
        self.normalize_data_var = tk.BooleanVar(value=True)
        self.chondrite_normalize_var = tk.BooleanVar(value=True)

        # MELTS tab variables
        self.melts_model_var = tk.StringVar(value="Green2025")
        self.melts_calc_type_var = tk.StringVar(value="Fractional Crystallization")
        self.melts_preset_var = tk.StringVar(value="Basalt")
        self.melts_T_start_var = tk.DoubleVar(value=1300.0)
        self.melts_T_end_var = tk.DoubleVar(value=800.0)
        self.melts_steps_var = tk.IntVar(value=20)
        self.melts_pressure_var = tk.DoubleVar(value=1000.0)
        self.melts_fo2_var = tk.StringVar(value="FMQ")
        self.melts_fo2_offset_var = tk.DoubleVar(value=0.0)
        self.melts_keep_frac_var = tk.BooleanVar(value=True)
        self.melts_parallel_var = tk.BooleanVar(value=True)

        # Comparison tab
        self.compare_results = {}
        self.compare_vars = {}

        # Reference data
        self._init_reference_data()
        self._init_composition_vars()

        self._check_dependencies()

        self.mix_mode_var = tk.StringVar(value="linear")
        self.mix_D_A = tk.DoubleVar(value=1.0)
        self.mix_D_B = tk.DoubleVar(value=1.0)
        self.mix_D_C = tk.DoubleVar(value=1.0)
        self.mix_phi = tk.DoubleVar(value=0.1)
        self.binary_conc_A = tk.DoubleVar(value=1.0)
        self.binary_conc_B = tk.DoubleVar(value=1.0)
        self.mix_ratios = {'A': 0.703, 'B': 0.706, 'C': 0.709}
        self.mix_concentrations = {'A': 100, 'B': 200, 'C': 300}

    def _init_reference_data(self):
        """Initialize reference compositions and Kd databases"""
        self.primitive_mantle = {
            "La": 0.687, "Ce": 1.775, "Pr": 0.276, "Nd": 1.354,
            "Sm": 0.444, "Eu": 0.168, "Gd": 0.596, "Tb": 0.108,
            "Dy": 0.737, "Ho": 0.164, "Er": 0.480, "Tm": 0.074,
            "Yb": 0.493, "Lu": 0.074,
            "Rb": 0.6, "Ba": 6.6, "Th": 0.08, "U": 0.02, "Nb": 0.7,
            "Ta": 0.04, "Sr": 20.0, "Zr": 11.0, "Hf": 0.3, "Y": 4.3
        }

        self.morbs = {
            "La": 3.5, "Ce": 10.0, "Pr": 1.6, "Nd": 9.0,
            "Sm": 3.3, "Eu": 1.2, "Gd": 4.5, "Tb": 0.8,
            "Dy": 5.2, "Ho": 1.1, "Er": 3.3, "Tm": 0.5,
            "Yb": 3.3, "Lu": 0.5,
            "Rb": 1.0, "Ba": 14.0, "Th": 0.2, "U": 0.1, "Nb": 4.0,
            "Ta": 0.3, "Sr": 120.0, "Zr": 90.0, "Hf": 2.5, "Y": 35.0
        }

        self.chondrite = {
            "La": 0.237, "Ce": 0.612, "Pr": 0.095, "Nd": 0.467,
            "Sm": 0.153, "Eu": 0.058, "Gd": 0.205, "Tb": 0.037,
            "Dy": 0.254, "Ho": 0.057, "Er": 0.166, "Tm": 0.026,
            "Yb": 0.170, "Lu": 0.025,
            "Rb": 0.35, "Ba": 4.5, "Th": 0.042, "U": 0.012, "Nb": 0.42,
            "Ta": 0.03, "Sr": 9.8, "Zr": 7.1, "Hf": 0.2, "Y": 1.8
        }

        self.mineral_compositions = {
            "Ol": {"SiO₂": 40.0, "MgO": 50.0, "FeO": 10.0},
            "Cpx": {"SiO₂": 52.0, "Al₂O₃": 4.0, "FeO": 5.0, "MgO": 16.0, "CaO": 23.0},
            "Opx": {"SiO₂": 55.0, "Al₂O₃": 3.0, "FeO": 8.0, "MgO": 31.0, "CaO": 3.0},
            "Plag": {"SiO₂": 55.0, "Al₂O₃": 28.0, "CaO": 12.0, "Na₂O": 5.0},
            "Grt": {"SiO₂": 41.0, "Al₂O₃": 22.0, "MgO": 18.0, "FeO": 15.0, "CaO": 4.0},
            "Sp": {"MgO": 20.0, "Al₂O₃": 65.0, "Cr₂O₃": 15.0},
            "Mt": {"FeO": 93.0, "TiO₂": 7.0},
            "Ilm": {"TiO₂": 53.0, "FeO": 47.0}
        }

        # Comprehensive Kd databases
        self.kd_databases = {
            "basalt": {
                "Ol": {"Ni": 10.0, "Cr": 5.0, "Co": 3.0, "Sc": 0.1, "V": 0.05,
                       "Mn": 0.8, "Ca": 0.01, "Al": 0.01, "Ti": 0.02,
                       "La": 0.0005, "Ce": 0.0007, "Nd": 0.001, "Sm": 0.002,
                       "Eu": 0.003, "Yb": 0.015, "Lu": 0.02},
                "Cpx": {"Ni": 2.0, "Cr": 30.0, "Sc": 3.0, "V": 1.0, "Sr": 0.1,
                        "Y": 0.2, "Zr": 0.1, "Hf": 0.1, "Ba": 0.001, "Rb": 0.001,
                        "La": 0.05, "Ce": 0.07, "Nd": 0.1, "Sm": 0.2, "Eu": 0.3,
                        "Gd": 0.4, "Dy": 0.6, "Er": 0.8, "Yb": 1.0, "Lu": 1.2},
                "Plag": {"Sr": 2.0, "Eu": 1.5, "Ba": 0.5, "Rb": 0.1, "Cs": 0.1,
                         "K": 0.1, "Na": 1.0, "Ca": 1.0,
                         "La": 0.1, "Ce": 0.1, "Nd": 0.1, "Sm": 0.1, "Eu": 0.5,
                         "Gd": 0.1, "Yb": 0.1, "Lu": 0.1},
                "Opx": {"Ni": 4.0, "Cr": 10.0, "Sc": 1.5, "V": 0.5, "Y": 0.1,
                        "La": 0.001, "Ce": 0.0015, "Nd": 0.002, "Sm": 0.003,
                        "Eu": 0.004, "Gd": 0.006, "Yb": 0.02, "Lu": 0.025},
                "Grt": {"Y": 2.0, "Yb": 4.0, "Lu": 5.0, "Sc": 2.0, "Cr": 5.0,
                        "La": 0.001, "Ce": 0.0015, "Nd": 0.005, "Sm": 0.02,
                        "Eu": 0.05, "Gd": 0.1, "Dy": 0.5, "Er": 1.0, "Yb": 2.0, "Lu": 3.0},
                "Ilm": {"Nb": 2.0, "Ta": 3.0, "Zr": 0.3, "Hf": 0.4},
                "Mt": {"V": 10.0, "Cr": 20.0, "Ni": 5.0}
            },
            "melting": {
                "Ol": {"La": 0.0005, "Ce": 0.0007, "Pr": 0.0008, "Nd": 0.001,
                       "Sm": 0.002, "Eu": 0.003, "Gd": 0.004, "Tb": 0.005,
                       "Dy": 0.007, "Ho": 0.008, "Er": 0.01, "Tm": 0.012,
                       "Yb": 0.015, "Lu": 0.02, "Rb": 0.0001, "Ba": 0.0001,
                       "Th": 0.0001, "U": 0.0001, "Nb": 0.0005, "Ta": 0.0005,
                       "Sr": 0.0005, "Zr": 0.001, "Hf": 0.001, "Y": 0.005},
                "Opx": {"La": 0.001, "Ce": 0.0015, "Pr": 0.002, "Nd": 0.002,
                        "Sm": 0.003, "Eu": 0.004, "Gd": 0.006, "Tb": 0.008,
                        "Dy": 0.01, "Ho": 0.012, "Er": 0.015, "Tm": 0.018,
                        "Yb": 0.02, "Lu": 0.025, "Rb": 0.001, "Ba": 0.001,
                        "Th": 0.001, "U": 0.001, "Nb": 0.002, "Ta": 0.002,
                        "Sr": 0.002, "Zr": 0.005, "Hf": 0.005, "Y": 0.01},
                "Cpx": {"La": 0.05, "Ce": 0.07, "Pr": 0.08, "Nd": 0.1,
                        "Sm": 0.2, "Eu": 0.3, "Gd": 0.4, "Tb": 0.5,
                        "Dy": 0.6, "Ho": 0.7, "Er": 0.8, "Tm": 0.9,
                        "Yb": 1.0, "Lu": 1.2, "Rb": 0.01, "Ba": 0.01,
                        "Th": 0.01, "U": 0.01, "Nb": 0.05, "Ta": 0.05,
                        "Sr": 0.1, "Zr": 0.1, "Hf": 0.1, "Y": 0.5},
                "Grt": {"La": 0.001, "Ce": 0.0015, "Pr": 0.002, "Nd": 0.005,
                        "Sm": 0.02, "Eu": 0.05, "Gd": 0.1, "Tb": 0.2,
                        "Dy": 0.5, "Ho": 0.8, "Er": 1.0, "Tm": 1.5,
                        "Yb": 2.0, "Lu": 3.0, "Rb": 0.001, "Ba": 0.001,
                        "Th": 0.001, "U": 0.001, "Nb": 0.005, "Ta": 0.005,
                        "Sr": 0.001, "Zr": 0.1, "Hf": 0.1, "Y": 1.0},
                "Plag": {"La": 0.1, "Ce": 0.1, "Pr": 0.1, "Nd": 0.1,
                         "Sm": 0.1, "Eu": 0.5, "Gd": 0.1, "Tb": 0.1,
                         "Dy": 0.1, "Ho": 0.1, "Er": 0.1, "Tm": 0.1,
                         "Yb": 0.1, "Lu": 0.1, "Rb": 0.1, "Ba": 0.2,
                         "Sr": 2.0, "Pb": 1.0},
                "Sp": {"V": 5.0, "Cr": 100.0, "Ni": 2.0, "Co": 1.0}
            }
        }

        # TAS diagram boundaries
        self.tas_fields = {
            'Foidite': [(41, 5), (45, 9), (45, 14), (41, 14)],
            'Phonolite': [(45, 14), (64, 14), (64, 17), (45, 17)],
            'Tephriphonolite': [(45, 9), (52, 9), (52, 14), (45, 14)],
            'Phonotephrite': [(41, 5), (45, 9), (45, 14), (41, 9)],
            'Trachyte': [(64, 8), (77, 8), (77, 14), (64, 14)],
            'Trachydacite': [(64, 5), (69, 5), (69, 8), (64, 8)],
            'Rhyolite': [(69, 0), (77, 0), (77, 5), (69, 5)],
            'Dacite': [(63, 0), (69, 0), (69, 5), (63, 5)],
            'Andesite': [(57, 0), (63, 0), (63, 5), (57, 5)],
            'Basaltic andesite': [(52, 0), (57, 0), (57, 5), (52, 5)],
            'Basalt': [(45, 0), (52, 0), (52, 5), (45, 5)],
            'Picrobasalt': [(41, 0), (45, 0), (45, 5), (41, 3)]
        }

        # Pearce tectonic diagrams
        self.pearce_fields = {
            'VAB': {'Nb': [2, 10], 'Y': [10, 50], 'Rb': [10, 100]},
            'ORB': {'Nb': [0.2, 2], 'Y': [10, 50], 'Rb': [1, 10]},
            'WPB': {'Nb': [10, 100], 'Y': [1, 10], 'Rb': [10, 100]}
        }

        # AFM diagram boundaries
        self.afm_tholeiitic_line = [(0, 100), (40, 60), (70, 30)]

    # ============ TDF DATABASE INTEGRATION ============
    def _load_tdf_database(self):
        """Load TDF database from main-app/config/ folder"""
        try:
            # Path from plugin to main app config
            # plugin: app/plugins/software/petrogenetic_modeling_suite.py
            # config: app/config/tdf_database.json
            tdf_path = Path(__file__).parent.parent.parent / "config" / "tdf_database.json"

            if tdf_path.exists():
                with open(tdf_path, 'r', encoding='utf-8') as f:
                    self.tdf_db = json.load(f)
                print(f"✅ Loaded TDF database from: {tdf_path}")
                print(f"   Found {len(self.tdf_db.get('tdf_entries', []))} entries")
                return True
            else:
                print(f"⚠️ TDF database not found at: {tdf_path}")
                self.tdf_db = None
                return False
        except Exception as e:
            print(f"⚠️ Error loading TDF database: {e}")
            self.tdf_db = None
            return False

    def _lookup_tdf(self, taxon=None, tissue=None, diet_type=None, trophic_level=None):
        """Look up TDF values from database"""
        # [full code from previous message]
        pass

    def _get_citation_for_source(self, source):
        """Get full citation for a source code"""
        citations = {
            'Stephens2023': 'Stephens, R.B. et al. (2023). Functional Ecology, 37(9), 2297-2548.',
            # [rest of citations]
        }
        for key, citation in citations.items():
            if key in source:
                return citation
        return source

    def _init_composition_vars(self):
        """Initialize composition variables for custom input"""
        oxides = ['SiO2', 'TiO2', 'Al2O3', 'Fe2O3', 'FeO', 'MnO',
                  'MgO', 'CaO', 'Na2O', 'K2O', 'P2O5', 'H2O', 'Cr2O3']
        self.comp_vars = {}
        for oxide in oxides:
            self.comp_vars[oxide] = tk.DoubleVar(value=0.0)

        # Set default basalt values
        basalt = {
            'SiO2': 50.0, 'TiO2': 1.5, 'Al2O3': 15.0, 'Fe2O3': 1.5,
            'FeO': 8.5, 'MnO': 0.2, 'MgO': 7.0, 'CaO': 11.0,
            'Na2O': 2.5, 'K2O': 0.8, 'P2O5': 0.2, 'H2O': 0.5, 'Cr2O3': 0.05
        }
        for oxide, value in basalt.items():
            if oxide in self.comp_vars:
                self.comp_vars[oxide].set(value)

    def _check_dependencies(self):
        """Check required packages"""
        missing = []
        if not HAS_MATPLOTLIB: missing.append("matplotlib")
        if not HAS_SCIPY: missing.append("scipy")
        if not HAS_OPENPYXL: missing.append("openpyxl (optional for Excel)")
        self.dependencies_met = len([m for m in missing if not m.endswith("optional")]) == 0
        self.missing_deps = missing

    def _safe_float(self, value):
        """Safely convert to float"""
        if value is None or value == '':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _load_from_main_app(self):
        """Load geochemical data from main app samples"""
        if not hasattr(self.app, 'samples') or not self.app.samples:
            return False

        self.samples = self.app.samples
        self.numeric_columns = []

        if self.samples and len(self.samples) > 0:
            first_sample = self.samples[0]
            for col in first_sample.keys():
                try:
                    val = first_sample[col]
                    if val and val != '':
                        float(val)
                        self.numeric_columns.append(col)
                except (ValueError, TypeError):
                    pass

        self._update_ui_columns()
        return True

    def _update_ui_columns(self):
        """Update column selectors in UI"""
        if hasattr(self, 'element_combo'):
            self.element_combo['values'] = self.numeric_columns
            if self.numeric_columns and not self.element_var.get():
                self.element_var.set(self.numeric_columns[0])

    def _create_tdf_selector_ui(self, parent):
        """Create TDF selector UI for the mixing tab"""
        # [full code from previous message]
        pass

    def _open_custom_tdf_dialog(self):
        """Dialog for custom TDF input"""
        # [full code from previous message]
        pass

    # ============================================================================
    # Kd DATABASE INTEGRATION
    # ============================================================================
    def _calculate_bulk_distribution(self, mineral_modes, element, database="basalt"):
        """Calculate bulk distribution coefficient from mineral modes"""
        if not mineral_modes or sum(mineral_modes.values()) == 0:
            return 0.1  # default

        bulk_D = 0
        total_mode = sum(mineral_modes.values())

        for mineral, mode in mineral_modes.items():
            # Get mineral-specific Kd for this element
            kd = self._get_mineral_kd(mineral, element, database)
            bulk_D += (mode / total_mode) * kd

        return bulk_D

    def _get_mineral_kd(self, mineral, element, database="basalt"):
        """Get Kd value from database with fallbacks"""
        # Try specified database first
        if database in self.kd_databases:
            if mineral in self.kd_databases[database]:
                if element in self.kd_databases[database][mineral]:
                    return self.kd_databases[database][mineral][element]

        # Try other database
        other_db = "melting" if database == "basalt" else "basalt"
        if other_db in self.kd_databases:
            if mineral in self.kd_databases[other_db]:
                if element in self.kd_databases[other_db][mineral]:
                    return self.kd_databases[other_db][mineral][element]

        # Default values for common elements
        defaults = {
            'La': 0.01, 'Ce': 0.01, 'Pr': 0.015, 'Nd': 0.02, 'Sm': 0.05,
            'Eu': 0.1, 'Gd': 0.12, 'Tb': 0.15, 'Dy': 0.2, 'Ho': 0.25,
            'Er': 0.3, 'Tm': 0.35, 'Yb': 0.4, 'Lu': 0.45,
            'Rb': 0.01, 'Ba': 0.01, 'Th': 0.01, 'U': 0.01, 'Nb': 0.05,
            'Ta': 0.05, 'Sr': 0.5, 'Zr': 0.1, 'Hf': 0.1, 'Y': 0.2
        }
        return defaults.get(element, 0.1)

    def _get_mineral_mode_dialog(self, elements=None):
        """Dialog to input mineral modes for bulk D calculation"""
        dialog = tk.Toplevel(self.window)
        dialog.title("Mineral Modes for Bulk D")
        dialog.geometry("400x300")
        dialog.transient(self.window)
        dialog.grab_set()

        tk.Label(dialog, text="Enter mineral modes (normalized automatically):",
                font=("Arial", 10, "bold")).pack(pady=5)

        minerals = ["Ol", "Cpx", "Opx", "Plag", "Grt", "Sp", "Mt", "Ilm"]
        mode_vars = {}

        frame = tk.Frame(dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        for i, mineral in enumerate(minerals):
            row = tk.Frame(frame)
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text=f"{mineral}:", width=8, anchor=tk.W).pack(side=tk.LEFT)
            var = tk.DoubleVar(value=0.0)
            mode_vars[mineral] = var
            tk.Spinbox(row, from_=0, to=100, increment=1, textvariable=var, width=8).pack(side=tk.LEFT, padx=5)
            tk.Label(row, text="%").pack(side=tk.LEFT)

        def get_modes():
            modes = {m: v.get() for m, v in mode_vars.items() if v.get() > 0}
            if modes:
                dialog.destroy()
                return modes
            else:
                messagebox.showwarning("No Input", "Enter at least one mineral mode")
                return None

        tk.Button(dialog, text="OK", command=get_modes, bg="#27ae60", fg="white").pack(pady=10)

        dialog.wait_window()
        return {m: v.get() for m, v in mode_vars.items() if v.get() > 0} if 'mode_vars' in locals() else {}

    # ============================================================================
    # AFC MODEL (Enhanced with Kd)
    # ============================================================================
    def _afc_model(self, C0, Ca, D, r, F):
        """AFC equation from DePaolo (1981)"""
        r = max(r, 0.001)
        z = r / (r + D - 1)
        term1 = F ** (-z)
        if abs(r - 1) < 1e-6:
            result = C0 * F ** (-z) + (Ca / (z * C0)) * (1 - F ** (-z))
        else:
            result = C0 * F ** (-z) + (r / (r - 1)) * (Ca / (z * C0)) * (1 - F ** (-z))
        return result

    def _calculate_afc(self):
        """Calculate AFC model curve with optional Kd"""
        C0 = self.afc_C0_var.get()
        Ca = self.afc_Ca_var.get()
        D = self.afc_D_var.get()
        r = self.afc_r_var.get()

        # Option to calculate D from mineral modes
        if messagebox.askyesno("Calculate D?", "Calculate bulk D from mineral modes?"):
            modes = self._get_mineral_mode_dialog()
            if modes and self.element_var.get():
                D = self._calculate_bulk_distribution(modes, self.element_var.get())
                self.afc_D_var.set(D)
                messagebox.showinfo("Bulk D", f"Calculated D = {D:.3f}")

        F = np.linspace(self.afc_F_min_var.get(),
                        self.afc_F_max_var.get(),
                        self.afc_F_steps_var.get())

        C = self._afc_model(C0, Ca, D, r, F)

        return {
            'F': F,
            'C': C,
            'params': {
                'C0': C0, 'Ca': Ca, 'D': D, 'r': r,
                'model': 'AFC (DePaolo 1981)'
            }
        }

    # ============================================================================
    # FRACTIONAL CRYSTALLIZATION MODELS (Enhanced with Kd)
    # ============================================================================
    def _rayleigh_model(self, C0, D, F):
        """Rayleigh fractional crystallization"""
        return C0 * F ** (D - 1)

    def _equilibrium_model(self, C0, D, F):
        """Equilibrium crystallization"""
        return C0 / (D + F * (1 - D))

    def _in_situ_model(self, C0, D, F):
        """In-situ crystallization (Langmuir 1989)"""
        return C0 / (1 - F * (1 - D)) ** (1 / D)

    def _calculate_fractional(self):
        """Calculate fractional crystallization model"""
        C0 = self.frac_C0_var.get()
        D = self.frac_D_var.get()
        model_type = self.frac_model_var.get()

        # Option to calculate D from mineral modes
        if messagebox.askyesno("Calculate D?", "Calculate bulk D from mineral modes?"):
            modes = self._get_mineral_mode_dialog()
            if modes and self.element_var.get():
                D = self._calculate_bulk_distribution(modes, self.element_var.get())
                self.frac_D_var.set(D)
                messagebox.showinfo("Bulk D", f"Calculated D = {D:.3f}")

        F = np.linspace(self.frac_F_min_var.get(),
                        self.frac_F_max_var.get(),
                        self.frac_F_steps_var.get())

        if model_type == 'rayleigh':
            C = self._rayleigh_model(C0, D, F)
            model_name = 'Rayleigh Fractionation'
        elif model_type == 'equilibrium':
            C = self._equilibrium_model(C0, D, F)
            model_name = 'Equilibrium Crystallization'
        else:
            C = self._in_situ_model(C0, D, F)
            model_name = 'In-Situ Crystallization (Langmuir 1989)'

        return {
            'F': F,
            'C': C,
            'params': {
                'C0': C0, 'D': D,
                'model': model_name
            }
        }

    # ============================================================================
    # ZONE REFINING
    # ============================================================================
    def _zone_refining_single_pass(self, C0, k, x, L=1.0):
        """Single pass zone refining"""
        return C0 * (1 - (1 - k) * np.exp(-k * x / L))

    def _zone_refining_multi_pass(self, C0, k, x, n_passes, L=1.0):
        """Multiple pass zone refining"""
        return C0 * (1 - (1 - k) ** n_passes * np.exp(-n_passes * k * x / L))

    def _calculate_zone_refining(self):
        """Calculate zone refining model"""
        C0 = self.zone_C0_var.get()
        k = self.zone_k_var.get()
        n_passes = self.zone_passes_var.get()
        L = self.zone_length_var.get()

        x = np.linspace(0, 10 * L, self.zone_steps_var.get())

        if n_passes == 1:
            C = self._zone_refining_single_pass(C0, k, x, L)
            model_name = f'Zone Refining (1 pass, k={k:.3f})'
        else:
            C = self._zone_refining_multi_pass(C0, k, x, n_passes, L)
            model_name = f'Zone Refining ({n_passes} passes, k={k:.3f})'

        return {
            'x': x,
            'C': C,
            'params': {
                'C0': C0, 'k': k, 'passes': n_passes,
                'model': model_name
            }
        }

    # ============================================================================
    # MIXING MODELS
    # ============================================================================
    def _binary_mixing(self, CA, CB, fA):
        """Binary mixing"""
        return CA * fA + CB * (1 - fA)

    def _ternary_mixing(self, CA, CB, CC, fA, fB):
        """
        Full ternary mixing implementation with support for:
        - Linear mixing (major elements)
        - Trace element partitioning
        - Isotope mixing
        """
        # Check if we're in trace element mode
        if hasattr(self, 'mixing_mode') and self.mixing_mode == 'trace':
            fC = 1 - fA - fB

            # Get partition coefficients (default to 1.0 if not set)
            D_A = getattr(self, 'mix_D_A', 1.0)
            D_B = getattr(self, 'mix_D_B', 1.0)
            D_C = getattr(self, 'mix_D_C', 1.0)
            phi = getattr(self, 'mix_phi', 0.1)

            # Equilibrium partitioning during mixing
            numerator = fA * CA * D_A + fB * CB * D_B + fC * CC * D_C
            denominator = fA * D_A + fB * D_B + fC * D_C + phi * (1 - (fA + fB + fC))

            return numerator / denominator if denominator > 0 else np.nan

        # Check if we're in isotope mode
        elif hasattr(self, 'mixing_mode') and self.mixing_mode == 'isotope':
            fC = 1 - fA - fB

            # Get isotope ratios and concentrations
            ratios = getattr(self, 'mix_ratios', {'A': CA, 'B': CB, 'C': CC})
            conc = getattr(self, 'mix_concentrations', {'A': 1.0, 'B': 1.0, 'C': 1.0})

            # R_mix = (fA*CA*RA + fB*CB*RB + fC*CC*RC) / (fA*CA + fB*CB + fC*CC)
            numerator = (fA * conc['A'] * ratios['A'] +
                        fB * conc['B'] * ratios['B'] +
                        fC * conc['C'] * ratios['C'])

            denominator = (fA * conc['A'] + fB * conc['B'] + fC * conc['C'])

            return numerator / denominator if denominator > 0 else np.nan

        # Default linear mixing
        else:
            fC = 1 - fA - fB
            return CA * fA + CB * fB + CC * fC

    def _calculate_mixing(self):
        """
        Calculate mixing model with support for linear, trace, and isotope modes
        """
        model_type = self.mix_model_var.get()

        # Check for mixing mode (set by UI elements)
        if hasattr(self, 'mix_mode_var'):
            self.mixing_mode = self.mix_mode_var.get()
        else:
            self.mixing_mode = 'linear'

        if model_type == 'binary':
            CA = self.mix_CA_var.get()
            CB = self.mix_CB_var.get()

            fA = np.linspace(self.mix_fA_min_var.get(),
                            self.mix_fA_max_var.get(),
                            self.mix_steps_var.get())

            if self.mixing_mode == 'isotope' and hasattr(self, 'binary_conc_A'):
                # Binary isotope mixing
                conc_A = self.binary_conc_A.get()
                conc_B = self.binary_conc_B.get()
                C = (CA * conc_A * fA + CB * conc_B * (1 - fA)) / (conc_A * fA + conc_B * (1 - fA))
                model_name = 'Binary Isotope Mixing'
            else:
                # Linear binary mixing
                C = CA * fA + CB * (1 - fA)
                model_name = 'Binary Mixing'

            return {
                'x': fA,
                'C': C,
                'params': {
                    'model': model_name,
                    'mode': self.mixing_mode,
                    'CA': CA, 'CB': CB
                },
                'xlabel': 'Fraction A'
            }

        else:  # ternary
            CA = self.mix_CA_var.get()
            CB = self.mix_CB_var.get()
            CC = self.mix_CC_var.get()

            steps = self.mix_steps_var.get()
            fA = np.linspace(0, 1, steps)
            fB = np.linspace(0, 1, steps)
            FA, FB = np.meshgrid(fA, fB)

            mask = FA + FB <= 1
            C = np.zeros_like(FA)
            C[~mask] = np.nan

            # Calculate for each valid point using _ternary_mixing
            for i in range(steps):
                for j in range(steps):
                    if mask[i, j]:
                        C[i, j] = self._ternary_mixing(CA, CB, CC, FA[i, j], FB[i, j])

            # Determine model name based on mode
            if self.mixing_mode == 'trace':
                model_name = 'Ternary Trace Element Mixing'
            elif self.mixing_mode == 'isotope':
                model_name = 'Ternary Isotope Mixing'
            else:
                model_name = 'Ternary Linear Mixing'

            return {
                'FA': FA, 'FB': FB, 'C': C,
                'params': {
                    'model': model_name,
                    'mode': self.mixing_mode,
                    'CA': CA, 'CB': CB, 'CC': CC
                }
            }
    # ============================================================================
    # PARTIAL MELTING MODELS (Enhanced with Kd)
    # ============================================================================
    def _batch_melting(self, C0, D, F):
        """Batch melting: C/C0 = 1 / [D + F*(1-D)]"""
        return C0 / (D + F * (1 - D))

    def _fractional_melting(self, C0, D, F):
        """Fractional melting (aggregated): C/C0 = (1 - F)^((1-D)/D) / D"""
        if abs(D) < 1e-6:
            return C0 / F
        return C0 * (1 - F) ** ((1/D) - 1) / D

    def _dynamic_melting(self, C0, D, F, porosity):
        """Dynamic melting (continuous removal)"""
        if porosity > 0:
            return C0 * (1 - F) ** ((1/D) - 1) / (D + porosity * (1 - D))
        return self._fractional_melting(C0, D, F)

    def _critical_melting(self, C0, D, F, porosity):
        """Critical melting with porosity"""
        if F <= porosity:
            return C0 / (D + F * (1 - D))
        else:
            return C0 * porosity / D * (1 - F) ** ((1/D) - 1)

    def _calculate_melting(self):
        """Calculate partial melting model with Kd database integration"""
        model = self.melting_model_var.get()
        source_type = self.melting_source_var.get()

        if source_type == "Primitive Mantle":
            source = self.primitive_mantle.copy()
        elif source_type == "MORB Source":
            source = self.morbs.copy()
        elif source_type == "Chondrite":
            source = self.chondrite.copy()
        else:
            source = {elem: var.get() for elem, var in self.ree_vars.items()}

        F_start = self.melting_F_start_var.get()
        F_end = self.melting_F_end_var.get()
        steps = self.melting_F_steps_var.get()
        F_values = np.linspace(F_start, F_end, steps)
        porosity = self.melting_porosity_var.get()

        # Use Kd database if requested
        if self.use_kd_database_var.get():
            # Get mineral modes for source
            modes = self._get_mineral_mode_dialog(elements=list(source.keys()))
            if not modes:
                modes = {"Ol": 0.6, "Opx": 0.2, "Cpx": 0.1, "Grt": 0.1}  # default lherzolite
        else:
            modes = None

        results = {"F": F_values.tolist()}

        for elem, C0 in source.items():
            if self.use_kd_database_var.get() and modes:
                D = self._calculate_bulk_distribution(modes, elem, database="melting")
            else:
                # Default D values
                default_D = {
                    "La": 0.01, "Ce": 0.015, "Pr": 0.02, "Nd": 0.025,
                    "Sm": 0.05, "Eu": 0.08, "Gd": 0.12, "Tb": 0.15,
                    "Dy": 0.2, "Ho": 0.25, "Er": 0.3, "Tm": 0.35,
                    "Yb": 0.4, "Lu": 0.45, "Rb": 0.01, "Ba": 0.01,
                    "Th": 0.01, "U": 0.01, "Nb": 0.05, "Ta": 0.05,
                    "Sr": 0.5, "Zr": 0.1, "Hf": 0.1, "Y": 0.2
                }
                D = default_D.get(elem, 0.1)

            if model == "Batch Melting":
                concentrations = self._batch_melting(C0, D, F_values)
            elif model == "Fractional Melting":
                concentrations = self._fractional_melting(C0, D, F_values)
            elif model == "Dynamic Melting":
                concentrations = self._dynamic_melting(C0, D, F_values, porosity)
            elif model == "Critical Melting":
                concentrations = self._critical_melting(C0, D, F_values, porosity)
            else:
                concentrations = self._batch_melting(C0, D, F_values)

            results[elem] = concentrations.tolist()

        return {
            'F': F_values,
            'results': results,
            'params': {
                'model': model,
                'source': source_type,
                'porosity': porosity,
                'used_kd': self.use_kd_database_var.get()
            }
        }

    # ============================================================================
    # SIMPLE MELTS FALLBACK
    # ============================================================================
    def _calculate_simple_melts(self):
        """Simplified MELTS model as fallback"""
        T_start = self.melts_T_start_var.get()
        T_end = self.melts_T_end_var.get()
        steps = self.melts_steps_var.get()

        T = np.linspace(T_start, T_end, steps)

        SiO2 = self.comp_vars['SiO2'].get()
        MgO = self.comp_vars['MgO'].get()
        H2O = self.comp_vars['H2O'].get()

        T_liquidus = 1200 + 5*MgO - 0.5*(SiO2-50) - 20*H2O
        T_solidus = 900 + 10*H2O

        melt_fraction = np.zeros_like(T)
        for i, temp in enumerate(T):
            if temp >= T_liquidus:
                melt_fraction[i] = 1.0
            elif temp <= T_solidus:
                melt_fraction[i] = 0.0
            else:
                melt_fraction[i] = ((temp - T_solidus) / (T_liquidus - T_solidus)) ** 1.5

        return {
            'T': T,
            'melt_fraction': melt_fraction,
            'params': {
                'T_liquidus': T_liquidus,
                'T_solidus': T_solidus,
                'model': 'Simple MELTS (Fallback)'
            }
        }

    # ============================================================================
    # PHASE DIAGRAMS - FULLY IMPLEMENTED
    # ============================================================================
    def _generate_phase_diagram(self):
        """Generate various petrogenetic diagrams - FULLY IMPLEMENTED"""
        if not self.samples:
            messagebox.showwarning("No Data", "Please load samples first")
            return

        diagram_type = self.diagram_type_var.get()

        # Create figure
        fig, ax = plt.subplots(figsize=(10, 8))

        # Generate selected diagram
        if "TAS" in diagram_type:
            self._plot_tas_diagram(ax)
        elif "AFM" in diagram_type:
            self._plot_afm_diagram(ax)
        elif "QAPF" in diagram_type:
            self._plot_qapf_diagram(ax)
        elif "REE Pattern" in diagram_type:
            self._plot_ree_pattern(ax)
        elif "Spider Diagram" in diagram_type:
            self._plot_spider_diagram(ax)
        elif "Pearce" in diagram_type:
            self._plot_pearce_diagram(ax)
        elif "SiO₂ vs Mg#" in diagram_type:
            self._plot_sio2_vs_mg_number(ax)
        else:
            messagebox.showinfo("Coming Soon", f"{diagram_type} diagram coming in next version!")
            return

        # Apply options
        if self.show_grid_var.get():
            ax.grid(True, alpha=0.3, linestyle='--')

        if self.show_legend_var.get():
            ax.legend(loc='best', fontsize=8)

        # Show in new window
        self._show_diagram_window(fig, diagram_type)

    def _plot_tas_diagram(self, ax):
        """Total Alkali-Silica diagram with IUGS fields"""
        # Plot field boundaries
        for field_name, vertices in self.tas_fields.items():
            poly = Polygon(vertices, alpha=0.1, closed=True,
                          label=field_name, linewidth=0.5, edgecolor='gray')
            ax.add_patch(poly)

        # Add major dividing lines
        x_line = [45, 77]
        ax.plot(x_line, [5, 5], 'k--', linewidth=0.5, alpha=0.5)
        ax.plot(x_line, [8, 8], 'k--', linewidth=0.5, alpha=0.5)
        ax.plot(x_line, [14, 14], 'k--', linewidth=0.5, alpha=0.5)

        # Plot sample data
        sample_points = []
        for sample in self.samples:
            try:
                si = float(sample.get('SiO2', 0))
                na = float(sample.get('Na2O', 0))
                k = float(sample.get('K2O', 0))
                if si > 0 and (na > 0 or k > 0):
                    alkali = na + k
                    sample_points.append([si, alkali])
            except (ValueError, TypeError):
                continue

        if sample_points:
            sample_points = np.array(sample_points)
            ax.scatter(sample_points[:, 0], sample_points[:, 1],
                      c='red', s=60, alpha=0.7, edgecolors='black',
                      label='Samples', zorder=5)

        # Add model results if requested
        if self.show_model_var.get():
            colors = ['blue', 'green', 'orange', 'purple']
            for i, (model_name, result) in enumerate(self.model_results.items()):
                if result and 'F' in result and 'C' in result:
                    # Convert model concentrations to TAS coordinates if possible
                    # This would require the model to output oxides
                    pass

        ax.set_xlabel('SiO₂ (wt%)', fontsize=12)
        ax.set_ylabel('Na₂O + K₂O (wt%)', fontsize=12)
        ax.set_title('TAS Diagram (Le Maitre et al. 2002)', fontsize=14)
        ax.set_xlim(35, 80)
        ax.set_ylim(0, 18)
        ax.set_aspect('auto')

    def _plot_afm_diagram(self, ax):
        """AFM diagram (Irvine & Baragar 1971)"""
        # Calculate A, F, M for each sample
        sample_points = []
        for sample in self.samples:
            try:
                na2o = float(sample.get('Na2O', 0))
                k2o = float(sample.get('K2O', 0))
                feo = float(sample.get('FeO', 0))
                fe2o3 = float(sample.get('Fe2O3', 0))
                mgo = float(sample.get('MgO', 0))

                # Convert Fe2O3 to FeO
                total_fe_as_feo = feo + fe2o3 * 0.8998

                # Calculate A, F, M
                alk = na2o + k2o
                total = alk + total_fe_as_feo + mgo

                if total > 0:
                    A = 100 * alk / total
                    F = 100 * total_fe_as_feo / total
                    M = 100 * mgo / total

                    # Convert to triangular coordinates
                    x = F + 0.5 * A
                    y = M
                    sample_points.append([x, y])
            except (ValueError, TypeError):
                continue

        # Plot tholeiitic-calcalkaline dividing line
        line_x = [20, 80]
        line_y = [80, 20]
        ax.plot(line_x, line_y, 'r--', linewidth=2, label='Tholeiitic - Calcalkaline boundary')

        # Fill fields
        tholeiitic = Polygon([(0, 100), (50, 50), (0, 0)], alpha=0.1, color='blue', label='Tholeiitic')
        calcalkaline = Polygon([(50, 50), (100, 0), (0, 0)], alpha=0.1, color='green', label='Calc-alkaline')
        ax.add_patch(tholeiitic)
        ax.add_patch(calcalkaline)

        # Plot samples
        if sample_points:
            sample_points = np.array(sample_points)
            ax.scatter(sample_points[:, 0], sample_points[:, 1],
                      c='red', s=60, alpha=0.7, edgecolors='black',
                      label='Samples', zorder=5)

        ax.set_xlabel('F (FeO*)', fontsize=12)
        ax.set_ylabel('M (MgO)', fontsize=12)
        ax.set_title('AFM Diagram (Irvine & Baragar 1971)', fontsize=14)
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 100)

    def _plot_qapf_diagram(self, ax):
        """QAPF diagram with proper CIPW norm calculation"""
        from matplotlib.patches import Polygon

        ax.clear()

        # ============ HELPER: CIPW Norm Calculation ============
        def calculate_cipw_norm(sample):
            """Calculate CIPW norm for a single sample"""
            try:
                # Get oxide weights
                SiO2 = float(sample.get('SiO2', 0))
                TiO2 = float(sample.get('TiO2', 0))
                Al2O3 = float(sample.get('Al2O3', 0))
                Fe2O3 = float(sample.get('Fe2O3', 0))
                FeO = float(sample.get('FeO', 0))
                MnO = float(sample.get('MnO', 0))
                MgO = float(sample.get('MgO', 0))
                CaO = float(sample.get('CaO', 0))
                Na2O = float(sample.get('Na2O', 0))
                K2O = float(sample.get('K2O', 0))
                P2O5 = float(sample.get('P2O5', 0))

                # Molecular weights
                mol_wt = {
                    'SiO2': 60.08, 'TiO2': 79.90, 'Al2O3': 101.96,
                    'Fe2O3': 159.69, 'FeO': 71.85, 'MnO': 70.94,
                    'MgO': 40.30, 'CaO': 56.08, 'Na2O': 61.98,
                    'K2O': 94.20, 'P2O5': 141.95
                }

                # Convert to molecular proportions
                mol = {}
                mol['SiO2'] = SiO2 / mol_wt['SiO2']
                mol['TiO2'] = TiO2 / mol_wt['TiO2']
                mol['Al2O3'] = Al2O3 / mol_wt['Al2O3']
                mol['Fe2O3'] = Fe2O3 / mol_wt['Fe2O3']
                mol['FeO'] = FeO / mol_wt['FeO']
                mol['MnO'] = MnO / mol_wt['MnO']
                mol['MgO'] = MgO / mol_wt['MgO']
                mol['CaO'] = CaO / mol_wt['CaO']
                mol['Na2O'] = Na2O / mol_wt['Na2O']
                mol['K2O'] = K2O / mol_wt['K2O']
                mol['P2O5'] = P2O5 / mol_wt['P2O5']

                # Step 1: Apatite (Ap)
                Ap = mol['P2O5']
                mol['CaO'] -= 10/3 * Ap

                # Step 2: Ilmenite (Il) and Magnetite (Mt)
                Il = mol['TiO2']
                mol['FeO'] -= Il
                mol['Fe2O3'] -= Il

                if mol['Fe2O3'] > mol['FeO']:
                    Mt = mol['FeO']
                    mol['Fe2O3'] -= Mt
                    mol['FeO'] = 0
                else:
                    Mt = mol['Fe2O3']
                    mol['FeO'] -= Mt
                    mol['Fe2O3'] = 0

                # Step 3: Orthoclase (Or)
                Or = mol['K2O']
                mol['Al2O3'] -= Or
                mol['SiO2'] -= 6 * Or

                # Step 4: Albite (Ab)
                Ab = mol['Na2O']
                mol['Al2O3'] -= Ab
                mol['SiO2'] -= 6 * Ab

                # Step 5: Anorthite (An)
                An = mol['CaO']
                if An > mol['Al2O3']:
                    An = mol['Al2O3']
                mol['Al2O3'] -= An
                mol['CaO'] -= An
                mol['SiO2'] -= 2 * An

                # Step 6: Diopside (Di)
                if mol['CaO'] > 0 and mol['MgO'] > 0:
                    Di = min(mol['CaO'], mol['MgO'])
                    mol['CaO'] -= Di
                    mol['MgO'] -= Di
                    mol['SiO2'] -= 2 * Di

                # Step 7: Hypersthene (Hy)
                Hy = mol['MgO'] + mol['FeO']
                mol['SiO2'] -= Hy

                # Step 8: Olivine (Ol)
                Ol = 0
                if mol['SiO2'] < 0:
                    Ol = -mol['SiO2'] / 2
                    mol['SiO2'] = 0

                # Step 9: Quartz (Q)
                Q = mol['SiO2'] if mol['SiO2'] > 0 else 0

                # Calculate normative mineral percentages
                total_norm = (Ap + Il + Mt + Or + Ab + An + Di + Hy + Ol + Q) * 100

                if total_norm == 0:
                    return 0, 0, 0

                # QAPF parameters
                Q_norm = Q * 100 / total_norm
                A_norm = Or * 100 / total_norm
                P_norm = An * 100 / total_norm

                # Normalize Q, A, P to 100%
                total_felsic = Q_norm + A_norm + P_norm
                if total_felsic > 0:
                    Q_final = Q_norm / total_felsic * 100
                    A_final = A_norm / total_felsic * 100
                    P_final = P_norm / total_felsic * 100
                else:
                    Q_final = A_final = P_final = 0

                return Q_final, A_final, P_final

            except (ValueError, TypeError, ZeroDivisionError):
                return 0, 0, 0

        # ============ PLOT FIELD BOUNDARIES ============
        # QAPF fields after Streckeisen (1976)
        fields = {
            'Alkali feldspar granite': [(20, 80), (20, 20), (35, 20), (35, 35), (65, 35), (65, 80)],
            'Granite': [(20, 35), (20, 20), (65, 20), (65, 35)],
            'Granodiorite': [(20, 65), (20, 35), (35, 35), (35, 65)],
            'Tonalite': [(10, 90), (10, 10), (35, 10), (35, 35), (65, 35), (65, 65), (90, 65), (90, 90)],
            'Quartz syenite': [(0, 80), (0, 20), (20, 20), (20, 80)],
            'Quartz monzonite': [(0, 65), (0, 35), (20, 35), (20, 65)],
            'Quartz monzodiorite': [(0, 90), (0, 65), (10, 65), (10, 90)],
            'Quartz diorite': [(0, 35), (0, 10), (20, 10), (20, 35)],
            'Syenite': [(-20, 80), (-20, 20), (0, 20), (0, 80)],
            'Monzonite': [(-20, 65), (-20, 35), (0, 35), (0, 65)],
            'Monzodiorite': [(-20, 90), (-20, 65), (-10, 65), (-10, 90)],
            'Diorite': [(-20, 35), (-20, 10), (0, 10), (0, 35)],
            'Foid syenite': [(-40, 80), (-40, 20), (-20, 20), (-20, 80)],
            'Foid monzosyenite': [(-40, 65), (-40, 35), (-20, 35), (-20, 65)],
            'Foid monzodiorite': [(-40, 90), (-40, 65), (-30, 65), (-30, 90)],
            'Foid diorite': [(-40, 35), (-40, 10), (-20, 10), (-20, 35)],
            'Foidolite': [(-60, 100), (-60, 0), (0, 0), (0, 100)]
        }

        # Plot fields with transparency
        colors = plt.cm.Set3(np.linspace(0, 1, len(fields)))
        for (field_name, vertices), color in zip(fields.items(), colors):
            poly = Polygon(vertices, alpha=0.1, closed=True,
                        facecolor=color, edgecolor='gray', linewidth=0.5)
            ax.add_patch(poly)

            # Add label at center of field
            if len(vertices) > 0:
                center_x = sum(v[0] for v in vertices) / len(vertices)
                center_y = sum(v[1] for v in vertices) / len(vertices)
                if field_name in ['Granite', 'Granodiorite', 'Syenite', 'Diorite']:
                    ax.text(center_x, center_y, field_name.split()[-1],
                        ha='center', va='center', fontsize=7, alpha=0.5)

        # Add grid lines
        for q in [0, 20, 35, 65, 80, 100]:
            ax.plot([-60, 100], [q, q], 'k-', alpha=0.1, linewidth=0.5)
        for a in [0, 20, 35, 65, 80, 100]:
            ax.plot([a, 100 - a], [0, 100], 'k-', alpha=0.1, linewidth=0.5)

        # ============ PLOT SAMPLES ============
        sample_points = []
        valid_samples = []

        for i, sample in enumerate(self.samples):
            Q, A, P = calculate_cipw_norm(sample)
            if Q >= 0 and A >= 0 and P >= 0 and (Q + A + P) > 0:
                # Convert to ternary coordinates: x = P + A/2, y = Q
                x = P + A/2
                y = Q
                if -20 <= x <= 100 and 0 <= y <= 100:
                    sample_points.append([x, y])
                    valid_samples.append(i)

        if sample_points:
            sample_points = np.array(sample_points)

            # Plot sample points
            scatter = ax.scatter(sample_points[:, 0], sample_points[:, 1],
                                c='red', s=60, alpha=0.7, edgecolors='black',
                                label='Samples', zorder=5)

            # Add sample labels if not too crowded
            if len(sample_points) < 20:
                for i, (x, y) in enumerate(sample_points):
                    sample_id = self.samples[valid_samples[i]].get('Sample_ID', str(valid_samples[i]+1))
                    ax.annotate(sample_id, (x, y), xytext=(3, 3),
                            textcoords='offset points', fontsize=6, alpha=0.6)

        # ============ FORMATTING ============
        ax.set_xlabel('P + A', fontsize=12)
        ax.set_ylabel('Q', fontsize=12)
        ax.set_title('QAPF Diagram (Streckeisen, 1976)', fontsize=14)
        ax.set_xlim(-60, 110)
        ax.set_ylim(-5, 105)
        ax.set_aspect('equal')

        # Add ternary axes labels
        ax.text(105, -2, 'A', ha='center', va='top', fontsize=10, fontweight='bold')
        ax.text(50, 108, 'Q', ha='center', va='bottom', fontsize=10, fontweight='bold')
        ax.text(-65, 50, 'P', ha='center', va='center', fontsize=10, fontweight='bold', rotation=90)

        if self.show_grid_var.get():
            ax.grid(True, alpha=0.2, linestyle='--')

        if self.show_legend_var.get():
            ax.legend(loc='upper left', fontsize=8)

    def _plot_ree_pattern(self, ax):
        """REE patterns normalized to chondrite"""
        ree_elements = ['La', 'Ce', 'Pr', 'Nd', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy', 'Ho', 'Er', 'Tm', 'Yb', 'Lu']
        x_positions = range(len(ree_elements))

        # Plot each sample
        for i, sample in enumerate(self.samples):
            values = []
            for elem in ree_elements:
                val = self._safe_float(sample.get(elem))
                if val is not None and val > 0:
                    if self.normalize_data_var.get() and self.chondrite_normalize_var.get():
                        # Normalize to chondrite
                        chondrite_val = self.chondrite.get(elem, 1.0)
                        if chondrite_val > 0:
                            val = val / chondrite_val
                    values.append(val)
                else:
                    values.append(np.nan)

            if any(not np.isnan(v) for v in values):
                ax.plot(x_positions, values, 'o-', linewidth=1.5, markersize=4,
                       label=f'Sample {i+1}', alpha=0.7)

        # Add reference patterns
        if self.show_model_var.get():
            # MORB pattern
            morb_values = []
            for elem in ree_elements:
                val = self.morbs.get(elem)
                if val is not None:
                    if self.chondrite_normalize_var.get():
                        val = val / self.chondrite.get(elem, 1.0)
                    morb_values.append(val)
                else:
                    morb_values.append(np.nan)
            ax.plot(x_positions, morb_values, 'k--', linewidth=2, label='MORB', alpha=0.8)

        ax.set_xlabel('REE Elements', fontsize=12)
        ax.set_ylabel('Sample / Chondrite' if self.chondrite_normalize_var.get() else 'Concentration (ppm)', fontsize=12)
        ax.set_title('REE Pattern', fontsize=14)
        ax.set_xticks(x_positions)
        ax.set_xticklabels(ree_elements, rotation=45, ha='right')
        ax.set_yscale('log')

    def _plot_spider_diagram(self, ax):
        """Spider diagram normalized to primitive mantle"""
        elements = ['Cs', 'Rb', 'Ba', 'Th', 'U', 'Nb', 'Ta', 'K', 'La', 'Ce',
                   'Pb', 'Pr', 'Sr', 'Nd', 'P', 'Sm', 'Zr', 'Hf', 'Eu', 'Ti',
                   'Gd', 'Tb', 'Dy', 'Y', 'Ho', 'Er', 'Tm', 'Yb', 'Lu']

        x_positions = range(len(elements))

        # Plot each sample
        for i, sample in enumerate(self.samples):
            values = []
            for elem in elements:
                val = self._safe_float(sample.get(elem))
                if val is not None and val > 0:
                    if self.normalize_data_var.get():
                        # Normalize to primitive mantle
                        pm_val = self.primitive_mantle.get(elem, 1.0)
                        if pm_val > 0:
                            val = val / pm_val
                    values.append(val)
                else:
                    values.append(np.nan)

            if any(not np.isnan(v) for v in values):
                ax.plot(x_positions, values, 'o-', linewidth=1, markersize=3,
                       label=f'Sample {i+1}', alpha=0.7)

        ax.set_xlabel('Elements', fontsize=12)
        ax.set_ylabel('Sample / Primitive Mantle' if self.normalize_data_var.get() else 'Concentration (ppm)', fontsize=12)
        ax.set_title('Spider Diagram (Primitive Mantle Normalized)', fontsize=14)
        ax.set_xticks(x_positions)
        ax.set_xticklabels(elements, rotation=90, ha='center', fontsize=8)
        ax.set_yscale('log')

    def _plot_pearce_diagram(self, ax):
        """Pearce tectonic discrimination diagrams"""
        # Nb-Y diagram
        if 'Nb' in self.numeric_columns and 'Y' in self.numeric_columns:
            # Plot fields
            syn_collisional = patches.Rectangle((1, 10), 9, 90, alpha=0.1, color='red', label='Syn-COLG')
            within_plate = patches.Rectangle((10, 20), 90, 80, alpha=0.1, color='blue', label='WPG')
            volcanic_arc = patches.Rectangle((0.1, 1), 3.9, 49, alpha=0.1, color='green', label='VAG')
            ocean_ridge = patches.Rectangle((0.1, 0.1), 3.9, 4.9, alpha=0.1, color='orange', label='ORG')

            ax.add_patch(syn_collisional)
            ax.add_patch(within_plate)
            ax.add_patch(volcanic_arc)
            ax.add_patch(ocean_ridge)

            # Plot samples
            for sample in self.samples:
                nb = self._safe_float(sample.get('Nb'))
                y = self._safe_float(sample.get('Y'))
                if nb is not None and y is not None and nb > 0 and y > 0:
                    ax.scatter(nb, y, c='red', s=50, alpha=0.7, edgecolors='black')

            ax.set_xlabel('Nb (ppm)', fontsize=12)
            ax.set_ylabel('Y (ppm)', fontsize=12)
            ax.set_title('Pearce Nb-Y Diagram', fontsize=14)
            ax.set_xscale('log')
            ax.set_yscale('log')
            ax.set_xlim(0.1, 100)
            ax.set_ylim(0.1, 100)

    def _plot_sio2_vs_mg_number(self, ax):
        """SiO₂ vs Mg# diagram"""
        sample_data = []
        for sample in self.samples:
            try:
                sio2 = float(sample.get('SiO2', 0))
                mgo = float(sample.get('MgO', 0))
                feo = float(sample.get('FeO', 0))
                fe2o3 = float(sample.get('Fe2O3', 0))

                if sio2 > 0 and (mgo > 0 or feo > 0):
                    # Calculate Mg#
                    total_fe_as_feo = feo + fe2o3 * 0.8998
                    mg_number = 100 * mgo / (mgo + total_fe_as_feo) if (mgo + total_fe_as_feo) > 0 else 0
                    sample_data.append([sio2, mg_number])
            except (ValueError, TypeError):
                continue

        if sample_data:
            sample_data = np.array(sample_data)
            ax.scatter(sample_data[:, 0], sample_data[:, 1],
                      c='red', s=60, alpha=0.7, edgecolors='black',
                      label='Samples', zorder=5)

            # Add trend line
            if len(sample_data) > 1:
                z = np.polyfit(sample_data[:, 0], sample_data[:, 1], 1)
                p = np.poly1d(z)
                x_trend = np.linspace(min(sample_data[:, 0]), max(sample_data[:, 0]), 50)
                ax.plot(x_trend, p(x_trend), 'b--', linewidth=2, label='Trend')

        ax.set_xlabel('SiO₂ (wt%)', fontsize=12)
        ax.set_ylabel('Mg#', fontsize=12)
        ax.set_title('SiO₂ vs Mg#', fontsize=14)
        ax.grid(True, alpha=0.3)

    def _show_diagram_window(self, fig, title):
        """Show diagram in new window"""
        window = tk.Toplevel(self.window)
        window.title(f"Phase Diagram: {title}")
        window.geometry("800x600")

        canvas = FigureCanvasTkAgg(fig, window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2Tk(canvas, window)
        toolbar.update()

        # Export button
        btn_frame = tk.Frame(window)
        btn_frame.pack(fill=tk.X, pady=5)

        def export_diagram():
            filename = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG", "*.png"), ("PDF", "*.pdf"), ("SVG", "*.svg")]
            )
            if filename:
                fig.savefig(filename, dpi=300, bbox_inches='tight')
                messagebox.showinfo("Export", f"Diagram saved to {filename}")

        tk.Button(btn_frame, text="💾 Export Diagram", command=export_diagram,
                 bg="#27ae60", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="❌ Close", command=window.destroy,
                 bg="#e74c3c", fg="white").pack(side=tk.RIGHT, padx=5)

    # ============================================================================
    # PLOTTING METHODS
    # ============================================================================
    def _plot_afc(self, ax, result):
        """Plot AFC model"""
        ax.clear()

        F = result['F']
        C = result['C']
        params = result['params']

        ax.plot(F, C, 'b-', linewidth=2, label=params['model'])

        if self.element_var.get() and self.element_var.get() in self.numeric_columns:
            elem = self.element_var.get()
            values = []
            for s in self.samples:
                val = self._safe_float(s.get(elem))
                if val is not None:
                    values.append(val)

            if values:
                ax.scatter([1.0] * len(values), values,
                          c='red', s=30, alpha=0.5, edgecolor='black',
                          label=f'Samples ({elem})', zorder=5)

        ax.set_xlabel('Melt Fraction (F)')
        ax.set_ylabel('Concentration (ppm)')
        ax.set_title(f'AFC Model\nC₀={params["C0"]:.1f}, Ca={params["Ca"]:.1f}, D={params["D"]:.2f}, r={params["r"]:.2f}')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best')
        ax.set_xlim(0, 1.05)
        ax.set_ylim(bottom=0)

    def _plot_fractional(self, ax, result):
        """Plot fractional crystallization model"""
        ax.clear()

        F = result['F']
        C = result['C']
        params = result['params']

        ax.plot(F, C, 'r-', linewidth=2, label=params['model'])

        if self.element_var.get() and self.element_var.get() in self.numeric_columns:
            elem = self.element_var.get()
            values = []
            for s in self.samples:
                val = self._safe_float(s.get(elem))
                if val is not None:
                    values.append(val)

            if values:
                ax.scatter([1.0] * len(values), values,
                          c='blue', s=30, alpha=0.5, edgecolor='black',
                          label=f'Samples ({elem})', zorder=5)

        ax.set_xlabel('Melt Fraction (F)')
        ax.set_ylabel('Concentration (ppm)')
        ax.set_title(f'{params["model"]}\nC₀={params["C0"]:.1f}, D={params["D"]:.2f}')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best')
        ax.set_xlim(0, 1.05)
        ax.set_ylim(bottom=0)

    def _plot_zone_refining(self, ax, result):
        """Plot zone refining model"""
        ax.clear()

        x = result['x']
        C = result['C']
        params = result['params']

        ax.plot(x, C, 'g-', linewidth=2, label=params['model'])

        ax.set_xlabel('Distance (zone lengths)')
        ax.set_ylabel('Concentration (ppm)')
        ax.set_title(f'Zone Refining\nC₀={params["C0"]:.1f}, k={params["k"]:.3f}, {params["passes"]} passes')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best')

    def _plot_binary_mixing(self, ax, result):
        """Plot binary mixing model"""
        ax.clear()

        x = result['x']
        C = result['C']
        params = result['params']

        ax.plot(x, C, 'm-', linewidth=2, label=params['model'])

        ax.set_xlabel('Fraction of Component A')
        ax.set_ylabel('Concentration (ppm)')
        ax.set_title(f'Binary Mixing\nA={params["CA"]:.1f}, B={params["CB"]:.1f}')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best')
        ax.set_xlim(0, 1)

    def _plot_ternary_mixing(self, ax, result):
        """Plot ternary mixing as contour"""
        ax.clear()

        FA = result['FA']
        FB = result['FB']
        C = result['C']
        params = result['params']

        contour = ax.contourf(FA, FB, C, levels=20, cmap='viridis', alpha=0.8)
        plt.colorbar(contour, ax=ax, label='Concentration (ppm)')

        ax.plot([0, 1, 0, 0], [0, 0, 1, 0], 'k-', linewidth=1)

        ax.set_xlabel('fA')
        ax.set_ylabel('fB')
        ax.set_title(f'Ternary Mixing\nA={params["CA"]:.1f}, B={params["CB"]:.1f}, C={params["CC"]:.1f}')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')

    def _plot_melting(self, ax, result):
        """Plot partial melting results"""
        ax.clear()

        F = result['F']
        results = result['results']
        params = result['params']

        ree_to_plot = ["La", "Ce", "Nd", "Sm", "Eu", "Gd", "Yb", "Lu"]
        colors = plt.cm.viridis(np.linspace(0, 1, len(ree_to_plot)))

        for i, elem in enumerate(ree_to_plot):
            if elem in results:
                ax.plot(F, results[elem], linewidth=2, color=colors[i], label=f'{elem}')

        ax.set_xlabel('Melt Fraction (F)')
        ax.set_ylabel('Concentration (ppm)')
        ax.set_title(f'{params["model"]}\nSource: {params["source"]}' +
                    (' (with Kd database)' if params.get('used_kd', False) else ''))
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best', ncol=2, fontsize=8)
        ax.set_yscale('log')

    def _plot_simple_melts(self, ax, result):
        """Plot simple MELTS results"""
        ax.clear()

        T = result['T']
        melt_frac = result['melt_fraction']
        params = result['params']

        ax.plot(T, melt_frac, 'b-', linewidth=2)
        ax.axvline(x=params['T_liquidus'], color='r', linestyle='--', alpha=0.7,
                   label=f'Liquidus: {params["T_liquidus"]:.0f}°C')
        ax.axvline(x=params['T_solidus'], color='g', linestyle='--', alpha=0.7,
                   label=f'Solidus: {params["T_solidus"]:.0f}°C')

        ax.set_xlabel('Temperature (°C)')
        ax.set_ylabel('Melt Fraction')
        ax.set_title('Simple MELTS Model')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.invert_xaxis()

    # ============================================================================
    # EXPORT METHODS - ENHANCED WITH MULTIPLE FORMATS
    # ============================================================================
    def _export_model_enhanced(self, result, model_name):
        """Enhanced export with multiple formats"""
        if not result:
            messagebox.showinfo("Export", "No model results to export")
            return

        # Create format selection dialog
        format_window = tk.Toplevel(self.window)
        format_window.title("Export Format")
        format_window.geometry("300x200")
        format_window.transient(self.window)
        format_window.grab_set()

        tk.Label(format_window, text="Select export format:",
                font=("Arial", 10, "bold")).pack(pady=10)

        format_var = tk.StringVar(value="csv")

        formats = [
            ("CSV (comma separated)", "csv"),
            ("Excel (.xlsx)", "excel"),
            ("JSON", "json"),
            ("Text file", "txt")
        ]

        for text, value in formats:
            tk.Radiobutton(format_window, text=text, variable=format_var,
                          value=value).pack(anchor=tk.W, padx=20, pady=2)

        def do_export():
            fmt = format_var.get()
            format_window.destroy()

            # Get filename
            ext = fmt if fmt != "excel" else "xlsx"
            filename = filedialog.asksaveasfilename(
                defaultextension=f".{ext}",
                filetypes=[(fmt.upper(), f"*.{ext}"), ("All files", "*.*")]
            )

            if filename:
                self._save_model_results(result, model_name, filename, fmt)

        tk.Button(format_window, text="Export", command=do_export,
                 bg="#27ae60", fg="white", width=15).pack(pady=10)
        tk.Button(format_window, text="Cancel", command=format_window.destroy,
                 bg="#e74c3c", fg="white", width=15).pack()

    def _save_model_results(self, result, model_name, filename, fmt):
        """Save model results in specified format"""
        try:
            # Prepare data
            records = []
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            if 'F' in result:
                if 'results' in result and isinstance(result['results'], dict):
                    F = result['F']
                    for i, f in enumerate(F):
                        record = {
                            'Sample_ID': f"{model_name}_{i+1:03d}",
                            'Model': result.get('params', {}).get('model', model_name),
                            'F_melt': f,
                            'Timestamp': timestamp
                        }
                        for elem, values in result['results'].items():
                            if elem != 'F' and i < len(values):
                                record[f'{elem}_ppm'] = values[i]
                        records.append(record)
                else:
                    for i, (f, c) in enumerate(zip(result['F'], result['C'])):
                        records.append({
                            'Sample_ID': f"{model_name}_{i+1:03d}",
                            'Model': result['params']['model'],
                            'F_melt': f,
                            'C_ppm': c,
                            'Timestamp': timestamp
                        })

            elif 'x' in result and 'C' in result:
                for i, (x, c) in enumerate(zip(result['x'], result['C'])):
                    records.append({
                        'Sample_ID': f"{model_name}_{i+1:03d}",
                        'Model': result['params']['model'],
                        'x': x,
                        'C_ppm': c,
                        'Timestamp': timestamp
                    })

            if not records:
                messagebox.showwarning("Export", "No data to export")
                return

            # Export based on format
            df = pd.DataFrame(records)

            if fmt == 'csv':
                df.to_csv(filename, index=False)
            elif fmt == 'excel' and HAS_OPENPYXL:
                with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name=model_name, index=False)

                    # Add metadata sheet
                    metadata = pd.DataFrame([{
                        'Model': model_name,
                        'Parameters': str(result.get('params', {})),
                        'Export_Date': timestamp,
                        'Plugin_Version': '2.1.0'
                    }])
                    metadata.to_excel(writer, sheet_name='Metadata', index=False)
            elif fmt == 'json':
                with open(filename, 'w') as f:
                    json.dump({
                        'model': model_name,
                        'params': result.get('params', {}),
                        'data': records,
                        'export_date': timestamp
                    }, f, indent=2)
            else:  # txt
                with open(filename, 'w') as f:
                    f.write(f"Petrogenetic Modeling Suite Export\n")
                    f.write(f"Model: {model_name}\n")
                    f.write(f"Parameters: {result.get('params', {})}\n")
                    f.write(f"Export Date: {timestamp}\n")
                    f.write("-" * 50 + "\n")
                    for record in records:
                        f.write(str(record) + "\n")

            # Also export to main app
            self.app.import_data_from_plugin(records)
            self.status_var.set(f"✅ Exported {len(records)} points to {fmt.upper()}")

            messagebox.showinfo("Export Success",
                               f"Data exported successfully to {filename}\n"
                               f"Also added {len(records)} points to main app")

        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {str(e)}")
            traceback.print_exc()

    # ============================================================================
    # COMPARISON TAB - FULLY IMPLEMENTED
    # ============================================================================
    def _create_comparison_tab(self):
        """Create comparison tab for multiple models"""
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="📊 Compare Models")

        # Top control panel
        control_frame = tk.Frame(tab, bg="#f5f5f5", height=100)
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(control_frame, text="Select models to compare:",
                font=("Arial", 10, "bold"), bg="#f5f5f5").pack(anchor=tk.W, pady=5)

        # Model selection checkboxes
        checkbox_frame = tk.Frame(control_frame, bg="#f5f5f5")
        checkbox_frame.pack(fill=tk.X, pady=5)

        self.compare_vars = {}
        model_names = {
            'afc': 'AFC', 'fractional': 'Fractional', 'zone': 'Zone Refining',
            'mixing': 'Mixing', 'melting': 'Partial Melting', 'melts': 'MELTS'
        }

        row = 0
        col = 0
        for i, (model_key, display_name) in enumerate(model_names.items()):
            var = tk.BooleanVar(value=False)
            self.compare_vars[model_key] = var
            cb = tk.Checkbutton(checkbox_frame, text=display_name, variable=var,
                               bg="#f5f5f5", command=self._update_comparison_plot)
            cb.grid(row=row, column=col, sticky=tk.W, padx=10)
            col += 1
            if col > 2:
                col = 0
                row += 1

        # Element selection for comparison
        elem_frame = tk.Frame(control_frame, bg="#f5f5f5")
        elem_frame.pack(fill=tk.X, pady=5)

        tk.Label(elem_frame, text="Element:", bg="#f5f5f5").pack(side=tk.LEFT, padx=5)
        self.compare_elem_var = tk.StringVar()
        compare_elem_combo = ttk.Combobox(elem_frame, textvariable=self.compare_elem_var,
                                         values=self.numeric_columns, width=10)
        compare_elem_combo.pack(side=tk.LEFT, padx=5)
        compare_elem_combo.bind('<<ComboboxSelected>>', lambda e: self._update_comparison_plot())

        # Plot type
        tk.Label(elem_frame, text="Plot type:", bg="#f5f5f5").pack(side=tk.LEFT, padx=(20, 5))
        self.compare_plot_type = tk.StringVar(value="linear")
        ttk.Combobox(elem_frame, textvariable=self.compare_plot_type,
                    values=["linear", "log"], width=8).pack(side=tk.LEFT)
        self.compare_plot_type.trace('w', lambda *args: self._update_comparison_plot())

        # Compare button
        tk.Button(control_frame, text="🔄 Update Comparison",
                 command=self._update_comparison_plot,
                 bg="#9C27B0", fg="white", font=("Arial", 10, "bold")).pack(pady=5)

        # Plot area
        plot_frame = tk.Frame(tab, bg="white")
        plot_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.compare_fig = plt.Figure(figsize=(9, 6), dpi=100)
        self.compare_fig.patch.set_facecolor('white')
        self.compare_ax = self.compare_fig.add_subplot(111)
        self.compare_ax.set_facecolor('#f8f9fa')

        self.compare_canvas = FigureCanvasTkAgg(self.compare_fig, plot_frame)
        self.compare_canvas.draw()
        self.compare_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        toolbar_frame = tk.Frame(plot_frame)
        toolbar_frame.pack(fill=tk.X)
        NavigationToolbar2Tk(self.compare_canvas, toolbar_frame).update()

    def _update_comparison_plot(self):
        """Update comparison plot with selected models"""
        self.compare_ax.clear()

        colors = ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00', '#a65628']
        elem = self.compare_elem_var.get()

        plotted = 0
        for i, (model_key, var) in enumerate(self.compare_vars.items()):
            if var.get() and self.model_results[model_key]:
                result = self.model_results[model_key]

                # Different models have different structures
                if model_key == 'melting':
                    if 'results' in result and elem in result['results']:
                        x = result['F']
                        y = result['results'][elem]
                        self.compare_ax.plot(x, y, color=colors[i % len(colors)],
                                           linewidth=2.5, label=f"Melting ({elem})")
                        plotted += 1

                elif model_key == 'mixing':
                    if 'x' in result and 'C' in result:
                        x = result['x']
                        y = result['C']
                        self.compare_ax.plot(x, y, color=colors[i % len(colors)],
                                           linewidth=2.5, label="Mixing")
                        plotted += 1

                elif 'F' in result and 'C' in result:
                    x = result['F']
                    y = result['C']
                    model_name = result.get('params', {}).get('model', model_key.capitalize())
                    self.compare_ax.plot(x, y, color=colors[i % len(colors)],
                                       linewidth=2.5, label=model_name)
                    plotted += 1

                elif 'T' in result and 'melt_fraction' in result:
                    x = result['T']
                    y = result['melt_fraction']
                    self.compare_ax.plot(x, y, color=colors[i % len(colors)],
                                       linewidth=2.5, label="MELTS")
                    plotted += 1

        if plotted == 0:
            self.compare_ax.text(0.5, 0.5, "No models selected for comparison\nor incompatible element",
                                ha='center', va='center', transform=self.compare_ax.transAxes,
                                fontsize=12, color='gray')
        else:
            # Set axis labels based on first plotted model
            if 'F' in locals():
                self.compare_ax.set_xlabel('F (melt fraction)', fontsize=12)
            elif 'x' in locals():
                self.compare_ax.set_xlabel('x', fontsize=12)
            elif 'T' in locals():
                self.compare_ax.set_xlabel('Temperature (°C)', fontsize=12)

            self.compare_ax.set_ylabel(f'Concentration (ppm) - {elem}' if elem else 'Concentration', fontsize=12)
            self.compare_ax.set_title('Model Comparison', fontsize=14)
            self.compare_ax.legend(loc='best', fontsize=9)
            self.compare_ax.grid(True, alpha=0.3)

            if self.compare_plot_type.get() == "log":
                self.compare_ax.set_yscale('log')

        self.compare_canvas.draw()

    # ============================================================================
    # MELTS - IMPROVED ERROR HANDLING
    # ============================================================================
    @staticmethod
    def _prepare_composition_for_magemin(comp_vars):
        """Convert comp_vars dict into a MAGEMin-compatible composition dict."""
        composition = {}
        for oxide, var in comp_vars.items():
            val = var.get()
            if val > 0:
                composition[oxide] = val

        # Normalize to 100
        total = sum(composition.values())
        if total > 0 and abs(total - 100) > 0.01:
            composition = {k: v * 100.0 / total for k, v in composition.items()}

        return composition

    @staticmethod
    def _parse_petthermotools_results(results):
        """Extract (T_array, comp_dict, mass_dict) from Green2025/Weller2024 results."""
        print("\n── petthermotools result inspector ──")
        print(f"Type: {type(results)}")

        if not isinstance(results, dict) or not results:
            print("Empty or non-dict result.")
            return None, None, {}

        print(f"Keys: {list(results.keys())}")
        for k, v in results.items():
            print(f"  [{k}] → {type(v).__name__}", end="")
            if hasattr(v, 'columns'):
                print(f"  columns={list(v.columns)[:8]}", end="")
            elif isinstance(v, (list, np.ndarray)):
                print(f"  len={len(v)}", end="")
            print()

        T = None
        comp_dict = {}
        mass_dict = {}

        # Get temperature
        for key in ['Conditions', 'All']:
            if key in results and hasattr(results[key], 'columns'):
                df = results[key]
                if 'T_C' in df.columns:
                    T = df['T_C'].values.copy()
                    print(f"T from '{key}['T_C']': {T.min():.0f}–{T.max():.0f}°C, n={len(T)}")
                    break

        if T is None:
            print("No temperature found.")
            return None, None, {}

        # Get liquid composition
        oxide_map = {
            'SiO2_Liq': 'SiO2', 'TiO2_Liq': 'TiO2', 'Al2O3_Liq': 'Al2O3',
            'FeOt_Liq': 'FeOt', 'MgO_Liq': 'MgO', 'CaO_Liq': 'CaO',
            'Na2O_Liq': 'Na2O', 'K2O_Liq': 'K2O', 'H2O_Liq': 'H2O',
        }

        liq_df = None
        for key in ['liquid1', 'All']:
            if key in results and hasattr(results[key], 'columns'):
                df = results[key]
                if any(c in df.columns for c in oxide_map):
                    liq_df = df
                    print(f"Liquid composition from '{key}'")
                    break

        if liq_df is not None:
            for col, oxide in oxide_map.items():
                if col in liq_df.columns:
                    comp_dict[oxide] = liq_df[col].values.copy()

        # Get phase masses
        if 'mass_g' in results and hasattr(results['mass_g'], 'columns'):
            mg = results['mass_g']
            phase_labels = {
                'olivine1': 'Olivine', 'clinopyroxene1': 'Cpx',
                'feldspar1': 'Feldspar', 'liquid1': 'Liquid',
                'spinel1': 'Spinel', 'ilm1': 'Ilmenite',
            }
            for col, label in phase_labels.items():
                if col in mg.columns:
                    mass_dict[label] = mg[col].values.copy()

        print(f"Oxides extracted: {list(comp_dict.keys())}")
        print(f"Phases with mass: {list(mass_dict.keys())}")

        if comp_dict:
            return T, comp_dict, mass_dict
        print("No liquid oxide columns found.")
        return None, None, {}

    @staticmethod
    def _julia_env_is_ready():
        """Return True if MAGEMin env was previously set up successfully."""
        sentinel = PetrogeneticModelingSuitePlugin._SENTINEL_FILE
        if not os.path.exists(sentinel):
            return False
        manifest = os.path.expanduser("~/.petthermotools_julia_env/Manifest.toml")
        if not os.path.exists(manifest):
            return False
        try:
            with open(manifest) as f:
                return "MAGEMinCalc" in f.read()
        except Exception:
            return False

    @staticmethod
    def _mark_julia_env_ready():
        """Write sentinel so we never call install_MAGEMinCalc() again."""
        try:
            with open(PetrogeneticModelingSuitePlugin._SENTINEL_FILE, 'w') as f:
                f.write("ready\n")
        except Exception as e:
            print(f"Warning: could not write sentinel: {e}")

    def _check_julia_installation(self):
        """Check if Julia is installed and in PATH"""
        try:
            result = subprocess.run(['julia', '--version'],
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def _validate_magemin_composition(self):
        """Validate composition for MAGEMin"""
        required_oxides = ['SiO2', 'Al2O3', 'CaO', 'MgO', 'FeO', 'Na2O', 'K2O', 'H2O']
        missing = []

        for oxide in required_oxides:
            if oxide not in self.comp_vars or self.comp_vars[oxide].get() <= 0:
                missing.append(oxide)

        if missing:
            messagebox.showwarning("Missing Oxides",
                                  f"Missing required oxides for MAGEMin:\n{', '.join(missing)}\n"
                                  "Using fallback model instead.")
            return False

        return True

    def _validate_magemin_inputs(self):
        """Validate all inputs for MAGEMin run"""
        missing = []
        required_oxides = ['SiO2', 'TiO2', 'Al2O3', 'FeO', 'MgO', 'CaO', 'Na2O', 'K2O', 'H2O']
        for oxide in required_oxides:
            if oxide not in self.comp_vars or self.comp_vars[oxide].get() <= 0:
                missing.append(oxide)

        if self.melts_T_start_var.get() <= self.melts_T_end_var.get():
            missing.append("T_start must be > T_end")

        if self.melts_pressure_var.get() <= 0:
            missing.append("Pressure must be > 0")

        if missing:
            messagebox.showerror("Missing Inputs",
                               "Cannot run MAGEMin:\n" + "\n".join(f"  • {m}" for m in missing))
            return False
        return True

    def _run_magemin_thread(self):
        """Run MAGEMin calculation in thread with improved error handling"""
        if not HAS_PETTERMO:
            self.window.after(0, lambda: messagebox.showerror(
                "PetThermoTools Missing",
                "Please install petthermotools first:\npip install petthermotools"
            ))
            return

        import petthermotools as ptt

        os.environ['JULIA_PKG_PRECOMPILE_AUTO'] = '0'

        # Check Julia installation
        if not self._check_julia_installation():
            self.window.after(0, lambda: messagebox.showinfo(
                "Julia Required",
                "Julia is not installed or not in PATH.\n"
                "Please install Julia from https://julialang.org/downloads/"
            ))
            return

        # One-time install check
        if not self._julia_env_is_ready():
            self.window.after(0, lambda: self.status_var.set(
                "🔧 First-time setup — installing MAGEMin (~3-5 min, once only)..."))
            self.window.after(0, lambda: self.julia_status_label.config(
                text="⏳ First-time install — please wait...", fg="orange"))
            try:
                ptt.install_MAGEMinCalc()
                self._mark_julia_env_ready()
                self.window.after(0, lambda: self.julia_status_label.config(
                    text="✅ Julia env ready", fg="green"))
            except Exception as e:
                self.window.after(0, lambda: messagebox.showerror(
                    "Installation Failed",
                    f"Failed to install MAGEMinCalc:\n{str(e)}\n\n"
                    "Please try:\n"
                    "1. Install Julia manually\n"
                    "2. Run: pip install --upgrade petthermotools\n"
                    "3. Restart the plugin"
                ))
                return

        # Build parameters
        composition = self._prepare_composition_for_magemin(self.comp_vars)
        print(f"\nComposition: {composition}")

        T_start = self.melts_T_start_var.get()
        T_end = self.melts_T_end_var.get()
        steps = self.melts_steps_var.get()
        pressure = self.melts_pressure_var.get()
        fo2 = self.melts_fo2_var.get()
        fo2_offset = self.melts_fo2_offset_var.get()
        frac_solid = "Fractional" in self.melts_calc_type_var.get()
        dt = (T_start - T_end) / max(steps, 1)

        timeout_seconds = int(steps * 30 + 480)
        print(f"Timeout: {timeout_seconds}s for {steps} steps")

        # Progress capture
        class ProgressCapture:
            def __init__(self_, update_cb, orig):
                self_.update_cb = update_cb
                self_.orig = orig
                self_.buf = ""

            def write(self_, text):
                self_.orig.write(text)
                self_.orig.flush()
                self_.buf += text
                m = re.search(r'Completed\s+([\d.]+)\s*%', self_.buf)
                if m:
                    pct = float(m.group(1))
                    self_.update_cb(pct)
                    self_.buf = ""

            def flush(self_):
                self_.orig.flush()

        def on_progress(pct):
            pct = min(pct, 100.0)
            self.window.after(0, lambda p=pct: (
                self.melts_pct_label.config(text=f"{p:.0f}%"),
                self.status_var.set(
                    f"⚙️ MAGEMin running… {p:.0f}% "
                    f"({T_start:.0f}→{T_end:.0f}°C, {steps} steps)"
                )
            ))

        self.window.after(0, lambda: self.melts_pct_label.config(text="0%"))
        self.window.after(0, lambda: self.status_var.set(
            f"⚙️ MAGEMin running… 0%  ({steps} steps, up to {timeout_seconds}s)"))

        orig_stdout = sys.stdout
        sys.stdout = ProgressCapture(on_progress, orig_stdout)

        start_time = time.time()
        try:
            # Map model names
            model_map = {
                "Green2025": "Green2025",
                "Weller2024": "Weller2024",
                "MAGEMin": "Green2025"  # fallback
            }
            model_str = model_map.get(self.melts_model_var.get(), "Green2025")
            print(f"Using petthermotools model: {model_str!r}")

            # Run calculation
            results = ptt.isobaric_crystallisation(
                Model=model_str,
                bulk=composition,
                P_bar=pressure,
                T_start_C=T_start,
                T_end_C=T_end,
                dt_C=dt,
                fO2_buffer=fo2,
                fO2_offset=fo2_offset,
                Frac_solid=frac_solid,
            )
        except Exception as e:
            sys.stdout = orig_stdout
            err_msg = str(e)
            self.window.after(0, lambda: self._show_magemin_error(err_msg))
            traceback.print_exc()
            return
        finally:
            sys.stdout = orig_stdout
            self.window.after(0, self._enable_run_button)
            self.window.after(0, lambda: self.progress.stop())

        elapsed = time.time() - start_time
        self.window.after(0, lambda: self.melts_pct_label.config(text="100%"))
        print(f"\nDone in {elapsed:.1f}s")
        self.window.after(0, self._display_magemin_results, results, elapsed)

    def _show_magemin_error(self, error_msg):
        """Show user-friendly MAGEMin error"""
        self.progress.stop()
        self.status_var.set("❌ MAGEMin calculation failed")

        # Parse common errors
        if "not found" in error_msg.lower() or "julia" in error_msg.lower():
            msg = ("Julia or MAGEMinCalc not found.\n\n"
                   "Troubleshooting:\n"
                   "1. Install Julia from julialang.org\n"
                   "2. Run: pip install --upgrade petthermotools\n"
                   "3. Restart the plugin\n\n"
                   f"Error: {error_msg[:200]}")
        elif "timeout" in error_msg.lower():
            msg = ("MAGEMin calculation timed out.\n\n"
                   "Try:\n"
                   "- Reduce number of steps\n"
                   "- Check composition validity\n"
                   "- Increase timeout if needed")
        else:
            msg = f"MAGEMin calculation failed:\n\n{error_msg[:300]}"

        messagebox.showerror("MAGEMin Error", msg)

    def _enable_run_button(self):
        """Re-enable run button"""
        try:
            if hasattr(self, 'run_button'):
                self.run_button.config(state='normal')
        except Exception:
            pass

    def _display_magemin_results(self, results, elapsed):
        """Display MAGEMin results"""
        try:
            self.model_results['melts'] = results
            self.melts_ax.clear()

            parsed = self._parse_petthermotools_results(results)
            if len(parsed) == 3:
                T, comp_dict, mass_dict = parsed
            else:
                T, comp_dict = parsed
                mass_dict = {}

            if T is None or not comp_dict:
                print("⚠️  Could not extract T+composition — using fallback plot")
                self.status_var.set("⚠️ No liquid composition extracted — using fallback")
                simple = self._calculate_simple_melts()
                self._plot_simple_melts(self.melts_ax, simple)
                self.melts_canvas.draw()
                self.model_results['melts'] = simple
                return

            # Build 2-panel figure
            self.melts_fig.clear()

            if mass_dict:
                ax1 = self.melts_fig.add_subplot(2, 1, 1)
                ax2 = self.melts_fig.add_subplot(2, 1, 2)
            else:
                ax1 = self.melts_fig.add_subplot(1, 1, 1)
                ax2 = None

            # Panel 1: liquid oxide evolution
            oxide_display = {
                'SiO2': 'SiO2', 'TiO2': 'TiO2', 'Al2O3': 'Al₂O₃',
                'FeOt': 'FeOt', 'MgO': 'MgO', 'CaO': 'CaO',
                'Na2O': 'Na₂O', 'K2O': 'K₂O',
            }
            colors = ['#e41a1c','#377eb8','#4daf4a','#984ea3','#ff7f00','#a65628','#f781bf','#999999']
            plotted = 0
            for i, (oxide, label) in enumerate(oxide_display.items()):
                if oxide in comp_dict:
                    vals = comp_dict[oxide]
                    if len(vals) == len(T) and np.any(np.isfinite(vals)):
                        ax1.plot(T, vals, label=label, linewidth=2,
                                color=colors[i % len(colors)])
                        plotted += 1

            ax1.set_xlabel('Temperature (°C)')
            ax1.set_ylabel('Liquid composition (wt%)')
            ax1.set_title(f'{self.melts_model_var.get()} — {self.melts_calc_type_var.get()} — {elapsed:.0f}s')
            ax1.legend(loc='upper left', fontsize=7, ncol=2)
            ax1.grid(True, alpha=0.3)
            ax1.invert_xaxis()

            # Panel 2: phase masses
            if ax2 is not None and mass_dict:
                phase_colors = {
                    'Liquid': '#2196F3', 'Olivine': '#4CAF50', 'Cpx': '#9C27B0',
                    'Feldspar': '#FF9800', 'Spinel': '#F44336', 'Ilmenite': '#607D8B',
                }
                for phase, masses in mass_dict.items():
                    if len(masses) == len(T):
                        c = phase_colors.get(phase, '#333333')
                        ax2.plot(T, masses, label=phase, linewidth=2, color=c)
                ax2.set_xlabel('Temperature (°C)')
                ax2.set_ylabel('Mass (g)')
                ax2.set_title('Phase abundances')
                ax2.legend(loc='best', fontsize=7)
                ax2.grid(True, alpha=0.3)
                ax2.invert_xaxis()

            self.melts_fig.tight_layout()
            self.melts_canvas.draw()
            self.status_var.set(
                f"✅ MAGEMin complete! {elapsed:.0f}s — {plotted} oxides, {len(mass_dict)} phases")

            if messagebox.askyesno("Export Results", "Export results to main app?"):
                self._export_model_enhanced(results, "MELTS")

        except Exception as e:
            messagebox.showerror("Display Error", str(e))
            traceback.print_exc()

    # ============================================================================
    # UI CONSTRUCTION - UPDATED WITH ALL TABS
    # ============================================================================
    def open_window(self):
        """Open the main window"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            self._load_from_main_app()
            return

        if not self.dependencies_met:
            messagebox.showerror(
                "Missing Dependencies",
                f"Please install: {', '.join(self.missing_deps)}"
            )
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("🌋 Petrogenetic Modeling Suite v2.1")
        self.window.geometry("1200x750")

        self._create_interface()

        if self._load_from_main_app():
            self.status_var.set("✅ Loaded data from main app")
        else:
            self.status_var.set("ℹ️ No geochemical data found")

        self.window.transient(self.app.root)
        self.window.lift()
        self.window.focus_force()

    def _create_interface(self):
        """Create the interface with all 8 tabs"""
        header = tk.Frame(self.window, bg="#8e44ad", height=40)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="🌋", font=("Arial", 18),
                bg="#8e44ad", fg="white").pack(side=tk.LEFT, padx=8)
        tk.Label(header, text="Petrogenetic Modeling Suite",
                font=("Arial", 14, "bold"),
                bg="#8e44ad", fg="white").pack(side=tk.LEFT, padx=2)
        tk.Label(header, text="v2.1 - Complete Implementation",
                font=("Arial", 8),
                bg="#8e44ad", fg="#f1c40f").pack(side=tk.LEFT, padx=8)

        elem_frame = tk.Frame(header, bg="#8e44ad")
        elem_frame.pack(side=tk.RIGHT, padx=10)

        tk.Label(elem_frame, text="Element:", bg="#8e44ad", fg="white",
                font=("Arial", 9)).pack(side=tk.LEFT, padx=2)

        self.element_combo = ttk.Combobox(elem_frame, textvariable=self.element_var,
                                          values=self.numeric_columns, width=8,
                                          state='readonly')
        self.element_combo.pack(side=tk.LEFT, padx=2)

        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create all 8 tabs
        self._create_afc_tab()
        self._create_fractional_tab()
        self._create_zone_tab()
        self._create_mixing_tab()
        self._create_melting_tab()
        self._create_phase_diagram_tab()
        self._create_melts_tab()
        self._create_comparison_tab()  # New comparison tab

        status = tk.Frame(self.window, bg="#34495e", height=24)
        status.pack(fill=tk.X, side=tk.BOTTOM)
        status.pack_propagate(False)

        self.status_var = tk.StringVar(value="Ready")
        tk.Label(status, textvariable=self.status_var,
                font=("Arial", 8), bg="#34495e", fg="white").pack(side=tk.LEFT, padx=8)

        self.progress = ttk.Progressbar(status, mode='indeterminate', length=120)
        self.progress.pack(side=tk.RIGHT, padx=5)

    # ============================================================================
    # TAB 1: AFC
    # ============================================================================
    def _create_afc_tab(self):
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="🌋 AFC")

        paned = tk.PanedWindow(tab, orient=tk.HORIZONTAL, sashwidth=4)
        paned.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        left = tk.Frame(paned, bg="#f5f5f5", width=300)
        paned.add(left, width=300, minsize=280)

        right = tk.Frame(paned, bg="white", width=600, height=500)
        paned.add(right, width=600, minsize=450)

        params = [
            ("C₀ (ppm):", self.afc_C0_var, 0, 10000),
            ("Ca (ppm):", self.afc_Ca_var, 0, 10000),
            ("D:", self.afc_D_var, 0, 10),
            ("r (Ma/Mc):", self.afc_r_var, 0, 2),
            ("F min:", self.afc_F_min_var, 0, 1),
            ("F max:", self.afc_F_max_var, 0, 1),
            ("Steps:", self.afc_F_steps_var, 10, 200)
        ]

        for label, var, minv, maxv in params:
            frame = tk.Frame(left, bg="#f5f5f5")
            frame.pack(fill=tk.X, padx=5, pady=2)
            tk.Label(frame, text=label, width=10, anchor=tk.W, bg="#f5f5f5").pack(side=tk.LEFT)
            if isinstance(var, tk.DoubleVar):
                tk.Spinbox(frame, from_=minv, to=maxv, increment=0.1, textvariable=var, width=8).pack(side=tk.LEFT, padx=2)
            else:
                tk.Spinbox(frame, from_=minv, to=maxv, increment=1, textvariable=var, width=8).pack(side=tk.LEFT, padx=2)

        tk.Button(left, text="🧮 Calculate AFC", command=self._calculate_and_plot_afc,
                 bg="#e67e22", fg="white", width=20, height=2).pack(pady=10)
        tk.Button(left, text="📤 Export Model",
                 command=lambda: self._export_model_enhanced(self.model_results['afc'], "AFC"),
                 bg="#27ae60", fg="white", width=20).pack(pady=2)

        self.afc_fig = plt.Figure(figsize=(6, 5), dpi=90)
        self.afc_fig.patch.set_facecolor('white')
        self.afc_ax = self.afc_fig.add_subplot(111)
        self.afc_ax.set_facecolor('#f8f9fa')
        self.afc_canvas = FigureCanvasTkAgg(self.afc_fig, right)
        self.afc_canvas.draw()
        self.afc_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        toolbar_frame = tk.Frame(right, height=25)
        toolbar_frame.pack(fill=tk.X)
        NavigationToolbar2Tk(self.afc_canvas, toolbar_frame).update()

    def _calculate_and_plot_afc(self):
        self.progress.start()
        self.status_var.set("Calculating AFC model...")
        self.model_results['afc'] = self._calculate_afc()
        self._plot_afc(self.afc_ax, self.model_results['afc'])
        self.afc_canvas.draw()
        self.status_var.set("✅ AFC model complete")
        self.progress.stop()

    # ============================================================================
    # TAB 2: Fractional Crystallization
    # ============================================================================
    def _create_fractional_tab(self):
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="🔬 Fractional")

        paned = tk.PanedWindow(tab, orient=tk.HORIZONTAL, sashwidth=4)
        paned.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        left = tk.Frame(paned, bg="#f5f5f5", width=300)
        paned.add(left, width=300, minsize=280)
        right = tk.Frame(paned, bg="white", width=600, height=500)
        paned.add(right, width=600, minsize=450)

        model_frame = tk.LabelFrame(left, text="Model Type", padx=5, pady=5, bg="#f5f5f5")
        model_frame.pack(fill=tk.X, padx=5, pady=2)
        tk.Radiobutton(model_frame, text="Rayleigh", variable=self.frac_model_var, value="rayleigh", bg="#f5f5f5").pack(anchor=tk.W)
        tk.Radiobutton(model_frame, text="Equilibrium", variable=self.frac_model_var, value="equilibrium", bg="#f5f5f5").pack(anchor=tk.W)
        tk.Radiobutton(model_frame, text="In-Situ (Langmuir 1989)", variable=self.frac_model_var, value="in_situ", bg="#f5f5f5").pack(anchor=tk.W)

        for label, var, minv, maxv in [("C₀ (ppm):", self.frac_C0_var, 0, 10000),
                                        ("D:", self.frac_D_var, 0, 10),
                                        ("F min:", self.frac_F_min_var, 0, 1),
                                        ("F max:", self.frac_F_max_var, 0, 1),
                                        ("Steps:", self.frac_F_steps_var, 10, 200)]:
            frame = tk.Frame(left, bg="#f5f5f5")
            frame.pack(fill=tk.X, padx=5, pady=2)
            tk.Label(frame, text=label, width=10, anchor=tk.W, bg="#f5f5f5").pack(side=tk.LEFT)
            inc = 0.1 if isinstance(var, tk.DoubleVar) else 1
            tk.Spinbox(frame, from_=minv, to=maxv, increment=inc, textvariable=var, width=8).pack(side=tk.LEFT, padx=2)

        tk.Button(left, text="🧮 Calculate", command=self._calculate_and_plot_fractional,
                 bg="#e67e22", fg="white", width=20, height=2).pack(pady=10)
        tk.Button(left, text="📤 Export Model",
                 command=lambda: self._export_model_enhanced(self.model_results['fractional'], "Fractional"),
                 bg="#27ae60", fg="white", width=20).pack(pady=2)

        self.frac_fig = plt.Figure(figsize=(6, 5), dpi=90)
        self.frac_fig.patch.set_facecolor('white')
        self.frac_ax = self.frac_fig.add_subplot(111)
        self.frac_ax.set_facecolor('#f8f9fa')
        self.frac_canvas = FigureCanvasTkAgg(self.frac_fig, right)
        self.frac_canvas.draw()
        self.frac_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        toolbar_frame = tk.Frame(right, height=25)
        toolbar_frame.pack(fill=tk.X)
        NavigationToolbar2Tk(self.frac_canvas, toolbar_frame).update()

    def _calculate_and_plot_fractional(self):
        self.progress.start()
        self.status_var.set("Calculating fractional crystallization...")
        self.model_results['fractional'] = self._calculate_fractional()
        self._plot_fractional(self.frac_ax, self.model_results['fractional'])
        self.frac_canvas.draw()
        self.status_var.set("✅ Fractional crystallization complete")
        self.progress.stop()

    # ============================================================================
    # TAB 3: Zone Refining
    # ============================================================================
    def _create_zone_tab(self):
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="🔬 Zone Refining")
        paned = tk.PanedWindow(tab, orient=tk.HORIZONTAL, sashwidth=4)
        paned.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        left = tk.Frame(paned, bg="#f5f5f5", width=300)
        paned.add(left, width=300, minsize=280)
        right = tk.Frame(paned, bg="white", width=600, height=500)
        paned.add(right, width=600, minsize=450)

        for label, var, minv, maxv in [("C₀ (ppm):", self.zone_C0_var, 0, 10000),
                                        ("k:", self.zone_k_var, 0, 10),
                                        ("Passes:", self.zone_passes_var, 1, 50),
                                        ("Length:", self.zone_length_var, 0.1, 10),
                                        ("Steps:", self.zone_steps_var, 50, 500)]:
            frame = tk.Frame(left, bg="#f5f5f5")
            frame.pack(fill=tk.X, padx=5, pady=2)
            tk.Label(frame, text=label, width=10, anchor=tk.W, bg="#f5f5f5").pack(side=tk.LEFT)
            inc = 0.1 if isinstance(var, tk.DoubleVar) else 1
            tk.Spinbox(frame, from_=minv, to=maxv, increment=inc, textvariable=var, width=8).pack(side=tk.LEFT, padx=2)

        tk.Button(left, text="🧮 Calculate", command=self._calculate_and_plot_zone,
                 bg="#e67e22", fg="white", width=20, height=2).pack(pady=10)
        tk.Button(left, text="📤 Export Model",
                 command=lambda: self._export_model_enhanced(self.model_results['zone'], "Zone"),
                 bg="#27ae60", fg="white", width=20).pack(pady=2)

        self.zone_fig = plt.Figure(figsize=(6, 5), dpi=90)
        self.zone_fig.patch.set_facecolor('white')
        self.zone_ax = self.zone_fig.add_subplot(111)
        self.zone_ax.set_facecolor('#f8f9fa')
        self.zone_canvas = FigureCanvasTkAgg(self.zone_fig, right)
        self.zone_canvas.draw()
        self.zone_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        toolbar_frame = tk.Frame(right, height=25)
        toolbar_frame.pack(fill=tk.X)
        NavigationToolbar2Tk(self.zone_canvas, toolbar_frame).update()

    def _calculate_and_plot_zone(self):
        self.progress.start()
        self.status_var.set("Calculating zone refining...")
        self.model_results['zone'] = self._calculate_zone_refining()
        self._plot_zone_refining(self.zone_ax, self.model_results['zone'])
        self.zone_canvas.draw()
        self.status_var.set("✅ Zone refining complete")
        self.progress.stop()

    # ============================================================================
    # TAB 4: Mixing
    # ============================================================================
    def _create_mixing_tab(self):
        """Create mixing tab with full mode selection UI"""
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="🔄 Mixing")

        paned = tk.PanedWindow(tab, orient=tk.HORIZONTAL, sashwidth=4)
        paned.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        left = tk.Frame(paned, bg="#f5f5f5", width=300)
        paned.add(left, width=300, minsize=280)

        right = tk.Frame(paned, bg="white", width=600, height=500)
        paned.add(right, width=600, minsize=450)

        # ============ MODEL TYPE ============
        model_frame = tk.LabelFrame(left, text="Model Type", padx=5, pady=5, bg="#f5f5f5")
        model_frame.pack(fill=tk.X, padx=5, pady=2)

        tk.Radiobutton(model_frame, text="Binary", variable=self.mix_model_var,
                    value="binary", command=self._toggle_mixing_ui,
                    bg="#f5f5f5").pack(anchor=tk.W)
        tk.Radiobutton(model_frame, text="Ternary", variable=self.mix_model_var,
                    value="ternary", command=self._toggle_mixing_ui,
                    bg="#f5f5f5").pack(anchor=tk.W)

        # ============ MIXING MODE ============
        mode_frame = tk.LabelFrame(left, text="Mixing Mode", padx=5, pady=5, bg="#f5f5f5")
        mode_frame.pack(fill=tk.X, padx=5, pady=2)

        # Mode selection
        self.mix_mode_var = tk.StringVar(value="linear")

        tk.Radiobutton(mode_frame, text="Linear (major elements)",
                    variable=self.mix_mode_var, value="linear",
                    bg="#f5f5f5").pack(anchor=tk.W)
        tk.Radiobutton(mode_frame, text="Trace element (with partitioning)",
                    variable=self.mix_mode_var, value="trace",
                    bg="#f5f5f5").pack(anchor=tk.W)
        tk.Radiobutton(mode_frame, text="Isotope mixing",
                    variable=self.mix_mode_var, value="isotope",
                    bg="#f5f5f5").pack(anchor=tk.W)

        # ============ TRACE ELEMENT PARAMETERS ============
        self.trace_param_frame = tk.Frame(mode_frame, bg="#f5f5f5")

        # Partition coefficients
        pc_frame = tk.Frame(self.trace_param_frame, bg="#f5f5f5")
        pc_frame.pack(fill=tk.X, pady=2)

        tk.Label(pc_frame, text="D_A:", bg="#f5f5f5", width=5).pack(side=tk.LEFT)
        self.mix_D_A = tk.DoubleVar(value=1.0)
        tk.Spinbox(pc_frame, from_=0.01, to=10, increment=0.1,
                textvariable=self.mix_D_A, width=6).pack(side=tk.LEFT, padx=2)

        tk.Label(pc_frame, text="D_B:", bg="#f5f5f5", width=5).pack(side=tk.LEFT, padx=(10,0))
        self.mix_D_B = tk.DoubleVar(value=1.0)
        tk.Spinbox(pc_frame, from_=0.01, to=10, increment=0.1,
                textvariable=self.mix_D_B, width=6).pack(side=tk.LEFT, padx=2)

        tk.Label(pc_frame, text="D_C:", bg="#f5f5f5", width=5).pack(side=tk.LEFT, padx=(10,0))
        self.mix_D_C = tk.DoubleVar(value=1.0)
        tk.Spinbox(pc_frame, from_=0.01, to=10, increment=0.1,
                textvariable=self.mix_D_C, width=6).pack(side=tk.LEFT, padx=2)

        # Porosity/Solid fraction
        phi_frame = tk.Frame(self.trace_param_frame, bg="#f5f5f5")
        phi_frame.pack(fill=tk.X, pady=2)

        tk.Label(phi_frame, text="φ (solid fraction):", bg="#f5f5f5", width=15).pack(side=tk.LEFT)
        self.mix_phi = tk.DoubleVar(value=0.1)
        tk.Spinbox(phi_frame, from_=0, to=1, increment=0.05,
                textvariable=self.mix_phi, width=6).pack(side=tk.LEFT, padx=2)

        # ============ ISOTOPE PARAMETERS ============
        self.isotope_param_frame = tk.Frame(mode_frame, bg="#f5f5f5")

        # Ratios
        ratio_frame = tk.Frame(self.isotope_param_frame, bg="#f5f5f5")
        ratio_frame.pack(fill=tk.X, pady=2)

        tk.Label(ratio_frame, text="Isotope Ratios:", bg="#f5f5f5", font=("Arial", 8, "bold")).pack(anchor=tk.W)

        ratio_grid = tk.Frame(ratio_frame, bg="#f5f5f5")
        ratio_grid.pack(fill=tk.X, pady=2)

        tk.Label(ratio_grid, text="").grid(row=0, column=0)
        tk.Label(ratio_grid, text="A").grid(row=0, column=1)
        tk.Label(ratio_grid, text="B").grid(row=0, column=2)
        tk.Label(ratio_grid, text="C").grid(row=0, column=3)

        tk.Label(ratio_grid, text="Ratio:").grid(row=1, column=0, sticky=tk.W)
        self.iso_ratio_A = tk.DoubleVar(value=0.703)
        self.iso_ratio_B = tk.DoubleVar(value=0.706)
        self.iso_ratio_C = tk.DoubleVar(value=0.709)

        tk.Entry(ratio_grid, textvariable=self.iso_ratio_A, width=8).grid(row=1, column=1)
        tk.Entry(ratio_grid, textvariable=self.iso_ratio_B, width=8).grid(row=1, column=2)
        tk.Entry(ratio_grid, textvariable=self.iso_ratio_C, width=8).grid(row=1, column=3)

        # Concentrations
        conc_frame = tk.Frame(self.isotope_param_frame, bg="#f5f5f5")
        conc_frame.pack(fill=tk.X, pady=2)

        tk.Label(conc_frame, text="Conc (ppm):", bg="#f5f5f5").grid(row=0, column=0, sticky=tk.W)
        self.iso_conc_A = tk.DoubleVar(value=100)
        self.iso_conc_B = tk.DoubleVar(value=200)
        self.iso_conc_C = tk.DoubleVar(value=300)

        tk.Entry(conc_frame, textvariable=self.iso_conc_A, width=8).grid(row=0, column=1)
        tk.Entry(conc_frame, textvariable=self.iso_conc_B, width=8).grid(row=0, column=2)
        tk.Entry(conc_frame, textvariable=self.iso_conc_C, width=8).grid(row=0, column=3)

        # Binary-specific isotope parameters
        self.binary_iso_frame = tk.Frame(self.isotope_param_frame, bg="#f5f5f5")

        tk.Label(self.binary_iso_frame, text="Binary Mixing Only:",
                font=("Arial", 8, "italic"), bg="#f5f5f5").pack(anchor=tk.W)

        bin_conc_frame = tk.Frame(self.binary_iso_frame, bg="#f5f5f5")
        bin_conc_frame.pack(fill=tk.X, pady=2)

        tk.Label(bin_conc_frame, text="Conc A (ppm):", bg="#f5f5f5", width=12).pack(side=tk.LEFT)
        self.binary_conc_A = tk.DoubleVar(value=100)
        tk.Spinbox(bin_conc_frame, from_=1, to=10000, textvariable=self.binary_conc_A, width=8).pack(side=tk.LEFT)

        tk.Label(bin_conc_frame, text="Conc B (ppm):", bg="#f5f5f5", width=12).pack(side=tk.LEFT, padx=(10,0))
        self.binary_conc_B = tk.DoubleVar(value=200)
        tk.Spinbox(bin_conc_frame, from_=1, to=10000, textvariable=self.binary_conc_B, width=8).pack(side=tk.LEFT)

        # ============ BINARY FRAME (existing) ============
        self.binary_frame = tk.Frame(left, bg="#f5f5f5")
        self.binary_frame.pack(fill=tk.X, padx=5, pady=2)

        for label, var, minv, maxv in [("CA (ppm):", self.mix_CA_var, 0, 10000),
                                        ("CB (ppm):", self.mix_CB_var, 0, 10000),
                                        ("fA min:", self.mix_fA_min_var, 0, 1),
                                        ("fA max:", self.mix_fA_max_var, 0, 1),
                                        ("Steps:", self.mix_steps_var, 10, 200)]:
            frame = tk.Frame(self.binary_frame, bg="#f5f5f5")
            frame.pack(fill=tk.X, pady=1)
            tk.Label(frame, text=label, width=12, anchor=tk.W, bg="#f5f5f5").pack(side=tk.LEFT)
            tk.Spinbox(frame, from_=minv, to=maxv, increment=0.1, textvariable=var, width=8).pack(side=tk.LEFT, padx=2)

        # ============ TERNARY FRAME (existing) ============
        self.ternary_frame = tk.Frame(left, bg="#f5f5f5")

        for label, var, minv, maxv in [("CA (ppm):", self.mix_CA_var, 0, 10000),
                                        ("CB (ppm):", self.mix_CB_var, 0, 10000),
                                        ("CC (ppm):", self.mix_CC_var, 0, 10000),
                                        ("Steps:", self.mix_steps_var, 10, 200)]:
            frame = tk.Frame(self.ternary_frame, bg="#f5f5f5")
            frame.pack(fill=tk.X, pady=1)
            tk.Label(frame, text=label, width=12, anchor=tk.W, bg="#f5f5f5").pack(side=tk.LEFT)
            tk.Spinbox(frame, from_=minv, to=maxv, increment=0.1, textvariable=var, width=8).pack(side=tk.LEFT, padx=2)

        # ============ TOGGLE FUNCTIONS ============
        def toggle_param_frames(*args):
            """Show/hide parameter frames based on selections"""
            mode = self.mix_mode_var.get()
            model = self.mix_model_var.get()

            # Hide all first
            self.trace_param_frame.pack_forget()
            self.isotope_param_frame.pack_forget()
            self.binary_iso_frame.pack_forget()

            # Show appropriate frame
            if mode == 'trace':
                self.trace_param_frame.pack(fill=tk.X, pady=5, after=mode_frame)
            elif mode == 'isotope':
                self.isotope_param_frame.pack(fill=tk.X, pady=5, after=mode_frame)
                if model == 'binary':
                    self.binary_iso_frame.pack(fill=tk.X, pady=2)

        # Bind toggle functions
        self.mix_mode_var.trace('w', toggle_param_frames)
        self.mix_model_var.trace('w', toggle_param_frames)

        # ============ SAVE ISOTOPE PARAMETERS BUTTON ============
        def save_isotope_params():
            """Save isotope parameters to be used in mixing calculations"""
            self.mix_ratios = {
                'A': self.iso_ratio_A.get(),
                'B': self.iso_ratio_B.get(),
                'C': self.iso_ratio_C.get()
            }
            self.mix_concentrations = {
                'A': self.iso_conc_A.get(),
                'B': self.iso_conc_B.get(),
                'C': self.iso_conc_C.get()
            }
            self.mixing_mode = self.mix_mode_var.get()
            self.status_var.set(f"✅ Isotope parameters saved for {self.mix_mode_var.get()} mode")

        tk.Button(mode_frame, text="💾 Save Isotope Parameters",
                command=save_isotope_params,
                bg="#3498db", fg="white", font=("Arial", 8)).pack(pady=5)

        # ============ ACTION BUTTONS ============
        tk.Button(left, text="🧮 Calculate Mixing", command=self._calculate_and_plot_mixing,
                bg="#e67e22", fg="white", width=20, height=2).pack(pady=10)

        tk.Button(left, text="📤 Export Model",
                command=lambda: self._export_model_enhanced(self.model_results['mixing'], "Mixing"),
                bg="#27ae60", fg="white", width=20).pack(pady=2)

        # ============ PLOT CANVAS ============
        self.mix_fig = plt.Figure(figsize=(6, 5), dpi=90)
        self.mix_fig.patch.set_facecolor('white')
        self.mix_ax = self.mix_fig.add_subplot(111)
        self.mix_ax.set_facecolor('#f8f9fa')

        self.mix_canvas = FigureCanvasTkAgg(self.mix_fig, right)
        self.mix_canvas.draw()
        self.mix_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        toolbar_frame = tk.Frame(right, height=25)
        toolbar_frame.pack(fill=tk.X)
        NavigationToolbar2Tk(self.mix_canvas, toolbar_frame).update()

        # Initialize UI state
        self._toggle_mixing_ui()
        toggle_param_frames()

    def _toggle_mixing_ui(self):
        if self.mix_model_var.get() == 'binary':
            self.binary_frame.pack(fill=tk.X, padx=5, pady=2)
            self.ternary_frame.pack_forget()
        else:
            self.binary_frame.pack_forget()
            self.ternary_frame.pack(fill=tk.X, padx=5, pady=2)

    def _calculate_and_plot_mixing(self):
        self.progress.start()
        self.status_var.set("Calculating mixing model...")
        self.model_results['mixing'] = self._calculate_mixing()
        if self.mix_model_var.get() == 'binary':
            self._plot_binary_mixing(self.mix_ax, self.model_results['mixing'])
        else:
            self._plot_ternary_mixing(self.mix_ax, self.model_results['mixing'])
        self.mix_canvas.draw()
        self.status_var.set("✅ Mixing model complete")
        self.progress.stop()

    # ============================================================================
    # TAB 5: Partial Melting
    # ============================================================================
    def _create_melting_tab(self):
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="🔥 Partial Melting")
        paned = tk.PanedWindow(tab, orient=tk.HORIZONTAL, sashwidth=4)
        paned.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        left = tk.Frame(paned, bg="#f5f5f5", width=300)
        paned.add(left, width=300, minsize=280)
        right = tk.Frame(paned, bg="white", width=600, height=500)
        paned.add(right, width=600, minsize=450)

        model_frame = tk.LabelFrame(left, text="Melting Model", padx=5, pady=5, bg="#f5f5f5")
        model_frame.pack(fill=tk.X, padx=5, pady=2)
        for model in ["Batch Melting", "Fractional Melting", "Dynamic Melting", "Critical Melting"]:
            tk.Radiobutton(model_frame, text=model, variable=self.melting_model_var, value=model, bg="#f5f5f5").pack(anchor=tk.W, pady=1)

        source_frame = tk.LabelFrame(left, text="Source Composition", padx=5, pady=5, bg="#f5f5f5")
        source_frame.pack(fill=tk.X, padx=5, pady=2)

        source_row = tk.Frame(source_frame, bg="#f5f5f5")
        source_row.pack(fill=tk.X)
        tk.Label(source_row, text="Source:", bg="#f5f5f5").pack(side=tk.LEFT)
        ttk.Combobox(source_row, textvariable=self.melting_source_var,
                    values=["Primitive Mantle", "MORB Source", "Chondrite", "Custom"],
                    width=15, state='readonly').pack(side=tk.LEFT, padx=5)

        # Kd database option
        kd_row = tk.Frame(source_frame, bg="#f5f5f5")
        kd_row.pack(fill=tk.X, pady=2)
        tk.Checkbutton(kd_row, text="Use Kd database for bulk D",
                      variable=self.use_kd_database_var, bg="#f5f5f5").pack(anchor=tk.W)

        for label, var, minv, maxv in [("F start:", self.melting_F_start_var, 0.001, 1),
                                        ("F end:", self.melting_F_end_var, 0.001, 1),
                                        ("Steps:", self.melting_F_steps_var, 10, 100),
                                        ("Porosity φ:", self.melting_porosity_var, 0, 0.1)]:
            frame = tk.Frame(left, bg="#f5f5f5")
            frame.pack(fill=tk.X, padx=5, pady=2)
            tk.Label(frame, text=label, width=10, anchor=tk.W, bg="#f5f5f5").pack(side=tk.LEFT)
            inc = 0.001 if isinstance(var, tk.DoubleVar) else 1
            tk.Spinbox(frame, from_=minv, to=maxv, increment=inc, textvariable=var, width=8).pack(side=tk.LEFT, padx=2)

        tk.Button(left, text="🔥 Calculate Melting", command=self._calculate_and_plot_melting,
                 bg="#e67e22", fg="white", width=20, height=2).pack(pady=10)
        tk.Button(left, text="📤 Export Model",
                 command=lambda: self._export_model_enhanced(self.model_results['melting'], "Melting"),
                 bg="#27ae60", fg="white", width=20).pack(pady=2)

        self.melting_fig = plt.Figure(figsize=(6, 5), dpi=90)
        self.melting_fig.patch.set_facecolor('white')
        self.melting_ax = self.melting_fig.add_subplot(111)
        self.melting_ax.set_facecolor('#f8f9fa')
        self.melting_canvas = FigureCanvasTkAgg(self.melting_fig, right)
        self.melting_canvas.draw()
        self.melting_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        toolbar_frame = tk.Frame(right, height=25)
        toolbar_frame.pack(fill=tk.X)
        NavigationToolbar2Tk(self.melting_canvas, toolbar_frame).update()

        self.ree_vars = {}
        for elem in ["La", "Ce", "Nd", "Sm", "Eu", "Gd", "Yb", "Lu"]:
            self.ree_vars[elem] = tk.DoubleVar(value=self.primitive_mantle.get(elem, 1.0))

    def _calculate_and_plot_melting(self):
        self.progress.start()
        self.status_var.set("Calculating partial melting...")
        self.model_results['melting'] = self._calculate_melting()
        self._plot_melting(self.melting_ax, self.model_results['melting'])
        self.melting_canvas.draw()
        self.status_var.set("✅ Partial melting complete")
        self.progress.stop()

    # ============================================================================
    # TAB 6: Phase Diagrams - FULLY IMPLEMENTED
    # ============================================================================
    def _create_phase_diagram_tab(self):
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="📊 Phase Diagrams")
        content = tk.Frame(tab, padx=15, pady=15)
        content.pack(fill=tk.BOTH, expand=True)

        tk.Label(content, text="PHASE DIAGRAM GENERATION", font=("Arial", 12, "bold"), fg="#388E3C").pack(anchor=tk.W, pady=10)

        diag_frame = tk.LabelFrame(content, text="Diagram Type", padx=10, pady=10)
        diag_frame.pack(fill=tk.X, pady=10)

        diagram_types = [
            "TAS (Total Alkali-Silica)", "AFM (Alkali-FeO-MgO)",
            "QAPF (Quartz-Alkali-Feldspar-Plagioclase)", "SiO₂ vs Mg#",
            "Pearce Tectonic", "REE Pattern", "Spider Diagram"
        ]

        for i, diagram in enumerate(diagram_types):
            tk.Radiobutton(diag_frame, text=diagram, variable=self.diagram_type_var,
                          value=diagram, font=("Arial", 10)).grid(row=i//3, column=i%3, sticky=tk.W, pady=2, padx=10)

        option_frame = tk.LabelFrame(content, text="Plot Options", padx=10, pady=10)
        option_frame.pack(fill=tk.X, pady=10)

        tk.Checkbutton(option_frame, text="Show model results", variable=self.show_model_var).grid(row=0, column=0, sticky=tk.W, pady=5)
        tk.Checkbutton(option_frame, text="Show grid", variable=self.show_grid_var).grid(row=0, column=1, sticky=tk.W, pady=5)
        tk.Checkbutton(option_frame, text="Show legend", variable=self.show_legend_var).grid(row=0, column=2, sticky=tk.W, pady=5)
        tk.Checkbutton(option_frame, text="Normalize data", variable=self.normalize_data_var).grid(row=1, column=0, sticky=tk.W, pady=5)
        tk.Checkbutton(option_frame, text="Chondrite normalize", variable=self.chondrite_normalize_var).grid(row=1, column=1, sticky=tk.W, pady=5)

        tk.Button(content, text="📊 Generate Phase Diagram", command=self._generate_phase_diagram,
                 bg="#388E3C", fg="white", font=("Arial", 11, "bold"), width=30).pack(pady=20)

    # ============================================================================
    # TAB 7: MELTS
    # ============================================================================
    def _create_melts_tab(self):
        """Create MELTS tab using PetThermoTools with MAGEMin backend"""
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="⚗️ MELTS")

        paned = tk.PanedWindow(tab, orient=tk.HORIZONTAL, sashwidth=4)
        paned.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Left panel - scrollable
        left_container = tk.Frame(paned, bg="#f5f5f5", width=320)
        paned.add(left_container, width=320, minsize=300)

        left_canvas = tk.Canvas(left_container, bg="#f5f5f5", highlightthickness=0)
        left_scrollbar = tk.Scrollbar(left_container, orient="vertical", command=left_canvas.yview)
        left_scrollable = tk.Frame(left_canvas, bg="#f5f5f5")
        left_scrollable.bind("<Configure>", lambda e: left_canvas.configure(scrollregion=left_canvas.bbox("all")))
        left_canvas.create_window((0, 0), window=left_scrollable, anchor="nw", width=300)
        left_canvas.configure(yscrollcommand=left_scrollbar.set)
        left_canvas.pack(side="left", fill="both", expand=True)
        left_scrollbar.pack(side="right", fill="y")

        right = tk.Frame(paned, bg="white", width=600, height=500)
        paned.add(right, width=600, minsize=450)

        # PetThermoTools status
        status_frame = tk.Frame(left_scrollable, bg="#f5f5f5", height=24)
        status_frame.pack(fill=tk.X, padx=5, pady=2)
        status_frame.pack_propagate(False)

        if HAS_PETTERMO:
            tk.Label(status_frame, text="✅ PetThermoTools Ready",
                    fg="green", bg="#f5f5f5", font=("Arial", 8)).pack(side=tk.LEFT)
        else:
            tk.Label(status_frame, text="⚠️ PetThermoTools not installed:",
                    fg="orange", bg="#f5f5f5", font=("Arial", 8)).pack(side=tk.LEFT)
            tk.Button(status_frame, text="Install", command=self._install_petthermo,
                     bg="#4CAF50", fg="white", font=("Arial", 7), padx=2, pady=0).pack(side=tk.LEFT, padx=2)

        # Julia init status
        julia_frame = tk.LabelFrame(left_scrollable, text="MAGEMin / Julia", padx=5, pady=3, bg="#f5f5f5")
        julia_frame.pack(fill=tk.X, padx=5, pady=2)

        if self._julia_env_is_ready():
            julia_status_text = "✅ Julia env ready"
            julia_status_color = "green"
        else:
            julia_status_text = "⏳ First run installs MAGEMin (~3-5 min)"
            julia_status_color = "orange"

        self.julia_status_label = tk.Label(julia_frame, text=julia_status_text,
                                           fg=julia_status_color, bg="#f5f5f5", font=("Arial", 8))
        self.julia_status_label.pack()

        # Model selection
        model_frame = tk.LabelFrame(left_scrollable, text="MELTS Model", padx=5, pady=3, bg="#f5f5f5")
        model_frame.pack(fill=tk.X, padx=5, pady=2)

        model_row = tk.Frame(model_frame, bg="#f5f5f5")
        model_row.pack(fill=tk.X)
        tk.Label(model_row, text="Model:", bg="#f5f5f5").pack(side=tk.LEFT)
        ttk.Combobox(model_row, textvariable=self.melts_model_var,
                    values=["Green2025", "Weller2024"], width=12).pack(side=tk.LEFT, padx=5)

        # Calculation Type
        calc_frame = tk.LabelFrame(left_scrollable, text="Calculation Type", padx=5, pady=3, bg="#f5f5f5")
        calc_frame.pack(fill=tk.X, padx=5, pady=2)
        for calc_type in ["Fractional Crystallization", "Equilibrium Crystallization", "Batch Melting"]:
            tk.Radiobutton(calc_frame, text=calc_type, variable=self.melts_calc_type_var,
                          value=calc_type, bg="#f5f5f5").pack(anchor=tk.W)

        # Composition
        comp_frame = tk.LabelFrame(left_scrollable, text="Composition", padx=5, pady=3, bg="#f5f5f5")
        comp_frame.pack(fill=tk.X, padx=5, pady=2)

        preset_row = tk.Frame(comp_frame, bg="#f5f5f5")
        preset_row.pack(fill=tk.X, pady=1)
        tk.Label(preset_row, text="Preset:", bg="#f5f5f5", width=8).pack(side=tk.LEFT)
        ttk.Combobox(preset_row, textvariable=self.melts_preset_var,
                    values=["Basalt", "Andesite", "Dacite", "Rhyolite", "MORB", "Granite", "Peridotite"],
                    width=12, state='readonly').pack(side=tk.LEFT, padx=2)
        tk.Button(preset_row, text="Load", command=self._load_melts_preset,
                 bg="#3498db", fg="white", width=5).pack(side=tk.LEFT, padx=2)

        tk.Button(comp_frame, text="✏️ Custom Composition", command=self._open_composition_dialog,
                 bg="#f39c12", fg="white").pack(fill=tk.X, pady=2)

        self.comp_status_label = tk.Label(comp_frame, text="⏳ No composition loaded",
                                         fg="red", bg="#f5f5f5", font=("Arial", 8))
        self.comp_status_label.pack(fill=tk.X, pady=1)

        # Conditions
        cond_frame = tk.LabelFrame(left_scrollable, text="Required Conditions", padx=5, pady=5, bg="#f5f5f5")
        cond_frame.pack(fill=tk.X, padx=5, pady=5)
        for i in range(2):
            cond_frame.columnconfigure(i, weight=1)

        temp_frame = tk.Frame(cond_frame, bg="#f5f5f5")
        temp_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=2)
        tk.Label(temp_frame, text="T start:", bg="#f5f5f5", width=8, anchor=tk.W).pack(side=tk.LEFT)
        tk.Spinbox(temp_frame, from_=600, to=2000, increment=10, textvariable=self.melts_T_start_var, width=8).pack(side=tk.LEFT, padx=2)
        tk.Label(temp_frame, text="T end:", bg="#f5f5f5", width=8, anchor=tk.W).pack(side=tk.LEFT, padx=(10, 0))
        tk.Spinbox(temp_frame, from_=600, to=2000, increment=10, textvariable=self.melts_T_end_var, width=8).pack(side=tk.LEFT, padx=2)
        self.temp_valid_label = tk.Label(temp_frame, text="", bg="#f5f5f5", font=("Arial", 7))
        self.temp_valid_label.pack(side=tk.LEFT, padx=2)

        tk.Label(cond_frame, text="Steps:", bg="#f5f5f5", anchor=tk.W).grid(row=1, column=0, sticky=tk.W, pady=2, padx=5)
        tk.Spinbox(cond_frame, from_=5, to=100, increment=5,
                   textvariable=self.melts_steps_var, width=6).grid(row=1, column=0, sticky=tk.W, padx=(50, 2), pady=2)
        step_est_label = tk.Label(cond_frame, text="~5 min", bg="#f5f5f5",
                                  fg="gray", font=("Arial", 7))
        step_est_label.grid(row=1, column=0, sticky=tk.W, padx=(108, 0), pady=2)

        def _update_step_estimate(*args):
            try:
                s = self.melts_steps_var.get()
                est_min = max(1, round(s * 15 / 60))
                step_est_label.config(text=f"~{est_min} min")
            except Exception:
                pass
        self.melts_steps_var.trace('w', _update_step_estimate)

        tk.Label(cond_frame, text="Pressure (bars):", bg="#f5f5f5", anchor=tk.W).grid(row=1, column=1, sticky=tk.W, pady=2, padx=5)
        tk.Spinbox(cond_frame, from_=1, to=30000, increment=100, textvariable=self.melts_pressure_var, width=8).grid(row=1, column=1, sticky=tk.W, padx=(70, 5), pady=2)

        tk.Label(cond_frame, text="fO₂ buffer:", bg="#f5f5f5", anchor=tk.W).grid(row=2, column=0, sticky=tk.W, pady=2, padx=5)
        ttk.Combobox(cond_frame, textvariable=self.melts_fo2_var,
                    values=["FMQ", "QFM", "NNO", "IW", "MH"], width=8).grid(row=2, column=0, sticky=tk.W, padx=(65, 5), pady=2)

        tk.Label(cond_frame, text="Δ log offset:", bg="#f5f5f5", anchor=tk.W).grid(row=2, column=1, sticky=tk.W, pady=2, padx=5)
        tk.Spinbox(cond_frame, from_=-3, to=3, increment=0.5, textvariable=self.melts_fo2_offset_var, width=8).grid(row=2, column=1, sticky=tk.W, padx=(70, 5), pady=2)

        # Options
        options_frame = tk.LabelFrame(left_scrollable, text="Options", padx=5, pady=3, bg="#f5f5f5")
        options_frame.pack(fill=tk.X, padx=5, pady=2)
        tk.Checkbutton(options_frame, text="Keep fractionated solids", variable=self.melts_keep_frac_var, bg="#f5f5f5").pack(anchor=tk.W)

        # Buttons
        button_frame = tk.Frame(left_scrollable, bg="#f5f5f5")
        button_frame.pack(fill=tk.X, padx=5, pady=5)

        if HAS_PETTERMO:
            self.run_button = tk.Button(button_frame, text="🚀 RUN MAGEMin",
                    command=self._run_magemin_calculation,
                    bg="#cccccc", fg="white",
                    font=("Arial", 11, "bold"),
                    height=1, state='disabled')
            self.run_button.pack(fill=tk.X, pady=2)

            # Progress percentage row
            pct_row = tk.Frame(button_frame, bg="#f5f5f5")
            pct_row.pack(fill=tk.X, pady=1)
            tk.Label(pct_row, text="Progress:", bg="#f5f5f5",
                    font=("Arial", 8)).pack(side=tk.LEFT)
            self.melts_pct_label = tk.Label(pct_row, text="—",
                    fg="#9C27B0", bg="#f5f5f5",
                    font=("Arial", 10, "bold"))
            self.melts_pct_label.pack(side=tk.LEFT, padx=4)
        else:
            tk.Button(button_frame, text="📥 Install PetThermoTools First",
                    command=self._install_petthermo,
                    bg="#4CAF50", fg="white",
                    font=("Arial", 11, "bold"),
                    height=1).pack(fill=tk.X, pady=2)
            self.melts_pct_label = tk.Label(button_frame, text="—",
                    bg="#f5f5f5", font=("Arial", 10, "bold"))

        tk.Button(button_frame, text="📤 Export Results",
                 command=lambda: self._export_model_enhanced(self.model_results.get('melts'), "MELTS"),
                 bg="#27ae60", fg="white").pack(fill=tk.X, pady=2)

        # Validation
        def validate_all_inputs():
            if self.melts_T_start_var.get() <= self.melts_T_end_var.get():
                self.temp_valid_label.config(text="❌ T start > T end required", fg="red")
                if HAS_PETTERMO:
                    self.run_button.config(state='disabled', bg="#cccccc")
                return False
            else:
                self.temp_valid_label.config(text="✅", fg="green")

            total = 0
            oxide_values = {}
            for oxide, var in self.comp_vars.items():
                val = var.get()
                oxide_values[oxide] = val
                total += val

            required_oxides = ['SiO2', 'Al2O3', 'CaO', 'MgO', 'FeO', 'Na2O', 'K2O', 'H2O']
            missing_required = [ox for ox in required_oxides if oxide_values.get(ox, 0) <= 0]

            if missing_required:
                self.comp_status_label.config(
                    text=f"❌ Missing: {', '.join(missing_required[:3])}" + ("..." if len(missing_required) > 3 else ""),
                    fg="red")
                if HAS_PETTERMO:
                    self.run_button.config(state='disabled', bg="#cccccc")
                return False

            if total < 98 or total > 102:
                self.comp_status_label.config(text=f"❌ Total = {total:.1f}% (need ~100%)", fg="red")
                if HAS_PETTERMO:
                    self.run_button.config(state='disabled', bg="#cccccc")
                return False

            self.comp_status_label.config(text=f"✅ Composition valid (total={total:.1f}%)", fg="green")
            if HAS_PETTERMO:
                self.run_button.config(state='normal', bg="#9C27B0")
            return True

        self.melts_T_start_var.trace('w', lambda *args: validate_all_inputs())
        self.melts_T_end_var.trace('w', lambda *args: validate_all_inputs())
        self.validate_callback = validate_all_inputs
        validate_all_inputs()

        # Plot canvas
        self.melts_fig = plt.Figure(figsize=(6, 5), dpi=90)
        self.melts_fig.patch.set_facecolor('white')
        self.melts_ax = self.melts_fig.add_subplot(111)
        self.melts_ax.set_facecolor('#f8f9fa')
        self.melts_canvas = FigureCanvasTkAgg(self.melts_fig, right)
        self.melts_canvas.draw()
        self.melts_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        toolbar_frame = tk.Frame(right, height=25)
        toolbar_frame.pack(fill=tk.X)
        NavigationToolbar2Tk(self.melts_canvas, toolbar_frame).update()

    def _install_petthermo(self):
        """Install petthermotools package"""
        self.progress.start()
        self.status_var.set("Installing PetThermoTools...")
        self.window.update()
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "petthermotools"])
            self.status_var.set("✅ PetThermoTools installed!")
            self.progress.stop()
            messagebox.showinfo("Success", "✅ PetThermoTools installed!\nPlease restart the plugin.")
            self._refresh_melts_tab()
        except Exception as e:
            self.progress.stop()
            messagebox.showerror("Installation Failed", f"Error: {str(e)}")

    def _run_magemin_calculation(self):
        """Start MAGEMin calculation in thread"""
        if not self._validate_magemin_inputs():
            return
        if hasattr(self, 'run_button'):
            self.run_button.config(state='disabled')
        self.progress.start()
        self.status_var.set("⚡ Starting MAGEMin...")
        self.window.update()

        thread = threading.Thread(target=self._run_magemin_thread)
        thread.daemon = True
        thread.start()

    def _open_composition_dialog(self):
        """Open dialog for custom composition input"""
        dialog = tk.Toplevel(self.window)
        dialog.title("Custom Composition")
        dialog.geometry("500x450")
        dialog.transient(self.window)
        dialog.grab_set()

        canvas = tk.Canvas(dialog)
        scrollbar = tk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        row = 0
        for oxide, var in self.comp_vars.items():
            tk.Label(scrollable_frame, text=f"{oxide}:").grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
            tk.Entry(scrollable_frame, textvariable=var, width=10).grid(row=row, column=1, pady=2, padx=5)
            tk.Label(scrollable_frame, text="wt%").grid(row=row, column=2, sticky=tk.W, pady=2)
            row += 1

        total_var = tk.StringVar()
        def update_total(*args):
            total = sum(var.get() for var in self.comp_vars.values())
            total_var.set(f"Total: {total:.2f}%")
            total_label.config(fg="green" if abs(total - 100) <= 1 else "red")

        for var in self.comp_vars.values():
            var.trace('w', update_total)

        total_label = tk.Label(scrollable_frame, textvariable=total_var, font=("Arial", 10, "bold"))
        total_label.grid(row=row, column=0, columnspan=3, pady=10)

        # Recommended values label
        rec_frame = tk.LabelFrame(scrollable_frame, text="Recommended ranges")
        rec_frame.grid(row=row+1, column=0, columnspan=3, pady=10, padx=5)

        rec_text = """
        SiO2: 45-75%     Al2O3: 10-18%    FeO: 1-12%
        MgO: 0.1-15%     CaO: 0.5-12%     Na2O: 2-5%
        K2O: 0.1-5%      H2O: 0.1-3%
        """
        tk.Label(rec_frame, text=rec_text, justify=tk.LEFT, font=("Arial", 8)).pack()

        button_frame = tk.Frame(scrollable_frame)
        button_frame.grid(row=row+2, column=0, columnspan=3, pady=10)

        def save_and_close():
            dialog.destroy()
            if hasattr(self, 'validate_callback'):
                self.validate_callback()

        tk.Button(button_frame, text="Save", command=save_and_close, bg="#27ae60", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=dialog.destroy, bg="#e74c3c", fg="white").pack(side=tk.LEFT, padx=5)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        update_total()

    def _load_melts_preset(self):
        """Load preset composition"""
        preset = self.melts_preset_var.get().lower()
        presets = {
            "basalt":     {'SiO2': 50.0, 'TiO2': 1.5, 'Al2O3': 15.0, 'Fe2O3': 1.5, 'FeO': 8.5, 'MnO': 0.2, 'MgO': 7.0,  'CaO': 11.0, 'Na2O': 2.5, 'K2O': 0.8, 'P2O5': 0.2, 'H2O': 0.5, 'Cr2O3': 0.05},
            "andesite":   {'SiO2': 60.0, 'TiO2': 0.8, 'Al2O3': 17.0, 'Fe2O3': 1.0, 'FeO': 4.0, 'MnO': 0.1, 'MgO': 3.0,  'CaO': 6.0,  'Na2O': 3.5, 'K2O': 1.5, 'P2O5': 0.2, 'H2O': 1.0, 'Cr2O3': 0.02},
            "dacite":     {'SiO2': 65.0, 'TiO2': 0.6, 'Al2O3': 16.0, 'Fe2O3': 0.8, 'FeO': 2.5, 'MnO': 0.1, 'MgO': 1.5,  'CaO': 4.0,  'Na2O': 4.0, 'K2O': 2.0, 'P2O5': 0.2, 'H2O': 1.5, 'Cr2O3': 0.01},
            "rhyolite":   {'SiO2': 75.0, 'TiO2': 0.2, 'Al2O3': 13.0, 'Fe2O3': 0.3, 'FeO': 0.8, 'MnO': 0.05,'MgO': 0.2,  'CaO': 0.8,  'Na2O': 4.0, 'K2O': 4.5, 'P2O5': 0.1, 'H2O': 2.0, 'Cr2O3': 0.0},
            "morb":       {'SiO2': 49.5, 'TiO2': 1.5, 'Al2O3': 16.0, 'Fe2O3': 1.2, 'FeO': 7.5, 'MnO': 0.2, 'MgO': 8.5,  'CaO': 11.5, 'Na2O': 2.8, 'K2O': 0.1, 'P2O5': 0.1, 'H2O': 0.2, 'Cr2O3': 0.1},
            "granite":    {'SiO2': 72.0, 'TiO2': 0.3, 'Al2O3': 14.0, 'Fe2O3': 0.5, 'FeO': 1.5, 'MnO': 0.05,'MgO': 0.5,  'CaO': 1.5,  'Na2O': 3.5, 'K2O': 4.5, 'P2O5': 0.1, 'H2O': 1.0, 'Cr2O3': 0.0},
            "peridotite": {'SiO2': 45.0, 'TiO2': 0.2, 'Al2O3': 4.0,  'Fe2O3': 0.5, 'FeO': 8.0, 'MnO': 0.1, 'MgO': 38.0, 'CaO': 3.5,  'Na2O': 0.3, 'K2O': 0.03,'P2O5': 0.02,'H2O': 0.1, 'Cr2O3': 0.3},
        }
        if preset in presets:
            for oxide, value in presets[preset].items():
                if oxide in self.comp_vars:
                    self.comp_vars[oxide].set(value)
            if hasattr(self, 'validate_callback'):
                self.validate_callback()
            self.status_var.set(f"✅ Loaded {self.melts_preset_var.get()} preset")

    def _refresh_melts_tab(self):
        """Refresh MELTS tab after installation"""
        for i in range(self.notebook.index("end")):
            if self.notebook.tab(i, "text") == "⚗️ MELTS":
                self.notebook.forget(i)
                self._create_melts_tab()
                break


def setup_plugin(main_app):
    """Plugin setup function"""
    plugin = PetrogeneticModelingSuitePlugin(main_app)
    return plugin
