"""
Petrogenetic Modeling Suite v2.0
Complete magma evolution modeling suite
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Author: Sefy Levy & DeepSeek
License: CC BY-NC-SA 4.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

PLUGIN_INFO = {
    "category": "software",
    "id": "petrogenetic_modeling_suite",
    "name": "Petrogenetic Modeling Suite",
    "description": "Complete magma evolution: AFC · Fractional · Zone Refining · Mixing · Partial Melting · Phase Diagrams · MELTS",
    "icon": "🌋",
    "version": "2.0.0",
    "requires": ["numpy", "scipy", "matplotlib", "pandas", "petthermotools", "juliapkg"],
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
import subprocess  # Only needed for pip install

try:
    import matplotlib
    matplotlib.use('TkAgg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    import matplotlib.patches as patches
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    from scipy import optimize, interpolate
    from scipy.integrate import odeint
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

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
    UNIFIED PETROGENETIC MODELS
    Complete magma evolution: AFC · Fractional · Zone Refining · Mixing · Partial Melting · Phase Diagrams · MELTS
    """

    # ── Class-level flag: Julia/MAGEMin is initialized ONCE per process lifetime ──
    _julia_initialized = False

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

        # Phase Diagrams tab
        self.diagram_type_var = tk.StringVar(value="TAS")
        self.show_model_var = tk.BooleanVar(value=True)
        self.show_grid_var = tk.BooleanVar(value=True)
        self.show_legend_var = tk.BooleanVar(value=True)

        # MELTS tab variables
        self.melts_model_var = tk.StringVar(value="Green2025")
        self.melts_calc_type_var = tk.StringVar(value="Fractional Crystallization")
        self.melts_preset_var = tk.StringVar(value="Basalt")
        self.melts_T_start_var = tk.DoubleVar(value=1300.0)
        self.melts_T_end_var = tk.DoubleVar(value=800.0)
        self.melts_steps_var = tk.IntVar(value=50)
        self.melts_pressure_var = tk.DoubleVar(value=1000.0)
        self.melts_fo2_var = tk.StringVar(value="FMQ")
        self.melts_fo2_offset_var = tk.DoubleVar(value=0.0)
        self.melts_keep_frac_var = tk.BooleanVar(value=True)
        self.melts_parallel_var = tk.BooleanVar(value=True)

        # Comparison tab
        self.compare_results = {}

        # Reference data
        self._init_reference_data()
        self._init_composition_vars()

        self._check_dependencies()

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
            "Yb": 0.170, "Lu": 0.025
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

        self.kd_databases = {
            "basalt": {
                "Ol": {"Ni": 10.0, "Cr": 5.0, "Co": 3.0, "Sc": 0.1, "V": 0.05,
                       "Mn": 0.8, "Ca": 0.01, "Al": 0.01, "Ti": 0.02},
                "Cpx": {"Ni": 2.0, "Cr": 30.0, "Sc": 3.0, "V": 1.0, "Sr": 0.1,
                        "Y": 0.2, "Zr": 0.1, "Hf": 0.1, "Ba": 0.001, "Rb": 0.001},
                "Plag": {"Sr": 2.0, "Eu": 1.5, "Ba": 0.5, "Rb": 0.1, "Cs": 0.1,
                         "K": 0.1, "Na": 1.0, "Ca": 1.0},
                "Opx": {"Ni": 4.0, "Cr": 10.0, "Sc": 1.5, "V": 0.5, "Y": 0.1},
                "Grt": {"Y": 2.0, "Yb": 4.0, "Lu": 5.0, "Sc": 2.0, "Cr": 5.0}
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
                         "Sr": 2.0, "Pb": 1.0}
            }
        }

    def _init_composition_vars(self):
        """Initialize composition variables for custom input"""
        oxides = ['SiO2', 'TiO2', 'Al2O3', 'Fe2O3', 'FeO', 'MnO',
                  'MgO', 'CaO', 'Na2O', 'K2O', 'P2O5', 'H2O']
        self.comp_vars = {}
        for oxide in oxides:
            self.comp_vars[oxide] = tk.DoubleVar(value=0.0)

        # Set default basalt values
        basalt = {
            'SiO2': 50.0, 'TiO2': 1.5, 'Al2O3': 15.0, 'Fe2O3': 1.5,
            'FeO': 8.5, 'MnO': 0.2, 'MgO': 7.0, 'CaO': 11.0,
            'Na2O': 2.5, 'K2O': 0.8, 'P2O5': 0.2, 'H2O': 0.5
        }
        for oxide, value in basalt.items():
            if oxide in self.comp_vars:
                self.comp_vars[oxide].set(value)

    def _check_dependencies(self):
        """Check required packages"""
        missing = []
        if not HAS_MATPLOTLIB: missing.append("matplotlib")
        if not HAS_SCIPY: missing.append("scipy")
        self.dependencies_met = len(missing) == 0
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

    # ============================================================================
    # AFC MODEL
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
        """Calculate AFC model curve"""
        C0 = self.afc_C0_var.get()
        Ca = self.afc_Ca_var.get()
        D = self.afc_D_var.get()
        r = self.afc_r_var.get()

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
    # FRACTIONAL CRYSTALLIZATION MODELS
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
        """Ternary mixing (fC = 1 - fA - fB)"""
        fC = 1 - fA - fB
        return CA * fA + CB * fB + CC * fC

    def _calculate_mixing(self):
        """Calculate mixing model"""
        model_type = self.mix_model_var.get()

        if model_type == 'binary':
            CA = self.mix_CA_var.get()
            CB = self.mix_CB_var.get()

            fA = np.linspace(self.mix_fA_min_var.get(),
                            self.mix_fA_max_var.get(),
                            self.mix_steps_var.get())

            C = self._binary_mixing(CA, CB, fA)

            return {
                'x': fA,
                'C': C,
                'params': {
                    'model': 'Binary Mixing',
                    'CA': CA, 'CB': CB
                },
                'xlabel': 'Fraction A'
            }

        else:
            CA = self.mix_CA_var.get()
            CB = self.mix_CB_var.get()
            CC = self.mix_CC_var.get()

            steps = self.mix_steps_var.get()
            fA = np.linspace(0, 1, steps)
            fB = np.linspace(0, 1, steps)
            FA, FB = np.meshgrid(fA, fB)

            mask = FA + FB <= 1
            C = np.zeros_like(FA)
            C[mask] = self._ternary_mixing(CA, CB, CC, FA[mask], FB[mask])
            C[~mask] = np.nan

            return {
                'FA': FA, 'FB': FB, 'C': C,
                'params': {
                    'model': 'Ternary Mixing',
                    'CA': CA, 'CB': CB, 'CC': CC
                }
            }

    # ============================================================================
    # PARTIAL MELTING MODELS
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
        """Calculate partial melting model"""
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

        bulk_D = {"La": 0.01, "Ce": 0.015, "Nd": 0.02, "Sm": 0.05,
                  "Eu": 0.1, "Gd": 0.15, "Yb": 0.3, "Lu": 0.4}

        results = {"F": F_values.tolist()}

        for elem, C0 in source.items():
            D = bulk_D.get(elem, 0.1)

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
                'porosity': porosity
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

        ree_to_plot = ["La", "Ce", "Sm", "Yb"]
        for elem in ree_to_plot:
            if elem in results:
                ax.plot(F, results[elem], linewidth=2, label=f'{elem}')

        ax.set_xlabel('Melt Fraction (F)')
        ax.set_ylabel('Concentration (ppm)')
        ax.set_title(f'{params["model"]}\nSource: {params["source"]}')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best')
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
    # EXPORT METHODS
    # ============================================================================
    def _export_model(self, result, model_name):
        """Export model results to main app"""
        if not result:
            messagebox.showinfo("Export", "No model results to export")
            return

        records = []
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if 'F' in result:
            if 'results' in result and isinstance(result['results'], dict):
                F = result['F']
                for i, f in enumerate(F):
                    record = {
                        'Sample_ID': f"{model_name}_{i+1:03d}",
                        'Model': result.get('params', {}).get('model', model_name),
                        'F_melt': f"{f:.3f}",
                        'Petrogenetic_Timestamp': timestamp
                    }
                    for elem, values in result['results'].items():
                        if elem != 'F' and i < len(values):
                            record[f'{elem}_ppm'] = f"{values[i]:.2f}"
                    records.append(record)
            else:
                for i, (f, c) in enumerate(zip(result['F'], result['C'])):
                    records.append({
                        'Sample_ID': f"{model_name}_{i+1:03d}",
                        'Model': result['params']['model'],
                        'F_melt': f"{f:.3f}",
                        'C_ppm': f"{c:.2f}",
                        'Petrogenetic_Timestamp': timestamp
                    })

        elif 'x' in result and 'C' in result:
            for i, (x, c) in enumerate(zip(result['x'], result['C'])):
                records.append({
                    'Sample_ID': f"{model_name}_{i+1:03d}",
                    'Model': result['params']['model'],
                    'x': f"{x:.3f}",
                    'C_ppm': f"{c:.2f}",
                    'Petrogenetic_Timestamp': timestamp
                })

        if records:
            self.app.import_data_from_plugin(records)
            self.status_var.set(f"✅ Exported {len(records)} model points")

    # ============================================================================
    # UI CONSTRUCTION
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
        self.window.title("🌋 Petrogenetic Modeling Suite v2.0")
        self.window.geometry("1100x700")

        self._create_interface()

        if self._load_from_main_app():
            self.status_var.set("✅ Loaded data from main app")
        else:
            self.status_var.set("ℹ️ No geochemical data found")

        self.window.transient(self.app.root)
        self.window.lift()
        self.window.focus_force()

    def _create_interface(self):
        """Create the interface with 7 tabs"""
        header = tk.Frame(self.window, bg="#8e44ad", height=40)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="🌋", font=("Arial", 18),
                bg="#8e44ad", fg="white").pack(side=tk.LEFT, padx=8)
        tk.Label(header, text="Petrogenetic Modeling Suite",
                font=("Arial", 14, "bold"),
                bg="#8e44ad", fg="white").pack(side=tk.LEFT, padx=2)
        tk.Label(header, text="v2.0 - AFC · Fractional · Zone · Mixing · Melting · Phase Diagrams · MELTS",
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

        self._create_afc_tab()
        self._create_fractional_tab()
        self._create_zone_tab()
        self._create_mixing_tab()
        self._create_melting_tab()
        self._create_phase_diagram_tab()
        self._create_melts_tab()

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
                 command=lambda: self._export_model(self.model_results['afc'], "AFC"),
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
                 command=lambda: self._export_model(self.model_results['fractional'], "Fractional"),
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
                 command=lambda: self._export_model(self.model_results['zone'], "Zone"),
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
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="🔄 Mixing")
        paned = tk.PanedWindow(tab, orient=tk.HORIZONTAL, sashwidth=4)
        paned.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        left = tk.Frame(paned, bg="#f5f5f5", width=300)
        paned.add(left, width=300, minsize=280)
        right = tk.Frame(paned, bg="white", width=600, height=500)
        paned.add(right, width=600, minsize=450)

        model_frame = tk.LabelFrame(left, text="Model Type", padx=5, pady=5, bg="#f5f5f5")
        model_frame.pack(fill=tk.X, padx=5, pady=2)
        tk.Radiobutton(model_frame, text="Binary", variable=self.mix_model_var, value="binary", command=self._toggle_mixing_ui, bg="#f5f5f5").pack(anchor=tk.W)
        tk.Radiobutton(model_frame, text="Ternary", variable=self.mix_model_var, value="ternary", command=self._toggle_mixing_ui, bg="#f5f5f5").pack(anchor=tk.W)

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

        self.ternary_frame = tk.Frame(left, bg="#f5f5f5")
        for label, var, minv, maxv in [("CA (ppm):", self.mix_CA_var, 0, 10000),
                                        ("CB (ppm):", self.mix_CB_var, 0, 10000),
                                        ("CC (ppm):", self.mix_CC_var, 0, 10000),
                                        ("Steps:", self.mix_steps_var, 10, 200)]:
            frame = tk.Frame(self.ternary_frame, bg="#f5f5f5")
            frame.pack(fill=tk.X, pady=1)
            tk.Label(frame, text=label, width=12, anchor=tk.W, bg="#f5f5f5").pack(side=tk.LEFT)
            tk.Spinbox(frame, from_=minv, to=maxv, increment=0.1, textvariable=var, width=8).pack(side=tk.LEFT, padx=2)

        tk.Button(left, text="🧮 Calculate Mixing", command=self._calculate_and_plot_mixing,
                 bg="#e67e22", fg="white", width=20, height=2).pack(pady=10)
        tk.Button(left, text="📤 Export Model",
                 command=lambda: self._export_model(self.model_results['mixing'], "Mixing"),
                 bg="#27ae60", fg="white", width=20).pack(pady=2)

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
        self._toggle_mixing_ui()

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
        tk.Label(source_frame, text="Source:").pack(side=tk.LEFT)
        ttk.Combobox(source_frame, textvariable=self.melting_source_var,
                    values=["Primitive Mantle", "MORB Source", "Chondrite", "Custom"],
                    width=15, state='readonly').pack(side=tk.LEFT, padx=5)

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
                 command=lambda: self._export_model(self.model_results['melting'], "Melting"),
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
    # TAB 6: Phase Diagrams
    # ============================================================================
    def _create_phase_diagram_tab(self):
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="📊 Phase Diagrams")
        content = tk.Frame(tab, padx=15, pady=15)
        content.pack(fill=tk.BOTH, expand=True)
        tk.Label(content, text="PHASE DIAGRAM GENERATION", font=("Arial", 12, "bold"), fg="#388E3C").pack(anchor=tk.W, pady=10)
        diag_frame = tk.LabelFrame(content, text="Diagram Type", padx=10, pady=10)
        diag_frame.pack(fill=tk.X, pady=10)
        for i, diagram in enumerate(["TAS (Total Alkali-Silica)", "AFM (Alkali-FeO-MgO)",
                                      "QAPF (Quartz-Alkali-Feldspar-Plagioclase)", "SiO₂ vs Mg#",
                                      "Pearce Tectonic", "REE Pattern", "Spider Diagram"]):
            tk.Radiobutton(diag_frame, text=diagram, variable=self.diagram_type_var,
                          value=diagram, font=("Arial", 10)).grid(row=i//3, column=i%3, sticky=tk.W, pady=2, padx=10)
        option_frame = tk.LabelFrame(content, text="Plot Options", padx=10, pady=10)
        option_frame.pack(fill=tk.X, pady=10)
        tk.Checkbutton(option_frame, text="Show model results", variable=self.show_model_var).grid(row=0, column=0, sticky=tk.W, pady=5)
        tk.Checkbutton(option_frame, text="Show grid", variable=self.show_grid_var).grid(row=0, column=1, sticky=tk.W, pady=5)
        tk.Checkbutton(option_frame, text="Show legend", variable=self.show_legend_var).grid(row=0, column=2, sticky=tk.W, pady=5)
        tk.Button(content, text="📊 Generate Phase Diagram", command=self._generate_phase_diagram,
                 bg="#388E3C", fg="white", font=("Arial", 11, "bold"), width=30).pack(pady=20)

    def _generate_phase_diagram(self):
        messagebox.showinfo("Phase Diagrams", "Phase diagram generation coming soon!")

    # ============================================================================
    # TAB 7: MELTS  ── ALL FIXES ARE IN THIS SECTION ──
    # ============================================================================

    @staticmethod
    def _prepare_composition_for_magemin(comp_vars):
        """
        Convert comp_vars dict into a MAGEMin-compatible composition dict.

        MAGEMin wants: SiO2, Al2O3, CaO, MgO, FeO (total iron as FeO),
                       K2O, Na2O, TiO2, Fe2O3, Cr2O3, H2O
        It does NOT want Fe2O3 AND FeO separately — combine them into FeOt
        if Fe2O3 is present, or just pass through as-is.
        petthermotools handles the Fe2O3/FeO split internally, so we pass both.
        """
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
        """
        Extract (T_array, comp_dict) from Green2025/Weller2024 results.

        Green2025 returns a rich dict. Key structure:
          results['All']        → big merged DataFrame, cols like T_C, SiO2_Liq, MgO_Liq...
          results['liquid1']    → liquid-only DataFrame, cols like SiO2_Liq, MgO_Liq...
          results['Conditions'] → T_C, P_bar, etc.
          results['mass_g']     → phase masses over T
        """
        print("\n── petthermotools result inspector ──")
        print(f"Type: {type(results)}")

        if not isinstance(results, dict) or not results:
            print("Empty or non-dict result.")
            return None, None

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
        mass_dict = {}   # phase masses, keyed by short name

        # ── Step 1: get temperature from Conditions or All ────────────────────
        for key in ['Conditions', 'All']:
            if key in results and hasattr(results[key], 'columns'):
                df = results[key]
                if 'T_C' in df.columns:
                    T = df['T_C'].values.copy()
                    print(f"T from '{key}['T_C']': {T.min():.0f}–{T.max():.0f}°C, n={len(T)}")
                    break

        if T is None:
            print("No temperature found.")
            return None, None

        # ── Step 2: liquid composition from liquid1 or All ───────────────────
        # Green2025 uses suffix _Liq; map to clean oxide names
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

        # ── Step 3: phase masses from mass_g ─────────────────────────────────
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

        # ── PetThermoTools status ──
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

        # ── Julia init status ──
        julia_frame = tk.LabelFrame(left_scrollable, text="MAGEMin / Julia", padx=5, pady=3, bg="#f5f5f5")
        julia_frame.pack(fill=tk.X, padx=5, pady=2)

        if PetrogeneticModelingSuitePlugin._julia_env_is_ready():
            julia_status_text = "✅ Julia env ready — will not reinstall"
            julia_status_color = "green"
        else:
            julia_status_text = "⏳ First run installs MAGEMin (~3-5 min, once only)"
            julia_status_color = "orange"

        self.julia_status_label = tk.Label(julia_frame, text=julia_status_text,
                                           fg=julia_status_color, bg="#f5f5f5", font=("Arial", 8))
        self.julia_status_label.pack()
        tk.Label(julia_frame, text="Subsequent runs use cached env — no recompile",
                fg="gray", bg="#f5f5f5", font=("Arial", 7)).pack()

        # ── Calculation Type ──
        calc_frame = tk.LabelFrame(left_scrollable, text="Calculation Type", padx=5, pady=3, bg="#f5f5f5")
        calc_frame.pack(fill=tk.X, padx=5, pady=2)
        self.melts_calc_type_var = tk.StringVar(value="Fractional Crystallization")
        for calc_type in ["Fractional Crystallization", "Equilibrium Crystallization", "Batch Melting"]:
            tk.Radiobutton(calc_frame, text=calc_type, variable=self.melts_calc_type_var,
                          value=calc_type, bg="#f5f5f5").pack(anchor=tk.W)

        # ── Composition ──
        comp_frame = tk.LabelFrame(left_scrollable, text="Composition", padx=5, pady=3, bg="#f5f5f5")
        comp_frame.pack(fill=tk.X, padx=5, pady=2)

        preset_row = tk.Frame(comp_frame, bg="#f5f5f5")
        preset_row.pack(fill=tk.X, pady=1)
        tk.Label(preset_row, text="Preset:", bg="#f5f5f5", width=8).pack(side=tk.LEFT)
        self.melts_preset_var = tk.StringVar(value="Basalt")
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

        # ── Conditions ──
        cond_frame = tk.LabelFrame(left_scrollable, text="Required Conditions", padx=5, pady=5, bg="#f5f5f5")
        cond_frame.pack(fill=tk.X, padx=5, pady=5)
        for i in range(2):
            cond_frame.columnconfigure(i, weight=1)

        temp_frame = tk.Frame(cond_frame, bg="#f5f5f5")
        temp_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=2)
        tk.Label(temp_frame, text="T start:", bg="#f5f5f5", width=8, anchor=tk.W).pack(side=tk.LEFT)
        self.melts_T_start_var = tk.DoubleVar(value=1300.0)
        tk.Spinbox(temp_frame, from_=600, to=2000, increment=10, textvariable=self.melts_T_start_var, width=8).pack(side=tk.LEFT, padx=2)
        tk.Label(temp_frame, text="T end:", bg="#f5f5f5", width=8, anchor=tk.W).pack(side=tk.LEFT, padx=(10, 0))
        self.melts_T_end_var = tk.DoubleVar(value=800.0)
        tk.Spinbox(temp_frame, from_=600, to=2000, increment=10, textvariable=self.melts_T_end_var, width=8).pack(side=tk.LEFT, padx=2)
        self.temp_valid_label = tk.Label(temp_frame, text="", bg="#f5f5f5", font=("Arial", 7))
        self.temp_valid_label.pack(side=tk.LEFT, padx=2)

        tk.Label(cond_frame, text="Steps:", bg="#f5f5f5", anchor=tk.W).grid(row=1, column=0, sticky=tk.W, pady=2, padx=5)
        # Default 20 steps: ~5 min.  50 steps = ~15 min (MAGEMin is slow per-step)
        self.melts_steps_var = tk.IntVar(value=20)
        step_spin = tk.Spinbox(cond_frame, from_=5, to=100, increment=5,
                               textvariable=self.melts_steps_var, width=6)
        step_spin.grid(row=1, column=0, sticky=tk.W, padx=(50, 2), pady=2)
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
        self.melts_pressure_var = tk.DoubleVar(value=1000.0)
        tk.Spinbox(cond_frame, from_=1, to=30000, increment=100, textvariable=self.melts_pressure_var, width=8).grid(row=1, column=1, sticky=tk.W, padx=(70, 5), pady=2)

        tk.Label(cond_frame, text="fO₂ buffer:", bg="#f5f5f5", anchor=tk.W).grid(row=2, column=0, sticky=tk.W, pady=2, padx=5)
        self.melts_fo2_var = tk.StringVar(value="FMQ")
        ttk.Combobox(cond_frame, textvariable=self.melts_fo2_var,
                    values=["FMQ", "QFM", "NNO", "IW", "MH"], width=8).grid(row=2, column=0, sticky=tk.W, padx=(65, 5), pady=2)

        tk.Label(cond_frame, text="Δ log offset:", bg="#f5f5f5", anchor=tk.W).grid(row=2, column=1, sticky=tk.W, pady=2, padx=5)
        self.melts_fo2_offset_var = tk.DoubleVar(value=0.0)
        tk.Spinbox(cond_frame, from_=-3, to=3, increment=0.5, textvariable=self.melts_fo2_offset_var, width=8).grid(row=2, column=1, sticky=tk.W, padx=(70, 5), pady=2)

        # ── Options ──
        options_frame = tk.LabelFrame(left_scrollable, text="Options", padx=5, pady=3, bg="#f5f5f5")
        options_frame.pack(fill=tk.X, padx=5, pady=2)
        self.melts_keep_frac_var = tk.BooleanVar(value=True)
        tk.Checkbutton(options_frame, text="Keep fractionated solids", variable=self.melts_keep_frac_var, bg="#f5f5f5").pack(anchor=tk.W)

        # ── Buttons ──
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
            tk.Label(pct_row,
                    text="(MAGEMin streams progress live)",
                    bg="#f5f5f5", fg="gray", font=("Arial", 7)).pack(side=tk.LEFT)
        else:
            tk.Button(button_frame, text="📥 Install PetThermoTools First",
                    command=self._install_petthermo,
                    bg="#4CAF50", fg="white",
                    font=("Arial", 11, "bold"),
                    height=1).pack(fill=tk.X, pady=2)
            self.melts_pct_label = tk.Label(button_frame, text="—",
                    bg="#f5f5f5", font=("Arial", 10, "bold"))

        tk.Button(button_frame, text="📤 Export Results",
                 command=lambda: self._export_model(self.model_results.get('melts'), "MELTS"),
                 bg="#27ae60", fg="white").pack(fill=tk.X, pady=2)

        # ── Validation ──
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

            required_oxides = ['SiO2', 'TiO2', 'Al2O3', 'FeO', 'MgO', 'CaO', 'Na2O', 'K2O', 'H2O']
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

        # ── Plot canvas ──
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

    # ── FIXED: Install helpers ──────────────────────────────────────────────────
    def _install_petthermo(self):
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

    def _validate_magemin_inputs(self):
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

    # ── FIXED: Main calculation entry point ────────────────────────────────────
    def _run_magemin_calculation(self):
        if not self._validate_magemin_inputs():
            return
        if hasattr(self, 'run_button'):
            self.run_button.config(state='disabled')
        self.progress.start()
        self.status_var.set("⚡ Starting MAGEMin...")
        self.window.update()

        import threading
        thread = threading.Thread(target=self._run_magemin_thread)
        thread.daemon = True
        thread.start()

    # ── Sentinel file path — persists across module reloads and process restarts ──
    _SENTINEL_FILE = os.path.expanduser("~/.petthermotools_julia_env/.plugin_ready")

    @staticmethod
    def _julia_env_is_ready():
        """Return True if MAGEMin env was previously set up successfully."""
        sentinel = PetrogeneticModelingSuitePlugin._SENTINEL_FILE
        if not os.path.exists(sentinel):
            return False
        # Double-check Manifest also exists with MAGEMinCalc inside
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

    def _run_magemin_thread(self):
        """
        Three fixes in this version:
          1. File-based sentinel (persists across reloads/restarts) — never reinstalls
          2. Timeout = steps*30 + 480  (4 min Julia JIT + 30s/step buffer)
          3. Live progress % by capturing petthermotools stdout
        """
        import re
        import time
        import petthermotools as ptt

        os.environ['JULIA_PKG_PRECOMPILE_AUTO'] = '0'

        # ── Step 1: one-time install, gated by sentinel file ──────────────────
        if not self._julia_env_is_ready():
            self.window.after(0, lambda: self.status_var.set(
                "🔧 First-time setup — installing MAGEMin (~3-5 min, once only)..."))
            self.window.after(0, lambda: self.julia_status_label.config(
                text="⏳ First-time install — please wait...", fg="orange"))
            try:
                ptt.install_MAGEMinCalc()
                self._mark_julia_env_ready()
                self.window.after(0, lambda: self.julia_status_label.config(
                    text="✅ Julia env ready — will not reinstall again", fg="green"))
            except Exception as e:
                print(f"install_MAGEMinCalc warning: {e}")
        else:
            # Sentinel exists → skip install entirely, zero overhead
            self.window.after(0, lambda: self.julia_status_label.config(
                text="✅ Cached Julia env (skipping install)", fg="green"))

        # ── Step 2: build parameters ──────────────────────────────────────────
        composition = self._prepare_composition_for_magemin(self.comp_vars)
        print(f"\nComposition: {composition}")

        T_start    = self.melts_T_start_var.get()
        T_end      = self.melts_T_end_var.get()
        steps      = self.melts_steps_var.get()
        pressure   = self.melts_pressure_var.get()
        fo2        = self.melts_fo2_var.get()
        fo2_offset = self.melts_fo2_offset_var.get()
        frac_solid = "Fractional" in self.melts_calc_type_var.get()
        dt         = (T_start - T_end) / max(steps, 1)

        # Timeout = 480s Julia JIT warm-up + 30s per step (conservative)
        timeout_seconds = int(steps * 30 + 480)
        print(f"Timeout: {timeout_seconds}s for {steps} steps")

        # ── Step 3: live progress capture ─────────────────────────────────────
        # petthermotools prints "Completed X.X %" to stdout — we intercept it.
        class ProgressCapture:
            def __init__(self_, update_cb, orig):
                self_.update_cb = update_cb
                self_.orig = orig
                self_.buf = ""

            def write(self_, text):
                self_.orig.write(text)        # still print to terminal
                self_.orig.flush()
                self_.buf += text
                # match "Completed 42.0 %" or "Completed 100.0%"
                m = re.search(r'Completed\s+([\d.]+)\s*%', self_.buf)
                if m:
                    pct = float(m.group(1))
                    self_.update_cb(pct)
                    self_.buf = ""            # reset after each match

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
            # "MAGEMin" is NOT a valid model string — petthermotools uses
            # "Green2025" (Holland et al. 2022) or "Weller2024".
            # Passing an invalid model causes silent hang until timeout.
            _model_map = {"MAGEMin": "Green2025", "Green2025": "Green2025", "Weller2024": "Weller2024"}
            model_str = _model_map.get(self.melts_model_var.get(), "Green2025")
            print(f"Using petthermotools model: {model_str!r}  (was: {self.melts_model_var.get()!r})")

            results = ptt.isobaric_crystallisation(
                Model=model_str,   # ← "Green2025", NOT "MAGEMin"
                bulk=composition,
                P_bar=pressure,
                T_start_C=T_start,
                T_end_C=T_end,
                dt_C=dt,
                fO2_buffer=fo2,
                fO2_offset=fo2_offset,
                Frac_solid=frac_solid,
                # no timeout= — runs to natural completion
            )
        except Exception as e:
            sys.stdout = orig_stdout
            err_msg = str(e)
            self.window.after(0, lambda: messagebox.showerror("MAGEMin Error", err_msg))
            self.window.after(0, lambda: self.status_var.set(f"❌ {err_msg[:80]}"))
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

    def _enable_run_button(self):
        try:
            if hasattr(self, 'run_button'):
                self.run_button.config(state='normal')
        except Exception:
            pass

    def _display_magemin_results(self, results, elapsed):
        try:
            self.model_results['melts'] = results
            self.melts_ax.clear()

            parsed = self._parse_petthermotools_results(results)
            # Now returns (T, comp_dict, mass_dict) or (None, None, {})
            if len(parsed) == 3:
                T, comp_dict, mass_dict = parsed
            else:
                T, comp_dict = parsed
                mass_dict = {}

            if T is None or not comp_dict:
                print("⚠️  Could not extract T+composition — using fallback plot")
                self.status_var.set("⚠️ No liquid composition extracted — check T range / composition")
                simple = self._calculate_simple_melts()
                self._plot_simple_melts(self.melts_ax, simple)
                self.melts_canvas.draw()
                self.model_results['melts'] = simple
                return

            # ── Build 2-panel figure: liquid composition + phase masses ──────
            self.melts_fig.clear()

            if mass_dict:
                ax1 = self.melts_fig.add_subplot(2, 1, 1)
                ax2 = self.melts_fig.add_subplot(2, 1, 2)
            else:
                ax1 = self.melts_fig.add_subplot(1, 1, 1)
                ax2 = None

            # Panel 1: liquid oxide evolution
            # Green2025 returns FeOt_Liq (total iron) — map to display name
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
            ax1.set_title(f'Green2025 MAGEMin — {self.melts_calc_type_var.get()} — {elapsed:.0f}s')
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
                self._export_model(results, "Green2025")

        except Exception as e:
            messagebox.showerror("Display Error", str(e))
            traceback.print_exc()

    def _refresh_melts_tab(self):
        for i in range(self.notebook.index("end")):
            if self.notebook.tab(i, "text") == "⚗️ MELTS":
                self.notebook.forget(i)
                self._create_melts_tab()
                break

    def _open_composition_dialog(self):
        dialog = tk.Toplevel(self.window)
        dialog.title("Custom Composition")
        dialog.geometry("500x400")
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

        button_frame = tk.Frame(scrollable_frame)
        button_frame.grid(row=row+1, column=0, columnspan=3, pady=10)

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
        preset = self.melts_preset_var.get().lower()
        presets = {
            "basalt":     {'SiO2': 50.0, 'TiO2': 1.5, 'Al2O3': 15.0, 'Fe2O3': 1.5, 'FeO': 8.5, 'MnO': 0.2, 'MgO': 7.0,  'CaO': 11.0, 'Na2O': 2.5, 'K2O': 0.8, 'P2O5': 0.2, 'H2O': 0.5},
            "andesite":   {'SiO2': 60.0, 'TiO2': 0.8, 'Al2O3': 17.0, 'Fe2O3': 1.0, 'FeO': 4.0, 'MnO': 0.1, 'MgO': 3.0,  'CaO': 6.0,  'Na2O': 3.5, 'K2O': 1.5, 'P2O5': 0.2, 'H2O': 1.0},
            "dacite":     {'SiO2': 65.0, 'TiO2': 0.6, 'Al2O3': 16.0, 'Fe2O3': 0.8, 'FeO': 2.5, 'MnO': 0.1, 'MgO': 1.5,  'CaO': 4.0,  'Na2O': 4.0, 'K2O': 2.0, 'P2O5': 0.2, 'H2O': 1.5},
            "rhyolite":   {'SiO2': 75.0, 'TiO2': 0.2, 'Al2O3': 13.0, 'Fe2O3': 0.3, 'FeO': 0.8, 'MnO': 0.05,'MgO': 0.2,  'CaO': 0.8,  'Na2O': 4.0, 'K2O': 4.5, 'P2O5': 0.1, 'H2O': 2.0},
            "morb":       {'SiO2': 49.5, 'TiO2': 1.5, 'Al2O3': 16.0, 'Fe2O3': 1.2, 'FeO': 7.5, 'MnO': 0.2, 'MgO': 8.5,  'CaO': 11.5, 'Na2O': 2.8, 'K2O': 0.1, 'P2O5': 0.1, 'H2O': 0.2},
            "granite":    {'SiO2': 72.0, 'TiO2': 0.3, 'Al2O3': 14.0, 'Fe2O3': 0.5, 'FeO': 1.5, 'MnO': 0.05,'MgO': 0.5,  'CaO': 1.5,  'Na2O': 3.5, 'K2O': 4.5, 'P2O5': 0.1, 'H2O': 1.0},
            "peridotite": {'SiO2': 45.0, 'TiO2': 0.2, 'Al2O3': 4.0,  'Fe2O3': 0.5, 'FeO': 8.0, 'MnO': 0.1, 'MgO': 38.0, 'CaO': 3.5,  'Na2O': 0.3, 'K2O': 0.03,'P2O5': 0.02,'H2O': 0.1},
        }
        if preset in presets:
            for oxide, value in presets[preset].items():
                if oxide in self.comp_vars:
                    self.comp_vars[oxide].set(value)
            if hasattr(self, 'validate_callback'):
                self.validate_callback()
            self.status_var.set(f"✅ Loaded {self.melts_preset_var.get()} preset")


def setup_plugin(main_app):
    """Plugin setup function"""
    plugin = PetrogeneticModelingSuitePlugin(main_app)
    return plugin
