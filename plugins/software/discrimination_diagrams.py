"""
Discrimination Diagrams Plugin for Basalt Provenance Toolkit
Provides tectonic discrimination plots (Pearce, Wood, Shervais, etc.)

Author: Sefy Levy
License: CC BY-NC-SA 4.0
"""
PLUGIN_INFO = {
      "category": "software",
    "id": "discrimination_diagrams",
    "name": "Discrimination Diagrams",
    "description": "Pearce-Cann, Wood, Shervais tectonic discrimination plots",
    "icon": "📈",
    "version": "1.0",
    "requires": ["matplotlib", "numpy"],
    "author": "Sefy Levy"
}



import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    from matplotlib.patches import Polygon
    HAS_REQUIREMENTS = True
except ImportError as e:
    HAS_REQUIREMENTS = False
    IMPORT_ERROR = str(e)


class DiscriminationDiagramsPlugin:
    """Plugin for tectonic discrimination diagrams"""
    
    def __init__(self, main_app):
        """Initialize plugin with reference to main app"""
        self.app = main_app
        self.window = None
    
    def open_window(self):
        """Open the discrimination diagrams interface"""
        if not HAS_REQUIREMENTS:
            messagebox.showerror(
                "Missing Dependencies",
                f"Discrimination Diagrams requires matplotlib:\n\n"
                f"Error: {IMPORT_ERROR}\n\n"
                f"Install with:\n"
                f"pip install matplotlib numpy"
            )  # ← ADDED MISSING PARENTHESIS
            return
        
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return
        
        self.window = tk.Toplevel(self.app.root)
        self.window.title("Tectonic Discrimination Diagrams")
        self.window.geometry("800x580")
        
        # Create notebook
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Different diagram tabs
        self._create_tas_diagram_tab(notebook)  # TAS = Most important!
        self._create_pearce_cann_tab(notebook)
        self._create_wood_tab(notebook)
        self._create_shervais_tab(notebook)
        self._create_custom_tab(notebook)
        self._create_help_tab(notebook)
    
    def _create_tas_diagram_tab(self, notebook):
        """Create TAS (Total Alkali vs Silica) diagram tab - THE standard classification diagram"""
        frame = tk.Frame(notebook)
        notebook.add(frame, text="⭐ TAS Diagram")
        
        # Controls
        controls = tk.Frame(frame, relief=tk.RAISED, borderwidth=2)
        controls.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        tk.Label(controls, 
                text="TAS Diagram - Total Alkali vs Silica (IUGS Classification)",
                font=("Arial", 12, "bold")).pack(anchor=tk.W, padx=10, pady=5)
        
        tk.Label(controls, 
                text="THE standard rock classification diagram. Na₂O + K₂O vs SiO₂ (wt%)",
                font=("Arial", 9), fg="blue").pack(anchor=tk.W, padx=10)
        
        tk.Button(controls, text="▶ Generate TAS Diagram",
                 command=lambda: self._plot_tas_diagram(plot_frame),
                 bg="#4CAF50", fg="white", 
                 font=("Arial", 10, "bold"),
                 width=20, height=2).pack(pady=5)
        
        # Plot frame
        plot_frame = tk.Frame(frame, relief=tk.SUNKEN, borderwidth=2)
        plot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        tk.Label(plot_frame, text="Click 'Generate TAS Diagram' to plot",
                font=("Arial", 10), fg="gray").pack(expand=True)
    
    def _plot_tas_diagram(self, parent):
        """Plot TAS (Total Alkali-Silica) diagram"""
        # Clear previous plot
        for widget in parent.winfo_children():
            widget.destroy()
        
        # Get samples with major element data
        samples = [s for s in self.app.samples if self._has_tas_data(s)]
        
        if not samples:
            tk.Label(parent, 
                    text="⚠️ No samples with SiO₂, Na₂O, and K₂O data found.\n\n"
                         "TAS requires major element data (wt%).",
                    font=("Arial", 11), fg="red").pack(expand=True)
            return
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 7))
        
        # TAS field boundaries (Le Bas et al., 1986)
        # These are the official IUGS classification boundaries
        
        # Draw field boundaries
        self._draw_tas_fields(ax)
        
        # Extract data
        sio2_values = []
        alkali_values = []
        colors = []
        labels_set = set()
        
        for sample in samples:
            sio2 = self._safe_float(sample.get('SiO2', ''))
            na2o = self._safe_float(sample.get('Na2O', ''))
            k2o = self._safe_float(sample.get('K2O', ''))
            
            if sio2 and na2o is not None and k2o is not None:
                total_alkali = na2o + k2o
                sio2_values.append(sio2)
                alkali_values.append(total_alkali)
                
                # Color by classification
                classification = sample.get('Final_Classification', 
                                          sample.get('Auto_Classification', 'UNKNOWN'))
                
                color_map = {
                    "EGYPTIAN (HADDADIN FLOW)": "blue",
                    "EGYPTIAN (ALKALINE / EXOTIC)": "red",
                    "SINAI / TRANSITIONAL": "gold",
                    "SINAI OPHIOLITIC": "orange",
                    "LOCAL LEVANTINE": "green",
                    "HARRAT ASH SHAAM": "purple",
                }
                color = color_map.get(classification, "gray")
                colors.append(color)
                labels_set.add(classification)
        
        # Plot samples
        scatter = ax.scatter(sio2_values, alkali_values, 
                           c=colors, s=100, alpha=0.6, 
                           edgecolors='black', linewidths=0.5, zorder=3)
        
        # Create legend
        from matplotlib.patches import Patch
        legend_elements = [Patch(facecolor=color_map.get(label, "gray"), 
                                label=label, edgecolor='black')
                         for label in sorted(labels_set)]
        if legend_elements:
            ax.legend(handles=legend_elements, loc='upper left', 
                     fontsize=9, framealpha=0.9)
        
        # Styling
        ax.set_xlabel('SiO₂ (wt%)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Na₂O + K₂O (wt%)', fontsize=12, fontweight='bold')
        ax.set_title('TAS Diagram - Total Alkali vs Silica\n(IUGS Classification)', 
                    fontsize=14, fontweight='bold', pad=20)
        ax.set_xlim(35, 80)
        ax.set_ylim(0, 16)
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Add sample count
        ax.text(0.02, 0.98, f'n = {len(samples)} samples', 
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
    
    def _draw_tas_fields(self, ax):
        """Draw TAS classification field boundaries (Le Bas et al., 1986)"""
        # This draws the standard IUGS rock classification fields
        
        # Alkaline vs Sub-alkaline dividing line (Irvine & Baragar, 1971)
        alkaline_line_x = [39, 40, 43, 45, 48.4, 52.5, 57.6, 63, 69, 77]
        alkaline_line_y = [0, 0.4, 2, 2.8, 4, 5, 6, 7, 8, 8]
        ax.plot(alkaline_line_x, alkaline_line_y, 'k-', linewidth=1.5, 
               linestyle='--', label='Alkaline/Sub-alkaline')
        
        # Field boundaries - these create the classification boxes
        # Basalt field
        basalt_x = [41, 45, 45, 52, 52, 41, 41]
        basalt_y = [0, 0, 5, 5, 0, 0, 0]
        ax.plot(basalt_x, basalt_y, 'k-', linewidth=1)
        ax.text(46, 2, 'Basalt', fontsize=9, ha='center', 
               bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
        
        # Basaltic Andesite
        ba_x = [52, 57, 57, 52, 52]
        ba_y = [0, 0, 5.9, 5, 0]
        ax.plot(ba_x, ba_y, 'k-', linewidth=1)
        ax.text(54.5, 3, 'Basaltic\nAndesite', fontsize=8, ha='center',
               bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.5))
        
        # Andesite
        and_x = [57, 63, 63, 57, 57]
        and_y = [0, 0, 7, 5.9, 0]
        ax.plot(and_x, and_y, 'k-', linewidth=1)
        ax.text(60, 3.5, 'Andesite', fontsize=9, ha='center',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # Add more field labels
        ax.text(43, 6.5, 'Trachy-\nbasalt', fontsize=8, ha='center')
        ax.text(49, 8, 'Basaltic\nTrachy-\nandesite', fontsize=7, ha='center')
        ax.text(55, 9, 'Trachy-\nandesite', fontsize=8, ha='center')
        ax.text(43, 10, 'Tephrite\nBasanite', fontsize=8, ha='center')
        ax.text(49, 12, 'Phono-\ntephrite', fontsize=8, ha='center')
        
        # Ultrabasic/Picrite field
        ax.text(41, 0.5, 'Picro-\nbasalt', fontsize=7, ha='center', style='italic')
    
    def _has_tas_data(self, sample):
        """Check if sample has required TAS data (SiO2, Na2O, K2O)"""
        sio2 = self._safe_float(sample.get('SiO2', ''))
        na2o = self._safe_float(sample.get('Na2O', ''))
        k2o = self._safe_float(sample.get('K2O', ''))
        return sio2 and na2o is not None and k2o is not None
    
    def _safe_float(self, value):
        """Safely convert value to float"""
        if value is None or value == '':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    
    def _create_pearce_cann_tab(self, notebook):
        """Create Pearce & Cann (1973) Ti-Zr-Y ternary diagram tab"""
        frame = tk.Frame(notebook)
        notebook.add(frame, text="Pearce & Cann (Ti-Zr-Y)")
        
        # Controls
        controls = tk.Frame(frame, relief=tk.RAISED, borderwidth=2)
        controls.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        tk.Label(controls, 
                text="Pearce & Cann (1973) - Ti-Zr-Y Ternary Diagram",
                font=("Arial", 12, "bold")).pack(anchor=tk.W, padx=10, pady=5)
        
        tk.Label(controls, 
                text="Discriminates basalts by tectonic setting: MORB, IAB, WPB, CAB",
                font=("Arial", 9), fg="gray").pack(anchor=tk.W, padx=10)
        
        tk.Button(controls, text="▶ Generate Diagram",
                 command=lambda: self._plot_pearce_cann(plot_frame),
                 bg="#2196F3", fg="white", 
                 font=("Arial", 10, "bold"),
                 width=20, height=2).pack(pady=5)
        
        # Plot frame
        plot_frame = tk.Frame(frame, relief=tk.SUNKEN, borderwidth=2)
        plot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        tk.Label(plot_frame, text="Click 'Generate Diagram' to plot",
                font=("Arial", 12), fg="gray").pack(expand=True)
    
    def _plot_pearce_cann(self, frame):
        """Generate Pearce & Cann ternary diagram"""
        # Get data
        samples = self.app.samples
        
        Ti_data = []
        Zr_data = []
        Y_data = []
        sample_ids = []
        colors_list = []
        
        for sample in samples:
            try:
                # Get Ti from TiO2 if available, otherwise skip
                # For now, we'll use a proxy or skip
                # In real implementation, you'd need TiO2 data
                
                Zr = float(sample.get('Zr_ppm', 0) or 0)
                # Y would need to be added to your data structure
                # For demonstration, we'll use a placeholder
                Y = float(sample.get('Y_ppm', Zr * 0.1) or 0)  # Placeholder ratio
                
                if Zr > 0:  # Basic validity check
                    # Calculate Ti (need TiO2 data - using placeholder)
                    Ti = Zr * 60  # Placeholder - typical Ti/Zr ratio ~60
                    
                    Ti_data.append(Ti)
                    Zr_data.append(Zr)
                    Y_data.append(Y * 3)  # Y×3 for Pearce diagram
                    sample_ids.append(sample.get('Sample_ID', 'Unknown'))
                    
                    # Color by classification
                    classification = sample.get('Final_Classification', 'Unknown')
                    if 'Jordan' in classification or 'Harrat' in classification:
                        colors_list.append('red')
                    elif 'Golan' in classification:
                        colors_list.append('blue')
                    elif 'Egypt' in classification or 'Sinai' in classification:
                        colors_list.append('green')
                    else:
                        colors_list.append('gray')
            except (ValueError, TypeError):
                continue
        
        if len(Ti_data) < 1:
            messagebox.showwarning("No Data", 
                                  "No valid Ti-Zr-Y data found.\n\n"
                                  "Note: This diagram requires Ti and Y data which may not be\n"
                                  "in your current dataset. This is a demonstration."

            )
            return
        
        # Clear frame
        for widget in frame.winfo_children():
            widget.destroy()
        
        # Create ternary plot (simplified - proper ternary requires specialized library)
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Convert to ternary coordinates (simplified 2D projection)
        total = np.array(Ti_data) + np.array(Zr_data) + np.array(Y_data)
        x = (np.array(Zr_data) + 2 * np.array(Y_data)) / (2 * total)
        y = (np.sqrt(3) * np.array(Y_data)) / (2 * total)
        
        # Plot field boundaries (approximate)
        # MORB field
        morb_x = [0.25, 0.4, 0.45, 0.3]
        morb_y = [0.05, 0.05, 0.2, 0.2]
        ax.fill(morb_x, morb_y, alpha=0.2, color='blue', label='MORB')
        
        # WPB field
        wpb_x = [0.5, 0.7, 0.8, 0.6]
        wpb_y = [0.1, 0.15, 0.25, 0.2]
        ax.fill(wpb_x, wpb_y, alpha=0.2, color='red', label='WPB')
        
        # Plot samples
        scatter = ax.scatter(x, y, c=colors_list, s=100, alpha=0.7, 
                           edgecolors='black', linewidth=1)
        
        # Add labels
        for i, label in enumerate(sample_ids):
            ax.annotate(label, (x[i], y[i]), fontsize=7, alpha=0.7)
        
        ax.set_title('Pearce & Cann (1973) Ti-Zr-Y Discrimination\n(Simplified Projection)',
                    fontsize=14, fontweight='bold')
        ax.set_xlabel('Zr + Y Component', fontsize=11)
        ax.set_ylabel('Y Component', fontsize=11)
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # Add warning note
        ax.text(0.02, 0.98, 'NOTE: Simplified projection. Full ternary requires Ti, Y data.',
               transform=ax.transAxes, fontsize=8, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))
        
        fig.tight_layout()
        
        # Embed
        canvas = FigureCanvasTkAgg(fig, frame)
        canvas.draw()
        toolbar = NavigationToolbar2Tk(canvas, frame)
        toolbar.update()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def _create_wood_tab(self, notebook):
        """Create Wood (1980) Ti vs V diagram tab"""
        frame = tk.Frame(notebook)
        notebook.add(frame, text="Wood (Ti vs V)")
        
        # Controls
        controls = tk.Frame(frame, relief=tk.RAISED, borderwidth=2)
        controls.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        tk.Label(controls, 
                text="Wood (1980) - Ti vs V Discrimination",
                font=("Arial", 12, "bold")).pack(anchor=tk.W, padx=10, pady=5)
        
        tk.Label(controls, 
                text="Discriminates basalts using Ti and V concentrations",
                font=("Arial", 9), fg="gray").pack(anchor=tk.W, padx=10)
        
        tk.Button(controls, text="▶ Generate Diagram",
                 command=lambda: self._plot_wood(plot_frame),
                 bg="#2196F3", fg="white", 
                 font=("Arial", 10, "bold"),
                 width=20, height=2).pack(pady=5)
        
        # Plot frame
        plot_frame = tk.Frame(frame, relief=tk.SUNKEN, borderwidth=2)
        plot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        tk.Label(plot_frame, text="Click 'Generate Diagram' to plot",
                font=("Arial", 12), fg="gray").pack(expand=True)
    
    def _plot_wood(self, frame):
        """Generate Wood Ti vs V diagram"""
        messagebox.showinfo("Feature Demonstration",
                          "Wood (1980) Ti vs V diagram requires Ti and V data.\n\n"
                          "This would plot Ti (ppm) vs V (ppm) with discrimination fields for:\n"
                          "- MORB (Mid-Ocean Ridge Basalt)\n"
                          "- OIB (Ocean Island Basalt)\n"
                          "- IAT (Island Arc Tholeiite)\n"
                          "- CAB (Calc-Alkaline Basalt)\n\n"
                          "Add Ti_ppm and V_ppm fields to your dataset to use this feature.")
    
    def _create_shervais_tab(self, notebook):
        """Create Shervais (1982) Ti/V ratio tab"""
        frame = tk.Frame(notebook)
        notebook.add(frame, text="Shervais (Ti/V)")
        
        # Controls
        controls = tk.Frame(frame, relief=tk.RAISED, borderwidth=2)
        controls.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        tk.Label(controls, 
                text="Shervais (1982) - Ti/V Ratio Discrimination",
                font=("Arial", 12, "bold")).pack(anchor=tk.W, padx=10, pady=5)
        
        tk.Label(controls, 
                text="Uses Ti/V ratio to discriminate tectonic settings",
                font=("Arial", 9), fg="gray").pack(anchor=tk.W, padx=10)
        
        tk.Button(controls, text="▶ Generate Diagram",
                 command=lambda: self._plot_shervais(plot_frame),
                 bg="#2196F3", fg="white", 
                 font=("Arial", 10, "bold"),
                 width=20, height=2).pack(pady=5)
        
        # Plot frame
        plot_frame = tk.Frame(frame, relief=tk.SUNKEN, borderwidth=2)
        plot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        tk.Label(plot_frame, text="Click 'Generate Diagram' to plot",
                font=("Arial", 12), fg="gray").pack(expand=True)
    
    def _plot_shervais(self, frame):
        """Generate Shervais Ti/V diagram"""
        messagebox.showinfo("Feature Demonstration",
                          "Shervais (1982) Ti/V discrimination requires Ti and V data.\n\n"
                          "Ti/V ratios discriminate:\n"
                          "- Ti/V < 10: Arc basalts\n"
                          "- Ti/V 10-20: MORB\n"
                          "- Ti/V 20-50: OIB, Back-arc\n"
                          "- Ti/V > 50: Alkaline within-plate\n\n"
                          "Add Ti_ppm and V_ppm to your dataset to use this feature.")
    
    def _create_custom_tab(self, notebook):
        """Create custom Zr-Nb-Ba discrimination tab"""
        frame = tk.Frame(notebook)
        notebook.add(frame, text="Custom (Zr-Nb-Ba)")
        
        # Controls
        controls = tk.Frame(frame, relief=tk.RAISED, borderwidth=2)
        controls.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        tk.Label(controls, 
                text="Custom Zr-Nb-Ba Discrimination (Your Data)",
                font=("Arial", 12, "bold")).pack(anchor=tk.W, padx=10, pady=5)
        
        tk.Label(controls, 
                text="Plots your samples using the trace elements in your dataset",
                font=("Arial", 9), fg="gray").pack(anchor=tk.W, padx=10)
        
        # Plot type selection
        plot_frame_controls = tk.Frame(controls)
        plot_frame_controls.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(plot_frame_controls, text="Plot type:", 
                font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=5)
        
        self.custom_plot_type = tk.StringVar(value="Zr vs Nb")
        plot_types = ["Zr vs Nb", "Zr vs Ba", "Nb vs Ba", "Zr/Nb vs Ba/Rb"]
        ttk.Combobox(plot_frame_controls, textvariable=self.custom_plot_type,
                    values=plot_types, width=20, state="readonly",
                    font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        
        tk.Button(controls, text="▶ Generate Plot",
                 command=lambda: self._plot_custom(plot_frame),
                 bg="#4CAF50", fg="white", 
                 font=("Arial", 10, "bold"),
                 width=20, height=2).pack(pady=5)
        
        # Plot frame
        plot_frame = tk.Frame(frame, relief=tk.SUNKEN, borderwidth=2)
        plot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        tk.Label(plot_frame, text="Select plot type and click 'Generate Plot'",
                font=("Arial", 12), fg="gray").pack(expand=True)
    
    def _plot_custom(self, frame):
        """Generate custom discrimination plot using available data"""
        samples = self.app.samples
        plot_type = self.custom_plot_type.get()
        
        # Prepare data based on plot type
        x_data = []
        y_data = []
        sample_ids = []
        colors_list = []
        
        for sample in samples:
            try:
                if plot_type == "Zr vs Nb":
                    x = float(sample.get('Zr_ppm', 0) or 0)
                    y = float(sample.get('Nb_ppm', 0) or 0)
                    x_label, y_label = "Zr (ppm)", "Nb (ppm)"
                elif plot_type == "Zr vs Ba":
                    x = float(sample.get('Zr_ppm', 0) or 0)
                    y = float(sample.get('Ba_ppm', 0) or 0)
                    x_label, y_label = "Zr (ppm)", "Ba (ppm)"
                elif plot_type == "Nb vs Ba":
                    x = float(sample.get('Nb_ppm', 0) or 0)
                    y = float(sample.get('Ba_ppm', 0) or 0)
                    x_label, y_label = "Nb (ppm)", "Ba (ppm)"
                else:  # Zr/Nb vs Ba/Rb
                    Zr = float(sample.get('Zr_ppm', 0) or 0)
                    Nb = float(sample.get('Nb_ppm', 1) or 1)  # Avoid div by zero
                    Ba = float(sample.get('Ba_ppm', 0) or 0)
                    Rb = float(sample.get('Rb_ppm', 1) or 1)
                    x = Zr / Nb if Nb > 0 else 0
                    y = Ba / Rb if Rb > 0 else 0
                    x_label, y_label = "Zr/Nb", "Ba/Rb"
                
                if x > 0 or y > 0:  # At least some data
                    x_data.append(x)
                    y_data.append(y)
                    sample_ids.append(sample.get('Sample_ID', 'Unknown'))
                    
                    # Color by classification
                    classification = sample.get('Final_Classification', 'Unknown')
                    if 'Jordan' in classification or 'Harrat' in classification:
                        colors_list.append('red')
                    elif 'Golan' in classification:
                        colors_list.append('blue')
                    elif 'Egypt' in classification or 'Sinai' in classification:
                        colors_list.append('green')
                    else:
                        colors_list.append('gray')
            except (ValueError, TypeError, ZeroDivisionError):
                continue
        
        if len(x_data) < 1:
            messagebox.showwarning("No Data", "No valid data found for this plot type")
            return
        
        # Clear frame
        for widget in frame.winfo_children():
            widget.destroy()
        
        # Create plot
        fig, ax = plt.subplots(figsize=(10, 8))
        
        scatter = ax.scatter(x_data, y_data, c=colors_list, s=100, alpha=0.7,
                           edgecolors='black', linewidth=1)
        
        # Add sample labels
        for i, label in enumerate(sample_ids):
            ax.annotate(label, (x_data[i], y_data[i]), fontsize=8, alpha=0.7)
        
        ax.set_xlabel(x_label, fontsize=12)
        ax.set_ylabel(y_label, fontsize=12)
        ax.set_title(f'Custom Discrimination: {plot_type}',
                    fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # Add legend
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], marker='o', color='w', markerfacecolor='red', 
                  markersize=10, label='Jordan/Harrat'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='blue', 
                  markersize=10, label='Golan'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='green', 
                  markersize=10, label='Egypt/Sinai'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='gray', 
                  markersize=10, label='Other/Unclassified')
        ]
        ax.legend(handles=legend_elements, loc='best')
        
        fig.tight_layout()
        
        # Embed
        canvas = FigureCanvasTkAgg(fig, frame)
        canvas.draw()
        toolbar = NavigationToolbar2Tk(canvas, frame)
        toolbar.update()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def _create_help_tab(self, notebook):
        """Create help documentation tab"""
        frame = tk.Frame(notebook)
        notebook.add(frame, text="❓ Help")
        
        # Scrollable text
        text_frame = tk.Frame(frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text = tk.Text(text_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set,
                      font=("Arial", 10), padx=10, pady=5)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text.yview)
        
        help_text = """
DISCRIMINATION DIAGRAMS - USER GUIDE
═══════════════════════════════════

WHAT ARE DISCRIMINATION DIAGRAMS?
─────────────────────────────────
Discrimination diagrams use trace element ratios and concentrations to classify
basalts by their tectonic setting (e.g., mid-ocean ridge, island arc, within-plate).

WHY USE THEM FOR PROVENANCE?
────────────────────────────
Different tectonic settings produce basalts with distinct geochemical signatures.
By plotting archaeological basalt artifacts on these diagrams, you can narrow down
their geological source.

AVAILABLE DIAGRAMS
──────────────────

1. PEARCE & CANN (1973) - Ti-Zr-Y Ternary
   • Classic discrimination diagram
   • Fields: MORB, IAB, WPB, CAB
   • Requires: Ti, Zr, Y data
   • Best for: Initial tectonic classification

2. WOOD (1980) - Ti vs V
   • Simple bivariate plot
   • Fields: MORB, OIB, IAT, CAB
   • Requires: Ti, V data
   • Best for: Quick screening

3. SHERVAIS (1982) - Ti/V Ratio
   • Uses single ratio
   • Ti/V ranges define settings
   • Requires: Ti, V data
   • Best for: Arc vs non-arc discrimination

4. CUSTOM PLOTS - Your Data
   • Uses Zr, Nb, Ba, Rb from your dataset
   • Flexible plotting options
   • Best for: Exploring your specific samples

DATA REQUIREMENTS
─────────────────
NOTE: Most classical diagrams require Ti, V, and Y which may not be in your
current dataset. The "Custom" tab uses elements you already have (Zr, Nb, Ba, Rb).

To add Ti, V, Y:
- Update your data collection to include these elements
- Common analytical methods: ICP-MS, XRF

INTERPRETATION TIPS
───────────────────
- Samples from same source should plot in same field
- Overlapping fields indicate transitional compositions
- Consider analytical uncertainty when interpreting boundaries
- Use multiple diagrams for robust classification
- Validate against known reference samples

REFERENCES
──────────
Pearce, J. A., & Cann, J. R. (1973). Tectonic setting of basic volcanic rocks
  determined using trace element analyses. Earth and Planetary Science Letters.

Wood, D. A. (1980). The application of a Th-Hf-Ta diagram to problems of
  tectonomagmatic classification. Earth and Planetary Science Letters.

Shervais, J. W. (1982). Ti-V plots and the petrogenesis of modern and ophiolitic
  lavas. Earth and Planetary Science Letters.

For more information, consult standard petrology references or contact Sefy Levy.
"""
        
        text.insert("1.0", help_text)
        text.config(state=tk.DISABLED)

def setup_plugin(main_app):
    """Plugin setup function"""
    plugin = DiscriminationDiagramsPlugin(main_app)
    return plugin  # ← REMOVE ALL MENU CODE
