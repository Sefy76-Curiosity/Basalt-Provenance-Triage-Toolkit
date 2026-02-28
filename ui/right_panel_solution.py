"""
Solution / Water Chemistry Right Panel
========================================
Features:
  - Dynamic updates when rows are selected in main table
  - Scrollable interface for all content
  - Shows ion concentrations and water classification diagrams
"""

import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from .right_panel import FieldPanelBase, OK_ICON, WARN_ICON, ERROR_ICON, INFO_ICON

# Equivalent weights (g/eq) for common ions
_EW = {
    'ca': 20.04, 'mg': 12.15, 'na': 22.99, 'k': 39.10,
    'hco3': 61.02, 'co3': 30.00, 'so4': 48.03, 'cl': 35.45, 'no3': 62.00,
}


class SolutionPanel(FieldPanelBase):
    PANEL_ID = "solution"
    PANEL_NAME = "Solution Chemistry"
    PANEL_ICON = "💧"
    DETECT_COLUMNS = ['ph', 'ec', 'tds', 'ca', 'mg', 'na', 'k',
                      'hco3', 'alkalinity', 'so4', 'cl', 'no3']
    is_right_panel = True

    def __init__(self, parent, app):
        super().__init__(parent, app)

        # Initialize data storage
        self.ph_vals = []
        self.ec_vals = []
        self.tds_vals = []
        self.cations = {'ca': [], 'mg': [], 'na': [], 'k': []}
        self.anions = {'hco3': [], 'co3': [], 'so4': [], 'cl': [], 'no3': []}
        self.cbe_vals = []
        self.hardness_vals = []
        self.samples = []
        self.sample_summary = []

        # Selection tracking
        self.selected_indices = set()

        # UI elements
        self.current_selection_label = None
        self.piper_frame = None
        self.ion_bar_frame = None
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
        self._redraw_piper_diagram()
        self._redraw_ion_bar_chart()

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
                text = f"Showing: Sample {self.sample_summary[idx].get('id', idx+1)}"
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

    def _redraw_piper_diagram(self):
        """Redraw Piper diagram with current selection."""
        if not hasattr(self, 'piper_frame') or not self.piper_frame:
            return
        try:
            for widget in self.piper_frame.winfo_children():
                widget.destroy()
            self._create_piper_diagram(self.piper_frame)
        except:
            pass

    def _redraw_ion_bar_chart(self):
        """Redraw ion bar chart with current selection."""
        if not hasattr(self, 'ion_bar_frame') or not self.ion_bar_frame:
            return
        try:
            for widget in self.ion_bar_frame.winfo_children():
                widget.destroy()
            self._create_ion_bar_chart(self.ion_bar_frame)
        except:
            pass

    # ------------------------------------------------------------------
    # Data extraction
    # ------------------------------------------------------------------
    def _extract_data(self):
        """Extract water chemistry data from samples."""
        self.ph_vals = []
        self.ec_vals = []
        self.tds_vals = []
        for ion in self.cations:
            self.cations[ion] = []
        for ion in self.anions:
            self.anions[ion] = []
        self.cbe_vals = []
        self.hardness_vals = []
        self.sample_summary = []

        if not self.samples:
            return

        # Find columns
        ph_col = self._find_column(self.samples, 'ph')
        ec_col = self._find_column(self.samples, 'ec', 'conductivity')
        tds_col = self._find_column(self.samples, 'tds', 'total_dissolved')

        # Cation columns
        ca_col = self._find_column(self.samples, 'ca')
        mg_col = self._find_column(self.samples, 'mg')
        na_col = self._find_column(self.samples, 'na')
        k_col = self._find_column(self.samples, 'k')

        # Anion columns
        hco3_col = self._find_column(self.samples, 'hco3', 'bicarbonate')
        co3_col = self._find_column(self.samples, 'co3', 'carbonate')
        so4_col = self._find_column(self.samples, 'so4', 'sulfate')
        cl_col = self._find_column(self.samples, 'cl', 'chloride')
        no3_col = self._find_column(self.samples, 'no3', 'nitrate')

        for i, sample in enumerate(self.samples):
            sample_info = {
                'index': i,
                'id': sample.get('Sample_ID', f"Sample {i+1}"),
                'ph': None,
                'ec': None,
                'tds': None,
                'cations': {},
                'anions': {},
                'cbe': None,
                'hardness': None,
                'raw_data': sample
            }

            # Basic parameters
            if ph_col:
                ph = self._tof(sample.get(ph_col))
                if ph is not None:
                    self.ph_vals.append(ph)
                    sample_info['ph'] = ph

            if ec_col:
                ec = self._tof(sample.get(ec_col))
                if ec is not None:
                    self.ec_vals.append(ec)
                    sample_info['ec'] = ec

            if tds_col:
                tds = self._tof(sample.get(tds_col))
                if tds is not None:
                    self.tds_vals.append(tds)
                    sample_info['tds'] = tds

            # Cations (mg/L)
            if ca_col:
                ca = self._tof(sample.get(ca_col))
                if ca is not None:
                    self.cations['ca'].append(ca)
                    sample_info['cations']['ca'] = ca

            if mg_col:
                mg = self._tof(sample.get(mg_col))
                if mg is not None:
                    self.cations['mg'].append(mg)
                    sample_info['cations']['mg'] = mg

            if na_col:
                na = self._tof(sample.get(na_col))
                if na is not None:
                    self.cations['na'].append(na)
                    sample_info['cations']['na'] = na

            if k_col:
                k = self._tof(sample.get(k_col))
                if k is not None:
                    self.cations['k'].append(k)
                    sample_info['cations']['k'] = k

            # Anions (mg/L)
            if hco3_col:
                hco3 = self._tof(sample.get(hco3_col))
                if hco3 is not None:
                    self.anions['hco3'].append(hco3)
                    sample_info['anions']['hco3'] = hco3

            if co3_col:
                co3 = self._tof(sample.get(co3_col))
                if co3 is not None:
                    self.anions['co3'].append(co3)
                    sample_info['anions']['co3'] = co3

            if so4_col:
                so4 = self._tof(sample.get(so4_col))
                if so4 is not None:
                    self.anions['so4'].append(so4)
                    sample_info['anions']['so4'] = so4

            if cl_col:
                cl = self._tof(sample.get(cl_col))
                if cl is not None:
                    self.anions['cl'].append(cl)
                    sample_info['anions']['cl'] = cl

            if no3_col:
                no3 = self._tof(sample.get(no3_col))
                if no3 is not None:
                    self.anions['no3'].append(no3)
                    sample_info['anions']['no3'] = no3

            self.sample_summary.append(sample_info)

        # Calculate derived parameters
        self._calculate_cbe()
        self._calculate_hardness()

    def _calculate_cbe(self):
        """Calculate Charge Balance Error for each sample."""
        self.cbe_vals = []

        for i, sample_info in enumerate(self.sample_summary):
            cations_meq = 0.0
            anions_meq = 0.0

            # Sum cations (meq/L)
            for ion, value in sample_info['cations'].items():
                cations_meq += value / _EW.get(ion, 1)

            # Sum anions (meq/L)
            for ion, value in sample_info['anions'].items():
                anions_meq += value / _EW.get(ion, 1)

            total = cations_meq + anions_meq
            if total > 0:
                cbe = 100 * (cations_meq - anions_meq) / total
                self.cbe_vals.append(cbe)
                sample_info['cbe'] = cbe

    def _calculate_hardness(self):
        """Calculate total hardness as mg/L CaCO3."""
        self.hardness_vals = []

        for i, sample_info in enumerate(self.sample_summary):
            ca = sample_info['cations'].get('ca', 0)
            mg = sample_info['cations'].get('mg', 0)

            if ca > 0 or mg > 0:
                # Hardness = (Ca/20.04 + Mg/12.15) * 50.045
                hardness = (ca/20.04 + mg/12.15) * 50.045
                self.hardness_vals.append(hardness)
                sample_info['hardness'] = hardness

    def _get_hardness_class(self, hardness):
        """Classify water hardness."""
        if hardness < 75:
            return "Soft"
        elif hardness < 150:
            return "Moderately hard"
        elif hardness < 300:
            return "Hard"
        else:
            return "Very hard"

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
        rows.append(("N samples", str(n)))

        if self.ph_vals:
            rows.append(("pH range", f"{min(self.ph_vals):.2f}-{max(self.ph_vals):.2f}"))
            rows.append(("Mean pH", f"{np.mean(self.ph_vals):.2f}"))

        if self.tds_vals:
            rows.append(("TDS range", f"{min(self.tds_vals):.0f}-{max(self.tds_vals):.0f} mg/L"))
            rows.append(("Mean TDS", f"{np.mean(self.tds_vals):.0f} mg/L"))

        if self.ec_vals:
            rows.append(("Mean EC", f"{np.mean(self.ec_vals):.0f} µS/cm"))

        return rows

    def _calc_validation(self, samples, columns):
        """Data validation."""
        rows = []

        if not samples:
            rows.append((WARN_ICON, "No data"))
            return rows

        # Check pH
        if self.ph_vals:
            bad_ph = sum(1 for v in self.ph_vals if not (0 <= v <= 14))
            if bad_ph == 0:
                rows.append((OK_ICON, "All pH values valid"))
            else:
                rows.append((ERROR_ICON, f"{bad_ph} pH out of range"))
        else:
            rows.append((INFO_ICON, "No pH data"))

        # Check CBE
        if self.cbe_vals:
            bad_cbe = sum(1 for v in self.cbe_vals if abs(v) > 5)
            if bad_cbe == 0:
                rows.append((OK_ICON, "All CBE ≤5%"))
            else:
                rows.append((WARN_ICON, f"{bad_cbe} samples CBE >5%"))

            mean_cbe = np.mean(self.cbe_vals)
            rows.append((INFO_ICON, f"Mean CBE: {mean_cbe:.2f}%"))
        else:
            rows.append((INFO_ICON, "Insufficient ions for CBE"))

        return rows

    def _calc_quick(self, samples, columns):
        """Quick calculations."""
        rows = []

        # Mean CBE
        if self.cbe_vals:
            rows.append(("Mean CBE", f"{np.mean(self.cbe_vals):.2f}%"))

        # Hardness
        if self.hardness_vals:
            mean_hardness = np.mean(self.hardness_vals)
            hardness_class = self._get_hardness_class(mean_hardness)
            rows.append(("Mean hardness", f"{mean_hardness:.0f} mg/L CaCO3"))
            rows.append(("Hardness class", hardness_class))

        # Dominant ions (simplified)
        cation_totals = [np.mean(self.cations[ion]) if self.cations[ion] else 0 for ion in self.cations]
        anion_totals = [np.mean(self.anions[ion]) if self.anions[ion] else 0 for ion in self.anions]

        if cation_totals and max(cation_totals) > 0:
            cation_names = list(self.cations.keys())
            dominant_cation = cation_names[np.argmax(cation_totals)]
            rows.append(("Dominant cation", dominant_cation.upper()))

        if anion_totals and max(anion_totals) > 0:
            anion_names = list(self.anions.keys())
            dominant_anion = anion_names[np.argmax(anion_totals)]
            rows.append(("Dominant anion", dominant_anion.upper()))

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

        # Piper diagram (simplified)
        self.piper_frame = ttk.Frame(container)
        self.piper_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self._create_piper_diagram(self.piper_frame)

        # Ion bar chart
        self.ion_bar_frame = ttk.Frame(container)
        self.ion_bar_frame.pack(fill="x", padx=5, pady=5)
        self._create_ion_bar_chart(self.ion_bar_frame)

        # Data table
        self._create_data_table(container)

    def _create_piper_diagram(self, parent):
        """Create simplified Piper diagram."""
        frame = ttk.LabelFrame(parent, text="Water Type Classification", padding=10)
        frame.pack(fill="both", expand=True)

        fig = Figure(figsize=(6, 5), dpi=100)

        # Collect data based on selection
        cation_data = {'ca': [], 'mg': [], 'na+k': []}
        anion_data = {'hco3+co3': [], 'so4': [], 'cl': []}

        indices = self.selected_indices if self.selected_indices else range(len(self.sample_summary))

        for idx in indices:
            if idx >= len(self.sample_summary):
                continue
            sample = self.sample_summary[idx]

            # Calculate cation percentages
            ca = sample['cations'].get('ca', 0) / _EW['ca']
            mg = sample['cations'].get('mg', 0) / _EW['mg']
            na = sample['cations'].get('na', 0) / _EW['na']
            k = sample['cations'].get('k', 0) / _EW['k']

            total_cat = ca + mg + na + k
            if total_cat > 0:
                cation_data['ca'].append(ca / total_cat * 100)
                cation_data['mg'].append(mg / total_cat * 100)
                cation_data['na+k'].append((na + k) / total_cat * 100)

            # Calculate anion percentages
            hco3 = sample['anions'].get('hco3', 0) / _EW['hco3']
            co3 = sample['anions'].get('co3', 0) / _EW['co3']
            so4 = sample['anions'].get('so4', 0) / _EW['so4']
            cl = sample['anions'].get('cl', 0) / _EW['cl']

            total_an = hco3 + co3 + so4 + cl
            if total_an > 0:
                anion_data['hco3+co3'].append((hco3 + co3) / total_an * 100)
                anion_data['so4'].append(so4 / total_an * 100)
                anion_data['cl'].append(cl / total_an * 100)

        # Create three subplots
        ax_cat = fig.add_subplot(221)
        ax_an = fig.add_subplot(222)
        ax_dia = fig.add_subplot(223)

        # Plot cation triangle
        if cation_data['ca'] and cation_data['mg'] and cation_data['na+k']:
            ax_cat.scatter(cation_data['ca'], cation_data['na+k'],
                          c='blue', alpha=0.7, s=30)
        ax_cat.set_xlim(0, 100)
        ax_cat.set_ylim(0, 100)
        ax_cat.set_xlabel("Ca (%)")
        ax_cat.set_ylabel("Na+K (%)")
        ax_cat.set_title("Cations")
        ax_cat.grid(True, alpha=0.3)

        # Plot anion triangle
        if anion_data['hco3+co3'] and anion_data['cl'] and anion_data['so4']:
            ax_an.scatter(anion_data['hco3+co3'], anion_data['cl'],
                         c='red', alpha=0.7, s=30)
        ax_an.set_xlim(0, 100)
        ax_an.set_ylim(0, 100)
        ax_an.set_xlabel("HCO₃+CO₃ (%)")
        ax_an.set_ylabel("Cl (%)")
        ax_an.set_title("Anions")
        ax_an.grid(True, alpha=0.3)

        # Plot diamond (simplified)
        ax_dia.text(0.5, 0.5, "Water Type\nClassification",
                   ha='center', va='center', transform=ax_dia.transAxes,
                   fontsize=10, multialignment='center')
        ax_dia.set_xlim(0, 1)
        ax_dia.set_ylim(0, 1)
        ax_dia.set_xticks([])
        ax_dia.set_yticks([])
        ax_dia.set_title("Combined")

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.figures.append(fig)

    def _create_ion_bar_chart(self, parent):
        """Create bar chart of mean ion concentrations."""
        frame = ttk.LabelFrame(parent, text="Mean Ion Concentrations", padding=10)
        frame.pack(fill="x")

        fig = Figure(figsize=(5, 3), dpi=100)
        ax = fig.add_subplot(111)

        # Calculate means based on selection
        cation_means = []
        anion_means = []

        indices = self.selected_indices if self.selected_indices else range(len(self.sample_summary))

        cation_sums = {'ca': 0, 'mg': 0, 'na': 0, 'k': 0}
        anion_sums = {'hco3': 0, 'co3': 0, 'so4': 0, 'cl': 0, 'no3': 0}
        cation_counts = {'ca': 0, 'mg': 0, 'na': 0, 'k': 0}
        anion_counts = {'hco3': 0, 'co3': 0, 'so4': 0, 'cl': 0, 'no3': 0}

        for idx in indices:
            if idx >= len(self.sample_summary):
                continue
            sample = self.sample_summary[idx]

            for ion, val in sample['cations'].items():
                cation_sums[ion] += val
                cation_counts[ion] += 1
            for ion, val in sample['anions'].items():
                anion_sums[ion] += val
                anion_counts[ion] += 1

        cation_names = ['Ca²⁺', 'Mg²⁺', 'Na⁺', 'K⁺']
        anion_names = ['HCO₃⁻', 'CO₃²⁻', 'SO₄²⁻', 'Cl⁻', 'NO₃⁻']

        cation_vals = []
        for ion in ['ca', 'mg', 'na', 'k']:
            if cation_counts[ion] > 0:
                cation_vals.append(cation_sums[ion] / cation_counts[ion])
            else:
                cation_vals.append(0)

        anion_vals = []
        for ion in ['hco3', 'co3', 'so4', 'cl', 'no3']:
            if anion_counts[ion] > 0:
                anion_vals.append(anion_sums[ion] / anion_counts[ion])
            else:
                anion_vals.append(0)

        x1 = range(len(cation_names))
        x2 = range(len(anion_names))

        if any(cation_vals):
            ax.bar(x1, cation_vals, alpha=0.7, color='blue', label='Cations')
        if any(anion_vals):
            ax.bar([i + len(cation_names) for i in x2], anion_vals,
                   alpha=0.7, color='red', label='Anions')

        all_names = cation_names + anion_names
        ax.set_xticks(range(len(all_names)))
        ax.set_xticklabels(all_names, rotation=45, ha='right')
        ax.set_ylabel('Concentration (mg/L)')
        ax.set_title('Mean Ion Concentrations')
        ax.legend()
        ax.grid(True, linestyle=':', alpha=0.6)

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.figures.append(fig)

    def _create_data_table(self, parent):
        """Create table of water chemistry data."""
        frame = ttk.LabelFrame(parent, text="Sample Data", padding=10)
        frame.pack(fill="x", padx=5, pady=5)

        cols = ["ID", "pH", "TDS", "Hardness", "CBE%"]
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=6)

        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=90, anchor="center")

        # Filter data based on selection
        indices = self.selected_indices if self.selected_indices else range(len(self.sample_summary))

        for i in sorted(indices)[:20]:  # Limit to 20 rows
            if i >= len(self.sample_summary):
                continue

            sample = self.sample_summary[i]

            sid = sample['id'][:8]
            ph = f"{sample['ph']:.2f}" if sample['ph'] is not None else "-"
            tds = f"{sample['tds']:.0f}" if sample['tds'] is not None else "-"
            hardness = f"{sample['hardness']:.0f}" if sample['hardness'] is not None else "-"
            cbe = f"{sample['cbe']:.1f}" if sample['cbe'] is not None else "-"

            tree.insert("", "end", values=(sid, ph, tds, hardness, cbe))

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
            if idx < len(self.sample_summary):
                hub_idx = self.sample_summary[idx]['index']
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
