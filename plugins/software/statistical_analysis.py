"""
Statistical Analysis Plugin for Basalt Provenance Toolkit
Provides PCA, clustering, and multivariate analysis for provenance studies

Author: Sefy Levy
License: CC BY-NC-SA 4.0
"""

PLUGIN_INFO = {
      "category": "software",
    "id": "statistical_analysis",
    "name": "Statistical Analysis",
    "description": "PCA, clustering, hierarchical analysis for provenance grouping",
    "icon": "📊",
    "version": "1.0",
    "requires": ["scikit-learn", "scipy", "numpy", "matplotlib"],
    "author": "Sefy Levy"
}

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np

# Conditional imports - graceful degradation if packages missing
try:
    from sklearn.decomposition import PCA
    from sklearn.cluster import KMeans, AgglomerativeClustering
    from sklearn.preprocessing import StandardScaler
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    from scipy.cluster.hierarchy import dendrogram, linkage
    HAS_REQUIREMENTS = True
except ImportError as e:
    HAS_REQUIREMENTS = False
    IMPORT_ERROR = str(e)


class StatisticalAnalysisPlugin:
    """Plugin for advanced statistical analysis of geochemical data"""
    
    def __init__(self, main_app):
        """
        Initialize plugin with reference to main app
        
        Args:
            main_app: Instance of BasaltTriageApp
        """
        self.app = main_app
        self.window = None
        
        # Analysis results storage
        self.pca_model = None
        self.scaler = None
        self.X_scaled = None
        self.feature_names = None
        self.sample_ids = None
    
    def open_window(self):
        """Open the statistical analysis interface"""
        if not HAS_REQUIREMENTS:
            messagebox.showerror(
                "Missing Dependencies",
                f"Statistical Analysis requires additional packages:\n\n"
                f"Error: {IMPORT_ERROR}\n\n"
                f"Install with:\n"
                f"pip install scikit-learn scipy matplotlib numpy"
            )
            return
        
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return
        
        self.window = tk.Toplevel(self.app.root)
        self.window.title("Statistical Analysis - Advanced Geochemistry")
        self.window.geometry("800x580")
        
        # Create notebook with tabs
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Tab 1: PCA
        pca_frame = tk.Frame(notebook)
        notebook.add(pca_frame, text="📊 Principal Component Analysis")
        self._create_pca_tab(pca_frame)
        
        # Tab 2: Clustering
        cluster_frame = tk.Frame(notebook)
        notebook.add(cluster_frame, text="🔗 Cluster Analysis")
        self._create_clustering_tab(cluster_frame)
        
        # Tab 3: Discriminant Function Analysis (NEW!)
        dfa_frame = tk.Frame(notebook)
        notebook.add(dfa_frame, text="🎯 Discriminant Function Analysis")
        self._create_dfa_tab(dfa_frame)
        
        # Tab 4: Help
        help_frame = tk.Frame(notebook)
        notebook.add(help_frame, text="❓ Help")
        self._create_help_tab(help_frame)
    
    def _create_pca_tab(self, parent):
        """Create PCA analysis interface"""
        # Controls frame at top
        controls = tk.Frame(parent, relief=tk.RAISED, borderwidth=2)
        controls.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        tk.Label(controls, 
                text="Principal Component Analysis - Dimensionality Reduction for Provenance Grouping",
                font=("Arial", 12, "bold")).pack(anchor=tk.W, padx=10, pady=5)
        
        tk.Label(controls, 
                text="PCA reduces your multi-element geochemistry to 2-3 principal components that capture the most variation.",
                font=("Arial", 9), fg="gray").pack(anchor=tk.W, padx=10)
        
        # Element selection
        elem_frame = tk.Frame(controls)
        elem_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(elem_frame, text="Elements to include:", 
                font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=5)
        
        self.pca_elements = {}
        elements = ['Zr', 'Nb', 'Ba', 'Rb', 'Cr', 'Ni']
        for elem in elements:
            var = tk.BooleanVar(value=True)
            self.pca_elements[elem] = var
            tk.Checkbutton(elem_frame, text=elem, variable=var,
                          font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        
        # Options
        options_frame = tk.Frame(controls)
        options_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(options_frame, text="Options:", 
                font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=5)
        
        self.pca_standardize = tk.BooleanVar(value=True)
        tk.Checkbutton(options_frame, text="Standardize data (recommended)", 
                      variable=self.pca_standardize,
                      font=("Arial", 9)).pack(side=tk.LEFT, padx=10)
        
        self.pca_show_labels = tk.BooleanVar(value=True)
        tk.Checkbutton(options_frame, text="Show sample labels", 
                      variable=self.pca_show_labels,
                      font=("Arial", 9)).pack(side=tk.LEFT, padx=10)
        
        # Run button
        btn_frame = tk.Frame(controls)
        btn_frame.pack(pady=5)
        
        tk.Button(btn_frame, text="▶ Run PCA Analysis",
                 command=self._run_pca,
                 bg="#2196F3", fg="white", 
                 font=("Arial", 10, "bold"),
                 width=20, height=2,
                 cursor="hand2").pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="💾 Export Plot",
                 command=lambda: self._export_plot(self.pca_plot_frame),
                 font=("Arial", 10),
                 width=15, height=2,
                 cursor="hand2").pack(side=tk.LEFT, padx=5)
        
        # Plot frame
        self.pca_plot_frame = tk.Frame(parent, relief=tk.SUNKEN, borderwidth=2)
        self.pca_plot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Initial placeholder
        tk.Label(self.pca_plot_frame, 
                text="👆 Click 'Run PCA Analysis' to generate plots",
                font=("Arial", 12), fg="gray").pack(expand=True)
    
    def _run_pca(self):
        """Run PCA on current dataset"""
        # Get selected elements
        selected_elements = [elem for elem, var in self.pca_elements.items() if var.get()]
        
        if len(selected_elements) < 2:
            messagebox.showwarning("Insufficient Elements", "Please select at least 2 elements for PCA", parent=self.window)
            return
        
        # Get data from main app
        samples = self.app.samples
        
        if len(samples) < 3:
            messagebox.showwarning("Insufficient Data", "Need at least 3 samples for PCA", parent=self.window)
            return
        
        # Extract geochemical data
        data = []
        sample_ids = []
        classifications = []
        
        for sample in samples:
            try:
                row = []
                for elem in selected_elements:
                    val = sample.get(f'{elem}_ppm', '')
                    if val == '' or val is None:
                        val = 0
                    row.append(float(val))
                
                # Skip if all zeros
                if any(row):
                    data.append(row)
                    sample_ids.append(sample.get('Sample_ID', 'Unknown'))
                    classifications.append(sample.get('Final_Classification', 'Unclassified'))
            except (ValueError, TypeError):
                continue
        
        if len(data) < 3:
            messagebox.showwarning("Insufficient Data", "Need at least 3 samples with valid geochemical data", parent=self.window)
            return
        
        # Convert to numpy array
        X = np.array(data)
        self.feature_names = selected_elements
        self.sample_ids = sample_ids
        
        # Standardize if requested
        if self.pca_standardize.get():
            self.scaler = StandardScaler()
            self.X_scaled = self.scaler.fit_transform(X)
        else:
            self.X_scaled = X
            self.scaler = None
        
        # Run PCA
        try:
            self.pca_model = PCA()
            X_pca = self.pca_model.fit_transform(self.X_scaled)
            
            # Plot results
            self._plot_pca_results(X_pca, classifications)
            
        except Exception as e:
            messagebox.showerror("PCA Error", f"Error running PCA:\n{e}", parent=self.window)
    
    def _plot_pca_results(self, X_pca, classifications):
        """Create comprehensive PCA plots"""
        # Clear previous plot
        for widget in self.pca_plot_frame.winfo_children():
            widget.destroy()
        
        # Create figure with subplots
        fig = plt.figure(figsize=(14, 10))
        gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
        
        # Define color map for classifications
        unique_classes = list(set(classifications))
        colors = plt.cm.tab10(np.linspace(0, 1, len(unique_classes)))
        color_map = dict(zip(unique_classes, colors))
        point_colors = [color_map[c] for c in classifications]
        
        # Plot 1: PC1 vs PC2 scatter
        ax1 = fig.add_subplot(gs[0, 0])
        scatter = ax1.scatter(X_pca[:, 0], X_pca[:, 1], 
                             c=point_colors, alpha=0.7, s=100, edgecolors='black')
        
        var_explained = self.pca_model.explained_variance_ratio_
        ax1.set_xlabel(f'PC1 ({var_explained[0]*100:.1f}% variance)', fontsize=10)
        ax1.set_ylabel(f'PC2 ({var_explained[1]*100:.1f}% variance)', fontsize=10)
        ax1.set_title('PCA Score Plot (PC1 vs PC2)', fontsize=12, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        
        # Add sample labels if requested
        if self.pca_show_labels.get():
            for i, label in enumerate(self.sample_ids):
                ax1.annotate(label, (X_pca[i, 0], X_pca[i, 1]),
                           fontsize=7, alpha=0.7)
        
        # Add legend for classifications
        handles = [plt.Line2D([0], [0], marker='o', color='w', 
                             markerfacecolor=color_map[cls], markersize=8, label=cls)
                  for cls in unique_classes]
        ax1.legend(handles=handles, loc='best', fontsize=8, title='Classification')
        
        # Plot 2: Scree plot
        ax2 = fig.add_subplot(gs[0, 1])
        n_components = len(var_explained)
        ax2.bar(range(1, n_components + 1), var_explained * 100, 
               color='steelblue', edgecolor='black')
        ax2.plot(range(1, n_components + 1), var_explained * 100, 
                'ro-', linewidth=2, markersize=8)
        ax2.set_xlabel('Principal Component', fontsize=10)
        ax2.set_ylabel('Variance Explained (%)', fontsize=10)
        ax2.set_title('Scree Plot', fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='y')
        ax2.set_xticks(range(1, n_components + 1))
        
        # Add cumulative variance line
        cumulative_var = np.cumsum(var_explained * 100)
        ax2_twin = ax2.twinx()
        ax2_twin.plot(range(1, n_components + 1), cumulative_var, 
                     'go-', linewidth=2, markersize=8, label='Cumulative')
        ax2_twin.set_ylabel('Cumulative Variance (%)', fontsize=10)
        ax2_twin.set_ylim([0, 105])
        ax2_twin.legend(loc='lower right', fontsize=8)
        
        # Plot 3: Loading plot (biplot-style)
        ax3 = fig.add_subplot(gs[1, 0])
        loadings = self.pca_model.components_.T
        
        for i, feature in enumerate(self.feature_names):
            ax3.arrow(0, 0, loadings[i, 0], loadings[i, 1],
                     head_width=0.05, head_length=0.05, fc='red', ec='red', alpha=0.7)
            ax3.text(loadings[i, 0] * 1.15, loadings[i, 1] * 1.15, feature,
                    fontsize=10, fontweight='bold', ha='center')
        
        ax3.set_xlabel(f'PC1 Loadings ({var_explained[0]*100:.1f}%)', fontsize=10)
        ax3.set_ylabel(f'PC2 Loadings ({var_explained[1]*100:.1f}%)', fontsize=10)
        ax3.set_title('Variable Loadings (Element Contributions)', fontsize=12, fontweight='bold')
        ax3.grid(True, alpha=0.3)
        ax3.axhline(y=0, color='k', linewidth=0.5)
        ax3.axvline(x=0, color='k', linewidth=0.5)
        
        # Set equal aspect ratio
        max_loading = np.abs(loadings[:, :2]).max()
        ax3.set_xlim([-max_loading*1.3, max_loading*1.3])
        ax3.set_ylim([-max_loading*1.3, max_loading*1.3])
        
        # Plot 4: Explained variance table
        ax4 = fig.add_subplot(gs[1, 1])
        ax4.axis('off')
        
        # Create table data
        table_data = []
        table_data.append(['PC', 'Variance %', 'Cumulative %'])
        for i in range(min(6, n_components)):
            table_data.append([
                f'PC{i+1}',
                f'{var_explained[i]*100:.2f}',
                f'{cumulative_var[i]:.2f}'
            ])
        
        table = ax4.table(cellText=table_data, cellLoc='center',
                         loc='center', bbox=[0, 0, 1, 1])
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 2)
        
        # Style header row
        for i in range(3):
            table[(0, i)].set_facecolor('#2196F3')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        ax4.set_title('Variance Explained Summary', fontsize=12, fontweight='bold', pad=20)
        
        # Overall title
        fig.suptitle('Principal Component Analysis Results', 
                    fontsize=14, fontweight='bold', y=0.98)
        
        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, self.pca_plot_frame)
        canvas.draw()
        
        # Add toolbar
        toolbar = NavigationToolbar2Tk(canvas, self.pca_plot_frame)
        toolbar.update()
        
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def _create_clustering_tab(self, parent):
        """Create clustering analysis interface"""
        # Controls
        controls = tk.Frame(parent, relief=tk.RAISED, borderwidth=2)
        controls.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        tk.Label(controls, 
                text="Hierarchical Cluster Analysis - Automatic Source Grouping",
                font=("Arial", 12, "bold")).pack(anchor=tk.W, padx=10, pady=5)
        
        tk.Label(controls, 
                text="Cluster analysis groups samples by geochemical similarity without prior classification.",
                font=("Arial", 9), fg="gray").pack(anchor=tk.W, padx=10)
        
        # Number of clusters
        param_frame = tk.Frame(controls)
        param_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(param_frame, text="Number of clusters:", 
                font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=5)
        
        self.n_clusters = tk.IntVar(value=3)
        tk.Spinbox(param_frame, from_=2, to=10, textvariable=self.n_clusters,
                  width=10, font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        
        tk.Label(param_frame, text="Method:", 
                font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(20, 5))
        
        self.cluster_method = tk.StringVar(value="ward")
        methods = ["ward", "complete", "average", "single"]
        ttk.Combobox(param_frame, textvariable=self.cluster_method, 
                    values=methods, width=10, state="readonly",
                    font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        
        # Run buttons
        btn_frame = tk.Frame(controls)
        btn_frame.pack(pady=5)
        
        tk.Button(btn_frame, text="▶ Run Hierarchical Clustering",
                 command=self._run_hierarchical_clustering,
                 bg="#4CAF50", fg="white", 
                 font=("Arial", 10, "bold"),
                 width=25, height=2,
                 cursor="hand2").pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="▶ Run K-Means",
                 command=self._run_kmeans,
                 bg="#FF9800", fg="white", 
                 font=("Arial", 10, "bold"),
                 width=15, height=2,
                 cursor="hand2").pack(side=tk.LEFT, padx=5)
        
        # Plot frame
        self.cluster_plot_frame = tk.Frame(parent, relief=tk.SUNKEN, borderwidth=2)
        self.cluster_plot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Placeholder
        tk.Label(self.cluster_plot_frame, 
                text="👆 Click 'Run Hierarchical Clustering' to generate dendrogram",
                font=("Arial", 12), fg="gray").pack(expand=True)
    
    def _run_hierarchical_clustering(self):
        """Run hierarchical clustering analysis"""
        if self.X_scaled is None:
            messagebox.showwarning("Run PCA First", "Please run PCA analysis first to prepare the data", parent=self.window)
            return
        
        try:
            # Perform linkage
            Z = linkage(self.X_scaled, method=self.cluster_method.get())
            
            # Clear plot
            for widget in self.cluster_plot_frame.winfo_children():
                widget.destroy()
            
            # Create dendrogram
            fig, ax = plt.subplots(figsize=(12, 6))
            
            dendrogram(Z, labels=self.sample_ids, ax=ax,
                      leaf_font_size=8, leaf_rotation=90)
            
            ax.set_title(f'Hierarchical Clustering Dendrogram ({self.cluster_method.get()} linkage)',
                        fontsize=14, fontweight='bold')
            ax.set_xlabel('Sample ID', fontsize=11)
            ax.set_ylabel('Distance', fontsize=11)
            ax.grid(True, alpha=0.3, axis='y')
            
            fig.tight_layout()
            
            # Embed
            canvas = FigureCanvasTkAgg(fig, self.cluster_plot_frame)
            canvas.draw()
            toolbar = NavigationToolbar2Tk(canvas, self.cluster_plot_frame)
            toolbar.update()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
        except Exception as e:
            messagebox.showerror("Clustering Error", f"Error running clustering:\n{e}", parent=self.window)
    
    def _run_kmeans(self):
        """Run K-means clustering"""
        if self.X_scaled is None:
            messagebox.showwarning("Run PCA First", "Please run PCA analysis first to prepare the data", parent=self.window)
            return
        
        try:
            n_clusters = self.n_clusters.get()
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(self.X_scaled)
            
            # Run PCA for visualization if not already done
            if self.pca_model is None:
                pca = PCA(n_components=2)
                X_pca = pca.fit_transform(self.X_scaled)
            else:
                X_pca = self.pca_model.transform(self.X_scaled)[:, :2]
            
            # Clear plot
            for widget in self.cluster_plot_frame.winfo_children():
                widget.destroy()
            
            # Plot clusters
            fig, ax = plt.subplots(figsize=(10, 7))
            
            scatter = ax.scatter(X_pca[:, 0], X_pca[:, 1], 
                               c=cluster_labels, cmap='tab10', 
                               s=100, alpha=0.7, edgecolors='black')
            
            # Plot cluster centers
            if self.pca_model:
                centers_pca = self.pca_model.transform(kmeans.cluster_centers_)[:, :2]
            else:
                centers_pca = pca.transform(kmeans.cluster_centers_)
            
            ax.scatter(centers_pca[:, 0], centers_pca[:, 1],
                      marker='X', s=300, c='red', edgecolors='black',
                      linewidths=2, label='Cluster Centers')
            
            # Labels
            for i, label in enumerate(self.sample_ids):
                ax.annotate(label, (X_pca[i, 0], X_pca[i, 1]),
                           fontsize=7, alpha=0.7)
            
            ax.set_title(f'K-Means Clustering (k={n_clusters})',
                        fontsize=14, fontweight='bold')
            ax.set_xlabel('PC1', fontsize=11)
            ax.set_ylabel('PC2', fontsize=11)
            ax.grid(True, alpha=0.3)
            ax.legend()
            
            fig.tight_layout()
            
            # Embed
            canvas = FigureCanvasTkAgg(fig, self.cluster_plot_frame)
            canvas.draw()
            toolbar = NavigationToolbar2Tk(canvas, self.cluster_plot_frame)
            toolbar.update()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
        except Exception as e:
            messagebox.showerror("K-Means Error", f"Error running K-means:\n{e}", parent=self.window)
    
    def _create_dfa_tab(self, parent):
        """Create Discriminant Function Analysis (DFA) tab - VALIDATES CLASSIFICATIONS STATISTICALLY"""
        # Controls
        controls = tk.Frame(parent, relief=tk.RAISED, borderwidth=2)
        controls.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        tk.Label(controls, 
                text="Discriminant Function Analysis - Statistical Validation of Classifications",
                font=("Arial", 12, "bold")).pack(anchor=tk.W, padx=10, pady=5)
        
        tk.Label(controls, 
                text="DFA tests if your provenance groups are statistically distinct using Linear Discriminant Analysis.",
                font=("Arial", 9), fg="blue").pack(anchor=tk.W, padx=10)
        
        # Element selection
        elem_frame = tk.Frame(controls)
        elem_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(elem_frame, text="Discriminating elements:", 
                font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=5)
        
        self.dfa_elements = {}
        elements = ['Zr', 'Nb', 'Ba', 'Rb', 'Cr', 'Ni']
        for elem in elements:
            var = tk.BooleanVar(value=True)
            ttk.Checkbutton(elem_frame, text=elem, variable=var).pack(side=tk.LEFT, padx=3)
            self.dfa_elements[elem] = var
        
        # Run button
        tk.Button(controls, text="▶ Run Discriminant Analysis",
                 command=self._run_dfa,
                 bg="#9C27B0", fg="white", 
                 font=("Arial", 10, "bold"),
                 width=25, height=2).pack(pady=5)
        
        # Results frame
        results_frame = tk.LabelFrame(parent, text="Analysis Results", font=("Arial", 10, "bold"))
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.dfa_results_text = tk.Text(results_frame, height=10, font=("Courier", 9))
        self.dfa_results_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Plot frame
        self.dfa_plot_frame = tk.Frame(parent)
        self.dfa_plot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        tk.Label(self.dfa_plot_frame, text="Click 'Run Discriminant Analysis' to see results",
                font=("Arial", 10), fg="gray").pack(expand=True)
    
    def _run_dfa(self):
        """Run Linear Discriminant Analysis to validate classifications"""
        try:
            from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
            from sklearn.model_selection import cross_val_score
        except ImportError:
            messagebox.showerror(
                "Missing Dependency",
                "DFA requires scikit-learn.\n\n"
                "Install with: pip install scikit-learn"
            )
            return
        
        # Get selected elements
        selected_elements = [elem for elem, var in self.dfa_elements.items() if var.get()]
        
        if len(selected_elements) < 2:
            messagebox.showwarning("Insufficient Elements", "Select at least 2 elements for DFA.", parent=self.window)
            return
        
        # Prepare data - only samples with classifications
        X = []
        y = []
        sample_ids = []
        
        for sample in self.app.samples:
            classification = sample.get('Final_Classification', 
                                       sample.get('Auto_Classification', ''))
            
            if not classification or classification == 'REVIEW REQUIRED':
                continue
            
            # Get element values
            values = []
            valid = True
            for elem in selected_elements:
                val = self._safe_float(sample.get(f'{elem}_ppm', ''))
                if val is None:
                    valid = False
                    break
                values.append(val)
            
            if valid:
                X.append(values)
                y.append(classification)
                sample_ids.append(sample.get('Sample_ID', 'Unknown'))
        
        if len(X) < 10:
            messagebox.showwarning("Insufficient Data", "Need at least 10 classified samples for DFA.", parent=self.window)
            return
        
        # Check if we have multiple classes
        unique_classes = list(set(y))
        if len(unique_classes) < 2:
            messagebox.showwarning("Single Class", "Need at least 2 different provenance groups for DFA.", parent=self.window)
            return
        
        X = np.array(X)
        
        # Standardize
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Run LDA
        lda = LinearDiscriminantAnalysis()
        
        try:
            X_lda = lda.fit_transform(X_scaled, y)
            
            # Cross-validation to test classification accuracy
            cv_scores = cross_val_score(lda, X_scaled, y, cv=min(5, len(X)//2))
            mean_accuracy = cv_scores.mean() * 100
            std_accuracy = cv_scores.std() * 100
            
            # Display results
            self.dfa_results_text.delete('1.0', tk.END)
            results = f"""
DISCRIMINANT FUNCTION ANALYSIS RESULTS
========================================

Dataset:
  Samples:              {len(X)}
  Provenance Groups:    {len(unique_classes)}
  Discriminating Elements: {', '.join(selected_elements)}

Cross-Validation Accuracy:
  Mean:                 {mean_accuracy:.1f}%
  Std Dev:              {std_accuracy:.1f}%
  
Interpretation:
  {self._interpret_dfa_accuracy(mean_accuracy)}

Provenance Groups:
  {', '.join(unique_classes)}

Explained Variance by LD Components:
"""
            if hasattr(lda, 'explained_variance_ratio_'):
                for i, var in enumerate(lda.explained_variance_ratio_):
                    results += f"  LD{i+1}: {var*100:.1f}%\n"
            
            self.dfa_results_text.insert('1.0', results)
            
            # Plot LDA space
            self._plot_lda(X_lda, y, unique_classes, sample_ids)
            
        except Exception as e:
            messagebox.showerror("DFA Error", f"Error running DFA:\n{str(e)}", parent=self.window)
    
    def _interpret_dfa_accuracy(self, accuracy):
        """Interpret DFA classification accuracy"""
        if accuracy >= 90:
            return "EXCELLENT - Your provenance groups are highly distinct!"
        elif accuracy >= 75:
            return "GOOD - Groups are well-separated statistically."
        elif accuracy >= 60:
            return "MODERATE - Some overlap between groups exists."
        else:
            return "WEAK - Groups may not be chemically distinct."
    
    def _plot_lda(self, X_lda, y, classes, sample_ids):
        """Plot LDA discriminant space"""
        # Clear previous plot
        for widget in self.dfa_plot_frame.winfo_children():
            widget.destroy()
        
        fig, ax = plt.subplots(figsize=(10, 7))
        
        # Color map
        color_map = {
            "EGYPTIAN (HADDADIN FLOW)": "blue",
            "EGYPTIAN (ALKALINE / EXOTIC)": "red",
            "SINAI / TRANSITIONAL": "gold",
            "SINAI OPHIOLITIC": "orange",
            "LOCAL LEVANTINE": "green",
            "HARRAT ASH SHAAM": "purple",
        }
        
        # Plot each class
        for class_name in classes:
            mask = np.array(y) == class_name
            color = color_map.get(class_name, "gray")
            
            if X_lda.shape[1] >= 2:
                ax.scatter(X_lda[mask, 0], X_lda[mask, 1], 
                          c=color, label=class_name, s=100, alpha=0.6, 
                          edgecolors='black', linewidths=0.5)
            else:
                ax.scatter(X_lda[mask, 0], np.zeros(np.sum(mask)), 
                          c=color, label=class_name, s=100, alpha=0.6,
                          edgecolors='black', linewidths=0.5)
        
        ax.set_xlabel('LD1 (First Discriminant Function)', fontsize=12, fontweight='bold')
        if X_lda.shape[1] >= 2:
            ax.set_ylabel('LD2 (Second Discriminant Function)', fontsize=12, fontweight='bold')
        ax.set_title('Linear Discriminant Analysis - Provenance Separation', 
                    fontsize=14, fontweight='bold')
        ax.legend(loc='best', fontsize=9)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Embed
        canvas = FigureCanvasTkAgg(fig, self.dfa_plot_frame)
        canvas.draw()
        toolbar = NavigationToolbar2Tk(canvas, self.dfa_plot_frame)
        toolbar.update()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def _create_help_tab(self, parent):
        """Create help/documentation tab"""
        # Create scrollable text
        text_frame = tk.Frame(parent)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text = tk.Text(text_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set,
                      font=("Arial", 10), padx=10, pady=5)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text.yview)
        
        help_text = """
STATISTICAL ANALYSIS PLUGIN - USER GUIDE
═══════════════════════════════════════

PRINCIPAL COMPONENT ANALYSIS (PCA)
───────────────────────────────────

What is PCA?
PCA reduces multi-dimensional geochemical data to 2-3 principal components that
capture the most variation. This helps identify natural groupings in your samples.

How to use:
1. Select which elements to include (minimum 2)
2. Choose whether to standardize (recommended - equalizes element ranges)
3. Click "Run PCA Analysis"

Understanding the plots:
• Score Plot: Shows sample positions in reduced PC space. Samples that plot
  together are geochemically similar.
• Scree Plot: Shows how much variance each PC explains. Look for "elbow" point.
• Loadings Plot: Shows which elements contribute most to each PC.
• Variance Table: Quantifies variance explained by each component.

Interpretation tips:
- Samples from the same source should cluster together
- 70-80% cumulative variance in 2-3 PCs indicates good data reduction
- Loading arrows pointing same direction = positively correlated elements


CLUSTER ANALYSIS
────────────────

What is Clustering?
Automatically groups samples by geochemical similarity without requiring you
to pre-define source groups.

Hierarchical Clustering:
• Creates a dendrogram (tree) showing sample relationships
• "Ward" linkage minimizes within-cluster variance (recommended)
• Height of branches = dissimilarity between groups

K-Means Clustering:
• Partitions samples into k distinct groups
• Choose k based on expected number of sources
• Works best when clusters are spherical

How to use:
1. Run PCA first to prepare data
2. For hierarchical: select linkage method and click "Run Hierarchical"
3. For K-means: set number of clusters and click "Run K-Means"

Tips:
- Try both methods and compare results
- Dendrogram "height" where you cut determines number of clusters
- Validate clusters against known reference samples


RECOMMENDED WORKFLOW
────────────────────

1. Run PCA with all 6 elements to see overall patterns
2. Check scree plot - are 2-3 PCs sufficient?
3. Look at score plot - do known sources separate?
4. Run hierarchical clustering to see natural groupings
5. Try K-means with number of clusters matching known sources
6. Export plots for your publication/report


REFERENCES
──────────

- Baxter, M. J. (2003). Statistics in Archaeology
- Jolliffe, I. T. (2002). Principal Component Analysis
- Rousseeuw, P. J. (1987). Silhouettes: A graphical aid to the interpretation
  of cluster analysis

For more help, consult the main toolkit documentation or contact Sefy Levy.
"""
        
        text.insert("1.0", help_text)
        text.config(state=tk.DISABLED)
    
    def _export_plot(self, frame):
        """Export current plot to file"""
        # Find the canvas in the frame
        for widget in frame.winfo_children():
            if isinstance(widget, FigureCanvasTkAgg):
                filename = filedialog.asksaveasfilename(
                    defaultextension=".png",
                    filetypes=[
                        ("PNG Image", "*.png"),
                        ("PDF Document", "*.pdf"),
                        ("SVG Vector", "*.svg"),
                        ("All Files", "*.*")
                    ]
                )
                
                if filename:
                    try:
                        widget.figure.savefig(filename, dpi=300, bbox_inches='tight')
                        messagebox.showinfo("Export Successful", f"Plot saved to:\n{filename}", parent=self.window)
                    except Exception as e:
                        messagebox.showerror("Export Error", f"Failed to export plot:\n{e}", parent=self.window)
                return
        
        messagebox.showwarning("No Plot", "Generate a plot first before exporting", parent=self.window)

def setup_plugin(main_app):
    """Plugin setup function"""
    plugin = StatisticalAnalysisPlugin(main_app)
    return plugin
