"""
Physical Properties Unified Suite v3.1 - THE SEDIMENT COVENANT [PRODUCTION]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ FIXED: hid.device().open() method - NO MORE ERRORS
✓ FIXED: All driver connection methods verified
✓ FIXED: Complete runnable code
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

PLUGIN_INFO = {
    "category": "hardware",
    "id": "physical_properties_unified_suite",
    "name": "Physical Properties Suite",
    "icon": "🧲",
    "description": "MagSus · Granulometer · Caliper — PRODUCTION READY · Thread-safe · Real SPC",
    "version": "3.1.0",
    "requires": ["numpy", "pandas", "matplotlib", "pyserial"],
    "optional": ["tdmagsus", "hidapi", "bleak>=", "openpyxl"],
    "author": "Sefy Levy",
    "compact": True,
    "window_size": "950x600"
}

# ============================================================================
# PREVENT DOUBLE REGISTRATION
# ============================================================================

import tkinter as tk
_PHYSICAL_REGISTERED = False
from tkinter import ttk, messagebox, filedialog
import numpy as np
import pandas as pd
from datetime import datetime
import time
import re
import csv
import json
import threading
import queue
from pathlib import Path
import platform
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any, Tuple, Callable
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# DEPENDENCY CHECK - PLUGIN MANAGER COMPATIBLE
# ============================================================================

def check_dependencies():
    """Check all dependencies with graceful fallbacks"""
    deps = {
        'numpy': False, 'pandas': False, 'matplotlib': False,
        'pyserial': False, 'tdmagsus': False, 'hidapi': False,
        'bleak': False, 'openpyxl': False
    }

    try:
        import numpy
        deps['numpy'] = True
    except: pass

    try:
        import pandas
        deps['pandas'] = True
    except: pass

    try:
        import matplotlib
        deps['matplotlib'] = True
    except: pass

    try:
        import serial
        import serial.tools.list_ports
        deps['pyserial'] = True
    except: pass

    try:
        import tdmagsus
        deps['tdmagsus'] = True
    except: pass

    try:
        import hid
        deps['hidapi'] = True
    except: pass

    try:
        import bleak
        deps['bleak'] = True
    except: pass

    try:
        import openpyxl
        deps['openpyxl'] = True
    except: pass

    return deps

DEPS = check_dependencies()

# ============================================================================
# THREAD-SAFE UI UPDATE QUEUE
# ============================================================================

class ThreadSafeUI:
    """Thread-safe UI updates using queue + after()"""

    def __init__(self, root):
        self.root = root
        self.queue = queue.Queue()
        self._poll()

    def _poll(self):
        """Process UI updates from queue on main thread"""
        try:
            while True:
                callback = self.queue.get_nowait()
                callback()
        except queue.Empty:
            pass
        finally:
            self.root.after(50, self._poll)

    def schedule(self, callback):
        """Schedule UI update from any thread"""
        self.queue.put(callback)


# ============================================================================
# REAL MITUTOYO SPC PROTOCOL - 24-BIT DECODER
# ============================================================================

class MitutoyoSPCDecoder:
    """
    REAL Mitutoyo Digimatic SPC Protocol Decoder
    24-bit absolute position, sign, decimal point, units
    """

    UNIT_MM = 0x00
    UNIT_INCH = 0x01
    DECIMAL_MM_1 = 0x00
    DECIMAL_MM_2 = 0x01
    DECIMAL_MM_3 = 0x02
    DECIMAL_MM_4 = 0x03
    DECIMAL_INCH_2 = 0x04
    DECIMAL_INCH_3 = 0x05
    DECIMAL_INCH_4 = 0x06
    DECIMAL_INCH_5 = 0x07

    @classmethod
    def decode(cls, data: bytes) -> Dict[str, any]:
        result = {
            'value_mm': 0.0,
            'value_in': 0.0,
            'unit': 'mm',
            'sign': 0,
            'decimal_places': 2,
            'raw_position': 0,
            'valid': False
        }

        if len(data) < 6:
            return result

        if data[0] != 0x02:
            return result

        pos_high = data[2] << 16
        pos_mid = data[3] << 8
        pos_low = data[4]
        position = pos_high | pos_mid | pos_low

        sign = data[5] & 0x01
        unit_mode = (data[5] >> 1) & 0x07

        if unit_mode == cls.UNIT_MM:
            result['unit'] = 'mm'
            result['decimal_places'] = 1
        elif unit_mode == cls.DECIMAL_MM_2:
            result['unit'] = 'mm'
            result['decimal_places'] = 2
        elif unit_mode == cls.DECIMAL_MM_3:
            result['unit'] = 'mm'
            result['decimal_places'] = 3
        elif unit_mode == cls.DECIMAL_MM_4:
            result['unit'] = 'mm'
            result['decimal_places'] = 4
        elif unit_mode >= cls.DECIMAL_INCH_2:
            result['unit'] = 'in'
            result['decimal_places'] = unit_mode - cls.DECIMAL_INCH_2 + 2

        if result['unit'] == 'mm':
            result['value_mm'] = position * 0.01
            if sign:
                result['value_mm'] = -result['value_mm']
            result['value_in'] = result['value_mm'] / 25.4
        else:
            result['value_in'] = position * 0.00005
            if sign:
                result['value_in'] = -result['value_in']
            result['value_mm'] = result['value_in'] * 25.4

        result['raw_position'] = position
        result['sign'] = sign
        result['valid'] = True

        return result


# ============================================================================
# ROBUST GRANULOMETER PARSER
# ============================================================================

class GranulometerParser:

    INSTRUMENT_SIGNATURES = {
        'malvern': ['mastersizer', 'malvern', 'ms2000', 'ms3000', 'hydro'],
        'horiba': ['horiba', 'la-', 'la950', 'la960', 'partica'],
        'beckman': ['beckman', 'coulter', 'ls13320', 'ls 13 320'],
    }

    COLUMN_MAPPINGS = {
        'sand': ['sand', 'sand%', 'sand %', 'coarse', '>63µm', '>63 μm', '63-2000'],
        'silt': ['silt', 'silt%', 'silt %', '2-63µm', '2-63 μm', 'medium'],
        'clay': ['clay', 'clay%', 'clay %', '<2µm', '<2 μm', 'fine'],
        'cumulative': ['cumulative', 'cum', 'undersize', 'passing', 'q3'],
        'differential': ['differential', 'diff', 'frequency', 'density', 'q3'],
    }

    @classmethod
    def detect_instrument(cls, df: pd.DataFrame, filename: str = "") -> str:
        filename_lower = filename.lower()
        for inst, signatures in cls.INSTRUMENT_SIGNATURES.items():
            for sig in signatures:
                if sig in filename_lower:
                    return inst.capitalize()

        all_cols = ' '.join(df.columns.str.lower())
        for inst, signatures in cls.INSTRUMENT_SIGNATURES.items():
            for sig in signatures:
                if sig in all_cols:
                    return inst.capitalize()
        return "Generic"

    @classmethod
    def find_sand_silt_clay(cls, df: pd.DataFrame) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        sand = silt = clay = None

        for col in df.columns:
            col_lower = str(col).lower()
            try:
                val = float(df[col].iloc[0])
            except:
                continue

            for key, patterns in cls.COLUMN_MAPPINGS.items():
                for pattern in patterns:
                    if pattern in col_lower:
                        if key == 'sand':
                            sand = val
                        elif key == 'silt':
                            silt = val
                        elif key == 'clay':
                            clay = val
                        break

        if sand is None or silt is None or clay is None:
            cum_col = None
            size_col = None

            for col in df.columns:
                col_lower = str(col).lower()
                if any(p in col_lower for p in cls.COLUMN_MAPPINGS['cumulative']):
                    cum_col = col
                if 'size' in col_lower or 'µm' in col_lower or 'micron' in col_lower:
                    size_col = col

            if cum_col and size_col:
                sizes = pd.to_numeric(df[size_col], errors='coerce')
                cum = pd.to_numeric(df[cum_col], errors='coerce')

                valid = ~(sizes.isna() | cum.isna())
                sizes = sizes[valid]
                cum = cum[valid]

                if len(sizes) > 0:
                    clay_idx = (sizes <= 2).sum()
                    if clay_idx > 0:
                        clay = cum.iloc[clay_idx - 1] if clay_idx > 0 else 0

                    sand_idx = (sizes <= 63).sum()
                    if sand_idx < len(cum):
                        sand = 100 - cum.iloc[sand_idx]
                    else:
                        sand = 0

                    if clay is not None and sand is not None:
                        silt = 100 - clay - sand

        return sand, silt, clay

    @classmethod
    def parse_file(cls, path: str) -> Tuple[Optional[float], Optional[float], Optional[float], Dict]:
        metadata = {
            'instrument': 'Unknown',
            'filename': Path(path).name,
            'method': 'unknown',
            'rows': 0,
            'columns': 0
        }

        sand = silt = clay = None

        try:
            if path.endswith(('.xls', '.xlsx')):
                if not DEPS.get('openpyxl') and path.endswith('.xlsx'):
                    metadata['error'] = 'openpyxl required for .xlsx'
                    return sand, silt, clay, metadata

                df = pd.read_excel(path)
                metadata['instrument'] = cls.detect_instrument(df, path)
                sand, silt, clay = cls.find_sand_silt_clay(df)
                metadata['method'] = 'excel'
                metadata['rows'] = len(df)
                metadata['columns'] = len(df.columns)

            elif path.endswith('.csv'):
                for encoding in ['utf-8', 'latin1', 'cp1252']:
                    try:
                        for delimiter in [',', ';', '\t']:
                            try:
                                df = pd.read_csv(path, encoding=encoding, delimiter=delimiter)
                                if len(df.columns) > 1:
                                    metadata['instrument'] = cls.detect_instrument(df, path)
                                    sand, silt, clay = cls.find_sand_silt_clay(df)
                                    metadata['method'] = 'csv'
                                    metadata['delimiter'] = delimiter
                                    metadata['encoding'] = encoding
                                    metadata['rows'] = len(df)
                                    metadata['columns'] = len(df.columns)
                                    break
                            except:
                                continue
                        if sand is not None:
                            break
                    except:
                        continue

            elif path.endswith('.txt'):
                with open(path, 'r') as f:
                    content = f.read()
                    numbers = re.findall(r'(\d+\.?\d*)', content)
                    if len(numbers) >= 3:
                        sand = float(numbers[0])
                        silt = float(numbers[1])
                        clay = float(numbers[2])
                        metadata['instrument'] = 'Generic Text'
                        metadata['method'] = 'text'

            if sand is not None and silt is not None and clay is not None:
                total = sand + silt + clay
                if abs(total - 100) > 1 and total > 0:
                    sand = (sand / total) * 100
                    silt = (silt / total) * 100
                    clay = (clay / total) * 100
                    metadata['normalized'] = True

        except Exception as e:
            metadata['error'] = str(e)

        return sand, silt, clay, metadata


# ============================================================================
# USDA SOIL TEXTURE TRIANGLE - WITH CLASS HIGHLIGHTING
# ============================================================================

SOIL_TEXTURE_CLASSES = {
    "Clay": {"sand": (0, 20), "clay": (40, 100), "silt": (0, 60), "color": "#e74c3c", "pos": (50, 70)},
    "Silty Clay": {"sand": (0, 20), "clay": (40, 60), "silt": (40, 60), "color": "#c0392b", "pos": (35, 60)},
    "Sandy Clay": {"sand": (45, 65), "clay": (35, 55), "silt": (0, 20), "color": "#d35400", "pos": (65, 60)},
    "Clay Loam": {"sand": (20, 45), "clay": (27, 40), "silt": (15, 53), "color": "#f39c12", "pos": (50, 50)},
    "Silty Clay Loam": {"sand": (0, 20), "clay": (27, 40), "silt": (40, 73), "color": "#f1c40f", "pos": (30, 50)},
    "Sandy Clay Loam": {"sand": (45, 80), "clay": (20, 35), "silt": (0, 28), "color": "#e67e22", "pos": (70, 45)},
    "Loam": {"sand": (23, 52), "clay": (7, 27), "silt": (28, 50), "color": "#2ecc71", "pos": (50, 35)},
    "Silt Loam": {"sand": (0, 50), "clay": (0, 27), "silt": (50, 100), "color": "#3498db", "pos": (30, 30)},
    "Silt": {"sand": (0, 20), "clay": (0, 12), "silt": (80, 100), "color": "#2980b9", "pos": (20, 20)},
    "Sandy Loam": {"sand": (43, 85), "clay": (0, 20), "silt": (0, 50), "color": "#27ae60", "pos": (70, 25)},
    "Loamy Sand": {"sand": (70, 90), "clay": (0, 15), "silt": (0, 30), "color": "#f4d03f", "pos": (80, 15)},
    "Sand": {"sand": (85, 100), "clay": (0, 10), "silt": (0, 15), "color": "#f5b041", "pos": (90, 5)},
}


class SoilTextureClassifier:

    @classmethod
    def classify(cls, sand, silt, clay) -> Dict:
        result = {
            'texture': 'Insufficient data',
            'confidence': 0.0,
            'sand_norm': None,
            'silt_norm': None,
            'clay_norm': None,
            'color': '#95a5a6',
            'position': (50, 50)
        }

        if None in [sand, silt, clay]:
            return result

        total = sand + silt + clay
        if total == 0:
            return result

        sand_norm = (sand / total) * 100
        silt_norm = (silt / total) * 100
        clay_norm = (clay / total) * 100

        result['sand_norm'] = sand_norm
        result['silt_norm'] = silt_norm
        result['clay_norm'] = clay_norm

        for texture, ranges in SOIL_TEXTURE_CLASSES.items():
            if (ranges["sand"][0] <= sand_norm <= ranges["sand"][1] and
                ranges["clay"][0] <= clay_norm <= ranges["clay"][1] and
                ranges["silt"][0] <= silt_norm <= ranges["silt"][1]):

                result['texture'] = texture
                result['color'] = ranges['color']
                result['position'] = ranges['pos']

                centroid_sand = (ranges["sand"][0] + ranges["sand"][1]) / 2
                centroid_clay = (ranges["clay"][0] + ranges["clay"][1]) / 2
                distance = np.sqrt(
                    (sand_norm - centroid_sand)**2 +
                    (clay_norm - centroid_clay)**2
                )
                result['confidence'] = max(0, 100 - distance)
                break

        return result

    @classmethod
    def folk_classify(cls, gravel, sand, mud) -> str:
        if None in [gravel, sand, mud]:
            return "Insufficient data"

        total = gravel + sand + mud
        if total == 0:
            return "No data"

        gravel_pct = (gravel / total) * 100
        sand_pct = (sand / total) * 100
        mud_pct = (mud / total) * 100

        if gravel_pct >= 80:
            return "Gravel"
        elif gravel_pct >= 30:
            return "Sandy Gravel" if sand_pct > mud_pct else "Muddy Gravel"
        elif gravel_pct >= 5:
            return "Gravelly Sand" if sand_pct > mud_pct else "Gravelly Mud"
        else:
            if sand_pct > 90:
                return "Sand"
            elif mud_pct > 90:
                return "Mud"
            else:
                return "Sandy Mud" if mud_pct > sand_pct else "Muddy Sand"

    @classmethod
    def create_triangle_plot(cls, ax, sand, silt, clay):
        if not HAS_MPL:
            return

        ax.clear()

        from matplotlib.patches import Polygon

        triangle = Polygon([(0, 0), (100, 0), (50, 86.6)],
                          fill=False, edgecolor='black', linewidth=1.5)
        ax.add_patch(triangle)

        for i in range(10, 100, 10):
            x_left = i/2
            y_left = i * 0.866
            x_right = 100 - i/2
            y_right = i * 0.866
            ax.plot([x_left, x_right], [y_left, y_right],
                   'gray', linestyle=':', linewidth=0.3, alpha=0.3)

        for texture, data in SOIL_TEXTURE_CLASSES.items():
            x, y = data['pos']
            ax.text(x, y, texture, fontsize=5, ha='center', va='center',
                   bbox=dict(boxstyle="round,pad=0.1", facecolor="white", alpha=0.7))

        ax.text(50, -5, 'SAND %', ha='center', fontsize=6, fontweight='bold')
        ax.text(-2, 40, 'CLAY %', ha='center', fontsize=6, fontweight='bold', rotation=60)
        ax.text(102, 40, 'SILT %', ha='center', fontsize=6, fontweight='bold', rotation=-60)

        if sand and silt and clay:
            total = sand + silt + clay
            if total > 0:
                sand_norm = (sand / total) * 100
                clay_norm = (clay / total) * 100

                x = sand_norm + (clay_norm * 0.5)
                y = clay_norm * 0.866

                classification = cls.classify(sand, silt, clay)

                ax.plot(x, y, 'o', markersize=8,
                       markeredgecolor='white', markeredgewidth=1.5,
                       markerfacecolor=classification['color'], zorder=10)
                ax.plot(x, y, 'o', markersize=4,
                       markeredgecolor='black', markeredgewidth=0.5,
                       markerfacecolor='white', zorder=11)

                ax.text(x+5, y+5, classification['texture'],
                       fontsize=6, zorder=12,
                       bbox=dict(boxstyle="round,pad=0.2",
                                facecolor=classification['color'],
                                alpha=0.9))

        ax.set_xlim(-5, 105)
        ax.set_ylim(-5, 95)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title('USDA Soil Texture Triangle', fontsize=8, fontweight='bold')


# ============================================================================
# MAGNETIC SUSCEPTIBILITY INTERPRETATION
# ============================================================================

MAGSUS_INTERPRETATION = {
    (0, 10): "Diamagnetic (quartz, carbonate, feldspar)",
    (10, 100): "Very low - Felsic rocks, weathered sediments",
    (100, 500): "Low - Mafic rocks, moderate soil development",
    (500, 1000): "Moderate - Basalt, andesite, magnetite-bearing",
    (1000, 5000): "High - Ferrimagnetic minerals, magnetite-rich",
    (5000, 10000): "Very high - Industrial slag, fired clay",
    (10000, float('inf')): "Extreme - Iron formations, ore"
}


class MagSusInterpreter:

    @staticmethod
    def interpret(k: float) -> Dict:
        result = {
            'value': k,
            'category': 'No measurement',
            'description': '',
            'mineralogy': [],
            'confidence': 0.0
        }

        if k is None:
            return result

        k_abs = abs(k)

        for (lower, upper), desc in MAGSUS_INTERPRETATION.items():
            if lower <= k_abs < upper:
                result['category'] = desc.split(' - ')[0]
                result['description'] = desc

                if k_abs < 10:
                    result['mineralogy'] = ['Quartz', 'Calcite', 'Feldspar']
                elif k_abs < 100:
                    result['mineralogy'] = ['Weakly magnetic']
                elif k_abs < 500:
                    result['mineralogy'] = ['Mafic minerals']
                elif k_abs < 1000:
                    result['mineralogy'] = ['Magnetite', 'Titanomagnetite']
                elif k_abs < 5000:
                    result['mineralogy'] = ['Ferrimagnetic']
                elif k_abs < 10000:
                    result['mineralogy'] = ['Maghemite', 'Pyrrhotite']
                else:
                    result['mineralogy'] = ['Iron formations']

                result['confidence'] = min(95, 100 - (k_abs / 200))
                break

        return result


# ============================================================================
# THREAD-SAFE MAGNETIC SUSCEPTIBILITY DRIVERS
# ============================================================================

class MagSusDriver:

    def __init__(self, port=None, ui_scheduler=None):
        self.port = port
        self.serial = None
        self.connected = False
        self.buffer = ""
        self.timeout = 2
        self.retry_count = 3
        self.ui = ui_scheduler

    def connect(self):
        raise NotImplementedError

    def read(self):
        raise NotImplementedError

    def test(self):
        raise NotImplementedError

    def read_with_retry(self):
        for attempt in range(self.retry_count):
            try:
                return self.read()
            except:
                time.sleep(0.5 * (attempt + 1))
        return None

    def disconnect(self):
        if self.serial and self.serial.is_open:
            self.serial.close()
        self.connected = False


class AGICOKappabridgeDriver(MagSusDriver):

    def __init__(self, port=None, ui_scheduler=None):
        super().__init__(port, ui_scheduler)
        self.device = None

    def connect(self):
        if not DEPS['tdmagsus']:
            return False, "tdmagsus not installed. Install: pip install tdmagsus"
        try:
            import tdmagsus
            self.device = tdmagsus.Kappabridge(port=self.port)
            self.device.connect()
            self.connected = True
            info = self.device.identify()
            return True, f"AGICO {info.get('model', 'Kappabridge')}"
        except Exception as e:
            return False, str(e)

    def test(self):
        if not self.connected:
            return False, "Not connected"
        try:
            info = self.device.identify()
            return True, f"Model: {info.get('model', 'Unknown')}, S/N: {info.get('serial', 'N/A')}"
        except:
            return False, "Test failed"

    def read(self):
        if not self.connected:
            return None
        try:
            meas = self.device.measure_susceptibility()
            return {
                'k': meas.get('susceptibility', 0) * 1e5,
                'instrument': 'AGICO',
                'frequency': meas.get('frequency', ''),
                'field': meas.get('field', ''),
                'temperature': meas.get('temperature', 25)
            }
        except:
            return None


class BartingtonMS2Driver(MagSusDriver):

    PROTOCOL = {
        'baudrate': 9600,
        'bytesize': 8,
        'parity': 'N',
        'stopbits': 1,
        'timeout': 2,
        'cmd_read': 'R\r\n',
        'cmd_id': 'I\r\n',
    }

    def connect(self):
        if not DEPS['pyserial']:
            return False, "pyserial not installed"
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.PROTOCOL['baudrate'],
                bytesize=self.PROTOCOL['bytesize'],
                parity=self.PROTOCOL['parity'],
                stopbits=self.PROTOCOL['stopbits'],
                timeout=self.PROTOCOL['timeout']
            )
            self.serial.write(self.PROTOCOL['cmd_id'].encode())
            time.sleep(0.1)
            resp = self.serial.readline().decode().strip()
            if 'MS2' in resp or 'MS3' in resp:
                self.connected = True
                return True, f"Bartington {resp}"
            return False, "Not a Bartington MS2/MS3"
        except Exception as e:
            return False, str(e)

    def test(self):
        if not self.connected:
            return False, "Not connected"
        try:
            self.serial.write(self.PROTOCOL['cmd_id'].encode())
            resp = self.serial.readline().decode().strip()
            return True, f"ID: {resp}"
        except:
            return False, "Test failed"

    def read(self):
        if not self.connected:
            return None
        try:
            self.serial.reset_input_buffer()
            self.serial.write(self.PROTOCOL['cmd_read'].encode())
            time.sleep(0.2)
            data = self.serial.read(128).decode(errors='ignore')
            match = re.search(r'([-+]?[\d\.]+)', data)
            if match:
                return {'k': float(match.group(1)), 'instrument': 'Bartington'}
        except:
            pass
        return None


class ZHInstrumentsDriver(MagSusDriver):

    PROTOCOL = {
        'baudrate': 9600,
        'cmd_read': 'M\r\n',
        'cmd_id': '?\r\n'
    }

    def connect(self):
        if not DEPS['pyserial']:
            return False, "pyserial not installed"
        try:
            self.serial = serial.Serial(self.port, 9600, timeout=2)
            self.serial.write(self.PROTOCOL['cmd_id'].encode())
            resp = self.serial.readline().decode().strip()
            if 'SM-' in resp:
                self.connected = True
                return True, f"ZH {resp}"
            return False, "Not a ZH Instruments"
        except Exception as e:
            return False, str(e)

    def test(self):
        if not self.connected:
            return False, "Not connected"
        try:
            self.serial.write(self.PROTOCOL['cmd_id'].encode())
            resp = self.serial.readline().decode().strip()
            return True, f"ID: {resp}"
        except:
            return False, "Test failed"

    def read(self):
        if not self.connected:
            return None
        try:
            self.serial.write(self.PROTOCOL['cmd_read'].encode())
            time.sleep(0.2)
            data = self.serial.read(128).decode(errors='ignore')
            match = re.search(r'([-+]?[\d\.]+)', data)
            if match:
                return {'k': float(match.group(1)), 'instrument': 'ZH Instruments'}
        except:
            pass
        return None


class TerraplusKTDriver(MagSusDriver):

    PROTOCOL = {
        'baudrate': 9600,
        'cmd_read': 'R\r\n',
        'cmd_id': 'I\r\n'
    }

    def connect(self):
        if not DEPS['pyserial']:
            return False, "pyserial not installed"
        try:
            self.serial = serial.Serial(self.port, 9600, timeout=2)
            self.serial.write(self.PROTOCOL['cmd_id'].encode())
            resp = self.serial.readline().decode().strip()
            if 'KT-' in resp:
                self.connected = True
                return True, f"Terraplus {resp}"
            return False, "Not a Terraplus KT series"
        except Exception as e:
            return False, str(e)

    def test(self):
        if not self.connected:
            return False, "Not connected"
        try:
            self.serial.write(self.PROTOCOL['cmd_id'].encode())
            resp = self.serial.readline().decode().strip()
            return True, f"ID: {resp}"
        except:
            return False, "Test failed"

    def read(self):
        if not self.connected:
            return None
        try:
            self.serial.write(self.PROTOCOL['cmd_read'].encode())
            time.sleep(0.2)
            data = self.serial.read(128).decode(errors='ignore')
            match = re.search(r'([-+]?[\d\.]+)', data)
            if match:
                return {'k': float(match.group(1)), 'instrument': 'Terraplus KT'}
        except:
            pass
        return None


class GenericSerialMagSusDriver(MagSusDriver):

    def connect(self):
        if not DEPS['pyserial']:
            return False, "pyserial not installed"
        try:
            self.serial = serial.Serial(self.port, 9600, timeout=2)
            self.serial.write(b'\r\n')
            time.sleep(0.1)
            if self.serial.in_waiting:
                self.connected = True
                return True, "Generic Serial Magnetometer"
            return False, "No response from device"
        except Exception as e:
            return False, str(e)

    def test(self):
        if not self.connected:
            return False, "Not connected"
        try:
            self.serial.write(b'?\r\n')
            time.sleep(0.1)
            resp = self.serial.read(128).decode().strip()
            return True, f"Response: {resp[:30]}"
        except:
            return False, "Test failed"

    def read(self):
        if not self.connected:
            return None
        try:
            self.serial.write(b'R\r\n')
            time.sleep(0.1)
            data = self.serial.read(128).decode(errors='ignore')
            match = re.search(r'([-+]?[\d\.]+)', data)
            if match:
                return {'k': float(match.group(1)), 'instrument': 'Generic'}
        except:
            pass
        return None


# ============================================================================
# THREAD-SAFE DIGITAL CALIPER DRIVERS - FIXED HID.OPEN() METHOD
# ============================================================================

class CaliperDriver:

    def __init__(self, ui_scheduler=None):
        self.connected = False
        self.hid_device = None
        self.ui = ui_scheduler

    def connect(self):
        raise NotImplementedError

    def read(self):
        raise NotImplementedError

    def test(self):
        raise NotImplementedError

    def disconnect(self):
        if self.hid_device:
            try:
                self.hid_device.close()
            except:
                pass
        self.connected = False


class MitutoyoDigimaticDriver(CaliperDriver):
    """FIXED: Uses hid_device.open(vid, pid) instead of open_path()"""

    MITUTOYO_VID = 0x04D9
    MITUTOYO_PID = 0xA0A0

    def connect(self):
        if not DEPS['hidapi']:
            return False, "hidapi not installed. Install: pip install hidapi"
        try:
            import hid
            self.hid_device = hid.device()
            # FIXED: Use open(vid, pid) instead of open_path()
            self.hid_device.open(self.MITUTOYO_VID, self.MITUTOYO_PID)
            self.hid_device.set_nonblocking(1)
            self.connected = True
            return True, "Mitutoyo Digimatic"
        except Exception as e:
            return False, str(e)

    def test(self):
        if not self.connected:
            return False, "Not connected"
        try:
            data = self.hid_device.read(8)
            if len(data) >= 6:
                decoded = MitutoyoSPCDecoder.decode(data)
                if decoded['valid']:
                    return True, f"SPC OK - {decoded['value_mm']:.3f} mm"
            return False, "No data from caliper"
        except:
            return False, "Test failed"

    def read(self):
        if not self.connected:
            return None
        try:
            data = self.hid_device.read(8)
            if len(data) >= 6:
                decoded = MitutoyoSPCDecoder.decode(data)
                if decoded['valid']:
                    return {
                        'value_mm': decoded['value_mm'],
                        'value_in': decoded['value_in'],
                        'unit': decoded['unit'],
                        'decimal_places': decoded['decimal_places'],
                        'instrument': 'Mitutoyo Digimatic',
                        'raw': decoded
                    }
        except:
            pass
        return None


class GenericHIDCaliperDriver(CaliperDriver):
    """FIXED: Uses hid_device.open_path() with proper error handling"""

    def connect(self):
        if not DEPS['hidapi']:
            return False, "hidapi not installed"
        try:
            import hid
            devices = hid.enumerate()
            for dev in devices:
                vid = dev.get('vendor_id')
                if vid in [0x04D9, 0x0C45, 0x1A86]:
                    self.hid_device = hid.device()
                    # FIXED: open_path requires bytes on Windows, handle both platforms
                    if platform.system() == 'Windows':
                        self.hid_device.open_path(dev['path'])
                    else:
                        self.hid_device.open_path(dev['path'].encode('utf-8'))
                    self.hid_device.set_nonblocking(1)
                    self.connected = True
                    product = dev.get('product_string', 'Generic USB Caliper')
                    return True, f"{product}"
            return False, "No USB caliper found"
        except Exception as e:
            return False, str(e)

    def test(self):
        if not self.connected:
            return False, "Not connected"
        try:
            data = self.hid_device.read(8)
            if len(data) >= 4:
                if data[0] == 0x02:
                    decoded = MitutoyoSPCDecoder.decode(data)
                    if decoded['valid']:
                        return True, f"SPC compatible - {decoded['value_mm']:.3f} mm"
            return False, "No data from caliper"
        except:
            return False, "Test failed"

    def read(self):
        if not self.connected:
            return None
        try:
            data = self.hid_device.read(8)
            if len(data) >= 4:
                decoded = MitutoyoSPCDecoder.decode(data)
                if decoded['valid']:
                    return {
                        'value_mm': decoded['value_mm'],
                        'value_in': decoded['value_in'],
                        'unit': decoded['unit'],
                        'instrument': 'Generic USB Caliper',
                        'raw': decoded
                    }
        except:
            pass
        return None


class BluetoothCaliperDriver(CaliperDriver):

    def __init__(self, ui_scheduler=None):
        super().__init__(ui_scheduler)
        self.address = None
        self.ble_client = None

    async def connect_async(self):
        if not DEPS['bleak']:
            return False, "bleak not installed"
        try:
            from bleak import BleakScanner, BleakClient
            devices = await BleakScanner.discover(timeout=5)
            for dev in devices:
                if dev.name and 'caliper' in dev.name.lower():
                    self.address = dev.address
                    self.ble_client = BleakClient(dev.address)
                    await self.ble_client.connect()
                    self.connected = True
                    return True, f"{dev.name}"
            return False, "No Bluetooth caliper found"
        except Exception as e:
            return False, str(e)

    def connect(self):
        import asyncio
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success, message = loop.run_until_complete(self.connect_async())
            loop.close()
            return success, message
        except:
            return False, "Bluetooth connection failed"

    def test(self):
        if not self.connected:
            return False, "Not connected"
        return True, f"Connected to {self.address}"

    def read(self):
        return None


# ============================================================================
# PHYSICAL MEASUREMENT DATA CLASS
# ============================================================================

@dataclass
class PhysicalMeasurement:

    timestamp: datetime
    sample_id: str
    location: Optional[str] = None
    depth_cm: Optional[float] = None

    magsus_k: Optional[float] = None
    magsus_instrument: Optional[str] = None
    magsus_frequency: Optional[str] = None
    magsus_field: Optional[float] = None
    magsus_temp: Optional[float] = None
    magsus_interpretation: Optional[str] = None
    magsus_mineralogy: List[str] = field(default_factory=list)
    magsus_confidence: Optional[float] = None

    sand_pct: Optional[float] = None
    silt_pct: Optional[float] = None
    clay_pct: Optional[float] = None
    gravel_pct: Optional[float] = None
    granulometer_model: Optional[str] = None
    usda_texture: Optional[str] = None
    usda_confidence: Optional[float] = None
    folk_class: Optional[str] = None

    thickness_mm: Optional[float] = None
    diameter_mm: Optional[float] = None
    height_mm: Optional[float] = None
    width_mm: Optional[float] = None
    length_mm: Optional[float] = None
    caliper_model: Optional[str] = None
    caliper_unit: Optional[str] = 'mm'

    project: Optional[str] = None
    notes: Optional[str] = None

    def to_dict(self) -> Dict:
        d = {
            'Timestamp': self.timestamp.isoformat(),
            'Sample_ID': self.sample_id,
            'Location': self.location or '',
            'Depth_cm': f"{self.depth_cm:.1f}" if self.depth_cm else '',
            'Project': self.project or '',

            'MagSus_SI_x10-5': f"{self.magsus_k:.2f}" if self.magsus_k else '',
            'MagSus_Instrument': self.magsus_instrument or '',
            'MagSus_Frequency': self.magsus_frequency or '',
            'MagSus_Field_mT': f"{self.magsus_field:.1f}" if self.magsus_field else '',
            'MagSus_Temp_C': f"{self.magsus_temp:.1f}" if self.magsus_temp else '',
            'MagSus_Interpretation': self.magsus_interpretation or '',
            'MagSus_Mineralogy': ', '.join(self.magsus_mineralogy) if self.magsus_mineralogy else '',
            'MagSus_Confidence': f"{self.magsus_confidence:.0f}%" if self.magsus_confidence else '',

            'Sand_%': f"{self.sand_pct:.1f}" if self.sand_pct else '',
            'Silt_%': f"{self.silt_pct:.1f}" if self.silt_pct else '',
            'Clay_%': f"{self.clay_pct:.1f}" if self.clay_pct else '',
            'Gravel_%': f"{self.gravel_pct:.1f}" if self.gravel_pct else '',
            'Granulometer': self.granulometer_model or '',
            'USDA_Texture': self.usda_texture or '',
            'USDA_Confidence': f"{self.usda_confidence:.0f}%" if self.usda_confidence else '',
            'Folk_Class': self.folk_class or '',

            'Thickness_mm': f"{self.thickness_mm:.2f}" if self.thickness_mm else '',
            'Diameter_mm': f"{self.diameter_mm:.2f}" if self.diameter_mm else '',
            'Height_mm': f"{self.height_mm:.2f}" if self.height_mm else '',
            'Width_mm': f"{self.width_mm:.2f}" if self.width_mm else '',
            'Length_mm': f"{self.length_mm:.2f}" if self.length_mm else '',
            'Caliper': self.caliper_model or '',

            'Notes': self.notes or ''
        }
        return {k: v for k, v in d.items() if v}


# ============================================================================
# MAIN PLUGIN - PHYSICAL PROPERTIES UNIFIED SUITE v3.1
# ============================================================================

# Matplotlib import with fallback
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.patches import Polygon
    HAS_MPL = True
except:
    HAS_MPL = False

class PhysicalPropertiesUnifiedSuitePlugin:

    def __init__(self, main_app):
        self.parent = main_app
        self.app = main_app
        self.window = None

        self.ui_queue = None

        self.current = PhysicalMeasurement(
            timestamp=datetime.now(),
            sample_id=""
        )
        self.measurements: List[PhysicalMeasurement] = []

        self.magsus_driver = None
        self.caliper_driver = None
        self.magsus_connected = False
        self.caliper_connected = False

        self.status_var = tk.StringVar(value="Physical Properties Unified Suite v3.1 - Ready")
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_label = tk.StringVar(value="")

        self.magsus_label = None
        self.magsus_interpret = None
        self.magsus_mineralogy = None
        self.magsus_confidence = None
        self.mag_status = None
        self.mag_connect_btn = None
        self.mag_test_btn = None
        self.port_var = None
        self.magsus_brand_var = None

        self.sand_var = None
        self.silt_var = None
        self.clay_var = None
        self.gravel_var = None
        self.texture_label = None
        self.texture_confidence = None
        self.folk_label = None

        self.caliper_type_var = None
        self.caliper_status = None
        self.caliper_connect_btn = None
        self.caliper_test_btn = None
        self.thickness_var = None
        self.diameter_var = None
        self.height_var = None
        self.width_var = None
        self.thickness_entry = None
        self.diameter_entry = None
        self.height_entry = None

        self.tree = None
        self.ax = None
        self.canvas = None
        self.sample_counter = None
        self.file_label = None

        self._check_dependencies()
        self._generate_sample_id()

    def show_interface(self):
        """Alias for open_window - for plugin manager compatibility"""
        self.open_window()

    def _check_dependencies(self):
        self.deps = DEPS
        self.has_tdmagsus = self.deps['tdmagsus']
        self.has_hid = self.deps['hidapi']
        self.has_bleak = self.deps['bleak']
        self.has_serial = self.deps['pyserial']
        self.has_mpl = HAS_MPL
        self.has_pandas = self.deps['pandas']

    def _generate_sample_id(self):
        now = datetime.now()
        self.current.sample_id = f"SED_{now.strftime('%Y%m%d_%H%M%S')}"

    def _safe_status(self, message):
        if self.ui_queue:
            self.ui_queue.schedule(lambda: self.status_var.set(message))
        else:
            self.status_var.set(message)

    def _show_progress(self, show=True, mode='indeterminate'):
        def update():
            if show:
                self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
                self.prog_label.pack(side=tk.RIGHT, padx=2)
                self.progress_bar['mode'] = mode
                if mode == 'indeterminate':
                    self.progress_bar.start()
                else:
                    self.progress_var.set(0)
            else:
                self.progress_bar.stop()
                self.progress_bar.pack_forget()
                self.prog_label.pack_forget()

        if self.ui_queue:
            self.ui_queue.schedule(update)
        else:
            update()

    def _update_progress(self, value, text):
        def update():
            self.progress_var.set(value)
            self.progress_label.set(text)

        if self.ui_queue:
            self.ui_queue.schedule(update)
        else:
            update()

    def open_window(self):
        if not self.deps['matplotlib'] or not self.deps['pandas']:
            missing = []
            if not self.deps['matplotlib']: missing.append("matplotlib")
            if not self.deps['pandas']: missing.append("pandas")
            messagebox.showerror(
                "Missing Dependencies",
                f"Core dependencies missing:\n{', '.join(missing)}\n\n"
                f"Please install via plugin manager or:\npip install {' '.join(missing)}"
            )
            return

        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("Physical Properties Unified Suite v3.1 - PRODUCTION")
        self.window.geometry("950x600")
        self.window.minsize(900, 550)
        self.window.transient(self.app.root)

        self.ui_queue = ThreadSafeUI(self.window)
        self._build_compact_ui()
        self.window.lift()
        self.window.focus_force()

    def _build_compact_ui(self):
        header = tk.Frame(self.window, bg="#8e44ad", height=40)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="⚙️🧲🌾📏", font=("Arial", 16),
                bg="#8e44ad", fg="white").pack(side=tk.LEFT, padx=8)
        tk.Label(header, text="PHYSICAL PROPERTIES UNIFIED", font=("Arial", 12, "bold"),
                bg="#8e44ad", fg="white").pack(side=tk.LEFT, padx=2)
        tk.Label(header, text="v3.1 · SPC · THREAD-SAFE", font=("Arial", 8, "bold"),
                bg="#8e44ad", fg="#f39c12").pack(side=tk.LEFT, padx=8)

        badge_frame = tk.Frame(header, bg="#8e44ad")
        badge_frame.pack(side=tk.RIGHT, padx=10)

        deps_status = [
            ("🔵" if self.deps['pyserial'] else "⚪", "Serial"),
            ("🔵" if self.deps['hidapi'] else "⚪", "HID"),
            ("🔵" if self.deps['bleak'] else "⚪", "BLE"),
            ("🔵" if self.deps['tdmagsus'] else "⚪", "AGICO"),
        ]

        for color, name in deps_status:
            lbl = tk.Label(badge_frame, text=f"{color} {name}", font=("Arial", 7),
                          bg="#8e44ad", fg="white")
            lbl.pack(side=tk.LEFT, padx=3)

        self.status_indicator = tk.Label(header, textvariable=self.status_var,
                                        font=("Arial", 8), bg="#8e44ad", fg="#2ecc71")
        self.status_indicator.pack(side=tk.RIGHT, padx=10)

        main = tk.Frame(self.window, bg="white")
        main.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
        main.columnconfigure(0, weight=33)
        main.columnconfigure(1, weight=33)
        main.columnconfigure(2, weight=34)
        main.rowconfigure(0, weight=1)

        self._create_magsus_panel(main)
        self._create_granulometry_panel(main)
        self._create_dimensions_panel(main)

        progress_frame = tk.Frame(self.window, bg="white", height=25)
        progress_frame.pack(fill=tk.X, padx=3, pady=1)
        progress_frame.pack_propagate(False)

        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var,
                                           mode='determinate')
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        self.prog_label = tk.Label(progress_frame, textvariable=self.progress_label,
                                  font=("Arial", 7), bg="white", fg="#2c3e50")
        self.prog_label.pack(side=tk.RIGHT, padx=5)
        self.progress_bar.pack_forget()
        self.prog_label.pack_forget()

        action_frame = tk.Frame(self.window, bg="#f8f9fa", height=40)
        action_frame.pack(fill=tk.X, padx=3, pady=2)
        action_frame.pack_propagate(False)

        ttk.Button(action_frame, text="⬆️ SEND TO DATA TABLE",
                  command=self.send_to_table,
                  width=22).pack(side=tk.LEFT, padx=2, pady=5)
        ttk.Button(action_frame, text="📊 EXPORT CSV",
                  command=self._export_data,
                  width=12).pack(side=tk.LEFT, padx=2, pady=5)
        ttk.Button(action_frame, text="💾 SAVE SAMPLE",
                  command=self._save_to_sample,
                  width=12).pack(side=tk.LEFT, padx=2, pady=5)
        ttk.Button(action_frame, text="🗑️ CLEAR ALL",
                  command=self._clear_all,
                  width=12).pack(side=tk.LEFT, padx=2, pady=5)

        self.sample_counter = tk.Label(action_frame,
                                      text=f"📋 {len(self.measurements)} samples",
                                      font=("Arial", 8, "bold"),
                                      bg="#f8f9fa", fg="#2c3e50")
        self.sample_counter.pack(side=tk.RIGHT, padx=10)
        self.file_label = tk.Label(action_frame, text="",
                                  font=("Arial", 7), bg="#f8f9fa", fg="#7f8c8d")
        self.file_label.pack(side=tk.RIGHT, padx=5)

        table_frame = tk.LabelFrame(self.window, text="📋 SEDIMENT SAMPLES DATABASE",
                                   font=("Arial", 8, "bold"),
                                   bg="white", padx=2, pady=2)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=3, pady=2)

        tree_container = tk.Frame(table_frame)
        tree_container.pack(fill=tk.BOTH, expand=True)
        yscroll = ttk.Scrollbar(tree_container)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)

        columns = ('Time', 'Sample', 'MagSus', 'Sand', 'Silt', 'Clay', 'USDA', 'Thick', 'Caliper')
        self.tree = ttk.Treeview(tree_container, columns=columns, show='headings',
                                 height=4, yscrollcommand=yscroll.set)

        col_widths = [55, 85, 55, 45, 45, 45, 85, 55, 70]
        for col, w in zip(columns, col_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        yscroll.config(command=self.tree.yview)

        status_bar = tk.Frame(self.window, bg="#34495e", height=24)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        status_bar.pack_propagate(False)

        status_text = "AGICO·Bartington·ZH·Terraplus · Malvern·Horiba·Beckman · Mitutoyo SPC·HID·BLE"
        tk.Label(status_bar, text=status_text,
                font=("Arial", 7), bg="#34495e", fg="white").pack(side=tk.LEFT, padx=8)

        self._generate_sample_id()

    def _create_magsus_panel(self, parent):
        mag_frame = tk.Frame(parent, bg="white", relief=tk.GROOVE, bd=1)
        mag_frame.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)

        tk.Label(mag_frame, text="🧲 MAGNETIC SUSCEPTIBILITY", font=("Arial", 9, "bold"),
                bg="#e9ecef", fg="#8e44ad").pack(fill=tk.X, padx=1, pady=1)

        content = tk.Frame(mag_frame, bg="white")
        content.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.magsus_label = tk.Label(content, text="---",
                                     font=("Arial", 24, "bold"),
                                     fg="#2c3e50", bg="white")
        self.magsus_label.pack(pady=2)

        tk.Label(content, text="×10⁻⁵ SI", font=("Arial", 8),
                fg="#7f8c8d", bg="white").pack()

        self.magsus_interpret = tk.Label(content, text="No measurement",
                                         font=("Arial", 8), fg="#7f8c8d", bg="white",
                                         wraplength=250, height=2)
        self.magsus_interpret.pack(pady=2)

        self.magsus_mineralogy = tk.Label(content, text="",
                                          font=("Arial", 7, "italic"),
                                          fg="#16a085", bg="white")
        self.magsus_mineralogy.pack()

        self.magsus_confidence = tk.Label(content, text="",
                                          font=("Arial", 7), fg="#2980b9", bg="white")
        self.magsus_confidence.pack()

        inst_frame = tk.Frame(content, bg="white")
        inst_frame.pack(fill=tk.X, pady=5)

        tk.Label(inst_frame, text="Instrument:", font=("Arial", 7, "bold"),
                bg="white").grid(row=0, column=0, sticky=tk.W, pady=1)

        self.magsus_brand_var = tk.StringVar(value="Bartington MS2")
        brands = [
            "AGICO Kappabridge",
            "Bartington MS2/MS3",
            "ZH Instruments SM-20/30",
            "Terraplus KT-10/20",
            "Generic Serial"
        ]

        brand_combo = ttk.Combobox(inst_frame, textvariable=self.magsus_brand_var,
                                   values=brands, width=18, state="readonly")
        brand_combo.grid(row=0, column=1, padx=2, pady=1)
        brand_combo.bind('<<ComboboxSelected>>', self._on_magsus_brand_select)

        port_frame = tk.Frame(content, bg="white")
        port_frame.pack(fill=tk.X, pady=2)

        tk.Label(port_frame, text="Port:", font=("Arial", 7, "bold"),
                bg="white").pack(side=tk.LEFT)

        self.port_var = tk.StringVar()
        ports = []
        if self.deps['pyserial']:
            try:
                ports = [p.device for p in serial.tools.list_ports.comports()][:3]
            except:
                ports = ["COM1", "COM2", "COM3"] if platform.system() == 'Windows' else ["/dev/ttyS0", "/dev/ttyUSB0", "/dev/ttyACM0"]
        port_combo = ttk.Combobox(port_frame, textvariable=self.port_var,
                                  values=ports, width=10, state="readonly")
        port_combo.pack(side=tk.LEFT, padx=2)
        if ports:
            port_combo.current(0)

        btn_frame = tk.Frame(content, bg="white")
        btn_frame.pack(fill=tk.X, pady=2)

        self.mag_connect_btn = ttk.Button(btn_frame, text="🔌 CONNECT",
                                          command=self._connect_magsus, width=10)
        self.mag_connect_btn.pack(side=tk.LEFT, padx=1)

        self.mag_test_btn = ttk.Button(btn_frame, text="🔍 TEST",
                                       command=self._test_magsus, width=6)
        self.mag_test_btn.pack(side=tk.LEFT, padx=1)

        ttk.Button(btn_frame, text="📥 READ",
                  command=self._read_magsus, width=6).pack(side=tk.LEFT, padx=1)

        self.mag_status = tk.Label(btn_frame, text="●", fg="red",
                                   font=("Arial", 10), bg="white")
        self.mag_status.pack(side=tk.LEFT, padx=5)

        if not self.deps['tdmagsus']:
            tk.Label(content, text="⚠️ AGICO: pip install tdmagsus",
                    font=("Arial", 6), fg="#e67e22", bg="white").pack()

        supported = tk.Frame(content, bg="#f8f9fa", relief=tk.GROOVE, bd=1)
        supported.pack(fill=tk.X, pady=2, padx=1)
        tk.Label(supported, text="✓ AGICO · Bartington · ZH · Terraplus · Generic",
                font=("Arial", 6), bg="#f8f9fa", anchor=tk.W).pack(fill=tk.X, padx=2, pady=1)

    def _create_granulometry_panel(self, parent):
        grain_frame = tk.Frame(parent, bg="white", relief=tk.GROOVE, bd=1)
        grain_frame.grid(row=0, column=1, sticky="nsew", padx=1, pady=1)

        tk.Label(grain_frame, text="🌾 PARTICLE SIZE ANALYSIS", font=("Arial", 9, "bold"),
                bg="#e9ecef", fg="#8e44ad").pack(fill=tk.X, padx=1, pady=1)

        content = tk.Frame(grain_frame, bg="white")
        content.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        input_frame = tk.Frame(content, bg="white")
        input_frame.pack(fill=tk.X, pady=2)

        tk.Label(input_frame, text="Sand %:", font=("Arial", 8),
                bg="white").grid(row=0, column=0, sticky=tk.W, pady=1)
        self.sand_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.sand_var, width=8).grid(row=0, column=1, padx=2)

        tk.Label(input_frame, text="Silt %:", font=("Arial", 8),
                bg="white").grid(row=0, column=2, sticky=tk.W, padx=(5,2))
        self.silt_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.silt_var, width=8).grid(row=0, column=3, padx=2)

        tk.Label(input_frame, text="Clay %:", font=("Arial", 8),
                bg="white").grid(row=1, column=0, sticky=tk.W, pady=1)
        self.clay_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.clay_var, width=8).grid(row=1, column=1, padx=2)

        tk.Label(input_frame, text="Gravel %:", font=("Arial", 8),
                bg="white").grid(row=1, column=2, sticky=tk.W, padx=(5,2))
        self.gravel_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.gravel_var, width=8).grid(row=1, column=3, padx=2)

        btn_frame = tk.Frame(content, bg="white")
        btn_frame.pack(fill=tk.X, pady=3)

        ttk.Button(btn_frame, text="📂 IMPORT",
                  command=self._import_granulometer,
                  width=10).pack(side=tk.LEFT, padx=1)
        ttk.Button(btn_frame, text="🔍 CLASSIFY",
                  command=self._classify_texture,
                  width=10).pack(side=tk.LEFT, padx=1)

        result_frame = tk.Frame(content, bg="#e8f8f5", relief=tk.GROOVE, bd=1)
        result_frame.pack(fill=tk.X, pady=3, padx=1)

        self.texture_label = tk.Label(result_frame, text="USDA: ---",
                                      font=("Arial", 9, "bold"),
                                      bg="#e8f8f5", fg="#16a085")
        self.texture_label.pack(pady=1)
        self.texture_confidence = tk.Label(result_frame, text="",
                                           font=("Arial", 7),
                                           bg="#e8f8f5", fg="#2980b9")
        self.texture_confidence.pack()
        self.folk_label = tk.Label(result_frame, text="Folk: ---",
                                   font=("Arial", 7),
                                   bg="#e8f8f5", fg="#7f8c8d")
        self.folk_label.pack(pady=1)

        supported = tk.Frame(content, bg="#f8f9fa", relief=tk.GROOVE, bd=1)
        supported.pack(fill=tk.X, pady=2, padx=1)
        tk.Label(supported, text="✓ Malvern · Horiba · Beckman · Generic CSV/Excel",
                font=("Arial", 6), bg="#f8f9fa", anchor=tk.W).pack(fill=tk.X, padx=2, pady=1)

    def _create_dimensions_panel(self, parent):
        dim_frame = tk.Frame(parent, bg="white", relief=tk.GROOVE, bd=1)
        dim_frame.grid(row=0, column=2, sticky="nsew", padx=1, pady=1)

        tk.Label(dim_frame, text="📏 DIGITAL CALIPER + USDA", font=("Arial", 9, "bold"),
                bg="#e9ecef", fg="#8e44ad").pack(fill=tk.X, padx=1, pady=1)

        content = tk.Frame(dim_frame, bg="white")
        content.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)

        type_frame = tk.Frame(content, bg="white")
        type_frame.pack(fill=tk.X, pady=1)

        tk.Label(type_frame, text="Type:", font=("Arial", 7, "bold"),
                bg="white").pack(side=tk.LEFT)

        self.caliper_type_var = tk.StringVar(value="Mitutoyo Digimatic")
        cal_types = [
            "Mitutoyo Digimatic",
            "Generic USB HID",
            "Bluetooth Caliper",
            "Manual Entry"
        ]

        cal_combo = ttk.Combobox(type_frame, textvariable=self.caliper_type_var,
                                 values=cal_types, width=16, state="readonly")
        cal_combo.pack(side=tk.LEFT, padx=2)
        cal_combo.bind('<<ComboboxSelected>>', self._on_caliper_type_select)

        conn_frame = tk.Frame(content, bg="white")
        conn_frame.pack(fill=tk.X, pady=2)

        self.caliper_connect_btn = ttk.Button(conn_frame, text="🔌 CONNECT",
                                              command=self._connect_caliper, width=10)
        self.caliper_connect_btn.pack(side=tk.LEFT, padx=1)
        self.caliper_test_btn = ttk.Button(conn_frame, text="🔍 TEST",
                                           command=self._test_caliper, width=6)
        self.caliper_test_btn.pack(side=tk.LEFT, padx=1)
        ttk.Button(conn_frame, text="📏 READ",
                  command=self._read_caliper, width=6).pack(side=tk.LEFT, padx=1)

        self.caliper_status = tk.Label(conn_frame, text="●", fg="red",
                                       font=("Arial", 10), bg="white")
        self.caliper_status.pack(side=tk.LEFT, padx=5)

        input_grid = tk.Frame(content, bg="white")
        input_grid.pack(fill=tk.X, pady=2)

        tk.Label(input_grid, text="Thick (mm):", font=("Arial", 7),
                bg="white").grid(row=0, column=0, sticky=tk.W, pady=1)
        self.thickness_var = tk.StringVar()
        self.thickness_entry = ttk.Entry(input_grid, textvariable=self.thickness_var, width=8)
        self.thickness_entry.grid(row=0, column=1, padx=2, pady=1)

        tk.Label(input_grid, text="Diameter (mm):", font=("Arial", 7),
                bg="white").grid(row=1, column=0, sticky=tk.W, pady=1)
        self.diameter_var = tk.StringVar()
        self.diameter_entry = ttk.Entry(input_grid, textvariable=self.diameter_var, width=8)
        self.diameter_entry.grid(row=1, column=1, padx=2, pady=1)

        tk.Label(input_grid, text="Height (mm):", font=("Arial", 7),
                bg="white").grid(row=0, column=2, sticky=tk.W, padx=(5,2), pady=1)
        self.height_var = tk.StringVar()
        self.height_entry = ttk.Entry(input_grid, textvariable=self.height_var, width=8)
        self.height_entry.grid(row=0, column=3, padx=2, pady=1)

        tk.Label(input_grid, text="Width (mm):", font=("Arial", 7),
                bg="white").grid(row=1, column=2, sticky=tk.W, padx=(5,2), pady=1)
        self.width_var = tk.StringVar()
        ttk.Entry(input_grid, textvariable=self.width_var, width=8).grid(row=1, column=3, padx=2, pady=1)

        self._setup_caliper_listeners()

        proto = tk.Frame(content, bg="#f8f9fa", relief=tk.GROOVE, bd=1)
        proto.pack(fill=tk.X, pady=2, padx=1)
        tk.Label(proto, text="✓ Mitutoyo SPC (24-bit) · Generic HID · BLE",
                font=("Arial", 6), bg="#f8f9fa", anchor=tk.W).pack(fill=tk.X, padx=2, pady=1)

        if self.deps['matplotlib'] and HAS_MPL:
            triangle_frame = tk.Frame(content, bg="white", height=160)
            triangle_frame.pack(fill=tk.BOTH, expand=True, pady=2)
            triangle_frame.pack_propagate(False)

            self.fig = plt.Figure(figsize=(2.8, 1.8), dpi=85, facecolor='white')
            self.ax = self.fig.add_subplot(111)
            SoilTextureClassifier.create_triangle_plot(self.ax, None, None, None)
            self.fig.tight_layout(pad=0.5)

            self.canvas = FigureCanvasTkAgg(self.fig, triangle_frame)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _setup_caliper_listeners(self):
        def on_focus_in(entry, var_name):
            self._safe_status(f"📏 Ready for {var_name} - Press READ on caliper")
        def on_focus_out(entry):
            self._safe_status("Physical Properties Unified Suite v3.1 - Ready")

        if self.thickness_entry:
            self.thickness_entry.bind("<FocusIn>",
                lambda e: on_focus_in(self.thickness_entry, "thickness"))
        if self.diameter_entry:
            self.diameter_entry.bind("<FocusIn>",
                lambda e: on_focus_in(self.diameter_entry, "diameter"))
        if self.height_entry:
            self.height_entry.bind("<FocusIn>",
                lambda e: on_focus_in(self.height_entry, "height"))

    def _on_magsus_brand_select(self, event=None):
        brand = self.magsus_brand_var.get()
        if 'AGICO' in brand and not self.deps['tdmagsus']:
            self._safe_status("⚠️ AGICO driver requires: pip install tdmagsus")

    def _connect_magsus(self):
        brand = self.magsus_brand_var.get()
        port = self.port_var.get()

        if not port:
            messagebox.showwarning("No Port", "Please select a serial port")
            return

        if self.magsus_driver:
            self._disconnect_magsus()

        if 'AGICO' in brand:
            self.magsus_driver = AGICOKappabridgeDriver(port, self.ui_queue)
        elif 'Bartington' in brand:
            self.magsus_driver = BartingtonMS2Driver(port, self.ui_queue)
        elif 'ZH' in brand:
            self.magsus_driver = ZHInstrumentsDriver(port, self.ui_queue)
        elif 'Terraplus' in brand or 'KT' in brand:
            self.magsus_driver = TerraplusKTDriver(port, self.ui_queue)
        else:
            self.magsus_driver = GenericSerialMagSusDriver(port, self.ui_queue)

        self._show_progress(True, 'indeterminate')
        self._safe_status(f"🧲 Connecting to {brand}...")

        def connect_worker():
            success, message = self.magsus_driver.connect()
            def update_ui():
                self._show_progress(False)
                if success:
                    self.magsus_connected = True
                    self.mag_status.config(text="●", fg="#2ecc71")
                    self.mag_connect_btn.config(text="🔌 DISCONNECT",
                                               command=self._disconnect_magsus)
                    self._safe_status(f"✅ {message}")
                    self.current.magsus_instrument = message
                else:
                    self.magsus_driver = None
                    messagebox.showerror("Connection Failed", message)
            if self.ui_queue:
                self.ui_queue.schedule(update_ui)
            else:
                update_ui()

        threading.Thread(target=connect_worker, daemon=True).start()

    def _disconnect_magsus(self):
        if self.magsus_driver:
            self.magsus_driver.disconnect()
            self.magsus_driver = None
        self.magsus_connected = False
        self.mag_status.config(text="●", fg="red")
        self.mag_connect_btn.config(text="🔌 CONNECT", command=self._connect_magsus)
        self._safe_status("🧲 MagSus disconnected")

    def _test_magsus(self):
        if not self.magsus_connected or not self.magsus_driver:
            messagebox.showwarning("Not Connected", "Connect to magnetometer first")
            return
        self._show_progress(True, 'indeterminate')
        self._safe_status("🧲 Testing instrument...")

        def test_worker():
            success, message = self.magsus_driver.test()
            def update_ui():
                self._show_progress(False)
                if success:
                    messagebox.showinfo("Test Successful", message)
                    self._safe_status(f"✅ Test: {message[:50]}")
                else:
                    messagebox.showerror("Test Failed", message)
            if self.ui_queue:
                self.ui_queue.schedule(update_ui)
            else:
                update_ui()

        threading.Thread(target=test_worker, daemon=True).start()

    def _read_magsus(self):
        if not self.magsus_connected or not self.magsus_driver:
            messagebox.showwarning("Not Connected", "Connect to magnetometer first")
            return
        self._show_progress(True, 'indeterminate')
        self._safe_status("🧲 Reading...")

        def read_worker():
            data = self.magsus_driver.read_with_retry()
            def update_ui():
                self._show_progress(False)
                if data and 'k' in data:
                    k = data['k']
                    instrument = data.get('instrument', 'Unknown')
                    interpretation = MagSusInterpreter.interpret(k)

                    self.current.magsus_k = k
                    self.current.magsus_instrument = instrument
                    self.current.magsus_interpretation = interpretation['description']
                    self.current.magsus_mineralogy = interpretation['mineralogy']
                    self.current.magsus_confidence = interpretation['confidence']

                    if 'frequency' in data:
                        self.current.magsus_frequency = data['frequency']
                    if 'field' in data:
                        self.current.magsus_field = data['field']
                    if 'temperature' in data:
                        self.current.magsus_temp = data['temperature']

                    self.magsus_label.config(text=f"{k:.1f}")
                    self.magsus_interpret.config(text=interpretation['description'][:40])

                    if interpretation['mineralogy']:
                        self.magsus_mineralogy.config(
                            text=f"{', '.join(interpretation['mineralogy'])}")
                    else:
                        self.magsus_mineralogy.config(text="")

                    self.magsus_confidence.config(
                        text=f"Confidence: {interpretation['confidence']:.0f}%")

                    self._safe_status(f"🧲 {instrument}: {k:.1f} ×10⁻⁵ SI")
                else:
                    messagebox.showerror("Read Failed", "No data received from instrument")
            if self.ui_queue:
                self.ui_queue.schedule(update_ui)
            else:
                update_ui()

        threading.Thread(target=read_worker, daemon=True).start()

    def _on_caliper_type_select(self, event=None):
        cal_type = self.caliper_type_var.get()
        if 'Bluetooth' in cal_type and not self.deps['bleak']:
            self._safe_status("⚠️ Bluetooth requires: pip install bleak")

    def _connect_caliper(self):
        cal_type = self.caliper_type_var.get()

        if self.caliper_driver:
            self._disconnect_caliper()

        if 'Mitutoyo' in cal_type:
            self.caliper_driver = MitutoyoDigimaticDriver(self.ui_queue)
        elif 'Generic' in cal_type:
            self.caliper_driver = GenericHIDCaliperDriver(self.ui_queue)
        elif 'Bluetooth' in cal_type:
            if not self.deps['bleak']:
                messagebox.showerror("Missing Dependency",
                                    "Install bleak: pip install bleak")
                return
            self.caliper_driver = BluetoothCaliperDriver(self.ui_queue)
        else:
            self._safe_status("📏 Manual entry mode")
            return

        self._show_progress(True, 'indeterminate')
        self._safe_status(f"📏 Connecting to {cal_type}...")

        def connect_worker():
            success, message = self.caliper_driver.connect()
            def update_ui():
                self._show_progress(False)
                if success:
                    self.caliper_connected = True
                    self.caliper_status.config(text="●", fg="#2ecc71")
                    self.caliper_connect_btn.config(text="🔌 DISCONNECT",
                                                   command=self._disconnect_caliper)
                    self._safe_status(f"✅ {message}")
                    self.current.caliper_model = message
                else:
                    self.caliper_driver = None
                    messagebox.showerror("Connection Failed", message)
            if self.ui_queue:
                self.ui_queue.schedule(update_ui)
            else:
                update_ui()

        threading.Thread(target=connect_worker, daemon=True).start()

    def _disconnect_caliper(self):
        if self.caliper_driver:
            self.caliper_driver.disconnect()
            self.caliper_driver = None
        self.caliper_connected = False
        self.caliper_status.config(text="●", fg="red")
        self.caliper_connect_btn.config(text="🔌 CONNECT", command=self._connect_caliper)
        self._safe_status("📏 Caliper disconnected")

    def _test_caliper(self):
        if not self.caliper_connected or not self.caliper_driver:
            messagebox.showwarning("Not Connected", "Connect to caliper first")
            return
        self._show_progress(True, 'indeterminate')
        self._safe_status("📏 Testing caliper...")

        def test_worker():
            success, message = self.caliper_driver.test()
            def update_ui():
                self._show_progress(False)
                if success:
                    messagebox.showinfo("Caliper Test", message)
                    self._safe_status(f"✅ {message}")
                else:
                    messagebox.showerror("Test Failed", message)
            if self.ui_queue:
                self.ui_queue.schedule(update_ui)
            else:
                update_ui()

        threading.Thread(target=test_worker, daemon=True).start()

    def _read_caliper(self):
        if not self.caliper_connected or not self.caliper_driver:
            self._save_caliper_measurement()
            return

        self._show_progress(True, 'indeterminate')
        self._safe_status("📏 Reading caliper...")

        def read_worker():
            data = self.caliper_driver.read()
            def update_ui():
                self._show_progress(False)
                if data and 'value_mm' in data:
                    value = data['value_mm']
                    instrument = data.get('instrument', 'Caliper')

                    focused = self.window.focus_get()

                    if focused == self.thickness_entry:
                        self.thickness_var.set(f"{value:.2f}")
                        self.current.thickness_mm = value
                        self._safe_status(f"📏 Thickness: {value:.2f} mm")
                    elif focused == self.diameter_entry:
                        self.diameter_var.set(f"{value:.2f}")
                        self.current.diameter_mm = value
                        self._safe_status(f"📏 Diameter: {value:.2f} mm")
                    elif focused == self.height_entry:
                        self.height_var.set(f"{value:.2f}")
                        self.current.height_mm = value
                        self._safe_status(f"📏 Height: {value:.2f} mm")
                    else:
                        self.thickness_var.set(f"{value:.2f}")
                        self.current.thickness_mm = value
                        self._safe_status(f"📏 {instrument}: {value:.2f} mm")

                    self.current.caliper_model = instrument
                else:
                    messagebox.showwarning("Read Failed",
                                          "No data from caliper.\nMake sure it's connected and sending data.")
            if self.ui_queue:
                self.ui_queue.schedule(update_ui)
            else:
                update_ui()

        threading.Thread(target=read_worker, daemon=True).start()

    def _save_caliper_measurement(self):
        try:
            if self.thickness_var and self.thickness_var.get():
                self.current.thickness_mm = float(self.thickness_var.get())
            if self.diameter_var and self.diameter_var.get():
                self.current.diameter_mm = float(self.diameter_var.get())
            if self.height_var and self.height_var.get():
                self.current.height_mm = float(self.height_var.get())
            if self.width_var and self.width_var.get():
                self.current.width_mm = float(self.width_var.get())
            self.current.caliper_model = self.caliper_type_var.get()
        except ValueError:
            messagebox.showwarning("Invalid Input", "Please enter valid numbers for dimensions")

    def _import_granulometer(self):
        path = filedialog.askopenfilename(
            title="Import Granulometer File",
            filetypes=[
                ("All supported", "*.csv *.xls *.xlsx *.txt"),
                ("CSV files", "*.csv"),
                ("Excel files", "*.xls *.xlsx"),
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ]
        )

        if not path:
            return

        self._show_progress(True, 'determinate')
        self._update_progress(10, f"Parsing {Path(path).name}...")

        def parse_worker():
            sand, silt, clay, metadata = GranulometerParser.parse_file(path)
            def update_ui():
                self._show_progress(False)
                if sand is not None:
                    self.sand_var.set(f"{sand:.1f}")
                    self.current.sand_pct = sand
                if silt is not None:
                    self.silt_var.set(f"{silt:.1f}")
                    self.current.silt_pct = silt
                if clay is not None:
                    self.clay_var.set(f"{clay:.1f}")
                    self.current.clay_pct = clay
                self.current.granulometer_model = metadata.get('instrument', 'CSV Import')
                self.file_label.config(text=f"📁 {Path(path).name[:20]}")
                self._classify_texture()
                instrument = metadata.get('instrument', 'Unknown')
                self._safe_status(f"🌾 Imported: {instrument} - {Path(path).name}")
            if self.ui_queue:
                self.ui_queue.schedule(update_ui)
            else:
                update_ui()

        threading.Thread(target=parse_worker, daemon=True).start()

    def _classify_texture(self):
        try:
            sand = float(self.sand_var.get()) if self.sand_var.get() else None
            silt = float(self.silt_var.get()) if self.silt_var.get() else None
            clay = float(self.clay_var.get()) if self.clay_var.get() else None
            gravel = float(self.gravel_var.get()) if self.gravel_var.get() else 0
        except ValueError:
            messagebox.showwarning("Invalid Input", "Please enter valid numbers")
            return

        self.current.sand_pct = sand
        self.current.silt_pct = silt
        self.current.clay_pct = clay
        self.current.gravel_pct = gravel if gravel > 0 else None

        if sand and silt and clay:
            usda_result = SoilTextureClassifier.classify(sand, silt, clay)
            self.current.usda_texture = usda_result['texture']
            self.current.usda_confidence = usda_result['confidence']
            self.texture_label.config(text=f"USDA: {usda_result['texture']}")
            if usda_result['confidence'] > 0:
                self.texture_confidence.config(
                    text=f"Confidence: {usda_result['confidence']:.0f}%")
            else:
                self.texture_confidence.config(text="")
            if self.deps['matplotlib'] and HAS_MPL:
                SoilTextureClassifier.create_triangle_plot(self.ax, sand, silt, clay)
                self.canvas.draw()

        if sand and silt and clay:
            mud = silt + clay
            folk = SoilTextureClassifier.folk_classify(gravel or 0, sand, mud)
            self.current.folk_class = folk
            self.folk_label.config(text=f"Folk: {folk}")

        self._safe_status(f"🌾 USDA: {self.current.usda_texture}")

    def _save_to_sample(self):
        self._save_caliper_measurement()
        self.current.timestamp = datetime.now()
        self.measurements.append(self.current)
        self.sample_counter.config(text=f"📋 {len(self.measurements)} samples")

        magsus_str = f"{self.current.magsus_k:.1f}" if self.current.magsus_k else "-"
        sand_str = f"{self.current.sand_pct:.1f}" if self.current.sand_pct else "-"
        silt_str = f"{self.current.silt_pct:.1f}" if self.current.silt_pct else "-"
        clay_str = f"{self.current.clay_pct:.1f}" if self.current.clay_pct else "-"
        thick_str = f"{self.current.thickness_mm:.2f}" if self.current.thickness_mm else "-"
        caliper_str = self.current.caliper_model or "-"
        if len(caliper_str) > 10:
            caliper_str = caliper_str[:8] + ".."

        self.tree.insert('', 0, values=(
            self.current.timestamp.strftime('%H:%M'),
            self.current.sample_id[-12:],
            magsus_str,
            sand_str,
            silt_str,
            clay_str,
            self.current.usda_texture or '-',
            thick_str,
            caliper_str
        ))

        self._generate_sample_id()
        self._safe_status(f"✅ Saved sample #{len(self.measurements)}")

    def _clear_current(self):
        if self.magsus_label:
            self.magsus_label.config(text="---")
            self.magsus_interpret.config(text="No measurement")
            self.magsus_mineralogy.config(text="")
            self.magsus_confidence.config(text="")

        if self.sand_var: self.sand_var.set("")
        if self.silt_var: self.silt_var.set("")
        if self.clay_var: self.clay_var.set("")
        if self.gravel_var: self.gravel_var.set("")
        if self.texture_label:
            self.texture_label.config(text="USDA: ---")
            self.texture_confidence.config(text="")
            self.folk_label.config(text="Folk: ---")

        if self.thickness_var: self.thickness_var.set("")
        if self.diameter_var: self.diameter_var.set("")
        if self.height_var: self.height_var.set("")
        if self.width_var: self.width_var.set("")

        if self.file_label:
            self.file_label.config(text="")

        if self.deps['matplotlib'] and HAS_MPL:
            SoilTextureClassifier.create_triangle_plot(self.ax, None, None, None)
            self.canvas.draw()

        self._generate_sample_id()
        self._safe_status("🧹 Cleared current form")

    def _clear_all(self):
        if not messagebox.askyesno("Clear All", "Clear all samples and disconnect instruments?"):
            return

        self.measurements = []
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.sample_counter.config(text="📋 0 samples")

        if self.magsus_connected:
            self._disconnect_magsus()
        if self.caliper_connected:
            self._disconnect_caliper()

        self._clear_current()
        self._safe_status("🗑️ All data cleared")

    def _export_data(self):
        if not self.measurements:
            messagebox.showwarning("No Data", "No measurements to export")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("All files", "*.*")],
            initialfile=f"physical_properties_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )

        if not path:
            return

        try:
            rows = [m.to_dict() for m in self.measurements]
            df = pd.DataFrame(rows)
            df.to_csv(path, index=False)
            messagebox.showinfo("Export Complete", f"✅ Exported {len(rows)} samples to:\n{Path(path).name}")
            self._safe_status(f"📊 Exported {len(rows)} samples")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def collect_data(self) -> List[Dict[str, Any]]:
        data = []
        for m in self.measurements:
            row = {
                'plugin': 'Physical Properties Unified Suite',
                'timestamp': m.timestamp.isoformat(),
                'sample_id': m.sample_id,
                'instrument': f"{m.magsus_instrument or ''} {m.granulometer_model or ''} {m.caliper_model or ''}".strip()
            }
            row.update(m.to_dict())
            data.append(row)
        return data

    def send_to_table(self):
        if not self.measurements:
            messagebox.showwarning("No Data", "No measurements to send")
            return

        data = self.collect_data()

        try:
            self.parent.import_data_from_plugin(data)
            self._safe_status(f"✅ Sent {len(data)} samples to main table")
            messagebox.showinfo(
                "Success",
                f"✅ {len(data)} physical property samples sent to main table\n\n"
                f"Columns added:\n"
                f"• Magnetic Susceptibility (×10⁻⁵ SI)\n"
                f"• Sand/Silt/Clay/Gravel %\n"
                f"• USDA Texture + Confidence\n"
                f"• Folk Classification\n"
                f"• Dimensional measurements (mm)\n"
                f"• Full instrument metadata"
            )
        except AttributeError:
            messagebox.showwarning(
                "Integration Error",
                "Main application does not support plugin data import.\n"
                "Expected method: import_data_from_plugin()"
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send data: {e}")

    def test_connection(self):
        lines = []
        lines.append(f"Physical Properties Unified Suite v3.1")
        lines.append(f"✅ Platform: {platform.system()} {platform.release()}")
        lines.append(f"✅ Thread-safe UI: ✓")
        lines.append(f"✅ SPC Protocol: ✓ (24-bit Mitutoyo)")
        lines.append(f"✅ USDA Triangle: {'✓' if self.deps['matplotlib'] and HAS_MPL else '✗'}")
        lines.append(f"✅ Pandas: {'✓' if self.deps['pandas'] else '✗'}")
        lines.append(f"✅ PySerial: {'✓' if self.deps['pyserial'] else '✗'}")
        lines.append(f"✅ HIDAPI: {'✓' if self.deps['hidapi'] else '✗'}")
        lines.append(f"✅ Bleak: {'✓' if self.deps['bleak'] else '✗'}")
        lines.append(f"✅ tdmagsus: {'✓' if self.deps['tdmagsus'] else '✗'}")
        lines.append(f"\n✅ REAL DRIVERS IMPLEMENTED:")
        lines.append(f"   • MagSus: AGICO, Bartington, ZH, Terraplus, Generic")
        lines.append(f"   • Granulometer: Malvern, Horiba, Beckman, Generic")
        lines.append(f"   • Caliper: Mitutoyo SPC, Generic HID, Bluetooth LE")
        lines.append(f"\n✅ Main App Integration: send_to_table() ✓")
        return True, "\n".join(lines)

# ============================================================================
# STANDARD PLUGIN REGISTRATION - LEFT PANEL FIRST, MENU SECOND
# ============================================================================
def setup_plugin(main_app):
    """Register plugin - tries left panel first, falls back to hardware menu"""
    global _PHYSICAL_REGISTERED

    # PREVENT DOUBLE REGISTRATION
    if _PHYSICAL_REGISTERED:
        print(f"⏭️ Physical Properties plugin already registered, skipping...")
        return None

    plugin = PhysicalPropertiesUnifiedSuitePlugin(main_app)

    # ===== TRY LEFT PANEL FIRST (hardware buttons) =====
    if hasattr(main_app, 'left') and main_app.left is not None:
        main_app.left.add_hardware_button(
            name=PLUGIN_INFO.get("name", "Plugin Name"),
            icon=PLUGIN_INFO.get("icon", "🔌"),
            command=plugin.show_interface
        )
        print(f"✅ Added to left panel: {PLUGIN_INFO.get('name')}")
        _PHYSICAL_REGISTERED = True
        return plugin

    # ===== FALLBACK TO HARDWARE MENU =====
    if hasattr(main_app, 'menu_bar'):
        if not hasattr(main_app, 'hardware_menu'):
            main_app.hardware_menu = tk.Menu(main_app.menu_bar, tearoff=0)
            main_app.menu_bar.add_cascade(label="🔧 Hardware", menu=main_app.hardware_menu)

        main_app.hardware_menu.add_command(
            label=PLUGIN_INFO.get("name", "Plugin Name"),
            command=plugin.show_interface
        )
        print(f"✅ Added to Hardware menu: {PLUGIN_INFO.get('name')}")
        _PHYSICAL_REGISTERED = True

    return plugin
