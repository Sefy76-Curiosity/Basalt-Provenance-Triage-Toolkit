"""
GIS Console - Spatial analysis for archaeological/geological data
"""
import tkinter as tk
from tkinter import ttk, filedialog
import subprocess
import tempfile
import os
import json

# Check for GIS packages
HAS_GEOPANDAS = False
HAS_FOLIUM = False
HAS_CONTEXTILY = False

try:
    import geopandas as gpd
    from shapely.geometry import Point
    HAS_GEOPANDAS = True
except:
    pass

try:
    import folium
    HAS_FOLIUM = True
except:
    pass

try:
    import contextily as ctx
    HAS_CONTEXTILY = True
except:
    pass

PLUGIN_INFO = {
    'id': 'gis_console',
    'name': 'GIS Console',
    'category': 'console',
    'icon': '🗺️',
    'version': '1.0',
    'requires': ['geopandas', 'folium', 'contextily'],
    'description': 'Spatial analysis and mapping for archaeological/geological data'
}

class GISConsolePlugin:
    def __init__(self, main_app):
        self.app = main_app
        self.history = []
        self.history_index = -1
        self.gdf = None  # Will hold GeoDataFrame of samples

    def create_tab(self, parent):
        """Create GIS console UI"""
        # Check dependencies
        missing = []
        if not HAS_GEOPANDAS:
            missing.append("geopandas")
        if not HAS_FOLIUM:
            missing.append("folium")
        if not HAS_CONTEXTILY:
            missing.append("contextily")

        if missing:
            # Show installation message
            frame = ttk.Frame(parent)
            frame.pack(fill=tk.BOTH, expand=True)

            msg = f"""
╔══════════════════════════════════════════════════════════╗
║               GIS Console - Missing Dependencies        ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  Missing packages: {', '.join(missing)}                  ║
║                                                          ║
║  Install with:                                           ║
║    pip install {' '.join(missing)}                       ║
║                                                          ║
║  Or install all at once:                                 ║
║    pip install geopandas folium contextily               ║
║                                                          ║
║  These packages enable:                                  ║
║    • Point-in-polygon analysis                          ║
║    • Interactive maps (folium)                          ║
║    • Base maps (contextily)                             ║
║    • Shapefile import/export                            ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
"""
            label = tk.Label(frame, text=msg, font=('Consolas', 10),
                           justify=tk.LEFT, bg='#1e1e1e', fg='#d4d4d4')
            label.pack(expand=True)
            return

        # Create output area
        output_frame = ttk.Frame(parent)
        output_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.output = tk.Text(
            output_frame,
            bg='#1e1e1e',
            fg='#d4d4d4',
            font=('Consolas', 10),
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(output_frame, orient=tk.VERTICAL,
                                  command=self.output.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.output.configure(yscrollcommand=scrollbar.set)

        # Quick commands bar
        quick_frame = ttk.Frame(parent)
        quick_frame.pack(fill=tk.X, padx=5, pady=2)

        commands = [
            ("🗺️ Map", self._show_map),
            ("📍 Points", lambda: self.execute("show_points()")),
            ("📊 Buffer", self._buffer_dialog),
            ("🔍 Spatial Join", self._spatial_join_dialog),
            ("💾 Export", self._export_shapefile),
        ]

        for text, cmd in commands:
            ttk.Button(quick_frame, text=text, command=cmd).pack(side=tk.LEFT, padx=2)

        # Input area
        input_frame = ttk.Frame(parent)
        input_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(input_frame, text="GIS>", font=('Consolas', 10, 'bold')).pack(side=tk.LEFT, padx=2)

        self.input = tk.Text(
            input_frame,
            height=3,
            bg='#2d2d2d',
            fg='#ffffff',
            font=('Consolas', 10),
            insertbackground='white',
            wrap=tk.WORD
        )
        self.input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Bind keys
        self.input.bind('<Return>', self._on_enter)
        self.input.bind('<Shift-Return>', self._insert_newline)
        self.input.bind('<Up>', self._history_up)
        self.input.bind('<Down>', self._history_down)

        # Button frame
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(button_frame, text="Run",
                  command=self.execute_input).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Clear",
                  command=self._clear_screen).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Help",
                  command=self._show_help).pack(side=tk.LEFT, padx=2)

        # Create GeoDataFrame from samples
        self._create_gdf()
        self._print_welcome()

    def _create_gdf(self):
        """Create GeoDataFrame from samples with coordinates"""
        samples = self.app.data_hub.get_all()
        if not samples:
            return

        # Find samples with coordinates
        points = []
        data = []

        for i, s in enumerate(samples):
            lat = None
            lon = None

            # Check common coordinate fields
            if 'Latitude' in s and 'Longitude' in s:
                try:
                    lat = float(s['Latitude'])
                    lon = float(s['Longitude'])
                except:
                    pass
            elif 'lat' in s and 'lon' in s:
                try:
                    lat = float(s['lat'])
                    lon = float(s['lon'])
                except:
                    pass
            elif 'Y' in s and 'X' in s:
                try:
                    lat = float(s['Y'])
                    lon = float(s['X'])
                except:
                    pass

            if lat and lon:
                points.append(Point(lon, lat))
                data.append({
                    'Sample_ID': s.get('Sample_ID', f'SAMPLE_{i}'),
                    'Classification': s.get('Auto_Classification', 'UNKNOWN'),
                    'Zr_ppm': s.get('Zr_ppm', 0),
                    'Nb_ppm': s.get('Nb_ppm', 0),
                    'index': i
                })

        if points:
            self.gdf = gpd.GeoDataFrame(data, geometry=points, crs='EPSG:4326')
            self.gdf['x'] = self.gdf.geometry.x
            self.gdf['y'] = self.gdf.geometry.y

    def _print_welcome(self):
        """Print welcome message"""
        if self.gdf is None or len(self.gdf) == 0:
            welcome = """
╔══════════════════════════════════════════════════════════╗
║                    GIS Console                           ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  ⚠️ No samples with coordinates found                    ║
║                                                          ║
║  To use GIS features, add samples with:                  ║
║    • Latitude/Longitude                                  ║
║    • lat/lon                                             ║
║    • Y/X                                                 ║
║                                                          ║
║  Once you have coordinates, the GeoDataFrame 'gdf'       ║
║  will be available for spatial analysis.                 ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
"""
        else:
            bounds = self.gdf.total_bounds
            welcome = f"""
╔══════════════════════════════════════════════════════════╗
║                    GIS Console                           ║
╠══════════════════════════════════════════════════════════╣
║  📍 Points: {len(self.gdf)} samples with coordinates      ║
║  🌍 Bounds:                                              ║
║     West: {bounds[0]:.4f}   East: {bounds[2]:.4f}        ║
║     South: {bounds[1]:.4f}  North: {bounds[3]:.4f}       ║
║                                                          ║
║  Available commands:                                     ║
║    gdf.head()              - View first 5 rows          ║
║    show_points()           - Display points on map      ║
║    buffer(1000)            - Create 1km buffers         ║
║    spatial_join(shp)       - Join with shapefile        ║
║    export_shapefile()      - Save as shapefile          ║
║                                                          ║
║  Examples:                                               ║
║    >>> gdf.crs                                            ║
║    >>> gdf[gdf['Classification'].str.contains('SINAI')]  ║
║    >>> gdf.distance(gdf.iloc[0].geometry)                ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
"""
        self._print_output(welcome)

    def _show_help(self):
        """Show detailed help"""
        help_text = """
🗺️ GIS CONSOLE HELP
═══════════════════════════════════════════════════════════

GEO DATAFRAME (gdf):
  Your samples with coordinates are stored in 'gdf' - a GeoPandas
  GeoDataFrame with methods for spatial analysis.

BASIC OPERATIONS:
  gdf.head()                    # View first 5 rows
  gdf.tail(10)                  # View last 10 rows
  gdf.columns                   # List column names
  gdf.crs                       # Show coordinate system
  gdf.total_bounds              # Show map bounds
  gdf.geometry.x                # Get longitude values
  gdf.geometry.y                # Get latitude values

FILTERING:
  # By classification
  gdf[gdf['Classification'] == 'SINAI_OPHIOLITIC']

  # By value
  gdf[gdf['Zr_ppm'] > 200]

  # By location (within bounding box)
  gdf.cx[-122.5:-122.0, 37.5:38.0]

SPATIAL OPERATIONS:
  # Buffer (in meters - need projected CRS)
  gdf.to_crs('EPSG:3857').buffer(1000)

  # Distance between points
  gdf.distance(gdf.iloc[0].geometry)

  # Convex hull of all points
  gdf.unary_union.convex_hull

PLOTTING:
  show_points()                  # Interactive map
  gdf.plot()                     # Simple static plot

  # With basemap (contextily)
  import contextily as ctx
  ax = gdf.plot(figsize=(10,10))
  ctx.add_basemap(ax)

EXPORT:
  export_shapefile()             # Save as shapefile
  gdf.to_file('sites.geojson', driver='GeoJSON')

💡 TIPS:
  • Use EPSG:4326 for lat/lon, EPSG:3857 for web maps
  • Always check CRS before buffer/distance operations
"""
        self._print_output(help_text)

    def _show_map(self):
        """Show interactive map with points"""
        if self.gdf is None or len(self.gdf) == 0:
            self._print_output("No points to display\n", error=True)
            return

        try:
            import folium

            # Center map on mean coordinates
            center_lat = self.gdf.geometry.y.mean()
            center_lon = self.gdf.geometry.x.mean()

            m = folium.Map(location=[center_lat, center_lon], zoom_start=10)

            # Add points
            for idx, row in self.gdf.iterrows():
                color = 'red'
                if 'SINAI' in row['Classification']:
                    color = 'blue'
                elif 'EGYPT' in row['Classification']:
                    color = 'green'

                popup = f"""
                <b>Sample:</b> {row['Sample_ID']}<br>
                <b>Classification:</b> {row['Classification']}<br>
                <b>Zr:</b> {row['Zr_ppm']} ppm<br>
                <b>Nb:</b> {row['Nb_ppm']} ppm
                """

                folium.Marker(
                    [row.geometry.y, row.geometry.x],
                    popup=popup,
                    icon=folium.Icon(color=color)
                ).add_to(m)

            # Save to temp file and open
            with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as f:
                m.save(f.name)
                import webbrowser
                webbrowser.open('file://' + f.name)

            self._print_output(f"✓ Map opened in browser with {len(self.gdf)} points\n")

        except Exception as e:
            self._print_output(f"Error creating map: {str(e)}\n", error=True)

    def _buffer_dialog(self):
        """Show dialog for buffer analysis"""
        dialog = tk.Toplevel(self.app.root)
        dialog.title("Buffer Analysis")
        dialog.geometry("400x300")
        dialog.transient(self.app.root)

        main = ttk.Frame(dialog, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="Buffer distance (meters):").pack(anchor=tk.W)
        dist_var = tk.StringVar(value="1000")
        ttk.Entry(main, textvariable=dist_var).pack(fill=tk.X, pady=5)

        ttk.Label(main, text="Apply to:").pack(anchor=tk.W, pady=(10,0))
        target_var = tk.StringVar(value="all")
        ttk.Radiobutton(main, text="All points", variable=target_var,
                       value="all").pack(anchor=tk.W)
        ttk.Radiobutton(main, text="Selected classification",
                       variable=target_var, value="selected").pack(anchor=tk.W)

        class_var = tk.StringVar()
        classes = self.gdf['Classification'].unique() if self.gdf is not None else []
        ttk.Combobox(main, textvariable=class_var, values=list(classes)).pack(fill=tk.X, pady=5)

        def do_buffer():
            dist = float(dist_var.get())
            if target_var.get() == "all":
                cmd = f"gdf.to_crs('EPSG:3857').buffer({dist})"
            else:
                cmd = f"gdf[gdf['Classification'] == '{class_var.get()}'].to_crs('EPSG:3857').buffer({dist})"
            dialog.destroy()
            self.execute(cmd)

        ttk.Button(main, text="Create Buffer", command=do_buffer).pack(pady=10)

    def _spatial_join_dialog(self):
        """Show dialog for spatial join"""
        dialog = tk.Toplevel(self.app.root)
        dialog.title("Spatial Join")
        dialog.geometry("500x400")
        dialog.transient(self.app.root)

        main = ttk.Frame(dialog, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="Join with shapefile/GeoJSON:").pack(anchor=tk.W)

        self.join_path_var = tk.StringVar()
        ttk.Entry(main, textvariable=self.join_path_var).pack(fill=tk.X, pady=5)

        def browse():
            path = filedialog.askopenfilename(
                filetypes=[
                    ("Shapefiles", "*.shp"),
                    ("GeoJSON", "*.geojson"),
                    ("All files", "*.*")
                ]
            )
            if path:
                self.join_path_var.set(path)

        ttk.Button(main, text="Browse", command=browse).pack(pady=5)

        ttk.Label(main, text="Join type:").pack(anchor=tk.W, pady=(10,0))
        join_type_var = tk.StringVar(value="within")
        ttk.Radiobutton(main, text="Points within polygons",
                       variable=join_type_var, value="within").pack(anchor=tk.W)
        ttk.Radiobutton(main, text="Nearest neighbor",
                       variable=join_type_var, value="nearest").pack(anchor=tk.W)

        def do_join():
            path = self.join_path_var.get()
            if not path:
                return

            if join_type_var.get() == "within":
                cmd = f"""
import geopandas as gpd
polygons = gpd.read_file(r'{path}')
joined = gpd.sjoin(gdf, polygons, how='left', predicate='within')
print(f"Joined {len(joined)} points")
joined.head()
"""
            else:
                cmd = f"""
import geopandas as gpd
polygons = gpd.read_file(r'{path}')
joined = gpd.sjoin_nearest(gdf, polygons, how='left')
print(f"Joined {len(joined)} points")
joined.head()
"""
            dialog.destroy()
            self.execute(cmd)

        ttk.Button(main, text="Run Join", command=do_join).pack(pady=10)

    def _export_shapefile(self):
        """Export as shapefile"""
        if self.gdf is None or len(self.gdf) == 0:
            self._print_output("No data to export\n", error=True)
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".shp",
            filetypes=[("Shapefile", "*.shp"), ("GeoJSON", "*.geojson")]
        )

        if path:
            try:
                self.gdf.to_file(path)
                self._print_output(f"✓ Exported to {path}\n")
            except Exception as e:
                self._print_output(f"Export failed: {str(e)}\n", error=True)

    def execute_input(self):
        """Execute command from input"""
        code = self.input.get("1.0", tk.END).strip()
        if code:
            self.execute(code)

    def execute(self, code):
        """Execute GIS command"""
        if not code:
            return

        self.history.append(code)
        self.history_index = len(self.history)

        self._print_output(f"GIS> {code}\n")
        self.input.delete("1.0", tk.END)

        # Create a local namespace with gdf and other useful objects
        local_ns = {
            'gdf': self.gdf,
            'gpd': gpd,
            'Point': Point,
            'show_points': self._show_map
        }

        # Capture output
        from contextlib import redirect_stdout, redirect_stderr
        import io

        stdout = io.StringIO()
        stderr = io.StringIO()

        try:
            with redirect_stdout(stdout), redirect_stderr(stderr):
                # Special commands
                if code == 'show_points()':
                    self._show_map()
                else:
                    result = eval(code, globals(), local_ns)
                    if result is not None:
                        print(result)

            output = stdout.getvalue()
            if output:
                self._print_output(output)

            error = stderr.getvalue()
            if error:
                self._print_output(error, error=True)

        except Exception as e:
            self._print_output(f"Error: {str(e)}\n", error=True)

        self._print_output("\n")

    def _print_output(self, text, error=False):
        """Print to output"""
        self.output.config(state=tk.NORMAL)
        if error:
            self.output.insert(tk.END, text, 'error')
            self.output.tag_config('error', foreground='#f48771')
        else:
            self.output.insert(tk.END, text)
        self.output.see(tk.END)
        self.output.config(state=tk.DISABLED)

    def _on_enter(self, event):
        """Handle Enter key"""
        if not (event.state & 0x1):  # Not Shift
            self.execute_input()
            return "break"
        return None

    def _insert_newline(self, event):
        """Insert newline on Shift+Enter"""
        self.input.insert(tk.INSERT, "\n")
        return "break"

    def _history_up(self, event):
        """Navigate history up"""
        if self.history and self.history_index > 0:
            self.history_index -= 1
            self.input.delete("1.0", tk.END)
            self.input.insert("1.0", self.history[self.history_index])
        return "break"

    def _history_down(self, event):
        """Navigate history down"""
        if self.history and self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.input.delete("1.0", tk.END)
            self.input.insert("1.0", self.history[self.history_index])
        elif self.history_index == len(self.history) - 1:
            self.history_index = len(self.history)
            self.input.delete("1.0", tk.END)
        return "break"

    def _clear_screen(self):
        """Clear output"""
        self.output.config(state=tk.NORMAL)
        self.output.delete("1.0", tk.END)
        self.output.config(state=tk.DISABLED)
        self._print_welcome()

def register_plugin(main_app):
    """Register this plugin"""
    plugin = GISConsolePlugin(main_app)

    if hasattr(main_app.center, 'add_console_plugin'):
        main_app.center.add_console_plugin(
            console_name="GIS",
            console_icon="🗺️",
            console_instance=plugin
        )
    return None
