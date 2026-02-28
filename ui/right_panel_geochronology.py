"""
Geochronology Right Panel (U-Pb)
==================================
Features:
  - Dynamic updates when rows are selected in main table
  - Scrollable interface for all content
  - Shows concordia diagram and age distributions
"""

import tkinter as tk
from tkinter import ttk
import numpy as np
import math
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from .right_panel import FieldPanelBase, OK_ICON, WARN_ICON, ERROR_ICON, INFO_ICON

# Decay constants
L238 = 1.55125e-10  # 238U decay constant (a⁻¹)
L235 = 9.8485e-10   # 235U decay constant (a⁻¹)


class GeochronologyPanel(FieldPanelBase):
    PANEL_ID = "geochronology"
    PANEL_NAME = "Geochronology"
    PANEL_ICON = "⏳"
    DETECT_COLUMNS = ['206pb', '238u', '207pb', '235u', 'pb206', 'u238', 'pb207', 'age']
    is_right_panel = True

    def __init__(self, parent, app):
        super().__init__(parent, app)

        # Initialize data storage
        self.ages_206 = []
        self.ages_207 = []
        self.ratios_206 = []
        self.ratios_207 = []
        self.discordance = []
        self.samples = []
        self.analysis_summary = []

        # Selection tracking
        self.selected_indices = set()

        # UI elements
        self.current_selection_label = None
        self.concordia_frame = None
        self.age_hist_frame = None
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
        self._redraw_concordia_plot()
        self._redraw_age_histogram()

    def _set_info_label(self):
        """Update selection info label."""
        if not hasattr(self, 'current_selection_label') or not self.current_selection_label:
            return

        if not self.selected_indices:
            text = "Showing: ALL analyses"
            color = "black"
        elif len(self.selected_indices) == 1:
            idx = next(iter(self.selected_indices))
            if idx < len(self.analysis_summary):
                text = f"Showing: Analysis {self.analysis_summary[idx].get('id', idx+1)}"
                color = "blue"
            else:
                text = "Showing: Selected analysis"
                color = "blue"
        else:
            text = f"Showing: {len(self.selected_indices)} selected analyses"
            color = "green"

        try:
            self.current_selection_label.config(text=text, foreground=color)
        except:
            pass

    def _redraw_concordia_plot(self):
        """Redraw concordia plot with current selection."""
        if not hasattr(self, 'concordia_frame') or not self.concordia_frame:
            return
        try:
            for widget in self.concordia_frame.winfo_children():
                widget.destroy()
            self._create_concordia_plot(self.concordia_frame)
        except:
            pass

    def _redraw_age_histogram(self):
        """Redraw age histogram with current selection."""
        if not hasattr(self, 'age_hist_frame') or not self.age_hist_frame:
            return
        try:
            for widget in self.age_hist_frame.winfo_children():
                widget.destroy()
            self._create_age_histogram(self.age_hist_frame)
        except:
            pass

    # ------------------------------------------------------------------
    # Data extraction
    # ------------------------------------------------------------------
    def _extract_data(self):
        """Extract U-Pb data from samples."""
        self.ages_206 = []
        self.ages_207 = []
        self.ratios_206 = []
        self.ratios_207 = []
        self.discordance = []
        self.analysis_summary = []

        if not self.samples:
            return

        # Find ratio columns
        r206_col = self._find_column(self.samples, '206pb/238', 'pb206_u238', '206_238', 'r206')
        r207_col = self._find_column(self.samples, '207pb/235', 'pb207_u235', '207_235', 'r207')

        # Find direct age columns
        age206_col = self._find_column(self.samples, '206_age', 'age206', 'age_206')
        age207_col = self._find_column(self.samples, '207_age', 'age207', 'age_207')

        for i, sample in enumerate(self.samples):
            analysis = {
                'index': i,
                'id': sample.get('Sample_ID', f"Analysis {i+1}"),
                'age_206': None,
                'age_207': None,
                'ratio_206': None,
                'ratio_207': None,
                'discordance': None,
                'raw_data': sample
            }

            # Try direct ages first
            if age206_col:
                age = self._tof(sample.get(age206_col))
                if age and age > 0:
                    self.ages_206.append(age)
                    analysis['age_206'] = age

            # Otherwise calculate from ratios
            if r206_col and not analysis['age_206']:
                r206 = self._tof(sample.get(r206_col))
                if r206 and r206 > 0:
                    self.ratios_206.append(r206)
                    analysis['ratio_206'] = r206
                    age = self._calc_age_238(r206)
                    if age:
                        self.ages_206.append(age)
                        analysis['age_206'] = age

            if r207_col:
                r207 = self._tof(sample.get(r207_col))
                if r207 and r207 > 0:
                    self.ratios_207.append(r207)
                    analysis['ratio_207'] = r207
                    age = self._calc_age_235(r207)
                    if age:
                        self.ages_207.append(age)
                        analysis['age_207'] = age

            # Calculate discordance if both ages available
            if analysis['age_206'] and analysis['age_207']:
                disc = abs(1 - analysis['age_207'] / analysis['age_206']) * 100
                self.discordance.append(disc)
                analysis['discordance'] = disc

            self.analysis_summary.append(analysis)

    def _calc_age_238(self, ratio):
        """Calculate 206Pb/238U age in Ma."""
        try:
            return math.log(1 + ratio) / L238 / 1e6
        except:
            return None

    def _calc_age_235(self, ratio):
        """Calculate 207Pb/235U age in Ma."""
        try:
            return math.log(1 + ratio) / L235 / 1e6
        except:
            return None

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
        rows.append(("N analyses", str(n)))

        if self.ages_206:
            mean_age = np.mean(self.ages_206)
            min_age = min(self.ages_206)
            max_age = max(self.ages_206)
            rows.append(("Mean ²⁰⁶Pb/²³⁸U age", f"{mean_age:.1f} Ma"))
            rows.append(("Age range", f"{min_age:.0f}-{max_age:.0f} Ma"))

            if len(self.ages_206) > 1:
                sd = np.std(self.ages_206)
                rows.append(("1σ uncertainty", f"±{sd:.1f} Ma"))

        return rows

    def _calc_validation(self, samples, columns):
        """Data validation."""
        rows = []

        if not samples:
            rows.append((WARN_ICON, "No data"))
            return rows

        # Check for required columns
        r206_col = self._find_column(samples, '206pb/238', 'pb206_u238', '206_238')
        r207_col = self._find_column(samples, '207pb/235', 'pb207_u235', '207_235')

        if r206_col:
            rows.append((OK_ICON, "²⁰⁶Pb/²³⁸U found"))
        else:
            rows.append((WARN_ICON, "No ²⁰⁶Pb/²³⁸U column"))

        if r207_col:
            rows.append((OK_ICON, "²⁰⁷Pb/²³⁵U found"))

        # Check concordance
        if self.discordance:
            discordant = sum(1 for d in self.discordance if d > 10)
            if discordant == 0:
                rows.append((OK_ICON, "All analyses concordant"))
            else:
                rows.append((WARN_ICON, f"{discordant} discordant >10%"))

        return rows

    def _calc_quick(self, samples, columns):
        """Quick calculations."""
        rows = []

        if not self.ages_206:
            rows.append(("Status", "No age data"))
            return rows

        # Weighted mean and MSWD
        n = len(self.ages_206)
        mean_age = np.mean(self.ages_206)
        sd = np.std(self.ages_206) if n > 1 else 0
        se = sd / math.sqrt(n) if n > 1 else 0

        rows.append(("Weighted mean", f"{mean_age:.1f} Ma"))
        rows.append(("2σ (2×SD)", f"±{2*sd:.1f} Ma"))

        if n > 1 and se > 0:
            mswd = (sd / se) ** 2
            rows.append(("MSWD", f"{mswd:.2f}"))

        # % concordant
        if self.discordance:
            concordant = sum(1 for d in self.discordance if d <= 10)
            pct_conc = (concordant / len(self.discordance)) * 100
            rows.append(("% concordant", f"{pct_conc:.0f}%"))

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
            text="Select rows in main table to filter analyses",
            font=("Segoe UI", 9, "italic")
        )
        self.current_selection_label.pack(side=tk.LEFT)

        # Concordia plot
        self.concordia_frame = ttk.Frame(container)
        self.concordia_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self._create_concordia_plot(self.concordia_frame)

        # Age histogram
        self.age_hist_frame = ttk.Frame(container)
        self.age_hist_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self._create_age_histogram(self.age_hist_frame)

        # Data table
        self._create_data_table(container)

    def _create_concordia_plot(self, parent):
        """Create Wetherill concordia plot."""
        frame = ttk.LabelFrame(parent, text="Concordia Diagram", padding=10)
        frame.pack(fill="both", expand=True)

        fig = Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)
        ax.set_xlabel("²⁰⁷Pb/²³⁵U")
        ax.set_ylabel("²⁰⁶Pb/²³⁸U")
        ax.set_title("Wetherill Concordia")
        ax.grid(True, linestyle=':', alpha=0.6)

        # Plot concordia curve
        t_values = np.linspace(10, 4500, 100)  # ages in Ma
        r207 = [np.exp(L235 * t * 1e6) - 1 for t in t_values]
        r206 = [np.exp(L238 * t * 1e6) - 1 for t in t_values]
        ax.plot(r207, r206, 'k-', linewidth=2, label='Concordia')

        # Collect data based on selection
        r206_vals = []
        r207_vals = []

        indices = self.selected_indices if self.selected_indices else range(len(self.analysis_summary))

        for idx in indices:
            if idx >= len(self.analysis_summary):
                continue
            analysis = self.analysis_summary[idx]
            if analysis['ratio_206'] is not None and analysis['ratio_207'] is not None:
                r206_vals.append(analysis['ratio_206'])
                r207_vals.append(analysis['ratio_207'])

        # Plot data points
        if r206_vals and r207_vals:
            if self.selected_indices:
                ax.scatter(r207_vals, r206_vals, c='red', edgecolors='black', s=50, zorder=5, alpha=0.7, label='Selected')
            else:
                ax.scatter(r207_vals, r206_vals, c='blue', edgecolors='black', s=50, zorder=5, alpha=0.7, label='All')
            ax.legend()

            # Add age ticks
            for t in [500, 1000, 2000, 3000]:
                x = np.exp(L235 * t * 1e6) - 1
                y = np.exp(L238 * t * 1e6) - 1
                ax.plot(x, y, 'ko', markersize=3)
                ax.annotate(f"{t} Ma", (x, y), xytext=(5, 5),
                           textcoords='offset points', fontsize=8)

            # Set axis limits
            max_x = max(r207_vals) * 1.1
            max_y = max(r206_vals) * 1.1
            ax.set_xlim(0, max_x)
            ax.set_ylim(0, max_y)
        else:
            ax.text(0.5, 0.5, "No ratio data to plot", ha='center', va='center',
                   transform=ax.transAxes, fontsize=10)

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.figures.append(fig)

    def _create_age_histogram(self, parent):
        """Create histogram of ages."""
        frame = ttk.LabelFrame(parent, text="Age Distribution", padding=10)
        frame.pack(fill="both", expand=True)

        fig = Figure(figsize=(5, 3), dpi=100)
        ax = fig.add_subplot(111)
        ax.set_xlabel("Age (Ma)")
        ax.set_ylabel("Frequency")
        ax.set_title("²⁰⁶Pb/²³⁸U Age Distribution")
        ax.grid(True, linestyle=':', alpha=0.6)

        # Collect data based on selection
        ages = []

        indices = self.selected_indices if self.selected_indices else range(len(self.analysis_summary))

        for idx in indices:
            if idx >= len(self.analysis_summary):
                continue
            analysis = self.analysis_summary[idx]
            if analysis['age_206'] is not None:
                ages.append(analysis['age_206'])

        if ages:
            n_bins = max(5, min(20, len(ages) // 3))
            ax.hist(ages, bins=n_bins, edgecolor='black',
                   alpha=0.7, color='steelblue')

            # Add statistics
            stats = (f"n = {len(ages)}\n"
                    f"mean = {np.mean(ages):.1f} Ma\n"
                    f"median = {np.median(ages):.1f} Ma")
            ax.text(0.95, 0.95, stats, transform=ax.transAxes,
                   fontsize=8, verticalalignment='top', horizontalalignment='right',
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        else:
            ax.text(0.5, 0.5, "No age data", ha='center', va='center',
                   transform=ax.transAxes, fontsize=10)

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.figures.append(fig)

    def _create_data_table(self, parent):
        """Create table of ages and discordance."""
        frame = ttk.LabelFrame(parent, text="Analysis Details", padding=10)
        frame.pack(fill="x", padx=5, pady=5)

        cols = ["Sample", "²⁰⁶Pb/²³⁸U Age", "²⁰⁷Pb/²³⁵U Age", "Discordance"]
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=6)

        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=90, anchor="center")

        # Filter data based on selection
        indices = self.selected_indices if self.selected_indices else range(len(self.analysis_summary))

        for i in sorted(indices)[:20]:  # Limit to 20 rows
            if i >= len(self.analysis_summary):
                continue

            analysis = self.analysis_summary[i]

            sample_id = analysis['id']
            if len(sample_id) > 10:
                sample_id = sample_id[:8] + "…"

            age206 = f"{analysis['age_206']:.1f}" if analysis['age_206'] is not None else "-"
            age207 = f"{analysis['age_207']:.1f}" if analysis['age_207'] is not None else "-"
            disc = f"{analysis['discordance']:.1f}%" if analysis['discordance'] is not None else "-"

            tree.insert("", "end", values=(sample_id, age206, age207, disc))

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
            if idx < len(self.analysis_summary):
                hub_idx = self.analysis_summary[idx]['index']
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
