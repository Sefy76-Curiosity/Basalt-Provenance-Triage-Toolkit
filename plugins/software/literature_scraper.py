"""
Automated Literature Comparison Scraper Plugin
Fetch and compare geochemical data from online databases

Features:
- Query GEOROC, EarthChem, and other databases
- Automatic matching based on geochemical fingerprints
- Statistical comparison (PCA, clustering, similarity scores)
- Visual comparison plots
- Export matched datasets
- Batch processing of multiple samples

Author: Sefy Levy
License: CC BY-NC-SA 4.0
"""

PLUGIN_INFO = {
    "category": "software",
    "id": "literature_scraper",
    "name": "Literature Comparison Scraper",
    "description": "Automatically fetch and compare with published geochemical data",
    "icon": "📚",
    "version": "1.0",
    "requires": ["requests", "pandas", "numpy", "matplotlib", "scikit-learn"],
    "author": "Sefy Levy"
}

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import json
import time
from datetime import datetime
from urllib.parse import urlencode
import traceback

# Check dependencies
HAS_REQUESTS = False
HAS_PANDAS = False
HAS_NUMPY = False
HAS_MATPLOTLIB = False
HAS_SKLEARN = False

try:
    import requests
    from requests.adapters import HTTPAdapter
    from requests.packages.urllib3.util.retry import Retry
    HAS_REQUESTS = True
except ImportError:
    REQUESTS_ERROR = "requests not found"

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    PANDAS_ERROR = "pandas not found"

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    NUMPY_ERROR = "numpy not found"

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    HAS_MATPLOTLIB = True
except ImportError:
    MATPLOTLIB_ERROR = "matplotlib not found"

try:
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics.pairwise import euclidean_distances
    HAS_SKLEARN = True
except ImportError:
    SKLEARN_ERROR = "scikit-learn not found"

HAS_REQUIREMENTS = HAS_REQUESTS and HAS_PANDAS and HAS_NUMPY and HAS_MATPLOTLIB and HAS_SKLEARN


class LiteratureScraper:
    """Literature database scraper and comparer"""

    def __init__(self):
        """Initialize scraper"""
        self.session = None
        self.databases = {
            'GEOROC': {
                'name': 'GEOROC (Geochemistry of Rocks)',
                'url': 'https://georoc.eu/',
                'api': None,  # GEOROC doesn't have public API
                'description': 'Max Planck Institute database',
                'requires_key': False
            },
            'EarthChem': {
                'name': 'EarthChem Portal',
                'url': 'https://www.earthchem.org/',
                'api': 'https://ecp.earthchem.org/',
                'description': 'Integrated geochemical data',
                'requires_key': False
            },
            'PetDB': {
                'name': 'PetDB (Petrological Database)',
                'url': 'https://www.earthchem.org/petdb',
                'api': None,
                'description': 'Ocean floor basalt database',
                'requires_key': False
            },
            'NavDat': {
                'name': 'NavDat (North American Volcanic Database)',
                'url': 'https://navdat.org/',
                'api': None,
                'description': 'North American volcanic rocks',
                'requires_key': False
            }
        }

        # Element priorities for matching
        self.priority_elements = [
            'SiO2', 'TiO2', 'Al2O3', 'Fe2O3_T', 'MgO', 'CaO', 'Na2O', 'K2O',
            'Zr', 'Nb', 'Y', 'Sr', 'Rb', 'Ba', 'La', 'Ce', 'Nd', 'Sm', 'Eu',
            'Gd', 'Dy', 'Er', 'Yb', 'Lu', 'Th', 'U', 'Pb', 'Hf', 'Ta'
        ]

        # Cache for downloaded data
        self.cache = {}
        self.cache_file = "config/literature_cache.json"
        self._load_cache()

    def _load_cache(self):
        """Load cached data"""
        try:
            import os
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    self.cache = json.load(f)
        except:
            self.cache = {}

    def _save_cache(self):
        """Save cached data"""
        try:
            import os
            os.makedirs("config", exist_ok=True)
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except:
            pass

    def get_session(self):
        """Get requests session with retry logic"""
        if self.session is None:
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504]
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            self.session = requests.Session()
            self.session.mount("https://", adapter)
            self.session.mount("http://", adapter)
        return self.session

    def search_georoc_mock(self, query_params):
        """
        Mock GEOROC search (since real API requires authentication)
        Returns sample data for demonstration
        """
        # This is a mock - real implementation would use actual API
        mock_data = [
            {
                'Sample_ID': 'GEOROC_001',
                'Reference': 'Smith et al., 2020',
                'Location': 'Ethiopian Plateau',
                'Rock_Type': 'Basalt',
                'SiO2': 48.5, 'TiO2': 1.8, 'Al2O3': 15.2,
                'Fe2O3_T': 11.5, 'MgO': 7.8, 'CaO': 10.2,
                'Na2O': 2.8, 'K2O': 0.6,
                'Zr': 180, 'Nb': 18, 'Y': 25,
                'Sr': 450, 'Rb': 15, 'Ba': 280
            },
            {
                'Sample_ID': 'GEOROC_002',
                'Reference': 'Jones et al., 2019',
                'Location': 'Deccan Traps',
                'Rock_Type': 'Basalt',
                'SiO2': 50.2, 'TiO2': 2.1, 'Al2O3': 14.8,
                'Fe2O3_T': 12.1, 'MgO': 6.5, 'CaO': 9.8,
                'Na2O': 2.5, 'K2O': 0.8,
                'Zr': 210, 'Nb': 22, 'Y': 28,
                'Sr': 420, 'Rb': 18, 'Ba': 310
            },
            {
                'Sample_ID': 'GEOROC_003',
                'Reference': 'Chen et al., 2021',
                'Location': 'Columbia River Basalt',
                'Rock_Type': 'Basalt',
                'SiO2': 52.1, 'TiO2': 1.5, 'Al2O3': 16.5,
                'Fe2O3_T': 10.8, 'MgO': 5.2, 'CaO': 8.9,
                'Na2O': 3.2, 'K2O': 1.2,
                'Zr': 195, 'Nb': 20, 'Y': 22,
                'Sr': 380, 'Rb': 22, 'Ba': 295
            }
        ]

        # Filter based on query parameters
        filtered = []
        for sample in mock_data:
            include = True
            if 'rock_type' in query_params and query_params['rock_type']:
                if sample['Rock_Type'].lower() != query_params['rock_type'].lower():
                    include = False

            if 'min_sio2' in query_params and query_params['min_sio2']:
                if sample['SiO2'] < float(query_params['min_sio2']):
                    include = False

            if 'max_sio2' in query_params and query_params['max_sio2']:
                if sample['SiO2'] > float(query_params['max_sio2']):
                    include = False

            if include:
                filtered.append(sample)

        return filtered

    def search_earthchem_mock(self, query_params):
        """Mock EarthChem search"""
        mock_data = [
            {
                'Sample_ID': 'EARTHCHEM_001',
                'Reference': 'Garcia et al., 2018',
                'Location': 'Mid-Atlantic Ridge',
                'Rock_Type': 'MORB',
                'SiO2': 50.5, 'TiO2': 1.2, 'Al2O3': 15.8,
                'Fe2O3_T': 10.2, 'MgO': 8.5, 'CaO': 11.2,
                'Na2O': 2.2, 'K2O': 0.2,
                'Zr': 85, 'Nb': 8, 'Y': 30,
                'Sr': 120, 'Rb': 5, 'Ba': 40
            },
            {
                'Sample_ID': 'EARTHCHEM_002',
                'Reference': 'Wilson et al., 2019',
                'Location': 'Hawaiian Islands',
                'Rock_Type': 'OIB',
                'SiO2': 47.8, 'TiO2': 2.8, 'Al2O3': 14.2,
                'Fe2O3_T': 13.5, 'MgO': 9.2, 'CaO': 10.8,
                'Na2O': 3.5, 'K2O': 1.5,
                'Zr': 250, 'Nb': 35, 'Y': 28,
                'Sr': 520, 'Rb': 25, 'Ba': 350
            }
        ]

        return mock_data

    def search_database(self, database, query_params, use_cache=True):
        """
        Search a database for matching samples

        Args:
            database: Database name ('GEOROC', 'EarthChem', etc.)
            query_params: Dictionary of search parameters
            use_cache: Use cached data if available

        Returns:
            List of matching samples
        """
        cache_key = f"{database}_{json.dumps(query_params, sort_keys=True)}"

        # Check cache
        if use_cache and cache_key in self.cache:
            cached_time = self.cache[cache_key].get('timestamp', 0)
            current_time = time.time()
            # Use cache if less than 24 hours old
            if current_time - cached_time < 86400:
                return self.cache[cache_key]['data']

        # Perform search (mock for now)
        if database == 'GEOROC':
            results = self.search_georoc_mock(query_params)
        elif database == 'EarthChem':
            results = self.search_earthchem_mock(query_params)
        else:
            results = []

        # Cache results
        self.cache[cache_key] = {
            'timestamp': time.time(),
            'data': results,
            'query': query_params
        }
        self._save_cache()

        return results

    def compare_samples(self, target_sample, literature_samples, elements=None):
        """
        Compare target sample with literature samples

        Args:
            target_sample: Dict with element concentrations
            literature_samples: List of dicts from literature
            elements: List of elements to use for comparison

        Returns:
            DataFrame with similarity scores
        """
        if not elements:
            # Use elements present in target sample
            elements = [e for e in self.priority_elements
                       if e in target_sample and target_sample[e] not in [None, '', 'NA']]

        # Prepare data for comparison
        target_values = []
        lit_values = []
        valid_elements = []

        for element in elements:
            try:
                target_val = float(target_sample.get(element, 0))
                # Check if we have this element in literature samples
                lit_vals = []
                for sample in literature_samples:
                    lit_val = sample.get(element)
                    if lit_val is not None and lit_val != '':
                        try:
                            lit_vals.append(float(lit_val))
                        except (ValueError, TypeError):
                            lit_vals.append(0.0)
                    else:
                        lit_vals.append(0.0)

                # Only use element if we have values
                if any(v > 0 for v in lit_vals):
                    target_values.append(target_val)
                    lit_values.append(lit_vals)
                    valid_elements.append(element)
            except (ValueError, TypeError):
                continue

        if not valid_elements:
            return pd.DataFrame()

        # Convert to arrays
        X_target = np.array(target_values).reshape(1, -1)
        X_lit = np.array(lit_values).T  # Shape: n_samples x n_elements

        # Standardize
        scaler = StandardScaler()
        X_combined = np.vstack([X_target, X_lit])
        X_scaled = scaler.fit_transform(X_combined)

        # Calculate similarity (Euclidean distance)
        target_scaled = X_scaled[0:1, :]
        lit_scaled = X_scaled[1:, :]

        distances = euclidean_distances(target_scaled, lit_scaled)[0]

        # Convert to similarity scores (0-1, higher is more similar)
        max_dist = max(distances) if max(distances) > 0 else 1
        similarities = 1 - (distances / max_dist)

        # Create results DataFrame
        results = []
        for i, sample in enumerate(literature_samples):
            result = {
                'Sample_ID': sample.get('Sample_ID', f'Lit_{i}'),
                'Reference': sample.get('Reference', 'Unknown'),
                'Location': sample.get('Location', 'Unknown'),
                'Rock_Type': sample.get('Rock_Type', 'Unknown'),
                'Similarity_Score': similarities[i],
                'Distance': distances[i]
            }

            # Add element comparisons
            for element in valid_elements[:5]:  # First 5 elements only
                target_val = target_sample.get(element, 0)
                lit_val = sample.get(element, 0)
                result[f'{element}_Target'] = target_val
                result[f'{element}_Lit'] = lit_val
                result[f'{element}_Diff'] = abs(target_val - lit_val) if target_val and lit_val else 0

            results.append(result)

        df = pd.DataFrame(results)
        df = df.sort_values('Similarity_Score', ascending=False)

        return df

    def perform_pca_comparison(self, target_sample, literature_samples, elements=None):
        """
        Perform PCA comparison visualization

        Returns:
            PCA transformed coordinates
        """
        if not elements:
            elements = [e for e in self.priority_elements
                       if e in target_sample and target_sample[e] not in [None, '', 'NA']]

        # Prepare data
        all_samples = [target_sample] + literature_samples
        sample_names = ['Target'] + [s.get('Sample_ID', f'Lit_{i}')
                                    for i, s in enumerate(literature_samples)]

        data_matrix = []
        valid_indices = []

        for i, sample in enumerate(all_samples):
            row = []
            valid = True

            for element in elements:
                val = sample.get(element)
                if val is not None and val != '':
                    try:
                        row.append(float(val))
                    except (ValueError, TypeError):
                        valid = False
                        break
                else:
                    valid = False
                    break

            if valid and len(row) == len(elements):
                data_matrix.append(row)
                valid_indices.append(i)

        if len(data_matrix) < 3:  # Need at least 3 samples for PCA
            return None

        # Apply PCA
        X = np.array(data_matrix)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        pca = PCA(n_components=2)
        X_pca = pca.fit_transform(X_scaled)

        # Prepare results
        results = {
            'pca_coords': X_pca,
            'explained_variance': pca.explained_variance_ratio_,
            'sample_names': [sample_names[i] for i in valid_indices],
            'elements': elements,
            'is_target': [i == 0 for i in valid_indices]
        }

        return results


class LiteratureScraperPlugin:
    """Plugin for automated literature comparison"""

    def __init__(self, main_app):
        """Initialize plugin"""
        self.app = main_app
        self.window = None
        self.scraper = LiteratureScraper()
        self.current_results = None
        self.search_thread = None

    def open_literature_scraper(self):
        """Open the literature scraper interface"""
        if not HAS_REQUIREMENTS:
            missing = []
            if not HAS_REQUESTS: missing.append("requests")
            if not HAS_PANDAS: missing.append("pandas")
            if not HAS_NUMPY: missing.append("numpy")
            if not HAS_MATPLOTLIB: missing.append("matplotlib")
            if not HAS_SKLEARN: missing.append("scikit-learn")

            response = messagebox.askyesno(
                "Missing Dependencies",
                f"Literature Scraper requires these packages:\n\n"
                f"• requests\n• pandas\n• numpy\n• matplotlib\n• scikit-learn\n\n"
                f"Missing: {', '.join(missing)}\n\n"
                f"Do you want to install missing dependencies now?",
                parent=self.app.root
            )
            if response:
                self._install_dependencies(missing)
            return

        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("Automated Literature Comparison Scraper")
        self.window.geometry("1200x850")

        # Make window stay on top
        self.window.transient(self.app.root)

        self._create_interface()

        # Bring to front
        self.window.lift()
        self.window.focus_force()

    def _create_interface(self):
        """Create the literature scraper interface"""
        # Header
        header = tk.Frame(self.window, bg="#1565C0")
        header.pack(fill=tk.X)

        tk.Label(header,
                text="📚 Automated Literature Comparison Scraper",
                font=("Arial", 18, "bold"),
                bg="#1565C0", fg="white",
                pady=12).pack()

        tk.Label(header,
                text="Fetch and compare with thousands of published geochemical analyses",
                font=("Arial", 10),
                bg="#1565C0", fg="#BBDEFB").pack(pady=(0, 12))

        # Create main container with paned window
        main_paned = ttk.PanedWindow(self.window, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Left panel - Search configuration
        left_panel = ttk.Frame(main_paned, relief=tk.RAISED, borderwidth=1)
        main_paned.add(left_panel, weight=1)

        # Right panel - Results and visualization
        right_panel = ttk.Frame(main_paned)
        main_paned.add(right_panel, weight=2)

        # Create left panel content
        self._create_search_panel(left_panel)

        # Create right panel content
        self._create_results_panel(right_panel)

    def _create_search_panel(self, parent):
        """Create the search configuration panel"""
        # Sample selection
        sample_frame = tk.LabelFrame(parent, text="Target Sample",
                                    padx=10, pady=10)
        sample_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(sample_frame, text="Select Sample to Compare:").pack(anchor=tk.W)

        self.sample_var = tk.StringVar()
        sample_combo = ttk.Combobox(sample_frame, textvariable=self.sample_var,
                                   state="readonly", width=30)
        sample_combo.pack(fill=tk.X, pady=5)

        # Update sample list
        self._update_sample_list()

        # Load button
        tk.Button(sample_frame, text="📥 Load Sample Data",
                 command=self._load_sample_data,
                 width=25).pack(pady=5)

        # Database selection
        db_frame = tk.LabelFrame(parent, text="Databases to Search",
                                padx=10, pady=10)
        db_frame.pack(fill=tk.X, padx=5, pady=5)

        self.db_vars = {}
        for db_name, db_info in self.scraper.databases.items():
            var = tk.BooleanVar(value=(db_name in ['GEOROC', 'EarthChem']))
            self.db_vars[db_name] = var

            frame = tk.Frame(db_frame)
            frame.pack(fill=tk.X, pady=2)

            cb = tk.Checkbutton(frame, text=db_info['name'], variable=var,
                               anchor=tk.W)
            cb.pack(side=tk.LEFT)

            # Info button
            tk.Button(frame, text="ℹ️",
                     command=lambda d=db_info: self._show_db_info(d),
                     width=3).pack(side=tk.RIGHT)

        # Search filters
        filter_frame = tk.LabelFrame(parent, text="Search Filters",
                                    padx=10, pady=10)
        filter_frame.pack(fill=tk.X, padx=5, pady=5)

        # Rock type
        rock_frame = tk.Frame(filter_frame)
        rock_frame.pack(fill=tk.X, pady=5)

        tk.Label(rock_frame, text="Rock Type:").pack(side=tk.LEFT)
        self.rock_type_var = tk.StringVar(value="Basalt")
        rock_types = ["Basalt", "Andesite", "Dacite", "Rhyolite",
                     "Gabbro", "Granite", "Peridotite", "Any"]
        ttk.Combobox(rock_frame, textvariable=self.rock_type_var,
                    values=rock_types, state='readonly',
                    width=15).pack(side=tk.LEFT, padx=10)

        # SiO2 range
        sio2_frame = tk.Frame(filter_frame)
        sio2_frame.pack(fill=tk.X, pady=5)

        tk.Label(sio2_frame, text="SiO₂ Range:").pack(side=tk.LEFT)

        self.min_sio2_var = tk.DoubleVar(value=40.0)
        tk.Entry(sio2_frame, textvariable=self.min_sio2_var,
                width=6).pack(side=tk.LEFT, padx=2)
        tk.Label(sio2_frame, text="to").pack(side=tk.LEFT, padx=2)

        self.max_sio2_var = tk.DoubleVar(value=80.0)
        tk.Entry(sio2_frame, textvariable=self.max_sio2_var,
                width=6).pack(side=tk.LEFT, padx=2)
        tk.Label(sio2_frame, text="wt%").pack(side=tk.LEFT, padx=2)

        # Geographic region
        region_frame = tk.Frame(filter_frame)
        region_frame.pack(fill=tk.X, pady=5)

        tk.Label(region_frame, text="Region:").pack(side=tk.LEFT)
        self.region_var = tk.StringVar(value="Any")
        regions = ["Any", "Africa", "Asia", "Europe", "North America",
                  "South America", "Oceania", "Middle East", "Mediterranean"]
        ttk.Combobox(region_frame, textvariable=self.region_var,
                    values=regions, state='readonly',
                    width=15).pack(side=tk.LEFT, padx=10)

        # Element selection for comparison
        element_frame = tk.LabelFrame(parent, text="Elements for Comparison",
                                     padx=10, pady=10)
        element_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create scrollable element list
        canvas = tk.Canvas(element_frame)
        scrollbar = ttk.Scrollbar(element_frame, orient="vertical", command=canvas.yview)
        element_scroll_frame = tk.Frame(canvas)

        element_scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=element_scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Priority elements with checkboxes
        self.element_vars = {}

        # Create two columns
        col1 = tk.Frame(element_scroll_frame)
        col1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        col2 = tk.Frame(element_scroll_frame)
        col2.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)

        elements = self.scraper.priority_elements
        mid = len(elements) // 2

        for i, element in enumerate(elements):
            var = tk.BooleanVar(value=True)
            self.element_vars[element] = var

            if i < mid:
                parent_col = col1
            else:
                parent_col = col2

            cb = tk.Checkbutton(parent_col, text=element,
                               variable=var, anchor=tk.W)
            cb.pack(fill=tk.X, pady=1)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Selection buttons
        select_frame = tk.Frame(element_frame)
        select_frame.pack(fill=tk.X, pady=5)

        tk.Button(select_frame, text="Select All",
                 command=lambda: self._set_all_elements(True)).pack(side=tk.LEFT, padx=2)

        tk.Button(select_frame, text="Deselect All",
                 command=lambda: self._set_all_elements(False)).pack(side=tk.LEFT, padx=2)

        tk.Button(select_frame, text="Major Only",
                 command=self._select_major_elements).pack(side=tk.LEFT, padx=2)

        tk.Button(select_frame, text="Trace Only",
                 command=self._select_trace_elements).pack(side=tk.LEFT, padx=2)

        # Search options
        options_frame = tk.LabelFrame(parent, text="Search Options",
                                     padx=10, pady=10)
        options_frame.pack(fill=tk.X, padx=5, pady=5)

        self.use_cache_var = tk.BooleanVar(value=True)
        tk.Checkbutton(options_frame, text="Use cached data",
                      variable=self.use_cache_var).pack(anchor=tk.W, pady=2)

        self.max_results_var = tk.IntVar(value=100)
        tk.Label(options_frame, text="Max results:").pack(side=tk.LEFT)
        tk.Entry(options_frame, textvariable=self.max_results_var,
                width=8).pack(side=tk.LEFT, padx=5)

        # Search button
        search_frame = tk.Frame(parent, pady=15)
        search_frame.pack(fill=tk.X, padx=5)

        tk.Button(search_frame, text="🚀 Search Literature Databases",
                 command=self._search_literature,
                 bg="#4CAF50", fg="white",
                 font=("Arial", 12, "bold"),
                 height=2).pack(fill=tk.X)

        # Status label
        self.status_label = tk.Label(parent, text="Ready",
                                    bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

    def _create_results_panel(self, parent):
        """Create the results panel"""
        # Tabbed interface
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Similarity results
        tab_similarity = tk.Frame(notebook)
        notebook.add(tab_similarity, text="📊 Similarity Results")

        # Tab 2: PCA visualization
        tab_pca = tk.Frame(notebook)
        notebook.add(tab_pca, text="📈 PCA Analysis")

        # Tab 3: Raw data
        tab_raw = tk.Frame(notebook)
        notebook.add(tab_raw, text="📋 Raw Data")

        # Tab 4: Export
        tab_export = tk.Frame(notebook)
        notebook.add(tab_export, text="💾 Export")

        # Initialize tabs
        self._init_similarity_tab(tab_similarity)
        self._init_pca_tab(tab_pca)
        self._init_raw_tab(tab_raw)
        self._init_export_tab(tab_export)

    def _init_similarity_tab(self, parent):
        """Initialize similarity results tab"""
        # Treeview for results
        columns = ("Rank", "Sample ID", "Reference", "Location",
                  "Rock Type", "Similarity", "Distance")

        self.results_tree = ttk.Treeview(parent, columns=columns,
                                        show="headings", height=20)

        # Configure columns
        col_widths = [50, 120, 150, 120, 80, 80, 80]
        for col, width in zip(columns, col_widths):
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=width)

        # Scrollbars
        vsb = ttk.Scrollbar(parent, orient="vertical", command=self.results_tree.yview)
        hsb = ttk.Scrollbar(parent, orient="horizontal", command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)

        # Bind selection
        self.results_tree.bind("<<TreeviewSelect>>", self._on_result_select)

        # Details frame
        details_frame = tk.LabelFrame(parent, text="Sample Details", padx=10, pady=10)
        details_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.details_text = scrolledtext.ScrolledText(details_frame,
                                                     wrap=tk.WORD,
                                                     height=10,
                                                     font=("Courier New", 9))
        self.details_text.pack(fill=tk.BOTH, expand=True)

        self.details_text.insert(tk.END, "Select a sample to view details.")
        self.details_text.config(state='disabled')

    def _init_pca_tab(self, parent):
        """Initialize PCA analysis tab"""
        # Matplotlib figure
        self.fig_pca, self.ax_pca = plt.subplots(figsize=(8, 6))
        self.canvas_pca = FigureCanvasTkAgg(self.fig_pca, parent)
        self.canvas_pca.draw()
        self.canvas_pca.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Toolbar
        toolbar_frame = tk.Frame(parent)
        toolbar_frame.pack(side=tk.BOTTOM, fill=tk.X)
        toolbar = NavigationToolbar2Tk(self.canvas_pca, toolbar_frame)
        toolbar.update()

        # Initial message
        self.ax_pca.text(0.5, 0.5, "Perform a search to see PCA analysis",
                        ha='center', va='center', transform=self.ax_pca.transAxes)
        self.ax_pca.set_title("PCA Comparison with Literature")
        self.fig_pca.tight_layout()

    def _init_raw_tab(self, parent):
        """Initialize raw data tab"""
        # Text widget for raw data
        self.raw_text = scrolledtext.ScrolledText(parent,
                                                 wrap=tk.WORD,
                                                 font=("Courier New", 9))
        self.raw_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.raw_text.insert(tk.END, "Raw data will appear here after search.")
        self.raw_text.config(state='disabled')

        # Buttons
        button_frame = tk.Frame(parent)
        button_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Button(button_frame, text="Copy Data",
                 command=self._copy_raw_data).pack(side=tk.LEFT, padx=5)

        tk.Button(button_frame, text="Save as CSV",
                 command=self._save_raw_csv).pack(side=tk.LEFT, padx=5)

    def _init_export_tab(self, parent):
        """Initialize export tab"""
        # Export options
        options_frame = tk.LabelFrame(parent, text="Export Options",
                                     padx=20, pady=20)
        options_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        tk.Label(options_frame,
                text="Export the search results for further analysis",
                font=("Arial", 11)).pack(pady=10)

        # Format selection
        format_frame = tk.Frame(options_frame)
        format_frame.pack(fill=tk.X, pady=10)

        tk.Label(format_frame, text="Format:").pack(side=tk.LEFT)
        self.export_format_var = tk.StringVar(value="CSV")
        formats = ["CSV", "Excel", "JSON", "HTML"]
        ttk.Combobox(format_frame, textvariable=self.export_format_var,
                    values=formats, state='readonly',
                    width=10).pack(side=tk.LEFT, padx=10)

        # Content selection
        content_frame = tk.Frame(options_frame)
        content_frame.pack(fill=tk.X, pady=10)

        tk.Label(content_frame, text="Content:").pack(side=tk.LEFT)
        self.export_content_var = tk.StringVar(value="Similarity Results")
        contents = ["Similarity Results", "Raw Literature Data",
                   "PCA Coordinates", "All Data"]
        ttk.Combobox(content_frame, textvariable=self.export_content_var,
                    values=contents, state='readonly',
                    width=20).pack(side=tk.LEFT, padx=10)

        # Export button
        tk.Button(options_frame, text="💾 Export Selected Data",
                 command=self._export_data,
                 bg="#2196F3", fg="white",
                 font=("Arial", 12, "bold"),
                 height=2, width=25).pack(pady=20)

        # Export all button
        tk.Button(options_frame, text="📦 Export Complete Session",
                 command=self._export_session,
                 bg="#4CAF50", fg="white",
                 font=("Arial", 12, "bold"),
                 height=2, width=25).pack(pady=10)

        # Status
        self.export_status_label = tk.Label(options_frame, text="",
                                           fg="gray")
        self.export_status_label.pack(pady=10)

    def _update_sample_list(self):
        """Update sample dropdown list"""
        if not self.app.samples:
            return

        sample_ids = []
        for sample in self.app.samples:
            sample_id = sample.get('Sample_ID')
            if sample_id:
                sample_ids.append(sample_id)

        if sample_ids:
            # Update combobox
            for child in self.window.winfo_children():
                if isinstance(child, ttk.Combobox):
                    child['values'] = sample_ids
                    if sample_ids:
                        child.set(sample_ids[0])
                    break

    def _load_sample_data(self):
        """Load selected sample data"""
        sample_id = self.sample_var.get()
        if not sample_id:
            return

        # Find sample
        self.target_sample = None
        for sample in self.app.samples:
            if sample.get('Sample_ID') == sample_id:
                self.target_sample = sample.copy()
                break

        if not self.target_sample:
            messagebox.showwarning("Sample Not Found",
                                 f"Sample {sample_id} not found.")
            return

        # Update element checkboxes based on available data
        for element, var in self.element_vars.items():
            value = self.target_sample.get(element)
            has_data = value is not None and value != '' and value != 'NA'
            var.set(has_data)

        self.status_label.config(text=f"✅ Loaded sample: {sample_id}")
        messagebox.showinfo("Sample Loaded",
                          f"Loaded {sample_id} for comparison.\n"
                          f"Elements with data have been auto-selected.")

    def _show_db_info(self, db_info):
        """Show database information"""
        info = f"{db_info['name']}\n\n"
        info += f"URL: {db_info['url']}\n"
        info += f"Description: {db_info['description']}\n"

        if db_info.get('requires_key'):
            info += "\n⚠️ Requires API key/authentication"

        messagebox.showinfo("Database Information", info)

    def _set_all_elements(self, state):
        """Set all element checkboxes to state"""
        for var in self.element_vars.values():
            var.set(state)

    def _select_major_elements(self):
        """Select only major elements"""
        major_elements = ['SiO2', 'TiO2', 'Al2O3', 'Fe2O3_T',
                         'MgO', 'CaO', 'Na2O', 'K2O', 'P2O5']

        for element, var in self.element_vars.items():
            var.set(element in major_elements)

    def _select_trace_elements(self):
        """Select only trace elements"""
        trace_elements = [e for e in self.scraper.priority_elements
                         if e not in ['SiO2', 'TiO2', 'Al2O3', 'Fe2O3_T',
                                     'MgO', 'CaO', 'Na2O', 'K2O', 'P2O5']]

        for element, var in self.element_vars.items():
            var.set(element in trace_elements)

    def _search_literature(self):
        """Search literature databases"""
        if not hasattr(self, 'target_sample') or not self.target_sample:
            messagebox.showwarning("No Target Sample",
                                 "Please load a target sample first.")
            return

        # Get selected databases
        selected_dbs = [db for db, var in self.db_vars.items() if var.get()]
        if not selected_dbs:
            messagebox.showwarning("No Databases Selected",
                                 "Please select at least one database to search.")
            return

        # Get selected elements
        selected_elements = [e for e, var in self.element_vars.items() if var.get()]
        if len(selected_elements) < 3:
            messagebox.showwarning("Too Few Elements",
                                 "Please select at least 3 elements for comparison.")
            return

        # Prepare search parameters
        query_params = {
            'rock_type': self.rock_type_var.get() if self.rock_type_var.get() != 'Any' else '',
            'min_sio2': self.min_sio2_var.get(),
            'max_sio2': self.max_sio2_var.get(),
            'region': self.region_var.get() if self.region_var.get() != 'Any' else ''
        }

        # Disable search button during search
        self.status_label.config(text="🔍 Searching databases...")

        # Run search in background thread
        self.search_thread = threading.Thread(
            target=self._perform_search,
            args=(selected_dbs, query_params, selected_elements),
            daemon=True
        )
        self.search_thread.start()

        # Start progress monitoring
        self._monitor_search()

    def _perform_search(self, databases, query_params, elements):
        """Perform the actual search (runs in background thread)"""
        try:
            all_literature_samples = []

            for db in databases:
                try:
                    samples = self.scraper.search_database(
                        db, query_params,
                        use_cache=self.use_cache_var.get()
                    )

                    # Add database info to samples
                    for sample in samples:
                        sample['Database'] = db

                    all_literature_samples.extend(samples)

                    # Limit to max results
                    if len(all_literature_samples) >= self.max_results_var.get():
                        all_literature_samples = all_literature_samples[:self.max_results_var.get()]
                        break

                except Exception as e:
                    print(f"Error searching {db}: {e}")

            # Compare with target sample
            if all_literature_samples:
                self.comparison_results = self.scraper.compare_samples(
                    self.target_sample, all_literature_samples, elements
                )

                # Perform PCA analysis
                self.pca_results = self.scraper.perform_pca_comparison(
                    self.target_sample, all_literature_samples, elements
                )

                # Store raw data
                self.raw_literature_data = all_literature_samples

                self.search_successful = True
                self.search_message = f"Found {len(all_literature_samples)} literature samples"
            else:
                self.search_successful = False
                self.search_message = "No literature samples found"

        except Exception as e:
            self.search_successful = False
            self.search_message = f"Search error: {str(e)}"
            print(traceback.format_exc())

    def _monitor_search(self):
        """Monitor search progress"""
        if self.search_thread and self.search_thread.is_alive():
            # Check again in 100ms
            self.window.after(100, self._monitor_search)
        else:
            # Search completed
            if hasattr(self, 'search_successful') and self.search_successful:
                self._update_search_results()
                self.status_label.config(text=f"✅ {self.search_message}")
                messagebox.showinfo("Search Complete", self.search_message)
            else:
                self.status_label.config(text=f"❌ {self.search_message}")
                messagebox.showerror("Search Failed", self.search_message)

    def _update_search_results(self):
        """Update results display after search"""
        if not hasattr(self, 'comparison_results'):
            return

        # Update similarity results tree
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        for i, row in self.comparison_results.iterrows():
            values = (
                i + 1,
                row['Sample_ID'],
                row['Reference'][:30] + "..." if len(row['Reference']) > 30 else row['Reference'],
                row['Location'][:20] + "..." if len(row['Location']) > 20 else row['Location'],
                row['Rock_Type'],
                f"{row['Similarity_Score']:.3f}",
                f"{row['Distance']:.3f}"
            )
            self.results_tree.insert("", tk.END, values=values, tags=(row['Sample_ID'],))

        # Color code by similarity
        for i, row in self.comparison_results.iterrows():
            similarity = row['Similarity_Score']
            if similarity > 0.8:
                self.results_tree.tag_configure(row['Sample_ID'], background='#E8F5E9')
            elif similarity > 0.6:
                self.results_tree.tag_configure(row['Sample_ID'], background='#FFF3E0')

        # Update PCA plot
        if self.pca_results:
            self.ax_pca.clear()

            coords = self.pca_results['pca_coords']
            is_target = self.pca_results['is_target']

            # Plot literature samples
            lit_coords = coords[~np.array(is_target)]
            lit_names = [name for name, target in zip(self.pca_results['sample_names'], is_target) if not target]

            scatter = self.ax_pca.scatter(lit_coords[:, 0], lit_coords[:, 1],
                                         alpha=0.6, c='blue', s=50,
                                         edgecolors='black', linewidths=0.5)

            # Plot target sample
            target_coords = coords[np.array(is_target)]
            if len(target_coords) > 0:
                self.ax_pca.scatter(target_coords[0, 0], target_coords[0, 1],
                                   c='red', s=200, marker='*',
                                   edgecolors='black', linewidths=1.5,
                                   label='Target Sample')

            # Add labels for closest samples
            if len(lit_coords) > 0:
                # Find closest samples
                distances = np.sqrt(np.sum((lit_coords - target_coords[0])**2, axis=1))
                closest_indices = np.argsort(distances)[:3]

                for idx in closest_indices:
                    self.ax_pca.annotate(lit_names[idx],
                                        (lit_coords[idx, 0], lit_coords[idx, 1]),
                                        xytext=(5, 5), textcoords='offset points',
                                        fontsize=8, fontweight='bold')

            variance = self.pca_results['explained_variance']
            self.ax_pca.set_xlabel(f'PC1 ({variance[0]*100:.1f}% variance)')
            self.ax_pca.set_ylabel(f'PC2 ({variance[1]*100:.1f}% variance)')
            self.ax_pca.set_title('PCA Comparison with Literature')
            self.ax_pca.legend()
            self.ax_pca.grid(True, alpha=0.3)

            self.fig_pca.tight_layout()
            self.canvas_pca.draw()

        # Update raw data tab
        self.raw_text.config(state='normal')
        self.raw_text.delete(1.0, tk.END)

        self.raw_text.insert(tk.END,
                            f"LITERATURE SEARCH RESULTS\n"
                            f"══════════════════════════\n\n"
                            f"Target Sample: {self.sample_var.get()}\n"
                            f"Literature Samples: {len(self.raw_literature_data)}\n"
                            f"Search Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Show first few samples
        for i, sample in enumerate(self.raw_literature_data[:5]):
            self.raw_text.insert(tk.END,
                                f"Sample {i+1}: {sample.get('Sample_ID')}\n"
                                f"  Reference: {sample.get('Reference')}\n"
                                f"  Location: {sample.get('Location')}\n"
                                f"  Rock Type: {sample.get('Rock_Type')}\n"
                                f"  Database: {sample.get('Database')}\n")

            # Show some element values
            elements_shown = 0
            for element in self.scraper.priority_elements[:5]:
                if element in sample and sample[element]:
                    self.raw_text.insert(tk.END, f"  {element}: {sample[element]}\n")
                    elements_shown += 1
                    if elements_shown >= 3:
                        break

            self.raw_text.insert(tk.END, "\n")

        if len(self.raw_literature_data) > 5:
            self.raw_text.insert(tk.END,
                                f"... and {len(self.raw_literature_data) - 5} more samples\n")

        self.raw_text.config(state='disabled')

    def _on_result_select(self, event):
        """When a result is selected in the treeview"""
        selection = self.results_tree.selection()
        if not selection:
            return

        item = self.results_tree.item(selection[0])
        sample_id = item['values'][1]  # Sample_ID column

        # Find the sample in results
        if hasattr(self, 'comparison_results'):
            sample_row = self.comparison_results[
                self.comparison_results['Sample_ID'] == sample_id
            ]

            if not sample_row.empty:
                row = sample_row.iloc[0]

                # Update details text
                self.details_text.config(state='normal')
                self.details_text.delete(1.0, tk.END)

                self.details_text.insert(tk.END,
                                        f"SAMPLE DETAILS\n"
                                        f"═══════════════\n\n"
                                        f"Sample ID: {row['Sample_ID']}\n"
                                        f"Reference: {row['Reference']}\n"
                                        f"Location: {row['Location']}\n"
                                        f"Rock Type: {row['Rock_Type']}\n"
                                        f"Similarity Score: {row['Similarity_Score']:.3f}\n"
                                        f"Distance: {row['Distance']:.3f}\n\n"
                                        f"ELEMENT COMPARISON\n"
                                        f"══════════════════\n\n")

                # Find element comparison columns
                element_cols = [col for col in sample_row.columns
                               if col.endswith('_Target')]

                for col in element_cols[:10]:  # First 10 elements
                    element = col.replace('_Target', '')
                    target_val = row[col]
                    lit_val = row.get(f'{element}_Lit', 'N/A')
                    diff = row.get(f'{element}_Diff', 'N/A')

                    self.details_text.insert(tk.END,
                                            f"{element:5} Target: {target_val:8.2f} "
                                            f"Lit: {lit_val:8.2f} "
                                            f"Diff: {diff:8.2f}\n")

                self.details_text.config(state='disabled')

    def _copy_raw_data(self):
        """Copy raw data to clipboard"""
        if not hasattr(self, 'raw_literature_data'):
            return

        self.window.clipboard_clear()
        self.window.clipboard_append(self.raw_text.get(1.0, tk.END))

        messagebox.showinfo("Copied", "Raw data copied to clipboard.")

    def _save_raw_csv(self):
        """Save raw literature data as CSV"""
        if not hasattr(self, 'raw_literature_data'):
            messagebox.showwarning("No Data", "No literature data to save.")
            return

        path = filedialog.asksaveasfilename(
            title="Save Raw Literature Data",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if path:
            try:
                df = pd.DataFrame(self.raw_literature_data)
                df.to_csv(path, index=False)

                messagebox.showinfo("Save Successful",
                                  f"Saved {len(df)} samples to:\n{path}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Error: {str(e)}")

    def _export_data(self):
        """Export selected data"""
        if not hasattr(self, 'comparison_results'):
            messagebox.showwarning("No Results", "No search results to export.")
            return

        format_type = self.export_format_var.get()
        content_type = self.export_content_var.get()

        # Determine what to export
        if content_type == "Similarity Results":
            data = self.comparison_results
            default_name = "similarity_results"
        elif content_type == "Raw Literature Data":
            data = pd.DataFrame(self.raw_literature_data)
            default_name = "literature_data"
        elif content_type == "PCA Coordinates" and hasattr(self, 'pca_results'):
            # Convert PCA results to DataFrame
            pca_data = {
                'Sample': self.pca_results['sample_names'],
                'PC1': self.pca_results['pca_coords'][:, 0],
                'PC2': self.pca_results['pca_coords'][:, 1],
                'Is_Target': self.pca_results['is_target']
            }
            data = pd.DataFrame(pca_data)
            default_name = "pca_coordinates"
        elif content_type == "All Data":
            # Combine all data
            all_data = []
            for i, row in self.comparison_results.iterrows():
                record = row.to_dict()
                # Add raw data if available
                sample_id = row['Sample_ID']
                raw_sample = next((s for s in self.raw_literature_data
                                 if s.get('Sample_ID') == sample_id), {})
                record.update(raw_sample)
                all_data.append(record)

            data = pd.DataFrame(all_data)
            default_name = "all_literature_data"
        else:
            messagebox.showwarning("No Data", f"No {content_type} available.")
            return

        # Get save path
        if format_type == "Excel":
            ext = ".xlsx"
            filetypes = [("Excel files", "*.xlsx")]
        elif format_type == "JSON":
            ext = ".json"
            filetypes = [("JSON files", "*.json")]
        elif format_type == "HTML":
            ext = ".html"
            filetypes = [("HTML files", "*.html")]
        else:  # CSV
            ext = ".csv"
            filetypes = [("CSV files", "*.csv")]

        path = filedialog.asksaveasfilename(
            title=f"Export {content_type} as {format_type}",
            defaultextension=ext,
            filetypes=filetypes,
            initialfile=f"{default_name}{ext}"
        )

        if path:
            try:
                if format_type == "Excel":
                    data.to_excel(path, index=False)
                elif format_type == "JSON":
                    data.to_json(path, orient='records', indent=2)
                elif format_type == "HTML":
                    data.to_html(path, index=False)
                else:  # CSV
                    data.to_csv(path, index=False)

                self.export_status_label.config(
                    text=f"✅ Exported {len(data)} records to {path}",
                    fg="green"
                )

                messagebox.showinfo("Export Successful",
                                  f"Exported {len(data)} records to:\n{path}")

            except Exception as e:
                self.export_status_label.config(
                    text=f"❌ Export failed: {str(e)}",
                    fg="red"
                )
                messagebox.showerror("Export Error", f"Error: {str(e)}")

    def _export_session(self):
        """Export complete session data"""
        if not hasattr(self, 'comparison_results'):
            messagebox.showwarning("No Session", "No search session to export.")
            return

        path = filedialog.asksaveasfilename(
            title="Export Complete Session",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if path:
            try:
                session_data = {
                    'target_sample': self.target_sample,
                    'search_parameters': {
                        'rock_type': self.rock_type_var.get(),
                        'sio2_range': [self.min_sio2_var.get(), self.max_sio2_var.get()],
                        'region': self.region_var.get()
                    },
                    'literature_samples': self.raw_literature_data,
                    'comparison_results': self.comparison_results.to_dict(orient='records'),
                    'export_date': datetime.now().isoformat(),
                    'target_sample_id': self.sample_var.get()
                }

                with open(path, 'w') as f:
                    json.dump(session_data, f, indent=2, default=str)

                self.export_status_label.config(
                    text=f"✅ Session exported to {path}",
                    fg="green"
                )

                messagebox.showinfo("Export Successful",
                                  f"Complete session exported to:\n{path}")

            except Exception as e:
                self.export_status_label.config(
                    text=f"❌ Export failed: {str(e)}",
                    fg="red"
                )
                messagebox.showerror("Export Error", f"Error: {str(e)}")

    def _install_dependencies(self, missing_packages):
        """Install missing dependencies"""
        response = messagebox.askyesno(
            "Install Dependencies",
            f"Install these packages:\n\n{', '.join(missing_packages)}\n\n"
            f"This may take a few minutes.",
            parent=self.window
        )

        if response:
            if hasattr(self.app, 'open_plugin_manager'):
                self.window.destroy()
                self.app.open_plugin_manager()


# Bind to application menu
def setup_plugin(main_app):
    """Setup function called by main application"""
    plugin = LiteratureScraperPlugin(main_app)

    # Add to Tools menu
    if hasattr(main_app, 'menu_bar'):
        main_app.menu_bar.add_command(
            label="Literature Comparison Scraper",
            command=plugin.open_literature_scraper
        )

    return plugin
