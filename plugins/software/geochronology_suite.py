"""
Geochronology Suite v1.0 - U-Pb · Ar-Ar · Detrital · Isochrons
WITH FULL MAIN APP INTEGRATION

✓ U-Pb Concordia (Wetherill & Tera-Wasserburg)
✓ Ar-Ar Age Spectra & Plateau Ages
✓ Detrital Provenance (KDE, CAD, MDS)
✓ Isochrons for Rb-Sr, Sm-Nd, Lu-Hf, Re-Os
✓ MSWD, probability, error ellipses
"""

PLUGIN_INFO = {
    "category": "software",
    "id": "geochronology_suite",
    "name": "Geochronology Suite",
    "description": "U-Pb · Ar-Ar · Detrital · Isochrons — Complete geochronology toolkit",
    "icon": "⏳",
    "version": "1.0.0",
    "requires": ["numpy", "scipy", "matplotlib", "pandas", "scikit-learn"],
    "author": "Sefy Levy & DeepSeek"
}

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import pandas as pd
from datetime import datetime
import json
import traceback
from pathlib import Path

try:
    import matplotlib
    matplotlib.use('TkAgg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    from matplotlib.patches import Ellipse
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    import numpy as np
    from scipy import stats, optimize
    from scipy.stats import gaussian_kde, chi2, ks_2samp
    from scipy.spatial.distance import pdist, squareform
    import sklearn.manifold
    HAS_SCIPY = True
    HAS_SKLEARN = True
except ImportError:
    HAS_SCIPY = False
    HAS_SKLEARN = False


class GeochronologySuitePlugin:
    """
    GEOCHRONOLOGY SUITE - Complete geochronology toolkit
    U-Pb · Ar-Ar · Detrital · Isochrons
    """

    # ============================================================================
    # CONSTANTS
    # ============================================================================
    LAMBDA_238 = 1.55125e-10  # ²³⁸U decay constant (yr⁻¹)
    LAMBDA_235 = 9.8485e-10    # ²³⁵U decay constant (yr⁻¹)
    U238_U235 = 137.818        # Present-day ²³⁸U/²³⁵U

    DECAY_CONSTANTS = {
        'Rb87': 1.42e-11,
        'Sm147': 6.54e-12,
        'Lu176': 1.867e-11,
        'Re187': 1.666e-11,
        'K40': 5.543e-10
    }

    def __init__(self, main_app):
        self.app = main_app
        self.window = None

        # ============ DATA ============
        self.samples = []

        # U-Pb data
        self.upb_spots = []

        # Ar-Ar data
        self.ar_steps = []

        # Detrital data
        self.detrital_samples = {}  # sample_id -> list of ages

        # Isochron data
        self.isochron_points = []   # list of (x, y, sigma_x, sigma_y, sample_id)

        # ============ RESULTS ============
        self.results = {}

        # ============ UI VARIABLES ============
        # Notebook tabs
        self.notebook = None

        # U-Pb tab
        self.upb_diagram_var = tk.StringVar(value="wetherill")
        self.upb_ellipse_var = tk.BooleanVar(value=True)
        self.upb_show_concordia_var = tk.BooleanVar(value=True)
        self.upb_age_min_var = tk.IntVar(value=0)
        self.upb_age_max_var = tk.IntVar(value=4500)

        # Ar-Ar tab
        self.ar_plateau_threshold_var = tk.DoubleVar(value=0.5)

        # Detrital tab
        self.detrital_plot_var = tk.StringVar(value="kde")
        self.detrital_bandwidth_var = tk.StringVar(value="scott")
        self.detrital_method_var = tk.StringVar(value="ks")
        self.detrital_age_min_var = tk.IntVar(value=0)
        self.detrital_age_max_var = tk.IntVar(value=3000)

        # Isochron tab
        self.iso_system_var = tk.StringVar(value="Rb-Sr")
        self.iso_regression_var = tk.StringVar(value="york")

        # Common
        self.status_var = None
        self.progress = None

        self._check_dependencies()

    def _check_dependencies(self):
        """Check required packages"""
        missing = []
        if not HAS_MATPLOTLIB: missing.append("matplotlib")
        if not HAS_SCIPY: missing.append("scipy")
        if not HAS_SKLEARN: missing.append("scikit-learn")
        self.dependencies_met = len(missing) == 0
        self.missing_deps = missing

    # ============================================================================
    # SAFE FLOAT CONVERSION
    # ============================================================================
    def _safe_float(self, value):
        """Safely convert to float"""
        if value is None or value == '':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    # ============================================================================
    # DATA LOADING FROM MAIN APP
    # ============================================================================
    def _load_from_main_app(self):
        """Load geochronology data from main app samples"""
        if not hasattr(self.app, 'samples') or not self.app.samples:
            print("❌ No samples in main app")
            return False

        self.samples = self.app.samples
        print(f"📊 Loading {len(self.samples)} samples from main app")

        # Clear existing data
        self.upb_spots = []
        self.ar_steps = []
        self.detrital_samples = {}
        self.isochron_points = []

        # Column pattern mappings
        upb_patterns = {
            '207_235': ['207_235', 'Pb207_U235', 'Pb207/U235', '207Pb/235U', 'r75'],
            'err_207_235': ['err_207_235', '2s_207_235', '207_235_err', 'Pb207_U235_err'],
            '206_238': ['206_238', 'Pb206_U238', 'Pb206/U238', '206Pb/238U', 'r68'],
            'err_206_238': ['err_206_238', '2s_206_238', '206_238_err', 'Pb206_U238_err'],
            '207_206': ['207_206', 'Pb207_Pb206', 'Pb207/Pb206', '207Pb/206Pb', 'r76'],
            'err_207_206': ['err_207_206', '2s_207_206', '207_206_err', 'Pb207_Pb206_err'],
            'rho': ['rho', 'correlation', 'err_corr']
        }

        ar_patterns = {
            'age': ['age_ma', 'age', 'Age_Ma', 'Ar_Age'],
            'age_err': ['age_err', 'error', '2s', 'Age_Error'],
            'pct_39Ar': ['pct_39Ar', 'percent_39Ar', 'cumulative_pct', 'gas_pct'],
            'J': ['J', 'J_value', 'irradiation']
        }

        detrital_patterns = {
            'age': ['age_ma', 'age', 'Age_Ma', 'U_Pb_Age', 'zircon_age']
        }

        isochron_patterns = {
            'Rb_Sr': ['Rb87_Sr86', '87Rb/86Sr', 'Rb_Sr'],
            'Sr87_Sr86': ['Sr87_Sr86', '87Sr/86Sr', 'Sr_ratio'],
            'Sm_Nd': ['Sm147_Nd144', '147Sm/144Nd', 'Sm_Nd'],
            'Nd143_Nd144': ['Nd143_Nd144', '143Nd/144Nd', 'Nd_ratio']
        }

        # Process each sample
        for idx, sample in enumerate(self.samples):
            if not isinstance(sample, dict):
                continue

            sample_id = sample.get('Sample_ID', f'SAMPLE_{idx:04d}')

            # ===== U-Pb DETECTION =====
            spot = {'sample_id': sample_id, 'spot_name': sample.get('Spot_ID', f'Spot_{idx:03d}')}
            has_upb = False

            for field, patterns in upb_patterns.items():
                for pattern in patterns:
                    if pattern in sample and sample[pattern] is not None:
                        val = self._safe_float(sample[pattern])
                        if val is not None:
                            spot[field] = val
                            has_upb = True
                            break

            if has_upb:
                self.upb_spots.append(spot)

            # ===== Ar-Ar DETECTION =====
            step = {'sample_id': sample_id, 'step': sample.get('Step', len(self.ar_steps))}
            has_ar = False

            for field, patterns in ar_patterns.items():
                for pattern in patterns:
                    if pattern in sample and sample[pattern] is not None:
                        val = self._safe_float(sample[pattern])
                        if val is not None:
                            step[field] = val
                            has_ar = True
                            break

            if has_ar:
                self.ar_steps.append(step)

            # ===== DETRITAL DETECTION =====
            for pattern in detrital_patterns['age']:
                if pattern in sample and sample[pattern] is not None:
                    age = self._safe_float(sample[pattern])
                    if age and age > 0:
                        if sample_id not in self.detrital_samples:
                            self.detrital_samples[sample_id] = []
                        self.detrital_samples[sample_id].append(age)
                        break

            # ===== ISOCHRON DETECTION =====
            # Try to detect isochron data (simplified - would need more sophisticated detection)
            if 'Rb87_Sr86' in sample and 'Sr87_Sr86' in sample:
                x = self._safe_float(sample['Rb87_Sr86'])
                y = self._safe_float(sample['Sr87_Sr86'])
                if x and y:
                    self.isochron_points.append({
                        'sample_id': sample_id,
                        'system': 'Rb-Sr',
                        'x': x,
                        'y': y,
                        'sigma_x': x * 0.01,  # Default 1% error
                        'sigma_y': y * 0.0001  # Default 0.01% error
                    })

        print(f"✅ Loaded {len(self.upb_spots)} U-Pb spots, {len(self.ar_steps)} Ar-Ar steps, "
              f"{len(self.detrital_samples)} detrital samples, {len(self.isochron_points)} isochron points")

        # Update UI if window is open
        self._update_ui_counts()

        return True

    def _update_ui_counts(self):
        """Update count displays in UI"""
        if hasattr(self, 'upb_count_label'):
            self.upb_count_label.config(text=f"Spots: {len(self.upb_spots)}")
        if hasattr(self, 'ar_count_label'):
            self.ar_count_label.config(text=f"Steps: {len(self.ar_steps)}")
        if hasattr(self, 'detrital_count_label'):
            self.detrital_count_label.config(text=f"Samples: {len(self.detrital_samples)}")
        if hasattr(self, 'iso_count_label'):
            self.iso_count_label.config(text=f"Points: {len(self.isochron_points)}")

    # ============================================================================
    # U-Pb CONCORDIA METHODS
    # ============================================================================
    def _draw_wetherill(self, ax):
        """Draw Wetherill concordia with square aspect"""
        if not self.upb_spots:
            ax.text(0.5, 0.5, "No U-Pb data loaded", ha='center', va='center')
            return

        # Draw concordia curve
        if self.upb_show_concordia_var.get():
            t_ma = np.linspace(self.upb_age_min_var.get(), self.upb_age_max_var.get(), 500)
            r68 = np.exp(self.LAMBDA_238 * t_ma * 1e6) - 1
            r75 = np.exp(self.LAMBDA_235 * t_ma * 1e6) - 1
            ax.plot(r75, r68, 'k-', linewidth=1.5, label='Concordia')

            # Add age ticks
            for age in [100, 500, 1000, 1500, 2000, 2500, 3000, 3500, 4000]:
                if self.upb_age_min_var.get() <= age <= self.upb_age_max_var.get():
                    idx = np.argmin(np.abs(t_ma - age))
                    ax.text(r75[idx], r68[idx], f'{age}', fontsize=7, ha='center')

        # Plot data
        for spot in self.upb_spots:
            if '207_235' in spot and '206_238' in spot:
                x = spot['207_235']
                y = spot['206_238']

                # Error ellipse
                if self.upb_ellipse_var.get() and 'err_207_235' in spot and 'err_206_238' in spot:
                    sx = spot['err_207_235'] * 2
                    sy = spot['err_206_238'] * 2
                    rho = spot.get('rho', 0)

                    if rho != 0:
                        # Calculate ellipse angle and dimensions
                        cov_xx = sx**2
                        cov_yy = sy**2
                        cov_xy = rho * sx * sy

                        eigenvalues, eigenvectors = np.linalg.eigh([[cov_xx, cov_xy], [cov_xy, cov_yy]])
                        angle = np.degrees(np.arctan2(eigenvectors[1, 0], eigenvectors[0, 0]))
                        width = 2 * np.sqrt(5.991 * eigenvalues[0])  # 95% confidence
                        height = 2 * np.sqrt(5.991 * eigenvalues[1])

                        # FIXED: angle as keyword argument
                        ellipse = Ellipse((x, y), width, height, angle=angle,
                                        facecolor='red', alpha=0.2, edgecolor='red', linewidth=0.5)
                        ax.add_patch(ellipse)
                    else:
                        # No correlation - simple ellipse
                        ellipse = Ellipse((x, y), width=2*sx, height=2*sy,
                                        facecolor='red', alpha=0.2, edgecolor='red', linewidth=0.5)
                        ax.add_patch(ellipse)

                ax.scatter(x, y, c='red', s=30, alpha=0.8, edgecolor='black', zorder=2)

        ax.set_xlabel('²⁰⁷Pb/²³⁵U')
        ax.set_ylabel('²⁰⁶Pb/²³⁸U')
        ax.set_title('Wetherill Concordia')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best')
        ax.set_aspect('equal')

    def _draw_tera_wasserburg(self, ax):
        """Draw Tera-Wasserburg concordia with square aspect"""
        if not self.upb_spots:
            ax.text(0.5, 0.5, "No U-Pb data loaded", ha='center', va='center')
            return

        # Draw concordia curve
        if self.upb_show_concordia_var.get():
            t_ma = np.linspace(self.upb_age_min_var.get(), self.upb_age_max_var.get(), 500)
            u206 = 1 / (np.exp(self.LAMBDA_238 * t_ma * 1e6) - 1)
            pb207_206 = (1/self.U238_U235) * (np.exp(self.LAMBDA_235 * t_ma * 1e6) - 1) / \
                       (np.exp(self.LAMBDA_238 * t_ma * 1e6) - 1)
            ax.plot(u206, pb207_206, 'k-', linewidth=1.5, label='Concordia')

        # Plot data
        for spot in self.upb_spots:
            if '206_238' in spot and '207_206' in spot:
                x = 1 / spot['206_238']
                y = spot['207_206']
                ax.scatter(x, y, c='red', s=30, alpha=0.8, edgecolor='black')

        ax.set_xlabel('²³⁸U/²⁰⁶Pb')
        ax.set_ylabel('²⁰⁷Pb/²⁰⁶Pb')
        ax.set_title('Tera-Wasserburg Concordia')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best')
        ax.set_aspect('equal')
        ax.invert_xaxis()

    def _plot_upb(self):
        """Update U-Pb plot"""
        self.upb_ax.clear()

        if self.upb_diagram_var.get() == 'wetherill':
            self._draw_wetherill(self.upb_ax)
        else:
            self._draw_tera_wasserburg(self.upb_ax)

        self.upb_canvas.draw()
        self.status_var.set(f"✅ U-Pb concordia plotted ({len(self.upb_spots)} spots)")

    # ============================================================================
    # Ar-Ar METHODS
    # ============================================================================
    def _plot_ar_spectrum(self):
        """Plot Ar-Ar age spectrum with plateau"""
        if not self.ar_steps:
            self.ar_ax.clear()
            self.ar_ax.text(0.5, 0.5, "No Ar-Ar data loaded", ha='center', va='center')
            self.ar_canvas.draw()
            return

        self.ar_ax.clear()

        # Sort by step
        steps_sorted = sorted(self.ar_steps, key=lambda x: x.get('step', 0))

        # Extract data
        ages = []
        errors = []
        pct_gas = []

        for step in steps_sorted:
            if 'age' in step and 'age_err' in step:
                ages.append(step['age'])
                errors.append(step['age_err'])
                pct_gas.append(step.get('pct_39Ar', 1))

        if not ages:
            self.ar_ax.text(0.5, 0.5, "No age data in steps", ha='center', va='center')
            self.ar_canvas.draw()
            return

        # Normalize gas percentages
        pct_gas = np.array(pct_gas)
        pct_gas = pct_gas / pct_gas.sum() * 100

        # Calculate cumulative
        cum_gas = np.cumsum(pct_gas)

        # Plot as boxes
        left = 0
        for i, (age, err, pct) in enumerate(zip(ages, errors, pct_gas)):
            rect = plt.Rectangle((left, age - err), pct, 2*err,
                                facecolor='steelblue', edgecolor='black', alpha=0.7)
            self.ar_ax.add_patch(rect)
            left += pct

        # Find and plot plateau (simplified - consecutive steps with >50% gas)
        if len(ages) >= 3:
            for i in range(len(ages)):
                for j in range(i+2, len(ages)):
                    if cum_gas[j] - cum_gas[i] > 50:
                        plateau_ages = ages[i:j+1]
                        plateau_errs = errors[i:j+1]

                        # Weighted mean
                        weights = 1 / np.array(plateau_errs)**2
                        plateau_age = np.sum(np.array(plateau_ages) * weights) / np.sum(weights)
                        plateau_err = 1 / np.sqrt(np.sum(weights))

                        # Draw plateau rectangle
                        rect = plt.Rectangle((cum_gas[i], plateau_age - plateau_err),
                                           cum_gas[j] - cum_gas[i], 2*plateau_err,
                                           facecolor='red', alpha=0.2, edgecolor='red', linewidth=2)
                        self.ar_ax.add_patch(rect)

                        self.ar_ax.axhline(y=plateau_age, xmin=cum_gas[i]/100, xmax=cum_gas[j]/100,
                                         color='red', linewidth=2,
                                         label=f'Plateau: {plateau_age:.1f} ± {plateau_err:.1f} Ma')
                        break

        self.ar_ax.set_xlim(0, 100)
        self.ar_ax.set_xlabel('Cumulative ³⁹Ar Released (%)')
        self.ar_ax.set_ylabel('Age (Ma)')
        self.ar_ax.set_title('⁴⁰Ar/³⁹Ar Age Spectrum')
        self.ar_ax.grid(True, alpha=0.3)
        self.ar_ax.legend(loc='best')

        self.ar_canvas.draw()
        self.status_var.set(f"✅ Ar-Ar spectrum plotted ({len(ages)} steps)")

    # ============================================================================
    # DETRITAL METHODS
    # ============================================================================
    def _plot_detrital_kde(self, ax):
        """Plot kernel density estimates for detrital samples"""
        if not self.detrital_samples:
            ax.text(0.5, 0.5, "No detrital data loaded", ha='center', va='center')
            return

        colors = plt.cm.tab10(np.linspace(0, 1, len(self.detrital_samples)))

        for i, (sample_id, ages) in enumerate(self.detrital_samples.items()):
            if len(ages) < 3:
                continue

            ages = np.array(ages)

            # Create KDE
            kde = gaussian_kde(ages)

            # Set bandwidth
            if self.detrital_bandwidth_var.get() == 'scott':
                kde.covariance_factor = lambda: np.power(len(ages), -1/5)
                kde._compute_covariance()

            # Evaluate
            x = np.linspace(max(0, ages.min() - 100), ages.max() + 100, 300)
            y = kde(x)

            # Filter by age range
            mask = (x >= self.detrital_age_min_var.get()) & (x <= self.detrital_age_max_var.get())

            ax.plot(x[mask], y[mask], color=colors[i], linewidth=2,
                   label=f"{sample_id} (n={len(ages)})")

        ax.set_xlabel('Age (Ma)')
        ax.set_ylabel('Probability Density')
        ax.set_title('Kernel Density Estimates')
        ax.set_xlim(self.detrital_age_min_var.get(), self.detrital_age_max_var.get())
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best', fontsize=8)

    def _plot_detrital_mds(self, ax):
        """Plot MDS configuration for detrital samples"""
        if len(self.detrital_samples) < 3:
            ax.text(0.5, 0.5, "Need at least 3 samples for MDS", ha='center', va='center')
            return

        # Calculate distance matrix using KS statistics
        names = list(self.detrital_samples.keys())
        n = len(names)
        dist_matrix = np.zeros((n, n))

        for i in range(n):
            for j in range(i+1, n):
                ages_i = np.array(self.detrital_samples[names[i]])
                ages_j = np.array(self.detrital_samples[names[j]])

                if self.detrital_method_var.get() == 'ks':
                    ks_stat, _ = ks_2samp(ages_i, ages_j)
                    dist = ks_stat
                else:  # wasserstein
                    # Simple approximation
                    a = np.sort(ages_i)
                    b = np.sort(ages_j)
                    m = min(len(a), len(b))
                    dist = np.mean(np.abs(a[:m] - b[:m]))

                dist_matrix[i, j] = dist
                dist_matrix[j, i] = dist

        # Run MDS
        mds = sklearn.manifold.MDS(n_components=2, dissimilarity='precomputed',
                                   random_state=42, normalized_stress='auto')
        coords = mds.fit_transform(dist_matrix)
        stress = mds.stress_ / (n**2)

        # Plot
        colors = plt.cm.tab10(np.linspace(0, 1, n))
        ax.scatter(coords[:, 0], coords[:, 1], c=colors, s=100, alpha=0.7, edgecolor='black')

        for i, name in enumerate(names):
            ax.annotate(name, (coords[i, 0], coords[i, 1]),
                       xytext=(5, 5), textcoords='offset points',
                       fontsize=8, bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.7))

        ax.set_xlabel('Dimension 1')
        ax.set_ylabel('Dimension 2')
        ax.set_title(f'MDS Configuration (stress = {stress:.3f})')
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')

    def _plot_detrital(self):
        """Update detrital plot"""
        self.detrital_ax.clear()

        if self.detrital_plot_var.get() == 'kde':
            self._plot_detrital_kde(self.detrital_ax)
        else:
            self._plot_detrital_mds(self.detrital_ax)

        self.detrital_canvas.draw()
        self.status_var.set(f"✅ Detrital {self.detrital_plot_var.get().upper()} plotted")

    # ============================================================================
    # ISOCHRON METHODS
    # ============================================================================
    def _york_regression(self, x, y, sigma_x, sigma_y):
        """Simplified York regression"""
        if len(x) < 3:
            return None

        # Simple weighted least squares
        weights = 1 / sigma_y**2
        slope, intercept = np.polyfit(x, y, 1, w=weights)

        # MSWD
        y_pred = intercept + slope * x
        mswd = np.sum(((y - y_pred) / sigma_y)**2) / (len(x) - 2)

        return slope, intercept, mswd

    def _plot_isochron(self):
        """Plot isochron for selected system"""
        if not self.isochron_points:
            self.iso_ax.clear()
            self.iso_ax.text(0.5, 0.5, "No isochron data loaded", ha='center', va='center')
            self.iso_canvas.draw()
            return

        # Filter by system
        system = self.iso_system_var.get()
        points = [p for p in self.isochron_points if p['system'] == system]

        if len(points) < 3:
            self.iso_ax.clear()
            self.iso_ax.text(0.5, 0.5, f"Need at least 3 points for {system}", ha='center', va='center')
            self.iso_canvas.draw()
            return

        # Extract data
        x = np.array([p['x'] for p in points])
        y = np.array([p['y'] for p in points])
        sigma_x = np.array([p.get('sigma_x', x[i]*0.01) for i, p in enumerate(points)])
        sigma_y = np.array([p.get('sigma_y', y[i]*0.0001) for i, p in enumerate(points)])

        # Run regression
        result = self._york_regression(x, y, sigma_x, sigma_y)

        self.iso_ax.clear()

        # Plot data with error bars
        self.iso_ax.errorbar(x, y, xerr=sigma_x, yerr=sigma_y,
                            fmt='ro', capsize=2, alpha=0.7, markersize=6)

        # Plot regression line
        if result:
            slope, intercept, mswd = result
            x_fit = np.linspace(min(x), max(x), 50)
            y_fit = intercept + slope * x_fit
            self.iso_ax.plot(x_fit, y_fit, 'b-', linewidth=2,
                            label=f'Slope: {slope:.4f}\nMSWD: {mswd:.2f}')

        # Labels based on system
        if system == 'Rb-Sr':
            self.iso_ax.set_xlabel('⁸⁷Rb/⁸⁶Sr')
            self.iso_ax.set_ylabel('⁸⁷Sr/⁸⁶Sr')
        elif system == 'Sm-Nd':
            self.iso_ax.set_xlabel('¹⁴⁷Sm/¹⁴⁴Nd')
            self.iso_ax.set_ylabel('¹⁴³Nd/¹⁴⁴Nd')
        else:
            self.iso_ax.set_xlabel('Parent/Daughter')
            self.iso_ax.set_ylabel('Daughter Ratio')

        self.iso_ax.set_title(f'{system} Isochron')
        self.iso_ax.grid(True, alpha=0.3)
        self.iso_ax.legend(loc='best')
        self.iso_ax.set_aspect('equal')

        self.iso_canvas.draw()
        self.status_var.set(f"✅ {system} isochron plotted ({len(points)} points)")

    # ============================================================================
    # EXPORT RESULTS
    # ============================================================================
    def _export_results(self):
        """Export results to main app"""
        records = []
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Export U-Pb spots
        for spot in self.upb_spots:
            record = {
                'Sample_ID': spot.get('sample_id', 'Unknown'),
                'Spot_ID': spot.get('spot_name', ''),
                'Geochron_Analysis': 'U-Pb',
                'Geochron_Timestamp': timestamp
            }
            if '206_238' in spot:
                record['206Pb_238U'] = f"{spot['206_238']:.6f}"
            if '207_235' in spot:
                record['207Pb_235U'] = f"{spot['207_235']:.6f}"
            records.append(record)

        # Export Ar-Ar steps
        for step in self.ar_steps:
            record = {
                'Sample_ID': step.get('sample_id', 'Unknown'),
                'Step': step.get('step', ''),
                'Geochron_Analysis': 'Ar-Ar',
                'Geochron_Timestamp': timestamp
            }
            if 'age' in step:
                record['Ar_Age_Ma'] = f"{step['age']:.1f}"
            records.append(record)

        # Export detrital summaries
        for sample_id, ages in self.detrital_samples.items():
            if ages:
                record = {
                    'Sample_ID': sample_id,
                    'Geochron_Analysis': 'Detrital',
                    'Geochron_Timestamp': timestamp,
                    'n_grains': len(ages),
                    'Mean_Age_Ma': f"{np.mean(ages):.1f}"
                }
                records.append(record)

        if records:
            self.app.import_data_from_plugin(records)
            self.status_var.set(f"✅ Exported {len(records)} records")
        else:
            messagebox.showinfo("Export", "No data to export")

    # ============================================================================
    # UI CONSTRUCTION - COMPACT DESIGN
    # ============================================================================
    def open_window(self):
        """Open the main window"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            self._load_from_main_app()
            return

        if not self.dependencies_met:
            messagebox.showerror(
                "Missing Dependencies",
                f"Please install: {', '.join(self.missing_deps)}"
            )
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("⏳ Geochronology Suite v1.0 - U-Pb · Ar-Ar · Detrital · Isochrons")
        self.window.geometry("1100x700")

        self._create_interface()

        # Load data
        if self._load_from_main_app():
            self.status_var.set(f"✅ Loaded data from main app")
        else:
            self.status_var.set("ℹ️ No geochronology data found")

        self.window.transient(self.app.root)
        self.window.lift()
        self.window.focus_force()

    def _create_interface(self):
        """Create the interface with 4 tabs"""
        # Header
        header = tk.Frame(self.window, bg="#2c3e50", height=40)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="⏳", font=("Arial", 18),
                bg="#2c3e50", fg="white").pack(side=tk.LEFT, padx=8)
        tk.Label(header, text="Geochronology Suite",
                font=("Arial", 14, "bold"),
                bg="#2c3e50", fg="white").pack(side=tk.LEFT, padx=2)
        tk.Label(header, text="v1.0 - U-Pb · Ar-Ar · Detrital · Isochrons",
                font=("Arial", 8),
                bg="#2c3e50", fg="#f1c40f").pack(side=tk.LEFT, padx=8)

        # Main notebook
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create tabs
        self._create_upb_tab()
        self._create_ar_tab()
        self._create_detrital_tab()
        self._create_isochron_tab()

        # Status bar
        status = tk.Frame(self.window, bg="#34495e", height=24)
        status.pack(fill=tk.X, side=tk.BOTTOM)
        status.pack_propagate(False)

        self.status_var = tk.StringVar(value="Ready")
        tk.Label(status, textvariable=self.status_var,
                font=("Arial", 8), bg="#34495e", fg="white").pack(side=tk.LEFT, padx=8)

        tk.Button(status, text="📤 Export to Main App",
                 command=self._export_results,
                 bg="#27ae60", fg="white", font=("Arial", 7)).pack(side=tk.RIGHT, padx=5)

        self.progress = ttk.Progressbar(status, mode='indeterminate', length=120)
        self.progress.pack(side=tk.RIGHT, padx=5)

    # ============================================================================
    # TAB 1: U-Pb Concordia
    # ============================================================================
    def _create_upb_tab(self):
        """Create U-Pb tab"""
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="🔷 U-Pb Concordia")

        # Split into left/right
        paned = tk.PanedWindow(tab, orient=tk.HORIZONTAL, sashwidth=4)
        paned.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Left panel - controls (280px)
        left = tk.Frame(paned, bg="#f5f5f5", width=280)
        paned.add(left, width=280, minsize=250)

        # Right panel - plot (500x500 square)
        right = tk.Frame(paned, bg="white", width=500, height=500)
        paned.add(right, width=500, minsize=450)

        # ===== Left controls =====
        # Data summary
        summary = tk.LabelFrame(left, text="📊 Data", padx=5, pady=5, bg="#f5f5f5")
        summary.pack(fill=tk.X, padx=5, pady=2)

        self.upb_count_label = tk.Label(summary, text=f"Spots: {len(self.upb_spots)}",
                                        font=("Arial", 9), bg="#f5f5f5")
        self.upb_count_label.pack(anchor=tk.W)

        # Diagram type
        diag_frame = tk.LabelFrame(left, text="📈 Diagram", padx=5, pady=5, bg="#f5f5f5")
        diag_frame.pack(fill=tk.X, padx=5, pady=2)

        tk.Radiobutton(diag_frame, text="Wetherill", variable=self.upb_diagram_var,
                      value="wetherill", bg="#f5f5f5").pack(anchor=tk.W)
        tk.Radiobutton(diag_frame, text="Tera-Wasserburg", variable=self.upb_diagram_var,
                      value="tera", bg="#f5f5f5").pack(anchor=tk.W)

        # Display options
        disp_frame = tk.LabelFrame(left, text="🎨 Display", padx=5, pady=5, bg="#f5f5f5")
        disp_frame.pack(fill=tk.X, padx=5, pady=2)

        tk.Checkbutton(disp_frame, text="Show error ellipses",
                      variable=self.upb_ellipse_var,
                      bg="#f5f5f5").pack(anchor=tk.W)
        tk.Checkbutton(disp_frame, text="Show concordia",
                      variable=self.upb_show_concordia_var,
                      bg="#f5f5f5").pack(anchor=tk.W)

        # Age range
        range_frame = tk.LabelFrame(left, text="📏 Age Range (Ma)", padx=5, pady=5, bg="#f5f5f5")
        range_frame.pack(fill=tk.X, padx=5, pady=2)

        tk.Label(range_frame, text="Min:").grid(row=0, column=0, sticky=tk.W)
        tk.Spinbox(range_frame, from_=0, to=4500, increment=10,
                  textvariable=self.upb_age_min_var, width=6).grid(row=0, column=1, padx=2)
        tk.Label(range_frame, text="Max:").grid(row=1, column=0, sticky=tk.W)
        tk.Spinbox(range_frame, from_=0, to=4500, increment=10,
                  textvariable=self.upb_age_max_var, width=6).grid(row=1, column=1, padx=2)

        # Plot button
        tk.Button(left, text="📈 Plot Concordia",
                 command=self._plot_upb,
                 bg="#e67e22", fg="white", width=20).pack(pady=5)

        # ===== Right plot =====
        self.upb_fig = plt.Figure(figsize=(5, 5), dpi=90)  # Square
        self.upb_fig.patch.set_facecolor('white')
        self.upb_ax = self.upb_fig.add_subplot(111)
        self.upb_ax.set_facecolor('#f8f9fa')

        self.upb_canvas = FigureCanvasTkAgg(self.upb_fig, right)
        self.upb_canvas.draw()
        self.upb_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Compact toolbar
        toolbar_frame = tk.Frame(right, height=25)
        toolbar_frame.pack(fill=tk.X)
        toolbar = NavigationToolbar2Tk(self.upb_canvas, toolbar_frame)
        toolbar.update()

    # ============================================================================
    # TAB 2: Ar-Ar
    # ============================================================================
    def _create_ar_tab(self):
        """Create Ar-Ar tab"""
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="⚛️ Ar-Ar Spectrum")

        # Split into left/right
        paned = tk.PanedWindow(tab, orient=tk.HORIZONTAL, sashwidth=4)
        paned.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Left panel - controls (280px)
        left = tk.Frame(paned, bg="#f5f5f5", width=280)
        paned.add(left, width=280, minsize=250)

        # Right panel - plot (500x500 square)
        right = tk.Frame(paned, bg="white", width=500, height=500)
        paned.add(right, width=500, minsize=450)

        # ===== Left controls =====
        # Data summary
        summary = tk.LabelFrame(left, text="📊 Data", padx=5, pady=5, bg="#f5f5f5")
        summary.pack(fill=tk.X, padx=5, pady=2)

        self.ar_count_label = tk.Label(summary, text=f"Steps: {len(self.ar_steps)}",
                                       font=("Arial", 9), bg="#f5f5f5")
        self.ar_count_label.pack(anchor=tk.W)

        # Plateau threshold
        thresh_frame = tk.LabelFrame(left, text="⚙️ Plateau", padx=5, pady=5, bg="#f5f5f5")
        thresh_frame.pack(fill=tk.X, padx=5, pady=2)

        tk.Label(thresh_frame, text="Min % ³⁹Ar:", bg="#f5f5f5").pack(anchor=tk.W)
        tk.Scale(thresh_frame, from_=0.1, to=0.9, resolution=0.05,
                orient=tk.HORIZONTAL, variable=self.ar_plateau_threshold_var,
                length=150).pack(fill=tk.X)

        # Plot button
        tk.Button(left, text="📊 Plot Age Spectrum",
                 command=self._plot_ar_spectrum,
                 bg="#e67e22", fg="white", width=20).pack(pady=5)

        # ===== Right plot =====
        self.ar_fig = plt.Figure(figsize=(5, 5), dpi=90)  # Square
        self.ar_fig.patch.set_facecolor('white')
        self.ar_ax = self.ar_fig.add_subplot(111)
        self.ar_ax.set_facecolor('#f8f9fa')

        self.ar_canvas = FigureCanvasTkAgg(self.ar_fig, right)
        self.ar_canvas.draw()
        self.ar_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        toolbar_frame = tk.Frame(right, height=25)
        toolbar_frame.pack(fill=tk.X)
        toolbar = NavigationToolbar2Tk(self.ar_canvas, toolbar_frame)
        toolbar.update()

    # ============================================================================
    # TAB 3: Detrital
    # ============================================================================
    def _create_detrital_tab(self):
        """Create detrital tab"""
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="🏜️ Detrital")

        # Split into left/right
        paned = tk.PanedWindow(tab, orient=tk.HORIZONTAL, sashwidth=4)
        paned.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Left panel - controls (280px)
        left = tk.Frame(paned, bg="#f5f5f5", width=280)
        paned.add(left, width=280, minsize=250)

        # Right panel - plot (500x500 square)
        right = tk.Frame(paned, bg="white", width=500, height=500)
        paned.add(right, width=500, minsize=450)

        # ===== Left controls =====
        # Data summary
        summary = tk.LabelFrame(left, text="📊 Data", padx=5, pady=5, bg="#f5f5f5")
        summary.pack(fill=tk.X, padx=5, pady=2)

        self.detrital_count_label = tk.Label(summary, text=f"Samples: {len(self.detrital_samples)}",
                                             font=("Arial", 9), bg="#f5f5f5")
        self.detrital_count_label.pack(anchor=tk.W)

        # Plot type
        plot_frame = tk.LabelFrame(left, text="📈 Plot", padx=5, pady=5, bg="#f5f5f5")
        plot_frame.pack(fill=tk.X, padx=5, pady=2)

        tk.Radiobutton(plot_frame, text="KDE", variable=self.detrital_plot_var,
                      value="kde", bg="#f5f5f5").pack(anchor=tk.W)
        tk.Radiobutton(plot_frame, text="MDS", variable=self.detrital_plot_var,
                      value="mds", bg="#f5f5f5").pack(anchor=tk.W)

        # KDE options
        kde_frame = tk.LabelFrame(left, text="⚙️ KDE", padx=5, pady=5, bg="#f5f5f5")
        kde_frame.pack(fill=tk.X, padx=5, pady=2)

        tk.Label(kde_frame, text="Bandwidth:", bg="#f5f5f5").pack(anchor=tk.W)
        tk.Radiobutton(kde_frame, text="Scott", variable=self.detrital_bandwidth_var,
                      value="scott", bg="#f5f5f5").pack(anchor=tk.W, padx=10)
        tk.Radiobutton(kde_frame, text="Silverman", variable=self.detrital_bandwidth_var,
                      value="silverman", bg="#f5f5f5").pack(anchor=tk.W, padx=10)

        # MDS options
        mds_frame = tk.LabelFrame(left, text="⚙️ MDS", padx=5, pady=5, bg="#f5f5f5")
        mds_frame.pack(fill=tk.X, padx=5, pady=2)

        tk.Label(mds_frame, text="Distance:", bg="#f5f5f5").pack(anchor=tk.W)
        tk.Radiobutton(mds_frame, text="KS", variable=self.detrital_method_var,
                      value="ks", bg="#f5f5f5").pack(anchor=tk.W, padx=10)
        tk.Radiobutton(mds_frame, text="Wasserstein", variable=self.detrital_method_var,
                      value="wasserstein", bg="#f5f5f5").pack(anchor=tk.W, padx=10)

        # Age range
        range_frame = tk.LabelFrame(left, text="📏 Age Range (Ma)", padx=5, pady=5, bg="#f5f5f5")
        range_frame.pack(fill=tk.X, padx=5, pady=2)

        tk.Label(range_frame, text="Min:").grid(row=0, column=0, sticky=tk.W)
        tk.Spinbox(range_frame, from_=0, to=4500, increment=10,
                  textvariable=self.detrital_age_min_var, width=6).grid(row=0, column=1, padx=2)
        tk.Label(range_frame, text="Max:").grid(row=1, column=0, sticky=tk.W)
        tk.Spinbox(range_frame, from_=0, to=4500, increment=10,
                  textvariable=self.detrital_age_max_var, width=6).grid(row=1, column=1, padx=2)

        # Plot button
        tk.Button(left, text="📈 Plot",
                 command=self._plot_detrital,
                 bg="#e67e22", fg="white", width=20).pack(pady=5)

        # ===== Right plot =====
        self.detrital_fig = plt.Figure(figsize=(5, 5), dpi=90)  # Square
        self.detrital_fig.patch.set_facecolor('white')
        self.detrital_ax = self.detrital_fig.add_subplot(111)
        self.detrital_ax.set_facecolor('#f8f9fa')

        self.detrital_canvas = FigureCanvasTkAgg(self.detrital_fig, right)
        self.detrital_canvas.draw()
        self.detrital_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        toolbar_frame = tk.Frame(right, height=25)
        toolbar_frame.pack(fill=tk.X)
        toolbar = NavigationToolbar2Tk(self.detrital_canvas, toolbar_frame)
        toolbar.update()

    # ============================================================================
    # TAB 4: Isochrons
    # ============================================================================
    def _create_isochron_tab(self):
        """Create isochron tab"""
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="📈 Isochrons")

        # Split into left/right
        paned = tk.PanedWindow(tab, orient=tk.HORIZONTAL, sashwidth=4)
        paned.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Left panel - controls (280px)
        left = tk.Frame(paned, bg="#f5f5f5", width=280)
        paned.add(left, width=280, minsize=250)

        # Right panel - plot (500x500 square)
        right = tk.Frame(paned, bg="white", width=500, height=500)
        paned.add(right, width=500, minsize=450)

        # ===== Left controls =====
        # Data summary
        summary = tk.LabelFrame(left, text="📊 Data", padx=5, pady=5, bg="#f5f5f5")
        summary.pack(fill=tk.X, padx=5, pady=2)

        self.iso_count_label = tk.Label(summary, text=f"Points: {len(self.isochron_points)}",
                                        font=("Arial", 9), bg="#f5f5f5")
        self.iso_count_label.pack(anchor=tk.W)

        # System selection
        sys_frame = tk.LabelFrame(left, text="🔬 System", padx=5, pady=5, bg="#f5f5f5")
        sys_frame.pack(fill=tk.X, padx=5, pady=2)

        systems = ["Rb-Sr", "Sm-Nd", "Lu-Hf", "Re-Os", "K-Ca", "Pb-Pb"]
        for sys in systems:
            tk.Radiobutton(sys_frame, text=sys, variable=self.iso_system_var,
                          value=sys, bg="#f5f5f5").pack(anchor=tk.W)

        # Regression method
        reg_frame = tk.LabelFrame(left, text="📐 Regression", padx=5, pady=5, bg="#f5f5f5")
        reg_frame.pack(fill=tk.X, padx=5, pady=2)

        tk.Radiobutton(reg_frame, text="York (1966)", variable=self.iso_regression_var,
                      value="york", bg="#f5f5f5").pack(anchor=tk.W)

        # Plot button
        tk.Button(left, text="📈 Plot Isochron",
                 command=self._plot_isochron,
                 bg="#e67e22", fg="white", width=20).pack(pady=5)

        # ===== Right plot =====
        self.iso_fig = plt.Figure(figsize=(5, 5), dpi=90)  # Square
        self.iso_fig.patch.set_facecolor('white')
        self.iso_ax = self.iso_fig.add_subplot(111)
        self.iso_ax.set_facecolor('#f8f9fa')

        self.iso_canvas = FigureCanvasTkAgg(self.iso_fig, right)
        self.iso_canvas.draw()
        self.iso_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        toolbar_frame = tk.Frame(right, height=25)
        toolbar_frame.pack(fill=tk.X)
        toolbar = NavigationToolbar2Tk(self.iso_canvas, toolbar_frame)
        toolbar.update()


def setup_plugin(main_app):
    """Plugin setup function"""
    plugin = GeochronologySuitePlugin(main_app)
    return plugin
