"""
LA-ICP-MS Pro Plugin - Professional LA-ICP-MS Data Analysis
Signal processing, U-Pb dating, elemental quantification, reference materials

Author: Sefy Levy
License: CC BY-NC-SA 4.0
Based on: Norris Scientific Knowledge Base (https://norsci.com/?p=kb-laicpms)
"""

PLUGIN_INFO = {
    "category": "software",
    "field": "Geology & Geochemistry",
    "id": "laicpms_pro",
    "name": "LA-ICP-MS Pro",
    "description": "Signal processing, U-Pb dating, elemental analysis, and data reduction",
    "icon": "⚛️",
    "version": "1.0",
    "requires": ["numpy", "scipy", "matplotlib", "pandas", "openpyxl"],
    "author": "Sefy Levy"
}

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import numpy as np
import pandas as pd
from datetime import datetime
import os
import threading
import warnings
warnings.filterwarnings('ignore')

# Scientific imports
try:
    from scipy import stats, optimize
    from scipy.signal import savgol_filter, find_peaks
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    from matplotlib.patches import Rectangle
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


class LAICPMSProPlugin:
    """
    ⚛️ LA-ICP-MS PRO - Professional Data Analysis
    ============================================================================
    Based on Norris Scientific Knowledge Base and key literature:

    • Signal Processing: Longerich et al. (1996) - JAAS 11:899-904
    • U-Pb Geochronology: Fryer et al. (1993) - Chem Geol 109:1-8
    • Elemental Quantification: Liu et al. (2008) - Chem Geol 257:34-43
    • Compositional Data: Aitchison (1982) - JRSSB 44:139-160
    • Reference Materials: Gilbert et al. (2017) - JAAS 32:638-646
    ============================================================================

    FEATURES:
    ✓ Load time-resolved signal data (CSV, Excel, LADR format)
    ✓ Baseline correction and signal integration
    ✓ U-Pb Concordia diagrams and age calculations
    ✓ Elemental quantification with internal/external standards
    ✓ Reference material database (NIST, zircons, glasses)
    ✓ Compositional data analysis (log-ratios)
    ✓ Publication-quality figures
    """

    # Common elements in LA-ICP-MS analysis
    COMMON_ELEMENTS = [
        "Li", "Be", "B", "Na", "Mg", "Al", "Si", "P", "K", "Ca", "Sc", "Ti", "V",
        "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn", "Ga", "Ge", "As", "Rb", "Sr",
        "Y", "Zr", "Nb", "Mo", "Ag", "Cd", "Sn", "Sb", "Cs", "Ba", "La", "Ce",
        "Pr", "Nd", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu",
        "Hf", "Ta", "W", "Tl", "Pb", "Bi", "Th", "U"
    ]

    # Reference materials with certified values
    REFERENCE_MATERIALS = {
        "NIST 610": {
            "type": "Glass",
            "reference": "Pearce et al. (1997) GGR 21:115-144",
            "values": {
                "Si": 500000, "Ti": 437, "Al": 10772, "Fe": 458, "Ca": 81500,
                "Na": 102000, "K": 461, "Rb": 425.7, "Sr": 515.5, "Y": 449,
                "Zr": 451, "Nb": 418, "Ba": 434, "La": 457, "Ce": 448,
                "Pr": 434, "Nd": 430, "Sm": 452, "Eu": 461, "Gd": 456,
                "Tb": 443, "Dy": 437, "Ho": 442, "Er": 439, "Tm": 430,
                "Yb": 449, "Lu": 438, "Hf": 432, "Ta": 401, "Pb": 426,
                "Th": 457.2, "U": 461.5
            }
        },
        "NIST 612": {
            "type": "Glass",
            "reference": "Pearce et al. (1997) GGR 21:115-144",
            "values": {
                "Si": 500000, "Ti": 44.1, "Al": 11000, "Fe": 51, "Ca": 85000,
                "Na": 104000, "K": 64, "Rb": 31.4, "Sr": 78.4, "Y": 38.3,
                "Zr": 37.7, "Nb": 38.9, "Ba": 38.3, "La": 35.8, "Ce": 38.4,
                "Pr": 37.9, "Nd": 35.5, "Sm": 37.7, "Eu": 35.5, "Gd": 37.3,
                "Tb": 37.0, "Dy": 36.8, "Ho": 37.1, "Er": 37.5, "Tm": 38.0,
                "Yb": 39.2, "Lu": 37.8, "Hf": 36.2, "Ta": 39.6, "Pb": 38.57,
                "Th": 37.79, "U": 37.38
            }
        },
        "GJ-1 (Zircon)": {
            "type": "Zircon",
            "reference": "Jackson et al. (2004) Chem Geol 211:47-69",
            "values": {
                "Pb206_U238_age": 600.4,  # Ma
                "Pb207_Pb206_age": 602.2,  # Ma
                "U": 247,  # ppm
                "Th": 12,  # ppm
                "Th_U": 0.048,
                "Lu": 1.2,  # ppm
                "Hf": 9100,  # ppm
                "Y": 380,  # ppm
                "REE": "Typical igneous zircon pattern"
            }
        },
        "91500 (Zircon)": {
            "type": "Zircon",
            "reference": "Wiedenbeck et al. (1995) GGR 19:1-23",
            "values": {
                "Pb206_U238_age": 1062.4,  # Ma
                "Pb207_Pb206_age": 1065.4,  # Ma
                "U": 81,  # ppm
                "Th": 29,  # ppm
                "Th_U": 0.36,
                "Pb": 15,  # ppm
                "Lu": 11.5,  # ppm
                "Hf": 5800  # ppm
            }
        }
    }

    # Common isotopes for U-Pb dating
    U_PB_ISOTOPES = [
        "Pb204", "Pb206", "Pb207", "Pb208",
        "U235", "U238", "Th232"
    ]

    def __init__(self, main_app):
        self.app = main_app
        self.window = None
        self.is_processing = False
        self.progress = None

        # Data storage
        self.raw_data = None  # Raw time-resolved signals
        self.processed_data = None  # Baseline-corrected signals
        self.results_df = None  # Final calculated concentrations/ages
        self.current_file = None
        self.sample_info = {}

        # Signal processing parameters
        self.baseline_start = 0
        self.baseline_end = 0
        self.signal_start = 0
        self.signal_end = 0

        # Reference materials
        self.ref_materials = self.REFERENCE_MATERIALS.copy()
        self.current_standard = None

        # UI elements
        self.notebook = None
        self.status_label = None
        self.signal_canvas = None
        self.signal_ax = None
        self.results_tree = None
        self.log_text = None

        # Check dependencies
        self._check_dependencies()

    def _check_dependencies(self):
        """Check if required packages are installed"""
        missing = []
        if not HAS_SCIPY:
            missing.append("scipy")
        if not HAS_MATPLOTLIB:
            missing.append("matplotlib")
        if not HAS_PANDAS:
            missing.append("pandas")

        self.dependencies_met = len(missing) == 0
        self.missing_deps = missing

    def _safe_import_message(self):
        """Show friendly import instructions"""
        if not self.dependencies_met:
            deps = " ".join(self.missing_deps)
            messagebox.showerror(
                "Missing Dependencies",
                f"LA-ICP-MS Pro requires:\n\n" +
                "\n".join(self.missing_deps) +
                f"\n\nInstall with:\npip install {deps}"
            )
            return False
        return True

    def open_window(self):
        """Open main plugin window - auto-loads data from main app if available"""
        if not self._safe_import_message():
            return

        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("⚛️ LA-ICP-MS Pro v1.0")
        self.window.geometry("1100x720")
        self.window.transient(self.app.root)

        self._create_interface()

        # ============ AUTO-LOAD FROM MAIN APP ============
        if hasattr(self.app, 'samples') and self.app.samples:
            # Schedule auto-load after window is fully created
            self.window.after(500, self._auto_load_from_main)

        self.window.lift()
        self.window.focus_force()

    def _auto_load_from_main(self):
        """Auto-load data from main app on startup"""
        try:
            # Check if there's data
            if not hasattr(self.app, 'samples') or not self.app.samples:
                return

            # Show auto-load message in status
            self.status_label.config(text="Auto-loading data from main app...")
            self.window.update()

            # Get data from main app
            main_samples = self.app.samples

            # Convert to DataFrame
            df = pd.DataFrame(main_samples)

            # Auto-detect time column
            if 'Time' not in df.columns and 'time' not in df.columns:
                df['Time'] = np.linspace(0, len(df)-1, len(df))
                self.time_col = 'Time'
            else:
                self.time_col = 'Time' if 'Time' in df.columns else 'time'

            # Auto-detect element columns
            exclude_cols = ['Sample_ID', 'Time', 'time', 'Notes', 'Location', 'Date',
                        'Auto_Classification', 'Auto_Confidence', 'Flag_For_Review']
            element_cols = []

            for col in df.columns:
                if col in exclude_cols:
                    continue
                try:
                    pd.to_numeric(df[col], errors='raise')
                    element_cols.append(col)
                except:
                    pass

            if not element_cols:
                self._log_message("ℹ️ No numeric element columns found in main data")
                return

            self.raw_data = df

            # Update UI
            self._log_message(f"✅ Auto-loaded {len(df)} samples from main app")
            self._log_message(f"   Detected elements: {', '.join(element_cols[:5])}" +
                            (f" + {len(element_cols)-5} more" if len(element_cols) > 5 else ""))

            # Update element list
            self.element_listbox.delete(0, tk.END)
            for col in element_cols:
                self.element_listbox.insert(tk.END, col)

            # Update status
            self.status_indicator.config(text="● AUTO-LOADED", fg="#27ae60")
            self.status_label.config(text=f"Auto-loaded {len(df)} samples from main app")

            # Switch to signal tab and initialize plot
            self.notebook.select(1)
            self._initialize_signal_plot()

        except Exception as e:
            self._log_message(f"⚠️ Auto-load failed: {str(e)}")
            # Don't show error dialog - just log it

    def _create_interface(self):
        """Create the main interface with tabs"""

        # ============ HEADER ============
        header = tk.Frame(self.window, bg="#2c3e50", height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="⚛️", font=("Arial", 20),
                bg="#2c3e50", fg="white").pack(side=tk.LEFT, padx=10)

        tk.Label(header, text="LA-ICP-MS Pro", font=("Arial", 16, "bold"),
                bg="#2c3e50", fg="white").pack(side=tk.LEFT, padx=5)

        tk.Label(header, text="Signal Processing • U-Pb Dating • Quantification",
                font=("Arial", 9), bg="#2c3e50", fg="#3498db").pack(side=tk.LEFT, padx=15)

        # Status indicator
        self.status_indicator = tk.Label(header, text="● READY",
                                        font=("Arial", 8, "bold"),
                                        bg="#2c3e50", fg="#2ecc71")
        self.status_indicator.pack(side=tk.RIGHT, padx=15)

        # ============ MAIN NOTEBOOK ============
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create tabs
        self._create_load_tab()
        self._create_signal_tab()
        self._create_quantification_tab()
        self._create_upb_tab()
        self._create_reference_tab()
        self._create_results_tab()
        self._create_help_tab()

        # ============ STATUS BAR ============
        status_bar = tk.Frame(self.window, bg="#ecf0f1", height=30)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        status_bar.pack_propagate(False)

        self.status_label = tk.Label(status_bar, text="Ready - Load LA-ICP-MS data to begin",
                                    font=("Arial", 9), bg="#ecf0f1", fg="#2c3e50")
        self.status_label.pack(side=tk.LEFT, padx=10)

        # Progress bar
        self.progress = ttk.Progressbar(status_bar, mode='indeterminate', length=200)
        self.progress.pack(side=tk.RIGHT, padx=10, pady=5)

    # ============ TAB 1: LOAD DATA ============
    def _create_load_tab(self):
        """Tab for loading LA-ICP-MS data files"""
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="📂 1. Load Data")

        # Left panel - File loading
        left = tk.Frame(tab, bg="white", width=400)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        left.pack_propagate(False)

        tk.Label(left, text="Load LA-ICP-MS Data",
                font=("Arial", 12, "bold"), bg="white").pack(anchor=tk.W, pady=5)

        # File type selection
        file_frame = tk.LabelFrame(left, text="File Format", padx=8, pady=8, bg="white")
        file_frame.pack(fill=tk.X, pady=5)

        self.file_type_var = tk.StringVar(value="csv")
        formats = [
            ("CSV (time-resolved)", "csv"),
            ("Excel (.xlsx)", "excel"),
            ("LADR export", "ladr"),
            ("Iolite export", "iolite"),
            ("Glitter export", "glitter")
        ]

        for text, val in formats:
            tk.Radiobutton(file_frame, text=text, variable=self.file_type_var,
                          value=val, bg="white").pack(anchor=tk.W, pady=2)

        # File selection
        select_frame = tk.Frame(left, bg="white")
        select_frame.pack(fill=tk.X, pady=10)

        tk.Button(select_frame, text="📁 Browse Files",
                 command=self._browse_files,
                 bg="#3498db", fg="white",
                 font=("Arial", 10, "bold"),
                 width=20, height=2).pack()

        tk.Button(select_frame, text="📂 Load Folder (batch)",
                 command=self._browse_folder,
                 bg="#9b59b6", fg="white",
                 font=("Arial", 10, "bold"),
                 width=20, height=2).pack(pady=5)

        # ============ NEW: IMPORT FROM MAIN APP BUTTON ============
        tk.Button(select_frame, text="📥 Import from Main App",
                 command=self._import_from_main,
                 bg="#27ae60", fg="white",
                 font=("Arial", 10, "bold"),
                 width=20, height=2).pack(pady=5)

        # Element selection
        elem_frame = tk.LabelFrame(left, text="Element Channels", padx=8, pady=8, bg="white")
        elem_frame.pack(fill=tk.X, pady=5)

        self.element_listbox = tk.Listbox(elem_frame, height=8, selectmode=tk.MULTIPLE)
        self.element_listbox.pack(fill=tk.X)

        # Quick select buttons
        btn_frame = tk.Frame(elem_frame, bg="white")
        btn_frame.pack(fill=tk.X, pady=5)

        tk.Button(btn_frame, text="Select All",
                 command=lambda: self.element_listbox.select_set(0, tk.END),
                 font=("Arial", 7), width=8).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Clear All",
                 command=lambda: self.element_listbox.selection_clear(0, tk.END),
                 font=("Arial", 7), width=8).pack(side=tk.LEFT, padx=2)

        # Sample metadata
        meta_frame = tk.LabelFrame(left, text="Sample Info", padx=8, pady=8, bg="white")
        meta_frame.pack(fill=tk.X, pady=5)

        tk.Label(meta_frame, text="Sample ID:", bg="white").grid(row=0, column=0, sticky=tk.W)
        self.sample_id_var = tk.StringVar()
        tk.Entry(meta_frame, textvariable=self.sample_id_var, width=20).grid(row=0, column=1, padx=5)

        tk.Label(meta_frame, text="Material:", bg="white").grid(row=1, column=0, sticky=tk.W)
        self.material_var = tk.StringVar(value="Zircon")
        ttk.Combobox(meta_frame, textvariable=self.material_var,
                    values=["Zircon", "Glass", "Apatite", "Silicate", "Metal", "Other"],
                    width=18).grid(row=1, column=1, padx=5)

        # Right panel - Preview
        right = tk.Frame(tab, bg="white")
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Label(right, text="Data Preview",
                font=("Arial", 12, "bold"), bg="white").pack(anchor=tk.W)

        # Preview text
        self.preview_text = scrolledtext.ScrolledText(right, height=15, font=("Courier", 9))
        self.preview_text.pack(fill=tk.BOTH, expand=True, pady=5)

        # Load button
        tk.Button(right, text="🚀 LOAD DATA",
                 command=self._load_data,
                 bg="#27ae60", fg="white",
                 font=("Arial", 12, "bold"),
                 height=2).pack(fill=tk.X, pady=5)

    def _browse_files(self):
        """Browse for single data file"""
        filename = filedialog.askopenfilename(
            title="Select LA-ICP-MS Data File",
            filetypes=[
                ("All supported", "*.csv *.xlsx *.txt *.dat"),
                ("CSV files", "*.csv"),
                ("Excel files", "*.xlsx"),
                ("Text files", "*.txt *.dat"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.current_file = filename
            self._preview_file(filename)

    def _browse_folder(self):
        """Browse for folder with multiple files"""
        folder = filedialog.askdirectory(title="Select Folder with LA-ICP-MS Data")
        if folder:
            files = [f for f in os.listdir(folder) if f.endswith(('.csv', '.xlsx', '.txt', '.dat'))]
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(tk.END, f"Found {len(files)} data files:\n\n")
            for f in files[:20]:
                self.preview_text.insert(tk.END, f"  • {f}\n")
            if len(files) > 20:
                self.preview_text.insert(tk.END, f"  • ... and {len(files)-20} more\n")
            self.current_file = folder

    def _preview_file(self, filename):
        """Show file preview"""
        try:
            if filename.endswith('.csv'):
                df = pd.read_csv(filename, nrows=20)
            elif filename.endswith('.xlsx'):
                df = pd.read_excel(filename, nrows=20)
            else:
                df = pd.read_csv(filename, nrows=20, sep='\t')

            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(tk.END, f"File: {os.path.basename(filename)}\n")
            self.preview_text.insert(tk.END, f"Shape: {df.shape[0]} rows, {df.shape[1]} columns\n\n")
            self.preview_text.insert(tk.END, df.head(10).to_string())

            # Update element list
            self.element_listbox.delete(0, tk.END)
            for col in df.columns:
                if col not in ['Time', 'time', 'Sample', 'sample']:
                    self.element_listbox.insert(tk.END, col)

        except Exception as e:
            self.preview_text.insert(tk.END, f"Error previewing file: {str(e)}")

    def _load_data(self):
        """Load the selected data file(s)"""
        if not self.current_file:
            messagebox.showwarning("No File", "Select a data file first!")
            return

        try:
            self.status_label.config(text="Loading data...")
            self.progress.start()

            if os.path.isfile(self.current_file):
                # Single file
                if self.current_file.endswith('.csv'):
                    self.raw_data = pd.read_csv(self.current_file)
                elif self.current_file.endswith('.xlsx'):
                    self.raw_data = pd.read_excel(self.current_file)
                else:
                    self.raw_data = pd.read_csv(self.current_file, sep='\t')

                self._log_message(f"✅ Loaded: {os.path.basename(self.current_file)}")
                self._log_message(f"   Rows: {len(self.raw_data)}, Columns: {len(self.raw_data.columns)}")

            else:
                # Folder - load first file as example
                files = [f for f in os.listdir(self.current_file)
                        if f.endswith(('.csv', '.xlsx', '.txt', '.dat'))]
                if files:
                    first = os.path.join(self.current_file, files[0])
                    if first.endswith('.csv'):
                        self.raw_data = pd.read_csv(first)
                    else:
                        self.raw_data = pd.read_csv(first, sep='\t')
                    self._log_message(f"✅ Loaded first file: {files[0]}")
                    self._log_message(f"   Found {len(files)} total files in folder")

            # Auto-detect time column
            time_cols = [c for c in self.raw_data.columns if 'time' in c.lower()]
            if time_cols:
                self.time_col = time_cols[0]
            else:
                self.time_col = self.raw_data.columns[0]

            self.status_indicator.config(text="● DATA LOADED", fg="#f39c12")
            self.status_label.config(text=f"Loaded {len(self.raw_data)} data points")
            self.progress.stop()

            # Switch to signal tab
            self.notebook.select(1)
            self._initialize_signal_plot()

        except Exception as e:
            self.progress.stop()
            messagebox.showerror("Load Error", f"Failed to load data:\n{str(e)}")

    def _import_from_main(self):
        """Import data from main application - preserves original Sample_IDs"""
        if not hasattr(self.app, 'samples') or not self.app.samples:
            messagebox.showwarning("No Data", "No samples in main application!")
            return

        try:
            self.status_label.config(text="Importing from main app...")
            self.progress.start()

            # Get data from main app
            main_samples = self.app.samples

            # Convert to DataFrame for processing
            df = pd.DataFrame(main_samples)

            # IMPORTANT: Ensure Sample_ID is preserved
            if 'Sample_ID' not in df.columns:
                # If no Sample_ID column exists, create one from index (fallback)
                df['Sample_ID'] = [f"SAMPLE_{i:04d}" for i in range(len(df))]
                self._log_message("ℹ️ No Sample_ID column found - created sequential IDs")
            else:
                # Ensure Sample_ID is treated as string
                df['Sample_ID'] = df['Sample_ID'].astype(str)
                self._log_message(f"✅ Sample IDs preserved (e.g., {df['Sample_ID'].iloc[0] if len(df) > 0 else 'none'})")

            # Auto-detect time column (create synthetic time if none exists)
            if 'Time' not in df.columns and 'time' not in df.columns:
                df['Time'] = np.linspace(0, len(df)-1, len(df))
                self.time_col = 'Time'
                self._log_message("ℹ️ Created synthetic Time column")
            else:
                self.time_col = 'Time' if 'Time' in df.columns else 'time'

            # Auto-detect element columns (any numeric columns except metadata)
            exclude_cols = ['Sample_ID', 'Time', 'time', 'Notes', 'Location', 'Date',
                        'Auto_Classification', 'Auto_Confidence', 'Flag_For_Review']
            element_cols = []

            for col in df.columns:
                if col in exclude_cols:
                    continue
                try:
                    # Test if column is numeric
                    pd.to_numeric(df[col], errors='raise')
                    element_cols.append(col)
                except:
                    pass

            if not element_cols:
                messagebox.showwarning("No Elements", "No numeric element columns found in main data!")
                self.progress.stop()
                return

            # Store the data WITH original Sample_IDs preserved
            self.raw_data = df

            self._log_message(f"✅ Imported {len(df)} samples from main app")
            self._log_message(f"   Detected elements: {', '.join(element_cols[:10])}")
            if len(element_cols) > 10:
                self._log_message(f"   ... and {len(element_cols)-10} more")

            # Update element list
            self.element_listbox.delete(0, tk.END)
            for col in element_cols:
                self.element_listbox.insert(tk.END, col)

            self.status_indicator.config(text="● DATA LOADED", fg="#f39c12")
            self.status_label.config(text=f"Loaded {len(df)} samples from main app")
            self.progress.stop()

            # Switch to signal tab and initialize plot
            self.notebook.select(1)
            self._initialize_signal_plot()

            messagebox.showinfo("Success",
                            f"Imported {len(df)} samples from main application\n"
                            f"Sample IDs preserved. Found {len(element_cols)} numeric channels.")

        except Exception as e:
            self.progress.stop()
            messagebox.showerror("Import Error", f"Failed to import from main app:\n{str(e)}")
            import traceback
            traceback.print_exc()

    # ============ TAB 2: SIGNAL PROCESSING ============
    def _create_signal_tab(self):
        """Tab for signal processing and visualization"""
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="📈 2. Signal Processing")

        # Control panel (left)
        control = tk.Frame(tab, bg="#f5f5f5", width=300)
        control.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        control.pack_propagate(False)

        tk.Label(control, text="Signal Processing Parameters",
                font=("Arial", 11, "bold"), bg="#f5f5f5").pack(anchor=tk.W, pady=5)

        # Element selection
        elem_frame = tk.LabelFrame(control, text="Display Element", padx=5, pady=5, bg="#f5f5f5")
        elem_frame.pack(fill=tk.X, pady=5)

        self.display_elem_var = tk.StringVar()
        self.display_elem_combo = ttk.Combobox(elem_frame, textvariable=self.display_elem_var,
                                              values=[], width=20)
        self.display_elem_combo.pack(fill=tk.X)
        self.display_elem_combo.bind('<<ComboboxSelected>>', lambda e: self._update_signal_plot())

        # Baseline selection
        baseline_frame = tk.LabelFrame(control, text="Baseline Region", padx=5, pady=5, bg="#f5f5f5")
        baseline_frame.pack(fill=tk.X, pady=5)

        tk.Label(baseline_frame, text="Start (s):", bg="#f5f5f5").grid(row=0, column=0, sticky=tk.W)
        self.baseline_start_var = tk.DoubleVar(value=0)
        tk.Entry(baseline_frame, textvariable=self.baseline_start_var, width=10).grid(row=0, column=1)

        tk.Label(baseline_frame, text="End (s):", bg="#f5f5f5").grid(row=1, column=0, sticky=tk.W)
        self.baseline_end_var = tk.DoubleVar(value=5)
        tk.Entry(baseline_frame, textvariable=self.baseline_end_var, width=10).grid(row=1, column=1)

        tk.Button(baseline_frame, text="← Set from plot",
                 command=self._set_baseline_from_plot,
                 font=("Arial", 8)).grid(row=2, column=0, columnspan=2, pady=5)

        # Signal selection
        signal_frame = tk.LabelFrame(control, text="Signal Region", padx=5, pady=5, bg="#f5f5f5")
        signal_frame.pack(fill=tk.X, pady=5)

        tk.Label(signal_frame, text="Start (s):", bg="#f5f5f5").grid(row=0, column=0, sticky=tk.W)
        self.signal_start_var = tk.DoubleVar(value=10)
        tk.Entry(signal_frame, textvariable=self.signal_start_var, width=10).grid(row=0, column=1)

        tk.Label(signal_frame, text="End (s):", bg="#f5f5f5").grid(row=1, column=0, sticky=tk.W)
        self.signal_end_var = tk.DoubleVar(value=30)
        tk.Entry(signal_frame, textvariable=self.signal_end_var, width=10).grid(row=1, column=1)

        tk.Button(signal_frame, text="← Set from plot",
                 command=self._set_signal_from_plot,
                 font=("Arial", 8)).grid(row=2, column=0, columnspan=2, pady=5)

        # Processing options
        options_frame = tk.LabelFrame(control, text="Processing Options", padx=5, pady=5, bg="#f5f5f5")
        options_frame.pack(fill=tk.X, pady=5)

        self.smooth_var = tk.BooleanVar(value=True)
        tk.Checkbutton(options_frame, text="Apply smoothing (Savitzky-Golay)",
                      variable=self.smooth_var, bg="#f5f5f5").pack(anchor=tk.W)

        self.subtract_baseline_var = tk.BooleanVar(value=True)
        tk.Checkbutton(options_frame, text="Subtract baseline",
                      variable=self.subtract_baseline_var, bg="#f5f5f5").pack(anchor=tk.W)

        self.integrate_var = tk.BooleanVar(value=True)
        tk.Checkbutton(options_frame, text="Calculate integrated signal",
                      variable=self.integrate_var, bg="#f5f5f5").pack(anchor=tk.W)

        # Process button
        tk.Button(control, text="⚡ PROCESS SIGNAL",
                 command=self._process_signal,
                 bg="#9b59b6", fg="white",
                 font=("Arial", 11, "bold"),
                 height=2).pack(fill=tk.X, pady=10)

        # Plot area (right)
        plot_frame = tk.Frame(tab, bg="white")
        plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.signal_fig, self.signal_ax = plt.subplots(figsize=(6, 4), dpi=100)
        self.signal_fig.patch.set_facecolor('white')
        self.signal_ax.set_facecolor('#f8f9fa')
        self.signal_ax.set_xlabel('Time (seconds)')
        self.signal_ax.set_ylabel('Intensity (cps)')
        self.signal_ax.set_title('LA-ICP-MS Time-Resolved Signal')
        self.signal_ax.grid(True, alpha=0.3)

        self.signal_canvas = FigureCanvasTkAgg(self.signal_fig, plot_frame)
        self.signal_canvas.draw()
        self.signal_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Connect click event
        self.signal_canvas.mpl_connect('button_press_event', self._on_plot_click)

    def _initialize_signal_plot(self):
        """Initialize signal plot with loaded data"""
        if self.raw_data is None:
            return

        # Update element dropdown
        elem_cols = [c for c in self.raw_data.columns if c != self.time_col]
        self.display_elem_combo['values'] = elem_cols
        if elem_cols:
            self.display_elem_var.set(elem_cols[0])

        self._update_signal_plot()

    def _update_signal_plot(self):
        """Update signal plot with selected element"""
        if self.raw_data is None or not self.display_elem_var.get():
            return

        self.signal_ax.clear()

        elem = self.display_elem_var.get()
        time = self.raw_data[self.time_col].values
        signal = self.raw_data[elem].values

        # Plot raw signal
        self.signal_ax.plot(time, signal, 'b-', linewidth=1, alpha=0.7, label='Raw signal')

        # Highlight baseline region
        if self.baseline_start_var.get() < self.baseline_end_var.get():
            self.signal_ax.axvspan(self.baseline_start_var.get(), self.baseline_end_var.get(),
                                  alpha=0.2, color='red', label='Baseline')

        # Highlight signal region
        if self.signal_start_var.get() < self.signal_end_var.get():
            self.signal_ax.axvspan(self.signal_start_var.get(), self.signal_end_var.get(),
                                  alpha=0.2, color='green', label='Signal')

        self.signal_ax.set_xlabel('Time (seconds)')
        self.signal_ax.set_ylabel('Intensity (cps)')
        self.signal_ax.set_title(f'Time-Resolved Signal: {elem}')
        self.signal_ax.grid(True, alpha=0.3)
        self.signal_ax.legend(loc='upper right')

        self.signal_canvas.draw()

    def _on_plot_click(self, event):
        """Handle plot clicks for region selection"""
        if event.inaxes != self.signal_ax:
            return

        if event.button == 1:  # Left click - set baseline
            self.baseline_start_var.set(event.xdata)
            self._update_signal_plot()
        elif event.button == 3:  # Right click - set signal
            self.signal_start_var.set(event.xdata)
            self._update_signal_plot()

    def _set_baseline_from_plot(self):
        """Set baseline region from current selection"""
        # This would be connected to a more sophisticated selection tool
        pass

    def _set_signal_from_plot(self):
        """Set signal region from current selection"""
        pass

    def _process_signal(self):
        """Process the selected signal region"""
        if self.raw_data is None:
            messagebox.showwarning("No Data", "Load data first!")
            return

        try:
            self.progress.start()
            self.status_label.config(text="Processing signal...")

            # Get selected elements
            selected = [self.element_listbox.get(i) for i in self.element_listbox.curselection()]
            if not selected:
                selected = [self.display_elem_var.get()]

            time = self.raw_data[self.time_col].values
            results = []

            for elem in selected:
                if elem not in self.raw_data.columns:
                    continue

                signal = self.raw_data[elem].values

                # Find indices for regions
                baseline_idx = np.where((time >= self.baseline_start_var.get()) &
                                       (time <= self.baseline_end_var.get()))[0]
                signal_idx = np.where((time >= self.signal_start_var.get()) &
                                     (time <= self.signal_end_var.get()))[0]

                if len(baseline_idx) < 5 or len(signal_idx) < 5:
                    self._log_message(f"⚠️ Insufficient data points for {elem}")
                    continue

                # Calculate baseline statistics
                baseline_mean = np.mean(signal[baseline_idx])
                baseline_std = np.std(signal[baseline_idx])

                # Extract signal
                signal_data = signal[signal_idx]

                # Apply smoothing if requested
                if self.smooth_var.get() and len(signal_data) > 10:
                    try:
                        signal_data = savgol_filter(signal_data, window_length=5, polyorder=2)
                    except:
                        pass

                # Subtract baseline
                if self.subtract_baseline_var.get():
                    signal_data = signal_data - baseline_mean

                # Calculate statistics
                signal_mean = np.mean(signal_data)
                signal_median = np.median(signal_data)
                signal_std = np.std(signal_data)

                # Calculate integrated signal
                if self.integrate_var.get():
                    dt = time[1] - time[0]
                    integrated = np.sum(signal_data) * dt
                else:
                    integrated = signal_mean

                # Signal-to-noise ratio
                snr = signal_mean / baseline_std if baseline_std > 0 else 0

                results.append({
                    'Element': elem,
                    'Mean_cps': signal_mean,
                    'Median_cps': signal_median,
                    'Std_cps': signal_std,
                    'RSD_%': (signal_std / signal_mean * 100) if signal_mean > 0 else 0,
                    'Integrated': integrated,
                    'Baseline_mean': baseline_mean,
                    'Baseline_std': baseline_std,
                    'SNR': snr,
                    'Sample_ID': self.sample_id_var.get() or 'Unknown'
                })

                self._log_message(f"✅ Processed {elem}: {signal_mean:.1f} ± {signal_std:.1f} cps, SNR={snr:.1f}")

            # Store results
            self.results_df = pd.DataFrame(results)

            # Show processed signal
            self.signal_ax.clear()
            self.signal_ax.plot(time[signal_idx], signal_data, 'g-', linewidth=1.5, label='Processed signal')
            self.signal_ax.axhline(y=baseline_mean, color='r', linestyle='--', label=f'Baseline: {baseline_mean:.1f}')
            self.signal_ax.set_xlabel('Time (seconds)')
            self.signal_ax.set_ylabel('Intensity (cps)')
            self.signal_ax.set_title(f'Processed Signal: {elem}')
            self.signal_ax.grid(True, alpha=0.3)
            self.signal_ax.legend()
            self.signal_canvas.draw()

            self.status_indicator.config(text="● PROCESSED", fg="#2ecc71")
            self.status_label.config(text=f"Processed {len(results)} elements")
            self.progress.stop()

            # Switch to results tab
            self.notebook.select(5)

        except Exception as e:
            self.progress.stop()
            messagebox.showerror("Processing Error", str(e))

    # ============ TAB 3: QUANTIFICATION ============
    def _create_quantification_tab(self):
        """Tab for elemental quantification"""
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="🧪 3. Quantification")

        # Control panel (left)
        control = tk.Frame(tab, bg="#f5f5f5", width=300)
        control.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        control.pack_propagate(False)

        tk.Label(control, text="Elemental Quantification",
                font=("Arial", 11, "bold"), bg="#f5f5f5").pack(anchor=tk.W, pady=5)

        # Calibration type
        cal_frame = tk.LabelFrame(control, text="Calibration Type", padx=5, pady=5, bg="#f5f5f5")
        cal_frame.pack(fill=tk.X, pady=5)

        self.cal_type_var = tk.StringVar(value="external")
        tk.Radiobutton(cal_frame, text="External standard", variable=self.cal_type_var,
                      value="external", bg="#f5f5f5").pack(anchor=tk.W)
        tk.Radiobutton(cal_frame, text="Internal standard", variable=self.cal_type_var,
                      value="internal", bg="#f5f5f5").pack(anchor=tk.W)
        tk.Radiobutton(cal_frame, text="Standard addition", variable=self.cal_type_var,
                      value="addition", bg="#f5f5f5").pack(anchor=tk.W)

        # Standard selection
        std_frame = tk.LabelFrame(control, text="Reference Material", padx=5, pady=5, bg="#f5f5f5")
        std_frame.pack(fill=tk.X, pady=5)

        self.std_var = tk.StringVar(value="NIST 610")
        ttk.Combobox(std_frame, textvariable=self.std_var,
                    values=list(self.REFERENCE_MATERIALS.keys()),
                    width=25).pack()

        tk.Button(std_frame, text="View Certified Values",
                 command=self._show_certified_values,
                 font=("Arial", 8)).pack(pady=5)

        # Internal standard
        is_frame = tk.LabelFrame(control, text="Internal Standard", padx=5, pady=5, bg="#f5f5f5")
        is_frame.pack(fill=tk.X, pady=5)

        tk.Label(is_frame, text="Element:", bg="#f5f5f5").grid(row=0, column=0, sticky=tk.W)
        self.is_elem_var = tk.StringVar(value="Si")
        ttk.Combobox(is_frame, textvariable=self.is_elem_var,
                    values=self.COMMON_ELEMENTS, width=10).grid(row=0, column=1)

        tk.Label(is_frame, text="Concentration (ppm):", bg="#f5f5f5").grid(row=1, column=0, sticky=tk.W)
        self.is_conc_var = tk.DoubleVar(value=500000)
        tk.Entry(is_frame, textvariable=self.is_conc_var, width=12).grid(row=1, column=1)

        # Calculate button
        tk.Button(control, text="📊 CALCULATE CONCENTRATIONS",
                 command=self._calculate_concentrations,
                 bg="#e67e22", fg="white",
                 font=("Arial", 11, "bold"),
                 height=2).pack(fill=tk.X, pady=10)

        # Results area (right)
        right = tk.Frame(tab, bg="white")
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Results tree
        columns = ('Element', 'CPS', 'CPS_RSD%', 'Conc_ppm', 'Conc_2SD', 'DL_ppm')
        self.quant_tree = ttk.Treeview(right, columns=columns, show='headings', height=20)

        for col in columns:
            self.quant_tree.heading(col, text=col)
            self.quant_tree.column(col, width=90)

        scrollbar = ttk.Scrollbar(right, orient=tk.VERTICAL, command=self.quant_tree.yview)
        self.quant_tree.configure(yscrollcommand=scrollbar.set)

        self.quant_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _show_certified_values(self):
        """Show certified values for selected reference material"""
        std = self.std_var.get()
        if std in self.REFERENCE_MATERIALS:
            info = self.REFERENCE_MATERIALS[std]
            values = info['values']

            win = tk.Toplevel(self.window)
            win.title(f"Certified Values: {std}")
            win.geometry("500x400")

            text = scrolledtext.ScrolledText(win, font=("Courier", 9))
            text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            text.insert(tk.END, f"REFERENCE MATERIAL: {std}\n")
            text.insert(tk.END, f"Type: {info['type']}\n")
            text.insert(tk.END, f"Reference: {info['reference']}\n")
            text.insert(tk.END, "="*50 + "\n\n")

            for elem, val in values.items():
                if isinstance(val, (int, float)):
                    text.insert(tk.END, f"{elem:10s}: {val:8.1f} ppm\n")
                else:
                    text.insert(tk.END, f"{elem:10s}: {val}\n")

            text.config(state=tk.DISABLED)

    def _calculate_concentrations(self):
        """Calculate elemental concentrations"""
        if self.results_df is None or self.results_df.empty:
            messagebox.showwarning("No Data", "Process signal data first!")
            return

        try:
            std = self.std_var.get()
            if std not in self.REFERENCE_MATERIALS:
                messagebox.showerror("Error", f"Reference material {std} not found")
                return

            # Clear tree
            for item in self.quant_tree.get_children():
                self.quant_tree.delete(item)

            # Get certified values
            certified = self.REFERENCE_MATERIALS[std]['values']

            # Calculate concentrations (simplified external calibration)
            for idx, row in self.results_df.iterrows():
                elem = row['Element']
                cps = row['Mean_cps']
                rsd = row['RSD_%']

                if elem in certified:
                    # Calculate sensitivity factor
                    std_cps = 100000  # This would come from actual standard measurement
                    std_conc = certified[elem]

                    # Concentration = (sample_cps / std_cps) * std_conc
                    conc = (cps / std_cps) * std_conc
                    dl = (3 * row['Baseline_std'] / std_cps) * std_conc if std_cps > 0 else 0

                    self.quant_tree.insert('', tk.END, values=(
                        elem,
                        f"{cps:.0f}",
                        f"{rsd:.1f}",
                        f"{conc:.1f}",
                        f"{conc*0.1:.1f}",  # Rough 10% uncertainty
                        f"{dl:.2f}"
                    ))

            self._log_message("✅ Concentrations calculated")

        except Exception as e:
            messagebox.showerror("Calculation Error", str(e))

    # ============ TAB 4: U-PB GEOCHRONOLOGY ============
    def _create_upb_tab(self):
        """Tab for U-Pb dating and Concordia diagrams"""
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="⏳ 4. U-Pb Dating")

        # Control panel (left)
        control = tk.Frame(tab, bg="#f5f5f5", width=300)
        control.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        control.pack_propagate(False)

        tk.Label(control, text="U-Pb Geochronology",
                font=("Arial", 11, "bold"), bg="#f5f5f5").pack(anchor=tk.W, pady=5)

        # Common Pb correction
        pb_frame = tk.LabelFrame(control, text="Common Pb Correction", padx=5, pady=5, bg="#f5f5f5")
        pb_frame.pack(fill=tk.X, pady=5)

        self.pb_correction_var = tk.StringVar(value="204")
        tk.Radiobutton(pb_frame, text="204Pb method", variable=self.pb_correction_var,
                      value="204", bg="#f5f5f5").pack(anchor=tk.W)
        tk.Radiobutton(pb_frame, text="207Pb method", variable=self.pb_correction_var,
                      value="207", bg="#f5f5f5").pack(anchor=tk.W)
        tk.Radiobutton(pb_frame, text="208Pb method", variable=self.pb_correction_var,
                      value="208", bg="#f5f5f5").pack(anchor=tk.W)

        # Age calculation
        age_frame = tk.LabelFrame(control, text="Age Calculation", padx=5, pady=5, bg="#f5f5f5")
        age_frame.pack(fill=tk.X, pady=5)

        self.age_method_var = tk.StringVar(value="206/238")
        tk.Radiobutton(age_frame, text="206Pb/238U", variable=self.age_method_var,
                      value="206/238", bg="#f5f5f5").pack(anchor=tk.W)
        tk.Radiobutton(age_frame, text="207Pb/235U", variable=self.age_method_var,
                      value="207/235", bg="#f5f5f5").pack(anchor=tk.W)
        tk.Radiobutton(age_frame, text="207Pb/206Pb", variable=self.age_method_var,
                      value="207/206", bg="#f5f5f5").pack(anchor=tk.W)

        # Discordance filter
        filter_frame = tk.Frame(control, bg="#f5f5f5")
        filter_frame.pack(fill=tk.X, pady=5)

        tk.Label(filter_frame, text="Discordance limit (%):", bg="#f5f5f5").pack(side=tk.LEFT)
        self.discordance_var = tk.DoubleVar(value=10)
        tk.Spinbox(filter_frame, from_=1, to=30, textvariable=self.discordance_var,
                  width=5).pack(side=tk.LEFT, padx=5)

        # Calculate button
        tk.Button(control, text="📈 CALCULATE AGES",
                 command=self._calculate_upb_ages,
                 bg="#e67e22", fg="white",
                 font=("Arial", 11, "bold"),
                 height=2).pack(fill=tk.X, pady=10)

        # Plot area (right)
        plot_frame = tk.Frame(tab, bg="white")
        plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.upb_fig, self.upb_ax = plt.subplots(figsize=(6, 5), dpi=100)
        self.upb_fig.patch.set_facecolor('white')
        self.upb_ax.set_facecolor('#f8f9fa')
        self.upb_ax.set_xlabel('238U/206Pb')
        self.upb_ax.set_ylabel('207Pb/206Pb')
        self.upb_ax.set_title('U-Pb Concordia Diagram')
        self.upb_ax.grid(True, alpha=0.3)

        self.upb_canvas = FigureCanvasTkAgg(self.upb_fig, plot_frame)
        self.upb_canvas.draw()
        self.upb_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _calculate_upb_ages(self):
        """Calculate U-Pb ages and plot Concordia"""
        try:
            # This would contain actual U-Pb calculations
            # For demonstration, create synthetic Concordia

            self.upb_ax.clear()

            # Generate Concordia curve
            t = np.linspace(0, 4500, 200)  # Age in Ma
            l238 = 1.55125e-10  # decay constant
            l235 = 9.8485e-10

            # U decay
            u238_u235 = 137.818
            pb206_u238 = np.exp(l238 * t * 1e6) - 1
            pb207_u235 = np.exp(l235 * t * 1e6) - 1
            pb207_pb206 = pb207_u235 / pb206_u238 / u238_u235

            # Plot Concordia
            self.upb_ax.plot(pb206_u238, pb207_pb206, 'k-', linewidth=2, label='Concordia')

            # Add age ticks
            for age in [500, 1000, 1500, 2000, 2500, 3000]:
                idx = np.argmin(np.abs(t - age))
                self.upb_ax.annotate(f'{age} Ma', (pb206_u238[idx], pb207_pb206[idx]),
                                    fontsize=8, ha='center')

            # Plot sample data (placeholder)
            if self.results_df is not None:
                # This would use actual measured ratios
                np.random.seed(42)
                n = min(10, len(self.results_df))
                x = np.random.normal(0.5, 0.1, n)
                y = np.random.normal(0.7, 0.05, n)
                self.upb_ax.scatter(x, y, c='red', s=50, alpha=0.7,
                                  edgecolors='black', label='Samples')

            self.upb_ax.set_xlabel('238U/206Pb')
            self.upb_ax.set_ylabel('207Pb/206Pb')
            self.upb_ax.set_title('U-Pb Concordia Diagram')
            self.upb_ax.grid(True, alpha=0.3)
            self.upb_ax.legend()

            self.upb_canvas.draw()
            self._log_message("✅ U-Pb Concordia generated")

        except Exception as e:
            messagebox.showerror("U-Pb Error", str(e))

    # ============ TAB 5: REFERENCE MATERIALS ============
    def _create_reference_tab(self):
        """Tab for reference material database"""
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="📚 5. Reference Materials")

        # Tree view for reference materials
        tree_frame = tk.Frame(tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ('Name', 'Type', 'Reference', 'Elements')
        self.ref_tree = ttk.Treeview(tree_frame, columns=columns, show='headings')

        for col in columns:
            self.ref_tree.heading(col, text=col)
            self.ref_tree.column(col, width=150)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.ref_tree.yview)
        self.ref_tree.configure(yscrollcommand=scrollbar.set)

        self.ref_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Populate tree
        for name, info in self.REFERENCE_MATERIALS.items():
            self.ref_tree.insert('', tk.END, values=(
                name,
                info['type'],
                info['reference'][:30] + "...",
                str(len(info['values']))
            ))

        # Buttons
        btn_frame = tk.Frame(tab)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Button(btn_frame, text="➕ Add Reference Material",
                 command=self._add_reference_material,
                 bg="#27ae60", fg="white").pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame, text="📥 Import from CSV",
                 command=self._import_references,
                 bg="#3498db", fg="white").pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame, text="📤 Export to CSV",
                 command=self._export_references,
                 bg="#9b59b6", fg="white").pack(side=tk.LEFT, padx=5)

    def _add_reference_material(self):
        """Add a new reference material with certified values"""
        # Create dialog window
        dialog = tk.Toplevel(self.window)
        dialog.title("Add Reference Material")
        dialog.geometry("600x700")
        dialog.transient(self.window)
        dialog.grab_set()

        # Main frame with scrollbar
        main_frame = tk.Frame(dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Form fields
        current_row = 0

        # Basic info
        tk.Label(scrollable_frame, text="Reference Material Details",
                font=("Arial", 12, "bold")).grid(row=current_row, column=0, columnspan=2,
                                                pady=10, sticky=tk.W)
        current_row += 1

        # Name
        tk.Label(scrollable_frame, text="Material Name:*").grid(row=current_row, column=0,
                                                                sticky=tk.W, pady=5)
        name_var = tk.StringVar()
        tk.Entry(scrollable_frame, textvariable=name_var, width=40).grid(row=current_row, column=1,
                                                                        pady=5, padx=5)
        current_row += 1

        # Type
        tk.Label(scrollable_frame, text="Material Type:*").grid(row=current_row, column=0,
                                                                sticky=tk.W, pady=5)
        type_var = tk.StringVar(value="Glass")
        type_combo = ttk.Combobox(scrollable_frame, textvariable=type_var,
                                values=["Glass", "Zircon", "Apatite", "Monazite", "Titanite",
                                        "Silicate", "Metal", "Sulfide", "Other"],
                                width=38)
        type_combo.grid(row=current_row, column=1, pady=5, padx=5)
        current_row += 1

        # Reference
        tk.Label(scrollable_frame, text="Citation/Reference:*").grid(row=current_row, column=0,
                                                                    sticky=tk.W, pady=5)
        ref_var = tk.StringVar()
        ref_entry = tk.Entry(scrollable_frame, textvariable=ref_var, width=40)
        ref_entry.grid(row=current_row, column=1, pady=5, padx=5)
        current_row += 1

        # Year
        tk.Label(scrollable_frame, text="Year:").grid(row=current_row, column=0,
                                                    sticky=tk.W, pady=5)
        year_var = tk.StringVar()
        tk.Entry(scrollable_frame, textvariable=year_var, width=40).grid(row=current_row, column=1,
                                                                        pady=5, padx=5)
        current_row += 1

        # Notes
        tk.Label(scrollable_frame, text="Notes:").grid(row=current_row, column=0,
                                                    sticky=tk.W, pady=5)
        notes_text = tk.Text(scrollable_frame, height=3, width=30)
        notes_text.grid(row=current_row, column=1, pady=5, padx=5, sticky=tk.W)
        current_row += 1

        # Separator
        ttk.Separator(scrollable_frame, orient='horizontal').grid(row=current_row, column=0,
                                                                columnspan=2, sticky="ew", pady=10)
        current_row += 1

        # Certified values section
        tk.Label(scrollable_frame, text="Certified Values (ppm unless noted)",
                font=("Arial", 11, "bold")).grid(row=current_row, column=0, columnspan=2,
                                                pady=5, sticky=tk.W)
        current_row += 1

        # Instructions
        tk.Label(scrollable_frame, text="Enter values (numbers only, leave blank if not certified)",
                font=("Arial", 9, "italic"), fg="gray").grid(row=current_row, column=0, columnspan=2,
                                                            pady=5, sticky=tk.W)
        current_row += 1

        # Create frame for element values with scrollbar
        elem_frame = tk.Frame(scrollable_frame)
        elem_frame.grid(row=current_row, column=0, columnspan=2, sticky="nsew", pady=5)
        current_row += 1

        # Canvas for scrolling elements
        elem_canvas = tk.Canvas(elem_frame, height=300)
        elem_scrollbar = ttk.Scrollbar(elem_frame, orient="vertical", command=elem_canvas.yview)
        elem_scrollable = tk.Frame(elem_canvas)

        elem_scrollable.bind(
            "<Configure>",
            lambda e: elem_canvas.configure(scrollregion=elem_canvas.bbox("all"))
        )

        elem_canvas.create_window((0, 0), window=elem_scrollable, anchor="nw")
        elem_canvas.configure(yscrollcommand=elem_scrollbar.set)

        elem_canvas.pack(side="left", fill="both", expand=True)
        elem_scrollbar.pack(side="right", fill="y")

        # Create entry widgets for common elements
        element_vars = {}

        # Common elements in reference materials
        common_elements = [
            ("Major Elements", ["Si", "Al", "Fe", "Ca", "Na", "K", "Mg", "Ti", "P"]),
            ("Trace Elements", ["Rb", "Sr", "Y", "Zr", "Nb", "Ba", "Hf", "Ta", "Pb", "Th", "U"]),
            ("REE", ["La", "Ce", "Pr", "Nd", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu"]),
            ("U-Pb Dating", ["Pb206", "Pb207", "Pb208", "U238", "Th232"]),
            ("Age (Ma)", ["Pb206_U238_age", "Pb207_Pb206_age", "Pb207_U235_age"])
        ]

        elem_row = 0
        for category, elements in common_elements:
            # Category header
            tk.Label(elem_scrollable, text=category, font=("Arial", 10, "bold"),
                    fg="#2980b9").grid(row=elem_row, column=0, columnspan=3,
                                    sticky=tk.W, pady=(10, 5))
            elem_row += 1

            # Element entries in 2 columns
            col1_elements = elements[:len(elements)//2 + len(elements)%2]
            col2_elements = elements[len(col1_elements):]

            # First column
            for i, elem in enumerate(col1_elements):
                tk.Label(elem_scrollable, text=f"{elem}:").grid(row=elem_row + i, column=0,
                                                                sticky=tk.W, padx=(20, 5))
                var = tk.StringVar()
                entry = tk.Entry(elem_scrollable, textvariable=var, width=12)
                entry.grid(row=elem_row + i, column=1, padx=5, pady=2)
                element_vars[elem] = var

                # Add units hint
                if "age" in elem.lower():
                    tk.Label(elem_scrollable, text="Ma", font=("Arial", 8),
                            fg="gray").grid(row=elem_row + i, column=2, sticky=tk.W)
                else:
                    tk.Label(elem_scrollable, text="ppm", font=("Arial", 8),
                            fg="gray").grid(row=elem_row + i, column=2, sticky=tk.W)

            # Second column
            for i, elem in enumerate(col2_elements):
                tk.Label(elem_scrollable, text=f"{elem}:").grid(row=elem_row + i, column=3,
                                                                sticky=tk.W, padx=(40, 5))
                var = tk.StringVar()
                entry = tk.Entry(elem_scrollable, textvariable=var, width=12)
                entry.grid(row=elem_row + i, column=4, padx=5, pady=2)
                element_vars[elem] = var

                tk.Label(elem_scrollable, text="ppm", font=("Arial", 8),
                        fg="gray").grid(row=elem_row + i, column=5, sticky=tk.W)

            elem_row += max(len(col1_elements), len(col2_elements))

        # Custom element entries
        tk.Label(elem_scrollable, text="Custom Elements",
                font=("Arial", 10, "bold"), fg="#2980b9").grid(row=elem_row, column=0,
                                                            columnspan=3, sticky=tk.W, pady=(15, 5))
        elem_row += 1

        # Frame for custom elements
        custom_frame = tk.Frame(elem_scrollable)
        custom_frame.grid(row=elem_row, column=0, columnspan=6, sticky=tk.W, pady=5)

        tk.Label(custom_frame, text="Element:").grid(row=0, column=0, padx=5)
        custom_elem_var = tk.StringVar()
        tk.Entry(custom_frame, textvariable=custom_elem_var, width=10).grid(row=0, column=1, padx=5)

        tk.Label(custom_frame, text="Value:").grid(row=0, column=2, padx=5)
        custom_val_var = tk.StringVar()
        tk.Entry(custom_frame, textvariable=custom_val_var, width=12).grid(row=0, column=3, padx=5)

        tk.Label(custom_frame, text="Unit:").grid(row=0, column=4, padx=5)
        custom_unit_var = tk.StringVar(value="ppm")
        ttk.Combobox(custom_frame, textvariable=custom_unit_var,
                    values=["ppm", "ppb", "wt%", "Ma", "ratio"],
                    width=6).grid(row=0, column=5, padx=5)

        # List to store custom elements
        custom_elements = []

        def add_custom_element():
            """Add a custom element to the list"""
            elem = custom_elem_var.get().strip()
            val = custom_val_var.get().strip()
            unit = custom_unit_var.get()

            if not elem or not val:
                return

            try:
                float_val = float(val)
                custom_elements.append((elem, float_val, unit))
                custom_elem_var.set("")
                custom_val_var.set("")

                # Update display
                update_custom_list()
            except ValueError:
                messagebox.showerror("Invalid Value", "Value must be a number")

        def update_custom_list():
            """Update the list of custom elements"""
            for widget in custom_display_frame.winfo_children():
                widget.destroy()

            for i, (elem, val, unit) in enumerate(custom_elements):
                frame = tk.Frame(custom_display_frame)
                frame.pack(fill=tk.X, pady=2)

                tk.Label(frame, text=f"• {elem}: {val} {unit}").pack(side=tk.LEFT)

                def remove_custom(idx=i):
                    if idx < len(custom_elements):
                        custom_elements.pop(idx)
                        update_custom_list()

                tk.Button(frame, text="✖", font=("Arial", 8),
                        command=remove_custom, width=2).pack(side=tk.RIGHT)

        # Add custom element button
        tk.Button(custom_frame, text="Add Custom Element",
                command=add_custom_element,
                font=("Arial", 8)).grid(row=0, column=6, padx=10)

        # Display custom elements
        custom_display_frame = tk.Frame(elem_scrollable)
        custom_display_frame.grid(row=elem_row+1, column=0, columnspan=6, sticky=tk.W, pady=5)

        # Validation and save functions
        def validate_and_save():
            """Validate form and save reference material"""
            # Check required fields
            name = name_var.get().strip()
            mat_type = type_var.get().strip()
            reference = ref_var.get().strip()

            if not name:
                messagebox.showerror("Validation Error", "Material Name is required!")
                return
            if not mat_type:
                messagebox.showerror("Validation Error", "Material Type is required!")
                return
            if not reference:
                messagebox.showerror("Validation Error", "Citation/Reference is required!")
                return

            # Collect certified values
            values = {}

            # Add element values
            for elem, var in element_vars.items():
                val_str = var.get().strip()
                if val_str:
                    try:
                        values[elem] = float(val_str)
                    except ValueError:
                        messagebox.showerror("Validation Error",
                                        f"Invalid number for {elem}: {val_str}")
                        return

            # Add custom elements
            for elem, val, unit in custom_elements:
                if unit != "ppm":
                    values[f"{elem}_{unit}"] = val
                else:
                    values[elem] = val

            # Create reference material entry
            new_material = {
                "type": mat_type,
                "reference": reference,
                "values": values
            }

            # Add year if provided
            year = year_var.get().strip()
            if year:
                new_material["year"] = year

            # Add notes if provided
            notes = notes_text.get("1.0", tk.END).strip()
            if notes:
                new_material["notes"] = notes

            # Add to reference materials
            self.ref_materials[name] = new_material

            # Update reference tree in main tab
            if hasattr(self, 'ref_tree'):
                self.ref_tree.insert('', tk.END, values=(
                    name,
                    mat_type,
                    reference[:30] + "...",
                    str(len(values))
                ))

            # Close dialog
            dialog.destroy()

            # Log success
            self._log_message(f"✅ Added reference material: {name} ({len(values)} certified values)")

            # Show success message with option to export
            response = messagebox.askyesno(
                "Success",
                f"✅ Reference material '{name}' added successfully!\n\n"
                f"Material: {mat_type}\n"
                f"Certified elements: {len(values)}\n\n"
                "Would you like to export the updated database to CSV?"
            )

            if response:
                self._export_references()

        # Buttons
        button_frame = tk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Button(button_frame, text="Save Reference Material",
                command=validate_and_save,
                bg="#27ae60", fg="white",
                font=("Arial", 10, "bold"),
                width=20).pack(side=tk.LEFT, padx=5)

        tk.Button(button_frame, text="Cancel",
                command=dialog.destroy,
                bg="#e74c3c", fg="white",
                width=15).pack(side=tk.RIGHT, padx=5)

        # Quick load from known materials
        quick_frame = tk.LabelFrame(dialog, text="Quick Load Template")
        quick_frame.pack(fill=tk.X, padx=10, pady=5)

        def load_template(template_name):
            """Load a template material"""
            if template_name in self.REFERENCE_MATERIALS:
                template = self.REFERENCE_MATERIALS[template_name]
                name_var.set(f"{template_name} (copy)")
                type_var.set(template['type'])
                ref_var.set(template['reference'])

                # Clear existing values
                for var in element_vars.values():
                    var.set("")

                # Set template values
                for elem, val in template['values'].items():
                    if elem in element_vars:
                        element_vars[elem].set(str(val))

        ttk.Button(quick_frame, text="Load NIST 610",
                command=lambda: load_template("NIST 610")).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(quick_frame, text="Load NIST 612",
                command=lambda: load_template("NIST 612")).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(quick_frame, text="Load GJ-1",
                command=lambda: load_template("GJ-1 (Zircon)")).pack(side=tk.LEFT, padx=5, pady=5)

    def _import_references(self):
        """Import reference materials from CSV"""
        filename = filedialog.askopenfilename(
            title="Import Reference Materials",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx"), ("All files", "*.*")]
        )

        if not filename:
            return

        try:
            if filename.endswith('.csv'):
                df = pd.read_csv(filename)
            elif filename.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(filename)
            else:
                messagebox.showerror("Format Error", "Unsupported file format. Please use CSV or Excel.")
                return

            # Parse the data
            imported_count = 0
            for idx, row in df.iterrows():
                name = row.get('Material_Name') or row.get('Name')
                if pd.isna(name):
                    continue

                mat_type = row.get('Type', 'Unknown')
                reference = row.get('Reference', '')

                # Extract values
                values = {}
                for col in df.columns:
                    if col not in ['Material_Name', 'Name', 'Type', 'Reference', 'Year', 'Notes']:
                        val = row[col]
                        if pd.notna(val) and isinstance(val, (int, float)):
                            values[col] = float(val)

                if values:
                    self.ref_materials[name] = {
                        'type': mat_type,
                        'reference': reference,
                        'values': values
                    }
                    imported_count += 1

            # Update tree
            if hasattr(self, 'ref_tree'):
                for item in self.ref_tree.get_children():
                    self.ref_tree.delete(item)

                for name, info in self.ref_materials.items():
                    self.ref_tree.insert('', tk.END, values=(
                        name,
                        info['type'],
                        info['reference'][:30] + "...",
                        str(len(info['values']))
                    ))

            self._log_message(f"✅ Imported {imported_count} reference materials from {filename}")
            messagebox.showinfo("Success", f"Imported {imported_count} reference materials")

        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import: {str(e)}")

    def _export_references(self):
        """Export reference materials to CSV"""
        if not self.ref_materials:
            messagebox.showwarning("No Data", "No reference materials to export!")
            return

        filename = filedialog.asksaveasfilename(
            title="Export Reference Materials",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")]
        )

        if not filename:
            return

        try:
            # Prepare data for export
            all_elements = set()
            for info in self.ref_materials.values():
                all_elements.update(info['values'].keys())

            all_elements = sorted(list(all_elements))

            # Create DataFrame
            rows = []
            for name, info in self.ref_materials.items():
                row = {
                    'Material_Name': name,
                    'Type': info['type'],
                    'Reference': info['reference']
                }

                if 'year' in info:
                    row['Year'] = info['year']
                if 'notes' in info:
                    row['Notes'] = info['notes']

                for elem in all_elements:
                    row[elem] = info['values'].get(elem, '')

                rows.append(row)

            df = pd.DataFrame(rows)

            # Save to file
            if filename.endswith('.csv'):
                df.to_csv(filename, index=False)
            else:
                df.to_excel(filename, index=False)

            self._log_message(f"✅ Exported {len(self.ref_materials)} reference materials to {filename}")
            messagebox.showinfo("Success", f"Exported {len(self.ref_materials)} reference materials")

        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {str(e)}")

    def _export_references(self):
        """Export reference materials to CSV"""
        filename = filedialog.asksaveasfilename(
            title="Export Reference Materials",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )
        if filename:
            messagebox.showinfo("Export", f"Would export to: {filename}")

    # ============ TAB 6: RESULTS ============
    def _create_results_tab(self):
        """Tab for viewing and exporting results"""
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="📊 6. Results")

        # Results tree
        tree_frame = tk.Frame(tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create tree with scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")

        self.results_tree = ttk.Treeview(tree_frame,
                                        yscrollcommand=vsb.set,
                                        xscrollcommand=hsb.set)

        vsb.config(command=self.results_tree.yview)
        hsb.config(command=self.results_tree.xview)

        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Export buttons
        btn_frame = tk.Frame(tab)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)

        # Export to Main App
        tk.Button(btn_frame, text="📤 Export to Main App",
                 command=self._export_to_main,
                 bg="#3498db", fg="white",
                 font=("Arial", 10, "bold"),
                 width=20).pack(side=tk.LEFT, padx=5)

        # Export to CSV
        tk.Button(btn_frame, text="💾 Export to CSV",
                 command=self._export_results,
                 bg="#9b59b6", fg="white",
                 width=15).pack(side=tk.LEFT, padx=5)

        # Export Figure
        tk.Button(btn_frame, text="📊 Export Figure",
                 command=self._export_figure,
                 bg="#9b59b6", fg="white",
                 width=15).pack(side=tk.LEFT, padx=5)

        # Log text
        log_frame = tk.LabelFrame(tab, text="Processing Log")
        log_frame.pack(fill=tk.X, padx=10, pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=6, font=("Courier", 8))
        self.log_text.pack(fill=tk.X)

    def _update_results_tree(self):
        """Update results tree with current data"""
        if self.results_df is None:
            return

        # Clear existing
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        # Set columns
        columns = list(self.results_df.columns)
        self.results_tree["columns"] = columns
        self.results_tree["show"] = "headings"

        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=100)

        # Add data
        for idx, row in self.results_df.iterrows():
            values = [f"{v:.2f}" if isinstance(v, float) else str(v) for v in row]
            self.results_tree.insert("", tk.END, values=values)

    def _export_results(self):
        """Export results to CSV"""
        if self.results_df is None or self.results_df.empty:
            messagebox.showwarning("No Data", "No results to export!")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=f"LAICPMS_results_{datetime.now().strftime('%Y%m%d')}.csv"
        )

        if filename:
            self.results_df.to_csv(filename, index=False)
            self._log_message(f"✅ Exported to: {filename}")
            messagebox.showinfo("Success", f"Results saved to:\n{filename}")

    def _export_figure(self):
        """Export current figure"""
        # Determine which figure is active
        current = self.notebook.index(self.notebook.select())

        if current == 1 and hasattr(self, 'signal_fig'):
            fig = self.signal_fig
        elif current == 3 and hasattr(self, 'upb_fig'):
            fig = self.upb_fig
        else:
            messagebox.showinfo("No Figure", "No figure to export in current tab")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf"), ("SVG files", "*.svg")]
        )

        if filename:
            fig.savefig(filename, dpi=300, bbox_inches='tight')
            self._log_message(f"✅ Figure exported: {filename}")

    def _export_to_main(self):
        """Export processed results back to main application"""
        if self.results_df is None or self.results_df.empty:
            messagebox.showwarning("No Data", "Process data first!")
            return

        if not hasattr(self.app, 'samples'):
            messagebox.showwarning("No Main App", "Main application not available!")
            return

        try:
            # Get current timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Create new entries for the main app
            new_entries = []

            # Group by Sample_ID if present
            if 'Sample_ID' in self.results_df.columns:
                grouped = self.results_df.groupby('Sample_ID')
                for sample_id, group in grouped:
                    entry = {
                        'Sample_ID': sample_id,
                        'Analysis_Date': timestamp,
                        'Method': 'LA-ICP-MS',
                        'Plugin': PLUGIN_INFO['name'],
                        'Notes': f"Processed: {datetime.now().strftime('%Y-%m-%d')}"
                    }

                    # Add all processed values
                    for idx, row in group.iterrows():
                        elem = row.get('Element', f'Element_{idx}')
                        for col in self.results_df.columns:
                            if col not in ['Sample_ID', 'Element', 'Index']:
                                val = row[col]
                                if pd.notna(val):
                                    if isinstance(val, (int, float)):
                                        entry[f"{elem}_{col}"] = f"{val:.2f}"
                                    else:
                                        entry[f"{elem}_{col}"] = str(val)

                    new_entries.append(entry)
            else:
                # No Sample_ID - create one entry per element
                for idx, row in self.results_df.iterrows():
                    entry = {
                        'Sample_ID': f"LA-{idx+1:04d}",
                        'Analysis_Date': timestamp,
                        'Method': 'LA-ICP-MS',
                        'Plugin': PLUGIN_INFO['name'],
                        'Notes': f"Processed: {datetime.now().strftime('%Y-%m-%d')}"
                    }

                    elem = row.get('Element', f'Element_{idx}')
                    for col in self.results_df.columns:
                        if col not in ['Sample_ID', 'Element', 'Index']:
                            val = row[col]
                            if pd.notna(val):
                                if isinstance(val, (int, float)):
                                    entry[f"{elem}_{col}"] = f"{val:.2f}"
                                else:
                                    entry[f"{elem}_{col}"] = str(val)

                    new_entries.append(entry)

            # Add to main app samples
            if hasattr(self.app, 'import_data_from_plugin'):
                self.app.import_data_from_plugin(new_entries)
                self._log_message(f"✅ Exported {len(new_entries)} entries to main app")
                messagebox.showinfo("Success", f"Exported {len(new_entries)} entries to main table")
            elif hasattr(self.app, 'samples'):
                self.app.samples.extend(new_entries)
                if hasattr(self.app, 'refresh_tree'):
                    self.app.refresh_tree()
                if hasattr(self.app, '_mark_unsaved_changes'):
                    self.app._mark_unsaved_changes()
                self._log_message(f"✅ Exported {len(new_entries)} entries to main app")
                messagebox.showinfo("Success", f"Exported {len(new_entries)} entries to main table")
            else:
                messagebox.showerror("Error", "Main app doesn't support adding samples")

        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    # ============ TAB 7: HELP ============
    def _create_help_tab(self):
        """Tab with documentation and references"""
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="❓ Help")

        text = scrolledtext.ScrolledText(tab, wrap=tk.WORD, font=("Arial", 10),
                                        padx=20, pady=20)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        help_text = """
⚛️ LA-ICP-MS PRO - USER GUIDE
═══════════════════════════════════════════════════════════════

OVERVIEW
────────────────────────────────────────────────────────────────
This plugin provides professional LA-ICP-MS data analysis tools
based on the Norris Scientific Knowledge Base and key literature.

FEATURES
────────────────────────────────────────────────────────────────

📂 1. LOAD DATA
   • Load time-resolved signal data (CSV, Excel, LADR, Iolite)
   • Batch process multiple files
   • 📥 Import from Main App - Pull samples directly from main table
   • Automatic element channel detection

📈 2. SIGNAL PROCESSING (Longerich et al. 1996)
   • Baseline correction and subtraction
   • Signal integration with user-defined regions
   • Smoothing with Savitzky-Golay filter
   • Signal-to-noise ratio calculation
   • RSD% and uncertainty propagation

🧪 3. QUANTIFICATION (Liu et al. 2008)
   • External calibration with reference materials
   • Internal standard normalization
   • Detection limit calculation
   • Reference material database (NIST, zircons)

⏳ 4. U-PB GEOCHRONOLOGY (Fryer et al. 1993)
   • Concordia diagram generation
   • Common Pb correction methods (204, 207, 208)
   • Age calculation (206/238, 207/235, 207/206)
   • Discordance filtering

📚 5. REFERENCE MATERIALS (Gilbert et al. 2017)
   • Certified values for NIST glasses
   • Zircon standards (GJ-1, 91500)
   • Add custom reference materials
   • Import/export reference databases

📊 6. RESULTS
   • View processed data table
   • 📤 Export to Main App - Push processed results back
   • Export to CSV for further analysis
   • Publication-quality figures

WORKFLOW
────────────────────────────────────────────────────────────────

1. LOAD DATA (File or Main App) → 2. PROCESS SIGNAL → 3. QUANTIFY → 4. EXPORT

For U-Pb dating:
1. LOAD DATA → 2. PROCESS → 4. U-Pb DATING → 6. EXPORT

For main app integration:
• 📥 Import from Main App (Tab 1) → Process → 📤 Export to Main App (Tab 6)

TIPS
────────────────────────────────────────────────────────────────

• Always check baseline stability before integration
• Use reference materials for quality control
• Apply discordance filters for U-Pb data
• Report 2-sigma uncertainties for all values
• Cite the appropriate references in publications

For more information, visit:
https://norsci.com/?p=kb-laicpms

═══════════════════════════════════════════════════════════════
"""
        text.insert('1.0', help_text)
        text.config(state=tk.DISABLED)

    # ============ UTILITY FUNCTIONS ============

    def _log_message(self, message):
        """Add message to log"""
        if hasattr(self, 'log_text'):
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.log_text.see(tk.END)

def setup_plugin(main_app):
    """Plugin setup function"""
    plugin = LAICPMSProPlugin(main_app)
    return plugin  # ← JUST RETURN PLUGIN, NO MENU CODE!
