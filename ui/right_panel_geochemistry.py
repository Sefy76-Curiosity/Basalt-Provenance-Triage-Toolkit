"""
Geochemistry Right Panel
==========================
Features:
  - Dynamic updates when rows are selected in main table
  - Scrollable interface for all content
  - Shows TAS diagram, AFM diagram, and derived values
"""

import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from .right_panel import FieldPanelBase, OK_ICON, WARN_ICON, ERROR_ICON

# TAS classification fields (Le Bas et al. 1986)
TAS_FIELDS = {
    'Foidolite': [(41, 0), (41, 8), (45, 5), (45, 0)],
    'Phonolite': [(45, 8), (45, 14), (52, 14), (52, 9)],
    'Tephrite Phonolite': [(41, 5), (41, 8), (45, 9), (45, 5)],
    'Phonolitic Tephrite': [(41, 0), (41, 5), (45, 5), (45, 0)],
    'Trachyte': [(52, 9), (52, 14), (63, 14), (63, 7)],
    'Trachyandesite': [(52, 5), (52, 9), (57, 9), (57, 5)],
    'Basaltic Trachyandesite': [(45, 5), (45, 9), (52, 9), (52, 5)],
    'Basalt': [(45, 0), (45, 5), (52, 5), (52, 0)],
    'Andesite': [(52, 0), (52, 5), (57, 5), (57, 0)],
    'Dacite': [(57, 0), (57, 7), (63, 7), (63, 0)],
    'Rhyolite': [(63, 0), (63, 7), (70, 7), (70, 0)],
}


class GeochemistryPanel(FieldPanelBase):
    PANEL_ID = "geochemistry"
    PANEL_NAME = "Geochemistry"
    PANEL_ICON = "🪨"
    DETECT_COLUMNS = ['sio2', 'tio2', 'al2o3', 'fe2o3', 'mgo', 'cao', 'na2o', 'k2o']
    is_right_panel = True
    _MAJOR_OXIDES = ['sio2', 'tio2', 'al2o3', 'fe2o3', 'feo', 'mgo', 'mno', 'cao', 'na2o', 'k2o', 'p2o5']

    def __init__(self, parent, app):
        super().__init__(parent, app)

        # Initialize data storage
        self.derived_data = []
        self.samples = []
        self.sample_summary = []

        # Selection tracking
        self.selected_indices = set()

        # UI elements
        self.current_selection_label = None
        self.tas_frame = None
        self.afm_frame = None
        self.mg_hist_frame = None
        self.figures = []

        # Create scrollable container
        self._create_scrollable_container()

        # Force an immediate refresh to populate data
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
        self._redraw_tas_diagram()
        self._redraw_afm_diagram()
        self._redraw_mg_histogram()

    def _set_info_label(self):
        """Update selection info label."""
        if not hasattr(self, 'current_selection_label') or not self.current_selection_label:
            return

        if not self.selected_indices:
            text = "Showing: ALL samples"
            color = "black"
        elif len(self.selected_indices) == 1:
            idx = next(iter(self.selected_indices))
            if idx < len(self.sample_summary):
                text = f"Showing: Sample {idx+1}"
                color = "blue"
            else:
                text = "Showing: Selected sample"
                color = "blue"
        else:
            text = f"Showing: {len(self.selected_indices)} selected samples"
            color = "green"

        try:
            self.current_selection_label.config(text=text, foreground=color)
        except:
            pass

    def _redraw_tas_diagram(self):
        """Redraw TAS diagram with current selection."""
        if not hasattr(self, 'tas_frame') or not self.tas_frame:
            return
        try:
            for widget in self.tas_frame.winfo_children():
                widget.destroy()
            self._create_tas_diagram(self.tas_frame)
        except:
            pass

    def _redraw_afm_diagram(self):
        """Redraw AFM diagram with current selection."""
        if not hasattr(self, 'afm_frame') or not self.afm_frame:
            return
        try:
            for widget in self.afm_frame.winfo_children():
                widget.destroy()
            self._create_afm_diagram(self.afm_frame)
        except:
            pass

    def _redraw_mg_histogram(self):
        """Redraw Mg# histogram with current selection."""
        if not hasattr(self, 'mg_hist_frame') or not self.mg_hist_frame:
            return
        try:
            for widget in self.mg_hist_frame.winfo_children():
                widget.destroy()
            self._create_mg_histogram(self.mg_hist_frame)
        except:
            pass

    # ------------------------------------------------------------------
    # Data extraction
    # ------------------------------------------------------------------
    def _update_samples(self):
        """Get samples from data hub."""
        try:
            self.samples = self.app.data_hub.get_all()
        except Exception:
            self.samples = []

    def _compute_derived_values(self):
        """Compute FeOt, Mg#, Na2O+K2O, and anhydrous totals."""
        self.derived_data = []
        self.sample_summary = []

        if not self.samples:
            return

        for i, sample in enumerate(self.samples):
            # Get oxide values
            oxides = {}

            # Common oxide patterns
            oxide_patterns = {
                'sio2': ['sio2', 'sio', 'sio2_wt', 'sio2_pct', 'sio2_%', 'sio2%', 'sio2_wt%'],
                'tio2': ['tio2', 'tio', 'tio2_wt', 'tio2_pct', 'tio2_%', 'tio2%'],
                'al2o3': ['al2o3', 'al2o3_wt', 'al2o3_pct', 'al2o3_%', 'al2o3%', 'al2o3_wt%'],
                'fe2o3': ['fe2o3', 'fe2o3_wt', 'fe2o3_pct', 'fe_iii', 'ferric'],
                'feo': ['feo', 'feo_wt', 'feo_pct', 'fe_ii', 'ferrous'],
                'mgo': ['mgo', 'mgo_wt', 'mgo_pct', 'mg_o'],
                'cao': ['cao', 'cao_wt', 'cao_pct', 'ca_o'],
                'na2o': ['na2o', 'na2o_wt', 'na2o_pct', 'na_o', 'sodium_oxide'],
                'k2o': ['k2o', 'k2o_wt', 'k2o_pct', 'k_o', 'potassium_oxide'],
                'p2o5': ['p2o5', 'p2o5_wt', 'p2o5_pct', 'p_o'],
                'mno': ['mno', 'mno_wt', 'mno_pct', 'mn_o']
            }

            for oxide, patterns in oxide_patterns.items():
                for pattern in patterns:
                    found = False
                    for col in sample:
                        if pattern in col.lower():
                            val = self._tof(sample[col])
                            if val is not None:
                                oxides[oxide] = val
                                found = True
                                break
                    if found:
                        break

            # Get LOI
            loi = None
            for pattern in ['loi', 'loss_on_ignition', 'loss_on_ign', 'LOI', 'Loss_on_Ignition']:
                for col in sample:
                    if pattern.lower() in col.lower():
                        loi = self._tof(sample[col])
                        if loi is not None:
                            break
                if loi is not None:
                    break

            # FeOt = FeO + 0.8998 * Fe2O3
            feo = oxides.get('feo')
            fe2o3 = oxides.get('fe2o3')
            feot = None
            if feo is not None or fe2o3 is not None:
                feot = (feo if feo is not None else 0) + 0.8998 * (fe2o3 if fe2o3 is not None else 0)

            # Mg# = 100 * (MgO/40.3044) / (MgO/40.3044 + FeOt/71.844)
            mgo = oxides.get('mgo')
            mg_num = None
            if mgo is not None and feot is not None and feot >= 0:
                mg_mol = mgo / 40.3044
                fe_mol = feot / 71.844
                denom = mg_mol + fe_mol
                if denom > 0:
                    mg_num = 100 * mg_mol / denom

            # Alkali sum
            na2o = oxides.get('na2o')
            k2o = oxides.get('k2o')
            alk_sum = None
            if na2o is not None and k2o is not None:
                alk_sum = na2o + k2o

            # Anhydrous total
            anhydrous_total = 0.0
            for ox in ['sio2', 'tio2', 'al2o3', 'fe2o3', 'feo', 'mgo', 'mno', 'cao', 'na2o', 'k2o', 'p2o5']:
                val = oxides.get(ox)
                if val is not None:
                    anhydrous_total += val

            # Raw total including LOI
            raw_total = anhydrous_total
            if loi is not None:
                raw_total += loi

            derived = {
                'sample': sample,
                'sample_index': i,
                'id': sample.get('Sample_ID', f"Sample {i+1}"),
                'feot': feot,
                'mg_num': mg_num,
                'alk_sum': alk_sum,
                'anhydrous_total': anhydrous_total if anhydrous_total > 0 else None,
                'raw_total': raw_total if raw_total > 0 else None,
                'loi': loi,
                'oxides': oxides,
                'sio2': oxides.get('sio2')
            }

            self.derived_data.append(derived)
            self.sample_summary.append(derived)

    # ------------------------------------------------------------------
    # Data processing helpers
    # ------------------------------------------------------------------
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
        """Summary KPI cards."""
        rows = []

        if not samples:
            rows.append(("Status", "No samples loaded"))
            return rows

        n = len(samples)
        rows.append(("N samples", str(n)))

        # Try to find SiO2 values
        sio2_vals = []
        for d in self.derived_data:
            if d['sio2'] is not None:
                sio2_vals.append(d['sio2'])

        if sio2_vals:
            rows.append(("SiO₂ range", f"{min(sio2_vals):.1f}–{max(sio2_vals):.1f} wt%"))
            rows.append(("Mean SiO₂", f"{np.mean(sio2_vals):.1f} wt%"))
        else:
            rows.append(("SiO₂", "Not found"))

        # Totals
        totals = [d['raw_total'] for d in self.derived_data if d['raw_total'] is not None]
        if totals:
            rows.append(("Mean total", f"{np.mean(totals):.1f} wt%"))

        # Mg#
        mg_nums = [d['mg_num'] for d in self.derived_data if d['mg_num'] is not None]
        if mg_nums:
            rows.append(("Mg# range", f"{min(mg_nums):.1f}–{max(mg_nums):.1f}"))

        return rows

    def _calc_validation(self, samples, columns):
        """Data validation."""
        rows = []

        if not samples:
            rows.append((WARN_ICON, "No data"))
            return rows

        # Check for oxide columns
        oxide_cols_found = set()
        for s in samples[:5]:
            for col in s:
                col_lower = col.lower()
                for ox in ['sio2', 'tio2', 'al2o3', 'fe2o3', 'feo', 'mgo', 'cao', 'na2o', 'k2o']:
                    if ox in col_lower:
                        oxide_cols_found.add(ox)

        if oxide_cols_found:
            rows.append((OK_ICON, f"Found {len(oxide_cols_found)} oxide types"))
        else:
            rows.append((WARN_ICON, "No oxide columns found"))

        # Check if we could compute any derived values
        if self.derived_data:
            computed = sum(1 for d in self.derived_data if d['feot'] is not None or d['mg_num'] is not None)
            if computed > 0:
                rows.append((OK_ICON, f"Computed values for {computed} samples"))
            else:
                rows.append((WARN_ICON, "Could not compute values"))

        return rows

    def _calc_quick(self, samples, columns):
        """Quick calculations."""
        rows = []

        if not self.derived_data:
            rows.append(("Status", "No data"))
            return rows

        # Calculate means
        feots = [d['feot'] for d in self.derived_data if d['feot'] is not None]
        mg_nums = [d['mg_num'] for d in self.derived_data if d['mg_num'] is not None]
        alk_sums = [d['alk_sum'] for d in self.derived_data if d['alk_sum'] is not None]

        if feots:
            rows.append(("Mean FeOt", f"{np.mean(feots):.2f} wt%"))
        if mg_nums:
            rows.append(("Mean Mg#", f"{np.mean(mg_nums):.1f}"))
        if alk_sums:
            rows.append(("Mean Na₂O+K₂O", f"{np.mean(alk_sums):.2f} wt%"))

        if not rows:
            rows.append(("Status", "No calculated values"))

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
            text="Select rows in main table to filter samples",
            font=("Segoe UI", 9, "italic")
        )
        self.current_selection_label.pack(side=tk.LEFT)

        # Derived values table
        self._create_derived_table(container)

        # TAS diagram
        self.tas_frame = ttk.Frame(container)
        self.tas_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self._create_tas_diagram(self.tas_frame)

        # AFM diagram
        self.afm_frame = ttk.Frame(container)
        self.afm_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self._create_afm_diagram(self.afm_frame)

        # Mg# histogram
        self.mg_hist_frame = ttk.Frame(container)
        self.mg_hist_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self._create_mg_histogram(self.mg_hist_frame)

    def _create_derived_table(self, parent):
        """Create a table showing derived values per sample."""
        frame = ttk.LabelFrame(parent, text="Derived Values", padding=10)
        frame.pack(fill="x", padx=5, pady=5)

        # Create treeview
        cols = ["Sample", "FeOt", "Mg#", "Na₂O+K₂O", "Total"]
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=6)

        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=80, anchor="center")

        # Filter data based on selection
        indices = self.selected_indices if self.selected_indices else range(len(self.sample_summary))

        for i in sorted(indices)[:20]:  # Limit to 20 rows for display
            if i >= len(self.sample_summary):
                continue

            d = self.sample_summary[i]

            sample_id = d['id']
            if len(sample_id) > 10:
                sample_id = sample_id[:8] + "…"

            feot = f"{d['feot']:.2f}" if d['feot'] is not None else "-"
            mg = f"{d['mg_num']:.1f}" if d['mg_num'] is not None else "-"
            alk = f"{d['alk_sum']:.2f}" if d['alk_sum'] is not None else "-"
            total = f"{d['raw_total']:.1f}" if d['raw_total'] is not None else "-"

            tree.insert("", "end", values=(sample_id, feot, mg, alk, total))

        # Add scrollbar
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind click to select main table row
        tree.bind('<ButtonRelease-1>', lambda e: self._on_table_click(e, tree))
        self.derived_tree = tree

    def _create_tas_diagram(self, parent):
        """Create TAS diagram."""
        frame = ttk.LabelFrame(parent, text="TAS Diagram (Le Bas 1986)", padding=10)
        frame.pack(fill="both", expand=True)

        # Collect data based on selection
        sio2_vals = []
        alk_vals = []

        indices = self.selected_indices if self.selected_indices else range(len(self.sample_summary))

        for idx in indices:
            if idx >= len(self.sample_summary):
                continue

            d = self.sample_summary[idx]
            if d['alk_sum'] is None or d['sio2'] is None:
                continue

            sio2_vals.append(d['sio2'])
            alk_vals.append(d['alk_sum'])

        fig = Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)
        ax.set_xlabel("SiO₂ (wt%)")
        ax.set_ylabel("Na₂O + K₂O (wt%)")
        ax.set_xlim(40, 75)
        ax.set_ylim(0, 15)
        ax.set_title("Total Alkali vs. Silica")
        ax.grid(True, linestyle=':', alpha=0.6)

        # Draw TAS fields
        for name, poly in TAS_FIELDS.items():
            x, y = zip(*poly)
            ax.fill(x, y, alpha=0.2, label='_nolegend_')

        # Plot samples
        if sio2_vals and alk_vals:
            if self.selected_indices:
                ax.scatter(sio2_vals, alk_vals, c='red', edgecolors='black', s=50, zorder=5, label='Selected')
            else:
                ax.scatter(sio2_vals, alk_vals, c='blue', edgecolors='black', s=50, zorder=5, alpha=0.7, label='All')
            ax.legend()
        else:
            ax.text(0.5, 0.5, "No data to plot", ha='center', va='center', transform=ax.transAxes)

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.figures.append(fig)

    def _create_afm_diagram(self, parent):
        """Create AFM diagram."""
        frame = ttk.LabelFrame(parent, text="AFM Diagram", padding=10)
        frame.pack(fill="both", expand=True)

        # Collect data based on selection
        points = []

        indices = self.selected_indices if self.selected_indices else range(len(self.sample_summary))

        for idx in indices:
            if idx >= len(self.sample_summary):
                continue

            d = self.sample_summary[idx]
            if d['feot'] is None or d['alk_sum'] is None:
                continue

            # Find MgO in sample
            mgo = d['oxides'].get('mgo')
            if mgo is not None:
                points.append((d['alk_sum'], d['feot'], mgo))

        fig = Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)

        if points:
            # Convert to percentages
            F_vals = []
            M_vals = []
            for a, f, m in points:
                total = a + f + m
                if total > 0:
                    F_vals.append(f/total*100)
                    M_vals.append(m/total*100)

            if self.selected_indices:
                ax.scatter(F_vals, M_vals, c='red', edgecolors='black', s=50, alpha=0.7, label='Selected')
            else:
                ax.scatter(F_vals, M_vals, c='blue', edgecolors='black', s=50, alpha=0.7, label='All')

            ax.set_xlabel("FeOₜ (%)")
            ax.set_ylabel("MgO (%)")
            ax.set_title("AFM Diagram")
            ax.set_xlim(0, 100)
            ax.set_ylim(0, 100)

            # Add Irvine & Baragar line approximation
            x_line = [30, 80]
            y_line = [50, 10]
            ax.plot(x_line, y_line, 'r--', linewidth=2, label='Tholeiitic/Calc-alkaline')
            ax.legend()
        else:
            ax.text(0.5, 0.5, "No data to plot", ha='center', va='center', transform=ax.transAxes)

        ax.grid(True, linestyle=':', alpha=0.6)
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.figures.append(fig)

    def _create_mg_histogram(self, parent):
        """Create Mg# histogram."""
        frame = ttk.LabelFrame(parent, text="Mg# Distribution", padding=10)
        frame.pack(fill="both", expand=True)

        # Collect data based on selection
        mg_nums = []

        indices = self.selected_indices if self.selected_indices else range(len(self.sample_summary))

        for idx in indices:
            if idx >= len(self.sample_summary):
                continue

            d = self.sample_summary[idx]
            if d['mg_num'] is not None:
                mg_nums.append(d['mg_num'])

        fig = Figure(figsize=(5, 3), dpi=100)
        ax = fig.add_subplot(111)
        ax.set_xlabel("Mg#")
        ax.set_ylabel("Frequency")
        ax.set_title("Magnesium Number Distribution")
        ax.grid(True, linestyle=':', alpha=0.6)

        if mg_nums:
            ax.hist(mg_nums, bins=10, edgecolor='black', alpha=0.7, color='steelblue')

            # Add statistics
            stats = f"n={len(mg_nums)}\nμ={np.mean(mg_nums):.1f}\nσ={np.std(mg_nums):.1f}"
            ax.text(0.95, 0.95, stats, transform=ax.transAxes,
                   fontsize=8, verticalalignment='top', horizontalalignment='right',
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        else:
            ax.text(0.5, 0.5, "No Mg# data", ha='center', va='center', transform=ax.transAxes)

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.figures.append(fig)

    def _on_table_click(self, event, tree):
        """Handle click on derived table → select matching row in main table."""
        item = tree.identify_row(event.y)
        if not item:
            return
        try:
            idx = int(tree.index(item))
            if idx < len(self.sample_summary):
                hub_idx = self.sample_summary[idx]['sample_index']
                if hasattr(self.app, 'center') and hasattr(self.app.center, 'selected_rows'):
                    self.app.center.selected_rows = {hub_idx}
                    if hasattr(self.app.center, '_refresh'):
                        self.app.center._refresh()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Refresh method
    # ------------------------------------------------------------------
    def refresh(self):
        """Refresh all data and rebuild UI."""
        self._update_samples()
        self._compute_derived_values()

        # Let the base class handle its sections
        super().refresh()

        # Rebuild custom UI
        if hasattr(self, 'scrollable_frame'):
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()
            self._add_custom_widgets()

        # Re-apply current selection
        self._update_for_selection()
