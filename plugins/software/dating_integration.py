"""
Chronological Dating Integration Plugin
PRODUCTION v7.0 - USER-SUPPLIED CURVE URLS
No hardcoded URLs - users provide their own sources
"""

PLUGIN_INFO = {
    "category": "software",
    "id": "dating_integration",
    "name": "Chronological Dating",
    "description": "User-supplied calibration curves (IntCal, Marine, SHCal, custom)",
    "icon": "⏳",
    "version": "7.0",
    "requires": ["numpy", "scipy", "matplotlib", "pandas"],
    "author": "Sefy Levy & DeepSeek",
    "item": {
        "type": "plugin",
        "subtype": "chronology",
        "tags": ["intcal", "marine", "shcal", "calibration", "user-curves"],
        "compatibility": ["main_app_v2+"],
        "dependencies": ["numpy>=1.21.0", "scipy>=1.7.0", "matplotlib>=3.4.0", "pandas>=1.3.0"],
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
from scipy.stats import norm
import warnings
import os
import json
import urllib.request
import urllib.error
import ssl
from pathlib import Path

warnings.filterwarnings('ignore')

# ============================================================================
# PART 1: USER-SUPPLIED CURVE MANAGER - NO HARDCODED URLS
# ============================================================================

class CurveManager:
    """
    Manages calibration curves from USER-SUPPLIED URLs and files.
    No hardcoded URLs - users provide their own sources.
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
# PART 2: MAIN PLUGIN CLASS - USER-SUPPLIED URLS
# ============================================================================

class DatingIntegrationPlugin:
    def __init__(self, main_app):
        self.app = main_app
        self.window = None
        self.df = pd.DataFrame()
        self.is_processing = False
        self.cancelled = False
        self.progress = None
        self.age_model = None
        self.calibration_results = None
        self._start_time = None

        # Initialize curve manager (NO HARDCODED URLS)
        self.curves = CurveManager()
        self.curves.set_status_callback(self._update_status)

        # Example repository entries (user can delete/modify)
        self._init_example_repository()

        # Modeling methods
        self.MODELING_METHODS = {
            "Clam": "Smoothing spline (Blaauw 2010) - RECOMMENDED",
            "Linear": "Linear interpolation",
            "Spline": "Monotonic cubic spline",
            "Polynomial": "Polynomial regression"
        }

        # Dating types
        self.DATING_TYPES = {
            "14C": "Radiocarbon - requires calibration curve",
            "OSL": "Optically Stimulated Luminescence",
            "U-Th": "Uranium-Thorium",
            "210Pb": "Lead-210",
            "Tephra": "Volcanic ash (known age)",
            "Varve": "Annual layer counting",
            "Custom": "User-provided ages"
        }

        # Default parameters
        self.DEFAULT_PARAMS = {
            "clam_smooth": 0.3,
            "poly_degree": 3,
            "confidence_level": 0.95
        }

    def _init_example_repository(self):
        """Initialize with EXAMPLE URLs - user must verify"""
        examples = {
            'IntCal20 (example)': {
                'url': 'https://intcal.org/curves/intcal20.14c',
                'description': 'Northern Hemisphere - verify URL works',
                'year': 2020,
                'type': 'example'
            },
            'Marine20 (example)': {
                'url': 'https://intcal.org/curves/marine20.14c',
                'description': 'Marine - verify URL works',
                'year': 2020,
                'type': 'example'
            },
            'SHCal20 (example)': {
                'url': 'https://intcal.org/curves/shcal20.14c',
                'description': 'Southern Hemisphere - verify URL works',
                'year': 2020,
                'type': 'example'
            }
        }

        for name, info in examples.items():
            if name not in self.curves.repository:
                self.curves.add_curve_source(name, info['url'], info['description'], info['year'], info['type'])

    def _update_status(self, message, level="info"):
        """Update status label with color coding"""
        colors = {
            "info": "#2c3e50",
            "success": "green",
            "warning": "orange",
            "error": "red"
        }
        color = colors.get(level, "#2c3e50")

        if hasattr(self, 'status_label'):
            self.status_label.config(text=message, fg=color)

    # ============= WINDOW MANAGEMENT =============

    def open_window(self):
        """Open the main plugin window"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title(f"{PLUGIN_INFO['icon']} {PLUGIN_INFO['name']} v{PLUGIN_INFO['version']}")
        self.window.geometry("1200x800")
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

    # ============= UI CREATION =============

    def _create_ui(self):
        """Create the user interface"""
        # Header
        header = tk.Frame(self.window, bg="#2c3e50")
        header.pack(fill=tk.X)

        tk.Label(header,
                text="⏳ User-Supplied Calibration Curves - YOU provide the URLs",
                font=("Arial", 14, "bold"),
                bg="#2c3e50", fg="white", pady=10).pack()

        # Main container
        main_paned = tk.PanedWindow(self.window, orient=tk.HORIZONTAL, sashwidth=6)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)

        # Left panel
        left_panel = tk.Frame(main_paned, bg="#ecf0f1", relief=tk.RAISED, borderwidth=1)
        main_paned.add(left_panel, minsize=400)

        # Right panel
        right_panel = tk.Frame(main_paned, bg="white")
        main_paned.add(right_panel, minsize=750)

        self._setup_left_panel(left_panel)
        self._setup_right_panel(right_panel)

    def _setup_left_panel(self, parent):
        """Setup left control panel"""
        # ========== DATA SECTION ==========
        data_frame = tk.LabelFrame(parent, text="📊 Dating Data", padx=8, pady=8, bg="#ecf0f1")
        data_frame.pack(fill=tk.X, padx=8, pady=8)

        self.data_info_label = tk.Label(data_frame, text="No data loaded",
                                       bg="#ecf0f1", font=("Arial", 9))
        self.data_info_label.pack(anchor=tk.W)

        # Column selection
        col_frame = tk.Frame(data_frame, bg="#ecf0f1")
        col_frame.pack(fill=tk.X, pady=5)

        tk.Label(col_frame, text="Depth:", bg="#ecf0f1", font=("Arial", 9)).grid(row=0, column=0, sticky=tk.W, pady=2)
        self.depth_var = tk.StringVar()
        self.depth_combo = ttk.Combobox(col_frame, textvariable=self.depth_var, width=18, font=("Arial", 9))
        self.depth_combo.grid(row=0, column=1, padx=3, pady=2)

        tk.Label(col_frame, text="Age/14C:", bg="#ecf0f1", font=("Arial", 9)).grid(row=1, column=0, sticky=tk.W, pady=2)
        self.age_var = tk.StringVar()
        self.age_combo = ttk.Combobox(col_frame, textvariable=self.age_var, width=18, font=("Arial", 9))
        self.age_combo.grid(row=1, column=1, padx=3, pady=2)

        tk.Label(col_frame, text="Error:", bg="#ecf0f1", font=("Arial", 9)).grid(row=2, column=0, sticky=tk.W, pady=2)
        self.error_var = tk.StringVar()
        self.error_combo = ttk.Combobox(col_frame, textvariable=self.error_var, width=18, font=("Arial", 9))
        self.error_combo.grid(row=2, column=1, padx=3, pady=2)

        # Dating type
        type_frame = tk.Frame(data_frame, bg="#ecf0f1")
        type_frame.pack(fill=tk.X, pady=2)

        tk.Label(type_frame, text="Type:", bg="#ecf0f1", font=("Arial", 9)).pack(side=tk.LEFT)
        self.dating_type_var = tk.StringVar(value="14C")
        dating_combo = ttk.Combobox(type_frame, textvariable=self.dating_type_var,
                                   values=list(self.DATING_TYPES.keys()), width=15, font=("Arial", 9))
        dating_combo.pack(side=tk.LEFT, padx=5)
        dating_combo.bind('<<ComboboxSelected>>', self._on_dating_type_change)

        # ========== CURVE MANAGEMENT SECTION ==========
        curve_frame = tk.LabelFrame(parent, text="🔬 Calibration Curves - YOU SUPPLY URLS", padx=8, pady=8, bg="#ecf0f1")
        curve_frame.pack(fill=tk.X, padx=8, pady=8)

        # Selected curve
        sel_frame = tk.Frame(curve_frame, bg="#ecf0f1")
        sel_frame.pack(fill=tk.X, pady=2)

        tk.Label(sel_frame, text="Active curve:", bg="#ecf0f1", font=("Arial", 9)).pack(side=tk.LEFT)
        self.curve_var = tk.StringVar()
        self.curve_combo = ttk.Combobox(sel_frame, textvariable=self.curve_var,
                                       values=self.curves.get_available_curves(),
                                       width=20, font=("Arial", 9))
        self.curve_combo.pack(side=tk.LEFT, padx=5)

        # Load button
        self.load_curve_btn = tk.Button(sel_frame, text="⬇️ Load", bg="#3498db", fg="white",
                                       font=("Arial", 8), command=self._load_selected_curve)
        self.load_curve_btn.pack(side=tk.LEFT, padx=2)

        # ========== ADD NEW CURVE URL ==========
        add_frame = tk.LabelFrame(curve_frame, text="Add Curve URL", padx=5, pady=5, bg="#ecf0f1")
        add_frame.pack(fill=tk.X, pady=5)

        # Name
        name_frame = tk.Frame(add_frame, bg="#ecf0f1")
        name_frame.pack(fill=tk.X, pady=2)
        tk.Label(name_frame, text="Name:", bg="#ecf0f1", font=("Arial", 8)).pack(side=tk.LEFT)
        self.new_curve_name = tk.Entry(name_frame, width=20, font=("Arial", 8))
        self.new_curve_name.pack(side=tk.LEFT, padx=5)

        # URL
        url_frame = tk.Frame(add_frame, bg="#ecf0f1")
        url_frame.pack(fill=tk.X, pady=2)
        tk.Label(url_frame, text="URL:", bg="#ecf0f1", font=("Arial", 8)).pack(side=tk.LEFT)
        self.new_curve_url = tk.Entry(url_frame, width=35, font=("Arial", 8))
        self.new_curve_url.pack(side=tk.LEFT, padx=5)
        self.new_curve_url.insert(0, "https://")

        # Description
        desc_frame = tk.Frame(add_frame, bg="#ecf0f1")
        desc_frame.pack(fill=tk.X, pady=2)
        tk.Label(desc_frame, text="Desc:", bg="#ecf0f1", font=("Arial", 8)).pack(side=tk.LEFT)
        self.new_curve_desc = tk.Entry(desc_frame, width=30, font=("Arial", 8))
        self.new_curve_desc.pack(side=tk.LEFT, padx=5)

        # Buttons
        btn_frame = tk.Frame(add_frame, bg="#ecf0f1")
        btn_frame.pack(fill=tk.X, pady=5)

        self.add_curve_btn = tk.Button(btn_frame, text="➕ Add URL", bg="#27ae60", fg="white",
                                      font=("Arial", 8), command=self._add_curve_url)
        self.add_curve_btn.pack(side=tk.LEFT, padx=2)

        self.file_curve_btn = tk.Button(btn_frame, text="📁 Load File", bg="#f39c12", fg="white",
                                       font=("Arial", 8), command=self._load_curve_file)
        self.file_curve_btn.pack(side=tk.LEFT, padx=2)

        self.remove_curve_btn = tk.Button(btn_frame, text="🗑️ Remove", bg="#e74c3c", fg="white",
                                         font=("Arial", 8), command=self._remove_curve)
        self.remove_curve_btn.pack(side=tk.LEFT, padx=2)

        # Reservoir correction
        reservoir_frame = tk.Frame(curve_frame, bg="#ecf0f1")
        reservoir_frame.pack(fill=tk.X, pady=5)

        tk.Label(reservoir_frame, text="ΔR:", bg="#ecf0f1", font=("Arial", 9)).pack(side=tk.LEFT)
        self.deltaR_var = tk.DoubleVar(value=0)
        tk.Spinbox(reservoir_frame, from_=-500, to=500, increment=10,
                  textvariable=self.deltaR_var, width=8, font=("Arial", 9)).pack(side=tk.LEFT, padx=2)

        tk.Label(reservoir_frame, text="±", bg="#ecf0f1", font=("Arial", 9)).pack(side=tk.LEFT)
        self.deltaR_error_var = tk.DoubleVar(value=0)
        tk.Spinbox(reservoir_frame, from_=0, to=200, increment=10,
                  textvariable=self.deltaR_error_var, width=8, font=("Arial", 9)).pack(side=tk.LEFT, padx=2)

        self.auto_calibrate_var = tk.BooleanVar(value=True)
        tk.Checkbutton(curve_frame, text="Auto-calibrate 14C",
                      variable=self.auto_calibrate_var, bg="#ecf0f1", font=("Arial", 9)
                      ).pack(anchor=tk.W, pady=2)

        # ========== MODELING SECTION ==========
        model_frame = tk.LabelFrame(parent, text="🔄 Age-Depth Model", padx=8, pady=8, bg="#ecf0f1")
        model_frame.pack(fill=tk.X, padx=8, pady=8)

        self.method_var = tk.StringVar(value="Clam")
        for method in self.MODELING_METHODS.keys():
            tk.Radiobutton(model_frame, text=method, variable=self.method_var,
                          value=method, bg="#ecf0f1", font=("Arial", 9),
                          command=self._update_method_params).pack(anchor=tk.W, pady=1)

        # Parameters
        self.params_frame = tk.Frame(model_frame, bg="#ecf0f1")
        self.params_frame.pack(fill=tk.X, pady=5)
        self._setup_clam_params()

        # ========== OUTPUT SECTION ==========
        output_frame = tk.LabelFrame(parent, text="📐 Output", padx=8, pady=8, bg="#ecf0f1")
        output_frame.pack(fill=tk.X, padx=8, pady=8)

        conf_frame = tk.Frame(output_frame, bg="#ecf0f1")
        conf_frame.pack(fill=tk.X)

        tk.Label(conf_frame, text="Confidence:", bg="#ecf0f1", font=("Arial", 9)).pack(side=tk.LEFT)
        self.confidence_var = tk.DoubleVar(value=0.95)
        tk.Spinbox(conf_frame, from_=0.50, to=0.99, increment=0.01,
                  textvariable=self.confidence_var, width=8, font=("Arial", 9)).pack(side=tk.LEFT, padx=5)

        # ========== ACTION BUTTONS ==========
        action_frame = tk.Frame(parent, bg="#ecf0f1", pady=8)
        action_frame.pack(fill=tk.X, padx=8)

        self.load_btn = tk.Button(action_frame, text="📥 Load Data", bg="#3498db", fg="white",
                                 width=12, font=("Arial", 9), command=self._load_data)
        self.load_btn.pack(side=tk.LEFT, padx=2)

        self.model_btn = tk.Button(action_frame, text="⏳ Run Model", bg="#9b59b6", fg="white",
                                  width=12, font=("Arial", 9), command=self._start_modeling)
        self.model_btn.pack(side=tk.LEFT, padx=2)

        self.export_btn = tk.Button(action_frame, text="💾 Export", bg="#2ecc71", fg="white",
                                   width=10, font=("Arial", 9), command=self._export_results)
        self.export_btn.pack(side=tk.LEFT, padx=2)

        self.cache_btn = tk.Button(action_frame, text="🧹 Clear Cache", bg="#95a5a6", fg="white",
                                  width=12, font=("Arial", 9), command=self._clear_cache)
        self.cache_btn.pack(side=tk.LEFT, padx=2)

        # ========== STATUS ==========
        self.status_label = tk.Label(parent, text="Ready - Add your curve URLs", bg="#ecf0f1",
                                    fg="#2c3e50", font=("Arial", 9), wraplength=380)
        self.status_label.pack(fill=tk.X, padx=8, pady=(8, 3))

        self.progress = ttk.Progressbar(parent, mode='determinate', length=100)
        self.progress.pack(fill=tk.X, padx=8, pady=3)

    def _setup_right_panel(self, parent):
        """Setup results panel"""
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)

        # Age-Depth tab
        age_depth_tab = tk.Frame(self.notebook)
        self.notebook.add(age_depth_tab, text="📈 Age-Depth Model")

        self.figure = plt.Figure(figsize=(8, 5), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, age_depth_tab)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2Tk(self.canvas, age_depth_tab)
        toolbar.update()

        # Calibration tab
        cal_tab = tk.Frame(self.notebook)
        self.notebook.add(cal_tab, text="🔬 Calibration")

        self.cal_figure = plt.Figure(figsize=(8, 4), dpi=100)
        self.cal_ax = self.cal_figure.add_subplot(111)
        self.cal_canvas = FigureCanvasTkAgg(self.cal_figure, cal_tab)
        self.cal_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Statistics tab
        stats_tab = tk.Frame(self.notebook)
        self.notebook.add(stats_tab, text="📋 Statistics")

        self.stats_text = scrolledtext.ScrolledText(stats_tab, wrap=tk.WORD,
                                                   font=("Courier", 9), height=15)
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)

    # ============= PARAMETER SETUP =============

    def _setup_clam_params(self):
        """Setup Clam parameters"""
        for widget in self.params_frame.winfo_children():
            widget.destroy()

        tk.Label(self.params_frame, text="Smoothing:", bg="#ecf0f1", font=("Arial", 9)).pack(side=tk.LEFT)
        self.clam_smooth_var = tk.DoubleVar(value=self.DEFAULT_PARAMS["clam_smooth"])
        tk.Spinbox(self.params_frame, from_=0.1, to=1.0, increment=0.05,
                  textvariable=self.clam_smooth_var, width=8, font=("Arial", 9)).pack(side=tk.LEFT, padx=5)

    def _setup_linear_params(self):
        """Setup Linear parameters"""
        for widget in self.params_frame.winfo_children():
            widget.destroy()

        self.extrapolate_var = tk.BooleanVar(value=False)
        tk.Checkbutton(self.params_frame, text="Allow extrapolation",
                      variable=self.extrapolate_var, bg="#ecf0f1", font=("Arial", 9)).pack(side=tk.LEFT)

    def _setup_polynomial_params(self):
        """Setup Polynomial parameters"""
        for widget in self.params_frame.winfo_children():
            widget.destroy()

        tk.Label(self.params_frame, text="Degree:", bg="#ecf0f1", font=("Arial", 9)).pack(side=tk.LEFT)
        self.poly_degree_var = tk.IntVar(value=self.DEFAULT_PARAMS["poly_degree"])
        tk.Spinbox(self.params_frame, from_=1, to=5, textvariable=self.poly_degree_var,
                  width=5, font=("Arial", 9)).pack(side=tk.LEFT, padx=5)

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

    def _on_dating_type_change(self, event=None):
        """Handle dating type change"""
        if self.dating_type_var.get() == "14C":
            self.auto_calibrate_var.set(True)
            self._update_status("14C selected - provide calibration curve URL", "info")
        else:
            self.auto_calibrate_var.set(False)
            self._update_status(f"{self.dating_type_var.get()} selected - no calibration", "info")

    # ============= CURVE MANAGEMENT =============

    def _add_curve_url(self):
        """Add new curve URL to repository"""
        name = self.new_curve_name.get().strip()
        url = self.new_curve_url.get().strip()
        desc = self.new_curve_desc.get().strip()

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
        self.new_curve_desc.delete(0, tk.END)

        # Update dropdown
        self.curve_combo['values'] = self.curves.get_available_curves()
        self.curve_var.set(name)

    def _remove_curve(self):
        """Remove curve from repository"""
        name = self.curve_var.get()
        if name:
            if messagebox.askyesno("Remove Curve", f"Remove '{name}' from repository?"):
                self.curves.remove_curve_source(name)
                self.curve_combo['values'] = self.curves.get_available_curves()
                if self.curve_combo['values']:
                    self.curve_var.set(self.curve_combo['values'][0])

    def _load_selected_curve(self):
        """Load selected curve"""
        name = self.curve_var.get()
        if not name:
            return

        self._update_status(f"Loading {name}...", "info")

        # Check if in repository
        if name in self.curves.repository:
            url = self.curves.repository[name]['url']
            self.curves.load_from_url(name, url, force=True)
        else:
            # Try to load from cache
            self.curves.ensure_curve(name, force_download=True)

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
                # Update dropdown
                self.curve_combo['values'] = self.curves.get_available_curves()
                self.curve_var.set(name)

    def _clear_cache(self):
        """Clear cached curves"""
        if messagebox.askyesno("Clear Cache", "Delete all cached curve files?"):
            self.curves.clear_cache()
            self.curve_combo['values'] = self.curves.get_available_curves()

    def _update_curve_dropdown(self):
        """Update curve dropdown"""
        self.curve_combo['values'] = self.curves.get_available_curves()

    # ============= DATA LOADING =============

    def _load_data(self):
        """Load data from main app"""
        if not hasattr(self.app, 'samples') or not self.app.samples:
            messagebox.showwarning("No Data", "Load data in main app first!")
            return

        try:
            self.df = pd.DataFrame(self.app.samples)

            # Convert to numeric
            numeric_cols = []
            for col in self.df.columns:
                try:
                    self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
                    if not self.df[col].isna().all():
                        numeric_cols.append(col)
                except:
                    pass

            # Update UI
            self.data_info_label.config(text=f"📊 {len(self.df)} dating samples")
            self.depth_combo['values'] = numeric_cols
            self.age_combo['values'] = numeric_cols
            self.error_combo['values'] = numeric_cols

            # Auto-select
            for col in numeric_cols:
                col_lower = col.lower()
                if 'depth' in col_lower:
                    self.depth_var.set(col)
                if any(x in col_lower for x in ['age', 'c14', '14c', 'bp']):
                    self.age_var.set(col)
                if any(x in col_lower for x in ['error', 'sigma', 'std', '±']):
                    self.error_var.set(col)

            self._update_status(f"✅ Loaded {len(self.df)} samples", "success")

        except Exception as e:
            self._update_status(f"❌ Load failed: {str(e)}", "error")

    # ============= VALIDATION =============

    def _validate_inputs(self):
        """Validate inputs before modeling"""
        if self.df.empty:
            return "No data loaded"

        depth_col = self.depth_var.get()
        age_col = self.age_var.get()

        if not depth_col or not age_col:
            return "Select depth and age columns"

        if depth_col not in self.df.columns:
            return f"Column '{depth_col}' not found"
        if age_col not in self.df.columns:
            return f"Column '{age_col}' not found"

        depths = self.df[depth_col].dropna().values
        ages = self.df[age_col].dropna().values

        if len(depths) < 3:
            return "Need at least 3 data points"

        if not np.all(np.diff(depths) > 0):
            return "Depths must be strictly increasing"

        # Check curve for 14C
        if self.dating_type_var.get() == "14C" and self.auto_calibrate_var.get():
            curve_name = self.curve_var.get()
            if not curve_name:
                return "Select a calibration curve"

            if not self.curves.ensure_curve(curve_name):
                return f"Curve '{curve_name}' not available. Load it first."

        return None

    # ============= MODELING =============

    def _start_modeling(self):
        """Start modeling in thread"""
        error = self._validate_inputs()
        if error:
            messagebox.showerror("Input Error", error)
            return

        self.is_processing = True
        self.cancelled = False
        self.model_btn.config(state=tk.DISABLED, text="Running...")
        self.progress['value'] = 0
        self._update_status("Starting age-depth modeling...", "info")
        self._start_time = time.time()

        thread = threading.Thread(target=self._run_modeling, daemon=True)
        thread.start()

    def _run_modeling(self):
        """Run the selected model"""
        try:
            # Get data
            depth_col = self.depth_var.get()
            age_col = self.age_var.get()
            error_col = self.error_var.get() if self.error_var.get() in self.df.columns else None

            depths = self.df[depth_col].dropna().values
            ages = self.df[age_col].dropna().values

            if error_col:
                errors = self.df[error_col].dropna().values
                errors = np.abs(errors)
                errors[errors < 1] = 50
            else:
                errors = np.ones_like(ages) * 50

            # Sort by depth
            sort_idx = np.argsort(depths)
            depths = depths[sort_idx]
            ages = ages[sort_idx]
            errors = errors[sort_idx]

            # Calibrate 14C if needed
            if self.dating_type_var.get() == "14C" and self.auto_calibrate_var.get():
                self._update_progress(10, "Calibrating 14C dates...")
                calibrated_ages = []
                calibrated_errors = []
                self.calibration_results = []

                curve_name = self.curve_var.get()

                for age, error in zip(ages, errors):
                    result = self.curves.calibrate(
                        age, error, curve_name,
                        deltaR=self.deltaR_var.get(),
                        deltaR_error=self.deltaR_error_var.get()
                    )
                    if result:
                        calibrated_ages.append(result['median'])
                        calibrated_errors.append(result['std'])
                        self.calibration_results.append(result)

                ages = np.array(calibrated_ages)
                errors = np.array(calibrated_errors)

            if self.cancelled:
                return

            # Run model
            method = self.method_var.get()
            self._update_progress(30, f"Running {method}...")

            if method == "Clam":
                smooth = self.clam_smooth_var.get()
                spline = UnivariateSpline(depths, ages, w=1/errors, s=len(depths)*smooth)
                eval_depths = np.linspace(np.min(depths), np.max(depths), 100)

                self.age_model = {
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
                extrapolate = getattr(self, 'extrapolate_var', tk.BooleanVar(value=False)).get()
                fill = 'extrapolate' if extrapolate else np.nan
                interp = interp1d(depths, ages, kind='linear',
                                bounds_error=False, fill_value=fill)
                eval_depths = np.linspace(np.min(depths), np.max(depths), 100)

                self.age_model = {
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
                spline = PchipInterpolator(depths, ages)
                eval_depths = np.linspace(np.min(depths), np.max(depths), 100)

                self.age_model = {
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
                coeffs = np.polyfit(depths, ages, degree, w=1/errors)
                poly = np.poly1d(coeffs)
                eval_depths = np.linspace(np.min(depths), np.max(depths), 100)

                self.age_model = {
                    'depths': eval_depths,
                    'median': poly(eval_depths),
                    'lower_ci': poly(eval_depths) - 1.96 * np.nanmean(errors),
                    'upper_ci': poly(eval_depths) + 1.96 * np.nanmean(errors),
                    'raw_depths': depths,
                    'raw_ages': ages,
                    'raw_errors': errors,
                    'method': f'Polynomial (deg {degree})'
                }

            # Add accumulation rates
            if self.age_model:
                rates = np.gradient(self.age_model['median'], self.age_model['depths'])
                rates = np.abs(rates)
                self.age_model['acc_rates'] = rates

            if self.cancelled:
                return

            self._update_progress(90, "Rendering plots...")
            self.window.after(0, lambda: self._update_results_ui(self.age_model))

        except Exception as e:
            import traceback
            traceback.print_exc()
            if not self.cancelled:
                self.window.after(0, lambda: self._update_status(f"❌ Error: {str(e)}", "error"))
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
        self.model_btn.config(state=tk.NORMAL, text="⏳ Run Model")
        self.progress['value'] = 0

    # ============= RESULTS DISPLAY =============

    def _update_results_ui(self, result):
        """Update UI with results"""
        if result is None:
            return

        # Clear and plot
        self.ax.clear()

        # Confidence band
        if 'lower_ci' in result and 'upper_ci' in result:
            self.ax.fill_betweenx(result['depths'],
                                 result['lower_ci'],
                                 result['upper_ci'],
                                 alpha=0.3, color='#3498db',
                                 label=f'{int(self.confidence_var.get()*100)}% CI')

        # Model
        self.ax.plot(result['median'], result['depths'], 'b-', linewidth=2, label='Model')

        # Data points
        self.ax.errorbar(result['raw_ages'], result['raw_depths'],
                        xerr=result['raw_errors'] * 1.96,
                        fmt='o', color='#e74c3c', capsize=3, markersize=6,
                        label=f'Dates (n={len(result["raw_depths"])})')

        self.ax.invert_yaxis()
        self.ax.set_xlabel('Age (cal BP)')
        self.ax.set_ylabel(f'{self.depth_var.get()} (cm)')
        self.ax.set_title(f'Age-Depth Model: {result["method"]}')
        self.ax.legend(loc='lower right')
        self.ax.grid(True, alpha=0.3)

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
                                   color=colors[i], alpha=0.7, linewidth=1.5,
                                   label=f'Sample {i+1}: {cal["median"]:.0f} cal BP')

            curve_name = self.curve_var.get()
            info = self.curves.get_curve_info(curve_name)

            self.cal_ax.set_xlabel('Probability density')
            self.cal_ax.set_ylabel('Calibrated age (cal BP)')
            self.cal_ax.set_title(f'{curve_name} Calibration')
            self.cal_ax.legend(fontsize=8)
            self.cal_ax.grid(True, alpha=0.3)

            self.cal_figure.tight_layout()
            self.cal_canvas.draw()

        # Statistics
        stats = f"{'='*60}\n"
        stats += f"CHRONOLOGICAL DATING RESULTS\n"
        stats += f"{'='*60}\n\n"

        stats += f"Model: {result['method']}\n"
        stats += f"Dates: {len(result['raw_ages'])}\n"
        stats += f"Depth range: {np.min(result['depths']):.1f} - {np.max(result['depths']):.1f} cm\n"
        stats += f"Age range: {np.min(result['median']):.0f} - {np.max(result['median']):.0f} cal BP\n"
        stats += f"Confidence: {int(self.confidence_var.get()*100)}%\n\n"

        if 'acc_rates' in result:
            stats += f"SEDIMENTATION RATES\n"
            stats += f"{'-'*40}\n"
            stats += f"  Mean: {np.nanmean(result['acc_rates']):.2f} yr/cm\n"
            stats += f"  Median: {np.nanmedian(result['acc_rates']):.2f} yr/cm\n"
            stats += f"  Range: {np.nanmin(result['acc_rates']):.2f} - {np.nanmax(result['acc_rates']):.2f} yr/cm\n\n"

        if self.calibration_results:
            stats += f"CALIBRATION\n"
            stats += f"{'-'*40}\n"
            stats += f"  Curve: {self.curve_var.get()}\n"
            stats += f"  ΔR: {self.deltaR_var.get()} ± {self.deltaR_error_var.get()} yr\n"
            stats += f"  Samples calibrated: {len(self.calibration_results)}\n"

            # Add curve info
            info = self.curves.get_curve_info(self.curve_var.get())
            if 'points' in info:
                stats += f"  Curve points: {info['points']}\n"
            if 'range' in info:
                stats += f"  Curve range: {info['range'][0]:.0f} - {info['range'][1]:.0f} cal BP\n\n"

        elapsed = time.time() - self._start_time if self._start_time else 0
        stats += f"PERFORMANCE\n"
        stats += f"{'-'*40}\n"
        stats += f"  Processing time: {elapsed:.1f}s\n"

        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats)

        self._update_status(f"✅ Completed {result['method']} in {elapsed:.1f}s", "success")
        self.notebook.select(0)

    # ============= EXPORT =============

    def _export_results(self):
        """Export results"""
        if self.age_model is None:
            messagebox.showwarning("No Results", "Run age-depth model first!")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[
                ("CSV files", "*.csv"),
                ("PNG files", "*.png"),
                ("PDF files", "*.pdf")
            ]
        )

        if filename:
            try:
                if filename.endswith('.csv'):
                    # Export age-depth model
                    df = pd.DataFrame({
                        'Depth_cm': self.age_model['depths'],
                        'Age_calBP_median': self.age_model['median'],
                        'Age_calBP_lower': self.age_model['lower_ci'],
                        'Age_calBP_upper': self.age_model['upper_ci']
                    })

                    if 'acc_rates' in self.age_model:
                        df['Sedimentation_rate_yr_per_cm'] = self.age_model['acc_rates']

                    df.to_csv(filename, index=False)

                    # Export calibration if available
                    if self.calibration_results:
                        cal_filename = filename.replace('.csv', '_calibration.csv')
                        cal_data = []
                        for i, cal in enumerate(self.calibration_results):
                            cal_data.append({
                                'Sample': i+1,
                                'Raw_14C_age': cal['raw_age'],
                                'Raw_14C_error': cal['raw_error'],
                                'DeltaR': cal['deltaR'],
                                'Corrected_age': cal['corrected_age'],
                                'Calibrated_age_median': cal['median'],
                                'Calibrated_age_mean': cal['mean'],
                                'Calibrated_age_mode': cal['mode'],
                                'Calibrated_std': cal['std'],
                                'HPD_2sigma_min': cal['hpd_2sigma'][0],
                                'HPD_2sigma_max': cal['hpd_2sigma'][1],
                                'Curve': cal['curve']
                            })
                        pd.DataFrame(cal_data).to_csv(cal_filename, index=False)

                else:
                    # Export figure
                    self.figure.savefig(filename, dpi=300, bbox_inches='tight')

                self._update_status(f"✅ Exported to {os.path.basename(filename)}", "success")

            except Exception as e:
                self._update_status(f"❌ Export failed: {str(e)}", "error")


# ============================================================================
# PART 4: PLUGIN SETUP
# ============================================================================

def setup_plugin(main_app):
    """Plugin setup function - called by main app"""
    plugin = DatingIntegrationPlugin(main_app)
    return plugin  # ← REMOVE ALL MENU CODE
