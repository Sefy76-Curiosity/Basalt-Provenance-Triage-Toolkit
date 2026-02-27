"""
PCA+LDA Explorer v2.1 - Complete Statistical & ML Suite
Full feature set including correlation, clustering, regression, t-SNE, and statistical tests

Author: Sefy Levy
License: Free for research & education
Version: 2.1 (February 16, 2026)
"""

PLUGIN_INFO = {
    "category": "software",
    "field": "Geology & Geochemistry",
    "id": "pca_lda_explorer",
    "name": "PCA+LDA Explorer Pro",
    "description": "Complete statistical suite - PCA, LDA, PLS-DA, RF, SVM, t-SNE, Clustering, Correlation, Regression, Statistical Tests",
    "icon": "📊",
    "version": "2.1",
    "date": "2026-02-16",
    "requires": ["scikit-learn", "matplotlib", "numpy", "pandas", "scipy", "seaborn"],
    "optional": ["xgboost", "imbalanced-learn", "plotly", "openpyxl", "statsmodels"],
    "author": "Sefy Levy"
}

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import pandas as pd
import traceback
import json
import zipfile
from pathlib import Path
from datetime import datetime
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CORE IMPORTS
# ============================================================================

try:
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.impute import SimpleImputer, KNNImputer
    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
    from sklearn.cross_decomposition import PLSRegression
    from sklearn.ensemble import RandomForestClassifier, IsolationForest, RandomForestRegressor
    from sklearn.svm import SVC
    from sklearn.model_selection import cross_val_score, StratifiedKFold, GridSearchCV, train_test_split
    from sklearn.metrics import (accuracy_score, confusion_matrix,
                                balanced_accuracy_score, cohen_kappa_score,
                                f1_score, r2_score, mean_squared_error, mean_absolute_error,
                                silhouette_score, davies_bouldin_score)
    from sklearn.inspection import permutation_importance
    from sklearn.multiclass import OneVsRestClassifier
    from sklearn.cluster import DBSCAN, KMeans, AgglomerativeClustering
    from sklearn.neighbors import LocalOutlierFactor
    from sklearn.covariance import MinCovDet
    from sklearn.linear_model import LinearRegression, Ridge, Lasso  # FIXED: Added missing imports
    from sklearn.manifold import TSNE
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

try:
    from scipy import stats
    from scipy.stats import (ttest_ind, ttest_rel, ttest_1samp, f_oneway,
                            pearsonr, spearmanr, kendalltau, mannwhitneyu,
                            shapiro, levene, normaltest)
    from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    from statsmodels.stats.multicomp import pairwise_tukeyhsd
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False

try:
    from imblearn.ensemble import BalancedRandomForestClassifier
    HAS_IMBALANCED = True
except ImportError:
    HAS_IMBALANCED = False

try:
    import matplotlib
    matplotlib.use('TkAgg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    from matplotlib.patches import Ellipse
    import matplotlib.cm as cm
    from mpl_toolkits.mplot3d import Axes3D
    import seaborn as sns
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


# ============================================================================
# TOOLTIP
# ============================================================================

class ToolTip:
    """Simple tooltip"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind('<Enter>', self.show_tip)
        widget.bind('<Leave>', self.hide_tip)

    def show_tip(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tip_window = tk.Toplevel(self.widget)
        self.tip_window.wm_overrideredirect(True)
        self.tip_window.wm_geometry(f"+{x}+{y}")
        tk.Label(self.tip_window, text=self.text, justify=tk.LEFT,
                background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                font=("Arial", 8)).pack()

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


# ============================================================================
# PLS-DA WITH VIP (FIXED: Handles 1D case)
# ============================================================================

class PLSDAWithVIP:
    """PLS-DA with per-class VIP scores - FIXED for 1D case"""
    def __init__(self, n_components=2):
        self.n_components = n_components
        self.classes_ = None
        self.vip_per_class = {}
        self.model = None

    def fit(self, X, y, feature_names=None):
        self.classes_ = np.unique(y)
        le = LabelEncoder()
        y_encoded = le.fit_transform(y)

        base_pls = PLSRegression(n_components=min(self.n_components, X.shape[1]))
        self.model = OneVsRestClassifier(base_pls)
        self.model.fit(X, y_encoded)

        # Calculate VIP for each class
        for i, class_name in enumerate(self.classes_):
            if i < len(self.model.estimators_):
                pls = self.model.estimators_[i]
                if hasattr(pls, 'x_weights_'):
                    W = pls.x_weights_
                    # FIXED: Handle 1D case
                    if W.ndim == 1:
                        W = W.reshape(-1, 1)

                    T = pls.x_scores_
                    if T.ndim == 1:
                        T = T.reshape(-1, 1)

                    SS = np.sum(T ** 2, axis=0)
                    vip = np.zeros(X.shape[1])
                    for j in range(X.shape[1]):
                        weight = np.sum(W[j, :]**2 * SS)
                        vip[j] = np.sqrt(X.shape[1] * weight / np.sum(SS)) if np.sum(SS) > 0 else 0
                    self.vip_per_class[class_name] = vip
        return self

    def predict(self, X):
        if self.model is None:
            return np.array([])
        return self.classes_[self.model.predict(X).astype(int)]


# ============================================================================
# OUTLIER DIALOG
# ============================================================================

class OutlierDialog:
    """Compact outlier dialog with all methods"""
    def __init__(self, parent, X, sample_ids, group_labels, on_exclude):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Outlier Detection")
        self.dialog.geometry("800x650")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.X = X
        self.sample_ids = sample_ids
        self.group_labels = group_labels
        self.on_exclude = on_exclude
        self.outlier_masks = {}
        self.check_vars = {}

        self._create_ui()
        self._detect_outliers()

    def _create_ui(self):
        # Notebook for multiple views
        self.notebook = ttk.Notebook(self.dialog)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.consensus_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.consensus_frame, text="Consensus")

        # Method tabs
        self.method_frames = {}
        for method in ['Isolation Forest', 'Robust Mahal', 'DBSCAN', 'LOF']:
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=method)
            self.method_frames[method] = frame

        # Buttons
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        select_btn = ttk.Button(btn_frame, text="Select Consensus",
                command=self._select_consensus)
        select_btn.pack(side=tk.LEFT, padx=2)
        ToolTip(select_btn, "Select samples flagged by ≥2 methods")

        deselect_btn = ttk.Button(btn_frame, text="Deselect All",
                command=self._deselect_all)
        deselect_btn.pack(side=tk.LEFT, padx=2)
        ToolTip(deselect_btn, "Clear all selections")

        export_btn = ttk.Button(btn_frame, text="Export CSV",
                command=self._export_csv)
        export_btn.pack(side=tk.LEFT, padx=2)
        ToolTip(export_btn, "Export outlier status to CSV")

        exclude_btn = ttk.Button(btn_frame, text="Exclude Selected",
                command=self._exclude)
        exclude_btn.pack(side=tk.RIGHT, padx=2)
        ToolTip(exclude_btn, "Remove selected samples from analysis")

    def _detect_outliers(self):
        # Isolation Forest
        iso = IsolationForest(contamination=0.1, random_state=42)
        self.outlier_masks['IF'] = iso.fit_predict(self.X) == -1

        # Robust Mahal
        try:
            mcd = MinCovDet().fit(self.X)
            mahal = mcd.mahalanobis(self.X)
            self.outlier_masks['MCD'] = mahal > np.percentile(mahal, 95)
        except:
            self.outlier_masks['MCD'] = np.zeros(len(self.X), dtype=bool)

        # DBSCAN
        db = DBSCAN(eps=0.5, min_samples=5)
        self.outlier_masks['DBSCAN'] = db.fit_predict(self.X) == -1

        # LOF
        lof = LocalOutlierFactor(contamination=0.1)
        self.outlier_masks['LOF'] = lof.fit_predict(self.X) == -1

        for widget in self.consensus_frame.winfo_children():
            widget.destroy()

        self._populate_consensus()
        self._populate_method_tabs()

    def _populate_consensus(self):
        masks = np.array([self.outlier_masks['IF'], self.outlier_masks['MCD'],
                        self.outlier_masks['DBSCAN'], self.outlier_masks['LOF']])
        consensus = np.sum(masks, axis=0) >= 2

        frame = ttk.Frame(self.consensus_frame)
        frame.pack(fill=tk.BOTH, expand=True)

        vsb = ttk.Scrollbar(frame)
        hsb = ttk.Scrollbar(frame, orient=tk.HORIZONTAL)

        columns = ["Select", "ID", "Group", "Flags", "IF", "MCD", "DBSCAN", "LOF"]
        self.tree = ttk.Treeview(frame, columns=columns, show="headings",
                                yscrollcommand=vsb.set, xscrollcommand=hsb.set,
                                height=15)

        self.tree.heading("Select", text="✓")
        self.tree.column("Select", width=30, anchor="center")
        for col in columns[1:]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=60 if len(col)<=3 else 80)

        self.tree.bind("<Button-1>", self._on_click)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)

        self.check_vars = {}
        for i, (sid, group) in enumerate(zip(self.sample_ids, self.group_labels)):
            flags = sum([self.outlier_masks['IF'][i], self.outlier_masks['MCD'][i],
                        self.outlier_masks['DBSCAN'][i], self.outlier_masks['LOF'][i]])
            consensus_value = bool(consensus[i])
            self.check_vars[i] = tk.BooleanVar(value=consensus_value)

            values = [
                "☑" if consensus_value else "☐",
                sid[:15] + ".." if len(sid) > 15 else sid,
                group[:10] + ".." if len(group) > 10 else group,
                f"{flags}/4",
                "⚠️" if self.outlier_masks['IF'][i] else "✓",
                "⚠️" if self.outlier_masks['MCD'][i] else "✓",
                "⚠️" if self.outlier_masks['DBSCAN'][i] else "✓",
                "⚠️" if self.outlier_masks['LOF'][i] else "✓",
            ]

            tag = 'outlier' if flags >= 2 else 'normal'
            self.tree.insert("", "end", values=values, tags=(tag,))

        self.tree.tag_configure('outlier', background='#fff3cd')

    def _populate_method_tabs(self):
        for method, key in [('Isolation Forest', 'IF'), ('Robust Mahal', 'MCD'),
                           ('DBSCAN', 'DBSCAN'), ('LOF', 'LOF')]:
            frame = self.method_frames[method]
            for w in frame.winfo_children():
                w.destroy()

            text = tk.Text(frame, height=10, font=("Courier", 9))
            scroll = ttk.Scrollbar(frame, command=text.yview)
            text.config(yscrollcommand=scroll.set)

            text.insert(tk.END, f"{method} Results:\n\n")
            for i, (sid, group) in enumerate(zip(self.sample_ids, self.group_labels)):
                if self.outlier_masks[key][i]:
                    text.insert(tk.END, f"⚠️ {sid} ({group})\n")

            text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def _on_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell" and self.tree.identify_column(event.x) == "#1":
            item = self.tree.identify_row(event.y)
            if item:
                idx = self.tree.index(item)
                if idx in self.check_vars:
                    current = self.check_vars[idx].get()
                    self.check_vars[idx].set(not current)
                    self.tree.set(item, column="Select", value="☑" if not current else "☐")

    def _select_consensus(self):
        for item in self.tree.get_children():
            idx = self.tree.index(item)
            if idx in self.check_vars:
                self.check_vars[idx].set(True)
                self.tree.set(item, column="Select", value="☑")

    def _deselect_all(self):
        for item in self.tree.get_children():
            idx = self.tree.index(item)
            if idx in self.check_vars:
                self.check_vars[idx].set(False)
                self.tree.set(item, column="Select", value="☐")

    def _export_csv(self):
        data = []
        for i in range(len(self.sample_ids)):
            data.append({
                'Sample_ID': self.sample_ids[i],
                'Group': self.group_labels[i],
                'Isolation_Forest': self.outlier_masks['IF'][i],
                'Robust_Mahal': self.outlier_masks['MCD'][i],
                'DBSCAN': self.outlier_masks['DBSCAN'][i],
                'LOF': self.outlier_masks['LOF'][i],
                'Flag_Count': sum([self.outlier_masks['IF'][i], self.outlier_masks['MCD'][i],
                                  self.outlier_masks['DBSCAN'][i], self.outlier_masks['LOF'][i]])
            })

        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                           filetypes=[("CSV", "*.csv")])
        if path:
            pd.DataFrame(data).to_csv(path, index=False)
            messagebox.showinfo("Success", f"Exported to {Path(path).name}")

    def _exclude(self):
        exclude = [i for i, var in self.check_vars.items() if var.get()]
        if exclude and messagebox.askyesno("Confirm", f"Exclude {len(exclude)} samples?"):
            self.on_exclude(exclude)
            self.dialog.destroy()


# ============================================================================
# GROUP STATISTICS POPUP
# ============================================================================

class GroupStatisticsPopup:
    """Group statistics with export"""
    def __init__(self, parent, scores, group_labels, sample_ids, loadings=None, elements=None):
        self.popup = tk.Toplevel(parent)
        self.popup.title("Group Statistics")
        self.popup.geometry("700x500")

        notebook = ttk.Notebook(self.popup)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Statistics tab
        stats_tab = ttk.Frame(notebook)
        notebook.add(stats_tab, text="Statistics")
        self._create_stats_tab(stats_tab, scores, group_labels)

        # Centroids tab
        centroids_tab = ttk.Frame(notebook)
        notebook.add(centroids_tab, text="Centroids")
        self._create_centroids_tab(centroids_tab, scores, group_labels)

        # Export button
        ttk.Button(self.popup, text="Export to Excel",
                  command=lambda: self._export_excel(scores, group_labels, sample_ids,
                                                     loadings, elements)).pack(pady=5)

    def _create_stats_tab(self, parent, scores, group_labels):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True)

        vsb = ttk.Scrollbar(frame)
        hsb = ttk.Scrollbar(frame, orient=tk.HORIZONTAL)

        groups = list(set(group_labels))
        columns = ["Group", "N"] + [f"PC{i+1} Mean" for i in range(min(5, scores.shape[1]))]

        tree = ttk.Treeview(frame, columns=columns, show="headings",
                           yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        tree.heading("Group", text="Group")
        tree.heading("N", text="N")
        for i in range(min(5, scores.shape[1])):
            tree.heading(f"PC{i+1} Mean", text=f"PC{i+1}")

        for group in groups:
            mask = [g == group for g in group_labels]
            group_scores = scores[mask]
            values = [group, len(group_scores)]
            for i in range(min(5, scores.shape[1])):
                values.append(f"{group_scores[:, i].mean():.3f}")
            tree.insert("", "end", values=values)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)

    def _create_centroids_tab(self, parent, scores, group_labels):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True)

        vsb = ttk.Scrollbar(frame)
        hsb = ttk.Scrollbar(frame, orient=tk.HORIZONTAL)

        groups = list(set(group_labels))
        columns = ["Group"] + [f"PC{i+1}" for i in range(scores.shape[1])]

        tree = ttk.Treeview(frame, columns=columns, show="headings",
                           yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        tree.heading("Group", text="Group")
        for i in range(scores.shape[1]):
            tree.heading(f"PC{i+1}", text=f"PC{i+1}")

        for group in groups:
            mask = [g == group for g in group_labels]
            centroid = scores[mask].mean(axis=0)
            values = [group] + [f"{centroid[i]:.3f}" for i in range(scores.shape[1])]
            tree.insert("", "end", values=values)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)

    def _export_excel(self, scores, group_labels, sample_ids, loadings, elements):
        try:
            import openpyxl
            path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                               filetypes=[("Excel", "*.xlsx")])
            if path:
                with pd.ExcelWriter(path, engine='openpyxl') as writer:
                    # Raw data
                    raw = []
                    for i, (sid, group) in enumerate(zip(sample_ids, group_labels)):
                        row = {'Sample_ID': sid, 'Group': group}
                        for pc in range(scores.shape[1]):
                            row[f'PC{pc+1}'] = scores[i, pc]
                        raw.append(row)
                    pd.DataFrame(raw).to_excel(writer, sheet_name='Raw_Scores', index=False)

                    # Centroids
                    centroids = []
                    for group in set(group_labels):
                        mask = [g == group for g in group_labels]
                        centroid = scores[mask].mean(axis=0)
                        row = {'Group': group, 'N': sum(mask)}
                        for pc in range(scores.shape[1]):
                            row[f'PC{pc+1}'] = centroid[pc]
                        centroids.append(row)
                    pd.DataFrame(centroids).to_excel(writer, sheet_name='Centroids', index=False)

                    # Loadings
                    if loadings is not None and elements is not None:
                        load_df = pd.DataFrame(loadings,
                                              columns=[f'PC{i+1}' for i in range(loadings.shape[1])],
                                              index=elements)
                        load_df.to_excel(writer, sheet_name='Loadings')

                messagebox.showinfo("Success", f"Exported to {Path(path).name}")
        except ImportError:
            messagebox.showerror("Error", "openpyxl not installed")


# ============================================================================
# CONFIG MANAGER
# ============================================================================

class ConfigManager:
    """Manage user preferences and last used settings"""
    def __init__(self, plugin_name):
        self.config_dir = Path.home() / f".{plugin_name}"
        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / "settings.json"
        self.last_vars_file = self.config_dir / "last_variables.json"
        self.settings = self._load_settings()

    def _load_settings(self):
        """Load settings from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file) as f:
                    return json.load(f)
            except:
                pass
        return {
            'alpha': 0.05,
            'conf_level': 0.95,
            'recall_last': True
        }

    def save_settings(self):
        """Save settings to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.settings, f, indent=2)

    def get_last_vars(self, dialog_name):
        """Get last used variables for a dialog"""
        if not self.settings.get('recall_last', True):
            return {}

        if self.last_vars_file.exists():
            try:
                with open(self.last_vars_file) as f:
                    data = json.load(f)
                    return data.get(dialog_name, {})
            except:
                pass
        return {}

    def save_last_vars(self, dialog_name, vars_dict):
        """Save last used variables for a dialog"""
        if not self.settings.get('recall_last', True):
            return

        data = {}
        if self.last_vars_file.exists():
            try:
                with open(self.last_vars_file) as f:
                    data = json.load(f)
            except:
                pass

        data[dialog_name] = vars_dict

        with open(self.last_vars_file, 'w') as f:
            json.dump(data, f, indent=2)


# ============================================================================
# MAIN PLUGIN CLASS
# ============================================================================

class PCALDAExplorerPlugin:
    """PCA+LDA Explorer Pro v2.1 - Complete statistical suite"""

    def __init__(self, main_app):
        self.app = main_app
        self.window = None

        # Data
        self.samples = []
        self.current_elements = []
        self.current_scores = None
        self.current_loadings = None
        self.current_pca = None
        self.current_scaler = None
        self.valid_indices = []
        self.group_labels = None
        self.unique_groups = []
        self.n_groups = 0
        self.group_subset = None  # FIXED: Initialize group_subset

        # Models
        self.lda_model = None
        self.plsda_model = None
        self.rf_model = None
        self.svm_model = None
        self.plsda_vip = {}
        self.model_results = {}

        # NEW: Clustering models
        self.cluster_model = None
        self.cluster_labels = None
        self.cluster_centers = None

        # NEW: Regression models
        self.reg_model = None
        self.reg_results = None

        # NEW: t-SNE results
        self.tsne_results = None

        # NEW: Correlation results
        self.corr_results = None

        # UI
        self.notebook = None
        self.fig = None
        self.ax = None
        self.fig3d = None
        self.ax3d = None
        self.scree_fig = None
        self.scree_ax = None
        self.canvas = None
        self.canvas3d = None
        self.scree_canvas = None
        self.loadings_text = None
        self.status_var = None

        # Settings
        self.scale_var = tk.BooleanVar(value=True)
        self.impute_var = tk.StringVar(value="knn")
        self.n_components_var = tk.IntVar(value=10)
        self.n_pcs_var = tk.IntVar(value=3)
        self.pc_x_var = tk.IntVar(value=1)
        self.pc_y_var = tk.IntVar(value=2)
        self.pc_z_var = tk.IntVar(value=3)
        self.ellipse_var = tk.BooleanVar(value=True)
        self.hull_var = tk.BooleanVar(value=False)
        self.scree_method_var = tk.StringVar(value="kaiser")

        # ML settings
        self.plsda_var = tk.BooleanVar(value=True)
        self.rf_var = tk.BooleanVar(value=True)
        self.svm_var = tk.BooleanVar(value=True)
        self.n_trees_var = tk.IntVar(value=100)
        self.svm_kernel_var = tk.StringVar(value='rbf')

        # Imbalance handling
        self.handle_imbalance_var = tk.BooleanVar(value=True)
        self.imbalance_method_var = tk.StringVar(value="balanced_weights")
        self.imbalance_methods = ["balanced_weights", "BalancedRandomForest"]

        # Outlier sensitivity
        self.outlier_sensitivity_var = tk.StringVar(value="balanced")

        # Grouping
        self.group_var = tk.StringVar(value="None")

        # Column detection
        self.numeric_columns = []
        self.categorical_columns = []

        # NEW: Configuration
        self.config = ConfigManager("pca_lda_explorer")

        # NEW: Tab-specific UI elements
        self._init_new_ui_vars()

    def _init_new_ui_vars(self):
        """Initialize UI variables for new tabs"""
        # t-SNE variables
        self.tsne_perplexity = tk.DoubleVar(value=30.0)
        self.tsne_random_state = tk.IntVar(value=42)
        self.tsne_n_components = tk.IntVar(value=2)

        # Correlation variables
        self.corr_method = tk.StringVar(value="pearson")
        self.corr_alpha = tk.DoubleVar(value=self.config.settings.get('alpha', 0.05))
        self.corr_show_p = tk.BooleanVar(value=True)
        self.corr_methods = ["pearson", "spearman", "kendall"]

        # Regression variables
        self.reg_target = tk.StringVar(value="")
        self.reg_method = tk.StringVar(value="random_forest")
        self.reg_methods = ["linear", "ridge", "lasso", "random_forest"]
        self.reg_test_size = tk.DoubleVar(value=0.2)
        self.reg_cv_folds = tk.IntVar(value=5)

        # Clustering variables
        self.cluster_method = tk.StringVar(value="hierarchical")
        self.cluster_methods = ["hierarchical", "kmeans"]
        self.cluster_n_clusters = tk.IntVar(value=3)
        self.cluster_linkage = tk.StringVar(value="ward")
        self.cluster_linkages = ["ward", "complete", "average", "single"]

        # Statistical tests variables
        self.stats_test_type = tk.StringVar(value="ttest")
        self.stats_test_types = ["ttest", "mannwhitney", "anova"]
        self.stats_var1 = tk.StringVar(value="")
        self.stats_var2 = tk.StringVar(value="")
        self.stats_group = tk.StringVar(value="")
        self.stats_group1 = tk.StringVar(value="")
        self.stats_group2 = tk.StringVar(value="")
        self.stats_alternative = tk.StringVar(value="two-sided")
        self.stats_alternatives = ["two-sided", "less", "greater"]
        self.stats_equal_var = tk.BooleanVar(value=True)

    def _detect_columns(self):
        """Detect numeric and categorical columns from samples"""
        if not hasattr(self.app, 'samples') or not self.app.samples:
            return

        self.numeric_columns = []
        self.categorical_columns = []

        if self.app.samples:
            first = self.app.samples[0]
            for col in first.keys():
                if col in ['Sample_ID', 'Notes', 'Museum_Code', 'Description']:
                    self.categorical_columns.append(col)
                    continue

                try:
                    val = first[col]
                    if val and val != '':
                        float(val)
                        self.numeric_columns.append(col)
                    else:
                        is_numeric = True
                        for s in self.app.samples[:5]:
                            v = s.get(col, '')
                            if v and v != '':
                                try:
                                    float(v)
                                except:
                                    is_numeric = False
                                    break
                        if is_numeric:
                            self.numeric_columns.append(col)
                        else:
                            self.categorical_columns.append(col)
                except:
                    self.categorical_columns.append(col)

    def open_window(self):
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        if not HAS_SKLEARN:
            messagebox.showerror("Error", "scikit-learn required")
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("📊 PCA+LDA Explorer Pro v2.1")
        self.window.geometry("1050x680")
        self.window.transient(self.app.root)

        self._create_interface()
        self._refresh_data()
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_interface(self):
        # Main container
        main = ttk.Frame(self.window, padding=2)
        main.pack(fill=tk.BOTH, expand=True)

        # Top toolbar
        toolbar = ttk.Frame(main)
        toolbar.pack(fill=tk.X, pady=1)

        # LEFT SIDE
        ttk.Button(toolbar, text="📥 Import", width=8,
                   command=self._import_from_main).pack(side=tk.LEFT, padx=1)
        ttk.Button(toolbar, text="📤 Export", width=8,
                   command=self._export_to_main).pack(side=tk.LEFT, padx=1)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=3, fill=tk.Y)

        ttk.Button(toolbar, text="🔄 Refresh", width=7,
                   command=self._refresh_data).pack(side=tk.LEFT, padx=1)
        ttk.Button(toolbar, text="🔍 Outliers", width=8,
                   command=self._manage_outliers).pack(side=tk.LEFT, padx=1)
        ttk.Button(toolbar, text="📊 Stats", width=7,
                   command=self._show_group_stats).pack(side=tk.LEFT, padx=1)
        ttk.Button(toolbar, text="⚙️", width=3,
                   command=self._open_settings).pack(side=tk.LEFT, padx=1)

        # RIGHT SIDE
        ttk.Label(toolbar, text="Group:").pack(side=tk.RIGHT, padx=(2,1))
        self.group_combo = ttk.Combobox(toolbar, textvariable=self.group_var,
                                         width=10, state='readonly')
        self.group_combo.pack(side=tk.RIGHT, padx=1)

        ttk.Button(toolbar, text="🚀 Run", width=6,
                  command=self._run_analysis,
                  style='Accent.TButton').pack(side=tk.RIGHT, padx=2)

        # Parameters toolbar
        param_toolbar = ttk.Frame(main)
        param_toolbar.pack(fill=tk.X, pady=1)

        param_row1 = ttk.Frame(param_toolbar)
        param_row1.pack(fill=tk.X)

        ttk.Label(param_row1, text="Impute:").pack(side=tk.LEFT)
        ttk.Combobox(param_row1, textvariable=self.impute_var,
                     values=['discard', 'mean', 'median', 'knn'],
                     width=5, state='readonly').pack(side=tk.LEFT, padx=1)

        ttk.Checkbutton(param_row1, text="Scale", variable=self.scale_var).pack(side=tk.LEFT, padx=2)
        ttk.Checkbutton(param_row1, text="Ellipses", variable=self.ellipse_var).pack(side=tk.LEFT, padx=2)

        ttk.Label(param_row1, text="PCs:").pack(side=tk.LEFT, padx=(5,1))
        ttk.Spinbox(param_row1, from_=1, to=10, textvariable=self.pc_x_var, width=2).pack(side=tk.LEFT)
        ttk.Spinbox(param_row1, from_=1, to=10, textvariable=self.pc_y_var, width=2).pack(side=tk.LEFT)
        ttk.Spinbox(param_row1, from_=1, to=10, textvariable=self.pc_z_var, width=2).pack(side=tk.LEFT)

        ttk.Label(param_row1, text="Max PCs:").pack(side=tk.LEFT, padx=(5,1))
        ttk.Spinbox(param_row1, from_=2, to=20, textvariable=self.n_components_var, width=3).pack(side=tk.LEFT)

        ttk.Label(param_row1, text="LDA PCs:").pack(side=tk.LEFT, padx=(5,1))
        ttk.Spinbox(param_row1, from_=1, to=10, textvariable=self.n_pcs_var, width=3).pack(side=tk.LEFT)

        # ML options row
        ml_row = ttk.Frame(param_toolbar)
        ml_row.pack(fill=tk.X, pady=1)

        ttk.Checkbutton(ml_row, text="PLS-DA", variable=self.plsda_var).pack(side=tk.LEFT, padx=2)
        ttk.Checkbutton(ml_row, text="RF", variable=self.rf_var).pack(side=tk.LEFT, padx=2)
        ttk.Checkbutton(ml_row, text="SVM", variable=self.svm_var).pack(side=tk.LEFT, padx=2)
        ttk.Checkbutton(ml_row, text="Balance", variable=self.handle_imbalance_var).pack(side=tk.LEFT, padx=2)

        ttk.Label(ml_row, text="Trees:").pack(side=tk.LEFT, padx=(5,1))
        ttk.Spinbox(ml_row, from_=10, to=500, textvariable=self.n_trees_var, width=4).pack(side=tk.LEFT)

        ttk.Label(ml_row, text="Kernel:").pack(side=tk.LEFT, padx=(5,1))
        ttk.Combobox(ml_row, textvariable=self.svm_kernel_var,
                     values=['linear', 'poly', 'rbf', 'sigmoid'],
                     width=5, state='readonly').pack(side=tk.LEFT)

        # Element selection
        elem_frame = ttk.LabelFrame(main, text="Elements", padding=1)
        elem_frame.pack(fill=tk.X, pady=1)

        btn_row = ttk.Frame(elem_frame)
        btn_row.pack(fill=tk.X)

        for text, cmd in [("All", self._select_all), ("Clear", self._clear_all),
                         ("Major", self._select_major), ("Trace", self._select_trace),
                         ("REE", self._select_ree)]:
            ttk.Button(btn_row, text=text, width=5, command=cmd).pack(side=tk.LEFT, padx=1)

        list_frame = ttk.Frame(elem_frame)
        list_frame.pack(fill=tk.X, pady=1)

        self.element_listbox = tk.Listbox(list_frame, height=3, selectmode=tk.MULTIPLE,
                                          exportselection=False, font=("TkDefaultFont", 8))
        scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.element_listbox.yview)
        self.element_listbox.config(yscrollcommand=scroll.set)

        self.element_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Notebook with tabs
        self.notebook = ttk.Notebook(main)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=1)

        tabs = [
            ("📈 Biplot", self._create_biplot_tab),
            ("📊 3D", self._create_3d_tab),
            ("🔮 t-SNE", self._create_tsne_tab),
            ("📊 Corr", self._create_correlation_tab),
            ("📉 Reg", self._create_regression_tab),
            ("🔗 Cluster", self._create_clustering_tab),
            ("📊 Tests", self._create_stats_tests_tab),
            ("📉 Scree", self._create_scree_tab),
            ("📋 Loadings", self._create_loadings_tab),
            ("🎯 LDA", self._create_lda_tab),
            ("🧠 PLS-DA", self._create_plsda_tab),
            ("🌲 RF", self._create_rf_tab),
            ("🤖 SVM", self._create_svm_tab),
            ("📊 Compare", self._create_compare_tab)
        ]

        for text, creator in tabs:
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=text)
            creator(frame)

        # Status bar
        status = ttk.Frame(main, relief=tk.SUNKEN, height=20)
        status.pack(fill=tk.X, side=tk.BOTTOM, pady=1)
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(status, textvariable=self.status_var, font=("TkDefaultFont", 8)).pack(side=tk.LEFT, padx=5)

    # ============================================================================
    # EXISTING TAB CREATION METHODS
    # ============================================================================

    def _create_biplot_tab(self, parent):
        self.fig, self.ax = plt.subplots(figsize=(6, 5))
        self.canvas = FigureCanvasTkAgg(self.fig, parent)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        toolbar = NavigationToolbar2Tk(self.canvas, parent)
        toolbar.update()

    def _create_3d_tab(self, parent):
        self.fig3d = plt.figure(figsize=(6, 5))
        self.ax3d = self.fig3d.add_subplot(111, projection='3d')
        self.canvas3d = FigureCanvasTkAgg(self.fig3d, parent)
        self.canvas3d.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _create_scree_tab(self, parent):
        self.scree_fig, self.scree_ax = plt.subplots(figsize=(6, 4))
        self.scree_canvas = FigureCanvasTkAgg(self.scree_fig, parent)
        self.scree_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _create_loadings_tab(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True)

        self.loadings_text = tk.Text(frame, font=("Courier", 8), wrap=tk.NONE)
        scroll_y = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.loadings_text.yview)
        scroll_x = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=self.loadings_text.xview)
        self.loadings_text.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.loadings_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

    def _create_lda_tab(self, parent):
        self.lda_frame = ttk.Frame(parent)
        self.lda_frame.pack(fill=tk.BOTH, expand=True)
        self.lda_placeholder = ttk.Label(self.lda_frame, text="Run analysis with grouping")
        self.lda_placeholder.pack(expand=True)

    def _create_plsda_tab(self, parent):
        self.plsda_frame = ttk.Frame(parent)
        self.plsda_frame.pack(fill=tk.BOTH, expand=True)
        self.plsda_placeholder = ttk.Label(self.plsda_frame, text="Run analysis with PLS-DA enabled")
        self.plsda_placeholder.pack(expand=True)

    def _create_rf_tab(self, parent):
        self.rf_frame = ttk.Frame(parent)
        self.rf_frame.pack(fill=tk.BOTH, expand=True)
        self.rf_placeholder = ttk.Label(self.rf_frame, text="Run analysis to see RF results")
        self.rf_placeholder.pack(expand=True)

    def _create_svm_tab(self, parent):
        self.svm_frame = ttk.Frame(parent)
        self.svm_frame.pack(fill=tk.BOTH, expand=True)
        self.svm_placeholder = ttk.Label(self.svm_frame, text="Run analysis to see SVM results")
        self.svm_placeholder.pack(expand=True)

    def _create_compare_tab(self, parent):
        self.compare_frame = ttk.Frame(parent)
        self.compare_frame.pack(fill=tk.BOTH, expand=True)
        self.compare_placeholder = ttk.Label(self.compare_frame, text="Run analysis to compare models")
        self.compare_placeholder.pack(expand=True)

    # ============================================================================
    # NEW TAB: t-SNE
    # ============================================================================

    def _create_tsne_tab(self, parent):
        """Create t-SNE visualization tab"""
        ctrl = ttk.LabelFrame(parent, text="t-SNE", padding=2)
        ctrl.pack(fill=tk.X, pady=1)

        param_frame = ttk.Frame(ctrl)
        param_frame.pack(fill=tk.X, pady=1)

        ttk.Label(param_frame, text="Perp:").pack(side=tk.LEFT)
        ttk.Spinbox(param_frame, from_=5, to=50, textvariable=self.tsne_perplexity,
                   width=4).pack(side=tk.LEFT, padx=1)

        ttk.Label(param_frame, text="Rand:").pack(side=tk.LEFT, padx=(3,1))
        ttk.Spinbox(param_frame, from_=0, to=999, textvariable=self.tsne_random_state,
                   width=4).pack(side=tk.LEFT)

        ttk.Label(param_frame, text="Color:").pack(side=tk.LEFT, padx=(3,1))
        self.tsne_color_var = tk.StringVar(value="group")
        ttk.Combobox(param_frame, textvariable=self.tsne_color_var,
                    values=["group", "cluster", "none"], width=5, state='readonly').pack(side=tk.LEFT)

        ttk.Button(param_frame, text="▶️ Run", width=6,
                  command=self._run_tsne).pack(side=tk.RIGHT, padx=1)

        self.tsne_frame = ttk.Frame(parent)
        self.tsne_frame.pack(fill=tk.BOTH, expand=True, pady=1)

        self.tsne_placeholder = ttk.Label(self.tsne_frame, text="Run t-SNE to visualize")
        self.tsne_placeholder.pack(expand=True)

    def _run_tsne(self):
        """Run t-SNE analysis"""
        if self.current_scores is None:
            messagebox.showwarning("Warning", "Run PCA analysis first")
            return

        try:
            X = self.current_scores

            tsne = TSNE(
                n_components=self.tsne_n_components.get(),
                perplexity=min(self.tsne_perplexity.get(), len(X)-1),
                random_state=self.tsne_random_state.get()
            )
            self.tsne_results = tsne.fit_transform(X)

            for widget in self.tsne_frame.winfo_children():
                widget.destroy()

            fig, ax = plt.subplots(figsize=(6, 5))

            if self.tsne_color_var.get() == "group" and hasattr(self, 'group_subset') and self.group_subset is not None:
                unique = list(set(self.group_subset))
                colors = plt.cm.tab10(np.linspace(0, 1, len(unique)))

                for i, g in enumerate(unique):
                    mask = [self.group_subset[j] == g for j in range(len(self.group_subset))]
                    ax.scatter(self.tsne_results[mask, 0], self.tsne_results[mask, 1],
                              c=[colors[i]], label=g[:10], alpha=0.7, s=20)

            elif self.tsne_color_var.get() == "cluster" and self.cluster_labels is not None:
                unique_clusters = np.unique(self.cluster_labels)
                colors = plt.cm.tab10(np.linspace(0, 1, len(unique_clusters)))

                for i, c in enumerate(unique_clusters):
                    mask = self.cluster_labels == c
                    ax.scatter(self.tsne_results[mask, 0], self.tsne_results[mask, 1],
                              c=[colors[i]], label=f'C{c}', alpha=0.7, s=20)

            else:
                ax.scatter(self.tsne_results[:, 0], self.tsne_results[:, 1],
                          alpha=0.6, s=20, c='steelblue')

            ax.set_xlabel('t-SNE 1')
            ax.set_ylabel('t-SNE 2')
            ax.set_title(f't-SNE (perp={self.tsne_perplexity.get()})')
            ax.grid(True, alpha=0.3)

            canvas = FigureCanvasTkAgg(fig, self.tsne_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            toolbar = NavigationToolbar2Tk(canvas, self.tsne_frame)
            toolbar.update()

            self.status_var.set("✅ t-SNE complete")

        except Exception as e:
            messagebox.showerror("t-SNE Error", f"Error: {str(e)}")

    # ============================================================================
    # NEW TAB: Correlation Analysis
    # ============================================================================

    def _create_correlation_tab(self, parent):
        """Create correlation analysis tab"""
        ctrl = ttk.LabelFrame(parent, text="Correlation", padding=2)
        ctrl.pack(fill=tk.X, pady=1)

        method_frame = ttk.Frame(ctrl)
        method_frame.pack(fill=tk.X, pady=1)

        ttk.Label(method_frame, text="Method:").pack(side=tk.LEFT)
        self.corr_method_combo = ttk.Combobox(method_frame, textvariable=self.corr_method,
                                              values=self.corr_methods, width=7, state='readonly')
        self.corr_method_combo.pack(side=tk.LEFT, padx=1)

        ttk.Label(method_frame, text="α:").pack(side=tk.LEFT, padx=(3,1))
        ttk.Spinbox(method_frame, from_=0.001, to=0.1, increment=0.001,
                   textvariable=self.corr_alpha, width=4).pack(side=tk.LEFT)

        ttk.Checkbutton(method_frame, text="p", variable=self.corr_show_p).pack(side=tk.LEFT, padx=2)

        ttk.Button(method_frame, text="▶️ Run", width=6,
                  command=self._run_correlation).pack(side=tk.RIGHT, padx=1)

        list_frame = ttk.Frame(ctrl)
        list_frame.pack(fill=tk.X, pady=1)

        self.corr_listbox = tk.Listbox(list_frame, height=3, selectmode=tk.MULTIPLE,
                                       exportselection=False, font=("TkDefaultFont", 8))
        scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.corr_listbox.yview)
        self.corr_listbox.config(yscrollcommand=scroll.set)

        self.corr_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.corr_notebook = ttk.Notebook(parent)
        self.corr_notebook.pack(fill=tk.BOTH, expand=True, pady=1)

        self.corr_matrix_tab = ttk.Frame(self.corr_notebook)
        self.corr_notebook.add(self.corr_matrix_tab, text="Matrix")

        self.corr_heatmap_tab = ttk.Frame(self.corr_notebook)
        self.corr_notebook.add(self.corr_heatmap_tab, text="Heatmap")

        self.corr_scatter_tab = ttk.Frame(self.corr_notebook)
        self.corr_notebook.add(self.corr_scatter_tab, text="Scatter")

        self.corr_details_tab = ttk.Frame(self.corr_notebook)
        self.corr_notebook.add(self.corr_details_tab, text="Details")

        for tab in [self.corr_matrix_tab, self.corr_heatmap_tab,
                   self.corr_scatter_tab, self.corr_details_tab]:
            ttk.Label(tab, text="Run correlation to see results").pack(expand=True)

    def _run_correlation(self):
        """Run correlation analysis"""
        selected = [self.corr_listbox.get(i) for i in self.corr_listbox.curselection()]

        if len(selected) < 2:
            messagebox.showwarning("Warning", "Select at least 2 variables")
            return

        data_dict = {}
        for var in selected:
            values = []
            for s in self.samples:
                try:
                    val = float(s.get(var, np.nan))
                    values.append(val)
                except:
                    values.append(np.nan)
            data_dict[var] = values

        df = pd.DataFrame(data_dict)
        df = df.dropna()

        if len(df) < 3:
            messagebox.showwarning("Warning", "Need at least 3 complete observations")
            return

        method = self.corr_method.get()
        alpha = self.corr_alpha.get()

        corr_matrix = df.corr(method=method)

        p_matrix = pd.DataFrame(np.ones((len(selected), len(selected))),
                               index=selected, columns=selected)

        for i in range(len(selected)):
            for j in range(i+1, len(selected)):
                x = df[selected[i]].values
                y = df[selected[j]].values

                if method == "pearson":
                    r, p = pearsonr(x, y)
                elif method == "spearman":
                    r, p = spearmanr(x, y)
                else:
                    r, p = kendalltau(x, y)

                p_matrix.iloc[i, j] = p_matrix.iloc[j, i] = p

        self.corr_results = {
            'variables': selected,
            'method': method,
            'n_obs': len(df),
            'correlation': corr_matrix,
            'p_values': p_matrix,
            'alpha': alpha,
            'data': df
        }

        self._update_corr_matrix()
        self._update_corr_heatmap()
        self._update_corr_scatter()
        self._update_corr_details()

        self.status_var.set(f"✅ Correlation complete - {len(df)} observations")

    def _update_corr_matrix(self):
        for w in self.corr_matrix_tab.winfo_children():
            w.destroy()

        fig, ax = plt.subplots(figsize=(6, 5))

        if self.corr_show_p.get():
            corr = self.corr_results['correlation']
            pvals = self.corr_results['p_values']

            annot = pd.DataFrame(index=corr.index, columns=corr.columns)
            for i in range(len(corr)):
                for j in range(len(corr)):
                    if i == j:
                        annot.iloc[i, j] = "1.000"
                    else:
                        p = pvals.iloc[i, j]
                        stars = ""
                        if p < 0.001:
                            stars = "***"
                        elif p < 0.01:
                            stars = "**"
                        elif p < 0.05:
                            stars = "*"
                        annot.iloc[i, j] = f"{corr.iloc[i, j]:.3f}{stars}"

            sns.heatmap(corr, annot=annot, fmt='', cmap='RdBu_r',
                       center=0, vmin=-1, vmax=1, square=True,
                       linewidths=0.5, ax=ax, cbar_kws={"shrink": 0.8})
        else:
            sns.heatmap(corr, annot=True, fmt='.3f', cmap='RdBu_r',
                       center=0, vmin=-1, vmax=1, square=True,
                       linewidths=0.5, ax=ax, cbar_kws={"shrink": 0.8})

        ax.set_title(f'{self.corr_results["method"].title()} (n={self.corr_results["n_obs"]})')

        canvas = FigureCanvasTkAgg(fig, self.corr_matrix_tab)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _update_corr_heatmap(self):
        for w in self.corr_heatmap_tab.winfo_children():
            w.destroy()

        corr = self.corr_results['correlation']

        try:
            cg = sns.clustermap(corr, annot=True, fmt='.3f', cmap='RdBu_r',
                               center=0, vmin=-1, vmax=1, linewidths=0.5,
                               figsize=(7, 6))
            cg.ax_heatmap.set_title(f'Clustered (n={self.corr_results["n_obs"]})', y=1.02)

            canvas = FigureCanvasTkAgg(cg.fig, self.corr_heatmap_tab)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        except Exception as e:
            ttk.Label(self.corr_heatmap_tab,
                     text=f"Clustering failed: {str(e)[:50]}...").pack(expand=True)

    def _update_corr_scatter(self):
        for w in self.corr_scatter_tab.winfo_children():
            w.destroy()

        if len(self.corr_results['variables']) > 8:
            ttk.Label(self.corr_scatter_tab,
                     text=f"Too many variables ({len(self.corr_results['variables'])})").pack(expand=True)
            return

        fig, axes = plt.subplots(len(self.corr_results['variables']),
                                len(self.corr_results['variables']),
                                figsize=(8, 7))

        data = self.corr_results['data']
        vars_list = self.corr_results['variables']

        for i, var1 in enumerate(vars_list):
            for j, var2 in enumerate(vars_list):
                if i == j:
                    axes[i, j].hist(data[var1].dropna(), bins=10,
                                   color='steelblue', alpha=0.7, edgecolor='black')
                else:
                    x = data[var2].dropna()
                    y = data[var1].dropna()
                    common_idx = x.index.intersection(y.index)
                    x = x.loc[common_idx]
                    y = y.loc[common_idx]

                    axes[i, j].scatter(x, y, alpha=0.5, s=15, c='steelblue')

                    corr_val = self.corr_results['correlation'].loc[var1, var2]
                    p_val = self.corr_results['p_values'].loc[var1, var2]

                    sig = ""
                    if p_val < 0.001:
                        sig = "***"
                    elif p_val < 0.01:
                        sig = "**"
                    elif p_val < 0.05:
                        sig = "*"

                    axes[i, j].text(0.05, 0.95, f'r={corr_val:.2f}{sig}',
                                   transform=axes[i, j].transAxes,
                                   fontsize=6, verticalalignment='top',
                                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

                if i == len(vars_list)-1:
                    axes[i, j].set_xlabel(var2, fontsize=6)
                if j == 0:
                    axes[i, j].set_ylabel(var1, fontsize=6)

        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, self.corr_scatter_tab)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _update_corr_details(self):
        for w in self.corr_details_tab.winfo_children():
            w.destroy()

        text = tk.Text(self.corr_details_tab, font=("Courier", 7), wrap=tk.NONE)
        scroll_y = ttk.Scrollbar(self.corr_details_tab, orient=tk.VERTICAL, command=text.yview)
        scroll_x = ttk.Scrollbar(self.corr_details_tab, orient=tk.HORIZONTAL, command=text.xview)
        text.config(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        r = self.corr_results
        report = self._generate_corr_report(r)

        text.insert(1.0, report)
        text.config(state=tk.DISABLED)

        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

    def _generate_corr_report(self, r):
        corr = r['correlation']
        pvals = r['p_values']
        alpha = r['alpha']

        report = f"""
{'='*60}
CORRELATION ANALYSIS REPORT
{'='*60}

Method: {r['method'].title()}
Variables: {len(r['variables'])}
Observations: {r['n_obs']}
α = {alpha}

{'='*60}
CORRELATION MATRIX (with significance)
{'='*60}

"""
        for i, var1 in enumerate(r['variables']):
            line = f"{var1:<12}"
            for j, var2 in enumerate(r['variables']):
                if i == j:
                    line += f"  {'1.000':>6}"
                else:
                    p = pvals.iloc[i, j]
                    stars = ""
                    if p < 0.001:
                        stars = "***"
                    elif p < 0.01:
                        stars = "**"
                    elif p < 0.05:
                        stars = "*"
                    line += f"  {corr.iloc[i, j]:>5.3f}{stars:<2}"
            report += line + "\n"

        sig_count = 0
        total_pairs = 0
        report += f"""
{'='*60}
SIGNIFICANT CORRELATIONS (p < {alpha})
{'='*60}

"""
        for i in range(len(r['variables'])):
            for j in range(i+1, len(r['variables'])):
                total_pairs += 1
                if pvals.iloc[i, j] < alpha:
                    sig_count += 1
                    report += f"{r['variables'][i]:<12} vs {r['variables'][j]:<12}: "
                    report += f"r = {corr.iloc[i, j]:.3f}  p = {pvals.iloc[i, j]:.4f}\n"

        report += f"""
{'='*60}
SUMMARY
{'='*60}

Total pairs: {total_pairs}
Significant: {sig_count} ({sig_count/total_pairs*100:.1f}%)
"""
        return report

    # ============================================================================
    # NEW TAB: Regression Analysis (FIXED with populated target dropdown)
    # ============================================================================

    def _create_regression_tab(self, parent):
        """Create regression analysis tab"""
        ctrl = ttk.LabelFrame(parent, text="Regression", padding=2)
        ctrl.pack(fill=tk.X, pady=1)

        target_frame = ttk.Frame(ctrl)
        target_frame.pack(fill=tk.X, pady=1)

        ttk.Label(target_frame, text="Target:").pack(side=tk.LEFT)
        self.reg_target_combo = ttk.Combobox(target_frame, textvariable=self.reg_target,
                                            values=[], width=8)
        self.reg_target_combo.pack(side=tk.LEFT, padx=1)

        # FIX: Populate immediately
        self.reg_target_combo['values'] = self.numeric_columns
        if self.numeric_columns:
            self.reg_target.set(self.numeric_columns[0])

        ttk.Label(target_frame, text="Method:").pack(side=tk.LEFT, padx=(3,1))
        self.reg_method_combo = ttk.Combobox(target_frame, textvariable=self.reg_method,
                                            values=self.reg_methods, width=8, state='readonly')
        self.reg_method_combo.pack(side=tk.LEFT)

        param_frame = ttk.Frame(ctrl)
        param_frame.pack(fill=tk.X, pady=1)

        ttk.Label(param_frame, text="Test:").pack(side=tk.LEFT)
        ttk.Spinbox(param_frame, from_=0.1, to=0.5, increment=0.05,
                   textvariable=self.reg_test_size, width=3).pack(side=tk.LEFT, padx=1)

        ttk.Label(param_frame, text="CV:").pack(side=tk.LEFT, padx=(3,1))
        ttk.Spinbox(param_frame, from_=2, to=10, textvariable=self.reg_cv_folds,
                   width=2).pack(side=tk.LEFT)

        ttk.Button(param_frame, text="▶️ Run", width=6,
                  command=self._run_regression).pack(side=tk.RIGHT, padx=1)

        list_frame = ttk.Frame(ctrl)
        list_frame.pack(fill=tk.X, pady=1)

        self.reg_listbox = tk.Listbox(list_frame, height=3, selectmode=tk.MULTIPLE,
                                      exportselection=False, font=("TkDefaultFont", 8))
        scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.reg_listbox.yview)
        self.reg_listbox.config(yscrollcommand=scroll.set)

        self.reg_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.reg_notebook = ttk.Notebook(parent)
        self.reg_notebook.pack(fill=tk.BOTH, expand=True, pady=1)

        self.reg_metrics_tab = ttk.Frame(self.reg_notebook)
        self.reg_notebook.add(self.reg_metrics_tab, text="Metrics")

        self.reg_plots_tab = ttk.Frame(self.reg_notebook)
        self.reg_notebook.add(self.reg_plots_tab, text="Plots")

        self.reg_importance_tab = ttk.Frame(self.reg_notebook)
        self.reg_notebook.add(self.reg_importance_tab, text="Importance")

        for tab in [self.reg_metrics_tab, self.reg_plots_tab, self.reg_importance_tab]:
            ttk.Label(tab, text="Run regression to see results").pack(expand=True)

    def _run_regression(self):
        """Run regression analysis"""
        target = self.reg_target.get()
        if not target:
            messagebox.showwarning("Warning", "Select a target variable")
            return

        selected = [self.reg_listbox.get(i) for i in self.reg_listbox.curselection()]
        if len(selected) < 1:
            messagebox.showwarning("Warning", "Select at least 1 feature")
            return

        X = []
        y = []
        valid_indices = []

        for i, s in enumerate(self.samples):
            row = []
            valid = True

            for feat in selected:
                try:
                    val = float(s.get(feat, np.nan))
                    if np.isnan(val):
                        valid = False
                        break
                    row.append(val)
                except:
                    valid = False
                    break

            if valid:
                try:
                    target_val = float(s.get(target, np.nan))
                    if not np.isnan(target_val):
                        X.append(row)
                        y.append(target_val)
                        valid_indices.append(i)
                except:
                    pass

        if len(X) < 10:
            messagebox.showwarning("Warning", f"Need at least 10 samples, have {len(X)}")
            return

        X = np.array(X)
        y = np.array(y)

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=self.reg_test_size.get(), random_state=42
        )

        method = self.reg_method.get()

        if method == "linear":
            model = LinearRegression()
        elif method == "ridge":
            model = Ridge(alpha=1.0)
        elif method == "lasso":
            model = Lasso(alpha=0.1)
        else:
            model = RandomForestRegressor(n_estimators=100, random_state=42)

        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)

        r2 = r2_score(y_test, y_pred)
        mse = mean_squared_error(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mse)

        try:
            cv_scores = cross_val_score(model, X_scaled, y, cv=self.reg_cv_folds.get(),
                                       scoring='r2')
            cv_mean = cv_scores.mean()
            cv_std = cv_scores.std()
        except:
            cv_mean = np.nan
            cv_std = np.nan

        self.reg_results = {
            'model': model,
            'method': method,
            'target': target,
            'features': selected,
            'n_samples': len(X),
            'r2': r2,
            'mse': mse,
            'mae': mae,
            'rmse': rmse,
            'cv_mean': cv_mean,
            'cv_std': cv_std,
            'y_true': y_test,
            'y_pred': y_pred,
            'feature_importance': getattr(model, 'feature_importances_', None)
        }

        self._update_reg_metrics()
        self._update_reg_plots()
        self._update_reg_importance()

        self.status_var.set(f"✅ Regression complete - R² = {r2:.3f}")

    def _update_reg_metrics(self):
        for w in self.reg_metrics_tab.winfo_children():
            w.destroy()

        r = self.reg_results

        text = tk.Text(self.reg_metrics_tab, font=("Courier", 8), padx=5, pady=5)
        text.pack(fill=tk.BOTH, expand=True)

        report = f"""
{'='*50}
REGRESSION RESULTS
{'='*50}

Method: {r['method'].title()}
Target: {r['target']}
Features: {len(r['features'])}
Samples: {r['n_samples']}

{'='*50}
PERFORMANCE
{'='*50}

R²:           {r['r2']:.3f}
MSE:          {r['mse']:.3f}
RMSE:         {r['rmse']:.3f}
MAE:          {r['mae']:.3f}

CV (k={self.reg_cv_folds.get()}):
  Mean R²:    {r['cv_mean']:.3f}
  Std Dev:    {r['cv_std']:.3f}
"""
        text.insert(1.0, report)
        text.config(state=tk.DISABLED)

    def _update_reg_plots(self):
        for w in self.reg_plots_tab.winfo_children():
            w.destroy()

        r = self.reg_results

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7, 3))

        ax1.scatter(r['y_true'], r['y_pred'], alpha=0.6, edgecolors='k', s=20)
        min_val = min(min(r['y_true']), min(r['y_pred']))
        max_val = max(max(r['y_true']), max(r['y_pred']))
        ax1.plot([min_val, max_val], [min_val, max_val], 'r--', alpha=0.5)
        ax1.set_xlabel('Actual')
        ax1.set_ylabel('Predicted')
        ax1.set_title(f'R² = {r["r2"]:.3f}')
        ax1.grid(True, alpha=0.3)

        residuals = r['y_true'] - r['y_pred']
        ax2.scatter(r['y_pred'], residuals, alpha=0.6, edgecolors='k', s=20)
        ax2.axhline(y=0, color='r', linestyle='--', alpha=0.5)
        ax2.set_xlabel('Predicted')
        ax2.set_ylabel('Residuals')
        ax2.set_title('Residuals')
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, self.reg_plots_tab)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _update_reg_importance(self):
        for w in self.reg_importance_tab.winfo_children():
            w.destroy()

        r = self.reg_results

        if r['feature_importance'] is None:
            ttk.Label(self.reg_importance_tab,
                     text="Feature importance not available").pack(expand=True)
            return

        importance = r['feature_importance']
        indices = np.argsort(importance)[::-1]

        fig, ax = plt.subplots(figsize=(5, 4))

        y_pos = np.arange(len(indices))
        ax.barh(y_pos, importance[indices])
        ax.set_yticks(y_pos)
        ax.set_yticklabels([r['features'][i] for i in indices], fontsize=8)
        ax.set_xlabel('Importance')
        ax.set_title('Feature Importance')
        ax.invert_yaxis()
        ax.grid(True, alpha=0.3, axis='x')

        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, self.reg_importance_tab)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # ============================================================================
    # NEW TAB: Clustering Analysis
    # ============================================================================

    def _create_clustering_tab(self, parent):
        """Create clustering analysis tab"""
        ctrl = ttk.LabelFrame(parent, text="Clustering", padding=2)
        ctrl.pack(fill=tk.X, pady=1)

        method_frame = ttk.Frame(ctrl)
        method_frame.pack(fill=tk.X, pady=1)

        ttk.Label(method_frame, text="Method:").pack(side=tk.LEFT)
        self.cluster_method_combo = ttk.Combobox(method_frame, textvariable=self.cluster_method,
                                                values=self.cluster_methods, width=8, state='readonly')
        self.cluster_method_combo.pack(side=tk.LEFT, padx=1)
        self.cluster_method_combo.bind('<<ComboboxSelected>>', self._update_cluster_ui)

        param_frame = ttk.Frame(ctrl)
        param_frame.pack(fill=tk.X, pady=1)

        self.cluster_hier_frame = ttk.Frame(param_frame)
        ttk.Label(self.cluster_hier_frame, text="Link:").pack(side=tk.LEFT)
        ttk.Combobox(self.cluster_hier_frame, textvariable=self.cluster_linkage,
                    values=self.cluster_linkages, width=5, state='readonly').pack(side=tk.LEFT, padx=1)

        self.cluster_kmeans_frame = ttk.Frame(param_frame)
        ttk.Label(self.cluster_kmeans_frame, text="k:").pack(side=tk.LEFT)
        ttk.Spinbox(self.cluster_kmeans_frame, from_=2, to=10,
                   textvariable=self.cluster_n_clusters, width=2).pack(side=tk.LEFT, padx=1)

        self.cluster_kmeans_frame.pack_forget()
        self.cluster_hier_frame.pack(side=tk.LEFT)

        ttk.Button(param_frame, text="▶️ Run", width=6,
                  command=self._run_clustering).pack(side=tk.RIGHT, padx=1)

        self.cluster_notebook = ttk.Notebook(parent)
        self.cluster_notebook.pack(fill=tk.BOTH, expand=True, pady=1)

        self.cluster_plot_tab = ttk.Frame(self.cluster_notebook)
        self.cluster_notebook.add(self.cluster_plot_tab, text="Plot")

        self.cluster_metrics_tab = ttk.Frame(self.cluster_notebook)
        self.cluster_notebook.add(self.cluster_metrics_tab, text="Metrics")

        self.cluster_details_tab = ttk.Frame(self.cluster_notebook)
        self.cluster_notebook.add(self.cluster_details_tab, text="Details")

        for tab in [self.cluster_plot_tab, self.cluster_metrics_tab, self.cluster_details_tab]:
            ttk.Label(tab, text="Run clustering to see results").pack(expand=True)

    def _update_cluster_ui(self, event=None):
        if self.cluster_method.get() == "hierarchical":
            self.cluster_kmeans_frame.pack_forget()
            self.cluster_hier_frame.pack(side=tk.LEFT)
        else:
            self.cluster_hier_frame.pack_forget()
            self.cluster_kmeans_frame.pack(side=tk.LEFT)

    def _run_clustering(self):
        if self.current_scores is None:
            messagebox.showwarning("Warning", "Run PCA analysis first")
            return

        X = self.current_scores[:, :self.n_pcs_var.get()]
        method = self.cluster_method.get()

        try:
            if method == "hierarchical":
                linkage_method = self.cluster_linkage.get()
                Z = linkage(X, method=linkage_method)

                self.cluster_labels = fcluster(Z, self.cluster_n_clusters.get(), criterion='maxclust')
                self.cluster_model = Z

                self._update_cluster_plot_hierarchical(Z)
            else:
                kmeans = KMeans(n_clusters=self.cluster_n_clusters.get(), random_state=42, n_init=10)
                self.cluster_labels = kmeans.fit_predict(X)
                self.cluster_centers = kmeans.cluster_centers_
                self.cluster_model = kmeans

                self._update_cluster_plot_kmeans(X)

            self._update_cluster_metrics(X)
            self._update_cluster_details()

            self.status_var.set(f"✅ Clustering complete - {len(np.unique(self.cluster_labels))} clusters")

        except Exception as e:
            messagebox.showerror("Clustering Error", f"Error: {str(e)}")

    def _update_cluster_plot_hierarchical(self, Z):
        for w in self.cluster_plot_tab.winfo_children():
            w.destroy()

        fig, ax = plt.subplots(figsize=(7, 5))

        sample_ids = [self.samples[i].get('Sample_ID', f'S{i}')
                     for i in self.valid_indices]

        dendrogram(Z, labels=sample_ids, ax=ax, leaf_rotation=90, leaf_font_size=6)

        if self.cluster_n_clusters.get() > 1:
            last_merge = Z[-(self.cluster_n_clusters.get()-1), 2]
            ax.axhline(y=last_merge, color='r', linestyle='--', alpha=0.5)

        ax.set_title(f'Hierarchical ({self.cluster_linkage.get()})')
        ax.set_xlabel('Sample')
        ax.set_ylabel('Distance')
        ax.grid(True, alpha=0.3, axis='y')

        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, self.cluster_plot_tab)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _update_cluster_plot_kmeans(self, X):
        for w in self.cluster_plot_tab.winfo_children():
            w.destroy()

        fig, ax = plt.subplots(figsize=(6, 5))

        colors = plt.cm.tab10(np.linspace(0, 1, self.cluster_n_clusters.get()))

        for i in range(self.cluster_n_clusters.get()):
            mask = self.cluster_labels == i+1
            ax.scatter(X[mask, 0], X[mask, 1],
                      c=[colors[i]], label=f'C{i+1}', alpha=0.7, s=20)

        if self.cluster_centers is not None:
            ax.scatter(self.cluster_centers[:, 0], self.cluster_centers[:, 1],
                      marker='X', s=100, c='red', edgecolors='black', linewidths=1)

        ax.set_xlabel(f'PC{self.pc_x_var.get()}')
        ax.set_ylabel(f'PC{self.pc_y_var.get()}')
        ax.set_title(f'K-Means (k={self.cluster_n_clusters.get()})')
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, self.cluster_plot_tab)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _update_cluster_metrics(self, X):
        for w in self.cluster_metrics_tab.winfo_children():
            w.destroy()

        text = tk.Text(self.cluster_metrics_tab, font=("Courier", 8), padx=5, pady=5)
        text.pack(fill=tk.BOTH, expand=True)

        unique_clusters = len(np.unique(self.cluster_labels))

        if unique_clusters > 1:
            silhouette = silhouette_score(X, self.cluster_labels)
            davies_bouldin = davies_bouldin_score(X, self.cluster_labels)
        else:
            silhouette = -1
            davies_bouldin = float('inf')

        report = f"""
{'='*50}
CLUSTERING METRICS
{'='*50}

Method: {self.cluster_method.get().title()}
Clusters: {unique_clusters}
Samples: {len(X)}

{'='*50}
QUALITY
{'='*50}

Silhouette:      {silhouette:.3f}
Davies-Bouldin:  {davies_bouldin:.3f}

{'='*50}
CLUSTER SIZES
{'='*50}

"""
        for i in range(1, unique_clusters + 1):
            size = np.sum(self.cluster_labels == i)
            report += f"Cluster {i}: {size}\n"

        text.insert(1.0, report)
        text.config(state=tk.DISABLED)

    def _update_cluster_details(self):
        for w in self.cluster_details_tab.winfo_children():
            w.destroy()

        frame = ttk.Frame(self.cluster_details_tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        vsb = ttk.Scrollbar(frame)
        hsb = ttk.Scrollbar(frame, orient=tk.HORIZONTAL)

        columns = ('ID', 'Group', 'Cluster')
        tree = ttk.Treeview(frame, columns=columns, show='headings',
                           yscrollcommand=vsb.set, xscrollcommand=hsb.set, height=10)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=80)

        for i, idx in enumerate(self.valid_indices):
            sample_id = self.samples[idx].get('Sample_ID', f'S{idx}')
            group = self.group_labels[idx] if self.group_labels else '-'
            cluster = self.cluster_labels[i] if i < len(self.cluster_labels) else '-'
            tree.insert('', 'end', values=(sample_id, group, cluster))

        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        vsb.config(command=tree.yview)
        hsb.config(command=tree.xview)

    # ============================================================================
    # NEW TAB: Statistical Tests
    # ============================================================================

    def _create_stats_tests_tab(self, parent):
        """Create statistical tests tab"""
        ctrl = ttk.LabelFrame(parent, text="Tests", padding=2)
        ctrl.pack(fill=tk.X, pady=1)

        type_frame = ttk.Frame(ctrl)
        type_frame.pack(fill=tk.X, pady=1)

        ttk.Label(type_frame, text="Test:").pack(side=tk.LEFT)
        self.stats_test_combo = ttk.Combobox(type_frame, textvariable=self.stats_test_type,
                                            values=self.stats_test_types, width=8, state='readonly')
        self.stats_test_combo.pack(side=tk.LEFT, padx=1)
        self.stats_test_combo.bind('<<ComboboxSelected>>', self._update_stats_ui)

        self.stats_vars_frame = ttk.Frame(ctrl)
        self.stats_vars_frame.pack(fill=tk.X, pady=1)

        ttk.Button(ctrl, text="▶️ Run", width=6,
                  command=self._run_statistical_test).pack(pady=1)

        self.stats_results_text = tk.Text(parent, font=("Courier", 8), height=15)
        scroll = ttk.Scrollbar(parent, command=self.stats_results_text.yview)
        self.stats_results_text.config(yscrollcommand=scroll.set)

        self.stats_results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self._update_stats_ui()

    def _update_stats_ui(self, event=None):
        for w in self.stats_vars_frame.winfo_children():
            w.destroy()

        test_type = self.stats_test_type.get()

        if test_type == "ttest":
            self._create_ttest_ui()
        elif test_type == "mannwhitney":
            self._create_mannwhitney_ui()
        elif test_type == "anova":
            self._create_anova_ui()

    def _create_ttest_ui(self):
        ttk.Label(self.stats_vars_frame, text="Var:").grid(row=0, column=0, sticky=tk.W, padx=1)
        self.stats_var1_combo = ttk.Combobox(self.stats_vars_frame, textvariable=self.stats_var1,
                                            values=self.numeric_columns, width=8)
        self.stats_var1_combo.grid(row=0, column=1, padx=1)

        ttk.Label(self.stats_vars_frame, text="Group:").grid(row=1, column=0, sticky=tk.W, padx=1)
        self.stats_group_combo = ttk.Combobox(self.stats_vars_frame, textvariable=self.stats_group,
                                             values=self.categorical_columns, width=8)
        self.stats_group_combo.grid(row=1, column=1, padx=1)
        self.stats_group_combo.bind('<<ComboboxSelected>>', self._update_ttest_groups)

        ttk.Label(self.stats_vars_frame, text="G1:").grid(row=2, column=0, sticky=tk.W, padx=1)
        self.stats_group1_combo = ttk.Combobox(self.stats_vars_frame, textvariable=self.stats_group1,
                                              values=[], width=8)
        self.stats_group1_combo.grid(row=2, column=1, padx=1)

        ttk.Label(self.stats_vars_frame, text="G2:").grid(row=3, column=0, sticky=tk.W, padx=1)
        self.stats_group2_combo = ttk.Combobox(self.stats_vars_frame, textvariable=self.stats_group2,
                                              values=[], width=8)
        self.stats_group2_combo.grid(row=3, column=1, padx=1)

    def _create_mannwhitney_ui(self):
        ttk.Label(self.stats_vars_frame, text="Var:").grid(row=0, column=0, sticky=tk.W, padx=1)
        self.stats_var1_combo = ttk.Combobox(self.stats_vars_frame, textvariable=self.stats_var1,
                                            values=self.numeric_columns, width=8)
        self.stats_var1_combo.grid(row=0, column=1, padx=1)

        ttk.Label(self.stats_vars_frame, text="Group:").grid(row=1, column=0, sticky=tk.W, padx=1)
        self.stats_group_combo = ttk.Combobox(self.stats_vars_frame, textvariable=self.stats_group,
                                             values=self.categorical_columns, width=8)
        self.stats_group_combo.grid(row=1, column=1, padx=1)
        self.stats_group_combo.bind('<<ComboboxSelected>>', self._update_ttest_groups)

        ttk.Label(self.stats_vars_frame, text="G1:").grid(row=2, column=0, sticky=tk.W, padx=1)
        self.stats_group1_combo = ttk.Combobox(self.stats_vars_frame, textvariable=self.stats_group1,
                                              values=[], width=8)
        self.stats_group1_combo.grid(row=2, column=1, padx=1)

        ttk.Label(self.stats_vars_frame, text="G2:").grid(row=3, column=0, sticky=tk.W, padx=1)
        self.stats_group2_combo = ttk.Combobox(self.stats_vars_frame, textvariable=self.stats_group2,
                                              values=[], width=8)
        self.stats_group2_combo.grid(row=3, column=1, padx=1)

    def _create_anova_ui(self):
        ttk.Label(self.stats_vars_frame, text="Dependent:").grid(row=0, column=0, sticky=tk.W, padx=1)
        self.stats_var1_combo = ttk.Combobox(self.stats_vars_frame, textvariable=self.stats_var1,
                                            values=self.numeric_columns, width=8)
        self.stats_var1_combo.grid(row=0, column=1, padx=1)

        ttk.Label(self.stats_vars_frame, text="Factor:").grid(row=1, column=0, sticky=tk.W, padx=1)
        self.stats_group_combo = ttk.Combobox(self.stats_vars_frame, textvariable=self.stats_group,
                                             values=self.categorical_columns, width=8)
        self.stats_group_combo.grid(row=1, column=1, padx=1)

    def _update_ttest_groups(self, event=None):
        group = self.stats_group.get()
        if group and self.samples:
            values = set()
            for s in self.samples:
                val = s.get(group, '')
                if val:
                    values.add(str(val))
            values = sorted(values)
            self.stats_group1_combo['values'] = values
            self.stats_group2_combo['values'] = values

    def _run_statistical_test(self):
        test_type = self.stats_test_type.get()

        if test_type == "ttest":
            self._run_ttest()
        elif test_type == "mannwhitney":
            self._run_mannwhitney()
        elif test_type == "anova":
            self._run_anova()

    def _run_ttest(self):
        var = self.stats_var1.get()
        group = self.stats_group.get()
        group1 = self.stats_group1.get()
        group2 = self.stats_group2.get()

        if not all([var, group, group1, group2]):
            messagebox.showwarning("Warning", "Please fill all fields")
            return

        data1 = []
        data2 = []

        for s in self.samples:
            group_val = s.get(group, '')
            if group_val == group1:
                try:
                    val = float(s.get(var, np.nan))
                    if not np.isnan(val):
                        data1.append(val)
                except:
                    pass
            elif group_val == group2:
                try:
                    val = float(s.get(var, np.nan))
                    if not np.isnan(val):
                        data2.append(val)
                except:
                    pass

        if len(data1) < 2 or len(data2) < 2:
            messagebox.showwarning("Warning", "Need at least 2 observations per group")
            return

        equal_var = self.stats_equal_var.get()

        levene_stat, levene_p = levene(data1, data2)

        t_stat, p_value = ttest_ind(data1, data2, equal_var=equal_var)

        pooled_std = np.sqrt(((len(data1)-1)*np.var(data1) + (len(data2)-1)*np.var(data2)) /
                            (len(data1) + len(data2) - 2))
        cohens_d = (np.mean(data1) - np.mean(data2)) / pooled_std if pooled_std > 0 else 0

        alpha = self.config.settings.get('alpha', 0.05)

        report = f"""
{'='*50}
T-TEST
{'='*50}

Variable: {var}
Groups: {group1} (n={len(data1)}) vs {group2} (n={len(data2)})

{'='*50}
RESULTS
{'='*50}

{group1}: Mean={np.mean(data1):.3f} SD={np.std(data1):.3f}
{group2}: Mean={np.mean(data2):.3f} SD={np.std(data2):.3f}
Difference: {np.mean(data1)-np.mean(data2):.3f}

Levene's test: p={levene_p:.3f}
t-statistic: {t_stat:.3f}
p-value: {p_value:.4f}
Cohen's d: {cohens_d:.3f}

{'='*50}
"""
        if p_value < alpha:
            report += f"✓ Significant difference (p < {alpha})"
        else:
            report += f"✗ No significant difference (p ≥ {alpha})"

        self.stats_results_text.delete(1.0, tk.END)
        self.stats_results_text.insert(1.0, report)

    def _run_mannwhitney(self):
        var = self.stats_var1.get()
        group = self.stats_group.get()
        group1 = self.stats_group1.get()
        group2 = self.stats_group2.get()

        if not all([var, group, group1, group2]):
            messagebox.showwarning("Warning", "Please fill all fields")
            return

        data1 = []
        data2 = []

        for s in self.samples:
            group_val = s.get(group, '')
            if group_val == group1:
                try:
                    val = float(s.get(var, np.nan))
                    if not np.isnan(val):
                        data1.append(val)
                except:
                    pass
            elif group_val == group2:
                try:
                    val = float(s.get(var, np.nan))
                    if not np.isnan(val):
                        data2.append(val)
                except:
                    pass

        if len(data1) < 2 or len(data2) < 2:
            messagebox.showwarning("Warning", "Need at least 2 observations per group")
            return

        u_stat, p_value = mannwhitneyu(data1, data2)

        n1, n2 = len(data1), len(data2)
        z = (u_stat - n1*n2/2) / np.sqrt(n1*n2*(n1+n2+1)/12)
        r = abs(z) / np.sqrt(n1 + n2)

        alpha = self.config.settings.get('alpha', 0.05)

        report = f"""
{'='*50}
MANN-WHITNEY U
{'='*50}

Variable: {var}
Groups: {group1} (n={len(data1)}) vs {group2} (n={len(data2)})

{'='*50}
RESULTS
{'='*50}

{group1}: Median={np.median(data1):.3f}
{group2}: Median={np.median(data2):.3f}

U-statistic: {u_stat:.0f}
z-score: {z:.3f}
p-value: {p_value:.4f}
Effect size (r): {r:.3f}

{'='*50}
"""
        if p_value < alpha:
            report += f"✓ Significant difference (p < {alpha})"
        else:
            report += f"✗ No significant difference (p ≥ {alpha})"

        self.stats_results_text.delete(1.0, tk.END)
        self.stats_results_text.insert(1.0, report)

    def _run_anova(self):
        dep = self.stats_var1.get()
        factor = self.stats_group.get()

        if not dep or not factor:
            messagebox.showwarning("Warning", "Please select dependent variable and factor")
            return

        groups = {}
        for s in self.samples:
            group_val = s.get(factor, '')
            if group_val:
                try:
                    val = float(s.get(dep, np.nan))
                    if not np.isnan(val):
                        if group_val not in groups:
                            groups[group_val] = []
                        groups[group_val].append(val)
                except:
                    pass

        groups = {k: v for k, v in groups.items() if len(v) >= 2}

        if len(groups) < 2:
            messagebox.showwarning("Warning", "Need at least 2 groups with ≥2 observations")
            return

        group_names = list(groups.keys())
        group_data = list(groups.values())

        levene_stat, levene_p = levene(*group_data)

        f_stat, p_value = f_oneway(*group_data)

        all_data = np.concatenate(group_data)
        grand_mean = np.mean(all_data)

        ss_between = sum(len(g) * (np.mean(g) - grand_mean)**2 for g in group_data)
        ss_total = sum((g - grand_mean)**2 for g in group_data)
        eta_sq = ss_between / ss_total if ss_total > 0 else 0

        alpha = self.config.settings.get('alpha', 0.05)

        report = f"""
{'='*50}
ANOVA
{'='*50}

Dependent: {dep}
Factor: {factor}
Groups: {len(groups)}

{'='*50}
GROUP STATS
{'='*50}
"""
        for name, data in groups.items():
            report += f"{name}: n={len(data)} Mean={np.mean(data):.3f}\n"

        report += f"""
{'='*50}
RESULTS
{'='*50}

Levene's test: p={levene_p:.3f}
F-statistic: {f_stat:.3f}
p-value: {p_value:.4f}
η² = {eta_sq:.3f}

{'='*50}
"""
        if p_value < alpha:
            report += f"✓ Significant difference (p < {alpha})"
        else:
            report += f"✗ No significant difference (p ≥ {alpha})"

        self.stats_results_text.delete(1.0, tk.END)
        self.stats_results_text.insert(1.0, report)

    # ============================================================================
    # EXISTING DATA HANDLING METHODS
    # ============================================================================

    def _import_from_main(self):
        """Import data from main app"""
        if hasattr(self.app, 'samples'):
            self.samples = self.app.samples.copy()
            self._refresh_data()
            self.status_var.set(f"✅ Imported {len(self.samples)} samples")

            # Update regression target
            if hasattr(self, 'reg_target_combo'):
                self.reg_target_combo['values'] = self.numeric_columns
                if self.numeric_columns:
                    self.reg_target.set(self.numeric_columns[0])
        else:
            messagebox.showerror("Error", "No data in main table")

    def _export_to_main(self):
        """Export results back to main app"""
        if self.current_scores is None:
            messagebox.showwarning("Warning", "Run analysis first")
            return

        if not hasattr(self.app, 'import_data_from_plugin'):
            messagebox.showerror("Error", "Main app doesn't support import")
            return

        records = []
        for i, idx in enumerate(self.valid_indices):
            sample = self.samples[idx].copy()

            for pc in range(min(3, self.current_scores.shape[1])):
                sample[f'PC{pc+1}'] = f"{self.current_scores[i, pc]:.3f}"

            if self.cluster_labels is not None and i < len(self.cluster_labels):
                sample['Cluster'] = f"C{self.cluster_labels[i]}"

            records.append(sample)

        self.app.import_data_from_plugin(records)
        self.status_var.set(f"✅ Exported {len(records)} records")

    def _refresh_data(self):
        if hasattr(self.app, 'samples'):
            self.samples = self.app.samples
            self._detect_columns()
            self.group_combo['values'] = ["None"] + self.categorical_columns
            self.group_combo.current(0)
            self._update_element_list()

            if hasattr(self, 'corr_listbox'):
                self._update_corr_listbox()
            if hasattr(self, 'reg_listbox'):
                self.reg_listbox.delete(0, tk.END)
                for col in sorted(self.numeric_columns):
                    self.reg_listbox.insert(tk.END, col)

            if hasattr(self, 'reg_target_combo'):
                self.reg_target_combo['values'] = self.numeric_columns
                if self.numeric_columns and not self.reg_target.get():
                    self.reg_target.set(self.numeric_columns[0])

            self.status_var.set(f"Loaded {len(self.samples)} samples")

    def _update_element_list(self):
        self.element_listbox.delete(0, tk.END)
        for col in sorted(self.numeric_columns):
            self.element_listbox.insert(tk.END, col)

    def _update_corr_listbox(self):
        self.corr_listbox.delete(0, tk.END)
        for col in sorted(self.numeric_columns):
            self.corr_listbox.insert(tk.END, col)

    def _select_all(self):
        self.element_listbox.selection_set(0, tk.END)

    def _clear_all(self):
        self.element_listbox.selection_clear(0, tk.END)

    def _select_major(self):
        majors = ['SiO2', 'TiO2', 'Al2O3', 'Fe2O3', 'MgO', 'CaO', 'Na2O', 'K2O', 'P2O5']
        self._select_by_pattern(majors)

    def _select_trace(self):
        traces = ['Zr', 'Nb', 'Ba', 'Rb', 'Sr', 'Cr', 'Ni', 'V', 'Y', 'Th', 'U', 'Pb']
        self._select_by_pattern(traces)

    def _select_ree(self):
        ree = ['La', 'Ce', 'Pr', 'Nd', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy', 'Ho', 'Er', 'Tm', 'Yb', 'Lu']
        self._select_by_pattern(ree)

    def _select_by_pattern(self, patterns):
        self.element_listbox.selection_clear(0, tk.END)
        for i, elem in enumerate(self.element_listbox.get(0, tk.END)):
            if any(p in elem for p in patterns):
                self.element_listbox.selection_set(i)

    def _update_group(self):
        if self.group_var.get() != "None" and self.samples:
            self.group_labels = [str(s.get(self.group_var.get(), 'Unknown')) for s in self.samples]
            self.unique_groups = list(set(self.group_labels))
            self.n_groups = len(self.unique_groups)

    def _handle_missing(self, data):
        strategy = self.impute_var.get()
        data = np.array(data, dtype=float)

        if strategy == "discard":
            valid = ~np.isnan(data).any(axis=1)
            return data[valid], [i for i, v in enumerate(valid) if v]
        elif strategy == "mean":
            imp = SimpleImputer(strategy='mean')
            return imp.fit_transform(data), list(range(len(data)))
        elif strategy == "median":
            imp = SimpleImputer(strategy='median')
            return imp.fit_transform(data), list(range(len(data)))
        else:
            imp = KNNImputer(n_neighbors=5)
            return imp.fit_transform(data), list(range(len(data)))

    # ============================================================================
    # EXISTING ANALYSIS METHODS
    # ============================================================================

    def _run_analysis(self):
        selected = self.element_listbox.curselection()
        if len(selected) < 2:
            messagebox.showwarning("Warning", "Select at least 2 elements")
            return

        elements = [self.element_listbox.get(i) for i in selected]

        data = []
        for s in self.samples:
            row = []
            for e in elements:
                try:
                    row.append(float(s.get(e, np.nan)))
                except:
                    row.append(np.nan)
            data.append(row)

        X, self.valid_indices = self._handle_missing(data)
        if len(X) < 3:
            messagebox.showwarning("Warning", "Need at least 3 valid samples")
            return

        if self.group_var.get() != "None" and self.samples:
            self.group_labels = [str(s.get(self.group_var.get(), 'Unknown')) for s in self.samples]
            group_subset = [self.group_labels[i] for i in self.valid_indices]
            self.unique_groups = list(set(group_subset))
            self.n_groups = len(self.unique_groups)
        else:
            group_subset = None

        self.group_subset = group_subset

        if self.scale_var.get():
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
        else:
            X_scaled = X

        n_comp = min(self.n_components_var.get(), X.shape[1], X.shape[0])
        self.current_pca = PCA(n_components=n_comp)
        self.current_scores = self.current_pca.fit_transform(X_scaled)
        self.current_loadings = self.current_pca.components_.T
        self.current_elements = elements

        self._update_biplot()
        self._update_3d()
        self._update_scree()
        self._update_loadings()

        if group_subset and len(set(group_subset)) >= 2:
            self._run_ml_models()
            self._update_lda_tab()
            self._update_plsda_tab()
            self._update_rf_tab()
            self._update_svm_tab()
            self._update_compare_tab()

        self.status_var.set(f"✅ Complete - {len(X)} samples, {len(elements)} elements")

    def _update_biplot(self):
        self.ax.clear()

        pc_x, pc_y = self.pc_x_var.get()-1, self.pc_y_var.get()-1
        scores = self.current_scores
        exp_var = self.current_pca.explained_variance_ratio_

        if hasattr(self, 'group_subset') and self.group_subset is not None:
            unique = list(set(self.group_subset))
            colors = plt.cm.tab10(np.linspace(0, 1, len(unique)))

            for i, g in enumerate(unique):
                mask = [self.group_subset[j] == g for j in range(len(self.group_subset))]
                self.ax.scatter(scores[mask, pc_x], scores[mask, pc_y],
                            c=[colors[i]], label=g[:8], alpha=0.7, s=20)

                if self.ellipse_var.get() and sum(mask) >= 3:
                    points = scores[mask][:, [pc_x, pc_y]]
                    self._add_ellipse(points, colors[i])
        else:
            self.ax.scatter(scores[:, pc_x], scores[:, pc_y], alpha=0.6, s=20, c='steelblue')

        scale = (scores[:, pc_x].max() - scores[:, pc_x].min()) * 0.7
        n_to_plot = min(self.current_loadings.shape[0], len(self.current_elements))

        for i in range(n_to_plot):
            x = self.current_loadings[i, pc_x] * scale
            y = self.current_loadings[i, pc_y] * scale
            self.ax.arrow(0, 0, x, y, alpha=0.3, head_width=scale*0.02, color='red')
            self.ax.text(x*1.1, y*1.1, self.current_elements[i][:6], fontsize=6)

        self.ax.set_xlabel(f'PC{pc_x+1} ({exp_var[pc_x]*100:.0f}%)')
        self.ax.set_ylabel(f'PC{pc_y+1} ({exp_var[pc_y]*100:.0f}%)')
        self.ax.grid(True, alpha=0.3)

        self.canvas.draw()

    def _add_ellipse(self, points, color):
        if len(points) < 3:
            return

        cov = np.cov(points.T)
        mean = np.mean(points, axis=0)

        vals, vecs = np.linalg.eigh(cov)
        order = vals.argsort()[::-1]
        vals, vecs = vals[order], vecs[:, order]

        theta = np.degrees(np.arctan2(*vecs[:, 0][::-1]))
        width, height = 2 * np.sqrt(5.991 * vals)

        ellipse = Ellipse(xy=mean, width=width, height=height,
                        angle=theta, edgecolor=color, facecolor='none',
                        linewidth=1, linestyle='--')
        self.ax.add_patch(ellipse)

    def _update_3d(self):
        self.ax3d.clear()
        pc_x, pc_y, pc_z = self.pc_x_var.get()-1, self.pc_y_var.get()-1, self.pc_z_var.get()-1
        scores = self.current_scores

        if hasattr(self, 'group_subset') and self.group_subset is not None:
            unique = list(set(self.group_subset))
            colors = plt.cm.tab10(np.linspace(0, 1, len(unique)))

            for i, g in enumerate(unique):
                mask = [self.group_subset[j] == g for j in range(len(self.group_subset))]
                self.ax3d.scatter(scores[mask, pc_x], scores[mask, pc_y], scores[mask, pc_z],
                                c=[colors[i]], label=g[:8], alpha=0.7, s=15)
        else:
            self.ax3d.scatter(scores[:, pc_x], scores[:, pc_y], scores[:, pc_z],
                            alpha=0.6, s=15, c='steelblue')

        self.ax3d.set_xlabel(f'PC{pc_x+1}')
        self.ax3d.set_ylabel(f'PC{pc_y+1}')
        self.ax3d.set_zlabel(f'PC{pc_z+1}')
        self.canvas3d.draw()

    def _update_scree(self):
        self.scree_ax.clear()
        exp_var = self.current_pca.explained_variance_ratio_
        comp = range(1, len(exp_var)+1)

        bars = self.scree_ax.bar(comp, exp_var, alpha=0.6, color='steelblue')
        self.scree_ax.plot(comp, np.cumsum(exp_var), 'ro-', linewidth=2, markersize=4)

        for bar, val in zip(bars, exp_var):
            self.scree_ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.01,
                              f'{val*100:.0f}%', ha='center', fontsize=6)

        self.scree_ax.set_xlabel('PC')
        self.scree_ax.set_ylabel('Variance %')
        self.scree_ax.set_title('Scree Plot')
        self.scree_ax.grid(True, alpha=0.3)
        self.scree_canvas.draw()

    def _update_loadings(self):
        self.loadings_text.delete(1.0, tk.END)
        exp_var = self.current_pca.explained_variance_ratio_

        header = "Element"
        n_pcs_to_show = min(6, len(exp_var))
        for i in range(n_pcs_to_show):
            header += f"  PC{i+1}({exp_var[i]*100:.0f}%)"
        self.loadings_text.insert(tk.END, header + "\n" + "-"*50 + "\n")

        n_loadings = self.current_loadings.shape[0]
        n_elements = len(self.current_elements)
        n_to_show = min(n_loadings, n_elements)

        for i in range(n_to_show):
            line = f"{self.current_elements[i]:<8}"
            for j in range(n_pcs_to_show):
                if j < self.current_loadings.shape[1]:
                    line += f"  {self.current_loadings[i, j]:>6.3f}"
            self.loadings_text.insert(tk.END, line + "\n")

    def _run_ml_models(self):
        X = self.current_scores[:, :self.n_pcs_var.get()]
        y = np.array(self.group_subset)

        n_samples = len(y)
        n_classes = len(np.unique(y))

        if n_samples <= n_classes:
            self.status_var.set(f"⚠️ Not enough samples for LDA")
            self.model_results = {}
            return

        self.model_results = {}

        lda = LDA()
        lda.fit(X, y)
        y_pred = lda.predict(X)
        self.lda_model = lda
        self.model_results['LDA'] = {
            'accuracy': accuracy_score(y, y_pred) * 100,
            'balanced': balanced_accuracy_score(y, y_pred) * 100,
            'kappa': cohen_kappa_score(y, y_pred)
        }

        if self.plsda_var.get():
            try:
                plsda = PLSDAWithVIP(n_components=min(2, X.shape[1]))
                plsda.fit(X, y)
                self.plsda_model = plsda
                self.plsda_vip = plsda.vip_per_class
                y_pred = plsda.predict(X)
                self.model_results['PLS-DA'] = {
                    'accuracy': accuracy_score(y, y_pred) * 100,
                    'balanced': balanced_accuracy_score(y, y_pred) * 100,
                    'kappa': cohen_kappa_score(y, y_pred)
                }
            except:
                pass

        if self.rf_var.get():
            try:
                rf = RandomForestClassifier(n_estimators=self.n_trees_var.get(),
                                            random_state=42, n_jobs=-1)
                rf.fit(X, y)
                self.rf_model = rf
                y_pred = rf.predict(X)
                self.model_results['RF'] = {
                    'accuracy': accuracy_score(y, y_pred) * 100,
                    'balanced': balanced_accuracy_score(y, y_pred) * 100,
                    'kappa': cohen_kappa_score(y, y_pred),
                    'importance': rf.feature_importances_
                }
            except:
                pass

        if self.svm_var.get():
            try:
                svm = SVC(kernel=self.svm_kernel_var.get(), probability=True)
                svm.fit(X, y)
                self.svm_model = svm
                y_pred = svm.predict(X)
                self.model_results['SVM'] = {
                    'accuracy': accuracy_score(y, y_pred) * 100,
                    'balanced': balanced_accuracy_score(y, y_pred) * 100,
                    'kappa': cohen_kappa_score(y, y_pred)
                }
            except:
                pass

    def _update_lda_tab(self):
        for w in self.lda_frame.winfo_children():
            w.destroy()

        if self.lda_model is None:
            return

        X = self.current_scores[:, :self.n_pcs_var.get()]
        y = np.array(self.group_subset)

        X_lda = self.lda_model.transform(X)

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 4))

        colors = plt.cm.tab10(np.linspace(0, 1, self.n_groups))

        if X_lda.shape[1] >= 2:
            for i, g in enumerate(self.unique_groups):
                mask = y == g
                ax1.scatter(X_lda[mask, 0], X_lda[mask, 1],
                           c=[colors[i]], label=g[:8], alpha=0.7, s=20)
            ax1.set_xlabel('LD1')
            ax1.set_ylabel('LD2')
        else:
            for i, g in enumerate(self.unique_groups):
                mask = y == g
                x_vals = X_lda[mask].flatten()
                y_jitter = np.random.normal(0, 0.05, size=len(x_vals))
                ax1.scatter(x_vals, y_jitter, c=[colors[i]], label=g[:8], alpha=0.7, s=20)
            ax1.set_xlabel('LD1')
            ax1.set_ylabel('Jitter')

        ax1.set_title(f'LDA - acc: {self.model_results["LDA"]["accuracy"]:.0f}%')
        ax1.grid(True, alpha=0.3)

        y_pred = self.lda_model.predict(X)
        cm = confusion_matrix(y, y_pred)
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax2,
                   xticklabels=self.unique_groups, yticklabels=self.unique_groups)
        ax2.set_title('Confusion Matrix')

        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, self.lda_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _update_plsda_tab(self):
        for w in self.plsda_frame.winfo_children():
            w.destroy()

        if not self.plsda_vip:
            ttk.Label(self.plsda_frame, text="PLS-DA not available").pack(expand=True)
            return

        text = tk.Text(self.plsda_frame, font=("Courier", 8))
        scroll = ttk.Scrollbar(self.plsda_frame, command=text.yview)
        text.config(yscrollcommand=scroll.set)

        text.insert(tk.END, "PLS-DA VIP Scores:\n\n")
        for class_name, vip in self.plsda_vip.items():
            text.insert(tk.END, f"\n{class_name}:\n")
            top_idx = np.argsort(vip)[::-1][:8]
            for i in top_idx:
                stars = "***" if vip[i] > 1 else "**" if vip[i] > 0.8 else "*"
                text.insert(tk.END, f"  {self.current_elements[i]}: {vip[i]:.2f} {stars}\n")

        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def _update_rf_tab(self):
        for w in self.rf_frame.winfo_children():
            w.destroy()

        if self.rf_model is None:
            ttk.Label(self.rf_frame, text="RF not available").pack(expand=True)
            return

        fig, ax = plt.subplots(figsize=(6, 4))

        imp = self.rf_model.feature_importances_
        idx = np.argsort(imp)[::-1][:10]
        ax.barh(range(len(idx)), imp[idx], color='steelblue')
        ax.set_yticks(range(len(idx)))
        ax.set_yticklabels([f'PC{i+1}' for i in idx])
        ax.set_xlabel('Importance')
        ax.set_title(f'RF - acc: {self.model_results["RF"]["accuracy"]:.0f}%')
        ax.grid(True, alpha=0.3, axis='x')

        canvas = FigureCanvasTkAgg(fig, self.rf_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _update_svm_tab(self):
        for w in self.svm_frame.winfo_children():
            w.destroy()

        if self.svm_model is None:
            ttk.Label(self.svm_frame, text="SVM not available").pack(expand=True)
            return

        fig, ax = plt.subplots(figsize=(6, 5))

        X = self.current_scores[:, :2]
        y = np.array([self.group_labels[i] for i in self.valid_indices])

        colors = plt.cm.tab10(np.linspace(0, 1, self.n_groups))
        for i, g in enumerate(self.unique_groups):
            mask = y == g
            ax.scatter(X[mask, 0], X[mask, 1],
                      c=[colors[i]], label=g[:8], alpha=0.7, s=20)

        ax.set_xlabel('PC1')
        ax.set_ylabel('PC2')
        ax.set_title(f'SVM ({self.svm_kernel_var.get()})')
        ax.grid(True, alpha=0.3)

        canvas = FigureCanvasTkAgg(fig, self.svm_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _update_compare_tab(self):
        for w in self.compare_frame.winfo_children():
            w.destroy()

        if not self.model_results:
            ttk.Label(self.compare_frame, text="No models to compare").pack(expand=True)
            return

        frame = ttk.Frame(self.compare_frame)
        frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        vsb = ttk.Scrollbar(frame)

        columns = ('Model', 'Accuracy', 'Kappa')
        tree = ttk.Treeview(frame, columns=columns, show='headings',
                           yscrollcommand=vsb.set, height=6)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=70)

        for name, res in self.model_results.items():
            tree.insert('', 'end', values=(
                name,
                f"{res['accuracy']:.0f}%",
                f"{res['kappa']:.2f}"
            ))

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

    def _manage_outliers(self):
        if self.current_scores is None:
            messagebox.showwarning("Warning", "Run analysis first")
            return

        sample_ids = [self.samples[i].get('Sample_ID', f'S{i}')
                     for i in self.valid_indices]
        groups = [self.group_labels[i] for i in self.valid_indices] if self.group_labels else ['']*len(sample_ids)

        OutlierDialog(self.window, self.current_scores[:, :self.n_pcs_var.get()],
                     sample_ids, groups, self._exclude_outliers)

    def _exclude_outliers(self, exclude_indices):
        exclude_global = [self.valid_indices[i] for i in exclude_indices]
        keep = [i for i in range(len(self.samples)) if i not in exclude_global]
        self.samples = [self.samples[i] for i in keep]
        self.status_var.set(f"Excluded {len(exclude_indices)} outliers")
        self._refresh_data()

    def _show_group_stats(self):
        if self.current_scores is None:
            messagebox.showwarning("Warning", "Run analysis first")
            return

        sample_ids = [self.samples[i].get('Sample_ID', f'S{i}')
                     for i in self.valid_indices]
        groups = [self.group_labels[i] for i in self.valid_indices] if self.group_labels else []

        GroupStatisticsPopup(self.window, self.current_scores, groups, sample_ids,
                            self.current_loadings, self.current_elements)

    def _open_settings(self):
        SettingsDialog(self.window, self.config)

    def _on_close(self):
        self.config.save_settings()
        plt.close('all')
        if self.window:
            self.window.destroy()


# ============================================================================
# SETTINGS DIALOG
# ============================================================================

class SettingsDialog:
    """Settings dialog for user preferences"""

    def __init__(self, parent, config):
        self.parent = parent
        self.config = config

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("⚙️ Settings")
        self.dialog.geometry("350x200")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._create_ui()

    def _create_ui(self):
        main = tk.Frame(self.dialog, padx=10, pady=10)
        main.pack(fill=tk.BOTH, expand=True)

        tk.Label(main, text="Settings", font=("Arial", 12, "bold")).pack(pady=5)

        tk.Label(main, text="Significance level (α):").pack(anchor=tk.W, pady=2)
        self.alpha_var = tk.DoubleVar(value=self.config.settings.get('alpha', 0.05))
        tk.Spinbox(main, from_=0.001, to=0.1, increment=0.001,
                  textvariable=self.alpha_var, width=8).pack(anchor=tk.W)

        self.recall_var = tk.BooleanVar(value=self.config.settings.get('recall_last', True))
        tk.Checkbutton(main, text="Remember last used variables",
                      variable=self.recall_var).pack(anchor=tk.W, pady=5)

        tk.Button(main, text="Save", command=self._save_settings,
                 bg="#27ae60", fg="white", width=10).pack(pady=10)

    def _save_settings(self):
        self.config.settings['alpha'] = self.alpha_var.get()
        self.config.settings['recall_last'] = self.recall_var.get()
        self.config.save_settings()
        self.dialog.destroy()


# ============================================================================
# PLUGIN SETUP
# ============================================================================

def setup_plugin(main_app):
    """Plugin setup"""
    return PCALDAExplorerPlugin(main_app)
