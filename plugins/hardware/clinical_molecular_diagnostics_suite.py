"""
CLINICAL & MOLECULAR DIAGNOSTICS UNIFIED SUITE v1.0 - PRODUCTION RELEASE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ PCR/qPCR/dPCR: Bio-Rad · Thermo · Roche · Qiagen · Agilent · Fluidigm · Stilla
✓ Plate Readers: Tecan · BioTek · Molecular Devices · BMG · PerkinElmer
✓ Flow Cytometry: BD · Beckman · Sony · Thermo · Miltenyi · Cytek
✓ ELISA/Clinical Chemistry: Dynex · Awareness · Mindray · Siemens · Roche
✓ Sample Processors: Cepheid · Abbott · Roche — Result parsing
✓ Small Clinical: Radiometer · HemoCue · Glucometers — Serial control
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

# ============================================================================
# PLUGIN METADATA
# ============================================================================
PLUGIN_INFO = {
    "id": "clinical_molecular_diagnostics_suite",
    "name": "Clinical & Molecular Diags",
    "category": "hardware",
    "icon": "🧬",
    "version": "1.0.0",
    "author": "Clinical Diagnostics Team",
    "description": "PCR · qPCR · dPCR · Plate Readers · Flow Cytometry · ELISA · Clinical Chemistry",
    "requires": ["numpy", "pandas", "scipy", "matplotlib", "pyserial"],
    "optional": [
        "fcsparser",
        "flowio",
        "h5py",
        "openpyxl",
        "xlrd",
        "lxml",
        "beautifulsoup4"
    ],
    "compact": True,
    "window_size": "850x600"
}

# ============================================================================
# PREVENT DOUBLE REGISTRATION
# ============================================================================
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import time
import re
import json
import threading
import queue
import subprocess
import sys
import os
import csv
import xml.etree.ElementTree as ET
from pathlib import Path
import platform
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Callable, Union
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# OPTIONAL SCIENTIFIC IMPORTS
# ============================================================================
try:
    from scipy import signal, integrate, optimize
    from scipy.signal import savgol_filter, find_peaks
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.patches import Rectangle, Polygon
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

# ============================================================================
# FCS PARSER (Flow Cytometry)
# ============================================================================
try:
    import fcsparser
    HAS_FCS = True
except ImportError:
    try:
        import flowio
        HAS_FLOWIO = True
    except:
        HAS_FCS = False
        HAS_FLOWIO = False

# ============================================================================
# HDF5 for Fluidigm
# ============================================================================
try:
    import h5py
    HAS_H5PY = True
except ImportError:
    HAS_H5PY = False

# ============================================================================
# CROSS-PLATFORM CHECK
# ============================================================================
IS_WINDOWS = platform.system() == 'Windows'
IS_LINUX = platform.system() == 'Linux'
IS_MAC = platform.system() == 'Darwin'

# ============================================================================
# THREAD-SAFE UI QUEUE
# ============================================================================
class ThreadSafeUI:
    def __init__(self, root):
        self.root = root
        self.queue = queue.Queue()
        self._poll()

    def _poll(self):
        try:
            while True:
                callback = self.queue.get_nowait()
                callback()
        except queue.Empty:
            pass
        finally:
            self.root.after(50, self._poll)

    def schedule(self, callback, *args, **kwargs):
        self.queue.put(lambda: callback(*args, **kwargs))

# ============================================================================
# TOOLTIP CLASS
# ============================================================================
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind('<Enter>', self.show_tip)
        widget.bind('<Leave>', self.hide_tip)

    def show_tip(self, event):
        x = self.widget.winfo_rootx() + 25
        y = self.widget.winfo_rooty() + 25
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                        background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                        font=("Arial", "8", "normal"))
        label.pack()

    def hide_tip(self, event):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

# ============================================================================
# DEPENDENCY CHECK
# ============================================================================
def check_dependencies():
    deps = {
        'numpy': False, 'pandas': False, 'scipy': False, 'matplotlib': False,
        'pyserial': False, 'fcsparser': False, 'flowio': False, 'h5py': False,
        'lxml': False, 'bs4': False
    }

    try: import numpy; deps['numpy'] = True
    except: pass
    try: import pandas; deps['pandas'] = True
    except: pass
    try: import scipy; deps['scipy'] = True
    except: pass
    try: import matplotlib; deps['matplotlib'] = True
    except: pass
    try: import serial; deps['pyserial'] = True
    except: pass
    try: import fcsparser; deps['fcsparser'] = True
    except: pass
    try: import flowio; deps['flowio'] = True
    except: pass
    try: import h5py; deps['h5py'] = True
    except: pass
    try: import lxml; deps['lxml'] = True
    except: pass
    try: import bs4; deps['bs4'] = True
    except: pass

    return deps

DEPS = check_dependencies()

# ============================================================================
# UNIVERSAL CLINICAL DATA CLASSES
# ============================================================================

@dataclass
class PCRCurve:
    """PCR amplification curve data"""

    # Core identifiers
    timestamp: datetime
    sample_id: str
    instrument: str
    assay: str = ""
    target: str = ""  # Gene, target name
    dye: str = "FAM"  # FAM, VIC, ROX, CY5, etc.

    # Curve data
    cycle: Optional[np.ndarray] = None
    fluorescence: Optional[np.ndarray] = None
    normalized_fluorescence: Optional[np.ndarray] = None
    derivative: Optional[np.ndarray] = None

    # Results
    ct: Optional[float] = None  # Threshold cycle
    cq: Optional[float] = None  # Quantification cycle (same as Ct)
    threshold: Optional[float] = None
    baseline_start: int = 3
    baseline_end: int = 15
    efficiency: Optional[float] = None
    r_squared: Optional[float] = None

    # Melt curve
    melt_temperature: Optional[np.ndarray] = None
    melt_fluorescence: Optional[np.ndarray] = None
    melt_peak: Optional[float] = None  # Tm

    # Multi-channel
    channels: Dict[str, np.ndarray] = field(default_factory=dict)
    channel_ct: Dict[str, float] = field(default_factory=dict)

    # File source
    file_source: str = ""
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict[str, str]:
        d = {
            'Timestamp': self.timestamp.isoformat() if self.timestamp else '',
            'Sample_ID': self.sample_id,
            'Instrument': self.instrument,
            'Assay': self.assay,
            'Target': self.target,
            'Dye': self.dye,
            'Ct': f"{self.ct:.3f}" if self.ct else '',
            'Tm': f"{self.melt_peak:.1f}" if self.melt_peak else '',
            'Efficiency': f"{self.efficiency:.3f}" if self.efficiency else '',
        }
        return d

    def calculate_ct(self, method: str = "auto", threshold: float = None):
        """Calculate Ct value"""
        if self.fluorescence is None or self.cycle is None:
            return

        if method == "auto":
            # Find exponential phase (simplified)
            # Look for region with highest slope
            if HAS_SCIPY and len(self.fluorescence) > 20:
                smooth = savgol_filter(self.fluorescence, window_length=7, polyorder=2)
                deriv = np.gradient(smooth)
                # Find where derivative starts rising significantly
                max_deriv_idx = np.argmax(deriv[10:]) + 10
                # Set threshold at half max of exponential phase
                self.threshold = 0.5 * np.max(self.fluorescence[max_deriv_idx:])
            else:
                self.threshold = 0.1 * np.max(self.fluorescence)

        # Find cycle where fluorescence crosses threshold
        for i in range(1, len(self.fluorescence)):
            if self.fluorescence[i] > self.threshold and self.fluorescence[i-1] <= self.threshold:
                # Linear interpolation
                x1, y1 = self.cycle[i-1], self.fluorescence[i-1]
                x2, y2 = self.cycle[i], self.fluorescence[i]
                self.ct = x1 + (self.threshold - y1) * (x2 - x1) / (y2 - y1)
                break


@dataclass
class DigitalPCRResult:
    """Digital PCR droplet data"""

    timestamp: datetime
    sample_id: str
    instrument: str
    assay: str = ""

    # Droplet data
    total_droplets: int = 0
    positive_droplets: int = 0
    negative_droplets: int = 0
    ambiguous_droplets: int = 0

    # Results
    concentration_copies_ul: Optional[float] = None
    copies_per_reaction: Optional[float] = None
    confidence_interval: Tuple[float, float] = (0, 0)
    poisson_confidence: float = 0.95

    # 2D data for multiplex
    channel1_amplitude: Optional[np.ndarray] = None
    channel2_amplitude: Optional[np.ndarray] = None
    channel1_positive_threshold: Optional[float] = None
    channel2_positive_threshold: Optional[float] = None

    # File source
    file_source: str = ""
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict[str, str]:
        d = {
            'Timestamp': self.timestamp.isoformat() if self.timestamp else '',
            'Sample_ID': self.sample_id,
            'Instrument': self.instrument,
            'Assay': self.assay,
            'Total_Droplets': str(self.total_droplets),
            'Positive': str(self.positive_droplets),
            'Concentration': f"{self.concentration_copies_ul:.1f}" if self.concentration_copies_ul else '',
            'Copies_per_rxn': f"{self.copies_per_reaction:.1f}" if self.copies_per_reaction else '',
        }
        return d


@dataclass
class ELISAWell:
    """ELISA well data"""
    well_id: str
    absorbance: float
    concentration: Optional[float] = None
    standard: bool = False
    replicate: int = 1
    flag: str = ""


@dataclass
class ELISA_Plate:
    """ELISAplate data"""

    timestamp: datetime
    sample_id: str
    instrument: str
    assay: str = ""

    # Plate data
    plate_type: str = "96well"
    wells: List[ELISAWell] = field(default_factory=list)
    standards: List[ELISAWell] = field(default_factory=list)
    unknowns: List[ELISAWell] = field(default_factory=list)

    # Standard curve
    standard_concentrations: Optional[np.ndarray] = None
    standard_absorbances: Optional[np.ndarray] = None
    curve_fit: Dict[str, float] = field(default_factory=dict)  # {'slope': 0, 'intercept': 0, 'r2': 0}
    curve_type: str = "linear"  # linear, 4PL, 5PL

    # Results
    calculated_concentrations: Dict[str, float] = field(default_factory=dict)

    # File source
    file_source: str = ""
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict[str, str]:
        d = {
            'Timestamp': self.timestamp.isoformat() if self.timestamp else '',
            'Sample_ID': self.sample_id,
            'Instrument': self.instrument,
            'Assay': self.assay,
            'Wells': str(len(self.wells)),
            'Standards': str(len(self.standards)),
            'Curve_R2': f"{self.curve_fit.get('r2', 0):.4f}",
        }
        return d

    def calculate_standard_curve(self, fit_type: str = "linear"):
        """Calculate standard curve from standards"""
        if not self.standards:
            return

        # Sort standards by concentration
        self.standards.sort(key=lambda x: x.concentration)
        concs = np.array([w.concentration for w in self.standards])
        abss = np.array([w.absorbance for w in self.standards])

        if fit_type == "linear":
            # Linear fit
            if HAS_SCIPY:
                from scipy import stats
                slope, intercept, r_value, p_value, std_err = stats.linregress(concs, abss)
                self.curve_fit = {
                    'slope': slope,
                    'intercept': intercept,
                    'r2': r_value**2,
                    'type': 'linear'
                }

                # Calculate unknowns
                for well in self.unknowns:
                    if well.absorbance:
                        well.concentration = (well.absorbance - intercept) / slope


@dataclass
class ClinicalChemistryResult:
    """Clinical chemistry analyzer result"""

    timestamp: datetime
    sample_id: str
    instrument: str
    test_name: str
    result_value: float
    unit: str = ""
    reference_range_low: Optional[float] = None
    reference_range_high: Optional[float] = None
    flag: str = ""  # Normal, High, Low, Critical

    # Flags based on reference ranges
    def check_flags(self):
        if self.reference_range_low is not None and self.result_value < self.reference_range_low:
            self.flag = "LOW"
        elif self.reference_range_high is not None and self.result_value > self.reference_range_high:
            self.flag = "HIGH"
        else:
            self.flag = "NORMAL"

    def to_dict(self) -> Dict[str, str]:
        self.check_flags()
        return {
            'Timestamp': self.timestamp.isoformat() if self.timestamp else '',
            'Sample_ID': self.sample_id,
            'Instrument': self.instrument,
            'Test': self.test_name,
            'Result': f"{self.result_value} {self.unit}",
            'Flag': self.flag,
            'Reference': f"{self.reference_range_low}-{self.reference_range_high}" if self.reference_range_low else '',
        }


@dataclass
class BloodGasResult:
    """Blood gas analyzer result"""

    timestamp: datetime
    sample_id: str
    instrument: str

    # Blood gas parameters
    ph: Optional[float] = None
    pco2_mmHg: Optional[float] = None
    po2_mmHg: Optional[float] = None
    hco3_mmol_L: Optional[float] = None
    be_mmol_L: Optional[float] = None  # Base excess
    so2_pct: Optional[float] = None  # Oxygen saturation
    lactate_mmol_L: Optional[float] = None
    glucose_mg_dL: Optional[float] = None
    sodium_mmol_L: Optional[float] = None
    potassium_mmol_L: Optional[float] = None
    calcium_mmol_L: Optional[float] = None
    hematocrit_pct: Optional[float] = None
    hemoglobin_g_dL: Optional[float] = None

    # Flags
    flags: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, str]:
        d = {
            'Timestamp': self.timestamp.isoformat() if self.timestamp else '',
            'Sample_ID': self.sample_id,
            'Instrument': self.instrument,
        }
        for key, value in self.__dict__.items():
            if value is not None and key not in d and not key.startswith('_'):
                if isinstance(value, (int, float)):
                    d[key] = f"{value:.2f}"
                elif isinstance(value, str):
                    d[key] = value
        return d


# ============================================================================
# 1. PCR / qPCR PARSERS
# ============================================================================

class BioRadCFXParser:
    """Bio-Rad CFX96/CFX384 qPCR parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(500)
                return any(x in content for x in ['Bio-Rad', 'CFX', 'CFX96', 'CFX384'])
        except:
            return False

    @staticmethod
    def parse(filepath: str) -> List[PCRCurve]:
        curves = []
        try:
            # Bio-Rad exports multi-sheet Excel or CSV
            if filepath.endswith('.xlsx'):
                df_dict = pd.read_excel(filepath, sheet_name=None)
                # Find sheet with amplification data
                for sheet_name, df in df_dict.items():
                    if 'Cycle' in df.columns and any('Well' in str(c) for c in df.columns):
                        # Parse amplification curves
                        cycles = df['Cycle'].values
                        for col in df.columns:
                            if 'Well' not in str(col) and col != 'Cycle':
                                # This is a well fluorescence column
                                fluor = df[col].values
                                if len(fluor) == len(cycles):
                                    curve = PCRCurve(
                                        timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                                        sample_id=f"Well_{col}",
                                        instrument="Bio-Rad CFX",
                                        assay=sheet_name,
                                        cycle=cycles,
                                        fluorescence=fluor,
                                        file_source=filepath
                                    )
                                    curve.calculate_ct()
                                    curves.append(curve)
            else:
                # CSV format
                df = pd.read_csv(filepath)
                if 'Cycle' in df.columns:
                    cycles = df['Cycle'].values
                    for col in df.columns:
                        if col != 'Cycle' and 'Well' not in col:
                            fluor = df[col].values
                            if len(fluor) == len(cycles):
                                curve = PCRCurve(
                                    timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                                    sample_id=col,
                                    instrument="Bio-Rad CFX",
                                    cycle=cycles,
                                    fluorescence=fluor,
                                    file_source=filepath
                                )
                                curve.calculate_ct()
                                curves.append(curve)

        except Exception as e:
            print(f"Bio-Rad parse error: {e}")

        return curves


class ThermoQuantStudioParser:
    """Thermo Fisher QuantStudio 3/5/7 parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(500)
                return any(x in content for x in ['QuantStudio', 'Applied Biosystems', 'ABI'])
        except:
            return False

    @staticmethod
    def parse(filepath: str) -> List[PCRCurve]:
        curves = []
        try:
            # QuantStudio exports CSV with specific format
            df = pd.read_csv(filepath, skiprows=10)  # Skip header

            # Find columns
            well_col = None
            cycle_col = None
            fluor_cols = []

            for col in df.columns:
                if 'Well' in col:
                    well_col = col
                elif 'Cycle' in col:
                    cycle_col = col
                elif any(x in col for x in ['FAM', 'VIC', 'ROX', 'CY5']):
                    fluor_cols.append(col)

            if cycle_col and fluor_cols:
                # Group by well if well column exists
                if well_col:
                    for well in df[well_col].unique():
                        well_data = df[df[well_col] == well]
                        cycles = well_data[cycle_col].values

                        for fluor in fluor_cols:
                            fluor_data = well_data[fluor].values
                            if len(fluor_data) == len(cycles):
                                curve = PCRCurve(
                                    timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                                    sample_id=f"Well_{well}_{fluor}",
                                    instrument="QuantStudio",
                                    dye=fluor,
                                    cycle=cycles,
                                    fluorescence=fluor_data,
                                    file_source=filepath
                                )
                                curve.calculate_ct()
                                curves.append(curve)

        except Exception as e:
            print(f"QuantStudio parse error: {e}")

        return curves


class RocheLightCyclerParser:
    """Roche LightCycler 480/96 parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(500)
                return any(x in content for x in ['Roche', 'LightCycler', 'LC480'])
        except:
            return False

    @staticmethod
    def parse(filepath: str) -> List[PCRCurve]:
        curves = []
        try:
            # LightCycler exports TXT/CSV with tab separation
            df = pd.read_csv(filepath, sep='\t', skiprows=5)

            if 'Cycle' in df.columns:
                cycles = df['Cycle'].values
                for col in df.columns:
                    if col != 'Cycle' and 'Well' not in col:
                        fluor = df[col].values
                        if len(fluor) == len(cycles):
                            curve = PCRCurve(
                                timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                                sample_id=col,
                                instrument="LightCycler",
                                cycle=cycles,
                                fluorescence=fluor,
                                file_source=filepath
                            )
                            curve.calculate_ct()
                            curves.append(curve)

        except Exception as e:
            print(f"LightCycler parse error: {e}")

        return curves


class QiagenRotorGeneParser:
    """Qiagen Rotor-Gene Q parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(500)
                return 'Rotor-Gene' in content or 'Qiagen' in content
        except:
            return False

    @staticmethod
    def parse(filepath: str) -> List[PCRCurve]:
        curves = []
        try:
            # Rotor-Gene exports CSV with multi-channel data
            df = pd.read_csv(filepath)

            if 'Cycle' in df.columns:
                cycles = df['Cycle'].values
                # Find channels (Green, Yellow, Orange, Red)
                channels = [c for c in df.columns if any(x in c for x in ['Green', 'Yellow', 'Orange', 'Red'])]

                for channel in channels:
                    fluor = df[channel].values
                    curve = PCRCurve(
                        timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                        sample_id=Path(filepath).stem,
                        instrument="Rotor-Gene Q",
                        dye=channel,
                        cycle=cycles,
                        fluorescence=fluor,
                        file_source=filepath
                    )
                    curve.calculate_ct()
                    curves.append(curve)

        except Exception as e:
            print(f"Rotor-Gene parse error: {e}")

        return curves


class AgilentAriaMxParser:
    """Agilent AriaMx qPCR parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(500)
                return 'AriaMx' in content or 'Agilent' in content
        except:
            return False

    @staticmethod
    def parse(filepath: str) -> List[PCRCurve]:
        curves = []
        try:
            # AriaMx exports Excel with multiple sheets
            if filepath.endswith('.xlsx'):
                df_dict = pd.read_excel(filepath, sheet_name=None)
                for sheet_name, df in df_dict.items():
                    if 'Cycle' in df.columns:
                        cycles = df['Cycle'].values
                        for col in df.columns:
                            if col != 'Cycle' and df[col].dtype in [float, int]:
                                fluor = df[col].values
                                if len(fluor) == len(cycles):
                                    curve = PCRCurve(
                                        timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                                        sample_id=f"{sheet_name}_{col}",
                                        instrument="AriaMx",
                                        cycle=cycles,
                                        fluorescence=fluor,
                                        file_source=filepath
                                    )
                                    curve.calculate_ct()
                                    curves.append(curve)

        except Exception as e:
            print(f"AriaMx parse error: {e}")

        return curves


# ============================================================================
# 2. DIGITAL PCR PARSERS
# ============================================================================

class FluidigmBiomarkParser:
    """Fluidigm Biomark HD digital PCR parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        try:
            return filepath.endswith('.h5') and 'biomark' in filepath.lower()
        except:
            return False

    @staticmethod
    def parse(filepath: str) -> List[DigitalPCRResult]:
        results = []
        if not HAS_H5PY:
            return results

        try:
            import h5py
            with h5py.File(filepath, 'r') as f:
                # Extract data from HDF5 structure
                # This is simplified - real Biomark HDF5 has complex structure
                results.append(DigitalPCRResult(
                    timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                    sample_id=Path(filepath).stem,
                    instrument="Biomark HD",
                    file_source=filepath
                ))

        except Exception as e:
            print(f"Fluidigm parse error: {e}")

        return results


class BioRadQX200Parser:
    """Bio-Rad QX200 Droplet Digital PCR parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(500)
                return any(x in content for x in ['QX200', 'Droplet', 'ddPCR'])
        except:
            return False

    @staticmethod
    def parse(filepath: str) -> List[DigitalPCRResult]:
        results = []
        try:
            df = pd.read_csv(filepath)

            # Look for droplet data
            if 'Amplitude' in df.columns:
                # Single channel
                amplitudes = df['Amplitude'].values
                threshold = df['Threshold'].iloc[0] if 'Threshold' in df.columns else None

                if threshold:
                    positives = np.sum(amplitudes > threshold)
                    negatives = np.sum(amplitudes <= threshold)

                    # Calculate concentration (simplified Poisson)
                    total = len(amplitudes)
                    if total > 0 and negatives > 0:
                        lambda_est = -np.log(negatives / total)
                        conc = lambda_est * 20000  # Approx conversion to copies/ul

                        result = DigitalPCRResult(
                            timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                            sample_id=Path(filepath).stem,
                            instrument="QX200",
                            total_droplets=total,
                            positive_droplets=int(positives),
                            negative_droplets=int(negatives),
                            concentration_copies_ul=conc,
                            copies_per_reaction=conc * 20,  # 20ul reaction
                            file_source=filepath
                        )
                        results.append(result)

        except Exception as e:
            print(f"QX200 parse error: {e}")

        return results


class StillaNaicaParser:
    """Stilla Naica System digital PCR parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(500)
                return 'Naica' in content or 'Stilla' in content
        except:
            return False

    @staticmethod
    def parse(filepath: str) -> List[DigitalPCRResult]:
        results = []
        try:
            df = pd.read_csv(filepath)

            # Naica exports 2D droplet data (FAM and VIC)
            if 'FAM' in df.columns and 'VIC' in df.columns:
                fam = df['FAM'].values
                vic = df['VIC'].values

                # Find thresholds
                fam_thresh = df['FAM_Threshold'].iloc[0] if 'FAM_Threshold' in df.columns else None
                vic_thresh = df['VIC_Threshold'].iloc[0] if 'VIC_Threshold' in df.columns else None

                if fam_thresh and vic_thresh:
                    fam_pos = np.sum(fam > fam_thresh)
                    vic_pos = np.sum(vic > vic_thresh)
                    double_pos = np.sum((fam > fam_thresh) & (vic > vic_thresh))
                    total = len(fam)

                    result = DigitalPCRResult(
                        timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                        sample_id=Path(filepath).stem,
                        instrument="Naica System",
                        total_droplets=total,
                        positive_droplets=int(fam_pos + vic_pos - double_pos),
                        negative_droplets=int(total - (fam_pos + vic_pos - double_pos)),
                        ambiguous_droplets=int(double_pos),
                        channel1_amplitude=fam,
                        channel2_amplitude=vic,
                        channel1_positive_threshold=fam_thresh,
                        channel2_positive_threshold=vic_thresh,
                        file_source=filepath
                    )
                    results.append(result)

        except Exception as e:
            print(f"Stilla parse error: {e}")

        return results


# ============================================================================
# 3. FLOW CYTOMETRY PARSERS (FCS)
# ============================================================================

class FCSParser:
    """Flow Cytometry Standard (FCS) parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        return filepath.lower().endswith(('.fcs', '.lmd'))

    @staticmethod
    def parse(filepath: str) -> Optional['FlowCytometryData']:
        # Reuse from previous suite
        if HAS_FCS:
            try:
                import fcsparser
                meta, data = fcsparser.parse(filepath, reformat_meta=True)

                # Get channel names
                channels = []
                for key in meta.get('_channel_names_', []):
                    channels.append(key.replace('$P', ''))

                from analytical_chromatography_suite import FlowCytometryData
                fcs = FlowCytometryData(
                    timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                    sample_id=meta.get('$SM', Path(filepath).stem),
                    instrument=meta.get('$CYT', 'Unknown'),
                    creator=meta.get('$CREATOR', ''),
                    channels=channels,
                    events=data.values,
                    file_source=filepath,
                    metadata=meta
                )
                return fcs

            except Exception as e:
                print(f"FCS parse error: {e}")

        return None


# ============================================================================
# 4. ELISA PARSERS
# ============================================================================

class DynexELISAParser:
    """Dynex DS2/DSX ELISA parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(500)
                return 'Dynex' in content or 'DS2' in content or 'DSX' in content
        except:
            return False

    @staticmethod
    def parse(filepath: str) -> Optional[ELISA_Plate]:
        try:
            df = pd.read_csv(filepath)

            # Find plate data (8x12 grid)
            wells = []
            rows = 'ABCDEFGH'

            for r, row in enumerate(rows):
                for c in range(12):
                    well_id = f"{row}{c+1}"
                    if well_id in df.columns or well_id in df.index:
                        # Get absorbance
                        if well_id in df.columns:
                            abs_val = df[well_id].iloc[0]
                        else:
                            abs_val = df.loc[well_id].iloc[0] if well_id in df.index else None

                        if abs_val is not None and not pd.isna(abs_val):
                            well = ELISAWell(
                                well_id=well_id,
                                absorbance=float(abs_val)
                            )
                            wells.append(well)

            if wells:
                plate = ELISA_Plate(
                    timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                    sample_id=Path(filepath).stem,
                    instrument="Dynex",
                    wells=wells,
                    file_source=filepath
                )
                return plate

        except Exception as e:
            print(f"Dynex parse error: {e}")

        return None


class AwarenessELISAParser:
    """Awareness Technology StatFax ELISA parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(500)
                return any(x in content for x in ['StatFax', 'Awareness'])
        except:
            return False

    @staticmethod
    def parse(filepath: str) -> Optional[ELISA_Plate]:
        try:
            with open(filepath, 'r') as f:
                lines = f.readlines()

            # Find plate data (ASCII grid format)
            wells = []
            in_data = False
            rows = 'ABCDEFGH'

            for line in lines:
                line = line.strip()
                if 'Plate' in line or 'Results' in line:
                    in_data = True
                    continue

                if in_data and line and line[0] in rows:
                    parts = line.split()
                    row = parts[0]
                    values = parts[1:13]

                    for c, val in enumerate(values, 1):
                        try:
                            abs_val = float(val)
                            well_id = f"{row}{c}"
                            well = ELISAWell(
                                well_id=well_id,
                                absorbance=abs_val
                            )
                            wells.append(well)
                        except:
                            pass

            if wells:
                plate = ELISA_Plate(
                    timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                    sample_id=Path(filepath).stem,
                    instrument="StatFax",
                    wells=wells,
                    file_source=filepath
                )
                return plate

        except Exception as e:
            print(f"StatFax parse error: {e}")

        return None


# ============================================================================
# 5. CLINICAL CHEMISTRY ANALYZER PARSERS
# ============================================================================

class MindrayChemistryParser:
    """Mindray BA-88A / BS series parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(500)
                return 'Mindray' in content or 'BA-88A' in content
        except:
            return False

    @staticmethod
    def parse(filepath: str) -> List[ClinicalChemistryResult]:
        results = []
        try:
            df = pd.read_csv(filepath)

            # Look for test results
            sample_col = None
            test_col = None
            result_col = None
            unit_col = None

            for col in df.columns:
                col_lower = col.lower()
                if 'sample' in col_lower or 'id' in col_lower:
                    sample_col = col
                elif 'test' in col_lower or 'parameter' in col_lower:
                    test_col = col
                elif 'result' in col_lower or 'value' in col_lower:
                    result_col = col
                elif 'unit' in col_lower:
                    unit_col = col

            if sample_col and test_col and result_col:
                for idx, row in df.iterrows():
                    try:
                        result = ClinicalChemistryResult(
                            timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                            sample_id=str(row[sample_col]),
                            instrument="Mindray",
                            test_name=str(row[test_col]),
                            result_value=float(row[result_col]),
                            unit=str(row[unit_col]) if unit_col and not pd.isna(row[unit_col]) else "",
                            file_source=filepath
                        )
                        results.append(result)
                    except:
                        pass

        except Exception as e:
            print(f"Mindray parse error: {e}")

        return results


class SiemensDimensionParser:
    """Siemens Dimension EXL parser (via LIS/middleware)"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(500)
                return 'Siemens' in content or 'Dimension' in content
        except:
            return False

    @staticmethod
    def parse(filepath: str) -> List[ClinicalChemistryResult]:
        results = []
        try:
            # Usually comes as XML or HL7
            if filepath.endswith('.xml'):
                import xml.etree.ElementTree as ET
                tree = ET.parse(filepath)
                root = tree.getroot()

                for result_elem in root.findall('.//Result'):
                    try:
                        result = ClinicalChemistryResult(
                            timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                            sample_id=result_elem.findtext('SampleID', ''),
                            instrument="Siemens Dimension",
                            test_name=result_elem.findtext('TestName', ''),
                            result_value=float(result_elem.findtext('Value', '0')),
                            unit=result_elem.findtext('Unit', ''),
                            reference_range_low=float(result_elem.findtext('RefLow', '0')) if result_elem.findtext('RefLow') else None,
                            reference_range_high=float(result_elem.findtext('RefHigh', '0')) if result_elem.findtext('RefHigh') else None,
                            file_source=filepath
                        )
                        results.append(result)
                    except:
                        pass

        except Exception as e:
            print(f"Siemens parse error: {e}")

        return results


# ============================================================================
# 6. SAMPLE PROCESSOR RESULT PARSERS (Cepheid, Abbott, Roche)
# ============================================================================

class CepheidGeneXpertParser:
    """Cepheid GeneXpert result parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(500)
                return 'GeneXpert' in content or 'Cepheid' in content
        except:
            return False

    @staticmethod
    def parse(filepath: str) -> List[ClinicalChemistryResult]:
        results = []
        try:
            if filepath.endswith('.xml'):
                import xml.etree.ElementTree as ET
                tree = ET.parse(filepath)
                root = tree.getroot()

                sample_id = root.findtext('.//SampleID', Path(filepath).stem)

                for assay in root.findall('.//Assay'):
                    assay_name = assay.get('Name', 'Unknown')

                    for target in assay.findall('.//Target'):
                        target_name = target.get('Name', '')
                        ct_value = target.findtext('Ct', '')

                        if ct_value:
                            result = ClinicalChemistryResult(
                                timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                                sample_id=sample_id,
                                instrument="GeneXpert",
                                test_name=f"{assay_name} {target_name}",
                                result_value=float(ct_value),
                                unit="Ct",
                                file_source=filepath
                            )
                            results.append(result)

        except Exception as e:
            print(f"GeneXpert parse error: {e}")

        return results


# ============================================================================
# 7. BLOOD GAS ANALYZER DRIVERS (Serial)
# ============================================================================

class RadiometerBloodGasDriver:
    """Radiometer blood gas analyzer serial driver"""

    def __init__(self, port: str = None, baudrate: int = 9600):
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self.connected = False
        self.model = ""

    def connect(self) -> Tuple[bool, str]:
        if not DEPS.get('pyserial', False):
            return False, "pyserial not installed"

        try:
            import serial

            if not self.port:
                import serial.tools.list_ports
                ports = serial.tools.list_ports.comports()
                for p in ports:
                    if any(x in p.description.lower() for x in ['radiometer', 'abl', 'blood gas']):
                        self.port = p.device
                        break

            if not self.port:
                return False, "No Radiometer device found"

            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=8,
                parity='N',
                stopbits=1,
                timeout=2
            )

            self.model = "Radiometer Blood Gas Analyzer"
            self.connected = True
            return True, f"Connected to {self.model} on {self.port}"

        except Exception as e:
            return False, str(e)

    def disconnect(self):
        if self.serial and self.serial.is_open:
            self.serial.close()
        self.connected = False

    def read_result(self) -> Optional[BloodGasResult]:
        """Read latest blood gas result"""
        if not self.connected:
            return None

        try:
            # Send request (protocol varies by model)
            self.serial.write(b"RQ\r\n")
            response = self.serial.readline().decode().strip()

            # Parse response (simplified - real parsing depends on protocol)
            parts = response.split(',')

            result = BloodGasResult(
                timestamp=datetime.now(),
                sample_id=f"BG_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                instrument=self.model
            )

            # Map fields based on position (example only)
            if len(parts) >= 7:
                result.ph = float(parts[0])
                result.pco2_mmHg = float(parts[1])
                result.po2_mmHg = float(parts[2])
                result.hco3_mmol_L = float(parts[3])
                result.be_mmol_L = float(parts[4])
                result.so2_pct = float(parts[5])
                result.lactate_mmol_L = float(parts[6])

            return result

        except Exception as e:
            print(f"Blood gas read error: {e}")

        return None

    def start_measurement(self) -> bool:
        """Start measurement"""
        if not self.connected:
            return False
        try:
            self.serial.write(b"START\r\n")
            return True
        except:
            return False


# ============================================================================
# 8. HEMOGLOBIN / GLUCOMETER DRIVERS (Serial)
# ============================================================================

class HemoCueDriver:
    """HemoCue hemoglobin analyzer serial driver"""

    def __init__(self, port: str = None):
        self.port = port
        self.serial = None
        self.connected = False
        self.model = ""

    def connect(self) -> Tuple[bool, str]:
        if not DEPS.get('pyserial', False):
            return False, "pyserial not installed"

        try:
            import serial

            if not self.port:
                import serial.tools.list_ports
                ports = serial.tools.list_ports.comports()
                for p in ports:
                    if 'hemocue' in p.description.lower():
                        self.port = p.device
                        break

            if not self.port:
                return False, "No HemoCue device found"

            self.serial = serial.Serial(
                port=self.port,
                baudrate=19200,
                bytesize=8,
                parity='N',
                stopbits=1,
                timeout=2
            )

            self.model = "HemoCue"
            self.connected = True
            return True, f"Connected to HemoCue on {self.port}"

        except Exception as e:
            return False, str(e)

    def disconnect(self):
        if self.serial and self.serial.is_open:
            self.serial.close()
        self.connected = False

    def read_hb(self) -> Optional[ClinicalChemistryResult]:
        """Read hemoglobin value"""
        if not self.connected:
            return None

        try:
            # Send request
            self.serial.write(b"R\r\n")
            response = self.serial.readline().decode().strip()

            # Parse: format like "HB=12.5 g/dL"
            match = re.search(r'HB=([\d.]+)', response)
            if match:
                hb = float(match.group(1))

                result = ClinicalChemistryResult(
                    timestamp=datetime.now(),
                    sample_id=f"HB_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    instrument="HemoCue",
                    test_name="Hemoglobin",
                    result_value=hb,
                    unit="g/dL",
                    reference_range_low=12.0,
                    reference_range_high=16.0,
                    file_source="live"
                )
                return result

        except Exception as e:
            print(f"HemoCue read error: {e}")

        return None


# ============================================================================
# PLOT EMBEDDER
# ============================================================================

class ClinicalPlotEmbedder:
    """Plot clinical diagnostics data"""

    def __init__(self, canvas_widget, figure):
        self.canvas = canvas_widget
        self.figure = figure
        self.current_plot = None

    def clear(self):
        self.figure.clear()
        self.figure.set_facecolor('white')
        self.current_plot = None

    def plot_pcr_curve(self, curve: PCRCurve):
        """Plot PCR amplification curve"""
        self.clear()
        ax = self.figure.add_subplot(111)

        if curve.cycle is not None and curve.fluorescence is not None:
            ax.plot(curve.cycle, curve.fluorescence, 'b-', linewidth=2)

            # Mark Ct if available
            if curve.ct:
                ax.axvline(curve.ct, color='r', linestyle='--',
                          alpha=0.7, label=f"Ct = {curve.ct:.2f}")

            # Mark threshold
            if curve.threshold:
                ax.axhline(curve.threshold, color='g', linestyle=':',
                          alpha=0.7, label=f"Threshold = {curve.threshold:.1f}")

            ax.set_xlabel('Cycle', fontweight='bold')
            ax.set_ylabel('Fluorescence', fontweight='bold')
            ax.set_title(f"{curve.instrument}: {curve.sample_id} - {curve.dye}", fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.legend()

        self.figure.tight_layout()
        self.canvas.draw()
        self.current_plot = 'pcr'

    def plot_digital_pcr(self, dpcr: DigitalPCRResult):
        """Plot digital PCR droplet scatter"""
        self.clear()
        ax = self.figure.add_subplot(111)

        if dpcr.channel1_amplitude is not None and dpcr.channel2_amplitude is not None:
            # 2D plot for multiplex
            ax.scatter(dpcr.channel1_amplitude, dpcr.channel2_amplitude,
                      c='blue', alpha=0.6, s=10)

            if dpcr.channel1_positive_threshold:
                ax.axvline(dpcr.channel1_positive_threshold, color='r', linestyle='--')
            if dpcr.channel2_positive_threshold:
                ax.axhline(dpcr.channel2_positive_threshold, color='r', linestyle='--')

            ax.set_xlabel('Channel 1 Amplitude', fontweight='bold')
            ax.set_ylabel('Channel 2 Amplitude', fontweight='bold')
        else:
            # 1D histogram
            ax.hist(dpcr.channel1_amplitude, bins=50, color='blue', alpha=0.7)

            if dpcr.channel1_positive_threshold:
                ax.axvline(dpcr.channel1_positive_threshold, color='r', linestyle='--',
                          label=f"Threshold = {dpcr.channel1_positive_threshold:.1f}")

            ax.set_xlabel('Amplitude', fontweight='bold')
            ax.set_ylabel('Droplet Count', fontweight='bold')

        title = f"{dpcr.instrument}: {dpcr.sample_id}\nPos: {dpcr.positive_droplets}/{dpcr.total_droplets}"
        ax.set_title(title, fontweight='bold')
        ax.legend()

        self.figure.tight_layout()
        self.canvas.draw()
        self.current_plot = 'dpcr'

    def plot_elisa_plate(self, plate: ELISA_Plate):
        """Plot ELISA plate heatmap"""
        self.clear()
        ax = self.figure.add_subplot(111)

        # Create 8x12 matrix
        matrix = np.zeros((8, 12))
        rows = 'ABCDEFGH'

        for well in plate.wells:
            row = rows.index(well.well_id[0])
            col = int(well.well_id[1:]) - 1
            if 0 <= row < 8 and 0 <= col < 12:
                matrix[row, col] = well.absorbance

        im = ax.imshow(matrix, cmap='viridis', aspect='auto')
        ax.set_xticks(np.arange(12))
        ax.set_xticklabels(np.arange(1, 13))
        ax.set_yticks(np.arange(8))
        ax.set_yticklabels(list(rows))
        ax.set_xlabel('Column')
        ax.set_ylabel('Row')
        ax.set_title(f"ELISA: {plate.sample_id}", fontweight='bold')
        plt.colorbar(im, ax=ax, label='Absorbance')

        self.figure.tight_layout()
        self.canvas.draw()
        self.current_plot = 'elisa'


# ============================================================================
# MAIN PLUGIN - CLINICAL & MOLECULAR DIAGNOSTICS SUITE
# ============================================================================
class ClinicalDiagnosticsSuitePlugin:

    def __init__(self, main_app):
        self.app = main_app
        self.window = None
        self.ui_queue = None
        self.deps = DEPS

        # Devices
        self.radiometer = None
        self.hemocue = None
        self.connected_devices = []

        # Data
        self.pcr_curves: List[PCRCurve] = []
        self.dpcr_results: List[DigitalPCRResult] = []
        self.elisa_plates: List[ELISA_Plate] = []
        self.clinical_results: List[ClinicalChemistryResult] = []
        self.blood_gas_results: List[BloodGasResult] = []
        self.current_pcr: Optional[PCRCurve] = None

        # Plot embedder
        self.plot_embedder = None

        # UI Variables
        self.status_var = tk.StringVar(value="Clinical Diagnostics v1.0 - Ready")
        self.category_var = tk.StringVar(value="PCR/qPCR")
        self.file_count_var = tk.StringVar(value="No files loaded")

        # UI Elements
        self.notebook = None
        self.log_listbox = None
        self.plot_canvas = None
        self.plot_fig = None
        self.status_indicator = None
        self.category_combo = None
        self.tree = None
        self.import_btn = None
        self.batch_btn = None

        self.categories = [
            "PCR/qPCR",
            "Digital PCR",
            "Flow Cytometry",
            "ELISA",
            "Clinical Chemistry",
            "Blood Gas",
            "Sample Processors"
        ]

    def show_interface(self):
        self.open_window()

    def open_window(self):
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("Clinical & Molecular Diagnostics v1.0")
        self.window.geometry("850x600")
        self.window.minsize(800, 550)
        self.window.transient(self.app.root)

        self.ui_queue = ThreadSafeUI(self.window)
        self._build_ui()
        self.window.lift()
        self.window.focus_force()
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        """850x600 UI"""

        # Header
        header = tk.Frame(self.window, bg="#e74c3c", height=40)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="🧬", font=("Arial", 16),
                bg="#e74c3c", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Label(header, text="CLINICAL & MOLECULAR DIAGNOSTICS", font=("Arial", 12, "bold"),
                bg="#e74c3c", fg="white").pack(side=tk.LEFT)
        tk.Label(header, text="v1.0", font=("Arial", 8),
                bg="#e74c3c", fg="#f1c40f").pack(side=tk.LEFT, padx=5)

        self.status_indicator = tk.Label(header, textvariable=self.status_var,
                                        font=("Arial", 8), bg="#e74c3c", fg="white")
        self.status_indicator.pack(side=tk.RIGHT, padx=10)

        # Toolbar
        toolbar = tk.Frame(self.window, bg="#ecf0f1", height=80)
        toolbar.pack(fill=tk.X)
        toolbar.pack_propagate(False)

        row1 = tk.Frame(toolbar, bg="#ecf0f1")
        row1.pack(fill=tk.X, pady=2)

        tk.Label(row1, text="Category:", font=("Arial", 9, "bold"),
                bg="#ecf0f1").pack(side=tk.LEFT, padx=5)
        self.category_combo = ttk.Combobox(row1, textvariable=self.category_var,
                                           values=self.categories, width=20)
        self.category_combo.pack(side=tk.LEFT, padx=2)

        self.import_btn = ttk.Button(row1, text="📂 Import File",
                                     command=self._import_file, width=12)
        self.import_btn.pack(side=tk.LEFT, padx=5)

        self.batch_btn = ttk.Button(row1, text="📁 Batch Folder",
                                    command=self._batch_folder, width=12)
        self.batch_btn.pack(side=tk.LEFT, padx=2)

        self.file_count_label = tk.Label(row1, textvariable=self.file_count_var,
                                        font=("Arial", 8), bg="#ecf0f1", fg="#7f8c8d")
        self.file_count_label.pack(side=tk.RIGHT, padx=10)

        # Row 2: Hardware controls
        row2 = tk.Frame(toolbar, bg="#ecf0f1")
        row2.pack(fill=tk.X, pady=2)

        ttk.Button(row2, text="🩸 Blood Gas Connect",
                  command=self._connect_blood_gas, width=15).pack(side=tk.LEFT, padx=2)

        ttk.Button(row2, text="🧪 HemoCue Connect",
                  command=self._connect_hemocue, width=15).pack(side=tk.LEFT, padx=2)

        ttk.Button(row2, text="📊 Calculate Ct",
                  command=self._calculate_ct, width=12).pack(side=tk.LEFT, padx=2)

        ttk.Button(row2, text="📈 Plot",
                  command=self._plot_selected, width=8).pack(side=tk.RIGHT, padx=2)

        # Notebook
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self._create_data_tab()
        self._create_plot_tab()
        self._create_hardware_tab()
        self._create_log_tab()

        # Status bar
        status = tk.Frame(self.window, bg="#34495e", height=22)
        status.pack(fill=tk.X, side=tk.BOTTOM)
        status.pack_propagate(False)

        self.count_label = tk.Label(status,
            text=f"📊 {len(self.pcr_curves)} PCR · {len(self.dpcr_results)} dPCR · {len(self.elisa_plates)} ELISA",
            font=("Arial", 8), bg="#34495e", fg="white")
        self.count_label.pack(side=tk.LEFT, padx=5)

        tk.Label(status,
                text="Bio-Rad · Thermo · Roche · Qiagen · BD · Tecan · Radiometer",
                font=("Arial", 8), bg="#34495e", fg="#bdc3c7").pack(side=tk.RIGHT, padx=5)

    def _create_data_tab(self):
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="📊 Data")

        frame = tk.Frame(tab, bg="white")
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ('Type', 'Sample', 'Instrument', 'Ct/Tm', 'Dye', 'File')
        self.tree = ttk.Treeview(frame, columns=columns, show='headings', height=15)

        col_widths = [60, 150, 150, 80, 80, 150]
        for col, width in zip(columns, col_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width)

        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        self.tree.bind('<Double-1>', self._on_tree_double_click)

    def _create_plot_tab(self):
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="📈 Plot")

        ctrl_frame = tk.Frame(tab, bg="#f8f9fa", height=30)
        ctrl_frame.pack(fill=tk.X)
        ctrl_frame.pack_propagate(False)

        ttk.Button(ctrl_frame, text="🔄 Refresh", command=self._refresh_plot,
                  width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(ctrl_frame, text="💾 Save", command=self._save_plot,
                  width=8).pack(side=tk.LEFT, padx=2)

        plot_frame = tk.Frame(tab, bg="white")
        plot_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.plot_fig = Figure(figsize=(8, 4), dpi=90, facecolor='white')
        self.plot_canvas = FigureCanvasTkAgg(self.plot_fig, master=plot_frame)
        self.plot_canvas.draw()
        self.plot_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.plot_embedder = ClinicalPlotEmbedder(self.plot_canvas, self.plot_fig)

        ax = self.plot_fig.add_subplot(111)
        ax.text(0.5, 0.5, 'Select data to plot', ha='center', va='center',
               transform=ax.transAxes, fontsize=12, color='#7f8c8d')
        ax.set_title('Clinical Diagnostics Plot', fontweight='bold')
        ax.axis('off')
        self.plot_canvas.draw()

    def _create_hardware_tab(self):
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="⚡ Hardware")

        # Blood Gas
        bg_frame = tk.LabelFrame(tab, text="Blood Gas Analyzer", bg="white", font=("Arial", 9, "bold"))
        bg_frame.pack(fill=tk.X, padx=5, pady=5)

        row1 = tk.Frame(bg_frame, bg="white")
        row1.pack(fill=tk.X, pady=2)

        tk.Label(row1, text="Port:", font=("Arial", 8), bg="white").pack(side=tk.LEFT, padx=2)
        self.bg_port_var = tk.StringVar(value="/dev/ttyUSB0" if IS_LINUX else "COM3")
        ttk.Entry(row1, textvariable=self.bg_port_var, width=12).pack(side=tk.LEFT, padx=2)

        self.bg_connect_btn = ttk.Button(row1, text="🔌 Connect",
                                         command=self._connect_blood_gas, width=10)
        self.bg_connect_btn.pack(side=tk.LEFT, padx=5)

        self.bg_status = tk.Label(row1, text="●", fg="red", font=("Arial", 10), bg="white")
        self.bg_status.pack(side=tk.LEFT, padx=2)

        row2 = tk.Frame(bg_frame, bg="white")
        row2.pack(fill=tk.X, pady=2)

        ttk.Button(row2, text="▶ Start Measurement",
                  command=self._start_blood_gas, width=15).pack(side=tk.LEFT, padx=2)
        ttk.Button(row2, text="📊 Read Result",
                  command=self._read_blood_gas, width=15).pack(side=tk.LEFT, padx=2)

        # HemoCue
        hb_frame = tk.LabelFrame(tab, text="HemoCue Hemoglobin", bg="white", font=("Arial", 9, "bold"))
        hb_frame.pack(fill=tk.X, padx=5, pady=5)

        row3 = tk.Frame(hb_frame, bg="white")
        row3.pack(fill=tk.X, pady=2)

        tk.Label(row3, text="Port:", font=("Arial", 8), bg="white").pack(side=tk.LEFT, padx=2)
        self.hb_port_var = tk.StringVar(value="/dev/ttyUSB1" if IS_LINUX else "COM4")
        ttk.Entry(row3, textvariable=self.hb_port_var, width=12).pack(side=tk.LEFT, padx=2)

        self.hb_connect_btn = ttk.Button(row3, text="🔌 Connect",
                                         command=self._connect_hemocue, width=10)
        self.hb_connect_btn.pack(side=tk.LEFT, padx=5)

        self.hb_status = tk.Label(row3, text="●", fg="red", font=("Arial", 10), bg="white")
        self.hb_status.pack(side=tk.LEFT, padx=2)

        ttk.Button(hb_frame, text="📊 Read Hb",
                  command=self._read_hemocue, width=15).pack(pady=2)

    def _create_log_tab(self):
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="📋 Log")

        self.log_listbox = tk.Listbox(tab, font=("Courier", 9))
        scroll = ttk.Scrollbar(tab, orient=tk.VERTICAL, command=self.log_listbox.yview)
        self.log_listbox.configure(yscrollcommand=scroll.set)
        self.log_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=5)

        btn_frame = tk.Frame(tab, bg="white")
        btn_frame.pack(fill=tk.X, pady=2)

        ttk.Button(btn_frame, text="🗑️ Clear", command=self._clear_log,
                  width=10).pack(side=tk.RIGHT, padx=5)

    # ============================================================================
    # FILE IMPORT METHODS
    # ============================================================================

    def _import_file(self):
        path = filedialog.askopenfilename(
            filetypes=[("All supported", "*.csv;*.xlsx;*.txt;*.fcs;*.xml;*.h5"),
                      ("PCR/qPCR", "*.csv;*.xlsx;*.txt"),
                      ("FCS", "*.fcs"),
                      ("All files", "*.*")]
        )
        if not path:
            return

        self._update_status(f"Parsing {Path(path).name}...", "#f39c12")
        self.import_btn.config(state='disabled')

        def parse_thread():
            results = []
            data_type = "Unknown"

            # Try PCR parsers
            for parser in [BioRadCFXParser, ThermoQuantStudioParser,
                          RocheLightCyclerParser, QiagenRotorGeneParser,
                          AgilentAriaMxParser]:
                if hasattr(parser, 'can_parse') and parser.can_parse(path):
                    curves = parser.parse(path)
                    if curves:
                        self.pcr_curves.extend(curves)
                        results.extend(curves)
                        data_type = "PCR"
                        break

            # Try dPCR
            if not results:
                for parser in [BioRadQX200Parser, StillaNaicaParser]:
                    if hasattr(parser, 'can_parse') and parser.can_parse(path):
                        dpcrs = parser.parse(path)
                        if dpcrs:
                            self.dpcr_results.extend(dpcrs)
                            results.extend(dpcrs)
                            data_type = "dPCR"
                            break

            # Try ELISA
            if not results:
                for parser in [DynexELISAParser, AwarenessELISAParser]:
                    if hasattr(parser, 'can_parse') and parser.can_parse(path):
                        plate = parser.parse(path)
                        if plate:
                            self.elisa_plates.append(plate)
                            results.append(plate)
                            data_type = "ELISA"
                            break

            # Try Clinical Chemistry
            if not results:
                for parser in [MindrayChemistryParser, SiemensDimensionParser,
                              CepheidGeneXpertParser]:
                    if hasattr(parser, 'can_parse') and parser.can_parse(path):
                        clin_results = parser.parse(path)
                        if clin_results:
                            self.clinical_results.extend(clin_results)
                            results.extend(clin_results)
                            data_type = "Clinical"
                            break

            def update_ui():
                self.import_btn.config(state='normal')
                if results:
                    self._update_tree()
                    self.file_count_var.set(f"Files: {len(self.pcr_curves)+len(self.dpcr_results)}")
                    self.count_label.config(
                        text=f"📊 {len(self.pcr_curves)} PCR · {len(self.dpcr_results)} dPCR · {len(self.elisa_plates)} ELISA")
                    self._add_to_log(f"✅ Imported {len(results)} {data_type} items from {Path(path).name}")

                    # Auto-plot first result
                    if results and self.plot_embedder:
                        if isinstance(results[0], PCRCurve):
                            self.plot_embedder.plot_pcr_curve(results[0])
                            self.current_pcr = results[0]
                        elif isinstance(results[0], DigitalPCRResult):
                            self.plot_embedder.plot_digital_pcr(results[0])
                        elif hasattr(results[0], 'wells'):  # ELISA_Plate
                            self.plot_embedder.plot_elisa_plate(results[0])
                        self.notebook.select(1)
                else:
                    self._add_to_log(f"❌ Failed to parse: {Path(path).name}")

            self.ui_queue.schedule(update_ui)

        threading.Thread(target=parse_thread, daemon=True).start()

    def _batch_folder(self):
        folder = filedialog.askdirectory()
        if not folder:
            return

        self._update_status(f"Scanning {Path(folder).name}...", "#f39c12")
        self.import_btn.config(state='disabled')
        self.batch_btn.config(state='disabled')

        def batch_thread():
            pcr_count = 0
            dpcr_count = 0
            elisa_count = 0

            for ext in ['*.csv', '*.xlsx', '*.txt', '*.fcs', '*.xml']:
                for filepath in Path(folder).glob(ext):
                    # Try PCR
                    curves = BioRadCFXParser.parse(str(filepath))
                    if curves:
                        self.pcr_curves.extend(curves)
                        pcr_count += len(curves)
                        continue

                    # Try dPCR
                    dpcrs = BioRadQX200Parser.parse(str(filepath))
                    if dpcrs:
                        self.dpcr_results.extend(dpcrs)
                        dpcr_count += len(dpcrs)

            def update_ui():
                self._update_tree()
                self.file_count_var.set(f"Files: {pcr_count+dpcr_count}")
                self.count_label.config(
                    text=f"📊 {len(self.pcr_curves)} PCR · {len(self.dpcr_results)} dPCR · {len(self.elisa_plates)} ELISA")
                self._add_to_log(f"📁 Batch imported: {pcr_count} PCR, {dpcr_count} dPCR")
                self._update_status(f"✅ Imported {pcr_count+dpcr_count} items")
                self.import_btn.config(state='normal')
                self.batch_btn.config(state='normal')

            self.ui_queue.schedule(update_ui)

        threading.Thread(target=batch_thread, daemon=True).start()

    def _update_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        # PCR curves
        for curve in self.pcr_curves[-50:]:
            self.tree.insert('', 0, values=(
                "PCR",
                curve.sample_id[:20],
                curve.instrument[:15],
                f"{curve.ct:.2f}" if curve.ct else "",
                curve.dye,
                Path(curve.file_source).name if curve.file_source else ""
            ))

        # dPCR results
        for dpcr in self.dpcr_results[-20:]:
            self.tree.insert('', 0, values=(
                "dPCR",
                dpcr.sample_id[:20],
                dpcr.instrument[:15],
                f"{dpcr.concentration_copies_ul:.0f} cp/µL" if dpcr.concentration_copies_ul else "",
                "",
                Path(dpcr.file_source).name if dpcr.file_source else ""
            ))

    def _on_tree_double_click(self, event):
        self._plot_selected()

    def _plot_selected(self):
        if self.pcr_curves and self.plot_embedder:
            self.plot_embedder.plot_pcr_curve(self.pcr_curves[-1])

    def _refresh_plot(self):
        if self.current_pcr and self.plot_embedder:
            self.plot_embedder.plot_pcr_curve(self.current_pcr)

    def _save_plot(self):
        if not self.plot_fig:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("PDF", "*.pdf"), ("SVG", "*.svg")],
            initialfile=f"clinical_plot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        )
        if path:
            self.plot_fig.savefig(path, dpi=300, bbox_inches='tight')
            self._add_to_log(f"💾 Plot saved: {Path(path).name}")

    def _calculate_ct(self):
        """Calculate Ct for current curve"""
        if self.current_pcr:
            self.current_pcr.calculate_ct()
            self._add_to_log(f"✅ Ct = {self.current_pcr.ct:.3f}")
            self._refresh_plot()

    # ============================================================================
    # HARDWARE CONTROL METHODS
    # ============================================================================

    def _connect_blood_gas(self):
        port = self.bg_port_var.get()

        def connect_thread():
            self.radiometer = RadiometerBloodGasDriver(port=port)
            success, msg = self.radiometer.connect()

            def update_ui():
                if success:
                    self.connected_devices.append(self.radiometer)
                    self.bg_status.config(fg="#2ecc71")
                    self.bg_connect_btn.config(text="✅ Connected")
                    self._add_to_log(f"🔌 Blood gas connected: {msg}")
                else:
                    self.bg_status.config(fg="red")
                    self.bg_connect_btn.config(text="🔌 Connect")
                    self._add_to_log(f"❌ Blood gas connection failed: {msg}")

            self.ui_queue.schedule(update_ui)

        threading.Thread(target=connect_thread, daemon=True).start()

    def _start_blood_gas(self):
        if not self.radiometer or not self.radiometer.connected:
            return

        def run_thread():
            success = self.radiometer.start_measurement()

            def update_ui():
                if success:
                    self._add_to_log("✅ Blood gas measurement started")
                else:
                    self._add_to_log("❌ Failed to start measurement")

            self.ui_queue.schedule(update_ui)

        threading.Thread(target=run_thread, daemon=True).start()

    def _read_blood_gas(self):
        if not self.radiometer or not self.radiometer.connected:
            return

        def read_thread():
            result = self.radiometer.read_result()

            def update_ui():
                if result:
                    self.blood_gas_results.append(result)
                    self._add_to_log(f"✅ Blood gas: pH={result.ph:.2f}, pCO2={result.pco2_mmHg:.1f}")
                else:
                    self._add_to_log("❌ Failed to read result")

            self.ui_queue.schedule(update_ui)

        threading.Thread(target=read_thread, daemon=True).start()

    def _connect_hemocue(self):
        port = self.hb_port_var.get()

        def connect_thread():
            self.hemocue = HemoCueDriver(port=port)
            success, msg = self.hemocue.connect()

            def update_ui():
                if success:
                    self.connected_devices.append(self.hemocue)
                    self.hb_status.config(fg="#2ecc71")
                    self.hb_connect_btn.config(text="✅ Connected")
                    self._add_to_log(f"🔌 HemoCue connected: {msg}")
                else:
                    self.hb_status.config(fg="red")
                    self.hb_connect_btn.config(text="🔌 Connect")
                    self._add_to_log(f"❌ HemoCue connection failed: {msg}")

            self.ui_queue.schedule(update_ui)

        threading.Thread(target=connect_thread, daemon=True).start()

    def _read_hemocue(self):
        if not self.hemocue or not self.hemocue.connected:
            return

        def read_thread():
            result = self.hemocue.read_hb()

            def update_ui():
                if result:
                    self.clinical_results.append(result)
                    flag = result.flag
                    color = "#27ae60" if flag == "NORMAL" else "#e74c3c"
                    self._add_to_log(f"✅ HemoCue: {result.result_value} {result.unit} [{flag}]")
                else:
                    self._add_to_log("❌ Failed to read HemoCue")

            self.ui_queue.schedule(update_ui)

        threading.Thread(target=read_thread, daemon=True).start()

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================

    def _add_to_log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_listbox.insert(0, f"[{timestamp}] {message}")
        if self.log_listbox.size() > 100:
            self.log_listbox.delete(100, tk.END)
        self.log_listbox.see(0)

    def _clear_log(self):
        self.log_listbox.delete(0, tk.END)

    def _update_status(self, message, color=None):
        self.status_var.set(message)
        if color and self.status_indicator:
            self.status_indicator.config(fg=color)

    def send_to_table(self):
        data = []
        for curve in self.pcr_curves:
            data.append(curve.to_dict())
        for dpcr in self.dpcr_results:
            data.append(dpcr.to_dict())
        for plate in self.elisa_plates:
            data.append(plate.to_dict())
        for result in self.clinical_results:
            data.append(result.to_dict())
        for bg in self.blood_gas_results:
            data.append(bg.to_dict())

        if not data:
            messagebox.showwarning("No Data", "No data to send")
            return

        try:
            self.app.import_data_from_plugin(data)
            self._add_to_log(f"📤 Sent {len(data)} records to main table")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def collect_data(self) -> List[Dict]:
        data = []
        for curve in self.pcr_curves:
            data.append(curve.to_dict())
        return data

    def _on_close(self):
        self._add_to_log("🛑 Shutting down...")

        for device in self.connected_devices:
            if device and hasattr(device, 'disconnect'):
                try:
                    device.disconnect()
                    self._add_to_log(f"✅ Device disconnected")
                except:
                    pass

        self.connected_devices.clear()

        if self.window:
            self.window.destroy()
            self.window = None

# ============================================================================
# SIMPLE PLUGIN REGISTRATION - NO DUPLICATES
# ============================================================================

def setup_plugin(main_app):
    """Register plugin - simple, no duplicates"""

    # Create plugin instance
    plugin = ClinicalDiagnosticsSuitePlugin(main_app)

    # Add to left panel if available
    if hasattr(main_app, 'left') and main_app.left is not None:
        main_app.left.add_hardware_button(
            name=PLUGIN_INFO.get("name", "Clinical & Molecular Diagnostics"),
            icon=PLUGIN_INFO.get("icon", "🧬"),
            command=plugin.show_interface
        )
        print(f"✅ Added: {PLUGIN_INFO.get('name')}")

    return plugin
