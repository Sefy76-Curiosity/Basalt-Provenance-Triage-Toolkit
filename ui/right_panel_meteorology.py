"""
Meteorology / Environmental Right Panel
==========================================
Features:
  - Dynamic updates when rows are selected in main table
  - Scrollable interface for all content
  - Shows time series and climate summaries
"""

import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from datetime import datetime

from .right_panel import FieldPanelBase, OK_ICON, WARN_ICON, ERROR_ICON, INFO_ICON


class MeteorologyPanel(FieldPanelBase):
    PANEL_ID = "meteorology"
    PANEL_NAME = "Meteorology"
    PANEL_ICON = "🌦️"
    DETECT_COLUMNS = ['temperature', 'temp', 'precipitation', 'rainfall',
                      'humidity', 'wind_speed', 'pressure', 'solar', 'dewpoint']
    is_right_panel = True

    def __init__(self, parent, app):
        super().__init__(parent, app)

        # Initialize data storage
        self.temp = []
        self.precip = []
        self.humidity = []
        self.wind_speed = []
        self.wind_dir = []
        self.pressure = []
        self.solar = []
        self.dates = []
        self.samples = []
        self.record_summary = []

        # Selection tracking
        self.selected_indices = set()

        # UI elements
        self.current_selection_label = None
        self.time_series_frame = None
        self.climate_summary_frame = None
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
        self._redraw_time_series()
        self._redraw_climate_summary()

    def _set_info_label(self):
        """Update selection info label."""
        if not hasattr(self, 'current_selection_label') or not self.current_selection_label:
            return

        if not self.selected_indices:
            text = "Showing: ALL records"
            color = "black"
        elif len(self.selected_indices) == 1:
            idx = next(iter(self.selected_indices))
            if idx < len(self.record_summary):
                text = f"Showing: Record {idx+1}"
                color = "blue"
            else:
                text = "Showing: Selected record"
                color = "blue"
        else:
            text = f"Showing: {len(self.selected_indices)} selected records"
            color = "green"

        try:
            self.current_selection_label.config(text=text, foreground=color)
        except:
            pass

    def _redraw_time_series(self):
        """Redraw time series plot with current selection."""
        if not hasattr(self, 'time_series_frame') or not self.time_series_frame:
            return
        try:
            for widget in self.time_series_frame.winfo_children():
                widget.destroy()
            self._create_time_series(self.time_series_frame)
        except:
            pass

    def _redraw_climate_summary(self):
        """Redraw climate summary with current selection."""
        if not hasattr(self, 'climate_summary_frame') or not self.climate_summary_frame:
            return
        try:
            for widget in self.climate_summary_frame.winfo_children():
                widget.destroy()
            self._create_climate_summary(self.climate_summary_frame)
        except:
            pass

    # ------------------------------------------------------------------
    # Data extraction
    # ------------------------------------------------------------------
    def _extract_data(self):
        """Extract meteorological data from samples."""
        self.temp = []
        self.precip = []
        self.humidity = []
        self.wind_speed = []
        self.wind_dir = []
        self.pressure = []
        self.solar = []
        self.dates = []
        self.record_summary = []

        if not self.samples:
            return

        # Find columns
        temp_col = self._find_column(self.samples, 'temperature', 'temp', 't', 't_mean')
        precip_col = self._find_column(self.samples, 'precipitation', 'rainfall', 'rain', 'precip')
        humid_col = self._find_column(self.samples, 'humidity', 'rh', 'relative_humidity')
        wind_speed_col = self._find_column(self.samples, 'wind_speed', 'ws', 'wind')
        wind_dir_col = self._find_column(self.samples, 'wind_direction', 'wd', 'wind_dir')
        pressure_col = self._find_column(self.samples, 'pressure', 'pres', 'air_pressure')
        solar_col = self._find_column(self.samples, 'solar', 'radiation', 'solar_radiation')
        date_col = self._find_column(self.samples, 'date', 'datetime', 'time', 'timestamp')

        for i, sample in enumerate(self.samples):
            record = {
                'index': i,
                'id': sample.get('Sample_ID', f"Record {i+1}"),
                'temp': None,
                'precip': None,
                'humidity': None,
                'wind_speed': None,
                'wind_dir': None,
                'pressure': None,
                'solar': None,
                'date': None,
                'raw_data': sample
            }

            # Temperature
            if temp_col:
                t = self._tof(sample.get(temp_col))
                if t is not None:
                    self.temp.append(t)
                    record['temp'] = t

            # Precipitation
            if precip_col:
                p = self._tof(sample.get(precip_col))
                if p is not None:
                    self.precip.append(p)
                    record['precip'] = p

            # Humidity
            if humid_col:
                h = self._tof(sample.get(humid_col))
                if h is not None:
                    self.humidity.append(h)
                    record['humidity'] = h

            # Wind
            if wind_speed_col:
                ws = self._tof(sample.get(wind_speed_col))
                if ws is not None:
                    self.wind_speed.append(ws)
                    record['wind_speed'] = ws

            if wind_dir_col:
                wd = self._tof(sample.get(wind_dir_col))
                if wd is not None:
                    self.wind_dir.append(wd)
                    record['wind_dir'] = wd

            # Pressure
            if pressure_col:
                pres = self._tof(sample.get(pressure_col))
                if pres is not None:
                    self.pressure.append(pres)
                    record['pressure'] = pres

            # Solar radiation
            if solar_col:
                sol = self._tof(sample.get(solar_col))
                if sol is not None:
                    self.solar.append(sol)
                    record['solar'] = sol

            # Date
            if date_col:
                date_val = sample.get(date_col)
                if date_val:
                    try:
                        if isinstance(date_val, str):
                            for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%d-%m-%Y', '%Y%m%d']:
                                try:
                                    dt = datetime.strptime(date_val, fmt)
                                    self.dates.append(dt)
                                    record['date'] = dt
                                    break
                                except:
                                    pass
                    except:
                        pass

            self.record_summary.append(record)

    def _calculate_degree_days(self, base_temp=18.0):
        """Calculate heating and cooling degree days."""
        temps = [r['temp'] for r in self.record_summary if r['temp'] is not None]
        if not temps:
            return 0, 0

        hdd = sum(max(0, base_temp - t) for t in temps)
        cdd = sum(max(0, t - base_temp) for t in temps)

        return hdd, cdd

    def _count_extremes(self):
        """Count extreme weather events."""
        extremes = {
            'heat_wave': 0,
            'cold_snap': 0,
            'heavy_rain': 0,
            'strong_wind': 0
        }

        for r in self.record_summary:
            if r['temp'] is not None and r['temp'] > 35:
                extremes['heat_wave'] += 1
            if r['temp'] is not None and r['temp'] < 0:
                extremes['cold_snap'] += 1
            if r['precip'] is not None and r['precip'] > 25:
                extremes['heavy_rain'] += 1
            if r['wind_speed'] is not None and r['wind_speed'] > 20:
                extremes['strong_wind'] += 1

        return extremes

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
        rows.append(("N records", str(n)))

        if self.temp:
            rows.append(("Temp range", f"{min(self.temp):.1f}°C - {max(self.temp):.1f}°C"))
            rows.append(("Mean temp", f"{np.mean(self.temp):.1f}°C"))

        if self.precip:
            total_rain = sum(self.precip)
            rows.append(("Total precip", f"{total_rain:.1f} mm"))
            rows.append(("Max daily", f"{max(self.precip):.1f} mm"))

        if self.humidity:
            rows.append(("Mean humidity", f"{np.mean(self.humidity):.0f}%"))

        return rows

    def _calc_validation(self, samples, columns):
        """Data validation."""
        rows = []

        if not samples:
            rows.append((WARN_ICON, "No data"))
            return rows

        # Check for temperature column
        temp_col = self._find_column(samples, 'temperature', 'temp')
        if temp_col:
            rows.append((OK_ICON, f"Temp column: {temp_col}"))

            # Check for plausible temperatures
            if self.temp:
                implausible = sum(1 for t in self.temp if t < -50 or t > 60)
                if implausible == 0:
                    rows.append((OK_ICON, "Temperatures plausible"))
                else:
                    rows.append((WARN_ICON, f"{implausible} implausible temps"))
        else:
            rows.append((WARN_ICON, "No temperature data"))

        # Check data completeness
        missing = 0
        for s in samples:
            if temp_col and s.get(temp_col) is None:
                missing += 1

        if missing == 0:
            rows.append((OK_ICON, "Complete data"))
        else:
            pct_missing = (missing / len(samples)) * 100
            rows.append((WARN_ICON, f"{pct_missing:.1f}% missing"))

        return rows

    def _calc_quick(self, samples, columns):
        """Quick calculations."""
        rows = []

        if self.temp:
            rows.append(("Max temp", f"{max(self.temp):.1f}°C"))
            rows.append(("Min temp", f"{min(self.temp):.1f}°C"))
            rows.append(("Mean temp", f"{np.mean(self.temp):.1f}°C"))

            # Degree days
            hdd, cdd = self._calculate_degree_days()
            rows.append(("HDD (18°C)", f"{hdd:.0f}"))
            rows.append(("CDD (18°C)", f"{cdd:.0f}"))

        # Extremes
        extremes = self._count_extremes()
        if extremes['heat_wave'] > 0:
            rows.append(("Hot days >35°C", str(extremes['heat_wave'])))
        if extremes['cold_snap'] > 0:
            rows.append(("Cold days <0°C", str(extremes['cold_snap'])))
        if extremes['heavy_rain'] > 0:
            rows.append(("Heavy rain days", str(extremes['heavy_rain'])))
        if extremes['strong_wind'] > 0:
            rows.append(("Strong wind days", str(extremes['strong_wind'])))

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
            text="Select rows in main table to filter records",
            font=("Segoe UI", 9, "italic")
        )
        self.current_selection_label.pack(side=tk.LEFT)

        # Time series
        self.time_series_frame = ttk.Frame(container)
        self.time_series_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self._create_time_series(self.time_series_frame)

        # Climate summary
        self.climate_summary_frame = ttk.Frame(container)
        self.climate_summary_frame.pack(fill="x", padx=5, pady=5)
        self._create_climate_summary(self.climate_summary_frame)

        # Data table
        self._create_data_table(container)

    def _create_time_series(self, parent):
        """Create time series plot."""
        frame = ttk.LabelFrame(parent, text="Time Series", padding=10)
        frame.pack(fill="both", expand=True)

        fig = Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)

        ax.set_xlabel("Date")
        ax.set_ylabel("Value")
        ax.set_title("Environmental Time Series")
        ax.grid(True, linestyle=':', alpha=0.6)

        has_data = False

        # Filter data based on selection
        indices = self.selected_indices if self.selected_indices else range(len(self.record_summary))

        temps = []
        precip_vals = []
        dates = []
        x_pos = []

        for i, idx in enumerate(sorted(indices)):
            if idx >= len(self.record_summary):
                continue
            record = self.record_summary[idx]
            if record['date'] is not None:
                dates.append(record['date'])
            else:
                dates.append(i)
            x_pos.append(i)
            if record['temp'] is not None:
                temps.append((i, record['temp']))
            if record['precip'] is not None:
                precip_vals.append((i, record['precip']))

        # Plot temperature
        if temps:
            x_t, y_t = zip(*temps)
            ax.plot(x_t, y_t, 'r-', linewidth=1.5, label='Temperature', alpha=0.7, marker='o')
            has_data = True

        # Plot precipitation on secondary axis if needed
        if precip_vals:
            ax2 = ax.twinx()
            x_p, y_p = zip(*precip_vals)
            ax2.bar(x_p, y_p, alpha=0.3, color='blue', label='Precipitation', width=0.8)
            ax2.set_ylabel('Precipitation (mm)')
            has_data = True

        if not has_data:
            ax.text(0.5, 0.5, "No time series data", ha='center', va='center',
                   transform=ax.transAxes, fontsize=12)

        ax.legend(loc='upper left')
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.figures.append(fig)

    def _create_climate_summary(self, parent):
        """Create climate summary statistics."""
        frame = ttk.LabelFrame(parent, text="Climate Summary", padding=10)
        frame.pack(fill="x")

        # Filter data based on selection
        temps = []
        precip_vals = []
        humidity_vals = []
        pressure_vals = []

        indices = self.selected_indices if self.selected_indices else range(len(self.record_summary))

        for idx in indices:
            if idx >= len(self.record_summary):
                continue
            record = self.record_summary[idx]
            if record['temp'] is not None:
                temps.append(record['temp'])
            if record['precip'] is not None:
                precip_vals.append(record['precip'])
            if record['humidity'] is not None:
                humidity_vals.append(record['humidity'])
            if record['pressure'] is not None:
                pressure_vals.append(record['pressure'])

        # Create two columns
        left_col = ttk.Frame(frame)
        left_col.pack(side=tk.LEFT, fill="both", expand=True, padx=5)

        right_col = ttk.Frame(frame)
        right_col.pack(side=tk.RIGHT, fill="both", expand=True, padx=5)

        # Temperature statistics
        if temps:
            ttk.Label(left_col, text="Temperature (°C):",
                     font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=2)
            ttk.Label(left_col, text=f"Mean: {np.mean(temps):.1f}").pack(anchor="w")
            ttk.Label(left_col, text=f"Max: {max(temps):.1f}").pack(anchor="w")
            ttk.Label(left_col, text=f"Min: {min(temps):.1f}").pack(anchor="w")
            ttk.Label(left_col, text=f"Std: {np.std(temps):.1f}").pack(anchor="w")

        # Precipitation statistics
        if precip_vals:
            ttk.Label(right_col, text="Precipitation (mm):",
                     font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=2)
            ttk.Label(right_col, text=f"Total: {sum(precip_vals):.1f}").pack(anchor="w")
            ttk.Label(right_col, text=f"Max daily: {max(precip_vals):.1f}").pack(anchor="w")
            rainy = sum(1 for p in precip_vals if p > 0.1)
            ttk.Label(right_col, text=f"Rainy days: {rainy}").pack(anchor="w")

        # Humidity
        if humidity_vals:
            ttk.Label(left_col, text="\nHumidity (%):",
                     font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=2)
            ttk.Label(left_col, text=f"Mean: {np.mean(humidity_vals):.0f}").pack(anchor="w")

        # Pressure
        if pressure_vals:
            ttk.Label(right_col, text="\nPressure (hPa):",
                     font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=2)
            ttk.Label(right_col, text=f"Mean: {np.mean(pressure_vals):.1f}").pack(anchor="w")

    def _create_data_table(self, parent):
        """Create table of meteorological data."""
        frame = ttk.LabelFrame(parent, text="Data Records", padding=10)
        frame.pack(fill="x", padx=5, pady=5)

        cols = ["ID", "Temp (°C)", "Precip (mm)", "Humidity (%)", "Pressure (hPa)"]
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=6)

        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=90, anchor="center")

        # Filter data based on selection
        indices = self.selected_indices if self.selected_indices else range(len(self.record_summary))

        for i in sorted(indices)[:20]:  # Limit to 20 rows
            if i >= len(self.record_summary):
                continue

            record = self.record_summary[i]

            rid = record['id'][:8]
            temp = f"{record['temp']:.1f}" if record['temp'] is not None else "-"
            precip = f"{record['precip']:.1f}" if record['precip'] is not None else "-"
            hum = f"{record['humidity']:.0f}" if record['humidity'] is not None else "-"
            pres = f"{record['pressure']:.1f}" if record['pressure'] is not None else "-"

            tree.insert("", "end", values=(rid, temp, precip, hum, pres))

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
            if idx < len(self.record_summary):
                hub_idx = self.record_summary[idx]['index']
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
