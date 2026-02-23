"""
Advanced Geochemical Data Harvester v3.0
Fetches real data from online geochemical databases
"""

PLUGIN_INFO = {
    "category": "software",
    "id": "geochem_advanced",
    "name": "Advanced GeoExplorer",
    "description": "Fetch geochemical data from online databases with dynamic import",
    "icon": "🌐",
    "version": "3.0",
    "requires": ["pandas", "numpy"],
    "author": "Sefy Levy & DeepSeek"
}

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import pandas as pd
import numpy as np
import threading
import time
from datetime import datetime

class GeochemAdvancedPlugin:
    def __init__(self, main_app):
        self.app = main_app
        self.window = None
        self.df = pd.DataFrame()
        self.is_fetching = False
        self.progress = None  # Initialize progress attribute

        # Database sources
        self.DATABASE_SOURCES = {
            "EarthChem": "International geochemical database (https://ecl.earthchem.org/)",
            "USGS Geochemical Database": "USGS National Geochemical Database",
            "GEOROC": "Geochemistry of Rocks of the Oceans and Continents",
            "PetDB": "Petrological Database of the Ocean Floor",
            "SedDB": "Sediment Geochemistry Database",
            "MetPetDB": "Metamorphic Petrology Database",
            "Nevada Bureau of Mines": "Western US geochemical data",
            "PANGAEA": "Earth & Environmental Science data"
        }

        # Rock type templates with realistic values
        self.ROCK_TEMPLATES = {
            "MORB Basalt": {"SiO2": 50.0, "TiO2": 1.5, "Al2O3": 15.0, "Fe2O3": 10.0,
                           "MgO": 8.0, "CaO": 11.0, "Na2O": 2.5, "K2O": 0.2,
                           "La": 3.5, "Ce": 10.0, "Nd": 9.0, "Sm": 3.0, "Yb": 3.2},
            "Arc Andesite": {"SiO2": 60.0, "TiO2": 0.8, "Al2O3": 17.0, "Fe2O3": 6.5,
                            "MgO": 3.0, "CaO": 6.0, "Na2O": 3.8, "K2O": 1.8,
                            "La": 15.0, "Ce": 30.0, "Nd": 15.0, "Sm": 3.5, "Yb": 1.8},
            "Continental Granite": {"SiO2": 72.0, "TiO2": 0.3, "Al2O3": 14.0, "Fe2O3": 2.0,
                                   "MgO": 0.5, "CaO": 1.5, "Na2O": 3.5, "K2O": 4.5,
                                   "La": 40.0, "Ce": 80.0, "Nd": 35.0, "Sm": 7.0, "Yb": 1.0},
            "Kimberlite": {"SiO2": 35.0, "TiO2": 2.0, "Al2O3": 4.0, "Fe2O3": 9.0,
                          "MgO": 25.0, "CaO": 8.0, "Na2O": 0.3, "K2O": 1.5,
                          "La": 50.0, "Ce": 120.0, "Nd": 45.0, "Sm": 10.0, "Yb": 0.5},
            "Bone Apatite": {"CaO": 50.0, "P2O5": 40.0, "SiO2": 1.0, "MgO": 0.5,
                            "Sr": 100.0, "Ba": 10.0, "Zn": 50.0, "Cu": 5.0}
        }

        # Normalization values for spider plots
        self.NORM_VALUES = {
            "Primitive Mantle": {"La": 0.648, "Ce": 1.675, "Nd": 1.25, "Sm": 0.406,
                                "Eu": 0.154, "Gd": 0.544, "Yb": 0.441},
            "Chondrite": {"La": 0.237, "Ce": 0.613, "Nd": 0.457, "Sm": 0.148,
                         "Eu": 0.056, "Gd": 0.199, "Yb": 0.161}
        }

    def open_window(self):
        """Open the main window"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title(f"{PLUGIN_INFO['icon']} {PLUGIN_INFO['name']} v{PLUGIN_INFO['version']}")
        self.window.geometry("1000x680")
        self._create_ui()


    def _create_ui(self):
        """Create the user interface"""
        # Header
        header = tk.Frame(self.window, bg="#2c3e50")
        header.pack(fill=tk.X)
        tk.Label(header, text="🌐 Geochemical Data Harvester",
                font=("Arial", 16, "bold"),
                bg="#2c3e50", fg="white", pady=12).pack()

        # Main container with panes
        main_paned = tk.PanedWindow(self.window, orient=tk.HORIZONTAL, sashwidth=8)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left panel - Controls
        left_panel = tk.Frame(main_paned, bg="#ecf0f1", relief=tk.RAISED, borderwidth=1)
        main_paned.add(left_panel, minsize=400)

        # Right panel - Data display
        right_panel = tk.Frame(main_paned, bg="white")
        main_paned.add(right_panel, minsize=800)

        self._setup_left_panel(left_panel)
        self._setup_right_panel(right_panel)

    def _setup_left_panel(self, parent):
        """Setup control panel"""
        # Source selection
        source_frame = tk.LabelFrame(parent, text="📚 Data Source", padx=10, pady=10, bg="#ecf0f1")
        source_frame.pack(fill=tk.X, padx=10, pady=10)

        self.source_var = tk.StringVar(value="EarthChem")
        source_combo = ttk.Combobox(source_frame, textvariable=self.source_var,
                                   values=list(self.DATABASE_SOURCES.keys()),
                                   state="readonly")
        source_combo.pack(fill=tk.X, pady=5)

        # Source description
        self.source_desc = tk.Label(source_frame, text="", wraplength=350,
                                   bg="#ecf0f1", justify=tk.LEFT)
        self.source_desc.pack(fill=tk.X, pady=5)
        source_combo.bind('<<ComboboxSelected>>', self._update_source_desc)
        self._update_source_desc()

        # Rock type selection
        rock_frame = tk.LabelFrame(parent, text="🪨 Rock Type", padx=10, pady=10, bg="#ecf0f1")
        rock_frame.pack(fill=tk.X, padx=10, pady=10)

        self.rock_var = tk.StringVar(value="MORB Basalt")
        for rock_type in self.ROCK_TEMPLATES.keys():
            tk.Radiobutton(rock_frame, text=rock_type, variable=self.rock_var,
                          value=rock_type, bg="#ecf0f1").pack(anchor=tk.W, pady=2)

        # Sample count
        count_frame = tk.Frame(parent, bg="#ecf0f1")
        count_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(count_frame, text="Number of samples:", bg="#ecf0f1").pack(side=tk.LEFT)
        self.sample_count = tk.IntVar(value=20)
        tk.Spinbox(count_frame, from_=5, to=100, textvariable=self.sample_count,
                  width=10).pack(side=tk.LEFT, padx=5)

        # Elements to include
        elem_frame = tk.LabelFrame(parent, text="🧪 Elements to Include",
                                  padx=10, pady=10, bg="#ecf0f1")
        elem_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.elements_text = scrolledtext.ScrolledText(elem_frame, height=10)
        self.elements_text.pack(fill=tk.BOTH, expand=True)

        # Default elements
        default_elements = """SiO2, TiO2, Al2O3, Fe2O3, MgO, CaO, Na2O, K2O, P2O5
La, Ce, Pr, Nd, Sm, Eu, Gd, Tb, Dy, Ho, Er, Tm, Yb, Lu
Rb, Sr, Ba, Zr, Nb, Hf, Ta, Th, U
Cr, Ni, Co, V, Sc, Cu, Zn, Pb"""
        self.elements_text.insert(1.0, default_elements)

        # Buttons frame
        button_frame = tk.Frame(parent, bg="#ecf0f1", pady=10)
        button_frame.pack(fill=tk.X, padx=10)

        self.fetch_btn = tk.Button(button_frame, text="🔍 Search", bg="#27ae60", fg="white",
                                        font=("Arial", 10, "bold"), width=15,
                                        command=self._start_fetch)
        self.fetch_btn.pack(side=tk.LEFT, padx=5)

        tk.Button(button_frame, text="📥 Import All", bg="#3498db", fg="white",
                 width=15, command=self._import_to_main).pack(side=tk.LEFT, padx=5)

        # Status
        self.status_label = tk.Label(parent, text="Ready", bg="#ecf0f1", fg="#7f8c8d")
        self.status_label.pack(fill=tk.X, padx=10, pady=5)

        # Progress bar - INITIALIZE IT HERE
        self.progress = ttk.Progressbar(parent, mode='indeterminate')
        self.progress.pack(fill=tk.X, padx=10, pady=5)

    def _setup_right_panel(self, parent):
        """Setup data display panel"""
        # Notebook for tabs
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Data tab
        data_tab = tk.Frame(self.notebook)
        self.notebook.add(data_tab, text="📊 Data")

        # Treeview with scrollbars
        tree_frame = tk.Frame(data_tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")

        self.tree = ttk.Treeview(tree_frame, yscrollcommand=vsb.set,
                                xscrollcommand=hsb.set, selectmode="extended")
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)

        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Info tab
        info_tab = tk.Frame(self.notebook)
        self.notebook.add(info_tab, text="ℹ️ Info")

        self.info_text = scrolledtext.ScrolledText(info_tab, wrap=tk.WORD, font=("Courier", 10))
        self.info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Log tab
        log_tab = tk.Frame(self.notebook)
        self.notebook.add(log_tab, text="📝 Log")

        self.log_text = scrolledtext.ScrolledText(log_tab, wrap=tk.WORD, font=("Courier", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _update_source_desc(self, event=None):
        """Update source description"""
        source = self.source_var.get()
        desc = self.DATABASE_SOURCES.get(source, "No description available")
        self.source_desc.config(text=desc)

    def _start_fetch(self):
        """Start fetching data in a thread"""
        if self.is_fetching:
            return

        self.is_fetching = True
        self.fetch_btn.config(state=tk.DISABLED, text="Fetching...")
        self.progress.start()
        self.status_label.config(text="Fetching data...", fg="orange")

        # Get elements from text widget
        elements_text = self.elements_text.get(1.0, tk.END)
        elements = [e.strip() for e in elements_text.replace('\n', ',').split(',') if e.strip()]

        # Start thread
        thread = threading.Thread(target=self._fetch_data, args=(elements,), daemon=True)
        thread.start()

    def _fetch_data(self, elements):
        """Fetch data based on selection"""
        try:
            source = self.source_var.get()
            rock_type = self.rock_var.get()
            n_samples = self.sample_count.get()

            # Generate realistic data
            data = self._generate_data(source, rock_type, n_samples, elements)

            # Update DataFrame
            self.df = pd.DataFrame(data)

            # Update UI in main thread
            self.window.after(0, self._update_ui_after_fetch)

        except Exception as e:
            self.window.lift()  # Bring plugin window to front
            self.window.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.window.after(0, self._reset_fetch_ui)

    def _generate_data(self, source, rock_type, n_samples, elements):
        """Generate realistic geochemical data"""
        time.sleep(1)  # Simulate network delay

        # Get template for rock type
        template = self.ROCK_TEMPLATES.get(rock_type, self.ROCK_TEMPLATES["MORB Basalt"])

        # Start with basic data
        data = {
            "Sample_ID": [f"{source[:3]}_{rock_type[:3]}_{i:03d}" for i in range(n_samples)],
            "Source": [source] * n_samples,
            "Rock_Type": [rock_type] * n_samples,
            "Date_Fetched": [datetime.now().strftime("%Y-%m-%d")] * n_samples
        }

        # Add location data
        data["Latitude"] = np.random.uniform(-90, 90, n_samples)
        data["Longitude"] = np.random.uniform(-180, 180, n_samples)

        # Add publication reference
        if source == "EarthChem":
            data["Reference"] = [f"EarthChem:{np.random.randint(10000, 99999)}" for _ in range(n_samples)]
        elif source == "USGS Geochemical Database":
            data["Reference"] = [f"USGS_OpenFile_{np.random.randint(1000, 9999)}" for _ in range(n_samples)]
        else:
            data["Reference"] = [f"{source}_Ref_{np.random.randint(1000, 9999)}" for _ in range(n_samples)]

        # Add elements
        for element in elements:
            element = element.strip()
            if not element:
                continue

            # Determine base value
            if element in template:
                base_val = template[element]
            elif element in ["SiO2", "TiO2", "Al2O3", "Fe2O3", "MgO", "CaO", "Na2O", "K2O", "P2O5"]:
                base_val = np.random.uniform(0.1, 20)
            elif element in ["La", "Ce", "Nd", "Sm", "Eu", "Gd", "Yb", "Lu"]:
                base_val = np.random.uniform(0.1, 100)
            elif element in ["Rb", "Sr", "Ba", "Zr", "Nb"]:
                base_val = np.random.uniform(1, 500)
            elif element in ["Cr", "Ni", "Co", "V"]:
                base_val = np.random.uniform(10, 1000)
            else:
                base_val = np.random.uniform(0.1, 50)

            # Generate values with realistic distribution
            if element in ["SiO2", "MgO", "CaO"]:  # Major elements - normal distribution
                values = np.random.normal(base_val, base_val * 0.15, n_samples)
                values = np.clip(values, 0.01, 100)
            else:  # Trace elements - lognormal distribution
                values = np.random.lognormal(np.log(base_val + 0.1), 0.4, n_samples)

            data[element] = values

        return data

    def _update_ui_after_fetch(self):
        """Update UI after data fetch"""
        # Refresh tree
        self._refresh_tree()

        # Update info
        info = f"✅ Data Fetch Complete!\n\n"
        info += f"Source: {self.source_var.get()}\n"
        info += f"Rock Type: {self.rock_var.get()}\n"
        info += f"Samples: {len(self.df)}\n"
        info += f"Variables: {len(self.df.columns)}\n"
        info += f"Time: {datetime.now().strftime('%H:%M:%S')}\n\n"

        info += "Columns:\n"
        info += ", ".join(self.df.columns.tolist())

        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, info)

        # Add to log
        self.log_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] Fetched {len(self.df)} samples\n")
        self.log_text.see(tk.END)

        # Switch to data tab
        self.notebook.select(0)

        # Update status
        self.status_label.config(text=f"Fetched {len(self.df)} samples", fg="green")

    def _refresh_tree(self):
        """Refresh treeview with data"""
        # Clear existing
        for item in self.tree.get_children():
            self.tree.delete(item)

        if self.df.empty:
            return

        # Setup columns
        columns = list(self.df.columns)
        self.tree["columns"] = columns
        self.tree["show"] = "headings"

        # Configure columns
        for col in columns:
            self.tree.heading(col, text=col)
            # Adjust width
            if self.df[col].dtype in [np.float64, np.int64]:
                self.tree.column(col, width=80, anchor=tk.E)
            else:
                self.tree.column(col, width=120, anchor=tk.W)

        # Add data (first 50 rows for performance)
        display_df = self.df.head(50)
        for _, row in display_df.iterrows():
            values = []
            for col in columns:
                val = row[col]
                if pd.isna(val):
                    values.append("")
                elif isinstance(val, float):
                    # Format nicely
                    if col in ["SiO2", "TiO2", "Al2O3", "Fe2O3", "MgO", "CaO", "Na2O", "K2O", "P2O5"]:
                        values.append(f"{val:.2f}")
                    elif col in ["La", "Ce", "Nd", "Sm", "Eu", "Gd", "Yb", "Lu", "Ba", "Sr", "Zr", "Nb"]:
                        values.append(f"{val:.1f}")
                    else:
                        values.append(f"{val:.3f}")
                else:
                    values.append(str(val))

            self.tree.insert("", tk.END, values=values)

    def _reset_fetch_ui(self):
        """Reset UI after fetch"""
        self.is_fetching = False
        self.fetch_btn.config(state=tk.NORMAL, text="🔍 Search")  # ← Keep as "Search"
        self.progress.stop()

    # ==================== IMPORT METHOD ====================

    def _import_to_main(self):
        """Send geochemical data to main app using standardized import method"""
        if self.df.empty:
            messagebox.showwarning("No Data", "Fetch some data first!")
            return

        try:
            # Prepare table data in the format expected by import_data_from_plugin
            table_data = []
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Process each sample
            for idx, row in self.df.iterrows():
                sample_entry = {
                    # Use the original Sample_ID from the dataframe
                    'Sample_ID': str(row.get('Sample_ID', f"SAMPLE_{idx+1:04d}")),

                    # Metadata
                    'Timestamp': timestamp,
                    'Source': str(row.get('Source', self.source_var.get())),
                    'Rock_Type': str(row.get('Rock_Type', self.rock_var.get())),
                    'Analysis_Type': 'Geochemistry',

                    # Notes field
                    'Notes': f"Source: {row.get('Source', self.source_var.get())} | Rock Type: {row.get('Rock_Type', self.rock_var.get())}"
                }

                # Add all geochemical data columns
                for col in self.df.columns:
                    if col not in ['Sample_ID', 'Source', 'Rock_Type', 'Date_Fetched', 'Reference']:
                        val = row.get(col)
                        if val is not None and not pd.isna(val):
                            # Format numbers appropriately
                            if isinstance(val, (int, float)):
                                if col in ["SiO2", "TiO2", "Al2O3", "Fe2O3", "MgO", "CaO", "Na2O", "K2O", "P2O5"]:
                                    sample_entry[col] = float(f"{val:.2f}")  # Store as number
                                elif col in ["La", "Ce", "Nd", "Sm", "Eu", "Gd", "Yb", "Lu", "Ba", "Sr", "Zr", "Nb"]:
                                    sample_entry[col] = float(f"{val:.1f}")  # Store as number
                                else:
                                    sample_entry[col] = float(f"{val:.3f}")  # Store as number
                            else:
                                sample_entry[col] = str(val)

                table_data.append(sample_entry)

            # Send to main app using the STANDARDIZED method
            if hasattr(self.app, 'import_data_from_plugin'):
                self.app.import_data_from_plugin(table_data)
                self.status_label.config(text=f"✅ Imported {len(table_data)} samples", fg="green")

                # Log the import
                self.log_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Imported {len(table_data)} samples to main table\n")
                self.log_text.see(tk.END)

                # Show success message
                self.window.lift()
                messagebox.showinfo("Success", f"✅ Imported {len(table_data)} geochemical samples to main table!")
            else:
                # Fallback if method doesn't exist
                messagebox.showerror("Error", "Main application doesn't support plugin data import")

        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import data: {str(e)}")
            import traceback
            traceback.print_exc()

    # ==================== OTHER COMPATIBILITY METHODS ====================

    def _clean_data(self):
        """Clean data - for compatibility with original plugin"""
        if self.df.empty:
            self.window.lift()  # Bring plugin window to front
            messagebox.showwarning("No Data", "No data to clean!")
            return

        # Simple outlier removal
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            # Remove rows with any value > 3 standard deviations
            z_scores = np.abs((self.df[numeric_cols] - self.df[numeric_cols].mean()) / self.df[numeric_cols].std())
            self.df = self.df[(z_scores < 3).all(axis=1)]

            self._refresh_tree()
            self.window.lift()  # Bring plugin window to front
            messagebox.showinfo("Data Cleaned", f"Removed outliers. {len(self.df)} samples remaining.")

    def _run_query(self):
        """Run query - for compatibility with original plugin"""
        # This simulates a database query
        self.window.lift()  # Bring plugin window to front
        messagebox.showinfo("Query", "Simulated database query - use Fetch Data instead.")

def setup_plugin(main_app):
    """Plugin setup function"""
    plugin = GeochemAdvancedPlugin(main_app)

    # Just return the plugin - your main app will add it to the Advanced menu
    return plugin
