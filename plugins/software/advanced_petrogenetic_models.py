"""
Advanced Petrogenetic Models Plugin v1.0
AFC · Zone Refining · In-Situ Crystallization
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Author: Sefy Levy & DeepSeek
License: CC BY-NC-SA 4.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

PLUGIN_INFO = {
    "category": "software",
    "id": "advanced_petrogenetic_models",
    "name": "Advanced Petrogenetic Models",
    "icon": "🌋⚗️",
    "description": "AFC · Zone Refining · In-Situ Crystallization — Complete magma evolution models",
    "version": "1.0.0",
    "requires": ["numpy", "scipy", "matplotlib"],
    "author": "Sefy Levy & DeepSeek"
}

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
from scipy.optimize import fsolve, minimize
from scipy.integrate import odeint
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import json

# ============================================================================
# AFC MODEL - DePaolo (1981) with full implementation
# ============================================================================

class AFCModel:
    """
    Assimilation-Fractional Crystallization (AFC)
    DePaolo (1981) - full implementation
    
    Equations:
    Cm/C0 = F^(-r) + (r/(r-1)) * (Ca/(z*C0)) * (1 - F^(-r))
    where r = (D + r - 1)/(r - 1)
          r = Ma/Mc (assimilation/crystallization ratio)
          D = bulk distribution coefficient
          z = r/(r + D - 1)
    """
    
    @staticmethod
    def calculate(C0: float, Ca: float, D: float, r: float, F: np.ndarray) -> np.ndarray:
        """
        Calculate AFC trajectory
        
        Parameters:
        C0: initial concentration in magma
        Ca: concentration in assimilant
        D: bulk distribution coefficient
        r: Ma/Mc (assimilation/crystallization ratio)
        F: array of melt fractions (0-1)
        """
        # Avoid division by zero
        r = max(r, 0.001)
        
        # Calculate z parameter
        z = r / (r + D - 1)
        
        # AFC equation
        term1 = F ** (-z)
        
        if abs(r - 1) < 1e-6:
            # Special case when r = 1
            result = C0 * F ** (-z) + (Ca / (z * C0)) * (1 - F ** (-z))
        else:
            result = C0 * F ** (-z) + (r / (r - 1)) * (Ca / (z * C0)) * (1 - F ** (-z))
        
        return result
    
    @staticmethod
    def isotope_ratio(R0: float, Ra: float, C0: float, Ca: float, 
                      D: float, r: float, F: np.ndarray) -> np.ndarray:
        """
        Calculate AFC for isotope ratios
        
        Parameters:
        R0: initial isotope ratio in magma
        Ra: isotope ratio in assimilant
        C0: initial concentration of reference element
        Ca: concentration in assimilant
        """
        # Calculate concentration first
        C = AFCModel.calculate(C0, Ca, D, r, F)
        
        # Isotope mixing equation
        numerator = R0 * C0 * F ** (-D) + Ra * (Ca / r) * (1 - F ** (-r))
        denominator = C0 * F ** (-D) + (Ca / r) * (1 - F ** (-r))
        
        return numerator / denominator


# ============================================================================
# ZONE REFINING - Harris (1974) with complete implementation
# ============================================================================

class ZoneRefiningModel:
    """
    Zone Refining model
    Harris (1974) - complete implementation
    
    Single pass: C/C0 = 1 - (1 - k) * exp(-k * x / L)
    Multiple passes: C/C0 = 1 - (1 - k)^n * exp(-n * k * x / L)
    """
    
    @staticmethod
    def single_pass(C0: float, k: float, x: np.ndarray, L: float = 1.0) -> np.ndarray:
        """
        Single zone refining pass
        
        C0: initial concentration
        k: partition coefficient
        x: distance along zone (normalized)
        L: zone length
        """
        return C0 * (1 - (1 - k) * np.exp(-k * x / L))
    
    @staticmethod
    def multiple_passes(C0: float, k: float, x: np.ndarray, 
                        n_passes: int, L: float = 1.0) -> np.ndarray:
        """
        Multiple zone refining passes
        
        n_passes: number of passes
        """
        return C0 * (1 - (1 - k) ** n_passes * np.exp(-n_passes * k * x / L))
    
    @staticmethod
    def effective_partition(x: np.ndarray, n_passes: int) -> np.ndarray:
        """
        Calculate effective partition coefficient after n passes
        """
        return 1 - (1 - x) ** n_passes / x


# ============================================================================
# IN-SITU CRYSTALLIZATION - Langmuir (1989)
# ============================================================================

class InSituCrystallizationModel:
    """
    In-Situ Crystallization (Langmuir, 1989)
    Crystals form and remain in contact with melt
    
    C/C0 = 1 / [1 - F(1 - D)]^(1/D)
    """
    
    @staticmethod
    def calculate(C0: float, D: float, F: np.ndarray) -> np.ndarray:
        """
        In-situ crystallization
        
        C0: initial concentration
        D: bulk distribution coefficient
        F: melt fraction (0-1)
        """
        return C0 / (1 - F * (1 - D)) ** (1 / D)
    
    @staticmethod
    def trapped_liquid_shift(C0: float, D: float, F: float, 
                              trapped_fraction: float = 0.1) -> float:
        """
        Calculate effect of trapped liquid on cumulate composition
        """
        melt = InSituCrystallizationModel.calculate(C0, D, np.array([F]))[0]
        crystal = C0 * D
        return trapped_fraction * melt + (1 - trapped_fraction) * crystal


# ============================================================================
# MAIN PLUGIN UI - COMPACT LIKE YOUR OTHER PLUGINS
# ============================================================================

class AdvancedPetrogeneticModelsPlugin:
    def __init__(self, main_app):
        self.app = main_app
        self.window = None
        self.results = {}
        
        # Default parameters
        self.C0 = 100.0      # Initial concentration
        self.Ca = 10.0        # Assimilant concentration
        self.D = 0.5          # Bulk distribution coefficient
        self.r = 0.3          # Assimilation/crystallization ratio
        self.k = 0.1          # Partition coefficient (zone refining)
        self.F_range = (0.1, 1.0, 50)  # Start, end, steps
        
        # UI Variables
        self.model_var = tk.StringVar(value="AFC")
        self.element_var = tk.StringVar(value="Zr")
        self.F_start_var = tk.DoubleVar(value=0.1)
        self.F_end_var = tk.DoubleVar(value=1.0)
        self.F_steps_var = tk.IntVar(value=50)
        self.C0_var = tk.DoubleVar(value=100.0)
        self.Ca_var = tk.DoubleVar(value=10.0)
        self.D_var = tk.DoubleVar(value=0.5)
        self.r_var = tk.DoubleVar(value=0.3)
        self.k_var = tk.DoubleVar(value=0.1)
        self.n_passes_var = tk.IntVar(value=5)
        
    def open_window(self):
        """Open the petrogenetic models window"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return
            
        self.window = tk.Toplevel(self.app.root)
        self.window.title("🌋 Advanced Petrogenetic Models v1.0")
        self.window.geometry("1000x650")
        self.window.transient(self.app.root)
        
        self._create_ui()
        self._load_from_main_app()
        self.window.lift()
        
    def _create_ui(self):
        """Create compact interface"""
        
        # Header
        header = tk.Frame(self.window, bg="#8e44ad", height=40)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(header, text="🌋", font=("Arial", 18),
                bg="#8e44ad", fg="white").pack(side=tk.LEFT, padx=8)
        tk.Label(header, text="Advanced Petrogenetic Models",
                font=("Arial", 12, "bold"), bg="#8e44ad", fg="white").pack(side=tk.LEFT, padx=2)
        tk.Label(header, text="AFC · Zone Refining · In-Situ",
                font=("Arial", 8), bg="#8e44ad", fg="#f1c40f").pack(side=tk.LEFT, padx=8)
        
        self.status_indicator = tk.Label(header, text="● READY",
                                        font=("Arial", 8), bg="#8e44ad", fg="#2ecc71")
        self.status_indicator.pack(side=tk.RIGHT, padx=10)
        
        # Main content
        main_paned = tk.PanedWindow(self.window, orient=tk.HORIZONTAL, sashwidth=4)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Controls
        left = tk.Frame(main_paned, bg="#ecf0f1", width=350)
        main_paned.add(left, width=350)
        
        # Model selection
        model_frame = tk.LabelFrame(left, text="1. Select Model", font=("Arial", 9, "bold"),
                                    bg="#ecf0f1", padx=8, pady=6)
        model_frame.pack(fill=tk.X, padx=5, pady=5)
        
        models = [
            ("🌋 AFC (DePaolo 1981)", "AFC"),
            ("🔬 Zone Refining (Harris 1974)", "Zone"),
            ("🧪 In-Situ Crystallization (Langmuir 1989)", "InSitu")
        ]
        
        for text, value in models:
            tk.Radiobutton(model_frame, text=text, variable=self.model_var,
                          value=value, bg="#ecf0f1", anchor=tk.W).pack(fill=tk.X, pady=1)
        
        # Parameters
        param_frame = tk.LabelFrame(left, text="2. Parameters", font=("Arial", 9, "bold"),
                                    bg="#ecf0f1", padx=8, pady=6)
        param_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # F range
        f_row = tk.Frame(param_frame, bg="#ecf0f1")
        f_row.pack(fill=tk.X, pady=2)
        tk.Label(f_row, text="F range:", width=10, anchor=tk.W,
                bg="#ecf0f1", font=("Arial", 8)).pack(side=tk.LEFT)
        tk.Spinbox(f_row, from_=0.01, to=1.0, increment=0.01,
                  textvariable=self.F_start_var, width=6).pack(side=tk.LEFT, padx=2)
        tk.Label(f_row, text="to", bg="#ecf0f1").pack(side=tk.LEFT)
        tk.Spinbox(f_row, from_=0.01, to=1.0, increment=0.01,
                  textvariable=self.F_end_var, width=6).pack(side=tk.LEFT, padx=2)
        tk.Label(f_row, text="steps:", bg="#ecf0f1").pack(side=tk.LEFT, padx=2)
        tk.Spinbox(f_row, from_=10, to=200, textvariable=self.F_steps_var,
                  width=4).pack(side=tk.LEFT)
        
        # Common parameters (grid layout)
        params = [
            ("C₀ (ppm):", self.C0_var),
            ("Ca (ppm):", self.Ca_var),
            ("D:", self.D_var)
        ]
        
        for i, (label, var) in enumerate(params):
            row = tk.Frame(param_frame, bg="#ecf0f1")
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text=label, width=10, anchor=tk.W,
                    bg="#ecf0f1", font=("Arial", 8)).pack(side=tk.LEFT)
            tk.Spinbox(row, from_=0.001, to=10000, increment=1.0,
                      textvariable=var, width=10).pack(side=tk.LEFT, padx=2)
        
        # AFC-specific parameters
        self.afc_frame = tk.Frame(param_frame, bg="#ecf0f1")
        self.afc_frame.pack(fill=tk.X, pady=2)
        tk.Label(self.afc_frame, text="r (Ma/Mc):", width=10, anchor=tk.W,
                bg="#ecf0f1", font=("Arial", 8)).pack(side=tk.LEFT)
        tk.Spinbox(self.afc_frame, from_=0.0, to=2.0, increment=0.05,
                  textvariable=self.r_var, width=10).pack(side=tk.LEFT, padx=2)
        
        # Zone refining parameters
        self.zone_frame = tk.Frame(param_frame, bg="#ecf0f1")
        self.zone_frame.pack(fill=tk.X, pady=2)
        tk.Label(self.zone_frame, text="k:", width=10, anchor=tk.W,
                bg="#ecf0f1", font=("Arial", 8)).pack(side=tk.LEFT)
        tk.Spinbox(self.zone_frame, from_=0.001, to=10.0, increment=0.05,
                  textvariable=self.k_var, width=6).pack(side=tk.LEFT, padx=2)
        tk.Label(self.zone_frame, text="passes:", bg="#ecf0f1").pack(side=tk.LEFT, padx=2)
        tk.Spinbox(self.zone_frame, from_=1, to=50, textvariable=self.n_passes_var,
                  width=4).pack(side=tk.LEFT)
        
        # Element selection from main app
        elem_frame = tk.LabelFrame(left, text="3. Element from Main App", 
                                   font=("Arial", 9, "bold"),
                                   bg="#ecf0f1", padx=8, pady=6)
        elem_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(elem_frame, text="Use data from:", bg="#ecf0f1",
                font=("Arial", 8)).pack(anchor=tk.W)
        
        self.element_combo = ttk.Combobox(elem_frame, textvariable=self.element_var,
                                          values=[], width=20)
        self.element_combo.pack(fill=tk.X, pady=2)
        
        tk.Button(elem_frame, text="📥 Load from Selected Sample",
                 command=self._load_from_selected,
                 bg="#3498db", fg="white", font=("Arial", 8)).pack(pady=2)
        
        # Run button
        tk.Button(left, text="▶ RUN MODEL", command=self._run_model,
                 bg="#e67e22", fg="white", font=("Arial", 11, "bold"),
                 height=2).pack(fill=tk.X, padx=5, pady=10)
        
        # Right panel - Plot
        right = tk.Frame(main_paned, bg="white")
        main_paned.add(right, width=600)
        
        self.fig = plt.Figure(figsize=(7, 5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, right)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Bottom status
        status = tk.Frame(self.window, bg="#2c3e50", height=24)
        status.pack(fill=tk.X, side=tk.BOTTOM)
        status.pack_propagate(False)
        self.status_var = tk.StringVar(value="Ready")
        tk.Label(status, textvariable=self.status_var,
                font=("Arial", 7), bg="#2c3e50", fg="white").pack(side=tk.LEFT, padx=8)
        
        # Show model selection by default
        self._on_model_change()
        self.model_var.trace('w', lambda *a: self._on_model_change())
        
    def _on_model_change(self):
        """Show/hide model-specific parameters"""
        model = self.model_var.get()
        
        if model == "AFC":
            self.afc_frame.pack(fill=tk.X, pady=2)
            self.zone_frame.pack_forget()
        elif model == "Zone":
            self.afc_frame.pack_forget()
            self.zone_frame.pack(fill=tk.X, pady=2)
        else:  # InSitu
            self.afc_frame.pack_forget()
            self.zone_frame.pack_forget()
    
    def _load_from_main_app(self):
        """Load numeric columns from main app"""
        if hasattr(self.app, 'samples') and self.app.samples:
            numeric_cols = []
            for col in self.app.samples[0].keys():
                try:
                    float(self.app.samples[0].get(col, 0))
                    numeric_cols.append(col)
                except:
                    pass
            self.element_combo['values'] = numeric_cols
            if numeric_cols:
                self.element_combo.current(0)
    
    def _load_from_selected(self):
        """Load C0 from selected sample"""
        selected = self.app.center.get_selected_indices()
        if not selected:
            messagebox.showwarning("No Selection", "Select a sample first")
            return
        
        sample = self.app.samples[selected[0]]
        elem = self.element_var.get()
        
        if elem in sample:
            try:
                val = float(sample[elem])
                self.C0_var.set(val)
                self.status_var.set(f"✅ Loaded {elem} = {val:.2f} ppm")
            except:
                messagebox.showerror("Error", f"Could not parse {elem} value")
    
    def _run_model(self):
        """Run selected model"""
        try:
            model = self.model_var.get()
            
            # Get parameters
            F = np.linspace(self.F_start_var.get(), 
                           self.F_end_var.get(), 
                           self.F_steps_var.get())
            C0 = self.C0_var.get()
            
            self.ax.clear()
            
            if model == "AFC":
                Ca = self.Ca_var.get()
                D = self.D_var.get()
                r = self.r_var.get()
                
                result = AFCModel.calculate(C0, Ca, D, r, F)
                
                self.ax.plot(F, result, 'b-', linewidth=2, label=f'AFC (r={r:.2f})')
                self.ax.set_title(f'AFC Model - DePaolo (1981)')
                
                # Store results
                self.results = {
                    'model': 'AFC',
                    'F': F.tolist(),
                    'C': result.tolist(),
                    'params': {'C0': C0, 'Ca': Ca, 'D': D, 'r': r}
                }
                
            elif model == "Zone":
                k = self.k_var.get()
                n = self.n_passes_var.get()
                
                # Normalized distance along zone
                x = np.linspace(0, 10, len(F))
                
                if n == 1:
                    result = ZoneRefiningModel.single_pass(C0, k, x)
                    label = f'Zone refining (k={k:.3f})'
                else:
                    result = ZoneRefiningModel.multiple_passes(C0, k, x, n)
                    label = f'Zone refining ({n} passes, k={k:.3f})'
                
                self.ax.plot(x, result, 'r-', linewidth=2, label=label)
                self.ax.set_xlabel('Distance (zone lengths)')
                self.ax.set_title(f'Zone Refining - Harris (1974)')
                
                self.results = {
                    'model': 'ZoneRefining',
                    'x': x.tolist(),
                    'C': result.tolist(),
                    'params': {'C0': C0, 'k': k, 'passes': n}
                }
                
            else:  # InSitu
                D = self.D_var.get()
                result = InSituCrystallizationModel.calculate(C0, D, F)
                
                self.ax.plot(F, result, 'g-', linewidth=2, label=f'In-Situ (D={D:.2f})')
                self.ax.set_title(f'In-Situ Crystallization - Langmuir (1989)')
                
                self.results = {
                    'model': 'InSitu',
                    'F': F.tolist(),
                    'C': result.tolist(),
                    'params': {'C0': C0, 'D': D}
                }
            
            # Common plot formatting
            self.ax.set_xlabel('Melt fraction (F)')
            self.ax.set_ylabel('Concentration (ppm)')
            self.ax.grid(True, alpha=0.3)
            self.ax.legend()
            
            self.canvas.draw()
            self.status_var.set(f"✅ {model} model complete")
            
            # Ask to export
            if messagebox.askyesno("Export", "Export results to main app?"):
                self._export_to_main()
                
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.status_var.set(f"❌ Error: {str(e)[:50]}")
    
    def _export_to_main(self):
        """Export results to main app"""
        if not self.results:
            return
        
        table_data = []
        model = self.results['model']
        
        if model == 'AFC':
            for i, (f, c) in enumerate(zip(self.results['F'], self.results['C'])):
                table_data.append({
                    'Sample_ID': f"AFC_{i+1:03d}",
                    'F_melt': f"{f:.3f}",
                    'C_ppm': f"{c:.2f}",
                    'Model': 'AFC',
                    'C0': f"{self.results['params']['C0']:.1f}",
                    'Ca': f"{self.results['params']['Ca']:.1f}",
                    'D': f"{self.results['params']['D']:.2f}",
                    'r': f"{self.results['params']['r']:.2f}",
                    'Notes': f"AFC model - DePaolo (1981)"
                })
        elif model == 'ZoneRefining':
            for i, (x, c) in enumerate(zip(self.results['x'], self.results['C'])):
                table_data.append({
                    'Sample_ID': f"ZONE_{i+1:03d}",
                    'Distance': f"{x:.2f}",
                    'C_ppm': f"{c:.2f}",
                    'Model': 'Zone Refining',
                    'C0': f"{self.results['params']['C0']:.1f}",
                    'k': f"{self.results['params']['k']:.3f}",
                    'Passes': str(self.results['params']['passes']),
                    'Notes': f"Zone refining - Harris (1974)"
                })
        else:  # InSitu
            for i, (f, c) in enumerate(zip(self.results['F'], self.results['C'])):
                table_data.append({
                    'Sample_ID': f"INSITU_{i+1:03d}",
                    'F_melt': f"{f:.3f}",
                    'C_ppm': f"{c:.2f}",
                    'Model': 'In-Situ',
                    'C0': f"{self.results['params']['C0']:.1f}",
                    'D': f"{self.results['params']['D']:.2f}",
                    'Notes': f"In-situ crystallization - Langmuir (1989)"
                })
        
        if table_data:
            self.app.import_data_from_plugin(table_data)
            self.status_var.set(f"✅ Exported {len(table_data)} rows")
            messagebox.showinfo("Success", f"Exported {len(table_data)} model points")


def setup_plugin(main_app):
    """Plugin setup"""
    return AdvancedPetrogeneticModelsPlugin(main_app)