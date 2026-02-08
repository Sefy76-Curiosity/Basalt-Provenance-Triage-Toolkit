"""
Spider Diagrams Plugin for Basalt Provenance Toolkit
Provides multi-element normalized spider/REE diagrams

Author: Sefy Levy
License: CC BY-NC-SA 4.0
"""
PLUGIN_INFO = {
      "category": "software",
    "id": "spider_diagrams",
    "name": "Spider/REE Diagrams",
    "description": "Multi-element primitive mantle & chondrite-normalized plots",
    "icon": "🕸️",
    "version": "1.0",
    "requires": ["matplotlib", "numpy"],
    "author": "Sefy Levy"
}



import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    HAS_REQUIREMENTS = True
except ImportError as e:
    HAS_REQUIREMENTS = False
    IMPORT_ERROR = str(e)


class SpiderDiagramsPlugin:
    """Plugin for spider/REE diagrams"""
    
    # Primitive mantle normalization values (McDonough & Sun, 1995)
    PRIMITIVE_MANTLE = {
        'Rb': 0.6,
        'Ba': 6.6,
        'Nb': 0.658,
        'Zr': 10.5,
        'Ni': 1960,
        'Cr': 2625
    }
    
    def __init__(self, main_app):
        """Initialize plugin"""
        self.app = main_app
        self.window = None
    
    def open_spider_window(self):
        """Open spider diagram interface"""
        if not HAS_REQUIREMENTS:
            messagebox.showerror(
                "Missing Dependencies",
                f"Spider Diagrams requires matplotlib:\n\n"
                f"Error: {IMPORT_ERROR}\n\n"
                f"Install with:\n"
                f"pip install matplotlib numpy"
            )
            return
        
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return
        
        self.window = tk.Toplevel(self.app.root)
        self.window.title("Spider / Multi-Element Diagrams")
        self.window.geometry("800x580")
        
        # Create interface
        self._create_spider_interface()
    
    def _create_spider_interface(self):
        """Create the spider diagram interface"""
        # Controls at top
        controls = tk.Frame(self.window, relief=tk.RAISED, borderwidth=2)
        controls.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        tk.Label(controls,
                text="Multi-Element Spider Diagram",
                font=("Arial", 14, "bold")).pack(anchor=tk.W, padx=10, pady=5)
        
        tk.Label(controls,
                text="Normalized multi-element patterns for geochemical fingerprinting",
                font=("Arial", 9), fg="gray").pack(anchor=tk.W, padx=10)
        
        # Options
        options_frame = tk.Frame(controls)
        options_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(options_frame, text="Normalization:",
                font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=5)
        
        self.norm_type = tk.StringVar(value="Primitive Mantle")
        norm_options = ["Primitive Mantle", "Absolute Values (No Normalization)"]
        ttk.Combobox(options_frame, textvariable=self.norm_type,
                    values=norm_options, width=30, state="readonly",
                    font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        
        self.show_legend = tk.BooleanVar(value=True)
        tk.Checkbutton(options_frame, text="Show legend",
                      variable=self.show_legend,
                      font=("Arial", 9)).pack(side=tk.LEFT, padx=10)
        
        # Sample selection
        sample_frame = tk.Frame(controls)
        sample_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(sample_frame, text="Display:",
                font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=5)
        
        self.display_mode = tk.StringVar(value="All Samples")
        display_options = ["All Samples", "By Classification", "Selected Samples"]
        ttk.Combobox(sample_frame, textvariable=self.display_mode,
                    values=display_options, width=20, state="readonly",
                    font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        
        # Generate button
        tk.Button(controls, text="▶ Generate Spider Diagram",
                 command=self._generate_spider,
                 bg="#673AB7", fg="white",
                 font=("Arial", 11, "bold"),
                 width=25, height=2,
                 cursor="hand2").pack(pady=5)
        
        # Plot frame
        self.plot_frame = tk.Frame(self.window, relief=tk.SUNKEN, borderwidth=2)
        self.plot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        tk.Label(self.plot_frame,
                text="👆 Configure options and click 'Generate Spider Diagram'",
                font=("Arial", 12), fg="gray").pack(expand=True)
    
    def _generate_spider(self):
        """Generate the spider diagram"""
        samples = self.app.samples
        
        if not samples:
            messagebox.showwarning("No Data", "No samples available to plot")
            return
        
        # Elements to plot (in order for spider diagram)
        elements = ['Rb', 'Ba', 'Nb', 'Zr', 'Cr', 'Ni']
        element_labels = elements
        
        # Collect data
        sample_data = {}
        
        for sample in samples:
            sample_id = sample.get('Sample_ID', 'Unknown')
            classification = sample.get('Final_Classification', 'Unclassified')
            
            values = []
            valid = False
            
            for elem in elements:
                try:
                    val = float(sample.get(f'{elem}_ppm', 0) or 0)
                    
                    # Normalize if requested
                    if self.norm_type.get() == "Primitive Mantle" and elem in self.PRIMITIVE_MANTLE:
                        if self.PRIMITIVE_MANTLE[elem] > 0:
                            val = val / self.PRIMITIVE_MANTLE[elem]
                    
                    values.append(val if val > 0 else None)
                    if val > 0:
                        valid = True
                except (ValueError, TypeError):
                    values.append(None)
            
            if valid:
                sample_data[sample_id] = {
                    'values': values,
                    'classification': classification
                }
        
        if not sample_data:
            messagebox.showwarning("No Data", "No valid geochemical data found")
            return
        
        # Clear plot frame
        for widget in self.plot_frame.winfo_children():
            widget.destroy()
        
        # Create plot
        fig, ax = plt.subplots(figsize=(12, 7))
        
        # Color map by classification
        classifications = set(d['classification'] for d in sample_data.values())
        colors = plt.cm.tab10(np.linspace(0, 1, len(classifications)))
        color_map = dict(zip(classifications, colors))
        
        # Plot each sample
        x_positions = np.arange(len(elements))
        
        for sample_id, data in sample_data.items():
            color = color_map[data['classification']]
            
            # Plot line connecting points
            valid_x = []
            valid_y = []
            for i, val in enumerate(data['values']):
                if val is not None:
                    valid_x.append(x_positions[i])
                    valid_y.append(val)
            
            if valid_x:
                ax.plot(valid_x, valid_y, marker='o', linewidth=1.5,
                       markersize=6, alpha=0.7, color=color,
                       label=f"{sample_id} ({data['classification']})")
        
        # Formatting
        ax.set_xticks(x_positions)
        ax.set_xticklabels(element_labels, rotation=0, fontsize=11)
        
        if self.norm_type.get() == "Primitive Mantle":
            ax.set_ylabel('Concentration / Primitive Mantle', fontsize=12, fontweight='bold')
            ax.set_yscale('log')
            ax.set_title('Primitive Mantle-Normalized Multi-Element Diagram',
                        fontsize=14, fontweight='bold')
        else:
            ax.set_ylabel('Concentration (ppm)', fontsize=12, fontweight='bold')
            ax.set_title('Multi-Element Concentration Diagram',
                        fontsize=14, fontweight='bold')
        
        ax.set_xlabel('Element', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
        
        # Legend
        if self.show_legend.get() and len(sample_data) <= 20:
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left',
                     fontsize=8, framealpha=0.9)
        elif len(sample_data) > 20:
            # Too many samples - show classification legend only
            handles = [plt.Line2D([0], [0], color=color_map[cls], linewidth=2, label=cls)
                      for cls in classifications]
            ax.legend(handles=handles, bbox_to_anchor=(1.05, 1), loc='upper left',
                     fontsize=9, title='Classification')
        
        fig.tight_layout()
        
        # Embed
        canvas = FigureCanvasTkAgg(fig, self.plot_frame)
        canvas.draw()
        toolbar = NavigationToolbar2Tk(canvas, self.plot_frame)
        toolbar.update()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
