"""
Universal Exporter Plugin - File Menu Integration
Export sample data, classification results, or plots to CSV, Excel, PDF, PNG, SVG,
JSON, GeoJSON, KML, Shapefile, TIFF, HDF5, NetCDF, and LaTeX.

Author: (Your Name)
Category: software (to appear in the File menu)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
import json
import os
from pathlib import Path

# Optional libraries – we'll check availability later
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import openpyxl
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, Paragraph
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    import matplotlib
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    import PIL
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import geopandas as gpd
    from shapely.geometry import Point
    GEOPANDAS_AVAILABLE = True
except ImportError:
    GEOPANDAS_AVAILABLE = False

try:
    import fiona
    FIONA_AVAILABLE = True
except ImportError:
    FIONA_AVAILABLE = False

try:
    import h5py
    H5PY_AVAILABLE = True
except ImportError:
    H5PY_AVAILABLE = False

try:
    import netCDF4 as nc
    NETCDF4_AVAILABLE = True
except ImportError:
    NETCDF4_AVAILABLE = False

try:
    import rasterio
    HAS_RASTERIO = True
except ImportError:
    HAS_RASTERIO = False

# For KML we might use simplekml as an alternative if geopandas doesn't support KML directly
try:
    import simplekml
    SIMPLEKML_AVAILABLE = True
except ImportError:
    SIMPLEKML_AVAILABLE = False


PLUGIN_INFO = {
    'id': 'universal_exporter',
    'name': 'Universal Exporter',
    'category': 'software',
    'icon': '💾',
    'version': '2.1',  # Minor version bump for the new features
    'requires': [],
    'description': 'Export samples, results, or plots to many scientific formats.'
}


class UniversalExporterPlugin:
    """Add-on that provides a universal export dialog."""

    def __init__(self, parent_app):
        self.app = parent_app

    def show(self):
        """Open the export dialog (called from menu)."""
        self.dialog = tk.Toplevel(self.app.root)
        self.dialog.title("Universal Exporter")
        self.dialog.geometry("550x700")  # Slightly taller to accommodate the format note
        self.dialog.resizable(False, False)

        # Header
        ttk.Label(self.dialog, text="💾 Export Data / Plots",
                 font=("Arial", 14, "bold")).pack(pady=10)

        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill="both", expand=True)

        # ---------- What to export ----------
        ttk.Label(main_frame, text="Export what?", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        self.export_var = tk.StringVar(value="samples")
        ttk.Radiobutton(main_frame, text="Sample data only", variable=self.export_var,
                       value="samples").grid(row=1, column=0, sticky="w")
        ttk.Radiobutton(main_frame, text="Classification results (if available)", variable=self.export_var,
                       value="classification").grid(row=2, column=0, sticky="w")
        ttk.Radiobutton(main_frame, text="Both (merged)", variable=self.export_var,
                       value="both").grid(row=3, column=0, sticky="w")
        ttk.Radiobutton(main_frame, text="Current plot (if available)", variable=self.export_var,
                       value="plot").grid(row=4, column=0, sticky="w")

        # ---------- Format selection ----------
        ttk.Label(main_frame, text="Format", font=("Arial", 10, "bold")).grid(row=0, column=1, sticky="w", padx=20, pady=5)
        self.format_var = tk.StringVar(value="csv")

        # Keep a list of (row_index, format_name, var_value, enabled_condition, tooltip)
        formats = [
            (1, "CSV (.csv)", "csv", True, ""),
            (2, "Excel (.xlsx)", "excel", (PANDAS_AVAILABLE or OPENPYXL_AVAILABLE), "Requires pandas/openpyxl"),
            (3, "PDF table", "pdf", REPORTLAB_AVAILABLE, "Requires reportlab"),
            (4, "PNG image", "png", MATPLOTLIB_AVAILABLE, "Requires matplotlib"),
            (5, "SVG image", "svg", MATPLOTLIB_AVAILABLE, "Requires matplotlib"),
            (6, "JSON (.json)", "json", True, ""),
            (7, "GeoJSON (.geojson)", "geojson", GEOPANDAS_AVAILABLE, "Requires geopandas + fiona + shapely"),
            (8, "KML (.kml)", "kml", (GEOPANDAS_AVAILABLE or SIMPLEKML_AVAILABLE), "Requires geopandas or simplekml"),
            (9, "Shapefile (.shp)", "shp", GEOPANDAS_AVAILABLE, "Requires geopandas + fiona + shapely"),
            (10, "GeoTIFF (.tif)", "geotiff", (MATPLOTLIB_AVAILABLE and PIL_AVAILABLE and HAS_RASTERIO), "Requires matplotlib + PIL + rasterio"),
            (11, "TIFF image (.tif)", "tiff", (MATPLOTLIB_AVAILABLE and PIL_AVAILABLE), "Requires matplotlib + PIL"),
            (12, "HDF5 (.h5)", "hdf5", H5PY_AVAILABLE, "Requires h5py"),
            (13, "NetCDF (.nc)", "netcdf", NETCDF4_AVAILABLE, "Requires netCDF4"),
            (14, "LaTeX table (.tex)", "latex", True, ""),
        ]

        for row, label, value, enabled, tooltip in formats:
            rb = ttk.Radiobutton(main_frame, text=label, variable=self.format_var,
                                 value=value, state="normal" if enabled else "disabled")
            rb.grid(row=row, column=1, sticky="w", padx=20, pady=2)
            if not enabled:
                ttk.Label(main_frame, text="(missing library)", foreground="gray").grid(row=row, column=2, sticky="w", padx=5)
            # Optional tooltip (not implemented in basic tkinter, but could be added with a hover label)

        # ---------- Options ----------
        ttk.Label(main_frame, text="Options", font=("Arial", 10, "bold")).grid(row=14, column=0, columnspan=3, sticky="w", pady=(15,5))
        self.include_headers_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(main_frame, text="Include column headers (where applicable)",
                       variable=self.include_headers_var).grid(row=15, column=0, columnspan=3, sticky="w")

        # Spatial note (if no coordinates, spatial formats will be disabled later in do_export)
        self.spatial_note = ttk.Label(main_frame, text="Note: Spatial formats require 'Latitude'/'Longitude' columns.",
                                      foreground="blue", font=("Arial", 8))
        self.spatial_note.grid(row=16, column=0, columnspan=3, sticky="w", pady=5)

        # Format-specific note (e.g., for NetCDF/HDF5 handling)
        self.format_note_var = tk.StringVar()
        self.format_note_label = ttk.Label(main_frame, textvariable=self.format_note_var,
                                           foreground="gray", font=("Arial", 8))
        self.format_note_label.grid(row=17, column=0, columnspan=3, sticky="w", pady=2)

        # Update the note when format changes
        self.format_var.trace('w', self.update_format_note)
        self.update_format_note()  # initial update

        # ---------- Buttons ----------
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="Export", command=self.do_export).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.dialog.destroy).pack(side="left", padx=5)

    def update_format_note(self, *args):
        """Update the format-specific note based on the selected format."""
        fmt = self.format_var.get()
        notes = {
            'netcdf': "Note: In NetCDF export, numeric missing values are replaced with 0, strings with empty string.",
            'hdf5': "Note: Columns with mixed data types will be stored as strings. A warning will appear if detected.",
            'geotiff': "Note: GeoTIFF exports the first numeric column as a raster grid.",
            'bufr': "Note: BUFR export is a placeholder - requires eccodes library.",
        }
        self.format_note_var.set(notes.get(fmt, ""))

    # ----------------------------------------------------------------------
    # Core export logic
    # ----------------------------------------------------------------------
    def do_export(self):
        what = self.export_var.get()
        fmt = self.format_var.get()

        # Validate we have something to export
        if what == "plot":
            if not self._has_plot():
                messagebox.showerror("Error", "No plot found to export.")
                return
        else:
            if not self.app.samples:
                messagebox.showerror("Error", "No sample data available.")
                return

        # Special validation for spatial formats
        if fmt in ("geojson", "kml", "shp"):
            if not self._has_coordinates():
                messagebox.showerror("Error",
                    "Spatial format selected but no coordinate columns found.\n"
                    "Please ensure your data has 'Latitude' and 'Longitude' (or 'X'/'Y') columns.")
                return

        # Ask for save location
        file_ext = self._get_extension(fmt)
        if not file_ext:
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=file_ext,
            filetypes=[(fmt.upper(), f"*{file_ext}"), ("All files", "*.*")]
        )
        if not filename:
            return

        # Dispatch to appropriate export method
        try:
            if fmt == "csv":
                self._export_csv(filename, what)
            elif fmt == "excel":
                self._export_excel(filename, what)
            elif fmt == "pdf":
                self._export_pdf(filename, what)
            elif fmt == "png":
                self._export_image(filename, fmt)
            elif fmt == "svg":
                self._export_image(filename, fmt)
            elif fmt == "json":
                self._export_json(filename, what)
            elif fmt == "geojson":
                self._export_geojson(filename, what)
            elif fmt == "kml":
                self._export_kml(filename, what)
            elif fmt == "shp":
                self._export_shapefile(filename, what)
            elif fmt == "tiff":
                self._export_image(filename, "tiff")
            elif fmt == "hdf5":
                self._export_hdf5(filename, what)
            elif fmt == "netcdf":
                self._export_netcdf(filename, what)
            elif fmt == "latex":
                self._export_latex(filename, what)
            else:
                messagebox.showerror("Error", f"Unsupported format: {fmt}")
                return

            messagebox.showinfo("Success", f"Exported successfully to:\n{filename}")
            self.dialog.destroy()
        except Exception as e:
            messagebox.showerror("Export Failed", f"An error occurred:\n{str(e)}")

    def _get_extension(self, fmt):
        extensions = {
            "csv": ".csv", "excel": ".xlsx", "pdf": ".pdf",
            "png": ".png", "svg": ".svg", "json": ".json",
            "geojson": ".geojson", "kml": ".kml", "shp": ".shp",
            "geotiff": ".tif", "tiff": ".tif", "hdf5": ".h5",
            "netcdf": ".nc", "latex": ".tex"
        }
        return extensions.get(fmt)

    def _get_data_export(self, what):
        """Return list of dicts for samples/classification/both."""
        samples = self.app.samples
        if what == "samples":
            return samples

        classification_data = []
        if hasattr(self.app, 'classification_results') and self.app.classification_results:
            classification_data = self.app.classification_results
        elif hasattr(self.app, 'results') and self.app.results:
            classification_data = self.app.results

        if what == "classification":
            return classification_data if classification_data else []

        if what == "both":
            if not classification_data:
                return samples
            class_dict = {item.get('Sample_ID'): item for item in classification_data if 'Sample_ID' in item}
            merged = []
            for s in samples:
                merged_row = s.copy()
                sid = s.get('Sample_ID')
                if sid in class_dict:
                    merged_row.update(class_dict[sid])
                merged.append(merged_row)
            return merged
        return []

    def _has_plot(self):
        return (hasattr(self.app, 'plot_canvas') and self.app.plot_canvas) or \
               (hasattr(self.app, 'figure') and self.app.figure) or \
               (hasattr(self.app, 'ax') and self.app.ax)

    def _get_figure(self):
        if hasattr(self.app, 'figure') and self.app.figure:
            return self.app.figure
        if hasattr(self.app, 'plot_canvas') and hasattr(self.app.plot_canvas, 'figure'):
            return self.app.plot_canvas.figure
        if hasattr(self.app, 'ax') and hasattr(self.app.ax, 'figure'):
            return self.app.ax.figure
        return None

    def _has_coordinates(self):
        """Check if the first sample has latitude/longitude or x/y columns."""
        if not self.app.samples:
            return False
        sample = self.app.samples[0]
        keys = [k.lower() for k in sample.keys()]
        return ('latitude' in keys and 'longitude' in keys) or ('x' in keys and 'y' in keys)

    def _get_coordinate_columns(self):
        """Return the names of the columns to use for longitude/X and latitude/Y."""
        if not self.app.samples:
            return None, None
        sample = self.app.samples[0]
        keys_lower = {k.lower(): k for k in sample.keys()}
        if 'latitude' in keys_lower and 'longitude' in keys_lower:
            return keys_lower['longitude'], keys_lower['latitude']  # (lon, lat)
        if 'x' in keys_lower and 'y' in keys_lower:
            return keys_lower['x'], keys_lower['y']
        return None, None

    # ----------------------------------------------------------------------
    # Existing export methods (CSV, Excel, PDF, PNG, SVG)
    # ----------------------------------------------------------------------
    def _export_csv(self, filename, what):
        data = self._get_data_export(what)
        if not data:
            raise ValueError("No data to export.")
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            if self.include_headers_var.get():
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            else:
                writer = csv.writer(f)
                for row in data:
                    writer.writerow(row.values())

    def _export_excel(self, filename, what):
        data = self._get_data_export(what)
        if not data:
            raise ValueError("No data to export.")
        if PANDAS_AVAILABLE:
            df = pd.DataFrame(data)
            df.to_excel(filename, index=False, engine='openpyxl')
        elif OPENPYXL_AVAILABLE:
            wb = openpyxl.Workbook()
            ws = wb.active
            if self.include_headers_var.get():
                ws.append(list(data[0].keys()))
            for row in data:
                ws.append(list(row.values()))
            wb.save(filename)
        else:
            raise ImportError("No Excel library available (pandas or openpyxl).")

    def _export_pdf(self, filename, what):
        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab is not installed.")
        data = self._get_data_export(what)
        if not data:
            raise ValueError("No data to export.")
        table_data = []
        if self.include_headers_var.get():
            table_data.append(list(data[0].keys()))
        for row in data:
            table_data.append([str(v) for v in row.values()])

        doc = SimpleDocTemplate(filename, pagesize=landscape(A4))
        elements = []
        styles = getSampleStyleSheet()
        title = Paragraph(f"Export: {what}", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 0.2*inch))

        if table_data:
            num_cols = len(table_data[0])
            col_widths = [doc.width / num_cols] * num_cols
            table = Table(table_data, colWidths=col_widths, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.grey),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,0), 10),
                ('BOTTOMPADDING', (0,0), (-1,0), 8),
                ('BACKGROUND', (0,1), (-1,-1), colors.beige),
                ('GRID', (0,0), (-1,-1), 1, colors.black)
            ]))
            elements.append(table)
        doc.build(elements)

    def _export_image(self, filename, fmt):
        fig = self._get_figure()
        if fig is None:
            raise ValueError("No matplotlib figure found.")
        # fmt can be 'png', 'svg', 'tiff'
        if fmt == 'tiff':
            # Use PIL to save as TIFF; matplotlib may not have native TIFF support
            fig.savefig(filename, format='png', dpi=300, bbox_inches='tight')  # save as PNG first
            # Convert to TIFF using PIL
            img = PIL.Image.open(filename)
            img.save(filename.replace('.png', '.tif'), format='TIFF')
            os.remove(filename)  # remove temporary PNG
        else:
            fig.savefig(filename, format=fmt, dpi=300, bbox_inches='tight')

    # ----------------------------------------------------------------------
    # New export methods
    # ----------------------------------------------------------------------
    def _export_json(self, filename, what):
        data = self._get_data_export(what)
        if not data:
            raise ValueError("No data to export.")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _export_geojson(self, filename, what):
        if not GEOPANDAS_AVAILABLE:
            raise ImportError("geopandas not available.")
        data = self._get_data_export(what)
        if not data:
            raise ValueError("No data to export.")
        lon_col, lat_col = self._get_coordinate_columns()
        # Create a GeoDataFrame
        df = pd.DataFrame(data)
        geometry = [Point(x, y) for x, y in zip(df[lon_col], df[lat_col])]
        gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
        # Drop the original coordinate columns if desired? Keep them.
        gdf.to_file(filename, driver='GeoJSON')

    def _export_kml(self, filename, what):
        # Try using geopandas (with KML driver) or simplekml
        data = self._get_data_export(what)
        if not data:
            raise ValueError("No data to export.")
        lon_col, lat_col = self._get_coordinate_columns()

        if GEOPANDAS_AVAILABLE:
            df = pd.DataFrame(data)
            geometry = [Point(x, y) for x, y in zip(df[lon_col], df[lat_col])]
            gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
            gdf.to_file(filename, driver='KML')
        elif SIMPLEKML_AVAILABLE:
            kml = simplekml.Kml()
            for row in data:
                pnt = kml.newpoint(name=row.get('Sample_ID', ''),
                                   coords=[(float(row[lon_col]), float(row[lat_col]))])
                # Add all other fields as description or extended data
                desc = "\n".join(f"{k}: {v}" for k, v in row.items() if k not in (lon_col, lat_col))
                pnt.description = desc
            kml.save(filename)
        else:
            raise ImportError("No library available for KML export (geopandas or simplekml).")

    def _export_shapefile(self, filename, what):
        if not GEOPANDAS_AVAILABLE:
            raise ImportError("geopandas not available.")
        data = self._get_data_export(what)
        if not data:
            raise ValueError("No data to export.")
        lon_col, lat_col = self._get_coordinate_columns()
        df = pd.DataFrame(data)
        geometry = [Point(x, y) for x, y in zip(df[lon_col], df[lat_col])]
        gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
        # Shapefile is actually a set of files; we'll save with .shp base
        gdf.to_file(filename, driver='ESRI Shapefile')

    def _detect_mixed_types(self, df):
        """Return list of column names that have mixed numeric/string data."""
        mixed_cols = []
        for col in df.columns:
            if df[col].dtype == 'object':
                # Check if values are mostly numbers but some are strings
                # We'll consider a column mixed if after dropping NA, some can be converted to numeric and some can't.
                non_na = df[col].dropna()
                if len(non_na) == 0:
                    continue
                # Try to convert to numeric, coerce errors to NaN
                numeric = pd.to_numeric(non_na, errors='coerce')
                # If some values become NaN, they were non-numeric; if all are NaN, it's all non-numeric
                # We consider mixed if there is at least one numeric and at least one non-numeric
                has_numeric = numeric.notna().any()
                has_non_numeric = numeric.isna().any()
                if has_numeric and has_non_numeric:
                    mixed_cols.append(col)
        return mixed_cols

    def _export_hdf5(self, filename, what):
        if not H5PY_AVAILABLE:
            raise ImportError("h5py not available.")
        data = self._get_data_export(what)
        if not data:
            raise ValueError("No data to export.")
        df = pd.DataFrame(data)

        # Check for mixed types and warn
        mixed = self._detect_mixed_types(df)
        if mixed:
            messagebox.showwarning("Mixed Data Types",
                f"The following columns contain mixed data types (numbers and strings) and will be stored as strings in HDF5:\n"
                f"{', '.join(mixed)}\n\nConsider cleaning the data for better numeric storage.")

        # Create a structured array
        dtype = []
        for col in df.columns:
            # Try to infer type from first non-null value
            sample_val = df[col].dropna().iloc[0] if not df[col].dropna().empty else ''
            if isinstance(sample_val, (int, float)):
                dtype.append((col, 'f8'))
            else:
                dtype.append((col, h5py.string_dtype(encoding='utf-8')))
        arr = df.to_records(index=False)
        with h5py.File(filename, 'w') as f:
            f.create_dataset('data', data=arr)

    def _export_netcdf(self, filename, what):
        if not NETCDF4_AVAILABLE:
            raise ImportError("netCDF4 not available.")
        data = self._get_data_export(what)
        if not data:
            raise ValueError("No data to export.")
        df = pd.DataFrame(data)
        # Create NetCDF file with a group for the table
        root = nc.Dataset(filename, 'w', format='NETCDF4')
        # Create a dimension for rows
        root.createDimension('row', len(df))
        # For each column, create a variable
        for col in df.columns:
            # Determine type
            sample_val = df[col].dropna().iloc[0] if not df[col].dropna().empty else ''
            if isinstance(sample_val, (int, float)):
                var = root.createVariable(col, 'f8', ('row',))
                # Replace NaN with 0
                data_vals = df[col].fillna(0).values
                var[:] = data_vals
            else:
                # String variable
                var = root.createVariable(col, str, ('row',))
                # Replace NaN with empty string
                data_vals = df[col].astype(str).fillna('').values
                var[:] = data_vals
        root.close()

    def _export_latex(self, filename, what):
        data = self._get_data_export(what)
        if not data:
            raise ValueError("No data to export.")
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("\\begin{tabular}{")
            # Determine number of columns and alignment
            num_cols = len(data[0])
            f.write("l" * num_cols)  # left-align all columns
            f.write("}\n")
            f.write("\\hline\n")
            if self.include_headers_var.get():
                headers = list(data[0].keys())
                f.write(" & ".join(headers) + " \\\\\n")
                f.write("\\hline\n")
            for row in data:
                # Escape underscores and other LaTeX specials
                escaped = [str(v).replace('_', '\\_') for v in row.values()]
                f.write(" & ".join(escaped) + " \\\\\n")
            f.write("\\hline\n")
            f.write("\\end{tabular}\n")

    def _export_geotiff(self, filename, what):
        """Export as GeoTIFF (requires spatial data and rasterio)"""
        if not HAS_RASTERIO:
            raise ImportError("rasterio not available for GeoTIFF export.")

        data = self._get_data_export(what)
        if not data:
            raise ValueError("No data to export.")

        # Check for coordinates
        lon_col, lat_col = self._get_coordinate_columns()
        if not lon_col or not lat_col:
            raise ValueError("GeoTIFF export requires Latitude/Longitude columns.")

        # Convert to DataFrame
        df = pd.DataFrame(data)

        # We need a value column to rasterize - ask user which one
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if not numeric_cols:
            raise ValueError("No numeric columns found to rasterize.")

        # For simplicity, use the first numeric column
        value_col = numeric_cols[0]

        # Create a simple raster grid
        from scipy.interpolate import griddata

        # Get points and values
        points = df[[lon_col, lat_col]].values
        values = df[value_col].values

        # Create grid
        lon_min, lon_max = points[:, 0].min(), points[:, 0].max()
        lat_min, lat_max = points[:, 1].min(), points[:, 1].max()

        # Add small padding
        lon_pad = (lon_max - lon_min) * 0.05
        lat_pad = (lat_max - lat_min) * 0.05

        lon_grid = np.linspace(lon_min - lon_pad, lon_max + lon_pad, 100)
        lat_grid = np.linspace(lat_min - lat_pad, lat_max + lat_pad, 100)
        lon_mesh, lat_mesh = np.meshgrid(lon_grid, lat_grid)

        # Interpolate
        grid_z = griddata(points, values, (lon_mesh, lat_mesh), method='cubic')

        # Create GeoTIFF
        transform = rasterio.transform.from_bounds(
            lon_min - lon_pad, lat_min - lat_pad,
            lon_max + lon_pad, lat_max + lat_pad,
            grid_z.shape[1], grid_z.shape[0]
        )

        with rasterio.open(
            filename, 'w',
            driver='GTiff',
            height=grid_z.shape[0],
            width=grid_z.shape[1],
            count=1,
            dtype=grid_z.dtype,
            crs='EPSG:4326',
            transform=transform,
        ) as dst:
            dst.write(grid_z, 1)


# ----------------------------------------------------------------------
# Registration functions (unchanged)
# ----------------------------------------------------------------------
def setup_plugin(main_app):
    plugin = UniversalExporterPlugin(main_app)
    menu_item_id = f"{PLUGIN_INFO['id']}_menu_item"
    if hasattr(main_app, '_added_plugins') and menu_item_id in main_app._added_plugins:
        return plugin

    target_menu = None
    if hasattr(main_app, 'file_menu'):
        target_menu = main_app.file_menu
    elif hasattr(main_app, 'tools_menu'):
        target_menu = main_app.tools_menu
    elif hasattr(main_app, 'advanced_menu'):
        target_menu = main_app.advanced_menu

    if target_menu:
        target_menu.add_command(
            label=f"{PLUGIN_INFO['icon']} Export...",
            command=plugin.show
        )
        if hasattr(main_app, '_added_plugins'):
            main_app._added_plugins.add(menu_item_id)
    else:
        print("Universal Exporter: No suitable menu found.")

    return plugin

def register_plugin(parent_app):
    return UniversalExporterPlugin(parent_app)
