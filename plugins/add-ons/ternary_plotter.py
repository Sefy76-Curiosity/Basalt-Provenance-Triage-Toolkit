"""
Ternary Plotter - UI Add-on
Ternary diagrams for geochemical data

Author: Sefy Levy
Category: UI Add-on
"""
import tkinter as tk

HAS_MATPLOTLIB = False
HAS_TERNARY = False
try:
    import matplotlib
    matplotlib.use('TkAgg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import numpy as np
    # Try to import python-ternary
    import ternary
    HAS_TERNARY = True
    HAS_MATPLOTLIB = True
except ImportError:
    # Fallback to matplotlib-based ternary
    HAS_MATPLOTLIB = True
    pass

PLUGIN_INFO = {
    'id': 'ternary_plotter',
    'name': 'Ternary Diagram Plotter',
    'category': 'add-on',
    'icon': '🔺',
    'version': '2.0',
    'requires': ['matplotlib', 'numpy'],
    'description': 'Ternary diagrams for geochemical classification',
    'exclusive_group': 'plotter'
}

class TernaryPlotterPlugin:
    """Ternary plotter add-on"""
    def __init__(self, parent_app):
        self.app = parent_app

def register_plugin(parent_app):
    """Register this add-on and return an instance."""
    return TernaryPlotterPlugin(parent_app)

def plot_ternary(frame, samples):
    """Draw ternary diagrams inside tkinter frame."""
    if not HAS_MATPLOTLIB:
        for widget in frame.winfo_children():
            widget.destroy()
        label = tk.Label(frame, text="Matplotlib not available\nInstall with: pip install matplotlib numpy",
                         fg="red", font=("Arial", 12))
        label.pack(expand=True)
        return

    # Clear frame
    for widget in frame.winfo_children():
        widget.destroy()

    if not samples:
        label = tk.Label(frame, text="No data to plot", font=("Arial", 12))
        label.pack(expand=True)
        return

    # Create figure with 2 ternary diagrams
    fig = plt.figure(figsize=(12, 10))

    if HAS_TERNARY:
        # Use python-ternary library for proper ternary plots
        fig, tax = ternary.figure(ax=fig.add_subplot(2, 2, 1, projection='ternary'))
        tax2, ax2 = ternary.figure(ax=fig.add_subplot(2, 2, 2, projection='ternary'))
        ax3 = fig.add_subplot(2, 2, 3)
        ax4 = fig.add_subplot(2, 2, 4)
    else:
        # Fallback to 4 regular subplots
        ax1 = fig.add_subplot(2, 2, 1)
        ax2 = fig.add_subplot(2, 2, 2)
        ax3 = fig.add_subplot(2, 2, 3)
        ax4 = fig.add_subplot(2, 2, 4)

    fig.suptitle('Geochemical Ternary Diagrams', fontsize=14, fontweight='bold')
    fig.tight_layout(pad=4.0)

    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # Extract data for ternary plots
    ternary_data = []
    for s in samples:
        try:
            # For QFL diagram (Quartz-Feldspar-Lithics) - sandstone classification
            q = float(s.get('Quartz', s.get('SiO2', 0)))
            f = float(s.get('Feldspar', s.get('Al2O3', 0)))
            l = float(s.get('Lithics', s.get('MgO', 0)))

            # For ACF diagram (metamorphic)
            a = float(s.get('Al2O3', 0))
            c = float(s.get('CaO', 0))
            f_meta = float(s.get('Fe2O3', 0)) + float(s.get('MgO', 0))

            # Normalize to 100%
            total1 = q + f + l
            total2 = a + c + f_meta

            if total1 > 0:
                ternary_data.append({
                    'Q': q/total1 * 100,
                    'F': f/total1 * 100,
                    'L': l/total1 * 100,
                    'Sample': s.get('Sample_ID', 'Unknown')
                })

            if total2 > 0:
                ternary_data.append({
                    'A': a/total2 * 100,
                    'C': c/total2 * 100,
                    'F_meta': f_meta/total2 * 100,
                    'Sample': s.get('Sample_ID', 'Unknown')
                })
        except:
            continue

    if not ternary_data and HAS_TERNARY:
        canvas.draw()
        return

    if HAS_TERNARY:
        # Plot QFL diagram
        tax.scatter([(d['Q'], d['F'], d['L']) for d in ternary_data if 'Q' in d],
                   marker='o', color='blue', alpha=0.7, label='Samples')
        tax.left_axis_label("Quartz (Q)", fontsize=10)
        tax.right_axis_label("Feldspar (F)", fontsize=10)
        tax.bottom_axis_label("Lithics (L)", fontsize=10)
        tax.set_title("QFL Diagram - Sandstone Classification", fontsize=12)
        tax.legend()
        tax.boundary(linewidth=1.5)
        tax.gridlines(multiple=10, color='gray', alpha=0.3)

        # Plot ACF diagram
        tax2.scatter([(d['A'], d['C'], d['F_meta']) for d in ternary_data if 'A' in d],
                    marker='s', color='red', alpha=0.7, label='Samples')
        tax2.left_axis_label("Al2O3 (A)", fontsize=10)
        tax2.right_axis_label("CaO (C)", fontsize=10)
        tax2.bottom_axis_label("Fe2O3+MgO (F)", fontsize=10)
        tax2.set_title("ACF Diagram - Metamorphic Facies", fontsize=12)
        tax2.legend()
        tax2.boundary(linewidth=1.5)
        tax2.gridlines(multiple=10, color='gray', alpha=0.3)
    else:
        # Fallback: 2D projections
        q_values = [d['Q'] for d in ternary_data if 'Q' in d]
        f_values = [d['F'] for d in ternary_data if 'F' in d]
        if q_values and f_values:
            ax1.scatter(q_values, f_values, alpha=0.6, s=50, c='blue')
            ax1.set_xlabel('Quartz %')
            ax1.set_ylabel('Feldspar %')
            ax1.set_title('Q-F Projection')
            ax1.grid(True, alpha=0.3)

        a_values = [d['A'] for d in ternary_data if 'A' in d]
        c_values = [d['C'] for d in ternary_data if 'C' in d]
        if a_values and c_values:
            ax2.scatter(a_values, c_values, alpha=0.6, s=50, c='red')
            ax2.set_xlabel('Al2O3 %')
            ax2.set_ylabel('CaO %')
            ax2.set_title('A-C Projection')
            ax2.grid(True, alpha=0.3)

    # Additional plots in bottom row
    # TAS Diagram (Total Alkali vs Silica)
    tas_data = []
    for s in samples:
        try:
            sio2 = float(s.get('SiO2', 0))
            na2o = float(s.get('Na2O', 0))
            k2o = float(s.get('K2O', 0))
            if sio2 > 0:
                tas_data.append({
                    'SiO2': sio2,
                    'Na2O+K2O': na2o + k2o,
                    'Sample': s.get('Sample_ID', 'Unknown')
                })
        except:
            continue

    if tas_data:
        ax3.scatter([d['SiO2'] for d in tas_data],
                   [d['Na2O+K2O'] for d in tas_data],
                   alpha=0.6, s=50, c='green', edgecolors='black')

        # Add TAS classification fields
        ax3.axvline(x=45, color='gray', linestyle='--', alpha=0.5)
        ax3.axvline(x=52, color='gray', linestyle='--', alpha=0.5)
        ax3.axvline(x=63, color='gray', linestyle='--', alpha=0.5)
        ax3.axvline(x=69, color='gray', linestyle='--', alpha=0.5)

        ax3.text(48, 15, 'Basic', rotation=90, alpha=0.5)
        ax3.text(57, 15, 'Intermediate', rotation=90, alpha=0.5)
        ax3.text(66, 15, 'Acidic', rotation=90, alpha=0.5)

        ax3.set_xlabel('SiO2 (wt%)')
        ax3.set_ylabel('Na2O + K2O (wt%)')
        ax3.set_title('TAS Diagram - Volcanic Rock Classification')
        ax3.grid(True, alpha=0.3)

    # Harker Diagram
    harker_data = []
    for s in samples:
        try:
            sio2 = float(s.get('SiO2', 0))
            tio2 = float(s.get('TiO2', 0))
            fe2o3 = float(s.get('Fe2O3', 0))
            mgo = float(s.get('MgO', 0))
            if sio2 > 0:
                harker_data.append({
                    'SiO2': sio2,
                    'TiO2': tio2,
                    'Fe2O3': fe2o3,
                    'MgO': mgo
                })
        except:
            continue

    if harker_data:
        for element, color in [('TiO2', 'purple'), ('Fe2O3', 'red'), ('MgO', 'green')]:
            values = [d[element] for d in harker_data if d[element] > 0]
            if values:
                ax4.scatter([d['SiO2'] for d in harker_data if d[element] > 0],
                           values, alpha=0.5, s=30, label=element, color=color)

        ax4.set_xlabel('SiO2 (wt%)')
        ax4.set_ylabel('Oxide (wt%)')
        ax4.set_title('Harker Variation Diagram')
        ax4.legend()
        ax4.grid(True, alpha=0.3)

    canvas.draw()

# Expose plot types
PLOT_TYPES = {
    "Ternary Diagrams (Geochemistry)": plot_ternary
}
