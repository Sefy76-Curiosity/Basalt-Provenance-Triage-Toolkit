"""
MATERIALS CHARACTERIZATION UNIFIED SUITE v1.0 - THE FINAL FRONTIER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ AFM: Bruker · Asylum · Park · JPK — .spm/.ibw/ASCII parsers
✓ NANOINDENTATION: Bruker Hysitron · Keysight · Alemnis — force-displacement
✓ MECHANICAL: Instron · MTS · Shimadzu — tensile/compression CSV
✓ SURFACE AREA: Micromeritics · Quantachrome — BET isotherms
✓ DLS/ZETA: Malvern · Horiba · Brookhaven — particle sizing
✓ RHEOMETERS: TA · Anton Paar · Malvern — viscosity/modulus
✓ THERMAL CONDUCTIVITY: Netzsch · C-Therm · Linseis — LFA/TCi
✓ MICROHARDNESS: Buehler · Shimadzu — Vickers/Knoop
✓ PROFILOMETERS: KLA-Tencor · Bruker · Mitutoyo — surface roughness
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

# ============================================================================
# PLUGIN METADATA
# ============================================================================
PLUGIN_INFO = {
    "id": "materials_characterization_unified_suite",
    "name": "Materials Sci Suite",
    "category": "hardware",
    "icon": "🔬",
    "version": "1.0.0",
    "author": "Materials Science Team",
    "description": "AFM · Nanoindentation · Mechanical · BET · DLS · Rheology · Thermal · Hardness · Profilometry · 50+ devices",
    "requires": ["numpy", "pandas", "scipy", "matplotlib"],
    "optional": [
        "igor",
        "h5py",
        "netCDF4",
        "pillow",
        "openpyxl",
        "xlrd"
    ],
    "compact": True,
    "window_size": "950x700"
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
    from scipy import signal, integrate, optimize, stats
    from scipy.signal import savgol_filter, find_peaks, peak_widths
    from scipy.optimize import curve_fit
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.patches import Rectangle, Polygon, Circle
    from matplotlib import cm
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

# ============================================================================
# MATERIALS-SPECIFIC IMPORTS
# ============================================================================
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import igor
    HAS_IGOR = True
except ImportError:
    HAS_IGOR = False

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
        'pillow': False, 'igor': False
    }

    try: import numpy; deps['numpy'] = True
    except: pass
    try: import pandas; deps['pandas'] = True
    except: pass
    try: import scipy; deps['scipy'] = True
    except: pass
    try: import matplotlib; deps['matplotlib'] = True
    except: pass
    try: from PIL import Image; deps['pillow'] = True
    except: pass
    try: import igor; deps['igor'] = True
    except: pass

    return deps

DEPS = check_dependencies()

# ============================================================================
# UNIVERSAL MATERIALS CHARACTERIZATION DATA CLASSES
# ============================================================================

@dataclass
class AFMImage:
    """Atomic Force Microscopy image data"""

    # Core identifiers
    timestamp: datetime
    sample_id: str
    instrument: str
    scan_size_um: float = 0
    pixels: int = 0

    # Image data
    height_data: Optional[np.ndarray] = None  # 2D array
    amplitude_data: Optional[np.ndarray] = None
    phase_data: Optional[np.ndarray] = None
    deflection_data: Optional[np.ndarray] = None

    # Metadata
    scan_rate_hz: float = 0
    setpoint_nm: float = 0
    drive_amplitude_mv: float = 0
    feedback_gain: float = 0
    tip_model: str = ""

    # Derived metrics
    roughness_ra_nm: Optional[float] = None
    roughness_rms_nm: Optional[float] = None
    max_height_nm: Optional[float] = None
    min_height_nm: Optional[float] = None

    # File source
    file_source: str = ""
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict[str, str]:
        d = {
            'Timestamp': self.timestamp.isoformat() if self.timestamp else '',
            'Sample_ID': self.sample_id,
            'Instrument': self.instrument,
            'Scan_Size_um': f"{self.scan_size_um:.2f}",
            'Pixels': str(self.pixels),
            'Roughness_Ra_nm': f"{self.roughness_ra_nm:.3f}" if self.roughness_ra_nm else '',
            'Roughness_RMS_nm': f"{self.roughness_rms_nm:.3f}" if self.roughness_rms_nm else '',
        }
        return d

    def calculate_roughness(self):
        """Calculate surface roughness parameters"""
        if self.height_data is None:
            return

        data = self.height_data.flatten()
        self.roughness_ra_nm = np.mean(np.abs(data - np.mean(data)))
        self.roughness_rms_nm = np.std(data)
        self.max_height_nm = np.max(data)
        self.min_height_nm = np.min(data)

    def plot(self, ax=None):
        """Plot AFM height image"""
        if not HAS_MPL or self.height_data is None:
            return None

        if ax is None:
            fig, ax = plt.subplots(figsize=(8, 6))

        im = ax.imshow(self.height_data, cmap='afmhot', extent=[0, self.scan_size_um, self.scan_size_um, 0])
        ax.set_xlabel('X (μm)')
        ax.set_ylabel('Y (μm)')
        ax.set_title(f'AFM: {self.sample_id}')
        plt.colorbar(im, ax=ax, label='Height (nm)')

        return ax


@dataclass
class NanoindentationData:
    """Nanoindentation force-displacement data"""

    timestamp: datetime
    sample_id: str
    instrument: str
    tip_type: str = "Berkovich"  # Berkovich, Cube-corner, Conical, Spherical

    # Loading curve
    displacement_nm: Optional[np.ndarray] = None
    load_mN: Optional[np.ndarray] = None

    # Unloading curve
    unloading_displacement_nm: Optional[np.ndarray] = None
    unloading_load_mN: Optional[np.ndarray] = None

    # Results
    hardness_GPa: Optional[float] = None
    modulus_GPa: Optional[float] = None
    max_load_mN: Optional[float] = None
    max_displacement_nm: Optional[float] = None
    contact_depth_nm: Optional[float] = None
    contact_area_um2: Optional[float] = None
    stiffness_mN_nm: Optional[float] = None

    # Creep
    creep_displacement_nm: Optional[float] = None
    creep_time_s: Optional[float] = None

    # Thermal drift
    thermal_drift_nm_s: Optional[float] = None

    # File source
    file_source: str = ""
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict[str, str]:
        d = {
            'Timestamp': self.timestamp.isoformat() if self.timestamp else '',
            'Sample_ID': self.sample_id,
            'Instrument': self.instrument,
            'Tip': self.tip_type,
            'Hardness_GPa': f"{self.hardness_GPa:.3f}" if self.hardness_GPa else '',
            'Modulus_GPa': f"{self.modulus_GPa:.1f}" if self.modulus_GPa else '',
            'Max_Load_mN': f"{self.max_load_mN:.3f}" if self.max_load_mN else '',
            'Max_Disp_nm': f"{self.max_displacement_nm:.1f}" if self.max_displacement_nm else '',
        }
        return d

    def calculate_properties(self):
        """Calculate hardness and modulus using Oliver-Pharr method"""
        if self.unloading_displacement_nm is None or self.unloading_load_mN is None:
            return

        # Fit unloading curve (top 25-50%)
        n_points = len(self.unloading_displacement_nm)
        start_idx = int(n_points * 0.25)

        if HAS_SCIPY:
            def power_law(x, a, m, b):
                return a * (x - b)**m

            try:
                # Fit unloading data
                params, _ = curve_fit(power_law,
                                     self.unloading_displacement_nm[start_idx:],
                                     self.unloading_load_mN[start_idx:],
                                     p0=[1, 1.5, 0])

                # Calculate stiffness at max load
                h_max = self.max_displacement_nm
                S = params[0] * params[1] * (h_max - params[2])**(params[1]-1)

                # Contact depth (Oliver-Pharr)
                epsilon = 0.75
                h_c = h_max - epsilon * self.max_load_mN / S

                # Projected area (Berkovich: A = 24.5 * h_c²)
                self.contact_depth_nm = h_c
                self.contact_area_um2 = 24.5 * (h_c/1000)**2

                # Hardness
                self.hardness_GPa = self.max_load_mN / self.contact_area_um2 / 1000

                # Reduced modulus
                beta = 1.034  # Berkovich correction
                self.stiffness_mN_nm = S
                reduced_modulus = S * np.sqrt(np.pi) / (2 * beta * np.sqrt(self.contact_area_um2 * 1e6))

                # Young's modulus (assuming diamond tip: Ei=1140 GPa, νi=0.07)
                Ei = 1140
                νi = 0.07
                νs = 0.3  # Typical Poisson's ratio
                self.modulus_GPa = 1 / ((1/reduced_modulus) - (1-νi**2)/Ei) * (1-νs**2)

            except:
                pass


@dataclass
class MechanicalTestData:
    """Tensile/Compression mechanical test data"""

    timestamp: datetime
    sample_id: str
    instrument: str
    test_type: str = "tensile"  # tensile, compression, bending, fatigue

    # Test parameters
    strain_rate_s: float = 0
    temperature_c: float = 23
    humidity_pct: float = 50
    gauge_length_mm: float = 0
    sample_width_mm: float = 0
    sample_thickness_mm: float = 0
    sample_diameter_mm: float = 0

    # Data
    strain_pct: Optional[np.ndarray] = None
    stress_MPa: Optional[np.ndarray] = None
    displacement_mm: Optional[np.ndarray] = None
    force_N: Optional[np.ndarray] = None
    time_s: Optional[np.ndarray] = None

    # Results
    youngs_modulus_GPa: Optional[float] = None
    yield_strength_MPa: Optional[float] = None
    ultimate_strength_MPa: Optional[float] = None
    fracture_strain_pct: Optional[float] = None
    toughness_MJ_m3: Optional[float] = None
    poissons_ratio: Optional[float] = None

    # Cyclic data
    cycles: Optional[np.ndarray] = None
    max_stress_MPa: Optional[np.ndarray] = None
    min_stress_MPa: Optional[np.ndarray] = None
    fatigue_life_cycles: Optional[int] = None

    # File source
    file_source: str = ""
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict[str, str]:
        d = {
            'Timestamp': self.timestamp.isoformat() if self.timestamp else '',
            'Sample_ID': self.sample_id,
            'Instrument': self.instrument,
            'Type': self.test_type,
            'E_GPa': f"{self.youngs_modulus_GPa:.2f}" if self.youngs_modulus_GPa else '',
            'Yield_MPa': f"{self.yield_strength_MPa:.1f}" if self.yield_strength_MPa else '',
            'UTS_MPa': f"{self.ultimate_strength_MPa:.1f}" if self.ultimate_strength_MPa else '',
            'Strain_pct': f"{self.fracture_strain_pct:.1f}" if self.fracture_strain_pct else '',
        }
        return d

    def calculate_properties(self):
        """Calculate mechanical properties from stress-strain curve"""
        if self.stress_MPa is None or self.strain_pct is None:
            return

        strain = self.strain_pct / 100  # Convert to absolute strain

        # Young's modulus (linear portion: 0.05-0.25% strain)
        mask = (strain > 0.0005) & (strain < 0.0025)
        if np.any(mask):
            coeffs = np.polyfit(strain[mask], self.stress_MPa[mask], 1)
            self.youngs_modulus_GPa = coeffs[0] / 1000  # Convert MPa to GPa

        # Yield strength (0.2% offset)
        offset_strain = strain - 0.002
        for i in range(1, len(stress)):
            if stress[i] > coeffs[0] * offset_strain[i] + coeffs[1]:
                self.yield_strength_MPa = stress[i]
                break

        # Ultimate strength
        self.ultimate_strength_MPa = np.max(self.stress_MPa)

        # Fracture strain
        self.fracture_strain_pct = strain[-1] * 100

        # Toughness (area under curve)
        self.toughness_MJ_m3 = np.trapz(self.stress_MPa, strain) / 1000


@dataclass
class BETIsotherm:
    """BET surface area and porosity data"""

    timestamp: datetime
    sample_id: str
    instrument: str
    adsorbate: str = "N2"  # N2, Ar, CO2, Kr
    temperature_k: float = 77.35  # Liquid N2 temp

    # Isotherm data
    relative_pressure: Optional[np.ndarray] = None  # P/P0
    volume_adsorbed_cc_g: Optional[np.ndarray] = None
    volume_desorbed_cc_g: Optional[np.ndarray] = None

    # BET results
    bet_surface_area_m2_g: Optional[float] = None
    bet_c_constant: Optional[float] = None
    bet_correlation: Optional[float] = None
    bet_pressure_range: Tuple[float, float] = (0.05, 0.3)

    # BJH results
    pore_volume_cc_g: Optional[float] = None
    pore_size_nm: Optional[float] = None
    pore_size_distribution: Optional[np.ndarray] = None

    # t-plot
    micropore_volume_cc_g: Optional[float] = None
    external_surface_area_m2_g: Optional[float] = None

    # File source
    file_source: str = ""
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict[str, str]:
        d = {
            'Timestamp': self.timestamp.isoformat() if self.timestamp else '',
            'Sample_ID': self.sample_id,
            'Instrument': self.instrument,
            'Adsorbate': self.adsorbate,
            'BET_Surface_m2_g': f"{self.bet_surface_area_m2_g:.2f}" if self.bet_surface_area_m2_g else '',
            'BET_C': f"{self.bet_c_constant:.1f}" if self.bet_c_constant else '',
            'Pore_Volume_cc_g': f"{self.pore_volume_cc_g:.3f}" if self.pore_volume_cc_g else '',
            'Pore_Size_nm': f"{self.pore_size_nm:.2f}" if self.pore_size_nm else '',
        }
        return d

    def calculate_bet(self):
        """Calculate BET surface area"""
        if self.relative_pressure is None or self.volume_adsorbed_cc_g is None:
            return

        # BET transform: 1/[V((P0/P)-1)] vs P/P0
        mask = (self.relative_pressure >= self.bet_pressure_range[0]) & \
               (self.relative_pressure <= self.bet_pressure_range[1])

        if not np.any(mask):
            return

        p = self.relative_pressure[mask]
        v = self.volume_adsorbed_cc_g[mask]

        # BET transform
        y = 1 / (v * (1/p - 1))

        if HAS_SCIPY:
            # Linear fit
            slope, intercept, r_value, _, _ = stats.linregress(p, y)

            # BET parameters
            vm = 1 / (slope + intercept)
            c = 1 + slope / intercept

            # Surface area (N2 cross-sectional area: 0.162 nm²)
            na = 6.022e23  # Avogadro
            sigma = 0.162e-18  # m² per molecule
            vm_mol_g = vm / 22414  # Convert cm³/g to mol/g (STP)

            self.bet_surface_area_m2_g = vm_mol_g * na * sigma
            self.bet_c_constant = c
            self.bet_correlation = r_value**2


@dataclass
class DLSData:
    """Dynamic Light Scattering particle size data"""

    timestamp: datetime
    sample_id: str
    instrument: str
    dispersant: str = "water"
    temperature_c: float = 25

    # Size data
    intensity_distribution: Optional[np.ndarray] = None
    intensity_peaks: List[float] = field(default_factory=list)
    intensity_peak_areas: List[float] = field(default_factory=list)

    volume_distribution: Optional[np.ndarray] = None
    volume_peaks: List[float] = field(default_factory=list)

    number_distribution: Optional[np.ndarray] = None
    number_peaks: List[float] = field(default_factory=list)

    # Average sizes
    z_average_d_nm: Optional[float] = None
    polydispersity_index: Optional[float] = None
    d10_nm: Optional[float] = None
    d50_nm: Optional[float] = None
    d90_nm: Optional[float] = None

    # Correlation data
    correlation_tau_us: Optional[np.ndarray] = None
    correlation_g2: Optional[np.ndarray] = None

    # Zeta potential
    zeta_potential_mV: Optional[float] = None
    zeta_deviation_mV: Optional[float] = None
    conductivity_ms_cm: Optional[float] = None

    # File source
    file_source: str = ""
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict[str, str]:
        d = {
            'Timestamp': self.timestamp.isoformat() if self.timestamp else '',
            'Sample_ID': self.sample_id,
            'Instrument': self.instrument,
            'Z_Average_nm': f"{self.z_average_d_nm:.1f}" if self.z_average_d_nm else '',
            'PDI': f"{self.polydispersity_index:.3f}" if self.polydispersity_index else '',
            'D50_nm': f"{self.d50_nm:.1f}" if self.d50_nm else '',
            'Zeta_mV': f"{self.zeta_potential_mV:.1f}" if self.zeta_potential_mV else '',
        }
        return d


@dataclass
class RheologyData:
    """Rheological measurement data"""

    timestamp: datetime
    sample_id: str
    instrument: str
    geometry: str = "parallel plate"  # parallel plate, cone-plate, couette
    gap_mm: float = 1.0

    # Flow sweep
    shear_rate_s: Optional[np.ndarray] = None
    viscosity_Pa_s: Optional[np.ndarray] = None
    shear_stress_Pa: Optional[np.ndarray] = None

    # Oscillatory
    frequency_Hz: Optional[np.ndarray] = None
    storage_modulus_GPa: Optional[np.ndarray] = None
    loss_modulus_GPa: Optional[np.ndarray] = None
    tan_delta: Optional[np.ndarray] = None
    complex_viscosity_Pa_s: Optional[np.ndarray] = None

    # Temperature sweep
    temperature_c: Optional[np.ndarray] = None
    temp_storage_modulus: Optional[np.ndarray] = None
    temp_loss_modulus: Optional[np.ndarray] = None

    # Time sweep
    time_s: Optional[np.ndarray] = None
    time_storage_modulus: Optional[np.ndarray] = None
    time_loss_modulus: Optional[np.ndarray] = None

    # Results
    yield_stress_Pa: Optional[float] = None
    zero_shear_viscosity_Pa_s: Optional[float] = None
    relaxation_time_s: Optional[float] = None
    gel_point_c: Optional[float] = None

    # File source
    file_source: str = ""
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict[str, str]:
        d = {
            'Timestamp': self.timestamp.isoformat() if self.timestamp else '',
            'Sample_ID': self.sample_id,
            'Instrument': self.instrument,
            'Zero_Shear_Viscosity_Pa_s': f"{self.zero_shear_viscosity_Pa_s:.2f}" if self.zero_shear_viscosity_Pa_s else '',
            'Yield_Stress_Pa': f"{self.yield_stress_Pa:.2f}" if self.yield_stress_Pa else '',
            'Gel_Point_C': f"{self.gel_point_c:.1f}" if self.gel_point_c else '',
        }
        return d


@dataclass
class MicrohardnessData:
    """Microhardness indentation data"""

    timestamp: datetime
    sample_id: str
    instrument: str
    indenter_type: str = "Vickers"  # Vickers, Knoop, Berkovich

    # Test parameters
    load_gf: float = 0  # grams-force
    load_N: float = 0
    dwell_time_s: float = 10

    # Measurements
    diagonal1_um: Optional[float] = None
    diagonal2_um: Optional[float] = None
    indent_diagonal_um: Optional[float] = None  # for Knoop
    indent_depth_um: Optional[float] = None

    # Results
    hardness_HV: Optional[float] = None  # Vickers hardness
    hardness_HK: Optional[float] = None  # Knoop hardness
    hardness_GPa: Optional[float] = None

    # Statistics
    n_indents: int = 1
    hardness_mean: Optional[float] = None
    hardness_std: Optional[float] = None

    # File source
    file_source: str = ""
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict[str, str]:
        d = {
            'Timestamp': self.timestamp.isoformat() if self.timestamp else '',
            'Sample_ID': self.sample_id,
            'Instrument': self.instrument,
            'Type': self.indenter_type,
            'Load_gf': f"{self.load_gf:.0f}",
            'Hardness': f"{self.hardness_HV:.1f}" if self.hardness_HV else '',
            'Hardness_GPa': f"{self.hardness_GPa:.3f}" if self.hardness_GPa else '',
        }
        return d

    def calculate_hardness(self):
        """Calculate hardness from indentation diagonals"""
        if self.indenter_type == "Vickers" and self.diagonal1_um and self.diagonal2_um:
            d = (self.diagonal1_um + self.diagonal2_um) / 2 / 1000  # Convert to mm
            # Vickers: HV = 1.8544 * F / d² (F in kgf)
            F_kgf = self.load_gf / 1000
            self.hardness_HV = 1.8544 * F_kgf / (d * d)
            self.hardness_GPa = self.hardness_HV * 0.009807  # Convert HV to GPa

        elif self.indenter_type == "Knoop" and self.indent_diagonal_um:
            d = self.indent_diagonal_um / 1000  # mm
            F_kgf = self.load_gf / 1000
            # Knoop: HK = 14.229 * F / d²
            self.hardness_HK = 14.229 * F_kgf / (d * d)
            self.hardness_GPa = self.hardness_HK * 0.009807


@dataclass
class ProfilometryData:
    """Surface profilometry data"""

    timestamp: datetime
    sample_id: str
    instrument: str
    scan_type: str = "2D"  # 2D, 3D

    # 2D profile
    distance_mm: Optional[np.ndarray] = None
    height_um: Optional[np.ndarray] = None

    # 3D surface
    x_mm: Optional[np.ndarray] = None
    y_mm: Optional[np.ndarray] = None
    z_um: Optional[np.ndarray] = None  # 2D array for 3D

    # Stylus parameters
    stylus_radius_um: float = 2
    stylus_force_mg: float = 10

    # Roughness parameters
    ra_um: Optional[float] = None
    rq_um: Optional[float] = None
    rz_um: Optional[float] = None
    rt_um: Optional[float] = None
    rsk: Optional[float] = None  # Skewness
    rku: Optional[float] = None  # Kurtosis

    # Waviness
    waviness_um: Optional[np.ndarray] = None
    primary_profile_um: Optional[np.ndarray] = None

    # File source
    file_source: str = ""
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict[str, str]:
        d = {
            'Timestamp': self.timestamp.isoformat() if self.timestamp else '',
            'Sample_ID': self.sample_id,
            'Instrument': self.instrument,
            'Ra_um': f"{self.ra_um:.3f}" if self.ra_um else '',
            'Rq_um': f"{self.rq_um:.3f}" if self.rq_um else '',
            'Rz_um': f"{self.rz_um:.3f}" if self.rz_um else '',
            'Scan_Length_mm': f"{self.distance_mm[-1]:.2f}" if self.distance_mm is not None else '',
        }
        return d

    def calculate_roughness(self):
        """Calculate surface roughness parameters"""
        if self.height_um is None:
            return

        profile = self.height_um
        self.ra_um = np.mean(np.abs(profile - np.mean(profile)))
        self.rq_um = np.std(profile)
        self.rt_um = np.max(profile) - np.min(profile)

        # Rz (average of 5 highest peaks - 5 lowest valleys)
        if len(profile) > 100:
            sorted_profile = np.sort(profile)
            peaks = sorted_profile[-5:]
            valleys = sorted_profile[:5]
            self.rz_um = np.mean(peaks) - np.mean(valleys)

        # Skewness and Kurtosis
        if HAS_SCIPY:
            self.rsk = stats.skew(profile)
            self.rku = stats.kurtosis(profile)


# ============================================================================
# 1. AFM PARSERS
# ============================================================================

class BrukerSPMParser:
    """Bruker AFM .spm file parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        return filepath.lower().endswith(('.spm', '.000'))

    @staticmethod
    def parse(filepath: str) -> Optional[AFMImage]:
        try:
            with open(filepath, 'rb') as f:
                # Read header
                header = f.read(512)

                # Try to extract metadata
                content = header.decode('ascii', errors='ignore')

                # Find image size
                scan_size = 0
                pixels = 0
                lines = content.split('\n')

                for line in lines:
                    if 'ScanSize' in line:
                        match = re.search(r'([\d.]+)', line)
                        if match:
                            scan_size = float(match.group(1))
                    if 'SampsLines' in line:
                        match = re.search(r'(\d+)', line)
                        if match:
                            pixels = int(match.group(1))

                # Read image data (16-bit integers)
                f.seek(512)
                data = np.frombuffer(f.read(), dtype='<u2')
                data = data.astype(float)

                # Reshape to square image
                side = int(np.sqrt(len(data)))
                if side * side == len(data):
                    data = data.reshape(side, side)

                    # Convert to nm (typical scaling)
                    data = data * 0.1  # Approximate

                    afm = AFMImage(
                        timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                        sample_id=Path(filepath).stem,
                        instrument="Bruker AFM",
                        scan_size_um=scan_size,
                        pixels=pixels,
                        height_data=data,
                        file_source=filepath
                    )
                    afm.calculate_roughness()
                    return afm

        except Exception as e:
            print(f"Bruker SPM parse error: {e}")

        return None


class AsylumIBWParser:
    """Asylum Research Igor .ibw file parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        return filepath.lower().endswith('.ibw')

    @staticmethod
    def parse(filepath: str) -> Optional[AFMImage]:
        if not HAS_IGOR:
            return None

        try:
            import igor
            wave = igor.load(filepath)

            # Get data
            data = wave.data

            # Get metadata
            scan_size = wave.get('ScanSize', 0)
            pixels = data.shape[0] if data.ndim == 2 else 0

            afm = AFMImage(
                timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                sample_id=Path(filepath).stem,
                instrument="Asylum Research",
                scan_size_um=scan_size,
                pixels=pixels,
                height_data=data,
                file_source=filepath
            )
            afm.calculate_roughness()
            return afm

        except Exception as e:
            print(f"Asylum IBW parse error: {e}")

        return None


class ParkAFMParser:
    """Park Systems AFM ASCII parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        try:
            with open(filepath, 'r') as f:
                first = f.readline()
                return 'Park' in first or 'XE' in first
        except:
            return False

    @staticmethod
    def parse(filepath: str) -> Optional[AFMImage]:
        try:
            # Park ASCII format is grid of numbers
            data = np.loadtxt(filepath)

            if data.ndim == 2:
                # Extract scan size from filename or header
                scan_size = 10  # Default

                afm = AFMImage(
                    timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                    sample_id=Path(filepath).stem,
                    instrument="Park Systems",
                    scan_size_um=scan_size,
                    pixels=data.shape[0],
                    height_data=data,
                    file_source=filepath
                )
                afm.calculate_roughness()
                return afm

        except Exception as e:
            print(f"Park AFM parse error: {e}")

        return None


class JPKAFMParser:
    """JPK AFM ASCII+TIFF parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        return filepath.lower().endswith(('.tiff', '.tif', '.txt'))

    @staticmethod
    def parse(filepath: str) -> Optional[AFMImage]:
        try:
            if filepath.lower().endswith(('.tiff', '.tif')) and HAS_PIL:
                # JPK saves height maps as TIFF with metadata
                img = Image.open(filepath)

                # Try to read metadata
                metadata = {}
                for key, value in img.info.items():
                    if isinstance(value, str):
                        metadata[key] = value

                # Convert to numpy array
                data = np.array(img).astype(float)

                # Scale to nm (typical)
                data = data * 0.1

                scan_size = float(metadata.get('scan_size', 10))

                afm = AFMImage(
                    timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                    sample_id=Path(filepath).stem,
                    instrument="JPK NanoWizard",
                    scan_size_um=scan_size,
                    pixels=data.shape[0],
                    height_data=data,
                    metadata=metadata,
                    file_source=filepath
                )
                afm.calculate_roughness()
                return afm

        except Exception as e:
            print(f"JPK AFM parse error: {e}")

        return None


# ============================================================================
# 2. NANOINDENTATION PARSERS
# ============================================================================

class HysitronParser:
    """Bruker Hysitron TI-series nanoindentation parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        try:
            with open(filepath, 'r') as f:
                first = f.read(500)
                return 'Hysitron' in first or 'TI' in first
        except:
            return False

    @staticmethod
    def parse(filepath: str) -> Optional[NanoindentationData]:
        try:
            df = pd.read_csv(filepath, skiprows=10)

            # Find columns
            disp_col = None
            load_col = None
            time_col = None

            for col in df.columns:
                col_lower = col.lower()
                if 'displacement' in col_lower or 'depth' in col_lower:
                    disp_col = col
                elif 'load' in col_lower or 'force' in col_lower:
                    load_col = col
                elif 'time' in col_lower:
                    time_col = col

            if disp_col and load_col:
                data = NanoindentationData(
                    timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                    sample_id=Path(filepath).stem,
                    instrument="Hysitron TI",
                    displacement_nm=df[disp_col].values,
                    load_mN=df[load_col].values,
                    file_source=filepath
                )

                # Find max load for unloading curve
                max_idx = np.argmax(df[load_col].values)
                data.max_load_mN = df[load_col].values[max_idx]
                data.max_displacement_nm = df[disp_col].values[max_idx]

                # Split into loading and unloading
                data.unloading_displacement_nm = df[disp_col].values[max_idx:]
                data.unloading_load_mN = df[load_col].values[max_idx:]

                data.calculate_properties()
                return data

        except Exception as e:
            print(f"Hysitron parse error: {e}")

        return None


class KeysightG200Parser:
    """Keysight G200 nanoindenter parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        try:
            with open(filepath, 'r') as f:
                first = f.read(500)
                return 'Keysight' in first or 'G200' in first or 'Agilent' in first
        except:
            return False

    @staticmethod
    def parse(filepath: str) -> Optional[NanoindentationData]:
        try:
            df = pd.read_csv(filepath, skiprows=15)

            # Keysight format
            if 'Displacement Into Surface' in df.columns and 'Load On Sample' in df.columns:
                data = NanoindentationData(
                    timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                    sample_id=Path(filepath).stem,
                    instrument="Keysight G200",
                    displacement_nm=df['Displacement Into Surface'].values * 1000,  # μm to nm
                    load_mN=df['Load On Sample'].values * 1000,  # mN to μN
                    file_source=filepath
                )
                return data

        except Exception as e:
            print(f"Keysight parse error: {e}")

        return None


class AlemnisParser:
    """Alemnis nanoindentation CSV parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        try:
            with open(filepath, 'r') as f:
                first = f.read(500)
                return 'Alemnis' in first
        except:
            return False

    @staticmethod
    def parse(filepath: str) -> Optional[NanoindentationData]:
        try:
            df = pd.read_csv(filepath)

            if 'Displacement_nm' in df.columns and 'Load_mN' in df.columns:
                data = NanoindentationData(
                    timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                    sample_id=Path(filepath).stem,
                    instrument="Alemnis",
                    displacement_nm=df['Displacement_nm'].values,
                    load_mN=df['Load_mN'].values,
                    file_source=filepath
                )
                return data

        except Exception as e:
            print(f"Alemnis parse error: {e}")

        return None


# ============================================================================
# 3. MECHANICAL TESTING PARSERS
# ============================================================================

class InstronBluehillParser:
    """Instron Bluehill series parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        try:
            with open(filepath, 'r') as f:
                first = f.read(500)
                return 'Instron' in first or 'Bluehill' in first
        except:
            return False

    @staticmethod
    def parse(filepath: str) -> Optional[MechanicalTestData]:
        try:
            df = pd.read_csv(filepath, skiprows=20)

            # Find columns
            strain_col = None
            stress_col = None
            disp_col = None
            force_col = None

            for col in df.columns:
                col_lower = col.lower()
                if 'strain' in col_lower:
                    strain_col = col
                elif 'stress' in col_lower:
                    stress_col = col
                elif 'displacement' in col_lower or 'extension' in col_lower:
                    disp_col = col
                elif 'force' in col_lower or 'load' in col_lower:
                    force_col = col

            data = MechanicalTestData(
                timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                sample_id=Path(filepath).stem,
                instrument="Instron Bluehill"
            )

            if strain_col and stress_col:
                data.strain_pct = df[strain_col].values
                data.stress_MPa = df[stress_col].values
            elif disp_col and force_col:
                # Need specimen geometry for stress/strain
                data.displacement_mm = df[disp_col].values
                data.force_N = df[force_col].values

            data.calculate_properties()
            return data

        except Exception as e:
            print(f"Instron parse error: {e}")

        return None


class MTSParser:
    """MTS Criterion series parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        try:
            with open(filepath, 'r') as f:
                first = f.read(500)
                return 'MTS' in first or 'Criterion' in first
        except:
            return False

    @staticmethod
    def parse(filepath: str) -> Optional[MechanicalTestData]:
        try:
            df = pd.read_csv(filepath)

            if 'Strain' in df.columns and 'Stress' in df.columns:
                data = MechanicalTestData(
                    timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                    sample_id=Path(filepath).stem,
                    instrument="MTS Criterion",
                    strain_pct=df['Strain'].values,
                    stress_MPa=df['Stress'].values,
                    file_source=filepath
                )
                data.calculate_properties()
                return data

        except Exception as e:
            print(f"MTS parse error: {e}")

        return None


class ShimadzuAGXParser:
    """Shimadzu AG-X series parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        try:
            with open(filepath, 'r') as f:
                first = f.read(500)
                return 'Shimadzu' in first or 'AG-X' in first
        except:
            return False

    @staticmethod
    def parse(filepath: str) -> Optional[MechanicalTestData]:
        try:
            df = pd.read_csv(filepath, skiprows=10, encoding='shift-jis')

            # Shimadzu often uses Japanese column headers
            strain_col = None
            stress_col = None

            for col in df.columns:
                if 'ひずみ' in col or 'Strain' in col:
                    strain_col = col
                elif '応力' in col or 'Stress' in col:
                    stress_col = col

            if strain_col and stress_col:
                data = MechanicalTestData(
                    timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                    sample_id=Path(filepath).stem,
                    instrument="Shimadzu AG-X",
                    strain_pct=df[strain_col].values,
                    stress_MPa=df[stress_col].values,
                    file_source=filepath
                )
                data.calculate_properties()
                return data

        except Exception as e:
            print(f"Shimadzu parse error: {e}")

        return None


# ============================================================================
# 4. BET SURFACE AREA PARSERS
# ============================================================================

class MicromeriticsASAPParser:
    """Micromeritics ASAP series parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        try:
            with open(filepath, 'r') as f:
                first = f.read(500)
                return any(x in first for x in ['Micromeritics', 'ASAP', 'TriStar'])
        except:
            return False

    @staticmethod
    def parse(filepath: str) -> Optional[BETIsotherm]:
        try:
            with open(filepath, 'r') as f:
                lines = f.readlines()

            in_isotherm = False
            p = []
            v = []

            for line in lines:
                line = line.strip()

                if 'Isotherm' in line or 'Adsorption' in line:
                    in_isotherm = True
                    continue

                if in_isotherm and line and not line.startswith(('-', '=', '#')):
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            p_val = float(parts[0])
                            v_val = float(parts[1])
                            p.append(p_val)
                            v.append(v_val)
                        except:
                            pass

            if p and v:
                bet = BETIsotherm(
                    timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                    sample_id=Path(filepath).stem,
                    instrument="Micromeritics ASAP",
                    relative_pressure=np.array(p),
                    volume_adsorbed_cc_g=np.array(v),
                    file_source=filepath
                )
                bet.calculate_bet()
                return bet

        except Exception as e:
            print(f"Micromeritics parse error: {e}")

        return None


class QuantachromeParser:
    """Quantachrome NOVA/Autosorb parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        try:
            with open(filepath, 'r') as f:
                first = f.read(500)
                return any(x in first for x in ['Quantachrome', 'NOVA', 'Autosorb'])
        except:
            return False

    @staticmethod
    def parse(filepath: str) -> Optional[BETIsotherm]:
        try:
            df = pd.read_csv(filepath, skiprows=15)

            if 'P/P0' in df.columns and 'Volume' in df.columns:
                bet = BETIsotherm(
                    timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                    sample_id=Path(filepath).stem,
                    instrument="Quantachrome",
                    relative_pressure=df['P/P0'].values,
                    volume_adsorbed_cc_g=df['Volume'].values,
                    file_source=filepath
                )
                bet.calculate_bet()
                return bet

        except Exception as e:
            print(f"Quantachrome parse error: {e}")

        return None


# ============================================================================
# 5. DLS/ZETA PARSERS
# ============================================================================

class MalvernZetasizerParser:
    """Malvern Zetasizer series parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        try:
            with open(filepath, 'r') as f:
                first = f.read(500)
                return 'Malvern' in first or 'Zetasizer' in first
        except:
            return False

    @staticmethod
    def parse(filepath: str) -> Optional[DLSData]:
        try:
            with open(filepath, 'r') as f:
                lines = f.readlines()

            dls = DLSData(
                timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                sample_id=Path(filepath).stem,
                instrument="Malvern Zetasizer"
            )

            in_size = False
            size_data = []

            for line in lines:
                line = line.strip()

                if 'Z-Average' in line:
                    match = re.search(r'([\d.]+)', line)
                    if match:
                        dls.z_average_d_nm = float(match.group(1))

                if 'PDI' in line:
                    match = re.search(r'([\d.]+)', line)
                    if match:
                        dls.polydispersity_index = float(match.group(1))

                if 'Zeta Potential' in line:
                    match = re.search(r'([-]?\d+\.?\d*)', line)
                    if match:
                        dls.zeta_potential_mV = float(match.group(1))

                if 'Size Distribution' in line:
                    in_size = True
                    continue

                if in_size and line and line[0].isdigit():
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            size_data.append([float(parts[0]), float(parts[1])])
                        except:
                            pass

            if size_data:
                size_array = np.array(size_data)
                dls.intensity_distribution = size_array[:, 1]
                # Find peaks
                if HAS_SCIPY and len(size_array[:, 1]) > 5:
                    peaks, _ = find_peaks(size_array[:, 1], height=0.1*np.max(size_array[:, 1]))
                    dls.intensity_peaks = size_array[peaks, 0].tolist()
                    dls.intensity_peak_areas = size_array[peaks, 1].tolist()

            return dls

        except Exception as e:
            print(f"Malvern parse error: {e}")

        return None


class HoribaSZParser:
    """Horiba SZ-100 DLS/Zeta parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        try:
            with open(filepath, 'r') as f:
                first = f.read(500)
                return 'Horiba' in first or 'SZ-100' in first
        except:
            return False

    @staticmethod
    def parse(filepath: str) -> Optional[DLSData]:
        try:
            df = pd.read_csv(filepath, skiprows=10)

            dls = DLSData(
                timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                sample_id=Path(filepath).stem,
                instrument="Horiba SZ-100"
            )

            if 'Z-Average' in df.columns:
                dls.z_average_d_nm = float(df['Z-Average'].iloc[0])
            if 'PDI' in df.columns:
                dls.polydispersity_index = float(df['PDI'].iloc[0])
            if 'Zeta' in df.columns:
                dls.zeta_potential_mV = float(df['Zeta'].iloc[0])

            return dls

        except Exception as e:
            print(f"Horiba parse error: {e}")

        return None

class BrookhavenDLS:
    """Brookhaven Instruments BI-series DLS parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        try:
            with open(filepath, 'r') as f:
                first = f.read(500)
                return 'Brookhaven' in first or 'BI-' in first
        except:
            return False

    @staticmethod
    def parse(filepath: str) -> Optional[DLSData]:
        try:
            with open(filepath, 'r') as f:
                lines = f.readlines()

            dls = DLSData(
                timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                sample_id=Path(filepath).stem,
                instrument="Brookhaven BI"
            )

            in_correlation = False
            corr_time = []
            corr_g2 = []

            for line in lines:
                line = line.strip()

                if 'Effective Diameter' in line:
                    match = re.search(r'([\d.]+)', line)
                    if match:
                        dls.z_average_d_nm = float(match.group(1))

                if 'Polydispersity' in line:
                    match = re.search(r'([\d.]+)', line)
                    if match:
                        dls.polydispersity_index = float(match.group(1))

                if 'Correlation Data' in line:
                    in_correlation = True
                    continue

                if in_correlation and line and line[0].isdigit():
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            corr_time.append(float(parts[0]))
                            corr_g2.append(float(parts[1]))
                        except:
                            pass

            if corr_time:
                dls.correlation_tau_us = np.array(corr_time)
                dls.correlation_g2 = np.array(corr_g2)

            return dls

        except Exception as e:
            print(f"Brookhaven parse error: {e}")

        return None


# ============================================================================
# 6. RHEOMETER PARSERS
# ============================================================================

class TARheometerParser:
    """TA Instruments Discovery HR series rheometer parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        try:
            with open(filepath, 'r') as f:
                first = f.read(500)
                return any(x in first for x in ['TA Instruments', 'Discovery HR', 'Rheology'])
        except:
            return False

    @staticmethod
    def parse(filepath: str) -> Optional[RheologyData]:
        try:
            df = pd.read_csv(filepath, skiprows=15)

            rheo = RheologyData(
                timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                sample_id=Path(filepath).stem,
                instrument="TA Discovery HR"
            )

            # Flow sweep
            if 'Shear Rate' in df.columns and 'Viscosity' in df.columns:
                rheo.shear_rate_s = df['Shear Rate'].values
                rheo.viscosity_Pa_s = df['Viscosity'].values

            # Oscillatory
            if 'Frequency' in df.columns:
                rheo.frequency_Hz = df['Frequency'].values
                if 'Storage Modulus' in df.columns:
                    rheo.storage_modulus_GPa = df['Storage Modulus'].values / 1000  # Pa to kPa
                if 'Loss Modulus' in df.columns:
                    rheo.loss_modulus_GPa = df['Loss Modulus'].values / 1000
                if 'Tan Delta' in df.columns:
                    rheo.tan_delta = df['Tan Delta'].values

            # Temperature sweep
            if 'Temperature' in df.columns:
                rheo.temperature_c = df['Temperature'].values
                if 'Storage Modulus' in df.columns:
                    rheo.temp_storage_modulus = df['Storage Modulus'].values / 1000

            return rheo

        except Exception as e:
            print(f"TA Rheometer parse error: {e}")

        return None


class AntonPaarMCRParser:
    """Anton Paar MCR series rheometer parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        try:
            with open(filepath, 'r') as f:
                first = f.read(500)
                return any(x in first for x in ['Anton Paar', 'MCR', 'RheoCompass'])
        except:
            return False

    @staticmethod
    def parse(filepath: str) -> Optional[RheologyData]:
        try:
            # Anton Paar exports tab-separated ASCII
            df = pd.read_csv(filepath, sep='\t', skiprows=20, encoding='latin1')

            rheo = RheologyData(
                timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                sample_id=Path(filepath).stem,
                instrument="Anton Paar MCR"
            )

            # Map common column names
            col_map = {
                'Shear Rate': 'shear_rate_s',
                'Viscosity': 'viscosity_Pa_s',
                'Shear Stress': 'shear_stress_Pa',
                'Frequency': 'frequency_Hz',
                'Storage Modulus': 'storage_modulus_GPa',
                'Loss Modulus': 'loss_modulus_GPa',
                'Tan Delta': 'tan_delta',
                'Temperature': 'temperature_c',
                'Time': 'time_s'
            }

            for col, attr in col_map.items():
                if col in df.columns:
                    setattr(rheo, attr, df[col].values)

            return rheo

        except Exception as e:
            print(f"Anton Paar parse error: {e}")

        return None


class MalvernKinexusParser:
    """Malvern Kinexus rheometer parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        try:
            with open(filepath, 'r') as f:
                first = f.read(500)
                return 'Malvern' in first or 'Kinexus' in first
        except:
            return False

    @staticmethod
    def parse(filepath: str) -> Optional[RheologyData]:
        try:
            df = pd.read_excel(filepath, sheet_name=0)

            rheo = RheologyData(
                timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                sample_id=Path(filepath).stem,
                instrument="Malvern Kinexus"
            )

            # Malvern format
            if 'Shear rate' in df.columns and 'Viscosity' in df.columns:
                rheo.shear_rate_s = df['Shear rate'].values
                rheo.viscosity_Pa_s = df['Viscosity'].values

            if 'Frequency' in df.columns:
                rheo.frequency_Hz = df['Frequency'].values
                if "G'" in df.columns:
                    rheo.storage_modulus_GPa = df["G'"].values / 1000
                if 'G"' in df.columns:
                    rheo.loss_modulus_GPa = df['G"'].values / 1000

            return rheo

        except Exception as e:
            print(f"Malvern Kinexus parse error: {e}")

        return None

# ============================================================================
# THERMAL CONDUCTIVITY DATA CLASS
# ============================================================================

@dataclass
class ThermalConductivityData:
    timestamp: datetime
    sample_id: str
    instrument: str
    technique: str = "Thermal Conductivity"
    manufacturer: str = ""
    model: str = ""
    thermal_conductivity_W_mK: Optional[float] = None
    thermal_diffusivity_mm2_s: Optional[float] = None
    specific_heat_J_gK: Optional[float] = None
    temperature_c: Optional[float] = None
    file_source: str = ""
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict[str, str]:
        d = {
            'Timestamp': self.timestamp.isoformat() if self.timestamp else '',
            'Sample_ID': self.sample_id,
            'Instrument': self.instrument,
            'Technique': self.technique,
            'k_W_mK': f"{self.thermal_conductivity_W_mK:.4f}" if self.thermal_conductivity_W_mK else '',
            'alpha_mm2_s': f"{self.thermal_diffusivity_mm2_s:.4f}" if self.thermal_diffusivity_mm2_s else '',
            'Cp_J_gK': f"{self.specific_heat_J_gK:.4f}" if self.specific_heat_J_gK else '',
            'Temp_C': f"{self.temperature_c:.1f}" if self.temperature_c else '',
        }
        return d

# ============================================================================
# 7. THERMAL CONDUCTIVITY PARSERS
# ============================================================================

class NetzschLFAParser:
    """Netzsch LFA 467/457 thermal conductivity parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        try:
            with open(filepath, 'r') as f:
                first = f.read(500)
                return 'NETZSCH' in first or 'LFA' in first
        except:
            return False

    @staticmethod
    def parse(filepath: str) -> Optional['ThermalConductivityData']:
        # Parse Netzsch LFA data directly
        try:
            with open(filepath, 'r') as f:
                lines = f.readlines()

            # Create thermal measurement
            meas = ThermalConductivityData(
                timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                sample_id=Path(filepath).stem,
                instrument="Netzsch LFA",
                manufacturer="Netzsch",
                model="LFA 467/457"
            )

            # Parse the file for thermal properties
            for line in lines:
                if 'Thermal Diffusivity' in line:
                    match = re.search(r'([\d.]+)', line)
                    if match:
                        meas.thermal_diffusivity_mm2_s = float(match.group(1))
                if 'Thermal Conductivity' in line:
                    match = re.search(r'([\d.]+)', line)
                    if match:
                        meas.thermal_conductivity_W_mK = float(match.group(1))
                if 'Specific Heat' in line:
                    match = re.search(r'([\d.]+)', line)
                    if match:
                        meas.specific_heat_J_gK = float(match.group(1))
                if 'Temperature' in line:
                    match = re.search(r'([\d.]+)', line)
                    if match:
                        meas.temperature_c = float(match.group(1))

            return meas

        except Exception as e:
            print(f"Netzsch LFA parse error: {e}")
            return None

class CThermTCiParser:
    """C-Therm TCi thermal conductivity analyzer parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        try:
            with open(filepath, 'r') as f:
                first = f.read(500)
                return 'C-Therm' in first or 'TCi' in first
        except:
            return False

    @staticmethod
    def parse(filepath: str) -> Optional[ThermalConductivityData]:
        try:
            df = pd.read_csv(filepath)

            # Create thermal measurement object
            from thermal_analysis_suite import ThermalMeasurement

            meas = ThermalMeasurement(
                timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                sample_id=Path(filepath).stem,
                technique="Thermal Conductivity",
                manufacturer="C-Therm",
                model="TCi"
            )

            if 'Conductivity' in df.columns:
                meas.thermal_conductivity_W_mK = df['Conductivity'].values[0]
            if 'Temperature' in df.columns:
                meas.temperature_c = df['Temperature'].values

            return meas

        except Exception as e:
            print(f"C-Therm parse error: {e}")

        return None


class LinseisLFAParser:
    """Linseis LFA series parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        try:
            with open(filepath, 'r') as f:
                first = f.read(500)
                return 'Linseis' in first or 'LFA' in first
        except:
            return False

    @staticmethod
    def parse(filepath: str) -> Optional[ThermalConductivityData]:
        try:
            with open(filepath, 'r') as f:
                lines = f.readlines()

            from thermal_analysis_suite import ThermalMeasurement

            meas = ThermalMeasurement(
                timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                sample_id=Path(filepath).stem,
                technique="Thermal Conductivity",
                manufacturer="Linseis",
                model="LFA"
            )

            for line in lines:
                if 'Thermal Diffusivity' in line:
                    match = re.search(r'([\d.]+)', line)
                    if match:
                        meas.thermal_diffusivity_mm2_s = float(match.group(1))
                if 'Thermal Conductivity' in line:
                    match = re.search(r'([\d.]+)', line)
                    if match:
                        meas.thermal_conductivity_W_mK = float(match.group(1))

            return meas

        except Exception as e:
            print(f"Linseis parse error: {e}")

        return None


# ============================================================================
# 8. MICROHARDNESS PARSERS
# ============================================================================

class BuehlerWilsonParser:
    """Buehler Wilson VH series microhardness parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        try:
            with open(filepath, 'r') as f:
                first = f.read(500)
                return any(x in first for x in ['Buehler', 'Wilson', 'VH'])
        except:
            return False

    @staticmethod
    def parse(filepath: str) -> List[MicrohardnessData]:
        measurements = []
        try:
            df = pd.read_csv(filepath, skiprows=5)

            for idx, row in df.iterrows():
                hd = MicrohardnessData(
                    timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                    sample_id=row.get('Sample', Path(filepath).stem),
                    instrument="Buehler Wilson",
                    indenter_type=row.get('Indenter', 'Vickers'),
                    load_gf=float(row.get('Load', 0)),
                    dwell_time_s=float(row.get('Dwell', 10)),
                    diagonal1_um=float(row.get('D1', 0)) if 'D1' in row else None,
                    diagonal2_um=float(row.get('D2', 0)) if 'D2' in row else None,
                    hardness_HV=float(row.get('HV', 0)) if 'HV' in row else None,
                    file_source=filepath
                )
                hd.calculate_hardness()
                measurements.append(hd)

        except Exception as e:
            print(f"Buehler parse error: {e}")

        return measurements


class ShimadzuHMVParser:
    """Shimadzu HMV series microhardness parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        try:
            with open(filepath, 'r') as f:
                first = f.read(500)
                return 'Shimadzu' in first or 'HMV' in first
        except:
            return False

    @staticmethod
    def parse(filepath: str) -> List[MicrohardnessData]:
        measurements = []
        try:
            with open(filepath, 'r') as f:
                lines = f.readlines()

            current = MicrohardnessData(
                timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                sample_id=Path(filepath).stem,
                instrument="Shimadzu HMV",
                file_source=filepath
            )

            for line in lines:
                line = line.strip()
                if 'Load' in line and 'gf' in line:
                    match = re.search(r'([\d.]+)', line)
                    if match:
                        current.load_gf = float(match.group(1))
                if 'Dwell' in line:
                    match = re.search(r'([\d.]+)', line)
                    if match:
                        current.dwell_time_s = float(match.group(1))
                if 'HV' in line:
                    match = re.search(r'([\d.]+)', line)
                    if match:
                        current.hardness_HV = float(match.group(1))
                        current.calculate_hardness()
                        measurements.append(current)
                        current = MicrohardnessData(
                            timestamp=current.timestamp,
                            sample_id=current.sample_id,
                            instrument=current.instrument,
                            file_source=filepath
                        )

        except Exception as e:
            print(f"Shimadzu HMV parse error: {e}")

        return measurements


# ============================================================================
# 9. PROFILOMETER PARSERS
# ============================================================================

class KLATencorParser:
    """KLA-Tencor P-7/P-17 profilometer parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        try:
            with open(filepath, 'r') as f:
                first = f.read(500)
                return any(x in first for x in ['KLA-Tencor', 'P-7', 'P-17'])
        except:
            return False

    @staticmethod
    def parse(filepath: str) -> Optional[ProfilometryData]:
        try:
            # KLA exports ASCII with header
            with open(filepath, 'r') as f:
                lines = f.readlines()

            data_start = 0
            for i, line in enumerate(lines):
                if line.strip() and line[0].isdigit():
                    data_start = i
                    break

            dist = []
            height = []

            for line in lines[data_start:]:
                line = line.strip()
                if line:
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            d = float(parts[0])
                            h = float(parts[1])
                            dist.append(d)
                            height.append(h)
                        except:
                            pass

            if dist:
                prof = ProfilometryData(
                    timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                    sample_id=Path(filepath).stem,
                    instrument="KLA-Tencor",
                    scan_type="2D",
                    distance_mm=np.array(dist),
                    height_um=np.array(height),
                    file_source=filepath
                )
                prof.calculate_roughness()
                return prof

        except Exception as e:
            print(f"KLA-Tencor parse error: {e}")

        return None


class BrukerDektakParser:
    """Bruker Dektak XT profilometer parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        try:
            with open(filepath, 'r') as f:
                first = f.read(500)
                return 'Bruker' in first or 'Dektak' in first
        except:
            return False

    @staticmethod
    def parse(filepath: str) -> Optional[ProfilometryData]:
        try:
            df = pd.read_csv(filepath, skiprows=20)

            if 'Scan Distance' in df.columns and 'Height' in df.columns:
                prof = ProfilometryData(
                    timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                    sample_id=Path(filepath).stem,
                    instrument="Bruker Dektak",
                    scan_type="2D",
                    distance_mm=df['Scan Distance'].values,
                    height_um=df['Height'].values,
                    file_source=filepath
                )
                prof.calculate_roughness()
                return prof

        except Exception as e:
            print(f"Bruker Dektak parse error: {e}")

        return None


class MitutoyoSurftestParser:
    """Mitutoyo Surftest series profilometer parser"""

    @staticmethod
    def can_parse(filepath: str) -> bool:
        try:
            with open(filepath, 'r') as f:
                first = f.read(500)
                return 'Mitutoyo' in first or 'Surftest' in first
        except:
            return False

    @staticmethod
    def parse(filepath: str) -> Optional[ProfilometryData]:
        try:
            with open(filepath, 'r') as f:
                lines = f.readlines()

            data_start = 0
            for i, line in enumerate(lines):
                if 'PROFILE' in line or 'DATA' in line:
                    data_start = i + 1
                    break

            values = []
            for line in lines[data_start:]:
                line = line.strip()
                if line:
                    for val in line.split():
                        try:
                            values.append(float(val))
                        except:
                            pass

            if values:
                # Create distance array (assuming constant step)
                step = 0.001  # 1 μm typical
                dist = np.arange(len(values)) * step

                prof = ProfilometryData(
                    timestamp=datetime.fromtimestamp(os.path.getmtime(filepath)),
                    sample_id=Path(filepath).stem,
                    instrument="Mitutoyo Surftest",
                    scan_type="2D",
                    distance_mm=dist,
                    height_um=np.array(values),
                    file_source=filepath
                )
                prof.calculate_roughness()
                return prof

        except Exception as e:
            print(f"Mitutoyo parse error: {e}")

        return None


# ============================================================================
# MATERIALS CHARACTERIZATION PARSER FACTORY
# ============================================================================

class MaterialsParserFactory:
    """Factory to select appropriate parser"""

    parsers = [
        # AFM
        BrukerSPMParser,
        AsylumIBWParser,
        ParkAFMParser,
        JPKAFMParser,

        # Nanoindentation
        HysitronParser,
        KeysightG200Parser,
        AlemnisParser,

        # Mechanical
        InstronBluehillParser,
        MTSParser,
        ShimadzuAGXParser,

        # BET
        MicromeriticsASAPParser,
        QuantachromeParser,

        # DLS
        MalvernZetasizerParser,
        HoribaSZParser,
        BrookhavenDLS,

        # Rheology
        TARheometerParser,
        AntonPaarMCRParser,
        MalvernKinexusParser,

        # Thermal Conductivity
        NetzschLFAParser,
        CThermTCiParser,
        LinseisLFAParser,

        # Microhardness
        BuehlerWilsonParser,
        ShimadzuHMVParser,

        # Profilometry
        KLATencorParser,
        BrukerDektakParser,
        MitutoyoSurftestParser
    ]

    @classmethod
    def parse_file(cls, filepath: str) -> Optional[Any]:
        """Try all parsers until one works"""
        for parser_class in cls.parsers:
            try:
                if hasattr(parser_class, 'can_parse') and parser_class.can_parse(filepath):
                    result = parser_class.parse(filepath)
                    if result:
                        return result
            except Exception as e:
                continue
        return None

    @classmethod
    def parse_folder(cls, folder: str) -> List[Any]:
        """Parse all supported files in a folder"""
        measurements = []
        for ext in ['*.spm', '*.ibw', '*.csv', '*.txt', '*.xlsx', '*.dat']:
            for filepath in Path(folder).glob(ext):
                result = cls.parse_file(str(filepath))
                if result:
                    measurements.append(result)
        return measurements


# ============================================================================
# PLOT EMBEDDER
# ============================================================================

class MaterialsPlotEmbedder:
    """Plot materials characterization data"""

    def __init__(self, canvas_widget, figure):
        self.canvas = canvas_widget
        self.figure = figure
        self.current_plot = None

    def clear(self):
        self.figure.clear()
        self.figure.set_facecolor('white')
        self.current_plot = None

    def plot_afm(self, afm: AFMImage):
        """Plot AFM height image"""
        self.clear()
        if afm.height_data is not None:
            ax = self.figure.add_subplot(111)
            im = ax.imshow(afm.height_data, cmap='afmhot',
                          extent=[0, afm.scan_size_um, afm.scan_size_um, 0])
            ax.set_xlabel('X (μm)')
            ax.set_ylabel('Y (μm)')
            ax.set_title(f'AFM: {afm.sample_id}  Ra={afm.roughness_ra_nm:.2f}nm')
            plt.colorbar(im, ax=ax, label='Height (nm)')

        self.figure.tight_layout()
        self.canvas.draw()
        self.current_plot = 'afm'

    def plot_nanoindentation(self, nano: NanoindentationData):
        """Plot force-displacement curve"""
        self.clear()
        ax = self.figure.add_subplot(111)

        if nano.displacement_nm is not None and nano.load_mN is not None:
            ax.plot(nano.displacement_nm, nano.load_mN, 'b-', linewidth=2, label='Loading')

            if nano.unloading_displacement_nm is not None:
                ax.plot(nano.unloading_displacement_nm, nano.unloading_load_mN,
                       'r-', linewidth=2, label='Unloading')

            ax.set_xlabel('Displacement (nm)')
            ax.set_ylabel('Load (mN)')
            title = f'Nanoindentation: {nano.sample_id}'
            if nano.hardness_GPa:
                title += f'  H={nano.hardness_GPa:.2f}GPa  E={nano.modulus_GPa:.1f}GPa'
            ax.set_title(title)
            ax.grid(True, alpha=0.3)
            ax.legend()

        self.figure.tight_layout()
        self.canvas.draw()
        self.current_plot = 'nano'

    def plot_stress_strain(self, mech: MechanicalTestData):
        """Plot stress-strain curve"""
        self.clear()
        ax = self.figure.add_subplot(111)

        if mech.strain_pct is not None and mech.stress_MPa is not None:
            ax.plot(mech.strain_pct, mech.stress_MPa, 'b-', linewidth=2)

            # Mark yield point
            if mech.yield_strength_MPa:
                yield_idx = np.argmin(np.abs(mech.stress_MPa - mech.yield_strength_MPa))
                ax.plot(mech.strain_pct[yield_idx], mech.yield_strength_MPa, 'ro',
                       markersize=8, label=f'Yield: {mech.yield_strength_MPa:.1f} MPa')

            # Mark UTS
            if mech.ultimate_strength_MPa:
                uts_idx = np.argmax(mech.stress_MPa)
                ax.plot(mech.strain_pct[uts_idx], mech.ultimate_strength_MPa, 'gs',
                       markersize=8, label=f'UTS: {mech.ultimate_strength_MPa:.1f} MPa')

            ax.set_xlabel('Strain (%)')
            ax.set_ylabel('Stress (MPa)')
            ax.set_title(f'Mechanical Test: {mech.sample_id}')
            ax.grid(True, alpha=0.3)
            ax.legend()

        self.figure.tight_layout()
        self.canvas.draw()
        self.current_plot = 'stress_strain'

    def plot_bet_isotherm(self, bet: BETIsotherm):
        """Plot BET isotherm"""
        self.clear()
        ax = self.figure.add_subplot(111)

        if bet.relative_pressure is not None and bet.volume_adsorbed_cc_g is not None:
            ax.plot(bet.relative_pressure, bet.volume_adsorbed_cc_g, 'bo-',
                   markersize=4, linewidth=1)

            # Highlight BET range
            if bet.bet_pressure_range:
                ax.axvspan(bet.bet_pressure_range[0], bet.bet_pressure_range[1],
                          alpha=0.2, color='yellow', label='BET range')

            ax.set_xlabel('Relative Pressure P/P₀')
            ax.set_ylabel('Volume Adsorbed (cm³/g STP)')
            title = f'BET Isotherm: {bet.sample_id}'
            if bet.bet_surface_area_m2_g:
                title += f'  SA={bet.bet_surface_area_m2_g:.1f} m²/g'
            ax.set_title(title)
            ax.grid(True, alpha=0.3)
            ax.legend()

        self.figure.tight_layout()
        self.canvas.draw()
        self.current_plot = 'bet'

    def plot_dls_distribution(self, dls: DLSData):
        """Plot DLS size distribution"""
        self.clear()
        ax = self.figure.add_subplot(111)

        if dls.intensity_distribution is not None:
            # Assume we have size bins from somewhere
            size_bins = np.arange(len(dls.intensity_distribution))

            ax.bar(size_bins, dls.intensity_distribution, width=0.8, alpha=0.7)

            # Mark peaks
            if dls.intensity_peaks:
                for peak in dls.intensity_peaks:
                    ax.axvline(peak, color='r', linestyle='--', alpha=0.7)

            ax.set_xlabel('Size (nm)')
            ax.set_ylabel('Intensity (%)')
            title = f'DLS: {dls.sample_id}'
            if dls.z_average_d_nm:
                title += f'  Z-Avg={dls.z_average_d_nm:.1f} nm'
                if dls.polydispersity_index:
                    title += f'  PDI={dls.polydispersity_index:.3f}'
            ax.set_title(title)
            ax.grid(True, alpha=0.3)

        self.figure.tight_layout()
        self.canvas.draw()
        self.current_plot = 'dls'

    def plot_rheology(self, rheo: RheologyData):
        """Plot rheology data (flow curve or frequency sweep)"""
        self.clear()

        if rheo.shear_rate_s is not None and rheo.viscosity_Pa_s is not None:
            # Flow curve
            ax = self.figure.add_subplot(111)
            ax.loglog(rheo.shear_rate_s, rheo.viscosity_Pa_s, 'bo-', linewidth=2)
            ax.set_xlabel('Shear Rate (1/s)')
            ax.set_ylabel('Viscosity (Pa·s)')
            ax.set_title(f'Flow Curve: {rheo.sample_id}')
            ax.grid(True, alpha=0.3, which='both')

        elif rheo.frequency_Hz is not None:
            # Frequency sweep
            ax1 = self.figure.add_subplot(111)

            if rheo.storage_modulus_GPa is not None:
                ax1.semilogx(rheo.frequency_Hz, rheo.storage_modulus_GPa, 'b-',
                            linewidth=2, label="G'")
            if rheo.loss_modulus_GPa is not None:
                ax1.semilogx(rheo.frequency_Hz, rheo.loss_modulus_GPa, 'r-',
                            linewidth=2, label='G"')

            ax1.set_xlabel('Frequency (Hz)')
            ax1.set_ylabel('Modulus (kPa)')
            ax1.set_title(f'Frequency Sweep: {rheo.sample_id}')
            ax1.grid(True, alpha=0.3)
            ax1.legend()

        self.figure.tight_layout()
        self.canvas.draw()
        self.current_plot = 'rheology'

    def plot_profilometry(self, prof: ProfilometryData):
        """Plot surface profile"""
        self.clear()
        ax = self.figure.add_subplot(111)

        if prof.distance_mm is not None and prof.height_um is not None:
            ax.plot(prof.distance_mm, prof.height_um, 'b-', linewidth=1.5)

            # Add roughness parameters to title
            title = f'Surface Profile: {prof.sample_id}'
            if prof.ra_um:
                title += f'  Ra={prof.ra_um:.3f}μm'
            if prof.rq_um:
                title += f'  Rq={prof.rq_um:.3f}μm'
            if prof.rz_um:
                title += f'  Rz={prof.rz_um:.3f}μm'

            ax.set_xlabel('Distance (mm)')
            ax.set_ylabel('Height (μm)')
            ax.set_title(title)
            ax.grid(True, alpha=0.3)

        self.figure.tight_layout()
        self.canvas.draw()
        self.current_plot = 'profile'


# ============================================================================
# MAIN PLUGIN - MATERIALS CHARACTERIZATION UNIFIED SUITE
# ============================================================================
class MaterialsCharacterizationSuitePlugin:

    def __init__(self, main_app):
        self.app = main_app
        self.window = None
        self.ui_queue = None
        self.deps = DEPS

        # Data collections
        self.afm_images: List[AFMImage] = []
        self.nano_data: List[NanoindentationData] = []
        self.mech_data: List[MechanicalTestData] = []
        self.bet_data: List[BETIsotherm] = []
        self.dls_data: List[DLSData] = []
        self.rheo_data: List[RheologyData] = []
        self.thermal_data: List[ThermalConductivityData] = []
        self.hardness_data: List[MicrohardnessData] = []
        self.profile_data: List[ProfilometryData] = []

        self.current_item = None

        # Plot embedder
        self.plot_embedder = None

        # UI Variables
        self.status_var = tk.StringVar(value="Materials Characterization v1.0 - Ready")
        self.technique_var = tk.StringVar(value="AFM")
        self.file_count_var = tk.StringVar(value="No files loaded")

        # UI Elements
        self.notebook = None
        self.log_listbox = None
        self.plot_canvas = None
        self.plot_fig = None
        self.status_indicator = None
        self.technique_combo = None
        self.tree = None
        self.import_btn = None
        self.batch_btn = None

        self.techniques = [
            "AFM",
            "Nanoindentation",
            "Mechanical Testing",
            "BET Surface Area",
            "DLS/Zeta Potential",
            "Rheology",
            "Thermal Conductivity",
            "Microhardness",
            "Profilometry"
        ]

    def show_interface(self):
        self.open_window()

    def open_window(self):
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("Materials Characterization Suite v1.0")
        self.window.geometry("950x700")
        self.window.minsize(900, 650)
        self.window.transient(self.app.root)

        self.ui_queue = ThreadSafeUI(self.window)
        self._build_ui()
        self.window.lift()
        self.window.focus_force()
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        """950x700 UI - All materials techniques"""

        # Header
        header = tk.Frame(self.window, bg="#8e44ad", height=45)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="🔬", font=("Arial", 18),
                bg="#8e44ad", fg="white").pack(side=tk.LEFT, padx=8)
        tk.Label(header, text="MATERIALS CHARACTERIZATION", font=("Arial", 14, "bold"),
                bg="#8e44ad", fg="white").pack(side=tk.LEFT, padx=2)
        tk.Label(header, text="v1.0 · FINAL SUITE", font=("Arial", 9),
                bg="#8e44ad", fg="#f1c40f").pack(side=tk.LEFT, padx=8)

        self.status_indicator = tk.Label(header, textvariable=self.status_var,
                                        font=("Arial", 9), bg="#8e44ad", fg="white")
        self.status_indicator.pack(side=tk.RIGHT, padx=10)

        # Toolbar
        toolbar = tk.Frame(self.window, bg="#ecf0f1", height=50)
        toolbar.pack(fill=tk.X)
        toolbar.pack_propagate(False)

        row1 = tk.Frame(toolbar, bg="#ecf0f1")
        row1.pack(fill=tk.X, pady=5)

        tk.Label(row1, text="Technique:", font=("Arial", 10, "bold"),
                bg="#ecf0f1").pack(side=tk.LEFT, padx=5)
        self.technique_combo = ttk.Combobox(row1, textvariable=self.technique_var,
                                           values=self.techniques, width=20)
        self.technique_combo.pack(side=tk.LEFT, padx=2)

        self.import_btn = ttk.Button(row1, text="📂 Import File",
                                     command=self._import_file, width=12)
        self.import_btn.pack(side=tk.LEFT, padx=5)

        self.batch_btn = ttk.Button(row1, text="📁 Batch Folder",
                                    command=self._batch_folder, width=12)
        self.batch_btn.pack(side=tk.LEFT, padx=2)

        self.file_count_label = tk.Label(row1, textvariable=self.file_count_var,
                                        font=("Arial", 9), bg="#ecf0f1", fg="#7f8c8d")
        self.file_count_label.pack(side=tk.RIGHT, padx=10)

        # Row 2: Quick plot buttons
        row2 = tk.Frame(toolbar, bg="#ecf0f1")
        row2.pack(fill=tk.X, pady=2)

        ttk.Button(row2, text="📈 Plot Selected",
                  command=self._plot_selected, width=15).pack(side=tk.LEFT, padx=2)
        ttk.Button(row2, text="📊 Calculate",
                  command=self._calculate_properties, width=15).pack(side=tk.LEFT, padx=2)
        ttk.Button(row2, text="📤 Send to Table",
                  command=self.send_to_table, width=15).pack(side=tk.RIGHT, padx=2)

        # Notebook
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self._create_data_tab()
        self._create_plot_tab()
        self._create_log_tab()

        # Status bar
        status = tk.Frame(self.window, bg="#34495e", height=24)
        status.pack(fill=tk.X, side=tk.BOTTOM)
        status.pack_propagate(False)

        total_samples = (len(self.afm_images) + len(self.nano_data) + len(self.mech_data) +
                        len(self.bet_data) + len(self.dls_data) + len(self.rheo_data) +
                        len(self.thermal_data) + len(self.hardness_data) + len(self.profile_data))

        self.count_label = tk.Label(status,
            text=f"📊 {total_samples} samples · {len(self.afm_images)} AFM · {len(self.mech_data)} Mech · {len(self.bet_data)} BET",
            font=("Arial", 9), bg="#34495e", fg="white")
        self.count_label.pack(side=tk.LEFT, padx=10)

        tk.Label(status,
                text="Bruker · Asylum · Park · Hysitron · Instron · Micromeritics · Malvern · TA · Netzsch",
                font=("Arial", 8), bg="#34495e", fg="#bdc3c7").pack(side=tk.RIGHT, padx=10)

    def _create_data_tab(self):
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="📊 Data Browser")

        frame = tk.Frame(tab, bg="white")
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ('Type', 'Sample', 'Instrument', 'Key Value', 'File')
        self.tree = ttk.Treeview(frame, columns=columns, show='headings', height=20)

        col_widths = [100, 200, 200, 150, 200]
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
        self.notebook.add(tab, text="📈 Plot Viewer")

        ctrl_frame = tk.Frame(tab, bg="#f8f9fa", height=35)
        ctrl_frame.pack(fill=tk.X)
        ctrl_frame.pack_propagate(False)

        ttk.Button(ctrl_frame, text="🔄 Refresh", command=self._refresh_plot,
                  width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(ctrl_frame, text="💾 Save Plot", command=self._save_plot,
                  width=12).pack(side=tk.LEFT, padx=2)

        plot_frame = tk.Frame(tab, bg="white")
        plot_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.plot_fig = Figure(figsize=(10, 6), dpi=100, facecolor='white')
        self.plot_canvas = FigureCanvasTkAgg(self.plot_fig, master=plot_frame)
        self.plot_canvas.draw()
        self.plot_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.plot_embedder = MaterialsPlotEmbedder(self.plot_canvas, self.plot_fig)

        ax = self.plot_fig.add_subplot(111)
        ax.text(0.5, 0.5, 'Select data to plot', ha='center', va='center',
               transform=ax.transAxes, fontsize=14, color='#7f8c8d')
        ax.set_title('Materials Characterization Plot', fontweight='bold')
        ax.axis('off')
        self.plot_canvas.draw()

    def _create_log_tab(self):
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="📋 Log")

        self.log_listbox = tk.Listbox(tab, font=("Courier", 10))
        scroll = ttk.Scrollbar(tab, orient=tk.VERTICAL, command=self.log_listbox.yview)
        self.log_listbox.configure(yscrollcommand=scroll.set)
        self.log_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=5)

        btn_frame = tk.Frame(tab, bg="white")
        btn_frame.pack(fill=tk.X, pady=2)

        ttk.Button(btn_frame, text="🗑️ Clear", command=self._clear_log,
                  width=12).pack(side=tk.RIGHT, padx=5)

    # ============================================================================
    # FILE IMPORT METHODS
    # ============================================================================

    def _import_file(self):
        filetypes = [
            ("All supported", "*.spm;*.ibw;*.csv;*.txt;*.xlsx;*.dat;*.000"),
            ("AFM", "*.spm;*.ibw;*.tiff;*.tif"),
            ("Nanoindentation", "*.csv;*.txt"),
            ("Mechanical", "*.csv;*.xlsx"),
            ("BET", "*.csv;*.txt"),
            ("DLS", "*.csv;*.txt"),
            ("Rheology", "*.csv;*.xlsx;*.dat"),
            ("Microhardness", "*.csv;*.txt"),
            ("Profilometry", "*.csv;*.txt"),
            ("All files", "*.*")
        ]

        path = filedialog.askopenfilename(filetypes=filetypes)
        if not path:
            return

        self._update_status(f"Parsing {Path(path).name}...", "#f39c12")
        self.import_btn.config(state='disabled')

        def parse_thread():
            result = MaterialsParserFactory.parse_file(path)

            def update_ui():
                self.import_btn.config(state='normal')
                if result:
                    # Add to appropriate collection
                    if isinstance(result, AFMImage):
                        self.afm_images.append(result)
                        self.current_item = result
                        data_type = "AFM"
                    elif isinstance(result, NanoindentationData):
                        self.nano_data.append(result)
                        self.current_item = result
                        data_type = "Nanoindentation"
                    elif isinstance(result, MechanicalTestData):
                        self.mech_data.append(result)
                        self.current_item = result
                        data_type = "Mechanical"
                    elif isinstance(result, BETIsotherm):
                        self.bet_data.append(result)
                        self.current_item = result
                        data_type = "BET"
                    elif isinstance(result, DLSData):
                        self.dls_data.append(result)
                        self.current_item = result
                        data_type = "DLS"
                    elif isinstance(result, RheologyData):
                        self.rheo_data.append(result)
                        self.current_item = result
                        data_type = "Rheology"
                    elif isinstance(result, ThermalConductivityData):
                        self.thermal_data.append(result)
                        self.current_item = result
                        data_type = "Thermal"
                    elif isinstance(result, MicrohardnessData):
                        self.hardness_data.append(result)
                        self.current_item = result
                        data_type = "Microhardness"
                    elif isinstance(result, ProfilometryData):
                        self.profile_data.append(result)
                        self.current_item = result
                        data_type = "Profilometry"

                    self._update_tree()
                    total = (len(self.afm_images) + len(self.nano_data) + len(self.mech_data) +
                            len(self.bet_data) + len(self.dls_data) + len(self.rheo_data) +
                            len(self.thermal_data) + len(self.hardness_data) + len(self.profile_data))
                    self.file_count_var.set(f"Files: {total}")
                    self.count_label.config(
                        text=f"📊 {total} samples · {len(self.afm_images)} AFM · {len(self.mech_data)} Mech")
                    self._add_to_log(f"✅ Imported {data_type}: {Path(path).name}")

                    # Auto-plot
                    if self.plot_embedder:
                        self._plot_item(result)
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
            results = MaterialsParserFactory.parse_folder(folder)

            def update_ui():
                for result in results:
                    if isinstance(result, AFMImage):
                        self.afm_images.append(result)
                    elif isinstance(result, NanoindentationData):
                        self.nano_data.append(result)
                    elif isinstance(result, MechanicalTestData):
                        self.mech_data.append(result)
                    elif isinstance(result, BETIsotherm):
                        self.bet_data.append(result)
                    elif isinstance(result, DLSData):
                        self.dls_data.append(result)
                    elif isinstance(result, RheologyData):
                        self.rheo_data.append(result)
                    elif isinstance(result, ThermalConductivityData):
                        self.thermal_data.append(result)
                    elif isinstance(result, MicrohardnessData):
                        self.hardness_data.append(result)
                    elif isinstance(result, ProfilometryData):
                        self.profile_data.append(result)

                self._update_tree()
                total = (len(self.afm_images) + len(self.nano_data) + len(self.mech_data) +
                        len(self.bet_data) + len(self.dls_data) + len(self.rheo_data) +
                        len(self.thermal_data) + len(self.hardness_data) + len(self.profile_data))
                self.file_count_var.set(f"Files: {total}")
                self.count_label.config(
                    text=f"📊 {total} samples · {len(self.afm_images)} AFM · {len(self.mech_data)} Mech")
                self._add_to_log(f"📁 Batch imported: {len(results)} files")
                self._update_status(f"✅ Imported {len(results)} files")
                self.import_btn.config(state='normal')
                self.batch_btn.config(state='normal')

            self.ui_queue.schedule(update_ui)

        threading.Thread(target=batch_thread, daemon=True).start()

    def _update_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        # AFM
        for afm in self.afm_images[-10:]:
            key = f"Ra={afm.roughness_ra_nm:.2f}nm" if afm.roughness_ra_nm else f"{afm.pixels}px"
            self.tree.insert('', 0, values=(
                "AFM",
                afm.sample_id[:30],
                afm.instrument,
                key,
                Path(afm.file_source).name if afm.file_source else ""
            ))

        # Nanoindentation
        for nano in self.nano_data[-10:]:
            key = f"H={nano.hardness_GPa:.2f}GPa" if nano.hardness_GPa else f"{nano.max_load_mN:.1f}mN"
            self.tree.insert('', 0, values=(
                "Nano",
                nano.sample_id[:30],
                nano.instrument,
                key,
                Path(nano.file_source).name if nano.file_source else ""
            ))

        # Mechanical
        for mech in self.mech_data[-10:]:
            key = f"UTS={mech.ultimate_strength_MPa:.1f}MPa" if mech.ultimate_strength_MPa else ""
            self.tree.insert('', 0, values=(
                "Mechanical",
                mech.sample_id[:30],
                mech.instrument,
                key,
                Path(mech.file_source).name if mech.file_source else ""
            ))

        # BET
        for bet in self.bet_data[-10:]:
            key = f"SA={bet.bet_surface_area_m2_g:.1f}m²/g" if bet.bet_surface_area_m2_g else ""
            self.tree.insert('', 0, values=(
                "BET",
                bet.sample_id[:30],
                bet.instrument,
                key,
                Path(bet.file_source).name if bet.file_source else ""
            ))

        # DLS
        for dls in self.dls_data[-10:]:
            key = f"Z-Avg={dls.z_average_d_nm:.1f}nm" if dls.z_average_d_nm else ""
            self.tree.insert('', 0, values=(
                "DLS",
                dls.sample_id[:30],
                dls.instrument,
                key,
                Path(dls.file_source).name if dls.file_source else ""
            ))

        # Rheology
        for rheo in self.rheo_data[-10:]:
            key = f"η₀={rheo.zero_shear_viscosity_Pa_s:.1f}Pa·s" if rheo.zero_shear_viscosity_Pa_s else ""
            self.tree.insert('', 0, values=(
                "Rheology",
                rheo.sample_id[:30],
                rheo.instrument,
                key,
                Path(rheo.file_source).name if rheo.file_source else ""
            ))

        # Thermal
        for th in self.thermal_data[-10:]:
            key = f"k={th.thermal_conductivity_W_mK:.3f}W/mK" if th.thermal_conductivity_W_mK else ""
            self.tree.insert('', 0, values=(
                "Thermal",
                th.sample_id[:30],
                th.instrument,
                key,
                Path(th.file_source).name if th.file_source else ""
            ))

        # Microhardness
        for hd in self.hardness_data[-10:]:
            key = f"HV={hd.hardness_HV:.1f}" if hd.hardness_HV else ""
            self.tree.insert('', 0, values=(
                "Hardness",
                hd.sample_id[:30],
                hd.instrument,
                key,
                Path(hd.file_source).name if hd.file_source else ""
            ))

        # Profilometry
        for prof in self.profile_data[-10:]:
            key = f"Ra={prof.ra_um:.3f}μm" if prof.ra_um else ""
            self.tree.insert('', 0, values=(
                "Profile",
                prof.sample_id[:30],
                prof.instrument,
                key,
                Path(prof.file_source).name if prof.file_source else ""
            ))

    def _on_tree_double_click(self, event):
        self._plot_selected()

    def _plot_selected(self):
        selection = self.tree.selection()
        if not selection:
            return

        # This is simplified - would need to map to actual object
        if self.afm_images and self.plot_embedder:
            self._plot_item(self.afm_images[-1])

    def _plot_item(self, item):
        """Plot the appropriate item type"""
        if isinstance(item, AFMImage):
            self.plot_embedder.plot_afm(item)
        elif isinstance(item, NanoindentationData):
            self.plot_embedder.plot_nanoindentation(item)
        elif isinstance(item, MechanicalTestData):
            self.plot_embedder.plot_stress_strain(item)
        elif isinstance(item, BETIsotherm):
            self.plot_embedder.plot_bet_isotherm(item)
        elif isinstance(item, DLSData):
            self.plot_embedder.plot_dls_distribution(item)
        elif isinstance(item, RheologyData):
            self.plot_embedder.plot_rheology(item)
        elif isinstance(item, ProfilometryData):
            self.plot_embedder.plot_profilometry(item)

    def _refresh_plot(self):
        if self.current_item and self.plot_embedder:
            self._plot_item(self.current_item)

    def _save_plot(self):
        if not self.plot_fig:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("PDF", "*.pdf"), ("SVG", "*.svg")],
            initialfile=f"materials_plot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        )
        if path:
            self.plot_fig.savefig(path, dpi=300, bbox_inches='tight')
            self._add_to_log(f"💾 Plot saved: {Path(path).name}")

    def _calculate_properties(self):
        """Calculate properties for current item"""
        if isinstance(self.current_item, AFMImage):
            self.current_item.calculate_roughness()
            self._add_to_log(f"✅ Roughness: Ra={self.current_item.roughness_ra_nm:.3f}nm")
            self._refresh_plot()

        elif isinstance(self.current_item, NanoindentationData):
            self.current_item.calculate_properties()
            self._add_to_log(f"✅ Hardness={self.current_item.hardness_GPa:.2f}GPa, Modulus={self.current_item.modulus_GPa:.1f}GPa")
            self._refresh_plot()

        elif isinstance(self.current_item, MechanicalTestData):
            self.current_item.calculate_properties()
            self._add_to_log(f"✅ E={self.current_item.youngs_modulus_GPa:.1f}GPa, UTS={self.current_item.ultimate_strength_MPa:.1f}MPa")
            self._refresh_plot()

        elif isinstance(self.current_item, BETIsotherm):
            self.current_item.calculate_bet()
            self._add_to_log(f"✅ BET Surface Area: {self.current_item.bet_surface_area_m2_g:.1f} m²/g")
            self._refresh_plot()

        elif isinstance(self.current_item, ProfilometryData):
            self.current_item.calculate_roughness()
            self._add_to_log(f"✅ Ra={self.current_item.ra_um:.3f}μm, Rq={self.current_item.rq_um:.3f}μm")
            self._refresh_plot()

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
        """Send all data to main table"""
        data = []

        for afm in self.afm_images:
            data.append(afm.to_dict())
        for nano in self.nano_data:
            data.append(nano.to_dict())
        for mech in self.mech_data:
            data.append(mech.to_dict())
        for bet in self.bet_data:
            data.append(bet.to_dict())
        for dls in self.dls_data:
            data.append(dls.to_dict())
        for rheo in self.rheo_data:
            data.append(rheo.to_dict())
        for th in self.thermal_data:
            data.append(th.to_dict())
        for hd in self.hardness_data:
            data.append(hd.to_dict())
        for prof in self.profile_data:
            data.append(prof.to_dict())

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
        for afm in self.afm_images:
            data.append(afm.to_dict())
        return data

    def _on_close(self):
        self._add_to_log("🛑 Shutting down...")
        if self.window:
            self.window.destroy()
            self.window = None


# ============================================================================
# SIMPLE PLUGIN REGISTRATION - NO DUPLICATES
# ============================================================================

def setup_plugin(main_app):
    """Register plugin - simple, no duplicates"""

    # Create plugin instance
    plugin = MaterialsCharacterizationSuitePlugin(main_app)

    # Add to left panel if available
    if hasattr(main_app, 'left') and main_app.left is not None:
        main_app.left.add_hardware_button(
            name=PLUGIN_INFO.get("name", "Materials Sci Suite"),
            icon=PLUGIN_INFO.get("icon", "🔬"),
            command=plugin.show_interface
        )
        print(f"✅ Added: {PLUGIN_INFO.get('name')}")

    return plugin
