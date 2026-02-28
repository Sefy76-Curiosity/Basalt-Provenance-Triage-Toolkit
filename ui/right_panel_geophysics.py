"""
Geophysics Right Panel
========================
Features:
  - Dynamic updates when rows are selected in main table
  - Scrollable interface for all content
  - Shows anomaly profiles and station maps
"""

import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from .right_panel import FieldPanelBase, OK_ICON, WARN_ICON, ERROR_ICON, INFO_ICON


class GeophysicsPanel(FieldPanelBase):
    PANEL_ID = "geophysics"
    PANEL_NAME = "Geophysics"
    PANEL_ICON = "🌍"
    DETECT_COLUMNS = ['gravity', 'g_obs', 'magnetic', 'mag_obs', 'total_field',
                      'elevation', 'altitude', 'bouguer', 'igrf', 'free_air']
    is_right_panel = True

    def __init__(self, parent, app):
        super().__init__(parent, app)

        # Initialize data storage
        self.elevation = []
        self.gravity_obs = []
        self.magnetic_obs = []
        self.igrf = []
        self.latitude = []
        self.longitude = []
        self.station_id = []
        self.samples = []
        self.station_summary = []

        # Derived anomalies
        self.free_air_anomaly = []
        self.bouguer_anomaly = []
        self.magnetic_anomaly = []

        # Selection tracking
        self.selected_indices = set()

        # UI elements
        self.current_selection_label = None
        self.anomaly_profile_frame = None
        self.station_map_frame = None
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
        self._redraw_anomaly_profile()
        self._redraw_station_map()

    def _set_info_label(self):
        """Update selection info label."""
        if not hasattr(self, 'current_selection_label') or not self.current_selection_label:
            return

        if not self.selected_indices:
            text = "Showing: ALL stations"
            color = "black"
        elif len(self.selected_indices) == 1:
            idx = next(iter(self.selected_indices))
            if idx < len(self.station_summary):
                text = f"Showing: Station {self.station_summary[idx].get('id', idx+1)}"
                color = "blue"
            else:
                text = "Showing: Selected station"
                color = "blue"
        else:
            text = f"Showing: {len(self.selected_indices)} selected stations"
            color = "green"

        try:
            self.current_selection_label.config(text=text, foreground=color)
        except:
            pass

    def _redraw_anomaly_profile(self):
        """Redraw anomaly profile with current selection."""
        if not hasattr(self, 'anomaly_profile_frame') or not self.anomaly_profile_frame:
            return
        try:
            for widget in self.anomaly_profile_frame.winfo_children():
                widget.destroy()
            self._create_anomaly_profile(self.anomaly_profile_frame)
        except:
            pass

    def _redraw_station_map(self):
        """Redraw station map with current selection."""
        if not hasattr(self, 'station_map_frame') or not self.station_map_frame:
            return
        try:
            for widget in self.station_map_frame.winfo_children():
                widget.destroy()
            self._create_station_map(self.station_map_frame)
        except:
            pass

    # ------------------------------------------------------------------
    # Data extraction
    # ------------------------------------------------------------------
    def _extract_data(self):
        """Extract geophysical data from samples."""
        self.elevation = []
        self.gravity_obs = []
        self.magnetic_obs = []
        self.igrf = []
        self.latitude = []
        self.longitude = []
        self.station_id = []
        self.station_summary = []

        self.free_air_anomaly = []
        self.bouguer_anomaly = []
        self.magnetic_anomaly = []

        if not self.samples:
            return

        # Find columns
        elev_col = self._find_column(self.samples, 'elevation', 'altitude', 'z', 'height')
        grav_col = self._find_column(self.samples, 'gravity', 'g_obs', 'grav')
        mag_col = self._find_column(self.samples, 'magnetic', 'mag_obs', 'total_field', 't')
        igrf_col = self._find_column(self.samples, 'igrf', 'reference_field', 'igrf_value')
        lat_col = self._find_column(self.samples, 'latitude', 'lat')
        lon_col = self._find_column(self.samples, 'longitude', 'lon', 'long')
        id_col = self._find_column(self.samples, 'station_id', 'station', 'id')

        for i, sample in enumerate(self.samples):
            station = {
                'index': i,
                'id': sample.get(id_col, f"Station {i+1}") if id_col else f"Station {i+1}",
                'elevation': None,
                'gravity': None,
                'magnetic': None,
                'igrf': None,
                'latitude': None,
                'longitude': None,
                'free_air': None,
                'bouguer': None,
                'mag_anomaly': None,
                'raw_data': sample
            }

            # Station ID
            if id_col:
                sid = sample.get(id_col)
                if sid:
                    self.station_id.append(str(sid))
                    station['id'] = str(sid)

            # Coordinates
            if lat_col:
                lat = self._tof(sample.get(lat_col))
                if lat is not None:
                    self.latitude.append(lat)
                    station['latitude'] = lat

            if lon_col:
                lon = self._tof(sample.get(lon_col))
                if lon is not None:
                    self.longitude.append(lon)
                    station['longitude'] = lon

            # Elevation
            if elev_col:
                elev = self._tof(sample.get(elev_col))
                if elev is not None:
                    self.elevation.append(elev)
                    station['elevation'] = elev

            # Gravity
            if grav_col:
                g = self._tof(sample.get(grav_col))
                if g is not None:
                    self.gravity_obs.append(g)
                    station['gravity'] = g

            # Magnetic
            if mag_col:
                m = self._tof(sample.get(mag_col))
                if m is not None:
                    self.magnetic_obs.append(m)
                    station['magnetic'] = m

            # IGRF
            if igrf_col:
                igrf_val = self._tof(sample.get(igrf_col))
                if igrf_val is not None:
                    self.igrf.append(igrf_val)
                    station['igrf'] = igrf_val

            self.station_summary.append(station)

        # Calculate anomalies
        self._calculate_anomalies()

    def _calculate_anomalies(self):
        """Calculate geophysical anomalies."""
        # Free-air correction: +0.3086 mGal/m
        for i, station in enumerate(self.station_summary):
            if station['gravity'] is not None and station['elevation'] is not None:
                fa = station['gravity'] + 0.3086 * station['elevation']
                self.free_air_anomaly.append(fa)
                station['free_air'] = fa

                # Simple Bouguer correction (assuming density 2.67 g/cm³)
                bg = fa - 0.0419 * 2.67 * station['elevation']
                self.bouguer_anomaly.append(bg)
                station['bouguer'] = bg

            # Magnetic anomaly (T_obs - IGRF)
            if station['magnetic'] is not None and station['igrf'] is not None:
                mag_anom = station['magnetic'] - station['igrf']
                self.magnetic_anomaly.append(mag_anom)
                station['mag_anomaly'] = mag_anom

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
        rows.append(("N stations", str(n)))

        if self.elevation:
            rows.append(("Elevation range", f"{min(self.elevation):.0f}-{max(self.elevation):.0f} m"))

        if self.gravity_obs:
            rows.append(("Gravity range", f"{min(self.gravity_obs):.2f}-{max(self.gravity_obs):.2f} mGal"))

        if self.magnetic_obs:
            rows.append(("Magnetic range", f"{min(self.magnetic_obs):.0f}-{max(self.magnetic_obs):.0f} nT"))

        if self.bouguer_anomaly:
            rows.append(("Bouguer range", f"{min(self.bouguer_anomaly):.2f}-{max(self.bouguer_anomaly):.2f} mGal"))

        return rows

    def _calc_validation(self, samples, columns):
        """Data validation."""
        rows = []

        if not samples:
            rows.append((WARN_ICON, "No data"))
            return rows

        # Check for critical columns
        if self.elevation:
            rows.append((OK_ICON, f"Elevation data: {len(self.elevation)} points"))
        else:
            rows.append((WARN_ICON, "No elevation data"))

        if self.gravity_obs:
            rows.append((OK_ICON, f"Gravity data: {len(self.gravity_obs)} points"))
        else:
            rows.append((INFO_ICON, "No gravity data"))

        if self.magnetic_obs:
            rows.append((OK_ICON, f"Magnetic data: {len(self.magnetic_obs)} points"))
        else:
            rows.append((INFO_ICON, "No magnetic data"))

        return rows

    def _calc_quick(self, samples, columns):
        """Quick calculations."""
        rows = []

        # Free-air anomaly stats
        if self.free_air_anomaly:
            rows.append(("Free-air mean", f"{np.mean(self.free_air_anomaly):.2f} mGal"))

        # Bouguer anomaly stats
        if self.bouguer_anomaly:
            rows.append(("Bouguer mean", f"{np.mean(self.bouguer_anomaly):.2f} mGal"))

        # Magnetic anomaly stats
        if self.magnetic_anomaly:
            rows.append(("Mag anomaly mean", f"{np.mean(self.magnetic_anomaly):.1f} nT"))

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
            text="Select rows in main table to filter stations",
            font=("Segoe UI", 9, "italic")
        )
        self.current_selection_label.pack(side=tk.LEFT)

        # Anomaly profile
        self.anomaly_profile_frame = ttk.Frame(container)
        self.anomaly_profile_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self._create_anomaly_profile(self.anomaly_profile_frame)

        # Station map
        self.station_map_frame = ttk.Frame(container)
        self.station_map_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self._create_station_map(self.station_map_frame)

        # Data table
        self._create_data_table(container)

    def _create_anomaly_profile(self, parent):
        """Create anomaly profile plot."""
        frame = ttk.LabelFrame(parent, text="Anomaly Profiles", padding=10)
        frame.pack(fill="both", expand=True)

        fig = Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)

        ax.set_xlabel("Station Index")
        ax.set_ylabel("Anomaly (mGal)")
        ax.set_title("Gravity Anomalies")
        ax.grid(True, linestyle=':', alpha=0.6)

        # Filter data based on selection
        indices = self.selected_indices if self.selected_indices else range(len(self.station_summary))

        free_air_vals = []
        bouguer_vals = []
        mag_vals = []
        x_vals = []

        for i, idx in enumerate(sorted(indices)):
            if idx >= len(self.station_summary):
                continue
            station = self.station_summary[idx]
            x_vals.append(i)
            if station['free_air'] is not None:
                free_air_vals.append((i, station['free_air']))
            if station['bouguer'] is not None:
                bouguer_vals.append((i, station['bouguer']))
            if station['mag_anomaly'] is not None:
                mag_vals.append((i, station['mag_anomaly']))

        if free_air_vals:
            x_fa, y_fa = zip(*free_air_vals)
            ax.plot(x_fa, y_fa, 'b-', linewidth=1.5, label='Free-air', alpha=0.7, marker='o')

        if bouguer_vals:
            x_bg, y_bg = zip(*bouguer_vals)
            ax.plot(x_bg, y_bg, 'r-', linewidth=1.5, label='Bouguer', alpha=0.7, marker='s')

        if mag_vals:
            ax2 = ax.twinx()
            x_mag, y_mag = zip(*mag_vals)
            ax2.plot(x_mag, y_mag, 'g-', linewidth=1.5, label='Magnetic', alpha=0.7, marker='^')
            ax2.set_ylabel('Magnetic Anomaly (nT)')

        ax.legend(loc='upper left')
        fig.tight_layout()

        if not (free_air_vals or bouguer_vals or mag_vals):
            ax.text(0.5, 0.5, "No anomaly data", ha='center', va='center',
                   transform=ax.transAxes, fontsize=12)

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.figures.append(fig)

    def _create_station_map(self, parent):
        """Create simple station map."""
        frame = ttk.LabelFrame(parent, text="Station Map", padding=10)
        frame.pack(fill="both", expand=True)

        fig = Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)

        # Filter data based on selection
        lats = []
        lons = []
        bouguer_vals = []
        station_ids = []

        indices = self.selected_indices if self.selected_indices else range(len(self.station_summary))

        for idx in indices:
            if idx >= len(self.station_summary):
                continue
            station = self.station_summary[idx]
            if station['latitude'] is not None and station['longitude'] is not None:
                lats.append(station['latitude'])
                lons.append(station['longitude'])
                bouguer_vals.append(station['bouguer'] if station['bouguer'] is not None else 0)
                station_ids.append(station['id'])

        if lats and lons:
            if bouguer_vals and any(v != 0 for v in bouguer_vals):
                scatter = ax.scatter(lons, lats, c=bouguer_vals, s=50, cmap='viridis', edgecolors='black')
                plt.colorbar(scatter, ax=ax, label='Bouguer Anomaly (mGal)')
            else:
                ax.scatter(lons, lats, c='blue', s=50, edgecolors='black', alpha=0.7)

            ax.set_xlabel("Longitude")
            ax.set_ylabel("Latitude")
            ax.set_title("Station Locations")
            ax.grid(True, linestyle=':', alpha=0.6)

            # Add station labels for first 10
            for i, (lon, lat, sid) in enumerate(zip(lons[:10], lats[:10], station_ids[:10])):
                ax.annotate(sid, (lon, lat), xytext=(5, 5), textcoords='offset points', fontsize=8)
        else:
            ax.text(0.5, 0.5, "No coordinate data", ha='center', va='center',
                   transform=ax.transAxes, fontsize=12)

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.figures.append(fig)

    def _create_data_table(self, parent):
        """Create table of station data."""
        frame = ttk.LabelFrame(parent, text="Station Data", padding=10)
        frame.pack(fill="x", padx=5, pady=5)

        cols = ["Station", "Elevation", "Gravity", "Free-air", "Bouguer"]
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=6)

        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=90, anchor="center")

        # Filter data based on selection
        indices = self.selected_indices if self.selected_indices else range(len(self.station_summary))

        for i in sorted(indices)[:20]:  # Limit to 20 rows
            if i >= len(self.station_summary):
                continue

            station = self.station_summary[i]

            sid = station['id'][:10]
            elev = f"{station['elevation']:.0f}" if station['elevation'] is not None else "-"
            grav = f"{station['gravity']:.2f}" if station['gravity'] is not None else "-"
            fa = f"{station['free_air']:.2f}" if station['free_air'] is not None else "-"
            bg = f"{station['bouguer']:.2f}" if station['bouguer'] is not None else "-"

            tree.insert("", "end", values=(sid, elev, grav, fa, bg))

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
            if idx < len(self.station_summary):
                hub_idx = self.station_summary[idx]['index']
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
