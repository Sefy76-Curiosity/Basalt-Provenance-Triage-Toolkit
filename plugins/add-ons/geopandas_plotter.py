"""
Geopandas Plotter - UI Add-on
Archaeological site mapping

Author: Sefy Levy
Category: UI Add-on
"""
import tkinter as tk
from tkinter import ttk
import threading

HAS_GEOPANDAS = False
HAS_MATPLOTLIB = False
try:
    import matplotlib
    matplotlib.use('TkAgg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import geopandas as gpd
    from shapely.geometry import Point
    import contextily as ctx
    HAS_GEOPANDAS = True
    HAS_MATPLOTLIB = True
except ImportError:
    pass

PLUGIN_INFO = {
    'id': 'geopandas_plotter',
    'name': 'Geopandas Archaeological Mapper',
    'category': 'add-ons',
    'icon': '🗺️',
    'version': '2.0',
    'requires': ['geopandas', 'matplotlib', 'contextily', 'shapely'],
    'description': 'Map archaeological sites with basemaps',
    'exclusive_group': 'plotter'
}

class GeopandasPlotterPlugin:
    """Geopandas plotter add-on"""
    def __init__(self, parent_app):
        self.app = parent_app

def register_plugin(parent_app):
    """Register this add-on and return an instance."""
    return GeopandasPlotterPlugin(parent_app)

def plot_geopandas(frame, samples):
    """Create archaeological site maps."""
    if not HAS_GEOPANDAS:
        for widget in frame.winfo_children():
            widget.destroy()
        label = tk.Label(frame,
                        text="Geopandas not available\nInstall with:\npip install geopandas matplotlib contextily shapely",
                        fg="red", font=("Arial", 12), justify=tk.LEFT)
        label.pack(expand=True)
        return

    # Clear frame
    for widget in frame.winfo_children():
        widget.destroy()

    if not samples:
        label = tk.Label(frame, text="No data to plot", font=("Arial", 12))
        label.pack(expand=True)
        return

    # Create control panel
    control_frame = ttk.Frame(frame)
    control_frame.pack(fill=tk.X, pady=5)

    ttk.Label(control_frame, text="Basemap:").pack(side=tk.LEFT, padx=5)
    basemap_var = tk.StringVar(value="Street")
    basemap_combo = ttk.Combobox(control_frame, textvariable=basemap_var,
                                 values=["Street", "Satellite", "Terrain", "None"],
                                 state='readonly', width=15)
    basemap_combo.pack(side=tk.LEFT, padx=5)

    ttk.Label(control_frame, text="Marker Size:").pack(side=tk.LEFT, padx=5)
    size_var = tk.StringVar(value="50")
    size_spin = ttk.Spinbox(control_frame, from_=10, to=200, textvariable=size_var, width=5)
    size_spin.pack(side=tk.LEFT, padx=5)

    def update_map():
        plot_map(basemap_var.get(), int(size_var.get()))

    ttk.Button(control_frame, text="Update Map", command=update_map).pack(side=tk.LEFT, padx=10)

    # Create frame for map
    map_frame = ttk.Frame(frame)
    map_frame.pack(fill=tk.BOTH, expand=True, pady=5)

    def plot_map(basemap='Street', marker_size=50):
        # Clear map frame
        for widget in map_frame.winfo_children():
            widget.destroy()

        # Create figure
        fig, ax = plt.subplots(1, 1, figsize=(10, 8))

        # Extract coordinates and data
        points = []
        data = []

        for s in samples:
            try:
                # Look for coordinates in various possible fields
                lat = None
                lon = None

                # Check common coordinate fields
                if 'Latitude' in s and 'Longitude' in s:
                    lat = float(s['Latitude'])
                    lon = float(s['Longitude'])
                elif 'lat' in s and 'lon' in s:
                    lat = float(s['lat'])
                    lon = float(s['lon'])
                elif 'Y' in s and 'X' in s:
                    lat = float(s['Y'])
                    lon = float(s['X'])

                if lat and lon:
                    points.append(Point(lon, lat))

                    # Use Zr/Nb ratio for coloring if available
                    try:
                        zr = float(s.get('Zr_ppm', 0))
                        nb = float(s.get('Nb_ppm', 1))
                        if zr > 0 and nb > 0:
                            data.append(zr/nb)
                        else:
                            data.append(1.0)
                    except:
                        data.append(1.0)
            except:
                continue

        if not points:
            ax.text(0.5, 0.5, "No coordinate data available\nAdd Latitude/Longitude to samples",
                   transform=ax.transAxes, ha='center', va='center', fontsize=14)
            canvas = FigureCanvasTkAgg(fig, master=map_frame)
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            canvas.draw()
            return

        # Create GeoDataFrame
        gdf = gpd.GeoDataFrame({'ZrNb_ratio': data, 'geometry': points}, crs='EPSG:4326')

        # Reproject to Web Mercator for basemaps
        gdf_web = gdf.to_crs(epsg=3857)

        # Plot
        ax = gdf_web.plot(column='ZrNb_ratio',
                         cmap='viridis',
                         markersize=marker_size,
                         alpha=0.7,
                         edgecolor='black',
                         linewidth=0.5,
                         legend=True,
                         ax=ax,
                         legend_kwds={'label': 'Zr/Nb Ratio', 'shrink': 0.8})

        # Add basemap
        if basemap != 'None':
            try:
                if basemap == 'Street':
                    ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)
                elif basemap == 'Satellite':
                    ctx.add_basemap(ax, source=ctx.providers.Esri.WorldImagery)
                elif basemap == 'Terrain':
                    ctx.add_basemap(ax, source=ctx.providers.Stamen.Terrain)
            except Exception as e:
                print(f"Basemap error: {e}")
                ax.set_title("Archaeological Sites (Basemap unavailable)")

        # Add labels
        ax.set_title('Archaeological Site Distribution', fontsize=14, fontweight='bold')
        ax.set_xlabel('Easting (m)')
        ax.set_ylabel('Northing (m)')

        # Add grid
        ax.grid(True, alpha=0.3, linestyle='--')

        # Create canvas
        canvas = FigureCanvasTkAgg(fig, master=map_frame)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        canvas.draw()

    # Initial plot
    plot_map()

# Expose plot types
PLOT_TYPES = {
    "Geopandas Site Map": plot_geopandas
}
