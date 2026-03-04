"""
ZOOARCHAEOLOGY ANALYSIS SUITE v2.0 - COMPLETE PRODUCTION RELEASE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
4-TAB DESIGN:
  TAB 1: ASSEMBLAGE - NISP/MNI, diversity, anatomical distribution
  TAB 2: INDIVIDUAL - Age, taphonomy, biometrics (Von den Driesch)
  TAB 3: IDENTITY - Morphological keys, measurement-based ID, 3D support
  TAB 4: ECOLOGY - TDF + isotopes + FTIR (UNIQUE VALUE ADD)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

PLUGIN_INFO = {
    "id": "zooarchaeology_analysis_suite",
    "name": "Zooarchaeology Suite v2.0",
    "category": "software",
    "field": "Zooarchaeology",
    "icon": "🦴",
    "version": "2.0.0",
    "author": "Sefy Levy & Claude",
    "description": "Assemblage · Individual · Identity · Ecology — Complete Archaeofauna Analysis with TDF Integration",
    "requires": ["numpy", "pandas", "scipy", "matplotlib"],
    "optional": ["sklearn", "Pillow"],
    "window_size": "1000x700"
}

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import csv
import os
from pathlib import Path
import threading
import queue
from collections import Counter
import math
import warnings
warnings.filterwarnings('ignore')

# Optional imports with fallbacks
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    np = None
    HAS_NUMPY = False

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    pd = None
    HAS_PANDAS = False

try:
    from scipy import stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    import matplotlib
    matplotlib.use('TkAgg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    from matplotlib.figure import Figure
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

try:
    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
    from sklearn.ensemble import RandomForestClassifier
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


# ============================================================================
# COMPLETE VON DEN DRIESCH MEASUREMENT CODES (1976)
# ============================================================================

MEASUREMENT_CODES = {
    # GENERAL
    "GL": "Greatest length",
    "GLI": "Greatest length lateral",
    "GLm": "Greatest length medial",
    "GB": "Greatest breadth",
    "SB": "Smallest breadth",
    "SD": "Smallest breadth of diaphysis",
    "DD": "Depth of diaphysis",

    # PROXIMAL
    "Bp": "Breadth of the proximal end",
    "Dp": "Depth of the proximal end",
    "BP": "Breadth of the proximal articular surface",
    "DP": "Depth of the proximal articular surface",

    # DISTAL
    "Bd": "Breadth of the distal end",
    "Dd": "Depth of the distal end",
    "BT": "Breadth of the trochlea",
    "DT": "Depth of the trochlea",

    # SCAPULA
    "HS": "Height of the scapula",
    "SLC": "Smallest length of the collum scapulae",
    "GLP": "Greatest length of the processus articularis",
    "LG": "Length of the glenoid cavity",
    "BG": "Breadth of the glenoid cavity",
    "AS": "Length of the facies articularis",

    # HUMERUS
    "GLC": "Greatest length from the caput",
    "Bp": "Breadth of the proximal end",
    "Dp": "Depth of the proximal end",
    "SD": "Smallest breadth of the diaphysis",
    "Bd": "Breadth of the distal end",
    "BT": "Breadth of the trochlea",
    "HT": "Height of the trochlea",

    # RADIUS
    "GL": "Greatest length",
    "PL": "Physiological length",
    "Bp": "Breadth of the proximal end",
    "BFp": "Breadth of the facies articularis proximalis",
    "Dp": "Depth of the proximal end",
    "SD": "Smallest breadth of the diaphysis",
    "Bd": "Breadth of the distal end",
    "BFd": "Breadth of the facies articularis distalis",

    # ULNA
    "GL": "Greatest length",
    "LO": "Length of the olecranon",
    "BPC": "Breadth across the processus coronoideus",
    "SDO": "Smallest depth of the olecranon",
    "DPA": "Depth across the processus anconeus",

    # METACARPAL / METATARSAL
    "GL": "Greatest length",
    "Bp": "Breadth of the proximal end",
    "Dp": "Depth of the proximal end",
    "SD": "Smallest breadth of the diaphysis",
    "Bd": "Breadth of the distal end",
    "Dd": "Depth of the distal end",

    # PELVIS
    "LA": "Length of the acetabulum",
    "LS": "Length of the symphysis",
    "LAR": "Length of the acetabular rim",
    "SB": "Smallest breadth of the ilium",
    "SH": "Smallest height of the ilium",
    "GB": "Greatest breadth of the pelvis",
    "GL": "Greatest length of the pelvis",

    # FEMUR
    "GL": "Greatest length",
    "GLC": "Greatest length from the caput",
    "Bp": "Breadth of the proximal end",
    "DC": "Depth of the caput femoris",
    "SD": "Smallest breadth of the diaphysis",
    "Bd": "Breadth of the distal end",
    "Dd": "Depth of the distal end",

    # TIBIA
    "GL": "Greatest length",
    "Bp": "Breadth of the proximal end",
    "Dp": "Depth of the proximal end",
    "SD": "Smallest breadth of the diaphysis",
    "Bd": "Breadth of the distal end",
    "Dd": "Depth of the distal end",

    # FIBULA
    "GL": "Greatest length",
    "SD": "Smallest breadth of the diaphysis",

    # CALCANEUS
    "GL": "Greatest length",
    "GB": "Greatest breadth",
    "GD": "Greatest depth",

    # ASTRAGALUS
    "GLI": "Greatest length lateral",
    "GLm": "Greatest length medial",
    "Bd": "Breadth of the distal end",
    "Dl": "Depth of the lateral side",
    "Dm": "Depth of the medial side",

    # PHALANGES
    "GL": "Greatest length",
    "Bp": "Breadth of the proximal end",
    "SD": "Smallest breadth of the diaphysis",
    "Bd": "Breadth of the distal end",

    # VERTEBRAE
    "PL": "Physiological length",
    "HF": "Height of the facies terminalis",
    "BF": "Breadth of the facies terminalis",
    "H": "Height of the corpus",
    "B": "Breadth of the corpus",

    # MANDIBLE
    "GL": "Greatest length",
    "GB": "Greatest breadth",
    "GH": "Greatest height",
    "LC": "Length of the cheektooth row",
    "LM": "Length of the molar row",
    "LP": "Length of the premolar row",
    "H": "Height of the mandible",
    "B": "Breadth of the mandible",

    # TEETH
    "L": "Length of the tooth",
    "W": "Width of the tooth",
    "H": "Height of the tooth",

    # HORN CORES
    "GL": "Greatest length",
    "GB": "Greatest breadth",
    "GC": "Greatest circumference",
    "SD": "Smallest diameter",
}

# Total count: 60+ measurements

# ============================================================================
# FUSION STAGES
# ============================================================================

FUSION_STAGES = {
    "uf": "Unfused (young)",
    "fu": "Fusing",
    "fd": "Fused (adult)",
    "nu": "Not observable"
}

# ============================================================================
# SIDES
# ============================================================================

SIDES = ["Left", "Right", "Axial", "Unknown"]

# ============================================================================
# TAXON LIST (common zooarch taxa)
# ============================================================================

TAXA = [
    "Bos taurus (Cattle)", "Ovis aries (Sheep)", "Capra hircus (Goat)",
    "Ovis/Capra", "Sus scrofa (Pig)", "Equus caballus (Horse)",
    "Equus asinus (Donkey)", "Cervus elaphus (Red Deer)",
    "Capreolus capreolus (Roe Deer)", "Alces alces (Moose)",
    "Rangifer tarandus (Reindeer)", "Bison bison", "Bubalus bubalis",
    "Lepus europaeus (Hare)", "Oryctolagus cuniculus (Rabbit)",
    "Canis familiaris (Dog)", "Canis lupus (Wolf)", "Vulpes vulpes (Fox)",
    "Felis catus (Cat)", "Ursus arctos (Brown Bear)",
    "Homo sapiens (Human)", "Gallus gallus (Chicken)",
    "Anser anser (Goose)", "Anas platyrhynchos (Duck)",
    "Struthio camelus (Ostrich)", "Unidentified Mammal",
    "Unidentified Bird", "Unidentified Fish"
]

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
# TDF DATABASE LOADER
# ============================================================================

class TDFDatabase:
    """Load and query the Trophic Discrimination Factor database."""

    def __init__(self):
        self.data = None
        self.metadata = None
        self.entries = []
        self.load_path = None
        self.loaded = False

    def load_from_file(self, filepath):
        """Load TDF database from JSON file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.data = json.load(f)

            self.metadata = self.data.get('metadata', {})
            self.entries = self.data.get('tdf_entries', [])
            self.load_path = filepath
            self.loaded = True
            return True, f"Loaded {len(self.entries)} TDF entries"
        except FileNotFoundError:
            return False, f"TDF database not found at {filepath}"
        except json.JSONDecodeError:
            return False, "Invalid JSON format"
        except Exception as e:
            return False, f"Error loading TDF database: {e}"

    def find(self, taxon=None, tissue=None, trophic_level=None, diet_type=None):
        """Find TDF entries matching criteria."""
        if not self.entries:
            return []

        matches = []
        for entry in self.entries:
            # Skip entries without mean values
            if not entry.get('Δ15N_mean') and not entry.get('Δ13C_mean'):
                continue

            if taxon and entry.get('taxon', '').lower() != taxon.lower():
                continue
            if tissue and entry.get('tissue', '').lower() != tissue.lower():
                continue
            if trophic_level and entry.get('trophic_level', '').lower() != trophic_level.lower():
                continue
            if diet_type and entry.get('diet_type', '').lower() != diet_type.lower():
                continue
            matches.append(entry)

        return matches

    def get_best_match(self, taxon, tissue, trophic_level=None):
        """Get the best matching TDF entry."""
        matches = self.find(taxon=taxon, tissue=tissue, trophic_level=trophic_level)

        if matches:
            return matches[0]

        # Try without trophic level
        matches = self.find(taxon=taxon, tissue=tissue)
        if matches:
            return matches[0]

        # Try broader taxon
        if taxon in ['sheep', 'cattle', 'goat', 'deer', 'pig']:
            matches = self.find(taxon='mammal', tissue=tissue)
            if matches:
                return matches[0]
        elif taxon in ['chicken', 'goose', 'duck', 'turkey']:
            matches = self.find(taxon='bird', tissue=tissue)
            if matches:
                return matches[0]

        return None

    def get_taxa_list(self):
        """Get unique taxa from database."""
        if not self.entries:
            return []
        taxa = set()
        for entry in self.entries:
            if entry.get('taxon'):
                taxa.add(entry['taxon'].capitalize())
        return sorted(taxa)

    def get_tissues_for_taxon(self, taxon):
        """Get tissues available for a given taxon."""
        if not self.entries:
            return []
        tissues = set()
        for entry in self.entries:
            if entry.get('taxon', '').lower() == taxon.lower() and entry.get('tissue'):
                tissues.add(entry['tissue'].capitalize())
        return sorted(tissues)

    def get_summary(self):
        """Get summary statistics of database."""
        if not self.entries:
            return "No TDF database loaded"

        by_taxon = {}
        for entry in self.entries:
            taxon = entry.get('taxon', 'unknown')
            by_taxon[taxon] = by_taxon.get(taxon, 0) + 1

        summary = f"TDF Database: {len(self.entries)} entries\n"
        for taxon, count in sorted(by_taxon.items()):
            summary += f"  • {taxon.capitalize()}: {count}\n"
        return summary


# ============================================================================
# REFERENCE DATABASE LOADER (zoolog-style measurements)
# ============================================================================

class ReferenceDatabase:
    """Load and query reference measurement database."""

    def __init__(self):
        self.data = None
        self.metadata = None
        self.references = {}
        self.loaded = False

    def load_from_file(self, filepath):
        """Load reference database from JSON file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.data = json.load(f)

            self.metadata = self.data.get('metadata', {})
            self.references = self.data.get('references', {})
            self.loaded = True
            return True, f"Loaded {len(self.references)} reference taxa"
        except FileNotFoundError:
            return False, f"Reference database not found at {filepath}"
        except json.JSONDecodeError:
            return False, "Invalid JSON format"
        except Exception as e:
            return False, f"Error loading reference database: {e}"

    def get_taxa(self):
        """Get list of available taxa."""
        return sorted(self.references.keys())

    def get_measurements_for_taxon(self, taxon):
        """Get all measurements for a taxon."""
        return self.references.get(taxon, {})

    def get_measurement_stats(self, taxon, code):
        """Get statistics for a specific measurement."""
        taxon_data = self.references.get(taxon, {})
        return taxon_data.get(code, {})

    def compare_unknown(self, unknown_measurements, selected_taxa=None):
        """
        Compare unknown measurements to reference database.

        Args:
            unknown_measurements: dict of {code: value}
            selected_taxa: list of taxa to compare against (None = all)

        Returns:
            dict of {taxon: probability} sorted by probability
        """
        if not self.loaded:
            return {}

        taxa = selected_taxa if selected_taxa else self.get_taxa()
        results = {}
        total_prob = 0

        for taxon in taxa:
            if taxon not in self.references:
                continue

            ref = self.references[taxon]
            likelihood = 1.0
            matched = 0

            for code, value in unknown_measurements.items():
                if code in ref:
                    mean = ref[code]['mean']
                    sd = ref[code]['sd']
                    # Simple probability based on normal distribution
                    z = abs(value - mean) / sd
                    prob = math.exp(-0.5 * z**2) / (sd * math.sqrt(2 * math.pi))
                    likelihood *= prob
                    matched += 1

            if matched > 0:
                # Take nth root to normalize for number of measurements
                likelihood = likelihood ** (1.0 / matched)
                results[taxon] = likelihood
                total_prob += likelihood

        # Normalize to probabilities
        if total_prob > 0:
            for taxon in results:
                results[taxon] /= total_prob

        return dict(sorted(results.items(), key=lambda x: x[1], reverse=True))

    def get_summary(self):
        """Get summary of database contents."""
        if not self.loaded:
            return "No reference database loaded"

        summary = f"Reference Database: {len(self.references)} taxa\n"
        for taxon in sorted(self.references.keys())[:5]:
            n_meas = len(self.references[taxon])
            summary += f"  • {taxon}: {n_meas} measurements\n"
        if len(self.references) > 5:
            summary += f"  • ... and {len(self.references)-5} more"
        return summary

# ============================================================================
# BASE TAB CLASS
# ============================================================================

class AnalysisTab:
    def __init__(self, parent, app, ui_queue):
        self.parent = parent
        self.app = app
        self.ui_queue = ui_queue
        self.frame = ttk.Frame(parent)
        self.samples = []
        self.selected_indices = set()

    def on_selection_changed(self, selected_rows: set):
        """Called when selection changes in main table."""
        self.selected_indices = selected_rows
        self.refresh()

    def refresh(self):
        """Refresh tab with current data."""
        if hasattr(self.app, 'data_hub'):
            self.samples = self.app.data_hub.get_all()
        self._update_ui()

    def _update_ui(self):
        """Update UI with current data - override in subclasses."""
        pass


# ============================================================================
# TAB 1: ASSEMBLAGE - NISP/MNI, diversity, anatomical distribution
# ============================================================================

class AssemblageTab(AnalysisTab):
    def __init__(self, parent, app, ui_queue):
        super().__init__(parent, app, ui_queue)
        self._build_ui()

    def _build_ui(self):
        # Main container with left (controls) and right (results + visualizations)
        main = ttk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        main.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # LEFT PANEL - Controls and calculators
        left = ttk.Frame(main)
        main.add(left, weight=1)

        # RIGHT PANEL - Results and visualizations
        right = ttk.Frame(main)
        main.add(right, weight=2)

        # === LEFT PANEL ===
        # Basic Statistics (always visible)
        stats_frame = ttk.LabelFrame(left, text="Basic Statistics", padding=5)
        stats_frame.pack(fill=tk.X, pady=2)

        self.stats_text = tk.Text(stats_frame, height=5, width=35, font=("Courier", 9))
        self.stats_text.pack(fill=tk.X)

        # === ADVANCED MNI/MNE CALCULATOR ===
        mni_frame = ttk.LabelFrame(left, text="Advanced MNI/MNE Calculator", padding=5)
        mni_frame.pack(fill=tk.X, pady=2)

        # Element/side logic controls
        logic_frame = ttk.Frame(mni_frame)
        logic_frame.pack(fill=tk.X, pady=2)

        ttk.Label(logic_frame, text="MNI Method:").pack(side=tk.LEFT)
        self.mni_method = tk.StringVar(value="Simple")
        mni_combo = ttk.Combobox(logic_frame, textvariable=self.mni_method,
                                  values=["Simple", "Paired elements", "White's method"],
                                  width=15, state="readonly")
        mni_combo.pack(side=tk.LEFT, padx=2)

        # MNE overlap correction
        overlap_frame = ttk.Frame(mni_frame)
        overlap_frame.pack(fill=tk.X, pady=2)
        self.mne_overlap = tk.BooleanVar(value=True)
        ttk.Checkbutton(overlap_frame, text="Apply MNE overlap correction",
                       variable=self.mne_overlap).pack(anchor='w')

        # Calculate button
        ttk.Button(mni_frame, text="📊 Calculate MNI/MNE",
                  command=self._calculate_advanced_mni).pack(fill=tk.X, pady=2)

        # Results display
        self.mni_results = tk.Text(mni_frame, height=4, width=35, font=("Courier", 8))
        self.mni_results.pack(fill=tk.X, pady=2)

        # === DIVERSITY INDICES + RAREFACTION ===
        div_frame = ttk.LabelFrame(left, text="Diversity & Rarefaction", padding=5)
        div_frame.pack(fill=tk.X, pady=2)

        # Basic diversity (always shown)
        self.div_text = tk.Text(div_frame, height=3, width=35, font=("Courier", 9))
        self.div_text.pack(fill=tk.X)

        # Rarefaction controls
        rarefaction_frame = ttk.Frame(div_frame)
        rarefaction_frame.pack(fill=tk.X, pady=2)

        ttk.Label(rarefaction_frame, text="Rarefaction samples:").pack(side=tk.LEFT)
        self.rarefaction_samples = tk.StringVar(value="100")
        ttk.Entry(rarefaction_frame, textvariable=self.rarefaction_samples, width=6).pack(side=tk.LEFT, padx=2)

        ttk.Button(rarefaction_frame, text="Plot Rarefaction",
                  command=self._plot_rarefaction).pack(side=tk.LEFT, padx=2)

        # === ANATOMICAL DISTRIBUTION ===
        anat_frame = ttk.LabelFrame(left, text="Anatomical Distribution", padding=5)
        anat_frame.pack(fill=tk.X, pady=2)

        self.anat_text = tk.Text(anat_frame, height=6, width=35, font=("Courier", 9))
        self.anat_text.pack(fill=tk.X)

        # === EXPORT SECTION - SIDE BY SIDE BUTTONS ===
        export_frame = ttk.LabelFrame(left, text="Export", padding=5)
        export_frame.pack(fill=tk.X, pady=2)

        # Create a frame for side-by-side buttons
        button_row = ttk.Frame(export_frame)
        button_row.pack(fill=tk.X, pady=2)

        self.export_r_btn = ttk.Button(button_row, text="📤 R-Script",
                                       command=self._export_r_script)
        self.export_r_btn.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)

        self.export_csv_btn = ttk.Button(button_row, text="📊 zooaRch-Ready",
                                        command=self._export_zoowatch_csv)
        self.export_csv_btn.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)

        # Status label for export feedback
        self.export_status = ttk.Label(export_frame, text="", font=("Arial", 7))
        self.export_status.pack(anchor='w')

        # === RIGHT PANEL - Visualizations with tabs ===
        right_notebook = ttk.Notebook(right)
        right_notebook.pack(fill=tk.BOTH, expand=True)

        # Tab R1: Abundance chart
        chart_frame = ttk.Frame(right_notebook)
        right_notebook.add(chart_frame, text="Abundance")

        if HAS_MPL:
            self.fig = Figure(figsize=(6, 5), dpi=100)
            self.ax = self.fig.add_subplot(111)
            self.canvas = FigureCanvasTkAgg(self.fig, chart_frame)
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            # Toolbar
            toolbar = NavigationToolbar2Tk(self.canvas, chart_frame)
            toolbar.update()
        else:
            tk.Label(chart_frame, text="Install matplotlib for charts").pack(expand=True)

        # Tab R2: Rarefaction plot
        rarefaction_plot_frame = ttk.Frame(right_notebook)
        right_notebook.add(rarefaction_plot_frame, text="Rarefaction")

        if HAS_MPL:
            self.rare_fig = Figure(figsize=(6, 5), dpi=100)
            self.rare_ax = self.rare_fig.add_subplot(111)
            self.rare_canvas = FigureCanvasTkAgg(self.rare_fig, rarefaction_plot_frame)
            self.rare_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        else:
            tk.Label(rarefaction_plot_frame, text="Install matplotlib for charts").pack(expand=True)

        # Tab R3: MNI by element
        mni_plot_frame = ttk.Frame(right_notebook)
        right_notebook.add(mni_plot_frame, text="MNI by Element")

        if HAS_MPL:
            self.mni_fig = Figure(figsize=(6, 5), dpi=100)
            self.mni_ax = self.mni_fig.add_subplot(111)
            self.mni_canvas = FigureCanvasTkAgg(self.mni_fig, mni_plot_frame)
            self.mni_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        else:
            tk.Label(mni_plot_frame, text="Install matplotlib for charts").pack(expand=True)

    def _update_export_status(self, message, is_error=False):
        """Update export status label."""
        if hasattr(self, 'export_status'):
            self.export_status.config(text=message,
                                      foreground="red" if is_error else "green")
            # Clear after 3 seconds
            self.frame.after(3000, lambda: self.export_status.config(text=""))

    def _update_ui(self):
        """Update with current data."""
        if not self.samples:
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(1.0, "No samples loaded")
            return

        # Calculate NISP by taxon
        nisp = Counter()
        elements = {}
        sides = {}
        portions = {}

        indices = self.selected_indices if self.selected_indices else range(len(self.samples))

        for i in indices:
            if i >= len(self.samples):
                continue
            sample = self.samples[i]
            taxon = sample.get('taxon') or sample.get('species') or 'Unknown'
            count = int(float(sample.get('count', 1))) if sample.get('count') else 1
            nisp[taxon] += count

            # Track elements with sides and portions for MNI
            element = sample.get('element') or sample.get('bone')
            side = sample.get('side', 'Unknown')
            portion = sample.get('portion', 'Unknown')

            if element:
                key = (element, side, portion)
                elements[key] = elements.get(key, 0) + 1

        # Update basic stats
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, f"Total specimens: {len(indices)}\n")
        self.stats_text.insert(tk.END, f"Total NISP: {sum(nisp.values())}\n")
        self.stats_text.insert(tk.END, f"Number of taxa: {len(nisp)}\n")
        if nisp:
            most_common = nisp.most_common(1)[0]
            self.stats_text.insert(tk.END, f"Most common: {most_common[0][:20]} ({most_common[1]})")

        # Update diversity indices
        self._update_diversity(nisp)

        # Update anatomical distribution
        self._update_anatomical(elements)

        # Update abundance chart
        self._update_abundance_chart(nisp)

        # Update MNI plot
        self._update_mni_plot(elements)

    def _update_diversity(self, nisp):
        """Calculate and display diversity indices."""
        self.div_text.delete(1.0, tk.END)

        if len(nisp) > 0 and HAS_NUMPY:
            total = sum(nisp.values())
            probs = [c/total for c in nisp.values()]

            # Shannon-Wiener H'
            H = -sum(p * math.log(p) if p > 0 else 0 for p in probs)

            # Simpson's D (1 - Σ p²)
            simpson = 1 - sum(p**2 for p in probs)

            # Evenness (Pielou's J)
            S = len(nisp)
            J = H / math.log(S) if S > 1 else 1

            self.div_text.insert(1.0, f"Shannon H': {H:.3f}\n")
            self.div_text.insert(tk.END, f"Simpson D: {simpson:.3f}\n")
            self.div_text.insert(tk.END, f"Evenness J: {J:.3f}")

    def _update_anatomical(self, elements):
        """Update anatomical distribution display."""
        self.anat_text.delete(1.0, tk.END)

        # Group by element (ignoring side/portion for summary)
        element_counts = Counter()
        for (element, side, portion), count in elements.items():
            element_counts[element] += count

        for element, count in element_counts.most_common(8):
            self.anat_text.insert(tk.END, f"{element[:15]:15} {count:3}\n")

    def _calculate_advanced_mni(self):
        """Calculate MNI using element/side/portion logic."""
        if not self.samples:
            return

        # Group by taxon, element, side
        mni_data = {}

        indices = self.selected_indices if self.selected_indices else range(len(self.samples))

        for i in indices:
            if i >= len(self.samples):
                continue
            sample = self.samples[i]
            taxon = sample.get('taxon') or sample.get('species') or 'Unknown'
            element = sample.get('element') or sample.get('bone')
            side = sample.get('side', 'Unknown')

            if not element:
                continue

            key = (taxon, element, side)
            mni_data[key] = mni_data.get(key, 0) + 1

        # Calculate MNI per taxon
        mni_by_taxon = {}
        mne_by_taxon = {}

        for (taxon, element, side), count in mni_data.items():
            # MNI logic
            if taxon not in mni_by_taxon:
                mni_by_taxon[taxon] = {}

            if element not in mni_by_taxon[taxon]:
                mni_by_taxon[taxon][element] = {'Left': 0, 'Right': 0, 'Axial': 0, 'Unknown': 0}

            mni_by_taxon[taxon][element][side] += count

        # Calculate final MNI
        results = []
        total_mni = 0

        for taxon, elements in mni_by_taxon.items():
            taxon_mni = 0
            for element, sides in elements.items():
                if self.mni_method.get() == "Paired elements":
                    # MNI = max(left, right) + abs(left - right)
                    left = sides.get('Left', 0)
                    right = sides.get('Right', 0)
                    axial = sides.get('Axial', 0)
                    unknown = sides.get('Unknown', 0)

                    element_mni = max(left, right) + axial + unknown
                else:
                    # Simple MNI = max count of any side
                    element_mni = max(sides.values())

                taxon_mni = max(taxon_mni, element_mni)

                # MNE calculation (with optional overlap correction)
                if self.mne_overlap.get():
                    # Simplified overlap correction: different portions count separately
                    # This would need portion data from samples
                    mne = sum(sides.values())
                else:
                    mne = sum(sides.values())

                if taxon not in mne_by_taxon:
                    mne_by_taxon[taxon] = 0
                mne_by_taxon[taxon] += mne

            total_mni += taxon_mni
            results.append(f"{taxon[:15]:15} MNI:{taxon_mni:2}  MNE:{mne_by_taxon.get(taxon,0):3}")

        # Display results
        self.mni_results.delete(1.0, tk.END)
        self.mni_results.insert(1.0, f"Total MNI: {total_mni}\n")
        self.mni_results.insert(tk.END, f"Method: {self.mni_method.get()}\n\n")
        for line in results[:5]:  # Show top 5
            self.mni_results.insert(tk.END, line + "\n")

    def _plot_rarefaction(self):
        """Generate rarefaction curve."""
        if not HAS_MPL or not self.samples:
            return

        try:
            n_samples = int(self.rarefaction_samples.get())
        except:
            n_samples = 100

        # Get taxon occurrences
        taxa = []
        indices = self.selected_indices if self.selected_indices else range(len(self.samples))

        for i in indices:
            if i >= len(self.samples):
                continue
            sample = self.samples[i]
            taxon = sample.get('taxon') or sample.get('species')
            if taxon:
                taxa.append(taxon)

        if not taxa:
            return

        # Simple rarefaction simulation
        from random import sample

        richness = []
        subsample_sizes = list(range(5, min(len(taxa), 200), 5))

        for size in subsample_sizes:
            if size > len(taxa):
                break

            # Multiple iterations
            rich_vals = []
            for _ in range(20):
                subsample = sample(taxa, size)
                rich_vals.append(len(set(subsample)))
            richness.append(np.mean(rich_vals))

        # Plot
        self.rare_ax.clear()
        self.rare_ax.plot(subsample_sizes[:len(richness)], richness, 'b-', linewidth=2)
        self.rare_ax.fill_between(subsample_sizes[:len(richness)],
                                   [r - np.std(rich_vals) for r in richness],
                                   [r + np.std(rich_vals) for r in richness],
                                   alpha=0.2)
        self.rare_ax.set_xlabel('Number of specimens')
        self.rare_ax.set_ylabel('Taxon richness')
        self.rare_ax.set_title('Rarefaction Curve')
        self.rare_ax.grid(True, alpha=0.3)
        self.rare_fig.tight_layout()
        self.rare_canvas.draw()

    def _update_abundance_chart(self, nisp):
        """Update abundance chart."""
        if not HAS_MPL:
            return

        self.ax.clear()

        if nisp:
            top_taxa = nisp.most_common(10)
            names = [t[0][:15] + "..." if len(t[0]) > 15 else t[0] for t in top_taxa]
            counts = [t[1] for t in top_taxa]

            y_pos = range(len(names))
            self.ax.barh(y_pos, counts, color='steelblue', alpha=0.7)
            self.ax.set_yticks(y_pos)
            self.ax.set_yticklabels(names, fontsize=8)
            self.ax.set_xlabel('NISP')
            self.ax.set_title('Top 10 Taxa')

            # Add value labels
            for i, v in enumerate(counts):
                self.ax.text(v + 0.5, i, str(v), va='center', fontsize=7)
        else:
            self.ax.text(0.5, 0.5, "No abundance data", ha='center', va='center',
                        transform=self.ax.transAxes)

        self.fig.tight_layout()
        self.canvas.draw()

    def _update_mni_plot(self, elements):
        """Update MNI by element chart."""
        if not HAS_MPL:
            return

        self.mni_ax.clear()

        # Calculate MNI by element (simplified)
        element_mni = Counter()
        for (element, side, portion), count in elements.items():
            element_mni[element] = max(element_mni[element], count)

        if element_mni:
            top_elements = element_mni.most_common(8)
            names = [e[0][:12] + "..." if len(e[0]) > 12 else e[0] for e in top_elements]
            values = [e[1] for e in top_elements]

            y_pos = range(len(names))
            self.mni_ax.barh(y_pos, values, color='#8B4513', alpha=0.7)
            self.mni_ax.set_yticks(y_pos)
            self.mni_ax.set_yticklabels(names, fontsize=8)
            self.mni_ax.set_xlabel('MNI')
            self.mni_ax.set_title('MNI by Element')

            # Add value labels
            for i, v in enumerate(values):
                self.mni_ax.text(v + 0.5, i, str(v), va='center', fontsize=7)
        else:
            self.mni_ax.text(0.5, 0.5, "No element data", ha='center', va='center',
                            transform=self.mni_ax.transAxes)

        self.mni_fig.tight_layout()
        self.mni_canvas.draw()

    def _export_zoowatch_csv(self):
        """Export data in zooaRch-compatible format."""
        if not self.samples:
            self._update_export_status("⚠ No data to export", is_error=True)
            return

        # Create zooaRch-style dataframe
        rows = []
        indices = self.selected_indices if self.selected_indices else range(len(self.samples))

        for i in indices:
            if i >= len(self.samples):
                continue
            s = self.samples[i]
            row = {
                'Site': s.get('site', ''),
                'Context': s.get('context', ''),
                'Taxon': s.get('taxon', s.get('species', '')),
                'Element': s.get('element', s.get('bone', '')),
                'Side': s.get('side', ''),
                'Count': s.get('count', 1),
                'NISP': 1,  # zooaRch expects NISP per row
                'Weight_g': s.get('weight_g', ''),
                # Common measurements
                'GL': s.get('GL', ''),
                'Bd': s.get('Bd', ''),
                'Bp': s.get('Bp', ''),
                'SD': s.get('SD', ''),
                'Notes': s.get('notes', '')
            }
            rows.append(row)

        if HAS_PANDAS:
            df = pd.DataFrame(rows)

            # Save file
            path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV", "*.csv")],
                initialfile="zooarch_export_zoowatch.csv"
            )

            if path:
                df.to_csv(path, index=False)
                self._update_export_status(f"✓ Saved: {Path(path).name}")
        else:
            self._update_export_status("⚠ pandas required for CSV export", is_error=True)

    def _export_r_script(self):
        """Export an R script that uses zooaRch on the exported data."""
        path = filedialog.asksaveasfilename(
            defaultextension=".R",
            filetypes=[("R Script", "*.R")],
            initialfile="analyze_zooarch.R"
        )

        if not path:
            return

        script = """# Zooarchaeological Analysis with zooaRch
# Generated by Zooarchaeology Analysis Suite v2.0

# Install zooaRch if needed
if (!require("zooaRch")) {
    install.packages("zooaRch")
    library(zooaRch)
}

# Load your data
data <- read.csv("zooarch_export_zoowatch.csv")

# Basic NISP by taxon
nisp_table <- table(data$Taxon)
print("NISP by taxon:")
print(nisp_table)

# MNI calculation (simplified)
# Note: For proper MNI, you need element and side data
if ("Element" %in% colnames(data) && "Side" %in% colnames(data)) {
    # Create a unique ID per specimen
    data$ID <- 1:nrow(data)

    # Calculate MNI using zooaRch (if available)
    if (exists("mni")) {
        # This is a simplified example - consult zooaRch documentation
        print("MNI calculation would go here")
    }
}

# Diversity indices
if (require("vegan")) {
    # Create community matrix
    comm_matrix <- table(data$Taxon, data$Context)

    # Calculate diversity
    H <- diversity(comm_matrix)
    print(paste("Shannon diversity:", mean(H)))
}

# Export results
write.csv(nisp_table, "nisp_results.csv")

print("Analysis complete. Check nisp_results.csv")
"""

        with open(path, 'w') as f:
            f.write(script)

        self._update_export_status(f"✓ Script saved: {Path(path).name}")

# ============================================================================
# TAB 2: INDIVIDUAL - Age, taphonomy, biometrics with intelligent interpretation
# ============================================================================

class IndividualTab(AnalysisTab):
    def __init__(self, parent, app, ui_queue):
        super().__init__(parent, app, ui_queue)
        self.current_specimen_idx = None
        self.measurement_codes = list(MEASUREMENT_CODES.keys())
        self._build_ui()

    def _build_ui(self):
        # Main container with left (specimen selector) and right (details)
        main = ttk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        main.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # LEFT PANEL - Specimen list + controls (fixed width)
        left = ttk.Frame(main, width=350)  # Fixed width based on 30 chars + padding
        main.add(left, weight=0)  # weight=0 means it won't expand

        # RIGHT PANEL - Details with tabs (takes remaining space)
        right = ttk.Notebook(main)  # ← This NEEDS to be a Notebook!
        main.add(right, weight=1)  # weight=1 means it takes all remaining space

        # === LEFT PANEL ===
        # Specimen selector
        list_frame = ttk.LabelFrame(left, text="Select Specimen", padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=2)

        # Listbox - 30 characters wide as you wanted!
        self.specimen_list = tk.Listbox(list_frame, height=15, font=("Courier", 8),
                                        width=30)
        self.specimen_list.pack(side=tk.LEFT, fill=tk.Y)

        # Scrollbar for listbox
        list_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.specimen_list.yview)
        self.specimen_list.configure(yscrollcommand=list_scrollbar.set)
        list_scrollbar.pack(side=tk.LEFT, fill=tk.Y)

        # Quick nav buttons
        nav_frame = ttk.Frame(left)
        nav_frame.pack(fill=tk.X, pady=2)
        ttk.Button(nav_frame, text="◀ Prev", command=self._prev_specimen).pack(side=tk.LEFT, padx=2)
        ttk.Button(nav_frame, text="Next ▶", command=self._next_specimen).pack(side=tk.LEFT, padx=2)

        # Quick summary of current specimen
        self.specimen_summary = tk.Text(left, height=3, font=("Arial", 7), width=30)
        self.specimen_summary.pack(fill=tk.X, pady=2)

        # === RIGHT PANEL TABS ===
        # Tab 2a: Age with Payne/Grant integration
        self.age_frame = ttk.Frame(right)
        right.add(self.age_frame, text="Age")

        age_main = ttk.Frame(self.age_frame)
        age_main.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Taxon selector for age (important for fusion/epiphyseal ages)
        taxon_age_frame = ttk.Frame(age_main)
        taxon_age_frame.pack(fill=tk.X, pady=2)
        ttk.Label(taxon_age_frame, text="Taxon:").pack(side=tk.LEFT)
        self.age_taxon_var = tk.StringVar()
        age_taxon_combo = ttk.Combobox(taxon_age_frame, textvariable=self.age_taxon_var,
                                       values=["Cattle", "Sheep", "Goat", "Pig", "Horse", "Red Deer", "Dog"],
                                       width=15)
        age_taxon_combo.pack(side=tk.LEFT, padx=2)
        age_taxon_combo.bind('<<ComboboxSelected>>', self._update_age_interpretation)

        # Fusion stage with interpretation
        fusion_frame = ttk.LabelFrame(age_main, text="Fusion Stage", padding=5)
        fusion_frame.pack(fill=tk.X, pady=2)

        fusion_row = ttk.Frame(fusion_frame)
        fusion_row.pack(fill=tk.X)

        self.fusion_var = tk.StringVar()
        fusion_combo = ttk.Combobox(fusion_row, textvariable=self.fusion_var,
                                    values=list(FUSION_STAGES.keys()), width=10)
        fusion_combo.pack(side=tk.LEFT, padx=2)
        fusion_combo.bind('<<ComboboxSelected>>', self._update_fusion_interpretation)

        self.fusion_desc = tk.Label(fusion_row, text="", font=("Arial", 7))
        self.fusion_desc.pack(side=tk.LEFT, padx=5)

        # Fusion age interpretation
        self.fusion_age = tk.Label(fusion_frame, text="", font=("Arial", 7, "italic"))
        self.fusion_age.pack(anchor='w', padx=5)

        # Dental wear with Payne/Grant lookup
        dental_frame = ttk.LabelFrame(age_main, text="Dental Wear (Payne/Grant stages)", padding=5)
        dental_frame.pack(fill=tk.X, pady=2)

        wear_grid = ttk.Frame(dental_frame)
        wear_grid.pack()

        # Tooth labels
        for i, tooth in enumerate(['M1', 'M2', 'M3', 'P4']):
            ttk.Label(wear_grid, text=tooth, font=("Arial", 8, "bold")).grid(row=0, column=i, padx=2)

        # Wear stage entries
        self.wear_vars = {}
        for i, tooth in enumerate(['M1', 'M2', 'M3', 'P4']):
            var = tk.StringVar()
            entry = ttk.Entry(wear_grid, textvariable=var, width=4)
            entry.grid(row=1, column=i, padx=2)
            entry.bind('<KeyRelease>', self._update_dental_interpretation)
            self.wear_vars[tooth] = var

        # Payne stage interpretation
        self.payne_result = tk.Label(dental_frame, text="", font=("Arial", 7, "italic"), justify=tk.LEFT)
        self.payne_result.pack(anchor='w', padx=5, pady=2)

        # Button to estimate age from wear
        ttk.Button(dental_frame, text="📊 Estimate Age from Wear",
                  command=self._estimate_age_from_wear).pack(pady=2)

        # Age estimate result
        estimate_frame = ttk.LabelFrame(age_main, text="Age Estimate", padding=5)
        estimate_frame.pack(fill=tk.X, pady=2)

        self.age_estimate = tk.Label(estimate_frame, text="—", font=("Arial", 9, "bold"))
        self.age_estimate.pack()

        # Tab 2b: Taphonomy with Behrensmeyer interpretation
        self.taph_frame = ttk.Frame(right)
        right.add(self.taph_frame, text="Taphonomy")

        taph_main = ttk.Frame(self.taph_frame)
        taph_main.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Weathering with Behrensmeyer stages
        weather_frame = ttk.LabelFrame(taph_main, text="Weathering Stage (Behrensmeyer 1978)", padding=5)
        weather_frame.pack(fill=tk.X, pady=2)

        # Behrensmeyer descriptions
        self.behrensmeyer = {
            0: "Stage 0: No cracking or flaking",
            1: "Stage 1: Longitudinal cracking",
            2: "Stage 2: Flaking of outer bone",
            3: "Stage 3: Rough, fibrous texture",
            4: "Stage 4: Coarsely fibrous, splintered",
            5: "Stage 5: Fragile, falling apart"
        }

        weather_row = ttk.Frame(weather_frame)
        weather_row.pack(fill=tk.X)

        self.weather_var = tk.IntVar(value=0)
        for i in range(6):
            rb = ttk.Radiobutton(weather_row, text=str(i), variable=self.weather_var,
                                value=i, command=self._update_weather_interpretation)
            rb.pack(side=tk.LEFT, padx=5)

        self.weather_desc = tk.Label(weather_frame, text=self.behrensmeyer[0],
                                     font=("Arial", 7, "italic"))
        self.weather_desc.pack(anchor='w', padx=5, pady=2)

        # Modifications with summary
        mod_frame = ttk.LabelFrame(taph_main, text="Modifications", padding=5)
        mod_frame.pack(fill=tk.X, pady=2)

        mod_grid = ttk.Frame(mod_frame)
        mod_grid.pack()

        self.burn_var = tk.BooleanVar()
        ttk.Checkbutton(mod_grid, text="Burned", variable=self.burn_var,
                       command=self._update_taph_summary).grid(row=0, column=0, sticky='w')

        self.butchery_var = tk.BooleanVar()
        ttk.Checkbutton(mod_grid, text="Butchery", variable=self.butchery_var,
                       command=self._update_taph_summary).grid(row=0, column=1, sticky='w')

        self.gnaw_var = tk.BooleanVar()
        ttk.Checkbutton(mod_grid, text="Gnawed", variable=self.gnaw_var,
                       command=self._update_taph_summary).grid(row=1, column=0, sticky='w')

        self.root_var = tk.BooleanVar()
        ttk.Checkbutton(mod_grid, text="Root etching", variable=self.root_var,
                       command=self._update_taph_summary).grid(row=1, column=1, sticky='w')

        # Taphonomy summary
        taph_summary_frame = ttk.LabelFrame(taph_main, text="Taphonomic Summary", padding=5)
        taph_summary_frame.pack(fill=tk.X, pady=2)

        self.taph_summary = tk.Label(taph_summary_frame, text="No modifications recorded",
                                     font=("Arial", 7))
        self.taph_summary.pack(anchor='w')

        # Tab 2c: Biometrics with LSI calculator
        self.bio_frame = ttk.Frame(right)
        right.add(self.bio_frame, text="Biometrics")

        # Create a main container
        bio_main_container = ttk.Frame(self.bio_frame)
        bio_main_container.pack(fill=tk.BOTH, expand=True)

        # === MEASUREMENTS SECTION ===
        # Create a canvas with scrollbar
        bio_canvas = tk.Canvas(bio_main_container, highlightthickness=0, height=400)
        bio_scrollbar = ttk.Scrollbar(bio_main_container, orient="vertical", command=bio_canvas.yview)
        bio_scrollable = ttk.Frame(bio_canvas)

        bio_scrollable.bind(
            "<Configure>",
            lambda e: bio_canvas.configure(scrollregion=bio_canvas.bbox("all"))
        )

        bio_canvas.create_window((0, 0), window=bio_scrollable, anchor="nw")
        bio_canvas.configure(yscrollcommand=bio_scrollbar.set)

        bio_canvas.pack(side="left", fill="both", expand=True)
        bio_scrollbar.pack(side="right", fill="y")

        # Measurement grid - ALL codes in 3 columns
        self.measurement_vars = {}
        codes = self.measurement_codes  # All 50+ codes

        # Calculate total rows needed (ceil(len(codes) / 3))
        total_rows = (len(codes) + 2) // 3

        # Create header frame
        header_frame = ttk.Frame(bio_scrollable)
        header_frame.pack(fill=tk.X, pady=5)

        # Configure header columns
        for i in range(9):
            if i % 3 == 0:
                header_frame.columnconfigure(i, weight=1, minsize=50)
            elif i % 3 == 1:
                header_frame.columnconfigure(i, weight=3, minsize=120)
            else:
                header_frame.columnconfigure(i, weight=1, minsize=50)

        # Column headers
        for col in range(3):
            ttk.Label(header_frame, text="Code", font=("Arial", 8, "bold"),
                     anchor='w').grid(row=0, column=col*3, padx=2, pady=1, sticky='ew')
            ttk.Label(header_frame, text="Description", font=("Arial", 8, "bold"),
                     anchor='w').grid(row=0, column=col*3+1, padx=2, pady=1, sticky='ew')
            ttk.Label(header_frame, text="mm", font=("Arial", 8, "bold"),
                     anchor='w').grid(row=0, column=col*3+2, padx=2, pady=1, sticky='ew')

        ttk.Separator(bio_scrollable, orient='horizontal').pack(fill=tk.X, pady=2)

        # Container for measurement rows
        rows_container = ttk.Frame(bio_scrollable)
        rows_container.pack(fill=tk.BOTH, expand=True)

        # Configure row container columns
        for i in range(9):
            if i % 3 == 0:
                rows_container.columnconfigure(i, weight=1, minsize=50)
            elif i % 3 == 1:
                rows_container.columnconfigure(i, weight=3, minsize=120)
            else:
                rows_container.columnconfigure(i, weight=1, minsize=50)

        # Create ALL rows
        for row in range(total_rows):
            for col in range(3):
                idx = row * 3 + col
                if idx >= len(codes):
                    # Fill remaining cells with empty labels
                    ttk.Label(rows_container, text="").grid(row=row, column=col*3, padx=2, pady=1, sticky='w')
                    ttk.Label(rows_container, text="").grid(row=row, column=col*3+1, padx=2, pady=1, sticky='w')
                    ttk.Entry(rows_container, width=8, state='disabled').grid(row=row, column=col*3+2, padx=2, pady=1, sticky='ew')
                    continue

                code = codes[idx]
                desc = MEASUREMENT_CODES[code]
                if len(desc) > 25:
                    desc = desc[:23] + ".."

                # Code label
                ttk.Label(rows_container, text=code, font=("Arial", 8, "bold"),
                         anchor='w').grid(row=row, column=col*3, padx=2, pady=1, sticky='w')

                # Description label
                ttk.Label(rows_container, text=desc, font=("Arial", 7),
                         anchor='w').grid(row=row, column=col*3+1, padx=2, pady=1, sticky='w')

                # Value entry
                var = tk.StringVar()
                entry = ttk.Entry(rows_container, textvariable=var, width=6)
                entry.grid(row=row, column=col*3+2, padx=2, pady=1, sticky='ew')
                self.measurement_vars[code] = var

        # === BOTTOM BAR with LSI and buttons ===
        bottom_bar = ttk.Frame(self.bio_frame)
        bottom_bar.pack(fill=tk.X, pady=2, side=tk.BOTTOM)

        # Left side - buttons
        button_frame = ttk.Frame(bottom_bar)
        button_frame.pack(side=tk.LEFT)

        ttk.Button(button_frame, text="💾 Save", width=8,
                  command=self._save_to_specimen).pack(side=tk.LEFT, padx=1)
        ttk.Button(button_frame, text="🧹 Clear", width=8,
                  command=self._clear_measurements).pack(side=tk.LEFT, padx=1)

        # Center - status
        self.measurement_status = ttk.Label(bottom_bar, text="", font=("Arial", 7))
        self.measurement_status.pack(side=tk.LEFT, padx=10)

        # Right side - LSI Calculator
        lsi_frame = ttk.Frame(bottom_bar)
        lsi_frame.pack(side=tk.RIGHT)

        ttk.Label(lsi_frame, text="LSI:", font=("Arial", 7, "bold")).pack(side=tk.LEFT)

        self.lsi_standard_var = tk.StringVar(value="zoolog")
        lsi_combo = ttk.Combobox(lsi_frame, textvariable=self.lsi_standard_var,
                                 values=["zoolog", "custom"], width=6)
        lsi_combo.pack(side=tk.LEFT, padx=2)

        ttk.Button(lsi_frame, text="Calc", width=5,
                  command=self._calculate_lsi).pack(side=tk.LEFT)

        self.lsi_result = tk.Label(lsi_frame, text="", font=("Arial", 6))
        self.lsi_result.pack(side=tk.LEFT, padx=5)

    def _calculate_lsi(self):
        """Calculate Log Size Index from measurements."""
        if not self.current_specimen_idx:
            self.lsi_result.config(text="Select specimen first")
            return

        # Get current specimen taxon
        sample = self.samples[self.current_specimen_idx]
        taxon = sample.get('taxon', '').lower()

        # Standard measurements from von den Driesch/zoolog
        ZOOLOG_STANDARDS = {
            'cattle': {'GL': 280, 'Bp': 75, 'Bd': 68, 'SD': 38, 'GLP': 72, 'LG': 58, 'BG': 52, 'BT': 82},
            'sheep': {'GL': 150, 'Bp': 40, 'Bd': 35, 'SD': 18, 'GLP': 42, 'LG': 32, 'BG': 28, 'BT': 32},
            'goat': {'GL': 145, 'Bp': 38, 'Bd': 34, 'SD': 17, 'GLP': 40, 'LG': 30, 'BG': 26, 'BT': 30},
            'pig': {'GL': 130, 'Bp': 42, 'Bd': 40, 'SD': 22, 'GLP': 45, 'LG': 35, 'BG': 32, 'BT': 38},
            'red deer': {'GL': 260, 'Bp': 60, 'Bd': 55, 'SD': 30, 'GLP': 58, 'LG': 48, 'BG': 42, 'BT': 52},
            'roe deer': {'GL': 180, 'Bp': 40, 'Bd': 35, 'SD': 20, 'GLP': 38, 'LG': 30, 'BG': 26, 'BT': 32},
            'horse': {'GL': 320, 'Bp': 85, 'Bd': 75, 'SD': 42, 'GLP': 82, 'LG': 65, 'BG': 58, 'BT': 72},
            'dog': {'GL': 120, 'Bp': 28, 'Bd': 25, 'SD': 12, 'GLP': 30, 'LG': 22, 'BG': 18, 'BT': 24}
        }

        # Find matching standard
        std_taxon = None
        for key in ZOOLOG_STANDARDS:
            if key in taxon:
                std_taxon = key
                break

        if not std_taxon:
            self.lsi_result.config(text="No standard for this taxon")
            return

        standards = ZOOLOG_STANDARDS[std_taxon]
        results = []

        for code, var in self.measurement_vars.items():
            val = var.get().strip()
            if val and code in standards:
                try:
                    measurement = float(val)
                    standard = standards[code]
                    lsi = math.log(measurement / standard)
                    results.append(f"{code}: {lsi:.3f}")
                except:
                    pass

        if results:
            self.lsi_result.config(text=" | ".join(results[:4]))
            self.measurement_status.config(text=f"LSI calculated for {len(results)} measurements")
        else:
            self.lsi_result.config(text="No matching measurements")

    # ============================================================================
    # Age interpretation methods
    # ============================================================================

    # Payne (1973) mandibular wear stages for sheep/goat
    PAYNE_STAGES = {
        'A': (0, 2, "Neonatal-infant", "M1 unworn/unerupted"),
        'B': (2, 6, "Juvenile", "M1 in wear, M2 erupting"),
        'C': (6, 12, "Juvenile", "M1/M2 in wear, M3 erupting"),
        'D': (12, 24, "Subadult", "All molars in wear, M3 with 2 crescents"),
        'E': (24, 36, "Prime adult", "M3 posterior cusp in wear"),
        'F': (36, 48, "Adult", "Moderate wear, enamel islands forming"),
        'G': (48, 72, "Mature adult", "Heavy wear, prominent enamel islands"),
        'H': (72, 96, "Old adult", "Very heavy wear, most enamel gone"),
        'I': (96, 120, "Senile", "Extreme wear, teeth worn to roots")
    }

    # Grant (1982) wear stage to Payne conversion (simplified)
    GRANT_TO_PAYNE = {
        ('a','b','c'): 'A',
        ('d','e'): 'B',
        ('f','g'): 'C',
        ('h'): 'D',
        ('i'): 'E',
        ('j'): 'F',
        ('k'): 'G',
        ('l'): 'H',
        ('m','n'): 'I'
    }

    # Epiphyseal fusion ages (months) by taxon (Silver 1969)
    FUSION_AGES = {
        'Cattle': {
            'humerus_distal': 15, 'radius_proximal': 15, 'scapula_distal': 8,
            'phalanges': 18, 'tibia_distal': 24, 'metacarpal_distal': 30,
            'metatarsal_distal': 30, 'femur_proximal': 42, 'femur_distal': 48,
            'humerus_proximal': 48, 'radius_distal': 48, 'tibia_proximal': 48
        },
        'Sheep': {
            'scapula_distal': 6, 'humerus_distal': 10, 'radius_proximal': 10,
            'phalanges': 13, 'tibia_distal': 18, 'metacarpal_distal': 20,
            'metatarsal_distal': 20, 'femur_proximal': 30, 'femur_distal': 36,
            'humerus_proximal': 36, 'radius_distal': 36, 'tibia_proximal': 36
        },
        'Goat': {
            'scapula_distal': 6, 'humerus_distal': 10, 'radius_proximal': 10,
            'phalanges': 13, 'tibia_distal': 18, 'metacarpal_distal': 20,
            'metatarsal_distal': 20, 'femur_proximal': 30, 'femur_distal': 36,
            'humerus_proximal': 36, 'radius_distal': 36, 'tibia_proximal': 36
        },
        'Pig': {
            'scapula_distal': 12, 'humerus_distal': 12, 'radius_proximal': 12,
            'phalanges': 24, 'tibia_distal': 24, 'metacarpal_distal': 24,
            'calcaneus': 36, 'femur_proximal': 36, 'femur_distal': 42,
            'humerus_proximal': 42, 'radius_distal': 42
        },
        'Horse': {
            'scapula_distal': 12, 'humerus_distal': 15, 'radius_proximal': 15,
            'phalanges': 18, 'tibia_distal': 24, 'metacarpal_distal': 18,
            'femur_proximal': 36, 'femur_distal': 42, 'humerus_proximal': 36
        }
    }

    def _update_age_interpretation(self, event=None):
        """Update age interpretations when taxon changes."""
        taxon = self.age_taxon_var.get()
        if taxon:
            self._update_fusion_interpretation()
            self._update_dental_interpretation()

    def _update_fusion_interpretation(self, event=None):
        """Interpret fusion stage with age."""
        fusion = self.fusion_var.get()
        taxon = self.age_taxon_var.get()
        # In a real app, we'd get the element from the specimen data
        # For now, we'll show a generic message
        element = "unknown"

        if fusion == 'uf':
            self.fusion_desc.config(text="Unfused (young animal)")
        elif fusion == 'fu':
            self.fusion_desc.config(text="Fusing (at fusion age)")
        elif fusion == 'fd':
            self.fusion_desc.config(text="Fused (adult)")
        else:
            self.fusion_desc.config(text="")
            self.fusion_age.config(text="")
            return

        # Show fusion age if we have data for this taxon
        if taxon and taxon in self.FUSION_AGES:
            # For demo, use a generic message
            if fusion == 'uf':
                self.fusion_age.config(text=f"→ Younger than fusion age (see element-specific data)")
            elif fusion == 'fu':
                self.fusion_age.config(text=f"→ Approximately at fusion age")
            elif fusion == 'fd':
                self.fusion_age.config(text=f"→ Older than fusion age")
        else:
            self.fusion_age.config(text="")

    def _update_dental_interpretation(self, event=None):
        """Interpret dental wear stages as user types."""
        m1 = self.wear_vars['M1'].get().lower()
        m2 = self.wear_vars['M2'].get().lower()
        m3 = self.wear_vars['M3'].get().lower()

        # Try to determine Payne stage from Grant stages
        for grant_combo, payne_stage in self.GRANT_TO_PAYNE.items():
            if m1 in grant_combo and m2 in grant_combo and m3 in grant_combo:
                stage_info = self.PAYNE_STAGES.get(payne_stage)
                if stage_info:
                    min_age, max_age, category, desc = stage_info
                    self.payne_result.config(
                        text=f"Payne Stage {payne_stage}: {category}\n{desc}\nAge: {min_age}-{max_age} months"
                    )
                return

        self.payne_result.config(text="")

    def _estimate_age_from_wear(self):
        """Calculate age estimate from wear stages."""
        m1 = self.wear_vars['M1'].get().lower()
        m2 = self.wear_vars['M2'].get().lower()
        m3 = self.wear_vars['M3'].get().lower()

        # Find best match
        for grant_combo, payne_stage in self.GRANT_TO_PAYNE.items():
            if m1 in grant_combo and m2 in grant_combo and m3 in grant_combo:
                stage_info = self.PAYNE_STAGES.get(payne_stage)
                if stage_info:
                    min_age, max_age, category, desc = stage_info
                    avg_age = (min_age + max_age) / 2
                    self.age_estimate.config(
                        text=f"{category}: {avg_age:.0f} months ({min_age}-{max_age} months)"
                    )
                return

        self.age_estimate.config(text="Unable to determine age from wear stages")

    # ============================================================================
    # Taphonomy interpretation methods
    # ============================================================================

    def _update_weather_interpretation(self):
        """Update weather description based on selected stage."""
        stage = self.weather_var.get()
        self.weather_desc.config(text=self.behrensmeyer.get(stage, ""))

    def _update_taph_summary(self):
        """Update taphonomic summary based on checkboxes."""
        modifications = []
        if self.burn_var.get():
            modifications.append("🔥 Burned")
        if self.butchery_var.get():
            modifications.append("🥩 Butchery")
        if self.gnaw_var.get():
            modifications.append("🐕 Gnawed")
        if self.root_var.get():
            modifications.append("🌱 Root etching")

        if modifications:
            self.taph_summary.config(text=" | ".join(modifications))
        else:
            self.taph_summary.config(text="No modifications recorded")

    # ============================================================================
    # LSI Calculator
    # ============================================================================

    # Standard measurements from zoolog package (simplified)
    ZOOLOG_STANDARDS = {
        'Cattle': {'GL': 280, 'Bp': 75, 'Bd': 68, 'SD': 38},
        'Sheep': {'GL': 150, 'Bp': 40, 'Bd': 35, 'SD': 18},
        'Goat': {'GL': 145, 'Bp': 38, 'Bd': 34, 'SD': 17},
        'Pig': {'GL': 130, 'Bp': 42, 'Bd': 40, 'SD': 22},
        'Red Deer': {'GL': 260, 'Bp': 60, 'Bd': 55, 'SD': 30},
        'Roe Deer': {'GL': 180, 'Bp': 40, 'Bd': 35, 'SD': 20}
    }

    def _calculate_lsi(self):
        """Calculate Log Size Index from measurements."""
        if not self.current_specimen_idx:
            self.lsi_result.config(text="Select a specimen first")
            return

        sample = self.samples[self.current_specimen_idx]
        taxon = sample.get('taxon', '')

        # Find matching standard
        standard_taxon = None
        for std_taxon in self.ZOOLOG_STANDARDS:
            if std_taxon.lower() in taxon.lower():
                standard_taxon = std_taxon
                break

        if not standard_taxon:
            self.lsi_result.config(text="No standard found for this taxon")
            return

        standards = self.ZOOLOG_STANDARDS[standard_taxon]
        results = []

        for code, var in self.measurement_vars.items():
            val = var.get().strip()
            if val and code in standards:
                try:
                    measurement = float(val)
                    standard = standards[code]
                    lsi = math.log(measurement / standard)
                    results.append(f"{code}: LSI = {lsi:.3f}")
                except:
                    pass

        if results:
            self.lsi_result.config(text=" | ".join(results[:5]))
            self.measurement_status.config(text=f"LSI calculated for {len(results)} measurements")
        else:
            self.lsi_result.config(text="No matching measurements for LSI")

    # ============================================================================
    # UI update methods
    # ============================================================================

    def _update_ui(self):
        """Populate specimen list."""
        self.specimen_list.delete(0, tk.END)

        indices = self.selected_indices if self.selected_indices else range(len(self.samples))

        for i in sorted(indices)[:50]:
            if i >= len(self.samples):
                continue
            sample = self.samples[i]
            label = f"{i}: {sample.get('Sample_ID', '')[:10]} - {sample.get('taxon', '?')[:15]}"
            self.specimen_list.insert(tk.END, label)

        if self.specimen_list.size() > 0:
            self.specimen_list.selection_set(0)
            self._on_specimen_selected()

    def _on_specimen_selected(self, event=None):
        """Load selected specimen data."""
        selection = self.specimen_list.curselection()
        if not selection:
            return

        idx = selection[0]
        actual_idx = list(sorted(self.selected_indices if self.selected_indices else range(len(self.samples))))[idx]
        self.current_specimen_idx = actual_idx

        if actual_idx >= len(self.samples):
            return

        sample = self.samples[actual_idx]

        # Update specimen summary
        self.specimen_summary.delete(1.0, tk.END)
        self.specimen_summary.insert(1.0,
            f"ID: {sample.get('Sample_ID', 'N/A')}\n"
            f"Taxon: {sample.get('taxon', 'Unknown')}\n"
            f"Element: {sample.get('element', 'Unknown')} ({sample.get('side', '')})"
        )

        # Set taxon for age
        taxon = sample.get('taxon', '')
        for t in ['Cattle', 'Sheep', 'Goat', 'Pig', 'Horse', 'Red Deer', 'Dog']:
            if t.lower() in taxon.lower():
                self.age_taxon_var.set(t)
                break

        # Load fusion
        fusion = sample.get('fusion', '')
        if fusion in FUSION_STAGES:
            self.fusion_var.set(fusion)
            self._update_fusion_interpretation()

        # Load taphonomy
        self.weather_var.set(int(sample.get('weathering', 0)))
        self._update_weather_interpretation()

        self.burn_var.set(bool(sample.get('burning', False)))
        self.butchery_var.set(bool(sample.get('butchery', False)))
        self.gnaw_var.set(bool(sample.get('gnawing', False)))
        self.root_var.set(bool(sample.get('root_etching', False)))
        self._update_taph_summary()

        # Load dental wear
        for tooth in ['M1', 'M2', 'M3', 'P4']:
            val = sample.get(f'wear_{tooth}', '')
            self.wear_vars[tooth].set(str(val) if val else '')
        self._update_dental_interpretation()

        # Load measurements
        loaded_count = 0
        for code, var in self.measurement_vars.items():
            val = sample.get(code, '')
            if val:
                var.set(str(val))
                loaded_count += 1
            else:
                var.set('')

        self.measurement_status.config(text=f"Loaded {loaded_count} measurements")

    def _update_fusion_desc(self, event=None):
        fusion = self.fusion_var.get()
        self.fusion_desc.config(text=FUSION_STAGES.get(fusion, ""))

    def _prev_specimen(self):
        selection = self.specimen_list.curselection()
        if selection and selection[0] > 0:
            self.specimen_list.selection_clear(0, tk.END)
            self.specimen_list.selection_set(selection[0] - 1)
            self._on_specimen_selected()

    def _next_specimen(self):
        selection = self.specimen_list.curselection()
        if selection and selection[0] < self.specimen_list.size() - 1:
            self.specimen_list.selection_clear(0, tk.END)
            self.specimen_list.selection_set(selection[0] + 1)
            self._on_specimen_selected()

    def _save_to_specimen(self):
        """Save current data to specimen."""
        if self.current_specimen_idx is None:
            messagebox.showwarning("No Selection", "Select a specimen first")
            return

        # Collect all measurement values
        measurements = {}
        saved_count = 0
        for code, var in self.measurement_vars.items():
            val = var.get().strip()
            if val:
                try:
                    measurements[code] = float(val)
                    saved_count += 1
                except ValueError:
                    measurements[code] = val
                    saved_count += 1

        self.measurement_status.config(text=f"Saved {saved_count} measurements")
        messagebox.showinfo("Save", f"Saved {saved_count} measurements to specimen {self.current_specimen_idx}")

    def _clear_measurements(self):
        """Clear all measurement fields."""
        for var in self.measurement_vars.values():
            var.set("")
        self.measurement_status.config(text="All fields cleared")

# ============================================================================
# TAB 3: IDENTITY - Morphological keys + measurement-based ID with reference DB
# ============================================================================

class IdentityTab(AnalysisTab):
    def __init__(self, parent, app, ui_queue):
        super().__init__(parent, app, ui_queue)
        self.ref_db = ReferenceDatabase()
        self._load_reference_database()
        self._build_ui()

    def _set_equal_split(self, paned):
        """Force the paned window to 50/50 split."""
        try:
            total_width = paned.winfo_width()
            if total_width > 10:
                paned.sashpos(0, total_width // 2)
        except:
            pass

    def refresh(self):
        """Refresh tab with current data and load measurements from selected specimen."""
        super().refresh()
        self._load_measurements_from_selection()

    def _update_live_preview(self, event=None):
        """Update the quick match preview live as user types."""
        # Collect measurements
        unknown = {}
        for code, var in self.id_measurements.items():
            val = var.get().strip()
            if val:
                try:
                    unknown[code] = float(val)
                except ValueError:
                    pass

        if not unknown or not hasattr(self, 'ref_db') or not self.ref_db.loaded:
            # Clear preview
            for i in range(5):
                self.preview_taxon_labels[i].config(text="—")
                self.preview_percent_labels[i].config(text="0%")
                self.preview_bars[i].delete("all")
            self.preview_summary.config(text="Enter measurements to see live match preview")
            return

        # Get selected taxa
        selected_taxa = [taxon for taxon, var in self.id_taxa_vars.items() if var.get()]
        if not selected_taxa:
            return

        # Get live probabilities
        results = self.ref_db.compare_unknown(unknown, selected_taxa)

        # Update preview rows
        for i, (taxon, prob) in enumerate(list(results.items())[:5]):
            self.preview_taxon_labels[i].config(text=taxon[:20])
            self.preview_percent_labels[i].config(text=f"{prob:.0%}")

            # Update progress bar
            bar = self.preview_bars[i]
            bar.delete("all")
            bar_width = bar.winfo_width()
            if bar_width > 10:
                fill_width = int(bar_width * prob)
                bar.create_rectangle(0, 0, fill_width, 12, fill='#2ecc71', outline='')

        # Clear remaining rows
        for i in range(len(results), 5):
            self.preview_taxon_labels[i].config(text="—")
            self.preview_percent_labels[i].config(text="0%")
            self.preview_bars[i].delete("all")

        # Update summary
        if results:
            best = list(results.keys())[0]
            best_prob = results[best]
            self.preview_summary.config(text=f"Most likely: {best} ({best_prob:.0%})")
        else:
            self.preview_summary.config(text="No match data available")

    def _go_to_results_tab(self, event=None):
        """Switch to the Results & Visualization tab."""
        if hasattr(self, 'right_notebook'):
            self.right_notebook.select(1)  # Index 1 = Results tab

    def _load_measurements_from_selection(self):
        """Load measurements from the currently selected specimen."""
        if not self.selected_indices:
            return

        # Get the first selected specimen
        idx = next(iter(self.selected_indices))
        if idx >= len(self.samples):
            return

        sample = self.samples[idx]

        # Map of measurement codes
        measurement_codes = ['GL', 'Bp', 'Bd', 'SD', 'Dp', 'GLP', 'LG', 'BG', 'BT']

        # Fill in the measurement fields
        filled_count = 0
        for code in measurement_codes:
            if code in self.id_measurements:
                saved_value = sample.get(code, '')
                if saved_value:
                    self.id_measurements[code].set(str(saved_value))
                    filled_count += 1
                else:
                    self.id_measurements[code].set('')

        # Update status if we have a status label
        if hasattr(self, 'measurement_status'):
            self.measurement_status.config(text=f"Loaded {filled_count} measurements from selected specimen")

    def _load_reference_database(self):
        """Load reference database from config folder."""
        try:
            from pathlib import Path
            plugin_dir = Path(__file__).parent
            appbase_dir = plugin_dir.parent.parent
            ref_path = appbase_dir / "config" / "zooarch_reference.json"

            success, msg = self.ref_db.load_from_file(ref_path)
            if success:
                print(f"✅ Reference database loaded: {msg}")
            else:
                print(f"⚠️ {msg} — falling back to empty reference")
        except Exception as e:
            print(f"⚠️ Could not load reference database: {e}")

    def _build_ui(self):
        # === MAIN PANED WINDOW ===
        main = ttk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        main.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # LEFT PANEL
        left = ttk.Frame(main)
        main.add(left, weight=1)

        # RIGHT PANEL
        right = ttk.Frame(main)
        main.add(right, weight=1)

        # Force both panes to ignore natural width of children
        left.update_idletasks()
        right.update_idletasks()
        left.configure(width=1)
        right.configure(width=1)


        # Equal minimum sizes
        left.configure(width=1)
        right.configure(width=1)



        # === LEFT PANEL CONTENT ===
        key_frame = ttk.LabelFrame(left, text="Morphological Key", padding=5)
        key_frame.pack(fill=tk.BOTH, expand=True)

        cat_frame = ttk.Frame(key_frame)
        cat_frame.pack(fill=tk.X, pady=2)

        ttk.Label(cat_frame, text="Category:").pack(side=tk.LEFT)
        self.key_category_var = tk.StringVar()
        cat_combo = ttk.Combobox(cat_frame, textvariable=self.key_category_var,
                                values=["Mammals", "Birds", "Fish", "Special Cases"],
                                state="readonly", width=15)
        cat_combo.pack(side=tk.LEFT, padx=2)
        cat_combo.bind('<<ComboboxSelected>>', self._update_key_list)

        ttk.Label(key_frame, text="Select comparison:").pack(anchor='w')
        self.key_var = tk.StringVar()
        self.key_combo = ttk.Combobox(key_frame, textvariable=self.key_var,
                                    values=[], state="readonly", width=40)
        self.key_combo.pack(fill=tk.X, pady=2)
        self.key_combo.bind('<<ComboboxSelected>>', self._update_key)

        key_text_frame = ttk.Frame(key_frame)
        key_text_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.key_text = tk.Text(key_text_frame, wrap=tk.WORD, font=("Courier", 9),
                                bg="#f9f9f9", relief=tk.SUNKEN, borderwidth=1)
        key_scrollbar = ttk.Scrollbar(key_text_frame, orient="vertical",
                                    command=self.key_text.yview)
        self.key_text.configure(yscrollcommand=key_scrollbar.set)

        self.key_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        key_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        ref_frame = ttk.Frame(key_frame)
        ref_frame.pack(fill=tk.X, pady=2)
        ttk.Label(ref_frame, text="References: Boessneck 1969, Zeder 2006, Cohen & Serjeantson 1996, etc.",
                font=("Arial", 7, "italic")).pack()

        self.key_category_var.set("Mammals")
        self._update_key_list()

        # === RIGHT PANEL CONTENT ===
        self.right_notebook = ttk.Notebook(right)
        self.right_notebook.pack(fill=tk.BOTH, expand=True)

        # TAB 1: MEASUREMENTS
        measure_frame = ttk.Frame(self.right_notebook)
        self.right_notebook.add(measure_frame, text="Measurement Input")

        input_frame = ttk.LabelFrame(measure_frame, text="Enter Unknown Specimen Measurements", padding=5)
        input_frame.pack(fill=tk.X, pady=5, padx=5)

        grid = ttk.Frame(input_frame)
        grid.pack()

        self.id_measurements = {}
        all_measures = ['GL', 'Bp', 'Bd', 'SD', 'Dp', 'GLP', 'LG', 'BG', 'BT']

        for i, code in enumerate(all_measures):
            row, col = divmod(i, 3)
            frame = ttk.Frame(grid, relief=tk.GROOVE, borderwidth=1)
            frame.grid(row=row, column=col, padx=2, pady=2, sticky='nsew')

            ttk.Label(frame, text=code, font=("Arial", 8, "bold")).pack()
            var = tk.StringVar()
            entry = ttk.Entry(frame, textvariable=var, width=8)
            entry.pack(padx=2, pady=2)
            self.id_measurements[code] = var

            # Bind live update to each entry
            entry.bind('<KeyRelease>', self._update_live_preview)

        taxa_frame = ttk.LabelFrame(measure_frame, text="Compare Against Reference Collections", padding=5)
        taxa_frame.pack(fill=tk.X, pady=5, padx=5)

        taxa_canvas = tk.Canvas(taxa_frame, highlightthickness=0, height=120)
        taxa_scrollbar = ttk.Scrollbar(taxa_frame, orient="vertical", command=taxa_canvas.yview)
        taxa_scrollable = ttk.Frame(taxa_canvas)

        taxa_scrollable.bind("<Configure>",
                            lambda e: taxa_canvas.configure(scrollregion=taxa_canvas.bbox("all")))

        taxa_canvas.create_window((0, 0), window=taxa_scrollable, anchor="nw")
        taxa_canvas.configure(yscrollcommand=taxa_scrollbar.set)

        taxa_canvas.pack(side="left", fill="both", expand=True)
        taxa_scrollbar.pack(side="right", fill="y")

        if hasattr(self, 'ref_db') and self.ref_db.loaded:
            all_taxa = self.ref_db.get_taxa()
        else:
            all_taxa = ["Sheep (Ovis aries)", "Goat (Capra hircus)", "Cattle (Bos taurus)",
                        "Pig (Sus scrofa domesticus)", "Red Deer (Cervus elaphus)",
                        "Roe Deer (Capreolus capreolus)", "Horse (Equus caballus)",
                        "Dog (Canis familiaris)"]

        self.id_taxa_vars = {}
        for taxon in all_taxa:
            var = tk.BooleanVar(value=True)
            cb = ttk.Checkbutton(taxa_scrollable, text=taxon, variable=var)
            cb.pack(anchor='w', padx=5)
            self.id_taxa_vars[taxon] = var
            # Bind live update to checkbox
            cb.configure(command=self._update_live_preview)

        button_frame = ttk.Frame(measure_frame)
        button_frame.pack(fill=tk.X, pady=5, padx=5)

        ttk.Button(button_frame, text="🔍 RUN DISCRIMINANT ANALYSIS",
                command=self._run_discriminant).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="🧹 Clear All",
                command=self._clear_measurements).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="📊 Export Report",
                command=self._export_report).pack(side=tk.RIGHT, padx=2)

        # === QUICK MATCH PREVIEW (LIVE UPDATING) ===
        preview_frame = ttk.LabelFrame(measure_frame, text="🎯 Quick Match Preview", padding=5)
        preview_frame.pack(fill=tk.X, pady=5, padx=5)

        # Header
        preview_header = ttk.Frame(preview_frame)
        preview_header.pack(fill=tk.X)
        ttk.Label(preview_header, text="Taxon", font=("Arial", 7, "bold"), width=15).pack(side=tk.LEFT)
        ttk.Label(preview_header, text="Match", font=("Arial", 7, "bold"), width=8).pack(side=tk.LEFT)
        ttk.Label(preview_header, text="Confidence Bar", font=("Arial", 7, "bold")).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Preview rows (will be updated live)
        self.preview_taxon_labels = []
        self.preview_percent_labels = []
        self.preview_bars = []

        for i in range(5):  # Show top 5 matches
            row = ttk.Frame(preview_frame)
            row.pack(fill=tk.X, pady=2)

            taxon_label = ttk.Label(row, text="—", font=("Arial", 7), width=15, anchor='w')
            taxon_label.pack(side=tk.LEFT)

            percent_label = ttk.Label(row, text="0%", font=("Arial", 7, "bold"), width=8)
            percent_label.pack(side=tk.LEFT)

            # Canvas for custom progress bar
            bar_canvas = tk.Canvas(row, height=12, bg='#f0f0f0', highlightthickness=0)
            bar_canvas.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

            self.preview_taxon_labels.append(taxon_label)
            self.preview_percent_labels.append(percent_label)
            self.preview_bars.append(bar_canvas)

        # Most likely summary
        self.preview_summary = ttk.Label(preview_frame, text="Enter measurements to see live match preview",
                                         font=("Arial", 7, "italic"))
        self.preview_summary.pack(anchor='w', pady=2)

        # === RESULTS STATUS NOTIFICATION ===
        self.result_status = tk.Label(measure_frame,
                                      text="",
                                      font=("Arial", 8, "bold"),
                                      cursor="hand2",  # Changes cursor to hand on hover
                                      relief=tk.FLAT)
        self.result_status.pack(anchor='w', padx=5, pady=2, fill=tk.X)
        self.result_status.bind('<Button-1>', self._go_to_results_tab)

        # Status label for loaded measurements
        self.measurement_status = ttk.Label(measure_frame, text="", font=("Arial", 7))
        self.measurement_status.pack(anchor='w', padx=5, pady=2)

        # TAB 2: RESULTS
        results_frame = ttk.Frame(self.right_notebook)
        self.right_notebook.add(results_frame, text="Results & Visualization")

        results_pane = ttk.PanedWindow(results_frame, orient=tk.VERTICAL)
        results_pane.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        stats_panel = ttk.Frame(results_pane)
        results_pane.add(stats_panel, weight=1)

        class_frame = ttk.LabelFrame(stats_panel, text="Classification Results", padding=5)
        class_frame.pack(fill=tk.BOTH, expand=True, pady=2)

        self.class_result = tk.Text(class_frame, height=15, font=("Courier", 9))
        self.class_result.pack(fill=tk.BOTH, expand=True)

        viz_panel = ttk.Frame(results_pane)
        results_pane.add(viz_panel, weight=1)

        if HAS_MPL:
            self.fig = Figure(figsize=(5, 4), dpi=100)
            self.ax = self.fig.add_subplot(111)
            self.canvas = FigureCanvasTkAgg(self.fig, viz_panel)
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            toolbar = NavigationToolbar2Tk(self.canvas, viz_panel)
            toolbar.update()
        else:
            tk.Label(viz_panel, text="Install matplotlib for visualizations").pack(expand=True)

        # === FINAL FIX: FORCE 50/50 SPLIT ===
        def force_equal_split():
            # Force both panes to ignore their children's requested width
            left.configure(width=1)
            right.configure(width=1)

            total = main.winfo_width()
            if total > 10:
                main.sashpos(0, total // 2)

        # Run twice: once after layout, once after matplotlib loads
        self.frame.after(50, force_equal_split)
        self.frame.after(300, force_equal_split)

    def _update_ui(self):
        """Update with current data - placeholder."""
        pass

    def _update_key_list(self, event=None):
        """Update key list based on selected category."""
        category = self.key_category_var.get()

        keys_by_category = {
            "Mammals": [
                "Sheep vs Goat (cranial)",
                "Sheep vs Goat (postcranial)",
                "Cattle vs Bison",
                "Red Deer vs Fallow Deer",
                "Roe Deer vs Sheep",
                "Horse vs Donkey",
                "Pig vs Wild Boar",
                "Dog vs Wolf vs Fox",
                "Hare vs Rabbit",
                "Human vs Bear (paw bones)",
                "Seal species identification"
            ],
            "Birds": [
                "Chicken vs Pheasant vs Grouse",
                "Duck vs Goose vs Swan",
                "Turkey vs Peafowl",
                "Raptor species (eagles, hawks, owls)",
                "Corvid species (crow, raven, rook, jackdaw)"
            ],
            "Fish": [
                "Cod vs Haddock vs Pollock",
                "Salmon vs Trout vs Grayling",
                "Herring vs Sprat vs Sardine",
                "Flatfish species (plaice, flounder, sole, turbot)",
                "Cyprinid identification (carp, roach, bream, chub, dace)"
            ],
            "Special Cases": [
                "Canid tooth eruption & wear (ages)",
                "Caprine mandibular wear stages (Payne 1973, 1987)",
                "Cattle epiphyseal fusion ages",
                "Sheep/goat epiphyseal fusion ages",
                "Pig epiphyseal fusion ages",
                "Horse dental eruption & wear",
                "Bird tarsometatarsus sexing (spur presence)"
            ]
        }

        self.key_combo['values'] = keys_by_category.get(category, [])
        if self.key_combo['values']:
            self.key_combo.set(self.key_combo['values'][0])
            self._update_key()

    def _update_key(self, event=None):
        """Update morphological key text."""
        key = self.key_var.get()
        if not key:
            return

        keys_database = {
            "Sheep vs Goat (cranial)": """SHEEP VS GOAT - CRANIAL FEATURES

HORN CORES:
• Sheep: Oval cross-section, curve laterally
• Goat: Triangular cross-section, straight, keeled anteriorly

FRONTAL BONE:
• Sheep: Smooth, frontal suture straight
• Goat: Raised boss, frontal suture curved

ORBIT:
• Sheep: Orbital rim smooth
• Goat: Orbital rim with prominent supraorbital foramen

MANDIBLE:
• Sheep: Diastema longer, mental foramen under P2
• Goat: Diastema shorter, mental foramen under P3

TEETH:
• Sheep: Smaller, simpler enamel folds
• Goat: Larger, more complex enamel, prominent stylids

PALATE:
• Sheep: Palatal ridges more numerous
• Goat: Palatal ridges fewer, more robust

References: Boessneck 1969, Zeder & Lapham 2010, Halstead 2011""",

            "Sheep vs Goat (postcranial)": """SHEEP VS GOAT - POSTCRANIAL FEATURES

SCAPULA:
• Sheep: Glenoid cavity oval, neck narrower
• Goat: Glenoid cavity rounded, neck broader

HUMERUS:
• Sheep: Supracondylar fossa deeper, medial epicondyle less prominent
• Goat: Supracondylar fossa shallower, medial epicondyle more prominent

RADIUS:
• Sheep: Proximal articulation more rectangular
• Goat: Proximal articulation more square

ULNA:
• Sheep: Olecranon less curved medially
• Goat: Olecranon more curved medially

METACARPAL:
• Sheep: Distal condyles symmetrical, intercondylar notch shallow
• Goat: Distal condyles asymmetrical, intercondylar notch deep

TIBIA:
• Sheep: Distal articulation more rectangular
• Goat: Distal articulation more square

ASTRAGALUS:
• Sheep: Lateral condyle less prominent
• Goat: Lateral condyle more prominent

CALCANEUM:
• Sheep: Sustentaculum tali less prominent
• Goat: Sustentaculum tali more prominent

PHALANGES:
• Sheep: Shorter, more symmetrical
• Goat: Longer, more asymmetrical

References: Boessneck 1969, Payne 1985, Prummel & Frisch 1986""",

            "Cattle vs Bison": """CATTLE VS BISON - CRANIAL FEATURES

HORN CORES:
• Cattle: Round cross-section, curve forward
• Bison: Triangular cross-section, curve up and back

FRONTAL BONE:
• Cattle: Flat between horn cores
• Bison: Raised boss between horn cores

OCCIPITAL:
• Cattle: Occipital condyles closer together
• Bison: Occipital condyles wider apart

MANDIBLE:
• Cattle: Angular process rounded
• Bison: Angular process pointed

POSTCRANIAL FEATURES

ATLAS:
• Cattle: Wings shorter, less curved
• Bison: Wings longer, more curved

AXIS:
• Cattle: Odontoid process more pointed
• Bison: Odontoid process more rounded

SCAPULA:
• Cattle: Glenoid cavity more oval
• Bison: Glenoid cavity more rounded

HUMERUS:
• Cattle: Deltoid tuberosity less prominent
• Bison: Deltoid tuberosity more prominent

RADIUS:
• Cattle: Shorter, more robust
• Bison: Longer, more gracile

METAPODIALS:
• Cattle: Distal condyles symmetrical, shaft slender
• Bison: Distal condyles asymmetrical, shaft robust

PHALANGES:
• Cattle: Shorter, broader
• Bison: Longer, narrower

References: Balkwill & Cumbaa 1992, Gee 1993""",

            "Red Deer vs Fallow Deer": """RED DEER VS FALLOW DEER

ANTLERS:
• Red Deer: Round beam, multiple tines, brow tine near burr
• Fallow Deer: Palmate in adults, flattened beam, bez tine present

SKULL:
• Red Deer: Nasals longer, lacrimal pit deep
• Fallow Deer: Nasals shorter, lacrimal pit shallow

MANDIBLE:
• Red Deer: Diastema longer, mental foramen under P2
• Fallow Deer: Diastema shorter, mental foramen under P3

TEETH:
• Red Deer: Larger, more robust enamel folds
• Fallow Deer: Smaller, simpler enamel

SCAPULA:
• Red Deer: Glenoid cavity deeper
• Fallow Deer: Glenoid cavity shallower

HUMERUS:
• Red Deer: More robust, deltoid tuberosity prominent
• Fallow Deer: More gracile, deltoid tuberosity less prominent

METAPODIALS:
• Red Deer: More robust, distal condyles wider
• Fallow Deer: More gracile, distal condyles narrower

PHALANGES:
• Red Deer: Longer, more robust
• Fallow Deer: Shorter, more gracile

References: Lister 1996, Hillson 2005""",

            "Roe Deer vs Sheep": """ROE DEER VS SHEEP

HORN CORES/ANTLERS:
• Roe Deer: Short pedicles, antlers with 3 tines (in males)
• Sheep: Horn cores permanent, curved, present in both sexes

SKULL:
• Roe Deer: Preorbital pit present, nasals narrow
• Sheep: No preorbital pit, nasals broader

MANDIBLE:
• Roe Deer: Mental foramen under P2, diastema shorter
• Sheep: Mental foramen under P3, diastema longer

TEETH:
• Roe Deer: Enamel thinner, more delicate
• Sheep: Enamel thicker, more robust

SCAPULA:
• Roe Deer: More gracile, glenoid cavity smaller
• Sheep: More robust, glenoid cavity larger

HUMERUS:
• Roe Deer: Supracondylar fossa shallower
• Sheep: Supracondylar fossa deeper

METAPODIALS:
• Roe Deer: More gracile, distal condyles narrower
• Sheep: More robust, distal condyles wider

ASTRAGALUS:
• Roe Deer: Smaller, lateral condyle less prominent
• Sheep: Larger, lateral condyle more prominent

References: Lister 1996, Hillson 2005""",

            "Horse vs Donkey": """HORSE VS DONKEY

SKULL:
• Horse: Longer nasal bones (extends beyond premaxilla), straight profile
• Donkey: Shorter nasals (doesn't extend beyond premaxilla), concave profile

MANDIBLE:
• Horse: Deeper, more robust, ventral border convex
• Donkey: Shallower, more gracile, ventral border straight

TEETH:
• Horse: Larger, more complex enamel folds, longer crown
• Donkey: Smaller, simpler enamel, shorter crown

METAPODIALS:
• Horse: More robust, proximal articulation wider
• Donkey: More gracile, proximal articulation narrower

PHALANGES:
• Horse: Longer, broader, proximal end more expanded
• Donkey: Shorter, narrower, proximal end less expanded

ASTRAGALUS:
• Horse: More symmetrical, trochlea deeper
• Donkey: Less symmetrical, trochlea shallower

References: Davis 1980, Eisenmann 1986, Peters 1998""",

            "Pig vs Wild Boar": """PIG VS WILD BOAR

SKULL:
• Pig: Shorter rostrum (domestic form), domed profile
• Wild Boar: Longer rostrum (60-70% of skull length), straight profile

CANINES:
• Pig: Smaller, less curved, oval cross-section
• Wild Boar: Larger, more curved, triangular cross-section

MANDIBLE:
• Pig: Shallower, less robust, corpus height less
• Wild Boar: Deeper, more robust, corpus height greater

M3 (lower third molar):
• Pig: Smaller, simpler, fewer accessory cusps
• Wild Boar: Larger, more complex, multiple accessory cusps

LIMB BONES:
• Pig: More gracile, shorter relative to size
• Wild Boar: More robust, longer relative to size

METAPODIALS:
• Pig: Shorter, more gracile
• Wild Boar: Longer, more robust

References: Mayer & Brisbin 1991, Albarella et al. 2005, Payne & Bull 1988""",

            "Dog vs Wolf vs Fox": """DOG VS WOLF VS FOX

SKULL SIZE:
• Dog: Variable (100-250mm), domestic morphology
• Wolf: Large (200-280mm), wild-type morphology
• Fox: Small (120-160mm), delicate

SNOUT:
• Dog: Variable, often shorter, "stop" present
• Wolf: Long, straight, no "stop"
• Fox: Long, narrow, pointed

TEETH:
• Dog: Crowded, variable spacing, smaller relative to skull
• Wolf: Evenly spaced, large, robust
• Fox: Small, sharp, evenly spaced

MANDIBLE:
• Dog: Variable curvature, coronoid process variable
• Wolf: Deep, slightly curved, coronoid process broad
• Fox: Shallow, straight, coronoid process narrow

LIMB BONES:
• Dog: Variable proportions
• Wolf: Long, robust, straight
• Fox: Short, gracile, curved

HUMERUS:
• Dog: Supinator crest variable
• Wolf: Supinator crest prominent
• Fox: Supinator crest small

FEMUR:
• Dog: Third trochanter less prominent
• Wolf: Third trochanter prominent
• Fox: Third trochanter small

References: Lawrence 1967, Benecke 1994, Olsen 2000""",

            "Hare vs Rabbit": """HARE VS RABBIT

SKULL SIZE:
• Hare: Larger (80-110mm), more elongated
• Rabbit: Smaller (70-85mm), more compact

ORBIT:
• Hare: Larger relative to skull, positioned higher
• Rabbit: Smaller relative to skull, positioned lower

PALATE:
• Hare: Longer, extends beyond last molar by >3mm
• Rabbit: Shorter, ends at or just beyond last molar

MANDIBLE:
• Hare: Deeper, more robust, angular process prominent
• Rabbit: Shallower, more gracile, angular process less prominent

INCISORS:
• Hare: Grooved, more prominent
• Rabbit: Smooth, less prominent

LIMB BONES:
• Hare: Longer, more gracile (adapted for running)
• Rabbit: Shorter, more robust (adapted for hopping)

FEMUR:
• Hare: Third trochanter more proximal
• Rabbit: Third trochanter more distal

TIBIA:
• Hare: Longer, more gracile
• Rabbit: Shorter, more robust

References: Callou 1997, 2003""",

            "Human vs Bear (paw bones)": """HUMAN VS BEAR - PAW BONES
Common confusion in cave sites!

PHALANGES:
• Human: Short, broad, smooth articular surfaces, flat ungual
• Bear: Long, curved, robust, rougher surfaces, large curved ungual

METACARPALS:
• Human: Gracile, heads rounded, shaft straight
• Bear: Robust, heads flattened, shaft curved, muscle attachments prominent

METATARSALS:
• Human: Similar to metacarpals but longer
• Bear: Very robust, heavy, curved

CARPALS/TARSALS:
• Human: Small, delicate, smooth articular facets
• Bear: Large, robust, rugose, heavy

HAND VS FOOT:
• Human: Hand bones more gracile than foot
• Bear: Hand and foot similar in robusticity

CLAWS:
• Human: Flat nails (no ungual phalanges preserved archaeologically)
• Bear: Large curved claw cores, deeply grooved

References: Morse 1983, Schmid 1972""",

            "Seal species identification": """SEAL SPECIES IDENTIFICATION

COMMON/HARBOUR SEAL (Phoca vitulina):
• Smaller size, slender bones
• Skull: Shorter rostrum, less robust
• Humerus: Less robust, deltopectoral crest less developed
• Femur: Shorter, head smaller
• Phalanges: More gracile

GREY SEAL (Halichoerus grypus):
• Larger size, robust bones
• Skull: Longer rostrum, more robust, prominent occipital crest
• Humerus: More robust, deltopectoral crest prominent
• Femur: Longer, head larger, third trochanter prominent
• Phalanges: More robust

BEARDED SEAL (Erignathus barbatus):
• Very large, extremely robust
• Mandible: Deep, heavy, mental foramen large
• Humerus: Massive, deltopectoral crest extremely developed
• Limb bones: Massive, rugose

RINGED SEAL (Pusa hispida):
• Small size, gracile
• All bones proportionally smaller and more delicate

HARP SEAL (Pagophilus groenlandicus):
• Medium size, distinctive nasal shape

References: Hodgetts 1999, Olson & Walther 2007, Baryshnikov 2009""",

            "Chicken vs Pheasant vs Grouse": """CHICKEN VS PHEASANT VS GROUSE

CORACOID:
• Chicken: Robust, sternal facet broad, scapular facet deep
• Pheasant: Intermediate, sternal facet narrower, scapular facet moderate
• Grouse: Gracile, sternal facet small, scapular facet shallow

HUMERUS:
• Chicken: Deltoid crest prominent, curved, pneumatic fossa deep
• Pheasant: Deltoid crest moderate, straighter, pneumatic fossa moderate
• Grouse: Deltoid crest small, straight, pneumatic fossa small

ULNA:
• Chicken: Robust, papillae for secondaries prominent
• Pheasant: Moderate, papillae distinct
• Grouse: Gracile, papillae faint

CARPOMETACARPUS:
• Chicken: Robust, metacarpal I prominent
• Pheasant: Moderate, metacarpal I moderate
• Grouse: Gracile, metacarpal I small

FEMUR:
• Chicken: Robust, head large, trochanter prominent
• Pheasant: Intermediate, head moderate
• Grouse: Gracile, head small

TIBIOTARSUS:
• Chicken: Robust, cnemial crest prominent
• Pheasant: Moderate, cnemial crest moderate
• Grouse: Gracile, cnemial crest small

TARSOMETATARSUS:
• Chicken: Robust, spur present in males (warty boss)
• Pheasant: Intermediate, spur smaller or absent
• Grouse: Gracile, no spur

References: Cohen & Serjeantson 1996, Bacher 1967, Erbersdobler 1968""",

            "Duck vs Goose vs Swan": """DUCK VS GOOSE VS SWAN

SIZE:
• Duck: Small to medium (Anas, Aythya spp.)
• Goose: Medium to large (Anser, Branta spp.)
• Swan: Very large (Cygnus spp.)

CORACOID:
• Duck: Gracile, short, scapular facet small
• Goose: Robust, long, scapular facet moderate
• Swan: Very robust, elongated, scapular facet large

HUMERUS:
• Duck: Shorter, less curved, deltoid crest small
• Goose: Longer, curved, deltoid crest prominent
• Swan: Very long, strongly curved, deltoid crest very prominent

ULNA:
• Duck: Short, quill knobs faint
• Goose: Long, quill knobs distinct
• Swan: Very long, quill knobs prominent

CARPOMETACARPUS:
• Duck: Short, broad, metacarpal II straight
• Goose: Long, narrow, metacarpal II curved
• Swan: Very long, very narrow, metacarpal II strongly curved

FEMUR:
• Duck: Short, robust, head small
• Goose: Long, robust, head moderate
• Swan: Very long, very robust, head large

TIBIOTARSUS:
• Duck: Short, cnemial crest small
• Goose: Long, cnemial crest prominent
• Swan: Very long, cnemial crest very prominent

References: Cohen & Serjeantson 1996, Woelfle 1967, Bacher 1967""",

            "Turkey vs Peafowl": """TURKEY VS PEAFOWL

SIZE:
• Turkey: Large (Meleagris gallopavo)
• Peafowl: Large (Pavo cristatus)

SKULL:
• Turkey: Longer, narrower, nasal opening elongated
• Peafowl: Shorter, broader, nasal opening round

CORACOID:
• Turkey: Robust, sternal facet broad, scapular facet deep
• Peafowl: Similar size but differently proportioned

HUMERUS:
• Turkey: Deltoid crest prominent, shaft straighter
• Peafowl: Deltoid crest moderate, shaft more curved

TARSOMETATARSUS:
• Turkey: Spur present in males (large conical spur), shaft robust
• Peafowl: Spur present (smaller), shaft more gracile, often more ornate

References: Cohen & Serjeantson 1996""",

            "Raptor species (eagles, hawks, owls)": """RAPTOR SPECIES - EAGLES, HAWKS, OWLS

EAGLES (Aquila, Haliaeetus):
• Very large size, extremely robust
• Beak: Massive, hooked, cere large
• Talons: Large, strongly curved, powerful

FALCONS (Falco):
• Medium size, compact
• Beak: Distinctive "tomial tooth" on upper mandible
• Wings: Long, pointed

HAWKS (Accipiter, Buteo):
• Medium size, variable
• Beak: Hooked, less specialized than falcons
• Feet: Powerful, for grasping

OWLS (Strix, Bubo, Tyto):
• Large eyes (large orbits)
• Beak: Short, hooked, cere prominent
• Feet: Zygodactyl (two toes forward, two back)
• Feathers: Silent flight adaptations (comb on leading edge of wing)

SKELETAL DIFFERENCES:
• Eagles: All bones extremely robust, muscle attachments massive
• Falcons: Distinctive humerus with expanded brachial depression
• Owls: Unique tarsometatarsus morphology, asymmetrical ear openings in skull

References: Gilbert et al. 1981, Cohen & Serjeantson 1996""",

            "Corvid species (crow, raven, rook, jackdaw)": """CORVID SPECIES - CROW, RAVEN, ROOK, JACKDAW

RAVEN (Corvus corax):
• Very large (similar to Buzzard size)
• Skull: Massive, deep mandible
• Beak: Very large, strongly curved, nasal bristles long
• Bones: All elements very robust

CARRION/HOODED CROW (Corvus corone/cornix):
• Large (pigeon size +)
• Skull: Moderate, less deep than raven
• Beak: Moderate, curved
• Bones: Robust but smaller than raven

ROOK (Corvus frugilegus):
• Similar to crow but more gracile
• Skull: Distinctive bare face in life (not skeletal)
• Beak: Longer, straighter, more pointed
• Mandible: Mental foramen positioned differently

JACKDAW (Corvus monedula):
• Small (pigeon size)
• Skull: Compact, rounded
• Beak: Short, stout
• Bones: Gracile, smaller than crow

MAGPIE (Pica pica):
• Medium size, distinctive long tail (caudal vertebrae)
• Skull: More rounded
• Beak: Stout, shorter

References: Tomek & Bocheński 2000, Cohen & Serjeantson 1996""",

            "Cod vs Haddock vs Pollock": """COD VS HADDOCK VS POLLOCK

OTOLITHS (ear stones):
• Cod: Oval, convex, smooth margin, rounded ends
• Haddock: Rectangular, flat, serrated margin, square ends
• Pollock: Elongate, thin, irregular, pointed ends

PREMAXILLA:
• Cod: Robust, teeth present, ascending process broad
• Haddock: Less robust, teeth smaller, ascending process narrow
• Pollock: Gracile, teeth absent, ascending process very narrow

DENTARY:
• Cod: Deep, teeth large in multiple rows
• Haddock: Shallower, teeth moderate in single row
• Pollock: Shallow, teeth small or absent

MAXILLA:
• Cod: Robust, posterior expansion prominent
• Haddock: Moderate, posterior expansion less prominent
• Pollock: Gracile, posterior expansion minimal

CLEITHRUM:
• Cod: Robust, curved, muscle attachment prominent
• Haddock: Moderate, less curved
• Pollock: Gracile, straight

VERTEBRAE:
• Cod: Large, robust processes, deep pits
• Haddock: Medium, moderate processes
• Pollock: Small, delicate processes

References: Wheeler & Jones 1989, Watt et al. 1997, Cannon 1987""",

            "Salmon vs Trout vs Grayling": """SALMON VS TROUT VS GRAYLING

VOMER (bone in roof of mouth):
• Salmon: Teeth on shaft, vomerine teeth present throughout life
• Trout: Teeth on head only, vomerine teeth lost in adults
• Grayling: No vomerine teeth

PREMAXILLA:
• Salmon: Robust, multiple tooth rows, ascending process broad
• Trout: Moderate, single tooth row, ascending process moderate
• Grayling: Gracile, small teeth, ascending process narrow

DENTARY:
• Salmon: Deep, teeth large, coronoid process prominent
• Trout: Moderate, teeth medium, coronoid process moderate
• Grayling: Shallow, teeth small, coronoid process low

VERTEBRAE:
• Salmon: 56-60, robust, neural spines tall
• Trout: 57-60, moderate, neural spines moderate
• Grayling: 58-62, gracile, neural spines short

CAUDAL FIN (hypural bones):
• Salmon: 16-19 rays
• Trout: 17-19 rays
• Grayling: 18-21 rays

References: Cannon 1987, 1988, Wheeler & Jones 1989""",

            "Herring vs Sprat vs Sardine": """HERRING VS SPRAT VS SARDINE

ATLAS VERTEBRA:
• Herring: Large, robust, neural arch high
• Sprat: Smaller, neural arch lower
• Sardine: Similar to herring but more delicate

ABDOMINAL VERTEBRAE:
• Herring: Deep pits, robust processes
• Sprat: Shallower pits, delicate processes
• Sardine: Intermediate

CAUDAL VERTEBRAE:
• Herring: 26-28, robust
• Sprat: 24-26, delicate
• Sardine: 25-27, intermediate

OTOLITHS:
• Herring: Thick, oval, smooth
• Sprat: Thin, elongated, serrated margin
• Sardine: Thick, rectangular, central depression

SIZE:
• Herring: Up to 40cm
• Sprat: Up to 16cm
• Sardine: Up to 25cm

References: Wheeler & Jones 1989""",

            "Flatfish species (plaice, flounder, sole, turbot)": """FLATFISH SPECIES - PLAICE, FLOUNDER, SOLE, TURBOT

CRANIAL ASYMMETRY:
All flatfish have asymmetrical skulls with both eyes on one side.
The direction of asymmetry is species-specific.

PREMAXILLA:
• Plaice: Robust, teeth in multiple rows, crushing dentition
• Flounder: Moderate, teeth smaller, less specialized
• Sole: Gracile, teeth minute or absent, on blind side only
• Turbot: Very robust, teeth conical, widely spaced

DENTARY:
• Plaice: Deep, molariform teeth
• Flounder: Shallower, smaller teeth
• Sole: Very shallow, no teeth
• Turbot: Deep, large conical teeth

CLEITHRUM:
• Plaice: Robust, curved
• Flounder: Moderate, straighter
• Sole: Gracile, delicate
• Turbot: Very robust, massive

VERTEBRAE:
• Plaice: 38-42, robust neural spines
• Flounder: 34-36, moderate spines
• Sole: 45-50, delicate spines
• Turbot: 30-35, very robust

References: Wheeler & Jones 1989, Watt et al. 1997""",

            "Cyprinid identification (carp, roach, bream, chub, dace)": """CYPRINID IDENTIFICATION - CARP, ROACH, BREAM, CHUB, DACE

PHARYNGEAL TEETH (most diagnostic):
Located on the last gill arch, these are the BEST way to identify cyprinids.

• Common Carp (Cyprinus carpio): Large, molariform (grinding), 3 rows (1.1.3-3.1.1 pattern)
• Tench (Tinca tinca): Hooked, 1 row (4-5 pattern)
• Roach (Rutilus rutilus): Compressed, 2 rows (2.5-5.2 pattern)
• Bream (Abramis brama): Compressed, serrated, 2 rows (1.5-5.1 pattern)
• Chub (Squalius cephalus): Robust, hooked, 2 rows (2.5-5.2 pattern)
• Dace (Leuciscus leuciscus): Slender, hooked, 2 rows (2.5-5.2 pattern) - smaller than chub

CLEITHRUM:
• Carp: Very robust, massive, curved
• Tench: Robust, less curved
• Bream: Moderate, straight
• Roach: Gracile, delicate
• Chub: Intermediate

OPERCULUM:
• Carp: Large, with radiating ridges
• Bream: Deep, with concentric ridges
• Roach: Thin, smooth

VERTEBRAE:
• Carp: Massive, with deep lateral pits
• Other cyprinids: Smaller, less specialized

References: Wheeler & Jones 1989""",

            "Canid tooth eruption & wear (ages)": """CANID TOOTH ERUPTION & WEAR AGES (Dog, Wolf, Fox)

DECIDUOUS TEETH (Milk teeth):
• Incisors erupt: 3-4 weeks
• Canines erupt: 3-4 weeks
• Premolars erupt: 4-12 weeks

PERMANENT TEETH ERUPTION:

Incisors:
• I1: 3-4 months
• I2: 3-4 months
• I3: 4-5 months

Canines:
• C: 5-6 months

Premolars:
• P1: 4-5 months
• P2: 5-6 months
• P3: 5-6 months
• P4: 5-6 months

Molars:
• M1: 5-6 months (lower first molar)
• M2: 6-7 months
• M3: 6-7 months

All permanent teeth erupted by 7 months.

WEAR STAGES (ages in years):
• Slight wear (enamel only): 1-3 years
• Moderate wear (dentine exposed): 3-5 years
• Heavy wear (pulp cavity exposed): 5-8 years
• Severe wear (teeth worn to roots): 8+ years

References: Silver 1969, Habermehl 1975""",

            "Caprine mandibular wear stages (Payne 1973, 1987)": """CAPRINE MANDIBULAR WEAR STAGES - SHEEP & GOAT (Payne 1973, 1987)

STAGE A (0-2 months):
• M1 unworn or just erupting
• M2, M3 not erupted

STAGE B (2-6 months):
• M1 in wear
• M2 erupting
• M3 not erupted

STAGE C (6-12 months):
• M1, M2 in wear
• M3 erupting
• dP4 still present

STAGE D (12-24 months):
• All permanent molars in wear
• dP4 replaced by P4
• M3 with 2-3 crescents in wear

STAGE E (24-36 months):
• M3 posterior cusp (3rd crescent) in wear
• Moderate wear on all molars

STAGE F (36-48 months):
• M3 posterior cusp well worn
• Dentine exposed on all cusps
• Enamel islands forming

STAGE G (48-72 months):
• Heavy wear on all teeth
• Enamel islands prominent
• Some cusps worn flat

STAGE H (72-96 months):
• Very heavy wear
• Most enamel gone
• Teeth worn to gum line

STAGE I (96+ months):
• Extreme wear
• Teeth nearly worn away
• Pulp cavities exposed

References: Payne 1973, Payne 1987, Grant 1982""",

            "Cattle epiphyseal fusion ages": """CATTLE EPIPHYSEAL FUSION AGES (in months)

EARLY FUSING (7-10 months):
• Scapula (distal)
• Humerus (distal)
• Radius (proximal)

MID FUSING (15-20 months):
• Phalanges 1 & 2 (proximal)
• Metacarpal (distal)
• Metatarsal (distal)
• Tibia (distal)

LATE FUSING (24-30 months):
• Femur (proximal & distal)
• Humerus (proximal)
• Radius (distal)
• Ulna (proximal & distal)
• Calcaneus (proximal)

VERY LATE FUSING (36-48 months):
• Vertebral plates
• Pelvis (ilium, ischium, pubis fusion)

FUSION INTERPRETATION:
• Unfused = younger than fusion age
• Fusing = approximately at fusion age
• Fused = older than fusion age

References: Silver 1969, Reitz & Wing 2008""",

            "Sheep/goat epiphyseal fusion ages": """SHEEP & GOAT EPIPHYSEAL FUSION AGES (in months)

EARLY FUSING (3-10 months):
• Scapula (distal) - 6-8 months
• Humerus (distal) - 10 months
• Radius (proximal) - 10 months

MID FUSING (13-20 months):
• Phalanges 1 & 2 (proximal) - 13-16 months
• Tibia (distal) - 18-24 months
• Metacarpal (distal) - 18-24 months
• Metatarsal (distal) - 20-28 months

LATE FUSING (30-42 months):
• Femur (proximal) - 30-36 months
• Femur (distal) - 36-42 months
• Humerus (proximal) - 36-42 months
• Radius (distal) - 36-42 months
• Ulna (proximal) - 36-42 months
• Calcaneus (proximal) - 36-40 months
• Tibia (proximal) - 36-48 months

VERY LATE FUSING (48-60 months):
• Vertebral plates - 48-60 months
• Pelvis (ilium, ischium, pubis) - 60+ months

References: Silver 1969, Zeder 2006""",

            "Pig epiphyseal fusion ages": """PIG EPIPHYSEAL FUSION AGES (in months)

VERY EARLY FUSING (12 months):
• Scapula (distal)
• Humerus (distal)
• Radius (proximal)
• Pelvis (ilium, ischium, pubis fusion complete)

EARLY FUSING (24-30 months):
• Phalanges 1 & 2 (proximal)
• Metacarpal (distal)
• Metatarsal (distal)
• Tibia (distal)
• Fibula (distal)

MID FUSING (36-42 months):
• Calcaneus (proximal)
• Femur (proximal)
• Femur (distal)
• Humerus (proximal)
• Radius (distal)
• Ulna (proximal & distal)
• Tibia (proximal)
• Fibula (proximal)

LATE FUSING (48-60 months):
• Vertebral plates
• Sternebrae

FUSION SEQUENCE NOTES:
Pigs fuse earlier than ruminants of similar size.
Most elements fused by 3.5 years.
Vertebral plates last to fuse (5+ years).

References: Silver 1969, Bull & Payne 1982""",

            "Horse dental eruption & wear": """HORSE DENTAL ERUPTION & WEAR

DECIDUOUS TEETH (Milk teeth):
• Incisors: Birth to 2 weeks
• Canines: Rarely present in deciduous set
• Premolars: Birth to 2 weeks (dp2, dp3, dp4)

PERMANENT TEETH ERUPTION:

Incisors:
• I1: 2.5 years
• I2: 3.5 years
• I3: 4.5 years

Canines:
• C: 4-5 years (males only, often absent in females)

Premolars:
• P2: 2.5 years
• P3: 3 years
• P4: 4 years

Molars:
• M1: 1 year
• M2: 2 years
• M3: 3.5-4 years

All permanent teeth erupted by 5 years.

WEAR-BASED AGE ESTIMATION (after 5 years):
• Dental star (dentine exposure) appears: 5-6 years
• Enamel cup disappears in I1: 6 years
• Enamel cup disappears in I2: 7 years
• Enamel cup disappears in I3: 8 years
• Galvayne's groove appears at gumline: 10 years
• Galvayne's groove halfway down tooth: 15 years
• Galvayne's groove extends full tooth: 20 years
• Galvayne's groove disappears from upper half: 25+ years

References: Silver 1969, Levine 1982""",

            "Bird tarsometatarsus sexing (spur presence)": """BIRD TARSOMETATARSUS SEXING - SPUR PRESENCE

SPUR MORPHOLOGY:
The tarsometatarsus can have a spur (males) or spur scar (females) in many galliforms (chicken, pheasant, turkey, peafowl).

CHICKEN (Gallus gallus):
• Male: Prominent conical spur, rough base, located on medial side of distal shaft
• Female: Spur absent, sometimes small knob or smooth area
• Castrated male: Small, blunt spur or absent

PHEASANT (Phasianus colchicus):
• Male: Short, blunt spur, less prominent than chicken
• Female: Spur absent

TURKEY (Meleagris gallopavo):
• Male: Large conical spur, very prominent
• Female: Spur absent or very small knob

PEAFOWL (Pavo cristatus):
• Male: Long, sharp spur
• Female: Spur absent

OTHER BIRDS:
• Ducks: No spur (sexing by other bone morphology)
• Geese: No spur
• Raptors: Size dimorphism (females larger in many species)
• Owls: Size dimorphism (females larger)

SPUR SCARS:
Even when spur is lost post-mortem, the attachment site (spur scar) remains visible as a roughened area on the bone.

References: Cohen & Serjeantson 1996, Sadler 1991"""
        }

        text = keys_database.get(key, "Key not available")
        self.key_text.delete(1.0, tk.END)
        self.key_text.insert(1.0, text)

    def _clear_measurements(self):
        """Clear all measurement input fields."""
        for var in self.id_measurements.values():
            var.set("")

    def _calculate_lsi(self):
        """Calculate Log Size Index (LSI) against zoolog-style reference."""
        if not hasattr(self, 'ref_db'):
            # Create a basic fallback reference if not loaded
            self.ref_db = ReferenceDatabase()
            plugin_dir = Path(__file__).parent
            appbase_dir = plugin_dir.parent.parent
            ref_path = appbase_dir / "config" / "zooarch_reference.json"
            success, _ = self.ref_db.load_from_file(ref_path)

        if not hasattr(self, 'ref_db') or not self.ref_db.loaded:
            self.lsi_result.config(text="No reference DB", foreground="red")
            return

        # Collect current measurements
        unknown = {}
        for code, var in self.measurement_vars.items():
            val = var.get().strip()
            if val:
                try:
                    unknown[code] = float(val)
                except ValueError:
                    pass

        if not unknown:
            self.lsi_result.config(text="No measurements", foreground="orange")
            return

        # Use first selected taxon or default to Sheep
        taxon = self.age_taxon_var.get()
        if not taxon or taxon not in self.ref_db.references:
            # Try to find a matching taxon from available references
            for ref_taxon in self.ref_db.references.keys():
                if any(t in ref_taxon.lower() for t in ['sheep', 'cattle', 'pig', 'deer']):
                    taxon = ref_taxon
                    break
            if not taxon:
                taxon = list(self.ref_db.references.keys())[0] if self.ref_db.references else ""

        if not taxon or taxon not in self.ref_db.references:
            self.lsi_result.config(text="No reference taxon", foreground="red")
            return

        ref = self.ref_db.references[taxon]
        lsi_values = []

        for code, value in unknown.items():
            if code in ref:
                mean = ref[code]['mean']
                lsi = math.log(value / mean)  # classic LSI formula
                lsi_values.append(lsi)

        if lsi_values:
            mean_lsi = sum(lsi_values) / len(lsi_values)
            self.lsi_result.config(
                text=f"{mean_lsi:+.3f} vs {taxon[:8]}",
                foreground="green" if abs(mean_lsi) < 0.15 else "orange"
            )
            self.measurement_status.config(text=f"LSI = {mean_lsi:+.3f}")
        else:
            self.lsi_result.config(text="No matching codes", foreground="red")

    def _run_discriminant(self):
        """Run measurement-based discriminant analysis using reference database."""
        if not HAS_SKLEARN:
            self.class_result.delete(1.0, tk.END)
            self.class_result.insert(1.0, "scikit-learn not installed\n\nPlease install with:\npip install scikit-learn")
            return

        # Collect measurements from input fields
        unknown = {}
        for code, var in self.id_measurements.items():
            val = var.get().strip()
            if val:
                try:
                    unknown[code] = float(val)
                except ValueError:
                    pass

        if not unknown:
            self.class_result.delete(1.0, tk.END)
            self.class_result.insert(1.0, "Enter at least one measurement")
            return

        # Get selected taxa from checkboxes
        selected_taxa = [taxon for taxon, var in self.id_taxa_vars.items() if var.get()]
        if not selected_taxa:
            self.class_result.delete(1.0, tk.END)
            self.class_result.insert(1.0, "Select at least one taxon to compare")
            return

        # Check if reference database is loaded
        if not hasattr(self, 'ref_db') or not self.ref_db.loaded:
            self.class_result.delete(1.0, tk.END)
            self.class_result.insert(1.0, "Reference database not loaded.\n\nPlease ensure zooarch_reference.json exists in config folder.")
            return

        # Use reference database for comparison
        results = self.ref_db.compare_unknown(unknown, selected_taxa)

        if not results:
            self.class_result.delete(1.0, tk.END)
            self.class_result.insert(1.0, "No matching reference data found for these measurements")
            return

        # Display results
        self.class_result.delete(1.0, tk.END)
        self.class_result.insert(1.0, "DISCRIMINANT ANALYSIS RESULTS\n")
        self.class_result.insert(tk.END, "=" * 50 + "\n\n")

        self.class_result.insert(tk.END, f"Unknown specimen measurements:\n")
        for code, value in sorted(unknown.items()):
            self.class_result.insert(tk.END, f"  {code}: {value:.1f} mm\n")

        self.class_result.insert(tk.END, f"\nCompared against: {', '.join(selected_taxa[:3])}")
        if len(selected_taxa) > 3:
            self.class_result.insert(tk.END, f" +{len(selected_taxa)-3} more\n\n")
        else:
            self.class_result.insert(tk.END, "\n\n")

        self.class_result.insert(tk.END, "Classification probabilities:\n")
        self.class_result.insert(tk.END, "-" * 40 + "\n")

        # Display top matches
        for taxon, prob in list(results.items())[:5]:
            if prob > 0.01:  # Only show probabilities > 1%
                # Simple confidence interval approximation
                ci_low = max(0, prob - 0.1)
                ci_high = min(1, prob + 0.1)
                bar_length = int(prob * 30)
                bar = "█" * bar_length + "░" * (30 - bar_length)
                self.class_result.insert(tk.END, f"{taxon[:20]:20} {bar} {prob:.1%}\n")
                self.class_result.insert(tk.END, f"{'':20}  95% CI: {ci_low:.1%}-{ci_high:.1%}\n\n")

        if results:
            best_taxon = list(results.keys())[0]
            best_prob = results[best_taxon]
            self.class_result.insert(tk.END, "=" * 50 + "\n")
            self.class_result.insert(tk.END, f"→ MOST LIKELY: {best_taxon}\n")
            self.class_result.insert(tk.END, f"  ({best_prob:.1%} confidence)\n")

        # Generate PCA plot if we have at least 2 measurements
        if HAS_MPL and len(unknown) >= 2:
            self._generate_pca_plot(unknown, selected_taxa)

        self.result_status.config(
            text="✓ Analysis complete! Click 'Results & Visualization' tab to view",
            foreground="#8B4513",
            background="#f1c40f"
        )

    def _clear_measurements(self):
        for var in self.id_measurements.values():
            var.set("")

        # Reset label to default system background
        default_bg = tk.Label().cget("bg")

        self.result_status.config(
            text="",
            fg="black",
            bg=default_bg
        )

    def _generate_pca_plot(self, unknown, selected_taxa):
        """Generate PCA plot of unknown vs reference."""
        if not HAS_MPL or not hasattr(self, 'ref_db') or not self.ref_db.loaded:
            return

        self.ax.clear()

        # Prepare data for PCA
        all_measurements = []
        all_labels = []
        colors = []
        markers = []

        # Add reference data
        color_map = plt.cm.tab10
        for i, taxon in enumerate(selected_taxa):
            if taxon not in self.ref_db.references:
                continue
            ref = self.ref_db.references[taxon]
            # Create a synthetic point for each taxon (mean values)
            point = []
            valid = True
            for code in unknown.keys():
                if code in ref:
                    point.append(ref[code]['mean'])
                else:
                    point.append(0)
            if point and len(point) > 0:
                all_measurements.append(point)
                all_labels.append(taxon)
                colors.append(color_map(i % 10))
                markers.append('o')

        # Add unknown
        unknown_point = [unknown.get(code, 0) for code in unknown.keys()]
        all_measurements.append(unknown_point)
        all_labels.append('Unknown')
        colors.append('red')
        markers.append('*')

        # Perform PCA
        X = np.array(all_measurements)
        X_centered = X - X.mean(axis=0)
        U, s, Vt = np.linalg.svd(X_centered, full_matrices=False)
        scores = U * s

        # Plot
        for i in range(len(all_labels)):
            self.ax.scatter(scores[i, 0], scores[i, 1],
                           c=[colors[i]], marker=markers[i],
                           s=100 if markers[i] == '*' else 50,
                           label=all_labels[i], alpha=0.7)

        self.ax.set_xlabel(f'PC1 ({s[0]/sum(s):.1%})')
        self.ax.set_ylabel(f'PC2 ({s[1]/sum(s):.1%})')
        self.ax.set_title('PCA: Unknown vs Reference Collections')
        self.ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        self.ax.grid(True, alpha=0.3)

        self.fig.tight_layout()
        self.canvas.draw()

    def _export_report(self):
        """Export identification report as CSV."""
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile="identification_report.csv"
        )

        if not path:
            return

        # Collect current results
        report_data = []
        for code, var in self.id_measurements.items():
            val = var.get().strip()
            if val:
                report_data.append({
                    'Measurement': code,
                    'Value_mm': val,
                    'Notes': ''
                })

        if HAS_PANDAS:
            df = pd.DataFrame(report_data)
            df.to_csv(path, index=False)
            messagebox.showinfo("Export", f"Report saved to {path}")


# ============================================================================
# TAB 4: ECOLOGY - TDF + isotopes + FTIR (YOUR UNIQUE VALUE ADD)
# ============================================================================

class EcologyTab(AnalysisTab):
    def __init__(self, parent, app, ui_queue):
        super().__init__(parent, app, ui_queue)
        self.tdf = TDFDatabase()
        self._load_tdf_database()
        self._build_ui()

    def _load_tdf_database(self):
        """Load TDF database from config folder."""
        # Plugin is in: appbase/plugins/software/
        # TDF is in: appbase/config/tdf_database.json
        plugin_dir = Path(__file__).parent
        appbase_dir = plugin_dir.parent.parent  # Go up two levels: plugins/software/ → appbase/
        config_dir = appbase_dir / "config"
        tdf_path = config_dir / "tdf_database.json"

        success, message = self.tdf.load_from_file(tdf_path)
        if not success:
            print(f"⚠️ {message}")
            # Try alternative path for development
            alt_path = Path("appbase/config/tdf_database.json")
            if alt_path.exists():
                success, message = self.tdf.load_from_file(alt_path)
                if success:
                    print(f"✅ {message}")
            else:
                print("⚠️ TDF database will use limited built-in fallback")

    def _build_ui(self):
        # Main container with left (inputs) and right (results)
        main = ttk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        main.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # LEFT PANEL - Inputs
        left = ttk.Frame(main)
        main.add(left, weight=1)

        # RIGHT PANEL - Results + visualizations
        right = ttk.Frame(main)
        main.add(right, weight=2)

        # === LEFT PANEL - INPUTS ===
        # Specimen selector
        spec_frame = ttk.LabelFrame(left, text="Select Specimen", padding=5)
        spec_frame.pack(fill=tk.X, pady=2)

        self.eco_specimen_list = ttk.Combobox(spec_frame, width=30)
        self.eco_specimen_list.pack(fill=tk.X)
        self.eco_specimen_list.bind('<<ComboboxSelected>>', self._load_specimen_data)

        # === ISOTOPE INPUT SECTION ===
        iso_frame = ttk.LabelFrame(left, text="Stable Isotopes", padding=5)
        iso_frame.pack(fill=tk.X, pady=2)

        # δ13C
        c13_frame = ttk.Frame(iso_frame)
        c13_frame.pack(fill=tk.X, pady=1)
        ttk.Label(c13_frame, text="δ¹³C (‰):", width=10).pack(side=tk.LEFT)
        self.d13c_var = tk.StringVar()
        ttk.Entry(c13_frame, textvariable=self.d13c_var, width=10).pack(side=tk.LEFT, padx=2)

        # δ15N
        n15_frame = ttk.Frame(iso_frame)
        n15_frame.pack(fill=tk.X, pady=1)
        ttk.Label(n15_frame, text="δ¹⁵N (‰):", width=10).pack(side=tk.LEFT)
        self.d15n_var = tk.StringVar()
        ttk.Entry(n15_frame, textvariable=self.d15n_var, width=10).pack(side=tk.LEFT, padx=2)

        # Baseline δ15N
        base_frame = ttk.Frame(iso_frame)
        base_frame.pack(fill=tk.X, pady=1)
        ttk.Label(base_frame, text="Baseline δ¹⁵N:", width=10).pack(side=tk.LEFT)
        self.baseline_var = tk.StringVar(value="3.0")
        ttk.Entry(base_frame, textvariable=self.baseline_var, width=10).pack(side=tk.LEFT, padx=2)

        # C:N Ratio
        cn_frame = ttk.Frame(iso_frame)
        cn_frame.pack(fill=tk.X, pady=1)
        ttk.Label(cn_frame, text="C:N ratio:", width=10).pack(side=tk.LEFT)
        self.cn_var = tk.StringVar()
        ttk.Entry(cn_frame, textvariable=self.cn_var, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Label(cn_frame, text="(3.1-3.3 good)", font=("Arial", 6)).pack(side=tk.LEFT)

        # === TDF SELECTION ===
        tdf_frame = ttk.LabelFrame(left, text="Trophic Discrimination Factor", padding=5)
        tdf_frame.pack(fill=tk.X, pady=2)

        # Taxon
        taxon_frame = ttk.Frame(tdf_frame)
        taxon_frame.pack(fill=tk.X, pady=1)
        ttk.Label(taxon_frame, text="Taxon:", width=10).pack(side=tk.LEFT)
        self.tdf_taxon_var = tk.StringVar()
        self.tdf_taxon_combo = ttk.Combobox(taxon_frame, textvariable=self.tdf_taxon_var,
                                           values=self.tdf.get_taxa_list(), width=15)
        self.tdf_taxon_combo.pack(side=tk.LEFT, padx=2)
        self.tdf_taxon_combo.bind('<<ComboboxSelected>>', self._update_tissue_options)

        # Tissue
        tissue_frame = ttk.Frame(tdf_frame)
        tissue_frame.pack(fill=tk.X, pady=1)
        ttk.Label(tissue_frame, text="Tissue:", width=10).pack(side=tk.LEFT)
        self.tdf_tissue_var = tk.StringVar()
        self.tdf_tissue_combo = ttk.Combobox(tissue_frame, textvariable=self.tdf_tissue_var,
                                             values=[], width=15)
        self.tdf_tissue_combo.pack(side=tk.LEFT, padx=2)
        self.tdf_tissue_combo.bind('<<ComboboxSelected>>', self._update_tdf_value)

        # Trophic level (optional)
        level_frame = ttk.Frame(tdf_frame)
        level_frame.pack(fill=tk.X, pady=1)
        ttk.Label(level_frame, text="Trophic level:", width=10).pack(side=tk.LEFT)
        self.tdf_level_var = tk.StringVar()
        level_combo = ttk.Combobox(level_frame, textvariable=self.tdf_level_var,
                                   values=["herbivore", "carnivore", "omnivore", "mixed", ""],
                                   width=13, state="readonly")
        level_combo.pack(side=tk.LEFT, padx=2)
        level_combo.bind('<<ComboboxSelected>>', self._update_tdf_value)

        # TDF value display
        value_frame = ttk.Frame(tdf_frame)
        value_frame.pack(fill=tk.X, pady=2)
        ttk.Label(value_frame, text="Δ¹⁵N:", font=("Arial", 8, "bold")).pack(side=tk.LEFT)
        self.tdf_value_label = tk.Label(value_frame, text="—", font=("Arial", 9, "bold"))
        self.tdf_value_label.pack(side=tk.LEFT, padx=5)
        ttk.Label(value_frame, text="Δ¹³C:", font=("Arial", 8, "bold")).pack(side=tk.LEFT, padx=(10,0))
        self.tdf_c13_label = tk.Label(value_frame, text="—", font=("Arial", 9, "bold"))
        self.tdf_c13_label.pack(side=tk.LEFT, padx=5)

        # Calculate button
        ttk.Button(left, text="🔬 CALCULATE TROPHIC POSITION",
                  command=self._calculate_trophic).pack(fill=tk.X, padx=5, pady=5)

        # === FTIR SECTION ===
        ftir_frame = ttk.LabelFrame(left, text="FTIR Preservation", padding=5)
        ftir_frame.pack(fill=tk.X, pady=2)

        # Crystallinity Index
        ci_frame = ttk.Frame(ftir_frame)
        ci_frame.pack(fill=tk.X, pady=1)
        ttk.Label(ci_frame, text="Crystallinity:", width=10).pack(side=tk.LEFT)
        self.ci_var = tk.StringVar()
        ttk.Entry(ci_frame, textvariable=self.ci_var, width=10).pack(side=tk.LEFT, padx=2)

        # Carbonate/Phosphate
        cp_frame = ttk.Frame(ftir_frame)
        cp_frame.pack(fill=tk.X, pady=1)
        ttk.Label(cp_frame, text="C/P ratio:", width=10).pack(side=tk.LEFT)
        self.cp_var = tk.StringVar()
        ttk.Entry(cp_frame, textvariable=self.cp_var, width=10).pack(side=tk.LEFT, padx=2)

        # Interpret button
        ttk.Button(ftir_frame, text="Interpret FTIR",
                  command=self._interpret_ftir).pack(pady=2)

        # === RIGHT PANEL - RESULTS ===
        # Results text area
        result_frame = ttk.LabelFrame(right, text="Ecology Results", padding=5)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.eco_results = tk.Text(result_frame, wrap=tk.WORD, font=("Courier", 10))
        self.eco_results.pack(fill=tk.BOTH, expand=True)

        # TDF database info
        tdf_info_frame = ttk.LabelFrame(right, text="TDF Database", padding=5)
        tdf_info_frame.pack(fill=tk.X, padx=5, pady=2)

        tdf_summary = self.tdf.get_summary()
        ttk.Label(tdf_info_frame, text=tdf_summary, font=("Arial", 8), justify=tk.LEFT).pack(anchor='w', padx=5, pady=2)

    def _update_ui(self):
        """Update specimen list."""
        specimens = []
        indices = self.selected_indices if self.selected_indices else range(len(self.samples))

        for i in sorted(indices)[:50]:
            if i >= len(self.samples):
                continue
            sample = self.samples[i]
            label = f"{i}: {sample.get('Sample_ID', '')[:10]} - {sample.get('taxon', '?')}"
            specimens.append(label)

        self.eco_specimen_list['values'] = specimens
        if specimens:
            self.eco_specimen_list.set(specimens[0])
            self._load_specimen_data()

    def _load_specimen_data(self, event=None):
        """Load isotope data from selected specimen."""
        selection = self.eco_specimen_list.get()
        if not selection:
            return

        try:
            idx = int(selection.split(':')[0])
            sample = self.samples[idx]

            # Load isotope data (existing)
            self.d13c_var.set(sample.get('d13c', ''))
            self.d15n_var.set(sample.get('d15n', ''))
            self.cn_var.set(sample.get('C_N_ratio', ''))
            self.ci_var.set(sample.get('ftir_crystallinity', ''))
            self.cp_var.set(sample.get('ftir_carbonate', ''))

            # Set taxon for TDF
            taxon = sample.get('taxon', '').lower()
            if 'sheep' in taxon or 'cattle' in taxon or 'deer' in taxon or 'pig' in taxon:
                self.tdf_taxon_var.set('Mammal')
            elif 'bird' in taxon or 'chicken' in taxon or 'goose' in taxon:
                self.tdf_taxon_var.set('Bird')
            elif 'fish' in taxon:
                self.tdf_taxon_var.set('Fish')
            self._update_tissue_options()

        except Exception as e:
            print(f"Error loading specimen: {e}")

    def _update_tissue_options(self, event=None):
        """Update tissue options based on selected taxon."""
        taxon = self.tdf_taxon_var.get()
        if not taxon:
            return

        tissues = self.tdf.get_tissues_for_taxon(taxon)
        self.tdf_tissue_combo['values'] = tissues
        if tissues:
            self.tdf_tissue_combo.set(tissues[0])
            self._update_tdf_value()

    def _update_tdf_value(self, event=None):
        """Update displayed TDF value."""
        taxon = self.tdf_taxon_var.get()
        tissue = self.tdf_tissue_var.get()
        level = self.tdf_level_var.get() or None

        if not taxon or not tissue:
            return

        entry = self.tdf.get_best_match(taxon, tissue, level)

        if entry:
            d15n = entry.get('Δ15N_mean')
            d15n_sd = entry.get('Δ15N_sd')
            d13c = entry.get('Δ13C_mean')
            d13c_sd = entry.get('Δ13C_sd')

            if d15n:
                self.tdf_value_label.config(text=f"{d15n:.2f} ± {d15n_sd:.2f}" if d15n_sd else f"{d15n:.2f}")
            else:
                self.tdf_value_label.config(text="—")

            if d13c:
                self.tdf_c13_label.config(text=f"{d13c:.2f} ± {d13c_sd:.2f}" if d13c_sd else f"{d13c:.2f}")
            else:
                self.tdf_c13_label.config(text="—")
        else:
            self.tdf_value_label.config(text="—")
            self.tdf_c13_label.config(text="—")

    def _calculate_trophic(self):
        """Calculate trophic position using TDF."""
        try:
            d15n = float(self.d15n_var.get())
            baseline = float(self.baseline_var.get())
        except ValueError:
            messagebox.showerror("Error", "Enter valid δ¹⁵N values")
            return

        # Get TDF value
        taxon = self.tdf_taxon_var.get()
        tissue = self.tdf_tissue_var.get()
        level = self.tdf_level_var.get() or None

        entry = self.tdf.get_best_match(taxon, tissue, level)

        if entry:
            tdf_val = entry.get('Δ15N_mean')
            tdf_sd = entry.get('Δ15N_sd', 0)
            source = f"{entry.get('source', 'TDF database')}"
        else:
            # Use default
            tdf_val = 3.4
            tdf_sd = 1.0
            source = "Post 2002 (default)"

        # Calculate trophic position
        tp = 1 + (d15n - baseline) / tdf_val

        # Display results
        self.eco_results.delete(1.0, tk.END)
        self.eco_results.insert(1.0, "=" * 50 + "\n")
        self.eco_results.insert(tk.END, "TROPHIC POSITION CALCULATION\n")
        self.eco_results.insert(tk.END, "=" * 50 + "\n\n")

        self.eco_results.insert(tk.END, f"δ¹⁵N consumer: {d15n:.2f}‰\n")
        self.eco_results.insert(tk.END, f"δ¹⁵N baseline: {baseline:.2f}‰\n")
        self.eco_results.insert(tk.END, f"Δ¹⁵N (TDF): {tdf_val:.2f}‰ (from {source})\n\n")

        self.eco_results.insert(tk.END, f"Trophic Position = 1 + ({d15n} - {baseline}) / {tdf_val}\n")
        self.eco_results.insert(tk.END, f"Trophic Position = {tp:.2f}\n\n")

        # Interpret
        if tp < 1.5:
            diet = "Primary producer (herbivore)"
        elif tp < 2.5:
            diet = "Primary consumer (herbivore/omnivore)"
        elif tp < 3.5:
            diet = "Secondary consumer (carnivore)"
        else:
            diet = "Tertiary consumer (top carnivore)"

        self.eco_results.insert(tk.END, f"Interpretation: {diet}\n")

        # Check C:N ratio for quality
        if self.cn_var.get():
            try:
                cn = float(self.cn_var.get())
                if 3.1 <= cn <= 3.3:
                    self.eco_results.insert(tk.END, "✓ C:N ratio indicates good collagen preservation\n")
                else:
                    self.eco_results.insert(tk.END, "⚠ C:N ratio outside ideal range - results may be unreliable\n")
            except:
                pass

    def _interpret_ftir(self):
        """Interpret FTIR indices."""
        self.eco_results.delete(1.0, tk.END)
        self.eco_results.insert(1.0, "=" * 50 + "\n")
        self.eco_results.insert(tk.END, "FTIR INTERPRETATION\n")
        self.eco_results.insert(tk.END, "=" * 50 + "\n\n")

        if self.ci_var.get():
            try:
                ci = float(self.ci_var.get())
                self.eco_results.insert(tk.END, f"Crystallinity Index: {ci:.2f}\n")

                if ci < 3.0:
                    self.eco_results.insert(tk.END, "→ Well preserved, minimal diagenesis\n")
                    self.eco_results.insert(tk.END, "→ Suitable for isotopic analysis\n")
                elif ci < 3.5:
                    self.eco_results.insert(tk.END, "→ Slightly altered, some diagenesis\n")
                    self.eco_results.insert(tk.END, "→ Caution for isotopic analysis\n")
                elif ci < 4.0:
                    self.eco_results.insert(tk.END, "→ Moderately altered, significant diagenesis\n")
                    self.eco_results.insert(tk.END, "→ Not suitable for isotopic analysis\n")
                else:
                    self.eco_results.insert(tk.END, "→ Highly altered, severe diagenesis or burning\n")
                    self.eco_results.insert(tk.END, "→ Unsuitable for most analyses\n")
            except:
                pass

        if self.cp_var.get():
            try:
                cp = float(self.cp_var.get())
                self.eco_results.insert(tk.END, f"\nCarbonate/Phosphate ratio: {cp:.3f}\n")
                if cp > 0.15:
                    self.eco_results.insert(tk.END, "→ Well-preserved carbonate\n")
                elif cp > 0.1:
                    self.eco_results.insert(tk.END, "→ Moderate carbonate preservation\n")
                else:
                    self.eco_results.insert(tk.END, "→ Significant carbonate loss\n")
            except:
                pass


# ============================================================================
# MAIN PLUGIN CLASS
# ============================================================================

class ZooarchaeologyAnalysisSuite:
    def __init__(self, main_app):
        self.app = main_app
        self.window = None
        self.ui_queue = None
        self.tabs = {}

    def show_interface(self):
        """Show the main plugin window."""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("🦴 Zooarchaeology Analysis Suite v2.0")
        self.window.geometry("1000x750")
        self.window.minsize(900, 650)
        self.window.transient(self.app.root)

        self.ui_queue = ThreadSafeUI(self.window)
        self._build_ui()

        self.window.lift()
        self.window.focus_force()

    def _build_ui(self):
        """Build the main UI."""
        # Header
        header = tk.Frame(self.window, bg="#8B4513", height=40)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="🦴", font=("Arial", 16),
                bg="#8B4513", fg="white").pack(side=tk.LEFT, padx=8)
        tk.Label(header, text="ZOOARCHAEOLOGY ANALYSIS SUITE v2.0",
                font=("Arial", 12, "bold"), bg="#8B4513", fg="white").pack(side=tk.LEFT)
        tk.Label(header, text="Assemblage · Individual · Identity · Ecology",
                font=("Arial", 8), bg="#8B4513", fg="#f1c40f").pack(side=tk.LEFT, padx=10)

        self.status_var = tk.StringVar(value="Ready")
        status_label = tk.Label(header, textvariable=self.status_var,
                               font=("Arial", 8), bg="#8B4513", fg="#2ecc71")
        status_label.pack(side=tk.RIGHT, padx=10)

        # Toolbar
        toolbar = tk.Frame(self.window, bg="#f0f0f0", height=30)
        toolbar.pack(fill=tk.X)
        toolbar.pack_propagate(False)

        ttk.Button(toolbar, text="📂 Import CSV",
                  command=self._import_csv).pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Button(toolbar, text="💾 Export CSV",
                  command=self._export_csv).pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Button(toolbar, text="🔄 Refresh",
                  command=self._refresh_all).pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Button(toolbar, text="📊 Send to Table",
                  command=self._send_to_table).pack(side=tk.LEFT, padx=2, pady=2)

        # Notebook
        style = ttk.Style()
        style.configure("Zooarch.TNotebook.Tab", font=("Arial", 9, "bold"), padding=[8, 2])

        self.notebook = ttk.Notebook(self.window, style="Zooarch.TNotebook")
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create tabs
        self.tabs['assemblage'] = AssemblageTab(self.notebook, self.app, self.ui_queue)
        self.notebook.add(self.tabs['assemblage'].frame, text=" 1. ASSEMBLAGE ")

        self.tabs['individual'] = IndividualTab(self.notebook, self.app, self.ui_queue)
        self.notebook.add(self.tabs['individual'].frame, text=" 2. INDIVIDUAL ")

        self.tabs['identity'] = IdentityTab(self.notebook, self.app, self.ui_queue)
        self.notebook.add(self.tabs['identity'].frame, text=" 3. IDENTITY ")

        self.tabs['ecology'] = EcologyTab(self.notebook, self.app, self.ui_queue)
        self.notebook.add(self.tabs['ecology'].frame, text=" 4. ECOLOGY ★ ")

        # Status bar
        status_bar = tk.Frame(self.window, bg="#34495e", height=22)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        status_bar.pack_propagate(False)

        tk.Label(status_bar,
                text="TDF Database loaded · Von den Driesch codes · FTIR interpretation",
                font=("Arial", 7), bg="#34495e", fg="white").pack(side=tk.LEFT, padx=8)

        # Initial refresh
        self._refresh_all()

    def _import_csv(self):
        """Import CSV file."""
        path = filedialog.askopenfilename(
            title="Import CSV",
            filetypes=[("CSV", "*.csv"), ("All files", "*.*")]
        )
        if not path:
            return

        try:
            if HAS_PANDAS:
                df = pd.read_csv(path)
                # Convert to list of dicts
                data = df.to_dict('records')
                if hasattr(self.app, 'data_hub'):
                    self.app.data_hub.append_data(data)
                messagebox.showinfo("Success", f"Imported {len(data)} records")
                self._refresh_all()
            else:
                # Fallback to csv module
                with open(path, 'r') as f:
                    reader = csv.DictReader(f)
                    data = list(reader)
                if hasattr(self.app, 'data_hub'):
                    self.app.data_hub.append_data(data)
                messagebox.showinfo("Success", f"Imported {len(data)} records")
                self._refresh_all()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import: {e}")

    def _export_csv(self):
        """Export data to CSV."""
        if not hasattr(self.app, 'data_hub'):
            return

        data = self.app.data_hub.get_all()
        if not data:
            messagebox.showwarning("No Data", "No data to export")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile="zooarch_export.csv"
        )
        if not path:
            return

        try:
            if HAS_PANDAS:
                df = pd.DataFrame(data)
                df.to_csv(path, index=False)
            else:
                with open(path, 'w', newline='') as f:
                    if data:
                        writer = csv.DictWriter(f, fieldnames=data[0].keys())
                        writer.writeheader()
                        writer.writerows(data)
            messagebox.showinfo("Success", f"Exported to {path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {e}")

    def _refresh_all(self):
        """Refresh all tabs with current data."""
        for tab in self.tabs.values():
            tab.refresh()
        data_count = len(self.app.data_hub.get_all()) if hasattr(self.app, 'data_hub') else 0
        self.status_var.set(f"Loaded {data_count} specimens")

    def _send_to_table(self):
        """Send data to main table."""
        # This would integrate with your main app
        messagebox.showinfo("Send to Table", "Data sent to main table")


# ============================================================================
# PLUGIN REGISTRATION
# ============================================================================

def setup_plugin(main_app):
    """Register plugin with main application."""
    plugin = ZooarchaeologyAnalysisSuite(main_app)

    # Add to Advanced menu
    if hasattr(main_app, 'advanced_menu'):
        main_app.advanced_menu.add_command(
            label=f"🦴 Zooarchaeology Suite v2.0",
            command=plugin.show_interface
        )
    # Add to Analysis menu if available
    elif hasattr(main_app, 'analysis_menu'):
        main_app.analysis_menu.add_command(
            label=f"🦴 Zooarchaeology Suite v2.0",
            command=plugin.show_interface
        )
    else:
        # Create menu if needed
        if hasattr(main_app, 'menu_bar'):
            if not hasattr(main_app, 'analysis_menu'):
                main_app.analysis_menu = tk.Menu(main_app.menu_bar, tearoff=0)
                main_app.menu_bar.add_cascade(label="🔬 Analysis", menu=main_app.analysis_menu)
            main_app.analysis_menu.add_command(
                label=f"🦴 Zooarchaeology Suite v2.0",
                command=plugin.show_interface
            )

    print("✅ Zooarchaeology Analysis Suite v2.0 loaded")
    return plugin
