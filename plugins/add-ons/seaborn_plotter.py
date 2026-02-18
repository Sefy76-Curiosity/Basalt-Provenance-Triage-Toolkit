"""
Seaborn Plotter - UI Add-on
Statistical visualizations with beautiful defaults

Author: Sefy Levy
Category: UI Add-on
"""
import tkinter as tk

HAS_SEABORN = False
HAS_MATPLOTLIB = False
try:
    import matplotlib
    matplotlib.use('TkAgg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import seaborn as sns
    HAS_SEABORN = True
    HAS_MATPLOTLIB = True
except ImportError:
    pass

PLUGIN_INFO = {
    'id': 'seaborn_plotter',
    'name': 'Seaborn Statistical Plotter',
    'category': 'add-ons',
    'icon': '📈',
    'version': '2.0',
    'requires': ['seaborn', 'matplotlib'],
    'description': 'Beautiful statistical plots with seaborn',
    'exclusive_group': 'plotter'
}

class SeabornPlotterPlugin:
    """Seaborn plotter add-on"""
    def __init__(self, parent_app):
        self.app = parent_app

def register_plugin(parent_app):
    """Register this add-on and return an instance."""
    return SeabornPlotterPlugin(parent_app)

def plot_seaborn(frame, samples):
    """Draw seaborn plots inside the given tkinter frame."""
    if not HAS_SEABORN:
        for widget in frame.winfo_children():
            widget.destroy()
        label = tk.Label(frame, text="Seaborn not available\nInstall with: pip install seaborn matplotlib",
                         fg="red", font=("Arial", 12))
        label.pack(expand=True)
        return

    # Clear frame
    for widget in frame.winfo_children():
        widget.destroy()

    # Create figure
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('Archaeological Data Analysis - Seaborn', fontsize=16, fontweight='bold')
    fig.tight_layout(pad=4.0)

    # Create canvas
    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    if not samples:
        canvas.draw()
        return

    # Prepare data in pandas format
    data = []
    for s in samples:
        try:
            row = {
                'Sample_ID': s.get('Sample_ID', 'Unknown'),
                'Zr_ppm': float(s.get('Zr_ppm', 0)),
                'Nb_ppm': float(s.get('Nb_ppm', 1)),
                'Cr_ppm': float(s.get('Cr_ppm', 0)),
                'Ni_ppm': float(s.get('Ni_ppm', 1)),
                'Ba_ppm': float(s.get('Ba_ppm', 0)),
                'Rb_ppm': float(s.get('Rb_ppm', 1)),
                'TiO2': float(s.get('TiO2', 0)),
                'Fe2O3': float(s.get('Fe2O3', 0)),
                'MgO': float(s.get('MgO', 0)),
                'CaO': float(s.get('CaO', 0)),
                'Na2O': float(s.get('Na2O', 0)),
                'K2O': float(s.get('K2O', 0)),
                'SiO2': float(s.get('SiO2', 0)),
                'Al2O3': float(s.get('Al2O3', 0))
            }
            # Calculate ratios
            if row['Nb_ppm'] > 0:
                row['Zr/Nb'] = row['Zr_ppm'] / row['Nb_ppm']
            if row['Ni_ppm'] > 0:
                row['Cr/Ni'] = row['Cr_ppm'] / row['Ni_ppm']
            if row['Rb_ppm'] > 0:
                row['Ba/Rb'] = row['Ba_ppm'] / row['Rb_ppm']
            data.append(row)
        except:
            pass

    if not data:
        canvas.draw()
        return

    import pandas as pd
    df = pd.DataFrame(data)

    # Use seaborn styles
    sns.set_style("whitegrid")
    sns.set_palette("husl")

    # Plot 1: Distribution of Zr/Nb with KDE
    ax1 = axes[0, 0]
    if 'Zr/Nb' in df.columns:
        sns.histplot(data=df, x='Zr/Nb', kde=True, ax=ax1, color='steelblue')
        ax1.set_title('Zr/Nb Distribution with KDE')
        ax1.set_xlabel('Zr/Nb Ratio')

    # Plot 2: Pairplot-style scatter with regression
    ax2 = axes[0, 1]
    if 'Zr/Nb' in df.columns and 'Cr/Ni' in df.columns:
        sns.regplot(data=df, x='Zr/Nb', y='Cr/Ni', ax=ax2,
                   scatter_kws={'alpha':0.6, 's':80},
                   line_kws={'color':'red'})
        ax2.set_title('Zr/Nb vs Cr/Ni with Regression')
        ax2.set_xlabel('Zr/Nb Ratio')
        ax2.set_ylabel('Cr/Ni Ratio')

    # Plot 3: Violin plot of major elements
    ax3 = axes[1, 0]
    major_elements = ['SiO2', 'Al2O3', 'Fe2O3', 'MgO', 'CaO', 'Na2O', 'K2O']
    available = [elem for elem in major_elements if elem in df.columns]
    if available:
        df_melted = df[available].melt(var_name='Element', value_name='Weight %')
        sns.violinplot(data=df_melted, x='Element', y='Weight %', ax=ax3)
        ax3.set_title('Major Element Distribution')
        ax3.tick_params(axis='x', rotation=45)

    # Plot 4: Heatmap of correlations
    ax4 = axes[1, 1]
    numeric_cols = df.select_dtypes(include=['float64']).columns
    if len(numeric_cols) > 1:
        corr = df[numeric_cols].corr()
        sns.heatmap(corr, annot=True, fmt='.2f', cmap='coolwarm',
                   square=True, ax=ax4, cbar_kws={'shrink': 0.8})
        ax4.set_title('Element Correlation Matrix')

    canvas.draw()

# Expose plot types for dynamic plot tab
PLOT_TYPES = {
    "Seaborn Statistical Dashboard": plot_seaborn
}
