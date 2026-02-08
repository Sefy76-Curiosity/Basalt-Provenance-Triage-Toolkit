"""
Machine Learning Plugin for Basalt Provenance Toolkit
Advanced ML analysis for geochemical classification and prediction

Features:
- Classification: Random Forest, SVM, KNN, Logistic Regression
- Clustering: K-means, DBSCAN, Hierarchical
- Dimensionality Reduction: PCA, t-SNE, UMAP
- Regression: Linear, Ridge, Lasso, Random Forest Regressor
- Feature importance and model evaluation
- Interactive visualization of results

Author: Sefy Levy
License: CC BY-NC-SA 4.0
"""

PLUGIN_INFO = {
    "category": "software",
    "id": "machine_learning",
    "name": "Machine Learning",
    "description": "Classification, clustering, PCA and ML analysis tools",
    "icon": "🤖",
    "version": "1.0",
    "requires": ["scikit-learn", "matplotlib", "numpy", "pandas", "seaborn"],
    "author": "Sefy Levy"
}

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import numpy as np
import pandas as pd
from io import StringIO
import threading
import traceback
import webbrowser
import json

# Check dependencies
HAS_SKLEARN = False
HAS_MATPLOTLIB = False
HAS_NUMPY = False
HAS_PANDAS = False
HAS_SEABORN = False
HAS_REQUIREMENTS = False

try:
    import sklearn
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
    from sklearn.metrics import silhouette_score, davies_bouldin_score
    from sklearn.decomposition import PCA
    from sklearn.manifold import TSNE
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
    from sklearn.svm import SVC, SVR
    from sklearn.neighbors import KNeighborsClassifier
    from sklearn.linear_model import LogisticRegression, Ridge, Lasso
    from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
    HAS_SKLEARN = True
except ImportError as e:
    SKLEARN_ERROR = str(e)

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    HAS_MATPLOTLIB = True
except ImportError as e:
    MATPLOTLIB_ERROR = str(e)

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    NUMPY_ERROR = "numpy not found"

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    PANDAS_ERROR = "pandas not found"

try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    SEABORN_ERROR = "seaborn not found"

HAS_REQUIREMENTS = HAS_SKLEARN and HAS_MATPLOTLIB and HAS_NUMPY and HAS_PANDAS


class MachineLearningPlugin:
    """Plugin for machine learning analysis"""

    def __init__(self, main_app):
        """Initialize plugin"""
        self.app = main_app
        self.window = None
        self.current_model = None
        self.current_results = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.feature_names = []
        self.target_name = ""

    def open_ml_window(self):
        """Open the machine learning interface"""
        # Check requirements
        if not HAS_REQUIREMENTS:
            missing = []
            if not HAS_SKLEARN: missing.append("scikit-learn")
            if not HAS_MATPLOTLIB: missing.append("matplotlib")
            if not HAS_NUMPY: missing.append("numpy")
            if not HAS_PANDAS: missing.append("pandas")

            response = messagebox.askyesno(
                "Missing Dependencies",
                f"Machine Learning requires these packages:\n\n"
                f"• scikit-learn\n• matplotlib\n• numpy\n• pandas\n\n"
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
        self.window.title("Machine Learning Analysis")
        self.window.geometry("1000x700")

        # Make window stay on top
        self.window.transient(self.app.root)

        self._create_interface()

        # Bring to front
        self.window.lift()
        self.window.focus_force()

    def _create_interface(self):
        """Create the ML interface"""
        # Header
        header = tk.Frame(self.window, bg="#673AB7")
        header.pack(fill=tk.X)

        tk.Label(header,
                text="🤖 Machine Learning Analysis",
                font=("Arial", 16, "bold"),
                bg="#673AB7", fg="white",
                pady=8).pack()

        # Create notebook
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Create tabs
        self._create_data_tab(notebook)
        self._create_classification_tab(notebook)
        self._create_clustering_tab(notebook)
        self._create_pca_tab(notebook)
        self._create_regression_tab(notebook)
        self._create_results_tab(notebook)
        self._create_help_tab(notebook)

    def _create_data_tab(self, notebook):
        """Create data preparation tab"""
        frame = tk.Frame(notebook)
        notebook.add(frame, text="📊 Data")

        # Content
        content = tk.Frame(frame)
        content.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        tk.Label(content,
                text="Select Features and Target",
                font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=5)

        # Data info frame
        info_frame = tk.LabelFrame(content, text="Dataset Info", padx=10, pady=10)
        info_frame.pack(fill=tk.X, pady=10)

        self.sample_count_label = tk.Label(info_frame, text="Samples: 0")
        self.sample_count_label.pack(anchor=tk.W)

        self.feature_count_label = tk.Label(info_frame, text="Features: 0")
        self.feature_count_label.pack(anchor=tk.W)

        self.target_label = tk.Label(info_frame, text="Target: None selected")
        self.target_label.pack(anchor=tk.W)

        # Feature selection
        feature_frame = tk.LabelFrame(content, text="Feature Selection", padx=10, pady=10)
        feature_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Lists for features and target
        list_frame = tk.Frame(feature_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        # Available features list
        tk.Label(list_frame, text="Available Features:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.feature_listbox = tk.Listbox(list_frame, selectmode=tk.MULTIPLE, height=15, width=30)
        self.feature_listbox.grid(row=1, column=0, sticky=tk.NSEW, padx=(0, 10))

        # Move buttons
        button_frame = tk.Frame(list_frame)
        button_frame.grid(row=1, column=1, sticky=tk.NS, padx=10)

        tk.Button(button_frame, text="→ Add →",
                 command=self._add_selected_features,
                 width=10).pack(pady=5)
        tk.Button(button_frame, text="← Remove ←",
                 command=self._remove_selected_features,
                 width=10).pack(pady=5)
        tk.Button(button_frame, text="Clear All",
                 command=self._clear_selected_features,
                 width=10).pack(pady=5)

        # Selected features list
        tk.Label(list_frame, text="Selected Features:").grid(row=0, column=2, sticky=tk.W, pady=5)
        self.selected_listbox = tk.Listbox(list_frame, height=15, width=30)
        self.selected_listbox.grid(row=1, column=2, sticky=tk.NSEW, padx=(10, 0))

        # Configure grid weights
        list_frame.columnconfigure(0, weight=1)
        list_frame.columnconfigure(2, weight=1)
        list_frame.rowconfigure(1, weight=1)

        # Target selection
        target_frame = tk.LabelFrame(content, text="Target Variable", padx=10, pady=10)
        target_frame.pack(fill=tk.X, pady=10)

        self.target_var = tk.StringVar()
        target_combo = ttk.Combobox(target_frame, textvariable=self.target_var, state="readonly")
        target_combo.pack(fill=tk.X, pady=5)

        # Update button
        tk.Button(content, text="🔄 Update Data from Current Samples",
                 command=self._update_data_lists,
                 bg="#2196F3", fg="white",
                 font=("Arial", 10, "bold"),
                 width=30, height=2).pack(pady=20)

        # Initial update
        self._update_data_lists()

    def _create_classification_tab(self, notebook):
        """Create classification tab"""
        frame = tk.Frame(notebook)
        notebook.add(frame, text="🎯 Classification")

        content = tk.Frame(frame, padx=15, pady=15)
        content.pack(fill=tk.BOTH, expand=True)

        tk.Label(content,
                text="Supervised Classification",
                font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=5)

        tk.Label(content,
                text="Train ML models to predict provenance classification",
                font=("Arial", 9)).pack(anchor=tk.W, pady="0 10")

        # Model selection
        model_frame = tk.LabelFrame(content, text="Model Selection", padx=10, pady=10)
        model_frame.pack(fill=tk.X, pady=10)

        self.class_model_var = tk.StringVar(value="Random Forest")
        models = ["Random Forest", "Support Vector Machine", "K-Nearest Neighbors", "Logistic Regression"]

        for model in models:
            tk.Radiobutton(model_frame, text=model, variable=self.class_model_var,
                          value=model, font=("Arial", 10)).pack(anchor=tk.W, pady=2)

        # Parameters frame
        param_frame = tk.LabelFrame(content, text="Model Parameters", padx=10, pady=10)
        param_frame.pack(fill=tk.X, pady=10)

        # Random Forest params
        self.rf_params_frame = tk.Frame(param_frame)
        tk.Label(self.rf_params_frame, text="n_estimators:").pack(side=tk.LEFT, padx=5)
        self.rf_n_estimators = tk.IntVar(value=100)
        tk.Entry(self.rf_params_frame, textvariable=self.rf_n_estimators, width=10).pack(side=tk.LEFT, padx=5)

        tk.Label(self.rf_params_frame, text="max_depth:").pack(side=tk.LEFT, padx=5)
        self.rf_max_depth = tk.StringVar(value="None")
        tk.Entry(self.rf_params_frame, textvariable=self.rf_max_depth, width=10).pack(side=tk.LEFT, padx=5)

        # SVM params
        self.svm_params_frame = tk.Frame(param_frame)
        tk.Label(self.svm_params_frame, text="C:").pack(side=tk.LEFT, padx=5)
        self.svm_c = tk.DoubleVar(value=1.0)
        tk.Entry(self.svm_params_frame, textvariable=self.svm_c, width=10).pack(side=tk.LEFT, padx=5)

        tk.Label(self.svm_params_frame, text="kernel:").pack(side=tk.LEFT, padx=5)
        self.svm_kernel = tk.StringVar(value="rbf")
        tk.Entry(self.svm_params_frame, textvariable=self.svm_kernel, width=10).pack(side=tk.LEFT, padx=5)

        # KNN params
        self.knn_params_frame = tk.Frame(param_frame)
        tk.Label(self.knn_params_frame, text="n_neighbors:").pack(side=tk.LEFT, padx=5)
        self.knn_n_neighbors = tk.IntVar(value=5)
        tk.Entry(self.knn_params_frame, textvariable=self.knn_n_neighbors, width=10).pack(side=tk.LEFT, padx=5)

        # Show/hide parameters based on model selection
        self._show_class_params()

        # Test split
        split_frame = tk.Frame(content)
        split_frame.pack(fill=tk.X, pady=10)

        tk.Label(split_frame, text="Test Size:").pack(side=tk.LEFT)
        self.test_size_var = tk.DoubleVar(value=0.2)
        tk.Scale(split_frame, from_=0.1, to=0.5, resolution=0.05, orient=tk.HORIZONTAL,
                variable=self.test_size_var, length=200).pack(side=tk.LEFT, padx=10)

        # Buttons
        button_frame = tk.Frame(content)
        button_frame.pack(pady=20)

        tk.Button(button_frame, text="🚀 Train & Evaluate Model",
                 command=self._run_classification,
                 bg="#4CAF50", fg="white",
                 font=("Arial", 11, "bold"),
                 width=25, height=2).pack()

        # Status
        self.class_status_label = tk.Label(content, text="", fg="gray")
        self.class_status_label.pack(pady=5)

    def _create_clustering_tab(self, notebook):
        """Create clustering tab"""
        frame = tk.Frame(notebook)
        notebook.add(frame, text="🔍 Clustering")

        content = tk.Frame(frame, padx=15, pady=15)
        content.pack(fill=tk.BOTH, expand=True)

        tk.Label(content,
                text="Unsupervised Clustering",
                font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=5)

        tk.Label(content,
                text="Discover natural groupings in your data",
                font=("Arial", 9)).pack(anchor=tk.W, pady="0 10")

        # Algorithm selection
        algo_frame = tk.LabelFrame(content, text="Clustering Algorithm", padx=10, pady=10)
        algo_frame.pack(fill=tk.X, pady=10)

        self.cluster_algo_var = tk.StringVar(value="K-means")
        algorithms = ["K-means", "DBSCAN", "Hierarchical"]

        for algo in algorithms:
            tk.Radiobutton(algo_frame, text=algo, variable=self.cluster_algo_var,
                          value=algo, font=("Arial", 10)).pack(anchor=tk.W, pady=2)

        # Parameters
        param_frame = tk.LabelFrame(content, text="Algorithm Parameters", padx=10, pady=10)
        param_frame.pack(fill=tk.X, pady=10)

        # K-means params
        self.kmeans_params_frame = tk.Frame(param_frame)
        tk.Label(self.kmeans_params_frame, text="n_clusters:").pack(side=tk.LEFT, padx=5)
        self.kmeans_n_clusters = tk.IntVar(value=3)
        tk.Entry(self.kmeans_params_frame, textvariable=self.kmeans_n_clusters, width=10).pack(side=tk.LEFT, padx=5)

        # DBSCAN params
        self.dbscan_params_frame = tk.Frame(param_frame)
        tk.Label(self.dbscan_params_frame, text="eps:").pack(side=tk.LEFT, padx=5)
        self.dbscan_eps = tk.DoubleVar(value=0.5)
        tk.Entry(self.dbscan_params_frame, textvariable=self.dbscan_eps, width=10).pack(side=tk.LEFT, padx=5)

        tk.Label(self.dbscan_params_frame, text="min_samples:").pack(side=tk.LEFT, padx=5)
        self.dbscan_min_samples = tk.IntVar(value=5)
        tk.Entry(self.dbscan_params_frame, textvariable=self.dbscan_min_samples, width=10).pack(side=tk.LEFT, padx=5)

        # Show/hide parameters
        self._show_cluster_params()

        # Button
        button_frame = tk.Frame(content)
        button_frame.pack(pady=20)

        tk.Button(button_frame, text="🔍 Run Clustering Analysis",
                 command=self._run_clustering,
                 bg="#FF9800", fg="white",
                 font=("Arial", 11, "bold"),
                 width=25, height=2).pack()

        # Status
        self.cluster_status_label = tk.Label(content, text="", fg="gray")
        self.cluster_status_label.pack(pady=5)

    def _create_pca_tab(self, notebook):
        """Create PCA/dimensionality reduction tab"""
        frame = tk.Frame(notebook)
        notebook.add(frame, text="📉 Dimensionality Reduction")

        content = tk.Frame(frame, padx=15, pady=15)
        content.pack(fill=tk.BOTH, expand=True)

        tk.Label(content,
                text="Principal Component Analysis (PCA)",
                font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=5)

        tk.Label(content,
                text="Reduce high-dimensional data to 2D/3D for visualization",
                font=("Arial", 9)).pack(anchor=tk.W, pady="0 10")

        # Method selection
        method_frame = tk.LabelFrame(content, text="Reduction Method", padx=10, pady=10)
        method_frame.pack(fill=tk.X, pady=10)

        self.pca_method_var = tk.StringVar(value="PCA")
        methods = ["PCA", "t-SNE"]

        for method in methods:
            tk.Radiobutton(method_frame, text=method, variable=self.pca_method_var,
                          value=method, font=("Arial", 10)).pack(anchor=tk.W, pady=2)

        # Parameters
        param_frame = tk.LabelFrame(content, text="Parameters", padx=10, pady=10)
        param_frame.pack(fill=tk.X, pady=10)

        # PCA params
        self.pca_params_frame = tk.Frame(param_frame)
        tk.Label(self.pca_params_frame, text="n_components:").pack(side=tk.LEFT, padx=5)
        self.pca_n_components = tk.StringVar(value="2")
        tk.Entry(self.pca_params_frame, textvariable=self.pca_n_components, width=10).pack(side=tk.LEFT, padx=5)

        # t-SNE params
        self.tsne_params_frame = tk.Frame(param_frame)
        tk.Label(self.tsne_params_frame, text="perplexity:").pack(side=tk.LEFT, padx=5)
        self.tsne_perplexity = tk.DoubleVar(value=30.0)
        tk.Entry(self.tsne_params_frame, textvariable=self.tsne_perplexity, width=10).pack(side=tk.LEFT, padx=5)

        # Show/hide parameters
        self._show_pca_params()

        # Coloring
        color_frame = tk.LabelFrame(content, text="Color Points By", padx=10, pady=10)
        color_frame.pack(fill=tk.X, pady=10)

        self.pca_color_var = tk.StringVar(value="Classification")
        colors = ["Classification", "Cluster", "None"]

        for color in colors:
            tk.Radiobutton(color_frame, text=color, variable=self.pca_color_var,
                          value=color, font=("Arial", 10)).pack(anchor=tk.W, pady=2)

        # Button
        button_frame = tk.Frame(content)
        button_frame.pack(pady=20)

        tk.Button(button_frame, text="📊 Visualize in 2D/3D",
                 command=self._run_pca,
                 bg="#9C27B0", fg="white",
                 font=("Arial", 11, "bold"),
                 width=25, height=2).pack()

        # Status
        self.pca_status_label = tk.Label(content, text="", fg="gray")
        self.pca_status_label.pack(pady=5)

    def _create_regression_tab(self, notebook):
        """Create regression tab"""
        frame = tk.Frame(notebook)
        notebook.add(frame, text="📈 Regression")

        content = tk.Frame(frame, padx=15, pady=15)
        content.pack(fill=tk.BOTH, expand=True)

        tk.Label(content,
                text="Regression Analysis",
                font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=5)

        tk.Label(content,
                text="Predict continuous values (e.g., concentration, thickness)",
                font=("Arial", 9)).pack(anchor=tk.W, pady="0 10")

        # Model selection
        model_frame = tk.LabelFrame(content, text="Regression Model", padx=10, pady=10)
        model_frame.pack(fill=tk.X, pady=10)

        self.reg_model_var = tk.StringVar(value="Random Forest")
        models = ["Random Forest", "Linear Regression", "Ridge", "Lasso"]

        for model in models:
            tk.Radiobutton(model_frame, text=model, variable=self.reg_model_var,
                          value=model, font=("Arial", 10)).pack(anchor=tk.W, pady=2)

        # Target selection for regression
        target_frame = tk.LabelFrame(content, text="Regression Target", padx=10, pady=10)
        target_frame.pack(fill=tk.X, pady=10)

        self.reg_target_var = tk.StringVar()
        self.reg_target_combo = ttk.Combobox(target_frame, textvariable=self.reg_target_var, state="readonly")
        self.reg_target_combo.pack(fill=tk.X, pady=5)

        # Update target list
        self._update_regression_targets()

        # Button
        button_frame = tk.Frame(content)
        button_frame.pack(pady=20)

        tk.Button(button_frame, text="📈 Run Regression",
                 command=self._run_regression,
                 bg="#2196F3", fg="white",
                 font=("Arial", 11, "bold"),
                 width=25, height=2).pack()

        # Status
        self.reg_status_label = tk.Label(content, text="", fg="gray")
        self.reg_status_label.pack(pady=5)

    def _create_results_tab(self, notebook):
        """Create results display tab"""
        frame = tk.Frame(notebook)
        notebook.add(frame, text="📋 Results")

        content = tk.Frame(frame)
        content.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Text widget for results
        self.results_text = scrolledtext.ScrolledText(content, wrap=tk.WORD,
                                                     font=("Courier New", 9))
        self.results_text.pack(fill=tk.BOTH, expand=True)

        # Clear button
        tk.Button(content, text="Clear Results",
                 command=lambda: self.results_text.delete(1.0, tk.END)).pack(pady=5)

    def _create_help_tab(self, notebook):
        """Create help tab"""
        frame = tk.Frame(notebook)
        notebook.add(frame, text="❓ Help")

        from tkinter import scrolledtext
        text = scrolledtext.ScrolledText(frame, wrap=tk.WORD,
                                        font=("Arial", 10), padx=8, pady=5)
        text.pack(fill=tk.BOTH, expand=True)

        help_text = """
MACHINE LEARNING PLUGIN - USER GUIDE
═══════════════════════════════════════════════════════════════

OVERVIEW
────────────────────────────────────────────────────────────────
This plugin provides machine learning tools for geochemical data:

1. CLASSIFICATION: Predict categorical labels (provenance)
2. CLUSTERING: Discover natural groupings in data
3. PCA: Reduce dimensions for visualization
4. REGRESSION: Predict continuous values

═══════════════════════════════════════════════════════════════

WORKFLOW
────────────────────────────────────────────────────────────────

1. DATA PREPARATION TAB:
   • Select features (element concentrations)
   • Choose target variable (classification labels)
   • Update from current dataset

2. CLASSIFICATION TAB:
   • Choose algorithm (Random Forest, SVM, etc.)
   • Set parameters
   • Train and evaluate model
   • View accuracy, confusion matrix

3. CLUSTERING TAB:
   • Choose algorithm (K-means, DBSCAN, etc.)
   • Find natural clusters
   • Compare with known classifications

4. PCA TAB:
   • Reduce high-dimensional data to 2D/3D
   • Visualize patterns
   • Color by classification or clusters

5. REGRESSION TAB:
   • Predict continuous values
   • Choose regression algorithm
   • Evaluate R² score

═══════════════════════════════════════════════════════════════

MODEL SELECTION GUIDE
────────────────────────────────────────────────────────────────

CLASSIFICATION:
• RANDOM FOREST: Good default, handles non-linear data
• SVM: Good for high-dimensional data, needs scaling
• KNN: Simple, interpretable
• LOGISTIC REGRESSION: Linear relationships only

CLUSTERING:
• K-MEANS: Spherical clusters, fast
• DBSCAN: Arbitrary shapes, handles noise
• HIERARCHICAL: Nested clusters, dendrogram

DIMENSIONALITY REDUCTION:
• PCA: Linear reduction, preserves variance
• t-SNE: Non-linear, preserves local structure

═══════════════════════════════════════════════════════════════

INTERPRETING RESULTS
────────────────────────────────────────────────────────────────

CLASSIFICATION:
• Accuracy: Overall correct predictions
• Precision: Correct positive predictions
• Recall: Ability to find all positives
• F1-Score: Balance of precision/recall
• Confusion Matrix: Error breakdown

CLUSTERING:
• Silhouette Score: -1 to 1 (higher is better)
• Davies-Bouldin: Lower is better
• Visual inspection: Check cluster plots

PCA:
• Explained Variance: % variance captured
• Loadings: Original feature contributions
• Biplots: Features + samples

═══════════════════════════════════════════════════════════════

BEST PRACTICES
────────────────────────────────────────────────────────────────

1. Always scale features before SVM, PCA
2. Use cross-validation for reliable estimates
3. Start with Random Forest as baseline
4. Visualize clusters in PCA space
5. Check feature importance for interpretation
6. Compare ML results with geochemical knowledge

═══════════════════════════════════════════════════════════════

EXAMPLE USE CASES
────────────────────────────────────────────────────────────────

PROVENANCE PREDICTION:
• Train on known source samples
• Predict unknown artifact origins
• Compare with geochemical fingerprints

QUALITY CONTROL:
• Cluster to detect outliers
• Identify analytical batches
• Find mixed or contaminated samples

EXPLORATION:
• PCA to visualize dataset structure
• Clustering to find natural groups
• Regression to predict element concentrations

═══════════════════════════════════════════════════════════════

TROUBLESHOOTING
────────────────────────────────────────────────────────────────

"Not enough samples":
→ Minimum 10-20 samples per class
→ Use simpler models (KNN, Logistic Regression)

"Poor accuracy":
→ Check feature selection
→ Try different algorithms
→ Scale features
→ Remove outliers

"Clustering not working":
→ Adjust parameters (eps, min_samples)
→ Try different algorithms
→ Pre-process with PCA first

"Memory errors":
→ Reduce number of features
→ Use simpler models
→ Increase RAM if possible

═══════════════════════════════════════════════════════════════
"""

        text.insert('1.0', help_text)
        text.config(state='disabled')

    def _show_class_params(self):
        """Show/hide classification parameters"""
        self.rf_params_frame.pack_forget()
        self.svm_params_frame.pack_forget()
        self.knn_params_frame.pack_forget()

        model = self.class_model_var.get()
        if model == "Random Forest":
            self.rf_params_frame.pack(anchor=tk.W, pady=5)
        elif model == "Support Vector Machine":
            self.svm_params_frame.pack(anchor=tk.W, pady=5)
        elif model == "K-Nearest Neighbors":
            self.knn_params_frame.pack(anchor=tk.W, pady=5)

    def _show_cluster_params(self):
        """Show/hide clustering parameters"""
        self.kmeans_params_frame.pack_forget()
        self.dbscan_params_frame.pack_forget()

        algo = self.cluster_algo_var.get()
        if algo == "K-means":
            self.kmeans_params_frame.pack(anchor=tk.W, pady=5)
        elif algo == "DBSCAN":
            self.dbscan_params_frame.pack(anchor=tk.W, pady=5)

    def _show_pca_params(self):
        """Show/hide PCA parameters"""
        self.pca_params_frame.pack_forget()
        self.tsne_params_frame.pack_forget()

        method = self.pca_method_var.get()
        if method == "PCA":
            self.pca_params_frame.pack(anchor=tk.W, pady=5)
        elif method == "t-SNE":
            self.tsne_params_frame.pack(anchor=tk.W, pady=5)

    def _update_data_lists(self):
        """Update feature lists from current samples"""
        if not self.app.samples:
            messagebox.showwarning("No Data", "No samples loaded.")
            return

        # Get all numeric columns (potential features)
        numeric_features = []
        categorical_features = []

        # Try to get columns from first sample
        sample = self.app.samples[0]

        for key in sample.keys():
            value = sample.get(key)
            if value is not None and value != '':
                try:
                    # Try to convert to float
                    float_val = float(value)
                    numeric_features.append(key)
                except (ValueError, TypeError):
                    categorical_features.append(key)

        # Update feature listbox
        self.feature_listbox.delete(0, tk.END)
        for feature in sorted(numeric_features):
            self.feature_listbox.insert(tk.END, feature)

        # Update target combobox with categorical features
        self.target_var.set('')
        target_values = ["Final_Classification", "Auto_Classification"] + sorted(categorical_features)

        # Update both classification and regression targets
        self.reg_target_combo['values'] = sorted(numeric_features)

        # Update labels
        self.sample_count_label.config(text=f"Samples: {len(self.app.samples)}")
        self.feature_count_label.config(text=f"Features: {len(numeric_features)}")

    def _add_selected_features(self):
        """Add selected features to selected list"""
        selected = self.feature_listbox.curselection()
        for idx in selected:
            feature = self.feature_listbox.get(idx)
            if feature not in self.selected_listbox.get(0, tk.END):
                self.selected_listbox.insert(tk.END, feature)

    def _remove_selected_features(self):
        """Remove selected features from selected list"""
        selected = self.selected_listbox.curselection()
        for idx in reversed(selected):
            self.selected_listbox.delete(idx)

    def _clear_selected_features(self):
        """Clear all selected features"""
        self.selected_listbox.delete(0, tk.END)

    def _update_regression_targets(self):
        """Update regression target list"""
        if not self.app.samples:
            return

        # Get numeric columns
        numeric_features = []
        sample = self.app.samples[0]

        for key in sample.keys():
            value = sample.get(key)
            if value is not None and value != '':
                try:
                    float(value)
                    numeric_features.append(key)
                except (ValueError, TypeError):
                    continue

        self.reg_target_combo['values'] = sorted(numeric_features)

    def _prepare_data(self, for_regression=False):
        """Prepare data for ML analysis"""
        # Get selected features
        features = list(self.selected_listbox.get(0, tk.END))

        if not features:
            messagebox.showwarning("No Features", "Please select features for analysis.")
            return None

        # Get target
        if for_regression:
            target = self.reg_target_var.get()
            if not target:
                messagebox.showwarning("No Target", "Please select a regression target.")
                return None
        else:
            target = self.target_var.get()
            if not target:
                messagebox.showwarning("No Target", "Please select a classification target.")
                return None

        # Prepare data arrays
        X = []
        y = []
        valid_samples = []

        for sample in self.app.samples:
            # Get feature values
            row = []
            valid = True
            for feature in features:
                value = sample.get(feature)
                try:
                    row.append(float(value))
                except (ValueError, TypeError):
                    valid = False
                    break

            if valid:
                # Get target value
                target_value = sample.get(target)
                if target_value is not None and target_value != '':
                    X.append(row)
                    y.append(target_value)
                    valid_samples.append(sample)

        if len(X) < 10:
            messagebox.showwarning("Insufficient Data",
                                 f"Only {len(X)} samples have complete data. Need at least 10.")
            return None

        # Convert to numpy arrays
        X = np.array(X)
        y = np.array(y)

        # For classification, encode labels
        if not for_regression:
            le = LabelEncoder()
            y = le.fit_transform(y)
            self.label_encoder = le
        else:
            y = y.astype(float)

        # Split data
        test_size = self.test_size_var.get() if hasattr(self, 'test_size_var') else 0.2

        if for_regression or len(np.unique(y)) > 1:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42, stratify=y if not for_regression else None
            )
        else:
            # Not enough classes for stratification
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42
            )

        self.X_train = X_train
        self.X_test = X_test
        self.y_train = y_train
        self.y_test = y_test
        self.feature_names = features
        self.target_name = target
        self.valid_samples = valid_samples

        return True

    def _run_classification(self):
        """Run classification analysis"""
        if not self._prepare_data(for_regression=False):
            return

        try:
            model_type = self.class_model_var.get()

            # Scale features for SVM
            scaler = StandardScaler()
            if model_type == "Support Vector Machine":
                X_train_scaled = scaler.fit_transform(self.X_train)
                X_test_scaled = scaler.transform(self.X_test)
            else:
                X_train_scaled = self.X_train
                X_test_scaled = self.X_test

            # Create model
            if model_type == "Random Forest":
                max_depth = None if self.rf_max_depth.get() == "None" else int(self.rf_max_depth.get())
                model = RandomForestClassifier(
                    n_estimators=self.rf_n_estimators.get(),
                    max_depth=max_depth,
                    random_state=42
                )
            elif model_type == "Support Vector Machine":
                model = SVC(
                    C=self.svm_c.get(),
                    kernel=self.svm_kernel.get(),
                    random_state=42
                )
            elif model_type == "K-Nearest Neighbors":
                model = KNeighborsClassifier(
                    n_neighbors=self.knn_n_neighbors.get()
                )
            elif model_type == "Logistic Regression":
                model = LogisticRegression(random_state=42, max_iter=1000)
            else:
                messagebox.showerror("Error", f"Unknown model: {model_type}")
                return

            # Train model
            model.fit(X_train_scaled, self.y_train)

            # Make predictions
            y_pred = model.predict(X_test_scaled)

            # Calculate metrics
            accuracy = accuracy_score(self.y_test, y_pred)
            report = classification_report(self.y_test, y_pred,
                                          target_names=self.label_encoder.classes_)

            # Feature importance for Random Forest
            if model_type == "Random Forest":
                importances = model.feature_importances_
                feature_importance = sorted(zip(self.feature_names, importances),
                                          key=lambda x: x[1], reverse=True)

            # Store results
            self.current_model = model
            self.current_results = {
                'type': 'classification',
                'model': model_type,
                'accuracy': accuracy,
                'report': report,
                'y_true': self.y_test,
                'y_pred': y_pred,
                'feature_importance': feature_importance if model_type == "Random Forest" else None
            }

            # Display results
            self._display_classification_results(accuracy, report,
                                                feature_importance if model_type == "Random Forest" else None)

            # Plot confusion matrix
            self._plot_confusion_matrix(self.y_test, y_pred, self.label_encoder.classes_)

            self.class_status_label.config(text=f"✅ Model trained - Accuracy: {accuracy:.2%}")

        except Exception as e:
            messagebox.showerror("Classification Error", f"Error: {str(e)}\n\n{traceback.format_exc()}")

    def _run_clustering(self):
        """Run clustering analysis"""
        if not self._prepare_data(for_regression=False):
            return

        try:
            algo = self.cluster_algo_var.get()

            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(self.X_train)

            # Apply clustering
            if algo == "K-means":
                n_clusters = self.kmeans_n_clusters.get()
                model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
                labels = model.fit_predict(X_scaled)
                centers = model.cluster_centers_

            elif algo == "DBSCAN":
                model = DBSCAN(eps=self.dbscan_eps.get(),
                              min_samples=self.dbscan_min_samples.get())
                labels = model.fit_predict(X_scaled)
                centers = None

            elif algo == "Hierarchical":
                model = AgglomerativeClustering(n_clusters=self.kmeans_n_clusters.get())
                labels = model.fit_predict(X_scaled)
                centers = None
            else:
                messagebox.showerror("Error", f"Unknown algorithm: {algo}")
                return

            # Calculate metrics
            if len(set(labels)) > 1:
                silhouette = silhouette_score(X_scaled, labels)
                db_score = davies_bouldin_score(X_scaled, labels)
            else:
                silhouette = -1
                db_score = float('inf')

            # Store results
            self.current_results = {
                'type': 'clustering',
                'algorithm': algo,
                'labels': labels,
                'centers': centers,
                'silhouette': silhouette,
                'davies_bouldin': db_score
            }

            # Display results
            self._display_clustering_results(labels, silhouette, db_score)

            # Visualize clusters
            self._plot_clusters(X_scaled, labels, centers)

            self.cluster_status_label.config(text=f"✅ Clustering complete - {len(set(labels))} clusters found")

        except Exception as e:
            messagebox.showerror("Clustering Error", f"Error: {str(e)}\n\n{traceback.format_exc()}")

    def _run_pca(self):
        """Run PCA/dimensionality reduction"""
        if not self._prepare_data(for_regression=False):
            return

        try:
            method = self.pca_method_var.get()

            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(self.X_train)

            # Apply reduction
            if method == "PCA":
                n_components = int(self.pca_n_components.get())
                model = PCA(n_components=n_components, random_state=42)
                X_reduced = model.fit_transform(X_scaled)
                explained_variance = model.explained_variance_ratio_

            elif method == "t-SNE":
                model = TSNE(n_components=2,
                            perplexity=self.tsne_perplexity.get(),
                            random_state=42)
                X_reduced = model.fit_transform(X_scaled)
                explained_variance = None
            else:
                messagebox.showerror("Error", f"Unknown method: {method}")
                return

            # Get coloring
            color_by = self.pca_color_var.get()
            if color_by == "Classification":
                colors = self.y_train
                color_label = "True Classes"
            elif color_by == "Cluster":
                if hasattr(self, 'current_results') and self.current_results.get('type') == 'clustering':
                    colors = self.current_results['labels']
                    color_label = "Cluster Labels"
                else:
                    colors = None
                    color_label = "No Clustering"
            else:
                colors = None
                color_label = "No Color"

            # Store results
            self.current_results = {
                'type': 'pca',
                'method': method,
                'X_reduced': X_reduced,
                'explained_variance': explained_variance,
                'colors': colors,
                'color_label': color_label
            }

            # Display results
            self._display_pca_results(explained_variance)

            # Plot
            self._plot_pca(X_reduced, colors, color_label, method)

            self.pca_status_label.config(text=f"✅ {method} complete - Dimensions: {X_reduced.shape[1]}")

        except Exception as e:
            messagebox.showerror("PCA Error", f"Error: {str(e)}\n\n{traceback.format_exc()}")

    def _run_regression(self):
        """Run regression analysis"""
        if not self._prepare_data(for_regression=True):
            return

        try:
            model_type = self.reg_model_var.get()

            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(self.X_train)
            X_test_scaled = scaler.transform(self.X_test)

            # Create model
            if model_type == "Random Forest":
                model = RandomForestRegressor(n_estimators=100, random_state=42)
            elif model_type == "Linear Regression":
                from sklearn.linear_model import LinearRegression
                model = LinearRegression()
            elif model_type == "Ridge":
                model = Ridge(alpha=1.0)
            elif model_type == "Lasso":
                model = Lasso(alpha=1.0)
            else:
                messagebox.showerror("Error", f"Unknown model: {model_type}")
                return

            # Train model
            model.fit(X_train_scaled, self.y_train)

            # Make predictions
            y_pred = model.predict(X_test_scaled)

            # Calculate metrics
            from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
            r2 = r2_score(self.y_test, y_pred)
            mse = mean_squared_error(self.y_test, y_pred)
            mae = mean_absolute_error(self.y_test, y_pred)

            # Feature importance for Random Forest
            if model_type == "Random Forest":
                importances = model.feature_importances_
                feature_importance = sorted(zip(self.feature_names, importances),
                                          key=lambda x: x[1], reverse=True)

            # Store results
            self.current_model = model
            self.current_results = {
                'type': 'regression',
                'model': model_type,
                'r2': r2,
                'mse': mse,
                'mae': mae,
                'y_true': self.y_test,
                'y_pred': y_pred,
                'feature_importance': feature_importance if model_type == "Random Forest" else None
            }

            # Display results
            self._display_regression_results(r2, mse, mae,
                                            feature_importance if model_type == "Random Forest" else None)

            # Plot predictions
            self._plot_regression_results(self.y_test, y_pred, self.target_name)

            self.reg_status_label.config(text=f"✅ Regression complete - R²: {r2:.3f}")

        except Exception as e:
            messagebox.showerror("Regression Error", f"Error: {str(e)}\n\n{traceback.format_exc()}")

    def _display_classification_results(self, accuracy, report, feature_importance=None):
        """Display classification results"""
        self.results_text.delete(1.0, tk.END)

        self.results_text.insert(tk.END, "="*60 + "\n")
        self.results_text.insert(tk.END, "CLASSIFICATION RESULTS\n")
        self.results_text.insert(tk.END, "="*60 + "\n\n")

        self.results_text.insert(tk.END, f"Accuracy: {accuracy:.2%}\n\n")
        self.results_text.insert(tk.END, "Classification Report:\n")
        self.results_text.insert(tk.END, report + "\n")

        if feature_importance:
            self.results_text.insert(tk.END, "\nFeature Importance (Random Forest):\n")
            for feature, importance in feature_importance[:10]:  # Top 10
                self.results_text.insert(tk.END, f"  {feature}: {importance:.4f}\n")

    def _display_clustering_results(self, labels, silhouette, db_score):
        """Display clustering results"""
        self.results_text.delete(1.0, tk.END)

        self.results_text.insert(tk.END, "="*60 + "\n")
        self.results_text.insert(tk.END, "CLUSTERING RESULTS\n")
        self.results_text.insert(tk.END, "="*60 + "\n\n")

        unique_clusters = set(labels)
        n_clusters = len(unique_clusters)

        self.results_text.insert(tk.END, f"Number of clusters: {n_clusters}\n")
        self.results_text.insert(tk.END, f"Silhouette Score: {silhouette:.3f}\n")
        self.results_text.insert(tk.END, f"Davies-Bouldin Score: {db_score:.3f}\n\n")

        # Cluster sizes
        self.results_text.insert(tk.END, "Cluster sizes:\n")
        for cluster in sorted(unique_clusters):
            count = sum(1 for l in labels if l == cluster)
            self.results_text.insert(tk.END, f"  Cluster {cluster}: {count} samples\n")

    def _display_pca_results(self, explained_variance):
        """Display PCA results"""
        self.results_text.delete(1.0, tk.END)

        self.results_text.insert(tk.END, "="*60 + "\n")
        self.results_text.insert(tk.END, "DIMENSIONALITY REDUCTION RESULTS\n")
        self.results_text.insert(tk.END, "="*60 + "\n\n")

        if explained_variance is not None:
            self.results_text.insert(tk.END, "Explained Variance Ratios:\n")
            for i, var in enumerate(explained_variance):
                self.results_text.insert(tk.END, f"  PC{i+1}: {var:.2%}\n")

            cumulative = sum(explained_variance)
            self.results_text.insert(tk.END, f"\nCumulative Variance: {cumulative:.2%}\n")

    def _display_regression_results(self, r2, mse, mae, feature_importance=None):
        """Display regression results"""
        self.results_text.delete(1.0, tk.END)

        self.results_text.insert(tk.END, "="*60 + "\n")
        self.results_text.insert(tk.END, "REGRESSION RESULTS\n")
        self.results_text.insert(tk.END, "="*60 + "\n\n")

        self.results_text.insert(tk.END, f"R² Score: {r2:.4f}\n")
        self.results_text.insert(tk.END, f"Mean Squared Error: {mse:.4f}\n")
        self.results_text.insert(tk.END, f"Mean Absolute Error: {mae:.4f}\n\n")

        if feature_importance:
            self.results_text.insert(tk.END, "Feature Importance (Random Forest):\n")
            for feature, importance in feature_importance[:10]:  # Top 10
                self.results_text.insert(tk.END, f"  {feature}: {importance:.4f}\n")

    def _plot_confusion_matrix(self, y_true, y_pred, class_names):
        """Plot confusion matrix"""
        try:
            cm = confusion_matrix(y_true, y_pred)

            fig, ax = plt.subplots(figsize=(8, 6))

            # Use seaborn if available
            if HAS_SEABORN:
                sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                           xticklabels=class_names, yticklabels=class_names,
                           ax=ax)
            else:
                # Fallback to matplotlib
                im = ax.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
                ax.figure.colorbar(im, ax=ax)

                # Add text annotations
                thresh = cm.max() / 2.
                for i in range(cm.shape[0]):
                    for j in range(cm.shape[1]):
                        ax.text(j, i, format(cm[i, j], 'd'),
                               ha="center", va="center",
                               color="white" if cm[i, j] > thresh else "black")

            ax.set_xlabel('Predicted')
            ax.set_ylabel('True')
            ax.set_title('Confusion Matrix')

            plt.tight_layout()
            plt.show()

        except Exception as e:
            print(f"Error plotting confusion matrix: {e}")

    def _plot_clusters(self, X, labels, centers):
        """Plot clusters"""
        try:
            # Reduce to 2D for visualization
            from sklearn.decomposition import PCA
            pca = PCA(n_components=2, random_state=42)
            X_2d = pca.fit_transform(X)

            fig, ax = plt.subplots(figsize=(10, 8))

            # Scatter plot
            scatter = ax.scatter(X_2d[:, 0], X_2d[:, 1], c=labels, cmap='viridis',
                                alpha=0.7, edgecolors='k', s=50)

            # Plot centers if available
            if centers is not None:
                centers_2d = pca.transform(centers)
                ax.scatter(centers_2d[:, 0], centers_2d[:, 1], c='red', marker='X',
                          s=200, edgecolors='black', linewidth=2, label='Cluster Centers')

            ax.set_xlabel('PCA Component 1')
            ax.set_ylabel('PCA Component 2')
            ax.set_title(f'Clusters (n={len(set(labels))})')
            ax.legend()
            ax.grid(True, alpha=0.3)

            plt.tight_layout()
            plt.show()

        except Exception as e:
            print(f"Error plotting clusters: {e}")

    def _plot_pca(self, X_reduced, colors, color_label, method):
        """Plot PCA results"""
        try:
            fig, ax = plt.subplots(figsize=(10, 8))

            if colors is not None:
                scatter = ax.scatter(X_reduced[:, 0], X_reduced[:, 1],
                                    c=colors, cmap='tab20',
                                    alpha=0.7, edgecolors='k', s=50)

                # Add colorbar
                plt.colorbar(scatter, ax=ax, label=color_label)
            else:
                ax.scatter(X_reduced[:, 0], X_reduced[:, 1],
                          alpha=0.7, edgecolors='k', s=50)

            ax.set_xlabel(f'{method} Component 1')
            ax.set_ylabel(f'{method} Component 2')
            ax.set_title(f'{method} Visualization')
            ax.grid(True, alpha=0.3)

            plt.tight_layout()
            plt.show()

        except Exception as e:
            print(f"Error plotting PCA: {e}")

    def _plot_regression_results(self, y_true, y_pred, target_name):
        """Plot regression results"""
        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

            # Scatter plot: predicted vs actual
            ax1.scatter(y_true, y_pred, alpha=0.6, edgecolors='k')

            # Perfect prediction line
            min_val = min(min(y_true), min(y_pred))
            max_val = max(max(y_true), max(y_pred))
            ax1.plot([min_val, max_val], [min_val, max_val], 'r--', label='Perfect Prediction')

            ax1.set_xlabel(f'Actual {target_name}')
            ax1.set_ylabel(f'Predicted {target_name}')
            ax1.set_title('Predicted vs Actual')
            ax1.legend()
            ax1.grid(True, alpha=0.3)

            # Residuals plot
            residuals = y_true - y_pred
            ax2.scatter(y_pred, residuals, alpha=0.6, edgecolors='k')
            ax2.axhline(y=0, color='r', linestyle='--')

            ax2.set_xlabel(f'Predicted {target_name}')
            ax2.set_ylabel('Residuals')
            ax2.set_title('Residuals Plot')
            ax2.grid(True, alpha=0.3)

            plt.tight_layout()
            plt.show()

        except Exception as e:
            print(f"Error plotting regression results: {e}")

    def _install_dependencies(self, missing_packages):
        """Install missing dependencies"""
        response = messagebox.askyesno(
            "Install Dependencies",
            f"Install these packages:\n\n{', '.join(missing_packages)}\n\n"
            f"This may take a few minutes.",
            parent=self.window
        )

        if response:
            # Try to use plugin manager
            if hasattr(self.app, 'open_plugin_manager'):
                self.window.destroy()
                self.app.open_plugin_manager()
            else:
                # Manual instructions
                pip_cmd = "pip install " + " ".join(missing_packages)
                messagebox.showinfo(
                    "Install Manually",
                    f"Run in terminal:\n\n{pip_cmd}\n\n"
                    f"Then restart the application.",
                    parent=self.window
                )

# Bind to application menu
def setup_plugin(main_app):
    """Setup function called by main application"""
    plugin = MachineLearningPlugin(main_app)

    # Add to Tools menu
    if hasattr(main_app, 'menu_bar'):
        main_app.menu_bar.add_command(
            label="Machine Learning",
            command=plugin.open_ml_window
        )

    return plugin
