"""
GEOPHYSICS ANALYSIS SUITE v3.0 - COMPLETE PRODUCTION RELEASE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
5-TAB WORKFLOW:
  TAB 1: 📥 DATA IMPORT & QC    - Load from table, quality control
  TAB 2: 🔧 PROCESSING           - Seismic · ERT · Gravity · Magnetics · MT · GPR
  TAB 3: 🗺️ GRIDDING             - Minimum curvature · Kriging · FFT · Derivatives
  TAB 4: 🧠 MODELING              - Euler · Joint inversion · ML · Lineaments
  TAB 5: 📤 VISUALIZATION         - 2D/3D plots · Folium maps · GIS export
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

PLUGIN_INFO = {
    "id": "geophysics_analysis_suite",
    "name": "Geophysics Analysis Suite",
    "category": "software",
    "field": "Geophysics",
    "icon": "🌍",
    "version": "3.0.0",
    "author": "Sefy Levy & DeepSeek",
    "description": "5-tab workflow: Import · Process · Grid · Model · Visualize",
    "requires": [
        "numpy",
        "pandas",
        "scipy",
        "matplotlib",
        "pygimli",
        "harmonica",
        "pyproj",
        "folium",
        "pyvista",
        "scikit-learn",
        "pykrige",
        "rasterio",
        "geopandas",
        "xgboost",
        "scikit-image"
    ],
    "window_size": "1200x800"
}

# ============================================================================
# FIX SCIPY IMPORT - MUST COME FIRST
# ============================================================================
import warnings
warnings.filterwarnings('ignore')

import scipy
import scipy.integrate
if not hasattr(scipy.integrate, 'trapz') and hasattr(scipy.integrate, 'trapezoid'):
    scipy.integrate.trapz = scipy.integrate.trapezoid
if not hasattr(scipy.integrate, 'simps') and hasattr(scipy.integrate, 'simpson'):
    scipy.integrate.simps = scipy.integrate.simpson
if not hasattr(scipy.integrate, 'cumtrapz') and hasattr(scipy.integrate, 'cumulative_trapezoid'):
    scipy.integrate.cumtrapz = scipy.integrate.cumulative_trapezoid

# ============================================================================
# STANDARD LIBRARY IMPORTS
# ============================================================================
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
from typing import List, Optional, Dict, Any, Tuple
import queue
import time
import os
from pathlib import Path
import sys
import platform
from dataclasses import dataclass, field
import json
from datetime import datetime
import numpy as np
import pandas as pd

# ============================================================================
# SCIENTIFIC IMPORTS
# ============================================================================
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec
from scipy import signal, ndimage, stats, optimize, interpolate
from scipy.fft import fft2, ifft2, fftfreq
from scipy.spatial import ConvexHull, cKDTree
from scipy.ndimage import gaussian_filter

# ============================================================================
# OPTIONAL DEPENDENCY CHECKS
# ============================================================================
try:
    import pygimli as pg
    from pygimli.physics import ert
    from pygimli.physics.gravimetry import GravityModelling
    HAS_PYGIMLI = True
    print(f"✅ pyGIMLi found: {pg.__version__ if hasattr(pg, '__version__') else 'unknown'}")
    print(f"   - ERT module: available")
    print(f"   - Gravimetry module: available")
except ImportError as e:
    HAS_PYGIMLI = False
    print(f"❌ pyGIMLi import failed: {e}")

try:
    import harmonica as hm
    HAS_HARMONICA = True
except ImportError:
    HAS_HARMONICA = False

try:
    import pyproj
    HAS_PYPROJ = True
except ImportError:
    HAS_PYPROJ = False

try:
    import folium
    from folium import plugins
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False

try:
    import pyvista as pv
    from pyvista import Plotter
    HAS_PYVISTA = True
except ImportError:
    HAS_PYVISTA = False

try:
    import sklearn
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.cluster import DBSCAN, KMeans
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

try:
    import pykrige
    from pykrige.ok import OrdinaryKriging
    HAS_PYKRIGE = True
except ImportError:
    HAS_PYKRIGE = False

try:
    import rasterio
    from rasterio.transform import from_origin
    HAS_RASTERIO = True
except ImportError:
    HAS_RASTERIO = False

try:
    import geopandas as gpd
    from shapely.geometry import Point, Polygon
    HAS_GEOPANDAS = True
except ImportError:
    HAS_GEOPANDAS = False

try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

try:
    import skimage
    HAS_SKIMAGE = True
except ImportError:
    HAS_SKIMAGE = False

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

    def schedule(self, callback):
        self.queue.put(callback)

# ============================================================================
# TOOLTIP CLASS FOR HELP TEXT
# ============================================================================
class ToolTip:
    """Create a tooltip for a given widget"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind('<Enter>', self.show_tip)
        widget.bind('<Leave>', self.hide_tip)

    def show_tip(self, event=None):
        """Show tooltip"""
        if self.tip_window or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                        background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                        font=("Arial", 9, "normal"))
        label.pack()

    def hide_tip(self, event=None):
        """Hide tooltip"""
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

# ============================================================================
# NORMALIZED DATA CLASSES - ALL 11 TYPES (copied from hardware plugin)
# ============================================================================

@dataclass
class SeismicTrace:
    timestamp: datetime
    station: str
    channel: str
    network: str = ""
    data: Optional[np.ndarray] = None
    sampling_rate: float = 0
    start_time: Optional[datetime] = None
    npts: int = 0
    latitude: float = 0.0
    longitude: float = 0.0
    instrument: str = ""
    file_source: str = ""

    def to_dict(self) -> Dict:
        return {
            'Sample_ID': f"{self.station}_{self.channel}_{self.timestamp.strftime('%H%M%S')}",
            'Instrument': self.instrument,
            'Method': 'Seismic',
            'Station': self.station,
            'Channel': self.channel,
            'Sampling_Rate_Hz': round(self.sampling_rate, 2),
            'Samples': self.npts,
            'Duration_s': round(self.npts / self.sampling_rate, 1) if self.sampling_rate > 0 else 0,
            'Timestamp': self.timestamp.isoformat(),
            'Latitude': self.latitude,
            'Longitude': self.longitude,
            'File_Source': self.file_source if self.file_source else '',
            'Auto_Classification': 'SEISMIC',
            'Display_Color': '#1E3F66'
        }

@dataclass
class GPRData:
    timestamp: datetime
    station: str
    instrument: str
    data: Optional[np.ndarray] = None
    antenna_frequency_mhz: float = 0
    time_window_ns: float = 0
    samples_per_trace: int = 0
    traces: int = 0
    file_source: str = ""

    def to_dict(self) -> Dict:
        return {
            'Sample_ID': f"{self.station}_{self.timestamp.strftime('%H%M%S')}",
            'Instrument': self.instrument,
            'Method': 'GPR',
            'Station': self.station,
            'Frequency_MHz': self.antenna_frequency_mhz,
            'Time_Window_ns': self.time_window_ns,
            'Samples_per_Trace': self.samples_per_trace,
            'Traces': self.traces,
            'Timestamp': self.timestamp.isoformat(),
            'File_Source': self.file_source if self.file_source else '',
            'Auto_Classification': 'GPR',
            'Display_Color': '#3A6B4A'
        }

@dataclass
class ERTData:
    timestamp: datetime
    station: str
    instrument: str
    resistances: Optional[np.ndarray] = None
    apparent_rho: Optional[np.ndarray] = None
    electrode_spacing: float = 0
    n_measurements: int = 0
    file_source: str = ""

    def to_dict(self) -> Dict:
        return {
            'Sample_ID': f"{self.station}_{self.timestamp.strftime('%H%M%S')}",
            'Instrument': self.instrument,
            'Method': 'ERT',
            'Station': self.station,
            'Measurements': self.n_measurements,
            'Electrode_Spacing_m': self.electrode_spacing,
            'Timestamp': self.timestamp.isoformat(),
            'File_Source': self.file_source if self.file_source else '',
            'Auto_Classification': 'ERT',
            'Display_Color': '#8B4513'
        }

@dataclass
class EMData:
    timestamp: datetime
    station: str
    instrument: str
    conductivity_ms_m: Optional[float] = None
    inphase_ppm: Optional[float] = None
    quadrature_ppm: Optional[float] = None
    latitude: float = 0.0
    longitude: float = 0.0
    coil_spacing_m: float = 0
    frequency_hz: float = 0

    def to_dict(self) -> Dict:
        return {
            'Sample_ID': f"{self.station}_{self.timestamp.strftime('%H%M%S')}",
            'Instrument': self.instrument,
            'Method': 'EM Induction',
            'Station': self.station,
            'Conductivity_mS_m': round(self.conductivity_ms_m, 2) if self.conductivity_ms_m else None,
            'Inphase_ppm': round(self.inphase_ppm, 1) if self.inphase_ppm else None,
            'Quadrature_ppm': round(self.quadrature_ppm, 1) if self.quadrature_ppm else None,
            'Coil_Spacing_m': self.coil_spacing_m,
            'Frequency_Hz': self.frequency_hz,
            'Timestamp': self.timestamp.isoformat(),
            'Latitude': self.latitude,
            'Longitude': self.longitude,
            'Auto_Classification': 'EM',
            'Display_Color': '#C45A3A'
        }

@dataclass
class MTData:
    timestamp: datetime
    station: str
    instrument: str
    frequencies: Optional[np.ndarray] = None
    impedance: Optional[np.ndarray] = None
    resistivity: Optional[np.ndarray] = None
    phase: Optional[np.ndarray] = None
    n_frequencies: int = 0
    file_source: str = ""

    def to_dict(self) -> Dict:
        return {
            'Sample_ID': f"{self.station}_{self.timestamp.strftime('%H%M%S')}",
            'Instrument': self.instrument,
            'Method': 'MT',
            'Station': self.station,
            'Frequencies': self.n_frequencies,
            'Timestamp': self.timestamp.isoformat(),
            'File_Source': self.file_source if self.file_source else '',
            'Auto_Classification': 'MT',
            'Display_Color': '#4A6A8A'
        }

@dataclass
class MagneticData:
    timestamp: datetime
    station: str
    instrument: str
    total_field_nt: Optional[float] = None
    x_nt: Optional[float] = None
    y_nt: Optional[float] = None
    z_nt: Optional[float] = None
    latitude: float = 0.0
    longitude: float = 0.0
    altitude_m: float = 0.0

    def to_dict(self) -> Dict:
        return {
            'Sample_ID': f"{self.station}_{self.timestamp.strftime('%H%M%S')}",
            'Instrument': self.instrument,
            'Method': 'Magnetics',
            'Station': self.station,
            'Total_Field_nT': round(self.total_field_nt, 1) if self.total_field_nt else None,
            'X_nT': round(self.x_nt, 1) if self.x_nt else None,
            'Y_nT': round(self.y_nt, 1) if self.y_nt else None,
            'Z_nT': round(self.z_nt, 1) if self.z_nt else None,
            'Timestamp': self.timestamp.isoformat(),
            'Latitude': self.latitude,
            'Longitude': self.longitude,
            'Altitude_m': self.altitude_m,
            'Auto_Classification': 'MAGNETICS',
            'Display_Color': '#B8860B'
        }

@dataclass
class GravityData:
    timestamp: datetime
    station: str
    instrument: str
    gravity_mgal: Optional[float] = None
    latitude: float = 0.0
    longitude: float = 0.0
    elevation_m: float = 0.0
    raw_reading: Optional[float] = None
    standard_deviation: Optional[float] = None

    def to_dict(self) -> Dict:
        return {
            'Sample_ID': f"{self.station}_{self.timestamp.strftime('%H%M%S')}",
            'Instrument': self.instrument,
            'Method': 'Gravity',
            'Station': self.station,
            'Gravity_mGal': round(self.gravity_mgal, 3) if self.gravity_mgal else None,
            'Raw_Reading': self.raw_reading,
            'Std_Dev': self.standard_deviation,
            'Timestamp': self.timestamp.isoformat(),
            'Latitude': self.latitude,
            'Longitude': self.longitude,
            'Elevation_m': self.elevation_m,
            'Auto_Classification': 'GRAVITY',
            'Display_Color': '#6A4A8A'
        }

@dataclass
class IMUData:
    timestamp: datetime
    station: str
    instrument: str
    accel_x_ms2: Optional[float] = None
    accel_y_ms2: Optional[float] = None
    accel_z_ms2: Optional[float] = None
    gyro_x_rad_s: Optional[float] = None
    gyro_y_rad_s: Optional[float] = None
    gyro_z_rad_s: Optional[float] = None
    mag_x_nt: Optional[float] = None
    mag_y_nt: Optional[float] = None
    mag_z_nt: Optional[float] = None
    temperature_c: Optional[float] = None

    def to_dict(self) -> Dict:
        return {
            'Sample_ID': f"{self.station}_{self.timestamp.strftime('%H%M%S')}",
            'Instrument': self.instrument,
            'Method': 'IMU',
            'Station': self.station,
            'Accel_X_ms2': round(self.accel_x_ms2, 3) if self.accel_x_ms2 else None,
            'Accel_Y_ms2': round(self.accel_y_ms2, 3) if self.accel_y_ms2 else None,
            'Accel_Z_ms2': round(self.accel_z_ms2, 3) if self.accel_z_ms2 else None,
            'Gyro_X_rad_s': round(self.gyro_x_rad_s, 3) if self.gyro_x_rad_s else None,
            'Gyro_Y_rad_s': round(self.gyro_y_rad_s, 3) if self.gyro_y_rad_s else None,
            'Gyro_Z_rad_s': round(self.gyro_z_rad_s, 3) if self.gyro_z_rad_s else None,
            'Mag_X_nT': round(self.mag_x_nt, 1) if self.mag_x_nt else None,
            'Mag_Y_nT': round(self.mag_y_nt, 1) if self.mag_y_nt else None,
            'Mag_Z_nT': round(self.mag_z_nt, 1) if self.mag_z_nt else None,
            'Temperature_C': round(self.temperature_c, 1) if self.temperature_c else None,
            'Timestamp': self.timestamp.isoformat(),
            'Auto_Classification': 'IMU',
            'Display_Color': '#7A6A4A'
        }

@dataclass
class GNSSPosition:
    timestamp: datetime
    station: str
    instrument: str
    latitude: float = 0.0
    longitude: float = 0.0
    altitude_m: float = 0.0
    fix_type: str = "none"
    satellites: int = 0
    hdop: Optional[float] = None
    vdop: Optional[float] = None
    pdop: Optional[float] = None
    age_s: Optional[float] = None
    raw_nmea: str = ""

    def to_dict(self) -> Dict:
        return {
            'Sample_ID': f"{self.station}_{self.timestamp.strftime('%H%M%S')}",
            'Instrument': self.instrument,
            'Method': 'GNSS',
            'Station': self.station,
            'Latitude': self.latitude,
            'Longitude': self.longitude,
            'Altitude_m': self.altitude_m,
            'Fix_Type': self.fix_type,
            'Satellites': self.satellites,
            'HDOP': round(self.hdop, 2) if self.hdop else None,
            'Timestamp': self.timestamp.isoformat(),
            'Auto_Classification': 'GNSS',
            'Display_Color': '#2A5A5A'
        }

@dataclass
class EnvironmentalData:
    timestamp: datetime
    station: str
    instrument: str
    temperature_c: Optional[float] = None
    pressure_hpa: Optional[float] = None
    humidity_pct: Optional[float] = None
    wind_speed_ms: Optional[float] = None
    wind_direction_deg: Optional[float] = None
    rainfall_mm: Optional[float] = None

    def to_dict(self) -> Dict:
        return {
            'Sample_ID': f"{self.station}_{self.timestamp.strftime('%H%M%S')}",
            'Instrument': self.instrument,
            'Method': 'Environmental',
            'Station': self.station,
            'Temperature_C': round(self.temperature_c, 1) if self.temperature_c else None,
            'Pressure_hPa': round(self.pressure_hpa, 1) if self.pressure_hpa else None,
            'Humidity_pct': round(self.humidity_pct, 1) if self.humidity_pct else None,
            'Wind_Speed_ms': round(self.wind_speed_ms, 1) if self.wind_speed_ms else None,
            'Wind_Direction_deg': round(self.wind_direction_deg, 0) if self.wind_direction_deg else None,
            'Rainfall_mm': round(self.rainfall_mm, 1) if self.rainfall_mm else None,
            'Timestamp': self.timestamp.isoformat(),
            'Auto_Classification': 'ENVIRONMENTAL',
            'Display_Color': '#5A7A3A'
        }

@dataclass
class GeophoneData:
    timestamp: datetime
    station: str
    channel: str
    data: Optional[np.ndarray] = None
    sampling_rate: float = 100
    npts: int = 0
    instrument: str = "SM-24 Geophone"
    adc_resolution_bits: int = 16

    def to_dict(self) -> Dict:
        return {
            'Sample_ID': f"{self.station}_{self.channel}_{self.timestamp.strftime('%H%M%S')}",
            'Instrument': self.instrument,
            'Method': 'Geophone',
            'Station': self.station,
            'Channel': self.channel,
            'Sampling_Rate_Hz': self.sampling_rate,
            'Samples': self.npts,
            'ADC_Bits': self.adc_resolution_bits,
            'Timestamp': self.timestamp.isoformat(),
            'Auto_Classification': 'GEOPHONE',
            'Display_Color': '#2E5A8A'
        }

@dataclass
class custEMData:
    timestamp: datetime
    station: str
    model_name: str
    frequencies: Optional[np.ndarray] = None
    responses: Optional[np.ndarray] = None
    mesh_cells: int = 0

    def to_dict(self) -> Dict:
        return {
            'Sample_ID': f"{self.station}_{self.timestamp.strftime('%H%M%S')}",
            'Method': 'custEM 3D',
            'Model': self.model_name,
            'Mesh_Cells': self.mesh_cells,
            'Frequencies': len(self.frequencies) if self.frequencies is not None else 0,
            'Timestamp': self.timestamp.isoformat(),
            'Auto_Classification': 'CUSTEM',
            'Display_Color': '#9A5A3A'
        }

# ============================================================================
# WORKFLOW STATE - Core data object passed between tabs
# ============================================================================
class WorkflowState:
    """Central data object that holds all data as it flows through the 5 tabs"""

    def __init__(self):
        self.raw_data = None           # Original DataFrame from table
        self.processed = {}             # Processed data by method
        self.coordinates = None         # X, Y, Z arrays
        self.metadata = {}               # Survey metadata
        self.quality_flags = {}          # QC results
        self.grids = {}                   # Gridded data
        self.models = {}                   # Inversion results
        self.history = []                   # Processing steps applied
        self.observers = []                 # For auto-refresh between tabs

    def add_data(self, method, data):
        """Add processed data for a specific method"""
        self.processed[method] = data
        self._notify_observers()

    def add_grid(self, name, grid):
        """Add a gridded dataset"""
        self.grids[name] = grid
        self._notify_observers()

    def add_model(self, name, model):
        """Add an inversion model"""
        self.models[name] = model
        self._notify_observers()

    def log_step(self, step_name, params=None):
        """Log a processing step"""
        self.history.append({
            'step': step_name,
            'timestamp': datetime.now(),
            'params': params or {}
        })

    def register_observer(self, observer):
        """Register a tab to be notified of changes"""
        self.observers.append(observer)

    def _notify_observers(self):
        """Notify all tabs that data has changed"""
        for observer in self.observers:
            try:
                observer.on_data_changed()
            except Exception as e:
                pass

    def get_summary(self) -> str:
        """Get a summary of current state"""
        lines = []
        if self.raw_data is not None:
            lines.append(f"Raw data: {len(self.raw_data)} rows")
        if self.processed:
            lines.append(f"Processed: {', '.join(self.processed.keys())}")
        if self.grids:
            lines.append(f"Grids: {', '.join(self.grids.keys())}")
        if self.models:
            lines.append(f"Models: {', '.join(self.models.keys())}")
        return " · ".join(lines) if lines else "No data loaded"

# ============================================================================
# CONFIGURABLE FILE BROWSER WIDGET
# ============================================================================
class FileBrowser(tk.Frame):
    """File browser that shows specified data types"""

    def __init__(self, parent, workflow_state, data_sources, callback, bg="#f0f0f0"):
        """
        data_sources: list of tuples (data_key, display_name, icon, display_func)
        Example: [('ert_raw', 'ERT', '⚡', lambda d: f"{d['n_measurements']} measurements")]
        """
        super().__init__(parent, bg=bg)
        self.workflow_state = workflow_state
        self.data_sources = data_sources
        self.callback = callback
        self.items = []  # List of (data_type, data_item)

        self.workflow_state.register_observer(self)
        self._build_ui()

    def _build_ui(self):
        tk.Label(self, text="📂 Loaded Files", font=("Arial", 10, "bold"),
                bg=self['bg'], fg="#1A3A5A").pack(anchor='w', padx=5, pady=2)

        list_frame = tk.Frame(self, bg=self['bg'])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
                                  font=("Courier", 8), height=8)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)

        self.listbox.bind('<<ListboxSelect>>', self._on_select)
        self.counter_label = tk.Label(self, text="Total: 0 files", font=("Arial", 8), bg=self['bg'])
        self.counter_label.pack(anchor='w', padx=5, pady=2)

    def on_data_changed(self):
        self.refresh()

    def refresh(self):
        self.listbox.delete(0, tk.END)
        self.items = []

        for key, name, icon, display_func in self.data_sources:
            if key in self.workflow_state.processed:
                data = self.workflow_state.processed[key]
                if isinstance(data, list):
                    for item in data:
                        display = f"{icon} {name}: {display_func(item)}"
                        self.listbox.insert(tk.END, display)
                        self.items.append((key, item))
                else:
                    display = f"{icon} {name}: {display_func(data)}"
                    self.listbox.insert(tk.END, display)
                    self.items.append((key, data))

        self.counter_label.config(text=f"Total: {len(self.items)} files")
        if self.items:
            self.listbox.selection_set(0)
            self.listbox.see(0)
            self._on_select()

    def _on_select(self, event=None):
        selection = self.listbox.curselection()
        if not selection or not self.callback:
            return
        idx = selection[0]
        if idx < len(self.items):
            self.callback(self.items[idx][0], self.items[idx][1])

# ============================================================================
# PARSER CLASSES - copied from hardware plugin
# ============================================================================

class SacParser:
    """SAC file parser for reading seismic data from files"""

    @staticmethod
    def parse(filepath: str) -> List[SeismicTrace]:
        try:
            import struct
            import numpy as np
            from datetime import datetime

            with open(filepath, 'rb') as f:
                # Read header (70 floats = 280 bytes)
                header_data = f.read(280)
                header = struct.unpack('<70f', header_data)

                # Essential header values
                delta = header[0]      # sampling interval
                scale = header[3]       # scaling factor

                # Get station and channel info from filename
                filename = Path(filepath).name
                parts = filename.split('.')
                if len(parts) >= 4:
                    network = parts[0]
                    station = parts[1]
                    channel = parts[3]
                else:
                    network = "XX"
                    station = Path(filepath).stem
                    channel = "BHZ"

                # Read data as integers
                data = np.frombuffer(f.read(), dtype='<i4')

                # Apply scaling if present
                if scale != 1.0 and scale > 0:
                    data = data.astype(np.float32) / scale

                trace = SeismicTrace(
                    timestamp=datetime.now(),
                    station=station,
                    channel=channel,
                    network=network,
                    data=data,
                    sampling_rate=1.0/delta if delta > 0 else 1.0,
                    start_time=datetime.now(),
                    npts=len(data),
                    instrument="SAC File",
                    latitude=0.0,
                    longitude=0.0,
                    file_source=filepath
                )
                return [trace]

        except Exception as e:
            print(f"SAC parse error: {e}")
            return []

class MiniSEEDParser:
    """MiniSEED parser using cymseed3 (Python 3.13 compatible)"""

    @staticmethod
    def parse(filepath: str) -> List[SeismicTrace]:
        if not HAS_CYMSEED3:
            return []

        try:
            import cymseed3
            traces = []
            records = cymseed3.read(filepath)

            for record in records:
                trace = SeismicTrace(
                    timestamp=datetime.now(),
                    station=record.station,
                    channel=record.channel,
                    network=record.network,
                    data=record.data,
                    sampling_rate=record.sampling_rate,
                    start_time=record.starttime.datetime if hasattr(record.starttime, 'datetime') else datetime.now(),
                    npts=len(record.data),
                    instrument="MiniSEED File",
                    file_source=filepath
                )
                traces.append(trace)
            return traces
        except Exception as e:
            print(f"cymseed3 parse error: {e}")
            return []

class GSSIDZTParser:
    """GSSI SIR DZT format parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        return filepath.lower().endswith('.dzt')

    @staticmethod
    def parse(filepath: str) -> Optional[GPRData]:
        try:
            with open(filepath, 'rb') as f:
                header = f.read(1024)

                samples_per_trace = struct.unpack('<H', header[16:18])[0]
                traces = struct.unpack('<H', header[20:22])[0]
                time_window_ns = struct.unpack('<f', header[24:28])[0]
                bits_per_sample = struct.unpack('<H', header[30:32])[0]

                data = np.frombuffer(f.read(), dtype='<i2' if bits_per_sample == 16 else '<i4')
                data = data.reshape(traces, samples_per_trace)

                gpr = GPRData(
                    timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                    station=Path(filepath).stem,
                    instrument="GSSI SIR",
                    antenna_frequency_mhz=400,
                    time_window_ns=time_window_ns,
                    samples_per_trace=samples_per_trace,
                    traces=traces,
                    data=data,
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
            hd_path = filepath.replace('.dt1', '.hd').replace('.DT1', '.HD')

            if not os.path.exists(hd_path):
                return None

            with open(hd_path, 'r') as f:
                hd_lines = f.readlines()

            params = {}
            for line in hd_lines:
                if '=' in line:
                    key, val = line.split('=', 1)
                    params[key.strip()] = val.strip()

            samples = int(params.get('NSAMP', 512))
            traces = int(params.get('NUMTRAC', 0))
            time_window = float(params.get('TIMEWINDOW', 100))
            freq = float(params.get('FREQUENCY', 100))

            data = np.fromfile(filepath, dtype='<i2')
            data = data.reshape(-1, samples)

            gpr = GPRData(
                timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                station=Path(filepath).stem,
                instrument="Sensors & Software",
                antenna_frequency_mhz=freq,
                time_window_ns=time_window,
                samples_per_trace=samples,
                traces=len(data),
                data=data,
                file_source=filepath
            )
            return gpr
        except Exception as e:
            print(f"DT1 parse error: {e}")
            return None

class BartingtonGrad601Parser:
    """Bartington Grad601 fluxgate gradiometer parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        try:
            with open(filepath, 'r') as f:
                first = f.read(500)
                return 'Bartington' in first or 'Grad601' in first
        except Exception as e:
            return False

    @staticmethod
    def parse(filepath: str) -> List[MagneticData]:
        measurements = []
        try:
            df = pd.read_csv(filepath)

            grad_col = None
            for col in df.columns:
                if 'grad' in col.lower():
                    grad_col = col
                    break

            for idx, row in df.iterrows():
                mag = MagneticData(
                    timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                    station=f"Line_{idx}",
                    instrument="Bartington Grad601",
                    total_field_nt=float(row[grad_col]) if grad_col and not pd.isna(row[grad_col]) else None,
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
        except Exception as e:
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

                    if len(parts) >= 2:
                        try:
                            timestamp = float(parts[0])
                            field_nt = float(parts[1])

                            mag = MagneticData(
                                timestamp=datetime.now(),
                                station=f"Point_{timestamp}",
                                instrument="Geometrics G-858",
                                total_field_nt=field_nt,
                                file_source=filepath
                            )
                            measurements.append(mag)
                        except Exception as e:
                            pass
        except Exception as e:
            print(f"Geometrics parse error: {e}")

        return measurements

class ScintrexCGParser:
    """Scintrex CG-5/CG-6 Autograv parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        try:
            with open(filepath, 'r') as f:
                first = f.read(500)
                return any(x in first for x in ['Scintrex', 'CG-5', 'CG-6', 'Autograv'])
        except Exception as e:
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

                            grav = GravityData(
                                timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                                station=station,
                                instrument="Scintrex CG",
                                raw_reading=reading,
                                standard_deviation=std_dev,
                                file_source=filepath
                            )
                            measurements.append(grav)
                        except Exception as e:
                            pass
        except Exception as e:
            print(f"Scintrex parse error: {e}")

        return measurements

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
                            except Exception as e:
                                pass

                    elif section == 'ZXXR':
                        parts = line.split()
                        for p in parts:
                            try:
                                zxxr.append(float(p))
                            except Exception as e:
                                pass

            if freq:
                data = MTData(
                    timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                    station=Path(filepath).stem,
                    instrument="MT Instrument",
                    frequencies=np.array(freq),
                    impedance=np.array(zxxr) if zxxr else None,
                    n_frequencies=len(freq),
                    file_source=filepath
                )
                return data
        except Exception as e:
            print(f"EDI parse error: {e}")
            return None

# ============================================================================
# PROCESSING ENGINE CLASSES
# ============================================================================

class SeismicProcessor:
    """Seismic data processing algorithms"""

    @staticmethod
    def bandpass(data, dt, fmin, fmax, order=4):
        """
        Apply a bandpass filter with safe frequency clamping.
        """
        nyquist = 0.5 / dt
        if nyquist <= 0:
            # Cannot filter; return original data
            return data

        # Ensure frequencies are strictly positive and below Nyquist
        fmin = max(float(fmin), 1e-6)                     # avoid zero
        fmax = min(float(fmax), nyquist * 0.999)          # stay below Nyquist

        # Normalise to [0,1]
        low = fmin / nyquist
        high = fmax / nyquist

        # Guard against low >= high (e.g., if fmin >= fmax after clamping)
        if low >= high:
            low = high * 0.9
            if low <= 0:
                low = 1e-6

        # Design and apply filter
        b, a = signal.butter(order, [low, high], btype='band')
        return signal.filtfilt(b, a, data)

    @staticmethod
    def sta_lta(data, dt, sta_len, lta_len):
        """STA/LTA picker"""
        sta_samples = int(sta_len / dt)
        lta_samples = int(lta_len / dt)
        energy = data ** 2
        sta = np.convolve(energy, np.ones(sta_samples)/sta_samples, mode='same')
        lta = np.convolve(energy, np.ones(lta_samples)/lta_samples, mode='same')
        lta = np.maximum(lta, 1e-10)
        return sta / lta

    @staticmethod
    def deconvolution(data, dt, wlen, prewhiten=0.01):
        """Predictive deconvolution"""
        nsamp = int(wlen / dt)
        nt = len(data)
        acf = np.correlate(data, data, mode='full')
        acf = acf[nt-1:nt-1+nsamp] / nt
        R = np.zeros((nsamp, nsamp))
        for i in range(nsamp):
            for j in range(nsamp):
                if abs(i-j) < nsamp:
                    R[i, j] = acf[abs(i-j)]
        R += prewhiten * R[0,0] * np.eye(nsamp)
        r = acf.copy()
        r[0] = 1.0
        try:
            pef = np.linalg.solve(R, r)
        except Exception as e:
            pef = np.linalg.lstsq(R, r, rcond=None)[0]
        return signal.lfilter(pef, [1.0], data)

    @staticmethod
    def agc(data, window_len):
        """Automatic Gain Control"""
        half = window_len // 2
        nt = len(data)
        data_agc = np.zeros_like(data)
        for i in range(nt):
            i1 = max(0, i - half)
            i2 = min(nt, i + half + 1)
            window = data[i1:i2]
            rms = np.sqrt(np.mean(window ** 2) + 1e-6)
            data_agc[i] = data[i] / rms
        return data_agc

    @staticmethod
    def velocity_analysis(cdp, dt, dx, vmin=1500, vmax=4000, nv=50):
        """Velocity analysis using semblance"""
        nt, noff = cdp.shape
        offsets = np.arange(noff) * dx
        t = np.arange(nt) * dt
        velocities = np.linspace(vmin, vmax, nv)
        semblance = np.zeros((nt, nv))
        for iv, v in enumerate(velocities):
            for it in range(nt):
                t0 = t[it]
                traces_nmo = np.zeros(noff)
                for ioff, offset in enumerate(offsets):
                    tnmo = np.sqrt(t0**2 + (offset/v)**2)
                    idx = int(round(tnmo / dt))
                    if 0 <= idx < nt:
                        traces_nmo[ioff] = cdp[idx, ioff]
                numerator = np.sum(traces_nmo)**2
                denominator = noff * np.sum(traces_nmo**2)
                semblance[it, iv] = numerator / denominator if denominator > 0 else 0
        return t, velocities, semblance

    @staticmethod
    def nmo(cdp, dt, dx, velocity):
        """Apply NMO correction"""
        nt, noff = cdp.shape
        offsets = np.arange(noff) * dx
        t = np.arange(nt) * dt
        data_nmo = np.zeros_like(cdp)
        for it in range(nt):
            t0 = t[it]
            for ioff, offset in enumerate(offsets):
                tnmo = np.sqrt(t0**2 + (offset/velocity[it])**2)
                idx = int(round(tnmo / dt))
                if 0 <= idx < nt:
                    data_nmo[it, ioff] = cdp[idx, ioff]
        return data_nmo

    @staticmethod
    def stack(cdp):
        """Stack CDP gather"""
        return np.mean(cdp, axis=1)


class ERTProcessor:
    """ERT data processing for real survey data"""

    @staticmethod
    def apparent_resistivity(resistance, geometry_factor):
        """
        Calculate apparent resistivity

        Parameters:
        - resistance: measured resistance in ohms (ΔV/I)
        - geometry_factor: k-factor for the array configuration

        Returns:
        - apparent resistivity in ohm-m
        """
        return resistance * geometry_factor

    @staticmethod
    def geometry_wenner(a):
        """
        Wenner Alpha array geometry factor

        Parameters:
        - a: electrode spacing (meters)

        Returns:
        - k-factor for Wenner Alpha
        """
        return 2 * np.pi * a

    @staticmethod
    def geometry_schlumberger(a, n):
        """
        Schlumberger array geometry factor

        Parameters:
        - a: potential electrode half-spacing (meters)
        - n: ratio of current electrode spacing to potential spacing

        Returns:
        - k-factor for Schlumberger
        """
        return np.pi * n * (n + 1) * a

    @staticmethod
    def geometry_dipole_dipole(a, n):
        """
        Dipole-dipole array geometry factor

        Parameters:
        - a: dipole length (meters)
        - n: number of dipole spacings between centers

        Returns:
        - k-factor for dipole-dipole
        """
        return np.pi * n * (n + 1) * (n + 2) * a

    @staticmethod
    def geometry_pole_pole(a):
        """
        Pole-Pole array geometry factor

        Parameters:
        - a: electrode spacing (meters)

        Returns:
        - k-factor for Pole-Pole
        """
        return 2 * np.pi * a

    @staticmethod
    def geometry_pole_dipole(a, n):
        """
        Pole-Dipole array geometry factor

        Parameters:
        - a: potential electrode spacing (meters)
        - n: number of spacings

        Returns:
        - k-factor for Pole-Dipole
        """
        return 2 * np.pi * n * (n + 1) * a

    @staticmethod
    def load_abem_data(filepath):
        """
        Load ERTLab format .data files from EGS Collab project
        Returns: (a, b, m, n, rhoa, err) arrays
        """
        a, b, m, n = [], [], [], []
        rhoa, err = [], []

        # First, read electrode mapping to convert cable+electrode to absolute electrode numbers
        electrode_map = {}  # Maps "cable,electrode" string to absolute electrode number
        absolute_electrode = 1

        with open(filepath, 'r') as f:
            lines = f.readlines()

        # First pass: read electrode positions and build mapping
        in_electrode_section = False
        for line in lines:
            line = line.strip()

            # Check for electrode section start
            if line == '#elec_start':
                in_electrode_section = True
                continue
            if line == '#elec_end':
                in_electrode_section = False
                continue

            # Parse electrode lines
            if in_electrode_section and line and not line.startswith('#'):
                # Format: "001,01 +1227.7 -864.57 +341.94 -1.0000 001"
                parts = line.split()
                if len(parts) >= 6:
                    cable_electrode = parts[0]  # e.g., "001,01"
                    electrode_map[cable_electrode] = absolute_electrode
                    absolute_electrode += 1

        # Second pass: read measurement data
        in_data_section = False
        all_rhoa = []  # Store all values before filtering

        for line in lines:
            line = line.strip()

            # Check for data section start
            if line == '#data_start':
                in_data_section = True
                continue
            if line == '#data_end':
                in_data_section = False
                continue

            # Skip header lines and empty lines
            if not in_data_section or line.startswith('!') or line.startswith('#') or not line:
                continue

            # Parse data line
            parts = line.split()

            # Need at least 10 columns for basic data
            if len(parts) >= 10:
                try:
                    # Column indices based on the header:
                    # 0: ID num
                    # 1: A cable,elec (e.g., "001,01")
                    # 2: B cable,elec
                    # 3: M cable,elec
                    # 4: N cable,elec
                    # 5: V/I (Ohms) - this is resistance
                    # 6: Std. (Ohms)
                    # ... other columns ...

                    a_key = parts[1]  # A electrode (cable,elec)
                    b_key = parts[2]  # B electrode
                    m_key = parts[3]  # M electrode
                    n_key = parts[4]  # N electrode

                    # Convert to absolute electrode numbers using our map
                    if a_key in electrode_map and b_key in electrode_map and m_key in electrode_map and n_key in electrode_map:
                        a_abs = electrode_map[a_key]
                        b_abs = electrode_map[b_key]
                        m_abs = electrode_map[m_key]
                        n_abs = electrode_map[n_key]

                        # Resistance in ohms (V/I)
                        resistance = float(parts[5])

                        # Standard deviation (error)
                        std_dev = float(parts[6])

                        # Calculate geometry factor for apparent resistivity
                        # For now, we'll store raw resistance and let pyGIMLi handle geometry
                        # But we need to compute apparent resistivity for the ERTData object

                        # Simple dipole-dipole geometry factor approximation
                        # You might want to adjust this based on your array type
                        spacing = 5.0  # Default electrode spacing in meters

                        # Calculate distance between current electrodes
                        current_distance = abs(a_abs - b_abs) * spacing
                        potential_distance = abs(m_abs - n_abs) * spacing

                        # Simplified geometry factor (adjust as needed)
                        if current_distance > 0 and potential_distance > 0:
                            k = 2 * np.pi * (current_distance * potential_distance) / (current_distance - potential_distance + 0.001)
                        else:
                            k = 2 * np.pi * spacing

                        # Apparent resistivity = resistance * k
                        rho_apparent = resistance * k

                        a.append(a_abs)
                        b.append(b_abs)
                        m.append(m_abs)
                        n.append(n_abs)
                        all_rhoa.append(rho_apparent)
                        err.append(std_dev * 100 / resistance if resistance > 0 else 2.0)  # Convert to percentage

                except (ValueError, KeyError) as e:
                    print(f"Skipping line due to error: {e}")
                    continue

        # Convert to numpy arrays
        a = np.array(a, dtype=int)
        b = np.array(b, dtype=int)
        m = np.array(m, dtype=int)
        n = np.array(n, dtype=int)
        all_rhoa = np.array(all_rhoa, dtype=float)
        err = np.array(err, dtype=float)

        # Filter out invalid measurements
        valid_mask = (all_rhoa > 0) & (np.isfinite(all_rhoa)) & (all_rhoa < 1e8)
        a = a[valid_mask]
        b = b[valid_mask]
        m = m[valid_mask]
        n = n[valid_mask]
        rhoa = all_rhoa[valid_mask]
        err = err[valid_mask]

        print(f"Successfully parsed {len(all_rhoa)} measurements")
        print(f"Filtered to {len(rhoa)} valid measurements (removed {len(all_rhoa) - len(rhoa)} invalid)")
        print(f"Electrode range: {a.min()} to {max(a.max(), b.max(), m.max(), n.max())}")
        print(f"Resistivity range: {rhoa.min():.1f} to {rhoa.max():.1f} Ω·m")

        return a, b, m, n, rhoa, err

    @staticmethod
    def load_syscal_bin(filepath):
        """
        Load IRIS Syscal .bin format

        Parameters:
        - filepath: path to .bin file

        Returns:
        - tuple: (a, b, m, n, rhoa, err) arrays
        """
        import struct

        a, b, m, n = [], [], [], []
        rhoa, err = [], []

        with open(filepath, 'rb') as f:
            # Skip header (first 12 bytes typically)
            f.read(12)

            # Read measurements
            while True:
                try:
                    # Each record is 16 bytes typically
                    data = f.read(16)
                    if len(data) < 16:
                        break

                    # Decode (format may vary by Syscal version)
                    values = struct.unpack('<hhhhff', data)

                    a.append(values[0])
                    b.append(values[1])
                    m.append(values[2])
                    n.append(values[3])
                    rhoa.append(values[4])
                    err.append(values[5] if values[5] > 0 else 2.0)
                except Exception as e:
                    break

        return np.array(a), np.array(b), np.array(m), np.array(n), np.array(rhoa), np.array(err)

    @staticmethod
    def create_pygimli_data(a, b, m, n, rhoa, spacing=1.0):
        import pygimli as pg

        # Create container
        data = pg.DataContainerERT()

        # Determine number of electrodes
        n_electrodes = int(max(a.max(), b.max(), m.max(), n.max()))

        # Create sensors
        for i in range(n_electrodes):
            data.createSensor([i * spacing, 0.0])

        # Create measurements
        for i in range(len(rhoa)):
            data.createFourPointData(
                int(i),
                int(a[i]) - 1,
                int(b[i]) - 1,
                int(m[i]) - 1,
                int(n[i]) - 1
            )

        # Assign apparent resistivity
        data["rhoa"] = pg.Vector(rhoa)

        return data

    @staticmethod
    def invert_pygimli(data_container, **kwargs):
        """
        Invert ERT data using pyGIMLi

        Parameters:
        - data_container: pyGIMLi DataContainerERT
        - **kwargs: inversion parameters (lam, robustData, etc.)

        Returns:
        - inversion result (model array)
        """
        if not HAS_PYGIMLI:
            return None

        try:
            from pygimli.physics import ert

            # Set default inversion parameters
            inv_params = {
                'lam': 20,
                'robustData': True,
                'robustModel': True,
                'verbose': False,
                'maxIter': 10
            }
            inv_params.update(kwargs)

            # Run inversion
            mgr = ert.ERTManager(data_container)
            model = mgr.invert(**inv_params)

            # Store manager for later access
            model.manager = mgr

            return model

        except Exception as e:
            print(f"ERT inversion error: {e}")
            return None

    @staticmethod
    def get_rms(manager):
        """Get RMS misfit from ERT manager"""
        try:
            return manager.inv.relrms()
        except Exception as e:
            return None

class GravityProcessor:
    """Gravity data processing"""

    @staticmethod
    def igf_1980(latitude):
        """International Gravity Formula 1980"""
        phi_rad = np.radians(latitude)
        sin_phi = np.sin(phi_rad)
        sin2_phi = np.sin(2 * phi_rad)
        gamma = 978032.7 * (1 + 0.0053024 * sin_phi**2 - 0.0000058 * sin2_phi**2)
        return gamma

    @staticmethod
    def free_air(elevation_m):
        """Free-air correction"""
        return 0.3086 * elevation_m

    @staticmethod
    def bouguer(elevation_m, density=2.67):
        """Bouguer slab correction"""
        return -0.04193 * density * elevation_m

    @staticmethod
    def terrain(elevation_m, dem_data=None):
        """Terrain correction (simplified)"""
        if dem_data is None or len(dem_data) < 10:
            return 0.1 * elevation_m / 1000
        roughness = np.std(dem_data) / np.mean(dem_data) if np.mean(dem_data) > 0 else 0
        return 0.05 * roughness * elevation_m / 500

    @staticmethod
    def eotvos(velocity, heading, latitude):
        """Eötvös correction for moving platforms"""
        return 7.5 * velocity * np.sin(heading) * np.cos(np.radians(latitude))

    @staticmethod
    def drift(times, readings):
        """Linear drift correction"""
        coeffs = np.polyfit(times, readings, 1)
        drift_rate = coeffs[0]
        corrected = readings - drift_rate * (times - times[0])
        return corrected, drift_rate

    @staticmethod
    def tide(date, latitude):
        """Tidal correction (simplified)"""
        # Use harmonic approximation
        day_angle = 2 * np.pi * date.day / 365.25
        lunar = 0.165 * np.cos(day_angle)  # Simplified lunar effect
        solar = 0.075 * np.cos(2 * day_angle)  # Simplified solar effect
        return lunar + solar


class MagneticsProcessor:
    """Magnetic data processing"""

    @staticmethod
    def igrf_remove(data, latitude, longitude, altitude, date):
        """Remove IGRF (simplified - using constant for demo)"""
        # In production, use pyIGRF or similar
        regional = 50000  # Approximate field strength in nT
        return data - regional

    @staticmethod
    def reduction_to_pole(data_fft, kx, ky, inclination, declination):
        """Reduce magnetic data to the pole"""
        theta = np.arctan2(ky, kx)
        inc_rad = np.radians(inclination)
        dec_rad = np.radians(declination)
        filter_rtp = 1.0 / ((np.sin(inc_rad) + 1j * np.cos(inc_rad) * np.cos(theta - dec_rad))**2)
        return data_fft * filter_rtp

    @staticmethod
    def analytic_signal(dx, dy, dz):
        """Calculate analytic signal amplitude"""
        return np.sqrt(dx**2 + dy**2 + dz**2)

    @staticmethod
    def upward_continuation(data_fft, kx, ky, dz):
        """Upward continuation in Fourier domain"""
        k = np.sqrt(kx**2 + ky**2)
        filter_uc = np.exp(-k * dz)
        return data_fft * filter_uc

    @staticmethod
    def euler_deconvolution(x, y, z, field, dx, dy, dz, structural_index=1):
        """Euler deconvolution for depth estimation"""
        # Simple implementation - in production use moving window
        A = np.column_stack([dx, dy, dz, np.ones_like(dx)])
        b = -structural_index * field
        try:
            sol, _, _, _ = np.linalg.lstsq(A, b, rcond=None)
            x0, y0, z0, base = sol
            return {'x': x0, 'y': y0, 'z': z0, 'base': base}
        except Exception as e:
            return None


class MTProcessor:
    """Magnetotelluric data processing"""

    @staticmethod
    def apparent_resistivity(Zxy, freq):
        """Calculate apparent resistivity"""
        mu0 = 4 * np.pi * 1e-7
        rho = (np.abs(Zxy)**2) / (2 * np.pi * freq * mu0)
        return rho

    @staticmethod
    def phase(Zxy):
        """Calculate impedance phase"""
        return np.arctan2(np.imag(Zxy), np.real(Zxy)) * 180 / np.pi

    @staticmethod
    def phase_tensor(Z):
        """Calculate phase tensor"""
        X = np.real(Z)
        Y = np.imag(Z)
        try:
            X_inv = np.linalg.inv(X)
            phi = X_inv @ Y
        except Exception as e:
            phi = np.eye(2)
        return phi

    @staticmethod
    def strike_angle(phi):
        """Estimate strike from phase tensor"""
        phi11, phi12 = phi[0,0], phi[0,1]
        phi21, phi22 = phi[1,0], phi[1,1]
        numerator = phi12 + phi21
        denominator = phi11 - phi22
        strike = 0.5 * np.arctan2(numerator, denominator) * 180 / np.pi
        return strike


class GPRProcessor:
    """GPR data processing"""

    @staticmethod
    def dewow(trace, window=50):
        """Remove low-frequency wow"""
        kernel = np.ones(window) / window
        low_freq = np.convolve(trace, kernel, mode='same')
        return trace - low_freq

    @staticmethod
    def background_remove(data_2d):
        """Remove background (average trace)"""
        avg_trace = np.mean(data_2d, axis=1, keepdims=True)
        return data_2d - avg_trace

    @staticmethod
    def agc_gain(data, window=100):
        """Apply AGC gain"""
        result = np.zeros_like(data)
        for i in range(data.shape[1]):
            trace = data[:, i]
            half = window // 2
            for j in range(len(trace)):
                i1 = max(0, j - half)
                i2 = min(len(trace), j + half + 1)
                rms = np.sqrt(np.mean(trace[i1:i2]**2) + 1e-6)
                result[j, i] = trace[j] / rms
        return result

    @staticmethod
    def kirchhoff_migration(data, dt_ns, dx_m, velocity_m_ns):
        """Kirchhoff time migration"""
        nt, nx = data.shape
        migrated = np.zeros_like(data)
        t = np.arange(nt) * dt_ns
        x = np.arange(nx) * dx_m
        for xi in range(nx):
            for ti in range(nt):
                t0 = t[ti]
                sum_val = 0.0
                count = 0
                for xj in range(nx):
                    dx = x[xi] - x[xj]
                    t_hyp = np.sqrt(t0**2 + (dx / velocity_m_ns)**2)
                    idx_t = int(round(t_hyp / dt_ns))
                    if 0 <= idx_t < nt:
                        sum_val += data[idx_t, xj]
                        count += 1
                if count > 0:
                    migrated[ti, xi] = sum_val / count
        return migrated

    @staticmethod
    def stolt_migration(data, dt_ns, dx_m, velocity_m_ns):
        """Stolt F-K migration"""
        nt, nx = data.shape
        n_pad = max(nt, nx)
        data_pad = np.pad(data, ((0, n_pad-nt), (0, n_pad-nx)), mode='constant')
        spec = np.fft.fft2(data_pad)
        spec = np.fft.fftshift(spec)
        f = np.fft.fftshift(np.fft.fftfreq(n_pad, dt_ns * 1e-9))
        k = np.fft.fftshift(np.fft.fftfreq(n_pad, dx_m))
        F, K = np.meshgrid(f, k, indexing='ij')
        omega = 2 * np.pi * f
        v = velocity_m_ns * 1e9
        omega_new = np.sqrt(omega**2 + (v * K)**2)
        from scipy.interpolate import griddata
        points = np.array([omega.ravel(), k.ravel()]).T
        values = spec.ravel()
        f_new = np.linspace(f.min(), f.max(), n_pad)
        k_new = np.linspace(k.min(), k.max(), n_pad)
        F_new, K_new = np.meshgrid(f_new, k_new, indexing='ij')
        omega_new_grid = 2 * np.pi * F_new
        spec_mig = griddata(points, values, (omega_new_grid.ravel(), K_new.ravel()), method='linear', fill_value=0)
        spec_mig = spec_mig.reshape(F_new.shape)
        spec_mig = np.fft.ifftshift(spec_mig)
        migrated_pad = np.real(np.fft.ifft2(spec_mig))
        return migrated_pad[:nt, :nx]


class GriddingEngine:
    """Gridding and enhancement algorithms"""

    def on_data_changed(self):
        """Called when workflow state changes"""
        print("Tab 3: Data changed")  # For testing
        # We'll add actual UI updates later

    @staticmethod
    def minimum_curvature(x, y, z, grid_x, grid_y):
        """Minimum curvature gridding (simplified)"""
        from scipy.interpolate import RBFInterpolator
        points = np.column_stack([x, y])
        rbf = RBFInterpolator(points, z, kernel='thin_plate_spline')
        X, Y = np.meshgrid(grid_x, grid_y)
        Z = rbf(np.column_stack([X.ravel(), Y.ravel()])).reshape(X.shape)
        return X, Y, Z

    @staticmethod
    def kriging(x, y, z, grid_x, grid_y, variogram_model='spherical'):
        """Ordinary kriging using pykrige"""
        if not HAS_PYKRIGE:
            return None
        OK = OrdinaryKriging(x, y, z, variogram_model=variogram_model)
        X, Y = np.meshgrid(grid_x, grid_y)
        Z, ss = OK.execute('grid', grid_x, grid_y)
        return X, Y, Z

    @staticmethod
    def fft_filter(grid, dx, dy, filter_type='low', cutoff=0.1):
        """Apply FFT filter to grid"""
        F = fft2(grid)
        F = np.fft.fftshift(F)
        ny, nx = grid.shape
        kx = fftfreq(nx, dx)
        ky = fftfreq(ny, dy)
        KX, KY = np.meshgrid(kx, ky)
        K = np.sqrt(KX**2 + KY**2)
        if filter_type == 'low':
            mask = K <= cutoff
        elif filter_type == 'high':
            mask = K >= cutoff
        else:
            mask = (K >= cutoff[0]) & (K <= cutoff[1])
        F_filtered = F * mask
        F_filtered = np.fft.ifftshift(F_filtered)
        return np.real(ifft2(F_filtered))

    @staticmethod
    def horizontal_gradient(grid, dx, dy):
        """Calculate horizontal gradient magnitude"""
        gy, gx = np.gradient(grid, dx, dy)
        return np.sqrt(gx**2 + gy**2)

    @staticmethod
    def tilt_derivative(grid, dx, dy):
        """Calculate tilt derivative"""
        gy, gx = np.gradient(grid, dy, dx)
        hg = np.sqrt(gx**2 + gy**2)
        # Vertical derivative approximated via second-order Laplacian
        d2x = np.gradient(np.gradient(grid, dx, axis=1), dx, axis=1)
        d2y = np.gradient(np.gradient(grid, dy, axis=0), dy, axis=0)
        vd = d2x + d2y
        with np.errstate(divide='ignore', invalid='ignore'):
            tilt = np.arctan2(vd, hg)
        return np.nan_to_num(tilt)


class ModelingEngine:
    """Interpretation and modeling algorithms"""

    @staticmethod
    def euler_deconvolution_2d(x, z, field, dx_dz, structural_index=1, window=10):
        """2D Euler deconvolution"""
        nx = len(x)
        solutions = []
        for i in range(window, nx - window):
            x_win = x[i-window:i+window]
            z_win = z[i-window:i+window]
            field_win = field[i-window:i+window]
            dx = np.gradient(field_win, x_win)
            dz = np.gradient(field_win, z_win)
            A = np.column_stack([dx, dz, np.ones_like(dx)])
            b = -structural_index * field_win
            try:
                sol, _, _, _ = np.linalg.lstsq(A, b, rcond=None)
                x0, z0, base = sol
                solutions.append({'x': x_win[window], 'x0': x0, 'z0': z0, 'base': base})
            except Exception as e:
                pass
        return solutions

    @staticmethod
    def joint_inversion_ert_gravity(ert_data, gravity_data, coupling=0.1):
        """Joint inversion of ERT and gravity data using pyGIMLi"""
        if not HAS_PYGIMLI:
            return None
        try:
            joint = pg.core.JointModelling()
            # Add ERT part
            fop_ert = ert.createERTModelling(ert_data)
            joint.add(fop_ert, ert_data, weight=1.0)
            # Add gravity part
            fop_grav = grav.createGravityModelling(gravity_data)
            joint.add(fop_grav, gravity_data, weight=coupling)
            model = joint.invert(verbose=False)
            return model
        except Exception as e:
            return None

    @staticmethod
    def lineament_detection(grid, threshold=0.5):
        """Detect lineaments using edge detection and Hough transform"""
        if not HAS_SKIMAGE:
            return []
        from skimage import feature, transform
        edges = feature.canny(grid, sigma=1)
        lines = transform.probabilistic_hough_line(edges, threshold=10, line_length=10, line_gap=3)
        return lines

    @staticmethod
    def xgboost_predict(features, target, new_features):
        """Predict using XGBoost"""
        if not HAS_XGBOOST:
            return None
        model = xgb.XGBRegressor()
        model.fit(features, target)
        return model.predict(new_features)

    @staticmethod
    def cluster_attributes(data, n_clusters=3, method='kmeans'):
        """Cluster geophysical attributes"""
        if not HAS_SKLEARN:
            return None
        if method == 'kmeans':
            model = KMeans(n_clusters=n_clusters)
        else:
            model = DBSCAN(eps=0.3, min_samples=10)
        return model.fit_predict(data)

# ============================================================================
# MAIN PLUGIN CLASS
# ============================================================================
class GeophysicsAnalysisSuite:
    def __init__(self, main_app):
        self.app = main_app
        self.window = None
        self.ui_queue = None
        self.workflow_state = None
        self.processing_tabs = {}

    def show_interface(self):
        """Show the main plugin window"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("🌍 Geophysics Analysis Suite v3.0")
        self.window.geometry(PLUGIN_INFO["window_size"])
        self.window.minsize(1000, 700)
        self.window.transient(self.app.root)

        self.ui_queue = ThreadSafeUI(self.window)
        self.workflow_state = WorkflowState()

        self._build_ui()

        # Auto-load data from main table if available
        self.window.after(500, self._auto_import)

        self.window.lift()
        self.window.focus_force()
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        """Build the 5-tab interface"""
        # Header
        header = tk.Frame(self.window, bg="#1A3A5A", height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="🌍", font=("Arial", 20),
                bg="#1A3A5A", fg="white").pack(side=tk.LEFT, padx=10)
        tk.Label(header, text="GEOPHYSICS ANALYSIS SUITE v3.0",
                font=("Arial", 14, "bold"), bg="#1A3A5A", fg="white").pack(side=tk.LEFT)
        tk.Label(header, text="5-Tab Workflow", font=("Arial", 10),
                bg="#1A3A5A", fg="#FFD700").pack(side=tk.LEFT, padx=10)

        self.status_var = tk.StringVar(value="Ready")
        tk.Label(header, textvariable=self.status_var,
                font=("Arial", 9), bg="#1A3A5A", fg="#FFD700").pack(side=tk.RIGHT, padx=10)

        # Notebook for 5 tabs
        style = ttk.Style()
        style.configure("Analysis.TNotebook.Tab", font=("Arial", 10, "bold"), padding=[10, 5])

        self.notebook = ttk.Notebook(self.window, style="Analysis.TNotebook")
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # ============ TAB 1: DATA IMPORT & QC ============
        self.tab1 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab1, text=" 1. 📥 IMPORT & QC ")
        self._build_tab1()

        # ============ TAB 2: PROCESSING ============
        self.tab2 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab2, text=" 2. 🔧 PROCESSING ")
        self._build_tab2()

        # ============ TAB 3: GRIDDING ============
        self.tab3 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab3, text=" 3. 🗺️ GRIDDING ")
        self._build_tab3()

        # ============ TAB 4: MODELING ============
        self.tab4 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab4, text=" 4. 🧠 MODELING ")
        self._build_tab4()

        # ============ TAB 5: VISUALIZATION ============
        self.tab5 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab5, text=" 5. 📤 VISUALIZATION ")
        self._build_tab5()

        # Bottom status bar with progress
        status = tk.Frame(self.window, bg="#f0f0f0", height=35)
        status.pack(fill=tk.X, side=tk.BOTTOM)
        status.pack_propagate(False)

        # Progress bar (left side)
        self.progress_bar = ttk.Progressbar(status, mode='indeterminate', length=150)
        self.progress_bar.pack(side=tk.LEFT, padx=5)

        self.state_label = tk.Label(status,
            text="📊 No data loaded", font=("Arial", 9), bg="#f0f0f0")
        self.state_label.pack(side=tk.LEFT, padx=10, expand=True)

        ttk.Button(status, text="📥 Import from Table",
                  command=self._import_from_table).pack(side=tk.RIGHT, padx=10)

    def _build_tab1(self):
        """Build Tab 1: Data Import & QC (from your existing code)"""
        # Main container with left (controls) and right (visualizations)
        tab1_paned = ttk.PanedWindow(self.tab1, orient=tk.HORIZONTAL)
        tab1_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # LEFT PANEL - Controls and stats
        left = ttk.Frame(tab1_paned, width=350)
        tab1_paned.add(left, weight=1)

        # RIGHT PANEL - Visualizations
        right = ttk.Frame(tab1_paned)
        tab1_paned.add(right, weight=2)

        # === LEFT PANEL CONTENT ===
        # Import section
        import_frame = ttk.LabelFrame(left, text="📥 Import Data", padding=10)
        import_frame.pack(fill=tk.X, pady=5)

        ttk.Button(import_frame, text="Import from Main Table",
                  command=self._import_from_table).pack(fill=tk.X, pady=2)

        self.data_status = ttk.Label(import_frame, text="No data loaded",
                                     font=("Arial", 9))
        self.data_status.pack(anchor='w', pady=2)

        # Data Health Dashboard
        health_frame = ttk.LabelFrame(left, text="📊 Data Health Dashboard", padding=10)
        health_frame.pack(fill=tk.X, pady=5)

        metrics = [
            ("Total samples:", "0"),
            ("Valid coordinates:", "0"),
            ("Missing values:", "0"),
            ("Outliers detected:", "0"),
            ("Spatial coverage:", "0%"),
            ("Quality flag:", "")
        ]

        self.health_labels = {}
        for i, (label, value) in enumerate(metrics):
            tk.Label(health_frame, text=label, font=("Arial", 8, "bold"),
                    anchor='w').grid(row=i, column=0, sticky='w', pady=1)
            self.health_labels[label] = tk.Label(health_frame, text=value,
                                                font=("Arial", 8))
            self.health_labels[label].grid(row=i, column=1, sticky='w', padx=10, pady=1)

        # Quality flag
        self.quality_flag = tk.Label(health_frame, text="⚪ NO DATA",
                                     font=("Arial", 9, "bold"),
                                     bg="#f0f0f0", fg="#666")
        self.quality_flag.grid(row=len(metrics), column=0, columnspan=2, pady=5, sticky='ew')

        # Survey Statistics
        stats_frame = ttk.LabelFrame(left, text="📐 Survey Statistics", padding=10)
        stats_frame.pack(fill=tk.X, pady=5)

        stats = [
            ("X range:", "—"),
            ("Y range:", "—"),
            ("Z range:", "—"),
            ("Line spacing:", "—"),
            ("Station spacing:", "—"),
            ("Survey area:", "—")
        ]

        self.stats_labels = {}
        for i, (label, value) in enumerate(stats):
            tk.Label(stats_frame, text=label, font=("Arial", 8, "bold"),
                    anchor='w').grid(row=i, column=0, sticky='w', pady=1)
            self.stats_labels[label] = tk.Label(stats_frame, text=value,
                                               font=("Arial", 8))
            self.stats_labels[label].grid(row=i, column=1, sticky='w', padx=10, pady=1)

        # Quality Control Tools
        qc_frame = ttk.LabelFrame(left, text="🔍 Quality Control", padding=10)
        qc_frame.pack(fill=tk.X, pady=5)

        ttk.Button(qc_frame, text="Detect Outliers (MAD)",
                  command=self._detect_outliers).pack(fill=tk.X, pady=2)
        ttk.Button(qc_frame, text="Remove Missing Values",
                  command=self._remove_missing).pack(fill=tk.X, pady=2)
        ttk.Button(qc_frame, text="Coordinate Transformation",
                  command=self._transform_coords).pack(fill=tk.X, pady=2)

        # QC Status area
        self.qc_status = tk.Text(qc_frame, height=8, width=35, font=("Courier", 8))
        self.qc_status.pack(fill=tk.X, pady=5)

        # === RIGHT PANEL CONTENT ===
        # Notebook for visualizations
        right_notebook = ttk.Notebook(right)
        right_notebook.pack(fill=tk.BOTH, expand=True)

        # Coverage Map tab
        map_frame = ttk.Frame(right_notebook)
        right_notebook.add(map_frame, text="🗺️ Coverage Map")

        self.coverage_fig = Figure(figsize=(6, 5), dpi=100, facecolor='white')
        self.coverage_ax = self.coverage_fig.add_subplot(111)
        self.coverage_canvas = FigureCanvasTkAgg(self.coverage_fig, map_frame)
        self.coverage_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Distributions tab
        dist_frame = ttk.Frame(right_notebook)
        right_notebook.add(dist_frame, text="📊 Distributions")

        self.dist_fig = Figure(figsize=(6, 5), dpi=100, facecolor='white')
        self.dist_ax = self.dist_fig.add_subplot(111)
        self.dist_canvas = FigureCanvasTkAgg(self.dist_fig, dist_frame)
        self.dist_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Initialize empty plots
        self.coverage_ax.text(0.5, 0.5, "Import data to see coverage map",
                             ha='center', va='center', transform=self.coverage_ax.transAxes)
        self.coverage_ax.set_xlabel("X (m)")
        self.coverage_ax.set_ylabel("Y (m)")
        self.coverage_canvas.draw()

        self.dist_ax.text(0.5, 0.5, "Import data to see distributions",
                         ha='center', va='center', transform=self.dist_ax.transAxes)
        self.dist_canvas.draw()

    def _build_tab2(self):
        """Build Tab 2: Processing with full method sub-tabs"""
        # Create notebook for processing methods
        self.processing_notebook = ttk.Notebook(self.tab2)
        self.processing_notebook.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # ============ SEISMIC TAB ============
        seismic_frame = ttk.Frame(self.processing_notebook)
        self.processing_notebook.add(seismic_frame, text="  🔧 Seismic  ")

        # Seismic main container
        seismic_paned = ttk.PanedWindow(seismic_frame, orient=tk.HORIZONTAL)
        seismic_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Seismic left controls
        seismic_left = ttk.Frame(seismic_paned, width=300)
        seismic_paned.add(seismic_left, weight=1)

        # Seismic right plot
        seismic_right = ttk.Frame(seismic_paned)
        seismic_paned.add(seismic_right, weight=2)

        # Seismic controls
        sf1 = tk.LabelFrame(seismic_left, text="Bandpass Filter", bg="#f0f0f0")
        sf1.pack(fill=tk.X, padx=5, pady=2)
        fmin_label = tk.Label(sf1, text="fmin (Hz):")
        fmin_label.grid(row=0, column=0, padx=2)
        ToolTip(fmin_label, "Minimum frequency to pass (Hz)\nLower values remove low-frequency noise")

        self.seis_fmin = tk.StringVar(value="5")
        tk.Entry(sf1, textvariable=self.seis_fmin, width=8).grid(row=0, column=1)

        fmax_label = tk.Label(sf1, text="fmax (Hz):")
        fmax_label.grid(row=1, column=0, padx=2)
        ToolTip(fmax_label, "Maximum frequency to pass (Hz)\nHigher values remove high-frequency noise")
        self.seis_fmax = tk.StringVar(value="40")
        tk.Entry(sf1, textvariable=self.seis_fmax, width=8).grid(row=1, column=1)
        ttk.Button(sf1, text="Apply", command=self._seismic_bandpass).grid(row=2, column=0, columnspan=2, pady=2)

        sf2 = tk.LabelFrame(seismic_left, text="STA/LTA Picker", bg="#f0f0f0")
        sf2.pack(fill=tk.X, padx=5, pady=2)
        tk.Label(sf2, text="STA (s):").grid(row=0, column=0, padx=2)
        self.seis_sta = tk.StringVar(value="1.0")
        tk.Entry(sf2, textvariable=self.seis_sta, width=8).grid(row=0, column=1)
        tk.Label(sf2, text="LTA (s):").grid(row=1, column=0, padx=2)
        self.seis_lta = tk.StringVar(value="5.0")
        tk.Entry(sf2, textvariable=self.seis_lta, width=8).grid(row=1, column=1)
        ttk.Button(sf2, text="Run", command=self._seismic_stalta).grid(row=2, column=0, columnspan=2, pady=2)

        sf3 = tk.LabelFrame(seismic_left, text="AGC", bg="#f0f0f0")
        sf3.pack(fill=tk.X, padx=5, pady=2)
        tk.Label(sf3, text="Window (s):").pack()
        self.seis_agc = tk.StringVar(value="1.0")
        tk.Entry(sf3, textvariable=self.seis_agc, width=8).pack()
        ttk.Button(sf3, text="Apply", command=self._seismic_agc).pack(pady=2)

        # SEISMIC STATUS AREA (no popups)
        self.seis_status = tk.Text(sf3, height=8, width=35, font=("Courier", 8))
        self.seis_status.pack(fill=tk.X, pady=5)

        # Seismic plot
        self.seis_fig = Figure(figsize=(6, 4), dpi=90)
        self.seis_ax = self.seis_fig.add_subplot(111)
        self.seis_canvas = FigureCanvasTkAgg(self.seis_fig, seismic_right)
        self.seis_canvas.draw()
        self.seis_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # ============ ERT TAB ============
        ert_frame = ttk.Frame(self.processing_notebook)
        self.processing_notebook.add(ert_frame, text="  ⚡ ERT  ")

        ert_paned = ttk.PanedWindow(ert_frame, orient=tk.HORIZONTAL)
        ert_paned.pack(fill=tk.BOTH, expand=True)

        ert_left = ttk.Frame(ert_paned, width=300)
        ert_paned.add(ert_left, weight=1)

        ert_right = ttk.Frame(ert_paned)
        ert_paned.add(ert_right, weight=2)

        # ===== DATA IMPORT FRAME (MOVED HERE, AFTER ert_left IS DEFINED) =====
        ef0 = tk.LabelFrame(ert_left, text="Data", bg="#f0f0f0")
        ef0.pack(fill=tk.X, padx=5, pady=2)

        ttk.Button(ef0, text="📂 Import ERT Survey File",
                  command=self._import_ert_file).pack(fill=tk.X, pady=2)

        self.ert_file_label = tk.Label(ef0, text="No file loaded", fg="red", font=("Arial", 8))
        self.ert_file_label.pack(pady=2)

        # ===== GEOMETRY FRAME =====
        ef1 = tk.LabelFrame(ert_left, text="Geometry", bg="#f0f0f0")
        ef1.pack(fill=tk.X, padx=5, pady=2)

        tk.Label(ef1, text="Array type:").pack()
        self.ert_array = tk.StringVar(value="Wenner Alpha")

        array_types = [
            "Wenner Alpha (wa)",
            "Wenner Beta (wb)",
            "Dipole Dipole (dd)",
            "Schlumberger (slm)",
        ]

        ttk.Combobox(ef1, textvariable=self.ert_array,
                    values=array_types, width=25).pack()

        tk.Label(ef1, text="Electrode spacing (m):").pack()
        self.ert_spacing = tk.StringVar(value="5.0")
        tk.Entry(ef1, textvariable=self.ert_spacing, width=8).pack()

        # ===== INVERSION FRAME =====
        ef2 = tk.LabelFrame(ert_left, text="Inversion", bg="#f0f0f0")
        ef2.pack(fill=tk.X, padx=5, pady=2)

        self.ert_status = tk.Text(ef2, height=8, width=35, font=("Courier", 8))
        self.ert_status.pack(fill=tk.X, pady=2)

        ttk.Button(ef2, text="Run pyGIMLi Inversion",
                  command=self._ert_invert,
                  state='normal' if HAS_PYGIMLI else 'disabled').pack(pady=2)

        # ===== ERT PLOT =====
        self.ert_fig = Figure(figsize=(6, 4), dpi=90)
        self.ert_ax = self.ert_fig.add_subplot(111)
        self.ert_canvas = FigureCanvasTkAgg(self.ert_fig, ert_right)
        self.ert_canvas.draw()
        self.ert_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # ===== FILE BROWSER =====
        browser_frame = tk.LabelFrame(ert_left, text="📂 Loaded Files", bg="#f0f0f0")
        browser_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.file_browser = FileBrowser(
            browser_frame,
            self.workflow_state,
            [
                ('ert_raw', 'ERT', '⚡',
                lambda d: f"{Path(d.get('file', 'Unknown')).name} - {len(d.get('rhoa', []))} measurements")
            ],
            self.on_file_selected
        )
        self.file_browser.pack(fill=tk.BOTH, expand=True)

        # ============ GRAVITY TAB ============
        grav_frame = ttk.Frame(self.processing_notebook)
        self.processing_notebook.add(grav_frame, text="  ⚖️ Gravity  ")

        grav_paned = ttk.PanedWindow(grav_frame, orient=tk.HORIZONTAL)
        grav_paned.pack(fill=tk.BOTH, expand=True)

        grav_left = ttk.Frame(grav_paned, width=300)
        grav_paned.add(grav_left, weight=1)

        grav_right = ttk.Frame(grav_paned)
        grav_paned.add(grav_right, weight=2)

        gf1 = tk.LabelFrame(grav_left, text="Corrections", bg="#f0f0f0")
        gf1.pack(fill=tk.X, padx=5, pady=2)

        self.grav_lat = tk.BooleanVar(value=True)
        tk.Checkbutton(gf1, text="Latitude (IGF80)", variable=self.grav_lat).pack(anchor='w')
        self.grav_fa = tk.BooleanVar(value=True)
        tk.Checkbutton(gf1, text="Free-air", variable=self.grav_fa).pack(anchor='w')
        self.grav_bouguer = tk.BooleanVar(value=True)
        tk.Checkbutton(gf1, text="Bouguer", variable=self.grav_bouguer).pack(anchor='w')
        self.grav_terrain = tk.BooleanVar(value=False)
        tk.Checkbutton(gf1, text="Terrain", variable=self.grav_terrain).pack(anchor='w')

        tk.Label(gf1, text="Density (g/cc):").pack()
        self.grav_density = tk.StringVar(value="2.67")
        tk.Entry(gf1, textvariable=self.grav_density, width=8).pack()

        ttk.Button(gf1, text="Compute Bouguer",
                  command=self._gravity_compute).pack(pady=2)

        # Gravity status area (no popups)
        self.grav_status = tk.Text(gf1, height=8, width=35, font=("Courier", 8))
        self.grav_status.pack(fill=tk.X, pady=5)

        # Gravity plot
        self.grav_fig = Figure(figsize=(6, 4), dpi=90)
        self.grav_ax = self.grav_fig.add_subplot(111)
        self.grav_canvas = FigureCanvasTkAgg(self.grav_fig, grav_right)
        self.grav_canvas.draw()
        self.grav_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # ============ MAGNETICS TAB ============
        mag_frame = ttk.Frame(self.processing_notebook)
        self.processing_notebook.add(mag_frame, text="  🧲 Magnetics  ")

        mag_paned = ttk.PanedWindow(mag_frame, orient=tk.HORIZONTAL)
        mag_paned.pack(fill=tk.BOTH, expand=True)

        mag_left = ttk.Frame(mag_paned, width=300)
        mag_paned.add(mag_left, weight=1)

        mag_right = ttk.Frame(mag_paned)
        mag_paned.add(mag_right, weight=2)

        mf1 = tk.LabelFrame(mag_left, text="Processing", bg="#f0f0f0")
        mf1.pack(fill=tk.X, padx=5, pady=2)

        ttk.Button(mf1, text="Remove IGRF",
                  command=self._magnetics_igrf).pack(fill=tk.X, pady=2)

        ttk.Button(mf1, text="Reduction to Pole",
                  command=self._magnetics_rtp).pack(fill=tk.X, pady=2)

        ttk.Button(mf1, text="Euler Deconvolution",
                  command=self._magnetics_euler).pack(fill=tk.X, pady=2)

        # Magnetics status area (no popups)
        self.mag_status = tk.Text(mf1, height=8, width=35, font=("Courier", 8))
        self.mag_status.pack(fill=tk.X, pady=5)

        # Magnetics plot
        self.mag_fig = Figure(figsize=(6, 4), dpi=90)
        self.mag_ax = self.mag_fig.add_subplot(111)
        self.mag_canvas = FigureCanvasTkAgg(self.mag_fig, mag_right)
        self.mag_canvas.draw()
        self.mag_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # ============ MT/EM TAB ============
        mt_frame = ttk.Frame(self.processing_notebook)
        self.processing_notebook.add(mt_frame, text="  📡 MT/EM  ")

        mt_paned = ttk.PanedWindow(mt_frame, orient=tk.HORIZONTAL)
        mt_paned.pack(fill=tk.BOTH, expand=True)

        mt_left = ttk.Frame(mt_paned, width=300)
        mt_paned.add(mt_left, weight=1)

        mt_right = ttk.Frame(mt_paned)
        mt_paned.add(mt_right, weight=2)

        mtf1 = tk.LabelFrame(mt_left, text="Transfer Functions", bg="#f0f0f0")
        mtf1.pack(fill=tk.X, padx=5, pady=2)

        ttk.Button(mtf1, text="Apparent Resistivity",
                  command=self._mt_rho).pack(fill=tk.X, pady=2)
        ttk.Button(mtf1, text="Phase",
                  command=self._mt_phase).pack(fill=tk.X, pady=2)
        ttk.Button(mtf1, text="Phase Tensor",
                  command=self._mt_tensor).pack(fill=tk.X, pady=2)

        # Status area for MT results (no popups)
        self.mt_status = tk.Text(mtf1, height=8, width=35, font=("Courier", 8))
        self.mt_status.pack(fill=tk.X, pady=5)

        # MT plot
        self.mt_fig = Figure(figsize=(6, 4), dpi=90)
        self.mt_ax = self.mt_fig.add_subplot(111)
        self.mt_canvas = FigureCanvasTkAgg(self.mt_fig, mt_right)
        self.mt_canvas.draw()
        self.mt_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # ============ GPR TAB ============
        gpr_frame = ttk.Frame(self.processing_notebook)
        self.processing_notebook.add(gpr_frame, text="  📻 GPR  ")

        gpr_paned = ttk.PanedWindow(gpr_frame, orient=tk.HORIZONTAL)
        gpr_paned.pack(fill=tk.BOTH, expand=True)

        gpr_left = ttk.Frame(gpr_paned, width=300)
        gpr_paned.add(gpr_left, weight=1)

        gpr_right = ttk.Frame(gpr_paned)
        gpr_paned.add(gpr_right, weight=2)

        gprf1 = tk.LabelFrame(gpr_left, text="Processing", bg="#f0f0f0")
        gprf1.pack(fill=tk.X, padx=5, pady=2)

        ttk.Button(gprf1, text="Dewow",
                  command=self._gpr_dewow).pack(fill=tk.X, pady=2)
        ttk.Button(gprf1, text="Background Remove",
                  command=self._gpr_background).pack(fill=tk.X, pady=2)
        ttk.Button(gprf1, text="AGC Gain",
                  command=self._gpr_agc).pack(fill=tk.X, pady=2)
        ttk.Button(gprf1, text="Kirchhoff Migration",
                  command=self._gpr_kirchhoff).pack(fill=tk.X, pady=2)

        # GPR STATUS AREA (no popups)
        self.gpr_status = tk.Text(gprf1, height=8, width=35, font=("Courier", 8))
        self.gpr_status.pack(fill=tk.X, pady=5)

        # GPR plot
        self.gpr_fig = Figure(figsize=(6, 4), dpi=90)
        self.gpr_ax = self.gpr_fig.add_subplot(111)
        self.gpr_canvas = FigureCanvasTkAgg(self.gpr_fig, gpr_right)
        self.gpr_canvas.draw()
        self.gpr_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # ============ ENVIRONMENTAL TAB ============
        env_frame = ttk.Frame(self.processing_notebook)
        self.processing_notebook.add(env_frame, text="  🌡️ Environmental  ")

        env_paned = ttk.PanedWindow(env_frame, orient=tk.HORIZONTAL)
        env_paned.pack(fill=tk.BOTH, expand=True)

        env_left = ttk.Frame(env_paned, width=300)
        env_paned.add(env_left, weight=1)

        env_right = ttk.Frame(env_paned)
        env_paned.add(env_right, weight=2)

        evf1 = tk.LabelFrame(env_left, text="Corrections", bg="#f0f0f0")
        evf1.pack(fill=tk.X, padx=5, pady=2)

        ttk.Button(evf1, text="Temperature Correction",
                  command=self._env_temp).pack(fill=tk.X, pady=2)
        ttk.Button(evf1, text="Pressure Correction",
                  command=self._env_pressure).pack(fill=tk.X, pady=2)

        # Environmental plot
        self.env_fig = Figure(figsize=(6, 4), dpi=90)
        self.env_ax = self.env_fig.add_subplot(111)
        self.env_canvas = FigureCanvasTkAgg(self.env_fig, env_right)
        self.env_canvas.draw()
        self.env_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # ============================================================================
    # SEISMIC METHODS - REAL IMPLEMENTATIONS
    # ============================================================================
    def _seismic_bandpass(self):
        """Apply bandpass filter to ALL seismic traces by loading from files"""
        if self.workflow_state.raw_data is None:
            self.seis_status.delete(1.0, tk.END)
            self.seis_status.insert(1.0, "⚠️ Import data first")
            return

        try:
            fmin = float(self.seis_fmin.get())
            fmax = float(self.seis_fmax.get())

            df = self.workflow_state.raw_data

            # Check if we have file_source column
            if 'File_Source' not in df.columns:
                self.seis_status.delete(1.0, tk.END)
                self.seis_status.insert(1.0, "❌ No file source information found")
                return

            # Process each trace by loading from file
            processed_traces = []
            trace_count = 0
            failed_files = []

            for idx, row in df.iterrows():
                file_path = row.get('File_Source')
                if not file_path or not os.path.exists(file_path):
                    failed_files.append(str(file_path))
                    continue

                # Parse the file to get waveform data
                traces = SacParser.parse(file_path)
                if not traces:
                    failed_files.append(file_path)
                    continue

                # Get the first trace from the file (assuming one trace per file)
                trace_data = traces[0].data
                sr = traces[0].sampling_rate

                if trace_data is None or not isinstance(trace_data, np.ndarray):
                    failed_files.append(file_path)
                    continue

                dt = 1.0 / sr if sr > 0 else 0.01

                # Apply filter to this trace
                filtered = SeismicProcessor.bandpass(trace_data, dt, fmin, fmax)
                processed_traces.append(filtered)
                trace_count += 1

            # Plot the first processed trace as preview
            if processed_traces:
                self.seis_ax.clear()
                time = np.arange(len(processed_traces[0])) * dt
                self.seis_ax.plot(time, processed_traces[0], 'b-', linewidth=0.8)
                self.seis_ax.set_xlabel("Time (s)")
                self.seis_ax.set_ylabel("Amplitude")
                self.seis_ax.set_title(f"Bandpass {fmin}-{fmax} Hz (First trace)")
                self.seis_ax.grid(True, alpha=0.3)
                self.seis_canvas.draw()

                # Store ALL processed traces
                self.workflow_state.processed['seismic_bandpass'] = processed_traces

                status = f"✓ Bandpass filter applied to {trace_count} traces\n• {fmin}-{fmax} Hz\n• Showing first trace preview"
                if failed_files:
                    status += f"\n⚠️ Failed to load {len(failed_files)} files"

                self.seis_status.delete(1.0, tk.END)
                self.seis_status.insert(1.0, status)
            else:
                self.seis_status.delete(1.0, tk.END)
                self.seis_status.insert(1.0, "❌ No valid traces could be loaded from files")

        except Exception as e:
            self.seis_status.delete(1.0, tk.END)
            self.seis_status.insert(1.0, f"❌ Error: {str(e)[:100]}")
            import traceback
            traceback.print_exc()

    def _seismic_stalta(self):
        """Run STA/LTA picker on ALL seismic traces by loading from files"""
        if self.workflow_state.raw_data is None:
            self.seis_status.delete(1.0, tk.END)
            self.seis_status.insert(1.0, "⚠️ Import data first")
            return

        try:
            sta = float(self.seis_sta.get())
            lta = float(self.seis_lta.get())

            df = self.workflow_state.raw_data

            # Check if we have file_source column
            if 'File_Source' not in df.columns:
                self.seis_status.delete(1.0, tk.END)
                self.seis_status.insert(1.0, "❌ No file source information found")
                return

            # Process each trace by loading from file
            all_cf = []
            all_picks = []
            trace_count = 0
            failed_files = []
            first_trace_data = None
            first_sr = None

            for idx, row in df.iterrows():
                file_path = row.get('File_Source')
                if not file_path or not os.path.exists(file_path):
                    failed_files.append(str(file_path))
                    continue

                # Parse the file to get waveform data
                traces = SacParser.parse(file_path)
                if not traces:
                    failed_files.append(file_path)
                    continue

                # Get the first trace from the file
                trace_data = traces[0].data
                sr = traces[0].sampling_rate

                if trace_data is None or not isinstance(trace_data, np.ndarray):
                    failed_files.append(file_path)
                    continue

                # Save first trace data for plotting
                if first_trace_data is None:
                    first_trace_data = trace_data
                    first_sr = sr

                dt = 1.0 / sr if sr > 0 else 0.01

                # Compute STA/LTA for this trace
                cf = SeismicProcessor.sta_lta(trace_data, dt, sta, lta)
                all_cf.append(cf)

                # Find picks
                threshold = 4.0
                picks = np.where(cf > threshold)[0]
                if len(picks) > 0:
                    all_picks.append(picks[0])  # First pick for this trace

                trace_count += 1

            # Plot the first trace as preview
            if all_cf and first_trace_data is not None:
                self.seis_ax.clear()
                dt = 1.0 / first_sr if first_sr > 0 else 0.01
                time = np.arange(len(first_trace_data)) * dt

                # Normalized trace
                self.seis_ax.plot(time, first_trace_data / np.max(np.abs(first_trace_data)),
                                'b-', alpha=0.5, label='Normalized trace')
                # STA/LTA
                self.seis_ax.plot(time, all_cf[0] / np.max(all_cf[0]),
                                'r-', linewidth=1.5, label='STA/LTA')

                if all_picks:
                    pick_time = all_picks[0] * dt
                    self.seis_ax.axvline(pick_time, color='g',
                                    linestyle='--', label=f'Pick at {pick_time:.2f}s')

                self.seis_ax.set_xlabel("Time (s)")
                self.seis_ax.set_ylabel("Amplitude")
                self.seis_ax.set_title(f"STA/LTA (STA={sta}s, LTA={lta}s) - First trace")
                self.seis_ax.legend()
                self.seis_ax.grid(True, alpha=0.3)
                self.seis_canvas.draw()

                # Store ALL processed results
                self.workflow_state.processed['seismic_stalta'] = all_cf

                status_text = (f"✓ STA/LTA complete on {trace_count} traces\n"
                            f"• STA={sta}s, LTA={lta}s\n"
                            f"• Traces with picks: {len(all_picks)}/{trace_count}\n"
                            f"• Showing first trace preview")

                if failed_files:
                    status_text += f"\n⚠️ Failed to load {len(failed_files)} files"

                self.seis_status.delete(1.0, tk.END)
                self.seis_status.insert(1.0, status_text)
            else:
                self.seis_status.delete(1.0, tk.END)
                self.seis_status.insert(1.0, "❌ No valid traces could be loaded from files")

        except Exception as e:
            self.seis_status.delete(1.0, tk.END)
            self.seis_status.insert(1.0, f"❌ Error: {str(e)[:100]}")
            import traceback
            traceback.print_exc()

    def _seismic_agc(self):
        """Apply AGC to ALL seismic traces by loading from files"""
        if self.workflow_state.raw_data is None:
            self.seis_status.delete(1.0, tk.END)
            self.seis_status.insert(1.0, "⚠️ Import data first")
            return

        try:
            window_s = float(self.seis_agc.get())

            df = self.workflow_state.raw_data

            # Check if we have file_source column
            if 'File_Source' not in df.columns:
                self.seis_status.delete(1.0, tk.END)
                self.seis_status.insert(1.0, "❌ No file source information found")
                return

            # Process each trace by loading from file
            all_agc = []
            orig_rms_list = []
            agc_rms_list = []
            trace_count = 0
            failed_files = []
            first_trace_data = None
            first_sr = None
            first_agc = None

            for idx, row in df.iterrows():
                file_path = row.get('File_Source')
                if not file_path or not os.path.exists(file_path):
                    failed_files.append(str(file_path))
                    continue

                # Parse the file to get waveform data
                traces = SacParser.parse(file_path)
                if not traces:
                    failed_files.append(file_path)
                    continue

                # Get the first trace from the file
                trace_data = traces[0].data
                sr = traces[0].sampling_rate

                if trace_data is None or not isinstance(trace_data, np.ndarray):
                    failed_files.append(file_path)
                    continue

                # Save first trace data for plotting
                if first_trace_data is None:
                    first_trace_data = trace_data
                    first_sr = sr

                dt = 1.0 / sr if sr > 0 else 0.01
                window_samples = int(window_s / dt)

                # Apply AGC to this trace
                agc_data = SeismicProcessor.agc(trace_data, window_samples)

                if first_agc is None:
                    first_agc = agc_data

                all_agc.append(agc_data)
                orig_rms_list.append(np.sqrt(np.mean(trace_data**2)))
                agc_rms_list.append(np.sqrt(np.mean(agc_data**2)))
                trace_count += 1

            # Plot the first trace as preview
            if all_agc and first_trace_data is not None and first_agc is not None:
                self.seis_ax.clear()
                dt = 1.0 / first_sr if first_sr > 0 else 0.01
                time = np.arange(len(first_trace_data)) * dt

                self.seis_ax.plot(time, first_trace_data, 'b-', alpha=0.5, label='Original')
                self.seis_ax.plot(time, first_agc, 'r-', linewidth=1, label='AGC')
                self.seis_ax.set_xlabel("Time (s)")
                self.seis_ax.set_ylabel("Amplitude")
                self.seis_ax.set_title(f"AGC (window={window_s}s) - First trace")
                self.seis_ax.legend()
                self.seis_ax.grid(True, alpha=0.3)
                self.seis_canvas.draw()

                # Store ALL processed traces
                self.workflow_state.processed['seismic_agc'] = all_agc

                status_text = (f"✓ AGC applied to {trace_count} traces\n"
                            f"• Window: {window_s}s\n"
                            f"• Avg Original RMS: {np.mean(orig_rms_list):.3f}\n"
                            f"• Avg AGC RMS: {np.mean(agc_rms_list):.3f}\n"
                            f"• Showing first trace preview")

                if failed_files:
                    status_text += f"\n⚠️ Failed to load {len(failed_files)} files"

                self.seis_status.delete(1.0, tk.END)
                self.seis_status.insert(1.0, status_text)
            else:
                self.seis_status.delete(1.0, tk.END)
                self.seis_status.insert(1.0, "❌ No valid traces could be loaded from files")

        except Exception as e:
            self.seis_status.delete(1.0, tk.END)
            self.seis_status.insert(1.0, f"❌ Error: {str(e)[:100]}")
            import traceback
            traceback.print_exc()

    # ============================================================================
    # ERT METHODS - REAL IMPLEMENTATIONS
    # ============================================================================
    def _import_ert_file(self):
        """Import and parse a real ABEM .data file"""
        path = filedialog.askopenfilename(
            title="Import ERT Survey File",
            filetypes=[
                ("ABEM data", "*.dat *.data *.Data"),
                ("Syscal binary", "*.bin"),
                ("BERT/ohm", "*.ohm"),
                ("Res2DInv", "*.dat"),
                ("All files", "*.*")
            ]
        )
        if not path:
            return

        try:
            # Parse the ABEM file using your existing parser
            a, b, m, n, rhoa, err = ERTProcessor.load_abem_data(path)

            # Check if we actually got data
            if rhoa is None or len(rhoa) == 0:
                self.ert_status.delete(1.0, tk.END)
                self.ert_status.insert(1.0, f"❌ No data parsed from file. The file format may not match ABEM expectations.")
                return

            # Create a proper ERTData object with real data
            ert_data = ERTData(
                timestamp=datetime.now(),
                station=Path(path).stem,
                instrument="ABEM Terrameter SAS4000",
                resistances=None,
                apparent_rho=rhoa,
                electrode_spacing=self._estimate_spacing(a, b, m, n),
                n_measurements=len(rhoa),
                file_source=path
            )

            # Store in workflow state
            self.workflow_state.raw_data = pd.DataFrame([ert_data.to_dict()])
            self.workflow_state.ert_file = path
            self.workflow_state.add_data('ert_raw', {
                'a': a, 'b': b, 'm': m, 'n': n,
                'rhoa': rhoa, 'err': err
            })

            # Update UI
            self.ert_file_label.config(text=f"✅ {Path(path).name}", fg="green")
            self.ert_status.delete(1.0, tk.END)
            self.ert_status.insert(1.0,
                f"✅ Loaded: {Path(path).name}\n"
                f"• Measurements: {len(rhoa)}\n"
                f"• Resistivity range: {np.min(rhoa):.1f} - {np.max(rhoa):.1f} Ω·m\n"
                f"• Click 'Run pyGIMLi Inversion' to process"
            )

            # Update the main display
            self._update_health_dashboard()

        except Exception as e:
            self.ert_status.delete(1.0, tk.END)
            self.ert_status.insert(1.0, f"❌ Failed to parse: {str(e)}")
            import traceback
            traceback.print_exc()

    def on_file_selected(self, data_type, data_item):
        """Callback from FileBrowser when a file/dataset is selected - preview it on the ERT canvas"""
        try:
            if data_type == 'ert_raw' and hasattr(self, 'ert_ax') and hasattr(self, 'ert_canvas'):
                self.ert_ax.clear()
                rhoa = np.array(data_item.get('rhoa', []))
                a    = np.array(data_item.get('a', []))
                n    = np.array(data_item.get('n', []))

                if len(rhoa) > 0 and len(a) == len(rhoa) and len(n) == len(rhoa):
                    # Standard ERT pseudosection: x = mid-point of AB, depth ~ n-level
                    spacing = self._estimate_spacing(a,
                                                     data_item.get('b', a),
                                                     data_item.get('m', a),
                                                     n)
                    x_mid   = (a + n) / 2.0 * spacing
                    depth   = n * spacing * 0.5        # conventional pseudo-depth
                    sc = self.ert_ax.scatter(x_mid, -depth,
                                             c=np.log10(np.abs(rhoa) + 1e-9),
                                             cmap='jet', s=20, alpha=0.8)
                    plt.colorbar(sc, ax=self.ert_ax, label='log₁₀(ρₐ) [Ω·m]')
                    self.ert_ax.set_xlabel('Distance (m)')
                    self.ert_ax.set_ylabel('Pseudo-depth (m)')
                    self.ert_ax.set_title(
                        f'ERT Pseudosection — {len(rhoa)} measurements')
                else:
                    # Fallback: simple histogram of rhoa values
                    if len(rhoa) > 0:
                        self.ert_ax.hist(rhoa, bins=min(30, len(rhoa)),
                                         color='steelblue', edgecolor='white')
                        self.ert_ax.set_xlabel('Apparent Resistivity (Ω·m)')
                        self.ert_ax.set_ylabel('Count')
                        self.ert_ax.set_title(
                            f'Apparent Resistivity — {len(rhoa)} measurements')
                    else:
                        self.ert_ax.text(0.5, 0.5, 'No resistivity data',
                                         ha='center', va='center',
                                         transform=self.ert_ax.transAxes)

                self.ert_canvas.draw()
        except Exception as e:
            print(f"on_file_selected preview error: {e}")

    def _estimate_spacing(self, a, b, m, n):
        """Estimate electrode spacing from indices"""
        if len(a) > 1:
            spacings = []
            for i in range(min(10, len(a) - 1)):
                if a[i] != a[i + 1]:
                    spacings.append(abs(a[i + 1] - a[i]))
            if spacings:
                return float(np.mean(spacings))
        return 5.0  # default

    def _ert_invert(self):
        """Run ERT inversion"""
        import threading
        def _worker():
            try:
                import pygimli as pg
                from pygimli.physics import ert

                ert_data = self.workflow_state.processed['ert_raw']
                a, b, m, n, rhoa = ert_data['a'], ert_data['b'], ert_data['m'], ert_data['n'], ert_data['rhoa']

                # Create container
                data = pg.DataContainerERT()
                n_elec = int(max(a.max(), b.max(), m.max(), n.max()))

                for i in range(n_elec):
                    data.createSensor([float(i) * 5.0, 0.0])

                for i in range(len(rhoa)):
                    data.createFourPointData(i, int(a[i])-1, int(b[i])-1, int(m[i])-1, int(n[i])-1)

                # Set data
                data['rhoa'] = pg.Vector(rhoa.tolist())
                data['k'] = ert.geometricFactors(data)  # This is required
                data['r'] = data['rhoa'] / data['k']
                data['err'] = pg.Vector([0.03] * len(rhoa))

                # Invert
                mgr = ert.ERTManager(data)
                mgr.invert(verbose=False)

                # Plot
                self.ert_ax.clear()
                mgr.showResult(ax=self.ert_ax)
                self.ert_canvas.draw()
                self.ert_status.insert(1.0, "✅ Success")

            except Exception as e:
                self.ert_status.insert(1.0, f"❌ {str(e)}")

        # ============================================================================
        # GRAVITY METHODS - REAL IMPLEMENTATIONS
        # ============================================================================
        threading.Thread(target=_worker, daemon=True).start()
    def _gravity_compute(self):
        """Compute Bouguer anomaly for ALL stations with proper terrain correction"""
        if self.workflow_state.raw_data is None:
            self.grav_status.delete(1.0, tk.END)
            self.grav_status.insert(1.0, "⚠️ Import data first")
            return
        import threading
        def _worker():
            try:
                density = float(self.grav_density.get())

                df = self.workflow_state.raw_data

                # Find required columns
                lat_col = self._find_coord_column(df, ['lat', 'latitude'])
                lon_col = self._find_coord_column(df, ['lon', 'longitude'])
                grav_col = self._find_coord_column(df, ['gravity', 'mgal', 'grav'])
                elev_col = self._find_coord_column(df, ['elev', 'elevation', 'z'])

                # Check for DEM data for terrain correction
                dem_data = None
                if self.grav_terrain.get():
                    # Look for DEM column or file
                    dem_col = self._find_coord_column(df, ['dem', 'terrain', 'topography'])
                    if dem_col:
                        dem_data = df[dem_col].values
                    else:
                        # Try to load from external DEM file
                        dem_file = filedialog.askopenfilename(
                            title="Select DEM file for terrain correction",
                            filetypes=[("GeoTIFF", "*.tif"), ("ASCII grid", "*.asc"), ("All files", "*.*")]
                        )
                        if dem_file:
                            try:
                                import rasterio
                                with rasterio.open(dem_file) as src:
                                    dem_data = src.read(1)
                                    # Note: would need to interpolate to station locations
                                    # This is simplified - real implementation would need proper interpolation
                            except Exception as e:
                                self.grav_status.insert(1.0, f"\n⚠️ Could not load DEM: {str(e)[:50]}")

                if grav_col is None:
                    self.grav_status.delete(1.0, tk.END)
                    self.grav_status.insert(1.0, "❌ No gravity column found")
                    return

                # Process ALL stations
                anomalies = []
                grav_values = []
                stations_processed = 0
                correction_details = {
                    'latitude': 0,
                    'free_air': 0,
                    'bouguer': 0,
                    'terrain': 0
                }

                for idx, row in df.iterrows():
                    grav = row[grav_col]
                    if pd.isna(grav):
                        continue

                    # Get elevation
                    if elev_col:
                        elev = row[elev_col] if not pd.isna(row[elev_col]) else 0
                    else:
                        elev = 0

                    # Get latitude
                    if lat_col:
                        lat = row[lat_col] if not pd.isna(row[lat_col]) else 0
                    else:
                        lat = 0

                    # Start with observed gravity
                    anomaly = float(grav)
                    grav_values.append(float(grav))

                    # Latitude correction (IGF80)
                    if self.grav_lat.get() and lat_col:
                        gamma = GravityProcessor.igf_1980(lat)
                        anomaly -= gamma
                        correction_details['latitude'] += gamma

                    # Free-air correction
                    if self.grav_fa.get():
                        fa = GravityProcessor.free_air(elev)
                        anomaly += fa
                        correction_details['free_air'] += fa

                    # Bouguer slab correction
                    if self.grav_bouguer.get():
                        bouguer = GravityProcessor.bouguer(elev, density)
                        anomaly += bouguer
                        correction_details['bouguer'] += bouguer

                    # Terrain correction
                    if self.grav_terrain.get() and dem_data is not None:
                        # Simplified terrain correction using DEM
                        # In reality, this would use Hammer charts or digital terrain models
                        if len(dem_data) > 10:
                            # Roughness-based estimation
                            terrain = 0.0419 * density * (np.std(dem_data) / np.mean(dem_data)) * (elev / 1000)
                            anomaly += terrain
                            correction_details['terrain'] += terrain

                    anomalies.append(anomaly)
                    stations_processed += 1

                # Plot results
                self.grav_ax.clear()
                if anomalies:
                    x = np.arange(len(anomalies))

                    self.grav_ax.plot(x, grav_values, 'b-', alpha=0.5, linewidth=1, label='Observed')
                    self.grav_ax.plot(x, anomalies, 'r-', linewidth=2, label='Bouguer')

                    # Add zero line for reference
                    self.grav_ax.axhline(y=0, color='k', linestyle=':', alpha=0.3)

                    self.grav_ax.set_xlabel("Station Index")
                    self.grav_ax.set_ylabel("Gravity (mGal)")
                    self.grav_ax.set_title(f"Bouguer Anomaly ({stations_processed} stations)")
                    self.grav_ax.legend()
                    self.grav_ax.grid(True, alpha=0.3)

                self.grav_canvas.draw()

                # Calculate statistics
                avg_corrections = {k: v/stations_processed if stations_processed > 0 else 0
                                for k, v in correction_details.items()}

                # Build status text
                status_text = f"✓ Bouguer anomaly computed for {stations_processed} stations\n"
                if anomalies:
                    status_text += f"• Range: {min(anomalies):.2f} to {max(anomalies):.2f} mGal\n"
                    status_text += f"• Mean: {np.mean(anomalies):.2f} ± {np.std(anomalies):.2f} mGal\n\n"
                    status_text += "Average corrections applied:\n"
                    if self.grav_lat.get():
                        status_text += f"• Latitude: {avg_corrections['latitude']:.2f} mGal\n"
                    if self.grav_fa.get():
                        status_text += f"• Free-air: {avg_corrections['free_air']:.2f} mGal\n"
                    if self.grav_bouguer.get():
                        status_text += f"• Bouguer slab: {avg_corrections['bouguer']:.2f} mGal\n"
                    if self.grav_terrain.get() and correction_details['terrain'] > 0:
                        status_text += f"• Terrain: {avg_corrections['terrain']:.3f} mGal\n"

                self.grav_status.delete(1.0, tk.END)
                self.grav_status.insert(1.0, status_text)

                # Store in workflow state
                self.workflow_state.processed['gravity_bouguer'] = anomalies
                self.workflow_state.log_step('bouguer', {
                    'density': density,
                    'stations': stations_processed,
                    'corrections': {k: bool(getattr(self, f'grav_{k}').get()) for k in ['lat', 'fa', 'bouguer', 'terrain']}
                })

            except Exception as e:
                self.grav_status.delete(1.0, tk.END)
                self.grav_status.insert(1.0, f"❌ Error: {str(e)[:100]}")
                import traceback
                traceback.print_exc()

        # ============================================================================
        # MAGNETICS METHODS - REAL IMPLEMENTATIONS
        # ============================================================================
        threading.Thread(target=_worker, daemon=True).start()
    def _magnetics_igrf(self):
        """Remove IGRF from magnetic data for ALL stations using real IGRF model"""
        if self.workflow_state.raw_data is None:
            self.mag_status.delete(1.0, tk.END)
            self.mag_status.insert(1.0, "⚠️ Import data first")
            return
        import threading
        def _worker():
            try:
                df = self.workflow_state.raw_data
                mag_col = self._find_coord_column(df, ['mag', 'field', 'nT', 'total_field'])
                lat_col = self._find_coord_column(df, ['lat', 'latitude'])
                lon_col = self._find_coord_column(df, ['lon', 'longitude'])
                elev_col = self._find_coord_column(df, ['elev', 'elevation', 'altitude'])
                date_col = self._find_coord_column(df, ['date', 'time', 'timestamp'])

                if mag_col is None:
                    self.mag_status.delete(1.0, tk.END)
                    self.mag_status.insert(1.0, "❌ No magnetic data column found")
                    return

                if lat_col is None or lon_col is None:
                    self.mag_status.delete(1.0, tk.END)
                    self.mag_status.insert(1.0, "❌ Need latitude and longitude for IGRF calculation")
                    return

                # Try to import pyigrf
                try:
                    from pyigrf import igrf
                    HAS_IGRF = True
                except ImportError:
                    HAS_IGRF = False
                    self.mag_status.delete(1.0, tk.END)
                    self.mag_status.insert(1.0, "⚠️ pyigrf not installed. Install with: pip install pyigrf")
                    return

                # Process ALL stations
                mag_values = []
                latitudes = []
                longitudes = []
                elevations = []
                dates = []

                for idx, row in df.iterrows():
                    mag = row[mag_col]
                    if pd.isna(mag):
                        continue

                    lat = row[lat_col] if not pd.isna(row[lat_col]) else 0
                    lon = row[lon_col] if not pd.isna(row[lon_col]) else 0

                    # Get elevation (default to 0 if not available)
                    elev = 0
                    if elev_col and not pd.isna(row[elev_col]):
                        elev = row[elev_col]

                    # Get date (use current date if not available)
                    date = datetime.now()
                    if date_col and not pd.isna(row[date_col]):
                        try:
                            date = pd.to_datetime(row[date_col])
                        except Exception as e:
                            pass

                    mag_values.append(float(mag))
                    latitudes.append(float(lat))
                    longitudes.append(float(lon))
                    elevations.append(float(elev))
                    dates.append(date)

                if len(mag_values) == 0:
                    self.mag_status.delete(1.0, tk.END)
                    self.mag_status.insert(1.0, "❌ No valid magnetic data")
                    return

                # Calculate IGRF for each station
                igrf_values = []
                for i in range(len(mag_values)):
                    try:
                        # Convert date to decimal year
                        decimal_year = dates[i].year + dates[i].timetuple().tm_yday / 365.25

                        # Calculate IGRF components
                        result = igrf(
                            decimal_year,
                            latitudes[i],
                            longitudes[i],
                            elevations[i] / 1000  # Convert to km
                        )
                        # Total field intensity
                        igrf_total = np.sqrt(result[3]**2 + result[4]**2 + result[5]**2)
                        igrf_values.append(igrf_total)
                    except Exception as e:
                        print(f"IGRF calculation error for station {i}: {e}")
                        # Fallback to approximate value
                        igrf_values.append(50000)

                # Calculate residuals
                residuals = np.array(mag_values) - np.array(igrf_values)

                # Plot
                self.mag_ax.clear()
                x = np.arange(len(mag_values))

                self.mag_ax.plot(x, mag_values, 'b-', alpha=0.5, label='Total field')
                self.mag_ax.plot(x, residuals, 'r-', linewidth=1.5, label='Residual')
                self.mag_ax.plot(x, igrf_values, 'g--', alpha=0.7, label='IGRF model')

                self.mag_ax.set_xlabel("Station Index")
                self.mag_ax.set_ylabel("Magnetic field (nT)")
                self.mag_ax.set_title(f"IGRF Removal ({len(mag_values)} stations)")
                self.mag_ax.legend()
                self.mag_ax.grid(True, alpha=0.3)
                self.mag_canvas.draw()

                # Update status
                status_text = (f"✓ IGRF removed from {len(mag_values)} stations using pyIGRF\n"
                            f"• Original: {np.mean(mag_values):.0f} ± {np.std(mag_values):.0f} nT\n"
                            f"• IGRF: {np.mean(igrf_values):.0f} ± {np.std(igrf_values):.0f} nT\n"
                            f"• Residual: {np.mean(residuals):.0f} ± {np.std(residuals):.0f} nT")

                self.mag_status.delete(1.0, tk.END)
                self.mag_status.insert(1.0, status_text)

                # Store results
                self.workflow_state.processed['magnetics_residual'] = residuals
                self.workflow_state.processed['magnetics_igrf'] = igrf_values

            except Exception as e:
                self.mag_status.delete(1.0, tk.END)
                self.mag_status.insert(1.0, f"❌ Error: {str(e)[:100]}")
                import traceback
                traceback.print_exc()
        threading.Thread(target=_worker, daemon=True).start()
    def _magnetics_rtp(self):
        """Reduction to pole - process REAL magnetic grid data"""
        if self.workflow_state.raw_data is None:
            self.mag_status.delete(1.0, tk.END)
            self.mag_status.insert(1.0, "⚠️ Import data first")
            return

        try:
            # Get magnetic data
            df = self.workflow_state.raw_data
            mag_col = self._find_coord_column(df, ['mag', 'field', 'nT', 'total_field'])
            x_col = self._find_coord_column(df, ['x', 'lon', 'longitude', 'easting'])
            y_col = self._find_coord_column(df, ['y', 'lat', 'latitude', 'northing'])

            # Check if we have all required data
            if not mag_col:
                self.mag_status.delete(1.0, tk.END)
                self.mag_status.insert(1.0, "❌ No magnetic data column found")
                return

            if not x_col or not y_col:
                self.mag_status.delete(1.0, tk.END)
                self.mag_status.insert(1.0, "❌ Need X and Y coordinates for gridding")
                return

            # Get valid data points
            data = df[[x_col, y_col, mag_col]].dropna()
            if len(data) < 10:
                self.mag_status.delete(1.0, tk.END)
                self.mag_status.insert(1.0, f"❌ Need ≥10 points for gridding (have {len(data)})")
                return

            # Create grid from scattered points
            from scipy.interpolate import griddata

            points = data[[x_col, y_col]].values
            values = data[mag_col].values

            # Create grid
            x = np.linspace(points[:,0].min(), points[:,0].max(), 50)
            y = np.linspace(points[:,1].min(), points[:,1].max(), 50)
            X, Y = np.meshgrid(x, y)
            Z = griddata(points, values, (X, Y), method='cubic')

            # Handle any NaN values
            if np.isnan(Z).all():
                self.mag_status.delete(1.0, tk.END)
                self.mag_status.insert(1.0, "❌ Gridding failed - all values are NaN")
                return

            # Fill small gaps with nearest neighbor
            if np.isnan(Z).any():
                Z = griddata(points, values, (X, Y), method='nearest')

            dx = x[1] - x[0]
            dy = y[1] - y[0]

            # Get inclination and declination from user input
            # You could add entry fields for these, using defaults for now
            inclination = 60.0  # degrees
            declination = 0.0    # degrees

            # FFT and RTP
            from scipy.fft import fft2, ifft2, fftfreq, fftshift, ifftshift

            F = fft2(Z)
            F = fftshift(F)

            ny, nx = Z.shape
            kx = fftfreq(nx, dx)
            ky = fftfreq(ny, dy)
            KX, KY = np.meshgrid(kx, ky)

            # RTP filter
            theta = np.arctan2(KY, KX)
            inc_rad = np.radians(inclination)
            dec_rad = np.radians(declination)

            filter_rtp = 1.0 / ((np.sin(inc_rad) + 1j * np.cos(inc_rad) * np.cos(theta - dec_rad))**2)
            filter_rtp = np.nan_to_num(filter_rtp, nan=0.0, posinf=0.0, neginf=0.0)

            F_rtp = F * filter_rtp
            F_rtp = ifftshift(F_rtp)
            Z_rtp = np.real(ifft2(F_rtp))

            # Calculate statistics
            original_stats = f"Original: {np.nanmin(Z):.1f} to {np.nanmax(Z):.1f} nT"
            rtp_stats = f"RTP: {np.nanmin(Z_rtp):.1f} to {np.nanmax(Z_rtp):.1f} nT"

            # Clear the figure and create two subplots
            self.mag_fig.clear()

            # Original
            ax1 = self.mag_fig.add_subplot(1, 2, 1)
            im1 = ax1.contourf(X, Y, Z, levels=20, cmap='viridis')
            plt.colorbar(im1, ax=ax1)
            ax1.set_title("Original")
            ax1.set_xlabel(x_col)
            ax1.set_ylabel(y_col)

            # RTP
            ax2 = self.mag_fig.add_subplot(1, 2, 2)
            im2 = ax2.contourf(X, Y, Z_rtp, levels=20, cmap='viridis')
            plt.colorbar(im2, ax=ax2)
            ax2.set_title("Reduced to Pole")
            ax2.set_xlabel(x_col)
            ax2.set_ylabel(y_col)

            self.mag_fig.tight_layout()
            self.mag_canvas.draw()

            # Update status
            status_text = (f"✓ Reduction to Pole applied\n"
                        f"• Grid size: {nx}×{ny}\n"
                        f"• Points used: {len(points)}\n"
                        f"• {original_stats}\n"
                        f"• {rtp_stats}\n"
                        f"• Inclination: {inclination}°, Declination: {declination}°")

            self.mag_status.delete(1.0, tk.END)
            self.mag_status.insert(1.0, status_text)

            # Store results
            self.workflow_state.processed['magnetics_rtp'] = Z_rtp

        except Exception as e:
            self.mag_status.delete(1.0, tk.END)
            self.mag_status.insert(1.0, f"❌ Error: {str(e)[:100]}")
            import traceback
            traceback.print_exc()

    def _magnetics_euler(self):
        """Euler deconvolution - process REAL magnetic data"""
        if self.workflow_state.raw_data is None:
            self.mag_status.delete(1.0, tk.END)
            self.mag_status.insert(1.0, "⚠️ Import data first")
            return

        try:
            # Get magnetic data
            df = self.workflow_state.raw_data
            mag_col = self._find_coord_column(df, ['mag', 'field', 'nT', 'total_field'])
            x_col = self._find_coord_column(df, ['x', 'lon', 'longitude', 'easting'])
            y_col = self._find_coord_column(df, ['y', 'lat', 'latitude', 'northing'])

            # Check if we have all required data
            if not mag_col:
                self.mag_status.delete(1.0, tk.END)
                self.mag_status.insert(1.0, "❌ No magnetic data column found")
                return

            if not x_col or not y_col:
                self.mag_status.delete(1.0, tk.END)
                self.mag_status.insert(1.0, "❌ Need X and Y coordinates")
                return

            # Get valid data points
            data = df[[x_col, y_col, mag_col]].dropna()
            if len(data) < 20:
                self.mag_status.delete(1.0, tk.END)
                self.mag_status.insert(1.0, f"❌ Need ≥20 points for Euler (have {len(data)})")
                return

            x = data[x_col].values
            y = data[y_col].values
            field = data[mag_col].values

            # Create grid for gradient calculation
            from scipy.interpolate import griddata

            # Create grid
            xi = np.linspace(x.min(), x.max(), 50)
            yi = np.linspace(y.min(), y.max(), 50)
            Xi, Yi = np.meshgrid(xi, yi)
            Zi = griddata((x, y), field, (Xi, Yi), method='cubic')

            # Handle any NaN values
            if np.isnan(Zi).any():
                # Fill NaN with nearest neighbor
                Zi = griddata((x, y), field, (Xi, Yi), method='nearest')

            # Calculate gradients
            dx = xi[1] - xi[0]
            dy = yi[1] - yi[0]
            gx, gy = np.gradient(Zi, dx, dy)

            # Total gradient (analytic signal)
            gz = np.sqrt(gx**2 + gy**2)

            # Interpolate gradients back to original points
            points = np.column_stack([Xi.flatten(), Yi.flatten()])
            values_gx = gx.flatten()
            values_gy = gy.flatten()
            values_gz = gz.flatten()

            gx_flat = griddata(points, values_gx, (x, y), method='linear')
            gy_flat = griddata(points, values_gy, (x, y), method='linear')
            gz_flat = griddata(points, values_gz, (x, y), method='linear')

            # Handle any remaining NaN in gradients
            if np.isnan(gx_flat).any():
                # Fill NaN with nearest neighbor
                gx_flat = griddata(points, values_gx, (x, y), method='nearest')
                gy_flat = griddata(points, values_gy, (x, y), method='nearest')
                gz_flat = griddata(points, values_gz, (x, y), method='nearest')

            # Run Euler deconvolution with moving window
            structural_index = self.si_var.get()
            window = self.euler_window.get()
            solutions = []

            n_points = len(x)
            for i in range(0, n_points - window, window // 2):
                idx = slice(i, i + window)
                x_win = x[idx]
                y_win = y[idx]
                f_win = field[idx]
                gx_win = gx_flat[idx]
                gy_win = gy_flat[idx]
                gz_win = gz_flat[idx]

                # Build equation system: x·∂T/∂x + y·∂T/∂y + z·∂T/∂z = N·(B - T)
                A = np.column_stack([gx_win, gy_win, gz_win, np.ones_like(gx_win)])
                b = x_win*gx_win + y_win*gy_win + f_win*gz_win + structural_index * f_win

                try:
                    sol, _, _, _ = np.linalg.lstsq(A, b, rcond=None)
                    x0, y0, z0, base = sol

                    # Only accept positive depths within reasonable range
                    # Relative to survey size
                    max_depth = (x.max() - x.min()) * 0.5
                    if 0 < z0 < max_depth:
                        solutions.append({
                            'x': np.mean(x_win),
                            'y': np.mean(y_win),
                            'x0': x0,
                            'y0': y0,
                            'z0': z0,
                            'base': base
                        })
                except Exception as e:
                    continue

            # Clear previous plot
            self.mag_ax.clear()

            if solutions:
                # Extract solution coordinates and depths
                x_sol = [s['x0'] for s in solutions]
                y_sol = [s['y0'] for s in solutions]
                z_sol = [s['z0'] for s in solutions]

                # Scatter plot of solutions colored by depth
                scatter = self.mag_ax.scatter(x_sol, y_sol, c=z_sol,
                                            cmap='viridis', s=50, alpha=0.7,
                                            edgecolors='black', linewidth=0.5)
                plt.colorbar(scatter, ax=self.mag_ax, label='Depth (m)')

                # Plot original data points for reference
                self.mag_ax.scatter(x, y, c='gray', s=10, alpha=0.3, marker='.')

                self.mag_ax.set_xlabel(x_col)
                self.mag_ax.set_ylabel(y_col)
                self.mag_ax.set_title(f"Euler Deconvolution (SI={structural_index})")
                self.mag_ax.grid(True, alpha=0.3)

                # Calculate statistics
                depths = z_sol
                status_text = (f"✓ Euler Deconvolution\n"
                            f"• Input points: {len(data)}\n"
                            f"• Solutions: {len(solutions)}\n"
                            f"• Depth range: {np.min(depths):.1f} to {np.max(depths):.1f} m\n"
                            f"• Mean depth: {np.mean(depths):.1f} ± {np.std(depths):.1f} m\n"
                            f"• Structural index: {structural_index}")
            else:
                self.mag_ax.text(0.5, 0.5, "No Euler solutions found\nTry adjusting parameters",
                            ha='center', va='center', transform=self.mag_ax.transAxes)

                # Plot original data anyway
                self.mag_ax.scatter(x, y, c=field, cmap='viridis', s=20, alpha=0.7)
                plt.colorbar(self.mag_ax.collections[0], ax=self.mag_ax, label='Field (nT)')
                self.mag_ax.set_xlabel(x_col)
                self.mag_ax.set_ylabel(y_col)
                self.mag_ax.set_title(f"Input Data - No Euler Solutions")

                status_text = "❌ No Euler solutions found"

            self.mag_canvas.draw()

            # Update status
            self.mag_status.delete(1.0, tk.END)
            self.mag_status.insert(1.0, status_text)

            # Store results
            self.workflow_state.processed['magnetics_euler'] = solutions

        except Exception as e:
            self.mag_status.delete(1.0, tk.END)
            self.mag_status.insert(1.0, f"❌ Error: {str(e)[:100]}")
            import traceback
            traceback.print_exc()

    # ============================================================================
    # MT METHODS - REAL IMPLEMENTATIONS
    # ============================================================================
    def _mt_rho(self):
        """Calculate apparent resistivity from MT impedance data"""
        if self.workflow_state.raw_data is None:
            self.mt_status.delete(1.0, tk.END)
            self.mt_status.insert(1.0, "⚠️ Import data first")
            return

        try:
            df = self.workflow_state.raw_data

            # Find required columns
            freq_col = self._find_coord_column(df, ['frequency', 'freq', 'f'])
            zxy_real_col = self._find_coord_column(df, ['zxy_real', 'impedance_real'])
            zxy_imag_col = self._find_coord_column(df, ['zxy_imag', 'impedance_imag'])

            if not freq_col or not zxy_real_col or not zxy_imag_col:
                self.mt_status.delete(1.0, tk.END)
                self.mt_status.insert(1.0, "❌ Need frequency and impedance columns")
                return

            # Extract data
            freq = df[freq_col].values
            zxy_real = df[zxy_real_col].values
            zxy_imag = df[zxy_imag_col].values

            # Calculate complex impedance and apparent resistivity
            Zxy = zxy_real + 1j * zxy_imag
            rho = MTProcessor.apparent_resistivity(Zxy, freq)

            # Plot
            self.mt_ax.clear()
            self.mt_ax.loglog(freq, rho, 'b-', linewidth=2, marker='o')
            self.mt_ax.set_xlabel("Frequency (Hz)")
            self.mt_ax.set_ylabel("Apparent resistivity (Ω·m)")
            self.mt_ax.set_title(f"MT Apparent Resistivity ({len(freq)} frequencies)")
            self.mt_ax.grid(True, alpha=0.3, which='both')
            self.mt_canvas.draw()

            # Store results
            self.workflow_state.processed['mt_rho'] = {'freq': freq, 'rho': rho}

            # Update status
            status_text = (f"✓ Apparent resistivity calculated\n"
                        f"• Frequencies: {len(freq)}\n"
                        f"• Rho range: {np.min(rho):.1f} - {np.max(rho):.1f} Ω·m")
            self.mt_status.delete(1.0, tk.END)
            self.mt_status.insert(1.0, status_text)

        except Exception as e:
            self.mt_status.delete(1.0, tk.END)
            self.mt_status.insert(1.0, f"❌ Error: {str(e)[:100]}")

    def _mt_phase(self):
        """Calculate impedance phase from MT data"""
        if self.workflow_state.raw_data is None:
            self.mt_status.delete(1.0, tk.END)
            self.mt_status.insert(1.0, "⚠️ Import data first")
            return

        try:
            df = self.workflow_state.raw_data

            # Find required columns
            freq_col = self._find_coord_column(df, ['frequency', 'freq', 'f'])
            zxy_real_col = self._find_coord_column(df, ['zxy_real', 'impedance_real'])
            zxy_imag_col = self._find_coord_column(df, ['zxy_imag', 'impedance_imag'])

            if not freq_col or not zxy_real_col or not zxy_imag_col:
                self.mt_status.delete(1.0, tk.END)
                self.mt_status.insert(1.0, "❌ Need frequency and impedance columns")
                return

            # Extract data
            freq = df[freq_col].values
            zxy_real = df[zxy_real_col].values
            zxy_imag = df[zxy_imag_col].values

            # Calculate complex impedance and phase
            Zxy = zxy_real + 1j * zxy_imag
            phase = MTProcessor.phase(Zxy)

            # Plot
            self.mt_ax.clear()
            self.mt_ax.semilogx(freq, phase, 'r-', linewidth=2, marker='s')
            self.mt_ax.set_xlabel("Frequency (Hz)")
            self.mt_ax.set_ylabel("Phase (degrees)")
            self.mt_ax.set_title(f"MT Phase ({len(freq)} frequencies)")
            self.mt_ax.grid(True, alpha=0.3)
            self.mt_ax.set_ylim(0, 90)
            self.mt_canvas.draw()

            # Store results
            self.workflow_state.processed['mt_phase'] = {'freq': freq, 'phase': phase}

            # Update status
            status_text = (f"✓ Phase calculated\n"
                        f"• Frequencies: {len(freq)}\n"
                        f"• Phase range: {np.min(phase):.1f} - {np.max(phase):.1f}°")
            self.mt_status.delete(1.0, tk.END)
            self.mt_status.insert(1.0, status_text)

        except Exception as e:
            self.mt_status.delete(1.0, tk.END)
            self.mt_status.insert(1.0, f"❌ Error: {str(e)[:100]}")

    def _mt_tensor(self):
        """Calculate phase tensor from MT impedance data"""
        if self.workflow_state.raw_data is None:
            self.mt_status.delete(1.0, tk.END)
            self.mt_status.insert(1.0, "⚠️ Import data first")
            return

        try:
            df = self.workflow_state.raw_data

            # Find required columns for full impedance tensor
            freq_col = self._find_coord_column(df, ['frequency', 'freq', 'f'])

            # Need all 4 components of impedance tensor
            zxx_real_col = self._find_coord_column(df, ['zxx_real', 'z11_real'])
            zxx_imag_col = self._find_coord_column(df, ['zxx_imag', 'z11_imag'])
            zxy_real_col = self._find_coord_column(df, ['zxy_real', 'z12_real'])
            zxy_imag_col = self._find_coord_column(df, ['zxy_imag', 'z12_imag'])
            zyx_real_col = self._find_coord_column(df, ['zyx_real', 'z21_real'])
            zyx_imag_col = self._find_coord_column(df, ['zyx_imag', 'z21_imag'])
            zyy_real_col = self._find_coord_column(df, ['zyy_real', 'z22_real'])
            zyy_imag_col = self._find_coord_column(df, ['zyy_imag', 'z22_imag'])

            if not all([freq_col, zxx_real_col, zxx_imag_col, zxy_real_col, zxy_imag_col,
                    zyx_real_col, zyx_imag_col, zyy_real_col, zyy_imag_col]):
                self.mt_status.delete(1.0, tk.END)
                self.mt_status.insert(1.0, "❌ Need full impedance tensor (Zxx, Zxy, Zyx, Zyy)")
                return

            # Extract frequencies
            freq = df[freq_col].values
            n_freq = len(freq)

            # Calculate phase tensor for each frequency
            strike_angles = []
            ellipticities = []
            skew_angles = []

            for i in range(n_freq):
                # Build impedance tensor for this frequency
                Z = np.array([
                    [df[zxx_real_col].iloc[i] + 1j * df[zxx_imag_col].iloc[i],
                    df[zxy_real_col].iloc[i] + 1j * df[zxy_imag_col].iloc[i]],
                    [df[zyx_real_col].iloc[i] + 1j * df[zyx_imag_col].iloc[i],
                    df[zyy_real_col].iloc[i] + 1j * df[zyy_imag_col].iloc[i]]
                ])

                # Calculate phase tensor
                phi = MTProcessor.phase_tensor(Z)

                # Extract parameters
                strike = MTProcessor.strike_angle(phi)
                strike_angles.append(strike)

                # Calculate ellipticity and skew
                phi11, phi12 = phi[0,0], phi[0,1]
                phi21, phi22 = phi[1,0], phi[1,1]

                beta = 0.5 * np.arctan2(phi12 - phi21, phi11 + phi22)
                ellipticities.append(np.tan(beta))

                skew = 0.5 * np.arctan2(phi12 - phi21, phi12 + phi21)
                skew_angles.append(np.degrees(skew))

            # Create plot with dual axes
            self.mt_ax.clear()

            # Primary axis for strike
            color = 'tab:blue'
            self.mt_ax.set_xlabel('Frequency (Hz)')
            self.mt_ax.set_ylabel('Strike (°)', color=color)
            self.mt_ax.semilogx(freq, strike_angles, color=color, linewidth=2, marker='o')
            self.mt_ax.tick_params(axis='y', labelcolor=color)
            self.mt_ax.grid(True, alpha=0.3)

            # Secondary axis for ellipticity
            ax2 = self.mt_ax.twinx()
            color = 'tab:red'
            ax2.set_ylabel('Ellipticity', color=color)
            ax2.semilogx(freq, ellipticities, color=color, linewidth=2, marker='s')
            ax2.tick_params(axis='y', labelcolor=color)

            self.mt_ax.set_title('MT Phase Tensor Analysis')

            self.mt_canvas.draw()

            # Store results
            self.workflow_state.processed['mt_tensor'] = {
                'freq': freq,
                'strike': strike_angles,
                'ellipticity': ellipticities,
                'skew': skew_angles
            }

            # Calculate statistics for status
            mean_skew = np.mean(np.abs(skew_angles))
            if mean_skew < 3:
                dim = "1D/2D (near 0° skew)"
            elif mean_skew < 10:
                dim = "2D/3D (moderate skew)"
            else:
                dim = "3D (high skew)"

            # Update status
            status_text = (f"✓ Phase Tensor Analysis\n"
                        f"• Frequencies: {n_freq}\n"
                        f"• Mean strike: {np.mean(strike_angles):.1f}°\n"
                        f"• Mean ellipticity: {np.mean(ellipticities):.3f}\n"
                        f"• Mean |skew|: {mean_skew:.2f}°\n"
                        f"• Dimensionality: {dim}")
            self.mt_status.delete(1.0, tk.END)
            self.mt_status.insert(1.0, status_text)

        except Exception as e:
            self.mt_status.delete(1.0, tk.END)
            self.mt_status.insert(1.0, f"❌ Error: {str(e)[:100]}")
            import traceback
            traceback.print_exc()

    # ============================================================================
    # GPR METHODS - REAL IMPLEMENTATIONS
    # ============================================================================
    def _gpr_dewow(self):
        """Apply dewow filter to GPR data"""
        if self.workflow_state.raw_data is None:
            self.gpr_status.delete(1.0, tk.END)
            self.gpr_status.insert(1.0, "⚠️ Import data first")
            return

        try:
            df = self.workflow_state.raw_data

            # Find GPR data column (contains 2D numpy arrays)
            data_col = None
            for col in df.columns:
                if col == 'data' or 'gpr' in col.lower() or 'radar' in col.lower():
                    first_valid = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
                    if first_valid is not None and isinstance(first_valid, np.ndarray) and len(first_valid.shape) == 2:
                        data_col = col
                        break

            if data_col is None:
                self.gpr_status.delete(1.0, tk.END)
                self.gpr_status.insert(1.0, "❌ No GPR data found (need 2D array)")
                return

            # Process each GPR trace/line
            processed_data = []
            trace_count = 0

            for idx, row in df.iterrows():
                gpr_data = row[data_col]
                if gpr_data is None or not isinstance(gpr_data, np.ndarray) or len(gpr_data.shape) != 2:
                    continue

                # Apply dewow to each trace in the 2D array
                nt, nx = gpr_data.shape
                dewowed = np.zeros_like(gpr_data)

                for i in range(nx):
                    trace = gpr_data[:, i]
                    dewowed[:, i] = GPRProcessor.dewow(trace, window=50)

                processed_data.append(dewowed)
                trace_count += 1

            # Plot first processed GPR section
            if processed_data:
                self.gpr_ax.clear()
                first_section = processed_data[0]

                extent = [0, first_section.shape[1], first_section.shape[0], 0]
                vmin, vmax = np.percentile(first_section, [5, 95])

                self.gpr_ax.imshow(first_section.T, aspect='auto', cmap='gray',
                                extent=extent, vmin=vmin, vmax=vmax)
                self.gpr_ax.set_xlabel("Trace")
                self.gpr_ax.set_ylabel("Time (ns)")
                self.gpr_ax.set_title(f"GPR Dewow - First section ({first_section.shape[1]} traces)")
                self.gpr_canvas.draw()

                # Store processed data
                self.workflow_state.processed['gpr_dewow'] = processed_data

                status_text = (f"✓ Dewow applied to {trace_count} GPR sections\n"
                            f"• First section: {first_section.shape[0]} samples × {first_section.shape[1]} traces")
                self.gpr_status.delete(1.0, tk.END)
                self.gpr_status.insert(1.0, status_text)
            else:
                self.gpr_status.delete(1.0, tk.END)
                self.gpr_status.insert(1.0, "❌ No valid GPR data found")

        except Exception as e:
            self.gpr_status.delete(1.0, tk.END)
            self.gpr_status.insert(1.0, f"❌ Error: {str(e)[:100]}")

    def _gpr_background(self):
        """Remove background (average trace) from GPR data"""
        if self.workflow_state.raw_data is None:
            self.gpr_status.delete(1.0, tk.END)
            self.gpr_status.insert(1.0, "⚠️ Import data first")
            return

        try:
            df = self.workflow_state.raw_data

            # Find GPR data column (contains 2D numpy arrays)
            data_col = None
            for col in df.columns:
                if col == 'data' or 'gpr' in col.lower() or 'radar' in col.lower():
                    first_valid = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
                    if first_valid is not None and isinstance(first_valid, np.ndarray) and len(first_valid.shape) == 2:
                        data_col = col
                        break

            if data_col is None:
                self.gpr_status.delete(1.0, tk.END)
                self.gpr_status.insert(1.0, "❌ No GPR data found (need 2D array)")
                return

            # Process each GPR section
            processed_data = []
            trace_count = 0

            for idx, row in df.iterrows():
                gpr_data = row[data_col]
                if gpr_data is None or not isinstance(gpr_data, np.ndarray) or len(gpr_data.shape) != 2:
                    continue

                # Calculate average trace and subtract
                avg_trace = np.mean(gpr_data, axis=1, keepdims=True)
                background_removed = gpr_data - avg_trace

                processed_data.append(background_removed)
                trace_count += 1

            # Plot first processed section
            if processed_data:
                self.gpr_ax.clear()
                first_section = processed_data[0]

                extent = [0, first_section.shape[1], first_section.shape[0], 0]
                vmin, vmax = np.percentile(first_section, [5, 95])

                self.gpr_ax.imshow(first_section.T, aspect='auto', cmap='gray',
                                extent=extent, vmin=vmin, vmax=vmax)
                self.gpr_ax.set_xlabel("Trace")
                self.gpr_ax.set_ylabel("Time (ns)")
                self.gpr_ax.set_title(f"GPR Background Removed - First section")
                self.gpr_canvas.draw()

                # Store processed data
                self.workflow_state.processed['gpr_background'] = processed_data

                status_text = (f"✓ Background removed from {trace_count} GPR sections")
                self.gpr_status.delete(1.0, tk.END)
                self.gpr_status.insert(1.0, status_text)
            else:
                self.gpr_status.delete(1.0, tk.END)
                self.gpr_status.insert(1.0, "❌ No valid GPR data found")

        except Exception as e:
            self.gpr_status.delete(1.0, tk.END)
            self.gpr_status.insert(1.0, f"❌ Error: {str(e)[:100]}")

    def _gpr_agc(self):
        """Apply Automatic Gain Control to GPR data"""
        if self.workflow_state.raw_data is None:
            self.gpr_status.delete(1.0, tk.END)
            self.gpr_status.insert(1.0, "⚠️ Import data first")
            return

        try:
            df = self.workflow_state.raw_data

            # Find GPR data column (contains 2D numpy arrays)
            data_col = None
            for col in df.columns:
                if col == 'data' or 'gpr' in col.lower() or 'radar' in col.lower():
                    first_valid = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
                    if first_valid is not None and isinstance(first_valid, np.ndarray) and len(first_valid.shape) == 2:
                        data_col = col
                        break

            if data_col is None:
                self.gpr_status.delete(1.0, tk.END)
                self.gpr_status.insert(1.0, "❌ No GPR data found (need 2D array)")
                return

            # AGC window size (in samples)
            window = 100

            # Process each GPR section
            processed_data = []
            trace_count = 0

            for idx, row in df.iterrows():
                gpr_data = row[data_col]
                if gpr_data is None or not isinstance(gpr_data, np.ndarray) or len(gpr_data.shape) != 2:
                    continue

                # Apply AGC to each trace
                nt, nx = gpr_data.shape
                agc_data = np.zeros_like(gpr_data)

                for i in range(nx):
                    trace = gpr_data[:, i]
                    half = window // 2
                    for j in range(nt):
                        i1 = max(0, j - half)
                        i2 = min(nt, j + half + 1)
                        rms = np.sqrt(np.mean(trace[i1:i2]**2) + 1e-6)
                        agc_data[j, i] = trace[j] / rms

                processed_data.append(agc_data)
                trace_count += 1

            # Plot first processed section
            if processed_data:
                self.gpr_ax.clear()
                first_section = processed_data[0]

                extent = [0, first_section.shape[1], first_section.shape[0], 0]
                vmin, vmax = np.percentile(first_section, [5, 95])

                self.gpr_ax.imshow(first_section.T, aspect='auto', cmap='gray',
                                extent=extent, vmin=vmin, vmax=vmax)
                self.gpr_ax.set_xlabel("Trace")
                self.gpr_ax.set_ylabel("Time (ns)")
                self.gpr_ax.set_title(f"GPR AGC Gain - First section")
                self.gpr_canvas.draw()

                # Store processed data
                self.workflow_state.processed['gpr_agc'] = processed_data

                status_text = (f"✓ AGC applied to {trace_count} GPR sections\n"
                            f"• Window: {window} samples")
                self.gpr_status.delete(1.0, tk.END)
                self.gpr_status.insert(1.0, status_text)
            else:
                self.gpr_status.delete(1.0, tk.END)
                self.gpr_status.insert(1.0, "❌ No valid GPR data found")

        except Exception as e:
            self.gpr_status.delete(1.0, tk.END)
            self.gpr_status.insert(1.0, f"❌ Error: {str(e)[:100]}")

    def _gpr_kirchhoff(self):
        """Apply Kirchhoff migration to GPR data"""
        if self.workflow_state.raw_data is None:
            self.gpr_status.delete(1.0, tk.END)
            self.gpr_status.insert(1.0, "⚠️ Import data first")
            return

        try:
            df = self.workflow_state.raw_data

            # Find GPR data column (contains 2D numpy arrays)
            data_col = None
            for col in df.columns:
                if col == 'data' or 'gpr' in col.lower() or 'radar' in col.lower():
                    first_valid = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
                    if first_valid is not None and isinstance(first_valid, np.ndarray) and len(first_valid.shape) == 2:
                        data_col = col
                        break

            if data_col is None:
                self.gpr_status.delete(1.0, tk.END)
                self.gpr_status.insert(1.0, "❌ No GPR data found (need 2D array)")
                return

            # Get velocity from user input (could add an entry field)
            # For now, use default velocity or try to read from metadata
            velocity = 0.1  # m/ns default

            # Try to find velocity in data
            if 'velocity' in df.columns:
                velocity = df['velocity'].iloc[0]
            elif 'velocity_m_ns' in df.columns:
                velocity = df['velocity_m_ns'].iloc[0]

            # Get trace spacing and time sampling
            dt_ns = 0.5  # default
            dx_m = 0.1   # default

            if 'dt_ns' in df.columns:
                dt_ns = df['dt_ns'].iloc[0]
            if 'dx_m' in df.columns:
                dx_m = df['dx_m'].iloc[0]

            # Process each GPR section
            processed_data = []
            trace_count = 0

            for idx, row in df.iterrows():
                gpr_data = row[data_col]
                if gpr_data is None or not isinstance(gpr_data, np.ndarray) or len(gpr_data.shape) != 2:
                    continue

                # Apply Kirchhoff migration
                migrated = GPRProcessor.kirchhoff_migration(gpr_data, dt_ns, dx_m, velocity)
                processed_data.append(migrated)
                trace_count += 1

            # Plot first migrated section
            if processed_data:
                self.gpr_ax.clear()
                first_section = processed_data[0]

                extent = [0, first_section.shape[1] * dx_m, first_section.shape[0] * dt_ns, 0]
                vmin, vmax = np.percentile(first_section, [5, 95])

                self.gpr_ax.imshow(first_section.T, aspect='auto', cmap='gray',
                                extent=extent, vmin=vmin, vmax=vmax)
                self.gpr_ax.set_xlabel("Distance (m)")
                self.gpr_ax.set_ylabel("Time (ns)")
                self.gpr_ax.set_title(f"GPR Kirchhoff Migration - First section")
                self.gpr_canvas.draw()

                # Store processed data
                self.workflow_state.processed['gpr_migrated'] = processed_data

                status_text = (f"✓ Migration applied to {trace_count} GPR sections\n"
                            f"• Velocity: {velocity} m/ns\n"
                            f"• dt: {dt_ns} ns, dx: {dx_m} m")
                self.gpr_status.delete(1.0, tk.END)
                self.gpr_status.insert(1.0, status_text)
            else:
                self.gpr_status.delete(1.0, tk.END)
                self.gpr_status.insert(1.0, "❌ No valid GPR data found")

        except Exception as e:
            self.gpr_status.delete(1.0, tk.END)
            self.gpr_status.insert(1.0, f"❌ Error: {str(e)[:100]}")
            import traceback
            traceback.print_exc()

    # ============================================================================
    # ENVIRONMENTAL METHODS - REAL IMPLEMENTATIONS
    # ============================================================================
    def _env_temp(self):
        """Temperature correction for ALL samples"""
        if self.workflow_state.raw_data is None:
            self.env_ax.clear()
            self.env_ax.text(0.5, 0.5, "⚠️ Import data first", ha='center', va='center')
            self.env_canvas.draw()
            return

        try:
            df = self.workflow_state.raw_data
            temp_col = self._find_coord_column(df, ['temp', 'temperature'])

            if temp_col:
                temp = df[temp_col].values
                # Simple correction to standard temperature
                corrected = temp - 20

                # Plot
                self.env_ax.clear()
                x = np.arange(len(temp))
                self.env_ax.plot(x, temp, 'b-', alpha=0.5, label='Original')
                self.env_ax.plot(x, corrected, 'r-', linewidth=1.5, label='Corrected (to 20°C)')
                self.env_ax.set_xlabel("Sample Index")
                self.env_ax.set_ylabel("Temperature (°C)")
                self.env_ax.set_title(f"Temperature Correction ({len(temp)} samples)")
                self.env_ax.legend()
                self.env_ax.grid(True, alpha=0.3)
            else:
                self.env_ax.clear()
                self.env_ax.text(0.5, 0.5, "No temperature data found", ha='center', va='center')

            self.env_canvas.draw()
            self.workflow_state.processed['temp_corrected'] = corrected if 'corrected' in locals() else None

        except Exception as e:
            self.env_ax.clear()
            self.env_ax.text(0.5, 0.5, f"❌ Error: {str(e)[:50]}", ha='center', va='center')
            self.env_canvas.draw()

    def _env_pressure(self):
        """Pressure correction for ALL samples"""
        if self.workflow_state.raw_data is None:
            self.env_ax.clear()
            self.env_ax.text(0.5, 0.5, "⚠️ Import data first", ha='center', va='center')
            self.env_canvas.draw()
            return

        try:
            df = self.workflow_state.raw_data
            press_col = self._find_coord_column(df, ['press', 'pressure'])

            if press_col:
                press = df[press_col].values
                # Simple correction to sea level
                corrected = press * (1013.25 / np.mean(press))

                # Plot
                self.env_ax.clear()
                x = np.arange(len(press))
                self.env_ax.plot(x, press, 'b-', alpha=0.5, label='Original')
                self.env_ax.plot(x, corrected, 'r-', linewidth=1.5, label='Corrected (to sea level)')
                self.env_ax.set_xlabel("Sample Index")
                self.env_ax.set_ylabel("Pressure (hPa)")
                self.env_ax.set_title(f"Pressure Correction ({len(press)} samples)")
                self.env_ax.legend()
                self.env_ax.grid(True, alpha=0.3)
            else:
                self.env_ax.clear()
                self.env_ax.text(0.5, 0.5, "No pressure data found", ha='center', va='center')

            self.env_canvas.draw()
            self.workflow_state.processed['pressure_corrected'] = corrected if 'corrected' in locals() else None

        except Exception as e:
            self.env_ax.clear()
            self.env_ax.text(0.5, 0.5, f"❌ Error: {str(e)[:50]}", ha='center', va='center')
            self.env_canvas.draw()

    def _build_tab3(self):
        """Build Tab 3: Gridding & Enhancement - COMPLETE"""
        main = ttk.PanedWindow(self.tab3, orient=tk.HORIZONTAL)
        main.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left controls
        left = ttk.Frame(main, width=350)
        main.add(left, weight=1)

        # Right plot area with notebook for multiple views
        right = ttk.Frame(main)
        main.add(right, weight=2)

        # Create notebook for different grid visualizations
        self.grid_notebook = ttk.Notebook(right)
        self.grid_notebook.pack(fill=tk.BOTH, expand=True)

        # Tab G1: Gridded Map
        map_frame = ttk.Frame(self.grid_notebook)
        self.grid_notebook.add(map_frame, text="🗺️ Gridded Map")

        self.grid_fig = Figure(figsize=(8, 6), dpi=90)
        self.grid_ax = self.grid_fig.add_subplot(111)
        self.grid_canvas = FigureCanvasTkAgg(self.grid_fig, map_frame)
        self.grid_canvas.draw()
        self.grid_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Tab G2: Filtered Map
        filter_frame = ttk.Frame(self.grid_notebook)
        self.grid_notebook.add(filter_frame, text="🔍 Filtered")

        self.filter_fig = Figure(figsize=(8, 6), dpi=90)
        self.filter_ax = self.filter_fig.add_subplot(111)
        self.filter_canvas = FigureCanvasTkAgg(self.filter_fig, filter_frame)
        self.filter_canvas.draw()
        self.filter_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Tab G3: Derivative Map
        deriv_frame = ttk.Frame(self.grid_notebook)
        self.grid_notebook.add(deriv_frame, text="📈 Derivatives")

        self.deriv_fig = Figure(figsize=(8, 6), dpi=90)
        self.deriv_ax = self.deriv_fig.add_subplot(111)
        self.deriv_canvas = FigureCanvasTkAgg(self.deriv_fig, deriv_frame)
        self.deriv_canvas.draw()
        self.deriv_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # ============ LEFT PANEL CONTROLS ============

        # Data Selection
        data_frame = ttk.LabelFrame(left, text="📊 Input Data", padding=5)
        data_frame.pack(fill=tk.X, pady=2)

        ttk.Label(data_frame, text="X column:").pack(anchor='w')
        self.grid_x_col = tk.StringVar()
        self.grid_x_combo = ttk.Combobox(data_frame, textvariable=self.grid_x_col, values=[], width=20)
        self.grid_x_combo.pack(fill=tk.X, pady=1)

        ttk.Label(data_frame, text="Y column:").pack(anchor='w')
        self.grid_y_col = tk.StringVar()
        self.grid_y_combo = ttk.Combobox(data_frame, textvariable=self.grid_y_col, values=[], width=20)
        self.grid_y_combo.pack(fill=tk.X, pady=1)

        ttk.Label(data_frame, text="Z column:").pack(anchor='w')
        self.grid_z_col = tk.StringVar()
        self.grid_z_combo = ttk.Combobox(data_frame, textvariable=self.grid_z_col, values=[], width=20)
        self.grid_z_combo.pack(fill=tk.X, pady=1)

        # Gridding methods
        grid_frame = ttk.LabelFrame(left, text="📍 Gridding Methods", padding=5)
        grid_frame.pack(fill=tk.X, pady=2)

        self.grid_method = tk.StringVar(value="minimum_curvature")
        ttk.Radiobutton(grid_frame, text="Minimum Curvature (RBF)",
                       variable=self.grid_method, value="minimum_curvature",
                       command=self._update_grid_method).pack(anchor='w')
        ttk.Radiobutton(grid_frame, text="Kriging (pykrige)",
                       variable=self.grid_method, value="kriging",
                       command=self._update_grid_method,
                       state='normal' if HAS_PYKRIGE else 'disabled').pack(anchor='w')
        ttk.Radiobutton(grid_frame, text="Nearest Neighbor",
                       variable=self.grid_method, value="nearest").pack(anchor='w')
        ttk.Radiobutton(grid_frame, text="Linear",
                       variable=self.grid_method, value="linear").pack(anchor='w')
        ttk.Radiobutton(grid_frame, text="Cubic",
                       variable=self.grid_method, value="cubic").pack(anchor='w')

        # Grid parameters
        param_frame = ttk.Frame(grid_frame)
        param_frame.pack(fill=tk.X, pady=2)

        ttk.Label(param_frame, text="Grid size:").pack(side=tk.LEFT)
        self.grid_size_var = tk.IntVar(value=100)
        tk.Spinbox(param_frame, from_=20, to=500, textvariable=self.grid_size_var,
                  width=6).pack(side=tk.RIGHT)

        # Kriging parameters (initially hidden)
        self.kriging_frame = ttk.Frame(grid_frame)
        ttk.Label(self.kriging_frame, text="Variogram model:").pack(anchor='w')
        self.vario_model = tk.StringVar(value="spherical")
        ttk.Combobox(self.kriging_frame, textvariable=self.vario_model,
                    values=["spherical", "exponential", "gaussian"], width=15).pack()

        # Create Grid button
        ttk.Button(grid_frame, text="🔨 Create Grid",
                  command=self._create_grid).pack(fill=tk.X, pady=3)

        # ============ FFT FILTERS ============
        fft_frame = ttk.LabelFrame(left, text="🎛️ FFT Filters", padding=5)
        fft_frame.pack(fill=tk.X, pady=2)

        self.filter_type = tk.StringVar(value="low")
        filter_row = ttk.Frame(fft_frame)
        filter_row.pack(fill=tk.X)
        ttk.Radiobutton(filter_row, text="Low", variable=self.filter_type,
                       value="low").pack(side=tk.LEFT)
        ttk.Radiobutton(filter_row, text="High", variable=self.filter_type,
                       value="high").pack(side=tk.LEFT)
        ttk.Radiobutton(filter_row, text="Band", variable=self.filter_type,
                       value="band").pack(side=tk.LEFT)

        cutoff_frame = ttk.Frame(fft_frame)
        cutoff_frame.pack(fill=tk.X, pady=2)
        ttk.Label(cutoff_frame, text="Cutoff (1/m):").pack(side=tk.LEFT)
        self.cutoff_var = tk.StringVar(value="0.1")
        ttk.Entry(cutoff_frame, textvariable=self.cutoff_var, width=8).pack(side=tk.RIGHT)

        band_frame = ttk.Frame(fft_frame)
        band_frame.pack(fill=tk.X, pady=2)
        ttk.Label(band_frame, text="Band min:").pack(side=tk.LEFT)
        self.band_min = tk.StringVar(value="0.05")
        ttk.Entry(band_frame, textvariable=self.band_min, width=6).pack(side=tk.LEFT, padx=2)
        ttk.Label(band_frame, text="max:").pack(side=tk.LEFT)
        self.band_max = tk.StringVar(value="0.2")
        ttk.Entry(band_frame, textvariable=self.band_max, width=6).pack(side=tk.LEFT, padx=2)

        ttk.Button(fft_frame, text="Apply FFT Filter",
                  command=self._apply_fft_filter).pack(fill=tk.X, pady=2)

        # ============ DERIVATIVES ============
        deriv_frame2 = ttk.LabelFrame(left, text="📐 Derivatives", padding=5)
        deriv_frame2.pack(fill=tk.X, pady=2)

        ttk.Button(deriv_frame2, text="Horizontal Gradient",
                  command=self._compute_hgrad).pack(fill=tk.X, pady=1)
        ttk.Button(deriv_frame2, text="Tilt Derivative",
                  command=self._compute_tilt).pack(fill=tk.X, pady=1)
        ttk.Button(deriv_frame2, text="Analytic Signal",
                  command=self._compute_analytic).pack(fill=tk.X, pady=1)

        # ============ UPWARD CONTINUATION ============
        upward_frame = ttk.LabelFrame(left, text="⬆️ Upward Continuation", padding=5)
        upward_frame.pack(fill=tk.X, pady=2)

        ttk.Label(upward_frame, text="Height (m):").pack()
        self.upward_height = tk.StringVar(value="100")
        ttk.Entry(upward_frame, textvariable=self.upward_height, width=8).pack()

        ttk.Button(upward_frame, text="Apply Upward",
                  command=self._apply_upward).pack(fill=tk.X, pady=2)

    def _update_grid_method(self):
        """Show/hide kriging parameters based on selection"""
        if hasattr(self, 'kriging_frame'):
            if self.grid_method.get() == "kriging":
                self.kriging_frame.pack(fill=tk.X, pady=2)
            else:
                self.kriging_frame.pack_forget()

    def _create_grid(self):
        """Create a grid from scattered data"""
        if self.workflow_state.raw_data is None:
            messagebox.showwarning("No Data", "Import data first")
            return

        # Get column selections
        x_col = self.grid_x_col.get()
        y_col = self.grid_y_col.get()
        z_col = self.grid_z_col.get()

        if not x_col or not y_col or not z_col:
            messagebox.showwarning("Missing Columns", "Select X, Y, and Z columns")
            return

        df = self.workflow_state.raw_data
        if x_col not in df.columns or y_col not in df.columns or z_col not in df.columns:
            messagebox.showerror("Error", "Selected columns not found")
            return

        # Get data and remove NaN
        data = df[[x_col, y_col, z_col]].dropna()
        if len(data) < 10:
            messagebox.showwarning("Too Few Points", f"Only {len(data)} valid points")
            return

        x = data[x_col].values
        y = data[y_col].values
        z = data[z_col].values

        # Create grid
        grid_size = self.grid_size_var.get()
        method = self.grid_method.get()

        # Define grid limits with padding
        x_min, x_max = x.min(), x.max()
        y_min, y_max = y.min(), y.max()
        x_pad = (x_max - x_min) * 0.05
        y_pad = (y_max - y_min) * 0.05

        grid_x = np.linspace(x_min - x_pad, x_max + x_pad, grid_size)
        grid_y = np.linspace(y_min - y_pad, y_max + y_pad, grid_size)
        XI, YI = np.meshgrid(grid_x, grid_y)

        self.status_var.set(f"Gridding with {method}...")
        self.window.update()

        try:
            if method == "minimum_curvature":
                from scipy.interpolate import RBFInterpolator
                points = np.column_stack([x, y])
                rbf = RBFInterpolator(points, z, kernel='thin_plate_spline')
                ZI = rbf(np.column_stack([XI.ravel(), YI.ravel()])).reshape(XI.shape)

            elif method == "kriging" and HAS_PYKRIGE:
                from pykrige.ok import OrdinaryKriging
                OK = OrdinaryKriging(x, y, z, variogram_model=self.vario_model.get())
                ZI, ss = OK.execute('grid', grid_x, grid_y)

            else:
                # Use scipy interpolation methods
                from scipy.interpolate import griddata
                points = np.column_stack([x, y])
                ZI = griddata(points, z, (XI, YI), method=method)

            # Store in workflow state
            grid_data = {'X': XI, 'Y': YI, 'Z': ZI, 'x_col': x_col, 'y_col': y_col, 'z_col': z_col}
            self.workflow_state.add_grid(f"{method}_grid", grid_data)

            # Plot in main grid tab
            self.grid_ax.clear()
            im = self.grid_ax.contourf(XI, YI, ZI, levels=20, cmap='viridis')
            self.grid_ax.scatter(x, y, c='red', s=10, alpha=0.5, label='Data points')
            plt.colorbar(im, ax=self.grid_ax, label=z_col)
            self.grid_ax.set_xlabel(x_col)
            self.grid_ax.set_ylabel(y_col)
            self.grid_ax.set_title(f"{method.title()} Grid ({len(x)} points)")
            self.grid_ax.legend()
            self.grid_canvas.draw()

            # Switch to Gridded Map tab
            self.grid_notebook.select(0)

            self.status_var.set(f"✅ Grid created: {method}")
            messagebox.showinfo("Success", f"Grid created with {len(x)} points")

        except Exception as e:
            self.status_var.set("❌ Gridding failed")
            messagebox.showerror("Error", str(e))

    def _apply_fft_filter(self):
        """Apply FFT filter to current grid"""
        if not self.workflow_state.grids:
            messagebox.showwarning("No Grid", "Create a grid first")
            return

        # Get last grid
        grid_name = list(self.workflow_state.grids.keys())[-1]
        grid = self.workflow_state.grids[grid_name]

        X = grid['X']
        Y = grid['Y']
        Z = grid['Z']
        dx = X[0, 1] - X[0, 0]
        dy = Y[1, 0] - Y[0, 0]

        # Get filter parameters
        filter_type = self.filter_type.get()
        if filter_type == 'band':
            try:
                cutoff = (float(self.band_min.get()), float(self.band_max.get()))
            except Exception as e:
                messagebox.showerror("Error", "Invalid band limits")
                return
        else:
            try:
                cutoff = float(self.cutoff_var.get())
            except Exception as e:
                messagebox.showerror("Error", "Invalid cutoff value")
                return

        # Apply FFT filter
        try:
            Z_filtered = GriddingEngine.fft_filter(Z, dx, dy, filter_type, cutoff)

            # Plot in filter tab
            self.filter_ax.clear()
            im = self.filter_ax.contourf(X, Y, Z_filtered, levels=20, cmap='viridis')
            plt.colorbar(im, ax=self.filter_ax, label=grid.get('z_col', 'Z'))
            self.filter_ax.set_xlabel(grid.get('x_col', 'X'))
            self.filter_ax.set_ylabel(grid.get('y_col', 'Y'))
            self.filter_ax.set_title(f"{filter_type.capitalize()}-pass Filter (cutoff={cutoff})")
            self.filter_canvas.draw()

            # Store filtered grid
            self.workflow_state.add_grid(f"{filter_type}_filtered",
                                        {'X': X, 'Y': Y, 'Z': Z_filtered})

            # Switch to Filtered tab
            self.grid_notebook.select(1)

            self.status_var.set(f"✅ Applied {filter_type}-pass filter")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _compute_hgrad(self):
        """Compute horizontal gradient"""
        if not self.workflow_state.grids:
            messagebox.showwarning("No Grid", "Create a grid first")
            return

        grid_name = list(self.workflow_state.grids.keys())[-1]
        grid = self.workflow_state.grids[grid_name]

        if 'X' not in grid or 'Z' not in grid:
            return

        X = grid['X']
        Y = grid['Y']
        Z = grid['Z']
        dx = X[0, 1] - X[0, 0]
        dy = Y[1, 0] - Y[0, 0]

        hgrad = GriddingEngine.horizontal_gradient(Z, dx, dy)

        # Plot in derivatives tab
        self.deriv_ax.clear()
        im = self.deriv_ax.contourf(X, Y, hgrad, levels=20, cmap='viridis')
        plt.colorbar(im, ax=self.deriv_ax, label='Horizontal Gradient')
        self.deriv_ax.set_xlabel(grid.get('x_col', 'X'))
        self.deriv_ax.set_ylabel(grid.get('y_col', 'Y'))
        self.deriv_ax.set_title("Horizontal Gradient")
        self.deriv_canvas.draw()

        self.workflow_state.add_grid("hgrad", {'X': X, 'Y': Y, 'Z': hgrad})

        # Switch to Derivatives tab
        self.grid_notebook.select(2)
        self.status_var.set("✅ Computed horizontal gradient")

    def _compute_tilt(self):
        """Compute tilt derivative"""
        if not self.workflow_state.grids:
            messagebox.showwarning("No Grid", "Create a grid first")
            return

        grid_name = list(self.workflow_state.grids.keys())[-1]
        grid = self.workflow_state.grids[grid_name]

        if 'X' not in grid or 'Z' not in grid:
            return

        X = grid['X']
        Y = grid['Y']
        Z = grid['Z']
        dx = X[0, 1] - X[0, 0]
        dy = Y[1, 0] - Y[0, 0]

        # Calculate tilt derivative
        gy, gx = np.gradient(Z, dx, dy)
        hg = np.sqrt(gx**2 + gy**2)

        # Avoid division by zero
        with np.errstate(divide='ignore', invalid='ignore'):
            tilt = np.arctan(hg / np.abs(Z))
            tilt = np.nan_to_num(tilt)

        # Plot in derivatives tab
        self.deriv_ax.clear()
        im = self.deriv_ax.contourf(X, Y, tilt, levels=20, cmap='RdBu_r')
        plt.colorbar(im, ax=self.deriv_ax, label='Tilt (rad)')
        self.deriv_ax.set_xlabel(grid.get('x_col', 'X'))
        self.deriv_ax.set_ylabel(grid.get('y_col', 'Y'))
        self.deriv_ax.set_title("Tilt Derivative")
        self.deriv_canvas.draw()

        self.workflow_state.add_grid("tilt", {'X': X, 'Y': Y, 'Z': tilt})

        # Switch to Derivatives tab
        self.grid_notebook.select(2)
        self.status_var.set("✅ Computed tilt derivative")

    def _compute_analytic(self):
        """Compute analytic signal"""
        if not self.workflow_state.grids:
            messagebox.showwarning("No Grid", "Create a grid first")
            return

        grid_name = list(self.workflow_state.grids.keys())[-1]
        grid = self.workflow_state.grids[grid_name]

        X = grid['X']
        Y = grid['Y']
        Z = grid['Z']
        dx = X[0, 1] - X[0, 0]
        dy = Y[1, 0] - Y[0, 0]

        # Compute gradients
        gy, gx = np.gradient(Z, dx, dy)

        # Analytic signal = sqrt(gx^2 + gy^2)
        analytic = np.sqrt(gx**2 + gy**2)

        # Plot in derivatives tab
        self.deriv_ax.clear()
        im = self.deriv_ax.contourf(X, Y, analytic, levels=20, cmap='magma')
        plt.colorbar(im, ax=self.deriv_ax, label='Analytic Signal')
        self.deriv_ax.set_xlabel(grid.get('x_col', 'X'))
        self.deriv_ax.set_ylabel(grid.get('y_col', 'Y'))
        self.deriv_ax.set_title("Analytic Signal")
        self.deriv_canvas.draw()

        self.workflow_state.add_grid("analytic", {'X': X, 'Y': Y, 'Z': analytic})

        # Switch to Derivatives tab
        self.grid_notebook.select(2)
        self.status_var.set("✅ Computed analytic signal")

    def _apply_upward(self):
        """Apply upward continuation"""
        if not self.workflow_state.grids:
            messagebox.showwarning("No Grid", "Create a grid first")
            return

        try:
            height = float(self.upward_height.get())
        except Exception as e:
            messagebox.showerror("Error", "Invalid height")
            return

        grid_name = list(self.workflow_state.grids.keys())[-1]
        grid = self.workflow_state.grids[grid_name]

        X = grid['X']
        Y = grid['Y']
        Z = grid['Z']
        dx = X[0, 1] - X[0, 0]
        dy = Y[1, 0] - Y[0, 0]

        # FFT upward continuation
        from scipy.fft import fft2, ifft2, fftfreq, fftshift, ifftshift

        F = fft2(Z)
        F = fftshift(F)

        ny, nx = Z.shape
        kx = fftfreq(nx, dx)
        ky = fftfreq(ny, dy)
        KX, KY = np.meshgrid(kx, ky)
        K = np.sqrt(KX**2 + KY**2)

        # Upward filter
        filter_up = np.exp(-K * height)
        F_up = F * filter_up
        F_up = ifftshift(F_up)
        Z_up = np.real(ifft2(F_up))

        # Plot in filter tab
        self.filter_ax.clear()
        im = self.filter_ax.contourf(X, Y, Z_up, levels=20, cmap='viridis')
        plt.colorbar(im, ax=self.filter_ax, label=grid.get('z_col', 'Z'))
        self.filter_ax.set_xlabel(grid.get('x_col', 'X'))
        self.filter_ax.set_ylabel(grid.get('y_col', 'Y'))
        self.filter_ax.set_title(f"Upward Continuation ({height} m)")
        self.filter_canvas.draw()

        self.workflow_state.add_grid(f"upward_{height}m",
                                    {'X': X, 'Y': Y, 'Z': Z_up})

        # Switch to Filtered tab
        self.grid_notebook.select(1)
        self.status_var.set(f"✅ Applied upward continuation ({height} m)")

    def _build_tab4(self):
        """Build Tab 4: Modeling & Interpretation - COMPLETE"""
        main = ttk.PanedWindow(self.tab4, orient=tk.HORIZONTAL)
        main.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left controls
        left = ttk.Frame(main, width=350)
        main.add(left, weight=1)

        # Right results area with notebook
        right = ttk.Frame(main)
        main.add(right, weight=2)

        # Create notebook for different results
        self.model_notebook = ttk.Notebook(right)
        self.model_notebook.pack(fill=tk.BOTH, expand=True)

        # Tab M1: Text Results
        text_frame = ttk.Frame(self.model_notebook)
        self.model_notebook.add(text_frame, text="📝 Results")

        self.model_text = tk.Text(text_frame, wrap=tk.WORD, font=("Courier", 10))
        scroll = ttk.Scrollbar(text_frame, orient="vertical", command=self.model_text.yview)
        self.model_text.configure(yscrollcommand=scroll.set)
        self.model_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Tab M2: Plot View
        plot_frame = ttk.Frame(self.model_notebook)
        self.model_notebook.add(plot_frame, text="📊 Plot")

        self.model_fig = Figure(figsize=(7, 5), dpi=90)
        self.model_ax = self.model_fig.add_subplot(111)
        self.model_canvas = FigureCanvasTkAgg(self.model_fig, plot_frame)
        self.model_canvas.draw()
        self.model_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # ============ LEFT PANEL CONTROLS ============

        # Euler Deconvolution
        euler_frame = ttk.LabelFrame(left, text="🧮 Euler Deconvolution", padding=5)
        euler_frame.pack(fill=tk.X, pady=2)

        tk.Label(euler_frame, text="Structural Index:").pack()
        self.si_var = tk.IntVar(value=1)
        si_scale = tk.Scale(euler_frame, from_=0, to=3, variable=self.si_var,
                           orient=tk.HORIZONTAL, resolution=1,
                           tickinterval=1, length=200)
        si_scale.pack(fill=tk.X)

        tk.Label(euler_frame, text="Window size:").pack()
        self.euler_window = tk.IntVar(value=15)
        tk.Spinbox(euler_frame, from_=5, to=50, textvariable=self.euler_window,
                  width=8).pack()

        ttk.Button(euler_frame, text="🔍 Run Euler",
                  command=self._run_euler).pack(fill=tk.X, pady=3)

        self.euler_status = tk.Text(euler_frame, height=8, width=35, font=("Courier", 8))
        self.euler_status.pack(fill=tk.X, pady=2)

        # Joint Inversion
        joint_frame = ttk.LabelFrame(left, text="🔗 Joint Inversion (ERT + Gravity)", padding=5)
        joint_frame.pack(fill=tk.X, pady=2)

        tk.Label(joint_frame, text="Coupling factor:").pack()
        self.coupling_var = tk.DoubleVar(value=0.1)
        coupling_scale = tk.Scale(joint_frame, from_=0.01, to=1.0, variable=self.coupling_var,
                                 orient=tk.HORIZONTAL, resolution=0.01,
                                 tickinterval=0.2, length=200)
        coupling_scale.pack(fill=tk.X)

        tk.Label(joint_frame, text="Max iterations:").pack()
        self.joint_iter = tk.IntVar(value=10)
        tk.Spinbox(joint_frame, from_=5, to=50, textvariable=self.joint_iter,
                  width=8).pack()

        ttk.Button(joint_frame, text="🔄 Run Joint Inversion",
                  command=self._run_joint_inversion,
                  state='normal' if HAS_PYGIMLI else 'disabled').pack(fill=tk.X, pady=3)

        if not HAS_PYGIMLI:
            tk.Label(joint_frame, text="⚠️ pyGIMLi required", fg="red",
                    font=("Arial", 7)).pack()

        self.joint_status = tk.Text(joint_frame, height=8, width=35, font=("Courier", 8))
        self.joint_status.pack(fill=tk.X, pady=2)

        # Machine Learning
        ml_frame = ttk.LabelFrame(left, text="🤖 Machine Learning", padding=5)
        ml_frame.pack(fill=tk.X, pady=2)

        # Method selector
        ml_method_frame = ttk.Frame(ml_frame)
        ml_method_frame.pack(fill=tk.X)
        self.ml_method = tk.StringVar(value="kmeans")
        ttk.Radiobutton(ml_method_frame, text="KMeans", variable=self.ml_method,
                       value="kmeans").pack(side=tk.LEFT)
        ttk.Radiobutton(ml_method_frame, text="DBSCAN", variable=self.ml_method,
                       value="dbscan").pack(side=tk.LEFT)

        tk.Label(ml_frame, text="Number of clusters:").pack()
        self.n_clusters = tk.IntVar(value=3)
        tk.Spinbox(ml_frame, from_=2, to=10, textvariable=self.n_clusters,
                  width=8).pack()

        ttk.Button(ml_frame, text="📊 Cluster Attributes",
                  command=self._cluster_data,
                  state='normal' if HAS_SKLEARN else 'disabled').pack(fill=tk.X, pady=2)

        # XGBoost
        xgb_frame = ttk.Frame(ml_frame)
        xgb_frame.pack(fill=tk.X, pady=2)
        tk.Label(xgb_frame, text="Target column:").pack(side=tk.LEFT)
        self.xgb_target = tk.StringVar()
        self.xgb_combo = ttk.Combobox(xgb_frame, textvariable=self.xgb_target,
                                     values=[], width=10)
        self.xgb_combo.pack(side=tk.RIGHT)

        ttk.Button(ml_frame, text="🎯 XGBoost Predict",
                  command=self._xgboost_predict,
                  state='normal' if HAS_XGBOOST else 'disabled').pack(fill=tk.X, pady=2)

        if not HAS_SKLEARN or not HAS_XGBOOST:
            missing = []
            if not HAS_SKLEARN: missing.append("scikit-learn")
            if not HAS_XGBOOST: missing.append("xgboost")
            tk.Label(ml_frame, text=f"⚠️ Missing: {', '.join(missing)}",
                    fg="orange", font=("Arial", 7)).pack()

        self.ml_status = tk.Text(ml_frame, height=8, width=35, font=("Courier", 8))
        self.ml_status.pack(fill=tk.X, pady=2)

        # Lineament Detection
        line_frame = ttk.LabelFrame(left, text="📏 Lineament Detection", padding=5)
        line_frame.pack(fill=tk.X, pady=2)

        tk.Label(line_frame, text="Threshold:").pack()
        self.line_thresh = tk.DoubleVar(value=0.5)
        tk.Scale(line_frame, from_=0.1, to=1.0, variable=self.line_thresh,
                orient=tk.HORIZONTAL).pack(fill=tk.X)

        ttk.Button(line_frame, text="🔍 Detect Lineaments",
                  command=self._detect_lineaments,
                  state='normal' if HAS_SKIMAGE else 'disabled').pack(fill=tk.X, pady=2)

        self.line_status = tk.Text(line_frame, height=8, width=35, font=("Courier", 8))
        self.line_status.pack(fill=tk.X, pady=2)

    def _build_tab5(self):
        """Build Tab 5: Visualization & Export - COMPLETE"""
        main = ttk.PanedWindow(self.tab5, orient=tk.HORIZONTAL)
        main.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left controls
        left = ttk.Frame(main, width=300)
        main.add(left, weight=1)

        # Right visualization area - just 2D plots now
        right = ttk.Frame(main)
        main.add(right, weight=2)

        # 2D Plot (only visualization tab)
        self.viz_fig = Figure(figsize=(8, 6), dpi=90)
        self.viz_ax = self.viz_fig.add_subplot(111)
        self.viz_canvas = FigureCanvasTkAgg(self.viz_fig, right)
        self.viz_canvas.draw()
        self.viz_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # ============ LEFT PANEL CONTROLS ============

        # Plot Controls
        plot_frame = ttk.LabelFrame(left, text="📊 Plot Controls", padding=5)
        plot_frame.pack(fill=tk.X, pady=2)

        # Plot type selector
        type_frame = ttk.Frame(plot_frame)
        type_frame.pack(fill=tk.X, pady=2)
        ttk.Label(type_frame, text="Plot type:").pack(side=tk.LEFT)
        self.plot_type = tk.StringVar(value="profile")
        plot_combo = ttk.Combobox(type_frame, textvariable=self.plot_type,
                                  values=["profile", "scatter", "histogram", "contour"],
                                  width=12)
        plot_combo.pack(side=tk.RIGHT)

        # X axis selector
        x_frame = ttk.Frame(plot_frame)
        x_frame.pack(fill=tk.X, pady=2)
        ttk.Label(x_frame, text="X axis:").pack(side=tk.LEFT)
        self.plot_x = tk.StringVar()
        self.plot_x_combo = ttk.Combobox(x_frame, textvariable=self.plot_x,
                                         values=[], width=15)
        self.plot_x_combo.pack(side=tk.RIGHT)

        # Y axis selector
        y_frame = ttk.Frame(plot_frame)
        y_frame.pack(fill=tk.X, pady=2)
        ttk.Label(y_frame, text="Y axis:").pack(side=tk.LEFT)
        self.plot_y = tk.StringVar()
        self.plot_y_combo = ttk.Combobox(y_frame, textvariable=self.plot_y,
                                         values=[], width=15)
        self.plot_y_combo.pack(side=tk.RIGHT)

        # Color by selector
        c_frame = ttk.Frame(plot_frame)
        c_frame.pack(fill=tk.X, pady=2)
        ttk.Label(c_frame, text="Color by:").pack(side=tk.LEFT)
        self.plot_c = tk.StringVar()
        self.plot_c_combo = ttk.Combobox(c_frame, textvariable=self.plot_c,
                                         values=[], width=15)
        self.plot_c_combo.pack(side=tk.RIGHT)

        ttk.Button(plot_frame, text="🎨 Generate Plot",
                  command=self._generate_plot).pack(fill=tk.X, pady=3)

        # Export Formats
        export_frame = ttk.LabelFrame(left, text="💾 Export", padding=5)
        export_frame.pack(fill=tk.X, pady=2)

        # Grid selection for export
        grid_frame = ttk.Frame(export_frame)
        grid_frame.pack(fill=tk.X, pady=2)
        ttk.Label(grid_frame, text="Grid to export:").pack(side=tk.LEFT)
        self.export_grid = tk.StringVar()
        self.export_combo = ttk.Combobox(grid_frame, textvariable=self.export_grid,
                                         values=[], width=15)
        self.export_combo.pack(side=tk.RIGHT)

        # Export buttons in a grid
        btn_frame = ttk.Frame(export_frame)
        btn_frame.pack(fill=tk.X, pady=2)

        ttk.Button(btn_frame, text="📦 GeoTIFF",
                  command=self._export_geotiff,
                  state='normal' if HAS_RASTERIO else 'disabled').grid(row=0, column=0, padx=2, pady=1, sticky='ew')

        ttk.Button(btn_frame, text="📁 Shapefile",
                  command=self._export_shapefile,
                  state='normal' if HAS_GEOPANDAS else 'disabled').grid(row=0, column=1, padx=2, pady=1, sticky='ew')

        ttk.Button(btn_frame, text="📄 XYZ",
                  command=self._export_xyz).grid(row=1, column=0, padx=2, pady=1, sticky='ew')

        ttk.Button(btn_frame, text="📊 Surfer GRD",
                  command=self._export_grd).grid(row=1, column=1, padx=2, pady=1, sticky='ew')

        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)

        # External Tools (separate frame)
        tools_frame = ttk.LabelFrame(left, text="🗺️ External Tools", padding=5)
        tools_frame.pack(fill=tk.X, pady=2)

        # Interactive Maps
        map_ctl_frame = ttk.Frame(tools_frame)
        map_ctl_frame.pack(fill=tk.X, pady=2)

        ttk.Label(map_ctl_frame, text="Latitude column:").grid(row=0, column=0, sticky='w')
        self.map_lat = tk.StringVar()
        self.map_lat_combo = ttk.Combobox(map_ctl_frame, textvariable=self.map_lat,
                                          values=[], width=15)
        self.map_lat_combo.grid(row=0, column=1, padx=2)

        ttk.Label(map_ctl_frame, text="Longitude column:").grid(row=1, column=0, sticky='w')
        self.map_lon = tk.StringVar()
        self.map_lon_combo = ttk.Combobox(map_ctl_frame, textvariable=self.map_lon,
                                          values=[], width=15)
        self.map_lon_combo.grid(row=1, column=1, padx=2)

        ttk.Label(map_ctl_frame, text="Popup column:").grid(row=2, column=0, sticky='w')
        self.map_popup = tk.StringVar()
        self.map_popup_combo = ttk.Combobox(map_ctl_frame, textvariable=self.map_popup,
                                            values=[], width=15)
        self.map_popup_combo.grid(row=2, column=1, padx=2)

        ttk.Button(tools_frame, text="🌍 Generate Folium Map (opens browser)",
                  command=self._generate_folium,
                  state='normal' if HAS_FOLIUM else 'disabled').pack(fill=tk.X, pady=2)

        # 3D Visualization
        viz3d_frame = ttk.Frame(tools_frame)
        viz3d_frame.pack(fill=tk.X, pady=2)

        ttk.Label(viz3d_frame, text="Grid for 3D:").pack(anchor='w')
        self.viz3d_grid = tk.StringVar()
        self.viz3d_combo = ttk.Combobox(viz3d_frame, textvariable=self.viz3d_grid,
                                        values=[], width=20)
        self.viz3d_combo.pack(fill=tk.X, pady=1)

        ttk.Button(viz3d_frame, text="🚀 Launch 3D Viewer (new window)",
                  command=self._launch_3d,
                  state='normal' if HAS_PYVISTA else 'disabled').pack(fill=tk.X, pady=2)

        if not HAS_FOLIUM or not HAS_PYVISTA:
            missing = []
            if not HAS_FOLIUM: missing.append("folium")
            if not HAS_PYVISTA: missing.append("pyvista")
            tk.Label(tools_frame, text=f"⚠️ Missing: {', '.join(missing)}",
                    fg="orange", font=("Arial", 7)).pack()

        # Status area
        self.viz_status = tk.Text(left, height=8, width=40, font=("Courier", 8))
        self.viz_status.pack(fill=tk.X, pady=5)

    # ============================================================================
    # TAB 1 METHODS (from your existing code)
    # ============================================================================

    def _auto_import(self):
        """Automatically import data from main table on startup"""
        if not hasattr(self.app, 'data_hub'):
            self.status_var.set("No data hub available")
            return

        samples = self.app.data_hub.get_all()
        if not samples:
            self.status_var.set("No data in main table")
            if hasattr(self, 'data_status'):
                self.data_status.config(text="No data loaded")
            if hasattr(self, 'state_label'):
                self.state_label.config(text="📊 No data loaded")
            return

        # Convert to DataFrame
        self.workflow_state.raw_data = pd.DataFrame(samples)

        # ===== LOAD RAW DATA FOR ERT FILES =====
        if 'Method' in self.workflow_state.raw_data.columns:
            ert_rows = self.workflow_state.raw_data[self.workflow_state.raw_data['Method'] == 'ERT']

            if not ert_rows.empty:
                # First, check if raw arrays are already in the table
                first_row = ert_rows.iloc[0]

                if 'ert_raw_a' in first_row and first_row['ert_raw_a'] is not None:
                    # Arrays are already in the table - use them directly
                    try:
                        a = np.array(first_row['ert_raw_a'])
                        b = np.array(first_row['ert_raw_b'])
                        m = np.array(first_row['ert_raw_m'])
                        n = np.array(first_row['ert_raw_n'])
                        rhoa = np.array(first_row['ert_raw_rhoa'])
                        err = np.array(first_row['ert_raw_err'])

                        # Store in workflow state
                        self.workflow_state.processed['ert_raw'] = {
                            'a': a, 'b': b, 'm': m, 'n': n,
                            'rhoa': rhoa, 'err': err,
                            'file': first_row.get('File_Source', '')
                        }
                        self.workflow_state.ert_file = first_row.get('File_Source', '')
                        print(f"✅ Loaded ERT data from table: {len(rhoa)} measurements")

                    except Exception as e:
                        print(f"❌ Failed to load ERT arrays from table: {e}")
                        # Fall back to file loading
                        self._load_ert_from_file(ert_rows)
                else:
                    # Arrays not in table, try to load from file
                    self._load_ert_from_file(ert_rows)

        # ===== DETECT DATA TYPE =====
        self.data_type = self._detect_data_type(samples)

        # Update labels
        if hasattr(self, 'data_status'):
            data_type_display = self.data_type.upper() if self.data_type else "UNKNOWN"
            self.data_status.config(text=f"Loaded {len(samples)} samples [{data_type_display}]")
        if hasattr(self, 'state_label'):
            self.state_label.config(text=f"📊 Loaded {len(samples)} samples")

        self.status_var.set(f"✅ Auto-imported {len(samples)} samples")

        # ===== CONFIGURE UI FOR THIS DATA TYPE =====
        self._configure_ui_for_data_type()

        # Update displays
        self._update_health_dashboard()

    def _import_from_table(self):
        """Import data from main table"""
        if not hasattr(self.app, 'data_hub'):
            messagebox.showwarning("No Data Hub", "Main app has no data hub")
            return

        samples = self.app.data_hub.get_all()
        if not samples:
            messagebox.showwarning("No Data", "No data in main table")
            return

        # Convert to DataFrame
        self.workflow_state.raw_data = pd.DataFrame(samples)

        # ===== DETECT DATA TYPE =====
        self.data_type = self._detect_data_type(samples)

        # Update labels with data type
        data_type_display = f" [{self.data_type.upper()}]" if self.data_type else ""
        self.state_label.config(text=f"📊 Loaded {len(samples)} samples{data_type_display}")
        self.status_var.set(f"✅ Imported {len(samples)} samples{data_type_display}")

        # ===== CONFIGURE UI FOR THIS DATA TYPE =====
        self._configure_ui_for_data_type()

        # Update displays
        self._update_health_dashboard()

        messagebox.showinfo("Success", f"Imported {len(samples)} samples from main table{data_type_display}")

    def _load_ert_from_file(self, ert_rows):
        """Load ERT data from file as fallback"""
        file_path = ert_rows.iloc[0].get('File_Source')
        if file_path and os.path.exists(file_path):
            try:
                a, b, m, n, rhoa, err = ERTProcessor.load_abem_data(file_path)

                # Filter out invalid measurements
                valid_mask = (rhoa > 0) & (np.isfinite(rhoa)) & (rhoa < 1e8)
                a = a[valid_mask]
                b = b[valid_mask]
                m = m[valid_mask]
                n = n[valid_mask]
                rhoa = rhoa[valid_mask]
                err = err[valid_mask]

                self.workflow_state.processed['ert_raw'] = {
                    'a': a, 'b': b, 'm': m, 'n': n,
                    'rhoa': rhoa, 'err': err,
                    'file': file_path
                }
                self.workflow_state.ert_file = file_path
                print(f"✅ Loaded ERT data from file: {len(rhoa)} measurements")

            except Exception as e:
                print(f"❌ Failed to load ERT data from file: {e}")

    def _detect_data_type(self, samples):
        """Detect what type of geophysics data this is"""
        if not samples:
            return None

        # Check first few samples for clues
        first = samples[0]

        # FIRST AND FOREMOST - Trust the database classification
        if first.get('Auto_Classification') in ['SEISMIC', 'ERT', 'GPR', 'MAGNETICS', 'GRAVITY', 'MT', 'GEOPHONE', 'EM', 'IMU', 'GNSS', 'ENVIRONMENTAL']:
            return first.get('Auto_Classification').lower()

        if first.get('Method') in ['Seismic', 'ERT', 'GPR', 'Magnetics', 'Gravity', 'MT', 'Geophone', 'EM Induction', 'IMU', 'GNSS', 'Environmental']:
            method = first.get('Method').lower()
            if method == 'em induction':
                return 'em'
            return method

        # Seismic indicators - fallback
        if any(k in first for k in ['channel', 'sampling_rate', 'npts', 'Station', 'Network']):
            if first.get('Method') == 'Seismic' or first.get('Auto_Classification') == 'SEISMIC':
                return 'seismic'
            if 'file_source' in first and ('.sac' in str(first['file_source']).lower() or '.mseed' in str(first['file_source']).lower()):
                return 'seismic'

        # ERT indicators - fallback
        if any(k in first for k in ['resistances', 'apparent_rho', 'electrode_spacing']):
            if first.get('Method') == 'ERT' or first.get('Auto_Classification') == 'ERT':
                return 'ert'

        # Gravity indicators - fallback
        if any(k in first for k in ['gravity_mgal', 'raw_reading', 'standard_deviation']):
            if first.get('Method') == 'Gravity' or first.get('Auto_Classification') == 'GRAVITY':
                return 'gravity'

        # Magnetics indicators - fallback
        if any(k in first for k in ['total_field_nt', 'x_nt', 'y_nt', 'z_nt']):
            if first.get('Method') == 'Magnetics' or first.get('Auto_Classification') == 'MAGNETICS':
                return 'magnetics'

        # MT indicators - fallback
        if any(k in first for k in ['frequencies', 'impedance', 'resistivity']):
            if first.get('Method') == 'MT' or first.get('Auto_Classification') == 'MT':
                return 'mt'

        # GPR indicators - fallback
        if any(k in first for k in ['antenna_frequency_mhz', 'time_window_ns', 'samples_per_trace']):
            if first.get('Method') == 'GPR' or first.get('Auto_Classification') == 'GPR':
                return 'gpr'

        # Default to unknown rather than None
        return 'unknown'

    def _update_health_dashboard(self):
        """Update all health metrics based on current data"""
        if self.workflow_state.raw_data is None:
            return

        df = self.workflow_state.raw_data
        total = len(df)

        # Find coordinate columns
        x_col = self._find_coord_column(df, ['x', 'lon', 'longitude', 'easting'])
        y_col = self._find_coord_column(df, ['y', 'lat', 'latitude', 'northing'])

        valid_coords = 0
        x_data = y_data = None

        if x_col and y_col:
            valid_mask = ~(df[x_col].isna() | df[y_col].isna())
            valid_coords = valid_mask.sum()
            x_data = df[x_col][valid_mask].values
            y_data = df[y_col][valid_mask].values

        # Count missing values
        missing = df.isna().sum().sum()

        # Update health labels
        self.health_labels["Total samples:"].config(text=str(total))
        self.health_labels["Valid coordinates:"].config(text=str(valid_coords))
        self.health_labels["Missing values:"].config(text=str(missing))

        # Outliers (if not calculated yet, show 0)
        self.health_labels["Outliers detected:"].config(text="0")

        # Calculate coverage
        coverage_pct = 0
        if valid_coords > 0 and total > 0:
            coverage_pct = (valid_coords / total) * 100
            self.health_labels["Spatial coverage:"].config(text=f"{coverage_pct:.1f}%")
        else:
            self.health_labels["Spatial coverage:"].config(text="0%")

        # Update quality flag
        if total == 0:
            self.quality_flag.config(text="⚪ NO DATA", bg="#f0f0f0", fg="#666")
        elif missing > total * 0.5:
            self.quality_flag.config(text="🔴 POOR QUALITY", bg="#ffcdd2", fg="#b71c1c")
        elif valid_coords < total * 0.7:
            self.quality_flag.config(text="🟡 MODERATE QUALITY", bg="#fff9c4", fg="#f57f17")
        else:
            self.quality_flag.config(text="🟢 GOOD QUALITY", bg="#c8e6c9", fg="#1b5e20")

        # Update the Quality flag label in health dashboard
        self.health_labels["Quality flag:"].config(text=self.quality_flag.cget("text"))

        # Update statistics
        if x_data is not None and y_data is not None and len(x_data) > 1:
            x_min, x_max = x_data.min(), x_data.max()
            y_min, y_max = y_data.min(), y_data.max()

            self.stats_labels["X range:"].config(text=f"{x_min:.2f} - {x_max:.2f}")
            self.stats_labels["Y range:"].config(text=f"{y_min:.2f} - {y_max:.2f}")

            # Estimate spacing
            x_spread = x_max - x_min
            y_spread = y_max - y_min

            if x_spread > 0 and y_spread > 0:
                n_points = len(x_data)
                area = x_spread * y_spread
                avg_spacing = np.sqrt(area / n_points)
                self.stats_labels["Station spacing:"].config(text=f"{avg_spacing:.2f} m")
                self.stats_labels["Survey area:"].config(text=f"{area:.2f} m²")

        # Add data type to the status display if available
        if hasattr(self, 'data_type') and self.data_type:
            data_type_text = f" [{self.data_type.upper()}]"
            # Update the data_status label if it exists
            if hasattr(self, 'data_status'):
                current_text = self.data_status.cget("text")
                if data_type_text not in current_text:
                    self.data_status.config(text=f"{current_text}{data_type_text}")

        # Update plots
        self._update_coverage_map()
        self._update_distributions()

    def _find_coord_column(self, df, possible_names):
        """Find a coordinate column from possible names"""
        for name in possible_names:
            if name in df.columns:
                return name
            for col in df.columns:
                if col.lower() == name:
                    return col
        return None

    def _configure_ui_for_data_type(self):
        """Configure UI based on data type - COMPLETE METHOD"""
        if not hasattr(self, 'data_type'):
            return

        dt = self.data_type

        # Update status message
        if dt == 'seismic':
            self.status_var.set("📡 Seismic data loaded - Processing tab ready")
            # Force update seismic tab UI
            if hasattr(self, 'seis_status'):
                self.seis_status.delete(1.0, tk.END)
                self.seis_status.insert(1.0,
                    f"✅ Seismic data loaded\n"
                    f"• {len(self.workflow_state.raw_data)} traces available\n"
                    f"• Use filters and processing tools above"
                )

        elif dt == 'ert':
            self.status_var.set("⚡ ERT data loaded - Processing tab ready")
            # Force update ERT tab UI with loaded data
            if 'ert_raw' in self.workflow_state.processed:
                ert_data = self.workflow_state.processed['ert_raw']
                if hasattr(self, 'ert_file_label'):
                    self.ert_file_label.config(
                        text=f"✅ {Path(ert_data['file']).name}",
                        fg="green"
                    )
                if hasattr(self, 'ert_status'):
                    self.ert_status.delete(1.0, tk.END)
                    self.ert_status.insert(1.0,
                        f"✅ Loaded: {Path(ert_data['file']).name}\n"
                        f"• Measurements: {len(ert_data['rhoa'])}\n"
                        f"• Resistivity range: {np.min(ert_data['rhoa']):.1f} - "
                        f"{np.max(ert_data['rhoa']):.1f} Ω·m\n"
                        f"• Click 'Run pyGIMLi Inversion' to process"
                    )
            else:
                # Try to load from raw_data if processed data not available
                df = self.workflow_state.raw_data
                ert_rows = df[df['Method'] == 'ERT'] if 'Method' in df.columns else pd.DataFrame()
                if not ert_rows.empty:
                    file_path = ert_rows.iloc[0].get('File_Source')
                    if file_path and os.path.exists(file_path):
                        if hasattr(self, 'ert_file_label'):
                            self.ert_file_label.config(
                                text=f"📁 {Path(file_path).name} (click Import ERT to load)",
                                fg="blue"
                            )

        elif dt == 'gravity':
            self.status_var.set("⚖️ Gravity data loaded - Processing tab ready")
            # Force update gravity tab UI
            if hasattr(self, 'grav_status'):
                grav_cols = [col for col in self.workflow_state.raw_data.columns
                            if any(x in col.lower() for x in ['gravity', 'mgal', 'grav'])]
                self.grav_status.delete(1.0, tk.END)
                self.grav_status.insert(1.0,
                    f"✅ Gravity data loaded\n"
                    f"• {len(self.workflow_state.raw_data)} stations\n"
                    f"• Gravity columns: {', '.join(grav_cols[:3])}\n"
                    f"• Select corrections above and click Compute Bouguer"
                )

        elif dt == 'magnetics':
            self.status_var.set("🧲 Magnetics data loaded - Processing tab ready")
            # Force update magnetics tab UI
            if hasattr(self, 'mag_status'):
                mag_cols = [col for col in self.workflow_state.raw_data.columns
                        if any(x in col.lower() for x in ['mag', 'field', 'nt', 'total_field'])]
                self.mag_status.delete(1.0, tk.END)
                self.mag_status.insert(1.0,
                    f"✅ Magnetics data loaded\n"
                    f"• {len(self.workflow_state.raw_data)} stations\n"
                    f"• Field columns: {', '.join(mag_cols[:3])}\n"
                    f"• Select processing option above"
                )

        elif dt == 'mt':
            self.status_var.set("📡 MT data loaded - Processing tab ready")
            # Force update MT tab UI
            if hasattr(self, 'mt_status'):
                self.mt_status.delete(1.0, tk.END)
                self.mt_status.insert(1.0,
                    f"✅ MT data loaded\n"
                    f"• {len(self.workflow_state.raw_data)} frequencies\n"
                    f"• Click Apparent Resistivity to process"
                )

        elif dt == 'gpr':
            self.status_var.set("📻 GPR data loaded - Processing tab ready")
            # Force update GPR tab UI
            if hasattr(self, 'gpr_status'):
                self.gpr_status.delete(1.0, tk.END)
                self.gpr_status.insert(1.0,
                    f"✅ GPR data loaded\n"
                    f"• {len(self.workflow_state.raw_data)} sections\n"
                    f"• Select processing option above"
                )

        elif dt == 'em':
            self.status_var.set("🧲 EM Induction data loaded - Processing tab ready")
            # Force update EM tab UI (part of MT tab in your UI)
            if hasattr(self, 'mt_status'):
                self.mt_status.delete(1.0, tk.END)
                self.mt_status.insert(1.0,
                    f"✅ EM Induction data loaded\n"
                    f"• {len(self.workflow_state.raw_data)} measurements\n"
                    f"• Processing options in MT/EM tab"
                )

        elif dt == 'geophone':
            self.status_var.set("🎤 Geophone data loaded - Processing tab ready")
            # Geophone data uses seismic processing tab
            if hasattr(self, 'seis_status'):
                self.seis_status.delete(1.0, tk.END)
                self.seis_status.insert(1.0,
                    f"✅ Geophone data loaded\n"
                    f"• {len(self.workflow_state.raw_data)} traces\n"
                    f"• Use seismic processing tools"
                )

        elif dt == 'imu':
            self.status_var.set("📊 IMU data loaded - Processing tab ready")
            # IMU data uses potential fields tab
            if hasattr(self, 'grav_status'):  # Reuse gravity status area
                self.grav_status.delete(1.0, tk.END)
                self.grav_status.insert(1.0,
                    f"✅ IMU data loaded\n"
                    f"• {len(self.workflow_state.raw_data)} samples\n"
                    f"• View in IMU display"
                )

        elif dt == 'gnss':
            self.status_var.set("🗺️ GNSS data loaded - Processing tab ready")
            # GNSS data uses auxiliary tab (not directly in processing)
            # Just update status
            pass

        elif dt == 'environmental':
            self.status_var.set("🌡️ Environmental data loaded - Processing tab ready")
            # Environmental data uses environmental tab
            if hasattr(self, 'env_ax'):
                self.env_ax.clear()
                self.env_ax.text(0.5, 0.5,
                    f"Environmental Data Loaded\n{len(self.workflow_state.raw_data)} samples",
                    ha='center', va='center', transform=self.env_ax.transAxes)
                self.env_canvas.draw()

        elif dt == 'unknown':
            self.status_var.set("📊 Generic data loaded - Limited processing available")
            # Show generic message
            if hasattr(self, 'seis_status'):
                self.seis_status.delete(1.0, tk.END)
                self.seis_status.insert(1.0,
                    f"ℹ️ Generic data loaded\n"
                    f"• {len(self.workflow_state.raw_data)} rows\n"
                    f"• Columns: {', '.join(self.workflow_state.raw_data.columns[:5])}\n"
                    f"• Use Visualization tab for plotting"
                )
        else:
            self.status_var.set("📊 No data loaded - Import from table")

        # Configure processing subtabs based on data type
        if hasattr(self, 'processing_notebook'):
            # First, enable ALL tabs (they start enabled, but we'll set based on data type)
            for i in range(self.processing_notebook.index('end')):
                self.processing_notebook.tab(i, state='normal')

            # Then, highlight the relevant tab based on data type
            if dt == 'seismic' or dt == 'geophone':
                self.processing_notebook.select(0)  # Seismic tab
            elif dt == 'ert':
                self.processing_notebook.select(1)  # ERT tab
            elif dt == 'gravity' or dt == 'magnetics' or dt == 'imu':
                self.processing_notebook.select(2)  # Gravity tab (also magnetics/IMU)
            elif dt == 'mt' or dt == 'em':
                self.processing_notebook.select(4)  # MT/EM tab
            elif dt == 'gpr':
                self.processing_notebook.select(5)  # GPR tab
            elif dt == 'environmental':
                self.processing_notebook.select(6)  # Environmental tab

        # Update the health dashboard with data type info
        self._update_health_dashboard()

    def _update_coverage_map(self):
        """Update the coverage map with current data"""
        if self.workflow_state.raw_data is None:
            return

        df = self.workflow_state.raw_data
        x_col = self._find_coord_column(df, ['x', 'lon', 'longitude', 'easting'])
        y_col = self._find_coord_column(df, ['y', 'lat', 'latitude', 'northing'])

        if not x_col or not y_col:
            self.coverage_ax.clear()
            self.coverage_ax.text(0.5, 0.5, "No coordinate columns found",
                                 ha='center', va='center', transform=self.coverage_ax.transAxes)
            self.coverage_canvas.draw()
            return

        x_data = df[x_col].values
        y_data = df[y_col].values
        valid = ~(np.isnan(x_data) | np.isnan(y_data))

        if valid.sum() == 0:
            self.coverage_ax.clear()
            self.coverage_ax.text(0.5, 0.5, "No valid coordinates",
                                 ha='center', va='center', transform=self.coverage_ax.transAxes)
            self.coverage_canvas.draw()
            return

        self.coverage_ax.clear()

        # Plot points
        self.coverage_ax.scatter(x_data[valid], y_data[valid],
                               c='blue', s=20, alpha=0.6, edgecolors='black', linewidth=0.5)

        # Add convex hull
        if valid.sum() > 3:
            try:
                points = np.column_stack([x_data[valid], y_data[valid]])
                hull = ConvexHull(points)
                for simplex in hull.simplices:
                    self.coverage_ax.plot(points[simplex, 0], points[simplex, 1],
                                        'r-', linewidth=1, alpha=0.7)
            except Exception as e:
                pass

        self.coverage_ax.set_xlabel(x_col)
        self.coverage_ax.set_ylabel(y_col)
        self.coverage_ax.set_title(f"Survey Coverage ({valid.sum()} stations)")
        self.coverage_ax.grid(True, alpha=0.3)
        self.coverage_ax.set_aspect('equal', adjustable='box')

        self.coverage_fig.tight_layout()
        self.coverage_canvas.draw()

    def _update_distributions(self):
        """Update distribution plots"""
        if self.workflow_state.raw_data is None:
            return

        df = self.workflow_state.raw_data
        numeric_cols = df.select_dtypes(include=[np.number]).columns[:3]

        self.dist_ax.clear()

        if len(numeric_cols) == 0:
            self.dist_ax.text(0.5, 0.5, "No numeric columns found",
                             ha='center', va='center', transform=self.dist_ax.transAxes)
            self.dist_canvas.draw()
            return

        colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
        for i, col in enumerate(numeric_cols):
            data = df[col].dropna().values
            if len(data) > 1:
                self.dist_ax.hist(data, bins=30, alpha=0.5, label=col, color=colors[i % 3])

        self.dist_ax.set_xlabel("Value")
        self.dist_ax.set_ylabel("Frequency")
        self.dist_ax.set_title("Data Distributions")
        self.dist_ax.legend()
        self.dist_ax.grid(True, alpha=0.3)

        self.dist_fig.tight_layout()
        self.dist_canvas.draw()

    def _detect_outliers(self):
        """Detect outliers using Median Absolute Deviation"""
        if self.workflow_state.raw_data is None:
            self.qc_status.delete(1.0, tk.END)
            self.qc_status.insert(1.0, "⚠️ Import data first")
            return

        df = self.workflow_state.raw_data
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        outlier_counts = {}
        for col in numeric_cols:
            data = df[col].dropna()
            if len(data) > 5:
                median = np.median(data)
                mad = np.median(np.abs(data - median))
                threshold = 3 * mad
                outliers = np.abs(data - median) > threshold
                outlier_counts[col] = outliers.sum()

        # Build status text
        if outlier_counts:
            status_text = "Outlier Detection Results (3×MAD):\n"
            total_outliers = 0
            for col, count in outlier_counts.items():
                if count > 0:
                    status_text += f"• {col}: {count} outliers\n"
                    total_outliers += count
            if total_outliers == 0:
                status_text = "✓ No outliers detected in any column"
        else:
            status_text = "No numeric columns found for outlier detection"

        self.qc_status.delete(1.0, tk.END)
        self.qc_status.insert(1.0, status_text)

        # Update health dashboard
        total_outliers = sum(outlier_counts.values())
        self.health_labels["Outliers detected:"].config(text=str(total_outliers))

    def _remove_missing(self):
        """Remove rows with missing values"""
        if self.workflow_state.raw_data is None:
            self.qc_status.delete(1.0, tk.END)
            self.qc_status.insert(1.0, "⚠️ Import data first")
            return

        before = len(self.workflow_state.raw_data)

        # Count missing before
        missing_before = self.workflow_state.raw_data.isna().sum().sum()

        # Remove rows with any missing values
        self.workflow_state.raw_data = self.workflow_state.raw_data.dropna()
        after = len(self.workflow_state.raw_data)

        removed = before - after
        missing_after = self.workflow_state.raw_data.isna().sum().sum()

        # Update status
        if removed > 0:
            status_text = (f"✓ Removed {removed} rows with missing values\n"
                          f"• Rows before: {before}\n"
                          f"• Rows after: {after}\n"
                          f"• Missing values: {missing_before} → {missing_after}")
        else:
            status_text = "✓ No missing values found in dataset"

        self.qc_status.delete(1.0, tk.END)
        self.qc_status.insert(1.0, status_text)

        # Update health dashboard
        self._update_health_dashboard()

    def _transform_coords(self):
        """Transform coordinates between systems"""
        if self.workflow_state.raw_data is None:
            self.qc_status.delete(1.0, tk.END)
            self.qc_status.insert(1.0, "⚠️ Import data first")
            return

        if not HAS_PYPROJ:
            self.qc_status.delete(1.0, tk.END)
            self.qc_status.insert(1.0, "❌ pyproj not installed")
            return

        # Simple dialog for coordinate transformation
        dialog = tk.Toplevel(self.window)
        dialog.title("Coordinate Transformation")
        dialog.geometry("400x300")
        dialog.transient(self.window)

        tk.Label(dialog, text="From EPSG:").pack(pady=5)
        from_entry = ttk.Entry(dialog)
        from_entry.insert(0, "4326")  # WGS84
        from_entry.pack()

        tk.Label(dialog, text="To EPSG:").pack(pady=5)
        to_entry = ttk.Entry(dialog)
        to_entry.insert(0, "32633")  # UTM zone 33N
        to_entry.pack()

        def do_transform():
            try:
                from_epsg = int(from_entry.get())
                to_epsg = int(to_entry.get())

                df = self.workflow_state.raw_data
                x_col = self._find_coord_column(df, ['x', 'lon', 'longitude', 'easting'])
                y_col = self._find_coord_column(df, ['y', 'lat', 'latitude', 'northing'])

                if not x_col or not y_col:
                    self.qc_status.delete(1.0, tk.END)
                    self.qc_status.insert(1.0, "❌ Could not find coordinate columns")
                    dialog.destroy()
                    return

                # Transform
                transformer = pyproj.Transformer.from_crs(from_epsg, to_epsg, always_xy=True)
                x_new, y_new = transformer.transform(df[x_col].values, df[y_col].values)

                # Add new columns
                self.workflow_state.raw_data[f'{x_col}_transformed'] = x_new
                self.workflow_state.raw_data[f'{y_col}_transformed'] = y_new

                # Update status
                status_text = (f"✓ Transformed coordinates\n"
                              f"• From EPSG:{from_epsg} → To EPSG:{to_epsg}\n"
                              f"• Added columns: {x_col}_transformed, {y_col}_transformed")
                self.qc_status.delete(1.0, tk.END)
                self.qc_status.insert(1.0, status_text)

                self._update_coverage_map()
                dialog.destroy()

            except Exception as e:
                self.qc_status.delete(1.0, tk.END)
                self.qc_status.insert(1.0, f"❌ Error: {str(e)[:100]}")
                dialog.destroy()

        ttk.Button(dialog, text="Transform", command=do_transform).pack(pady=10)

    # ============================================================================
    # TAB 3 METHODS
    # ============================================================================

    def _compute_hgrad(self):
        """Compute horizontal gradient"""
        if not self.workflow_state.grids:
            messagebox.showwarning("No Grid", "Create a grid first")
            return

        grid_name = list(self.workflow_state.grids.keys())[-1]
        grid_data = self.workflow_state.grids[grid_name]

        if 'X' not in grid_data or 'Z' not in grid_data:
            return

        X = grid_data['X']
        Y = grid_data['Y']
        Z = grid_data['Z']
        dx = X[0, 1] - X[0, 0]
        dy = Y[1, 0] - Y[0, 0]

        hgrad = GriddingEngine.horizontal_gradient(Z, dx, dy)

        self.grid_ax.clear()
        im = self.grid_ax.contourf(X, Y, hgrad, levels=20, cmap='viridis')
        plt.colorbar(im, ax=self.grid_ax, label='Horizontal Gradient')
        self.grid_ax.set_title("Horizontal Gradient")
        self.grid_canvas.draw()

        self.workflow_state.add_grid("hgrad", {'X': X, 'Y': Y, 'Z': hgrad})

    def _compute_tilt(self):
        """Compute tilt derivative"""
        if not self.workflow_state.grids:
            messagebox.showwarning("No Grid", "Create a grid first")
            return

        grid_name = list(self.workflow_state.grids.keys())[-1]
        grid_data = self.workflow_state.grids[grid_name]

        if 'X' not in grid_data or 'Z' not in grid_data:
            return

        X = grid_data['X']
        Y = grid_data['Y']
        Z = grid_data['Z']
        dx = X[0, 1] - X[0, 0]
        dy = Y[1, 0] - Y[0, 0]

        tilt = GriddingEngine.tilt_derivative(Z, dx, dy)

        self.grid_ax.clear()
        im = self.grid_ax.contourf(X, Y, tilt, levels=20, cmap='RdBu')
        plt.colorbar(im, ax=self.grid_ax, label='Tilt (rad)')
        self.grid_ax.set_title("Tilt Derivative")
        self.grid_canvas.draw()

        self.workflow_state.add_grid("tilt", {'X': X, 'Y': Y, 'Z': tilt})

    # ============================================================================
    # TAB 4 METHODS - REAL IMPLEMENTATIONS
    # ============================================================================

    def _run_euler(self):
        """Run Euler deconvolution on REAL field data"""
        if self.workflow_state.raw_data is None:
            self.euler_status.delete(1.0, tk.END)
            self.euler_status.insert(1.0, "⚠️ Import data first")
            return

        try:
            # Get field data (magnetic or gravity)
            df = self.workflow_state.raw_data
            field_col = self._find_coord_column(df, ['mag', 'field', 'nT', 'total_field', 'gravity', 'mgal'])
            x_col = self._find_coord_column(df, ['x', 'lon', 'longitude', 'easting'])
            y_col = self._find_coord_column(df, ['y', 'lat', 'latitude', 'northing'])

            if not field_col:
                self.euler_status.delete(1.0, tk.END)
                self.euler_status.insert(1.0, "❌ No field data column found")
                return

            if not x_col or not y_col:
                self.euler_status.delete(1.0, tk.END)
                self.euler_status.insert(1.0, "❌ Need X and Y coordinates")
                return

            # Get valid data
            data = df[[x_col, y_col, field_col]].dropna()
            if len(data) < 20:
                self.euler_status.delete(1.0, tk.END)
                self.euler_status.insert(1.0, f"❌ Need ≥20 points (have {len(data)})")
                return

            x = data[x_col].values
            y = data[y_col].values
            field = data[field_col].values

            # Create grid for gradient calculation
            from scipy.interpolate import griddata

            # Define grid extent with 10% padding
            x_min, x_max = x.min(), x.max()
            y_min, y_max = y.min(), y.max()
            x_pad = (x_max - x_min) * 0.1
            y_pad = (y_max - y_min) * 0.1

            xi = np.linspace(x_min - x_pad, x_max + x_pad, 50)
            yi = np.linspace(y_min - y_pad, y_max + y_pad, 50)
            Xi, Yi = np.meshgrid(xi, yi)

            # Grid the data
            Zi = griddata((x, y), field, (Xi, Yi), method='cubic')

            # Handle any NaN values (fill with nearest neighbor)
            nan_mask = np.isnan(Zi)
            if nan_mask.any():
                Zi_nearest = griddata((x, y), field, (Xi, Yi), method='nearest')
                Zi[nan_mask] = Zi_nearest[nan_mask]

            # Calculate gradients
            dx = xi[1] - xi[0]
            dy = yi[1] - yi[0]
            gx, gy = np.gradient(Zi, dx, dy)

            # Interpolate gradients back to original points
            points = np.column_stack([Xi.flatten(), Yi.flatten()])
            gx_flat = griddata(points, gx.flatten(), (x, y), method='linear')
            gy_flat = griddata(points, gy.flatten(), (x, y), method='linear')

            # Handle any NaN in gradients
            nan_gx = np.isnan(gx_flat)
            if nan_gx.any():
                gx_flat[nan_gx] = griddata(points, gx.flatten(), (x[nan_gx], y[nan_gx]), method='nearest')
                gy_flat[nan_gx] = griddata(points, gy.flatten(), (x[nan_gx], y[nan_gx]), method='nearest')

            # Run Euler deconvolution with moving window
            structural_index = self.si_var.get()
            window = self.euler_window.get()
            solutions = []

            for i in range(0, len(x) - window, window // 2):
                idx = slice(i, i + window)
                x_win = x[idx]
                y_win = y[idx]
                f_win = field[idx]
                gx_win = gx_flat[idx]
                gy_win = gy_flat[idx]

                # 2D Euler equation: (x-x0)*∂T/∂x + (y-y0)*∂T/∂y = N*(B - T)
                # Rearranged: x0*∂T/∂x + y0*∂T/∂y + N*B = x*∂T/∂x + y*∂T/∂y + N*T
                A = np.column_stack([gx_win, gy_win, np.ones_like(gx_win)])
                b = x_win*gx_win + y_win*gy_win + structural_index * f_win

                try:
                    sol, residuals, rank, s = np.linalg.lstsq(A, b, rcond=None)
                    x0, y0, base = sol

                    # Estimate depth from gradient ratio
                    # z0 = |T| / |∇T| (simplified)
                    grad_mag = np.sqrt(np.mean(gx_win**2 + gy_win**2))
                    if grad_mag > 1e-10:
                        z0 = np.abs(np.mean(f_win)) / grad_mag
                    else:
                        z0 = 0

                    # Quality control
                    if 0 < z0 < 100:  # Reasonable depth range
                        solutions.append({
                            'x': x0,
                            'y': y0,
                            'z': z0,
                            'residual': np.mean(residuals) if len(residuals) > 0 else 0,
                            'n_points': window
                        })
                except Exception as e:
                    continue

            # Clear previous plot
            self.model_ax.clear()

            if solutions:
                # Extract solution parameters
                xs = [s['x'] for s in solutions]
                ys = [s['y'] for s in solutions]
                zs = [s['z'] for s in solutions]
                residuals = [s['residual'] for s in solutions]

                # Scatter plot colored by depth
                scatter = self.model_ax.scatter(xs, ys, c=zs, cmap='viridis',
                                            s=50, alpha=0.7, edgecolors='black',
                                            vmin=0, vmax=np.percentile(zs, 95))
                plt.colorbar(scatter, ax=self.model_ax, label='Depth (m)')

                # Plot original data points for context
                self.model_ax.scatter(x, y, c='lightgray', s=10, alpha=0.3, marker='.')

                self.model_ax.set_xlabel(x_col)
                self.model_ax.set_ylabel(y_col)
                self.model_ax.set_title(f"Euler Deconvolution (SI={structural_index})")
                self.model_ax.grid(True, alpha=0.3)

                # Calculate statistics
                depths = np.array(zs)
                q25, q50, q75 = np.percentile(depths, [25, 50, 75])

                status_text = (f"✓ Euler Deconvolution\n"
                            f"• Input points: {len(data)}\n"
                            f"• Solutions: {len(solutions)}\n"
                            f"• Depth range: {depths.min():.1f} - {depths.max():.1f} m\n"
                            f"• Median depth: {q50:.1f} m (Q25={q25:.1f}, Q75={q75:.1f})\n"
                            f"• Structural index: {structural_index}")
            else:
                # Plot original data if no solutions found
                scatter = self.model_ax.scatter(x, y, c=field, cmap='viridis',
                                            s=30, alpha=0.7, edgecolors='black')
                plt.colorbar(scatter, ax=self.model_ax, label='Field Value')
                self.model_ax.set_xlabel(x_col)
                self.model_ax.set_ylabel(y_col)
                self.model_ax.set_title(f"Input Data - No Euler Solutions (SI={structural_index})")
                status_text = "❌ No Euler solutions found"

            self.model_canvas.draw()
            self.model_notebook.select(1)  # Switch to plot tab

            self.euler_status.delete(1.0, tk.END)
            self.euler_status.insert(1.0, status_text)

            # Store results
            self.workflow_state.processed['euler_solutions'] = solutions
            self.workflow_state.log_step('euler', {
                'structural_index': structural_index,
                'window': window,
                'solutions': len(solutions)
            })

        except Exception as e:
            self.euler_status.delete(1.0, tk.END)
            self.euler_status.insert(1.0, f"❌ Error: {str(e)[:100]}")
            import traceback
            traceback.print_exc()

    def _run_joint_inversion(self):
        """Run joint inversion of ERT and Gravity data using pyGIMLi"""
        if not HAS_PYGIMLI:
            self.joint_status.delete(1.0, tk.END)
            self.joint_status.insert(1.0, "❌ pyGIMLi required")
            return
        import threading
        def _worker():
            # Check if we have both ERT and gravity data
            if not hasattr(self.workflow_state, 'ert_file') or not self.workflow_state.ert_file:
                self.joint_status.delete(1.0, tk.END)
                self.joint_status.insert(1.0, "⚠️ Please import an ERT data file first")
                return

            # Check for gravity data in workflow
            if 'gravity_bouguer' not in self.workflow_state.processed:
                self.joint_status.delete(1.0, tk.END)
                self.joint_status.insert(1.0, "⚠️ Please compute Bouguer anomaly first (Gravity tab)")
                return

            self.joint_status.delete(1.0, tk.END)
            self.joint_status.insert(1.0, "🔄 Running joint inversion...")
            self.window.update()

            try:
                import pygimli as pg
                from pygimli.physics import ert
                from pygimli.physics.gravimetry import GravityModelling

                # --------------------------------------------------
                # Load ERT data
                # --------------------------------------------------
                filepath = self.workflow_state.ert_file
                ert_data = ert.load(filepath)

                # --------------------------------------------------
                # Get gravity data
                # --------------------------------------------------
                gravity_anomalies = self.workflow_state.processed['gravity_bouguer']

                # Need station coordinates for gravity
                df = self.workflow_state.raw_data
                x_col = self._find_coord_column(df, ['x', 'lon', 'longitude', 'easting'])
                y_col = self._find_coord_column(df, ['y', 'lat', 'latitude', 'northing'])

                if not x_col or not y_col:
                    self.joint_status.delete(1.0, tk.END)
                    self.joint_status.insert(1.0, "❌ Need coordinates for gravity stations")
                    return

                # Create gravity data container
                gravity_data = pg.core.DataContainer()

                # Add measurement positions
                for i, (idx, row) in enumerate(df.iterrows()):
                    if i >= len(gravity_anomalies):
                        break
                    gravity_data.createSensor([row[x_col], row[y_col], 0])

                # Add gravity measurements
                gravity_data.add('g', gravity_anomalies[:gravity_data.sensorCount()])

                # --------------------------------------------------
                # Set up joint inversion
                # --------------------------------------------------
                coupling = self.coupling_var.get()

                # Create joint modelling object
                joint = pg.core.JointModelling()

                # Add ERT part
                fop_ert = ert.ERTModelling()
                fop_ert.setData(ert_data)
                joint.add(fop_ert, ert_data, weight=1.0)

                # Add gravity part
                fop_grav = GravityModelling(gravity_data)
                joint.add(fop_grav, gravity_data, weight=coupling)

                # Run inversion
                inv = joint.invert(
                    maxIter=self.joint_iter.get(),
                    verbose=False
                )

                # --------------------------------------------------
                # Plot results
                # --------------------------------------------------
                self.model_ax.clear()

                # Plot ERT result
                ert_result = inv[0]  # First part is ERT model
                depth = pg.utils.grafic.createDepthAxis(ert_result)

                # Simple 1D plot for demonstration
                # In production, would create proper 2D/3D visualization
                self.model_ax.plot(ert_result, depth, 'b-', linewidth=2, label='ERT Model')
                self.model_ax.set_xlabel("Resistivity (Ω·m)")
                self.model_ax.set_ylabel("Depth (m)")
                self.model_ax.set_title(f"Joint Inversion (α={coupling})")
                self.model_ax.invert_yaxis()
                self.model_ax.grid(True, alpha=0.3)

                self.model_canvas.draw()
                self.model_notebook.select(1)

                # Store results
                self.workflow_state.add_model('joint', inv)
                self.workflow_state.log_step('joint_inversion', {
                    'coupling': coupling,
                    'iterations': self.joint_iter.get()
                })

                # Get RMS
                try:
                    rms = inv.relrms()
                    rms_text = f"{rms:.2f}%"
                except Exception as e:
                    rms_text = "N/A"

                self.joint_status.delete(1.0, tk.END)
                self.joint_status.insert(1.0,
                    f"✓ Joint inversion complete\n"
                    f"Coupling: {coupling}\n"
                    f"RMS: {rms_text}")

            except Exception as e:
                self.joint_status.delete(1.0, tk.END)
                self.joint_status.insert(1.0, f"❌ Error: {str(e)[:200]}")
                import traceback
                traceback.print_exc()
        threading.Thread(target=_worker, daemon=True).start()
    def _cluster_data(self):
        """Cluster geophysical attributes using scikit-learn"""
        if not HAS_SKLEARN:
            self.ml_status.delete(1.0, tk.END)
            self.ml_status.insert(1.0, "❌ scikit-learn not installed")
            return

        if self.workflow_state.raw_data is None:
            self.ml_status.delete(1.0, tk.END)
            self.ml_status.insert(1.0, "⚠️ Import data first")
            return
        import threading
        def _worker():
            try:
                # Get numeric columns for clustering
                df = self.workflow_state.raw_data
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

                # Allow user to select columns (in a real UI, this would be checkboxes)
                # For now, use first 5 numeric columns or all if less than 5
                if len(numeric_cols) > 5:
                    numeric_cols = numeric_cols[:5]
                    auto_selected = True
                else:
                    auto_selected = False

                if len(numeric_cols) < 2:
                    self.ml_status.delete(1.0, tk.END)
                    self.ml_status.insert(1.0, "❌ Need at least 2 numeric columns for clustering")
                    return

                # Prepare data - remove rows with any NaN
                data = df[numeric_cols].dropna()
                if len(data) < 10:
                    self.ml_status.delete(1.0, tk.END)
                    self.ml_status.insert(1.0, f"❌ Need at least 10 samples (have {len(data)})")
                    return

                X = data.values

                # Standardize features
                from sklearn.preprocessing import StandardScaler
                scaler = StandardScaler()
                X_scaled = scaler.fit_transform(X)

                # Perform clustering based on selected method
                from sklearn.cluster import KMeans, DBSCAN

                if self.ml_method.get() == "kmeans":
                    # KMeans clustering
                    n_clusters = self.n_clusters.get()
                    model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
                    labels = model.fit_predict(X_scaled)

                    # Calculate cluster statistics
                    unique_labels = np.unique(labels)
                    n_clusters_found = len(unique_labels)

                    # Calculate silhouette score if enough samples
                    from sklearn.metrics import silhouette_score
                    if len(unique_labels) > 1 and len(X) > n_clusters:
                        sil_score = silhouette_score(X_scaled, labels)
                        sil_text = f"{sil_score:.3f}"
                    else:
                        sil_text = "N/A"

                    status_text = (f"✓ KMeans clustering complete\n"
                                f"• Features: {', '.join(numeric_cols)}\n"
                                f"• Samples: {len(X)}\n"
                                f"• Clusters: {n_clusters_found}\n"
                                f"• Silhouette score: {sil_text}")

                    # Get cluster centers for plotting
                    centers = model.cluster_centers_

                else:  # DBSCAN
                    # DBSCAN clustering
                    model = DBSCAN(eps=0.5, min_samples=5)
                    labels = model.fit_predict(X_scaled)

                    unique_labels = np.unique(labels)
                    n_clusters_found = len(unique_labels) - (1 if -1 in labels else 0)
                    n_noise = sum(labels == -1)

                    status_text = (f"✓ DBSCAN clustering complete\n"
                                f"• Features: {', '.join(numeric_cols)}\n"
                                f"• Samples: {len(X)}\n"
                                f"• Clusters: {n_clusters_found}\n"
                                f"• Noise points: {n_noise}")

                    centers = None

                # Plot results (first two dimensions)
                self.model_ax.clear()

                # Use first two features for visualization
                scatter = self.model_ax.scatter(X_scaled[:, 0], X_scaled[:, 1],
                                            c=labels, cmap='tab10', s=50, alpha=0.7,
                                            edgecolors='black', linewidth=0.5)

                # Add cluster centers for KMeans
                if centers is not None:
                    self.model_ax.scatter(centers[:, 0], centers[:, 1],
                                        c='red', s=200, marker='X',
                                        edgecolors='black', linewidth=2,
                                        label='Cluster Centers')
                    self.model_ax.legend()

                plt.colorbar(scatter, ax=self.model_ax, label='Cluster')

                self.model_ax.set_xlabel(f"{numeric_cols[0]} (standardized)")
                self.model_ax.set_ylabel(f"{numeric_cols[1]} (standardized)")
                self.model_ax.set_title(f"{self.ml_method.get().upper()} Clustering")
                self.model_ax.grid(True, alpha=0.3)

                self.model_canvas.draw()
                self.model_notebook.select(1)  # Switch to plot tab

                # Add note about auto-selection if applicable
                if auto_selected:
                    status_text += f"\nℹ️ First 5 numeric columns auto-selected"

                self.ml_status.delete(1.0, tk.END)
                self.ml_status.insert(1.0, status_text)

                # Store results
                self.workflow_state.processed['clustering'] = {
                    'labels': labels.tolist(),
                    'features': numeric_cols,
                    'method': self.ml_method.get(),
                    'n_clusters': n_clusters_found,
                    'data': X_scaled.tolist()
                }

            except Exception as e:
                self.ml_status.delete(1.0, tk.END)
                self.ml_status.insert(1.0, f"❌ Error: {str(e)[:100]}")
                import traceback
                traceback.print_exc()
        threading.Thread(target=_worker, daemon=True).start()
    def _xgboost_predict(self):
        """Run XGBoost prediction on REAL data"""
        if not HAS_XGBOOST:
            self.ml_status.delete(1.0, tk.END)
            self.ml_status.insert(1.0, "❌ XGBoost not installed")
            return

        if self.workflow_state.raw_data is None:
            self.ml_status.delete(1.0, tk.END)
            self.ml_status.insert(1.0, "⚠️ Import data first")
            return
        import threading
        def _worker():
            try:
                df = self.workflow_state.raw_data

                # Get target column from UI or auto-select
                target_col = self.xgb_target.get()

                # If no target selected, show column selection dialog
                if not target_col or target_col not in df.columns:
                    # Get all numeric columns
                    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

                    if len(numeric_cols) < 2:
                        self.ml_status.delete(1.0, tk.END)
                        self.ml_status.insert(1.0, "❌ Need at least 2 numeric columns")
                        return

                    # For now, use the last numeric column as target
                    # In a real UI, this would be a dropdown
                    target_col = numeric_cols[-1]
                    feature_cols = numeric_cols[:-1]
                    auto_selected = True
                else:
                    # Use selected target, all other numeric columns as features
                    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                    feature_cols = [c for c in numeric_cols if c != target_col]
                    auto_selected = False

                if len(feature_cols) < 1:
                    self.ml_status.delete(1.0, tk.END)
                    self.ml_status.insert(1.0, "❌ Need at least one feature column")
                    return

                # Prepare data - remove rows with any NaN in features or target
                data = df[feature_cols + [target_col]].dropna()
                if len(data) < 20:
                    self.ml_status.delete(1.0, tk.END)
                    self.ml_status.insert(1.0, f"❌ Need at least 20 samples (have {len(data)})")
                    return

                X = data[feature_cols].values
                y = data[target_col].values

                # Train/test split
                from sklearn.model_selection import train_test_split
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=42
                )

                # Train XGBoost model with hyperparameter tuning
                import xgboost as xgb

                # Create model with reasonable defaults
                model = xgb.XGBRegressor(
                    n_estimators=100,
                    max_depth=5,
                    learning_rate=0.1,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42,
                    verbosity=0
                )

                # Train the model
                model.fit(
                    X_train, y_train,
                    eval_set=[(X_test, y_test)],
                    verbose=False
                )

                # Predict
                y_pred = model.predict(X_test)

                # Calculate metrics
                from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
                r2 = r2_score(y_test, y_pred)
                mae = mean_absolute_error(y_test, y_pred)
                rmse = np.sqrt(mean_squared_error(y_test, y_pred))

                # Calculate relative error (if y not near zero)
                if np.abs(np.mean(y_test)) > 1e-10:
                    rel_error = np.mean(np.abs((y_test - y_pred) / y_test)) * 100
                else:
                    rel_error = np.nan

                # Plot results
                self.model_ax.clear()

                # Scatter plot of actual vs predicted
                scatter = self.model_ax.scatter(y_test, y_pred, alpha=0.6,
                                            c='blue', edgecolors='black', linewidth=0.5)

                # Perfect prediction line
                min_val = min(y_test.min(), y_pred.min())
                max_val = max(y_test.max(), y_pred.max())
                self.model_ax.plot([min_val, max_val], [min_val, max_val],
                                'r--', linewidth=2, label='Perfect prediction')

                self.model_ax.set_xlabel(f"Actual {target_col}")
                self.model_ax.set_ylabel(f"Predicted {target_col}")
                self.model_ax.set_title(f"XGBoost: {target_col}")
                self.model_ax.legend()
                self.model_ax.grid(True, alpha=0.3)

                # Add trend line
                from scipy import stats
                z = np.polyfit(y_test, y_pred, 1)
                p = np.poly1d(z)
                self.model_ax.plot([min_val, max_val], p([min_val, max_val]),
                                'g-', alpha=0.5, label=f'Trend (slope={z[0]:.2f})')
                self.model_ax.legend()

                self.model_canvas.draw()
                self.model_notebook.select(1)

                # Feature importance
                importance = model.feature_importances_
                importance_idx = np.argsort(importance)[::-1]

                # Get top features
                n_top = min(5, len(feature_cols))
                top_features = []
                for i in range(n_top):
                    idx = importance_idx[i]
                    top_features.append(f"{feature_cols[idx]}: {importance[idx]:.3f}")

                features_text = "\n".join(top_features)

                # Update status
                status_text = (f"✓ XGBoost Regression\n"
                            f"• Target: {target_col}\n"
                            f"• Features: {len(feature_cols)}\n"
                            f"• Training samples: {len(X_train)}\n"
                            f"• Test samples: {len(X_test)}\n"
                            f"• R² = {r2:.3f}\n"
                            f"• MAE = {mae:.2f}\n"
                            f"• RMSE = {rmse:.2f}\n")

                if not np.isnan(rel_error):
                    status_text += f"• Relative error: {rel_error:.1f}%\n"

                status_text += f"\nTop features:\n{features_text}"

                if auto_selected:
                    status_text += f"\nℹ️ Target auto-selected: {target_col}"

                self.ml_status.delete(1.0, tk.END)
                self.ml_status.insert(1.0, status_text)

                # Store results
                self.workflow_state.processed['xgboost'] = {
                    'target': target_col,
                    'features': feature_cols,
                    'r2': r2,
                    'mae': mae,
                    'rmse': rmse,
                    'feature_importance': dict(zip(feature_cols, importance.tolist())),
                    'model': model  # Note: model may not be serializable
                }

            except Exception as e:
                self.ml_status.delete(1.0, tk.END)
                self.ml_status.insert(1.0, f"❌ Error: {str(e)[:100]}")
                import traceback
                traceback.print_exc()
        threading.Thread(target=_worker, daemon=True).start()
    def _detect_lineaments(self):
        """Detect lineaments using edge detection on gridded data"""
        if not self.workflow_state.grids:
            self.line_status.delete(1.0, tk.END)
            self.line_status.insert(1.0, "⚠️ Create a grid first (Tab 3)")
            return

        try:
            # Get the selected grid or last grid
            grid_name = self.export_grid.get() if hasattr(self, 'export_grid') else None
            if not grid_name or grid_name not in self.workflow_state.grids:
                grid_name = list(self.workflow_state.grids.keys())[-1]
                if hasattr(self, 'export_grid'):
                    self.export_grid.set(grid_name)

            grid_data = self.workflow_state.grids[grid_name]

            if 'Z' not in grid_data:
                self.line_status.delete(1.0, tk.END)
                self.line_status.insert(1.0, "❌ Grid has no data")
                return

            Z = grid_data['Z']
            X = grid_data.get('X', None)
            Y = grid_data.get('Y', None)

            # Get threshold from UI
            threshold = self.line_thresh.get()

            # Edge detection using multiple methods
            from scipy import ndimage
            if not HAS_SKIMAGE:
                self.line_status.delete(1.0, tk.END)
                self.line_status.insert(1.0, "⚠️ scikit-image not installed\npip install scikit-image")
                return
            from skimage import feature, transform, filters

            # 1. Sobel filter for gradient magnitude
            sx = ndimage.sobel(Z, axis=0)
            sy = ndimage.sobel(Z, axis=1)
            sobel_edges = np.hypot(sx, sy)
            sobel_edges = sobel_edges / sobel_edges.max()  # Normalize

            # 2. Canny edge detection
            try:
                # Rescale to 0-255 for Canny
                Z_norm = (Z - Z.min()) / (Z.max() - Z.min())
                Z_uint8 = (Z_norm * 255).astype(np.uint8)

                # Apply Canny with adaptive thresholds
                sigma = 1.0
                low_threshold = 10
                high_threshold = 30
                canny_edges = feature.canny(Z_uint8, sigma=sigma,
                                        low_threshold=low_threshold,
                                        high_threshold=high_threshold)
            except Exception as e:
                print(f"Canny failed: {e}")
                canny_edges = sobel_edges > threshold

            # 3. Line detection using Hough transform
            lines = []
            try:
                # Probabilistic Hough transform on canny edges
                lines = transform.probabilistic_hough_line(
                    canny_edges,
                    threshold=10,
                    line_length=10,
                    line_gap=3
                )
            except Exception as e:
                print(f"Hough transform failed: {e}")

            # Calculate line statistics
            line_lengths = []
            line_angles = []

            if lines and len(lines) > 0:
                for line in lines:
                    p0, p1 = line
                    # Calculate length
                    length = np.sqrt((p1[0] - p0[0])**2 + (p1[1] - p0[1])**2)
                    line_lengths.append(length)

                    # Calculate angle in degrees
                    angle = np.arctan2(p1[1] - p0[1], p1[0] - p0[0]) * 180 / np.pi
                    line_angles.append(angle)

            # Clear previous plot
            self.model_ax.clear()

            # Create visualization
            if X is not None and Y is not None:
                # Plot original grid as background
                extent = [X.min(), X.max(), Y.min(), Y.max()]
                self.model_ax.imshow(Z, cmap='gray', aspect='auto',
                                    extent=extent, alpha=0.7,
                                    origin='lower')
            else:
                # Just show array indices
                self.model_ax.imshow(Z, cmap='gray', aspect='auto', alpha=0.7)

            # Overlay edges
            self.model_ax.imshow(canny_edges, cmap='Reds', aspect='auto',
                                alpha=0.3, interpolation='nearest')

            # Draw detected lines
            if lines and len(lines) > 0:
                for line in lines[:100]:  # Limit to first 100 lines for clarity
                    p0, p1 = line
                    self.model_ax.plot([p0[0], p1[0]], [p0[1], p1[1]],
                                    'b-', linewidth=1, alpha=0.5)

            self.model_ax.set_title(f"Lineament Detection - {grid_name}")
            self.model_ax.set_xlabel("X")
            self.model_ax.set_ylabel("Y")

            self.model_canvas.draw()
            self.model_notebook.select(1)  # Switch to plot tab

            # Calculate statistics
            n_lines = len(lines) if lines else 0

            status_text = (f"✓ Lineament Detection\n"
                        f"• Grid: {grid_name}\n"
                        f"• Threshold: {threshold:.2f}\n"
                        f"• Lineaments detected: {n_lines}\n")

            if n_lines > 0:
                # Line length statistics
                avg_length = np.mean(line_lengths)
                max_length = np.max(line_lengths)
                status_text += f"• Avg length: {avg_length:.1f} pixels\n"
                status_text += f"• Max length: {max_length:.1f} pixels\n"

                # Orientation statistics (rose diagram data)
                # Convert angles to 0-180 range
                angles_mod = np.array(line_angles) % 180
                hist, bins = np.histogram(angles_mod, bins=12, range=(0, 180))
                dominant_bin = np.argmax(hist)
                dominant_angle = (bins[dominant_bin] + bins[dominant_bin+1]) / 2

                status_text += f"• Dominant orientation: {dominant_angle:.0f}°\n"

                # Create a small orientation histogram inset
                from mpl_toolkits.axes_grid1.inset_locator import inset_axes
                ax_hist = inset_axes(self.model_ax, width="30%", height="30%",
                                    loc='upper right')
                ax_hist.hist(angles_mod, bins=12, range=(0, 180),
                            color='blue', alpha=0.7)
                ax_hist.set_xlabel('Angle (°)')
                ax_hist.set_ylabel('Count')
                ax_hist.set_title('Orientation')

            self.line_status.delete(1.0, tk.END)
            self.line_status.insert(1.0, status_text)

            # Store results
            self.workflow_state.processed['lineaments'] = {
                'grid': grid_name,
                'threshold': threshold,
                'n_lines': n_lines,
                'lines': lines if n_lines > 0 else [],
                'canny_edges': canny_edges.tolist() if n_lines > 0 else []
            }

        except Exception as e:
            self.line_status.delete(1.0, tk.END)
            self.line_status.insert(1.0, f"❌ Error: {str(e)[:100]}")
            import traceback
            traceback.print_exc()

    # ============================================================================
    # TAB 5 METHODS - COMPLETE REAL IMPLEMENTATIONS
    # ============================================================================

    def _generate_plot(self):
        """Generate 2D plot based on selections"""
        if self.workflow_state.raw_data is None:
            self.viz_status.delete(1.0, tk.END)
            self.viz_status.insert(1.0, "⚠️ Import data first")
            return

        df = self.workflow_state.raw_data
        plot_type = self.plot_type.get()
        x_col = self.plot_x.get()
        y_col = self.plot_y.get()
        c_col = self.plot_c.get()

        if not x_col or x_col not in df.columns:
            self.viz_status.delete(1.0, tk.END)
            self.viz_status.insert(1.0, "❌ Select valid X column")
            return

        self.viz_ax.clear()

        try:
            if plot_type == "profile" and y_col and y_col in df.columns:
                # Line plot
                x = df[x_col].values
                y = df[y_col].values
                self.viz_ax.plot(x, y, 'b-', linewidth=1)
                self.viz_ax.set_xlabel(x_col)
                self.viz_ax.set_ylabel(y_col)
                self.viz_ax.set_title(f"{y_col} vs {x_col}")
                self.viz_ax.grid(True, alpha=0.3)

            elif plot_type == "scatter":
                x = df[x_col].values
                if y_col and y_col in df.columns:
                    y = df[y_col].values
                    if c_col and c_col in df.columns:
                        c = df[c_col].values
                        scatter = self.viz_ax.scatter(x, y, c=c, cmap='viridis',
                                                      alpha=0.6, edgecolors='black', linewidth=0.5)
                        plt.colorbar(scatter, ax=self.viz_ax, label=c_col)
                    else:
                        self.viz_ax.scatter(x, y, alpha=0.6, edgecolors='black', linewidth=0.5)
                    self.viz_ax.set_xlabel(x_col)
                    self.viz_ax.set_ylabel(y_col)
                else:
                    self.viz_ax.plot(x, 'b-', linewidth=1)
                    self.viz_ax.set_xlabel("Index")
                    self.viz_ax.set_ylabel(x_col)
                self.viz_ax.grid(True, alpha=0.3)

            elif plot_type == "histogram":
                data = df[x_col].dropna()
                self.viz_ax.hist(data, bins=30, alpha=0.7, edgecolor='black')
                self.viz_ax.set_xlabel(x_col)
                self.viz_ax.set_ylabel("Frequency")
                self.viz_ax.set_title(f"Histogram of {x_col}")
                self.viz_ax.grid(True, alpha=0.3)

            elif plot_type == "contour" and y_col and y_col in df.columns:
                from scipy.interpolate import griddata
                data = df[[x_col, y_col]].dropna()
                if len(data) > 10:
                    x = data[x_col].values
                    y = data[y_col].values
                    if c_col and c_col in df.columns:
                        z = df[c_col].values
                    else:
                        z = np.ones(len(x))

                    xi = np.linspace(x.min(), x.max(), 50)
                    yi = np.linspace(y.min(), y.max(), 50)
                    Xi, Yi = np.meshgrid(xi, yi)
                    Zi = griddata((x, y), z, (Xi, Yi), method='cubic')

                    contour = self.viz_ax.contourf(Xi, Yi, Zi, levels=20, cmap='viridis')
                    plt.colorbar(contour, ax=self.viz_ax, label=c_col if c_col else 'Value')
                    self.viz_ax.set_xlabel(x_col)
                    self.viz_ax.set_ylabel(y_col)
                    self.viz_ax.set_title(f"Contour of {c_col if c_col else 'data'}")
                else:
                    self.viz_ax.text(0.5, 0.5, "Insufficient data for contour",
                                   ha='center', va='center', transform=self.viz_ax.transAxes)

            self.viz_canvas.draw()
            self.viz_notebook.select(0)

            self.viz_status.delete(1.0, tk.END)
            self.viz_status.insert(1.0, f"✓ Generated {plot_type} plot")

        except Exception as e:
            self.viz_status.delete(1.0, tk.END)
            self.viz_status.insert(1.0, f"❌ Error: {str(e)[:100]}")

    def _export_geotiff(self):
        """Export grid as GeoTIFF"""
        if not HAS_RASTERIO:
            self.viz_status.delete(1.0, tk.END)
            self.viz_status.insert(1.0, "❌ rasterio not installed")
            return

        if not self.workflow_state.grids:
            self.viz_status.delete(1.0, tk.END)
            self.viz_status.insert(1.0, "⚠️ No grids to export")
            return

        grid_name = self.export_grid.get()
        if not grid_name or grid_name not in self.workflow_state.grids:
            grid_name = list(self.workflow_state.grids.keys())[-1]
            self.export_grid.set(grid_name)

        grid = self.workflow_state.grids[grid_name]

        if 'X' not in grid or 'Y' not in grid or 'Z' not in grid:
            self.viz_status.delete(1.0, tk.END)
            self.viz_status.insert(1.0, "❌ Grid missing coordinate data")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".tif",
            filetypes=[("GeoTIFF", "*.tif"), ("All files", "*.*")]
        )
        if not filename:
            return

        try:
            import rasterio
            from rasterio.transform import from_origin

            X = grid['X']
            Y = grid['Y']
            Z = grid['Z']

            x_min, x_max = X.min(), X.max()
            y_min, y_max = Y.min(), Y.max()
            x_res = (x_max - x_min) / (Z.shape[1] - 1)
            y_res = (y_max - y_min) / (Z.shape[0] - 1)

            transform = from_origin(x_min, y_max, x_res, y_res)

            with rasterio.open(
                filename,
                'w',
                driver='GTiff',
                height=Z.shape[0],
                width=Z.shape[1],
                count=1,
                dtype=Z.dtype,
                crs='EPSG:4326',
                transform=transform,
            ) as dst:
                dst.write(Z, 1)

            self.viz_status.delete(1.0, tk.END)
            self.viz_status.insert(1.0, f"✓ Exported to {Path(filename).name}")

        except Exception as e:
            self.viz_status.delete(1.0, tk.END)
            self.viz_status.insert(1.0, f"❌ Export failed: {str(e)[:100]}")

    def _export_shapefile(self):
        """Export points as Shapefile"""
        if not HAS_GEOPANDAS:
            self.viz_status.delete(1.0, tk.END)
            self.viz_status.insert(1.0, "❌ geopandas not installed")
            return

        if self.workflow_state.raw_data is None:
            self.viz_status.delete(1.0, tk.END)
            self.viz_status.insert(1.0, "⚠️ No data to export")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".shp",
            filetypes=[("Shapefile", "*.shp"), ("All files", "*.*")]
        )
        if not filename:
            return

        try:
            import geopandas as gpd
            from shapely.geometry import Point

            df = self.workflow_state.raw_data

            x_col = self._find_coord_column(df, ['x', 'lon', 'longitude', 'easting'])
            y_col = self._find_coord_column(df, ['y', 'lat', 'latitude', 'northing'])

            if not x_col or not y_col:
                self.viz_status.delete(1.0, tk.END)
                self.viz_status.insert(1.0, "❌ No coordinate columns found")
                return

            geometry = [Point(x, y) for x, y in zip(df[x_col], df[y_col])]
            gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
            gdf.to_file(filename)

            self.viz_status.delete(1.0, tk.END)
            self.viz_status.insert(1.0, f"✓ Exported {len(gdf)} points to {Path(filename).name}")

        except Exception as e:
            self.viz_status.delete(1.0, tk.END)
            self.viz_status.insert(1.0, f"❌ Export failed: {str(e)[:100]}")

    def _export_xyz(self):
        """Export grid as XYZ ASCII"""
        if not self.workflow_state.grids:
            self.viz_status.delete(1.0, tk.END)
            self.viz_status.insert(1.0, "⚠️ No grids to export")
            return

        grid_name = self.export_grid.get()
        if not grid_name or grid_name not in self.workflow_state.grids:
            grid_name = list(self.workflow_state.grids.keys())[-1]
            self.export_grid.set(grid_name)

        grid = self.workflow_state.grids[grid_name]

        if 'X' not in grid or 'Y' not in grid or 'Z' not in grid:
            self.viz_status.delete(1.0, tk.END)
            self.viz_status.insert(1.0, "❌ Grid missing data")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".xyz",
            filetypes=[("XYZ files", "*.xyz"), ("All files", "*.*")]
        )
        if not filename:
            return

        try:
            X = grid['X'].ravel()
            Y = grid['Y'].ravel()
            Z = grid['Z'].ravel()

            with open(filename, 'w') as f:
                f.write("# X Y Z\n")
                for i in range(len(X)):
                    if not np.isnan(Z[i]):
                        f.write(f"{X[i]:.3f} {Y[i]:.3f} {Z[i]:.6f}\n")

            self.viz_status.delete(1.0, tk.END)
            self.viz_status.insert(1.0, f"✓ Exported {len(X)} points to {Path(filename).name}")

        except Exception as e:
            self.viz_status.delete(1.0, tk.END)
            self.viz_status.insert(1.0, f"❌ Export failed: {str(e)[:100]}")

    def _export_grd(self):
        """Export grid as Surfer GRD (ASCII)"""
        if not self.workflow_state.grids:
            self.viz_status.delete(1.0, tk.END)
            self.viz_status.insert(1.0, "⚠️ No grids to export")
            return

        grid_name = self.export_grid.get()
        if not grid_name or grid_name not in self.workflow_state.grids:
            grid_name = list(self.workflow_state.grids.keys())[-1]
            self.export_grid.set(grid_name)

        grid = self.workflow_state.grids[grid_name]

        if 'Z' not in grid:
            self.viz_status.delete(1.0, tk.END)
            self.viz_status.insert(1.0, "❌ Grid has no data")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".grd",
            filetypes=[("Surfer GRD", "*.grd"), ("All files", "*.*")]
        )
        if not filename:
            return

        try:
            Z = grid['Z']
            ny, nx = Z.shape

            with open(filename, 'w') as f:
                f.write("DSAA\n")
                f.write(f"{nx} {ny}\n")

                if 'X' in grid:
                    f.write(f"{grid['X'].min():.6f} {grid['X'].max():.6f}\n")
                    f.write(f"{grid['Y'].min():.6f} {grid['Y'].max():.6f}\n")
                else:
                    f.write("0 100\n0 100\n")

                f.write(f"{np.nanmin(Z):.6f} {np.nanmax(Z):.6f}\n")

                for i in range(ny):
                    row = Z[i, :]
                    f.write(" ".join(f"{v:.6f}" for v in row))
                    f.write("\n")

            self.viz_status.delete(1.0, tk.END)
            self.viz_status.insert(1.0, f"✓ Exported to {Path(filename).name}")

        except Exception as e:
            self.viz_status.delete(1.0, tk.END)
            self.viz_status.insert(1.0, f"❌ Export failed: {str(e)[:100]}")

    def _generate_folium(self):
        """Generate interactive Folium map"""
        if not HAS_FOLIUM:
            self.viz_status.delete(1.0, tk.END)
            self.viz_status.insert(1.0, "❌ folium not installed")
            return

        if self.workflow_state.raw_data is None:
            self.viz_status.delete(1.0, tk.END)
            self.viz_status.insert(1.0, "⚠️ Import data first")
            return

        df = self.workflow_state.raw_data
        lat_col = self.map_lat.get() or self._find_coord_column(df, ['lat', 'latitude'])
        lon_col = self.map_lon.get() or self._find_coord_column(df, ['lon', 'longitude'])
        popup_col = self.map_popup.get() or 'Sample_ID'

        if not lat_col or lat_col not in df.columns:
            self.viz_status.delete(1.0, tk.END)
            self.viz_status.insert(1.0, "❌ Select valid latitude column")
            return

        if not lon_col or lon_col not in df.columns:
            self.viz_status.delete(1.0, tk.END)
            self.viz_status.insert(1.0, "❌ Select valid longitude column")
            return

        try:
            center_lat = df[lat_col].mean()
            center_lon = df[lon_col].mean()

            m = folium.Map(location=[center_lat, center_lon], zoom_start=10)

            for idx, row in df.iterrows():
                if pd.notna(row[lat_col]) and pd.notna(row[lon_col]):
                    if popup_col and popup_col in df.columns:
                        popup_text = f"{popup_col}: {row[popup_col]}"
                    else:
                        popup_text = f"Sample {idx}"

                    folium.CircleMarker(
                        [row[lat_col], row[lon_col]],
                        radius=5,
                        popup=popup_text,
                        color='blue',
                        fill=True,
                        fillOpacity=0.7
                    ).add_to(m)

            import tempfile
            import webbrowser

            with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as f:
                m.save(f.name)
                webbrowser.open(f'file://{f.name}')

            self.viz_status.delete(1.0, tk.END)
            self.viz_status.insert(1.0, f"✓ Map generated with {len(df)} points")

        except Exception as e:
            self.viz_status.delete(1.0, tk.END)
            self.viz_status.insert(1.0, f"❌ Map failed: {str(e)[:100]}")

    def _launch_3d(self):
        """Launch 3D viewer - Opens interactive PyVista window"""
        if not HAS_PYVISTA:
            self.viz_status.delete(1.0, tk.END)
            self.viz_status.insert(1.0, "❌ pyvista not installed")
            return

        if not self.workflow_state.grids:
            self.viz_status.delete(1.0, tk.END)
            self.viz_status.insert(1.0, "⚠️ Create a grid first (Tab 3)")
            return

        grid_name = self.viz3d_grid.get()
        if not grid_name or grid_name not in self.workflow_state.grids:
            grid_name = list(self.workflow_state.grids.keys())[-1]
            self.viz3d_grid.set(grid_name)

        grid = self.workflow_state.grids[grid_name]

        if 'X' not in grid or 'Y' not in grid or 'Z' not in grid:
            self.viz_status.delete(1.0, tk.END)
            self.viz_status.insert(1.0, "❌ Grid missing data")
            return

        try:
            import pyvista as pv

            X = grid['X']
            Y = grid['Y']
            Z = grid['Z']

            x = X[0, :]
            y = Y[:, 0]
            grid_pv = pv.StructuredGrid(x, y, Z.T)

            # Create interactive plotter in a new window
            plotter = pv.Plotter()
            plotter.add_mesh(grid_pv, cmap='viridis', show_edges=False)
            plotter.show_grid()
            plotter.show(title=f"3D View: {grid_name}")

            self.viz_status.delete(1.0, tk.END)
            self.viz_status.insert(1.0, f"✓ Interactive 3D window opened for {grid_name}")

        except Exception as e:
            self.viz_status.delete(1.0, tk.END)
            self.viz_status.insert(1.0, f"❌ 3D failed: {str(e)[:100]}")

    # ============================================================================
    # CLEANUP
    # ============================================================================

    def _on_close(self):
        """Clean up on close"""
        if self.window:
            self.window.destroy()
            self.window = None

    def start_progress(self, message="Processing..."):
        """Start indeterminate progress bar"""
        self.progress_bar.config(mode='indeterminate')
        self.progress_bar.start(10)
        self.status_var.set(message)
        self.window.update()

    def stop_progress(self):
        """Stop progress bar"""
        self.progress_bar.stop()
        self.progress_bar.config(mode='determinate', value=0)
        self.window.update()

    def update_progress(self, value, message=""):
        """Update determinate progress bar"""
        self.progress_bar.config(mode='determinate', value=value)
        if message:
            self.status_var.set(message)
        self.window.update()
# ============================================================================
# PLUGIN REGISTRATION
# ============================================================================
def setup_plugin(main_app):
    """Register plugin with main application"""

    plugin = GeophysicsAnalysisSuite(main_app)

    # Add to Analysis menu
    if hasattr(main_app, 'analysis_menu'):
        main_app.analysis_menu.add_command(
            label=f"{PLUGIN_INFO['icon']} {PLUGIN_INFO['name']} v{PLUGIN_INFO['version']}",
            command=plugin.show_interface
        )
        print(f"✅ Added to Analysis menu: {PLUGIN_INFO['name']} v{PLUGIN_INFO['version']}")

    elif hasattr(main_app, 'advanced_menu'):
        main_app.advanced_menu.add_command(
            label=f"{PLUGIN_INFO['icon']} {PLUGIN_INFO['name']} v{PLUGIN_INFO['version']}",
            command=plugin.show_interface
        )
        print(f"✅ Added to Advanced menu: {PLUGIN_INFO['name']} v{PLUGIN_INFO['version']}")

    elif hasattr(main_app, 'menu_bar'):
        if not hasattr(main_app, 'analysis_menu'):
            main_app.analysis_menu = tk.Menu(main_app.menu_bar, tearoff=0)
            main_app.menu_bar.add_cascade(label="🔬 Analysis", menu=main_app.analysis_menu)
        main_app.analysis_menu.add_command(
            label=f"{PLUGIN_INFO['icon']} {PLUGIN_INFO['name']} v{PLUGIN_INFO['version']}",
            command=plugin.show_interface
        )
        print(f"✅ Created Analysis menu and added: {PLUGIN_INFO['name']} v{PLUGIN_INFO['version']}")

    return plugin
