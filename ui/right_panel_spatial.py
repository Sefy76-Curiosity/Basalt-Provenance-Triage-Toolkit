"""
Spatial / GIS Right Panel
===========================
Features:
  - Dynamic updates when rows are selected in main table
  - Scrollable interface for all content
  - Shows location maps and spatial metrics
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


class SpatialPanel(FieldPanelBase):
    PANEL_ID = "spatial"
    PANEL_NAME = "Spatial / GIS"
    PANEL_ICON = "🗺️"
    DETECT_COLUMNS = ['latitude', 'longitude', 'lat', 'lon', 'long',
                      'easting', 'northing', 'x_coord', 'y_coord', 'utm']
    is_right_panel = True

    def __init__(self, parent, app):
        super().__init__(parent, app)

        # Initialize data storage
        self.latitude = []
        self.longitude = []
        self.easting = []
        self.northing = []
        self.utm_zone = []
        self.sample_id = []
        self.samples = []
        self.point_summary = []

        # Derived values
        self.centroid = None
        self.bounding_box = None
        self.bounding_box_area = None
        self.mean_nn_distance = None

        # Selection tracking
        self.selected_indices = set()

        # UI elements
        self.current_selection_label = None
        self.map_frame = None
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
        self._redraw_location_map()
        self._update_spatial_metrics()

    def _set_info_label(self):
        """Update selection info label."""
        if not hasattr(self, 'current_selection_label') or not self.current_selection_label:
            return

        if not self.selected_indices:
            text = "Showing: ALL points"
            color = "black"
        elif len(self.selected_indices) == 1:
            idx = next(iter(self.selected_indices))
            if idx < len(self.point_summary):
                text = f"Showing: Point {self.point_summary[idx].get('id', idx+1)}"
                color = "blue"
            else:
                text = "Showing: Selected point"
                color = "blue"
        else:
            text = f"Showing: {len(self.selected_indices)} selected points"
            color = "green"

        try:
            self.current_selection_label.config(text=text, foreground=color)
        except:
            pass

    def _redraw_location_map(self):
        """Redraw location map with current selection."""
        if not hasattr(self, 'map_frame') or not self.map_frame:
            return
        try:
            for widget in self.map_frame.winfo_children():
                widget.destroy()
            self._create_location_map(self.map_frame)
        except:
            pass

    def _update_spatial_metrics(self):
        """Update spatial metrics display."""
        if hasattr(self, 'metrics_frame'):
            try:
                for widget in self.metrics_frame.winfo_children():
                    widget.destroy()
                self._create_spatial_metrics(self.metrics_frame)
            except:
                pass

    # ------------------------------------------------------------------
    # Data extraction
    # ------------------------------------------------------------------
    def _extract_data(self):
        """Extract spatial data from samples."""
        self.latitude = []
        self.longitude = []
        self.easting = []
        self.northing = []
        self.utm_zone = []
        self.sample_id = []
        self.point_summary = []

        if not self.samples:
            return

        # Find columns
        lat_col = self._find_column(self.samples, 'latitude', 'lat')
        lon_col = self._find_column(self.samples, 'longitude', 'lon', 'long')
        east_col = self._find_column(self.samples, 'easting', 'x', 'x_coord')
        north_col = self._find_column(self.samples, 'northing', 'y', 'y_coord')
        utm_col = self._find_column(self.samples, 'utm_zone', 'zone', 'utm')
        id_col = self._find_column(self.samples, 'sample_id', 'id', 'point_id')

        for i, sample in enumerate(self.samples):
            point = {
                'index': i,
                'id': sample.get(id_col, f"Point {i+1}") if id_col else f"Point {i+1}",
                'latitude': None,
                'longitude': None,
                'easting': None,
                'northing': None,
                'utm_zone': None,
                'raw_data': sample
            }

            # Sample ID
            if id_col:
                sid = sample.get(id_col)
                if sid:
                    self.sample_id.append(str(sid))
                    point['id'] = str(sid)

            # Geographic coordinates
            if lat_col:
                lat = self._tof(sample.get(lat_col))
                if lat is not None:
                    self.latitude.append(lat)
                    point['latitude'] = lat

            if lon_col:
                lon = self._tof(sample.get(lon_col))
                if lon is not None:
                    self.longitude.append(lon)
                    point['longitude'] = lon

            # Projected coordinates
            if east_col:
                east = self._tof(sample.get(east_col))
                if east is not None:
                    self.easting.append(east)
                    point['easting'] = east

            if north_col:
                north = self._tof(sample.get(north_col))
                if north is not None:
                    self.northing.append(north)
                    point['northing'] = north

            # UTM zone
            if utm_col:
                zone = sample.get(utm_col)
                if zone:
                    self.utm_zone.append(str(zone))
                    point['utm_zone'] = str(zone)

            self.point_summary.append(point)

        # Calculate derived values
        self._calculate_spatial_metrics()

    def _haversine(self, lat1, lon1, lat2, lon2):
        """Calculate great-circle distance between two points in km."""
        R = 6371.0  # Earth's radius in km

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = (math.sin(dlat/2)**2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        return R * c

    def _calculate_spatial_metrics(self):
        """Calculate spatial metrics based on selection."""
        self.centroid = None
        self.bounding_box = None
        self.bounding_box_area = None
        self.mean_nn_distance = None

        # Get coordinates based on selection
        lats = []
        lons = []

        indices = self.selected_indices if self.selected_indices else range(len(self.point_summary))

        for idx in indices:
            if idx >= len(self.point_summary):
                continue
            point = self.point_summary[idx]
            if point['latitude'] is not None and point['longitude'] is not None:
                lats.append(point['latitude'])
                lons.append(point['longitude'])

        if len(lats) < 2:
            return

        # Centroid
        self.centroid = (np.mean(lats), np.mean(lons))

        # Bounding box
        self.bounding_box = {
            'min_lat': min(lats),
            'max_lat': max(lats),
            'min_lon': min(lons),
            'max_lon': max(lons)
        }

        # Approximate bounding box area (km²)
        lat_center = (self.bounding_box['min_lat'] + self.bounding_box['max_lat']) / 2

        width = self._haversine(lat_center, self.bounding_box['min_lon'],
                               lat_center, self.bounding_box['max_lon'])
        height = self._haversine(self.bounding_box['min_lat'], self.bounding_box['min_lon'],
                                self.bounding_box['max_lat'], self.bounding_box['min_lon'])

        self.bounding_box_area = width * height

        # Mean nearest neighbour distance
        nn_distances = []
        for i in range(len(lats)):
            min_dist = float('inf')
            for j in range(len(lats)):
                if i == j:
                    continue
                dist = self._haversine(lats[i], lons[i], lats[j], lons[j])
                if dist < min_dist:
                    min_dist = dist
            if min_dist != float('inf'):
                nn_distances.append(min_dist)

        if nn_distances:
            self.mean_nn_distance = np.mean(nn_distances)

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
        rows.append(("N points", str(n)))

        if self.latitude and self.longitude:
            rows.append(("Lat range", f"{min(self.latitude):.4f} - {max(self.latitude):.4f}"))
            rows.append(("Lon range", f"{min(self.longitude):.4f} - {max(self.longitude):.4f}"))

        if self.centroid:
            rows.append(("Centroid", f"({self.centroid[0]:.4f}, {self.centroid[1]:.4f})"))

        if self.bounding_box_area:
            rows.append(("BBox area", f"{self.bounding_box_area:.1f} km²"))

        return rows

    def _calc_validation(self, samples, columns):
        """Data validation."""
        rows = []

        if not samples:
            rows.append((WARN_ICON, "No data"))
            return rows

        # Check for coordinate columns
        lat_col = self._find_column(samples, 'latitude', 'lat')
        lon_col = self._find_column(samples, 'longitude', 'lon', 'long')

        if lat_col:
            rows.append((OK_ICON, f"Latitude: {lat_col}"))
        else:
            rows.append((ERROR_ICON, "No latitude column"))

        if lon_col:
            rows.append((OK_ICON, f"Longitude: {lon_col}"))
        else:
            rows.append((ERROR_ICON, "No longitude column"))

        # Validate coordinate ranges
        if self.latitude:
            bad_lat = sum(1 for lat in self.latitude if not (-90 <= lat <= 90))
            if bad_lat == 0:
                rows.append((OK_ICON, "All latitudes valid"))
            else:
                rows.append((ERROR_ICON, f"{bad_lat} latitudes out of range"))

        if self.longitude:
            bad_lon = sum(1 for lon in self.longitude if not (-180 <= lon <= 180))
            if bad_lon == 0:
                rows.append((OK_ICON, "All longitudes valid"))
            else:
                rows.append((ERROR_ICON, f"{bad_lon} longitudes out of range"))

        return rows

    def _calc_quick(self, samples, columns):
        """Quick calculations."""
        rows = []

        if self.mean_nn_distance:
            rows.append(("Mean NN dist", f"{self.mean_nn_distance:.2f} km"))

        if self.bounding_box_area:
            rows.append(("BBox area", f"{self.bounding_box_area:.1f} km²"))

        # Point density
        if self.bounding_box_area and self.bounding_box_area > 0:
            n_points = len(self.selected_indices) if self.selected_indices else len(self.latitude)
            density = n_points / self.bounding_box_area
            rows.append(("Point density", f"{density:.2f} pts/km²"))

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
            text="Select rows in main table to filter points",
            font=("Segoe UI", 9, "italic")
        )
        self.current_selection_label.pack(side=tk.LEFT)

        # Location map
        self.map_frame = ttk.Frame(container)
        self.map_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self._create_location_map(self.map_frame)

        # Spatial metrics
        self.metrics_frame = ttk.Frame(container)
        self.metrics_frame.pack(fill="x", padx=5, pady=5)
        self._create_spatial_metrics(self.metrics_frame)

        # Data table
        self._create_coordinate_table(container)

    def _create_location_map(self, parent):
        """Create simple location map."""
        frame = ttk.LabelFrame(parent, text="Location Map", padding=10)
        frame.pack(fill="both", expand=True)

        fig = Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)

        # Get coordinates based on selection
        lats = []
        lons = []

        indices = self.selected_indices if self.selected_indices else range(len(self.point_summary))

        for idx in indices:
            if idx >= len(self.point_summary):
                continue
            point = self.point_summary[idx]
            if point['latitude'] is not None and point['longitude'] is not None:
                lats.append(point['latitude'])
                lons.append(point['longitude'])

        if lats and lons:
            if self.selected_indices:
                ax.scatter(lons, lats, c='red', s=50, alpha=0.7, edgecolors='black', label='Selected')
            else:
                ax.scatter(lons, lats, c='blue', s=50, alpha=0.7, edgecolors='black', label='All')

            ax.set_xlabel("Longitude")
            ax.set_ylabel("Latitude")
            ax.set_title(f"Sample Locations (n={len(lats)})")
            ax.grid(True, linestyle=':', alpha=0.6)

            # Add bounding box
            if self.bounding_box and not self.selected_indices:
                x_box = [self.bounding_box['min_lon'], self.bounding_box['max_lon'],
                        self.bounding_box['max_lon'], self.bounding_box['min_lon'],
                        self.bounding_box['min_lon']]
                y_box = [self.bounding_box['min_lat'], self.bounding_box['min_lat'],
                        self.bounding_box['max_lat'], self.bounding_box['max_lat'],
                        self.bounding_box['min_lat']]
                ax.plot(x_box, y_box, 'g--', linewidth=1, alpha=0.7, label='Bounding box')

            # Add centroid
            if self.centroid and not self.selected_indices:
                ax.plot(self.centroid[1], self.centroid[0], 'r*', markersize=15,
                       label='Centroid')

            ax.legend()
        else:
            ax.text(0.5, 0.5, "No coordinate data", ha='center', va='center',
                   transform=ax.transAxes, fontsize=12)

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.figures.append(fig)

    def _create_spatial_metrics(self, parent):
        """Create spatial metrics display."""
        frame = ttk.LabelFrame(parent, text="Spatial Metrics", padding=10)
        frame.pack(fill="x")

        metrics_frame = ttk.Frame(frame)
        metrics_frame.pack(fill="x")

        if self.centroid:
            row1 = ttk.Frame(metrics_frame)
            row1.pack(fill="x", pady=2)
            ttk.Label(row1, text="Centroid:", font=("Segoe UI", 9, "bold"),
                     width=15, anchor="w").pack(side=tk.LEFT)
            ttk.Label(row1, text=f"({self.centroid[0]:.4f}, {self.centroid[1]:.4f})").pack(side=tk.LEFT)

        if self.bounding_box_area:
            row2 = ttk.Frame(metrics_frame)
            row2.pack(fill="x", pady=2)
            ttk.Label(row2, text="BBox area:", font=("Segoe UI", 9, "bold"),
                     width=15, anchor="w").pack(side=tk.LEFT)
            ttk.Label(row2, text=f"{self.bounding_box_area:.1f} km²").pack(side=tk.LEFT)

        if self.mean_nn_distance:
            row3 = ttk.Frame(metrics_frame)
            row3.pack(fill="x", pady=2)
            ttk.Label(row3, text="Mean NN dist:", font=("Segoe UI", 9, "bold"),
                     width=15, anchor="w").pack(side=tk.LEFT)
            ttk.Label(row3, text=f"{self.mean_nn_distance:.2f} km").pack(side=tk.LEFT)

        if self.bounding_box:
            row4 = ttk.Frame(metrics_frame)
            row4.pack(fill="x", pady=2)
            ttk.Label(row4, text="Lat range:", font=("Segoe UI", 9, "bold"),
                     width=15, anchor="w").pack(side=tk.LEFT)
            ttk.Label(row4, text=f"{self.bounding_box['min_lat']:.4f} - {self.bounding_box['max_lat']:.4f}").pack(side=tk.LEFT)

            row5 = ttk.Frame(metrics_frame)
            row5.pack(fill="x", pady=2)
            ttk.Label(row5, text="Lon range:", font=("Segoe UI", 9, "bold"),
                     width=15, anchor="w").pack(side=tk.LEFT)
            ttk.Label(row5, text=f"{self.bounding_box['min_lon']:.4f} - {self.bounding_box['max_lon']:.4f}").pack(side=tk.LEFT)

    def _create_coordinate_table(self, parent):
        """Create table of coordinates."""
        frame = ttk.LabelFrame(parent, text="Coordinate List", padding=10)
        frame.pack(fill="x", padx=5, pady=5)

        cols = ["ID", "Latitude", "Longitude"]
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=6)

        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor="center")

        # Filter data based on selection
        indices = self.selected_indices if self.selected_indices else range(len(self.point_summary))

        for i in sorted(indices)[:20]:  # Limit to 20 rows
            if i >= len(self.point_summary):
                continue

            point = self.point_summary[i]

            pid = point['id'][:10]
            lat = f"{point['latitude']:.6f}" if point['latitude'] is not None else "-"
            lon = f"{point['longitude']:.6f}" if point['longitude'] is not None else "-"

            tree.insert("", "end", values=(pid, lat, lon))

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
            if idx < len(self.point_summary):
                hub_idx = self.point_summary[idx]['index']
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
