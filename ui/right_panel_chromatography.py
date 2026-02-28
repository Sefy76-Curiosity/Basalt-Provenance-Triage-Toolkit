"""
Chromatography Right Panel (GC/HPLC/LC-MS)
=============================================
Features:
  - Dynamic updates when rows are selected in main table
  - Scrollable interface for all content
  - Shows chromatogram and peak data
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


class ChromatographyPanel(FieldPanelBase):
    PANEL_ID = "chromatography"
    PANEL_NAME = "Chromatography"
    PANEL_ICON = "🧪"
    DETECT_COLUMNS = ['retention_time', 'rt', 'peak_area', 'area',
                      'concentration', 'analyte', 'compound', 'peak_height']
    is_right_panel = True

    def __init__(self, parent, app):
        super().__init__(parent, app)

        # Initialize data storage
        self.retention_times = []
        self.areas = []
        self.heights = []
        self.compounds = []
        self.concentrations = []
        self.samples = []
        self.peak_summary = []

        # Calibration data
        self.calibration_curve = None
        self.calibration_r2 = None
        self.calibration_slope = None
        self.calibration_intercept = None

        # Selection tracking
        self.selected_indices = set()

        # UI elements
        self.current_selection_label = None
        self.chromatogram_frame = None
        self.calibration_frame = None
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
        self._redraw_chromatogram()
        self._redraw_calibration()

    def _set_info_label(self):
        """Update selection info label."""
        if not hasattr(self, 'current_selection_label') or not self.current_selection_label:
            return

        if not self.selected_indices:
            text = "Showing: ALL peaks"
            color = "black"
        elif len(self.selected_indices) == 1:
            idx = next(iter(self.selected_indices))
            if idx < len(self.peak_summary):
                text = f"Showing: Peak {self.peak_summary[idx].get('compound', idx+1)}"
                color = "blue"
            else:
                text = "Showing: Selected peak"
                color = "blue"
        else:
            text = f"Showing: {len(self.selected_indices)} selected peaks"
            color = "green"

        try:
            self.current_selection_label.config(text=text, foreground=color)
        except:
            pass

    def _redraw_chromatogram(self):
        """Redraw chromatogram with current selection."""
        if not hasattr(self, 'chromatogram_frame') or not self.chromatogram_frame:
            return
        try:
            for widget in self.chromatogram_frame.winfo_children():
                widget.destroy()
            self._create_chromatogram(self.chromatogram_frame)
        except:
            pass

    def _redraw_calibration(self):
        """Redraw calibration plot with current selection."""
        if not hasattr(self, 'calibration_frame') or not self.calibration_frame:
            return
        try:
            for widget in self.calibration_frame.winfo_children():
                widget.destroy()
            self._create_calibration_plot(self.calibration_frame)
        except:
            pass

    # ------------------------------------------------------------------
    # Data extraction
    # ------------------------------------------------------------------
    def _extract_data(self):
        """Extract chromatographic data from samples."""
        self.retention_times = []
        self.areas = []
        self.heights = []
        self.compounds = []
        self.concentrations = []
        self.peak_summary = []

        if not self.samples:
            return

        # Find columns
        rt_col = self._find_column(self.samples, 'retention_time', 'rt', 'ret_time', 'time')
        area_col = self._find_column(self.samples, 'peak_area', 'area', 'peak_area')
        height_col = self._find_column(self.samples, 'peak_height', 'height')
        compound_col = self._find_column(self.samples, 'compound', 'analyte', 'peak_name', 'name')
        conc_col = self._find_column(self.samples, 'concentration', 'conc', 'amount')

        for i, sample in enumerate(self.samples):
            peak = {
                'index': i,
                'id': sample.get('Sample_ID', f"Peak {i+1}"),
                'rt': None,
                'area': None,
                'height': None,
                'compound': None,
                'concentration': None,
                'raw_data': sample
            }

            # Retention time
            if rt_col:
                rt = self._tof(sample.get(rt_col))
                if rt is not None and rt > 0:
                    self.retention_times.append(rt)
                    peak['rt'] = rt

            # Peak area
            if area_col:
                area = self._tof(sample.get(area_col))
                if area is not None:
                    self.areas.append(area)
                    peak['area'] = area

            # Peak height
            if height_col:
                height = self._tof(sample.get(height_col))
                if height is not None:
                    self.heights.append(height)
                    peak['height'] = height

            # Compound name
            if compound_col:
                compound = sample.get(compound_col)
                if compound:
                    self.compounds.append(str(compound))
                    peak['compound'] = str(compound)

            # Concentration
            if conc_col:
                conc = self._tof(sample.get(conc_col))
                if conc is not None:
                    self.concentrations.append(conc)
                    peak['concentration'] = conc

            self.peak_summary.append(peak)

        # Try to build calibration curve
        self._build_calibration()

    def _build_calibration(self):
        """Build linear calibration curve from area vs concentration."""
        self.calibration_curve = None
        self.calibration_r2 = None
        self.calibration_slope = None
        self.calibration_intercept = None

        # Get data based on selection or all
        indices = self.selected_indices if self.selected_indices else range(len(self.peak_summary))

        x_vals = []
        y_vals = []

        for idx in indices:
            if idx < len(self.peak_summary):
                peak = self.peak_summary[idx]
                if peak['concentration'] is not None and peak['area'] is not None:
                    if peak['concentration'] > 0 and peak['area'] > 0:
                        x_vals.append(peak['concentration'])
                        y_vals.append(peak['area'])

        if len(x_vals) < 3:
            return

        x = np.array(x_vals)
        y = np.array(y_vals)

        # Linear regression
        from scipy import stats
        try:
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            self.calibration_slope = slope
            self.calibration_intercept = intercept
            self.calibration_r2 = r_value**2
            self.calibration_curve = (x, y, slope * x + intercept)
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
        rows.append(("N peaks", str(n)))

        if self.retention_times:
            rows.append(("RT range", f"{min(self.retention_times):.2f}-{max(self.retention_times):.2f} min"))

        if self.areas:
            rows.append(("Total area", f"{sum(self.areas):.2e}"))
            rows.append(("Max area", f"{max(self.areas):.2e}"))

        if self.compounds:
            unique_compounds = len(set(self.compounds))
            rows.append(("Unique compounds", str(unique_compounds)))

        return rows

    def _calc_validation(self, samples, columns):
        """Data validation."""
        rows = []

        if not samples:
            rows.append((WARN_ICON, "No data"))
            return rows

        # Check for required columns
        rt_col = self._find_column(samples, 'retention_time', 'rt')
        area_col = self._find_column(samples, 'peak_area', 'area')

        if rt_col:
            rows.append((OK_ICON, f"RT column: {rt_col}"))
        else:
            rows.append((WARN_ICON, "No retention time column"))

        if area_col:
            rows.append((OK_ICON, f"Area column: {area_col}"))
        else:
            rows.append((INFO_ICON, "No area column"))

        # Validate retention times
        if self.retention_times:
            bad_rt = sum(1 for rt in self.retention_times if rt <= 0)
            if bad_rt == 0:
                rows.append((OK_ICON, "All RT > 0"))
            else:
                rows.append((WARN_ICON, f"{bad_rt} RT ≤ 0"))

        return rows

    def _calc_quick(self, samples, columns):
        """Quick calculations."""
        rows = []

        if self.areas:
            rows.append(("Total area", f"{sum(self.areas):.2e}"))

        # Most abundant peak
        if self.areas and self.compounds and len(self.areas) == len(self.compounds):
            max_idx = np.argmax(self.areas)
            top_compound = self.compounds[max_idx][:15]
            top_area = self.areas[max_idx]
            rows.append(("Top peak", f"{top_compound} ({top_area:.2e})"))
        elif self.areas:
            rows.append(("Max area", f"{max(self.areas):.2e}"))

        # Calibration quality
        if self.calibration_r2 is not None:
            rows.append(("Calibration R²", f"{self.calibration_r2:.4f}"))
            if self.calibration_r2 < 0.99:
                rows.append((WARN_ICON, "R² < 0.99"))

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
            text="Select rows in main table to filter peaks",
            font=("Segoe UI", 9, "italic")
        )
        self.current_selection_label.pack(side=tk.LEFT)

        # Chromatogram
        self.chromatogram_frame = ttk.Frame(container)
        self.chromatogram_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self._create_chromatogram(self.chromatogram_frame)

        # Calibration plot
        self.calibration_frame = ttk.Frame(container)
        self.calibration_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self._create_calibration_plot(self.calibration_frame)

        # Peak table
        self._create_peak_table(container)

    def _create_chromatogram(self, parent):
        """Create simulated chromatogram."""
        frame = ttk.LabelFrame(parent, text="Chromatogram", padding=10)
        frame.pack(fill="both", expand=True)

        fig = Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)

        ax.set_xlabel("Retention Time (min)")
        ax.set_ylabel("Intensity")
        ax.set_title("Chromatogram")
        ax.grid(True, linestyle=':', alpha=0.6)

        # Filter data based on selection
        rts = []
        areas = []
        compounds = []

        indices = self.selected_indices if self.selected_indices else range(len(self.peak_summary))

        for idx in indices:
            if idx < len(self.peak_summary):
                peak = self.peak_summary[idx]
                if peak['rt'] is not None and peak['area'] is not None:
                    rts.append(peak['rt'])
                    areas.append(peak['area'])
                    compounds.append(peak['compound'] or f"Peak {len(compounds)+1}")

        if rts and areas:
            # Create simulated peaks (Gaussian shapes)
            rt_array = np.linspace(0, max(rts) * 1.1, 1000)
            signal = np.zeros_like(rt_array)

            for rt, area in zip(rts, areas):
                # Gaussian peak
                width = 0.1  # approximate peak width
                peak = area * np.exp(-((rt_array - rt) ** 2) / (2 * width ** 2))
                signal += peak

            ax.plot(rt_array, signal, 'b-', linewidth=1.5)

            # Mark peak positions
            ax.scatter(rts, [max(signal)] * len(rts),
                      c='red', s=20, zorder=5, alpha=0.7)

            # Label major peaks
            for i, (rt, area, comp) in enumerate(zip(rts, areas, compounds)):
                if area > max(areas) * 0.1:  # Only label significant peaks
                    ax.annotate(comp[:8], (rt, max(signal) * 0.9),
                               rotation=45, fontsize=8)
        else:
            ax.text(0.5, 0.5, "No chromatographic data", ha='center', va='center',
                   transform=ax.transAxes, fontsize=12)

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.figures.append(fig)

    def _create_calibration_plot(self, parent):
        """Create calibration curve plot."""
        frame = ttk.LabelFrame(parent, text="Calibration Curve", padding=10)
        frame.pack(fill="both", expand=True)

        fig = Figure(figsize=(5, 3), dpi=100)
        ax = fig.add_subplot(111)

        if self.calibration_curve is not None:
            x, y, y_fit = self.calibration_curve

            ax.scatter(x, y, c='blue', s=50, alpha=0.7, label='Standards')
            ax.plot(x, y_fit, 'r-', linewidth=2,
                   label=f'R² = {self.calibration_r2:.4f}')

            ax.set_xlabel("Concentration")
            ax.set_ylabel("Peak Area")
            ax.set_title("Calibration Curve")
            ax.legend()
            ax.grid(True, linestyle=':', alpha=0.6)

            # Add equation
            if self.calibration_slope and self.calibration_intercept:
                eqn = f"y = {self.calibration_slope:.2e}x + {self.calibration_intercept:.2e}"
                ax.text(0.05, 0.95, eqn, transform=ax.transAxes,
                       fontsize=9, verticalalignment='top',
                       bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        else:
            ax.text(0.5, 0.5, "Need area and concentration data\nfor calibration",
                   ha='center', va='center', transform=ax.transAxes,
                   fontsize=11, multialignment='center')

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.figures.append(fig)

    def _create_peak_table(self, parent):
        """Create table of detected peaks."""
        frame = ttk.LabelFrame(parent, text="Peak List", padding=10)
        frame.pack(fill="x", padx=5, pady=5)

        cols = ["RT (min)", "Area", "Height", "Compound"]
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=8)

        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=90, anchor="center")

        # Filter data based on selection
        indices = self.selected_indices if self.selected_indices else range(len(self.peak_summary))

        for i in sorted(indices)[:20]:  # Limit to 20 rows
            if i >= len(self.peak_summary):
                continue

            peak = self.peak_summary[i]

            rt = f"{peak['rt']:.2f}" if peak['rt'] is not None else "-"
            area = f"{peak['area']:.2e}" if peak['area'] is not None else "-"
            height = f"{peak['height']:.2e}" if peak['height'] is not None else "-"
            compound = peak['compound'][:15] if peak['compound'] else f"Peak {i+1}"

            tree.insert("", "end", values=(rt, area, height, compound))

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind click to select main table row
        tree.bind('<ButtonRelease-1>', lambda e: self._on_table_click(e, tree))
        self.peak_tree = tree

    def _on_table_click(self, event, tree):
        """Handle click on peak table → select matching row in main table."""
        item = tree.identify_row(event.y)
        if not item:
            return
        try:
            idx = int(tree.index(item))
            if idx < len(self.peak_summary):
                hub_idx = self.peak_summary[idx]['index']
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
