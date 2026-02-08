"""
Matplotlib Plotter - UI Add-on
High-quality plotting with matplotlib

Author: Sefy Levy
Category: UI Add-on
"""

import tkinter as tk
from tkinter import ttk, messagebox

HAS_MATPLOTLIB = False
try:
    import matplotlib
    matplotlib.use('TkAgg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    HAS_MATPLOTLIB = True
except ImportError:
    pass

PLUGIN_INFO = {
    'id': 'matplotlib_plotter',
    'name': 'Matplotlib Plotter (High Quality)',
    'category': 'add-on',
    'icon': '📊',
    'requires': ['matplotlib'],
    'description': 'High-quality scientific plots with matplotlib (exclusive plotter)',
    'exclusive_group': 'plotter'
}

class MatplotlibPlotterPlugin:
    """Matplotlib plotter add-on"""
    
    def __init__(self, parent_app):
        self.app = parent_app
        self.canvas = None
        self.figure = None
        
    def create_plot_frame(self, parent):
        """Create matplotlib plot in parent frame"""
        if not HAS_MATPLOTLIB:
            label = tk.Label(parent, text="Matplotlib not available\nInstall with: pip install matplotlib",
                           fg="red", font=("Arial", 12))
            label.pack(expand=True)
            return None
        
        # Create figure
        self.figure, axes = plt.subplots(2, 2, figsize=(10, 8))
        self.figure.tight_layout(pad=3.0)
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.figure, parent)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        return axes
    
    def plot(self, samples):
        """Update plots with sample data"""
        if not HAS_MATPLOTLIB or not self.figure:
            return
        
        # Clear all axes
        for ax in self.figure.axes:
            ax.clear()
        
        if not samples:
            self.canvas.draw()
            return
        
        axes = self.figure.axes
        
        # Extract data
        zr_nb = []
        cr_ni = []
        ba_rb = []
        
        for s in samples:
            try:
                zr = float(s.get('Zr_ppm', 0))
                nb = float(s.get('Nb_ppm', 1))
                cr = float(s.get('Cr_ppm', 0))
                ni = float(s.get('Ni_ppm', 1))
                ba = float(s.get('Ba_ppm', 0))
                rb = float(s.get('Rb_ppm', 1))
                
                if zr > 0 and nb > 0:
                    zr_nb.append(zr/nb)
                if cr > 0 and ni > 0:
                    cr_ni.append(cr/ni)
                if ba > 0 and rb > 0:
                    ba_rb.append(ba/rb)
            except:
                pass
        
        # Plot 1: Zr/Nb histogram
        if zr_nb:
            axes[0].hist(zr_nb, bins=20, color='steelblue', edgecolor='black')
            axes[0].set_xlabel('Zr/Nb Ratio')
            axes[0].set_ylabel('Frequency')
            axes[0].set_title('Zr/Nb Distribution')
            axes[0].grid(True, alpha=0.3)
        
        # Plot 2: Cr/Ni histogram
        if cr_ni:
            axes[1].hist(cr_ni, bins=20, color='coral', edgecolor='black')
            axes[1].set_xlabel('Cr/Ni Ratio')
            axes[1].set_ylabel('Frequency')
            axes[1].set_title('Cr/Ni Distribution')
            axes[1].grid(True, alpha=0.3)
        
        # Plot 3: Zr/Nb vs Cr/Ni scatter
        if zr_nb and cr_ni and len(zr_nb) == len(cr_ni):
            axes[2].scatter(zr_nb, cr_ni, alpha=0.6, s=50, c='green', edgecolors='black')
            axes[2].set_xlabel('Zr/Nb Ratio')
            axes[2].set_ylabel('Cr/Ni Ratio')
            axes[2].set_title('Provenance Discrimination')
            axes[2].grid(True, alpha=0.3)
        
        # Plot 4: Ba/Rb histogram
        if ba_rb:
            axes[3].hist(ba_rb, bins=20, color='purple', edgecolor='black')
            axes[3].set_xlabel('Ba/Rb Ratio')
            axes[3].set_ylabel('Frequency')
            axes[3].set_title('Ba/Rb Distribution')
            axes[3].grid(True, alpha=0.3)
        
        self.canvas.draw()

def register_plugin(parent_app):
    """Register this add-on"""
    return MatplotlibPlotterPlugin(parent_app)
