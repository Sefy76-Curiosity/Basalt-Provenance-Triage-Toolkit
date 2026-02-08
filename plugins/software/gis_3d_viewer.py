"""
3D/GIS Viewer Plugin for Basalt Provenance Toolkit
Advanced spatial visualization without external GIS software

Features:
- Tier 1: Basic 2D matplotlib map (always available)
- Tier 2: Interactive Folium web maps (optional: pip install folium geopandas)
- Tier 3: PyVista 3D scatter viewer (optional: pip install pyvista)

NO Google Earth integration yet - that's being decided separately

Author: Sefy Levy
License: CC BY-NC-SA 4.0
"""

PLUGIN_INFO = {
      "category": "software",
    "id": "gis_3d_viewer",
    "name": "3D/GIS Viewer",
    "description": "3D scatter plots and interactive maps (PyVista, Folium)",
    "icon": "🌍",
    "version": "1.0",
    "requires": ["matplotlib", "numpy", "pyvista", "folium", "geopandas", "shapely"],
    "author": "Sefy Levy"
}

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import webbrowser
import tempfile
import os

# Check dependencies - FIXED VERSION
HAS_REQUIREMENTS = False
HAS_PYVISTA = False
HAS_FOLIUM = False
HAS_GEOPANDAS = False
HAS_MATPLOTLIB = False
HAS_NUMPY = False
IMPORT_ERROR = ""

try:
    import matplotlib
    HAS_MATPLOTLIB = True
except ImportError as e:
    IMPORT_ERROR += f"matplotlib: {str(e)}\n"

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError as e:
    IMPORT_ERROR += f"numpy: {str(e)}\n"

try:
    import pyvista as pv
    HAS_PYVISTA = True
except ImportError as e:
    IMPORT_ERROR += f"pyvista: {str(e)}\n"

try:
    import folium
    HAS_FOLIUM = True
except ImportError as e:
    IMPORT_ERROR += f"folium: {str(e)}\n"

try:
    import geopandas as gpd
    from shapely.geometry import Point
    HAS_GEOPANDAS = True
except ImportError as e:
    IMPORT_ERROR += f"geopandas/shapely: {str(e)}\n"

# Plugin can load if we have minimum requirements
HAS_REQUIREMENTS = HAS_MATPLOTLIB and HAS_NUMPY


def safe_float(value):
    """Safely convert value to float"""
    if value is None or value == '':
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


class Gis3dViewerPlugin:
    """Plugin for 3D/GIS visualization"""

    def __init__(self, main_app):
        """Initialize plugin"""
        self.app = main_app
        self.window = None

    def open_gis_3d_viewer_window(self):
        """Open the 3D/GIS viewer interface"""
        # Check minimum requirements
        if not HAS_REQUIREMENTS:
            response = messagebox.askyesno(
                "Missing Dependencies",
                f"3D/GIS Viewer requires these packages:\n\n"
                f"• matplotlib (required)\n"
                f"• numpy (required)\n"
                f"• pyvista (for 3D viewer)\n"
                f"• folium (for web maps)\n"
                f"• geopandas & shapely (for web maps)\n\n"
                f"Missing:\n{IMPORT_ERROR}\n\n"
                f"Do you want to install missing dependencies now?",
                parent=self.app.root
            )
            if response:
                # Try to open plugin manager
                if hasattr(self.app, 'open_plugin_manager'):
                    self.app.open_plugin_manager()
                elif hasattr(self.app, 'plugin_manager'):
                    self.app.plugin_manager()
                else:
                    messagebox.showinfo(
                        "Install Manually",
                        "Please use:\n"
                        "1. Tools → Plugin Manager → 'Install All Missing'\n"
                        "OR\n"
                        "2. Run in terminal:\n"
                        "   pip install matplotlib numpy pyvista folium geopandas shapely",
                        parent=self.app.root
                    )
            return

        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("3D/GIS Viewer")
        self.window.geometry("750x520")

        # Make window stay on top
        self.window.transient(self.app.root)

        self._create_interface()

        # Bring to front
        self.window.lift()
        self.window.focus_force()

    def _create_interface(self):
        """Create the viewer interface"""
        # Header
        header = tk.Frame(self.window, bg="#00897B")
        header.pack(fill=tk.X)

        tk.Label(header,
                text="🌍 3D/GIS Viewer",
                font=("Arial", 16, "bold"),
                bg="#00897B", fg="white",
                pady=5).pack()

        tk.Label(header,
                text="Visualize your samples in 3D space and on interactive maps",
                font=("Arial", 10),
                bg="#00897B", fg="white",
                pady=5).pack()

        # Create notebook
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Tab 1: 3D Viewer
        self._create_3d_viewer_tab(notebook)

        # Tab 2: Interactive Maps
        self._create_maps_tab(notebook)

        # Tab 3: Basic 2D (Always Available)
        self._create_basic_2d_tab(notebook)

        # Tab 4: Help
        self._create_help_tab(notebook)

    def _create_3d_viewer_tab(self, notebook):
        """Create 3D viewer tab"""
        frame = tk.Frame(notebook)
        notebook.add(frame, text="🎲 3D Viewer")

        # Status banner
        status_frame = tk.Frame(frame, bg="#E3F2FD" if HAS_PYVISTA else "#FFEBEE",
                               relief=tk.RAISED, borderwidth=2)
        status_frame.pack(fill=tk.X, padx=10, pady=5)

        if HAS_PYVISTA:
            tk.Label(status_frame,
                    text="✅ PyVista Available - 3D visualization enabled!",
                    font=("Arial", 10, "bold"),
                    bg="#E3F2FD", fg="green",
                    pady=5).pack()
        else:
            tk.Label(status_frame,
                    text="❌ PyVista Not Installed",
                    font=("Arial", 10, "bold"),
                    bg="#FFEBEE", fg="red",
                    pady=5).pack()
            tk.Label(status_frame,
                    text="Install with: pip install pyvista",
                    font=("Courier", 9),
                    bg="#FFEBEE",
                    pady=5).pack()
            # Install button
            install_btn = tk.Button(status_frame,
                                  text="Install Now",
                                  command=self._install_pyvista,
                                  bg="#FF9800", fg="white",
                                  font=("Arial", 9, "bold"),
                                  cursor="hand2")
            install_btn.pack(pady=5)

        # Content
        content = tk.Frame(frame)
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        tk.Label(content,
                text="Interactive 3D Scatter Plot",
                font=("Arial", 12, "bold")).pack(anchor=tk.W, pady="0 5")

        tk.Label(content,
                text="• Rotate, zoom, and pan in true 3D space\n"
                     "• Color-coded by provenance classification\n"
                     "• Professional visualization for publications\n"
                     "• Export high-resolution snapshots",
                font=("Arial", 9),
                justify=tk.LEFT).pack(anchor=tk.W, pady=5)

        # Options
        if HAS_PYVISTA:
            options_frame = tk.LabelFrame(content, text="Display Options",
                                         font=("Arial", 10, "bold"),
                                         padx=10, pady=5)
            options_frame.pack(fill=tk.X, pady=5)

            # Point size
            size_frame = tk.Frame(options_frame)
            size_frame.pack(fill=tk.X, pady=5)
            tk.Label(size_frame, text="Point Size:",
                    font=("Arial", 9)).pack(side=tk.LEFT)
            self.point_size_var = tk.IntVar(value=15)
            tk.Scale(size_frame, from_=5, to=50, orient=tk.HORIZONTAL,
                    variable=self.point_size_var, length=200).pack(side=tk.LEFT, padx=10)

            # Checkboxes
            self.show_axes_var = tk.BooleanVar(value=True)
            tk.Checkbutton(options_frame, text="Show coordinate axes",
                          variable=self.show_axes_var,
                          font=("Arial", 9)).pack(anchor=tk.W, pady=2)

            self.show_grid_var = tk.BooleanVar(value=False)
            tk.Checkbutton(options_frame, text="Show grid",
                          variable=self.show_grid_var,
                          font=("Arial", 9)).pack(anchor=tk.W, pady=2)

        # Button
        btn_frame = tk.Frame(content)
        btn_frame.pack(pady=8)

        if HAS_PYVISTA:
            tk.Button(btn_frame, text="🚀 Launch 3D Viewer",
                     command=self._launch_pyvista_viewer,
                     bg="#00897B", fg="white",
                     font=("Arial", 11, "bold"),
                     width=20, height=2).pack()
        else:
            tk.Label(btn_frame,
                    text="Install PyVista to enable 3D visualization:\n\n"
                         "pip install pyvista\n\n"
                         "PyVista provides professional 3D scatter plots\n"
                         "with interactive rotation, zooming, and export.",
                    font=("Arial", 9),
                    fg="gray",
                    justify=tk.CENTER).pack(pady=8)

    def _create_maps_tab(self, notebook):
        """Create interactive maps tab"""
        frame = tk.Frame(notebook)
        notebook.add(frame, text="🗺️ Web Maps")

        # Status banner
        status_frame = tk.Frame(frame, bg="#FFF3E0" if HAS_FOLIUM else "#FFEBEE",
                               relief=tk.RAISED, borderwidth=2)
        status_frame.pack(fill=tk.X, padx=10, pady=5)

        if HAS_FOLIUM:
            tk.Label(status_frame,
                    text="✅ Folium Available - Interactive web maps enabled!",
                    font=("Arial", 10, "bold"),
                    bg="#FFF3E0", fg="green",
                    pady=5).pack()
        else:
            tk.Label(status_frame,
                    text="❌ Folium Not Installed",
                    font=("Arial", 10, "bold"),
                    bg="#FFEBEE", fg="red",
                    pady=5).pack()
            tk.Label(status_frame,
                    text="Install with: pip install folium geopandas shapely",
                    font=("Courier", 9),
                    bg="#FFEBEE",
                    pady=5).pack()
            # Install button
            install_btn = tk.Button(status_frame,
                                  text="Install Now",
                                  command=self._install_folium,
                                  bg="#FF9800", fg="white",
                                  font=("Arial", 9, "bold"),
                                  cursor="hand2")
            install_btn.pack(pady=5)

        # Content
        content = tk.Frame(frame)
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        tk.Label(content,
                text="Interactive Web Maps (Google Maps Style)",
                font=("Arial", 12, "bold")).pack(anchor=tk.W, pady="0 5")

        tk.Label(content,
                text="• Zoom and pan like Google Maps\n"
                     "• Click markers for sample details\n"
                     "• Multiple base map styles\n"
                     "• Export as standalone HTML file",
                font=("Arial", 9),
                justify=tk.LEFT).pack(anchor=tk.W, pady=5)

        # Options
        if HAS_FOLIUM:
            options_frame = tk.LabelFrame(content, text="Map Options",
                                         font=("Arial", 10, "bold"),
                                         padx=10, pady=5)
            options_frame.pack(fill=tk.X, pady=5)

            # Base map style
            style_frame = tk.Frame(options_frame)
            style_frame.pack(fill=tk.X, pady=5)
            tk.Label(style_frame, text="Base Map:",
                    font=("Arial", 9)).pack(side=tk.LEFT)
            self.map_style_var = tk.StringVar(value="OpenStreetMap")
            map_styles = ["OpenStreetMap", "Stamen Terrain", "Stamen Toner", "CartoDB Positron"]
            ttk.Combobox(style_frame, textvariable=self.map_style_var,
                        values=map_styles, state='readonly',
                        width=20).pack(side=tk.LEFT, padx=10)

            self.cluster_markers_var = tk.BooleanVar(value=False)
            tk.Checkbutton(options_frame, text="Cluster nearby markers (reduces clutter)",
                          variable=self.cluster_markers_var,
                          font=("Arial", 9)).pack(anchor=tk.W, pady=2)

        # Button
        btn_frame = tk.Frame(content)
        btn_frame.pack(pady=8)

        if HAS_FOLIUM:
            tk.Button(btn_frame, text="🗺️ Generate Interactive Map",
                     command=self._generate_folium_map,
                     bg="#FF6F00", fg="white",
                     font=("Arial", 11, "bold"),
                     width=25, height=2).pack()
        else:
            tk.Label(btn_frame,
                    text="Install Folium for interactive web maps:\n\n"
                         "pip install folium geopandas shapely\n\n"
                         "Creates beautiful HTML maps that open in your browser.\n"
                         "Perfect for sharing with collaborators!",
                    font=("Arial", 9),
                    fg="gray",
                    justify=tk.CENTER).pack(pady=8)

    def _create_basic_2d_tab(self, notebook):
        """Create basic 2D map tab"""
        frame = tk.Frame(notebook)
        notebook.add(frame, text="📍 Basic 2D")

        # Status banner (always available)
        status_frame = tk.Frame(frame, bg="#E8F5E9", relief=tk.RAISED, borderwidth=2)
        status_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(status_frame,
                text="✅ Always Available - No dependencies required!",
                font=("Arial", 10, "bold"),
                bg="#E8F5E9", fg="green",
                pady=5).pack()

        # Content
        content = tk.Frame(frame)
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        tk.Label(content,
                text="Simple 2D Scatter Map",
                font=("Arial", 12, "bold")).pack(anchor=tk.W, pady="0 5")

        tk.Label(content,
                text="• Basic lat/long scatter plot using matplotlib\n"
                     "• Color-coded by provenance\n"
                     "• No external dependencies\n"
                     "• Export as PNG/PDF",
                font=("Arial", 9),
                justify=tk.LEFT).pack(anchor=tk.W, pady=5)

        tk.Label(content,
                text="\nThis is a quick visualization option that works immediately.\n"
                     "For more advanced features, install PyVista or Folium above.",
                font=("Arial", 9),
                fg="gray",
                justify=tk.LEFT).pack(anchor=tk.W, pady=5)

        # Button
        btn_frame = tk.Frame(content)
        btn_frame.pack(pady=8)

        tk.Button(btn_frame, text="📊 Generate 2D Map",
                 command=self._generate_basic_2d_map,
                 bg="#4CAF50", fg="white",
                 font=("Arial", 11, "bold"),
                 width=20, height=2).pack()

    def _create_help_tab(self, notebook):
        """Create help tab"""
        frame = tk.Frame(notebook)
        notebook.add(frame, text="❓ Help")

        from tkinter import scrolledtext
        text = scrolledtext.ScrolledText(frame, wrap=tk.WORD,
                                        font=("Arial", 10), padx=8, pady=5)
        text.pack(fill=tk.BOTH, expand=True)

        help_text = """
3D/GIS VIEWER - USER GUIDE
═══════════════════════════════════════════════════════════════

OVERVIEW
────────────────────────────────────────────────────────────────
This plugin provides THREE tiers of spatial visualization:

TIER 1 - Basic 2D Map (Always Available)
• Simple latitude/longitude scatter plot
• Uses matplotlib (already installed)
• Good for quick checks
• Export as PNG/PDF

TIER 2 - Interactive Web Maps (Install: pip install folium geopandas)
• Google Maps-style interface
• Zoom, pan, satellite/terrain views
• Click markers for sample details
• Export as standalone HTML file
• Share with colleagues

TIER 3 - 3D Viewer (Install: pip install pyvista)
• Professional 3D scatter plot
• Rotate, zoom, pan in 3D space
• Interactive visualization
• Export high-resolution images
• Publication-quality output

═══════════════════════════════════════════════════════════════

DATA REQUIREMENTS
────────────────────────────────────────────────────────────────
Your samples need geographic coordinates to appear on maps:

REQUIRED COLUMNS:
• Latitude (decimal degrees, e.g., 32.5420)
• Longitude (decimal degrees, e.g., 35.2167)

OPTIONAL COLUMNS:
• Elevation (meters above sea level, for 3D viewer)

IMPORTANT: Coordinates must be in decimal degrees format, NOT
degrees/minutes/seconds (DMS).

Example:
✓ Good: 32.5420, 35.2167
✗ Bad: 32°32'31"N, 35°13'00"E

═══════════════════════════════════════════════════════════════

INSTALLATION
────────────────────────────────────────────────────────────────

For Interactive Web Maps:
    pip install folium geopandas shapely

For 3D Viewer:
    pip install pyvista

Install Both:
    pip install folium geopandas shapely pyvista

If pip3 command not found:
    python -m pip install folium geopandas shapely pyvista
    OR
    python3 -m pip install folium geopandas shapely pyvista

═══════════════════════════════════════════════════════════════

USAGE - 3D VIEWER
────────────────────────────────────────────────────────────────
Mouse Controls:
• Left click + drag: Rotate view
• Right click + drag: Pan/move
• Scroll wheel: Zoom in/out

Keyboard Shortcuts:
• 's' key: Save screenshot
• 'r' key: Reset camera view
• 'q' key: Quit viewer

Tips:
• Adjust point size for better visibility
• Use axes to understand orientation
• Elevation data enhances 3D effect

═══════════════════════════════════════════════════════════════

USAGE - INTERACTIVE MAPS
────────────────────────────────────────────────────────────────
• Map opens automatically in your browser
• Zoom and pan like Google Maps
• Click any marker to see sample details
• Change base map for different views
• Save HTML file to share with team

Tips:
• OpenStreetMap good for labels
• Terrain shows topography
• Toner provides clean, minimal look
• HTML file works offline

═══════════════════════════════════════════════════════════════

USAGE - BASIC 2D MAP
────────────────────────────────────────────────────────────────
• Opens in matplotlib window
• Use toolbar to zoom/pan
• Click save icon to export
• Good for quick visualization

═══════════════════════════════════════════════════════════════

USE CASES
────────────────────────────────────────────────────────────────

Archaeological Survey:
• Map artifact findspots across excavation
• Visualize provenance patterns geographically
• Identify spatial clusters

Provenance Studies:
• Compare sample locations to source regions
• Identify trade routes
• Show "local" vs "imported" patterns

Publication Figures:
• Generate professional maps for papers
• Export high-res images
• Create supplementary HTML maps

Field Planning:
• Identify gaps in sampling coverage
• Plan future excavation locations
• Share maps with field teams

═══════════════════════════════════════════════════════════════

TROUBLESHOOTING
────────────────────────────────────────────────────────────────

"No samples with coordinates":
→ Check your data has Latitude and Longitude columns
→ Make sure values are decimal degrees (not blank)

"PyVista won't install":
→ Try: python -m pip install pyvista
→ May need Visual C++ on Windows

"Map doesn't open in browser":
→ Check default browser settings
→ Look for HTML file in save location
→ Try opening HTML file manually

"3D viewer is slow":
→ Reduce number of samples
→ Decrease point size
→ Update graphics drivers
→ Close other 3D applications

"Wrong map location":
→ Check coordinate format (decimal degrees)
→ Verify positive/negative signs
→ Ensure Latitude/Longitude not swapped

═══════════════════════════════════════════════════════════════

BEST PRACTICES
────────────────────────────────────────────────────────────────

1. Always check coordinates with Basic 2D Map first
2. Use WGS84 coordinate system (standard GPS format)
3. Keep coordinate precision to 4-6 decimal places
4. Export visualizations for backup
5. Save HTML maps for presentations
6. Use 3D viewer for detailed spatial analysis
7. Choose appropriate base map for your region

═══════════════════════════════════════════════════════════════

FUTURE FEATURES
────────────────────────────────────────────────────────────────

Planned for future versions:
• Heatmaps showing concentration gradients
• 3D terrain overlays (DEM integration)
• Distance calculations between samples
• Spatial clustering analysis
• Export to QGIS/ArcGIS formats
• Integration with Google Earth (KML export)

═══════════════════════════════════════════════════════════════
"""

        text.insert('1.0', help_text)
        text.config(state='disabled')

    def _launch_pyvista_viewer(self):
        """Launch PyVista 3D viewer"""
        if not HAS_PYVISTA:
            response = messagebox.askyesno(
                "PyVista Required",
                "3D Viewer requires PyVista.\n\n"
                "Install with: pip install pyvista\n\n"
                "Do you want to install it now?",
                parent=self.window
            )
            if response:
                self._install_pyvista()
            return

        # Get samples with coordinates
        samples_with_coords = []
        for s in self.app.samples:
            lat = safe_float(s.get('Latitude'))
            lon = safe_float(s.get('Longitude'))
            if lat is not None and lon is not None:
                samples_with_coords.append(s)

        if not samples_with_coords:
            messagebox.showwarning("No Coordinates",
                                 "No samples have Latitude/Longitude data.",
                                 parent=self.window)
            return

        try:
            import numpy as np

            # Create plotter
            plotter = pv.Plotter(window_size=[1200, 800])
            plotter.set_background("white")

            # Prepare data
            points = []
            colors = []

            color_map = {
                "EGYPTIAN (HADDADIN FLOW)": [0, 0, 255],  # Blue
                "EGYPTIAN (ALKALINE / EXOTIC)": [255, 0, 0],  # Red
                "SINAI / TRANSITIONAL": [255, 215, 0],  # Gold
                "SINAI OPHIOLITIC": [255, 165, 0],  # Orange
                "LOCAL LEVANTINE": [0, 255, 0],  # Green
                "HARRAT ASH SHAAM": [128, 0, 128],  # Purple
            }

            for sample in samples_with_coords:
                lat = safe_float(sample.get('Latitude'))
                lon = safe_float(sample.get('Longitude'))
                elev = safe_float(sample.get('Elevation', 0))

                if elev is None:
                    elev = 0

                # Add point (Z scaled for visibility)
                points.append([lon, lat, elev / 1000])

                # Add color
                classification = sample.get('Final_Classification',
                                          sample.get('Auto_Classification', 'UNKNOWN'))
                rgb = color_map.get(classification, [128, 128, 128])
                colors.append(rgb)

            # Create point cloud
            points_array = np.array(points)
            point_cloud = pv.PolyData(points_array)
            point_cloud['colors'] = np.array(colors, dtype=np.uint8)

            # Add to plotter
            point_size = self.point_size_var.get()
            plotter.add_points(point_cloud,
                             scalars='colors',
                             rgb=True,
                             point_size=point_size,
                             render_points_as_spheres=True)

            # Add axes
            if self.show_axes_var.get():
                plotter.add_axes(xlabel='Longitude', ylabel='Latitude', zlabel='Elevation (km)')

            # Add grid
            if self.show_grid_var.get():
                plotter.show_grid()

            # Add title
            plotter.add_text(f"3D Sample Distribution ({len(samples_with_coords)} samples)",
                           position='upper_edge', font_size=14, color='black')

            # Show
            plotter.show()

        except Exception as e:
            messagebox.showerror("3D Viewer Error",
                               f"Error: {str(e)}",
                               parent=self.window)

    def _generate_folium_map(self):
        """Generate interactive Folium map"""
        if not HAS_FOLIUM:
            response = messagebox.askyesno(
                "Folium Required",
                "Interactive maps require Folium, geopandas, and shapely.\n\n"
                "Install with: pip install folium geopandas shapely\n\n"
                "Do you want to install them now?",
                parent=self.window
            )
            if response:
                self._install_folium()
            return

        # Get samples with coordinates
        samples_with_coords = []
        for s in self.app.samples:
            lat = safe_float(s.get('Latitude'))
            lon = safe_float(s.get('Longitude'))
            if lat is not None and lon is not None:
                samples_with_coords.append(s)

        if not samples_with_coords:
            messagebox.showwarning("No Coordinates",
                                 "No samples have Latitude/Longitude data.",
                                 parent=self.window)
            return

        try:
            # Calculate center
            lats = [safe_float(s['Latitude']) for s in samples_with_coords]
            lons = [safe_float(s['Longitude']) for s in samples_with_coords]
            center_lat = sum(lats) / len(lats)
            center_lon = sum(lons) / len(lons)

            # Create map
            m = folium.Map(location=[center_lat, center_lon],
                          zoom_start=8,
                          tiles=self.map_style_var.get())

            # Color map
            color_map = {
                "EGYPTIAN (HADDADIN FLOW)": "blue",
                "EGYPTIAN (ALKALINE / EXOTIC)": "red",
                "SINAI / TRANSITIONAL": "orange",
                "SINAI OPHIOLITIC": "darkred",
                "LOCAL LEVANTINE": "green",
                "HARRAT ASH SHAAM": "purple",
            }

            # Add markers
            for sample in samples_with_coords:
                lat = safe_float(sample['Latitude'])
                lon = safe_float(sample['Longitude'])

                classification = sample.get('Final_Classification',
                                          sample.get('Auto_Classification', 'UNKNOWN'))

                popup_html = f"""
                <b>{sample.get('Sample_ID', 'Unknown')}</b><br>
                <b>Classification:</b> {classification}<br>
                <b>Zr:</b> {sample.get('Zr_ppm', 'N/A')} ppm<br>
                <b>Nb:</b> {sample.get('Nb_ppm', 'N/A')} ppm<br>
                <b>Cr:</b> {sample.get('Cr_ppm', 'N/A')} ppm<br>
                <b>Ni:</b> {sample.get('Ni_ppm', 'N/A')} ppm
                """

                folium.CircleMarker(
                    location=[lat, lon],
                    radius=8,
                    popup=folium.Popup(popup_html, max_width=300),
                    color=color_map.get(classification, "gray"),
                    fill=True,
                    fillColor=color_map.get(classification, "gray"),
                    fillOpacity=0.7
                ).add_to(m)

            # Save
            path = filedialog.asksaveasfilename(
                title="Save Interactive Map",
                defaultextension=".html",
                filetypes=[("HTML files", "*.html")],
                parent=self.window
            )

            if path:
                m.save(path)
                webbrowser.open('file://' + os.path.abspath(path))
                messagebox.showinfo("Map Saved",
                                  f"Map saved and opened!\n\n{path}",
                                  parent=self.window)

        except Exception as e:
            messagebox.showerror("Map Error",
                               f"Error: {str(e)}",
                               parent=self.window)

    def _generate_basic_2d_map(self):
        """Generate basic 2D map using matplotlib"""
        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
        except ImportError:
            messagebox.showerror("Matplotlib Required",
                               "Basic 2D map requires matplotlib.",
                               parent=self.window)
            return

        # Get samples
        samples_with_coords = []
        for s in self.app.samples:
            lat = safe_float(s.get('Latitude'))
            lon = safe_float(s.get('Longitude'))
            if lat is not None and lon is not None:
                samples_with_coords.append(s)

        if not samples_with_coords:
            messagebox.showwarning("No Coordinates",
                                 "No samples have Latitude/Longitude data.",
                                 parent=self.window)
            return

        # Create window
        map_window = tk.Toplevel(self.window)
        map_window.title("Basic 2D Map")
        map_window.geometry("1000x800")

        # Create figure
        fig, ax = plt.subplots(figsize=(10, 8))

        color_map = {
            "EGYPTIAN (HADDADIN FLOW)": "blue",
            "EGYPTIAN (ALKALINE / EXOTIC)": "red",
            "SINAI / TRANSITIONAL": "gold",
            "SINAI OPHIOLITIC": "orange",
            "LOCAL LEVANTINE": "green",
            "HARRAT ASH SHAAM": "purple",
        }

        # Plot
        for sample in samples_with_coords:
            lat = safe_float(sample['Latitude'])
            lon = safe_float(sample['Longitude'])
            classification = sample.get('Final_Classification',
                                      sample.get('Auto_Classification', 'UNKNOWN'))

            ax.scatter(lon, lat,
                      c=color_map.get(classification, "gray"),
                      s=100, alpha=0.7,
                      edgecolors='black', linewidths=0.5)

        ax.set_xlabel('Longitude', fontsize=12, fontweight='bold')
        ax.set_ylabel('Latitude', fontsize=12, fontweight='bold')
        ax.set_title(f'Sample Distribution ({len(samples_with_coords)} samples)',
                    fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        plt.tight_layout()

        # Embed
        canvas = FigureCanvasTkAgg(fig, map_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        toolbar_frame = tk.Frame(map_window)
        toolbar_frame.pack(side=tk.BOTTOM, fill=tk.X)
        toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
        toolbar.update()

    def _install_pyvista(self):
        """Install PyVista dependency"""
        self._install_packages(["pyvista"], "PyVista")

    def _install_folium(self):
        """Install Folium and geopandas dependencies"""
        self._install_packages(["folium", "geopandas", "shapely"], "Folium/Geopandas")

    def _install_packages(self, packages, feature_name):
        """Install packages using the plugin manager"""
        # First try to use plugin manager if available
        if hasattr(self.app, 'open_plugin_manager'):
            # We can trigger installation through plugin manager
            messagebox.showinfo(
                "Install via Plugin Manager",
                f"Please install {feature_name} dependencies:\n\n"
                f"Packages: {', '.join(packages)}\n\n"
                f"1. Go to Tools → Plugin Manager\n"
                f"2. Find '3D/GIS Viewer' plugin\n"
                f"3. Click 'Install' button\n"
                f"4. Restart application after installation",
                parent=self.window
            )
            self.window.destroy()  # Close current window
            self.app.open_plugin_manager()
        else:
            # Manual installation instructions
            pip_cmd = "pip install " + " ".join(packages)
            python_cmd = "python -m pip install " + " ".join(packages)

            messagebox.showinfo(
                "Install Manually",
                f"To install {feature_name}, run in terminal:\n\n"
                f"Option 1 (recommended):\n"
                f"  {pip_cmd}\n\n"
                f"Option 2 (if above doesn't work):\n"
                f"  {python_cmd}\n\n"
                f"After installation, restart the application.",
                parent=self.window
            )
