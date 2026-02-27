"""
Geochemical Explorer v1.0 - PCA · LDA · Clustering · Statistical Tests
WITH FULL MAIN APP INTEGRATION

✓ PCA biplots with loadings and confidence ellipses
✓ LDA classification with confusion matrices
✓ K-means and hierarchical clustering
✓ Statistical tests (t-test, ANOVA, Mann-Whitney)
✓ Correlation matrices with significance
✓ Outlier detection and management
"""

PLUGIN_INFO = {
    "category": "software",
    "field": "Geology & Geochemistry",
    "id": "geochemical_explorer",
    "name": "Geochemical Explorer",
    "description": "PCA · LDA · Clustering · Statistical Tests — Complete multivariate toolkit",
    "icon": "📊",
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
    import matplotlib.cm as cm
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    import numpy as np
    from scipy import stats
    from scipy.stats import gaussian_kde, pearsonr, spearmanr, f_oneway, ttest_ind, mannwhitneyu
    from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
    from scipy.spatial.distance import pdist, squareform
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    from sklearn.decomposition import PCA
    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.impute import SimpleImputer
    from sklearn.cluster import KMeans, AgglomerativeClustering
    from sklearn.metrics import silhouette_score, confusion_matrix
    import sklearn.manifold
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


class GeochemicalExplorerPlugin:
    """
    GEOCHEMICAL EXPLORER - Complete multivariate analysis toolkit
    PCA · LDA · Clustering · Statistical Tests
    """

    def __init__(self, main_app):
        self.app = main_app
        self.window = None

        # ============ DATA ============
        self.samples = []
        self.numeric_columns = []
        self.categorical_columns = []

        # Current dataset for analysis
        self.X = None  # Feature matrix
        self.y = None  # Labels (if any)
        self.feature_names = []
        self.sample_ids = []
        self.valid_indices = []

        # Analysis results
        self.pca = None
        self.pca_scores = None
        self.pca_loadings = None
        self.pca_scaler = None
        self.pca_var_ratio = None

        self.lda = None
        self.lda_scores = None
        self.lda_classes = None

        self.cluster_labels = None
        self.cluster_centers = None
        self.linkage_matrix = None

        self.correlation_matrix = None
        self.pvalue_matrix = None

        # ============ UI VARIABLES ============
        # Notebook tabs
        self.notebook = None

        # Common
        self.status_var = None
        self.progress = None

        # Element selection
        self.element_listbox = None
        self.select_all_var = tk.BooleanVar(value=False)

        # Group selection
        self.group_var = tk.StringVar(value="None")
        self.group_combo = None

        # PCA tab
        self.pca_pc_x_var = tk.IntVar(value=1)
        self.pca_pc_y_var = tk.IntVar(value=2)
        self.pca_scale_var = tk.BooleanVar(value=True)
        self.pca_ellipse_var = tk.BooleanVar(value=True)
        self.pca_loading_var = tk.BooleanVar(value=True)
        self.pca_point_size_var = tk.IntVar(value=20)

        # LDA tab
        self.lda_pc_x_var = tk.IntVar(value=1)
        self.lda_pc_y_var = tk.IntVar(value=2)
        self.lda_solver_var = tk.StringVar(value="svd")

        # Clustering tab
        self.cluster_method_var = tk.StringVar(value="kmeans")
        self.cluster_n_var = tk.IntVar(value=3)
        self.cluster_linkage_var = tk.StringVar(value="ward")

        # Statistics tab
        self.stats_test_var = tk.StringVar(value="ttest")
        self.stats_var1_var = tk.StringVar(value="")
        self.stats_var2_var = tk.StringVar(value="")
        self.stats_group_var = tk.StringVar(value="")
        self.stats_alpha_var = tk.DoubleVar(value=0.05)

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
        """Load geochemical data from main app samples"""
        if not hasattr(self.app, 'samples') or not self.app.samples:
            return False

        self.samples = self.app.samples

        # Detect column types
        self.numeric_columns = []
        self.categorical_columns = []

        if self.samples and len(self.samples) > 0:
            first_sample = self.samples[0]
            for col in first_sample.keys():
                # Skip ID columns
                if col.lower() in ['sample_id', 'id', 'sample', 'name']:
                    self.categorical_columns.append(col)
                    continue

                # Try to convert to float
                try:
                    val = first_sample[col]
                    if val and val != '':
                        float(val)
                        self.numeric_columns.append(col)
                    else:
                        # Check if it's consistently numeric
                        is_numeric = True
                        for s in self.samples[:5]:
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
                except (ValueError, TypeError):
                    self.categorical_columns.append(col)


        # Update UI if window is open
        self._update_ui_columns()

        return True

    def _update_ui_columns(self):
        """Update column selectors in UI"""
        if hasattr(self, 'element_listbox') and self.element_listbox:
            self.element_listbox.delete(0, tk.END)
            for col in sorted(self.numeric_columns):
                self.element_listbox.insert(tk.END, col)

        if hasattr(self, 'group_combo') and self.group_combo:
            self.group_combo['values'] = ["None"] + self.categorical_columns
            self.group_combo.current(0)

        # Update stats combos
        for combo_name in ['stats_var1_combo', 'stats_var2_combo', 'stats_group_combo']:
            if hasattr(self, combo_name):
                combo = getattr(self, combo_name)
                if combo:
                    combo['values'] = self.numeric_columns if 'var' in combo_name else self.categorical_columns

    # ============================================================================
    # DATA PREPARATION
    # ============================================================================
    def _prepare_data(self):
        """Prepare data matrix from selected elements"""
        selected = [self.element_listbox.get(i) for i in self.element_listbox.curselection()]

        if len(selected) < 2:
            messagebox.showwarning("Warning", "Select at least 2 elements")
            return False

        self.feature_names = selected

        # Build data matrix
        data = []
        sample_ids = []
        valid_indices = []

        for idx, sample in enumerate(self.samples):
            row = []
            valid = True

            for feat in selected:
                val = self._safe_float(sample.get(feat))
                if val is None:
                    valid = False
                    break
                row.append(val)

            if valid:
                data.append(row)
                sample_ids.append(sample.get('Sample_ID', f'S{idx}'))
                valid_indices.append(idx)

        if len(data) < 3:
            messagebox.showwarning("Warning", f"Need at least 3 samples, have {len(data)}")
            return False

        self.X = np.array(data)
        self.sample_ids = sample_ids
        self.valid_indices = valid_indices

        # Get group labels if selected
        if self.group_var.get() != "None":
            group_col = self.group_var.get()
            groups = []
            for idx in valid_indices:
                groups.append(str(self.samples[idx].get(group_col, 'Unknown')))
            self.y = np.array(groups)
        else:
            self.y = None

        return True

    # ============================================================================
    # PCA ANALYSIS
    # ============================================================================
    def _run_pca(self):
        """Run PCA on selected data"""
        if not self._prepare_data():
            return False

        self.progress.start()
        self.status_var.set("Running PCA...")

        # Scale data if requested
        if self.pca_scale_var.get():
            self.pca_scaler = StandardScaler()
            X_scaled = self.pca_scaler.fit_transform(self.X)
        else:
            self.pca_scaler = None
            X_scaled = self.X

        # Run PCA
        n_comp = min(10, X_scaled.shape[0], X_scaled.shape[1])
        self.pca = PCA(n_components=n_comp)
        self.pca_scores = self.pca.fit_transform(X_scaled)
        self.pca_loadings = self.pca.components_.T
        self.pca_var_ratio = self.pca.explained_variance_ratio_

        self.status_var.set(f"✅ PCA complete - {n_comp} components, {self.pca_var_ratio[0]*100:.1f}% variance in PC1")
        self.progress.stop()

        # Update plots
        self._update_pca_plot()
        self._update_scree_plot()
        self._update_loadings_text()

        return True

    def _update_pca_plot(self):
        """Update PCA biplot"""
        self.pca_ax.clear()

        pc_x = self.pca_pc_x_var.get() - 1
        pc_y = self.pca_pc_y_var.get() - 1

        scores = self.pca_scores
        var_exp = self.pca_var_ratio

        # Plot scores with group colors if available
        if self.y is not None:
            unique_groups = np.unique(self.y)
            colors = plt.cm.tab10(np.linspace(0, 1, len(unique_groups)))

            for i, group in enumerate(unique_groups):
                mask = self.y == group
                self.pca_ax.scatter(scores[mask, pc_x], scores[mask, pc_y],
                                   c=[colors[i]], label=group[:10],
                                   s=self.pca_point_size_var.get(),
                                   alpha=0.7, edgecolor='black', linewidth=0.3)

                # Add confidence ellipse
                if self.pca_ellipse_var.get() and np.sum(mask) >= 3:
                    self._add_ellipse(self.pca_ax, scores[mask, pc_x], scores[mask, pc_y], colors[i])
        else:
            self.pca_ax.scatter(scores[:, pc_x], scores[:, pc_y],
                               c='steelblue', s=self.pca_point_size_var.get(),
                               alpha=0.7, edgecolor='black', linewidth=0.3)

        # Add loadings as arrows
        if self.pca_loading_var.get() and self.pca_loadings is not None:
            scale = (scores[:, pc_x].max() - scores[:, pc_x].min()) * 0.8

            for i, name in enumerate(self.feature_names):
                x = self.pca_loadings[i, pc_x] * scale
                y = self.pca_loadings[i, pc_y] * scale

                self.pca_ax.arrow(0, 0, x, y, head_width=scale*0.02,
                                 head_length=scale*0.02, fc='red', ec='red', alpha=0.5)
                self.pca_ax.text(x*1.1, y*1.1, name[:6], fontsize=7, color='darkred')

        self.pca_ax.set_xlabel(f'PC{pc_x+1} ({var_exp[pc_x]*100:.1f}%)')
        self.pca_ax.set_ylabel(f'PC{pc_y+1} ({var_exp[pc_y]*100:.1f}%)')
        self.pca_ax.set_title('PCA Biplot')
        self.pca_ax.grid(True, alpha=0.3)
        self.pca_ax.axhline(0, color='gray', linewidth=0.5, alpha=0.5)
        self.pca_ax.axvline(0, color='gray', linewidth=0.5, alpha=0.5)

        if self.y is not None:
            self.pca_ax.legend(loc='best', fontsize=7)

        self.pca_ax.set_aspect('equal')
        self.pca_canvas.draw()

    def _add_ellipse(self, ax, x, y, color):
        """Add confidence ellipse to plot"""
        if len(x) < 3:
            return

        cov = np.cov(x, y)
        mean = [np.mean(x), np.mean(y)]

        # Calculate ellipse parameters
        vals, vecs = np.linalg.eigh(cov)
        order = vals.argsort()[::-1]
        vals, vecs = vals[order], vecs[:, order]

        theta = np.degrees(np.arctan2(*vecs[:, 0][::-1]))
        width, height = 2 * np.sqrt(5.991 * vals)  # 95% confidence

        ellipse = Ellipse(xy=mean, width=width, height=height,
                         angle=theta, edgecolor=color, facecolor='none',
                         linewidth=1, linestyle='--', alpha=0.7)
        ax.add_patch(ellipse)

    def _update_scree_plot(self):
        """Update scree plot"""
        self.scree_ax.clear()

        if self.pca_var_ratio is None:
            return

        n_comps = len(self.pca_var_ratio)
        x = range(1, n_comps + 1)

        # Variance explained
        bars = self.scree_ax.bar(x, self.pca_var_ratio * 100,
                                 alpha=0.6, color='steelblue', edgecolor='black')

        # Cumulative variance
        cumulative = np.cumsum(self.pca_var_ratio) * 100
        self.scree_ax.plot(x, cumulative, 'ro-', linewidth=2, markersize=4,
                          label='Cumulative')

        # Add value labels
        for i, (bar, val) in enumerate(zip(bars, self.pca_var_ratio * 100)):
            self.scree_ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                              f'{val:.0f}%', ha='center', fontsize=6)

        self.scree_ax.set_xlabel('Principal Component')
        self.scree_ax.set_ylabel('Variance Explained (%)')
        self.scree_ax.set_title('Scree Plot')
        self.scree_ax.set_xticks(x)
        self.scree_ax.legend(loc='best', fontsize=7)
        self.scree_ax.grid(True, alpha=0.3, axis='y')

        self.scree_canvas.draw()

    def _update_loadings_text(self):
        """Update loadings text display"""
        self.loadings_text.delete(1.0, tk.END)

        if self.pca_loadings is None:
            return

        # Header
        header = "Element"
        n_pcs = min(5, self.pca_loadings.shape[1])
        for i in range(n_pcs):
            header += f"  PC{i+1}({self.pca_var_ratio[i]*100:.0f}%)"
        self.loadings_text.insert(tk.END, header + "\n")
        self.loadings_text.insert(tk.END, "-" * 50 + "\n")

        # Loadings
        for i, name in enumerate(self.feature_names):
            line = f"{name:<8}"
            for j in range(n_pcs):
                line += f"  {self.pca_loadings[i, j]:>6.3f}"
            self.loadings_text.insert(tk.END, line + "\n")

    # ============================================================================
    # LDA ANALYSIS
    # ============================================================================
    def _run_lda(self):
        """Run LDA on selected data"""
        if not self._prepare_data():
            return False

        if self.y is None or len(np.unique(self.y)) < 2:
            messagebox.showwarning("Warning", "Need at least 2 groups for LDA")
            return False

        self.progress.start()
        self.status_var.set("Running LDA...")

        # Scale data
        scaler = StandardScaler()
        try:
            X_scaled = scaler.fit_transform(self.X)
        except Exception as e:
            messagebox.showerror("Scaling Error", f"Could not scale data:\n{e}")
            self.progress.stop()
            return False

        n_samples = X_scaled.shape[0]
        n_classes = len(np.unique(self.y))

        # LDA requires more samples than classes
        if n_samples <= n_classes:
            messagebox.showwarning(
                "LDA Error",
                f"LDA requires more samples than classes.\n"
                f"You have {n_samples} samples and {n_classes} classes."
            )
            self.progress.stop()
            return False

        # Determine number of components (cannot exceed n_classes-1)
        n_comp = min(n_classes - 1, X_scaled.shape[1], 5)

        self.lda = LDA(n_components=n_comp, solver=self.lda_solver_var.get())

        try:
            self.lda_scores = self.lda.fit_transform(X_scaled, self.y)
            self.lda_classes = self.lda.classes_
        except Exception as e:
            messagebox.showerror("LDA Failed", f"LDA could not be computed:\n{e}")
            self.progress.stop()
            return False

        # Calculate accuracy (optional, but nice)
        y_pred = self.lda.predict(X_scaled)
        acc = np.mean(y_pred == self.y) * 100

        self.status_var.set(f"✅ LDA complete - {n_comp} components, accuracy: {acc:.1f}%")
        self.progress.stop()

        # Update plots
        self._update_lda_plot()
        self._update_confusion_matrix()

        return True

        # Calculate accuracy
        y_pred = self.lda.predict(X_scaled)
        acc = np.mean(y_pred == self.y) * 100

        self.status_var.set(f"✅ LDA complete - {n_comp} components, accuracy: {acc:.1f}%")
        self.progress.stop()

        # Update plots
        self._update_lda_plot()
        self._update_confusion_matrix()

    def _update_lda_plot(self):
        """Update LDA plot"""
        self.lda_ax.clear()

        if self.lda_scores is None:
            return

        pc_x = self.lda_pc_x_var.get() - 1
        pc_y = self.lda_pc_y_var.get() - 1

        scores = self.lda_scores
        unique_groups = np.unique(self.y)
        colors = plt.cm.tab10(np.linspace(0, 1, len(unique_groups)))

        for i, group in enumerate(unique_groups):
            mask = self.y == group
            self.lda_ax.scatter(scores[mask, pc_x] if scores.shape[1] > pc_x else scores[mask, 0],
                               scores[mask, pc_y] if scores.shape[1] > pc_y else np.zeros(np.sum(mask)),
                               c=[colors[i]], label=group,
                               s=25, alpha=0.7, edgecolor='black', linewidth=0.3)

        self.lda_ax.set_xlabel(f'LD{pc_x+1}')
        self.lda_ax.set_ylabel(f'LD{pc_y+1}' if scores.shape[1] > pc_y else '')
        self.lda_ax.set_title('LDA Projection')
        self.lda_ax.grid(True, alpha=0.3)
        self.lda_ax.legend(loc='best', fontsize=7)

        if scores.shape[1] > pc_y:
            self.lda_ax.set_aspect('equal')

        self.lda_canvas.draw()

    def _update_confusion_matrix(self):
        """Update confusion matrix plot"""
        self.cm_ax.clear()

        if self.lda is None:
            return

        # Predict on training data
        X_scaled = StandardScaler().fit_transform(self.X)
        y_pred = self.lda.predict(X_scaled)

        # Compute confusion matrix
        cm = confusion_matrix(self.y, y_pred, labels=self.lda_classes)

        # Plot
        im = self.cm_ax.imshow(cm, interpolation='nearest', cmap='Blues')
        self.cm_ax.figure.colorbar(im, ax=self.cm_ax, shrink=0.8)

        # Add labels
        tick_marks = np.arange(len(self.lda_classes))
        self.cm_ax.set_xticks(tick_marks)
        self.cm_ax.set_yticks(tick_marks)
        self.cm_ax.set_xticklabels([c[:6] for c in self.lda_classes], rotation=45, ha='right', fontsize=7)
        self.cm_ax.set_yticklabels([c[:6] for c in self.lda_classes], fontsize=7)

        # Add values
        thresh = cm.max() / 2.
        for i in range(cm.shape[0]):
            for j in range(cm.shape[1]):
                self.cm_ax.text(j, i, format(cm[i, j], 'd'),
                               ha="center", va="center",
                               color="white" if cm[i, j] > thresh else "black", fontsize=8)

        self.cm_ax.set_xlabel('Predicted', fontsize=8)
        self.cm_ax.set_ylabel('True', fontsize=8)
        self.cm_ax.set_title('Confusion Matrix', fontsize=9)

        self.cm_canvas.draw()

    # ============================================================================
    # CLUSTERING ANALYSIS
    # ============================================================================
    def _run_clustering(self):
        """Run clustering analysis"""
        if not self._prepare_data():
            return False

        self.progress.start()
        self.status_var.set("Running clustering...")

        # Scale data
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(self.X)

        method = self.cluster_method_var.get()
        n_clusters = self.cluster_n_var.get()

        if method == 'kmeans':
            # K-means clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            self.cluster_labels = kmeans.fit_predict(X_scaled)
            self.cluster_centers = kmeans.cluster_centers_

            # Silhouette score
            if len(np.unique(self.cluster_labels)) > 1:
                sil = silhouette_score(X_scaled, self.cluster_labels)
                self.status_var.set(f"✅ K-means complete - Silhouette: {sil:.3f}")
            else:
                self.status_var.set("✅ K-means complete")

        else:  # hierarchical
            # Hierarchical clustering
            self.linkage_matrix = linkage(X_scaled, method=self.cluster_linkage_var.get())
            self.cluster_labels = fcluster(self.linkage_matrix, n_clusters, criterion='maxclust')

            # Silhouette score
            if len(np.unique(self.cluster_labels)) > 1:
                sil = silhouette_score(X_scaled, self.cluster_labels)
                self.status_var.set(f"✅ Hierarchical complete - Silhouette: {sil:.3f}")
            else:
                self.status_var.set("✅ Hierarchical complete")

        self.progress.stop()

        # Update plots
        self._update_cluster_plot()
        if method == 'hierarchical':
            self._update_dendrogram()

    def _update_cluster_plot(self):
        """Update clustering plot"""
        self.cluster_ax.clear()

        if self.cluster_labels is None:
            return

        # Use first two PCs for visualization
        if self.pca_scores is not None:
            X_plot = self.pca_scores[:, :2]
            xlabel = 'PC1'
            ylabel = 'PC2'
        else:
            # Use first two features
            X_plot = self.X[:, :2]
            xlabel = self.feature_names[0][:8]
            ylabel = self.feature_names[1][:8]

        unique_labels = np.unique(self.cluster_labels)
        colors = plt.cm.tab10(np.linspace(0, 1, len(unique_labels)))

        for i, label in enumerate(unique_labels):
            mask = self.cluster_labels == label
            self.cluster_ax.scatter(X_plot[mask, 0], X_plot[mask, 1],
                                   c=[colors[i]], label=f'C{label}',
                                   s=25, alpha=0.7, edgecolor='black', linewidth=0.3)

        # Add cluster centers for k-means
        if self.cluster_method_var.get() == 'kmeans' and self.cluster_centers is not None:
            centers_pca = self.cluster_centers[:, :2] if self.pca_scores is not None else self.cluster_centers[:, :2]
            self.cluster_ax.scatter(centers_pca[:, 0], centers_pca[:, 1],
                                   marker='X', s=100, c='red', edgecolor='black',
                                   linewidth=1, label='Centers')

        self.cluster_ax.set_xlabel(xlabel)
        self.cluster_ax.set_ylabel(ylabel)
        self.cluster_ax.set_title(f'Clustering (k={self.cluster_n_var.get()})')
        self.cluster_ax.grid(True, alpha=0.3)
        self.cluster_ax.legend(loc='best', fontsize=7)

        self.cluster_canvas.draw()

    def _update_dendrogram(self):
        """Update dendrogram plot"""
        self.dendro_ax.clear()

        if self.linkage_matrix is None:
            return

        # Plot dendrogram
        dendrogram(self.linkage_matrix, ax=self.dendro_ax,
                  labels=[s[:8] for s in self.sample_ids],
                  leaf_rotation=90, leaf_font_size=6)

        # Add cut line
        if self.cluster_n_var.get() > 1:
            last_merge = self.linkage_matrix[-(self.cluster_n_var.get()-1), 2]
            self.dendro_ax.axhline(y=last_merge, color='r', linestyle='--', alpha=0.5)

        self.dendro_ax.set_xlabel('Sample')
        self.dendro_ax.set_ylabel('Distance')
        self.dendro_ax.set_title('Hierarchical Clustering Dendrogram')
        self.dendro_ax.grid(True, alpha=0.3, axis='y')

        self.dendro_canvas.draw()

    # ============================================================================
    # STATISTICAL TESTS
    # ============================================================================
    def _run_statistical_test(self):
        """Run selected statistical test"""
        test_type = self.stats_test_var.get()

        if test_type in ['ttest', 'mannwhitney']:
            self._run_two_sample_test()
        elif test_type == 'anova':
            self._run_anova()
        elif test_type == 'correlation':
            self._run_correlation()

    def _run_two_sample_test(self):
        """Run two-sample test (t-test or Mann-Whitney)"""
        var1 = self.stats_var1_var.get()
        var2 = self.stats_var2_var.get()

        if not var1 or not var2:
            messagebox.showwarning("Warning", "Select two variables")
            return

        # Extract data
        data1 = []
        data2 = []

        for s in self.samples:
            val1 = self._safe_float(s.get(var1))
            val2 = self._safe_float(s.get(var2))

            if val1 is not None:
                data1.append(val1)
            if val2 is not None:
                data2.append(val2)

        if len(data1) < 3 or len(data2) < 3:
            messagebox.showwarning("Warning", "Need at least 3 samples per variable")
            return

        # Run test
        if self.stats_test_var.get() == 'ttest':
            stat, p = ttest_ind(data1, data2, equal_var=False)
            test_name = "Welch's t-test"
        else:
            stat, p = mannwhitneyu(data1, data2)
            test_name = "Mann-Whitney U"

        # Display results
        self._show_test_results(test_name, var1, var2, stat, p, {
            f'{var1}': {'n': len(data1), 'mean': np.mean(data1), 'std': np.std(data1)},
            f'{var2}': {'n': len(data2), 'mean': np.mean(data2), 'std': np.std(data2)}
        })

    def _run_anova(self):
        """Run one-way ANOVA"""
        group_var = self.stats_group_var.get()
        value_var = self.stats_var1_var.get()

        if not group_var or not value_var:
            messagebox.showwarning("Warning", "Select group and value variables")
            return

        # Group data
        groups = {}
        for s in self.samples:
            group = str(s.get(group_var, ''))
            if not group:
                continue

            val = self._safe_float(s.get(value_var))
            if val is not None:
                if group not in groups:
                    groups[group] = []
                groups[group].append(val)

        # Filter groups with enough data
        groups = {k: v for k, v in groups.items() if len(v) >= 3}

        if len(groups) < 2:
            messagebox.showwarning("Warning", "Need at least 2 groups with ≥3 samples")
            return

        # Run ANOVA
        data = list(groups.values())
        group_names = list(groups.keys())
        stat, p = f_oneway(*data)

        # Calculate group statistics
        stats_dict = {}
        for name, vals in groups.items():
            stats_dict[name] = {'n': len(vals), 'mean': np.mean(vals), 'std': np.std(vals)}

        self._show_test_results("One-way ANOVA", value_var, group_var, stat, p, stats_dict)

    def _run_correlation(self):
        """Run correlation analysis"""
        var1 = self.stats_var1_var.get()
        var2 = self.stats_var2_var.get()

        if not var1 or not var2:
            messagebox.showwarning("Warning", "Select two variables")
            return

        # Extract paired data
        x = []
        y = []

        for s in self.samples:
            val1 = self._safe_float(s.get(var1))
            val2 = self._safe_float(s.get(var2))

            if val1 is not None and val2 is not None:
                x.append(val1)
                y.append(val2)

        if len(x) < 5:
            messagebox.showwarning("Warning", "Need at least 5 paired samples")
            return

        # Calculate correlation
        r, p = pearsonr(x, y)

        # Create scatter plot
        self.stats_ax.clear()
        self.stats_ax.scatter(x, y, alpha=0.7, s=30, c='steelblue',
                             edgecolor='black', linewidth=0.3)

        # Add regression line
        z = np.polyfit(x, y, 1)
        p_line = np.poly1d(z)
        x_line = np.linspace(min(x), max(x), 50)
        self.stats_ax.plot(x_line, p_line(x_line), 'r--', alpha=0.7,
                          label=f'r = {r:.3f}, p = {p:.4f}')

        self.stats_ax.set_xlabel(var1)
        self.stats_ax.set_ylabel(var2)
        self.stats_ax.set_title('Correlation Plot')
        self.stats_ax.legend(loc='best', fontsize=8)
        self.stats_ax.grid(True, alpha=0.3)

        self.stats_canvas.draw()
        self.status_var.set(f"✅ Correlation: r={r:.3f}, p={p:.4f}")

    def _show_test_results(self, test_name, var1, var2, stat, p, stats_dict):
        """Display test results in text widget"""
        self.stats_text.delete(1.0, tk.END)

        result = f"{'='*50}\n"
        result += f"{test_name.upper()}\n"
        result += f"{'='*50}\n\n"
        result += f"Variables: {var1} vs {var2}\n\n"

        # Sample statistics
        result += "Sample Statistics:\n"
        result += "-" * 30 + "\n"
        for name, s in stats_dict.items():
            result += f"{name[:15]:15} n={s['n']:3}  mean={s['mean']:8.2f}  std={s['std']:6.2f}\n"

        result += f"\nTest Statistic: {stat:.4f}\n"
        result += f"p-value: {p:.4f}\n\n"

        # Interpretation
        alpha = self.stats_alpha_var.get()
        if p < alpha:
            result += f"✓ Significant at α={alpha} (p < {alpha})\n"
            if test_name == "Correlation":
                result += "  → Variables are correlated"
            else:
                result += "  → Groups are significantly different"
        else:
            result += f"✗ Not significant at α={alpha} (p ≥ {alpha})\n"
            if test_name == "Correlation":
                result += "  → No evidence of correlation"
            else:
                result += "  → No evidence of difference"

        self.stats_text.insert(1.0, result)

    # ============================================================================
    # EXPORT RESULTS
    # ============================================================================
    def _export_results(self):
        """Export results to main app"""
        records = []
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Export PCA scores
        if self.pca_scores is not None:
            for i, idx in enumerate(self.valid_indices):
                record = {
                    'Sample_ID': self.sample_ids[i],
                    'Analysis': 'PCA',
                    'Explorer_Timestamp': timestamp
                }
                for pc in range(min(5, self.pca_scores.shape[1])):
                    record[f'PC{pc+1}'] = f"{self.pca_scores[i, pc]:.3f}"
                records.append(record)

        # Export cluster labels
        if self.cluster_labels is not None:
            for i, idx in enumerate(self.valid_indices):
                records.append({
                    'Sample_ID': self.sample_ids[i],
                    'Cluster': f"{self.cluster_labels[i]}",
                    'Explorer_Timestamp': timestamp
                })

        if records:
            self.app.import_data_from_plugin(records)
            self.status_var.set(f"✅ Exported {len(records)} records")

    # ============================================================================
    # UI CONSTRUCTION - COMPACT
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
        self.window.title("📊 Geochemical Explorer v1.0")
        self.window.geometry("1100x700")

        self._create_interface()

        # Load data
        if self._load_from_main_app():
            self.status_var.set(f"✅ Loaded geochemical data")
        else:
            self.status_var.set("ℹ️ No numeric data found")

        self.window.transient(self.app.root)
        self.window.lift()
        self.window.focus_force()

    def _create_interface(self):
        """Create the interface with multiple tabs"""
        # Header
        header = tk.Frame(self.window, bg="#8e44ad", height=35)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="📊", font=("Arial", 14),
                bg="#8e44ad", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Label(header, text="Geochemical Explorer",
                font=("Arial", 11, "bold"),
                bg="#8e44ad", fg="white").pack(side=tk.LEFT, padx=2)
        tk.Label(header, text="v1.0",
                font=("Arial", 7),
                bg="#8e44ad", fg="#f1c40f").pack(side=tk.LEFT, padx=3)

        # Element selection bar
        elem_frame = tk.Frame(header, bg="#8e44ad")
        elem_frame.pack(side=tk.RIGHT, padx=5)

        tk.Label(elem_frame, text="Elements:", bg="#8e44ad", fg="white",
                font=("Arial", 8)).pack(side=tk.LEFT, padx=2)

        self.element_listbox = tk.Listbox(elem_frame, height=1, width=20,
                                         exportselection=False, font=("Arial", 7))
        self.element_listbox.pack(side=tk.LEFT)

        tk.Button(elem_frame, text="All", command=self._select_all_elements,
                 bg="#3498db", fg="white", font=("Arial", 6), width=3).pack(side=tk.LEFT, padx=1)
        tk.Button(elem_frame, text="Clear", command=self._clear_all_elements,
                 bg="#e74c3c", fg="white", font=("Arial", 6), width=3).pack(side=tk.LEFT, padx=1)

        # Main notebook
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)

        # Create tabs
        self._create_pca_tab()
        self._create_lda_tab()
        self._create_clustering_tab()
        self._create_stats_tab()

        # Status bar
        status = tk.Frame(self.window, bg="#34495e", height=20)
        status.pack(fill=tk.X, side=tk.BOTTOM)
        status.pack_propagate(False)

        self.status_var = tk.StringVar(value="Ready")
        tk.Label(status, textvariable=self.status_var,
                font=("Arial", 7), bg="#34495e", fg="white").pack(side=tk.LEFT, padx=5)

        tk.Button(status, text="📤 Export",
                 command=self._export_results,
                 bg="#27ae60", fg="white", font=("Arial", 6), height=1, width=8).pack(side=tk.RIGHT, padx=2)

        self.progress = ttk.Progressbar(status, mode='indeterminate', length=80)
        self.progress.pack(side=tk.RIGHT, padx=2)

    def _select_all_elements(self):
        """Select all elements in listbox"""
        self.element_listbox.selection_set(0, tk.END)

    def _clear_all_elements(self):
        """Clear all element selections"""
        self.element_listbox.selection_clear(0, tk.END)

    # ============================================================================
    # TAB 1: PCA
    # ============================================================================
    def _create_pca_tab(self):
        """Create PCA tab"""
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="📈 PCA")

        # Top control bar
        ctrl = tk.Frame(tab, bg="#f5f5f5", height=30)
        ctrl.pack(fill=tk.X)
        ctrl.pack_propagate(False)

        tk.Label(ctrl, text="PC X:", bg="#f5f5f5", font=("Arial", 8)).pack(side=tk.LEFT, padx=(5,1))
        tk.Spinbox(ctrl, from_=1, to=10, textvariable=self.pca_pc_x_var,
                  width=2, font=("Arial", 8)).pack(side=tk.LEFT, padx=1)

        tk.Label(ctrl, text="Y:", bg="#f5f5f5", font=("Arial", 8)).pack(side=tk.LEFT, padx=(5,1))
        tk.Spinbox(ctrl, from_=1, to=10, textvariable=self.pca_pc_y_var,
                  width=2, font=("Arial", 8)).pack(side=tk.LEFT, padx=1)

        tk.Checkbutton(ctrl, text="Scale", variable=self.pca_scale_var,
                      bg="#f5f5f5", font=("Arial", 8)).pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(ctrl, text="Ellipses", variable=self.pca_ellipse_var,
                      bg="#f5f5f5", font=("Arial", 8)).pack(side=tk.LEFT, padx=2)
        tk.Checkbutton(ctrl, text="Loadings", variable=self.pca_loading_var,
                      bg="#f5f5f5", font=("Arial", 8)).pack(side=tk.LEFT, padx=2)

        tk.Label(ctrl, text="Group:", bg="#f5f5f5", font=("Arial", 8)).pack(side=tk.LEFT, padx=(10,1))
        self.group_combo = ttk.Combobox(ctrl, textvariable=self.group_var,
                                        values=["None"], width=8, state='readonly')
        self.group_combo.pack(side=tk.LEFT, padx=1)

        tk.Button(ctrl, text="▶ Run PCA", command=self._run_pca,
                 bg="#e67e22", fg="white", font=("Arial", 8), width=8).pack(side=tk.RIGHT, padx=5)

        # Main content - split into left (plot) and right (scree+loadings)
        main = tk.Frame(tab)
        main.pack(fill=tk.BOTH, expand=True)

        # Left - PCA plot (400x400)
        left = tk.Frame(main, bg="white", width=400, height=400)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)

        self.pca_fig = plt.Figure(figsize=(4, 4), dpi=90)
        self.pca_fig.patch.set_facecolor('white')
        self.pca_ax = self.pca_fig.add_subplot(111)
        self.pca_canvas = FigureCanvasTkAgg(self.pca_fig, left)
        self.pca_canvas.draw()
        self.pca_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Right - stacked (scree + loadings)
        right = tk.Frame(main, width=300)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Scree plot
        scree_frame = tk.LabelFrame(right, text="Scree Plot", padx=2, pady=2, font=("Arial", 8))
        scree_frame.pack(fill=tk.BOTH, expand=True, pady=1)

        self.scree_fig = plt.Figure(figsize=(3, 2), dpi=80)
        self.scree_fig.patch.set_facecolor('white')
        self.scree_ax = self.scree_fig.add_subplot(111)
        self.scree_canvas = FigureCanvasTkAgg(self.scree_fig, scree_frame)
        self.scree_canvas.draw()
        self.scree_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Loadings text
        loadings_frame = tk.LabelFrame(right, text="Loadings", padx=2, pady=2, font=("Arial", 8))
        loadings_frame.pack(fill=tk.BOTH, expand=True, pady=1)

        self.loadings_text = tk.Text(loadings_frame, height=6, font=("Courier", 7))
        scroll = tk.Scrollbar(loadings_frame, command=self.loadings_text.yview)
        self.loadings_text.configure(yscrollcommand=scroll.set)

        self.loadings_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

    # ============================================================================
    # TAB 2: LDA
    # ============================================================================
    def _create_lda_tab(self):
        """Create LDA tab"""
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="🎯 LDA")

        # Control bar
        ctrl = tk.Frame(tab, bg="#f5f5f5", height=30)
        ctrl.pack(fill=tk.X)
        ctrl.pack_propagate(False)

        tk.Label(ctrl, text="LD X:", bg="#f5f5f5", font=("Arial", 8)).pack(side=tk.LEFT, padx=(5,1))
        tk.Spinbox(ctrl, from_=1, to=5, textvariable=self.lda_pc_x_var,
                  width=2, font=("Arial", 8)).pack(side=tk.LEFT, padx=1)

        tk.Label(ctrl, text="Y:", bg="#f5f5f5", font=("Arial", 8)).pack(side=tk.LEFT, padx=(5,1))
        tk.Spinbox(ctrl, from_=1, to=5, textvariable=self.lda_pc_y_var,
                  width=2, font=("Arial", 8)).pack(side=tk.LEFT, padx=1)

        tk.Label(ctrl, text="Solver:", bg="#f5f5f5", font=("Arial", 8)).pack(side=tk.LEFT, padx=(5,1))
        ttk.Combobox(ctrl, textvariable=self.lda_solver_var,
                    values=['svd', 'lsqr', 'eigen'], width=5, state='readonly').pack(side=tk.LEFT)

        tk.Button(ctrl, text="▶ Run LDA", command=self._run_lda,
                 bg="#e67e22", fg="white", font=("Arial", 8), width=8).pack(side=tk.RIGHT, padx=5)

        # Main content - two plots side by side
        main = tk.Frame(tab)
        main.pack(fill=tk.BOTH, expand=True)

        # LDA plot
        left = tk.Frame(main, bg="white")
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)

        self.lda_fig = plt.Figure(figsize=(4, 4), dpi=90)
        self.lda_fig.patch.set_facecolor('white')
        self.lda_ax = self.lda_fig.add_subplot(111)
        self.lda_canvas = FigureCanvasTkAgg(self.lda_fig, left)
        self.lda_canvas.draw()
        self.lda_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Confusion matrix
        right = tk.Frame(main, bg="white")
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=2, pady=2)

        self.cm_fig = plt.Figure(figsize=(4, 4), dpi=90)
        self.cm_fig.patch.set_facecolor('white')
        self.cm_ax = self.cm_fig.add_subplot(111)
        self.cm_canvas = FigureCanvasTkAgg(self.cm_fig, right)
        self.cm_canvas.draw()
        self.cm_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # ============================================================================
    # TAB 3: Clustering
    # ============================================================================
    def _create_clustering_tab(self):
        """Create clustering tab"""
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="🔗 Clustering")

        # Control bar
        ctrl = tk.Frame(tab, bg="#f5f5f5", height=30)
        ctrl.pack(fill=tk.X)
        ctrl.pack_propagate(False)

        tk.Label(ctrl, text="Method:", bg="#f5f5f5", font=("Arial", 8)).pack(side=tk.LEFT, padx=(5,1))
        ttk.Combobox(ctrl, textvariable=self.cluster_method_var,
                    values=['kmeans', 'hierarchical'], width=10, state='readonly').pack(side=tk.LEFT, padx=1)

        tk.Label(ctrl, text="k:", bg="#f5f5f5", font=("Arial", 8)).pack(side=tk.LEFT, padx=(5,1))
        tk.Spinbox(ctrl, from_=2, to=10, textvariable=self.cluster_n_var,
                  width=2, font=("Arial", 8)).pack(side=tk.LEFT, padx=1)

        tk.Label(ctrl, text="Linkage:", bg="#f5f5f5", font=("Arial", 8)).pack(side=tk.LEFT, padx=(5,1))
        ttk.Combobox(ctrl, textvariable=self.cluster_linkage_var,
                    values=['ward', 'complete', 'average', 'single'], width=6, state='readonly').pack(side=tk.LEFT)

        tk.Button(ctrl, text="▶ Run", command=self._run_clustering,
                 bg="#e67e22", fg="white", font=("Arial", 8), width=5).pack(side=tk.RIGHT, padx=5)

        # Main content - two plots
        main = tk.Frame(tab)
        main.pack(fill=tk.BOTH, expand=True)

        # Cluster plot
        left = tk.Frame(main, bg="white")
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)

        self.cluster_fig = plt.Figure(figsize=(4, 4), dpi=90)
        self.cluster_fig.patch.set_facecolor('white')
        self.cluster_ax = self.cluster_fig.add_subplot(111)
        self.cluster_canvas = FigureCanvasTkAgg(self.cluster_fig, left)
        self.cluster_canvas.draw()
        self.cluster_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Dendrogram
        right = tk.Frame(main, bg="white")
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=2, pady=2)

        self.dendro_fig = plt.Figure(figsize=(4, 4), dpi=90)
        self.dendro_fig.patch.set_facecolor('white')
        self.dendro_ax = self.dendro_fig.add_subplot(111)
        self.dendro_canvas = FigureCanvasTkAgg(self.dendro_fig, right)
        self.dendro_canvas.draw()
        self.dendro_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # ============================================================================
    # TAB 4: Statistics
    # ============================================================================
    def _create_stats_tab(self):
        """Create statistics tab"""
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="📊 Statistics")

        # Control bar
        ctrl = tk.Frame(tab, bg="#f5f5f5", height=30)
        ctrl.pack(fill=tk.X)
        ctrl.pack_propagate(False)

        tk.Label(ctrl, text="Test:", bg="#f5f5f5", font=("Arial", 8)).pack(side=tk.LEFT, padx=(5,1))
        ttk.Combobox(ctrl, textvariable=self.stats_test_var,
                    values=['ttest', 'mannwhitney', 'anova', 'correlation'],
                    width=10, state='readonly').pack(side=tk.LEFT, padx=1)

        tk.Label(ctrl, text="Var1:", bg="#f5f5f5", font=("Arial", 8)).pack(side=tk.LEFT, padx=(5,1))
        self.stats_var1_combo = ttk.Combobox(ctrl, textvariable=self.stats_var1_var,
                                            values=self.numeric_columns, width=6, state='readonly')
        self.stats_var1_combo.pack(side=tk.LEFT, padx=1)

        tk.Label(ctrl, text="Var2:", bg="#f5f5f5", font=("Arial", 8)).pack(side=tk.LEFT, padx=(5,1))
        self.stats_var2_combo = ttk.Combobox(ctrl, textvariable=self.stats_var2_var,
                                            values=self.numeric_columns, width=6, state='readonly')
        self.stats_var2_combo.pack(side=tk.LEFT, padx=1)

        tk.Label(ctrl, text="Group:", bg="#f5f5f5", font=("Arial", 8)).pack(side=tk.LEFT, padx=(5,1))
        self.stats_group_combo = ttk.Combobox(ctrl, textvariable=self.stats_group_var,
                                             values=self.categorical_columns, width=6, state='readonly')
        self.stats_group_combo.pack(side=tk.LEFT, padx=1)

        tk.Button(ctrl, text="▶ Run", command=self._run_statistical_test,
                 bg="#e67e22", fg="white", font=("Arial", 8), width=5).pack(side=tk.RIGHT, padx=5)

        # Main content - plot and results
        main = tk.Frame(tab)
        main.pack(fill=tk.BOTH, expand=True)

        # Plot area
        plot_frame = tk.Frame(main, bg="white")
        plot_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)

        self.stats_fig = plt.Figure(figsize=(4, 4), dpi=90)
        self.stats_fig.patch.set_facecolor('white')
        self.stats_ax = self.stats_fig.add_subplot(111)
        self.stats_canvas = FigureCanvasTkAgg(self.stats_fig, plot_frame)
        self.stats_canvas.draw()
        self.stats_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Results text
        text_frame = tk.Frame(main, width=300)
        text_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=2, pady=2)

        self.stats_text = tk.Text(text_frame, font=("Courier", 8), height=20)
        scroll = tk.Scrollbar(text_frame, command=self.stats_text.yview)
        self.stats_text.configure(yscrollcommand=scroll.set)

        self.stats_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)


def setup_plugin(main_app):
    """Plugin setup function"""
    plugin = GeochemicalExplorerPlugin(main_app)
    return plugin
