"""
Ternary Diagrams Plugin for Basalt Provenance Toolkit
Provides AFM and other ternary plots for igneous petrology

Author: Sefy Levy
License: CC BY-NC-SA 4.0
"""

PLUGIN_INFO = {
      "category": "software",
    "id": "ternary_diagrams",
    "name": "Ternary Diagrams",
    "description": "AFM and other ternary plots (requires mpltern)",
    "icon": "🔺",
    "version": "1.0",
    "requires": ["mpltern", "matplotlib", "numpy"],
    "author": "Sefy Levy"
}

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# Conditional imports
try:
    import mpltern
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    import numpy as np
    HAS_REQUIREMENTS = True
except ImportError as e:
    HAS_REQUIREMENTS = False
    IMPORT_ERROR = str(e)


def safe_float(value):
    """Safely convert value to float"""
    if value is None or value == '':
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


class TernaryDiagramsPlugin:
    """Plugin for ternary diagrams (AFM, etc.)"""
    
    def __init__(self, main_app):
        """Initialize plugin with reference to main app"""
        self.app = main_app
        self.window = None
    
    def open_ternary_diagrams_window(self):
        """Open the ternary diagrams interface"""
        if not HAS_REQUIREMENTS:
            messagebox.showerror(
                "Missing Dependencies",
                f"Ternary Diagrams requires mpltern:\n\n"
                f"Error: {IMPORT_ERROR}\n\n"
                f"Install with:\n"
                f"pip install mpltern",
                parent=self.app.root
            )
            return
        
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return
        
        self.window = tk.Toplevel(self.app.root)
        self.window.title("Ternary Diagrams - Igneous Petrology")
        self.window.geometry("800x580")
        
        # Make window stay on top of main window
        self.window.transient(self.app.root)
        
        # Create notebook
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # AFM diagram tab
        self._create_afm_tab(notebook)
        
        # Help tab
        self._create_help_tab(notebook)
        
        # Bring window to front
        self.window.lift()
        self.window.focus_force()
    
    def _create_afm_tab(self, notebook):
        """Create AFM (Alkali-FeO-MgO) ternary diagram tab"""
        frame = tk.Frame(notebook)
        notebook.add(frame, text="AFM Diagram")
        
        # Controls
        controls = tk.Frame(frame, relief=tk.RAISED, borderwidth=2)
        controls.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        tk.Label(controls, 
                text="AFM Diagram - Alkali-FeO*-MgO Ternary",
                font=("Arial", 12, "bold")).pack(anchor=tk.W, padx=10, pady=5)
        
        tk.Label(controls, 
                text="Shows tholeiitic vs calc-alkaline magma evolution trends",
                font=("Arial", 9), fg="gray").pack(anchor=tk.W, padx=10)
        
        # Options
        options_frame = tk.Frame(controls)
        options_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(options_frame, text="FeO* calculation:", 
                font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=5)
        
        self.feo_method = tk.StringVar(value="total")
        tk.Radiobutton(options_frame, text="Total iron as FeO*", 
                      variable=self.feo_method, value="total").pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(options_frame, text="Use FeO if available", 
                      variable=self.feo_method, value="feo").pack(side=tk.LEFT, padx=5)
        
        tk.Button(controls, text="▶ Generate AFM Diagram",
                 command=lambda: self._plot_afm(plot_frame),
                 bg="#FF6F00", fg="white", 
                 font=("Arial", 10, "bold"),
                 width=20, height=2).pack(pady=5)
        
        # Plot frame
        plot_frame = tk.Frame(frame, relief=tk.SUNKEN, borderwidth=2)
        plot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        tk.Label(plot_frame, text="Click 'Generate AFM Diagram' to plot",
                font=("Arial", 10), fg="gray").pack(expand=True)
    
    def _plot_afm(self, parent):
        """Plot AFM ternary diagram"""
        # Clear previous plot
        for widget in parent.winfo_children():
            widget.destroy()
        
        # Get samples with major element data (Na2O, K2O, FeO/Fe2O3, MgO)
        samples_with_data = []
        for s in self.app.samples:
            na2o = safe_float(s.get('Na2O', ''))
            k2o = safe_float(s.get('K2O', ''))
            mgo = safe_float(s.get('MgO', ''))
            
            # Get FeO*
            if self.feo_method.get() == "feo":
                feo = safe_float(s.get('FeO', ''))
                if not feo:
                    # Fallback to Fe2O3
                    fe2o3 = safe_float(s.get('Fe2O3', ''))
                    if fe2o3:
                        feo = fe2o3 * 0.8998  # Convert Fe2O3 to FeO
            else:
                # Use total iron as Fe2O3, convert to FeO*
                fe2o3 = safe_float(s.get('Fe2O3', ''))
                if fe2o3:
                    feo = fe2o3 * 0.8998
                else:
                    feo = None
            
            if na2o is not None and k2o is not None and feo and mgo:
                samples_with_data.append({
                    'sample': s,
                    'alkali': na2o + k2o,
                    'feo': feo,
                    'mgo': mgo
                })
        
        if not samples_with_data:
            tk.Label(parent, 
                    text="⚠️ No samples with Na₂O, K₂O, FeO*, and MgO data.\n\n"
                         "AFM diagram requires major element data (wt%).",
                    font=("Arial", 11), fg="red").pack(expand=True)
            return
        
        # Create ternary figure
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(projection='ternary')
        
        # Extract data
        alkali = []
        feo = []
        mgo = []
        colors = []
        
        for data in samples_with_data:
            alkali.append(data['alkali'])
            feo.append(data['feo'])
            mgo.append(data['mgo'])
            
            classification = data['sample'].get('Final_Classification', 
                                              data['sample'].get('Auto_Classification', 'UNKNOWN'))
            color_map = {
                "EGYPTIAN (HADDADIN FLOW)": "blue",
                "EGYPTIAN (ALKALINE / EXOTIC)": "red",
                "SINAI / TRANSITIONAL": "gold",
                "SINAI OPHIOLITIC": "orange",
                "LOCAL LEVANTINE": "green",
                "HARRAT ASH SHAAM": "purple",
            }
            colors.append(color_map.get(classification, "gray"))
        
        # Plot samples
        ax.scatter(alkali, feo, mgo, c=colors, s=100, alpha=0.7,
                  edgecolors='black', linewidths=0.5, zorder=3)
        
        # Add tholeiitic vs calc-alkaline dividing line (Irvine & Baragar, 1971)
        # Approximate trend line
        t_alkali = np.linspace(0, 100, 100)
        t_feo = np.linspace(100, 0, 100)
        t_mgo = np.zeros(100)
        
        # Tholeiitic-calc-alkaline boundary (simplified)
        # This is an approximate curve, not exact
        boundary_alkali = [0, 10, 20, 30, 40, 50, 60, 70]
        boundary_feo = [100, 85, 70, 55, 40, 25, 12, 0]
        boundary_mgo = [0, 5, 10, 15, 20, 25, 28, 30]
        
        # Normalize to 100%
        total = [a+f+m for a,f,m in zip(boundary_alkali, boundary_feo, boundary_mgo)]
        boundary_alkali = [a/t*100 for a,t in zip(boundary_alkali, total)]
        boundary_feo = [f/t*100 for f,t in zip(boundary_feo, total)]
        boundary_mgo = [m/t*100 for m,t in zip(boundary_mgo, total)]
        
        ax.plot(boundary_alkali, boundary_feo, boundary_mgo, 
               'k--', linewidth=2, alpha=0.7, zorder=2)
        
        # Add field labels
        ax.text(20, 60, 20, 'Tholeiitic', fontsize=11, fontweight='bold',
               ha='center', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.6))
        ax.text(30, 40, 30, 'Calc-alkaline', fontsize=11, fontweight='bold',
               ha='center', bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.6))
        
        # Labels
        ax.set_tlabel('Alkali (Na₂O + K₂O)', fontsize=11, fontweight='bold')
        ax.set_llabel('FeO*', fontsize=11, fontweight='bold')
        ax.set_rlabel('MgO', fontsize=11, fontweight='bold')
        ax.set_title('AFM Diagram - Alkali-FeO*-MgO\n(Irvine & Baragar, 1971)', 
                    fontsize=13, fontweight='bold', pad=20)
        
        # Grid
        ax.grid()
        
        # Sample count
        ax.text(0.02, 0.98, f'n = {len(samples_with_data)} samples', 
               transform=ax.transAxes, fontsize=10,
               verticalalignment='top', 
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        
        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add toolbar
        toolbar_frame = tk.Frame(parent)
        toolbar_frame.pack(side=tk.BOTTOM, fill=tk.X)
        toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
        toolbar.update()
    
    def _create_help_tab(self, notebook):
        """Create help tab"""
        frame = tk.Frame(notebook)
        notebook.add(frame, text="❓ Help")
        
        text_frame = tk.Frame(frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text = tk.Text(text_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set,
                      font=("Arial", 10), padx=10, pady=5)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text.yview)
        
        help_text = """
TERNARY DIAGRAMS PLUGIN - USER GUIDE
═══════════════════════════════════════════════════════════════

WHAT ARE TERNARY DIAGRAMS?

Ternary diagrams plot three components (A, B, C) where A + B + C = 100%.
Each apex represents 100% of one component. Points inside the triangle
represent mixtures of the three components.

═══════════════════════════════════════════════════════════════

AFM DIAGRAM (Alkali-FeO*-MgO)

PURPOSE:
- Distinguishes tholeiitic from calc-alkaline magma series
- Shows magmatic evolution trends
- Standard in igneous petrology

COMPONENTS:
- A (top): Na₂O + K₂O (total alkali)
- F (left): FeO* (total iron as FeO)
- M (right): MgO

FIELDS:
- Tholeiitic: Iron enrichment trend (toward FeO corner)
- Calc-alkaline: Alkali enrichment trend (toward Alkali corner)

CITATION:
Irvine, T. N., & Baragar, W. R. A. (1971). A guide to the chemical 
classification of the common volcanic rocks. Canadian Journal of 
Earth Sciences, 8(5), 523-548.

═══════════════════════════════════════════════════════════════

REQUIREMENTS:

This plugin requires mpltern for ternary plotting:

    pip install mpltern

Also needs matplotlib and numpy (usually already installed).

═══════════════════════════════════════════════════════════════

DATA REQUIREMENTS:

AFM Diagram needs:
- Na₂O (wt%)
- K₂O (wt%)
- FeO* or Fe₂O₃ (wt%)
- MgO (wt%)

All values should be normalized major element data.

═══════════════════════════════════════════════════════════════

TIPS:

1. Use normalized major elements (sum to 100%)
2. FeO* = total iron expressed as FeO
3. If only Fe₂O₃ available, plugin converts automatically
4. Tholeiitic basalts are most common
5. Calc-alkaline trend suggests subduction influence

═══════════════════════════════════════════════════════════════

FUTURE ADDITIONS:

Other ternary diagrams may be added:
- Ti-Cr-Zr (tectonic discrimination)
- Cr-Al-Fe³⁺ (chromite classification)
- An-Ab-Or (feldspar ternary)

═══════════════════════════════════════════════════════════════
"""
        
        text.insert('1.0', help_text)
        text.config(state='disabled')


# Plugin interface for main app
def activate(main_app):
    """Called when plugin is loaded"""
    plugin = TernaryDiagramsPlugin(main_app)
    return plugin
