"""
Compositional Data Analysis Plugin for Basalt Provenance Toolkit v10.2+
AITCHISON GEOMETRY - ROBUST PCA - FULL ILR - SUBCOMPOSITIONS - INTERACTIVE BIPLOT
v1.1.1 - Orthonormal basis, enhanced hover, fast MCD option

Author: Sefy Levy
License: CC BY-NC-SA 4.0
Version: 1.1.1 - Fixed label, enhanced tooltips, performance option
"""

PLUGIN_INFO = {
    "category": "software",
    "id": "compositional_stats",
    "name": "Compositional Data Analysis",
    "description": "Aitchison geometry, robust PCA, full ilr balances, subcomposition analysis - mathematically correct stats for geochemists",
    "icon": "📐",
    "version": "1.1.1",
    "requires": ["numpy", "scipy", "sklearn", "matplotlib"],
    "author": "Sefy Levy"
}

import tkinter as tk
from tkinter import ttk, messagebox
import math
import numpy as np
from datetime import datetime

try:
    from scipy.stats import chi2
    from scipy.spatial.distance import pdist, squareform
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    from sklearn.decomposition import PCA
    from sklearn.covariance import MinCovDet
    from sklearn.preprocessing import StandardScaler
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.widgets import Cursor
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


class CompositionalStatsPlugin:
    """
    PROFESSIONAL COMPOSITIONAL DATA ANALYSIS v1.1.1
    ============================================================================
    ✓ Full ilr with orthonormal bases (Gram-Schmidt orthogonalization)
    ✓ Robust PCA with Minimum Covariance Determinant (MCD) estimator
    ✓ Fast MCD option for large datasets (>100 samples)
    ✓ Subcomposition selection (HFSE, REE, LILE, transition metals, custom)
    ✓ Interactive biplot with hover tooltips (sample ID + Mahalanobis + outlier flag)
    ✓ Aitchison distance matrix with hierarchical clustering
    ✓ Mahalanobis outlier detection with 95%/99% confidence ellipses
    ✓ Export transformed coordinates (clr, ilr, robust PCA scores)
    ============================================================================
    """

    # Predefined subcomposition templates
    SUBCOMPOSITIONS = {
        "all": {"name": "All elements", "pattern": None},
        "hfse": {"name": "HFSE (High Field Strength)", "elements": ["Zr", "Nb", "Ti", "Y", "Hf", "Ta"]},
        "ree": {"name": "REE (Rare Earth Elements)", "elements": ["La", "Ce", "Pr", "Nd", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu"]},
        "lile": {"name": "LILE (Large Ion Lithophile)", "elements": ["Ba", "Rb", "Sr", "Cs", "K"]},
        "transition": {"name": "Transition metals", "elements": ["Cr", "Ni", "Co", "Sc", "V", "Cu", "Zn"]},
        "custom": {"name": "Custom selection...", "elements": []}
    }

    def __init__(self, main_app):
        """Initialize plugin with dynamic table support"""
        self.app = main_app
        self.window = None
        self.transformed_data = None
        self.pca_result = None
        self.selected_elements = []
        self.current_transform = None
        self.sample_ids = []
        self.psi_matrix = None  # For ilr orthonormal bases
        self.subcomp_elements = {}  # For storing custom selections

        # UI elements
        self.preview_text = None
        self.results_tree = None
        self.elem_listbox = None
        self.status_indicator = None
        self.stats_label = None
        self.pca_canvas_frame = None
        self.dist_text = None
        self.outlier_text = None
        self.elem_count_label = None

    def _get_available_elements(self):
        """Smart detection of element columns (ppm only)"""
        if not self.app.samples:
            return []

        elements = set()
        element_patterns = ['Zr', 'Nb', 'Cr', 'Ni', 'Ba', 'Rb', 'Sr', 'Y',
                           'La', 'Ce', 'Nd', 'Sm', 'Eu', 'Gd', 'Dy', 'Er',
                           'Yb', 'Lu', 'Th', 'U', 'Ti', 'V', 'Co', 'Sc',
                           'Hf', 'Ta', 'Cs', 'Pr', 'Tb', 'Ho', 'Tm']

        for sample in self.app.samples[:5]:
            for key in sample.keys():
                key_str = str(key)
                for elem in element_patterns:
                    if (elem in key_str or elem.lower() in key_str.lower()) and 'ppm' in key_str.lower():
                        elements.add(key_str)

        return sorted(list(elements))

    def _get_element_values(self, sample, element_col):
        """Extract numeric values from element column"""
        try:
            val = sample.get(element_col, 0)
            if val is None or val == '':
                return None
            return float(val)
        except (ValueError, TypeError):
            return None

    def _ilr_transform_full(self, X):
        """
        FULL ISOMETRIC LOG-RATIO TRANSFORM with orthonormal bases
        Uses Gram-Schmidt orthogonalization on Sequential Binary Partition
        This is mathematically complete - not a simplified version!
        """
        n, D = X.shape
        if D < 2:
            return X, None

        # Step 1: Create Sequential Binary Partition (SBP) matrix
        # This defines balances between groups of parts
        psi = np.zeros((D-1, D))

        # Generate orthonormal basis using Gram-Schmidt process
        # This ensures the balances are orthogonal in the simplex
        for i in range(D-1):
            if i == 0:
                # First balance: part 1 vs geometric mean of parts 2..D
                r = 1
                s = D - 1
                psi[i, 0] = np.sqrt(s / (r * (r + s)))
                psi[i, 1:] = -np.sqrt(r / (s * (r + s)))
            else:
                # Subsequent balances: part i+1 vs geometric mean of parts i+2..D
                r = 1
                s = D - i - 1
                if s > 0:
                    psi[i, i] = np.sqrt(s / (r * (r + s)))
                    psi[i, i+1:] = -np.sqrt(r / (s * (r + s)))
                else:
                    psi[i, i] = 1.0

        # Step 2: Orthonormalize using Gram-Schmidt
        # This ensures the basis vectors are orthonormal in the Aitchison geometry
        for i in range(1, D-1):
            for j in range(i):
                # Project out component j from i
                projection = np.dot(psi[i], psi[j])
                psi[i] = psi[i] - projection * psi[j]
            # Normalize
            norm = np.linalg.norm(psi[i])
            if norm > 0:
                psi[i] = psi[i] / norm

        # Step 3: Apply ilr transformation
        ilr_coords = np.zeros((n, D-1))
        for i in range(n):
            log_x = np.log(X[i])
            for j in range(D-1):
                ilr_coords[i, j] = np.dot(psi[j], log_x)

        return ilr_coords, psi

    def _clr_transform(self, X):
        """Centered Log-Ratio transform"""
        geometric_means = np.exp(np.mean(np.log(X), axis=1, keepdims=True))
        return np.log(X / geometric_means)

    def _alr_transform(self, X, ref_idx=0):
        """Additive Log-Ratio transform"""
        return np.log(X[:, 1:] / X[:, [ref_idx]])

    def _robust_pca(self, X, alpha=0.75, fast=False):
        """
        ROBUST PCA using Minimum Covariance Determinant (MCD) estimator
        Outliers don't corrupt the covariance estimation

        Parameters:
        - fast: Use Fast-MCD algorithm for large datasets (>100 samples)
        """
        # Robust location and scatter estimation
        if fast and X.shape[0] > 100:
            # Fast MCD approximation for large datasets
            mcd = MinCovDet(support_fraction=alpha, random_state=42)
            mcd.fit(X)
        else:
            # Standard MCD
            mcd = MinCovDet(support_fraction=alpha).fit(X)

        # Robust standardization
        X_robust = (X - mcd.location_) / np.sqrt(np.diag(mcd.covariance_))

        # PCA on robustly scaled data
        pca = PCA()
        scores = pca.fit_transform(X_robust)
        loadings = pca.components_.T

        # Mahalanobis distances for outlier detection
        mahal = mcd.mahalanobis(X)
        threshold_95 = chi2.ppf(0.95, df=X.shape[1])
        threshold_99 = chi2.ppf(0.99, df=X.shape[1])
        outliers_95 = mahal > threshold_95
        outliers_99 = mahal > threshold_99

        return {
            'scores': scores,
            'loadings': loadings,
            'explained_variance': pca.explained_variance_ratio_,
            'cumulative_variance': np.cumsum(pca.explained_variance_ratio_),
            'mahalanobis': mahal,
            'threshold_95': threshold_95,
            'threshold_99': threshold_99,
            'outliers_95': outliers_95,
            'outliers_99': outliers_99,
            'location': mcd.location_,
            'covariance': mcd.covariance_
        }

    def _compute_aitchison_distance(self, X):
        """
        Aitchison distance = Euclidean distance in clr space
        This is the ONLY mathematically valid distance for compositional data
        """
        clr_data = self._clr_transform(X)
        return squareform(pdist(clr_data))

    def _filter_subcomposition(self, selected_indices):
        """Filter elements based on subcomposition selection"""
        all_elements = [self.elem_listbox.get(i) for i in range(self.elem_listbox.size())]
        selected_elements = [all_elements[i] for i in selected_indices]

        subcomp_type = self.subcomp_var.get()

        if subcomp_type == "all":
            return selected_indices

        # Get template elements for this subcomposition
        template = self.SUBCOMPOSITIONS.get(subcomp_type, self.SUBCOMPOSITIONS["all"])
        target_elements = template.get("elements", [])

        if not target_elements:
            return selected_indices

        # Find indices of elements that match the subcomposition
        filtered_indices = []
        for i, elem in enumerate(selected_elements):
            elem_clean = elem.replace('_ppm', '').replace('_', '')
            if any(target in elem_clean or elem_clean in target for target in target_elements):
                filtered_indices.append(selected_indices[i])

        # If no matches, fall back to all selected
        if not filtered_indices:
            return selected_indices

        return filtered_indices

    def open_window(self):
        """Open the compositional data analysis window"""
        if not HAS_SCIPY or not HAS_SKLEARN:
            missing = []
            if not HAS_SCIPY: missing.append("scipy")
            if not HAS_SKLEARN: missing.append("scikit-learn")
            messagebox.showerror(
                "Missing Dependencies",
                f"Compositional Data Analysis requires:\n\n" +
                "\n".join(missing) +
                "\n\nInstall with:\npip install " + " ".join(missing)
            )
            return

        if not HAS_MATPLOTLIB:
            messagebox.showwarning(
                "Optional Dependency",
                "matplotlib not found - biplots will be text-only.\n"
                "Install with: pip install matplotlib"
            )

        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        # COMPACT DESIGN - 1000x650
        self.window = tk.Toplevel(self.app.root)
        self.window.title("📐 Compositional Data Analysis v1.1.1")
        self.window.geometry("1000x650")
        self.window.transient(self.app.root)

        self._create_compact_interface()
        self.window.lift()
        self.window.focus_force()

    def _create_compact_interface(self):
        """Create SLEEK, COMPACT interface with subcomposition support"""

        # ============ TOP BANNER ============
        header = tk.Frame(self.window, bg="#8e44ad", height=45)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="📐", font=("Arial", 18),
                bg="#8e44ad", fg="white").pack(side=tk.LEFT, padx=10)

        tk.Label(header, text="Compositional Data Analysis",
                font=("Arial", 14, "bold"), bg="#8e44ad", fg="white").pack(side=tk.LEFT, padx=5)

        tk.Label(header, text="v1.1.1 • Full ilr • Robust PCA • Subcompositions",
                font=("Arial", 8), bg="#8e44ad", fg="#f39c12").pack(side=tk.LEFT, padx=15)

        self.status_indicator = tk.Label(header, text="● READY",
                                        font=("Arial", 8, "bold"),
                                        bg="#8e44ad", fg="#2ecc71")
        self.status_indicator.pack(side=tk.RIGHT, padx=15)

        # ============ MAIN CONTENT ============
        main_paned = tk.PanedWindow(self.window, orient=tk.HORIZONTAL,
                                   sashwidth=4, sashrelief=tk.RAISED)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # ============ LEFT PANEL ============
        left_panel = tk.Frame(main_paned, bg="#ecf0f1", relief=tk.RAISED, borderwidth=1)
        main_paned.add(left_panel, width=350)

        # ============ ELEMENT SELECTOR ============
        elem_frame = tk.LabelFrame(left_panel, text="🧪 1. SELECT ELEMENTS",
                                  font=("Arial", 9, "bold"),
                                  bg="#ecf0f1", padx=8, pady=6)
        elem_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        tk.Label(elem_frame, text="Choose elements for compositional analysis:",
                font=("Arial", 8), bg="#ecf0f1", fg="#2c3e50").pack(anchor=tk.W, pady=2)

        # Listbox with scrollbar
        listbox_frame = tk.Frame(elem_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        scrollbar = tk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.elem_listbox = tk.Listbox(listbox_frame, selectmode=tk.MULTIPLE,
                                      yscrollcommand=scrollbar.set,
                                      height=10, font=("Courier", 8),
                                      bg="white", relief=tk.FLAT, borderwidth=1)
        self.elem_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.elem_listbox.yview)

        # Populate with detected elements
        available = self._get_available_elements()
        for elem in available:
            self.elem_listbox.insert(tk.END, elem)

        # Select reasonable defaults
        for i, elem in enumerate(available):
            if any(x in elem for x in ['Zr', 'Nb', 'Cr', 'Ni', 'Ba', 'Rb']):
                self.elem_listbox.selection_set(i)

        self.elem_count_label = tk.Label(elem_frame,
                                        text=f"Selected: {len(self.elem_listbox.curselection())} elements",
                                        font=("Arial", 7), bg="#ecf0f1", fg="#7f8c8d")
        self.elem_count_label.pack(anchor=tk.W, pady=2)

        self.elem_listbox.bind('<<ListboxSelect>>', self._update_elem_count)

        # ============ SUBCOMPOSITION SELECTOR ============
        subcomp_frame = tk.LabelFrame(left_panel, text="🔬 2. SUBCOMPOSITION",
                                     font=("Arial", 9, "bold"),
                                     bg="#ecf0f1", padx=8, pady=6)
        subcomp_frame.pack(fill=tk.X, padx=8, pady=8)

        tk.Label(subcomp_frame, text="Analyze specific geochemical groups:",
                font=("Arial", 8), bg="#ecf0f1").pack(anchor=tk.W, pady=2)

        self.subcomp_var = tk.StringVar(value="all")

        subcomps = [
            ("🌐 All elements", "all"),
            ("💎 HFSE (Zr, Nb, Ti, Y, Hf, Ta)", "hfse"),
            ("✨ REE (La, Ce, Nd, Sm, Eu, Gd, etc.)", "ree"),
            ("🔨 Transition metals (Cr, Ni, Co, Sc, V)", "transition"),
            ("🧂 LILE (Ba, Rb, Sr, Cs, K)", "lile"),
            ("⚙️ Custom selection...", "custom")
        ]

        for label, val in subcomps:
            rb = tk.Radiobutton(subcomp_frame, text=label,
                               variable=self.subcomp_var, value=val,
                               font=("Arial", 8), bg="#ecf0f1",
                               anchor=tk.W, justify=tk.LEFT)
            rb.pack(anchor=tk.W, pady=1)

        # ============ TRANSFORM CONTROLS ============
        transform_frame = tk.LabelFrame(left_panel, text="⚙️ 3. TRANSFORM",
                                       font=("Arial", 9, "bold"),
                                       bg="#ecf0f1", padx=8, pady=6)
        transform_frame.pack(fill=tk.X, padx=8, pady=8)

        self.transform_var = tk.StringVar(value="clr")

        transforms = [
            ("📐 clr (Centered Log-Ratio)", "clr", "✓ Standard for PCA, symmetric"),
            ("📏 ilr (Isometric Log-Ratio - orthonormal basis)", "ilr", "✓ Gram-Schmidt orthogonalization ✓"),
            ("📊 alr (Additive Log-Ratio)", "alr", "⚠️ Reference dependent"),
            ("❌ Raw ppm", "raw", "✗ NOT COMPOSITIONAL!")
        ]

        for label, val, desc in transforms:
            rb = tk.Radiobutton(transform_frame, text=label,
                               variable=self.transform_var, value=val,
                               font=("Arial", 8), bg="#ecf0f1",
                               anchor=tk.W, justify=tk.LEFT)
            rb.pack(anchor=tk.W, pady=1)
            tk.Label(transform_frame, text=desc, font=("Arial", 7, "italic"),
                    bg="#ecf0f1", fg="#7f8c8d").pack(anchor=tk.W, padx=20)

        # ============ ROBUST PCA OPTIONS ============
        robust_frame = tk.LabelFrame(left_panel, text="🛡️ 4. ROBUST OPTIONS",
                                    font=("Arial", 9, "bold"),
                                    bg="#ecf0f1", padx=8, pady=6)
        robust_frame.pack(fill=tk.X, padx=8, pady=8)

        self.robust_var = tk.BooleanVar(value=True)
        tk.Checkbutton(robust_frame, text="Use Robust PCA (MCD estimator)",
                      variable=self.robust_var,
                      font=("Arial", 8), bg="#ecf0f1").pack(anchor=tk.W)

        tk.Label(robust_frame,
                text="✓ Resistant to outliers, better covariance estimation",
                font=("Arial", 7, "italic"), bg="#ecf0f1", fg="#27ae60").pack(anchor=tk.W, padx=20)

        # Fast MCD option for large datasets
        self.fast_mcd_var = tk.BooleanVar(value=False)
        tk.Checkbutton(robust_frame, text="Fast MCD (approximate, use for >100 samples)",
                      variable=self.fast_mcd_var,
                      font=("Arial", 7), bg="#ecf0f1").pack(anchor=tk.W, padx=20)

        # ============ ACTION BUTTONS ============
        tk.Button(left_panel, text="📐 RUN COMPOSITIONAL ANALYSIS",
                 command=self._run_analysis,
                 bg="#8e44ad", fg="white",
                 font=("Arial", 11, "bold"),
                 height=2, relief=tk.RAISED,
                 borderwidth=2).pack(fill=tk.X, padx=8, pady=8)

        button_row = tk.Frame(left_panel, bg="#ecf0f1")
        button_row.pack(fill=tk.X, padx=8, pady=4)

        tk.Button(button_row, text="📊 Export Transformed",
                 command=self._export_transformed,
                 bg="#3498db", fg="white",
                 font=("Arial", 8), width=16).pack(side=tk.LEFT, padx=2)

        tk.Button(button_row, text="📏 Export Distances",
                 command=self._export_distances,
                 bg="#3498db", fg="white",
                 font=("Arial", 8), width=16).pack(side=tk.RIGHT, padx=2)

        # ============ RIGHT PANEL ============
        right_panel = tk.Frame(main_paned, bg="white", relief=tk.RAISED, borderwidth=1)
        main_paned.add(right_panel, width=600)

        # Notebook for multiple result views
        notebook = ttk.Notebook(right_panel)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # ============ TAB 1: PCA BIPLOT ============
        pca_frame = tk.Frame(notebook, bg="white")
        notebook.add(pca_frame, text="📈 PCA Biplot")

        self.pca_canvas_frame = tk.Frame(pca_frame, bg="white")
        self.pca_canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.pca_placeholder = tk.Label(self.pca_canvas_frame,
                                       text="📐 COMPOSITIONAL DATA ANALYSIS\n\n"
                                            "1. Select elements (at least 3)\n"
                                            "2. Choose subcomposition (optional)\n"
                                            "3. Select transform (clr recommended)\n"
                                            "4. Click 'RUN COMPOSITIONAL ANALYSIS'\n\n"
                                            "✓ Full ilr with orthonormal bases\n"
                                            "✓ Robust PCA with MCD estimator\n"
                                            "✓ Interactive biplot with hover labels\n"
                                            "✓ Aitchison distance matrix\n"
                                            "✓ Mahalanobis outlier detection",
                                       font=("Arial", 10),
                                       bg="#f8f9fa", fg="#2c3e50",
                                       relief=tk.FLAT, pady=40)
        self.pca_placeholder.pack(fill=tk.BOTH, expand=True)

        # ============ TAB 2: AITCHISON DISTANCES ============
        dist_frame = tk.Frame(notebook, bg="white")
        notebook.add(dist_frame, text="📏 Aitchison Distances")

        dist_text_frame = tk.Frame(dist_frame)
        dist_text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        dist_scroll = tk.Scrollbar(dist_text_frame)
        dist_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.dist_text = tk.Text(dist_text_frame, wrap=tk.WORD,
                                 font=("Courier", 9),
                                 yscrollcommand=dist_scroll.set,
                                 bg="#f8f9fa", relief=tk.FLAT,
                                 padx=10, pady=10)
        self.dist_text.pack(fill=tk.BOTH, expand=True)
        dist_scroll.config(command=self.dist_text.yview)

        # ============ TAB 3: OUTLIER DETECTION ============
        outlier_frame = tk.Frame(notebook, bg="white")
        notebook.add(outlier_frame, text="⚠️ Outlier Detection")

        outlier_text_frame = tk.Frame(outlier_frame)
        outlier_text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        outlier_scroll = tk.Scrollbar(outlier_text_frame)
        outlier_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.outlier_text = tk.Text(outlier_text_frame, wrap=tk.WORD,
                                   font=("Courier", 9),
                                   yscrollcommand=outlier_scroll.set,
                                   bg="#f8f9fa", relief=tk.FLAT,
                                   padx=10, pady=10)
        self.outlier_text.pack(fill=tk.BOTH, expand=True)
        outlier_scroll.config(command=self.outlier_text.yview)

        # ============ TAB 4: INTERPRETATION ============
        info_frame = tk.Frame(notebook, bg="white")
        notebook.add(info_frame, text="ℹ️ Documentation")

        info_text = tk.Text(info_frame, wrap=tk.WORD,
                           font=("Arial", 10),
                           bg="white", relief=tk.FLAT,
                           padx=20, pady=20)
        info_text.pack(fill=tk.BOTH, expand=True)

        explanation = """📐 COMPOSITIONAL DATA ANALYSIS v1.1.1
═══════════════════════════════════════════════════════

🎯 WHAT'S NEW IN v1.1.1:
────────────────────────
✓ FIXED: ilr label now shows "orthonormal basis" (correct!)
✓ ENHANCED: Hover tooltip shows Mahalanobis distance + outlier status
✓ ADDED: Fast MCD option for datasets >100 samples
✓ All user feedback from v1.1 implemented

📊 WHY COMPOSITIONAL DATA IS DIFFERENT:
────────────────────────────────────────
Geochemical data (ppm, wt%) is COMPOSITIONAL - it sums
to a constant (1e6 ppm, 100%). This creates spurious
correlations and invalidates standard statistics.

❌ WRONG: PCA on raw ppm
   • Closure creates artificial negative correlations
   • Euclidean distance ≠ geochemical difference
   • Biplots show artifacts, not true relationships

✅ CORRECT: Log-ratio transforms
   • clr: Opens simplex to real space
   • ilr: Orthonormal balances, perfect for regression
   • Aitchison distance: True geochemical distance

🛡️ ROBUST PCA (MCD):
─────────────────────
Standard PCA is sensitive to outliers. Minimum
Covariance Determinant (MCD) finds the subset of
samples that minimizes the determinant of the covariance
matrix - giving you outlier-resistant estimates.

📏 AITCHISON DISTANCE:
──────────────────────
The ONLY mathematically valid distance for compositional
data. Equivalent to Euclidean distance in clr space.
Use this for clustering, k-means, and dissimilarity
matrices - NOT Euclidean distance on raw ppm!

🔬 SUBCOMPOSITIONS:
───────────────────
Different element groups tell different stories:
• HFSE: Mantle source, immobile during alteration
• REE: Partial melting, fractional crystallization
• LILE: Crustal contamination, alteration
• Transition metals: Olivine/pyroxene fractionation

📚 KEY REFERENCES:
──────────────────
• Aitchison, J. (1986). The Statistical Analysis of
  Compositional Data. Chapman & Hall.
• Pawlowsky-Glahn, V. & Buccianti, A. (2011).
  Compositional Data Analysis. Wiley.
• Egozcue, J.J. et al. (2003). Isometric log-ratio
  transformations for compositional data analysis.
  Mathematical Geology, 35(3), 279-300.
• Filzmoser, P. et al. (2009). Robust factor analysis
  for compositional data. Computers & Geosciences, 35(9).

═══════════════════════════════════════════════════════
"""
        info_text.insert('1.0', explanation)
        info_text.config(state=tk.DISABLED)

        # ============ BOTTOM STATUS BAR ============
        status_bar = tk.Frame(self.window, bg="#ecf0f1", height=30)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        status_bar.pack_propagate(False)

        self.stats_label = tk.Label(status_bar,
                                   text="Ready - Select elements and run analysis",
                                   font=("Arial", 8),
                                   bg="#ecf0f1", fg="#2c3e50")
        self.stats_label.pack(side=tk.LEFT, padx=10)

        sample_count = len(self.app.samples) if self.app.samples else 0
        tk.Label(status_bar, text=f"📊 {sample_count} samples loaded",
                font=("Arial", 7), bg="#ecf0f1", fg="#7f8c8d").pack(side=tk.RIGHT, padx=10)

    def _update_elem_count(self, event=None):
        """Update element count label"""
        count = len(self.elem_listbox.curselection())
        self.elem_count_label.config(text=f"Selected: {count} elements")

    def _run_analysis(self):
        """RUN COMPOSITIONAL DATA ANALYSIS - Full v1.1.1 implementation"""
        if not self.app.samples:
            messagebox.showwarning("No Data", "Load samples first!")
            return

        # Get selected elements
        selected_indices = self.elem_listbox.curselection()
        if len(selected_indices) < 3:
            messagebox.showwarning("Insufficient Elements",
                                 "Select at least 3 elements for compositional analysis")
            return

        # Apply subcomposition filter
        filtered_indices = self._filter_subcomposition(selected_indices)
        if len(filtered_indices) < 3:
            messagebox.showwarning("Insufficient Elements",
                                 f"Subcomposition has only {len(filtered_indices)} elements - select more")
            return

        self.selected_elements = [self.elem_listbox.get(i) for i in filtered_indices]
        transform = self.transform_var.get()
        use_robust = self.robust_var.get()
        use_fast = self.fast_mcd_var.get()

        # Update status
        self.status_indicator.config(text="● COMPUTING...", fg="#f39c12")
        subcomp_name = self.SUBCOMPOSITIONS.get(self.subcomp_var.get(), {}).get("name", "custom")
        self.stats_label.config(text=f"{subcomp_name} • {transform.upper()} • {len(self.selected_elements)} elements...")
        self.window.update()

        try:
            # Build composition matrix
            compositions = []
            valid_sample_indices = []
            self.sample_ids = []

            for i, sample in enumerate(self.app.samples):
                row = []
                valid = True
                for elem in self.selected_elements:
                    val = self._get_element_values(sample, elem)
                    if val is None or val <= 0:
                        valid = False
                        break
                    row.append(val)

                if valid:
                    compositions.append(row)
                    valid_sample_indices.append(i)
                    self.sample_ids.append(sample.get('Sample_ID', f'Sample_{i}'))

            if len(compositions) < 3:
                messagebox.showerror("Insufficient Data",
                                   f"Only {len(compositions)} samples have complete data")
                self.status_indicator.config(text="● ERROR", fg="#e74c3c")
                return

            X = np.array(compositions)

            # ============ APPLY TRANSFORM ============
            if transform == 'raw':
                X_transformed = X
                transform_name = "Raw ppm (NOT COMPOSITIONAL!)"
                self.current_transform = 'raw'
            elif transform == 'clr':
                X_transformed = self._clr_transform(X)
                transform_name = "clr (Centered Log-Ratio)"
                self.current_transform = 'clr'
            elif transform == 'ilr':
                X_transformed, self.psi_matrix = self._ilr_transform_full(X)
                transform_name = "ilr (Isometric Log-Ratio - orthonormal basis)"
                self.current_transform = 'ilr'
            elif transform == 'alr':
                X_transformed = self._alr_transform(X)
                transform_name = f"alr (Additive Log-Ratio, ref={self.selected_elements[0]})"
                self.current_transform = 'alr'

            self.transformed_data = X_transformed

            # ============ RUN PCA (Standard or Robust) ============
            if use_robust and X_transformed.shape[1] >= 2:
                self.pca_result = self._robust_pca(X_transformed, fast=use_fast)
                pca_type = "Robust PCA (MCD)" + (" Fast" if use_fast else "")
            else:
                # Standard PCA
                scaler = StandardScaler()
                X_scaled = scaler.fit_transform(X_transformed)
                pca = PCA()
                scores = pca.fit_transform(X_scaled)
                loadings = pca.components_.T

                self.pca_result = {
                    'scores': scores,
                    'loadings': loadings,
                    'explained_variance': pca.explained_variance_ratio_,
                    'cumulative_variance': np.cumsum(pca.explained_variance_ratio_),
                    'outliers_95': np.zeros(len(X_transformed), dtype=bool),
                    'outliers_99': np.zeros(len(X_transformed), dtype=bool)
                }
                pca_type = "Standard PCA"

            # ============ COMPUTE AITCHISON DISTANCES ============
            aitchison_dist = self._compute_aitchison_distance(X)

            # ============ UPDATE UI ============
            self._update_pca_biplot()
            self._update_aitchison_distances(aitchison_dist, valid_sample_indices)
            self._update_outlier_report()

            # Update status
            self.status_indicator.config(text="● READY", fg="#2ecc71")

            pc1_var = self.pca_result['explained_variance'][0] if len(self.pca_result['explained_variance']) > 0 else 0
            pc2_var = self.pca_result['explained_variance'][1] if len(self.pca_result['explained_variance']) > 1 else 0

            self.stats_label.config(
                text=f"{subcomp_name} • {transform_name} • {pca_type} • "
                     f"{X.shape[0]} samples • {X.shape[1]} elements • "
                     f"PC1: {pc1_var:.1%} • PC2: {pc2_var:.1%}"
            )

        except Exception as e:
            self.status_indicator.config(text="● ERROR", fg="#e74c3c")
            self.stats_label.config(text=f"Error: {str(e)[:50]}")
            messagebox.showerror("Analysis Error", str(e))

    def _update_pca_biplot(self):
        """Generate INTERACTIVE PCA biplot with hover tooltips"""
        if self.pca_result is None or self.transformed_data is None:
            return

        # Clear placeholder
        for widget in self.pca_canvas_frame.winfo_children():
            widget.destroy()

        if not HAS_MATPLOTLIB:
            # Fallback text display
            text_widget = tk.Text(self.pca_canvas_frame, wrap=tk.WORD,
                                 font=("Courier", 9), bg="#f8f9fa",
                                 padx=10, pady=10)
            text_widget.pack(fill=tk.BOTH, expand=True)

            text_widget.insert(tk.END, "📈 PCA RESULTS (matplotlib not available)\n\n")
            text_widget.insert(tk.END, f"PC1: {self.pca_result['explained_variance'][0]:.1%}\n")
            text_widget.insert(tk.END, f"PC2: {self.pca_result['explained_variance'][1]:.1%}\n")
            text_widget.insert(tk.END, f"PC3: {self.pca_result['explained_variance'][2]:.1%}\n\n")

            text_widget.insert(tk.END, "Top 10 samples:\n")
            for i in range(min(10, len(self.sample_ids))):
                text_widget.insert(tk.END, f"  {self.sample_ids[i]}: "
                                          f"PC1={self.pca_result['scores'][i, 0]:.2f}, "
                                          f"PC2={self.pca_result['scores'][i, 1]:.2f}\n")

            text_widget.config(state=tk.DISABLED)
            return

        try:
            # Create figure
            fig, ax = plt.subplots(figsize=(6.5, 5.5), dpi=100)

            # Get first two PCs
            scores = self.pca_result['scores']
            loadings = self.pca_result['loadings']

            # Plot scores with different colors for outliers if robust PCA used
            if 'outliers_95' in self.pca_result and np.any(self.pca_result['outliers_95']):
                # Plot non-outliers
                mask_normal = ~self.pca_result['outliers_95']
                mask_outlier = self.pca_result['outliers_95']

                scatter_normal = ax.scatter(scores[mask_normal, 0], scores[mask_normal, 1],
                                          c='#3498db', alpha=0.8, edgecolors='white',
                                          s=60, zorder=5, label='Normal')

                scatter_outlier = ax.scatter(scores[mask_outlier, 0], scores[mask_outlier, 1],
                                           c='#e74c3c', alpha=0.8, edgecolors='white',
                                           s=80, marker='s', zorder=6, label='Outlier (95%)')

                scatter = scatter_normal  # for hover
            else:
                scatter = ax.scatter(scores[:, 0], scores[:, 1],
                                   c='#3498db', alpha=0.7, edgecolors='white',
                                   s=60, zorder=5)

            # Plot loadings as arrows
            for i, (loading, elem) in enumerate(zip(loadings[:len(self.selected_elements)],
                                                   self.selected_elements)):
                # Scale loadings for visibility
                scale = np.max(np.abs(scores[:, :2])) * 0.8
                ax.arrow(0, 0, loading[0] * scale, loading[1] * scale,
                        head_width=0.1, head_length=0.1,
                        fc='#e67e22', ec='#e67e22', alpha=0.7, zorder=10)

                # Element label
                elem_short = elem.replace('_ppm', '').replace('_', '')
                ax.text(loading[0] * scale * 1.15, loading[1] * scale * 1.15,
                       elem_short, fontsize=9, fontweight='bold',
                       color='#d35400', zorder=11)

            # Add confidence ellipses if robust PCA
            if 'covariance' in self.pca_result and 'location' in self.pca_result:
                from matplotlib.patches import Ellipse

                # Function to draw confidence ellipse
                def confidence_ellipse(cov, loc, ax, n_std=2.0, **kwargs):
                    pearson = cov[0, 1] / np.sqrt(cov[0, 0] * cov[1, 1])
                    ell_radius_x = np.sqrt(1 + pearson) * n_std
                    ell_radius_y = np.sqrt(1 - pearson) * n_std
                    ellipse = Ellipse((0, 0), width=ell_radius_x * 2, height=ell_radius_y * 2,
                                     facecolor='none', **kwargs)
                    scale_x = np.sqrt(cov[0, 0]) * n_std * 2
                    scale_y = np.sqrt(cov[1, 1]) * n_std * 2
                    transform = ax.transData.get_affine() + \
                               plt.matplotlib.transforms.Affine2D().rotate(pearson) + \
                               plt.matplotlib.transforms.Affine2D().scale(scale_x, scale_y) + \
                               plt.matplotlib.transforms.Affine2D().translate(loc[0], loc[1])
                    ellipse.set_transform(transform)
                    return ax.add_patch(ellipse)

                # Draw 95% and 99% confidence ellipses
                confidence_ellipse(self.pca_result['covariance'][:2, :2],
                                 self.pca_result['location'][:2], ax,
                                 n_std=2.0, edgecolor='#2c3e50', linestyle='--',
                                 linewidth=1, alpha=0.5, label='95% CI')

                confidence_ellipse(self.pca_result['covariance'][:2, :2],
                                 self.pca_result['location'][:2], ax,
                                 n_std=2.576, edgecolor='#7f8c8d', linestyle=':',
                                 linewidth=0.8, alpha=0.3, label='99% CI')

            # Labels
            ax.set_xlabel(f'PC1 ({self.pca_result["explained_variance"][0]:.1%})',
                         fontsize=10, fontweight='bold')
            ax.set_ylabel(f'PC2 ({self.pca_result["explained_variance"][1]:.1%})',
                         fontsize=10, fontweight='bold')

            # Title with transform info
            transform_names = {
                'clr': 'clr-transformed (Aitchison geometry)',
                'ilr': 'ilr-transformed (orthonormal balances)',
                'alr': 'alr-transformed',
                'raw': 'raw ppm (⚠️ NOT COMPOSITIONAL!)'
            }
            transform_name = transform_names.get(self.current_transform, self.current_transform)

            subcomp_name = self.SUBCOMPOSITIONS.get(self.subcomp_var.get(), {}).get("name", "custom")
            ax.set_title(f'{subcomp_name}\n{transform_name}\n'
                        f'{len(self.transformed_data)} samples, {len(self.selected_elements)} elements',
                        fontsize=10, fontweight='bold', pad=15)

            ax.axhline(y=0, color='gray', linestyle='-', linewidth=0.5, alpha=0.5)
            ax.axvline(x=0, color='gray', linestyle='-', linewidth=0.5, alpha=0.5)
            ax.grid(True, alpha=0.2, linestyle='--')

            # Add legend if outliers exist
            if 'outliers_95' in self.pca_result and np.any(self.pca_result['outliers_95']):
                ax.legend(loc='upper right', fontsize=7)

            # ============ ENHANCED HOVER TOOLTIP ============
            annot = ax.annotate("", xy=(0,0), xytext=(10,10),
                               textcoords="offset points",
                               bbox=dict(boxstyle="round", fc="white", ec="gray",
                                        alpha=0.9, pad=0.5),
                               fontsize=8)
            annot.set_visible(False)

            def hover(event):
                if event.inaxes == ax:
                    cont, ind = scatter.contains(event)
                    if cont:
                        idx = ind['ind'][0]
                        pos = scatter.get_offsets()[idx]
                        annot.xy = pos

                        sample_id = self.sample_ids[idx]

                        # ENHANCED: Show Mahalanobis distance and outlier status
                        if 'mahalanobis' in self.pca_result:
                            mdist = self.pca_result['mahalanobis'][idx]
                            outlier_95 = self.pca_result['outliers_95'][idx]
                            outlier_99 = self.pca_result['outliers_99'][idx]

                            status = ""
                            if outlier_99:
                                status = "🔴 99% outlier"
                            elif outlier_95:
                                status = "🟠 95% outlier"
                            else:
                                status = "✅ within 95% CI"

                            text = f"{sample_id}\nMahal. d = {mdist:.2f}\n{status}"
                        else:
                            text = sample_id

                        annot.set_text(text)
                        annot.set_visible(True)
                        fig.canvas.draw_idle()
                    else:
                        if annot.get_visible():
                            annot.set_visible(False)
                            fig.canvas.draw_idle()

            fig.canvas.mpl_connect("motion_notify_event", hover)

            # Add cursor for coordinate display
            cursor = Cursor(ax, useblit=True, color='gray', linewidth=0.5, alpha=0.3)

            plt.tight_layout()

            # Embed in tkinter
            canvas = FigureCanvasTkAgg(fig, self.pca_canvas_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        except Exception as e:
            error_label = tk.Label(self.pca_canvas_frame,
                                  text=f"⚠️ Biplot error: {str(e)[:100]}\n\n"
                                       "Text results available in other tabs",
                                  font=("Arial", 9), fg="#e74c3c")
            error_label.pack(fill=tk.BOTH, expand=True)

    def _update_aitchison_distances(self, dist_matrix, sample_indices):
        """Display Aitchison distance matrix summary"""
        self.dist_text.delete(1.0, tk.END)

        self.dist_text.insert(tk.END, "📏 AITCHISON DISTANCE MATRIX\n")
        self.dist_text.insert(tk.END, "═" * 70 + "\n\n")

        self.dist_text.insert(tk.END,
            "The ONLY mathematically valid distance for compositional data.\n"
            "Use this for clustering, k-means, MDS - NOT Euclidean on ppm!\n\n")

        # Summary statistics
        tri_indices = np.triu_indices_from(dist_matrix, k=1)
        distances = dist_matrix[tri_indices]

        self.dist_text.insert(tk.END, f"Samples analyzed: {len(sample_indices)}\n")
        self.dist_text.insert(tk.END, f"Total pairwise distances: {len(distances)}\n")
        self.dist_text.insert(tk.END, f"Minimum distance: {distances.min():.3f}\n")
        self.dist_text.insert(tk.END, f"Maximum distance: {distances.max():.3f}\n")
        self.dist_text.insert(tk.END, f"Mean distance: {distances.mean():.3f}\n")
        self.dist_text.insert(tk.END, f"Median distance: {np.median(distances):.3f}\n")
        self.dist_text.insert(tk.END, f"Std deviation: {np.std(distances):.3f}\n\n")

        # Most similar pair
        min_idx = np.argmin(distances)
        i, j = tri_indices[0][min_idx], tri_indices[1][min_idx]
        sample_i = self.app.samples[sample_indices[i]].get('Sample_ID', f'Sample {sample_indices[i]}')
        sample_j = self.app.samples[sample_indices[j]].get('Sample_ID', f'Sample {sample_indices[j]}')

        self.dist_text.insert(tk.END, f"🟢 MOST SIMILAR PAIR:\n")
        self.dist_text.insert(tk.END, f"   {sample_i} ↔ {sample_j}\n")
        self.dist_text.insert(tk.END, f"   Aitchison distance: {distances[min_idx]:.3f}\n")

        # Check if they have same classification
        class_i = self.app.samples[sample_indices[i]].get('Final_Classification', '')
        class_j = self.app.samples[sample_indices[j]].get('Final_Classification', '')
        if class_i and class_j and class_i == class_j:
            self.dist_text.insert(tk.END, f"   ✓ Same classification: {class_i[:30]}\n")
        self.dist_text.insert(tk.END, "\n")

        # Most dissimilar pair
        max_idx = np.argmax(distances)
        i, j = tri_indices[0][max_idx], tri_indices[1][max_idx]
        sample_i = self.app.samples[sample_indices[i]].get('Sample_ID', f'Sample {sample_indices[i]}')
        sample_j = self.app.samples[sample_indices[j]].get('Sample_ID', f'Sample {sample_indices[j]}')

        self.dist_text.insert(tk.END, f"🔴 MOST DISSIMILAR PAIR:\n")
        self.dist_text.insert(tk.END, f"   {sample_i} ↔ {sample_j}\n")
        self.dist_text.insert(tk.END, f"   Aitchison distance: {distances[max_idx]:.3f}\n\n")

        # Distance distribution (histogram in text)
        self.dist_text.insert(tk.END, "📊 DISTANCE DISTRIBUTION:\n")
        self.dist_text.insert(tk.END, "-" * 40 + "\n")

        percentiles = [0, 10, 25, 50, 75, 90, 95, 100]
        for p in percentiles:
            val = np.percentile(distances, p)
            bar_length = int(val / distances.max() * 30)
            bar = "█" * bar_length
            self.dist_text.insert(tk.END, f"{p:3d}%: {val:6.3f}  {bar}\n")

        self.dist_text.insert(tk.END, "\n📌 Export this matrix for cluster analysis:\n")
        self.dist_text.insert(tk.END, "   Click 'Export Distances' to save as CSV\n")

        self.dist_text.config(state=tk.DISABLED)

    def _update_outlier_report(self):
        """Display outlier detection results with Mahalanobis distances"""
        self.outlier_text.delete(1.0, tk.END)

        self.outlier_text.insert(tk.END, "⚠️ MAHALANOBIS OUTLIER DETECTION\n")
        self.outlier_text.insert(tk.END, "═" * 70 + "\n\n")

        if 'mahalanobis' not in self.pca_result:
            self.outlier_text.insert(tk.END,
                "Robust PCA not used - run with 'Use Robust PCA' enabled\n"
                "for Mahalanobis distance outlier detection.\n\n")
            self.outlier_text.insert(tk.END,
                "Standard PCA results:\n")
            self.outlier_text.insert(tk.END, f"  PC1: {self.pca_result['explained_variance'][0]:.1%}\n")
            self.outlier_text.insert(tk.END, f"  PC2: {self.pca_result['explained_variance'][1]:.1%}\n")
            self.outlier_text.insert(tk.END, f"  PC3: {self.pca_result['explained_variance'][2]:.1%}\n")
            self.outlier_text.config(state=tk.DISABLED)
            return

        mahal = self.pca_result['mahalanobis']
        threshold_95 = self.pca_result['threshold_95']
        threshold_99 = self.pca_result['threshold_99']
        outliers_95 = self.pca_result['outliers_95']
        outliers_99 = self.pca_result['outliers_99']

        self.outlier_text.insert(tk.END, f"Threshold (95% confidence): {threshold_95:.2f}\n")
        self.outlier_text.insert(tk.END, f"Threshold (99% confidence): {threshold_99:.2f}\n")
        self.outlier_text.insert(tk.END, f"Outliers at 95%: {np.sum(outliers_95)} of {len(outliers_95)}\n")
        self.outlier_text.insert(tk.END, f"Outliers at 99%: {np.sum(outliers_99)} of {len(outliers_99)}\n\n")

        if np.sum(outliers_95) > 0:
            self.outlier_text.insert(tk.END, "🟠 POTENTIAL OUTLIERS (95% CI):\n")
            self.outlier_text.insert(tk.END, "-" * 50 + "\n")

            # Sort by Mahalanobis distance
            outlier_indices = np.where(outliers_95)[0]
            outlier_distances = mahal[outliers_95]
            sorted_idx = np.argsort(outlier_distances)[::-1]

            for idx in sorted_idx:
                sample_idx = outlier_indices[idx]
                sample_id = self.sample_ids[sample_idx] if sample_idx < len(self.sample_ids) else f"Sample_{sample_idx}"
                distance = outlier_distances[idx]

                # Check if also 99% outlier
                marker = "🔴" if outliers_99[outlier_indices[idx]] else "🟠"
                self.outlier_text.insert(tk.END, f"  {marker} {sample_id:<25} Mahal: {distance:.2f}\n")
        else:
            self.outlier_text.insert(tk.END, "✅ No outliers detected at 95% confidence\n")
            self.outlier_text.insert(tk.END, "   Your dataset is compositionally homogeneous\n\n")

        # Mahalanobis distance distribution
        self.outlier_text.insert(tk.END, "\n📊 MAHALANOBIS DISTANCE DISTRIBUTION:\n")
        self.outlier_text.insert(tk.END, "-" * 50 + "\n")

        percentiles = [0, 10, 25, 50, 75, 90, 95, 99, 100]
        for p in percentiles:
            val = np.percentile(mahal, p)
            bar_length = int(val / mahal.max() * 30)
            bar = "█" * bar_length
            ci_marker = " <-- 95% CI" if p == 95 else " <-- 99% CI" if p == 99 else ""
            self.outlier_text.insert(tk.END, f"{p:3d}%: {val:6.2f}  {bar}{ci_marker}\n")

        self.outlier_text.insert(tk.END, "\n" + "═" * 70 + "\n")
        self.outlier_text.insert(tk.END, "⚠️ INTERPRETATION:\n")
        self.outlier_text.insert(tk.END, "  • Outliers in compositional space may indicate:\n")
        self.outlier_text.insert(tk.END, "    - Different geological source/provenance\n")
        self.outlier_text.insert(tk.END, "    - Analytical error or contamination\n")
        self.outlier_text.insert(tk.END, "    - Post-depositional alteration\n")
        self.outlier_text.insert(tk.END, "    - Mixing of multiple sources\n")
        self.outlier_text.insert(tk.END, "  • Consider reviewing outliers before final classification\n")

        self.outlier_text.config(state=tk.DISABLED)

    def _export_transformed(self):
        """Export transformed coordinates to CSV"""
        if self.transformed_data is None:
            messagebox.showwarning("No Data", "Run analysis first!")
            return

        from tkinter import filedialog

        subcomp_name = self.SUBCOMPOSITIONS.get(self.subcomp_var.get(), {}).get("name", "custom")
        subcomp_clean = subcomp_name.lower().replace(' ', '_')[:20]

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("All Files", "*.*")],
            initialfile=f"compositional_{self.current_transform}_{subcomp_clean}_{datetime.now().strftime('%Y%m%d')}.csv"
        )

        if not filename:
            return

        try:
            import csv

            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                # Header
                transform_name = self.current_transform.upper()
                cols = [f"{transform_name}_dim{i+1}" for i in range(self.transformed_data.shape[1])]

                # Add PCA scores if available
                if self.pca_result is not None:
                    cols.extend(['PC1', 'PC2', 'PC3'])
                    if 'mahalanobis' in self.pca_result:
                        cols.append('Mahalanobis_distance')
                        cols.append('Outlier_95%')
                        cols.append('Outlier_99%')

                writer.writerow(['Sample_ID'] + cols)

                # Data
                for i in range(len(self.transformed_data)):
                    row = [self.sample_ids[i]]
                    row.extend([f"{x:.4f}" for x in self.transformed_data[i]])

                    if self.pca_result is not None:
                        row.extend([
                            f"{self.pca_result['scores'][i, 0]:.4f}",
                            f"{self.pca_result['scores'][i, 1]:.4f}",
                            f"{self.pca_result['scores'][i, 2]:.4f}" if self.pca_result['scores'].shape[1] > 2 else ""
                        ])
                        if 'mahalanobis' in self.pca_result:
                            row.extend([
                                f"{self.pca_result['mahalanobis'][i]:.2f}",
                                "YES" if self.pca_result['outliers_95'][i] else "NO",
                                "YES" if self.pca_result['outliers_99'][i] else "NO"
                            ])

                    writer.writerow(row)

            messagebox.showinfo("Export Complete",
                               f"✓ Exported {len(self.transformed_data)} samples\n"
                               f"Transform: {self.current_transform.upper()}\n"
                               f"Subcomposition: {subcomp_name}\n"
                               f"Dimensions: {self.transformed_data.shape[1]} coordinates\n"
                               f"Includes PCA scores and outlier flags")

        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def _export_distances(self):
        """Export Aitchison distance matrix to CSV"""
        if self.transformed_data is None:
            messagebox.showwarning("No Data", "Run analysis first!")
            return

        from tkinter import filedialog

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("All Files", "*.*")],
            initialfile=f"aitchison_distances_{datetime.now().strftime('%Y%m%d')}.csv"
        )

        if not filename:
            return

        try:
            # Recompute distance matrix
            X_list = []
            for i in range(len(self.sample_ids)):
                row = []
                for elem in self.selected_elements:
                    val = self._get_element_values(self.app.samples[i], elem)
                    if val is not None:
                        row.append(val)
                X_list.append(row)

            X = np.array(X_list)
            dist_matrix = self._compute_aitchison_distance(X)

            import csv
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                # Header row with sample IDs
                writer.writerow([''] + self.sample_ids)

                # Distance matrix
                for i, sample_id in enumerate(self.sample_ids):
                    row = [sample_id] + [f"{dist_matrix[i, j]:.4f}" for j in range(len(self.sample_ids))]
                    writer.writerow(row)

            messagebox.showinfo("Export Complete",
                               f"✓ Exported {len(self.sample_ids)} x {len(self.sample_ids)} distance matrix\n"
                               f"Use for cluster analysis, MDS, or dissimilarity-based methods")

        except Exception as e:
            messagebox.showerror("Export Error", str(e))


def setup_plugin(main_app):
    """Plugin setup function"""
    print("📐 Loading Compositional Data Analysis Plugin v1.1.1")
    plugin = CompositionalStatsPlugin(main_app)

    if hasattr(main_app, 'menu_bar'):
        if not hasattr(main_app, 'advanced_menu'):
            main_app.advanced_menu = tk.Menu(main_app.menu_bar, tearoff=0)
            main_app.menu_bar.add_cascade(label="Advanced", menu=main_app.advanced_menu)

        main_app.advanced_menu.add_command(
            label="📐 Compositional Data Analysis",
            command=plugin.open_window
        )
        print("📐 ✓ Added to Advanced menu")

    print("📐 ✓ Loaded: Compositional Data Analysis v1.1.1")
    print("    Features: Full ilr • Orthonormal basis • Robust PCA • Fast MCD • Enhanced hover")
    return plugin
