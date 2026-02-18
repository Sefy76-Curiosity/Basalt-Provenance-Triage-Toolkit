"""
Missingno Plotter - UI Add-on
Visualize missing data patterns in geochemical dataset

Author: Sefy Levy
Category: UI Add-on
"""
import tkinter as tk
from tkinter import ttk

HAS_MISSINGNO = False
HAS_MATPLOTLIB = False
try:
    import matplotlib
    matplotlib.use('TkAgg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import missingno as msno
    import pandas as pd
    import numpy as np
    HAS_MISSINGNO = True
    HAS_MATPLOTLIB = True
except ImportError:
    pass

PLUGIN_INFO = {
    'id': 'missingno_plotter',
    'name': 'Missing Data Visualizer',
    'category': 'add-ons',
    'icon': '🔍',
    'version': '2.0',
    'requires': ['missingno', 'matplotlib', 'pandas', 'numpy'],
    'description': 'Visualize missing data patterns and data quality',
    'exclusive_group': 'plotter'
}

class MissingnoPlotterPlugin:
    """Missingno plotter add-on"""
    def __init__(self, parent_app):
        self.app = parent_app

def register_plugin(parent_app):
    """Register this add-on and return an instance."""
    return MissingnoPlotterPlugin(parent_app)

def plot_missingno(frame, samples):
    """Draw missing data visualizations inside tkinter frame."""
    if not HAS_MISSINGNO:
        for widget in frame.winfo_children():
            widget.destroy()
        label = tk.Label(frame, text="Missingno not available\nInstall with: pip install missingno matplotlib pandas numpy",
                         fg="red", font=("Arial", 12))
        label.pack(expand=True)
        return

    # Clear frame
    for widget in frame.winfo_children():
        widget.destroy()

    if not samples:
        label = tk.Label(frame, text="No data to analyze", font=("Arial", 12))
        label.pack(expand=True)
        return

    # Control panel
    control_frame = ttk.Frame(frame)
    control_frame.pack(fill=tk.X, pady=5)

    ttk.Label(control_frame, text="Plot Type:").pack(side=tk.LEFT, padx=5)
    plot_var = tk.StringVar(value="Matrix")
    plot_combo = ttk.Combobox(control_frame, textvariable=plot_var,
                              values=["Matrix", "Bar", "Heatmap", "Dendrogram"],
                              state='readonly', width=15)
    plot_combo.pack(side=tk.LEFT, padx=5)

    def update_plot():
        plot_missing(plot_var.get())

    ttk.Button(control_frame, text="Update", command=update_plot).pack(side=tk.LEFT, padx=10)

    # Frame for plot
    plot_frame = ttk.Frame(frame)
    plot_frame.pack(fill=tk.BOTH, expand=True, pady=5)

    def plot_missing(plot_type='Matrix'):
        # Clear plot frame
        for widget in plot_frame.winfo_children():
            widget.destroy()

        # Create DataFrame from samples
        data = []
        elements = ['Zr_ppm', 'Nb_ppm', 'Cr_ppm', 'Ni_ppm', 'Ba_ppm', 'Rb_ppm',
                   'SiO2', 'TiO2', 'Al2O3', 'Fe2O3', 'MgO', 'CaO', 'Na2O', 'K2O']

        for s in samples:
            row = {'Sample_ID': s.get('Sample_ID', 'Unknown')}
            for elem in elements:
                try:
                    val = float(s.get(elem, np.nan))
                    row[elem] = val if val > 0 else np.nan
                except:
                    row[elem] = np.nan
            data.append(row)

        df = pd.DataFrame(data)
        df.set_index('Sample_ID', inplace=True)

        # Create figure
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))

        # Generate missingno plot
        if plot_type == "Matrix":
            msno.matrix(df, ax=ax, fontsize=10, sparkline=True, figsize=(12, 8))
            ax.set_title('Missing Data Matrix\n(White = Missing, Black = Present)', fontsize=14)
        elif plot_type == "Bar":
            msno.bar(df, ax=ax, fontsize=10, figsize=(12, 8), color='steelblue')
            ax.set_title('Data Completeness by Element', fontsize=14)
            ax.set_ylabel('Data Present (%)')
        elif plot_type == "Heatmap":
            msno.heatmap(df, ax=ax, fontsize=10, figsize=(12, 8), cmap='RdBu')
            ax.set_title('Missing Data Correlation Heatmap\n(How missingness correlates between elements)', fontsize=14)
        elif plot_type == "Dendrogram":
            msno.dendrogram(df, ax=ax, fontsize=10, figsize=(12, 8))
            ax.set_title('Hierarchical Clustering of Missing Patterns', fontsize=14)

        # Add summary statistics
        completeness = (1 - df.isnull().sum() / len(df)) * 100
        total_completeness = completeness.mean()

        fig.text(0.02, 0.02,
                f"Total Data Completeness: {total_completeness:.1f}%\n"
                f"Complete Samples: {len(df.dropna())} / {len(df)}\n"
                f"Elements with >80% data: {sum(completeness > 80)}/{len(completeness)}",
                fontsize=10, bbox=dict(boxstyle="round", facecolor='lightgray', alpha=0.8))

        fig.tight_layout()

        # Create canvas
        canvas = FigureCanvasTkAgg(fig, master=plot_frame)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        canvas.draw()

    # Initial plot
    plot_missing()

# Expose plot types
PLOT_TYPES = {
    "Missing Data Analysis": plot_missingno
}
