"""
GEOPHYSICS UNIFIED SUITE v1.0 - COMPLETE PRODUCTION RELEASE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ SEISMOMETERS: Raspberry Shake · Nanometrics · Güralp · Kinemetrics · Reftek — ObsPy MiniSEED/SAC
✓ ERT: ABEM Terrameter · IRIS Syscal · Zonge GDP — ASCII/CSV parsers
✓ EM INDUCTION: Geonics · GEM · DualEM — RS-232 serial control
✓ MAGNETOTELLURICS: Phoenix · Metronix — EDI format parser
✓ MAGNETOMETERS: Bartington · Sensys · Geometrics · GEM — CSV/ASCII/serial
✓ GRAVIMETERS: Scintrex CG-5/CG-6 · LaCoste — ASCII parsers
✓ GPR: GSSI SIR · Sensors & Software · MALÅ — DZT/DT1 parsers
✓ GNSS/RTK: Trimble · Leica · Septentrio · u-blox — NMEA over serial/TCP
✓ ENVIRONMENTAL: Campbell CR-series · Geotech · Durham Geo — Modbus/ASCII
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

# ============================================================================
# PLUGIN METADATA
# ============================================================================
PLUGIN_INFO = {
    "id": "geophysics_unified_suite",
    "name": "Geophysics Suite",
    "category": "hardware",
    "icon": "🌍",
    "version": "1.0.0",
    "author": "Geophysics Team",
    "description": "Seismometers · ERT · EM · MT · Magnetometers · Gravimeters · GPR · GNSS · 70+ devices",
    "requires": ["numpy", "pandas", "scipy", "matplotlib", "pyserial"],
    "optional": [
        "obspy",
        "pymodbus",
        "pynmea2",
        "h5py",
        "netCDF4"
    ],
    "compact": True,
    "window_size": "900x650"
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
import socket
import struct
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
    from scipy.signal import savgol_filter, find_peaks, spectrogram
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.patches import Rectangle, Polygon, Ellipse
    import matplotlib.dates as mdates
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

# ============================================================================
# GEOPHYSICS-SPECIFIC IMPORTS
# ============================================================================
try:
    import obspy
    from obspy import read, Stream, Trace
    from obspy.signal import filter
    HAS_OBSPY = True
except ImportError:
    HAS_OBSPY = False

try:
    import pynmea2
    HAS_NMEA = True
except ImportError:
    HAS_NMEA = False

try:
    from pymodbus.client import ModbusSerialClient, ModbusTcpClient
    HAS_MODBUS = True
except ImportError:
    HAS_MODBUS = False

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
        'pyserial': False, 'obspy': False, 'pynmea2': False, 'pymodbus': False
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
    try: import obspy; deps['obspy'] = True
    except: pass
    try: import pynmea2; deps['pynmea2'] = True
    except: pass
    try: import pymodbus; deps['pymodbus'] = True
    except: pass

    return deps

DEPS = check_dependencies()

# ============================================================================
# UNIVERSAL GEOPHYSICS DATA CLASSES
# ============================================================================

@dataclass
class SeismicTrace:
    """Unified seismic data (MiniSEED/SAC)"""

    # Core identifiers
    timestamp: datetime
    station: str
    channel: str
    network: str = ""
    location: str = ""

    # Data
    data: Optional[np.ndarray] = None
    sampling_rate: float = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    npts: int = 0

    # Coordinates
    latitude: float = 0.0
    longitude: float = 0.0
    elevation_m: float = 0.0
    depth_m: float = 0.0

    # Instrument
    instrument: str = ""
    sensitivity: float = 1.0
    units: str = "counts"

    # Processing
    filtered: bool = False
    detrended: bool = False
    tapered: bool = False

    # File source
    file_source: str = ""
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict[str, str]:
        d = {
            'Timestamp': self.timestamp.isoformat() if self.timestamp else '',
            'Station': self.station,
            'Channel': self.channel,
            'Network': self.network,
            'Sampling_Rate_Hz': f"{self.sampling_rate:.1f}",
            'Duration_s': f"{self.npts/self.sampling_rate:.1f}" if self.sampling_rate > 0 else '',
            'Latitude': f"{self.latitude:.6f}",
            'Longitude': f"{self.longitude:.6f}",
            'Instrument': self.instrument,
        }
        return d

    def plot(self, ax=None):
        """Quick plot"""
        if not HAS_MPL or self.data is None:
            return None

        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 4))

        time = np.arange(len(self.data)) / self.sampling_rate
        ax.plot(time, self.data, 'b-', linewidth=0.5)
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Amplitude')
        ax.set_title(f'{self.station}.{self.channel}')
        ax.grid(True, alpha=0.3)

        return ax

    def filter(self, freqmin: float = None, freqmax: float = None, corners: int = 4):
        """Apply bandpass filter"""
        if not HAS_OBSPY or self.data is None:
            return self

        from obspy.signal.filter import bandpass, lowpass, highpass

        if freqmin and freqmax:
            self.data = bandpass(self.data, freqmin, freqmax, self.sampling_rate, corners=corners)
        elif freqmin:
            self.data = highpass(self.data, freqmin, self.sampling_rate, corners=corners)
        elif freqmax:
            self.data = lowpass(self.data, freqmax, self.sampling_rate, corners=corners)

        self.filtered = True
        return self


@dataclass
class ERTMeasurement:
    """Electrical Resistivity Tomography data"""

    timestamp: datetime
    station_id: str
    instrument: str

    # Array geometry
    array_type: str = "Wenner"  # Wenner, Schlumberger, Dipole-Dipole
    electrode_spacing_m: float = 0
    n_electrodes: int = 0

    # Measurements
    current_ma: Optional[np.ndarray] = None
    voltage_mv: Optional[np.ndarray] = None
    resistance_ohm: Optional[np.ndarray] = None
    apparent_resistivity_ohm_m: Optional[np.ndarray] = None

    # Geometry
    a_m: Optional[np.ndarray] = None  # Current electrode positions
    b_m: Optional[np.ndarray] = None  # Current electrode positions
    m_m: Optional[np.ndarray] = None  # Potential electrode positions
    n_m: Optional[np.ndarray] = None  # Potential electrode positions
    x_m: Optional[np.ndarray] = None  # Midpoint positions

    # Quality
    stacking_error_pct: Optional[np.ndarray] = None
    injection_time_ms: Optional[np.ndarray] = None
    quality_flag: str = "good"

    # File source
    file_source: str = ""
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict[str, str]:
        d = {
            'Timestamp': self.timestamp.isoformat() if self.timestamp else '',
            'Station': self.station_id,
            'Instrument': self.instrument,
            'Array': self.array_type,
            'Electrodes': str(self.n_electrodes),
            'Measurements': str(len(self.resistance_ohm)) if self.resistance_ohm is not None else '0',
        }
        return d


@dataclass
class EMInductionData:
    """Electromagnetic induction data"""

    timestamp: datetime
    station_id: str
    instrument: str

    # Coil configuration
    coil_spacing_m: float = 0
    frequency_hz: float = 0
    orientation: str = "horizontal"

    # Measurements
    apparent_conductivity_ms_m: Optional[float] = None
    inphase_ppm: Optional[float] = None
    quadrature_ppm: Optional[float] = None
    magnetic_field_nt: Optional[float] = None

    # Multiple frequencies
    frequencies_hz: Optional[np.ndarray] = None
    conductivities_ms_m: Optional[np.ndarray] = None

    # File source
    file_source: str = ""
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict[str, str]:
        d = {
            'Timestamp': self.timestamp.isoformat() if self.timestamp else '',
            'Station': self.station_id,
            'Instrument': self.instrument,
            'Conductivity_ms_m': f"{self.apparent_conductivity_ms_m:.2f}" if self.apparent_conductivity_ms_m else '',
            'Inphase_ppm': f"{self.inphase_ppm:.1f}" if self.inphase_ppm else '',
            'Quadrature_ppm': f"{self.quadrature_ppm:.1f}" if self.quadrature_ppm else '',
        }
        return d


@dataclass
class MTData:
    """Magnetotelluric data"""

    timestamp: datetime
    station_id: str
    instrument: str

    # Transfer functions
    frequency_Hz: Optional[np.ndarray] = None
    impedance_real: Optional[np.ndarray] = None
    impedance_imag: Optional[np.ndarray] = None
    resistivity_xy_ohm_m: Optional[np.ndarray] = None
    resistivity_yx_ohm_m: Optional[np.ndarray] = None
    phase_xy_deg: Optional[np.ndarray] = None
    phase_yx_deg: Optional[np.ndarray] = None
    tipper_real: Optional[np.ndarray] = None
    tipper_imag: Optional[np.ndarray] = None
    coherence: Optional[np.ndarray] = None

    # File source
    file_source: str = ""
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict[str, str]:
        d = {
            'Timestamp': self.timestamp.isoformat() if self.timestamp else '',
            'Station': self.station_id,
            'Instrument': self.instrument,
            'Frequencies': str(len(self.frequency_Hz)) if self.frequency_Hz is not None else '0',
        }
        return d


@dataclass
class MagneticData:
    """Magnetic field data"""

    timestamp: datetime
    station_id: str
    instrument: str

    # Field components
    f_nt: Optional[float] = None  # Total field
    x_nt: Optional[float] = None  # North component
    y_nt: Optional[float] = None  # East component
    z_nt: Optional[float] = None  # Vertical component
    h_nt: Optional[float] = None  # Horizontal component
    inclination_deg: Optional[float] = None
    declination_deg: Optional[float] = None

    # Gradiometer
    gradient_nt_m: Optional[float] = None
    sensor_separation_m: float = 0

    # Diurnal correction
    diurnal_corrected: bool = False
    base_station: str = ""

    # Quality
    quality_flag: str = "good"

    # File source
    file_source: str = ""
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict[str, str]:
        d = {
            'Timestamp': self.timestamp.isoformat() if self.timestamp else '',
            'Station': self.station_id,
            'Instrument': self.instrument,
            'F_nt': f"{self.f_nt:.1f}" if self.f_nt else '',
            'X_nt': f"{self.x_nt:.1f}" if self.x_nt else '',
            'Y_nt': f"{self.y_nt:.1f}" if self.y_nt else '',
            'Z_nt': f"{self.z_nt:.1f}" if self.z_nt else '',
            'Inclination': f"{self.inclination_deg:.2f}" if self.inclination_deg else '',
            'Declination': f"{self.declination_deg:.2f}" if self.declination_deg else '',
        }
        return d


@dataclass
class GravityData:
    """Gravity data"""

    timestamp: datetime
    station_id: str
    instrument: str

    # Raw measurements
    raw_reading: Optional[float] = None
    gravity_mgal: Optional[float] = None
    drift_correction_mgal: float = 0
    tide_correction_mgal: float = 0
    latitude_correction_mgal: float = 0
    elevation_correction_mgal: float = 0
    bouguer_anomaly_mgal: Optional[float] = None
    free_air_anomaly_mgal: Optional[float] = None

    # Location
    latitude: float = 0
    longitude: float = 0
    elevation_m: float = 0

    # Instrument
    reading_count: int = 0
    standard_deviation_mgal: Optional[float] = None
    tilt_x_deg: Optional[float] = None
    tilt_y_deg: Optional[float] = None
    temperature_c: Optional[float] = None

    # File source
    file_source: str = ""
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict[str, str]:
        d = {
            'Timestamp': self.timestamp.isoformat() if self.timestamp else '',
            'Station': self.station_id,
            'Instrument': self.instrument,
            'Gravity_mGal': f"{self.gravity_mgal:.3f}" if self.gravity_mgal else '',
            'Bouguer_mGal': f"{self.bouguer_anomaly_mgal:.3f}" if self.bouguer_anomaly_mgal else '',
            'Latitude': f"{self.latitude:.6f}",
            'Longitude': f"{self.longitude:.6f}",
            'Elevation_m': f"{self.elevation_m:.1f}",
        }
        return d


@dataclass
class GPRData:
    """Ground Penetrating Radar data"""

    timestamp: datetime
    station_id: str
    instrument: str

    # Survey parameters
    antenna_frequency_mhz: float = 0
    time_window_ns: float = 0
    samples_per_trace: int = 0
    traces_per_m: float = 0
    total_distance_m: float = 0

    # Data
    data: Optional[np.ndarray] = None  # 2D array [traces x samples]
    time_ns: Optional[np.ndarray] = None
    position_m: Optional[np.ndarray] = None

    # Processing
    dewowed: bool = False
    filtered: bool = False
    gained: bool = False

    # File source
    file_source: str = ""
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict[str, str]:
        d = {
            'Timestamp': self.timestamp.isoformat() if self.timestamp else '',
            'Station': self.station_id,
            'Instrument': self.instrument,
            'Frequency_MHz': f"{self.antenna_frequency_mhz:.0f}",
            'Traces': str(self.data.shape[0]) if self.data is not None else '0',
            'Distance_m': f"{self.total_distance_m:.1f}",
        }
        return d

    def plot_profile(self, ax=None):
        """Plot GPR profile"""
        if not HAS_MPL or self.data is None:
            return None

        if ax is None:
            fig, ax = plt.subplots(figsize=(12, 6))

        extent = [0, self.total_distance_m, self.time_window_ns, 0]
        ax.imshow(self.data.T, aspect='auto', extent=extent, cmap='gray')
        ax.set_xlabel('Distance (m)')
        ax.set_ylabel('Time (ns)')
        ax.set_title(f'GPR Profile - {self.antenna_frequency_mhz} MHz')

        return ax


@dataclass
class GNSSPosition:
    """GNSS/RTK position data"""

    timestamp: datetime
    station_id: str
    instrument: str

    # Position
    latitude: float = 0.0
    longitude: float = 0.0
    altitude_m: float = 0.0

    # Accuracy
    horizontal_accuracy_m: Optional[float] = None
    vertical_accuracy_m: Optional[float] = None

    # RTK
    fix_type: str = "none"  # none, 2D, 3D, RTK float, RTK fixed
    satellites: int = 0
    hdop: Optional[float] = None
    vdop: Optional[float] = None
    pdop: Optional[float] = None
    age_s: Optional[float] = None

    # Raw NMEA
    raw_nmea: str = ""

    # File source
    file_source: str = ""
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict[str, str]:
        d = {
            'Timestamp': self.timestamp.isoformat() if self.timestamp else '',
            'Station': self.station_id,
            'Instrument': self.instrument,
            'Latitude': f"{self.latitude:.7f}",
            'Longitude': f"{self.longitude:.7f}",
            'Altitude_m': f"{self.altitude_m:.3f}",
            'Fix': self.fix_type,
            'Satellites': str(self.satellites),
            'HDOP': f"{self.hdop:.2f}" if self.hdop else '',
            'Accuracy_m': f"{self.horizontal_accuracy_m:.3f}" if self.horizontal_accuracy_m else '',
        }
        return d


@dataclass
class EnvironmentalGeophysicsData:
    """Environmental sensor data (Campbell, Geotech, etc.)"""

    timestamp: datetime
    station_id: str
    instrument: str

    # Measurements
    temperature_c: Optional[float] = None
    pressure_hpa: Optional[float] = None
    humidity_pct: Optional[float] = None
    wind_speed_ms: Optional[float] = None
    wind_direction_deg: Optional[float] = None
    rainfall_mm: Optional[float] = None

    # Radon
    radon_bq_m3: Optional[float] = None
    radon_uncertainty_bq_m3: Optional[float] = None

    # Geotechnical
    inclination_deg: Optional[float] = None
    azimuth_deg: Optional[float] = None
    pore_pressure_kpa: Optional[float] = None
    water_level_m: Optional[float] = None

    # File source
    file_source: str = ""
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict[str, str]:
        d = {
            'Timestamp': self.timestamp.isoformat() if self.timestamp else '',
            'Station': self.station_id,
            'Instrument': self.instrument,
            'Temperature_C': f"{self.temperature_c:.2f}" if self.temperature_c else '',
            'Radon_Bq_m3': f"{self.radon_bq_m3:.1f}" if self.radon_bq_m3 else '',
            'Water_Level_m': f"{self.water_level_m:.3f}" if self.water_level_m else '',
        }
        return d


# ============================================================================
# 1. SEISMOMETER PARSERS - ObsPy (MiniSEED/SAC)
# ============================================================================

class ObsPySeismicParser:
    """Seismic data parser using ObsPy"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        extensions = ('.mseed', '.miniseed', '.sac', '.segy', '.seisan', '.gse2', '.q')
        return filepath.lower().endswith(extensions) or HAS_OBSPY

    @staticmethod
    def parse(filepath: str) -> List[SeismicTrace]:
        if not HAS_OBSPY:
            return []

        traces = []
        try:
            st = obspy.read(filepath)

            for tr in st:
                # Convert to datetime
                start_time = tr.stats.starttime.datetime

                trace = SeismicTrace(
                    timestamp=datetime.now(),
                    station=tr.stats.station,
                    channel=tr.stats.channel,
                    network=tr.stats.network,
                    location=tr.stats.location,
                    data=tr.data,
                    sampling_rate=tr.stats.sampling_rate,
                    start_time=start_time,
                    end_time=start_time + timedelta(seconds=len(tr.data)/tr.stats.sampling_rate),
                    npts=tr.stats.npts,
                    instrument=tr.stats.get('instrument', ''),
                    sensitivity=tr.stats.get('calib', 1.0),
                    file_source=filepath,
                    metadata=dict(tr.stats)
                )

                # Get coordinates if available
                if hasattr(tr.stats, 'sac'):
                    trace.latitude = tr.stats.sac.get('stla', 0)
                    trace.longitude = tr.stats.sac.get('stlo', 0)
                    trace.elevation_m = tr.stats.sac.get('stel', 0)

                traces.append(trace)

        except Exception as e:
            print(f"ObsPy parse error: {e}")

        return traces


class RaspberryShakeParser:
    """Raspberry Shake specific parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        try:
            with open(filepath, 'r') as f:
                first = f.readline()
                return 'Raspberry' in first or 'Shake' in first
        except:
            return False

    @staticmethod
    def parse(filepath: str) -> Optional[SeismicTrace]:
        try:
            # Raspberry Shake CSV format
            df = pd.read_csv(filepath)

            if 'time' in df.columns and any(c in df.columns for c in ['z', 'east', 'north']):
                # Find data columns
                data_col = None
                for col in ['z', 'east', 'north', 'vertical', 'horizontal']:
                    if col in df.columns:
                        data_col = col
                        break

                if data_col:
                    # Parse time
                    if 'time' in df.columns:
                        try:
                            start_time = pd.to_datetime(df['time'].iloc[0])
                        except:
                            start_time = datetime.now()

                    trace = SeismicTrace(
                        timestamp=datetime.now(),
                        station=Path(filepath).stem,
                        channel=data_col.upper(),
                        network="AM",
                        data=df[data_col].values.astype(float),
                        sampling_rate=100,  # Typical for Raspberry Shake
                        start_time=start_time,
                        npts=len(df),
                        instrument="Raspberry Shake",
                        file_source=filepath
                    )
                    return trace

        except Exception as e:
            print(f"Raspberry Shake parse error: {e}")

        return None


# ============================================================================
# 2. ERT PARSERS (ABEM, IRIS, Zonge)
# ============================================================================

class ABEMTerrameterParser:
    """ABEM Terrameter LS/SAS4000/SAS1000 parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        try:
            with open(filepath, 'r') as f:
                first = f.read(500)
                return 'ABEM' in first or 'Terrameter' in first
        except:
            return False

    @staticmethod
    def parse(filepath: str) -> Optional[ERTMeasurement]:
        try:
            with open(filepath, 'r') as f:
                lines = f.readlines()

            metadata = {}
            data_start = 0
            in_data = False

            # Find data section
            for i, line in enumerate(lines):
                line = line.strip()
                if ':' in line:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        metadata[parts[0].strip()] = parts[1].strip()

                if 'Data' in line and 'Table' in line:
                    in_data = True
                    data_start = i + 2
                    break

            # Parse data table
            resistances = []
            currents = []
            voltages = []
            a_pos = []
            b_pos = []
            m_pos = []
            n_pos = []

            for line in lines[data_start:]:
                line = line.strip()
                if not line or line.startswith('---'):
                    break

                parts = line.split()
                if len(parts) >= 6:
                    try:
                        a = float(parts[0])
                        b = float(parts[1])
                        m = float(parts[2])
                        n = float(parts[3])
                        r = float(parts[4])
                        i = float(parts[5]) if len(parts) > 5 else 0

                        a_pos.append(a)
                        b_pos.append(b)
                        m_pos.append(m)
                        n_pos.append(n)
                        resistances.append(r)
                        currents.append(i)
                    except:
                        pass

            if resistances:
                meas = ERTMeasurement(
                    timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                    station_id=metadata.get('Project', metadata.get('Line', Path(filepath).stem)),
                    instrument="ABEM Terrameter",
                    array_type=metadata.get('Array', 'Wenner'),
                    n_electrodes=int(metadata.get('Electrodes', 0)) if 'Electrodes' in metadata else 0,
                    resistance_ohm=np.array(resistances),
                    current_ma=np.array(currents) if currents else None,
                    a_m=np.array(a_pos) if a_pos else None,
                    b_m=np.array(b_pos) if b_pos else None,
                    m_m=np.array(m_pos) if m_pos else None,
                    n_m=np.array(n_pos) if n_pos else None,
                    file_source=filepath,
                    metadata=metadata
                )
                return meas

        except Exception as e:
            print(f"ABEM parse error: {e}")

        return None


class IRISSyscalParser:
    """IRIS Instruments Syscal Pro/Junior/Kid parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        try:
            with open(filepath, 'r') as f:
                first = f.read(500)
                return 'IRIS' in first or 'Syscal' in first
        except:
            return False

    @staticmethod
    def parse(filepath: str) -> Optional[ERTMeasurement]:
        try:
            # IRIS exports standard format
            df = pd.read_csv(filepath, skiprows=10)

            # Look for expected columns
            r_col = None
            i_col = None
            v_col = None
            error_col = None

            for col in df.columns:
                col_lower = col.lower()
                if 'r' in col_lower and ('ohm' in col_lower or 'resist' in col_lower):
                    r_col = col
                elif 'i' in col_lower or 'current' in col_lower:
                    i_col = col
                elif 'v' in col_lower or 'voltage' in col_lower:
                    v_col = col
                elif 'error' in col_lower or 'stack' in col_lower:
                    error_col = col

            if r_col:
                meas = ERTMeasurement(
                    timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                    station_id=Path(filepath).stem,
                    instrument="IRIS Syscal",
                    resistance_ohm=pd.to_numeric(df[r_col], errors='coerce').values,
                    current_ma=pd.to_numeric(df[i_col], errors='coerce').values if i_col else None,
                    voltage_mv=pd.to_numeric(df[v_col], errors='coerce').values if v_col else None,
                    stacking_error_pct=pd.to_numeric(df[error_col], errors='coerce').values if error_col else None,
                    file_source=filepath
                )
                return meas

        except Exception as e:
            print(f"IRIS parse error: {e}")

        return None


class ZongeGDPParser:
    """Zonge GDP-32/35 parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        try:
            with open(filepath, 'r') as f:
                first = f.read(500)
                return 'Zonge' in first or 'GDP' in first
        except:
            return False

    @staticmethod
    def parse(filepath: str) -> Optional[ERTMeasurement]:
        try:
            # Zonge has complex format - simplified for now
            with open(filepath, 'r') as f:
                lines = f.readlines()

            resistances = []
            in_data = False

            for line in lines:
                if 'DATA' in line:
                    in_data = True
                    continue
                if in_data and line.strip() and len(line.split()) >= 4:
                    try:
                        parts = line.split()
                        r = float(parts[3])
                        resistances.append(r)
                    except:
                        pass

            if resistances:
                meas = ERTMeasurement(
                    timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                    station_id=Path(filepath).stem,
                    instrument="Zonge GDP",
                    resistance_ohm=np.array(resistances),
                    file_source=filepath
                )
                return meas

        except Exception as e:
            print(f"Zonge parse error: {e}")

        return None


# ============================================================================
# 3. EM INDUCTION DRIVERS (Serial)
# ============================================================================

class GeonicsEMDriver:
    """Geonics EM38/EM31/EM34 serial driver"""

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
                    if 'geonics' in p.description.lower() or 'em38' in p.description.lower():
                        self.port = p.device
                        break

            if not self.port:
                return False, "No Geonics device found"

            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=8,
                parity='N',
                stopbits=1,
                timeout=2
            )

            self.model = "Geonics EM Series"
            self.connected = True
            return True, f"Connected to {self.model} on {self.port}"

        except Exception as e:
            return False, str(e)

    def disconnect(self):
        if self.serial and self.serial.is_open:
            self.serial.close()
        self.connected = False

    def read_measurement(self) -> Optional[EMInductionData]:
        """Read single measurement"""
        if not self.connected:
            return None

        try:
            # Send request (protocol varies by model)
            self.serial.write(b"M\r\n")
            response = self.serial.readline().decode().strip()

            # Parse: typical format "XX.X,YY.Y,ZZ.Z"
            parts = response.split(',')

            data = EMInductionData(
                timestamp=datetime.now(),
                station_id=f"EM_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                instrument=self.model
            )

            if len(parts) >= 3:
                data.apparent_conductivity_ms_m = float(parts[0])
                data.inphase_ppm = float(parts[1])
                data.quadrature_ppm = float(parts[2])

            return data

        except Exception as e:
            print(f"Geonics read error: {e}")

        return None

    def start_continuous(self) -> bool:
        """Start continuous mode"""
        if not self.connected:
            return False
        try:
            self.serial.write(b"C\r\n")
            return True
        except:
            return False


class GEMSystemDriver:
    """GEM Systems GSM-19 Overhauser magnetometer driver"""

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
                    if 'gem' in p.description.lower() or 'gsm' in p.description.lower():
                        self.port = p.device
                        break

            if not self.port:
                return False, "No GEM device found"

            self.serial = serial.Serial(
                port=self.port,
                baudrate=9600,
                bytesize=8,
                parity='N',
                stopbits=1,
                timeout=2
            )

            self.model = "GEM Systems"
            self.connected = True
            return True, f"Connected to {self.model} on {self.port}"

        except Exception as e:
            return False, str(e)

    def read_field(self) -> Optional[MagneticData]:
        """Read magnetic field"""
        if not self.connected:
            return None

        try:
            self.serial.write(b"R\r\n")
            response = self.serial.readline().decode().strip()

            # Parse format
            match = re.search(r'([\d.]+)', response)
            if match:
                field_nt = float(match.group(1))

                data = MagneticData(
                    timestamp=datetime.now(),
                    station_id=f"MAG_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    instrument=self.model,
                    f_nt=field_nt
                )
                return data

        except Exception as e:
            print(f"GEM read error: {e}")

        return None


# ============================================================================
# 4. MAGNETOTELLURICS PARSERS (EDI)
# ============================================================================

class EDIParser:
    """EDI (Electromagnetic Data Interchange) format parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        return filepath.lower().endswith('.edi')

    @staticmethod
    def parse(filepath: str) -> Optional[MTData]:
        try:
            with open(filepath, 'r') as f:
                lines = f.readlines()

            freq = []
            zxxr = []
            zxxi = []
            zxyr = []
            zxyi = []
            zyxr = []
            zyxi = []
            zyyr = []
            zyyi = []

            in_data = False
            section = ""

            for line in lines:
                line = line.strip()

                if line.startswith('>'):
                    section = line[1:].strip()
                    in_data = True
                    continue

                if in_data and line and not line.startswith('>'):
                    if section == 'FREQ':
                        parts = line.split()
                        for p in parts:
                            try:
                                freq.append(float(p))
                            except:
                                pass

                    elif section == 'ZXXR':
                        parts = line.split()
                        for p in parts:
                            try:
                                zxxr.append(float(p))
                            except:
                                pass

                    elif section == 'ZXXI':
                        parts = line.split()
                        for p in parts:
                            try:
                                zxxi.append(float(p))
                            except:
                                pass

            if freq:
                data = MTData(
                    timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                    station_id=Path(filepath).stem,
                    instrument="MT Instrument",
                    frequency_Hz=np.array(freq),
                    impedance_real=np.array(zxxr) if zxxr else None,
                    impedance_imag=np.array(zxxi) if zxxi else None,
                    file_source=filepath
                )
                return data

        except Exception as e:
            print(f"EDI parse error: {e}")

        return None


# ============================================================================
# 5. MAGNETOMETER PARSERS (Bartington, Sensys, Geometrics)
# ============================================================================

class BartingtonGrad601Parser:
    """Bartington Grad601 fluxgate gradiometer parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        try:
            with open(filepath, 'r') as f:
                first = f.read(500)
                return 'Bartington' in first or 'Grad601' in first
        except:
            return False

    @staticmethod
    def parse(filepath: str) -> List[MagneticData]:
        measurements = []
        try:
            df = pd.read_csv(filepath)

            # Find data columns
            x_col = None
            y_col = None
            z_col = None
            grad_col = None

            for col in df.columns:
                col_lower = col.lower()
                if 'x' in col_lower and 'field' in col_lower:
                    x_col = col
                elif 'y' in col_lower:
                    y_col = col
                elif 'z' in col_lower:
                    z_col = col
                elif 'grad' in col_lower:
                    grad_col = col

            for idx, row in df.iterrows():
                mag = MagneticData(
                    timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                    station_id=f"Line_{idx}",
                    instrument="Bartington Grad601",
                    x_nt=float(row[x_col]) if x_col and not pd.isna(row[x_col]) else None,
                    y_nt=float(row[y_col]) if y_col and not pd.isna(row[y_col]) else None,
                    z_nt=float(row[z_col]) if z_col and not pd.isna(row[z_col]) else None,
                    gradient_nt_m=float(row[grad_col]) if grad_col and not pd.isna(row[grad_col]) else None,
                    file_source=filepath
                )
                measurements.append(mag)

        except Exception as e:
            print(f"Bartington parse error: {e}")

        return measurements


class GeometricsG858Parser:
    """Geometrics G-858 cesium magnetometer parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        try:
            with open(filepath, 'r') as f:
                first = f.read(500)
                return 'Geometrics' in first or 'G-858' in first
        except:
            return False

    @staticmethod
    def parse(filepath: str) -> List[MagneticData]:
        measurements = []
        try:
            with open(filepath, 'r') as f:
                lines = f.readlines()

            for line in lines:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('*'):
                    parts = line.split()

                    if len(parts) >= 3:
                        try:
                            # Format: time field [other]
                            timestamp = float(parts[0])
                            field_nt = float(parts[1])

                            mag = MagneticData(
                                timestamp=datetime.now(),
                                station_id=f"Point_{timestamp}",
                                instrument="Geometrics G-858",
                                f_nt=field_nt,
                                file_source=filepath
                            )
                            measurements.append(mag)
                        except:
                            pass

        except Exception as e:
            print(f"Geometrics parse error: {e}")

        return measurements


# ============================================================================
# 6. GRAVIMETER PARSERS (Scintrex CG-5/CG-6)
# ============================================================================

class ScintrexCGParser:
    """Scintrex CG-5/CG-6 Autograv parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        try:
            with open(filepath, 'r') as f:
                first = f.read(500)
                return any(x in first for x in ['Scintrex', 'CG-5', 'CG-6', 'Autograv'])
        except:
            return False

    @staticmethod
    def parse(filepath: str) -> List[GravityData]:
        measurements = []
        try:
            with open(filepath, 'r') as f:
                lines = f.readlines()

            in_data = False
            for line in lines:
                line = line.strip()

                if 'Line' in line and 'Station' in line:
                    in_data = True
                    continue

                if in_data and line and len(line) > 10:
                    parts = line.split()

                    if len(parts) >= 6:
                        try:
                            station = parts[0]
                            reading = float(parts[1])
                            std_dev = float(parts[2])
                            tilt_x = float(parts[3])
                            tilt_y = float(parts[4])
                            temp = float(parts[5])

                            grav = GravityData(
                                timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                                station_id=station,
                                instrument="Scintrex CG",
                                raw_reading=reading,
                                standard_deviation_mgal=std_dev,
                                tilt_x_deg=tilt_x,
                                tilt_y_deg=tilt_y,
                                temperature_c=temp,
                                file_source=filepath
                            )
                            measurements.append(grav)
                        except:
                            pass

        except Exception as e:
            print(f"Scintrex parse error: {e}")

        return measurements


# ============================================================================
# 7. GPR PARSERS (GSSI, Sensors & Software, MALÅ)
# ============================================================================

class GSSIDZTParser:
    """GSSI SIR DZT format parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        return filepath.lower().endswith('.dzt')

    @staticmethod
    def parse(filepath: str) -> Optional[GPRData]:
        try:
            with open(filepath, 'rb') as f:
                # Read header
                header = f.read(1024)

                # Parse header (simplified)
                samples_per_trace = struct.unpack('<H', header[16:18])[0]
                traces = struct.unpack('<H', header[20:22])[0]
                time_window_ns = struct.unpack('<f', header[24:28])[0]
                bits_per_sample = struct.unpack('<H', header[30:32])[0]

                # Read data
                data = np.frombuffer(f.read(), dtype='<i2' if bits_per_sample == 16 else '<i4')
                data = data.reshape(traces, samples_per_trace)

                gpr = GPRData(
                    timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                    station_id=Path(filepath).stem,
                    instrument="GSSI SIR",
                    antenna_frequency_mhz=400,  # Often not in header
                    time_window_ns=time_window_ns,
                    samples_per_trace=samples_per_trace,
                    data=data,
                    time_ns=np.linspace(0, time_window_ns, samples_per_trace),
                    position_m=np.arange(traces) * 0.1,  # Approximate
                    file_source=filepath
                )
                return gpr

        except Exception as e:
            print(f"GSSI DZT parse error: {e}")

        return None


class SensorsSoftwareDT1Parser:
    """Sensors & Software DT1 format parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        return filepath.lower().endswith('.dt1')

    @staticmethod
    def parse(filepath: str) -> Optional[GPRData]:
        try:
            # Look for associated HD file
            hd_path = filepath.replace('.dt1', '.hd').replace('.DT1', '.HD')

            if not os.path.exists(hd_path):
                return None

            # Parse HD header
            with open(hd_path, 'r') as f:
                hd_lines = f.readlines()

            params = {}
            for line in hd_lines:
                if '=' in line:
                    key, val = line.split('=', 1)
                    params[key.strip()] = val.strip()

            # Parse DT1 data
            samples = int(params.get('NSAMP', 512))
            traces = int(params.get('NUMTRAC', 0))
            time_window = float(params.get('TIMEWINDOW', 100))
            freq = float(params.get('FREQUENCY', 100))

            data = np.fromfile(filepath, dtype='<i2')
            data = data.reshape(-1, samples)

            gpr = GPRData(
                timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                station_id=Path(filepath).stem,
                instrument="Sensors & Software",
                antenna_frequency_mhz=freq,
                time_window_ns=time_window,
                samples_per_trace=samples,
                data=data,
                file_source=filepath,
                metadata=params
            )
            return gpr

        except Exception as e:
            print(f"DT1 parse error: {e}")

        return None


# ============================================================================
# 8. GNSS/RTK DRIVERS (NMEA Serial/TCP)
# ============================================================================

class GNSSDriver:
    """GNSS/RTK receiver driver (NMEA over serial/TCP)"""

    def __init__(self, port: str = None, baudrate: int = 115200, host: str = None):
        self.port = port
        self.baudrate = baudrate
        self.host = host
        self.serial = None
        self.socket = None
        self.connected = False
        self.model = ""
        self.last_position = None

    def connect_serial(self) -> Tuple[bool, str]:
        if not DEPS.get('pyserial', False):
            return False, "pyserial not installed"

        try:
            import serial

            if not self.port:
                import serial.tools.list_ports
                ports = serial.tools.list_ports.comports()
                for p in ports:
                    if any(x in p.description.lower() for x in ['gps', 'gnss', 'ublox', 'trimble']):
                        self.port = p.device
                        break

            if not self.port:
                return False, "No GNSS receiver found"

            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=8,
                parity='N',
                stopbits=1,
                timeout=1
            )

            self.connected = True
            self.model = "GNSS Receiver"
            return True, f"Connected to {self.model} on {self.port}"

        except Exception as e:
            return False, str(e)

    def connect_tcp(self) -> Tuple[bool, str]:
        if not self.host:
            return False, "No host specified"

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if ':' in self.host:
                host, port = self.host.split(':')
                self.socket.connect((host, int(port)))
            else:
                self.socket.connect((self.host, 2101))  # Default NMEA port

            self.socket.settimeout(1)
            self.connected = True
            self.model = "GNSS Receiver (TCP)"
            return True, f"Connected to {self.host}"

        except Exception as e:
            return False, str(e)

    def disconnect(self):
        if self.serial and self.serial.is_open:
            self.serial.close()
        if self.socket:
            self.socket.close()
        self.connected = False

    def read_nmea(self) -> Optional[str]:
        """Read a single NMEA sentence"""
        if not self.connected:
            return None

        try:
            if self.serial:
                line = self.serial.readline().decode('ascii', errors='ignore').strip()
            else:
                line = self.socket.recv(1024).decode('ascii', errors='ignore').strip()

            return line

        except:
            return None

    def parse_position(self, nmea_line: str) -> Optional[GNSSPosition]:
        """Parse NMEA sentence to position"""
        if not nmea_line or not nmea_line.startswith('$'):
            return None

        if not HAS_NMEA:
            return None

        try:
            import pynmea2
            msg = pynmea2.parse(nmea_line)

            pos = GNSSPosition(
                timestamp=datetime.now(),
                station_id=f"GNSS_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                instrument=self.model,
                raw_nmea=nmea_line
            )

            if isinstance(msg, pynmea2.GGA):
                pos.latitude = msg.latitude
                pos.longitude = msg.longitude
                pos.altitude_m = msg.altitude
                pos.satellites = msg.num_sats
                pos.hdop = msg.horizontal_dop

                # Fix type
                if msg.gps_qual == 1:
                    pos.fix_type = "GPS"
                elif msg.gps_qual == 2:
                    pos.fix_type = "DGPS"
                elif msg.gps_qual == 4:
                    pos.fix_type = "RTK"
                elif msg.gps_qual == 5:
                    pos.fix_type = "RTK Float"
                else:
                    pos.fix_type = "none"

            elif isinstance(msg, pynmea2.RMC):
                pos.latitude = msg.latitude
                pos.longitude = msg.longitude
                pos.fix_type = "3D" if msg.status == 'A' else "none"

            elif isinstance(msg, pynmea2.GST):
                pos.horizontal_accuracy_m = msg.lat_std_dev
                pos.vertical_accuracy_m = msg.alt_std_dev

            return pos

        except Exception as e:
            print(f"NMEA parse error: {e}")

        return None

    def get_position(self) -> Optional[GNSSPosition]:
        """Get current position"""
        for _ in range(10):  # Try up to 10 lines
            line = self.read_nmea()
            if line:
                pos = self.parse_position(line)
                if pos and pos.latitude != 0:
                    self.last_position = pos
                    return pos
        return self.last_position


# ============================================================================
# 9. CAMPBELL SCIENTIFIC DRIVER (Modbus/ASCII)
# ============================================================================

class CampbellCRDriver:
    """Campbell Scientific CR-series datalogger driver"""

    def __init__(self, port: str = None, baudrate: int = 115200):
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
                    if 'campbell' in p.description.lower() or 'cr' in p.description.lower():
                        self.port = p.device
                        break

            if not self.port:
                return False, "No Campbell datalogger found"

            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=8,
                parity='N',
                stopbits=1,
                timeout=2
            )

            self.model = "Campbell CR"
            self.connected = True
            return True, f"Connected to {self.model} on {self.port}"

        except Exception as e:
            return False, str(e)

    def disconnect(self):
        if self.serial and self.serial.is_open:
            self.serial.close()
        self.connected = False

    def get_data(self) -> Optional[EnvironmentalGeophysicsData]:
        """Get current sensor data"""
        if not self.connected:
            return None

        try:
            # Send command (simplified)
            self.serial.write(b"DATA\r\n")
            response = self.serial.readline().decode().strip()

            # Parse CSV format
            parts = response.split(',')

            data = EnvironmentalGeophysicsData(
                timestamp=datetime.now(),
                station_id=f"CR_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                instrument=self.model
            )

            if len(parts) >= 5:
                data.temperature_c = float(parts[0])
                data.pressure_hpa = float(parts[1])
                data.humidity_pct = float(parts[2])
                data.wind_speed_ms = float(parts[3])
                data.wind_direction_deg = float(parts[4])

            return data

        except Exception as e:
            print(f"Campbell read error: {e}")

        return None


# ============================================================================
# PLOT EMBEDDER
# ============================================================================

class GeophysicsPlotEmbedder:
    """Plot geophysical data"""

    def __init__(self, canvas_widget, figure):
        self.canvas = canvas_widget
        self.figure = figure
        self.current_plot = None

    def clear(self):
        self.figure.clear()
        self.figure.set_facecolor('white')
        self.current_plot = None

    def plot_seismic(self, trace: SeismicTrace):
        """Plot seismic trace"""
        self.clear()
        ax = self.figure.add_subplot(111)

        if trace.data is not None:
            time = np.arange(len(trace.data)) / trace.sampling_rate
            ax.plot(time, trace.data, 'b-', linewidth=0.5)
            ax.set_xlabel('Time (s)')
            ax.set_ylabel('Amplitude')
            ax.set_title(f'{trace.station}.{trace.channel}')
            ax.grid(True, alpha=0.3)

        self.figure.tight_layout()
        self.canvas.draw()
        self.current_plot = 'seismic'

    def plot_ert_pseudosection(self, ert: ERTMeasurement):
        """Plot ERT pseudosection"""
        self.clear()
        ax = self.figure.add_subplot(111)

        if ert.resistance_ohm is not None and ert.x_m is not None:
            # Simplified pseudosection
            scatter = ax.scatter(ert.x_m, np.ones_like(ert.x_m) * 0.5,
                               c=ert.resistance_ohm, cmap='viridis', s=50)
            ax.set_xlabel('Distance (m)')
            ax.set_title('ERT Pseudosection')
            plt.colorbar(scatter, ax=ax, label='Resistance (Ω)')

        self.figure.tight_layout()
        self.canvas.draw()
        self.current_plot = 'ert'

    def plot_gpr_profile(self, gpr: GPRData):
        """Plot GPR profile"""
        self.clear()
        ax = self.figure.add_subplot(111)

        if gpr.data is not None:
            extent = [0, gpr.total_distance_m, gpr.time_window_ns, 0]
            ax.imshow(gpr.data.T, aspect='auto', extent=extent, cmap='gray')
            ax.set_xlabel('Distance (m)')
            ax.set_ylabel('Time (ns)')
            ax.set_title(f'GPR - {gpr.antenna_frequency_mhz} MHz')

        self.figure.tight_layout()
        self.canvas.draw()
        self.current_plot = 'gpr'

    def plot_magnetic_map(self, positions: List[Tuple[float, float, float]]):
        """Plot magnetic data on map"""
        self.clear()
        ax = self.figure.add_subplot(111)

        if positions:
            x = [p[0] for p in positions]
            y = [p[1] for p in positions]
            z = [p[2] for p in positions]

            scatter = ax.scatter(x, y, c=z, cmap='viridis', s=50)
            ax.set_xlabel('Easting (m)')
            ax.set_ylabel('Northing (m)')
            ax.set_title('Magnetic Field Map')
            ax.set_aspect('equal')
            plt.colorbar(scatter, ax=ax, label='Field (nT)')

        self.figure.tight_layout()
        self.canvas.draw()
        self.current_plot = 'magnetic'

    def plot_gravity_profile(self, gravity_data: List[GravityData]):
        """Plot gravity profile"""
        self.clear()
        ax = self.figure.add_subplot(111)

        stations = [g.station_id for g in gravity_data]
        gravity = [g.gravity_mgal for g in gravity_data if g.gravity_mgal]

        if gravity:
            ax.plot(range(len(gravity)), gravity, 'bo-')
            ax.set_xlabel('Station')
            ax.set_ylabel('Gravity (mGal)')
            ax.set_title('Gravity Profile')
            ax.grid(True, alpha=0.3)

        self.figure.tight_layout()
        self.canvas.draw()
        self.current_plot = 'gravity'


# ============================================================================
# MAIN PLUGIN - GEOPHYSICS UNIFIED SUITE
# ============================================================================
class GeophysicsUnifiedSuitePlugin:

    def __init__(self, main_app):
        self.app = main_app
        self.window = None
        self.ui_queue = None
        self.deps = DEPS

        # Hardware devices
        self.geonics = None
        self.gem = None
        self.gnss = None
        self.campbell = None
        self.connected_devices = []

        # Data
        self.seismic_traces: List[SeismicTrace] = []
        self.ert_measurements: List[ERTMeasurement] = []
        self.em_measurements: List[EMInductionData] = []
        self.mt_measurements: List[MTData] = []
        self.magnetic_measurements: List[MagneticData] = []
        self.gravity_measurements: List[GravityData] = []
        self.gpr_data: List[GPRData] = []
        self.gnss_positions: List[GNSSPosition] = []
        self.environmental_data: List[EnvironmentalGeophysicsData] = []

        self.current_seismic: Optional[SeismicTrace] = None
        self.current_gpr: Optional[GPRData] = None

        # Plot embedder
        self.plot_embedder = None

        # UI Variables
        self.status_var = tk.StringVar(value="Geophysics v1.0 - Ready")
        self.method_var = tk.StringVar(value="Seismic")
        self.file_count_var = tk.StringVar(value="No files loaded")

        # UI Elements
        self.notebook = None
        self.log_listbox = None
        self.plot_canvas = None
        self.plot_fig = None
        self.status_indicator = None
        self.method_combo = None
        self.tree = None
        self.import_btn = None
        self.batch_btn = None

        self.methods = [
            "Seismic",
            "ERT",
            "EM Induction",
            "Magnetotellurics (MT)",
            "Magnetics",
            "Gravity",
            "GPR",
            "GNSS/RTK",
            "Environmental"
        ]

    def show_interface(self):
        self.open_window()

    def open_window(self):
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("Geophysics Unified Suite v1.0")
        self.window.geometry("900x650")
        self.window.minsize(850, 600)
        self.window.transient(self.app.root)

        self.ui_queue = ThreadSafeUI(self.window)
        self._build_ui()
        self.window.lift()
        self.window.focus_force()
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        """900x650 UI"""

        # Header
        header = tk.Frame(self.window, bg="#2c3e50", height=40)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="🌍", font=("Arial", 16),
                bg="#2c3e50", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Label(header, text="GEOPHYSICS UNIFIED SUITE", font=("Arial", 12, "bold"),
                bg="#2c3e50", fg="white").pack(side=tk.LEFT)
        tk.Label(header, text="v1.0", font=("Arial", 8),
                bg="#2c3e50", fg="#f1c40f").pack(side=tk.LEFT, padx=5)

        self.status_indicator = tk.Label(header, textvariable=self.status_var,
                                        font=("Arial", 8), bg="#2c3e50", fg="white")
        self.status_indicator.pack(side=tk.RIGHT, padx=10)

        # Toolbar
        toolbar = tk.Frame(self.window, bg="#ecf0f1", height=80)
        toolbar.pack(fill=tk.X)
        toolbar.pack_propagate(False)

        row1 = tk.Frame(toolbar, bg="#ecf0f1")
        row1.pack(fill=tk.X, pady=2)

        tk.Label(row1, text="Method:", font=("Arial", 9, "bold"),
                bg="#ecf0f1").pack(side=tk.LEFT, padx=5)
        self.method_combo = ttk.Combobox(row1, textvariable=self.method_var,
                                        values=self.methods, width=20)
        self.method_combo.pack(side=tk.LEFT, padx=2)

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

        ttk.Button(row2, text="🧲 EM Connect",
                  command=self._connect_geonics, width=12).pack(side=tk.LEFT, padx=2)

        ttk.Button(row2, text="📡 GNSS Connect",
                  command=self._connect_gnss, width=12).pack(side=tk.LEFT, padx=2)

        ttk.Button(row2, text="🌡️ Campbell Connect",
                  command=self._connect_campbell, width=15).pack(side=tk.LEFT, padx=2)

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
            text=f"📊 {len(self.seismic_traces)} seismic · {len(self.gpr_data)} GPR · {len(self.gnss_positions)} GNSS",
            font=("Arial", 8), bg="#34495e", fg="white")
        self.count_label.pack(side=tk.LEFT, padx=5)

        tk.Label(status,
                text="Seismic · ERT · EM · MT · Magnetics · Gravity · GPR · GNSS",
                font=("Arial", 8), bg="#34495e", fg="#bdc3c7").pack(side=tk.RIGHT, padx=5)

    def _create_data_tab(self):
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="📊 Data")

        frame = tk.Frame(tab, bg="white")
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ('Type', 'Station', 'Instrument', 'Channel', 'Samples', 'File')
        self.tree = ttk.Treeview(frame, columns=columns, show='headings', height=15)

        col_widths = [80, 120, 150, 80, 80, 150]
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
        ttk.Button(ctrl_frame, text="🔍 Filter", command=self._filter_seismic,
                  width=8).pack(side=tk.LEFT, padx=2)

        plot_frame = tk.Frame(tab, bg="white")
        plot_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.plot_fig = Figure(figsize=(9, 5), dpi=90, facecolor='white')
        self.plot_canvas = FigureCanvasTkAgg(self.plot_fig, master=plot_frame)
        self.plot_canvas.draw()
        self.plot_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.plot_embedder = GeophysicsPlotEmbedder(self.plot_canvas, self.plot_fig)

        ax = self.plot_fig.add_subplot(111)
        ax.text(0.5, 0.5, 'Select data to plot', ha='center', va='center',
               transform=ax.transAxes, fontsize=12, color='#7f8c8d')
        ax.set_title('Geophysics Plot', fontweight='bold')
        ax.axis('off')
        self.plot_canvas.draw()

    def _create_hardware_tab(self):
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="⚡ Hardware")

        # EM Induction
        em_frame = tk.LabelFrame(tab, text="EM Induction (Geonics)", bg="white", font=("Arial", 9, "bold"))
        em_frame.pack(fill=tk.X, padx=5, pady=5)

        row1 = tk.Frame(em_frame, bg="white")
        row1.pack(fill=tk.X, pady=2)

        tk.Label(row1, text="Port:", font=("Arial", 8), bg="white").pack(side=tk.LEFT, padx=2)
        self.em_port_var = tk.StringVar(value="/dev/ttyUSB0" if IS_LINUX else "COM3")
        ttk.Entry(row1, textvariable=self.em_port_var, width=12).pack(side=tk.LEFT, padx=2)

        self.em_connect_btn = ttk.Button(row1, text="🔌 Connect",
                                         command=self._connect_geonics, width=10)
        self.em_connect_btn.pack(side=tk.LEFT, padx=5)

        self.em_status = tk.Label(row1, text="●", fg="red", font=("Arial", 10), bg="white")
        self.em_status.pack(side=tk.LEFT, padx=2)

        ttk.Button(em_frame, text="📊 Read Measurement",
                  command=self._read_em, width=20).pack(pady=2)

        # GNSS
        gnss_frame = tk.LabelFrame(tab, text="GNSS/RTK", bg="white", font=("Arial", 9, "bold"))
        gnss_frame.pack(fill=tk.X, padx=5, pady=5)

        row2 = tk.Frame(gnss_frame, bg="white")
        row2.pack(fill=tk.X, pady=2)

        tk.Label(row2, text="Port/IP:", font=("Arial", 8), bg="white").pack(side=tk.LEFT, padx=2)
        self.gnss_port_var = tk.StringVar(value="/dev/ttyUSB1" if IS_LINUX else "COM4")
        ttk.Entry(row2, textvariable=self.gnss_port_var, width=15).pack(side=tk.LEFT, padx=2)

        ttk.Radiobutton(row2, text="Serial", variable=tk.StringVar(value="serial"),
                       value="serial").pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(row2, text="TCP", variable=tk.StringVar(value="tcp"),
                       value="tcp").pack(side=tk.LEFT, padx=2)

        self.gnss_connect_btn = ttk.Button(row2, text="🔌 Connect",
                                           command=self._connect_gnss, width=10)
        self.gnss_connect_btn.pack(side=tk.LEFT, padx=5)

        self.gnss_status = tk.Label(row2, text="●", fg="red", font=("Arial", 10), bg="white")
        self.gnss_status.pack(side=tk.LEFT, padx=2)

        ttk.Button(gnss_frame, text="📡 Get Position",
                  command=self._get_gnss_position, width=15).pack(pady=2)

        # Campbell
        camp_frame = tk.LabelFrame(tab, text="Campbell Datalogger", bg="white", font=("Arial", 9, "bold"))
        camp_frame.pack(fill=tk.X, padx=5, pady=5)

        row3 = tk.Frame(camp_frame, bg="white")
        row3.pack(fill=tk.X, pady=2)

        tk.Label(row3, text="Port:", font=("Arial", 8), bg="white").pack(side=tk.LEFT, padx=2)
        self.camp_port_var = tk.StringVar(value="/dev/ttyUSB2" if IS_LINUX else "COM5")
        ttk.Entry(row3, textvariable=self.camp_port_var, width=12).pack(side=tk.LEFT, padx=2)

        self.camp_connect_btn = ttk.Button(row3, text="🔌 Connect",
                                           command=self._connect_campbell, width=10)
        self.camp_connect_btn.pack(side=tk.LEFT, padx=5)

        self.camp_status = tk.Label(row3, text="●", fg="red", font=("Arial", 10), bg="white")
        self.camp_status.pack(side=tk.LEFT, padx=2)

        ttk.Button(camp_frame, text="📊 Read Data",
                  command=self._read_campbell, width=15).pack(pady=2)

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
        filetypes = [
            ("All supported", "*.mseed;*.miniseed;*.sac;*.csv;*.txt;*.edi;*.dzt;*.dt1"),
            ("Seismic", "*.mseed;*.miniseed;*.sac"),
            ("ERT", "*.csv;*.txt"),
            ("EDI", "*.edi"),
            ("GPR", "*.dzt;*.dt1"),
            ("All files", "*.*")
        ]

        path = filedialog.askopenfilename(filetypes=filetypes)
        if not path:
            return

        self._update_status(f"Parsing {Path(path).name}...", "#f39c12")
        self.import_btn.config(state='disabled')

        def parse_thread():
            result = None
            data_type = "Unknown"

            # Try seismic
            traces = ObsPySeismicParser.parse(path)
            if traces:
                self.seismic_traces.extend(traces)
                self.current_seismic = traces[0]
                data_type = "Seismic"
                result = traces[0]

            # Try ERT
            if not result:
                for parser in [ABEMTerrameterParser, IRISSyscalParser, ZongeGDPParser]:
                    if hasattr(parser, 'can_parse') and parser.can_parse(path):
                        ert = parser.parse(path)
                        if ert:
                            self.ert_measurements.append(ert)
                            data_type = "ERT"
                            result = ert
                            break

            # Try EDI
            if not result and EDIParser.can_parse(path):
                mt = EDIParser.parse(path)
                if mt:
                    self.mt_measurements.append(mt)
                    data_type = "MT"
                    result = mt

            # Try Magnetics
            if not result:
                for parser in [BartingtonGrad601Parser, GeometricsG858Parser]:
                    if hasattr(parser, 'can_parse') and parser.can_parse(path):
                        mags = parser.parse(path)
                        if mags:
                            self.magnetic_measurements.extend(mags)
                            data_type = "Magnetics"
                            result = mags[0]
                            break

            # Try Gravity
            if not result and ScintrexCGParser.can_parse(path):
                gravs = ScintrexCGParser.parse(path)
                if gravs:
                    self.gravity_measurements.extend(gravs)
                    data_type = "Gravity"
                    result = gravs[0]

            # Try GPR
            if not result:
                for parser in [GSSIDZTParser, SensorsSoftwareDT1Parser]:
                    if hasattr(parser, 'can_parse') and parser.can_parse(path):
                        gpr = parser.parse(path)
                        if gpr:
                            self.gpr_data.append(gpr)
                            self.current_gpr = gpr
                            data_type = "GPR"
                            result = gpr
                            break

            def update_ui():
                self.import_btn.config(state='normal')
                if result:
                    self._update_tree()
                    self.file_count_var.set(f"Files: {len(self.seismic_traces)+len(self.gpr_data)}")
                    self.count_label.config(
                        text=f"📊 {len(self.seismic_traces)} seismic · {len(self.gpr_data)} GPR · {len(self.gnss_positions)} GNSS")
                    self._add_to_log(f"✅ Imported {data_type}: {Path(path).name}")

                    # Auto-plot
                    if self.plot_embedder:
                        if isinstance(result, SeismicTrace):
                            self.plot_embedder.plot_seismic(result)
                        elif isinstance(result, GPRData):
                            self.plot_embedder.plot_gpr_profile(result)
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
            seismic_count = 0
            gpr_count = 0

            for ext in ['*.mseed', '*.miniseed', '*.sac', '*.dzt', '*.dt1']:
                for filepath in Path(folder).glob(ext):
                    # Try seismic
                    traces = ObsPySeismicParser.parse(str(filepath))
                    if traces:
                        self.seismic_traces.extend(traces)
                        seismic_count += len(traces)
                        continue

                    # Try GPR
                    gpr = GSSIDZTParser.parse(str(filepath))
                    if gpr:
                        self.gpr_data.append(gpr)
                        gpr_count += 1

            def update_ui():
                self._update_tree()
                self.file_count_var.set(f"Files: {seismic_count+gpr_count}")
                self.count_label.config(
                    text=f"📊 {len(self.seismic_traces)} seismic · {len(self.gpr_data)} GPR · {len(self.gnss_positions)} GNSS")
                self._add_to_log(f"📁 Batch imported: {seismic_count} seismic, {gpr_count} GPR")
                self._update_status(f"✅ Imported {seismic_count+gpr_count} files")
                self.import_btn.config(state='normal')
                self.batch_btn.config(state='normal')

            self.ui_queue.schedule(update_ui)

        threading.Thread(target=batch_thread, daemon=True).start()

    def _update_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Seismic
        for trace in self.seismic_traces[-20:]:
            self.tree.insert('', 0, values=(
                "Seismic",
                trace.station,
                trace.instrument[:15],
                trace.channel,
                str(trace.npts),
                Path(trace.file_source).name if trace.file_source else ""
            ))

        # GPR
        for gpr in self.gpr_data[-10:]:
            self.tree.insert('', 0, values=(
                "GPR",
                gpr.station_id,
                gpr.instrument[:15],
                f"{gpr.antenna_frequency_mhz:.0f} MHz",
                str(gpr.data.shape[0]) if gpr.data is not None else "0",
                Path(gpr.file_source).name if gpr.file_source else ""
            ))

    def _on_tree_double_click(self, event):
        self._plot_selected()

    def _plot_selected(self):
        if self.seismic_traces and self.plot_embedder:
            self.plot_embedder.plot_seismic(self.seismic_traces[-1])

    def _refresh_plot(self):
        if self.current_seismic and self.plot_embedder:
            self.plot_embedder.plot_seismic(self.current_seismic)

    def _save_plot(self):
        if not self.plot_fig:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("PDF", "*.pdf"), ("SVG", "*.svg")],
            initialfile=f"geophysics_plot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        )
        if path:
            self.plot_fig.savefig(path, dpi=300, bbox_inches='tight')
            self._add_to_log(f"💾 Plot saved: {Path(path).name}")

    def _filter_seismic(self):
        """Apply bandpass filter to seismic trace"""
        if not self.current_seismic or not HAS_OBSPY:
            return

        self.current_seismic.filter(freqmin=1, freqmax=10)
        self._add_to_log("✅ Applied 1-10 Hz bandpass filter")
        self._refresh_plot()

    # ============================================================================
    # HARDWARE CONTROL METHODS
    # ============================================================================

    def _connect_geonics(self):
        port = self.em_port_var.get()

        def connect_thread():
            self.geonics = GeonicsEMDriver(port=port)
            success, msg = self.geonics.connect()

            def update_ui():
                if success:
                    self.connected_devices.append(self.geonics)
                    self.em_status.config(fg="#2ecc71")
                    self.em_connect_btn.config(text="✅ Connected")
                    self._add_to_log(f"🔌 EM connected: {msg}")
                else:
                    self.em_status.config(fg="red")
                    self.em_connect_btn.config(text="🔌 Connect")
                    self._add_to_log(f"❌ EM connection failed: {msg}")

            self.ui_queue.schedule(update_ui)

        threading.Thread(target=connect_thread, daemon=True).start()

    def _read_em(self):
        if not self.geonics or not self.geonics.connected:
            return

        def read_thread():
            data = self.geonics.read_measurement()

            def update_ui():
                if data:
                    self.em_measurements.append(data)
                    self._add_to_log(f"✅ EM: Cond={data.apparent_conductivity_ms_m:.2f} mS/m")
                else:
                    self._add_to_log("❌ Failed to read EM")

            self.ui_queue.schedule(update_ui)

        threading.Thread(target=read_thread, daemon=True).start()

    def _connect_gnss(self):
        port = self.gnss_port_var.get()

        def connect_thread():
            self.gnss = GNSSDriver(port=port)
            success, msg = self.gnss.connect_serial()

            def update_ui():
                if success:
                    self.connected_devices.append(self.gnss)
                    self.gnss_status.config(fg="#2ecc71")
                    self.gnss_connect_btn.config(text="✅ Connected")
                    self._add_to_log(f"🔌 GNSS connected: {msg}")
                else:
                    self.gnss_status.config(fg="red")
                    self.gnss_connect_btn.config(text="🔌 Connect")
                    self._add_to_log(f"❌ GNSS connection failed: {msg}")

            self.ui_queue.schedule(update_ui)

        threading.Thread(target=connect_thread, daemon=True).start()

    def _get_gnss_position(self):
        if not self.gnss or not self.gnss.connected:
            return

        def read_thread():
            pos = self.gnss.get_position()

            def update_ui():
                if pos:
                    self.gnss_positions.append(pos)
                    self._add_to_log(f"✅ GNSS: {pos.latitude:.6f}, {pos.longitude:.6f} ({pos.fix_type})")
                else:
                    self._add_to_log("❌ Failed to get GNSS position")

            self.ui_queue.schedule(update_ui)

        threading.Thread(target=read_thread, daemon=True).start()

    def _connect_campbell(self):
        port = self.camp_port_var.get()

        def connect_thread():
            self.campbell = CampbellCRDriver(port=port)
            success, msg = self.campbell.connect()

            def update_ui():
                if success:
                    self.connected_devices.append(self.campbell)
                    self.camp_status.config(fg="#2ecc71")
                    self.camp_connect_btn.config(text="✅ Connected")
                    self._add_to_log(f"🔌 Campbell connected: {msg}")
                else:
                    self.camp_status.config(fg="red")
                    self.camp_connect_btn.config(text="🔌 Connect")
                    self._add_to_log(f"❌ Campbell connection failed: {msg}")

            self.ui_queue.schedule(update_ui)

        threading.Thread(target=connect_thread, daemon=True).start()

    def _read_campbell(self):
        if not self.campbell or not self.campbell.connected:
            return

        def read_thread():
            data = self.campbell.get_data()

            def update_ui():
                if data:
                    self.environmental_data.append(data)
                    self._add_to_log(f"✅ Campbell: T={data.temperature_c:.1f}°C, P={data.pressure_hpa:.1f}hPa")
                else:
                    self._add_to_log("❌ Failed to read Campbell")

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
        for trace in self.seismic_traces:
            data.append(trace.to_dict())
        for gpr in self.gpr_data:
            data.append(gpr.to_dict())
        for pos in self.gnss_positions:
            data.append(pos.to_dict())

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
        for trace in self.seismic_traces:
            data.append(trace.to_dict())
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
    plugin = GeophysicsUnifiedSuitePlugin(main_app)

    # Add to left panel if available
    if hasattr(main_app, 'left') and main_app.left is not None:
        main_app.left.add_hardware_button(
            name=PLUGIN_INFO.get("name", "Geophysics Suite"),
            icon=PLUGIN_INFO.get("icon", "🌍"),
            command=plugin.show_interface
        )
        print(f"✅ Added: {PLUGIN_INFO.get('name')}")

    return plugin
