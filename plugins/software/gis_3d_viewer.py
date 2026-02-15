"""
3D/GIS Viewer Plugin - Professional Spatial Visualization
LIVE PREVIEW: 2D maps, 3D scenes, SRTM terrain IN-PANEL
v3.0 - FINAL RELEASE
"""

PLUGIN_INFO = {
    "category": "software",
    "id": "gis_3d_viewer",
    "name": "3D GIS Viewer",
    "description": "LIVE preview: 2D maps, 3D scenes, SRTM terrain IN-PANEL",
    "icon": "🌍",
    "version": "3.0",
    "requires": ["matplotlib", "numpy"],
    "optional": ["pyvista", "folium", "geopandas", "shapely", "scipy", "requests", "pandas"],
    "author": "Sefy Levy & DeepSeek",
}

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import webbrowser
import tempfile
import os
import json
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# DEPENDENCY MANAGEMENT
# ============================================================================

try:
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    HAS_CORE = True
except ImportError:
    HAS_CORE = False

try:
    import folium
    from folium import plugins
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False

try:
    import geopandas as gpd
    from shapely.geometry import Point, box
    HAS_GEOPANDAS = True
except ImportError:
    HAS_GEOPANDAS = False

try:
    import pyvista as pv
    HAS_PYVISTA = True
except ImportError:
    HAS_PYVISTA = False

try:
    from scipy.interpolate import griddata
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


# ============================================================================
# UTILITIES
# ============================================================================

class SpatialUtils:
    """Coordinate validation, DMS conversion, bounding boxes"""

    @staticmethod
    def safe_float(value):
        if value is None or value == '':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def dms_to_decimal(dms_str):
        if not dms_str or not isinstance(dms_str, str):
            return None
        try:
            dms_str = dms_str.strip()
            direction = 1
            if dms_str.endswith(('N', 'S', 'E', 'W')):
                if dms_str[-1] in ('S', 'W'):
                    direction = -1
                dms_str = dms_str[:-1]
            dms_str = dms_str.replace('°', ' ').replace("'", ' ').replace('"', ' ')
            parts = dms_str.split()
            if len(parts) == 3:
                degrees = float(parts[0])
                minutes = float(parts[1])
                seconds = float(parts[2])
                return direction * (degrees + minutes/60 + seconds/3600)
            elif len(parts) == 2:
                degrees = float(parts[0])
                minutes = float(parts[1])
                return direction * (degrees + minutes/60)
            elif len(parts) == 1:
                return direction * float(parts[0])
        except:
            pass
        return None

    @staticmethod
    def validate_lat(lat):
        if lat is None:
            return False
        try:
            lat = float(lat)
            return -90 <= lat <= 90
        except:
            return False

    @staticmethod
    def validate_lon(lon):
        if lon is None:
            return False
        try:
            lon = float(lon)
            return -180 <= lon <= 180
        except:
            return False

    @staticmethod
    def get_bounds(samples, lat_col='Latitude', lon_col='Longitude'):
        lats = []
        lons = []
        for s in samples:
            lat = SpatialUtils.safe_float(s.get(lat_col))
            lon = SpatialUtils.safe_float(s.get(lon_col))
            if lat is not None and lon is not None:
                if SpatialUtils.validate_lat(lat) and SpatialUtils.validate_lon(lon):
                    lats.append(lat)
                    lons.append(lon)
        if not lats:
            return None
        return {
            'min_lat': min(lats), 'max_lat': max(lats),
            'min_lon': min(lons), 'max_lon': max(lons),
            'center_lat': (min(lats) + max(lats)) / 2,
            'center_lon': (min(lons) + max(lons)) / 2,
            'width': max(lons) - min(lons),
            'height': max(lats) - min(lats)
        }


class SettingsManager:
    """Persistent user settings"""

    def __init__(self, plugin_id):
        self.plugin_id = plugin_id
        self.settings_file = Path.home() / f'.basalt_{plugin_id}.json'
        self.settings = self.load()

    def load(self):
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            'view_mode': 'basic', 'point_size': 15, 'map_style': 'OpenStreetMap',
            'cluster_markers': False, 'show_axes': True, 'show_grid': False,
            'elevation_exaggeration': 1.0, 'color_by': 'classification',
        }

    def save(self):
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except:
            pass

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings[key] = value
        self.save()


# ============================================================================
# LIVE PREVIEW RENDERERS
# ============================================================================

class LivePreview:
    """Render visualizations directly to right panel"""

    @staticmethod
    def clear(frame):
        for widget in frame.winfo_children():
            widget.destroy()

    @staticmethod
    def show_welcome(frame):
        LivePreview.clear(frame)
        welcome = tk.Label(frame,
            text="🌍 3D GIS Viewer v3.0\n\n"
                 "1. Load data in main app\n"
                 "2. Select coordinate columns\n"
                 "3. Watch LIVE preview here!\n\n"
                 "✅ 2D Map: Renders here\n"
                 "✅ 3D Preview: Renders here\n"
                 "✅ SRTM Terrain: Renders here\n"
                 "🌐 Web Maps: Opens in browser",
            font=("Arial", 11),
            bg="white", fg="#2C3E50",
            justify=tk.CENTER)
        welcome.pack(expand=True)

    @staticmethod
    def render_2d(frame, samples, lat_col, lon_col, color_col=None, bounds=None):
        if not HAS_CORE:
            LivePreview.show_error(frame, "Matplotlib not available")
            return None

        LivePreview.clear(frame)

        valid_samples = []
        for s in samples:
            lat = SpatialUtils.safe_float(s.get(lat_col))
            lon = SpatialUtils.safe_float(s.get(lon_col))
            if lat is not None and lon is not None:
                if SpatialUtils.validate_lat(lat) and SpatialUtils.validate_lon(lon):
                    valid_samples.append((lon, lat, s))

        if not valid_samples:
            LivePreview.show_error(frame, "No valid coordinates")
            return None

        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(7, 5), dpi=100, facecolor='#2C3E50')
        ax.set_facecolor('#34495E')

        color_map = {
            "EGYPTIAN (HADDADIN FLOW)": "#3498DB",
            "EGYPTIAN (ALKALINE / EXOTIC)": "#E74C3C",
            "SINAI / TRANSITIONAL": "#F1C40F",
            "SINAI OPHIOLITIC": "#E67E22",
            "LOCAL LEVANTINE": "#2ECC71",
            "HARRAT ASH SHAAM": "#9B59B6",
        }

        for lon, lat, s in valid_samples:
            color = "#95A5A6"
            if color_col:
                val = s.get(color_col, 'UNKNOWN')
                color = color_map.get(val, "#95A5A6")
            ax.scatter(lon, lat, c=color, s=80, alpha=0.9,
                      edgecolors='white', linewidths=0.5, zorder=5)

        ax.set_xlabel('Longitude', color='white', fontweight='bold')
        ax.set_ylabel('Latitude', color='white', fontweight='bold')
        ax.set_title(f'2D Preview ({len(valid_samples)} points)',
                    color='white', fontweight='bold')
        ax.tick_params(colors='white')
        ax.grid(True, alpha=0.2, linestyle='--', color='white')

        if bounds:
            ax.set_xlim(bounds['min_lon'] - 0.1, bounds['max_lon'] + 0.1)
            ax.set_ylim(bounds['min_lat'] - 0.1, bounds['max_lat'] + 0.1)

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        toolbar_frame = tk.Frame(frame, bg='#2C3E50')
        toolbar_frame.pack(side=tk.BOTTOM, fill=tk.X)
        NavigationToolbar2Tk(canvas, toolbar_frame)

        return fig

    @staticmethod
    def render_3d_preview(frame, samples, lat_col, lon_col, elev_col,
                         color_col=None, point_size=10, exaggeration=1.0):
        if not HAS_PYVISTA:
            LivePreview.show_error(frame, "PyVista not installed - 3D preview unavailable")
            return

        LivePreview.clear(frame)

        info = tk.Label(frame,
                       text="🎲 3D Preview - Click 'LAUNCH FULLSCREEN' for interactive view",
                       bg="#2C3E50", fg="white", pady=5)
        info.pack(fill=tk.X)

        plot_frame = tk.Frame(frame, bg='black')
        plot_frame.pack(fill=tk.BOTH, expand=True)

        points = []
        colors = []

        color_map = {
            "EGYPTIAN (HADDADIN FLOW)": [52, 152, 219],
            "EGYPTIAN (ALKALINE / EXOTIC)": [231, 76, 60],
            "SINAI / TRANSITIONAL": [241, 196, 15],
            "SINAI OPHIOLITIC": [230, 126, 34],
            "LOCAL LEVANTINE": [46, 204, 113],
            "HARRAT ASH SHAAM": [155, 89, 182],
        }

        for s in samples[:100]:
            lat = SpatialUtils.safe_float(s.get(lat_col))
            lon = SpatialUtils.safe_float(s.get(lon_col))
            elev = SpatialUtils.safe_float(s.get(elev_col, 0))
            if lat is None or lon is None:
                continue
            if elev is None:
                elev = 0
            elev_scaled = elev * exaggeration / 1000
            points.append([lon, lat, elev_scaled])
            classification = s.get(color_col, 'UNKNOWN') if color_col else 'UNKNOWN'
            rgb = color_map.get(classification, [149, 165, 166])
            colors.append(rgb)

        if points:
            plotter = pv.Plotter(window_size=[600, 400], off_screen=True)
            plotter.set_background("#2C3E50")
            points_array = np.array(points)
            point_cloud = pv.PolyData(points_array)
            point_cloud['colors'] = np.array(colors, dtype=np.uint8)

            plotter.add_points(
                point_cloud, scalars='colors', rgb=True,
                point_size=point_size, render_points_as_spheres=True
            )

            temp_img = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            plotter.screenshot(temp_img.name)
            temp_img.close()

            from PIL import Image, ImageTk
            img = Image.open(temp_img.name)
            img = img.resize((600, 400), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)

            label = tk.Label(plot_frame, image=photo, bg='black')
            label.image = photo
            label.pack()

            os.unlink(temp_img.name)

    @staticmethod
    def render_terrain_preview(frame, samples, lat_col, lon_col, color_col=None,
                              exaggeration=1.0, status_callback=None):
        if not all([HAS_PYVISTA, HAS_SCIPY, HAS_REQUESTS, HAS_PANDAS]):
            missing = []
            if not HAS_PYVISTA: missing.append("pyvista")
            if not HAS_SCIPY: missing.append("scipy")
            if not HAS_REQUESTS: missing.append("requests")
            if not HAS_PANDAS: missing.append("pandas")
            LivePreview.show_error(frame, f"Missing: {', '.join(missing)}")
            return

        LivePreview.clear(frame)

        info = tk.Label(frame,
                       text="🏔️ SRTM Terrain Preview - Downloading elevation data...",
                       bg="#2C3E50", fg="white", pady=5)
        info.pack(fill=tk.X)

        plot_frame = tk.Frame(frame, bg='#2C3E50')
        plot_frame.pack(fill=tk.BOTH, expand=True)

        try:
            bounds = SpatialUtils.get_bounds(samples, lat_col, lon_col)
            if not bounds:
                LivePreview.show_error(frame, "Could not calculate bounds")
                return

            pad_lat = bounds['height'] * 0.1
            pad_lon = bounds['width'] * 0.1
            bounds['min_lat'] -= pad_lat
            bounds['max_lat'] += pad_lat
            bounds['min_lon'] -= pad_lon
            bounds['max_lon'] += pad_lon

            url = "https://portal.opentopography.org/API/globaldem"
            params = {
                'demtype': 'SRTMGL3',
                'south': bounds['min_lat'],
                'north': bounds['max_lat'],
                'west': bounds['min_lon'],
                'east': bounds['max_lon'],
                'outputFormat': 'CSV'
            }

            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 200:
                df = pd.read_csv(pd.io.common.StringIO(response.text))

                if 'elevation' in df.columns and 'latitude' in df.columns and 'longitude' in df.columns:
                    xi = np.linspace(bounds['min_lon'], bounds['max_lon'], 80)
                    yi = np.linspace(bounds['min_lat'], bounds['max_lat'], 60)
                    XI, YI = np.meshgrid(xi, yi)

                    points = df[['longitude', 'latitude']].values
                    values = df['elevation'].values * exaggeration / 1000
                    ZI = griddata(points, values, (XI, YI), method='cubic', fill_value=0)

                    plt.style.use('dark_background')
                    fig, ax = plt.subplots(figsize=(7, 5), dpi=100, facecolor='#2C3E50')
                    ax.set_facecolor('#34495E')

                    im = ax.imshow(ZI, extent=[bounds['min_lon'], bounds['max_lon'],
                                              bounds['min_lat'], bounds['max_lat']],
                                 origin='lower', cmap='terrain', alpha=0.8)

                    color_map = {
                        "EGYPTIAN (HADDADIN FLOW)": "#3498DB",
                        "EGYPTIAN (ALKALINE / EXOTIC)": "#E74C3C",
                        "SINAI / TRANSITIONAL": "#F1C40F",
                        "SINAI OPHIOLITIC": "#E67E22",
                        "LOCAL LEVANTINE": "#2ECC71",
                        "HARRAT ASH SHAAM": "#9B59B6",
                    }

                    for s in samples[:200]:
                        lat = SpatialUtils.safe_float(s.get(lat_col))
                        lon = SpatialUtils.safe_float(s.get(lon_col))
                        if lat is None or lon is None:
                            continue

                        color = "#95A5A6"
                        if color_col:
                            classification = s.get(color_col, 'UNKNOWN')
                            color = color_map.get(classification, "#95A5A6")

                        ax.scatter(lon, lat, c=color, s=30, alpha=0.9,
                                  edgecolors='white', linewidths=0.5, zorder=5)

                    ax.set_xlabel('Longitude', color='white', fontweight='bold')
                    ax.set_ylabel('Latitude', color='white', fontweight='bold')
                    ax.set_title(f'SRTM Terrain + Samples ({len(df)} elevation points)',
                               color='white', fontweight='bold')
                    ax.tick_params(colors='white')

                    plt.colorbar(im, ax=ax, label='Elevation (km)', shrink=0.8)
                    fig.tight_layout()

                    canvas = FigureCanvasTkAgg(fig, plot_frame)
                    canvas.draw()
                    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

                    if status_callback:
                        status_callback("✅ Terrain preview loaded", "success")
                else:
                    LivePreview.show_error(frame, "Invalid terrain data format")
            else:
                LivePreview.show_error(frame, f"Failed to download terrain: HTTP {response.status_code}")

        except Exception as e:
            LivePreview.show_error(frame, f"Terrain error: {str(e)[:50]}...")

    @staticmethod
    def show_error(frame, message):
        LivePreview.clear(frame)
        error = tk.Label(frame,
            text=f"❌ {message}",
            font=("Arial", 11),
            bg="white", fg="#E74C3C",
            justify=tk.CENTER)
        error.pack(expand=True)

    @staticmethod
    def show_info(frame, title, message):
        LivePreview.clear(frame)
        info = tk.Label(frame,
            text=f"{title}\n\n{message}",
            font=("Arial", 11),
            bg="white", fg="#2C3E50",
            justify=tk.CENTER)
        info.pack(expand=True)


# ============================================================================
# EXPORT RENDERERS (Fullscreen versions)
# ============================================================================

class Basic2DMap:
    @staticmethod
    def create(parent, samples, lat_col, lon_col, color_col=None, title=None):
        if not HAS_CORE:
            return None
        valid_samples = []
        for s in samples:
            lat = SpatialUtils.safe_float(s.get(lat_col))
            lon = SpatialUtils.safe_float(s.get(lon_col))
            if lat is not None and lon is not None:
                if SpatialUtils.validate_lat(lat) and SpatialUtils.validate_lon(lon):
                    valid_samples.append((lon, lat, s))
        if not valid_samples:
            return None
        fig, ax = plt.subplots(figsize=(10, 8), dpi=100)
        color_map = {
            "EGYPTIAN (HADDADIN FLOW)": "blue",
            "EGYPTIAN (ALKALINE / EXOTIC)": "red",
            "SINAI / TRANSITIONAL": "gold",
            "SINAI OPHIOLITIC": "orange",
            "LOCAL LEVANTINE": "green",
            "HARRAT ASH SHAAM": "purple",
        }
        for lon, lat, s in valid_samples:
            color = "gray"
            if color_col:
                val = s.get(color_col, 'UNKNOWN')
                color = color_map.get(val, "gray")
            ax.scatter(lon, lat, c=color, s=80, alpha=0.7,
                      edgecolors='black', linewidths=0.5, zorder=5)
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        ax.set_title(title or f'Sample Distribution ({len(valid_samples)} points)')
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.set_aspect(1.0 / np.cos(np.mean([s[1] for s in valid_samples]) * np.pi/180))
        fig.tight_layout()
        window = tk.Toplevel(parent)
        window.title("2D Map - Fullscreen")
        window.geometry("1000x800")
        canvas = FigureCanvasTkAgg(fig, window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        toolbar_frame = tk.Frame(window)
        toolbar_frame.pack(side=tk.BOTTOM, fill=tk.X)
        NavigationToolbar2Tk(canvas, toolbar_frame)
        return window


class WebMapGenerator:
    @staticmethod
    def create(samples, lat_col, lon_col, color_col=None, style='OpenStreetMap',
               cluster=False, parent=None):
        if not HAS_FOLIUM:
            return None, "Folium not installed"
        bounds = SpatialUtils.get_bounds(samples, lat_col, lon_col)
        if not bounds:
            return None, "No valid coordinates"
        m = folium.Map(
            location=[bounds['center_lat'], bounds['center_lon']],
            zoom_start=8, tiles=style, control_scale=True
        )
        plugins.Fullscreen().add_to(m)
        color_map = {
            "EGYPTIAN (HADDADIN FLOW)": "blue",
            "EGYPTIAN (ALKALINE / EXOTIC)": "red",
            "SINAI / TRANSITIONAL": "orange",
            "SINAI OPHIOLITIC": "darkred",
            "LOCAL LEVANTINE": "green",
            "HARRAT ASH SHAAM": "purple",
        }
        markers = []
        for s in samples:
            lat = SpatialUtils.safe_float(s.get(lat_col))
            lon = SpatialUtils.safe_float(s.get(lon_col))
            if lat is None or lon is None:
                continue
            classification = s.get(color_col, 'UNKNOWN') if color_col else 'UNKNOWN'
            color = color_map.get(classification, "gray")
            popup_html = f"<b>{s.get('Sample_ID', 'Unknown')}</b><br>{classification}<br>{lat:.4f}, {lon:.4f}"
            marker = folium.CircleMarker(
                location=[lat, lon], radius=8,
                popup=folium.Popup(popup_html, max_width=300),
                color=color, fill=True, fillColor=color, fillOpacity=0.8
            )
            marker.add_to(m)
            markers.append(marker)
        if cluster and len(markers) > 10:
            marker_cluster = plugins.MarkerCluster().add_to(m)
            for marker in markers:
                marker.add_to(marker_cluster)
        return m, None

    @staticmethod
    def export_kml(samples, lat_col, lon_col, color_col=None, path=None):
        if not path:
            return False
        try:
            kml_header = '''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document><name>Basalt Samples</name>'''
            kml_footer = '</Document>\n</kml>'
            placemarks = []
            for s in samples:
                lat = SpatialUtils.safe_float(s.get(lat_col))
                lon = SpatialUtils.safe_float(s.get(lon_col))
                if lat is None or lon is None:
                    continue
                placemark = f'''
    <Placemark>
        <name>{s.get('Sample_ID', 'Unknown')}</name>
        <Point><coordinates>{lon},{lat},0</coordinates></Point>
    </Placemark>'''
                placemarks.append(placemark)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(kml_header)
                f.write(''.join(placemarks))
                f.write(kml_footer)
            return True
        except:
            return False


class ThreeDViewer:
    @staticmethod
    def create(samples, lat_col, lon_col, elev_col, color_col=None,
               point_size=15, show_axes=True, show_grid=False,
               exaggeration=1.0, parent=None):
        if not HAS_PYVISTA:
            return False, "PyVista not installed"
        points = []
        colors = []
        color_map = {
            "EGYPTIAN (HADDADIN FLOW)": [0, 0, 255],
            "EGYPTIAN (ALKALINE / EXOTIC)": [255, 0, 0],
            "SINAI / TRANSITIONAL": [255, 215, 0],
            "SINAI OPHIOLITIC": [255, 165, 0],
            "LOCAL LEVANTINE": [0, 255, 0],
            "HARRAT ASH SHAAM": [128, 0, 128],
        }
        for s in samples:
            lat = SpatialUtils.safe_float(s.get(lat_col))
            lon = SpatialUtils.safe_float(s.get(lon_col))
            elev = SpatialUtils.safe_float(s.get(elev_col, 0))
            if lat is None or lon is None:
                continue
            elev_scaled = elev * exaggeration / 1000
            points.append([lon, lat, elev_scaled])
            classification = s.get(color_col, 'UNKNOWN') if color_col else 'UNKNOWN'
            rgb = color_map.get(classification, [128, 128, 128])
            colors.append(rgb)
        if not points:
            return False, "No valid points"
        plotter = pv.Plotter(window_size=[1200, 800])
        plotter.set_background("white")
        points_array = np.array(points)
        point_cloud = pv.PolyData(points_array)
        point_cloud['colors'] = np.array(colors, dtype=np.uint8)
        plotter.add_points(
            point_cloud, scalars='colors', rgb=True,
            point_size=point_size, render_points_as_spheres=True
        )
        if show_axes:
            plotter.add_axes(xlabel='Longitude', ylabel='Latitude',
                           zlabel=f'Elevation (km x{exaggeration})')
        if show_grid:
            plotter.show_grid()
        plotter.add_text(f"3D View ({len(points)} samples)", position='upper_edge', font_size=14)
        plotter.show()
        return True, None


# ============================================================================
# MAIN PLUGIN CLASS - CLEAN, RELEASE READY
# ============================================================================

class Gis3dViewerPlugin:
    """3D/GIS Viewer with LIVE preview in right panel - v3.0 FINAL"""

    def __init__(self, main_app):
        self.app = main_app
        self.window = None
        self.settings = SettingsManager('gis_3d_viewer')

        # Plain value storage - NO TKINTER VARS HERE
        self._lat_col = ""
        self._lon_col = ""
        self._elev_col = ""
        self._color_col = "Final_Classification"
        self._time_col = ""
        self._current_view = self.settings.get('view_mode', 'basic')
        self._point_size = self.settings.get('point_size', 15)
        self._map_style = self.settings.get('map_style', 'OpenStreetMap')
        self._cluster_markers = self.settings.get('cluster_markers', False)
        self._show_axes = self.settings.get('show_axes', True)
        self._show_grid = self.settings.get('show_grid', False)
        self._elev_exaggeration = self.settings.get('elevation_exaggeration', 1.0)

        # UI widgets - created in _create_ui
        self.lat_combo = None
        self.lon_combo = None
        self.elev_combo = None
        self.color_combo = None
        self.time_combo = None
        self.data_info = None
        self.preview_frame = None
        self.current_figure = None
        self.status_bar = None

        # Tkinter vars - created in _create_tkinter_vars
        self.lat_col = None
        self.lon_col = None
        self.elev_col = None
        self.color_col = None
        self.time_col = None
        self.point_size = None
        self.map_style = None
        self.cluster_markers = None
        self.show_axes = None
        self.show_grid = None
        self.elev_exaggeration = None
        self.view_mode = None
        self.status_var = None

    def show(self):
        """Standard plugin entry point - menu calls this"""
        self.open_window()

    def open_window(self):
        """Open main plugin window with LIVE preview"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        if not self.app or not self.app.root:
            messagebox.showerror("Plugin Error", "Main application not initialized.")
            return

        try:
            self.window = tk.Toplevel(self.app.root)
            self.window.title(f"🌍 3D GIS Viewer v3.0 - Live Preview")
            self.window.geometry("1200x700")
            self.window.minsize(1000, 600)
            self.window.transient(self.app.root)
            self.window.protocol("WM_DELETE_WINDOW", self._on_close)

            self._create_tkinter_vars()
            self._create_ui()
            self._refresh_data()

            if self.preview_frame:
                LivePreview.show_welcome(self.preview_frame)

        except Exception as e:
            print(f"Window creation failed: {e}")

    def _create_tkinter_vars(self):
        """Create Tkinter variables - window MUST exist"""
        self.lat_col = tk.StringVar(value=self._lat_col)
        self.lon_col = tk.StringVar(value=self._lon_col)
        self.elev_col = tk.StringVar(value=self._elev_col)
        self.color_col = tk.StringVar(value=self._color_col)
        self.time_col = tk.StringVar(value=self._time_col)
        self.point_size = tk.IntVar(value=self._point_size)
        self.map_style = tk.StringVar(value=self._map_style)
        self.cluster_markers = tk.BooleanVar(value=self._cluster_markers)
        self.show_axes = tk.BooleanVar(value=self._show_axes)
        self.show_grid = tk.BooleanVar(value=self._show_grid)
        self.elev_exaggeration = tk.DoubleVar(value=self._elev_exaggeration)
        self.view_mode = tk.StringVar(value=self._current_view)
        self.status_var = tk.StringVar(value="✓ Ready")

    def _create_ui(self):
        """Create compact left/right panel UI"""
        # Header
        header = tk.Frame(self.window, bg="#2c3e50", height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title_frame = tk.Frame(header, bg="#2c3e50")
        title_frame.pack(expand=True)

        tk.Label(title_frame, text="🌍", font=("Arial", 20),
                bg="#2c3e50", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Label(title_frame, text="3D GIS Viewer", font=("Arial", 16, "bold"),
                bg="#2c3e50", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Label(title_frame, text="v3.0 - Live Preview", font=("Arial", 11),
                bg="#2c3e50", fg="#BDC3C7").pack(side=tk.LEFT, padx=10)

        # Status bar - store reference
        self.status_bar = tk.Label(self.window, textvariable=self.status_var,
                                  bg="#ECF0F1", fg="#2C3E50", font=("Arial", 9),
                                  anchor=tk.W, padx=10, pady=2)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        # Main paned container
        main_paned = tk.PanedWindow(self.window, orient=tk.HORIZONTAL, sashwidth=6)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # LEFT PANEL - Controls
        left_panel = tk.Frame(main_paned, bg="#ECF0F1", relief=tk.FLAT)
        main_paned.add(left_panel, width=360, minsize=320)

        # RIGHT PANEL - LIVE PREVIEW
        right_panel = tk.Frame(main_paned, bg="white", relief=tk.FLAT)
        main_paned.add(right_panel, width=800, minsize=600)

        self._setup_left_panel(left_panel)
        self._setup_right_panel(right_panel)

    def _setup_right_panel(self, parent):
        """RIGHT PANEL - LIVE PREVIEW"""
        self.preview_frame = tk.Frame(parent, bg="white")
        self.preview_frame.pack(fill=tk.BOTH, expand=True)

    def _setup_left_panel(self, parent):
        """LEFT PANEL - All controls with LIVE preview triggers"""
        canvas = tk.Canvas(parent, bg="#ECF0F1", highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#ECF0F1")

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # ========== DATA INFO ==========
        info_frame = tk.LabelFrame(scrollable_frame, text="📊 Data Summary",
                                  padx=10, pady=8, bg="#ECF0F1",
                                  font=("Arial", 10, "bold"))
        info_frame.pack(fill=tk.X, padx=10, pady=5)

        self.data_info = tk.Text(info_frame, height=4, width=30,
                                bg="white", fg="#2C3E50",
                                font=("Courier", 9), relief=tk.FLAT, borderwidth=1)
        self.data_info.pack(fill=tk.X)
        self.data_info.insert('1.0', "Total samples: 0\nWith coords: 0\nWith elevation: 0")
        self.data_info.config(state=tk.DISABLED)

        # ========== COLUMN MAPPING ==========
        col_frame = tk.LabelFrame(scrollable_frame, text="📝 Column Mapping",
                                 padx=10, pady=8, bg="#ECF0F1",
                                 font=("Arial", 10, "bold"))
        col_frame.pack(fill=tk.X, padx=10, pady=5)

        # Latitude
        lat_row = tk.Frame(col_frame, bg="#ECF0F1")
        lat_row.pack(fill=tk.X, pady=2)
        tk.Label(lat_row, text="Latitude:", width=10, anchor=tk.W,
                bg="#ECF0F1", font=("Arial", 9)).pack(side=tk.LEFT)
        self.lat_combo = ttk.Combobox(lat_row, textvariable=self.lat_col,
                                      values=[], width=18, font=("Arial", 9))
        self.lat_combo.pack(side=tk.LEFT, padx=5)
        self.lat_combo.bind('<<ComboboxSelected>>', lambda e: self._update_preview())

        # Longitude
        lon_row = tk.Frame(col_frame, bg="#ECF0F1")
        lon_row.pack(fill=tk.X, pady=2)
        tk.Label(lon_row, text="Longitude:", width=10, anchor=tk.W,
                bg="#ECF0F1", font=("Arial", 9)).pack(side=tk.LEFT)
        self.lon_combo = ttk.Combobox(lon_row, textvariable=self.lon_col,
                                      values=[], width=18, font=("Arial", 9))
        self.lon_combo.pack(side=tk.LEFT, padx=5)
        self.lon_combo.bind('<<ComboboxSelected>>', lambda e: self._update_preview())

        # Elevation
        elev_row = tk.Frame(col_frame, bg="#ECF0F1")
        elev_row.pack(fill=tk.X, pady=2)
        tk.Label(elev_row, text="Elevation:", width=10, anchor=tk.W,
                bg="#ECF0F1", font=("Arial", 9)).pack(side=tk.LEFT)
        self.elev_combo = ttk.Combobox(elev_row, textvariable=self.elev_col,
                                       values=[], width=18, font=("Arial", 9))
        self.elev_combo.pack(side=tk.LEFT, padx=5)
        self.elev_combo.bind('<<ComboboxSelected>>', lambda e: self._update_preview())

        # Color by
        color_row = tk.Frame(col_frame, bg="#ECF0F1")
        color_row.pack(fill=tk.X, pady=2)
        tk.Label(color_row, text="Color by:", width=10, anchor=tk.W,
                bg="#ECF0F1", font=("Arial", 9)).pack(side=tk.LEFT)
        self.color_combo = ttk.Combobox(color_row, textvariable=self.color_col,
                                        values=['Final_Classification', 'Auto_Classification', 'Group'],
                                        width=18, font=("Arial", 9))
        self.color_combo.pack(side=tk.LEFT, padx=5)
        self.color_combo.bind('<<ComboboxSelected>>', lambda e: self._update_preview())

        # Time column (optional)
        time_row = tk.Frame(col_frame, bg="#ECF0F1")
        time_row.pack(fill=tk.X, pady=2)
        tk.Label(time_row, text="Time/Year:", width=10, anchor=tk.W,
                bg="#ECF0F1", font=("Arial", 9)).pack(side=tk.LEFT)
        self.time_combo = ttk.Combobox(time_row, textvariable=self.time_col,
                                       values=[], width=18, font=("Arial", 9))
        self.time_combo.pack(side=tk.LEFT, padx=5)

        # ========== VIEW MODE ==========
        view_frame = tk.LabelFrame(scrollable_frame, text="🎯 Preview Mode",
                                  padx=10, pady=8, bg="#ECF0F1",
                                  font=("Arial", 10, "bold"))
        view_frame.pack(fill=tk.X, padx=10, pady=5)

        modes = [
            ("📍 2D Map", "basic"),
            ("🗺️ Web Map (Browser)", "web"),
            ("🎲 3D Preview", "3d"),
            ("🏔️ SRTM Terrain", "terrain"),
        ]

        for text, value in modes:
            rb = tk.Radiobutton(view_frame, text=text, variable=self.view_mode,
                               value=value, bg="#ECF0F1", font=("Arial", 9),
                               command=self._update_preview)
            rb.pack(anchor=tk.W, pady=2)

        # ========== SETTINGS ==========
        settings_frame = tk.LabelFrame(scrollable_frame, text="⚙️ Settings",
                                      padx=10, pady=8, bg="#ECF0F1",
                                      font=("Arial", 10, "bold"))
        settings_frame.pack(fill=tk.X, padx=10, pady=5)

        # Point size
        size_row = tk.Frame(settings_frame, bg="#ECF0F1")
        size_row.pack(fill=tk.X, pady=2)
        tk.Label(size_row, text="Point size:", width=12, anchor=tk.W,
                bg="#ECF0F1", font=("Arial", 9)).pack(side=tk.LEFT)
        tk.Scale(size_row, from_=5, to=30, orient=tk.HORIZONTAL,
                variable=self.point_size, length=120,
                command=lambda x: self._update_preview(),
                bg="#ECF0F1", highlightthickness=0).pack(side=tk.LEFT, padx=5)

        # Z scale
        z_row = tk.Frame(settings_frame, bg="#ECF0F1")
        z_row.pack(fill=tk.X, pady=2)
        tk.Label(z_row, text="Z scale:", width=12, anchor=tk.W,
                bg="#ECF0F1", font=("Arial", 9)).pack(side=tk.LEFT)
        tk.Scale(z_row, from_=0.1, to=5.0, resolution=0.1,
                orient=tk.HORIZONTAL, variable=self.elev_exaggeration,
                length=120, command=lambda x: self._update_preview(),
                bg="#ECF0F1", highlightthickness=0).pack(side=tk.LEFT, padx=5)

        # ========== ACTION BUTTONS ==========
        action_frame = tk.Frame(scrollable_frame, bg="#ECF0F1", pady=10)
        action_frame.pack(fill=tk.X, padx=10)

        # Fullscreen button
        self.fullscreen_btn = tk.Button(action_frame, text="🚀 LAUNCH FULLSCREEN",
                                       bg="#3498DB", fg="white",
                                       font=("Arial", 12, "bold"),
                                       height=2, command=self._launch_fullscreen)
        self.fullscreen_btn.pack(fill=tk.X, pady=2)

        # Export buttons
        btn_row = tk.Frame(action_frame, bg="#ECF0F1")
        btn_row.pack(fill=tk.X, pady=2)

        self.export_btn = tk.Button(btn_row, text="💾 Export PNG",
                                   bg="#2ECC71", fg="white",
                                   font=("Arial", 9, "bold"),
                                   command=self._export_preview)
        self.export_btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)

        self.kml_btn = tk.Button(btn_row, text="🌐 Google Earth",
                                bg="#E67E22", fg="white",
                                font=("Arial", 9, "bold"),
                                command=self._export_kml)
        self.kml_btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)

        self.refresh_btn = tk.Button(action_frame, text="🔄 Refresh Data",
                                    bg="#95A5A6", fg="white",
                                    font=("Arial", 9),
                                    command=self._refresh_data)
        self.refresh_btn.pack(fill=tk.X, pady=2)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # ========== LIVE PREVIEW ==========

    def _update_preview(self):
        """Update live preview based on current settings"""
        if not self.preview_frame or not hasattr(self.app, 'samples') or not self.app.samples:
            return

        mode = self.view_mode.get() if self.view_mode else "basic"

        if mode == "basic":
            self._preview_2d()
        elif mode == "3d":
            self._preview_3d()
        elif mode == "terrain":
            self._preview_terrain()
        elif mode == "web":
            LivePreview.show_info(self.preview_frame, "🌐 Web Map",
                                 "Interactive map will open in your browser.\n\n"
                                 "Click 'LAUNCH FULLSCREEN' to generate.")

    def _preview_2d(self):
        """Render 2D preview in panel"""
        if not self.lat_col.get() or not self.lon_col.get():
            LivePreview.show_error(self.preview_frame, "Select latitude and longitude columns")
            return

        bounds = SpatialUtils.get_bounds(self.app.samples, self.lat_col.get(), self.lon_col.get())
        LivePreview.render_2d(self.preview_frame, self.app.samples,
                            self.lat_col.get(), self.lon_col.get(),
                            self.color_col.get() if self.color_col.get() else None,
                            bounds)

    def _preview_3d(self):
        """Render 3D preview screenshot in panel"""
        if not HAS_PYVISTA:
            LivePreview.show_error(self.preview_frame, "PyVista not installed\n\npip install pyvista")
            return

        if not self.lat_col.get() or not self.lon_col.get():
            LivePreview.show_error(self.preview_frame, "Select latitude and longitude columns")
            return

        elev_col = self.elev_col.get() if self.elev_col.get() else 'Elevation'

        LivePreview.render_3d_preview(self.preview_frame, self.app.samples,
                                     self.lat_col.get(), self.lon_col.get(), elev_col,
                                     self.color_col.get() if self.color_col.get() else None,
                                     self.point_size.get(), self.elev_exaggeration.get())

    def _preview_terrain(self):
        """Render SRTM terrain preview in panel"""
        if not all([HAS_PYVISTA, HAS_SCIPY, HAS_REQUESTS, HAS_PANDAS]):
            LivePreview.show_error(self.preview_frame,
                                  "Terrain requires: pyvista, scipy, requests, pandas\n\n"
                                  "pip install pyvista scipy requests pandas")
            return

        if not self.lat_col.get() or not self.lon_col.get():
            LivePreview.show_error(self.preview_frame, "Select latitude and longitude columns")
            return

        LivePreview.render_terrain_preview(self.preview_frame, self.app.samples,
                                          self.lat_col.get(), self.lon_col.get(),
                                          self.color_col.get() if self.color_col.get() else None,
                                          self.elev_exaggeration.get(),
                                          self._update_status)

    # ========== FULLSCREEN LAUNCH ==========

    def _launch_fullscreen(self):
        """Launch current view in fullscreen window"""
        mode = self.view_mode.get() if self.view_mode else "basic"

        if mode == "basic":
            self._launch_basic_2d()
        elif mode == "web":
            self._launch_web_map()
        elif mode in ["3d", "terrain"]:
            self._launch_3d_viewer()

    def _launch_basic_2d(self):
        """Launch fullscreen 2D map"""
        if not self.lat_col.get() or not self.lon_col.get():
            self._update_status("⚠️ Select latitude and longitude columns", "warning")
            return

        Basic2DMap.create(self.window, self.app.samples,
                         self.lat_col.get(), self.lon_col.get(),
                         self.color_col.get() if self.color_col.get() else None,
                         "Sample Distribution")
        self._update_status("✅ 2D map opened", "success")

    def _launch_web_map(self):
        """Launch interactive web map in browser"""
        if not HAS_FOLIUM:
            self._update_status("❌ Folium required", "error")
            return

        if not self.lat_col.get() or not self.lon_col.get():
            self._update_status("⚠️ Select latitude and longitude columns", "warning")
            return

        self._update_status("🌐 Generating web map...", "info")

        m, error = WebMapGenerator.create(
            self.app.samples, self.lat_col.get(), self.lon_col.get(),
            self.color_col.get() if self.color_col.get() else None,
            self.map_style.get(), self.cluster_markers.get(), self.window
        )

        if m:
            path = os.path.join(tempfile.gettempdir(),
                               f"basalt_map_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
            m.save(path)
            webbrowser.open('file://' + os.path.abspath(path))
            self._update_status("✅ Map opened in browser", "success")
        else:
            self._update_status(f"❌ Failed: {error}", "error")

    def _launch_3d_viewer(self):
        """Launch fullscreen 3D viewer"""
        if not HAS_PYVISTA:
            self._update_status("❌ PyVista required", "error")
            return

        if not self.lat_col.get() or not self.lon_col.get():
            self._update_status("⚠️ Select latitude and longitude columns", "warning")
            return

        self._update_status("🎲 Launching 3D viewer...", "info")

        elev_col = self.elev_col.get() if self.elev_col.get() else 'Elevation'

        success, error = ThreeDViewer.create(
            self.app.samples, self.lat_col.get(), self.lon_col.get(), elev_col,
            self.color_col.get() if self.color_col.get() else None,
            self.point_size.get(), self.show_axes.get(), self.show_grid.get(),
            self.elev_exaggeration.get(), self.window
        )

        if success:
            self._update_status("✅ 3D viewer closed", "success")
        else:
            self._update_status(f"❌ 3D error: {error}", "error")

    # ========== EXPORT ==========

    def _export_preview(self):
        """Export current preview as PNG"""
        if not self.preview_frame:
            return

        path = filedialog.asksaveasfilename(
            title="Save Preview",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png")],
            parent=self.window
        )

        if path:
            for widget in self.preview_frame.winfo_children():
                if isinstance(widget, tk.Canvas) and hasattr(widget, 'figure'):
                    widget.figure.savefig(path, dpi=300, bbox_inches='tight')
                    self._update_status(f"✅ Saved to {os.path.basename(path)}", "success")
                    return
            self._update_status("❌ No preview to export", "error")

    def _export_kml(self):
        """Export as KML for Google Earth"""
        if not self.lat_col.get() or not self.lon_col.get():
            self._update_status("⚠️ Select latitude and longitude columns", "warning")
            return

        path = filedialog.asksaveasfilename(
            title="Export to Google Earth",
            defaultextension=".kml",
            filetypes=[("KML files", "*.kml")],
            parent=self.window
        )

        if path:
            success = WebMapGenerator.export_kml(
                self.app.samples, self.lat_col.get(), self.lon_col.get(),
                self.color_col.get() if self.color_col.get() else None, path
            )

            if success:
                if messagebox.askyesno("Open in Google Earth",
                                      "KML exported successfully.\n\nOpen in Google Earth now?",
                                      parent=self.window):
                    webbrowser.open(path)
                self._update_status("✅ KML saved", "success")
            else:
                self._update_status("❌ KML export failed", "error")

    # ========== DATA MANAGEMENT ==========

    def _refresh_data(self):
        """Refresh column lists and update preview"""
        if not hasattr(self.app, 'samples') or not self.app.samples:
            self._update_status("⚠️ No data loaded", "warning")
            return

        columns = set()
        for sample in self.app.samples:
            columns.update(sample.keys())
        columns = sorted(list(columns))

        if self.lat_combo:
            self.lat_combo['values'] = columns
        if self.lon_combo:
            self.lon_combo['values'] = columns
        if self.elev_combo:
            self.elev_combo['values'] = [''] + columns
        if self.time_combo:
            self.time_combo['values'] = [''] + columns

        for col in columns:
            col_lower = col.lower()
            if 'lat' in col_lower:
                self.lat_col.set(col)
            if 'lon' in col_lower or 'long' in col_lower:
                self.lon_col.set(col)
            if 'elev' in col_lower or 'alt' in col_lower:
                self.elev_col.set(col)

        self._update_data_info()
        self._update_preview()
        self._update_status(f"✅ Loaded {len(self.app.samples)} samples", "success")

    def _update_data_info(self):
        """Update data summary text"""
        if not hasattr(self.app, 'samples') or not self.app.samples:
            return

        samples = self.app.samples
        total = len(samples)
        with_coords = 0
        with_elev = 0

        lat_col = self.lat_col.get() if self.lat_col else ""
        lon_col = self.lon_col.get() if self.lon_col else ""
        elev_col = self.elev_col.get() if self.elev_col else ""

        for s in samples:
            lat = SpatialUtils.safe_float(s.get(lat_col))
            lon = SpatialUtils.safe_float(s.get(lon_col))
            if lat is not None and lon is not None:
                if SpatialUtils.validate_lat(lat) and SpatialUtils.validate_lon(lon):
                    with_coords += 1
                    elev = SpatialUtils.safe_float(s.get(elev_col))
                    if elev is not None:
                        with_elev += 1

        if self.data_info:
            self.data_info.config(state=tk.NORMAL)
            self.data_info.delete('1.0', tk.END)
            self.data_info.insert('1.0',
                f"Total samples: {total}\n"
                f"With coords: {with_coords}\n"
                f"With elevation: {with_elev}"
            )
            self.data_info.config(state=tk.DISABLED)

    def _update_status(self, message, level="info"):
        """Update status bar using stored reference"""
        colors = {"info": "#2C3E50", "success": "green",
                 "warning": "#E67E22", "error": "red"}
        if self.status_var:
            self.status_var.set(message)
        if self.status_bar:
            self.status_bar.config(fg=colors.get(level, "#2C3E50"))

    def _on_view_mode_change(self):
        """Handle view mode change"""
        if self.view_mode:
            self._current_view = self.view_mode.get()
            self.settings.set('view_mode', self._current_view)

    def _on_close(self):
        """Save settings and close"""
        if self.view_mode:
            self.settings.set('view_mode', self.view_mode.get())
        if self.point_size:
            self.settings.set('point_size', self.point_size.get())
        if self.map_style:
            self.settings.set('map_style', self.map_style.get())
        if self.cluster_markers:
            self.settings.set('cluster_markers', self.cluster_markers.get())
        if self.show_axes:
            self.settings.set('show_axes', self.show_axes.get())
        if self.show_grid:
            self.settings.set('show_grid', self.show_grid.get())
        if self.elev_exaggeration:
            self.settings.set('elevation_exaggeration', self.elev_exaggeration.get())

        if self.window:
            self.window.destroy()


# ============================================================================
# PLUGIN SETUP
# ============================================================================

def setup_plugin(main_app):
    """Plugin setup function"""
    plugin = Gis3dViewerPlugin(main_app)
    return plugin
