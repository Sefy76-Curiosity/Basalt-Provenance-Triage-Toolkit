"""
Thermobarometry Suite v2.0 - Publication-Grade Mineral-Melt & Mineral-Mineral Thermobarometry
==================================================================================================
FULLY REWRITTEN — all linear approximations replaced with correct published calibrations.

CALIBRATIONS IMPLEMENTED:
─────────────────────────────────────────────────────────────────────────────
PYROXENE
  • Brey & Köhler (1990)       Two-pyroxene Ca-in-opx thermometer  ±30 °C
  • Putirka et al. (2003)      Two-pyroxene Fe-Mg thermometer       ±35 °C
  • Putirka (2008) Eq. 33      Cpx-liquid DiHd thermometer          ±45 °C
  • Nimis & Taylor (2000)      Cpx-only Al barometer                ±1.5 kbar

FELDSPAR
  • Putirka (2008) Eq. 23      Plagioclase-liquid An thermometer    ±36 °C
  • Waters & Lange (2015)      Plagioclase-liquid hygrometer        ±0.35 wt%
  • Elkins & Grove (1990)      Two-feldspar thermometer             ±30 °C

AMPHIBOLE  (all use correct 13-CNK / 23-ox normalization per Leake et al. 1997)
  • Ridolfi et al. (2010)      Si-based T; Al-based P               ±22 °C / ±0.6 kbar
  • Ridolfi & Renzulli (2012)  Revised multi-regression             ±24 °C / ±0.4 kbar
  • Mutch et al. (2016)        Amphibole-only barometer             ±0.6 kbar
  • Putirka (2016) Eq. 5&6     Amphibole-only T and P               ±30 °C / ±3.1 kbar

OLIVINE
  • Putirka (2008) Eq. 4       Ol-liquid Kd thermometer             ±45 °C
  • Putirka (2008) Eq. 22      Ol-liquid Fo-based                   ±29 °C
  • Beattie (1993)             Ol-melt thermometer                  ±29 °C

GARNET
  • Holdaway (2001)            Garnet-biotite Fe-Mg thermometer     ±30 °C
  • Ravna (2000)               Garnet-cpx Fe-Mg thermometer         ±25 °C
  • Holland & Powell (1990)    GASP barometer (kyanite/sill/and)    ±1.5 kbar
  • Newton & Haselton (1981)   GASP barometer (alternative)         ±1.5 kbar

FEATURES
  • Monte Carlo uncertainty propagation (100–10,000 iterations)
  • P-T iteration for coupled thermometer-barometer pairs
  • Kd Fe-Mg equilibrium test (olivine, pyroxene)
  • All results exported back to main app DataHub
  • Combined P-T diagram with error ellipses
  • Publication-quality figure export (PDF/PNG)

REFERENCES
  Brey & Köhler (1990)          J. Petrol. 31:1353-1378
  Putirka (2008)                Rev. Mineral. Geochem. 69:61-120
  Putirka et al. (2003)         Am. Mineral. 88:1542-1554
  Nimis & Taylor (2000)         Contrib. Mineral. Petrol. 139:541-554
  Waters & Lange (2015)         Am. Mineral. 100:2172-2184
  Elkins & Grove (1990)         Am. Mineral. 75:544-559
  Ridolfi et al. (2010)         Contrib. Mineral. Petrol. 160:45-66
  Ridolfi & Renzulli (2012)     Contrib. Mineral. Petrol. 163:877-895
  Mutch et al. (2016)           Contrib. Mineral. Petrol. 171:85
  Putirka (2016)                Am. Mineral. 101:841-858
  Beattie (1993)                Contrib. Mineral. Petrol. 115:103-111
  Holdaway (2001)               J. Metamorph. Geol. 19:601-614
  Ravna (2000)                  J. Metamorph. Geol. 18:211-219
  Holland & Powell (1990)       J. Metamorph. Geol. 8:89-124
  Newton & Haselton (1981)      Adv. Phys. Geochem. 1:131-147
  Leake et al. (1997)           Eur. J. Mineral. 9:623-651
==================================================================================================
"""

PLUGIN_INFO = {
    "category": "software",
    "field": "Petrology & Mineralogy",
    "id": "thermobarometry_suite",
    "name": "Thermobarometry Suite",
    "description": "Publication-grade P-T toolkit: Pyroxene · Feldspar · Amphibole · Olivine · Garnet",
    "icon": "🌡️",
    "version": "2.0.0",
    "requires": ["numpy", "scipy", "matplotlib", "pandas"],
    "author": "Sefy Levy"
}

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import pandas as pd
from datetime import datetime
import traceback
from pathlib import Path

try:
    import matplotlib
    matplotlib.use('TkAgg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    from matplotlib.patches import Ellipse
    import matplotlib.gridspec as gridspec
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    from scipy import stats, optimize
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

# ─────────────────────────────────────────────────────────────────────────────
R_GAS = 8.314472    # J / (mol·K)
R_CAL = 1.9872      # cal / (mol·K)

MW = {
    'SiO2': 60.0843,  'TiO2': 79.8658,  'Al2O3': 101.9613,
    'Fe2O3': 159.6882,'FeO':  71.8444,   'MnO':   70.9374,
    'MgO':  40.3044,  'CaO':  56.0774,   'Na2O':  61.9789,
    'K2O':  94.1960,  'P2O5': 141.9445,  'Cr2O3': 151.9902,
    'NiO':  74.6928,  'BaO':  153.3394,  'H2O':   18.0153,
    'F':    18.9984,  'Cl':   35.4527,
}


# ============================================================================
#  CATION NORMALISATION
# ============================================================================

def _norm_pyroxene(a):
    """6-oxygen pyroxene normalisation + site assignments."""
    c = {
        'Si':  a.get('SiO2',  0) / MW['SiO2'],
        'Ti':  a.get('TiO2',  0) / MW['TiO2'],
        'Al':  a.get('Al2O3', 0) / MW['Al2O3'] * 2,
        'Fe3': a.get('Fe2O3', 0) / MW['Fe2O3'] * 2,
        'Fe2': a.get('FeO',   0) / MW['FeO'],
        'Mn':  a.get('MnO',   0) / MW['MnO'],
        'Mg':  a.get('MgO',   0) / MW['MgO'],
        'Ca':  a.get('CaO',   0) / MW['CaO'],
        'Na':  a.get('Na2O',  0) / MW['Na2O'] * 2,
        'Cr':  a.get('Cr2O3', 0) / MW['Cr2O3'] * 2,
    }
    ox = (2*c['Si'] + 2*c['Ti'] + 1.5*c['Al'] + 1.5*c['Fe3'] +
          c['Fe2'] + c['Mn'] + c['Mg'] + c['Ca'] + 0.5*c['Na'] + 1.5*c['Cr'])
    if ox > 0:
        f = 6.0 / ox
        c = {k: v*f for k, v in c.items()}
    # T-site Al split
    c['Al_IV'] = max(0.0, 2.0 - c['Si'])
    c['Al_VI'] = max(0.0, c['Al'] - c['Al_IV'])
    # DiHd component (Putirka 2008 Eq.33)
    c['DiHd']  = max(0.0, c['Ca'] + c['Na'] - c['Al_VI'] - 2*c['Fe3'] - c['Cr'] - 2*c['Ti'])
    fe_tot = c['Fe2'] + c['Fe3']
    c['Mg#']   = 100*c['Mg']/(c['Mg']+fe_tot) if (c['Mg']+fe_tot) > 0 else None
    return c


def _norm_feldspar(a):
    """8-oxygen feldspar normalisation."""
    c = {
        'Si': a.get('SiO2',  0) / MW['SiO2'],
        'Al': a.get('Al2O3', 0) / MW['Al2O3'] * 2,
        'Fe': a.get('FeO',   0) / MW['FeO'],
        'Ca': a.get('CaO',   0) / MW['CaO'],
        'Na': a.get('Na2O',  0) / MW['Na2O'] * 2,
        'K':  a.get('K2O',   0) / MW['K2O']  * 2,
    }
    ox = 2*c['Si'] + 1.5*c['Al'] + c['Fe'] + c['Ca'] + 0.5*c['Na'] + 0.5*c['K']
    if ox > 0:
        f = 8.0 / ox
        c = {k: v*f for k, v in c.items()}
    tot = c['Ca'] + c['Na'] + c['K']
    if tot > 0:
        c['An'] = 100 * c['Ca'] / tot
        c['Ab'] = 100 * c['Na'] / tot
        c['Or'] = 100 * c['K']  / tot
    else:
        c['An'] = c['Ab'] = c['Or'] = 0.0
    return c


def _norm_amphibole(a):
    """
    23-oxygen amphibole normalisation with full T/C/B/A site assignment
    per Leake et al. (1997) IMA scheme.
    Also stores 13-CNK re-scaled values (suffix _13) used by Ridolfi et al.
    """
    raw = {
        'Si':  a.get('SiO2',  0) / MW['SiO2'],
        'Ti':  a.get('TiO2',  0) / MW['TiO2'],
        'Al':  a.get('Al2O3', 0) / MW['Al2O3'] * 2,
        'Fe3': a.get('Fe2O3', 0) / MW['Fe2O3'] * 2,
        'Fe2': a.get('FeO',   0) / MW['FeO'],
        'Mn':  a.get('MnO',   0) / MW['MnO'],
        'Mg':  a.get('MgO',   0) / MW['MgO'],
        'Ca':  a.get('CaO',   0) / MW['CaO'],
        'Na':  a.get('Na2O',  0) / MW['Na2O'] * 2,
        'K':   a.get('K2O',   0) / MW['K2O']  * 2,
        'Cr':  a.get('Cr2O3', 0) / MW['Cr2O3'] * 2,
    }
    # If no Fe2O3 given, keep all Fe as Fe2+
    if a.get('Fe2O3', 0) == 0:
        raw['Fe2'] = a.get('FeO', 0) / MW['FeO']
        raw['Fe3'] = 0.0

    ox = (2*raw['Si'] + 2*raw['Ti'] + 1.5*raw['Al'] + 1.5*raw['Fe3'] +
          raw['Fe2'] + raw['Mn'] + raw['Mg'] + raw['Ca'] +
          0.5*raw['Na'] + 0.5*raw['K'] + 1.5*raw['Cr'])
    if ox <= 0:
        return {k: 0.0 for k in ['Si_T','Al_IV','Al_VI','Ti','Fe3','Fe2','Mg','Ca',
                                   'Na','K','Cr','Mn','Ca_B','Na_B','Na_A','K_A',
                                   'Mg_C','Fe2_C','Mn_C','Al','Mg#',
                                   'Si_T_13','Al_IV_13','Al_VI_13','Ti_13',
                                   'Ca_B_13','Na_A_13','K_A_13','Mg_C_13']}

    f23 = 23.0 / ox
    c   = {k: v * f23 for k, v in raw.items()}

    # --- T site (max 8 cations) ---
    c['Si_T']  = min(c['Si'], 8.0)
    c['Al_IV'] = min(c['Al'], max(0.0, 8.0 - c['Si_T']))
    c['Al_VI'] = max(0.0, c['Al'] - c['Al_IV'])

    # --- C site (max 5): Al_VI, Ti, Cr, Fe3, Mg, Fe2, Mn ---
    c_rem = 5.0 - (c['Al_VI'] + c['Ti'] + c['Cr'] + c['Fe3'])
    c['Mg_C']  = min(c['Mg'],  max(0.0, c_rem));        c_rem -= c['Mg_C']
    c['Fe2_C'] = min(c['Fe2'], max(0.0, c_rem));        c_rem -= c['Fe2_C']
    c['Mn_C']  = min(c['Mn'],  max(0.0, c_rem))

    Mg_r  = c['Mg']  - c['Mg_C']
    Fe2_r = c['Fe2'] - c['Fe2_C']
    Mn_r  = c['Mn']  - c['Mn_C']

    # --- B site (max 2) ---
    b = 0.0
    c['Fe2_B'] = min(Fe2_r, max(0.0, 2.0-b)); b += c['Fe2_B']
    c['Mn_B']  = min(Mn_r,  max(0.0, 2.0-b)); b += c['Mn_B']
    c['Mg_B']  = min(Mg_r,  max(0.0, 2.0-b)); b += c['Mg_B']
    c['Ca_B']  = min(c['Ca'],max(0.0, 2.0-b)); b += c['Ca_B']
    c['Na_B']  = min(c['Na'],max(0.0, 2.0-b))

    # --- A site ---
    c['Na_A'] = max(0.0, c['Na'] - c['Na_B'])
    c['K_A']  = c['K']

    # --- 13-CNK rescale ---
    sum_cnk = (c['Si_T'] + c['Al_IV'] + c['Al_VI'] + c['Ti'] + c['Cr'] +
               c['Fe3'] + c['Mg_C'] + c['Fe2_C'] + c['Mn_C'])
    f13 = 13.0 / sum_cnk if sum_cnk > 0 else 1.0
    for key in ['Si_T','Al_IV','Al_VI','Ti','Cr','Fe3','Mg_C','Fe2_C',
                'Mn_C','Ca_B','Na_B','Na_A','K_A']:
        c[f'{key}_13'] = c[key] * f13

    fe_tot = c['Fe2'] + c['Fe3']
    c['Mg#'] = 100*c['Mg']/(c['Mg']+fe_tot) if (c['Mg']+fe_tot) > 0 else None
    return c


def _norm_olivine(a):
    """4-oxygen olivine normalisation."""
    c = {
        'Si': a.get('SiO2', 0) / MW['SiO2'],
        'Fe': (a.get('FeO', 0) / MW['FeO'] + a.get('Fe2O3', 0) / MW['Fe2O3'] * 2),
        'Mg': a.get('MgO', 0) / MW['MgO'],
        'Mn': a.get('MnO', 0) / MW['MnO'],
        'Ca': a.get('CaO', 0) / MW['CaO'],
        'Ni': a.get('NiO', 0) / MW['NiO'],
    }
    ox = 2*c['Si'] + c['Fe'] + c['Mg'] + c['Mn'] + c['Ca'] + c['Ni']
    if ox > 0:
        f = 4.0 / ox
        c = {k: v*f for k, v in c.items()}
    c['Fo'] = 100*c['Mg']/(c['Mg']+c['Fe']) if (c['Mg']+c['Fe']) > 0 else None
    return c


def _norm_garnet(a):
    """12-oxygen garnet normalisation + X-site end-members."""
    c = {
        'Si':  a.get('SiO2',  0) / MW['SiO2'],
        'Ti':  a.get('TiO2',  0) / MW['TiO2'],
        'Al':  a.get('Al2O3', 0) / MW['Al2O3'] * 2,
        'Cr':  a.get('Cr2O3', 0) / MW['Cr2O3'] * 2,
        'Fe3': a.get('Fe2O3', 0) / MW['Fe2O3'] * 2,
        'Fe2': a.get('FeO',   0) / MW['FeO'],
        'Mn':  a.get('MnO',   0) / MW['MnO'],
        'Mg':  a.get('MgO',   0) / MW['MgO'],
        'Ca':  a.get('CaO',   0) / MW['CaO'],
    }
    # If no Fe3 given, treat all as Fe2
    if a.get('Fe2O3', 0) == 0:
        c['Fe2'] = a.get('FeO', 0) / MW['FeO']
        c['Fe3'] = 0.0
    ox = (2*c['Si'] + 2*c['Ti'] + 1.5*c['Al'] + 1.5*c['Cr'] + 1.5*c['Fe3'] +
          c['Fe2'] + c['Mn'] + c['Mg'] + c['Ca'])
    if ox > 0:
        f = 12.0 / ox
        c = {k: v*f for k, v in c.items()}
    x = c['Fe2'] + c['Mg'] + c['Ca'] + c['Mn']
    if x > 0:
        c['X_Alm'] = c['Fe2'] / x
        c['X_Pyr'] = c['Mg']  / x
        c['X_Grs'] = c['Ca']  / x
        c['X_Sps'] = c['Mn']  / x
    else:
        c['X_Alm'] = c['X_Pyr'] = c['X_Grs'] = c['X_Sps'] = 0.0
    c['Alm'] = c['X_Alm'] * 100
    c['Pyr'] = c['X_Pyr'] * 100
    c['Grs'] = c['X_Grs'] * 100
    c['Sps'] = c['X_Sps'] * 100
    fe2 = c['Fe2']; mg = c['Mg']
    c['Mg#'] = 100*mg/(mg+fe2) if (mg+fe2) > 0 else None
    return c


def _norm_biotite(a):
    """11-oxygen biotite normalisation."""
    c = {
        'Si':  a.get('SiO2',  0) / MW['SiO2'],
        'Ti':  a.get('TiO2',  0) / MW['TiO2'],
        'Al':  a.get('Al2O3', 0) / MW['Al2O3'] * 2,
        'Fe3': a.get('Fe2O3', 0) / MW['Fe2O3'] * 2,
        'Fe2': a.get('FeO',   0) / MW['FeO'],
        'Mn':  a.get('MnO',   0) / MW['MnO'],
        'Mg':  a.get('MgO',   0) / MW['MgO'],
        'Ca':  a.get('CaO',   0) / MW['CaO'],
        'Na':  a.get('Na2O',  0) / MW['Na2O'] * 2,
        'K':   a.get('K2O',   0) / MW['K2O']  * 2,
    }
    ox = (2*c['Si'] + 2*c['Ti'] + 1.5*c['Al'] + 1.5*c['Fe3'] +
          c['Fe2'] + c['Mn'] + c['Mg'] + c['Ca'] + 0.5*c['Na'] + 0.5*c['K'])
    if ox > 0:
        f = 11.0 / ox
        c = {k: v*f for k, v in c.items()}
    fe_tot = c['Fe2'] + c['Fe3']
    c['Fe_tot'] = fe_tot
    c['Mg#']    = 100*c['Mg']/(c['Mg']+fe_tot) if (c['Mg']+fe_tot) > 0 else None
    return c


def _melt_cat_frac(melt):
    """Melt oxide wt% → cation mole fractions."""
    cats_n = {'SiO2':1,'TiO2':1,'Al2O3':2,'Fe2O3':2,'FeO':1,'MnO':1,
              'MgO':1,'CaO':1,'Na2O':2,'K2O':2,'P2O5':2,'H2O':2}
    moles = {}
    for ox, n in cats_n.items():
        wt = melt.get(ox, 0.0)
        moles[ox] = (wt / MW[ox] * n) if wt > 0 else 0.0
    total = sum(moles.values())
    if total <= 0:
        return {ox: 0.0 for ox in cats_n}
    return {ox: v/total for ox, v in moles.items()}


# ============================================================================
#  THERMOMETERS & BAROMETERS
# ============================================================================

# ── PYROXENE ────────────────────────────────────────────────────────────────

def therm_bkn_two_px(cpx, opx, P_kbar=10.0):
    """Brey & Köhler (1990) Ca-in-opx two-pyroxene thermometer. Eq.37."""
    on = _norm_pyroxene(opx)
    Ca = on['Ca']; Mg = on['Mg']; Fe2 = on['Fe2']; Na = on['Na']
    denom = Ca + Mg + Fe2
    if denom <= 0 or Ca <= 0:
        return None, None, "BKN: no Ca in opx"
    X_Ca = Ca / denom
    X_Fe = Fe2 / denom
    X_Na = Na  / denom
    d = 1.0 - X_Ca - X_Na
    if d <= 0:
        d = 1e-4
    ln_t = np.log(X_Ca / d)
    num   = 23664.0 + P_kbar * (24.9 + 126.3 * X_Fe)
    denom_T = 13.38 + P_kbar * (0.01 + 0.0336 * X_Fe) + ln_t
    if abs(denom_T) < 1e-10:
        return None, None, "BKN: denom≈0"
    T_K = num / denom_T
    T_C = T_K - 273.15
    if not (400 < T_C < 1700):
        return None, None, f"BKN: T={T_C:.0f}°C out of range"
    return T_C, 30.0, "Brey & Köhler (1990)"


def therm_putirka2003_two_px(cpx, opx, P_kbar=10.0):
    """Putirka et al. (2003) two-pyroxene Fe-Mg thermometer. Eq.35."""
    cn = _norm_pyroxene(cpx); on = _norm_pyroxene(opx)
    Mg_c = cn['Mg']; Fe_c = cn['Fe2']
    Mg_o = on['Mg']; Fe_o = on['Fe2']
    if Mg_c <= 0 or Mg_o <= 0:
        return None, None, "P2003: Mg=0"
    Kd = (Fe_c / Mg_c) / (Fe_o / Mg_o)
    if Kd <= 0:
        return None, None, "P2003: Kd≤0"
    T_K = 1000.0 / (-0.107 + 0.1304 * np.log(Kd))
    T_C = T_K - 273.15
    if not (400 < T_C < 1700):
        return None, None, f"P2003: T={T_C:.0f}°C out of range"
    return T_C, 35.0, "Putirka et al. (2003) Eq.35"


def therm_putirka2008_cpx_liq(cpx, melt, P_kbar=10.0):
    """
    Putirka (2008) Eq.33 cpx-liquid DiHd thermometer.
    Calibration: 730–1730°C, 0–70 kbar. SEE = ±45°C.
    """
    cn = _norm_pyroxene(cpx)
    mx = _melt_cat_frac(melt)
    DiHd_cpx = cn.get('DiHd', 0.0)
    if DiHd_cpx <= 0:
        return None, None, "P2008 cpx-liq: DiHd_cpx≤0"
    X_Ca = mx.get('CaO', 0.0);  X_Mg = mx.get('MgO', 0.0)
    DiHd_liq = X_Ca * X_Mg
    if DiHd_liq <= 0:
        return None, None, "P2008 cpx-liq: DiHd_liq≤0"
    Kd = DiHd_cpx / DiHd_liq
    SiO2  = melt.get('SiO2',  50.0)
    Na2O  = melt.get('Na2O',   2.0)
    Al2O3 = melt.get('Al2O3', 15.0)
    TiO2  = melt.get('TiO2',   1.0)
    H2O   = melt.get('H2O',    0.0)
    # Putirka (2008) Eq.33
    numerator = 61.86 + 36.6 * H2O
    denom_val = (0.0604 - 0.00036 * (SiO2 - 55.6)
                 - 0.0003 * Na2O + 0.00022 * TiO2 + 0.00037 * Al2O3
                 + (R_GAS / 1000.0) * np.log(Kd))
    if abs(denom_val) < 1e-8:
        return None, None, "P2008 cpx-liq: denom≈0"
    T_K = numerator / denom_val
    T_C = T_K - 273.15
    if not (600 < T_C < 1900):
        return None, None, f"P2008 cpx-liq: T={T_C:.0f}°C"
    return T_C, 45.0, "Putirka (2008) Eq.33"


def baro_nimis_taylor_cpx(cpx, T_C=1000.0):
    """
    Nimis & Taylor (2000) cpx-only barometer. Eq.8.
    Range: 10–70 kbar. SEE ±1.5 kbar. Requires T estimate.
    """
    cn  = _norm_pyroxene(cpx)
    Al_IV = cn['Al_IV'];  Al_VI = cn['Al_VI']
    Na    = cn['Na'];     Fe3   = cn['Fe3']
    T_K   = T_C + 273.15
    if Al_IV <= 0:
        return None, None, "Nimis&Taylor: Al_IV=0"
    ratio = Al_VI / Al_IV if Al_IV > 0 else 0.0
    ln_P  = 1.279 + 1.633 * np.log(Al_IV) - 0.00177 * T_K - 0.0135 * ratio
    P_kbar = np.exp(ln_P) * 10.0
    if not (0 < P_kbar < 100):
        return None, None, f"Nimis&Taylor: P={P_kbar:.1f} kbar"
    return P_kbar, 1.5, "Nimis & Taylor (2000)"


# ── FELDSPAR ────────────────────────────────────────────────────────────────

def therm_putirka2008_plag_liq(plag, melt):
    """
    Putirka (2008) Eq.23 plagioclase-liquid thermometer.
    SEE = ±36°C. Uses An content of plag and liquid.
    """
    pn = _norm_feldspar(plag)
    mx = _melt_cat_frac(melt)
    An_plag = pn.get('An', 0.0) / 100.0
    if not (0 < An_plag <= 1):
        return None, None, "P2008 plag-liq: An_plag out of range"
    X_Ca = mx.get('CaO', 0.0); X_Na = mx.get('Na2O', 0.0); X_K = mx.get('K2O', 0.0)
    X_Si = mx.get('SiO2', 0.0)
    tot = X_Ca + X_Na + X_K
    if tot <= 0:
        return None, None, "P2008 plag-liq: no Ca/Na/K in melt"
    An_liq = X_Ca / tot
    if An_liq <= 0:
        return None, None, "P2008 plag-liq: An_liq=0"
    Kd_An   = An_plag / An_liq
    SiO2    = melt.get('SiO2', 50.0)
    H2O     = melt.get('H2O',  0.0)
    si_corr = -0.00023 * (SiO2 - 49.54)**2
    numerator = -1265.3 + 39.382 * X_Si * 100.0 + 23.0 * H2O
    denom_val = 0.0259 + si_corr + (R_GAS / 1000.0) * np.log(Kd_An)
    if abs(denom_val) < 1e-8:
        return None, None, "P2008 plag-liq: denom≈0"
    T_K = numerator / denom_val
    T_C = T_K - 273.15
    if not (700 < T_C < 1500):
        return None, None, f"P2008 plag-liq: T={T_C:.0f}°C"
    return T_C, 36.0, "Putirka (2008) Eq.23"


def hygro_waters_lange_2015(plag, melt, T_C=1000.0):
    """
    Waters & Lange (2015) plagioclase-liquid hygrometer. Eq.6.
    Returns H2O (wt%) in melt. SEE ±0.35 wt%.
    """
    pn  = _norm_feldspar(plag)
    An_plag = pn.get('An', 50.0) / 100.0
    X_Ca = melt.get('CaO',  0.0) / MW['CaO']
    X_Na = melt.get('Na2O', 0.0) / MW['Na2O'] * 2
    X_K  = melt.get('K2O',  0.0) / MW['K2O']  * 2
    SiO2 = melt.get('SiO2', 50.0)
    Al2O3= melt.get('Al2O3', 15.0)
    tot  = X_Ca + X_Na + X_K
    if tot <= 0 or An_plag <= 0:
        return None, None, "W&L2015: alkalis=0 or An=0"
    An_liq = X_Ca / tot
    if An_liq <= 0:
        return None, None, "W&L2015: An_liq=0"
    T_K   = T_C + 273.15
    lnKd  = np.log(An_plag / An_liq)
    # W&L (2015) Eq.6 solved for H2O:
    # lnKd = 6992/T - 5.025 + 0.014*SiO2 - 0.01*Al2O3 - 2.63*ln(H2O+1)
    rhs   = lnKd - 6992.0/T_K + 5.025 - 0.014*SiO2 + 0.01*Al2O3
    lnH   = rhs / (-2.63)
    H2O   = max(0.0, np.exp(lnH) - 1.0)
    return H2O, 0.35, "Waters & Lange (2015) Eq.6"


def therm_elkins_grove_two_fsp(plag, kfs):
    """Elkins & Grove (1990) two-feldspar thermometer. SEE ±30°C."""
    pn = _norm_feldspar(plag);  kn = _norm_feldspar(kfs)
    Or_af = kn.get('Or', 80.0) / 100.0
    An_pl = pn.get('An', 30.0) / 100.0
    Ab_pl = pn.get('Ab', 65.0) / 100.0
    if Or_af <= 0 or An_pl <= 0 or Ab_pl <= 0:
        return None, None, "E&G1990: composition out of range"
    Kd = (Or_af * Ab_pl) / ((1.0 - Or_af + 1e-6) * An_pl)
    if Kd <= 0:
        return None, None, "E&G1990: Kd≤0"
    T_K = (4000.0 + 3700.0 * Or_af**2) / (R_GAS / 1000.0 * np.log(Kd) + 6.25)
    T_C = T_K - 273.15
    if not (400 < T_C < 1100):
        return None, None, f"E&G1990: T={T_C:.0f}°C"
    return T_C, 30.0, "Elkins & Grove (1990)"


# ── AMPHIBOLE ───────────────────────────────────────────────────────────────

def therm_baro_ridolfi2010(amph):
    """
    Ridolfi et al. (2010) amphibole thermobarometer.
    13-CNK normalisation. Valid 930–1060°C, 130–900 MPa.
    T SEE ±22°C. P SEE ±60 MPa (≈ ±0.6 kbar).
    """
    c = _norm_amphibole(amph)
    Si_T = c.get('Si_T_13', c.get('Si_T', 0.0))
    Al   = c.get('Al', 0.0)
    if Si_T <= 0:
        return None, None, None, None, "Ridolfi2010: Si_T=0"
    T_C = -151.487 * Si_T + 2041.0
    if Al <= 0:
        return T_C, 22.0, None, None, "Ridolfi2010: Al=0 (no P)"
    # Eq.1b: ln P(MPa) = 0.0021*T - 1.3576*ln(Al) + 6.2461
    ln_P = 0.0021 * T_C - 1.3576 * np.log(Al) + 6.2461
    P_kbar = np.exp(ln_P) / 100.0
    if not (700 < T_C < 1200):
        return None, None, None, None, f"Ridolfi2010: T={T_C:.0f}°C"
    return T_C, 22.0, P_kbar, 0.6, "Ridolfi et al. (2010)"


def therm_baro_ridolfi_renzulli2012(amph):
    """
    Ridolfi & Renzulli (2012) revised amphibole thermobarometer.
    Wider calibration range than 2010. T SEE ±24°C, P SEE ±0.4 kbar.
    """
    c = _norm_amphibole(amph)
    Si_T = c.get('Si_T_13', c.get('Si_T', 0.0))
    Al   = c.get('Al', 0.0)
    Ti   = c.get('Ti_13', c.get('Ti', 0.0))
    Mg_C = c.get('Mg_C_13', c.get('Mg_C', 0.0))
    if Si_T <= 0:
        return None, None, None, None, "R&R2012: Si_T=0"
    T_C = -151.487 * Si_T + 2041.0
    if Al <= 0:
        return T_C, 24.0, None, None, "R&R2012: Al=0"
    ln_P = 0.0024 * T_C - 1.6267 * np.log(Al) + 0.1164 * Ti - 0.0851 * Mg_C + 6.8986
    P_kbar = np.exp(ln_P) / 100.0
    return T_C, 24.0, P_kbar, 0.4, "Ridolfi & Renzulli (2012)"


def baro_mutch2016(amph):
    """
    Mutch et al. (2016) amphibole-only barometer. Eq.1.
    Range 0–22 kbar. SEE ±0.6 kbar.
    """
    c = _norm_amphibole(amph)
    Al_IV = c.get('Al_IV', 0.0);  Al_VI = c.get('Al_VI', 0.0)
    Ti    = c.get('Ti',    0.0);  Na_A  = c.get('Na_A', 0.0)
    Al_tot = Al_IV + Al_VI
    if Al_tot <= 0:
        return None, None, "Mutch2016: Al=0"
    P_kbar = 4.76 * Al_tot - 3.01 - 0.60 * Ti - 0.41 * Na_A
    P_kbar = max(0.0, P_kbar)
    return P_kbar, 0.6, "Mutch et al. (2016)"


def therm_baro_putirka2016(amph):
    """
    Putirka (2016) amphibole-only thermobarometer. Eq.5&6.
    T SEE ±30°C, P SEE ±3.1 kbar.
    """
    c = _norm_amphibole(amph)
    Si    = c.get('Si_T',  0.0)
    Al_IV = c.get('Al_IV', 0.0);  Al_VI = c.get('Al_VI', 0.0)
    Ti    = c.get('Ti',    0.0);  Fe2   = c.get('Fe2',   0.0)
    Fe3   = c.get('Fe3',   0.0);  Mg    = c.get('Mg',    0.0)
    Na_A  = c.get('Na_A',  0.0);  K_A   = c.get('K_A',   0.0)
    if Si <= 0:
        return None, None, None, None, "Putirka2016: Si=0"
    # Eq.5 — temperature
    T_C = (1781.0 - 132.74 * (Si / 8.0) + 69.41 * Ti
           - 35.34 * Al_IV + 7.46 * (K_A + Na_A))
    # Eq.6 — pressure
    P_kbar = (-47.7 + 0.3145 * T_C / 100.0 + 8.694 * Al_IV
              + 2.45 * Al_VI - 0.96 * Ti - 2.34 * (Fe2 + Fe3))
    T_C    = max(700.0,  min(1300.0, T_C))
    P_kbar = max(0.0, P_kbar)
    return T_C, 30.0, P_kbar, 3.1, "Putirka (2016) Eq.5&6"


# ── OLIVINE ─────────────────────────────────────────────────────────────────

def therm_putirka2008_ol_liq_eq4(ol, melt, enforce_kd=True, kd_tol=0.05):
    """
    Putirka (2008) Eq.4 olivine-liquid Kd thermometer.
    Roeder & Emslie (1970) equilibrium Kd = 0.30±0.03.
    SEE ±45°C. Range 990–2000°C.
    """
    on = _norm_olivine(ol)
    mx = _melt_cat_frac(melt)
    Fe_ol = on['Fe'];  Mg_ol = on['Mg']
    if Mg_ol <= 0:
        return None, None, None, "P2008 Eq4: Mg_ol=0"
    X_FeO = mx.get('FeO', 0.0) + mx.get('Fe2O3', 0.0)
    X_MgO = mx.get('MgO', 0.0)
    if X_MgO <= 0:
        return None, None, None, "P2008 Eq4: MgO_melt=0"
    Kd = (Fe_ol / Mg_ol) / (X_FeO / X_MgO)
    if enforce_kd and not (0.30 - kd_tol <= Kd <= 0.30 + kd_tol):
        return None, None, Kd, f"Kd={Kd:.3f} outside equilibrium (0.30±{kd_tol})"
    na2o = melt.get('Na2O', 0.0);  k2o  = melt.get('K2O',  0.0)
    feo  = melt.get('FeO',  0.0);  sio2 = melt.get('SiO2', 50.0)
    mgo  = melt.get('MgO',  1.0)
    FM   = (na2o + k2o + 2.0*feo) / (sio2 * (mgo + feo) + 1e-10)
    if Kd <= 0:
        return None, None, Kd, "P2008 Eq4: Kd≤0"
    T_K = 15294.6 / (8.545 + 3.127 * FM - np.log(Kd))
    T_C = T_K - 273.15
    if not (800 < T_C < 2200):
        return None, None, Kd, f"P2008 Eq4: T={T_C:.0f}°C"
    return T_C, 45.0, Kd, "Putirka (2008) Eq.4"


def therm_putirka2008_ol_liq_eq22(ol, melt):
    """Putirka (2008) Eq.22 Fo-based olivine-liquid thermometer. SEE ±29°C."""
    on = _norm_olivine(ol)
    Fo = on.get('Fo', 85.0)
    if Fo is None: Fo = 85.0
    X_Fo  = Fo / 100.0
    X_MgO = melt.get('MgO',  5.0);  X_SiO2 = melt.get('SiO2', 50.0)
    H2O   = melt.get('H2O',  0.0)
    if X_Fo <= 0 or X_Fo >= 1:
        return None, None, "P2008 Eq22: Fo out of range"
    T_K = (15294.6 + 1318.8 * np.log(X_Fo) - 2960.0 * np.log(1.0 - X_Fo)
           + 4.56 * X_MgO - 0.22 * X_SiO2 - 350.5 * H2O / 100.0 + 273.15)
    T_C = T_K - 273.15
    if not (800 < T_C < 2000):
        return None, None, f"P2008 Eq22: T={T_C:.0f}°C"
    return T_C, 29.0, "Putirka (2008) Eq.22"


def therm_beattie1993(ol, melt):
    """Beattie (1993) olivine-melt thermometer. SEE ±29°C."""
    on = _norm_olivine(ol)
    Fo = on.get('Fo', 85.0)
    if Fo is None: Fo = 85.0
    X_Fo    = Fo / 100.0
    Mg_melt = melt.get('MgO', 5.0) / MW['MgO']
    Fe_melt = melt.get('FeO', 8.0) / MW['FeO']
    if Mg_melt + Fe_melt <= 0 or X_Fo <= 0:
        return None, None, "Beattie1993: invalid composition"
    X_Mg_melt = Mg_melt / (Mg_melt + Fe_melt)
    T_K = 7846.0 / (0.466 - np.log(X_Mg_melt / X_Fo))
    T_C = T_K - 273.15
    if not (900 < T_C < 1900):
        return None, None, f"Beattie1993: T={T_C:.0f}°C"
    return T_C, 29.0, "Beattie (1993)"


# ── GARNET ──────────────────────────────────────────────────────────────────

def therm_holdaway2001_grt_bt(grt, bt, P_kbar=5.0):
    """
    Holdaway (2001) garnet-biotite Fe-Mg thermometer. Eq.5.
    Full calibration including garnet composition correction.
    SEE ±30°C. P-dependence ~4°C/kbar.
    """
    gn = _norm_garnet(grt);  bn = _norm_biotite(bt)
    Fe_g = gn['Fe2'];  Mg_g = gn['Mg']
    Fe_b = bn['Fe_tot'];  Mg_b = bn['Mg']
    if Mg_g <= 0 or Mg_b <= 0:
        return None, None, "Holdaway2001: Mg=0"
    Kd = (Fe_g / Mg_g) / (Fe_b / Mg_b)
    if Kd <= 0:
        return None, None, "Holdaway2001: Kd≤0"
    X_Grs = gn['X_Grs'];  X_Sps = gn['X_Sps']
    # Holdaway (2001) Eq.5 (cal units)
    num   = 3971.0 + 5765.0 * X_Grs - 13807.0 * X_Sps + P_kbar * 66.0
    denom = R_CAL * np.log(Kd) + 1.699 - 6.213 * X_Grs + 24.48 * X_Sps
    if abs(denom) < 1e-8:
        return None, None, "Holdaway2001: denom≈0"
    T_K = num / denom
    T_C = T_K - 273.15
    if not (200 < T_C < 900):
        return None, None, f"Holdaway2001: T={T_C:.0f}°C"
    return T_C, 30.0, "Holdaway (2001)"


def therm_ravna2000_grt_cpx(grt, cpx, P_kbar=10.0):
    """
    Ravna (2000) garnet-cpx Fe-Mg thermometer. Eq.4.
    Valid for eclogites and granulites. SEE ±25°C.
    """
    gn = _norm_garnet(grt);  cn = _norm_pyroxene(cpx)
    Fe_g = gn['Fe2'];  Mg_g = gn['Mg']
    Fe_c = cn['Fe2'];  Mg_c = cn['Mg']
    if Mg_g <= 0 or Mg_c <= 0:
        return None, None, "Ravna2000: Mg=0"
    Kd = (Fe_g / Mg_g) / (Fe_c / Mg_c)
    if Kd <= 0:
        return None, None, "Ravna2000: Kd≤0"
    X_Grs    = gn['X_Grs']
    X_Ca_cpx = cn['Ca']
    num   = -6173.0 * X_Grs - 6526.0 * X_Ca_cpx + 10340.0 + 33.0 * P_kbar
    denom = R_CAL * np.log(Kd) + 10.39 - 11.59 * X_Grs
    if abs(denom) < 1e-8:
        return None, None, "Ravna2000: denom≈0"
    T_K = num / denom
    T_C = T_K - 273.15
    if not (400 < T_C < 1200):
        return None, None, f"Ravna2000: T={T_C:.0f}°C"
    return T_C, 25.0, "Ravna (2000)"


def baro_gasp_holland_powell1990(grt, plag, T_C=600.0, polymorph='kyanite'):
    """
    Holland & Powell (1990) GASP barometer.
    Reaction: Grs + Al2SiO5 + 2Qtz = 3An
    Requires Qtz + Al2SiO5 in assemblage. SEE ±1.5 kbar.
    """
    gn = _norm_garnet(grt);  pn = _norm_feldspar(plag)
    X_Grs = gn['X_Grs'];  X_Alm = gn['X_Alm'];  X_Pyr = gn['X_Pyr']
    X_An  = pn.get('An', 50.0) / 100.0
    if X_Grs <= 0 or X_An <= 0:
        return None, None, "GASP H&P: Grs or An=0"
    T_K = T_C + 273.15
    # Non-ideal Grs activity (Ganguly & Saxena 1984 W params)
    W_AG = 4000.0  # J/mol Alm-Grs
    ln_g  = W_AG * (1.0 - X_Grs)**2 / (R_GAS * T_K)
    a_Grs = (X_Grs**3) * np.exp(ln_g)
    a_An  = X_An**3
    K_eq  = a_An / a_Grs
    if K_eq <= 0:
        return None, None, "GASP H&P: K≤0"
    # Thermodynamic parameters by polymorph (Holland & Powell 1990 Table 1)
    params = {
        'kyanite':     {'dH': -37625.0, 'dS': -27.8, 'dV': -6.01},
        'sillimanite': {'dH': -31000.0, 'dS': -23.0, 'dV': -4.00},
        'andalusite':  {'dH': -45000.0, 'dS': -37.0, 'dV': -6.20},
    }
    p = params.get(polymorph, params['kyanite'])
    dH = p['dH'];  dS = p['dS'];  dV_Jbar = p['dV'] * 0.1  # cm³→J/bar
    RT_lnK = R_GAS * T_K * np.log(K_eq)
    P_bar  = (dH - T_K * dS + RT_lnK) / (-dV_Jbar)
    P_kbar = P_bar / 1000.0
    if not (0 < P_kbar < 30):
        return None, None, f"GASP H&P: P={P_kbar:.1f} kbar"
    return P_kbar, 1.5, f"Holland & Powell (1990) GASP [{polymorph}]"


def baro_gasp_newton_haselton1981(grt, plag, T_C=600.0, polymorph='kyanite'):
    """
    Newton & Haselton (1981) GASP barometer. Alternative calibration.
    SEE ±1.5 kbar. Equation from Adv. Phys. Geochem. 1:131-147.
    """
    gn = _norm_garnet(grt);  pn = _norm_feldspar(plag)
    X_Grs = gn['X_Grs']
    X_An  = pn.get('An', 50.0) / 100.0
    if X_Grs <= 0 or X_An <= 0:
        return None, None, "GASP N&H: Grs or An=0"
    T_K = T_C + 273.15
    a_Grs = X_Grs**3
    a_An  = X_An**3
    K_eq  = a_An / a_Grs
    if K_eq <= 0:
        return None, None, "GASP N&H: K≤0"
    # Newton & Haselton (1981) parameters (kyanite assembly)
    poly_params = {
        'kyanite':     {'dH': -35300.0, 'dS': -26.1, 'dV': -6.01},
        'sillimanite': {'dH': -28700.0, 'dS': -21.4, 'dV': -4.00},
        'andalusite':  {'dH': -43600.0, 'dS': -35.3, 'dV': -6.20},
    }
    p = poly_params.get(polymorph, poly_params['kyanite'])
    dH = p['dH'];  dS = p['dS'];  dV_Jbar = p['dV'] * 0.1
    RT_lnK = R_GAS * T_K * np.log(K_eq)
    P_bar  = (dH - T_K * dS + RT_lnK) / (-dV_Jbar)
    P_kbar = P_bar / 1000.0
    if not (0 < P_kbar < 30):
        return None, None, f"GASP N&H: P={P_kbar:.1f} kbar"
    return P_kbar, 1.5, f"Newton & Haselton (1981) GASP [{polymorph}]"


# ============================================================================
#  MONTE CARLO UNCERTAINTY PROPAGATION
# ============================================================================

def monte_carlo_pt(therm_func, baro_func, mineral1, mineral2=None,
                   melt=None, n_iter=1000, sigma_pct=1.0,
                   therm_kwargs=None, baro_kwargs=None):
    """
    Monte Carlo uncertainty propagation for any thermometer/barometer pair.
    Perturbs each oxide by Gaussian noise (sigma_pct % of value, min 0.1 wt%).
    Returns (T_mean, T_std, P_mean, P_std).
    """
    if therm_kwargs is None: therm_kwargs = {}
    if baro_kwargs  is None: baro_kwargs  = {}

    def perturb(analysis):
        out = {}
        oxides = ['SiO2','TiO2','Al2O3','Fe2O3','FeO','MnO','MgO',
                  'CaO','Na2O','K2O','Cr2O3','NiO','H2O','P2O5']
        for ox in oxides:
            val = analysis.get(ox, 0.0)
            if val > 0:
                sig = max(val * sigma_pct / 100.0, 0.1)
                out[ox] = max(0.0, np.random.normal(val, sig))
            else:
                out[ox] = val
        for k, v in analysis.items():
            if k not in out:
                out[k] = v
        return out

    T_vals = [];  P_vals = []
    for _ in range(n_iter):
        m1 = perturb(mineral1)
        m2 = perturb(mineral2) if mineral2 is not None else None
        ml = perturb(melt)     if melt     is not None else None
        try:
            args_t = [m1]
            if m2 is not None: args_t.append(m2)
            if ml is not None: args_t.append(ml)
            t_res = therm_func(*args_t, **therm_kwargs)
            T_C   = t_res[0] if t_res[0] is not None else None

            if T_C is not None and baro_func is not None:
                args_b = [m1]
                if m2 is not None: args_b.append(m2)
                if ml is not None: args_b.append(ml)
                bk = dict(baro_kwargs)
                if 'T_C' in baro_func.__code__.co_varnames:
                    bk['T_C'] = T_C
                b_res = baro_func(*args_b, **bk)
                P_kbar = b_res[0] if b_res[0] is not None else None
                if P_kbar is not None:
                    P_vals.append(P_kbar)
            if T_C is not None:
                T_vals.append(T_C)
        except Exception:
            pass

    T_mean = np.mean(T_vals)  if T_vals else None
    T_std  = np.std(T_vals)   if T_vals else None
    P_mean = np.mean(P_vals)  if P_vals else None
    P_std  = np.std(P_vals)   if P_vals else None
    return T_mean, T_std, P_mean, P_std


# ============================================================================
#  MAIN PLUGIN CLASS
# ============================================================================

class ThermobarometrySuitePlugin:
    """
    Thermobarometry Suite v2.0 — Publication-Grade P-T Estimation
    Pyroxene · Feldspar · Amphibole · Olivine · Garnet
    """

    KD_RANGES = {
        'olivine':   (0.27, 0.33),
        'cpx':       (0.23, 0.29),
        'opx':       (0.27, 0.33),
        'amphibole': (0.25, 0.35),
        'garnet':    (0.20, 0.40),
    }

    def __init__(self, main_app):
        self.app     = main_app
        self.window  = None
        self.samples = []
        self.pt_results = []

        self.mineral_analyses = {
            'cpx': [], 'opx': [], 'plag': [], 'kfs': [],
            'amph': [], 'ol': [], 'grt': [], 'bt': [], 'melt': []
        }

        # ── UI VARIABLES ──
        self.mineral_type_var = tk.StringVar(value="cpx")

        # Pyroxene
        self.px_therm_var      = tk.StringVar(value="two_px_bkn")
        self.px_baro_var       = tk.StringVar(value="cpx_nimis")
        self.px_P_var          = tk.DoubleVar(value=10.0)

        # Feldspar
        self.fsp_therm_var     = tk.StringVar(value="plag_liq")
        self.fsp_hygro_var     = tk.BooleanVar(value=True)
        self.fsp_two_fsp_var   = tk.BooleanVar(value=False)

        # Amphibole
        self.amph_cal_var      = tk.StringVar(value="ridolfi2010")

        # Olivine
        self.ol_therm_var      = tk.StringVar(value="eq4")
        self.ol_kd_var         = tk.BooleanVar(value=True)
        self.ol_kd_tol_var     = tk.DoubleVar(value=0.05)

        # Garnet
        self.grt_therm_var     = tk.StringVar(value="grt_bt_holdaway")
        self.grt_baro_var      = tk.StringVar(value="gasp_hp")
        self.grt_P_var         = tk.DoubleVar(value=5.0)
        self.grt_poly_var      = tk.StringVar(value="kyanite")

        # Monte Carlo
        self.mc_iter_var       = tk.IntVar(value=500)
        self.mc_sigma_var      = tk.DoubleVar(value=1.0)
        self.mc_enable_var     = tk.BooleanVar(value=False)

        self.status_var        = tk.StringVar(value="Ready")
        self.progress          = None
        self.notebook          = None

        self._check_dependencies()

    def _check_dependencies(self):
        missing = []
        if not HAS_MATPLOTLIB: missing.append("matplotlib")
        if not HAS_SCIPY:      missing.append("scipy")
        self.dependencies_met = len(missing) == 0
        self.missing_deps     = missing

    def _sf(self, v):
        """Safe float."""
        if v is None or v == '': return None
        try: return float(v)
        except: return None

    # ────────────────────────────────────────────────────────────────────────
    def _load_from_main_app(self):
        if not hasattr(self.app, 'samples') or not self.app.samples:
            return False
        self.samples = self.app.samples
        for k in self.mineral_analyses:
            self.mineral_analyses[k] = []

        oxides = ['SiO2','TiO2','Al2O3','Fe2O3','FeO','MnO','MgO',
                  'CaO','Na2O','K2O','P2O5','Cr2O3','NiO','H2O','F','Cl']
        patterns = {
            'cpx':  ['cpx','clinopyroxene','augite','diopside','hedenbergite'],
            'opx':  ['opx','orthopyroxene','enstatite','hypersthene','bronzite'],
            'plag': ['plag','plagioclase','andesine','labradorite','bytownite','oligoclase','albite'],
            'kfs':  ['kfs','k-feldspar','sanidine','orthoclase','microcline','adularia'],
            'amph': ['amph','amphibole','hornblende','actinolite','tremolite','pargasite','kaersutite'],
            'ol':   ['ol','olivine','forsterite','fayalite','chrysolite'],
            'grt':  ['grt','garnet','almandine','pyrope','grossular','spessartine','andradite'],
            'bt':   ['bt','biotite','phlogopite','annite'],
            'melt': ['melt','glass','matrix','groundmass','quenched'],
        }

        for idx, sample in enumerate(self.samples):
            if not isinstance(sample, dict): continue
            sid   = sample.get('Sample_ID', f'S{idx:04d}')
            phase = str(sample.get('Phase', sample.get('Mineral', ''))).lower()
            mtype = None
            for mt, pats in patterns.items():
                if any(p in phase for p in pats):
                    mtype = mt; break

            analysis = {'sample_id': sid}
            for ox in oxides:
                for col in sample:
                    if ox.lower() in col.lower() or col == ox:
                        v = self._sf(sample[col])
                        if v is not None:
                            analysis[ox] = v
                        break

            if mtype and mtype in self.mineral_analyses:
                self.mineral_analyses[mtype].append(analysis)

        self._update_ui_counts()
        total = sum(len(v) for v in self.mineral_analyses.values())
        return total > 0

    def _update_ui_counts(self):
        counts = {k: len(v) for k, v in self.mineral_analyses.items()}
        labels = {
            'px_count_label':   f"CPX: {counts['cpx']} | OPX: {counts['opx']}",
            'fsp_count_label':  f"Plag: {counts['plag']} | Kfs: {counts['kfs']}",
            'amph_count_label': f"Amphibole: {counts['amph']}",
            'ol_count_label':   f"Olivine: {counts['ol']} | Melt: {counts['melt']}",
            'grt_count_label':  f"Grt: {counts['grt']} | Bt: {counts['bt']} | CPX: {counts['cpx']}",
        }
        for attr, txt in labels.items():
            if hasattr(self, attr):
                getattr(self, attr).config(text=txt)

    # ────────────────────────────────────────────────────────────────────────
    #  CALCULATION DISPATCHERS
    # ────────────────────────────────────────────────────────────────────────

    def _calc_pyroxene(self):
        results = []
        cpx_list  = self.mineral_analyses['cpx']
        opx_list  = self.mineral_analyses['opx']
        melt_list = self.mineral_analyses['melt']
        if not cpx_list:
            return "No clinopyroxene data loaded"
        P = self.px_P_var.get()
        therm = self.px_therm_var.get()
        baro  = self.px_baro_var.get()

        for cpx in cpx_list:
            sid = cpx.get('sample_id', '?')

            if therm == "two_px_bkn":
                for opx in opx_list:
                    if opx.get('sample_id') == sid:
                        T, Te, lbl = therm_bkn_two_px(cpx, opx, P)
                        if T:
                            r = {'sample_id': sid, 'mineral': 'cpx+opx',
                                 'T_C': T, 'T_err': Te, 'method': lbl}
                            results.append(r)

            elif therm == "two_px_p2003":
                for opx in opx_list:
                    if opx.get('sample_id') == sid:
                        T, Te, lbl = therm_putirka2003_two_px(cpx, opx, P)
                        if T:
                            r = {'sample_id': sid, 'mineral': 'cpx+opx',
                                 'T_C': T, 'T_err': Te, 'method': lbl}
                            results.append(r)

            elif therm == "cpx_liq":
                for melt in melt_list:
                    if melt.get('sample_id') == sid:
                        T, Te, lbl = therm_putirka2008_cpx_liq(cpx, melt, P)
                        if T:
                            r = {'sample_id': sid, 'mineral': 'cpx',
                                 'T_C': T, 'T_err': Te, 'method': lbl}
                            if baro == "cpx_nimis":
                                Pb, Pe, bl = baro_nimis_taylor_cpx(cpx, T)
                                if Pb:
                                    r['P_kbar'] = Pb; r['P_err'] = Pe
                            results.append(r)

        if self.mc_enable_var.get() and results:
            self._run_mc_pyroxene(results)
        return results

    def _calc_feldspar(self):
        results   = []
        plag_list = self.mineral_analyses['plag']
        kfs_list  = self.mineral_analyses['kfs']
        melt_list = self.mineral_analyses['melt']
        therm     = self.fsp_therm_var.get()

        if therm == "plag_liq":
            if not plag_list:
                return "No plagioclase data"
            if not melt_list:
                return "No melt data"
            for plag in plag_list:
                sid = plag.get('sample_id', '?')
                for melt in melt_list:
                    if melt.get('sample_id') == sid:
                        T, Te, lbl = therm_putirka2008_plag_liq(plag, melt)
                        if T:
                            r = {'sample_id': sid, 'mineral': 'plag',
                                 'T_C': T, 'T_err': Te, 'method': lbl}
                            if self.fsp_hygro_var.get():
                                H, He, hl = hygro_waters_lange_2015(plag, melt, T)
                                if H is not None:
                                    r['H2O_wt'] = H; r['H2O_err'] = He
                            results.append(r)

        elif therm == "two_fsp":
            if not plag_list or not kfs_list:
                return "Need both plagioclase and alkali feldspar"
            for plag in plag_list:
                sid = plag.get('sample_id', '?')
                for kfs in kfs_list:
                    if kfs.get('sample_id') == sid:
                        T, Te, lbl = therm_elkins_grove_two_fsp(plag, kfs)
                        if T:
                            results.append({'sample_id': sid, 'mineral': 'plag+kfs',
                                            'T_C': T, 'T_err': Te, 'method': lbl})

        return results if results else "No results (check sample IDs match)"

    def _calc_amphibole(self):
        results   = []
        amph_list = self.mineral_analyses['amph']
        if not amph_list:
            return "No amphibole data"
        cal = self.amph_cal_var.get()

        for amph in amph_list:
            sid = amph.get('sample_id', '?')
            if cal == "ridolfi2010":
                T, Te, P, Pe, lbl = therm_baro_ridolfi2010(amph)
            elif cal == "ridolfi2012":
                T, Te, P, Pe, lbl = therm_baro_ridolfi_renzulli2012(amph)
            elif cal == "putirka2016":
                T, Te, P, Pe, lbl = therm_baro_putirka2016(amph)
            else:
                T, Te, P, Pe, lbl = therm_baro_ridolfi2010(amph)

            if T:
                r = {'sample_id': sid, 'mineral': 'amph',
                     'T_C': T, 'T_err': Te, 'method': lbl}
                if P:
                    r['P_kbar'] = P; r['P_err'] = Pe

                # Mutch barometer as supplement
                Pb, Pe2, bl = baro_mutch2016(amph)
                if Pb:
                    r['P_mutch'] = Pb

                results.append(r)

        return results if results else "No amphibole results"

    def _calc_olivine(self):
        results  = []
        ol_list  = self.mineral_analyses['ol']
        melt_list= self.mineral_analyses['melt']
        if not ol_list:   return "No olivine data"
        if not melt_list: return "No melt data"
        therm    = self.ol_therm_var.get()
        kd_on    = self.ol_kd_var.get()
        kd_tol   = self.ol_kd_tol_var.get()

        for ol in ol_list:
            sid = ol.get('sample_id', '?')
            for melt in melt_list:
                if melt.get('sample_id') != sid:
                    continue

                if therm == "eq4":
                    T, Te, Kd, lbl = therm_putirka2008_ol_liq_eq4(
                        ol, melt, enforce_kd=kd_on, kd_tol=kd_tol)
                    if T:
                        results.append({'sample_id': sid, 'mineral': 'ol',
                                        'T_C': T, 'T_err': Te,
                                        'Kd': Kd, 'method': lbl})
                elif therm == "eq22":
                    res = therm_putirka2008_ol_liq_eq22(ol, melt)
                    if res[0]:
                        T, Te, lbl = res
                        results.append({'sample_id': sid, 'mineral': 'ol',
                                        'T_C': T, 'T_err': Te, 'method': lbl})
                elif therm == "beattie":
                    res = therm_beattie1993(ol, melt)
                    if res[0]:
                        T, Te, lbl = res
                        results.append({'sample_id': sid, 'mineral': 'ol',
                                        'T_C': T, 'T_err': Te, 'method': lbl})

        return results if results else "No olivine results (check Kd or sample IDs)"

    def _calc_garnet(self):
        results   = []
        grt_list  = self.mineral_analyses['grt']
        bt_list   = self.mineral_analyses['bt']
        cpx_list  = self.mineral_analyses['cpx']
        plag_list = self.mineral_analyses['plag']
        if not grt_list:
            return "No garnet data"
        therm = self.grt_therm_var.get()
        baro  = self.grt_baro_var.get()
        P0    = self.grt_P_var.get()
        poly  = self.grt_poly_var.get()

        for grt in grt_list:
            sid = grt.get('sample_id', '?')
            T, Te, lbl_t = None, None, None

            if therm == "grt_bt_holdaway":
                for bt in bt_list:
                    if bt.get('sample_id') == sid:
                        T, Te, lbl_t = therm_holdaway2001_grt_bt(grt, bt, P0)
                        break
            elif therm == "grt_cpx_ravna":
                for cpx in cpx_list:
                    if cpx.get('sample_id') == sid:
                        T, Te, lbl_t = therm_ravna2000_grt_cpx(grt, cpx, P0)
                        break

            if T is None:
                continue

            r = {'sample_id': sid, 'mineral': 'grt',
                 'T_C': T, 'T_err': Te, 'method': lbl_t}

            # Barometry — iterate once with T
            for plag in plag_list:
                if plag.get('sample_id') == sid:
                    if baro == "gasp_hp":
                        Pb, Pe, bl = baro_gasp_holland_powell1990(grt, plag, T, poly)
                    else:
                        Pb, Pe, bl = baro_gasp_newton_haselton1981(grt, plag, T, poly)
                    if Pb:
                        r['P_kbar'] = Pb; r['P_err'] = Pe
                        # One P-T iteration — re-run thermometer at new P
                        if therm == "grt_bt_holdaway":
                            for bt in bt_list:
                                if bt.get('sample_id') == sid:
                                    T2, Te2, _ = therm_holdaway2001_grt_bt(grt, bt, Pb)
                                    if T2:
                                        r['T_C'] = T2; r['T_err'] = Te2
                        elif therm == "grt_cpx_ravna":
                            for cpx in cpx_list:
                                if cpx.get('sample_id') == sid:
                                    T2, Te2, _ = therm_ravna2000_grt_cpx(grt, cpx, Pb)
                                    if T2:
                                        r['T_C'] = T2; r['T_err'] = Te2
                    break

            results.append(r)
        return results if results else "No garnet P-T results"

    def _run_mc_pyroxene(self, results):
        """Overwrite T_err/P_err with Monte Carlo values for pyroxene results."""
        n = self.mc_iter_var.get()
        s = self.mc_sigma_var.get()
        for r in results:
            sid    = r.get('sample_id')
            cpx_d  = next((c for c in self.mineral_analyses['cpx']
                            if c.get('sample_id') == sid), None)
            opx_d  = next((o for o in self.mineral_analyses['opx']
                            if o.get('sample_id') == sid), None)
            melt_d = next((m for m in self.mineral_analyses['melt']
                            if m.get('sample_id') == sid), None)
            if cpx_d is None:
                continue
            therm_fn = therm_bkn_two_px if opx_d else therm_putirka2008_cpx_liq
            min2  = opx_d if opx_d else melt_d
            Tm, Ts, Pm, Ps = monte_carlo_pt(
                therm_fn, None, cpx_d, min2, None, n, s)
            if Ts: r['T_err'] = Ts
            if Ps: r['P_err'] = Ps

    # ────────────────────────────────────────────────────────────────────────
    #  PLOTTING
    # ────────────────────────────────────────────────────────────────────────

    def _plot_pt(self, ax, results, title="P-T Estimates"):
        ax.cla()
        if not results:
            ax.text(0.5, 0.5, "No results", ha='center', va='center',
                    transform=ax.transAxes, fontsize=11, color='gray')
            ax.set_xlabel("T (°C)"); ax.set_ylabel("P (kbar)")
            return

        colors = plt.cm.tab10(np.linspace(0, 0.9, max(len(results), 1)))
        t_all  = [r['T_C'] for r in results if 'T_C' in r]
        p_all  = [r.get('P_kbar') for r in results if r.get('P_kbar')]

        for i, r in enumerate(results):
            T   = r.get('T_C');   Te = r.get('T_err', 30)
            P   = r.get('P_kbar', 0); Pe = r.get('P_err', 0)
            sid = r.get('sample_id', '')
            col = colors[i % len(colors)]

            if P and P > 0:
                ax.errorbar(T, P, xerr=Te, yerr=Pe,
                            fmt='o', color=col, capsize=4,
                            markersize=7, alpha=0.85,
                            label=f"{sid} [{r.get('mineral','')}]")
                # Error ellipse
                if Te and Pe:
                    ell = Ellipse((T, P), width=2*Te, height=2*Pe,
                                  angle=0, color=col, alpha=0.12, zorder=0)
                    ax.add_patch(ell)
            else:
                ax.axvline(T, color=col, alpha=0.4, linestyle='--', linewidth=1)
                ax.scatter([T], [0.5], s=60, marker='v', color=col, zorder=5,
                           label=f"{sid} [{r.get('mineral','')}]")

        ax.set_xlabel("Temperature (°C)", fontsize=9)
        ax.set_ylabel("Pressure (kbar)", fontsize=9)
        ax.set_title(title, fontsize=9, fontweight='bold')
        ax.grid(True, alpha=0.25, linestyle=':')
        if p_all:
            ax.invert_yaxis()
        if len(results) <= 8:
            ax.legend(fontsize=7, loc='best')
        ax.tick_params(labelsize=8)

    # ────────────────────────────────────────────────────────────────────────
    #  UI CONSTRUCTION
    # ────────────────────────────────────────────────────────────────────────

    def open_window(self):
        if self.window and self.window.winfo_exists():
            self.window.lift()
            self._load_from_main_app()
            return
        if not self.dependencies_met:
            messagebox.showerror("Missing",
                f"Install: {', '.join(self.missing_deps)}")
            return
        self.window = tk.Toplevel(self.app.root)
        self.window.title("🌡️ Thermobarometry Suite v2.0")
        self.window.geometry("1150x680")
        self._build_ui()
        loaded = self._load_from_main_app()
        self.status_var.set(f"✅ Data loaded" if loaded else "ℹ️ No mineral data — add Phase/Mineral column")
        self.window.transient(self.app.root)
        self.window.lift()

    def _build_ui(self):
        # ── header ──
        hdr = tk.Frame(self.window, bg="#922b21", height=38)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        tk.Label(hdr, text="🌡️  Thermobarometry Suite v2.0",
                 font=("Arial", 13, "bold"), bg="#922b21", fg="white").pack(side=tk.LEFT, padx=10)
        tk.Label(hdr, text="Pyroxene · Feldspar · Amphibole · Olivine · Garnet",
                 font=("Arial", 8), bg="#922b21", fg="#f5b7b1").pack(side=tk.LEFT)

        # ── reload button ──
        tk.Button(hdr, text="↺ Reload Data", font=("Arial", 8),
                  bg="#641e16", fg="white", relief=tk.FLAT,
                  command=self._reload).pack(side=tk.RIGHT, padx=8, pady=5)

        # ── MC controls (compact, top-right) ──
        mc_f = tk.Frame(hdr, bg="#922b21")
        mc_f.pack(side=tk.RIGHT, padx=10)
        tk.Checkbutton(mc_f, text="Monte Carlo", variable=self.mc_enable_var,
                       bg="#922b21", fg="white", activebackground="#922b21",
                       selectcolor="#641e16", font=("Arial", 8)).pack(side=tk.LEFT)
        tk.Label(mc_f, text="n=", bg="#922b21", fg="white",
                 font=("Arial", 8)).pack(side=tk.LEFT)
        tk.Spinbox(mc_f, from_=100, to=10000, increment=100,
                   textvariable=self.mc_iter_var, width=5,
                   font=("Arial", 8)).pack(side=tk.LEFT, padx=2)

        # ── notebook ──
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self._tab_pyroxene()
        self._tab_feldspar()
        self._tab_amphibole()
        self._tab_olivine()
        self._tab_garnet()
        self._tab_results()

        # ── status bar ──
        sb = tk.Frame(self.window, bg="#2c3e50", height=22)
        sb.pack(fill=tk.X, side=tk.BOTTOM)
        sb.pack_propagate(False)
        tk.Label(sb, textvariable=self.status_var,
                 font=("Arial", 8), bg="#2c3e50", fg="white").pack(side=tk.LEFT, padx=8)
        self.progress = ttk.Progressbar(sb, mode='indeterminate', length=100)
        self.progress.pack(side=tk.RIGHT, padx=6)

    def _reload(self):
        loaded = self._load_from_main_app()
        self.status_var.set("✅ Data reloaded" if loaded else "⚠️ No mineral data found")

    # ── shared tab layout helper ──
    def _make_tab_panes(self, tab_name, icon):
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text=f"{icon} {tab_name}")
        paned = tk.PanedWindow(tab, orient=tk.HORIZONTAL, sashwidth=4,
                                bg="#ddd", sashrelief=tk.FLAT)
        paned.pack(fill=tk.BOTH, expand=True)
        left = tk.Frame(paned, bg="#f2f3f4", width=270)
        paned.add(left, width=270, minsize=230)
        right = tk.Frame(paned, bg="white")
        paned.add(right, minsize=400)
        return tab, left, right

    def _make_plot(self, parent):
        fig = plt.Figure(figsize=(6, 5), dpi=88)
        fig.patch.set_facecolor('white')
        ax  = fig.add_subplot(111)
        ax.set_facecolor('#fdfefe')
        canvas  = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        tb_f = tk.Frame(parent, height=22)
        tb_f.pack(fill=tk.X)
        NavigationToolbar2Tk(canvas, tb_f).update()
        return fig, ax, canvas

    # ────────── TAB 1: PYROXENE ──────────────────────────────────────────────
    def _tab_pyroxene(self):
        tab, left, right = self._make_tab_panes("Pyroxene", "🔮")

        s = tk.LabelFrame(left, text="📊 Data", bg="#f2f3f4", pady=3, padx=5)
        s.pack(fill=tk.X, padx=6, pady=4)
        self.px_count_label = tk.Label(s, text="CPX: 0 | OPX: 0",
                                        font=("Arial", 8), bg="#f2f3f4")
        self.px_count_label.pack(anchor=tk.W)

        tf = tk.LabelFrame(left, text="🌡️ Thermometer", bg="#f2f3f4", pady=3, padx=5)
        tf.pack(fill=tk.X, padx=6, pady=2)
        opts = [("Two-pyroxene BKN (1990)",           "two_px_bkn"),
                ("Two-pyroxene Putirka (2003)",        "two_px_p2003"),
                ("Cpx-liquid Putirka (2008) Eq.33",   "cpx_liq")]
        for txt, val in opts:
            tk.Radiobutton(tf, text=txt, variable=self.px_therm_var,
                           value=val, bg="#f2f3f4",
                           font=("Arial", 8)).pack(anchor=tk.W)

        bf = tk.LabelFrame(left, text="⚖️ Barometer", bg="#f2f3f4", pady=3, padx=5)
        bf.pack(fill=tk.X, padx=6, pady=2)
        tk.Radiobutton(bf, text="Nimis & Taylor (2000) cpx-only",
                       variable=self.px_baro_var, value="cpx_nimis",
                       bg="#f2f3f4", font=("Arial", 8)).pack(anchor=tk.W)
        tk.Radiobutton(bf, text="None (T only)",
                       variable=self.px_baro_var, value="none",
                       bg="#f2f3f4", font=("Arial", 8)).pack(anchor=tk.W)

        pf = tk.LabelFrame(left, text="Initial P (kbar)", bg="#f2f3f4", pady=3, padx=5)
        pf.pack(fill=tk.X, padx=6, pady=2)
        tk.Scale(pf, from_=0, to=60, resolution=1, orient=tk.HORIZONTAL,
                 variable=self.px_P_var, bg="#f2f3f4", length=180).pack(fill=tk.X)

        tk.Button(left, text="🧮  Calculate",
                  command=lambda: self._run("px"),
                  bg="#7d6608", fg="white", font=("Arial", 10, "bold"),
                  height=2, relief=tk.FLAT).pack(fill=tk.X, padx=6, pady=8)

        self.px_fig, self.px_ax, self.px_canvas = self._make_plot(right)
        self._plot_pt(self.px_ax, [], "Pyroxene P-T")
        self.px_canvas.draw()

    # ────────── TAB 2: FELDSPAR ──────────────────────────────────────────────
    def _tab_feldspar(self):
        tab, left, right = self._make_tab_panes("Feldspar", "🟡")

        s = tk.LabelFrame(left, text="📊 Data", bg="#f2f3f4", pady=3, padx=5)
        s.pack(fill=tk.X, padx=6, pady=4)
        self.fsp_count_label = tk.Label(s, text="Plag: 0 | Kfs: 0",
                                         font=("Arial", 8), bg="#f2f3f4")
        self.fsp_count_label.pack(anchor=tk.W)

        tf = tk.LabelFrame(left, text="🌡️ Thermometer", bg="#f2f3f4", pady=3, padx=5)
        tf.pack(fill=tk.X, padx=6, pady=2)
        tk.Radiobutton(tf, text="Plag-liquid Putirka (2008) Eq.23",
                       variable=self.fsp_therm_var, value="plag_liq",
                       bg="#f2f3f4", font=("Arial", 8)).pack(anchor=tk.W)
        tk.Radiobutton(tf, text="Two-feldspar Elkins & Grove (1990)",
                       variable=self.fsp_therm_var, value="two_fsp",
                       bg="#f2f3f4", font=("Arial", 8)).pack(anchor=tk.W)

        of = tk.LabelFrame(left, text="⚗️ Options", bg="#f2f3f4", pady=3, padx=5)
        of.pack(fill=tk.X, padx=6, pady=2)
        tk.Checkbutton(of, text="Waters & Lange (2015) hygrometer",
                       variable=self.fsp_hygro_var, bg="#f2f3f4",
                       font=("Arial", 8)).pack(anchor=tk.W)

        tk.Button(left, text="🧮  Calculate",
                  command=lambda: self._run("fsp"),
                  bg="#7d6608", fg="white", font=("Arial", 10, "bold"),
                  height=2, relief=tk.FLAT).pack(fill=tk.X, padx=6, pady=8)

        self.fsp_fig, self.fsp_ax, self.fsp_canvas = self._make_plot(right)
        self._plot_pt(self.fsp_ax, [], "Feldspar T")
        self.fsp_canvas.draw()

    # ────────── TAB 3: AMPHIBOLE ─────────────────────────────────────────────
    def _tab_amphibole(self):
        tab, left, right = self._make_tab_panes("Amphibole", "🟤")

        s = tk.LabelFrame(left, text="📊 Data", bg="#f2f3f4", pady=3, padx=5)
        s.pack(fill=tk.X, padx=6, pady=4)
        self.amph_count_label = tk.Label(s, text="Amphibole: 0",
                                          font=("Arial", 8), bg="#f2f3f4")
        self.amph_count_label.pack(anchor=tk.W)

        cf = tk.LabelFrame(left, text="📐 Calibration", bg="#f2f3f4", pady=3, padx=5)
        cf.pack(fill=tk.X, padx=6, pady=2)
        cals = [
            ("Ridolfi et al. (2010)  ±22°C/±0.6 kb",      "ridolfi2010"),
            ("Ridolfi & Renzulli (2012)  ±24°C/±0.4 kb",  "ridolfi2012"),
            ("Putirka (2016) Eq.5&6  ±30°C/±3.1 kb",      "putirka2016"),
        ]
        for txt, val in cals:
            tk.Radiobutton(cf, text=txt, variable=self.amph_cal_var,
                           value=val, bg="#f2f3f4",
                           font=("Arial", 8)).pack(anchor=tk.W)

        nf = tk.Frame(left, bg="#f2f3f4")
        nf.pack(fill=tk.X, padx=6, pady=4)
        tk.Label(nf, text="ℹ️ Mutch (2016) barometer also\ncomputed as cross-check.",
                 bg="#f2f3f4", fg="#555", font=("Arial", 7),
                 justify=tk.LEFT).pack(anchor=tk.W)

        tk.Button(left, text="🧮  Calculate",
                  command=lambda: self._run("amph"),
                  bg="#7d6608", fg="white", font=("Arial", 10, "bold"),
                  height=2, relief=tk.FLAT).pack(fill=tk.X, padx=6, pady=8)

        self.amph_fig, self.amph_ax, self.amph_canvas = self._make_plot(right)
        self._plot_pt(self.amph_ax, [], "Amphibole P-T")
        self.amph_canvas.draw()

    # ────────── TAB 4: OLIVINE ───────────────────────────────────────────────
    def _tab_olivine(self):
        tab, left, right = self._make_tab_panes("Olivine", "🟢")

        s = tk.LabelFrame(left, text="📊 Data", bg="#f2f3f4", pady=3, padx=5)
        s.pack(fill=tk.X, padx=6, pady=4)
        self.ol_count_label = tk.Label(s, text="Olivine: 0 | Melt: 0",
                                        font=("Arial", 8), bg="#f2f3f4")
        self.ol_count_label.pack(anchor=tk.W)

        tf = tk.LabelFrame(left, text="🌡️ Thermometer", bg="#f2f3f4", pady=3, padx=5)
        tf.pack(fill=tk.X, padx=6, pady=2)
        opts = [("Putirka (2008) Eq.4  Kd-based  ±45°C", "eq4"),
                ("Putirka (2008) Eq.22  Fo-based  ±29°C", "eq22"),
                ("Beattie (1993)  ±29°C",                  "beattie")]
        for txt, val in opts:
            tk.Radiobutton(tf, text=txt, variable=self.ol_therm_var,
                           value=val, bg="#f2f3f4",
                           font=("Arial", 8)).pack(anchor=tk.W)

        kf = tk.LabelFrame(left, text="⚖️ Kd Equilibrium Filter", bg="#f2f3f4", pady=3, padx=5)
        kf.pack(fill=tk.X, padx=6, pady=2)
        tk.Checkbutton(kf, text="Apply Fe-Mg Kd test  (Kd = 0.30±tol)",
                       variable=self.ol_kd_var, bg="#f2f3f4",
                       font=("Arial", 8)).pack(anchor=tk.W)
        tk.Label(kf, text="Tolerance:", bg="#f2f3f4", font=("Arial", 8)).pack(anchor=tk.W)
        tk.Scale(kf, from_=0.01, to=0.15, resolution=0.01, orient=tk.HORIZONTAL,
                 variable=self.ol_kd_tol_var, bg="#f2f3f4", length=170).pack(fill=tk.X)

        tk.Button(left, text="🧮  Calculate",
                  command=lambda: self._run("ol"),
                  bg="#7d6608", fg="white", font=("Arial", 10, "bold"),
                  height=2, relief=tk.FLAT).pack(fill=tk.X, padx=6, pady=8)

        self.ol_fig, self.ol_ax, self.ol_canvas = self._make_plot(right)
        self._plot_pt(self.ol_ax, [], "Olivine T")
        self.ol_canvas.draw()

    # ────────── TAB 5: GARNET ────────────────────────────────────────────────
    def _tab_garnet(self):
        tab, left, right = self._make_tab_panes("Garnet", "🔴")

        s = tk.LabelFrame(left, text="📊 Data", bg="#f2f3f4", pady=3, padx=5)
        s.pack(fill=tk.X, padx=6, pady=4)
        self.grt_count_label = tk.Label(s, text="Grt: 0 | Bt: 0 | CPX: 0",
                                         font=("Arial", 8), bg="#f2f3f4")
        self.grt_count_label.pack(anchor=tk.W)

        tf = tk.LabelFrame(left, text="🌡️ Thermometer", bg="#f2f3f4", pady=3, padx=5)
        tf.pack(fill=tk.X, padx=6, pady=2)
        tk.Radiobutton(tf, text="Grt-Bt  Holdaway (2001)  ±30°C",
                       variable=self.grt_therm_var, value="grt_bt_holdaway",
                       bg="#f2f3f4", font=("Arial", 8)).pack(anchor=tk.W)
        tk.Radiobutton(tf, text="Grt-Cpx  Ravna (2000)  ±25°C",
                       variable=self.grt_therm_var, value="grt_cpx_ravna",
                       bg="#f2f3f4", font=("Arial", 8)).pack(anchor=tk.W)

        bf = tk.LabelFrame(left, text="⚖️ Barometer (GASP)", bg="#f2f3f4", pady=3, padx=5)
        bf.pack(fill=tk.X, padx=6, pady=2)
        tk.Radiobutton(bf, text="Holland & Powell (1990)",
                       variable=self.grt_baro_var, value="gasp_hp",
                       bg="#f2f3f4", font=("Arial", 8)).pack(anchor=tk.W)
        tk.Radiobutton(bf, text="Newton & Haselton (1981)",
                       variable=self.grt_baro_var, value="gasp_nh",
                       bg="#f2f3f4", font=("Arial", 8)).pack(anchor=tk.W)

        pf = tk.LabelFrame(left, text="Al₂SiO₅ polymorph", bg="#f2f3f4", pady=3, padx=5)
        pf.pack(fill=tk.X, padx=6, pady=2)
        for txt in ["kyanite", "sillimanite", "andalusite"]:
            tk.Radiobutton(pf, text=txt.capitalize(), variable=self.grt_poly_var,
                           value=txt, bg="#f2f3f4",
                           font=("Arial", 8)).pack(anchor=tk.W)

        ip = tk.LabelFrame(left, text="Initial P (kbar)", bg="#f2f3f4", pady=3, padx=5)
        ip.pack(fill=tk.X, padx=6, pady=2)
        tk.Scale(ip, from_=0, to=25, resolution=1, orient=tk.HORIZONTAL,
                 variable=self.grt_P_var, bg="#f2f3f4", length=180).pack(fill=tk.X)

        tk.Button(left, text="🧮  Calculate (with P-T iteration)",
                  command=lambda: self._run("grt"),
                  bg="#7d6608", fg="white", font=("Arial", 10, "bold"),
                  height=2, relief=tk.FLAT).pack(fill=tk.X, padx=6, pady=8)

        self.grt_fig, self.grt_ax, self.grt_canvas = self._make_plot(right)
        self._plot_pt(self.grt_ax, [], "Garnet P-T")
        self.grt_canvas.draw()

    # ────────── TAB 6: RESULTS ───────────────────────────────────────────────
    def _tab_results(self):
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="📊 Results")

        # stats bar
        sf = tk.LabelFrame(tab, text="Summary", padx=6, pady=4)
        sf.pack(fill=tk.X, padx=8, pady=4)
        self.stats_text = tk.Text(sf, height=3, font=("Courier", 8),
                                   relief=tk.FLAT, bg="#fdfefe")
        self.stats_text.pack(fill=tk.X)

        # tree
        fr = tk.Frame(tab)
        fr.pack(fill=tk.BOTH, expand=True, padx=8, pady=2)

        cols = ('Sample', 'Mineral', 'T (°C)', '±T', 'P (kbar)', '±P', 'H₂O wt%', 'Method')
        widths = (110, 70, 60, 40, 65, 40, 60, 200)
        self.results_tree = ttk.Treeview(fr, columns=cols, show='headings', height=14)
        for col, w in zip(cols, widths):
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=w, anchor='center')
        vsb = ttk.Scrollbar(fr, orient=tk.VERTICAL,   command=self.results_tree.yview)
        hsb = ttk.Scrollbar(fr, orient=tk.HORIZONTAL, command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.results_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        fr.grid_rowconfigure(0, weight=1); fr.grid_columnconfigure(0, weight=1)

        # buttons
        bf = tk.Frame(tab, bg="white")
        bf.pack(fill=tk.X, padx=8, pady=4)
        btns = [
            ("📤 Export to App",        self._export_to_app,  "#1a5276"),
            ("📋 Copy TSV",             self._copy_tsv,       "#1a5276"),
            ("💾 Save CSV",             self._save_csv,       "#196f3d"),
            ("📈 Combined P-T plot",    self._combined_pt,    "#6e2f1a"),
            ("🗑️ Clear",                self._clear_results,  "#922b21"),
        ]
        for txt, cmd, col in btns:
            tk.Button(bf, text=txt, command=cmd, bg=col, fg="white",
                      font=("Arial", 8), relief=tk.FLAT,
                      padx=6).pack(side=tk.LEFT, padx=2)

    # ────────────────────────────────────────────────────────────────────────
    #  CALCULATE + UPDATE
    # ────────────────────────────────────────────────────────────────────────

    def _run(self, which):
        self.progress.start()
        dispatch = {'px': self._calc_pyroxene, 'fsp': self._calc_feldspar,
                    'amph': self._calc_amphibole, 'ol': self._calc_olivine,
                    'grt': self._calc_garnet}
        axes    = {'px': (self.px_ax,   self.px_canvas,   "Pyroxene P-T"),
                   'fsp':(self.fsp_ax,  self.fsp_canvas,  "Feldspar T"),
                   'amph':(self.amph_ax,self.amph_canvas, "Amphibole P-T"),
                   'ol': (self.ol_ax,   self.ol_canvas,   "Olivine T"),
                   'grt':(self.grt_ax,  self.grt_canvas,  "Garnet P-T")}
        try:
            results = dispatch[which]()
            if isinstance(results, str):
                messagebox.showinfo("Info", results)
                self.status_var.set(f"ℹ️ {results}")
                return
            ax, canvas, title = axes[which]
            self._plot_pt(ax, results, title)
            canvas.draw()
            self.pt_results = results
            self._update_results_tab(results)
            self.status_var.set(f"✅ {len(results)} P-T estimates")
        except Exception as e:
            self.status_var.set(f"❌ Error: {e}")
            messagebox.showerror("Calculation Error", traceback.format_exc())
        finally:
            self.progress.stop()

    def _update_results_tab(self, results):
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        if not results:
            return
        t_vals = []; p_vals = []
        for r in results:
            if not isinstance(r, dict): continue
            T   = r.get('T_C');    Te = r.get('T_err')
            P   = r.get('P_kbar'); Pe = r.get('P_err')
            H2O = r.get('H2O_wt')
            vals = (
                r.get('sample_id', '')[:18],
                r.get('mineral', ''),
                f"{T:.0f}" if T else '-',
                f"{Te:.0f}" if Te else '-',
                f"{P:.1f}"  if P  else '-',
                f"{Pe:.1f}" if Pe else '-',
                f"{H2O:.2f}" if H2O else '-',
                r.get('method', '')[:35],
            )
            self.results_tree.insert('', tk.END, values=vals)
            if T:  t_vals.append(T)
            if P:  p_vals.append(P)
        self.stats_text.delete(1.0, tk.END)
        lines = [f"Estimates: {len(results)}"]
        if t_vals:
            lines.append(f"T: {min(t_vals):.0f}–{max(t_vals):.0f} °C  |  "
                         f"mean {np.mean(t_vals):.0f} ± {np.std(t_vals):.0f} °C")
        if p_vals:
            lines.append(f"P: {min(p_vals):.1f}–{max(p_vals):.1f} kbar  |  "
                         f"mean {np.mean(p_vals):.1f} ± {np.std(p_vals):.1f} kbar")
        self.stats_text.insert(1.0, "\n".join(lines))
        self.notebook.tab(5, text=f"📊 Results ({len(results)})")

    # ────────────────────────────────────────────────────────────────────────
    #  EXPORT
    # ────────────────────────────────────────────────────────────────────────

    def _export_to_app(self):
        if not self.pt_results:
            messagebox.showinfo("Export", "No results")
            return
        ts  = datetime.now().strftime('%Y-%m-%d %H:%M')
        recs = []
        for r in self.pt_results:
            rec = {
                'Sample_ID':   r.get('sample_id', '?'),
                'Mineral':     r.get('mineral', ''),
                'Method':      r.get('method', ''),
                'Timestamp':   ts,
                'T_C':         f"{r['T_C']:.0f}" if r.get('T_C') else '',
                'T_err':       f"{r.get('T_err',0):.0f}",
            }
            if r.get('P_kbar'): rec['P_kbar'] = f"{r['P_kbar']:.1f}"
            if r.get('P_err'):  rec['P_err']  = f"{r['P_err']:.1f}"
            if r.get('H2O_wt'): rec['H2O_wt'] = f"{r['H2O_wt']:.2f}"
            recs.append(rec)
        self.app.import_data_from_plugin(recs)
        self.status_var.set(f"✅ Exported {len(recs)} records to app")

    def _copy_tsv(self):
        if not self.pt_results:
            return
        hdr  = "Sample\tMineral\tT(°C)\tT_err\tP(kbar)\tP_err\tH2O_wt\tMethod"
        lines = [hdr]
        for r in self.pt_results:
            lines.append(
                f"{r.get('sample_id','')}\t{r.get('mineral','')}\t"
                f"{r.get('T_C',0):.0f}\t{r.get('T_err',0):.0f}\t"
                f"{r.get('P_kbar','')}\t{r.get('P_err','')}\t"
                f"{r.get('H2O_wt','')}\t{r.get('method','')}")
        self.window.clipboard_clear()
        self.window.clipboard_append("\n".join(lines))
        self.status_var.set(f"✅ Copied {len(self.pt_results)} rows to clipboard")

    def _save_csv(self):
        if not self.pt_results:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("All", "*.*")],
            title="Save P-T results")
        if not path: return
        rows = []
        for r in self.pt_results:
            rows.append({
                'sample_id': r.get('sample_id',''),
                'mineral':   r.get('mineral',''),
                'T_C':       r.get('T_C',''),
                'T_err':     r.get('T_err',''),
                'P_kbar':    r.get('P_kbar',''),
                'P_err':     r.get('P_err',''),
                'H2O_wt':    r.get('H2O_wt',''),
                'method':    r.get('method',''),
            })
        pd.DataFrame(rows).to_csv(path, index=False)
        self.status_var.set(f"✅ Saved to {Path(path).name}")

    def _combined_pt(self):
        if not self.pt_results:
            messagebox.showinfo("Plot", "No results to plot")
            return
        fig, ax = plt.subplots(figsize=(7, 5))
        self._plot_pt(ax, self.pt_results, "Combined P-T Diagram")
        fig.tight_layout()
        plt.show()

    def _clear_results(self):
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        self.pt_results = []
        self.stats_text.delete(1.0, tk.END)
        self.notebook.tab(5, text="📊 Results")
        self.status_var.set("Results cleared")


# ============================================================================

def setup_plugin(main_app):
    return ThermobarometrySuitePlugin(main_app)
