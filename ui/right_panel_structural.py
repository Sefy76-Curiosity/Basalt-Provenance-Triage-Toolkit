"""
Structural Geology Right Panel
================================
Features:
  - Dynamic updates when rows are selected in main table
  - Scrollable interface for all content
  - Shows structural measurements (strike/dip, fold axes, etc.) on stereonet
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
from matplotlib.patches import Circle as MplCircle

from .right_panel import FieldPanelBase, OK_ICON, WARN_ICON, ERROR_ICON, INFO_ICON


class StructuralPanel(FieldPanelBase):
    PANEL_ID = "structural"
    PANEL_NAME = "Structural Geology"
    PANEL_ICON = "⚒️"
    DETECT_COLUMNS = ['strike', 'dip', 'dip_direction', 'azimuth', 'plunge',
                      'trend', 'rake', 'pitch', 'fold_axis', 'lineation']
    is_right_panel = True

    def __init__(self, parent, app):
        super().__init__(parent, app)

        # Initialize data storage
        self.strike = []
        self.dip = []
        self.dip_direction = []
        self.trend = []
        self.plunge = []
        self.rake = []
        self.structure_type = []
        self.samples = []
        self.measurement_summary = []

        # Selection tracking
        self.selected_indices = set()

        # UI elements
        self.current_selection_label = None
        self.stereonet_frame = None
        self.rose_frame = None
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
        self._redraw_stereonet()
        self._redraw_rose_diagram()

    def _set_info_label(self):
        """Update selection info label."""
        if not hasattr(self, 'current_selection_label') or not self.current_selection_label:
            return

        if not self.selected_indices:
            text = "Showing: ALL measurements"
            color = "black"
        elif len(self.selected_indices) == 1:
            idx = next(iter(self.selected_indices))
            if idx < len(self.measurement_summary):
                text = f"Showing: Measurement {self.measurement_summary[idx].get('id', idx+1)}"
                color = "blue"
            else:
                text = "Showing: Selected measurement"
                color = "blue"
        else:
            text = f"Showing: {len(self.selected_indices)} selected measurements"
            color = "green"

        try:
            self.current_selection_label.config(text=text, foreground=color)
        except:
            pass

    def _redraw_stereonet(self):
        """Redraw stereonet with current selection."""
        if not hasattr(self, 'stereonet_frame') or not self.stereonet_frame:
            return
        try:
            for widget in self.stereonet_frame.winfo_children():
                widget.destroy()
            self._create_stereonet(self.stereonet_frame)
        except:
            pass

    def _redraw_rose_diagram(self):
        """Redraw rose diagram with current selection."""
        if not hasattr(self, 'rose_frame') or not self.rose_frame:
            return
        try:
            for widget in self.rose_frame.winfo_children():
                widget.destroy()
            self._create_rose_diagram(self.rose_frame)
        except:
            pass

    # ------------------------------------------------------------------
    # Data extraction
    # ------------------------------------------------------------------
    def _extract_data(self):
        """Extract structural data from samples."""
        self.strike = []
        self.dip = []
        self.dip_direction = []
        self.trend = []
        self.plunge = []
        self.rake = []
        self.structure_type = []
        self.measurement_summary = []

        if not self.samples:
            return

        # Find columns
        strike_col = self._find_column(self.samples, 'strike')
        dip_col = self._find_column(self.samples, 'dip')
        dip_dir_col = self._find_column(self.samples, 'dip_direction', 'dip_dir')
        trend_col = self._find_column(self.samples, 'trend', 'azimuth')
        plunge_col = self._find_column(self.samples, 'plunge')
        rake_col = self._find_column(self.samples, 'rake', 'pitch')
        type_col = self._find_column(self.samples, 'structure_type', 'type', 'feature')

        for i, sample in enumerate(self.samples):
            measurement = {
                'index': i,
                'id': sample.get('Sample_ID', f"Measurement {i+1}"),
                'strike': None,
                'dip': None,
                'dip_direction': None,
                'trend': None,
                'plunge': None,
                'rake': None,
                'type': None,
                'raw_data': sample
            }

            # Strike/dip measurements
            if strike_col:
                s = self._tof(sample.get(strike_col))
                if s is not None and 0 <= s <= 360:
                    self.strike.append(s)
                    measurement['strike'] = s

            if dip_col:
                d = self._tof(sample.get(dip_col))
                if d is not None and 0 <= d <= 90:
                    self.dip.append(d)
                    measurement['dip'] = d

            if dip_dir_col:
                dd = self._tof(sample.get(dip_dir_col))
                if dd is not None and 0 <= dd <= 360:
                    self.dip_direction.append(dd)
                    measurement['dip_direction'] = dd

            # Lineation measurements
            if trend_col:
                t = self._tof(sample.get(trend_col))
                if t is not None and 0 <= t <= 360:
                    self.trend.append(t)
                    measurement['trend'] = t

            if plunge_col:
                p = self._tof(sample.get(plunge_col))
                if p is not None and 0 <= p <= 90:
                    self.plunge.append(p)
                    measurement['plunge'] = p

            if rake_col:
                r = self._tof(sample.get(rake_col))
                if r is not None and 0 <= r <= 180:
                    self.rake.append(r)
                    measurement['rake'] = r

            # Structure type
            if type_col:
                typ = sample.get(type_col)
                if typ:
                    self.structure_type.append(str(typ))
                    measurement['type'] = str(typ)

            self.measurement_summary.append(measurement)

    def _calculate_dip_direction_from_strike(self, strike, dip):
        """Calculate dip direction from strike (using right-hand rule)."""
        if strike is None or dip is None:
            return None
        # Right-hand rule: dip direction = strike + 90°
        dd = (strike + 90) % 360
        return dd

    def _stereographic_projection(self, strike, dip):
        """Calculate stereographic projection coordinates for a plane."""
        # Convert to radians
        strike_rad = math.radians(strike)
        dip_rad = math.radians(dip)

        # Calculate pole coordinates
        theta = strike_rad + math.pi/2  # Pole direction is perpendicular to strike
        rho = math.pi/2 - dip_rad  # Pole plunge

        # Convert to x,y coordinates (Schmidt net - equal area)
        R = math.sqrt(2) * math.sin(rho/2)
        x = R * math.sin(theta)
        y = R * math.cos(theta)

        return x, y

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
        rows.append(("N measurements", str(n)))

        if self.strike:
            rows.append(("Strike range", f"{min(self.strike):.0f}°-{max(self.strike):.0f}°"))
            rows.append(("Mean strike", f"{np.mean(self.strike):.0f}°"))

        if self.dip:
            rows.append(("Dip range", f"{min(self.dip):.0f}°-{max(self.dip):.0f}°"))
            rows.append(("Mean dip", f"{np.mean(self.dip):.0f}°"))

        if self.trend:
            rows.append(("Trend range", f"{min(self.trend):.0f}°-{max(self.trend):.0f}°"))

        if self.plunge:
            rows.append(("Plunge range", f"{min(self.plunge):.0f}°-{max(self.plunge):.0f}°"))

        if self.structure_type:
            unique_types = len(set(self.structure_type))
            rows.append(("Structure types", str(unique_types)))

        return rows

    def _calc_validation(self, samples, columns):
        """Data validation."""
        rows = []

        if not samples:
            rows.append((WARN_ICON, "No data"))
            return rows

        # Check strike values
        if self.strike:
            bad_strike = sum(1 for s in self.strike if not (0 <= s <= 360))
            if bad_strike == 0:
                rows.append((OK_ICON, "All strikes valid (0-360°)"))
            else:
                rows.append((ERROR_ICON, f"{bad_strike} invalid strikes"))

        # Check dip values
        if self.dip:
            bad_dip = sum(1 for d in self.dip if not (0 <= d <= 90))
            if bad_dip == 0:
                rows.append((OK_ICON, "All dips valid (0-90°)"))
            else:
                rows.append((ERROR_ICON, f"{bad_dip} invalid dips"))

        # Check for required pairs
        if self.strike and not self.dip:
            rows.append((WARN_ICON, "Strike without dip"))
        if self.dip and not self.strike:
            rows.append((WARN_ICON, "Dip without strike"))

        # Check lineation data
        if self.trend and not self.plunge:
            rows.append((WARN_ICON, "Trend without plunge"))
        if self.plunge and not self.trend:
            rows.append((WARN_ICON, "Plunge without trend"))

        return rows

    def _calc_quick(self, samples, columns):
        """Quick calculations."""
        rows = []

        # Principal orientations
        if self.strike:
            # Calculate mean strike (circular mean)
            sin_sum = sum(math.sin(math.radians(s)) for s in self.strike)
            cos_sum = sum(math.cos(math.radians(s)) for s in self.strike)
            mean_strike = math.degrees(math.atan2(sin_sum, cos_sum)) % 360
            rows.append(("Mean strike", f"{mean_strike:.0f}°"))

        if self.dip:
            rows.append(("Mean dip", f"{np.mean(self.dip):.0f}°"))

        # Structural style
        if self.dip and self.strike:
            steep_dips = sum(1 for d in self.dip if d > 60)
            gentle_dips = sum(1 for d in self.dip if d < 30)
            if steep_dips > len(self.dip)/2:
                rows.append(("Style", "Steeply dipping"))
            elif gentle_dips > len(self.dip)/2:
                rows.append(("Style", "Gently dipping"))
            else:
                rows.append(("Style", "Moderate dip"))

        # Most common structure type
        if self.structure_type:
            type_counts = Counter(self.structure_type)
            most_common = type_counts.most_common(1)[0]
            rows.append(("Most common", f"{most_common[0]} ({most_common[1]})"))

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
            text="Select rows in main table to filter measurements",
            font=("Segoe UI", 9, "italic")
        )
        self.current_selection_label.pack(side=tk.LEFT)

        # Stereonet plot
        self.stereonet_frame = ttk.Frame(container)
        self.stereonet_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self._create_stereonet(self.stereonet_frame)

        # Rose diagram
        self.rose_frame = ttk.Frame(container)
        self.rose_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self._create_rose_diagram(self.rose_frame)

        # Data table
        self._create_data_table(container)

    def _create_stereonet(self, parent):
        """Create stereonet plot for structural data."""
        frame = ttk.LabelFrame(parent, text="Stereonet (Equal Area)", padding=10)
        frame.pack(fill="both", expand=True)

        fig = Figure(figsize=(5, 5), dpi=100)
        ax = fig.add_subplot(111)

        # Draw the stereonet circle
        circle = MplCircle((0, 0), 1, fill=False, color='black', linewidth=1)
        ax.add_patch(circle)

        # Draw grid lines (simplified)
        for angle in range(0, 360, 30):
            rad = math.radians(angle)
            x = [0, math.sin(rad)]
            y = [0, math.cos(rad)]
            ax.plot(x, y, 'gray', linewidth=0.5, alpha=0.3)

        # Draw dip circles
        for dip in range(10, 90, 10):
            rho = math.radians(90 - dip)
            R = math.sqrt(2) * math.sin(rho/2)
            circle = MplCircle((0, 0), R, fill=False, color='gray', linewidth=0.5, alpha=0.3)
            ax.add_patch(circle)

        ax.set_xlim(-1.1, 1.1)
        ax.set_ylim(-1.1, 1.1)
        ax.set_aspect('equal')
        ax.set_title("Stereographic Projection")
        ax.set_xticks([])
        ax.set_yticks([])

        # Plot data points based on selection
        indices = self.selected_indices if self.selected_indices else range(len(self.measurement_summary))

        for idx in indices:
            if idx >= len(self.measurement_summary):
                continue
            meas = self.measurement_summary[idx]

            # Plot planes if we have strike/dip
            if meas['strike'] is not None and meas['dip'] is not None:
                x, y = self._stereographic_projection(meas['strike'], meas['dip'])
                if self.selected_indices:
                    ax.plot(x, y, 'ro', markersize=6, alpha=0.7)
                else:
                    ax.plot(x, y, 'bo', markersize=4, alpha=0.5)

            # Plot lineations if we have trend/plunge
            if meas['trend'] is not None and meas['plunge'] is not None:
                # Convert lineation to point on stereonet
                trend_rad = math.radians(meas['trend'])
                plunge_rad = math.radians(meas['plunge'])
                rho = math.pi/2 - plunge_rad
                R = math.sqrt(2) * math.sin(rho/2)
                x = R * math.sin(trend_rad)
                y = R * math.cos(trend_rad)

                if self.selected_indices:
                    ax.plot(x, y, 'g^', markersize=6, alpha=0.7)
                else:
                    ax.plot(x, y, 'g^', markersize=4, alpha=0.5)

        # Add north indicator
        ax.annotate('N', (0, 1.05), ha='center', va='center', fontweight='bold')

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.figures.append(fig)

    def _create_rose_diagram(self, parent):
        """Create rose diagram for strike/orientation data."""
        frame = ttk.LabelFrame(parent, text="Rose Diagram", padding=10)
        frame.pack(fill="both", expand=True)

        fig = Figure(figsize=(5, 4), dpi=100)

        # Collect strike data based on selection
        strikes = []

        indices = self.selected_indices if self.selected_indices else range(len(self.measurement_summary))

        for idx in indices:
            if idx >= len(self.measurement_summary):
                continue
            meas = self.measurement_summary[idx]
            if meas['strike'] is not None:
                strikes.append(meas['strike'])

        if strikes:
            # Create polar histogram
            ax = fig.add_subplot(111, projection='polar')

            # Convert strikes to radians (for rose diagram, we double the angles)
            directions = np.radians(strikes)
            # Double the angles for bidirectional data
            directions = np.concatenate([directions, directions + np.pi])

            # Create histogram
            n_bins = 18  # 20° bins
            theta = np.linspace(0, 2*np.pi, n_bins, endpoint=False)
            width = 2*np.pi / n_bins

            hist, _ = np.histogram(directions, bins=n_bins, range=(0, 2*np.pi))

            # Plot bars
            bars = ax.bar(theta, hist, width=width, alpha=0.7, color='steelblue', edgecolor='black')
            ax.set_theta_zero_location('N')
            ax.set_theta_direction(-1)
            ax.set_title('Strike Orientation')
            ax.grid(True, alpha=0.3)

            # Add mean strike line
            if strikes:
                # Circular mean
                sin_sum = sum(math.sin(math.radians(s * 2)) for s in strikes)
                cos_sum = sum(math.cos(math.radians(s * 2)) for s in strikes)
                mean_dir = (math.atan2(sin_sum, cos_sum) / 2) % 360  # Halve to get back to strike
                mean_rad = math.radians(mean_dir)
                ax.plot([0, mean_rad], [0, max(hist)], 'r-', linewidth=2, label=f'Mean: {mean_dir:.0f}°')
                ax.legend(loc='upper right')
        else:
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, "No strike data", ha='center', va='center',
                   transform=ax.transAxes, fontsize=12)

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.figures.append(fig)

    def _create_data_table(self, parent):
        """Create table of structural measurements."""
        frame = ttk.LabelFrame(parent, text="Measurements", padding=10)
        frame.pack(fill="x", padx=5, pady=5)

        cols = ["ID", "Strike", "Dip", "Dip Dir", "Trend", "Plunge", "Type"]
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=6)

        for col in cols:
            tree.heading(col, text=col)
            if col in ["Strike", "Dip", "Dip Dir", "Trend", "Plunge"]:
                tree.column(col, width=60, anchor="center")
            elif col == "Type":
                tree.column(col, width=80, anchor="w")
            else:
                tree.column(col, width=70, anchor="w")

        # Filter data based on selection
        indices = self.selected_indices if self.selected_indices else range(len(self.measurement_summary))

        for i in sorted(indices)[:20]:  # Limit to 20 rows
            if i >= len(self.measurement_summary):
                continue

            meas = self.measurement_summary[i]

            mid = meas['id'][:8]
            strike = f"{meas['strike']:.0f}°" if meas['strike'] is not None else "-"
            dip = f"{meas['dip']:.0f}°" if meas['dip'] is not None else "-"
            dip_dir = f"{meas['dip_direction']:.0f}°" if meas['dip_direction'] is not None else "-"
            trend = f"{meas['trend']:.0f}°" if meas['trend'] is not None else "-"
            plunge = f"{meas['plunge']:.0f}°" if meas['plunge'] is not None else "-"
            typ = meas['type'][:10] if meas['type'] else "-"

            tree.insert("", "end", values=(mid, strike, dip, dip_dir, trend, plunge, typ))

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
            if idx < len(self.measurement_summary):
                hub_idx = self.measurement_summary[idx]['index']
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
