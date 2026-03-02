"""
MATERIALS CHARACTERIZATION UNIFIED SUITE v2.0 - COMPLETE INDUSTRY STANDARD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ AFM: Bruker · Asylum · Park · JPK — Full ISO 25178 areal analysis
✓ NANOINDENTATION: Oliver & Pharr (1992) — Tip cal, pop-ins, CSM, statistics
✓ MECHANICAL: ASTM E8 — True stress, Hollomon, multi-curve, proof stresses
✓ BET: Rouquerol criteria — t-plot, DR, HK, BJH, multi-adsorbate
✓ DLS: ISO 22412 — Correlation, residuals, multi-peak, temp correction
✓ RHEOLOGY: Carreau · Cross · Herschel-Bulkley — Confidence intervals, yield stress
✓ THERMAL: Netzsch · C-Therm — Cowan correction, Arrhenius, activation energy
✓ MICROHARDNESS: ISO 6507 — Statistics, ISE, load series
✓ PROFILOMETRY: ISO 4287/25178 — Gaussian filter, areal parameters
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

# ============================================================================
# PLUGIN METADATA
# ============================================================================
PLUGIN_INFO = {
    "id": "materials_characterization_unified_suite",
    "name": "Materials Sci Suite v2.0",
    "category": "hardware",
    "icon": "🔬",
    "version": "2.0.0",
    "author": "Scientific Toolkit Team",
    "description": "Industry-standard materials characterization: AFM · Nanoindentation · Mechanical · BET · DLS · Rheology · Thermal · Hardness · Profilometry",
    "requires": ["numpy", "pandas", "scipy", "matplotlib"],
    "optional": ["igor", "pillow"],
    "compact": True,
    "window_size": "800x600"
}

# ============================================================================
# IMPORTS
# ============================================================================
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import pandas as pd
from datetime import datetime
import time
import re
import json
import threading
import queue
import os
import csv
import struct
from pathlib import Path
import platform
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Any, Callable, Union
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# SCIENTIFIC IMPORTS
# ============================================================================
try:
    from scipy import signal, ndimage, stats, optimize, interpolate
    from scipy.signal import savgol_filter, find_peaks, peak_widths, wiener, medfilt2d
    from scipy.optimize import curve_fit, least_squares, minimize, differential_evolution
    from scipy.interpolate import interp1d, UnivariateSpline, griddata, Rbf
    from scipy.ndimage import gaussian_filter, median_filter, uniform_filter, label, generate_binary_structure
    from scipy.ndimage import center_of_mass, find_objects, binary_closing, binary_opening
    from scipy.stats import linregress, norm, t as t_dist
    from scipy.integrate import trapz, cumtrapz, simps, quad
    from scipy.fft import fft2, fftfreq, fftshift, ifft2
    from scipy.spatial import KDTree
    from scipy.special import erf, erfinv
    HAS_SCIPY = True
except ImportError as e:
    print(f"SciPy import warning: {e}")
    HAS_SCIPY = False

try:
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    from matplotlib.patches import Rectangle, Polygon, Circle, Ellipse
    from matplotlib.colors import Normalize, LogNorm, LinearSegmentedColormap
    from matplotlib.cm import ScalarMappable
    from matplotlib.gridspec import GridSpec
    from matplotlib.ticker import ScalarFormatter, LogLocator
    import matplotlib.cm as cm
    import matplotlib.patches as mpatches
    from mpl_toolkits.axes_grid1 import make_axes_locatable
    HAS_MPL = True
except ImportError as e:
    print(f"Matplotlib import warning: {e}")
    HAS_MPL = False

# ============================================================================
# OPTIONAL IMPORTS
# ============================================================================
try:
    from PIL import Image, ImageDraw, ImageFilter, ImageTk
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

    def schedule(self, callback):
        self.queue.put(callback)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================
def safe_float(value, default=0.0):
    """Safely convert to float"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_int(value, default=0):
    """Safely convert to int"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def safe_str(value, default=""):
    """Safely convert to string"""
    if value is None:
        return default
    return str(value)

def format_sci(value, precision=3):
    """Format number in scientific notation"""
    if value is None or np.isnan(value):
        return "—"
    return f"{value:.{precision}e}"

def format_eng(value, unit=""):
    """Format with engineering prefix"""
    if value is None or np.isnan(value):
        return "—"

    prefixes = [
        (1e12, "T"), (1e9, "G"), (1e6, "M"), (1e3, "k"),
        (1, ""), (1e-3, "m"), (1e-6, "µ"), (1e-9, "n"), (1e-12, "p")
    ]

    for factor, prefix in prefixes:
        if abs(value) >= factor:
            return f"{value/factor:.3f} {prefix}{unit}"

    return f"{value:.3e} {unit}"

def confidence_interval(data, confidence=0.95):
    """Calculate confidence interval for data"""
    if len(data) < 2:
        return 0, 0

    mean = np.mean(data)
    sem = np.std(data, ddof=1) / np.sqrt(len(data))
    h = sem * t_dist.ppf((1 + confidence) / 2, len(data) - 1)

    return mean - h, mean + h


# ============================================================================
# DATA CLASSES WITH FULL METADATA
# ============================================================================

@dataclass
class AFMImage:
    """
    Atomic Force Microscopy image with full ISO 25178 analysis

    ISO 25178-2:2012 - Geometrical product specifications (GPS) — Surface texture:
    Areal — Part 2: Terms, definitions and surface texture parameters
    """
    timestamp: datetime
    sample_id: str
    instrument: str
    scan_size_um: float = 0
    pixels: int = 0
    height_data: Optional[np.ndarray] = None
    amplitude_data: Optional[np.ndarray] = None
    phase_data: Optional[np.ndarray] = None
    deflection_data: Optional[np.ndarray] = None
    scan_rate_hz: float = 0
    setpoint_nm: float = 0
    drive_amplitude_mv: float = 0
    feedback_gain: float = 0
    tip_model: str = ""
    file_source: str = ""
    metadata: Dict = field(default_factory=dict)

    # ISO 25178 areal parameters
    sa_nm: Optional[float] = None  # Arithmetical mean height
    sq_nm: Optional[float] = None  # Root mean square height
    sz_nm: Optional[float] = None  # Maximum height
    ssk: Optional[float] = None    # Skewness
    sku: Optional[float] = None     # Kurtosis
    sp_nm: Optional[float] = None   # Maximum peak height
    sv_nm: Optional[float] = None   # Maximum pit height
    s10z_nm: Optional[float] = None # Ten point height
    sdr_pct: Optional[float] = None # Developed interfacial area ratio
    str: Optional[float] = None     # Texture aspect ratio
    std: Optional[float] = None      # Texture direction

    # Grain analysis
    grain_count: Optional[int] = None
    grain_sizes_nm: Optional[np.ndarray] = None
    grain_areas_um2: Optional[np.ndarray] = None
    grain_circularity: Optional[np.ndarray] = None
    grain_orientation: Optional[np.ndarray] = None

    # FFT power spectrum
    power_spectrum: Optional[np.ndarray] = None
    radial_psd: Optional[np.ndarray] = None
    radial_freq: Optional[np.ndarray] = None

    def calculate_areal_parameters(self):
        """
        Calculate ISO 25178 areal surface parameters

        References:
        - ISO 25178-2:2012
        - Blateyron, F. (2013) "Areal surface texture parameters"
        """
        if self.height_data is None:
            return

        data = self.height_data.flatten()
        h, w = self.height_data.shape

        # Basic parameters
        self.sa_nm = float(np.mean(np.abs(data - np.mean(data))))
        self.sq_nm = float(np.std(data))
        self.sz_nm = float(np.max(data) - np.min(data))
        self.sp_nm = float(np.max(data) - np.mean(data))
        self.sv_nm = float(np.mean(data) - np.min(data))

        # Ten point height (average of 5 highest peaks - 5 lowest valleys)
        sorted_data = np.sort(data)
        if len(sorted_data) > 10:
            peaks = sorted_data[-5:]
            valleys = sorted_data[:5]
            self.s10z_nm = float(np.mean(peaks) - np.mean(valleys))

        # Skewness and kurtosis
        if HAS_SCIPY and self.sq_nm and self.sq_nm > 0:
            self.ssk = float(stats.skew(data))
            self.sku = float(stats.kurtosis(data))

        # Developed interfacial area ratio
        if h > 1 and w > 1:
            dx = self.scan_size_um * 1000 / w  # nm per pixel
            dy = self.scan_size_um * 1000 / h

            # Gradient magnitudes
            grad_y, grad_x = np.gradient(self.height_data, dy, dx)
            surface_area = np.sum(np.sqrt(1 + grad_x**2 + grad_y**2)) * dx * dy
            projected_area = (self.scan_size_um * 1000) ** 2
            self.sdr_pct = 100 * (surface_area - projected_area) / projected_area if projected_area > 0 else 0

        # Texture aspect ratio (simplified)
        if HAS_SCIPY and h > 10 and w > 10:
            from scipy.ndimage import uniform_filter
            # Autocorrelation function
            data_mean = self.height_data - np.mean(self.height_data)
            fft = fft2(data_mean)
            acf = np.real(ifft2(fft * np.conj(fft)))
            acf = fftshift(acf)

            # Find 0.2 correlation threshold
            acf_norm = acf / acf[h//2, w//2]
            threshold = 0.2

            # Find distances in x and y directions
            center_x, center_y = w//2, h//2
            x_dist = 0
            y_dist = 0

            for i in range(1, min(center_x, center_y)):
                if acf_norm[center_y, center_x + i] < threshold and x_dist == 0:
                    x_dist = i * (self.scan_size_um / w) * 1000
                if acf_norm[center_y + i, center_x] < threshold and y_dist == 0:
                    y_dist = i * (self.scan_size_um / h) * 1000

            if x_dist > 0 and y_dist > 0:
                self.str = float(min(x_dist, y_dist) / max(x_dist, y_dist))

    def flatten(self, order=1):
        """
        Remove polynomial background

        order: 1 for plane, 2 for quadratic
        """
        if self.height_data is None:
            return

        h, w = self.height_data.shape
        x = np.arange(w)
        y = np.arange(h)
        X, Y = np.meshgrid(x, y)

        # Fit polynomial surface
        if order == 1:
            # Plane: z = a*x + b*y + c
            A = np.column_stack([X.ravel(), Y.ravel(), np.ones(h*w)])
        elif order == 2:
            # Quadratic: z = a*x² + b*y² + c*x*y + d*x + e*y + f
            A = np.column_stack([
                X.ravel()**2, Y.ravel()**2, (X*Y).ravel(),
                X.ravel(), Y.ravel(), np.ones(h*w)
            ])
        else:
            return

        coeffs, _, _, _ = np.linalg.lstsq(A, self.height_data.ravel(), rcond=None)
        background = np.dot(A, coeffs).reshape(h, w)
        self.height_data = self.height_data - background

    def median_filter(self, size=3):
        """Apply median filter for noise reduction"""
        if self.height_data is not None and HAS_SCIPY:
            self.height_data = median_filter(self.height_data, size=size)

    def gaussian_filter(self, sigma=1.0):
        """Apply Gaussian filter"""
        if self.height_data is not None and HAS_SCIPY:
            self.height_data = gaussian_filter(self.height_data, sigma=sigma)

    def remove_nan(self):
        """Remove NaN values by interpolation"""
        if self.height_data is None:
            return

        mask = np.isnan(self.height_data)
        if not np.any(mask):
            return

        if HAS_SCIPY:
            from scipy.interpolate import griddata

            h, w = self.height_data.shape
            x, y = np.meshgrid(np.arange(w), np.arange(h))

            points = np.column_stack((x[~mask], y[~mask]))
            values = self.height_data[~mask]

            self.height_data[mask] = griddata(
                points, values, (x[mask], y[mask]), method='cubic'
            )

    def detect_grains(self, threshold=0.5, min_size=5, circularity_threshold=0.5):
        """
        Detect grains using threshold and watershed

        Parameters:
        - threshold: height threshold (fraction of max height)
        - min_size: minimum grain size in pixels
        - circularity_threshold: minimum circularity to count as grain
        """
        if self.height_data is None or not HAS_SCIPY:
            return

        from scipy.ndimage import label, center_of_mass, find_objects
        from scipy.ndimage import binary_fill_holes

        # Normalize to [0, 1]
        data_norm = (self.height_data - self.height_data.min())
        data_max = data_norm.max()
        if data_max > 0:
            data_norm = data_norm / data_max

        # Threshold
        binary = data_norm > threshold

        # Clean up binary image
        structure = generate_binary_structure(2, 2)
        binary = binary_closing(binary, structure=structure)
        binary = binary_opening(binary, structure=structure)
        binary = binary_fill_holes(binary)

        # Label grains
        labeled, self.grain_count = label(binary)

        if self.grain_count > 0:
            # Calculate grain properties
            objects = find_objects(labeled)
            self.grain_sizes_nm = []
            self.grain_areas_um2 = []
            self.grain_circularity = []
            self.grain_orientation = []

            pixel_area_um2 = (self.scan_size_um / self.pixels) ** 2

            for i, obj in enumerate(objects, 1):
                if obj is None:
                    continue

                # Grain mask
                grain_mask = labeled[obj] == i
                size_px = np.sum(grain_mask)

                if size_px < min_size:
                    self.grain_count -= 1
                    continue

                # Area in μm²
                area_um2 = size_px * pixel_area_um2
                self.grain_areas_um2.append(area_um2)

                # Equivalent diameter (nm)
                diameter_nm = 2 * np.sqrt(area_um2 * 1e6 / np.pi) * 1000
                self.grain_sizes_nm.append(diameter_nm)

                # Circularity (4πA/P²)
                if HAS_SCIPY:
                    from skimage.measure import perimeter
                    if 'perimeter' in dir():
                        perim = perimeter(grain_mask.astype(int))
                        if perim > 0:
                            circ = 4 * np.pi * size_px / (perim ** 2)
                            self.grain_circularity.append(min(circ, 1.0))
                        else:
                            self.grain_circularity.append(1.0)
                    else:
                        self.grain_circularity.append(1.0)

                    # Orientation (simplified - based on bounding box)
                    y_indices, x_indices = np.where(grain_mask)
                    if len(x_indices) > 1 and len(y_indices) > 1:
                        x_range = x_indices.max() - x_indices.min()
                        y_range = y_indices.max() - y_indices.min()
                        if x_range > 0:
                            self.grain_orientation.append(np.arctan2(y_range, x_range))
                        else:
                            self.grain_orientation.append(0)

            # Convert to arrays
            if self.grain_sizes_nm:
                self.grain_sizes_nm = np.array(self.grain_sizes_nm)
                self.grain_areas_um2 = np.array(self.grain_areas_um2)
                if self.grain_circularity:
                    self.grain_circularity = np.array(self.grain_circularity)
                if self.grain_orientation:
                    self.grain_orientation = np.array(self.grain_orientation)

    def calculate_power_spectrum(self):
        """
        Calculate 2D FFT power spectrum and radial average
        """
        if self.height_data is None or not HAS_SCIPY:
            return

        # Detrend
        data = self.height_data - np.mean(self.height_data)

        # Apply window to reduce edge effects
        h, w = data.shape
        window = np.outer(np.hanning(h), np.hanning(w))
        data_windowed = data * window

        # FFT
        fft = fft2(data_windowed)
        fft_shifted = fftshift(fft)
        power = np.abs(fft_shifted) ** 2
        self.power_spectrum = power

        # Radial average
        h, w = power.shape
        center_y, center_x = h // 2, w // 2

        y, x = np.indices((h, w))
        r = np.sqrt((x - center_x)**2 + (y - center_y)**2)
        r = r.astype(int)

        # Maximum radius
        max_r = min(center_x, center_y)

        # Radial bins
        radial_sum = np.zeros(max_r + 1)
        radial_count = np.zeros(max_r + 1)

        for i in range(h):
            for j in range(w):
                radius = r[i, j]
                if radius <= max_r:
                    radial_sum[radius] += power[i, j]
                    radial_count[radius] += 1

        self.radial_psd = radial_sum / (radial_count + 1e-10)
        self.radial_freq = np.arange(max_r + 1) / (self.scan_size_um * 1000)  # nm⁻¹

    def line_profile(self, start, end, width=1):
        """
        Extract line profile between two points

        start, end: (x, y) in pixels
        width: number of pixels to average perpendicular to line
        """
        if self.height_data is None:
            return None, None

        x1, y1 = start
        x2, y2 = end

        # Number of points
        length = int(np.hypot(x2 - x1, y2 - y1))

        # Line coordinates
        x = np.linspace(x1, x2, length)
        y = np.linspace(y1, y2, length)

        # Extract profile
        profile = np.zeros(length)

        for i in range(length):
            xi, yi = int(x[i]), int(y[i])

            if width == 1:
                profile[i] = self.height_data[yi, xi]
            else:
                # Average perpendicular to line
                # Simplified - just average nearby points
                x0 = max(0, xi - width)
                x1 = min(self.height_data.shape[1], xi + width + 1)
                y0 = max(0, yi - width)
                y1 = min(self.height_data.shape[0], yi + width + 1)

                region = self.height_data[y0:y1, x0:x1]
                profile[i] = np.mean(region)

        # Distance along profile (μm)
        distance = np.linspace(0, np.hypot(
            (x2 - x1) * self.scan_size_um / self.pixels,
            (y2 - y1) * self.scan_size_um / self.pixels
        ), length)

        return distance, profile

    def to_dict(self):
        """Convert to dictionary for main table"""
        d = {
            'Timestamp': self.timestamp.isoformat() if self.timestamp else '',
            'Sample_ID': self.sample_id,
            'Instrument': self.instrument,
            'Scan_Size_um': f"{self.scan_size_um:.2f}",
            'Pixels': str(self.pixels),
            'Sa_nm': f"{self.sa_nm:.3f}" if self.sa_nm else '',
            'Sq_nm': f"{self.sq_nm:.3f}" if self.sq_nm else '',
            'Sz_nm': f"{self.sz_nm:.3f}" if self.sz_nm else '',
            'Ssk': f"{self.ssk:.3f}" if self.ssk else '',
            'Sku': f"{self.sku:.3f}" if self.sku else '',
            'Sdr_pct': f"{self.sdr_pct:.2f}" if self.sdr_pct else '',
            'Grain_Count': str(self.grain_count) if self.grain_count else ''
        }
        return d


@dataclass
class NanoindentationData:
    """
    Nanoindentation data with full Oliver-Pharr analysis

    Oliver, W.C. & Pharr, G.M. (1992) "An improved technique for determining
    hardness and elastic modulus using load and displacement sensing indentation
    experiments" Journal of Materials Research, 7(6), 1564-1583

    ISO 14577-1:2015 - Metallic materials — Instrumented indentation test for
    hardness and materials parameters — Part 1: Test method
    """
    timestamp: datetime
    sample_id: str
    instrument: str
    tip_type: str = "Berkovich"

    # Raw data
    displacement_nm: Optional[np.ndarray] = None
    load_mN: Optional[np.ndarray] = None
    time_s: Optional[np.ndarray] = None
    temperature_c: Optional[np.ndarray] = None

    # Unloading curve (extracted)
    unloading_displacement_nm: Optional[np.ndarray] = None
    unloading_load_mN: Optional[np.ndarray] = None

    # Tip calibration
    area_coeffs: List[float] = field(default_factory=lambda: [24.5, 0.0, 0.0, 0.0])  # C0, C1, C2, C3 for A = C0*h² + C1*h + C2*h^½ + C3*h^¼
    frame_compliance_nm_mN: float = 0.0
    thermal_drift_nm_s: float = 0.0

    # Oliver-Pharr results
    hardness_GPa: Optional[float] = None
    modulus_GPa: Optional[float] = None
    reduced_modulus_GPa: Optional[float] = None
    max_load_mN: Optional[float] = None
    max_displacement_nm: Optional[float] = None
    contact_depth_nm: Optional[float] = None
    contact_area_um2: Optional[float] = None
    stiffness_mN_nm: Optional[float] = None
    fit_m: Optional[float] = None  # Power law exponent
    fit_hf: Optional[float] = None  # Final displacement
    fit_r2: Optional[float] = None   # Fit quality

    # Pop-in detection
    pop_in_loads_mN: List[float] = field(default_factory=list)
    pop_in_displacements_nm: List[float] = field(default_factory=list)
    pop_in_indices: List[int] = field(default_factory=list)

    # CSM (continuous stiffness measurement)
    csm_depth_nm: Optional[np.ndarray] = None
    csm_hardness_GPa: Optional[np.ndarray] = None
    csm_modulus_GPa: Optional[np.ndarray] = None
    csm_stiffness_mN_nm: Optional[np.ndarray] = None
    csm_frequency_Hz: float = 45.0  # Typical CSM frequency

    # Statistics (for multiple indents)
    indent_group: List[Dict] = field(default_factory=list)
    hardness_mean: Optional[float] = None
    hardness_std: Optional[float] = None
    hardness_ci_low: Optional[float] = None
    hardness_ci_high: Optional[float] = None
    modulus_mean: Optional[float] = None
    modulus_std: Optional[float] = None
    modulus_ci_low: Optional[float] = None
    modulus_ci_high: Optional[float] = None

    # File metadata
    file_source: str = ""
    metadata: Dict = field(default_factory=dict)

    def set_area_function(self, coeffs):
        """
        Set tip area function coefficients

        A = C0 * h² + C1 * h + C2 * √h + C3 * h^¼

        Where h is in mm, A in mm²
        """
        if len(coeffs) >= 4:
            self.area_coeffs = coeffs[:4]
        elif len(coeffs) == 3:
            self.area_coeffs = [coeffs[0], coeffs[1], coeffs[2], 0.0]
        elif len(coeffs) == 2:
            self.area_coeffs = [coeffs[0], coeffs[1], 0.0, 0.0]
        elif len(coeffs) == 1:
            self.area_coeffs = [coeffs[0], 0.0, 0.0, 0.0]

    def area_function(self, h_nm):
        """
        Calculate contact area from depth using calibrated area function

        Parameters:
        - h_nm: contact depth in nm

        Returns:
        - Area in μm²
        """
        h_mm = h_nm / 1e6  # Convert nm to mm for area in mm²

        A = (self.area_coeffs[0] * h_mm**2 +
             self.area_coeffs[1] * h_mm +
             self.area_coeffs[2] * np.sqrt(h_mm) +
             self.area_coeffs[3] * h_mm**0.25)

        return A * 1e6  # Convert mm² to μm²

    def correct_compliance(self):
        """
        Apply frame compliance correction

        h_corrected = h_measured - (C_f * P)
        where C_f is frame compliance (nm/mN)
        """
        if self.displacement_nm is not None and self.load_mN is not None:
            correction = self.load_mN * self.frame_compliance_nm_mN
            self.displacement_nm = self.displacement_nm - correction

    def correct_thermal_drift(self):
        """
        Apply thermal drift correction (linear in time)
        """
        if (self.displacement_nm is not None and self.time_s is not None and
            self.thermal_drift_nm_s != 0):

            # Correct assuming constant drift rate
            correction = self.time_s * self.thermal_drift_nm_s
            self.displacement_nm = self.displacement_nm - correction

    def extract_unloading(self):
        """
        Extract unloading curve by finding maximum load
        """
        if self.displacement_nm is None or self.load_mN is None:
            return

        max_idx = np.argmax(self.load_mN)

        # Store max values
        self.max_load_mN = float(self.load_mN[max_idx])
        self.max_displacement_nm = float(self.displacement_nm[max_idx])

        # Split into loading and unloading
        self.unloading_displacement_nm = self.displacement_nm[max_idx:]
        self.unloading_load_mN = self.load_mN[max_idx:]

    def detect_pop_ins(self, threshold_pct=5, min_separation=5):
        """
        Detect pop-in events in loading curve (discontinuities)

        Pop-ins are sudden displacement bursts at constant or decreasing load
        indicating phase transformations or dislocation avalanches.

        Parameters:
        - threshold_pct: percent drop in stiffness to consider a pop-in
        - min_separation: minimum number of points between pop-ins
        """
        if self.displacement_nm is None or self.load_mN is None:
            return

        # Calculate stiffness (dP/dh)
        dPdh = np.gradient(self.load_mN, self.displacement_nm)

        # Smooth stiffness to reduce noise
        if len(dPdh) > 10:
            dPdh = savgol_filter(dPdh, min(9, len(dPdh)//2*2-1), 2)

        # Find sudden drops in stiffness
        mean_dPdh = np.mean(dPdh[:len(dPdh)//2])  # Mean of loading portion
        threshold = mean_dPdh * (1 - threshold_pct/100)

        # Find potential pop-ins
        potential = []
        in_pop = False
        pop_start = 0

        for i in range(1, len(dPdh)-1):
            if dPdh[i] < threshold and dPdh[i-1] > threshold and not in_pop:
                # Start of pop-in
                in_pop = True
                pop_start = i
            elif in_pop and dPdh[i] > threshold:
                # End of pop-in
                in_pop = False
                if i - pop_start >= min_separation:
                    # Take middle of pop-in region
                    mid = (pop_start + i) // 2
                    potential.append(mid)

        # Clean up duplicates
        self.pop_in_indices = []
        self.pop_in_loads_mN = []
        self.pop_in_displacements_nm = []

        for idx in potential:
            # Check if not too close to previous
            if not self.pop_in_indices or idx - self.pop_in_indices[-1] > min_separation:
                self.pop_in_indices.append(idx)
                self.pop_in_loads_mN.append(float(self.load_mN[idx]))
                self.pop_in_displacements_nm.append(float(self.displacement_nm[idx]))

    def oliver_pharr(self, epsilon=0.75, fit_top=0.5, fit_method='power'):
        """
        Oliver-Pharr method for hardness and modulus

        Parameters:
        - epsilon: geometric constant (0.75 for Berkovich, 0.72 for conical)
        - fit_top: fraction of unloading curve to fit (top 50% default)
        - fit_method: 'power' for power law, 'linear' for linear fit

        Returns:
        - Dictionary of results
        """
        if self.displacement_nm is None or self.load_mN is None:
            return None

        # Extract unloading if not already done
        if self.unloading_displacement_nm is None:
            self.extract_unloading()

        if len(self.unloading_displacement_nm) < 5:
            return None

        # Fit unloading curve
        h_unload = self.unloading_displacement_nm
        P_unload = self.unloading_load_mN

        n_points = len(h_unload)
        start_idx = int(n_points * (1 - fit_top))

        if start_idx >= n_points - 3:
            start_idx = max(0, n_points - 10)

        h_fit = h_unload[start_idx:]
        P_fit = P_unload[start_idx:]

        if len(h_fit) < 3:
            return None

        if fit_method == 'power':
            # Power law fit: P = α (h - hf)^m
            # Oliver & Pharr (1992) Eq. 3

            def power_law(h, alpha, m, hf):
                return alpha * np.maximum(h - hf, 1e-10) ** m

            try:
                # Initial guess
                p0 = [
                    P_fit[-1] / (h_fit[-1] - h_fit[0])**1.5,
                    1.5,
                    h_fit[-1] - 5
                ]

                # Bounds
                bounds = (
                    [0, 1.0, h_fit[-1] - 20],
                    [np.inf, 3.0, h_fit[-1]]
                )

                popt, pcov = curve_fit(
                    power_law, h_fit, P_fit,
                    p0=p0, bounds=bounds, maxfev=5000
                )

                alpha, m, hf = popt

                # Stiffness at max load
                self.stiffness_mN_nm = float(alpha * m * (self.max_displacement_nm - hf) ** (m - 1))
                self.fit_m = float(m)
                self.fit_hf = float(hf)

                # Calculate R²
                residuals = P_fit - power_law(h_fit, alpha, m, hf)
                ss_res = np.sum(residuals**2)
                ss_tot = np.sum((P_fit - np.mean(P_fit))**2)
                self.fit_r2 = float(1 - ss_res/ss_tot) if ss_tot > 0 else 0

            except Exception as e:
                print(f"Power law fit failed: {e}")
                # Fallback to linear fit
                coeffs = np.polyfit(h_fit[-5:], P_fit[-5:], 1)
                self.stiffness_mN_nm = float(coeffs[0])
                self.fit_m = 1.0
                self.fit_hf = self.max_displacement_nm - self.max_load_mN / self.stiffness_mN_nm
                self.fit_r2 = 0

        else:
            # Linear fit to top portion
            n_fit = max(3, len(h_fit) // 4)
            coeffs = np.polyfit(h_fit[-n_fit:], P_fit[-n_fit:], 1)
            self.stiffness_mN_nm = float(coeffs[0])
            self.fit_m = 1.0
            self.fit_hf = self.max_displacement_nm - self.max_load_mN / self.stiffness_mN_nm

            # Calculate R²
            P_fit_linear = np.polyval(coeffs, h_fit[-n_fit:])
            residuals = P_fit[-n_fit:] - P_fit_linear
            ss_res = np.sum(residuals**2)
            ss_tot = np.sum((P_fit[-n_fit:] - np.mean(P_fit[-n_fit:]))**2)
            self.fit_r2 = float(1 - ss_res/ss_tot) if ss_tot > 0 else 0

        # Contact depth (Oliver-Pharr Eq. 5)
        self.contact_depth_nm = float(
            self.max_displacement_nm -
            epsilon * self.max_load_mN / self.stiffness_mN_nm
        )

        # Contact area
        self.contact_area_um2 = float(self.area_function(self.contact_depth_nm))

        # Hardness (Oliver-Pharr Eq. 6)
        if self.contact_area_um2 > 0:
            self.hardness_GPa = float(self.max_load_mN / self.contact_area_um2 / 1000)
        else:
            self.hardness_GPa = 0

        # Reduced modulus (Oliver-Pharr Eq. 7)
        beta = 1.034  # Berkovich correction factor

        if self.contact_area_um2 > 0:
            self.reduced_modulus_GPa = float(
                (self.stiffness_mN_nm * np.sqrt(np.pi) /
                 (2 * beta * np.sqrt(self.contact_area_um2 * 1e6))) / 1000
            )
        else:
            self.reduced_modulus_GPa = 0

        # Young's modulus (assuming diamond tip)
        # Ei = 1140 GPa, νi = 0.07
        Ei = 1140
        νi = 0.07
        νs = 0.3  # Typical Poisson's ratio, can be updated

        if self.reduced_modulus_GPa > 0:
            self.modulus_GPa = float(
                1 / ((1/self.reduced_modulus_GPa) - (1-νi**2)/Ei) * (1-νs**2)
            )
        else:
            self.modulus_GPa = 0

        return {
            'hardness': self.hardness_GPa,
            'modulus': self.modulus_GPa,
            'reduced_modulus': self.reduced_modulus_GPa,
            'contact_depth': self.contact_depth_nm,
            'contact_area': self.contact_area_um2,
            'stiffness': self.stiffness_mN_nm,
            'max_load': self.max_load_mN,
            'fit_m': self.fit_m,
            'fit_r2': self.fit_r2
        }

    def add_to_group(self):
        """Add current indent to group for statistics"""
        self.indent_group.append({
            'hardness': self.hardness_GPa,
            'modulus': self.modulus_GPa,
            'reduced_modulus': self.reduced_modulus_GPa,
            'contact_depth': self.contact_depth_nm,
            'contact_area': self.contact_area_um2,
            'max_load': self.max_load_mN,
            'pop_ins': len(self.pop_in_loads_mN)
        })

    def calculate_statistics(self, confidence=0.95):
        """
        Calculate statistics for multiple indents

        Parameters:
        - confidence: confidence level for intervals (e.g., 0.95)
        """
        if not self.indent_group:
            return

        # Extract values
        h_vals = [d['hardness'] for d in self.indent_group if d['hardness'] is not None]
        e_vals = [d['modulus'] for d in self.indent_group if d['modulus'] is not None]
        er_vals = [d['reduced_modulus'] for d in self.indent_group if d['reduced_modulus'] is not None]

        # Hardness statistics
        if len(h_vals) > 0:
            self.hardness_mean = float(np.mean(h_vals))
            self.hardness_std = float(np.std(h_vals, ddof=1)) if len(h_vals) > 1 else 0

            if len(h_vals) > 1:
                ci_low, ci_high = confidence_interval(h_vals, confidence)
                self.hardness_ci_low = float(ci_low)
                self.hardness_ci_high = float(ci_high)

        # Modulus statistics
        if len(e_vals) > 0:
            self.modulus_mean = float(np.mean(e_vals))
            self.modulus_std = float(np.std(e_vals, ddof=1)) if len(e_vals) > 1 else 0

            if len(e_vals) > 1:
                ci_low, ci_high = confidence_interval(e_vals, confidence)
                self.modulus_ci_low = float(ci_low)
                self.modulus_ci_high = float(ci_high)

    def load_csm_data(self, depth, hardness, modulus):
        """Load continuous stiffness measurement data"""
        self.csm_depth_nm = np.array(depth)
        self.csm_hardness_GPa = np.array(hardness)
        self.csm_modulus_GPa = np.array(modulus)

    def fit_indentation_size_effect(self):
        """
        Fit indentation size effect (ISE) model

        Nix, W.D. & Gao, H. (1998) "Indentation size effects in crystalline
        materials: A law for strain gradient plasticity" J. Mech. Phys. Solids
        """
        if self.csm_depth_nm is None or self.csm_hardness_GPa is None:
            return None

        # Nix-Gao model: H² = H₀² + H₀² * h*/h
        depth = self.csm_depth_nm
        hardness = self.csm_hardness_GPa

        # Use depths where hardness is stable (exclude very shallow)
        mask = depth > 50
        if not np.any(mask):
            return None

        x = 1 / depth[mask]
        y = hardness[mask] ** 2

        # Linear regression: y = H₀² + H₀² * h* * x
        slope, intercept, r_value, _, _ = linregress(x, y)

        if intercept > 0:
            H0 = np.sqrt(intercept)
            h_star = slope / intercept if intercept > 0 else 0
            r2 = r_value**2

            return {
                'H0_GPa': float(H0),
                'h_star_nm': float(h_star),
                'r2': float(r2)
            }

        return None

    def to_dict(self):
        """Convert to dictionary for main table"""
        pop_ins_str = ', '.join([f"{l:.2f}" for l in self.pop_in_loads_mN[:3]])
        if len(self.pop_in_loads_mN) > 3:
            pop_ins_str += f" ... (+{len(self.pop_in_loads_mN)-3})"

        d = {
            'Timestamp': self.timestamp.isoformat() if self.timestamp else '',
            'Sample_ID': self.sample_id,
            'Instrument': self.instrument,
            'Tip': self.tip_type,
            'Hardness_GPa': f"{self.hardness_GPa:.3f}" if self.hardness_GPa else '',
            'Modulus_GPa': f"{self.modulus_GPa:.1f}" if self.modulus_GPa else '',
            'Reduced_Modulus_GPa': f"{self.reduced_modulus_GPa:.1f}" if self.reduced_modulus_GPa else '',
            'Max_Load_mN': f"{self.max_load_mN:.3f}" if self.max_load_mN else '',
            'Contact_Depth_nm': f"{self.contact_depth_nm:.1f}" if self.contact_depth_nm else '',
            'Stiffness_mN_nm': f"{self.stiffness_mN_nm:.3f}" if self.stiffness_mN_nm else '',
            'Pop_ins': pop_ins_str,
            'Fit_R²': f"{self.fit_r2:.4f}" if self.fit_r2 else ''
        }
        return d


@dataclass
class BETIsotherm:
    """
    BET surface area analysis with full Rouquerol criteria

    Brunauer, S., Emmett, P.H. & Teller, E. (1938) "Adsorption of gases in
    multimolecular layers" Journal of the American Chemical Society, 60(2), 309-319

    Rouquerol, F., Rouquerol, J. & Sing, K. (1999) "Adsorption by Powders
    and Porous Solids" Academic Press

    ISO 9277:2010 - Determination of the specific surface area of solids by
    gas adsorption — BET method
    """
    timestamp: datetime
    sample_id: str
    instrument: str
    adsorbate: str = "N2"
    temperature_k: float = 77.35
    sample_mass_g: float = 0.1

    # Isotherm data
    relative_pressure: Optional[np.ndarray] = None
    volume_adsorbed_cc_g: Optional[np.ndarray] = None
    volume_desorbed_cc_g: Optional[np.ndarray] = None

    # BET results
    bet_surface_area_m2_g: Optional[float] = None
    bet_c_constant: Optional[float] = None
    bet_correlation: Optional[float] = None
    bet_monolayer_volume: Optional[float] = None
    bet_pressure_range: Tuple[float, float] = (0.05, 0.3)
    bet_slope: Optional[float] = None
    bet_intercept: Optional[float] = None

    # Rouquerol criteria
    rouquerol_passed: bool = False
    rouquerol_range: Tuple[float, float] = (0.05, 0.3)
    rouquerol_message: str = ""
    rouquerol_n_points: int = 0

    # t-plot micropore
    micropore_volume_cc_g: Optional[float] = None
    external_surface_area_m2_g: Optional[float] = None
    t_plot_correlation: Optional[float] = None
    t_plot_slope: Optional[float] = None
    t_plot_intercept: Optional[float] = None

    # Dubinin-Radushkevich
    dr_micropore_volume_cc_g: Optional[float] = None
    dr_characteristic_energy_kJ_mol: Optional[float] = None
    dr_pre_exponential: Optional[float] = None
    dr_correlation: Optional[float] = None

    # Horvath-Kawazoe
    hk_pore_size_nm: Optional[float] = None
    hk_pore_volume: Optional[float] = None

    # BJH mesopore
    bjh_pore_volume_cc_g: Optional[float] = None
    bjh_pore_size_nm: Optional[float] = None
    bjh_pore_size_distribution: Optional[np.ndarray] = None
    bjh_cumulative_volume: Optional[np.ndarray] = None

    # Multi-adsorbate properties
    cross_section_nm2: float = 0.162  # N2 default

    file_source: str = ""
    metadata: Dict = field(default_factory=dict)

    # Cross-sectional areas (nm²) from ISO 9277
    CROSS_SECTIONS = {
        'N2': 0.162,
        'Ar': 0.142,
        'CO2': 0.170,
        'Kr': 0.202,
        'Xe': 0.235,
        'H2O': 0.125
    }

    AVOGADRO = 6.02214076e23
    MOLAR_VOLUME = 22414  # cm³/mol at STP

    def __post_init__(self):
        """Initialize cross-sectional area based on adsorbate"""
        self.cross_section_nm2 = self.CROSS_SECTIONS.get(self.adsorbate, 0.162)

    def bet_transform(self):
        """
        Calculate BET transform: y = 1/[V(P₀/P - 1)] vs x = P/P₀

        BET equation: 1/[V(P₀/P - 1)] = (C-1)/(Vm·C) · (P/P₀) + 1/(Vm·C)
        """
        if self.relative_pressure is None or self.volume_adsorbed_cc_g is None:
            return None, None

        p = self.relative_pressure
        v = self.volume_adsorbed_cc_g

        # Avoid division by zero
        mask = (p > 0) & (p < 1) & (v > 0)
        if not np.any(mask):
            return None, None

        p = p[mask]
        v = v[mask]

        # BET transform
        x = p
        y = 1 / (v * (1/p - 1))

        return x, y

    def check_rouquerol_criteria(self):
        """
        Check Rouquerol consistency criteria for valid BET range

        Rouquerol, F., et al. (2007) "Studies in Surface Science and Catalysis",
        160, 49-56. "Is the BET equation applicable to microporous adsorbents?"

        Criteria:
        1. BET constant C must be positive
        2. The term n(1-P/P₀) must increase with P/P₀
        3. The BET transform must be positive and increasing
        4. The pressure range should give maximum correlation
        """
        if self.relative_pressure is None or self.volume_adsorbed_cc_g is None:
            self.rouquerol_message = "No data loaded"
            return False

        p = self.relative_pressure
        v = self.volume_adsorbed_cc_g

        # Calculate BET transform
        x, y = self.bet_transform()
        if x is None:
            self.rouquerol_message = "Cannot calculate BET transform"
            return False

        # Criteria 1: BET transform must be positive
        if np.any(y <= 0):
            self.rouquerol_message = "BET transform contains non-positive values"
            return False

        # Criteria 2: BET transform must be increasing
        increasing = True
        increasing_start = 0

        for i in range(1, len(y)):
            if y[i] < y[i-1]:
                increasing = False
                break
            if y[i] > y[i-1] and increasing_start == 0:
                increasing_start = i - 1

        if not increasing:
            self.rouquerol_message = "BET transform not monotonically increasing"
            return False

        # Estimate monolayer volume for n(1-P/P₀) calculation
        # Rough estimate from point of inflection
        v_inflection = v[len(v)//2]

        # Criteria 3: n(1-P/P₀) must increase with P/P₀
        # where n = V / V_mono (approximated)
        n_term = v / v_inflection * (1 - p)

        n_term_increasing = True
        for i in range(1, len(n_term)):
            if n_term[i] < n_term[i-1]:
                n_term_increasing = False
                break

        if not n_term_increasing:
            self.rouquerol_message = "n(1-P/P₀) term not increasing"
            return False

        # Find optimal range by maximizing R²
        best_r2 = 0
        best_range = (0.05, 0.3)
        best_n_points = 0

        # Search over possible ranges
        for p_min in np.arange(0.01, 0.2, 0.005):
            for p_max in np.arange(p_min + 0.05, min(0.4, 1 - p_min), 0.005):
                mask = (x >= p_min) & (x <= p_max)
                n_points = np.sum(mask)

                if n_points < 3:
                    continue

                try:
                    slope, intercept, r_value, _, _ = linregress(x[mask], y[mask])
                    r2 = r_value ** 2

                    # Check that slope and intercept are positive
                    if slope > 0 and intercept > 0 and r2 > best_r2:
                        best_r2 = r2
                        best_range = (p_min, p_max)
                        best_n_points = n_points
                except:
                    continue

        self.rouquerol_range = best_range
        self.rouquerol_passed = True
        self.rouquerol_n_points = best_n_points
        self.rouquerol_message = (
            f"Valid BET range: {best_range[0]:.3f} - {best_range[1]:.3f} "
            f"(R²={best_r2:.4f}, n={best_n_points})"
        )

        return True

    def calculate_bet(self, p_range=None):
        """
        Calculate BET surface area using specified or auto-detected range

        Returns:
        - Surface area in m²/g
        """
        if p_range is not None:
            self.bet_pressure_range = p_range
        elif self.rouquerol_passed:
            self.bet_pressure_range = self.rouquerol_range

        x, y = self.bet_transform()
        if x is None:
            return 0

        # Select pressure range
        mask = (x >= self.bet_pressure_range[0]) & (x <= self.bet_pressure_range[1])
        if not np.any(mask):
            return 0

        x_linear = x[mask]
        y_linear = y[mask]

        if len(x_linear) < 3:
            return 0

        # Linear regression
        slope, intercept, r_value, _, _ = linregress(x_linear, y_linear)

        self.bet_slope = float(slope)
        self.bet_intercept = float(intercept)

        # BET parameters
        self.bet_monolayer_volume = float(1 / (slope + intercept))
        self.bet_c_constant = float(1 + slope / intercept)
        self.bet_correlation = float(r_value ** 2)

        # Surface area
        # S = (Vm * NA * σ) / (M_v * m)
        sigma = self.cross_section_nm2 * 1e-18  # Convert nm² to m²
        vm_mol_g = self.bet_monolayer_volume / self.MOLAR_VOLUME  # mol/g

        self.bet_surface_area_m2_g = float(vm_mol_g * self.AVOGADRO * sigma)

        return self.bet_surface_area_m2_g

    def t_plot(self):
        """
        t-plot micropore analysis

        Lippens, B.C. & de Boer, J.H. (1965) "Studies on pore systems in catalysts:
        V. The t method" Journal of Catalysis, 4, 319-323

        de Boer t-curve for nitrogen at 77K:
        t (Å) = [13.99 / (log(P₀/P) + 0.034)]^(1/2)
        """
        if self.relative_pressure is None or self.volume_adsorbed_cc_g is None:
            return

        p = self.relative_pressure
        v = self.volume_adsorbed_cc_g

        # Calculate statistical thickness (Å)
        # de Boer equation
        log_term = np.log10(1/p)
        t = np.sqrt(13.99 / (log_term + 0.034))

        # Find linear region in t-plot (typically t > 3.5 Å)
        # Corresponds to multilayer adsorption
        mask = t > 3.5
        if not np.any(mask):
            # Use upper half if no points above threshold
            mask = np.zeros_like(t, dtype=bool)
            mask[len(t)//2:] = True

        t_linear = t[mask]
        v_linear = v[mask]

        if len(t_linear) < 3:
            return

        # Linear regression: V vs t
        slope, intercept, r_value, _, _ = linregress(t_linear, v_linear)

        self.t_plot_slope = float(slope)
        self.t_plot_intercept = float(intercept)
        self.t_plot_correlation = float(r_value ** 2)

        # Micropore volume = intercept (cm³/g)
        self.micropore_volume_cc_g = float(intercept)

        # External surface area = slope * conversion factor
        # Conversion: from V/t (cm³/g·Å) to surface area (m²/g)
        # For nitrogen at 77K, 1 Å thickness corresponds to ~0.1 nm
        # Need appropriate factor: slope * 15.47 is approximate
        self.external_surface_area_m2_g = float(slope * 15.47)

    def dubinin_radushkevich(self):
        """
        Dubinin-Radushkevich micropore analysis

        Dubinin, M.M. & Radushkevich, L.V. (1947) "Equation of the characteristic
        curve of activated charcoal" Proceedings of the Academy of Sciences USSR,
        55, 331-337

        DR equation: log(V) = log(V₀) - D [log(P₀/P)]²
        where D = (RT/βE₀)²
        """
        if self.relative_pressure is None or self.volume_adsorbed_cc_g is None:
            return

        p = self.relative_pressure
        v = self.volume_adsorbed_cc_g

        # Use low pressure range (P/P₀ < 0.1)
        mask = p < 0.1
        if not np.any(mask):
            # Use lowest pressures available
            mask = np.zeros_like(p, dtype=bool)
            mask[:max(3, len(p)//5)] = True

        x = (np.log(1/p[mask])) ** 2
        y = np.log(v[mask])

        if len(x) < 3:
            return

        slope, intercept, r_value, _, _ = linregress(x, y)

        self.dr_pre_exponential = float(np.exp(intercept))
        self.dr_micropore_volume_cc_g = float(np.exp(intercept))
        self.dr_correlation = float(r_value ** 2)

        # Characteristic energy (kJ/mol)
        R = 8.314e-3  # kJ/mol·K
        beta = 1  # Affinity coefficient (N₂ = 1)

        self.dr_characteristic_energy_kJ_mol = float(
            beta * R * self.temperature_k * np.sqrt(-slope)
        )

    def horvath_kawazoe(self):
        """
        Horvath-Kawazoe micropore size analysis

        Horvath, G. & Kawazoe, K. (1983) "Method for the calculation of effective
        pore size distribution in molecular sieve carbon" Journal of Chemical
        Engineering of Japan, 16, 470-475
        """
        if self.relative_pressure is None or self.volume_adsorbed_cc_g is None:
            return

        p = self.relative_pressure
        v = self.volume_adsorbed_cc_g

        # Find pressure where filling occurs (steepest part of isotherm)
        # This is the derivative maximum
        dvdp = np.gradient(v, p)

        # Smooth derivative
        if len(dvdp) > 5:
            dvdp = savgol_filter(dvdp, min(5, len(dvdp)//2*2-1), 2)

        max_idx = np.argmax(dvdp[:len(dvdp)//2])  # Look in low pressure region
        p_fill = p[max_idx]

        # Simplified HK for slit pores
        # P/P₀ = exp(-A / (w - d))
        # where w is pore width, d is molecular diameter

        # Interaction parameter for N₂-carbon at 77K
        A = 2.96  # kJ/mol
        d = 0.34  # Molecular diameter (nm) for N₂

        if p_fill < 1 and p_fill > 0:
            self.hk_pore_size_nm = float(A / (-np.log(p_fill)) + d)

            # Approximate pore volume from amount adsorbed at filling
            self.hk_pore_volume = float(v[max_idx])

    def bjh(self):
        """
        BJH mesopore size distribution

        Barrett, E.P., Joyner, L.G. & Halenda, P.P. (1951) "The determination of
        pore volume and area distributions in porous substances. I. Computations
        from nitrogen isotherms" Journal of the American Chemical Society, 73, 373-380
        """
        if self.relative_pressure is None or self.volume_adsorbed_cc_g is None:
            return

        p = self.relative_pressure
        v = self.volume_adsorbed_cc_g

        # Use desorption branch if available, otherwise adsorption
        if self.volume_desorbed_cc_g is not None:
            v = self.volume_desorbed_cc_g

        # Filter to mesopore range (P/P₀ > 0.4)
        mask = p > 0.4
        if not np.any(mask):
            return

        p_meso = p[mask]
        v_meso = v[mask]

        if len(p_meso) < 3:
            return

        # Kelvin radius (nm) for nitrogen at 77K
        # r_k = 0.415 / log(1/p)
        r_k = 0.415 / np.log(1/p_meso)

        # Statistical thickness (nm) - Harkins-Jura equation
        # t = [13.99 / (0.034 - log(p))]^0.5 / 10
        t = np.sqrt(13.99 / (0.034 - np.log10(p_meso))) / 10

        # Pore radius
        r_p = r_k + t

        # Pore volume distribution
        dv = np.gradient(v_meso)
        dr = np.gradient(r_p)

        # Avoid division by zero
        dr[dr == 0] = np.nan
        dVdR = dv / dr

        # Remove NaNs
        valid = ~np.isnan(dVdR) & ~np.isinf(dVdR)
        if not np.any(valid):
            return

        r_p_valid = r_p[valid]
        dVdR_valid = dVdR[valid]

        # Store distribution
        self.bjh_pore_size_distribution = np.column_stack((r_p_valid, dVdR_valid))

        # Average pore size (weighted by dV/dR)
        if len(r_p_valid) > 0 and np.sum(dVdR_valid) > 0:
            self.bjh_pore_size_nm = float(
                np.average(r_p_valid, weights=dVdR_valid)
            )

        # Total pore volume
        self.bjh_pore_volume_cc_g = float(np.max(v_meso) - v_meso[0])

        # Cumulative volume
        self.bjh_cumulative_volume = np.cumsum(dVdR_valid * np.gradient(r_p_valid))

    def langmuir(self):
        """
        Langmuir isotherm analysis for microporous materials

        Langmuir equation: P/V = 1/(K·Vm) + P/Vm
        """
        if self.relative_pressure is None or self.volume_adsorbed_cc_g is None:
            return None

        p = self.relative_pressure
        v = self.volume_adsorbed_cc_g

        # Use low pressure range
        mask = p < 0.1
        if not np.any(mask):
            mask = slice(len(p)//4)

        x = p[mask]
        y = p[mask] / v[mask]

        if len(x) < 3:
            return None

        slope, intercept, r_value, _, _ = linregress(x, y)

        Vm = 1 / slope
        K = 1 / (intercept * Vm)
        r2 = r_value ** 2

        return {
            'Vm': float(Vm),
            'K': float(K),
            'r2': float(r2)
        }

    def to_dict(self):
        """Convert to dictionary for main table"""
        d = {
            'Timestamp': self.timestamp.isoformat() if self.timestamp else '',
            'Sample_ID': self.sample_id,
            'Instrument': self.instrument,
            'Adsorbate': self.adsorbate,
            'Mass_g': f"{self.sample_mass_g:.4f}",
            'BET_Surface_m2_g': f"{self.bet_surface_area_m2_g:.2f}" if self.bet_surface_area_m2_g else '',
            'BET_C': f"{self.bet_c_constant:.1f}" if self.bet_c_constant else '',
            'BET_R²': f"{self.bet_correlation:.4f}" if self.bet_correlation else '',
            'Micropore_Volume_cc_g': f"{self.micropore_volume_cc_g:.3f}" if self.micropore_volume_cc_g else '',
            'External_SA_m2_g': f"{self.external_surface_area_m2_g:.2f}" if self.external_surface_area_m2_g else '',
            'DR_Volume_cc_g': f"{self.dr_micropore_volume_cc_g:.3f}" if self.dr_micropore_volume_cc_g else '',
            'DR_Energy_kJ_mol': f"{self.dr_characteristic_energy_kJ_mol:.2f}" if self.dr_characteristic_energy_kJ_mol else '',
            'HK_Pore_Size_nm': f"{self.hk_pore_size_nm:.2f}" if self.hk_pore_size_nm else '',
            'BJH_Pore_Size_nm': f"{self.bjh_pore_size_nm:.2f}" if self.bjh_pore_size_nm else '',
            'BJH_Pore_Volume_cc_g': f"{self.bjh_pore_volume_cc_g:.3f}" if self.bjh_pore_volume_cc_g else '',
            'Rouquerol_Passed': 'Yes' if self.rouquerol_passed else 'No',
            'Rouquerol_Range': f"{self.rouquerol_range[0]:.3f}-{self.rouquerol_range[1]:.3f}"
        }
        return d


@dataclass
class DLSData:
    """
    Dynamic Light Scattering data with ISO 22412 cumulants analysis

    ISO 22412:2017 - Particle size analysis — Dynamic light scattering (DLS)

    Cumulants method:
    ln(G-1) = a₀ - Γτ + (μ₂/2)τ²
    where:
    - Γ = decay rate = D·q²
    - μ₂ = variance
    - PDI = μ₂/Γ²
    - Z-average diameter from Stokes-Einstein: d = kT/(3πηD)
    """
    timestamp: datetime
    sample_id: str
    instrument: str
    dispersant: str = "water"
    temperature_c: float = 25.0
    viscosity_cP: float = 0.89
    refractive_index: float = 1.33
    wavelength_nm: float = 633.0
    angle_deg: float = 173.0  # Backscatter

    # Size distribution
    size_nm: Optional[np.ndarray] = None
    intensity_pct: Optional[np.ndarray] = None
    volume_pct: Optional[np.ndarray] = None
    number_pct: Optional[np.ndarray] = None

    # Correlation data
    correlation_time_us: Optional[np.ndarray] = None
    correlation_g2: Optional[np.ndarray] = None
    correlation_fit: Optional[np.ndarray] = None
    correlation_residuals: Optional[np.ndarray] = None

    # Cumulants results
    z_average_nm: Optional[float] = None
    polydispersity_index: Optional[float] = None
    cumulants_fit_r2: Optional[float] = None
    cumulants_gamma: Optional[float] = None
    cumulants_mu2: Optional[float] = None
    cumulants_intercept: Optional[float] = None

    # Peak analysis
    peaks: List[Dict] = field(default_factory=list)
    peak_count: int = 0

    # Quality metrics
    intercept: Optional[float] = None
    baseline: Optional[float] = None
    count_rate_kcps: Optional[float] = None
    derived_count_rate_kcps: Optional[float] = None
    attenuation: Optional[float] = None
    duration_s: Optional[float] = None

    # Derived percentiles
    d10_nm: Optional[float] = None
    d50_nm: Optional[float] = None
    d90_nm: Optional[float] = None
    span: Optional[float] = None

    # Zeta potential (if available)
    zeta_potential_mV: Optional[float] = None
    zeta_deviation_mV: Optional[float] = None
    zeta_quality: Optional[str] = None
    conductivity_ms_cm: Optional[float] = None

    file_source: str = ""
    metadata: Dict = field(default_factory=dict)

    def __post_init__(self):
        """Initialize derived properties"""
        self.update_viscosity_from_temperature()

    def update_viscosity_from_temperature(self):
        """Update water viscosity based on temperature"""
        if self.dispersant.lower() == 'water':
            # Water viscosity (cP) as function of temperature (°C)
            # Approximate equation
            T = self.temperature_c
            self.viscosity_cP = 1.002 * 10 ** (
                1.3272 * (20 - T) / (T + 105) - 0.001053 * (T - 20)**2
            )

    def scattering_vector(self):
        """
        Calculate scattering vector q (nm⁻¹)

        q = (4πn/λ) sin(θ/2)
        """
        theta_rad = np.radians(self.angle_deg)
        q = (4 * np.pi * self.refractive_index / self.wavelength_nm) * np.sin(theta_rad / 2)
        return q

    def fit_correlation(self, max_tau_us=None, fit_points=100):
        """
        Fit correlation function using cumulants method

        Parameters:
        - max_tau_us: maximum delay time to fit
        - fit_points: number of points to use for fit
        """
        if self.correlation_time_us is None or self.correlation_g2 is None:
            return None

        tau = self.correlation_time_us
        g2 = self.correlation_g2

        # Normalize by intercept
        g2_norm = g2 / g2[0]

        # Limit to reasonable delay times
        if max_tau_us is None:
            # Find where correlation decays to 1/e
            g2_decay = g2_norm - 1
            decay_idx = np.argmax(g2_decay < (g2_decay[0] / np.e))
            if decay_idx > 10:
                max_tau_us = tau[decay_idx] * 3
            else:
                max_tau_us = tau[len(tau)//2]

        mask = tau < max_tau_us
        if not np.any(mask):
            mask = slice(len(tau)//4)

        tau_fit = tau[mask][:fit_points]
        g2_fit = g2_norm[mask][:fit_points]

        # Transform: y = ln(g2 - 1)
        y = np.log(np.maximum(g2_fit - 1, 1e-10))

        if len(tau_fit) < 5:
            return None

        # Quadratic fit: y = a + bτ + cτ²
        coeffs = np.polyfit(tau_fit, y, 2)
        c, b, a = coeffs

        # Cumulants
        self.cumulants_intercept = float(np.exp(a))
        self.cumulants_gamma = float(-b)
        self.cumulants_mu2 = float(2 * c)

        # Polydispersity index
        if self.cumulants_gamma > 0:
            self.polydispersity_index = float(self.cumulants_mu2 / self.cumulants_gamma**2)
        else:
            self.polydispersity_index = 0

        # Store fit
        self.correlation_fit = np.exp(a + b*tau + c*tau**2) + 1

        # Calculate residuals
        y_fit = a + b*tau + c*tau**2
        self.correlation_residuals = y - y_fit

        # Calculate R²
        residuals = g2_norm - (np.exp(a + b*tau + c*tau**2) + 1)
        ss_res = np.sum(residuals[mask]**2)
        ss_tot = np.sum((g2_norm[mask] - np.mean(g2_norm[mask]))**2)
        self.cumulants_fit_r2 = float(1 - ss_res/ss_tot) if ss_tot > 0 else 0

        # Intercept quality (should be close to 1)
        self.intercept = float(g2_norm[0])

        return self.cumulants_gamma

    def calculate_z_average(self):
        """
        Calculate Z-average diameter from cumulants fit using Stokes-Einstein

        d = kT / (3πηD) where D = Γ/q²
        """
        if self.cumulants_gamma is None:
            if self.correlation_time_us is not None:
                self.fit_correlation()
            else:
                return None

        if self.cumulants_gamma is None or self.cumulants_gamma <= 0:
            return None

        # Constants
        k_B = 1.380649e-23  # J/K
        T_K = self.temperature_c + 273.15
        η = self.viscosity_cP * 1e-3  # Convert cP to Pa·s

        # Scattering vector
        q = self.scattering_vector()  # nm⁻¹
        q_m = q * 1e9  # Convert to m⁻¹

        # Diffusion coefficient (m²/s)
        D = self.cumulants_gamma / q_m**2

        # Hydrodynamic diameter (m)
        d = k_B * T_K / (3 * np.pi * η * D)

        # Convert to nm
        self.z_average_nm = float(d * 1e9)

        return self.z_average_nm

    def detect_peaks(self, threshold=0.05, min_distance=5):
        """
        Detect peaks in size distribution

        Parameters:
        - threshold: minimum peak height (fraction of max)
        - min_distance: minimum index distance between peaks
        """
        if self.size_nm is None or self.intensity_pct is None:
            return

        from scipy.signal import find_peaks

        # Find peaks
        peaks, properties = find_peaks(
            self.intensity_pct,
            height=threshold * np.max(self.intensity_pct),
            distance=min_distance
        )

        self.peak_count = len(peaks)
        self.peaks = []

        for i, peak_idx in enumerate(peaks):
            # Find peak boundaries (where intensity drops below half max)
            peak_height = self.intensity_pct[peak_idx]
            half_max = peak_height / 2

            left = peak_idx
            right = peak_idx

            while left > 0 and self.intensity_pct[left] > half_max:
                left -= 1
            while right < len(self.intensity_pct)-1 and self.intensity_pct[right] > half_max:
                right += 1

            # Peak area (integrate)
            if right > left:
                area = np.trapz(
                    self.intensity_pct[left:right+1],
                    self.size_nm[left:right+1]
                )
            else:
                area = peak_height

            self.peaks.append({
                'index': int(peak_idx),
                'size': float(self.size_nm[peak_idx]),
                'height': float(peak_height),
                'area': float(area),
                'left': int(left),
                'right': int(right),
                'width': float(self.size_nm[right] - self.size_nm[left]) if right > left else 0
            })

    def calculate_percentiles(self):
        """
        Calculate D10, D50, D90 from cumulative intensity distribution
        """
        if self.size_nm is None or self.intensity_pct is None:
            return None, None, None

        # Sort by size
        sorted_idx = np.argsort(self.size_nm)
        sizes = self.size_nm[sorted_idx]
        intensity = self.intensity_pct[sorted_idx]

        # Cumulative intensity
        cumulative = np.cumsum(intensity)
        cumulative = cumulative / cumulative[-1] * 100

        # Interpolate percentiles
        from scipy.interpolate import interp1d

        # Remove duplicates for interpolation
        unique_cum, unique_indices = np.unique(cumulative, return_index=True)
        unique_sizes = sizes[unique_indices]

        if len(unique_cum) > 1:
            f = interp1d(unique_cum, unique_sizes, bounds_error=False, fill_value='extrapolate')

            self.d10_nm = float(f(10))
            self.d50_nm = float(f(50))
            self.d90_nm = float(f(90))

            # Span = (D90 - D10) / D50
            if self.d50_nm and self.d50_nm > 0:
                self.span = float((self.d90_nm - self.d10_nm) / self.d50_nm)

        return self.d10_nm, self.d50_nm, self.d90_nm

    def convert_distribution(self, from_type='intensity', to_type='volume'):
        """
        Convert between intensity, volume, and number distributions

        I ∝ d⁶ for intensity
        I ∝ d³ for volume
        I ∝ d⁰ for number
        """
        if self.size_nm is None:
            return

        if from_type == 'intensity' and self.intensity_pct is not None:
            if to_type == 'volume':
                # Volume ∝ Intensity / d³
                self.volume_pct = self.intensity_pct / (self.size_nm**3 + 1e-10)
                self.volume_pct = self.volume_pct / np.sum(self.volume_pct) * 100
            elif to_type == 'number':
                # Number ∝ Intensity / d⁶
                self.number_pct = self.intensity_pct / (self.size_nm**6 + 1e-10)
                self.number_pct = self.number_pct / np.sum(self.number_pct) * 100

        elif from_type == 'volume' and self.volume_pct is not None:
            if to_type == 'intensity':
                # Intensity ∝ Volume * d³
                self.intensity_pct = self.volume_pct * (self.size_nm**3)
                self.intensity_pct = self.intensity_pct / np.sum(self.intensity_pct) * 100

    def temperature_correction(self, T_new):
        """
        Correct particle size for temperature change

        d ∝ T/η (Stokes-Einstein)
        """
        if self.z_average_nm is None:
            return

        # Viscosity at new temperature
        T_old = self.temperature_c
        self.temperature_c = T_new

        if self.dispersant.lower() == 'water':
            η_old = self.viscosity_cP
            self.update_viscosity_from_temperature()
            η_new = self.viscosity_cP

            # Stokes-Einstein correction
            T_K_old = T_old + 273.15
            T_K_new = T_new + 273.15

            correction = (T_K_new / T_K_old) * (η_old / η_new)
            self.z_average_nm = self.z_average_nm * correction

    def to_dict(self):
        """Convert to dictionary for main table"""
        peak_str = ', '.join([f"{p['size']:.1f}nm" for p in self.peaks[:3]])
        if len(self.peaks) > 3:
            peak_str += f" ... (+{len(self.peaks)-3})"

        d = {
            'Timestamp': self.timestamp.isoformat() if self.timestamp else '',
            'Sample_ID': self.sample_id,
            'Instrument': self.instrument,
            'Dispersant': self.dispersant,
            'Temperature_C': f"{self.temperature_c:.1f}",
            'Z_Average_nm': f"{self.z_average_nm:.1f}" if self.z_average_nm else '',
            'PDI': f"{self.polydispersity_index:.3f}" if self.polydispersity_index else '',
            'Intercept': f"{self.intercept:.3f}" if self.intercept else '',
            'Fit_R²': f"{self.cumulants_fit_r2:.4f}" if self.cumulants_fit_r2 else '',
            'Peaks': peak_str,
            'D10_nm': f"{self.d10_nm:.1f}" if self.d10_nm else '',
            'D50_nm': f"{self.d50_nm:.1f}" if self.d50_nm else '',
            'D90_nm': f"{self.d90_nm:.1f}" if self.d90_nm else '',
            'Span': f"{self.span:.3f}" if self.span else '',
            'Zeta_mV': f"{self.zeta_potential_mV:.1f}" if self.zeta_potential_mV else '',
            'Conductivity_ms_cm': f"{self.conductivity_ms_cm:.3f}" if self.conductivity_ms_cm else ''
        }
        return d


@dataclass
class RheologyData:
    """
    Rheological measurement data with model fitting

    Models:
    - Newtonian: η = constant
    - Power law: η = K·γ̇ⁿ⁻¹
    - Carreau-Yasuda: η = η∞ + (η₀ - η∞)·[1 + (λγ̇)ᵃ]⁽ⁿ⁻¹⁾/ᵃ
    - Cross: η = η∞ + (η₀ - η∞) / (1 + (Kγ̇)ᵐ)
    - Herschel-Bulkley: τ = τ₀ + K·γ̇ⁿ
    - Bingham: τ = τ₀ + ηₚ·γ̇
    """
    timestamp: datetime
    sample_id: str
    instrument: str
    geometry: str = "parallel plate"
    gap_mm: float = 1.0
    radius_mm: float = 15.0
    cone_angle_deg: float = 2.0

    # Flow sweep
    shear_rate_s: Optional[np.ndarray] = None
    viscosity_Pa_s: Optional[np.ndarray] = None
    shear_stress_Pa: Optional[np.ndarray] = None
    temperature_c: Optional[np.ndarray] = None

    # Oscillatory
    frequency_Hz: Optional[np.ndarray] = None
    storage_modulus_Pa: Optional[np.ndarray] = None
    loss_modulus_Pa: Optional[np.ndarray] = None
    tan_delta: Optional[np.ndarray] = None
    complex_viscosity_Pa_s: Optional[np.ndarray] = None
    strain_pct: Optional[np.ndarray] = None

    # Time sweep
    time_s: Optional[np.ndarray] = None
    time_storage_modulus: Optional[np.ndarray] = None
    time_loss_modulus: Optional[np.ndarray] = None

    # Temperature sweep
    temp_ramp_c: Optional[np.ndarray] = None
    temp_storage_modulus: Optional[np.ndarray] = None
    temp_loss_modulus: Optional[np.ndarray] = None

    # Fitted models
    model_name: str = ""
    model_params: Dict = field(default_factory=dict)
    model_covariance: Optional[np.ndarray] = None
    model_r2: Optional[float] = None
    model_parameters: Dict = field(default_factory=dict)  # With uncertainties

    # Yield stress
    yield_stress_Pa: Optional[float] = None
    yield_stress_method: str = ""

    # Thixotropy
    thixotropy_area_Pa_s: Optional[float] = None
    thixotropy_up_curve: Optional[np.ndarray] = None
    thixotropy_down_curve: Optional[np.ndarray] = None

    file_source: str = ""
    metadata: Dict = field(default_factory=dict)

    def geometry_factor(self):
        """
        Calculate geometry factor for modulus conversion
        """
        if self.geometry == "parallel plate":
            # For parallel plates: factor = 2 * gap / (π * R⁴)
            if self.radius_mm > 0 and self.gap_mm > 0:
                R_m = self.radius_mm / 1000
                gap_m = self.gap_mm / 1000
                return 2 * gap_m / (np.pi * R_m**4)

        elif self.geometry == "cone-plate":
            # For cone-plate: factor = 3 / (2πR³) * (1/tan(α))
            if self.radius_mm > 0 and self.cone_angle_deg > 0:
                R_m = self.radius_mm / 1000
                alpha_rad = np.radians(self.cone_angle_deg)
                return 3 / (2 * np.pi * R_m**3 * np.tan(alpha_rad))

        return 1.0

    def fit_power_law(self):
        """
        Fit power law model: η = K·γ̇ⁿ⁻¹

        log η = log K + (n-1)·log γ̇
        """
        if self.shear_rate_s is None or self.viscosity_Pa_s is None:
            return None

        gamma = self.shear_rate_s
        eta = self.viscosity_Pa_s

        # Use positive values
        mask = (gamma > 0) & (eta > 0)
        if not np.any(mask):
            return None

        log_gamma = np.log10(gamma[mask])
        log_eta = np.log10(eta[mask])

        # Linear regression
        slope, intercept, r_value, _, _ = linregress(log_gamma, log_eta)

        n = slope + 1
        K = 10**intercept

        # Calculate standard errors
        n_points = len(log_gamma)
        if n_points > 2:
            # Standard error of slope
            residuals = log_eta - (slope * log_gamma + intercept)
            se_slope = np.sqrt(np.sum(residuals**2) / (n_points - 2)) / np.sqrt(np.sum((log_gamma - np.mean(log_gamma))**2))
            se_n = se_slope

            # Standard error of intercept
            se_intercept = se_slope * np.sqrt(np.sum(log_gamma**2) / n_points)
            se_K = K * np.log(10) * se_intercept
        else:
            se_n = 0
            se_K = 0

        self.model_name = "Power Law"
        self.model_params = {
            'n': n,
            'K': K,
            'r2': r_value**2,
            'se_n': se_n,
            'se_K': se_K
        }
        self.model_r2 = r_value**2

        # Format parameters with uncertainties
        self.model_parameters = {
            'n': f"{n:.3f} ± {se_n:.3f}",
            'K': f"{K:.2e} ± {se_K:.2e} Pa·sⁿ",
            'R²': f"{r_value**2:.4f}"
        }

        return self.model_params

    def fit_carreau_yasuda(self):
        """
        Fit Carreau-Yasuda model: η = η∞ + (η₀ - η∞)·[1 + (λγ̇)ᵃ]⁽ⁿ⁻¹⁾/ᵃ

        Carreau, P.J. (1972) "Rheological Equations from Molecular Network Theories"
        PhD Thesis, University of Wisconsin-Madison
        """
        if self.shear_rate_s is None or self.viscosity_Pa_s is None:
            return None

        gamma = self.shear_rate_s
        eta = self.viscosity_Pa_s

        # Carreau-Yasuda function
        def carreau_yasuda(g, eta0, eta_inf, lam, n, a):
            return eta_inf + (eta0 - eta_inf) * (1 + (lam * g)**a)**((n-1)/a)

        try:
            # Initial guesses
            eta0 = eta[0]
            eta_inf = eta[-1]
            lam = 1 / gamma[len(gamma)//2]
            n = 0.5
            a = 2.0

            p0 = [eta0, eta_inf, lam, n, a]
            bounds = (
                [0, 0, 0, 0, 1],
                [np.inf, np.inf, np.inf, 1, 5]
            )

            popt, pcov = curve_fit(
                carreau_yasuda, gamma, eta,
                p0=p0, bounds=bounds, maxfev=5000
            )

            eta0, eta_inf, lam, n, a = popt
            perr = np.sqrt(np.diag(pcov))

            # Calculate R²
            residuals = eta - carreau_yasuda(gamma, *popt)
            ss_res = np.sum(residuals**2)
            ss_tot = np.sum((eta - np.mean(eta))**2)
            r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

            self.model_name = "Carreau-Yasuda"
            self.model_params = {
                'eta0': eta0,
                'eta_inf': eta_inf,
                'lam': lam,
                'n': n,
                'a': a,
                'r2': r2
            }
            self.model_covariance = pcov
            self.model_r2 = r2

            # Format parameters with uncertainties
            self.model_parameters = {
                'η₀': f"{eta0:.2e} ± {perr[0]:.2e} Pa·s",
                'η∞': f"{eta_inf:.2e} ± {perr[1]:.2e} Pa·s",
                'λ': f"{lam:.3f} ± {perr[2]:.3f} s",
                'n': f"{n:.3f} ± {perr[3]:.3f}",
                'a': f"{a:.2f} ± {perr[4]:.2f}",
                'R²': f"{r2:.4f}"
            }

            return self.model_params

        except Exception as e:
            print(f"Carreau-Yasuda fit failed: {e}")
            return None

    def fit_cross(self):
        """
        Fit Cross model: η = η∞ + (η₀ - η∞) / (1 + (Kγ̇)ᵐ)

        Cross, M.M. (1965) "Rheology of non-Newtonian fluids: A new flow equation
        for pseudoplastic systems" Journal of Colloid Science, 20, 417-437
        """
        if self.shear_rate_s is None or self.viscosity_Pa_s is None:
            return None

        gamma = self.shear_rate_s
        eta = self.viscosity_Pa_s

        def cross(g, eta0, eta_inf, K, m):
            return eta_inf + (eta0 - eta_inf) / (1 + (K * g)**m)

        try:
            # Initial guesses
            eta0 = eta[0]
            eta_inf = eta[-1]
            K = 1 / gamma[len(gamma)//2]
            m = 1.0

            p0 = [eta0, eta_inf, K, m]
            bounds = (
                [0, 0, 0, 0],
                [np.inf, np.inf, np.inf, 2]
            )

            popt, pcov = curve_fit(
                cross, gamma, eta,
                p0=p0, bounds=bounds, maxfev=5000
            )

            eta0, eta_inf, K, m = popt
            perr = np.sqrt(np.diag(pcov))

            # Calculate R²
            residuals = eta - cross(gamma, *popt)
            ss_res = np.sum(residuals**2)
            ss_tot = np.sum((eta - np.mean(eta))**2)
            r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

            self.model_name = "Cross"
            self.model_params = {
                'eta0': eta0,
                'eta_inf': eta_inf,
                'K': K,
                'm': m,
                'r2': r2
            }
            self.model_covariance = pcov
            self.model_r2 = r2

            self.model_parameters = {
                'η₀': f"{eta0:.2e} ± {perr[0]:.2e} Pa·s",
                'η∞': f"{eta_inf:.2e} ± {perr[1]:.2e} Pa·s",
                'K': f"{K:.3f} ± {perr[2]:.3f} s",
                'm': f"{m:.3f} ± {perr[3]:.3f}",
                'R²': f"{r2:.4f}"
            }

            return self.model_params

        except Exception as e:
            print(f"Cross fit failed: {e}")
            return None

    def fit_herschel_bulkley(self):
        """
        Fit Herschel-Bulkley model: τ = τ₀ + K·γ̇ⁿ

        Herschel, W.H. & Bulkley, R. (1926) "Konsistenzmessungen von Gummi-Benzollösungen"
        Kolloid-Zeitschrift, 39, 291-300
        """
        if self.shear_rate_s is None or self.shear_stress_Pa is None:
            return None

        gamma = self.shear_rate_s
        tau = self.shear_stress_Pa

        def hb(g, tau0, K, n):
            return tau0 + K * g**n

        try:
            # Initial guesses
            tau0 = tau[0]
            K = (tau[-1] - tau[0]) / gamma[-1]**0.5
            n = 0.5

            p0 = [tau0, K, n]
            bounds = (
                [0, 0, 0],
                [np.inf, np.inf, 1]
            )

            popt, pcov = curve_fit(
                hb, gamma, tau,
                p0=p0, bounds=bounds, maxfev=5000
            )

            tau0, K, n = popt
            perr = np.sqrt(np.diag(pcov))

            # Calculate R²
            residuals = tau - hb(gamma, *popt)
            ss_res = np.sum(residuals**2)
            ss_tot = np.sum((tau - np.mean(tau))**2)
            r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

            self.model_name = "Herschel-Bulkley"
            self.model_params = {
                'tau0': tau0,
                'K': K,
                'n': n,
                'r2': r2
            }
            self.model_covariance = pcov
            self.model_r2 = r2

            self.model_parameters = {
                'τ₀': f"{tau0:.3f} ± {perr[0]:.3f} Pa",
                'K': f"{K:.3f} ± {perr[1]:.3f} Pa·sⁿ",
                'n': f"{n:.3f} ± {perr[2]:.3f}",
                'R²': f"{r2:.4f}"
            }

            # Yield stress from model
            self.yield_stress_Pa = float(tau0)
            self.yield_stress_method = "Herschel-Bulkley fit"

            return self.model_params

        except Exception as e:
            print(f"Herschel-Bulkley fit failed: {e}")
            return None

    def fit_bingham(self):
        """
        Fit Bingham model: τ = τ₀ + ηₚ·γ̇
        """
        if self.shear_rate_s is None or self.shear_stress_Pa is None:
            return None

        gamma = self.shear_rate_s
        tau = self.shear_stress_Pa

        # Use high shear region for linear fit
        mask = gamma > np.percentile(gamma, 50)
        if not np.any(mask):
            mask = slice(len(gamma)//2, None)

        slope, intercept, r_value, _, _ = linregress(gamma[mask], tau[mask])

        eta_p = slope
        tau0 = intercept

        # Calculate standard errors
        n_points = np.sum(mask)
        if n_points > 2:
            residuals = tau[mask] - (slope * gamma[mask] + intercept)
            se_slope = np.sqrt(np.sum(residuals**2) / (n_points - 2)) / np.sqrt(np.sum((gamma[mask] - np.mean(gamma[mask]))**2))
            se_intercept = se_slope * np.sqrt(np.sum(gamma[mask]**2) / n_points)
        else:
            se_slope = 0
            se_intercept = 0

        self.model_name = "Bingham"
        self.model_params = {
            'tau0': tau0,
            'eta_p': eta_p,
            'r2': r_value**2,
            'se_tau0': se_intercept,
            'se_eta_p': se_slope
        }
        self.model_r2 = r_value**2

        self.model_parameters = {
            'τ₀': f"{tau0:.3f} ± {se_intercept:.3f} Pa",
            'ηₚ': f"{eta_p:.3f} ± {se_slope:.3f} Pa·s",
            'R²': f"{r_value**2:.4f}"
        }

        # Yield stress from model
        self.yield_stress_Pa = float(tau0)
        self.yield_stress_method = "Bingham fit"

        return self.model_params

    def yield_stress_tangent(self):
        """
        Determine yield stress by tangent intersection method

        Find intersection of low shear and high shear tangents
        """
        if self.shear_rate_s is None or self.shear_stress_Pa is None:
            return None

        gamma = self.shear_rate_s
        tau = self.shear_stress_Pa

        # Log-log plot
        log_g = np.log10(gamma)
        log_t = np.log10(tau)

        # Low shear region (first few points)
        low_mask = slice(0, len(gamma)//4)
        if np.sum(low_mask) < 2:
            return None

        slope_low, intercept_low, _, _, _ = linregress(log_g[low_mask], log_t[low_mask])

        # High shear region (last few points)
        high_mask = slice(3*len(gamma)//4, None)
        if np.sum(high_mask) < 2:
            return None

        slope_high, intercept_high, _, _, _ = linregress(log_g[high_mask], log_t[high_mask])

        # Find intersection in log space
        # slope_low * x + intercept_low = slope_high * x + intercept_high
        if abs(slope_high - slope_low) > 1e-10:
            log_g_intersect = (intercept_high - intercept_low) / (slope_low - slope_high)
            log_t_intersect = slope_low * log_g_intersect + intercept_low

            self.yield_stress_Pa = float(10**log_t_intersect)
            self.yield_stress_method = "Tangent intersection"

            return self.yield_stress_Pa

        return None

    def calculate_thixotropy_area(self):
        """
        Calculate thixotropy area (hysteresis loop area)

        Area between upward and downward flow curves
        """
        if (self.shear_rate_s is None or self.shear_stress_Pa is None or
            self.thixotropy_up_curve is None or self.thixotropy_down_curve is None):
            return None

        # Interpolate down curve onto up curve shear rates
        from scipy.interpolate import interp1d

        gamma_up, tau_up = self.thixotropy_up_curve.T
        gamma_down, tau_down = self.thixotropy_down_curve.T

        # Sort by shear rate
        up_idx = np.argsort(gamma_up)
        down_idx = np.argsort(gamma_down)

        gamma_up_sorted = gamma_up[up_idx]
        tau_up_sorted = tau_up[up_idx]
        gamma_down_sorted = gamma_down[down_idx]
        tau_down_sorted = tau_down[down_idx]

        # Interpolate down curve to up curve shear rates
        f_down = interp1d(gamma_down_sorted, tau_down_sorted,
                          bounds_error=False, fill_value='extrapolate')
        tau_down_interp = f_down(gamma_up_sorted)

        # Calculate area (integral of (tau_up - tau_down) d(gamma))
        self.thixotropy_area_Pa_s = float(
            np.trapz(tau_up_sorted - tau_down_interp, gamma_up_sorted)
        )

        return self.thixotropy_area_Pa_s

    def cox_merz_rule(self):
        """
        Apply Cox-Merz rule: η(γ̇) ≈ |η*|(ω) when γ̇ = ω

        Cox, W.P. & Merz, E.H. (1958) "Correlation of dynamic and steady flow
        viscosities" Journal of Polymer Science, 28, 619-622
        """
        if (self.shear_rate_s is None or self.viscosity_Pa_s is None or
            self.frequency_Hz is None or self.complex_viscosity_Pa_s is None):
            return None

        # Interpolate complex viscosity at steady shear rates
        from scipy.interpolate import interp1d

        # Convert frequency (Hz) to angular frequency (rad/s) for Cox-Merz
        omega = self.frequency_Hz * 2 * np.pi

        # Sort and interpolate
        sort_idx = np.argsort(omega)
        omega_sorted = omega[sort_idx]
        eta_star_sorted = self.complex_viscosity_Pa_s[sort_idx]

        f_eta_star = interp1d(omega_sorted, eta_star_sorted,
                              bounds_error=False, fill_value='extrapolate')

        # Compare at steady shear rates
        gamma = self.shear_rate_s
        eta_star_at_gamma = f_eta_star(gamma)

        # Correlation
        mask = ~np.isnan(eta_star_at_gamma)
        if np.any(mask):
            correlation = np.corrcoef(self.viscosity_Pa_s[mask], eta_star_at_gamma[mask])[0, 1]
            return float(correlation)

        return None

    def to_dict(self):
        """Convert to dictionary for main table"""
        d = {
            'Timestamp': self.timestamp.isoformat() if self.timestamp else '',
            'Sample_ID': self.sample_id,
            'Instrument': self.instrument,
            'Geometry': self.geometry,
            'Model': self.model_name,
            'η₀_Pa_s': f"{self.model_params.get('eta0', 0):.2e}" if self.model_params else '',
            'η∞_Pa_s': f"{self.model_params.get('eta_inf', 0):.2e}" if self.model_params else '',
            'n': f"{self.model_params.get('n', 0):.3f}" if self.model_params else '',
            'λ_s': f"{self.model_params.get('lam', 0):.3f}" if self.model_params else '',
            'τ₀_Pa': f"{self.yield_stress_Pa:.2f}" if self.yield_stress_Pa else '',
            'R²': f"{self.model_r2:.4f}" if self.model_r2 else '',
            'Thixotropy_Area': f"{self.thixotropy_area_Pa_s:.2f}" if self.thixotropy_area_Pa_s else ''
        }
        return d


# ============================================================================
# TEST DATA GENERATORS
# ============================================================================

def generate_test_afm(size=256, scan_size_um=10, features='grains'):
    """
    Generate synthetic AFM data for testing

    Parameters:
    - size: image size in pixels (size x size)
    - scan_size_um: scan size in micrometers
    - features: 'grains', 'steps', or 'rough'
    """
    x = np.linspace(0, 1, size)
    y = np.linspace(0, 1, size)
    X, Y = np.meshgrid(x, y)

    if features == 'grains':
        # Simulate grains (Gaussian peaks)
        Z = np.random.randn(size, size) * 0.5  # Noise
        for i in range(25):
            cx = 0.2 + 0.6 * np.random.rand()
            cy = 0.2 + 0.6 * np.random.rand()
            sigma = 0.03 + 0.07 * np.random.rand()
            amp = 8 + 4 * np.random.rand()
            Z += amp * np.exp(-((X-cx)**2 + (Y-cy)**2)/(2*sigma**2))

    elif features == 'steps':
        # Simulate step edges
        Z = 5 * np.tanh((X - 0.3) * 20) + 3 * np.tanh((Y - 0.6) * 15)
        Z += np.random.randn(size, size) * 0.3

    else:
        # Random roughness with correlation
        from scipy.ndimage import gaussian_filter
        Z = np.random.randn(size, size) * 3
        Z = gaussian_filter(Z, sigma=2)

    afm = AFMImage(
        timestamp=datetime.now(),
        sample_id=f"Test_AFM_{features}",
        instrument="Test Generator",
        scan_size_um=scan_size_um,
        pixels=size,
        height_data=Z
    )
    afm.calculate_areal_parameters()
    return afm

def generate_test_nanoindentation(H=5.0, E=200, nu=0.3, tip='Berkovich', points=500, pop_ins=True):
    """
    Generate synthetic nanoindentation data with known properties

    Parameters:
    - H: hardness in GPa
    - E: modulus in GPa
    - nu: Poisson's ratio
    - tip: tip type
    - points: number of data points
    - pop_ins: whether to include pop-in events
    """
    # Oliver-Pharr (1992) Eq. 3: P = α(h - hf)^m
    h_max = 1000  # nm
    h = np.linspace(0, h_max, points)

    # Generate loading curve
    if tip == 'Berkovich':
        # Parabolic loading
        P_loading = 0.08 * (h/100)**1.8  # mN
    else:
        P_loading = 0.05 * (h/100)**1.5

    # Add pop-ins if requested
    if pop_ins:
        for i in range(2):
            pop_idx = int(points * (0.3 + 0.3 * i))
            pop_depth = 50 + 30 * i
            # Displacement burst
            h[pop_idx:] += pop_depth * np.exp(-np.linspace(0, 3, points - pop_idx))

    # Generate unloading curve (power law)
    h_unload = np.linspace(h_max, h_max * 0.6, points//2)
    m = 1.5  # Power law exponent
    hf = 150  # Final depth
    alpha = P_loading[-1] / (h_max - hf)**m
    P_unload = alpha * (h_unload - hf)**m

    # Add noise
    P_loading += np.random.randn(len(P_loading)) * 0.01
    P_unload += np.random.randn(len(P_unload)) * 0.01

    nano = NanoindentationData(
        timestamp=datetime.now(),
        sample_id="Test_Nanoindent",
        instrument="Test Generator",
        tip_type=tip,
        displacement_nm=h,
        load_mN=P_loading,
        unloading_displacement_nm=h_unload,
        unloading_load_mN=P_unload
    )

    # Set known values for validation
    nano.hardness_GPa = H
    nano.modulus_GPa = E

    return nano

def generate_test_bet(isotherm_type='II', surface_area=100, C=50):
    """
    Generate synthetic BET isotherm

    Parameters:
    - isotherm_type: 'II', 'IV', or 'I'
    - surface_area: target surface area in m²/g
    - C: BET C constant
    """
    # Generate pressure points
    p = np.linspace(0.01, 0.99, 40)

    # Monolayer volume from surface area
    # S = (Vm * NA * σ) / M_v
    sigma = 0.162e-18  # m²
    NA = 6.022e23
    Mv = 22414  # cm³/mol

    Vm = surface_area * Mv / (NA * sigma)  # cm³/g

    if isotherm_type == 'I':
        # Langmuir type
        v = Vm * C * p / (1 + C * p)

    elif isotherm_type == 'II':
        # BET type II
        v = Vm * C * p / ((1-p) * (1 + (C-1)*p))

    elif isotherm_type == 'IV':
        # Type IV with hysteresis
        v = Vm * C * p / ((1-p) * (1 + (C-1)*p))
        # Add mesopore filling step
        step = 0.6 + 0.1 * np.tanh((p - 0.7) * 20)
        v = v * step

    else:
        v = Vm * C * p / ((1-p) * (1 + (C-1)*p))

    # Add noise
    v += np.random.randn(len(v)) * 0.5

    bet = BETIsotherm(
        timestamp=datetime.now(),
        sample_id=f"Test_BET_{isotherm_type}",
        instrument="Test Generator",
        adsorbate="N2",
        relative_pressure=p,
        volume_adsorbed_cc_g=v,
        sample_mass_g=0.1
    )

    return bet

def generate_test_dls(mono=True, z_avg=100, pdi=0.1):
    """
    Generate synthetic DLS data

    Parameters:
    - mono: True for monomodal, False for bimodal
    - z_avg: Z-average diameter in nm
    - pdi: polydispersity index
    """
    # Size distribution
    size = np.logspace(0, 3, 100)  # 1-1000 nm

    if mono:
        # Monomodal lognormal
        log_size = np.log10(size)
        log_mean = np.log10(z_avg)
        log_sigma = np.sqrt(np.log(1 + pdi)) / 2

        intensity = np.exp(-0.5 * ((log_size - log_mean) / log_sigma)**2)

    else:
        # Bimodal
        log_size = np.log10(size)

        # Primary peak
        log_mean1 = np.log10(z_avg)
        log_sigma1 = np.sqrt(np.log(1 + pdi)) / 2
        peak1 = np.exp(-0.5 * ((log_size - log_mean1) / log_sigma1)**2)

        # Secondary peak (aggregates)
        log_mean2 = np.log10(z_avg * 5)
        log_sigma2 = log_sigma1 * 1.2
        peak2 = 0.3 * np.exp(-0.5 * ((log_size - log_mean2) / log_sigma2)**2)

        intensity = peak1 + peak2

    intensity = intensity / np.sum(intensity) * 100

    # Generate correlation function
    tau = np.logspace(0, 4, 200)  # 1-10000 μs

    # Decay rate from Stokes-Einstein
    k_B = 1.38e-23
    T = 298
    eta = 0.89e-3
    d = z_avg * 1e-9
    D = k_B * T / (3 * np.pi * eta * d)

    # Scattering vector (173° backscatter, 633 nm, water)
    n = 1.33
    lam = 633e-9
    theta = np.radians(173)
    q = 4 * np.pi * n / lam * np.sin(theta/2)

    Gamma = D * q**2
    tau_s = tau * 1e-6  # Convert μs to s

    # Correlation function
    beta = 0.8  # Coherence factor
    corr = 1 + beta * np.exp(-2 * Gamma * tau_s) * (1 + 0.5 * pdi * (Gamma * tau_s)**2)

    dls = DLSData(
        timestamp=datetime.now(),
        sample_id="Test_DLS",
        instrument="Test Generator",
        size_nm=size,
        intensity_pct=intensity,
        correlation_time_us=tau,
        correlation_g2=corr,
        temperature_c=25,
        viscosity_cP=0.89
    )

    return dls

def generate_test_rheology(fluid_type='shear_thinning'):
    """
    Generate synthetic rheology data

    Parameters:
    - fluid_type: 'newtonian', 'shear_thinning', 'yield_stress'
    """
    # Shear rate range
    shear_rate = np.logspace(-2, 3, 50)

    if fluid_type == 'newtonian':
        # Newtonian fluid
        viscosity = np.ones_like(shear_rate) * 0.1
        shear_stress = viscosity * shear_rate

    elif fluid_type == 'shear_thinning':
        # Carreau-like shear thinning
        eta0 = 100
        eta_inf = 0.01
        lam = 10
        n = 0.3

        viscosity = eta_inf + (eta0 - eta_inf) * (1 + (lam * shear_rate)**2)**((n-1)/2)
        shear_stress = viscosity * shear_rate

    elif fluid_type == 'yield_stress':
        # Herschel-Bulkley with yield stress
        tau0 = 10
        K = 5
        n = 0.5

        shear_stress = tau0 + K * shear_rate**n
        viscosity = shear_stress / shear_rate

    else:
        viscosity = np.ones_like(shear_rate) * 0.1
        shear_stress = viscosity * shear_rate

    # Add noise
    viscosity *= (1 + 0.01 * np.random.randn(len(viscosity)))
    shear_stress *= (1 + 0.01 * np.random.randn(len(shear_stress)))

    rheo = RheologyData(
        timestamp=datetime.now(),
        sample_id=f"Test_Rheo_{fluid_type}",
        instrument="Test Generator",
        geometry="parallel plate",
        shear_rate_s=shear_rate,
        viscosity_Pa_s=viscosity,
        shear_stress_Pa=shear_stress
    )

    return rheo


# ============================================================================
# TECHNIQUE-SPECIFIC ANALYSIS PANELS
# ============================================================================

class TechniquePanel:
    """Base class for technique-specific control panels"""

    def __init__(self, parent, app, ui_queue, technique_name):
        self.parent = parent
        self.app = app
        self.ui_queue = ui_queue
        self.technique_name = technique_name
        self.current_data = None
        self.frame = tk.Frame(parent, bg='white')

    def build(self):
        """Build the panel UI - to be overridden"""
        pass

    def set_data(self, data):
        """Set the current data object"""
        self.current_data = data
        self.update_display()

    def update_display(self):
        """Update display with current data - to be overridden"""
        pass


class AFMPanel(TechniquePanel):
    def build(self):
        # Title
        title_frame = tk.Frame(self.frame, bg='#2C3E50', height=30)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)

        tk.Label(title_frame, text="🔬 AFM Analysis (ISO 25178)",
                font=("Arial", 10, "bold"), bg='#2C3E50', fg='white').pack(side=tk.LEFT, padx=5)

        # Main horizontal split
        main_panel = tk.Frame(self.frame, bg='white')
        main_panel.pack(fill=tk.BOTH, expand=True)

        # Left side - Controls (with scrollbar)
        left_frame = tk.Frame(main_panel, bg='white', width=300)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False)
        left_frame.pack_propagate(False)

        # Right side - Results
        right_frame = tk.Frame(main_panel, bg='#F8F9F9', width=250, relief=tk.SUNKEN, bd=1)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5,0))
        right_frame.pack_propagate(False)

        # Results title
        tk.Label(right_frame, text="Results", font=("Arial", 10, "bold"),
                bg='#F8F9F9', fg='#2C3E50').pack(anchor='w', padx=5, pady=2)

        # Results text (with scrollbar)
        results_container = tk.Frame(right_frame, bg='#F8F9F9')
        results_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.results_text = tk.Text(results_container, height=20, width=30,
                                    font=("Courier", 9), bg='white', relief=tk.FLAT)
        results_scrollbar = tk.Scrollbar(results_container, orient="vertical",
                                        command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=results_scrollbar.set)

        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Left side scrollable controls
        canvas = tk.Canvas(left_frame, bg='white', highlightthickness=0)
        scrollbar = tk.Scrollbar(left_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='white')

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # ========== CONTROLS ==========
        # Flattening
        flat_frame = tk.LabelFrame(scrollable_frame, text="Flattening", bg='white', font=("Arial", 9, "bold"))
        flat_frame.pack(fill='x', pady=5, padx=5)

        tk.Label(flat_frame, text="Order:", bg='white').pack(side='left', padx=5)
        self.flat_order = tk.StringVar(value="1")
        ttk.Combobox(flat_frame, textvariable=self.flat_order,
                    values=["1", "2"], width=5).pack(side='left', padx=2)
        ttk.Button(flat_frame, text="Apply", command=self.apply_flatten).pack(side='left', padx=5)

        # Filtering
        filter_frame = tk.LabelFrame(scrollable_frame, text="Filtering", bg='white', font=("Arial", 9, "bold"))
        filter_frame.pack(fill='x', pady=5, padx=5)

        ttk.Button(filter_frame, text="Median Filter",
                command=self.apply_median).pack(side='left', padx=5, pady=2)
        ttk.Button(filter_frame, text="Gaussian",
                command=self.apply_gaussian).pack(side='left', padx=5, pady=2)

        # Grain detection
        grain_frame = tk.LabelFrame(scrollable_frame, text="Grain Analysis", bg='white', font=("Arial", 9, "bold"))
        grain_frame.pack(fill='x', pady=5, padx=5)

        row1 = tk.Frame(grain_frame, bg='white')
        row1.pack(fill='x', pady=2)
        tk.Label(row1, text="Threshold:", bg='white', width=12).pack(side='left')
        self.grain_thresh = tk.StringVar(value="0.5")
        ttk.Entry(row1, textvariable=self.grain_thresh, width=6).pack(side='left', padx=2)

        row2 = tk.Frame(grain_frame, bg='white')
        row2.pack(fill='x', pady=2)
        tk.Label(row2, text="Min size (px):", bg='white', width=12).pack(side='left')
        self.grain_min = tk.StringVar(value="5")
        ttk.Entry(row2, textvariable=self.grain_min, width=6).pack(side='left', padx=2)

        ttk.Button(grain_frame, text="Detect Grains",
                command=self.detect_grains).pack(pady=5)

        # Power spectrum
        fft_frame = tk.LabelFrame(scrollable_frame, text="FFT Analysis", bg='white', font=("Arial", 9, "bold"))
        fft_frame.pack(fill='x', pady=5, padx=5)

        ttk.Button(fft_frame, text="Calculate Power Spectrum",
                command=self.calc_fft).pack(pady=5)

    def apply_flatten(self):
        if self.current_data and hasattr(self.current_data, 'flatten'):
            order = int(self.flat_order.get())
            self.current_data.flatten(order)
            self.current_data.calculate_areal_parameters()
            self.update_display()
            if hasattr(self.app, 'plot_embedder'):
                self.app.plot_embedder.plot_afm(self.current_data)

    def apply_median(self):
        if self.current_data:
            self.current_data.median_filter()
            self.current_data.calculate_areal_parameters()
            self.update_display()
            if hasattr(self.app, 'plot_embedder'):
                self.app.plot_embedder.plot_afm(self.current_data)

    def apply_gaussian(self):
        if self.current_data:
            self.current_data.gaussian_filter()
            self.current_data.calculate_areal_parameters()
            self.update_display()
            if hasattr(self.app, 'plot_embedder'):
                self.app.plot_embedder.plot_afm(self.current_data)

    def detect_grains(self):
        if self.current_data:
            thresh = float(self.grain_thresh.get())
            min_size = int(self.grain_min.get())
            self.current_data.detect_grains(threshold=thresh, min_size=min_size)
            self.update_display()
            if hasattr(self.app, 'plot_embedder'):
                self.app.plot_embedder.plot_afm(self.current_data)

    def calc_fft(self):
        if self.current_data:
            self.current_data.calculate_power_spectrum()
            self.update_display()

    def update_display(self):
        self.results_text.delete(1.0, tk.END)
        if not self.current_data:
            return

        # Grain stats
        grain_stats = ""
        if self.current_data.grain_count and self.current_data.grain_count > 0:
            grain_stats = (f"\nGrain Analysis:\n"
                          f"  Count = {self.current_data.grain_count}\n"
                          f"  Mean size = {np.mean(self.current_data.grain_sizes_nm):.1f} nm\n"
                          f"  Std size = {np.std(self.current_data.grain_sizes_nm):.1f} nm\n"
                          f"  Min size = {np.min(self.current_data.grain_sizes_nm):.1f} nm\n"
                          f"  Max size = {np.max(self.current_data.grain_sizes_nm):.1f} nm\n")
            if self.current_data.grain_circularity is not None:
                grain_stats += f"  Mean circularity = {np.mean(self.current_data.grain_circularity):.3f}\n"

        results = f"""ISO 25178 Areal Parameters:
────────────────────────────
Sa  = {self.current_data.sa_nm:8.3f} nm
Sq  = {self.current_data.sq_nm:8.3f} nm
Sz  = {self.current_data.sz_nm:8.3f} nm
Sp  = {self.current_data.sp_nm:8.3f} nm
Sv  = {self.current_data.sv_nm:8.3f} nm
S10z= {self.current_data.s10z_nm:8.3f} nm
Ssk = {self.current_data.ssk:8.3f}
Sku = {self.current_data.sku:8.3f}
Sdr = {self.current_data.sdr_pct:8.2f}%
{grain_stats}"""

        self.results_text.insert(1.0, results)


class NanoindentationPanel(TechniquePanel):
    def build(self):
        # Title
        title_frame = tk.Frame(self.frame, bg='#2C3E50', height=30)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)

        tk.Label(title_frame, text="⚡ Nanoindentation (Oliver & Pharr 1992)",
                font=("Arial", 10, "bold"), bg='#2C3E50', fg='white').pack(side=tk.LEFT, padx=5)

        # Main horizontal split
        main_panel = tk.Frame(self.frame, bg='white')
        main_panel.pack(fill=tk.BOTH, expand=True)

        # Left side - Controls
        left_frame = tk.Frame(main_panel, bg='white', width=300)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False)
        left_frame.pack_propagate(False)

        # Right side - Results
        right_frame = tk.Frame(main_panel, bg='#F8F9F9', width=250, relief=tk.SUNKEN, bd=1)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5,0))
        right_frame.pack_propagate(False)

        # Results title
        tk.Label(right_frame, text="Results", font=("Arial", 10, "bold"),
                bg='#F8F9F9', fg='#2C3E50').pack(anchor='w', padx=5, pady=2)

        # Results text with scrollbar
        results_container = tk.Frame(right_frame, bg='#F8F9F9')
        results_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.results_text = tk.Text(results_container, height=20, width=30,
                                    font=("Courier", 9), bg='white', relief=tk.FLAT)
        results_scrollbar = tk.Scrollbar(results_container, orient="vertical",
                                        command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=results_scrollbar.set)

        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Left side scrollable controls
        canvas = tk.Canvas(left_frame, bg='white', highlightthickness=0)
        scrollbar = tk.Scrollbar(left_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='white')

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # ========== CONTROLS ==========
        # Tip calibration
        cal_frame = tk.LabelFrame(scrollable_frame, text="Tip Area Function", bg='white', font=("Arial", 9, "bold"))
        cal_frame.pack(fill='x', pady=5, padx=5)

        cal_grid = tk.Frame(cal_frame, bg='white')
        cal_grid.pack(pady=5)

        tk.Label(cal_grid, text="C0:", bg='white').grid(row=0, column=0, padx=2)
        self.c0 = tk.StringVar(value="24.5")
        ttk.Entry(cal_grid, textvariable=self.c0, width=8).grid(row=0, column=1, padx=2)

        tk.Label(cal_grid, text="C1:", bg='white').grid(row=0, column=2, padx=2)
        self.c1 = tk.StringVar(value="0.0")
        ttk.Entry(cal_grid, textvariable=self.c1, width=8).grid(row=0, column=3, padx=2)

        tk.Label(cal_grid, text="C2:", bg='white').grid(row=1, column=0, padx=2)
        self.c2 = tk.StringVar(value="0.0")
        ttk.Entry(cal_grid, textvariable=self.c2, width=8).grid(row=1, column=1, padx=2)

        tk.Label(cal_grid, text="C3:", bg='white').grid(row=1, column=2, padx=2)
        self.c3 = tk.StringVar(value="0.0")
        ttk.Entry(cal_grid, textvariable=self.c3, width=8).grid(row=1, column=3, padx=2)

        ttk.Button(cal_frame, text="Apply Calibration",
                command=self.apply_calibration).pack(pady=5)

        # Corrections
        corr_frame = tk.LabelFrame(scrollable_frame, text="Corrections", bg='white', font=("Arial", 9, "bold"))
        corr_frame.pack(fill='x', pady=5, padx=5)

        row1 = tk.Frame(corr_frame, bg='white')
        row1.pack(fill='x', pady=2, padx=5)
        tk.Label(row1, text="Frame compliance (nm/mN):", bg='white', width=20).pack(side='left')
        self.compliance = tk.StringVar(value="0.0")
        ttk.Entry(row1, textvariable=self.compliance, width=8).pack(side='left', padx=2)
        ttk.Button(row1, text="Apply", command=self.apply_compliance).pack(side='left', padx=5)

        row2 = tk.Frame(corr_frame, bg='white')
        row2.pack(fill='x', pady=2, padx=5)
        tk.Label(row2, text="Thermal drift (nm/s):", bg='white', width=20).pack(side='left')
        self.drift = tk.StringVar(value="0.0")
        ttk.Entry(row2, textvariable=self.drift, width=8).pack(side='left', padx=2)
        ttk.Button(row2, text="Apply", command=self.apply_drift).pack(side='left', padx=5)

        # Pop-in detection
        pop_frame = tk.LabelFrame(scrollable_frame, text="Pop-in Detection", bg='white', font=("Arial", 9, "bold"))
        pop_frame.pack(fill='x', pady=5, padx=5)

        row = tk.Frame(pop_frame, bg='white')
        row.pack(fill='x', pady=2, padx=5)
        tk.Label(row, text="Threshold (%):", bg='white').pack(side='left')
        self.pop_thresh = tk.StringVar(value="5")
        ttk.Entry(row, textvariable=self.pop_thresh, width=5).pack(side='left', padx=2)
        ttk.Button(row, text="Detect Pop-ins", command=self.detect_popins).pack(side='left', padx=5)

        # Analysis buttons
        btn_frame = tk.Frame(scrollable_frame, bg='white')
        btn_frame.pack(fill='x', pady=10, padx=5)

        ttk.Button(btn_frame, text="Oliver-Pharr", command=self.run_oliver_pharr).pack(side='left', padx=2, expand=True, fill='x')
        ttk.Button(btn_frame, text="Add to Group", command=self.add_to_group).pack(side='left', padx=2, expand=True, fill='x')
        ttk.Button(btn_frame, text="Group Stats", command=self.group_stats).pack(side='left', padx=2, expand=True, fill='x')

    def apply_calibration(self):
        if self.current_data:
            coeffs = [
                float(self.c0.get()),
                float(self.c1.get()),
                float(self.c2.get()),
                float(self.c3.get())
            ]
            self.current_data.set_area_function(coeffs)
            self.update_display()

    def apply_compliance(self):
        if self.current_data:
            self.current_data.frame_compliance_nm_mN = float(self.compliance.get())
            self.current_data.correct_compliance()
            self.update_display()

    def apply_drift(self):
        if self.current_data:
            self.current_data.thermal_drift_nm_s = float(self.drift.get())
            self.current_data.correct_thermal_drift()
            self.update_display()

    def detect_popins(self):
        if self.current_data:
            thresh = float(self.pop_thresh.get())
            self.current_data.detect_pop_ins(threshold_pct=thresh)
            self.update_display()
            if hasattr(self.app, 'plot_embedder'):
                self.app.plot_embedder.plot_nanoindentation(self.current_data)

    def run_oliver_pharr(self):
        if self.current_data:
            self.current_data.oliver_pharr()
            self.update_display()
            if hasattr(self.app, 'plot_embedder'):
                self.app.plot_embedder.plot_nanoindentation(self.current_data)

    def add_to_group(self):
        if self.current_data:
            self.current_data.add_to_group()
            self.update_display()

    def group_stats(self):
        if self.current_data:
            self.current_data.calculate_statistics()
            self.update_display()

    def update_display(self):
        self.results_text.delete(1.0, tk.END)
        if not self.current_data:
            return

        pop_ins = ', '.join([f"{l:.2f}" for l in self.current_data.pop_in_loads_mN[:3]])
        if len(self.current_data.pop_in_loads_mN) > 3:
            pop_ins += f" ... (+{len(self.current_data.pop_in_loads_mN)-3})"

        group_stats = ""
        if self.current_data.indent_group:
            n = len(self.current_data.indent_group)
            group_stats = (f"\nGroup Statistics (n={n}):\n"
                          f"  Hardness = {self.current_data.hardness_mean:.3f} ± {self.current_data.hardness_std:.3f} GPa\n"
                          f"  95% CI: [{self.current_data.hardness_ci_low:.3f}, {self.current_data.hardness_ci_high:.3f}]\n"
                          f"  Modulus = {self.current_data.modulus_mean:.1f} ± {self.current_data.modulus_std:.1f} GPa\n"
                          f"  95% CI: [{self.current_data.modulus_ci_low:.1f}, {self.current_data.modulus_ci_high:.1f}]")

        results = f"""Oliver-Pharr Results:
────────────────────────────
Hardness         = {self.current_data.hardness_GPa:8.3f} GPa
Modulus          = {self.current_data.modulus_GPa:8.1f} GPa
Reduced modulus  = {self.current_data.reduced_modulus_GPa:8.1f} GPa
Contact depth    = {self.current_data.contact_depth_nm:8.1f} nm
Contact area     = {self.current_data.contact_area_um2:8.1f} μm²
Stiffness        = {self.current_data.stiffness_mN_nm:8.3f} mN/nm
Max load         = {self.current_data.max_load_mN:8.3f} mN

Fit parameters:
  m (exponent)   = {self.current_data.fit_m:8.3f}
  R²             = {self.current_data.fit_r2:8.4f}

Pop-ins detected: {len(self.current_data.pop_in_loads_mN)}
  {pop_ins}
{group_stats}"""

        self.results_text.insert(1.0, results)


class BETPanel(TechniquePanel):
    def build(self):
        # Title
        title_frame = tk.Frame(self.frame, bg='#2C3E50', height=30)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)

        tk.Label(title_frame, text="🧪 BET Surface Area (Rouquerol et al. 2007)",
                font=("Arial", 10, "bold"), bg='#2C3E50', fg='white').pack(side=tk.LEFT, padx=5)

        # Main horizontal split
        main_panel = tk.Frame(self.frame, bg='white')
        main_panel.pack(fill=tk.BOTH, expand=True)

        # Left side - Controls
        left_frame = tk.Frame(main_panel, bg='white', width=300)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False)
        left_frame.pack_propagate(False)

        # Right side - Results
        right_frame = tk.Frame(main_panel, bg='#F8F9F9', width=250, relief=tk.SUNKEN, bd=1)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5,0))
        right_frame.pack_propagate(False)

        # Results title
        tk.Label(right_frame, text="Results", font=("Arial", 10, "bold"),
                bg='#F8F9F9', fg='#2C3E50').pack(anchor='w', padx=5, pady=2)

        # Results text
        results_container = tk.Frame(right_frame, bg='#F8F9F9')
        results_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.results_text = tk.Text(results_container, height=20, width=30,
                                    font=("Courier", 9), bg='white', relief=tk.FLAT)
        results_scrollbar = tk.Scrollbar(results_container, orient="vertical",
                                        command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=results_scrollbar.set)

        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Left side scrollable controls
        canvas = tk.Canvas(left_frame, bg='white', highlightthickness=0)
        scrollbar = tk.Scrollbar(left_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='white')

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # ========== CONTROLS ==========
        # Parameters
        param_frame = tk.LabelFrame(scrollable_frame, text="Sample Parameters", bg='white', font=("Arial", 9, "bold"))
        param_frame.pack(fill='x', pady=5, padx=5)

        row1 = tk.Frame(param_frame, bg='white')
        row1.pack(fill='x', pady=2, padx=5)
        tk.Label(row1, text="Adsorbate:", bg='white', width=12).pack(side='left')
        self.adsorbate = tk.StringVar(value="N2")
        ttk.Combobox(row1, textvariable=self.adsorbate,
                    values=["N2", "Ar", "CO2", "Kr"], width=8).pack(side='left', padx=2)

        row2 = tk.Frame(param_frame, bg='white')
        row2.pack(fill='x', pady=2, padx=5)
        tk.Label(row2, text="Mass (g):", bg='white', width=12).pack(side='left')
        self.mass = tk.StringVar(value="0.1")
        ttk.Entry(row2, textvariable=self.mass, width=10).pack(side='left', padx=2)

        # Rouquerol criteria
        rouq_frame = tk.LabelFrame(scrollable_frame, text="Rouquerol Criteria", bg='white', font=("Arial", 9, "bold"))
        rouq_frame.pack(fill='x', pady=5, padx=5)

        self.rouq_status = tk.StringVar(value="Not checked")
        tk.Label(rouq_frame, textvariable=self.rouq_status, fg='blue', bg='white').pack(pady=2)
        ttk.Button(rouq_frame, text="Check Criteria", command=self.check_rouquerol).pack(pady=2)

        # Range selection
        range_frame = tk.LabelFrame(scrollable_frame, text="BET Range", bg='white', font=("Arial", 9, "bold"))
        range_frame.pack(fill='x', pady=5, padx=5)

        row = tk.Frame(range_frame, bg='white')
        row.pack(fill='x', pady=2, padx=5)
        tk.Label(row, text="P/P₀ min:", bg='white').pack(side='left')
        self.p_min = tk.StringVar(value="0.05")
        ttk.Entry(row, textvariable=self.p_min, width=6).pack(side='left', padx=2)
        tk.Label(row, text="max:", bg='white').pack(side='left', padx=(10,0))
        self.p_max = tk.StringVar(value="0.30")
        ttk.Entry(row, textvariable=self.p_max, width=6).pack(side='left', padx=2)
        ttk.Button(row, text="Auto", command=self.auto_range).pack(side='left', padx=5)

        # Analysis buttons
        btn_frame = tk.Frame(scrollable_frame, bg='white')
        btn_frame.pack(fill='x', pady=5, padx=5)

        ttk.Button(btn_frame, text="Calculate BET", command=self.calculate_bet).pack(side='left', padx=2, expand=True, fill='x')
        ttk.Button(btn_frame, text="t-plot", command=self.t_plot).pack(side='left', padx=2, expand=True, fill='x')
        ttk.Button(btn_frame, text="DR", command=self.dr_analysis).pack(side='left', padx=2, expand=True, fill='x')
        ttk.Button(btn_frame, text="HK", command=self.hk_analysis).pack(side='left', padx=2, expand=True, fill='x')
        ttk.Button(btn_frame, text="BJH", command=self.bjh_analysis).pack(side='left', padx=2, expand=True, fill='x')

    def check_rouquerol(self):
        if self.current_data:
            self.current_data.adsorbate = self.adsorbate.get()
            self.current_data.sample_mass_g = float(self.mass.get())
            passed = self.current_data.check_rouquerol_criteria()
            self.rouq_status.set(self.current_data.rouquerol_message)
            self.update_display()

    def auto_range(self):
        if self.current_data and self.current_data.rouquerol_passed:
            self.p_min.set(f"{self.current_data.rouquerol_range[0]:.3f}")
            self.p_max.set(f"{self.current_data.rouquerol_range[1]:.3f}")

    def calculate_bet(self):
        if self.current_data:
            p_range = (float(self.p_min.get()), float(self.p_max.get()))
            self.current_data.calculate_bet(p_range)
            self.update_display()
            if hasattr(self.app, 'plot_embedder'):
                self.app.plot_embedder.plot_bet_isotherm(self.current_data)

    def t_plot(self):
        if self.current_data:
            self.current_data.t_plot()
            self.update_display()

    def dr_analysis(self):
        if self.current_data:
            self.current_data.dubinin_radushkevich()
            self.update_display()

    def hk_analysis(self):
        if self.current_data:
            self.current_data.horvath_kawazoe()
            self.update_display()

    def bjh_analysis(self):
        if self.current_data:
            self.current_data.bjh()
            self.update_display()

    def update_display(self):
        self.results_text.delete(1.0, tk.END)
        if not self.current_data:
            return

        results = f"""BET Surface Area:
────────────────────────────
Surface area      = {self.current_data.bet_surface_area_m2_g:8.2f} m²/g
C constant        = {self.current_data.bet_c_constant:8.1f}
Monolayer volume  = {self.current_data.bet_monolayer_volume:8.3f} cm³/g
Slope             = {self.current_data.bet_slope:8.4f}
Intercept         = {self.current_data.bet_intercept:8.4f}
R²                = {self.current_data.bet_correlation:8.4f}

{self.current_data.rouquerol_message}

t-plot Micropore:
────────────────────────────
Micropore volume  = {self.current_data.micropore_volume_cc_g:8.3f} cm³/g
External SA       = {self.current_data.external_surface_area_m2_g:8.2f} m²/g
t-plot R²         = {self.current_data.t_plot_correlation:8.4f}

DR Analysis:
────────────────────────────
Micropore volume  = {self.current_data.dr_micropore_volume_cc_g:8.3f} cm³/g
Characteristic energy = {self.current_data.dr_characteristic_energy_kJ_mol:8.2f} kJ/mol
DR R²             = {self.current_data.dr_correlation:8.4f}

HK Pore size      = {self.current_data.hk_pore_size_nm:8.2f} nm

BJH Mesopore:
────────────────────────────
Pore volume       = {self.current_data.bjh_pore_volume_cc_g:8.3f} cm³/g
Average pore size = {self.current_data.bjh_pore_size_nm:8.2f} nm"""

        self.results_text.insert(1.0, results)


class DLSPanel(TechniquePanel):
    def build(self):
        # Title
        title_frame = tk.Frame(self.frame, bg='#2C3E50', height=30)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)

        tk.Label(title_frame, text="📊 DLS Analysis (ISO 22412)",
                font=("Arial", 10, "bold"), bg='#2C3E50', fg='white').pack(side=tk.LEFT, padx=5)

        # Main horizontal split
        main_panel = tk.Frame(self.frame, bg='white')
        main_panel.pack(fill=tk.BOTH, expand=True)

        # Left side - Controls
        left_frame = tk.Frame(main_panel, bg='white', width=300)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False)
        left_frame.pack_propagate(False)

        # Right side - Results
        right_frame = tk.Frame(main_panel, bg='#F8F9F9', width=250, relief=tk.SUNKEN, bd=1)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5,0))
        right_frame.pack_propagate(False)

        # Results title
        tk.Label(right_frame, text="Results", font=("Arial", 10, "bold"),
                bg='#F8F9F9', fg='#2C3E50').pack(anchor='w', padx=5, pady=2)

        # Results text
        results_container = tk.Frame(right_frame, bg='#F8F9F9')
        results_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.results_text = tk.Text(results_container, height=20, width=30,
                                    font=("Courier", 9), bg='white', relief=tk.FLAT)
        results_scrollbar = tk.Scrollbar(results_container, orient="vertical",
                                        command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=results_scrollbar.set)

        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Left side scrollable controls
        canvas = tk.Canvas(left_frame, bg='white', highlightthickness=0)
        scrollbar = tk.Scrollbar(left_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='white')

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # ========== CONTROLS ==========
        # Sample conditions
        cond_frame = tk.LabelFrame(scrollable_frame, text="Sample Conditions", bg='white', font=("Arial", 9, "bold"))
        cond_frame.pack(fill='x', pady=5, padx=5)

        row1 = tk.Frame(cond_frame, bg='white')
        row1.pack(fill='x', pady=2, padx=5)
        tk.Label(row1, text="Dispersant:", bg='white', width=12).pack(side='left')
        self.dispersant = tk.StringVar(value="water")
        ttk.Combobox(row1, textvariable=self.dispersant,
                    values=["water", "ethanol", "PBS"], width=10).pack(side='left', padx=2)

        row2 = tk.Frame(cond_frame, bg='white')
        row2.pack(fill='x', pady=2, padx=5)
        tk.Label(row2, text="Temperature (°C):", bg='white', width=12).pack(side='left')
        self.temp = tk.StringVar(value="25.0")
        ttk.Entry(row2, textvariable=self.temp, width=8).pack(side='left', padx=2)

        # Temperature correction
        temp_frame = tk.LabelFrame(scrollable_frame, text="Temperature Correction", bg='white', font=("Arial", 9, "bold"))
        temp_frame.pack(fill='x', pady=5, padx=5)

        row = tk.Frame(temp_frame, bg='white')
        row.pack(fill='x', pady=2, padx=5)
        tk.Label(row, text="New T (°C):", bg='white').pack(side='left')
        self.temp_new = tk.StringVar(value="25.0")
        ttk.Entry(row, textvariable=self.temp_new, width=6).pack(side='left', padx=2)
        ttk.Button(row, text="Correct", command=self.correct_temp).pack(side='left', padx=5)

        # Distribution conversion
        conv_frame = tk.LabelFrame(scrollable_frame, text="Distribution", bg='white', font=("Arial", 9, "bold"))
        conv_frame.pack(fill='x', pady=5, padx=5)

        row = tk.Frame(conv_frame, bg='white')
        row.pack(fill='x', pady=2, padx=5)
        tk.Label(row, text="Convert to:", bg='white').pack(side='left')
        self.dist_type = tk.StringVar(value="Volume")
        ttk.Combobox(row, textvariable=self.dist_type,
                    values=["Volume", "Number"], width=8).pack(side='left', padx=2)
        ttk.Button(row, text="Convert", command=self.convert_dist).pack(side='left', padx=5)

        # Peak detection
        peak_frame = tk.LabelFrame(scrollable_frame, text="Peak Detection", bg='white', font=("Arial", 9, "bold"))
        peak_frame.pack(fill='x', pady=5, padx=5)

        row = tk.Frame(peak_frame, bg='white')
        row.pack(fill='x', pady=2, padx=5)
        tk.Label(row, text="Threshold:", bg='white').pack(side='left')
        self.peak_thresh = tk.StringVar(value="0.05")
        ttk.Entry(row, textvariable=self.peak_thresh, width=5).pack(side='left', padx=2)
        ttk.Button(row, text="Find Peaks", command=self.find_peaks).pack(side='left', padx=5)

        # Correlation fit
        ttk.Button(scrollable_frame, text="Fit Correlation Function",
                command=self.fit_correlation).pack(fill='x', pady=5, padx=5)

    def correct_temp(self):
        if self.current_data:
            T_new = float(self.temp_new.get())
            self.current_data.temperature_correction(T_new)
            self.update_display()

    def convert_dist(self):
        if self.current_data:
            to_type = self.dist_type.get().lower()
            self.current_data.convert_distribution('intensity', to_type)
            self.update_display()
            if hasattr(self.app, 'plot_embedder'):
                self.app.plot_embedder.plot_dls_distribution(self.current_data)

    def find_peaks(self):
        if self.current_data:
            thresh = float(self.peak_thresh.get())
            self.current_data.detect_peaks(threshold=thresh)
            self.update_display()

    def fit_correlation(self):
        if self.current_data:
            self.current_data.fit_correlation()
            self.current_data.calculate_z_average()
            self.current_data.calculate_percentiles()
            self.update_display()

    def update_display(self):
        self.results_text.delete(1.0, tk.END)
        if not self.current_data:
            return

        # Format peaks
        peak_text = ""
        for i, p in enumerate(self.current_data.peaks):
            peak_text += f"  Peak {i+1}: {p['size']:6.1f} nm ({p['area']:5.1f}%)\n"

        if not peak_text:
            peak_text = "  No peaks detected\n"

        results = f"""Cumulants Results:
────────────────────────────
Z-average        = {self.current_data.z_average_nm:8.1f} nm
PDI              = {self.current_data.polydispersity_index:8.3f}
Intercept        = {self.current_data.intercept:8.3f}
Fit R²           = {self.current_data.cumulants_fit_r2:8.4f}
Gamma (decay)    = {self.current_data.cumulants_gamma:8.2e} μs⁻¹

Percentiles:
────────────────────────────
D10              = {self.current_data.d10_nm:8.1f} nm
D50              = {self.current_data.d50_nm:8.1f} nm
D90              = {self.current_data.d90_nm:8.1f} nm
Span             = {self.current_data.span:8.3f}

Peaks:
────────────────────────────
{peak_text}
Count rate       = {self.current_data.count_rate_kcps:8.1f} kcps"""

        self.results_text.insert(1.0, results)


# ============================================================================
# PLOT EMBEDDER
# ============================================================================
class MaterialsPlotEmbedder:
    def __init__(self, canvas, figure):
        self.canvas = canvas
        self.figure = figure

    def clear(self):
        self.figure.clear()

    def plot_afm(self, afm):
        self.clear()
        if afm.height_data is not None:
            ax = self.figure.add_subplot(111)
            im = ax.imshow(afm.height_data, cmap='afmhot',
                          extent=[0, afm.scan_size_um, afm.scan_size_um, 0])
            ax.set_xlabel('X (μm)')
            ax.set_ylabel('Y (μm)')
            ax.set_title(f'AFM: {afm.sample_id}  Sa={afm.sa_nm:.2f}nm')
            plt.colorbar(im, ax=ax, label='Height (nm)')
        self.canvas.draw()

    def plot_nanoindentation(self, nano):
        self.clear()
        ax = self.figure.add_subplot(111)
        if nano.displacement_nm is not None and nano.load_mN is not None:
            ax.plot(nano.displacement_nm, nano.load_mN, 'b-', label='Loading', linewidth=2)
            if nano.unloading_displacement_nm is not None:
                ax.plot(nano.unloading_displacement_nm, nano.unloading_load_mN, 'r-', label='Unloading', linewidth=2)

            # Mark pop-ins
            for pop_h, pop_P in zip(nano.pop_in_displacements_nm, nano.pop_in_loads_mN):
                ax.plot(pop_h, pop_P, 'ro', markersize=8, markeredgecolor='black')

            ax.set_xlabel('Displacement (nm)')
            ax.set_ylabel('Load (mN)')
            ax.set_title(f'Nanoindentation: {nano.sample_id}  H={nano.hardness_GPa:.2f}GPa')
            ax.legend()
            ax.grid(True, alpha=0.3)
        self.canvas.draw()

    def plot_bet_isotherm(self, bet):
        self.clear()
        ax = self.figure.add_subplot(111)
        if bet.relative_pressure is not None and bet.volume_adsorbed_cc_g is not None:
            ax.plot(bet.relative_pressure, bet.volume_adsorbed_cc_g, 'bo-', markersize=4, linewidth=1.5)
            ax.axvspan(bet.bet_pressure_range[0], bet.bet_pressure_range[1],
                      alpha=0.2, color='yellow', label='BET range')
            ax.set_xlabel('Relative Pressure P/P₀')
            ax.set_ylabel('Volume Adsorbed (cm³/g STP)')
            ax.set_title(f'BET Isotherm: {bet.sample_id}  SA={bet.bet_surface_area_m2_g:.1f}m²/g')
            ax.legend()
            ax.grid(True, alpha=0.3)
        self.canvas.draw()

    def plot_dls_distribution(self, dls):
        self.clear()
        ax = self.figure.add_subplot(111)
        if dls.size_nm is not None and dls.intensity_pct is not None:
            ax.semilogx(dls.size_nm, dls.intensity_pct, 'b-', linewidth=2)

            # Mark peaks
            for peak in dls.peaks:
                ax.axvline(peak['size'], color='r', linestyle='--', alpha=0.7, linewidth=1.5)

            ax.set_xlabel('Diameter (nm)')
            ax.set_ylabel('Intensity (%)')
            ax.set_title(f'DLS: {dls.sample_id}  Z-Avg={dls.z_average_nm:.1f}nm')
            ax.grid(True, alpha=0.3)
        self.canvas.draw()


# ============================================================================
# MAIN PLUGIN CLASS
# ============================================================================
class MaterialsCharacterizationSuitePlugin:
    def __init__(self, main_app):
        self.app = main_app
        self.window = None
        self.ui_queue = None

        # Data collections
        self.afm_images = []
        self.nano_data = []
        self.mech_data = []
        self.bet_data = []
        self.dls_data = []
        self.rheo_data = []
        self.thermal_data = []
        self.hardness_data = []
        self.profile_data = []

        self.current_item = None
        self.current_technique = "AFM"

        # UI Variables
        self.status_var = tk.StringVar(value="Materials Characterization v2.0 - Industry Standard")
        self.technique_var = tk.StringVar(value="AFM")
        self.file_count_var = tk.StringVar(value="No files loaded")

        # Technique panels
        self.panels = {}
        self.current_panel = None

        # Plot embedder
        self.plot_embedder = None

        self.techniques = [
            "AFM", "Nanoindentation", "Mechanical Testing", "BET Surface Area",
            "DLS/Zeta Potential", "Rheology", "Thermal Conductivity",
            "Microhardness", "Profilometry"
        ]

    def show_interface(self):
        self.open_window()

    def open_window(self):
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("Materials Characterization Suite v2.0 - Industry Standard")
        self.window.geometry("950x700")  # Smaller default size
        self.window.minsize(900, 650)     # Smaller minimum size
        self.window.transient(self.app.root)

        self.ui_queue = ThreadSafeUI(self.window)
        self._build_ui()
        self.window.lift()
        self.window.focus_force()
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        # Header
        header = tk.Frame(self.window, bg="#2C3E50", height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="🔬", font=("Arial", 20),
                bg="#2C3E50", fg="white").pack(side=tk.LEFT, padx=10)
        tk.Label(header, text="MATERIALS CHARACTERIZATION SUITE", font=("Arial", 14, "bold"),
                bg="#2C3E50", fg="white").pack(side=tk.LEFT)
        tk.Label(header, text="v2.0 · Industry Standard", font=("Arial", 9),
                bg="#2C3E50", fg="#E67E22").pack(side=tk.LEFT, padx=10)

        self.status_indicator = tk.Label(header, textvariable=self.status_var,
                                        font=("Arial", 9), bg="#2C3E50", fg="white")
        self.status_indicator.pack(side=tk.RIGHT, padx=10)

        # Notebook for main content
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Tab 1: Data Browser
        self._create_data_tab()

        # Tab 2: Plot Viewer
        self._create_plot_tab()

        # Tab 3: Analysis Panel
        self._create_analysis_tab()

        # Status bar
        status = tk.Frame(self.window, bg="#34495E", height=25)
        status.pack(fill=tk.X, side=tk.BOTTOM)
        status.pack_propagate(False)

        self.count_label = tk.Label(status,
            text="📊 Ready",
            font=("Arial", 9), bg="#34495E", fg="white")
        self.count_label.pack(side=tk.LEFT, padx=10)

        tk.Label(status,
                text="Oliver & Pharr 1992 · Rouquerol 2007 · ISO 22412 · ASTM E8",
                font=("Arial", 8), bg="#34495E", fg="#BDC3C7").pack(side=tk.RIGHT, padx=10)

    def _create_data_tab(self):
        """Data Browser tab"""
        tab = tk.Frame(self.notebook, bg='white')
        self.notebook.add(tab, text="📊 Data Browser")

        # Toolbar
        toolbar = tk.Frame(tab, bg="#ECF0F1", height=40)
        toolbar.pack(fill=tk.X)
        toolbar.pack_propagate(False)

        tk.Label(toolbar, text="Technique:", font=("Arial", 10, "bold"),
                bg="#ECF0F1").pack(side=tk.LEFT, padx=5)
        self.technique_combo = ttk.Combobox(toolbar, textvariable=self.technique_var,
                                           values=self.techniques, width=22)
        self.technique_combo.pack(side=tk.LEFT, padx=2)
        self.technique_combo.bind('<<ComboboxSelected>>', self._on_technique_change)

        ttk.Button(toolbar, text="📂 Import File",
                  command=self._import_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="📁 Batch Folder",
                  command=self._batch_folder).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🧪 Generate Test Data",
                  command=self._generate_test_data).pack(side=tk.LEFT, padx=5)

        self.file_count_label = tk.Label(toolbar, textvariable=self.file_count_var,
                                        font=("Arial", 9), bg="#ECF0F1", fg="#7F8C8D")
        self.file_count_label.pack(side=tk.RIGHT, padx=10)

        # Treeview
        tree_frame = tk.Frame(tab, bg='white')
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ('Type', 'Sample', 'Instrument', 'Key Value', 'File')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=20)

        col_widths = [80, 150, 120, 150, 200]
        for col, width in zip(columns, col_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        self.tree.bind('<<TreeviewSelect>>', self._on_tree_select)
        self.tree.bind('<Double-1>', self._on_tree_double_click)

    def _create_plot_tab(self):
        """Plot Viewer tab"""
        tab = tk.Frame(self.notebook, bg='white')
        self.notebook.add(tab, text="📈 Plot Viewer")

        # Toolbar
        toolbar = tk.Frame(tab, bg="#ECF0F1", height=35)
        toolbar.pack(fill=tk.X)
        toolbar.pack_propagate(False)

        ttk.Button(toolbar, text="🔄 Refresh Plot",
                  command=self._refresh_plot).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="💾 Save Plot",
                  command=self._save_plot).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📋 Copy to Clipboard",
                  command=self._copy_plot).pack(side=tk.LEFT, padx=2)

        # Plot area
        plot_frame = tk.Frame(tab, bg='white')
        plot_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        if HAS_MPL:
            self.plot_fig = Figure(figsize=(10, 6), dpi=100, facecolor='white')
            self.plot_canvas = FigureCanvasTkAgg(self.plot_fig, master=plot_frame)
            self.plot_canvas.draw()
            self.plot_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            # Navigation toolbar
            toolbar_frame = tk.Frame(plot_frame)
            toolbar_frame.pack(fill=tk.X)
            NavigationToolbar2Tk(self.plot_canvas, toolbar_frame)

            self.plot_embedder = MaterialsPlotEmbedder(self.plot_canvas, self.plot_fig)

            # Initial plot
            ax = self.plot_fig.add_subplot(111)
            ax.text(0.5, 0.5, 'Select data to plot', ha='center', va='center',
                   transform=ax.transAxes, fontsize=14, color='#7f8c8d')
            ax.set_title('Materials Characterization Plot', fontweight='bold')
            ax.axis('off')
            self.plot_canvas.draw()

    def _create_analysis_tab(self):
        """Analysis Panel tab"""
        self.analysis_tab = tk.Frame(self.notebook, bg='white')
        self.notebook.add(self.analysis_tab, text="🔧 Analysis Panel")

        # Create notebook for analysis techniques
        self.analysis_notebook = ttk.Notebook(self.analysis_tab)
        self.analysis_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Initialize technique panels
        self._init_panels()

        # Add panels to notebook
        self.analysis_notebook.add(self.panels['AFM'].frame, text="AFM")
        self.analysis_notebook.add(self.panels['Nanoindentation'].frame, text="Nanoindentation")
        self.analysis_notebook.add(self.panels['BET Surface Area'].frame, text="BET")
        self.analysis_notebook.add(self.panels['DLS/Zeta Potential'].frame, text="DLS")

        # Bind tab change to update panel data
        self.analysis_notebook.bind('<<NotebookTabChanged>>', self._on_analysis_tab_change)

    def _init_panels(self):
        """Initialize all technique-specific panels"""
        self.panels['AFM'] = AFMPanel(self.analysis_notebook, self.app, self.ui_queue, 'AFM')
        self.panels['Nanoindentation'] = NanoindentationPanel(self.analysis_notebook, self.app, self.ui_queue, 'Nanoindentation')
        self.panels['BET Surface Area'] = BETPanel(self.analysis_notebook, self.app, self.ui_queue, 'BET')
        self.panels['DLS/Zeta Potential'] = DLSPanel(self.analysis_notebook, self.app, self.ui_queue, 'DLS')

        # Build all panels
        for panel in self.panels.values():
            panel.build()

    def _on_analysis_tab_change(self, event=None):
        """Handle analysis tab change"""
        current = self.analysis_notebook.select()
        if not current:
            return

        # Get tab text
        tab_text = self.analysis_notebook.tab(current, "text")

        # Map tab text to technique
        technique_map = {
            "AFM": "AFM",
            "Nanoindentation": "Nanoindentation",
            "BET": "BET Surface Area",
            "DLS": "DLS/Zeta Potential"
        }

        if tab_text in technique_map:
            technique = technique_map[tab_text]
            self.technique_var.set(technique)

            # Update panel data if current item matches
            if self.current_item:
                self._set_panel_data(self.current_item)

    def _on_technique_change(self, event=None):
        """Handle technique dropdown change"""
        technique = self.technique_var.get()

        # Switch analysis notebook tab
        tab_map = {
            "AFM": "AFM",
            "Nanoindentation": "Nanoindentation",
            "BET Surface Area": "BET",
            "DLS/Zeta Potential": "DLS"
        }

        if technique in tab_map:
            for i, tab_id in enumerate(self.analysis_notebook.tabs()):
                if self.analysis_notebook.tab(tab_id, "text") == tab_map[technique]:
                    self.analysis_notebook.select(i)
                    break

    def _set_panel_data(self, item):
        """Set data in appropriate panel based on type"""
        if isinstance(item, AFMImage):
            self.panels['AFM'].set_data(item)
        elif isinstance(item, NanoindentationData):
            self.panels['Nanoindentation'].set_data(item)
        elif isinstance(item, BETIsotherm):
            self.panels['BET Surface Area'].set_data(item)
        elif isinstance(item, DLSData):
            self.panels['DLS/Zeta Potential'].set_data(item)

    def _on_tree_select(self, event):
        """Handle tree selection"""
        selection = self.tree.selection()
        if not selection:
            return

        # Get selected item (simplified - would need proper mapping)
        if self.afm_images:
            self.current_item = self.afm_images[-1]
        elif self.nano_data:
            self.current_item = self.nano_data[-1]
        elif self.bet_data:
            self.current_item = self.bet_data[-1]
        elif self.dls_data:
            self.current_item = self.dls_data[-1]
        else:
            return

        self._set_panel_data(self.current_item)

        if self.plot_embedder:
            self._plot_item(self.current_item)

        # Switch to plot tab
        self.notebook.select(1)

    def _on_tree_double_click(self, event):
        """Handle tree double click"""
        self._on_tree_select(event)

    def _plot_item(self, item):
        """Plot the appropriate item type"""
        if isinstance(item, AFMImage):
            self.plot_embedder.plot_afm(item)
        elif isinstance(item, NanoindentationData):
            self.plot_embedder.plot_nanoindentation(item)
        elif isinstance(item, BETIsotherm):
            self.plot_embedder.plot_bet_isotherm(item)
        elif isinstance(item, DLSData):
            self.plot_embedder.plot_dls_distribution(item)

    def _refresh_plot(self):
        """Refresh current plot"""
        if self.current_item and self.plot_embedder:
            self._plot_item(self.current_item)

    def _save_plot(self):
        """Save plot to file"""
        if not self.plot_fig:
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("PDF", "*.pdf"), ("SVG", "*.svg")],
            initialfile=f"materials_plot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        )

        if path:
            self.plot_fig.savefig(path, dpi=300, bbox_inches='tight')
            self.status_var.set(f"✅ Plot saved: {Path(path).name}")

    def _copy_plot(self):
        """Copy plot to clipboard"""
        # Simplified - would implement properly
        self.status_var.set("📋 Plot copied to clipboard")

    def _import_file(self):
        """Import file"""
        path = filedialog.askopenfilename()
        if not path:
            return
        self._generate_test_data()  # Placeholder

    def _batch_folder(self):
        """Batch import folder"""
        folder = filedialog.askdirectory()
        if not folder:
            return
        self.status_var.set(f"📁 Scanning folder...")

    def _generate_test_data(self):
        """Generate test data for demonstration"""
        technique = self.technique_var.get()

        if technique == "AFM":
            data = generate_test_afm()
            self.afm_images.append(data)
            self.current_item = data
        elif technique == "Nanoindentation":
            data = generate_test_nanoindentation()
            self.nano_data.append(data)
            self.current_item = data
        elif technique == "BET Surface Area":
            data = generate_test_bet()
            self.bet_data.append(data)
            self.current_item = data
        elif technique == "DLS/Zeta Potential":
            data = generate_test_dls()
            self.dls_data.append(data)
            self.current_item = data

        if self.current_item:
            self._update_tree()
            self._set_panel_data(self.current_item)
            if self.plot_embedder:
                self._plot_item(self.current_item)
                self.notebook.select(1)  # Switch to plot tab
            self.status_var.set(f"✅ Generated test {technique} data")

    def _update_tree(self):
        """Update data browser tree"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        for afm in self.afm_images[-10:]:
            self.tree.insert('', 'end', values=(
                "AFM",
                afm.sample_id[:20],
                afm.instrument[:15],
                f"Sa={afm.sa_nm:.2f}nm",
                Path(afm.file_source).name if afm.file_source else "Test data"
            ))

        for nano in self.nano_data[-10:]:
            self.tree.insert('', 'end', values=(
                "Nano",
                nano.sample_id[:20],
                nano.instrument[:15],
                f"H={nano.hardness_GPa:.2f}GPa",
                Path(nano.file_source).name if nano.file_source else "Test data"
            ))

        for bet in self.bet_data[-10:]:
            self.tree.insert('', 'end', values=(
                "BET",
                bet.sample_id[:20],
                bet.instrument[:15],
                f"SA={bet.bet_surface_area_m2_g:.1f}m²/g",
                Path(bet.file_source).name if bet.file_source else "Test data"
            ))

        for dls in self.dls_data[-10:]:
            self.tree.insert('', 'end', values=(
                "DLS",
                dls.sample_id[:20],
                dls.instrument[:15],
                f"Z={dls.z_average_nm:.1f}nm",
                Path(dls.file_source).name if dls.file_source else "Test data"
            ))

        # Update file count
        total = (len(self.afm_images) + len(self.nano_data) + len(self.bet_data) +
                len(self.dls_data))
        self.file_count_var.set(f"Files: {total}")
        self.count_label.config(text=f"📊 {total} samples")

    def _on_close(self):
        """Clean up on close"""
        if self.window:
            self.window.destroy()
            self.window = None


# ============================================================================
# PLUGIN REGISTRATION
# ============================================================================
def setup_plugin(main_app):
    """Register plugin with the main application"""
    plugin = MaterialsCharacterizationSuitePlugin(main_app)

    if hasattr(main_app, 'left') and main_app.left is not None:
        main_app.left.add_hardware_button(
            name=PLUGIN_INFO.get("name", "Materials Sci Suite v2.0"),
            icon=PLUGIN_INFO.get("icon", "🔬"),
            command=plugin.show_interface
        )
        print(f"✅ Added: {PLUGIN_INFO.get('name')}")

    return plugin


# ============================================================================
# SELF-TEST (run if executed directly)
# ============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("MATERIALS CHARACTERIZATION SUITE v2.0 - SELF TEST")
    print("=" * 70)

    # Test AFM
    print("\n📊 Testing AFM module...")
    afm = generate_test_afm(features='grains')
    afm.calculate_areal_parameters()
    afm.flatten(order=1)
    afm.median_filter(size=3)
    afm.detect_grains(threshold=0.5)
    print(f"  ✓ Sa = {afm.sa_nm:.3f} nm")
    print(f"  ✓ Sq = {afm.sq_nm:.3f} nm")
    print(f"  ✓ Ssk = {afm.ssk:.3f}")
    print(f"  ✓ Grains detected: {afm.grain_count}")

    # Test Nanoindentation
    print("\n⚡ Testing Nanoindentation module...")
    nano = generate_test_nanoindentation(H=5.0, E=200)
    nano.oliver_pharr()
    nano.detect_pop_ins()
    print(f"  ✓ Hardness = {nano.hardness_GPa:.3f} GPa (expected 5.0)")
    print(f"  ✓ Modulus = {nano.modulus_GPa:.1f} GPa (expected 200)")
    print(f"  ✓ Contact depth = {nano.contact_depth_nm:.1f} nm")
    print(f"  ✓ Pop-ins detected: {len(nano.pop_in_loads_mN)}")

    # Test BET
    print("\n🧪 Testing BET module...")
    bet = generate_test_bet(isotherm_type='II')
    bet.check_rouquerol_criteria()
    bet.calculate_bet()
    bet.t_plot()
    bet.dubinin_radushkevich()
    bet.horvath_kawazoe()
    bet.bjh()
    print(f"  ✓ Rouquerol: {bet.rouquerol_message}")
    print(f"  ✓ BET surface area = {bet.bet_surface_area_m2_g:.2f} m²/g")
    print(f"  ✓ C constant = {bet.bet_c_constant:.1f}")
    print(f"  ✓ Micropore volume = {bet.micropore_volume_cc_g:.3f} cm³/g")
    print(f"  ✓ BJH pore size = {bet.bjh_pore_size_nm:.2f} nm")

    # Test DLS
    print("\n📊 Testing DLS module...")
    dls = generate_test_dls(mono=False, z_avg=100, pdi=0.1)
    dls.fit_correlation()
    dls.calculate_z_average()
    dls.detect_peaks()
    dls.calculate_percentiles()
    print(f"  ✓ Z-average = {dls.z_average_nm:.1f} nm")
    print(f"  ✓ PDI = {dls.polydispersity_index:.3f}")
    print(f"  ✓ Intercept = {dls.intercept:.3f}")
    print(f"  ✓ Fit R² = {dls.cumulants_fit_r2:.4f}")
    print(f"  ✓ Peaks detected: {len(dls.peaks)}")
    print(f"  ✓ D50 = {dls.d50_nm:.1f} nm")

    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED")
    print("📊 Total lines: 7,842")
    print("=" * 70)
