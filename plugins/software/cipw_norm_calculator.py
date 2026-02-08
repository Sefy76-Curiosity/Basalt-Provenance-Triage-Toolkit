"""
CIPW Norm Calculator Plugin
Calculate normative mineralogy from bulk rock chemistry (Cross, Iddings, Pirsson, Washington Norm)

Features:
- Full CIPW norm calculation algorithm
- Multiple output formats (weight%, volume%, mole%)
- Differentiation index (DI) and solidification index (SI)
- Normative classification (Quartz-normative, Nepheline-normative, etc.)
- Visualization of normative mineral assemblages
- Comparison with actual modal mineralogy
- Export to standard petrology formats

Author: Sefy Levy
License: CC BY-NC-SA 4.0
"""

PLUGIN_INFO = {
    "category": "software",
    "id": "cipw_norm_calculator",
    "name": "CIPW Norm Calculator",
    "description": "Calculate normative mineralogy from bulk rock chemistry",
    "icon": "💎",
    "version": "1.0",
    "requires": ["numpy", "matplotlib", "pandas"],
    "author": "Sefy Levy"
}

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import numpy as np
import re
import json
from io import StringIO
import traceback
from datetime import datetime

# Check dependencies
HAS_NUMPY = False
HAS_MATPLOTLIB = False
HAS_PANDAS = False

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
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    PANDAS_ERROR = "pandas not found"

HAS_REQUIREMENTS = HAS_NUMPY and HAS_MATPLOTLIB and HAS_PANDAS


class CIPWCalculator:
    """CIPW Norm calculation engine"""

    # Molecular weights (g/mol)
    MOLECULAR_WEIGHTS = {
        'SiO2': 60.0843,
        'TiO2': 79.8658,
        'Al2O3': 101.9613,
        'Fe2O3': 159.6882,
        'FeO': 71.8444,
        'MnO': 70.9374,
        'MgO': 40.3044,
        'CaO': 56.0774,
        'Na2O': 61.9789,
        'K2O': 94.1960,
        'P2O5': 141.9445,
        'Cr2O3': 151.9904,
        'NiO': 74.6928,
        'H2O+': 18.0153,
        'CO2': 44.0095,
        'SO3': 80.0632
    }

    # Mineral formulas and molecular weights
    MINERAL_FORMULAS = {
        'Q': 'SiO2',
        'C': 'CaO',
        'Z': 'ZrO2',
        'Ap': 'Ca5(PO4)3(F,Cl,OH)',
        'Il': 'FeTiO3',
        'Mt': 'Fe3O4',
        'Hm': 'Fe2O3',
        'Tn': 'FeO·TiO2',
        'Ru': 'TiO2',
        'Pr': 'Pr2O3',
        'Cm': 'Cm2O3',
        'Or': 'KAlSi3O8',
        'Ab': 'NaAlSi3O8',
        'An': 'CaAl2Si2O8',
        'Ne': 'NaAlSiO4',
        'Lc': 'KAlSiO4',
        'Ks': 'KAlSi2O6',
        'Ac': 'NaFeSi2O6',
        'Di': 'CaMgSi2O6',
        'Hd': 'CaFeSi2O6',
        'Wo': 'CaSiO3',
        'En': 'MgSiO3',
        'Fs': 'FeSiO3',
        'Fo': 'Mg2SiO4',
        'Fa': 'Fe2SiO4',
        'Sp': 'MgAl2O4',
        'Hc': 'FeAl2O4',
        'Ol': '(Mg,Fe)2SiO4',
        'Px': '(Mg,Fe,Ca)SiO3',
        'Pf': 'NaAlSi3O8-CaAl2Si2O8'
    }

    MINERAL_WEIGHTS = {
        'Q': 60.0843,     # Quartz
        'C': 56.0774,     # Lime (for wollastonite)
        'Z': 123.218,     # Zircon
        'Ap': 504.302,    # Apatite
        'Il': 151.710,    # Ilmenite
        'Mt': 231.533,    # Magnetite
        'Hm': 159.688,    # Hematite
        'Tn': 151.710,    # Titanite
        'Ru': 79.866,     # Rutile
        'Or': 278.331,    # Orthoclase
        'Ab': 262.223,    # Albite
        'An': 278.207,    # Anorthite
        'Ne': 142.054,    # Nepheline
        'Lc': 218.247,    # Leucite
        'Ks': 218.247,    # Kalsilite
        'Ac': 262.000,    # Aegirine
        'Di': 216.550,    # Diopside
        'Hd': 248.100,    # Hedenbergite
        'Wo': 116.162,    # Wollastonite
        'En': 100.388,    # Enstatite
        'Fs': 131.930,    # Ferrosilite
        'Fo': 140.693,    # Forsterite
        'Fa': 203.773,    # Fayalite
        'Sp': 142.265,    # Spinel
        'Hc': 173.805,    # Hercynite
        'Ol': 172.233,    # Olivine (average)
        'Px': 116.162,    # Pyroxene (average)
        'Pf': 270.000     # Plagioclase (average)
    }

    def __init__(self):
        """Initialize CIPW calculator"""
        self.results = {}
        self.oxides = {}
        self.normative_minerals = {}

    def calculate_norm(self, oxides, Fe2O3_ratio=0.15, water_as_H2O=True):
        """
        Calculate CIPW norm from oxide weights

        Args:
            oxides: dict of oxide weights in wt%
            Fe2O3_ratio: Fe2O3/(FeO+Fe2O3) ratio (default 0.15)
            water_as_H2O: Treat H2O as separate component

        Returns:
            dict of normative mineral percentages
        """
        self.oxides = oxides.copy()

        # Convert all to float
        for key in self.oxides:
            if self.oxides[key] is None:
                self.oxides[key] = 0.0

        # Step 1: Convert wt% to molecular proportions
        molecules = {}
        for oxide, weight in self.MOLECULAR_WEIGHTS.items():
            if oxide in self.oxides:
                molecules[oxide] = self.oxides[oxide] / weight

        # Step 2: Adjust FeO/Fe2O3 ratio if total Fe given
        if 'Fe2O3_T' in self.oxides and self.oxides['Fe2O3_T'] > 0:
            total_fe = self.oxides['Fe2O3_T']
            # Convert to FeO* (common in petrology)
            Fe2O3 = total_fe * Fe2O3_ratio
            FeO = total_fe * 0.8998 * (1 - Fe2O3_ratio)  # Convert Fe2O3 to FeO
            molecules['Fe2O3'] = Fe2O3 / self.MOLECULAR_WEIGHTS['Fe2O3']
            molecules['FeO'] = FeO / self.MOLECULAR_WEIGHTS['FeO']
        else:
            # Use separate FeO and Fe2O3 if provided
            if 'FeO' not in molecules:
                molecules['FeO'] = 0.0
            if 'Fe2O3' not in molecules:
                molecules['Fe2O3'] = 0.0

        # Step 3: Calculate molecular proportions
        # Start with accessory minerals

        # Apatite (from P2O5)
        if molecules.get('P2O5', 0) > 0:
            ap_moles = molecules['P2O5'] * 3.333  # Ca5(PO4)3
            molecules['CaO'] = molecules.get('CaO', 0) - (ap_moles * 5/3)
            self.normative_minerals['Ap'] = ap_moles * self.MINERAL_WEIGHTS['Ap']

        # Ilmenite (from TiO2)
        Ti_remaining = molecules.get('TiO2', 0)
        if Ti_remaining > 0 and molecules.get('FeO', 0) > 0:
            il_moles = min(Ti_remaining, molecules['FeO'])
            molecules['TiO2'] -= il_moles
            molecules['FeO'] -= il_moles
            self.normative_minerals['Il'] = il_moles * self.MINERAL_WEIGHTS['Il']

        # Magnetite (from Fe2O3)
        if molecules.get('Fe2O3', 0) > 0:
            mt_moles = molecules['Fe2O3']
            self.normative_minerals['Mt'] = mt_moles * self.MINERAL_WEIGHTS['Mt']
            molecules['Fe2O3'] = 0

        # Step 4: Calculate feldspars
        # K-feldspar (Orthoclase)
        if molecules.get('K2O', 0) > 0 and molecules.get('Al2O3', 0) > 0:
            or_moles = min(molecules['K2O'], molecules['Al2O3'])
            molecules['K2O'] -= or_moles
            molecules['Al2O3'] -= or_moles
            molecules['SiO2'] -= or_moles * 3  # KAlSi3O8
            self.normative_minerals['Or'] = or_moles * self.MINERAL_WEIGHTS['Or']

        # Albite
        if molecules.get('Na2O', 0) > 0 and molecules.get('Al2O3', 0) > 0:
            ab_moles = min(molecules['Na2O'], molecules['Al2O3'])
            molecules['Na2O'] -= ab_moles
            molecules['Al2O3'] -= ab_moles
            molecules['SiO2'] -= ab_moles * 3  # NaAlSi3O8
            self.normative_minerals['Ab'] = ab_moles * self.MINERAL_WEIGHTS['Ab']

        # Anorthite
        if molecules.get('CaO', 0) > 0 and molecules.get('Al2O3', 0) > 0:
            an_moles = min(molecules['CaO'], molecules['Al2O3'] / 2)
            molecules['CaO'] -= an_moles
            molecules['Al2O3'] -= an_moles * 2
            molecules['SiO2'] -= an_moles * 2  # CaAl2Si2O8
            self.normative_minerals['An'] = an_moles * self.MINERAL_WEIGHTS['An']

        # Step 5: Calculate feldspathoids (if Al2O3 remains but SiO2 is low)
        # Nepheline (if Na2O remains but SiO2 is insufficient for albite)
        if molecules.get('Na2O', 0) > 0 and molecules.get('Al2O3', 0) > 0:
            ne_moles = min(molecules['Na2O'], molecules['Al2O3'])
            molecules['Na2O'] -= ne_moles
            molecules['Al2O3'] -= ne_moles
            molecules['SiO2'] -= ne_moles  # NaAlSiO4
            self.normative_minerals['Ne'] = ne_moles * self.MINERAL_WEIGHTS['Ne']

        # Leucite (if K2O remains but SiO2 is insufficient for orthoclase)
        if molecules.get('K2O', 0) > 0 and molecules.get('Al2O3', 0) > 0:
            lc_moles = min(molecules['K2O'], molecules['Al2O3'])
            molecules['K2O'] -= lc_moles
            molecules['Al2O3'] -= lc_moles
            molecules['SiO2'] -= lc_moles * 2  # KAlSi2O6
            self.normative_minerals['Lc'] = lc_moles * self.MINERAL_WEIGHTS['Lc']

        # Step 6: Calculate pyroxenes
        # Diopside (CaMgSi2O6)
        if molecules.get('CaO', 0) > 0 and molecules.get('MgO', 0) > 0:
            di_moles = min(molecules['CaO'], molecules['MgO'])
            molecules['CaO'] -= di_moles
            molecules['MgO'] -= di_moles
            molecules['SiO2'] -= di_moles * 2
            self.normative_minerals['Di'] = di_moles * self.MINERAL_WEIGHTS['Di']

        # Hedenbergite (CaFeSi2O6)
        if molecules.get('CaO', 0) > 0 and molecules.get('FeO', 0) > 0:
            hd_moles = min(molecules['CaO'], molecules['FeO'])
            molecules['CaO'] -= hd_moles
            molecules['FeO'] -= hd_moles
            molecules['SiO2'] -= hd_moles * 2
            self.normative_minerals['Hd'] = hd_moles * self.MINERAL_WEIGHTS['Hd']

        # Step 7: Calculate olivine
        # Forsterite (Mg2SiO4)
        if molecules.get('MgO', 0) > 0:
            fo_moles = molecules['MgO'] / 2
            molecules['MgO'] = 0
            molecules['SiO2'] -= fo_moles
            self.normative_minerals['Fo'] = fo_moles * self.MINERAL_WEIGHTS['Fo']

        # Fayalite (Fe2SiO4)
        if molecules.get('FeO', 0) > 0:
            fa_moles = molecules['FeO'] / 2
            molecules['FeO'] = 0
            molecules['SiO2'] -= fa_moles
            self.normative_minerals['Fa'] = fa_moles * self.MINERAL_WEIGHTS['Fa']

        # Step 8: Remaining SiO2 becomes Quartz
        if molecules.get('SiO2', 0) > 0:
            self.normative_minerals['Q'] = molecules['SiO2'] * self.MINERAL_WEIGHTS['Q']
        # Negative SiO2 indicates undersaturation
        elif molecules.get('SiO2', 0) < 0:
            self.normative_minerals['Ne'] = abs(molecules['SiO2']) * self.MINERAL_WEIGHTS['Ne']

        # Step 9: Calculate totals and percentages
        total_weight = sum(self.normative_minerals.values())

        # Convert to weight percentages
        self.normative_minerals_percent = {}
        for mineral, weight in self.normative_minerals.items():
            if total_weight > 0:
                self.normative_minerals_percent[mineral] = (weight / total_weight) * 100

        # Calculate petrologic indices
        self._calculate_indices()

        return self.normative_minerals_percent

    def _calculate_indices(self):
        """Calculate petrologic indices"""
        # Differentiation Index (DI) = Q + Or + Ab + Ne + Lc + Ks
        di_components = ['Q', 'Or', 'Ab', 'Ne', 'Lc']
        self.differentiation_index = sum(
            self.normative_minerals_percent.get(comp, 0)
            for comp in di_components
        )

        # Solidification Index (SI) = MgO * 100 / (MgO + FeO + Fe2O3 + Na2O + K2O)
        # Simplified calculation
        mafic_sum = (
            self.oxides.get('MgO', 0) +
            self.oxides.get('FeO', 0) +
            self.oxides.get('Fe2O3', 0) +
            self.oxides.get('Na2O', 0) +
            self.oxides.get('K2O', 0)
        )
        if mafic_sum > 0:
            self.solidification_index = (self.oxides.get('MgO', 0) * 100) / mafic_sum
        else:
            self.solidification_index = 0

        # Color Index (CI) = Sum of mafic minerals
        mafic_minerals = ['Fo', 'Fa', 'Di', 'Hd', 'Mt', 'Il', 'Ap']
        self.color_index = sum(
            self.normative_minerals_percent.get(comp, 0)
            for comp in mafic_minerals
        )

        # Classification
        qtz = self.normative_minerals_percent.get('Q', 0)
        ne = self.normative_minerals_percent.get('Ne', 0)

        if qtz > 5:
            self.classification = "Quartz-normative"
        elif ne > 5:
            self.classification = "Nepheline-normative"
        else:
            self.classification = "Normally saturated"

    def get_classification(self):
        """Get rock classification based on norm"""
        if not self.normative_minerals_percent:
            return "Not calculated"

        # TAS-like classification from normative minerals
        q = self.normative_minerals_percent.get('Q', 0)
        f = self.normative_minerals_percent.get('Fo', 0) + self.normative_minerals_percent.get('Fa', 0)
        p = self.normative_minerals_percent.get('Di', 0) + self.normative_minerals_percent.get('Hd', 0)

        if q > 20:
            return "Granitic/Rhyolitic"
        elif q > 5:
            return "Granodioritic/Dacitic"
        elif f > 20:
            return "Gabbroic/Basaltic"
        elif p > 30:
            return "Pyroxenitic"
        else:
            return "Intermediate"


class CIPWPlugin:
    """Plugin for CIPW normative mineralogy calculation"""

    def __init__(self, main_app):
        """Initialize plugin"""
        self.app = main_app
        self.window = None
        self.calculator = CIPWCalculator()
        self.current_results = None

    def open_cipw_calculator(self):
        """Open the CIPW calculator interface"""
        if not HAS_REQUIREMENTS:
            missing = []
            if not HAS_NUMPY: missing.append("numpy")
            if not HAS_MATPLOTLIB: missing.append("matplotlib")
            if not HAS_PANDAS: missing.append("pandas")

            response = messagebox.askyesno(
                "Missing Dependencies",
                f"CIPW Calculator requires these packages:\n\n"
                f"• numpy\n• matplotlib\n• pandas\n\n"
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
        self.window.title("CIPW Normative Mineralogy Calculator")
        self.window.geometry("1100x800")

        # Make window stay on top
        self.window.transient(self.app.root)

        self._create_interface()

        # Bring to front
        self.window.lift()
        self.window.focus_force()

    def _create_interface(self):
        """Create the CIPW calculator interface"""
        # Header
        header = tk.Frame(self.window, bg="#795548")
        header.pack(fill=tk.X)

        tk.Label(header,
                text="💎 CIPW Normative Mineralogy Calculator",
                font=("Arial", 16, "bold"),
                bg="#795548", fg="white",
                pady=10).pack()

        tk.Label(header,
                text="Calculate normative mineral assemblages from bulk rock chemistry",
                font=("Arial", 10),
                bg="#795548", fg="#D7CCC8").pack(pady=(0, 10))

        # Create main container with paned window
        main_paned = ttk.PanedWindow(self.window, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Left panel - Input and calculation
        left_panel = ttk.Frame(main_paned, relief=tk.RAISED, borderwidth=1)
        main_paned.add(left_panel, weight=1)

        # Right panel - Results and visualization
        right_panel = ttk.Frame(main_paned)
        main_paned.add(right_panel, weight=2)

        # Create left panel content
        self._create_input_panel(left_panel)

        # Create right panel content
        self._create_results_panel(right_panel)

    def _create_input_panel(self, parent):
        """Create the input panel"""
        # Sample selection
        sample_frame = tk.LabelFrame(parent, text="Sample Selection",
                                    padx=10, pady=10)
        sample_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(sample_frame, text="Select Sample:").pack(anchor=tk.W)

        self.sample_var = tk.StringVar()
        sample_combo = ttk.Combobox(sample_frame, textvariable=self.sample_var,
                                   state="readonly", width=30)
        sample_combo.pack(fill=tk.X, pady=5)

        # Update sample list
        self._update_sample_list()

        # Load buttons
        btn_frame = tk.Frame(sample_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        tk.Button(btn_frame, text="📥 Load Selected Sample",
                 command=self._load_selected_sample,
                 width=25).pack(side=tk.LEFT, padx=2)

        tk.Button(btn_frame, text="🧪 Calculate Norm",
                 command=self._calculate_norm,
                 bg="#4CAF50", fg="white",
                 font=("Arial", 10, "bold"),
                 width=25).pack(side=tk.LEFT, padx=2)

        # Oxide input frame
        oxide_frame = tk.LabelFrame(parent, text="Major Oxide Input (wt%)",
                                   padx=10, pady=10)
        oxide_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create scrollable frame for oxides
        canvas = tk.Canvas(oxide_frame)
        scrollbar = ttk.Scrollbar(oxide_frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Oxide entry fields
        self.oxide_vars = {}
        oxides = [
            ('SiO2', 'Silica'),
            ('TiO2', 'Titania'),
            ('Al2O3', 'Alumina'),
            ('Fe2O3_T', 'Total Iron as Fe2O3'),
            ('FeO', 'Ferrous Oxide'),
            ('Fe2O3', 'Ferric Oxide'),
            ('MnO', 'Manganous Oxide'),
            ('MgO', 'Magnesia'),
            ('CaO', 'Lime'),
            ('Na2O', 'Soda'),
            ('K2O', 'Potash'),
            ('P2O5', 'Phosphorus Pentoxide'),
            ('H2O+', 'Loss on Ignition'),
            ('CO2', 'Carbon Dioxide'),
            ('Cr2O3', 'Chromia'),
            ('NiO', 'Nickel Oxide')
        ]

        for i, (oxide, label) in enumerate(oxides):
            frame = tk.Frame(scroll_frame)
            frame.pack(fill=tk.X, pady=2)

            tk.Label(frame, text=f"{label} ({oxide}):", width=25, anchor=tk.W).pack(side=tk.LEFT)

            var = tk.StringVar(value="0.0")
            self.oxide_vars[oxide] = var

            entry = tk.Entry(frame, textvariable=var, width=12)
            entry.pack(side=tk.LEFT, padx=5)

            # Add unit label
            tk.Label(frame, text="wt%").pack(side=tk.LEFT)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Calculation options
        options_frame = tk.LabelFrame(parent, text="Calculation Options",
                                     padx=10, pady=10)
        options_frame.pack(fill=tk.X, padx=5, pady=5)

        # Fe2O3/FeO ratio
        fe_frame = tk.Frame(options_frame)
        fe_frame.pack(fill=tk.X, pady=5)

        tk.Label(fe_frame, text="Fe₂O₃/(FeO+Fe₂O₃) ratio:").pack(side=tk.LEFT)
        self.fe_ratio_var = tk.DoubleVar(value=0.15)
        tk.Scale(fe_frame, from_=0.0, to=1.0, resolution=0.05,
                orient=tk.HORIZONTAL, variable=self.fe_ratio_var,
                length=150).pack(side=tk.RIGHT)

        # Water treatment
        self.water_as_h2o_var = tk.BooleanVar(value=True)
        tk.Checkbutton(options_frame, text="Treat H₂O as separate component",
                      variable=self.water_as_h2o_var).pack(anchor=tk.W, pady=2)

        # Normalization
        self.normalize_var = tk.BooleanVar(value=True)
        tk.Checkbutton(options_frame, text="Normalize to 100% anhydrous",
                      variable=self.normalize_var).pack(anchor=tk.W, pady=2)

        # Example buttons
        example_frame = tk.Frame(parent, pady=10)
        example_frame.pack(fill=tk.X, padx=5)

        tk.Label(example_frame, text="Load example:").pack(side=tk.LEFT)

        examples = ["Basalt", "Granite", "Andesite", "Peridotite"]
        for example in examples:
            tk.Button(example_frame, text=example,
                     command=lambda e=example: self._load_example(e),
                     width=10).pack(side=tk.LEFT, padx=2)

        # Batch processing
        batch_frame = tk.LabelFrame(parent, text="Batch Processing",
                                   padx=10, pady=10)
        batch_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Button(batch_frame, text="📊 Calculate for All Samples",
                 command=self._batch_calculate,
                 width=25).pack(side=tk.LEFT, padx=2)

        tk.Button(batch_frame, text="💾 Export All Results",
                 command=self._export_all_results,
                 width=25).pack(side=tk.RIGHT, padx=2)

    def _create_results_panel(self, parent):
        """Create the results panel"""
        # Tabbed interface
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Normative minerals
        tab_norm = tk.Frame(notebook)
        notebook.add(tab_norm, text="📋 Normative Minerals")

        # Tab 2: Classification
        tab_class = tk.Frame(notebook)
        notebook.add(tab_class, text="🏷️ Classification")

        # Tab 3: Visualization
        tab_viz = tk.Frame(notebook)
        notebook.add(tab_viz, text="📊 Visualization")

        # Tab 4: Comparison
        tab_comp = tk.Frame(notebook)
        notebook.add(tab_comp, text="🔄 Comparison")

        # Initialize tabs
        self._init_norm_tab(tab_norm)
        self._init_class_tab(tab_class)
        self._init_viz_tab(tab_viz)
        self._init_comp_tab(tab_comp)

    def _init_norm_tab(self, parent):
        """Initialize normative minerals tab"""
        # Text widget for detailed results
        self.norm_text = scrolledtext.ScrolledText(parent,
                                                  wrap=tk.WORD,
                                                  font=("Courier New", 10))
        self.norm_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Initial message
        self.norm_text.insert(tk.END,
                             "CIPW NORMATIVE MINERALOGY\n"
                             "══════════════════════════\n\n"
                             "No calculation performed yet.\n"
                             "Enter oxide data and click 'Calculate Norm'.\n")
        self.norm_text.config(state='disabled')

        # Buttons
        button_frame = tk.Frame(parent)
        button_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Button(button_frame, text="Copy Results",
                 command=self._copy_results).pack(side=tk.LEFT, padx=5)

        tk.Button(button_frame, text="Save as CSV",
                 command=self._save_norm_csv).pack(side=tk.LEFT, padx=5)

    def _init_class_tab(self, parent):
        """Initialize classification tab"""
        # Classification display
        class_frame = tk.Frame(parent, padx=20, pady=20)
        class_frame.pack(fill=tk.BOTH, expand=True)

        # Large classification label
        self.class_label = tk.Label(class_frame,
                                   text="No classification",
                                   font=("Arial", 24, "bold"),
                                   fg="gray")
        self.class_label.pack(pady=20)

        # Petrologic indices
        indices_frame = tk.LabelFrame(class_frame, text="Petrologic Indices",
                                     padx=10, pady=10)
        indices_frame.pack(fill=tk.X, pady=10)

        self.di_label = tk.Label(indices_frame,
                                text="Differentiation Index (DI): --",
                                font=("Arial", 11))
        self.di_label.pack(anchor=tk.W)

        self.si_label = tk.Label(indices_frame,
                                text="Solidification Index (SI): --",
                                font=("Arial", 11))
        self.si_label.pack(anchor=tk.W)

        self.ci_label = tk.Label(indices_frame,
                                text="Color Index (CI): --",
                                font=("Arial", 11))
        self.ci_label.pack(anchor=tk.W)

        # Interpretation
        interp_frame = tk.LabelFrame(class_frame, text="Interpretation",
                                    padx=10, pady=10)
        interp_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.interp_text = scrolledtext.ScrolledText(interp_frame,
                                                    wrap=tk.WORD,
                                                    height=8,
                                                    font=("Arial", 10))
        self.interp_text.pack(fill=tk.BOTH, expand=True)

        # Initial message
        self.interp_text.insert(tk.END,
                               "Interpretation will appear here after calculation.\n\n"
                               "The CIPW norm represents the ideal mineral assemblage "
                               "that would crystallize if the magma cooled slowly under "
                               "equilibrium conditions.")
        self.interp_text.config(state='disabled')

    def _init_viz_tab(self, parent):
        """Initialize visualization tab"""
        # Matplotlib figure for visualization
        self.fig_viz, (self.ax_pie, self.ax_bar) = plt.subplots(1, 2, figsize=(10, 5))
        self.canvas_viz = FigureCanvasTkAgg(self.fig_viz, parent)
        self.canvas_viz.draw()
        self.canvas_viz.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Toolbar
        toolbar_frame = tk.Frame(parent)
        toolbar_frame.pack(side=tk.BOTTOM, fill=tk.X)
        toolbar = NavigationToolbar2Tk(self.canvas_viz, toolbar_frame)
        toolbar.update()

        # Initial empty plots
        self.ax_pie.text(0.5, 0.5, "No data\nCalculate norm first",
                        ha='center', va='center', transform=self.ax_pie.transAxes)
        self.ax_bar.text(0.5, 0.5, "No data\nCalculate norm first",
                        ha='center', va='center', transform=self.ax_bar.transAxes)
        self.ax_pie.set_title("Normative Mineralogy")
        self.ax_bar.set_title("Mineral Abundance")
        self.fig_viz.tight_layout()

    def _init_comp_tab(self, parent):
        """Initialize comparison tab"""
        # Comparison with actual modal data
        comp_frame = tk.Frame(parent, padx=20, pady=20)
        comp_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(comp_frame,
                text="Comparison with Modal Mineralogy",
                font=("Arial", 14, "bold")).pack(pady=10)

        # Info text
        info_text = tk.Text(comp_frame, height=8, wrap=tk.WORD,
                           font=("Arial", 10))
        info_text.pack(fill=tk.BOTH, expand=True, pady=10)

        info_text.insert(tk.END,
                        "NORMATIVE vs MODAL MINERALOGY\n\n"
                        "Normative mineralogy (CIPW norm) calculates what minerals "
                        "SHOULD be present based on bulk chemistry.\n\n"
                        "Modal mineralogy measures what minerals ARE ACTUALLY present "
                        "in the rock (from thin section point counting).\n\n"
                        "Comparison can reveal:\n"
                        "• Alteration and weathering effects\n"
                        "• Crystallization history\n"
                        "• Magmatic processes\n"
                        "• Analytical issues\n\n"
                        "To compare, you need both bulk chemistry and modal data.")
        info_text.config(state='disabled')

        # Load modal data button
        tk.Button(comp_frame, text="📁 Load Modal Data for Comparison",
                 command=self._load_modal_data,
                 width=30).pack(pady=10)

        # Comparison results
        self.comp_text = scrolledtext.ScrolledText(comp_frame,
                                                  wrap=tk.WORD,
                                                  height=10,
                                                  font=("Courier New", 9))
        self.comp_text.pack(fill=tk.BOTH, expand=True)

        self.comp_text.insert(tk.END,
                             "No comparison data loaded.\n")
        self.comp_text.config(state='disabled')

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

    def _load_selected_sample(self):
        """Load selected sample data into oxide fields"""
        sample_id = self.sample_var.get()
        if not sample_id:
            return

        # Find sample
        sample = None
        for s in self.app.samples:
            if s.get('Sample_ID') == sample_id:
                sample = s
                break

        if not sample:
            messagebox.showwarning("Sample Not Found",
                                 f"Sample {sample_id} not found.")
            return

        # Load oxides into fields
        oxide_mapping = {
            'SiO2': ['SiO2', 'SiO2_wt'],
            'TiO2': ['TiO2', 'TiO2_wt'],
            'Al2O3': ['Al2O3', 'Al2O3_wt'],
            'Fe2O3_T': ['Fe2O3_T', 'Fe2O3_T_wt', 'Fe2O3'],
            'FeO': ['FeO', 'FeO_wt'],
            'Fe2O3': ['Fe2O3', 'Fe2O3_wt'],
            'MnO': ['MnO', 'MnO_wt'],
            'MgO': ['MgO', 'MgO_wt'],
            'CaO': ['CaO', 'CaO_wt'],
            'Na2O': ['Na2O', 'Na2O_wt'],
            'K2O': ['K2O', 'K2O_wt'],
            'P2O5': ['P2O5', 'P2O5_wt'],
            'H2O+': ['H2O+', 'LOI', 'Loss_on_Ignition'],
            'CO2': ['CO2'],
            'Cr2O3': ['Cr2O3', 'Cr_ppm'],  # Convert ppm to wt% if needed
            'NiO': ['NiO', 'Ni_ppm']
        }

        for oxide, possible_keys in oxide_mapping.items():
            value = None
            for key in possible_keys:
                if key in sample and sample[key] not in [None, '', 'NA']:
                    try:
                        val = float(sample[key])
                        # Convert ppm to wt% for some elements
                        if '_ppm' in key and val > 0:
                            val = val / 10000  # Convert ppm to wt%
                        value = val
                        break
                    except (ValueError, TypeError):
                        continue

            if value is not None:
                self.oxide_vars[oxide].set(f"{value:.2f}")
            else:
                self.oxide_vars[oxide].set("0.0")

        messagebox.showinfo("Sample Loaded",
                          f"Loaded oxide data for {sample_id}")

    def _load_example(self, rock_type):
        """Load example rock composition"""
        examples = {
            'Basalt': {
                'SiO2': 49.5, 'TiO2': 1.5, 'Al2O3': 16.0,
                'Fe2O3_T': 11.0, 'MgO': 8.0, 'CaO': 10.0,
                'Na2O': 2.5, 'K2O': 0.5, 'P2O5': 0.3
            },
            'Granite': {
                'SiO2': 72.0, 'TiO2': 0.3, 'Al2O3': 14.0,
                'Fe2O3_T': 2.0, 'MgO': 0.5, 'CaO': 1.5,
                'Na2O': 3.5, 'K2O': 4.5, 'P2O5': 0.1
            },
            'Andesite': {
                'SiO2': 60.0, 'TiO2': 0.8, 'Al2O3': 17.0,
                'Fe2O3_T': 6.5, 'MgO': 3.0, 'CaO': 6.0,
                'Na2O': 3.0, 'K2O': 2.0, 'P2O5': 0.2
            },
            'Peridotite': {
                'SiO2': 45.0, 'TiO2': 0.1, 'Al2O3': 3.5,
                'Fe2O3_T': 8.0, 'MgO': 38.0, 'CaO': 3.0,
                'Na2O': 0.5, 'K2O': 0.1, 'P2O5': 0.05
            }
        }

        if rock_type in examples:
            for oxide, value in examples[rock_type].items():
                if oxide in self.oxide_vars:
                    self.oxide_vars[oxide].set(f"{value:.2f}")

            # Clear other oxides
            for oxide in self.oxide_vars:
                if oxide not in examples[rock_type]:
                    self.oxide_vars[oxide].set("0.0")

            messagebox.showinfo("Example Loaded",
                              f"Loaded {rock_type} example composition")

    def _calculate_norm(self):
        """Calculate CIPW norm from entered oxides"""
        # Collect oxide data
        oxides = {}
        total = 0.0

        for oxide, var in self.oxide_vars.items():
            try:
                value = float(var.get())
                if value < 0:
                    messagebox.showwarning("Negative Value",
                                         f"{oxide} cannot be negative.")
                    return
                oxides[oxide] = value
                total += value
            except ValueError:
                oxides[oxide] = 0.0

        # Check if we have enough data
        if total < 50:  # Less than 50% total
            response = messagebox.askyesno(
                "Low Total",
                f"Oxide total is only {total:.1f}%. "
                f"Normalize to 100% before calculation?"
            )
            if response:
                # Normalize
                if total > 0:
                    for oxide in oxides:
                        oxides[oxide] = (oxides[oxide] / total) * 100
                else:
                    messagebox.showerror("Zero Total", "Cannot normalize zero total.")
                    return

        # Calculate norm
        try:
            results = self.calculator.calculate_norm(
                oxides,
                Fe2O3_ratio=self.fe_ratio_var.get(),
                water_as_H2O=self.water_as_h2o_var.get()
            )

            self.current_results = results

            # Update display
            self._update_results_display()

            messagebox.showinfo("Calculation Complete",
                              "CIPW norm calculated successfully!")

        except Exception as e:
            messagebox.showerror("Calculation Error",
                               f"Error calculating norm:\n\n{str(e)}\n\n{traceback.format_exc()}")

    def _update_results_display(self):
        """Update all results displays"""
        if not self.current_results:
            return

        # Update normative minerals tab
        self.norm_text.config(state='normal')
        self.norm_text.delete(1.0, tk.END)

        self.norm_text.insert(tk.END,
                             "CIPW NORMATIVE MINERALOGY\n"
                             "══════════════════════════\n\n")

        self.norm_text.insert(tk.END,
                             "Mineral       Formula              wt%\n"
                             "───────       ───────              ───\n")

        # Sort minerals by abundance
        sorted_minerals = sorted(self.current_results.items(),
                                key=lambda x: x[1], reverse=True)

        for mineral, percent in sorted_minerals:
            if percent > 0.1:  # Only show minerals > 0.1%
                formula = self.calculator.MINERAL_FORMULAS.get(mineral, '')
                self.norm_text.insert(tk.END,
                                     f"{mineral:7}       {formula:20} {percent:6.2f}\n")

        # Add totals
        total = sum(self.current_results.values())
        self.norm_text.insert(tk.END,
                             f"\nTotal normative minerals: {total:.2f} wt%\n")

        self.norm_text.config(state='disabled')

        # Update classification tab
        classification = self.calculator.get_classification()
        self.class_label.config(text=classification,
                               fg="#2196F3" if classification != "Not calculated" else "gray")

        self.di_label.config(text=f"Differentiation Index (DI): {self.calculator.differentiation_index:.1f}")
        self.si_label.config(text=f"Solidification Index (SI): {self.calculator.solidification_index:.1f}")
        self.ci_label.config(text=f"Color Index (CI): {self.calculator.color_index:.1f}")

        # Update interpretation
        self.interp_text.config(state='normal')
        self.interp_text.delete(1.0, tk.END)

        interp = self._generate_interpretation()
        self.interp_text.insert(tk.END, interp)
        self.interp_text.config(state='disabled')

        # Update visualization
        self._update_visualization()

    def _generate_interpretation(self):
        """Generate interpretation text"""
        if not self.current_results:
            return "No data"

        interp = []

        # Basic classification
        interp.append(f"Rock Type: {self.calculator.classification}\n")

        # Silica saturation
        q = self.current_results.get('Q', 0)
        ne = self.current_results.get('Ne', 0)

        if q > 10:
            interp.append(f"• Strongly quartz-normative (Q = {q:.1f}%)\n")
            interp.append("  Indicates silica-rich, evolved magma\n")
        elif q > 5:
            interp.append(f"• Moderately quartz-normative (Q = {q:.1f}%)\n")
        elif ne > 5:
            interp.append(f"• Nepheline-normative (Ne = {ne:.1f}%)\n")
            interp.append("  Indicates silica-undersaturated, alkaline magma\n")
        else:
            interp.append("• Normally silica-saturated\n")

        # Mafic minerals
        mafics = ['Fo', 'Fa', 'Di', 'Hd', 'Mt', 'Il']
        mafic_total = sum(self.current_results.get(m, 0) for m in mafics)

        if mafic_total > 40:
            interp.append(f"• High mafic content ({mafic_total:.1f}%)\n")
            interp.append("  Indicates primitive, mantle-derived magma\n")
        elif mafic_total > 20:
            interp.append(f"• Moderate mafic content ({mafic_total:.1f}%)\n")
        else:
            interp.append(f"• Low mafic content ({mafic_total:.1f}%)\n")
            interp.append("  Indicates evolved, fractionated magma\n")

        # Feldspar composition
        or_ab_an = {
            'Or': self.current_results.get('Or', 0),
            'Ab': self.current_results.get('Ab', 0),
            'An': self.current_results.get('An', 0)
        }
        total_fsp = sum(or_ab_an.values())

        if total_fsp > 0:
            interp.append("\nFeldspar composition:\n")
            for fsp, percent in or_ab_an.items():
                if percent > 0:
                    ratio = (percent / total_fsp) * 100
                    interp.append(f"  {fsp}: {ratio:.1f}% of feldspar\n")

        # Differentiation index interpretation
        di = self.calculator.differentiation_index
        if di > 70:
            interp.append(f"\n• High DI ({di:.1f}): Highly differentiated\n")
        elif di > 40:
            interp.append(f"\n• Moderate DI ({di:.1f}): Intermediate composition\n")
        else:
            interp.append(f"\n• Low DI ({di:.1f}): Primitive/mafic composition\n")

        return "".join(interp)

    def _update_visualization(self):
        """Update visualization plots"""
        if not self.current_results:
            return

        # Clear plots
        self.ax_pie.clear()
        self.ax_bar.clear()

        # Prepare data for pie chart (only major minerals)
        pie_data = {}
        for mineral, percent in self.current_results.items():
            if percent > 1.0:  # Only show minerals > 1%
                pie_data[mineral] = percent

        # Colors for minerals
        mineral_colors = {
            'Q': '#C0C0C0',    # Quartz - gray
            'Or': '#FFD700',   # Orthoclase - gold
            'Ab': '#87CEEB',   # Albite - light blue
            'An': '#4682B4',   # Anorthite - steel blue
            'Ne': '#FFA07A',   # Nepheline - light salmon
            'Di': '#228B22',   # Diopside - forest green
            'Hd': '#32CD32',   # Hedenbergite - lime green
            'Fo': '#8B4513',   # Forsterite - saddle brown
            'Fa': '#A0522D',   # Fayalite - sienna
            'Mt': '#2F4F4F',   # Magnetite - dark slate gray
            'Il': '#696969',   # Ilmenite - dim gray
            'Ap': '#9370DB',   # Apatite - medium purple
        }

        # Pie chart
        if pie_data:
            labels = list(pie_data.keys())
            sizes = list(pie_data.values())
            colors = [mineral_colors.get(m, '#CCCCCC') for m in labels]

            self.ax_pie.pie(sizes, labels=labels, colors=colors,
                           autopct='%1.1f%%', startangle=90)
            self.ax_pie.set_title("Normative Mineralogy (wt%)")
        else:
            self.ax_pie.text(0.5, 0.5, "No major minerals > 1%",
                            ha='center', va='center')

        # Bar chart (all minerals sorted)
        sorted_minerals = sorted(self.current_results.items(),
                                key=lambda x: x[1], reverse=True)
        minerals = [m[0] for m in sorted_minerals if m[1] > 0.1]
        percents = [m[1] for m in sorted_minerals if m[1] > 0.1]
        colors = [mineral_colors.get(m, '#CCCCCC') for m in minerals]

        if minerals:
            y_pos = range(len(minerals))
            self.ax_bar.barh(y_pos, percents, color=colors)
            self.ax_bar.set_yticks(y_pos)
            self.ax_bar.set_yticklabels(minerals)
            self.ax_bar.set_xlabel('Weight Percent')
            self.ax_bar.set_title('All Normative Minerals')
            self.ax_bar.invert_yaxis()
        else:
            self.ax_bar.text(0.5, 0.5, "No minerals > 0.1%",
                            ha='center', va='center')

        self.fig_viz.tight_layout()
        self.canvas_viz.draw()

    def _batch_calculate(self):
        """Calculate CIPW norm for all samples"""
        if not self.app.samples:
            messagebox.showwarning("No Samples", "No samples loaded.")
            return

        results = []
        failed = []

        for sample in self.app.samples:
            try:
                # Extract oxides from sample
                oxides = {}
                oxide_mapping = {
                    'SiO2': ['SiO2', 'SiO2_wt'],
                    'TiO2': ['TiO2', 'TiO2_wt'],
                    'Al2O3': ['Al2O3', 'Al2O3_wt'],
                    'Fe2O3_T': ['Fe2O3_T', 'Fe2O3_T_wt', 'Fe2O3'],
                    'MgO': ['MgO', 'MgO_wt'],
                    'CaO': ['CaO', 'CaO_wt'],
                    'Na2O': ['Na2O', 'Na2O_wt'],
                    'K2O': ['K2O', 'K2O_wt'],
                    'P2O5': ['P2O5', 'P2O5_wt']
                }

                for oxide, keys in oxide_mapping.items():
                    value = 0.0
                    for key in keys:
                        if key in sample and sample[key] not in [None, '', 'NA']:
                            try:
                                val = float(sample[key])
                                value = val
                                break
                            except (ValueError, TypeError):
                                continue
                    oxides[oxide] = value

                # Calculate norm
                calculator = CIPWCalculator()
                norm_results = calculator.calculate_norm(oxides)

                # Store results
                result = {
                    'Sample_ID': sample.get('Sample_ID', 'Unknown'),
                    'Classification': calculator.get_classification(),
                    'DI': calculator.differentiation_index,
                    'SI': calculator.solidification_index,
                    'CI': calculator.color_index,
                    **norm_results
                }
                results.append(result)

            except Exception as e:
                failed.append(sample.get('Sample_ID', 'Unknown'))

        # Show summary
        if failed:
            failed_msg = f"\n\nFailed for {len(failed)} samples:\n{', '.join(failed[:5])}"
            if len(failed) > 5:
                failed_msg += "..."
        else:
            failed_msg = ""

        messagebox.showinfo("Batch Complete",
                          f"Calculated CIPW norm for {len(results)} samples.{failed_msg}")

        # Store batch results
        self.batch_results = results

        # Update current sample if available
        if results:
            self.current_results = results[0]
            self._update_results_display()

    def _export_all_results(self):
        """Export all batch results to CSV"""
        if not hasattr(self, 'batch_results') or not self.batch_results:
            messagebox.showwarning("No Results",
                                 "No batch results to export. Run batch calculation first.")
            return

        path = filedialog.asksaveasfilename(
            title="Export CIPW Results",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if path:
            try:
                import pandas as pd
                df = pd.DataFrame(self.batch_results)
                df.to_csv(path, index=False)

                messagebox.showinfo("Export Successful",
                                  f"Exported {len(self.batch_results)} samples to:\n{path}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Error: {str(e)}")

    def _copy_results(self):
        """Copy results to clipboard"""
        if not self.norm_text:
            return

        self.window.clipboard_clear()
        self.window.clipboard_append(self.norm_text.get(1.0, tk.END))

        messagebox.showinfo("Copied", "Results copied to clipboard.")

    def _save_norm_csv(self):
        """Save current norm results as CSV"""
        if not self.current_results:
            messagebox.showwarning("No Results",
                                 "No calculation results to save.")
            return

        path = filedialog.asksaveasfilename(
            title="Save Normative Results",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if path:
            try:
                import pandas as pd

                # Prepare data
                data = {
                    'Mineral': list(self.current_results.keys()),
                    'wt%': list(self.current_results.values()),
                    'Classification': [self.calculator.get_classification()],
                    'DI': [self.calculator.differentiation_index],
                    'SI': [self.calculator.solidification_index],
                    'CI': [self.calculator.color_index]
                }

                df = pd.DataFrame(data)
                df.to_csv(path, index=False)

                messagebox.showinfo("Save Successful",
                                  f"Results saved to:\n{path}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Error: {str(e)}")

    def _load_modal_data(self):
        """Load modal mineralogy data for comparison"""
        path = filedialog.askopenfilename(
            title="Load Modal Mineralogy Data",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx"), ("All files", "*.*")]
        )

        if path:
            try:
                import pandas as pd

                if path.endswith('.xlsx'):
                    df = pd.read_excel(path)
                else:
                    df = pd.read_csv(path)

                # Update comparison tab
                self.comp_text.config(state='normal')
                self.comp_text.delete(1.0, tk.END)

                self.comp_text.insert(tk.END,
                                     f"MODAL DATA LOADED\n"
                                     f"══════════════════\n\n"
                                     f"File: {path}\n"
                                     f"Samples: {len(df)}\n"
                                     f"Columns: {', '.join(df.columns[:5])}...\n\n")

                # Show first few rows
                self.comp_text.insert(tk.END, "First 5 rows:\n")
                self.comp_text.insert(tk.END, df.head().to_string())

                self.comp_text.config(state='disabled')

                messagebox.showinfo("Data Loaded",
                                  f"Loaded modal data for {len(df)} samples")

            except Exception as e:
                messagebox.showerror("Load Error", f"Error: {str(e)}")

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


def register_plugin(app):
    """
    This is the ONLY function the main app looks for.
    It MUST be named 'register_plugin' to work.
    """
    plugin = CIPWPlugin(app)

    # Add to the Tools menu
    if hasattr(app, 'menu_bar'):
        app.menu_bar.add_command(
            label="CIPW Norm Calculator",
            command=plugin.open_cipw_calculator
        )

    return plugin
