"""
Archaeology / Lithic Analysis Right Panel
==========================================
Features:
  - Dynamic updates when rows are selected in main table
  - Scrollable interface for all content
  - Shows artefact metrics and distributions
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


class ArchaeologyPanel(FieldPanelBase):
    PANEL_ID = "archaeology"
    PANEL_NAME = "Archaeology"
    PANEL_ICON = "🏺"
    DETECT_COLUMNS = ['length', 'width', 'thickness', 'mass', 'weight',
                      'cortex', 'raw_material', 'type', 'retouch', 'platform']
    is_right_panel = True

    def __init__(self, parent, app):
        super().__init__(parent, app)

        # Initialize data storage
        self.lengths = []
        self.widths = []
        self.thicknesses = []
        self.masses = []
        self.cortex_pct = []
        self.raw_materials = []
        self.artefact_types = []
        self.platform_types = []
        self.retouch = []
        self.samples = []

        # Selection tracking
        self.selected_indices = set()
        self.artefact_summary = []

        # UI elements
        self.current_selection_label = None
        self.metric_scatter_frame = None
        self.material_pie_frame = None
        self.cortex_hist_frame = None
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
        self._redraw_metric_scatter()
        self._redraw_material_pie()
        self._redraw_cortex_histogram()

    def _set_info_label(self):
        """Update selection info label."""
        if not hasattr(self, 'current_selection_label') or not self.current_selection_label:
            return

        if not self.selected_indices:
            text = "Showing: ALL artefacts"
            color = "black"
        elif len(self.selected_indices) == 1:
            idx = next(iter(self.selected_indices))
            if idx < len(self.artefact_summary):
                text = f"Showing: Artefact {idx+1}"
                color = "blue"
            else:
                text = "Showing: Selected artefact"
                color = "blue"
        else:
            text = f"Showing: {len(self.selected_indices)} selected artefacts"
            color = "green"

        try:
            self.current_selection_label.config(text=text, foreground=color)
        except:
            pass

    def _redraw_metric_scatter(self):
        """Redraw metric scatter plot with current selection."""
        if not hasattr(self, 'metric_scatter_frame') or not self.metric_scatter_frame:
            return
        try:
            for widget in self.metric_scatter_frame.winfo_children():
                widget.destroy()
            self._create_metric_scatter(self.metric_scatter_frame)
        except:
            pass

    def _redraw_material_pie(self):
        """Redraw material pie chart with current selection."""
        if not hasattr(self, 'material_pie_frame') or not self.material_pie_frame:
            return
        try:
            for widget in self.material_pie_frame.winfo_children():
                widget.destroy()
            self._create_material_pie(self.material_pie_frame)
        except:
            pass

    def _redraw_cortex_histogram(self):
        """Redraw cortex histogram with current selection."""
        if not hasattr(self, 'cortex_hist_frame') or not self.cortex_hist_frame:
            return
        try:
            for widget in self.cortex_hist_frame.winfo_children():
                widget.destroy()
            self._create_cortex_histogram(self.cortex_hist_frame)
        except:
            pass

    # ------------------------------------------------------------------
    # Data extraction
    # ------------------------------------------------------------------
    def _extract_data(self):
        """Extract lithic analysis data from samples."""
        self.lengths = []
        self.widths = []
        self.thicknesses = []
        self.masses = []
        self.cortex_pct = []
        self.raw_materials = []
        self.artefact_types = []
        self.platform_types = []
        self.retouch = []
        self.artefact_summary = []

        if not self.samples:
            return

        # Find columns
        length_col = self._find_column(self.samples, 'length', 'len')
        width_col = self._find_column(self.samples, 'width', 'wid')
        thick_col = self._find_column(self.samples, 'thickness', 'thick')
        mass_col = self._find_column(self.samples, 'mass', 'weight')
        cortex_col = self._find_column(self.samples, 'cortex', 'cortex_pct')
        material_col = self._find_column(self.samples, 'raw_material', 'material', 'lithology')
        type_col = self._find_column(self.samples, 'type', 'artefact_type', 'typology')
        platform_col = self._find_column(self.samples, 'platform', 'platform_type')
        retouch_col = self._find_column(self.samples, 'retouch', 'retouch_type')

        for i, sample in enumerate(self.samples):
            artefact = {
                'index': i,
                'id': sample.get('Sample_ID', f"ART-{i+1:03d}"),
                'length': None,
                'width': None,
                'thickness': None,
                'mass': None,
                'cortex': None,
                'material': None,
                'type': None,
                'platform': None,
                'retouch': None,
                'raw_data': sample
            }

            # Metrics
            if length_col:
                l = self._tof(sample.get(length_col))
                if l is not None and l > 0:
                    self.lengths.append(l)
                    artefact['length'] = l

            if width_col:
                w = self._tof(sample.get(width_col))
                if w is not None and w > 0:
                    self.widths.append(w)
                    artefact['width'] = w

            if thick_col:
                t = self._tof(sample.get(thick_col))
                if t is not None and t > 0:
                    self.thicknesses.append(t)
                    artefact['thickness'] = t

            if mass_col:
                m = self._tof(sample.get(mass_col))
                if m is not None and m > 0:
                    self.masses.append(m)
                    artefact['mass'] = m

            # Cortex
            if cortex_col:
                c = self._tof(sample.get(cortex_col))
                if c is not None:
                    self.cortex_pct.append(c)
                    artefact['cortex'] = c

            # Categorical data
            if material_col:
                mat = sample.get(material_col)
                if mat:
                    self.raw_materials.append(str(mat))
                    artefact['material'] = str(mat)

            if type_col:
                typ = sample.get(type_col)
                if typ:
                    self.artefact_types.append(str(typ))
                    artefact['type'] = str(typ)

            if platform_col:
                plat = sample.get(platform_col)
                if plat:
                    self.platform_types.append(str(plat))
                    artefact['platform'] = str(plat)

            if retouch_col:
                ret = sample.get(retouch_col)
                if ret:
                    self.retouch.append(str(ret))
                    artefact['retouch'] = str(ret)

            self.artefact_summary.append(artefact)

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
        rows.append(("N artefacts", str(n)))

        if self.lengths:
            rows.append(("Length range", f"{min(self.lengths):.1f}-{max(self.lengths):.1f} mm"))
            rows.append(("Mean length", f"{np.mean(self.lengths):.1f} mm"))

        if self.widths:
            rows.append(("Mean width", f"{np.mean(self.widths):.1f} mm"))

        if self.masses:
            rows.append(("Mean mass", f"{np.mean(self.masses):.1f} g"))

        if self.raw_materials:
            unique_mats = len(set(self.raw_materials))
            rows.append(("Raw materials", str(unique_mats)))

        return rows

    def _calc_validation(self, samples, columns):
        """Data validation."""
        rows = []

        if not samples:
            rows.append((WARN_ICON, "No data"))
            return rows

        # Check dimensions
        if self.lengths:
            bad_len = sum(1 for l in self.lengths if l <= 0)
            if bad_len == 0:
                rows.append((OK_ICON, "All lengths > 0"))
            else:
                rows.append((ERROR_ICON, f"{bad_len} invalid lengths"))

        if self.widths:
            bad_wid = sum(1 for w in self.widths if w <= 0)
            if bad_wid == 0:
                rows.append((OK_ICON, "All widths > 0"))
            else:
                rows.append((ERROR_ICON, f"{bad_wid} invalid widths"))

        # Check typology
        type_col = self._find_column(samples, 'type', 'artefact_type')
        if type_col:
            missing_type = sum(1 for s in samples if not s.get(type_col))
            if missing_type == 0:
                rows.append((OK_ICON, "All artefacts typed"))
            else:
                rows.append((WARN_ICON, f"{missing_type} untyped"))
        else:
            rows.append((INFO_ICON, "No typology column"))

        return rows

    def _calc_quick(self, samples, columns):
        """Quick calculations."""
        rows = []

        # Flaking index (L/W ratio)
        if self.lengths and self.widths:
            n = min(len(self.lengths), len(self.widths))
            ratios = [self.lengths[i] / self.widths[i] for i in range(n) if self.widths[i] > 0]

            if ratios:
                mean_ratio = np.mean(ratios)
                rows.append(("Mean L/W", f"{mean_ratio:.2f}"))

                # Blank classification
                blades = sum(1 for r in ratios if r >= 2.0)
                flakes = sum(1 for r in ratios if r < 2.0)
                rows.append(("Blades (≥2.0)", f"{blades} ({100*blades//len(ratios)}%)"))
                rows.append(("Flakes (<2.0)", f"{flakes} ({100*flakes//len(ratios)}%)"))

        # Cortex distribution
        if self.cortex_pct:
            high_cortex = sum(1 for c in self.cortex_pct if c > 50)
            no_cortex = sum(1 for c in self.cortex_pct if c == 0)
            rows.append(("Cortex >50%", f"{high_cortex} ({100*high_cortex//len(self.cortex_pct)}%)"))
            rows.append(("No cortex", f"{no_cortex} ({100*no_cortex//len(self.cortex_pct)}%)"))

        # Raw material diversity
        if self.raw_materials:
            mat_counts = Counter(self.raw_materials)
            dominant = mat_counts.most_common(1)[0]
            rows.append(("Dominant material", f"{dominant[0][:15]} ({dominant[1]})"))

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
            text="Select rows in main table to filter artefacts",
            font=("Segoe UI", 9, "italic")
        )
        self.current_selection_label.pack(side=tk.LEFT)

        # Metric scatter plot
        self.metric_scatter_frame = ttk.Frame(container)
        self.metric_scatter_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self._create_metric_scatter(self.metric_scatter_frame)

        # Material pie chart
        self.material_pie_frame = ttk.Frame(container)
        self.material_pie_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self._create_material_pie(self.material_pie_frame)

        # Cortex histogram
        self.cortex_hist_frame = ttk.Frame(container)
        self.cortex_hist_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self._create_cortex_histogram(self.cortex_hist_frame)

        # Data table
        self._create_data_table(container)

    def _create_metric_scatter(self, parent):
        """Create scatter plot of length vs width."""
        frame = ttk.LabelFrame(parent, text="Length vs Width", padding=10)
        frame.pack(fill="both", expand=True)

        fig = Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)

        ax.set_xlabel("Length (mm)")
        ax.set_ylabel("Width (mm)")
        ax.set_title("Artefact Dimensions")
        ax.grid(True, linestyle=':', alpha=0.6)

        # Filter data based on selection
        if self.selected_indices:
            lengths_filtered = []
            widths_filtered = []
            for idx in self.selected_indices:
                if idx < len(self.artefact_summary):
                    artefact = self.artefact_summary[idx]
                    if artefact['length'] and artefact['width']:
                        lengths_filtered.append(artefact['length'])
                        widths_filtered.append(artefact['width'])

            if lengths_filtered and widths_filtered:
                ax.scatter(lengths_filtered, widths_filtered,
                          c='red', alpha=0.7, edgecolors='black', s=50, label='Selected')
        else:
            # All data
            if self.lengths and self.widths:
                n = min(len(self.lengths), len(self.widths))
                ax.scatter(self.lengths[:n], self.widths[:n],
                          c='steelblue', alpha=0.7, edgecolors='black', s=50, label='All')

        # Add blade/flake boundary line
        if self.lengths:
            max_len = max(self.lengths) * 1.1
            x_line = np.linspace(0, max_len, 100)
            y_line = x_line / 2
            ax.plot(x_line, y_line, 'r--', linewidth=2, label='Blade/Flake boundary')
            ax.legend()

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.figures.append(fig)

    def _create_material_pie(self, parent):
        """Create pie chart of raw materials."""
        frame = ttk.LabelFrame(parent, text="Raw Materials", padding=10)
        frame.pack(fill="both", expand=True)

        fig = Figure(figsize=(5, 3), dpi=100)
        ax = fig.add_subplot(111)

        # Filter materials based on selection
        materials = []
        if self.selected_indices:
            for idx in self.selected_indices:
                if idx < len(self.artefact_summary):
                    mat = self.artefact_summary[idx]['material']
                    if mat:
                        materials.append(mat)
        else:
            materials = self.raw_materials

        if materials:
            material_counts = Counter(materials)
            labels = [f"{m[:12]}..." if len(m) > 12 else m for m in material_counts.keys()]
            sizes = list(material_counts.values())

            # Explode smallest slice
            explode = [0.05 if s == min(sizes) else 0 for s in sizes]

            ax.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
                  shadow=True, startangle=90)
            ax.axis('equal')
            ax.set_title('Raw Material Distribution')
        else:
            ax.text(0.5, 0.5, "No material data", ha='center', va='center',
                   transform=ax.transAxes, fontsize=12)

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.figures.append(fig)

    def _create_cortex_histogram(self, parent):
        """Create histogram of cortex percentage."""
        frame = ttk.LabelFrame(parent, text="Cortex Distribution", padding=10)
        frame.pack(fill="both", expand=True)

        fig = Figure(figsize=(5, 3), dpi=100)
        ax = fig.add_subplot(111)

        # Filter cortex based on selection
        cortex_vals = []
        if self.selected_indices:
            for idx in self.selected_indices:
                if idx < len(self.artefact_summary):
                    cortex = self.artefact_summary[idx]['cortex']
                    if cortex is not None:
                        cortex_vals.append(cortex)
        else:
            cortex_vals = self.cortex_pct

        if cortex_vals:
            ax.hist(cortex_vals, bins=10, edgecolor='black',
                   alpha=0.7, color='brown')
            ax.set_xlabel("Cortex %")
            ax.set_ylabel("Frequency")
            ax.set_title("Cortex Preservation")
            ax.grid(True, linestyle=':', alpha=0.6)

            # Add reduction stage indicators
            ax.axvline(x=50, color='red', linestyle='--', alpha=0.7, label='Primary/Secondary')
            ax.axvline(x=5, color='green', linestyle='--', alpha=0.7, label='Tertiary')
            ax.legend()
        else:
            ax.text(0.5, 0.5, "No cortex data", ha='center', va='center',
                   transform=ax.transAxes, fontsize=12)

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.figures.append(fig)

    def _create_data_table(self, parent):
        """Create table of artefact data."""
        frame = ttk.LabelFrame(parent, text="Artefact Inventory", padding=10)
        frame.pack(fill="x", padx=5, pady=5)

        cols = ["ID", "Length", "Width", "L/W", "Material", "Type"]
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=6)

        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=80, anchor="center")

        # Add data (filtered by selection or all)
        indices = self.selected_indices if self.selected_indices else range(len(self.artefact_summary))

        for i in sorted(indices)[:15]:  # Limit to 15 rows
            if i >= len(self.artefact_summary):
                continue

            artefact = self.artefact_summary[i]

            length = artefact['length'] or 0
            width = artefact['width'] or 0
            lw_ratio = length/width if width > 0 else 0
            material = artefact['material'][:10] if artefact['material'] else "-"
            a_type = artefact['type'][:10] if artefact['type'] else "-"

            tree.insert("", "end", values=(
                artefact['id'][:8],
                f"{length:.1f}" if length > 0 else "-",
                f"{width:.1f}" if width > 0 else "-",
                f"{lw_ratio:.2f}" if lw_ratio > 0 else "-",
                material,
                a_type
            ))

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind click to select main table row
        tree.bind('<ButtonRelease-1>', lambda e: self._on_table_click(e, tree))
        self.artefact_tree = tree

    def _on_table_click(self, event, tree):
        """Handle click on artefact table → select matching row in main table."""
        item = tree.identify_row(event.y)
        if not item:
            return
        try:
            # Get the index from the item's position in the tree
            # This is a simplified version; you might need to store indices in the tree
            idx = int(tree.index(item))
            if idx < len(self.artefact_summary):
                hub_idx = self.artefact_summary[idx]['index']
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
