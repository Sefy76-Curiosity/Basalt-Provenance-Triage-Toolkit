"""
Petrogenetic Suite v1.0 - AFC · Fractional Crystallization · Zone Refining · Mixing
WITH FULL MAIN APP INTEGRATION

✓ AFC (DePaolo 1981) with full parameterization
✓ Fractional Crystallization (Rayleigh, equilibrium, in-situ)
✓ Zone Refining (Harris 1974) with multiple passes
✓ Binary & Three-component Mixing Models
✓ Real-time curve plotting · Model comparison · Export
"""

PLUGIN_INFO = {
    "category": "software",
    "id": "petrogenetic_suite",
    "name": "Petrogenetic Suite",
    "description": "AFC · Fractional · Zone Refining · Mixing — Complete magma evolution models",
    "icon": "🌋",
    "version": "1.0.0",
    "requires": ["numpy", "scipy", "matplotlib", "pandas"],
    "author": "Sefy Levy & DeepSeek"
}

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import pandas as pd
from datetime import datetime
import json
import traceback
from pathlib import Path

try:
    import matplotlib
    matplotlib.use('TkAgg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    import numpy as np
    from scipy import optimize, interpolate
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


class PetrogeneticSuitePlugin:
    """
    PETROGENETIC SUITE - Complete magma evolution models
    AFC · Fractional Crystallization · Zone Refining · Mixing
    """

    def __init__(self, main_app):
        self.app = main_app
        self.window = None

        # ============ DATA ============
        self.samples = []
        self.current_element = None
        self.model_results = {}
        self.comparison_results = []

        # ============ UI VARIABLES ============
        # Notebook tabs
        self.notebook = None

        # Common
        self.status_var = None
        self.progress = None

        # Element selection
        self.element_var = tk.StringVar(value="")
        self.numeric_columns = []

        # AFC tab
        self.afc_C0_var = tk.DoubleVar(value=100.0)
        self.afc_Ca_var = tk.DoubleVar(value=10.0)
        self.afc_D_var = tk.DoubleVar(value=0.5)
        self.afc_r_var = tk.DoubleVar(value=0.3)
        self.afc_F_min_var = tk.DoubleVar(value=0.1)
        self.afc_F_max_var = tk.DoubleVar(value=1.0)
        self.afc_F_steps_var = tk.IntVar(value=50)

        # Fractional tab
        self.frac_C0_var = tk.DoubleVar(value=100.0)
        self.frac_D_var = tk.DoubleVar(value=0.5)
        self.frac_model_var = tk.StringVar(value="rayleigh")
        self.frac_F_min_var = tk.DoubleVar(value=0.1)
        self.frac_F_max_var = tk.DoubleVar(value=1.0)
        self.frac_F_steps_var = tk.IntVar(value=50)

        # Zone Refining tab
        self.zone_C0_var = tk.DoubleVar(value=100.0)
        self.zone_k_var = tk.DoubleVar(value=0.1)
        self.zone_passes_var = tk.IntVar(value=5)
        self.zone_length_var = tk.DoubleVar(value=1.0)
        self.zone_steps_var = tk.IntVar(value=100)

        # Mixing tab
        self.mix_model_var = tk.StringVar(value="binary")
        self.mix_CA_var = tk.DoubleVar(value=100.0)
        self.mix_CB_var = tk.DoubleVar(value=20.0)
        self.mix_fA_var = tk.DoubleVar(value=0.5)
        self.mix_fA_min_var = tk.DoubleVar(value=0.0)
        self.mix_fA_max_var = tk.DoubleVar(value=1.0)
        self.mix_steps_var = tk.IntVar(value=50)
        self.mix_CC_var = tk.DoubleVar(value=50.0)  # For ternary

        # Comparison tab
        self.compare_elements = []
        self.compare_results = {}

        self._check_dependencies()

    def _check_dependencies(self):
        """Check required packages"""
        missing = []
        if not HAS_MATPLOTLIB: missing.append("matplotlib")
        if not HAS_SCIPY: missing.append("scipy")
        self.dependencies_met = len(missing) == 0
        self.missing_deps = missing

    # ============================================================================
    # SAFE FLOAT CONVERSION
    # ============================================================================
    def _safe_float(self, value):
        """Safely convert to float"""
        if value is None or value == '':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    # ============================================================================
    # DATA LOADING FROM MAIN APP
    # ============================================================================
    def _load_from_main_app(self):
        """Load geochemical data from main app samples"""
        if not hasattr(self.app, 'samples') or not self.app.samples:
            return False

        self.samples = self.app.samples

        # Detect numeric columns
        self.numeric_columns = []

        if self.samples and len(self.samples) > 0:
            first_sample = self.samples[0]
            for col in first_sample.keys():
                # Try to convert to float
                try:
                    val = first_sample[col]
                    if val and val != '':
                        float(val)
                        self.numeric_columns.append(col)
                except (ValueError, TypeError):
                    pass


        # Update UI if window is open
        self._update_ui_columns()

        return True

    def _update_ui_columns(self):
        """Update column selectors in UI"""
        if hasattr(self, 'element_combo'):
            self.element_combo['values'] = self.numeric_columns
            if self.numeric_columns and not self.element_var.get():
                self.element_var.set(self.numeric_columns[0])

        if hasattr(self, 'compare_listbox'):
            self.compare_listbox.delete(0, tk.END)
            for col in sorted(self.numeric_columns):
                self.compare_listbox.insert(tk.END, col)

    # ============================================================================
    # AFC MODEL (DePaolo 1981)
    # ============================================================================
    def _afc_model(self, C0, Ca, D, r, F):
        """
        AFC equation from DePaolo (1981)

        Cm/C0 = F^(-r) + (r/(r-1)) * (Ca/(z*C0)) * (1 - F^(-r))
        where z = (r + D - 1)/r
        """
        # Avoid division by zero
        if abs(r - 1) < 1e-6:
            r = 1.001

        # Calculate z parameter
        z = (r + D - 1) / r

        # AFC equation
        term1 = F ** (-z)
        term2 = (r / (r - 1)) * (Ca / (z * C0)) * (1 - F ** (-z))

        return C0 * (term1 + term2)

    def _calculate_afc(self):
        """Calculate AFC model curve"""
        C0 = self.afc_C0_var.get()
        Ca = self.afc_Ca_var.get()
        D = self.afc_D_var.get()
        r = self.afc_r_var.get()

        F = np.linspace(self.afc_F_min_var.get(),
                        self.afc_F_max_var.get(),
                        self.afc_F_steps_var.get())

        C = self._afc_model(C0, Ca, D, r, F)

        return {
            'F': F,
            'C': C,
            'params': {
                'C0': C0, 'Ca': Ca, 'D': D, 'r': r,
                'model': 'AFC (DePaolo 1981)'
            }
        }

    # ============================================================================
    # FRACTIONAL CRYSTALLIZATION MODELS
    # ============================================================================
    def _rayleigh_model(self, C0, D, F):
        """Rayleigh fractional crystallization"""
        return C0 * F ** (D - 1)

    def _equilibrium_model(self, C0, D, F):
        """Equilibrium crystallization"""
        return C0 / (D + F * (1 - D))

    def _in_situ_model(self, C0, D, F):
        """In-situ crystallization (Langmuir 1989)"""
        return C0 / (1 - F * (1 - D)) ** (1 / D)

    def _calculate_fractional(self):
        """Calculate fractional crystallization model"""
        C0 = self.frac_C0_var.get()
        D = self.frac_D_var.get()
        model_type = self.frac_model_var.get()

        F = np.linspace(self.frac_F_min_var.get(),
                        self.frac_F_max_var.get(),
                        self.frac_F_steps_var.get())

        if model_type == 'rayleigh':
            C = self._rayleigh_model(C0, D, F)
            model_name = 'Rayleigh Fractionation'
        elif model_type == 'equilibrium':
            C = self._equilibrium_model(C0, D, F)
            model_name = 'Equilibrium Crystallization'
        else:  # in-situ
            C = self._in_situ_model(C0, D, F)
            model_name = 'In-Situ Crystallization (Langmuir 1989)'

        return {
            'F': F,
            'C': C,
            'params': {
                'C0': C0, 'D': D,
                'model': model_name
            }
        }

    # ============================================================================
    # ZONE REFINING (Harris 1974)
    # ============================================================================
    def _zone_refining_single_pass(self, C0, k, x, L=1.0):
        """Single pass zone refining"""
        return C0 * (1 - (1 - k) * np.exp(-k * x / L))

    def _zone_refining_multi_pass(self, C0, k, x, n_passes, L=1.0):
        """Multiple pass zone refining"""
        return C0 * (1 - (1 - k) ** n_passes * np.exp(-n_passes * k * x / L))

    def _calculate_zone_refining(self):
        """Calculate zone refining model"""
        C0 = self.zone_C0_var.get()
        k = self.zone_k_var.get()
        n_passes = self.zone_passes_var.get()
        L = self.zone_length_var.get()

        x = np.linspace(0, 10 * L, self.zone_steps_var.get())

        if n_passes == 1:
            C = self._zone_refining_single_pass(C0, k, x, L)
            model_name = f'Zone Refining (1 pass, k={k:.3f})'
        else:
            C = self._zone_refining_multi_pass(C0, k, x, n_passes, L)
            model_name = f'Zone Refining ({n_passes} passes, k={k:.3f})'

        return {
            'x': x,
            'C': C,
            'params': {
                'C0': C0, 'k': k, 'passes': n_passes,
                'model': model_name
            }
        }

    # ============================================================================
    # MIXING MODELS
    # ============================================================================
    def _binary_mixing(self, CA, CB, fA):
        """Binary mixing"""
        return CA * fA + CB * (1 - fA)

    def _ternary_mixing(self, CA, CB, CC, fA, fB):
        """Ternary mixing (fC = 1 - fA - fB)"""
        fC = 1 - fA - fB
        return CA * fA + CB * fB + CC * fC

    def _calculate_mixing(self):
        """Calculate mixing model"""
        model_type = self.mix_model_var.get()

        if model_type == 'binary':
            CA = self.mix_CA_var.get()
            CB = self.mix_CB_var.get()

            fA = np.linspace(self.mix_fA_min_var.get(),
                            self.mix_fA_max_var.get(),
                            self.mix_steps_var.get())

            C = self._binary_mixing(CA, CB, fA)

            return {
                'x': fA,
                'C': C,
                'params': {
                    'model': 'Binary Mixing',
                    'CA': CA, 'CB': CB
                },
                'xlabel': 'Fraction A'
            }

        else:  # ternary
            CA = self.mix_CA_var.get()
            CB = self.mix_CB_var.get()
            CC = self.mix_CC_var.get()

            # Create ternary grid
            steps = self.mix_steps_var.get()
            fA = np.linspace(0, 1, steps)
            fB = np.linspace(0, 1, steps)
            FA, FB = np.meshgrid(fA, fB)

            # Only keep points where fA + fB ≤ 1
            mask = FA + FB <= 1
            C = np.zeros_like(FA)
            C[mask] = self._ternary_mixing(CA, CB, CC, FA[mask], FB[mask])
            C[~mask] = np.nan

            return {
                'FA': FA, 'FB': FB, 'C': C,
                'params': {
                    'model': 'Ternary Mixing',
                    'CA': CA, 'CB': CB, 'CC': CC
                }
            }

    # ============================================================================
    # PLOTTING METHODS
    # ============================================================================
    def _plot_afc(self, ax, result):
        """Plot AFC model"""
        ax.clear()

        F = result['F']
        C = result['C']
        params = result['params']

        ax.plot(F, C, 'b-', linewidth=2, label=params['model'])

        # Add sample data if element selected
        if self.element_var.get() and self.element_var.get() in self.numeric_columns:
            elem = self.element_var.get()
            values = []
            for s in self.samples:
                val = self._safe_float(s.get(elem))
                if val is not None:
                    values.append(val)

            if values:
                # Plot as horizontal lines at F=1 (parent magma)
                ax.scatter([1.0] * len(values), values,
                          c='red', s=30, alpha=0.5, edgecolor='black',
                          label=f'Samples ({elem})', zorder=5)

        ax.set_xlabel('Melt Fraction (F)')
        ax.set_ylabel('Concentration (ppm)')
        ax.set_title(f'AFC Model\nC₀={params["C0"]:.1f}, Ca={params["Ca"]:.1f}, D={params["D"]:.2f}, r={params["r"]:.2f}')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best')
        ax.set_xlim(0, 1.05)
        ax.set_ylim(bottom=0)

    def _plot_fractional(self, ax, result):
        """Plot fractional crystallization model"""
        ax.clear()

        F = result['F']
        C = result['C']
        params = result['params']

        ax.plot(F, C, 'r-', linewidth=2, label=params['model'])

        # Add sample data if element selected
        if self.element_var.get() and self.element_var.get() in self.numeric_columns:
            elem = self.element_var.get()
            values = []
            for s in self.samples:
                val = self._safe_float(s.get(elem))
                if val is not None:
                    values.append(val)

            if values:
                ax.scatter([1.0] * len(values), values,
                          c='blue', s=30, alpha=0.5, edgecolor='black',
                          label=f'Samples ({elem})', zorder=5)

        ax.set_xlabel('Melt Fraction (F)')
        ax.set_ylabel('Concentration (ppm)')
        ax.set_title(f'{params["model"]}\nC₀={params["C0"]:.1f}, D={params["D"]:.2f}')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best')
        ax.set_xlim(0, 1.05)
        ax.set_ylim(bottom=0)

    def _plot_zone_refining(self, ax, result):
        """Plot zone refining model"""
        ax.clear()

        x = result['x']
        C = result['C']
        params = result['params']

        ax.plot(x, C, 'g-', linewidth=2, label=params['model'])

        ax.set_xlabel('Distance (zone lengths)')
        ax.set_ylabel('Concentration (ppm)')
        ax.set_title(f'Zone Refining\nC₀={params["C0"]:.1f}, k={params["k"]:.3f}, {params["passes"]} passes')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best')

    def _plot_binary_mixing(self, ax, result):
        """Plot binary mixing model"""
        ax.clear()

        x = result['x']
        C = result['C']
        params = result['params']

        ax.plot(x, C, 'm-', linewidth=2, label=params['model'])

        # Add sample data if element selected
        if self.element_var.get() and self.element_var.get() in self.numeric_columns:
            elem = self.element_var.get()
            values = []
            for s in self.samples:
                val = self._safe_float(s.get(elem))
                if val is not None:
                    values.append(val)

            if values:
                # For mixing, we need to estimate fA from composition
                # This is just a placeholder - would need actual mixing calculation
                ax.axhline(y=np.mean(values), color='red', linestyle='--',
                          alpha=0.5, label=f'Mean sample ({elem})')

        ax.set_xlabel('Fraction of Component A')
        ax.set_ylabel('Concentration (ppm)')
        ax.set_title(f'Binary Mixing\nA={params["CA"]:.1f}, B={params["CB"]:.1f}')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best')
        ax.set_xlim(0, 1)

    def _plot_ternary_mixing(self, ax, result):
        """Plot ternary mixing as contour"""
        ax.clear()

        FA = result['FA']
        FB = result['FB']
        C = result['C']
        params = result['params']

        # Create contour plot
        contour = ax.contourf(FA, FB, C, levels=20, cmap='viridis', alpha=0.8)
        plt.colorbar(contour, ax=ax, label='Concentration (ppm)')

        # Add ternary boundaries
        ax.plot([0, 1, 0, 0], [0, 0, 1, 0], 'k-', linewidth=1)

        ax.set_xlabel('fA')
        ax.set_ylabel('fB')
        ax.set_title(f'Ternary Mixing\nA={params["CA"]:.1f}, B={params["CB"]:.1f}, C={params["CC"]:.1f}')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')

    # ============================================================================
    # MODEL COMPARISON
    # ============================================================================
    def _compare_models(self):
        """Compare multiple models for selected elements"""
        selected = [self.compare_listbox.get(i) for i in self.compare_listbox.curselection()]

        if len(selected) < 1:
            messagebox.showwarning("Warning", "Select at least one element")
            return

        self.compare_results = {}

        # Get sample data for selected elements
        for elem in selected:
            values = []
            for s in self.samples:
                val = self._safe_float(s.get(elem))
                if val is not None:
                    values.append(val)

            if values:
                self.compare_results[elem] = {
                    'values': values,
                    'mean': np.mean(values),
                    'std': np.std(values),
                    'min': np.min(values),
                    'max': np.max(values)
                }

        self._update_comparison_plot()

    def _update_comparison_plot(self):
        """Update comparison plot"""
        self.comp_ax.clear()

        if not self.compare_results:
            self.comp_ax.text(0.5, 0.5, "No data to compare", ha='center', va='center')
            self.comp_canvas.draw()
            return

        # Plot as bar chart
        elements = list(self.compare_results.keys())
        means = [self.compare_results[e]['mean'] for e in elements]
        stds = [self.compare_results[e]['std'] for e in elements]

        x_pos = np.arange(len(elements))
        bars = self.comp_ax.bar(x_pos, means, yerr=stds, capsize=5,
                               color='steelblue', alpha=0.7, edgecolor='black')

        # Add value labels
        for i, (bar, val) in enumerate(zip(bars, means)):
            height = bar.get_height()
            self.comp_ax.text(bar.get_x() + bar.get_width()/2., height + stds[i],
                            f'{val:.1f}', ha='center', va='bottom', fontsize=8)

        self.comp_ax.set_xlabel('Element')
        self.comp_ax.set_ylabel('Concentration (ppm)')
        self.comp_ax.set_title('Element Comparison')
        self.comp_ax.set_xticks(x_pos)
        self.comp_ax.set_xticklabels(elements, rotation=45, ha='right')
        self.comp_ax.grid(True, alpha=0.3, axis='y')

        self.comp_canvas.draw()
        self.status_var.set(f"✅ Compared {len(elements)} elements")

    # ============================================================================
    # EXPORT RESULTS
    # ============================================================================
    def _export_model(self, result, model_name):
        """Export model results to main app"""
        if not result:
            messagebox.showinfo("Export", "No model results to export")
            return

        records = []
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if 'F' in result:  # AFC or Fractional
            for i, (f, c) in enumerate(zip(result['F'], result['C'])):
                records.append({
                    'Sample_ID': f"{model_name}_{i+1:03d}",
                    'Model': result['params']['model'],
                    'F_melt': f"{f:.3f}",
                    'C_ppm': f"{c:.2f}",
                    'Petrogenetic_Timestamp': timestamp
                })

        elif 'x' in result and 'C' in result:  # Zone Refining or Binary Mixing
            for i, (x, c) in enumerate(zip(result['x'], result['C'])):
                records.append({
                    'Sample_ID': f"{model_name}_{i+1:03d}",
                    'Model': result['params']['model'],
                    'x': f"{x:.3f}",
                    'C_ppm': f"{c:.2f}",
                    'Petrogenetic_Timestamp': timestamp
                })

        if records:
            self.app.import_data_from_plugin(records)
            self.status_var.set(f"✅ Exported {len(records)} model points")

    # ============================================================================
    # UI CONSTRUCTION
    # ============================================================================
    def open_window(self):
        """Open the main window"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            self._load_from_main_app()
            return

        if not self.dependencies_met:
            messagebox.showerror(
                "Missing Dependencies",
                f"Please install: {', '.join(self.missing_deps)}"
            )
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("🌋 Petrogenetic Suite v1.0 - AFC · Fractional · Zone Refining · Mixing")
        self.window.geometry("1050x680")

        self._create_interface()

        # Load data
        if self._load_from_main_app():
            self.status_var.set(f"✅ Loaded data from main app")
        else:
            self.status_var.set("ℹ️ No geochemical data found")

        self.window.transient(self.app.root)
        self.window.lift()
        self.window.focus_force()

    def _create_interface(self):
        """Create the interface with 5 tabs"""
        # Header
        header = tk.Frame(self.window, bg="#8e44ad", height=40)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="🌋", font=("Arial", 18),
                bg="#8e44ad", fg="white").pack(side=tk.LEFT, padx=8)
        tk.Label(header, text="Petrogenetic Suite",
                font=("Arial", 14, "bold"),
                bg="#8e44ad", fg="white").pack(side=tk.LEFT, padx=2)
        tk.Label(header, text="v1.0 - AFC · Fractional · Zone Refining · Mixing",
                font=("Arial", 8),
                bg="#8e44ad", fg="#f1c40f").pack(side=tk.LEFT, padx=8)

        # Element selector (top)
        elem_frame = tk.Frame(header, bg="#8e44ad")
        elem_frame.pack(side=tk.RIGHT, padx=10)

        tk.Label(elem_frame, text="Element:", bg="#8e44ad", fg="white",
                font=("Arial", 9)).pack(side=tk.LEFT, padx=2)

        self.element_combo = ttk.Combobox(elem_frame, textvariable=self.element_var,
                                          values=self.numeric_columns, width=8,
                                          state='readonly')
        self.element_combo.pack(side=tk.LEFT, padx=2)

        # Main notebook
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create tabs
        self._create_afc_tab()
        self._create_fractional_tab()
        self._create_zone_tab()
        self._create_mixing_tab()
        self._create_comparison_tab()

        # Status bar
        status = tk.Frame(self.window, bg="#34495e", height=24)
        status.pack(fill=tk.X, side=tk.BOTTOM)
        status.pack_propagate(False)

        self.status_var = tk.StringVar(value="Ready")
        tk.Label(status, textvariable=self.status_var,
                font=("Arial", 8), bg="#34495e", fg="white").pack(side=tk.LEFT, padx=8)

        self.progress = ttk.Progressbar(status, mode='indeterminate', length=120)
        self.progress.pack(side=tk.RIGHT, padx=5)

    # ============================================================================
    # TAB 1: AFC
    # ============================================================================
    def _create_afc_tab(self):
        """Create AFC tab"""
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="🌋 AFC")

        # Split into left/right
        paned = tk.PanedWindow(tab, orient=tk.HORIZONTAL, sashwidth=4)
        paned.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Left panel - controls (300px)
        left = tk.Frame(paned, bg="#f5f5f5", width=300)
        paned.add(left, width=300, minsize=280)

        # Right panel - plot (500x500 square)
        right = tk.Frame(paned, bg="white", width=500, height=500)
        paned.add(right, width=500, minsize=450)

        # ===== Left controls =====
        # Parameters in grid
        params = [
            ("C₀ (ppm):", self.afc_C0_var, 0, 10000),
            ("Ca (ppm):", self.afc_Ca_var, 0, 10000),
            ("D:", self.afc_D_var, 0, 10),
            ("r (Ma/Mc):", self.afc_r_var, 0, 2),
            ("F min:", self.afc_F_min_var, 0, 1),
            ("F max:", self.afc_F_max_var, 0, 1),
            ("Steps:", self.afc_F_steps_var, 10, 200)
        ]

        row = 0
        for label, var, minv, maxv in params:
            frame = tk.Frame(left, bg="#f5f5f5")
            frame.pack(fill=tk.X, padx=5, pady=2)

            tk.Label(frame, text=label, width=8, anchor=tk.W,
                    bg="#f5f5f5").pack(side=tk.LEFT)

            if isinstance(var, tk.DoubleVar):
                tk.Spinbox(frame, from_=minv, to=maxv, increment=0.1,
                          textvariable=var, width=8).pack(side=tk.LEFT, padx=2)
            else:
                tk.Spinbox(frame, from_=minv, to=maxv, increment=1,
                          textvariable=var, width=8).pack(side=tk.LEFT, padx=2)

        # Calculate button
        tk.Button(left, text="🧮 Calculate AFC",
                 command=self._calculate_and_plot_afc,
                 bg="#e67e22", fg="white", width=20, height=2).pack(pady=10)

        # Export button
        tk.Button(left, text="📤 Export Model",
                 command=lambda: self._export_model(self.afc_result, "AFC"),
                 bg="#27ae60", fg="white", width=20).pack(pady=2)

        # ===== Right plot =====
        self.afc_fig = plt.Figure(figsize=(5, 5), dpi=90)
        self.afc_fig.patch.set_facecolor('white')
        self.afc_ax = self.afc_fig.add_subplot(111)
        self.afc_ax.set_facecolor('#f8f9fa')

        self.afc_canvas = FigureCanvasTkAgg(self.afc_fig, right)
        self.afc_canvas.draw()
        self.afc_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        toolbar_frame = tk.Frame(right, height=25)
        toolbar_frame.pack(fill=tk.X)
        toolbar = NavigationToolbar2Tk(self.afc_canvas, toolbar_frame)
        toolbar.update()

    def _calculate_and_plot_afc(self):
        """Calculate and plot AFC model"""
        self.progress.start()
        self.status_var.set("Calculating AFC model...")

        self.afc_result = self._calculate_afc()
        self._plot_afc(self.afc_ax, self.afc_result)
        self.afc_canvas.draw()

        self.status_var.set("✅ AFC model complete")
        self.progress.stop()

    # ============================================================================
    # TAB 2: Fractional Crystallization
    # ============================================================================
    def _create_fractional_tab(self):
        """Create fractional crystallization tab"""
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="🔬 Fractional")

        paned = tk.PanedWindow(tab, orient=tk.HORIZONTAL, sashwidth=4)
        paned.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        left = tk.Frame(paned, bg="#f5f5f5", width=300)
        paned.add(left, width=300, minsize=280)

        right = tk.Frame(paned, bg="white", width=500, height=500)
        paned.add(right, width=500, minsize=450)

        # ===== Left controls =====
        # Model type
        model_frame = tk.LabelFrame(left, text="Model Type", padx=5, pady=5, bg="#f5f5f5")
        model_frame.pack(fill=tk.X, padx=5, pady=2)

        tk.Radiobutton(model_frame, text="Rayleigh", variable=self.frac_model_var,
                      value="rayleigh", bg="#f5f5f5").pack(anchor=tk.W)
        tk.Radiobutton(model_frame, text="Equilibrium", variable=self.frac_model_var,
                      value="equilibrium", bg="#f5f5f5").pack(anchor=tk.W)
        tk.Radiobutton(model_frame, text="In-Situ", variable=self.frac_model_var,
                      value="in_situ", bg="#f5f5f5").pack(anchor=tk.W)

        # Parameters
        params = [
            ("C₀ (ppm):", self.frac_C0_var, 0, 10000),
            ("D:", self.frac_D_var, 0, 10),
            ("F min:", self.frac_F_min_var, 0, 1),
            ("F max:", self.frac_F_max_var, 0, 1),
            ("Steps:", self.frac_F_steps_var, 10, 200)
        ]

        for label, var, minv, maxv in params:
            frame = tk.Frame(left, bg="#f5f5f5")
            frame.pack(fill=tk.X, padx=5, pady=2)

            tk.Label(frame, text=label, width=8, anchor=tk.W,
                    bg="#f5f5f5").pack(side=tk.LEFT)

            if isinstance(var, tk.DoubleVar):
                tk.Spinbox(frame, from_=minv, to=maxv, increment=0.1,
                          textvariable=var, width=8).pack(side=tk.LEFT, padx=2)
            else:
                tk.Spinbox(frame, from_=minv, to=maxv, increment=1,
                          textvariable=var, width=8).pack(side=tk.LEFT, padx=2)

        tk.Button(left, text="🧮 Calculate",
                 command=self._calculate_and_plot_fractional,
                 bg="#e67e22", fg="white", width=20, height=2).pack(pady=10)

        tk.Button(left, text="📤 Export Model",
                 command=lambda: self._export_model(self.frac_result, "Fractional"),
                 bg="#27ae60", fg="white", width=20).pack(pady=2)

        # ===== Right plot =====
        self.frac_fig = plt.Figure(figsize=(5, 5), dpi=90)
        self.frac_fig.patch.set_facecolor('white')
        self.frac_ax = self.frac_fig.add_subplot(111)
        self.frac_ax.set_facecolor('#f8f9fa')

        self.frac_canvas = FigureCanvasTkAgg(self.frac_fig, right)
        self.frac_canvas.draw()
        self.frac_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        toolbar_frame = tk.Frame(right, height=25)
        toolbar_frame.pack(fill=tk.X)
        toolbar = NavigationToolbar2Tk(self.frac_canvas, toolbar_frame)
        toolbar.update()

    def _calculate_and_plot_fractional(self):
        """Calculate and plot fractional crystallization model"""
        self.progress.start()
        self.status_var.set("Calculating fractional crystallization...")

        self.frac_result = self._calculate_fractional()
        self._plot_fractional(self.frac_ax, self.frac_result)
        self.frac_canvas.draw()

        self.status_var.set("✅ Fractional crystallization complete")
        self.progress.stop()

    # ============================================================================
    # TAB 3: Zone Refining
    # ============================================================================
    def _create_zone_tab(self):
        """Create zone refining tab"""
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="🔬 Zone Refining")

        paned = tk.PanedWindow(tab, orient=tk.HORIZONTAL, sashwidth=4)
        paned.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        left = tk.Frame(paned, bg="#f5f5f5", width=300)
        paned.add(left, width=300, minsize=280)

        right = tk.Frame(paned, bg="white", width=500, height=500)
        paned.add(right, width=500, minsize=450)

        # ===== Left controls =====
        params = [
            ("C₀ (ppm):", self.zone_C0_var, 0, 10000),
            ("k:", self.zone_k_var, 0, 10),
            ("Passes:", self.zone_passes_var, 1, 50),
            ("Length:", self.zone_length_var, 0.1, 10),
            ("Steps:", self.zone_steps_var, 50, 500)
        ]

        for label, var, minv, maxv in params:
            frame = tk.Frame(left, bg="#f5f5f5")
            frame.pack(fill=tk.X, padx=5, pady=2)

            tk.Label(frame, text=label, width=8, anchor=tk.W,
                    bg="#f5f5f5").pack(side=tk.LEFT)

            if isinstance(var, tk.DoubleVar):
                tk.Spinbox(frame, from_=minv, to=maxv, increment=0.1,
                          textvariable=var, width=8).pack(side=tk.LEFT, padx=2)
            else:
                tk.Spinbox(frame, from_=minv, to=maxv, increment=1,
                          textvariable=var, width=8).pack(side=tk.LEFT, padx=2)

        tk.Button(left, text="🧮 Calculate",
                 command=self._calculate_and_plot_zone,
                 bg="#e67e22", fg="white", width=20, height=2).pack(pady=10)

        tk.Button(left, text="📤 Export Model",
                 command=lambda: self._export_model(self.zone_result, "Zone"),
                 bg="#27ae60", fg="white", width=20).pack(pady=2)

        # ===== Right plot =====
        self.zone_fig = plt.Figure(figsize=(5, 5), dpi=90)
        self.zone_fig.patch.set_facecolor('white')
        self.zone_ax = self.zone_fig.add_subplot(111)
        self.zone_ax.set_facecolor('#f8f9fa')

        self.zone_canvas = FigureCanvasTkAgg(self.zone_fig, right)
        self.zone_canvas.draw()
        self.zone_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        toolbar_frame = tk.Frame(right, height=25)
        toolbar_frame.pack(fill=tk.X)
        toolbar = NavigationToolbar2Tk(self.zone_canvas, toolbar_frame)
        toolbar.update()

    def _calculate_and_plot_zone(self):
        """Calculate and plot zone refining model"""
        self.progress.start()
        self.status_var.set("Calculating zone refining...")

        self.zone_result = self._calculate_zone_refining()
        self._plot_zone_refining(self.zone_ax, self.zone_result)
        self.zone_canvas.draw()

        self.status_var.set("✅ Zone refining complete")
        self.progress.stop()

    # ============================================================================
    # TAB 4: Mixing
    # ============================================================================
    def _create_mixing_tab(self):
        """Create mixing tab"""
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="🔄 Mixing")

        paned = tk.PanedWindow(tab, orient=tk.HORIZONTAL, sashwidth=4)
        paned.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        left = tk.Frame(paned, bg="#f5f5f5", width=300)
        paned.add(left, width=300, minsize=280)

        right = tk.Frame(paned, bg="white", width=500, height=500)
        paned.add(right, width=500, minsize=450)

        # ===== Left controls =====
        # Model type
        model_frame = tk.LabelFrame(left, text="Model Type", padx=5, pady=5, bg="#f5f5f5")
        model_frame.pack(fill=tk.X, padx=5, pady=2)

        tk.Radiobutton(model_frame, text="Binary", variable=self.mix_model_var,
                      value="binary", command=self._toggle_mixing_ui,
                      bg="#f5f5f5").pack(anchor=tk.W)
        tk.Radiobutton(model_frame, text="Ternary", variable=self.mix_model_var,
                      value="ternary", command=self._toggle_mixing_ui,
                      bg="#f5f5f5").pack(anchor=tk.W)

        # Binary parameters frame
        self.binary_frame = tk.Frame(left, bg="#f5f5f5")
        self.binary_frame.pack(fill=tk.X, padx=5, pady=2)

        binary_params = [
            ("CA (ppm):", self.mix_CA_var, 0, 10000),
            ("CB (ppm):", self.mix_CB_var, 0, 10000),
            ("fA range min:", self.mix_fA_min_var, 0, 1),
            ("fA range max:", self.mix_fA_max_var, 0, 1),
            ("Steps:", self.mix_steps_var, 10, 200)
        ]

        for label, var, minv, maxv in binary_params:
            frame = tk.Frame(self.binary_frame, bg="#f5f5f5")
            frame.pack(fill=tk.X, pady=1)
            tk.Label(frame, text=label, width=12, anchor=tk.W,
                    bg="#f5f5f5").pack(side=tk.LEFT)
            tk.Spinbox(frame, from_=minv, to=maxv, increment=0.1,
                      textvariable=var, width=8).pack(side=tk.LEFT, padx=2)

        # Ternary parameters frame (initially hidden)
        self.ternary_frame = tk.Frame(left, bg="#f5f5f5")

        ternary_params = [
            ("CA (ppm):", self.mix_CA_var, 0, 10000),
            ("CB (ppm):", self.mix_CB_var, 0, 10000),
            ("CC (ppm):", self.mix_CC_var, 0, 10000),
            ("Steps:", self.mix_steps_var, 10, 200)
        ]

        for label, var, minv, maxv in ternary_params:
            frame = tk.Frame(self.ternary_frame, bg="#f5f5f5")
            frame.pack(fill=tk.X, pady=1)
            tk.Label(frame, text=label, width=12, anchor=tk.W,
                    bg="#f5f5f5").pack(side=tk.LEFT)
            tk.Spinbox(frame, from_=minv, to=maxv, increment=0.1,
                      textvariable=var, width=8).pack(side=tk.LEFT, padx=2)

        # Calculate button
        tk.Button(left, text="🧮 Calculate Mixing",
                 command=self._calculate_and_plot_mixing,
                 bg="#e67e22", fg="white", width=20, height=2).pack(pady=10)

        tk.Button(left, text="📤 Export Model",
                 command=lambda: self._export_model(self.mix_result, "Mixing"),
                 bg="#27ae60", fg="white", width=20).pack(pady=2)

        # ===== Right plot =====
        self.mix_fig = plt.Figure(figsize=(5, 5), dpi=90)
        self.mix_fig.patch.set_facecolor('white')
        self.mix_ax = self.mix_fig.add_subplot(111)
        self.mix_ax.set_facecolor('#f8f9fa')

        self.mix_canvas = FigureCanvasTkAgg(self.mix_fig, right)
        self.mix_canvas.draw()
        self.mix_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        toolbar_frame = tk.Frame(right, height=25)
        toolbar_frame.pack(fill=tk.X)
        toolbar = NavigationToolbar2Tk(self.mix_canvas, toolbar_frame)
        toolbar.update()

    def _toggle_mixing_ui(self):
        """Toggle between binary and ternary UI"""
        if self.mix_model_var.get() == 'binary':
            self.binary_frame.pack(fill=tk.X, padx=5, pady=2)
            self.ternary_frame.pack_forget()
        else:
            self.binary_frame.pack_forget()
            self.ternary_frame.pack(fill=tk.X, padx=5, pady=2)

    def _calculate_and_plot_mixing(self):
        """Calculate and plot mixing model"""
        self.progress.start()
        self.status_var.set("Calculating mixing model...")

        self.mix_result = self._calculate_mixing()

        if self.mix_model_var.get() == 'binary':
            self._plot_binary_mixing(self.mix_ax, self.mix_result)
        else:
            self._plot_ternary_mixing(self.mix_ax, self.mix_result)

        self.mix_canvas.draw()

        self.status_var.set("✅ Mixing model complete")
        self.progress.stop()

    # ============================================================================
    # TAB 5: Comparison
    # ============================================================================
    def _create_comparison_tab(self):
        """Create comparison tab"""
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="📊 Compare")

        paned = tk.PanedWindow(tab, orient=tk.HORIZONTAL, sashwidth=4)
        paned.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        left = tk.Frame(paned, bg="#f5f5f5", width=300)
        paned.add(left, width=300, minsize=280)

        right = tk.Frame(paned, bg="white", width=500, height=500)
        paned.add(right, width=500, minsize=450)

        # ===== Left controls =====
        tk.Label(left, text="Select Elements to Compare:",
                font=("Arial", 9, "bold"), bg="#f5f5f5").pack(anchor=tk.W, padx=5, pady=5)

        # Listbox with scrollbar
        list_frame = tk.Frame(left, bg="#f5f5f5")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.compare_listbox = tk.Listbox(list_frame, height=15, selectmode=tk.MULTIPLE)
        scroll = tk.Scrollbar(list_frame, command=self.compare_listbox.yview)
        self.compare_listbox.configure(yscrollcommand=scroll.set)

        self.compare_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Buttons
        btn_frame = tk.Frame(left, bg="#f5f5f5")
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Button(btn_frame, text="📊 Compare", command=self._compare_models,
                 bg="#3498db", fg="white", width=15).pack(pady=2)

        tk.Button(btn_frame, text="📤 Export Stats",
                 command=self._export_comparison,
                 bg="#27ae60", fg="white", width=15).pack(pady=2)

        # ===== Right plot =====
        self.comp_fig = plt.Figure(figsize=(5, 5), dpi=90)
        self.comp_fig.patch.set_facecolor('white')
        self.comp_ax = self.comp_fig.add_subplot(111)
        self.comp_ax.set_facecolor('#f8f9fa')

        self.comp_canvas = FigureCanvasTkAgg(self.comp_fig, right)
        self.comp_canvas.draw()
        self.comp_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        toolbar_frame = tk.Frame(right, height=25)
        toolbar_frame.pack(fill=tk.X)
        toolbar = NavigationToolbar2Tk(self.comp_canvas, toolbar_frame)
        toolbar.update()

    def _export_comparison(self):
        """Export comparison statistics to main app"""
        if not self.compare_results:
            messagebox.showinfo("Export", "No comparison results to export")
            return

        records = []
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        for elem, stats in self.compare_results.items():
            records.append({
                'Sample_ID': f"STATS_{elem}",
                'Element': elem,
                'Mean_ppm': f"{stats['mean']:.2f}",
                'Std_ppm': f"{stats['std']:.2f}",
                'Min_ppm': f"{stats['min']:.2f}",
                'Max_ppm': f"{stats['max']:.2f}",
                'N': len(stats['values']),
                'Petrogenetic_Timestamp': timestamp
            })

        if records:
            self.app.import_data_from_plugin(records)
            self.status_var.set(f"✅ Exported {len(records)} statistics")


def setup_plugin(main_app):
    """Plugin setup function"""
    plugin = PetrogeneticSuitePlugin(main_app)
    return plugin
