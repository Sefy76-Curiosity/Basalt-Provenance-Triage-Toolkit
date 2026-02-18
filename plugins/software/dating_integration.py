"""
Chronological Dating Integration Plugin
ENHANCED v8.0 - COMPLETE WORKING VERSION
All methods included - no missing attributes
"""

PLUGIN_INFO = {
    "category": "software",
    "id": "dating_integration",
    "name": "Chronological Dating (Enhanced)",
    "description": "Bayesian age-depth with MCMC, parallel processing, user-supplied curves",
    "icon": "⏳🔬",
    "version": "8.0",
    "requires": ["numpy", "scipy", "matplotlib", "pandas", "emcee", "corner", "joblib"],
    "author": "Enhanced from Sefy Levy & DeepSeek",
    "item": {
        "type": "plugin",
        "subtype": "chronology",
        "tags": ["bayesian", "mcmc", "parallel", "intcal", "calibration"],
        "compatibility": ["main_app_v2+"],
        "dependencies": [
            "numpy>=1.21.0",
            "scipy>=1.7.0",
            "matplotlib>=3.4.0",
            "pandas>=1.3.0",
            "emcee>=3.1.0",
            "corner>=2.2.1",
            "joblib>=1.1.0"
        ],
        "settings": {
            "default_method": "clam",
            "auto_calibrate": True,
            "curve_repository": {}
        }
    }
}

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import pandas as pd
import numpy as np
import threading
import time
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from scipy.interpolate import interp1d, PchipInterpolator, UnivariateSpline
from scipy.stats import norm, gaussian_kde
import warnings
import os
import json
import urllib.request
import urllib.error
import ssl
from pathlib import Path
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import traceback

# Try importing optional packages
try:
    import emcee
    import corner
    HAS_EMCEE = True
except ImportError:
    HAS_EMCEE = False
    print("⚠️ emcee not installed - Bayesian MCMC disabled")

try:
    from joblib import Parallel, delayed
    HAS_JOBLIB = True
except ImportError:
    HAS_JOBLIB = False
    print("⚠️ joblib not installed - parallel processing disabled")

warnings.filterwarnings('ignore')

# ============================================================================
# PART 1: CURVE MANAGER - COMPLETE WITH ALL METHODS
# ============================================================================

class CurveManager:
    """
    Manages calibration curves from USER-SUPPLIED URLs and files.
    Complete with all methods including set_status_callback
    """

    # Default repository file
    REPO_FILE = 'curve_repository.json'

    def __init__(self, app_dir=None):
        """Initialize curve manager"""
        if app_dir is None:
            app_dir = Path.home() / '.chrono'

        self.app_dir = Path(app_dir)
        self.app_dir.mkdir(parents=True, exist_ok=True)

        self.cache_dir = self.app_dir / 'curves'
        self.cache_dir.mkdir(exist_ok=True)

        self.repo_file = self.app_dir / self.REPO_FILE

        # Storage
        self.curves = {}           # Loaded curve data
        self.interpolators = {}    # Interpolation functions
        self.repository = {}       # User's URL collection
        self.status_callback = None
        self.model_btn = None

        # Load saved repository
        self._load_repository()

    def set_status_callback(self, callback):
        """Set callback for status updates"""
        self.status_callback = callback

    def _update_status(self, message, level="info"):
        """Update status via callback"""
        if self.status_callback:
            self.status_callback(message, level)

    # ========== REPOSITORY MANAGEMENT ==========

    def _load_repository(self):
        """Load saved curve repository"""
        if self.repo_file.exists():
            try:
                with open(self.repo_file, 'r') as f:
                    self.repository = json.load(f)
                self._update_status(f"📚 Loaded {len(self.repository)} saved curves", "info")
            except:
                self.repository = {}

    def _save_repository(self):
        """Save curve repository"""
        try:
            with open(self.repo_file, 'w') as f:
                json.dump(self.repository, f, indent=2)
        except Exception as e:
            self._update_status(f"⚠️ Could not save repository: {e}", "warning")

    def add_curve_source(self, name, url, description="", year=None, curve_type="custom"):
        """Add a curve source URL to repository"""
        self.repository[name] = {
            'url': url,
            'description': description,
            'year': year,
            'type': curve_type,
            'added': datetime.now().isoformat(),
            'last_accessed': None
        }
        self._save_repository()
        self._update_status(f"✅ Added curve source: {name}", "success")

    def remove_curve_source(self, name):
        """Remove curve source from repository"""
        if name in self.repository:
            del self.repository[name]
            self._save_repository()
            self._update_status(f"🗑️ Removed curve: {name}", "info")

    def get_repository_curves(self):
        """Get list of available curve sources"""
        return [(name, info) for name, info in self.repository.items()]

    # ========== CURVE LOADING ==========

    def _parse_14c_file(self, content, source):
        """Parse .14c format file"""
        lines = content.strip().split('\n')

        data = []
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = line.split()
            if len(parts) >= 3:
                try:
                    cal_age = float(parts[0])
                    c14_age = float(parts[1])
                    error = float(parts[2])
                    data.append([cal_age, c14_age, error])
                except ValueError:
                    continue

        if len(data) < 5:
            raise ValueError(f"Insufficient data points in {source}")

        return np.array(data, dtype=float)

    def load_from_url(self, name, url, force=False):
        """Load curve from user-supplied URL"""
        cache_path = self.cache_dir / f"{name.replace(' ', '_')}.14c"

        # Check cache
        if not force and cache_path.exists():
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                data = self._parse_14c_file(content, f"cache:{name}")

                # Update repository
                if name in self.repository:
                    self.repository[name]['last_accessed'] = datetime.now().isoformat()
                    self._save_repository()

                self._add_curve(name, data, {'source': 'cache', 'url': url})
                self._update_status(f"✅ Loaded {name} from cache", "success")
                return data

            except Exception as e:
                self._update_status(f"⚠️ Cache invalid for {name}, re-downloading...", "warning")

        # Download from URL
        self._update_status(f"⬇️ Downloading {name} from {url}", "info")

        try:
            # Create SSL context
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'Mozilla/5.0 (ChronoPlugin/7.0)'}
            )

            with urllib.request.urlopen(req, context=ssl_context, timeout=30) as response:
                content = response.read().decode('utf-8')

            # Parse
            data = self._parse_14c_file(content, f"url:{url}")

            # Save to cache
            with open(cache_path, 'w', encoding='utf-8') as f:
                f.write(content)

            # Update repository
            if name in self.repository:
                self.repository[name]['last_accessed'] = datetime.now().isoformat()
                self.repository[name]['url'] = url  # Update URL
            else:
                self.add_curve_source(name, url, "Downloaded curve")

            self._add_curve(name, data, {'source': 'url', 'url': url})
            self._update_status(f"✅ Downloaded {name} ({len(data)} points)", "success")
            return data

        except urllib.error.HTTPError as e:
            if e.code == 404:
                self._update_status(f"❌ URL not found (404): {url}", "error")
            else:
                self._update_status(f"❌ HTTP {e.code}: {url}", "error")
            return None

        except Exception as e:
            self._update_status(f"❌ Download failed: {str(e)}", "error")
            return None

    def load_from_file(self, filepath):
        """Load curve from local file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            name = os.path.splitext(os.path.basename(filepath))[0]
            data = self._parse_14c_file(content, f"file:{filepath}")

            # Copy to cache
            cache_path = self.cache_dir / f"{name.replace(' ', '_')}.14c"
            with open(cache_path, 'w', encoding='utf-8') as f:
                f.write(content)

            self._add_curve(name, data, {'source': 'file', 'path': filepath})
            self._update_status(f"✅ Loaded {name} from file", "success")
            return name, data

        except Exception as e:
            self._update_status(f"❌ File load failed: {str(e)}", "error")
            return None, None

    def _add_curve(self, name, data, metadata=None):
        """Add curve to memory and build interpolator"""
        cal_age = data[:, 0]
        c14_age = data[:, 1]
        c14_error = data[:, 2]

        # Sort and clean
        sort_idx = np.argsort(cal_age)
        cal_age = cal_age[sort_idx]
        c14_age = c14_age[sort_idx]
        c14_error = c14_error[sort_idx]

        _, unique_idx = np.unique(cal_age, return_index=True)
        cal_age = cal_age[unique_idx]
        c14_age = c14_age[unique_idx]
        c14_error = c14_error[unique_idx]

        # Store data
        self.curves[name] = {
            'data': data,
            'metadata': metadata or {},
            'loaded': datetime.now().isoformat()
        }

        # Build interpolator
        self.interpolators[name] = {
            'age': interp1d(cal_age, c14_age, kind='linear',
                          bounds_error=False, fill_value=np.nan),
            'error': interp1d(cal_age, c14_error, kind='linear',
                            bounds_error=False, fill_value=np.nan),
            'range': (np.min(cal_age), np.max(cal_age)),
            'points': len(cal_age)
        }

    def get_available_curves(self):
        """Get list of available curves (loaded + repository)"""
        loaded = list(self.curves.keys())
        repos = [name for name in self.repository.keys() if name not in loaded]
        return loaded + repos

    def get_curve_info(self, name):
        """Get curve metadata"""
        if name in self.curves:
            info = self.curves[name]['metadata'].copy()
            info['loaded'] = self.curves[name]['loaded']
            info['points'] = len(self.curves[name]['data'])
            info['range'] = self.interpolators[name]['range']
            return info
        elif name in self.repository:
            return self.repository[name].copy()
        return {}

    def ensure_curve(self, name, force_download=False):
        """Ensure curve is loaded, try to load if not"""
        if name in self.interpolators:
            return True

        # Try repository
        if name in self.repository:
            url = self.repository[name]['url']
            data = self.load_from_url(name, url, force=force_download)
            return data is not None

        return False

    def load_multiple_curves_parallel(self, curve_names, force=False):
        """Load multiple curves in parallel"""
        if not HAS_JOBLIB:
            # Fall back to sequential
            results = {}
            for name in curve_names:
                results[name] = self.ensure_curve(name, force)
            return results

        def _load_one(name):
            return name, self.ensure_curve(name, force)

        results_list = Parallel(n_jobs=-1, verbose=0)(
            delayed(_load_one)(name) for name in curve_names
        )
        return dict(results_list)

    # ========== CALIBRATION ==========

    def calibrate(self, c14_age, c14_error, curve_name, deltaR=0, deltaR_error=0):
        """Calibrate radiocarbon date using named curve"""
        # Ensure curve is loaded
        if not self.ensure_curve(curve_name):
            raise ValueError(f"Curve '{curve_name}' not available")

        interp = self.interpolators[curve_name]

        # Apply reservoir correction
        corrected_age = c14_age - deltaR
        corrected_error = np.sqrt(c14_error**2 + deltaR_error**2)

        # Get curve range
        cal_min, cal_max = interp['range']

        # Define calibration range
        min_cal = max(cal_min, corrected_age - 5 * corrected_error)
        max_cal = min(cal_max, corrected_age + 5 * corrected_error)

        cal_grid = np.arange(min_cal, max_cal + 1, 1)
        curve_age = interp['age'](cal_grid)
        curve_error = interp['error'](cal_grid)

        # Remove NaN
        valid = ~(np.isnan(curve_age) | np.isnan(curve_error))
        cal_grid = cal_grid[valid]
        curve_age = curve_age[valid]
        curve_error = curve_error[valid]

        if len(cal_grid) < 2:
            return None

        # Calculate probability
        sigma = np.sqrt(corrected_error**2 + curve_error**2)
        prob = np.exp(-0.5 * ((curve_age - corrected_age) / sigma) ** 2)
        prob = prob / np.sum(prob)

        # Statistics
        mean_age = np.sum(cal_grid * prob)
        median_age = np.percentile(cal_grid, 50, weights=prob)
        std_age = np.sqrt(np.sum(prob * (cal_grid - mean_age) ** 2))
        mode_age = cal_grid[np.argmax(prob)]

        # HPD interval (95%)
        sorted_idx = np.argsort(prob)[::-1]
        cumsum = np.cumsum(prob[sorted_idx])
        hpd_idx = sorted_idx[cumsum <= 0.9545]

        if len(hpd_idx) > 0:
            hpd_min = np.min(cal_grid[hpd_idx])
            hpd_max = np.max(cal_grid[hpd_idx])
        else:
            hpd_min = median_age - std_age
            hpd_max = median_age + std_age

        return {
            'raw_age': c14_age,
            'raw_error': c14_error,
            'corrected_age': corrected_age,
            'corrected_error': corrected_error,
            'mean': mean_age,
            'median': median_age,
            'mode': mode_age,
            'std': std_age,
            'hpd_2sigma': (hpd_min, hpd_max),
            'probability': np.column_stack((cal_grid, prob)),
            'curve': curve_name,
            'deltaR': deltaR,
            'curve_points': interp['points'],
            'curve_range': interp['range']
        }

    def clear_cache(self):
        """Clear all cached curve files"""
        import shutil
        try:
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(exist_ok=True)
            self.curves = {}
            self.interpolators = {}
            self._update_status("🧹 Cache cleared", "success")
        except Exception as e:
            self._update_status(f"⚠️ Cache clear failed: {e}", "warning")


# ============================================================================
# PART 2: BAYESIAN AGE-DEPTH MODEL
# ============================================================================

class BayesianAgeDepthModel:
    """
    Bayesian age-depth modeling with MCMC
    Inspired by BACON but simplified and Python-native
    """

    def __init__(self):
        self.sampler = None
        self.samples = None
        self.chain = None
        self.acceptance = None

    def log_prior(self, params, depths, ages, errors, prior_info):
        """
        Prior probability
        params: [accumulation_rate, memory]
        """
        # Simple prior: accumulation rate > 0, memory between 0 and 1
        acc_rate = params[0]
        memory = params[1] if len(params) > 1 else 0.5

        if acc_rate <= 0:
            return -np.inf
        if memory < 0 or memory > 1:
            return -np.inf

        # Prior from user if provided
        if 'acc_rate_prior' in prior_info:
            mu, sigma = prior_info['acc_rate_prior']
            prior_acc = norm.logpdf(acc_rate, mu, sigma)
        else:
            # Weak prior (log-uniform)
            prior_acc = -np.log(acc_rate)

        if 'memory_prior' in prior_info:
            mu, sigma = prior_info['memory_prior']
            prior_mem = norm.logpdf(memory, mu, sigma)
        else:
            prior_mem = 0  # Uniform

        return prior_acc + prior_mem

    def log_likelihood(self, params, depths, ages, errors):
        """
        Likelihood: how well model fits the data
        """
        acc_rate = params[0]
        memory = params[1] if len(params) > 1 else 0.5

        # Simple piecewise linear model with memory
        n_points = len(depths)
        modeled_ages = np.zeros(n_points)
        modeled_ages[0] = ages[0]

        for i in range(1, n_points):
            # Memory: weighted average between accumulation rate and previous
            dx = depths[i] - depths[i-1]
            expected_increase = dx * acc_rate
            modeled_ages[i] = modeled_ages[i-1] + expected_increase * memory + \
                             (ages[i] - ages[i-1]) * (1 - memory)

        # Calculate likelihood (Gaussian)
        chi2 = np.sum(((ages - modeled_ages) / errors) ** 2)
        return -0.5 * chi2

    def log_probability(self, params, depths, ages, errors, prior_info):
        """Combined log probability"""
        lp = self.log_prior(params, depths, ages, errors, prior_info)
        if not np.isfinite(lp):
            return -np.inf
        return lp + self.log_likelihood(params, depths, ages, errors)

    def run_mcmc(self, depths, ages, errors,
                 n_walkers=32, n_steps=2000, n_burn=500,
                 prior_info=None, threads=1):
        """
        Run MCMC sampling
        """
        if not HAS_EMCEE:
            raise ImportError("emcee required for Bayesian modeling")

        prior_info = prior_info or {}

        # Initial guess
        acc_rate_init = np.mean(np.diff(ages) / np.diff(depths))
        memory_init = 0.5

        n_dim = 2  # [acc_rate, memory]
        pos = [np.array([acc_rate_init * (1 + 0.1*np.random.randn()),
                         memory_init * (1 + 0.1*np.random.randn())])
               for _ in range(n_walkers)]

        # Run MCMC
        self.sampler = emcee.EnsembleSampler(
            n_walkers, n_dim, self.log_probability,
            args=(depths, ages, errors, prior_info),
            threads=threads
        )

        # Burn-in
        print("Running burn-in...")
        pos, _, _ = self.sampler.run_mcmc(pos, n_burn, progress=True)
        self.sampler.reset()

        # Production
        print("Running production MCMC...")
        self.sampler.run_mcmc(pos, n_steps, progress=True)

        # Get samples
        self.samples = self.sampler.get_chain(flat=True)
        self.chain = self.sampler.get_chain()
        self.acceptance = np.mean(self.sampler.acceptance_fraction)

        return self.samples

    def predict(self, new_depths, samples=None, thin=10):
        """
        Predict ages at new depths using MCMC samples
        """
        if samples is None:
            samples = self.samples

        # Thin samples to reduce memory
        samples = samples[::thin]

        n_samples = len(samples)
        n_depths = len(new_depths)
        predictions = np.zeros((n_samples, n_depths))

        for i, (acc_rate, memory) in enumerate(samples):
            # Simple accumulation model
            pred = np.zeros(n_depths)
            pred[0] = 0  # Reference age at top

            for j in range(1, n_depths):
                dx = new_depths[j] - new_depths[j-1]
                pred[j] = pred[j-1] + dx * acc_rate

            predictions[i] = pred

        # Calculate statistics
        median = np.median(predictions, axis=0)
        lower = np.percentile(predictions, 2.5, axis=0)
        upper = np.percentile(predictions, 97.5, axis=0)

        return {
            'depths': new_depths,
            'median': median,
            'lower_ci': lower,
            'upper_ci': upper,
            'samples': predictions,
            'acc_rate_samples': samples[:, 0],
            'memory_samples': samples[:, 1] if samples.shape[1] > 1 else None
        }


# ============================================================================
# PART 3: ENHANCED DATING PLUGIN - COMPLETE IMPLEMENTATION
# ============================================================================

class EnhancedDatingIntegrationPlugin:
    def __init__(self, main_app):
        self.app = main_app
        self.window = None
        self.df = pd.DataFrame()
        self.is_processing = False
        self.cancelled = False
        self.progress = None
        self.age_model = None
        self.calibration_results = None
        self.bayesian_model = None
        self._start_time = None
        self.mcmc_samples = None

        # Initialize curve manager
        self.curves = CurveManager()
        self.curves.set_status_callback(self._update_status)

        # Initialize example repository
        self._init_example_repository()

        # Modeling methods
        self.MODELING_METHODS = {
            "Clam": "Smoothing spline (Blaauw 2010)",
            "Linear": "Linear interpolation",
            "Spline": "Monotonic cubic spline",
            "Polynomial": "Polynomial regression",
            "Bayesian MCMC": "BACON-like MCMC with priors (requires emcee)"
        }

        # Parallel processing options
        self.PARALLEL_OPTIONS = {
            "None": 1,
            "2": 2,
            "4": 4,
            "8": 8,
            "Max": multiprocessing.cpu_count()
        }

        # Dating types
        self.DATING_TYPES = {
            "14C": "Radiocarbon",
            "OSL": "Optically Stimulated Luminescence",
            "U-Th": "Uranium-Thorium",
            "210Pb": "Lead-210",
            "Tephra": "Volcanic ash",
            "Varve": "Varve counting",
            "Archaeo": "Archaeological",
            "Historical": "Historical records",
            "Custom": "User-provided"
        }

        # Default parameters
        self.DEFAULT_PARAMS = {
            "clam_smooth": 0.3,
            "poly_degree": 3,
            "confidence_level": 0.95,
            "mcmc_walkers": 32,
            "mcmc_steps": 2000,
            "mcmc_burn": 500,
            "mcmc_thin": 10
        }

        # UI Variables - ALL DEFINED HERE
        self.depth_var = tk.StringVar()
        self.age_var = tk.StringVar()
        self.error_var = tk.StringVar()
        self.dating_type_var = tk.StringVar(value="14C")
        self.curve_var = tk.StringVar()
        self.auto_calibrate_var = tk.BooleanVar(value=True)
        self.deltaR_var = tk.DoubleVar(value=0)
        self.deltaR_error_var = tk.DoubleVar(value=0)
        self.method_var = tk.StringVar(value="Clam")
        self.confidence_var = tk.DoubleVar(value=0.95)

        # Bayesian prior variables
        self.acc_prior_mean = tk.DoubleVar(value=50)
        self.acc_prior_std = tk.DoubleVar(value=20)
        self.mem_prior_mean = tk.DoubleVar(value=0.5)
        self.mem_prior_std = tk.DoubleVar(value=0.2)
        self.use_priors_var = tk.BooleanVar(value=True)

        # MCMC variables
        self.mcmc_walkers_var = tk.IntVar(value=self.DEFAULT_PARAMS["mcmc_walkers"])
        self.mcmc_steps_var = tk.IntVar(value=self.DEFAULT_PARAMS["mcmc_steps"])
        self.mcmc_burn_var = tk.IntVar(value=self.DEFAULT_PARAMS["mcmc_burn"])

        # Parallel variable
        self.parallel_var = tk.StringVar(value="Max")

        # Corner plot option
        self.corner_plot_var = tk.BooleanVar(value=True)

        # Clam smooth variable
        self.clam_smooth_var = tk.DoubleVar(value=self.DEFAULT_PARAMS["clam_smooth"])

        # Extrapolate variable for linear
        self.extrapolate_var = tk.BooleanVar(value=False)

        # Polynomial degree
        self.poly_degree_var = tk.IntVar(value=self.DEFAULT_PARAMS["poly_degree"])

        # UI Components (to be created later)
        self.depth_combo = None
        self.age_combo = None
        self.error_combo = None
        self.curve_combo = None
        self.new_curve_name = None
        self.new_curve_url = None
        self.new_curve_desc = None
        self.status_label = None
        self.data_info_label = None
        self.params_frame = None
        self.notebook = None
        self.figure = None
        self.ax = None
        self.canvas = None
        self.cal_figure = None
        self.cal_ax = None
        self.cal_canvas = None
        self.mcmc_figure = None
        self.mcmc_ax1 = None
        self.mcmc_ax2 = None
        self.mcmc_ax3 = None
        self.mcmc_ax4 = None
        self.mcmc_canvas = None
        self.corner_figure = None
        self.corner_canvas = None
        self.stats_text = None
        self.model_btn = None  # Will be set when UI is created

    def _init_example_repository(self):
        """Initialize with EXAMPLE URLs"""
        examples = {
            'IntCal20': {
                'url': 'https://intcal.org/curves/intcal20.14c',
                'description': 'Northern Hemisphere',
                'year': 2020,
                'type': 'standard'
            },
            'Marine20': {
                'url': 'https://intcal.org/curves/marine20.14c',
                'description': 'Marine',
                'year': 2020,
                'type': 'standard'
            },
            'SHCal20': {
                'url': 'https://intcal.org/curves/shcal20.14c',
                'description': 'Southern Hemisphere',
                'year': 2020,
                'type': 'standard'
            }
        }

        for name, info in examples.items():
            if name not in self.curves.repository:
                self.curves.add_curve_source(name, info['url'], info['description'],
                                            info['year'], info['type'])

    def _update_status(self, message, level="info"):
        """Update status label"""
        colors = {
            "info": "#2c3e50",
            "success": "green",
            "warning": "orange",
            "error": "red"
        }
        color = colors.get(level, "#2c3e50")

        if hasattr(self, 'status_label') and self.status_label:
            self.status_label.config(text=message, fg=color)
            print(f"[{level.upper()}] {message}")

    # ============= WINDOW MANAGEMENT =============

    def open_window(self):
        """Open the main plugin window"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title(f"{PLUGIN_INFO['icon']} {PLUGIN_INFO['name']} v{PLUGIN_INFO['version']}")
        self.window.geometry("1000x700")
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

        self._create_ui()

    def _on_close(self):
        """Handle window closing"""
        if self.is_processing:
            if messagebox.askyesno("Cancel", "Modeling in progress. Cancel and close?"):
                self.cancelled = True
                self.is_processing = False
                if self.progress:
                    self.progress.stop()
                time.sleep(0.1)
        if self.window:
            self.window.destroy()
            self.window = None

    # ============= UI CREATION =============

    def _create_ui(self):
        """Create compact user interface"""
        # Header
        header = tk.Frame(self.window, bg="#2c3e50", height=30)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header,
                text="⏳🔬 Chronological Dating v8.0",
                font=("Arial", 11, "bold"),
                bg="#2c3e50", fg="white").pack(pady=5)

        # Main container
        main_paned = tk.PanedWindow(self.window, orient=tk.HORIZONTAL, sashwidth=2)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        # Left panel
        left_panel = tk.Frame(main_paned, bg="#ecf0f1", relief=tk.RAISED, borderwidth=1)
        main_paned.add(left_panel, minsize=350)

        # Right panel
        right_panel = tk.Frame(main_paned, bg="white")
        main_paned.add(right_panel, minsize=600)

        self._setup_left_panel(left_panel)
        self._setup_right_panel(right_panel)

    def _setup_left_panel(self, parent):
        """Setup left panel with compact layout"""

        font_small = ("Arial", 8)
        font_tiny = ("Arial", 7)

        # ========== DATA SECTION ==========
        data_frame = tk.LabelFrame(parent, text="📊 Data", padx=4, pady=2,
                                   bg="#ecf0f1", font=font_small)
        data_frame.pack(fill=tk.X, padx=4, pady=2)

        self.data_info_label = tk.Label(data_frame, text="No data loaded",
                                       bg="#ecf0f1", font=font_tiny)
        self.data_info_label.pack(anchor=tk.W, pady=1)

        # Column selection
        col_frame = tk.Frame(data_frame, bg="#ecf0f1")
        col_frame.pack(fill=tk.X, pady=1)

        tk.Label(col_frame, text="Depth:", bg="#ecf0f1", font=font_tiny).grid(row=0, column=0, sticky=tk.W)
        self.depth_combo = ttk.Combobox(col_frame, textvariable=self.depth_var, width=15, font=font_tiny)
        self.depth_combo.grid(row=0, column=1, padx=2, sticky=tk.W)

        tk.Label(col_frame, text="Age:", bg="#ecf0f1", font=font_tiny).grid(row=1, column=0, sticky=tk.W)
        self.age_combo = ttk.Combobox(col_frame, textvariable=self.age_var, width=15, font=font_tiny)
        self.age_combo.grid(row=1, column=1, padx=2, sticky=tk.W)

        tk.Label(col_frame, text="Error:", bg="#ecf0f1", font=font_tiny).grid(row=2, column=0, sticky=tk.W)
        self.error_combo = ttk.Combobox(col_frame, textvariable=self.error_var, width=15, font=font_tiny)
        self.error_combo.grid(row=2, column=1, padx=2, sticky=tk.W)

        # Dating type
        type_frame = tk.Frame(data_frame, bg="#ecf0f1")
        type_frame.pack(fill=tk.X, pady=1)

        tk.Label(type_frame, text="Type:", bg="#ecf0f1", font=font_tiny).pack(side=tk.LEFT)
        dating_combo = ttk.Combobox(type_frame, textvariable=self.dating_type_var,
                                   values=list(self.DATING_TYPES.keys()), width=10, font=font_tiny)
        dating_combo.pack(side=tk.LEFT, padx=2)
        dating_combo.bind('<<ComboboxSelected>>', self._on_dating_type_change)

        # ========== CURVE MANAGEMENT ==========
        curve_frame = tk.LabelFrame(parent, text="🔬 Curves", padx=4, pady=2,
                                    bg="#ecf0f1", font=font_small)
        curve_frame.pack(fill=tk.X, padx=4, pady=2)

        # Selected curve
        sel_frame = tk.Frame(curve_frame, bg="#ecf0f1")
        sel_frame.pack(fill=tk.X, pady=1)

        tk.Label(sel_frame, text="Active:", bg="#ecf0f1", font=font_tiny).pack(side=tk.LEFT)
        self.curve_combo = ttk.Combobox(sel_frame, textvariable=self.curve_var,
                                       values=self.curves.get_available_curves(),
                                       width=15, font=font_tiny)
        self.curve_combo.pack(side=tk.LEFT, padx=2)

        self.load_curve_btn = tk.Button(sel_frame, text="⬇️", bg="#3498db", fg="white",
                                       font=font_tiny, width=2, command=self._load_selected_curve)
        self.load_curve_btn.pack(side=tk.LEFT, padx=1)

        # Add URL
        add_frame = tk.Frame(curve_frame, bg="#ecf0f1")
        add_frame.pack(fill=tk.X, pady=1)

        tk.Label(add_frame, text="Name:", bg="#ecf0f1", font=font_tiny).pack(side=tk.LEFT)
        self.new_curve_name = tk.Entry(add_frame, width=10, font=font_tiny)
        self.new_curve_name.pack(side=tk.LEFT, padx=1)

        url_frame = tk.Frame(curve_frame, bg="#ecf0f1")
        url_frame.pack(fill=tk.X, pady=1)
        tk.Label(url_frame, text="URL:", bg="#ecf0f1", font=font_tiny).pack(side=tk.LEFT)
        self.new_curve_url = tk.Entry(url_frame, width=25, font=font_tiny)
        self.new_curve_url.pack(side=tk.LEFT, padx=1)
        self.new_curve_url.insert(0, "https://")

        # Buttons
        btn_frame = tk.Frame(curve_frame, bg="#ecf0f1")
        btn_frame.pack(fill=tk.X, pady=1)

        self.add_curve_btn = tk.Button(btn_frame, text="➕", bg="#27ae60", fg="white",
                                      font=font_tiny, width=2, command=self._add_curve_url)
        self.add_curve_btn.pack(side=tk.LEFT, padx=1)

        self.file_curve_btn = tk.Button(btn_frame, text="📁", bg="#f39c12", fg="white",
                                       font=font_tiny, width=2, command=self._load_curve_file)
        self.file_curve_btn.pack(side=tk.LEFT, padx=1)

        self.remove_curve_btn = tk.Button(btn_frame, text="🗑️", bg="#e74c3c", fg="white",
                                         font=font_tiny, width=2, command=self._remove_curve)
        self.remove_curve_btn.pack(side=tk.LEFT, padx=1)

        # Reservoir correction
        res_frame = tk.Frame(curve_frame, bg="#ecf0f1")
        res_frame.pack(fill=tk.X, pady=1)

        tk.Label(res_frame, text="ΔR:", bg="#ecf0f1", font=font_tiny).pack(side=tk.LEFT)
        tk.Spinbox(res_frame, from_=-500, to=500, increment=10,
                  textvariable=self.deltaR_var, width=5, font=font_tiny).pack(side=tk.LEFT, padx=1)

        tk.Label(res_frame, text="±", bg="#ecf0f1", font=font_tiny).pack(side=tk.LEFT)
        tk.Spinbox(res_frame, from_=0, to=200, increment=10,
                  textvariable=self.deltaR_error_var, width=4, font=font_tiny).pack(side=tk.LEFT, padx=1)

        tk.Checkbutton(curve_frame, text="Auto", variable=self.auto_calibrate_var,
                      bg="#ecf0f1", font=font_tiny).pack(anchor=tk.W)

        # ========== BAYESIAN PRIORS ==========
        prior_frame = tk.LabelFrame(parent, text="🎯 Priors", padx=4, pady=2,
                                    bg="#ecf0f1", font=font_small)
        prior_frame.pack(fill=tk.X, padx=4, pady=2)

        # Acc rate
        acc_frame = tk.Frame(prior_frame, bg="#ecf0f1")
        acc_frame.pack(fill=tk.X, pady=1)
        tk.Label(acc_frame, text="Acc μ/σ:", bg="#ecf0f1", font=font_tiny).pack(side=tk.LEFT)
        tk.Spinbox(acc_frame, from_=0.1, to=1000, increment=10,
                  textvariable=self.acc_prior_mean, width=5, font=font_tiny).pack(side=tk.LEFT, padx=1)
        tk.Label(acc_frame, text="/", bg="#ecf0f1", font=font_tiny).pack(side=tk.LEFT)
        tk.Spinbox(acc_frame, from_=1, to=500, increment=5,
                  textvariable=self.acc_prior_std, width=4, font=font_tiny).pack(side=tk.LEFT, padx=1)

        # Memory
        mem_frame = tk.Frame(prior_frame, bg="#ecf0f1")
        mem_frame.pack(fill=tk.X, pady=1)
        tk.Label(mem_frame, text="Mem μ/σ:", bg="#ecf0f1", font=font_tiny).pack(side=tk.LEFT)
        tk.Spinbox(mem_frame, from_=0, to=1, increment=0.1,
                  textvariable=self.mem_prior_mean, width=4, font=font_tiny).pack(side=tk.LEFT, padx=1)
        tk.Label(mem_frame, text="/", bg="#ecf0f1", font=font_tiny).pack(side=tk.LEFT)
        tk.Spinbox(mem_frame, from_=0.01, to=0.5, increment=0.05,
                  textvariable=self.mem_prior_std, width=4, font=font_tiny).pack(side=tk.LEFT, padx=1)

        tk.Checkbutton(prior_frame, text="Use", variable=self.use_priors_var,
                      bg="#ecf0f1", font=font_tiny).pack(anchor=tk.W)

        # ========== MCMC SETTINGS ==========
        mcmc_frame = tk.LabelFrame(parent, text="🔄 MCMC", padx=4, pady=2,
                                   bg="#ecf0f1", font=font_small)
        mcmc_frame.pack(fill=tk.X, padx=4, pady=2)

        ws_frame = tk.Frame(mcmc_frame, bg="#ecf0f1")
        ws_frame.pack(fill=tk.X, pady=1)
        tk.Label(ws_frame, text="W:", bg="#ecf0f1", font=font_tiny).pack(side=tk.LEFT)
        tk.Spinbox(ws_frame, from_=4, to=128, increment=4,
                  textvariable=self.mcmc_walkers_var, width=4, font=font_tiny).pack(side=tk.LEFT, padx=1)
        tk.Label(ws_frame, text="S:", bg="#ecf0f1", font=font_tiny).pack(side=tk.LEFT, padx=2)
        tk.Spinbox(ws_frame, from_=500, to=10000, increment=500,
                  textvariable=self.mcmc_steps_var, width=5, font=font_tiny).pack(side=tk.LEFT, padx=1)
        tk.Label(ws_frame, text="B:", bg="#ecf0f1", font=font_tiny).pack(side=tk.LEFT, padx=2)
        tk.Spinbox(ws_frame, from_=100, to=2000, increment=100,
                  textvariable=self.mcmc_burn_var, width=4, font=font_tiny).pack(side=tk.LEFT, padx=1)

        # ========== PARALLEL ==========
        parallel_frame = tk.LabelFrame(parent, text="⚡ Parallel", padx=4, pady=2,
                                       bg="#ecf0f1", font=font_small)
        parallel_frame.pack(fill=tk.X, padx=4, pady=2)

        par_frame = tk.Frame(parallel_frame, bg="#ecf0f1")
        par_frame.pack(fill=tk.X, pady=1)
        tk.Label(par_frame, text="Threads:", bg="#ecf0f1", font=font_tiny).pack(side=tk.LEFT)
        parallel_combo = ttk.Combobox(par_frame, textvariable=self.parallel_var,
                                     values=list(self.PARALLEL_OPTIONS.keys()),
                                     width=4, font=font_tiny)
        parallel_combo.pack(side=tk.LEFT, padx=2)
        tk.Label(par_frame, text=f"({multiprocessing.cpu_count()})",
                bg="#ecf0f1", font=font_tiny).pack(side=tk.LEFT)

        # ========== MODEL SELECTION ==========
        model_frame = tk.LabelFrame(parent, text="🔄 Model", padx=4, pady=2,
                                    bg="#ecf0f1", font=font_small)
        model_frame.pack(fill=tk.X, padx=4, pady=2)

        model_row = tk.Frame(model_frame, bg="#ecf0f1")
        model_row.pack(fill=tk.X, pady=1)

        methods = ["Clam", "Linear", "Spline", "Poly", "Bayes"]
        for i, method in enumerate(methods):
            rb = tk.Radiobutton(model_row, text=method, variable=self.method_var,
                               value=method if method != "Bayes" else "Bayesian MCMC",
                               bg="#ecf0f1", font=font_tiny, indicatoron=0,
                               width=5, height=1, selectcolor="#3498db")
            rb.pack(side=tk.LEFT, padx=1)

        self.params_frame = tk.Frame(model_frame, bg="#ecf0f1", height=20)
        self.params_frame.pack(fill=tk.X, pady=1)
        self.params_frame.pack_propagate(False)
        self._update_method_params()

        # ========== OUTPUT ==========
        output_frame = tk.LabelFrame(parent, text="📐 Output", padx=4, pady=2,
                                     bg="#ecf0f1", font=font_small)
        output_frame.pack(fill=tk.X, padx=4, pady=2)

        out_row = tk.Frame(output_frame, bg="#ecf0f1")
        out_row.pack(fill=tk.X, pady=1)
        tk.Label(out_row, text="CI:", bg="#ecf0f1", font=font_tiny).pack(side=tk.LEFT)
        tk.Spinbox(out_row, from_=0.50, to=0.99, increment=0.01,
                  textvariable=self.confidence_var, width=4, font=font_tiny).pack(side=tk.LEFT, padx=2)
        tk.Checkbutton(out_row, text="Corner", variable=self.corner_plot_var,
                      bg="#ecf0f1", font=font_tiny).pack(side=tk.LEFT, padx=2)

        # ========== ACTION BUTTONS ==========
        action_frame = tk.Frame(parent, bg="#ecf0f1")
        action_frame.pack(fill=tk.X, padx=4, pady=2)

        buttons = [
            ("📥 Load", self._load_data, "#3498db"),
            ("▶ Run", self._start_modeling, "#9b59b6"),
            ("💾 Save", self._export_results, "#2ecc71"),
            ("🗑️ Cache", self._clear_cache, "#95a5a6"),
            ("⚡ All", self._load_all_curves_parallel, "#e67e22")
        ]

        for text, cmd, color in buttons:
            btn = tk.Button(action_frame, text=text, bg=color, fg="white",
                        font=font_tiny, command=cmd, padx=2, pady=0, height=1)
            btn.pack(side=tk.LEFT, padx=1)

            # Store reference to the Run button
            if text == "▶ Run":
                self.model_btn = btn

        # ========== STATUS ==========
        status_text = "Bayesian ready" if HAS_EMCEE else "Install emcee for Bayes"
        self.status_label = tk.Label(parent, text=status_text,
                                    bg="#ecf0f1", fg="#2c3e50" if HAS_EMCEE else "orange",
                                    font=font_tiny, anchor=tk.W)
        self.status_label.pack(fill=tk.X, padx=4, pady=(1, 0))

        self.progress = ttk.Progressbar(parent, mode='determinate', length=100)
        self.progress.pack(fill=tk.X, padx=4, pady=1)

    def _setup_right_panel(self, parent):
        """Setup right panel with smaller graphics"""
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        # Age-Depth tab
        age_depth_tab = tk.Frame(self.notebook)
        self.notebook.add(age_depth_tab, text="📈 Age-Depth")

        self.figure = plt.Figure(figsize=(5, 3.5), dpi=80)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, age_depth_tab)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2Tk(self.canvas, age_depth_tab)
        toolbar.update()

        # Calibration tab
        cal_tab = tk.Frame(self.notebook)
        self.notebook.add(cal_tab, text="🔬 Calibration")

        self.cal_figure = plt.Figure(figsize=(5, 2.5), dpi=80)
        self.cal_ax = self.cal_figure.add_subplot(111)
        self.cal_canvas = FigureCanvasTkAgg(self.cal_figure, cal_tab)
        self.cal_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # MCMC Diagnostics tab
        mcmc_tab = tk.Frame(self.notebook)
        self.notebook.add(mcmc_tab, text="📈 MCMC")

        self.mcmc_figure = plt.Figure(figsize=(5, 3.5), dpi=80)
        self.mcmc_ax1 = self.mcmc_figure.add_subplot(2, 2, 1)
        self.mcmc_ax2 = self.mcmc_figure.add_subplot(2, 2, 2)
        self.mcmc_ax3 = self.mcmc_figure.add_subplot(2, 2, 3)
        self.mcmc_ax4 = self.mcmc_figure.add_subplot(2, 2, 4)
        self.mcmc_canvas = FigureCanvasTkAgg(self.mcmc_figure, mcmc_tab)
        self.mcmc_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Corner plot tab
        corner_tab = tk.Frame(self.notebook)
        self.notebook.add(corner_tab, text="🎯 Corner")

        self.corner_figure = plt.Figure(figsize=(4, 4), dpi=80)
        self.corner_canvas = FigureCanvasTkAgg(self.corner_figure, corner_tab)
        self.corner_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Statistics tab
        stats_tab = tk.Frame(self.notebook)
        self.notebook.add(stats_tab, text="📋 Stats")

        self.stats_text = scrolledtext.ScrolledText(stats_tab, wrap=tk.WORD,
                                                   font=("Courier", 7), height=10)
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

    # ============= PARAMETER SETUP METHODS =============

    def _update_method_params(self):
        """Update parameters based on selected method"""
        method = self.method_var.get()
        for widget in self.params_frame.winfo_children():
            widget.destroy()

        if method == "Clam":
            self._setup_clam_params()
        elif method == "Linear":
            self._setup_linear_params()
        elif method == "Polynomial":
            self._setup_polynomial_params()
        elif method == "Bayesian MCMC":
            tk.Label(self.params_frame, text="(set in Priors)",
                    bg="#ecf0f1", font=("Arial", 7)).pack()

    def _setup_clam_params(self):
        """Setup Clam parameters"""
        tk.Label(self.params_frame, text="Smooth:", bg="#ecf0f1",
                font=("Arial", 7)).pack(side=tk.LEFT)
        tk.Spinbox(self.params_frame, from_=0.1, to=1.0, increment=0.05,
                  textvariable=self.clam_smooth_var, width=4,
                  font=("Arial", 7)).pack(side=tk.LEFT, padx=2)

    def _setup_linear_params(self):
        """Setup Linear parameters"""
        tk.Checkbutton(self.params_frame, text="Extrap",
                      variable=self.extrapolate_var, bg="#ecf0f1",
                      font=("Arial", 7)).pack(side=tk.LEFT)

    def _setup_polynomial_params(self):
        """Setup Polynomial parameters"""
        tk.Label(self.params_frame, text="Deg:", bg="#ecf0f1",
                font=("Arial", 7)).pack(side=tk.LEFT)
        tk.Spinbox(self.params_frame, from_=1, to=5,
                  textvariable=self.poly_degree_var,
                  width=2, font=("Arial", 7)).pack(side=tk.LEFT, padx=2)

    # ============= CURVE MANAGEMENT METHODS =============

    def _add_curve_url(self):
        """Add new curve URL to repository"""
        name = self.new_curve_name.get().strip()
        url = self.new_curve_url.get().strip()
        desc = self.new_curve_desc.get().strip() if hasattr(self, 'new_curve_desc') else ""

        if not name:
            messagebox.showerror("Error", "Curve name is required")
            return

        if not url or url == "https://":
            messagebox.showerror("Error", "Valid URL is required")
            return

        self.curves.add_curve_source(name, url, desc)

        # Clear inputs
        self.new_curve_name.delete(0, tk.END)
        self.new_curve_url.delete(0, tk.END)
        self.new_curve_url.insert(0, "https://")
        if hasattr(self, 'new_curve_desc'):
            self.new_curve_desc.delete(0, tk.END)

        # Update dropdown
        self._update_curve_dropdown()
        self.curve_var.set(name)

    def _remove_curve(self):
        """Remove curve from repository"""
        name = self.curve_var.get()
        if name:
            if messagebox.askyesno("Remove Curve", f"Remove '{name}' from repository?"):
                self.curves.remove_curve_source(name)
                self._update_curve_dropdown()
                if self.curve_combo['values']:
                    self.curve_var.set(self.curve_combo['values'][0])

    def _load_selected_curve(self):
        """Load selected curve"""
        name = self.curve_var.get()
        if not name:
            return

        self._update_status(f"Loading {name}...", "info")

        if name in self.curves.repository:
            url = self.curves.repository[name]['url']
            self.curves.load_from_url(name, url, force=True)
        else:
            self.curves.ensure_curve(name, force_download=True)

        self._update_curve_dropdown()

    def _load_curve_file(self):
        """Load curve from local file"""
        filename = filedialog.askopenfilename(
            title="Select Calibration Curve File",
            filetypes=[
                ("Curve files", "*.14c *.txt *.csv"),
                ("All files", "*.*")
            ]
        )

        if filename:
            name, data = self.curves.load_from_file(filename)
            if name:
                self._update_curve_dropdown()
                self.curve_var.set(name)

    def _load_all_curves_parallel(self):
        """Load all curves in parallel"""
        curves = self.curves.get_repository_curves()
        if not curves:
            messagebox.showinfo("No Curves", "No curves in repository")
            return

        curve_names = [name for name, _ in curves]

        self._update_status(f"⚡ Loading {len(curve_names)} curves...", "info")
        self.progress['value'] = 10

        def load_thread():
            try:
                results = self.curves.load_multiple_curves_parallel(curve_names, force=False)
                success = sum(1 for v in results.values() if v)
                self.window.after(0, lambda: self._update_status(
                    f"✅ Loaded {success}/{len(curve_names)} curves", "success"))
                self.window.after(0, self._update_curve_dropdown)
                self.window.after(0, lambda: self.progress.configure(value=0))
            except Exception as e:
                self.window.after(0, lambda: self._update_status(f"❌ Parallel load failed: {e}", "error"))

        thread = threading.Thread(target=load_thread, daemon=True)
        thread.start()

    def _clear_cache(self):
        """Clear cached curves"""
        if messagebox.askyesno("Clear Cache", "Delete all cached curve files?"):
            self.curves.clear_cache()
            self._update_curve_dropdown()

    def _update_curve_dropdown(self):
        """Update curve dropdown"""
        if self.curve_combo:
            self.curve_combo['values'] = self.curves.get_available_curves()

    def _on_dating_type_change(self, event=None):
        """Handle dating type change"""
        if self.dating_type_var.get() == "14C":
            self.auto_calibrate_var.set(True)
        else:
            self.auto_calibrate_var.set(False)

    # ============= DATA LOADING =============

    def _load_data(self):
        """Load data from main app - USING chemical_elements.json mappings"""
        if not hasattr(self.app, 'samples') or not self.app.samples:
            messagebox.showwarning("No Data", "Load data in main app first!")
            return

        try:
            # DEBUG: Print what we're getting
            print("="*50)
            print("LOADING DATA FROM MAIN APP")
            print(f"Number of samples: {len(self.app.samples)}")

            # Load the chemical elements mapping
            elements_map = {}
            if hasattr(self.app, 'chemical_tables'):
                # If app has chemical_tables attribute, use it
                elements_map = self.app.chemical_tables
                print(f"Chemical tables found: {list(elements_map.keys()) if elements_map else 'None'}")
            else:
                # Try to load from file
                try:
                    import json
                    with open('chemical_elements.json', 'r') as f:
                        elements_map = json.load(f)
                    print("Loaded chemical_elements.json")
                except:
                    print("Could not load chemical_elements.json")

            # Convert to DataFrame
            self.df = pd.DataFrame(self.app.samples)

            if self.df.empty:
                print("DataFrame is empty!")
                messagebox.showwarning("Empty Data", "No data found in samples")
                return

            print(f"DataFrame shape: {self.df.shape}")
            print(f"Columns: {list(self.df.columns)}")

            # Get all columns
            all_columns = list(self.df.columns)

            # Update UI
            self.data_info_label.config(
                text=f"📊 {len(self.df)} samples | {len(all_columns)} columns"
            )

            # Update comboboxes with ALL columns
            self.depth_combo['values'] = all_columns
            self.age_combo['values'] = all_columns
            self.error_combo['values'] = all_columns

            # AUTO-SELECT columns USING chemical_elements.json mappings
            depth_selected = False
            age_selected = False
            error_selected = False

            # Look for depth-related columns in the mappings
            depth_patterns = ['depth', 'Depth', 'sample depth', 'core depth']
            age_patterns = ['C14', '14C', 'radiocarbon', 'age', 'Age', 'BP', 'cal BP']
            error_patterns = ['error', 'Error', 'uncertainty', 'sigma', '±', 'C14_error']

            # Check each column against the mappings
            for col in all_columns:
                col_lower = col.lower()

                # Check if this column is in the elements map
                is_depth = False
                is_age = False
                is_error = False

                # Look through the elements map for matching patterns
                if elements_map and 'elements' in elements_map:
                    for elem_key, elem_info in elements_map['elements'].items():
                        # Check variations
                        variations = elem_info.get('variations', [])
                        for var in variations:
                            if var == col or var.lower() == col_lower:
                                # Found a match in the mapping
                                if 'depth' in elem_key.lower():
                                    is_depth = True
                                elif any(x in elem_key.lower() for x in ['c14', '14c', 'age', 'bp']):
                                    is_age = True
                                elif 'error' in elem_key.lower():
                                    is_error = True
                                break

                # Also check common patterns
                if not is_depth and any(x in col_lower for x in depth_patterns):
                    is_depth = True
                if not is_age and any(x in col_lower for x in age_patterns):
                    is_age = True
                if not is_error and any(x in col_lower for x in error_patterns):
                    is_error = True

                # Set the selections
                if is_depth and not depth_selected:
                    self.depth_var.set(col)
                    depth_selected = True
                    print(f"Found DEPTH column: {col}")

                if is_age and not age_selected:
                    self.age_var.set(col)
                    age_selected = True
                    print(f"Found AGE column: {col}")

                if is_error and not error_selected:
                    self.error_var.set(col)
                    error_selected = True
                    print(f"Found ERROR column: {col}")

            # If still not found, look for exact matches in the CSV
            if not depth_selected:
                for col in ['Depth_cm', 'depth_cm', 'Depth', 'depth']:
                    if col in all_columns:
                        self.depth_var.set(col)
                        depth_selected = True
                        print(f"Exact match DEPTH: {col}")
                        break

            if not age_selected:
                for col in ['C14_age_BP', 'C14_Age', 'radiocarbon_age', 'Age_BP']:
                    if col in all_columns:
                        self.age_var.set(col)
                        age_selected = True
                        print(f"Exact match AGE: {col}")
                        break

            if not error_selected:
                for col in ['C14_error', 'C14_Error', 'Age_error', 'error']:
                    if col in all_columns:
                        self.error_var.set(col)
                        error_selected = True
                        print(f"Exact match ERROR: {col}")
                        break

            # Last resort: use first three numeric-looking columns
            if not depth_selected or not age_selected:
                numeric_cols = []
                for col in all_columns[:10]:  # Check first 10 columns
                    try:
                        pd.to_numeric(self.df[col].iloc[0] if len(self.df) > 0 else '0', errors='raise')
                        numeric_cols.append(col)
                    except:
                        pass

                if not depth_selected and len(numeric_cols) > 0:
                    self.depth_var.set(numeric_cols[0])
                    print(f"Fallback DEPTH (first numeric): {numeric_cols[0]}")

                if not age_selected and len(numeric_cols) > 1:
                    self.age_var.set(numeric_cols[1])
                    print(f"Fallback AGE (second numeric): {numeric_cols[1]}")

                if not error_selected and len(numeric_cols) > 2:
                    self.error_var.set(numeric_cols[2])
                    print(f"Fallback ERROR (third numeric): {numeric_cols[2]}")

            # Show summary
            summary = f"✅ Loaded {len(self.df)} samples\n\n"
            summary += f"Selected columns:\n"
            summary += f"  Depth: {self.depth_var.get()}\n"
            summary += f"  Age: {self.age_var.get()}\n"
            summary += f"  Error: {self.error_var.get() or 'None (will use defaults)'}\n"

            self._update_status(f"✅ Loaded {len(self.df)} samples", "success")
            print(summary)

        except Exception as e:
            import traceback
            traceback.print_exc()
            self._update_status(f"❌ Load failed: {str(e)}", "error")
            messagebox.showerror("Load Error", f"Failed to load data:\n{str(e)}")

    def _detect_dating_columns(self):
        """Detect dating-specific columns from chemical tables or column mapping"""
        dating_columns = {
            'c14': [],
            'osl': [],
            'errors': []
        }

        # Check column mapping first
        if hasattr(self.app, 'column_mapping'):
            mapping = self.app.column_mapping
            for key, col in mapping.items():
                key_lower = key.lower()
                if 'c14' in key_lower or 'radiocarbon' in key_lower:
                    dating_columns['c14'].append(col)
                elif 'error' in key_lower or 'sigma' in key_lower:
                    dating_columns['errors'].append(col)

        # Check chemical tables
        if hasattr(self.app, 'chemical_tables'):
            for table_name, table_info in self.app.chemical_tables.items():
                if 'columns' in table_info:
                    for col in table_info['columns']:
                        col_lower = col.lower()
                        if 'c14' in col_lower or '14c' in col_lower:
                            dating_columns['c14'].append(col)
                        elif 'error' in col_lower and ('c14' in col_lower or 'age' in col_lower):
                            dating_columns['errors'].append(col)

        return dating_columns

    # ============= VALIDATION =============

    def _validate_inputs(self):
        """Validate inputs before modeling - HONEST version with clear messaging"""
        if self.df.empty:
            messagebox.showwarning("No Data", "No data loaded. Please load data first.")
            return "No data loaded"

        depth_col = self.depth_var.get()
        age_col = self.age_var.get()
        error_col = self.error_var.get()

        # Check if columns are selected
        if not depth_col or not age_col:
            messagebox.showinfo("Selection Required",
                            "Please select Depth and Age columns from the dropdown menus.\n\n"
                            "For age-depth modeling, you need:\n"
                            "• Depth column (must be strictly increasing)\n"
                            "• Age column (radiocarbon or other dates)\n"
                            "• Error column (analytical uncertainty)")
            return "Select depth and age columns"

        # Check if selected columns exist
        if depth_col not in self.df.columns:
            messagebox.showerror("Column Error",
                            f"Selected depth column '{depth_col}' not found in data.\n\n"
                            f"Available columns: {', '.join(list(self.df.columns)[:10])}...")
            return f"Column '{depth_col}' not found"

        if age_col not in self.df.columns:
            messagebox.showerror("Column Error",
                            f"Selected age column '{age_col}' not found in data.")
            return f"Column '{age_col}' not found"

        # Convert to numeric and check for valid data
        try:
            depths = pd.to_numeric(self.df[depth_col], errors='coerce')
            ages = pd.to_numeric(self.df[age_col], errors='coerce')
        except Exception as e:
            messagebox.showerror("Data Error",
                            f"Could not convert columns to numeric values.\n\nError: {str(e)}")
            return "Columns must contain numeric data"

        # Find samples with valid depth AND age
        valid_mask = ~(depths.isna() | ages.isna())
        valid_depths = depths[valid_mask].values
        valid_ages = ages[valid_mask].values
        valid_indices = np.where(valid_mask)[0]

        # Check if we have any valid samples
        if len(valid_depths) == 0:
            # Show which columns have issues
            depth_issues = depths.isna().sum()
            age_issues = ages.isna().sum()

            msg = "No samples have both valid depth AND age values.\n\n"
            msg += f"• Depth column '{depth_col}': {depth_issues} missing values\n"
            msg += f"• Age column '{age_col}': {age_issues} missing values\n\n"
            msg += "Please check your data or select different columns."

            messagebox.showwarning("No Valid Data", msg)
            return "No valid data points"

        # Check if we have enough samples (minimum 3 for any modeling)
        if len(valid_depths) < 3:
            msg = f"Insufficient data: Only {len(valid_depths)} samples with valid depth and age.\n\n"
            msg += "Age-depth modeling requires at least 3 dated samples.\n"
            msg += f"Found {len(valid_depths)} valid samples out of {len(self.df)} total."

            messagebox.showwarning("Insufficient Data", msg)
            return f"Need at least 3 valid data points, only have {len(valid_depths)}"

        # CRITICAL CHECK: Depths must be strictly increasing
        if not np.all(np.diff(valid_depths) > 0):
            # Find where the problem occurs
            bad_indices = np.where(np.diff(valid_depths) <= 0)[0]

            msg = "❌ DEPTHS ARE NOT STRICTLY INCREASING\n"
            msg += "="*50 + "\n\n"
            msg += "For valid age-depth modeling, depths must increase with each sample.\n"
            msg += f"Found {len(bad_indices)} issues in your data:\n\n"

            # Show first 5 problems
            for i, idx in enumerate(bad_indices[:5]):
                sample_idx = valid_indices[idx]
                sample_id = self.df.iloc[sample_idx].get('Sample_ID', f'Sample {sample_idx}')
                msg += f"{i+1}. {sample_id}: depth={valid_depths[idx]:.1f} → {valid_depths[idx+1]:.1f}\n"

            if len(bad_indices) > 5:
                msg += f"... and {len(bad_indices)-5} more issues\n"

            msg += "\nPlease check your stratigraphy - depths must increase downward in the core/section.\n"
            msg += "Samples may need to be reordered or checked for errors."

            messagebox.showerror("Invalid Depth Order", msg)
            return "Depths must be strictly increasing"

        # Check error column if selected
        if error_col:
            if error_col not in self.df.columns:
                msg = f"Selected error column '{error_col}' not found.\n\n"
                msg += "The plugin will use default errors (50 years) for all samples.\n"
                msg += "This may affect the uncertainty estimates."
                messagebox.showwarning("Error Column Missing", msg)
                # Don't return - this is just a warning
            else:
                errors = pd.to_numeric(self.df[error_col], errors='coerce')
                valid_errors = errors[valid_mask].values

                # Check if any errors are missing/zero
                missing_errors = np.isnan(valid_errors).sum()
                zero_errors = (valid_errors == 0).sum()

                if missing_errors > 0 or zero_errors > 0:
                    msg = "Issues with error column:\n"
                    if missing_errors > 0:
                        msg += f"• {missing_errors} samples have missing error values\n"
                    if zero_errors > 0:
                        msg += f"• {zero_errors} samples have zero error (will use default 50)\n"
                    messagebox.showwarning("Error Data Issues", msg)

        # Check calibration curve for 14C dates
        if self.dating_type_var.get() == "14C" and self.auto_calibrate_var.get():
            curve_name = self.curve_var.get()
            if not curve_name:
                messagebox.showinfo("Curve Required",
                                "Please select a calibration curve for radiocarbon dates.\n\n"
                                "Common curves:\n"
                                "• IntCal20 - Northern Hemisphere terrestrial\n"
                                "• SHCal20 - Southern Hemisphere terrestrial\n"
                                "• Marine20 - Marine samples")
                return "Select a calibration curve"

            # Check if curve is available
            try:
                if not self.curves.ensure_curve(curve_name):
                    msg = f"Calibration curve '{curve_name}' is not available.\n\n"
                    msg += "Please:\n"
                    msg += "1. Check your internet connection\n"
                    msg += "2. Click 'Load' to download the curve\n"
                    msg += "3. Or select a different curve"
                    messagebox.showerror("Curve Not Available", msg)
                    return f"Curve '{curve_name}' not available"
            except Exception as e:
                messagebox.showerror("Curve Error", f"Error loading curve:\n{str(e)}")
                return f"Curve error: {str(e)}"

        # All checks passed - show summary
        msg = f"✅ Data validation passed!\n\n"
        msg += f"• {len(valid_depths)} samples with valid depth and age\n"
        msg += f"• Depth range: {valid_depths.min():.1f} - {valid_depths.max():.1f} cm\n"
        msg += f"• Age range: {valid_ages.min():.0f} - {valid_ages.max():.0f} BP\n"

        if error_col and error_col in self.df.columns:
            msg += f"• Using error column: {error_col}\n"
        else:
            msg += f"• Using default errors (50 years)\n"

        if self.dating_type_var.get() == "14C" and self.auto_calibrate_var.get():
            msg += f"• Calibration curve: {curve_name}\n"

        messagebox.showinfo("Ready to Run", msg)

        return None  # All good!

    # ============= MODELING =============

    def _start_modeling(self):
        """Start enhanced modeling"""
        error = self._validate_inputs()
        if error:
            messagebox.showerror("Input Error", error)
            return

        # Check for Bayesian requirements
        if self.method_var.get() == "Bayesian MCMC" and not HAS_EMCEE:
            messagebox.showerror(
                "Missing Dependency",
                "Bayesian MCMC requires emcee and corner.\n\n"
                "Install with: pip install emcee corner"
            )
            return

        self.is_processing = True
        self.cancelled = False
        self.model_btn.config(state=tk.DISABLED, text="Running...")
        self.progress['value'] = 0
        self._update_status(f"Starting {self.method_var.get()}...", "info")
        self._start_time = time.time()

        thread = threading.Thread(target=self._run_enhanced_modeling, daemon=True)
        thread.start()

    def _run_enhanced_modeling(self):
        """Run the selected model - with proper validation and reporting"""
        try:
            # Get threads setting
            parallel_setting = self.parallel_var.get()
            n_threads = self.PARALLEL_OPTIONS.get(parallel_setting, 1)
            if isinstance(n_threads, str) and n_threads == "Max":
                n_threads = multiprocessing.cpu_count()

            # Get data with proper numeric conversion
            depth_col = self.depth_var.get()
            age_col = self.age_var.get()
            error_col = self.error_var.get() if self.error_var.get() in self.df.columns else None

            # Report on data loading
            total_samples = len(self.df)
            self._update_status(f"Processing {total_samples} total samples...", "info")

            # Convert to numeric safely
            depths = pd.to_numeric(self.df[depth_col], errors='coerce')
            ages = pd.to_numeric(self.df[age_col], errors='coerce')

            # Find valid samples (both depth and age are numeric)
            valid_mask = ~(depths.isna() | ages.isna())
            valid_count = valid_mask.sum()
            invalid_count = total_samples - valid_count

            if invalid_count > 0:
                self._update_status(f"⚠️ {invalid_count} samples have missing/invalid data and will be skipped", "warning")

                # List first few invalid samples for transparency
                invalid_samples = []
                for idx in range(total_samples):
                    if not valid_mask[idx]:
                        sample_id = self.df.iloc[idx].get('Sample_ID', f'Sample {idx}')
                        invalid_samples.append(sample_id)
                        if len(invalid_samples) >= 5:
                            break

                if invalid_samples:
                    print(f"Skipped samples: {', '.join(invalid_samples)}...")

            if valid_count == 0:
                self._update_status("❌ No valid samples with both depth and age", "error")
                messagebox.showerror("No Valid Data",
                                "No samples have both valid depth AND age values.\n\n"
                                "Please check your column selections and data.")
                return

            # Extract valid data
            depths = depths[valid_mask].values
            ages = ages[valid_mask].values

            # Handle errors
            if error_col:
                errors = pd.to_numeric(self.df[error_col], errors='coerce')
                errors = errors[valid_mask].values

                # Check for invalid errors
                missing_errors = np.isnan(errors).sum()
                zero_errors = (errors == 0).sum()

                if missing_errors > 0 or zero_errors > 0:
                    self._update_status(f"⚠️ Fixing {missing_errors + zero_errors} invalid error values", "warning")
                    errors = np.abs(errors)
                    errors[np.isnan(errors)] = 50
                    errors[errors < 1] = 50
            else:
                errors = np.ones_like(ages) * 50
                self._update_status(f"ℹ️ No error column - using default 50 years", "info")

            # Sort by depth (critical for age-depth modeling)
            sort_idx = np.argsort(depths)
            depths = depths[sort_idx]
            ages = ages[sort_idx]
            errors = errors[sort_idx]

            # Verify depths are strictly increasing
            if not np.all(np.diff(depths) > 0):
                # Find duplicate or out-of-order depths
                problem_indices = np.where(np.diff(depths) <= 0)[0]
                self._update_status(f"❌ Found {len(problem_indices)} depth ordering issues", "error")

                # Show the problems
                msg = "Depths are not strictly increasing!\n\n"
                msg += "This is required for age-depth modeling.\n"
                msg += f"Found issues at {len(problem_indices)} points:\n"
                for i, idx in enumerate(problem_indices[:5]):
                    msg += f"  Depth {depths[idx]:.1f} → {depths[idx+1]:.1f}\n"
                if len(problem_indices) > 5:
                    msg += f"  ... and {len(problem_indices)-5} more\n"
                msg += "\nPlease check your stratigraphy and reorder samples."

                messagebox.showerror("Depth Order Error", msg)
                return

            # Final data summary
            self._update_status(f"✅ Using {valid_count} samples with valid data", "success")
            print(f"Depth range: {depths.min():.1f} - {depths.max():.1f} cm")
            print(f"Age range: {ages.min():.0f} - {ages.max():.0f} BP")

            # Check minimum samples requirement
            if valid_count < 3:
                self._update_status(f"❌ Need at least 3 samples, only have {valid_count}", "error")
                messagebox.showerror("Insufficient Data",
                                f"Age-depth modeling requires at least 3 dated samples.\n"
                                f"Only {valid_count} valid samples found.")
                return

            # Calibrate 14C if needed
            if self.dating_type_var.get() == "14C" and self.auto_calibrate_var.get():
                self._update_progress(10, f"Calibrating {valid_count} dates...")
                calibrated_ages = []
                calibrated_errors = []
                self.calibration_results = []

                curve_name = self.curve_var.get()

                # Check if curve is available
                if not self.curves.ensure_curve(curve_name):
                    self._update_status(f"❌ Calibration curve '{curve_name}' not available", "error")
                    messagebox.showerror("Curve Error",
                                    f"Calibration curve '{curve_name}' is not available.\n\n"
                                    "Please load it first using the curve manager.")
                    return

                # Parallel calibration if many samples
                if valid_count > 10 and HAS_JOBLIB and n_threads > 1:
                    self._update_status(f"⚡ Using {n_threads} threads for parallel calibration", "info")

                    def _calibrate_one(args):
                        age, error = args
                        return self.curves.calibrate(
                            age, error, curve_name,
                            deltaR=self.deltaR_var.get(),
                            deltaR_error=self.deltaR_error_var.get()
                        )

                    results = Parallel(n_jobs=n_threads)(
                        delayed(_calibrate_one)((age, err))
                        for age, err in zip(ages, errors)
                    )

                    for i, result in enumerate(results):
                        if result:
                            calibrated_ages.append(result['median'])
                            calibrated_errors.append(result['std'])
                            self.calibration_results.append(result)
                        else:
                            self._update_status(f"⚠️ Calibration failed for sample {i+1}", "warning")
                else:
                    # Sequential
                    for i, (age, error) in enumerate(zip(ages, errors)):
                        self._update_progress(10 + int(20 * i / len(ages)), f"Calibrating sample {i+1}/{len(ages)}")
                        result = self.curves.calibrate(
                            age, error, curve_name,
                            deltaR=self.deltaR_var.get(),
                            deltaR_error=self.deltaR_error_var.get()
                        )
                        if result:
                            calibrated_ages.append(result['median'])
                            calibrated_errors.append(result['std'])
                            self.calibration_results.append(result)
                        else:
                            self._update_status(f"⚠️ Calibration failed for sample {i+1}", "warning")

                if len(calibrated_ages) == 0:
                    self._update_status("❌ No dates could be calibrated", "error")
                    messagebox.showerror("Calibration Error",
                                    "No radiocarbon dates could be calibrated.\n"
                                    "Please check your curve and date values.")
                    return

                if len(calibrated_ages) < valid_count:
                    self._update_status(f"⚠️ Calibrated {len(calibrated_ages)}/{valid_count} dates", "warning")

                ages = np.array(calibrated_ages)
                errors = np.array(calibrated_errors)
                valid_count = len(ages)

            if self.cancelled:
                return

            # Run selected model
            method = self.method_var.get()
            self._update_progress(30, f"Running {method} with {valid_count} dates...")

            try:
                if method == "Bayesian MCMC":
                    if not HAS_EMCEE:
                        raise ImportError("emcee not installed")

                    # Setup priors
                    prior_info = {}
                    if self.use_priors_var.get():
                        prior_info = {
                            'acc_rate_prior': (self.acc_prior_mean.get(), self.acc_prior_std.get()),
                            'memory_prior': (self.mem_prior_mean.get(), self.mem_prior_std.get())
                        }

                    # Initialize Bayesian model
                    self.bayesian_model = BayesianAgeDepthModel()

                    # Run MCMC
                    self._update_status(f"Running MCMC with {self.mcmc_walkers_var.get()} walkers...", "info")
                    samples = self.bayesian_model.run_mcmc(
                        depths, ages, errors,
                        n_walkers=self.mcmc_walkers_var.get(),
                        n_steps=self.mcmc_steps_var.get(),
                        n_burn=self.mcmc_burn_var.get(),
                        prior_info=prior_info,
                        threads=n_threads
                    )

                    # Predict
                    eval_depths = np.linspace(np.min(depths), np.max(depths), 100)
                    result = self.bayesian_model.predict(
                        eval_depths,
                        samples,
                        thin=self.DEFAULT_PARAMS["mcmc_thin"]
                    )

                    result['raw_depths'] = depths
                    result['raw_ages'] = ages
                    result['raw_errors'] = errors
                    result['method'] = 'Bayesian MCMC'
                    result['acceptance_rate'] = self.bayesian_model.acceptance

                    self.mcmc_samples = samples

                    if self.corner_plot_var.get() and HAS_EMCEE:
                        self._generate_corner_plot(samples)

                    self._generate_mcmc_diagnostics(self.bayesian_model.chain)

                elif method == "Clam":
                    smooth = self.clam_smooth_var.get()
                    self._update_status(f"Fitting Clam spline (smoothness={smooth})...", "info")
                    spline = UnivariateSpline(depths, ages, w=1/errors, s=len(depths)*smooth)
                    eval_depths = np.linspace(np.min(depths), np.max(depths), 100)

                    result = {
                        'depths': eval_depths,
                        'median': spline(eval_depths),
                        'lower_ci': spline(eval_depths) - 1.96 * np.nanmean(errors),
                        'upper_ci': spline(eval_depths) + 1.96 * np.nanmean(errors),
                        'raw_depths': depths,
                        'raw_ages': ages,
                        'raw_errors': errors,
                        'method': 'Clam'
                    }

                elif method == "Linear":
                    extrapolate = self.extrapolate_var.get()
                    fill = 'extrapolate' if extrapolate else np.nan
                    self._update_status(f"Fitting linear interpolation (extrapolate={extrapolate})...", "info")
                    interp = interp1d(depths, ages, kind='linear',
                                    bounds_error=False, fill_value=fill)
                    eval_depths = np.linspace(np.min(depths), np.max(depths), 100)

                    result = {
                        'depths': eval_depths,
                        'median': interp(eval_depths),
                        'lower_ci': interp(eval_depths) - 1.96 * np.nanmean(errors),
                        'upper_ci': interp(eval_depths) + 1.96 * np.nanmean(errors),
                        'raw_depths': depths,
                        'raw_ages': ages,
                        'raw_errors': errors,
                        'method': 'Linear'
                    }

                elif method == "Spline":
                    self._update_status("Fitting monotonic cubic spline...", "info")
                    spline = PchipInterpolator(depths, ages)
                    eval_depths = np.linspace(np.min(depths), np.max(depths), 100)

                    result = {
                        'depths': eval_depths,
                        'median': spline(eval_depths),
                        'lower_ci': spline(eval_depths) - 1.96 * np.nanmean(errors),
                        'upper_ci': spline(eval_depths) + 1.96 * np.nanmean(errors),
                        'raw_depths': depths,
                        'raw_ages': ages,
                        'raw_errors': errors,
                        'method': 'Spline'
                    }

                elif method == "Polynomial":
                    degree = self.poly_degree_var.get()
                    self._update_status(f"Fitting degree-{degree} polynomial...", "info")
                    coeffs = np.polyfit(depths, ages, degree, w=1/errors)
                    poly = np.poly1d(coeffs)
                    eval_depths = np.linspace(np.min(depths), np.max(depths), 100)

                    result = {
                        'depths': eval_depths,
                        'median': poly(eval_depths),
                        'lower_ci': poly(eval_depths) - 1.96 * np.nanmean(errors),
                        'upper_ci': poly(eval_depths) + 1.96 * np.nanmean(errors),
                        'raw_depths': depths,
                        'raw_ages': ages,
                        'raw_errors': errors,
                        'method': f'Polynomial (deg {degree})'
                    }

                # Calculate accumulation rates
                if result:
                    rates = np.gradient(result['median'], result['depths'])
                    rates = np.abs(rates)
                    result['acc_rates'] = rates

                    # Find change points
                    rate_changes = np.gradient(rates, result['depths'])
                    change_points = np.where(np.abs(rate_changes) > np.std(rate_changes) * 2)[0]
                    result['change_points'] = result['depths'][change_points] if len(change_points) > 0 else []

                if self.cancelled:
                    return

                self._update_progress(90, "Rendering results...")
                self.age_model = result
                self.window.after(0, lambda: self._update_results_ui(result))

            except Exception as e:
                self._update_status(f"❌ Modeling error: {str(e)}", "error")
                traceback.print_exc()
                messagebox.showerror("Modeling Error",
                                f"Error during {method} modeling:\n\n{str(e)}\n\n"
                                "Please check your data and parameters.")
                return

        except Exception as e:
            traceback.print_exc()
            if not self.cancelled:
                self._update_status(f"❌ Error: {str(e)}", "error")
                messagebox.showerror("Unexpected Error",
                                f"An unexpected error occurred:\n\n{str(e)}")
        finally:
            self.window.after(0, self._reset_processing_ui)

    def _update_progress(self, value, message):
        """Update progress bar"""
        if not self.cancelled and self.window:
            self.window.after(0, lambda: self.progress.configure(value=value))
            self.window.after(0, lambda: self._update_status(message, "info"))

    def _reset_processing_ui(self):
        """Reset UI after processing"""
        self.is_processing = False
        self.model_btn.config(state=tk.NORMAL, text="▶ Run")
        self.progress['value'] = 0

    def _generate_mcmc_diagnostics(self, chain):
        """Generate MCMC diagnostic plots"""
        if chain is None or not hasattr(self, 'mcmc_ax1'):
            return

        self.mcmc_ax1.clear()
        self.mcmc_ax2.clear()
        self.mcmc_ax3.clear()
        self.mcmc_ax4.clear()

        n_walkers, n_steps, n_dim = chain.shape

        for i in range(min(n_walkers, 10)):
            self.mcmc_ax1.plot(chain[i, :, 0], alpha=0.3, lw=0.5)
        self.mcmc_ax1.set_title('Acc Rate Trace', fontsize=8)
        self.mcmc_ax1.set_xlabel('Step', fontsize=7)
        self.mcmc_ax1.set_ylabel('Acc Rate', fontsize=7)

        for i in range(min(n_walkers, 10)):
            self.mcmc_ax2.plot(chain[i, :, 1], alpha=0.3, lw=0.5)
        self.mcmc_ax2.set_title('Memory Trace', fontsize=8)
        self.mcmc_ax2.set_xlabel('Step', fontsize=7)
        self.mcmc_ax2.set_ylabel('Memory', fontsize=7)

        samples = chain.reshape(-1, n_dim)
        self.mcmc_ax3.hist(samples[:, 0], bins=50, alpha=0.7, color='blue')
        self.mcmc_ax3.set_title('Acc Rate Distribution', fontsize=8)
        self.mcmc_ax3.set_xlabel('Acc Rate', fontsize=7)

        self.mcmc_ax4.hist(samples[:, 1], bins=50, alpha=0.7, color='green')
        self.mcmc_ax4.set_title('Memory Distribution', fontsize=8)
        self.mcmc_ax4.set_xlabel('Memory', fontsize=7)

        self.mcmc_figure.tight_layout()
        self.mcmc_canvas.draw()

    def _generate_corner_plot(self, samples):
        """Generate corner plot of parameters"""
        if not HAS_EMCEE or samples is None or not hasattr(self, 'corner_figure'):
            return

        self.corner_figure.clear()
        figure = corner.corner(
            samples,
            labels=['Acc Rate', 'Memory'],
            quantiles=[0.16, 0.5, 0.84],
            show_titles=True,
            title_kwargs={"fontsize": 9},
            fig=self.corner_figure
        )
        self.corner_canvas.draw()

    def _update_results_ui(self, result):
        """Update UI with results"""
        if result is None:
            return

        # Age-depth plot
        self.ax.clear()

        if 'lower_ci' in result and 'upper_ci' in result:
            self.ax.fill_betweenx(result['depths'],
                                 result['lower_ci'],
                                 result['upper_ci'],
                                 alpha=0.3, color='#3498db',
                                 label=f'{int(self.confidence_var.get()*100)}% CI')

        self.ax.plot(result['median'], result['depths'], 'b-', linewidth=2, label='Model')

        self.ax.errorbar(result['raw_ages'], result['raw_depths'],
                        xerr=result['raw_errors'] * 1.96,
                        fmt='o', color='#e74c3c', capsize=2, markersize=4,
                        label=f'Dates (n={len(result["raw_depths"])})')

        if 'change_points' in result and len(result['change_points']) > 0:
            for cp in result['change_points']:
                self.ax.axhline(y=cp, color='purple', linestyle='--', alpha=0.5, linewidth=0.5)

        self.ax.invert_yaxis()
        self.ax.set_xlabel('Age (cal BP)', fontsize=8)
        self.ax.set_ylabel(f'{self.depth_var.get()} (cm)', fontsize=8)
        self.ax.set_title(f'Model: {result["method"]}', fontsize=9)
        self.ax.legend(fontsize=6, loc='lower right')
        self.ax.grid(True, alpha=0.3)
        self.ax.tick_params(labelsize=7)

        self.figure.tight_layout()
        self.canvas.draw()

        # Calibration plot
        if self.calibration_results:
            self.cal_ax.clear()
            colors = plt.cm.Set1(np.linspace(0, 1, min(8, len(self.calibration_results))))

            for i, cal in enumerate(self.calibration_results[:8]):
                prob = cal['probability']
                if prob is not None:
                    self.cal_ax.plot(prob[:, 1], prob[:, 0],
                                   color=colors[i], alpha=0.7, linewidth=1,
                                   label=f'{cal["median"]:.0f}')

            self.cal_ax.set_xlabel('Probability', fontsize=8)
            self.cal_ax.set_ylabel('Cal age (cal BP)', fontsize=8)
            self.cal_ax.set_title('Calibration', fontsize=9)
            self.cal_ax.legend(fontsize=5, ncol=2)
            self.cal_ax.tick_params(labelsize=7)

            self.cal_figure.tight_layout()
            self.cal_canvas.draw()

        # Statistics
        stats = f"{'='*50}\n"
        stats += f"CHRONOLOGICAL DATING RESULTS\n"
        stats += f"{'='*50}\n\n"

        stats += f"Model: {result['method']}\n"
        stats += f"Dates: {len(result['raw_ages'])}\n"
        stats += f"Depth: {np.min(result['depths']):.1f}-{np.max(result['depths']):.1f} cm\n"
        stats += f"Age: {np.min(result['median']):.0f}-{np.max(result['median']):.0f} cal BP\n\n"

        if 'acc_rates' in result:
            stats += f"SEDIMENTATION RATES\n"
            stats += f"{'-'*30}\n"
            stats += f"  Mean: {np.nanmean(result['acc_rates']):.1f} yr/cm\n"
            stats += f"  Median: {np.nanmedian(result['acc_rates']):.1f} yr/cm\n"
            stats += f"  Range: {np.nanmin(result['acc_rates']):.1f}-{np.nanmax(result['acc_rates']):.1f}\n"

        if self.calibration_results:
            stats += f"\nCALIBRATION\n"
            stats += f"{'-'*30}\n"
            stats += f"  Curve: {self.curve_var.get()}\n"
            stats += f"  ΔR: {self.deltaR_var.get()}±{self.deltaR_error_var.get()}\n"

        elapsed = time.time() - self._start_time if self._start_time else 0
        stats += f"\nTime: {elapsed:.1f}s"

        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats)

        self._update_status(f"✅ Completed in {elapsed:.1f}s", "success")

    # ============= EXPORT =============

    def _export_results(self):
        """Export results"""
        if self.age_model is None:
            messagebox.showwarning("No Results", "Run model first!")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[
                ("CSV files", "*.csv"),
                ("PNG files", "*.png"),
                ("PDF files", "*.pdf"),
                ("NPZ files", "*.npz"),
            ]
        )

        if filename:
            try:
                if filename.endswith('.csv'):
                    # Export age-depth model
                    df = pd.DataFrame({
                        'Depth_cm': self.age_model['depths'],
                        'Age_median': self.age_model['median'],
                        'Age_lower': self.age_model['lower_ci'],
                        'Age_upper': self.age_model['upper_ci']
                    })
                    df.to_csv(filename, index=False)

                    # Export calibration if available
                    if self.calibration_results:
                        cal_filename = filename.replace('.csv', '_cal.csv')
                        cal_data = []
                        for i, cal in enumerate(self.calibration_results):
                            cal_data.append({
                                'Sample': i+1,
                                'Raw_age': cal['raw_age'],
                                'Raw_error': cal['raw_error'],
                                'Cal_median': cal['median'],
                                'Cal_mean': cal['mean'],
                                'HPD_min': cal['hpd_2sigma'][0],
                                'HPD_max': cal['hpd_2sigma'][1],
                            })
                        pd.DataFrame(cal_data).to_csv(cal_filename, index=False)

                    # Export MCMC samples
                    if self.mcmc_samples is not None:
                        np.savez(filename.replace('.csv', '_mcmc.npz'),
                                samples=self.mcmc_samples)

                elif filename.endswith('.npz') and self.mcmc_samples is not None:
                    np.savez(filename, samples=self.mcmc_samples)

                else:
                    self.figure.savefig(filename, dpi=150, bbox_inches='tight')

                self._update_status(f"✅ Exported", "success")

            except Exception as e:
                self._update_status(f"❌ Export failed: {str(e)}", "error")


# ============================================================================
# PLUGIN SETUP
# ============================================================================

def setup_plugin(main_app):
    """Plugin setup function"""
    plugin = EnhancedDatingIntegrationPlugin(main_app)
    return plugin
