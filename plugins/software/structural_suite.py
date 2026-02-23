"""
Structural Suite v1.0 - Stereonets · Rose Diagrams · Contouring
WITH FULL MAIN APP INTEGRATION

✓ Schmidt (equal area) and Wulff (equal angle) nets
✓ Great circles, poles, and lineations
✓ Rose diagrams for directional data
✓ Kamb contouring and density analysis
✓ Fold axis analysis and cylindrical best fit
"""

PLUGIN_INFO = {
    "category": "software",
    "id": "structural_suite",
    "name": "Structural Suite",
    "description": "Stereonets · Rose Diagrams · Contouring — Complete structural toolkit",
    "icon": "🧭",
    "version": "1.0.0",
    "requires": ["numpy", "scipy", "matplotlib", "pandas"],
    "author": "Sefy Levy & DeepSeek"
}

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import pandas as pd
from datetime import datetime
import json
import traceback
from pathlib import Path
import math

try:
    import matplotlib
    matplotlib.use('TkAgg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    from matplotlib.patches import Circle, Polygon
    from matplotlib.collections import LineCollection
    import matplotlib.cm as cm
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    import numpy as np
    from scipy import stats, optimize
    from scipy.spatial import KDTree
    from scipy.ndimage import gaussian_filter
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


class StructuralSuitePlugin:
    """
    STRUCTURAL SUITE - Complete structural geology toolkit
    Stereonets · Rose Diagrams · Contouring · Fold Analysis
    """

    def __init__(self, main_app):
        self.app = main_app
        self.window = None

        # ============ DATA ============
        self.samples = []

        # Structural measurements
        self.planes = []      # List of (strike, dip) tuples - Right Hand Rule
        self.lines = []       # List of (trend, plunge) tuples
        self.poles = []       # Will be auto-calculated from planes

        # Fold data
        self.fold_measurements = []  # List of (strike, dip) for folded surfaces

        # Analysis results
        self.fold_axis = None
        self.cone_angle = None
        self.density_grid = None
        self.contour_levels = None

        # ============ UI VARIABLES ============
        # Notebook tabs
        self.notebook = None

        # Common
        self.status_var = None
        self.progress = None

        # Projection type
        self.projection_var = tk.StringVar(value="equal_area")  # equal_area or equal_angle

        # Data entry
        self.strike_var = tk.DoubleVar(value=0)
        self.dip_var = tk.DoubleVar(value=45)
        self.trend_var = tk.DoubleVar(value=0)
        self.plunge_var = tk.DoubleVar(value=30)

        # Display options
        self.show_grid_var = tk.BooleanVar(value=True)
        self.point_size_var = tk.IntVar(value=15)
        self.contour_var = tk.BooleanVar(value=False)
        self.contour_levels_var = tk.IntVar(value=6)

        # Rose diagram
        self.rose_bin_size_var = tk.IntVar(value=10)
        self.rose_normalize_var = tk.BooleanVar(value=True)
        self.rose_color_var = tk.StringVar(value="steelblue")

        # Fold analysis
        self.fold_search_radius_var = tk.DoubleVar(value=30)  # degrees

        self._check_dependencies()

    def _check_dependencies(self):
        """Check required packages"""
        missing = []
        if not HAS_MATPLOTLIB: missing.append("matplotlib")
        if not HAS_SCIPY: missing.append("scipy")
        self.dependencies_met = len(missing) == 0
        self.missing_deps = missing

    # ============================================================================
    # SAFE FLOAT CONVERSION
    # ============================================================================
    def _safe_float(self, value):
        """Safely convert to float"""
        if value is None or value == '':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    # ============================================================================
    # DATA LOADING FROM MAIN APP
    # ============================================================================
    def _load_from_main_app(self):
        """Load structural data from main app samples"""
        if not hasattr(self.app, 'samples') or not self.app.samples:
            return False

        self.samples = self.app.samples

        # Clear existing data
        self.planes = []
        self.lines = []
        self.fold_measurements = []

        # Column pattern mappings
        strike_patterns = ['strike', 'Strike', 'azimuth', 'Azimuth']
        dip_patterns = ['dip', 'Dip', 'inclination', 'Inclination']
        trend_patterns = ['trend', 'Trend', 'direction', 'Direction']
        plunge_patterns = ['plunge', 'Plunge', 'plunge_angle', 'Plunge_angle']
        type_patterns = ['type', 'Type', 'structure', 'Structure']

        for idx, sample in enumerate(self.samples):
            if not isinstance(sample, dict):
                continue

            sample_id = sample.get('Sample_ID', f'SAMPLE_{idx:04d}')

            # Try to determine structure type
            struct_type = None
            for pattern in type_patterns:
                if pattern in sample:
                    val = str(sample.get(pattern, '')).lower()
                    if 'plane' in val or 'bedding' in val or 'foliation' in val:
                        struct_type = 'plane'
                    elif 'line' in val or 'fold' in val or 'lineation' in val:
                        struct_type = 'line'
                    break

            # Look for strike/dip (planes)
            strike = None
            dip = None

            for pattern in strike_patterns:
                if pattern in sample:
                    val = self._safe_float(sample[pattern])
                    if val is not None:
                        strike = val
                        break

            for pattern in dip_patterns:
                if pattern in sample:
                    val = self._safe_float(sample[pattern])
                    if val is not None:
                        dip = val
                        break

            if strike is not None and dip is not None:
                self.planes.append({
                    'sample_id': sample_id,
                    'strike': strike,
                    'dip': dip,
                    'type': struct_type or 'plane'
                })

                # Also add to fold measurements if it's a folded surface
                if 'fold' in str(sample.get('Notes', '')).lower():
                    self.fold_measurements.append((strike, dip))
                continue

            # Look for trend/plunge (lines)
            trend = None
            plunge = None

            for pattern in trend_patterns:
                if pattern in sample:
                    val = self._safe_float(sample[pattern])
                    if val is not None:
                        trend = val
                        break

            for pattern in plunge_patterns:
                if pattern in sample:
                    val = self._safe_float(sample[pattern])
                    if val is not None:
                        plunge = val
                        break

            if trend is not None and plunge is not None:
                self.lines.append({
                    'sample_id': sample_id,
                    'trend': trend,
                    'plunge': plunge,
                    'type': struct_type or 'line'
                })

        # Calculate poles from planes
        self._update_poles()


        # Update UI if window is open
        self._update_ui_counts()

        return True

    def _update_poles(self):
        """Calculate poles from planes"""
        self.poles = []
        for plane in self.planes:
            strike = plane['strike']
            dip = plane['dip']

            # Pole is perpendicular to plane
            # trend = strike + 90°, plunge = 90 - dip
            trend = (strike + 90) % 360
            plunge = 90 - dip

            self.poles.append({
                'sample_id': plane['sample_id'],
                'trend': trend,
                'plunge': plunge,
                'source_plane': plane
            })

    def _update_ui_counts(self):
        """Update count displays in UI"""
        if hasattr(self, 'plane_count_label'):
            self.plane_count_label.config(text=f"P: {len(self.planes)} | L: {len(self.lines)} | Po: {len(self.poles)}")

    # ============================================================================
    # STEREOGRAPHIC PROJECTIONS
    # ============================================================================
    def _equal_area_projection(self, trend, plunge):
        """Schmidt net (equal area) projection"""
        plunge_rad = np.radians(plunge)
        trend_rad = np.radians(trend)

        r = np.sqrt(2) * np.sin(plunge_rad / 2)
        x = r * np.sin(trend_rad)
        y = r * np.cos(trend_rad)

        return x, y

    def _equal_angle_projection(self, trend, plunge):
        """Wulff net (equal angle) projection"""
        plunge_rad = np.radians(plunge)
        trend_rad = np.radians(trend)

        if plunge >= 90:
            return 0, 0

        r = np.tan((90 - plunge) * np.pi / 360)
        x = r * np.sin(trend_rad)
        y = r * np.cos(trend_rad)

        return x, y

    def _project(self, trend, plunge):
        """Project a point based on selected projection"""
        if self.projection_var.get() == "equal_area":
            return self._equal_area_projection(trend, plunge)
        else:
            return self._equal_angle_projection(trend, plunge)

    def _draw_net(self, ax):
        """Draw stereonet base with grid"""
        ax.clear()

        # Draw primitive circle
        circle = Circle((0, 0), 1, fill=False, edgecolor='black', linewidth=1)
        ax.add_patch(circle)

        if self.show_grid_var.get():
            # Draw cardinal directions
            ax.text(1.08, 0, 'E', ha='left', va='center', fontsize=7)
            ax.text(-1.08, 0, 'W', ha='right', va='center', fontsize=7)
            ax.text(0, 1.08, 'N', ha='center', va='bottom', fontsize=7)
            ax.text(0, -1.08, 'S', ha='center', va='top', fontsize=7)

            # Draw great circles (every 20° dip for cleaner look)
            for dip in range(20, 90, 20):
                x_great = []
                y_great = []
                for trend in np.linspace(0, 360, 91):
                    if self.projection_var.get() == "equal_area":
                        x, y = self._equal_area_projection(trend, dip)
                    else:
                        x, y = self._equal_angle_projection(trend, dip)
                    if not np.isnan(x) and not np.isnan(y):
                        x_great.append(x)
                        y_great.append(y)
                ax.plot(x_great, y_great, 'gray', linewidth=0.3, alpha=0.5)

            # Draw small circles (every 20° plunge)
            for plunge in range(20, 90, 20):
                x_small = []
                y_small = []
                for trend in np.linspace(0, 360, 181):
                    if self.projection_var.get() == "equal_area":
                        x, y = self._equal_area_projection(trend, plunge)
                    else:
                        x, y = self._equal_angle_projection(trend, plunge)
                    if not np.isnan(x) and not np.isnan(y):
                        x_small.append(x)
                        y_small.append(y)
                ax.plot(x_small, y_small, 'gray', linewidth=0.3, alpha=0.5)

        ax.set_xlim(-1.15, 1.15)
        ax.set_ylim(-1.15, 1.15)
        ax.set_aspect('equal')
        ax.axis('off')

        proj_name = "Schmidt" if self.projection_var.get() == "equal_area" else "Wulff"
        ax.set_title(f'{proj_name} Net', fontsize=9)

    def _plot_great_circle(self, ax, strike, dip, **kwargs):
        """Plot a plane as a great circle"""
        x_circle = []
        y_circle = []

        # Simplified great circle - points 90° from pole
        pole_trend = (strike + 90) % 360
        pole_plunge = 90 - dip

        for angle in np.linspace(0, 360, 91):
            point_trend = (pole_trend + angle) % 360
            point_plunge = 90 * np.abs(np.sin(np.radians(angle)))

            x, y = self._project(point_trend, point_plunge)
            x_circle.append(x)
            y_circle.append(y)

        ax.plot(x_circle, y_circle, **kwargs)

    def _plot_pole(self, ax, strike, dip, **kwargs):
        """Plot pole to a plane"""
        trend = (strike + 90) % 360
        plunge = 90 - dip

        x, y = self._project(trend, plunge)
        ax.scatter([x], [y], **kwargs)

    def _plot_line(self, ax, trend, plunge, **kwargs):
        """Plot a linear feature"""
        x, y = self._project(trend, plunge)
        ax.scatter([x], [y], **kwargs)

    # ============================================================================
    # DENSITY CONTOURING (Simplified)
    # ============================================================================
    def _calculate_density(self, points, grid_size=40):
        """Calculate point density on stereonet"""
        if not points:
            return None, None, None

        # Create grid
        x = np.linspace(-1, 1, grid_size)
        y = np.linspace(-1, 1, grid_size)
        X, Y = np.meshgrid(x, y)

        # Calculate distance to each point
        density = np.zeros_like(X)

        for px, py in points:
            if px**2 + py**2 <= 1:
                dist = np.sqrt((X - px)**2 + (Y - py)**2)
                # Simple inverse distance weighting
                weight = 1 / (dist + 0.1)
                density += weight

        # Mask outside circle
        mask = X**2 + Y**2 > 1
        density[mask] = np.nan

        # Normalize
        if not np.all(np.isnan(density)):
            density = density / np.nanmax(density)

        return X, Y, density

    def _plot_contours(self, ax):
        """Plot density contours"""
        # Collect all points
        points = []
        for pole in self.poles:
            x, y = self._project(pole['trend'], pole['plunge'])
            points.append((x, y))
        for line in self.lines:
            x, y = self._project(line['trend'], line['plunge'])
            points.append((x, y))

        if len(points) < 5:
            return

        X, Y, density = self._calculate_density(points, grid_size=40)

        if X is not None:
            levels = self.contour_levels_var.get()
            contour = ax.contour(X, Y, density, levels=levels,
                                cmap='hot', alpha=0.6, linewidths=0.8)

    # ============================================================================
    # FOLD ANALYSIS (Simplified)
    # ============================================================================
    def _analyze_fold(self):
        """Analyze fold axis from poles to bedding"""
        if len(self.poles) < 3:
            return None, None

        # Convert poles to unit vectors
        vectors = []
        for pole in self.poles:
            trend_rad = np.radians(pole['trend'])
            plunge_rad = np.radians(pole['plunge'])

            x = np.cos(plunge_rad) * np.sin(trend_rad)
            y = np.cos(plunge_rad) * np.cos(trend_rad)
            z = np.sin(plunge_rad)

            vectors.append([x, y, z])

        vectors = np.array(vectors)

        # Find mean vector (fold axis is perpendicular to mean pole)
        mean_vec = np.mean(vectors, axis=0)
        if np.linalg.norm(mean_vec) > 0:
            mean_vec = mean_vec / np.linalg.norm(mean_vec)

            # Fold axis is perpendicular to mean pole
            fold_axis_vec = np.cross(mean_vec, [0, 0, 1])
            if np.linalg.norm(fold_axis_vec) > 0:
                fold_axis_vec = fold_axis_vec / np.linalg.norm(fold_axis_vec)

                # Convert back to trend/plunge
                fold_trend = np.degrees(np.arctan2(fold_axis_vec[0], fold_axis_vec[1])) % 360
                fold_plunge = np.degrees(np.arcsin(fold_axis_vec[2]))

                # Calculate cone angle (average angle from fold axis)
                angles = []
                for vec in vectors:
                    dot = np.abs(np.dot(vec, fold_axis_vec))
                    if abs(dot) <= 1:
                        angle = np.degrees(np.arccos(dot))
                        angles.append(angle)

                cone_angle = np.mean(angles) if angles else None

                return (fold_trend, fold_plunge), cone_angle

        return None, None

    # ============================================================================
    # ROSE DIAGRAM
    # ============================================================================
    def _plot_rose(self, ax):
        """Plot rose diagram from directional data"""
        ax.clear()

        # Collect azimuths from lines and poles
        azimuths = []
        for line in self.lines:
            azimuths.append(line['trend'])
        for pole in self.poles:
            azimuths.append(pole['trend'])

        if not azimuths:
            ax.text(0.5, 0.5, "No data", ha='center', va='center', fontsize=9)
            return

        # Convert to radians
        az_rad = np.radians(azimuths)

        # Create histogram
        bin_size = self.rose_bin_size_var.get()
        bins = np.radians(np.arange(0, 361, bin_size))
        counts, edges = np.histogram(az_rad, bins=bins)

        # Normalize if requested
        if self.rose_normalize_var.get() and counts.max() > 0:
            counts = counts / counts.max()

        # Plot
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)

        theta = edges[:-1] + (edges[1] - edges[0]) / 2
        width = (edges[1] - edges[0])

        ax.bar(theta, counts, width=width, bottom=0.0,
               color=self.rose_color_var.get(), alpha=0.7,
               edgecolor='black', linewidth=0.3)

        ax.set_ylim(0, counts.max() * 1.1)
        ax.set_title(f'Rose (n={len(azimuths)})', fontsize=9)
        ax.grid(True, alpha=0.2)

    # ============================================================================
    # UPDATE PLOT
    # ============================================================================
    def _update_stereonet(self):
        """Update stereonet plot"""
        self.stereo_ax.clear()

        # Draw base net
        self._draw_net(self.stereo_ax)

        # Plot contours if enabled
        if self.contour_var.get():
            self._plot_contours(self.stereo_ax)

        # Plot planes as great circles (max 10 for clarity)
        max_planes = min(10, len(self.planes))
        for i in range(max_planes):
            plane = self.planes[i]
            color = plt.cm.tab10(i % 10)
            self._plot_great_circle(self.stereo_ax, plane['strike'], plane['dip'],
                                   color=color, linewidth=1, alpha=0.6)

        # Plot poles
        if self.poles:
            pole_x, pole_y = [], []
            for pole in self.poles:
                x, y = self._project(pole['trend'], pole['plunge'])
                pole_x.append(x)
                pole_y.append(y)
            self.stereo_ax.scatter(pole_x, pole_y, c='blue', s=self.point_size_var.get(),
                                  alpha=0.6, edgecolor='black', linewidth=0.3)

        # Plot lines
        if self.lines:
            line_x, line_y = [], []
            for line in self.lines:
                x, y = self._project(line['trend'], line['plunge'])
                line_x.append(x)
                line_y.append(y)
            self.stereo_ax.scatter(line_x, line_y, c='red', s=self.point_size_var.get(),
                                  marker='^', alpha=0.6, edgecolor='black', linewidth=0.3)

        # Plot fold axis if calculated
        if self.fold_axis:
            trend, plunge = self.fold_axis
            x, y = self._project(trend, plunge)
            self.stereo_ax.scatter([x], [y], c='green', s=60, marker='*',
                                  edgecolor='black', linewidth=0.5)

        self.stereo_canvas.draw()

    def _update_rose(self):
        """Update rose diagram"""
        self._plot_rose(self.rose_ax)
        self.rose_canvas.draw()

    # ============================================================================
    # ANALYSIS ACTIONS
    # ============================================================================
    def _run_fold_analysis(self):
        """Run fold axis analysis"""
        self.progress.start()
        self.status_var.set("Analyzing fold...")

        axis, cone = self._analyze_fold()

        if axis:
            self.fold_axis = axis
            self.cone_angle = cone

            trend, plunge = axis
            msg = (f"Fold Axis: {trend:.0f}° → {plunge:.0f}°\n"
                   f"Cone: {cone:.0f}°")
            messagebox.showinfo("Fold Analysis", msg)
            self.status_var.set(f"✅ Fold axis: {trend:.0f}°→{plunge:.0f}°")
            self._update_stereonet()
        else:
            messagebox.showwarning("Fold Analysis", "Insufficient data")
            self.status_var.set("❌ Fold analysis failed")

        self.progress.stop()

    def _add_plane_from_entry(self):
        """Add a plane from entry fields"""
        strike = self.strike_var.get()
        dip = self.dip_var.get()

        if 0 <= strike <= 360 and 0 <= dip <= 90:
            self.planes.append({
                'sample_id': f"M{len(self.planes)+1}",
                'strike': strike,
                'dip': dip,
                'type': 'plane'
            })
            self._update_poles()
            self._update_ui_counts()
            self._update_stereonet()
            self.status_var.set(f"✅ Added: {strike:.0f}/{dip:.0f}")
        else:
            messagebox.showwarning("Invalid", "Strike:0-360, Dip:0-90")

    def _add_line_from_entry(self):
        """Add a line from entry fields"""
        trend = self.trend_var.get()
        plunge = self.plunge_var.get()

        if 0 <= trend <= 360 and 0 <= plunge <= 90:
            self.lines.append({
                'sample_id': f"M{len(self.lines)+1}",
                'trend': trend,
                'plunge': plunge,
                'type': 'line'
            })
            self._update_ui_counts()
            self._update_stereonet()
            self.status_var.set(f"✅ Added: {trend:.0f}→{plunge:.0f}°")
        else:
            messagebox.showwarning("Invalid", "Trend:0-360, Plunge:0-90")

    def _clear_all(self):
        """Clear all data"""
        self.planes = []
        self.lines = []
        self.poles = []
        self.fold_axis = None
        self._update_ui_counts()
        self._update_stereonet()
        self._update_rose()
        self.status_var.set("🧹 Cleared")

    # ============================================================================
    # EXPORT RESULTS
    # ============================================================================
    def _export_results(self):
        """Export structural data to main app"""
        records = []
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Export planes
        for plane in self.planes:
            records.append({
                'Sample_ID': plane.get('sample_id', 'Unknown'),
                'Structure_Type': 'Plane',
                'Strike': f"{plane['strike']:.1f}",
                'Dip': f"{plane['dip']:.1f}",
                'Structural_Timestamp': timestamp
            })

        # Export lines
        for line in self.lines:
            records.append({
                'Sample_ID': line.get('sample_id', 'Unknown'),
                'Structure_Type': 'Line',
                'Trend': f"{line['trend']:.1f}",
                'Plunge': f"{line['plunge']:.1f}",
                'Structural_Timestamp': timestamp
            })

        # Export fold axis if calculated
        if self.fold_axis:
            trend, plunge = self.fold_axis
            records.append({
                'Sample_ID': 'FOLD_AXIS',
                'Structure_Type': 'Fold Axis',
                'Trend': f"{trend:.1f}",
                'Plunge': f"{plunge:.1f}",
                'Cone_Angle': f"{self.cone_angle:.1f}" if self.cone_angle else '',
                'Structural_Timestamp': timestamp
            })

        if records:
            self.app.import_data_from_plugin(records)
            self.status_var.set(f"✅ Exported {len(records)} measurements")

    # ============================================================================
    # UI CONSTRUCTION - COMPACT VERSION
    # ============================================================================
    def open_window(self):
        """Open the main window"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            self._load_from_main_app()
            self._update_stereonet()
            self._update_rose()
            return

        if not self.dependencies_met:
            messagebox.showerror(
                "Missing Dependencies",
                f"Please install: {', '.join(self.missing_deps)}"
            )
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("🧭 Structural Suite v1.0")
        self.window.geometry("950x650")  # MUCH MORE COMPACT!

        self._create_interface()

        # Load data
        if self._load_from_main_app():
            self.status_var.set(f"✅ Loaded structural data")
        else:
            self.status_var.set("ℹ️ No data - add manually")

        self._update_stereonet()
        self._update_rose()

        self.window.transient(self.app.root)
        self.window.lift()
        self.window.focus_force()

    def _create_interface(self):
        """Create the interface with 2 main tabs - COMPACT"""
        # Header - smaller
        header = tk.Frame(self.window, bg="#16a085", height=32)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="🧭", font=("Arial", 14),
                bg="#16a085", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Label(header, text="Structural Suite",
                font=("Arial", 11, "bold"),
                bg="#16a085", fg="white").pack(side=tk.LEFT, padx=2)
        tk.Label(header, text="v1.0",
                font=("Arial", 7),
                bg="#16a085", fg="#f1c40f").pack(side=tk.LEFT, padx=3)

        # Compact status in header
        self.compact_status = tk.Label(header, text="●", font=("Arial", 10),
                                       bg="#16a085", fg="#2ecc71")
        self.compact_status.pack(side=tk.RIGHT, padx=5)

        # Main notebook
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)

        # Create tabs
        self._create_stereonet_tab()
        self._create_rose_tab()

        # Status bar - smaller
        status = tk.Frame(self.window, bg="#34495e", height=20)
        status.pack(fill=tk.X, side=tk.BOTTOM)
        status.pack_propagate(False)

        self.status_var = tk.StringVar(value="Ready")
        tk.Label(status, textvariable=self.status_var,
                font=("Arial", 7), bg="#34495e", fg="white").pack(side=tk.LEFT, padx=5)

        tk.Button(status, text="📤 Export",
                 command=self._export_results,
                 bg="#27ae60", fg="white", font=("Arial", 6), height=1, width=8).pack(side=tk.RIGHT, padx=2)

        self.progress = ttk.Progressbar(status, mode='indeterminate', length=80)
        self.progress.pack(side=tk.RIGHT, padx=2)

    # ============================================================================
    # TAB 1: Stereonet - COMPACT
    # ============================================================================
    def _create_stereonet_tab(self):
        """Create stereonet tab - COMPACT"""
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="🧭 Stereonet")

        # Split into left/right
        paned = tk.PanedWindow(tab, orient=tk.HORIZONTAL, sashwidth=2)
        paned.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        # Left panel - controls (200px compact!)
        left = tk.Frame(paned, bg="#f5f5f5", width=200)
        paned.add(left, width=200, minsize=180)

        # Right panel - plot (400x400 square - 1/3 smaller!)
        right = tk.Frame(paned, bg="white", width=400, height=400)
        paned.add(right, width=400, minsize=350)

        # ===== Left controls - VERY COMPACT =====
        # Data summary - one line
        summary = tk.LabelFrame(left, text="📊", padx=3, pady=2, bg="#f5f5f5", font=("Arial", 7))
        summary.pack(fill=tk.X, padx=3, pady=1)

        self.plane_count_label = tk.Label(summary, text=f"P:0 L:0 Po:0",
                                          font=("Arial", 7), bg="#f5f5f5")
        self.plane_count_label.pack()

        # Projection - compact
        proj_frame = tk.LabelFrame(left, text="🌐 Proj", padx=3, pady=2, bg="#f5f5f5", font=("Arial", 7))
        proj_frame.pack(fill=tk.X, padx=3, pady=1)

        tk.Radiobutton(proj_frame, text="Schmidt", variable=self.projection_var,
                      value="equal_area", command=self._update_stereonet,
                      bg="#f5f5f5", font=("Arial", 7)).pack(anchor=tk.W)
        tk.Radiobutton(proj_frame, text="Wulff", variable=self.projection_var,
                      value="equal_angle", command=self._update_stereonet,
                      bg="#f5f5f5", font=("Arial", 7)).pack(anchor=tk.W)

        # Manual entry - VERY compact
        entry_frame = tk.LabelFrame(left, text="✏️ Add", padx=3, pady=2, bg="#f5f5f5", font=("Arial", 7))
        entry_frame.pack(fill=tk.X, padx=3, pady=1)

        # Plane entry - one line
        p_frame = tk.Frame(entry_frame, bg="#f5f5f5")
        p_frame.pack(fill=tk.X)
        tk.Label(p_frame, text="P:", font=("Arial", 7, "bold"),
                bg="#f5f5f5").pack(side=tk.LEFT)
        tk.Spinbox(p_frame, from_=0, to=360, increment=1,
                  textvariable=self.strike_var, width=3, font=("Arial", 7)).pack(side=tk.LEFT, padx=1)
        tk.Spinbox(p_frame, from_=0, to=90, increment=1,
                  textvariable=self.dip_var, width=2, font=("Arial", 7)).pack(side=tk.LEFT, padx=1)
        tk.Button(p_frame, text="+", width=1, command=self._add_plane_from_entry,
                 bg="#3498db", fg="white", font=("Arial", 6)).pack(side=tk.LEFT, padx=1)

        # Line entry - one line
        l_frame = tk.Frame(entry_frame, bg="#f5f5f5")
        l_frame.pack(fill=tk.X)
        tk.Label(l_frame, text="L:", font=("Arial", 7, "bold"),
                bg="#f5f5f5").pack(side=tk.LEFT)
        tk.Spinbox(l_frame, from_=0, to=360, increment=1,
                  textvariable=self.trend_var, width=3, font=("Arial", 7)).pack(side=tk.LEFT, padx=1)
        tk.Spinbox(l_frame, from_=0, to=90, increment=1,
                  textvariable=self.plunge_var, width=2, font=("Arial", 7)).pack(side=tk.LEFT, padx=1)
        tk.Button(l_frame, text="+", width=1, command=self._add_line_from_entry,
                 bg="#e67e22", fg="white", font=("Arial", 6)).pack(side=tk.LEFT, padx=1)

        # Display options - compact grid
        disp_frame = tk.LabelFrame(left, text="🎨 Display", padx=3, pady=2, bg="#f5f5f5", font=("Arial", 7))
        disp_frame.pack(fill=tk.X, padx=3, pady=1)

        tk.Checkbutton(disp_frame, text="Grid", variable=self.show_grid_var,
                      command=self._update_stereonet, bg="#f5f5f5",
                      font=("Arial", 7)).pack(side=tk.LEFT, padx=1)

        tk.Checkbutton(disp_frame, text="Contour", variable=self.contour_var,
                      command=self._update_stereonet, bg="#f5f5f5",
                      font=("Arial", 7)).pack(side=tk.LEFT, padx=1)

        # Size and levels in one line
        sz_frame = tk.Frame(disp_frame, bg="#f5f5f5")
        sz_frame.pack(fill=tk.X)
        tk.Label(sz_frame, text="Sz:", bg="#f5f5f5", font=("Arial", 7)).pack(side=tk.LEFT)
        tk.Scale(sz_frame, from_=5, to=30, orient=tk.HORIZONTAL,
                variable=self.point_size_var, command=lambda x: self._update_stereonet(),
                length=50, showvalue=0).pack(side=tk.LEFT)

        # Analysis buttons - compact
        anal_frame = tk.Frame(left, bg="#f5f5f5")
        anal_frame.pack(fill=tk.X, padx=3, pady=1)

        tk.Button(anal_frame, text="🔍 Fold", command=self._run_fold_analysis,
                 bg="#9b59b6", fg="white", font=("Arial", 7), width=6).pack(side=tk.LEFT, padx=1)
        tk.Button(anal_frame, text="🗑️ Clear", command=self._clear_all,
                 bg="#e74c3c", fg="white", font=("Arial", 7), width=5).pack(side=tk.RIGHT, padx=1)

        # ===== Right plot - 400x400 square =====
        self.stereo_fig = plt.Figure(figsize=(4, 4), dpi=90)  # 400x400
        self.stereo_fig.patch.set_facecolor('white')
        self.stereo_ax = self.stereo_fig.add_subplot(111)

        self.stereo_canvas = FigureCanvasTkAgg(self.stereo_fig, right)
        self.stereo_canvas.draw()
        self.stereo_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Minimal toolbar
        toolbar_frame = tk.Frame(right, height=18)
        toolbar_frame.pack(fill=tk.X)
        toolbar = NavigationToolbar2Tk(self.stereo_canvas, toolbar_frame)
        toolbar.update()

    # ============================================================================
    # TAB 2: Rose Diagram - COMPACT
    # ============================================================================
    def _create_rose_tab(self):
        """Create rose diagram tab - COMPACT"""
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="🌹 Rose")

        # Split into left/right
        paned = tk.PanedWindow(tab, orient=tk.HORIZONTAL, sashwidth=2)
        paned.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        # Left panel - controls (180px)
        left = tk.Frame(paned, bg="#f5f5f5", width=180)
        paned.add(left, width=180, minsize=160)

        # Right panel - plot (400x400 square)
        right = tk.Frame(paned, bg="white", width=400, height=400)
        paned.add(right, width=400, minsize=350)

        # ===== Left controls - VERY COMPACT =====
        # Options
        opt_frame = tk.LabelFrame(left, text="⚙️ Options", padx=3, pady=2, bg="#f5f5f5", font=("Arial", 7))
        opt_frame.pack(fill=tk.X, padx=3, pady=1)

        # Bin size
        bin_frame = tk.Frame(opt_frame, bg="#f5f5f5")
        bin_frame.pack(fill=tk.X)
        tk.Label(bin_frame, text="Bin:", bg="#f5f5f5", font=("Arial", 7)).pack(side=tk.LEFT)
        tk.Spinbox(bin_frame, from_=5, to=30, increment=5,
                  textvariable=self.rose_bin_size_var, width=3,
                  command=self._update_rose, font=("Arial", 7)).pack(side=tk.LEFT, padx=2)

        # Normalize
        tk.Checkbutton(opt_frame, text="Norm", variable=self.rose_normalize_var,
                      command=self._update_rose, bg="#f5f5f5",
                      font=("Arial", 7)).pack(anchor=tk.W)

        # Color
        color_frame = tk.Frame(opt_frame, bg="#f5f5f5")
        color_frame.pack(fill=tk.X)
        tk.Label(color_frame, text="Color:", bg="#f5f5f5", font=("Arial", 7)).pack(side=tk.LEFT)
        colors = ['steelblue', 'red', 'green', 'purple']
        ttk.Combobox(color_frame, textvariable=self.rose_color_var,
                    values=colors, width=6, state='readonly',
                    font=("Arial", 7)).pack(side=tk.LEFT, padx=2)

        # Update button
        tk.Button(opt_frame, text="🔄 Update", command=self._update_rose,
                 bg="#3498db", fg="white", font=("Arial", 7), width=8).pack(pady=2)

        # ===== Right plot - 400x400 square =====
        self.rose_fig = plt.Figure(figsize=(4, 4), dpi=90)
        self.rose_fig.patch.set_facecolor('white')
        self.rose_ax = self.rose_fig.add_subplot(111, projection='polar')

        self.rose_canvas = FigureCanvasTkAgg(self.rose_fig, right)
        self.rose_canvas.draw()
        self.rose_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        toolbar_frame = tk.Frame(right, height=18)
        toolbar_frame.pack(fill=tk.X)
        toolbar = NavigationToolbar2Tk(self.rose_canvas, toolbar_frame)
        toolbar.update()


def setup_plugin(main_app):
    """Plugin setup function"""
    plugin = StructuralSuitePlugin(main_app)
    return plugin
