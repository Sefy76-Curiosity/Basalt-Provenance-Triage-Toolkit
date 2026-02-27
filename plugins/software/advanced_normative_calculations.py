"""
Advanced Normative Calculations Plugin v5.0
Professional-grade implementation of ALL major normative systems.
New in v5: Vol% (density-based), Ternary diagrams, Pie charts, bug fixes, compact UI.
"""

PLUGIN_INFO = {
    "category": "software", "menu": "Advanced",
    "field": "Petrology & Mineralogy",
    "id": "advanced_normative_calculations",
    "name": "Professional Normative Calculator",
    "description": "All industry-standard normative methods: CIPW, Hutchison, Niggli, Mesonorm, Catanorm, Rittmann",
    "icon": "⚖️", "version": "5.1",
    "requires": ["pandas", "numpy", "scipy", "matplotlib"],
    "author": "Sefy Levy"
}

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import numpy as np
import json
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional

try:
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.patches import FancyArrowPatch
    import matplotlib.tri as tri
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

# ============================================================================
# ENUMS
# ============================================================================

class NormSystem(Enum):
    CIPW_STANDARD       = "CIPW Standard (Cross et al. 1903)"
    CIPW_MATRIX         = "CIPW Matrix Algebra (Pandey 2009)"
    HUTCHISON           = "Hutchison Norm (1974/1975)"
    HUTCHISON_BIOTITE   = "Hutchison with Biotite"
    NIGGLI_CATANORM     = "Niggli Catanorm (1936)"
    BARTH_NIGGLI        = "Barth-Niggli Catanorm (1952)"
    MESONORM            = "Mesonorm (Winkler 1979)"
    MESONORM_GRANITE    = "Granite Mesonorm (Parslow 1969)"
    EPINORM             = "Epinorm (Barth 1959)"
    RITTMANN            = "Rittmann Norm (1973)"
    RITTMANN_VOLCANIC   = "Rittmann Volcanic Facies"
    SINCLAS             = "SINCLAS Method (Verma et al. 2002)"
    CATANORM_METAMORPHIC= "Catanorm for Metamorphic (Barth 1959)"

class MetamorphicFacies(Enum):
    GRANULITE   = "Granulite Facies"
    AMPHIBOLITE = "Amphibolite Facies"
    GREENSCHIST = "Greenschist Facies"
    ECLOGITE    = "Eclogite Facies"

# ============================================================================
# MINERAL DATABASE
# ============================================================================

@dataclass
class Mineral:
    name: str
    formula: str
    mw: float
    density: float          # g/cm³ for Vol% calculation
    category: str
    systems: List[NormSystem]
    cation_eq: Dict[str, float] = field(default_factory=dict)
    stability: Dict[str, object] = field(default_factory=dict)

_ALL = list(NormSystem)

class MineralDatabase:
    MINERALS: Dict[str, Mineral] = {
        # --- Silica ---
        'Quartz':      Mineral('Quartz',      'SiO2',             60.084,  2.65, 'Tectosilicates', _ALL, {'Si':1.0}),
        'Tridymite':   Mineral('Tridymite',   'SiO2',             60.084,  2.26, 'Tectosilicates', [NormSystem.RITTMANN_VOLCANIC], {'Si':1.0}),
        'Cristobalite':Mineral('Cristobalite','SiO2',             60.084,  2.20, 'Tectosilicates', [NormSystem.RITTMANN_VOLCANIC], {'Si':1.0}),
        # --- Feldspars ---
        'Orthoclase':  Mineral('Orthoclase',  'KAlSi3O8',        278.332,  2.56, 'Feldspars', _ALL, {'K':1,'Al':1,'Si':3}),
        'Sanidine':    Mineral('Sanidine',    'KAlSi3O8',        278.332,  2.53, 'Feldspars', [NormSystem.RITTMANN_VOLCANIC], {'K':1,'Al':1,'Si':3}),
        'Microcline':  Mineral('Microcline',  'KAlSi3O8',        278.332,  2.56, 'Feldspars', [NormSystem.MESONORM, NormSystem.CATANORM_METAMORPHIC], {'K':1,'Al':1,'Si':3}),
        'Albite':      Mineral('Albite',      'NaAlSi3O8',       262.223,  2.62, 'Feldspars', _ALL, {'Na':1,'Al':1,'Si':3}),
        'Oligoclase':  Mineral('Oligoclase',  '(Na0.8Ca0.2)AlSi3O8', 265.0, 2.64, 'Feldspars', [NormSystem.MESONORM, NormSystem.CATANORM_METAMORPHIC], {'Na':0.8,'Ca':0.2,'Al':1.2,'Si':2.8}),
        'Andesine':    Mineral('Andesine',    '(Na0.6Ca0.4)AlSi3O8', 268.0, 2.67, 'Feldspars', [NormSystem.MESONORM, NormSystem.CATANORM_METAMORPHIC], {'Na':0.6,'Ca':0.4,'Al':1.4,'Si':2.6}),
        'Labradorite': Mineral('Labradorite', '(Ca0.6Na0.4)AlSi3O8', 271.0, 2.70, 'Feldspars', [NormSystem.MESONORM, NormSystem.CATANORM_METAMORPHIC], {'Na':0.4,'Ca':0.6,'Al':1.6,'Si':2.4}),
        'Bytownite':   Mineral('Bytownite',   '(Ca0.8Na0.2)AlSi3O8', 274.0, 2.72, 'Feldspars', [NormSystem.MESONORM, NormSystem.CATANORM_METAMORPHIC], {'Na':0.2,'Ca':0.8,'Al':1.8,'Si':2.2}),
        'Anorthite':   Mineral('Anorthite',   'CaAl2Si2O8',      278.207,  2.76, 'Feldspars', _ALL, {'Ca':1,'Al':2,'Si':2}),
        # --- Feldspathoids ---
        'Nepheline':   Mineral('Nepheline',   'NaAlSiO4',        142.054,  2.62, 'Feldspathoids', [NormSystem.CIPW_STANDARD, NormSystem.HUTCHISON, NormSystem.NIGGLI_CATANORM, NormSystem.RITTMANN, NormSystem.RITTMANN_VOLCANIC], {'Na':1,'Al':1,'Si':1}),
        'Kalsilite':   Mineral('Kalsilite',   'KAlSiO4',         158.160,  2.61, 'Feldspathoids', [NormSystem.RITTMANN, NormSystem.RITTMANN_VOLCANIC], {'K':1,'Al':1,'Si':1}),
        'Leucite':     Mineral('Leucite',     'KAlSi2O6',        218.246,  2.47, 'Feldspathoids', [NormSystem.CIPW_STANDARD, NormSystem.HUTCHISON, NormSystem.RITTMANN, NormSystem.RITTMANN_VOLCANIC], {'K':1,'Al':1,'Si':2}),
        'Sodalite':    Mineral('Sodalite',    'Na4Al3Si3O12Cl',  584.665,  2.27, 'Feldspathoids', [NormSystem.RITTMANN], {'Na':4,'Al':3,'Si':3,'Cl':1}),
        'Nosean':      Mineral('Nosean',      'Na8Al6Si6O24SO4', 1068.0,   2.34, 'Feldspathoids', [NormSystem.RITTMANN], {'Na':8,'Al':6,'Si':6,'S':1}),
        'Cancrinite':  Mineral('Cancrinite',  'Na6Ca2Al6Si6O24(CO3)2', 1170.0, 2.52, 'Feldspathoids', [NormSystem.RITTMANN], {'Na':6,'Ca':2,'Al':6,'Si':6}),
        # --- Pyroxenes ---
        'Enstatite':   Mineral('Enstatite',   'MgSiO3',          100.389,  3.21, 'Pyroxenes', [NormSystem.CIPW_STANDARD, NormSystem.HUTCHISON, NormSystem.NIGGLI_CATANORM, NormSystem.MESONORM, NormSystem.CATANORM_METAMORPHIC], {'Mg':1,'Si':1}),
        'Ferrosilite': Mineral('Ferrosilite', 'FeSiO3',          131.928,  3.96, 'Pyroxenes', [NormSystem.CIPW_STANDARD, NormSystem.HUTCHISON, NormSystem.MESONORM, NormSystem.CATANORM_METAMORPHIC], {'Fe':1,'Si':1}),
        'Hypersthene': Mineral('Hypersthene', '(Mg,Fe)SiO3',     116.0,    3.40, 'Pyroxenes', [NormSystem.CIPW_STANDARD, NormSystem.HUTCHISON, NormSystem.HUTCHISON_BIOTITE, NormSystem.MESONORM, NormSystem.MESONORM_GRANITE, NormSystem.EPINORM, NormSystem.RITTMANN, NormSystem.SINCLAS], {'Mg':0.5,'Fe':0.5,'Si':1}),
        'Diopside':    Mineral('Diopside',    'CaMgSi2O6',       216.550,  3.27, 'Pyroxenes', [NormSystem.CIPW_STANDARD, NormSystem.HUTCHISON, NormSystem.HUTCHISON_BIOTITE, NormSystem.NIGGLI_CATANORM, NormSystem.BARTH_NIGGLI, NormSystem.MESONORM, NormSystem.MESONORM_GRANITE, NormSystem.RITTMANN, NormSystem.SINCLAS, NormSystem.CATANORM_METAMORPHIC], {'Ca':1,'Mg':1,'Si':2}),
        'Hedenbergite':Mineral('Hedenbergite','CaFeSi2O6',       248.090,  3.65, 'Pyroxenes', [NormSystem.CIPW_STANDARD, NormSystem.HUTCHISON, NormSystem.MESONORM, NormSystem.RITTMANN, NormSystem.CATANORM_METAMORPHIC], {'Ca':1,'Fe':1,'Si':2}),
        'Augite':      Mineral('Augite',      '(Ca,Mg,Fe,Al)2Si2O6', 236.0, 3.30, 'Pyroxenes', [NormSystem.MESONORM, NormSystem.CATANORM_METAMORPHIC, NormSystem.RITTMANN], {}),
        'Pigeonite':   Mineral('Pigeonite',   '(Mg,Fe,Ca)SiO3',  215.0,    3.38, 'Pyroxenes', [NormSystem.RITTMANN_VOLCANIC], {'Mg':0.6,'Fe':0.3,'Ca':0.1,'Si':1}),
        'Aegirine':    Mineral('Aegirine',    'NaFeSi2O6',       231.001,   3.58, 'Pyroxenes', [NormSystem.RITTMANN, NormSystem.RITTMANN_VOLCANIC], {'Na':1,'Fe':1,'Si':2}),
        'Jadeite':     Mineral('Jadeite',     'NaAlSi2O6',       202.139,   3.34, 'Pyroxenes', [NormSystem.CATANORM_METAMORPHIC], {'Na':1,'Al':1,'Si':2}),
        'Spodumene':   Mineral('Spodumene',   'LiAlSi2O6',       186.090,   3.18, 'Pyroxenes', [NormSystem.HUTCHISON], {'Li':1,'Al':1,'Si':2}),
        # --- Amphiboles ---
        'Tremolite':   Mineral('Tremolite',   'Ca2Mg5Si8O22(OH)2', 812.0,  2.98, 'Amphiboles', [NormSystem.MESONORM, NormSystem.CATANORM_METAMORPHIC], {'Ca':2,'Mg':5,'Si':8}),
        'Actinolite':  Mineral('Actinolite',  'Ca2(Mg,Fe)5Si8O22(OH)2', 835.0, 3.10, 'Amphiboles', [NormSystem.MESONORM, NormSystem.EPINORM], {'Ca':2,'Mg':3,'Fe':2,'Si':8}),
        'Hornblende':  Mineral('Hornblende',  'Ca2(Mg,Fe,Al)5(Al,Si)8O22(OH)2', 860.0, 3.20, 'Amphiboles', [NormSystem.HUTCHISON_BIOTITE, NormSystem.MESONORM, NormSystem.MESONORM_GRANITE], {'Ca':2,'Mg':2.5,'Fe':1.5,'Al':1.5,'Si':6.5}),
        'Glaucophane': Mineral('Glaucophane', 'Na2Mg3Al2Si8O22(OH)2', 810.0, 3.08, 'Amphiboles', [NormSystem.CATANORM_METAMORPHIC], {'Na':2,'Mg':3,'Al':2,'Si':8}),
        # --- Micas ---
        'Muscovite':   Mineral('Muscovite',   'KAl2(AlSi3O10)(OH)2', 398.308, 2.82, 'Micas', [NormSystem.HUTCHISON_BIOTITE, NormSystem.MESONORM, NormSystem.MESONORM_GRANITE, NormSystem.EPINORM, NormSystem.CATANORM_METAMORPHIC], {'K':1,'Al':3,'Si':3}),
        'Biotite':     Mineral('Biotite',     'K(Mg,Fe)3AlSi3O10(OH)2', 433.0, 3.00, 'Micas', [NormSystem.HUTCHISON_BIOTITE, NormSystem.MESONORM_GRANITE, NormSystem.EPINORM], {'K':1,'Mg':1.5,'Fe':1.5,'Al':1,'Si':3}),
        'Phlogopite':  Mineral('Phlogopite',  'KMg3AlSi3O10(OH)2', 419.0,  2.86, 'Micas', [NormSystem.CATANORM_METAMORPHIC], {'K':1,'Mg':3,'Al':1,'Si':3}),
        'Annite':      Mineral('Annite',      'KFe3AlSi3O10(OH)2', 512.0,  3.30, 'Micas', [NormSystem.HUTCHISON_BIOTITE], {'K':1,'Fe':3,'Al':1,'Si':3}),
        'Lepidolite':  Mineral('Lepidolite',  'K(Li,Al)3(AlSi3O10)(OH,F)2', 390.0, 2.85, 'Micas', [NormSystem.HUTCHISON], {'K':1,'Li':1.5,'Al':2,'Si':3}),
        # --- Clay minerals ---
        'Kaolinite':   Mineral('Kaolinite',   'Al2Si2O5(OH)4',   258.161,  2.60, 'Clay minerals', [NormSystem.EPINORM], {'Al':2,'Si':2}),
        'Pyrophyllite':Mineral('Pyrophyllite','Al2Si4O10(OH)2',   360.314,  2.82, 'Clay minerals', [NormSystem.EPINORM], {'Al':2,'Si':4}),
        'Talc':        Mineral('Talc',        'Mg3Si4O10(OH)2',  379.266,  2.75, 'Clay minerals', [NormSystem.EPINORM], {'Mg':3,'Si':4}),
        'Serpentine':  Mineral('Serpentine',  'Mg3Si2O5(OH)4',   277.112,  2.57, 'Clay minerals', [NormSystem.EPINORM], {'Mg':3,'Si':2}),
        'Chlorite':    Mineral('Chlorite',    '(Mg,Fe)5Al(AlSi3O10)(OH)8', 630.0, 2.75, 'Clay minerals', [NormSystem.EPINORM], {'Mg':3,'Fe':2,'Al':2,'Si':3}),
        # --- Oxides ---
        'Magnetite':   Mineral('Magnetite',   'Fe3O4',           231.533,  5.20, 'Oxides', _ALL, {'Fe':3}),
        'Hematite':    Mineral('Hematite',    'Fe2O3',           159.688,  5.26, 'Oxides', [NormSystem.CIPW_STANDARD, NormSystem.HUTCHISON, NormSystem.NIGGLI_CATANORM, NormSystem.RITTMANN, NormSystem.SINCLAS], {'Fe':2}),
        'Ilmenite':    Mineral('Ilmenite',    'FeTiO3',          151.710,  4.72, 'Oxides', _ALL, {'Fe':1,'Ti':1}),
        'Rutile':      Mineral('Rutile',      'TiO2',             79.866,  4.25, 'Oxides', [NormSystem.CIPW_STANDARD, NormSystem.HUTCHISON, NormSystem.MESONORM, NormSystem.CATANORM_METAMORPHIC], {'Ti':1}),
        'Anatase':     Mineral('Anatase',     'TiO2',             79.866,  3.88, 'Oxides', [NormSystem.EPINORM], {'Ti':1}),
        'Perovskite':  Mineral('Perovskite',  'CaTiO3',          135.943,  4.03, 'Oxides', [NormSystem.RITTMANN, NormSystem.CATANORM_METAMORPHIC], {'Ca':1,'Ti':1}),
        'Spinel':      Mineral('Spinel',      'MgAl2O4',         142.266,  3.55, 'Oxides', [NormSystem.CATANORM_METAMORPHIC], {'Mg':1,'Al':2}),
        'Chromite':    Mineral('Chromite',    'FeCr2O4',         223.837,  5.09, 'Oxides', [NormSystem.CIPW_STANDARD, NormSystem.HUTCHISON, NormSystem.SINCLAS], {'Fe':1,'Cr':2}),
        'Corundum':    Mineral('Corundum',    'Al2O3',           101.961,  3.99, 'Oxides', [NormSystem.CIPW_STANDARD, NormSystem.HUTCHISON, NormSystem.NIGGLI_CATANORM, NormSystem.BARTH_NIGGLI, NormSystem.MESONORM, NormSystem.CATANORM_METAMORPHIC], {'Al':2}),
        # --- Olivine ---
        'Olivine':     Mineral('Olivine',     '(Mg,Fe)2SiO4',    172.24,   3.32, 'Olivine', [NormSystem.CIPW_STANDARD, NormSystem.HUTCHISON, NormSystem.HUTCHISON_BIOTITE, NormSystem.NIGGLI_CATANORM, NormSystem.RITTMANN], {'Mg':1,'Fe':1,'Si':0.5}),
        'Forsterite':  Mineral('Forsterite',  'Mg2SiO4',         140.694,  3.22, 'Olivine', [NormSystem.CATANORM_METAMORPHIC], {'Mg':2,'Si':1}),
        'Fayalite':    Mineral('Fayalite',    'Fe2SiO4',         203.778,  4.39, 'Olivine', [NormSystem.CATANORM_METAMORPHIC], {'Fe':2,'Si':1}),
        # --- Carbonates ---
        'Calcite':     Mineral('Calcite',     'CaCO3',           100.087,  2.71, 'Carbonates', [NormSystem.CIPW_STANDARD, NormSystem.HUTCHISON, NormSystem.NIGGLI_CATANORM, NormSystem.RITTMANN, NormSystem.SINCLAS, NormSystem.EPINORM], {'Ca':1}),
        'Dolomite':    Mineral('Dolomite',    'CaMg(CO3)2',      184.401,  2.87, 'Carbonates', [NormSystem.CIPW_STANDARD, NormSystem.HUTCHISON, NormSystem.EPINORM], {'Ca':1,'Mg':1}),
        'Magnesite':   Mineral('Magnesite',   'MgCO3',            84.314,  2.96, 'Carbonates', [NormSystem.CIPW_STANDARD, NormSystem.EPINORM], {'Mg':1}),
        'Siderite':    Mineral('Siderite',    'FeCO3',           115.854,   3.96, 'Carbonates', [NormSystem.CIPW_STANDARD, NormSystem.EPINORM], {'Fe':1}),
        'Ankerite':    Mineral('Ankerite',    'Ca(Fe,Mg)(CO3)2', 215.0,    2.93, 'Carbonates', [NormSystem.EPINORM], {'Ca':1,'Fe':0.5,'Mg':0.5}),
        # --- Sulfates ---
        'Anhydrite':   Mineral('Anhydrite',   'CaSO4',           136.141,  2.96, 'Sulfates', [NormSystem.CIPW_STANDARD, NormSystem.HUTCHISON, NormSystem.SINCLAS], {'Ca':1,'S':1}),
        'Gypsum':      Mineral('Gypsum',      'CaSO4·2H2O',      172.171,  2.32, 'Sulfates', [NormSystem.EPINORM], {'Ca':1,'S':1}),
        'Barite':      Mineral('Barite',      'BaSO4',           233.391,  4.48, 'Sulfates', [NormSystem.CIPW_STANDARD], {'Ba':1,'S':1}),
        'Pyrite':      Mineral('Pyrite',      'FeS2',            119.975,  5.02, 'Sulfides', [NormSystem.CIPW_STANDARD, NormSystem.HUTCHISON], {'Fe':1,'S':2}),
        # --- Phosphates ---
        'Apatite':     Mineral('Apatite',     'Ca5(PO4)3(F,Cl,OH)', 504.303, 3.19, 'Phosphates', _ALL, {'Ca':5,'P':3}),
        # --- Halides ---
        'Halite':      Mineral('Halite',      'NaCl',             58.443,  2.17, 'Halides', [NormSystem.CIPW_STANDARD, NormSystem.SINCLAS], {'Na':1,'Cl':1}),
        'Fluorite':    Mineral('Fluorite',    'CaF2',             78.075,  3.18, 'Halides', [NormSystem.CIPW_STANDARD, NormSystem.HUTCHISON, NormSystem.SINCLAS], {'Ca':1,'F':2}),
        # --- Accessory ---
        'Zircon':      Mineral('Zircon',      'ZrSiO4',          183.307,  4.65, 'Accessory', _ALL, {'Zr':1,'Si':1}),
        'Titanite':    Mineral('Titanite',    'CaTiSiO5',        196.023,   3.52, 'Accessory', [NormSystem.MESONORM, NormSystem.CATANORM_METAMORPHIC, NormSystem.RITTMANN], {'Ca':1,'Ti':1,'Si':1}),
        'Tourmaline':  Mineral('Tourmaline',  'Na(Mg,Fe)3Al6(BO3)3Si6O18(OH)4', 970.0, 3.10, 'Accessory', [NormSystem.HUTCHISON, NormSystem.MESONORM_GRANITE], {}),
        'Andalusite':  Mineral('Andalusite',  'Al2SiO5',         162.046,  3.15, 'Accessory', [NormSystem.MESONORM, NormSystem.CATANORM_METAMORPHIC], {'Al':2,'Si':1}),
        'Kyanite':     Mineral('Kyanite',     'Al2SiO5',         162.046,  3.60, 'Accessory', [NormSystem.CATANORM_METAMORPHIC], {'Al':2,'Si':1}),
        'Sillimanite': Mineral('Sillimanite', 'Al2SiO5',         162.046,  3.23, 'Accessory', [NormSystem.CATANORM_METAMORPHIC], {'Al':2,'Si':1}),
        'Staurolite':  Mineral('Staurolite',  'Fe2Al9Si4O23(OH)', 812.0,   3.74, 'Accessory', [NormSystem.MESONORM, NormSystem.CATANORM_METAMORPHIC], {'Fe':2,'Al':9,'Si':4}),
        'Epidote':     Mineral('Epidote',     'Ca2(Al,Fe)3Si3O12(OH)', 519.0, 3.45, 'Accessory', [NormSystem.MESONORM, NormSystem.EPINORM], {'Ca':2,'Al':2,'Fe':1,'Si':3}),
        'Zoisite':     Mineral('Zoisite',     'Ca2Al3Si3O12(OH)', 454.0,   3.35, 'Accessory', [NormSystem.CATANORM_METAMORPHIC], {'Ca':2,'Al':3,'Si':3}),
        'Lawsonite':   Mineral('Lawsonite',   'CaAl2Si2O7(OH)2·H2O', 314.0, 3.09, 'Accessory', [NormSystem.CATANORM_METAMORPHIC], {'Ca':1,'Al':2,'Si':2}),
        'Prehnite':    Mineral('Prehnite',    'Ca2Al2Si3O10(OH)2', 414.0,  2.87, 'Accessory', [NormSystem.EPINORM], {'Ca':2,'Al':2,'Si':3}),
        'Pumpellyite': Mineral('Pumpellyite', 'Ca2MgAl2Si3O11(OH)3·H2O', 560.0, 3.21, 'Accessory', [NormSystem.EPINORM], {'Ca':2,'Mg':1,'Al':2,'Si':3}),
    }

# ============================================================================
# BASE ENGINE
# ============================================================================

class NormEngine:
    OXIDE_MW = {
        'SiO2':60.084,'TiO2':79.866,'Al2O3':101.961,'Fe2O3':159.688,
        'FeO':71.844,'MnO':70.937,'MgO':40.304,'CaO':56.077,
        'Na2O':61.979,'K2O':94.196,'P2O5':141.945,'H2O+':18.015,
        'CO2':44.010,'SO3':80.064,'Cr2O3':151.990,'NiO':74.692,
        'BaO':153.329,'SrO':103.619,'ZrO2':123.218,'F':18.998,'Cl':35.453,
        'Li2O':29.877,'B2O3':69.620
    }

    def oxides_to_mol(self, oxides: Dict[str, float]) -> Dict[str, float]:
        return {k: oxides.get(k, 0) / mw for k, mw in self.OXIDE_MW.items() if mw > 0}

    def _g(self, d: Dict, k: str, default=0.0) -> float:
        """Safe dict get, never negative"""
        return max(0.0, d.get(k, default))

    def _sub(self, d: Dict, k: str, val: float):
        """Subtract from dict, clamp to 0"""
        d[k] = max(0.0, d.get(k, 0.0) - val)

# ============================================================================
# CIPW ENGINE
# ============================================================================

class CIPWEngine(NormEngine):
    def calculate(self, oxides: Dict[str, float], **kw) -> Dict[str, float]:
        m = self.oxides_to_mol(oxides)
        mins = {}

        # 1. Apatite
        p = self._g(m,'P2O5')
        if p > 0:
            mins['Apatite'] = p * 10/3
            self._sub(m,'CaO', p * 10/3 * 56.077/101.961)  # simplified

        # 2. Pyrite (if SO3 present)
        so3 = self._g(m,'SO3')
        if so3 > 0 and self._g(m,'FeO') > 0:
            py = min(so3/2, self._g(m,'FeO'))
            mins['Pyrite'] = py
            self._sub(m,'FeO', py)
            self._sub(m,'SO3', py*2)

        # 3. Ilmenite
        ti = self._g(m,'TiO2')
        fe_for_il = self._g(m,'FeO')
        if ti > 0 and fe_for_il > 0:
            il = min(ti, fe_for_il)
            mins['Ilmenite'] = il
            self._sub(m,'TiO2', il)
            self._sub(m,'FeO', il)

        # Remaining TiO2 -> Rutile
        if self._g(m,'TiO2') > 0:
            mins['Rutile'] = m['TiO2']
            m['TiO2'] = 0

        # 4. Magnetite
        fe3 = self._g(m,'Fe2O3')
        if fe3 > 0:
            mt = fe3
            mins['Magnetite'] = mt
            self._sub(m,'FeO', mt)
            m['Fe2O3'] = 0

        # 5. Chromite
        cr = self._g(m,'Cr2O3')
        if cr > 0 and self._g(m,'FeO') > 0:
            ch = min(cr, self._g(m,'FeO'))
            mins['Chromite'] = ch
            self._sub(m,'FeO', ch)
            self._sub(m,'Cr2O3', ch)

        # Zircon
        zr = self._g(m,'ZrO2')
        if zr > 0 and self._g(m,'SiO2') >= zr:
            mins['Zircon'] = zr
            self._sub(m,'SiO2', zr)
            m['ZrO2'] = 0

        # Fluorite
        f = self._g(m,'F')
        if f > 0 and self._g(m,'CaO') >= f/2:
            fl = f/2
            mins['Fluorite'] = fl
            self._sub(m,'CaO', fl)
            m['F'] = 0

        # Halite
        cl = self._g(m,'Cl')
        if cl > 0 and self._g(m,'Na2O') >= cl/2:
            hl = cl/2
            mins['Halite'] = hl
            self._sub(m,'Na2O', cl/2)
            m['Cl'] = 0

        # Calcite (if CO2 present)
        co2 = self._g(m,'CO2')
        if co2 > 0 and self._g(m,'CaO') > 0:
            cc = min(co2, self._g(m,'CaO'))
            mins['Calcite'] = cc
            self._sub(m,'CaO', cc)
            self._sub(m,'CO2', cc)

        # Anhydrite (remaining SO3)
        so3 = self._g(m,'SO3')
        if so3 > 0 and self._g(m,'CaO') > 0:
            an_sulf = min(so3, self._g(m,'CaO'))
            mins['Anhydrite'] = an_sulf
            self._sub(m,'CaO', an_sulf)
            self._sub(m,'SO3', an_sulf)

        # 6. Orthoclase
        k2o = self._g(m,'K2O')
        if k2o > 0 and self._g(m,'Al2O3') >= k2o and self._g(m,'SiO2') >= k2o*3:
            mins['Orthoclase'] = k2o
            self._sub(m,'Al2O3', k2o)
            self._sub(m,'SiO2', k2o*3)
            m['K2O'] = 0

        # 7. Albite
        na2o = self._g(m,'Na2O')
        if na2o > 0 and self._g(m,'Al2O3') >= na2o and self._g(m,'SiO2') >= na2o*3:
            mins['Albite'] = na2o
            self._sub(m,'Al2O3', na2o)
            self._sub(m,'SiO2', na2o*3)
            m['Na2O'] = 0

        # 8. Anorthite
        al = self._g(m,'Al2O3')
        cao = self._g(m,'CaO')
        if al > 0 and cao >= al and self._g(m,'SiO2') >= al*2:
            mins['Anorthite'] = al
            self._sub(m,'CaO', al)
            self._sub(m,'SiO2', al*2)
            m['Al2O3'] = 0

        # 9. Corundum (excess Al)
        al = self._g(m,'Al2O3')
        if al > 0:
            mins['Corundum'] = al
            m['Al2O3'] = 0

        # 10. Diopside
        cao = self._g(m,'CaO')
        if cao > 0:
            mg = self._g(m,'MgO')
            fe = self._g(m,'FeO')
            mg_fe = mg + fe
            di = min(cao, mg_fe, self._g(m,'SiO2')/2)
            if di > 0:
                mins['Diopside'] = di
                self._sub(m,'CaO', di)
                self._sub(m,'SiO2', di*2)
                mg_used = min(mg, di)
                self._sub(m,'MgO', mg_used)
                self._sub(m,'FeO', di - mg_used)

        # Remaining CaO -> Wollastonite (simplified)
        if self._g(m,'CaO') > 0 and self._g(m,'SiO2') >= self._g(m,'CaO'):
            wo = self._g(m,'CaO')
            mins['Wollastonite'] = mins.get('Wollastonite', 0) + wo
            self._sub(m,'SiO2', wo)
            m['CaO'] = 0

        # 11. Hypersthene
        hy = self._g(m,'MgO') + self._g(m,'FeO')
        if hy > 0 and self._g(m,'SiO2') >= hy:
            mins['Hypersthene'] = hy
            self._sub(m,'SiO2', hy)
            m['MgO'] = 0
            m['FeO'] = 0

        # 12/13. Silica saturation
        sio2 = m.get('SiO2', 0)
        if sio2 < -1e-6:  # Undersaturated - convert Hy -> Ol
            deficit = -sio2
            hy_avail = mins.get('Hypersthene', 0)
            ol_needed = min(deficit, hy_avail/2)
            if ol_needed > 0:
                mins['Olivine'] = ol_needed
                mins['Hypersthene'] = max(0, hy_avail - ol_needed*2)
                m['SiO2'] = max(0, sio2 + ol_needed)

            # Still undersaturated -> Nepheline from Albite
            if m.get('SiO2', 0) < -1e-6 and 'Albite' in mins:
                deficit = -m.get('SiO2', 0)
                ne_mol = min(deficit/2, mins['Albite'])
                mins['Nepheline'] = mins.get('Nepheline', 0) + ne_mol
                mins['Albite'] = max(0, mins.get('Albite', 0) - ne_mol)
                m['SiO2'] = max(0, m.get('SiO2', 0) + ne_mol*2)

            # Leucite from Orthoclase
            if m.get('SiO2', 0) < -1e-6 and 'Orthoclase' in mins:
                deficit = -m.get('SiO2', 0)
                lc_mol = min(deficit/2, mins['Orthoclase'])
                mins['Leucite'] = mins.get('Leucite', 0) + lc_mol
                mins['Orthoclase'] = max(0, mins.get('Orthoclase', 0) - lc_mol)
                m['SiO2'] = max(0, m.get('SiO2', 0) + lc_mol*2)

            m['SiO2'] = max(0, m.get('SiO2', 0))

        elif sio2 > 1e-6:
            mins['Quartz'] = sio2
            m['SiO2'] = 0

        return {k: v for k, v in mins.items() if v > 1e-9}


# ============================================================================
# HUTCHISON ENGINE
# ============================================================================

class HutchisonEngine(NormEngine):
    def calculate(self, oxides: Dict[str, float], include_biotite: bool = False, **kw) -> Dict[str, float]:
        m = self.oxides_to_mol(oxides)
        mins = {}

        # Accessory minerals (same as CIPW)
        for k_oxide, m_key, factor in [('P2O5','CaO',10/3), ('TiO2','FeO',1)]:
            val = self._g(m, k_oxide)
            if val > 0:
                dep = self._g(m, m_key)
                used = min(val, dep) if m_key else val
                mins['Apatite' if k_oxide == 'P2O5' else 'Ilmenite'] = used
                self._sub(m, k_oxide, used)
                if m_key:
                    self._sub(m, m_key, used)

        fe3 = self._g(m,'Fe2O3')
        if fe3 > 0:
            mins['Magnetite'] = fe3
            self._sub(m,'FeO', fe3)
            m['Fe2O3'] = 0

        # Li minerals
        li = self._g(m,'Li2O')
        if li > 0 and self._g(m,'Al2O3') >= li and self._g(m,'SiO2') >= li*2:
            mins['Spodumene'] = li
            self._sub(m,'Al2O3', li)
            self._sub(m,'SiO2', li*2)
            m['Li2O'] = 0

        # Micas if include_biotite
        if include_biotite:
            # Muscovite first
            k = self._g(m,'K2O')
            al = self._g(m,'Al2O3')
            si = self._g(m,'SiO2')
            if k > 0 and al >= k*2 and si >= k*3:
                mu = k * 0.5  # Split K between muscovite and orthoclase
                mins['Muscovite'] = mu
                self._sub(m,'K2O', mu)
                self._sub(m,'Al2O3', mu*2)
                self._sub(m,'SiO2', mu*3)

            # Biotite
            k = self._g(m,'K2O')
            mg = self._g(m,'MgO')
            fe = self._g(m,'FeO')
            al = self._g(m,'Al2O3')
            si = self._g(m,'SiO2')
            mg_fe = mg + fe
            if k > 0 and mg_fe > 0 and al > 0 and si > 0:
                bi = min(k, mg_fe/3, al, si/3)
                if bi > 0:
                    mins['Biotite'] = bi
                    self._sub(m,'K2O', bi)
                    mg_used = min(mg, bi*1.5)
                    self._sub(m,'MgO', mg_used)
                    self._sub(m,'FeO', bi*3 - mg_used)
                    self._sub(m,'Al2O3', bi)
                    self._sub(m,'SiO2', bi*3)

        # Feldspars
        k = self._g(m,'K2O')
        if k > 0 and self._g(m,'Al2O3') >= k and self._g(m,'SiO2') >= k*3:
            mins['Orthoclase'] = k
            self._sub(m,'Al2O3', k)
            self._sub(m,'SiO2', k*3)
            m['K2O'] = 0

        na = self._g(m,'Na2O')
        if na > 0 and self._g(m,'Al2O3') >= na and self._g(m,'SiO2') >= na*3:
            mins['Albite'] = na
            self._sub(m,'Al2O3', na)
            self._sub(m,'SiO2', na*3)
            m['Na2O'] = 0

        al = self._g(m,'Al2O3')
        ca = self._g(m,'CaO')
        if al > 0 and ca >= al and self._g(m,'SiO2') >= al*2:
            mins['Anorthite'] = al
            self._sub(m,'CaO', al)
            self._sub(m,'SiO2', al*2)
            m['Al2O3'] = 0

        if self._g(m,'Al2O3') > 0:
            mins['Corundum'] = m['Al2O3']
            m['Al2O3'] = 0

        # Diopside
        ca = self._g(m,'CaO')
        if ca > 0:
            mg = self._g(m,'MgO'); fe = self._g(m,'FeO')
            di = min(ca, mg+fe, self._g(m,'SiO2')/2)
            if di > 0:
                mins['Diopside'] = di
                self._sub(m,'CaO', di)
                self._sub(m,'SiO2', di*2)
                mg_u = min(mg, di)
                self._sub(m,'MgO', mg_u)
                self._sub(m,'FeO', di-mg_u)

        # Hypersthene
        hy = self._g(m,'MgO') + self._g(m,'FeO')
        if hy > 0 and self._g(m,'SiO2') >= hy:
            mins['Hypersthene'] = hy
            self._sub(m,'SiO2', hy)
            m['MgO'] = 0; m['FeO'] = 0

        # Silica saturation (same logic as CIPW)
        sio2 = m.get('SiO2', 0)
        if sio2 < -1e-6:
            deficit = -sio2
            hy_a = mins.get('Hypersthene', 0)
            ol = min(deficit, hy_a/2)
            if ol > 0:
                mins['Olivine'] = ol
                mins['Hypersthene'] = max(0, hy_a - ol*2)
                m['SiO2'] = max(0, sio2 + ol)
            m['SiO2'] = max(0, m.get('SiO2', 0))
            if self._g(m,'SiO2') < 1e-6 and 'Albite' in mins:
                ne = min(self._g(m,'SiO2')*0.5, mins['Albite'])
                mins['Nepheline'] = mins.get('Nepheline', 0) + ne
                mins['Albite'] = max(0, mins['Albite'] - ne)
        elif sio2 > 1e-6:
            mins['Quartz'] = sio2

        return {k: v for k, v in mins.items() if v > 1e-9}


# ============================================================================
# NIGGLI ENGINE
# ============================================================================

class NiggliEngine(NormEngine):
    def calculate_catanorm(self, oxides: Dict[str, float], **kw) -> Dict[str, float]:
        m = self.oxides_to_mol(oxides)  # Use oxide mol props (keys are SiO2, Al2O3 etc.)
        mins = {}

        # Apatite
        p = self._g(m,'P2O5')
        if p > 0:
            mins['Apatite'] = p * 10/3
            self._sub(m,'CaO', p * 10/3)

        # Ilmenite
        ti = self._g(m,'TiO2')
        fe = self._g(m,'FeO')
        if ti > 0 and fe > 0:
            il = min(ti, fe)
            mins['Ilmenite'] = il
            self._sub(m,'TiO2', il)
            self._sub(m,'FeO', il)

        if self._g(m,'TiO2') > 0:
            mins['Rutile'] = m['TiO2']
            m['TiO2'] = 0

        # Magnetite
        fe3 = self._g(m,'Fe2O3')
        if fe3 > 0:
            mins['Magnetite'] = fe3
            self._sub(m,'FeO', fe3)
            m['Fe2O3'] = 0

        # Orthoclase
        k = self._g(m,'K2O')
        if k > 0 and self._g(m,'Al2O3') >= k and self._g(m,'SiO2') >= k*3:
            mins['Orthoclase'] = k
            self._sub(m,'Al2O3', k)
            self._sub(m,'SiO2', k*3)
            m['K2O'] = 0

        # Albite
        na = self._g(m,'Na2O')
        if na > 0 and self._g(m,'Al2O3') >= na and self._g(m,'SiO2') >= na*3:
            mins['Albite'] = na
            self._sub(m,'Al2O3', na)
            self._sub(m,'SiO2', na*3)
            m['Na2O'] = 0

        # Anorthite
        al = self._g(m,'Al2O3')
        ca = self._g(m,'CaO')
        if al > 0 and ca >= al and self._g(m,'SiO2') >= al*2:
            mins['Anorthite'] = al
            self._sub(m,'CaO', al)
            self._sub(m,'SiO2', al*2)
            m['Al2O3'] = 0

        if self._g(m,'Al2O3') > 0:
            mins['Corundum'] = m['Al2O3']
            m['Al2O3'] = 0

        # Diopside
        ca = self._g(m,'CaO')
        if ca > 0:
            mg = self._g(m,'MgO'); fe = self._g(m,'FeO')
            di = min(ca, mg+fe, self._g(m,'SiO2')/2)
            if di > 0:
                mins['Diopside'] = di
                self._sub(m,'CaO', di)
                self._sub(m,'SiO2', di*2)
                mg_u = min(mg, di)
                self._sub(m,'MgO', mg_u)
                self._sub(m,'FeO', di-mg_u)

        # Hypersthene
        hy = self._g(m,'MgO') + self._g(m,'FeO')
        if hy > 0 and self._g(m,'SiO2') >= hy:
            mins['Hypersthene'] = hy
            self._sub(m,'SiO2', hy)
            m['MgO'] = 0; m['FeO'] = 0
        elif hy > 0:
            ol = hy/2
            mins['Olivine'] = ol
            m['MgO'] = 0; m['FeO'] = 0

        if self._g(m,'SiO2') > 1e-6:
            mins['Quartz'] = m['SiO2']

        return {k: v for k, v in mins.items() if v > 1e-9}

    def calculate_niggli_numbers(self, oxides: Dict[str, float]) -> Dict[str, float]:
        m = self.oxides_to_mol(oxides)
        total = sum(m.values())
        if total == 0:
            return {}
        s = lambda k: m.get(k, 0) * 1000 / total
        fe_total = m.get('FeO', 0) + m.get('Fe2O3', 0) * 2
        mg_total = m.get('MgO', 0)
        k_total = m.get('K2O', 0)
        na_total = m.get('Na2O', 0)
        return {
            'si':  s('SiO2'), 'al': s('Al2O3'),
            'fm':  (m.get('FeO',0)+m.get('MgO',0)+m.get('MnO',0))*1000/total,
            'c':   s('CaO'),  'alk': (m.get('Na2O',0)+m.get('K2O',0))*1000/total,
            'ti':  s('TiO2'), 'p':  s('P2O5'),
            'mg':  mg_total/(mg_total+fe_total) if (mg_total+fe_total) > 0 else 0,
            'k':   k_total/(k_total+na_total) if (k_total+na_total) > 0 else 0,
        }


# ============================================================================
# MESONORM ENGINE
# ============================================================================

class MesonormEngine(NormEngine):
    def calculate(self, oxides: Dict[str, float], granite_version: bool = False, **kw) -> Dict[str, float]:
        m = self.oxides_to_mol(oxides)
        mins = {}

        # Accessory
        p = self._g(m,'P2O5')
        if p > 0:
            mins['Apatite'] = p * 10/3
            self._sub(m,'CaO', p*10/3)

        ti = self._g(m,'TiO2')
        if ti > 0:
            if granite_version and self._g(m,'CaO') > ti and self._g(m,'SiO2') > ti:
                mins['Titanite'] = ti
                self._sub(m,'CaO', ti)
                self._sub(m,'SiO2', ti)
                m['TiO2'] = 0
            elif self._g(m,'FeO') > 0:
                il = min(ti, self._g(m,'FeO'))
                mins['Ilmenite'] = il
                self._sub(m,'TiO2', il)
                self._sub(m,'FeO', il)

        fe3 = self._g(m,'Fe2O3')
        if fe3 > 0:
            mins['Magnetite'] = fe3
            self._sub(m,'FeO', fe3)
            m['Fe2O3'] = 0

        # Micas (granite version first)
        if granite_version:
            k = self._g(m,'K2O')
            al = self._g(m,'Al2O3')
            si = self._g(m,'SiO2')
            if k > 0 and al >= k*2 and si >= k*3:
                mu = k * 0.6
                mins['Muscovite'] = mu
                self._sub(m,'K2O', mu)
                self._sub(m,'Al2O3', mu*2)
                self._sub(m,'SiO2', mu*3)

            k = self._g(m,'K2O')
            mg = self._g(m,'MgO'); fe = self._g(m,'FeO'); al = self._g(m,'Al2O3')
            if k > 0 and (mg+fe) > 0 and al > 0:
                bi = min(k, (mg+fe)/3, al, self._g(m,'SiO2')/3)
                if bi > 0:
                    mins['Biotite'] = bi
                    self._sub(m,'K2O', bi)
                    mg_u = min(mg, bi*1.5)
                    self._sub(m,'MgO', mg_u)
                    self._sub(m,'FeO', bi*3-mg_u)
                    self._sub(m,'Al2O3', bi)
                    self._sub(m,'SiO2', bi*3)

        # K-feldspar
        k = self._g(m,'K2O')
        if k > 0 and self._g(m,'Al2O3') >= k and self._g(m,'SiO2') >= k*3:
            label = 'Microcline' if granite_version else 'Orthoclase'
            mins[label] = k
            self._sub(m,'Al2O3', k)
            self._sub(m,'SiO2', k*3)
            m['K2O'] = 0

        # Plagioclase (mesonorm uses intermediate compositions)
        na = self._g(m,'Na2O'); ca = self._g(m,'CaO')
        if na + ca > 0:
            an_frac = ca / (na + ca) if (na + ca) > 0 else 0
            plag_labels = [(0.10,'Albite'),(0.30,'Oligoclase'),(0.50,'Andesine'),
                          (0.70,'Labradorite'),(0.90,'Bytownite'),(1.01,'Anorthite')]
            plag = next(lbl for thr,lbl in plag_labels if an_frac <= thr)
            al_needed = na + ca*2
            si_needed = na*3 + ca*2
            if self._g(m,'Al2O3') >= al_needed and self._g(m,'SiO2') >= si_needed:
                mins[plag] = na + ca
                self._sub(m,'Al2O3', al_needed)
                self._sub(m,'SiO2', si_needed)
                m['Na2O'] = 0; m['CaO'] = 0

        # Excess Al -> Al2SiO5
        al = self._g(m,'Al2O3')
        if al > 0:
            si_avail = self._g(m,'SiO2')
            if si_avail >= al:
                mins['Andalusite'] = al
                self._sub(m,'SiO2', al)
            else:
                mins['Corundum'] = al
            m['Al2O3'] = 0

        # Amphibole
        ca = self._g(m,'CaO')
        mg = self._g(m,'MgO'); fe = self._g(m,'FeO')
        if ca > 0 and (mg+fe) > 0:
            si_avail = self._g(m,'SiO2')
            hb = min(ca/2, (mg+fe)/4, si_avail/7)
            if hb > 0:
                mins['Hornblende'] = hb
                self._sub(m,'CaO', hb*2)
                mg_u = min(mg, hb*2)
                self._sub(m,'MgO', mg_u)
                self._sub(m,'FeO', hb*4-mg_u)
                self._sub(m,'SiO2', hb*7)

        # Diopside
        ca = self._g(m,'CaO')
        if ca > 0 and (self._g(m,'MgO')+self._g(m,'FeO')) > 0:
            mg = self._g(m,'MgO'); fe = self._g(m,'FeO')
            di = min(ca, mg+fe, self._g(m,'SiO2')/2)
            if di > 0:
                mins['Diopside'] = di
                self._sub(m,'CaO', di)
                self._sub(m,'SiO2', di*2)
                mg_u = min(mg, di)
                self._sub(m,'MgO', mg_u)
                self._sub(m,'FeO', di-mg_u)

        # Hypersthene
        hy = self._g(m,'MgO') + self._g(m,'FeO')
        si_avail = self._g(m,'SiO2')
        if hy > 0 and si_avail >= hy:
            mins['Hypersthene'] = hy
            self._sub(m,'SiO2', hy)
            m['MgO'] = 0; m['FeO'] = 0
        elif hy > 0:
            mins['Olivine'] = mins.get('Olivine', 0) + hy/2
            m['MgO'] = 0; m['FeO'] = 0

        if self._g(m,'SiO2') > 1e-6:
            mins['Quartz'] = m['SiO2']

        return {k: v for k, v in mins.items() if v > 1e-9}


# ============================================================================
# EPINORM ENGINE
# ============================================================================

class EpinormEngine(NormEngine):
    def calculate(self, oxides: Dict[str, float], **kw) -> Dict[str, float]:
        m = self.oxides_to_mol(oxides)
        mins = {}

        # Apatite
        p = self._g(m,'P2O5')
        if p > 0:
            mins['Apatite'] = p * 10/3
            self._sub(m,'CaO', p*10/3)

        # Carbonates
        co2 = self._g(m,'CO2')
        if co2 > 0:
            ca = self._g(m,'CaO')
            cc = min(co2, ca)
            if cc > 0:
                mins['Calcite'] = cc
                self._sub(m,'CaO', cc)
                self._sub(m,'CO2', cc)
            mg = self._g(m,'MgO')
            dol = min(self._g(m,'CO2')/2, mg)
            if dol > 0:
                mins['Dolomite'] = dol
                self._sub(m,'MgO', dol)
                self._sub(m,'CO2', dol*2)
            fe = self._g(m,'FeO')
            sd = min(self._g(m,'CO2'), fe)
            if sd > 0:
                mins['Siderite'] = sd
                self._sub(m,'FeO', sd)
                self._sub(m,'CO2', sd)

        # TiO2 -> Anatase (low-T)
        ti = self._g(m,'TiO2')
        if ti > 0:
            mins['Anatase'] = ti
            m['TiO2'] = 0

        # Fe2O3 -> Hematite
        fe3 = self._g(m,'Fe2O3')
        if fe3 > 0:
            mins['Hematite'] = fe3
            m['Fe2O3'] = 0

        # Muscovite
        k = self._g(m,'K2O')
        if k > 0 and self._g(m,'Al2O3') >= k*2 and self._g(m,'SiO2') >= k*3:
            mins['Muscovite'] = k
            self._sub(m,'Al2O3', k*2)
            self._sub(m,'SiO2', k*3)
            m['K2O'] = 0

        # Kaolinite
        al = self._g(m,'Al2O3')
        if al > 0 and self._g(m,'SiO2') >= al:
            mins['Kaolinite'] = al
            self._sub(m,'SiO2', al)
            m['Al2O3'] = 0

        # Chlorite (consumes remaining MgO/FeO with any remaining Al)
        al = self._g(m,'Al2O3')
        mg = self._g(m,'MgO'); fe = self._g(m,'FeO')
        if (mg+fe) > 0 and al > 0:
            chl = min((mg+fe)/5, al, self._g(m,'SiO2')/3)
            if chl > 0:
                mins['Chlorite'] = chl
                mg_u = min(mg, chl*2.5)
                self._sub(m,'MgO', mg_u)
                self._sub(m,'FeO', chl*5-mg_u)
                self._sub(m,'Al2O3', chl)
                self._sub(m,'SiO2', chl*3)

        # Remaining Mg -> Talc (consume before Serpentine to avoid double)
        mg = self._g(m,'MgO')
        si_avail = self._g(m,'SiO2')
        if mg > 0 and si_avail >= mg*4/3:
            tc = mg/3
            mins['Talc'] = tc
            self._sub(m,'SiO2', tc*4)
            m['MgO'] = 0
        elif mg > 0 and si_avail >= mg*2/3:
            srp = mg/3
            mins['Serpentine'] = srp
            self._sub(m,'SiO2', srp*2)
            m['MgO'] = 0

        # Epidote from remaining Ca
        ca = self._g(m,'CaO'); fe = self._g(m,'FeO')
        if ca > 0 and fe > 0 and self._g(m,'SiO2') >= ca*1.5:
            ep = min(ca/2, fe)
            mins['Epidote'] = ep
            self._sub(m,'CaO', ep*2)
            self._sub(m,'FeO', ep)
            self._sub(m,'SiO2', ep*3)

        # Calcite from remaining CaO + CO2
        ca = self._g(m,'CaO')
        if ca > 0:
            mins['Calcite'] = mins.get('Calcite', 0) + ca
            m['CaO'] = 0

        if self._g(m,'SiO2') > 1e-6:
            mins['Quartz'] = m['SiO2']

        return {k: v for k, v in mins.items() if v > 1e-9}


# ============================================================================
# RITTMANN ENGINE
# ============================================================================

class RittmannEngine(NormEngine):
    def calculate(self, oxides: Dict[str, float], volcanic_facies: bool = True, **kw) -> Dict[str, float]:
        m = self.oxides_to_mol(oxides)
        mins = {}

        # Apatite
        p = self._g(m,'P2O5')
        if p > 0:
            mins['Apatite'] = p * 10/3
            self._sub(m,'CaO', p*10/3)

        # Perovskite for high-Ti alkaline, else Ilmenite
        ti = self._g(m,'TiO2')
        ca = self._g(m,'CaO')
        if ti > 0 and ca > ti:
            mins['Perovskite'] = ti
            self._sub(m,'CaO', ti)
            m['TiO2'] = 0
        elif ti > 0 and self._g(m,'FeO') > 0:
            il = min(ti, self._g(m,'FeO'))
            mins['Ilmenite'] = il
            self._sub(m,'TiO2', il)
            self._sub(m,'FeO', il)

        fe3 = self._g(m,'Fe2O3')
        if fe3 > 0:
            mins['Magnetite'] = fe3
            self._sub(m,'FeO', fe3)
            m['Fe2O3'] = 0

        # Aegirine (peralkaline)
        na = self._g(m,'Na2O'); k = self._g(m,'K2O'); al = self._g(m,'Al2O3')
        excess_alk = (na + k) - al
        if excess_alk > 0 and self._g(m,'FeO') > 0 and self._g(m,'SiO2') >= excess_alk*2:
            ae = min(excess_alk, self._g(m,'FeO'))
            mins['Aegirine'] = ae
            self._sub(m,'Na2O', ae)
            self._sub(m,'FeO', ae)
            self._sub(m,'SiO2', ae*2)

        # Feldspars (Sanidine for volcanic)
        k = self._g(m,'K2O')
        if k > 0 and self._g(m,'Al2O3') >= k and self._g(m,'SiO2') >= k*3:
            label = 'Sanidine' if volcanic_facies else 'Orthoclase'
            mins[label] = k
            self._sub(m,'Al2O3', k)
            self._sub(m,'SiO2', k*3)
            m['K2O'] = 0

        na = self._g(m,'Na2O')
        if na > 0 and self._g(m,'Al2O3') >= na and self._g(m,'SiO2') >= na*3:
            mins['Albite'] = na
            self._sub(m,'Al2O3', na)
            self._sub(m,'SiO2', na*3)
            m['Na2O'] = 0

        al = self._g(m,'Al2O3'); ca = self._g(m,'CaO')
        if al > 0 and ca >= al and self._g(m,'SiO2') >= al*2:
            mins['Anorthite'] = al
            self._sub(m,'CaO', al)
            self._sub(m,'SiO2', al*2)
            m['Al2O3'] = 0

        # Nepheline (undersaturated)
        na = self._g(m,'Na2O')
        al = self._g(m,'Al2O3')
        if na > 0 and al > 0 and self._g(m,'SiO2') >= min(na,al):
            ne = min(na, al)
            mins['Nepheline'] = ne
            self._sub(m,'Na2O', ne)
            self._sub(m,'Al2O3', ne)
            self._sub(m,'SiO2', ne)

        # Diopside
        ca = self._g(m,'CaO')
        if ca > 0 and (self._g(m,'MgO')+self._g(m,'FeO')) > 0:
            mg = self._g(m,'MgO'); fe = self._g(m,'FeO')
            di = min(ca, mg+fe, self._g(m,'SiO2')/2)
            if di > 0:
                mins['Diopside'] = di
                self._sub(m,'CaO', di)
                self._sub(m,'SiO2', di*2)
                mg_u = min(mg, di)
                self._sub(m,'MgO', mg_u)
                self._sub(m,'FeO', di-mg_u)

        # Pigeonite (volcanic low-Ca pyroxene)
        hy = self._g(m,'MgO') + self._g(m,'FeO')
        if hy > 0 and self._g(m,'SiO2') >= hy:
            label = 'Pigeonite' if volcanic_facies else 'Hypersthene'
            mins[label] = hy
            self._sub(m,'SiO2', hy)
            m['MgO'] = 0; m['FeO'] = 0

        sio2 = self._g(m,'SiO2')
        if sio2 > 1e-6:
            label = 'Tridymite' if volcanic_facies else 'Quartz'
            mins[label] = sio2

        return {k: v for k, v in mins.items() if v > 1e-9}


# ============================================================================
# SINCLAS ENGINE
# ============================================================================

class SINCLASEngine(NormEngine):
    def calculate(self, oxides: Dict[str, float], **kw) -> Dict[str, float]:
        oxides = dict(oxides)
        sio2 = oxides.get('SiO2', 0)
        # Optimize Fe ratio
        ratio = (0.2 if sio2 < 45 else 0.3 if sio2 < 52 else 0.4 if sio2 < 57
                 else 0.5 if sio2 < 63 else 0.6 if sio2 < 69 else 0.7)
        fe2o3 = oxides.get('Fe2O3', 0)
        feo = oxides.get('FeO', 0)
        total_fe_fe2o3 = fe2o3 + feo * 159.688 / 143.688
        oxides['Fe2O3'] = total_fe_fe2o3 * ratio
        oxides['FeO'] = (total_fe_fe2o3 - oxides['Fe2O3']) * 143.688 / 159.688
        return CIPWEngine().calculate(oxides)


# ============================================================================
# VOLUME % CALCULATOR
# ============================================================================

def calculate_vol_percent(mineral_wt: Dict[str, float]) -> tuple:
    """Convert wt% to vol% using mineral densities.

    Returns:
        (vol_pct_dict, warnings_list)  — warnings is empty when all densities are known.
    """
    _DEFAULT_DENSITY = 2.70  # g/cm³ – crustal average fallback
    vol = {}
    warnings = []
    for mineral, wt in mineral_wt.items():
        info = MineralDatabase.MINERALS.get(mineral)
        if info is None or info.density <= 0:
            density = _DEFAULT_DENSITY
            warnings.append(
                f"⚠  {mineral}: density unknown, assumed {_DEFAULT_DENSITY} g/cm³ (Vol% approximate)"
            )
        else:
            density = info.density
        vol[mineral] = wt / density
    total_vol = sum(vol.values())
    if total_vol > 0:
        return {k: v / total_vol * 100 for k, v in vol.items()}, warnings
    return vol, warnings


# ============================================================================
# PLOT HELPERS
# ============================================================================

def _ternary_coords(a, b, c):
    """Convert ternary (a,b,c) normalized to Cartesian (x,y)."""
    total = a + b + c
    if total == 0:
        return 0.5, 0.288
    a, b, c = a/total, b/total, c/total
    x = 0.5*(2*b + c)/(a + b + c)
    y = (np.sqrt(3)/2) * c / (a + b + c)
    return x, y

def draw_ternary(ax, title, labels, point, color='red', regions=None):
    """Draw a ternary diagram with a single data point and optional named regions.

    Parameters
    ----------
    regions : list of dict, optional
        Each dict: {'abc': (a, b, c), 'label': str, 'ha': str, 'va': str, 'style': dict}
        abc are un-normalised ternary coordinates of the text anchor.
    """
    verts = np.array([[0, 0], [1, 0], [0.5, np.sqrt(3) / 2]])

    # Background fill for readability
    triangle = plt.Polygon(verts, facecolor='#fafafa', edgecolor='black', linewidth=1.5, zorder=0)
    ax.add_patch(triangle)

    # Grid lines at 20 % intervals
    for pct in [0.2, 0.4, 0.6, 0.8]:
        for i in range(3):
            p1 = (1 - pct) * verts[i] + pct * verts[(i + 1) % 3]
            p2 = (1 - pct) * verts[i] + pct * verts[(i + 2) % 3]
            ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color='#cccccc', lw=0.5, zorder=1)
            # Tick label on first side only (bottom)
            if i == 0 and pct in [0.2, 0.4, 0.6, 0.8]:
                ax.text(p1[0], p1[1] - 0.04, f"{int(pct*100)}", fontsize=5,
                        ha='center', va='top', color='#888')

    # Vertex labels (bold, slightly outside)
    offsets = [(-0.10, -0.06), (1.06, -0.06), (0.5, np.sqrt(3) / 2 + 0.06)]
    ha_list  = ['right', 'left', 'center']
    for lbl, off, ha in zip(labels, offsets, ha_list):
        ax.text(off[0], off[1], lbl, ha=ha, va='center',
                fontsize=9, fontweight='bold', zorder=5)

    # Named rock-field regions (beginner helpers)
    if regions:
        for reg in regions:
            a, b, c = reg['abc']
            rx, ry = _ternary_coords(a, b, c)
            default_style = dict(fontsize=6, color='#444', ha=reg.get('ha','center'),
                                 va=reg.get('va','center'), style='italic',
                                 bbox=dict(boxstyle='round,pad=0.15', fc='white',
                                           ec='none', alpha=0.6))
            default_style.update(reg.get('style', {}))
            ax.text(rx, ry, reg['label'], zorder=4, **default_style)

    # Data point
    a, b, c = point
    x, y = _ternary_coords(a, b, c)
    ax.scatter([x], [y], color=color, s=90, zorder=6, edgecolors='white', linewidths=0.6)
    total = a + b + c
    if total > 0:
        pct = (a/total*100, b/total*100, c/total*100)
        ax.annotate(f"  {pct[0]:.0f}/{pct[1]:.0f}/{pct[2]:.0f}",
                    (x, y), fontsize=6, zorder=7, color=color)

    ax.set_xlim(-0.18, 1.18)
    ax.set_ylim(-0.13, 1.06)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(title, fontsize=9, pad=4)


# Named regions for standard ternary diagrams
_QORAB_REGIONS = [
    {'abc': (80,10,10), 'label': 'Quartzolite',         'ha': 'center'},
    {'abc': (35,55,10), 'label': 'Alkali granite',      'ha': 'center'},
    {'abc': (35,20,45), 'label': 'Granite',             'ha': 'center'},
    {'abc': (35, 5,60), 'label': 'Granodiorite',        'ha': 'center'},
    {'abc': (15,55,30), 'label': 'Syenite',             'ha': 'center'},
]
_OABAN_REGIONS = [
    {'abc': (80,15, 5), 'label': 'Alkali feldspar',     'ha': 'center'},
    {'abc': (30,55,15), 'label': 'Granite plag.',       'ha': 'center'},
    {'abc': (10,50,40), 'label': 'Andesine field',      'ha': 'center'},
    {'abc': ( 5,20,75), 'label': 'Calcic plag.',        'ha': 'center'},
]
_ENFSWO_REGIONS = [
    {'abc': (80,10,10), 'label': 'Orthopyroxene',       'ha': 'center'},
    {'abc': (40,40,20), 'label': 'Pigeonite',           'ha': 'center'},
    {'abc': (30,15,55), 'label': 'Augite/Diopside',     'ha': 'center'},
    {'abc': (10,60,30), 'label': 'Hedenbergite',        'ha': 'center'},
]
_FOFAEN_REGIONS = [
    {'abc': (80,10,10), 'label': 'Fo-rich olivine',     'ha': 'center'},
    {'abc': (10,80,10), 'label': 'Fa-rich olivine',     'ha': 'center'},
    {'abc': (10,10,80), 'label': 'Enstatite field',     'ha': 'center'},
]


def make_charts(results_wt: Dict[str, float]) -> 'plt.Figure':
    """Generate pie chart + 3 ternary diagrams."""
    fig = plt.figure(figsize=(8, 6))
    fig.suptitle("Normative Diagrams", fontsize=12, fontweight='bold')

    # ---- PIE CHART ----
    ax_pie = fig.add_axes([0.02, 0.52, 0.45, 0.42])
    GROUPS = {
        'Quartz/SiO2': ['Quartz','Tridymite','Cristobalite'],
        'Alkali Fsp':  ['Orthoclase','Sanidine','Microcline'],
        'Plagioclase': ['Albite','Oligoclase','Andesine','Labradorite','Bytownite','Anorthite'],
        'Feldspathoids':['Nepheline','Leucite','Kalsilite','Sodalite','Nosean','Cancrinite'],
        'Pyroxenes':   ['Diopside','Hedenbergite','Hypersthene','Enstatite','Ferrosilite','Augite','Pigeonite','Aegirine','Jadeite'],
        'Amphiboles':  ['Hornblende','Tremolite','Actinolite','Glaucophane'],
        'Micas':       ['Biotite','Muscovite','Phlogopite','Annite','Lepidolite'],
        'Olivine':     ['Olivine','Forsterite','Fayalite'],
        'Oxides':      ['Magnetite','Ilmenite','Hematite','Rutile','Anatase','Chromite','Corundum','Spinel','Perovskite'],
        'Others':      [],  # catch-all
    }
    # Semantic colour palette: geologically meaningful per group
    GROUP_COLORS = {
        'Quartz/SiO2':  '#a8d8ea',   # pale blue  – felsic/silica
        'Alkali Fsp':   '#e8a87c',   # warm salmon – K-feldspar
        'Plagioclase':  '#f4d35e',   # yellow-gold – plagioclase
        'Feldspathoids':'#d4a5e8',   # lavender   – undersaturated
        'Pyroxenes':    '#4a7c59',   # dark green  – mafic
        'Amphiboles':   '#2d6a4f',   # deep green  – mafic
        'Micas':        '#c9a84c',   # ochre       – pelitic
        'Olivine':      '#52b788',   # medium green – ultramafic
        'Oxides':       '#7b2d8b',   # purple      – oxides
        'Others':       '#adb5bd',   # neutral grey
    }
    known = {m for grp in GROUPS.values() for m in grp}
    pie_vals, pie_labels, pie_colors = [], [], []
    for grp, members in GROUPS.items():
        v = sum(results_wt.get(m, 0) for m in members)
        if grp == 'Others':
            v += sum(results_wt.get(m, 0) for m in results_wt if m not in known)
        if v > 0.5:
            pie_vals.append(v)
            pie_labels.append(f"{grp}\n{v:.1f}%")
            pie_colors.append(GROUP_COLORS.get(grp, '#adb5bd'))

    ax_pie.pie(pie_vals, labels=pie_labels, colors=pie_colors,
               startangle=140, textprops={'fontsize': 7},
               wedgeprops={'linewidth':0.7,'edgecolor':'white'},
               pctdistance=0.82)
    ax_pie.set_title("Normative Groups (wt%)", fontsize=9, pad=4)

    # ---- TERNARY 1: Q-Or-Ab (QAPF) ----
    ax_t1 = fig.add_axes([0.50, 0.52, 0.22, 0.42])
    q  = results_wt.get('Quartz', 0) + results_wt.get('Tridymite', 0)
    or_ = (results_wt.get('Orthoclase', 0) + results_wt.get('Sanidine', 0) +
           results_wt.get('Microcline', 0))
    ab = results_wt.get('Albite', 0)
    draw_ternary(ax_t1, "Q–Or–Ab", ['Q','Or','Ab'], (q, or_, ab),
                 color='royalblue', regions=_QORAB_REGIONS)

    # ---- TERNARY 2: Or-Ab-An (Feldspar) ----
    ax_t2 = fig.add_axes([0.74, 0.52, 0.22, 0.42])
    an = sum(results_wt.get(m,0) for m in ['Anorthite','Bytownite','Labradorite','Andesine','Oligoclase'])
    draw_ternary(ax_t2, "Or–Ab–An", ['Or','Ab','An'], (or_, ab, an),
                 color='darkgreen', regions=_OABAN_REGIONS)

    # ---- TERNARY 3: En-Fs-Wo (Pyroxene) ----
    ax_t3 = fig.add_axes([0.02, 0.05, 0.22, 0.42])
    en = results_wt.get('Enstatite', 0) + results_wt.get('Hypersthene', 0)*0.5
    fs = results_wt.get('Ferrosilite', 0) + results_wt.get('Hypersthene', 0)*0.5 + results_wt.get('Hedenbergite',0)*0.5
    wo = results_wt.get('Diopside', 0) + results_wt.get('Hedenbergite', 0)*0.5
    draw_ternary(ax_t3, "En–Fs–Wo (Px)", ['En','Fs','Wo'], (en, fs, wo),
                 color='firebrick', regions=_ENFSWO_REGIONS)

    # ---- TERNARY 4: Fo-Fa-En (Ol-Opx) ----
    ax_t4 = fig.add_axes([0.26, 0.05, 0.22, 0.42])
    fo = results_wt.get('Forsterite',0) + results_wt.get('Olivine',0)*0.5
    fa = results_wt.get('Fayalite',0)  + results_wt.get('Olivine',0)*0.5
    draw_ternary(ax_t4, "Fo–Fa–En (Ol-Opx)", ['Fo','Fa','En'], (fo, fa, en),
                 color='purple', regions=_FOFAEN_REGIONS)

    # ---- BAR CHART: Top minerals ----
    ax_bar = fig.add_axes([0.52, 0.05, 0.44, 0.40])
    top = sorted(results_wt.items(), key=lambda x: x[1], reverse=True)[:12]
    names = [x[0] for x in top]
    vals  = [x[1] for x in top]
    bar_colors = plt.cm.viridis(np.linspace(0.1, 0.9, len(names)))
    bars = ax_bar.barh(names[::-1], vals[::-1], color=bar_colors[::-1])
    ax_bar.set_xlabel('wt%', fontsize=8)
    ax_bar.set_title("Top Normative Minerals", fontsize=9)
    ax_bar.tick_params(labelsize=7)
    for bar, val in zip(bars, vals[::-1]):
        ax_bar.text(bar.get_width()+0.3, bar.get_y()+bar.get_height()/2,
                    f'{val:.1f}', va='center', fontsize=6.5)
    ax_bar.set_xlim(0, max(vals)*1.15 if vals else 10)

    fig.patch.set_facecolor('#f8f9fa')
    return fig


# ============================================================================
# MAIN PLUGIN CLASS
# ============================================================================

METHOD_DESC = {
    NormSystem.CIPW_STANDARD.value:        "Standard CIPW norm (Cross et al. 1903). Anhydrous, low-pressure igneous assemblage.",
    NormSystem.CIPW_MATRIX.value:          "Matrix algebra CIPW (Pandey 2009) with optimized Fe ratio via SINCLAS.",
    NormSystem.HUTCHISON.value:            "Hutchison (1974/1975) modifications for granites & pegmatites.",
    NormSystem.HUTCHISON_BIOTITE.value:    "Hutchison Norm including biotite + muscovite allocation.",
    NormSystem.NIGGLI_CATANORM.value:      "Niggli Catanorm (1936) – molecular norm for high-grade metamorphic.",
    NormSystem.BARTH_NIGGLI.value:         "Barth-Niggli Catanorm (1952) for granulite facies rocks.",
    NormSystem.MESONORM.value:             "Mesonorm (Winkler 1979) for amphibolite facies with amphiboles.",
    NormSystem.MESONORM_GRANITE.value:     "Granite Mesonorm (Parslow 1969) – biotite + muscovite for granitoids.",
    NormSystem.EPINORM.value:              "Epinorm (Barth 1959) for greenschist facies with clay minerals.",
    NormSystem.RITTMANN.value:             "Rittmann Norm (1973) for volcanic rocks.",
    NormSystem.RITTMANN_VOLCANIC.value:    "Rittmann Volcanic – sanidine, tridymite, pigeonite, aegirine.",
    NormSystem.SINCLAS.value:              "SINCLAS (Verma et al. 2002) with optimised Fe2O3/FeO ratio.",
    NormSystem.CATANORM_METAMORPHIC.value: "Catanorm for high-grade metamorphic rocks (Barth 1959).",
}

SAMPLES = {
    'Granite (typical)':    [72.0, 0.3, 14.5, 1.2, 1.5, 0.05, 0.5, 1.5, 3.5, 4.2, 0.1, 0.5, 0.1, 0.02, 0.0, 0.0, 0.05, 0.0, 0.02, 0.03, 0.01, 0.0, 0.0],
    'Basalt (MORB)':        [50.5, 1.5, 15.0, 2.0, 8.5, 0.2, 7.5, 11.0, 2.8, 0.2, 0.1, 0.5, 0.1, 0.1, 0.05, 0.01, 0.01, 0.01, 0.01, 0.02, 0.01, 0.0, 0.0],
    'Granulite (felsic)':   [68.5, 0.5, 15.2, 1.5, 2.8, 0.1, 1.8, 3.2, 3.8, 3.0, 0.2, 0.3, 0.1, 0.02, 0.01, 0.0, 0.05, 0.01, 0.03, 0.02, 0.01, 0.0, 0.0],
    'Amphibolite':          [51.2, 1.2, 14.8, 2.5, 7.2, 0.2, 6.8, 9.5, 2.5, 1.2, 0.2, 1.2, 0.2, 0.1, 0.05, 0.01, 0.02, 0.01, 0.01, 0.03, 0.01, 0.0, 0.0],
    'Greenschist':          [48.5, 1.0, 15.5, 3.0, 6.5, 0.2, 5.5, 8.5, 2.2, 1.0, 0.2, 2.5, 1.5, 0.2, 0.05, 0.01, 0.02, 0.01, 0.01, 0.02, 0.01, 0.0, 0.0],
    'Rhyolite':             [73.5, 0.2, 13.5, 1.0, 1.2, 0.05, 0.3, 1.2, 4.0, 4.5, 0.05, 0.3, 0.05, 0.02, 0.0, 0.0, 0.05, 0.0, 0.02, 0.02, 0.01, 0.0, 0.0],
    'Phonolite':            [55.0, 0.5, 20.0, 2.5, 2.0, 0.2, 1.0, 2.5, 9.0, 5.0, 0.2, 1.0, 0.5, 0.3, 0.0, 0.0, 0.1, 0.02, 0.05, 0.05, 0.02, 0.0, 0.0],
    'Carbonatite':          [5.0, 0.1, 1.0, 3.0, 5.0, 0.3, 5.0, 45.0, 0.5, 0.5, 3.0, 1.0, 30.0, 0.5, 0.0, 0.0, 0.2, 0.1, 0.05, 0.1, 0.02, 0.0, 0.0],
}

OXIDES = ["SiO2","TiO2","Al2O3","Fe2O3","FeO","MnO","MgO","CaO","Na2O","K2O",
          "P2O5","H2O+","CO2","SO3","Cr2O3","NiO","BaO","SrO","ZrO2","F","Cl","Li2O","B2O3"]
OXIDE_DEFAULTS = [50.0, 1.0, 15.0, 2.0, 8.0, 0.2, 10.0, 8.0, 3.0, 2.0,
                  0.5, 0.5, 0.1, 0.05, 0.05, 0.01, 0.05, 0.01, 0.02, 0.05, 0.01, 0.0, 0.0]

ENGINE_MAP = {
    NormSystem.CIPW_STANDARD:        (CIPWEngine,      {}),
    NormSystem.CIPW_MATRIX:          (SINCLASEngine,   {}),
    NormSystem.HUTCHISON:            (HutchisonEngine, {'include_biotite': False}),
    NormSystem.HUTCHISON_BIOTITE:    (HutchisonEngine, {'include_biotite': True}),
    NormSystem.NIGGLI_CATANORM:      (NiggliEngine,    {}),
    NormSystem.BARTH_NIGGLI:         (NiggliEngine,    {}),
    NormSystem.MESONORM:             (MesonormEngine,  {'granite_version': False}),
    NormSystem.MESONORM_GRANITE:     (MesonormEngine,  {'granite_version': True}),
    NormSystem.EPINORM:              (EpinormEngine,   {}),
    NormSystem.RITTMANN:             (RittmannEngine,  {'volcanic_facies': False}),
    NormSystem.RITTMANN_VOLCANIC:    (RittmannEngine,  {'volcanic_facies': True}),
    NormSystem.SINCLAS:              (SINCLASEngine,   {}),
    NormSystem.CATANORM_METAMORPHIC: (NiggliEngine,    {}),
}

class AdvancedNormativeCalculationsPlugin:
    def __init__(self, app):
        self.app = app
        self.window = None
        self.results_wt = None
        self.results_vol = None
        self.results_mol = None
        self.niggli = None
        self.current_system = None
        self.entries: Dict[str, tk.Entry] = {}
        self.chart_fig = None
        self.chart_canvas = None
        self._vol_warnings: List[str] = []

    def open_window(self):
        if self.window and self.window.winfo_exists():
            self.window.lift(); self.window.focus_force(); return
        self.window = tk.Toplevel(self.app.root)
        self.window.title("Normative Calculator v5")
        self.window.geometry("820x620")
        self._build_ui()

    def _build_ui(self):
        win = self.window
        win.columnconfigure(0, weight=1)
        win.rowconfigure(0, weight=1)

        pw = ttk.PanedWindow(win, orient=tk.HORIZONTAL)
        pw.grid(row=0, column=0, sticky='nsew', padx=4, pady=4)

        # ---- LEFT PANEL ----
        left = ttk.Frame(pw, width=270)
        pw.add(left, weight=0)
        left.columnconfigure(0, weight=1)

        # Method
        mf = ttk.LabelFrame(left, text="Method", padding=4)
        mf.grid(row=0, column=0, sticky='ew', pady=(0,3))
        mf.columnconfigure(1, weight=1)

        self.method_var = tk.StringVar(value=NormSystem.CIPW_STANDARD.value)
        ttk.Label(mf, text="System:").grid(row=0, column=0, sticky='w')
        cb = ttk.Combobox(mf, textvariable=self.method_var,
                          values=[m.value for m in NormSystem],
                          state='readonly', width=30)
        cb.grid(row=0, column=1, sticky='ew', padx=(3,0))
        cb.bind('<<ComboboxSelected>>', self._on_method_change)

        self.desc_var = tk.StringVar()
        ttk.Label(mf, textvariable=self.desc_var, wraplength=255,
                  foreground='#555', font=('TkDefaultFont', 7)).grid(
            row=1, column=0, columnspan=2, sticky='w', pady=(2,0))
        self._on_method_change()

        ttk.Label(mf, text="Facies:").grid(row=2, column=0, sticky='w', pady=(3,0))
        self.facies_var = tk.StringVar(value=MetamorphicFacies.AMPHIBOLITE.value)
        ttk.Combobox(mf, textvariable=self.facies_var,
                     values=[f.value for f in MetamorphicFacies],
                     state='readonly', width=20).grid(row=2, column=1, sticky='w', padx=(3,0), pady=(3,0))

        # Oxide entries in scrollable frame
        inp = ttk.LabelFrame(left, text="Oxides (wt%)", padding=3)
        inp.grid(row=1, column=0, sticky='nsew', pady=(0,3))
        inp.columnconfigure(0, weight=1)
        left.rowconfigure(1, weight=1)

        canvas = tk.Canvas(inp, highlightthickness=0)
        sb = ttk.Scrollbar(inp, orient='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sf = ttk.Frame(canvas)
        sf.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0,0), window=sf, anchor='nw')
        canvas.pack(side='left', fill='both', expand=True)
        sb.pack(side='right', fill='y')

        for i, (oxide, val) in enumerate(zip(OXIDES, OXIDE_DEFAULTS)):
            r, c = i % 12, i // 12
            f = ttk.Frame(sf)
            f.grid(row=r, column=c*2, padx=3, pady=1, sticky='w')
            ttk.Label(f, text=f"{oxide}:", width=6, anchor='e').pack(side='left')
            e = ttk.Entry(f, width=8)
            e.insert(0, str(val))
            e.pack(side='left', padx=(2,0))
            self.entries[oxide] = e

        # Buttons
        bf = ttk.Frame(left)
        bf.grid(row=2, column=0, sticky='ew', pady=2)
        for text, cmd in [("Calculate", self.calculate_norm),
                          ("Sample", self.load_sample),
                          ("Export", self.export_results),
                          ("Charts", self.show_charts),
                          ("Clear", self.clear)]:
            ttk.Button(bf, text=text, command=cmd, width=8).pack(side='left', padx=1)

        # ---- RIGHT PANEL ----
        right = ttk.Frame(pw)
        pw.add(right, weight=1)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=1)

        nb = ttk.Notebook(right)
        nb.grid(row=0, column=0, sticky='nsew')

        # Tab 1: Minerals table
        tab_min = ttk.Frame(nb)
        nb.add(tab_min, text="Minerals")
        cols = ("Mineral", "Category", "Wt%", "Vol%", "Mol prop")
        self.tree = ttk.Treeview(tab_min, columns=cols, show='headings', height=22)
        widths = [150, 100, 65, 65, 70]
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor='w' if w > 80 else 'center')
        sb2 = ttk.Scrollbar(tab_min, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb2.set)
        self.tree.pack(side='left', fill='both', expand=True)
        sb2.pack(side='right', fill='y')

        # Tab 2: Niggli
        tab_nig = ttk.Frame(nb)
        nb.add(tab_nig, text="Niggli")
        self.nig_tree = ttk.Treeview(tab_nig, columns=('Par','Val','Desc'), show='headings')
        for col, w, lbl in [('Par',60,'Param'),('Val',80,'Value'),('Desc',250,'Meaning')]:
            self.nig_tree.heading(col, text=lbl)
            self.nig_tree.column(col, width=w)
        self.nig_tree.pack(fill='both', expand=True)

        # Tab 3: Classification
        tab_cls = ttk.Frame(nb)
        nb.add(tab_cls, text="Classification")
        self.cls_text = tk.Text(tab_cls, wrap='word', font=('Courier', 8))
        sb3 = ttk.Scrollbar(tab_cls, orient='vertical', command=self.cls_text.yview)
        self.cls_text.configure(yscrollcommand=sb3.set)
        self.cls_text.pack(side='left', fill='both', expand=True)
        sb3.pack(side='right', fill='y')

        # Tab 4: Charts (embedded)
        tab_chart = ttk.Frame(nb)
        nb.add(tab_chart, text="Charts")
        self.chart_frame = tab_chart

        self.notebook = nb

    def _on_method_change(self, event=None):
        self.desc_var.set(METHOD_DESC.get(self.method_var.get(), ''))

    def _get_system(self) -> Optional[NormSystem]:
        for m in NormSystem:
            if m.value == self.method_var.get():
                return m
        return None

    def _get_oxides(self) -> Dict[str, float]:
        return {ox: max(0.0, float(self.entries[ox].get() or 0)) for ox in OXIDES}

    def calculate_norm(self):
        try:
            oxides = self._get_oxides()
            system = self._get_system()
            if not system:
                messagebox.showerror("Error", "Invalid method"); return

            EngClass, kw = ENGINE_MAP[system]
            engine = EngClass()

            if system in (NormSystem.NIGGLI_CATANORM, NormSystem.BARTH_NIGGLI, NormSystem.CATANORM_METAMORPHIC):
                mol_mins = engine.calculate_catanorm(oxides, **kw)
                self.niggli = engine.calculate_niggli_numbers(oxides)
            else:
                mol_mins = engine.calculate(oxides, **kw)
                self.niggli = None

            # Convert mol proportions -> wt%
            wt_raw = {}
            mol_raw = {}
            for mineral, mol_prop in mol_mins.items():
                info = MineralDatabase.MINERALS.get(mineral)
                if info and mol_prop > 1e-9:
                    wt_raw[mineral] = mol_prop * info.mw
                    mol_raw[mineral] = mol_prop
                elif mol_prop > 1e-9:
                    wt_raw[mineral] = mol_prop * 100  # fallback
                    mol_raw[mineral] = mol_prop

            total_wt = sum(wt_raw.values())
            if total_wt > 0:
                self.results_wt = {k: v/total_wt*100 for k, v in wt_raw.items()}
            else:
                self.results_wt = {}

            self.results_vol, self._vol_warnings = calculate_vol_percent(self.results_wt)
            total_mol = sum(mol_raw.values())
            self.results_mol = {k: v/total_mol for k, v in mol_raw.items()} if total_mol > 0 else {}
            self.current_system = system

            self._update_display()
            n = len(self.results_wt)
            messagebox.showinfo("Done", f"{system.value}\n{n} minerals | Total wt: {sum(self.results_wt.values()):.1f}%")

        except Exception as e:
            import traceback; traceback.print_exc()
            messagebox.showerror("Error", str(e))

    def _update_display(self):
        # Clear
        for item in self.tree.get_children(): self.tree.delete(item)
        for item in self.nig_tree.get_children(): self.nig_tree.delete(item)
        self.cls_text.delete('1.0', 'end')

        if not self.results_wt: return

        # Minerals table
        for mineral, wt in sorted(self.results_wt.items(), key=lambda x: x[1], reverse=True):
            if wt < 0.01: continue
            info = MineralDatabase.MINERALS.get(mineral)
            cat = info.category if info else 'Unknown'
            vol = self.results_vol.get(mineral, 0) if self.results_vol else 0
            mol = self.results_mol.get(mineral, 0) if self.results_mol else 0
            self.tree.insert('', 'end', values=(
                mineral, cat, f"{wt:.2f}", f"{vol:.2f}", f"{mol:.5f}"
            ))

        # Niggli
        niggli_descs = {
            'si': 'Silica saturation', 'al': 'Alumina index',
            'fm': 'Fe+Mg index', 'c': 'Calcic index',
            'alk': 'Alkali index', 'ti': 'Titanium index',
            'p': 'Phosphorus index', 'mg': 'Mg# (0-1)', 'k': 'K/(K+Na)'
        }
        if self.niggli:
            for k, v in self.niggli.items():
                self.nig_tree.insert('', 'end', values=(k.upper(), f"{v:.3f}", niggli_descs.get(k,'')))

        # Classification
        self.cls_text.insert('1.0', self._build_classification())

        # Auto-refresh embedded chart
        self._embed_chart()

    def _build_classification(self) -> str:
        R = self.results_wt
        sys_name = self.current_system.value if self.current_system else 'Unknown'
        q  = R.get('Quartz',0)+R.get('Tridymite',0)
        or_= R.get('Orthoclase',0)+R.get('Sanidine',0)+R.get('Microcline',0)
        ab = R.get('Albite',0)
        an = sum(R.get(m,0) for m in ['Anorthite','Bytownite','Labradorite','Andesine','Oligoclase'])
        ne = R.get('Nepheline',0)+R.get('Leucite',0)+R.get('Kalsilite',0)
        ol = R.get('Olivine',0)+R.get('Forsterite',0)+R.get('Fayalite',0)
        cor= R.get('Corundum',0)
        aeg= R.get('Aegirine',0)
        mafics = sum(R.get(m,0) for m in ['Olivine','Diopside','Hypersthene','Hedenbergite',
                                            'Augite','Hornblende','Biotite','Magnetite','Ilmenite',
                                            'Forsterite','Fayalite','Pigeonite'])
        total_fsp = or_ + ab + an
        lines = [f"Method: {sys_name}", "="*48, ""]

        # QAPF
        total_qapf = q + or_ + ab + an + ne
        if total_qapf > 0:
            q_p = q/total_qapf*100; or_p = or_/total_qapf*100
            ab_p = ab/total_qapf*100; an_p = an/total_qapf*100; ne_p = ne/total_qapf*100
            lines += [f"QAPF: Q={q_p:.1f} Or={or_p:.1f} Ab={ab_p:.1f} An={an_p:.1f} Ne={ne_p:.1f}", ""]

        # Saturation
        if ne > 5:
            lines.append(f"► SILICA-UNDERSATURATED  (Ne/Lc = {ne:.1f}%)")
        elif q > 20:
            lines.append(f"► SILICA-OVERSATURATED   (Q = {q:.1f}%)")
        elif q > 0:
            lines.append(f"► Quartz-normative       (Q = {q:.1f}%)")
        elif ol > 0:
            lines.append(f"► Olivine-normative      (Ol = {ol:.1f}%)")

        # Al saturation
        if cor > 5:    lines.append(f"► PERALUMINOUS           (Cor = {cor:.1f}%)")
        elif aeg > 0:  lines.append(f"► PERALKALINE            (Aeg present)")
        else:          lines.append("► Metaluminous")

        # Color index
        lines.append(f"\nColor Index M = {mafics:.1f}%")
        ci_desc = ("Leucocratic" if mafics < 10 else "Mesocratic" if mafics < 35
                   else "Melanocratic" if mafics < 65 else "Ultramafic")
        lines.append(f"→ {ci_desc}")

        # Feldspar comp
        if total_fsp > 5:
            Or = or_/total_fsp*100; Ab = ab/total_fsp*100; An = an/total_fsp*100
            lines.append(f"\nFeldspar: Or{Or:.0f} Ab{Ab:.0f} An{An:.0f}")

        # Vol% density warnings
        if getattr(self, '_vol_warnings', []):
            lines.append("\n" + "─"*48)
            lines.append("Vol% density fallbacks:")
            for w in self._vol_warnings:
                lines.append(f"  {w}")

        return "\n".join(lines)

    def _embed_chart(self):
        if not HAS_MPL or not self.results_wt: return
        # Clear old
        for w in self.chart_frame.winfo_children():
            w.destroy()
        try:
            fig = make_charts(self.results_wt)
            canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill='both', expand=True)
            self.chart_canvas = canvas
            self.chart_fig = fig
        except Exception as e:
            ttk.Label(self.chart_frame, text=f"Chart error: {e}").pack()

    def show_charts(self):
        """Open charts in a separate window for better viewing + PNG export."""
        if not HAS_MPL:
            messagebox.showerror("Error", "matplotlib not installed"); return
        if not self.results_wt:
            messagebox.showerror("Error", "Calculate a norm first"); return
        win = tk.Toplevel(self.window)
        win.title("Normative Diagrams")
        win.geometry("850x650")

        fig = make_charts(self.results_wt)

        # Toolbar frame (top)
        toolbar_frame = ttk.Frame(win)
        toolbar_frame.pack(side='top', fill='x')

        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

        try:
            from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
            toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
            toolbar.update()
        except Exception:
            pass

        # Save PNG button (right-aligned in toolbar frame)
        def save_png():
            fp = filedialog.asksaveasfilename(
                title="Save diagram as PNG",
                defaultextension=".png",
                filetypes=[("PNG image","*.png"),("SVG vector","*.svg"),
                           ("PDF","*.pdf"),("All","*.*")],
                initialfile="normative_diagrams.png",
            )
            if fp:
                try:
                    fig.savefig(fp, dpi=180, bbox_inches='tight', facecolor=fig.get_facecolor())
                    messagebox.showinfo("Saved", fp, parent=win)
                except Exception as e:
                    messagebox.showerror("Save error", str(e), parent=win)

        ttk.Button(toolbar_frame, text="💾 Save PNG/SVG/PDF", command=save_png).pack(
            side='right', padx=6, pady=2)

    def load_sample(self):
        dlg = tk.Toplevel(self.window)
        dlg.title("Load Sample")
        dlg.geometry("280x260")
        lb = tk.Listbox(dlg, selectmode='single')
        for s in SAMPLES: lb.insert('end', s)
        lb.pack(fill='both', expand=True, padx=8, pady=8)

        def do_load():
            sel = lb.curselection()
            if sel:
                vals = SAMPLES[lb.get(sel[0])]
                for i, ox in enumerate(OXIDES):
                    self.entries[ox].delete(0, 'end')
                    self.entries[ox].insert(0, str(vals[i] if i < len(vals) else 0.0))
                dlg.destroy()

        ttk.Button(dlg, text="Load", command=do_load).pack(pady=4)

    def export_results(self):
        if not self.results_wt:
            messagebox.showerror("Error", "No results to export"); return
        fp = filedialog.asksaveasfilename(
            defaultextension='.csv',
            filetypes=[("CSV","*.csv"),("JSON","*.json"),("Text","*.txt"),("All","*.*")])
        if not fp: return
        try:
            if fp.endswith('.json'):
                out = {
                    'method': self.method_var.get(),
                    'timestamp': pd.Timestamp.now().isoformat(),
                    'minerals': [
                        {'name': m, 'formula': (MineralDatabase.MINERALS[m].formula if m in MineralDatabase.MINERALS else ''),
                         'category': (MineralDatabase.MINERALS[m].category if m in MineralDatabase.MINERALS else ''),
                         'wt_pct': self.results_wt.get(m, 0),
                         'vol_pct': self.results_vol.get(m, 0),
                         'mol_prop': self.results_mol.get(m, 0)}
                        for m in self.results_wt
                    ]
                }
                if self.niggli: out['niggli'] = self.niggli
                with open(fp, 'w') as f: json.dump(out, f, indent=2)
            elif fp.endswith('.csv'):
                rows = []
                for m, wt in self.results_wt.items():
                    info = MineralDatabase.MINERALS.get(m)
                    rows.append({'Mineral': m,
                                 'Formula': info.formula if info else '',
                                 'Category': info.category if info else '',
                                 'Wt%': round(wt, 4),
                                 'Vol%': round(self.results_vol.get(m, 0), 4),
                                 'Mol_prop': round(self.results_mol.get(m, 0), 6)})
                pd.DataFrame(rows).to_csv(fp, index=False)
            else:
                with open(fp, 'w') as f:
                    f.write(f"Method: {self.method_var.get()}\n")
                    f.write(f"{'Mineral':<22}{'Wt%':>8}{'Vol%':>8}{'Mol':>12}\n")
                    f.write("-"*50 + "\n")
                    for m, wt in sorted(self.results_wt.items(), key=lambda x: x[1], reverse=True):
                        vol = self.results_vol.get(m, 0)
                        mol = self.results_mol.get(m, 0)
                        f.write(f"{m:<22}{wt:>8.2f}{vol:>8.2f}{mol:>12.5f}\n")
                    if self.niggli:
                        f.write("\nNiggli Numbers:\n")
                        for k, v in self.niggli.items():
                            f.write(f"  {k.upper()} = {v:.3f}\n")
            messagebox.showinfo("Exported", fp)
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def clear(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        for item in self.nig_tree.get_children(): self.nig_tree.delete(item)
        self.cls_text.delete('1.0', 'end')
        for w in self.chart_frame.winfo_children(): w.destroy()
        self.results_wt = self.results_vol = self.results_mol = self.niggli = None


def setup_plugin(main_app):
    plugin = AdvancedNormativeCalculationsPlugin(main_app)
    return plugin
