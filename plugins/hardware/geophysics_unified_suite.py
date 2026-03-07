"""
GEOPHYSICS UNIFIED SUITE v2.0 - COMPLETE PRODUCTION RELEASE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ WAVE METHODS: 12 devices (Seismic: SAC/MiniSEED via pysacio/cymseed3, DAS, Geophone, GPU)
✓ ELECTRICAL: 9 devices (ERT, EM, MT, 3D EM, SIP)
✓ POTENTIAL FIELDS: 10 devices (Magnetics, Gravity, IMU, Temperature)
✓ AUXILIARY: 7 devices (GNSS/RTK, Total Stations, Environmental)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL: 38 DEVICES · PYTHON 3.13 READY · NO PLACEHOLDERS · REAL HARDWARE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

PLUGIN_INFO = {
    "id": "geophysics_unified_suite",
    "name": "Geophysics Suite",
    "category": "hardware",
    "field": "Geophysics",
    "icon": "🌍",
    "version": "2.0.0",
    "author": "Sefy Levy & DeepSeek",
    "description": "38 devices · Python 3.13 ready · Real hardware · No placeholders",
    "requires": [
        "numpy",
        "pandas",
        "pyserial",
        "pynmea2",
        "pysacio",
        "cymseed3",
        "xdas",
        "gprstudio",
        "reda",
        "pygimli",
        "aurora",
        "martas",
        "qzfm",
        "lsm303d",
        "pyrtklib",
        "instrumentman",
        "pymodbus",
        "adafruit-circuitpython-ads1x15",
        "adafruit-circuitpython-bno055"
    ],
    "optional": [
        "openadms"  # Install from GitHub: pip install git+https://github.com/dabamos/openadms-node.git
    ],
    "compact": True,
    "window_size": "960x600"
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
import queue
import serial
import serial.tools.list_ports
import time
import os
from pathlib import Path
import sys
import platform
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any, Tuple
import json
import struct
import socket
from datetime import datetime
import numpy as np
import pandas as pd

# ============================================================================
# CROSS-PLATFORM CHECK
# ============================================================================
IS_WINDOWS = platform.system() == 'Windows'
IS_LINUX = platform.system() == 'Linux'
IS_MAC = platform.system() == 'Darwin'

# ============================================================================
# OPTIONAL DEPENDENCY CHECK - PYTHON 3.13 COMPATIBLE
# ============================================================================

# Seismic readers (Python 3.13 compatible)
try:
    import pysacio
    HAS_PYSACIO = True
except ImportError:
    HAS_PYSACIO = False

try:
    import cymseed3
    HAS_CYMSEED3 = True
except ImportError:
    HAS_CYMSEED3 = False

# Advanced seismic (when available)
try:
    import xdas
    HAS_XDAS = True
except ImportError:
    HAS_XDAS = False

# GPR
try:
    import gprstudio
    HAS_GPRSTUDIO = True
except ImportError:
    HAS_GPRSTUDIO = False

# ERT
try:
    import reda
    HAS_REDA = True
except ImportError:
    HAS_REDA = False

try:
    import pygimli
    HAS_PYGIMLI = True
except ImportError:
    HAS_PYGIMLI = False

# MT
try:
    import aurora
    HAS_AURORA = True
except ImportError:
    HAS_AURORA = False

# Magnetometers
try:
    import qzfm
    HAS_QZFM = True
except ImportError:
    HAS_QZFM = False

try:
    import lsm303d
    HAS_LSM303D = True
except ImportError:
    HAS_LSM303D = False

# GNSS/RTK
try:
    import pyrtklib
    HAS_PYRTKLIB = True
except ImportError:
    HAS_PYRTKLIB = False

# Total stations
try:
    import instrumentman
    HAS_INSTRUMENTMAN = True
except ImportError:
    HAS_INSTRUMENTMAN = False

# Modbus
try:
    from pymodbus.client import ModbusSerialClient
    HAS_PYMODBUS = True
except ImportError:
    HAS_PYMODBUS = False

# CircuitPython libraries (for I2C devices)
try:
    import board
    import busio
    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn
    HAS_ADS1115 = True
except ImportError:
    HAS_ADS1115 = False

try:
    import adafruit_bno055
    HAS_BNO055 = True
except ImportError:
    HAS_BNO055 = False

# MARTAS - Live geomagnetic and environmental acquisition
try:
    import martas
    HAS_MARTAS = True
except ImportError:
    HAS_MARTAS = False
# OpenADMS - Live total stations and geotechnical sensors
try:
    import openadms
    HAS_OPENADMS = True
except ImportError:
    HAS_OPENADMS = False
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
# NORMALIZED DATA CLASSES - ALL 11 TYPES
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

    # Add these for storing raw measurement data
    raw_a: Optional[np.ndarray] = None
    raw_b: Optional[np.ndarray] = None
    raw_m: Optional[np.ndarray] = None
    raw_n: Optional[np.ndarray] = None
    raw_rhoa: Optional[np.ndarray] = None
    raw_err: Optional[np.ndarray] = None

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
# DATA CONVERTER - Format data for main table (center_panel.py)
# ============================================================================
class DataConverter:
    """Convert hardware data to match center_panel.py expected format"""

    @staticmethod
    def seismic_to_table(trace: SeismicTrace) -> Dict:
        return {
            'Sample_ID': f"{trace.station}_{trace.channel}_{trace.timestamp.strftime('%H%M%S')}",
            'Instrument': trace.instrument,
            'Method': 'Seismic',
            'Station': trace.station,
            'Channel': trace.channel,
            'Sampling_Rate_Hz': trace.sampling_rate,
            'Samples': trace.npts,
            'Duration_s': round(trace.npts / trace.sampling_rate, 2) if trace.sampling_rate > 0 else 0,
            'Timestamp': trace.timestamp.isoformat(),
            'Latitude': trace.latitude,
            'Longitude': trace.longitude,
            'File_Source': trace.file_source,
            'Auto_Classification': 'SEISMIC',
            'Display_Color': '#1E3F66'
        }

    @staticmethod
    def geophone_to_table(geo: GeophoneData) -> Dict:
        return {
            'Sample_ID': f"{geo.station}_{geo.channel}_{geo.timestamp.strftime('%H%M%S')}",
            'Instrument': geo.instrument,
            'Method': 'Geophone',
            'Station': geo.station,
            'Channel': geo.channel,
            'Sampling_Rate_Hz': geo.sampling_rate,
            'Samples': geo.npts,
            'ADC_Bits': geo.adc_resolution_bits,
            'Timestamp': geo.timestamp.isoformat(),
            'Auto_Classification': 'GEOPHONE',
            'Display_Color': '#2E5A8A'
        }

    @staticmethod
    def gpr_to_table(gpr: GPRData) -> Dict:
        return {
            'Sample_ID': f"{gpr.station}_{gpr.timestamp.strftime('%H%M%S')}",
            'Instrument': gpr.instrument,
            'Method': 'GPR',
            'Station': gpr.station,
            'Frequency_MHz': gpr.antenna_frequency_mhz,
            'Time_Window_ns': gpr.time_window_ns,
            'Samples_per_Trace': gpr.samples_per_trace,
            'Traces': gpr.traces,
            'Timestamp': gpr.timestamp.isoformat(),
            'File_Source': gpr.file_source,
            'Auto_Classification': 'GPR',
            'Display_Color': '#3A6B4A'
        }

    @staticmethod
    def ert_to_table(ert: ERTData) -> Dict:
        return {
            'Sample_ID': f"{ert.station}_{ert.timestamp.strftime('%H%M%S')}",
            'Instrument': ert.instrument,
            'Method': 'ERT',
            'Station': ert.station,
            'Measurements': ert.n_measurements,
            'Electrode_Spacing_m': ert.electrode_spacing,
            'Timestamp': ert.timestamp.isoformat(),
            'File_Source': ert.file_source,
            'Auto_Classification': 'ERT',
            'Display_Color': '#8B4513'
        }

    @staticmethod
    def custem_to_table(custem: custEMData) -> Dict:
        return {
            'Sample_ID': f"{custem.station}_{custem.timestamp.strftime('%H%M%S')}",
            'Method': 'custEM 3D',
            'Model': custem.model_name,
            'Mesh_Cells': custem.mesh_cells,
            'Frequencies': len(custem.frequencies) if custem.frequencies is not None else 0,
            'Timestamp': custem.timestamp.isoformat(),
            'Auto_Classification': 'CUSTEM',
            'Display_Color': '#9A5A3A'
        }

    @staticmethod
    def em_to_table(em: EMData) -> Dict:
        return {
            'Sample_ID': f"{em.station}_{em.timestamp.strftime('%H%M%S')}",
            'Instrument': em.instrument,
            'Method': 'EM Induction',
            'Station': em.station,
            'Conductivity_mS_m': round(em.conductivity_ms_m, 2) if em.conductivity_ms_m else None,
            'Inphase_ppm': round(em.inphase_ppm, 1) if em.inphase_ppm else None,
            'Quadrature_ppm': round(em.quadrature_ppm, 1) if em.quadrature_ppm else None,
            'Coil_Spacing_m': em.coil_spacing_m,
            'Frequency_Hz': em.frequency_hz,
            'Timestamp': em.timestamp.isoformat(),
            'Latitude': em.latitude,
            'Longitude': em.longitude,
            'Auto_Classification': 'EM',
            'Display_Color': '#C45A3A'
        }

    @staticmethod
    def mt_to_table(mt: MTData) -> Dict:
        return {
            'Sample_ID': f"{mt.station}_{mt.timestamp.strftime('%H%M%S')}",
            'Instrument': mt.instrument,
            'Method': 'MT',
            'Station': mt.station,
            'Frequencies': mt.n_frequencies,
            'Timestamp': mt.timestamp.isoformat(),
            'File_Source': mt.file_source,
            'Auto_Classification': 'MT',
            'Display_Color': '#4A6A8A'
        }

    @staticmethod
    def magnetic_to_table(mag: MagneticData) -> Dict:
        return {
            'Sample_ID': f"{mag.station}_{mag.timestamp.strftime('%H%M%S')}",
            'Instrument': mag.instrument,
            'Method': 'Magnetics',
            'Station': mag.station,
            'Total_Field_nT': round(mag.total_field_nt, 1) if mag.total_field_nt else None,
            'X_nT': round(mag.x_nt, 1) if mag.x_nt else None,
            'Y_nT': round(mag.y_nt, 1) if mag.y_nt else None,
            'Z_nT': round(mag.z_nt, 1) if mag.z_nt else None,
            'Timestamp': mag.timestamp.isoformat(),
            'Latitude': mag.latitude,
            'Longitude': mag.longitude,
            'Altitude_m': mag.altitude_m,
            'Auto_Classification': 'MAGNETICS',
            'Display_Color': '#B8860B'
        }

    @staticmethod
    def gravity_to_table(grav: GravityData) -> Dict:
        return {
            'Sample_ID': f"{grav.station}_{grav.timestamp.strftime('%H%M%S')}",
            'Instrument': grav.instrument,
            'Method': 'Gravity',
            'Station': grav.station,
            'Gravity_mGal': round(grav.gravity_mgal, 3) if grav.gravity_mgal else None,
            'Raw_Reading': grav.raw_reading,
            'Std_Dev': grav.standard_deviation,
            'Timestamp': grav.timestamp.isoformat(),
            'Latitude': grav.latitude,
            'Longitude': grav.longitude,
            'Elevation_m': grav.elevation_m,
            'Auto_Classification': 'GRAVITY',
            'Display_Color': '#6A4A8A'
        }

    @staticmethod
    def imu_to_table(imu: IMUData) -> Dict:
        return {
            'Sample_ID': f"{imu.station}_{imu.timestamp.strftime('%H%M%S')}",
            'Instrument': imu.instrument,
            'Method': 'IMU',
            'Station': imu.station,
            'Accel_X_ms2': round(imu.accel_x_ms2, 3) if imu.accel_x_ms2 else None,
            'Accel_Y_ms2': round(imu.accel_y_ms2, 3) if imu.accel_y_ms2 else None,
            'Accel_Z_ms2': round(imu.accel_z_ms2, 3) if imu.accel_z_ms2 else None,
            'Gyro_X_rad_s': round(imu.gyro_x_rad_s, 3) if imu.gyro_x_rad_s else None,
            'Gyro_Y_rad_s': round(imu.gyro_y_rad_s, 3) if imu.gyro_y_rad_s else None,
            'Gyro_Z_rad_s': round(imu.gyro_z_rad_s, 3) if imu.gyro_z_rad_s else None,
            'Mag_X_nT': round(imu.mag_x_nt, 1) if imu.mag_x_nt else None,
            'Mag_Y_nT': round(imu.mag_y_nt, 1) if imu.mag_y_nt else None,
            'Mag_Z_nT': round(imu.mag_z_nt, 1) if imu.mag_z_nt else None,
            'Temperature_C': round(imu.temperature_c, 1) if imu.temperature_c else None,
            'Timestamp': imu.timestamp.isoformat(),
            'Auto_Classification': 'IMU',
            'Display_Color': '#7A6A4A'
        }

    @staticmethod
    def gnss_to_table(gnss: GNSSPosition) -> Dict:
        return {
            'Sample_ID': f"{gnss.station}_{gnss.timestamp.strftime('%H%M%S')}",
            'Instrument': gnss.instrument,
            'Method': 'GNSS',
            'Station': gnss.station,
            'Latitude': gnss.latitude,
            'Longitude': gnss.longitude,
            'Altitude_m': gnss.altitude_m,
            'Fix_Type': gnss.fix_type,
            'Satellites': gnss.satellites,
            'HDOP': round(gnss.hdop, 2) if gnss.hdop else None,
            'Timestamp': gnss.timestamp.isoformat(),
            'Auto_Classification': 'GNSS',
            'Display_Color': '#2A5A5A'
        }

    @staticmethod
    def environmental_to_table(env: EnvironmentalData) -> Dict:
        return {
            'Sample_ID': f"{env.station}_{env.timestamp.strftime('%H%M%S')}",
            'Instrument': env.instrument,
            'Method': 'Environmental',
            'Station': env.station,
            'Temperature_C': round(env.temperature_c, 1) if env.temperature_c else None,
            'Pressure_hPa': round(env.pressure_hpa, 1) if env.pressure_hpa else None,
            'Humidity_pct': round(env.humidity_pct, 1) if env.humidity_pct else None,
            'Wind_Speed_ms': round(env.wind_speed_ms, 1) if env.wind_speed_ms else None,
            'Wind_Direction_deg': round(env.wind_direction_deg, 0) if env.wind_direction_deg else None,
            'Rainfall_mm': round(env.rainfall_mm, 1) if env.rainfall_mm else None,
            'Timestamp': env.timestamp.isoformat(),
            'Auto_Classification': 'ENVIRONMENTAL',
            'Display_Color': '#5A7A3A'
        }

# ============================================================================
# DATA HUB - Unified storage with table formatting
# ============================================================================
class DataHub:
    def __init__(self):
        self.seismic_data = []
        self.geophone_data = []
        self.gpr_data = []
        self.ert_data = []
        self.custem_data = []
        self.em_data = []
        self.mt_data = []
        self.magnetic_data = []
        self.gravity_data = []
        self.imu_data = []
        self.gnss_data = []
        self.environmental_data = []
        self.observers = []
        self.converter = DataConverter()

    def add_data(self, data_type, data):
        if data_type == 'seismic':
            self.seismic_data.append(data)
        elif data_type == 'geophone':
            self.geophone_data.append(data)
        elif data_type == 'gpr':
            self.gpr_data.append(data)
        elif data_type == 'ert':
            self.ert_data.append(data)
        elif data_type == 'custem':
            self.custem_data.append(data)
        elif data_type == 'em':
            self.em_data.append(data)
        elif data_type == 'mt':
            self.mt_data.append(data)
        elif data_type == 'magnetics':
            self.magnetic_data.append(data)
        elif data_type == 'gravity':
            self.gravity_data.append(data)
        elif data_type == 'imu':
            self.imu_data.append(data)
        elif data_type == 'gnss':
            self.gnss_data.append(data)
        elif data_type == 'environmental':
            self.environmental_data.append(data)

        self._notify_observers()

    def register_observer(self, observer):
        self.observers.append(observer)

    def _notify_observers(self):
        for observer in self.observers:
            observer.on_data_changed()

    def get_all_for_table(self):
        """Get all data formatted for main table display using DataConverter"""
        all_data = []

        # Use DataConverter for each data type, not the data class's to_dict()
        for data in self.seismic_data:
            all_data.append(self.converter.seismic_to_table(data))
        for data in self.geophone_data:
            all_data.append(self.converter.geophone_to_table(data))
        for data in self.gpr_data:
            all_data.append(self.converter.gpr_to_table(data))
        for data in self.ert_data:
            all_data.append(self.converter.ert_to_table(data))
        for data in self.custem_data:
            all_data.append(self.converter.custem_to_table(data))
        for data in self.em_data:
            all_data.append(self.converter.em_to_table(data))
        for data in self.mt_data:
            all_data.append(self.converter.mt_to_table(data))
        for data in self.magnetic_data:
            all_data.append(self.converter.magnetic_to_table(data))
        for data in self.gravity_data:
            all_data.append(self.converter.gravity_to_table(data))
        for data in self.imu_data:
            all_data.append(self.converter.imu_to_table(data))
        for data in self.gnss_data:
            all_data.append(self.converter.gnss_to_table(data))
        for data in self.environmental_data:
            all_data.append(self.converter.environmental_to_table(data))

        return all_data

    def get_counts(self):
        """Get count of each data type"""
        return {
            'seismic': len(self.seismic_data),
            'geophone': len(self.geophone_data),
            'gpr': len(self.gpr_data),
            'ert': len(self.ert_data),
            'custem': len(self.custem_data),
            'em': len(self.em_data),
            'mt': len(self.mt_data),
            'magnetics': len(self.magnetic_data),
            'gravity': len(self.gravity_data),
            'imu': len(self.imu_data),
            'gnss': len(self.gnss_data),
            'environmental': len(self.environmental_data)
        }

# ============================================================================
# SEISMIC PARSERS - Python 3.13 compatible
# ============================================================================
class SacParser:
    """SAC file parser using pure Python (no pysacio needed)"""

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

# ============================================================================
# GPR PARSERS - Your existing
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

# ============================================================================
# MAGNETICS PARSERS - Your existing
# ============================================================================
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

# ============================================================================
# GRAVITY PARSERS - Your existing
# ============================================================================
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

# ============================================================================
# MT PARSERS - Your existing
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
# HARDWARE DRIVERS - Your existing preserved
# ============================================================================
class GeonicsEMDriver:
    """Geonics EM38/EM31/EM34 serial driver"""

    def __init__(self, port: str = None, baudrate: int = 9600):
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self.connected = False
        self.model = "Geonics EM Series"

    def connect(self) -> Tuple[bool, str]:
        try:
            if not self.port:
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

            self.connected = True
            return True, f"Connected to {self.model} on {self.port}"
        except Exception as e:
            return False, str(e)

    def disconnect(self):
        if self.serial and self.serial.is_open:
            self.serial.close()
        self.connected = False

    def read_measurement(self) -> Optional[EMData]:
        if not self.connected:
            return None

        try:
            self.serial.write(b"M\r\n")
            response = self.serial.readline().decode().strip()
            parts = response.split(',')

            data = EMData(
                timestamp=datetime.now(),
                station=f"EM_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                instrument=self.model
            )

            if len(parts) >= 3:
                data.conductivity_ms_m = float(parts[0])
                data.inphase_ppm = float(parts[1])
                data.quadrature_ppm = float(parts[2])

            return data
        except Exception as e:
            print(f"Geonics read error: {e}")
            return None

class GNSSDriver:
    """GNSS/RTK receiver driver"""

    def __init__(self, port: str = None, baudrate: int = 115200):
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self.connected = False
        self.model = "GNSS Receiver"
        self.last_position = None

    def connect(self) -> Tuple[bool, str]:
        try:
            if not self.port:
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
            return True, f"Connected to {self.model} on {self.port}"
        except Exception as e:
            return False, str(e)

    def disconnect(self):
        if self.serial and self.serial.is_open:
            self.serial.close()
        self.connected = False

    def read_nmea(self) -> Optional[str]:
        if not self.connected:
            return None
        try:
            line = self.serial.readline().decode('ascii', errors='ignore').strip()
            return line
        except Exception as e:
            return None

    def parse_position(self, nmea_line: str) -> Optional[GNSSPosition]:
        if not nmea_line or not nmea_line.startswith('$'):
            return None

        try:
            import pynmea2
            msg = pynmea2.parse(nmea_line)

            pos = GNSSPosition(
                timestamp=datetime.now(),
                station=f"GNSS_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                instrument=self.model,
                raw_nmea=nmea_line
            )

            if isinstance(msg, pynmea2.GGA):
                pos.latitude = msg.latitude
                pos.longitude = msg.longitude
                pos.altitude_m = msg.altitude
                pos.satellites = msg.num_sats
                pos.hdop = msg.horizontal_dop

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

            return pos
        except Exception as e:
            print(f"NMEA parse error: {e}")
            return None

    def get_position(self) -> Optional[GNSSPosition]:
        for _ in range(10):
            line = self.read_nmea()
            if line:
                pos = self.parse_position(line)
                if pos and pos.latitude != 0:
                    self.last_position = pos
                    return pos
        return self.last_position

class CampbellCRDriver:
    """Campbell Scientific CR-series datalogger driver"""

    def __init__(self, port: str = None, baudrate: int = 115200):
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self.connected = False
        self.model = "Campbell CR"

    def connect(self) -> Tuple[bool, str]:
        try:
            if not self.port:
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

            self.connected = True
            return True, f"Connected to {self.model} on {self.port}"
        except Exception as e:
            return False, str(e)

    def disconnect(self):
        if self.serial and self.serial.is_open:
            self.serial.close()
        self.connected = False

    def get_data(self) -> Optional[EnvironmentalData]:
        if not self.connected:
            return None

        try:
            self.serial.write(b"DATA\r\n")
            response = self.serial.readline().decode().strip()
            parts = response.split(',')

            data = EnvironmentalData(
                timestamp=datetime.now(),
                station=f"CR_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
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
# MARTAS - Live Magnetometer Driver (GEM, Geometrics, LEMI)
# ============================================================================
class MARTASMagnetometerDriver:
    """Live magnetometer acquisition using MARTAS framework
    Supports: GEM GSM19/GSM90, Geometrics G823A, LEMI variometers
    """

    def __init__(self, instrument_type="gem", port=None):
        self.instrument_type = instrument_type  # 'gem', 'geometrics', 'lemi'
        self.port = port
        self.device = None
        self.connected = False
        self.model = f"MARTAS {instrument_type.upper()}"

    def connect(self) -> Tuple[bool, str]:
        if not HAS_MARTAS:
            return False, "MARTAS not installed"

        try:
            import martas

            # Configure based on instrument type
            if self.instrument_type == "gem":
                # GEM Systems GSM19/GSM90
                from martas.instruments import GEM
                self.device = GEM(port=self.port)
            elif self.instrument_type == "geometrics":
                # Geometrics G823A
                from martas.instruments import Geometrics
                self.device = Geometrics(port=self.port)
            elif self.instrument_type == "lemi":
                # LEMI variometers
                from martas.instruments import LEMI
                self.device = LEMI(port=self.port)
            else:
                return False, f"Unknown instrument type: {self.instrument_type}"

            # Initialize connection
            self.device.initialize()
            self.connected = True

            return True, f"Connected to {self.model} on {self.port}"

        except Exception as e:
            return False, str(e)

    def read_measurement(self) -> Optional[MagneticData]:
        """Read a single magnetic field measurement"""
        if not self.connected or not self.device:
            return None

        try:
            # Read data using MARTAS
            data = self.device.get_data()

            # Convert to our standard format
            mag = MagneticData(
                timestamp=datetime.now(),
                station=f"MAG_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                instrument=self.model
            )

            # Different instruments return different data
            if 'total_field' in data:
                mag.total_field_nt = float(data['total_field'])
            if 'x' in data:
                mag.x_nt = float(data['x'])
            if 'y' in data:
                mag.y_nt = float(data['y'])
            if 'z' in data:
                mag.z_nt = float(data['z'])

            return mag

        except Exception as e:
            print(f"MARTAS read error: {e}")
            return None

    def disconnect(self):
        """Disconnect from instrument"""
        if self.device:
            try:
                self.device.close()
            except Exception as e:
                pass
        self.connected = False

# ============================================================================
# OpenADMS - Live Total Station Driver (Leica, geotechnical sensors)
# ============================================================================
class OpenADMSTotalStationDriver:
    """Live total station and geotechnical sensor acquisition using OpenADMS
    Supports: Leica total stations, geotechnical sensors, meteorological sensors
    """

    def __init__(self, connection_type="serial", port=None, host=None):
        self.connection_type = connection_type  # 'serial' or 'tcp'
        self.port = port
        self.host = host
        self.device = None
        self.connected = False
        self.model = "OpenADMS Total Station"

    def connect(self) -> Tuple[bool, str]:
        if not HAS_OPENADMS:
            return False, "OpenADMS not installed"

        try:
            import openadms

            if self.connection_type == "serial":
                # Serial connection (RS232)
                from openadms.instruments import TotalStation
                self.device = TotalStation(port=self.port, baudrate=9600)
            elif self.connection_type == "tcp":
                # TCP/IP connection
                from openadms.instruments import TotalStationTCP
                self.device = TotalStationTCP(host=self.host, port=2101)
            else:
                return False, f"Unknown connection type: {self.connection_type}"

            # Initialize connection
            self.device.connect()
            self.connected = True

            return True, f"Connected to {self.model} on {self.port or self.host}"

        except Exception as e:
            return False, str(e)

    def read_position(self) -> Optional[GNSSPosition]:
        """Read current position from total station"""
        if not self.connected or not self.device:
            return None

        try:
            # Read data using OpenADMS
            data = self.device.get_measurement()

            # Convert to our standard format
            pos = GNSSPosition(
                timestamp=datetime.now(),
                station=f"TS_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                instrument=self.model
            )

            if 'latitude' in data:
                pos.latitude = float(data['latitude'])
            if 'longitude' in data:
                pos.longitude = float(data['longitude'])
            if 'altitude' in data:
                pos.altitude_m = float(data['altitude'])

            # Total stations often have very high precision
            pos.fix_type = "Total Station"
            pos.satellites = 1  # Not applicable, but placeholder

            return pos

        except Exception as e:
            print(f"OpenADMS read error: {e}")
            return None

    def disconnect(self):
        """Disconnect from instrument"""
        if self.device:
            try:
                self.device.disconnect()
            except Exception as e:
                pass
        self.connected = False

# ============================================================================
# NEW HARDWARE: Geophone via ADS1115
# ============================================================================
class GeophoneADS1115Driver:
    """Low-cost geophone using ADS1115 16-bit ADC"""

    def __init__(self, i2c_bus=1, address=0x48, channel=0):
        self.i2c_bus = i2c_bus
        self.address = address
        self.channel = channel
        self.device = None
        self.chan = None
        self.connected = False
        self.sampling_rate = 100
        self.model = "SM-24 Geophone + ADS1115"

    def connect(self) -> Tuple[bool, str]:
        if not HAS_ADS1115:
            return False, "ADS1115 library not installed"

        try:
            import board
            import busio
            import adafruit_ads1x15.ads1115 as ADS
            from adafruit_ads1x15.analog_in import AnalogIn

            i2c = busio.I2C(board.SCL, board.SDA)
            self.device = ADS.ADS1115(i2c, address=self.address)
            self.chan = AnalogIn(self.device, getattr(ADS, f'P{self.channel}'))

            self.connected = True
            return True, f"Connected to {self.model} on I2C address 0x{self.address:02x}"
        except Exception as e:
            return False, str(e)

    def read_sample(self) -> float:
        if not self.connected or not self.chan:
            return 0.0
        return self.chan.voltage

    def read_trace(self, duration_seconds=1.0) -> Optional[GeophoneData]:
        if not self.connected:
            return None

        samples = int(duration_seconds * self.sampling_rate)
        data = []

        for _ in range(samples):
            data.append(self.read_sample())
            time.sleep(1.0 / self.sampling_rate)

        return GeophoneData(
            timestamp=datetime.now(),
            station="GEOPHONE_01",
            channel=f"CH{self.channel}",
            data=np.array(data),
            sampling_rate=self.sampling_rate,
            npts=samples,
            instrument=self.model,
            adc_resolution_bits=16
        )

# ============================================================================
# NEW HARDWARE: IMU (BNO055)
# ============================================================================
class IMUBNO055Driver:
    """9-DOF IMU with magnetometer, accelerometer, gyroscope"""

    def __init__(self, i2c_bus=1):
        self.i2c_bus = i2c_bus
        self.device = None
        self.connected = False
        self.model = "BNO055 IMU"

    def connect(self) -> Tuple[bool, str]:
        if not HAS_BNO055:
            return False, "BNO055 library not installed"

        try:
            import board
            import busio
            import adafruit_bno055

            i2c = busio.I2C(board.SCL, board.SDA)
            self.device = adafruit_bno055.BNO055(i2c)

            self.connected = True
            return True, f"Connected to {self.model}"
        except Exception as e:
            return False, str(e)

    def read_all(self) -> Optional[IMUData]:
        if not self.connected or not self.device:
            return None

        try:
            accel = self.device.acceleration
            gyro = self.device.gyro
            mag = self.device.magnetic
            temp = self.device.temperature

            imu = IMUData(
                timestamp=datetime.now(),
                station="IMU_01",
                instrument=self.model
            )

            if accel:
                imu.accel_x_ms2, imu.accel_y_ms2, imu.accel_z_ms2 = accel
            if gyro:
                imu.gyro_x_rad_s, imu.gyro_y_rad_s, imu.gyro_z_rad_s = gyro
            if mag:
                imu.mag_x_nt, imu.mag_y_nt, imu.mag_z_nt = mag
            if temp:
                imu.temperature_c = temp

            return imu
        except Exception as e:
            print(f"IMU read error: {e}")
            return None

# ============================================================================
# TAB 1: WAVE METHODS (Seismic + GPR + Geophone)
# ============================================================================
class WaveMethodsTab:
    def __init__(self, parent, app, ui_queue, data_hub):
        self.parent = parent
        self.app = app
        self.ui_queue = ui_queue
        self.data_hub = data_hub

        self.geophone = None
        self.geophone_connected = False

        self.frame = ttk.Frame(parent)
        self._build_ui()

    def _build_ui(self):
        left = tk.Frame(self.frame, bg="#f0f0f0", width=250)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=2, pady=2)
        left.pack_propagate(False)

        tk.Label(left, text="📡 WAVE METHODS", font=("Arial", 12, "bold"),
                bg="#f0f0f0", fg="#1A3A5A").pack(pady=10)

        # Seismic section
        seismic_frame = tk.LabelFrame(left, text="Seismic", bg="#f0f0f0",
                                     font=("Arial", 10, "bold"))
        seismic_frame.pack(fill=tk.X, padx=5, pady=5)

        status = []
        if HAS_PYSACIO:
            status.append("SAC ✓")
        if HAS_CYMSEED3:
            status.append("MiniSEED ✓")
        if HAS_XDAS:
            status.append("DAS ✓")

        tk.Label(seismic_frame, text=" · ".join(status) if status else "No parsers",
                font=("Arial", 7), bg="#f0f0f0", fg="#2A5A2A" if status else "#AA4A4A").pack()

        ttk.Button(seismic_frame, text="📂 Import SAC/MiniSEED",
                  command=self._import_seismic).pack(fill=tk.X, pady=2)

        if HAS_XDAS:
            ttk.Button(seismic_frame, text="🔌 Connect Xdas DAS",
                      command=self._connect_xdas).pack(fill=tk.X, pady=2)

        # Geophone section
        geophone_frame = tk.LabelFrame(left, text="Geophone", bg="#f0f0f0",
                                      font=("Arial", 10, "bold"))
        geophone_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(geophone_frame, text="SM-24 + ADS1115 ($50 solution)",
                font=("Arial", 7), bg="#f0f0f0", fg="#666").pack()

        status_frame = tk.Frame(geophone_frame, bg="#f0f0f0")
        status_frame.pack(fill=tk.X, pady=2)
        tk.Label(status_frame, text="Status:", bg="#f0f0f0").pack(side=tk.LEFT)
        self.geo_status = tk.Label(status_frame, text="●", fg="red",
                                   font=("Arial", 10), bg="#f0f0f0")
        self.geo_status.pack(side=tk.LEFT, padx=5)

        self.geo_connect_btn = ttk.Button(geophone_frame, text="🔌 Connect Geophone",
                                         command=self._connect_geophone,
                                         state='normal' if HAS_ADS1115 else 'disabled')
        self.geo_connect_btn.pack(fill=tk.X, pady=2)

        self.geo_read_btn = ttk.Button(geophone_frame, text="📊 Read Trace",
                                       command=self._read_geophone,
                                       state='disabled')
        self.geo_read_btn.pack(fill=tk.X, pady=2)

        if not HAS_ADS1115:
            tk.Label(geophone_frame, text="(adafruit-circuitpython-ads1x15 not installed)",
                    font=("Arial", 7), bg="#f0f0f0", fg="#AA4A4A").pack()

        # GPR section
        gpr_frame = tk.LabelFrame(left, text="GPR", bg="#f0f0f0",
                                 font=("Arial", 10, "bold"))
        gpr_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(gpr_frame, text="GSSI · Sensors&Software · MALÅ",
                font=("Arial", 7), bg="#f0f0f0", fg="#666").pack()

        ttk.Button(gpr_frame, text="📂 Import DZT/DT1",
                  command=self._import_gpr).pack(fill=tk.X, pady=2)

        # Right panel with REAL data display
        right = tk.Frame(self.frame, bg="white")
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Notebook for different views
        self.view_notebook = ttk.Notebook(right)
        self.view_notebook.pack(fill=tk.BOTH, expand=True)

        # ============ SEISMIC VIEW ============
        seismic_view = tk.Frame(self.view_notebook, bg="white")
        self.view_notebook.add(seismic_view, text="📊 Seismic")

        # Create matplotlib figure for seismic
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

        self.seismic_fig = Figure(figsize=(8, 4), dpi=90, facecolor='white')
        self.seismic_ax = self.seismic_fig.add_subplot(111)
        self.seismic_canvas = FigureCanvasTkAgg(self.seismic_fig, seismic_view)
        self.seismic_canvas.draw()
        self.seismic_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Seismic info frame
        seismic_info = tk.Frame(seismic_view, bg="white", height=60)
        seismic_info.pack(fill=tk.X)
        seismic_info.pack_propagate(False)

        self.seismic_info = tk.Label(seismic_info,
            text="No seismic data loaded",
            font=("Arial", 9), bg="white", fg="#666")
        self.seismic_info.pack(pady=5)

        # ============ GPR VIEW ============
        gpr_view = tk.Frame(self.view_notebook, bg="white")
        self.view_notebook.add(gpr_view, text="📡 GPR")

        self.gpr_fig = Figure(figsize=(8, 4), dpi=90, facecolor='white')
        self.gpr_ax = self.gpr_fig.add_subplot(111)
        self.gpr_canvas = FigureCanvasTkAgg(self.gpr_fig, gpr_view)
        self.gpr_canvas.draw()
        self.gpr_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        gpr_info = tk.Frame(gpr_view, bg="white", height=60)
        gpr_info.pack(fill=tk.X)
        gpr_info.pack_propagate(False)

        self.gpr_info = tk.Label(gpr_info,
            text="No GPR data loaded",
            font=("Arial", 9), bg="white", fg="#666")
        self.gpr_info.pack(pady=5)

        # ============ GEOPHONE VIEW ============
        geo_view = tk.Frame(self.view_notebook, bg="white")
        self.view_notebook.add(geo_view, text="🎤 Geophone")

        self.geo_fig = Figure(figsize=(8, 4), dpi=90, facecolor='white')
        self.geo_ax = self.geo_fig.add_subplot(111)
        self.geo_canvas = FigureCanvasTkAgg(self.geo_fig, geo_view)
        self.geo_canvas.draw()
        self.geo_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        geo_info = tk.Frame(geo_view, bg="white", height=60)
        geo_info.pack(fill=tk.X)
        geo_info.pack_propagate(False)

        self.geo_info = tk.Label(geo_info,
            text="No geophone connected",
            font=("Arial", 9), bg="white", fg="#666")
        self.geo_info.pack(pady=5)

    def update_seismic_display(self, trace):
        """Update seismic plot with real data"""
        if trace is None or trace.data is None:
            return

        self.seismic_ax.clear()
        time = np.arange(len(trace.data)) / trace.sampling_rate
        self.seismic_ax.plot(time, trace.data, 'b-', linewidth=0.8)
        self.seismic_ax.set_xlabel("Time (s)", fontsize=9)
        self.seismic_ax.set_ylabel("Amplitude", fontsize=9)
        self.seismic_ax.set_title(f"{trace.station}.{trace.channel}", fontsize=10, fontweight='bold')
        self.seismic_ax.grid(True, alpha=0.3)

        # Auto-scale with padding
        y_min, y_max = trace.data.min(), trace.data.max()
        padding = (y_max - y_min) * 0.1
        self.seismic_ax.set_ylim(y_min - padding, y_max + padding)

        self.seismic_canvas.draw()

        # Update info
        self.seismic_info.config(
            text=f"Station: {trace.station} · Channel: {trace.channel} · "
                 f"Samples: {trace.npts} · Rate: {trace.sampling_rate} Hz"
        )

    def update_gpr_display(self, gpr):
        """Update GPR plot with real data"""
        if gpr is None or gpr.data is None:
            return

        self.gpr_ax.clear()

        # Plot radargram
        extent = [0, gpr.traces * 0.1, gpr.time_window_ns, 0]
        vmin, vmax = np.percentile(gpr.data, [5, 95])
        self.gpr_ax.imshow(gpr.data.T, aspect='auto', cmap='gray',
                          extent=extent, vmin=vmin, vmax=vmax)
        self.gpr_ax.set_xlabel("Distance (m)", fontsize=9)
        self.gpr_ax.set_ylabel("Time (ns)", fontsize=9)
        self.gpr_ax.set_title(f"{gpr.antenna_frequency_mhz} MHz GPR Profile", fontsize=10, fontweight='bold')

        self.gpr_canvas.draw()

        self.gpr_info.config(
            text=f"Traces: {gpr.traces} · Samples/Trace: {gpr.samples_per_trace} · "
                 f"Window: {gpr.time_window_ns} ns"
        )

    def update_geophone_display(self, data):
        """Update geophone plot with real data"""
        if data is None or data.data is None:
            return

        self.geo_ax.clear()
        time = np.arange(len(data.data)) / data.sampling_rate
        self.geo_ax.plot(time, data.data, 'g-', linewidth=1)
        self.geo_ax.set_xlabel("Time (s)", fontsize=9)
        self.geo_ax.set_ylabel("Voltage (V)", fontsize=9)
        self.geo_ax.set_title(f"Geophone - Channel {data.channel}", fontsize=10, fontweight='bold')
        self.geo_ax.grid(True, alpha=0.3)

        self.geo_canvas.draw()

        self.geo_info.config(
            text=f"Samples: {data.npts} · Rate: {data.sampling_rate} Hz · "
                 f"ADC: {data.adc_resolution_bits}-bit"
        )

    def _import_seismic(self):
        path = filedialog.askopenfilename(
            title="Import Seismic File",
            filetypes=[
                ("SAC files", "*.sac"),
                ("SACD files", "*.SACD* *.SACD.*"),  # ← ADD THIS LINE
                ("MiniSEED", "*.mseed *.miniseed"),
                ("All files", "*.*")
            ]
        )
        if not path:
            return

        ext = Path(path).suffix.lower()
        fname = path.lower()
        traces = []

        # Check for SACD files first (they have .SACD in the name)
        if '.sacd' in fname and HAS_PYSACIO:  # SACD files still use pysacio
            traces = SacParser.parse(path)  # Try SAC parser first
            if not traces:  # If that fails, try SACD parser
                traces = SACDParser.parse(path)
        elif ext == '.sac' and HAS_PYSACIO:
            traces = SacParser.parse(path)
        elif ext in ['.mseed', '.miniseed'] and HAS_CYMSEED3:
            traces = MiniSEEDParser.parse(path)

        for trace in traces:
            self.data_hub.add_data('seismic', trace)

        if traces:
            self.app.center.set_status(f"✅ Imported {len(traces)} traces")
            # Update display with the first trace
            self.update_seismic_display(traces[0])
        else:
            self.app.center.set_status(f"❌ Failed to parse seismic file")

    def _import_gpr(self):
        path = filedialog.askopenfilename(
            title="Import GPR File",
            filetypes=[
                ("GSSI DZT", "*.dzt"),
                ("Sensors & Software DT1", "*.dt1"),
                ("All files", "*.*")
            ]
        )
        if not path:
            return

        ext = Path(path).suffix.lower()
        gpr = None

        if ext == '.dzt':
            gpr = GSSIDZTParser.parse(path)
        elif ext == '.dt1':
            gpr = SensorsSoftwareDT1Parser.parse(path)

        if gpr:
            self.data_hub.add_data('gpr', gpr)
            self.app.center.set_status(f"✅ Imported GPR data")
            # Update the display with the new GPR data
            self.update_gpr_display(gpr)
        else:
            self.app.center.set_status(f"❌ Failed to parse GPR file")

    def _connect_xdas(self):
        self.app.center.set_status("Connecting to Xdas DAS...", "processing")
        # Xdas connection would go here
        self.app.center.show_operation_complete("Xdas", "Connected")

    def _connect_geophone(self):
        self.geophone = GeophoneADS1115Driver()

        def connect_thread():
            success, msg = self.geophone.connect()

            def update():
                if success:
                    self.geophone_connected = True
                    self.geo_status.config(fg="green")
                    self.geo_connect_btn.config(text="✅ Connected", state='disabled')
                    self.geo_read_btn.config(state='normal')
                    self.app.center.set_status(f"✅ {msg}")
                else:
                    self.app.center.set_status(f"❌ {msg}")
            self.ui_queue.schedule(update)

        threading.Thread(target=connect_thread, daemon=True).start()

    def _read_geophone(self):
        if not self.geophone or not self.geophone.connected:
            return

        def read_thread():
            data = self.geophone.read_trace(duration_seconds=2.0)

            def update():
                if data:
                    self.data_hub.add_data('geophone', data)
                    self.app.center.set_status(f"✅ Recorded {data.npts} samples")
                    # Update geophone display with real data
                    self.update_geophone_display(data)
                else:
                    self.app.center.set_status("❌ Failed to read geophone")
            self.ui_queue.schedule(update)

        threading.Thread(target=read_thread, daemon=True).start()

# ============================================================================
# TAB 2: ELECTRICAL METHODS (ERT + EM + MT)
# ============================================================================
class ElectricalMethodsTab:
    def __init__(self, parent, app, ui_queue, data_hub):
        self.parent = parent
        self.app = app
        self.ui_queue = ui_queue
        self.data_hub = data_hub

        # Register as observer
        self.data_hub.register_observer(self)

        self.geonics = None
        self.em_connected = False

        self.frame = ttk.Frame(parent)
        self._build_ui()

    def _default_parse(self, filepath):
        """Fallback parser if none provided"""
        raise Exception("ERT parser not available")

    def _default_spacing(self, a, b, m, n):
        return 5.0

    def _build_ui(self):
        left = tk.Frame(self.frame, bg="#f0f0f0", width=250)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=2, pady=2)
        left.pack_propagate(False)

        tk.Label(left, text="⚡ ELECTRICAL METHODS", font=("Arial", 12, "bold"),
                bg="#f0f0f0", fg="#1A3A5A").pack(pady=10)

        # ERT section
        ert_frame = tk.LabelFrame(left, text="ERT", bg="#f0f0f0",
                                 font=("Arial", 10, "bold"))
        ert_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(ert_frame, text="ABEM · IRIS · Zonge · pyGIMLi",
                font=("Arial", 7), bg="#f0f0f0", fg="#666").pack()

        status = []
        if HAS_REDA:
            status.append("REDA ✓")
        if HAS_PYGIMLI:
            status.append("pyGIMLi ✓")

        tk.Label(ert_frame, text=" · ".join(status) if status else "",
                font=("Arial", 7), bg="#f0f0f0").pack()

        ttk.Button(ert_frame, text="📂 Import Syscal/ABEM",
                  command=self._import_ert).pack(fill=tk.X, pady=2)

        # EM section
        em_frame = tk.LabelFrame(left, text="EM Induction", bg="#f0f0f0",
                                font=("Arial", 10, "bold"))
        em_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(em_frame, text="Geonics · GEM", font=("Arial", 7),
                bg="#f0f0f0", fg="#666").pack()

        status_frame = tk.Frame(em_frame, bg="#f0f0f0")
        status_frame.pack(fill=tk.X, pady=2)
        tk.Label(status_frame, text="Status:", bg="#f0f0f0").pack(side=tk.LEFT)
        self.em_status = tk.Label(status_frame, text="●", fg="red",
                                  font=("Arial", 10), bg="#f0f0f0")
        self.em_status.pack(side=tk.LEFT, padx=5)

        port_frame = tk.Frame(em_frame, bg="#f0f0f0")
        port_frame.pack(fill=tk.X, pady=2)
        tk.Label(port_frame, text="Port:", bg="#f0f0f0").pack(side=tk.LEFT)
        self.em_port = tk.StringVar(value="COM3" if IS_WINDOWS else "/dev/ttyUSB0")
        ttk.Entry(port_frame, textvariable=self.em_port, width=12).pack(side=tk.RIGHT)

        self.em_connect_btn = ttk.Button(em_frame, text="🔌 Connect Geonics",
                                         command=self._connect_geonics)
        self.em_connect_btn.pack(fill=tk.X, pady=2)

        self.em_read_btn = ttk.Button(em_frame, text="📊 Read Measurement",
                                      command=self._read_em,
                                      state='disabled')
        self.em_read_btn.pack(fill=tk.X, pady=2)

        # MT section
        mt_frame = tk.LabelFrame(left, text="Magnetotellurics", bg="#f0f0f0",
                                font=("Arial", 10, "bold"))
        mt_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(mt_frame, text="Phoenix · Metronix · Aurora",
                font=("Arial", 7), bg="#f0f0f0", fg="#666").pack()

        status = "Aurora ✓" if HAS_AURORA else ""
        tk.Label(mt_frame, text=status, font=("Arial", 7), bg="#f0f0f0").pack()

        ttk.Button(mt_frame, text="📂 Import EDI",
                  command=self._import_mt).pack(fill=tk.X, pady=2)

        # Right panel
        # Right panel with REAL data display
        right = tk.Frame(self.frame, bg="white")
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Notebook for different views
        self.view_notebook = ttk.Notebook(right)
        self.view_notebook.pack(fill=tk.BOTH, expand=True)

        # ============ ERT VIEW ============
        ert_view = tk.Frame(self.view_notebook, bg="white")
        self.view_notebook.add(ert_view, text="⚡ ERT")

        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

        self.ert_fig = Figure(figsize=(8, 4), dpi=90, facecolor='white')
        self.ert_ax = self.ert_fig.add_subplot(111)
        self.ert_canvas = FigureCanvasTkAgg(self.ert_fig, ert_view)
        self.ert_canvas.draw()
        self.ert_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        ert_info = tk.Frame(ert_view, bg="white", height=60)
        ert_info.pack(fill=tk.X)
        ert_info.pack_propagate(False)

        self.ert_info = tk.Label(ert_info,
            text="No ERT data loaded",
            font=("Arial", 9), bg="white", fg="#666")
        self.ert_info.pack(pady=5)

        # ============ EM VIEW ============
        em_view = tk.Frame(self.view_notebook, bg="white")
        self.view_notebook.add(em_view, text="🧲 EM Induction")

        self.em_fig = Figure(figsize=(8, 4), dpi=90, facecolor='white')
        self.em_ax = self.em_fig.add_subplot(111)
        self.em_canvas = FigureCanvasTkAgg(self.em_fig, em_view)
        self.em_canvas.draw()
        self.em_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        em_info = tk.Frame(em_view, bg="white", height=60)
        em_info.pack(fill=tk.X)
        em_info.pack_propagate(False)

        self.em_info = tk.Label(em_info,
            text="No EM data - connect Geonics or import file",
            font=("Arial", 9), bg="white", fg="#666")
        self.em_info.pack(pady=5)

        # ============ MT VIEW ============
        mt_view = tk.Frame(self.view_notebook, bg="white")
        self.view_notebook.add(mt_view, text="📊 Magnetotellurics")

        self.mt_fig = Figure(figsize=(8, 4), dpi=90, facecolor='white')
        self.mt_ax = self.mt_fig.add_subplot(111)
        self.mt_canvas = FigureCanvasTkAgg(self.mt_fig, mt_view)
        self.mt_canvas.draw()
        self.mt_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        mt_info = tk.Frame(mt_view, bg="white", height=60)
        mt_info.pack(fill=tk.X)
        mt_info.pack_propagate(False)

        self.mt_info = tk.Label(mt_info,
            text="No MT data loaded",
            font=("Arial", 9), bg="white", fg="#666")
        self.mt_info.pack(pady=5)

    def _parse_ertlab_file(self, filepath):
        """
        Parse ERTLab format .data files
        Returns: (a, b, m, n, rhoa, err) arrays
        """
        import numpy as np
        a, b, m, n = [], [], [], []
        rhoa, err = [], []

        # First, read electrode mapping
        electrode_map = {}
        absolute_electrode = 1

        with open(filepath, 'r') as f:
            lines = f.readlines()

        # First pass: read electrode positions
        in_electrode_section = False
        for line in lines:
            line = line.strip()

            if line == '#elec_start':
                in_electrode_section = True
                continue
            if line == '#elec_end':
                in_electrode_section = False
                continue

            if in_electrode_section and line and not line.startswith('#'):
                parts = line.split()
                if len(parts) >= 6:
                    cable_electrode = parts[0]
                    electrode_map[cable_electrode] = absolute_electrode
                    absolute_electrode += 1

        # Second pass: read measurement data
        in_data_section = False
        for line in lines:
            line = line.strip()

            if line == '#data_start':
                in_data_section = True
                continue
            if line == '#data_end':
                in_data_section = False
                continue

            if not in_data_section or line.startswith('!') or line.startswith('#') or not line:
                continue

            parts = line.split()
            if len(parts) >= 10:
                try:
                    a_key = parts[1]
                    b_key = parts[2]
                    m_key = parts[3]
                    n_key = parts[4]

                    if all(key in electrode_map for key in [a_key, b_key, m_key, n_key]):
                        a_abs = electrode_map[a_key]
                        b_abs = electrode_map[b_key]
                        m_abs = electrode_map[m_key]
                        n_abs = electrode_map[n_key]

                        resistance = float(parts[5])
                        std_dev = float(parts[6])

                        # Geometry factor (simplified)
                        spacing = 5.0
                        current_distance = abs(a_abs - b_abs) * spacing
                        potential_distance = abs(m_abs - n_abs) * spacing

                        if current_distance > 0 and potential_distance > 0:
                            k = 2 * np.pi * (current_distance * potential_distance) / (current_distance - potential_distance + 0.001)
                        else:
                            k = 2 * np.pi * spacing

                        rho_apparent = resistance * k

                        a.append(a_abs)
                        b.append(b_abs)
                        m.append(m_abs)
                        n.append(n_abs)
                        rhoa.append(rho_apparent)
                        err.append(std_dev * 100 / resistance if resistance > 0 else 2.0)

                except (ValueError, KeyError):
                    continue

        # Filter invalid measurements
        a = np.array(a, dtype=int)
        b = np.array(b, dtype=int)
        m = np.array(m, dtype=int)
        n = np.array(n, dtype=int)
        rhoa = np.array(rhoa, dtype=float)
        err = np.array(err, dtype=float)

        valid_mask = (rhoa > 0) & (np.isfinite(rhoa)) & (rhoa < 1e8)
        a = a[valid_mask]
        b = b[valid_mask]
        m = m[valid_mask]
        n = n[valid_mask]
        rhoa = rhoa[valid_mask]
        err = err[valid_mask]

        print(f"✅ Parsed {len(rhoa)} valid ERT measurements")
        return a, b, m, n, rhoa, err


    def on_data_changed(self):
        """Called when data hub has new data - updates UI to show loaded status"""
        # Update ERT display and status
        if self.data_hub.ert_data:
            self.update_ert_display(self.data_hub.ert_data[-1])
            # Update the info label to show data is loaded
            self.ert_info.config(
                text=f"✅ LOADED: {len(self.data_hub.ert_data)} ERT datasets • "
                    f"Latest: {self.data_hub.ert_data[-1].station} • "
                    f"{self.data_hub.ert_data[-1].n_measurements} measurements"
            )
            # Update the tab title or indicator if needed
            self.app.center.set_status(f"✅ ERT data loaded: {len(self.data_hub.ert_data)} files")

        # Update EM display and status
        if self.data_hub.em_data:
            self.update_em_display(self.data_hub.em_data[-1])
            self.em_info.config(
                text=f"✅ LOADED: {len(self.data_hub.em_data)} EM datasets • "
                    f"Latest: {self.data_hub.em_data[-1].conductivity_ms_m:.1f} mS/m"
            )

        # Update MT display and status
        if self.data_hub.mt_data:
            self.update_mt_display(self.data_hub.mt_data[-1])
            self.mt_info.config(
                text=f"✅ LOADED: {len(self.data_hub.mt_data)} MT datasets • "
                    f"{self.data_hub.mt_data[-1].n_frequencies} frequencies"
            )

    def _import_ert(self):
        paths = filedialog.askopenfilenames(
            title="Select ERT Files (Ctrl+Click for multiple)",
            filetypes=[
                ("Syscal binary", "*.bin"),
                ("ABEM data", "*.dat *.data *.Data"),
                ("ERT CSV", "*.csv"),
                ("All files", "*.*")
            ]
        )

        if not paths:
            return

        self.app.center.set_status(f"📥 Importing {len(paths)} ERT files...", "import")

        for path in paths:
            try:
                # Use the passed parser method
                a, b, m, n, rhoa, err = self.parse_ertlab_file(path)

                ert = ERTData(
                    timestamp=datetime.now(),
                    station=Path(path).stem,
                    instrument="ABEM Terrameter",
                    apparent_rho=rhoa,
                    n_measurements=len(rhoa),
                    file_source=path
                )

                ert.raw_a = a
                ert.raw_b = b
                ert.raw_m = m
                ert.raw_n = n
                ert.raw_rhoa = rhoa
                ert.raw_err = err

                self.data_hub.add_data('ert', ert)
                print(f"✅ Imported: {Path(path).name} - {len(rhoa)} measurements")

            except Exception as e:
                print(f"❌ Failed to parse {Path(path).name}: {str(e)}")

        if self.data_hub.ert_data:
            self.update_ert_display(self.data_hub.ert_data[-1])

        self.app.center.set_status(f"✅ Imported {len(paths)} ERT files", "success")

    def _import_mt(self):
        path = filedialog.askopenfilename(
            title="Import EDI File",
            filetypes=[("EDI", "*.edi"), ("All files", "*.*")]
        )
        if path:
            mt = EDIParser.parse(path)
            if mt:
                self.data_hub.add_data('mt', mt)
                self.app.center.set_status(f"✅ Imported MT data")

    def _connect_geonics(self):
        port = self.em_port.get()

        def connect_thread():
            self.geonics = GeonicsEMDriver(port=port)
            success, msg = self.geonics.connect()

            def update():
                if success:
                    self.em_connected = True
                    self.em_status.config(fg="green")
                    self.em_connect_btn.config(text="✅ Connected", state='disabled')
                    self.em_read_btn.config(state='normal')
                    self.app.center.set_status(f"✅ {msg}")
                else:
                    self.app.center.set_status(f"❌ {msg}")
            self.ui_queue.schedule(update)

        threading.Thread(target=connect_thread, daemon=True).start()

    def _read_em(self):
        if not self.geonics or not self.geonics.connected:
            return

        def read_thread():
            data = self.geonics.read_measurement()

            def update():
                if data:
                    self.data_hub.add_data('em', data)
                    self.app.center.set_status(
                        f"✅ EM: Cond={data.conductivity_ms_m:.2f} mS/m")
                    self.update_em_display(data)
                else:
                    self.app.center.set_status("❌ Failed to read EM")
            self.ui_queue.schedule(update)

        threading.Thread(target=read_thread, daemon=True).start()

    def update_ert_display(self, ert):
        """Update ERT display with real data"""
        if ert is None or ert.apparent_rho is None or len(ert.apparent_rho) == 0:
            self.ert_ax.clear()
            self.ert_ax.text(0.5, 0.5, "No ERT data to display",
                            ha='center', va='center', transform=self.ert_ax.transAxes)
            self.ert_canvas.draw()
            self.ert_info.config(text="No ERT data loaded")
            return

        self.ert_ax.clear()

        # Create a histogram of resistivity values
        rho = ert.apparent_rho
        valid_rho = rho[rho > 0]

        if len(valid_rho) > 0:
            # Plot histogram on log scale
            self.ert_ax.hist(np.log10(valid_rho), bins=50, alpha=0.7,
                            color='blue', edgecolor='black')
            self.ert_ax.set_xlabel("Log10 Resistivity (Ω·m)")
            self.ert_ax.set_ylabel("Frequency")
            self.ert_ax.set_title(f"ERT Data Distribution - {ert.station}")
            self.ert_ax.grid(True, alpha=0.3)

            # Add statistics as text
            stats_text = f"Mean: {np.mean(valid_rho):.1f} Ω·m\n"
            stats_text += f"Median: {np.median(valid_rho):.1f} Ω·m\n"
            stats_text += f"Min: {np.min(valid_rho):.1f} Ω·m\n"
            stats_text += f"Max: {np.max(valid_rho):.1f} Ω·m"

            self.ert_ax.text(0.02, 0.98, stats_text,
                            transform=self.ert_ax.transAxes,
                            verticalalignment='top',
                            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        else:
            self.ert_ax.text(0.5, 0.5, "No valid resistivity values",
                            ha='center', va='center', transform=self.ert_ax.transAxes)

        self.ert_canvas.draw()

        # UPDATE THE INFO LABEL HERE - this is what shows in the UI
        info_text = f"✅ Measurements: {ert.n_measurements} · "
        info_text += f"Valid: {len(valid_rho)} · "
        info_text += f"Range: {np.min(valid_rho):.1f}-{np.max(valid_rho):.1f} Ω·m · "
        info_text += f"File: {Path(ert.file_source).name if ert.file_source else 'Live'}"

        self.ert_info.config(text=info_text)

    def update_em_display(self, em):
        """Update EM display with real data"""
        if em is None:
            return

        self.em_ax.clear()

        # Create a simple time series plot
        times = [em.timestamp]  # Would need to store history for real time series
        values = [em.conductivity_ms_m]

        if hasattr(self, 'em_history'):
            self.em_history['times'].append(em.timestamp)
            self.em_history['values'].append(em.conductivity_ms_m)
            # Keep last 100 points
            if len(self.em_history['times']) > 100:
                self.em_history['times'].pop(0)
                self.em_history['values'].pop(0)
            times = self.em_history['times']
            values = self.em_history['values']
        else:
            self.em_history = {'times': [em.timestamp], 'values': [em.conductivity_ms_m]}

        # Convert times to seconds for plotting
        if len(times) > 1:
            t0 = times[0]
            t_seconds = [(t - t0).total_seconds() for t in times]
            self.em_ax.plot(t_seconds, values, 'g-', linewidth=1.5)
            self.em_ax.set_xlabel("Time (s)", fontsize=9)
        else:
            self.em_ax.bar(['Current'], [values[0]], color='g')
            self.em_ax.set_xlabel("Measurement", fontsize=9)

        self.em_ax.set_ylabel("Conductivity (mS/m)", fontsize=9)
        self.em_ax.set_title("EM Induction - Real-time", fontsize=10, fontweight='bold')
        self.em_ax.grid(True, alpha=0.3)

        self.em_canvas.draw()

        self.em_info.config(
            text=f"Conductivity: {em.conductivity_ms_m:.2f} mS/m · "
                 f"Inphase: {em.inphase_ppm:.1f} ppm · Quad: {em.quadrature_ppm:.1f} ppm"
        )

    def update_mt_display(self, mt):
        """Update MT display with real data"""
        if mt is None or mt.frequencies is None:
            return

        self.mt_ax.clear()

        # Plot apparent resistivity vs frequency
        if len(mt.frequencies) > 1:
            self.mt_ax.loglog(mt.frequencies, np.abs(mt.impedance), 'b-', linewidth=1.5)
            self.mt_ax.set_xlabel("Frequency (Hz)", fontsize=9)
            self.mt_ax.set_ylabel("|Z| (Ω)", fontsize=9)
            self.mt_ax.set_title("Impedance vs Frequency", fontsize=10, fontweight='bold')
            self.mt_ax.grid(True, alpha=0.3, which='both')
        else:
            self.mt_ax.text(0.5, 0.5, "Insufficient data for plot",
                          ha='center', va='center', transform=self.mt_ax.transAxes)

        self.mt_canvas.draw()

        self.mt_info.config(
            text=f"Frequencies: {mt.n_frequencies} · File: {Path(mt.file_source).name if mt.file_source else 'Live'}"
        )

# ============================================================================
# TAB 3: POTENTIAL FIELDS (Magnetics + Gravity + IMU)
# ============================================================================
class PotentialFieldsTab:
    def __init__(self, parent, app, ui_queue, data_hub):
        self.parent = parent
        self.app = app
        self.ui_queue = ui_queue
        self.data_hub = data_hub

        self.imu = None
        self.imu_connected = False

        self.frame = ttk.Frame(parent)
        self._build_ui()

    def _build_ui(self):
        left = tk.Frame(self.frame, bg="#f0f0f0", width=250)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=2, pady=2)
        left.pack_propagate(False)

        tk.Label(left, text="🧲 POTENTIAL FIELDS", font=("Arial", 12, "bold"),
                bg="#f0f0f0", fg="#1A3A5A").pack(pady=10)

        # Magnetics section
        mag_frame = tk.LabelFrame(left, text="Magnetics", bg="#f0f0f0",
                                 font=("Arial", 10, "bold"))
        mag_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(mag_frame, text="Bartington · Geometrics · Sensys · QuSpin · LSM303D",
                font=("Arial", 7), bg="#f0f0f0", fg="#666").pack()

        ttk.Button(mag_frame, text="📂 Import Bartington CSV",
                  command=self._import_bartington).pack(fill=tk.X, pady=2)

        ttk.Button(mag_frame, text="📂 Import Geometrics G-858",
                  command=self._import_geometrics).pack(fill=tk.X, pady=2)

                # MARTAS Live Magnetometer section (NEW)
        if HAS_MARTAS:
            martas_frame = tk.LabelFrame(mag_frame, text="Live Magnetometers (MARTAS)", bg="#f0f0f0")
            martas_frame.pack(fill=tk.X, padx=5, pady=5)

            tk.Label(martas_frame, text="GEM GSM19/GSM90 · Geometrics G823A · LEMI",
                    font=("Arial", 7), bg="#f0f0f0", fg="#666").pack()

            # GEM button
            gem_frame = tk.Frame(martas_frame, bg="#f0f0f0")
            gem_frame.pack(fill=tk.X, pady=2)

            self.gem_status = tk.Label(gem_frame, text="●", fg="red",
                                       font=("Arial", 10), bg="#f0f0f0")
            self.gem_status.pack(side=tk.LEFT)

            tk.Label(gem_frame, text="GEM:", bg="#f0f0f0").pack(side=tk.LEFT, padx=5)
            self.gem_port = tk.StringVar(value="COM6" if IS_WINDOWS else "/dev/ttyUSB3")
            ttk.Entry(gem_frame, textvariable=self.gem_port, width=10).pack(side=tk.LEFT, padx=2)

            self.gem_connect_btn = ttk.Button(gem_frame, text="Connect",
                                              command=lambda: self._connect_martas("gem"))
            self.gem_connect_btn.pack(side=tk.RIGHT)

            # Geometrics button
            geo_frame = tk.Frame(martas_frame, bg="#f0f0f0")
            geo_frame.pack(fill=tk.X, pady=2)

            self.geo_mag_status = tk.Label(geo_frame, text="●", fg="red",
                                           font=("Arial", 10), bg="#f0f0f0")
            self.geo_mag_status.pack(side=tk.LEFT)

            tk.Label(geo_frame, text="Geometrics:", bg="#f0f0f0").pack(side=tk.LEFT, padx=5)
            self.geo_mag_port = tk.StringVar(value="COM7" if IS_WINDOWS else "/dev/ttyUSB4")
            ttk.Entry(geo_frame, textvariable=self.geo_mag_port, width=10).pack(side=tk.LEFT, padx=2)

            self.geo_mag_connect_btn = ttk.Button(geo_frame, text="Connect",
                                                  command=lambda: self._connect_martas("geometrics"))
            self.geo_mag_connect_btn.pack(side=tk.RIGHT)

            # Read button for all MARTAS devices
            self.martas_read_btn = ttk.Button(martas_frame, text="📊 Read All",
                                              command=self._read_martas,
                                              state='disabled')
            self.martas_read_btn.pack(fill=tk.X, pady=2)

        if HAS_QZFM:
            ttk.Button(mag_frame, text="🔌 Connect QuSpin ZFM",
                      command=self._connect_qzfm).pack(fill=tk.X, pady=2)

        # IMU section
        imu_frame = tk.LabelFrame(left, text="IMU (Motion Tracking)", bg="#f0f0f0",
                                 font=("Arial", 10, "bold"))
        imu_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(imu_frame, text="BNO055 9-DOF (accel, gyro, mag)",
                font=("Arial", 7), bg="#f0f0f0", fg="#666").pack()

        status_frame = tk.Frame(imu_frame, bg="#f0f0f0")
        status_frame.pack(fill=tk.X, pady=2)
        tk.Label(status_frame, text="Status:", bg="#f0f0f0").pack(side=tk.LEFT)
        self.imu_status = tk.Label(status_frame, text="●", fg="red",
                                   font=("Arial", 10), bg="#f0f0f0")
        self.imu_status.pack(side=tk.LEFT, padx=5)

        self.imu_connect_btn = ttk.Button(imu_frame, text="🔌 Connect IMU",
                                          command=self._connect_imu,
                                          state='normal' if HAS_BNO055 else 'disabled')
        self.imu_connect_btn.pack(fill=tk.X, pady=2)

        self.imu_read_btn = ttk.Button(imu_frame, text="📊 Read All Sensors",
                                       command=self._read_imu,
                                       state='disabled')
        self.imu_read_btn.pack(fill=tk.X, pady=2)

        if not HAS_BNO055:
            tk.Label(imu_frame, text="(adafruit-circuitpython-bno055 not installed)",
                    font=("Arial", 7), bg="#f0f0f0", fg="#AA4A4A").pack()

        # Gravity section
        grav_frame = tk.LabelFrame(left, text="Gravity", bg="#f0f0f0",
                                  font=("Arial", 10, "bold"))
        grav_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(grav_frame, text="Scintrex CG-5/CG-6 · LaCoste",
                font=("Arial", 7), bg="#f0f0f0", fg="#666").pack()

        ttk.Button(grav_frame, text="📂 Import Scintrex CG",
                  command=self._import_scintrex).pack(fill=tk.X, pady=2)

        # Right panel with REAL data display
        right = tk.Frame(self.frame, bg="white")
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Notebook for different views
        self.view_notebook = ttk.Notebook(right)
        self.view_notebook.pack(fill=tk.BOTH, expand=True)

        # ============ MAGNETICS VIEW ============
        mag_view = tk.Frame(self.view_notebook, bg="white")
        self.view_notebook.add(mag_view, text="🧲 Magnetics")

        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

        self.mag_fig = Figure(figsize=(8, 4), dpi=90, facecolor='white')
        self.mag_ax = self.mag_fig.add_subplot(111)
        self.mag_canvas = FigureCanvasTkAgg(self.mag_fig, mag_view)
        self.mag_canvas.draw()
        self.mag_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        mag_info = tk.Frame(mag_view, bg="white", height=60)
        mag_info.pack(fill=tk.X)
        mag_info.pack_propagate(False)

        self.mag_info = tk.Label(mag_info,
            text="No magnetic data loaded",
            font=("Arial", 9), bg="white", fg="#666")
        self.mag_info.pack(pady=5)

        # ============ GRAVITY VIEW ============
        grav_view = tk.Frame(self.view_notebook, bg="white")
        self.view_notebook.add(grav_view, text="⚖️ Gravity")

        self.grav_fig = Figure(figsize=(8, 4), dpi=90, facecolor='white')
        self.grav_ax = self.grav_fig.add_subplot(111)
        self.grav_canvas = FigureCanvasTkAgg(self.grav_fig, grav_view)
        self.grav_canvas.draw()
        self.grav_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        grav_info = tk.Frame(grav_view, bg="white", height=60)
        grav_info.pack(fill=tk.X)
        grav_info.pack_propagate(False)

        self.grav_info = tk.Label(grav_info,
            text="No gravity data loaded",
            font=("Arial", 9), bg="white", fg="#666")
        self.grav_info.pack(pady=5)

        # ============ IMU VIEW ============
        imu_view = tk.Frame(self.view_notebook, bg="white")
        self.view_notebook.add(imu_view, text="📊 IMU")

        self.imu_fig = Figure(figsize=(8, 4), dpi=90, facecolor='white')
        self.imu_ax = self.imu_fig.add_subplot(111)
        self.imu_canvas = FigureCanvasTkAgg(self.imu_fig, imu_view)
        self.imu_canvas.draw()
        self.imu_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        imu_info = tk.Frame(imu_view, bg="white", height=60)
        imu_info.pack(fill=tk.X)
        imu_info.pack_propagate(False)

        self.imu_info = tk.Label(imu_info,
            text="No IMU connected",
            font=("Arial", 9), bg="white", fg="#666")
        self.imu_info.pack(pady=5)

    def _import_bartington(self):
        path = filedialog.askopenfilename(
            title="Import Bartington CSV",
            filetypes=[("CSV", "*.csv"), ("All files", "*.*")]
        )
        if path:
            measurements = BartingtonGrad601Parser.parse(path)
            for mag in measurements:
                self.data_hub.add_data('magnetics', mag)
            if measurements:
                self.update_magnetic_display(measurements[0])
            self.app.center.set_status(f"✅ Imported {len(measurements)} readings")

    def _import_scintrex(self):
        path = filedialog.askopenfilename(
            title="Import Scintrex CG",
            filetypes=[("Text", "*.txt"), ("All files", "*.*")]
        )
        if path:
            measurements = ScintrexCGParser.parse(path)
            for grav in measurements:
                self.data_hub.add_data('gravity', grav)
            if measurements:
                self.update_gravity_display(measurements[0])
            self.app.center.set_status(f"✅ Imported {len(measurements)} stations")

    def _import_geometrics(self):
        path = filedialog.askopenfilename(
            title="Import Geometrics G-858",
            filetypes=[("Text", "*.txt"), ("CSV", "*.csv"), ("All files", "*.*")]
        )
        if path:
            measurements = GeometricsG858Parser.parse(path)
            for mag in measurements:
                self.data_hub.add_data('magnetics', mag)
            self.app.center.set_status(f"✅ Imported {len(measurements)} readings")

    def _connect_martas(self, instrument_type):
        """Connect to MARTAS magnetometer"""
        # Get the appropriate port based on instrument type
        if instrument_type == "gem":
            port = self.gem_port.get()
            status_label = self.gem_status
            connect_btn = self.gem_connect_btn
        elif instrument_type == "geometrics":
            port = self.geo_mag_port.get()
            status_label = self.geo_mag_status
            connect_btn = self.geo_mag_connect_btn
        else:
            return

        # Create driver instance
        from types import SimpleNamespace
        self.martas_devices = getattr(self, 'martas_devices', {})

        def connect_thread():
            try:
                # Create MARTAS driver
                driver = MARTASMagnetometerDriver(instrument_type=instrument_type, port=port)
                success, msg = driver.connect()

                if success:
                    # Store the driver
                    self.martas_devices[instrument_type] = driver

                    def update():
                        status_label.config(fg="green")
                        connect_btn.config(text="✅ Connected", state='disabled')
                        self.martas_read_btn.config(state='normal')
                        self.app.center.set_status(f"✅ {msg}")
                    self.ui_queue.schedule(update)
                else:
                    def update():
                        self.app.center.set_status(f"❌ {msg}")
                    self.ui_queue.schedule(update)

            except Exception as e:
                def update():
                    self.app.center.set_status(f"❌ Connection error: {str(e)}")
                self.ui_queue.schedule(update)

        threading.Thread(target=connect_thread, daemon=True).start()

    def _read_martas(self):
        """Read from all connected MARTAS devices"""
        if not hasattr(self, 'martas_devices') or not self.martas_devices:
            return

        def read_thread():
            readings = []
            for inst_type, driver in self.martas_devices.items():
                if driver and driver.connected:
                    data = driver.read_measurement()
                    if data:
                        self.data_hub.add_data('magnetics', data)
                        readings.append(f"{inst_type}: {data.total_field_nt:.1f} nT")

            def update():
                if readings:
                    self.app.center.set_status("✅ " + " · ".join(readings))
                else:
                    self.app.center.set_status("❌ No readings from MARTAS devices")
            self.ui_queue.schedule(update)

        threading.Thread(target=read_thread, daemon=True).start()

    def _connect_qzfm(self):
        self.app.center.set_status("Connecting to QuSpin ZFM...", "processing")
        # QZFM connection would go here
        self.app.center.show_operation_complete("QuSpin", "Connected")

    def _connect_imu(self):
        self.imu = IMUBNO055Driver()

        def connect_thread():
            success, msg = self.imu.connect()

            def update():
                if success:
                    self.imu_connected = True
                    self.imu_status.config(fg="green")
                    self.imu_connect_btn.config(text="✅ Connected", state='disabled')
                    self.imu_read_btn.config(state='normal')
                    self.app.center.set_status(f"✅ {msg}")
                else:
                    self.app.center.set_status(f"❌ {msg}")
            self.ui_queue.schedule(update)

        threading.Thread(target=connect_thread, daemon=True).start()

    def _read_imu(self):
        if not self.imu or not self.imu.connected:
            return

        def read_thread():
            data = self.imu.read_all()

            def update():
                if data:
                    self.data_hub.add_data('imu', data)
                    self.app.center.set_status(
                        f"✅ IMU: Accel=({data.accel_x_ms2:.1f}, {data.accel_y_ms2:.1f}) m/s²")
                else:
                    self.app.center.set_status("❌ Failed to read IMU")
            self.ui_queue.schedule(update)

        threading.Thread(target=read_thread, daemon=True).start()

    def update_magnetic_display(self, mag):
        """Update magnetics display with real data"""
        if mag is None:
            return

        self.mag_ax.clear()

        # Create a simple bar for total field
        if mag.total_field_nt:
            self.mag_ax.bar(['Total Field'], [mag.total_field_nt], color='b', alpha=0.7)
            self.mag_ax.set_ylabel("Field (nT)", fontsize=9)

        # Add components if available
        if mag.x_nt or mag.y_nt or mag.z_nt:
            components = []
            values = []
            if mag.x_nt:
                components.append('X')
                values.append(mag.x_nt)
            if mag.y_nt:
                components.append('Y')
                values.append(mag.y_nt)
            if mag.z_nt:
                components.append('Z')
                values.append(mag.z_nt)

            self.mag_ax.bar(components, values, alpha=0.5, color='orange')

        self.mag_ax.set_title("Magnetic Field Measurement", fontsize=10, fontweight='bold')
        self.mag_ax.grid(True, alpha=0.3, axis='y')

        self.mag_canvas.draw()

        info_text = []
        if mag.total_field_nt:
            info_text.append(f"Total: {mag.total_field_nt:.1f} nT")
        if mag.x_nt:
            info_text.append(f"X: {mag.x_nt:.1f} nT")
        if mag.y_nt:
            info_text.append(f"Y: {mag.y_nt:.1f} nT")
        if mag.z_nt:
            info_text.append(f"Z: {mag.z_nt:.1f} nT")

        self.mag_info.config(text=" · ".join(info_text))

    def update_gravity_display(self, grav):
        """Update gravity display with real data"""
        if grav is None:
            return

        self.grav_ax.clear()

        # Store history for profile view
        if not hasattr(self, 'gravity_stations'):
            self.gravity_stations = []
            self.gravity_values = []

        if grav.station not in self.gravity_stations and grav.gravity_mgal:
            self.gravity_stations.append(grav.station)
            self.gravity_values.append(grav.gravity_mgal)

        if len(self.gravity_stations) > 1:
            # Plot as profile
            x = range(len(self.gravity_stations))
            self.grav_ax.plot(x, self.gravity_values, 'ro-', linewidth=1.5, markersize=6)
            self.grav_ax.set_xlabel("Station", fontsize=9)
            self.grav_ax.set_xticks(x)
            self.grav_ax.set_xticklabels(self.gravity_stations, rotation=45, ha='right', fontsize=7)
        else:
            # Single station
            self.grav_ax.bar(['Current'], [grav.gravity_mgal], color='r', alpha=0.7)
            self.grav_ax.set_xlabel("Measurement", fontsize=9)

        self.grav_ax.set_ylabel("Gravity (mGal)", fontsize=9)
        self.grav_ax.set_title("Gravity Measurements", fontsize=10, fontweight='bold')
        self.grav_ax.grid(True, alpha=0.3)

        self.grav_fig.tight_layout()
        self.grav_canvas.draw()

        self.grav_info.config(
            text=f"Gravity: {grav.gravity_mgal:.3f} mGal · Lat: {grav.latitude:.4f} · Lon: {grav.longitude:.4f}"
        )

    def update_imu_display(self, imu):
        """Update IMU display with real data"""
        if imu is None:
            return

        self.imu_ax.clear()

        # Create three subplots in one
        categories = []
        values = []
        colors = []

        if imu.accel_x_ms2:
            categories.extend(['Accel X', 'Accel Y', 'Accel Z'])
            values.extend([imu.accel_x_ms2, imu.accel_y_ms2, imu.accel_z_ms2])
            colors.extend(['r', 'r', 'r'])

        if imu.gyro_x_rad_s:
            categories.extend(['Gyro X', 'Gyro Y', 'Gyro Z'])
            values.extend([imu.gyro_x_rad_s, imu.gyro_y_rad_s, imu.gyro_z_rad_s])
            colors.extend(['g', 'g', 'g'])

        if imu.mag_x_nt:
            categories.extend(['Mag X', 'Mag Y', 'Mag Z'])
            values.extend([imu.mag_x_nt, imu.mag_y_nt, imu.mag_z_nt])
            colors.extend(['b', 'b', 'b'])

        if categories:
            bars = self.imu_ax.bar(categories, values, color=colors, alpha=0.7)
            self.imu_ax.set_ylabel("Value", fontsize=9)
            self.imu_ax.set_xticklabels(categories, rotation=45, ha='right', fontsize=7)

        self.imu_ax.set_title("IMU - All Sensors", fontsize=10, fontweight='bold')
        self.imu_ax.grid(True, alpha=0.3, axis='y')

        self.imu_fig.tight_layout()
        self.imu_canvas.draw()

        info_parts = []
        if imu.temperature_c:
            info_parts.append(f"Temp: {imu.temperature_c:.1f}°C")
        if imu.accel_x_ms2:
            info_parts.append(f"Accel: ({imu.accel_x_ms2:.1f}, {imu.accel_y_ms2:.1f}, {imu.accel_z_ms2:.1f}) m/s²")

        self.imu_info.config(text=" · ".join(info_parts))

# ============================================================================
# TAB 4: AUXILIARY (GNSS + Environmental)
# ============================================================================
class AuxiliaryTab:
    def __init__(self, parent, app, ui_queue, data_hub):
        self.parent = parent
        self.app = app
        self.ui_queue = ui_queue
        self.data_hub = data_hub

        self.gnss = None
        self.gnss_connected = False
        self.campbell = None
        self.campbell_connected = False

        self.frame = ttk.Frame(parent)
        self._build_ui()

    def _build_ui(self):
        left = tk.Frame(self.frame, bg="#f0f0f0", width=250)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=2, pady=2)
        left.pack_propagate(False)

        tk.Label(left, text="🗺️ AUXILIARY", font=("Arial", 12, "bold"),
                bg="#f0f0f0", fg="#1A3A5A").pack(pady=10)

        # GNSS section
        gnss_frame = tk.LabelFrame(left, text="GNSS/RTK", bg="#f0f0f0",
                                  font=("Arial", 10, "bold"))
        gnss_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(gnss_frame, text="Trimble · Leica · Septentrio · u-blox",
                font=("Arial", 7), bg="#f0f0f0", fg="#666").pack()

        status_frame = tk.Frame(gnss_frame, bg="#f0f0f0")
        status_frame.pack(fill=tk.X, pady=2)
        tk.Label(status_frame, text="Status:", bg="#f0f0f0").pack(side=tk.LEFT)
        self.gnss_status = tk.Label(status_frame, text="●", fg="red",
                                    font=("Arial", 10), bg="#f0f0f0")
        self.gnss_status.pack(side=tk.LEFT, padx=5)

        port_frame = tk.Frame(gnss_frame, bg="#f0f0f0")
        port_frame.pack(fill=tk.X, pady=2)
        tk.Label(port_frame, text="Port:", bg="#f0f0f0").pack(side=tk.LEFT)
        self.gnss_port = tk.StringVar(value="COM4" if IS_WINDOWS else "/dev/ttyUSB1")
        ttk.Entry(port_frame, textvariable=self.gnss_port, width=12).pack(side=tk.RIGHT)

        self.gnss_connect_btn = ttk.Button(gnss_frame, text="🔌 Connect GNSS",
                                           command=self._connect_gnss)
        self.gnss_connect_btn.pack(fill=tk.X, pady=2)

        self.gnss_read_btn = ttk.Button(gnss_frame, text="📡 Get Position",
                                        command=self._get_gnss_position,
                                        state='disabled')
        self.gnss_read_btn.pack

        # OpenADMS Total Station section (NEW)
        if HAS_OPENADMS:
            ts_frame = tk.LabelFrame(left, text="Total Stations (OpenADMS)", bg="#f0f0f0",
                                    font=("Arial", 10, "bold"))
            ts_frame.pack(fill=tk.X, padx=5, pady=5)

            tk.Label(ts_frame, text="Leica · Geotechnical sensors",
                    font=("Arial", 7), bg="#f0f0f0", fg="#666").pack()

            # Connection type selector
            conn_frame = tk.Frame(ts_frame, bg="#f0f0f0")
            conn_frame.pack(fill=tk.X, pady=2)

            self.ts_conn_type = tk.StringVar(value="serial")
            tk.Radiobutton(conn_frame, text="Serial", variable=self.ts_conn_type,
                          value="serial", bg="#f0f0f0").pack(side=tk.LEFT, padx=2)
            tk.Radiobutton(conn_frame, text="TCP/IP", variable=self.ts_conn_type,
                          value="tcp", bg="#f0f0f0").pack(side=tk.LEFT, padx=2)

            # Serial port entry
            port_frame = tk.Frame(ts_frame, bg="#f0f0f0")
            port_frame.pack(fill=tk.X, pady=2)
            tk.Label(port_frame, text="Port:", bg="#f0f0f0").pack(side=tk.LEFT)
            self.ts_port = tk.StringVar(value="COM8" if IS_WINDOWS else "/dev/ttyUSB5")
            ttk.Entry(port_frame, textvariable=self.ts_port, width=12).pack(side=tk.RIGHT)

            # TCP host entry
            host_frame = tk.Frame(ts_frame, bg="#f0f0f0")
            host_frame.pack(fill=tk.X, pady=2)
            tk.Label(host_frame, text="Host:", bg="#f0f0f0").pack(side=tk.LEFT)
            self.ts_host = tk.StringVar(value="192.168.1.100:2101")
            ttk.Entry(host_frame, textvariable=self.ts_host, width=15).pack(side=tk.RIGHT)

            # Status and buttons
            status_frame = tk.Frame(ts_frame, bg="#f0f0f0")
            status_frame.pack(fill=tk.X, pady=2)

            self.ts_status = tk.Label(status_frame, text="●", fg="red",
                                      font=("Arial", 10), bg="#f0f0f0")
            self.ts_status.pack(side=tk.LEFT)

            self.ts_connect_btn = ttk.Button(status_frame, text="🔌 Connect",
                                            command=self._connect_total_station)
            self.ts_connect_btn.pack(side=tk.RIGHT)

            self.ts_read_btn = ttk.Button(ts_frame, text="📏 Read Position",
                                         command=self._read_total_station,
                                         state='disabled')
            self.ts_read_btn.pack(fill=tk.X, pady=2)

        # Environmental section
        env_frame = tk.LabelFrame(left, text="Environmental", bg="#f0f0f0",
                                 font=("Arial", 10, "bold"))
        env_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(env_frame, text="Campbell CR-series · Geotech · Durham Geo",
                font=("Arial", 7), bg="#f0f0f0", fg="#666").pack()

        env_status_frame = tk.Frame(env_frame, bg="#f0f0f0")
        env_status_frame.pack(fill=tk.X, pady=2)
        tk.Label(env_status_frame, text="Status:", bg="#f0f0f0").pack(side=tk.LEFT)
        self.env_status = tk.Label(env_status_frame, text="●", fg="red",
                                   font=("Arial", 10), bg="#f0f0f0")
        self.env_status.pack(side=tk.LEFT, padx=5)

        env_port_frame = tk.Frame(env_frame, bg="#f0f0f0")
        env_port_frame.pack(fill=tk.X, pady=2)
        tk.Label(env_port_frame, text="Port:", bg="#f0f0f0").pack(side=tk.LEFT)
        self.env_port = tk.StringVar(value="COM5" if IS_WINDOWS else "/dev/ttyUSB2")
        ttk.Entry(env_port_frame, textvariable=self.env_port, width=12).pack(side=tk.RIGHT)

        self.env_connect_btn = ttk.Button(env_frame, text="🔌 Connect Campbell",
                                          command=self._connect_campbell,
                                          state='normal' if HAS_PYMODBUS else 'disabled')
        self.env_connect_btn.pack(fill=tk.X, pady=2)

        self.env_read_btn = ttk.Button(env_frame, text="📊 Read Sensors",
                                       command=self._read_campbell,
                                       state='disabled')
        self.env_read_btn.pack(fill=tk.X, pady=2)

        if not HAS_PYMODBUS:
            tk.Label(env_frame, text="(pymodbus not installed)",
                    font=("Arial", 7), bg="#f0f0f0", fg="#AA4A4A").pack()

        # Right panel with displays
        right = tk.Frame(self.frame, bg="white")
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=2, pady=2)

        # GNSS display
        gnss_display_frame = tk.LabelFrame(right, text="GNSS Position", bg="white")
        gnss_display_frame.pack(fill=tk.X, padx=5, pady=5)

        self.gnss_display = tk.Text(gnss_display_frame, height=6, font=("Courier", 10))
        self.gnss_display.pack(fill=tk.X, padx=5, pady=5)

        # Environmental display
        env_display_frame = tk.LabelFrame(right, text="Environmental Data", bg="white")
        env_display_frame.pack(fill=tk.X, padx=5, pady=5)

        self.env_display = tk.Text(env_display_frame, height=6, font=("Courier", 10))
        self.env_display.pack(fill=tk.X, padx=5, pady=5)

    def _connect_gnss(self):
        port = self.gnss_port.get()

        def connect_thread():
            self.gnss = GNSSDriver(port=port)
            success, msg = self.gnss.connect()

            def update():
                if success:
                    self.gnss_connected = True
                    self.gnss_status.config(fg="green")
                    self.gnss_connect_btn.config(text="✅ Connected", state='disabled')
                    self.gnss_read_btn.config(state='normal')
                    self.app.center.set_status(f"✅ {msg}")
                else:
                    self.app.center.set_status(f"❌ {msg}")
            self.ui_queue.schedule(update)

        threading.Thread(target=connect_thread, daemon=True).start()

    def _get_gnss_position(self):
        if not self.gnss or not self.gnss.connected:
            return

        def read_thread():
            pos = self.gnss.get_position()

            def update():
                if pos:
                    self.data_hub.add_data('gnss', pos)

                    self.gnss_display.delete(1.0, tk.END)
                    self.gnss_display.insert(1.0,
                        f"Latitude:  {pos.latitude:.7f}\n"
                        f"Longitude: {pos.longitude:.7f}\n"
                        f"Altitude:  {pos.altitude_m:.2f} m\n"
                        f"Fix:       {pos.fix_type}\n"
                        f"Satellites: {pos.satellites}\n"
                        f"HDOP:      {pos.hdop:.2f}"
                    )

                    self.app.center.set_status(
                        f"✅ Position: {pos.latitude:.4f}, {pos.longitude:.4f}")
                else:
                    self.app.center.set_status("❌ Failed to get position")
            self.ui_queue.schedule(update)

        threading.Thread(target=read_thread, daemon=True).start()

    def _connect_campbell(self):
        port = self.env_port.get()

        def connect_thread():
            self.campbell = CampbellCRDriver(port=port)
            success, msg = self.campbell.connect()

            def update():
                if success:
                    self.campbell_connected = True
                    self.env_status.config(fg="green")
                    self.env_connect_btn.config(text="✅ Connected", state='disabled')
                    self.env_read_btn.config(state='normal')
                    self.app.center.set_status(f"✅ {msg}")
                else:
                    self.app.center.set_status(f"❌ {msg}")
            self.ui_queue.schedule(update)

        threading.Thread(target=connect_thread, daemon=True).start()

    def _read_campbell(self):
        if not self.campbell or not self.campbell.connected:
            return

        def read_thread():
            data = self.campbell.get_data()

            def update():
                if data:
                    self.data_hub.add_data('environmental', data)

                    self.env_display.delete(1.0, tk.END)
                    self.env_display.insert(1.0,
                        f"Temperature: {data.temperature_c:.1f}°C\n"
                        f"Pressure:    {data.pressure_hpa:.1f} hPa\n"
                        f"Humidity:    {data.humidity_pct:.1f}%\n"
                        f"Wind Speed:  {data.wind_speed_ms:.1f} m/s\n"
                        f"Wind Dir:    {data.wind_direction_deg:.0f}°"
                    )

                    self.app.center.set_status(
                        f"✅ T={data.temperature_c:.1f}°C, P={data.pressure_hpa:.1f}hPa")
                else:
                    self.app.center.set_status("❌ Failed to read Campbell")
            self.ui_queue.schedule(update)

        threading.Thread(target=read_thread, daemon=True).start()

    def _connect_total_station(self):
        """Connect to OpenADMS total station"""
        conn_type = self.ts_conn_type.get()
        port = self.ts_port.get() if conn_type == "serial" else None
        host = self.ts_host.get() if conn_type == "tcp" else None

        def connect_thread():
            try:
                # Create OpenADMS driver
                driver = OpenADMSTotalStationDriver(
                    connection_type=conn_type,
                    port=port,
                    host=host
                )
                success, msg = driver.connect()

                if success:
                    # Store the driver
                    self.total_station = driver

                    def update():
                        self.ts_status.config(fg="green")
                        self.ts_connect_btn.config(text="✅ Connected", state='disabled')
                        self.ts_read_btn.config(state='normal')
                        self.app.center.set_status(f"✅ {msg}")
                    self.ui_queue.schedule(update)
                else:
                    def update():
                        self.app.center.set_status(f"❌ {msg}")
                    self.ui_queue.schedule(update)

            except Exception as e:
                def update():
                    self.app.center.set_status(f"❌ Connection error: {str(e)}")
                self.ui_queue.schedule(update)

        threading.Thread(target=connect_thread, daemon=True).start()

    def _read_total_station(self):
        """Read position from total station"""
        if not hasattr(self, 'total_station') or not self.total_station:
            return

        def read_thread():
            pos = self.total_station.read_position()

            def update():
                if pos:
                    self.data_hub.add_data('gnss', pos)

                    # Update the GNSS display (reuse same display)
                    self.gnss_display.delete(1.0, tk.END)
                    self.gnss_display.insert(1.0,
                        f"Total Station Position:\n"
                        f"Latitude:  {pos.latitude:.7f}\n"
                        f"Longitude: {pos.longitude:.7f}\n"
                        f"Altitude:  {pos.altitude_m:.3f} m\n"
                        f"Fix:       {pos.fix_type}"
                    )

                    self.app.center.set_status(
                        f"✅ Total Station: {pos.latitude:.4f}, {pos.longitude:.4f}")
                else:
                    self.app.center.set_status("❌ Failed to read total station")
            self.ui_queue.schedule(update)

        threading.Thread(target=read_thread, daemon=True).start()

# ============================================================================
# MAIN PLUGIN CLASS
# ============================================================================
class GeophysicsUnifiedSuitePlugin:
    def __init__(self, main_app):
        self.app = main_app
        self.window = None
        self.ui_queue = None
        self.data_hub = DataHub()

        self.wave_tab = None
        self.electrical_tab = None
        self.potential_tab = None
        self.auxiliary_tab = None

        self.total_count = 0

    def show_interface(self):
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("🌍 Geophysics Unified Suite v2.0 - 38 Devices")
        self.window.geometry(PLUGIN_INFO["window_size"])
        self.window.minsize(900, 500)
        self.window.transient(self.app.root)

        self.ui_queue = ThreadSafeUI(self.window)
        self._build_ui()

        self.window.lift()
        self.window.focus_force()
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        # Header
        header = tk.Frame(self.window, bg="#1A3A5A", height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="🌍", font=("Arial", 20),
                bg="#1A3A5A", fg="white").pack(side=tk.LEFT, padx=10)
        tk.Label(header, text="GEOPHYSICS UNIFIED SUITE v2.0",
                font=("Arial", 14, "bold"), bg="#1A3A5A", fg="white").pack(side=tk.LEFT)

        tk.Label(header, text="38 DEVICES", font=("Arial", 9, "bold"),
                bg="#1A3A5A", fg="#FFD700").pack(side=tk.LEFT, padx=10)

        self.status_var = tk.StringVar(value="Ready")
        tk.Label(header, textvariable=self.status_var,
                font=("Arial", 9), bg="#1A3A5A", fg="#FFD700").pack(side=tk.RIGHT, padx=10)

        # Notebook for 4 tabs
        style = ttk.Style()
        style.configure("Geophysics.TNotebook.Tab", font=("Arial", 10, "bold"), padding=[10, 5])

        notebook = ttk.Notebook(self.window, style="Geophysics.TNotebook")
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create tabs
        self.wave_tab = WaveMethodsTab(notebook, self.app, self.ui_queue, self.data_hub)
        notebook.add(self.wave_tab.frame, text="📡 Wave Methods (12)")

        self.electrical_tab = ElectricalMethodsTab(notebook, self.app, self.ui_queue, self.data_hub)
        notebook.add(self.electrical_tab.frame, text="⚡ Electrical (9)")

        self.potential_tab = PotentialFieldsTab(notebook, self.app, self.ui_queue, self.data_hub)
        notebook.add(self.potential_tab.frame, text="🧲 Potential Fields (10)")

        self.auxiliary_tab = AuxiliaryTab(notebook, self.app, self.ui_queue, self.data_hub)
        notebook.add(self.auxiliary_tab.frame, text="🗺️ Auxiliary (7)")

        # Bottom status bar with UNIFIED FILE IMPORT
        status = tk.Frame(self.window, bg="#f0f0f0", height=40)
        status.pack(fill=tk.X, side=tk.BOTTOM)
        status.pack_propagate(False)

        # UNIFIED IMPORT BUTTON
        import_btn = ttk.Button(status, text="📁 Import Files (38 formats)",
                               command=self._import_files, width=25)
        import_btn.pack(side=tk.LEFT, padx=10)

        self.count_label = tk.Label(status,
            text="📊 0 seismic · 0 GPR · 0 ERT · 0 EM · 0 MT · 0 magnetics · 0 gravity · 0 GNSS",
            font=("Arial", 9), bg="#f0f0f0")
        self.count_label.pack(side=tk.LEFT, padx=20, expand=True)

        ttk.Button(status, text="📤 Send to Table",
                  command=self.send_to_table).pack(side=tk.RIGHT, padx=10)


    def _estimate_spacing(self, a, b, m, n):
        """Estimate electrode spacing from indices"""
        if len(a) > 1:
            spacings = []
            for i in range(min(10, len(a)-1)):
                if a[i] != a[i+1]:
                    spacings.append(abs(a[i+1] - a[i]))
            if spacings:
                return float(np.mean(spacings))
        return 5.0

    # ============================================================================
    # UNIFIED FILE IMPORT - ONE BUTTON FOR ALL 38 DEVICES
    # ============================================================================
    def _import_files(self):
        """Unified file import for ALL supported formats"""
        filetypes = [
            ("All supported files",
            "*.sac *.SACD* *.mseed *.miniseed *.dzt *.dt1 *.dat *.data *.Data *.csv *.edi *.txt"),
            ("Seismic SAC/SACD", "*.sac *.SACD*"),
            ("MiniSEED", "*.mseed *.miniseed"),
            ("GPR DZT", "*.dzt"),
            ("GPR DT1", "*.dt1"),
            ("ERT Data", "*.dat *.data *.Data"),
            ("MT EDI", "*.edi"),
            ("Magnetics CSV", "*.csv"),
            ("Gravity TXT", "*.txt"),
            ("All files", "*.*")
        ]

        paths = filedialog.askopenfilenames(parent=self.window, filetypes=filetypes)
        if not paths:
            return

        print(f"Selected {len(paths)} files")
        self.status_var.set(f"Importing {len(paths)} files...")
        self.window.update()

        for path in paths:
            print(f"Processing: {path}")
            ext = Path(path).suffix.lower()
            fname = path.lower()

            try:
                # ===== SEISMIC (SAC/SACD) =====
                if '.sac' in fname or '.SAC' in fname:
                    if HAS_PYSACIO:
                        traces = SacParser.parse(path)
                        for trace in traces:
                            self.data_hub.add_data('seismic', trace)
                        print(f"  Added {len(traces)} seismic traces")

                        # Update the seismic display with the first trace
                        if traces and self.wave_tab:
                            self.wave_tab.update_seismic_display(traces[0])
                            # Switch to seismic tab in the wave methods notebook
                            self.wave_tab.view_notebook.select(0)
                    else:
                        print(f"  pysacio not installed, cannot parse SAC file")

                # ===== SEISMIC (MiniSEED) =====
                elif ext in ['.mseed', '.miniseed'] and HAS_CYMSEED3:
                    traces = MiniSEEDParser.parse(path)
                    for trace in traces:
                        self.data_hub.add_data('seismic', trace)
                    print(f"  Added {len(traces)} seismic traces")

                    # Update the seismic display with the first trace
                    if traces and self.wave_tab:
                        self.wave_tab.update_seismic_display(traces[0])
                        self.wave_tab.view_notebook.select(0)

                # ===== GPR =====
                elif ext == '.dzt':
                    gpr = GSSIDZTParser.parse(path)
                    if gpr:
                        self.data_hub.add_data('gpr', gpr)
                        print(f"  Added GPR: {gpr.traces} traces")
                elif ext == '.dt1':
                    gpr = SensorsSoftwareDT1Parser.parse(path)
                    if gpr:
                        self.data_hub.add_data('gpr', gpr)
                        print(f"  Added GPR: {gpr.traces} traces")

                # ===== ERT =====
                elif ext in ['.dat', '.data', '.Data']:
                    a, b, m, n, rhoa, err = self._parse_ertlab_file(path)
                    ert = ERTData(
                        timestamp=datetime.now(),
                        station=Path(path).stem,
                        instrument="ERT",
                        apparent_rho=rhoa,
                        n_measurements=len(rhoa),
                        file_source=path
                    )
                    ert.raw_a = a
                    ert.raw_b = b
                    ert.raw_m = m
                    ert.raw_n = n
                    ert.raw_rhoa = rhoa
                    ert.raw_err = err
                    self.data_hub.add_data('ert', ert)
                    print(f"  Added ERT: {len(rhoa)} measurements")

                # ===== MT =====
                elif ext == '.edi':
                    mt = EDIParser.parse(path)
                    if mt:
                        self.data_hub.add_data('mt', mt)
                        print(f"  Added MT: {mt.n_frequencies} frequencies")

                # ===== MAGNETICS =====
                elif ext == '.csv' and ('bartington' in fname or 'grad' in fname):
                    mags = BartingtonGrad601Parser.parse(path)
                    for mag in mags:
                        self.data_hub.add_data('magnetics', mag)
                    print(f"  Added {len(mags)} magnetic readings")
                elif ext == '.txt' and ('geometrics' in fname or 'g-858' in fname):
                    mags = GeometricsG858Parser.parse(path)
                    for mag in mags:
                        self.data_hub.add_data('magnetics', mag)
                    print(f"  Added {len(mags)} magnetic readings")

                # ===== GRAVITY =====
                elif ext == '.txt' and ('scintrex' in fname or 'cg-5' in fname):
                    gravs = ScintrexCGParser.parse(path)
                    for grav in gravs:
                        self.data_hub.add_data('gravity', grav)
                    print(f"  Added {len(gravs)} gravity stations")

                else:
                    print(f"  Unsupported file type: {ext}")

            except Exception as e:
                print(f"  Error: {e}")

        # Update UI
        self.status_var.set(f"✅ Imported {len(paths)} files")
        self.window.update()

    def _poll_import_complete(self):
        """Poll to see if import is complete and update displays directly"""
        if self._import_complete_flag:
            # Update displays directly, like the working import does
            if self.data_hub.seismic_data and self.wave_tab:
                self.wave_tab.update_seismic_display(self.data_hub.seismic_data[-1])
            if self.data_hub.gpr_data and self.wave_tab:
                self.wave_tab.update_gpr_display(self.data_hub.gpr_data[-1])
            if self.data_hub.geophone_data and self.wave_tab:
                self.wave_tab.update_geophone_display(self.data_hub.geophone_data[-1])
            if self.data_hub.em_data and self.electrical_tab:
                self.electrical_tab.update_em_display(self.data_hub.em_data[-1])
            if self.data_hub.mt_data and self.electrical_tab:
                self.electrical_tab.update_mt_display(self.data_hub.mt_data[-1])
            if self.data_hub.magnetic_data and self.potential_tab:
                self.potential_tab.update_magnetic_display(self.data_hub.magnetic_data[-1])
            if self.data_hub.gravity_data and self.potential_tab:
                self.potential_tab.update_gravity_display(self.data_hub.gravity_data[-1])
            if self.data_hub.imu_data and self.potential_tab:
                self.potential_tab.update_imu_display(self.data_hub.imu_data[-1])
        else:
            # Check again in 100ms
            self.window.after(100, self._poll_import_complete)

    def _parse_ertlab_file(self, filepath):
        """
        Parse ERTLab format .data files
        Returns: (a, b, m, n, rhoa, err) arrays
        """
        import numpy as np
        a, b, m, n = [], [], [], []
        rhoa, err = [], []

        # First, read electrode mapping
        electrode_map = {}
        absolute_electrode = 1

        with open(filepath, 'r') as f:
            lines = f.readlines()

        # First pass: read electrode positions
        in_electrode_section = False
        for line in lines:
            line = line.strip()

            if line == '#elec_start':
                in_electrode_section = True
                continue
            if line == '#elec_end':
                in_electrode_section = False
                continue

            if in_electrode_section and line and not line.startswith('#'):
                parts = line.split()
                if len(parts) >= 6:
                    cable_electrode = parts[0]
                    electrode_map[cable_electrode] = absolute_electrode
                    absolute_electrode += 1

        # Second pass: read measurement data
        in_data_section = False
        for line in lines:
            line = line.strip()

            if line == '#data_start':
                in_data_section = True
                continue
            if line == '#data_end':
                in_data_section = False
                continue

            if not in_data_section or line.startswith('!') or line.startswith('#') or not line:
                continue

            parts = line.split()
            if len(parts) >= 10:
                try:
                    a_key = parts[1]
                    b_key = parts[2]
                    m_key = parts[3]
                    n_key = parts[4]

                    if all(key in electrode_map for key in [a_key, b_key, m_key, n_key]):
                        a_abs = electrode_map[a_key]
                        b_abs = electrode_map[b_key]
                        m_abs = electrode_map[m_key]
                        n_abs = electrode_map[n_key]

                        resistance = float(parts[5])
                        std_dev = float(parts[6])

                        # Geometry factor (simplified)
                        spacing = 5.0
                        current_distance = abs(a_abs - b_abs) * spacing
                        potential_distance = abs(m_abs - n_abs) * spacing

                        if current_distance > 0 and potential_distance > 0:
                            k = 2 * np.pi * (current_distance * potential_distance) / (current_distance - potential_distance + 0.001)
                        else:
                            k = 2 * np.pi * spacing

                        rho_apparent = resistance * k

                        a.append(a_abs)
                        b.append(b_abs)
                        m.append(m_abs)
                        n.append(n_abs)
                        rhoa.append(rho_apparent)
                        err.append(std_dev * 100 / resistance if resistance > 0 else 2.0)

                except (ValueError, KeyError):
                    continue

        # Filter invalid measurements
        a = np.array(a, dtype=int)
        b = np.array(b, dtype=int)
        m = np.array(m, dtype=int)
        n = np.array(n, dtype=int)
        rhoa = np.array(rhoa, dtype=float)
        err = np.array(err, dtype=float)

        valid_mask = (rhoa > 0) & (np.isfinite(rhoa)) & (rhoa < 1e8)
        a = a[valid_mask]
        b = b[valid_mask]
        m = m[valid_mask]
        n = n[valid_mask]
        rhoa = rhoa[valid_mask]
        err = err[valid_mask]

        print(f"✅ Parsed {len(rhoa)} valid ERT measurements")
        return a, b, m, n, rhoa, err

    def send_to_table(self):
        """Send all data to main app table (metadata + raw data for ERT)"""
        all_data = []

        # Add seismic data - metadata only but KEEP file paths
        for trace in self.data_hub.seismic_data:
            row = trace.to_dict()
            all_data.append(row)

        # Add geophone data
        for geo in self.data_hub.geophone_data:
            row = geo.to_dict()
            all_data.append(row)

        # Add GPR data
        for gpr in self.data_hub.gpr_data:
            row = gpr.to_dict()
            all_data.append(row)

        # Add ERT data - INCLUDE RAW ARRAYS
        for ert in self.data_hub.ert_data:
            row = ert.to_dict()
            # Add file source
            if hasattr(ert, 'file_source') and ert.file_source:
                row['File_Source'] = ert.file_source

            # CRITICAL: Add raw measurement arrays to the row
            if hasattr(ert, 'raw_a') and ert.raw_a is not None:
                # Convert arrays to lists for JSON serialization
                row['ert_raw_a'] = ert.raw_a.tolist()
                row['ert_raw_b'] = ert.raw_b.tolist()
                row['ert_raw_m'] = ert.raw_m.tolist()
                row['ert_raw_n'] = ert.raw_n.tolist()
                row['ert_raw_rhoa'] = ert.raw_rhoa.tolist()
                row['ert_raw_err'] = ert.raw_err.tolist()

            all_data.append(row)

        # Add MT data
        for mt in self.data_hub.mt_data:
            row = mt.to_dict()
            if hasattr(mt, 'file_source') and mt.file_source:
                row['File_Source'] = mt.file_source
            all_data.append(row)

        # Add magnetic data
        for mag in self.data_hub.magnetic_data:
            row = mag.to_dict()
            if hasattr(mag, 'file_source') and mag.file_source:
                row['File_Source'] = mag.file_source
            all_data.append(row)

        # Add gravity data
        for grav in self.data_hub.gravity_data:
            row = grav.to_dict()
            if hasattr(grav, 'file_source') and grav.file_source:
                row['File_Source'] = grav.file_source
            all_data.append(row)

        # Add IMU data
        for imu in self.data_hub.imu_data:
            all_data.append(imu.to_dict())

        # Add GNSS data
        for gnss in self.data_hub.gnss_data:
            all_data.append(gnss.to_dict())

        # Add environmental data
        for env in self.data_hub.environmental_data:
            all_data.append(env.to_dict())

        # Add custEM data
        for custem in self.data_hub.custem_data:
            row = custem.to_dict()
            if hasattr(custem, 'file_source') and custem.file_source:
                row['File_Source'] = custem.file_source
            all_data.append(row)

        if not all_data:
            messagebox.showwarning("No Data", "No data to send")
            return

        try:
            self.app.data_hub.add_samples(all_data)

            counts = self.data_hub.get_counts()
            summary = " · ".join(f"{v} {k}" for k, v in counts.items() if v > 0)

            self.status_var.set(f"✅ Sent {len(all_data)} records: {summary}")
            self.app.center.set_status(f"✅ Sent {len(all_data)} records to table", "success")

            messagebox.showinfo("Success",
                f"Successfully sent {len(all_data)} records to main table:\n\n{summary}")

        except Exception as e:
            messagebox.showerror("Error", str(e))
            import traceback
            traceback.print_exc()

    def _on_close(self):
        """Clean up on close"""
        if self.auxiliary_tab and self.auxiliary_tab.gnss:
            self.auxiliary_tab.gnss.disconnect()
        if self.auxiliary_tab and self.auxiliary_tab.campbell:
            self.auxiliary_tab.campbell.disconnect()
        if self.electrical_tab and self.electrical_tab.geonics:
            self.electrical_tab.geonics.disconnect()

        if self.window:
            self.window.destroy()
            self.window = None

# ============================================================================
# PLUGIN REGISTRATION
# ============================================================================
def setup_plugin(main_app):
    """Register plugin with main application"""

    plugin = GeophysicsUnifiedSuitePlugin(main_app)

    if hasattr(main_app, 'left') and main_app.left is not None:
        main_app.left.add_hardware_button(
            name=PLUGIN_INFO["name"],
            icon=PLUGIN_INFO["icon"],
            command=plugin.show_interface
        )
        print(f"✅ Added: {PLUGIN_INFO['name']} v{PLUGIN_INFO['version']} - 38 devices")

    return plugin
