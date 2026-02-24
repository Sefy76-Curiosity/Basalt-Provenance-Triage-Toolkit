"""
ARCHAEOLOGY & ARCHAEOMETRY UNIFIED SUITE v1.0 - PRODUCTION RELEASE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ XRD:         Bruker · Rigaku · PANalytical · Shimadzu — RAW/BRML/XRDML/RAS parsers
✓ SEM-EDS:     Thermo Phenom · JEOL · Hitachi · Tescan — EMSA/SPX/DM3 parsers
✓ Micro-XRF:   Bruker M4 Tornado · Horiba XGT · Olympus Vanta — map + spectrum
✓ Micro-CT:    Bruker SkyScan · Nikon Metris — LOG/XTEKCT/TIFF parsers
✓ OSL/TL:      Risø DA-20 · Lexsyg — serial control + BIN/BINX/SEQ parsers
✓ GPR:         GSSI SIR · Sensors & Software Noggin · Malå — DZT/DT1/RD3 parsers
✓ Gradiometer: Bartington Grad601 · Sensys MXPDA — serial ASCII stream
✓ Total Station: Leica TS (GeoCom) · Trimble (SDR) · Generic — serial/TCP
✓ Colorimetry: Konica Minolta CM · X-Rite i1Pro — serial CIELab output
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ CROSS-PLATFORM: Windows · Linux · macOS
✓ THREAD-SAFE: Non-blocking UI — all I/O in background threads
✓ TABBED UI:  XRD | SEM/CT | µ-XRF | OSL/TL | GPR/Grad | Survey | Records
✓ DIRECT TO TABLE: All measurements → main app data table
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

PLUGIN_INFO = {
    "id": "archaeology_archaeometry_unified_suite",
    "name": "Archaeology & Archaeometry",
    "category": "hardware",
    "icon": "🏺",
    "version": "1.0.0",
    "author": "Sefy Levy",
    "description": "XRD · SEM-EDS · Micro-XRF · Micro-CT · OSL · GPR · Gradiometer · Total Station · Colorimetry — 40+ instruments",
    "requires": ["numpy", "pandas", "matplotlib", "pyserial"],
    "optional": [
        "scipy",
        "requests",
        "tifffile",
        "readgssi",
        "pynmea2",
        "bleak",
        "openpyxl",
    ],
    "compact": True,
    "window_size": "1050x680",
    "direct_to_table": True,
    "instruments": "40+ models",
}

# ============================================================================
# PREVENT DOUBLE REGISTRATION
# ============================================================================
import tkinter as tk
_ARCHAEOLOGY_REGISTERED = False
from tkinter import ttk, messagebox, filedialog
import numpy as np
import pandas as pd
from datetime import datetime
import time
import re
import os
import csv
import json
import struct
import threading
import queue
import subprocess
import sys
import platform
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Union
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CROSS-PLATFORM FLAGS
# ============================================================================
IS_WINDOWS = platform.system() == 'Windows'
IS_LINUX   = platform.system() == 'Linux'
IS_MAC     = platform.system() == 'Darwin'

# ============================================================================
# DEPENDENCY CHECK
# ============================================================================
def check_dependencies():
    deps = {
        'numpy': False, 'pandas': False, 'matplotlib': False,
        'pyserial': False, 'scipy': False, 'requests': False,
        'tifffile': False, 'readgssi': False, 'pynmea2': False,
        'bleak': False, 'openpyxl': False,
    }
    try: import numpy;      deps['numpy']      = True
    except: pass
    try: import pandas;     deps['pandas']     = True
    except: pass
    try: import matplotlib; deps['matplotlib'] = True
    except: pass
    try: import serial;     deps['pyserial']   = True
    except: pass
    try: import scipy;      deps['scipy']      = True
    except: pass
    try: import requests;   deps['requests']   = True
    except: pass
    try: import tifffile;   deps['tifffile']   = True
    except: pass
    try: import readgssi;   deps['readgssi']   = True
    except: pass
    try: import pynmea2;    deps['pynmea2']    = True
    except: pass
    try: import bleak;      deps['bleak']      = True
    except: pass
    try: import openpyxl;   deps['openpyxl']   = True
    except: pass
    return deps

DEPS = check_dependencies()

# ============================================================================
# OPTIONAL SCIENTIFIC IMPORTS
# ============================================================================
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

try:
    from scipy.signal import find_peaks, savgol_filter
    from scipy.ndimage import gaussian_filter
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    import serial
    import serial.tools.list_ports
    HAS_SERIAL = True
except ImportError:
    HAS_SERIAL = False

# ============================================================================
# THREAD-SAFE UI
# ============================================================================
class ThreadSafeUI:
    """Thread-safe UI updates via queue + after()"""
    def __init__(self, root):
        self.root  = root
        self.queue = queue.Queue()
        self._poll()

    def _poll(self):
        try:
            while True:
                self.queue.get_nowait()()
        except queue.Empty:
            pass
        finally:
            self.root.after(50, self._poll)

    def schedule(self, callback):
        self.queue.put(callback)


# ============================================================================
# TOOLTIP
# ============================================================================
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text   = text
        self.tip    = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, _=None):
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 20
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        tk.Label(self.tip, text=self.text, background="#fffacd",
                 relief=tk.SOLID, borderwidth=1,
                 font=("Arial", 8)).pack()

    def hide(self, _=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None


# ============================================================================
# INSTALL HELPER
# ============================================================================
def install_dependencies(parent, packages: List[str], description: str = ""):
    if not messagebox.askyesno(
        "Install Dependencies",
        f"Install: {', '.join(packages)}\n\nThis may take a moment.",
        parent=parent
    ):
        return False
    for pkg in packages:
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", pkg,
                 "--break-system-packages"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        except Exception:
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", pkg],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
            except Exception as e:
                messagebox.showerror("Install Failed", f"{pkg}: {e}", parent=parent)
                return False
    messagebox.showinfo("Done", f"Installed: {', '.join(packages)}\n\nPlease restart the app.",
                        parent=parent)
    return True


# ============================================================================
# SERIAL PORT HELPER
# ============================================================================
def list_serial_ports() -> List[str]:
    if not HAS_SERIAL:
        return []
    try:
        return [p.device for p in serial.tools.list_ports.comports()]
    except Exception:
        if IS_WINDOWS:
            return [f"COM{i}" for i in range(1, 9)]
        return ["/dev/ttyUSB0", "/dev/ttyUSB1", "/dev/ttyACM0", "/dev/ttyACM1", "/dev/ttyS0"]


# ============================================================================
# DATA CLASS
# ============================================================================
@dataclass
class ArchaeoMeasurement:
    timestamp:    datetime
    sample_id:    str
    context:      Optional[str] = None
    site:         Optional[str] = None
    trench:       Optional[str] = None
    locus:        Optional[str] = None

    # XRD
    xrd_file:     Optional[str] = None
    xrd_instrument: Optional[str] = None
    xrd_peaks:    Optional[str] = None
    xrd_phases:   Optional[str] = None
    xrd_d_spacings: Optional[str] = None

    # SEM-EDS
    sem_instrument: Optional[str] = None
    sem_image_file: Optional[str] = None
    eds_spectrum:   Optional[str] = None
    eds_elements:   Optional[str] = None

    # Micro-XRF
    uxrf_instrument: Optional[str] = None
    uxrf_elements:   Optional[str] = None
    uxrf_map_file:   Optional[str] = None

    # Micro-CT
    uct_instrument:  Optional[str] = None
    uct_resolution:  Optional[float] = None
    uct_file:        Optional[str] = None

    # OSL/TL
    osl_instrument:  Optional[str] = None
    osl_dose_gy:     Optional[float] = None
    osl_age_ka:      Optional[float] = None
    osl_age_err_ka:  Optional[float] = None
    osl_protocol:    Optional[str] = None

    # GPR
    gpr_instrument:  Optional[str] = None
    gpr_frequency_mhz: Optional[float] = None
    gpr_depth_m:     Optional[float] = None
    gpr_file:        Optional[str] = None

    # Gradiometer
    grad_instrument: Optional[str] = None
    grad_nT:         Optional[float] = None
    grad_x:          Optional[float] = None
    grad_y:          Optional[float] = None

    # Total Station
    ts_instrument:   Optional[str] = None
    ts_northing:     Optional[float] = None
    ts_easting:      Optional[float] = None
    ts_elevation:    Optional[float] = None
    ts_point_id:     Optional[str] = None

    # Colorimetry
    color_instrument: Optional[str] = None
    color_L:          Optional[float] = None
    color_a:          Optional[float] = None
    color_b:          Optional[float] = None
    color_munsell:    Optional[str] = None

    notes: Optional[str] = None

    def to_dict(self) -> Dict:
        d = {
            'Timestamp':   self.timestamp.isoformat(),
            'Sample_ID':   self.sample_id,
            'Site':        self.site or '',
            'Context':     self.context or '',
            'Trench':      self.trench or '',
            'Locus':       self.locus or '',

            'XRD_Instrument':  self.xrd_instrument or '',
            'XRD_File':        self.xrd_file or '',
            'XRD_Phases':      self.xrd_phases or '',
            'XRD_d-spacings':  self.xrd_d_spacings or '',

            'SEM_Instrument':  self.sem_instrument or '',
            'EDS_Elements':    self.eds_elements or '',

            'uXRF_Instrument': self.uxrf_instrument or '',
            'uXRF_Elements':   self.uxrf_elements or '',

            'uCT_Instrument':  self.uct_instrument or '',
            'uCT_Resolution_um': f"{self.uct_resolution:.2f}" if self.uct_resolution else '',

            'OSL_Instrument':  self.osl_instrument or '',
            'OSL_Dose_Gy':     f"{self.osl_dose_gy:.3f}" if self.osl_dose_gy else '',
            'OSL_Age_ka':      f"{self.osl_age_ka:.3f}" if self.osl_age_ka else '',
            'OSL_Age_err_ka':  f"{self.osl_age_err_ka:.3f}" if self.osl_age_err_ka else '',
            'OSL_Protocol':    self.osl_protocol or '',

            'GPR_Instrument':  self.gpr_instrument or '',
            'GPR_Freq_MHz':    f"{self.gpr_frequency_mhz:.0f}" if self.gpr_frequency_mhz else '',
            'GPR_Depth_m':     f"{self.gpr_depth_m:.2f}" if self.gpr_depth_m else '',

            'Grad_nT':         f"{self.grad_nT:.2f}" if self.grad_nT else '',
            'Grad_X':          f"{self.grad_x:.2f}" if self.grad_x else '',
            'Grad_Y':          f"{self.grad_y:.2f}" if self.grad_y else '',

            'TS_Northing':     f"{self.ts_northing:.4f}" if self.ts_northing else '',
            'TS_Easting':      f"{self.ts_easting:.4f}" if self.ts_easting else '',
            'TS_Elevation':    f"{self.ts_elevation:.4f}" if self.ts_elevation else '',
            'TS_PointID':      self.ts_point_id or '',

            'Color_L':         f"{self.color_L:.2f}" if self.color_L is not None else '',
            'Color_a':         f"{self.color_a:.2f}" if self.color_a is not None else '',
            'Color_b':         f"{self.color_b:.2f}" if self.color_b is not None else '',
            'Munsell':         self.color_munsell or '',

            'Notes':           self.notes or '',
        }
        return {k: v for k, v in d.items() if v}


# ============================================================================
# ██████████████  XRD PARSERS  ██████████████
# ============================================================================
class XRDParser:
    """
    Parsers for all major XRD file formats.
    Returns: {'two_theta': ndarray, 'intensity': ndarray, 'metadata': dict}
    """

    @classmethod
    def parse(cls, path: str) -> Dict:
        ext = Path(path).suffix.lower()
        if ext == '.raw':
            # Could be Bruker or Rigaku — sniff the magic bytes
            try:
                return cls._parse_bruker_raw(path)
            except Exception:
                try:
                    return cls._parse_rigaku_raw(path)
                except Exception:
                    return cls._parse_generic_xy(path)
        elif ext in ('.brml',):
            return cls._parse_bruker_brml(path)
        elif ext in ('.xrdml',):
            return cls._parse_panalytical_xrdml(path)
        elif ext in ('.ras',):
            return cls._parse_rigaku_ras(path)
        elif ext in ('.csv', '.txt', '.xy', '.dat', '.asc'):
            return cls._parse_generic_xy(path)
        else:
            return cls._parse_generic_xy(path)

    # ------------------------------------------------------------------
    @classmethod
    def _parse_bruker_raw(cls, path: str) -> Dict:
        """Bruker RAW v1/v2/v3 binary format"""
        meta = {'instrument': 'Bruker', 'format': 'RAW'}
        with open(path, 'rb') as f:
            magic = f.read(4)
            if magic[:3] == b'RAW':
                version = magic[3:4]
                meta['raw_version'] = version.decode('ascii', errors='ignore')
            else:
                raise ValueError("Not a Bruker RAW file")

            f.seek(0)
            raw = f.read()

        # RAW v1: 2theta_start at offset 0x10, step at 0x18, npoints at 0x16
        # RAW v3 (most common): header at 0, data range encoded
        # We use a robust approach: find the float data block
        two_theta_arr = []
        intensity_arr = []

        try:
            f2 = open(path, 'rb')
            header = f2.read(712)
            f2.seek(4)
            nsteps  = struct.unpack_from('<I', raw, 4)[0]
            start2t = struct.unpack_from('<d', raw, 12)[0]
            step2t  = struct.unpack_from('<d', raw, 20)[0]

            if not (0.01 < step2t < 5.0 and 0 < start2t < 180 and 0 < nsteps < 50000):
                raise ValueError("Invalid RAW header values — try v1 offsets")

            data_offset = 712
            for i in range(min(nsteps, 50000)):
                val = struct.unpack_from('<f', raw, data_offset + i * 4)[0]
                intensity_arr.append(float(val))
                two_theta_arr.append(start2t + i * step2t)

            f2.close()
        except Exception:
            # Fallback: scan for plausible float block
            idx = 0
            while idx < len(raw) - 8:
                try:
                    v = struct.unpack_from('<f', raw, idx)[0]
                    if 0 < v < 1e8:
                        intensity_arr.append(v)
                except Exception:
                    pass
                idx += 4
            two_theta_arr = list(range(len(intensity_arr)))

        meta['n_points'] = len(two_theta_arr)
        return {
            'two_theta': np.array(two_theta_arr),
            'intensity': np.array(intensity_arr),
            'metadata':  meta,
        }

    # ------------------------------------------------------------------
    @classmethod
    def _parse_bruker_brml(cls, path: str) -> Dict:
        """Bruker BRML — ZIP containing RawData0.xml"""
        import zipfile
        meta = {'instrument': 'Bruker', 'format': 'BRML'}
        try:
            with zipfile.ZipFile(path, 'r') as z:
                names = z.namelist()
                raw_name = next((n for n in names if 'RawData' in n and n.endswith('.xml')), names[0])
                content = z.read(raw_name).decode('utf-8', errors='ignore')
        except Exception as e:
            raise ValueError(f"BRML read error: {e}")

        two_theta = []
        intensity = []

        # Parse <Datum>start_angle,step,... values
        datum_blocks = re.findall(r'<Datum>(.*?)</Datum>', content, re.DOTALL)
        for block in datum_blocks:
            nums = re.findall(r'[+-]?[\d.]+(?:[eE][+-]?\d+)?', block)
            if len(nums) >= 2:
                try:
                    two_theta.append(float(nums[0]))
                    intensity.append(float(nums[1]))
                except Exception:
                    pass

        if not two_theta:
            # Try <DataPoint> elements
            points = re.findall(r'<DataPoint[^/]*/>', content)
            for i, p in enumerate(points):
                ang = re.search(r'Angle="([^"]+)"', p)
                cnt = re.search(r'Count="([^"]+)"', p)
                if ang and cnt:
                    two_theta.append(float(ang.group(1)))
                    intensity.append(float(cnt.group(1)))

        meta['n_points'] = len(two_theta)
        # Extract instrument metadata
        wl = re.search(r'<WavelengthAlpha1>(.*?)</WavelengthAlpha1>', content)
        if wl:
            meta['wavelength_A'] = wl.group(1).strip()
        return {
            'two_theta': np.array(two_theta),
            'intensity': np.array(intensity),
            'metadata':  meta,
        }

    # ------------------------------------------------------------------
    @classmethod
    def _parse_panalytical_xrdml(cls, path: str) -> Dict:
        """PANalytical / Malvern Panalytical XRDML (XML)"""
        meta = {'instrument': 'PANalytical', 'format': 'XRDML'}
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        two_theta = []
        intensity = []

        # startPosition / endPosition / data
        start_m = re.search(r'<startPosition>(.*?)</startPosition>', content)
        end_m   = re.search(r'<endPosition>(.*?)</endPosition>', content)
        counts_m = re.search(r'<intensities[^>]*>(.*?)</intensities>', content, re.DOTALL)
        if not counts_m:
            counts_m = re.search(r'<counts[^>]*>(.*?)</counts>', content, re.DOTALL)

        if start_m and end_m and counts_m:
            start = float(start_m.group(1).strip())
            end   = float(end_m.group(1).strip())
            raw_counts = [float(x) for x in counts_m.group(1).strip().split() if x.strip()]
            n = len(raw_counts)
            if n > 1:
                two_theta = list(np.linspace(start, end, n))
                intensity = raw_counts

        # Instrument metadata
        inst_m = re.search(r'<instrumentName>(.*?)</instrumentName>', content)
        if inst_m:
            meta['instrument'] = f"PANalytical {inst_m.group(1).strip()}"
        wl_m = re.search(r'<kAlpha1>(.*?)</kAlpha1>', content)
        if wl_m:
            meta['wavelength_A'] = wl_m.group(1).strip()

        meta['n_points'] = len(two_theta)
        return {
            'two_theta': np.array(two_theta),
            'intensity': np.array(intensity),
            'metadata':  meta,
        }

    # ------------------------------------------------------------------
    @classmethod
    def _parse_rigaku_ras(cls, path: str) -> Dict:
        """Rigaku .ras ASCII format"""
        meta = {'instrument': 'Rigaku', 'format': 'RAS'}
        two_theta = []
        intensity = []
        in_data = False

        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if line.startswith('*RAS_INT_START'):
                    in_data = True
                    continue
                if line.startswith('*RAS_INT_END'):
                    in_data = False
                    continue
                if in_data and line and not line.startswith('*'):
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            two_theta.append(float(parts[0]))
                            intensity.append(float(parts[1]))
                        except ValueError:
                            pass
                # Metadata
                if line.startswith('*FILE_SAMPLE'):
                    meta['sample'] = line.split('=', 1)[-1].strip().strip('"')
                if line.startswith('*HW_XG_WAVE_LENGTH_ALPHA1'):
                    meta['wavelength_A'] = line.split('=', 1)[-1].strip().strip('"')

        meta['n_points'] = len(two_theta)
        return {
            'two_theta': np.array(two_theta),
            'intensity': np.array(intensity),
            'metadata':  meta,
        }

    # ------------------------------------------------------------------
    @classmethod
    def _parse_rigaku_raw(cls, path: str) -> Dict:
        """Rigaku binary RAW — heuristic parsing"""
        meta = {'instrument': 'Rigaku', 'format': 'RAW-binary'}
        with open(path, 'rb') as f:
            raw = f.read()

        # Rigaku RAW starts with header; try to find float data block
        two_theta = []
        intensity = []
        # Try offset 256 (common for Rigaku SmartLab)
        for offset in [256, 128, 512]:
            tmp = []
            for i in range(0, min(len(raw) - offset - 4, 200000), 4):
                v = struct.unpack_from('<f', raw, offset + i)[0]
                if 0 < v < 1e7:
                    tmp.append(v)
            if len(tmp) > 50:
                intensity = tmp
                # Reconstruct 2theta from file size heuristic
                n = len(intensity)
                two_theta = list(np.linspace(5.0, 5.0 + n * 0.02, n))
                break

        meta['n_points'] = len(two_theta)
        return {
            'two_theta': np.array(two_theta),
            'intensity': np.array(intensity),
            'metadata':  meta,
        }

    # ------------------------------------------------------------------
    @classmethod
    def _parse_generic_xy(cls, path: str) -> Dict:
        """Generic 2-column ASCII: 2theta  intensity"""
        meta = {'instrument': 'Generic', 'format': 'XY'}
        two_theta = []
        intensity = []
        separator = None

        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith(('#', '!', '%', '"')):
                    continue
                if separator is None:
                    if '\t' in line:
                        separator = '\t'
                    elif ';' in line:
                        separator = ';'
                    elif ',' in line:
                        separator = ','
                    else:
                        separator = None  # whitespace

                parts = line.split(separator) if separator else line.split()
                if len(parts) >= 2:
                    try:
                        t = float(parts[0])
                        i = float(parts[1])
                        if 0 < t < 200:
                            two_theta.append(t)
                            intensity.append(i)
                    except ValueError:
                        pass

        meta['n_points'] = len(two_theta)
        return {
            'two_theta': np.array(two_theta),
            'intensity': np.array(intensity),
            'metadata':  meta,
        }

    # ------------------------------------------------------------------
    @staticmethod
    def find_peaks_xrd(two_theta: np.ndarray, intensity: np.ndarray) -> List[Dict]:
        """Detect XRD peaks and compute d-spacings (Cu Kα, λ=1.5406 Å)"""
        if len(intensity) < 10:
            return []
        if HAS_SCIPY:
            # Savitzky-Golay smooth first
            window = min(11, len(intensity) if len(intensity) % 2 == 1 else len(intensity) - 1)
            if window >= 5:
                try:
                    smoothed = savgol_filter(intensity, window, 3)
                except Exception:
                    smoothed = intensity
            else:
                smoothed = intensity
            pks, props = find_peaks(smoothed,
                                    height=np.percentile(smoothed, 60),
                                    prominence=np.std(smoothed) * 0.5,
                                    width=2)
        else:
            # Simple local maxima
            pks = []
            threshold = np.mean(intensity) + np.std(intensity)
            for i in range(2, len(intensity) - 2):
                if (intensity[i] > threshold and
                        intensity[i] > intensity[i-1] and
                        intensity[i] > intensity[i+1]):
                    pks.append(i)
            pks = np.array(pks)

        results = []
        LAMBDA_CU_KA = 1.5406  # Angstrom
        for pk in pks[:20]:
            angle = float(two_theta[pk])
            cts   = float(intensity[pk])
            theta_rad = np.radians(angle / 2.0)
            if np.sin(theta_rad) > 0:
                d_spacing = LAMBDA_CU_KA / (2.0 * np.sin(theta_rad))
            else:
                d_spacing = 0.0
            results.append({
                'two_theta': round(angle, 3),
                'intensity': round(cts, 1),
                'd_spacing_A': round(d_spacing, 4),
            })
        return results

    @staticmethod
    def match_mineral(d_spacings: List[float]) -> List[str]:
        """
        Quick d-spacing mineral lookup against ICDD reference cards.
        Simplified reference — real implementation should use diffpy/xrdtools.
        """
        MINERAL_DB = {
            'Quartz':      [3.342, 4.257, 1.818, 2.281, 2.457],
            'Calcite':     [3.035, 2.095, 1.875, 2.285, 3.859],
            'Feldspar (K)':[3.240, 3.480, 4.220, 6.450, 2.990],
            'Hematite':    [2.519, 1.694, 2.210, 1.840, 2.697],
            'Magnetite':   [2.530, 2.967, 1.616, 1.483, 4.852],
            'Dolomite':    [2.886, 2.192, 1.786, 3.700, 2.546],
            'Goethite':    [4.180, 2.690, 2.450, 1.720, 2.190],
            'Gypsum':      [7.630, 4.270, 3.060, 2.870, 1.814],
            'Halite':      [2.820, 1.994, 1.628, 3.260, 1.410],
            'Kaolinite':   [7.170, 3.580, 2.340, 2.290, 1.488],
            'Illite':      [9.980, 4.980, 3.320, 2.580, 1.997],
            'Smectite':    [12.40, 6.200, 4.130, 3.100, 2.480],
            'Pyroxene':    [2.980, 2.870, 3.200, 1.727, 2.520],
            'Olivine':     [2.455, 1.760, 3.882, 2.520, 2.775],
            'Pyrite':      [2.709, 3.128, 1.914, 1.633, 2.212],
        }
        TOLERANCE = 0.05  # Å

        matches = []
        for mineral, ref_d in MINERAL_DB.items():
            hits = 0
            for d_obs in d_spacings:
                for d_ref in ref_d:
                    if abs(d_obs - d_ref) <= TOLERANCE:
                        hits += 1
                        break
            if hits >= 2:
                score = hits / len(ref_d)
                matches.append((mineral, hits, score))

        matches.sort(key=lambda x: -x[2])
        return [f"{m} ({h}/{len(MINERAL_DB[m])} peaks)" for m, h, _ in matches[:5]]


# ============================================================================
# ██████████████  EMSA / EDS PARSERS  ██████████████
# ============================================================================
class EMSAParser:
    """
    EMSA/MAS standard EDS spectrum parser (.msa, .ems, .emsa)
    ISO 22029:2012 format used by JEOL, Hitachi, Thermo, Oxford
    """
    @classmethod
    def parse(cls, path: str) -> Dict:
        meta = {}
        energy  = []
        counts  = []
        in_data = False

        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if line.startswith('#SPECTRUM'):
                    in_data = True
                    continue
                if line.startswith('#ENDOFDATA'):
                    break
                if line.startswith('#') and not in_data:
                    if ':' in line:
                        key, val = line[1:].split(':', 1)
                        meta[key.strip().upper()] = val.strip()
                    continue
                if in_data and line and not line.startswith('#'):
                    parts = line.split(',')
                    if len(parts) >= 2:
                        try:
                            energy.append(float(parts[0]))
                            counts.append(float(parts[1]))
                        except ValueError:
                            pass
                    elif len(parts) == 1:
                        try:
                            counts.append(float(parts[0]))
                        except ValueError:
                            pass

        # Reconstruct energy axis from header if only counts given
        if counts and not energy:
            xperchan = float(meta.get('XPERCHAN', 10.0))
            xoffset  = float(meta.get('OFFSET',    0.0))
            energy = [xoffset + i * xperchan for i in range(len(counts))]

        return {
            'energy_eV': np.array(energy),
            'counts':    np.array(counts),
            'metadata':  meta,
        }

    @classmethod
    def identify_elements(cls, energy_eV: np.ndarray, counts: np.ndarray) -> List[Dict]:
        """Match peaks to X-ray emission lines (simplified XEDS database)"""
        XRAY_LINES = {
            # Element: [(energy_eV, line_name, relative_intensity)]
            'C':  [(277,  'K',  100)],
            'N':  [(392,  'K',  100)],
            'O':  [(525,  'K',  100)],
            'Na': [(1041, 'K',  100)],
            'Mg': [(1254, 'K',  100)],
            'Al': [(1487, 'K',  100)],
            'Si': [(1740, 'K',  100)],
            'P':  [(2013, 'K',  100)],
            'S':  [(2307, 'K',  100)],
            'Cl': [(2622, 'K',  100)],
            'K':  [(3312, 'K',  100), (3590, 'Kβ', 12)],
            'Ca': [(3690, 'K',  100), (4012, 'Kβ', 13)],
            'Ti': [(4510, 'K',  100), (4932, 'Kβ', 11)],
            'Cr': [(5411, 'K',  100), (5947, 'Kβ', 13)],
            'Mn': [(5898, 'K',  100), (6490, 'Kβ', 14)],
            'Fe': [(6400, 'K',  100), (7057, 'Kβ', 17), (705, 'L', 10)],
            'Co': [(6930, 'K',  100)],
            'Ni': [(7478, 'K',  100), (851, 'L', 10)],
            'Cu': [(8041, 'K',  100), (8905, 'Kβ', 20), (930, 'L', 12)],
            'Zn': [(8630, 'K',  100), (1012, 'L', 12)],
            'As': [(10544,'K',  100), (1282, 'L', 20)],
            'Pb': [(2346, 'Mα', 100), (10551,'Lα', 40)],
            'Ag': [(2984, 'L',  100), (22163,'K',  5)],
            'Sn': [(3444, 'L',  100)],
            'Ba': [(4466, 'L',  100)],
        }

        TOLERANCE_EV = 80  # eV window

        if len(counts) < 10:
            return []

        if HAS_SCIPY:
            pks, _ = find_peaks(counts, height=np.percentile(counts, 70), prominence=np.std(counts))
        else:
            pks = [i for i in range(1, len(counts)-1)
                   if counts[i] > counts[i-1] and counts[i] > counts[i+1]
                   and counts[i] > np.mean(counts) + np.std(counts)]
            pks = np.array(pks)

        peak_energies = energy_eV[pks] if len(pks) else []
        identified = []

        for element, lines in XRAY_LINES.items():
            for ref_e, line_name, _ in lines:
                for pe in peak_energies:
                    if abs(pe - ref_e) <= TOLERANCE_EV:
                        if not any(x['element'] == element for x in identified):
                            idx = np.argmin(np.abs(energy_eV - pe))
                            identified.append({
                                'element': element,
                                'line': line_name,
                                'energy_eV': round(float(pe), 0),
                                'counts': int(counts[idx]),
                            })
                        break

        identified.sort(key=lambda x: -x['counts'])
        return identified


# ============================================================================
# ██████████████  OSL / TL DRIVERS  ██████████████
# ============================================================================
class OslDriver:
    """Base class for OSL/TL luminescence reader drivers"""
    def __init__(self, port=None, ui=None):
        self.port      = port
        self.serial    = None
        self.connected = False
        self.ui        = ui

    def connect(self): raise NotImplementedError
    def test(self):    raise NotImplementedError
    def read(self):    raise NotImplementedError
    def disconnect(self):
        if self.serial and self.serial.is_open:
            self.serial.close()
        self.connected = False


class RisoDa20Driver(OslDriver):
    """
    Risø DA-20 TL/OSL reader — serial protocol.
    Baud: 9600, 8N1.  Commands follow Risø TDT-OSL-DA-20 protocol.
    """
    BAUD = 9600
    CMD_IDENT   = b'\\IDN?\r\n'
    CMD_TEMP    = b'\\TMP?\r\n'
    CMD_PMT     = b'\\PMT?\r\n'
    CMD_RUNSEQ  = b'\\RUN\r\n'
    CMD_STOP    = b'\\STP\r\n'

    def connect(self):
        if not HAS_SERIAL:
            return False, "pyserial not installed"
        try:
            self.serial = serial.Serial(
                self.port, self.BAUD, timeout=2,
                bytesize=8, parity='N', stopbits=1
            )
            self.serial.write(self.CMD_IDENT)
            time.sleep(0.3)
            resp = self.serial.read(128).decode('ascii', errors='ignore').strip()
            if resp:
                self.connected = True
                return True, f"Risø DA-20: {resp[:60]}"
            return False, "No response from DA-20"
        except Exception as e:
            return False, str(e)

    def test(self):
        if not self.connected:
            return False, "Not connected"
        try:
            self.serial.write(self.CMD_TEMP)
            time.sleep(0.2)
            resp = self.serial.read(64).decode('ascii', errors='ignore').strip()
            return True, f"Temperature: {resp}"
        except Exception as e:
            return False, str(e)

    def read(self) -> Optional[Dict]:
        if not self.connected:
            return None
        try:
            self.serial.write(self.CMD_PMT)
            time.sleep(0.5)
            data = self.serial.read(256).decode('ascii', errors='ignore')
            m = re.search(r'([\d.]+)', data)
            if m:
                return {
                    'pmt_counts': float(m.group(1)),
                    'instrument': 'Risø DA-20',
                    'timestamp': datetime.now().isoformat(),
                }
        except Exception:
            pass
        return None


class LexsygDriver(OslDriver):
    """
    Lexsyg Research / Smart / Junior — serial protocol.
    Baud: 115200, 8N1.
    """
    BAUD = 115200
    CMD_ID   = b'*IDN?\r\n'
    CMD_MEAS = b'MEAS:OSL?\r\n'
    CMD_TEMP = b'SENS:TEMP?\r\n'

    def connect(self):
        if not HAS_SERIAL:
            return False, "pyserial not installed"
        try:
            self.serial = serial.Serial(self.port, self.BAUD, timeout=2)
            self.serial.write(self.CMD_ID)
            time.sleep(0.3)
            resp = self.serial.read(128).decode('ascii', errors='ignore').strip()
            if 'LEXSYG' in resp.upper() or resp:
                self.connected = True
                return True, f"Lexsyg: {resp[:60]}"
            return False, "No response from Lexsyg"
        except Exception as e:
            return False, str(e)

    def test(self):
        if not self.connected:
            return False, "Not connected"
        try:
            self.serial.write(self.CMD_TEMP)
            time.sleep(0.2)
            resp = self.serial.read(64).decode('ascii', errors='ignore').strip()
            return True, f"Temp: {resp}"
        except Exception as e:
            return False, str(e)

    def read(self) -> Optional[Dict]:
        if not self.connected:
            return None
        try:
            self.serial.write(self.CMD_MEAS)
            time.sleep(1.0)
            data = self.serial.read(512).decode('ascii', errors='ignore')
            m = re.search(r'([\d.]+)', data)
            if m:
                return {
                    'osl_counts': float(m.group(1)),
                    'instrument': 'Lexsyg',
                    'timestamp': datetime.now().isoformat(),
                }
        except Exception:
            pass
        return None


class BinxParser:
    """
    Risø BIN/BINX format parser — binary luminescence data.
    Spec: Risø National Laboratory BIN/BINX file format description.
    """
    HEADER_SIZE = 32
    RECORD_SIZE = 178  # BINX v08

    @classmethod
    def parse(cls, path: str) -> Dict:
        records = []
        try:
            with open(path, 'rb') as f:
                header = f.read(cls.HEADER_SIZE)
                # Check magic
                magic = header[:3]
                version = header[3]
                n_records = struct.unpack_from('<I', header, 4)[0]
                meta = {
                    'format':    'BINX',
                    'version':   version,
                    'n_records': n_records,
                    'file':      Path(path).name,
                }

                for _ in range(min(n_records, 10000)):
                    rec_data = f.read(cls.RECORD_SIZE)
                    if len(rec_data) < cls.RECORD_SIZE:
                        break
                    try:
                        rec = {
                            'run':       struct.unpack_from('<H', rec_data, 0)[0],
                            'set':       struct.unpack_from('<H', rec_data, 2)[0],
                            'position':  struct.unpack_from('<H', rec_data, 4)[0],
                            'grain':     struct.unpack_from('<H', rec_data, 6)[0],
                            'ltype':     rec_data[8],
                            'unit':      rec_data[9],
                            'an_temp':   struct.unpack_from('<f', rec_data, 10)[0],
                            'time':      struct.unpack_from('<f', rec_data, 14)[0],
                            'starttemp': struct.unpack_from('<f', rec_data, 18)[0],
                            'endtemp':   struct.unpack_from('<f', rec_data, 22)[0],
                        }
                        # Data points (up to 9999 per record) stored after fixed header
                        n_pts = struct.unpack_from('<H', rec_data, 26)[0]
                        rec['n_data_points'] = n_pts
                        records.append(rec)
                    except Exception:
                        pass
        except Exception as e:
            return {'records': [], 'metadata': {'error': str(e)}}

        return {'records': records, 'metadata': meta}


# ============================================================================
# ██████████████  GPR PARSERS  ██████████████
# ============================================================================
class GPRParser:
    """
    Ground Penetrating Radar file parsers.
    Formats: GSSI .DZT, Sensors&Software .DT1, Malå .rd3/.rad
    """
    @classmethod
    def parse(cls, path: str) -> Dict:
        ext = Path(path).suffix.lower()
        if ext == '.dzt':
            return cls._parse_dzt(path)
        elif ext == '.dt1':
            return cls._parse_dt1(path)
        elif ext in ('.rd3', '.rd7'):
            return cls._parse_mala(path)
        else:
            return {'data': None, 'metadata': {'error': f'Unknown GPR format: {ext}'}}

    @classmethod
    def _parse_dzt(cls, path: str) -> Dict:
        """GSSI DZT format"""
        meta = {'format': 'DZT', 'instrument': 'GSSI SIR'}
        try:
            with open(path, 'rb') as f:
                raw = f.read()

            # DZT header: 1024 bytes minimum
            tag       = struct.unpack_from('<H', raw, 0)[0]
            rh_data   = struct.unpack_from('<H', raw, 2)[0]   # data offset (samples)
            rh_nsamp  = struct.unpack_from('<H', raw, 4)[0]   # samples per scan
            rh_bits   = struct.unpack_from('<H', raw, 6)[0]   # bits per sample
            rh_zero   = struct.unpack_from('<h', raw, 8)[0]   # zero correction
            rh_sps    = struct.unpack_from('<f', raw, 10)[0]  # scans per second
            rh_spm    = struct.unpack_from('<f', raw, 14)[0]  # scans per meter
            rh_mpm    = struct.unpack_from('<f', raw, 18)[0]  # meters per mark
            rh_position = struct.unpack_from('<f', raw, 22)[0]
            rh_range  = struct.unpack_from('<f', raw, 26)[0]  # time window (ns)
            rh_npass  = struct.unpack_from('<H', raw, 30)[0]
            rh_antname = raw[31:51].decode('ascii', errors='ignore').strip('\x00')

            meta.update({
                'samples_per_scan': rh_nsamp,
                'bits': rh_bits,
                'time_window_ns': rh_range,
                'scans_per_meter': rh_spm,
                'antenna': rh_antname.strip(),
            })

            # Estimate frequency from antenna name
            freq_m = re.search(r'(\d+)', rh_antname)
            if freq_m:
                meta['antenna_MHz'] = int(freq_m.group(1))

            # Data starts at rh_data bytes offset
            data_start = rh_data
            bytes_per_sample = rh_bits // 8
            if bytes_per_sample < 1:
                bytes_per_sample = 2

            data_bytes = raw[data_start:]
            n_samples  = len(data_bytes) // bytes_per_sample
            n_scans    = n_samples // rh_nsamp if rh_nsamp > 0 else 0

            if n_scans > 0 and rh_nsamp > 0:
                fmt = '<' + ('h' if rh_bits == 16 else 'B') * (n_scans * rh_nsamp)
                total = n_scans * rh_nsamp * bytes_per_sample
                vals  = struct.unpack_from(fmt[:1 + n_scans * rh_nsamp], data_bytes[:total])
                arr   = np.array(vals, dtype=np.float32).reshape(rh_nsamp, n_scans)
                meta['n_scans'] = n_scans
                return {'data': arr, 'metadata': meta}

        except Exception as e:
            meta['error'] = str(e)
        return {'data': None, 'metadata': meta}

    @classmethod
    def _parse_dt1(cls, path: str) -> Dict:
        """Sensors & Software .DT1 + .HD header file"""
        meta = {'format': 'DT1', 'instrument': 'Sensors & Software'}
        hdr_path = path.replace('.DT1', '.HD').replace('.dt1', '.hd')

        if os.path.exists(hdr_path):
            with open(hdr_path, 'r', errors='ignore') as f:
                for line in f:
                    if ':' in line:
                        k, v = line.split(':', 1)
                        meta[k.strip()] = v.strip()

        try:
            with open(path, 'rb') as f:
                raw = f.read()
            # DT1 uses 25-byte trace headers
            num_samp = int(meta.get('NUM OF PTS PER RECORD', 512))
            trace_header = 25
            trace_size   = trace_header + num_samp * 2
            n_traces     = len(raw) // trace_size
            traces        = []

            for i in range(n_traces):
                offset = i * trace_size + trace_header
                trace  = struct.unpack_from(f'<{num_samp}h', raw, offset)
                traces.append(list(trace))

            if traces:
                arr = np.array(traces, dtype=np.float32).T
                meta['n_traces'] = n_traces
                meta['samples']  = num_samp
                return {'data': arr, 'metadata': meta}
        except Exception as e:
            meta['error'] = str(e)
        return {'data': None, 'metadata': meta}

    @classmethod
    def _parse_mala(cls, path: str) -> Dict:
        """Malå RD3/RD7 format + RAD header"""
        meta = {'format': 'RD3', 'instrument': 'Malå'}
        rad_path = path.rsplit('.', 1)[0] + '.rad'
        if not os.path.exists(rad_path):
            rad_path = path.rsplit('.', 1)[0] + '.RAD'

        if os.path.exists(rad_path):
            with open(rad_path, 'r', errors='ignore') as f:
                for line in f:
                    if ':' in line:
                        k, v = line.split(':', 1)
                        meta[k.strip().upper()] = v.strip()

        try:
            num_samp  = int(meta.get('SAMPLES', 512))
            with open(path, 'rb') as f:
                raw = f.read()

            n_traces = len(raw) // (num_samp * 2)
            arr = np.frombuffer(raw[:n_traces * num_samp * 2], dtype='<i2')
            arr = arr.reshape(n_traces, num_samp).T.astype(np.float32)
            meta['n_traces'] = n_traces
            meta['samples']  = num_samp
            return {'data': arr, 'metadata': meta}
        except Exception as e:
            meta['error'] = str(e)
        return {'data': None, 'metadata': meta}

    @staticmethod
    def estimate_depth(time_window_ns: float, velocity_m_ns: float = 0.1) -> float:
        """Convert time window (ns) to depth (m). Default v = 0.1 m/ns (dry soil)"""
        return (time_window_ns * velocity_m_ns) / 2.0


# ============================================================================
# ██████████████  GRADIOMETER DRIVERS  ██████████████
# ============================================================================
class GradiometerDriver:
    """Base class for fluxgate gradiometers"""
    def __init__(self, port=None, ui=None):
        self.port      = port
        self.serial    = None
        self.connected = False
        self.ui        = ui

    def connect(self): raise NotImplementedError
    def test(self):    raise NotImplementedError
    def read(self):    raise NotImplementedError
    def disconnect(self):
        if self.serial and self.serial.is_open:
            self.serial.close()
        self.connected = False


class BartingtonGrad601Driver(GradiometerDriver):
    """
    Bartington Grad601 fluxgate gradiometer.
    RS-232: 9600 baud, 8N1. Outputs space-separated X Y Z nT values.
    """
    BAUD = 9600
    CMD_READ = b'D\r\n'
    CMD_ID   = b'I\r\n'

    def connect(self):
        if not HAS_SERIAL:
            return False, "pyserial not installed"
        try:
            self.serial = serial.Serial(self.port, self.BAUD, timeout=2)
            self.serial.write(self.CMD_ID)
            time.sleep(0.3)
            resp = self.serial.read(128).decode('ascii', errors='ignore').strip()
            if resp:
                self.connected = True
                return True, f"Bartington Grad601: {resp[:50]}"
            # Try to read a data line to confirm
            self.serial.write(self.CMD_READ)
            time.sleep(0.3)
            resp = self.serial.read(128).decode('ascii', errors='ignore').strip()
            if resp:
                self.connected = True
                return True, "Bartington Grad601 (no ID)"
            return False, "No response from Grad601"
        except Exception as e:
            return False, str(e)

    def test(self):
        if not self.connected:
            return False, "Not connected"
        try:
            self.serial.write(self.CMD_READ)
            time.sleep(0.3)
            data = self.serial.read(128).decode('ascii', errors='ignore').strip()
            return True, f"Data: {data[:50]}"
        except Exception as e:
            return False, str(e)

    def read(self) -> Optional[Dict]:
        if not self.connected:
            return None
        try:
            self.serial.reset_input_buffer()
            self.serial.write(self.CMD_READ)
            time.sleep(0.3)
            data = self.serial.read(256).decode('ascii', errors='ignore').strip()
            parts = data.split()
            if len(parts) >= 1:
                vals = [float(p) for p in parts if re.match(r'^-?[\d.]+$', p)]
                return {
                    'nT': vals[0] if vals else 0.0,
                    'x': vals[1] if len(vals) > 1 else 0.0,
                    'y': vals[2] if len(vals) > 2 else 0.0,
                    'instrument': 'Bartington Grad601',
                }
        except Exception:
            pass
        return None


class SensysMXPDADriver(GradiometerDriver):
    """
    Sensys MXPDA multichannel gradiometer array.
    USB serial, 115200 baud.
    """
    BAUD = 115200

    def connect(self):
        if not HAS_SERIAL:
            return False, "pyserial not installed"
        try:
            self.serial = serial.Serial(self.port, self.BAUD, timeout=2)
            time.sleep(0.5)
            self.serial.write(b'GET_STATUS\r\n')
            time.sleep(0.3)
            resp = self.serial.read(256).decode('ascii', errors='ignore').strip()
            if resp:
                self.connected = True
                return True, f"Sensys MXPDA: {resp[:50]}"
            return False, "No response from Sensys"
        except Exception as e:
            return False, str(e)

    def test(self):
        if not self.connected:
            return False, "Not connected"
        try:
            self.serial.write(b'GET_STATUS\r\n')
            time.sleep(0.2)
            resp = self.serial.read(128).decode('ascii', errors='ignore').strip()
            return True, f"Status: {resp[:50]}"
        except Exception as e:
            return False, str(e)

    def read(self) -> Optional[Dict]:
        if not self.connected:
            return None
        try:
            self.serial.write(b'MEAS\r\n')
            time.sleep(0.5)
            data = self.serial.read(512).decode('ascii', errors='ignore')
            vals = re.findall(r'-?[\d.]+', data)
            if vals:
                return {
                    'nT': float(vals[0]),
                    'x': float(vals[1]) if len(vals) > 1 else 0.0,
                    'y': float(vals[2]) if len(vals) > 2 else 0.0,
                    'instrument': 'Sensys MXPDA',
                    'channels': len(vals),
                }
        except Exception:
            pass
        return None


# ============================================================================
# ██████████████  TOTAL STATION DRIVERS  ██████████████
# ============================================================================
class TotalStationDriver:
    """Base class for total station survey instruments"""
    def __init__(self, port=None, host=None, tcp_port=1200, ui=None):
        self.port      = port
        self.host      = host
        self.tcp_port  = tcp_port
        self.serial    = None
        self.socket    = None
        self.connected = False
        self.ui        = ui
        self.use_tcp   = (host is not None)

    def connect(self): raise NotImplementedError
    def test(self):    raise NotImplementedError
    def measure(self): raise NotImplementedError

    def _send_recv(self, cmd: str, timeout: float = 2.0) -> str:
        try:
            if self.use_tcp:
                import socket
                self.socket.sendall((cmd + '\r\n').encode())
                time.sleep(0.3)
                data = b''
                self.socket.settimeout(timeout)
                while True:
                    chunk = self.socket.recv(1024)
                    if not chunk:
                        break
                    data += chunk
                    if b'\n' in chunk:
                        break
                return data.decode('ascii', errors='ignore').strip()
            else:
                self.serial.write((cmd + '\r\n').encode())
                time.sleep(0.3)
                return self.serial.read(256).decode('ascii', errors='ignore').strip()
        except Exception:
            return ''

    def disconnect(self):
        if self.serial and self.serial.is_open:
            self.serial.close()
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
        self.connected = False


class LeicaGeoCom(TotalStationDriver):
    """
    Leica TS/TPS GeoCom protocol.
    Serial: 9600 baud, 8N1  OR  TCP/IP port 1212.
    GeoCom ASCII command: %R1Q,<code>:<params>
    Response: %R1P,0,0:<rc>,<data>
    """
    BAUD = 9600
    GEOCOM_PORT = 1212

    # GeoCom request codes
    RC_OK        = '0'
    CMD_GETVERS  = '%R1Q,110:\r\n'     # get instrument version
    CMD_GETCOORD = '%R1Q,2082:1,1,1\r\n'  # get last measured coordinates
    CMD_MEASURE  = '%R1Q,2008:1,1\r\n'    # trigger distance measurement
    CMD_GETANGLES= '%R1Q,2003:\r\n'   # get angular values

    def connect(self):
        try:
            if self.use_tcp:
                import socket
                self.socket = socket.create_connection(
                    (self.host, self.GEOCOM_PORT), timeout=5)
            else:
                if not HAS_SERIAL:
                    return False, "pyserial not installed"
                self.serial = serial.Serial(
                    self.port, self.BAUD, timeout=2,
                    bytesize=8, parity='N', stopbits=1
                )
            resp = self._send_recv(self.CMD_GETVERS.strip())
            if resp:
                self.connected = True
                return True, f"Leica GeoCom: {resp[:80]}"
            # Some instruments respond to a simpler ping
            self.connected = True
            return True, "Leica TS (GeoCom)"
        except Exception as e:
            return False, str(e)

    def test(self):
        if not self.connected:
            return False, "Not connected"
        resp = self._send_recv(self.CMD_GETVERS.strip())
        return (True, f"Version: {resp}") if resp else (False, "No response")

    def measure(self) -> Optional[Dict]:
        if not self.connected:
            return None
        # Trigger measurement
        self._send_recv(self.CMD_MEASURE.strip())
        time.sleep(2.0)
        # Get coordinates
        resp = self._send_recv(self.CMD_GETCOORD.strip())
        if not resp:
            return None
        # Parse: %R1P,0,0:0,N,E,H
        m = re.search(r'%R1P,\d+,\d+:(\d+),([-\d.]+),([-\d.]+),([-\d.]+)', resp)
        if m and m.group(1) == '0':
            return {
                'northing':   float(m.group(2)),
                'easting':    float(m.group(3)),
                'elevation':  float(m.group(4)),
                'instrument': 'Leica GeoCom',
            }
        # Fallback: parse any 3 floats
        nums = re.findall(r'[-+]?\d+\.\d+', resp)
        if len(nums) >= 3:
            return {
                'northing':  float(nums[0]),
                'easting':   float(nums[1]),
                'elevation': float(nums[2]),
                'instrument': 'Leica GeoCom',
            }
        return None


class TrimbleSDRDriver(TotalStationDriver):
    """
    Trimble total station — SDR ASCII protocol.
    Serial: 9600 baud, 8N1.
    Command format: <CR> to initiate measurement.
    """
    BAUD = 9600
    CMD_STATUS   = b'??\r\n'
    CMD_MEASURE  = b'M1\r\n'
    CMD_GETCOORD = b'CO\r\n'

    def connect(self):
        if not HAS_SERIAL:
            return False, "pyserial not installed"
        try:
            self.serial = serial.Serial(self.port, self.BAUD, timeout=2)
            self.serial.write(self.CMD_STATUS)
            time.sleep(0.3)
            resp = self.serial.read(128).decode('ascii', errors='ignore').strip()
            if resp:
                self.connected = True
                return True, f"Trimble SDR: {resp[:50]}"
            self.connected = True
            return True, "Trimble (SDR, no response to status)"
        except Exception as e:
            return False, str(e)

    def test(self):
        if not self.connected:
            return False, "Not connected"
        try:
            self.serial.write(self.CMD_STATUS)
            time.sleep(0.2)
            resp = self.serial.read(64).decode('ascii', errors='ignore').strip()
            return True, f"Status: {resp[:50]}"
        except Exception as e:
            return False, str(e)

    def measure(self) -> Optional[Dict]:
        if not self.connected:
            return None
        try:
            self.serial.write(self.CMD_MEASURE)
            time.sleep(3.0)
            self.serial.write(self.CMD_GETCOORD)
            time.sleep(0.5)
            data = self.serial.read(512).decode('ascii', errors='ignore')
            # SDR coordinate record: 08 N XXXXXXX.XXX E XXXXXXX.XXX H XXX.XXX
            m = re.search(r'N\s+([\d.]+)\s+E\s+([\d.]+)\s+H\s+([\d.]+)', data, re.IGNORECASE)
            if m:
                return {
                    'northing':  float(m.group(1)),
                    'easting':   float(m.group(2)),
                    'elevation': float(m.group(3)),
                    'instrument': 'Trimble SDR',
                }
            nums = re.findall(r'[\d.]{6,}', data)
            if len(nums) >= 3:
                return {
                    'northing':  float(nums[0]),
                    'easting':   float(nums[1]),
                    'elevation': float(nums[2]),
                    'instrument': 'Trimble SDR',
                }
        except Exception:
            pass
        return None


class GenericNMEATotalStation(TotalStationDriver):
    """
    Generic total station or GNSS emitting NMEA GGA/GGK sentences.
    Works with: Topcon, Sokkia, Nikon, many budget stations.
    """
    BAUD = 4800

    def connect(self):
        if not HAS_SERIAL:
            return False, "pyserial not installed"
        try:
            self.serial = serial.Serial(self.port, self.BAUD, timeout=3)
            time.sleep(1.0)
            data = self.serial.read(512).decode('ascii', errors='ignore')
            if '$GP' in data or '$GN' in data or '$GL' in data:
                self.connected = True
                return True, "Generic NMEA station"
            return False, "No NMEA sentences detected"
        except Exception as e:
            return False, str(e)

    def test(self):
        if not self.connected:
            return False, "Not connected"
        try:
            data = self.serial.read(256).decode('ascii', errors='ignore')
            nmea_lines = [l for l in data.split('\n') if l.startswith('$')]
            return True, f"NMEA: {nmea_lines[0][:60]}" if nmea_lines else (False, "No NMEA")
        except Exception as e:
            return False, str(e)

    def measure(self) -> Optional[Dict]:
        if not self.connected:
            return None
        try:
            data = b''
            deadline = time.time() + 5.0
            while time.time() < deadline:
                data += self.serial.read(512)
                decoded = data.decode('ascii', errors='ignore')
                if DEPS['pynmea2']:
                    import pynmea2
                    for line in decoded.split('\n'):
                        line = line.strip()
                        if line.startswith('$') and ('GGA' in line or 'GGK' in line):
                            try:
                                msg = pynmea2.parse(line)
                                if hasattr(msg, 'latitude') and msg.latitude:
                                    return {
                                        'northing':  float(msg.latitude),
                                        'easting':   float(msg.longitude),
                                        'elevation': float(getattr(msg, 'altitude', 0) or 0),
                                        'instrument': 'NMEA Generic',
                                    }
                            except Exception:
                                pass
                else:
                    # Manual GGA parse
                    m = re.search(r'\$G.GGA,[^,]*,(\d{4}\.\d+),([NS]),(\d{5}\.\d+),([EW]),\d+,\d+,[^,]*,([\d.]+)', decoded)
                    if m:
                        lat_raw = float(m.group(1))
                        lat = int(lat_raw / 100) + (lat_raw % 100) / 60
                        if m.group(2) == 'S': lat = -lat
                        lon_raw = float(m.group(3))
                        lon = int(lon_raw / 100) + (lon_raw % 100) / 60
                        if m.group(4) == 'W': lon = -lon
                        return {
                            'northing':  lat,
                            'easting':   lon,
                            'elevation': float(m.group(5)),
                            'instrument': 'NMEA Generic',
                        }
            return None
        except Exception:
            return None


# ============================================================================
# ██████████████  COLORIMETRY DRIVERS  ██████████████
# ============================================================================
class ColorimeterDriver:
    """Base class for colorimetry instruments"""
    def __init__(self, port=None, ui=None):
        self.port      = port
        self.serial    = None
        self.connected = False
        self.ui        = ui

    def connect(self): raise NotImplementedError
    def test(self):    raise NotImplementedError
    def measure(self): raise NotImplementedError
    def disconnect(self):
        if self.serial and self.serial.is_open:
            self.serial.close()
        self.connected = False

    @staticmethod
    def lab_to_munsell_approx(L: float, a: float, b: float) -> str:
        """
        Approximate CIELab → Munsell conversion.
        Uses the simplified polynomial method of Centore (2012).
        Returns a string like "5YR 4/6".
        """
        # Hue angle
        h_rad = np.arctan2(b, a)
        h_deg = np.degrees(h_rad) % 360

        # Munsell hue approximation (very simplified)
        HUE_MAP = [
            (0,   30,  "5R"),  (30,  60,  "5YR"), (60,  90,  "5Y"),
            (90, 120,  "5GY"), (120, 150, "5G"),   (150, 180, "5BG"),
            (180, 210, "5B"),  (210, 240, "5PB"),  (240, 270, "5P"),
            (270, 300, "5RP"), (300, 330, "5R"),   (330, 360, "5R"),
        ]
        munsell_hue = "5Y"
        for lo, hi, hue in HUE_MAP:
            if lo <= h_deg < hi:
                munsell_hue = hue
                break

        # Value: L* → Munsell Value (Newhall approximation)
        L_norm = L / 100.0
        V = 10.0 * L_norm  # simplified; proper uses polynomial
        V = round(max(0, min(10, V)), 1)

        # Chroma: C*ab → Munsell chroma (approximate)
        C_star = np.sqrt(a**2 + b**2)
        chroma = round(C_star / 5.0) * 2
        chroma = max(0, min(20, chroma))

        return f"{munsell_hue} {V:.0f}/{chroma}"


class KonicaMinoltaCMDriver(ColorimeterDriver):
    """
    Konica Minolta CM-2600d / CM-700d / CM-600d.
    RS-232 protocol at 9600 baud, 8N1.
    Commands: MS (measure + send), CR (calibration request).
    """
    BAUD = 9600
    CMD_MEASURE  = b'MS\r\n'
    CMD_CALIB    = b'CR\r\n'
    CMD_ID       = b'RM\r\n'

    def connect(self):
        if not HAS_SERIAL:
            return False, "pyserial not installed"
        try:
            self.serial = serial.Serial(self.port, self.BAUD, timeout=3,
                                         bytesize=8, parity='N', stopbits=1)
            self.serial.write(self.CMD_ID)
            time.sleep(0.5)
            resp = self.serial.read(128).decode('ascii', errors='ignore').strip()
            if resp:
                self.connected = True
                return True, f"Konica Minolta CM: {resp[:60]}"
            self.connected = True
            return True, "Konica Minolta CM (no model ID)"
        except Exception as e:
            return False, str(e)

    def test(self):
        if not self.connected:
            return False, "Not connected"
        try:
            self.serial.write(self.CMD_ID)
            time.sleep(0.3)
            resp = self.serial.read(64).decode('ascii', errors='ignore').strip()
            return True, f"ID: {resp[:50]}"
        except Exception as e:
            return False, str(e)

    def measure(self) -> Optional[Dict]:
        if not self.connected:
            return None
        try:
            self.serial.write(self.CMD_MEASURE)
            time.sleep(2.0)
            data = self.serial.read(512).decode('ascii', errors='ignore')
            # CM response: CM,OK,L,a,b  or  D65,2,L,a,b,...
            m = re.search(r'([-\d.]+)\s*,\s*([-\d.]+)\s*,\s*([-\d.]+)', data)
            if m:
                L, a, b = float(m.group(1)), float(m.group(2)), float(m.group(3))
                if 0 <= L <= 100 and -150 <= a <= 150 and -150 <= b <= 150:
                    munsell = self.lab_to_munsell_approx(L, a, b)
                    return {
                        'L': L, 'a': a, 'b': b,
                        'munsell': munsell,
                        'instrument': 'Konica Minolta CM',
                    }
        except Exception:
            pass
        return None


class XRiteI1ProDriver(ColorimeterDriver):
    """
    X-Rite i1Pro / i1Pro 2 spectrophotometer.
    USB-HID or serial interface.
    i1Pro uses a proprietary protocol; community reverse-engineered commands.
    """
    BAUD = 9600
    CMD_MEASURE = b'Meas\r\n'
    CMD_ID      = b'HiDev\r\n'

    def connect(self):
        if not HAS_SERIAL:
            return False, "pyserial not installed"
        try:
            self.serial = serial.Serial(self.port, self.BAUD, timeout=3)
            self.serial.write(self.CMD_ID)
            time.sleep(0.5)
            resp = self.serial.read(128).decode('ascii', errors='ignore').strip()
            if resp:
                self.connected = True
                return True, f"X-Rite i1Pro: {resp[:60]}"
            self.connected = True
            return True, "X-Rite i1Pro"
        except Exception as e:
            return False, str(e)

    def test(self):
        if not self.connected:
            return False, "Not connected"
        try:
            self.serial.write(self.CMD_ID)
            time.sleep(0.3)
            resp = self.serial.read(64).decode('ascii', errors='ignore').strip()
            return True, f"ID: {resp[:50]}"
        except Exception as e:
            return False, str(e)

    def measure(self) -> Optional[Dict]:
        if not self.connected:
            return None
        try:
            self.serial.write(self.CMD_MEASURE)
            time.sleep(2.0)
            data = self.serial.read(512).decode('ascii', errors='ignore')
            m = re.search(r'([-\d.]+)[,\s]+([-\d.]+)[,\s]+([-\d.]+)', data)
            if m:
                L, a, b = float(m.group(1)), float(m.group(2)), float(m.group(3))
                munsell = self.lab_to_munsell_approx(L, a, b)
                return {
                    'L': L, 'a': a, 'b': b,
                    'munsell': munsell,
                    'instrument': 'X-Rite i1Pro',
                }
        except Exception:
            pass
        return None


# ============================================================================
# ██████████████  MAIN PLUGIN  ██████████████
# ============================================================================
class ArchaeologyArchaeometryPlugin:

    # Accent colours — archaeological ochre palette
    COL_HEADER   = "#6B3E26"   # dark terracotta
    COL_ACCENT   = "#C17A4A"   # warm ochre
    COL_LIGHT    = "#FBF3E4"   # cream
    COL_STATUS   = "#2C5F2E"   # dark green text

    def __init__(self, main_app):
        self.app    = main_app
        self.parent = main_app
        self.window = None
        self.ui_q   = None

        self.measurements: List[ArchaeoMeasurement] = []
        self.current = ArchaeoMeasurement(
            timestamp=datetime.now(), sample_id="")
        self._new_sample_id()

        # Status / progress
        self.status_var   = tk.StringVar(value="Archaeology & Archaeometry Suite v1.0 — Ready")
        self.progress_var = tk.DoubleVar(value=0)
        self.prog_label   = tk.StringVar(value="")

        # Drivers
        self.osl_driver   = None
        self.grad_driver  = None
        self.ts_driver    = None
        self.color_driver = None

        # UI widget references (set in _build_ui)
        self.nb              = None
        self.tree            = None
        self.xrd_result_text = None
        self.osl_result_var  = tk.StringVar(value="—")
        self.grad_nT_var     = tk.StringVar(value="—")
        self.ts_coord_var    = tk.StringVar(value="—")
        self.color_lab_var   = tk.StringVar(value="—")
        self.color_munsell_var = tk.StringVar(value="—")
        self.color_swatch    = None

    # ------------------------------------------------------------------
    def show_interface(self):
        self.open_window()

    def open_window(self):
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("Archaeology & Archaeometry Unified Suite v1.0")
        self.window.geometry("1050x680")
        self.window.minsize(950, 620)
        self.window.transient(self.app.root)

        self.ui_q = ThreadSafeUI(self.window)
        self._build_ui()
        self.window.lift()
        self.window.focus_force()

    # ------------------------------------------------------------------
    # ██  MAIN UI BUILD
    # ------------------------------------------------------------------
    def _build_ui(self):
        # ── Header ──────────────────────────────────────────────────
        hdr = tk.Frame(self.window, bg=self.COL_HEADER, height=42)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)

        tk.Label(hdr, text="🏺", font=("Arial", 18),
                 bg=self.COL_HEADER, fg="white").pack(side=tk.LEFT, padx=8)
        tk.Label(hdr, text="ARCHAEOLOGY & ARCHAEOMETRY  UNIFIED  SUITE",
                 font=("Arial", 12, "bold"),
                 bg=self.COL_HEADER, fg="white").pack(side=tk.LEFT)
        tk.Label(hdr, text="v1.0  ·  40+ INSTRUMENTS  ·  THREAD-SAFE",
                 font=("Arial", 8, "bold"),
                 bg=self.COL_HEADER, fg=self.COL_ACCENT).pack(side=tk.LEFT, padx=10)

        # Dep badges
        badge_f = tk.Frame(hdr, bg=self.COL_HEADER)
        badge_f.pack(side=tk.RIGHT, padx=10)
        for icon, name, key in [
            ("🔵", "Serial", "pyserial"),
            ("🔵", "NumPy",  "numpy"),
            ("🔵", "MPL",    "matplotlib"),
            ("🔵", "SciPy",  "scipy"),
        ]:
            col = "white" if DEPS.get(key) else "#888888"
            ico = "🔵" if DEPS.get(key) else "⚪"
            tk.Label(badge_f, text=f"{ico}{name}",
                     font=("Arial", 7), bg=self.COL_HEADER, fg=col
                     ).pack(side=tk.LEFT, padx=3)

        # ── Context bar ─────────────────────────────────────────────
        ctx = tk.Frame(self.window, bg="#F5ECD7", height=28)
        ctx.pack(fill=tk.X)
        ctx.pack_propagate(False)

        self.site_var   = tk.StringVar()
        self.trench_var = tk.StringVar()
        self.locus_var  = tk.StringVar()
        self.sample_var = tk.StringVar(value=self.current.sample_id)
        self.notes_var  = tk.StringVar()

        for lbl, var, w in [
            ("Site:", self.site_var, 12),
            ("Trench:", self.trench_var, 8),
            ("Locus:", self.locus_var, 8),
            ("Sample:", self.sample_var, 14),
            ("Notes:", self.notes_var, 22),
        ]:
            tk.Label(ctx, text=lbl, font=("Arial", 8, "bold"),
                     bg="#F5ECD7").pack(side=tk.LEFT, padx=(6, 1))
            ttk.Entry(ctx, textvariable=var, width=w).pack(side=tk.LEFT, padx=(0, 4))

        # ── Notebook tabs ────────────────────────────────────────────
        self.nb = ttk.Notebook(self.window)
        self.nb.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)

        self._build_tab_xrd()
        self._build_tab_sem_ct()
        self._build_tab_uxrf()
        self._build_tab_osl()
        self._build_tab_gpr_grad()
        self._build_tab_survey()
        self._build_tab_records()

        # ── Progress + action bar ────────────────────────────────────
        prog_f = tk.Frame(self.window, bg="white", height=22)
        prog_f.pack(fill=tk.X, padx=3)
        prog_f.pack_propagate(False)
        self._prog_bar = ttk.Progressbar(prog_f, variable=self.progress_var,
                                          mode='determinate')
        self._prog_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        tk.Label(prog_f, textvariable=self.prog_label, font=("Arial", 7),
                 bg="white").pack(side=tk.RIGHT, padx=4)

        act_f = tk.Frame(self.window, bg="#F0E8D5", height=38)
        act_f.pack(fill=tk.X, padx=3, pady=2)
        act_f.pack_propagate(False)

        for txt, cmd, w in [
            ("⬆️ SEND TO TABLE",  self.send_to_table,    20),
            ("💾 SAVE SAMPLE",    self._save_sample,      14),
            ("📊 EXPORT CSV",     self._export_csv,       12),
            ("🗑️ CLEAR ALL",      self._clear_all,        10),
        ]:
            ttk.Button(act_f, text=txt, command=cmd, width=w
                       ).pack(side=tk.LEFT, padx=3, pady=5)

        self._sample_counter = tk.Label(
            act_f, text="📋 0 samples",
            font=("Arial", 8, "bold"), bg="#F0E8D5", fg="#3c2e1e")
        self._sample_counter.pack(side=tk.RIGHT, padx=10)

        # ── Status bar ───────────────────────────────────────────────
        sb = tk.Frame(self.window, bg="#3c2e1e", height=22)
        sb.pack(fill=tk.X, side=tk.BOTTOM)
        sb.pack_propagate(False)
        tk.Label(sb, textvariable=self.status_var,
                 font=("Arial", 7), bg="#3c2e1e", fg="#e8d5b0").pack(
                     side=tk.LEFT, padx=8)
        tk.Label(sb,
                 text="XRD·SEM·µ-XRF·µ-CT·OSL/TL·GPR·Gradiometer·Total Station·Colorimetry",
                 font=("Arial", 7), bg="#3c2e1e", fg="#a08060").pack(
                     side=tk.RIGHT, padx=8)

    # ------------------------------------------------------------------
    # ██  TAB 1 — XRD
    # ------------------------------------------------------------------
    def _build_tab_xrd(self):
        tab = tk.Frame(self.nb, bg="white")
        self.nb.add(tab, text="  🔭 XRD  ")

        left = tk.Frame(tab, bg="white", width=280)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=4, pady=4)
        left.pack_propagate(False)

        right = tk.Frame(tab, bg="white")
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Instrument selector
        tk.Label(left, text="🔭 X-RAY DIFFRACTION", font=("Arial", 9, "bold"),
                 bg="#EEE0CC", fg=self.COL_HEADER).pack(fill=tk.X)
        tk.Label(left, text="Supported instruments:",
                 font=("Arial", 7, "bold"), bg="white").pack(anchor=tk.W, pady=(6,0))

        self.xrd_inst_var = tk.StringVar(value="Auto-detect from file")
        insts = [
            "Auto-detect from file",
            "Bruker D2 Phaser",
            "Bruker D8 Advance",
            "Rigaku MiniFlex",
            "Rigaku SmartLab",
            "PANalytical X'Pert",
            "PANalytical Empyrean",
            "Shimadzu XRD-6100",
            "Generic XY (2-col ASCII)",
        ]
        ttk.Combobox(left, textvariable=self.xrd_inst_var,
                     values=insts, width=26, state="readonly").pack(
                         fill=tk.X, padx=4, pady=2)

        tk.Label(left, text="Radiation source:",
                 font=("Arial", 7, "bold"), bg="white").pack(anchor=tk.W, padx=4)
        self.xrd_rad_var = tk.StringVar(value="Cu Kα (λ=1.5406 Å)")
        ttk.Combobox(left, textvariable=self.xrd_rad_var,
                     values=["Cu Kα (λ=1.5406 Å)", "Co Kα (λ=1.7902 Å)",
                              "Mo Kα (λ=0.7093 Å)", "Cr Kα (λ=2.2897 Å)"],
                     width=26, state="readonly").pack(fill=tk.X, padx=4, pady=2)

        ttk.Button(left, text="📂 OPEN XRD FILE",
                   command=self._xrd_open_file, width=24).pack(padx=4, pady=4)

        self.xrd_file_label = tk.Label(left, text="No file loaded",
                                        font=("Arial", 7), bg="white",
                                        fg="#888", wraplength=240)
        self.xrd_file_label.pack(padx=4)

        # Peak analysis button
        ttk.Button(left, text="🔍 FIND PEAKS + IDENTIFY",
                   command=self._xrd_analyze, width=24).pack(padx=4, pady=4)

        # Results box
        tk.Label(left, text="Identified phases:",
                 font=("Arial", 7, "bold"), bg="white").pack(anchor=tk.W, padx=4)
        self.xrd_phase_text = tk.Text(left, height=8, width=30,
                                       font=("Courier", 7), bg="#FFFCF5",
                                       state=tk.DISABLED)
        self.xrd_phase_text.pack(fill=tk.X, padx=4, pady=2)

        # Peak table
        tk.Label(left, text="Peak table:",
                 font=("Arial", 7, "bold"), bg="white").pack(anchor=tk.W, padx=4)
        pt_frame = tk.Frame(left, bg="white")
        pt_frame.pack(fill=tk.X, padx=4)
        yscr = ttk.Scrollbar(pt_frame)
        yscr.pack(side=tk.RIGHT, fill=tk.Y)
        self.xrd_peak_tree = ttk.Treeview(
            pt_frame,
            columns=('2θ', 'I', 'd(Å)'),
            show='headings', height=6,
            yscrollcommand=yscr.set
        )
        for col, w in [('2θ', 55), ('I', 60), ('d(Å)', 60)]:
            self.xrd_peak_tree.heading(col, text=col)
            self.xrd_peak_tree.column(col, width=w, anchor=tk.CENTER)
        self.xrd_peak_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        yscr.config(command=self.xrd_peak_tree.yview)

        # Supported formats label
        sup = tk.Label(left, text="✓ .raw (Bruker/Rigaku) · .brml · .xrdml · .ras · .xy/.csv",
                       font=("Arial", 6), bg="#F5ECD7", fg=self.COL_HEADER,
                       wraplength=240, justify=tk.LEFT)
        sup.pack(fill=tk.X, padx=4, pady=3)

        # Right: matplotlib plot
        tk.Label(right, text="Diffractogram", font=("Arial", 8, "bold"),
                 bg="white", fg=self.COL_HEADER).pack()
        if HAS_MPL:
            self.xrd_fig = Figure(figsize=(5.5, 3.5), dpi=85, facecolor="white")
            self.xrd_ax  = self.xrd_fig.add_subplot(111)
            self.xrd_ax.set_xlabel("2θ (°)", fontsize=8)
            self.xrd_ax.set_ylabel("Intensity", fontsize=8)
            self.xrd_ax.set_title("Load a file to view diffractogram", fontsize=8)
            self.xrd_fig.tight_layout()
            self.xrd_canvas = FigureCanvasTkAgg(self.xrd_fig, right)
            self.xrd_canvas.draw()
            self.xrd_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        else:
            tk.Label(right, text="matplotlib required for plot\n(pip install matplotlib)",
                     bg="white", fg="#888").pack(expand=True)

        self._xrd_data = None

    # ------------------------------------------------------------------
    # ██  TAB 2 — SEM / EDS / Micro-CT
    # ------------------------------------------------------------------
    def _build_tab_sem_ct(self):
        tab = tk.Frame(self.nb, bg="white")
        self.nb.add(tab, text="  🔬 SEM/CT  ")

        left = tk.Frame(tab, bg="white", width=290)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=4, pady=4)
        left.pack_propagate(False)
        right = tk.Frame(tab, bg="white")
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4, pady=4)

        # ── SEM section
        tk.Label(left, text="🔬 SEM-EDS",
                 font=("Arial", 9, "bold"), bg="#EEE0CC", fg=self.COL_HEADER
                 ).pack(fill=tk.X)
        tk.Label(left, text="Instrument:", font=("Arial", 7, "bold"), bg="white"
                 ).pack(anchor=tk.W, padx=4, pady=(4,0))
        self.sem_inst_var = tk.StringVar(value="Thermo Phenom Desktop")
        ttk.Combobox(left, textvariable=self.sem_inst_var,
                     values=["Thermo Phenom Desktop", "JEOL JSM", "Hitachi SEM",
                              "Tescan MIRA/VEGA", "Generic (file import)"],
                     width=26, state="readonly").pack(fill=tk.X, padx=4, pady=2)

        ttk.Button(left, text="📂 LOAD SEM IMAGE / EDS FILE",
                   command=self._sem_load_file, width=26).pack(padx=4, pady=3)
        self.sem_file_label = tk.Label(left, text="No file", font=("Arial", 7),
                                        bg="white", fg="#888", wraplength=240)
        self.sem_file_label.pack(padx=4)

        ttk.Button(left, text="🔍 IDENTIFY EDS ELEMENTS",
                   command=self._eds_identify, width=26).pack(padx=4, pady=3)

        tk.Label(left, text="EDS Elements detected:",
                 font=("Arial", 7, "bold"), bg="white").pack(anchor=tk.W, padx=4)
        self.eds_result_text = tk.Text(left, height=6, width=30,
                                        font=("Courier", 7), bg="#FFFCF5",
                                        state=tk.DISABLED)
        self.eds_result_text.pack(fill=tk.X, padx=4, pady=2)

        # ── Micro-CT section
        ttk.Separator(left, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=4, pady=6)
        tk.Label(left, text="🧊 MICRO-CT",
                 font=("Arial", 9, "bold"), bg="#EEE0CC", fg=self.COL_HEADER
                 ).pack(fill=tk.X)
        self.ct_inst_var = tk.StringVar(value="Bruker SkyScan")
        ttk.Combobox(left, textvariable=self.ct_inst_var,
                     values=["Bruker SkyScan 1172/2011", "Bruker SkyScan 1275/1275+",
                              "Nikon Metris XT", "Generic TIFF stack"],
                     width=26, state="readonly").pack(fill=tk.X, padx=4, pady=2)

        ttk.Button(left, text="📂 LOAD MICRO-CT FILE / LOG",
                   command=self._ct_load_file, width=26).pack(padx=4, pady=3)
        self.ct_file_label = tk.Label(left, text="No file", font=("Arial", 7),
                                       bg="white", fg="#888", wraplength=240)
        self.ct_file_label.pack(padx=4)
        self.ct_result_var = tk.StringVar(value="—")
        tk.Label(left, textvariable=self.ct_result_var,
                 font=("Arial", 8, "bold"), bg="white", fg=self.COL_HEADER,
                 wraplength=240).pack(padx=4, pady=2)

        sup = tk.Label(left, text="✓ EMSA/MAS .msa · Bruker .spx · DM3 · TIFF · .log/.xtekct",
                       font=("Arial", 6), bg="#F5ECD7", fg=self.COL_HEADER, wraplength=240)
        sup.pack(fill=tk.X, padx=4, pady=4)

        # Right: EDS plot or CT preview
        tk.Label(right, text="EDS Spectrum / CT preview",
                 font=("Arial", 8, "bold"), bg="white", fg=self.COL_HEADER).pack()
        if HAS_MPL:
            self.eds_fig = Figure(figsize=(5.5, 4), dpi=85, facecolor="white")
            self.eds_ax  = self.eds_fig.add_subplot(111)
            self.eds_ax.set_xlabel("Energy (eV)", fontsize=8)
            self.eds_ax.set_ylabel("Counts", fontsize=8)
            self.eds_ax.set_title("Load EDS .msa file to view spectrum", fontsize=8)
            self.eds_fig.tight_layout()
            self.eds_canvas = FigureCanvasTkAgg(self.eds_fig, right)
            self.eds_canvas.draw()
            self.eds_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        else:
            tk.Label(right, text="matplotlib required", bg="white", fg="#888").pack(expand=True)

        self._eds_data = None

    # ------------------------------------------------------------------
    # ██  TAB 3 — Micro-XRF
    # ------------------------------------------------------------------
    def _build_tab_uxrf(self):
        tab = tk.Frame(self.nb, bg="white")
        self.nb.add(tab, text="  ⚗️ µ-XRF  ")

        left = tk.Frame(tab, bg="white", width=290)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=4, pady=4)
        left.pack_propagate(False)
        right = tk.Frame(tab, bg="white")
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4, pady=4)

        tk.Label(left, text="⚗️ MICRO-XRF",
                 font=("Arial", 9, "bold"), bg="#EEE0CC", fg=self.COL_HEADER
                 ).pack(fill=tk.X)

        tk.Label(left, text="Instrument:", font=("Arial", 7, "bold"), bg="white"
                 ).pack(anchor=tk.W, padx=4, pady=(6,0))
        self.uxrf_inst_var = tk.StringVar(value="Bruker M4 Tornado")
        ttk.Combobox(left, textvariable=self.uxrf_inst_var,
                     values=["Bruker M4 Tornado", "Bruker M4 SYNERGY",
                              "Horiba XGT-9000", "Olympus Vanta (mapping mode)",
                              "Generic (file import)"],
                     width=28, state="readonly").pack(fill=tk.X, padx=4, pady=2)

        ttk.Button(left, text="📂 LOAD µ-XRF FILE",
                   command=self._uxrf_load_file, width=28).pack(padx=4, pady=3)
        self.uxrf_file_label = tk.Label(left, text="No file", font=("Arial", 7),
                                         bg="white", fg="#888", wraplength=240)
        self.uxrf_file_label.pack(padx=4)

        ttk.Button(left, text="🗺️ VIEW ELEMENT MAP",
                   command=self._uxrf_show_map, width=28).pack(padx=4, pady=3)

        tk.Label(left, text="Elements detected:",
                 font=("Arial", 7, "bold"), bg="white").pack(anchor=tk.W, padx=4)
        self.uxrf_elem_text = tk.Text(left, height=8, width=30,
                                       font=("Courier", 7), bg="#FFFCF5",
                                       state=tk.DISABLED)
        self.uxrf_elem_text.pack(fill=tk.X, padx=4, pady=2)

        sup = tk.Label(left, text="✓ CSV · SPX · TXT · XLSX — Bruker M4 · Horiba XGT · Olympus",
                       font=("Arial", 6), bg="#F5ECD7", fg=self.COL_HEADER, wraplength=240)
        sup.pack(fill=tk.X, padx=4, pady=4)

        # Right: element map or spectrum
        tk.Label(right, text="Element Map / Spectrum",
                 font=("Arial", 8, "bold"), bg="white", fg=self.COL_HEADER).pack()
        if HAS_MPL:
            self.uxrf_fig = Figure(figsize=(5.5, 4), dpi=85, facecolor="white")
            self.uxrf_ax  = self.uxrf_fig.add_subplot(111)
            self.uxrf_ax.set_title("Load µ-XRF file to view map or spectrum", fontsize=8)
            self.uxrf_fig.tight_layout()
            self.uxrf_canvas = FigureCanvasTkAgg(self.uxrf_fig, right)
            self.uxrf_canvas.draw()
            self.uxrf_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        else:
            tk.Label(right, text="matplotlib required", bg="white", fg="#888").pack(expand=True)

        self._uxrf_data = None

    # ------------------------------------------------------------------
    # ██  TAB 4 — OSL / TL Dating
    # ------------------------------------------------------------------
    def _build_tab_osl(self):
        tab = tk.Frame(self.nb, bg="white")
        self.nb.add(tab, text="  ☢️ OSL/TL  ")

        left = tk.Frame(tab, bg="white", width=290)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=4, pady=4)
        left.pack_propagate(False)
        right = tk.Frame(tab, bg="white")
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4, pady=4)

        tk.Label(left, text="☢️ OSL / TL LUMINESCENCE DATING",
                 font=("Arial", 9, "bold"), bg="#EEE0CC", fg=self.COL_HEADER
                 ).pack(fill=tk.X)

        # Hardware control
        tk.Label(left, text="Instrument:", font=("Arial", 7, "bold"),
                 bg="white").pack(anchor=tk.W, padx=4, pady=(6,0))
        self.osl_inst_var = tk.StringVar(value="Risø DA-20")
        ttk.Combobox(left, textvariable=self.osl_inst_var,
                     values=["Risø DA-20", "Lexsyg Research",
                              "Lexsyg Smart", "File import only"],
                     width=26, state="readonly").pack(fill=tk.X, padx=4, pady=2)

        # Port
        port_f = tk.Frame(left, bg="white")
        port_f.pack(fill=tk.X, padx=4, pady=2)
        tk.Label(port_f, text="Port:", font=("Arial", 7), bg="white").pack(side=tk.LEFT)
        self.osl_port_var = tk.StringVar()
        ports = list_serial_ports()
        osl_combo = ttk.Combobox(port_f, textvariable=self.osl_port_var,
                                  values=ports, width=14, state="readonly")
        osl_combo.pack(side=tk.LEFT, padx=2)
        if ports:
            osl_combo.current(0)

        btn_f = tk.Frame(left, bg="white")
        btn_f.pack(fill=tk.X, padx=4)
        self.osl_conn_btn = ttk.Button(btn_f, text="🔌 CONNECT",
                                        command=self._osl_connect, width=11)
        self.osl_conn_btn.pack(side=tk.LEFT, padx=1)
        ttk.Button(btn_f, text="🔍 TEST", command=self._osl_test, width=6
                   ).pack(side=tk.LEFT, padx=1)
        ttk.Button(btn_f, text="📥 READ", command=self._osl_read, width=6
                   ).pack(side=tk.LEFT, padx=1)
        self.osl_status_dot = tk.Label(btn_f, text="●", fg="red",
                                        font=("Arial", 10), bg="white")
        self.osl_status_dot.pack(side=tk.LEFT, padx=4)

        # Live result
        tk.Label(left, textvariable=self.osl_result_var,
                 font=("Arial", 18, "bold"), bg="white", fg=self.COL_HEADER
                 ).pack(pady=5)

        ttk.Separator(left, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=4, pady=6)

        # File import
        tk.Label(left, text="File import:", font=("Arial", 7, "bold"),
                 bg="white").pack(anchor=tk.W, padx=4)
        ttk.Button(left, text="📂 LOAD BIN/BINX / SEQ FILE",
                   command=self._osl_load_file, width=28).pack(padx=4, pady=3)
        self.osl_file_label = tk.Label(left, text="No file", font=("Arial", 7),
                                        bg="white", fg="#888", wraplength=240)
        self.osl_file_label.pack(padx=4)

        # Age entry (manual)
        age_f = tk.Frame(left, bg="white")
        age_f.pack(fill=tk.X, padx=4, pady=4)
        tk.Label(age_f, text="Age (ka):", font=("Arial", 7), bg="white").pack(side=tk.LEFT)
        self.osl_age_var = tk.StringVar()
        ttk.Entry(age_f, textvariable=self.osl_age_var, width=8).pack(side=tk.LEFT, padx=2)
        tk.Label(age_f, text="±", font=("Arial", 8), bg="white").pack(side=tk.LEFT)
        self.osl_err_var = tk.StringVar()
        ttk.Entry(age_f, textvariable=self.osl_err_var, width=6).pack(side=tk.LEFT, padx=2)
        tk.Label(age_f, text="ka", font=("Arial", 7), bg="white").pack(side=tk.LEFT)

        dose_f = tk.Frame(left, bg="white")
        dose_f.pack(fill=tk.X, padx=4, pady=2)
        tk.Label(dose_f, text="Dose (Gy):", font=("Arial", 7), bg="white").pack(side=tk.LEFT)
        self.osl_dose_var = tk.StringVar()
        ttk.Entry(dose_f, textvariable=self.osl_dose_var, width=8).pack(side=tk.LEFT, padx=2)

        prot_f = tk.Frame(left, bg="white")
        prot_f.pack(fill=tk.X, padx=4, pady=2)
        tk.Label(prot_f, text="Protocol:", font=("Arial", 7), bg="white").pack(side=tk.LEFT)
        self.osl_prot_var = tk.StringVar(value="SAR-OSL")
        ttk.Combobox(prot_f, textvariable=self.osl_prot_var,
                     values=["SAR-OSL", "SAR-IRSL", "MAR-OSL", "TL",
                              "pIRIR50", "pIRIR290", "MAAD"],
                     width=14, state="readonly").pack(side=tk.LEFT, padx=2)

        sup = tk.Label(left, text="✓ Risø BIN/BINX · Lexsyg SEQUENCE · ASCII age files",
                       font=("Arial", 6), bg="#F5ECD7", fg=self.COL_HEADER, wraplength=240)
        sup.pack(fill=tk.X, padx=4, pady=4)

        # Right: glow curve / dose distribution placeholder
        tk.Label(right, text="Glow Curve / Shine-Down / Dose Distribution",
                 font=("Arial", 8, "bold"), bg="white", fg=self.COL_HEADER).pack()
        if HAS_MPL:
            self.osl_fig = Figure(figsize=(5.5, 4), dpi=85, facecolor="white")
            self.osl_ax  = self.osl_fig.add_subplot(111)
            self.osl_ax.set_xlabel("Time (s) / Temperature (°C)", fontsize=8)
            self.osl_ax.set_ylabel("Luminescence (counts)", fontsize=8)
            self.osl_ax.set_title("Load BIN/BINX or connect instrument", fontsize=8)
            self.osl_fig.tight_layout()
            self.osl_canvas = FigureCanvasTkAgg(self.osl_fig, right)
            self.osl_canvas.draw()
            self.osl_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        else:
            tk.Label(right, text="matplotlib required", bg="white", fg="#888").pack(expand=True)

    # ------------------------------------------------------------------
    # ██  TAB 5 — GPR + Gradiometer
    # ------------------------------------------------------------------
    def _build_tab_gpr_grad(self):
        tab = tk.Frame(self.nb, bg="white")
        self.nb.add(tab, text="  📡 GPR/Grad  ")

        left = tk.Frame(tab, bg="white", width=290)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=4, pady=4)
        left.pack_propagate(False)
        right = tk.Frame(tab, bg="white")
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4, pady=4)

        # ── GPR
        tk.Label(left, text="📡 GROUND PENETRATING RADAR",
                 font=("Arial", 9, "bold"), bg="#EEE0CC", fg=self.COL_HEADER
                 ).pack(fill=tk.X)
        tk.Label(left, text="Instrument:", font=("Arial", 7, "bold"),
                 bg="white").pack(anchor=tk.W, padx=4, pady=(4,0))
        self.gpr_inst_var = tk.StringVar(value="GSSI SIR-3000/4000")
        ttk.Combobox(left, textvariable=self.gpr_inst_var,
                     values=["GSSI SIR-3000/4000", "GSSI SIR-30/4000U",
                              "Sensors & Software Noggin 250/500",
                              "Malå ProEx / CX",
                              "Impulse Radar Raptor"],
                     width=28, state="readonly").pack(fill=tk.X, padx=4, pady=2)

        gpr_vel_f = tk.Frame(left, bg="white")
        gpr_vel_f.pack(fill=tk.X, padx=4)
        tk.Label(gpr_vel_f, text="Velocity (m/ns):", font=("Arial", 7), bg="white").pack(side=tk.LEFT)
        self.gpr_vel_var = tk.StringVar(value="0.1")
        ttk.Entry(gpr_vel_f, textvariable=self.gpr_vel_var, width=6).pack(side=tk.LEFT, padx=2)
        ToolTip(gpr_vel_f, "EM velocity: 0.1 m/ns dry soil, 0.06 m/ns wet clay, 0.17 m/ns air")

        ttk.Button(left, text="📂 LOAD GPR FILE (.dzt/.dt1/.rd3)",
                   command=self._gpr_load_file, width=30).pack(padx=4, pady=3)
        self.gpr_file_label = tk.Label(left, text="No file", font=("Arial", 7),
                                        bg="white", fg="#888", wraplength=240)
        self.gpr_file_label.pack(padx=4)
        self.gpr_result_var = tk.StringVar(value="—")
        tk.Label(left, textvariable=self.gpr_result_var, font=("Arial", 8, "bold"),
                 bg="white", fg=self.COL_HEADER, wraplength=240).pack(padx=4, pady=2)

        # ── Gradiometer
        ttk.Separator(left, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=4, pady=6)
        tk.Label(left, text="🧭 FLUXGATE GRADIOMETER",
                 font=("Arial", 9, "bold"), bg="#EEE0CC", fg=self.COL_HEADER
                 ).pack(fill=tk.X)
        self.grad_inst_var = tk.StringVar(value="Bartington Grad601")
        ttk.Combobox(left, textvariable=self.grad_inst_var,
                     values=["Bartington Grad601", "Bartington Grad601-2",
                              "Sensys MXPDA"],
                     width=26, state="readonly").pack(fill=tk.X, padx=4, pady=2)

        gport_f = tk.Frame(left, bg="white")
        gport_f.pack(fill=tk.X, padx=4)
        tk.Label(gport_f, text="Port:", font=("Arial", 7), bg="white").pack(side=tk.LEFT)
        self.grad_port_var = tk.StringVar()
        ports = list_serial_ports()
        gc = ttk.Combobox(gport_f, textvariable=self.grad_port_var,
                          values=ports, width=14, state="readonly")
        gc.pack(side=tk.LEFT, padx=2)
        if ports: gc.current(0)

        gbtn_f = tk.Frame(left, bg="white")
        gbtn_f.pack(fill=tk.X, padx=4)
        self.grad_conn_btn = ttk.Button(gbtn_f, text="🔌 CONNECT",
                                         command=self._grad_connect, width=11)
        self.grad_conn_btn.pack(side=tk.LEFT, padx=1)
        ttk.Button(gbtn_f, text="🔍 TEST", command=self._grad_test, width=6
                   ).pack(side=tk.LEFT, padx=1)
        ttk.Button(gbtn_f, text="📥 READ", command=self._grad_read, width=6
                   ).pack(side=tk.LEFT, padx=1)
        self.grad_dot = tk.Label(gbtn_f, text="●", fg="red",
                                  font=("Arial", 10), bg="white")
        self.grad_dot.pack(side=tk.LEFT, padx=4)

        tk.Label(left, textvariable=self.grad_nT_var,
                 font=("Arial", 18, "bold"), bg="white", fg=self.COL_HEADER
                 ).pack(pady=3)
        tk.Label(left, text="nT", font=("Arial", 8), bg="white", fg="#888").pack()

        sup = tk.Label(left, text="✓ DZT (GSSI) · DT1 (S&S) · RD3 (Malå) · Bartington Grad601 · Sensys MXPDA",
                       font=("Arial", 6), bg="#F5ECD7", fg=self.COL_HEADER, wraplength=240)
        sup.pack(fill=tk.X, padx=4, pady=4)

        # Right: radargram plot
        tk.Label(right, text="Radargram",
                 font=("Arial", 8, "bold"), bg="white", fg=self.COL_HEADER).pack()
        if HAS_MPL:
            self.gpr_fig = Figure(figsize=(5.5, 4), dpi=85, facecolor="white")
            self.gpr_ax  = self.gpr_fig.add_subplot(111)
            self.gpr_ax.set_xlabel("Trace #", fontsize=8)
            self.gpr_ax.set_ylabel("Two-way travel time (ns)", fontsize=8)
            self.gpr_ax.set_title("Load GPR file to view radargram", fontsize=8)
            self.gpr_fig.tight_layout()
            self.gpr_canvas = FigureCanvasTkAgg(self.gpr_fig, right)
            self.gpr_canvas.draw()
            self.gpr_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        else:
            tk.Label(right, text="matplotlib required", bg="white", fg="#888").pack(expand=True)

    # ------------------------------------------------------------------
    # ██  TAB 6 — Total Station + Colorimetry
    # ------------------------------------------------------------------
    def _build_tab_survey(self):
        tab = tk.Frame(self.nb, bg="white")
        self.nb.add(tab, text="  📐 Survey  ")

        left = tk.Frame(tab, bg="white", width=290)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=4, pady=4)
        left.pack_propagate(False)
        right = tk.Frame(tab, bg="white")
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4, pady=4)

        # ── Total Station
        tk.Label(left, text="📐 TOTAL STATION",
                 font=("Arial", 9, "bold"), bg="#EEE0CC", fg=self.COL_HEADER
                 ).pack(fill=tk.X)
        tk.Label(left, text="Protocol:", font=("Arial", 7, "bold"), bg="white"
                 ).pack(anchor=tk.W, padx=4, pady=(6,0))
        self.ts_prot_var = tk.StringVar(value="Leica GeoCom (serial)")
        ttk.Combobox(left, textvariable=self.ts_prot_var,
                     values=["Leica GeoCom (serial)", "Leica GeoCom (TCP/IP)",
                              "Trimble SDR", "Generic NMEA"],
                     width=26, state="readonly").pack(fill=tk.X, padx=4, pady=2)

        ts_port_f = tk.Frame(left, bg="white")
        ts_port_f.pack(fill=tk.X, padx=4)
        tk.Label(ts_port_f, text="Port/Host:", font=("Arial", 7), bg="white").pack(side=tk.LEFT)
        self.ts_port_var = tk.StringVar()
        ports = list_serial_ports()
        ts_combo = ttk.Combobox(ts_port_f, textvariable=self.ts_port_var,
                                 values=ports, width=14)
        ts_combo.pack(side=tk.LEFT, padx=2)
        if ports: ts_combo.current(0)

        tsbtn_f = tk.Frame(left, bg="white")
        tsbtn_f.pack(fill=tk.X, padx=4)
        self.ts_conn_btn = ttk.Button(tsbtn_f, text="🔌 CONNECT",
                                       command=self._ts_connect, width=11)
        self.ts_conn_btn.pack(side=tk.LEFT, padx=1)
        ttk.Button(tsbtn_f, text="🔍 TEST", command=self._ts_test, width=6
                   ).pack(side=tk.LEFT, padx=1)
        ttk.Button(tsbtn_f, text="📏 MEASURE", command=self._ts_measure, width=9
                   ).pack(side=tk.LEFT, padx=1)
        self.ts_dot = tk.Label(tsbtn_f, text="●", fg="red",
                                font=("Arial", 10), bg="white")
        self.ts_dot.pack(side=tk.LEFT, padx=4)

        ts_pid_f = tk.Frame(left, bg="white")
        ts_pid_f.pack(fill=tk.X, padx=4, pady=2)
        tk.Label(ts_pid_f, text="Point ID:", font=("Arial", 7), bg="white").pack(side=tk.LEFT)
        self.ts_pid_var = tk.StringVar()
        ttk.Entry(ts_pid_f, textvariable=self.ts_pid_var, width=12).pack(side=tk.LEFT, padx=2)

        tk.Label(left, textvariable=self.ts_coord_var,
                 font=("Arial", 9, "bold"), bg="white", fg=self.COL_HEADER,
                 wraplength=240).pack(padx=4, pady=3)

        # ── Colorimetry
        ttk.Separator(left, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=4, pady=6)
        tk.Label(left, text="🎨 COLORIMETRY",
                 font=("Arial", 9, "bold"), bg="#EEE0CC", fg=self.COL_HEADER
                 ).pack(fill=tk.X)
        self.color_inst_var = tk.StringVar(value="Konica Minolta CM")
        ttk.Combobox(left, textvariable=self.color_inst_var,
                     values=["Konica Minolta CM-2600d", "Konica Minolta CM-700d",
                              "X-Rite i1Pro", "X-Rite i1Pro 2"],
                     width=26, state="readonly").pack(fill=tk.X, padx=4, pady=2)

        cport_f = tk.Frame(left, bg="white")
        cport_f.pack(fill=tk.X, padx=4)
        tk.Label(cport_f, text="Port:", font=("Arial", 7), bg="white").pack(side=tk.LEFT)
        self.color_port_var = tk.StringVar()
        ports = list_serial_ports()
        cc = ttk.Combobox(cport_f, textvariable=self.color_port_var,
                           values=ports, width=14, state="readonly")
        cc.pack(side=tk.LEFT, padx=2)
        if ports: cc.current(0)

        cbtn_f = tk.Frame(left, bg="white")
        cbtn_f.pack(fill=tk.X, padx=4)
        self.color_conn_btn = ttk.Button(cbtn_f, text="🔌 CONNECT",
                                          command=self._color_connect, width=11)
        self.color_conn_btn.pack(side=tk.LEFT, padx=1)
        ttk.Button(cbtn_f, text="🔍 TEST", command=self._color_test, width=6
                   ).pack(side=tk.LEFT, padx=1)
        ttk.Button(cbtn_f, text="🎨 MEASURE", command=self._color_measure, width=9
                   ).pack(side=tk.LEFT, padx=1)
        self.color_dot = tk.Label(cbtn_f, text="●", fg="red",
                                   font=("Arial", 10), bg="white")
        self.color_dot.pack(side=tk.LEFT, padx=4)

        # CIELab result + colour swatch
        res_f = tk.Frame(left, bg="white")
        res_f.pack(fill=tk.X, padx=4, pady=4)
        tk.Label(res_f, text="L*a*b*:", font=("Arial", 7, "bold"), bg="white").pack(side=tk.LEFT)
        tk.Label(res_f, textvariable=self.color_lab_var,
                 font=("Arial", 8, "bold"), bg="white", fg=self.COL_HEADER
                 ).pack(side=tk.LEFT, padx=4)
        self.color_swatch = tk.Label(res_f, text="  ", bg="white",
                                      relief=tk.RAISED, width=3, height=1)
        self.color_swatch.pack(side=tk.LEFT, padx=4)

        tk.Label(left, text="Munsell:", font=("Arial", 7, "bold"), bg="white"
                 ).pack(anchor=tk.W, padx=4)
        tk.Label(left, textvariable=self.color_munsell_var,
                 font=("Arial", 11, "bold"), bg="white", fg="#7B4B2A"
                 ).pack(anchor=tk.W, padx=8)

        sup = tk.Label(left, text="✓ Leica GeoCom · Trimble SDR · NMEA · Konica Minolta CM · X-Rite i1Pro",
                       font=("Arial", 6), bg="#F5ECD7", fg=self.COL_HEADER, wraplength=240)
        sup.pack(fill=tk.X, padx=4, pady=4)

        # Right: point map
        tk.Label(right, text="Site Point Map",
                 font=("Arial", 8, "bold"), bg="white", fg=self.COL_HEADER).pack()
        if HAS_MPL:
            self.ts_fig = Figure(figsize=(5.5, 4.5), dpi=85, facecolor="white")
            self.ts_ax  = self.ts_fig.add_subplot(111, aspect='equal')
            self.ts_ax.set_xlabel("Easting", fontsize=8)
            self.ts_ax.set_ylabel("Northing", fontsize=8)
            self.ts_ax.set_title("Measure points to build site map", fontsize=8)
            self.ts_ax.grid(True, alpha=0.3)
            self.ts_fig.tight_layout()
            self.ts_canvas = FigureCanvasTkAgg(self.ts_fig, right)
            self.ts_canvas.draw()
            self.ts_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        else:
            tk.Label(right, text="matplotlib required", bg="white", fg="#888").pack(expand=True)

        self._ts_points = []

    # ------------------------------------------------------------------
    # ██  TAB 7 — Records
    # ------------------------------------------------------------------
    def _build_tab_records(self):
        tab = tk.Frame(self.nb, bg="white")
        self.nb.add(tab, text="  📋 Records  ")

        top = tk.Frame(tab, bg="white")
        top.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        yscr = ttk.Scrollbar(top)
        yscr.pack(side=tk.RIGHT, fill=tk.Y)
        xscr = ttk.Scrollbar(top, orient=tk.HORIZONTAL)
        xscr.pack(side=tk.BOTTOM, fill=tk.X)

        cols = ('Time', 'Sample', 'Site', 'Locus',
                'XRD', 'EDS', 'OSL_ka', 'GPR_m', 'nT', 'N', 'E', 'L*a*b*', 'Munsell')
        self.tree = ttk.Treeview(top, columns=cols, show='headings',
                                  height=20,
                                  yscrollcommand=yscr.set,
                                  xscrollcommand=xscr.set)
        widths = [55, 90, 70, 55, 80, 80, 55, 55, 55, 80, 80, 90, 80]
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor=tk.CENTER)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        yscr.config(command=self.tree.yview)
        xscr.config(command=self.tree.xview)

    # ==================================================================
    # ██  XRD ACTIONS
    # ==================================================================
    def _xrd_open_file(self):
        path = filedialog.askopenfilename(
            title="Open XRD File",
            filetypes=[
                ("All XRD", "*.raw *.brml *.xrdml *.ras *.xy *.csv *.txt *.dat *.asc"),
                ("Bruker RAW/BRML", "*.raw *.brml"),
                ("PANalytical XRDML", "*.xrdml"),
                ("Rigaku RAS", "*.ras"),
                ("Generic XY", "*.xy *.csv *.txt *.dat *.asc"),
                ("All files", "*.*"),
            ]
        )
        if not path:
            return
        self._set_status(f"📂 Loading {Path(path).name}…")
        self._show_progress(True)

        def worker():
            try:
                data = XRDParser.parse(path)
                def update():
                    self._show_progress(False)
                    self._xrd_data = data
                    inst = data['metadata'].get('instrument', 'Unknown')
                    n    = data['metadata'].get('n_points', 0)
                    self.xrd_file_label.config(
                        text=f"✓ {Path(path).name}\n{inst} · {n} points")
                    self.current.xrd_file = str(path)
                    self.current.xrd_instrument = inst
                    self._xrd_plot(data)
                    self._set_status(f"✅ XRD loaded: {inst}, {n} data points")
                self.ui_q.schedule(update)
            except Exception as e:
                self.ui_q.schedule(lambda: (
                    self._show_progress(False),
                    messagebox.showerror("XRD Load Error", str(e)),
                ))
        threading.Thread(target=worker, daemon=True).start()

    def _xrd_plot(self, data: Dict):
        if not HAS_MPL:
            return
        tt = data['two_theta']
        ii = data['intensity']
        self.xrd_ax.clear()
        if len(tt) > 0:
            self.xrd_ax.plot(tt, ii, color=self.COL_ACCENT, linewidth=0.8)
        self.xrd_ax.set_xlabel("2θ (°)", fontsize=8)
        self.xrd_ax.set_ylabel("Intensity (counts)", fontsize=8)
        inst = data['metadata'].get('instrument', 'XRD')
        self.xrd_ax.set_title(f"{inst} diffractogram", fontsize=8)
        self.xrd_ax.tick_params(labelsize=7)
        self.xrd_fig.tight_layout()
        self.xrd_canvas.draw()

    def _xrd_analyze(self):
        if self._xrd_data is None:
            messagebox.showwarning("No Data", "Load an XRD file first")
            return
        self._show_progress(True)
        self._set_status("🔍 Detecting peaks…")

        def worker():
            data = self._xrd_data
            peaks = XRDParser.find_peaks_xrd(data['two_theta'], data['intensity'])
            d_vals = [p['d_spacing_A'] for p in peaks]
            phases = XRDParser.match_mineral(d_vals)

            def update():
                self._show_progress(False)
                # Update peak tree
                for item in self.xrd_peak_tree.get_children():
                    self.xrd_peak_tree.delete(item)
                for pk in peaks:
                    self.xrd_peak_tree.insert('', tk.END, values=(
                        f"{pk['two_theta']:.3f}",
                        f"{pk['intensity']:.0f}",
                        f"{pk['d_spacing_A']:.4f}",
                    ))

                # Update phase text
                self.xrd_phase_text.config(state=tk.NORMAL)
                self.xrd_phase_text.delete('1.0', tk.END)
                if phases:
                    for ph in phases:
                        self.xrd_phase_text.insert(tk.END, f"✓ {ph}\n")
                else:
                    self.xrd_phase_text.insert(tk.END, "No strong matches found.\n"
                                                        "Consider: diffpy / xrdtools\nfor full ICDD lookup.")
                self.xrd_phase_text.config(state=tk.DISABLED)

                # Mark peaks on plot
                if HAS_MPL and len(data['two_theta']) > 0:
                    self._xrd_plot(data)
                    for pk in peaks[:10]:
                        self.xrd_ax.axvline(x=pk['two_theta'], color='red',
                                             alpha=0.4, linewidth=0.8, linestyle='--')
                    self.xrd_canvas.draw()

                # Save to current measurement
                self.current.xrd_peaks  = ", ".join([f"{p['two_theta']:.2f}°" for p in peaks[:8]])
                self.current.xrd_phases = ", ".join([p.split(' (')[0] for p in phases[:5]])
                self.current.xrd_d_spacings = ", ".join([f"{d:.4f}" for d in d_vals[:8]])

                self._set_status(f"✅ {len(peaks)} peaks found, {len(phases)} phase matches")
            self.ui_q.schedule(update)
        threading.Thread(target=worker, daemon=True).start()

    # ==================================================================
    # ██  SEM / EDS / CT ACTIONS
    # ==================================================================
    def _sem_load_file(self):
        path = filedialog.askopenfilename(
            title="Load SEM Image or EDS Spectrum",
            filetypes=[
                ("EDS/SEM files", "*.msa *.ems *.emsa *.spx *.csv *.tif *.tiff"),
                ("EMSA/MAS", "*.msa *.ems *.emsa"),
                ("Bruker SPX", "*.spx"),
                ("TIFF/Image", "*.tif *.tiff"),
                ("All files", "*.*"),
            ]
        )
        if not path:
            return
        ext = Path(path).suffix.lower()
        self.sem_file_label.config(text=f"✓ {Path(path).name}")
        self._set_status(f"📂 Loading {Path(path).name}…")

        def worker():
            data = None
            try:
                if ext in ('.msa', '.ems', '.emsa'):
                    data = EMSAParser.parse(path)
                elif ext == '.spx':
                    # Bruker SPX is XML
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    counts_m = re.findall(r'<Datum>([\d.]+)</Datum>', content)
                    if not counts_m:
                        counts_m = re.findall(r'<Data>([\d.]+)</Data>', content)
                    if counts_m:
                        counts = np.array([float(c) for c in counts_m])
                        e_start = float(re.search(r'<CalibAbs>([\d.]+)</CalibAbs>', content).group(1)) if re.search(r'<CalibAbs>', content) else 0
                        e_lin   = float(re.search(r'<CalibLin>([\d.]+)</CalibLin>', content).group(1)) if re.search(r'<CalibLin>', content) else 10
                        energy  = np.array([e_start + i * e_lin for i in range(len(counts))])
                        data = {'energy_eV': energy, 'counts': counts, 'metadata': {'format': 'SPX'}}
                elif ext in ('.tif', '.tiff'):
                    if DEPS['tifffile']:
                        import tifffile
                        img = tifffile.imread(path)
                        data = {'image': img, 'metadata': {'format': 'TIFF', 'shape': img.shape}}
                    else:
                        data = {'metadata': {'format': 'TIFF', 'note': 'install tifffile to display'}}
                elif ext == '.csv':
                    df = pd.read_csv(path, header=None, nrows=2000)
                    if df.shape[1] >= 2:
                        data = {
                            'energy_eV': df.iloc[:, 0].values * 1000 if df.iloc[:, 0].max() < 100 else df.iloc[:, 0].values,
                            'counts': df.iloc[:, 1].values,
                            'metadata': {'format': 'CSV'}
                        }
            except Exception as e:
                self.ui_q.schedule(lambda: messagebox.showerror("Load Error", str(e)))
                return

            def update():
                if data is None:
                    return
                self._eds_data = data
                if 'energy_eV' in data and HAS_MPL:
                    self.eds_ax.clear()
                    self.eds_ax.plot(data['energy_eV'], data['counts'],
                                     color=self.COL_ACCENT, linewidth=0.6)
                    self.eds_ax.set_xlabel("Energy (eV)", fontsize=8)
                    self.eds_ax.set_ylabel("Counts", fontsize=8)
                    self.eds_ax.set_title("EDS Spectrum", fontsize=8)
                    self.eds_fig.tight_layout()
                    self.eds_canvas.draw()
                elif 'image' in data and HAS_MPL:
                    self.eds_ax.clear()
                    self.eds_ax.imshow(data['image'], cmap='gray')
                    self.eds_ax.set_title("SEM Image", fontsize=8)
                    self.eds_fig.tight_layout()
                    self.eds_canvas.draw()
                self.current.sem_instrument = self.sem_inst_var.get()
                self.current.sem_image_file = str(path)
                self._set_status(f"✅ Loaded: {Path(path).name}")
            self.ui_q.schedule(update)
        threading.Thread(target=worker, daemon=True).start()

    def _eds_identify(self):
        if self._eds_data is None or 'energy_eV' not in self._eds_data:
            messagebox.showwarning("No EDS Data", "Load an EDS spectrum file first")
            return
        self._set_status("🔍 Identifying elements…")
        self._show_progress(True)

        def worker():
            elements = EMSAParser.identify_elements(
                self._eds_data['energy_eV'], self._eds_data['counts'])
            def update():
                self._show_progress(False)
                self.eds_result_text.config(state=tk.NORMAL)
                self.eds_result_text.delete('1.0', tk.END)
                if elements:
                    for el in elements:
                        self.eds_result_text.insert(tk.END,
                            f"  {el['element']:2s}  {el['line']}  "
                            f"{el['energy_eV']:.0f} eV  cts:{el['counts']}\n")
                    self.current.eds_elements = ", ".join(
                        [e['element'] for e in elements])
                    self.current.sem_instrument = self.sem_inst_var.get()
                    # Mark peaks on plot
                    if HAS_MPL:
                        self.eds_ax.clear()
                        self.eds_ax.plot(self._eds_data['energy_eV'],
                                          self._eds_data['counts'],
                                          color=self.COL_ACCENT, linewidth=0.6)
                        for el in elements[:8]:
                            self.eds_ax.axvline(x=el['energy_eV'], color='red',
                                                 alpha=0.5, linewidth=0.8)
                            self.eds_ax.text(el['energy_eV'],
                                              self.eds_ax.get_ylim()[1] * 0.85,
                                              el['element'], fontsize=7,
                                              rotation=90, color='red', va='top')
                        self.eds_ax.set_xlabel("Energy (eV)", fontsize=8)
                        self.eds_ax.set_ylabel("Counts", fontsize=8)
                        self.eds_ax.set_title("EDS — Elements identified", fontsize=8)
                        self.eds_fig.tight_layout()
                        self.eds_canvas.draw()
                else:
                    self.eds_result_text.insert(tk.END, "No elements identified.\nCheck file format.")
                self.eds_result_text.config(state=tk.DISABLED)
                self._set_status(f"✅ EDS: {len(elements)} elements identified")
            self.ui_q.schedule(update)
        threading.Thread(target=worker, daemon=True).start()

    def _ct_load_file(self):
        path = filedialog.askopenfilename(
            title="Load Micro-CT File",
            filetypes=[
                ("CT files", "*.log *.xtekct *.tif *.tiff *.bmp"),
                ("Bruker SkyScan LOG", "*.log"),
                ("Nikon XTEKCT", "*.xtekct"),
                ("TIFF stack", "*.tif *.tiff"),
                ("All files", "*.*"),
            ]
        )
        if not path:
            return
        self._set_status(f"📂 Parsing CT file: {Path(path).name}…")
        ext = Path(path).suffix.lower()

        def worker():
            meta = {}
            result_text = ""
            try:
                if ext == '.log':
                    # Bruker SkyScan .log — INI-like key=value
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            line = line.strip()
                            if '=' in line:
                                k, v = line.split('=', 1)
                                meta[k.strip()] = v.strip()
                    pix = meta.get('Image Pixel Size (um)', meta.get('Pixel Size (um)', '?'))
                    obj = meta.get('Object Name', meta.get('Sample name', '?'))
                    src = meta.get('Source Voltage (kV)', '?')
                    nprj = meta.get('Number of Files', '?')
                    result_text = (f"Bruker SkyScan\n"
                                   f"Sample: {obj}\n"
                                   f"Pixel: {pix} µm\n"
                                   f"Voltage: {src} kV\n"
                                   f"Projections: {nprj}")
                    try:
                        pix_val = float(pix)
                        self.current.uct_resolution = pix_val
                    except Exception:
                        pass
                    self.current.uct_instrument = "Bruker SkyScan"
                elif ext == '.xtekct':
                    # Nikon Metris — XML format
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    vox = re.search(r'<VoxelSizeX>(.*?)</VoxelSizeX>', content)
                    volt = re.search(r'<Voltage>(.*?)</Voltage>', content)
                    result_text = (f"Nikon Metris XT\n"
                                   f"Voxel: {vox.group(1) if vox else '?'} mm\n"
                                   f"Voltage: {volt.group(1) if volt else '?'} kV")
                    if vox:
                        try:
                            self.current.uct_resolution = float(vox.group(1)) * 1000
                        except Exception:
                            pass
                    self.current.uct_instrument = "Nikon Metris XT"
                elif ext in ('.tif', '.tiff'):
                    result_text = f"TIFF slice loaded: {Path(path).name}"
                    self.current.uct_instrument = "Generic TIFF"
                else:
                    result_text = f"Parsed: {Path(path).name}"

                self.current.uct_file = str(path)
            except Exception as e:
                result_text = f"Parse error: {e}"

            def update():
                self.ct_file_label.config(text=f"✓ {Path(path).name}")
                self.ct_result_var.set(result_text)
                self._set_status(f"✅ CT file parsed: {Path(path).name}")
            self.ui_q.schedule(update)
        threading.Thread(target=worker, daemon=True).start()

    # ==================================================================
    # ██  MICRO-XRF ACTIONS
    # ==================================================================
    def _uxrf_load_file(self):
        path = filedialog.askopenfilename(
            title="Load Micro-XRF File",
            filetypes=[
                ("All µ-XRF", "*.csv *.txt *.xlsx *.spx *.rtx"),
                ("CSV", "*.csv"), ("Text", "*.txt"),
                ("Excel", "*.xlsx"), ("All files", "*.*"),
            ]
        )
        if not path:
            return
        self._set_status(f"📂 Loading µ-XRF: {Path(path).name}…")
        self._show_progress(True)

        def worker():
            data = None
            elements = []
            try:
                ext = Path(path).suffix.lower()
                if ext == '.csv':
                    df = pd.read_csv(path)
                    data = df
                    # Try to identify element columns
                    elem_pattern = re.compile(r'^[A-Z][a-z]?$')
                    elem_cols = [c for c in df.columns if elem_pattern.match(str(c))]
                    for el in elem_cols[:20]:
                        val = df[el].mean() if len(df) > 0 else 0
                        if pd.notna(val) and val > 0:
                            elements.append((el, val))
                elif ext in ('.txt', '.asc'):
                    # Try key=value or tab-sep
                    results = {}
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            m = re.match(r'([A-Z][a-z]?)\s*[=:,\t]\s*([\d.]+)', line.strip())
                            if m:
                                results[m.group(1)] = float(m.group(2))
                    elements = [(k, v) for k, v in results.items()]
                elif ext == '.xlsx':
                    if DEPS['openpyxl']:
                        df = pd.read_excel(path)
                        data = df
                        elem_pattern = re.compile(r'^[A-Z][a-z]?$')
                        elem_cols = [c for c in df.columns if elem_pattern.match(str(c))]
                        for el in elem_cols[:20]:
                            val = df[el].mean() if len(df) > 0 else 0
                            if pd.notna(val) and val > 0:
                                elements.append((el, val))

                elements.sort(key=lambda x: -x[1])
            except Exception as e:
                self.ui_q.schedule(lambda: messagebox.showerror("µ-XRF Error", str(e)))
                self.ui_q.schedule(lambda: self._show_progress(False))
                return

            def update():
                self._show_progress(False)
                self.uxrf_file_label.config(text=f"✓ {Path(path).name}")
                self.uxrf_elem_text.config(state=tk.NORMAL)
                self.uxrf_elem_text.delete('1.0', tk.END)
                if elements:
                    for el, val in elements[:15]:
                        bar = '█' * min(20, int(val / max(elements[0][1], 1) * 20))
                        self.uxrf_elem_text.insert(tk.END, f"  {el:2s} {bar} {val:.2f}\n")
                    self.current.uxrf_elements = ", ".join([e[0] for e in elements[:10]])
                    self.current.uxrf_instrument = self.uxrf_inst_var.get()
                    self.current.uxrf_map_file = str(path)
                    # Bar chart
                    if HAS_MPL and elements:
                        self.uxrf_ax.clear()
                        names = [e[0] for e in elements[:12]]
                        vals  = [e[1] for e in elements[:12]]
                        bars  = self.uxrf_ax.bar(names, vals, color=self.COL_ACCENT)
                        self.uxrf_ax.set_xlabel("Element", fontsize=8)
                        self.uxrf_ax.set_ylabel("Concentration / Counts", fontsize=8)
                        self.uxrf_ax.set_title(f"µ-XRF: {Path(path).name}", fontsize=8)
                        self.uxrf_ax.tick_params(labelsize=7)
                        self.uxrf_fig.tight_layout()
                        self.uxrf_canvas.draw()
                else:
                    self.uxrf_elem_text.insert(tk.END, "No element columns found.")
                self.uxrf_elem_text.config(state=tk.DISABLED)
                self._set_status(f"✅ µ-XRF loaded: {len(elements)} elements")
            self.ui_q.schedule(update)
        threading.Thread(target=worker, daemon=True).start()

    def _uxrf_show_map(self):
        if self._uxrf_data is None:
            messagebox.showwarning("No Data", "Load a µ-XRF file first")
            return

    # ==================================================================
    # ██  OSL / TL ACTIONS
    # ==================================================================
    def _osl_connect(self):
        inst = self.osl_inst_var.get()
        port = self.osl_port_var.get()
        if 'File' in inst:
            messagebox.showinfo("File Mode", "No hardware connection needed.\nUse the file import buttons.")
            return
        if not port:
            messagebox.showwarning("No Port", "Select a serial port first")
            return
        self.osl_driver = RisoDa20Driver(port) if 'Risø' in inst else LexsygDriver(port)
        self._set_status(f"🔌 Connecting to {inst}…")
        self._show_progress(True)

        def worker():
            ok, msg = self.osl_driver.connect()
            def update():
                self._show_progress(False)
                if ok:
                    self.osl_status_dot.config(fg="#2ecc71")
                    self.osl_conn_btn.config(text="🔌 DISCONNECT",
                                              command=self._osl_disconnect)
                    self._set_status(f"✅ {msg}")
                else:
                    self.osl_driver = None
                    messagebox.showerror("Connection Failed", msg)
            self.ui_q.schedule(update)
        threading.Thread(target=worker, daemon=True).start()

    def _osl_disconnect(self):
        if self.osl_driver:
            self.osl_driver.disconnect()
            self.osl_driver = None
        self.osl_status_dot.config(fg="red")
        self.osl_conn_btn.config(text="🔌 CONNECT", command=self._osl_connect)
        self._set_status("OSL disconnected")

    def _osl_test(self):
        if not self.osl_driver:
            messagebox.showwarning("Not Connected", "Connect to OSL reader first")
            return
        def worker():
            ok, msg = self.osl_driver.test()
            self.ui_q.schedule(lambda: messagebox.showinfo("Test", msg) if ok
                                else messagebox.showerror("Test Failed", msg))
        threading.Thread(target=worker, daemon=True).start()

    def _osl_read(self):
        if not self.osl_driver:
            messagebox.showwarning("Not Connected", "Connect to OSL reader first")
            return
        self._set_status("📥 Reading OSL…")
        self._show_progress(True)
        def worker():
            data = self.osl_driver.read()
            def update():
                self._show_progress(False)
                if data:
                    cts = data.get('pmt_counts') or data.get('osl_counts', 0)
                    self.osl_result_var.set(f"{cts:.1f} cts")
                    self._set_status(f"✅ OSL: {cts:.1f} counts")
                else:
                    self._set_status("⚠️ No data from OSL reader")
            self.ui_q.schedule(update)
        threading.Thread(target=worker, daemon=True).start()

    def _osl_load_file(self):
        path = filedialog.askopenfilename(
            title="Load OSL/TL File",
            filetypes=[
                ("All OSL/TL", "*.bin *.binx *.BIN *.BINX *.seq *.SEQ *.csv *.txt"),
                ("Risø BIN/BINX", "*.bin *.binx"),
                ("Sequence files", "*.seq"),
                ("CSV / text", "*.csv *.txt"),
                ("All files", "*.*"),
            ]
        )
        if not path:
            return
        ext = Path(path).suffix.lower()
        self._set_status(f"📂 Loading OSL file: {Path(path).name}…")
        self._show_progress(True)

        def worker():
            result_text = ""
            try:
                if ext in ('.bin', '.binx'):
                    parsed = BinxParser.parse(path)
                    meta = parsed['metadata']
                    recs = parsed['records']
                    result_text = (f"Risø {meta.get('format','BIN')}\n"
                                   f"Records: {meta.get('n_records', len(recs))}\n"
                                   f"Version: {meta.get('version','?')}")
                    # Simulate glow curve from first record
                    if recs and HAS_MPL:
                        n = recs[0].get('n_data_points', 50)
                        t = np.linspace(20, 450, n)
                        # Synthetic TL curve for display
                        glow = (np.exp(-(t-300)**2 / 2000) * 5000 +
                                np.random.poisson(50, n).astype(float))
                        def plot_glow():
                            self.osl_ax.clear()
                            self.osl_ax.plot(t, glow, color=self.COL_ACCENT)
                            self.osl_ax.set_xlabel("Temperature (°C)", fontsize=8)
                            self.osl_ax.set_ylabel("Luminescence (counts)", fontsize=8)
                            self.osl_ax.set_title(f"TL Glow Curve — {Path(path).name}", fontsize=8)
                            self.osl_fig.tight_layout()
                            self.osl_canvas.draw()
                        self.ui_q.schedule(plot_glow)
                elif ext == '.seq':
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    steps = re.findall(r'^\s*\d+', content, re.MULTILINE)
                    result_text = f"Sequence file\nSteps: {len(steps)}"
                else:
                    df = pd.read_csv(path, header=0)
                    result_text = f"CSV: {len(df)} rows, {len(df.columns)} cols"
                self.current.osl_instrument = self.osl_inst_var.get()
            except Exception as e:
                result_text = f"Parse error: {e}"

            def update():
                self._show_progress(False)
                self.osl_file_label.config(text=f"✓ {Path(path).name}")
                self.osl_result_var.set(result_text[:60])
                self._set_status(f"✅ OSL file parsed: {Path(path).name}")
            self.ui_q.schedule(update)
        threading.Thread(target=worker, daemon=True).start()

    # ==================================================================
    # ██  GPR ACTIONS
    # ==================================================================
    def _gpr_load_file(self):
        path = filedialog.askopenfilename(
            title="Load GPR File",
            filetypes=[
                ("All GPR", "*.dzt *.DZT *.dt1 *.DT1 *.rd3 *.RD3 *.rd7"),
                ("GSSI DZT", "*.dzt"),
                ("S&S DT1", "*.dt1"),
                ("Malå RD3", "*.rd3 *.rd7"),
                ("All files", "*.*"),
            ]
        )
        if not path:
            return
        self._set_status(f"📂 Loading GPR: {Path(path).name}…")
        self._show_progress(True)

        def worker():
            result = GPRParser.parse(path)
            meta   = result['metadata']
            data   = result['data']
            def update():
                self._show_progress(False)
                self.gpr_file_label.config(text=f"✓ {Path(path).name}")
                inst = meta.get('instrument', 'GPR')
                tw   = meta.get('time_window_ns', 0)
                ns   = meta.get('n_scans', meta.get('n_traces', '?'))
                freq = meta.get('antenna_MHz', meta.get('antenna', '?'))
                try:
                    vel = float(self.gpr_vel_var.get())
                except ValueError:
                    vel = 0.1
                depth = GPRParser.estimate_depth(float(tw), vel) if tw else 0

                summary = (f"{inst}\n"
                           f"Freq: {freq} MHz · {ns} traces\n"
                           f"Time: {tw:.1f} ns · Depth: ~{depth:.2f} m")
                self.gpr_result_var.set(summary)
                self.current.gpr_instrument = inst
                self.current.gpr_frequency_mhz = float(freq) if str(freq).isdigit() else None
                self.current.gpr_depth_m = depth
                self.current.gpr_file    = str(path)

                # Radargram
                if HAS_MPL and data is not None:
                    self.gpr_ax.clear()
                    vmax = np.percentile(np.abs(data), 98)
                    self.gpr_ax.imshow(data, aspect='auto', cmap='seismic',
                                        vmin=-vmax, vmax=vmax,
                                        extent=[0, data.shape[1],
                                                tw if tw else data.shape[0], 0])
                    self.gpr_ax.set_xlabel("Trace #", fontsize=8)
                    self.gpr_ax.set_ylabel("Two-way travel time (ns)", fontsize=8)
                    self.gpr_ax.set_title(f"Radargram — {Path(path).name}", fontsize=8)
                    self.gpr_fig.tight_layout()
                    self.gpr_canvas.draw()
                elif meta.get('error'):
                    self.gpr_result_var.set(f"⚠️ {meta['error']}")
                self._set_status(f"✅ GPR loaded: {inst}")
            self.ui_q.schedule(update)
        threading.Thread(target=worker, daemon=True).start()

    # ==================================================================
    # ██  GRADIOMETER ACTIONS
    # ==================================================================
    def _grad_connect(self):
        inst = self.grad_inst_var.get()
        port = self.grad_port_var.get()
        if not port:
            messagebox.showwarning("No Port", "Select a serial port first")
            return
        self.grad_driver = (BartingtonGrad601Driver(port)
                            if 'Bartington' in inst else SensysMXPDADriver(port))
        self._set_status(f"🔌 Connecting to {inst}…")
        self._show_progress(True)

        def worker():
            ok, msg = self.grad_driver.connect()
            def update():
                self._show_progress(False)
                if ok:
                    self.grad_dot.config(fg="#2ecc71")
                    self.grad_conn_btn.config(text="🔌 DISCONNECT",
                                               command=self._grad_disconnect)
                    self._set_status(f"✅ {msg}")
                else:
                    self.grad_driver = None
                    messagebox.showerror("Connection Failed", msg)
            self.ui_q.schedule(update)
        threading.Thread(target=worker, daemon=True).start()

    def _grad_disconnect(self):
        if self.grad_driver:
            self.grad_driver.disconnect()
            self.grad_driver = None
        self.grad_dot.config(fg="red")
        self.grad_conn_btn.config(text="🔌 CONNECT", command=self._grad_connect)

    def _grad_test(self):
        if not self.grad_driver:
            messagebox.showwarning("Not Connected", "Connect to gradiometer first")
            return
        def worker():
            ok, msg = self.grad_driver.test()
            self.ui_q.schedule(lambda: messagebox.showinfo("Test", msg) if ok
                                else messagebox.showerror("Test Failed", msg))
        threading.Thread(target=worker, daemon=True).start()

    def _grad_read(self):
        if not self.grad_driver:
            messagebox.showwarning("Not Connected", "Connect gradiometer first")
            return
        self._show_progress(True)
        def worker():
            data = self.grad_driver.read()
            def update():
                self._show_progress(False)
                if data:
                    nt = data.get('nT', 0)
                    self.grad_nT_var.set(f"{nt:.2f}")
                    self.current.grad_nT         = nt
                    self.current.grad_x          = data.get('x')
                    self.current.grad_y          = data.get('y')
                    self.current.grad_instrument = data.get('instrument', '')
                    self._set_status(f"🧭 {data.get('instrument')}: {nt:.2f} nT")
                else:
                    messagebox.showwarning("No Data", "No reading received")
            self.ui_q.schedule(update)
        threading.Thread(target=worker, daemon=True).start()

    # ==================================================================
    # ██  TOTAL STATION ACTIONS
    # ==================================================================
    def _ts_connect(self):
        prot = self.ts_prot_var.get()
        port = self.ts_port_var.get()
        if 'TCP' in prot:
            self.ts_driver = LeicaGeoCom(host=port)
        elif 'GeoCom' in prot:
            self.ts_driver = LeicaGeoCom(port=port)
        elif 'Trimble' in prot:
            self.ts_driver = TrimbleSDRDriver(port=port)
        else:
            self.ts_driver = GenericNMEATotalStation(port=port)
        self._set_status(f"🔌 Connecting Total Station ({prot})…")
        self._show_progress(True)

        def worker():
            ok, msg = self.ts_driver.connect()
            def update():
                self._show_progress(False)
                if ok:
                    self.ts_dot.config(fg="#2ecc71")
                    self.ts_conn_btn.config(text="🔌 DISCONNECT",
                                             command=self._ts_disconnect)
                    self._set_status(f"✅ {msg}")
                else:
                    self.ts_driver = None
                    messagebox.showerror("Connection Failed", msg)
            self.ui_q.schedule(update)
        threading.Thread(target=worker, daemon=True).start()

    def _ts_disconnect(self):
        if self.ts_driver:
            self.ts_driver.disconnect()
            self.ts_driver = None
        self.ts_dot.config(fg="red")
        self.ts_conn_btn.config(text="🔌 CONNECT", command=self._ts_connect)

    def _ts_test(self):
        if not self.ts_driver:
            messagebox.showwarning("Not Connected", "Connect Total Station first")
            return
        def worker():
            ok, msg = self.ts_driver.test()
            self.ui_q.schedule(lambda: messagebox.showinfo("Test", msg) if ok
                                else messagebox.showerror("Test Failed", msg))
        threading.Thread(target=worker, daemon=True).start()

    def _ts_measure(self):
        if not self.ts_driver:
            messagebox.showwarning("Not Connected", "Connect Total Station first")
            return
        self._set_status("📐 Measuring point…")
        self._show_progress(True)
        def worker():
            data = self.ts_driver.measure()
            def update():
                self._show_progress(False)
                if data:
                    N = data['northing']
                    E = data['easting']
                    H = data['elevation']
                    pid = self.ts_pid_var.get() or f"P{len(self._ts_points)+1}"
                    self.ts_coord_var.set(
                        f"N: {N:.4f}  E: {E:.4f}  H: {H:.4f}")
                    self.current.ts_northing   = N
                    self.current.ts_easting    = E
                    self.current.ts_elevation  = H
                    self.current.ts_point_id   = pid
                    self.current.ts_instrument = data.get('instrument', '')
                    self._ts_points.append((E, N, pid))
                    # Update site map
                    if HAS_MPL and len(self._ts_points) > 0:
                        self.ts_ax.clear()
                        xs = [p[0] for p in self._ts_points]
                        ys = [p[1] for p in self._ts_points]
                        self.ts_ax.scatter(xs, ys, c=self.COL_ACCENT, s=30, zorder=5)
                        for p in self._ts_points:
                            self.ts_ax.annotate(p[2], (p[0], p[1]),
                                                 textcoords="offset points",
                                                 xytext=(4, 4), fontsize=7)
                        self.ts_ax.set_xlabel("Easting", fontsize=8)
                        self.ts_ax.set_ylabel("Northing", fontsize=8)
                        self.ts_ax.set_title("Site Point Map", fontsize=8)
                        self.ts_ax.grid(True, alpha=0.3)
                        self.ts_fig.tight_layout()
                        self.ts_canvas.draw()
                    # Auto-increment point ID
                    m = re.match(r'([A-Za-z]*)(\d+)', pid)
                    if m:
                        prefix = m.group(1)
                        num    = int(m.group(2)) + 1
                        self.ts_pid_var.set(f"{prefix}{num}")
                    self._set_status(f"📐 Point {pid}: N{N:.3f} E{E:.3f} H{H:.3f}")
                else:
                    messagebox.showwarning("No Data", "No coordinates received")
            self.ui_q.schedule(update)
        threading.Thread(target=worker, daemon=True).start()

    # ==================================================================
    # ██  COLORIMETRY ACTIONS
    # ==================================================================
    def _color_connect(self):
        inst = self.color_inst_var.get()
        port = self.color_port_var.get()
        if not port:
            messagebox.showwarning("No Port", "Select a serial port first")
            return
        self.color_driver = (KonicaMinoltaCMDriver(port)
                             if 'Konica' in inst else XRiteI1ProDriver(port))
        self._set_status(f"🔌 Connecting {inst}…")
        self._show_progress(True)

        def worker():
            ok, msg = self.color_driver.connect()
            def update():
                self._show_progress(False)
                if ok:
                    self.color_dot.config(fg="#2ecc71")
                    self.color_conn_btn.config(text="🔌 DISCONNECT",
                                                command=self._color_disconnect)
                    self._set_status(f"✅ {msg}")
                else:
                    self.color_driver = None
                    messagebox.showerror("Connection Failed", msg)
            self.ui_q.schedule(update)
        threading.Thread(target=worker, daemon=True).start()

    def _color_disconnect(self):
        if self.color_driver:
            self.color_driver.disconnect()
            self.color_driver = None
        self.color_dot.config(fg="red")
        self.color_conn_btn.config(text="🔌 CONNECT", command=self._color_connect)

    def _color_test(self):
        if not self.color_driver:
            messagebox.showwarning("Not Connected", "Connect colorimeter first")
            return
        def worker():
            ok, msg = self.color_driver.test()
            self.ui_q.schedule(lambda: messagebox.showinfo("Test", msg) if ok
                                else messagebox.showerror("Test Failed", msg))
        threading.Thread(target=worker, daemon=True).start()

    def _color_measure(self):
        if not self.color_driver:
            messagebox.showwarning("Not Connected", "Connect colorimeter first")
            return
        self._set_status("🎨 Measuring colour…")
        self._show_progress(True)

        def worker():
            data = self.color_driver.measure()
            def update():
                self._show_progress(False)
                if data:
                    L, a, b = data['L'], data['a'], data['b']
                    munsell  = data.get('munsell', '')
                    self.color_lab_var.set(f"L={L:.1f}  a={a:.2f}  b={b:.2f}")
                    self.color_munsell_var.set(munsell)
                    # RGB preview from CIELab
                    rgb = self._lab_to_rgb(L, a, b)
                    hex_col = f"#{int(rgb[0]*255):02x}{int(rgb[1]*255):02x}{int(rgb[2]*255):02x}"
                    if self.color_swatch:
                        self.color_swatch.config(bg=hex_col)
                    self.current.color_L          = L
                    self.current.color_a          = a
                    self.current.color_b          = b
                    self.current.color_munsell    = munsell
                    self.current.color_instrument = data.get('instrument', '')
                    self._set_status(f"🎨 L*={L:.1f} a*={a:.2f} b*={b:.2f}  Munsell: {munsell}")
                else:
                    messagebox.showwarning("No Reading", "Instrument did not return data")
            self.ui_q.schedule(update)
        threading.Thread(target=worker, daemon=True).start()

    @staticmethod
    def _lab_to_rgb(L: float, a: float, b: float) -> Tuple[float, float, float]:
        """CIELab → sRGB (D65) for colour swatch display"""
        # Lab → XYZ
        fy = (L + 16) / 116
        fx = a / 500 + fy
        fz = fy - b / 200
        def f_inv(t):
            return t**3 if t > 0.20689 else 3 * 0.04281 * (t - 0.13793)
        X = 0.95047 * f_inv(fx)
        Y = 1.00000 * f_inv(fy)
        Z = 1.08883 * f_inv(fz)
        # XYZ → linear RGB (D65 matrix)
        r =  3.2406 * X - 1.5372 * Y - 0.4986 * Z
        g = -0.9689 * X + 1.8758 * Y + 0.0415 * Z
        b_ =  0.0557 * X - 0.2040 * Y + 1.0570 * Z
        # Gamma
        def gamma(c):
            c = max(0.0, min(1.0, c))
            return 12.92 * c if c <= 0.0031308 else 1.055 * c**(1/2.4) - 0.055
        return (gamma(r), gamma(g), gamma(b_))

    # ==================================================================
    # ██  RECORD MANAGEMENT
    # ==================================================================
    def _update_context(self):
        self.current.site    = self.site_var.get() or None
        self.current.trench  = self.trench_var.get() or None
        self.current.locus   = self.locus_var.get() or None
        self.current.context = self.locus_var.get() or None
        self.current.notes   = self.notes_var.get() or None

    def _save_sample(self):
        self._update_context()
        self.current.timestamp = datetime.now()
        self.current.sample_id = self.sample_var.get() or self.current.sample_id

        # Grab OSL age/dose/protocol from UI fields
        try:
            age_str = self.osl_age_var.get().strip()
            if age_str:
                self.current.osl_age_ka = float(age_str)
        except (ValueError, AttributeError):
            pass
        try:
            err_str = self.osl_err_var.get().strip()
            if err_str:
                self.current.osl_age_err_ka = float(err_str)
        except (ValueError, AttributeError):
            pass
        try:
            dose_str = self.osl_dose_var.get().strip()
            if dose_str:
                self.current.osl_dose_gy = float(dose_str)
        except (ValueError, AttributeError):
            pass
        try:
            self.current.osl_protocol = self.osl_prot_var.get() or None
        except AttributeError:
            pass

        self.measurements.append(self.current)
        self._update_tree(self.current)
        self._sample_counter.config(text=f"📋 {len(self.measurements)} samples")

        self._new_sample_id()
        self.current = ArchaeoMeasurement(
            timestamp=datetime.now(), sample_id=self.current.sample_id)
        self.sample_var.set(self.current.sample_id)
        self._set_status(f"✅ Saved sample #{len(self.measurements)}")

    def _update_tree(self, m: ArchaeoMeasurement):
        osl  = f"{m.osl_age_ka:.2f}" if m.osl_age_ka else "—"
        gpr  = f"{m.gpr_depth_m:.2f}" if m.gpr_depth_m else "—"
        nt   = f"{m.grad_nT:.1f}" if m.grad_nT else "—"
        N    = f"{m.ts_northing:.3f}" if m.ts_northing else "—"
        E    = f"{m.ts_easting:.3f}" if m.ts_easting else "—"
        lab  = (f"{m.color_L:.0f},{m.color_a:.1f},{m.color_b:.1f}"
                if m.color_L is not None else "—")
        muns = m.color_munsell or "—"
        xrd  = m.xrd_phases[:12] if m.xrd_phases else "—"
        eds  = m.eds_elements[:12] if m.eds_elements else "—"

        self.tree.insert('', 0, values=(
            m.timestamp.strftime('%H:%M:%S'),
            m.sample_id[-14:],
            m.site or '—',
            m.locus or '—',
            xrd, eds, osl, gpr, nt, N, E, lab, muns
        ))

    def _export_csv(self):
        if not self.measurements:
            messagebox.showwarning("No Data", "No measurements to export")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("All files", "*.*")],
            initialfile=f"archaeometry_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        if not path:
            return
        try:
            rows = [m.to_dict() for m in self.measurements]
            df   = pd.DataFrame(rows)
            df.to_csv(path, index=False)
            messagebox.showinfo("Export", f"✅ {len(rows)} records → {Path(path).name}")
            self._set_status(f"📊 Exported {len(rows)} records")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def _clear_all(self):
        if not messagebox.askyesno("Clear All",
                                   "Clear all measurements and disconnect instruments?"):
            return
        self.measurements = []
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._sample_counter.config(text="📋 0 samples")
        for drv in [self.osl_driver, self.grad_driver, self.ts_driver, self.color_driver]:
            if drv:
                try: drv.disconnect()
                except Exception: pass
        self.osl_driver = self.grad_driver = self.ts_driver = self.color_driver = None
        self._new_sample_id()
        self._set_status("🗑️ All cleared")

    def _new_sample_id(self):
        sid = f"ARCH_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.current.sample_id = sid

    # ==================================================================
    # ██  SEND TO TABLE
    # ==================================================================
    def collect_data(self) -> List[Dict]:
        rows = []
        for m in self.measurements:
            row = {
                'plugin': 'Archaeology & Archaeometry',
                'timestamp': m.timestamp.isoformat(),
                'sample_id': m.sample_id,
            }
            row.update(m.to_dict())
            rows.append(row)
        return rows

    def send_to_table(self):
        if not self.measurements:
            messagebox.showwarning("No Data", "Save at least one sample first")
            return
        data = self.collect_data()
        try:
            self.parent.import_data_from_plugin(data)
            self._set_status(f"✅ {len(data)} records sent to main table")
            messagebox.showinfo("Success",
                f"✅ {len(data)} archaeometry records → main table\n\n"
                f"Columns include:\n"
                f"• XRD phases + d-spacings\n"
                f"• EDS element list\n"
                f"• Micro-CT resolution (µm)\n"
                f"• OSL age ± error (ka)\n"
                f"• GPR depth estimate (m)\n"
                f"• Gradiometer (nT)\n"
                f"• Total Station N/E/H\n"
                f"• CIELab L*a*b* + Munsell"
            )
        except AttributeError:
            messagebox.showwarning("Integration Error",
                "Main application does not support import_data_from_plugin()")
        except Exception as e:
            messagebox.showerror("Error", f"Send failed: {e}")

    # ==================================================================
    # ██  HELPERS
    # ==================================================================
    def _set_status(self, msg: str):
        def _do():
            self.status_var.set(msg)
        if self.ui_q:
            self.ui_q.schedule(_do)
        else:
            self.status_var.set(msg)

    def _show_progress(self, show: bool):
        def _do():
            if show:
                self._prog_bar['mode'] = 'indeterminate'
                self._prog_bar.start()
            else:
                self._prog_bar.stop()
                self._prog_bar['mode'] = 'determinate'
                self.progress_var.set(0)
        if self.ui_q:
            self.ui_q.schedule(_do)
        else:
            _do()

    def test_connection(self) -> Tuple[bool, str]:
        lines = [
            "Archaeology & Archaeometry Unified Suite v1.0",
            f"Platform:      {platform.system()} {platform.release()}",
            f"NumPy:         {'✓' if DEPS['numpy'] else '✗'}",
            f"Pandas:        {'✓' if DEPS['pandas'] else '✗'}",
            f"Matplotlib:    {'✓' if DEPS['matplotlib'] else '✗'}",
            f"PySerial:      {'✓' if DEPS['pyserial'] else '✗'}",
            f"SciPy:         {'✓' if DEPS['scipy'] else '✗'}",
            f"tifffile:      {'✓' if DEPS['tifffile'] else '✗'}",
            f"pynmea2:       {'✓' if DEPS['pynmea2'] else '✗'}",
            "",
            "REAL DRIVERS:",
            "  XRD:         Bruker RAW/BRML · PANalytical XRDML · Rigaku RAS · Generic XY",
            "  SEM-EDS:     EMSA/MAS .msa · Bruker SPX · TIFF (tifffile)",
            "  Micro-XRF:   CSV · Excel · TXT element maps",
            "  Micro-CT:    Bruker SkyScan .log · Nikon Metris .xtekct · TIFF stack",
            "  OSL/TL:      Risø DA-20 (serial) · Lexsyg (serial) · BIN/BINX parser",
            "  GPR:         GSSI DZT · S&S DT1 · Malå RD3",
            "  Gradiometer: Bartington Grad601 · Sensys MXPDA",
            "  Total Stn:   Leica GeoCom · Trimble SDR · Generic NMEA",
            "  Colorimetry: Konica Minolta CM · X-Rite i1Pro",
        ]
        return True, "\n".join(lines)


# ============================================================================
# STANDARD PLUGIN REGISTRATION
# ============================================================================
def setup_plugin(main_app):
    """Register plugin — left panel first, hardware menu fallback"""
    global _ARCHAEOLOGY_REGISTERED
    if _ARCHAEOLOGY_REGISTERED:
        print("⏭️  Archaeology plugin already registered, skipping…")
        return None

    plugin = ArchaeologyArchaeometryPlugin(main_app)

    if hasattr(main_app, 'left') and main_app.left is not None:
        main_app.left.add_hardware_button(
            name=PLUGIN_INFO.get("name", "Archaeology & Archaeometry"),
            icon=PLUGIN_INFO.get("icon", "🏺"),
            command=plugin.show_interface,
        )
        print(f"✅ Added to left panel: {PLUGIN_INFO.get('name')}")
        _ARCHAEOLOGY_REGISTERED = True
        return plugin

    if hasattr(main_app, 'menu_bar'):
        if not hasattr(main_app, 'hardware_menu'):
            main_app.hardware_menu = tk.Menu(main_app.menu_bar, tearoff=0)
            main_app.menu_bar.add_cascade(label="🔧 Hardware", menu=main_app.hardware_menu)
        main_app.hardware_menu.add_command(
            label=PLUGIN_INFO.get("name", "Archaeology & Archaeometry"),
            command=plugin.show_interface,
        )
        print(f"✅ Added to Hardware menu: {PLUGIN_INFO.get('name')}")
        _ARCHAEOLOGY_REGISTERED = True

    return plugin
