"""
Petrology Right Panel (Modal & Normative Mineralogy)
======================================================
Features:
  - Dynamic updates when rows are selected in main table
  - Scrollable interface for all content
  - Shows QAP diagram and mineral distributions
"""

import tkinter as tk
from tkinter import ttk
import numpy as np
from collections import Counter
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from .right_panel import FieldPanelBase, OK_ICON, WARN_ICON, ERROR_ICON, INFO_ICON


class PetrologyPanel(FieldPanelBase):
    PANEL_ID = "petrology"
    PANEL_NAME = "Petrology"
    PANEL_ICON = "🔥"
    DETECT_COLUMNS = ['quartz', 'feldspar', 'plagioclase', 'orthoclase',
                      'biotite', 'hornblende', 'pyroxene', 'olivine',
                      'modal', 'point_count', 'nepheline', 'muscovite']
    is_right_panel = True

    # Mineral classifications
    MAFIC_MINERALS = ['biotite', 'hornblende', 'pyroxene', 'olivine',
                      'opaque', 'augite', 'hypersthene', 'diopside',
                      'epidote', 'magnetite', 'ilmenite']

    FELSIC_MINERALS = ['quartz', 'feldspar', 'plagioclase', 'orthoclase',
                       'alkali_feldspar', 'k_feldspar', 'albite', 'anorthite',
                       'nepheline', 'leucite', 'muscovite']

    def __init__(self, parent, app):
        super().__init__(parent, app)

        # Initialize data storage
        self.modal_data = {}  # mineral -> list of percentages
        self.sample_totals = []
        self.color_indices = []
        self.qap_ratios = []  # (Q, A, P) normalized
        self.samples = []
        self.sample_summary = []

        # Selection tracking
        self.selected_indices = set()

        # UI elements
        self.current_selection_label = None
        self.qap_frame = None
        self.mineral_bar_frame = None
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
        self._redraw_qap_ternary()
        self._redraw_mineral_bar_chart()

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

    def _redraw_qap_ternary(self):
        """Redraw QAP diagram with current selection."""
        if not hasattr(self, 'qap_frame') or not self.qap_frame:
            return
        try:
            for widget in self.qap_frame.winfo_children():
                widget.destroy()
            self._create_qap_ternary(self.qap_frame)
        except:
            pass

    def _redraw_mineral_bar_chart(self):
        """Redraw mineral bar chart with current selection."""
        if not hasattr(self, 'mineral_bar_frame') or not self.mineral_bar_frame:
            return
        try:
            for widget in self.mineral_bar_frame.winfo_children():
                widget.destroy()
            self._create_mineral_bar_chart(self.mineral_bar_frame)
        except:
            pass

    # ------------------------------------------------------------------
    # Data extraction
    # ------------------------------------------------------------------
    def _extract_data(self):
        """Extract modal mineralogy data from samples."""
        self.modal_data = {}
        self.sample_totals = []
        self.color_indices = []
        self.qap_ratios = []
        self.sample_summary = []

        if not self.samples:
            return

        # Initialize data structure for all possible minerals
        all_minerals = self.MAFIC_MINERALS + self.FELSIC_MINERALS
        for mineral in all_minerals:
            self.modal_data[mineral] = []

        # Find mineral columns
        mineral_columns = {}
        for mineral in all_minerals:
            col = self._find_column(self.samples, mineral)
            if col:
                mineral_columns[mineral] = col

        # Extract data
        for i, sample in enumerate(self.samples):
            sample_modal = {}
            total = 0
            sample_info = {
                'index': i,
                'id': sample.get('Sample_ID', f"Sample {i+1}"),
                'minerals': {},
                'total': 0,
                'color_index': 0,
                'qap': None,
                'raw_data': sample
            }

            for mineral, col in mineral_columns.items():
                val = self._tof(sample.get(col))
                if val is not None and val > 0:
                    self.modal_data[mineral].append(val)
                    sample_modal[mineral] = val
                    sample_info['minerals'][mineral] = val
                    total += val

            self.sample_totals.append(total)
            sample_info['total'] = total

            # Calculate color index (M) = sum of mafic minerals
            m = sum(sample_modal.get(m, 0) for m in self.MAFIC_MINERALS if m in sample_modal)
            self.color_indices.append(m)
            sample_info['color_index'] = m

            # Calculate QAP if we have the right minerals
            q = sample_modal.get('quartz', 0)
            a = (sample_modal.get('orthoclase', 0) +
                 sample_modal.get('alkali_feldspar', 0) +
                 sample_modal.get('k_feldspar', 0))
            p = (sample_modal.get('plagioclase', 0) +
                 sample_modal.get('albite', 0) +
                 sample_modal.get('anorthite', 0))

            qap_total = q + a + p
            if qap_total > 0:
                qap = {
                    'Q': q / qap_total * 100,
                    'A': a / qap_total * 100,
                    'P': p / qap_total * 100,
                    'total': qap_total
                }
                self.qap_ratios.append(qap)
                sample_info['qap'] = qap

            self.sample_summary.append(sample_info)

    def _classify_qap(self, Q, A, P):
        """Simple QAP classification."""
        if Q > 60:
            if A > P:
                return "Alkali granite"
            else:
                return "Granite"
        elif Q > 20:
            if A > P*2:
                return "Alkali syenite"
            elif A > P/2:
                return "Syenite"
            else:
                return "Monzonite"
        elif Q > 5:
            if A > P*2:
                return "Alkali syenite"
            elif A > P/2:
                return "Syenite"
            else:
                return "Monzonite"
        else:
            if A > P*2:
                return "Alkali syenite"
            elif A > P/2:
                return "Syenite"
            else:
                return "Monzonite"

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

        # Find most abundant mineral
        mineral_means = {}
        for mineral, values in self.modal_data.items():
            if values:
                mineral_means[mineral] = np.mean(values)

        if mineral_means:
            top_mineral = max(mineral_means, key=mineral_means.get)
            rows.append(("Top mineral", top_mineral.capitalize()))
            rows.append((f"{top_mineral} mean", f"{mineral_means[top_mineral]:.1f}%"))

        # Quartz mean
        if self.modal_data.get('quartz'):
            q_mean = np.mean(self.modal_data['quartz'])
            rows.append(("Quartz mean", f"{q_mean:.1f}%"))

        # Mean color index
        if self.color_indices:
            rows.append(("Mean M (color)", f"{np.mean(self.color_indices):.1f}%"))

        return rows

    def _calc_validation(self, samples, columns):
        """Data validation."""
        rows = []

        if not samples:
            rows.append((WARN_ICON, "No data"))
            return rows

        # Count mineral columns found
        mineral_count = sum(1 for m, v in self.modal_data.items() if v)
        if mineral_count > 0:
            rows.append((OK_ICON, f"{mineral_count} minerals detected"))
        else:
            rows.append((WARN_ICON, "No mineral columns found"))

        # Check modal totals
        if self.sample_totals:
            off_total = sum(1 for t in self.sample_totals
                           if t > 0 and not (95 <= t <= 105))
            if off_total == 0:
                rows.append((OK_ICON, "All totals near 100%"))
            else:
                rows.append((WARN_ICON, f"{off_total} samples off 100%"))

        # Check for negative values
        negative_count = 0
        for mineral, values in self.modal_data.items():
            if values:
                negative_count += sum(1 for v in values if v < 0)

        if negative_count == 0:
            rows.append((OK_ICON, "No negative percentages"))
        else:
            rows.append((ERROR_ICON, f"{negative_count} negative values"))

        return rows

    def _calc_quick(self, samples, columns):
        """Quick calculations."""
        rows = []

        # Color index classification
        if self.color_indices:
            mean_m = np.mean(self.color_indices)
            if mean_m < 10:
                rows.append(("Rock type", "Leucocratic"))
            elif mean_m < 35:
                rows.append(("Rock type", "Mesocratic"))
            elif mean_m < 65:
                rows.append(("Rock type", "Melanocratic"))
            else:
                rows.append(("Rock type", "Ultramafic"))

        # QAP summary
        if self.qap_ratios:
            mean_q = np.mean([r['Q'] for r in self.qap_ratios])
            mean_a = np.mean([r['A'] for r in self.qap_ratios])
            mean_p = np.mean([r['P'] for r in self.qap_ratios])

            rows.append(("QAP (mean)", f"{mean_q:.0f}/{mean_a:.0f}/{mean_p:.0f}"))

            # Classification hint
            class_name = self._classify_qap(mean_q, mean_a, mean_p)
            rows.append(("QAP field", class_name))

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

        # QAP diagram
        self.qap_frame = ttk.Frame(container)
        self.qap_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self._create_qap_ternary(self.qap_frame)

        # Mineral bar chart
        self.mineral_bar_frame = ttk.Frame(container)
        self.mineral_bar_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self._create_mineral_bar_chart(self.mineral_bar_frame)

        # Data table
        self._create_modal_table(container)

    def _create_qap_ternary(self, parent):
        """Create QAP ternary diagram."""
        frame = ttk.LabelFrame(parent, text="QAP Diagram", padding=10)
        frame.pack(fill="both", expand=True)

        fig = Figure(figsize=(5, 4), dpi=100)

        # Filter data based on selection
        qap_vals = []

        indices = self.selected_indices if self.selected_indices else range(len(self.sample_summary))

        for idx in indices:
            if idx >= len(self.sample_summary):
                continue
            sample = self.sample_summary[idx]
            if sample['qap'] is not None:
                qap_vals.append(sample['qap'])

        if qap_vals:
            # This would use a proper ternary plot
            # For now, create a simplified version
            ax = fig.add_subplot(111)

            # Plot Q vs A/P ratio
            q_vals = [r['Q'] for r in qap_vals]
            ap_ratio = [r['A']/(r['P']+0.1) for r in qap_vals]

            if self.selected_indices:
                ax.scatter(q_vals, ap_ratio, c='red', s=50, alpha=0.7, label='Selected')
            else:
                ax.scatter(q_vals, ap_ratio, c='blue', s=50, alpha=0.7, label='All')

            ax.set_xlabel("Q (%)")
            ax.set_ylabel("A/P ratio")
            ax.set_title("QAP Projection")
            ax.grid(True, linestyle=':', alpha=0.6)
            ax.legend()

            # Add field boundaries (simplified)
            ax.axvline(x=60, color='red', linestyle='--', alpha=0.5)
            ax.axvline(x=20, color='red', linestyle='--', alpha=0.5)
            ax.axhline(y=1, color='red', linestyle='--', alpha=0.5)
            ax.axhline(y=0.5, color='red', linestyle='--', alpha=0.5)
            ax.axhline(y=2, color='red', linestyle='--', alpha=0.5)
        else:
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, "Need Q, A, P data", ha='center', va='center',
                   transform=ax.transAxes, fontsize=12)

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.figures.append(fig)

    def _create_mineral_bar_chart(self, parent):
        """Create bar chart of mean mineral percentages."""
        frame = ttk.LabelFrame(parent, text="Mean Mineralogy", padding=10)
        frame.pack(fill="both", expand=True)

        fig = Figure(figsize=(5, 3), dpi=100)
        ax = fig.add_subplot(111)

        # Calculate means for minerals based on selection
        minerals = []
        means = []
        colors = []

        # Get mineral data from selected samples
        mineral_sums = {}
        mineral_counts = {}

        indices = self.selected_indices if self.selected_indices else range(len(self.sample_summary))

        for idx in indices:
            if idx >= len(self.sample_summary):
                continue
            sample = self.sample_summary[idx]
            for mineral, val in sample['minerals'].items():
                mineral_sums[mineral] = mineral_sums.get(mineral, 0) + val
                mineral_counts[mineral] = mineral_counts.get(mineral, 0) + 1

        for mineral in self.FELSIC_MINERALS + self.MAFIC_MINERALS:
            if mineral in mineral_sums and mineral_counts[mineral] > 0:
                mean_val = mineral_sums[mineral] / mineral_counts[mineral]
                if mean_val > 0.1:  # Only show minerals with significant presence
                    minerals.append(mineral.capitalize()[:8])
                    means.append(mean_val)
                    colors.append('steelblue' if mineral in self.FELSIC_MINERALS else 'peru')

        if minerals:
            ax.bar(range(len(minerals)), means, color=colors, alpha=0.7,
                  edgecolor='black')
            ax.set_xticks(range(len(minerals)))
            ax.set_xticklabels(minerals, rotation=45, ha='right')
            ax.set_ylabel('Mean %')
            ax.set_title('Average Mineral Composition')
            ax.grid(True, linestyle=':', alpha=0.3, axis='y')

            # Add legend
            from matplotlib.patches import Patch
            legend_elements = [
                Patch(facecolor='steelblue', label='Felsic'),
                Patch(facecolor='peru', label='Mafic')
            ]
            ax.legend(handles=legend_elements, loc='upper right')
        else:
            ax.text(0.5, 0.5, "No mineral data", ha='center', va='center',
                   transform=ax.transAxes, fontsize=12)

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.figures.append(fig)

    def _create_modal_table(self, parent):
        """Create table of modal mineralogy."""
        frame = ttk.LabelFrame(parent, text="Modal Mineralogy", padding=10)
        frame.pack(fill="x", padx=5, pady=5)

        # Get minerals present in selected samples
        active_minerals = set()
        indices = self.selected_indices if self.selected_indices else range(len(self.sample_summary))

        for idx in indices:
            if idx >= len(self.sample_summary):
                continue
            sample = self.sample_summary[idx]
            active_minerals.update(sample['minerals'].keys())

        active_minerals = sorted(list(active_minerals))[:8]  # Limit to 8 minerals for display

        if active_minerals:
            cols = ["Sample"] + [m.capitalize()[:8] for m in active_minerals] + ["Total"]
            tree = ttk.Treeview(frame, columns=cols, show="headings", height=6)

            for col in cols:
                tree.heading(col, text=col)
                tree.column(col, width=70, anchor="center")

            # Add data for selected samples
            for i in sorted(indices)[:10]:  # Limit to 10 samples
                if i >= len(self.sample_summary):
                    continue

                sample = self.sample_summary[i]
                sample_id = sample['id']
                if len(sample_id) > 6:
                    sample_id = sample_id[:6]

                row_values = [sample_id]
                for mineral in active_minerals:
                    val = sample['minerals'].get(mineral, 0)
                    row_values.append(f"{val:.1f}" if val > 0 else "-")

                row_values.append(f"{sample['total']:.1f}")
                tree.insert("", "end", values=row_values)

            scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)

            tree.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

            # Bind click to select main table row
            tree.bind('<ButtonRelease-1>', lambda e: self._on_table_click(e, tree))
            self.data_tree = tree
        else:
            ttk.Label(frame, text="No modal data available").pack(pady=10)

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
