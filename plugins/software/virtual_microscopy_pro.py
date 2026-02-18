"""
Virtual Microscopy Pro v4.0 - Petrography + 3D Archaeology
WITH FULL MAIN APP INTEGRATION

NOW WITH 3D ARCHAEOLOGICAL ANALYSIS:
✓ Load 3D Meshes (STL/OBJ/PLY)
✓ Curvature Analysis - Tool marks, manufacturing traces
✓ Profile Extraction - Cross-sections through artifacts
✓ Unwrap Cylinder - Flatten curved surfaces (pottery)
✓ Feature Detection - Automatic identification
"""

PLUGIN_INFO = {
    "category": "software",
    "id": "virtual_microscopy_pro",
    "name": "Virtual Microscopy Pro",
    "description": "Petrographic analysis + 3D archaeological mesh analysis",
    "icon": "🔬",
    "version": "4.0.0",
    "requires": ["numpy", "matplotlib", "pillow", "scipy", "pandas", "trimesh"],
    "author": "Sefy Levy & DeepSeek"
}

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
from datetime import datetime
from pathlib import Path
import json
import traceback

# Scientific imports
try:
    import matplotlib
    matplotlib.use('TkAgg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    from matplotlib.patches import Ellipse, Polygon
    from matplotlib.lines import Line2D
    from mpl_toolkits.mplot3d import Axes3D
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    import numpy as np
    from scipy import ndimage, stats
    from scipy.spatial import KDTree, Delaunay, Voronoi, distance
    import pandas as pd
    HAS_NUMPY = True
    HAS_SCIPY = True
    HAS_PANDAS = True
except ImportError:
    HAS_NUMPY = False
    HAS_SCIPY = False
    HAS_PANDAS = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# 3D Mesh Processing
try:
    import trimesh
    from trimesh import transformations
    HAS_TRIMESH = True
except ImportError:
    HAS_TRIMESH = False

HAS_REQUIREMENTS = HAS_NUMPY and HAS_MATPLOTLIB and HAS_PIL and HAS_PANDAS


class VirtualMicroscopyProPlugin:
    """
    VIRTUAL MICROSCOPY PRO v4.0 - PETROGRAPHY + 3D ARCHAEOLOGY
    """

    # ============================================================================
    # MINERAL DATABASE with optical properties
    # ============================================================================
    MINERAL_DATABASE = {
        'quartz': {
            'color': [0.9, 0.9, 0.9], 'hardness': 7, 'birefringence': 0.009,
            'cleavage': 'none', 'habit': 'equant', 'formula': 'SiO2',
            'qapf_group': 'Q'
        },
        'plagioclase': {
            'color': [0.8, 0.8, 1.0], 'hardness': 6, 'birefringence': 0.007,
            'cleavage': 'two', 'habit': 'tabular', 'formula': '(Na,Ca)AlSi3O8',
            'qapf_group': 'P'
        },
        'k-feldspar': {
            'color': [1.0, 0.9, 0.8], 'hardness': 6, 'birefringence': 0.007,
            'cleavage': 'two', 'habit': 'prismatic', 'formula': 'KAlSi3O8',
            'qapf_group': 'A'
        },
        'biotite': {
            'color': [0.2, 0.1, 0.1], 'hardness': 2.5, 'birefringence': 0.040,
            'cleavage': 'perfect', 'habit': 'flaky', 'formula': 'K(Mg,Fe)3AlSi3O10(OH)2',
            'qapf_group': 'M'
        },
        'muscovite': {
            'color': [0.9, 0.9, 0.7], 'hardness': 2.5, 'birefringence': 0.035,
            'cleavage': 'perfect', 'habit': 'flaky', 'formula': 'KAl2(AlSi3O10)(OH)2',
            'qapf_group': 'M'
        },
        'hornblende': {
            'color': [0.1, 0.4, 0.1], 'hardness': 5.5, 'birefringence': 0.025,
            'cleavage': 'two', 'habit': 'prismatic', 'formula': 'Ca2(Mg,Fe,Al)5(Al,Si)8O22(OH)2',
            'qapf_group': 'M'
        },
        'augite': {
            'color': [0.2, 0.3, 0.1], 'hardness': 6, 'birefringence': 0.030,
            'cleavage': 'two', 'habit': 'prismatic', 'formula': '(Ca,Na)(Mg,Fe,Al,Ti)(Si,Al)2O6',
            'qapf_group': 'M'
        },
        'olivine': {
            'color': [0.2, 0.6, 0.2], 'hardness': 6.5, 'birefringence': 0.035,
            'cleavage': 'poor', 'habit': 'equant', 'formula': '(Mg,Fe)2SiO4',
            'qapf_group': 'M'
        },
        'apatite': {
            'color': [0.8, 0.4, 0.8], 'hardness': 5, 'birefringence': 0.003,
            'cleavage': 'poor', 'habit': 'prismatic', 'formula': 'Ca5(PO4)3(OH,F,Cl)',
            'qapf_group': 'Accessory'
        },
        'zircon': {
            'color': [0.9, 0.8, 0.1], 'hardness': 7.5, 'birefringence': 0.050,
            'cleavage': 'poor', 'habit': 'prismatic', 'formula': 'ZrSiO4',
            'qapf_group': 'Accessory'
        },
        'calcite': {
            'color': [1.0, 1.0, 0.9], 'hardness': 3, 'birefringence': 0.170,
            'cleavage': 'perfect', 'habit': 'rhombohedral', 'formula': 'CaCO3',
            'qapf_group': 'Carbonate'
        },
        'opaque': {
            'color': [0.1, 0.1, 0.1], 'hardness': 5, 'birefringence': 0,
            'cleavage': 'none', 'habit': 'massive', 'formula': 'Fe-Ti oxides',
            'qapf_group': 'Opaque'
        },
        'void': {
            'color': [0.0, 0.0, 0.0], 'hardness': 0, 'birefringence': 0,
            'cleavage': 'none', 'habit': 'none', 'formula': 'porosity',
            'qapf_group': None
        }
    }

    # ============================================================================
    # WENTWORTH GRAIN SIZE SCALE (mm)
    # ============================================================================
    WENTWORTH_SCALE = [
        (256, 'Boulder'),
        (64, 'Cobble'),
        (4, 'Pebble'),
        (2, 'Granule'),
        (1, 'Very coarse sand'),
        (0.5, 'Coarse sand'),
        (0.25, 'Medium sand'),
        (0.125, 'Fine sand'),
        (0.0625, 'Very fine sand'),
        (0.0039, 'Silt'),
        (0, 'Clay')
    ]

    # ============================================================================
    # QAPF CLASSIFICATION (Streckeisen, 1976)
    # ============================================================================
    QAPF_FIELDS = {
        'Granite': {'Q': (20, 60), 'P': (0, 100), 'A': (0, 100)},
        'Granodiorite': {'Q': (20, 60), 'P': (65, 90), 'A': (10, 35)},
        'Tonalite': {'Q': (20, 60), 'P': (90, 100), 'A': (0, 10)},
        'Quartz monzonite': {'Q': (5, 20), 'P': (35, 65), 'A': (35, 65)},
        'Quartz monzodiorite': {'Q': (5, 20), 'P': (65, 90), 'A': (10, 35)},
        'Quartz diorite': {'Q': (5, 20), 'P': (90, 100), 'A': (0, 10)},
        'Syenite': {'Q': (0, 5), 'P': (35, 65), 'A': (35, 65)},
        'Monzonite': {'Q': (0, 5), 'P': (65, 90), 'A': (10, 35)},
        'Diorite': {'Q': (0, 5), 'P': (90, 100), 'A': (0, 10)},
    }

    def __init__(self, main_app):
        self.app = main_app
        self.window = None

        # ============ DATA FROM MAIN APP ============
        self.samples = None
        self.sample_data = {}  # Organized by Sample_ID
        self.mineralogy_estimates = {}  # Estimated from geochemistry

        # ============ PETROGRAPHIC DATA ============
        self.mineral_data = []  # Generated grains
        self.point_counts = {}  # Modal analysis results
        self.qapf_values = {}   # QAPF coordinates per sample
        self.rock_classification = {}  # Rock type per sample
        self.grain_stats = {}    # Grain size statistics

        # ============ 3D ARCHAEOLOGICAL DATA ============
        self.mesh = None
        self.mesh_path = None
        self.mesh_info = {}
        self.curvature_map = None
        self.features = {}
        self.comparison_results = {}

        # ============ UI ELEMENTS ============
        self.notebook = None
        self.fig = None
        self.ax = None
        self.canvas = None
        self.fig_3d = None
        self.ax_3d = None
        self.canvas_3d = None
        self.mineral_vars = {}
        self.status_var = None
        self.progress = None
        self.sample_selector = None
        self.mesh_info_var = None
        self.analysis_type_var = None
        self.scale_var = None
        self.sensitivity_var = None

        # Check dependencies
        self._check_dependencies()

    def _check_dependencies(self):
        """Check if required packages are installed"""
        missing = []
        if not HAS_NUMPY: missing.append("numpy")
        if not HAS_MATPLOTLIB: missing.append("matplotlib")
        if not HAS_PIL: missing.append("pillow")
        if not HAS_SCIPY: missing.append("scipy")
        if not HAS_PANDAS: missing.append("pandas")
        if not HAS_TRIMESH: missing.append("trimesh (for 3D)")

        self.dependencies_met = len(missing) == 0
        self.missing_deps = missing

    # ============================================================================
    # SAFE FLOAT CONVERSION
    # ============================================================================
    def _safe_float(self, value):
        """Safely convert value to float"""
        if value is None or value == '':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    # ============================================================================
    # MAIN APP INTEGRATION - AUTO LOAD
    # ============================================================================
    def _load_from_main_app(self):
        """Auto-load samples from main app on window open"""
        if not hasattr(self.app, 'samples') or not self.app.samples:
            print("❌ No samples in main app")
            return False

        self.samples = pd.DataFrame(self.app.samples)
        print(f"📊 Loaded {len(self.samples)} samples from main app")

        # DEBUG: Print ALL columns available
        print("\n📋 ALL COLUMNS IN DATA:")
        for i, col in enumerate(self.samples.columns):
            print(f"  {i+1}. {col}")

        # DEBUG: Print first sample values for major oxides
        if len(self.samples) > 0:
            first = self.samples.iloc[0]
            print("\n🔍 FIRST SAMPLE VALUES:")
            for col in self.samples.columns[:20]:  # First 20 columns
                val = first[col]
                print(f"  {col}: {val} (type: {type(val).__name__})")

        # Organize by Sample_ID
        for i, row in self.samples.iterrows():
            sample_id = row.get('Sample_ID', f'SAMPLE_{i:04d}')
            self.sample_data[sample_id] = row.to_dict()

        # Detect geochemical columns
        self._detect_geochemical_columns()

        # Generate thin section from data
        print("\n🔨 GENERATING FROM GEOCHEMISTRY...")
        success = self._generate_from_geochemistry()
        print(f"✅ Generated {len(self.mineral_data)} grains from geochemistry")

        return success

    def _refresh_all_tabs(self):
        """Refresh all tabs with current data"""
        if hasattr(self, 'sample_selector') and self.sample_selector:
            self.sample_selector['values'] = list(self.sample_data.keys())
            if self.sample_data:
                self.sample_selector.set(list(self.sample_data.keys())[0])

        self._update_plot()
        self._update_provenance_tree()
        self._update_modal_tab()
        self._update_qapf_plot()
        self._update_grain_size_tab()
        self._update_fabric_tab()

        if self.mineral_data:
            self.status_var.set(f"✅ Loaded {len(self.samples)} samples, {len(self.mineral_data)} grains")
        else:
            self.status_var.set("ℹ️ No mineral data generated - check console for CIPW debug output")

    def _detect_geochemical_columns(self):
        """Detect major element columns using chemical_elements.json"""
        if self.samples is None or len(self.samples) == 0:
            return

        # Major elements for CIPW norm (these are the STANDARD names)
        self.major_elements = {
            'SiO2_wt': None, 'TiO2_wt': None, 'Al2O3_wt': None,
            'Fe2O3_T_wt': None, 'FeO_wt': None, 'MnO_wt': None,
            'MgO_wt': None, 'CaO_wt': None, 'Na2O_wt': None,
            'K2O_wt': None, 'P2O5_wt': None
        }

        # Use the app's reverse mapping to find columns
        if hasattr(self.app, 'element_reverse_map'):
            reverse_map = self.app.element_reverse_map

            # Check each column in samples
            for col in self.samples.columns:
                col_str = str(col)

                # Find the standard name for this column
                if col_str in reverse_map:
                    standard = reverse_map[col_str]

                    # Check if this standard matches any of our major elements
                    for major in self.major_elements.keys():
                        if major in standard or standard in major:
                            self.major_elements[major] = col_str
                            print(f"✅ Detected {major} column: {col_str}")
                            break
        else:
            # Fallback to simple detection if no mapping
            print("⚠️ No element_reverse_map found, using simple detection")
            for col in self.samples.columns:
                col_upper = str(col).upper()
                for major in self.major_elements.keys():
                    if major.upper().replace('_WT', '') in col_upper:
                        self.major_elements[major] = col
                        print(f"✅ Detected {major} column: {col}")
                        break

    # ============================================================================
    # GEOCHEMISTRY TO MINERALOGY (CIPW Norm)
    # ============================================================================
    def _calculate_cipw_norm(self, sample):
        """
        Calculate CIPW normative minerals from major oxides
        """
        print("\n📊 CALCULATING CIPW FOR SAMPLE:")

        # Check if we have major elements
        oxides = {}
        for oxide, col in self.major_elements.items():
            if col and col in sample:
                val = self._safe_float(sample[col])
                standard_name = oxide  # This is the standard name like 'SiO2_wt'
                print(f"  {standard_name}: column='{col}', raw value='{sample.get(col)}', converted={val}")
                if val is not None and val > 0:
                    oxides[standard_name] = val

        print(f"  Collected oxides with values >0: {list(oxides.keys())}")

        if len(oxides) < 3:
            print(f"  ❌ Not enough oxides with values: {len(oxides)}")
            return None

        # Molecular weights (using standard names)
        mol_wt = {
            'SiO2_wt': 60.08, 'TiO2_wt': 79.88, 'Al2O3_wt': 101.96,
            'Fe2O3_T_wt': 159.69, 'FeO_wt': 71.85, 'MnO_wt': 70.94,
            'MgO_wt': 40.31, 'CaO_wt': 56.08, 'Na2O_wt': 61.98,
            'K2O_wt': 94.20, 'P2O5_wt': 141.94
        }

        # Convert to molecular proportions
        mol = {}
        for oxide, value in oxides.items():
            if oxide in mol_wt and value > 0:
                mol[oxide] = value / mol_wt[oxide]
                print(f"  {oxide}: {value:.2f} wt% → {mol[oxide]:.4f} mol")

        # Initialize norms dictionary
        norms = {}
        print("\n  Calculating normative minerals:")

        # Apatite
        if 'P2O5_wt' in mol and 'CaO_wt' in mol:
            ap = mol['P2O5_wt'] * 3.33
            if ap * 100 > 0.1:
                norms['apatite'] = min(ap * 100, 5)
                print(f"    Apatite: {norms['apatite']:.2f}%")
                if 'CaO_wt' in mol:
                    mol['CaO_wt'] = mol.get('CaO_wt', 0) - ap

        # Ilmenite
        if 'TiO2_wt' in mol:
            ilm = mol['TiO2_wt'] * 100
            if ilm > 0.1:
                norms['ilmenite'] = ilm
                print(f"    Ilmenite: {norms['ilmenite']:.2f}%")
                mol['TiO2_wt'] = 0

        # Orthoclase
        if 'K2O_wt' in mol:
            or_ = mol['K2O_wt']
            if or_ * 100 > 0.1:
                norms['k-feldspar'] = or_ * 100
                print(f"    K-feldspar: {norms['k-feldspar']:.2f}%")
                mol['K2O_wt'] = 0
                if 'Al2O3_wt' in mol:
                    mol['Al2O3_wt'] = mol.get('Al2O3_wt', 0) - or_

        # Albite
        if 'Na2O_wt' in mol:
            ab = mol['Na2O_wt']
            if ab * 100 > 0.1:
                norms['plagioclase'] = ab * 100
                print(f"    Plagioclase (albite): {norms['plagioclase']:.2f}%")
                mol['Na2O_wt'] = 0
                if 'Al2O3_wt' in mol:
                    mol['Al2O3_wt'] = mol.get('Al2O3_wt', 0) - ab

        # Anorthite (remaining CaO and Al2O3)
        if 'CaO_wt' in mol and 'Al2O3_wt' in mol:
            an = min(mol['CaO_wt'], mol['Al2O3_wt'])
            if an * 100 > 0.1:
                norms['plagioclase'] = norms.get('plagioclase', 0) + an * 100
                print(f"    Plagioclase (anorthite): +{an*100:.2f}%")
                mol['CaO_wt'] = mol.get('CaO_wt', 0) - an
                mol['Al2O3_wt'] = mol.get('Al2O3_wt', 0) - an

        # Quartz (remaining SiO2)
        if 'SiO2_wt' in mol:
            # Estimate used silica (simplified)
            used_sio2 = 0
            if 'k-feldspar' in norms:
                used_sio2 += mol.get('K2O_wt', 0) * 6
            if 'plagioclase' in norms:
                used_sio2 += (mol.get('Na2O_wt', 0) * 6 + mol.get('CaO_wt', 0) * 2)

            qz = mol['SiO2_wt'] - used_sio2
            if qz * 100 > 0.1:
                norms['quartz'] = qz * 100
                print(f"    Quartz: {norms['quartz']:.2f}%")

        # Mafics
        mafics = 0
        for oxide in ['FeO_wt', 'Fe2O3_T_wt', 'MgO_wt', 'MnO_wt']:
            if oxide in mol:
                mafics += mol.get(oxide, 0) * 100
        if mafics > 1:
            norms['mafics'] = mafics
            print(f"    Mafics: {norms['mafics']:.2f}%")

        if not norms:
            print("  ❌ No normative minerals calculated")
            return None

        print(f"  ✅ Calculated {len(norms)} normative minerals")
        return norms

    def _classify_qapf(self, q, a, p):
        """Classify rock based on QAPF coordinates (Streckeisen, 1976)"""
        total = q + a + p
        if total == 0:
            return 'Unknown'

        # Normalize to 100%
        q_norm = q / total * 100
        a_norm = a / total * 100
        p_norm = p / total * 100

        # QAPF classification
        if q_norm > 60:
            return 'Quartz-rich'
        elif q_norm > 20:
            if a_norm > p_norm:
                return 'Granite' if a_norm > 65 else 'Granodiorite'
            else:
                return 'Tonalite'
        elif q_norm > 5:
            if a_norm > p_norm:
                return 'Quartz monzonite'
            else:
                return 'Quartz diorite'
        else:
            if a_norm > p_norm:
                return 'Syenite' if abs(a_norm - p_norm) < 30 else 'Monzonite'
            else:
                return 'Diorite' if p_norm > 90 else 'Gabbro'

    def _generate_from_geochemistry(self):
        """Generate virtual thin section from geochemical data"""
        if self.samples is None:
            return False

        # CLEAR existing data FIRST
        self.mineral_data = []
        self.qapf_values = {}
        self.rock_classification = {}

        # Get coordinates if available
        lat_col = None
        lon_col = None
        for col in self.samples.columns:
            if 'lat' in str(col).lower():
                lat_col = col
            if 'lon' in str(col).lower() or 'long' in str(col).lower():
                lon_col = col

        # Process each sample
        grains_generated = 0

        for idx, sample in self.samples.iterrows():
            sample_id = sample.get('Sample_ID', f'SAMPLE_{idx:04d}')

            # Get coordinates
            x_base = (idx % 10) * 50  # Grid layout: 10 columns
            y_base = (idx // 10) * 50

            if lat_col and lon_col:
                lat = self._safe_float(sample.get(lat_col))
                lon = self._safe_float(sample.get(lon_col))
                if lat and lon:
                    x_base = lon * 10
                    y_base = lat * 10

            # Calculate CIPW norms
            norms = self._calculate_cipw_norm(sample)

            # ALWAYS create entries for this sample, even if norms is None
            if norms:
                # Calculate QAPF values
                q = norms.get('quartz', 0)
                a = norms.get('k-feldspar', 0)
                p = norms.get('plagioclase', 0)

                # Store QAPF
                self.qapf_values[sample_id] = {'Q': q, 'A': a, 'P': p}

                # Classify rock
                self.rock_classification[sample_id] = self._classify_qapf(q, a, p)

                # Generate grains based on mineralogy
                for mineral, pct in norms.items():
                    if mineral in self.MINERAL_DATABASE and pct > 1:
                        # Number of grains proportional to percentage
                        n_grains = max(1, int(pct / 5))

                        for i in range(n_grains):
                            grain = {
                                'type': mineral,
                                'x': x_base + np.random.uniform(-20, 20),
                                'y': y_base + np.random.uniform(-20, 20) + (i * 3),
                                'z': np.random.uniform(0, 10),
                                'size': np.random.lognormal(2, 0.5) * (pct / 30),
                                'aspect_ratio': np.random.uniform(0.5, 1.5),
                                'angle': np.random.uniform(0, 180),
                                'sample_id': sample_id
                            }
                            self.mineral_data.append(grain)
                            grains_generated += 1
            else:
                # Even if no norms, still create empty entries for this sample
                self.qapf_values[sample_id] = {'Q': 0, 'A': 0, 'P': 0}
                self.rock_classification[sample_id] = 'Unknown'

        print(f"✅ Generated {grains_generated} grains from {len(self.samples)} samples")
        print(f"📊 QAPF values for {len(self.qapf_values)} samples")

        return grains_generated > 0

    # ============================================================================
    # GRAIN SIZE ANALYSIS (Folk & Ward, 1957)
    # ============================================================================
    def _analyze_grain_size(self, sample_id=None):
        """Calculate grain size statistics"""
        # Filter grains by sample
        if sample_id:
            grains = [g for g in self.mineral_data if g.get('sample_id') == sample_id]
        else:
            grains = self.mineral_data

        if len(grains) < 5:
            return None

        sizes = [g['size'] for g in grains]

        # Folk & Ward (1957) graphical measures
        sizes_sorted = np.sort(sizes)
        n = len(sizes_sorted)

        # Percentiles
        p5 = np.percentile(sizes_sorted, 5)
        p16 = np.percentile(sizes_sorted, 16)
        p25 = np.percentile(sizes_sorted, 25)
        p50 = np.percentile(sizes_sorted, 50)
        p75 = np.percentile(sizes_sorted, 75)
        p84 = np.percentile(sizes_sorted, 84)
        p95 = np.percentile(sizes_sorted, 95)

        # Folk & Ward parameters (phi scale)
        mean = (p16 + p50 + p84) / 3
        sorting = ((p84 - p16) / 4) + ((p95 - p5) / 6.6)
        skewness = ((p16 + p84 - 2*p50) / (2*(p84 - p16))) + ((p5 + p95 - 2*p50) / (2*(p95 - p5)))
        kurtosis = (p95 - p5) / (2.44 * (p75 - p25))

        # Wentworth classification
        wentworth = self._get_wentworth_class(p50)

        return {
            'count': n,
            'mean': mean,
            'median': p50,
            'sorting': sorting,
            'skewness': skewness,
            'kurtosis': kurtosis,
            'wentworth': wentworth,
            'percentiles': {'5': p5, '16': p16, '25': p25, '50': p50,
                           '75': p75, '84': p84, '95': p95}
        }

    def _get_wentworth_class(self, size_mm):
        """Classify grain size using Wentworth scale"""
        for threshold, name in self.WENTWORTH_SCALE:
            if size_mm >= threshold:
                return name
        return 'Clay'

    # ============================================================================
    # FABRIC ANALYSIS (Woodcock, 1977)
    # ============================================================================
    def _analyze_fabric(self, sample_id=None):
        """Analyze grain orientation fabric"""
        # Filter grains by sample
        if sample_id:
            grains = [g for g in self.mineral_data if g.get('sample_id') == sample_id]
        else:
            grains = self.mineral_data

        if len(grains) < 10:
            return None

        # Get orientations
        angles = [g.get('angle', 0) for g in grains]

        # Convert to radians for statistics
        angles_rad = np.radians(angles)

        # Calculate mean resultant vector (Rayleigh test)
        R = np.sqrt(np.mean(np.cos(angles_rad))**2 + np.mean(np.sin(angles_rad))**2)
        mean_angle = np.degrees(np.arctan2(np.mean(np.sin(angles_rad)),
                                          np.mean(np.cos(angles_rad)))) % 360

        # Woodcock (1977) fabric parameters
        if R > 0.5:
            fabric_type = 'Strong'
        elif R > 0.3:
            fabric_type = 'Moderate'
        elif R > 0.1:
            fabric_type = 'Weak'
        else:
            fabric_type = 'Random'

        return {
            'R': R,
            'mean_angle': mean_angle,
            'fabric_type': fabric_type,
            'n_grains': len(grains)
        }

    # ============================================================================
    # POINT COUNTING MODAL ANALYSIS
    # ============================================================================
    def _point_count_modal(self, sample_id=None):
        """Calculate modal percentages by point counting"""
        # Filter grains by sample
        if sample_id:
            grains = [g for g in self.mineral_data if g.get('sample_id') == sample_id]
        else:
            grains = self.mineral_data

        if len(grains) < 10:
            return None

        # Count minerals
        counts = {}
        for grain in grains:
            mineral = grain['type']
            counts[mineral] = counts.get(mineral, 0) + 1

        # Convert to percentages
        total = len(grains)
        modal = {mineral: (count / total * 100) for mineral, count in counts.items()}

        return modal

    # ============================================================================
    # SEND RESULTS TO MAIN APP
    # ============================================================================
    def _send_results_to_main(self):
        """Add petrographic results to main app as new columns"""
        if not self.sample_data:
            messagebox.showwarning("No Data", "No samples to export")
            return

        updates = []

        for sample_id, sample in self.sample_data.items():
            # Get results for this sample
            qapf = self.qapf_values.get(sample_id, {})
            rock_type = self.rock_classification.get(sample_id, 'Unknown')
            grain_stats = self._analyze_grain_size(sample_id)
            fabric = self._analyze_fabric(sample_id)
            modal = self._point_count_modal(sample_id)

            # Build update record
            record = {
                'Sample_ID': sample_id,
                'Rock_Type_QAPF': rock_type,
                'QAPF_Q': f"{qapf.get('Q', 0):.1f}",
                'QAPF_A': f"{qapf.get('A', 0):.1f}",
                'QAPF_P': f"{qapf.get('P', 0):.1f}",
            }

            # Add modal analysis
            if modal:
                for mineral, pct in modal.items():
                    if pct > 1:  # Only significant minerals
                        record[f'Modal_{mineral.capitalize()}'] = f"{pct:.1f}"

            # Add grain size stats
            if grain_stats:
                record['Grain_Size_Mean'] = f"{grain_stats['mean']:.2f}"
                record['Grain_Size_Class'] = grain_stats['wentworth']
                record['Sorting'] = f"{grain_stats['sorting']:.2f}"

            # Add fabric analysis
            if fabric:
                record['Fabric_Strength'] = fabric['fabric_type']
                record['Fabric_R'] = f"{fabric['R']:.3f}"
                record['Fabric_Orientation'] = f"{fabric['mean_angle']:.1f}"

            record['VM_Timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            updates.append(record)

        # Send to main app
        if updates:
            self.app.import_data_from_plugin(updates)
            self.status_var.set(f"✅ Exported {len(updates)} sample analyses")
            messagebox.showinfo("Success",
                               f"Added {len(updates)} sample analyses\n"
                               f"New columns: Rock_Type_QAPF, QAPF_*, Modal_*, Grain_Size_*")

    # ============================================================================
    # 3D ARCHAEOLOGICAL ANALYSIS METHODS
    # ============================================================================

    def _load_3d_mesh(self):
        """Load 3D mesh file"""
        if not HAS_TRIMESH:
            messagebox.showerror("Error", "Please install trimesh: pip install trimesh")
            return

        path = filedialog.askopenfilename(
            title="Load 3D Mesh",
            filetypes=[("3D files", "*.stl *.obj *.ply"), ("All files", "*.*")]
        )
        if not path:
            return

        self.progress.start()
        self.status_var.set(f"Loading {Path(path).name}...")

        try:
            self.mesh = trimesh.load(path)
            self.mesh_path = path

            info = f"✅ {Path(path).name}\n"
            info += f"Vertices: {len(self.mesh.vertices):,}\n"
            info += f"Faces: {len(self.mesh.faces):,}\n"
            info += f"Area: {self.mesh.area:.2f} mm²"
            self.mesh_info_var.set(info)

            self._display_3d_mesh()
            self.status_var.set(f"✅ Loaded {Path(path).name}")

        except Exception as e:
            messagebox.showerror("Error", str(e))
            traceback.print_exc()
        finally:
            self.progress.stop()

    def _display_3d_mesh(self):
        """Show mesh in 3D view"""
        if self.mesh is None:
            return

        self.ax_3d.clear()
        vertices = self.mesh.vertices
        faces = self.mesh.faces

        self.ax_3d.plot_trisurf(vertices[:,0], vertices[:,1], vertices[:,2],
                               triangles=faces, cmap='viridis', alpha=0.9)

        bounds = self.mesh.bounds
        self.ax_3d.set_xlim(bounds[0][0], bounds[1][0])
        self.ax_3d.set_ylim(bounds[0][1], bounds[1][1])
        self.ax_3d.set_zlim(bounds[0][2], bounds[1][2])
        self.ax_3d.set_title(self.mesh_info_var.get().split('\n')[0])
        self.canvas_3d.draw()

    def _curvature_analysis(self):
        """Calculate mesh curvature"""
        if self.mesh is None:
            return

        self.progress.start()
        self.status_var.set("Calculating curvature...")

        try:
            vertices = self.mesh.vertices
            tree = KDTree(vertices)
            bbox_size = np.ptp(vertices, axis=0).max()
            radius = bbox_size * 0.05 * self.scale_var.get()

            curvature = np.zeros(len(vertices))

            for i, v in enumerate(vertices):
                neighbors = tree.query_ball_point(v, radius)
                if len(neighbors) > 3:
                    center = np.mean(vertices[neighbors], axis=0)
                    curvature[i] = np.linalg.norm(v - center)

            self.curvature_map = {'mean': curvature}

            # Color mesh by curvature
            self.ax_3d.clear()
            norm_curv = curvature / curvature.max() if curvature.max() > 0 else curvature
            colors = plt.cm.RdYlBu_r(norm_curv)

            self.ax_3d.plot_trisurf(vertices[:,0], vertices[:,1], vertices[:,2],
                                   triangles=self.mesh.faces,
                                   facecolors=colors, alpha=0.9)
            self.ax_3d.set_title("Mean Curvature (Red: High, Blue: Low)")
            self.canvas_3d.draw()

            self.status_var.set("✅ Curvature complete")

        except Exception as e:
            messagebox.showerror("Error", str(e))
            traceback.print_exc()
        finally:
            self.progress.stop()

    def _extract_profile(self):
        """Extract cross-section profile"""
        if self.mesh is None:
            return

        self.progress.start()
        self.status_var.set("Extracting profile...")

        try:
            center = self.mesh.centroid
            slice_2d = self.mesh.section(plane_origin=center, plane_normal=[0,1,0])

            if slice_2d and len(slice_2d.entities) > 0:
                slice_2d, _ = slice_2d.to_planar()

                fig, ax = plt.subplots(figsize=(8,4))
                ax.plot(slice_2d.vertices[:,0], slice_2d.vertices[:,1], 'b-', linewidth=2)
                ax.set_title("Cross-section Profile")
                ax.set_xlabel("X (mm)")
                ax.set_ylabel("Z (mm)")
                ax.grid(True)
                ax.axis('equal')
                plt.tight_layout()
                plt.show()

                self.status_var.set("✅ Profile extracted")
            else:
                messagebox.showinfo("No Intersection", "Plane does not intersect mesh")

        except Exception as e:
            messagebox.showerror("Error", str(e))
            traceback.print_exc()
        finally:
            self.progress.stop()

    def _unwrap_cylinder(self):
        """Unwrap cylindrical surface"""
        if self.mesh is None:
            return

        self.progress.start()
        self.status_var.set("Unwrapping...")

        try:
            vertices = self.mesh.vertices - self.mesh.centroid

            # Find principal axis using SVD
            from scipy.linalg import svd
            U, s, Vt = svd(vertices, full_matrices=False)
            axis = Vt[0]

            # Convert to cylindrical coordinates
            heights = []
            angles = []
            radii = []

            for v in vertices:
                h = np.dot(v, axis)
                radial = v - h * axis
                r = np.linalg.norm(radial)

                if r > 0:
                    # Project onto plane perpendicular to axis
                    basis_u = Vt[1]
                    basis_v = Vt[2]
                    u = np.dot(radial, basis_u)
                    w = np.dot(radial, basis_v)
                    angle = np.arctan2(w, u)

                    heights.append(h)
                    angles.append(angle)
                    radii.append(r)

            if heights:
                # Create scatter plot of unwrapped surface
                fig, ax = plt.subplots(figsize=(10,4))
                scatter = ax.scatter(heights, angles, c=radii, cmap='viridis',
                                    s=2, alpha=0.6)
                plt.colorbar(scatter, ax=ax, label='Radius (mm)')
                ax.set_xlabel('Height (mm)')
                ax.set_ylabel('Angle (radians)')
                ax.set_title('Unwrapped Surface')
                ax.grid(True, alpha=0.3)
                plt.tight_layout()
                plt.show()

                self.status_var.set("✅ Unwrapping complete")
            else:
                messagebox.showinfo("No Data", "Could not unwrap mesh")

        except Exception as e:
            messagebox.showerror("Error", str(e))
            traceback.print_exc()
        finally:
            self.progress.stop()

    def _detect_features(self):
        """Detect archaeological features from curvature"""
        if self.curvature_map is None:
            messagebox.showwarning("Warning", "Run curvature analysis first")
            return

        curvature = self.curvature_map['mean']
        threshold = np.percentile(curvature, 100 - self.sensitivity_var.get() * 100)
        features = curvature > threshold

        from scipy import ndimage
        labeled, count = ndimage.label(features)

        # Calculate feature sizes
        sizes = []
        for i in range(1, count+1):
            sizes.append(np.sum(labeled == i))

        self.features = {
            'count': count,
            'sizes': sizes,
            'total_points': np.sum(features)
        }

        # Visualize features
        self.ax_3d.clear()
        vertices = self.mesh.vertices
        colors = np.zeros((len(vertices), 4))
        colors[~features] = [0.8, 0.8, 0.8, 0.3]  # Gray for non-features
        colors[features] = [1, 0, 0, 0.8]  # Red for features

        self.ax_3d.plot_trisurf(vertices[:,0], vertices[:,1], vertices[:,2],
                               triangles=self.mesh.faces,
                               facecolors=colors, alpha=0.9)
        self.ax_3d.set_title(f"Detected {count} Features (Red)")
        self.canvas_3d.draw()

        messagebox.showinfo("Features Detected",
                          f"Found {count} features\n"
                          f"Largest: {max(sizes) if sizes else 0} points\n"
                          f"Total feature points: {np.sum(features)}")

    def _run_3d_analysis(self):
        """Run selected 3D analysis"""
        if self.mesh is None:
            messagebox.showwarning("No Mesh", "Load a 3D mesh first")
            return

        analysis = self.analysis_type_var.get()
        if analysis == "curvature":
            self._curvature_analysis()
        elif analysis == "profile":
            self._extract_profile()
        elif analysis == "unwrap":
            self._unwrap_cylinder()
        elif analysis == "features":
            self._detect_features()

    def _export_3d_results(self):
        """Export 3D analysis results"""
        if self.mesh is None:
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        if path:
            data = {
                'mesh_info': {
                    'path': self.mesh_path,
                    'vertices': len(self.mesh.vertices),
                    'faces': len(self.mesh.faces),
                    'area': self.mesh.area
                },
                'features': self.features,
                'timestamp': datetime.now().isoformat()
            }
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
            self.status_var.set(f"✅ Exported to {Path(path).name}")

    # ============================================================================
    # UI CONSTRUCTION
    # ============================================================================

    def open_window(self):
        """Open the main window"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            self._load_from_main_app()
            self._refresh_all_tabs()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("🔬 Virtual Microscopy Pro v4.0 - Petrography + 3D Archaeology")
        self.window.geometry("1200x750")

        self._create_interface()
        data_loaded = self._load_from_main_app()

        if data_loaded and self.mineral_data:
            self._refresh_all_tabs()
            self.status_var.set(f"✅ Loaded {len(self.samples)} samples, {len(self.mineral_data)} grains")
        else:
            self._show_empty_plot()
            self.status_var.set("ℹ️ No data - Click 'Generate Demo'")

        self.window.transient(self.app.root)
        self.window.lift()
        self.window.focus_force()

    def _create_interface(self):
        """Create the interface with all 6 tabs"""
        # Header
        header = tk.Frame(self.window, bg="#2c3e50", height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="🔬", font=("Arial", 20),
                bg="#2c3e50", fg="white").pack(side=tk.LEFT, padx=10)
        tk.Label(header, text="Virtual Microscopy Pro",
                font=("Arial", 16, "bold"),
                bg="#2c3e50", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Label(header, text="v4.0 - Petrography + 3D Archaeology",
                font=("Arial", 9),
                bg="#2c3e50", fg="#f1c40f").pack(side=tk.LEFT, padx=10)

        # Sample selector
        tk.Label(header, text="Sample:", bg="#2c3e50", fg="white").pack(side=tk.RIGHT, padx=5)
        self.sample_selector = ttk.Combobox(header, values=list(self.sample_data.keys()),
                                           width=15, state="readonly")
        self.sample_selector.pack(side=tk.RIGHT, padx=5)
        if self.sample_data:
            self.sample_selector.set(list(self.sample_data.keys())[0])
        self.sample_selector.bind('<<ComboboxSelected>>', lambda e: self._update_plot())

        # Main notebook
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Tab 1: Thin Section
        tab1 = ttk.Frame(self.notebook)
        self.notebook.add(tab1, text="📊 Thin Section")
        self._build_thin_section_tab(tab1)

        # Tab 2: Modal Analysis
        tab2 = ttk.Frame(self.notebook)
        self.notebook.add(tab2, text="📈 Modal Analysis")
        self._build_modal_tab(tab2)

        # Tab 3: Grain Size
        tab3 = ttk.Frame(self.notebook)
        self.notebook.add(tab3, text="📏 Grain Size")
        self._build_grain_size_tab(tab3)

        # Tab 4: Fabric Analysis
        tab4 = ttk.Frame(self.notebook)
        self.notebook.add(tab4, text="🧭 Fabric")
        self._build_fabric_tab(tab4)

        # Tab 5: Provenance
        tab5 = ttk.Frame(self.notebook)
        self.notebook.add(tab5, text="📍 Provenance")
        self._build_provenance_tab(tab5)

        # Tab 6: 3D Archaeology
        tab6 = ttk.Frame(self.notebook)
        self.notebook.add(tab6, text="🏛️ 3D Artifact")
        self._build_archaeology_tab(tab6)

        # Status bar
        status = tk.Frame(self.window, bg="#34495e", height=28)
        status.pack(fill=tk.X, side=tk.BOTTOM)
        status.pack_propagate(False)

        self.status_var = tk.StringVar(value="Ready")
        tk.Label(status, textvariable=self.status_var,
                font=("Arial", 8), bg="#34495e", fg="white").pack(side=tk.LEFT, padx=10)

        tk.Button(status, text="📤 Send to Main App",
                 command=self._send_results_to_main,
                 bg="#27ae60", fg="white", font=("Arial", 8, "bold"),
                 padx=10).pack(side=tk.RIGHT, padx=5)

        tk.Button(status, text="🎲 Generate Demo",
                 command=self._generate_demo,
                 bg="#f39c12", fg="white", font=("Arial", 8),
                 padx=10).pack(side=tk.RIGHT, padx=5)

        self.progress = ttk.Progressbar(status, mode='indeterminate', length=150)
        self.progress.pack(side=tk.RIGHT, padx=5)

    def _build_thin_section_tab(self, parent):
        """Build thin section tab"""
        paned = tk.PanedWindow(parent, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        left = tk.Frame(paned, bg="#f5f5f5", width=280)
        paned.add(left, width=280)
        right = tk.Frame(paned, bg="white", width=400)
        paned.add(right, width=400)

        # Left panel controls
        toggle_frame = tk.LabelFrame(left, text="Show Minerals", padx=5, pady=5, bg="#f5f5f5")
        toggle_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        canvas = tk.Canvas(toggle_frame, bg="#f5f5f5", highlightthickness=0)
        scrollbar = tk.Scrollbar(toggle_frame, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas, bg="#f5f5f5")

        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        self.mineral_vars = {}
        for mineral in sorted(self.MINERAL_DATABASE.keys()):
            if mineral != 'void':
                var = tk.BooleanVar(value=True)
                self.mineral_vars[mineral] = var
                frame = tk.Frame(scrollable, bg="#f5f5f5")
                frame.pack(fill=tk.X, pady=1)
                tk.Checkbutton(frame, text=mineral.capitalize(), variable=var,
                             bg="#f5f5f5", font=("Arial", 8)).pack(side=tk.LEFT)
                color = self.MINERAL_DATABASE[mineral]['color']
                hex_color = '#%02x%02x%02x' % (int(color[0]*255), int(color[1]*255), int(color[2]*255))
                preview = tk.Canvas(frame, width=12, height=12, bg=hex_color,
                                   highlightthickness=1, highlightbackground="black")
                preview.pack(side=tk.RIGHT, padx=2)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        btn_frame = tk.Frame(left, bg="#f5f5f5")
        btn_frame.pack(fill=tk.X, padx=5, pady=2)
        tk.Button(btn_frame, text="All", command=lambda: self._set_all_minerals(True),
                 width=6).pack(side=tk.LEFT, padx=1)
        tk.Button(btn_frame, text="None", command=lambda: self._set_all_minerals(False),
                 width=6).pack(side=tk.LEFT, padx=1)
        tk.Button(btn_frame, text="Apply", command=self._update_plot,
                 bg="#27ae60", fg="white", width=8).pack(side=tk.RIGHT)

        disp_frame = tk.LabelFrame(left, text="Display", padx=5, pady=5, bg="#f5f5f5")
        disp_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(disp_frame, text="Size:").pack(anchor=tk.W)
        self.size_var = tk.DoubleVar(value=30)
        tk.Scale(disp_frame, from_=5, to=100, orient=tk.HORIZONTAL,
                variable=self.size_var, command=lambda x: self._update_plot()).pack(fill=tk.X)
        tk.Label(disp_frame, text="Opacity:").pack(anchor=tk.W)
        self.alpha_var = tk.DoubleVar(value=0.7)
        tk.Scale(disp_frame, from_=0.1, to=1.0, resolution=0.1,
                variable=self.alpha_var, command=lambda x: self._update_plot()).pack(fill=tk.X)

        # Right panel plot
        self.fig = plt.Figure(figsize=(4.5, 4), dpi=90)
        self.ax = self.fig.add_subplot(111)
        self.fig.patch.set_facecolor('white')
        self.ax.set_facecolor('#f8f9fa')

        self.canvas = FigureCanvasTkAgg(self.fig, right)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2Tk(self.canvas, right)
        toolbar.update()

        self._update_plot()

    def _build_modal_tab(self, parent):
        """Build modal analysis tab"""
        paned = tk.PanedWindow(parent, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        left = tk.Frame(paned, bg="white")
        paned.add(left, width=350)
        right = tk.Frame(paned, bg="white")
        paned.add(right, width=400)

        tk.Label(left, text="Modal Analysis (Point Counting)",
                font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=5, pady=5)
        tree_frame = tk.Frame(left)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.modal_tree = ttk.Treeview(tree_frame, columns=('Mineral', 'Count', '%'),
                                       show='headings', height=12)
        self.modal_tree.heading('Mineral', text='Mineral')
        self.modal_tree.heading('Count', text='Count')
        self.modal_tree.heading('%', text='%')
        self.modal_tree.column('Mineral', width=130)
        self.modal_tree.column('Count', width=60, anchor='center')
        self.modal_tree.column('%', width=60, anchor='center')

        scrollbar = ttk.Scrollbar(tree_frame, command=self.modal_tree.yview)
        self.modal_tree.configure(yscrollcommand=scrollbar.set)
        self.modal_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.rock_type_var = tk.StringVar(value="Rock Type: Not classified")
        tk.Label(left, textvariable=self.rock_type_var,
                font=("Arial", 10, "bold"), fg="#27ae60").pack(anchor=tk.W, padx=5, pady=5)
        tk.Button(left, text="🔄 Update", command=self._update_modal_tab,
                 bg="#3498db", fg="white").pack(pady=5)

        # QAPF plot
        self.qapf_fig = plt.Figure(figsize=(4, 4), dpi=90)
        self.qapf_ax = self.qapf_fig.add_subplot(111)
        self.qapf_canvas = FigureCanvasTkAgg(self.qapf_fig, right)
        self.qapf_canvas.draw()
        self.qapf_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self._update_qapf_plot()

    def _build_grain_size_tab(self, parent):
        """Build grain size tab"""
        paned = tk.PanedWindow(parent, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        left = tk.Frame(paned, bg="white")
        paned.add(left, width=280)
        right = tk.Frame(paned, bg="white")
        paned.add(right, width=450)

        tk.Label(left, text="Grain Size Statistics",
                font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=5, pady=5)
        self.size_stats_text = tk.Text(left, height=20, width=32,
                                       font=("Courier", 8), bg="#f8f9fa")
        self.size_stats_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        tk.Button(left, text="📊 Analyze", command=self._update_grain_size_tab,
                 bg="#27ae60", fg="white").pack(pady=5)

        self.size_fig = plt.Figure(figsize=(5, 4), dpi=90)
        self.size_ax = self.size_fig.add_subplot(111)
        self.size_canvas = FigureCanvasTkAgg(self.size_fig, right)
        self.size_canvas.draw()
        self.size_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _build_fabric_tab(self, parent):
        """Build fabric tab"""
        paned = tk.PanedWindow(parent, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        left = tk.Frame(paned, bg="white")
        paned.add(left, width=280)
        right = tk.Frame(paned, bg="white")
        paned.add(right, width=450)

        tk.Label(left, text="Fabric Analysis",
                font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=5, pady=5)
        self.fabric_stats_text = tk.Text(left, height=15, width=32,
                                         font=("Courier", 8), bg="#f8f9fa")
        self.fabric_stats_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        tk.Button(left, text="🧭 Analyze", command=self._update_fabric_tab,
                 bg="#9b59b6", fg="white").pack(pady=5)

        self.fabric_fig = plt.Figure(figsize=(4.5, 4), dpi=90)
        self.fabric_ax = self.fabric_fig.add_subplot(111, projection='polar')
        self.fabric_canvas = FigureCanvasTkAgg(self.fabric_fig, right)
        self.fabric_canvas.draw()
        self.fabric_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _build_provenance_tab(self, parent):
        """Build provenance tab"""
        paned = tk.PanedWindow(parent, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        left = tk.Frame(paned, bg="white")
        paned.add(left, width=320)
        right = tk.Frame(paned, bg="white")
        paned.add(right, width=450)

        tk.Label(left, text="Samples from Main App",
                font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=5, pady=5)
        tree_frame = tk.Frame(left)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.prov_tree = ttk.Treeview(tree_frame, columns=('Rock Type', 'Q', 'A', 'P'),
                                      show='headings', height=16)
        self.prov_tree.heading('#0', text='Sample ID')
        self.prov_tree.heading('Rock Type', text='Rock Type')
        self.prov_tree.heading('Q', text='Q%')
        self.prov_tree.heading('A', text='A%')
        self.prov_tree.heading('P', text='P%')
        self.prov_tree.column('#0', width=100)
        self.prov_tree.column('Rock Type', width=100)
        self.prov_tree.column('Q', width=40, anchor='center')
        self.prov_tree.column('A', width=40, anchor='center')
        self.prov_tree.column('P', width=40, anchor='center')

        scrollbar = ttk.Scrollbar(tree_frame, command=self.prov_tree.yview)
        self.prov_tree.configure(yscrollcommand=scrollbar.set)
        self.prov_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        tk.Label(right, text="Mineral Assemblage by Sample",
                font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=5, pady=5)
        self.assemblage_text = tk.Text(right, wrap=tk.WORD,
                                       font=("Courier", 8), bg="#f8f9fa", height=20)
        self.assemblage_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.prov_tree.bind('<<TreeviewSelect>>', self._on_sample_select)
        self._update_provenance_tree()

    def _build_archaeology_tab(self, parent):
        """Build 3D archaeology tab"""
        paned = tk.PanedWindow(parent, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        left = tk.Frame(paned, bg="#f5f5f5", width=300)
        paned.add(left, width=300)
        right = tk.Frame(paned, bg="white")
        paned.add(right, width=600)

        # Left panel controls
        file_frame = tk.LabelFrame(left, text="📂 Mesh File", padx=5, pady=5, bg="#f5f5f5")
        file_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Button(file_frame, text="Load 3D Mesh (STL/OBJ/PLY)",
                 command=self._load_3d_mesh,
                 bg="#3498db", fg="white").pack(fill=tk.X, pady=2)

        self.mesh_info_var = tk.StringVar(value="No mesh loaded")
        tk.Label(file_frame, textvariable=self.mesh_info_var,
                font=("Arial", 8), bg="#f5f5f5", justify=tk.LEFT).pack()

        analysis_frame = tk.LabelFrame(left, text="🔍 Analysis", padx=5, pady=5, bg="#f5f5f5")
        analysis_frame.pack(fill=tk.X, padx=5, pady=5)

        self.analysis_type_var = tk.StringVar(value="curvature")
        analyses = [
            ("Curvature Analysis", "curvature"),
            ("Profile Extraction", "profile"),
            ("Unwrap Cylinder", "unwrap"),
            ("Feature Detection", "features")
        ]
        for text, value in analyses:
            tk.Radiobutton(analysis_frame, text=text, variable=self.analysis_type_var,
                          value=value, bg="#f5f5f5").pack(anchor=tk.W)

        param_frame = tk.LabelFrame(left, text="⚙️ Parameters", padx=5, pady=5, bg="#f5f5f5")
        param_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(param_frame, text="Scale:").pack(anchor=tk.W)
        self.scale_var = tk.DoubleVar(value=1.0)
        tk.Scale(param_frame, from_=0.1, to=5.0, resolution=0.1,
                orient=tk.HORIZONTAL, variable=self.scale_var).pack(fill=tk.X)
        tk.Label(param_frame, text="Sensitivity:").pack(anchor=tk.W)
        self.sensitivity_var = tk.DoubleVar(value=0.5)
        tk.Scale(param_frame, from_=0.0, to=1.0, resolution=0.05,
                orient=tk.HORIZONTAL, variable=self.sensitivity_var).pack(fill=tk.X)

        tk.Button(left, text="▶ Run Analysis",
                 command=self._run_3d_analysis,
                 bg="#e67e22", fg="white", font=("Arial", 10, "bold"),
                 height=2).pack(fill=tk.X, padx=5, pady=10)

        tk.Button(left, text="📤 Export Results",
                 command=self._export_3d_results,
                 bg="#27ae60", fg="white").pack(fill=tk.X, padx=5, pady=2)

        # Right panel 3D view
        self.fig_3d = plt.Figure(figsize=(5, 4.5), dpi=90)
        self.ax_3d = self.fig_3d.add_subplot(111, projection='3d')
        self.ax_3d.set_facecolor('#f8f9fa')

        self.canvas_3d = FigureCanvasTkAgg(self.fig_3d, right)
        self.canvas_3d.draw()
        self.canvas_3d.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        toolbar_frame = tk.Frame(right)
        toolbar_frame.pack(fill=tk.X)
        toolbar = NavigationToolbar2Tk(self.canvas_3d, toolbar_frame)
        toolbar.update()

    def _show_empty_plot(self):
        """Show empty plot"""
        self.ax.clear()
        self.ax.text(0.5, 0.5, "No data loaded\nClick 'Generate Demo'",
                    ha='center', va='center', transform=self.ax.transAxes,
                    fontsize=10, color='gray')
        self.ax.set_axis_off()
        self.canvas.draw()

    def _update_plot(self):
        """Update thin section plot"""
        if not self.mineral_data or len(self.mineral_data) == 0:
            self._show_empty_plot()
            return

        self.ax.clear()
        selected = self.sample_selector.get()

        if selected and selected in self.sample_data:
            grains = [g for g in self.mineral_data if g.get('sample_id') == selected]
        else:
            grains = self.mineral_data

        filtered = []
        for grain in grains:
            mineral = grain.get('type', 'unknown')
            if mineral in self.mineral_vars and self.mineral_vars[mineral].get():
                filtered.append(grain)

        if not filtered:
            self.ax.text(0.5, 0.5, "No minerals selected",
                        ha='center', va='center', transform=self.ax.transAxes)
        else:
            x = [g['x'] for g in filtered]
            y = [g['y'] for g in filtered]
            colors = []
            sizes = []

            for grain in filtered:
                mineral = grain['type']
                color = self.MINERAL_DATABASE.get(mineral, {}).get('color', [0.5, 0.5, 0.5])
                colors.append(color)
                sizes.append(grain['size'] * self.size_var.get())

            self.ax.scatter(x, y, s=sizes, c=colors, alpha=self.alpha_var.get(),
                          edgecolors='black', linewidths=0.3)

            self.ax.set_xlabel('X Position (μm)')
            self.ax.set_ylabel('Y Position (μm)')
            self.ax.set_title(f'Thin Section - {selected if selected else "All"}')
            self.ax.set_aspect('equal')
            self.ax.grid(True, alpha=0.3)

        self.canvas.draw()

    def _update_qapf_plot(self):
        """Update QAPF ternary diagram"""
        self.qapf_ax.clear()
        self.qapf_ax.plot([0, 100, 50, 0], [0, 0, 86.6, 0], 'k-', linewidth=1)
        self.qapf_ax.text(0, -5, 'Q', ha='center', fontsize=10, fontweight='bold')
        self.qapf_ax.text(100, -5, 'A', ha='center', fontsize=10, fontweight='bold')
        self.qapf_ax.text(50, 90, 'P', ha='center', fontsize=10, fontweight='bold')

        selected = self.sample_selector.get()
        for sample_id, qapf in self.qapf_values.items():
            q = qapf.get('Q', 0)
            a = qapf.get('A', 0)
            p = qapf.get('P', 0)
            total = q + a + p
            if total > 0:
                q_norm = q / total * 100
                a_norm = a / total * 100
                p_norm = p / total * 100
                x = p_norm * 0.5 + q_norm
                y = p_norm * 0.866
                color = 'red' if sample_id == selected else 'blue'
                alpha = 0.9 if sample_id == selected else 0.5
                size = 60 if sample_id == selected else 30
                self.qapf_ax.scatter(x, y, c=color, s=size, alpha=alpha,
                                    edgecolors='black', linewidth=0.5)

        self.qapf_ax.set_xlim(-10, 110)
        self.qapf_ax.set_ylim(-10, 100)
        self.qapf_ax.set_aspect('equal')
        self.qapf_ax.axis('off')
        self.qapf_canvas.draw()

    def _update_modal_tab(self):
        """Update modal analysis tab"""
        selected = self.sample_selector.get()
        modal = self._point_count_modal(selected)

        for item in self.modal_tree.get_children():
            self.modal_tree.delete(item)

        if modal:
            total = sum(modal.values())
            for mineral, pct in sorted(modal.items(), key=lambda x: x[1], reverse=True):
                count = int(pct * total / 100) if total > 0 else 0
                self.modal_tree.insert('', tk.END, values=(
                    mineral.capitalize(),
                    count,
                    f"{pct:.1f}"
                ))
            if selected in self.rock_classification:
                self.rock_type_var.set(f"Rock Type: {self.rock_classification[selected]}")
            else:
                self.rock_type_var.set("Rock Type: Not classified")

        self._update_qapf_plot()

    def _update_grain_size_tab(self):
        """Update grain size tab"""
        selected = self.sample_selector.get()
        stats = self._analyze_grain_size(selected)

        self.size_stats_text.delete(1.0, tk.END)

        if stats:
            text = f"""GRAIN SIZE STATISTICS (Folk & Ward, 1957)
{'='*40}

Sample: {selected if selected else 'All'}
Count: {stats['count']} grains

MEASURES (μm):
Mean:       {stats['mean']:.2f}
Median:     {stats['median']:.2f}
Sorting:    {stats['sorting']:.3f}
Skewness:   {stats['skewness']:.3f}
Kurtosis:   {stats['kurtosis']:.3f}

WENTWORTH CLASS:
{stats['wentworth']}

PERCENTILES:
φ5:   {stats['percentiles']['5']:.2f}
φ16:  {stats['percentiles']['16']:.2f}
φ25:  {stats['percentiles']['25']:.2f}
φ50:  {stats['percentiles']['50']:.2f}
φ75:  {stats['percentiles']['75']:.2f}
φ84:  {stats['percentiles']['84']:.2f}
φ95:  {stats['percentiles']['95']:.2f}

INTERPRETATION:
{self._interpret_sorting(stats['sorting'])}
"""
            self.size_stats_text.insert(1.0, text)

            self.size_ax.clear()
            grains = [g for g in self.mineral_data if g.get('sample_id') == selected] if selected else self.mineral_data
            sizes = [g['size'] for g in grains]

            self.size_ax.hist(sizes, bins=15, alpha=0.7, color='skyblue', edgecolor='black')
            self.size_ax.axvline(stats['mean'], color='red', linestyle='--', label=f"Mean: {stats['mean']:.1f}")
            self.size_ax.axvline(stats['median'], color='green', linestyle='--', label=f"Median: {stats['median']:.1f}")
            self.size_ax.set_xlabel('Grain Size (μm)')
            self.size_ax.set_ylabel('Frequency')
            self.size_ax.set_title('Grain Size Distribution')
            self.size_ax.legend()
            self.size_ax.grid(True, alpha=0.3)
            self.size_canvas.draw()

    def _interpret_sorting(self, sorting):
        """Interpret sorting coefficient"""
        if sorting < 0.35:
            return "Very well sorted"
        elif sorting < 0.5:
            return "Well sorted"
        elif sorting < 1.0:
            return "Moderately sorted"
        elif sorting < 2.0:
            return "Poorly sorted"
        else:
            return "Very poorly sorted"

    def _update_fabric_tab(self):
        """Update fabric tab"""
        selected = self.sample_selector.get()
        fabric = self._analyze_fabric(selected)

        self.fabric_stats_text.delete(1.0, tk.END)

        if fabric:
            text = f"""FABRIC ANALYSIS (Woodcock, 1977)
{'='*40}

Sample: {selected if selected else 'All'}
Grains: {fabric['n_grains']}

Mean resultant vector (R): {fabric['R']:.3f}
Mean orientation: {fabric['mean_angle']:.1f}°

Fabric strength: {fabric['fabric_type']}

INTERPRETATION:
{fabric['fabric_type']} preferred orientation
"""
            self.fabric_stats_text.insert(1.0, text)

            self.fabric_ax.clear()
            grains = [g for g in self.mineral_data if g.get('sample_id') == selected] if selected else self.mineral_data
            angles = [g.get('angle', 0) for g in grains]
            angles_rad = np.radians(angles)

            nbins = 12
            theta = np.linspace(0, 2*np.pi, nbins+1)
            counts, _ = np.histogram(angles_rad, bins=theta)

            self.fabric_ax.bar(theta[:-1], counts, width=2*np.pi/nbins,
                              alpha=0.7, color='steelblue', edgecolor='black')
            self.fabric_ax.set_theta_zero_location('N')
            self.fabric_ax.set_theta_direction(-1)
            self.fabric_ax.set_title('Grain Orientation')
            self.fabric_canvas.draw()

    def _update_provenance_tree(self):
        """Update provenance tree"""
        for item in self.prov_tree.get_children():
            self.prov_tree.delete(item)

        for sample_id in self.sample_data.keys():
            qapf = self.qapf_values.get(sample_id, {})
            rock_type = self.rock_classification.get(sample_id, 'Unknown')
            self.prov_tree.insert('', tk.END, text=sample_id,
                                 values=(rock_type,
                                        f"{qapf.get('Q', 0):.0f}",
                                        f"{qapf.get('A', 0):.0f}",
                                        f"{qapf.get('P', 0):.0f}"))

    def _on_sample_select(self, event):
        """Handle sample selection"""
        selection = self.prov_tree.selection()
        if not selection:
            return

        item = selection[0]
        sample_id = self.prov_tree.item(item, 'text')
        modal = self._point_count_modal(sample_id)

        self.assemblage_text.delete(1.0, tk.END)
        if modal:
            text = f"MINERAL ASSEMBLAGE: {sample_id}\n{'='*40}\n\n"
            for mineral, pct in sorted(modal.items(), key=lambda x: x[1], reverse=True):
                props = self.MINERAL_DATABASE.get(mineral, {})
                formula = props.get('formula', '')
                text += f"{mineral.capitalize():12} {pct:5.1f}%  {formula}\n"
            text += f"\nRock Type: {self.rock_classification.get(sample_id, 'Unknown')}"
            self.assemblage_text.insert(1.0, text)

    def _set_all_minerals(self, value):
        """Set all mineral checkboxes"""
        for var in self.mineral_vars.values():
            var.set(value)
        self._update_plot()

    def _generate_demo(self):
        """Generate demo data"""
        self.progress.start()
        self.status_var.set("Generating demo data...")

        demo_samples = []
        for i in range(5):
            sample = {
                'Sample_ID': f"DEMO_{i+1:03d}",
                'SiO2': np.random.uniform(45, 75),
                'Al2O3': np.random.uniform(10, 18),
                'Fe2O3': np.random.uniform(1, 10),
                'MgO': np.random.uniform(0.5, 8),
                'CaO': np.random.uniform(1, 12),
                'Na2O': np.random.uniform(2, 5),
                'K2O': np.random.uniform(0.5, 5),
                'TiO2': np.random.uniform(0.1, 2),
                'P2O5': np.random.uniform(0.1, 1),
                'Latitude': 32 + np.random.uniform(-1, 1),
                'Longitude': 35 + np.random.uniform(-1, 1)
            }
            demo_samples.append(sample)

        self.samples = pd.DataFrame(demo_samples)
        self.sample_data = {s['Sample_ID']: s for s in demo_samples}
        self._detect_geochemical_columns()
        self._generate_from_geochemistry()

        self.sample_selector['values'] = list(self.sample_data.keys())
        if self.sample_data:
            self.sample_selector.set(list(self.sample_data.keys())[0])

        self._refresh_all_tabs()
        self.progress.stop()
        self.status_var.set(f"✅ Generated demo with {len(self.sample_data)} samples")


def setup_plugin(main_app):
    """Plugin setup function"""
    plugin = VirtualMicroscopyProPlugin(main_app)
    return plugin
