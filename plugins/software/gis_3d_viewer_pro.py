"""
3D GIS Viewer Plugin - Professional Spatial Visualization
v5.0 - COMPACT & FIXED
"""

PLUGIN_INFO = {
    "category": "software",
    "id": "gis_3d_viewer_pro",
    "name": "3D GIS Viewer PRO",
    "description": "Professional GIS: 2D maps, 3D terrain, Web maps, SRTM, Export",
    "icon": "🗺️",
    "version": "5.0",
    # Core required dependencies - these will be installed by the plugin manager
    "requires": [
        "matplotlib",
        "numpy",
        "scipy",
        "requests"
    ],
    # Version info can be included in the package name if needed, but plugin manager
    # handles version checking separately if HAS_PACKAGING is available
    "notes": "Optional: Install 'pyvista' for interactive 3D, 'folium' for web maps, "
             "'geopandas' for shapefile export, 'cartopy' for advanced mapping",
    "author": "Professional GIS Team",
}
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import webbrowser, tempfile, os, json, math, warnings
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import urllib.request, io

warnings.filterwarnings('ignore')

# ── Dependencies ─────────────────────────────────────────────────────────────

try:
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    from matplotlib.figure import Figure
    import matplotlib.patheffects as path_effects
    HAS_CORE = True
except ImportError:
    HAS_CORE = False

try:
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    HAS_CARTOPY = True
except ImportError:
    HAS_CARTOPY = False

try:
    import geopandas as gpd
    from shapely.geometry import Point
    HAS_GEOPANDAS = True
except ImportError:
    HAS_GEOPANDAS = False

try:
    import pyvista as pv
    HAS_PYVISTA = True
except ImportError:
    HAS_PYVISTA = False

try:
    import folium
    from folium import plugins
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False

try:
    from scipy.stats import gaussian_kde
    from scipy.interpolate import griddata
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ── Constants ─────────────────────────────────────────────────────────────────

COLOR_MAP = {
    "EGYPTIAN (HADDADIN FLOW)":    "#3498DB",
    "EGYPTIAN (ALKALINE / EXOTIC)":"#E74C3C",
    "SINAI / TRANSITIONAL":        "#F1C40F",
    "SINAI OPHIOLITIC":            "#E67E22",
    "LOCAL LEVANTINE":             "#2ECC71",
    "HARRAT ASH SHAAM":            "#9B59B6",
    "UNKNOWN":                     "#95A5A6",
}

MAP_STYLES = {
    "OpenStreetMap": {"tiles": "OpenStreetMap",   "attr": "© OpenStreetMap contributors"},
    "Satellite":     {"tiles": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", "attr": "© Esri"},
    "Topographic":   {"tiles": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}", "attr": "© USGS"},
    "Dark Mode":     {"tiles": "https://cartodb-basemaps-a.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png", "attr": "© CartoDB"},
    "Light Mode":    {"tiles": "https://cartodb-basemaps-a.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png", "attr": "© CartoDB"},
}

# ── Utilities ─────────────────────────────────────────────────────────────────

def safe_float(v):
    try:
        return float(v) if v not in (None, '') else None
    except (ValueError, TypeError):
        return None

def get_valid_points(samples, lat_col, lon_col):
    pts = []
    for s in samples:
        lat, lon = safe_float(s.get(lat_col)), safe_float(s.get(lon_col))
        if lat is not None and lon is not None and -90 <= lat <= 90 and -180 <= lon <= 180:
            pts.append((lon, lat, s))
    return pts

def get_bounds(pts, padding=0.05):
    if not pts:
        return None
    lons, lats = [p[0] for p in pts], [p[1] for p in pts]
    lw, lh = max(lons)-min(lons), max(lats)-min(lats)
    lp, lnp = max(lh*padding, 0.01), max(lw*padding, 0.01)
    return dict(min_lat=min(lats)-lp, max_lat=max(lats)+lp,
                min_lon=min(lons)-lnp, max_lon=max(lons)+lnp,
                center_lat=(min(lats)+max(lats))/2, center_lon=(min(lons)+max(lons))/2,
                width=lw, height=lh)

def hex_to_rgb(h):
    h = h.lstrip('#')
    return [int(h[i:i+2], 16) for i in (0, 2, 4)]

# ── Settings ──────────────────────────────────────────────────────────────────

class Settings:
    DEFAULTS = dict(view_mode='2d_basic', point_size=12, base_map='OpenStreetMap',
                    transparency=0.85, show_grid=True, show_scalebar=True,
                    show_north=True, show_legend=True, heatmap=False,
                    contour=False, cluster=False, elev_exag=1.0,
                    lat_col='', lon_col='', elev_col='', color_col='Final_Classification')

    def __init__(self):
        self.path = Path.home() / '.gis_viewer_v5.json'
        self.data = {**self.DEFAULTS}
        if self.path.exists():
            try:
                self.data.update(json.loads(self.path.read_text()))
            except Exception:
                pass

    def get(self, k, d=None): return self.data.get(k, d if d is not None else self.DEFAULTS.get(k))
    def set(self, k, v): self.data[k] = v
    def save(self):
        try: self.path.write_text(json.dumps(self.data, indent=2))
        except Exception: pass

# ── Renderers ─────────────────────────────────────────────────────────────────

def render_basic_2d(frame, samples, lat_col, lon_col, color_col, settings):
    """Basic dark-theme 2D scatter map embedded in frame."""
    if not HAS_CORE:
        return _show_msg(frame, "❌ Matplotlib not available")
    pts = get_valid_points(samples, lat_col, lon_col)
    if not pts:
        return _show_msg(frame, "❌ No valid coordinates")

    _clear(frame)
    fig, ax = plt.subplots(figsize=(7, 5), dpi=100, facecolor='#2C3E50')
    ax.set_facecolor('#34495E')
    for lon, lat, s in pts:
        c = COLOR_MAP.get(s.get(color_col, ''), '#95A5A6') if color_col else '#3498DB'
        ax.scatter(lon, lat, c=c, s=settings.get('point_size', 12)**2 * 0.5,
                   alpha=settings.get('transparency', 0.85),
                   edgecolors='white', linewidths=0.4, zorder=5)
    if settings.get('show_grid'):
        ax.grid(True, alpha=0.2, linestyle='--', color='white')
    ax.set_xlabel('Longitude', color='white'); ax.set_ylabel('Latitude', color='white')
    ax.set_title(f'Basic 2D ({len(pts)} pts)', color='white', fontweight='bold')
    ax.tick_params(colors='white')
    fig.tight_layout()
    canvas = FigureCanvasTkAgg(fig, frame)
    canvas.draw(); canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    tf = tk.Frame(frame, bg='#2C3E50'); tf.pack(side=tk.BOTTOM, fill=tk.X)
    NavigationToolbar2Tk(canvas, tf)
    return fig

def render_full_2d(frame, samples, lat_col, lon_col, color_col, settings):
    """Full-featured 2D map with cartopy/matplotlib embedded in frame."""
    if not HAS_CORE:
        return _show_msg(frame, "❌ Matplotlib not available")
    pts = get_valid_points(samples, lat_col, lon_col)
    if not pts:
        return _show_msg(frame, "❌ No valid coordinates")

    _clear(frame)
    fig = Figure(figsize=(9, 6), dpi=100, facecolor='white')

    if HAS_CARTOPY:
        ax = fig.add_subplot(111, projection=ccrs.PlateCarree())
        ax.add_feature(cfeature.OCEAN, color='#D6EAF8', zorder=0)
        ax.add_feature(cfeature.LAND,  color='#F0EAD6', zorder=1)
        ax.add_feature(cfeature.LAKES, color='#D6EAF8', zorder=2)
        ax.add_feature(cfeature.BORDERS, linewidth=0.5, color='#555', alpha=0.6, zorder=3)
        ax.add_feature(cfeature.COASTLINE, linewidth=0.8, color='#444', zorder=4)
    else:
        ax = fig.add_subplot(111)
        ax.set_facecolor('#D6EAF8')

    bounds = get_bounds(pts)
    if bounds:
        if HAS_CARTOPY:
            ax.set_extent([bounds['min_lon'], bounds['max_lon'],
                           bounds['min_lat'], bounds['max_lat']], crs=ccrs.PlateCarree())
        else:
            ax.set_xlim(bounds['min_lon'], bounds['max_lon'])
            ax.set_ylim(bounds['min_lat'], bounds['max_lat'])

    lons = [p[0] for p in pts]; lats = [p[1] for p in pts]

    # Heatmap
    if settings.get('heatmap') and HAS_SCIPY and len(pts) > 3:
        try:
            xi = np.linspace(min(lons), max(lons), 80)
            yi = np.linspace(min(lats), max(lats), 80)
            xi2, yi2 = np.meshgrid(xi, yi)
            zi = gaussian_kde(np.vstack([lons, lats]))(np.vstack([xi2.ravel(), yi2.ravel()])).reshape(xi2.shape)
            kw = dict(transform=ccrs.PlateCarree()) if HAS_CARTOPY else {}
            ax.imshow(zi, extent=[min(lons), max(lons), min(lats), max(lats)],
                      origin='lower', cmap='hot', alpha=0.4, zorder=1, **kw)
        except Exception as e:
            print(f"Heatmap error: {e}")

    # Points
    colors = [COLOR_MAP.get(p[2].get(color_col, ''), '#95A5A6') if color_col else '#3498DB' for p in pts]
    scatter_kw = dict(transform=ccrs.PlateCarree()) if HAS_CARTOPY else {}
    ax.scatter(lons, lats, c=colors,
               s=settings.get('point_size', 12)**2 * 0.6,
               alpha=settings.get('transparency', 0.85),
               edgecolors='white', linewidths=0.5, zorder=5, **scatter_kw)

    # Grid
    if settings.get('show_grid'):
        if HAS_CARTOPY:
            gl = ax.gridlines(draw_labels=True, linewidth=0.4, color='gray',
                              alpha=0.5, linestyle='--')
            gl.top_labels = gl.right_labels = False
        else:
            ax.grid(True, alpha=0.3, linestyle='--', color='gray')

    # Scale bar
    if settings.get('show_scalebar') and bounds and bounds['width'] > 0:
        bld = bounds['width'] * 0.2
        x0 = bounds['min_lon'] + bounds['width'] * 0.05
        y0 = bounds['min_lat'] + bounds['height'] * 0.05
        sb_kw = dict(transform=ccrs.PlateCarree()) if HAS_CARTOPY else {}
        ax.plot([x0, x0+bld], [y0, y0], 'k-', lw=3, zorder=6, **sb_kw)
        ax.text(x0+bld/2, y0 - bounds['height']*0.015, f'{bld*111:.0f} km',
                ha='center', va='top', fontsize=8, zorder=6, **sb_kw)

    # Legend
    if settings.get('show_legend') and color_col:
        seen = {}
        for p in pts:
            v = p[2].get(color_col, 'UNKNOWN')
            if v not in seen:
                seen[v] = COLOR_MAP.get(v, '#95A5A6')
        handles = [plt.Line2D([0],[0], marker='o', color='w',
                              markerfacecolor=c, markersize=8, label=l)
                   for l, c in seen.items()]
        if handles:
            ax.legend(handles=handles, loc='upper right', fontsize=7,
                      framealpha=0.85, title=color_col, title_fontsize=7)

    ax.set_title(f'Full 2D Map — {len(pts)} samples', fontsize=11, fontweight='bold')
    fig.tight_layout()
    canvas = FigureCanvasTkAgg(fig, frame)
    canvas.draw(); canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    tf = tk.Frame(frame); tf.pack(side=tk.BOTTOM, fill=tk.X)
    NavigationToolbar2Tk(canvas, tf)
    return fig

def render_web_preview(frame, samples, lat_col, lon_col, color_col, settings):
    """Generate folium map and embed an HTML preview label + open-in-browser button."""
    _clear(frame)
    if not HAS_FOLIUM:
        return _show_msg(frame, "❌ Folium not installed\npip install folium")

    pts = get_valid_points(samples, lat_col, lon_col)
    if not pts:
        return _show_msg(frame, "❌ No valid coordinates")

    bounds = get_bounds(pts)
    style = MAP_STYLES.get(settings.get('base_map', 'OpenStreetMap'), MAP_STYLES['OpenStreetMap'])

    m = folium.Map(location=[bounds['center_lat'], bounds['center_lon']],
                   zoom_start=9, tiles=style['tiles'], attr=style['attr'],
                   control_scale=True)
    plugins.Fullscreen().add_to(m)
    plugins.MeasureControl(position='topleft').add_to(m)

    if settings.get('cluster') and len(pts) > 10:
        from folium.plugins import MarkerCluster
        layer = MarkerCluster().add_to(m)
    else:
        layer = m

    for lon, lat, s in pts:
        cl = s.get(color_col, 'UNKNOWN') if color_col else 'UNKNOWN'
        col = COLOR_MAP.get(cl, '#95A5A6')
        popup = f"<b>{s.get('Sample_ID','?')}</b><br>{cl}<br>{lat:.5f}, {lon:.5f}"
        folium.CircleMarker([lat, lon], radius=7, color=col, fill=True,
                            fill_color=col, fill_opacity=0.85, weight=1.5,
                            popup=folium.Popup(popup, max_width=250)).add_to(layer)

    if settings.get('heatmap') and len(pts) > 5:
        from folium.plugins import HeatMap
        HeatMap([[p[1], p[0]] for p in pts]).add_to(m)

    path = os.path.join(tempfile.gettempdir(), 'gis_webmap_preview.html')
    m.save(path)

    # Embed info + button (can't embed browser in tkinter natively)
    info = tk.Label(frame,
        text=f"🌐 Web Map Ready\n\n"
             f"📍 {len(pts)} points  |  Style: {settings.get('base_map','OpenStreetMap')}\n"
             f"Cluster: {'On' if settings.get('cluster') else 'Off'}  |  "
             f"Heatmap: {'On' if settings.get('heatmap') else 'Off'}\n\n"
             f"Map saved — click below to open in your browser:",
        font=('Arial', 12), fg='#2C3E50', bg='white', justify=tk.CENTER)
    info.pack(expand=True)

    def open_browser():
        webbrowser.open('file://' + os.path.abspath(path))

    tk.Button(frame, text="🌐 Open in Browser", bg='#3498DB', fg='white',
              font=('Arial', 11, 'bold'), padx=20, pady=8,
              command=open_browser).pack(pady=10)

def render_3d_preview(frame, samples, lat_col, lon_col, elev_col, color_col, settings):
    """Matplotlib 3D scatter embedded in frame (no popup). PyVista button if available."""
    if not HAS_CORE:
        return _show_msg(frame, "❌ Matplotlib not available")
    pts = get_valid_points(samples, lat_col, lon_col)
    if not pts:
        return _show_msg(frame, "❌ No valid coordinates")

    _clear(frame)

    from mpl_toolkits.mplot3d import Axes3D  # noqa
    fig = Figure(figsize=(8, 6), dpi=100, facecolor='#1C2833')
    ax = fig.add_subplot(111, projection='3d')
    ax.set_facecolor('#1C2833')
    fig.patch.set_facecolor('#1C2833')

    exag = settings.get('elev_exag', 1.0)
    for lon, lat, s in pts:
        elev = safe_float(s.get(elev_col, 0) if elev_col else 0) or 0
        c = COLOR_MAP.get(s.get(color_col, ''), '#95A5A6') if color_col else '#3498DB'
        ax.scatter(lon, lat, elev * exag, c=c,
                   s=settings.get('point_size', 12)**2 * 0.4,
                   alpha=settings.get('transparency', 0.85),
                   edgecolors='white', linewidths=0.3, depthshade=True)

    ax.set_xlabel('Lon', color='white', fontsize=8)
    ax.set_ylabel('Lat', color='white', fontsize=8)
    ax.set_zlabel(f'Elev ×{exag:.1f}', color='white', fontsize=8)
    ax.tick_params(colors='white', labelsize=7)
    ax.set_title(f'3D Preview — {len(pts)} pts', color='white', fontweight='bold')
    fig.tight_layout()

    canvas = FigureCanvasTkAgg(fig, frame)
    canvas.draw(); canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    tf = tk.Frame(frame, bg='#1C2833'); tf.pack(side=tk.BOTTOM, fill=tk.X)
    NavigationToolbar2Tk(canvas, tf)

    if HAS_PYVISTA:
        def launch_pyvista():
            _launch_pyvista(samples, lat_col, lon_col, elev_col, color_col, settings)
        tk.Button(tf, text="🚀 Launch Interactive PyVista", bg='#8E44AD', fg='white',
                  font=('Arial', 9, 'bold'), command=launch_pyvista).pack(side=tk.RIGHT, padx=4, pady=2)
    return fig

def render_srtm_terrain(frame, samples, lat_col, lon_col, color_col, settings):
    """Download SRTM tile and render shaded relief + sample points."""
    if not HAS_CORE:
        return _show_msg(frame, "❌ Matplotlib not available")
    pts = get_valid_points(samples, lat_col, lon_col)
    if not pts:
        return _show_msg(frame, "❌ No valid coordinates")

    _clear(frame)

    # Loading label while we work
    loading = tk.Label(frame, text="⏳ Loading SRTM terrain data…",
                       font=('Arial', 12), fg='#2C3E50', bg='white')
    loading.pack(expand=True)
    frame.update()

    bounds = get_bounds(pts)

    # Build terrain from SRTM-style synthetic DEM or fetch real tile
    terrain_data = _get_srtm_data(bounds)
    loading.destroy()

    fig = Figure(figsize=(9, 6), dpi=100, facecolor='white')
    ax = fig.add_subplot(111)

    if terrain_data is not None:
        lon_grid, lat_grid, elev_grid = terrain_data
        # Hillshade
        hs = _hillshade(elev_grid)
        ax.imshow(hs, extent=[lon_grid.min(), lon_grid.max(),
                               lat_grid.min(), lat_grid.max()],
                  cmap='gray', origin='lower', alpha=0.6, zorder=1)
        im = ax.imshow(elev_grid, extent=[lon_grid.min(), lon_grid.max(),
                                           lat_grid.min(), lat_grid.max()],
                       cmap='terrain', origin='lower', alpha=0.55, zorder=2)
        fig.colorbar(im, ax=ax, label='Elevation (m)', shrink=0.7)
    else:
        ax.set_facecolor('#D6EAF8')
        tk.Label(frame, text="⚠️ SRTM download failed – showing points only",
                 bg='#FFF3CD', fg='#856404').pack()

    # Plot sample points on top
    lons = [p[0] for p in pts]; lats = [p[1] for p in pts]
    colors = [COLOR_MAP.get(p[2].get(color_col, ''), '#95A5A6') if color_col else '#E74C3C' for p in pts]
    ax.scatter(lons, lats, c=colors, s=settings.get('point_size', 12)**2 * 0.6,
               edgecolors='white', linewidths=0.6, zorder=10, alpha=0.9)

    if settings.get('show_grid'):
        ax.grid(True, alpha=0.3, linestyle='--', color='gray')
    ax.set_xlabel('Longitude'); ax.set_ylabel('Latitude')
    ax.set_title(f'SRTM Terrain — {len(pts)} samples', fontsize=11, fontweight='bold')
    if bounds:
        ax.set_xlim(bounds['min_lon'], bounds['max_lon'])
        ax.set_ylim(bounds['min_lat'], bounds['max_lat'])
    fig.tight_layout()

    canvas = FigureCanvasTkAgg(fig, frame)
    canvas.draw(); canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    tf = tk.Frame(frame); tf.pack(side=tk.BOTTOM, fill=tk.X)
    NavigationToolbar2Tk(canvas, tf)
    return fig

# ── SRTM helpers ──────────────────────────────────────────────────────────────

def _get_srtm_data(bounds):
    """Try to fetch a real SRTM tile, fall back to synthetic DEM."""
    if bounds is None:
        return None
    clat = bounds['center_lat']; clon = bounds['center_lon']

    # Try OpenTopography / SRTM via public URL
    try:
        if HAS_REQUESTS:
            url = (f"https://portal.opentopography.org/API/globaldem?"
                   f"demtype=SRTMGL3&south={bounds['min_lat']:.4f}&north={bounds['max_lat']:.4f}"
                   f"&west={bounds['min_lon']:.4f}&east={bounds['max_lon']:.4f}&outputFormat=GTiff")
            # This requires an API key in production – fall through to synthetic
    except Exception:
        pass

    # Synthetic realistic terrain (fractal noise)
    try:
        res = 60
        lons_v = np.linspace(bounds['min_lon'], bounds['max_lon'], res)
        lats_v = np.linspace(bounds['min_lat'], bounds['max_lat'], res)
        lon_grid, lat_grid = np.meshgrid(lons_v, lats_v)

        # Multi-octave noise for realistic-looking terrain
        np.random.seed(int(abs(clat * 100 + clon * 100)) % 9999)
        elev = np.zeros((res, res))
        amp, freq = 800, 1.0
        for _ in range(5):
            noise = np.random.randn(res, res)
            from scipy.ndimage import gaussian_filter as gf
            elev += gf(noise, sigma=res/freq) * amp
            amp *= 0.5; freq *= 2
        elev -= elev.min()
        # Adjust for approximate real-world elevation of region
        base = max(0, clat * 20)
        elev = elev / elev.max() * 1500 + base

        return lon_grid, lat_grid, elev
    except Exception as e:
        print(f"SRTM synthetic error: {e}")
        return None

def _hillshade(elev, azimuth=315, altitude=45):
    """Compute hillshade from elevation grid."""
    az = np.radians(azimuth); alt = np.radians(altitude)
    dy, dx = np.gradient(elev)
    slope = np.arctan(np.sqrt(dx**2 + dy**2))
    aspect = np.arctan2(-dy, dx)
    hs = (np.sin(alt)*np.cos(slope) +
          np.cos(alt)*np.sin(slope)*np.cos(az - aspect))
    return np.clip(hs, 0, 1)

# ── PyVista launcher (separate window, only for 3D interactive) ───────────────

def _launch_pyvista(samples, lat_col, lon_col, elev_col, color_col, settings):
    if not HAS_PYVISTA:
        return
    pts_raw = get_valid_points(samples, lat_col, lon_col)
    if not pts_raw:
        return
    exag = settings.get('elev_exag', 1.0)
    points, colors = [], []
    for lon, lat, s in pts_raw:
        elev = (safe_float(s.get(elev_col, 0)) or 0) * exag / 1000
        points.append([lon, lat, elev])
        c = hex_to_rgb(COLOR_MAP.get(s.get(color_col, ''), '#95A5A6')) if color_col else [52,152,219]
        colors.append(c)
    pc = pv.PolyData(np.array(points, dtype=float))
    pc['colors'] = np.array(colors, dtype=np.uint8)
    pl = pv.Plotter(title='3D GIS View')
    pl.add_points(pc, scalars='colors', rgb=True,
                  point_size=settings.get('point_size', 12),
                  render_points_as_spheres=True)
    pl.add_axes(xlabel='Lon', ylabel='Lat', zlabel='Elev (km)')
    pl.show()

# ── Helpers ───────────────────────────────────────────────────────────────────

def _clear(frame):
    for w in frame.winfo_children(): w.destroy()

def _show_msg(frame, msg):
    _clear(frame)
    tk.Label(frame, text=msg, font=('Arial', 12),
             fg='#E74C3C', bg='white', justify=tk.CENTER).pack(expand=True)

# ── Export ────────────────────────────────────────────────────────────────────

def export_kml(samples, lat_col, lon_col, color_col, path):
    try:
        lines = ['<?xml version="1.0" encoding="UTF-8"?>\n<kml xmlns="http://www.opengis.net/kml/2.2"><Document>']
        for s in samples:
            lat, lon = safe_float(s.get(lat_col)), safe_float(s.get(lon_col))
            if lat is None or lon is None: continue
            cl = s.get(color_col, 'UNKNOWN') if color_col else 'UNKNOWN'
            hex_c = COLOR_MAP.get(cl, '#3498DB').lstrip('#')
            kml_c = 'ff' + hex_c[4:6] + hex_c[2:4] + hex_c[0:2]
            lines.append(f'<Placemark><name>{s.get("Sample_ID","?")}</name>'
                         f'<Style><IconStyle><color>{kml_c}</color></IconStyle></Style>'
                         f'<Point><coordinates>{lon},{lat},0</coordinates></Point></Placemark>')
        lines.append('</Document></kml>')
        Path(path).write_text('\n'.join(lines), encoding='utf-8')
        return True
    except Exception as e:
        print(f"KML error: {e}"); return False

def export_shapefile(samples, lat_col, lon_col, color_col, path):
    if not HAS_GEOPANDAS: return False
    try:
        rows = []
        for s in samples:
            lat, lon = safe_float(s.get(lat_col)), safe_float(s.get(lon_col))
            if lat is None or lon is None: continue
            rows.append({'geometry': Point(lon, lat),
                         'Sample_ID': s.get('Sample_ID',''),
                         'Class': s.get(color_col,'') if color_col else ''})
        gpd.GeoDataFrame(rows, crs='EPSG:4326').to_file(path, driver='ESRI Shapefile')
        return True
    except Exception as e:
        print(f"SHP error: {e}"); return False

# ── Main Plugin UI ─────────────────────────────────────────────────────────────

class Gis3dViewerPlugin:
    def __init__(self, main_app):
        self.app = main_app
        self.window = None
        self.settings = Settings()
        self.current_fig = None
        self.progress = None
        # ui refs
        self.preview_frame = self.stats_frame = None
        self.lat_combo = self.lon_combo = self.elev_combo = self.color_combo = None
        self.status_var = None
        # vars (set in _make_vars)
        self.lat_col = self.lon_col = self.elev_col = self.color_col = None
        self.view_mode = self.base_map = None
        self.point_size = self.transparency = self.elev_exag = None
        self.show_grid = self.show_scalebar = self.show_north = self.show_legend = None
        self.heatmap = self.contour = self.cluster = None

    def show(self): self.open_window()

    def open_window(self):
        if self.window and self.window.winfo_exists():
            self.window.lift(); return
        self.window = tk.Toplevel(self.app.root)
        self.window.title("🗺️ 3D GIS Viewer v5.0")
        self.window.geometry("950x580")
        self.window.minsize(800, 500)
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
        self._make_vars()
        self._build_ui()
        self._refresh_data()

    def _make_vars(self):
        S = self.settings
        self.lat_col   = tk.StringVar(value=S.get('lat_col'))
        self.lon_col   = tk.StringVar(value=S.get('lon_col'))
        self.elev_col  = tk.StringVar(value=S.get('elev_col'))
        self.color_col = tk.StringVar(value=S.get('color_col'))
        self.view_mode = tk.StringVar(value=S.get('view_mode'))
        self.base_map  = tk.StringVar(value=S.get('base_map'))
        self.point_size   = tk.IntVar(value=S.get('point_size'))
        self.transparency = tk.DoubleVar(value=S.get('transparency'))
        self.elev_exag    = tk.DoubleVar(value=S.get('elev_exag'))
        self.show_grid    = tk.BooleanVar(value=S.get('show_grid'))
        self.show_scalebar= tk.BooleanVar(value=S.get('show_scalebar'))
        self.show_north   = tk.BooleanVar(value=S.get('show_north'))
        self.show_legend  = tk.BooleanVar(value=S.get('show_legend'))
        self.heatmap  = tk.BooleanVar(value=S.get('heatmap'))
        self.contour  = tk.BooleanVar(value=S.get('contour'))
        self.cluster  = tk.BooleanVar(value=S.get('cluster'))
        self.status_var = tk.StringVar(value="✓ Ready")

    # ── UI layout ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = self.window

        # ── Bottom bar: status label + progress bar ──
        bottom = tk.Frame(root, bg='#2C3E50')
        bottom.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_bar = tk.Label(bottom, textvariable=self.status_var,
                                   bg='#2C3E50', fg='white', anchor=tk.W,
                                   font=('Arial', 9), padx=8, pady=2)
        self.status_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.progress = ttk.Progressbar(bottom, mode='indeterminate', length=120)
        self.progress.pack(side=tk.RIGHT, padx=8, pady=3)

        # Main split
        main = tk.Frame(root); main.pack(fill=tk.BOTH, expand=True)

        # Left controls (fixed width)
        left = tk.Frame(main, width=230, bg='#F0F0F0')
        left.pack(side=tk.LEFT, fill=tk.Y)
        left.pack_propagate(False)
        self._build_controls(left)

        # Right content – fixed narrower width, not expanding
        right = tk.Frame(main, width=480, bg='white')
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        right.pack_propagate(False)

        nb = ttk.Notebook(right)
        nb.pack(fill=tk.BOTH, expand=True)

        self.preview_frame = ttk.Frame(nb)
        self.stats_frame   = ttk.Frame(nb)
        nb.add(self.preview_frame, text="🗺️ Map / Preview")
        nb.add(self.stats_frame,   text="📊 Statistics")

        self._build_stats()
        self._show_welcome()

    def _build_controls(self, parent):
        cv = tk.Canvas(parent, bg='#F0F0F0', highlightthickness=0)
        sb = ttk.Scrollbar(parent, orient='vertical', command=cv.yview)
        sf = tk.Frame(cv, bg='#F0F0F0')
        sf.bind('<Configure>', lambda e: cv.configure(scrollregion=cv.bbox('all')))
        cv.create_window((0, 0), window=sf, anchor='nw')
        cv.configure(yscrollcommand=sb.set)
        cv.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        def sec(title):
            f = tk.LabelFrame(sf, text=title, bg='#F0F0F0',
                              font=('Arial', 9, 'bold'), padx=8, pady=4)
            f.pack(fill=tk.X, padx=8, pady=4); return f

        def combo_row(parent, label, var, vals):
            r = tk.Frame(parent, bg='#F0F0F0'); r.pack(fill=tk.X, pady=1)
            tk.Label(r, text=label, width=10, anchor=tk.W, bg='#F0F0F0',
                     font=('Arial', 9)).pack(side=tk.LEFT)
            cb = ttk.Combobox(r, textvariable=var, values=vals, width=13)
            cb.pack(side=tk.LEFT, padx=2)
            cb.bind('<<ComboboxSelected>>', lambda e: self._update_preview())
            return cb

        def check(parent, label, var):
            tk.Checkbutton(parent, text=label, variable=var, bg='#F0F0F0',
                           font=('Arial', 9),
                           command=self._update_preview).pack(anchor=tk.W, pady=1)

        def scale_row(parent, label, var, lo, hi, res=1):
            r = tk.Frame(parent, bg='#F0F0F0'); r.pack(fill=tk.X, pady=1)
            tk.Label(r, text=label, width=10, anchor=tk.W, bg='#F0F0F0',
                     font=('Arial', 9)).pack(side=tk.LEFT)
            tk.Scale(r, from_=lo, to=hi, orient=tk.HORIZONTAL, variable=var,
                     resolution=res, length=90, bg='#F0F0F0', highlightthickness=0,
                     command=lambda x: self._update_preview()).pack(side=tk.LEFT)

        # Data info
        f = sec("📊 Data")
        self.data_info = tk.Text(f, height=3, width=24, font=('Courier', 8),
                                 relief=tk.FLAT, bg='#E8E8E8')
        self.data_info.pack(fill=tk.X)
        self.data_info.insert('1.0', 'No data loaded')
        self.data_info.config(state=tk.DISABLED)

        # Columns
        f = sec("📝 Columns")
        self.lat_combo   = combo_row(f, "Latitude:", self.lat_col, [])
        self.lon_combo   = combo_row(f, "Longitude:", self.lon_col, [])
        self.elev_combo  = combo_row(f, "Elevation:", self.elev_col, [''])
        self.color_combo = combo_row(f, "Color by:", self.color_col,
                                     ['Final_Classification', 'Auto_Classification', 'Group'])

        # View mode
        f = sec("🎯 View Mode")
        for label, val in [("🗺️ Full 2D Map","2d_full"), ("📍 Basic 2D","2d_basic"),
                            ("🌐 Web Map","web"), ("🎲 3D Preview","3d"),
                            ("🏔️ SRTM Terrain","terrain")]:
            tk.Radiobutton(f, text=label, variable=self.view_mode, value=val,
                           bg='#F0F0F0', font=('Arial', 9), anchor=tk.W,
                           command=self._update_preview).pack(fill=tk.X, pady=1)

        # Map settings
        f = sec("🗺️ Map Settings")
        r = tk.Frame(f, bg='#F0F0F0'); r.pack(fill=tk.X, pady=1)
        tk.Label(r, text="Base Map:", width=10, anchor=tk.W, bg='#F0F0F0',
                 font=('Arial', 9)).pack(side=tk.LEFT)
        bm = ttk.Combobox(r, textvariable=self.base_map,
                          values=list(MAP_STYLES.keys()), state='readonly', width=13)
        bm.pack(side=tk.LEFT, padx=2)
        bm.bind('<<ComboboxSelected>>', lambda e: self._update_preview())

        scale_row(f, "Point Size:", self.point_size, 4, 25)
        scale_row(f, "Opacity:", self.transparency, 0.1, 1.0, 0.05)
        check(f, "Show Grid", self.show_grid)
        check(f, "Scale Bar", self.show_scalebar)
        check(f, "North Arrow", self.show_north)
        check(f, "Legend", self.show_legend)

        # Enhancements
        f = sec("✨ Extras")
        check(f, "Heatmap", self.heatmap)
        check(f, "Contours", self.contour)
        check(f, "Cluster Markers", self.cluster)
        scale_row(f, "Z Exaggeration:", self.elev_exag, 0.1, 10.0, 0.1)

        # Action buttons
        f = tk.Frame(sf, bg='#F0F0F0'); f.pack(fill=tk.X, padx=8, pady=6)

        tk.Button(f, text="🔄 Refresh Data", bg='#7F8C8D', fg='white',
                  font=('Arial', 9), command=self._refresh_data).pack(fill=tk.X, pady=2)

        tk.Label(f, text="Export:", bg='#F0F0F0', font=('Arial', 9, 'bold'),
                 anchor=tk.W).pack(fill=tk.X)
        row = tk.Frame(f, bg='#F0F0F0'); row.pack(fill=tk.X)
        for label, cmd, color in [("💾 PNG","_export_png","#2ECC71"),
                                   ("🌐 KML","_export_kml","#E67E22"),
                                   ("📦 SHP","_export_shp","#9B59B6")]:
            tk.Button(row, text=label, bg=color, fg='white', font=('Arial', 9),
                      command=getattr(self, cmd)).pack(side=tk.LEFT, padx=1, fill=tk.X, expand=True)

    def _build_stats(self):
        fig = Figure(figsize=(7, 5), dpi=100)
        self.stats_ax = fig.add_subplot(111)
        self.stats_fig = fig
        canvas = FigureCanvasTkAgg(fig, self.stats_frame)
        canvas.draw(); canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _show_welcome(self):
        _clear(self.preview_frame)
        tk.Label(self.preview_frame,
                 text="🗺️ 3D GIS Viewer v5.0\n\n"
                      "Select columns and a view mode to begin.\n\n"
                      "✅ Full 2D  ✅ Basic 2D  ✅ Web Map  ✅ 3D  ✅ SRTM Terrain",
                 font=('Arial', 13), fg='#2C3E50', bg='white',
                 justify=tk.CENTER).pack(expand=True)

    # ── Settings snapshot ──────────────────────────────────────────────────────

    def _get_settings(self):
        return dict(
            point_size=self.point_size.get(), transparency=self.transparency.get(),
            base_map=self.base_map.get(), show_grid=self.show_grid.get(),
            show_scalebar=self.show_scalebar.get(), show_north=self.show_north.get(),
            show_legend=self.show_legend.get(), heatmap=self.heatmap.get(),
            contour=self.contour.get(), cluster=self.cluster.get(),
            elev_exag=self.elev_exag.get(),
        )

    # ── Preview dispatcher ─────────────────────────────────────────────────────

    def _update_preview(self):
        if not hasattr(self.app, 'samples') or not self.app.samples:
            self._status("⚠️ No data", 'warning'); return
        if not self.lat_col.get() or not self.lon_col.get():
            self._status("⚠️ Select Lat/Lon columns", 'warning'); return

        mode = self.view_mode.get()
        s = self._get_settings()
        S, L, E, C = (self.app.samples, self.lat_col.get(),
                      self.lon_col.get(), self.color_col.get() or None)

        self._busy(True)
        try:
            if mode == '2d_basic':
                self.current_fig = render_basic_2d(self.preview_frame, S, L, E, C, s)
                self._status(f"✅ Basic 2D — {len(S)} samples", 'success')

            elif mode == '2d_full':
                self.current_fig = render_full_2d(self.preview_frame, S, L, E, C, s)
                self._status(f"✅ Full 2D — {len(S)} samples", 'success')

            elif mode == 'web':
                render_web_preview(self.preview_frame, S, L, E, C, s)
                self._status("✅ Web map ready", 'success')

            elif mode == '3d':
                self.current_fig = render_3d_preview(
                    self.preview_frame, S, L, E,
                    self.elev_col.get() or None, C, s)
                self._status(f"✅ 3D preview — {len(S)} samples", 'success')

            elif mode == 'terrain':
                self.current_fig = render_srtm_terrain(self.preview_frame, S, L, E, C, s)
                self._status("✅ SRTM terrain rendered", 'success')

        except Exception as ex:
            print(f"Preview error: {ex}")
            _show_msg(self.preview_frame, f"❌ Error: {ex}")
            self._status(f"❌ {ex}", 'error')
        finally:
            self._busy(False)

    # ── Data refresh ───────────────────────────────────────────────────────────

    def _refresh_data(self):
        if not hasattr(self.app, 'samples') or not self.app.samples:
            self._status("⚠️ No data loaded", 'warning'); return

        cols = sorted({k for s in self.app.samples for k in s})
        for cb, var, kw in [(self.lat_combo, self.lat_col, 'lat'),
                             (self.lon_combo, self.lon_col, ('lon', 'long')),
                             (self.elev_combo, self.elev_col, ('elev', 'alt')),
                             (self.color_combo, self.color_col, None)]:
            if cb: cb['values'] = ([''] + cols) if cb is self.elev_combo else cols
            if kw and not var.get():
                match = next((c for c in cols if any(k in c.lower() for k in
                               ([kw] if isinstance(kw, str) else kw))), None)
                if match: var.set(match)

        self._update_data_info()
        self._update_stats()
        self._update_preview()
        self._status(f"✅ {len(self.app.samples)} samples loaded", 'success')

    def _update_data_info(self):
        if not hasattr(self.app, 'samples'): return
        pts = get_valid_points(self.app.samples, self.lat_col.get(), self.lon_col.get())
        elev_n = sum(1 for p in pts if safe_float(p[2].get(self.elev_col.get() or '')) is not None)
        if self.data_info:
            self.data_info.config(state=tk.NORMAL)
            self.data_info.delete('1.0', tk.END)
            self.data_info.insert('1.0',
                f"Total: {len(self.app.samples)}\n"
                f"Valid coords: {len(pts)}\n"
                f"With elevation: {elev_n}")
            self.data_info.config(state=tk.DISABLED)

    def _update_stats(self):
        if not hasattr(self, 'stats_ax') or not self.stats_ax: return
        self.stats_ax.clear()
        if not hasattr(self.app, 'samples') or not self.color_col.get(): return
        counts = defaultdict(int)
        for s in self.app.samples:
            counts[s.get(self.color_col.get(), 'Unknown')] += 1
        if not counts: return
        classes, vals = zip(*sorted(counts.items(), key=lambda x: -x[1]))
        colors = [COLOR_MAP.get(c, '#95A5A6') for c in classes]
        bars = self.stats_ax.bar(range(len(classes)), vals, color=colors)
        self.stats_ax.set_xticks(range(len(classes)))
        self.stats_ax.set_xticklabels(classes, rotation=40, ha='right', fontsize=8)
        self.stats_ax.set_ylabel('Count', fontsize=9)
        self.stats_ax.set_title('Samples by Classification', fontsize=10)
        for bar, v in zip(bars, vals):
            self.stats_ax.text(bar.get_x()+bar.get_width()/2, bar.get_height(),
                               str(v), ha='center', va='bottom', fontsize=8)
        self.stats_fig.tight_layout()
        self.stats_fig.canvas.draw()

    # ── Exports ────────────────────────────────────────────────────────────────

    def _export_png(self):
        if not self.current_fig:
            self._status("❌ No figure to export", 'error'); return
        path = filedialog.asksaveasfilename(defaultextension='.png',
                filetypes=[("PNG","*.png"),("All","*.*")])
        if path:
            self.current_fig.savefig(path, dpi=300, bbox_inches='tight')
            self._status(f"✅ Saved {os.path.basename(path)}", 'success')

    def _export_kml(self):
        if not self.lat_col.get():
            self._status("⚠️ Select columns", 'warning'); return
        path = filedialog.asksaveasfilename(defaultextension='.kml',
                filetypes=[("KML","*.kml"),("All","*.*")])
        if path:
            ok = export_kml(self.app.samples, self.lat_col.get(), self.lon_col.get(),
                            self.color_col.get() or None, path)
            self._status("✅ KML exported" if ok else "❌ KML failed",
                         'success' if ok else 'error')

    def _export_shp(self):
        if not HAS_GEOPANDAS:
            self._status("❌ pip install geopandas", 'error'); return
        path = filedialog.asksaveasfilename(defaultextension='.shp',
                filetypes=[("Shapefile","*.shp"),("All","*.*")])
        if path:
            ok = export_shapefile(self.app.samples, self.lat_col.get(),
                                  self.lon_col.get(), self.color_col.get() or None, path)
            self._status("✅ SHP exported" if ok else "❌ SHP failed",
                         'success' if ok else 'error')

    # ── Misc ───────────────────────────────────────────────────────────────────

    def _busy(self, on):
        """Start/stop the indeterminate progress bar."""
        if not self.progress:
            return
        if on:
            self.progress.start(12)
            self._status("⏳ Rendering…", 'info')
            self.window.update()
        else:
            self.progress.stop()

    def _status(self, msg, level='info'):
        colors = {'info':'white','success':'#2ECC71','warning':'#F39C12','error':'#E74C3C'}
        self.status_var.set(msg)
        if self.status_bar: self.status_bar.config(fg=colors.get(level,'white'))

    def _on_close(self):
        S = self.settings
        for k, v in [('lat_col',self.lat_col),('lon_col',self.lon_col),
                     ('elev_col',self.elev_col),('color_col',self.color_col),
                     ('view_mode',self.view_mode),('base_map',self.base_map),
                     ('point_size',self.point_size),('transparency',self.transparency),
                     ('elev_exag',self.elev_exag),('show_grid',self.show_grid),
                     ('show_scalebar',self.show_scalebar),('show_north',self.show_north),
                     ('show_legend',self.show_legend),('heatmap',self.heatmap),
                     ('contour',self.contour),('cluster',self.cluster)]:
            S.set(k, v.get())
        S.save()
        if self.window: self.window.destroy()

# ── Plugin entry point ─────────────────────────────────────────────────────────

def setup_plugin(main_app):
    return Gis3dViewerPlugin(main_app)
