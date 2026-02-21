"""
Spectral Processing Toolbox - REAL MATLAB-like functionality
Replaces: spectral_tools.py + spectral_processing.py
"""

PLUGIN_INFO = {
    "id": "spectral_toolbox",
    "category": "software",
    "name": "Spectral Processing Toolbox",
    "description": "MATLAB-like spectral analysis: peak detection, baseline correction, smoothing, derivatives, peak fitting",
    "icon": "📉",
    "version": "2.0",
    "requires": ["numpy", "scipy", "pybaselines", "lmfit", "matplotlib"],
    "author": "Sefy Levy / AI Enhanced"
}

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
from collections import defaultdict

class SpectralToolboxPlugin:
    def __init__(self, app):
        self.app = app
        self.window = None

        # Check dependencies
        self.deps_available = self._check_dependencies()

        # Data storage
        self.current_spectrum = None
        self.original_spectrum = None
        self.processed_data = {}

    def _check_dependencies(self):
        """Check if required packages are installed"""
        missing = []
        for package in PLUGIN_INFO['requires']:
            try:
                if package == "numpy":
                    import numpy
                elif package == "scipy":
                    import scipy
                elif package == "pybaselines":
                    import pybaselines
                elif package == "lmfit":
                    import lmfit
                elif package == "matplotlib":
                    import matplotlib
            except ImportError:
                missing.append(package)

        if missing:
            messagebox.showwarning(
                "Missing Dependencies",
                f"Please install missing packages:\npip install {' '.join(missing)}\n\n"
                "Some features will be limited."
            )
            return False
        return True

    def open_window(self):
        """Open the main spectral processing window"""
        if self.window and tk.Toplevel.winfo_exists(self.window):
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title(f"{PLUGIN_INFO['name']} v{PLUGIN_INFO['version']}")
        self.window.geometry("900x700")

        # Make resizable
        self.window.minsize(800, 600)

        self._create_main_ui()

        # Load data from app
        self._load_app_data()

    def _create_main_ui(self):
        """Create the main UI layout"""
        # Create notebook for different sections
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Tab 1: Data Selection
        self.tab_data = ttk.Frame(notebook)
        notebook.add(self.tab_data, text="📊 Data Selection")
        self._create_data_tab()

        # Tab 2: Baseline Correction
        self.tab_baseline = ttk.Frame(notebook)
        notebook.add(self.tab_baseline, text="📈 Baseline")
        self._create_baseline_tab()

        # Tab 3: Peak Analysis
        self.tab_peaks = ttk.Frame(notebook)
        notebook.add(self.tab_peaks, text="⛰️ Peaks")
        self._create_peaks_tab()

        # Tab 4: Smoothing & Derivatives
        self.tab_smoothing = ttk.Frame(notebook)
        notebook.add(self.tab_smoothing, text="📐 Smoothing")
        self._create_smoothing_tab()

        # Tab 5: Peak Fitting
        self.tab_fitting = ttk.Frame(notebook)
        notebook.add(self.tab_fitting, text="🎯 Fitting")
        self._create_fitting_tab()

    def _create_data_tab(self):
        """Create data selection tab"""
        # Title
        ttk.Label(self.tab_data, text="Select Spectral Data",
                 font=("Arial", 12, "bold")).pack(pady=10)

        # Frame for data source selection
        source_frame = ttk.LabelFrame(self.tab_data, text="Data Source", padding=10)
        source_frame.pack(fill=tk.X, padx=10, pady=5)

        # Option 1: Use app data (trace elements as pseudo-spectrum)
        ttk.Radiobutton(source_frame, text="Use Trace Elements as Pseudo-Spectrum",
                       value="app", variable=tk.StringVar(value="app")).pack(anchor=tk.W, pady=5)

        # Option 2: Import from file
        ttk.Radiobutton(source_frame, text="Import from CSV/TXT file",
                       value="file", variable=tk.StringVar()).pack(anchor=tk.W, pady=5)

        # Option 3: Manual input
        ttk.Radiobutton(source_frame, text="Manual Entry",
                       value="manual", variable=tk.StringVar()).pack(anchor=tk.W, pady=5)

        # Load from app button
        ttk.Button(source_frame, text="Load Current App Data",
                  command=self._load_app_data).pack(pady=10)

        # Data preview
        preview_frame = ttk.LabelFrame(self.tab_data, text="Data Preview", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Create text widget for preview
        self.preview_text = tk.Text(preview_frame, height=10, width=80)
        scrollbar = ttk.Scrollbar(preview_frame, command=self.preview_text.yview)
        self.preview_text.configure(yscrollcommand=scrollbar.set)

        self.preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Statistics
        stats_frame = ttk.Frame(self.tab_data)
        stats_frame.pack(fill=tk.X, padx=10, pady=5)

        self.stats_label = ttk.Label(stats_frame, text="No data loaded")
        self.stats_label.pack()

    def _load_app_data(self):
        """Load spectral data from app's dynamic table"""
        if not self.app.samples:
            messagebox.showinfo("No Data", "No samples in the main app.")
            return

        try:
            import numpy as np

            # Get all available columns from the dynamic table
            if hasattr(self.app, 'active_headers') and self.app.active_headers:
                all_columns = self.app.active_headers
            else:
                # Fallback: get from first sample
                all_columns = list(self.app.samples[0].keys())

            # Look for trace element columns (common patterns)
            trace_elements = []
            element_patterns = ['Zr', 'Nb', 'Ba', 'Rb', 'Cr', 'Ni', 'La', 'Ce',
                            'Nd', 'Sm', 'Eu', 'Gd', 'Yb', 'Lu', 'Sr', 'Y']

            for col in all_columns:
                col_lower = col.lower()
                for elem in element_patterns:
                    if elem.lower() in col_lower and 'ppm' in col_lower:
                        trace_elements.append(col)
                        break

            # If no trace elements found, use numeric columns
            if not trace_elements:
                # Try to identify numeric columns
                numeric_cols = []
                sample = self.app.samples[0]
                for col in all_columns:
                    try:
                        val = self._safe_float(sample.get(col, ''))
                        if val is not None:
                            numeric_cols.append(col)
                    except:
                        pass
                trace_elements = numeric_cols[:10]  # Use first 10 numeric columns

            if not trace_elements:
                messagebox.showwarning("No Numeric Data", "No numeric trace element data found.")
                return

            # Use element indices as pseudo-wavelengths
            wavelengths = np.arange(len(trace_elements))

            # Create average spectrum from all samples
            all_intensities = []
            valid_samples = 0

            for sample in self.app.samples:
                intensities = []
                valid_point = True
                for elem in trace_elements:
                    val = self._safe_float(sample.get(elem, ''))
                    if val is not None:
                        intensities.append(val)
                    else:
                        intensities.append(0.0)
                        valid_point = False
                if valid_point and any(v > 0 for v in intensities):
                    all_intensities.append(intensities)
                    valid_samples += 1

            if not all_intensities:
                messagebox.showwarning("No Valid Data", "No valid numeric data found in samples.")
                return

            # Use median spectrum (robust to outliers)
            all_intensities = np.array(all_intensities)
            intensities = np.median(all_intensities, axis=0)

            # Store the spectrum
            self.original_spectrum = (wavelengths.copy(), intensities.copy())
            self.current_spectrum = (wavelengths.copy(), intensities.copy())

            # Store element names for reference
            self.spectrum_elements = trace_elements

            # Update preview
            self._update_preview()

            # Update status
            if hasattr(self, 'stats_label'):
                self.stats_label.config(
                    text=f"Loaded pseudo-spectrum from {valid_samples} samples, {len(trace_elements)} elements"
                )

            messagebox.showinfo("Data Loaded",
                            f"✅ Loaded pseudo-spectrum from {valid_samples} samples\n"
                            f"Elements: {', '.join(trace_elements[:10])}" +
                            ("..." if len(trace_elements) > 10 else ""))

        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Load Error", f"Failed to load data: {str(e)}")

    def _safe_float(self, value):
        """Safely convert to float"""
        try:
            return float(value) if value else None
        except:
            return None

    def _update_preview(self):
        """Update data preview"""
        if not self.current_spectrum:
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(1.0, "No data loaded.")
            self.stats_label.config(text="No data loaded")
            return

        x, y = self.current_spectrum

        # Update preview text
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.insert(1.0, "Wavelength/Index\tIntensity\n")
        self.preview_text.insert(2.0, "-" * 40 + "\n")

        for i in range(min(50, len(x))):  # Show first 50 points
            self.preview_text.insert(tk.END, f"{x[i]:.2f}\t{y[i]:.4f}\n")

        if len(x) > 50:
            self.preview_text.insert(tk.END, f"... and {len(x)-50} more points\n")

        # Update statistics
        import numpy as np
        stats_text = (f"Points: {len(x)} | Min: {np.min(y):.4f} | "
                     f"Max: {np.max(y):.4f} | Mean: {np.mean(y):.4f} | "
                     f"Std: {np.std(y):.4f}")
        self.stats_label.config(text=stats_text)

    def _create_baseline_tab(self):
        """Create baseline correction tab"""
        ttk.Label(self.tab_baseline, text="Baseline Correction Methods",
                 font=("Arial", 12, "bold")).pack(pady=10)

        # Method selection
        method_frame = ttk.LabelFrame(self.tab_baseline, text="Correction Method", padding=10)
        method_frame.pack(fill=tk.X, padx=10, pady=5)

        self.baseline_method = tk.StringVar(value="als")

        methods = [
            ("ALS (Asymmetric Least Squares)", "als"),
            ("Polynomial (PolyFit)", "poly"),
            ("Rolling Ball", "rolling_ball"),
            ("Median Filter", "median"),
            ("TopHat", "tophat")
        ]

        for text, value in methods:
            ttk.Radiobutton(method_frame, text=text, value=value,
                           variable=self.baseline_method).pack(anchor=tk.W, pady=2)

        # Parameters frame
        params_frame = ttk.LabelFrame(self.tab_baseline, text="Parameters", padding=10)
        params_frame.pack(fill=tk.X, padx=10, pady=5)

        # ALS parameters
        als_frame = ttk.Frame(params_frame)
        als_frame.pack(fill=tk.X, pady=5)

        ttk.Label(als_frame, text="λ (smoothness):").pack(side=tk.LEFT, padx=5)
        self.als_lambda = ttk.Entry(als_frame, width=10)
        self.als_lambda.insert(0, "1e6")
        self.als_lambda.pack(side=tk.LEFT, padx=5)

        ttk.Label(als_frame, text="p (asymmetry):").pack(side=tk.LEFT, padx=5)
        self.als_p = ttk.Entry(als_frame, width=10)
        self.als_p.insert(0, "0.05")
        self.als_p.pack(side=tk.LEFT, padx=5)

        # Polynomial parameters
        poly_frame = ttk.Frame(params_frame)
        poly_frame.pack(fill=tk.X, pady=5)

        ttk.Label(poly_frame, text="Degree:").pack(side=tk.LEFT, padx=5)
        self.poly_degree = ttk.Entry(poly_frame, width=10)
        self.poly_degree.insert(0, "3")
        self.poly_degree.pack(side=tk.LEFT, padx=5)

        # Apply button
        ttk.Button(self.tab_baseline, text="Apply Baseline Correction",
                  command=self._apply_baseline_correction).pack(pady=20)

        # Results frame
        results_frame = ttk.LabelFrame(self.tab_baseline, text="Results", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.baseline_results = tk.Text(results_frame, height=8, width=80)
        scrollbar = ttk.Scrollbar(results_frame, command=self.baseline_results.yview)
        self.baseline_results.configure(yscrollcommand=scrollbar.set)

        self.baseline_results.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _apply_baseline_correction(self):
        """Apply baseline correction to current spectrum"""
        if not self.current_spectrum:
            messagebox.showwarning("No Data", "Please load spectral data first.")
            return

        try:
            import numpy as np
            x, y = self.current_spectrum

            method = self.baseline_method.get()

            if method == "als":
                # Asymmetric Least Squares baseline
                from pybaselines import Baseline
                baseline_fitter = Baseline(x)
                lambda_val = float(self.als_lambda.get())
                p_val = float(self.als_p.get())

                baseline, params = baseline_fitter.als(y, lam=lambda_val, p=p_val)
                corrected = y - baseline

                result_text = f"ALS Baseline Correction\n"
                result_text += f"λ = {lambda_val:.2e}, p = {p_val:.3f}\n"
                result_text += f"Baseline RMSE: {np.sqrt(np.mean(baseline**2)):.4f}\n"

            elif method == "poly":
                # Polynomial baseline
                degree = int(self.poly_degree.get())
                coeffs = np.polyfit(x, y, degree)
                baseline = np.polyval(coeffs, x)
                corrected = y - baseline

                result_text = f"Polynomial Baseline (degree {degree})\n"
                result_text += f"Coefficients: {coeffs}\n"
                result_text += f"Baseline range: {baseline.min():.4f} to {baseline.max():.4f}\n"

            elif method == "rolling_ball":
                # Rolling ball baseline
                from scipy.ndimage import uniform_filter1d
                window_size = 51  # Adjust based on data
                baseline = uniform_filter1d(y, size=window_size)
                corrected = y - baseline

                result_text = f"Rolling Ball Baseline\n"
                result_text += f"Window size: {window_size}\n"

            else:
                messagebox.showerror("Not Implemented", f"Method '{method}' not yet implemented.")
                return

            # Update current spectrum
            self.current_spectrum = (x, corrected)

            # Store baseline
            self.processed_data['baseline'] = baseline
            self.processed_data['baseline_method'] = method
            self.processed_data['baseline_corrected'] = corrected

            # Update results
            self.baseline_results.delete(1.0, tk.END)
            self.baseline_results.insert(1.0, result_text)

            # Update preview
            self._update_preview()

            messagebox.showinfo("Success", "Baseline correction applied successfully!")

            # Plot results
            self._plot_results(x, y, baseline, corrected, "Baseline Correction")

        except Exception as e:
            messagebox.showerror("Baseline Error", f"Failed to apply baseline: {str(e)}")

    def _create_peaks_tab(self):
        """Create peak detection tab"""
        ttk.Label(self.tab_peaks, text="Peak Detection & Analysis",
                 font=("Arial", 12, "bold")).pack(pady=10)

        # Parameters frame
        params_frame = ttk.LabelFrame(self.tab_peaks, text="Detection Parameters", padding=10)
        params_frame.pack(fill=tk.X, padx=10, pady=5)

        # Prominence
        prom_frame = ttk.Frame(params_frame)
        prom_frame.pack(fill=tk.X, pady=5)

        ttk.Label(prom_frame, text="Min Prominence:").pack(side=tk.LEFT, padx=5)
        self.peak_prominence = ttk.Entry(prom_frame, width=10)
        self.peak_prominence.insert(0, "0.1")
        self.peak_prominence.pack(side=tk.LEFT, padx=5)

        # Width
        width_frame = ttk.Frame(params_frame)
        width_frame.pack(fill=tk.X, pady=5)

        ttk.Label(width_frame, text="Min Width:").pack(side=tk.LEFT, padx=5)
        self.peak_width = ttk.Entry(width_frame, width=10)
        self.peak_width.insert(0, "1")
        self.peak_width.pack(side=tk.LEFT, padx=5)

        # Distance
        dist_frame = ttk.Frame(params_frame)
        dist_frame.pack(fill=tk.X, pady=5)

        ttk.Label(dist_frame, text="Min Distance:").pack(side=tk.LEFT, padx=5)
        self.peak_distance = ttk.Entry(dist_frame, width=10)
        self.peak_distance.insert(0, "5")
        self.peak_distance.pack(side=tk.LEFT, padx=5)

        # Buttons
        button_frame = ttk.Frame(self.tab_peaks)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Detect Peaks",
                  command=self._detect_peaks).pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="Find Valleys",
                  command=self._detect_valleys).pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="Export Peaks to App",
                  command=self._export_peaks_to_app).pack(side=tk.LEFT, padx=5)

        # Results frame
        results_frame = ttk.LabelFrame(self.tab_peaks, text="Detected Peaks", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Create treeview for peaks
        columns = ("index", "x", "y", "prominence", "width")
        self.peaks_tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=8)

        for col in columns:
            self.peaks_tree.heading(col, text=col.capitalize())
            self.peaks_tree.column(col, width=100)

        scrollbar = ttk.Scrollbar(results_frame, command=self.peaks_tree.yview)
        self.peaks_tree.configure(yscrollcommand=scrollbar.set)

        self.peaks_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Peak statistics
        self.peak_stats = ttk.Label(self.tab_peaks, text="No peaks detected")
        self.peak_stats.pack(pady=5)

    def _detect_peaks(self):
        """Detect peaks in current spectrum"""
        if not self.current_spectrum:
            messagebox.showwarning("No Data", "Please load spectral data first.")
            return

        try:
            from scipy.signal import find_peaks

            x, y = self.current_spectrum

            # Get parameters
            prominence = float(self.peak_prominence.get())
            width = float(self.peak_width.get())
            distance = float(self.peak_distance.get())

            # Find peaks
            peaks, properties = find_peaks(
                y,
                prominence=prominence,
                width=width,
                distance=distance
            )

            # Clear tree
            for item in self.peaks_tree.get_children():
                self.peaks_tree.delete(item)

            # Add peaks to tree
            for i, peak_idx in enumerate(peaks):
                peak_x = x[peak_idx]
                peak_y = y[peak_idx]
                peak_prom = properties['prominences'][i] if 'prominences' in properties else 0
                peak_width_val = properties['widths'][i] if 'widths' in properties else 0

                self.peaks_tree.insert("", "end", values=(
                    peak_idx, f"{peak_x:.4f}", f"{peak_y:.4f}",
                    f"{peak_prom:.4f}", f"{peak_width_val:.4f}"
                ))

            # Update statistics
            self.peak_stats.config(
                text=f"Found {len(peaks)} peaks | "
                     f"Average prominence: {np.mean(properties['prominences']) if 'prominences' in properties else 0:.4f}"
            )

            # Store peaks
            self.processed_data['peaks'] = peaks
            self.processed_data['peak_properties'] = properties

            # Plot peaks
            self._plot_peaks(x, y, peaks, "Detected Peaks")

            messagebox.showinfo("Peaks Detected", f"Found {len(peaks)} peaks in the spectrum.")

        except Exception as e:
            messagebox.showerror("Peak Detection Error", f"Failed to detect peaks: {str(e)}")

    def _detect_valleys(self):
        """Detect valleys (inverse peaks)"""
        if not self.current_spectrum:
            messagebox.showwarning("No Data", "Please load spectral data first.")
            return

        try:
            from scipy.signal import find_peaks

            x, y = self.current_spectrum

            # Find valleys by inverting the signal
            valleys, properties = find_peaks(-y)

            # Clear tree
            for item in self.peaks_tree.get_children():
                self.peaks_tree.delete(item)

            # Add valleys to tree
            for i, valley_idx in enumerate(valleys):
                valley_x = x[valley_idx]
                valley_y = y[valley_idx]

                self.peaks_tree.insert("", "end", values=(
                    valley_idx, f"{valley_x:.4f}", f"{valley_y:.4f}",
                    "N/A", "N/A"
                ))

            self.peak_stats.config(text=f"Found {len(valleys)} valleys")
            self.processed_data['valleys'] = valleys

            messagebox.showinfo("Valleys Detected", f"Found {len(valleys)} valleys.")

        except Exception as e:
            messagebox.showerror("Valley Detection Error", f"Failed to detect valleys: {str(e)}")

    def _export_peaks_to_app(self):
        """Export detected peaks to main app as new samples - FIXED with proper import pattern"""
        if 'peaks' not in self.processed_data:
            messagebox.showwarning("No Peaks", "No peaks detected to export.")
            return

        try:
            import numpy as np
            from datetime import datetime

            x, y = self.current_spectrum
            peaks = self.processed_data['peaks']

            # Prepare table data in the format expected by import_data_from_plugin
            table_data = []
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Create a sample entry for each detected peak
            for i, peak_idx in enumerate(peaks):
                sample_entry = {
                    # REQUIRED: Sample_ID
                    'Sample_ID': f"PEAK_{i+1:03d}_{x[peak_idx]:.2f}",

                    # Metadata
                    'Timestamp': timestamp,
                    'Source': 'Spectral Analysis',
                    'Analysis_Type': 'Peak Detection',
                    'Plugin': PLUGIN_INFO['name'],

                    # REQUIRED: Notes field
                    'Notes': f"Detected peak at position {x[peak_idx]:.4f}"
                }

                # Add peak data
                sample_entry['Peak_X'] = f"{x[peak_idx]:.4f}"
                sample_entry['Peak_Y'] = f"{y[peak_idx]:.4f}"
                sample_entry['Peak_Index'] = str(peak_idx)

                # Add prominence if available
                if 'peak_properties' in self.processed_data:
                    props = self.processed_data['peak_properties']
                    if 'prominences' in props and i < len(props['prominences']):
                        sample_entry['Peak_Prominence'] = f"{props['prominences'][i]:.4f}"
                    if 'widths' in props and i < len(props['widths']):
                        sample_entry['Peak_Width'] = f"{props['widths'][i]:.4f}"

                table_data.append(sample_entry)

            # Send to main app using the STANDARDIZED method
            if hasattr(self.app, 'import_data_from_plugin'):
                self.app.import_data_from_plugin(table_data)

                # Refresh app table if needed (import_data_from_plugin should handle this)
                if hasattr(self.app, 'refresh_tree'):
                    self.app.refresh_tree()

                messagebox.showinfo("Export Complete",
                                f"✅ Exported {len(peaks)} peaks to main app.\n\n"
                                f"Peaks detected at positions:\n" +
                                "\n".join([f"  • {x[p]:.4f}" for p in peaks[:10]]) +
                                ("\n  • ..." if len(peaks) > 10 else ""))
            else:
                # Fallback to legacy method
                self._legacy_peak_export(table_data)

        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export peaks: {str(e)}")

    def _legacy_peak_export(self, table_data):
        """Fallback method for older main app versions"""
        try:
            # Add to app samples manually
            for entry in table_data:
                self.app.samples.append(entry)

            # Refresh app table
            if hasattr(self.app, 'refresh_tree'):
                self.app.refresh_tree()

            messagebox.showinfo("Export Complete",
                            f"✅ Exported {len(table_data)} peaks to main app (legacy mode)")

        except Exception as e:
            messagebox.showerror("Legacy Export Error", str(e))

    def _create_smoothing_tab(self):
        """Create smoothing and derivatives tab"""
        ttk.Label(self.tab_smoothing, text="Smoothing & Derivatives",
                 font=("Arial", 12, "bold")).pack(pady=10)

        # Smoothing methods
        smooth_frame = ttk.LabelFrame(self.tab_smoothing, text="Smoothing Methods", padding=10)
        smooth_frame.pack(fill=tk.X, padx=10, pady=5)

        self.smooth_method = tk.StringVar(value="savgol")

        ttk.Radiobutton(smooth_frame, text="Savitzky-Golay", value="savgol",
                       variable=self.smooth_method).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(smooth_frame, text="Moving Average", value="moving",
                       variable=self.smooth_method).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(smooth_frame, text="Gaussian", value="gaussian",
                       variable=self.smooth_method).pack(anchor=tk.W, pady=2)

        # Parameters
        params_frame = ttk.LabelFrame(self.tab_smoothing, text="Parameters", padding=10)
        params_frame.pack(fill=tk.X, padx=10, pady=5)

        # Window size
        window_frame = ttk.Frame(params_frame)
        window_frame.pack(fill=tk.X, pady=5)

        ttk.Label(window_frame, text="Window Size:").pack(side=tk.LEFT, padx=5)
        self.smooth_window = ttk.Entry(window_frame, width=10)
        self.smooth_window.insert(0, "11")
        self.smooth_window.pack(side=tk.LEFT, padx=5)

        # Polynomial order (for Savitzky-Golay)
        poly_frame = ttk.Frame(params_frame)
        poly_frame.pack(fill=tk.X, pady=5)

        ttk.Label(poly_frame, text="Polynomial Order:").pack(side=tk.LEFT, padx=5)
        self.smooth_poly = ttk.Entry(poly_frame, width=10)
        self.smooth_poly.insert(0, "3")
        self.smooth_poly.pack(side=tk.LEFT, padx=5)

        # Derivatives
        deriv_frame = ttk.LabelFrame(self.tab_smoothing, text="Derivatives", padding=10)
        deriv_frame.pack(fill=tk.X, padx=10, pady=5)

        self.deriv_order = tk.StringVar(value="1")

        ttk.Radiobutton(deriv_frame, text="1st Derivative", value="1",
                       variable=self.deriv_order).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(deriv_frame, text="2nd Derivative", value="2",
                       variable=self.deriv_order).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(deriv_frame, text="No Derivative", value="0",
                       variable=self.deriv_order).pack(anchor=tk.W, pady=2)

        # Buttons
        button_frame = ttk.Frame(self.tab_smoothing)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Apply Smoothing",
                  command=self._apply_smoothing).pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="Calculate Derivative",
                  command=self._calculate_derivative).pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="Reset to Original",
                  command=self._reset_to_original).pack(side=tk.LEFT, padx=5)

    def _apply_smoothing(self):
        """Apply smoothing to current spectrum"""
        if not self.current_spectrum:
            messagebox.showwarning("No Data", "Please load spectral data first.")
            return

        try:
            import numpy as np
            from scipy.signal import savgol_filter

            x, y = self.current_spectrum
            method = self.smooth_method.get()
            window = int(self.smooth_window.get())

            if window % 2 == 0:
                window += 1  # Make odd

            if method == "savgol":
                polyorder = int(self.smooth_poly.get())
                smoothed = savgol_filter(y, window, polyorder)

                result_text = f"Savitzky-Golay Smoothing\n"
                result_text += f"Window: {window}, Polynomial: {polyorder}\n"

            elif method == "moving":
                # Moving average
                smoothed = np.convolve(y, np.ones(window)/window, mode='same')
                result_text = f"Moving Average\nWindow: {window}\n"

            elif method == "gaussian":
                # Gaussian smoothing
                from scipy.ndimage import gaussian_filter1d
                smoothed = gaussian_filter1d(y, sigma=window/6)
                result_text = f"Gaussian Smoothing\nSigma: {window/6:.2f}\n"

            else:
                messagebox.showerror("Not Implemented", f"Method '{method}' not implemented.")
                return

            # Update spectrum
            self.current_spectrum = (x, smoothed)
            self.processed_data['smoothed'] = smoothed
            self.processed_data['smoothing_method'] = method

            # Update preview
            self._update_preview()

            messagebox.showinfo("Smoothing Applied", "Spectrum smoothed successfully!")

            # Plot
            self._plot_comparison(x, y, smoothed, "Original vs Smoothed")

        except Exception as e:
            messagebox.showerror("Smoothing Error", f"Failed to apply smoothing: {str(e)}")

    def _calculate_derivative(self):
        """Calculate derivative of current spectrum"""
        if not self.current_spectrum:
            messagebox.showwarning("No Data", "Please load spectral data first.")
            return

        try:
            from scipy.signal import savgol_filter

            x, y = self.current_spectrum
            order = int(self.deriv_order.get())

            if order == 0:
                return  # No derivative

            window = int(self.smooth_window.get())
            if window % 2 == 0:
                window += 1

            polyorder = max(3, order + 1)  # Need higher poly order for derivatives

            # Calculate derivative using Savitzky-Golay
            derivative = savgol_filter(y, window, polyorder, deriv=order)

            # Update spectrum with derivative
            self.current_spectrum = (x, derivative)
            self.processed_data['derivative'] = derivative
            self.processed_data['derivative_order'] = order

            # Update preview
            self._update_preview()

            messagebox.showinfo("Derivative Calculated",
                              f"{order}st derivative calculated successfully!")

            # Plot
            self._plot_results(x, derivative, None, None,
                             f"{order}st Derivative Spectrum")

        except Exception as e:
            messagebox.showerror("Derivative Error", f"Failed to calculate derivative: {str(e)}")

    def _reset_to_original(self):
        """Reset spectrum to original"""
        if self.original_spectrum:
            self.current_spectrum = (self.original_spectrum[0].copy(),
                                   self.original_spectrum[1].copy())
            self._update_preview()
            messagebox.showinfo("Reset", "Spectrum reset to original.")
        else:
            messagebox.showwarning("No Original", "No original spectrum stored.")

    def _create_fitting_tab(self):
        """Create peak fitting tab"""
        ttk.Label(self.tab_fitting, text="Peak Fitting & Deconvolution",
                 font=("Arial", 12, "bold")).pack(pady=10)

        # Peak models
        model_frame = ttk.LabelFrame(self.tab_fitting, text="Peak Models", padding=10)
        model_frame.pack(fill=tk.X, padx=10, pady=5)

        self.fit_model = tk.StringVar(value="gaussian")

        ttk.Radiobutton(model_frame, text="Gaussian", value="gaussian",
                       variable=self.fit_model).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(model_frame, text="Lorentzian", value="lorentzian",
                       variable=self.fit_model).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(model_frame, text="Voigt (Gaussian + Lorentzian)", value="voigt",
                       variable=self.fit_model).pack(anchor=tk.W, pady=2)

        # Fitting region
        region_frame = ttk.LabelFrame(self.tab_fitting, text="Fitting Region", padding=10)
        region_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(region_frame, text="X min:").pack(side=tk.LEFT, padx=5)
        self.fit_xmin = ttk.Entry(region_frame, width=10)
        self.fit_xmin.insert(0, "0")
        self.fit_xmin.pack(side=tk.LEFT, padx=5)

        ttk.Label(region_frame, text="X max:").pack(side=tk.LEFT, padx=5)
        self.fit_xmax = ttk.Entry(region_frame, width=10)
        self.fit_xmax.insert(0, "5")
        self.fit_xmax.pack(side=tk.LEFT, padx=5)

        # Number of peaks
        peaks_frame = ttk.Frame(self.tab_fitting)
        peaks_frame.pack(pady=5)

        ttk.Label(peaks_frame, text="Number of peaks to fit:").pack(side=tk.LEFT, padx=5)
        self.fit_npeaks = ttk.Entry(peaks_frame, width=10)
        self.fit_npeaks.insert(0, "1")
        self.fit_npeaks.pack(side=tk.LEFT, padx=5)

        # Buttons
        button_frame = ttk.Frame(self.tab_fitting)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Fit Peaks",
                  command=self._fit_peaks).pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="Deconvolve Overlapping Peaks",
                  command=self._deconvolve_peaks).pack(side=tk.LEFT, padx=5)

        # Results
        results_frame = ttk.LabelFrame(self.tab_fitting, text="Fitting Results", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.fit_results = tk.Text(results_frame, height=10, width=80)
        scrollbar = ttk.Scrollbar(results_frame, command=self.fit_results.yview)
        self.fit_results.configure(yscrollcommand=scrollbar.set)

        self.fit_results.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _fit_peaks(self):
        """Fit peaks with selected model"""
        if not self.current_spectrum:
            messagebox.showwarning("No Data", "Please load spectral data first.")
            return

        try:
            import numpy as np
            from lmfit.models import GaussianModel, LorentzianModel, VoigtModel

            x, y = self.current_spectrum

            # Get fitting region
            xmin = float(self.fit_xmin.get())
            xmax = float(self.fit_xmax.get())
            npeaks = int(self.fit_npeaks.get())

            # Select region
            mask = (x >= xmin) & (x <= xmax)
            x_fit = x[mask]
            y_fit = y[mask]

            if len(x_fit) < 10:
                messagebox.showerror("Region Too Small", "Selected region has too few points.")
                return

            # Select model
            model_name = self.fit_model.get()
            if model_name == "gaussian":
                model = GaussianModel()
            elif model_name == "lorentzian":
                model = LorentzianModel()
            elif model_name == "voigt":
                model = VoigtModel()
            else:
                messagebox.showerror("Invalid Model", f"Model '{model_name}' not supported.")
                return

            # Create composite model for multiple peaks
            composite_model = model
            for i in range(1, npeaks):
                composite_model += model

            # Initial parameters
            params = composite_model.make_params()

            # Set initial guesses
            y_max = np.max(y_fit)
            x_peak = x_fit[np.argmax(y_fit)]

            for i in range(npeaks):
                prefix = f"m{i}_" if i > 0 else ""
                params[f'{prefix}amplitude'].set(y_max/npeaks, min=0)
                params[f'{prefix}center'].set(x_peak + i*0.5, min=xmin, max=xmax)
                params[f'{prefix}sigma'].set(0.5, min=0.1, max=5)

            # Fit the model
            result = composite_model.fit(y_fit, params, x=x_fit)

            # Display results
            self.fit_results.delete(1.0, tk.END)
            self.fit_results.insert(1.0, f"Fitting Results ({model_name.upper()})\n")
            self.fit_results.insert(2.0, "="*50 + "\n")
            self.fit_results.insert(3.0, result.fit_report())

            # Store results
            self.processed_data['fit_result'] = result
            self.processed_data['fit_model'] = model_name

            # Plot fit
            self._plot_fit(x_fit, y_fit, result, model_name)

            messagebox.showinfo("Fit Successful",
                              f"Fitted {npeaks} {model_name} peaks with R² = {result.rsquared:.4f}")

        except Exception as e:
            messagebox.showerror("Fitting Error", f"Failed to fit peaks: {str(e)}")
    def _deconvolve_peaks(self):
        """Deconvolve overlapping peaks using peak fitting"""
        if not self.current_spectrum:
            messagebox.showwarning("No Data", "Please load spectral data first.")
            return

        try:
            import numpy as np
            from scipy import optimize
            from scipy.signal import find_peaks

            x, y = self.current_spectrum

            # Get parameters from UI or use defaults
            n_peaks = None
            try:
                n_peaks = int(self.fit_npeaks.get())
            except:
                n_peaks = None

            # Get fitting region if specified
            try:
                xmin = float(self.fit_xmin.get())
                xmax = float(self.fit_xmax.get())
                mask = (x >= xmin) & (x <= xmax)
                x_fit = x[mask]
                y_fit = y[mask]
            except:
                x_fit, y_fit = x, y

            # First, detect peaks automatically if number not specified
            if n_peaks is None:
                # Auto-detect peaks
                peaks, properties = find_peaks(y_fit, prominence=0.1*np.max(y_fit))
                n_peaks = min(len(peaks), 10)  # Limit to 10 peaks max
                if n_peaks == 0:
                    n_peaks = 1  # Default to at least one peak

            # Define peak functions
            def gaussian(x, amp, cen, sigma):
                return amp * np.exp(-(x - cen)**2 / (2 * sigma**2))

            def lorentzian(x, amp, cen, sigma):
                return amp * sigma**2 / ((x - cen)**2 + sigma**2)

            def voigt(x, amp, cen, sigma, gamma):
                # Pseudo-Voigt approximation
                g = gaussian(x, amp, cen, sigma)
                l = lorentzian(x, amp, cen, sigma)
                return 0.5 * g + 0.5 * l  # Equal mixture

            # Select peak shape
            model_type = self.fit_model.get()
            if model_type == "gaussian":
                peak_func = gaussian
                params_per_peak = 3
            elif model_type == "lorentzian":
                peak_func = lorentzian
                params_per_peak = 3
            elif model_type == "voigt":
                peak_func = voigt
                params_per_peak = 4
            else:
                peak_func = gaussian
                params_per_peak = 3

            # Composite model function
            def composite_model(x, *params):
                result = np.zeros_like(x, dtype=float)
                idx = 0
                for i in range(n_peaks):
                    if params_per_peak == 4:
                        amp, cen, sigma, gamma = params[idx:idx+4]
                        result += peak_func(x, amp, cen, sigma, gamma)
                        idx += 4
                    else:
                        amp, cen, sigma = params[idx:idx+3]
                        result += peak_func(x, amp, cen, sigma)
                        idx += 3
                return result

            # Initial parameter guesses
            p0 = []
            bounds_lower = []
            bounds_upper = []

            # Find peaks for initial guesses
            detected_peaks, props = find_peaks(y_fit, prominence=0.05*np.max(y_fit))
            peak_positions = x_fit[detected_peaks] if len(detected_peaks) > 0 else []

            # Distribute peaks if not enough detected
            if len(peak_positions) < n_peaks:
                x_range = np.linspace(np.min(x_fit), np.max(x_fit), n_peaks+2)[1:-1]
                peak_positions = list(peak_positions) + list(x_range[len(peak_positions):])

            # Use top N peaks
            peak_positions = peak_positions[:n_peaks]

            # Estimate peak widths
            dx = np.mean(np.diff(x_fit))
            x_span = np.max(x_fit) - np.min(x_fit)
            estimated_width = x_span / (n_peaks * 3)

            # Set parameter bounds and initial guesses
            for i, pos in enumerate(peak_positions):
                # Amplitude
                p0.append(np.max(y_fit) / n_peaks)
                bounds_lower.append(0)
                bounds_upper.append(np.max(y_fit) * 2)

                # Center
                p0.append(pos)
                bounds_lower.append(np.min(x_fit))
                bounds_upper.append(np.max(x_fit))

                # Sigma (width)
                p0.append(estimated_width)
                bounds_lower.append(dx)
                bounds_upper.append(x_span)

                if params_per_peak == 4:
                    # Gamma (for Voigt)
                    p0.append(0.5)
                    bounds_lower.append(0.1)
                    bounds_upper.append(2)

            # Perform fit
            try:
                popt, pcov = optimize.curve_fit(composite_model, x_fit, y_fit,
                                            p0=p0,
                                            bounds=(bounds_lower, bounds_upper),
                                            maxfev=5000)

                # Calculate fitted curve
                y_fitted = composite_model(x_fit, *popt)

                # Calculate individual components
                components = []
                idx = 0
                for i in range(n_peaks):
                    if params_per_peak == 4:
                        comp_params = popt[idx:idx+4]
                        comp_y = peak_func(x_fit, *comp_params)
                        idx += 4
                    else:
                        comp_params = popt[idx:idx+3]
                        comp_y = peak_func(x_fit, *comp_params)
                        idx += 3
                    components.append(comp_y)

                # Calculate residuals and statistics
                residuals = y_fit - y_fitted
                rmse = np.sqrt(np.mean(residuals**2))
                r2 = 1 - np.sum(residuals**2) / np.sum((y_fit - np.mean(y_fit))**2)

                # Display results
                self.fit_results.delete(1.0, tk.END)
                self.fit_results.insert(1.0, f"PEAK DECONVOLUTION RESULTS\n")
                self.fit_results.insert(2.0, "="*60 + "\n")
                self.fit_results.insert(3.0, f"Model: {model_type.capitalize()}\n")
                self.fit_results.insert(4.0, f"Number of peaks: {n_peaks}\n")
                self.fit_results.insert(5.0, f"RMSE: {rmse:.6f}\n")
                self.fit_results.insert(6.0, f"R²: {r2:.6f}\n\n")
                self.fit_results.insert(7.0, "PEAK PARAMETERS:\n")
                self.fit_results.insert(8.0, "-"*40 + "\n")

                idx = 0
                for i in range(n_peaks):
                    if params_per_peak == 4:
                        amp, cen, sigma, gamma = popt[idx:idx+4]
                        self.fit_results.insert(tk.END,
                            f"Peak {i+1}:\n"
                            f"  Center: {cen:.4f}\n"
                            f"  Amplitude: {amp:.4f}\n"
                            f"  Width (σ): {sigma:.4f}\n"
                            f"  Shape (γ): {gamma:.4f}\n"
                            f"  Area: {amp * sigma * np.sqrt(2*np.pi):.4f}\n\n")
                        idx += 4
                    else:
                        amp, cen, sigma = popt[idx:idx+3]
                        self.fit_results.insert(tk.END,
                            f"Peak {i+1}:\n"
                            f"  Center: {cen:.4f}\n"
                            f"  Amplitude: {amp:.4f}\n"
                            f"  Width (σ): {sigma:.4f}\n"
                            f"  Area: {amp * sigma * np.sqrt(2*np.pi):.4f}\n\n")
                        idx += 3

                # Store results
                self.processed_data['deconvolution'] = {
                    'x': x_fit,
                    'y_fitted': y_fitted,
                    'components': components,
                    'params': popt,
                    'residuals': residuals,
                    'rmse': rmse,
                    'r2': r2,
                    'model': model_type
                }

                # Plot results
                self._plot_deconvolution(x_fit, y_fit, y_fitted, components,
                                        f"Peak Deconvolution - {model_type}")

                messagebox.showinfo("Deconvolution Complete",
                                f"Successfully deconvolved {n_peaks} peaks\n"
                                f"RMSE: {rmse:.6f}, R²: {r2:.6f}")

            except Exception as fit_error:
                messagebox.showerror("Fitting Failed",
                                f"Could not fit peaks: {str(fit_error)}\n\n"
                                f"Try:\n"
                                f"• Reducing number of peaks\n"
                                f"• Selecting a smaller region\n"
                                f"• Using a different peak model")

        except Exception as e:
            messagebox.showerror("Deconvolution Error", f"Failed: {str(e)}")

    def _plot_deconvolution(self, x, y_orig, y_fit, components, title):
        """Plot deconvolution results"""
        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

            plot_window = tk.Toplevel(self.window)
            plot_window.title(f"Deconvolution: {title}")
            plot_window.geometry("900x700")

            # Create subplots: main plot and residuals
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8),
                                        gridspec_kw={'height_ratios': [3, 1]})

            # Main plot
            ax1.plot(x, y_orig, 'ko', label='Original Data', markersize=3, alpha=0.6)
            ax1.plot(x, y_fit, 'r-', label='Combined Fit', linewidth=2)

            # Plot individual components
            colors = ['b', 'g', 'c', 'm', 'y', 'orange', 'purple', 'brown']
            for i, comp in enumerate(components):
                ax1.plot(x, comp, '--', color=colors[i % len(colors)],
                        label=f'Peak {i+1}', alpha=0.7, linewidth=1.5)

            ax1.set_xlabel('Wavelength/Index')
            ax1.set_ylabel('Intensity')
            ax1.set_title(title, fontweight='bold')
            ax1.grid(True, alpha=0.3)
            ax1.legend()

            # Residuals plot
            residuals = y_orig - y_fit
            ax2.plot(x, residuals, 'b-', alpha=0.7)
            ax2.axhline(y=0, color='r', linestyle='--', alpha=0.5)
            ax2.set_xlabel('Wavelength/Index')
            ax2.set_ylabel('Residuals')
            ax2.grid(True, alpha=0.3)
            ax2.set_title(f'Residuals (RMSE: {np.sqrt(np.mean(residuals**2)):.6f})')

            plt.tight_layout()

            canvas = FigureCanvasTkAgg(fig, plot_window)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        except Exception as e:
            print(f"Deconvolution plotting error: {e}")

    def _plot_results(self, x, y, baseline=None, corrected=None, title=""):
        """Plot spectral results"""
        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

            # Create plot window
            plot_window = tk.Toplevel(self.window)
            plot_window.title(f"Spectral Plot: {title}")
            plot_window.geometry("800x600")

            fig, ax = plt.subplots(figsize=(10, 6))

            if baseline is not None and corrected is not None:
                # Plot original, baseline, and corrected
                ax.plot(x, y, 'b-', label='Original', alpha=0.7, linewidth=1.5)
                ax.plot(x, baseline, 'r--', label='Baseline', alpha=0.7, linewidth=2)
                ax.plot(x, corrected, 'g-', label='Corrected', alpha=0.9, linewidth=2)
            else:
                # Plot single spectrum
                ax.plot(x, y, 'b-', linewidth=2)

            ax.set_xlabel('Wavelength/Index', fontsize=12)
            ax.set_ylabel('Intensity', fontsize=12)
            ax.set_title(title, fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.legend()

            plt.tight_layout()

            # Embed in tkinter
            canvas = FigureCanvasTkAgg(fig, plot_window)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        except Exception as e:
            print(f"Plotting error: {e}")

    def _plot_peaks(self, x, y, peaks, title=""):
        """Plot spectrum with detected peaks"""
        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

            plot_window = tk.Toplevel(self.window)
            plot_window.title(f"Peak Detection: {title}")
            plot_window.geometry("800x600")

            fig, ax = plt.subplots(figsize=(10, 6))

            ax.plot(x, y, 'b-', label='Spectrum', alpha=0.7, linewidth=1.5)
            ax.plot(x[peaks], y[peaks], 'ro', label='Peaks', markersize=8)

            ax.set_xlabel('Wavelength/Index', fontsize=12)
            ax.set_ylabel('Intensity', fontsize=12)
            ax.set_title(title, fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.legend()

            plt.tight_layout()

            canvas = FigureCanvasTkAgg(fig, plot_window)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        except Exception as e:
            print(f"Peak plotting error: {e}")

    def _plot_comparison(self, x, y1, y2, title=""):
        """Plot comparison of two spectra"""
        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

            plot_window = tk.Toplevel(self.window)
            plot_window.title(f"Comparison: {title}")
            plot_window.geometry("800x600")

            fig, ax = plt.subplots(figsize=(10, 6))

            ax.plot(x, y1, 'b-', label='Original', alpha=0.7, linewidth=1.5)
            ax.plot(x, y2, 'r-', label='Processed', alpha=0.7, linewidth=1.5)

            ax.set_xlabel('Wavelength/Index', fontsize=12)
            ax.set_ylabel('Intensity', fontsize=12)
            ax.set_title(title, fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.legend()

            plt.tight_layout()

            canvas = FigureCanvasTkAgg(fig, plot_window)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        except Exception as e:
            print(f"Comparison plotting error: {e}")

    def _plot_fit(self, x, y, result, model_name):
        """Plot fitting results"""
        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            import numpy as np

            plot_window = tk.Toplevel(self.window)
            plot_window.title(f"Peak Fitting: {model_name}")
            plot_window.geometry("800x600")

            fig, ax = plt.subplots(figsize=(10, 6))

            # Plot data and fit
            ax.plot(x, y, 'bo', label='Data', alpha=0.6, markersize=4)
            ax.plot(x, result.best_fit, 'r-', label='Fit', linewidth=2)

            # Plot individual components if available
            try:
                components = result.eval_components(x=x)
                for i, comp in enumerate(components.values()):
                    ax.plot(x, comp, '--', alpha=0.5, label=f'Component {i+1}')
            except:
                pass

            ax.set_xlabel('Wavelength/Index', fontsize=12)
            ax.set_ylabel('Intensity', fontsize=12)
            ax.set_title(f'{model_name.capitalize()} Peak Fitting', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.legend()

            # Add fit statistics
            stats_text = f"R² = {result.rsquared:.4f}\nχ² = {result.chisqr:.4f}"
            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
                   verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

            plt.tight_layout()

            canvas = FigureCanvasTkAgg(fig, plot_window)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        except Exception as e:
            print(f"Fit plotting error: {e}")


def setup_plugin(main_app):
    """Plugin setup function"""
    plugin = SpectralToolboxPlugin(main_app)
    return plugin
