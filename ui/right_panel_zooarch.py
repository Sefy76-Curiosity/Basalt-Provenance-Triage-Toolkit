"""
Zooarchaeology Right Panel
============================
Features:
  - Dynamic updates when rows are selected in main table
  - Scrollable interface for all content
  - Shows taxon abundance and diversity metrics
"""

import tkinter as tk
from tkinter import ttk
import numpy as np
import math
from collections import Counter
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from .right_panel import FieldPanelBase, OK_ICON, WARN_ICON, ERROR_ICON, INFO_ICON


class ZooarchPanel(FieldPanelBase):
    PANEL_ID = "zooarchaeology"
    PANEL_NAME = "Zooarchaeology"
    PANEL_ICON = "🦴"
    DETECT_COLUMNS = ['taxon', 'taxa', 'nisp', 'mni', 'element',
                      'side', 'skeletal', 'species', 'bone']
    is_right_panel = True

    def __init__(self, parent, app):
        super().__init__(parent, app)

        # Initialize data storage
        self.taxa = []
        self.nisp_by_taxon = Counter()
        self.elements = []
        self.sides = []
        self.modifications = []
        self.samples = []
        self.specimen_summary = []

        # Selection tracking
        self.selected_indices = set()

        # UI elements
        self.current_selection_label = None
        self.abundance_frame = None
        self.diversity_frame = None
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
        self._redraw_abundance_chart()
        self._redraw_diversity_gauge()

    def _set_info_label(self):
        """Update selection info label."""
        if not hasattr(self, 'current_selection_label') or not self.current_selection_label:
            return

        if not self.selected_indices:
            text = "Showing: ALL specimens"
            color = "black"
        elif len(self.selected_indices) == 1:
            idx = next(iter(self.selected_indices))
            if idx < len(self.specimen_summary):
                text = f"Showing: Specimen {self.specimen_summary[idx].get('id', idx+1)}"
                color = "blue"
            else:
                text = "Showing: Selected specimen"
                color = "blue"
        else:
            text = f"Showing: {len(self.selected_indices)} selected specimens"
            color = "green"

        try:
            self.current_selection_label.config(text=text, foreground=color)
        except:
            pass

    def _redraw_abundance_chart(self):
        """Redraw abundance chart with current selection."""
        if not hasattr(self, 'abundance_frame') or not self.abundance_frame:
            return
        try:
            for widget in self.abundance_frame.winfo_children():
                widget.destroy()
            self._create_abundance_chart(self.abundance_frame)
        except:
            pass

    def _redraw_diversity_gauge(self):
        """Redraw diversity gauge with current selection."""
        if not hasattr(self, 'diversity_frame') or not self.diversity_frame:
            return
        try:
            for widget in self.diversity_frame.winfo_children():
                widget.destroy()
            self._create_diversity_gauge(self.diversity_frame)
        except:
            pass

    # ------------------------------------------------------------------
    # Data extraction
    # ------------------------------------------------------------------
    def _extract_data(self):
        """Extract zooarchaeological data from samples."""
        self.taxa = []
        self.nisp_by_taxon = Counter()
        self.elements = []
        self.sides = []
        self.modifications = []
        self.specimen_summary = []

        if not self.samples:
            return

        # Find columns
        taxon_col = self._find_column(self.samples, 'taxon', 'taxa', 'species')
        nisp_col = self._find_column(self.samples, 'nisp', 'count')
        element_col = self._find_column(self.samples, 'element', 'bone')
        side_col = self._find_column(self.samples, 'side')
        mod_col = self._find_column(self.samples, 'modification', 'taphonomy')

        for i, sample in enumerate(self.samples):
            specimen = {
                'index': i,
                'id': sample.get('Sample_ID', f"Specimen {i+1}"),
                'taxon': None,
                'nisp': 1,
                'element': None,
                'side': None,
                'modification': None,
                'raw_data': sample
            }

            # Taxon
            if taxon_col:
                taxon = sample.get(taxon_col)
                if taxon and str(taxon).strip():
                    self.taxa.append(str(taxon))
                    specimen['taxon'] = str(taxon)

                    # NISP
                    nisp = 1
                    if nisp_col:
                        try:
                            nisp_val = sample.get(nisp_col)
                            if nisp_val is not None:
                                nisp = int(float(nisp_val))
                        except:
                            pass
                    specimen['nisp'] = nisp
                    self.nisp_by_taxon[str(taxon)] += nisp

            # Element
            if element_col:
                element = sample.get(element_col)
                if element:
                    self.elements.append(str(element))
                    specimen['element'] = str(element)

            # Side
            if side_col:
                side = sample.get(side_col)
                if side:
                    self.sides.append(str(side).lower())
                    specimen['side'] = str(side)

            # Modifications
            if mod_col:
                mod = sample.get(mod_col)
                if mod:
                    self.modifications.append(str(mod))
                    specimen['modification'] = str(mod)

            self.specimen_summary.append(specimen)

    def _calculate_diversity(self):
        """Calculate Shannon diversity index based on selection."""
        # Get NISP counts based on selection
        nisp_counts = Counter()

        indices = self.selected_indices if self.selected_indices else range(len(self.specimen_summary))

        for idx in indices:
            if idx >= len(self.specimen_summary):
                continue
            spec = self.specimen_summary[idx]
            if spec['taxon']:
                nisp_counts[spec['taxon']] += spec['nisp']

        total_nisp = sum(nisp_counts.values())
        if total_nisp == 0:
            return None, None, 0

        # Shannon index H' = -Σ p_i * ln(p_i)
        H = 0
        for count in nisp_counts.values():
            p = count / total_nisp
            if p > 0:
                H -= p * math.log(p)

        # Evenness J = H' / ln(S)
        S = len(nisp_counts)
        J = H / math.log(S) if S > 1 else 1

        return H, J, S

    def _estimate_mni(self):
        """Estimate Minimum Number of Individuals."""
        # Simplified MNI based on unique specimens
        return len(self.selected_indices) if self.selected_indices else len(self.specimen_summary)

    def _tof(self, v):
        try:
            if v is None:
                return None
            return float(v)
        except:
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
        rows.append(("N specimens", str(n)))

        # Total NISP
        total_nisp = sum(self.nisp_by_taxon.values())
        rows.append(("Total NISP", str(total_nisp)))

        # Number of taxa
        n_taxa = len(self.nisp_by_taxon)
        rows.append(("N taxa (richness)", str(n_taxa)))

        # Most abundant taxon
        if self.nisp_by_taxon:
            most_common = self.nisp_by_taxon.most_common(1)[0]
            rows.append(("Top taxon", f"{most_common[0]} ({most_common[1]})"))

        return rows

    def _calc_validation(self, samples, columns):
        """Data validation."""
        rows = []

        if not samples:
            rows.append((WARN_ICON, "No data"))
            return rows

        # Check for taxon column
        taxon_col = self._find_column(samples, 'taxon', 'taxa', 'species')
        if taxon_col:
            rows.append((OK_ICON, f"Taxon column: {taxon_col}"))

            # Check for missing taxa
            missing = sum(1 for s in samples if not s.get(taxon_col))
            if missing == 0:
                rows.append((OK_ICON, "All specimens identified"))
            else:
                rows.append((WARN_ICON, f"{missing} unidentified specimens"))
        else:
            rows.append((ERROR_ICON, "No taxon column"))

        return rows

    def _calc_quick(self, samples, columns):
        """Quick calculations - diversity and MNI."""
        rows = []

        # Shannon diversity
        H, J, S = self._calculate_diversity()
        if H is not None:
            rows.append(("Shannon H'", f"{H:.3f}"))
            if J is not None:
                rows.append(("Evenness J", f"{J:.3f}"))
            rows.append(("Richness S", str(S)))

        # MNI estimate
        mni = self._estimate_mni()
        rows.append(("MNI estimate", str(mni)))

        # NISP/MNI ratio
        total_nisp = 0
        indices = self.selected_indices if self.selected_indices else range(len(self.specimen_summary))
        for idx in indices:
            if idx < len(self.specimen_summary):
                total_nisp += self.specimen_summary[idx]['nisp']

        if mni > 0:
            rows.append(("NISP/MNI", f"{total_nisp/mni:.1f}"))

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
            text="Select rows in main table to filter specimens",
            font=("Segoe UI", 9, "italic")
        )
        self.current_selection_label.pack(side=tk.LEFT)

        # Abundance chart
        self.abundance_frame = ttk.Frame(container)
        self.abundance_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self._create_abundance_chart(self.abundance_frame)

        # Diversity gauge
        self.diversity_frame = ttk.Frame(container)
        self.diversity_frame.pack(fill="x", padx=5, pady=5)
        self._create_diversity_gauge(self.diversity_frame)

        # Data table
        self._create_data_table(container)

    def _create_abundance_chart(self, parent):
        """Create bar chart of taxon abundances."""
        frame = ttk.LabelFrame(parent, text="Taxon Abundance", padding=10)
        frame.pack(fill="both", expand=True)

        fig = Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)

        # Get NISP counts based on selection
        nisp_counts = Counter()

        indices = self.selected_indices if self.selected_indices else range(len(self.specimen_summary))

        for idx in indices:
            if idx >= len(self.specimen_summary):
                continue
            spec = self.specimen_summary[idx]
            if spec['taxon']:
                nisp_counts[spec['taxon']] += spec['nisp']

        if nisp_counts:
            # Get top 10 taxa
            top_taxa = nisp_counts.most_common(10)
            names = [t[0][:15] + "..." if len(t[0]) > 15 else t[0] for t in top_taxa]
            counts = [t[1] for t in top_taxa]

            y_pos = range(len(names))
            ax.barh(y_pos, counts, align='center', alpha=0.7, color='steelblue')
            ax.set_yticks(y_pos)
            ax.set_yticklabels(names)
            ax.invert_yaxis()
            ax.set_xlabel('NISP')
            ax.set_title('Top 10 Taxa')

            # Add value labels
            for i, v in enumerate(counts):
                ax.text(v + 0.5, i, str(v), va='center')
        else:
            ax.text(0.5, 0.5, "No abundance data", ha='center', va='center',
                   transform=ax.transAxes)

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.figures.append(fig)

    def _create_diversity_gauge(self, parent):
        """Create gauge for Shannon diversity."""
        frame = ttk.LabelFrame(parent, text="Diversity Metrics", padding=10)
        frame.pack(fill="x")

        fig = Figure(figsize=(5, 2), dpi=100)
        ax = fig.add_subplot(111)

        H, J, S = self._calculate_diversity()

        if H is not None:
            max_H = math.log(S) if S > 1 else 1

            # Create horizontal bar for H'
            ax.barh(0, H, height=0.3, color='steelblue', alpha=0.7, label=f"H' = {H:.3f}")
            ax.barh(0, max_H, height=0.3, color='lightgray', alpha=0.3, left=0)
            ax.set_xlim(0, max_H * 1.1)
            ax.set_yticks([])
            ax.set_xlabel("Shannon Index H'")
            ax.set_title(f"Richness (S) = {S} | Evenness (J) = {J:.3f}" if J else f"Richness (S) = {S}")
            ax.legend(loc='upper right')
        else:
            ax.text(0.5, 0.5, "Insufficient data", ha='center', va='center',
                   transform=ax.transAxes)

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.figures.append(fig)

    def _create_data_table(self, parent):
        """Create table of specimen data."""
        frame = ttk.LabelFrame(parent, text="Specimen Data", padding=10)
        frame.pack(fill="x", padx=5, pady=5)

        cols = ["ID", "Taxon", "NISP", "Element", "Side"]
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=6)

        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=90, anchor="w")

        # Filter data based on selection
        indices = self.selected_indices if self.selected_indices else range(len(self.specimen_summary))

        for i in sorted(indices)[:20]:  # Limit to 20 rows
            if i >= len(self.specimen_summary):
                continue

            spec = self.specimen_summary[i]

            sid = spec['id'][:8]
            taxon = spec['taxon'][:15] if spec['taxon'] else '-'
            nisp = str(spec['nisp'])
            element = spec['element'][:10] if spec['element'] else '-'
            side = spec['side'][:5] if spec['side'] else '-'

            tree.insert("", "end", values=(sid, taxon, nisp, element, side))

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
            if idx < len(self.specimen_summary):
                hub_idx = self.specimen_summary[idx]['index']
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
