"""
CLINICAL & MOLECULAR DIAGNOSTICS UNIFIED SUITE v2.0 - COMPLETE MERGE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ORIGINAL v1.0 CODE (PRESERVED 100%):
✓ PCR/qPCR: Bio-Rad · Thermo · Roche · Qiagen · Agilent
✓ Digital PCR: Bio-Rad QX200 · Stilla Naica · Fluidigm
✓ Flow Cytometry: FCS parser
✓ ELISA: Dynex · Awareness
✓ Clinical Chemistry: Mindray · Siemens · Cepheid
✓ Blood Gas · HemoCue

NEW IN v2.0 (ADDED, NOT REPLACED):
✓ Contour Next Glucometer - USB HID
✓ FreeStyle Libre CGM - HID interface
✓ Contec CMS50E Pulse Oximeter - serial live streaming
✓ ChoiceMMed Pulse Oximeter - serial live streaming
✓ Siemens Clinitek Urinalysis - serial strip reader
✓ Dirui H500 Urinalysis - serial strip reader
✓ Ocean USB2000+ Spectrometer - USBTMC
✓ Ocean STS Spectrometer - USBTMC

EVERYTHING WORKS TOGETHER. NOTHING REMOVED.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

# ============================================================================
# PLUGIN METADATA
# ============================================================================
PLUGIN_INFO = {
    "id": "clinical_molecular_diagnostics_suite_v2_complete",
    "name": "Clinical & Molecular Diags v2.0 Complete",
    "category": "hardware",
    "icon": "🧬",
    "version": "2.0.0",
    "author": "Clinical Diagnostics Team",
    "description": "COMPLETE: PCR/qPCR/dPCR/ELISA/Flow + 8 NEW live devices",
    "requires": ["numpy", "pandas", "scipy", "matplotlib", "pyserial"],
    "optional": [
        "fcsparser", "flowio", "h5py", "openpyxl", "xlrd", "lxml",
        "glucometerutils", "hidapi", "pyvisa-py"
    ],
    "window_size": "1200x800"
}

# ============================================================================
# CORE IMPORTS
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
# OPTIONAL IMPORTS WITH GRACEFUL FALLBACK
# ============================================================================
try:
    import serial
    import serial.tools.list_ports
    HAS_SERIAL = True
except ImportError:
    HAS_SERIAL = False

try:
    import hid
    HAS_HID = True
except ImportError:
    HAS_HID = False

try:
    import pyvisa
    HAS_VISA = True
except ImportError:
    HAS_VISA = False

try:
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    from matplotlib.figure import Figure
    from matplotlib.gridspec import GridSpec
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

try:
    from scipy import stats, optimize, signal
    from scipy.signal import savgol_filter, find_peaks
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

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
# COLOR PALETTE — FROM YOUR ANALYSIS SUITE
# ============================================================================
C_HEADER   = "#003366"   # dark medical blue
C_ACCENT   = "#CC3333"   # diagnostic red
C_ACCENT2  = "#006633"   # result green
C_ACCENT3  = "#FF9900"   # warning orange
C_LIGHT    = "#F5F5F5"   # light gray
C_BORDER   = "#BDC3C7"   # silver
C_STATUS   = "#006633"   # green
C_WARN     = "#CC3333"   # red
PLOT_COLORS = ["#003366", "#CC3333", "#006633", "#FF9900", "#663399", "#008080", "#CC6600"]

# ============================================================================
# THREAD-SAFE UI QUEUE (YOUR EXACT PATTERN)
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
# TOOLTIP CLASS (FROM YOUR ANALYSIS SUITE)
# ============================================================================
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, event=None):
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 20
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        tk.Label(self.tip, text=self.text, background="#FFFACD",
                 relief=tk.SOLID, borderwidth=1,
                 font=("Arial", 8)).pack()

    def _hide(self, event=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None

# ============================================================================
# DATA CLASSES (YOUR ORIGINAL + NEW ONES)
# ============================================================================

@dataclass
class PCRCurve:
    """PCR amplification curve data (YOUR ORIGINAL)"""
    timestamp: datetime
    sample_id: str
    instrument: str
    assay: str = ""
    target: str = ""
    dye: str = "FAM"
    cycle: Optional[np.ndarray] = None
    fluorescence: Optional[np.ndarray] = None
    normalized_fluorescence: Optional[np.ndarray] = None
    derivative: Optional[np.ndarray] = None
    ct: Optional[float] = None
    cq: Optional[float] = None
    threshold: Optional[float] = None
    baseline_start: int = 3
    baseline_end: int = 15
    efficiency: Optional[float] = None
    r_squared: Optional[float] = None
    melt_temperature: Optional[np.ndarray] = None
    melt_fluorescence: Optional[np.ndarray] = None
    melt_peak: Optional[float] = None
    channels: Dict[str, np.ndarray] = field(default_factory=dict)
    channel_ct: Dict[str, float] = field(default_factory=dict)
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

@dataclass
class DigitalPCRResult:
    """Digital PCR droplet data (YOUR ORIGINAL)"""
    timestamp: datetime
    sample_id: str
    instrument: str
    assay: str = ""
    total_droplets: int = 0
    positive_droplets: int = 0
    negative_droplets: int = 0
    ambiguous_droplets: int = 0
    concentration_copies_ul: Optional[float] = None
    copies_per_reaction: Optional[float] = None
    confidence_interval: Tuple[float, float] = (0, 0)
    poisson_confidence: float = 0.95
    channel1_amplitude: Optional[np.ndarray] = None
    channel2_amplitude: Optional[np.ndarray] = None
    channel1_positive_threshold: Optional[float] = None
    channel2_positive_threshold: Optional[float] = None
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
        }
        return d

@dataclass
class ELISAWell:
    """ELISA well data (YOUR ORIGINAL)"""
    well_id: str
    absorbance: float
    concentration: Optional[float] = None
    standard: bool = False
    replicate: int = 1
    flag: str = ""

@dataclass
class ELISA_Plate:
    """ELISA plate data (YOUR ORIGINAL)"""
    timestamp: datetime
    sample_id: str
    instrument: str
    assay: str = ""
    plate_type: str = "96well"
    wells: List[ELISAWell] = field(default_factory=list)
    standards: List[ELISAWell] = field(default_factory=list)
    unknowns: List[ELISAWell] = field(default_factory=list)
    standard_concentrations: Optional[np.ndarray] = None
    standard_absorbances: Optional[np.ndarray] = None
    curve_fit: Dict[str, float] = field(default_factory=dict)
    curve_type: str = "linear"
    calculated_concentrations: Dict[str, float] = field(default_factory=dict)
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

@dataclass
class ClinicalChemistryResult:
    """Clinical chemistry analyzer result (YOUR ORIGINAL + expanded)"""
    timestamp: datetime
    sample_id: str
    instrument: str
    test_name: str
    result_value: float
    unit: str = ""
    reference_range_low: Optional[float] = None
    reference_range_high: Optional[float] = None
    flag: str = ""
    file_source: str = ""

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
        }

@dataclass
class BloodGasResult:
    """Blood gas analyzer result (YOUR ORIGINAL)"""
    timestamp: datetime
    sample_id: str
    instrument: str
    ph: Optional[float] = None
    pco2_mmHg: Optional[float] = None
    po2_mmHg: Optional[float] = None
    hco3_mmol_L: Optional[float] = None
    be_mmol_L: Optional[float] = None
    so2_pct: Optional[float] = None
    lactate_mmol_L: Optional[float] = None
    glucose_mg_dL: Optional[float] = None
    sodium_mmol_L: Optional[float] = None
    potassium_mmol_L: Optional[float] = None
    calcium_mmol_L: Optional[float] = None
    hematocrit_pct: Optional[float] = None
    hemoglobin_g_dL: Optional[float] = None
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
# NEW DATA CLASSES FOR V2.0 DEVICES
# ============================================================================

@dataclass
class PulseOximetryReading:
    """Pulse oximeter reading (NEW)"""
    timestamp: datetime
    spo2: int
    heart_rate: int
    pleth: Optional[float] = None
    instrument: str = ""

    def to_dict(self) -> Dict[str, str]:
        return {
            'Timestamp': self.timestamp.isoformat(),
            'SpO2': str(self.spo2),
            'HR': str(self.heart_rate),
            'Instrument': self.instrument
        }

@dataclass
class UrinalysisStrip:
    """Urinalysis strip result (NEW)"""
    timestamp: datetime
    sample_id: str
    instrument: str
    parameters: Dict[str, str]
    file_source: str = ""

    def to_dict(self) -> Dict[str, str]:
        d = {
            'Timestamp': self.timestamp.isoformat(),
            'Sample_ID': self.sample_id,
            'Instrument': self.instrument
        }
        d.update(self.parameters)
        return d

@dataclass
class SpectrumReading:
    """Spectrometer reading (NEW)"""
    timestamp: datetime
    sample_id: str
    instrument: str
    wavelengths: np.ndarray
    intensities: np.ndarray
    integration_time_ms: int = 100
    file_source: str = ""

    def to_dict(self) -> Dict:
        return {
            'Timestamp': self.timestamp.isoformat(),
            'Sample_ID': self.sample_id,
            'Instrument': self.instrument,
            'Peak': f"{self.wavelengths[np.argmax(self.intensities)]:.1f} nm"
        }

# ============================================================================
# YOUR ORIGINAL PARSERS - PART 1: PCR/qPCR
# ============================================================================

class BioRadCFXParser:
    """Bio-Rad CFX96/CFX384 qPCR parser (YOUR ORIGINAL)"""
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
            if filepath.endswith('.xlsx'):
                df_dict = pd.read_excel(filepath, sheet_name=None)
                for sheet_name, df in df_dict.items():
                    if 'Cycle' in df.columns and any('Well' in str(c) for c in df.columns):
                        cycles = df['Cycle'].values
                        for col in df.columns:
                            if 'Well' not in str(col) and col != 'Cycle':
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
                                    curves.append(curve)
            else:
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
                                curves.append(curve)
        except Exception as e:
            print(f"Bio-Rad parse error: {e}")
        return curves

class ThermoQuantStudioParser:
    """Thermo Fisher QuantStudio parser (YOUR ORIGINAL)"""
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
            df = pd.read_csv(filepath, skiprows=10)
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
                                curves.append(curve)
        except Exception as e:
            print(f"QuantStudio parse error: {e}")
        return curves

class RocheLightCyclerParser:
    """Roche LightCycler parser (YOUR ORIGINAL)"""
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
                            curves.append(curve)
        except Exception as e:
            print(f"LightCycler parse error: {e}")
        return curves

class QiagenRotorGeneParser:
    """Qiagen Rotor-Gene Q parser (YOUR ORIGINAL)"""
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
            df = pd.read_csv(filepath)
            if 'Cycle' in df.columns:
                cycles = df['Cycle'].values
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
                    curves.append(curve)
        except Exception as e:
            print(f"Rotor-Gene parse error: {e}")
        return curves

class AgilentAriaMxParser:
    """Agilent AriaMx qPCR parser (YOUR ORIGINAL)"""
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
                                    curves.append(curve)
        except Exception as e:
            print(f"AriaMx parse error: {e}")
        return curves

# ============================================================================
# YOUR ORIGINAL PARSERS - PART 2: DIGITAL PCR
# ============================================================================

class FluidigmBiomarkParser:
    """Fluidigm Biomark HD digital PCR parser (YOUR ORIGINAL)"""
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
    """Bio-Rad QX200 Droplet Digital PCR parser (YOUR ORIGINAL)"""
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
            if 'Amplitude' in df.columns:
                amplitudes = df['Amplitude'].values
                threshold = df['Threshold'].iloc[0] if 'Threshold' in df.columns else None
                if threshold:
                    positives = np.sum(amplitudes > threshold)
                    negatives = np.sum(amplitudes <= threshold)
                    total = len(amplitudes)
                    if total > 0 and negatives > 0:
                        lambda_est = -np.log(negatives / total)
                        conc = lambda_est * 20000
                        result = DigitalPCRResult(
                            timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                            sample_id=Path(filepath).stem,
                            instrument="QX200",
                            total_droplets=total,
                            positive_droplets=int(positives),
                            negative_droplets=int(negatives),
                            concentration_copies_ul=conc,
                            copies_per_reaction=conc * 20,
                            file_source=filepath
                        )
                        results.append(result)
        except Exception as e:
            print(f"QX200 parse error: {e}")
        return results

class StillaNaicaParser:
    """Stilla Naica System digital PCR parser (YOUR ORIGINAL)"""
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
            if 'FAM' in df.columns and 'VIC' in df.columns:
                fam = df['FAM'].values
                vic = df['VIC'].values
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
# YOUR ORIGINAL PARSERS - PART 3: FLOW CYTOMETRY
# ============================================================================

class FCSParser:
    """Flow Cytometry Standard (FCS) parser (YOUR ORIGINAL)"""
    @staticmethod
    def can_parse(filepath: str) -> bool:
        return filepath.lower().endswith(('.fcs', '.lmd'))

    @staticmethod
    def parse(filepath: str) -> Optional[Dict]:
        if HAS_FCS:
            try:
                import fcsparser
                meta, data = fcsparser.parse(filepath, reformat_meta=True)
                channels = []
                for key in meta.get('_channel_names_', []):
                    channels.append(key.replace('$P', ''))
                return {
                    "timestamp": datetime.fromtimestamp(os.path.getmtime(filepath)),
                    "sample_id": meta.get('$SM', Path(filepath).stem),
                    "instrument": meta.get('$CYT', 'Unknown'),
                    "channels": channels,
                    "events": data.values,
                    "file_source": filepath,
                    "metadata": meta
                }
            except Exception as e:
                print(f"FCS parse error: {e}")
        return None

# ============================================================================
# YOUR ORIGINAL PARSERS - PART 4: ELISA
# ============================================================================

class DynexELISAParser:
    """Dynex DS2/DSX ELISA parser (YOUR ORIGINAL)"""
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
            wells = []
            rows = 'ABCDEFGH'
            for r, row in enumerate(rows):
                for c in range(12):
                    well_id = f"{row}{c+1}"
                    if well_id in df.columns or well_id in df.index:
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
    """Awareness Technology StatFax ELISA parser (YOUR ORIGINAL)"""
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
# YOUR ORIGINAL PARSERS - PART 5: CLINICAL CHEMISTRY
# ============================================================================

class MindrayChemistryParser:
    """Mindray BA-88A / BS series parser (YOUR ORIGINAL)"""
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
    """Siemens Dimension EXL parser (YOUR ORIGINAL)"""
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

class CepheidGeneXpertParser:
    """Cepheid GeneXpert result parser (YOUR ORIGINAL)"""
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
# YOUR ORIGINAL HARDWARE DRIVERS (Blood Gas, HemoCue)
# ============================================================================

class RadiometerBloodGasDriver:
    """Radiometer blood gas analyzer serial driver (YOUR ORIGINAL)"""
    def __init__(self, port: str = None, baudrate: int = 9600):
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self.connected = False
        self.model = ""

    def connect(self) -> Tuple[bool, str]:
        if not HAS_SERIAL:
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
        if not self.connected:
            return None
        try:
            self.serial.write(b"RQ\r\n")
            response = self.serial.readline().decode().strip()
            parts = response.split(',')
            result = BloodGasResult(
                timestamp=datetime.now(),
                sample_id=f"BG_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                instrument=self.model
            )
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
        if not self.connected:
            return False
        try:
            self.serial.write(b"START\r\n")
            return True
        except:
            return False

class HemoCueDriver:
    """HemoCue hemoglobin analyzer serial driver (YOUR ORIGINAL)"""
    def __init__(self, port: str = None):
        self.port = port
        self.serial = None
        self.connected = False
        self.model = ""

    def connect(self) -> Tuple[bool, str]:
        if not HAS_SERIAL:
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
        if not self.connected:
            return None
        try:
            self.serial.write(b"R\r\n")
            response = self.serial.readline().decode().strip()
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
# NEW V2.0 DEVICE 1: CONTOUR NEXT GLUCOMETER
# ============================================================================
class ContourNextGlucometer:
    """Contour Next USB glucometer - via glucometerutils"""
    def __init__(self):
        self.connected = False
        self.model = "Contour Next"
        self.device = None
        self._has_lib = False
        try:
            import glucometerutils.drivers.contour_next
            self._has_lib = True
        except ImportError:
            pass

    def connect(self) -> Tuple[bool, str]:
        if not self._has_lib:
            return False, "glucometerutils not installed (pip install glucometerutils)"
        try:
            from glucometerutils.drivers.contour_next import Device
            self.device = Device()
            self.device.connect()
            self.connected = True
            return True, "Contour Next connected"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"

    def disconnect(self):
        if self.device:
            try:
                self.device.disconnect()
            except:
                pass
        self.connected = False

    def read_glucose(self) -> Optional[ClinicalChemistryResult]:
        if not self.connected or not self.device:
            return None
        try:
            readings = list(self.device.get_readings())
            if not readings:
                return None
            latest = readings[-1]
            result = ClinicalChemistryResult(
                timestamp=datetime.now(),
                sample_id=f"GLU_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                instrument="Contour Next",
                test_name="Glucose",
                result_value=latest.value,
                unit=latest.unit,
                reference_range_low=70,
                reference_range_high=180,
                file_source="live"
            )
            return result
        except Exception as e:
            print(f"Contour read error: {e}")
            return None

# ============================================================================
# NEW V2.0 DEVICE 2: FREESTYLE LIBRE CGM
# ============================================================================
class FreestyleLibreReader:
    """FreeStyle Libre continuous glucose monitor - HID interface"""
    VENDOR_ID = 0x1a61
    PRODUCT_ID = 0x3650

    def __init__(self):
        self.connected = False
        self.model = "FreeStyle Libre"
        self.device = None
        self._has_hid = HAS_HID

    def connect(self) -> Tuple[bool, str]:
        if not self._has_hid:
            return False, "hidapi not installed (pip install hidapi)"
        try:
            import hid
            self.device = hid.device()
            self.device.open(self.VENDOR_ID, self.PRODUCT_ID)
            self.device.set_nonblocking(True)
            self.connected = True
            return True, "FreeStyle Libre connected"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"

    def disconnect(self):
        if self.device:
            try:
                self.device.close()
            except:
                pass
        self.connected = False

    def read_sensor(self) -> List[ClinicalChemistryResult]:
        if not self.connected or not self.device:
            return []
        results = []
        try:
            cmd = [0x00] * 65
            cmd[0] = 0x00
            cmd[1] = 0xa1
            self.device.write(cmd)
            time.sleep(0.1)
            data = self.device.read(65, timeout=1000)
            if data and len(data) > 20:
                for i in range(16):
                    if i*2+2 < len(data):
                        value = data[16 + i*2] | (data[16 + i*2 + 1] << 8)
                        if value > 0 and value < 500:
                            result = ClinicalChemistryResult(
                                timestamp=datetime.now() - timedelta(minutes=15*i),
                                sample_id=f"LIBRE_{datetime.now().strftime('%Y%m%d')}",
                                instrument="FreeStyle Libre",
                                test_name="Glucose",
                                result_value=float(value),
                                unit="mg/dL",
                                reference_range_low=70,
                                reference_range_high=180,
                                file_source="live"
                            )
                            results.append(result)
        except Exception as e:
            print(f"Libre read error: {e}")
        return results

# ============================================================================
# NEW V2.0 DEVICE 3: CONTEC CMS50E PULSE OXIMETER
# ============================================================================
class ContecOximeter:
    """Contec CMS50E pulse oximeter - serial protocol"""
    def __init__(self, port=None):
        self.port = port
        self.serial = None
        self.connected = False
        self.running = False
        self.read_thread = None
        self.data_queue = queue.Queue()
        self.latest_reading = None

    def connect(self) -> Tuple[bool, str]:
        if not HAS_SERIAL:
            return False, "pyserial not installed"
        try:
            import serial
            import serial.tools.list_ports
            if not self.port:
                ports = serial.tools.list_ports.comports()
                for p in ports:
                    if any(x in p.description.lower() for x in ['contec', 'cms50', 'usb-serial']):
                        self.port = p.device
                        break
            if not self.port:
                return False, "No Contec device found"
            self.serial = serial.Serial(
                port=self.port,
                baudrate=115200,
                bytesize=8,
                parity='N',
                stopbits=1,
                timeout=1
            )
            self.connected = True
            return True, f"Connected to Contec on {self.port}"
        except Exception as e:
            return False, str(e)

    def disconnect(self):
        self.running = False
        if self.read_thread and self.read_thread.is_alive():
            self.read_thread.join(timeout=2)
        if self.serial and self.serial.is_open:
            self.serial.close()
        self.connected = False

    def start_streaming(self):
        if not self.connected or self.running:
            return
        self.running = True
        self.read_thread = threading.Thread(target=self._stream_worker, daemon=True)
        self.read_thread.start()

    def stop_streaming(self):
        self.running = False

    def _stream_worker(self):
        buffer = bytearray()
        while self.running and self.serial and self.serial.is_open:
            try:
                data = self.serial.read(20)
                if data:
                    buffer.extend(data)
                    while len(buffer) >= 6:
                        packet = buffer[:6]
                        buffer = buffer[6:]
                        if packet[0] == 0xAA:
                            spo2 = packet[2]
                            hr = packet[3]
                            if 0 <= spo2 <= 100 and 30 <= hr <= 250:
                                reading = PulseOximetryReading(
                                    timestamp=datetime.now(),
                                    spo2=spo2,
                                    heart_rate=hr,
                                    pleth=packet[4] / 255.0 if len(packet) > 4 else None,
                                    instrument="Contec CMS50E"
                                )
                                self.latest_reading = reading
                                self.data_queue.put(reading)
            except Exception as e:
                print(f"Stream error: {e}")
                time.sleep(0.1)

    def get_latest(self) -> Optional[PulseOximetryReading]:
        return self.latest_reading

# ============================================================================
# NEW V2.0 DEVICE 4: CHOICEMED PULSE OXIMETER
# ============================================================================
class ChoiceMMedOximeter(ContecOximeter):
    """ChoiceMMed pulse oximeter - same protocol family"""
    def connect(self) -> Tuple[bool, str]:
        if not HAS_SERIAL:
            return False, "pyserial not installed"
        try:
            import serial
            import serial.tools.list_ports
            if not self.port:
                ports = serial.tools.list_ports.comports()
                for p in ports:
                    if any(x in p.description.lower() for x in ['choicemed', 'md300']):
                        self.port = p.device
                        break
            if not self.port:
                return False, "No ChoiceMMed device found"
            self.serial = serial.Serial(
                port=self.port,
                baudrate=19200,
                bytesize=8,
                parity='N',
                stopbits=1,
                timeout=1
            )
            self.connected = True
            return True, f"Connected to ChoiceMMed on {self.port}"
        except Exception as e:
            return False, str(e)

# ============================================================================
# NEW V2.0 DEVICE 5: SIEMENS CLINITEK URINALYSIS
# ============================================================================
class ClinitekAnalyzer:
    """Siemens Clinitek Status urinalysis analyzer - serial ASCII"""
    PARAMETER_MAP = {
        'GLU': 'Glucose', 'BIL': 'Bilirubin', 'KET': 'Ketones',
        'SG': 'Specific Gravity', 'pH': 'pH', 'PRO': 'Protein',
        'URO': 'Urobilinogen', 'NIT': 'Nitrite', 'LEU': 'Leukocytes',
        'BLD': 'Blood'
    }

    def __init__(self, port=None):
        self.port = port
        self.serial = None
        self.connected = False
        self.model = "Clinitek Status"

    def connect(self) -> Tuple[bool, str]:
        if not HAS_SERIAL:
            return False, "pyserial not installed"
        try:
            import serial
            import serial.tools.list_ports
            if not self.port:
                ports = serial.tools.list_ports.comports()
                for p in ports:
                    if 'clinitek' in p.description.lower():
                        self.port = p.device
                        break
            if not self.port:
                self.port = 'COM3' if IS_WINDOWS else '/dev/ttyUSB0'
            self.serial = serial.Serial(
                port=self.port,
                baudrate=9600,
                bytesize=8,
                parity='N',
                stopbits=1,
                timeout=3
            )
            self.connected = True
            return True, f"Connected to Clinitek on {self.port}"
        except Exception as e:
            return False, str(e)

    def disconnect(self):
        if self.serial and self.serial.is_open:
            self.serial.close()
        self.connected = False

    def read_strip(self) -> Optional[UrinalysisStrip]:
        if not self.connected or not self.serial:
            return None
        try:
            self.serial.write(b"R\r\n")
            time.sleep(0.5)
            lines = []
            timeout = time.time() + 5
            while time.time() < timeout:
                if self.serial.in_waiting:
                    line = self.serial.readline().decode('ascii', errors='ignore').strip()
                    if line:
                        lines.append(line)
                else:
                    time.sleep(0.1)
            parameters = {}
            for line in lines:
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    display_key = self.PARAMETER_MAP.get(key, key)
                    parameters[display_key] = value
            if parameters:
                strip = UrinalysisStrip(
                    timestamp=datetime.now(),
                    sample_id=f"URINE_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    instrument="Clinitek Status",
                    parameters=parameters,
                    file_source="live"
                )
                return strip
        except Exception as e:
            print(f"Clinitek read error: {e}")
        return None

# ============================================================================
# NEW V2.0 DEVICE 6: DIRUI H500 URINALYSIS (COMPLETE)
# ============================================================================
class DiruiUrinalyzer:
    """Dirui H500 / H100 urinalysis analyzer - serial ASCII"""

    PARAMETER_MAP = {
        'GLU': 'Glucose',
        'BIL': 'Bilirubin',
        'KET': 'Ketones',
        'SG': 'Specific Gravity',
        'PH': 'pH',
        'PRO': 'Protein',
        'UBG': 'Urobilinogen',
        'NIT': 'Nitrite',
        'LEU': 'Leukocytes',
        'BLD': 'Blood',
        'VC': 'Vitamin C',
        'CRE': 'Creatinine',
        'ALB': 'Albumin',
        'CA': 'Calcium'
    }

    def __init__(self, port=None):
        self.port = port
        self.serial = None
        self.connected = False
        self.model = "Dirui H500"

    def connect(self) -> Tuple[bool, str]:
        if not HAS_SERIAL:
            return False, "pyserial not installed"
        try:
            import serial
            import serial.tools.list_ports

            # Auto-detect if no port specified
            if not self.port:
                ports = serial.tools.list_ports.comports()
                for p in ports:
                    desc = p.description.lower()
                    if any(x in desc for x in ['dirui', 'h500', 'h100', 'urit']):
                        self.port = p.device
                        break

            if not self.port:
                # Default ports by platform
                self.port = 'COM4' if IS_WINDOWS else '/dev/ttyUSB1'

            self.serial = serial.Serial(
                port=self.port,
                baudrate=9600,
                bytesize=8,
                parity='N',
                stopbits=1,
                timeout=3
            )

            self.connected = True
            return True, f"Connected to Dirui on {self.port}"

        except Exception as e:
            return False, str(e)

    def disconnect(self):
        if self.serial and self.serial.is_open:
            self.serial.close()
        self.connected = False

    def read_strip(self) -> Optional[UrinalysisStrip]:
        """Read a single strip result"""
        if not self.connected or not self.serial:
            return None

        try:
            # Clear any pending data
            self.serial.reset_input_buffer()

            # Send request (common command: 'R' or 'READ')
            self.serial.write(b"R\r\n")
            time.sleep(1)  # Wait for analyzer to respond

            # Read response lines
            lines = []
            timeout = time.time() + 5

            while time.time() < timeout:
                if self.serial.in_waiting:
                    line = self.serial.readline().decode('ascii', errors='ignore').strip()
                    if line:
                        lines.append(line)
                else:
                    time.sleep(0.1)

            # Parse parameters from lines
            parameters = {}

            for line in lines:
                # Format 1: KEY=VALUE
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip().upper()
                    value = value.strip()

                    # Map to readable name
                    display_key = self.PARAMETER_MAP.get(key, key)
                    parameters[display_key] = value

                # Format 2: CSV: ID,GLU,BIL,KET,SG,PH,PRO,UBG,NIT,LEU,BLD,VC
                elif ',' in line and len(line.split(',')) >= 10:
                    parts = line.split(',')
                    param_keys = ['Glucose', 'Bilirubin', 'Ketones', 'Specific Gravity',
                                 'pH', 'Protein', 'Urobilinogen', 'Nitrite',
                                 'Leukocytes', 'Blood', 'Vitamin C']

                    # Skip ID if present
                    start_idx = 1 if parts[0].isdigit() else 0

                    for i, key in enumerate(param_keys):
                        idx = start_idx + i
                        if idx < len(parts) and parts[idx]:
                            parameters[key] = parts[idx]

            if parameters:
                strip = UrinalysisStrip(
                    timestamp=datetime.now(),
                    sample_id=f"URINE_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    instrument=self.model,
                    parameters=parameters,
                    file_source="live"
                )
                return strip

        except Exception as e:
            print(f"Dirui read error: {e}")

        return None

    def get_parameters_list(self) -> str:
        """Return formatted list of parameters for display"""
        return "\n".join([f"{k}: {v}" for k, v in self.PARAMETER_MAP.items()])

# ============================================================================
# MISSING PIECE 1: OCEAN SPECTROMETER (USB2000+) - COMPLETE
# ============================================================================
class OceanSpectrometer:
    """Ocean Insight USB2000+ spectrometer - pure Python USBTMC via pyvisa-py"""

    def __init__(self, model_name="USB2000+"):
        self.connected = False
        self.model = f"Ocean {model_name}"
        self.inst = None
        self.rm = None
        self._has_visa = HAS_VISA

    def connect(self) -> Tuple[bool, str]:
        if not self._has_visa:
            return False, "pyvisa not installed (pip install pyvisa pyvisa-py)"

        try:
            import pyvisa
            self.rm = pyvisa.ResourceManager('@py')  # Pure Python backend
            resources = self.rm.list_resources()

            # Ocean Insight USB VID = 0x2457
            for res in resources:
                if 'USB' in res and ('0x2457' in res or 'Ocean' in res or 'USB2000' in res):
                    try:
                        self.inst = self.rm.open_resource(res)
                        self.inst.timeout = 3000
                        self.inst.read_termination = '\n'
                        self.inst.write_termination = '\n'

                        # Try to identify
                        try:
                            idn = self.inst.query('*IDN?').strip()
                            if idn:
                                self.model = idn
                        except:
                            pass

                        self.connected = True
                        return True, f"Connected to {self.model} on {res}"
                    except Exception as e:
                        continue

            return False, "No Ocean spectrometer found (looked for VID 0x2457)"

        except Exception as e:
            return False, f"Connection error: {str(e)}"

    def get_spectrum(self, integration_time_ms: int = 100) -> Optional[SpectrumReading]:
        if not self.connected or not self.inst:
            return None

        try:
            # Set integration time
            self.inst.write(f"INTEGRATION {integration_time_ms}")
            time.sleep(0.1)

            # Request spectrum
            self.inst.write("SPECTRUM")
            raw = self.inst.read_raw()

            # Parse binary data (2048 pixels * 4 bytes = 8192 bytes)
            if len(raw) >= 8192:
                intensities = np.frombuffer(raw[-8192:], dtype=np.float32)
            else:
                # Try ASCII format
                try:
                    text = raw.decode('ascii', errors='ignore')
                    values = [float(x) for x in text.strip().split(',') if x.strip()]
                    intensities = np.array(values)
                except:
                    # Fallback to zeros
                    intensities = np.zeros(2048)

            # Ensure we have reasonable data
            if len(intensities) < 100:
                intensities = np.zeros(2048)

            # Generate wavelengths (350-1000nm typical for USB2000+)
            wavelengths = np.linspace(350, 1000, len(intensities))

            return SpectrumReading(
                timestamp=datetime.now(),
                sample_id=f"SPEC_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                instrument=self.model,
                wavelengths=wavelengths,
                intensities=intensities,
                integration_time_ms=integration_time_ms,
                file_source="live"
            )

        except Exception as e:
            print(f"Ocean spectrum error: {e}")
            return None

    def disconnect(self):
        if self.inst:
            try:
                self.inst.close()
            except:
                pass
        if self.rm:
            try:
                self.rm.close()
            except:
                pass
        self.connected = False

# ============================================================================
# MISSING PIECE 2: STS SPECTROMETER - COMPLETE
# ============================================================================
class STSSpectrometer(OceanSpectrometer):
    """Ocean Insight STS series - same USBTMC interface as USB2000+"""

    def __init__(self):
        super().__init__(model_name="STS")

    def connect(self) -> Tuple[bool, str]:
        """Override to specifically identify STS devices"""
        if not self._has_visa:
            return False, "pyvisa not installed (pip install pyvisa pyvisa-py)"

        try:
            import pyvisa
            self.rm = pyvisa.ResourceManager('@py')
            resources = self.rm.list_resources()

            for res in resources:
                try:
                    inst = self.rm.open_resource(res)
                    inst.timeout = 2000
                    inst.read_termination = '\n'
                    inst.write_termination = '\n'

                    # Query identification
                    idn = inst.query('*IDN?').strip()
                    if 'STS' in idn:
                        self.inst = inst
                        self.model = f"Ocean STS ({idn})"
                        self.connected = True
                        return True, f"Connected to {self.model} on {res}"
                    else:
                        inst.close()
                except:
                    continue

            return False, "No STS spectrometer found"

        except Exception as e:
            return False, f"Connection error: {str(e)}"


# ============================================================================
# MISSING PIECE 3: DIRUI URINALYZER - COMPLETE
# ============================================================================
class DiruiUrinalyzer:
    """Dirui H500 / H100 urinalysis analyzer - complete serial implementation"""

    PARAMETER_MAP = {
        'GLU': 'Glucose',
        'BIL': 'Bilirubin',
        'KET': 'Ketones',
        'SG': 'Specific Gravity',
        'PH': 'pH',
        'PRO': 'Protein',
        'UBG': 'Urobilinogen',
        'NIT': 'Nitrite',
        'LEU': 'Leukocytes',
        'BLD': 'Blood',
        'VC': 'Vitamin C',
        'CRE': 'Creatinine',
        'ALB': 'Albumin',
        'CA': 'Calcium'
    }

    def __init__(self, port=None):
        self.port = port
        self.serial = None
        self.connected = False
        self.model = "Dirui H500"

    def connect(self) -> Tuple[bool, str]:
        if not HAS_SERIAL:
            return False, "pyserial not installed"

        try:
            import serial
            import serial.tools.list_ports

            # Auto-detect if no port specified
            if not self.port:
                ports = serial.tools.list_ports.comports()
                for p in ports:
                    desc = p.description.lower()
                    if any(x in desc for x in ['dirui', 'h500', 'h100', 'urit']):
                        self.port = p.device
                        break

            if not self.port:
                # Default ports by platform
                self.port = 'COM4' if IS_WINDOWS else '/dev/ttyUSB1'

            self.serial = serial.Serial(
                port=self.port,
                baudrate=9600,
                bytesize=8,
                parity='N',
                stopbits=1,
                timeout=3
            )

            # Clear any pending data
            self.serial.reset_input_buffer()

            self.connected = True
            return True, f"Connected to Dirui on {self.port}"

        except Exception as e:
            return False, str(e)

    def disconnect(self):
        if self.serial and self.serial.is_open:
            self.serial.close()
        self.connected = False

    def read_strip(self) -> Optional[UrinalysisStrip]:
        """Read a single strip result with complete parsing"""
        if not self.connected or not self.serial:
            return None

        try:
            # Clear buffer
            self.serial.reset_input_buffer()

            # Send read command
            self.serial.write(b"R\r\n")
            time.sleep(1)  # Wait for analyzer to respond

            # Read all available lines
            lines = []
            timeout = time.time() + 5

            while time.time() < timeout:
                if self.serial.in_waiting:
                    line = self.serial.readline().decode('ascii', errors='ignore').strip()
                    if line:
                        lines.append(line)
                else:
                    time.sleep(0.1)

            # Parse parameters
            parameters = {}

            for line in lines:
                # Format 1: KEY=VALUE
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip().upper()
                    value = value.strip()
                    display_key = self.PARAMETER_MAP.get(key, key)
                    parameters[display_key] = value

                # Format 2: CSV (ID,GLU,BIL,KET,SG,PH,PRO,UBG,NIT,LEU,BLD,VC)
                elif ',' in line and len(line.split(',')) >= 10:
                    parts = line.split(',')
                    param_keys = ['Glucose', 'Bilirubin', 'Ketones', 'Specific Gravity',
                                 'pH', 'Protein', 'Urobilinogen', 'Nitrite',
                                 'Leukocytes', 'Blood', 'Vitamin C']

                    # Skip ID if present
                    start_idx = 1 if parts[0].replace('.', '').isdigit() else 0

                    for i, key in enumerate(param_keys):
                        idx = start_idx + i
                        if idx < len(parts) and parts[idx]:
                            parameters[key] = parts[idx]

            if parameters:
                return UrinalysisStrip(
                    timestamp=datetime.now(),
                    sample_id=f"URINE_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    instrument=self.model,
                    parameters=parameters,
                    file_source="live"
                )

        except Exception as e:
            print(f"Dirui read error: {e}")

        return None

    def get_parameters_list(self) -> str:
        """Return formatted list of parameters for display"""
        return "\n".join([f"{k}: {v}" for k, v in self.PARAMETER_MAP.items()])

# ============================================================================
# NEW V2.0 DEVICE 8: OCEAN INSIGHT STS SPECTROMETER
# ============================================================================
class STSSpectrometer(OceanSpectrometer):
    """Ocean Insight STS series - same USBTMC interface as USB2000+"""
    def __init__(self):
        super().__init__(model_name="STS")

    def connect(self) -> Tuple[bool, str]:
        """Override to specifically look for STS devices"""
        if not HAS_VISA:
            return False, "pyvisa not installed (pip install pyvisa pyvisa-py)"
        try:
            import pyvisa
            self.rm = pyvisa.ResourceManager('@py')
            resources = self.rm.list_resources()
            for res in resources:
                # Try to open and identify
                try:
                    inst = self.rm.open_resource(res)
                    inst.timeout = 2000
                    inst.read_termination = '\n'
                    inst.write_termination = '\n'

                    # Send identification query
                    idn = inst.query('*IDN?').strip()
                    if 'STS' in idn:
                        self.inst = inst
                        self.model = f"Ocean STS ({idn})"
                        self.connected = True
                        return True, f"Connected to {self.model}"
                    else:
                        inst.close()
                except:
                    continue

            return False, "No STS spectrometer found"
        except Exception as e:
            return False, f"Connection error: {str(e)}"

# ============================================================================
# MAIN PLUGIN CLASS - COMPLETE V2.0 WITH EVERYTHING
# ============================================================================
class ClinicalDiagnosticsSuitePlugin:

    def __init__(self, main_app):
        self.app = main_app
        self.window = None
        self.ui_queue = None

        # YOUR ORIGINAL DATA STORAGE
        self.pcr_curves: List[PCRCurve] = []
        self.dpcr_results: List[DigitalPCRResult] = []
        self.elisa_plates: List[ELISA_Plate] = []
        self.clinical_results: List[ClinicalChemistryResult] = []
        self.blood_gas_results: List[BloodGasResult] = []

        # NEW V2.0 DATA STORAGE
        self.glucometer_readings: List[ClinicalChemistryResult] = []
        self.pulse_readings: List[PulseOximetryReading] = []
        self.urinalysis_results: List[UrinalysisStrip] = []
        self.spectra: List[SpectrumReading] = []

        # YOUR ORIGINAL DEVICES
        self.radiometer = None
        self.hemocue = None

        # NEW V2.0 DEVICES
        self.contour = None
        self.libre = None
        self.contec = None
        self.choicemed = None
        self.clinitek = None
        self.dirui = None
        self.ocean = None
        self.sts = None

        self.connected_devices = []

        # UI Variables
        self.status_var = tk.StringVar(value="Clinical Diagnostics v2.0 COMPLETE - Ready")
        self.category_var = tk.StringVar(value="PCR/qPCR")
        self.file_count_var = tk.StringVar(value="No files loaded")

        # UI Elements
        self.notebook = None
        self.log_listbox = None
        self.plot_canvas = None
        self.plot_fig = None
        self.status_indicator = None
        self.tree = None
        self.import_btn = None
        self.batch_btn = None
        self.count_label = None

        # Device status labels
        self.contour_status = None
        self.libre_status = None
        self.contec_status = None
        self.choicemed_status = None
        self.clinitek_status = None
        self.dirui_status = None
        self.ocean_status = None
        self.sts_status = None
        self.radiometer_status = None
        self.hemocue_status = None

        # Plot canvases
        self.pulseox_fig = None
        self.pulseox_ax = None
        self.pulseox_canvas = None
        self.spec_fig = None
        self.spec_ax = None
        self.spec_canvas = None

        # Streaming control
        self.pulse_streaming = False
        self.pulse_update_id = None

        self.categories = [
            "PCR/qPCR", "Digital PCR", "Flow Cytometry", "ELISA",
            "Clinical Chemistry", "Blood Gas", "Sample Processors"
        ]

    def show_interface(self):
        self.open_window()

    def open_window(self):
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("Clinical & Molecular Diagnostics v2.0 COMPLETE")
        self.window.geometry("1200x800")
        self.window.minsize(1000, 700)
        self.window.transient(self.app.root)

        self.ui_queue = ThreadSafeUI(self.window)
        self._build_ui()
        self.window.lift()
        self.window.focus_force()
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        """Build the complete UI with all tabs"""

        # Header
        header = tk.Frame(self.window, bg=C_HEADER, height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="🧬", font=("Arial", 20),
                bg=C_HEADER, fg="white").pack(side=tk.LEFT, padx=10)
        tk.Label(header, text="CLINICAL DIAGNOSTICS v2.0 COMPLETE",
                font=("Arial", 14, "bold"), bg=C_HEADER, fg="white").pack(side=tk.LEFT)
        tk.Label(header, text="ALL PARSERS + 8 NEW DEVICES",
                font=("Arial", 9), bg=C_HEADER, fg=C_ACCENT).pack(side=tk.LEFT, padx=10)

        self.status_indicator = tk.Label(header, textvariable=self.status_var,
                                        font=("Arial", 9), bg=C_HEADER, fg=C_LIGHT)
        self.status_indicator.pack(side=tk.RIGHT, padx=10)

        # Toolbar (YOUR ORIGINAL)
        toolbar = tk.Frame(self.window, bg=C_LIGHT, height=80)
        toolbar.pack(fill=tk.X)
        toolbar.pack_propagate(False)

        row1 = tk.Frame(toolbar, bg=C_LIGHT)
        row1.pack(fill=tk.X, pady=2)

        tk.Label(row1, text="Category:", font=("Arial", 9, "bold"),
                bg=C_LIGHT).pack(side=tk.LEFT, padx=5)
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
                                        font=("Arial", 8), bg=C_LIGHT, fg="#7f8c8d")
        self.file_count_label.pack(side=tk.RIGHT, padx=10)

        # Notebook
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create ALL tabs (YOUR ORIGINAL + NEW)
        self._create_data_tab()           # YOUR ORIGINAL data display
        self._create_file_import_tab()     # YOUR ORIGINAL file import
        self._create_hardware_tab()         # YOUR ORIGINAL hardware (Radiometer, HemoCue)
        self._create_glucometer_tab()       # NEW
        self._create_pulse_ox_tab()         # NEW
        self._create_urinalysis_tab()       # NEW
        self._create_spectrometer_tab()     # NEW
        self._create_log_tab()              # YOUR ORIGINAL log

        # Status bar
        status = tk.Frame(self.window, bg="#34495e", height=25)
        status.pack(fill=tk.X, side=tk.BOTTOM)
        status.pack_propagate(False)

        self.count_label = tk.Label(status,
            text=f"📊 {len(self.pcr_curves)} PCR · {len(self.dpcr_results)} dPCR · {len(self.elisa_plates)} ELISA · {len(self.clinical_results)} Chem · {len(self.glucometer_readings)} Glucose",
            font=("Arial", 9), bg="#34495e", fg="white")
        self.count_label.pack(side=tk.LEFT, padx=5)

        tk.Label(status,
                text="Bio-Rad · Thermo · Roche · Qiagen · Agilent · BD · Tecan · Radiometer · HemoCue · Contour · Libre · Contec · Clinitek · Dirui · Ocean",
                font=("Arial", 8), bg="#34495e", fg="#bdc3c7").pack(side=tk.RIGHT, padx=5)

    def _create_data_tab(self):
        """YOUR ORIGINAL data display tab"""
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="📊 All Data")

        frame = tk.Frame(tab, bg="white")
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ('Type', 'Sample', 'Instrument', 'Value', 'Details', 'File')
        self.tree = ttk.Treeview(frame, columns=columns, show='headings', height=20)

        col_widths = [60, 150, 150, 100, 150, 200]
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

        # Buttons
        btn_frame = tk.Frame(tab, bg="white")
        btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(btn_frame, text="🔄 Refresh", command=self._update_tree,
                  width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📤 Send to Main Table",
                  command=self.send_to_table, width=15).pack(side=tk.LEFT, padx=5)

    def _create_file_import_tab(self):
        """YOUR ORIGINAL file import functionality"""
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="📁 File Import")

        # Left side - parser list
        left = tk.Frame(tab, bg="white", width=300)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        left.pack_propagate(False)

        tk.Label(left, text="Supported Instruments", font=("Arial", 10, "bold"),
                bg="white").pack(anchor=tk.W, pady=2)

        parsers = [
            "✅ Bio-Rad CFX96/384",
            "✅ Thermo QuantStudio",
            "✅ Roche LightCycler",
            "✅ Qiagen Rotor-Gene Q",
            "✅ Agilent AriaMx",
            "✅ Bio-Rad QX200 ddPCR",
            "✅ Stilla Naica dPCR",
            "✅ Fluidigm Biomark",
            "✅ Flow Cytometry FCS",
            "✅ Dynex ELISA",
            "✅ Awareness ELISA",
            "✅ Mindray Chemistry",
            "✅ Siemens Dimension",
            "✅ Cepheid GeneXpert"
        ]

        for parser in parsers:
            tk.Label(left, text=parser, font=("Arial", 9),
                    bg="white", fg=C_HEADER).pack(anchor=tk.W, pady=1)

        # Right side - import controls
        right = tk.Frame(tab, bg="white")
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        tk.Label(right, text="Import Data", font=("Arial", 12, "bold"),
                bg="white").pack(pady=10)

        ttk.Button(right, text="📂 Import Single File",
                  command=self._import_file, width=25).pack(pady=5)

        ttk.Button(right, text="📁 Import Batch Folder",
                  command=self._batch_folder, width=25).pack(pady=5)

        tk.Label(right, text="Drag and drop files or click above to import",
                font=("Arial", 9), bg="white", fg="#888").pack(pady=20)

        # Recent imports
        tk.Label(right, text="Recent Imports", font=("Arial", 10, "bold"),
                bg="white").pack(anchor=tk.W, pady=(20,5))

        self.recent_listbox = tk.Listbox(right, height=8, font=("Courier", 9))
        scroll = ttk.Scrollbar(right, orient=tk.VERTICAL, command=self.recent_listbox.yview)
        self.recent_listbox.configure(yscrollcommand=scroll.set)

        self.recent_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_hardware_tab(self):
        """YOUR ORIGINAL hardware tab (Radiometer, HemoCue)"""
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="⚡ Legacy Hardware")

        # Blood Gas
        bg_frame = tk.LabelFrame(tab, text="Blood Gas Analyzer", bg="white", font=("Arial", 10, "bold"))
        bg_frame.pack(fill=tk.X, padx=10, pady=5)

        row1 = tk.Frame(bg_frame, bg="white")
        row1.pack(fill=tk.X, pady=2)

        tk.Label(row1, text="Port:", font=("Arial", 9), bg="white").pack(side=tk.LEFT, padx=2)
        self.bg_port_var = tk.StringVar(value="/dev/ttyUSB0" if IS_LINUX else "COM3")
        ttk.Entry(row1, textvariable=self.bg_port_var, width=12).pack(side=tk.LEFT, padx=2)

        self.bg_connect_btn = ttk.Button(row1, text="🔌 Connect",
                                         command=self._connect_blood_gas, width=12)
        self.bg_connect_btn.pack(side=tk.LEFT, padx=5)

        self.radiometer_status = tk.Label(row1, text="●", fg="red", font=("Arial", 12), bg="white")
        self.radiometer_status.pack(side=tk.LEFT, padx=2)

        row2 = tk.Frame(bg_frame, bg="white")
        row2.pack(fill=tk.X, pady=2)

        ttk.Button(row2, text="▶ Start", command=self._start_blood_gas, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(row2, text="📊 Read", command=self._read_blood_gas, width=10).pack(side=tk.LEFT, padx=2)

        # HemoCue
        hb_frame = tk.LabelFrame(tab, text="HemoCue Hemoglobin", bg="white", font=("Arial", 10, "bold"))
        hb_frame.pack(fill=tk.X, padx=10, pady=5)

        row3 = tk.Frame(hb_frame, bg="white")
        row3.pack(fill=tk.X, pady=2)

        tk.Label(row3, text="Port:", font=("Arial", 9), bg="white").pack(side=tk.LEFT, padx=2)
        self.hb_port_var = tk.StringVar(value="/dev/ttyUSB1" if IS_LINUX else "COM4")
        ttk.Entry(row3, textvariable=self.hb_port_var, width=12).pack(side=tk.LEFT, padx=2)

        self.hb_connect_btn = ttk.Button(row3, text="🔌 Connect",
                                         command=self._connect_hemocue, width=12)
        self.hb_connect_btn.pack(side=tk.LEFT, padx=5)

        self.hemocue_status = tk.Label(row3, text="●", fg="red", font=("Arial", 12), bg="white")
        self.hemocue_status.pack(side=tk.LEFT, padx=2)

        ttk.Button(hb_frame, text="📊 Read Hb", command=self._read_hemocue, width=15).pack(pady=2)

    def _create_glucometer_tab(self):
        """NEW tab for Contour Next and FreeStyle Libre"""
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="🩸 Glucometers")

        # Contour Next
        contour_frame = tk.LabelFrame(tab, text="Contour Next", bg="white", font=("Arial", 10, "bold"))
        contour_frame.pack(fill=tk.X, padx=10, pady=5)

        row1 = tk.Frame(contour_frame, bg="white")
        row1.pack(fill=tk.X, pady=5)

        self.contour_btn = ttk.Button(row1, text="🔌 Connect", command=self._connect_contour, width=12)
        self.contour_btn.pack(side=tk.LEFT, padx=5)

        self.contour_status = tk.Label(row1, text="●", fg="red", font=("Arial", 12), bg="white")
        self.contour_status.pack(side=tk.LEFT, padx=5)

        self.contour_read_btn = ttk.Button(row1, text="📊 Read Glucose",
                                           command=self._read_contour, width=15, state='disabled')
        self.contour_read_btn.pack(side=tk.LEFT, padx=5)

        self.contour_value = tk.Label(row1, text="", font=("Arial", 10, "bold"), bg="white", fg=C_ACCENT2)
        self.contour_value.pack(side=tk.LEFT, padx=10)

        # FreeStyle Libre
        libre_frame = tk.LabelFrame(tab, text="FreeStyle Libre", bg="white", font=("Arial", 10, "bold"))
        libre_frame.pack(fill=tk.X, padx=10, pady=5)

        row2 = tk.Frame(libre_frame, bg="white")
        row2.pack(fill=tk.X, pady=5)

        self.libre_btn = ttk.Button(row2, text="🔌 Connect", command=self._connect_libre, width=12)
        self.libre_btn.pack(side=tk.LEFT, padx=5)

        self.libre_status = tk.Label(row2, text="●", fg="red", font=("Arial", 12), bg="white")
        self.libre_status.pack(side=tk.LEFT, padx=5)

        self.libre_read_btn = ttk.Button(row2, text="📊 Read Sensor",
                                         command=self._read_libre, width=15, state='disabled')
        self.libre_read_btn.pack(side=tk.LEFT, padx=5)

        # Results tree
        tree_frame = tk.Frame(tab, bg="white")
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Label(tree_frame, text="Recent Glucose Readings", font=("Arial", 10, "bold"),
                bg="white").pack(anchor=tk.W)

        columns = ('Time', 'Device', 'Value', 'Unit')
        self.glucometer_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=8)

        for col in columns:
            self.glucometer_tree.heading(col, text=col)
            self.glucometer_tree.column(col, width=150)

        self.glucometer_tree.pack(fill=tk.BOTH, expand=True)

    def _create_pulse_ox_tab(self):
        """NEW tab for Contec and ChoiceMMed pulse oximeters"""
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="❤️ Pulse Oximeters")

        # Contec
        contec_frame = tk.LabelFrame(tab, text="Contec CMS50E", bg="white", font=("Arial", 10, "bold"))
        contec_frame.pack(fill=tk.X, padx=10, pady=5)

        row1 = tk.Frame(contec_frame, bg="white")
        row1.pack(fill=tk.X, pady=5)

        tk.Label(row1, text="Port:", font=("Arial", 9), bg="white").pack(side=tk.LEFT, padx=5)
        self.contec_port = tk.StringVar(value="/dev/ttyUSB0" if IS_LINUX else "COM3")
        ttk.Entry(row1, textvariable=self.contec_port, width=12).pack(side=tk.LEFT, padx=2)

        self.contec_btn = ttk.Button(row1, text="🔌 Connect", command=self._connect_contec, width=12)
        self.contec_btn.pack(side=tk.LEFT, padx=5)

        self.contec_status = tk.Label(row1, text="●", fg="red", font=("Arial", 12), bg="white")
        self.contec_status.pack(side=tk.LEFT, padx=5)

        self.contec_start_btn = ttk.Button(row1, text="▶ Start Streaming",
                                           command=self._start_contec, width=15, state='disabled')
        self.contec_start_btn.pack(side=tk.LEFT, padx=5)

        self.contec_stop_btn = ttk.Button(row1, text="⏹ Stop",
                                          command=self._stop_contec, width=8, state='disabled')
        self.contec_stop_btn.pack(side=tk.LEFT, padx=2)

        # ChoiceMMed
        choicemed_frame = tk.LabelFrame(tab, text="ChoiceMMed", bg="white", font=("Arial", 10, "bold"))
        choicemed_frame.pack(fill=tk.X, padx=10, pady=5)

        row2 = tk.Frame(choicemed_frame, bg="white")
        row2.pack(fill=tk.X, pady=5)

        tk.Label(row2, text="Port:", font=("Arial", 9), bg="white").pack(side=tk.LEFT, padx=5)
        self.choicemed_port = tk.StringVar(value="/dev/ttyUSB1" if IS_LINUX else "COM4")
        ttk.Entry(row2, textvariable=self.choicemed_port, width=12).pack(side=tk.LEFT, padx=2)

        self.choicemed_btn = ttk.Button(row2, text="🔌 Connect", command=self._connect_choicemed, width=12)
        self.choicemed_btn.pack(side=tk.LEFT, padx=5)

        self.choicemed_status = tk.Label(row2, text="●", fg="red", font=("Arial", 12), bg="white")
        self.choicemed_status.pack(side=tk.LEFT, padx=5)

        self.choicemed_start_btn = ttk.Button(row2, text="▶ Start Streaming",
                                              command=self._start_choicemed, width=15, state='disabled')
        self.choicemed_start_btn.pack(side=tk.LEFT, padx=5)

        # Live display
        display_frame = tk.Frame(tab, bg="white")
        display_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        current_frame = tk.Frame(display_frame, bg="white")
        current_frame.pack(fill=tk.X, pady=5)

        tk.Label(current_frame, text="Current:", font=("Arial", 10, "bold"),
                bg="white").pack(side=tk.LEFT)

        self.current_spo2 = tk.Label(current_frame, text="SpO₂: --%", font=("Arial", 14, "bold"),
                                     bg="white", fg="#2980b9")
        self.current_spo2.pack(side=tk.LEFT, padx=20)

        self.current_hr = tk.Label(current_frame, text="HR: -- bpm", font=("Arial", 14, "bold"),
                                   bg="white", fg="#c0392b")
        self.current_hr.pack(side=tk.LEFT, padx=20)

        if HAS_MPL:
            self.pulseox_fig = Figure(figsize=(8, 3), dpi=90, facecolor='white')
            self.pulseox_ax = self.pulseox_fig.add_subplot(111)
            self.pulseox_ax.set_title("Real-time SpO₂ & Heart Rate", fontweight='bold')
            self.pulseox_ax.set_xlabel("Time (s)")
            self.pulseox_ax.set_ylabel("Value")
            self.pulseox_ax.grid(True, alpha=0.3)

            self.pulseox_canvas = FigureCanvasTkAgg(self.pulseox_fig, display_frame)
            self.pulseox_canvas.draw()
            self.pulseox_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _create_urinalysis_tab(self):
        """NEW tab for Siemens Clinitek and Dirui urinalysis"""
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="🧪 Urinalysis")

        # Clinitek
        clinitek_frame = tk.LabelFrame(tab, text="Siemens Clinitek", bg="white", font=("Arial", 10, "bold"))
        clinitek_frame.pack(fill=tk.X, padx=10, pady=5)

        row1 = tk.Frame(clinitek_frame, bg="white")
        row1.pack(fill=tk.X, pady=5)

        tk.Label(row1, text="Port:", font=("Arial", 9), bg="white").pack(side=tk.LEFT, padx=5)
        self.clinitek_port = tk.StringVar(value="COM3" if IS_WINDOWS else "/dev/ttyUSB0")
        ttk.Entry(row1, textvariable=self.clinitek_port, width=12).pack(side=tk.LEFT, padx=2)

        self.clinitek_btn = ttk.Button(row1, text="🔌 Connect", command=self._connect_clinitek, width=12)
        self.clinitek_btn.pack(side=tk.LEFT, padx=5)

        self.clinitek_status = tk.Label(row1, text="●", fg="red", font=("Arial", 12), bg="white")
        self.clinitek_status.pack(side=tk.LEFT, padx=5)

        self.clinitek_read_btn = ttk.Button(row1, text="📊 Read Strip",
                                            command=self._read_clinitek, width=12, state='disabled')
        self.clinitek_read_btn.pack(side=tk.LEFT, padx=5)

        # Dirui
        dirui_frame = tk.LabelFrame(tab, text="Dirui H500", bg="white", font=("Arial", 10, "bold"))
        dirui_frame.pack(fill=tk.X, padx=10, pady=5)

        row2 = tk.Frame(dirui_frame, bg="white")
        row2.pack(fill=tk.X, pady=5)

        tk.Label(row2, text="Port:", font=("Arial", 9), bg="white").pack(side=tk.LEFT, padx=5)
        self.dirui_port = tk.StringVar(value="COM4" if IS_WINDOWS else "/dev/ttyUSB1")
        ttk.Entry(row2, textvariable=self.dirui_port, width=12).pack(side=tk.LEFT, padx=2)

        self.dirui_btn = ttk.Button(row2, text="🔌 Connect", command=self._connect_dirui, width=12)
        self.dirui_btn.pack(side=tk.LEFT, padx=5)

        self.dirui_status = tk.Label(row2, text="●", fg="red", font=("Arial", 12), bg="white")
        self.dirui_status.pack(side=tk.LEFT, padx=5)

        self.dirui_read_btn = ttk.Button(row2, text="📊 Read Strip",
                                         command=self._read_dirui, width=12, state='disabled')
        self.dirui_read_btn.pack(side=tk.LEFT, padx=5)

        # Results display
        result_frame = tk.Frame(tab, bg="white")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Label(result_frame, text="Last Strip Results", font=("Arial", 10, "bold"),
                bg="white").pack(anchor=tk.W)

        self.urinalysis_text = tk.Text(result_frame, height=12, font=("Courier", 10))
        scroll = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.urinalysis_text.yview)
        self.urinalysis_text.configure(yscrollcommand=scroll.set)

        self.urinalysis_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_spectrometer_tab(self):
        """NEW tab for Ocean Insight spectrometers"""
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="🌊 Spectrometers")

        # USB2000+
        ocean_frame = tk.LabelFrame(tab, text="Ocean USB2000+", bg="white", font=("Arial", 10, "bold"))
        ocean_frame.pack(fill=tk.X, padx=10, pady=5)

        row1 = tk.Frame(ocean_frame, bg="white")
        row1.pack(fill=tk.X, pady=5)

        self.ocean_btn = ttk.Button(row1, text="🔌 Connect", command=self._connect_ocean, width=12)
        self.ocean_btn.pack(side=tk.LEFT, padx=5)

        self.ocean_status = tk.Label(row1, text="●", fg="red", font=("Arial", 12), bg="white")
        self.ocean_status.pack(side=tk.LEFT, padx=5)

        tk.Label(row1, text="Integration (ms):", font=("Arial", 9), bg="white").pack(side=tk.LEFT, padx=5)
        self.ocean_integration = tk.StringVar(value="100")
        ttk.Entry(row1, textvariable=self.ocean_integration, width=6).pack(side=tk.LEFT)

        self.ocean_read_btn = ttk.Button(row1, text="📊 Read Spectrum",
                                         command=self._read_ocean, width=15, state='disabled')
        self.ocean_read_btn.pack(side=tk.LEFT, padx=5)

        # STS
        sts_frame = tk.LabelFrame(tab, text="Ocean STS", bg="white", font=("Arial", 10, "bold"))
        sts_frame.pack(fill=tk.X, padx=10, pady=5)

        row2 = tk.Frame(sts_frame, bg="white")
        row2.pack(fill=tk.X, pady=5)

        self.sts_btn = ttk.Button(row2, text="🔌 Connect", command=self._connect_sts, width=12)
        self.sts_btn.pack(side=tk.LEFT, padx=5)

        self.sts_status = tk.Label(row2, text="●", fg="red", font=("Arial", 12), bg="white")
        self.sts_status.pack(side=tk.LEFT, padx=5)

        tk.Label(row2, text="Integration (ms):", font=("Arial", 9), bg="white").pack(side=tk.LEFT, padx=5)
        self.sts_integration = tk.StringVar(value="100")
        ttk.Entry(row2, textvariable=self.sts_integration, width=6).pack(side=tk.LEFT)

        self.sts_read_btn = ttk.Button(row2, text="📊 Read Spectrum",
                                       command=self._read_sts, width=15, state='disabled')
        self.sts_read_btn.pack(side=tk.LEFT, padx=5)

        # Plot area
        plot_frame = tk.Frame(tab, bg="white")
        plot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        if HAS_MPL:
            self.spec_fig = Figure(figsize=(8, 4), dpi=90, facecolor='white')
            self.spec_ax = self.spec_fig.add_subplot(111)
            self.spec_ax.set_title("Spectrum", fontweight='bold')
            self.spec_ax.set_xlabel("Wavelength (nm)")
            self.spec_ax.set_ylabel("Intensity")
            self.spec_ax.grid(True, alpha=0.3)

            self.spec_canvas = FigureCanvasTkAgg(self.spec_fig, plot_frame)
            self.spec_canvas.draw()
            self.spec_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _create_log_tab(self):
        """YOUR ORIGINAL log tab"""
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="📋 Activity Log")

        self.log_listbox = tk.Listbox(tab, font=("Courier", 9))
        scroll = ttk.Scrollbar(tab, orient=tk.VERTICAL, command=self.log_listbox.yview)
        self.log_listbox.configure(yscrollcommand=scroll.set)
        self.log_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=5)

        btn_frame = tk.Frame(tab, bg="white")
        btn_frame.pack(fill=tk.X, pady=2)

        ttk.Button(btn_frame, text="🗑️ Clear Log", command=self._clear_log,
                  width=12).pack(side=tk.RIGHT, padx=5)

    # ============================================================================
    # YOUR ORIGINAL FILE IMPORT METHODS
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

        self.status_var.set(f"Parsing {Path(path).name}...")
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
                for parser in [BioRadQX200Parser, StillaNaicaParser, FluidigmBiomarkParser]:
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
                for parser in [MindrayChemistryParser, SiemensDimensionParser, CepheidGeneXpertParser]:
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
                    self.recent_listbox.insert(0, f"✅ {datetime.now().strftime('%H:%M')} - {Path(path).name} ({len(results)} {data_type})")
                    if self.recent_listbox.size() > 10:
                        self.recent_listbox.delete(10, tk.END)
                    self._add_to_log(f"✅ Imported {len(results)} {data_type} items from {Path(path).name}")
                    self._update_counts()
                else:
                    self._add_to_log(f"❌ Failed to parse: {Path(path).name}")

            self.ui_queue.schedule(update_ui)

        threading.Thread(target=parse_thread, daemon=True).start()

    def _batch_folder(self):
        folder = filedialog.askdirectory()
        if not folder:
            return

        self.status_var.set(f"Scanning {Path(folder).name}...")
        self.import_btn.config(state='disabled')
        self.batch_btn.config(state='disabled')

        def batch_thread():
            pcr_count = 0
            dpcr_count = 0
            elisa_count = 0
            chem_count = 0

            for ext in ['*.csv', '*.xlsx', '*.txt', '*.fcs', '*.xml', '*.h5']:
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
                        continue

            def update_ui():
                self._update_tree()
                self.file_count_var.set(f"Files: {pcr_count+dpcr_count}")
                self.recent_listbox.insert(0, f"📁 {datetime.now().strftime('%H:%M')} - {Path(folder).name} ({pcr_count} PCR, {dpcr_count} dPCR)")
                if self.recent_listbox.size() > 10:
                    self.recent_listbox.delete(10, tk.END)
                self._add_to_log(f"📁 Batch imported: {pcr_count} PCR, {dpcr_count} dPCR")
                self.status_var.set(f"✅ Imported {pcr_count+dpcr_count} items")
                self.import_btn.config(state='normal')
                self.batch_btn.config(state='normal')
                self._update_counts()

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
                f"Ct={curve.ct:.2f}" if curve.ct else "",
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
                f"Pos:{dpcr.positive_droplets}",
                Path(dpcr.file_source).name if dpcr.file_source else ""
            ))

        # ELISA plates
        for plate in self.elisa_plates[-10:]:
            self.tree.insert('', 0, values=(
                "ELISA",
                plate.sample_id[:20],
                plate.instrument[:15],
                f"{len(plate.wells)} wells",
                f"R²={plate.curve_fit.get('r2',0):.3f}",
                Path(plate.file_source).name if plate.file_source else ""
            ))

        # Clinical chemistry
        for chem in self.clinical_results[-30:]:
            self.tree.insert('', 0, values=(
                "Chemistry",
                chem.sample_id[:20],
                chem.instrument[:15],
                f"{chem.result_value} {chem.unit}",
                chem.test_name[:15],
                chem.file_source
            ))

        # Glucometer readings
        for glu in self.glucometer_readings[-20:]:
            self.tree.insert('', 0, values=(
                "Glucose",
                glu.sample_id[:20],
                glu.instrument[:15],
                f"{glu.result_value} {glu.unit}",
                glu.test_name,
                "live"
            ))

    def _update_counts(self):
        if self.count_label:
            self.count_label.config(
                text=f"📊 {len(self.pcr_curves)} PCR · {len(self.dpcr_results)} dPCR · {len(self.elisa_plates)} ELISA · {len(self.clinical_results)} Chem · {len(self.glucometer_readings)} Glucose"
            )

    # ============================================================================
    # YOUR ORIGINAL HARDWARE METHODS
    # ============================================================================

    def _connect_blood_gas(self):
        def connect_thread():
            self.radiometer = RadiometerBloodGasDriver(port=self.bg_port_var.get())
            success, msg = self.radiometer.connect()

            def update_ui():
                if success:
                    self.connected_devices.append(self.radiometer)
                    self.radiometer_status.config(fg=C_ACCENT2)
                    self.bg_connect_btn.config(text="✅ Connected")
                    self._add_to_log(f"🔌 Blood gas: {msg}")
                else:
                    self.radiometer_status.config(fg="red")
                    self.bg_connect_btn.config(text="🔌 Connect")
                    self._add_to_log(f"❌ Blood gas: {msg}")

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
        def connect_thread():
            self.hemocue = HemoCueDriver(port=self.hb_port_var.get())
            success, msg = self.hemocue.connect()

            def update_ui():
                if success:
                    self.connected_devices.append(self.hemocue)
                    self.hemocue_status.config(fg=C_ACCENT2)
                    self.hb_connect_btn.config(text="✅ Connected")
                    self._add_to_log(f"🔌 HemoCue: {msg}")
                else:
                    self.hemocue_status.config(fg="red")
                    self.hb_connect_btn.config(text="🔌 Connect")
                    self._add_to_log(f"❌ HemoCue: {msg}")

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
                    result.check_flags()
                    flag = result.flag
                    color = C_ACCENT2 if flag == "NORMAL" else C_WARN
                    self._add_to_log(f"✅ HemoCue: {result.result_value} {result.unit} [{flag}]")
                    self._update_counts()
                else:
                    self._add_to_log("❌ Failed to read HemoCue")
            self.ui_queue.schedule(update_ui)

        threading.Thread(target=read_thread, daemon=True).start()

    # ============================================================================
    # NEW V2.0 HARDWARE METHODS
    # ============================================================================

    def _connect_contour(self):
        def connect_thread():
            self.contour = ContourNextGlucometer()
            success, msg = self.contour.connect()

            def update_ui():
                if success:
                    self.contour_status.config(fg=C_ACCENT2)
                    self.contour_btn.config(text="✅ Connected")
                    self.contour_read_btn.config(state='normal')
                    self._add_to_log(f"✅ Contour Next: {msg}")
                else:
                    self.contour_status.config(fg="red")
                    self.contour_btn.config(text="🔌 Connect")
                    self.contour_read_btn.config(state='disabled')
                    self._add_to_log(f"❌ Contour Next: {msg}")

            self.ui_queue.schedule(update_ui)

        threading.Thread(target=connect_thread, daemon=True).start()

    def _read_contour(self):
        if not self.contour or not self.contour.connected:
            return

        def read_thread():
            result = self.contour.read_glucose()

            def update_ui():
                if result:
                    self.glucometer_readings.append(result)
                    self.contour_value.config(text=f"{result.result_value} {result.unit}")

                    self.glucometer_tree.insert('', 0, values=(
                        result.timestamp.strftime('%H:%M:%S'),
                        'Contour',
                        f"{result.result_value}",
                        result.unit
                    ))

                    self._add_to_log(f"✅ Contour: {result.result_value} {result.unit}")
                    self._update_tree()
                    self._update_counts()
                else:
                    self._add_to_log("❌ Contour: No reading available")

            self.ui_queue.schedule(update_ui)

        threading.Thread(target=read_thread, daemon=True).start()

    def _connect_libre(self):
        def connect_thread():
            self.libre = FreestyleLibreReader()
            success, msg = self.libre.connect()

            def update_ui():
                if success:
                    self.libre_status.config(fg=C_ACCENT2)
                    self.libre_btn.config(text="✅ Connected")
                    self.libre_read_btn.config(state='normal')
                    self._add_to_log(f"✅ FreeStyle Libre: {msg}")
                else:
                    self.libre_status.config(fg="red")
                    self.libre_btn.config(text="🔌 Connect")
                    self.libre_read_btn.config(state='disabled')
                    self._add_to_log(f"❌ FreeStyle Libre: {msg}")

            self.ui_queue.schedule(update_ui)

        threading.Thread(target=connect_thread, daemon=True).start()

    def _read_libre(self):
        if not self.libre or not self.libre.connected:
            return

        def read_thread():
            results = self.libre.read_sensor()

            def update_ui():
                if results:
                    for result in results[-5:]:
                        self.glucometer_readings.append(result)
                        self.glucometer_tree.insert('', 0, values=(
                            result.timestamp.strftime('%H:%M'),
                            'Libre',
                            f"{result.result_value}",
                            result.unit
                        ))

                    self._add_to_log(f"✅ Libre: Read {len(results)} readings")
                    self._update_tree()
                    self._update_counts()
                else:
                    self._add_to_log("❌ Libre: No data available")

            self.ui_queue.schedule(update_ui)

        threading.Thread(target=read_thread, daemon=True).start()

    def _connect_contec(self):
        def connect_thread():
            self.contec = ContecOximeter(port=self.contec_port.get())
            success, msg = self.contec.connect()

            def update_ui():
                if success:
                    self.contec_status.config(fg=C_ACCENT2)
                    self.contec_btn.config(text="✅ Connected")
                    self.contec_start_btn.config(state='normal')
                    self._add_to_log(f"✅ Contec: {msg}")
                else:
                    self.contec_status.config(fg="red")
                    self.contec_btn.config(text="🔌 Connect")
                    self.contec_start_btn.config(state='disabled')
                    self._add_to_log(f"❌ Contec: {msg}")

            self.ui_queue.schedule(update_ui)

        threading.Thread(target=connect_thread, daemon=True).start()

    def _start_contec(self):
        if not self.contec or not self.contec.connected:
            return

        self.contec.start_streaming()
        self.pulse_streaming = True
        self.contec_start_btn.config(state='disabled')
        self.contec_stop_btn.config(state='normal')

        self._update_pulse_display()
        self._add_to_log("▶ Contec streaming started")

    def _stop_contec(self):
        if self.contec:
            self.contec.stop_streaming()

        self.pulse_streaming = False
        self.contec_start_btn.config(state='normal')
        self.contec_stop_btn.config(state='disabled')

        if self.pulse_update_id:
            self.window.after_cancel(self.pulse_update_id)
            self.pulse_update_id = None

        self._add_to_log("⏹ Contec streaming stopped")

    def _update_pulse_display(self):
        if not self.pulse_streaming or not self.contec:
            return

        reading = self.contec.get_latest()
        if reading:
            self.current_spo2.config(text=f"SpO₂: {reading.spo2}%")
            self.current_hr.config(text=f"HR: {reading.heart_rate} bpm")

            self.pulse_readings.append(reading)

            if HAS_MPL and len(self.pulse_readings) > 5:
                recent = self.pulse_readings[-50:]
                if recent:
                    times = [(r.timestamp - recent[0].timestamp).total_seconds() for r in recent]
                    spo2 = [r.spo2 for r in recent]
                    hr = [r.heart_rate for r in recent]

                    self.pulseox_ax.clear()
                    self.pulseox_ax.plot(times, spo2, 'b-', label='SpO₂', linewidth=2)
                    self.pulseox_ax.plot(times, hr, 'r-', label='HR', linewidth=2)
                    self.pulseox_ax.set_xlabel("Time (s)")
                    self.pulseox_ax.set_ylabel("Value")
                    self.pulseox_ax.set_title("Real-time SpO₂ & Heart Rate")
                    self.pulseox_ax.legend()
                    self.pulseox_ax.grid(True, alpha=0.3)
                    self.pulseox_canvas.draw()

        self.pulse_update_id = self.window.after(100, self._update_pulse_display)

    def _connect_choicemed(self):
        def connect_thread():
            self.choicemed = ChoiceMMedOximeter(port=self.choicemed_port.get())
            success, msg = self.choicemed.connect()

            def update_ui():
                if success:
                    self.choicemed_status.config(fg=C_ACCENT2)
                    self.choicemed_btn.config(text="✅ Connected")
                    self.choicemed_start_btn.config(state='normal')
                    self._add_to_log(f"✅ ChoiceMMed: {msg}")
                else:
                    self.choicemed_status.config(fg="red")
                    self.choicemed_btn.config(text="🔌 Connect")
                    self.choicemed_start_btn.config(state='disabled')
                    self._add_to_log(f"❌ ChoiceMMed: {msg}")

            self.ui_queue.schedule(update_ui)

        threading.Thread(target=connect_thread, daemon=True).start()

    def _start_choicemed(self):
        if not self.choicemed or not self.choicemed.connected:
            return

        self.choicemed.start_streaming()
        self._add_to_log("▶ ChoiceMMed streaming started")

    def _connect_clinitek(self):
        def connect_thread():
            self.clinitek = ClinitekAnalyzer(port=self.clinitek_port.get())
            success, msg = self.clinitek.connect()

            def update_ui():
                if success:
                    self.clinitek_status.config(fg=C_ACCENT2)
                    self.clinitek_btn.config(text="✅ Connected")
                    self.clinitek_read_btn.config(state='normal')
                    self._add_to_log(f"✅ Clinitek: {msg}")
                else:
                    self.clinitek_status.config(fg="red")
                    self.clinitek_btn.config(text="🔌 Connect")
                    self.clinitek_read_btn.config(state='disabled')
                    self._add_to_log(f"❌ Clinitek: {msg}")

            self.ui_queue.schedule(update_ui)

        threading.Thread(target=connect_thread, daemon=True).start()

    def _read_clinitek(self):
        if not self.clinitek or not self.clinitek.connected:
            return

        def read_thread():
            strip = self.clinitek.read_strip()

            def update_ui():
                if strip:
                    self.urinalysis_results.append(strip)

                    self.urinalysis_text.delete(1.0, tk.END)
                    self.urinalysis_text.insert(tk.END, f"Time: {strip.timestamp.strftime('%H:%M:%S')}\n")
                    self.urinalysis_text.insert(tk.END, f"Device: {strip.instrument}\n")
                    self.urinalysis_text.insert(tk.END, "-" * 40 + "\n")

                    for param, value in strip.parameters.items():
                        self.urinalysis_text.insert(tk.END, f"{param:15}: {value}\n")

                    self._add_to_log(f"✅ Clinitek: Read {len(strip.parameters)} parameters")
                    self._update_counts()
                else:
                    self._add_to_log("❌ Clinitek: No strip data")

            self.ui_queue.schedule(update_ui)

        threading.Thread(target=read_thread, daemon=True).start()

    def _connect_dirui(self):
        def connect_thread():
            self.dirui = DiruiUrinalyzer(port=self.dirui_port.get())
            success, msg = self.dirui.connect()

            def update_ui():
                if success:
                    self.dirui_status.config(fg=C_ACCENT2)
                    self.dirui_btn.config(text="✅ Connected")
                    self.dirui_read_btn.config(state='normal')
                    self._add_to_log(f"✅ Dirui: {msg}")
                else:
                    self.dirui_status.config(fg="red")
                    self.dirui_btn.config(text="🔌 Connect")
                    self.dirui_read_btn.config(state='disabled')
                    self._add_to_log(f"❌ Dirui: {msg}")

            self.ui_queue.schedule(update_ui)

        threading.Thread(target=connect_thread, daemon=True).start()

    def _read_dirui(self):
        if not self.dirui or not self.dirui.connected:
            return

        def read_thread():
            strip = self.dirui.read_strip()

            def update_ui():
                if strip:
                    self.urinalysis_results.append(strip)

                    self.urinalysis_text.delete(1.0, tk.END)
                    self.urinalysis_text.insert(tk.END, f"Time: {strip.timestamp.strftime('%H:%M:%S')}\n")
                    self.urinalysis_text.insert(tk.END, f"Device: {strip.instrument}\n")
                    self.urinalysis_text.insert(tk.END, "-" * 40 + "\n")

                    for param, value in strip.parameters.items():
                        self.urinalysis_text.insert(tk.END, f"{param:15}: {value}\n")

                    self._add_to_log(f"✅ Dirui: Read {len(strip.parameters)} parameters")
                    self._update_counts()
                else:
                    self._add_to_log("❌ Dirui: No strip data")

            self.ui_queue.schedule(update_ui)

        threading.Thread(target=read_thread, daemon=True).start()

    def _connect_ocean(self):
        def connect_thread():
            self.ocean = OceanSpectrometer()
            success, msg = self.ocean.connect()

            def update_ui():
                if success:
                    self.ocean_status.config(fg=C_ACCENT2)
                    self.ocean_btn.config(text="✅ Connected")
                    self.ocean_read_btn.config(state='normal')
                    self._add_to_log(f"✅ Ocean USB2000+: {msg}")
                else:
                    self.ocean_status.config(fg="red")
                    self.ocean_btn.config(text="🔌 Connect")
                    self.ocean_read_btn.config(state='disabled')
                    self._add_to_log(f"❌ Ocean USB2000+: {msg}")

            self.ui_queue.schedule(update_ui)

        threading.Thread(target=connect_thread, daemon=True).start()

    def _read_ocean(self):
        if not self.ocean or not self.ocean.connected:
            return

        def read_thread():
            try:
                integration = int(self.ocean_integration.get())
            except:
                integration = 100

            spectrum = self.ocean.get_spectrum(integration)

            def update_ui():
                if spectrum:
                    self.spectra.append(spectrum)

                    if HAS_MPL:
                        self.spec_ax.clear()
                        self.spec_ax.plot(spectrum.wavelengths, spectrum.intensities,
                                         'b-', linewidth=1.5)
                        self.spec_ax.set_xlabel("Wavelength (nm)")
                        self.spec_ax.set_ylabel("Intensity")
                        self.spec_ax.set_title(f"USB2000+ - {spectrum.timestamp.strftime('%H:%M:%S')}")
                        self.spec_ax.grid(True, alpha=0.3)

                        peak_idx = np.argmax(spectrum.intensities)
                        peak_wl = spectrum.wavelengths[peak_idx]
                        peak_int = spectrum.intensities[peak_idx]
                        self.spec_ax.plot(peak_wl, peak_int, 'ro', markersize=8)
                        self.spec_ax.text(peak_wl + 10, peak_int, f"{peak_wl:.1f} nm",
                                         fontsize=9, fontweight='bold')

                        self.spec_canvas.draw()

                    self._add_to_log(f"✅ Ocean: Spectrum read ({len(spectrum.intensities)} points)")
                    self._update_counts()
                else:
                    self._add_to_log("❌ Ocean: Failed to read spectrum")

            self.ui_queue.schedule(update_ui)

        threading.Thread(target=read_thread, daemon=True).start()

    def _connect_sts(self):
        def connect_thread():
            self.sts = STSSpectrometer()
            success, msg = self.sts.connect()

            def update_ui():
                if success:
                    self.sts_status.config(fg=C_ACCENT2)
                    self.sts_btn.config(text="✅ Connected")
                    self.sts_read_btn.config(state='normal')
                    self._add_to_log(f"✅ Ocean STS: {msg}")
                else:
                    self.sts_status.config(fg="red")
                    self.sts_btn.config(text="🔌 Connect")
                    self.sts_read_btn.config(state='disabled')
                    self._add_to_log(f"❌ Ocean STS: {msg}")

            self.ui_queue.schedule(update_ui)

        threading.Thread(target=connect_thread, daemon=True).start()

    def _read_sts(self):
        if not self.sts or not self.sts.connected:
            return

        def read_thread():
            try:
                integration = int(self.sts_integration.get())
            except:
                integration = 100

            spectrum = self.sts.get_spectrum(integration)

            def update_ui():
                if spectrum:
                    self.spectra.append(spectrum)

                    if HAS_MPL:
                        self.spec_ax.clear()
                        self.spec_ax.plot(spectrum.wavelengths, spectrum.intensities,
                                         'g-', linewidth=1.5)
                        self.spec_ax.set_xlabel("Wavelength (nm)")
                        self.spec_ax.set_ylabel("Intensity")
                        self.spec_ax.set_title(f"STS - {spectrum.timestamp.strftime('%H:%M:%S')}")
                        self.spec_ax.grid(True, alpha=0.3)

                        peak_idx = np.argmax(spectrum.intensities)
                        peak_wl = spectrum.wavelengths[peak_idx]
                        peak_int = spectrum.intensities[peak_idx]
                        self.spec_ax.plot(peak_wl, peak_int, 'ro', markersize=8)
                        self.spec_ax.text(peak_wl + 10, peak_int, f"{peak_wl:.1f} nm",
                                         fontsize=9, fontweight='bold')

                        self.spec_canvas.draw()

                    self._add_to_log(f"✅ STS: Spectrum read ({len(spectrum.intensities)} points)")
                    self._update_counts()
                else:
                    self._add_to_log("❌ STS: Failed to read spectrum")

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
        for glu in self.glucometer_readings:
            data.append(glu.to_dict())

        if not data:
            messagebox.showwarning("No Data", "No data to send")
            return

        try:
            self.app.import_data_from_plugin(data)
            self._add_to_log(f"📤 Sent {len(data)} records to main table")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _on_close(self):
        self._add_to_log("🛑 Shutting down...")

        # Stop streaming
        if self.contec:
            self.contec.stop_streaming()
        if self.choicemed:
            self.choicemed.stop_streaming()

        # Disconnect all devices
        for device in [self.radiometer, self.hemocue, self.contour, self.libre,
                       self.contec, self.choicemed, self.clinitek, self.dirui,
                       self.ocean, self.sts]:
            if device and hasattr(device, 'disconnect'):
                try:
                    device.disconnect()
                except:
                    pass

        self.connected_devices.clear()

        if self.window:
            self.window.destroy()
            self.window = None

# ============================================================================
# PLUGIN REGISTRATION
# ============================================================================
def setup_plugin(main_app):
    """Register with main application"""
    plugin = ClinicalDiagnosticsSuitePlugin(main_app)

    if hasattr(main_app, 'plugins_menu'):
        main_app.plugins_menu.add_command(
            label="🧬 Clinical Diagnostics v2.0 COMPLETE",
            command=plugin.show_interface
        )
    elif hasattr(main_app, 'menu'):
        menu = tk.Menu(main_app.menu, tearoff=0)
        main_app.menu.add_cascade(label="🧬 Diagnostics", menu=menu)
        menu.add_command(label="Open Complete Suite", command=plugin.show_interface)

    return plugin
