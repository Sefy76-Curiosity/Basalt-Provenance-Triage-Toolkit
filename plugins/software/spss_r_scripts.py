"""
Advanced Statistics Plugin for Basalt Provenance Toolkit
SPSS/R-like statistical analysis

Author: Sefy Levy
License: CC BY-NC-SA 4.0
"""

PLUGIN_INFO = {
      "category": "software",
    "id": "advanced_statistics",
    "name": "SPSS/R Advanced Statistics",
    "description": "Statistical analysis: PCA, clustering, ANOVA, discriminant functions",
    "icon": "📈",  # SINGLE ICON ONLY
    "version": "1.0",
    "requires": ["scikit-learn", "scipy", "pandas", "statsmodels"],
    "author": "Sefy Levy"
}

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import webbrowser
import tempfile
import os
import json
import subprocess
import platform
import statistics

# ========== DEPENDENCY CHECKING ==========
TIER_1_AVAILABLE = True  # Basic Python (always)
TIER_2_AVAILABLE = False  # scikit-learn
HAS_SCIKIT_LEARN = False
HAS_SCIPY = False
HAS_STATSMODELS = False
HAS_PANDAS = False

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    import scipy.stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    from sklearn.decomposition import PCA
    from sklearn.cluster import KMeans
    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
    from sklearn.preprocessing import StandardScaler
    HAS_SCIKIT_LEARN = True
except ImportError:
    HAS_SCIKIT_LEARN = False

try:
    import statsmodels.api as sm
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False

if HAS_SCIKIT_LEARN and HAS_SCIPY and HAS_PANDAS:
    TIER_2_AVAILABLE = True


def safe_float(value):
    """Safely convert value to float"""
    if value is None or value == '':
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


class AdvancedStatisticsPlugin:
    """Plugin for advanced statistical analysis"""

    def __init__(self, main_app):
        """Initialize plugin"""
        self.app = main_app
        self.window = None
        self.numeric_vars = []
        self.var_checkboxes = {}

    def open_statistics_window(self):
        """Open the statistics interface"""
        # Check for any statistics capability
        if not TIER_1_AVAILABLE and not TIER_2_AVAILABLE:
            messagebox.showerror(
                "No Statistics Available",
                "No statistical packages found.\n\n"
                "Please install at least:\n"
                "pip install pandas scipy\n\n"
                "For advanced features:\n"
                "pip install scikit-learn statsmodels",
                parent=self.app.root
            )
            return

        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("📊 SPSS/R Advanced Statistics")
        self.window.geometry("700x520")  # REASONABLE SIZE

        # Prevent window from being too large
        self.window.maxsize(1000, 800)
        self.window.minsize(700, 500)

        self.window.transient(self.app.root)
        self._create_interface()
        self.window.lift()
        self.window.focus_force()

    def _create_interface(self):
        """Create the statistics interface"""
        # Header
        header = tk.Frame(self.window, bg="#3F51B5")
        header.pack(fill=tk.X)

        tk.Label(header,
                text="📊 SPSS/R Advanced Statistics",
                font=("Arial", 16, "bold"),
                bg="#3F51B5", fg="white",
                pady=12).pack()

        # Status banner
        if TIER_2_AVAILABLE:
            status_text = "✅ scikit-learn available for advanced analysis"
            status_bg = "#E3F2FD"
            status_fg = "green"
        else:
            status_text = "⚠️ Install scikit-learn for full features"
            status_bg = "#FFF3E0"
            status_fg = "orange"

        status_frame = tk.Frame(self.window, bg=status_bg, relief=tk.RAISED, borderwidth=1)
        status_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(status_frame,
                text=status_text,
                font=("Arial", 9, "bold"),
                bg=status_bg, fg=status_fg,
                pady=8).pack()

        # Create notebook
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Tab 1: Basic Statistics
        self._create_basic_stats_tab(notebook)

        # Tab 2: Multivariate Analysis
        self._create_multivariate_tab(notebook)

        # Tab 3: Results
        self._create_results_tab(notebook)

    def _create_basic_stats_tab(self, notebook):
        """Create basic statistics tab"""
        frame = tk.Frame(notebook)
        notebook.add(frame, text="📋 Basic Stats")

        # Main content with scrollbar
        container = tk.Frame(frame)
        container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        content = scrollable_frame

        # Title
        tk.Label(content,
                text="Descriptive Statistics & Tests",
                font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=3,
                                               sticky="w", pady=(10, 15), padx=10)

        # Get numeric variables from samples
        self._populate_numeric_vars()

        # Variable selection
        var_frame = tk.LabelFrame(content, text="Select Variables",
                                 font=("Arial", 10, "bold"),
                                 padx=10, pady=5)
        var_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=10, pady=5)

        self.var_checkboxes = {}
        row_num = 0
        col_num = 0

        for i, var in enumerate(self.numeric_vars[:15]):  # Limit to 15
            var_bool = tk.BooleanVar()
            cb = tk.Checkbutton(var_frame, text=var,
                               variable=var_bool, font=("Arial", 9))
            cb.grid(row=row_num, column=col_num, sticky="w", padx=5, pady=2)
            self.var_checkboxes[var] = var_bool

            col_num += 1
            if col_num >= 3:
                col_num = 0
                row_num += 1

        # Grouping variable
        group_frame = tk.Frame(content)
        group_frame.grid(row=2, column=0, columnspan=3, sticky="w", padx=10, pady=5)

        tk.Label(group_frame, text="Group by Classification:",
                font=("Arial", 10)).pack(side=tk.LEFT)

        self.group_var = tk.StringVar(value="Final_Classification")
        group_combo = ttk.Combobox(group_frame, textvariable=self.group_var,
                                 values=["Final_Classification", "Auto_Classification"],
                                 state='readonly', width=25)
        group_combo.pack(side=tk.LEFT, padx=10)

        # Select All button
        tk.Button(group_frame, text="Select All Variables",
                 command=self._select_all_vars,
                 font=("Arial", 9)).pack(side=tk.LEFT, padx=10)

        # Analysis buttons
        btn_frame = tk.Frame(content)
        btn_frame.grid(row=3, column=0, columnspan=3, pady=8, padx=10)

        tk.Button(btn_frame, text="📊 Descriptive Stats",
                 command=self._run_descriptive_stats,
                 bg="#2196F3", fg="white",
                 font=("Arial", 10, "bold"),
                 width=20, height=2).pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame, text="📈 ANOVA / t-test",
                 command=self._run_anova_ttest,
                 bg="#4CAF50", fg="white",
                 font=("Arial", 10, "bold"),
                 width=20, height=2).pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame, text="📉 Correlation Matrix",
                 command=self._run_correlation,
                 bg="#FF9800", fg="white",
                 font=("Arial", 10, "bold"),
                 width=20, height=2).pack(side=tk.LEFT, padx=5)

        # Make scrollable
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_multivariate_tab(self, notebook):
        """Create multivariate analysis tab"""
        frame = tk.Frame(notebook)
        notebook.add(frame, text="🌀 Multivariate")

        content = tk.Frame(frame)
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        if TIER_2_AVAILABLE:
            tk.Label(content,
                    text="Multivariate Analysis",
                    font=("Arial", 14, "bold")).pack(anchor=tk.W, pady=(0, 10))

            # Analysis options
            options_frame = tk.LabelFrame(content, text="Analysis Type",
                                         font=("Arial", 10, "bold"),
                                         padx=10, pady=5)
            options_frame.pack(fill=tk.X, pady=5)

            self.analysis_type = tk.StringVar(value="pca")

            analyses = [
                ("Principal Component Analysis (PCA)", "pca"),
                ("Cluster Analysis (K-means)", "kmeans"),
                ("Discriminant Function Analysis", "lda"),
                ("Hierarchical Clustering", "hclust")
            ]

            for text, value in analyses:
                rb = tk.Radiobutton(options_frame, text=text,
                                   variable=self.analysis_type,
                                   value=value,
                                   font=("Arial", 9))
                rb.pack(anchor=tk.W, padx=10, pady=3)

            # Parameters
            param_frame = tk.Frame(content)
            param_frame.pack(fill=tk.X, pady=5)

            tk.Label(param_frame, text="Number of components/clusters:",
                    font=("Arial", 9)).pack(side=tk.LEFT)

            self.n_components = tk.IntVar(value=3)
            tk.Spinbox(param_frame, from_=2, to=10,
                      textvariable=self.n_components,
                      width=10).pack(side=tk.LEFT, padx=10)

            # Button
            btn_frame = tk.Frame(content)
            btn_frame.pack(pady=8)

            tk.Button(btn_frame, text="🚀 Run Analysis",
                     command=self._run_multivariate,
                     bg="#9C27B0", fg="white",
                     font=("Arial", 12, "bold"),
                     width=20, height=2).pack()
        else:
            # Show installation instructions
            install_frame = tk.LabelFrame(content, text="Install Required Packages",
                                         font=("Arial", 10, "bold"),
                                         padx=8, pady=5)
            install_frame.pack(fill=tk.BOTH, expand=True, pady=8)

            tk.Label(install_frame,
                    text="Install scikit-learn for multivariate analysis:\n\n"
                         "Run in terminal:\n"
                         "pip install scikit-learn scipy pandas\n\n"
                         "Features include:\n"
                         "• Principal Component Analysis (PCA)\n"
                         "• K-means Clustering\n"
                         "• Discriminant Analysis\n"
                         "• Hierarchical Clustering",
                    font=("Arial", 10),
                    fg="gray",
                    justify=tk.LEFT,
                    padx=10, pady=5).pack()

    def _create_results_tab(self, notebook):
        """Create results display tab"""
        frame = tk.Frame(notebook)
        notebook.add(frame, text="📄 Results")

        self.results_text = scrolledtext.ScrolledText(frame,
                                                     wrap=tk.WORD,
                                                     font=("Courier", 10),
                                                     padx=8, pady=5)
        self.results_text.pack(fill=tk.BOTH, expand=True)

        # Results toolbar
        toolbar = tk.Frame(frame)
        toolbar.pack(fill=tk.X, pady=5, padx=10)

        tk.Button(toolbar, text="📋 Copy Results",
                 command=self._copy_results,
                 font=("Arial", 9)).pack(side=tk.LEFT, padx=5)

        tk.Button(toolbar, text="💾 Save to File",
                 command=self._save_results,
                 font=("Arial", 9)).pack(side=tk.LEFT, padx=5)

        tk.Button(toolbar, text="🧹 Clear",
                 command=self._clear_results,
                 font=("Arial", 9)).pack(side=tk.LEFT, padx=5)

    def _populate_numeric_vars(self):
        """Get numeric columns from samples"""
        self.numeric_vars = []
        if self.app.samples:
            sample = self.app.samples[0]
            for key in sample.keys():
                if any(x in key.lower() for x in ['ppm', 'ratio', 'thickness', 'oxide', 'wt%']):
                    if any(safe_float(s.get(key)) is not None for s in self.app.samples):
                        self.numeric_vars.append(key)

        # If no numeric vars found, add defaults
        if not self.numeric_vars:
            self.numeric_vars = ["Zr_ppm", "Nb_ppm", "Ba_ppm", "Cr_ppm", "Ni_ppm",
                               "Wall_Thickness_mm", "Zr_Nb_Ratio", "Cr_Ni_Ratio"]

    def _select_all_vars(self):
        """Select all variables"""
        for var, cb in self.var_checkboxes.items():
            cb.set(True)

    def _run_descriptive_stats(self):
        """Run descriptive statistics"""
        if not self.app.samples:
            messagebox.showwarning("No Data", "No samples to analyze.", parent=self.window)
            return

        selected_vars = [var for var, cb in self.var_checkboxes.items() if cb.get()]
        if not selected_vars:
            selected_vars = self.numeric_vars[:5]  # Use first 5 if none selected

        results = "=" * 80 + "\n"
        results += "DESCRIPTIVE STATISTICS\n"
        results += "=" * 80 + "\n\n"
        results += f"Total samples: {len(self.app.samples)}\n\n"

        for var in selected_vars:
            values = [safe_float(s.get(var)) for s in self.app.samples]
            values = [v for v in values if v is not None]

            if not values:
                results += f"{var}: No valid data\n\n"
                continue

            try:
                mean_val = statistics.mean(values)
                median_val = statistics.median(values)
                if len(values) > 1:
                    std_val = statistics.stdev(values)
                else:
                    std_val = 0
                min_val = min(values)
                max_val = max(values)
                count = len(values)

                results += f"{var}:\n"
                results += f"  N = {count}\n"
                results += f"  Mean = {mean_val:.3f}\n"
                results += f"  Median = {median_val:.3f}\n"
                results += f"  Std Dev = {std_val:.3f}\n"
                results += f"  Min = {min_val:.3f}\n"
                results += f"  Max = {max_val:.3f}\n"
                results += f"  Range = {max_val - min_val:.3f}\n\n"
            except Exception as e:
                results += f"{var}: Error calculating - {str(e)}\n\n"

        self._display_results(results)

    def _run_anova_ttest(self):
        """Run ANOVA or t-test"""
        if not HAS_SCIPY:
            messagebox.showerror("scipy Required",
                               "Install scipy for statistical tests:\n\n"
                               "pip install scipy",
                               parent=self.window)
            return

        selected_vars = [var for var, cb in self.var_checkboxes.items() if cb.get()]
        if not selected_vars:
            selected_vars = self.numeric_vars[:2]

        group_var = self.group_var.get()
        groups = {}
        for sample in self.app.samples:
            group = sample.get(group_var)
            if group:
                if group not in groups:
                    groups[group] = []
                groups[group].append(sample)

        if len(groups) < 2:
            messagebox.showwarning("Not Enough Groups",
                                 f"Need at least 2 groups in {group_var}",
                                 parent=self.window)
            return

        results = "=" * 80 + "\n"
        results += f"GROUP COMPARISONS (by {group_var})\n"
        results += "=" * 80 + "\n\n"

        for var in selected_vars:
            results += f"Variable: {var}\n"

            # Prepare data for ANOVA
            group_data = []
            group_names = []
            for group_name, group_samples in groups.items():
                values = [safe_float(s.get(var)) for s in group_samples]
                values = [v for v in values if v is not None]
                if len(values) >= 2:
                    group_data.append(values)
                    group_names.append(group_name)

            if len(group_data) >= 2:
                # One-way ANOVA
                try:
                    f_stat, p_value = scipy.stats.f_oneway(*group_data)

                    results += f"  One-way ANOVA:\n"
                    total_n = sum(len(g) for g in group_data)
                    results += f"    F({len(group_data)-1}, {total_n-len(group_data)}) = {f_stat:.4f}\n"
                    results += f"    p-value = {p_value:.4f}\n"

                    if p_value < 0.05:
                        results += "    * Significant difference between groups (p < 0.05)\n"
                    else:
                        results += "    * No significant difference between groups\n"

                    # Group means
                    results += "\n  Group means:\n"
                    for name, data in zip(group_names, group_data):
                        mean_val = statistics.mean(data)
                        std_val = statistics.stdev(data) if len(data) > 1 else 0
                        results += f"    {name}: {mean_val:.3f} ± {std_val:.3f} (n={len(data)})\n"

                except Exception as e:
                    results += f"  ANOVA failed: {str(e)}\n"

            results += "\n"

        self._display_results(results)

    def _run_correlation(self):
        """Run correlation analysis"""
        if not HAS_SCIPY:
            messagebox.showerror("scipy Required",
                               "Install scipy for correlation analysis:\n\n"
                               "pip install scipy",
                               parent=self.window)
            return

        selected_vars = [var for var, cb in self.var_checkboxes.items() if cb.get()]
        if len(selected_vars) < 2:
            selected_vars = self.numeric_vars[:5]

        # Extract data
        data = {}
        for var in selected_vars:
            values = [safe_float(s.get(var)) for s in self.app.samples]
            values = [v for v in values if v is not None]
            if len(values) > 1:
                data[var] = values

        if len(data) < 2:
            messagebox.showwarning("Not Enough Data",
                                 "Need at least 2 variables with numeric data",
                                 parent=self.window)
            return

        results = "=" * 80 + "\n"
        results += "CORRELATION MATRIX\n"
        results += "=" * 80 + "\n\n"

        # Create correlation matrix
        import numpy as np

        vars_list = list(data.keys())
        n = len(vars_list)

        results += "Pearson Correlation Coefficients:\n\n"
        results += f"{'Variable':20s}" + "".join([f"{v:12s}" for v in vars_list]) + "\n"
        results += "-" * (20 + 12*n) + "\n"

        for i, var1 in enumerate(vars_list):
            results += f"{var1:20s}"
            for j, var2 in enumerate(vars_list):
                if i == j:
                    results += f"{'1.000':12s}"
                elif i > j:
                    # Calculate correlation
                    values1 = data[var1][:min(len(data[var1]), len(data[var2]))]
                    values2 = data[var2][:min(len(data[var1]), len(data[var2]))]

                    if len(values1) >= 3:
                        corr, p_value = scipy.stats.pearsonr(values1, values2)
                        results += f"{corr:12.3f}"
                    else:
                        results += f"{'---':12s}"
                else:
                    results += f"{'':12s}"
            results += "\n"

        self._display_results(results)

    def _run_multivariate(self):
        """Run multivariate analysis"""
        if not TIER_2_AVAILABLE:
            messagebox.showerror("scikit-learn Required",
                               "Install scikit-learn for multivariate analysis:\n\n"
                               "pip install scikit-learn scipy pandas",
                               parent=self.window)
            return

        # This would contain your multivariate analysis code
        # For now, just show a message
        results = "=" * 80 + "\n"
        results += "MULTIVARIATE ANALYSIS\n"
        results += "=" * 80 + "\n\n"
        results += "Analysis type: " + self.analysis_type.get() + "\n"
        results += "Number of components: " + str(self.n_components.get()) + "\n\n"
        results += "Multivariate analysis would run here.\n"
        results += "This requires valid sample data with numeric variables."

        self._display_results(results)

    def _display_results(self, text):
        """Display results in results tab"""
        if hasattr(self, 'results_text'):
            self.results_text.delete('1.0', tk.END)
            self.results_text.insert('1.0', text)
            # Switch to results tab
            if hasattr(self, 'window'):
                notebook = self.window.winfo_children()[2]  # Notebook is 3rd child
                notebook.select(2)  # Switch to results tab (index 2)

    def _copy_results(self):
        """Copy results to clipboard"""
        if hasattr(self, 'results_text'):
            text = self.results_text.get('1.0', tk.END)
            self.window.clipboard_clear()
            self.window.clipboard_append(text)
            messagebox.showinfo("Copied", "Results copied to clipboard", parent=self.window)

    def _save_results(self):
        """Save results to file"""
        if hasattr(self, 'results_text'):
            text = self.results_text.get('1.0', tk.END)
            path = filedialog.asksaveasfilename(
                title="Save Results",
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                parent=self.window
            )
            if path:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(text)
                messagebox.showinfo("Saved", f"Results saved to:\n{path}", parent=self.window)

    def _clear_results(self):
        """Clear results"""
        if hasattr(self, 'results_text'):
            self.results_text.delete('1.0', tk.END)
