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
import gzip
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
    # GENERAL / SHARED (Von den Driesch 1976)
    "GL":  "Greatest length",
    "GLI": "Greatest length lateral",
    "GLm": "Greatest length medial",
    "GLC": "Greatest length from the caput",
    "GB":  "Greatest breadth",
    "GD":  "Greatest depth",
    "GH":  "Greatest height",
    "GC":  "Greatest circumference",
    "SB":  "Smallest breadth",
    "SH":  "Smallest height of the ilium",
    "SD":  "Smallest breadth of diaphysis",
    "DD":  "Depth of diaphysis",
    # PROXIMAL / DISTAL
    "Bp":  "Breadth of the proximal end",
    "Dp":  "Depth of the proximal end",
    "BP":  "Breadth of the proximal articular surface",
    "DP":  "Depth of the proximal articular surface",
    "Bd":  "Breadth of the distal end",
    "Dd":  "Depth of the distal end",
    "BT":  "Breadth of the trochlea",
    "DT":  "Depth of the trochlea",
    "HT":  "Height of the trochlea",
    # SCAPULA
    "HS":  "Height of the scapula",
    "SLC": "Smallest length of the collum scapulae",
    "GLP": "Greatest length of the processus articularis",
    "LG":  "Length of the glenoid cavity",
    "BG":  "Breadth of the glenoid cavity",
    "AS":  "Length of the facies articularis",
    # RADIUS / LONG BONES
    "PL":  "Physiological length",
    "BFp": "Breadth of the facies articularis proximalis",
    "BFd": "Breadth of the facies articularis distalis",
    # ULNA
    "LO":  "Length of the olecranon",
    "BPC": "Breadth across the processus coronoideus",
    "SDO": "Smallest depth of the olecranon",
    "DPA": "Depth across the processus anconeus",
    # PELVIS
    "LA":  "Length of the acetabulum",
    "LS":  "Length of the symphysis",
    "LAR": "Length of the acetabular rim",
    # FEMUR
    "DC":  "Depth of the caput femoris",
    # ASTRAGALUS
    "Dl":  "Depth of the lateral side",
    "Dm":  "Depth of the medial side",
    # VERTEBRAE
    "HF":  "Height of the facies terminalis",
    "BF":  "Breadth of the facies terminalis",
    "H":   "Height of the corpus / mandible",
    "B":   "Breadth of the corpus / mandible",
    # MANDIBLE
    "LC":  "Length of the cheektooth row",
    "LM":  "Length of the molar row",
    "LP":  "Length of the premolar row",
    # TEETH
    "L":   "Length of the tooth",
    "W":   "Width of the tooth",
}

# Total count: 52 unique Von den Driesch measurement codes

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
            # Skip entries that have neither mean value (explicit None check — 0.0 is valid)
            if entry.get('Δ15N_mean') is None and entry.get('Δ13C_mean') is None:
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

                    # Handle case where sd is None (single specimen)
                    if sd is None or sd == 0:
                        # Use a default CV of 5% if no SD available
                        sd = mean * 0.05

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

    def set_status(self, message, message_type="info"):
        """Send status message to main app's status bar."""
        if hasattr(self.app, 'center') and hasattr(self.app.center, 'set_status'):
            self.app.center.set_status(message, message_type)
        else:
            print(f"[{message_type}] {message}")


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
        """Calculate MNI and MNE using element/side/portion logic with optional overlap correction."""
        if not self.samples:
            self.set_status("⚠️ No samples loaded", "warning")
            return

        # Check if any samples have portion data when overlap correction is ON
        if self.mne_overlap.get():
            has_portion = False
            indices = self.selected_indices if self.selected_indices else range(len(self.samples))
            for i in indices:
                if i >= len(self.samples):
                    continue
                sample = self.samples[i]
                portion = sample.get('portion')
                if portion and portion != 'Unknown' and portion.strip():
                    has_portion = True
                    break

            if not has_portion:
                self.set_status("⚠️ No portion data found - overlap correction will have no effect", "warning")
                # Keep correction ON but warn user via status bar

        # Group by taxon, element, side, portion
        mni_data = {}
        indices = self.selected_indices if self.selected_indices else range(len(self.samples))

        for i in indices:
            if i >= len(self.samples):
                continue
            sample = self.samples[i]
            taxon = sample.get('taxon') or sample.get('species') or 'Unknown'
            element = sample.get('element') or sample.get('bone')
            side = sample.get('side', 'Unknown')
            portion = sample.get('portion', 'Unknown')

            if not element:
                continue

            key = (taxon, element, side, portion)
            mni_data[key] = mni_data.get(key, 0) + 1

        # Organise for MNI and MNE
        mni_by_taxon = {}
        mne_counts = {}   # stores counts per (taxon, element, side, portion)

        for (taxon, element, side, portion), count in mni_data.items():
            # MNI: track sides per element (portion ignored for MNI)
            if taxon not in mni_by_taxon:
                mni_by_taxon[taxon] = {}
            if element not in mni_by_taxon[taxon]:
                mni_by_taxon[taxon][element] = {'Left': 0, 'Right': 0, 'Axial': 0, 'Unknown': 0}
            mni_by_taxon[taxon][element][side] += count

            # For MNE, store per element-side-portion
            key_mne = (taxon, element, side, portion)
            mne_counts[key_mne] = count

        # Compute MNE
        mne_final = {}
        if self.mne_overlap.get():
            # Overlap correction: for each taxon, element, side, take max across portions
            per_element_side = {}
            for (taxon, element, side, portion), count in mne_counts.items():
                key_es = (taxon, element, side)
                if key_es not in per_element_side:
                    per_element_side[key_es] = {}
                per_element_side[key_es][portion] = count

            for (taxon, element, side), portions in per_element_side.items():
                mne_val = max(portions.values())   # best estimate of minimum number of elements for that side
                if taxon not in mne_final:
                    mne_final[taxon] = 0
                mne_final[taxon] += mne_val
        else:
            # No correction: sum all specimens
            for (taxon, element, side, portion), count in mne_counts.items():
                if taxon not in mne_final:
                    mne_final[taxon] = 0
                mne_final[taxon] += count

        # Calculate MNI per taxon
        results = []
        total_mni = 0

        for taxon, elements in mni_by_taxon.items():
            taxon_mni = 0
            for element, sides in elements.items():
                if not sides:
                    continue
                left    = sides.get('Left', 0)
                right   = sides.get('Right', 0)
                axial   = sides.get('Axial', 0)
                unknown = sides.get('Unknown', 0)

                if self.mni_method.get() == "Paired elements":
                    # Conservative: treat unknowns as additional paired specimens
                    element_mni = max(left, right) + axial + unknown

                elif self.mni_method.get() == "White's method":
                    # White (1953): split unknowns conservatively between sides,
                    # then take the higher side; axial specimens are counted separately.
                    half_unknown = unknown // 2
                    element_mni = max(left + half_unknown, right + half_unknown) + axial

                else:
                    # Simple MNI = highest count of any single side category
                    element_mni = max(sides.values())
                taxon_mni = max(taxon_mni, element_mni)

            total_mni += taxon_mni
            mne_val = mne_final.get(taxon, 0)
            results.append(f"{taxon[:15]:15} MNI:{taxon_mni:2}  MNE:{mne_val:3}")

        # Display results
        self.mni_results.delete(1.0, tk.END)
        self.mni_results.insert(1.0, f"Total MNI: {total_mni}\n")
        self.mni_results.insert(tk.END, f"Method: {self.mni_method.get()}\n")
        self.mni_results.insert(tk.END, f"MNE overlap correction: {'ON' if self.mne_overlap.get() else 'OFF'}\n\n")
        for line in results[:5]:
            self.mni_results.insert(tk.END, line + "\n")

        self.set_status(f"✅ MNI: {total_mni} | Correction: {'ON' if self.mne_overlap.get() else 'OFF'}", "success")

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
        stds = []
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
            stds.append(np.std(rich_vals))

        # Plot
        self.rare_ax.clear()
        self.rare_ax.plot(subsample_sizes[:len(richness)], richness, 'b-', linewidth=2)
        self.rare_ax.fill_between(subsample_sizes[:len(richness)],
                                   [r - s for r, s in zip(richness, stds)],
                                   [r + s for r, s in zip(richness, stds)],
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
    # Grant's mandibular wear stages with absolute ages (Greenfield & Arnold 2008, Table 6)
    GRANT_MWS_AGES = {
        1:  (0, 2,   "No wear", "A"), 2:  (0, 2,   "Minimal wear", "A"),
        3:  (2, 5,   "Early wear", "B1"), 4:  (2, 5,   "Light wear", "B1"),
        5:  (2, 5,   "Light-moderate wear", "B1"), 6:  (2, 5,   "Moderate wear", "B1"),
        7:  (2, 5,   "Moderate wear", "B1"), 8:  (2, 5,   "Moderate wear", "B1"),
        9:  (5, 6,   "Moderate wear", "B2"), 10: (5, 6,   "Moderate wear", "B2"),
        11: (5, 6,   "Moderate-heavy wear", "B2"), 12: (5, 6,   "Heavy wear", "B2"),
        13: (6, 12,  "Heavy wear", "C"), 14: (6, 12,  "Heavy wear", "C"),
        15: (6, 12,  "Heavy wear", "C"), 16: (6, 12,  "Heavy wear", "C"),
        17: (6, 12,  "Heavy wear", "C"), 18: (6, 12,  "Heavy wear", "C"),
        19: (12, 15, "Very heavy wear", "D1"), 20: (12, 15, "Very heavy wear", "D1"),
        21: (16, 22, "Extreme wear", "D2"), 22: (16, 22, "Extreme wear", "D2"),
        23: (16, 22, "Extreme wear", "D2"), 24: (16, 22, "Extreme wear", "D2"),
        25: (16, 22, "Extreme wear", "D2"), 26: (16, 22, "Extreme wear", "D2"),
        27: (22, 24, "Severe wear", "D3"), 28: (22, 24, "Severe wear", "D3"),
        29: (24, 36, "Severe wear", "E"), 30: (24, 36, "Severe wear", "E"),
        31: (24, 36, "Severe wear", "E"), 32: (24, 36, "Severe wear", "E"),
        33: (24, 36, "Severe wear", "E"), 34: (36, 48, "Severe wear", "F"),
        35: (36, 48, "Severe wear", "F"), 36: (36, 48, "Severe wear", "F"),
        37: (36, 48, "Severe wear", "F"), 38: (48, 72, "Severe wear", "G"),
        39: (48, 72, "Severe wear", "G"), 40: (48, 72, "Severe wear", "G"),
        41: (48, 72, "Severe wear", "G"), 42: (72, 96, "Severe wear", "H"),
        43: (72, 96, "Severe wear", "H"), 44: (72, 96, "Severe wear", "H"),
        45: (96, 120, "Severe wear", "I"),
    }

    # Payne stages for reference/conversion (Greenfield & Arnold 2008, Table 1)
    PAYNE_STAGES = {
        'A': (0, 2, "Infant - Neonate"), 'B': (2, 6, "Infant - Old"),
        'C': (6, 12, "Juvenile"), 'D': (12, 24, "Subadult - Young"),
        'E': (24, 36, "Subadult - Old"), 'F': (36, 48, "Adult - Young"),
        'G': (48, 72, "Adult - Young"), 'H': (72, 96, "Adult - Middle"),
        'I': (96, 120, "Adult - Old/Senile"),
    }

    # Epiphyseal fusion ages (months) by taxon (Silver 1969) - fallback if JSON missing
    FUSION_AGES = {
        'Cattle': {'humerus_distal': 15, 'radius_proximal': 15, 'scapula_distal': 8,
                   'phalanges': 18, 'tibia_distal': 24, 'metacarpal_distal': 30,
                   'metatarsal_distal': 30, 'femur_proximal': 42, 'femur_distal': 48,
                   'humerus_proximal': 48, 'radius_distal': 48, 'tibia_proximal': 48},
        'Sheep': {'scapula_distal': 6, 'humerus_distal': 10, 'radius_proximal': 10,
                  'phalanges': 13, 'tibia_distal': 18, 'metacarpal_distal': 20,
                  'metatarsal_distal': 20, 'femur_proximal': 30, 'femur_distal': 36,
                  'humerus_proximal': 36, 'radius_distal': 36, 'tibia_proximal': 36},
        'Goat': {'scapula_distal': 6, 'humerus_distal': 10, 'radius_proximal': 10,
                 'phalanges': 13, 'tibia_distal': 18, 'metacarpal_distal': 20,
                 'metatarsal_distal': 20, 'femur_proximal': 30, 'femur_distal': 36,
                 'humerus_proximal': 36, 'radius_distal': 36, 'tibia_proximal': 36},
        'Pig': {'scapula_distal': 12, 'humerus_distal': 12, 'radius_proximal': 12,
                'phalanges': 24, 'tibia_distal': 24, 'metacarpal_distal': 24,
                'calcaneus': 36, 'femur_proximal': 36, 'femur_distal': 42,
                'humerus_proximal': 42, 'radius_distal': 42},
        'Horse': {'scapula_distal': 12, 'humerus_distal': 15, 'radius_proximal': 15,
                  'phalanges': 18, 'tibia_distal': 24, 'metacarpal_distal': 18,
                  'femur_proximal': 36, 'femur_distal': 42, 'humerus_proximal': 36}
    }

    # ── Grant MWS helpers ──────────────────────────────────────────────────
    _GRANT_NUM = {c: i + 1 for i, c in enumerate('abcdefghijklmnop')}
    _GRANT_TEETH = {
        'dP4': ['—'] + list('abcdefghi'),
        'P4':  ['—'] + list('abcdefgh'),
        'M1':  ['—'] + list('abcdefghijklmnop'),
        'M2':  ['—'] + list('abcdefghijklmnop'),
        'M3':  ['—'] + list('abcdefghijklmnop'),
    }
    _MWS_PAYNE = [
        (1,   2,  'A',   0,   2),
        (3,  12,  'B',   2,   6),
        (13,  18,  'C',   6,  12),
        (19,  28,  'D',  12,  24),
        (29,  33,  'E',  24,  36),
        (34,  37,  'F',  36,  48),
        (38,  41,  'G',  48,  72),
        (42,  44,  'H',  72,  96),
        (45, 999,  'I',  96, 144),
    ]

    # ── New Age Tab constants ──────────────────────────────────────────────
    _TAXON_GROUPS = {
        'Cattle': 'artiodactyl', 'Sheep': 'artiodactyl', 'Goat': 'artiodactyl',
        'Pig': 'artiodactyl', 'Red Deer': 'artiodactyl', 'Fallow Deer': 'artiodactyl',
        'Horse': 'perissodactyl', 'Donkey': 'perissodactyl',
        'Dog': 'carnivore', 'Cat': 'carnivore',
        'Chicken': 'bird', 'Goose': 'bird', 'Duck': 'bird', 'Other Bird': 'bird',
        'Fish': 'fish', 'Other': 'unknown',
    }

    _ERUPTION_DATA = {
        'Cattle': {
            'dI1/I1': {'dec_erupting':(0,1),   'dec_present':(0,18),  'perm_erupting':(18,24), 'perm_present':(24,144)},
            'dI2/I2': {'dec_erupting':(0,2),   'dec_present':(0,24),  'perm_erupting':(24,30), 'perm_present':(30,144)},
            'dI3/I3': {'dec_erupting':(0,3),   'dec_present':(0,36),  'perm_erupting':(30,42), 'perm_present':(36,144)},
            'dP4/P4': {'dec_erupting':(0,1),   'dec_present':(0,24),  'perm_erupting':(24,30), 'perm_present':(30,144)},
            'M1':     {'perm_erupting':(5,6),   'perm_present':(6,144)},
            'M2':     {'perm_erupting':(15,18), 'perm_present':(18,144)},
            'M3':     {'perm_erupting':(24,28), 'perm_present':(28,144)},
        },
        'Sheep': {
            'dI1/I1': {'dec_erupting':(0,1),   'dec_present':(0,12),  'perm_erupting':(12,18), 'perm_present':(18,144)},
            'dI2/I2': {'dec_erupting':(0,2),   'dec_present':(0,21),  'perm_erupting':(21,24), 'perm_present':(24,144)},
            'dI3/I3': {'dec_erupting':(1,2),   'dec_present':(1,30),  'perm_erupting':(30,36), 'perm_present':(36,144)},
            'dP4/P4': {'dec_erupting':(0,1),   'dec_present':(0,21),  'perm_erupting':(21,24), 'perm_present':(24,144)},
            'M1':     {'perm_erupting':(3,4),   'perm_present':(4,144)},
            'M2':     {'perm_erupting':(9,12),  'perm_present':(12,144)},
            'M3':     {'perm_erupting':(18,24), 'perm_present':(24,144)},
        },
        'Pig': {
            'dI1/I1': {'dec_erupting':(0,1),   'dec_present':(0,12),  'perm_erupting':(12,14), 'perm_present':(14,144)},
            'dI3/I3': {'dec_erupting':(1,2),   'dec_present':(1,8),   'perm_erupting':(8,10),  'perm_present':(10,144)},
            'dC/C':   {'dec_erupting':(1,2),   'dec_present':(1,8),   'perm_erupting':(8,10),  'perm_present':(10,144)},
            'dP4/P4': {'dec_erupting':(0,1),   'dec_present':(0,12),  'perm_erupting':(12,16), 'perm_present':(16,144)},
            'M1':     {'perm_erupting':(4,6),   'perm_present':(6,144)},
            'M2':     {'perm_erupting':(12,16), 'perm_present':(16,144)},
            'M3':     {'perm_erupting':(17,22), 'perm_present':(22,144)},
        },
        'Horse': {
            'dI1/I1': {'dec_erupting':(0,1),   'dec_present':(0,30),  'perm_erupting':(30,36), 'perm_present':(36,240)},
            'dI2/I2': {'dec_erupting':(1,2),   'dec_present':(1,42),  'perm_erupting':(42,48), 'perm_present':(48,240)},
            'dI3/I3': {'dec_erupting':(6,9),   'dec_present':(6,54),  'perm_erupting':(54,60), 'perm_present':(60,240)},
            'dP2/P2': {'dec_erupting':(0,1),   'dec_present':(0,30),  'perm_erupting':(30,36), 'perm_present':(36,240)},
            'dP3/P3': {'dec_erupting':(0,1),   'dec_present':(0,36),  'perm_erupting':(36,42), 'perm_present':(42,240)},
            'dP4/P4': {'dec_erupting':(0,1),   'dec_present':(0,48),  'perm_erupting':(48,54), 'perm_present':(54,240)},
            'M1':     {'perm_erupting':(9,12),  'perm_present':(12,240)},
            'M2':     {'perm_erupting':(24,30), 'perm_present':(30,240)},
            'M3':     {'perm_erupting':(36,48), 'perm_present':(48,240)},
        },
        'Red Deer': {
            'dI1/I1': {'dec_erupting':(0,1),   'dec_present':(0,14),  'perm_erupting':(14,16), 'perm_present':(16,240)},
            'dI2/I2': {'dec_erupting':(0,2),   'dec_present':(0,26),  'perm_erupting':(26,28), 'perm_present':(28,240)},
            'dI3/I3': {'dec_erupting':(0,3),   'dec_present':(0,38),  'perm_erupting':(38,40), 'perm_present':(40,240)},
            'dP4/P4': {'dec_erupting':(0,2),   'dec_present':(0,26),  'perm_erupting':(26,30), 'perm_present':(30,240)},
            'M1':     {'perm_erupting':(4,5),   'perm_present':(5,240)},
            'M2':     {'perm_erupting':(13,14), 'perm_present':(14,240)},
            'M3':     {'perm_erupting':(24,28), 'perm_present':(28,240)},
        },
        'Dog': {
            'dI/I':   {'dec_erupting':(1,2),   'dec_present':(1,14),  'perm_erupting':(12,14), 'perm_present':(14,180)},
            'dC/C':   {'dec_erupting':(1,2),   'dec_present':(1,20),  'perm_erupting':(18,20), 'perm_present':(20,180)},
            'dP/P':   {'dec_erupting':(2,4),   'dec_present':(2,16),  'perm_erupting':(14,18), 'perm_present':(18,180)},
            'M1':     {'perm_erupting':(14,16), 'perm_present':(16,180)},
            'M2':     {'perm_erupting':(16,20), 'perm_present':(20,180)},
            'M3':     {'perm_erupting':(18,22), 'perm_present':(22,180)},
        },
    }
    _ERUPTION_DATA['Goat']        = _ERUPTION_DATA['Sheep']
    _ERUPTION_DATA['Fallow Deer'] = _ERUPTION_DATA['Red Deer']
    _ERUPTION_DATA['Cat']         = _ERUPTION_DATA['Dog']

    _ERUPT_STATES_WITH_DEC = [
        '— not observed', 'Absent (not yet erupted)',
        'Deciduous erupting', 'Deciduous present',
        'Permanent erupting', 'Permanent present', 'Shed / not present',
    ]
    _ERUPT_STATES_PERM_ONLY = [
        '— not observed', 'Absent (not yet erupted)',
        'Permanent erupting', 'Permanent present', 'Shed / not present',
    ]
    _ERUPT_STATE_KEY = {
        'Deciduous erupting': 'dec_erupting',
        'Deciduous present':  'dec_present',
        'Permanent erupting': 'perm_erupting',
        'Permanent present':  'perm_present',
    }
    _TEETH_WITH_DEC = {'dI1/I1','dI2/I2','dI3/I3','dC/C','dP2/P2','dP3/P3','dP4/P4','dI/I','dP/P'}

    _PIG_WEAR = {
        'A': (0,   6,   'No wear — dP4 unworn, M1 not erupted',    '#2e7d32'),
        'B': (6,   12,  'Light wear on dP4, M1 erupting',          '#558b2f'),
        'C': (12,  18,  'M1 in wear; dP4 heavily worn',            '#f9a825'),
        'D': (18,  24,  'M2 erupting; perm premolars erupting',    '#e65100'),
        'E': (24,  36,  'M2 in wear; perm premolars present',      '#bf360c'),
        'F': (36,  48,  'M3 erupting or in early wear',            '#b71c1c'),
        'G': (48,  72,  'M3 in full wear; heavy attrition',        '#880e4f'),
        'H': (72,  120, 'Severe wear throughout; senile changes',  '#4a148c'),
    }

    _GROSS_MORPH = {
        '':         (None, None),
        'foetal':   (0,    0),
        'neonate':  (0,    1),
        'juvenile': (1,    24),
        'subadult': (12,   36),
        'adult':    (24,   999),
        'mature':   (36,   999),
        'old':      (72,   999),
    }
    _GROSS_MORPH_LABELS = {
        '':         '— not assessed',
        'foetal':   'Foetal  (prenatal)',
        'neonate':  'Neonate  (0–1 mo)',
        'juvenile': 'Juvenile  (~1–24 mo)',
        'subadult': 'Subadult  (not fully mature)',
        'adult':    'Adult  (fully mature)',
        'mature':   'Mature adult  (prime)',
        'old':      'Old adult  (senile changes)',
    }
    _BONE_TEXTURE_OPTS = [
        ('',          '— not assessed'),
        ('porous',    'Porous / immature cortex'),
        ('normal',    'Normal cortical density'),
        ('compact',   'Dense / compact'),
        ('osteoporo', 'Osteoporotic / thinning'),
    ]

    # ── Taphonomy constants ────────────────────────────────────────────────
    _BEHRENSMEYER = {
        0: ("Stage 0", "No cracking or flaking. Bone grease still present. Fresh surface.", "#2e7d32"),
        1: ("Stage 1", "Longitudinal cracking, no flaking. Surface may be greasy or slightly bleached.", "#558b2f"),
        2: ("Stage 2", "Mosaic cracking, flaking parallel to fibrous structure begins.", "#f9a825"),
        3: ("Stage 3", "Rough, homogeneous texture. Fibrous structure visible. Large cracks present.", "#e65100"),
        4: ("Stage 4", "Coarsely splintered. Bone falling apart. Only dense portions remain.", "#b71c1c"),
        5: ("Stage 5", "Bone structurally fragile. May crumble when touched. Extreme weathering.", "#7b1fa2"),
    }
    _BURNING = {
        'none':       ("None",       "No evidence of burning",                              "#9e9e9e"),
        'scorched':   ("Scorched",   "Brown/black discolouration, partial charring, <300°C","#795548"),
        'carbonised': ("Carbonised", "Black throughout, fully charred, 300–600°C",          "#212121"),
        'calcined':   ("Calcined",   "White/grey/blue, fully oxidised, >600°C",             "#90caf9"),
    }
    _SURF_QUAL = {
        1: ("1 — Poor",      "Heavy erosion, surface largely destroyed, no fine detail",  "#b71c1c"),
        2: ("2 — Fair",      "Moderate erosion, some detail lost",                        "#e65100"),
        3: ("3 — Moderate",  "Slight erosion, most surface detail intact",                "#f9a825"),
        4: ("4 — Good",      "Minor abrasion only, fine detail present",                  "#2e7d32"),
        5: ("5 — Excellent", "Fresh/pristine surface, all morphological detail preserved", "#1565c0"),
    }

    def __init__(self, parent, app, ui_queue):
        super().__init__(parent, app, ui_queue)
        self.current_specimen_idx = None
        self.measurement_codes = list(MEASUREMENT_CODES.keys())
        self.grant_vars = {}
        self.morph_keys = {}

        self._horse_vars = {}
        self._dog_wear_var = None
        self.debug_taph = False

        # New age tab vars
        self._eruption_vars    = {}
        self._erupt_interp     = {}
        self._pig_wear_var     = None
        self._cement_rings_var = tk.StringVar()
        self._cement_season_var = tk.StringVar(value='')
        self._histo_method_var = tk.StringVar(value='')
        self._histo_age_var    = tk.StringVar()
        self._histo_ref_var    = tk.StringVar()
        self._gross_morph_var  = tk.StringVar(value='')
        self._bone_texture_var = tk.StringVar(value='')
        self._gross_notes_var  = tk.StringVar()

        # === UNIFIED DATABASE CONTAINERS ===
        self.full_db = None
        self.references = {}
        self.taxon_references = {}
        self.reference_standards = {}
        self.taxonomy = {}
        self.taxon_thesaurus = {}
        self.element_thesaurus = {}
        self.measure_thesaurus = {}
        self.reference_sets = {}
        self.example_specimens = []

        self._last_lsi_results = {}
        self._last_lsi_condensed = {}
        self._batch_lsi_results = []

        self._AXIS_PRIORITY = {
            'Length': ['GL', 'GLl', 'GLI', 'GLm', 'GLC', 'GLpe', 'HTC'],
            'Width':  ['BT', 'Bd', 'Bp', 'SD', 'BFd', 'BFp', 'GLP', 'LG', 'SLC', 'GB'],
            'Depth':  ['Dd', 'DD', 'BG', 'Dp', 'DPA', 'DC'],
        }

        self._build_ui()
        self._load_unified_database()
        self.frame.after(100, self._populate_lsi_tab)
        self.frame.after(200, self._load_morph_keys)

    def _build_ui(self):
        main = ttk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        main.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        left = ttk.Frame(main, width=350)
        main.add(left, weight=0)

        self.right_notebook = ttk.Notebook(main)
        main.add(self.right_notebook, weight=1)

        # === LEFT PANEL ===
        list_frame = ttk.LabelFrame(left, text="Select Specimen", padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=2)

        self.specimen_list = tk.Listbox(list_frame, height=15, font=("Courier", 8), width=30)
        self.specimen_list.pack(side=tk.LEFT, fill=tk.Y)
        self.specimen_list.bind('<<ListboxSelect>>', self._on_specimen_selected)

        list_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.specimen_list.yview)
        self.specimen_list.configure(yscrollcommand=list_scrollbar.set)
        list_scrollbar.pack(side=tk.LEFT, fill=tk.Y)

        nav_frame = ttk.Frame(left)
        nav_frame.pack(fill=tk.X, pady=2)
        ttk.Button(nav_frame, text="◀ Prev", command=self._prev_specimen).pack(side=tk.LEFT, padx=2)
        ttk.Button(nav_frame, text="Next ▶", command=self._next_specimen).pack(side=tk.LEFT, padx=2)
        ttk.Button(nav_frame, text="📚 Example", command=self._load_example_specimen).pack(side=tk.LEFT, padx=2)

        self.specimen_summary = tk.Text(left, height=3, font=("Arial", 7), width=30)
        self.specimen_summary.pack(fill=tk.X, pady=2)

        # === AGE TAB ===
        self.age_frame = ttk.Frame(self.right_notebook)
        self.right_notebook.add(self.age_frame, text="Age")
        self._build_age_tab_ui()

        # === TAPHONOMY TAB (Enhanced) ===
        self.taph_frame = ttk.Frame(self.right_notebook)
        self.right_notebook.add(self.taph_frame, text="Taphonomy")

        taph_canvas = tk.Canvas(self.taph_frame, highlightthickness=0)
        taph_vsb = ttk.Scrollbar(self.taph_frame, orient="vertical", command=taph_canvas.yview)
        taph_canvas.configure(yscrollcommand=taph_vsb.set)
        taph_vsb.pack(side=tk.RIGHT, fill=tk.Y)
        taph_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        taph_inner = ttk.Frame(taph_canvas)
        taph_canvas_window = taph_canvas.create_window((0, 0), window=taph_inner, anchor="nw")
        taph_inner.bind("<Configure>", lambda e: taph_canvas.configure(
            scrollregion=taph_canvas.bbox("all")))
        taph_canvas.bind("<Configure>", lambda e: taph_canvas.itemconfig(
            taph_canvas_window, width=e.width))

        taph_main = ttk.Frame(taph_inner)
        taph_main.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        taph_body = ttk.Frame(taph_main)
        taph_body.pack(fill=tk.BOTH, expand=True)
        taph_body.columnconfigure(0, weight=1)
        taph_body.columnconfigure(1, weight=1)

        left_col = ttk.Frame(taph_body)
        left_col.grid(row=0, column=0, sticky='nsew', padx=(0, 4))

        weather_lf = ttk.LabelFrame(left_col, text="Weathering Stage  (Behrensmeyer 1978)", padding=6)
        weather_lf.pack(fill=tk.X, pady=(0, 6))

        self.weather_var = tk.IntVar(value=-1)
        for stage, (label, desc, color) in self._BEHRENSMEYER.items():
            row_f = ttk.Frame(weather_lf)
            row_f.pack(fill=tk.X, pady=1)
            rb = tk.Radiobutton(row_f, text=f"  {label}", variable=self.weather_var,
                                value=stage, command=self._update_taph_summary,
                                font=("Arial", 8, "bold"), fg=color,
                                activeforeground=color, selectcolor="#f0f0f0",
                                anchor='w', width=9)
            rb.pack(side=tk.LEFT)
            tk.Label(row_f, text=desc, font=("Arial", 7), foreground="#555",
                     wraplength=220, justify=tk.LEFT, anchor='w').pack(side=tk.LEFT, fill=tk.X)

        nr_row = ttk.Frame(weather_lf)
        nr_row.pack(fill=tk.X, pady=(4, 0))
        tk.Radiobutton(nr_row, text="  Not recorded", variable=self.weather_var,
                       value=-1, command=self._update_taph_summary,
                       font=("Arial", 8), foreground="gray").pack(side=tk.LEFT)

        burn_lf = ttk.LabelFrame(left_col, text="Burning Stage", padding=6)
        burn_lf.pack(fill=tk.X, pady=(0, 6))

        self.burning_var = tk.StringVar(value="none")
        for key, (label, desc, color) in self._BURNING.items():
            row_f = ttk.Frame(burn_lf)
            row_f.pack(fill=tk.X, pady=1)
            rb = tk.Radiobutton(row_f, text=f"  {label}", variable=self.burning_var,
                                value=key, command=self._update_taph_summary,
                                font=("Arial", 8, "bold"), fg=color,
                                activeforeground=color, selectcolor="#f0f0f0",
                                anchor='w', width=12)
            rb.pack(side=tk.LEFT)
            tk.Label(row_f, text=desc, font=("Arial", 7), foreground="#555",
                     wraplength=200, justify=tk.LEFT, anchor='w').pack(side=tk.LEFT, fill=tk.X)

        surf_lf = ttk.LabelFrame(left_col, text="Surface Preservation Quality", padding=6)
        surf_lf.pack(fill=tk.X, pady=(0, 6))

        self.surf_qual_var = tk.IntVar(value=0)
        for score, (label, desc, color) in self._SURF_QUAL.items():
            row_f = ttk.Frame(surf_lf)
            row_f.pack(fill=tk.X, pady=1)
            rb = tk.Radiobutton(row_f, text=f"  {label}", variable=self.surf_qual_var,
                                value=score, command=self._update_taph_summary,
                                font=("Arial", 8, "bold"), fg=color,
                                activeforeground=color, selectcolor="#f0f0f0",
                                anchor='w', width=14)
            rb.pack(side=tk.LEFT)
            tk.Label(row_f, text=desc, font=("Arial", 7), foreground="#555",
                     wraplength=195, justify=tk.LEFT, anchor='w').pack(side=tk.LEFT, fill=tk.X)

        nr2_row = ttk.Frame(surf_lf)
        nr2_row.pack(fill=tk.X, pady=(4, 0))
        tk.Radiobutton(nr2_row, text="  Not recorded", variable=self.surf_qual_var,
                       value=0, command=self._update_taph_summary,
                       font=("Arial", 8), foreground="gray").pack(side=tk.LEFT)

        right_col = ttk.Frame(taph_body)
        right_col.grid(row=0, column=1, sticky='nsew', padx=(4, 0))

        butch_lf = ttk.LabelFrame(right_col, text="Butchery Marks", padding=6)
        butch_lf.pack(fill=tk.X, pady=(0, 6))

        butch_types = [
            ('cut_marks',        'Cut marks',
             'Fine parallel incisions from stone/metal blade — skinning, filleting, disarticulation'),
            ('chop_marks',       'Chop marks',
             'Deep V-shaped notches from axe or cleaver — disarticulation, portioning'),
            ('percussion_marks', 'Percussion marks',
             'Circular/oval pits or internal cone fractures — marrow extraction'),
            ('scraping_marks',   'Scraping marks',
             'Broad striations covering large areas — periosteum removal, pot-polishing'),
        ]
        self.butchery_vars = {}
        for key, label, desc in butch_types:
            row_f = ttk.Frame(butch_lf)
            row_f.pack(fill=tk.X, pady=2)
            var = tk.BooleanVar()
            self.butchery_vars[key] = var
            tk.Checkbutton(row_f, text=f"  {label}", variable=var,
                           command=self._update_taph_summary,
                           font=("Arial", 8, "bold"), anchor='w').pack(side=tk.LEFT, anchor='n')
            tk.Label(row_f, text=desc, font=("Arial", 7), foreground="#555",
                     wraplength=230, justify=tk.LEFT).pack(side=tk.LEFT, padx=(4, 0))

        bn_row = ttk.Frame(butch_lf)
        bn_row.pack(fill=tk.X, pady=(4, 0))
        ttk.Label(bn_row, text="Location/notes:", font=("Arial", 7)).pack(side=tk.LEFT)
        self.butchery_notes_var = tk.StringVar()
        ttk.Entry(bn_row, textvariable=self.butchery_notes_var, width=28
                  ).pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)

        gnaw_lf = ttk.LabelFrame(right_col, text="Gnawing", padding=6)
        gnaw_lf.pack(fill=tk.X, pady=(0, 6))

        gnaw_types = [
            ('none',      'None',              "No gnawing present",                         "#9e9e9e"),
            ('carnivore', 'Carnivore gnawing',
             'Pits, scores, crenulated edges, furrows — dog/wolf/hyaena',                     "#c62828"),
            ('rodent',    'Rodent gnawing',
             'Paired parallel grooves with flat bases — mouse, rat, rabbit',                  "#6a1fa2"),
            ('both',      'Both present',
             'Carnivore and rodent gnawing recorded on same element',                         "#1565c0"),
        ]
        self.gnawing_var = tk.StringVar(value='none')
        for key, label, desc, color in gnaw_types:
            row_f = ttk.Frame(gnaw_lf)
            row_f.pack(fill=tk.X, pady=1)
            rb = tk.Radiobutton(row_f, text=f"  {label}", variable=self.gnawing_var,
                                value=key, command=self._update_taph_summary,
                                font=("Arial", 8, "bold"), fg=color,
                                activeforeground=color, selectcolor="#f0f0f0",
                                anchor='w', width=18)
            rb.pack(side=tk.LEFT)
            tk.Label(row_f, text=desc, font=("Arial", 7), foreground="#555",
                     wraplength=175, justify=tk.LEFT).pack(side=tk.LEFT)

        tp_row = ttk.Frame(gnaw_lf)
        tp_row.pack(fill=tk.X, pady=(4, 0))
        self.tooth_pits_var = tk.BooleanVar()
        tk.Checkbutton(tp_row, text="  Tooth pits present",
                       variable=self.tooth_pits_var,
                       command=self._update_taph_summary,
                       font=("Arial", 8)).pack(side=tk.LEFT)

        surf_mod_lf = ttk.LabelFrame(right_col, text="Surface Modifications", padding=6)
        surf_mod_lf.pack(fill=tk.X, pady=(0, 6))

        surf_mods = [
            ('root_etching',       'Root etching',
             'Dendritic branching marks from plant roots / fungi'),
            ('abrasion',           'Abrasion',
             'Surface smoothed/rounded by sediment particle contact'),
            ('rounding',           'Rounding',
             'Edge rounding suggesting water transport or trampling'),
            ('bleaching',          'Bleaching',
             'White/chalky surface from UV exposure or prolonged subaerial weathering'),
            ('manganese_staining', 'Manganese staining',
             'Black dendritic staining from soil Mn-oxides (waterlogged/anoxic contexts)'),
            ('iron_staining',      'Iron/ochre staining',
             'Red-brown surface discolouration from Fe-oxides or ochre use'),
            ('trampling',          'Trampling damage',
             'Subparallel striae on shaft surfaces, random orientation'),
        ]
        self.surf_mod_vars = {}
        for key, label, desc in surf_mods:
            row_f = ttk.Frame(surf_mod_lf)
            row_f.pack(fill=tk.X, pady=1)
            var = tk.BooleanVar()
            self.surf_mod_vars[key] = var
            tk.Checkbutton(row_f, text=f"  {label}", variable=var,
                           command=self._update_taph_summary,
                           font=("Arial", 8, "bold"), anchor='w').pack(side=tk.LEFT, anchor='n')
            tk.Label(row_f, text=desc, font=("Arial", 7), foreground="#555",
                     wraplength=220, justify=tk.LEFT).pack(side=tk.LEFT, padx=(4, 0))

        bot_frame = ttk.Frame(taph_main)
        bot_frame.pack(fill=tk.X, pady=(6, 0))
        bot_frame.columnconfigure(0, weight=1)
        bot_frame.columnconfigure(1, weight=2)

        frag_lf = ttk.LabelFrame(bot_frame, text="Fragmentation / Completeness", padding=6)
        frag_lf.grid(row=0, column=0, sticky='nsew', padx=(0, 4))

        fc_row = ttk.Frame(frag_lf)
        fc_row.pack(fill=tk.X, pady=2)
        ttk.Label(fc_row, text="Portion:", width=10).pack(side=tk.LEFT)
        self.fragmentation_var = tk.StringVar(value="")
        frag_opts = [
            "", "Complete", "Nearly complete (>75%)",
            "Proximal half", "Distal half", "Proximal epiphysis",
            "Distal epiphysis", "Shaft fragment", "Proximal + shaft",
            "Distal + shaft", "Epiphysis only", "Fragment (<25%)", "Other",
        ]
        ttk.Combobox(fc_row, textvariable=self.fragmentation_var,
                     values=frag_opts, width=22, state="readonly"
                     ).pack(side=tk.LEFT, padx=2)

        comp_row = ttk.Frame(frag_lf)
        comp_row.pack(fill=tk.X, pady=2)
        ttk.Label(comp_row, text="Completeness:", width=10).pack(side=tk.LEFT)
        self.completeness_var = tk.StringVar(value="")
        ttk.Entry(comp_row, textvariable=self.completeness_var, width=6).pack(side=tk.LEFT, padx=2)
        ttk.Label(comp_row, text="%  (0–100)", font=("Arial", 7),
                  foreground="gray").pack(side=tk.LEFT)

        summ_lf = ttk.LabelFrame(bot_frame, text="Taphonomic Summary", padding=6)
        summ_lf.grid(row=0, column=1, sticky='nsew', padx=(4, 0))

        self.taph_summary_text = tk.Text(
            summ_lf, height=5, font=("Arial", 8),
            wrap=tk.WORD, state=tk.DISABLED,
            bg="#fafafa", relief=tk.FLAT, borderwidth=1)
        self.taph_summary_text.pack(fill=tk.BOTH, expand=True)

        self.taph_summary_text.tag_configure("header",  font=("Arial", 8, "bold"))
        self.taph_summary_text.tag_configure("good",    foreground="#2e7d32")
        self.taph_summary_text.tag_configure("warn",    foreground="#e65100")
        self.taph_summary_text.tag_configure("bad",     foreground="#b71c1c")
        self.taph_summary_text.tag_configure("neutral", foreground="#555")

        notes_lf = ttk.LabelFrame(taph_main, text="Taphonomic Notes (free text)", padding=4)
        notes_lf.pack(fill=tk.X, pady=(6, 0))
        self.taph_notes_var = tk.StringVar()
        ttk.Entry(notes_lf, textvariable=self.taph_notes_var, font=("Arial", 8)
                  ).pack(fill=tk.X)

        # Backward-compat dummy vars for taphonomy
        self.burn_var     = tk.BooleanVar()
        self.butchery_var = tk.BooleanVar()
        self.gnaw_var     = tk.BooleanVar()
        self.root_var     = tk.BooleanVar()

        # === BIOMETRICS TAB ===
        self.bio_frame = ttk.Frame(self.right_notebook)
        self.right_notebook.add(self.bio_frame, text="Biometrics")

        bio_main_container = ttk.Frame(self.bio_frame)
        bio_main_container.pack(fill=tk.BOTH, expand=True)

        bio_canvas = tk.Canvas(bio_main_container, highlightthickness=0, height=400)
        bio_scrollbar = ttk.Scrollbar(bio_main_container, orient="vertical", command=bio_canvas.yview)
        bio_scrollable = ttk.Frame(bio_canvas)

        bio_scrollable.bind("<Configure>", lambda e: bio_canvas.configure(
            scrollregion=bio_canvas.bbox("all")))
        bio_canvas.create_window((0, 0), window=bio_scrollable, anchor="nw")
        bio_canvas.configure(yscrollcommand=bio_scrollbar.set)
        bio_canvas.pack(side="left", fill="both", expand=True)
        bio_scrollbar.pack(side="right", fill="y")

        self.measurement_vars = {}
        codes = self.measurement_codes
        total_rows = (len(codes) + 2) // 3

        header_frame = ttk.Frame(bio_scrollable)
        header_frame.pack(fill=tk.X, pady=5)
        for col in range(3):
            ttk.Label(header_frame, text="Code", font=("Arial", 8, "bold"),
                    anchor='w').grid(row=0, column=col*3, padx=2, pady=1, sticky='ew')
            ttk.Label(header_frame, text="Description", font=("Arial", 8, "bold"),
                    anchor='w').grid(row=0, column=col*3+1, padx=2, pady=1, sticky='ew')
            ttk.Label(header_frame, text="mm", font=("Arial", 8, "bold"),
                    anchor='w').grid(row=0, column=col*3+2, padx=2, pady=1, sticky='ew')

        ttk.Separator(bio_scrollable, orient='horizontal').pack(fill=tk.X, pady=2)

        rows_container = ttk.Frame(bio_scrollable)
        rows_container.pack(fill=tk.BOTH, expand=True)

        for i in range(9):
            if i % 3 == 0:
                rows_container.columnconfigure(i, weight=1, minsize=50)
            elif i % 3 == 1:
                rows_container.columnconfigure(i, weight=3, minsize=120)
            else:
                rows_container.columnconfigure(i, weight=1, minsize=50)

        for row in range(total_rows):
            for col in range(3):
                idx = row * 3 + col
                if idx >= len(codes):
                    continue
                code = codes[idx]
                desc = MEASUREMENT_CODES[code]
                if len(desc) > 25:
                    desc = desc[:23] + ".."
                ttk.Label(rows_container, text=code, font=("Arial", 8, "bold"),
                        anchor='w').grid(row=row, column=col*3, padx=2, pady=1, sticky='w')
                ttk.Label(rows_container, text=desc, font=("Arial", 7),
                        anchor='w').grid(row=row, column=col*3+1, padx=2, pady=1, sticky='w')
                var = tk.StringVar()
                entry = ttk.Entry(rows_container, textvariable=var, width=6)
                entry.grid(row=row, column=col*3+2, padx=2, pady=1, sticky='ew')
                self.measurement_vars[code] = var

        # === LSI TAB ===
        self.lsi_frame = ttk.Frame(self.right_notebook)
        self.right_notebook.add(self.lsi_frame, text="LSI Calculator")
        self._build_lsi_skeleton()

        # === BOTTOM BAR ===
        self.bottom_bar = ttk.Frame(self.frame)
        self.bottom_bar.pack(fill=tk.X, pady=2, side=tk.BOTTOM)

        button_frame = ttk.Frame(self.bottom_bar)
        button_frame.pack(side=tk.LEFT)
        ttk.Button(button_frame, text="💾 Save", width=8,
                   command=self._save_to_specimen).pack(side=tk.LEFT, padx=1)
        ttk.Button(button_frame, text="🧹 Clear", width=8,
                   command=self._clear_measurements).pack(side=tk.LEFT, padx=1)

        self.measurement_status = ttk.Label(self.bottom_bar, text="", font=("Arial", 7))
        self.measurement_status.pack(side=tk.LEFT, padx=10)

        self.lsi_indicator = tk.Label(self.bottom_bar, text="", font=("Arial", 7, "bold"),
                                fg="#2c3e50", bg="#ecf0f1", relief=tk.SUNKEN, padx=5)
        self.lsi_indicator.pack(side=tk.RIGHT, padx=5)

    # ============================================================================
    # AGE TAB — UI BUILDER
    # ============================================================================

    def _build_age_tab_ui(self):
        """Build the complete Age tab — all 6 methods, scrollable, species-isolated."""
        age_canvas = tk.Canvas(self.age_frame, highlightthickness=0)
        age_vsb    = ttk.Scrollbar(self.age_frame, orient='vertical',
                                   command=age_canvas.yview)
        age_canvas.configure(yscrollcommand=age_vsb.set)
        age_vsb.pack(side=tk.RIGHT, fill=tk.Y)
        age_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        age_inner = ttk.Frame(age_canvas)
        _win = age_canvas.create_window((0, 0), window=age_inner, anchor='nw')
        age_inner.bind('<Configure>',
            lambda e: age_canvas.configure(scrollregion=age_canvas.bbox('all')))
        age_canvas.bind('<Configure>',
            lambda e: age_canvas.itemconfig(_win, width=e.width))

        age_main = ttk.Frame(age_inner)
        age_main.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # ── Taxon row ──────────────────────────────────────────────────────────
        top_row = ttk.Frame(age_main)
        top_row.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(top_row, text='Taxon:', font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        self.age_taxon_var   = tk.StringVar()
        self.age_taxon_combo = ttk.Combobox(
            top_row, textvariable=self.age_taxon_var, width=14, state='readonly',
            values=['Cattle','Sheep','Goat','Pig','Horse','Red Deer','Fallow Deer',
                    'Dog','Cat','Chicken','Goose','Duck','Other Bird','Fish','Other'])
        self.age_taxon_combo.pack(side=tk.LEFT, padx=5)
        self.age_taxon_combo.bind('<<ComboboxSelected>>', self._on_age_taxon_changed)

        self._age_taxon_info = ttk.Label(top_row, text='',
            font=('Arial', 8, 'italic'), foreground='gray')
        self._age_taxon_info.pack(side=tk.LEFT, padx=8)

        # ── Two-column grid ────────────────────────────────────────────────────
        body = ttk.Frame(age_main)
        body.pack(fill=tk.BOTH, expand=True)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)

        left_col = ttk.Frame(body)
        left_col.grid(row=0, column=0, sticky='nsew', padx=(0, 4))

        right_col = ttk.Frame(body)
        right_col.grid(row=0, column=1, sticky='nsew', padx=(4, 0))

        # ── Section 1 — Dental Eruption ────────────────────────────────────────
        s1_lf = ttk.LabelFrame(left_col,
            text='1.  Dental Eruption & Replacement  (Silver 1969)', padding=5)
        s1_lf.pack(fill=tk.X, pady=(0, 5))
        self._s1_inner  = ttk.Frame(s1_lf)
        self._s1_inner.pack(fill=tk.BOTH)
        self._s1_result = tk.Label(s1_lf, text='', font=('Arial', 8, 'bold'),
            foreground='#1a5276', wraplength=310, justify=tk.LEFT)
        self._s1_result.pack(fill=tk.X, padx=2, pady=(3, 0))

        # ── Section 3 — Epiphyseal Fusion ──────────────────────────────────────
        s3_lf = ttk.LabelFrame(left_col,
            text='3.  Epiphyseal Fusion  (Silver 1969)', padding=5)
        s3_lf.pack(fill=tk.X, pady=(0, 5))
        self._s3_inner  = ttk.Frame(s3_lf)
        self._s3_inner.pack(fill=tk.BOTH)
        self._s3_result = tk.Label(s3_lf, text='', font=('Arial', 8, 'bold'),
            foreground='#1a5276', wraplength=310, justify=tk.LEFT)
        self._s3_result.pack(fill=tk.X, padx=2, pady=(3, 0))

        # ── Section 5 — Bone Histology ─────────────────────────────────────────
        s5_lf = ttk.LabelFrame(left_col,
            text='5.  Bone Histology  (Kerley 1965)  ⚗ destructive', padding=5)
        s5_lf.pack(fill=tk.X, pady=(0, 5))
        self._build_histology_section(s5_lf)

        # ── Section 2 — Dental Wear ────────────────────────────────────────────
        s2_lf = ttk.LabelFrame(right_col,
            text='2.  Dental Wear  (species-specific)', padding=5)
        s2_lf.pack(fill=tk.X, pady=(0, 5))
        self._s2_inner  = ttk.Frame(s2_lf)
        self._s2_inner.pack(fill=tk.BOTH)
        # MWS result strip — named attrs kept for backward compat
        mws_strip = ttk.Frame(s2_lf)
        mws_strip.pack(fill=tk.X, pady=(4, 0))
        ttk.Label(mws_strip, text='MWS:', font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        self.mws_score_label   = ttk.Label(mws_strip, text='—',
            font=('Arial', 11, 'bold'), foreground='#1a5276', width=5)
        self.mws_score_label.pack(side=tk.LEFT, padx=(2, 10))
        ttk.Label(mws_strip, text='Stage:', font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        self.payne_stage_label = ttk.Label(mws_strip, text='—',
            font=('Arial', 11, 'bold'), foreground='#1a5276', width=4)
        self.payne_stage_label.pack(side=tk.LEFT, padx=(2, 0))
        self.payne_desc_label  = tk.Label(s2_lf, text='Select a taxon to begin',
            font=('Arial', 8, 'italic'), foreground='#1a5276',
            wraplength=295, justify=tk.LEFT)
        self.payne_desc_label.pack(fill=tk.X, padx=2, pady=2)
        self._s2_result = tk.Label(s2_lf, text='', font=('Arial', 8, 'bold'),
            foreground='#1a5276', wraplength=310, justify=tk.LEFT)
        self._s2_result.pack(fill=tk.X, padx=2)

        # ── Section 4 — Cementum Annuli ────────────────────────────────────────
        self._s4_lf = ttk.LabelFrame(right_col,
            text='4.  Cementum Annuli  ⚗ destructive / lab', padding=5)
        self._s4_lf.pack(fill=tk.X, pady=(0, 5))
        self._build_cementum_section(self._s4_lf)

        # ── Section 6 — Gross Morphology ───────────────────────────────────────
        s6_lf = ttk.LabelFrame(right_col,
            text='6.  Gross Morphology', padding=5)
        s6_lf.pack(fill=tk.X, pady=(0, 5))
        self._build_gross_morph_section(s6_lf)

        # ── Age Method Summary ──────────────────────────────────────────────────
        summ_lf = ttk.LabelFrame(age_main, text='Age Method Summary', padding=6)
        summ_lf.pack(fill=tk.X, pady=(6, 0))

        self.age_summary_text = tk.Text(
            summ_lf, height=9, font=('Arial', 8),
            wrap=tk.WORD, state=tk.DISABLED, bg='#fafafa', relief=tk.FLAT)
        self.age_summary_text.pack(fill=tk.BOTH, expand=True)

        for tag, cfg in [
            ('meth', {'font': ('Arial', 8, 'bold')}),
            ('res',  {'foreground': '#1a5276'}),
            ('good', {'foreground': '#2e7d32'}),
            ('warn', {'foreground': '#e65100'}),
            ('na',   {'foreground': '#aaa', 'font': ('Arial', 8, 'italic')}),
            ('comb', {'font': ('Arial', 9, 'bold'), 'foreground': '#8B0000'}),
            ('note', {'font': ('Arial', 8, 'italic'), 'foreground': '#555'}),
        ]:
            self.age_summary_text.tag_configure(tag, **cfg)

        comb_row = ttk.Frame(summ_lf)
        comb_row.pack(fill=tk.X, pady=(4, 0))
        ttk.Label(comb_row, text='Combined estimate:',
                  font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        self.age_estimate    = tk.Label(comb_row, text='—',
            font=('Arial', 11, 'bold'), foreground='#8B0000')
        self.age_estimate.pack(side=tk.LEFT, padx=8)
        self.grant_age_label = ttk.Label(comb_row, text='',
            font=('Arial', 8, 'italic'), foreground='gray')
        self.grant_age_label.pack(side=tk.LEFT)

        # ── Backward-compat hidden widgets ─────────────────────────────────────
        _h = tk.Frame(self.age_frame)   # never packed/shown
        self.fusion_var          = tk.StringVar()
        self.fusion_element_var  = tk.StringVar()
        self.fusion_desc         = tk.Label(_h)
        self.fusion_age          = tk.Label(_h)
        self.fusion_source_label = tk.Label(_h)
        self.dental_inner        = self._s2_inner   # alias

        # Grant vars kept for save/load compatibility
        self.grant_vars = {t: tk.StringVar() for t in ['dP4', 'P4', 'M1', 'M2', 'M3']}

        # Section placeholder text until taxon is chosen
        for inner in [self._s1_inner, self._s2_inner, self._s3_inner]:
            ttk.Label(inner, text='Select a taxon above.',
                      font=('Arial', 8, 'italic'), foreground='gray').pack(pady=5)

    # ── Static section builders ────────────────────────────────────────────────

    def _build_histology_section(self, parent):
        ttk.Label(parent,
            text='Record lab result below. Does not auto-calculate — enter age directly.',
            font=('Arial', 7, 'italic'), foreground='gray',
            wraplength=280).pack(anchor='w', pady=(0, 4))

        r1 = ttk.Frame(parent); r1.pack(fill=tk.X, pady=1)
        ttk.Label(r1, text='Method:', width=12).pack(side=tk.LEFT)
        self._histo_method_var = tk.StringVar(value='')
        ttk.Combobox(r1, textvariable=self._histo_method_var, width=22,
            values=['', 'Kerley (1965)', 'Stout & Paine (1992)',
                    'Robling & Stout (2008)', 'Other'],
            state='readonly').pack(side=tk.LEFT)

        r2 = ttk.Frame(parent); r2.pack(fill=tk.X, pady=1)
        ttk.Label(r2, text='Age (years):', width=12).pack(side=tk.LEFT)
        self._histo_age_var = tk.StringVar()
        ttk.Entry(r2, textvariable=self._histo_age_var, width=8).pack(side=tk.LEFT)
        ttk.Label(r2, text='yr  (from lab)',
                  font=('Arial', 7), foreground='gray').pack(side=tk.LEFT, padx=4)

        r3 = ttk.Frame(parent); r3.pack(fill=tk.X, pady=1)
        ttk.Label(r3, text='Reference:', width=12).pack(side=tk.LEFT)
        self._histo_ref_var = tk.StringVar()
        ttk.Entry(r3, textvariable=self._histo_ref_var, width=22).pack(side=tk.LEFT)

        for v in [self._histo_method_var, self._histo_age_var]:
            v.trace_add('write', lambda *_: self._calculate_age_live())

    def _build_cementum_section(self, parent):
        self._s4_type_label = ttk.Label(parent, text='Tooth cementum rings:',
            font=('Arial', 8, 'italic'), foreground='gray', wraplength=280)
        self._s4_type_label.pack(anchor='w', pady=(0, 4))

        r1 = ttk.Frame(parent); r1.pack(fill=tk.X, pady=1)
        ttk.Label(r1, text='Ring count:', width=12).pack(side=tk.LEFT)
        self._cement_rings_var = tk.StringVar()
        ttk.Entry(r1, textvariable=self._cement_rings_var, width=6).pack(side=tk.LEFT)
        ttk.Label(r1, text='rings',
                  font=('Arial', 7), foreground='gray').pack(side=tk.LEFT, padx=4)

        r2 = ttk.Frame(parent); r2.pack(fill=tk.X, pady=1)
        ttk.Label(r2, text='Season of death:', width=12).pack(side=tk.LEFT)
        self._cement_season_var = tk.StringVar(value='')
        ttk.Combobox(r2, textvariable=self._cement_season_var, width=12,
            values=['', 'Spring', 'Summer', 'Autumn', 'Winter', 'Unknown'],
            state='readonly').pack(side=tk.LEFT)

        self._s4_result = tk.Label(parent, text='',
            font=('Arial', 8, 'bold'), foreground='#1a5276', wraplength=280)
        self._s4_result.pack(fill=tk.X, padx=2, pady=(4, 0))

        for v in [self._cement_rings_var, self._cement_season_var]:
            v.trace_add('write', lambda *_: self._calculate_age_live())

    def _build_gross_morph_section(self, parent):
        r1 = ttk.Frame(parent); r1.pack(fill=tk.X, pady=1)
        ttk.Label(r1, text='Age class:', width=12).pack(side=tk.LEFT)
        self._gross_morph_var = tk.StringVar(value='')
        ttk.Combobox(r1, textvariable=self._gross_morph_var, width=22,
            values=list(self._GROSS_MORPH_LABELS.values()),
            state='readonly').pack(side=tk.LEFT)

        r2 = ttk.Frame(parent); r2.pack(fill=tk.X, pady=1)
        ttk.Label(r2, text='Bone texture:', width=12).pack(side=tk.LEFT)
        self._bone_texture_var = tk.StringVar(value='')
        ttk.Combobox(r2, textvariable=self._bone_texture_var, width=22,
            values=[v for _, v in self._BONE_TEXTURE_OPTS],
            state='readonly').pack(side=tk.LEFT)

        r3 = ttk.Frame(parent); r3.pack(fill=tk.X, pady=1)
        ttk.Label(r3, text='Notes:', width=12).pack(side=tk.LEFT)
        self._gross_notes_var = tk.StringVar()
        ttk.Entry(r3, textvariable=self._gross_notes_var,
                  width=22).pack(side=tk.LEFT, fill=tk.X, expand=True)

        self._s6_result = tk.Label(parent, text='', font=('Arial', 8, 'bold'),
            foreground='#1a5276', wraplength=280)
        self._s6_result.pack(fill=tk.X, padx=2, pady=(3, 0))

        self._gross_morph_var.trace_add('write', lambda *_: self._calculate_age_live())

    # ============================================================================
    # AGE TAB — METHODS
    # ============================================================================

    def _get_taxon_group(self, taxon):
        return self._TAXON_GROUPS.get(taxon, 'unknown')

    def _on_age_taxon_changed(self, event=None):
        taxon = self.age_taxon_var.get()
        group = self._get_taxon_group(taxon)

        group_desc = {
            'artiodactyl':   'Even-toed ungulate — dental + fusion + cementum applicable',
            'perissodactyl': 'Odd-toed ungulate — dental + fusion + cementum applicable',
            'carnivore':     'Carnivore — dental eruption + wear + fusion applicable',
            'bird':          'Bird — NO teeth; fusion = pneumatization; rings = not standard',
            'fish':          'Fish — NO teeth/fusion in standard sense; rings = otolith/vertebral',
            'unknown':       '',
        }
        self._age_taxon_info.config(text=group_desc.get(group, ''))

        self._rebuild_eruption_section(taxon, group)
        self._rebuild_wear_section(taxon, group)
        self._rebuild_fusion_section(taxon, group)

        if hasattr(self, '_s4_type_label'):
            if group == 'fish':
                self._s4_type_label.config(
                    text='Otolith / vertebral rings (record count from lab):')
            else:
                self._s4_type_label.config(text='Tooth cementum rings:')

        self._calculate_age_live()

    # ── Section 1: Dental Eruption ────────────────────────────────────────────

    def _rebuild_eruption_section(self, taxon, group):
        for w in self._s1_inner.winfo_children():
            w.destroy()
        self._eruption_vars = {}
        self._erupt_interp  = {}

        if group in ('bird', 'fish'):
            msg = ('Birds have no teeth — eruption/replacement\nnot applicable.'
                   if group == 'bird' else
                   'Fish have no teeth in the mammalian sense —\neruption not applicable.')
            tk.Label(self._s1_inner, text=msg, font=('Arial', 8, 'italic'),
                     foreground='gray', justify=tk.LEFT).pack(anchor='w', padx=4, pady=6)
            self._s1_result.config(text='')
            return

        erupt_teeth = self._ERUPTION_DATA.get(taxon, {})
        if not erupt_teeth:
            tk.Label(self._s1_inner,
                     text=f'No eruption reference data available for {taxon}.\nManual notes only.',
                     font=('Arial', 8, 'italic'), foreground='gray',
                     justify=tk.LEFT).pack(anchor='w', padx=4, pady=6)
            self._s1_result.config(text='')
            return

        hdr = ttk.Frame(self._s1_inner)
        hdr.pack(fill=tk.X, pady=(0, 2))
        for col, (txt, w) in enumerate([('Tooth', 8), ('State', 22), ('Interpretation', 18)]):
            ttk.Label(hdr, text=txt, font=('Arial', 8, 'bold'), width=w
                      ).grid(row=0, column=col, padx=3, sticky='w')

        ttk.Separator(self._s1_inner, orient='horizontal').pack(fill=tk.X, pady=1)

        grid = ttk.Frame(self._s1_inner)
        grid.pack(fill=tk.X)

        for row_i, (tooth, timing) in enumerate(erupt_teeth.items()):
            has_dec = tooth in self._TEETH_WITH_DEC
            states  = self._ERUPT_STATES_WITH_DEC if has_dec else self._ERUPT_STATES_PERM_ONLY

            ttk.Label(grid, text=tooth, font=('Arial', 8, 'bold'), width=8
                      ).grid(row=row_i, column=0, padx=3, pady=2, sticky='w')

            var = tk.StringVar(value='— not observed')
            self._eruption_vars[tooth] = var
            cb = ttk.Combobox(grid, textvariable=var, values=states, width=22,
                              state='readonly')
            cb.grid(row=row_i, column=1, padx=3, pady=2)
            cb.bind('<<ComboboxSelected>>', self._on_eruption_changed)

            interp_lbl = tk.Label(grid, text='', font=('Arial', 7),
                                  foreground='#5D4037', width=18, anchor='w')
            interp_lbl.grid(row=row_i, column=2, padx=3, pady=2, sticky='w')
            self._erupt_interp[tooth] = interp_lbl

        ttk.Label(self._s1_inner,
            text='Ref: Silver 1969 / species-specific literature',
            font=('Arial', 7, 'italic'), foreground='gray').pack(anchor='w', padx=2, pady=(4, 0))

    def _on_eruption_changed(self, event=None):
        taxon    = self.age_taxon_var.get()
        erupt_db = self._ERUPTION_DATA.get(taxon, {})
        for tooth, var in self._eruption_vars.items():
            state_label = var.get()
            state_key   = self._ERUPT_STATE_KEY.get(state_label)
            interp_lbl  = self._erupt_interp.get(tooth)
            if interp_lbl is None:
                continue
            timing = erupt_db.get(tooth, {})
            if not state_key or state_key not in timing:
                interp_lbl.config(text='')
            else:
                lo, hi = timing[state_key]
                def _fmt(m):
                    return f'{m/12:.0f} yr' if m >= 24 else f'{m} mo'
                interp_lbl.config(text=f'{_fmt(lo)}–{_fmt(hi)}')
        self._calculate_age_live()

    def _get_eruption_age_range(self, taxon):
        erupt_db = self._ERUPTION_DATA.get(taxon, {})
        if not erupt_db or not self._eruption_vars:
            return None, None
        ranges = []
        for tooth, var in self._eruption_vars.items():
            state_label = var.get()
            state_key   = self._ERUPT_STATE_KEY.get(state_label)
            if not state_key:
                continue
            timing = erupt_db.get(tooth, {})
            rng = timing.get(state_key)
            if rng:
                ranges.append(rng)
        if not ranges:
            return None, None
        lo = max(r[0] for r in ranges)
        hi = min(r[1] for r in ranges)
        if hi < lo:
            hi = lo
        return lo, hi

    # ── Section 2: Dental Wear ────────────────────────────────────────────────

    def _rebuild_wear_section(self, taxon, group):
        for w in self._s2_inner.winfo_children():
            w.destroy()
        self.mws_score_label.config(text='—')
        self.payne_stage_label.config(text='—')
        self.payne_desc_label.config(text='')
        self._s2_result.config(text='')

        if group in ('bird', 'fish'):
            msg = ('Birds have no teeth — dental wear\nnot applicable.'
                   if group == 'bird' else
                   'Fish dental wear not applicable\nin standard zooarchaeological form.')
            tk.Label(self._s2_inner, text=msg, font=('Arial', 8, 'italic'),
                     foreground='gray', justify=tk.LEFT).pack(anchor='w', padx=4, pady=6)
            return

        if group == 'unknown':
            tk.Label(self._s2_inner, text='Select a taxon to load wear reference.',
                     font=('Arial', 8, 'italic'), foreground='gray').pack(pady=5)
            return

        if taxon == 'Pig':
            self._build_pig_wear_ui()
        elif group == 'artiodactyl':
            self._build_grant_dental_ui(taxon)
        elif group == 'perissodactyl':
            self._build_horse_dental_ui()
        elif group == 'carnivore':
            self._build_dog_dental_ui()

    def _build_pig_wear_ui(self):
        ttk.Label(self._s2_inner,
            text='Bull & Payne (1982) — mandibular wear stages',
            font=('Arial', 7, 'italic'), foreground='gray').pack(anchor='w', pady=(0, 4))

        self._pig_wear_var = tk.StringVar(value='')
        for stage, (lo, hi, desc, color) in self._PIG_WEAR.items():
            def _fmt(m): return f'{m/12:.0f} yr' if m >= 24 else f'{m} mo'
            row_f = ttk.Frame(self._s2_inner)
            row_f.pack(fill=tk.X, pady=1)
            tk.Radiobutton(row_f, text=f'  {stage}', variable=self._pig_wear_var,
                           value=stage, command=self._calculate_age_live,
                           font=('Arial', 8, 'bold'), fg=color,
                           activeforeground=color, selectcolor='#f0f0f0',
                           width=3, anchor='w').pack(side=tk.LEFT)
            tk.Label(row_f, text=f'{_fmt(lo)}–{_fmt(hi)}  |  {desc}',
                     font=('Arial', 7), foreground='#555',
                     wraplength=240, justify=tk.LEFT).pack(side=tk.LEFT, fill=tk.X)

        nr = ttk.Frame(self._s2_inner)
        nr.pack(fill=tk.X, pady=(4, 0))
        tk.Radiobutton(nr, text='  Not recorded', variable=self._pig_wear_var,
                       value='', command=self._calculate_age_live,
                       font=('Arial', 8), foreground='gray').pack(side=tk.LEFT)

    def _build_grant_dental_ui(self, taxon):
        note = ('dP4 present before ~6 mo; replaced by P4 after ~6 mo'
                if taxon in {'Sheep', 'Goat', 'Cattle'} else
                'Red Deer: score each tooth present; absent → leave as —')
        ttk.Label(self._s2_inner,
                  text=f'Grant (1982) / Payne (1973) MWS   |   {note}',
                  font=('Arial', 7, 'italic'), foreground='gray',
                  wraplength=290).pack(anchor='w', pady=(0, 4))

        grid = ttk.Frame(self._s2_inner)
        grid.pack(fill=tk.X, padx=2)
        for col, (hdr, w) in enumerate([('Tooth', 5), ('Stage', 5), ('Range', 18)]):
            ttk.Label(grid, text=hdr, font=('Arial', 8, 'bold'), width=w
                      ).grid(row=0, column=col, padx=4, pady=1, sticky='w')

        tooth_info = {'dP4': 'a–i (9)', 'P4': 'a–h (8)',
                      'M1': 'a–p (16)', 'M2': 'a–p (16)', 'M3': 'a–p (16)'}
        for row_i, (tooth, valid_txt) in enumerate(tooth_info.items(), start=1):
            ttk.Label(grid, text=tooth, font=('Arial', 9, 'bold'), width=5
                      ).grid(row=row_i, column=0, padx=4, pady=2, sticky='w')
            cb = ttk.Combobox(grid, textvariable=self.grant_vars[tooth],
                              values=self._GRANT_TEETH[tooth], width=5, state='readonly')
            cb.grid(row=row_i, column=1, padx=4, pady=2)
            cb.bind('<<ComboboxSelected>>', self._on_tooth_stage_changed)
            ttk.Label(grid, text=valid_txt, font=('Arial', 7), foreground='gray'
                      ).grid(row=row_i, column=2, padx=4, pady=2, sticky='w')

    def _build_horse_dental_ui(self):
        self._horse_vars = {}
        ttk.Label(self._s2_inner, text='Levine (1982) — check all indicators present:',
                  font=('Arial', 8, 'bold')).pack(anchor='w', pady=(2, 4))
        for key, label in [
            ('m1_erupted',     'M1 erupted  (≥ 1 yr)'),
            ('m2_erupted',     'M2 erupted  (≥ 2 yr)'),
            ('i1_permanent',   'I1 permanent  (≥ 2.5 yr)'),
            ('i2_permanent',   'I2 permanent  (≥ 3.5 yr)'),
            ('i3_permanent',   'I3 permanent  (≥ 4.5 yr)'),
            ('dental_star',    'Dental star on incisors  (≥ 5 yr)'),
            ('galvayne_start', "Galvayne's groove at gumline  (≥ 10 yr)"),
            ('galvayne_half',  "Galvayne's groove halfway  (≥ 15 yr)"),
            ('galvayne_full',  "Galvayne's groove full length  (≥ 20 yr)"),
        ]:
            var = tk.BooleanVar()
            self._horse_vars[key] = var
            ttk.Checkbutton(self._s2_inner, text=label, variable=var,
                            command=self._calculate_age_live).pack(anchor='w', padx=4)

    def _build_dog_dental_ui(self):
        self._dog_wear_var = tk.StringVar(value='— not recorded')
        ttk.Label(self._s2_inner,
                  text='König & Liebich (2004) — overall wear stage:',
                  font=('Arial', 8, 'bold')).pack(anchor='w', pady=(2, 4))
        for stage in ['— not recorded',
                      'Deciduous teeth  (< 7 mo)',
                      'Slight wear — enamel only  (1–3 yr)',
                      'Moderate — dentine exposed  (3–5 yr)',
                      'Heavy — pulp cavity exposed  (5–8 yr)',
                      'Severe — worn to roots  (8+ yr)']:
            ttk.Radiobutton(self._s2_inner, text=stage, variable=self._dog_wear_var,
                            value=stage, command=self._calculate_age_live
                            ).pack(anchor='w', padx=4, pady=1)

    def _on_tooth_stage_changed(self, event=None):
        self._calculate_age_live()

    # ── Section 3: Epiphyseal Fusion ──────────────────────────────────────────

    def _rebuild_fusion_section(self, taxon, group):
        for w in self._s3_inner.winfo_children():
            w.destroy()
        self._s3_result.config(text='')

        if group == 'fish':
            tk.Label(self._s3_inner,
                     text='Standard epiphyseal fusion not applicable to fish.',
                     font=('Arial', 8, 'italic'), foreground='gray',
                     justify=tk.LEFT).pack(anchor='w', padx=4, pady=6)
            return

        if group == 'bird':
            tk.Label(self._s3_inner,
                     text='Birds: no growth plate fusion in mammalian sense.\n'
                          'Record pneumatization state in notes below.',
                     font=('Arial', 8, 'italic'), foreground='gray',
                     justify=tk.LEFT).pack(anchor='w', padx=4, pady=3)
            r = ttk.Frame(self._s3_inner); r.pack(fill=tk.X, pady=2)
            ttk.Label(r, text='Pneumatization:', width=14).pack(side=tk.LEFT)
            self._bird_pneum_var = tk.StringVar(value='')
            ttk.Combobox(r, textvariable=self._bird_pneum_var, width=20,
                values=['', 'None (immature)', 'Partial', 'Full (adult)'],
                state='readonly').pack(side=tk.LEFT)
            self._bird_pneum_var.trace_add('write', lambda *_: self._calculate_age_live())
            return

        # Standard mammal fusion
        fe_row = ttk.Frame(self._s3_inner); fe_row.pack(fill=tk.X, pady=(0, 3))
        ttk.Label(fe_row, text='Element:', width=9).pack(side=tk.LEFT)
        self.fusion_element_var = tk.StringVar()
        self.fusion_element_combo = ttk.Combobox(
            fe_row, textvariable=self.fusion_element_var, width=22, state='readonly')
        self.fusion_element_combo.pack(side=tk.LEFT, padx=2)
        self.fusion_element_combo.bind('<<ComboboxSelected>>',
                                       self._update_fusion_interpretation)

        fs_row = ttk.Frame(self._s3_inner); fs_row.pack(fill=tk.X, pady=(0, 3))
        ttk.Label(fs_row, text='State:', width=9).pack(side=tk.LEFT)
        self.fusion_var = tk.StringVar()
        for code, label in [('uf', 'Unfused'), ('fu', 'Fusing'), ('fd', 'Fused')]:
            ttk.Radiobutton(fs_row, text=label, variable=self.fusion_var,
                            value=code,
                            command=self._update_fusion_interpretation
                            ).pack(side=tk.LEFT, padx=4)

        self.fusion_desc = tk.Label(
            self._s3_inner, text='Select element and state above',
            font=('Arial', 8, 'italic'), foreground='#5D4037',
            wraplength=290, justify=tk.LEFT)
        self.fusion_desc.pack(fill=tk.X, padx=2, pady=(3, 0))

        self.fusion_age = tk.Label(
            self._s3_inner, text='', font=('Arial', 8), foreground='#5D4037',
            wraplength=290, justify=tk.LEFT)
        self.fusion_age.pack(fill=tk.X, padx=2)

        self.fusion_source_label = tk.Label(
            self._s3_inner, text='', font=('Arial', 7), foreground='gray',
            wraplength=290, justify=tk.LEFT)
        self.fusion_source_label.pack(fill=tk.X, padx=2)

        self._refresh_fusion_elements(taxon)

    def _refresh_fusion_elements(self, taxon):
        elems_dict = self._parse_fusion_elements(taxon) if taxon else {}
        elem_list  = list(elems_dict.keys())
        if hasattr(self, 'fusion_element_combo'):
            self.fusion_element_combo['values'] = [''] + elem_list
            current = self.fusion_element_var.get()
            if current and current not in elem_list:
                self.fusion_element_var.set('')
        self._update_fusion_interpretation()

    def _update_fusion_interpretation(self, event=None):
        taxon  = self.age_taxon_var.get()
        group  = self._get_taxon_group(taxon)
        if group in ('bird', 'fish') or not hasattr(self, 'fusion_element_combo'):
            self._calculate_age_live()
            return

        element    = self.fusion_element_var.get()
        state_code = self.fusion_var.get()
        _labels    = {'uf': 'Unfused', 'fu': 'Fusing', 'fd': 'Fused'}
        state_txt  = _labels.get(state_code, '')

        if not state_code:
            self.fusion_desc.config(text='Select element and state above')
            self.fusion_age.config(text='')
            self.fusion_source_label.config(text='')
            self._calculate_age_live()
            return

        if not element:
            self.fusion_desc.config(text=f'State: {state_txt} — select element for age range')
            self.fusion_age.config(text='')
            self.fusion_source_label.config(text='')
            self._calculate_age_live()
            return

        elems_dict = self._parse_fusion_elements(taxon)
        rng = elems_dict.get(element)
        if rng:
            lo, hi = rng
            if state_code == 'uf':
                self.fusion_desc.config(text=f'Unfused → younger than {lo}–{hi} mo')
                self.fusion_age.config(text=f'{element} fuses at {lo}–{hi} mo')
            elif state_code == 'fu':
                self.fusion_desc.config(text=f'Fusing → approximately {lo}–{hi} mo')
                self.fusion_age.config(text=f'Near fusion age for {element}')
            else:
                self.fusion_desc.config(text=f'Fused → older than {lo} mo')
                self.fusion_age.config(text=f'{element} fusion age: {lo}–{hi} mo')
            self.fusion_source_label.config(
                text='Ref: Silver 1969 / morphological_keys.json')
        else:
            self.fusion_desc.config(text=f'State: {state_txt}')
            self.fusion_age.config(text='Age data not available for this element')
            self.fusion_source_label.config(text='')
        self._calculate_age_live()

    # ── Main live calculator ───────────────────────────────────────────────────

    def _calculate_age_live(self):
        """
        Independently calculate age from each of the 6 methods.
        Each method updates its own result label.
        Summary table and combined estimate rebuilt at the end.
        Methods NEVER share calculations.
        """
        taxon = self.age_taxon_var.get()
        group = self._get_taxon_group(taxon)
        results = {}  # method_name → (lo_mo, hi_mo, display_str, ref_str, confidence)

        # ── Method 1: Dental Eruption ──────────────────────────────────────────
        if group not in ('bird', 'fish') and hasattr(self, '_eruption_vars') and self._eruption_vars:
            lo, hi = self._get_eruption_age_range(taxon)
            if lo is not None:
                def _fmt(m): return f'{m/12:.1f} yr' if m >= 24 else f'{m} mo'
                txt = f'{_fmt(lo)} – {_fmt(hi)}'
                results['eruption'] = (lo, hi, txt, 'Silver 1969', 'medium')
                self._s1_result.config(text=f'→ {txt}')
            else:
                self._s1_result.config(text='')
        else:
            if hasattr(self, '_s1_result'):
                self._s1_result.config(text='')

        # ── Method 2: Dental Wear ─────────────────────────────────────────────
        wear_lo = wear_hi = None
        wear_txt = ''

        if group == 'artiodactyl' and taxon == 'Pig':
            stage = getattr(self, '_pig_wear_var', tk.StringVar()).get()
            if stage and stage in self._PIG_WEAR:
                lo, hi, desc, _ = self._PIG_WEAR[stage]
                def _fmt(m): return f'{m/12:.1f} yr' if m >= 24 else f'{m} mo'
                wear_lo, wear_hi = lo, hi
                wear_txt = f'Stage {stage}: {_fmt(lo)}–{_fmt(hi)}'
                self.mws_score_label.config(text=stage)
                self.payne_stage_label.config(text='—')
                self.payne_desc_label.config(text=desc)
                self._s2_result.config(text=f'→ {wear_txt}')

        elif group == 'artiodactyl' and taxon in self._ERUPTION_DATA:
            mws_sum = n_teeth = 0
            for tooth, var in self.grant_vars.items():
                val = var.get().strip().lower()
                if val and val != '—':
                    num = self._GRANT_NUM.get(val)
                    if num:
                        mws_sum += num
                        n_teeth += 1
            if n_teeth > 0:
                mws_total = mws_sum
                self.mws_score_label.config(text=str(mws_total))
                for mws_lo_b, mws_hi_b, stage, age_lo, age_hi in self._MWS_PAYNE:
                    if mws_lo_b <= mws_total <= mws_hi_b:
                        wear_lo, wear_hi = age_lo, age_hi
                        def _fmt(m): return f'{m/12:.1f} yr' if m >= 24 else f'{m} mo'
                        wear_txt = f'MWS {mws_total} → Stage {stage}: {_fmt(age_lo)}–{_fmt(age_hi)}'
                        self.payne_stage_label.config(text=stage)
                        desc = self._get_payne_stage_description(stage)
                        self.payne_desc_label.config(text=desc or f'Payne stage {stage}')
                        self._s2_result.config(text=f'→ {wear_txt}')
                        break
            else:
                self.mws_score_label.config(text='—')
                self.payne_stage_label.config(text='—')
                self.payne_desc_label.config(text='Enter tooth stages to calculate MWS')
                self._s2_result.config(text='')

        elif group == 'perissodactyl':
            rng = self._interpret_horse_age()
            if rng:
                wear_lo, wear_hi = rng
                def _fmt(m): return f'{m/12:.1f} yr' if m >= 24 else f'{m} mo'
                wear_txt = f'Levine indicators: {_fmt(wear_lo)}–{_fmt(wear_hi)}'
                self._s2_result.config(text=f'→ {wear_txt}')
            self.mws_score_label.config(text='n/a')
            self.payne_stage_label.config(text='—')

        elif group == 'carnivore':
            rng = self._interpret_dog_age()
            if rng:
                wear_lo, wear_hi = rng
                def _fmt(m): return f'{m/12:.1f} yr' if m >= 24 else f'{m} mo'
                wear_txt = f'Wear stage: {_fmt(wear_lo)}–{_fmt(wear_hi)}'
                self._s2_result.config(text=f'→ {wear_txt}')
            self.mws_score_label.config(text='n/a')
            self.payne_stage_label.config(text='—')

        if wear_lo is not None:
            ref2 = ('Bull & Payne 1982' if taxon == 'Pig' else
                    'Levine 1982' if group == 'perissodactyl' else
                    'König & Liebich 2004' if group == 'carnivore' else
                    'Grant 1982 / Payne 1973')
            results['wear'] = (wear_lo, wear_hi, wear_txt, ref2, 'high')

        # ── Method 3: Epiphyseal Fusion ───────────────────────────────────────
        if group not in ('bird', 'fish') and hasattr(self, 'fusion_var'):
            state_code = self.fusion_var.get()
            element    = self.fusion_element_var.get() if hasattr(self, 'fusion_element_var') else ''
            if state_code and element and taxon:
                elems = self._parse_fusion_elements(taxon)
                rng   = elems.get(element)
                if rng:
                    lo, hi = rng
                    if state_code == 'uf':
                        fusion_lo, fusion_hi = 0, lo
                    elif state_code == 'fu':
                        fusion_lo, fusion_hi = lo, hi
                    else:
                        fusion_lo, fusion_hi = hi, 999
                    def _fmt(m): return f'{m/12:.1f} yr' if m >= 24 else f'{m} mo'
                    if state_code == 'uf':
                        fus_txt = f'Unfused → < {_fmt(lo)}'
                    elif state_code == 'fu':
                        fus_txt = f'Fusing → ~{_fmt(lo)}–{_fmt(hi)}'
                    else:
                        fus_txt = f'Fused → > {_fmt(lo)}'
                    self._s3_result.config(text=f'→ {fus_txt}')
                    results['fusion'] = (fusion_lo, fusion_hi, fus_txt, 'Silver 1969', 'medium')
                else:
                    self._s3_result.config(text='')
            else:
                if hasattr(self, '_s3_result'):
                    self._s3_result.config(text='')
        elif group == 'bird' and hasattr(self, '_bird_pneum_var'):
            state = self._bird_pneum_var.get()
            if state == 'Full (adult)':
                results['fusion'] = (12, 999, 'Fully pneumatized (adult)', 'Serjeantson 2009', 'low')

        # ── Method 4: Cementum Annuli ──────────────────────────────────────────
        if hasattr(self, '_cement_rings_var'):
            rings_raw = self._cement_rings_var.get().strip()
            season    = self._cement_season_var.get()
            if rings_raw:
                try:
                    rings = int(rings_raw)
                    season_frac = {'Spring': 0.25, 'Summer': 0.5,
                                   'Autumn': 0.75, 'Winter': 0.0}.get(season, 0.0)
                    age_yr  = rings + season_frac
                    lo_mo   = int((age_yr - 0.5) * 12)
                    hi_mo   = int((age_yr + 0.5) * 12)
                    cement_lo, cement_hi = max(0, lo_mo), hi_mo
                    label4  = 'Otolith/vertebral' if group == 'fish' else 'Cementum'
                    season_txt = f' ({season})' if season and season != 'Unknown' else ''
                    c_txt = f'{label4}: {rings} rings{season_txt} ≈ {age_yr:.1f} yr'
                    self._s4_result.config(text=f'→ {c_txt}')
                    results['cementum'] = (cement_lo, cement_hi, c_txt, 'Hillson 2005', 'high')
                except ValueError:
                    self._s4_result.config(text='')
            else:
                self._s4_result.config(text='')

        # ── Method 5: Bone Histology ──────────────────────────────────────────
        if hasattr(self, '_histo_age_var'):
            histo_raw = self._histo_age_var.get().strip()
            if histo_raw:
                try:
                    histo_yr = float(histo_raw)
                    h_lo = max(0, int((histo_yr - 1) * 12))
                    h_hi = int((histo_yr + 1) * 12)
                    h_txt = f'Lab estimate: {histo_yr:.1f} yr'
                    method = self._histo_method_var.get() or 'Histology'
                    results['histology'] = (h_lo, h_hi, h_txt, method, 'high')
                except ValueError:
                    pass

        # ── Method 6: Gross Morphology ────────────────────────────────────────
        if hasattr(self, '_gross_morph_var'):
            morph_label = self._gross_morph_var.get()
            morph_key = next(
                (k for k, v in self._GROSS_MORPH_LABELS.items() if v == morph_label), '')
            lo_mo, hi_mo = self._GROSS_MORPH.get(morph_key, (None, None))
            if lo_mo is not None:
                def _fmt(m): return f'{m/12:.1f} yr' if m >= 24 else f'{m} mo'
                g_txt = morph_label
                if hi_mo and hi_mo < 999:
                    g_txt += f' (~{_fmt(lo_mo)}–{_fmt(hi_mo)})'
                else:
                    g_txt += f' (≥ {_fmt(lo_mo)})'
                self._s6_result.config(text=f'→ {g_txt}')
                results['morphology'] = (lo_mo, hi_mo, g_txt, 'Gross observation', 'low')
            else:
                if hasattr(self, '_s6_result'):
                    self._s6_result.config(text='')

        self._update_age_summary(results)

    def _update_age_summary(self, results):
        """Rebuild the summary Text widget and combined estimate from all method results."""
        METHOD_NAMES = {
            'eruption':  '1. Dental Eruption  (Silver 1969)',
            'wear':      '2. Dental Wear',
            'fusion':    '3. Epiphyseal Fusion  (Silver 1969)',
            'cementum':  '4. Cementum / Annuli',
            'histology': '5. Bone Histology',
            'morphology':'6. Gross Morphology',
        }
        ALL_METHODS = list(METHOD_NAMES.keys())

        self.age_summary_text.config(state=tk.NORMAL)
        self.age_summary_text.delete(1.0, tk.END)

        for key in ALL_METHODS:
            name = METHOD_NAMES[key]
            if key in results:
                lo, hi, txt, ref, conf = results[key]
                conf_icon = {'high': '●', 'medium': '◑', 'low': '○'}.get(conf, '◑')
                line = f'{conf_icon} {name:<42}  {txt}  [{ref}]'
                tag  = 'good' if conf == 'high' else 'res'
                self.age_summary_text.insert(tk.END, line + '\n', tag)
            else:
                self.age_summary_text.insert(tk.END,
                    f'○ {name:<42}  not recorded\n', 'na')

        if results:
            self.age_summary_text.insert(tk.END, '─' * 78 + '\n', 'na')
            hm = {k: v for k, v in results.items() if v[4] in ('high', 'medium')}
            if not hm:
                hm = results
            if hm:
                all_lo = [v[0] for v in hm.values() if v[0] is not None]
                all_hi = [v[1] for v in hm.values() if v[1] is not None and v[1] < 999]
                if all_lo and all_hi:
                    best_lo = max(all_lo)
                    best_hi = min(all_hi)
                    def _fmt(m): return f'{m/12:.1f} yr' if m >= 24 else f'{m} mo'
                    if best_hi >= best_lo:
                        combined_txt = f'{_fmt(best_lo)} – {_fmt(best_hi)}'
                        note = f'({len(hm)} method{"s" if len(hm)>1 else ""} consistent)'
                    else:
                        combined_txt = f'~{_fmt(best_lo)}'
                        note = '(methods suggest slightly different ages — see above)'
                    self.age_estimate.config(text=combined_txt)
                    self.grant_age_label.config(text=note)
                    self.age_summary_text.insert(tk.END,
                        f'  Combined:  {combined_txt}   {note}\n', 'comb')
                elif all_lo:
                    lo_only = max(all_lo)
                    def _fmt(m): return f'{m/12:.1f} yr' if m >= 24 else f'{m} mo'
                    combined_txt = f'≥ {_fmt(lo_only)}'
                    self.age_estimate.config(text=combined_txt)
                    self.grant_age_label.config(text='(minimum age from fusion/morphology)')
                    self.age_summary_text.insert(tk.END,
                        f'  Combined:  {combined_txt}\n', 'comb')
                else:
                    self.age_estimate.config(text='—')
                    self.grant_age_label.config(text='')
            else:
                self.age_estimate.config(text='—')
                self.grant_age_label.config(text='')
        else:
            self.age_estimate.config(text='—')
            self.grant_age_label.config(text='')
            self.age_summary_text.insert(tk.END, 'No age data recorded.\n', 'na')

        self.age_summary_text.config(state=tk.DISABLED)

    def _interpret_horse_age(self):
        if not hasattr(self, '_horse_vars') or not self._horse_vars:
            return None
        v = self._horse_vars
        for key, rng in [
            ('galvayne_full',  (240, 360)),
            ('galvayne_half',  (180, 240)),
            ('galvayne_start', (120, 180)),
            ('dental_star',    (60,  120)),
            ('i3_permanent',   (54,   72)),
            ('i2_permanent',   (42,   54)),
            ('i1_permanent',   (30,   42)),
            ('m2_erupted',     (24,   36)),
            ('m1_erupted',     (12,   24)),
        ]:
            var = v.get(key)
            if var and var.get():
                return rng
        return None

    def _interpret_dog_age(self):
        if not hasattr(self, '_dog_wear_var') or not self._dog_wear_var:
            return None
        return {
            'Deciduous teeth  (< 7 mo)':               (0,   7),
            'Slight wear — enamel only  (1–3 yr)':      (12,  36),
            'Moderate — dentine exposed  (3–5 yr)':     (36,  60),
            'Heavy — pulp cavity exposed  (5–8 yr)':    (60,  96),
            'Severe — worn to roots  (8+ yr)':          (96, 180),
        }.get(self._dog_wear_var.get())

    # Stubs for backward compat
    def _calculate_mws(self):
        self._calculate_age_live()

    def _estimate_age_from_grant(self):
        self._calculate_age_live()

    def _update_age_interpretation(self, event=None):
        self._on_age_taxon_changed(event)

    # ============================================================================
    # MORPHOLOGICAL KEYS LOADER
    # ============================================================================

    def _load_morph_keys(self):
        try:
            plugin_dir = Path(__file__).parent
            appbase_dir = plugin_dir.parent.parent
            path = appbase_dir / "config" / "morphological_keys.json"
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    self.morph_keys = json.load(f)
                self.set_status("✅ Loaded morphological keys", "success")
            else:
                self.morph_keys = {}
                self.set_status("⚠️ morphological_keys.json not found - using built-in fusion ages", "warning")
        except Exception as e:
            self.morph_keys = {}
            self.set_status(f"⚠️ Error loading morphological keys: {e}", "warning")

    def _parse_fusion_elements(self, taxon):
        import re as _re
        if not self.morph_keys:
            taxon_ages = self.FUSION_AGES.get(taxon, {})
            return {k.replace('_', ' ').title(): (v, v)
                    for k, v in sorted(taxon_ages.items(), key=lambda x: x[1])}

        key_map = {
            'Cattle': 'Cattle epiphyseal fusion ages',
            'Sheep':  'Sheep/goat epiphyseal fusion ages',
            'Goat':   'Sheep/goat epiphyseal fusion ages',
            'Pig':    'Pig epiphyseal fusion ages',
        }
        json_key = key_map.get(taxon)
        if not json_key or json_key not in self.morph_keys:
            taxon_ages = self.FUSION_AGES.get(taxon, {})
            return {k.replace('_', ' ').title(): (v, v)
                    for k, v in sorted(taxon_ages.items(), key=lambda x: x[1])}

        text = self.morph_keys[json_key].get('text', '')
        elements = {}
        current_group_range = None

        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            if 'FUSING' in line.upper() and '(' in line:
                m = _re.search(r'(\d+)\s*[-\u2013]\s*(\d+)', line)
                if m:
                    current_group_range = (int(m.group(1)), int(m.group(2)))
            elif line.startswith('\u2022'):
                line_clean = line.lstrip('\u2022').strip()
                m = _re.search(r'(\d+)\s*[-\u2013]\s*(\d+)\s*months', line_clean)
                if m:
                    age_range = (int(m.group(1)), int(m.group(2)))
                else:
                    m = _re.search(r'(\d+)\+?\s*months', line_clean)
                    if m:
                        v = int(m.group(1))
                        age_range = (v, v + 12)
                    elif current_group_range:
                        age_range = current_group_range
                    else:
                        continue
                elem = _re.sub(r'\s*[-\u2013]\s*\d+.*$', '', line_clean).strip()
                if elem:
                    elements[elem] = age_range

        return dict(sorted(elements.items(), key=lambda x: x[1][0]))

    def _get_payne_stage_description(self, stage):
        import re as _re
        text = (self.morph_keys
                .get('Caprine mandibular wear stages (Payne 1973, 1987)', {})
                .get('text', ''))
        if not text or not stage or stage == '—':
            return ''
        pattern = r'STAGE ' + _re.escape(stage) + r'\s*\([^)]+\):\s*(.*?)(?=\nSTAGE [A-I]|\Z)'
        m = _re.search(pattern, text, _re.DOTALL)
        if not m:
            return ''
        lines = [l.strip().lstrip('\u2022').strip()
                 for l in m.group(1).splitlines() if l.strip()]
        return '  \u00b7  '.join(lines[:4])

    # ============================================================================
    # UNIFIED DATABASE LOADER
    # ============================================================================

    def _load_unified_database(self):
        try:
            plugin_dir = Path(__file__).parent
            appbase_dir = plugin_dir.parent.parent
            gz_path = appbase_dir / "config" / "zooarch_database.json.gz"

            if not gz_path.exists():
                self.set_status("⚠️ zooarch_database.json.gz not found in config folder", "warning")
                self._legacy_database_load()
                return False

            with gzip.open(gz_path, 'rt', encoding='utf-8') as f:
                self.full_db = json.load(f)

            self.references = self.full_db.get('references', {})

            self.taxon_references = {}
            for ref_name, ref_data in self.references.items():
                taxon = ref_data.get('taxon', 'Unknown')
                self.taxon_references.setdefault(taxon, []).append(ref_name)

            self.reference_standards = {}
            for ref_name, ref_data in self.references.items():
                taxon = ref_data.get('taxon', 'Unknown')
                measurements = ref_data.get('measurements', [])
                elem_dict = {}
                for m in measurements:
                    element = m.get('element', 'Unknown')
                    measure = m.get('measure', '')
                    value = m.get('standard')
                    if measure and value is not None:
                        elem_dict.setdefault(element, {})[measure] = float(value)
                if elem_dict:
                    self.reference_standards.setdefault(taxon, {})[ref_name] = elem_dict

            self.taxonomy = {}
            for taxon_entry in self.full_db.get('taxonomy', []):
                species = taxon_entry.get('species')
                if species:
                    self.taxonomy[species] = {
                        'genus': taxon_entry.get('genus'),
                        'tribe': taxon_entry.get('tribe'),
                        'subfamily': taxon_entry.get('subfamily'),
                        'family': taxon_entry.get('family')
                    }

            thesaurus = self.full_db.get('thesaurus', {})
            self.taxon_thesaurus = thesaurus.get('taxon', {})
            self.element_thesaurus = thesaurus.get('element', {})

            measure_lists = thesaurus.get('measure', [])
            self.measure_thesaurus = {}
            if len(measure_lists) >= 1:
                for code in measure_lists[0]:
                    self.measure_thesaurus[code] = code
                for i, variant_list in enumerate(measure_lists[1:], 1):
                    for j, variant in enumerate(variant_list):
                        if variant and j < len(measure_lists[0]):
                            self.measure_thesaurus[variant] = measure_lists[0][j]

            self.reference_sets = self.full_db.get('reference_sets', {})
            self.specimen_data = self.full_db.get('specimen_data', {})
            self.example_specimens = self.specimen_data.get('records', [])

            ref_count = len(self.references)
            taxon_count = len(self.taxon_references)
            specimen_count = len(self.example_specimens)
            self.set_status(
                f"✅ Loaded unified DB: {ref_count} references ({taxon_count} taxa), "
                f"{specimen_count} example specimens", "success")
            return True

        except Exception as e:
            self.set_status(f"⚠️ Error loading unified database: {e}", "warning")
            import traceback
            traceback.print_exc()
            self._legacy_database_load()
            return False

    def _legacy_database_load(self):
        try:
            plugin_dir = Path(__file__).parent
            appbase_dir = plugin_dir.parent.parent
            gz_path = appbase_dir / "config" / "zooarch_database.json.gz"
            old_path = appbase_dir / "config" / "zooarch_reference.json"

            if gz_path.exists():
                with gzip.open(gz_path, 'rt', encoding='utf-8') as f:
                    full_db = json.load(f)
                self.full_db = full_db
                raw_refs = full_db.get('references', {})
                for ref_name, ref_data in raw_refs.items():
                    taxon = ref_data.get('taxon', '')
                    if not taxon:
                        continue
                    elem_dict = {}
                    for m in ref_data.get('measurements', []):
                        el    = m.get('element', 'Unknown')
                        mcode = m.get('measure', '')
                        val   = m.get('standard')
                        if not mcode or val is None:
                            continue
                        elem_dict.setdefault(el, {})[mcode] = float(val)
                    if not elem_dict:
                        continue
                    self.taxon_references.setdefault(taxon, [])
                    if ref_name not in self.taxon_references[taxon]:
                        self.taxon_references[taxon].append(ref_name)
                    self.reference_standards.setdefault(taxon, {})[ref_name] = elem_dict
                taxa_count = len(self.taxon_references)
                self.set_status(f"✅ Loaded {taxa_count} reference taxa (legacy mode)", "success")
            else:
                success, msg = self._load_simple_json(old_path)
                if not success:
                    self.set_status(f"⚠️ No database found. LSI will use built-in standards.", "warning")
        except Exception as e:
            self.set_status(f"⚠️ Legacy load failed: {e}", "warning")

    def _load_simple_json(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for taxon, meas_dict in data.get('references', {}).items():
                self.taxon_references[taxon] = [taxon]
                elem_dict = {'All': {}}
                for code, stats in meas_dict.items():
                    if isinstance(stats, dict) and 'mean' in stats:
                        elem_dict['All'][code] = stats['mean']
                self.reference_standards.setdefault(taxon, {})[taxon] = elem_dict
            return True, f"Loaded {len(self.taxon_references)} taxa"
        except Exception as e:
            return False, str(e)

    # ============================================================================
    # LSI TAB CONSTRUCTION
    # ============================================================================

    def _build_lsi_skeleton(self):
        header = tk.Frame(self.lsi_frame, bg="#2c3e50", height=32)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        self.lsi_header_label = tk.Label(header,
                 text=f"📊 Log Size Index (LSI) Calculator — Loading database...",
                 font=("Arial", 10, "bold"), bg="#2c3e50", fg="white")
        self.lsi_header_label.pack(side=tk.LEFT, padx=10, pady=5)

        mode_nb = ttk.Notebook(self.lsi_frame)
        mode_nb.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)

        self.single_tab = ttk.Frame(mode_nb)
        self.batch_tab  = ttk.Frame(mode_nb)
        mode_nb.add(self.single_tab, text="  Single Specimen  ")
        mode_nb.add(self.batch_tab,  text="  Batch Dataset (zoolog LogRatios)  ")

        ttk.Label(self.single_tab,
                  text="Loading reference database...\n\nPlease wait.",
                  font=("Arial", 10)).pack(expand=True, pady=50)
        ttk.Label(self.batch_tab,
                  text="Loading reference database...\n\nPlease wait.",
                  font=("Arial", 10)).pack(expand=True, pady=50)

    def _populate_lsi_tab(self):
        for widget in self.single_tab.winfo_children():
            widget.destroy()
        for widget in self.batch_tab.winfo_children():
            widget.destroy()

        self._build_single_tab(self.single_tab)
        self._build_batch_tab(self.batch_tab)

        if self.example_specimens:
            example_frame = ttk.Frame(self.lsi_frame)
            example_frame.pack(fill=tk.X, padx=8, pady=2)
            ttk.Button(example_frame, text="📚 Load Example Specimen",
                      command=self._load_example_specimen).pack(side=tk.LEFT)

        self.lsi_header_label.config(
            text=f"📊 Log Size Index (LSI) Calculator — zoolog methodology")

        self._last_lsi_results  = {}
        self._last_lsi_condensed = {}
        self._batch_lsi_results  = []

        self._auto_select_from_specimen()
        if hasattr(self, 'lsi_taxon_var') and self.lsi_taxon_var.get():
            self._on_taxon_selected()

    def _build_single_tab(self, parent):
        cfg = ttk.Frame(parent)
        cfg.pack(fill=tk.X, padx=8, pady=(6, 2))

        ttk.Label(cfg, text="Taxon:", font=("Arial", 9, "bold")).grid(row=0, column=0, sticky='w', padx=(0, 2))
        self.lsi_taxon_var = tk.StringVar()
        self.lsi_taxon_combo = ttk.Combobox(cfg, textvariable=self.lsi_taxon_var,
                                             values=sorted(self.taxon_references.keys()) if self.taxon_references else [],
                                             width=15, state="readonly")
        self.lsi_taxon_combo.grid(row=0, column=1, sticky='ew', padx=(0, 5))
        self.lsi_taxon_combo.bind('<<ComboboxSelected>>', self._on_taxon_selected)

        ttk.Label(cfg, text="Reference:", font=("Arial", 9, "bold")).grid(row=0, column=2, sticky='w', padx=(0, 2))
        self.lsi_ref_var = tk.StringVar()
        self.lsi_ref_combo = ttk.Combobox(cfg, textvariable=self.lsi_ref_var, width=15, state="readonly")
        self.lsi_ref_combo.grid(row=0, column=3, sticky='ew', padx=(0, 5))
        self.lsi_ref_combo.bind('<<ComboboxSelected>>', self._on_reference_selected)

        ttk.Label(cfg, text="Element:", font=("Arial", 9, "bold")).grid(row=0, column=4, sticky='w', padx=(0, 2))
        self.lsi_element_var = tk.StringVar()
        self.lsi_element_combo = ttk.Combobox(cfg, textvariable=self.lsi_element_var, width=12, state="readonly")
        self.lsi_element_combo.grid(row=0, column=5, sticky='ew', padx=(0, 5))
        self.lsi_element_combo.bind('<<ComboboxSelected>>', self._on_element_selected)

        ttk.Label(cfg, text="Condense:").grid(row=0, column=6, sticky='w', padx=(0, 2))
        self.lsi_condense_var = tk.StringVar(value="Priority")
        ttk.Combobox(cfg, textvariable=self.lsi_condense_var,
                     values=["Priority", "Average"], width=9, state="readonly"
                     ).grid(row=0, column=7, padx=(0, 0))

        self.ref_metadata = ttk.Label(parent, text="", font=("Arial", 7, "italic"), foreground="gray")
        self.ref_metadata.pack(anchor='w', padx=10, pady=(0, 4))

        body = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        body.pack(fill=tk.BOTH, expand=True, padx=8, pady=2)

        left_pane  = ttk.Frame(body)
        right_pane = ttk.Frame(body)
        body.add(left_pane,  weight=55)
        body.add(right_pane, weight=45)

        tree_lf = ttk.LabelFrame(left_pane,
                                  text="Reference measurements  (values auto-read from Biometrics tab)",
                                  padding=3)
        tree_lf.pack(fill=tk.BOTH, expand=True)

        cols = ("axis", "specimen", "reference", "lsi", "flag")
        self.lsi_tree = ttk.Treeview(tree_lf, columns=cols, show="tree headings", height=18)
        self.lsi_tree.heading("#0",        text="Code",           anchor='w')
        self.lsi_tree.heading("axis",      text="Axis",           anchor='center')
        self.lsi_tree.heading("specimen",  text="Specimen (mm)",  anchor='center')
        self.lsi_tree.heading("reference", text="Reference (mm)", anchor='center')
        self.lsi_tree.heading("lsi",       text="LSI",            anchor='center')
        self.lsi_tree.heading("flag",      text="",               anchor='center')
        self.lsi_tree.column("#0",        width=55,  anchor='w',      stretch=False)
        self.lsi_tree.column("axis",      width=58,  anchor='center', stretch=False)
        self.lsi_tree.column("specimen",  width=110, anchor='center')
        self.lsi_tree.column("reference", width=110, anchor='center')
        self.lsi_tree.column("lsi",       width=80,  anchor='center', stretch=False)
        self.lsi_tree.column("flag",      width=28,  anchor='center', stretch=False)

        tree_sb = ttk.Scrollbar(tree_lf, orient="vertical", command=self.lsi_tree.yview)
        self.lsi_tree.configure(yscrollcommand=tree_sb.set)
        self.lsi_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.lsi_tree.tag_configure("positive",    foreground="#1a7a3c")
        self.lsi_tree.tag_configure("negative",    foreground="#c0392b")
        self.lsi_tree.tag_configure("near_zero",   foreground="#555")
        self.lsi_tree.tag_configure("no_specimen", foreground="#bbb")
        self.lsi_tree.tag_configure("sel_length",  background="#d5f5e3")
        self.lsi_tree.tag_configure("sel_width",   background="#d6eaf8")
        self.lsi_tree.tag_configure("sel_depth",   background="#fdebd0")

        cond_lf = ttk.LabelFrame(right_pane,
                                  text="CondenseLogs — one summary value per axis",
                                  padding=8)
        cond_lf.pack(fill=tk.X, pady=(0, 6))

        AXIS_COLORS = {"Length": "#1a7a3c", "Width": "#2471a3", "Depth": "#ca6f1e"}
        self.condense_labels = {}
        for axis, color in AXIS_COLORS.items():
            row = ttk.Frame(cond_lf)
            row.pack(fill=tk.X, pady=3)
            tk.Label(row, text=f"{axis}", font=("Arial", 9, "bold"),
                     fg=color, width=7, anchor='w').pack(side=tk.LEFT)
            lbl = tk.Label(row, text="—", font=("Courier", 9), anchor='w',
                           fg="#2c3e50", bg="#f8f9fa", relief=tk.SUNKEN, padx=6)
            lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.condense_labels[axis] = lbl

        prio_lf = ttk.LabelFrame(right_pane, text="Priority Order (zoolog default)", padding=5)
        prio_lf.pack(fill=tk.X, pady=(0, 6))
        for line in [
            "Length:  GL > GLl > GLm > GLc > HTC",
            "Width:   BT > Bd > Bp > SD > Bfd > Bfp",
            "Depth:   Dd > DD > BG > Dp",
        ]:
            ttk.Label(prio_lf, text=line, font=("Courier", 8), foreground="#555").pack(anchor='w')
        ttk.Label(prio_lf,
                  text="★ Highlighted rows = selected condensed value",
                  font=("Arial", 7, "italic"), foreground="gray").pack(anchor='w', pady=(4, 0))

        if HAS_MPL:
            chart_lf = ttk.LabelFrame(right_pane, text="LSI Chart", padding=3)
            chart_lf.pack(fill=tk.BOTH, expand=True, pady=(0, 4))
            self.lsi_fig = Figure(figsize=(3.6, 3.0), dpi=90)
            self.lsi_ax  = self.lsi_fig.add_subplot(111)
            self.lsi_fig.patch.set_facecolor('#f8f9fa')
            self.lsi_canvas_widget = FigureCanvasTkAgg(self.lsi_fig, chart_lf)
            self.lsi_canvas_widget.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        else:
            ttk.Label(right_pane, text="Install matplotlib for charts",
                      foreground="gray").pack(pady=20)

        btn_bar = ttk.Frame(parent)
        btn_bar.pack(fill=tk.X, padx=8, pady=(2, 6))

        ttk.Button(btn_bar, text="⚡  CALCULATE LSI",
                   command=self._calculate_lsi_zoolog).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(btn_bar, text="📋 Copy Results",
                   command=self._copy_lsi_results).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_bar, text="💾 Export CSV",
                   command=self._export_lsi_csv).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_bar, text="🔄 Refresh",
                   command=self._refresh_lsi_data).pack(side=tk.LEFT, padx=2)

        self.lsi_status_label = ttk.Label(
            btn_bar,
            text="Select taxon + reference, then click CALCULATE LSI",
            font=("Arial", 7), foreground="gray")
        self.lsi_status_label.pack(side=tk.LEFT, padx=10)

    def _build_batch_tab(self, parent):
        ctrl = ttk.Frame(parent)
        ctrl.pack(fill=tk.X, padx=8, pady=6)

        ctrl.columnconfigure(1, weight=2)
        ctrl.columnconfigure(3, weight=2)
        ctrl.columnconfigure(5, weight=1)
        ctrl.columnconfigure(7, weight=1)

        current_col = 0

        ttk.Label(ctrl, text="Taxon:", font=("Arial", 8, "bold")).grid(
            row=0, column=current_col, sticky='w', padx=(0, 2))
        current_col += 1

        self.batch_taxon_var = tk.StringVar()
        self.batch_taxon_combo = ttk.Combobox(ctrl, textvariable=self.batch_taxon_var,
                                               values=sorted(self.taxon_references.keys()) if self.taxon_references else [],
                                               width=14, state="readonly")
        self.batch_taxon_combo.grid(row=0, column=current_col, padx=(0, 8), sticky='ew')
        self.batch_taxon_combo.bind('<<ComboboxSelected>>', self._on_batch_taxon_selected)
        current_col += 1

        ttk.Label(ctrl, text="Ref:", font=("Arial", 8, "bold")).grid(
            row=0, column=current_col, sticky='w', padx=(0, 2))
        current_col += 1

        self.batch_ref_var = tk.StringVar()
        self.batch_ref_combo = ttk.Combobox(ctrl, textvariable=self.batch_ref_var,
                                             width=14, state="readonly")
        self.batch_ref_combo.grid(row=0, column=current_col, padx=(0, 8), sticky='ew')
        self.batch_ref_combo.bind('<<ComboboxSelected>>', self._on_batch_ref_selected)
        current_col += 1

        ttk.Label(ctrl, text="Condense:", font=("Arial", 8, "bold")).grid(
            row=0, column=current_col, sticky='w', padx=(0, 2))
        current_col += 1

        self.batch_condense_var = tk.StringVar(value="Priority")
        ttk.Combobox(ctrl, textvariable=self.batch_condense_var,
                     values=["Priority", "Average"], width=8, state="readonly"
                     ).grid(row=0, column=current_col, padx=(0, 8), sticky='ew')
        current_col += 1

        ttk.Label(ctrl, text="Group:", font=("Arial", 8, "bold")).grid(
            row=0, column=current_col, sticky='w', padx=(0, 2))
        current_col += 1

        self.batch_group_var = tk.StringVar(value="(none)")
        self.batch_group_combo = ttk.Combobox(ctrl, textvariable=self.batch_group_var, width=10)
        self.batch_group_combo.grid(row=0, column=current_col, padx=0, sticky='ew')

        self.batch_ref_meta_label = ttk.Label(parent, text="", font=("Arial", 7, "italic"), foreground="gray")
        self.batch_ref_meta_label.pack(anchor='w', padx=10)

        abf = ttk.Frame(parent)
        abf.pack(fill=tk.X, padx=8, pady=(2, 4))
        ttk.Button(abf, text="🔢 Calculate All (LogRatios)", width=24,
                   command=self._calculate_lsi_batch).pack(side=tk.LEFT, padx=2)
        ttk.Button(abf, text="📈 Plot Distribution", width=18,
                   command=self._plot_batch_lsi).pack(side=tk.LEFT, padx=2)
        ttk.Button(abf, text="💾 Export CSV", width=14,
                   command=self._export_lsi_batch).pack(side=tk.LEFT, padx=2)
        self.batch_status_label = ttk.Label(abf, text="", font=("Arial", 8), foreground="#1a7a1a")
        self.batch_status_label.pack(side=tk.LEFT, padx=10)

        tbl_lf = ttk.LabelFrame(parent,
                                  text="Batch Results — CondenseLogs (one Length · Width · Depth per specimen)",
                                  padding=3)
        tbl_lf.pack(fill=tk.BOTH, expand=True, padx=8, pady=2)

        bcols = ("ID", "Taxon", "Element", "Group", "Length", "Width", "Depth", "N")
        self.batch_tree = ttk.Treeview(tbl_lf, columns=bcols, show='headings', height=10)
        bwidths = (45, 140, 110, 90, 75, 75, 75, 40)
        for col, w in zip(bcols, bwidths):
            self.batch_tree.heading(col, text=col)
            self.batch_tree.column(col, width=w, anchor='center')
        vsb = ttk.Scrollbar(tbl_lf, orient="vertical",   command=self.batch_tree.yview)
        hsb = ttk.Scrollbar(tbl_lf, orient="horizontal", command=self.batch_tree.xview)
        self.batch_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.batch_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        tbl_lf.rowconfigure(0, weight=1)
        tbl_lf.columnconfigure(0, weight=1)

        self.batch_summary_text = tk.Text(parent, height=3, font=("Courier", 7),
                                           wrap=tk.WORD, state=tk.DISABLED)
        self.batch_summary_text.pack(fill=tk.X, padx=8, pady=(2, 4))

        self._refresh_batch_group_options()

    # ============================================================================
    # THESAURUS-BASED NORMALIZATION
    # ============================================================================

    def _normalize_taxon(self, raw_taxon):
        if not raw_taxon or not hasattr(self, 'taxon_thesaurus'):
            return raw_taxon
        raw_lower = raw_taxon.lower().strip()
        if raw_lower in self.taxon_thesaurus:
            return self.taxon_thesaurus[raw_lower]
        for variant, standard in self.taxon_thesaurus.items():
            if variant in raw_lower or raw_lower in variant:
                return standard
        return raw_taxon

    def _normalize_element(self, raw_element):
        if not raw_element or not hasattr(self, 'element_thesaurus'):
            return raw_element
        return self.element_thesaurus.get(raw_element.lower().strip(), raw_element)

    def _normalize_measurement(self, raw_code):
        if not raw_code or not hasattr(self, 'measure_thesaurus'):
            return raw_code
        return self.measure_thesaurus.get(raw_code, raw_code)

    def _get_taxonomic_info(self, species):
        if not hasattr(self, 'taxonomy'):
            return {}
        return self.taxonomy.get(species, {})

    # ============================================================================
    # EXAMPLE SPECIMEN LOADER
    # ============================================================================

    def _load_example_specimen(self):
        if not self.example_specimens:
            self.set_status("⚠️ No example specimens available", "warning")
            return

        import random
        example = random.choice(self.example_specimens)

        taxon_code = example.get('taxon_code', '')
        taxon_name = self._normalize_taxon(taxon_code)
        if taxon_name == taxon_code and taxon_code:
            taxon_map = {
                'bota': 'Bos taurus', 'ovar': 'Ovis aries', 'cahi': 'Capra hircus',
                'sudo': 'Sus domesticus', 'ceel': 'Cervus elaphus', 'oc': 'Ovis/Capra'
            }
            taxon_name = taxon_map.get(taxon_code, taxon_code)

        element_code = example.get('element', '')
        element_name = self._normalize_element(element_code)

        sample = {
            'Sample_ID': f"{example.get('site', '')}-{example.get('inv_n', '')}",
            'taxon': taxon_name, 'element': element_name,
            'side': example.get('lateral', ''), 'portion': example.get('fragment', ''),
            'fusion': example.get('epiphysis', ''), 'sex': example.get('sex', ''),
            'context': example.get('ue', ''), 'period': example.get('period', ''),
        }

        measurements = example.get('measurements', {})
        for code, value in measurements.items():
            std_code = self._normalize_measurement(code)
            sample[std_code] = value

        if hasattr(self, 'samples') and hasattr(self.app, 'data_hub'):
            self.app.data_hub.add_row(sample)
            self._update_ui()
            if self.specimen_list.size() > 0:
                self.specimen_list.selection_set(self.specimen_list.size() - 1)
                self._on_specimen_selected()
            self.set_status(f"✅ Loaded example: {sample['Sample_ID']} ({taxon_name})", "success")
        else:
            msg = f"Example: {sample['Sample_ID']} - {taxon_name} - {element_name}\n"
            msg += f"Measurements: {len(measurements)}"
            messagebox.showinfo("Example Specimen", msg)

    # ============================================================================
    # LSI METHODS
    # ============================================================================

    def _ensure_database_loaded(self):
        if not self.taxon_references:
            self._load_unified_database()
        return bool(self.taxon_references)

    def _on_taxon_selected(self, event=None):
        taxon = self.lsi_taxon_var.get()
        if not taxon or taxon not in self.taxon_references:
            return
        refs = self.taxon_references[taxon]
        self.lsi_ref_combo['values'] = refs
        if refs:
            self.lsi_ref_combo.set(refs[0])
            self._on_reference_selected()

    def _on_reference_selected(self, event=None):
        taxon = self.lsi_taxon_var.get()
        ref   = self.lsi_ref_var.get()
        if not taxon or not ref or taxon not in self.reference_standards:
            return
        ref_data = self.reference_standards[taxon].get(ref, {})
        available_elements = sorted(ref_data.keys())
        self.lsi_element_combo['values'] = available_elements
        if available_elements:
            self.lsi_element_combo.set(available_elements[0])
            self._on_element_selected()
        if hasattr(self, 'ref_metadata') and self.full_db:
            raw_ref  = self.full_db.get('references', {}).get(ref, {})
            citation = raw_ref.get('citation', {})
            if isinstance(citation, dict):
                src = citation.get('source_text', '')
                sci = citation.get('taxon_scientific', taxon)
                self.ref_metadata.config(text=f"{sci} — {src[:80]}" if src else sci)
            else:
                self.ref_metadata.config(text=taxon)

    def _on_element_selected(self, event=None):
        pass

    def _get_axis(self, code):
        cu = code.upper()
        for axis, codes in self._AXIS_PRIORITY.items():
            if cu in [c.upper() for c in codes]:
                return axis
        return 'Width'

    def _calculate_lsi_zoolog(self):
        if self.current_specimen_idx is None:
            messagebox.showwarning("Warning", "Select a specimen first (in the specimen list)")
            return
        taxon    = self.lsi_taxon_var.get()
        ref_name = self.lsi_ref_var.get()
        element  = self.lsi_element_var.get()
        if not taxon or not ref_name:
            messagebox.showwarning("Warning", "Select taxon and reference standard first")
            return

        ref_elem_data = self.reference_standards.get(taxon, {}).get(ref_name, {})
        if element and element in ref_elem_data:
            ref_meas = ref_elem_data[element]
        else:
            ref_meas = {}
            for el_m in ref_elem_data.values():
                for mc, v in el_m.items():
                    if mc not in ref_meas:
                        ref_meas[mc] = v

        if not ref_meas:
            messagebox.showwarning("Warning",
                                   "No reference measurements found for this taxon/reference/element combo.")
            return

        spec_meas = {}
        for code, var in self.measurement_vars.items():
            raw = var.get().strip()
            if raw:
                try:
                    spec_meas[code] = float(raw)
                except ValueError:
                    pass

        for item in self.lsi_tree.get_children():
            self.lsi_tree.delete(item)

        lsi_vals   = {}
        axis_order = {'Length': 0, 'Width': 1, 'Depth': 2}
        sorted_codes = sorted(ref_meas.keys(),
                              key=lambda c: (axis_order.get(self._get_axis(c), 3), c))

        for code in sorted_codes:
            ref_v  = ref_meas[code]
            spec_v = spec_meas.get(code)
            axis   = self._get_axis(code)

            if spec_v is not None and ref_v and ref_v > 0:
                try:
                    lsi  = math.log10(spec_v / ref_v)
                    lsi_vals[code] = lsi
                    sign = "+" if lsi >= 0 else ""
                    tag  = ("positive" if lsi > 0.001 else "negative" if lsi < -0.001 else "near_zero")
                    self.lsi_tree.insert("", tk.END, text=code,
                        values=(axis, f"{spec_v:.2f}", f"{ref_v:.2f}", f"{sign}{lsi:.4f}", "✓"),
                        tags=(tag,))
                except (ValueError, ZeroDivisionError):
                    self.lsi_tree.insert("", tk.END, text=code,
                        values=(axis, f"{spec_v:.2f}", f"{ref_v:.2f}", "err", ""),
                        tags=("no_specimen",))
            else:
                spec_str = f"{spec_v:.2f}" if spec_v is not None else "—"
                self.lsi_tree.insert("", tk.END, text=code,
                    values=(axis, spec_str, f"{ref_v:.2f}", "—", ""),
                    tags=("no_specimen",))

        if not lsi_vals:
            msg = ("⚠  No measurements match reference codes.\n\n"
                   "Make sure you have entered measurements\n"
                   "in the Biometrics tab, using Von den Driesch\n"
                   "codes (GL, Bd, Bp, SD, etc.) as column names.")
            if hasattr(self, 'lsi_status_label'):
                self.lsi_status_label.config(text="⚠ No matching measurements", foreground="red")
            self.lsi_indicator.config(text="No data")
            messagebox.showinfo("No Data", msg)
            return

        method = getattr(self, 'lsi_condense_var', None)
        condense_method = method.get() if method else "Priority"
        condensed = {}
        sel_tag = {"Length": "sel_length", "Width": "sel_width", "Depth": "sel_depth"}

        for axis, priority in self._AXIS_PRIORITY.items():
            axis_vals = {c: v for c, v in lsi_vals.items() if self._get_axis(c) == axis}
            if not axis_vals:
                condensed[axis] = None
                continue
            if condense_method == "Priority":
                selected = None
                for pc in priority:
                    if pc in axis_vals:
                        selected = (pc, axis_vals[pc])
                        break
                if selected is None:
                    fb = sorted(axis_vals.keys())[0]
                    selected = (fb, axis_vals[fb])
            else:
                avg = sum(axis_vals.values()) / len(axis_vals)
                selected = (f"avg(n={len(axis_vals)})", avg)
            condensed[axis] = selected

        summary_parts = []
        for axis, result in condensed.items():
            lbl = self.condense_labels[axis]
            if result is None:
                lbl.config(text="— (no measurements)", fg="#bbb")
            else:
                code_lbl, val = result
                sign = "+" if val >= 0 else ""
                lbl.config(text=f"{code_lbl:10}  {sign}{val:.4f}", fg="#2c3e50")
                summary_parts.append(f"{axis[:3]}: {sign}{val:.4f}")
                for item in self.lsi_tree.get_children():
                    if self.lsi_tree.item(item, "text") == code_lbl:
                        existing = list(self.lsi_tree.item(item, "tags"))
                        self.lsi_tree.item(item, tags=existing + [sel_tag[axis]])
                        self.lsi_tree.see(item)

        if summary_parts:
            self.lsi_indicator.config(text="  ".join(summary_parts))
            self.measurement_status.config(
                text=f"LSI: {taxon} — {ref_name}  ({len(lsi_vals)} meas)",
                foreground="#1a7a3c")

        n_ref  = len(ref_meas)
        n_calc = len(lsi_vals)
        n_miss = n_ref - n_calc
        miss_note = f"  ({n_miss} codes have no specimen value)" if n_miss else ""
        if hasattr(self, 'lsi_status_label'):
            self.lsi_status_label.config(
                text=f"✓  {n_calc}/{n_ref} measurements computed  |  {condense_method}{miss_note}",
                foreground="#1a7a3c")

        self._last_lsi_results  = lsi_vals
        self._last_lsi_condensed = condensed
        self._last_lsi_ref      = (taxon, ref_name, element)

        if HAS_MPL and hasattr(self, 'lsi_ax'):
            self._plot_lsi_chart(lsi_vals, condensed)

    def _plot_lsi_chart(self, lsi_vals, condensed):
        ax = self.lsi_ax
        ax.clear()
        if not lsi_vals:
            self.lsi_canvas_widget.draw()
            return

        AXIS_COLOR = {"Length": "#1a7a3c", "Width": "#2471a3", "Depth": "#ca6f1e"}
        codes, values, colors = [], [], []
        for code in sorted(lsi_vals.keys(),
                           key=lambda c: ({"Length": 0, "Width": 1, "Depth": 2}.get(self._get_axis(c), 3), c)):
            codes.append(code)
            values.append(lsi_vals[code])
            colors.append(AXIS_COLOR.get(self._get_axis(code), "#7f8c8d"))

        xs = range(len(codes))
        ax.bar(xs, values, color=colors, alpha=0.8, edgecolor='white', linewidth=0.5)
        ax.axhline(0, color='#2c3e50', linewidth=1.2, linestyle='-')

        for axis, result in condensed.items():
            if result:
                sel_code = result[0]
                if sel_code in codes:
                    i = codes.index(sel_code)
                    ax.bar([i], [values[i]], color=AXIS_COLOR.get(axis, '#555'),
                           alpha=1.0, edgecolor='black', linewidth=1.5)

        ax.set_xticks(list(xs))
        ax.set_xticklabels(codes, rotation=45, ha='right', fontsize=7)
        ax.set_ylabel("LSI  (log₁₀)", fontsize=8)
        ax.tick_params(axis='y', labelsize=7)
        ax.set_facecolor('#f8f9fa')
        self.lsi_fig.tight_layout()
        self.lsi_canvas_widget.draw()

    def _copy_lsi_results(self):
        if not hasattr(self, '_last_lsi_condensed') or not self._last_lsi_condensed:
            messagebox.showinfo("Nothing to copy", "Run CALCULATE LSI first.")
            return
        lines = []
        taxon, ref, elem = getattr(self, '_last_lsi_ref', ('?', '?', '?'))
        lines.append(f"LSI Results — {taxon} / {ref} / {elem}")
        lines.append("-" * 50)
        lines.append("CondenseLogs (one value per axis):")
        for axis, result in self._last_lsi_condensed.items():
            if result:
                code_lbl, val = result
                sign = "+" if val >= 0 else ""
                lines.append(f"  {axis:<8} {code_lbl:<12} {sign}{val:.4f}")
            else:
                lines.append(f"  {axis:<8} —")
        lines.append("")
        lines.append("All measurements:")
        for code, val in sorted(self._last_lsi_results.items()):
            sign = "+" if val >= 0 else ""
            lines.append(f"  {code:<6} {sign}{val:.4f}")
        text = "\n".join(lines)
        self.lsi_frame.clipboard_clear()
        self.lsi_frame.clipboard_append(text)
        if hasattr(self, 'lsi_status_label'):
            self.lsi_status_label.config(text="✓ Results copied to clipboard", foreground="#1a7a3c")

    def _export_lsi_csv(self):
        if not hasattr(self, '_last_lsi_results') or not self._last_lsi_results:
            messagebox.showinfo("Nothing to export", "Run CALCULATE LSI first.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV", "*.csv")],
            initialfile="lsi_results.csv")
        if not path:
            return
        try:
            taxon, ref, elem = getattr(self, '_last_lsi_ref', ('?', '?', '?'))
            spec_id = ""
            if self.current_specimen_idx is not None and self.current_specimen_idx < len(self.samples):
                spec_id = self.samples[self.current_specimen_idx].get('Sample_ID', '')
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Sample_ID", "Taxon", "Reference", "Element",
                                 "Code", "Axis", "Specimen_mm", "Reference_mm", "LSI",
                                 "Condensed_Length", "Condensed_Width", "Condensed_Depth"])
                cond = getattr(self, '_last_lsi_condensed', {})
                cl = cond.get('Length', (None, None))
                cw = cond.get('Width',  (None, None))
                cd = cond.get('Depth',  (None, None))
                for code, lsi in sorted(self._last_lsi_results.items()):
                    axis   = self._get_axis(code)
                    spec_v = self.measurement_vars.get(code, tk.StringVar()).get()
                    ref_data = self.reference_standards.get(taxon, {}).get(ref, {})
                    ref_meas = {}
                    if elem and elem in ref_data:
                        ref_meas = ref_data[elem]
                    else:
                        for el_m in ref_data.values():
                            for mc, v in el_m.items():
                                if mc not in ref_meas:
                                    ref_meas[mc] = v
                    ref_v = ref_meas.get(code, "")
                    writer.writerow([
                        spec_id, taxon, ref, elem or "all", code, axis, spec_v, ref_v,
                        f"{lsi:.6f}",
                        f"{cl[1]:.6f}" if cl and cl[1] is not None else "",
                        f"{cw[1]:.6f}" if cw and cw[1] is not None else "",
                        f"{cd[1]:.6f}" if cd and cd[1] is not None else "",
                    ])
            messagebox.showinfo("Exported", f"LSI results saved to:\n{path}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def _refresh_lsi_data(self):
        spec_info = ""
        if self.current_specimen_idx is not None and self.current_specimen_idx < len(self.samples):
            s = self.samples[self.current_specimen_idx]
            spec_info = (f"  ·  Specimen: {s.get('Sample_ID', '—')}"
                         f"  |  {s.get('taxon', '—')}"
                         f"  |  {s.get('element', '—')}")
        if hasattr(self, 'lsi_header_label'):
            self.lsi_header_label.config(
                text=f"📊 Log Size Index (LSI) Calculator — zoolog methodology{spec_info}")
        self._auto_select_from_specimen()
        if hasattr(self, 'lsi_taxon_var') and self.lsi_taxon_var.get() and \
           hasattr(self, 'lsi_ref_var') and self.lsi_ref_var.get():
            self._calculate_lsi_zoolog()

    def _auto_select_from_specimen(self):
        if self.current_specimen_idx is None:
            return
        if self.current_specimen_idx >= len(self.samples):
            return
        sample    = self.samples[self.current_specimen_idx]
        raw_taxon = (sample.get('taxon') or sample.get('species') or '').lower()
        normalized = self._normalize_taxon(raw_taxon)
        if normalized != raw_taxon:
            for db_taxon in self.taxon_references.keys():
                if normalized in db_taxon or db_taxon.lower() in normalized.lower():
                    if hasattr(self, 'lsi_taxon_var'):
                        self.lsi_taxon_var.set(db_taxon)
                        self._on_taxon_selected()
                    if hasattr(self, 'batch_taxon_var'):
                        self.batch_taxon_var.set(db_taxon)
                        self._on_batch_taxon_selected()
                    return
        for db_taxon in self.taxon_references.keys():
            if raw_taxon in db_taxon.lower() or db_taxon.lower() in raw_taxon:
                if hasattr(self, 'lsi_taxon_var'):
                    self.lsi_taxon_var.set(db_taxon)
                    self._on_taxon_selected()
                if hasattr(self, 'batch_taxon_var'):
                    self.batch_taxon_var.set(db_taxon)
                    self._on_batch_taxon_selected()
                break

    def _refresh_batch_group_options(self):
        if not hasattr(self, 'batch_group_combo'):
            return
        options = ["(none)"]
        if self.samples:
            all_keys = set()
            for s in self.samples:
                all_keys.update(s.keys())
            meas_codes_lower = {c.lower() for c in MEASUREMENT_CODES.keys()}
            skip = meas_codes_lower | {'id', 'row', 'index', 'notes', 'comment', 'remarks',
                                        'sample_id', 'log'}
            options += sorted(k for k in all_keys if k.lower() not in skip)
        self.batch_group_combo['values'] = options
        if self.batch_group_var.get() not in options:
            self.batch_group_var.set("(none)")

    def _on_batch_taxon_selected(self, event=None):
        if not hasattr(self, 'batch_taxon_var'):
            return
        taxon = self.batch_taxon_var.get()
        if not taxon or taxon not in self.taxon_references:
            return
        refs = self.taxon_references[taxon]
        if hasattr(self, 'batch_ref_combo'):
            self.batch_ref_combo['values'] = refs
            if refs:
                self.batch_ref_combo.set(refs[0])
                self._on_batch_ref_selected()

    def _on_batch_ref_selected(self, event=None):
        if not (hasattr(self, 'batch_taxon_var') and hasattr(self, 'batch_ref_var')):
            return
        taxon = self.batch_taxon_var.get()
        ref   = self.batch_ref_var.get()
        if hasattr(self, 'batch_ref_meta_label') and self.full_db and taxon and ref:
            raw = self.full_db.get('references', {}).get(ref, {})
            cit = raw.get('citation', {})
            if isinstance(cit, dict):
                src = cit.get('source_text', '')
                sci = cit.get('taxon_scientific', taxon)
                self.batch_ref_meta_label.config(text=f"{sci} — {src[:90]}" if src else sci)
            else:
                self.batch_ref_meta_label.config(text=taxon)

    def _calculate_lsi_batch(self):
        if not hasattr(self, 'batch_taxon_var'):
            return
        taxon_sel = self.batch_taxon_var.get()
        ref_sel   = self.batch_ref_var.get()
        if not taxon_sel or not ref_sel:
            messagebox.showwarning("Batch LSI", "Select Taxon and Reference Standard first.")
            return
        if not self.samples:
            messagebox.showwarning("Batch LSI", "No specimens loaded.")
            return

        ref_elem_data = self.reference_standards.get(taxon_sel, {}).get(ref_sel, {})
        flat_ref = {}
        for el_measures in ref_elem_data.values():
            for mcode, val in el_measures.items():
                if mcode not in flat_ref:
                    flat_ref[mcode] = float(val)

        if not flat_ref:
            messagebox.showerror("Batch LSI",
                                  f"No reference measurements found for {taxon_sel} / {ref_sel}.")
            return

        condense_method = self.batch_condense_var.get()
        group_col = self.batch_group_var.get()
        if group_col == "(none)":
            group_col = None

        self._refresh_batch_group_options()

        def taxon_match(sp_taxon):
            if not sp_taxon:
                return False
            st = sp_taxon.lower()
            tt = taxon_sel.lower()
            return (tt in st) or (st in tt)

        results = []
        n_proc = n_skip = 0

        for i, sample in enumerate(self.samples):
            sp_taxon = sample.get('taxon') or sample.get('species') or ''
            if not taxon_match(sp_taxon):
                n_skip += 1
                continue

            lsi_vals = {}
            for code, ref_val in flat_ref.items():
                raw = sample.get(code, '')
                if raw == '' or raw is None:
                    continue
                try:
                    meas = float(raw)
                    lsi_vals[code] = math.log10(meas / ref_val)
                except (ValueError, ZeroDivisionError):
                    continue

            if not lsi_vals:
                n_skip += 1
                continue

            condensed = {}
            for axis, priority_list in self._AXIS_PRIORITY.items():
                axis_codes  = [c for c in priority_list if c in lsi_vals]
                other_codes = [c for c in lsi_vals
                               if c not in priority_list and self._get_axis(c) == axis]
                all_axis = axis_codes + other_codes
                if not all_axis:
                    condensed[axis] = None
                    continue
                if condense_method == "Priority":
                    condensed[axis] = lsi_vals[all_axis[0]]
                else:
                    vals = [lsi_vals[c] for c in all_axis]
                    condensed[axis] = sum(vals) / len(vals)

            results.append({
                'idx': i, 'taxon': sp_taxon,
                'element': sample.get('element') or sample.get('bone') or '',
                'group': str(sample.get(group_col, '')) if group_col else '',
                'Length': condensed.get('Length'), 'Width': condensed.get('Width'),
                'Depth': condensed.get('Depth'), 'n_meas': len(lsi_vals),
                'all_lsi': lsi_vals,
            })
            n_proc += 1

        self._batch_lsi_results = results

        for item in self.batch_tree.get_children():
            self.batch_tree.delete(item)

        def fmt(v):
            return f"{v:+.4f}" if v is not None else "—"

        for row in results:
            self.batch_tree.insert('', tk.END, values=(
                row['idx'] + 1, row['taxon'][:20], row['element'][:15],
                str(row['group'])[:12], fmt(row['Length']), fmt(row['Width']),
                fmt(row['Depth']), row['n_meas'],
            ))

        def axis_stats(axis):
            vals = [r[axis] for r in results if r[axis] is not None]
            if not vals:
                return f"{axis}: — (n=0)"
            mean = sum(vals) / len(vals)
            sd   = (sum((v - mean)**2 for v in vals) / len(vals))**0.5 if len(vals) > 1 else 0.0
            return f"{axis}: mean={mean:+.4f}  SD={sd:.4f}  n={len(vals)}"

        summary = (
            f"Reference: {taxon_sel} / {ref_sel}   CondenseLogs: {condense_method}\n"
            f"Processed: {n_proc}  |  Skipped/no-match: {n_skip}\n"
            + "  ".join(axis_stats(ax) for ax in ('Length', 'Width', 'Depth'))
        )
        self.batch_summary_text.config(state=tk.NORMAL)
        self.batch_summary_text.delete(1.0, tk.END)
        self.batch_summary_text.insert(1.0, summary)
        self.batch_summary_text.config(state=tk.DISABLED)

        if hasattr(self, 'batch_status_label'):
            self.batch_status_label.config(
                text=f"✅ {n_proc} specimens processed", foreground="#1a7a1a")
        self.measurement_status.config(
            text=f"Batch LSI: {n_proc} specimens | {ref_sel}", foreground="#1a7a1a")

    def _plot_batch_lsi(self):
        if not self._batch_lsi_results:
            messagebox.showwarning("Plot", "Run 'Calculate All' first.")
            return
        if not HAS_MPL:
            messagebox.showerror("Plot", "matplotlib not installed.")
            return

        group_col  = self.batch_group_var.get() if hasattr(self, 'batch_group_var') else "(none)"
        use_groups = (group_col and group_col != "(none)"
                      and any(r['group'] for r in self._batch_lsi_results))

        axes_list = [ax for ax in ('Length', 'Width', 'Depth')
                     if any(r[ax] is not None for r in self._batch_lsi_results)]
        if not axes_list:
            messagebox.showinfo("Plot", "No condensed values to plot.")
            return

        import matplotlib.pyplot as plt
        import matplotlib.gridspec as gridspec

        fig = plt.figure(figsize=(5 * len(axes_list), 5))
        taxon_sel = self.batch_taxon_var.get() if hasattr(self, 'batch_taxon_var') else "?"
        ref_sel   = self.batch_ref_var.get() if hasattr(self, 'batch_ref_var') else "?"
        cond_meth = self.batch_condense_var.get() if hasattr(self, 'batch_condense_var') else "?"
        fig.suptitle(f"LSI Distribution  ·  {taxon_sel} / {ref_sel}  [{cond_meth}]",
                     fontsize=10, fontweight='bold')

        gs = gridspec.GridSpec(1, len(axes_list), figure=fig)
        AXIS_COLOR = {"Length": "#1a7a3c", "Width": "#2471a3", "Depth": "#ca6f1e"}

        for col_i, axis in enumerate(axes_list):
            ax = fig.add_subplot(gs[0, col_i])
            ax.axhline(0, color='#c0392b', linewidth=1.2, linestyle='--', alpha=0.7)

            if use_groups:
                groups = sorted(set(r['group'] for r in self._batch_lsi_results
                                    if r[axis] is not None and r['group']))
                data_by_g = {g: [r[axis] for r in self._batch_lsi_results
                                  if r[axis] is not None and r['group'] == g]
                             for g in groups}
                positions = list(range(1, len(groups) + 1))
                ax.boxplot([data_by_g[g] for g in groups], positions=positions,
                           notch=False, patch_artist=True,
                           boxprops=dict(facecolor=AXIS_COLOR.get(axis, '#ccc'), alpha=0.5),
                           medianprops=dict(color='#c0392b', linewidth=2))
                for pos, g in zip(positions, groups):
                    vals   = data_by_g[g]
                    jitter = [pos + (hash(str(v*1e6)) % 100 - 50) / 600 for v in vals]
                    ax.scatter(jitter, vals, alpha=0.55, s=18,
                               color=AXIS_COLOR.get(axis, '#555'), zorder=3)
                ax.set_xticks(positions)
                ax.set_xticklabels(groups, rotation=35, ha='right', fontsize=7)
                ax.set_xlabel(group_col, fontsize=8)
            else:
                vals = [r[axis] for r in self._batch_lsi_results if r[axis] is not None]
                ax.boxplot(vals, notch=False, patch_artist=True,
                           boxprops=dict(facecolor=AXIS_COLOR.get(axis, '#ccc'), alpha=0.5),
                           medianprops=dict(color='#c0392b', linewidth=2))
                jitter = [1 + (hash(str(v*1e6)) % 100 - 50) / 600 for v in vals]
                ax.scatter(jitter, vals, alpha=0.55, s=18,
                           color=AXIS_COLOR.get(axis, '#555'), zorder=3)
                ax.set_xticks([])
                ax.set_xlabel(f"n={len(vals)}", fontsize=8)

            ax.set_ylabel("LSI value (log₁₀)", fontsize=8)
            ax.set_title(axis, fontsize=9, fontweight='bold',
                         color=AXIS_COLOR.get(axis, '#2c3e50'))
            ax.grid(axis='y', linestyle=':', alpha=0.4)

        plt.tight_layout()
        plt.show()

    def _export_lsi_batch(self):
        if not self._batch_lsi_results:
            messagebox.showwarning("Export", "Run 'Calculate All' first.")
            return
        taxon_sel = self.batch_taxon_var.get() if hasattr(self, 'batch_taxon_var') else "batch"
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV", "*.csv")],
            initialfile=f"LSI_{taxon_sel.replace(' ', '_')}.csv")
        if not path:
            return
        try:
            all_codes = sorted(set(
                code for r in self._batch_lsi_results for code in r['all_lsi'].keys()))
            with open(path, 'w', newline='', encoding='utf-8') as f:
                fieldnames = (['Index', 'Taxon', 'Element', 'Group',
                                'Length', 'Width', 'Depth', 'N_measurements']
                               + [f"log{c}" for c in all_codes])
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for r in self._batch_lsi_results:
                    row = {
                        'Index': r['idx'] + 1, 'Taxon': r['taxon'],
                        'Element': r['element'], 'Group': r['group'],
                        'Length': f"{r['Length']:+.6f}" if r['Length'] is not None else '',
                        'Width':  f"{r['Width']:+.6f}"  if r['Width']  is not None else '',
                        'Depth':  f"{r['Depth']:+.6f}"  if r['Depth']  is not None else '',
                        'N_measurements': r['n_meas'],
                    }
                    for code in all_codes:
                        val = r['all_lsi'].get(code)
                        row[f"log{code}"] = f"{val:+.6f}" if val is not None else ''
                    writer.writerow(row)
            messagebox.showinfo("Export", f"Batch LSI results saved to:\n{path}")
            if hasattr(self, 'batch_status_label'):
                self.batch_status_label.config(
                    text=f"✅ Exported {len(self._batch_lsi_results)} rows")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    # ============================================================================
    # TAPHONOMY METHODS
    # ============================================================================

    def _load_taph_from_sample(self, sample):
        if hasattr(self, 'debug_taph') and self.debug_taph:
            print(f"\n--- Loading taphonomy from specimen ---")
            for key, value in sample.items():
                if any(x in key for x in ['weather','burn','butcher','gnaw','root','surface','frag','taph']):
                    print(f"  {key}: {value}")

        w = sample.get('weathering', sample.get('weathering_stage', -1))
        try:
            w = int(w)
            if w not in range(6):
                w = -1
        except (TypeError, ValueError):
            w = -1
        self.weather_var.set(w)

        burning = sample.get('burning_stage', '')
        if not burning:
            legacy = sample.get('burning', False)
            if str(legacy).lower() in ('true','1','yes','scorched'):
                burning = 'scorched'
            elif str(legacy).lower() in ('carbonised','carbonized','charred'):
                burning = 'carbonised'
            elif str(legacy).lower() in ('calcined','white','burnt'):
                burning = 'calcined'
            else:
                burning = 'none'
        if burning not in self._BURNING:
            burning = 'none'
        self.burning_var.set(burning)
        self.burn_var.set(burning != 'none')

        legacy_butchery = bool(sample.get('butchery', False))
        for key in self.butchery_vars:
            val = sample.get(key, False)
            if isinstance(val, str):
                val = val.lower() in ('true','1','yes','present')
            self.butchery_vars[key].set(bool(val))
        if legacy_butchery and not any(v.get() for v in self.butchery_vars.values()):
            self.butchery_vars['cut_marks'].set(True)
        self.butchery_var.set(any(v.get() for v in self.butchery_vars.values()))
        self.butchery_notes_var.set(sample.get('butchery_notes', ''))

        gnawing = sample.get('gnawing_type', sample.get('gnawing', ''))
        if isinstance(gnawing, bool) or str(gnawing).lower() in ('true','1','yes'):
            gnawing = 'carnivore'
        if gnawing not in ('none','carnivore','rodent','both'):
            gnawing = 'none'
        self.gnawing_var.set(gnawing)
        self.gnaw_var.set(gnawing != 'none')
        self.tooth_pits_var.set(bool(sample.get('tooth_pits', False)))

        for key in self.surf_mod_vars:
            val = sample.get(key, False)
            if isinstance(val, str):
                val = val.lower() in ('true','1','yes','present')
            self.surf_mod_vars[key].set(bool(val))
        if sample.get('root_etching', False):
            self.surf_mod_vars['root_etching'].set(True)
        self.root_var.set(self.surf_mod_vars['root_etching'].get())

        sq = sample.get('surface_preservation', sample.get('surf_qual', 0))
        try:
            sq = int(sq)
            if sq not in range(1, 6):
                sq = 0
        except (TypeError, ValueError):
            sq = 0
        self.surf_qual_var.set(sq)

        self.fragmentation_var.set(sample.get('fragmentation', sample.get('portion', '')))
        comp = sample.get('completeness', sample.get('completeness_pct', ''))
        self.completeness_var.set(str(comp) if comp else '')
        self.taph_notes_var.set(sample.get('taph_notes', sample.get('taphonomy_notes', '')))

        self._update_taph_summary()

    def _update_taph_summary(self):
        lines = []

        w = self.weather_var.get()
        if w in self._BEHRENSMEYER:
            label, desc, _ = self._BEHRENSMEYER[w]
            tag = "good" if w <= 1 else "warn" if w <= 3 else "bad"
            lines.append((f"Weathering: {label} — {desc}", tag))
        else:
            lines.append(("Weathering: not recorded", "neutral"))

        b = self.burning_var.get()
        if b != 'none':
            label, desc, _ = self._BURNING[b]
            lines.append((f"Burning: {label} — {desc}", "warn"))

        sq = self.surf_qual_var.get()
        if sq in self._SURF_QUAL:
            sq_label, sq_desc, _ = self._SURF_QUAL[sq]
            sq_tag = "good" if sq >= 4 else "warn" if sq >= 2 else "bad"
            lines.append((f"Surface quality: {sq_label} — {sq_desc}", sq_tag))

        active_butchery = [k for k, v in self.butchery_vars.items() if v.get()]
        if active_butchery:
            labels = {'cut_marks':'Cut marks','chop_marks':'Chop marks',
                      'percussion_marks':'Percussion marks','scraping_marks':'Scraping marks'}
            parts = [labels[k] for k in active_butchery]
            note  = self.butchery_notes_var.get().strip()
            txt   = "Butchery: " + ", ".join(parts)
            if note:
                txt += f"  [{note}]"
            lines.append((txt, "warn"))

        gnaw = self.gnawing_var.get()
        if gnaw != 'none':
            tp = "  + tooth pits" if self.tooth_pits_var.get() else ""
            gnaw_labels = {'carnivore':'Carnivore gnawing',
                           'rodent':'Rodent gnawing','both':'Carnivore & rodent gnawing'}
            lines.append((f"Gnawing: {gnaw_labels.get(gnaw, gnaw)}{tp}", "warn"))

        active_mods = [k for k, v in self.surf_mod_vars.items() if v.get()]
        if active_mods:
            mod_labels = {
                'root_etching':'Root etching','abrasion':'Abrasion','rounding':'Rounding',
                'bleaching':'Bleaching','manganese_staining':'Mn staining',
                'iron_staining':'Fe/ochre staining','trampling':'Trampling',
            }
            parts = [mod_labels.get(k, k) for k in active_mods]
            lines.append(("Surface mods: " + ", ".join(parts), "neutral"))

        frag = self.fragmentation_var.get()
        comp = self.completeness_var.get().strip()
        frag_parts = []
        if frag:
            frag_parts.append(frag)
        if comp:
            frag_parts.append(f"{comp}% complete")
        if frag_parts:
            lines.append(("Fragmentation: " + "  ·  ".join(frag_parts), "neutral"))

        note = self.taph_notes_var.get().strip()
        if note:
            lines.append((f"Notes: {note}", "neutral"))

        self.taph_summary_text.config(state=tk.NORMAL)
        self.taph_summary_text.delete(1.0, tk.END)
        if not lines:
            self.taph_summary_text.insert(tk.END, "No taphonomic data recorded.", "neutral")
        else:
            for i, (text, tag) in enumerate(lines):
                self.taph_summary_text.insert(tk.END, text, tag)
                if i < len(lines) - 1:
                    self.taph_summary_text.insert(tk.END, "\n")
        self.taph_summary_text.config(state=tk.DISABLED)

    # ============================================================================
    # UI METHODS
    # ============================================================================

    def _update_ui(self):
        self.specimen_list.delete(0, tk.END)
        indices = self.selected_indices if self.selected_indices else range(len(self.samples))
        for i in sorted(indices):
            if i >= len(self.samples):
                continue
            sample   = self.samples[i]
            sample_id = sample.get('Sample_ID', f"Spec{i}")
            taxon    = sample.get('taxon', '?')[:15]
            element  = sample.get('element', sample.get('bone', '?'))[:10]
            label    = f"{i:3d}: {sample_id[:10]:10} - {taxon:15} - {element:10}"
            self.specimen_list.insert(tk.END, label)
        if self.specimen_list.size() > 0:
            self.specimen_list.selection_set(0)
            self._on_specimen_selected()

    def _on_specimen_selected(self, event=None):
        selection = self.specimen_list.curselection()
        if not selection:
            return

        idx = selection[0]
        if self.selected_indices:
            actual_idx = list(sorted(self.selected_indices))[idx]
        else:
            actual_idx = idx

        self.current_specimen_idx = actual_idx
        if actual_idx >= len(self.samples):
            return

        sample = self.samples[actual_idx]

        self.specimen_summary.delete(1.0, tk.END)
        self.specimen_summary.insert(1.0,
            f"ID: {sample.get('Sample_ID', 'N/A')}\n"
            f"Taxon: {sample.get('taxon', 'Unknown')}\n"
            f"Element: {sample.get('element', 'Unknown')} ({sample.get('side', '')})"
        )

        # ── Age tab: set taxon, rebuild all 6 sections, load data ─────────────
        taxon_raw = sample.get('taxon', '')
        for t in ['Cattle','Sheep','Goat','Pig','Horse','Red Deer','Fallow Deer',
                  'Dog','Cat','Chicken','Goose','Duck','Other Bird','Fish','Other']:
            if t.lower() in taxon_raw.lower():
                self.age_taxon_var.set(t)
                self._on_age_taxon_changed()
                break

        # Fusion state + element
        fusion = sample.get('fusion', '')
        if hasattr(self, 'fusion_var'):
            self.fusion_var.set(fusion if fusion in FUSION_STAGES else '')
        fusion_elem = sample.get('fusion_element', '')
        if hasattr(self, 'fusion_element_var'):
            self.fusion_element_var.set(fusion_elem)
        self._update_fusion_interpretation()

        # Grant wear stages
        for tooth in ['dP4', 'P4', 'M1', 'M2', 'M3']:
            val = sample.get(f'grant_{tooth}', '')
            if tooth in self.grant_vars:
                self.grant_vars[tooth].set(str(val) if val else '—')

        # Pig wear
        if hasattr(self, '_pig_wear_var') and self._pig_wear_var is not None:
            self._pig_wear_var.set(sample.get('pig_wear_stage', ''))

        # Horse indicators
        if hasattr(self, '_horse_vars') and self._horse_vars:
            for key, var in self._horse_vars.items():
                var.set(bool(sample.get(f'horse_{key}', False)))

        # Dog wear
        if hasattr(self, '_dog_wear_var') and self._dog_wear_var is not None:
            self._dog_wear_var.set(sample.get('dog_wear_stage', '— not recorded'))

        # Eruption states (section 1)
        if hasattr(self, '_eruption_vars'):
            for tooth, var in self._eruption_vars.items():
                saved = sample.get(f'erupt_{tooth.replace("/","_")}', '— not observed')
                var.set(saved)
            self._on_eruption_changed()

        # Cementum
        if hasattr(self, '_cement_rings_var'):
            self._cement_rings_var.set(str(sample.get('cement_rings', '')))
            self._cement_season_var.set(sample.get('cement_season', ''))

        # Histology
        if hasattr(self, '_histo_age_var'):
            self._histo_age_var.set(str(sample.get('histo_age_yr', '')))
            self._histo_method_var.set(sample.get('histo_method', ''))
            self._histo_ref_var.set(sample.get('histo_ref', ''))

        # Gross morphology
        if hasattr(self, '_gross_morph_var'):
            morph_key   = sample.get('gross_morph', '')
            morph_label = self._GROSS_MORPH_LABELS.get(morph_key, '')
            self._gross_morph_var.set(morph_label)
            texture_key   = sample.get('bone_texture', '')
            texture_label = next((lbl for k, lbl in self._BONE_TEXTURE_OPTS if k == texture_key), '')
            self._bone_texture_var.set(texture_label)
            self._gross_notes_var.set(sample.get('gross_morph_notes', ''))

        # Taphonomy
        self._load_taph_from_sample(sample)

        # Measurements
        loaded = 0
        for code, var in self.measurement_vars.items():
            val = sample.get(code, '')
            if val:
                var.set(str(val))
                loaded += 1
            else:
                var.set('')
        self.measurement_status.config(text=f"Loaded {loaded} measurements")

        self._calculate_age_live()

        self.frame.update_idletasks()
        self.set_status(f"✅ Loaded specimen {actual_idx}", "success")

        if hasattr(self, 'lsi_header_label'):
            spec_info = (f"  ·  Specimen: {sample.get('Sample_ID', '—')}"
                         f"  |  {sample.get('taxon', '—')}"
                         f"  |  {sample.get('element', '—')}")
            self.lsi_header_label.config(
                text=f"📊 Log Size Index (LSI) Calculator — zoolog methodology{spec_info}")

        self._auto_select_from_specimen()

    def _prev_specimen(self):
        sel = self.specimen_list.curselection()
        if sel and sel[0] > 0:
            self.specimen_list.selection_clear(0, tk.END)
            self.specimen_list.selection_set(sel[0] - 1)
            self._on_specimen_selected()

    def _next_specimen(self):
        sel = self.specimen_list.curselection()
        if sel and sel[0] < self.specimen_list.size() - 1:
            self.specimen_list.selection_clear(0, tk.END)
            self.specimen_list.selection_set(sel[0] + 1)
            self._on_specimen_selected()

    def _save_to_specimen(self):
        if self.current_specimen_idx is None:
            self.set_status("⚠️ No specimen selected", "warning")
            return
        all_samples = self.app.data_hub.get_all()
        if self.current_specimen_idx >= len(all_samples):
            return
        updated = all_samples[self.current_specimen_idx].copy()

        # Measurements
        meas_count = 0
        for code, var in self.measurement_vars.items():
            val = var.get().strip()
            if val:
                try:
                    updated[code] = float(val)
                    meas_count += 1
                except ValueError:
                    updated[code] = val
                    meas_count += 1
            elif code in updated:
                del updated[code]

        # ── Age fields ────────────────────────────────────────────────────────
        # Fusion
        if hasattr(self, 'fusion_var') and self.fusion_var.get():
            updated['fusion'] = self.fusion_var.get()
        if hasattr(self, 'fusion_element_var') and self.fusion_element_var.get():
            updated['fusion_element'] = self.fusion_element_var.get()

        # Grant wear
        for tooth, var in self.grant_vars.items():
            val = var.get().strip()
            key = f'grant_{tooth}'
            if val and val != '—':
                updated[key] = val
            elif key in updated:
                del updated[key]

        mws_text = self.mws_score_label.cget('text')
        if mws_text not in ('—', '?', 'n/a', ''):
            try:
                updated['grant_mws'] = int(mws_text)
            except Exception:
                pass

        # Pig wear
        if hasattr(self, '_pig_wear_var') and self._pig_wear_var is not None:
            updated['pig_wear_stage'] = self._pig_wear_var.get()

        # Horse indicators
        if hasattr(self, '_horse_vars') and self._horse_vars:
            for key, var in self._horse_vars.items():
                updated[f'horse_{key}'] = var.get()

        # Dog wear
        if hasattr(self, '_dog_wear_var') and self._dog_wear_var is not None:
            updated['dog_wear_stage'] = self._dog_wear_var.get()

        # Eruption states
        if hasattr(self, '_eruption_vars'):
            for tooth, var in self._eruption_vars.items():
                updated[f'erupt_{tooth.replace("/","_")}'] = var.get()

        # Cementum
        if hasattr(self, '_cement_rings_var'):
            rings = self._cement_rings_var.get().strip()
            if rings:
                try:
                    updated['cement_rings'] = int(rings)
                except ValueError:
                    pass
            updated['cement_season'] = self._cement_season_var.get()

        # Histology
        if hasattr(self, '_histo_age_var'):
            h = self._histo_age_var.get().strip()
            if h:
                try:
                    updated['histo_age_yr'] = float(h)
                except ValueError:
                    pass
            updated['histo_method'] = self._histo_method_var.get()
            updated['histo_ref']    = self._histo_ref_var.get()

        # Gross morphology
        if hasattr(self, '_gross_morph_var'):
            morph_label = self._gross_morph_var.get()
            morph_key   = next(
                (k for k, v in self._GROSS_MORPH_LABELS.items() if v == morph_label), '')
            updated['gross_morph'] = morph_key
            texture_label = self._bone_texture_var.get()
            texture_key   = next(
                (k for k, v in self._BONE_TEXTURE_OPTS if v == texture_label), '')
            updated['bone_texture']      = texture_key
            updated['gross_morph_notes'] = self._gross_notes_var.get().strip()

        # ── Taphonomy ─────────────────────────────────────────────────────────
        updated['weathering']           = self.weather_var.get()
        updated['burning_stage']        = self.burning_var.get()
        updated['burning']              = (self.burning_var.get() != 'none')

        for key, var in self.butchery_vars.items():
            updated[key] = var.get()
        updated['butchery']             = any(v.get() for v in self.butchery_vars.values())
        updated['butchery_notes']       = self.butchery_notes_var.get().strip()

        updated['gnawing_type']         = self.gnawing_var.get()
        updated['gnawing']              = (self.gnawing_var.get() != 'none')
        updated['tooth_pits']           = self.tooth_pits_var.get()

        for key, var in self.surf_mod_vars.items():
            updated[key] = var.get()
        updated['root_etching']         = self.surf_mod_vars['root_etching'].get()

        updated['surface_preservation'] = self.surf_qual_var.get()
        updated['fragmentation']        = self.fragmentation_var.get()

        comp = self.completeness_var.get().strip()
        if comp:
            try:
                updated['completeness'] = float(comp)
            except ValueError:
                updated['completeness'] = comp
        elif 'completeness' in updated:
            del updated['completeness']

        updated['taph_notes'] = self.taph_notes_var.get().strip()

        try:
            self.app.data_hub.update_row(self.current_specimen_idx, updated)
            self.measurement_status.config(text=f"Saved {meas_count} measurements", foreground="green")
            self.set_status(f"✅ Saved specimen {self.current_specimen_idx}", "success")
        except Exception as e:
            self.set_status(f"❌ Save failed: {str(e)[:50]}", "error")

    def _clear_measurements(self):
        # Biometrics
        for var in self.measurement_vars.values():
            var.set("")

        # Age fields
        for var in self.grant_vars.values():
            var.set('')
        self.mws_score_label.config(text='—')
        self.payne_stage_label.config(text='—')
        self.age_estimate.config(text='—')
        self.grant_age_label.config(text='')

        if hasattr(self, 'fusion_var'):
            self.fusion_var.set('')
        if hasattr(self, 'fusion_element_var'):
            self.fusion_element_var.set('')

        if hasattr(self, '_pig_wear_var') and self._pig_wear_var is not None:
            self._pig_wear_var.set('')

        if hasattr(self, '_horse_vars') and self._horse_vars:
            for v in self._horse_vars.values():
                v.set(False)

        if hasattr(self, '_dog_wear_var') and self._dog_wear_var is not None:
            self._dog_wear_var.set('— not recorded')

        if hasattr(self, '_eruption_vars'):
            for v in self._eruption_vars.values():
                v.set('— not observed')

        if hasattr(self, '_cement_rings_var'):
            self._cement_rings_var.set('')
            self._cement_season_var.set('')

        if hasattr(self, '_histo_age_var'):
            self._histo_age_var.set('')
            self._histo_method_var.set('')
            self._histo_ref_var.set('')

        if hasattr(self, '_gross_morph_var'):
            self._gross_morph_var.set('')
            self._bone_texture_var.set('')
            self._gross_notes_var.set('')

        # Taphonomy
        self.weather_var.set(-1)
        self.burning_var.set('none')
        self.surf_qual_var.set(0)
        for v in self.butchery_vars.values():
            v.set(False)
        self.butchery_notes_var.set('')
        self.gnawing_var.set('none')
        self.tooth_pits_var.set(False)
        for v in self.surf_mod_vars.values():
            v.set(False)
        self.fragmentation_var.set('')
        self.completeness_var.set('')
        self.taph_notes_var.set('')
        self._update_taph_summary()

        self._calculate_age_live()

        self.measurement_status.config(text="")
        self.lsi_indicator.config(text="")
# ============================================================================
# TAB 3: IDENTITY - Morphological keys + OsteoID Calculator with Results
# ============================================================================

class IdentityTab(AnalysisTab):
    def __init__(self, parent, app, ui_queue):
        super().__init__(parent, app, ui_queue)
        self.ref_db = ReferenceDatabase()
        self._load_reference_database()
        self.keys_database = {}
        self._load_morphological_keys()

        # OsteoID database (lazy loaded)
        self.osteoid_data = None
        self.osteoid_stats = None
        self.osteoid_bone_types = []
        self.osteoid_common_names = []
        self.osteoid_scientific_names = []
        self.osteoid_loaded = False
        self.last_results = []
        self.last_unknown = {}

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
        """Refresh tab with current data."""
        super().refresh()

    def _load_reference_database(self):
        """Load the complete unified database."""
        try:
            plugin_dir = Path(__file__).parent
            appbase_dir = plugin_dir.parent.parent
            gz_path = appbase_dir / "config" / "zooarch_database.json.gz"

            with gzip.open(gz_path, 'rt', encoding='utf-8') as f:
                self.full_database = json.load(f)

            # Extract references for LSI calculations
            self.references = self.full_database.get('references', {})

            # Build taxon_references structure
            self.taxon_references = {}
            for ref_name, ref_data in self.references.items():
                taxon = ref_data.get('taxon', 'Unknown')
                self.taxon_references.setdefault(taxon, []).append(ref_name)

            # Build reference_standards for LSI (element-level grouping)
            self.reference_standards = {}
            for ref_name, ref_data in self.references.items():
                taxon = ref_data.get('taxon', 'Unknown')
                measurements = ref_data.get('measurements', [])

                # Group by element
                elem_dict = {}
                for m in measurements:
                    element = m.get('element', 'Unknown')
                    measure = m.get('measure', '')
                    standard = m.get('standard')
                    if measure and standard is not None:
                        elem_dict.setdefault(element, {})[measure] = float(standard)

                if elem_dict:
                    self.reference_standards.setdefault(taxon, {})[ref_name] = elem_dict

            # Load taxonomy
            self.taxonomy = {}
            for taxon in self.full_database.get('taxonomy', []):
                species = taxon.get('species')
                if species:
                    self.taxonomy[species] = {
                        'genus': taxon.get('genus'),
                        'tribe': taxon.get('tribe'),
                        'subfamily': taxon.get('subfamily'),
                        'family': taxon.get('family')
                    }

            # Load thesauri for data cleaning
            thesaurus = self.full_database.get('thesaurus', {})
            self.taxon_thesaurus = thesaurus.get('taxon', {})
            self.element_thesaurus = thesaurus.get('element', {})

            # Load specimen data for analysis examples
            self.specimen_data = self.full_database.get('specimen_data', {})

            taxa_count = len(self.taxon_references)
            self.set_status(f"✅ Loaded unified database: {taxa_count} taxa, {len(self.references)} references", "success")

            return True

        except Exception as e:
            self.set_status(f"⚠️ Error loading database: {e}", "warning")
            return False

    def _load_morphological_keys(self):
        """Load morphological keys from config folder."""
        try:
            from pathlib import Path
            plugin_dir = Path(__file__).parent
            appbase_dir = plugin_dir.parent.parent
            keys_path = appbase_dir / "config" / "morphological_keys.json"

            with open(keys_path, 'r', encoding='utf-8') as f:
                self.keys_database = json.load(f)

            if "metadata" in self.keys_database:
                metadata = self.keys_database.pop("metadata")
                version = metadata.get("version", "unknown")
                self.set_status(f"✅ Loaded morphological keys v{version}", "success")
                print(f"✅ Loaded morphological keys v{version}")
            else:
                self.set_status(f"✅ Loaded {len(self.keys_database)} morphological keys", "success")
                print(f"✅ Loaded morphological keys")

            return True
        except FileNotFoundError:
            self.set_status("⚠️ morphological_keys.json not found", "warning")
            print(f"⚠️ morphological_keys.json not found")
            self.keys_database = {
                "Sheep vs Goat (cranial)": "Sheep vs Goat cranial features - see references",
                "Sheep vs Goat (postcranial)": "Sheep vs Goat postcranial features - see references",
            }
            return False
        except Exception as e:
            self.set_status(f"⚠️ Error loading morphological keys: {e}", "warning")
            print(f"⚠️ Error loading morphological keys: {e}")
            self.keys_database = {}
            return False

    def _lazy_load_osteoid(self):
        """Load OsteoID database only when needed."""
        if self.osteoid_loaded:
            return True

        try:
            from pathlib import Path
            plugin_dir = Path(__file__).parent
            appbase_dir = plugin_dir.parent.parent

            # Try compressed version first, fall back to uncompressed
            gz_path = appbase_dir / "config" / "osteoid_database.json.gz"
            json_path = appbase_dir / "config" / "osteoid_database.json"

            # Show loading indicator
            if hasattr(self, 'osteoid_status'):
                self.osteoid_status.config(text="🔄 Loading OsteoID database (20MB)...")
                self.frame.update()

            print("🔄 Loading OsteoID database...")

            # Load from gzip if it exists
            if gz_path.exists():
                with gzip.open(gz_path, 'rt', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"✅ Loaded from compressed file (saved space)")
            else:
                # Fall back to uncompressed
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"✅ Loaded from uncompressed file")

            # Rest of your loading code remains the same...
            self.osteoid_data = data.get('data_by_specimen', [])

            # Process into long format for statistics
            df = self._process_specimen_data(self.osteoid_data)

            if len(df) == 0:
                print(f"⚠️ No valid bone measurements found")
                return False

            # Convert measurement columns to numeric
            for col in ['MaxL', 'MaxPW', 'MaxDW', 'MaxPD', 'DiamFH']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            # Rename MaxPW to MaxCPW for compatibility
            if 'MaxPW' in df.columns:
                df['MaxCPW'] = df['MaxPW']

            # Pre-calculate species statistics
            self.osteoid_stats = df.groupby(['Bone', 'Common_Name', 'Genus', 'Species']).agg({
                'MaxL': ['mean', 'std', 'min', 'max', 'count'],
                'MaxCPW': ['mean', 'std', 'min', 'max'],
                'MaxDW': ['mean', 'std', 'min', 'max']
            }).dropna()

            # Get bone types with counts
            bone_counts = df['Bone'].value_counts()
            self.osteoid_bone_types = [f"{bone}({count})" for bone, count in bone_counts.items()]

            # Get unique common and scientific names for autocomplete
            self.osteoid_common_names = sorted(df['Common_Name'].dropna().unique())

            # Build scientific names list
            sci_names = set()
            for _, row in df.iterrows():
                if pd.notna(row.get('Genus')) and pd.notna(row.get('Species')):
                    sci_names.add(f"{row['Genus']} {row['Species']}")
            self.osteoid_scientific_names = sorted(sci_names)

            # Update UI components if they exist
            if hasattr(self, 'bone_combo'):
                self.bone_combo['values'] = self.osteoid_bone_types
                if self.osteoid_bone_types:
                    self.bone_combo.set(self.osteoid_bone_types[0])

            if hasattr(self, 'common_combo'):
                self.common_combo['values'] = self.osteoid_common_names

            if hasattr(self, 'scientific_combo'):
                self.scientific_combo['values'] = self.osteoid_scientific_names

            self.osteoid_loaded = True

            if hasattr(self, 'osteoid_status'):
                self.osteoid_status.config(text=f"✅ Loaded {len(df)} bones from {len(self.osteoid_data)} specimens")

            print(f"✅ OsteoID database loaded: {len(df)} bone records")
            return True

        except FileNotFoundError:
            if hasattr(self, 'osteoid_status'):
                self.osteoid_status.config(text="⚠️ osteoid_database.json not found")
            print(f"⚠️ osteoid_database.json not found")
            return False
        except Exception as e:
            if hasattr(self, 'osteoid_status'):
                self.osteoid_status.config(text=f"⚠️ Error: {str(e)[:50]}")
            print(f"⚠️ Error loading OsteoID database: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _process_specimen_data(self, specimen_data):
        """Convert specimen data to long bone format."""
        rows = []

        # Define bone codes to look for
        bone_codes = ['Hum', 'Fem', 'Tib', 'Rad', 'Uln', 'Scap', 'OsCox', 'Fib', 'Metac', 'Metat']

        for specimen in specimen_data:
            common_name = specimen.get('Common_Name', '')
            genus = specimen.get('Genus', '')
            species = specimen.get('Species', '')

            if not common_name and not (genus and species):
                continue

            for bone in bone_codes:
                # Check for length measurement (minimum requirement)
                len_key = f"{bone}_MaxL"
                if len_key not in specimen or specimen[len_key] is None:
                    continue

                try:
                    row = {
                        'Bone': bone,
                        'Common_Name': common_name,
                        'Genus': genus,
                        'Species': species,
                        'MaxL': float(specimen[len_key]) if specimen[len_key] else None,
                        'MaxPW': None,
                        'MaxDW': None,
                        'MaxPD': None,
                        'DiamFH': None
                    }

                    # Check for other measurements
                    pw_key = f"{bone}_MaxPW"
                    if pw_key in specimen and specimen[pw_key]:
                        row['MaxPW'] = float(specimen[pw_key])

                    dw_key = f"{bone}_MaxDW"
                    if dw_key in specimen and specimen[dw_key]:
                        row['MaxDW'] = float(specimen[dw_key])

                    pd_key = f"{bone}_MaxPD"
                    if pd_key in specimen and specimen[pd_key]:
                        row['MaxPD'] = float(specimen[pd_key])

                    fh_key = f"{bone}_DiamFH"
                    if fh_key in specimen and specimen[fh_key]:
                        row['DiamFH'] = float(specimen[fh_key])

                    rows.append(row)
                except:
                    continue

        return pd.DataFrame(rows)

    def _update_dropdowns_from_filter(self):
        """Update dropdowns based on current filter values in both name fields."""
        if not self.osteoid_data:
            return

        # Get current filter values
        common_filter = self.common_name_var.get().strip().lower()
        scientific_filter = self.scientific_name_var.get().strip().lower()

        # If both filters are empty, reset everything
        if not common_filter and not scientific_filter:
            self._reset_all_dropdowns()
            self._perform_search()  # Make sure this is here
            return

        # Collect matching specimens based on both filters
        matching_specimens = []

        for specimen in self.osteoid_data:
            # Check common name match
            common_match = True
            if common_filter:
                common_val = specimen.get('Common_Name', '').lower()
                common_match = common_filter in common_val

            # Check scientific name match
            scientific_match = True
            if scientific_filter:
                genus = specimen.get('Genus', '').lower()
                species = specimen.get('Species', '').lower()
                sci_val = f"{genus} {species}".strip()
                scientific_match = scientific_filter in sci_val

            if common_match and scientific_match:
                matching_specimens.append(specimen)

        # Update common names dropdown
        common_names = set()
        for specimen in matching_specimens:
            name = specimen.get('Common_Name', '')
            if name:
                common_names.add(name)

        if hasattr(self, 'common_combo'):
            self.common_combo['values'] = sorted(common_names)

        # Update scientific names dropdown
        sci_names = set()
        for specimen in matching_specimens:
            genus = specimen.get('Genus', '')
            species = specimen.get('Species', '')
            if genus and species:
                sci_names.add(f"{genus} {species}")

        if hasattr(self, 'scientific_combo'):
            self.scientific_combo['values'] = sorted(sci_names)

        # Update bone dropdown with counts
        bone_counts = {}
        for specimen in matching_specimens:
            for bone_code in ['Hum', 'Fem', 'Tib', 'Rad', 'Uln', 'Scap', 'OsCox', 'Fib', 'Metac', 'Metat']:
                if f"{bone_code}_MaxL" in specimen and specimen[f"{bone_code}_MaxL"]:
                    bone_counts[bone_code] = bone_counts.get(bone_code, 0) + 1

        bone_display = [f"{bone}({count})" for bone, count in sorted(bone_counts.items())]
        if hasattr(self, 'bone_combo'):
            # Store current bone selection
            current_bone = self.bone_var.get()

            # Update the dropdown options
            self.bone_combo['values'] = bone_display

            # If the current selection is not in the new options, clear it
            if current_bone and current_bone not in bone_display:
                self.bone_var.set("")  # Clear the selection
            # Otherwise, if there's no selection and we have options, select the first one
            elif not current_bone and bone_display:
                self.bone_combo.set(bone_display[0])

        # IMPORTANT: Trigger the search to update results
        self._perform_search()

    def _on_common_name_type(self, *args):
        """Handle typing in common name field."""
        if not self.osteoid_loaded:
            self._lazy_load_osteoid()
            return

        common_text = self.common_name_var.get().strip()
        sci_text = self.scientific_name_var.get().strip()

        # If common field is cleared, also clear scientific field
        if not common_text and sci_text:
            self.scientific_name_var.set("")

        self._update_dropdowns_from_filter()

    def _on_scientific_name_type(self, *args):
        """Handle typing in scientific name field."""
        if not self.osteoid_loaded:
            self._lazy_load_osteoid()
            return

        sci_text = self.scientific_name_var.get().strip()
        common_text = self.common_name_var.get().strip()

        # If scientific field is cleared, also clear common field
        if not sci_text and common_text:
            self.common_name_var.set("")

        self._update_dropdowns_from_filter()

    def _reset_all_dropdowns(self):
        """Reset all dropdowns to show all available options."""
        if not self.osteoid_data:
            return

        # Reset common names
        all_common = set()
        all_scientific = set()
        bone_counts = {}

        for specimen in self.osteoid_data:
            # Common names
            common = specimen.get('Common_Name', '')
            if common:
                all_common.add(common)

            # Scientific names
            genus = specimen.get('Genus', '')
            species = specimen.get('Species', '')
            if genus and species:
                all_scientific.add(f"{genus} {species}")

            # Bone counts
            for bone_code in ['Hum', 'Fem', 'Tib', 'Rad', 'Uln', 'Scap', 'OsCox', 'Fib', 'Metac', 'Metat']:
                if f"{bone_code}_MaxL" in specimen and specimen[f"{bone_code}_MaxL"]:
                    bone_counts[bone_code] = bone_counts.get(bone_code, 0) + 1

        # Update common combo
        if hasattr(self, 'common_combo'):
            self.common_combo['values'] = sorted(all_common)

        # Update scientific combo
        if hasattr(self, 'scientific_combo'):
            self.scientific_combo['values'] = sorted(all_scientific)

        # Update bone combo with counts
        bone_display = [f"{bone}({count})" for bone, count in sorted(bone_counts.items())]
        if hasattr(self, 'bone_combo'):
            self.bone_combo['values'] = bone_display
            if bone_display and not self.bone_var.get():
                self.bone_combo.set(bone_display[0])

    def search_osteoid(self, bone_type=None, common_name=None, scientific_name=None,
                    length=None, prox_width=None, dist_width=None, top_n=15):
        """
        Search the OsteoID database with any combination of filters.
        """
        if not self.osteoid_loaded:
            if not self._lazy_load_osteoid():
                return []

        # Filter stats by criteria
        filtered_stats = self.osteoid_stats.copy()

        # Filter by bone type if provided
        if bone_type:
            try:
                filtered_stats = filtered_stats.loc[bone_type]
            except KeyError:
                return []

            # Prepare results list for single bone type
            results = []
            for (common, genus, species), row in filtered_stats.iterrows():
                # Filter by common name if provided
                if common_name and common_name.lower() not in str(common).lower():
                    continue

                # Filter by scientific name if provided
                if scientific_name:
                    sci = f"{genus} {species}".lower()
                    if scientific_name.lower() not in sci:
                        continue

                results.append((common, genus, species, row))

            return self._score_results(results, length, prox_width, dist_width, top_n)

        else:
            # If no bone type, combine all bones
            all_results = []
            for bt in filtered_stats.index.get_level_values(0).unique():
                try:
                    bt_stats = filtered_stats.loc[bt]
                    for (common, genus, species), row in bt_stats.iterrows():
                        # Apply name filters here too
                        if common_name and common_name.lower() not in str(common).lower():
                            continue
                        if scientific_name:
                            sci = f"{genus} {species}".lower()
                            if scientific_name.lower() not in sci:
                                continue
                        all_results.append((common, genus, species, row))
                except:
                    continue

            return self._score_results(all_results, length, prox_width, dist_width, top_n)

    def _score_results(self, results, length, prox_width, dist_width, top_n):
        """Calculate scores for filtered results."""
        scored = []

        for common, genus, species, row in results:
            z_scores = []
            dimensions_used = 0

            # Length
            if length is not None and pd.notna(length) and row[('MaxL', 'std')] > 0:
                z = (length - row[('MaxL', 'mean')]) / row[('MaxL', 'std')]
                z_scores.append(z)
                dimensions_used += 1

            # Proximal Width
            if prox_width is not None and pd.notna(prox_width) and row[('MaxCPW', 'std')] > 0:
                z = (prox_width - row[('MaxCPW', 'mean')]) / row[('MaxCPW', 'std')]
                z_scores.append(z)
                dimensions_used += 1

            # Distal Width
            if dist_width is not None and pd.notna(dist_width) and row[('MaxDW', 'std')] > 0:
                z = (dist_width - row[('MaxDW', 'mean')]) / row[('MaxDW', 'std')]
                z_scores.append(z)
                dimensions_used += 1

            # If no measurements provided, still include but with score 0
            if not z_scores:
                final_score = 0
            else:
                final_score = np.sqrt(np.mean(np.square(z_scores)))

            # Check range
            in_range = True
            range_issues = []

            if length is not None and pd.notna(length):
                if length < row[('MaxL', 'min')] or length > row[('MaxL', 'max')]:
                    in_range = False
                    range_issues.append('L')
            if prox_width is not None and pd.notna(prox_width):
                if prox_width < row[('MaxCPW', 'min')] or prox_width > row[('MaxCPW', 'max')]:
                    in_range = False
                    range_issues.append('P')
            if dist_width is not None and pd.notna(dist_width):
                if dist_width < row[('MaxDW', 'min')] or dist_width > row[('MaxDW', 'max')]:
                    in_range = False
                    range_issues.append('D')

            # Sample size and confidence
            sample_size = row[('MaxL', 'count')] if pd.notna(row[('MaxL', 'count')]) else 0
            ci = 1.96 * (final_score / np.sqrt(sample_size)) if sample_size > 1 and final_score > 0 else 0

            if sample_size >= 10 and final_score < 1.5:
                confidence = "High"
            elif sample_size >= 5 and final_score < 2.5:
                confidence = "Medium"
            else:
                confidence = "Low"

            scored.append({
                'Common Name': common,
                'Scientific Name': f"{genus} {species}",
                'Match Score': round(final_score, 3),
                'Within Range': "✓" if in_range else f"✗ ({','.join(range_issues)})",
                'Confidence': confidence,
                'Sample Size': int(sample_size) if pd.notna(sample_size) else 0,
                'CI': round(ci, 3),
                'Mean L': round(row[('MaxL', 'mean')], 1) if pd.notna(row[('MaxL', 'mean')]) else None,
                'Mean PW': round(row[('MaxCPW', 'mean')], 1) if pd.notna(row[('MaxCPW', 'mean')]) else None,
                'Mean DW': round(row[('MaxDW', 'mean')], 1) if pd.notna(row[('MaxDW', 'mean')]) else None,
                'Std L': round(row[('MaxL', 'std')], 2) if pd.notna(row[('MaxL', 'std')]) else None,
                'Std PW': round(row[('MaxCPW', 'std')], 2) if pd.notna(row[('MaxCPW', 'std')]) else None,
                'Std DW': round(row[('MaxDW', 'std')], 2) if pd.notna(row[('MaxDW', 'std')]) else None,
            })

        # Sort by best match
        if any(m['Match Score'] > 0 for m in scored):
            scored.sort(key=lambda x: (0 if x['Within Range'].startswith('✓') else 1, x['Match Score']))
        else:
            # If no measurements, sort alphabetically
            scored.sort(key=lambda x: x['Common Name'])

        return scored[:top_n]

    def _perform_search(self, *args):
        """Perform the actual search and update results."""
        # Lazy load if needed
        if not self.osteoid_loaded:
            if not self._lazy_load_osteoid():
                return

        # Get filter values
        bone_selection = self.bone_var.get()
        bone_type = bone_selection.split('(')[0] if '(' in bone_selection else bone_selection if bone_selection else None

        common_name = self.common_name_var.get().strip() or None
        scientific_name = self.scientific_name_var.get().strip() or None

        # Get measurements
        try:
            length = float(self.length_var.get()) if self.length_var.get().strip() else None
            prox = float(self.prox_var.get()) if self.prox_var.get().strip() else None
            dist = float(self.dist_var.get()) if self.dist_var.get().strip() else None
        except ValueError:
            self.osteoid_status.config(text="⚠️ Invalid number format")
            return

        # Run search
        results = self.search_osteoid(
            bone_type=bone_type,
            common_name=common_name,
            scientific_name=scientific_name,
            length=length,
            prox_width=prox,
            dist_width=dist
        )

        # Store results
        self.last_results = results
        self.last_unknown = {
            'bone': bone_type,
            'common': common_name,
            'scientific': scientific_name,
            'length': length,
            'prox_width': prox,
            'dist_width': dist
        }

        # Update results display
        self._update_results_display(results)

        # Update status
        if results:
            if results[0]['Match Score'] > 0:
                self.osteoid_status.config(
                    text=f"✓ Found {len(results)} matches. Best: {results[0]['Common Name']} (Z={results[0]['Match Score']:.2f})"
                )
            else:
                self.osteoid_status.config(
                    text=f"✓ Found {len(results)} matches. (No measurements for scoring)"
                )
        else:
            self.osteoid_status.config(text="No matches found")

    def _update_results_display(self, results):
        """Update the results tab with search results."""
        self.class_result.delete(1.0, tk.END)

        if not results:
            self.class_result.insert(1.0, "No matches found for the entered criteria.")
            return

        # Header
        self.class_result.insert(1.0, "OSTEOID BONE IDENTIFICATION RESULTS\n")
        self.class_result.insert(tk.END, "=" * 60 + "\n\n")

        # Search criteria
        self.class_result.insert(tk.END, "SEARCH CRITERIA:\n")
        if self.last_unknown['common']:
            self.class_result.insert(tk.END, f"Common Name: {self.last_unknown['common']}\n")
        if self.last_unknown['scientific']:
            self.class_result.insert(tk.END, f"Scientific Name: {self.last_unknown['scientific']}\n")
        if self.last_unknown['bone']:
            self.class_result.insert(tk.END, f"Bone Type: {self.last_unknown['bone']}\n")
        if self.last_unknown['length']:
            self.class_result.insert(tk.END, f"Max Length: {self.last_unknown['length']:.1f} mm\n")
        if self.last_unknown['prox_width']:
            self.class_result.insert(tk.END, f"Proximal Width: {self.last_unknown['prox_width']:.1f} mm\n")
        if self.last_unknown['dist_width']:
            self.class_result.insert(tk.END, f"Distal Width: {self.last_unknown['dist_width']:.1f} mm\n")

        self.class_result.insert(tk.END, "\n" + "-" * 60 + "\n\n")
        self.class_result.insert(tk.END, "MATCHING SPECIES:\n\n")

        # Display results
        for i, r in enumerate(results, 1):
            self.class_result.insert(tk.END, f"{i}. {r['Common Name']} ({r['Scientific Name']})\n")

            if r['Match Score'] > 0:
                self.class_result.insert(tk.END, f"   Z-Score: {r['Match Score']:.2f}  |  Range: {r['Within Range']}  |  Confidence: {r['Confidence']}\n")
                self.class_result.insert(tk.END, f"   Sample Size: n={r['Sample Size']}  |  95% CI: ±{r['CI']:.2f}\n")
            else:
                self.class_result.insert(tk.END, f"   (No measurements for scoring)\n")

            # Show mean values
            means = []
            if r['Mean L']:
                means.append(f"L: {r['Mean L']:.1f}")
            if r['Mean PW']:
                means.append(f"PW: {r['Mean PW']:.1f}")
            if r['Mean DW']:
                means.append(f"DW: {r['Mean DW']:.1f}")
            if means:
                self.class_result.insert(tk.END, f"   Reference means: {', '.join(means)} mm\n")

            self.class_result.insert(tk.END, "\n")

        # Generate plot if we have measurements
        if HAS_MPL and any([self.last_unknown['length'], self.last_unknown['prox_width'], self.last_unknown['dist_width']]):
            self._generate_comparison_plot(results)

        self.result_status.config(
            text="✓ Search complete! View results above",
            foreground="#8B4513",
            background="#f1c40f"
        )

    def _generate_comparison_plot(self, results):
        """Generate comparison plot for top matches."""
        if not HAS_MPL:
            return

        self.ax.clear()

        # Get top 5 results with scores
        top_results = [r for r in results if r['Match Score'] > 0][:5]
        if not top_results:
            return

        # Set up dimensions
        dimensions = []
        if self.last_unknown['length']:
            dimensions.append('Length')
        if self.last_unknown['prox_width']:
            dimensions.append('Prox Width')
        if self.last_unknown['dist_width']:
            dimensions.append('Dist Width')

        if not dimensions:
            return

        x = np.arange(len(dimensions))
        width = 0.15

        # Plot each species
        for i, result in enumerate(top_results):
            means = []
            if 'Length' in dimensions and result['Mean L']:
                means.append(result['Mean L'])
            elif 'Length' in dimensions:
                means.append(0)

            if 'Prox Width' in dimensions and result['Mean PW']:
                means.append(result['Mean PW'])
            elif 'Prox Width' in dimensions:
                means.append(0)

            if 'Dist Width' in dimensions and result['Mean DW']:
                means.append(result['Mean DW'])
            elif 'Dist Width' in dimensions:
                means.append(0)

            offset = width * (i - (len(top_results)-1)/2)
            bars = self.ax.bar(x + offset, means, width, label=result['Common Name'][:15], alpha=0.7)

            # Add error bars
            errors = []
            if 'Length' in dimensions and result['Std L']:
                errors.append(result['Std L'])
            elif 'Length' in dimensions:
                errors.append(0)

            if 'Prox Width' in dimensions and result['Std PW']:
                errors.append(result['Std PW'])
            elif 'Prox Width' in dimensions:
                errors.append(0)

            if 'Dist Width' in dimensions and result['Std DW']:
                errors.append(result['Std DW'])
            elif 'Dist Width' in dimensions:
                errors.append(0)

            self.ax.errorbar(x + offset, means, yerr=errors, fmt='none', ecolor='black', capsize=3)

        # Plot unknown
        unknown_vals = []
        if 'Length' in dimensions and self.last_unknown['length']:
            unknown_vals.append(self.last_unknown['length'])
        elif 'Length' in dimensions:
            unknown_vals.append(0)

        if 'Prox Width' in dimensions and self.last_unknown['prox_width']:
            unknown_vals.append(self.last_unknown['prox_width'])
        elif 'Prox Width' in dimensions:
            unknown_vals.append(0)

        if 'Dist Width' in dimensions and self.last_unknown['dist_width']:
            unknown_vals.append(self.last_unknown['dist_width'])
        elif 'Dist Width' in dimensions:
            unknown_vals.append(0)

        self.ax.scatter(x, unknown_vals, color='red', s=100, marker='*', label='Your specimen', zorder=5)

        # Customize
        self.ax.set_xticks(x)
        self.ax.set_xticklabels(dimensions)
        self.ax.set_ylabel('Measurement (mm)')
        self.ax.set_title('Top Matches vs Your Specimen')
        self.ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
        self.ax.grid(True, alpha=0.3)

        self.fig.tight_layout()
        self.canvas.draw()

    def _build_ui(self):
        # === MAIN PANED WINDOW ===
        main = ttk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        main.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # LEFT PANEL - Morphological Keys
        left = ttk.Frame(main)
        main.add(left, weight=1)

        # RIGHT PANEL - OsteoID Calculator + Results
        right = ttk.Frame(main)
        main.add(right, weight=1)

        left.configure(width=1)
        right.configure(width=1)

        # === LEFT PANEL - MORPHOLOGICAL KEYS ===
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

        # === RIGHT PANEL - NOTEBOOK WITH TWO TABS ===
        self.right_notebook = ttk.Notebook(right)
        self.right_notebook.pack(fill=tk.BOTH, expand=True)

        # === TAB 1: OSTEOID CALCULATOR ===
        calc_frame = ttk.Frame(self.right_notebook)
        self.right_notebook.add(calc_frame, text="OsteoID Calculator")

        # Title
        title_frame = ttk.Frame(calc_frame)
        title_frame.pack(fill=tk.X, pady=5)
        ttk.Label(title_frame, text="🦴 OsteoID Bone Calculator",
                 font=("Arial", 12, "bold")).pack()
        ttk.Label(title_frame, text="Search by name or measurements",
                 font=("Arial", 8, "italic")).pack()

        # Input Frame
        input_frame = ttk.LabelFrame(calc_frame, text="Search Criteria", padding=10)
        input_frame.pack(fill=tk.X, pady=5, padx=5)

        # Common Name search
        common_frame = ttk.Frame(input_frame)
        common_frame.pack(fill=tk.X, pady=2)
        ttk.Label(common_frame, text="Common Name:", width=15).pack(side=tk.LEFT)
        self.common_name_var = tk.StringVar()
        self.common_combo = ttk.Combobox(common_frame, textvariable=self.common_name_var,
                                        values=[], width=30)
        self.common_combo.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        self.common_name_var.trace_add('write', self._on_common_name_type)
        self.common_combo.bind('<<ComboboxSelected>>', self._perform_search)

        # Scientific Name search
        scientific_frame = ttk.Frame(input_frame)
        scientific_frame.pack(fill=tk.X, pady=2)
        ttk.Label(scientific_frame, text="Scientific Name:", width=15).pack(side=tk.LEFT)
        self.scientific_name_var = tk.StringVar()
        self.scientific_combo = ttk.Combobox(scientific_frame, textvariable=self.scientific_name_var,
                                           values=[], width=30)
        self.scientific_combo.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        self.scientific_name_var.trace_add('write', self._on_scientific_name_type)
        self.scientific_combo.bind('<<ComboboxSelected>>', self._perform_search)

        # Bone Type
        bone_frame = ttk.Frame(input_frame)
        bone_frame.pack(fill=tk.X, pady=2)
        ttk.Label(bone_frame, text="Bone Type:", width=15).pack(side=tk.LEFT)
        self.bone_var = tk.StringVar()
        self.bone_combo = ttk.Combobox(bone_frame, textvariable=self.bone_var,
                                       values=[], width=20)
        self.bone_combo.pack(side=tk.LEFT, padx=2)
        self.bone_combo.bind('<<ComboboxSelected>>', self._perform_search)

        # Separator
        ttk.Separator(input_frame, orient='horizontal').pack(fill=tk.X, pady=10)

        # Measurements
        meas_label = ttk.Label(input_frame, text="Measurements (optional):", font=("Arial", 9, "bold"))
        meas_label.pack(anchor='w', pady=2)

        # Length
        len_frame = ttk.Frame(input_frame)
        len_frame.pack(fill=tk.X, pady=2)
        ttk.Label(len_frame, text="Max Length (mm):", width=15).pack(side=tk.LEFT)
        self.length_var = tk.StringVar()
        self.length_var.trace_add('write', self._perform_search)
        ttk.Entry(len_frame, textvariable=self.length_var, width=10).pack(side=tk.LEFT, padx=2)

        # Proximal Width
        prox_frame = ttk.Frame(input_frame)
        prox_frame.pack(fill=tk.X, pady=2)
        ttk.Label(prox_frame, text="Proximal Width (mm):", width=15).pack(side=tk.LEFT)
        self.prox_var = tk.StringVar()
        self.prox_var.trace_add('write', self._perform_search)
        ttk.Entry(prox_frame, textvariable=self.prox_var, width=10).pack(side=tk.LEFT, padx=2)

        # Distal Width
        dist_frame = ttk.Frame(input_frame)
        dist_frame.pack(fill=tk.X, pady=2)
        ttk.Label(dist_frame, text="Distal Width (mm):", width=15).pack(side=tk.LEFT)
        self.dist_var = tk.StringVar()
        self.dist_var.trace_add('write', self._perform_search)
        ttk.Entry(dist_frame, textvariable=self.dist_var, width=10).pack(side=tk.LEFT, padx=2)

        # Status
        self.osteoid_status = ttk.Label(calc_frame, text="Start typing to search...",
                                       font=("Arial", 7))
        self.osteoid_status.pack(anchor='w', padx=5, pady=2)

        # Instructions
        note_frame = ttk.Frame(calc_frame)
        note_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(note_frame,
                 text="Type to filter - dropdowns update automatically. Results appear in the 'Results' tab.",
                 font=("Arial", 7, "italic"), foreground="gray").pack()

        # === TAB 2: RESULTS & VISUALIZATION ===
        results_frame = ttk.Frame(self.right_notebook)
        self.right_notebook.add(results_frame, text="Results & Visualization")
        self.results_frame = results_frame

        results_pane = ttk.PanedWindow(results_frame, orient=tk.VERTICAL)
        results_pane.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        stats_panel = ttk.Frame(results_pane)
        results_pane.add(stats_panel, weight=1)

        class_frame = ttk.LabelFrame(stats_panel, text="Classification Results", padding=5)
        class_frame.pack(fill=tk.BOTH, expand=True, pady=2)

        self.class_result = tk.Text(class_frame, wrap=tk.WORD, font=("Courier", 9))
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

        # Status notification
        self.result_status = tk.Label(results_frame,
                                      text="",
                                      font=("Arial", 8, "bold"),
                                      relief=tk.FLAT)
        self.result_status.pack(anchor='w', padx=5, pady=2, fill=tk.X)

        # === FORCE EQUAL SPLIT ===
        def force_equal_split():
            left.configure(width=1)
            right.configure(width=1)
            total = main.winfo_width()
            if total > 10:
                main.sashpos(0, total // 2)

        self.frame.after(50, force_equal_split)
        self.frame.after(300, force_equal_split)

    def _clear_all(self):
        """Clear all input fields."""
        self.common_name_var.set("")
        self.scientific_name_var.set("")
        self.bone_var.set("")
        self.length_var.set("")
        self.prox_var.set("")
        self.dist_var.set("")
        self.class_result.delete(1.0, tk.END)
        if HAS_MPL:
            self.ax.clear()
            self.ax.text(0.5, 0.5, "Enter search criteria", ha='center', va='center')
            self.canvas.draw()
        self.osteoid_status.config(text="Input cleared")

    def _update_ui(self):
        """Required by base class."""
        pass

    def _update_key_list(self, event=None):
        """Update key list based on selected category."""
        category = self.key_category_var.get()

        all_keys = list(self.keys_database.keys())

        if category == "Mammals":
            terms = ['Sheep', 'Goat', 'Cattle', 'Bison', 'Deer', 'Horse', 'Donkey',
                    'Pig', 'Boar', 'Dog', 'Wolf', 'Fox', 'Hare', 'Rabbit', 'Bear', 'Seal']
            filtered = [k for k in all_keys if any(t in k for t in terms)]
        elif category == "Birds":
            terms = ['Chicken', 'Pheasant', 'Grouse', 'Duck', 'Goose', 'Swan', 'Turkey',
                    'Peafowl', 'Raptor', 'Eagle', 'Hawk', 'Owl', 'Corvid', 'Crow', 'Raven']
            filtered = [k for k in all_keys if any(t in k for t in terms)]
        elif category == "Fish":
            terms = ['Cod', 'Haddock', 'Pollock', 'Salmon', 'Trout', 'Grayling', 'Herring',
                    'Sprat', 'Sardine', 'Flatfish', 'Plaice', 'Flounder', 'Sole', 'Turbot',
                    'Cyprinid', 'Carp', 'Roach', 'Bream', 'Chub', 'Dace']
            filtered = [k for k in all_keys if any(t in k for t in terms)]
        elif category == "Special Cases":
            terms = ['eruption', 'wear', 'ages', 'fusion', 'epiphyseal', 'dental', 'sexing',
                    'spur', 'Payne', 'Grant', 'Behrensmeyer', 'Butchery', 'Burning', 'Root',
                    'Gnawing', 'Trampling', 'Digestion', 'Cementum', 'Oxygen', 'Strontium',
                    'Carbon', 'Nitrogen', 'Sulfur', 'FTIR', 'Collagen', 'Trophic']
            filtered = [k for k in all_keys if any(t in k.lower() for t in terms)]
        else:
            filtered = []

        self.key_combo['values'] = filtered
        if filtered:
            self.key_combo.set(filtered[0])
            self._update_key()

    def _update_key(self, event=None):
        """Update morphological key text with citations."""
        key = self.key_var.get()
        if not key:
            return

        self.key_text.delete(1.0, tk.END)

        if key in self.keys_database:
            entry = self.keys_database[key]

            if isinstance(entry, dict):
                text = entry.get("text", "")
                citations = entry.get("citations", [])

                self.key_text.insert(1.0, text)

                if citations:
                    self.key_text.insert(tk.END, "\n\n" + "="*50 + "\n")
                    self.key_text.insert(tk.END, "REFERENCES:\n")
                    for i, citation in enumerate(citations, 1):
                        self.key_text.insert(tk.END, f"{i}. {citation}\n")
            else:
                self.key_text.insert(1.0, entry)
        else:
            self.key_text.insert(1.0, f"Key '{key}' not available")

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
        plugin_dir = Path(__file__).parent
        appbase_dir = plugin_dir.parent.parent
        config_dir = appbase_dir / "config"
        tdf_path = config_dir / "tdf_database.json"

        success, message = self.tdf.load_from_file(tdf_path)
        if success:
            self.set_status(f"✅ Loaded {len(self.tdf.entries)} TDF entries for ecology", "success")
            print(f"✅ {message}")
        else:
            self.set_status(f"⚠️ TDF database not found - using defaults", "warning")
            print(f"⚠️ {message}")

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

    def set_status(self, message, message_type="info"):
        """Send status message to main app's status bar."""
        if hasattr(self.app, 'center') and hasattr(self.app.center, 'set_status'):
            self.app.center.set_status(message, message_type)
        else:
            print(f"[{message_type}] {message}")

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
        """Import CSV file using main app's import method."""
        # Let the main app's LeftPanel handle the import
        if hasattr(self.app, 'left') and hasattr(self.app.left, 'import_csv'):
            # Call the main app's import method
            self.app.left.import_csv()

            # Refresh all tabs with the new data
            self._refresh_all()

            # Also refresh the main app's center panel to show the new data
            if hasattr(self.app, 'center') and hasattr(self.app.center, '_refresh'):
                self.app.center._refresh()

            self.set_status("✅ Import complete and tables refreshed", "success")
        else:
            self.set_status("❌ Main app import method not available", "error")
            messagebox.showerror("Error", "Main app import method not available")

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
        """Send selected data from current tab to main table."""
        current_tab_id = self.notebook.index(self.notebook.select())
        tab_names = list(self.tabs.keys())
        if current_tab_id >= len(tab_names):
            self.set_status("⚠️ No active tab found", "warning")
            return

        active_tab = self.tabs[tab_names[current_tab_id]]
        selected = active_tab.selected_indices

        if not selected:
            self.set_status("⚠️ No specimens selected", "warning")
            return

        # If tab has a gather_updates method, use it
        if hasattr(active_tab, 'gather_updates'):
            updates = active_tab.gather_updates(selected)
            success = 0
            for idx, update_data in updates.items():
                if update_data:
                    self.app.data_hub.update_row(idx, update_data)
                    success += 1
            self.set_status(f"✅ Updated {success} records in main table", "success")
        else:
            self.set_status(f"⚠️ Tab '{tab_names[current_tab_id]}' doesn't support sending data", "warning")

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
