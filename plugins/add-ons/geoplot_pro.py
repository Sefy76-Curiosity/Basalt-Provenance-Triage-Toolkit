"""
GeoPlot Pro v2.0 - Complete Geochemical Graphics Suite
IUGS-IMA Standards + Mineral Plots + Thermobarometry + AFC Modeling

Author: Sefy Levy & DeepSeek
Category: add-ons (provides PLOT_TYPES)
Version: 2.0 (February 17, 2026) - ENHANCED PLOTTER EDITION
"""

PLUGIN_INFO = {
    'id': 'geoplot_pro',
    'name': 'GeoPlot Pro',
    'category': 'add-ons',
    'icon': '🪨',
    'version': '2.0',
    'requires': ['matplotlib', 'scipy', 'pillow', 'pandas', 'openpyxl',
                 'mplcursors', 'scikit-learn', 'compositional'],
    'optional': ['pyrolite'],  # ← Only pyrolite remains optional
    'description': 'GeoPlot Pro: Specialized Geochemical Graphics - IUGS diagrams, mineral classification, AFC modeling, thermobarometry plots, and machine learning visualization'
}

import tkinter as tk
from tkinter import ttk, colorchooser, filedialog, messagebox, scrolledtext
import numpy as np
import pandas as pd
import json
import csv
from pathlib import Path
import datetime
import threading
import warnings
import matplotlib.font_manager as fm
from mpl_toolkits.mplot3d import Axes3D
warnings.filterwarnings('ignore')

# ============================================================================
# CORE IMPORTS (EXACTLY AS YOURS - PRESERVED)
# ============================================================================

HAS_MPL = False
HAS_SCIPY = False
HAS_PIL = False
HAS_MPLCURSORS = False
HAS_SKLEARN = False
HAS_PYROLITE = False
HAS_COMPOSITIONAL = False

try:
    import matplotlib
    matplotlib.use('TkAgg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    from matplotlib.backends.backend_pdf import PdfPages
    from matplotlib.gridspec import GridSpec
    from matplotlib.patches import Rectangle, Ellipse, Polygon
    from matplotlib.lines import Line2D
    from matplotlib.figure import Figure
    import matplotlib.patches as mpatches
    import matplotlib.text as mtext
    HAS_MPL = True

    try:
        import mplcursors
        HAS_MPLCURSORS = True
    except ImportError:
        pass

    try:
        from scipy import stats
        from scipy.optimize import curve_fit, minimize
        from scipy.signal import find_peaks, savgol_filter
        from scipy.interpolate import interp1d
        HAS_SCIPY = True
    except ImportError:
        pass

    try:
        from PIL import Image, ImageDraw, ImageTk
        HAS_PIL = True
    except ImportError:
        pass

    try:
        import sklearn
        HAS_SKLEARN = True
    except ImportError:
        pass

    try:
        import pyrolite.plot
        from pyrolite.geochem import REE, norm, get_REE
        from pyrolite.util.synthetic import normal_scores
        HAS_PYROLITE = True
    except ImportError:
        pass

    try:
        import compositional
        HAS_COMPOSITIONAL = True
    except ImportError:
        pass

except ImportError:
    HAS_MPL = False

# ============================================================================
# CONSTANTS (PRESERVED + NEW)
# ============================================================================

REE_ORDER = ["La", "Ce", "Pr", "Nd", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu"]

JOURNAL_SIZES = {
    "None": (8, 6),
    "Nature (1-col)": (3.5, 2.8),
    "Nature (2-col)": (7.2, 5.8),
    "Science": (3.5, 3.0),
    "Elsevier": (6.5, 5.0),
    "AGU": (7.0, 5.5),
    "PNAS": (3.5, 3.5),
    "Geology": (7.0, 5.0),
    # NEW: Additional journal formats
    "GSA Bulletin": (7.0, 5.0),
    "Chemical Geology": (6.5, 5.0),
    "Lithos": (6.5, 5.0),
    "J Petrology": (6.5, 5.5),
    "EPSL": (7.0, 5.0)
}

# ============ IUGS-IMA NORMALIZATION VALUES (PRESERVED) ============
REE_NORMALIZATION = {
    "Chondrite (Sun & McDonough 1989)": {
        "La": 0.237, "Ce": 0.612, "Pr": 0.095, "Nd": 0.467, "Sm": 0.153,
        "Eu": 0.058, "Gd": 0.205, "Tb": 0.037, "Dy": 0.254, "Ho": 0.056,
        "Er": 0.165, "Tm": 0.025, "Yb": 0.170, "Lu": 0.025
    },
    "Chondrite (Boynton 1984)": {
        "La": 0.310, "Ce": 0.808, "Pr": 0.122, "Nd": 0.600, "Sm": 0.195,
        "Eu": 0.0735, "Gd": 0.259, "Tb": 0.0474, "Dy": 0.322, "Ho": 0.0718,
        "Er": 0.210, "Tm": 0.0326, "Yb": 0.209, "Lu": 0.0322
    },
    "Chondrite (McDonough & Sun 1995)": {
        "La": 0.237, "Ce": 0.613, "Pr": 0.0928, "Nd": 0.457, "Sm": 0.148,
        "Eu": 0.0563, "Gd": 0.199, "Tb": 0.0361, "Dy": 0.246, "Ho": 0.0546,
        "Er": 0.160, "Tm": 0.0247, "Yb": 0.161, "Lu": 0.0246
    },
    "N-MORB (Sun & McDonough 1989)": {
        "La": 2.5, "Ce": 7.5, "Pr": 1.1, "Nd": 7.3, "Sm": 2.6,
        "Eu": 0.95, "Gd": 3.4, "Tb": 0.64, "Dy": 4.2, "Ho": 0.64,
        "Er": 2.3, "Tm": 0.42, "Yb": 2.1, "Lu": 0.42
    },
    "Primitive Mantle (McDonough & Sun 1995)": {
        "La": 0.648, "Ce": 1.675, "Pr": 0.254, "Nd": 1.25, "Sm": 0.406,
        "Eu": 0.154, "Gd": 0.544, "Tb": 0.099, "Dy": 0.674, "Ho": 0.149,
        "Er": 0.438, "Tm": 0.068, "Yb": 0.441, "Lu": 0.0675
    }
}

# ============ NEW: Scientific Color Maps ============
# Crameri's scientific colormaps (colorblind-friendly)
SCIENTIFIC_CMAPS = {
    "Viridis (Sequential)": "viridis",
    "Plasma (Sequential)": "plasma",
    "Inferno (Sequential)": "inferno",
    "Magma (Sequential)": "magma",
    "Cividis (Sequential)": "cividis",
    "Turbo (Rainbow)": "turbo",
    "Coolwarm (Diverging)": "coolwarm",
    "RdBu (Diverging)": "RdBu",
    "Spectral (Diverging)": "Spectral",
    "Set1 (Qualitative)": "Set1",
    "Set2 (Qualitative)": "Set2",
    "Set3 (Qualitative)": "Set3",
    "Tab10 (Qualitative)": "tab10",
    "Tab20 (Qualitative)": "tab20"
}

# ============ NEW: Mineral End-Members ============
FELDSPAR_ENDMEMBERS = {
    "Anorthite (An)": {"CaAl2Si2O8": 1.0},
    "Albite (Ab)": {"NaAlSi3O8": 1.0},
    "Orthoclase (Or)": {"KAlSi3O8": 1.0}
}

PYROXENE_ENDMEMBERS = {
    "Enstatite (En)": {"Mg2Si2O6": 1.0},
    "Ferrosilite (Fs)": {"Fe2Si2O6": 1.0},
    "Wollastonite (Wo)": {"Ca2Si2O6": 1.0},
    "Diopside": {"CaMgSi2O6": 1.0},
    "Hedenbergite": {"CaFeSi2O6": 1.0},
    "Augite": {"(Ca,Na)(Mg,Fe,Al)(Si,Al)2O6": 1.0}
}

AMPHIBOLE_ENDMEMBERS = {
    "Tremolite": {"Ca2Mg5Si8O22(OH)2": 1.0},
    "Actinolite": {"Ca2(Mg,Fe)5Si8O22(OH)2": 1.0},
    "Hornblende": {"(Ca,Na)2-3(Mg,Fe,Al)5Si6(Al,Si)2O22(OH)2": 1.0},
    "Glaucophane": {"Na2Mg3Al2Si8O22(OH)2": 1.0},
    "Riebeckite": {"Na2Fe2+3Fe3+2Si8O22(OH)2": 1.0}
}

# ============ NEW: AFC Model Parameters ============
AFC_DEFAULTS = {
    "r_ratio": 0.3,  # assimilation/crystallization ratio
    "bulk_D": 0.5,   # bulk distribution coefficient
    "F": 0.5,        # fraction of melt remaining
    "Ca": 100,       # concentration in assimilant
    "Co": 50         # initial concentration
}

# ============ NEW: Discrimination Diagram Fields ============

# Th/Yb vs Ta/Yb (Pearce, 1983)
TH_YB_TA_YB_FIELDS = {
    "MORB": {"Th_Yb": [0.01, 0.1], "Ta_Yb": [0.01, 0.1], "color": "#87CEEB"},
    "VAB": {"Th_Yb": [0.1, 1.0], "Ta_Yb": [0.01, 0.1], "color": "#F4A460"},
    "WPB": {"Th_Yb": [0.1, 10], "Ta_Yb": [0.1, 10], "color": "#FFB6C1"},
    "SHO": {"Th_Yb": [1.0, 10], "Ta_Yb": [0.1, 1.0], "color": "#98FB98"}
}

# La/Yb vs Th/Yb for crustal contamination
LA_YB_TH_YB_FIELDS = {
    "Mantle Array": {"La_Yb": [0.5, 2], "Th_Yb": [0.1, 0.5], "color": "#87CEEB"},
    "Lower Crust": {"La_Yb": [2, 5], "Th_Yb": [0.5, 2], "color": "#F4A460"},
    "Upper Crust": {"La_Yb": [5, 20], "Th_Yb": [2, 10], "color": "#B22222"}
}

# S'CK Diagram for granitoids (SiO₂'–CaO/(CaO + K₂O))
SCK_FIELDS = {
    "I-type": {"SiO2_prime": [50, 77], "CaO_CaO_K2O": [0.4, 1.0], "color": "#87CEEB"},
    "S-type": {"SiO2_prime": [50, 77], "CaO_CaO_K2O": [0.1, 0.4], "color": "#F4A460"},
    "A-type": {"SiO2_prime": [50, 77], "CaO_CaO_K2O": [0.0, 0.1], "color": "#FFB6C1"}
}

# Additional trace element normalization for N-MORB (PRESERVED)
NMORB_NORM = {
    "Rb": 0.56, "Ba": 6.3, "Th": 0.085, "U": 0.032,
    "Nb": 2.33, "Ta": 0.132, "La": 2.5, "Ce": 7.5,
    "Pb": 0.3, "Pr": 0.95, "Sr": 90, "Nd": 7.3,
    "Sm": 2.63, "Zr": 74, "Hf": 2.05, "Eu": 1.02,
    "Gd": 3.68, "Tb": 0.67, "Dy": 4.55, "Y": 22,
    "Er": 3.0, "Tm": 0.48, "Yb": 3.05, "Lu": 0.46,
    "Sc": 32, "V": 240, "Cr": 285, "Co": 49, "Ni": 105
}

# ============ IUGS TAS FIELDS (PRESERVED) ============
TAS_FIELDS = {
    # Basic volcanic rocks
    "Basalt": {"SiO2": [45, 52], "alkali": [0, 5], "color": "#6497b1", "type": "volcanic"},
    "Basaltic Andesite": {"SiO2": [52, 57], "alkali": [0, 5.9], "color": "#005b96", "type": "volcanic"},
    "Andesite": {"SiO2": [57, 63], "alkali": [0, 5.9], "color": "#03396c", "type": "volcanic"},
    "Dacite": {"SiO2": [63, 69], "alkali": [0, 7.3], "color": "#011f4b", "type": "volcanic"},
    "Rhyolite": {"SiO2": [69, 80], "alkali": [0, 12], "color": "#b22222", "type": "volcanic"},

    # Alkaline volcanic
    "Trachybasalt": {"SiO2": [45, 52], "alkali": [5, 9.4], "color": "#b88b4a", "type": "volcanic"},
    "Trachyandesite": {"SiO2": [52, 57], "alkali": [5.9, 9.4], "color": "#d2b48c", "type": "volcanic"},
    "Trachyte": {"SiO2": [57, 69], "alkali": [9.4, 14], "color": "#4b2e83", "type": "volcanic"},
    "Phonolite": {"SiO2": [45, 57], "alkali": [9.4, 17], "color": "#b88b4a", "type": "volcanic"},

    # Plutonic equivalents
    "Gabbro": {"SiO2": [45, 52], "alkali": [0, 5], "color": "#6497b1", "type": "plutonic"},
    "Diorite": {"SiO2": [52, 63], "alkali": [0, 5.9], "color": "#03396c", "type": "plutonic"},
    "Granodiorite": {"SiO2": [63, 69], "alkali": [0, 7.3], "color": "#011f4b", "type": "plutonic"},
    "Granite": {"SiO2": [69, 80], "alkali": [0, 12], "color": "#b22222", "type": "plutonic"},
    "Syenite": {"SiO2": [52, 69], "alkali": [9.4, 14], "color": "#4b2e83", "type": "plutonic"}
}

# AFM boundary points (PRESERVED)
AFM_BOUNDARY = [(18, 0), (22, 5), (30, 15), (40, 30), (55, 55), (70, 80), (85, 100)]

# Multi-element spider order (PRESERVED)
MULTI_ELEMENTS = ['Rb', 'Ba', 'Th', 'U', 'Nb', 'Ta', 'La', 'Ce', 'Sr', 'Nd',
                  'Sm', 'Zr', 'Hf', 'Eu', 'Gd', 'Dy', 'Y', 'Er', 'Yb', 'Lu']

# Meschede Zr/Y-Nb/Y fields (PRESERVED)
MESCHEDE_FIELDS = {
    "WPA": {"Zr_Y": [0, 10], "Nb_Y": [0.6, 2.0], "color": "#FFB6C1", "name": "Within-Plate Alkaline"},
    "WPT": {"Zr_Y": [2, 10], "Nb_Y": [0.1, 0.6], "color": "#87CEEB", "name": "Within-Plate Tholeiitic"},
    "VAB": {"Zr_Y": [0, 4], "Nb_Y": [0, 0.4], "color": "#F4A460", "name": "Volcanic Arc Basalt"},
    "N-MORB": {"Zr_Y": [0, 4], "Nb_Y": [0, 0.1], "color": "#B0C4DE", "name": "N-MORB"},
    "E-MORB": {"Zr_Y": [4, 10], "Nb_Y": [0, 0.1], "color": "#98FB98", "name": "E-MORB"}
}

# Shervais V-Ti diagram (PRESERVED)
SHERVAIS_FIELDS = {
    "MORB": {"V": [200, 500], "Ti": [8000, 20000], "Ti_V": [20, 50], "color": "#87CEEB"},
    "IAT": {"V": [250, 450], "Ti": [3000, 8000], "Ti_V": [10, 20], "color": "#F4A460"},
    "BAB": {"V": [250, 400], "Ti": [2000, 6000], "Ti_V": [8, 15], "color": "#98FB98"},
    "OIB": {"V": [150, 300], "Ti": [15000, 30000], "Ti_V": [50, 100], "color": "#FFB6C1"}
}

# ============================================================================
# GEOCHEMICAL DATA MANAGER (COMPLETELY PRESERVED - NO CHANGES)
# ============================================================================

class GeochemicalDataManager:
    """Central data manager for all geochemical calculations with Pyrolite"""
    # [EXACTLY AS YOUR ORIGINAL - 100% PRESERVED]
    # ... (keeping all your original code here)

    def __init__(self, app):
        self.app = app
        self._dirty = True
        self._cached_df = None
        self._calculation_lock = threading.Lock()

        self.df = pd.DataFrame()
        self.major_mappings = {}
        self.ree_mappings = {}
        self.trace_mappings = {}

        # IUGS complete major elements with molar masses
        self.IUGS_MAJOR = {
            "SiO2": {"required": True, "range": [0, 100], "molar_mass": 60.08},
            "TiO2": {"required": False, "range": [0, 100], "molar_mass": 79.87},
            "Al2O3": {"required": True, "range": [0, 100], "molar_mass": 101.96},
            "Fe2O3": {"required": False, "range": [0, 100], "molar_mass": 159.69},
            "FeO": {"required": False, "range": [0, 100], "molar_mass": 71.84},
            "FeO_total": {"required": True, "range": [0, 100], "molar_mass": 71.84},
            "MnO": {"required": False, "range": [0, 100], "molar_mass": 70.94},
            "MgO": {"required": True, "range": [0, 100], "molar_mass": 40.30},
            "CaO": {"required": True, "range": [0, 100], "molar_mass": 56.08},
            "Na2O": {"required": True, "range": [0, 100], "molar_mass": 61.98},
            "K2O": {"required": True, "range": [0, 100], "molar_mass": 94.20},
            "P2O5": {"required": False, "range": [0, 100], "molar_mass": 141.94}
        }

        # Default correction settings
        self.loi_correction = "None"
        self.anhydrous = True
        self.fe_ratio = "FeO + 0.9*Fe2O3"
        self.blank = 0.0

    def mark_dirty(self):
        self._dirty = True

    def refresh_from_main(self):
        if hasattr(self.app, 'get_current_samples'):
            samples = self.app.get_current_samples()
        elif hasattr(self.app, 'data_manager') and hasattr(self.app.data_manager, 'get_current_data'):
            samples = self.app.data_manager.get_current_data()
        elif hasattr(self.app, 'samples'):
            samples = self.app.samples
        else:
            return False

        if samples:
            self.df = pd.DataFrame(samples)
            for col in self.df.columns:
                try:
                    self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
                except:
                    pass
            self.mark_dirty()
            return True
        return False

    def get_column_list(self):
        if self.df.empty:
            return []
        exclude = ['Sample_ID', 'Notes', 'Location', 'Date', 'Description']
        return [col for col in self.df.columns if col not in exclude]

    def calculate_all_indices(self, force=False):
        if not force and not self._dirty and self._cached_df is not None:
            return self._cached_df

        with self._calculation_lock:
            if not force and not self._dirty and self._cached_df is not None:
                return self._cached_df

            df = self._perform_calculations()
            self._cached_df = df
            self._dirty = False
            return df

    def _perform_calculations(self):
        if self.df.empty:
            return self.df

        df = self.df.copy()

        # Extract major elements using mappings
        major_data = {}
        for element in self.IUGS_MAJOR.keys():
            if element in self.major_mappings:
                col = self.major_mappings[element].get().strip()
                if col and col in df.columns:
                    major_data[element] = df[col].fillna(0)
                else:
                    major_data[element] = pd.Series(0, index=df.index)
            else:
                major_data[element] = pd.Series(0, index=df.index)

        # Calculate FeO_total if not directly mapped
        if 'FeO_total' not in [k for k, v in self.major_mappings.items() if v.get()]:
            feo = major_data.get('FeO', pd.Series(0, index=df.index))
            fe2o3 = major_data.get('Fe2O3', pd.Series(0, index=df.index))
            major_data['FeO_total'] = feo + fe2o3 * 0.8998

        # Apply LOI correction
        if self.loi_correction != "None" and 'LOI' in major_data:
            if "LOI-free" in self.loi_correction:
                total = sum(major_data.values()) - major_data['LOI']
                total = total.replace(0, np.nan)
                for element in major_data:
                    if element != 'LOI':
                        major_data[element] = (major_data[element] / total * 100).fillna(0)
                major_data['LOI'] = pd.Series(0, index=major_data['LOI'].index)
            elif "Subtract" in self.loi_correction:
                total = sum(major_data.values())
                total = total.replace(0, np.nan)
                for element in major_data:
                    major_data[element] = (major_data[element] / total * 100).fillna(0)

        # Apply anhydrous normalization
        if self.anhydrous:
            elements_to_sum = [v for k, v in major_data.items() if k != 'LOI']
            total = sum(elements_to_sum)
            total = total.replace(0, np.nan)
            for element in major_data:
                if element != 'LOI':
                    major_data[element] = (major_data[element] / total * 100).fillna(0)
            if 'LOI' in major_data:
                major_data['LOI'] = pd.Series(0, index=major_data['LOI'].index)

        # Calculate FeO* for AFM
        if "FeO + 0.9*Fe2O3" in self.fe_ratio:
            major_data["FeO_star"] = major_data["FeO"] + 0.9 * major_data["Fe2O3"]
        elif "Fe2O3*0.8998" in self.fe_ratio:
            major_data["FeO_star"] = major_data["Fe2O3"] * 0.8998
        else:
            major_data["FeO_star"] = major_data["FeO"] + major_data["Fe2O3"] * 0.8998

        # Add to dataframe
        for element, series in major_data.items():
            df[f"{element}_wt"] = series

        # Calculate Alkali
        df['Alkali'] = major_data["Na2O"] + major_data["K2O"]

        # ASI (Aluminum Saturation Index)
        al_molar = major_data["Al2O3"] / 101.96
        ca_molar = major_data["CaO"] / 56.08
        na_molar = major_data["Na2O"] / 61.98
        k_molar = major_data["K2O"] / 94.20
        denominator = (ca_molar + na_molar + k_molar).replace(0, np.nan)
        df['ASI'] = al_molar / denominator
        df['ASI'] = df['ASI'].replace([np.inf, -np.inf], np.nan).fillna(0)

        # ASI Classification
        conditions = [
            df['ASI'] > 1.0,
            df['ASI'] < 1.0
        ]
        choices = ['Peraluminous', 'Metaluminous']
        df['ASI_Class'] = np.select(conditions, choices, default='Peralkaline')

        # Mg#
        mg_molar = major_data["MgO"] / 40.30
        fe_molar = major_data["FeO_star"] / 71.84
        denominator = (mg_molar + fe_molar).replace(0, np.nan)
        df['Mg#'] = (mg_molar / denominator * 100).fillna(0)
        df['Mg#_Class'] = np.where(df['Mg#'] > 65, 'Primitive', 'Differentiated')

        # MALI (Modified Alkali-Lime Index)
        df['MALI'] = major_data["Na2O"] + major_data["K2O"] - major_data["CaO"]

        # REE data with blank correction
        for ree in REE_ORDER + ['Y']:
            if ree in self.ree_mappings:
                col = self.ree_mappings[ree].get().strip()
                if col and col in df.columns:
                    values = df[col].fillna(0).values - self.blank
                    values[values < 0] = 0
                    df[f"{ree}_ppm"] = values

        # Chondrite normalization using pyrolite if available
        if HAS_PYROLITE:
            try:
                ree_cols = [f"{r}_ppm" for r in REE_ORDER if f"{r}_ppm" in df.columns]
                if len(ree_cols) > 5:
                    ree_df = df[ree_cols].copy()
                    ree_df.columns = [c.replace('_ppm', '') for c in ree_cols]
                    norm_ree = pyrolite.geochem.norm(ree_df, to='chondrite')
                    for r in REE_ORDER:
                        if r in norm_ree.columns:
                            df[f"{r}_N"] = norm_ree[r]
            except:
                norm_dict = REE_NORMALIZATION.get("Chondrite (Sun & McDonough 1989)", {})
                for ree in REE_ORDER + ['Y']:
                    if ree in norm_dict and f"{ree}_ppm" in df.columns:
                        with np.errstate(divide='ignore', invalid='ignore'):
                            df[f"{ree}_N"] = df[f"{ree}_ppm"] / norm_dict[ree]
                            df[f"{ree}_N"] = df[f"{ree}_N"].replace([np.inf, -np.inf], np.nan).fillna(0)
        else:
            norm_dict = REE_NORMALIZATION.get("Chondrite (Sun & McDonough 1989)", {})
            for ree in REE_ORDER + ['Y']:
                if ree in norm_dict and f"{ree}_ppm" in df.columns:
                    with np.errstate(divide='ignore', invalid='ignore'):
                        df[f"{ree}_N"] = df[f"{ree}_ppm"] / norm_dict[ree]
                        df[f"{ree}_N"] = df[f"{ree}_N"].replace([np.inf, -np.inf], np.nan).fillna(0)

        # Eu anomaly
        if all(e in df.columns for e in ['Eu_N', 'Sm_N', 'Gd_N']):
            with np.errstate(divide='ignore', invalid='ignore'):
                df['Eu_Eu*'] = df['Eu_N'] / np.sqrt(df['Sm_N'] * df['Gd_N'])
                df['Eu_Eu*'] = df['Eu_Eu*'].replace([np.inf, -np.inf], np.nan).fillna(0)

            conditions = [
                df['Eu_Eu*'] < 0.85,
                df['Eu_Eu*'] > 1.15
            ]
            choices = ['Negative', 'Positive']
            df['Eu_Anomaly'] = np.select(conditions, choices, default='None')

        # Ce anomaly
        if all(e in df.columns for e in ['Ce_N', 'La_N', 'Pr_N']):
            with np.errstate(divide='ignore', invalid='ignore'):
                df['Ce_Ce*'] = df['Ce_N'] / np.sqrt(df['La_N'] * df['Pr_N'])
                df['Ce_Ce*'] = df['Ce_Ce*'].replace([np.inf, -np.inf], np.nan).fillna(0)

        # La/Yb ratio
        if all(e in df.columns for e in ['La_N', 'Yb_N']):
            with np.errstate(divide='ignore', invalid='ignore'):
                df['LaN_YbN'] = df['La_N'] / df['Yb_N'].replace(0, np.nan)
                df['LaN_YbN'] = df['LaN_YbN'].replace([np.inf, -np.inf], np.nan).fillna(0)

        # Trace elements with blank correction
        for trace in MULTI_ELEMENTS:
            if trace in self.trace_mappings:
                col = self.trace_mappings[trace].get().strip()
                if col and col in df.columns:
                    values = df[col].fillna(0).values - self.blank
                    values[values < 0] = 0
                    df[f"{trace}_ppm"] = values

        # N-MORB normalization
        for trace in MULTI_ELEMENTS:
            if trace in NMORB_NORM and f"{trace}_ppm" in df.columns:
                with np.errstate(divide='ignore', invalid='ignore'):
                    df[f"{trace}_N-MORB"] = df[f"{trace}_ppm"] / NMORB_NORM[trace]
                    df[f"{trace}_N-MORB"] = df[f"{trace}_N-MORB"].replace([np.inf, -np.inf], np.nan).fillna(0)

        # Pearce Nb-Y diagram
        if 'Nb_ppm' in df.columns and 'Y_ppm' in df.columns:
            with np.errstate(divide='ignore', invalid='ignore'):
                df['Nb_Y'] = df['Nb_ppm'] / df['Y_ppm'].replace(0, np.nan)
                df['Nb_Y'] = df['Nb_Y'].replace([np.inf, -np.inf], np.nan).fillna(0)
            df['NbY_Tectonic'] = np.where(df['Nb_Y'] > 0.1, 'WPG', 'VAG+COLG+ORG')

        # Ta-Yb diagram
        if 'Ta_ppm' in df.columns and 'Yb_ppm' in df.columns:
            with np.errstate(divide='ignore', invalid='ignore'):
                df['Ta_Yb'] = df['Ta_ppm'] / df['Yb_ppm'].replace(0, np.nan)
                df['Ta_Yb'] = df['Ta_Yb'].replace([np.inf, -np.inf], np.nan).fillna(0)

        # Rb-Y+Nb diagram
        if all(e in df.columns for e in ['Rb_ppm', 'Y_ppm', 'Nb_ppm']):
            with np.errstate(divide='ignore', invalid='ignore'):
                y_nb = (df['Y_ppm'] + df['Nb_ppm']).replace(0, np.nan)
                df['Rb_Y+Nb'] = df['Rb_ppm'] / y_nb
                df['Rb_Y+Nb'] = df['Rb_Y+Nb'].replace([np.inf, -np.inf], np.nan).fillna(0)

        # Whalen A-type discrimination
        if all(e in df.columns for e in ['Zr_ppm', 'Nb_ppm', 'Ce_ppm', 'Y_ppm']):
            df['Zr+Nb+Ce+Y'] = sum(df[f"{e}_ppm"] for e in ['Zr', 'Nb', 'Ce', 'Y'] if f"{e}_ppm" in df.columns)
            if 'FeO_star_wt' in df.columns and 'MgO_wt' in df.columns:
                with np.errstate(divide='ignore', invalid='ignore'):
                    df['FeO_MgO'] = df['FeO_star_wt'] / df['MgO_wt'].replace(0, np.nan)
                    df['FeO_MgO'] = df['FeO_MgO'].replace([np.inf, -np.inf], np.nan).fillna(0)

                conditions = [
                    (df['Zr+Nb+Ce+Y'] > 350) & (df['FeO_MgO'] > 10),
                    (df['Zr+Nb+Ce+Y'] <= 350) | (df['FeO_MgO'] <= 10)
                ]
                df['Granite_Type'] = np.select(conditions, ['A-type', 'I-S-type'], default='Unknown')

        # Meschede Zr/Y vs Nb/Y
        if 'Zr_ppm' in df.columns and 'Y_ppm' in df.columns and 'Nb_ppm' in df.columns:
            with np.errstate(divide='ignore', invalid='ignore'):
                df['Zr_Y'] = df['Zr_ppm'] / df['Y_ppm'].replace(0, np.nan)
                df['Zr_Y'] = df['Zr_Y'].replace([np.inf, -np.inf], np.nan).fillna(0)
                df['Nb_Y_meschede'] = df['Nb_ppm'] / df['Y_ppm'].replace(0, np.nan)
                df['Nb_Y_meschede'] = df['Nb_Y_meschede'].replace([np.inf, -np.inf], np.nan).fillna(0)

        # Shervais V-Ti
        if 'V_ppm' in df.columns and 'Ti_ppm' in df.columns:
            with np.errstate(divide='ignore', invalid='ignore'):
                df['Ti_V'] = df['Ti_ppm'] / df['V_ppm'].replace(0, np.nan)
                df['Ti_V'] = df['Ti_V'].replace([np.inf, -np.inf], np.nan).fillna(0)

        # CIPW Norm Calculation
        df = self.calculate_cipw_norm(df, major_data)

        # Zircon Saturation Temperature
        if all(k in df.columns for k in ['SiO2_wt', 'Al2O3_wt', 'Na2O_wt', 'K2O_wt', 'CaO_wt', 'Zr_ppm']):
            df['T_zircon_C'] = df.apply(self.calculate_zircon_temperature, axis=1)

        df['Analysis_Date'] = datetime.now().strftime('%Y-%m-%d')
        return df

    def calculate_cipw_norm(self, df, major_data):
        if not HAS_PYROLITE:
            df['CIPW_Q'] = 0
            df['CIPW_Or'] = major_data['K2O'] * 5.0
            df['CIPW_Ab'] = major_data['Na2O'] * 8.0
            df['CIPW_An'] = major_data['CaO'] * 4.5
            df['CIPW_Di'] = 0
            df['CIPW_Hy'] = 0
            df['CIPW_Ol'] = 0
            df['CIPW_Mt'] = major_data['FeO_star'] * 2.0
            df['CIPW_Ilm'] = major_data['TiO2'] * 2.0
            df['CIPW_Ap'] = major_data['P2O5'] * 2.5
        else:
            try:
                pass
            except:
                pass
        return df

    def calculate_zircon_temperature(self, row):
        try:
            sio2 = row.get('SiO2_wt', 0)
            al2o3 = row.get('Al2O3_wt', 0)
            na2o = row.get('Na2O_wt', 0)
            k2o = row.get('K2O_wt', 0)
            cao = row.get('CaO_wt', 0)
            zr = row.get('Zr_ppm', 0)

            if min(sio2, al2o3, na2o, k2o, cao, zr) <= 0:
                return np.nan

            si = sio2 / 60.08
            al = (al2o3 / 101.96) * 2
            na = (na2o / 61.98) * 2
            k = (k2o / 94.20) * 2
            ca = cao / 56.08

            M = (na + k + 2*ca) / (al * si) if al * si > 0 else 0

            if M <= 0 or zr <= 0:
                return np.nan

            T = 12900 / (2.95 + 0.85*M + np.log(496000 / zr))
            return T - 273.15
        except:
            return np.nan

    def get_available_indices(self):
        if self.df.empty:
            return []
        return [col for col in self.df.columns if col not in self.get_column_list()]

# ============================================================================
# GEOCHEMICAL MAPPING DIALOG (COMPLETELY PRESERVED)
# ============================================================================

class GeochemicalMappingDialog(tk.Toplevel):
    """Unified mapping dialog for major, REE, and trace elements with live preview"""
    # [EXACTLY AS YOUR ORIGINAL - PRESERVED]
    # ... (keeping all your original code here)

    def __init__(self, parent, data_manager, callback):
        super().__init__(parent)
        self.title("Geochemical Column Mapping")
        self.geometry("1000x700")
        self.transient(parent)
        self.data_manager = data_manager
        self.callback = callback

        self.data_manager.refresh_from_main()
        self.columns = self.data_manager.get_column_list()
        self.preview_df = None

        self._create_ui()
        self._update_preview()

    def _create_ui(self):
        main = ttk.Frame(self, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        paned = ttk.PanedWindow(main, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        left_panel = ttk.Frame(paned)
        paned.add(left_panel, weight=1)

        notebook = ttk.Notebook(left_panel)
        notebook.pack(fill=tk.BOTH, expand=True)

        major_tab = ttk.Frame(notebook)
        notebook.add(major_tab, text="🪨 Major Elements")
        self._create_major_tab(major_tab)

        ree_tab = ttk.Frame(notebook)
        notebook.add(ree_tab, text="🧪 REE + Y")
        self._create_ree_tab(ree_tab)

        trace_tab = ttk.Frame(notebook)
        notebook.add(trace_tab, text="🔬 Trace Elements")
        self._create_trace_tab(trace_tab)

        corr_tab = ttk.Frame(notebook)
        notebook.add(corr_tab, text="⚙️ Corrections")
        self._create_corrections_tab(corr_tab)

        right_panel = ttk.Frame(paned)
        paned.add(right_panel, weight=1)

        self._create_preview_panel(right_panel)

        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(btn_frame, text="Auto-Detect All",
                  command=self.auto_detect_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Preview Calculations",
                  command=self._update_preview).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Apply Mapping",
                  command=self._apply).pack(side=tk.RIGHT, padx=2)
        ttk.Button(btn_frame, text="Cancel",
                  command=self.destroy).pack(side=tk.RIGHT, padx=2)

    def _create_preview_panel(self, parent):
        preview_notebook = ttk.Notebook(parent)
        preview_notebook.pack(fill=tk.BOTH, expand=True)

        counts_tab = ttk.Frame(preview_notebook)
        preview_notebook.add(counts_tab, text="📊 Sample Counts")

        self.counts_text = scrolledtext.ScrolledText(counts_tab, height=20, font=('Courier', 9))
        self.counts_text.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        data_tab = ttk.Frame(preview_notebook)
        preview_notebook.add(data_tab, text="👁️ Preview Data")

        columns = ("Element", "Mapped Column", "Samples", "Min", "Max", "Mean")
        self.preview_tree = ttk.Treeview(data_tab, columns=columns, show="headings", height=15)

        for col in columns:
            self.preview_tree.heading(col, text=col)
            self.preview_tree.column(col, width=80)

        vsb = ttk.Scrollbar(data_tab, orient=tk.VERTICAL, command=self.preview_tree.yview)
        self.preview_tree.configure(yscrollcommand=vsb.set)

        self.preview_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        indices_tab = ttk.Frame(preview_notebook)
        preview_notebook.add(indices_tab, text="📈 Calculated Indices")

        self.indices_text = scrolledtext.ScrolledText(indices_tab, height=20, font=('Courier', 9))
        self.indices_text.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

    def _create_major_tab(self, parent):
        frame = ttk.Frame(parent, padding=5)
        frame.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable = ttk.Frame(canvas)

        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Label(scrollable, text="REQUIRED ELEMENTS (IUGS):",
                 font=('Arial', 8, 'bold'), foreground='red').grid(row=0, column=0, columnspan=2, pady=5, sticky=tk.W)

        required = ["SiO2", "Al2O3", "MgO", "CaO", "Na2O", "K2O", "FeO_total"]
        for i, element in enumerate(required):
            self._create_mapping_row(scrollable, element, i+1, 0, required=True)

        ttk.Label(scrollable, text="\nOPTIONAL ELEMENTS:",
                 font=('Arial', 8, 'bold')).grid(row=len(required)+2, column=0, columnspan=2, pady=5, sticky=tk.W)

        optional = ["TiO2", "Fe2O3", "FeO", "MnO", "P2O5", "LOI"]
        for i, element in enumerate(optional):
            self._create_mapping_row(scrollable, element, i+len(required)+3, 0)

    def _create_ree_tab(self, parent):
        frame = ttk.Frame(parent, padding=5)
        frame.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable = ttk.Frame(canvas)

        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        ree_list = REE_ORDER + ["Y"]
        for i, element in enumerate(ree_list):
            self._create_mapping_row(scrollable, element, i, 0, is_ree=True)

    def _create_trace_tab(self, parent):
        frame = ttk.Frame(parent, padding=5)
        frame.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable = ttk.Frame(canvas)

        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        trace_list = MULTI_ELEMENTS
        for i, element in enumerate(trace_list):
            self._create_mapping_row(scrollable, element, i, 0, is_trace=True)

    def _create_corrections_tab(self, parent):
        frame = ttk.Frame(parent, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        loi_frame = ttk.LabelFrame(frame, text="LOI Correction", padding=5)
        loi_frame.pack(fill=tk.X, pady=5)

        self.loi_var = tk.StringVar(value=self.data_manager.loi_correction)
        ttk.Combobox(loi_frame, textvariable=self.loi_var,
                    values=["None", "LOI-free 100%", "Subtract LOI"],
                    width=20).pack(anchor=tk.W)

        self.anhydrous_var = tk.BooleanVar(value=self.data_manager.anhydrous)
        ttk.Checkbutton(loi_frame, text="Anhydrous 100% normalization",
                       variable=self.anhydrous_var).pack(anchor=tk.W, pady=2)

        fe_frame = ttk.LabelFrame(frame, text="Fe Speciation", padding=5)
        fe_frame.pack(fill=tk.X, pady=5)

        self.fe_var = tk.StringVar(value=self.data_manager.fe_ratio)
        ttk.Combobox(fe_frame, textvariable=self.fe_var,
                    values=["FeO + 0.9*Fe2O3", "Fe2O3*0.8998", "Total Fe as FeO"],
                    width=25).pack(anchor=tk.W)

        blank_frame = ttk.LabelFrame(frame, text="Blank Correction", padding=5)
        blank_frame.pack(fill=tk.X, pady=5)

        blank_row = ttk.Frame(blank_frame)
        blank_row.pack(anchor=tk.W)
        ttk.Label(blank_row, text="Blank value (ppm):").pack(side=tk.LEFT)
        self.blank_var = tk.DoubleVar(value=self.data_manager.blank)
        ttk.Spinbox(blank_row, from_=0, to=100, increment=0.01,
                   textvariable=self.blank_var, width=8).pack(side=tk.LEFT, padx=5)

        coda_frame = ttk.LabelFrame(frame, text="Compositional Data Analysis", padding=5)
        coda_frame.pack(fill=tk.X, pady=5)

        self.send_to_coda_btn = ttk.Button(coda_frame, text="📤 Send to Compositional Plugin",
                                          command=self.send_to_coda)
        self.send_to_coda_btn.pack(anchor=tk.W, pady=2)

        if not HAS_COMPOSITIONAL:
            self.send_to_coda_btn.config(state=tk.DISABLED)
            ttk.Label(coda_frame, text="(compositional plugin not installed)",
                     font=('Arial', 7, 'italic')).pack(anchor=tk.W)

    def _create_mapping_row(self, parent, element, row, col, required=False, is_ree=False, is_trace=False):
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=col, padx=2, pady=1, sticky=tk.W)

        if required:
            label_text = f"{element}*:"
            fg = "red"
        else:
            label_text = f"{element}:"
            fg = "black"

        ttk.Label(frame, text=label_text, font=('Arial', 8, 'bold' if required else 'normal'),
                 foreground=fg, width=8).pack(side=tk.LEFT)

        var = tk.StringVar()
        if is_ree:
            if element not in self.data_manager.ree_mappings:
                self.data_manager.ree_mappings[element] = var
            else:
                var = self.data_manager.ree_mappings[element]
        elif is_trace:
            if element not in self.data_manager.trace_mappings:
                self.data_manager.trace_mappings[element] = var
            else:
                var = self.data_manager.trace_mappings[element]
        else:
            if element not in self.data_manager.major_mappings:
                self.data_manager.major_mappings[element] = var
            else:
                var = self.data_manager.major_mappings[element]

        combo = ttk.Combobox(frame, textvariable=var, values=[""] + self.columns,
                             width=12, font=('Arial', 8))
        combo.pack(side=tk.LEFT, padx=2)
        combo.bind('<<ComboboxSelected>>', lambda e: self._update_preview())

        count_label = ttk.Label(frame, text="", font=('Arial', 7), foreground='gray')
        count_label.pack(side=tk.LEFT, padx=2)

        if not hasattr(self, '_count_labels'):
            self._count_labels = {}
        self._count_labels[element] = count_label

        return var

    def _update_preview(self):
        self.data_manager.loi_correction = self.loi_var.get()
        self.data_manager.anhydrous = self.anhydrous_var.get()
        self.data_manager.fe_ratio = self.fe_var.get()
        self.data_manager.blank = self.blank_var.get()

        preview_df = self.data_manager.calculate_all_indices(force=True)

        if hasattr(self, '_count_labels'):
            for element, label in self._count_labels.items():
                col = None
                if element in self.data_manager.major_mappings:
                    col = self.data_manager.major_mappings[element].get()
                elif element in self.data_manager.ree_mappings:
                    col = self.data_manager.ree_mappings[element].get()
                elif element in self.data_manager.trace_mappings:
                    col = self.data_manager.trace_mappings[element].get()

                if col and col in preview_df.columns:
                    count = preview_df[col].notna().sum()
                    label.config(text=f"({count})")
                else:
                    label.config(text="")

        self.counts_text.delete(1.0, tk.END)
        self.counts_text.insert(1.0, "SAMPLE COUNTS BY ELEMENT GROUP:\n\n")

        self.counts_text.insert(1.0, "MAJOR ELEMENTS:\n")
        for element in self.data_manager.major_mappings:
            col = self.data_manager.major_mappings[element].get()
            if col and col in preview_df.columns:
                count = preview_df[col].notna().sum()
                self.counts_text.insert(tk.END, f"  {element}: {col} → {count} samples\n")

        self.counts_text.insert(tk.END, "\nREE ELEMENTS:\n")
        for element in self.data_manager.ree_mappings:
            col = self.data_manager.ree_mappings[element].get()
            if col and col in preview_df.columns:
                count = preview_df[col].notna().sum()
                self.counts_text.insert(tk.END, f"  {element}: {col} → {count} samples\n")

        self.counts_text.insert(tk.END, "\nTRACE ELEMENTS:\n")
        for element in self.data_manager.trace_mappings:
            col = self.data_manager.trace_mappings[element].get()
            if col and col in preview_df.columns:
                count = preview_df[col].notna().sum()
                self.counts_text.insert(tk.END, f"  {element}: {col} → {count} samples\n")

        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)

        for element in list(self.data_manager.major_mappings.keys())[:5]:
            col = self.data_manager.major_mappings[element].get()
            if col and col in preview_df.columns:
                data = preview_df[col].dropna()
                if len(data) > 0:
                    self.preview_tree.insert("", tk.END, values=(
                        element, col[:10], len(data),
                        f"{data.min():.2f}", f"{data.max():.2f}", f"{data.mean():.2f}"
                    ))

        self.indices_text.delete(1.0, tk.END)
        self.indices_text.insert(1.0, "CALCULATED INDICES (first 5 samples):\n\n")

        indices = self.data_manager.get_available_indices()[:10]
        if indices:
            header = "Sample".ljust(15)
            for idx in indices:
                header += idx[:10].ljust(12)
            self.indices_text.insert(tk.END, header + "\n")
            self.indices_text.insert(tk.END, "-" * (15 + len(indices)*12) + "\n")

            for i, (idx, row) in enumerate(preview_df.head(5).iterrows()):
                line = str(row.get('Sample_ID', f'S{i}'))[:15].ljust(15)
                for col in indices:
                    val = row.get(col, '')
                    if isinstance(val, float):
                        line += f"{val:.2f}".ljust(12)
                    else:
                        line += str(val)[:10].ljust(12)
                self.indices_text.insert(tk.END, line + "\n")

    def auto_detect_all(self):
        major_keywords = {
            "SiO2": ["sio2", "si", "silica", "sio₂", "sio2_wt"],
            "TiO2": ["tio2", "ti", "titanium", "tio₂", "tio2_wt"],
            "Al2O3": ["al2o3", "al", "alumina", "al₂o₃", "al2o3_wt"],
            "Fe2O3": ["fe2o3", "fe₂o₃", "ferric", "fe2o3_wt"],
            "FeO": ["feo", "ferrous", "feo_wt"],
            "FeO_total": ["feo_total", "feot", "total_fe", "feo*"],
            "MnO": ["mno", "mn", "manganese", "mno_wt"],
            "MgO": ["mgo", "mg", "magnesium", "mgo_wt"],
            "CaO": ["cao", "ca", "calcium", "cao_wt"],
            "Na2O": ["na2o", "na", "sodium", "na₂o", "na2o_wt"],
            "K2O": ["k2o", "k", "potassium", "k₂o", "k2o_wt"],
            "P2O5": ["p2o5", "p", "phosphorus", "p₂o₅", "p2o5_wt"],
            "LOI": ["loi", "loss"]
        }

        for element, keywords in major_keywords.items():
            if element in self.data_manager.major_mappings:
                for col in self.columns:
                    col_lower = col.lower()
                    if any(kw in col_lower for kw in keywords):
                        self.data_manager.major_mappings[element].set(col)
                        break

        ree_variations = {
            "La": ["la", "lanthanum"],
            "Ce": ["ce", "cerium"],
            "Pr": ["pr", "praseodymium"],
            "Nd": ["nd", "neodymium"],
            "Sm": ["sm", "samarium"],
            "Eu": ["eu", "europium"],
            "Gd": ["gd", "gadolinium"],
            "Tb": ["tb", "terbium"],
            "Dy": ["dy", "dysprosium"],
            "Ho": ["ho", "holmium"],
            "Er": ["er", "erbium"],
            "Tm": ["tm", "thulium"],
            "Yb": ["yb", "ytterbium"],
            "Lu": ["lu", "lutetium"],
            "Y": ["y", "yttrium"]
        }

        for element, keywords in ree_variations.items():
            if element in self.data_manager.ree_mappings:
                for col in self.columns:
                    col_lower = col.lower()
                    if any(kw in col_lower for kw in keywords):
                        self.data_manager.ree_mappings[element].set(col)
                        break

        trace_keywords = {
            "Zr": ["zr", "zirconium"],
            "Nb": ["nb", "niobium"],
            "Y": ["y", "yttrium"],
            "Rb": ["rb", "rubidium"],
            "Ta": ["ta", "tantalum"],
            "Yb": ["yb", "ytterbium"],
            "Th": ["th", "thorium"],
            "U": ["u", "uranium"],
            "Sr": ["sr", "strontium"],
            "Ba": ["ba", "barium"],
            "Cr": ["cr", "chromium"],
            "Ni": ["ni", "nickel"],
            "V": ["v", "vanadium"],
            "Ti": ["ti", "titanium"]
        }

        for element, keywords in trace_keywords.items():
            if element in self.data_manager.trace_mappings:
                for col in self.columns:
                    col_lower = col.lower()
                    if any(kw in col_lower for kw in keywords):
                        self.data_manager.trace_mappings[element].set(col)
                        break

        self._update_preview()
        messagebox.showinfo("Auto-Detect", "Auto-detection complete. Review mappings in preview.")

    def send_to_coda(self):
        if not HAS_COMPOSITIONAL:
            messagebox.showerror("Error", "Compositional plugin not installed")
            return

        df = self.data_manager.calculate_all_indices()

        if df.empty:
            messagebox.showwarning("No Data", "No data to send")
            return

        dialog = tk.Toplevel(self)
        dialog.title("Send to Compositional Plugin")
        dialog.geometry("400x300")
        dialog.transient(self)

        ttk.Label(dialog, text="Select columns for CLR/ILR transformation:",
                 font=('Arial', 10, 'bold')).pack(pady=10)

        listbox = tk.Listbox(dialog, selectmode=tk.EXTENDED, height=10)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        for col in self.data_manager.get_column_list():
            listbox.insert(tk.END, col)

        scroll = ttk.Scrollbar(dialog, command=listbox.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        listbox.config(yscrollcommand=scroll.set)

        def send():
            selected = [listbox.get(i) for i in listbox.curselection()]
            if not selected:
                messagebox.showwarning("No Selection", "Select at least one column")
                return

            comp_df = df[selected].copy()

            if hasattr(self.data_manager.app, 'compositional_plugin'):
                self.data_manager.app.compositional_plugin.load_data(comp_df)
                messagebox.showinfo("Success", f"Sent {len(selected)} columns to Compositional plugin")
                dialog.destroy()
            else:
                filename = filedialog.asksaveasfilename(
                    defaultextension=".csv",
                    filetypes=[("CSV", "*.csv")],
                    initialfile="compositional_data.csv"
                )
                if filename:
                    comp_df.to_csv(filename, index=False)
                    messagebox.showinfo("Success", f"Data saved to {filename}")
                    dialog.destroy()

        ttk.Button(dialog, text="Send", command=send).pack(pady=10)

    def _apply(self):
        self.data_manager.loi_correction = self.loi_var.get()
        self.data_manager.anhydrous = self.anhydrous_var.get()
        self.data_manager.fe_ratio = self.fe_var.get()
        self.data_manager.blank = self.blank_var.get()

        self.data_manager.calculate_all_indices(force=True)

        self.callback(self.data_manager)
        self.destroy()

# ============================================================================
# TEMPLATE MANAGER (PRESERVED + ENHANCED WITH COLORBLIND PALETTES)
# ============================================================================

class TemplateManager:
    """Manages loading and applying templates from app's templates directory"""

    def __init__(self, app):
        self.app = app
        self.templates = {}

        if hasattr(app, 'base_dir'):
            base_dir = app.base_dir
        elif hasattr(app, 'config_dir'):
            base_dir = Path(app.config_dir).parent
        else:
            base_dir = Path.cwd()

        self.template_dir = Path(base_dir) / 'templates'
        print(f"📁 Looking for templates in: {self.template_dir.absolute()}")

        self.load_templates()

    def load_templates(self):
        if not self.template_dir.exists():
            print(f"📁 Creating templates directory: {self.template_dir}")
            self.template_dir.mkdir(parents=True, exist_ok=True)
            return

        loaded = 0
        for template_file in self.template_dir.glob('*.json'):
            print(f"📄 Found template file: {template_file.name}")
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                    for template_key, template_content in data.items():
                        if 'name' not in template_content:
                            template_content['name'] = template_key
                        self.templates[template_content['name']] = template_content
                        loaded += 1
                        print(f"✅ Loaded template: {template_content['name']}")

            except Exception as e:
                print(f"⚠️ Error loading {template_file.name}: {e}")

        print(f"📊 Loaded {loaded} templates")
        print(f"📊 Available: {list(self.templates.keys())}")

    def get_template_names(self):
        return list(self.templates.keys())

    def import_template(self):
        path = filedialog.askopenfilename(
            title="Import Template",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if not path:
            return None

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if not isinstance(data, dict):
                raise ValueError("Template file must contain a JSON object")

            self.template_dir.mkdir(parents=True, exist_ok=True)

            dest = self.template_dir / Path(path).name
            counter = 1
            while dest.exists():
                dest = self.template_dir / f"{Path(path).stem}_{counter}{Path(path).suffix}"
                counter += 1

            with open(dest, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

            loaded = 0
            for template_key, template_content in data.items():
                if 'name' not in template_content:
                    template_content['name'] = template_key
                self.templates[template_content['name']] = template_content
                loaded += 1

            messagebox.showinfo("Success", f"Imported {loaded} templates")
            return list(data.keys())[0]

        except Exception as e:
            messagebox.showerror("Error", f"Failed to import: {e}")
            return None

    def apply_style(self, ax, template_name):
        if template_name not in self.templates:
            return ax

        style = self.templates[template_name]

        axes_style = style.get('axes', {})
        ax.tick_params(
            direction=axes_style.get('direction', 'in'),
            top=axes_style.get('mirror', True),
            right=axes_style.get('mirror', True),
            bottom=True,
            left=True,
            which='major',
            length=axes_style.get('major_tick_len', 5),
            width=axes_style.get('spine_width', 1.0)
        )

        spine_width = axes_style.get('spine_width', 1.0)
        spine_color = axes_style.get('spine_color', 'black')

        for spine in ax.spines.values():
            spine.set_linewidth(spine_width)
            spine.set_color(spine_color)

        grid_style = style.get('grid', {})
        if grid_style.get('enabled', False):
            ax.grid(
                True,
                which='major',
                linestyle=grid_style.get('style', '--'),
                linewidth=grid_style.get('width', 0.5),
                color=grid_style.get('color', 'gray'),
                alpha=grid_style.get('alpha', 0.3)
            )

        font_style = style.get('fonts', {})
        if font_style:
            label_size = font_style.get('label_size', 10)
            tick_size = font_style.get('tick_size', 9)
            font_family = 'Arial'
            font_weight = font_style.get('weight', 'normal')

            if ax.get_xlabel():
                ax.xaxis.label.set_size(label_size)
                ax.xaxis.label.set_family(font_family)
                ax.xaxis.label.set_weight(font_weight)

            if ax.get_ylabel():
                ax.yaxis.label.set_size(label_size)
                ax.yaxis.label.set_family(font_family)
                ax.yaxis.label.set_weight(font_weight)

            if hasattr(ax, 'get_title') and ax.get_title():
                ax.title.set_size(label_size + 1)
                ax.title.set_family(font_family)
                ax.title.set_weight('bold')

            for label in ax.get_xticklabels() + ax.get_yticklabels():
                label.set_fontsize(tick_size)
                label.set_family(font_family)
                if font_weight == 'bold':
                    label.set_weight('bold')

        return ax

    def get_geochem_values(self, template_name):
        if template_name not in self.templates:
            return None
        return self.templates[template_name].get('geochem', {}).get('norm_values', None)

# ============================================================================
# NEW: EXPORT DIALOG WITH VECTOR FORMATS
# ============================================================================

class ExportDialog(tk.Toplevel):
    """Professional export dialog with vector format support"""

    def __init__(self, parent, figure, current_settings):
        super().__init__(parent)
        self.title("Export Figure")
        self.geometry("550x650")
        self.transient(parent)
        self.figure = figure
        self.current_settings = current_settings
        self.result_path = None

        self._create_ui()

    def _create_ui(self):
        main = ttk.Frame(self, padding=15)
        main.pack(fill=tk.BOTH, expand=True)

        # Title
        ttk.Label(main, text="Export Publication-Quality Figure",
                 font=('Arial', 12, 'bold')).pack(pady=(0, 15))

        # ===== FORMAT SELECTION =====
        format_frame = ttk.LabelFrame(main, text="Export Format", padding=10)
        format_frame.pack(fill=tk.X, pady=5)

        self.format_var = tk.StringVar(value="PDF (Vector - Journals prefer)")
        formats = [
            "PDF (Vector - Journals prefer)",
            "SVG (Vector - Editable in Inkscape/Illustrator)",
            "EPS (Vector - LaTeX compatible)",
            "PNG (Raster - High resolution)",
            "TIFF (Raster - Print quality)",
            "JPG (Raster - Small file size)"
        ]
        format_combo = ttk.Combobox(format_frame, textvariable=self.format_var,
                                    values=formats, state='readonly', width=40)
        format_combo.pack(pady=5)
        format_combo.bind('<<ComboboxSelected>>', self._on_format_change)

        # Format info label
        self.format_info = ttk.Label(format_frame, text="", font=('Arial', 8, 'italic'))
        self.format_info.pack()
        self._update_format_info()

        # ===== RESOLUTION (for raster formats) =====
        self.resolution_frame = ttk.LabelFrame(main, text="Resolution Settings", padding=10)
        self.resolution_frame.pack(fill=tk.X, pady=5)

        dpi_row = ttk.Frame(self.resolution_frame)
        dpi_row.pack(fill=tk.X, pady=2)
        ttk.Label(dpi_row, text="DPI:").pack(side=tk.LEFT)
        self.dpi_var = tk.IntVar(value=self.current_settings.get('dpi', 300))
        dpi_spin = ttk.Spinbox(dpi_row, from_=72, to=1200, increment=1,
                              textvariable=self.dpi_var, width=6)
        dpi_spin.pack(side=tk.LEFT, padx=5)

        ttk.Label(dpi_row, text="(300+ for print, 150 for web, 72 for screen)").pack(side=tk.LEFT)

        # DPI presets
        preset_frame = ttk.Frame(self.resolution_frame)
        preset_frame.pack(fill=tk.X, pady=5)
        ttk.Label(preset_frame, text="Presets:").pack(side=tk.LEFT)
        ttk.Button(preset_frame, text="Screen (72)",
                  command=lambda: self.dpi_var.set(72)).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_frame, text="Web (150)",
                  command=lambda: self.dpi_var.set(150)).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_frame, text="Print (300)",
                  command=lambda: self.dpi_var.set(300)).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_frame, text="Journal (600)",
                  command=lambda: self.dpi_var.set(600)).pack(side=tk.LEFT, padx=2)

        # ===== SIZE OPTIONS =====
        size_frame = ttk.LabelFrame(main, text="Figure Size", padding=10)
        size_frame.pack(fill=tk.X, pady=5)

        # Get current size
        width_in, height_in = self.figure.get_size_inches()

        size_row = ttk.Frame(size_frame)
        size_row.pack(fill=tk.X, pady=2)
        ttk.Label(size_row, text="Width:").pack(side=tk.LEFT)
        self.width_var = tk.DoubleVar(value=width_in)
        w_spin = ttk.Spinbox(size_row, from_=1, to=20, increment=0.1,
                            textvariable=self.width_var, width=5)
        w_spin.pack(side=tk.LEFT, padx=2)
        ttk.Label(size_row, text="inches").pack(side=tk.LEFT)

        ttk.Label(size_row, text="  Height:").pack(side=tk.LEFT, padx=(10,0))
        self.height_var = tk.DoubleVar(value=height_in)
        h_spin = ttk.Spinbox(size_row, from_=1, to=20, increment=0.1,
                            textvariable=self.height_var, width=5)
        h_spin.pack(side=tk.LEFT, padx=2)
        ttk.Label(size_row, text="inches").pack(side=tk.LEFT)

        # Aspect ratio lock
        self.lock_aspect = tk.BooleanVar(value=True)
        ttk.Checkbutton(size_frame, text="Lock aspect ratio",
                       variable=self.lock_aspect).pack(anchor=tk.W, pady=2)

        # Journal presets
        journal_frame = ttk.Frame(size_frame)
        journal_frame.pack(fill=tk.X, pady=5)
        ttk.Label(journal_frame, text="Journal Presets:").pack(side=tk.LEFT)

        journals = [
            ("Nature (1-col)", 3.5, 2.8),
            ("Nature (2-col)", 7.2, 5.8),
            ("Science", 3.5, 3.0),
            ("AGU", 7.0, 5.5),
            ("Geology", 7.0, 5.0),
            ("EPSL", 7.0, 5.0),
            ("J Petrology", 6.5, 5.5)
        ]

        for name, w, h in journals[:4]:  # First 4
            btn = ttk.Button(journal_frame, text=name,
                           command=lambda w=w, h=h: self._set_size(w, h))
            btn.pack(side=tk.LEFT, padx=2)

        more_frame = ttk.Frame(size_frame)
        more_frame.pack(fill=tk.X, pady=2)
        for name, w, h in journals[4:]:  # Rest
            btn = ttk.Button(more_frame, text=name,
                           command=lambda w=w, h=h: self._set_size(w, h))
            btn.pack(side=tk.LEFT, padx=2)

        # ===== COLOR OPTIONS =====
        color_frame = ttk.LabelFrame(main, text="Color Options", padding=10)
        color_frame.pack(fill=tk.X, pady=5)

        # Color mode
        mode_row = ttk.Frame(color_frame)
        mode_row.pack(fill=tk.X)
        ttk.Label(mode_row, text="Color mode:").pack(side=tk.LEFT)
        self.color_mode = tk.StringVar(value="RGB")
        ttk.Radiobutton(mode_row, text="RGB", variable=self.color_mode,
                       value="RGB").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_row, text="CMYK", variable=self.color_mode,
                       value="CMYK").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_row, text="Grayscale", variable=self.color_mode,
                       value="Grayscale").pack(side=tk.LEFT, padx=5)

        # Transparency
        trans_row = ttk.Frame(color_frame)
        trans_row.pack(fill=tk.X, pady=2)
        self.transparent = tk.BooleanVar(value=False)
        ttk.Checkbutton(trans_row, text="Transparent background",
                       variable=self.transparent).pack(side=tk.LEFT)

        # ===== METADATA =====
        meta_frame = ttk.LabelFrame(main, text="Metadata", padding=10)
        meta_frame.pack(fill=tk.X, pady=5)

        ttk.Label(meta_frame, text="Title:").grid(row=0, column=0, sticky=tk.W)
        self.title_var = tk.StringVar(value="GeoPlot Pro Figure")
        ttk.Entry(meta_frame, textvariable=self.title_var, width=30).grid(row=0, column=1, padx=5)

        ttk.Label(meta_frame, text="Author:").grid(row=1, column=0, sticky=tk.W)
        self.author_var = tk.StringVar(value="Generated with GeoPlot Pro")
        ttk.Entry(meta_frame, textvariable=self.author_var, width=30).grid(row=1, column=1, padx=5)

        # ===== PREVIEW =====
        preview_frame = ttk.LabelFrame(main, text="Export Preview", padding=5)
        preview_frame.pack(fill=tk.X, pady=5)

        # Calculate file size estimate
        self.preview_label = ttk.Label(preview_frame, text="")
        self.preview_label.pack()
        self._update_preview()

        # ===== BUTTONS =====
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X, pady=10)

        ttk.Button(btn_frame, text="Export", command=self._export,
                  style='Accent.TButton').pack(side=tk.RIGHT, padx=2)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=2)

    def _on_format_change(self, event=None):
        """Update UI based on selected format"""
        self._update_format_info()
        self._update_preview()

        # Enable/disable resolution for vector formats
        fmt = self.format_var.get()
        if "PDF" in fmt or "SVG" in fmt or "EPS" in fmt:
            # Vector formats - DPI is less relevant
            for child in self.resolution_frame.winfo_children():
                if isinstance(child, ttk.LabelFrame):
                    child.configure(text="Resolution (for raster preview only)")
        else:
            # Raster formats
            for child in self.resolution_frame.winfo_children():
                if isinstance(child, ttk.LabelFrame):
                    child.configure(text="Resolution Settings")

    def _update_format_info(self):
        """Update format information text"""
        fmt = self.format_var.get()
        if "PDF" in fmt:
            self.format_info.config(text="✓ Preferred by most journals • Vector • Editable text • Small file size")
        elif "SVG" in fmt:
            self.format_info.config(text="✓ Editable in Inkscape/Illustrator • Vector • Web-compatible")
        elif "EPS" in fmt:
            self.format_info.config(text="✓ LaTeX compatible • Vector • Older format, use PDF for new work")
        elif "PNG" in fmt:
            self.format_info.config(text="✓ Widely supported • Lossless • Good for web • Large file size")
        elif "TIFF" in fmt:
            self.format_info.config(text="✓ Print industry standard • Lossless • Very large files")
        elif "JPG" in fmt:
            self.format_info.config(text="✓ Small file size • Lossy compression • Not for publications")

    def _update_preview(self):
        """Update export preview information"""
        fmt = self.format_var.get()
        dpi = self.dpi_var.get()
        width = self.width_var.get()
        height = self.height_var.get()

        # Estimate file size (rough approximation)
        if "PDF" in fmt or "SVG" in fmt or "EPS" in fmt:
            # Vector files: size based on complexity, not DPI
            size_estimate = "50 KB - 500 KB (depends on complexity)"
        else:
            # Raster files: width * height * dpi^2 * color depth / compression
            pixels = int(width * dpi) * int(height * dpi)
            if "PNG" in fmt:
                size_mb = pixels * 3 / 1024 / 1024 / 2  # Rough PNG compression
            elif "TIFF" in fmt:
                size_mb = pixels * 3 / 1024 / 1024  # Uncompressed
            else:  # JPG
                size_mb = pixels * 3 / 1024 / 1024 / 10  # JPG compression
            size_estimate = f"~{size_mb:.1f} MB"

        # Journal check
        journal_ok = "✓" if "PDF" in fmt else "⚠️"
        journal_text = f"{journal_ok} PDF recommended for journals" if "PDF" not in fmt else "✓ PDF format - journal ready"

        preview = f"Format: {fmt}\nSize: {width:.1f} × {height:.1f} inches @ {dpi} DPI\nEstimated file: {size_estimate}\n{journal_text}"
        self.preview_label.config(text=preview)

    def _set_size(self, width, height):
        """Set figure size from preset"""
        self.width_var.set(width)
        self.height_var.set(height)
        self._update_preview()

    def _export(self):
        """Perform the export"""
        fmt = self.format_var.get()
        dpi = self.dpi_var.get()
        width = self.width_var.get()
        height = self.height_var.get()

        # Determine file extension
        if "PDF" in fmt:
            ext = ".pdf"
            ftype = "PDF files"
        elif "SVG" in fmt:
            ext = ".svg"
            ftype = "SVG files"
        elif "EPS" in fmt:
            ext = ".eps"
            ftype = "EPS files"
        elif "PNG" in fmt:
            ext = ".png"
            ftype = "PNG files"
        elif "TIFF" in fmt:
            ext = ".tiff"
            ftype = "TIFF files"
        else:  # JPG
            ext = ".jpg"
            ftype = "JPEG files"

        # Ask for filename
        filename = filedialog.asksaveasfilename(
            defaultextension=ext,
            filetypes=[(ftype, f"*{ext}"), ("All files", "*.*")],
            initialfile=f"geoplot_{datetime.datetime.now().strftime('%Y%m%d')}{ext}"
        )

        if not filename:
            return

        try:
            # Set figure size
            self.figure.set_size_inches(width, height)

            # Prepare save arguments
            save_kwargs = {
                'dpi': dpi,
                'bbox_inches': 'tight',
                'pad_inches': 0.05
            }

            # Format-specific options
            if ext == '.pdf':
                save_kwargs.update({
                    'format': 'pdf',
                    'metadata': {
                        'Title': self.title_var.get(),
                        'Author': self.author_var.get(),
                        'Creator': 'GeoPlot Pro v2.0'
                    }
                })
            elif ext == '.svg':
                save_kwargs.update({
                    'format': 'svg',
                    'metadata': {
                        'Title': self.title_var.get(),
                        'Author': self.author_var.get()
                    }
                })
            elif ext == '.eps':
                save_kwargs.update({
                    'format': 'eps'
                })
            elif ext == '.png':
                save_kwargs.update({
                    'format': 'png',
                    'transparent': self.transparent.get()
                })
            elif ext == '.tiff':
                save_kwargs.update({
                    'format': 'tiff',
                    'transparent': self.transparent.get()
                })
            elif ext == '.jpg':
                save_kwargs.update({
                    'format': 'jpeg',
                    'quality': 95,
                    'optimize': True
                })

            # Handle color mode
            if self.color_mode.get() == "Grayscale":
                # Convert figure to grayscale
                import matplotlib.colors as mcolors
                for ax in self.figure.axes:
                    for artist in ax.collections + ax.lines + ax.patches:
                        if hasattr(artist, 'set_color'):
                            if artist.get_color() is not None:
                                # Convert RGB to grayscale
                                c = artist.get_color()
                                if len(c) >= 3 and not isinstance(c, str):
                                    gray = 0.2989 * c[0] + 0.5870 * c[1] + 0.1140 * c[2]
                                    artist.set_color((gray, gray, gray, c[3] if len(c) > 3 else 1.0))

            # Save the figure
            self.figure.savefig(filename, **save_kwargs)

            self.result_path = filename
            messagebox.showinfo("Export Successful",
                              f"Figure exported to:\n{filename}\n\n"
                              f"Format: {fmt}\n"
                              f"Size: {width:.1f} × {height:.1f} inches @ {dpi} DPI")
            self.destroy()

        except Exception as e:
            messagebox.showerror("Export Failed", f"Error saving figure:\n{str(e)}")
            import traceback
            traceback.print_exc()

# ============================================================================
# NEW: MINERAL CLASSIFICATION PLOTS
# ============================================================================

class MineralPlots:
    """Mineral classification diagrams"""

    @staticmethod
    def plot_pyroxene_quadrilateral(ax, samples, df):
        """Plot pyroxene quadrilateral (Wo-En-Fs)"""
        if df.empty:
            ax.text(0.5, 0.5, "No pyroxene data", ha='center', va='center')
            return

        # Check for pyroxene end-members
        wo_cols = [c for c in df.columns if 'Wo' in c or 'Wollastonite' in c]
        en_cols = [c for c in df.columns if 'En' in c or 'Enstatite' in c]
        fs_cols = [c for c in df.columns if 'Fs' in c or 'Ferrosilite' in c]

        if not (wo_cols and en_cols and fs_cols):
            # Calculate from major elements if available
            if all(c in df.columns for c in ['SiO2_wt', 'MgO_wt', 'FeO_star_wt', 'CaO_wt']):
                # Simplified pyroxene calculation
                sio2 = df['SiO2_wt'].values
                mgo = df['MgO_wt'].values
                feo = df['FeO_star_wt'].values
                cao = df['CaO_wt'].values

                # Normalize to 4 cations
                total = sio2/60.08 + mgo/40.30 + feo/71.84 + cao/56.08
                wo = (cao/56.08) / total * 100
                en = (mgo/40.30) / total * 100
                fs = (feo/71.84) / total * 100

                # Renormalize to 100%
                pyx_total = wo + en + fs
                wo = wo / pyx_total * 100
                en = en / pyx_total * 100
                fs = fs / pyx_total * 100
            else:
                ax.text(0.5, 0.5, "Map pyroxene data first", ha='center', va='center')
                return
        else:
            wo = df[wo_cols[0]].values
            en = df[en_cols[0]].values
            fs = df[fs_cols[0]].values

        # Draw quadrilateral
        # Clinopyroxene field
        cpx_x = [0, 20, 45, 45, 20, 0]
        cpx_y = [100, 80, 55, 45, 20, 0]
        ax.fill(cpx_x, cpx_y, alpha=0.1, color='#87CEEB', label='Clinopyroxene')

        # Orthopyroxene field
        opx_x = [0, 50, 50, 0]
        opx_y = [0, 0, 50, 50]
        ax.fill(opx_x, opx_y, alpha=0.1, color='#F4A460', label='Orthopyroxene')

        # Pigeonite field
        pig_x = [30, 50, 50, 30]
        pig_y = [70, 50, 30, 50]
        ax.fill(pig_x, pig_y, alpha=0.1, color='#98FB98', label='Pigeonite')

        # Plot data
        ax.scatter(en, wo, c='red', s=30, alpha=0.7, edgecolors='black', linewidth=0.5, zorder=5)

        # Add sample labels
        for i, (e, w) in enumerate(zip(en, wo)):
            if i < 10:  # Label first 10 samples
                sample_id = df.iloc[i].get('Sample_ID', f'S{i}')
                ax.annotate(str(sample_id)[:4], (e, w), fontsize=6,
                          xytext=(2,2), textcoords='offset points')

        ax.set_xlim(0, 100)
        ax.set_ylim(0, 100)
        ax.set_xlabel('Enstatite (En)', fontsize=8)
        ax.set_ylabel('Wollastonite (Wo)', fontsize=8)

        # Add diagonal line for Diopside-Hedenbergite join
        ax.plot([0, 0], [0, 100], 'k--', alpha=0.3, linewidth=0.5)
        ax.plot([100, 0], [0, 100], 'k--', alpha=0.3, linewidth=0.5)

        ax.text(10, 90, 'Di', fontsize=6, ha='center')
        ax.text(90, 10, 'Hd', fontsize=6, ha='center')
        ax.text(50, 10, 'En', fontsize=6, ha='center')
        ax.text(10, 10, 'Fs', fontsize=6, ha='center')

        ax.set_title('Pyroxene Quadrilateral', fontsize=10, fontweight='bold')
        ax.legend(loc='upper right', fontsize=6)
        ax.grid(True, alpha=0.2)

    @staticmethod
    def plot_feldspar_ternary(ax, samples, df):
        """Plot feldspar ternary (An-Ab-Or)"""
        if df.empty:
            ax.text(0.5, 0.5, "No feldspar data", ha='center', va='center')
            return

        # Check for feldspar end-members
        an_cols = [c for c in df.columns if 'An' in c or 'Anorthite' in c]
        ab_cols = [c for c in df.columns if 'Ab' in c or 'Albite' in c]
        or_cols = [c for c in df.columns if 'Or' in c or 'Orthoclase' in c]

        if not (an_cols and ab_cols and or_cols):
            # Calculate from major elements
            if all(c in df.columns for c in ['CaO_wt', 'Na2O_wt', 'K2O_wt']):
                cao = df['CaO_wt'].values
                na2o = df['Na2O_wt'].values
                k2o = df['K2O_wt'].values

                # Convert to molecular proportions
                an = (cao / 56.08) * 2
                ab = (na2o / 61.98) * 2
                or_ = (k2o / 94.20) * 2

                # Normalize to 100%
                total = an + ab + or_
                an = an / total * 100
                ab = ab / total * 100
                or_ = or_ / total * 100
            else:
                ax.text(0.5, 0.5, "Map feldspar data first", ha='center', va='center')
                return
        else:
            an = df[an_cols[0]].values
            ab = df[ab_cols[0]].values
            or_ = df[or_cols[0]].values

        # Draw ternary diagram
        # Convert to ternary coordinates
        x = 0.5 * (2*ab + or_) / (an + ab + or_ + 1e-10)
        y = np.sqrt(3)/2 * or_ / (an + ab + or_ + 1e-10)

        # Draw ternary frame
        ax.plot([0, 1], [0, 0], 'k-', linewidth=1)
        ax.plot([0, 0.5], [0, np.sqrt(3)/2], 'k-', linewidth=1)
        ax.plot([1, 0.5], [0, np.sqrt(3)/2], 'k-', linewidth=1)

        # Add field boundaries
        # Alkali feldspar
        ax.fill([0, 0.2, 0.3, 0.1], [0, 0.1, 0.26, 0.17], alpha=0.1, color='#FFB6C1', label='Alkali Feldspar')

        # Plagioclase
        ax.fill([0.2, 0.8, 0.7, 0.3], [0.1, 0.1, 0.26, 0.26], alpha=0.1, color='#87CEEB', label='Plagioclase')

        # Plot data
        ax.scatter(x, y, c='red', s=30, alpha=0.7, edgecolors='black', linewidth=0.5, zorder=5)

        # Labels
        ax.text(0.5, -0.08, 'Albite (Ab)', ha='center', fontsize=8)
        ax.text(-0.08, 0, 'Anorthite (An)', ha='right', va='center', fontsize=8)
        ax.text(1.08, 0, 'Orthoclase (Or)', ha='left', va='center', fontsize=8)

        ax.set_xlim(-0.1, 1.1)
        ax.set_ylim(-0.1, np.sqrt(3)/2 + 0.1)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title('Feldspar Ternary (An-Ab-Or)', fontsize=10, fontweight='bold')
        ax.legend(loc='upper right', fontsize=6)

    @staticmethod
    def plot_amphibole_classification(ax, samples, df):
        """Plot amphibole classification after Hawthorne et al."""
        if df.empty:
            ax.text(0.5, 0.5, "No amphibole data", ha='center', va='center')
            return

        # Check for required elements
        if not all(c in df.columns for c in ['Si_apfu', 'Mg#', 'Na_apfu', 'Ca_apfu']):
            ax.text(0.5, 0.5, "Calculate amphibole APFU first", ha='center', va='center')
            return

        si = df['Si_apfu'].values
        mg_number = df['Mg#'].values

        # Draw classification fields
        # Tremolite - Actinolite - Hornblende
        ax.axvspan(7.5, 8.0, 0.5, 1.0, alpha=0.1, color='#87CEEB', label='Tremolite')
        ax.axvspan(7.0, 7.5, 0.5, 1.0, alpha=0.1, color='#F4A460', label='Actinolite')
        ax.axvspan(6.0, 7.0, 0.5, 1.0, alpha=0.1, color='#FFB6C1', label='Hornblende')
        ax.axvspan(5.0, 6.0, 0.5, 1.0, alpha=0.1, color='#98FB98', label='Cummingtonite')

        # Plot data
        ax.scatter(si, mg_number, c='red', s=30, alpha=0.7, edgecolors='black', linewidth=0.5, zorder=5)

        ax.set_xlim(5.0, 8.0)
        ax.set_ylim(0, 100)
        ax.set_xlabel('Si (apfu)', fontsize=8)
        ax.set_ylabel('Mg#', fontsize=8)
        ax.set_title('Amphibole Classification', fontsize=10, fontweight='bold')
        ax.legend(loc='upper left', fontsize=6)
        ax.grid(True, alpha=0.2)

    @staticmethod
    def plot_compositional_biplot(ax, df, elements):
        """Plot compositional biplot using CLR transformation"""
        if not HAS_SKLEARN or df.empty:
            ax.text(0.5, 0.5, "scikit-learn not available", ha='center', va='center')
            return

        from sklearn.decomposition import PCA

        # Get compositional data
        comp_data = df[elements].fillna(0).values
        comp_data = comp_data[comp_data.sum(axis=1) > 0]

        if len(comp_data) < 2:
            ax.text(0.5, 0.5, "Insufficient data", ha='center', va='center')
            return

        # CLR transformation
        with np.errstate(divide='ignore', invalid='ignore'):
            log_data = np.log(comp_data)
            clr = log_data - log_data.mean(axis=1, keepdims=True)
            clr = np.nan_to_num(clr, nan=0, posinf=0, neginf=0)

        # PCA on CLR
        pca = PCA(n_components=2)
        scores = pca.fit_transform(clr)

        # Plot scores
        ax.scatter(scores[:, 0], scores[:, 1], c='blue', s=20, alpha=0.6,
                  edgecolors='black', linewidth=0.5)

        # Plot loadings
        loadings = pca.components_.T
        for i, (loading, elem) in enumerate(zip(loadings, elements)):
            ax.arrow(0, 0, loading[0]*2, loading[1]*2,
                    head_width=0.1, head_length=0.1, fc='red', ec='red', alpha=0.5)
            ax.text(loading[0]*2.2, loading[1]*2.2, elem, fontsize=6, color='red')

        var_exp = pca.explained_variance_ratio_ * 100
        ax.set_xlabel(f'CLR PC1 ({var_exp[0]:.1f}%)', fontsize=8)
        ax.set_ylabel(f'CLR PC2 ({var_exp[1]:.1f}%)', fontsize=8)
        ax.set_title('Compositional Biplot (CLR)', fontsize=10, fontweight='bold')
        ax.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
        ax.axvline(x=0, color='gray', linestyle='-', alpha=0.3)
        ax.grid(True, alpha=0.2)

# ============================================================================
# NEW: AFC MODELING PLOTS
# ============================================================================

class AFCModel:
    """Assimilation-Fractional Crystallization modeling"""

    def __init__(self):
        self.params = AFC_DEFAULTS.copy()
        self.reset()

    def reset(self):
        """Reset to default parameters"""
        self.params = AFC_DEFAULTS.copy()
        self.trace_element = 'Sr'
        self.compatible = False

    def afc_equation(self, F, r, D, C0, Ca):
        """AFC equation after DePaolo (1981)"""
        if abs(r - 1.0) < 1e-6:
            # Special case r = 1
            return C0 * F ** (-D) + Ca * (1 - F ** (-D))
        else:
            z = (r + D - 1) / (r - 1)
            return C0 * F ** (-z) + (Ca / (r * z)) * (1 - F ** z)

    def plot_afc_curve(self, ax, F_range=(0.1, 1.0)):
        """Plot AFC curve"""
        F = np.linspace(F_range[0], F_range[1], 100)

        r = self.params['r_ratio']
        D = self.params['bulk_D']
        C0 = self.params['Co']
        Ca = self.params['Ca']

        C = self.afc_equation(F, r, D, C0, Ca)

        ax.plot(F, C, 'b-', linewidth=2, label=f'AFC (r={r:.2f}, D={D:.2f})')

        # Add fractional crystallization for comparison
        C_fc = C0 * F ** (D - 1)
        ax.plot(F, C_fc, 'r--', linewidth=1.5, alpha=0.7, label='FC only')

        ax.set_xlabel('F (melt fraction)', fontsize=8)
        ax.set_ylabel(f'Concentration ({self.trace_element} ppm)', fontsize=8)
        ax.set_title('AFC Model', fontsize=10, fontweight='bold')
        ax.legend(fontsize=6)
        ax.grid(True, alpha=0.2)
        ax.set_xlim(F_range)
        ax.invert_xaxis()  # F decreases during crystallization

        return F, C

    def plot_mixing_curve(self, ax, samples, df, x_col, y_col):
        """Plot binary mixing curve"""
        if df.empty or x_col not in df.columns or y_col not in df.columns:
            ax.text(0.5, 0.5, "Map X and Y columns first", ha='center', va='center')
            return

        # Get end-member compositions
        x_min, x_max = df[x_col].min(), df[x_col].max()
        y_min, y_max = df[y_col].min(), df[y_col].max()

        # Generate mixing curve
        f = np.linspace(0, 1, 100)  # mixing proportion

        # Assume end-members are min and max values
        x1, y1 = x_min, y_min
        x2, y2 = x_max, y_max

        x_mix = x1 * f + x2 * (1 - f)
        y_mix = y1 * f + y2 * (1 - f)

        ax.plot(x_mix, y_mix, 'g-', linewidth=2, label='Mixing line')

        # Add tick marks for mixing proportions
        for fi in [0.2, 0.4, 0.6, 0.8]:
            xi = x1 * fi + x2 * (1 - fi)
            yi = y1 * fi + y2 * (1 - fi)
            ax.plot(xi, yi, 'go', markersize=3)
            ax.annotate(f'{fi:.1f}', (xi, yi), fontsize=5, xytext=(2,2),
                       textcoords='offset points')

        # Plot data
        ax.scatter(df[x_col], df[y_col], c='red', s=20, alpha=0.7,
                  edgecolors='black', linewidth=0.5, zorder=5, label='Samples')

        ax.set_xlabel(x_col, fontsize=8)
        ax.set_ylabel(y_col, fontsize=8)
        ax.set_title('Binary Mixing Model', fontsize=10, fontweight='bold')
        ax.legend(fontsize=6)
        ax.grid(True, alpha=0.2)

    def plot_rayleigh_fractionation(self, ax, D_values=[0.01, 0.1, 0.5, 2, 5]):
        """Plot Rayleigh fractionation curves for different D"""
        F = np.linspace(0.01, 1, 100)

        for D in D_values:
            C_C0 = F ** (D - 1)
            label = f'D={D}' if D != 1 else 'D=1 (compatible)' if D < 1 else f'D={D} (incompatible)'
            ax.plot(F, C_C0, linewidth=1.5, label=label)

        ax.set_xlabel('F (melt fraction)', fontsize=8)
        ax.set_ylabel('C/C₀', fontsize=8)
        ax.set_title('Rayleigh Fractionation', fontsize=10, fontweight='bold')
        ax.legend(fontsize=6)
        ax.grid(True, alpha=0.2)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 5)
        ax.invert_xaxis()
        ax.axhline(y=1, color='gray', linestyle='--', alpha=0.5, linewidth=0.5)

# ============================================================================
# NEW: AFC Interactive Dialog
# ============================================================================

class AFCInteractiveDialog(tk.Toplevel):
    """Interactive AFC modeling with sliders"""

    def __init__(self, parent, plotter):
        super().__init__(parent)
        self.title("AFC Modeler")
        self.geometry("600x700")
        self.transient(parent)
        self.plotter = plotter
        self.model = AFCModel()

        self._create_ui()
        self._update_plot()

    def _create_ui(self):
        main = ttk.Frame(self, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        # Title
        ttk.Label(main, text="Assimilation-Fractional Crystallization Model",
                 font=('Arial', 12, 'bold')).pack(pady=5)

        # ===== PARAMETER CONTROLS =====
        params_frame = ttk.LabelFrame(main, text="Model Parameters", padding=10)
        params_frame.pack(fill=tk.X, pady=5)

        # r ratio (assimilation/crystallization)
        r_frame = ttk.Frame(params_frame)
        r_frame.pack(fill=tk.X, pady=2)
        ttk.Label(r_frame, text="r (assimilation/crystallization):", width=25).pack(side=tk.LEFT)
        self.r_var = tk.DoubleVar(value=self.model.params['r_ratio'])
        r_scale = ttk.Scale(r_frame, from_=0, to=1, variable=self.r_var,
                           orient=tk.HORIZONTAL, command=self._on_param_change)
        r_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.r_label = ttk.Label(r_frame, text=f"{self.r_var.get():.2f}", width=5)
        self.r_label.pack(side=tk.LEFT)

        # Bulk D
        d_frame = ttk.Frame(params_frame)
        d_frame.pack(fill=tk.X, pady=2)
        ttk.Label(d_frame, text="Bulk D (distribution coefficient):", width=25).pack(side=tk.LEFT)
        self.d_var = tk.DoubleVar(value=self.model.params['bulk_D'])
        d_scale = ttk.Scale(d_frame, from_=0, to=5, variable=self.d_var,
                           orient=tk.HORIZONTAL, command=self._on_param_change)
        d_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.d_label = ttk.Label(d_frame, text=f"{self.d_var.get():.2f}", width=5)
        self.d_label.pack(side=tk.LEFT)

        # Initial concentration (C0)
        c0_frame = ttk.Frame(params_frame)
        c0_frame.pack(fill=tk.X, pady=2)
        ttk.Label(c0_frame, text="Initial concentration (C₀):", width=25).pack(side=tk.LEFT)
        self.c0_var = tk.DoubleVar(value=self.model.params['Co'])
        c0_scale = ttk.Scale(c0_frame, from_=1, to=1000, variable=self.c0_var,
                            orient=tk.HORIZONTAL, command=self._on_param_change)
        c0_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.c0_label = ttk.Label(c0_frame, text=f"{self.c0_var.get():.1f}", width=5)
        self.c0_label.pack(side=tk.LEFT)

        # Assimilant concentration (Ca)
        ca_frame = ttk.Frame(params_frame)
        ca_frame.pack(fill=tk.X, pady=2)
        ttk.Label(ca_frame, text="Assimilant concentration (Cₐ):", width=25).pack(side=tk.LEFT)
        self.ca_var = tk.DoubleVar(value=self.model.params['Ca'])
        ca_scale = ttk.Scale(ca_frame, from_=1, to=1000, variable=self.ca_var,
                            orient=tk.HORIZONTAL, command=self._on_param_change)
        ca_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.ca_label = ttk.Label(ca_frame, text=f"{self.ca_var.get():.1f}", width=5)
        self.ca_label.pack(side=tk.LEFT)

        # ===== TRACE ELEMENT SELECTION =====
        elem_frame = ttk.LabelFrame(main, text="Trace Element", padding=10)
        elem_frame.pack(fill=tk.X, pady=5)

        ttk.Label(elem_frame, text="Element:").pack(side=tk.LEFT)
        self.elem_var = tk.StringVar(value="Sr")
        elements = ["Sr", "Nd", "Pb", "Rb", "Ba", "Th", "U", "Zr", "Hf", "Y"]
        elem_combo = ttk.Combobox(elem_frame, textvariable=self.elem_var,
                                 values=elements, width=10)
        elem_combo.pack(side=tk.LEFT, padx=5)
        elem_combo.bind('<<ComboboxSelected>>', lambda e: self._on_param_change())

        ttk.Label(elem_frame, text="Compatibility:").pack(side=tk.LEFT, padx=(20,2))
        self.compat_var = tk.StringVar(value="Incompatible (D<1)")
        compat_combo = ttk.Combobox(elem_frame, textvariable=self.compat_var,
                                   values=["Compatible (D>1)", "Incompatible (D<1)"],
                                   width=15)
        compat_combo.pack(side=tk.LEFT)

        # ===== PLOT AREA =====
        plot_frame = ttk.LabelFrame(main, text="AFC Model Plot", padding=5)
        plot_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # ===== BUTTONS =====
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(btn_frame, text="Reset", command=self._reset).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Export Plot", command=self._export_plot).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Add to Main Plot", command=self._add_to_main).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Close", command=self.destroy).pack(side=tk.RIGHT, padx=2)

    def _on_param_change(self, event=None):
        """Update model parameters and redraw"""
        self.model.params['r_ratio'] = self.r_var.get()
        self.model.params['bulk_D'] = self.d_var.get()
        self.model.params['Co'] = self.c0_var.get()
        self.model.params['Ca'] = self.ca_var.get()
        self.model.trace_element = self.elem_var.get()

        self.r_label.config(text=f"{self.r_var.get():.2f}")
        self.d_label.config(text=f"{self.d_var.get():.2f}")
        self.c0_label.config(text=f"{self.c0_var.get():.1f}")
        self.ca_label.config(text=f"{self.ca_var.get():.1f}")

        self._update_plot()

    def _update_plot(self):
        """Update the AFC plot"""
        self.ax.clear()
        self.model.plot_afc_curve(self.ax)
        self.ax.set_title(f"AFC Model - {self.model.trace_element}", fontsize=10, fontweight='bold')
        self.canvas.draw()

    def _reset(self):
        """Reset to default parameters"""
        self.model.reset()
        self.r_var.set(self.model.params['r_ratio'])
        self.d_var.set(self.model.params['bulk_D'])
        self.c0_var.set(self.model.params['Co'])
        self.ca_var.set(self.model.params['Ca'])
        self.elem_var.set('Sr')
        self._on_param_change()

    def _export_plot(self):
        """Export the AFC plot"""
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("PDF", "*.pdf"), ("SVG", "*.svg")],
            initialfile=f"afc_model_{datetime.datetime.now().strftime('%Y%m%d')}.png"
        )
        if filename:
            self.fig.savefig(filename, dpi=300, bbox_inches='tight')
            messagebox.showinfo("Success", f"Plot saved to {filename}")

    def _add_to_main(self):
        """Add this model to the main plot"""
        if hasattr(self.plotter, 'fig') and self.plotter.fig:
            # Create a new axis in the main figure
            ax = self.plotter.fig.add_subplot(2, 2, 4)  # Add as subplot
            self.model.plot_afc_curve(ax)
            self.plotter.canvas.draw()
            messagebox.showinfo("Success", "AFC model added to main plot")
        else:
            messagebox.showwarning("No Plot", "Generate a main plot first")

# ============================================================================
# NEW: ML Visualization Plots
# ============================================================================

class MLVisualization:
    """Machine learning visualization for geochemical data"""

    @staticmethod
    def plot_kmeans_clusters(ax, df, x_col, y_col, n_clusters=3):
        """Plot K-means clustering results"""
        if not HAS_SKLEARN or df.empty:
            ax.text(0.5, 0.5, "scikit-learn not available", ha='center', va='center')
            return

        from sklearn.cluster import KMeans
        from sklearn.preprocessing import StandardScaler

        # Get numeric columns for clustering
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) < 2:
            ax.text(0.5, 0.5, "Need at least 2 numeric columns", ha='center', va='center')
            return

        # Prepare data
        X = df[numeric_cols].fillna(0).values
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Perform clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(X_scaled)

        # Plot
        scatter = ax.scatter(df[x_col], df[y_col], c=clusters, cmap='viridis',
                           s=30, alpha=0.7, edgecolors='black', linewidth=0.5)

        # Plot centroids
        centroids = kmeans.cluster_centers_
        centroids_original = scaler.inverse_transform(centroids)

        # Find indices of x_col and y_col in numeric_cols
        x_idx = list(numeric_cols).index(x_col) if x_col in numeric_cols else 0
        y_idx = list(numeric_cols).index(y_col) if y_col in numeric_cols else 1

        ax.scatter(centroids_original[:, x_idx], centroids_original[:, y_idx],
                  c='red', s=100, marker='X', edgecolors='black', linewidth=1,
                  label='Centroids')

        ax.set_xlabel(x_col, fontsize=8)
        ax.set_ylabel(y_col, fontsize=8)
        ax.set_title(f'K-Means Clustering (k={n_clusters})', fontsize=10, fontweight='bold')
        ax.legend(fontsize=6)
        ax.grid(True, alpha=0.2)

        return clusters

    @staticmethod
    def plot_pca_biplot(ax, df):
        """Plot PCA biplot with loadings"""
        if not HAS_SKLEARN or df.empty:
            ax.text(0.5, 0.5, "scikit-learn not available", ha='center', va='center')
            return

        from sklearn.decomposition import PCA
        from sklearn.preprocessing import StandardScaler

        # Get numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) < 2:
            ax.text(0.5, 0.5, "Need at least 2 numeric columns", ha='center', va='center')
            return

        # Prepare data
        X = df[numeric_cols].fillna(0).values
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Perform PCA
        pca = PCA(n_components=2)
        X_pca = pca.fit_transform(X_scaled)

        # Plot scores
        ax.scatter(X_pca[:, 0], X_pca[:, 1], c='blue', s=20, alpha=0.6,
                  edgecolors='black', linewidth=0.5)

        # Plot loadings as arrows
        loadings = pca.components_.T
        for i, (loading, col) in enumerate(zip(loadings, numeric_cols)):
            ax.arrow(0, 0, loading[0]*3, loading[1]*3,
                    head_width=0.1, head_length=0.1, fc='red', ec='red', alpha=0.5)
            ax.text(loading[0]*3.2, loading[1]*3.2, col, fontsize=6, color='red')

        # Add variance explained
        var_exp = pca.explained_variance_ratio_ * 100
        ax.set_xlabel(f'PC1 ({var_exp[0]:.1f}%)', fontsize=8)
        ax.set_ylabel(f'PC2 ({var_exp[1]:.1f}%)', fontsize=8)
        ax.set_title('PCA Biplot', fontsize=10, fontweight='bold')
        ax.axhline(y=0, color='gray', linestyle='-', alpha=0.3, linewidth=0.5)
        ax.axvline(x=0, color='gray', linestyle='-', alpha=0.3, linewidth=0.5)
        ax.grid(True, alpha=0.2)

        return X_pca, pca

# ============================================================================
# NEW: CoDA Visualization
# ============================================================================

# ============================================================================
# NEW: CoDA Visualization
# ============================================================================

class CoDAVisualization:
    """Compositional Data Analysis visualization"""

    @staticmethod
    def plot_balance_dendrogram(ax, df, elements):
        """Plot balance dendrogram for compositional data"""
        if not HAS_COMPOSITIONAL or df.empty:
            ax.text(0.5, 0.5, "compositional package not available", ha='center', va='center')
            return

        try:
            # Get compositional data
            comp_data = df[elements].fillna(0).values
            comp_data = comp_data[comp_data.sum(axis=1) > 0]  # Remove zero rows

            if len(comp_data) < 2:
                ax.text(0.5, 0.5, "Insufficient data", ha='center', va='center')
                return

            # Calculate balances using Aitchison distance
            from scipy.cluster.hierarchy import dendrogram, linkage

            # Convert to CLR first
            with np.errstate(divide='ignore', invalid='ignore'):
                log_data = np.log(comp_data)
                clr = log_data - log_data.mean(axis=1, keepdims=True)
                clr = np.nan_to_num(clr, nan=0, posinf=0, neginf=0)

            # Hierarchical clustering
            Z = linkage(clr, method='ward')

            # Plot dendrogram
            dendrogram(Z, ax=ax, labels=elements, leaf_rotation=90, leaf_font_size=6)

            ax.set_title('Balance Dendrogram', fontsize=10, fontweight='bold')
            ax.set_ylabel('Aitchison Distance', fontsize=8)
            ax.set_xlabel('Elements', fontsize=8)

        except Exception as e:
            ax.text(0.5, 0.5, f"Error: {str(e)[:50]}", ha='center', va='center')

    @staticmethod
    def plot_compositional_biplot(ax, df, elements):  # ← FIXED: no space!
        """Plot compositional biplot using CLR transformation"""
        if not HAS_SKLEARN or df.empty:
            ax.text(0.5, 0.5, "scikit-learn not available", ha='center', va='center')
            return

        from sklearn.decomposition import PCA

        # Get compositional data
        comp_data = df[elements].fillna(0).values
        comp_data = comp_data[comp_data.sum(axis=1) > 0]

        if len(comp_data) < 2:
            ax.text(0.5, 0.5, "Insufficient data", ha='center', va='center')
            return

        # CLR transformation
        with np.errstate(divide='ignore', invalid='ignore'):
            log_data = np.log(comp_data)
            clr = log_data - log_data.mean(axis=1, keepdims=True)
            clr = np.nan_to_num(clr, nan=0, posinf=0, neginf=0)

        # PCA on CLR
        pca = PCA(n_components=2)
        scores = pca.fit_transform(clr)

        # Plot scores
        ax.scatter(scores[:, 0], scores[:, 1], c='blue', s=20, alpha=0.6,
                  edgecolors='black', linewidth=0.5)

        # Plot loadings
        loadings = pca.components_.T
        for i, (loading, elem) in enumerate(zip(loadings, elements)):
            ax.arrow(0, 0, loading[0]*2, loading[1]*2,
                    head_width=0.1, head_length=0.1, fc='red', ec='red', alpha=0.5)
            ax.text(loading[0]*2.2, loading[1]*2.2, elem, fontsize=6, color='red')

        var_exp = pca.explained_variance_ratio_ * 100
        ax.set_xlabel(f'CLR PC1 ({var_exp[0]:.1f}%)', fontsize=8)
        ax.set_ylabel(f'CLR PC2 ({var_exp[1]:.1f}%)', fontsize=8)
        ax.set_title('Compositional Biplot (CLR)', fontsize=10, fontweight='bold')
        ax.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
        ax.axvline(x=0, color='gray', linestyle='-', alpha=0.3)
        ax.grid(True, alpha=0.2)

# ============================================================================
# COLUMN SELECTOR (PRESERVED)
# ============================================================================

class ColumnSelector(tk.Toplevel):
    """Interactive column mapping for complex datasets (legacy)"""
    # [EXACTLY AS YOUR ORIGINAL - PRESERVED]

    def __init__(self, parent, samples, callback):
        super().__init__(parent)
        self.title("Column Selector")
        self.geometry("500x400")
        self.transient(parent)
        self.samples = samples
        self.callback = callback

        self._create_ui()

    def _create_ui(self):
        main = ttk.Frame(self, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="Map data columns to plot axes:",
                 font=('Arial', 10, 'bold')).pack(pady=5)

        columns = []
        if self.samples:
            for col in self.samples[0].keys():
                if col not in ['Sample_ID', 'Notes']:
                    columns.append(col)

        x_frame = ttk.Frame(main)
        x_frame.pack(fill=tk.X, pady=5)
        ttk.Label(x_frame, text="X-axis:", width=10).pack(side=tk.LEFT)
        self.x_var = tk.StringVar()
        ttk.Combobox(x_frame, textvariable=self.x_var, values=columns,
                    state='readonly').pack(side=tk.LEFT, fill=tk.X, expand=True)

        y_frame = ttk.Frame(main)
        y_frame.pack(fill=tk.X, pady=5)
        ttk.Label(y_frame, text="Y-axis:", width=10).pack(side=tk.LEFT)
        self.y_var = tk.StringVar()
        ttk.Combobox(y_frame, textvariable=self.y_var, values=columns,
                    state='readonly').pack(side=tk.LEFT, fill=tk.X, expand=True)

        z_frame = ttk.Frame(main)
        z_frame.pack(fill=tk.X, pady=5)
        ttk.Label(z_frame, text="Z-axis (opt):", width=10).pack(side=tk.LEFT)
        self.z_var = tk.StringVar()
        ttk.Combobox(z_frame, textvariable=self.z_var, values=[''] + columns,
                    state='readonly').pack(side=tk.LEFT, fill=tk.X, expand=True)

        err_frame = ttk.Frame(main)
        err_frame.pack(fill=tk.X, pady=5)
        ttk.Label(err_frame, text="Error (opt):", width=10).pack(side=tk.LEFT)
        self.err_var = tk.StringVar()
        ttk.Combobox(err_frame, textvariable=self.err_var, values=[''] + columns,
                    state='readonly').pack(side=tk.LEFT, fill=tk.X, expand=True)

        preview_frame = ttk.LabelFrame(main, text="Data Preview", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        preview_text = tk.Text(preview_frame, height=10, width=50)
        preview_text.pack(fill=tk.BOTH, expand=True)

        if self.samples:
            preview_text.insert('1.0', f"Columns: {', '.join(columns)}\n\n")
            preview_text.insert('end', f"Total samples: {len(self.samples)}\n\n")
            preview_text.insert('end', "First sample:\n")
            for k, v in list(self.samples[0].items())[:10]:
                preview_text.insert('end', f"  {k}: {v}\n")

        preview_text.config(state='disabled')

        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="Apply", command=self._apply).pack(side=tk.RIGHT, padx=2)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=2)

    def _apply(self):
        mapping = {
            'x': self.x_var.get(),
            'y': self.y_var.get(),
            'z': self.z_var.get() if self.z_var.get() else None,
            'error': self.err_var.get() if self.err_var.get() else None
        }
        self.callback(mapping)
        self.destroy()

# ============================================================================
# ADVANCED PEAK FITTER (PRESERVED)
# ============================================================================

class AdvancedPeakFitter:
    """Advanced multi-peak fitting with various peak shapes and baselines"""
    # [EXACTLY AS YOUR ORIGINAL - PRESERVED]

    BASELINE_TYPES = ['none', 'constant', 'linear', 'quadratic', 'cubic']

    def __init__(self):
        self.last_fit = None

    def gaussian(self, x, amp, center, width):
        return amp * np.exp(-(x - center)**2 / (2 * width**2))

    def lorentzian(self, x, amp, center, width):
        return amp * width**2 / ((x - center)**2 + width**2)

    def baseline_func(self, x, baseline_type, params):
        if baseline_type == 'none':
            return np.zeros_like(x)
        elif baseline_type == 'constant':
            return np.ones_like(x) * params[0]
        elif baseline_type == 'linear':
            return params[0] + params[1] * x
        elif baseline_type == 'quadratic':
            return params[0] + params[1] * x + params[2] * x**2
        elif baseline_type == 'cubic':
            return params[0] + params[1] * x + params[2] * x**2 + params[3] * x**3

    def voigt(self, x, amp, center, width, gamma=None):
        if gamma is None:
            gamma = width

        if HAS_SCIPY:
            from scipy.special import voigt_profile
            sigma = width / np.sqrt(2 * np.log(2))
            return amp * voigt_profile(x - center, sigma, gamma)
        else:
            return self.pseudo_voigt(x, amp, center, width, 0.5)

    def pseudo_voigt(self, x, amp, center, width, eta=0.5):
        g = self.gaussian(x, amp, center, width)
        l = self.lorentzian(x, amp, center, width)
        return eta * g + (1 - eta) * l

    def fit_peaks(self, x, y, n_peaks, peak_type='Gaussian', baseline_type='linear'):
        if not HAS_SCIPY:
            return None

        try:
            baseline_params = {
                'none': 0,
                'constant': 1,
                'linear': 2,
                'quadratic': 3,
                'cubic': 4
            }
            n_baseline = baseline_params.get(baseline_type, 2)

            if peak_type == 'Gaussian':
                peak_func = self.gaussian
            elif peak_type == 'Lorentzian':
                peak_func = self.lorentzian
            elif peak_type == 'Voigt':
                peak_func = self.voigt
            else:
                peak_func = self.gaussian
                print(f"Warning: Unknown peak type '{peak_type}', using Gaussian")

            def model(x, *params):
                baseline_p = params[:n_baseline]
                peak_p = params[n_baseline:]

                result = self.baseline_func(x, baseline_type, baseline_p)

                for i in range(n_peaks):
                    amp, center, width = peak_p[i*3:(i+1)*3]
                    result += peak_func(x, amp, center, width)

                return result

            p0 = []

            if baseline_type == 'none':
                pass
            elif baseline_type == 'constant':
                p0.append(np.min(y))
            elif baseline_type == 'linear':
                p0.extend([np.min(y), 0])
            elif baseline_type == 'quadratic':
                p0.extend([np.min(y), 0, 0])
            elif baseline_type == 'cubic':
                p0.extend([np.min(y), 0, 0, 0])

            x_range = x.max() - x.min()
            for i in range(n_peaks):
                center = x.min() + (i + 1) * x_range / (n_peaks + 1)
                amp = (y.max() - y.min()) * 0.8
                width = x_range / (n_peaks * 4)
                p0.extend([amp, center, width])

            popt, pcov = curve_fit(model, x, y, p0=p0, maxfev=10000)

            y_fit = model(x, *popt)

            baseline_p = popt[:n_baseline]
            y_baseline = self.baseline_func(x, baseline_type, baseline_p)

            individuals = []
            peak_p = popt[n_baseline:]
            for i in range(n_peaks):
                amp, center, width = peak_p[i*3:(i+1)*3]
                individuals.append(peak_func(x, amp, center, width))

            residuals = y - y_fit
            ss_res = np.sum(residuals**2)
            ss_tot = np.sum((y - np.mean(y))**2)
            r_squared = 1 - (ss_res / ss_tot)

            n = len(y)
            k = len(popt)
            adj_r_squared = 1 - (1 - r_squared) * (n - 1) / (n - k - 1)

            aic = n * np.log(ss_res / n) + 2 * k

            self.last_fit = {
                'fitted': y_fit,
                'baseline': y_baseline,
                'individuals': individuals,
                'params': popt,
                'r_squared': r_squared,
                'adj_r_squared': adj_r_squared,
                'aic': aic,
                'residuals': residuals
            }

            return self.last_fit

        except Exception as e:
            return None

# ============================================================================
# BATCH PROCESSOR (PRESERVED + ENHANCED)
# ============================================================================

class BatchProcessor(tk.Toplevel):
    """Batch plot generation with threading - ENHANCED"""
    # [PRESERVING YOUR ORIGINAL STRUCTURE + ADDING ENHANCEMENTS]

    def __init__(self, parent, plotter):
        super().__init__(parent)
        self.title("Batch Processor")
        self.geometry("700x600")
        self.transient(parent)
        self.plotter = plotter
        self.running = False
        self._thread_lock = threading.Lock()

        self._create_ui()

    def _create_ui(self):
        main = ttk.Frame(self, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="Batch Plot Generation",
                 font=('Arial', 12, 'bold')).pack(pady=5)

        # File selection
        file_frame = ttk.LabelFrame(main, text="Data Files", padding=10)
        file_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.file_list = tk.Listbox(file_frame, selectmode=tk.EXTENDED)
        self.file_list.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        scroll = ttk.Scrollbar(file_frame, command=self.file_list.yview)
        scroll.pack(fill=tk.Y, side=tk.RIGHT)
        self.file_list.config(yscrollcommand=scroll.set)

        btn_frame = ttk.Frame(file_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="Add Files", command=self.add_files).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Add Folder", command=self.add_folder).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Clear", command=lambda: self.file_list.delete(0, tk.END)).pack(side=tk.LEFT, padx=2)

        # Options
        opt_frame = ttk.LabelFrame(main, text="Options", padding=10)
        opt_frame.pack(fill=tk.X, pady=5)

        # Format
        format_row = ttk.Frame(opt_frame)
        format_row.pack(fill=tk.X, pady=2)
        ttk.Label(format_row, text="Output Format:").pack(side=tk.LEFT)
        self.format_var = tk.StringVar(value='png')
        format_combo = ttk.Combobox(format_row, textvariable=self.format_var,
                    values=['png', 'pdf', 'svg', 'jpg', 'tiff'], state='readonly',
                    width=8)
        format_combo.pack(side=tk.LEFT, padx=5)

        # DPI
        ttk.Label(format_row, text="DPI:").pack(side=tk.LEFT, padx=(20,2))
        self.dpi_var = tk.IntVar(value=300)
        ttk.Spinbox(format_row, from_=72, to=1200, textvariable=self.dpi_var,
                   width=5).pack(side=tk.LEFT)

        # Output directory
        dir_row = ttk.Frame(opt_frame)
        dir_row.pack(fill=tk.X, pady=2)
        ttk.Label(dir_row, text="Output Directory:").pack(side=tk.LEFT)
        self.output_dir = tk.StringVar(value=str(Path.home() / "batch_plots"))
        ttk.Entry(dir_row, textvariable=self.output_dir, width=40).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(dir_row, text="Browse", command=self.select_output).pack(side=tk.LEFT)

        # Naming convention
        name_row = ttk.Frame(opt_frame)
        name_row.pack(fill=tk.X, pady=2)
        ttk.Label(name_row, text="File Naming:").pack(side=tk.LEFT)
        self.naming_var = tk.StringVar(value="{filename}_{plottype}_{date}")
        ttk.Combobox(name_row, textvariable=self.naming_var,
                    values=["{filename}_{plottype}", "{filename}_{date}",
                           "{filename}_{plottype}_{date}", "custom"],
                    width=25).pack(side=tk.LEFT, padx=5)

        # Template
        template_row = ttk.Frame(opt_frame)
        template_row.pack(fill=tk.X, pady=2)
        ttk.Label(template_row, text="Apply Template:").pack(side=tk.LEFT)
        self.apply_template = tk.BooleanVar(value=True)
        ttk.Checkbutton(template_row, variable=self.apply_template).pack(side=tk.LEFT)

        # Progress
        progress_frame = ttk.Frame(main)
        progress_frame.pack(fill=tk.X, pady=5)
        self.progress = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress.pack(fill=tk.X)

        self.status_label = ttk.Label(progress_frame, text="Ready")
        self.status_label.pack(pady=2)

        # Log
        log_frame = ttk.LabelFrame(main, text="Processing Log", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, font=('Courier', 8))
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Control buttons
        ctrl_frame = ttk.Frame(main)
        ctrl_frame.pack(fill=tk.X, pady=5)
        self.start_btn = ttk.Button(ctrl_frame, text="Start Batch", command=self.start_batch)
        self.start_btn.pack(side=tk.LEFT, padx=2)
        ttk.Button(ctrl_frame, text="Generate Report", command=self.generate_report).pack(side=tk.LEFT, padx=2)
        ttk.Button(ctrl_frame, text="Close", command=self.destroy).pack(side=tk.RIGHT, padx=2)

    def add_files(self):
        files = filedialog.askopenfilenames(
            title="Select Data Files",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx *.xls"),
                      ("All files", "*.*")]
        )
        for f in files:
            self.file_list.insert(tk.END, f)
        self.log(f"Added {len(files)} files")

    def add_folder(self):
        folder = filedialog.askdirectory(title="Select Folder")
        if folder:
            folder_path = Path(folder)
            for ext in ['*.csv', '*.xlsx', '*.xls']:
                for f in folder_path.glob(ext):
                    self.file_list.insert(tk.END, str(f))
            self.log(f"Added files from {folder}")

    def select_output(self):
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_dir.set(directory)

    def log(self, message):
        """Add message to log"""
        self.log_text.insert(tk.END, f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {message}\n")
        self.log_text.see(tk.END)
        self.update_idletasks()

    def start_batch(self):
        if self.running:
            return

        files = [self.file_list.get(i) for i in range(self.file_list.size())]
        if not files:
            messagebox.showwarning("No Files", "Please add files to process")
            return

        self.running = True
        self.start_btn.config(state='disabled')
        self.log(f"Starting batch processing of {len(files)} files")

        thread = threading.Thread(target=self._process_batch, args=(files,))
        thread.daemon = True
        thread.start()

    def _process_batch(self, files):
        """Process multiple files using current plotter settings"""
        output_dir = Path(self.output_dir.get())
        output_dir.mkdir(parents=True, exist_ok=True)

        plot_type = self.plotter.plot_type.get()
        template = self.plotter.template_name.get() if self.apply_template.get() else None
        dpi = self.dpi_var.get()
        column_mapping = self.plotter.column_mapping

        total = len(files)
        successful = 0
        failed = []

        for i, file_path in enumerate(files):
            try:
                self.status_label.config(text=f"Processing {i+1}/{total}: {Path(file_path).name}")
                self.progress['value'] = (i / total) * 100
                self.log(f"Processing: {Path(file_path).name}")

                if file_path.endswith('.csv'):
                    df = pd.read_csv(file_path)
                else:
                    df = pd.read_excel(file_path)

                samples = df.to_dict('records')

                with self._thread_lock:
                    temp_plotter = UltimatePlotter(None, samples, self.plotter.app)

                    temp_plotter.plot_type.set(plot_type)
                    if template:
                        temp_plotter.template_name.set(template)
                    temp_plotter.dpi.set(dpi)
                    temp_plotter.column_mapping = column_mapping

                    fig = temp_plotter.generate_figure_only()

                if fig:
                    # Generate filename
                    name_template = self.naming_var.get()
                    filename = Path(file_path).stem
                    date_str = datetime.datetime.now().strftime('%Y%m%d')

                    if "{filename}" in name_template:
                        out_name = name_template.replace("{filename}", filename)
                    else:
                        out_name = filename

                    if "{plottype}" in name_template:
                        out_name = out_name.replace("{plottype}", plot_type.replace(" ", "_"))

                    if "{date}" in name_template:
                        out_name = out_name.replace("{date}", date_str)

                    out_name = out_name.replace(" ", "_") + f".{self.format_var.get()}"
                    output_file = output_dir / out_name

                    with self._thread_lock:
                        fig.savefig(output_file, dpi=dpi, bbox_inches='tight')
                        plt.close(fig)

                    successful += 1
                    self.log(f"  ✓ Saved: {out_name}")

            except Exception as e:
                failed.append((Path(file_path).name, str(e)))
                self.log(f"  ✗ Error: {str(e)}")

        self.progress['value'] = 100
        self.status_label.config(text=f"Complete! {successful}/{total} files processed")

        if failed:
            self.log(f"\nFailed files ({len(failed)}):")
            for name, error in failed:
                self.log(f"  {name}: {error}")

        self.log(f"\nBatch processing complete. Files saved to: {output_dir}")
        self.running = False
        self.start_btn.config(state='normal')

        # Show summary
        messagebox.showinfo("Batch Complete",
                          f"Processing complete!\n"
                          f"✓ Successful: {successful}\n"
                          f"✗ Failed: {len(failed)}\n\n"
                          f"Output directory:\n{output_dir}")

    def generate_report(self):
        """Generate summary report of processed files"""
        files = [self.file_list.get(i) for i in range(self.file_list.size())]
        if not files:
            messagebox.showwarning("No Files", "No files to report")
            return

        report = f"""Batch Processing Report
Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Files to process: {len(files)}
Output format: {self.format_var.get()}
DPI: {self.dpi_var.get()}
Output directory: {self.output_dir.get()}

Files:
"""
        for f in files:
            report += f"  {Path(f).name}\n"

        # Save report
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"batch_report_{datetime.datetime.now().strftime('%Y%m%d')}.txt"
        )

        if filename:
            with open(filename, 'w') as f:
                f.write(report)
            messagebox.showinfo("Report Saved", f"Report saved to:\n{filename}")

# ============================================================================
# DIGITIZER TOOL (PRESERVED)
# ============================================================================

class DigitizerTool(tk.Toplevel):
    """Image digitizer for extracting data from plots"""
    # [EXACTLY AS YOUR ORIGINAL - PRESERVED]

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Plot Digitizer")
        self.geometry("800x600")
        self.transient(parent)

        self.image = None
        self.photo = None
        self.points = []
        self.calibration = {'x1': None, 'x2': None, 'y1': None, 'y2': None}
        self.mode = 'calibrate_x1'

        self._create_ui()

    def _create_ui(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, pady=2)

        ttk.Button(toolbar, text="Load Image", command=self.load_image).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Export Data", command=self.export_data).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Clear Points", command=self.clear_points).pack(side=tk.LEFT, padx=2)

        ttk.Label(toolbar, text="Mode:").pack(side=tk.LEFT, padx=(10,2))
        self.mode_var = tk.StringVar(value='calibrate_x1')
        modes = ['calibrate_x1', 'calibrate_x2', 'calibrate_y1', 'calibrate_y2', 'digitize']
        ttk.Combobox(toolbar, textvariable=self.mode_var, values=modes,
                    state='readonly', width=12).pack(side=tk.LEFT)

        self.canvas = tk.Canvas(self, bg='white', cursor='crosshair')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind('<Button-1>', self.on_click)

        self.status = ttk.Label(self, text="Load an image to begin")
        self.status.pack(fill=tk.X)

    def load_image(self):
        if not HAS_PIL:
            messagebox.showerror("Error", "PIL not available")
            return

        path = filedialog.askopenfilename(
            title="Select Plot Image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.gif *.bmp"), ("All files", "*.*")]
        )

        if not path:
            return

        try:
            self.image = Image.open(path)
            max_size = (800, 600)
            self.image.thumbnail(max_size, Image.Resampling.LANCZOS)

            self.photo = ImageTk.PhotoImage(self.image)
            self.canvas.config(width=self.image.width, height=self.image.height)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)

            self.status.config(text="Image loaded. Click to set calibration points.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {e}")

    def on_click(self, event):
        mode = self.mode_var.get()

        if mode.startswith('calibrate'):
            self.canvas.create_oval(event.x-3, event.y-3, event.x+3, event.y+3,
                                fill='red', outline='black')
            self.canvas.create_text(event.x, event.y-10, text=mode, fill='red')

            if mode == 'calibrate_x1':
                self.calibration['x1'] = (event.x, event.y)
                self.status.config(text="X1 set. Switch mode to calibrate_x2")
            elif mode == 'calibrate_x2':
                self.calibration['x2'] = (event.x, event.y)
                self.status.config(text="X2 set. Switch mode to calibrate_y1")
            elif mode == 'calibrate_y1':
                self.calibration['y1'] = (event.x, event.y)
                self.status.config(text="Y1 set. Switch mode to calibrate_y2")
            elif mode == 'calibrate_y2':
                self.calibration['y2'] = (event.x, event.y)
                self.status.config(text="Y2 set. Now enter real values")
                self.ask_calibration_values()

        elif mode == 'digitize':
            self.canvas.create_oval(event.x-2, event.y-2, event.x+2, event.y+2,
                                fill='blue', outline='black')
            self.canvas.create_text(event.x, event.y-5, text=str(len(self.points)+1),
                                fill='blue', font=('Arial', 8))
            self.points.append((event.x, event.y))
            self.status.config(text=f"Points: {len(self.points)}")

    def ask_calibration_values(self):
        dialog = tk.Toplevel(self)
        dialog.title("Calibration Values")
        dialog.geometry("300x200")
        dialog.transient(self)

        ttk.Label(dialog, text="Enter real-world values:",
                font=('Arial', 10, 'bold')).pack(pady=10)

        frame = ttk.Frame(dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="X1 value:").grid(row=0, column=0, pady=2)
        x1_entry = ttk.Entry(frame)
        x1_entry.grid(row=0, column=1, pady=2)
        x1_entry.insert(0, "0")

        ttk.Label(frame, text="X2 value:").grid(row=1, column=0, pady=2)
        x2_entry = ttk.Entry(frame)
        x2_entry.grid(row=1, column=1, pady=2)
        x2_entry.insert(0, "100")

        ttk.Label(frame, text="Y1 value:").grid(row=2, column=0, pady=2)
        y1_entry = ttk.Entry(frame)
        y1_entry.grid(row=2, column=1, pady=2)
        y1_entry.insert(0, "0")

        ttk.Label(frame, text="Y2 value:").grid(row=3, column=0, pady=2)
        y2_entry = ttk.Entry(frame)
        y2_entry.grid(row=3, column=1, pady=2)
        y2_entry.insert(0, "100")

        def save_calibration():
            try:
                self.calibration['x1_val'] = float(x1_entry.get())
                self.calibration['x2_val'] = float(x2_entry.get())
                self.calibration['y1_val'] = float(y1_entry.get())
                self.calibration['y2_val'] = float(y2_entry.get())

                x_pixel_dist = abs(self.calibration['x2'][0] - self.calibration['x1'][0])
                y_pixel_dist = abs(self.calibration['y2'][1] - self.calibration['y1'][1])

                if x_pixel_dist > 0:
                    self.calibration['x_scale'] = (self.calibration['x2_val'] - self.calibration['x1_val']) / x_pixel_dist
                if y_pixel_dist > 0:
                    self.calibration['y_scale'] = (self.calibration['y2_val'] - self.calibration['y1_val']) / y_pixel_dist

                self.status.config(text="Calibration complete! Switch to digitize mode")
                dialog.destroy()
            except:
                messagebox.showerror("Error", "Enter valid numbers")

        ttk.Button(dialog, text="Apply", command=save_calibration).pack(pady=10)

    def clear_points(self):
        self.points = []
        self.canvas.delete('all')
        if self.photo:
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        self.status.config(text="Points cleared")

    def export_data(self):
        if not self.points:
            messagebox.showwarning("No Data", "No points digitized")
            return

        if 'x_scale' not in self.calibration or 'y_scale' not in self.calibration:
            messagebox.showwarning("No Calibration",
                                "Please calibrate first:\n1. Set 4 calibration points\n2. Enter real values")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if path:
            try:
                ox, oy = self.calibration['x1']

                with open(path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['X_data', 'Y_data'])

                    for px, py in self.points:
                        data_x = (px - ox) * self.calibration['x_scale']
                        data_y = (oy - py) * self.calibration['y_scale']
                        writer.writerow([f"{data_x:.4f}", f"{data_y:.4f}"])

                messagebox.showinfo("Success", f"Exported {len(self.points)} points with real coordinates")
                self.status.config(text=f"Exported {len(self.points)} points")

            except Exception as e:
                messagebox.showerror("Error", f"Export failed: {e}")

# ============================================================================
# PROPERTY EDITOR (PRESERVED)
# ============================================================================

class PropertyEditor(tk.Toplevel):
    """Floating property editor for plot objects"""
    # [EXACTLY AS YOUR ORIGINAL - PRESERVED]

    def __init__(self, parent, callback):
        super().__init__(parent)
        self.title("Object Properties")
        self.geometry("350x500")
        self.transient(parent)
        self.callback = callback
        self.current_obj = None
        self.current_type = None
        self.current_color = 'black'

        self._create_ui()

    def _create_ui(self):
        main = ttk.Frame(self, padding=5)
        main.pack(fill=tk.BOTH, expand=True)

        self.type_label = ttk.Label(main, text="No object selected",
                                    font=('Arial', 10, 'bold'))
        self.type_label.pack(fill=tk.X, pady=2)

        ttk.Separator(main).pack(fill=tk.X, pady=5)

        self.notebook = ttk.Notebook(main)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.appearance_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.appearance_tab, text="Appearance")
        self._create_appearance_tab()

        self.line_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.line_tab, text="Line")
        self._create_line_tab()

        self.marker_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.marker_tab, text="Marker")
        self._create_marker_tab()

        self.text_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.text_tab, text="Text")
        self._create_text_tab()

        ttk.Button(main, text="Apply Changes", command=self._apply_changes).pack(pady=5)

    def _create_appearance_tab(self):
        color_frame = ttk.Frame(self.appearance_tab)
        color_frame.pack(fill=tk.X, pady=2)
        ttk.Label(color_frame, text="Color:").pack(side=tk.LEFT)
        self.color_btn = ttk.Button(color_frame, text="Pick Color",
                                    command=self._pick_color)
        self.color_btn.pack(side=tk.LEFT, padx=5)
        self.color_preview = tk.Canvas(color_frame, width=20, height=20, bg='black')
        self.color_preview.pack(side=tk.LEFT)

        alpha_frame = ttk.Frame(self.appearance_tab)
        alpha_frame.pack(fill=tk.X, pady=2)
        ttk.Label(alpha_frame, text="Opacity:").pack(side=tk.LEFT)
        self.alpha_var = tk.DoubleVar(value=1.0)
        ttk.Scale(alpha_frame, from_=0.0, to=1.0, variable=self.alpha_var,
                 orient=tk.HORIZONTAL).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        zorder_frame = ttk.Frame(self.appearance_tab)
        zorder_frame.pack(fill=tk.X, pady=2)
        ttk.Label(zorder_frame, text="Z-order:").pack(side=tk.LEFT)
        self.zorder_var = tk.IntVar(value=1)
        ttk.Spinbox(zorder_frame, from_=1, to=100, textvariable=self.zorder_var,
                   width=5).pack(side=tk.LEFT)

    def _create_line_tab(self):
        style_frame = ttk.Frame(self.line_tab)
        style_frame.pack(fill=tk.X, pady=2)
        ttk.Label(style_frame, text="Style:").pack(side=tk.LEFT)
        self.line_style_var = tk.StringVar(value='-')
        ttk.Combobox(style_frame, textvariable=self.line_style_var,
                    values=['-', '--', '-.', ':', 'None'], width=5).pack(side=tk.LEFT, padx=5)

        width_frame = ttk.Frame(self.line_tab)
        width_frame.pack(fill=tk.X, pady=2)
        ttk.Label(width_frame, text="Width:").pack(side=tk.LEFT)
        self.line_width_var = tk.DoubleVar(value=1.0)
        ttk.Spinbox(width_frame, from_=0.1, to=10.0, increment=0.1,
                textvariable=self.line_width_var, width=5).pack(side=tk.LEFT)

    def _create_marker_tab(self):
        style_frame = ttk.Frame(self.marker_tab)
        style_frame.pack(fill=tk.X, pady=2)
        ttk.Label(style_frame, text="Style:").pack(side=tk.LEFT)
        self.marker_style_var = tk.StringVar(value='o')
        ttk.Combobox(style_frame, textvariable=self.marker_style_var,
                    values=['o', 's', '^', 'D', 'v', '<', '>', 'p', '*', 'x', '+'],
                    width=5).pack(side=tk.LEFT, padx=5)

        size_frame = ttk.Frame(self.marker_tab)
        size_frame.pack(fill=tk.X, pady=2)
        ttk.Label(size_frame, text="Size:").pack(side=tk.LEFT)
        self.marker_size_var = tk.DoubleVar(value=6.0)
        ttk.Spinbox(size_frame, from_=1, to=20, textvariable=self.marker_size_var,
                width=5).pack(side=tk.LEFT)

    def _create_text_tab(self):
        size_frame = ttk.Frame(self.text_tab)
        size_frame.pack(fill=tk.X, pady=2)
        ttk.Label(size_frame, text="Size:").pack(side=tk.LEFT)
        self.font_size_var = tk.IntVar(value=10)
        ttk.Spinbox(size_frame, from_=6, to=24, textvariable=self.font_size_var,
                   width=5).pack(side=tk.LEFT)

        weight_frame = ttk.Frame(self.text_tab)
        weight_frame.pack(fill=tk.X, pady=2)
        ttk.Label(weight_frame, text="Weight:").pack(side=tk.LEFT)
        self.font_weight_var = tk.StringVar(value='normal')
        ttk.Combobox(weight_frame, textvariable=self.font_weight_var,
                    values=['normal', 'bold'], width=8).pack(side=tk.LEFT)

        rot_frame = ttk.Frame(self.text_tab)
        rot_frame.pack(fill=tk.X, pady=2)
        ttk.Label(rot_frame, text="Rotation:").pack(side=tk.LEFT)
        self.text_rotation_var = tk.IntVar(value=0)
        ttk.Spinbox(rot_frame, from_=-90, to=90, textvariable=self.text_rotation_var,
                   width=5).pack(side=tk.LEFT)

    def _pick_color(self):
        color = colorchooser.askcolor(initialcolor=self.current_color)[1]
        if color:
            self.current_color = color
            self.color_preview.config(bg=color)

    def set_object(self, obj, obj_type):
        self.current_obj = obj
        self.current_type = obj_type
        self.type_label.config(text=f"Selected: {obj_type}")

        if hasattr(obj, 'get_color'):
            self.current_color = obj.get_color()
        elif hasattr(obj, 'get_edgecolor'):
            self.current_color = obj.get_edgecolor()
        else:
            self.current_color = 'black'
        self.color_preview.config(bg=self.current_color)

    def _apply_changes(self):
        if self.current_obj is None:
            return

        if hasattr(self.current_obj, 'set_color'):
            self.current_obj.set_color(self.current_color)
        if hasattr(self.current_obj, 'set_alpha'):
            self.current_obj.set_alpha(self.alpha_var.get())
        if hasattr(self.current_obj, 'set_zorder'):
            self.current_obj.set_zorder(self.zorder_var.get())

        self.callback()

# ============================================================================
# MAIN PLOTTER CLASS - ENHANCED WITH ALL NEW FEATURES
# ============================================================================

class UltimatePlotter:
    """Professional scientific plotter with IUGS-IMA geochemical standards"""

    def __init__(self, frame, samples, app):
        self.frame = frame
        self.samples = samples
        self.app = app
        self.fig = None
        self.canvas = None
        self.toolbar = None
        self.property_editor = None
        self.edit_mode = False
        self.fitter = AdvancedPeakFitter()
        self.column_mapping = None
        self.batch_processor = None
        self.digitizer = None
        self.data_viewer = None
        self.afc_dialog = None

        # NEW: Mineral and ML visualization helpers
        self.mineral_plots = MineralPlots()
        self.afc_model = AFCModel()
        self.ml_viz = MLVisualization()
        self.coda_viz = CoDAVisualization()

        # Geochemical data manager
        self.geo_manager = GeochemicalDataManager(app)
        self.geo_manager.refresh_from_main()

        self.extra_frame = None
        self.plot_frame = None
        self.status = None
        self.template_combo = None
        self.plot_combo = None
        self.journal_combo = None
        self.dpi_spin = None
        self.edit_btn = None
        self.main = None

        self._is_generating = False
        self._settings_locked = False
        self._first_load = True

        self.tm = TemplateManager(app)

        self.plot_type = tk.StringVar(value="Multi-Panel Dashboard")
        self.template_name = tk.StringVar()
        self.journal = tk.StringVar(value="None")
        self.normalization = tk.StringVar(value="Chondrite (Sun & McDonough 1989)")
        self.dpi = tk.IntVar(value=300)
        self.n_peaks = tk.IntVar(value=3)
        self.peak_type = tk.StringVar(value="Gaussian")
        self.baseline_type = tk.StringVar(value="linear")
        self.max_samples_var = tk.IntVar(value=8)

        # NEW: Color map selection
        self.colormap = tk.StringVar(value="Viridis (Sequential)")

        # EXPANDED plot types including all new diagrams
        self.all_plot_types = [
            "Multi-Panel Dashboard",
            "Spider Diagram",
            "Binary Plot",
            "Ternary Diagram",
            "Multi-Peak Fitting",
            "--- IUGS-IMA Geochemical ---",
            "TAS Diagram (IUGS)",
            "AFM Diagram (Irvine)",
            "REE Spider (Chondrite)",
            "Multi-Element Spider (N-MORB)",
            "Pearce Nb-Y",
            "Pearce Ta-Yb",
            "Pearce Rb-Y+Nb",
            "Whalen A-type",
            "Harker Diagram",
            "--- Advanced Diagrams ---",
            "Meschede Zr/Y-Nb/Y",
            "Shervais V-Ti",
            "3D Ternary (REE)",
            "CIPW Norm Bars",
            "--- NEW v2.0 Diagrams ---",
            "Pyroxene Quadrilateral",
            "Feldspar Ternary (An-Ab-Or)",
            "Amphibole Classification",
            "Th/Yb vs Ta/Yb (Pearce 1983)",
            "La/Yb vs Th/Yb (Contamination)",
            "S'CK Granitoid Diagram",
            "AFC Model",
            "Binary Mixing Model",
            "Rayleigh Fractionation",
            "K-Means Clustering",
            "PCA Biplot",
            "Compositional Biplot (CLR)",
            "Balance Dendrogram"
        ]

        if HAS_SKLEARN:
            self.all_plot_types.extend(["K-Means Clustering", "PCA Biplot"])

        if HAS_COMPOSITIONAL:
            self.all_plot_types.extend(["Compositional Biplot (CLR)", "Balance Dendrogram"])

        # FIX: Get template names properly
        template_names = self.tm.get_template_names()
        if template_names:
            self.template_name.set(template_names[0])

    def create_ui(self):
        """Create the plotter interface with geochemical tools"""
        for widget in self.frame.winfo_children():
            widget.destroy()

        self.main = ttk.Frame(self.frame)
        self.main.pack(fill=tk.BOTH, expand=True)

        toolbar = ttk.Frame(self.main)
        toolbar.pack(fill=tk.X, pady=2)

        ttk.Label(toolbar, text="Plot:").pack(side=tk.LEFT)
        self.plot_combo = ttk.Combobox(toolbar, textvariable=self.plot_type,
                    values=self.all_plot_types,
                    state='readonly', width=25)
        self.plot_combo.pack(side=tk.LEFT, padx=2)
        self.plot_combo.bind('<<ComboboxSelected>>', self._on_plot_type_selected)

        ttk.Label(toolbar, text="Template:").pack(side=tk.LEFT, padx=(10,2))
        self.template_combo = ttk.Combobox(toolbar, textvariable=self.template_name,
                                        values=self.tm.get_template_names(),
                                        state='readonly', width=20)
        self.template_combo.pack(side=tk.LEFT, padx=2)
        self.template_combo.bind('<<ComboboxSelected>>', self._on_template_selected)

        ttk.Button(toolbar, text="📂 Import",
                  command=self.import_template).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="💾 Save",
                  command=self.save_current_as_template).pack(side=tk.LEFT, padx=2)

        # ENHANCED Tools menu
        tools_btn = ttk.Menubutton(toolbar, text="🔧 Tools")
        tools_btn.pack(side=tk.LEFT, padx=5)

        tools_menu = tk.Menu(tools_btn, tearoff=0)
        tools_btn.config(menu=tools_menu)

        # Geochemistry tools
        tools_menu.add_command(label="🧪 Geochemical Mapping",
                              command=self.open_geochemical_mapping)
        tools_menu.add_command(label="📊 View Indices",
                              command=self.open_data_viewer)
        tools_menu.add_separator()

        # NEW v2.0 tools
        tools_menu.add_command(label="📈 AFC Modeler (Interactive)",
                              command=self.open_afc_modeler)
        tools_menu.add_command(label="🧬 Mineral Calculator",
                              command=self.open_mineral_calculator)
        tools_menu.add_separator()

        # General tools
        tools_menu.add_command(label="📊 Column Selector", command=self.open_column_selector)
        tools_menu.add_command(label="🔄 Batch Processor", command=self.open_batch_processor)
        tools_menu.add_command(label="📐 Digitizer", command=self.open_digitizer)
        tools_menu.add_separator()
        tools_menu.add_command(label="📈 Peak Fitting Options", command=self.show_peak_options)
        tools_menu.add_command(label="🎨 Color Map", command=self.show_colormap_options)
        tools_menu.add_separator()
        tools_menu.add_command(label="📋 Export Settings", command=self.export_settings)
        tools_menu.add_command(label="📂 Import Settings", command=self.import_settings)

        ttk.Label(toolbar, text="Journal:").pack(side=tk.LEFT, padx=(10,2))
        self.journal_combo = ttk.Combobox(toolbar, textvariable=self.journal,
                    values=list(JOURNAL_SIZES.keys()),
                    state='readonly', width=15)
        self.journal_combo.pack(side=tk.LEFT, padx=2)
        self.journal_combo.bind('<<ComboboxSelected>>', lambda e: self.generate_plot())

        ttk.Label(toolbar, text="Norm:").pack(side=tk.LEFT, padx=(10,2))
        self.norm_combo = ttk.Combobox(toolbar, textvariable=self.normalization,
                    values=list(REE_NORMALIZATION.keys()),
                    state='readonly', width=18)
        self.norm_combo.pack(side=tk.LEFT, padx=2)
        self.norm_combo.bind('<<ComboboxSelected>>', lambda e: self.generate_plot())

        ttk.Label(toolbar, text="DPI:").pack(side=tk.LEFT, padx=(10,2))
        self.dpi_spin = ttk.Spinbox(toolbar, from_=72, to=1200, textvariable=self.dpi,
                   width=5)
        self.dpi_spin.pack(side=tk.LEFT)
        self.dpi_spin.bind('<Return>', lambda e: self.generate_plot())

        self.edit_btn = ttk.Checkbutton(toolbar, text="✎ Edit",
                                        command=self.toggle_edit_mode)
        self.edit_btn.pack(side=tk.LEFT, padx=10)

        ttk.Button(toolbar, text="🔄 Generate",
                  command=self.generate_plot).pack(side=tk.RIGHT, padx=2)
        ttk.Button(toolbar, text="💾 Export",
                  command=self.export_figure).pack(side=tk.RIGHT, padx=2)

        self.extra_frame = ttk.Frame(self.main)
        self.extra_frame.pack(fill=tk.X, pady=2)

        self.plot_frame = ttk.Frame(self.main, relief=tk.SUNKEN, borderwidth=1)
        self.plot_frame.pack(fill=tk.BOTH, expand=True)

        status_frame = ttk.Frame(self.main, relief=tk.SUNKEN)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.status = ttk.Label(status_frame, text="Ready - GeoPlot Pro v2.0")
        self.status.pack(side=tk.LEFT, padx=5)

        self.frame.update_idletasks()
        self.update_controls()
        self.frame.after(50, self._initial_generate)

    # ========================================================================
    # NEW: AFC Modeler Dialog
    # ========================================================================

    def open_afc_modeler(self):
        """Open interactive AFC modeler"""
        if not hasattr(self, 'afc_dialog') or not self.afc_dialog or not self.afc_dialog.winfo_exists():
            self.afc_dialog = AFCInteractiveDialog(self.frame.winfo_toplevel(), self)
        else:
            self.afc_dialog.lift()
        self.status.config(text="AFC Modeler opened")

    def open_mineral_calculator(self):
        """Open mineral formula calculator (simplified - just for plotting)"""
        # This would open a dialog to input mineral data
        # For now, just show a message
        messagebox.showinfo("Mineral Calculator",
                          "Mineral formula recalculation will be available in v2.1\n\n"
                          "For now, use the mineral classification plots with your data.")

    def show_colormap_options(self):
        """Show colormap selection dialog"""
        dialog = tk.Toplevel(self.frame.winfo_toplevel())
        dialog.title("Color Map Selection")
        dialog.geometry("300x400")
        dialog.transient(self.frame.winfo_toplevel())

        ttk.Label(dialog, text="Select Color Map",
                 font=('Arial', 10, 'bold')).pack(pady=10)

        # Color map list
        listbox = tk.Listbox(dialog, height=15)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        for cmap in SCIENTIFIC_CMAPS.keys():
            listbox.insert(tk.END, cmap)

        # Preview area
        preview_frame = ttk.Frame(dialog, height=50)
        preview_frame.pack(fill=tk.X, padx=10, pady=5)

        def on_select(event):
            if listbox.curselection():
                cmap_name = listbox.get(listbox.curselection()[0])
                self.colormap.set(cmap_name)
                # Draw preview
                preview_frame.delete("all")
                fig = Figure(figsize=(3, 0.5), dpi=100)
                ax = fig.add_subplot(111)
                gradient = np.linspace(0, 1, 256).reshape(1, -1)
                ax.imshow(gradient, aspect='auto', cmap=SCIENTIFIC_CMAPS[cmap_name])
                ax.set_xticks([])
                ax.set_yticks([])
                canvas = FigureCanvasTkAgg(fig, preview_frame)
                canvas.draw()
                canvas.get_tk_widget().pack()

        listbox.bind('<<ListboxSelect>>', on_select)

        ttk.Button(dialog, text="Apply",
                  command=lambda: [self.generate_plot(), dialog.destroy()]).pack(pady=10)

    # ========================================================================
    # NEW PLOT GENERATION METHODS
    # ========================================================================

    def generate_pyroxene_plot(self, ax):
        """Generate pyroxene quadrilateral"""
        df = self.geo_manager.df if not self.geo_manager.df.empty else pd.DataFrame()
        self.mineral_plots.plot_pyroxene_quadrilateral(ax, self.samples, df)

    def generate_feldspar_plot(self, ax):
        """Generate feldspar ternary"""
        df = self.geo_manager.df if not self.geo_manager.df.empty else pd.DataFrame()
        self.mineral_plots.plot_feldspar_ternary(ax, self.samples, df)

    def generate_amphibole_plot(self, ax):
        """Generate amphibole classification"""
        df = self.geo_manager.df if not self.geo_manager.df.empty else pd.DataFrame()
        self.mineral_plots.plot_amphibole_classification(ax, self.samples, df)

    def generate_th_yb_ta_yb(self, ax):
        """Generate Th/Yb vs Ta/Yb diagram (Pearce, 1983)"""
        df = self.geo_manager.df

        if df.empty:
            ax.text(0.5, 0.5, "No data", ha='center', va='center')
            return

        if 'Th_ppm' in df.columns and 'Yb_ppm' in df.columns and 'Ta_ppm' in df.columns:
            th_yb = df['Th_ppm'] / df['Yb_ppm'].replace(0, np.nan)
            ta_yb = df['Ta_ppm'] / df['Yb_ppm'].replace(0, np.nan)

            mask = (th_yb > 0) & (ta_yb > 0) & (~pd.isna(th_yb)) & (~pd.isna(ta_yb))

            if mask.sum() > 0:
                # Plot fields
                for field_name, field in TH_YB_TA_YB_FIELDS.items():
                    rect = Rectangle((field['Th_Yb'][0], field['Ta_Yb'][0]),
                                   field['Th_Yb'][1] - field['Th_Yb'][0],
                                   field['Ta_Yb'][1] - field['Ta_Yb'][0],
                                   alpha=0.1, color=field['color'], label=field_name)
                    ax.add_patch(rect)

                ax.scatter(th_yb[mask], ta_yb[mask], c='red', s=15, alpha=0.7,
                          edgecolors='black', linewidth=0.2, zorder=5)

                ax.set_xscale('log')
                ax.set_yscale('log')
                ax.set_xlabel('Th/Yb', fontsize=7)
                ax.set_ylabel('Ta/Yb', fontsize=7)
                ax.set_xlim(0.01, 10)
                ax.set_ylim(0.01, 10)
                ax.grid(True, alpha=0.2, which='both')
                ax.legend(loc='best', fontsize=5)
                ax.set_title('Th/Yb vs Ta/Yb (Pearce, 1983)', fontsize=8)
        else:
            ax.text(0.5, 0.5, "Map Th, Ta, Yb first", ha='center', va='center')

    def generate_la_yb_th_yb(self, ax):
        """Generate La/Yb vs Th/Yb contamination diagram"""
        df = self.geo_manager.df

        if df.empty:
            ax.text(0.5, 0.5, "No data", ha='center', va='center')
            return

        if 'La_ppm' in df.columns and 'Yb_ppm' in df.columns and 'Th_ppm' in df.columns:
            la_yb = df['La_ppm'] / df['Yb_ppm'].replace(0, np.nan)
            th_yb = df['Th_ppm'] / df['Yb_ppm'].replace(0, np.nan)

            mask = (la_yb > 0) & (th_yb > 0) & (~pd.isna(la_yb)) & (~pd.isna(th_yb))

            if mask.sum() > 0:
                # Plot fields
                for field_name, field in LA_YB_TH_YB_FIELDS.items():
                    rect = Rectangle((field['La_Yb'][0], field['Th_Yb'][0]),
                                   field['La_Yb'][1] - field['La_Yb'][0],
                                   field['Th_Yb'][1] - field['Th_Yb'][0],
                                   alpha=0.1, color=field['color'], label=field_name)
                    ax.add_patch(rect)

                ax.scatter(la_yb[mask], th_yb[mask], c='red', s=15, alpha=0.7,
                          edgecolors='black', linewidth=0.2, zorder=5)

                ax.set_xscale('log')
                ax.set_yscale('log')
                ax.set_xlabel('La/Yb', fontsize=7)
                ax.set_ylabel('Th/Yb', fontsize=7)
                ax.set_xlim(0.1, 100)
                ax.set_ylim(0.01, 10)
                ax.grid(True, alpha=0.2, which='both')
                ax.legend(loc='best', fontsize=5)
                ax.set_title('La/Yb vs Th/Yb (Crustal Contamination)', fontsize=8)
        else:
            ax.text(0.5, 0.5, "Map La, Th, Yb first", ha='center', va='center')

    def generate_sck_diagram(self, ax):
        """Generate S'CK diagram for granitoids"""
        df = self.geo_manager.df

        if df.empty:
            ax.text(0.5, 0.5, "No data", ha='center', va='center')
            return

        if all(c in df.columns for c in ['SiO2_wt', 'CaO_wt', 'K2O_wt']):
            sio2 = df['SiO2_wt'].values
            cao_k2o = df['CaO_wt'] / (df['CaO_wt'] + df['K2O_wt']).replace(0, np.nan)

            mask = ~(pd.isna(sio2) | pd.isna(cao_k2o) | (cao_k2o == 0))

            if mask.sum() > 0:
                # Plot fields
                for field_name, field in SCK_FIELDS.items():
                    rect = Rectangle((field['SiO2_prime'][0], field['CaO_CaO_K2O'][0]),
                                   field['SiO2_prime'][1] - field['SiO2_prime'][0],
                                   field['CaO_CaO_K2O'][1] - field['CaO_CaO_K2O'][0],
                                   alpha=0.1, color=field['color'], label=field_name)
                    ax.add_patch(rect)

                ax.scatter(sio2[mask], cao_k2o[mask], c='red', s=15, alpha=0.7,
                          edgecolors='black', linewidth=0.2, zorder=5)

                ax.set_xlabel("SiO₂' (wt%)", fontsize=7)
                ax.set_ylabel('CaO/(CaO+K₂O)', fontsize=7)
                ax.set_xlim(50, 80)
                ax.set_ylim(0, 1)
                ax.grid(True, alpha=0.2)
                ax.legend(loc='best', fontsize=5)
                ax.set_title("S'CK Granitoid Diagram", fontsize=8)
        else:
            ax.text(0.5, 0.5, "Map SiO2, CaO, K2O first", ha='center', va='center')

    def generate_afc_model_plot(self, ax):
        """Generate AFC model plot"""
        self.afc_model.plot_afc_curve(ax)

    def generate_mixing_model_plot(self, ax):
        """Generate binary mixing model plot"""
        df = self.geo_manager.df
        if self.column_mapping and self.column_mapping.get('x') and self.column_mapping.get('y'):
            self.afc_model.plot_mixing_curve(ax, self.samples, df,
                                            self.column_mapping['x'],
                                            self.column_mapping['y'])
        else:
            ax.text(0.5, 0.5, "Map X and Y columns first", ha='center', va='center')

    def generate_rayleigh_plot(self, ax):
        """Generate Rayleigh fractionation plot"""
        self.afc_model.plot_rayleigh_fractionation(ax)

    def generate_kmeans_plot(self, ax):
        """Generate K-means clustering plot"""
        df = self.geo_manager.df
        if self.column_mapping and self.column_mapping.get('x') and self.column_mapping.get('y'):
            self.ml_viz.plot_kmeans_clusters(ax, df,
                                            self.column_mapping['x'],
                                            self.column_mapping['y'])
        else:
            ax.text(0.5, 0.5, "Map X and Y columns first", ha='center', va='center')

    def generate_pca_biplot(self, ax):
        """Generate PCA biplot"""
        df = self.geo_manager.df
        self.ml_viz.plot_pca_biplot(ax, df)

    def generate_compositional_biplot(self, ax):
        """Generate compositional biplot"""
        df = self.geo_manager.df
        elements = REE_ORDER[:8]  # Use first 8 REE
        self.coda_viz.plot_compositional_biplot(ax, df, elements)

    def generate_balance_dendrogram(self, ax):
        """Generate balance dendrogram"""
        df = self.geo_manager.df
        elements = REE_ORDER[:8]  # Use first 8 REE
        self.coda_viz.plot_balance_dendrogram(ax, df, elements)

    # ========================================================================
    # ENHANCED EXPORT METHOD
    # ========================================================================

    def export_figure(self):
        """Enhanced export with vector formats and options"""
        if not hasattr(self, 'fig') or self.fig is None:
            messagebox.showwarning("No Figure", "Generate a plot first")
            return

        # Get current settings
        current_settings = {
            'dpi': self.dpi.get(),
            'journal': self.journal.get(),
            'plot_type': self.plot_type.get()
        }

        # Open enhanced export dialog
        dialog = ExportDialog(self.frame.winfo_toplevel(), self.fig, current_settings)
        self.wait_window(dialog)

        if hasattr(dialog, 'result_path') and dialog.result_path:
            self.status.config(text=f"✅ Exported to: {Path(dialog.result_path).name}")

    # ========================================================================
    # EXISTING METHODS (PRESERVED)
    # ========================================================================

    def open_geochemical_mapping(self):
        dialog = GeochemicalMappingDialog(
            self.frame.winfo_toplevel(),
            self.geo_manager,
            self.on_geochemical_mapping_applied
        )
        self.status.config(text="Geochemical mapping opened")

    def on_geochemical_mapping_applied(self, data_manager):
        self.geo_manager = data_manager
        self.status.config(text="✅ Geochemical mapping applied")
        if not self.geo_manager.df.empty:
            self.samples = self.geo_manager.df.to_dict('records')
        self.generate_plot()

    def open_data_viewer(self):
        if not hasattr(self, 'data_viewer') or not self.data_viewer or not self.data_viewer.winfo_exists():
            self.data_viewer = GeochemicalDataViewer(
                self.frame.winfo_toplevel(),
                self.geo_manager
            )
        else:
            self.data_viewer.lift()
            self.data_viewer._refresh_data()
        self.status.config(text="Data viewer opened")

    def generate_tas_diagram(self, ax):
        if self.geo_manager.df.empty:
            ax.text(0.5, 0.5, "No geochemical data", ha='center', va='center')
            return

        df = self.geo_manager.df

        if 'SiO2_wt' not in df.columns or 'Alkali' not in df.columns:
            ax.text(0.5, 0.5, "Map major elements first", ha='center', va='center')
            return

        for field_name, field in TAS_FIELDS.items():
            if field['type'] == 'volcanic':
                x1, x2 = field['SiO2']
                y1, y2 = field['alkali']
                polygon = Polygon([(x1, y1), (x2, y1), (x2, y2), (x1, y2)],
                                alpha=0.1, color=field['color'], linewidth=0)
                ax.add_patch(polygon)

                x_center = (x1 + x2) / 2
                y_center = (y1 + y2) / 2
                if y_center < 15:
                    ax.text(x_center, y_center, field_name, fontsize=5,
                           ha='center', va='center', alpha=0.6)

        x_line = np.linspace(45, 80, 50)
        y_line = 0.371 * x_line - 14.5
        ax.plot(x_line, y_line, 'k--', linewidth=0.8, label='Irvine', alpha=0.5)

        ax.scatter(df['SiO2_wt'], df['Alkali'],
                  c='red', s=15, alpha=0.7, edgecolors='black', linewidth=0.2, zorder=5)

        ax.set_xlim(35, 80)
        ax.set_ylim(0, 18)
        ax.set_xlabel('SiO₂ (wt%)', fontsize=7)
        ax.set_ylabel('Na₂O+K₂O (wt%)', fontsize=7)
        ax.grid(True, alpha=0.2)
        ax.tick_params(labelsize=6)

        if len(df) < 20 and 'Sample_ID' in df.columns:
            for idx, row in df.iterrows():
                ax.annotate(row['Sample_ID'][:4], (row['SiO2_wt'], row['Alkali']),
                           fontsize=4, xytext=(2,2), textcoords='offset points')

    def generate_afm_diagram(self, ax):
        if self.geo_manager.df.empty:
            ax.text(0.5, 0.5, "No geochemical data", ha='center', va='center')
            return

        df = self.geo_manager.df

        required = ['Na2O_wt', 'K2O_wt', 'FeO_star_wt', 'MgO_wt']
        if not all(col in df.columns for col in required):
            ax.text(0.5, 0.5, "Map major elements first", ha='center', va='center')
            return

        A = df['Na2O_wt'] + df['K2O_wt']
        F = df['FeO_star_wt']
        M = df['MgO_wt']
        total = A + F + M

        ax.scatter(F/total*100, M/total*100, c='blue', s=15, alpha=0.7,
                  edgecolors='black', linewidth=0.2, zorder=5)

        bx, by = zip(*AFM_BOUNDARY)
        ax.plot(bx, by, 'k--', linewidth=0.8, label='Tholeiitic - Calc-alkaline', alpha=0.5)

        ax.set_xlim(0, 100)
        ax.set_ylim(0, 100)
        ax.set_xlabel('F (FeO*)', fontsize=7)
        ax.set_ylabel('M (MgO)', fontsize=7)
        ax.grid(True, alpha=0.2)
        ax.tick_params(labelsize=6)

    def generate_ree_spider(self, ax):
        if self.geo_manager.df.empty:
            ax.text(0.5, 0.5, "No geochemical data", ha='center', va='center')
            return

        df = self.geo_manager.df

        ree_norm_cols = [f"{r}_N" for r in REE_ORDER if f"{r}_N" in df.columns]
        if not ree_norm_cols:
            ax.text(0.5, 0.5, "Map REE elements first", ha='center', va='center')
            return

        x = np.arange(len(REE_ORDER))
        n = min(self.max_samples_var.get(), len(df))
        colors = plt.cm.rainbow(np.linspace(0, 1, n))

        has_data = False
        for idx in range(n):
            values = []
            for r in REE_ORDER:
                col = f"{r}_N"
                if col in df.columns:
                    val = df[col].iloc[idx]
                    values.append(val if val > 0 else np.nan)
                else:
                    values.append(np.nan)

            if np.sum(~np.isnan(values)) > 5:
                sample_id = df.iloc[idx].get('Sample_ID', f'S{idx}')
                ax.semilogy(x, values, 'o-', color=colors[idx],
                           markersize=2, linewidth=0.5, alpha=0.7, label=sample_id[:6])
                has_data = True

        if has_data:
            ax.set_xticks(x)
            ax.set_xticklabels(REE_ORDER, rotation=45, fontsize=5)
            ax.set_ylabel('Sample/Chondrite', fontsize=7)
            ax.axhline(y=1, color='gray', linestyle='--', linewidth=0.3, alpha=0.5)
            ax.grid(True, alpha=0.2, which='both')
            ax.tick_params(labelsize=5)
            if n <= 6:
                ax.legend(loc='upper right', fontsize=5, ncol=2)
        else:
            ax.text(0.5, 0.5, "Insufficient REE data", ha='center', va='center')

    def generate_multi_spider(self, ax):
        if self.geo_manager.df.empty:
            ax.text(0.5, 0.5, "No geochemical data", ha='center', va='center')
            return

        df = self.geo_manager.df

        available = []
        for e in MULTI_ELEMENTS:
            col = f"{e}_N-MORB"
            if col in df.columns and df[col].sum() > 0:
                available.append(e)

        if not available:
            ax.text(0.5, 0.5, "Map trace elements first", ha='center', va='center')
            return

        x = np.arange(len(available))
        n = min(self.max_samples_var.get(), len(df))
        colors = plt.cm.Set2(np.linspace(0, 1, n))

        for idx in range(n):
            values = []
            for e in available:
                col = f"{e}_N-MORB"
                val = df[col].iloc[idx]
                values.append(val if val > 0 else np.nan)

            if np.sum(~np.isnan(values)) > 5:
                sample_id = df.iloc[idx].get('Sample_ID', f'S{idx}')
                ax.semilogy(x, values, 'o-', color=colors[idx],
                           markersize=2, linewidth=0.5, alpha=0.7, label=sample_id[:6])

        ax.set_xticks(x)
        ax.set_xticklabels(available, rotation=90, fontsize=4)
        ax.set_ylabel('Sample/N-MORB', fontsize=7)
        ax.axhline(y=1, color='gray', linestyle='--', linewidth=0.3, alpha=0.5)
        ax.grid(True, alpha=0.2, which='both')
        ax.tick_params(labelsize=5)

    def generate_pearce_nb_y(self, ax):
        if self.geo_manager.df.empty:
            ax.text(0.5, 0.5, "No geochemical data", ha='center', va='center')
            return

        df = self.geo_manager.df

        if 'Nb_ppm' in df.columns and 'Y_ppm' in df.columns:
            nb = df['Nb_ppm']
            y = df['Y_ppm']
            mask = (y > 0) & (nb > 0) & (~pd.isna(y)) & (~pd.isna(nb))

            if mask.sum() > 0:
                ax.axvspan(0, 65, 0, 1, alpha=0.15, color='#87CEEB', label='VAG+COLG')
                ax.axvspan(65, 1000, 0, 1, alpha=0.15, color='#FFB6C1', label='WPG')

                ax.scatter(y[mask], nb[mask], c='red', s=15, alpha=0.7,
                          edgecolors='black', linewidth=0.2, zorder=5)

                ax.set_xscale('log')
                ax.set_yscale('log')
                ax.set_xlabel('Y (ppm)', fontsize=7)
                ax.set_ylabel('Nb (ppm)', fontsize=7)
                ax.set_xlim(0.5, 200)
                ax.set_ylim(0.1, 1000)
                ax.grid(True, alpha=0.2, which='both')
                ax.tick_params(labelsize=6)
                ax.legend(loc='lower right', fontsize=5)

                ax.text(10, 0.5, 'VAG+COLG', fontsize=5, alpha=0.5)
                ax.text(100, 100, 'WPG', fontsize=5, alpha=0.5)
        else:
            ax.text(0.5, 0.5, "Map Nb and Y first", ha='center', va='center')

    def generate_pearce_ta_yb(self, ax):
        if self.geo_manager.df.empty:
            ax.text(0.5, 0.5, "No geochemical data", ha='center', va='center')
            return

        df = self.geo_manager.df

        if 'Ta_ppm' in df.columns and 'Yb_ppm' in df.columns:
            ta = df['Ta_ppm']
            yb = df['Yb_ppm']
            mask = (yb > 0) & (ta > 0) & (~pd.isna(yb)) & (~pd.isna(ta))

            if mask.sum() > 0:
                ax.axvspan(0, 2.5, 0, 1, alpha=0.15, color='#87CEEB', label='VAG+COLG')
                ax.axvspan(2.5, 100, 0, 1, alpha=0.15, color='#FFB6C1', label='WPG')

                ax.scatter(yb[mask], ta[mask], c='blue', s=15, alpha=0.7,
                          edgecolors='black', linewidth=0.2, zorder=5)

                ax.set_xscale('log')
                ax.set_yscale('log')
                ax.set_xlabel('Yb (ppm)', fontsize=7)
                ax.set_ylabel('Ta (ppm)', fontsize=7)
                ax.set_xlim(0.1, 50)
                ax.set_ylim(0.01, 10)
                ax.grid(True, alpha=0.2, which='both')
                ax.tick_params(labelsize=6)
                ax.legend(loc='lower right', fontsize=5)
        else:
            ax.text(0.5, 0.5, "Map Ta and Yb first", ha='center', va='center')

    def generate_pearce_rb_y_nb(self, ax):
        if self.geo_manager.df.empty:
            ax.text(0.5, 0.5, "No geochemical data", ha='center', va='center')
            return

        df = self.geo_manager.df

        if all(e in df.columns for e in ['Rb_ppm', 'Y_ppm', 'Nb_ppm']):
            rb = df['Rb_ppm']
            y_nb = df['Y_ppm'] + df['Nb_ppm']
            mask = (y_nb > 0) & (rb > 0) & (~pd.isna(y_nb)) & (~pd.isna(rb))

            if mask.sum() > 0:
                ax.axvspan(0, 55, 0, 550, alpha=0.15, color='#87CEEB', label='VAG')
                ax.axvspan(55, 550, 0, 550, alpha=0.15, color='#F4A460', label='syn-COLG')
                ax.axvspan(550, 2000, 0, 550, alpha=0.15, color='#FFB6C1', label='WPG')

                ax.scatter(y_nb[mask], rb[mask], c='green', s=15, alpha=0.7,
                          edgecolors='black', linewidth=0.2, zorder=5)

                ax.set_xscale('log')
                ax.set_yscale('log')
                ax.set_xlabel('Y+Nb (ppm)', fontsize=7)
                ax.set_ylabel('Rb (ppm)', fontsize=7)
                ax.set_xlim(1, 2000)
                ax.set_ylim(1, 1000)
                ax.grid(True, alpha=0.2, which='both')
                ax.tick_params(labelsize=6)
                ax.legend(loc='lower right', fontsize=5)
        else:
            ax.text(0.5, 0.5, "Map Rb, Y, Nb first", ha='center', va='center')

    def generate_whalen_diagram(self, ax):
        if self.geo_manager.df.empty:
            ax.text(0.5, 0.5, "No geochemical data", ha='center', va='center')
            return

        df = self.geo_manager.df

        if 'Zr+Nb+Ce+Y' in df.columns and 'FeO_MgO' in df.columns:
            z = df['Zr+Nb+Ce+Y']
            f = df['FeO_MgO']
            mask = (z > 0) & (f > 0) & (~pd.isna(z)) & (~pd.isna(f))

            if mask.sum() > 0:
                ax.axvspan(0, 350, 0, 10, alpha=0.15, color='#B0C4DE', label='I&S-type')
                ax.axvspan(350, 2000, 10, 100, alpha=0.15, color='#FFA07A', label='A-type')
                ax.axhline(y=10, color='black', linestyle='--', linewidth=0.5, alpha=0.3)
                ax.axvline(x=350, color='black', linestyle='--', linewidth=0.5, alpha=0.3)

                if 'Granite_Type' in df.columns:
                    colors = np.where(df['Granite_Type'] == 'A-type', '#FFA07A', '#B0C4DE')
                else:
                    colors = ['#B0C4DE'] * len(z)

                ax.scatter(z[mask], f[mask], c=colors[mask], s=15, alpha=0.7,
                          edgecolors='black', linewidth=0.2, zorder=5)

                ax.set_xscale('log')
                ax.set_yscale('log')
                ax.set_xlabel('Zr+Nb+Ce+Y (ppm)', fontsize=7)
                ax.set_ylabel('FeO*/MgO', fontsize=7)
                ax.set_xlim(10, 2000)
                ax.set_ylim(0.1, 100)
                ax.grid(True, alpha=0.2, which='both')
                ax.tick_params(labelsize=6)
                ax.legend(loc='upper left', fontsize=5)
        else:
            ax.text(0.5, 0.5, "Insufficient trace elements", ha='center', va='center')

    def generate_harker_diagram(self, ax):
        if self.geo_manager.df.empty:
            ax.text(0.5, 0.5, "No geochemical data", ha='center', va='center')
            return

        df = self.geo_manager.df

        if 'SiO2_wt' in df.columns and 'MgO_wt' in df.columns:
            sio2 = df['SiO2_wt']
            mgo = df['MgO_wt']
            mask = ~(sio2.isna() | mgo.isna() | (sio2 == 0))

            if mask.sum() > 0:
                ax.scatter(sio2[mask], mgo[mask], c='green', s=15, alpha=0.7,
                          edgecolors='black', linewidth=0.2, zorder=5)

                if mask.sum() > 1:
                    z = np.polyfit(sio2[mask], mgo[mask], 1)
                    p = np.poly1d(z)
                    x_trend = np.linspace(sio2[mask].min(), sio2[mask].max(), 50)
                    ax.plot(x_trend, p(x_trend), "r--", alpha=0.6, linewidth=0.8)

                ax.set_xlabel('SiO₂ (wt%)', fontsize=7)
                ax.set_ylabel('MgO (wt%)', fontsize=7)
                ax.grid(True, alpha=0.2)
                ax.tick_params(labelsize=6)
        else:
            ax.text(0.5, 0.5, "Map SiO2 and MgO first", ha='center', va='center')

    def generate_meschede_diagram(self, ax):
        if self.geo_manager.df.empty:
            ax.text(0.5, 0.5, "No geochemical data", ha='center', va='center')
            return

        df = self.geo_manager.df

        if all(e in df.columns for e in ['Zr_Y', 'Nb_Y_meschede']):
            zr_y = df['Zr_Y']
            nb_y = df['Nb_Y_meschede']
            mask = (zr_y > 0) & (nb_y > 0) & (~pd.isna(zr_y)) & (~pd.isna(nb_y))

            if mask.sum() > 0:
                for field_name, field in MESCHEDE_FIELDS.items():
                    if field_name == "WPA":
                        x = [0, 10, 10, 0.6/0.1*10, 0]
                        y = [0.6, 0.6, 2.0, 2.0, 0.6]
                    elif field_name == "WPT":
                        x = [2, 10, 10, 0.6/0.1*2, 2]
                        y = [0.1, 0.1, 0.6, 0.6, 0.1]
                    elif field_name == "VAB":
                        x = [0, 4, 4, 0, 0]
                        y = [0, 0, 0.4, 0.4, 0]
                    elif field_name == "N-MORB":
                        x = [0, 4, 4, 0, 0]
                        y = [0, 0, 0.1, 0.1, 0]
                    elif field_name == "E-MORB":
                        x = [4, 10, 10, 4, 4]
                        y = [0, 0, 0.1, 0.1, 0]

                    polygon = Polygon(list(zip(x, y)), alpha=0.15,
                                    color=field['color'], label=field['name'])
                    ax.add_patch(polygon)

                ax.scatter(zr_y[mask], nb_y[mask], c='red', s=15, alpha=0.7,
                          edgecolors='black', linewidth=0.2, zorder=5)

                ax.set_xscale('log')
                ax.set_yscale('log')
                ax.set_xlabel('Zr/Y', fontsize=7)
                ax.set_ylabel('Nb/Y', fontsize=7)
                ax.set_xlim(0.1, 20)
                ax.set_ylim(0.01, 5)
                ax.grid(True, alpha=0.2, which='both')
                ax.tick_params(labelsize=6)
                ax.legend(loc='best', fontsize=5)
        else:
            ax.text(0.5, 0.5, "Map Zr, Nb, Y first", ha='center', va='center')

    def generate_shervais_diagram(self, ax):
        if self.geo_manager.df.empty:
            ax.text(0.5, 0.5, "No geochemical data", ha='center', va='center')
            return

        df = self.geo_manager.df

        if all(e in df.columns for e in ['V_ppm', 'Ti_ppm']):
            v = df['V_ppm']
            ti = df['Ti_ppm']
            mask = (v > 0) & (ti > 0) & (~pd.isna(v)) & (~pd.isna(ti))

            if mask.sum() > 0:
                ti_v_ratios = [10, 20, 50, 100]
                for ratio in ti_v_ratios:
                    x_line = np.linspace(10, 1000, 50)
                    y_line = ratio * x_line
                    ax.plot(x_line, y_line, 'k--', alpha=0.2, linewidth=0.3)
                    ax.text(800, ratio*800, f'Ti/V={ratio}', fontsize=4, alpha=0.5)

                for field_name, field in SHERVAIS_FIELDS.items():
                    rect = Rectangle((field['V'][0], field['Ti'][0]),
                                   field['V'][1] - field['V'][0],
                                   field['Ti'][1] - field['Ti'][0],
                                   alpha=0.1, color=field['color'], label=field_name)
                    ax.add_patch(rect)

                ax.scatter(v[mask], ti[mask], c='blue', s=15, alpha=0.7,
                          edgecolors='black', linewidth=0.2, zorder=5)

                ax.set_xscale('log')
                ax.set_yscale('log')
                ax.set_xlabel('V (ppm)', fontsize=7)
                ax.set_ylabel('Ti (ppm)', fontsize=7)
                ax.set_xlim(10, 1000)
                ax.set_ylim(100, 100000)
                ax.grid(True, alpha=0.2, which='both')
                ax.tick_params(labelsize=6)
                ax.legend(loc='best', fontsize=5)
        else:
            ax.text(0.5, 0.5, "Map V and Ti first", ha='center', va='center')

    def generate_3d_ternary(self, ax):
        """Generate 3D ternary diagram for REE"""
        if self.geo_manager.df.empty:
            # For 3D axes, need z coordinate even for text
            ax.text(0.5, 0.5, 0.5, "No geochemical data", ha='center', va='center')
            return

        df = self.geo_manager.df

        if all(e in df.columns for e in ['La_N', 'Sm_N', 'Yb_N']):
            la = df['La_N'].fillna(0).values
            sm = df['Sm_N'].fillna(0).values
            yb = df['Yb_N'].fillna(0).values

            total = la + sm + yb
            mask = total > 0
            la_norm = la[mask] / total[mask]
            sm_norm = sm[mask] / total[mask]
            yb_norm = yb[mask] / total[mask]

            if 'Eu_Eu*' in df.columns:
                height = df['Eu_Eu*'].fillna(0).values[mask]
            else:
                height = np.ones_like(la_norm)

            # Convert to 3D coordinates
            x = 0.5 * (2*sm_norm + yb_norm) / (la_norm + sm_norm + yb_norm + 1e-10)
            y = np.sqrt(3)/2 * yb_norm / (la_norm + sm_norm + yb_norm + 1e-10)
            z = height

            # Create 3D scatter
            scatter = ax.scatter(x, y, z, c=z, s=30, alpha=0.7, cmap='viridis', edgecolors='black', linewidth=0.5)

            # Draw ternary base at z=0
            ax.plot([0, 1, 0.5, 0], [0, 0, np.sqrt(3)/2, 0], [0, 0, 0, 0], 'k-', alpha=0.3, linewidth=1)

            # Add colorbar
            cbar = self.fig.colorbar(scatter, ax=ax, shrink=0.5, aspect=10)
            cbar.set_label('Eu/Eu*', fontsize=8)

            ax.set_xlabel('La', fontsize=8, labelpad=10)
            ax.set_ylabel('Sm', fontsize=8, labelpad=10)
            ax.set_zlabel('Eu/Eu*', fontsize=8, labelpad=10)
            ax.set_title('3D REE Ternary (La-Sm-Yb)', fontsize=10, fontweight='bold')

            # Set better viewing angle
            ax.view_init(elev=25, azim=45)

            # Remove tick labels for cleaner look (optional)
            ax.set_xticklabels([])
            ax.set_yticklabels([])

        else:
            # Check which elements are missing
            missing = []
            if 'La_N' not in df.columns:
                missing.append('La')
            if 'Sm_N' not in df.columns:
                missing.append('Sm')
            if 'Yb_N' not in df.columns:
                missing.append('Yb')

            ax.text(0.5, 0.5, 0.5, f"Map {', '.join(missing)} first",
                    ha='center', va='center', fontsize=10)

    def generate_cipw_bars(self, ax):
        if self.geo_manager.df.empty:
            ax.text(0.5, 0.5, "No geochemical data", ha='center', va='center')
            return

        df = self.geo_manager.df

        cipw_cols = [c for c in df.columns if c.startswith('CIPW_')]
        if not cipw_cols:
            ax.text(0.5, 0.5, "Calculate CIPW norms first", ha='center', va='center')
            return

        n_samples = min(5, len(df))
        x = np.arange(len(cipw_cols))
        width = 0.15

        for i in range(n_samples):
            values = [df[col].iloc[i] for col in cipw_cols]
            ax.bar(x + i*width, values, width, label=f'Sample {i+1}', alpha=0.7)

        ax.set_xlabel('Mineral', fontsize=7)
        ax.set_ylabel('Normative %', fontsize=7)
        ax.set_xticks(x + width * (n_samples-1)/2)
        ax.set_xticklabels([c.replace('CIPW_', '') for c in cipw_cols], rotation=45, fontsize=5)
        ax.legend(fontsize=5)
        ax.set_title('CIPW Normative Minerals', fontsize=8)
        ax.grid(True, alpha=0.2, axis='y')

    # ========================================================================
    # ORIGINAL PLOT GENERATION METHODS (PRESERVED)
    # ========================================================================

    def save_current_as_template(self):
        from tkinter import simpledialog

        name = simpledialog.askstring("Template Name",
                                    "Enter name for this style:",
                                    parent=self.frame.winfo_toplevel())
        if not name:
            return

        if not hasattr(self, 'fig') or not self.fig.axes:
            messagebox.showwarning("No Plot", "Generate a plot first")
            return

        ax = self.fig.axes[0]

        template = {
            "name": name,
            "description": f"User-saved template from {datetime.datetime.now().strftime('%Y-%m-%d')}",
            "axes": {
                "direction": ax.xaxis._major_tick_kw.get('direction', 'in'),
                "mirror": True,
                "spine_width": ax.spines['bottom'].get_linewidth(),
                "spine_color": '#000000',
                "major_tick_len": ax.xaxis._major_tick_kw.get('length', 5)
            },
            "grid": {
                "enabled": ax.xaxis._gridOnMajor,
                "style": '--' if ax.xaxis.get_gridlines() and ax.xaxis.get_gridlines()[0].get_linestyle() == '--' else '-',
                "color": '#cccccc',
                "alpha": 0.3
            },
            "fonts": {
                "family": 'Arial',
                "label_size": ax.xaxis.label.get_size() if ax.xaxis.label else 10,
                "tick_size": ax.xaxis.get_ticklabels()[0].get_size() if ax.xaxis.get_ticklabels() else 9,
                "weight": 'normal'
            }
        }

        filename = name.replace(' ', '_').replace('(', '').replace(')', '')
        path = self.tm.template_dir / f"{filename}.json"

        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump({filename: template}, f, indent=2)

            self.tm.load_templates()
            self.template_combo['values'] = self.tm.get_template_names()
            self.template_name.set(name)

            messagebox.showinfo("Success", f"Template '{name}' saved!\n{path}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save template: {e}")

    def _initial_generate(self):
        if self._first_load:
            self._first_load = False
            self.generate_plot()

    def _on_plot_type_selected(self, event=None):
        if self._is_generating:
            return
        print(f"📊 Plot type selected: {self.plot_type.get()}")
        self.update_controls()
        self.generate_plot()

    def _on_template_selected(self, event=None):
        if self._is_generating:
            return
        print(f"📋 Template selected: {self.template_name.get()}")
        self.generate_plot()

    def update_controls(self):
        if not hasattr(self, 'extra_frame') or self.extra_frame is None:
            return

        print(f"🔄 Updating controls for: {self.plot_type.get()}")

        for widget in self.extra_frame.winfo_children():
            widget.destroy()

        if self.plot_type.get() == "Multi-Peak Fitting" and HAS_SCIPY:
            ttk.Label(self.extra_frame, text="Peaks:").pack(side=tk.LEFT, padx=2)
            peaks_spin = ttk.Spinbox(self.extra_frame, from_=1, to=10,
                    textvariable=self.n_peaks, width=3)
            peaks_spin.pack(side=tk.LEFT)
            peaks_spin.bind('<Return>', lambda e: self.generate_plot())

            ttk.Label(self.extra_frame, text="Type:").pack(side=tk.LEFT, padx=(10,2))
            peak_combo = ttk.Combobox(self.extra_frame, textvariable=self.peak_type,
                        values=['Gaussian', 'Lorentzian', 'Voigt'],
                        width=10, state='readonly')
            peak_combo.pack(side=tk.LEFT)
            peak_combo.bind('<<ComboboxSelected>>', lambda e: self.generate_plot())

            ttk.Label(self.extra_frame, text="Baseline:").pack(side=tk.LEFT, padx=(10,2))
            baseline_combo = ttk.Combobox(self.extra_frame, textvariable=self.baseline_type,
                        values=AdvancedPeakFitter.BASELINE_TYPES,
                        width=10, state='readonly')
            baseline_combo.pack(side=tk.LEFT)
            baseline_combo.bind('<<ComboboxSelected>>', lambda e: self.generate_plot())

        elif self.plot_type.get() in ["REE Spider (Chondrite)", "Multi-Element Spider (N-MORB)"]:
            ttk.Label(self.extra_frame, text="Max Samples:").pack(side=tk.LEFT, padx=2)
            samples_spin = ttk.Spinbox(self.extra_frame, from_=1, to=20,
                                      textvariable=self.max_samples_var, width=3)
            samples_spin.pack(side=tk.LEFT)
            samples_spin.bind('<Return>', lambda e: self.generate_plot())

        elif self.plot_type.get() in ["K-Means Clustering", "PCA Biplot"]:
            ttk.Label(self.extra_frame, text="Requires X/Y mapping").pack(side=tk.LEFT, padx=5)

    def generate_plot(self):
        if not HAS_MPL:
            return

        if self._is_generating:
            print("⏭️ Already generating, skipping...")
            return

        if not hasattr(self, 'plot_frame') or self.plot_frame is None:
            return

        self._is_generating = True

        current_plot_type = self.plot_type.get()
        current_template = self.template_name.get()
        current_journal = self.journal.get()
        current_dpi = self.dpi.get()
        current_n_peaks = self.n_peaks.get()
        current_peak_type = self.peak_type.get()
        current_baseline = self.baseline_type.get()
        current_normalization = self.normalization.get()

        original_load = self.tm.load_templates
        self.tm.load_templates = lambda: None

        try:
            if not self.frame.winfo_exists() or not self.plot_frame.winfo_exists():
                self._is_generating = False
                return
        except:
            self._is_generating = False
            return

        try:
            for widget in self.plot_frame.winfo_children():
                widget.destroy()
        except:
            pass

        self.geo_manager.refresh_from_main()
        if not self.geo_manager.df.empty:
            self.samples = self.geo_manager.df.to_dict('records')

        self.create_figure()

        try:
            # Map plot types to generation methods
            plot_methods = {
                "Spider Diagram": self.generate_spider,
                "Ternary Diagram": self.generate_ternary,
                "Binary Plot": self.generate_binary,
                "Multi-Peak Fitting": self.generate_peak_fitting,
                "TAS Diagram (IUGS)": lambda: self.generate_tas_diagram(self.fig.axes[0]),
                "AFM Diagram (Irvine)": lambda: self.generate_afm_diagram(self.fig.axes[0]),
                "REE Spider (Chondrite)": lambda: self.generate_ree_spider(self.fig.axes[0]),
                "Multi-Element Spider (N-MORB)": lambda: self.generate_multi_spider(self.fig.axes[0]),
                "Pearce Nb-Y": lambda: self.generate_pearce_nb_y(self.fig.axes[0]),
                "Pearce Ta-Yb": lambda: self.generate_pearce_ta_yb(self.fig.axes[0]),
                "Pearce Rb-Y+Nb": lambda: self.generate_pearce_rb_y_nb(self.fig.axes[0]),
                "Whalen A-type": lambda: self.generate_whalen_diagram(self.fig.axes[0]),
                "Harker Diagram": lambda: self.generate_harker_diagram(self.fig.axes[0]),
                "Meschede Zr/Y-Nb/Y": lambda: self.generate_meschede_diagram(self.fig.axes[0]),
                "Shervais V-Ti": lambda: self.generate_shervais_diagram(self.fig.axes[0]),
                "3D Ternary (REE)": lambda: self.generate_3d_ternary(self.fig.add_subplot(111, projection='3d')),
                "CIPW Norm Bars": lambda: self.generate_cipw_bars(self.fig.axes[0]),
                # NEW v2.0 methods
                "Pyroxene Quadrilateral": lambda: self.generate_pyroxene_plot(self.fig.axes[0]),
                "Feldspar Ternary (An-Ab-Or)": lambda: self.generate_feldspar_plot(self.fig.axes[0]),
                "Amphibole Classification": lambda: self.generate_amphibole_plot(self.fig.axes[0]),
                "Th/Yb vs Ta/Yb (Pearce 1983)": lambda: self.generate_th_yb_ta_yb(self.fig.axes[0]),
                "La/Yb vs Th/Yb (Contamination)": lambda: self.generate_la_yb_th_yb(self.fig.axes[0]),
                "S'CK Granitoid Diagram": lambda: self.generate_sck_diagram(self.fig.axes[0]),
                "AFC Model": lambda: self.generate_afc_model_plot(self.fig.axes[0]),
                "Binary Mixing Model": lambda: self.generate_mixing_model_plot(self.fig.axes[0]),
                "Rayleigh Fractionation": lambda: self.generate_rayleigh_plot(self.fig.axes[0]),
                "K-Means Clustering": lambda: self.generate_kmeans_plot(self.fig.axes[0]),
                "PCA Biplot": lambda: self.generate_pca_biplot(self.fig.axes[0]),
                "Compositional Biplot (CLR)": lambda: self.generate_compositional_biplot(self.fig.axes[0]),
                "Balance Dendrogram": lambda: self.generate_balance_dendrogram(self.fig.axes[0])
            }

            if current_plot_type in plot_methods:
                if current_plot_type in ["Spider Diagram", "Ternary Diagram", "Binary Plot", "Multi-Peak Fitting"]:
                    ax = self.fig.add_subplot(111)
                    if current_template:
                        ax = self.tm.apply_style(ax, current_template)
                    plot_methods[current_plot_type]()
                else:
                    # For methods that create their own axes
                    if current_plot_type == "3D Ternary (REE)":
                        # Special case for 3D
                        ax = self.fig.add_subplot(111, projection='3d')
                        if current_template:
                            ax = self.tm.apply_style(ax, current_template)
                        self.generate_3d_ternary(ax)
                    else:
                        ax = self.fig.add_subplot(111)
                        if current_template:
                            ax = self.tm.apply_style(ax, current_template)
                        plot_methods[current_plot_type]()

                    # Set title for the plot
                    ax.set_title(current_plot_type, fontsize=10, fontweight='bold')
            else:
                self.generate_multipanel()

            self.fig.tight_layout()

            self.canvas = FigureCanvasTkAgg(self.fig, self.plot_frame)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            toolbar_frame = ttk.Frame(self.plot_frame)
            toolbar_frame.pack(fill=tk.X, before=self.canvas.get_tk_widget())
            toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
            toolbar.update()

            if hasattr(self, 'status') and self.status:
                template_display = current_template or "default"
                self.status.config(text=f"✅ Generated: {current_plot_type} with template: {template_display}")

        except Exception as e:
            print(f"Error generating plot: {e}")
            import traceback
            traceback.print_exc()
            if not isinstance(e, (tk.TclError, AttributeError)):
                messagebox.showerror("Error", f"Failed to generate plot: {e}")
        finally:
            self._is_generating = False

    def generate_figure_only(self):
        if not HAS_MPL:
            return None

        self.create_figure()
        plot_type = self.plot_type.get()

        try:
            plot_methods = {
                "Spider Diagram": self.generate_spider,
                "Ternary Diagram": self.generate_ternary,
                "Binary Plot": self.generate_binary,
                "Multi-Peak Fitting": self.generate_peak_fitting,
                "TAS Diagram (IUGS)": lambda: self.generate_tas_diagram(self.fig.axes[0]),
                "AFM Diagram (Irvine)": lambda: self.generate_afm_diagram(self.fig.axes[0]),
                "REE Spider (Chondrite)": lambda: self.generate_ree_spider(self.fig.axes[0]),
                "Multi-Element Spider (N-MORB)": lambda: self.generate_multi_spider(self.fig.axes[0]),
                "Pearce Nb-Y": lambda: self.generate_pearce_nb_y(self.fig.axes[0]),
                "Pearce Ta-Yb": lambda: self.generate_pearce_ta_yb(self.fig.axes[0]),
                "Pearce Rb-Y+Nb": lambda: self.generate_pearce_rb_y_nb(self.fig.axes[0]),
                "Whalen A-type": lambda: self.generate_whalen_diagram(self.fig.axes[0]),
                "Harker Diagram": lambda: self.generate_harker_diagram(self.fig.axes[0]),
                "Meschede Zr/Y-Nb/Y": lambda: self.generate_meschede_diagram(self.fig.axes[0]),
                "Shervais V-Ti": lambda: self.generate_shervais_diagram(self.fig.axes[0]),
                "3D Ternary (REE)": lambda: self.generate_3d_ternary(self.fig.add_subplot(111, projection='3d')),
                "CIPW Norm Bars": lambda: self.generate_cipw_bars(self.fig.axes[0]),
                "Pyroxene Quadrilateral": lambda: self.generate_pyroxene_plot(self.fig.axes[0]),
                "Feldspar Ternary (An-Ab-Or)": lambda: self.generate_feldspar_plot(self.fig.axes[0]),
                "Amphibole Classification": lambda: self.generate_amphibole_plot(self.fig.axes[0]),
                "Th/Yb vs Ta/Yb (Pearce 1983)": lambda: self.generate_th_yb_ta_yb(self.fig.axes[0]),
                "La/Yb vs Th/Yb (Contamination)": lambda: self.generate_la_yb_th_yb(self.fig.axes[0]),
                "S'CK Granitoid Diagram": lambda: self.generate_sck_diagram(self.fig.axes[0]),
                "AFC Model": lambda: self.generate_afc_model_plot(self.fig.axes[0]),
                "Binary Mixing Model": lambda: self.generate_mixing_model_plot(self.fig.axes[0]),
                "Rayleigh Fractionation": lambda: self.generate_rayleigh_plot(self.fig.axes[0]),
                "K-Means Clustering": lambda: self.generate_kmeans_plot(self.fig.axes[0]),
                "PCA Biplot": lambda: self.generate_pca_biplot(self.fig.axes[0]),
                "Compositional Biplot (CLR)": lambda: self.generate_compositional_biplot(self.fig.axes[0]),
                "Balance Dendrogram": lambda: self.generate_balance_dendrogram(self.fig.axes[0])
            }

            if plot_type in plot_methods:
                if plot_type in ["Spider Diagram", "Ternary Diagram", "Binary Plot", "Multi-Peak Fitting"]:
                    ax = self.fig.add_subplot(111)
                    plot_methods[plot_type]()
                elif plot_type == "3D Ternary (REE)":
                    ax = self.fig.add_subplot(111, projection='3d')
                    self.generate_3d_ternary(ax)
                else:
                    ax = self.fig.add_subplot(111)
                    plot_methods[plot_type]()
            else:
                self.generate_multipanel()

            self.fig.tight_layout()
            return self.fig
        except Exception as e:
            print(f"Error in batch: {e}")
            return None

    def create_figure(self):
        size = JOURNAL_SIZES.get(self.journal.get(), (8, 6))

        try:
            if hasattr(self, 'plot_frame') and self.plot_frame.winfo_exists():
                plot_width = self.plot_frame.winfo_width()
                plot_height = self.plot_frame.winfo_height()

                if plot_width > 100 and plot_height > 100:
                    screen_dpi = 100
                    max_width = plot_width / screen_dpi
                    max_height = (plot_height - 60) / screen_dpi

                    if max_width > 3 and max_height > 2:
                        fig_aspect = size[0] / size[1]

                        if max_width / fig_aspect <= max_height:
                            new_width = max_width
                            new_height = new_width / fig_aspect
                        else:
                            new_height = max_height
                            new_width = new_height * fig_aspect

                        size = (new_width, new_height)

        except Exception as e:
            print(f"⚠️ Error sizing figure: {e}")

        self.fig = plt.figure(figsize=size, dpi=100)
        self.export_dpi = self.dpi.get()
        return self.fig

    def add_panel_label(self, ax, label):
        ax.text(0.02, 0.98, label, transform=ax.transAxes,
               fontsize=12, fontweight='bold', va='top', ha='left')

    def generate_spider(self):
        norm_name = self.normalization.get()
        if norm_name not in REE_NORMALIZATION:
            norm_name = "Chondrite (Sun & McDonough 1989)"
        norm = REE_NORMALIZATION[norm_name]

        ax = self.fig.add_subplot(111)
        if self.template_name.get():
            ax = self.tm.apply_style(ax, self.template_name.get())

        ax.set_xticks(range(len(REE_ORDER)))
        ax.set_xticklabels(REE_ORDER, rotation=90)
        ax.set_xlim(-0.5, len(REE_ORDER)-0.5)
        ax.set_yscale('log')
        ax.set_ylim(0.1, 1000)

        ax.axhline(y=1, color='gray', linestyle='--', alpha=0.3, linewidth=0.5)

        ax.set_xlabel("Element")
        ax.set_ylabel("Sample/Chondrite")
        ax.set_title("REE Spider Diagram")

        colors = plt.cm.tab10(np.linspace(0, 1, min(10, len(self.samples))))

        for i, sample in enumerate(self.samples[:10]):
            values = []
            valid = True

            for elem in REE_ORDER:
                val = None
                for col in [elem, f"{elem}_ppm", elem.lower()]:
                    if col in sample:
                        try:
                            v = float(sample[col])
                            if v > 0:
                                val = v
                                break
                        except:
                            pass

                if val is None:
                    valid = False
                    break
                values.append(val / norm[elem])

            if valid and values:
                ax.plot(range(len(REE_ORDER)), values,
                       marker='o', linestyle='-', linewidth=1.5,
                       markersize=5, color=colors[i % len(colors)], alpha=0.7,
                       label=sample.get('Sample_ID', f'Sample {i}')[:8],
                       picker=True)

        if len(ax.get_legend_handles_labels()[0]) > 0:
            ax.legend(fontsize=8, loc='best')

    def generate_ternary(self):
        ax = self.fig.add_subplot(111)
        if self.template_name.get():
            ax = self.tm.apply_style(ax, self.template_name.get())

        a_col = self.column_mapping.get('x') if self.column_mapping else None
        b_col = self.column_mapping.get('y') if self.column_mapping else None
        c_col = self.column_mapping.get('z') if self.column_mapping else None

        ax.plot([0, 1], [0, 0], 'k-', linewidth=2)
        ax.plot([0, 0.5], [0, np.sqrt(3)/2], 'k-', linewidth=2)
        ax.plot([1, 0.5], [0, np.sqrt(3)/2], 'k-', linewidth=2)

        ax.text(0.5, -0.08, f"{b_col or 'B'}",
                ha='center', fontsize=11, fontweight='bold')
        ax.text(-0.08, 0, f"{a_col or 'A'}",
                ha='right', va='center', fontsize=11, fontweight='bold')
        ax.text(1.08, 0, f"{c_col or 'C'}",
                ha='left', va='center', fontsize=11, fontweight='bold')

        for i in range(1, 5):
            p = i * 0.2
            ax.plot([p/2, 1-p/2], [p*np.sqrt(3)/2, p*np.sqrt(3)/2],
                'gray', linestyle='--', alpha=0.3, linewidth=0.5)

        for sample in self.samples:
            try:
                if a_col and b_col and c_col:
                    a = float(sample.get(a_col, 0))
                    b = float(sample.get(b_col, 0))
                    c = float(sample.get(c_col, 0))
                else:
                    numeric = [v for k,v in sample.items()
                            if k not in ['Sample_ID', 'Notes'] and isinstance(v, (int, float))]
                    if len(numeric) >= 3:
                        a, b, c = numeric[0], numeric[1], numeric[2]
                    else:
                        continue

                total = a + b + c
                if total > 0:
                    x = b/total + 0.5 * (c/total)
                    y = (np.sqrt(3)/2) * (c/total)
                    ax.scatter(x, y, s=50, alpha=0.7, picker=True)
            except:
                continue

        ax.set_xlim(-0.1, 1.1)
        ax.set_ylim(-0.1, np.sqrt(3)/2 + 0.1)
        ax.set_aspect('equal')
        ax.axis('off')

    def generate_binary(self):
        ax = self.fig.add_subplot(111)
        if self.template_name.get():
            ax = self.tm.apply_style(ax, self.template_name.get())

        x_col = self.column_mapping.get('x') if self.column_mapping else None
        y_col = self.column_mapping.get('y') if self.column_mapping else None
        err_col = self.column_mapping.get('error') if self.column_mapping else None

        x_vals, y_vals, err_vals = [], [], []

        for sample in self.samples:
            try:
                if x_col and y_col:
                    x = float(sample.get(x_col, 0))
                    y = float(sample.get(y_col, 0))
                    x_vals.append(x)
                    y_vals.append(y)

                    if err_col:
                        try:
                            err = float(sample.get(err_col, 0))
                            err_vals.append(err)
                        except:
                            err_vals.append(0)
                    else:
                        err_vals.append(0)
            except:
                continue

        if x_vals and y_vals:
            x = np.array(x_vals)
            y = np.array(y_vals)
            err = np.array(err_vals)

            if np.any(err > 0):
                ax.errorbar(x, y, yerr=err, fmt='o', capsize=3,
                        ecolor='gray', elinewidth=1.2, alpha=0.7,
                        markersize=6, picker=True)
            else:
                ax.scatter(x, y, s=50, alpha=0.7, picker=True)

            if HAS_SCIPY and len(x) > 2:
                z = np.polyfit(x, y, 1)
                p = np.poly1d(z)
                x_line = np.linspace(min(x), max(x), 100)
                ax.plot(x_line, p(x_line), 'r-', linewidth=2,
                    label=f'R² = {np.corrcoef(x, y)[0,1]**2:.3f}')
                ax.legend()

        ax.set_xlabel(x_col or "X")
        ax.set_ylabel(y_col or "Y")
        ax.set_title("Binary Plot")

    def generate_peak_fitting(self):
        ax = self.fig.add_subplot(111)
        if self.template_name.get():
            ax = self.tm.apply_style(ax, self.template_name.get())

        x = None
        y = None
        x_col = "X"
        y_col = "Intensity"

        if self.column_mapping and self.column_mapping.get('x') and self.column_mapping.get('y'):
            x_col = self.column_mapping['x']
            y_col = self.column_mapping['y']

            x_vals = []
            y_vals = []
            for s in self.samples:
                try:
                    if x_col in s and y_col in s:
                        x_val = float(s[x_col])
                        y_val = float(s[y_col])
                        x_vals.append(x_val)
                        y_vals.append(y_val)
                except (ValueError, TypeError):
                    continue

            if len(x_vals) > 5:
                x = np.array(x_vals)
                y = np.array(y_vals)
                sort_idx = np.argsort(x)
                x = x[sort_idx]
                y = y[sort_idx]

        if x is None:
            x = np.linspace(0, 10, 200)
            y = np.zeros_like(x)
            centers = [2, 5, 8]
            for i, center in enumerate(centers[:self.n_peaks.get()]):
                amp = 5 - i
                y += amp * np.exp(-(x - center)**2 / 0.5)
            y += np.random.normal(0, 0.2, len(x))
            self.status.config(text="⚠️ Using synthetic data - map X/Y columns first")
        else:
            self.status.config(text=f"✅ Fitting {len(x)} data points")

        result = self.fitter.fit_peaks(x, y, self.n_peaks.get(),
                                    self.peak_type.get(),
                                    self.baseline_type.get())

        ax.scatter(x, y, s=10, alpha=0.5, label='Data', picker=True)

        if result:
            ax.plot(x, result['fitted'], 'r-', linewidth=2, label='Fit')
            ax.plot(x, result['baseline'], 'g--', linewidth=1, label='Baseline')
            for i, indiv in enumerate(result['individuals']):
                ax.plot(x, indiv, '--', alpha=0.5, label=f'Peak {i+1}')

            stats_text = (f"R² = {result['r_squared']:.4f}\n"
                        f"Adj R² = {result['adj_r_squared']:.4f}\n"
                        f"AIC = {result['aic']:.1f}")
            ax.text(0.05, 0.95, stats_text, transform=ax.transAxes,
                fontsize=8, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        ax.set_title(f"{self.peak_type.get()} Peak Fitting")
        ax.legend(fontsize=8)

    def generate_multipanel(self):
        gs = GridSpec(2, 2, figure=self.fig, hspace=0.3, wspace=0.3)

        ax1 = self.fig.add_subplot(gs[0, 0])
        if self.template_name.get():
            ax1 = self.tm.apply_style(ax1, self.template_name.get())
        self.add_panel_label(ax1, 'a')
        ax1.plot([1,2,3,4], [1,4,2,3], 'o-')
        ax1.set_xlabel("X1")
        ax1.set_ylabel("Y1")
        ax1.set_title("Panel A")

        ax2 = self.fig.add_subplot(gs[0, 1])
        if self.template_name.get():
            ax2 = self.tm.apply_style(ax2, self.template_name.get())
        self.add_panel_label(ax2, 'b')
        ax2.plot([1,2,3,4], [3,2,4,1], 's-')
        ax2.set_xlabel("X2")
        ax2.set_ylabel("Y2")
        ax2.set_title("Panel B")

        ax3 = self.fig.add_subplot(gs[1, 0])
        if self.template_name.get():
            ax3 = self.tm.apply_style(ax3, self.template_name.get())
        self.add_panel_label(ax3, 'c')
        ax3.plot([1,2,3,4], [2,3,1,4], '^-')
        ax3.set_xlabel("X3")
        ax3.set_ylabel("Y3")
        ax3.set_title("Panel C")

        ax4 = self.fig.add_subplot(gs[1, 1])
        if self.template_name.get():
            ax4 = self.tm.apply_style(ax4, self.template_name.get())
        self.add_panel_label(ax4, 'd')
        ax4.plot([1,2,3,4], [4,1,3,2], 'd-')
        ax4.set_xlabel("X4")
        ax4.set_ylabel("Y4")
        ax4.set_title("Panel D")

        self.fig.suptitle("Multi-Panel Figure", fontsize=14, fontweight='bold', y=0.98)

    def import_template(self):
        new_template = self.tm.import_template()
        if new_template:
            self.template_combo['values'] = self.tm.get_template_names()
            self.template_name.set(new_template)
            self.generate_plot()

    def open_column_selector(self):
        if hasattr(self.app, 'get_current_samples'):
            samples = self.app.get_current_samples()
        elif hasattr(self.app, 'data_manager') and hasattr(self.app.data_manager, 'get_current_data'):
            samples = self.app.data_manager.get_current_data()
        else:
            samples = self.samples

        if not samples:
            messagebox.showwarning("No Data", "No data loaded in main app")
            return

        ColumnSelector(self.frame.winfo_toplevel(), samples, self.set_column_mapping)
        self.status.config(text="Column selector opened")

    def set_column_mapping(self, mapping):
        self.column_mapping = mapping
        self.status.config(text=f"Columns mapped: X={mapping['x']}, Y={mapping['y']}" +
                        (f", Error={mapping['error']}" if mapping.get('error') else ""))
        self.generate_plot()

    def open_batch_processor(self):
        if not hasattr(self, 'batch_processor') or not self.batch_processor or not self.batch_processor.winfo_exists():
            self.batch_processor = BatchProcessor(self.frame.winfo_toplevel(), self)
        else:
            self.batch_processor.lift()
        self.status.config(text="Batch processor opened")

    def open_digitizer(self):
        if not hasattr(self, 'digitizer') or not self.digitizer or not self.digitizer.winfo_exists():
            self.digitizer = DigitizerTool(self.frame.winfo_toplevel())
        else:
            self.digitizer.lift()
        self.status.config(text="Digitizer opened")

    def show_peak_options(self):
        dialog = tk.Toplevel(self.frame.winfo_toplevel())
        dialog.title("Peak Fitting Options")
        dialog.geometry("300x200")
        dialog.transient(self.frame.winfo_toplevel())

        ttk.Label(dialog, text="Advanced Peak Fitting Options",
                 font=('Arial', 10, 'bold')).pack(pady=10)

        ttk.Label(dialog, text="Number of peaks:").pack()
        ttk.Spinbox(dialog, from_=1, to=10, textvariable=self.n_peaks,
                   width=5).pack()

        ttk.Label(dialog, text="Peak type:").pack(pady=(10,0))
        ttk.Combobox(dialog, textvariable=self.peak_type,
                    values=['Gaussian', 'Lorentzian'],
                    state='readonly', width=12).pack()

        ttk.Label(dialog, text="Baseline type:").pack(pady=(10,0))
        ttk.Combobox(dialog, textvariable=self.baseline_type,
                    values=AdvancedPeakFitter.BASELINE_TYPES,
                    state='readonly', width=12).pack()

        ttk.Button(dialog, text="Apply", command=lambda: [self.generate_plot(), dialog.destroy()]).pack(pady=10)

    def export_settings(self):
        settings = {
            'plot_type': self.plot_type.get(),
            'template': self.template_name.get(),
            'journal': self.journal.get(),
            'dpi': self.dpi.get(),
            'normalization': self.normalization.get(),
            'n_peaks': self.n_peaks.get(),
            'peak_type': self.peak_type.get(),
            'baseline_type': self.baseline_type.get(),
            'colormap': self.colormap.get()
        }

        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if path:
            with open(path, 'w') as f:
                json.dump(settings, f, indent=2)
            messagebox.showinfo("Success", "Settings exported successfully")

    def import_settings(self):
        path = filedialog.askopenfilename(
            title="Import Settings",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if not path:
            return

        try:
            with open(path, 'r') as f:
                settings = json.load(f)

            if 'plot_type' in settings:
                self.plot_type.set(settings['plot_type'])
            if 'template' in settings:
                self.template_name.set(settings['template'])
            if 'journal' in settings:
                self.journal.set(settings['journal'])
            if 'dpi' in settings:
                self.dpi.set(settings['dpi'])
            if 'normalization' in settings:
                self.normalization.set(settings['normalization'])
            if 'n_peaks' in settings:
                self.n_peaks.set(settings['n_peaks'])
            if 'peak_type' in settings:
                self.peak_type.set(settings['peak_type'])
            if 'baseline_type' in settings:
                self.baseline_type.set(settings['baseline_type'])
            if 'colormap' in settings:
                self.colormap.set(settings['colormap'])

            self.update_controls()
            self.generate_plot()
            messagebox.showinfo("Success", "Settings imported successfully")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to import settings: {e}")

    def toggle_edit_mode(self):
        self.edit_mode = not self.edit_mode

        if self.edit_mode:
            if self.canvas:
                self.canvas.mpl_connect('pick_event', self.on_pick)
                self.status.config(text="Edit mode ON - Click objects to edit")

                if not self.property_editor:
                    self.property_editor = PropertyEditor(self.frame.winfo_toplevel(),
                                                         self.on_property_change)
        else:
            self.status.config(text="Edit mode OFF")

    def on_pick(self, event):
        if not self.edit_mode or not self.property_editor:
            return

        obj = event.artist
        obj_type = type(obj).__name__

        self.property_editor.set_object(obj, obj_type)
        self.property_editor.lift()

    def on_property_change(self):
        if self.canvas:
            self.canvas.draw_idle()

# ============================================================================
# GEOCHEMICAL DATA VIEWER (PRESERVED)
# ============================================================================

class GeochemicalDataViewer(tk.Toplevel):
    """View calculated geochemical indices"""
    # [EXACTLY AS YOUR ORIGINAL - PRESERVED]

    def __init__(self, parent, data_manager):
        super().__init__(parent)
        self.title("Geochemical Indices")
        self.geometry("1000x600")
        self.transient(parent)
        self.data_manager = data_manager

        self._create_ui()
        self._update_table()

    def _create_ui(self):
        main = ttk.Frame(self, padding=5)
        main.pack(fill=tk.BOTH, expand=True)

        toolbar = ttk.Frame(main)
        toolbar.pack(fill=tk.X, pady=2)

        ttk.Button(toolbar, text="🔄 Refresh",
                  command=self._refresh_data).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📊 Export",
                  command=self._export_data).pack(side=tk.LEFT, padx=2)

        ttk.Label(toolbar, text="Show:").pack(side=tk.LEFT, padx=(20,2))
        self.view_var = tk.StringVar(value="All Indices")
        view_combo = ttk.Combobox(toolbar, textvariable=self.view_var,
                    values=["All Indices", "Major Elements", "REE Indices",
                           "Trace Elements", "Tectonic Discriminants", "CIPW Norms"],
                    state='readonly', width=15)
        view_combo.pack(side=tk.LEFT)
        view_combo.bind('<<ComboboxSelected>>', lambda e: self._update_table())

        tree_frame = ttk.Frame(main)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        vsb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        hsb = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)

        self.tree = ttk.Treeview(tree_frame,
                                 yscrollcommand=vsb.set,
                                 xscrollcommand=hsb.set,
                                 selectmode='extended')

        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)

        self.tree.grid(row=0, column=0, sticky=tk.NSEW)
        vsb.grid(row=0, column=1, sticky=tk.NS)
        hsb.grid(row=1, column=0, sticky=tk.EW)

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        self.status = ttk.Label(main, text="", relief=tk.SUNKEN)
        self.status.pack(fill=tk.X, side=tk.BOTTOM)

    def _refresh_data(self):
        self.data_manager.refresh_from_main()
        self.data_manager.calculate_all_indices(force=True)
        self._update_table()

    def _update_table(self, *args):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if self.data_manager.df.empty:
            self.status.config(text="No data available")
            return

        df = self.data_manager.df

        view = self.view_var.get()
        if view == "Major Elements":
            cols = [c for c in df.columns if any(m in c for m in
                    ["_wt", "Alkali", "ASI", "Mg#", "MALI"])]
        elif view == "REE Indices":
            cols = [c for c in df.columns if any(r in c for r in
                    REE_ORDER + ["_N", "Eu", "Ce", "LaN"])]
        elif view == "Trace Elements":
            cols = [c for c in df.columns if any(t in c for t in
                    MULTI_ELEMENTS + ["_ppm"]) and "_N" not in c]
        elif view == "Tectonic Discriminants":
            cols = [c for c in df.columns if any(d in c for d in
                    ["Nb_Y", "Ta_Yb", "Rb_Y+Nb", "Granite_Type", "NbY_Tectonic",
                     "Zr_Y", "Nb_Y_meschede", "Ti_V"])]
        elif view == "CIPW Norms":
            cols = [c for c in df.columns if c.startswith("CIPW_")]
        else:
            original = self.data_manager.get_column_list()
            cols = [c for c in df.columns if c not in original]

        cols = cols[:20]

        if not cols:
            self.tree["columns"] = []
            self.tree["show"] = "tree"
            self.tree.insert("", tk.END, text="No calculated indices available")
            self.status.config(text="No indices for current view")
            return

        self.tree["columns"] = cols
        self.tree["show"] = "headings"

        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor=tk.CENTER)

        for idx, row in df.head(50).iterrows():
            values = []
            for col in cols:
                val = row.get(col, "")
                if isinstance(val, float):
                    if abs(val) < 0.01 or abs(val) > 1000:
                        values.append(f"{val:.2e}")
                    else:
                        values.append(f"{val:.2f}")
                else:
                    values.append(str(val)[:15])

            self.tree.insert("", tk.END, values=values)

        self.status.config(text=f"Showing {len(cols)} indices for {min(50, len(df))} samples")

    def _export_data(self):
        if self.data_manager.df.empty:
            messagebox.showwarning("No Data", "No data to export")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("Excel", "*.xlsx")],
            initialfile=f"geochemical_data_{datetime.datetime.now().strftime('%Y%m%d')}.csv"
        )

        if filename:
            try:
                if filename.endswith('.csv'):
                    self.data_manager.df.to_csv(filename, index=False)
                else:
                    self.data_manager.df.to_excel(filename, index=False)
                messagebox.showinfo("Export Complete", f"Data exported to:\n{filename}")
            except Exception as e:
                messagebox.showerror("Export Failed", str(e))

# ============================================================================
# PLOTTER FUNCTION
# ============================================================================

def plot_publication(frame, samples):
    """Main entry point - IMMEDIATELY creates the UI"""
    if not HAS_MPL:
        label = tk.Label(frame, text="❌ matplotlib not installed!\nPlease install: pip install matplotlib scipy pillow pandas openpyxl",
                        font=('Arial', 12), fg='red')
        label.pack(expand=True)
        return None

    for widget in frame.winfo_children():
        widget.destroy()

    app = None
    widget = frame
    while widget:
        if hasattr(widget, 'app'):
            app = widget.app
            break
        if hasattr(widget, 'master'):
            widget = widget.master
        else:
            break

    if app is None and hasattr(frame, 'winfo_toplevel'):
        top = frame.winfo_toplevel()
        if hasattr(top, 'app'):
            app = top.app

    plotter = UltimatePlotter(frame, samples, app)
    plotter.create_ui()
    return plotter

# ============================================================================
# EXPORT
# ============================================================================

PLOT_TYPES = {
    "GeoPlot Pro": plot_publication
}
