"""
Materials Characterisation Right Panel
=========================================
Features:
  - Dynamic updates when rows are selected in main table
  - Scrollable interface for all content
  - Shows stress-strain curves and mechanical properties
"""

import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from .right_panel import FieldPanelBase, OK_ICON, WARN_ICON, ERROR_ICON, INFO_ICON


class MaterialsPanel(FieldPanelBase):
    PANEL_ID = "materials"
    PANEL_NAME = "Materials Characterisation"
    PANEL_ICON = "🔩"
    DETECT_COLUMNS = ['stress', 'strain', 'force', 'displacement',
                      'uts', 'yield', 'hardness', 'elongation', 'youngs']
    is_right_panel = True

    def __init__(self, parent, app):
        super().__init__(parent, app)

        # Initialize data storage
        self.stress = []
        self.strain = []
        self.uts = None
        self.yield_stress = None
        self.youngs_modulus = None
        self.elongation = None
        self.samples = []
        self.test_summary = []

        # Selection tracking
        self.selected_indices = set()

        # UI elements
        self.current_selection_label = None
        self.stress_strain_frame = None
        self.params_frame = None
        self.figures = []

        # Create scrollable container
        self._create_scrollable_container()

        # Load data and compute
        self.refresh()

    # ------------------------------------------------------------------
    # Public API called by CenterPanel
    # ------------------------------------------------------------------
    def on_selection_changed(self, selected_rows: set):
        """Called by CenterPanel when selection changes."""
        if selected_rows == self.selected_indices:
            return
        self.selected_indices = selected_rows
        self._update_for_selection()

    # ------------------------------------------------------------------
    # Scrollable container
    # ------------------------------------------------------------------
    def _create_scrollable_container(self):
        """Create a scrollable container for all content."""
        self.canvas = tk.Canvas(self.frame, borderwidth=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self._bind_mousewheel()

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        def _configure_canvas(event):
            if self.canvas.winfo_width() > 0:
                self.canvas.itemconfig(1, width=event.width)
        self.canvas.bind('<Configure>', _configure_canvas)

    def _bind_mousewheel(self):
        """Bind mouse wheel for scrolling."""
        def _on_mousewheel(event):
            if event.delta:
                self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            elif event.num == 4:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self.canvas.yview_scroll(1, "units")
            return "break"

        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        self.canvas.bind_all("<Button-4>", _on_mousewheel)
        self.canvas.bind_all("<Button-5>", _on_mousewheel)

    # ------------------------------------------------------------------
    # Selection → display routing
    # ------------------------------------------------------------------
    def _update_for_selection(self):
        """Update display based on current selection."""
        self._set_info_label()
        self._redraw_stress_strain_plot()
        self._redraw_params_table()

    def _set_info_label(self):
        """Update selection info label."""
        if not hasattr(self, 'current_selection_label') or not self.current_selection_label:
            return

        if not self.selected_indices:
            text = "Showing: ALL tests"
            color = "black"
        elif len(self.selected_indices) == 1:
            idx = next(iter(self.selected_indices))
            if idx < len(self.test_summary):
                text = f"Showing: Test {idx+1}"
                color = "blue"
            else:
                text = "Showing: Selected test"
                color = "blue"
        else:
            text = f"Showing: {len(self.selected_indices)} selected tests"
            color = "green"

        try:
            self.current_selection_label.config(text=text, foreground=color)
        except:
            pass

    def _redraw_stress_strain_plot(self):
        """Redraw stress-strain plot with current selection."""
        if not hasattr(self, 'stress_strain_frame') or not self.stress_strain_frame:
            return
        try:
            for widget in self.stress_strain_frame.winfo_children():
                widget.destroy()
            self._create_stress_strain_plot(self.stress_strain_frame)
        except:
            pass

    def _redraw_params_table(self):
        """Redraw parameters table with current selection."""
        if not hasattr(self, 'params_frame') or not self.params_frame:
            return
        try:
            for widget in self.params_frame.winfo_children():
                widget.destroy()
            self._create_parameters_table(self.params_frame)
        except:
            pass

    # ------------------------------------------------------------------
    # Data extraction
    # ------------------------------------------------------------------
    def _extract_data(self):
        """Extract mechanical testing data from samples."""
        self.stress = []
        self.strain = []
        self.uts = None
        self.yield_stress = None
        self.youngs_modulus = None
        self.elongation = None
        self.test_summary = []

        if not self.samples:
            return

        # Find columns
        stress_col = self._find_column(self.samples, 'stress', 'sigma')
        strain_col = self._find_column(self.samples, 'strain', 'epsilon')
        force_col = self._find_column(self.samples, 'force', 'load')
        disp_col = self._find_column(self.samples, 'displacement', 'disp')

        # Pre-calculated parameters
        uts_col = self._find_column(self.samples, 'uts', 'tensile_strength')
        yield_col = self._find_column(self.samples, 'yield', 'yield_strength')
        youngs_col = self._find_column(self.samples, 'youngs', 'modulus', 'e')
        elongation_col = self._find_column(self.samples, 'elongation', 'strain_at_break')

        # Extract stress-strain data
        if stress_col and strain_col:
            for i, sample in enumerate(self.samples):
                s = self._tof(sample.get(stress_col))
                e = self._tof(sample.get(strain_col))
                if s is not None and e is not None:
                    self.stress.append(s)
                    self.strain.append(e)

                    test = {
                        'index': i,
                        'id': sample.get('Sample_ID', f"Test {i+1}"),
                        'stress': s,
                        'strain': e,
                        'uts': None,
                        'yield': None,
                        'modulus': None,
                        'elongation': None,
                        'raw_data': sample
                    }
                    self.test_summary.append(test)

        # Sort by strain for proper curve
        if self.stress and self.strain:
            pairs = sorted(zip(self.strain, self.stress))
            self.strain, self.stress = zip(*pairs)

        # Extract pre-calculated parameters
        if uts_col:
            uts_vals = [self._tof(s.get(uts_col)) for s in self.samples if self._tof(s.get(uts_col)) is not None]
            self.uts = np.mean(uts_vals) if uts_vals else None

        if yield_col:
            yield_vals = [self._tof(s.get(yield_col)) for s in self.samples if self._tof(s.get(yield_col)) is not None]
            self.yield_stress = np.mean(yield_vals) if yield_vals else None

        if youngs_col:
            e_vals = [self._tof(s.get(youngs_col)) for s in self.samples if self._tof(s.get(youngs_col)) is not None]
            self.youngs_modulus = np.mean(e_vals) if e_vals else None

        if elongation_col:
            el_vals = [self._tof(s.get(elongation_col)) for s in self.samples if self._tof(s.get(elongation_col)) is not None]
            self.elongation = np.mean(el_vals) if el_vals else None

        # Calculate parameters if not provided
        if self.uts is None and self.stress:
            self.uts = max(self.stress)

        if self.youngs_modulus is None and len(self.stress) > 10:
            self._calculate_youngs_modulus()

        if self.elongation is None and self.strain:
            self.elongation = max(self.strain)

    def _calculate_youngs_modulus(self):
        """Calculate Young's modulus from elastic region."""
        if len(self.stress) < 10 or len(self.strain) < 10:
            return

        strain_array = np.array(self.strain)
        stress_array = np.array(self.stress)

        max_strain = max(strain_array)
        elastic_limit = max_strain * 0.2

        # Get elastic region data
        elastic_indices = strain_array <= elastic_limit
        if sum(elastic_indices) < 3:
            return

        e_strain = strain_array[elastic_indices]
        e_stress = stress_array[elastic_indices]

        # Linear regression
        from scipy import stats
        try:
            slope, intercept, r_value, p_value, std_err = stats.linregress(e_strain, e_stress)
            self.youngs_modulus = slope / 1000  # Convert MPa to GPa if needed
            self.modulus_r2 = r_value**2
        except:
            pass

    def _tof(self, v):
        try:
            if v is None:
                return None
            if isinstance(v, (int, float)):
                return float(v)
            if isinstance(v, str):
                v = v.strip()
                if not v or v.lower() in ['nan', 'na', 'none', 'null', '']:
                    return None
                return float(v)
            return None
        except (TypeError, ValueError):
            return None

    # ------------------------------------------------------------------
    # Base class overrides
    # ------------------------------------------------------------------
    def _calc_summary(self, samples, columns):
        """Summary statistics."""
        rows = []

        if not samples:
            rows.append(("Status", "No samples loaded"))
            return rows

        n = len(samples)
        rows.append(("N data points", str(n)))

        if self.uts:
            rows.append(("UTS", f"{self.uts:.1f} MPa"))

        if self.youngs_modulus:
            rows.append(("Young's modulus", f"{self.youngs_modulus:.1f} GPa"))

        if self.elongation:
            rows.append(("Elongation", f"{self.elongation*100:.1f}%"))

        if self.yield_stress:
            rows.append(("Yield strength", f"{self.yield_stress:.1f} MPa"))

        return rows

    def _calc_validation(self, samples, columns):
        """Data validation."""
        rows = []

        if not samples:
            rows.append((WARN_ICON, "No data"))
            return rows

        # Check for required columns
        stress_col = self._find_column(samples, 'stress')
        strain_col = self._find_column(samples, 'strain')

        if stress_col:
            rows.append((OK_ICON, f"Stress column: {stress_col}"))
        else:
            rows.append((INFO_ICON, "No stress column"))

        if strain_col:
            rows.append((OK_ICON, f"Strain column: {strain_col}"))
        else:
            rows.append((INFO_ICON, "No strain column"))

        # Validate values
        if self.stress:
            neg_stress = sum(1 for v in self.stress if v < 0)
            if neg_stress == 0:
                rows.append((OK_ICON, "All stress ≥0"))
            else:
                rows.append((WARN_ICON, f"{neg_stress} negative stress"))

        if self.strain:
            neg_strain = sum(1 for v in self.strain if v < 0)
            if neg_strain == 0:
                rows.append((OK_ICON, "All strain ≥0"))
            else:
                rows.append((WARN_ICON, f"{neg_strain} negative strain"))

        return rows

    def _calc_quick(self, samples, columns):
        """Quick calculations."""
        rows = []

        if self.youngs_modulus:
            rows.append(("Young's modulus", f"{self.youngs_modulus:.1f} GPa"))

        if self.uts:
            rows.append(("UTS", f"{self.uts:.1f} MPa"))

        if self.yield_stress:
            rows.append(("Yield strength", f"{self.yield_stress:.1f} MPa"))

        if self.elongation:
            rows.append(("Elongation", f"{self.elongation*100:.1f}%"))

        # Toughness (area under curve)
        if len(self.stress) > 1 and len(self.strain) > 1:
            try:
                toughness = np.trapz(self.stress, self.strain)
                rows.append(("Toughness", f"{toughness:.2f} MJ/m³"))
            except:
                pass

        return rows

    # ------------------------------------------------------------------
    # Custom UI elements
    # ------------------------------------------------------------------
    def _add_custom_widgets(self):
        """Add custom widgets to the scrollable frame."""
        container = self.scrollable_frame

        # Selection info label
        info_frame = ttk.Frame(container)
        info_frame.pack(fill=tk.X, padx=5, pady=5)

        self.current_selection_label = ttk.Label(
            info_frame,
            text="Select rows in main table to filter tests",
            font=("Segoe UI", 9, "italic")
        )
        self.current_selection_label.pack(side=tk.LEFT)

        # Stress-strain plot
        self.stress_strain_frame = ttk.Frame(container)
        self.stress_strain_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self._create_stress_strain_plot(self.stress_strain_frame)

        # Parameters table
        self.params_frame = ttk.Frame(container)
        self.params_frame.pack(fill="x", padx=5, pady=5)
        self._create_parameters_table(self.params_frame)

        # Data table
        self._create_data_table(container)

    def _create_stress_strain_plot(self, parent):
        """Create stress-strain curve plot."""
        frame = ttk.LabelFrame(parent, text="Stress-Strain Curve", padding=10)
        frame.pack(fill="both", expand=True)

        fig = Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)

        ax.set_xlabel("Strain")
        ax.set_ylabel("Stress (MPa)")
        ax.set_title("Tensile Test")
        ax.grid(True, linestyle=':', alpha=0.6)

        # Filter data based on selection
        strains = []
        stresses = []

        indices = self.selected_indices if self.selected_indices else range(len(self.test_summary))

        for idx in indices:
            if idx >= len(self.test_summary):
                continue
            test = self.test_summary[idx]
            strains.append(test['strain'])
            stresses.append(test['stress'])

        if strains and stresses:
            ax.plot(strains, stresses, 'b-', linewidth=2, label='Stress-Strain')

            # Mark UTS
            if self.uts:
                idx = np.argmax(stresses)
                ax.plot(strains[idx], stresses[idx], 'ro', markersize=8, label='UTS')
                ax.annotate(f'UTS: {self.uts:.0f} MPa',
                           (strains[idx], stresses[idx]),
                           xytext=(10, 10), textcoords='offset points')

            # Show elastic region
            if self.youngs_modulus:
                max_strain = max(strains) * 0.2
                e_strain = np.linspace(0, max_strain, 100)
                e_stress = self.youngs_modulus * 1000 * e_strain
                ax.plot(e_strain, e_stress, 'r--', linewidth=1,
                       label=f'E = {self.youngs_modulus:.1f} GPa')

            ax.legend(loc='lower right')
        else:
            ax.text(0.5, 0.5, "No stress-strain data", ha='center', va='center',
                   transform=ax.transAxes, fontsize=12)

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.figures.append(fig)

    def _create_parameters_table(self, parent):
        """Create table of mechanical properties."""
        frame = ttk.LabelFrame(parent, text="Mechanical Properties", padding=10)
        frame.pack(fill="x")

        # Create a grid of parameters
        params_frame = ttk.Frame(frame)
        params_frame.pack(fill="x")

        properties = [
            ("Young's modulus", f"{self.youngs_modulus:.1f} GPa" if self.youngs_modulus else "N/A"),
            ("UTS", f"{self.uts:.1f} MPa" if self.uts else "N/A"),
            ("Yield strength", f"{self.yield_stress:.1f} MPa" if self.yield_stress else "N/A"),
            ("Elongation", f"{self.elongation*100:.1f}%" if self.elongation else "N/A"),
        ]

        for i, (prop, value) in enumerate(properties):
            row = ttk.Frame(params_frame)
            row.pack(fill="x", pady=2)

            ttk.Label(row, text=f"{prop}:", font=("Segoe UI", 9, "bold"),
                     width=20, anchor="w").pack(side=tk.LEFT, padx=5)
            ttk.Label(row, text=value, width=15, anchor="w").pack(side=tk.LEFT, padx=5)

    def _create_data_table(self, parent):
        """Create table of test data."""
        frame = ttk.LabelFrame(parent, text="Test Data", padding=10)
        frame.pack(fill="x", padx=5, pady=5)

        cols = ["ID", "Stress", "Strain"]
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=6)

        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor="center")

        # Filter data based on selection
        indices = self.selected_indices if self.selected_indices else range(len(self.test_summary))

        for i in sorted(indices)[:20]:  # Limit to 20 rows
            if i >= len(self.test_summary):
                continue

            test = self.test_summary[i]

            tid = test['id'][:10]
            stress = f"{test['stress']:.1f}" if test['stress'] is not None else "-"
            strain = f"{test['strain']:.3f}" if test['strain'] is not None else "-"

            tree.insert("", "end", values=(tid, stress, strain))

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind click to select main table row
        tree.bind('<ButtonRelease-1>', lambda e: self._on_table_click(e, tree))
        self.data_tree = tree

    def _on_table_click(self, event, tree):
        """Handle click on data table → select matching row in main table."""
        item = tree.identify_row(event.y)
        if not item:
            return
        try:
            idx = int(tree.index(item))
            if idx < len(self.test_summary):
                hub_idx = self.test_summary[idx]['index']
                if hasattr(self.app, 'center') and hasattr(self.app.center, 'selected_rows'):
                    self.app.center.selected_rows = {hub_idx}
                    if hasattr(self.app.center, '_refresh'):
                        self.app.center._refresh()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------
    def refresh(self):
        """Reload data and rebuild the entire panel UI."""
        self.samples = self.app.data_hub.get_all() if hasattr(self.app, 'data_hub') else []
        self._extract_data()

        # Rebuild base section widgets
        super().refresh()

        # Rebuild custom widgets
        if hasattr(self, 'scrollable_frame'):
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()
            self._add_custom_widgets()

        # Re-apply current selection
        self._update_for_selection()
