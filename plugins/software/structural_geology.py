"""
Structural Geology Plugin v1.0
Stereonets · Schmidt nets · Wulff nets · Rose diagrams
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Author: Sefy Levy & DeepSeek
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

PLUGIN_INFO = {
    "category": "software",
    "id": "structural_geology",
    "name": "Structural Geology Suite",
    "icon": "🧭",
    "description": "Stereonets · Schmidt nets · Wulff nets · Rose diagrams · Structural analysis",
    "version": "1.0.0",
    "requires": ["numpy", "matplotlib", "scipy"],
    "author": "Sefy Levy & DeepSeek"
}

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Circle, Polygon
import math

# ============================================================================
# CORE STEREONET FUNCTIONS
# ============================================================================

class Stereonet:
    """Base class for stereographic projections"""

    @staticmethod
    def equal_area(plunge: float, trend: float) -> tuple:
        """
        Schmidt net (equal area) projection
        plunge: dip angle (0-90°)
        trend: dip direction (0-360°)
        Returns (x, y) coordinates on unit circle
        """
        plunge_rad = np.radians(plunge)
        trend_rad = np.radians(trend)

        r = np.sqrt(2) * np.sin(plunge_rad / 2)
        x = r * np.sin(trend_rad)
        y = r * np.cos(trend_rad)

        return x, y

    @staticmethod
    def equal_angle(plunge: float, trend: float) -> tuple:
        """
        Wulff net (equal angle) projection
        plunge: dip angle (0-90°)
        trend: dip direction (0-360°)
        Returns (x, y) coordinates on unit circle
        """
        plunge_rad = np.radians(plunge)
        trend_rad = np.radians(trend)

        r = np.tan((90 - plunge) * np.pi / 360)
        x = r * np.sin(trend_rad)
        y = r * np.cos(trend_rad)

        return x, y

    @staticmethod
    def plot_net(ax, projection='equal_area', grid=True):
        """Plot stereonet base"""
        ax.clear()

        # Draw primitive circle
        circle = Circle((0, 0), 1, fill=False, edgecolor='black', linewidth=1.5)
        ax.add_patch(circle)

        if grid:
            # Draw great circles and small circles
            theta = np.linspace(0, 2*np.pi, 100)

            # Meridians (great circles) every 10°
            for strike in range(0, 180, 10):
                x, y = [], []
                for plunge in range(0, 91, 5):
                    if projection == 'equal_area':
                        xi, yi = Stereonet.equal_area(plunge, strike)
                    else:
                        xi, yi = Stereonet.equal_angle(plunge, strike)
                    x.append(xi)
                    y.append(yi)
                ax.plot(x, y, 'gray', linewidth=0.5, alpha=0.5)

            # Small circles (latitude lines) every 10°
            for plunge in range(10, 90, 10):
                x, y = [], []
                for trend in range(0, 361, 5):
                    if projection == 'equal_area':
                        xi, yi = Stereonet.equal_area(plunge, trend)
                    else:
                        xi, yi = Stereonet.equal_angle(plunge, trend)
                    x.append(xi)
                    y.append(yi)
                ax.plot(x, y, 'gray', linewidth=0.5, alpha=0.5)

        ax.set_xlim(-1.1, 1.1)
        ax.set_ylim(-1.1, 1.1)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title(f"{'Schmidt' if projection=='equal_area' else 'Wulff'} Net")

        return ax

    @staticmethod
    def plot_plane(ax, strike: float, dip: float, projection='equal_area',
                   color='red', linewidth=2):
        """Plot a plane as a great circle"""
        # Convert strike/dip to poles for each azimuth
        x, y = [], []
        for trend in range(0, 361, 5):
            # Calculate apparent dip in direction trend
            apparent_dip = np.degrees(np.arctan(
                np.tan(np.radians(dip)) * np.sin(np.radians(trend - strike))
            ))
            if apparent_dip > 0:
                if projection == 'equal_area':
                    xi, yi = Stereonet.equal_area(apparent_dip, trend)
                else:
                    xi, yi = Stereonet.equal_angle(apparent_dip, trend)
                x.append(xi)
                y.append(yi)

        ax.plot(x, y, color=color, linewidth=linewidth)
        return ax

    @staticmethod
    def plot_pole(ax, strike: float, dip: float, projection='equal_area',
                  marker='o', color='blue', size=50):
        """Plot pole to a plane"""
        # Pole is perpendicular to plane: trend = strike ± 90°, plunge = 90 - dip
        pole_trend = (strike + 90) % 360
        pole_plunge = 90 - dip

        if projection == 'equal_area':
            x, y = Stereonet.equal_area(pole_plunge, pole_trend)
        else:
            x, y = Stereonet.equal_angle(pole_plunge, pole_trend)

        ax.scatter([x], [y], c=color, marker=marker, s=size, alpha=0.7)
        return ax

    @staticmethod
    def plot_line(ax, plunge: float, trend: float, projection='equal_area',
                  marker='^', color='green', size=50):
        """Plot a line (fold axis, lineation)"""
        if projection == 'equal_area':
            x, y = Stereonet.equal_area(plunge, trend)
        else:
            x, y = Stereonet.equal_angle(plunge, trend)

        ax.scatter([x], [y], c=color, marker=marker, s=size, alpha=0.7)
        return ax


# ============================================================================
# ROSE DIAGRAM (for azimuth data)
# ============================================================================

class RoseDiagram:
    """Rose diagram for directional data"""

    @staticmethod
    def plot(ax, azimuths: list, weights: list = None,
             bin_size: int = 10, color: str = 'steelblue'):
        """
        Plot rose diagram

        azimuths: list of azimuth angles (0-360°)
        weights: optional weights (e.g., fracture length)
        bin_size: bin width in degrees
        """
        # Convert to radians
        az_rad = np.radians(azimuths)

        # Create histogram
        bins = np.radians(np.arange(0, 361, bin_size))
        counts, edges = np.histogram(az_rad, bins=bins)

        if weights is not None:
            counts, _ = np.histogram(az_rad, bins=bins, weights=weights)

        # Normalize to max length
        max_count = max(counts)
        if max_count > 0:
            counts = counts / max_count

        # Plot as bar chart in polar coordinates
        ax.clear()
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)

        # Calculate bar positions
        theta = edges[:-1] + (edges[1] - edges[0]) / 2
        width = (edges[1] - edges[0])

        bars = ax.bar(theta, counts, width=width, bottom=0.0,
                     color=color, alpha=0.7, edgecolor='black')

        # Add radial grid
        ax.set_ylim(0, 1)
        ax.grid(True, alpha=0.3)
        ax.set_title("Rose Diagram")

        return ax

    @staticmethod
    def rose_from_stereo(ax, stereo_data: list, bin_size: int = 10):
        """Extract azimuths from stereonet points and plot rose"""
        azimuths = []
        for x, y in stereo_data:
            # Convert Cartesian to polar
            r = np.sqrt(x**2 + y**2)
            if r > 0:
                theta = np.degrees(np.arctan2(x, y)) % 360
                azimuths.append(theta)

        return RoseDiagram.plot(ax, azimuths, bin_size=bin_size)


# ============================================================================
# MAIN PLUGIN UI
# ============================================================================

class StructuralGeologyPlugin:
    def __init__(self, main_app):
        self.app = main_app
        self.window = None

        # Data storage
        self.planes = []      # List of (strike, dip) tuples
        self.lines = []        # List of (plunge, trend) tuples
        self.poles = []        # Will be auto-calculated

        # UI Variables
        self.projection_var = tk.StringVar(value="equal_area")  # equal_area or equal_angle
        self.strike_var = tk.DoubleVar(value=0)
        self.dip_var = tk.DoubleVar(value=45)
        self.plunge_var = tk.DoubleVar(value=30)
        self.trend_var = tk.DoubleVar(value=0)
        self.bin_size_var = tk.IntVar(value=10)
        self.view_var = tk.StringVar(value="stereonet")

    def open_window(self):
        """Open the structural geology window"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("🧭 Structural Geology Suite v1.0")
        self.window.geometry("1100x650")
        self.window.transient(self.app.root)

        self._create_ui()
        self._plot_stereonet()
        self.window.lift()

    def _create_ui(self):
        """Create compact interface"""

        # Header
        header = tk.Frame(self.window, bg="#16a085", height=40)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="🧭", font=("Arial", 18),
                bg="#16a085", fg="white").pack(side=tk.LEFT, padx=8)
        tk.Label(header, text="Structural Geology Suite",
                font=("Arial", 12, "bold"), bg="#16a085", fg="white").pack(side=tk.LEFT, padx=2)
        tk.Label(header, text="Stereonets · Rose diagrams · Structural analysis",
                font=("Arial", 8), bg="#16a085", fg="#f1c40f").pack(side=tk.LEFT, padx=8)

        self.status_indicator = tk.Label(header, text="● READY",
                                        font=("Arial", 8), bg="#16a085", fg="#2ecc71")
        self.status_indicator.pack(side=tk.RIGHT, padx=10)

        # Main content
        main_paned = tk.PanedWindow(self.window, orient=tk.HORIZONTAL, sashwidth=4)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left panel - Controls
        left = tk.Frame(main_paned, bg="#ecf0f1", width=350)
        main_paned.add(left, width=350)

        # Projection selection
        proj_frame = tk.LabelFrame(left, text="1. Projection", font=("Arial", 9, "bold"),
                                   bg="#ecf0f1", padx=8, pady=6)
        proj_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Radiobutton(proj_frame, text="Schmidt net (Equal area)",
                      variable=self.projection_var, value="equal_area",
                      bg="#ecf0f1").pack(anchor=tk.W)
        tk.Radiobutton(proj_frame, text="Wulff net (Equal angle)",
                      variable=self.projection_var, value="equal_angle",
                      bg="#ecf0f1").pack(anchor=tk.W)

        # View selection
        view_frame = tk.LabelFrame(left, text="2. View", font=("Arial", 9, "bold"),
                                   bg="#ecf0f1", padx=8, pady=6)
        view_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Radiobutton(view_frame, text="Stereonet",
                      variable=self.view_var, value="stereonet",
                      bg="#ecf0f1").pack(anchor=tk.W)
        tk.Radiobutton(view_frame, text="Rose diagram",
                      variable=self.view_var, value="rose",
                      bg="#ecf0f1", command=self._switch_view).pack(anchor=tk.W)

        # Data entry
        data_frame = tk.LabelFrame(left, text="3. Add Data", font=("Arial", 9, "bold"),
                                   bg="#ecf0f1", padx=8, pady=6)
        data_frame.pack(fill=tk.X, padx=5, pady=5)

        # Planes
        plane_frame = tk.Frame(data_frame, bg="#ecf0f1")
        plane_frame.pack(fill=tk.X, pady=2)

        tk.Label(plane_frame, text="Plane:", width=6, anchor=tk.W,
                bg="#ecf0f1", font=("Arial", 8, "bold")).grid(row=0, column=0)

        tk.Label(plane_frame, text="Strike:", bg="#ecf0f1").grid(row=0, column=1, padx=2)
        strike_spin = tk.Spinbox(plane_frame, from_=0, to=360, increment=1,
                                textvariable=self.strike_var, width=5)
        strike_spin.grid(row=0, column=2, padx=2)

        tk.Label(plane_frame, text="Dip:", bg="#ecf0f1").grid(row=0, column=3, padx=2)
        dip_spin = tk.Spinbox(plane_frame, from_=0, to=90, increment=1,
                             textvariable=self.dip_var, width=4)
        dip_spin.grid(row=0, column=4, padx=2)

        tk.Button(plane_frame, text="➕ Add Plane",
                 command=self._add_plane,
                 bg="#3498db", fg="white", font=("Arial", 7)).grid(row=0, column=5, padx=2)

        # Lines
        line_frame = tk.Frame(data_frame, bg="#ecf0f1")
        line_frame.pack(fill=tk.X, pady=2)

        tk.Label(line_frame, text="Line:", width=6, anchor=tk.W,
                bg="#ecf0f1", font=("Arial", 8, "bold")).grid(row=0, column=0)

        tk.Label(line_frame, text="Plunge:", bg="#ecf0f1").grid(row=0, column=1, padx=2)
        plunge_spin = tk.Spinbox(line_frame, from_=0, to=90, increment=1,
                                textvariable=self.plunge_var, width=5)
        plunge_spin.grid(row=0, column=2, padx=2)

        tk.Label(line_frame, text="Trend:", bg="#ecf0f1").grid(row=0, column=3, padx=2)
        trend_spin = tk.Spinbox(line_frame, from_=0, to=360, increment=1,
                               textvariable=self.trend_var, width=5)
        trend_spin.grid(row=0, column=4, padx=2)

        tk.Button(line_frame, text="➕ Add Line",
                 command=self._add_line,
                 bg="#e67e22", fg="white", font=("Arial", 7)).grid(row=0, column=5, padx=2)

        # Rose diagram options
        self.rose_frame = tk.Frame(data_frame, bg="#ecf0f1")

        tk.Label(self.rose_frame, text="Bin size:", bg="#ecf0f1",
                font=("Arial", 8)).pack(side=tk.LEFT, padx=2)
        tk.Spinbox(self.rose_frame, from_=5, to=30, increment=5,
                  textvariable=self.bin_size_var, width=4).pack(side=tk.LEFT, padx=2)
        tk.Button(self.rose_frame, text="Update Rose",
                 command=self._plot_rose,
                 bg="#27ae60", fg="white", font=("Arial", 7)).pack(side=tk.LEFT, padx=2)

        # Data list
        list_frame = tk.LabelFrame(left, text="4. Data List", font=("Arial", 9, "bold"),
                                   bg="#ecf0f1", padx=8, pady=6)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.data_listbox = tk.Listbox(list_frame, height=8)
        scroll = tk.Scrollbar(list_frame, command=self.data_listbox.yview)
        self.data_listbox.configure(yscrollcommand=scroll.set)

        self.data_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Clear button
        tk.Button(list_frame, text="🗑️ Clear All",
                 command=self._clear_all,
                 bg="#e74c3c", fg="white").pack(pady=2)

        # Right panel - Plot
        right = tk.Frame(main_paned, bg="white")
        main_paned.add(right, width=600)

        self.fig = plt.Figure(figsize=(7, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, right)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Bottom status
        status = tk.Frame(self.window, bg="#2c3e50", height=24)
        status.pack(fill=tk.X, side=tk.BOTTOM)
        status.pack_propagate(False)
        self.status_var = tk.StringVar(value="Ready")
        tk.Label(status, textvariable=self.status_var,
                font=("Arial", 7), bg="#2c3e50", fg="white").pack(side=tk.LEFT, padx=8)

        # Export button
        tk.Button(status, text="📊 Export to Table",
                 command=self._export_to_main,
                 bg="#27ae60", fg="white", font=("Arial", 7)).pack(side=tk.RIGHT, padx=5)

    def _add_plane(self):
        """Add a plane to the stereonet"""
        strike = self.strike_var.get()
        dip = self.dip_var.get()

        self.planes.append((strike, dip))
        self.data_listbox.insert(tk.END, f"Plane: {strike:.0f}/{dip:.0f}")

        self._plot_stereonet()
        self.status_var.set(f"✅ Added plane {strike:.0f}/{dip:.0f}")

    def _add_line(self):
        """Add a line to the stereonet"""
        plunge = self.plunge_var.get()
        trend = self.trend_var.get()

        self.lines.append((plunge, trend))
        self.data_listbox.insert(tk.END, f"Line: {plunge:.0f}→{trend:.0f}")

        self._plot_stereonet()
        self.status_var.set(f"✅ Added line {plunge:.0f}°→{trend:.0f}°")

    def _clear_all(self):
        """Clear all data"""
        self.planes.clear()
        self.lines.clear()
        self.data_listbox.delete(0, tk.END)
        self._plot_stereonet()
        self.status_var.set("🧹 Cleared")

    def _plot_stereonet(self):
        """Plot stereonet with current data"""
        projection = self.projection_var.get()

        # Plot base
        Stereonet.plot_net(self.ax, projection=projection)

        # Plot planes
        colors = plt.cm.Set1(np.linspace(0, 1, max(1, len(self.planes))))
        for i, (strike, dip) in enumerate(self.planes):
            Stereonet.plot_plane(self.ax, strike, dip, projection=projection,
                                color=colors[i % len(colors)], linewidth=2)
            Stereonet.plot_pole(self.ax, strike, dip, projection=projection,
                               color=colors[i % len(colors)])

        # Plot lines
        for plunge, trend in self.lines:
            Stereonet.plot_line(self.ax, plunge, trend, projection=projection)

        self.canvas.draw()

    def _plot_rose(self):
        """Plot rose diagram from current data"""
        # Extract azimuths from lines and poles
        azimuths = []

        # Add line trends
        for plunge, trend in self.lines:
            azimuths.append(trend)

        # Add pole trends from planes
        for strike, dip in self.planes:
            pole_trend = (strike + 90) % 360
            azimuths.append(pole_trend)

        if not azimuths:
            messagebox.showwarning("No Data", "Add planes or lines first")
            return

        self.ax.clear()
        RoseDiagram.plot(self.ax, azimuths, bin_size=self.bin_size_var.get())
        self.canvas.draw()
        self.status_var.set(f"✅ Rose diagram from {len(azimuths)} measurements")

    def _switch_view(self):
        """Switch between stereonet and rose diagram"""
        if self.view_var.get() == "stereonet":
            self._plot_stereonet()
        else:
            self._plot_rose()

    def _export_to_main(self):
        """Export data to main app"""
        table_data = []

        for i, (strike, dip) in enumerate(self.planes):
            table_data.append({
                'Sample_ID': f"PLANE_{i+1:03d}",
                'Structure_Type': 'Plane',
                'Strike': f"{strike:.1f}",
                'Dip': f"{dip:.1f}",
                'Dip_Direction': f"{(strike+90)%360:.1f}",
                'Notes': f"Plane orientation (RHR)"
            })

        for i, (plunge, trend) in enumerate(self.lines):
            table_data.append({
                'Sample_ID': f"LINE_{i+1:03d}",
                'Structure_Type': 'Line',
                'Plunge': f"{plunge:.1f}",
                'Trend': f"{trend:.1f}",
                'Notes': f"Lineation / fold axis"
            })

        if table_data:
            self.app.import_data_from_plugin(table_data)
            self.status_var.set(f"✅ Exported {len(table_data)} structures")


def setup_plugin(main_app):
    """Plugin setup"""
    return StructuralGeologyPlugin(main_app)
