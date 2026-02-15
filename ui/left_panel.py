"""
Left Panel - 10% width, Data Input
Manual Entry takes fixed height, Hardware at bottom
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import re

class LeftPanel:
    # Canonical column name mapping - handles common variations
    COLUMN_MAPPINGS = {
        # Core identification columns
        'sample_id': 'Sample_ID',
        'sample id': 'Sample_ID',
        'sampleid': 'Sample_ID',
        'id': 'Sample_ID',
        
        'museum_code': 'Museum_Code',
        'museum code': 'Museum_Code',
        'museumcode': 'Museum_Code',
        
        'notes': 'Notes',
        'note': 'Notes',
        'comments': 'Notes',
        'remarks': 'Notes',
        
        'date': 'Date',
        
        # Trace elements (ppm)
        'zr_ppm': 'Zr_ppm',
        'zr ppm': 'Zr_ppm',
        'zr': 'Zr_ppm',
        'zirconium': 'Zr_ppm',
        
        'zr_error': 'Zr_error',
        'zr error': 'Zr_error',
        
        'nb_ppm': 'Nb_ppm',
        'nb ppm': 'Nb_ppm',
        'nb': 'Nb_ppm',
        'niobium': 'Nb_ppm',
        
        'ba_ppm': 'Ba_ppm',
        'ba ppm': 'Ba_ppm',
        'ba': 'Ba_ppm',
        'barium': 'Ba_ppm',
        
        'rb_ppm': 'Rb_ppm',
        'rb ppm': 'Rb_ppm',
        'rb': 'Rb_ppm',
        'rubidium': 'Rb_ppm',
        
        'sr_ppm': 'Sr_ppm',
        'sr ppm': 'Sr_ppm',
        'sr': 'Sr_ppm',
        'strontium': 'Sr_ppm',
        
        'y_ppm': 'Y_ppm',
        'y ppm': 'Y_ppm',
        'y': 'Y_ppm',
        'yttrium': 'Y_ppm',
        
        'cr_ppm': 'Cr_ppm',
        'cr ppm': 'Cr_ppm',
        'cr': 'Cr_ppm',
        'chromium': 'Cr_ppm',
        
        'ni_ppm': 'Ni_ppm',
        'ni ppm': 'Ni_ppm',
        'ni': 'Ni_ppm',
        'nickel': 'Ni_ppm',
        
        'cu_ppm': 'Cu_ppm',
        'cu ppm': 'Cu_ppm',
        'cu': 'Cu_ppm',
        'copper': 'Cu_ppm',
        
        'pb_ppm': 'Pb_ppm',
        'pb ppm': 'Pb_ppm',
        'pb': 'Pb_ppm',
        'lead': 'Pb_ppm',
        
        'th_ppm': 'Th_ppm',
        'th ppm': 'Th_ppm',
        'th': 'Th_ppm',
        'thorium': 'Th_ppm',
        
        'yb_ppm': 'Yb_ppm',
        'yb ppm': 'Yb_ppm',
        'yb': 'Yb_ppm',
        'ytterbium': 'Yb_ppm',
        
        'fe_ppm': 'Fe_ppm',
        'fe ppm': 'Fe_ppm',
        'iron_ppm': 'Fe_ppm',
        
        'mn_ppm': 'Mn_ppm',
        'mn ppm': 'Mn_ppm',
        'manganese_ppm': 'Mn_ppm',
        
        'ti_ppm': 'Ti_ppm',
        'ti ppm': 'Ti_ppm',
        'titanium_ppm': 'Ti_ppm',
        
        'v_ppm': 'V_ppm',
        'v ppm': 'V_ppm',
        'vanadium_ppm': 'V_ppm',
        
        # Weight percent oxides
        'sio2_wt': 'SiO2_wt',
        'sio2 wt': 'SiO2_wt',
        'sio2': 'SiO2_wt',
        
        'tio2_wt': 'TiO2_wt',
        'tio2 wt': 'TiO2_wt',
        'tio2': 'TiO2_wt',
        
        'al2o3_wt': 'Al2O3_wt',
        'al2o3 wt': 'Al2O3_wt',
        'al2o3': 'Al2O3_wt',
        
        'fe2o3_t_wt': 'Fe2O3_T_wt',
        'fe2o3_wt': 'Fe2O3_T_wt',
        'fe2o3 wt': 'Fe2O3_T_wt',
        
        'mgo_wt': 'MgO_wt',
        'mgo wt': 'MgO_wt',
        'mgo': 'MgO_wt',
        
        'cao_wt': 'CaO_wt',
        'cao wt': 'CaO_wt',
        'cao': 'CaO_wt',
        
        'na2o_wt': 'Na2O_wt',
        'na2o wt': 'Na2O_wt',
        'na2o': 'Na2O_wt',
        
        'k2o_wt': 'K2O_wt',
        'k2o wt': 'K2O_wt',
        'k2o': 'K2O_wt',
        
        # Percent values
        'ti_pct': 'Ti_pct',
        'ti pct': 'Ti_pct',
        'ti%': 'Ti_pct',
        'ti percent': 'Ti_pct',
        
        'c_pct': 'C_pct',
        'c pct': 'C_pct',
        'c%': 'C_pct',
        'c percent': 'C_pct',
        'carbon_pct': 'C_pct',
        
        'cao_pct': 'CaO_pct',
        'cao pct': 'CaO_pct',
        
        'mgo_pct': 'MgO_pct',
        'mgo pct': 'MgO_pct',
        
        'sio2_pct': 'SiO2_pct',
        'sio2 pct': 'SiO2_pct',
        
        'al2o3_pct': 'Al2O3_pct',
        'al2o3 pct': 'Al2O3_pct',
        
        # Other measurements
        'wall_thickness_mm': 'Wall_Thickness_mm',
        'wall thickness mm': 'Wall_Thickness_mm',
        'wall_thickness': 'Wall_Thickness_mm',
        'wall thickness': 'Wall_Thickness_mm',
        'thickness_mm': 'Wall_Thickness_mm',
        'thickness': 'Wall_Thickness_mm',
        
        'latitude': 'Latitude',
        'lat': 'Latitude',
        
        'longitude': 'Longitude',
        'lon': 'Longitude',
        'long': 'Longitude',
        
        # Ratios and calculated values
        'ti_v_ratio': 'Ti_V_Ratio',
        'ti/v': 'Ti_V_Ratio',
        
        'zr_nb_ratio': 'Zr_Nb_Ratio',
        'zr/nb': 'Zr_Nb_Ratio',
        
        'cr_ni_ratio': 'Cr_Ni_Ratio',
        'cr/ni': 'Cr_Ni_Ratio',
        
        'th_yb_ratio': 'Th_Yb_Ratio',
        'th/yb': 'Th_Yb_Ratio',
        
        'nb_yb_ratio': 'Nb_Yb_Ratio',
        'nb/yb': 'Nb_Yb_Ratio',
        
        'fe_mn_ratio': 'Fe_Mn_Ratio',
        'fe/mn': 'Fe_Mn_Ratio',
        
        'v_ratio': 'V_Ratio',
        
        'zr_rsd': 'Zr_RSD',
        'zr rsd': 'Zr_RSD',
        
        'cia_value': 'CIA_Value',
        'cia': 'CIA_Value',
        
        'pb_ef': 'Pb_EF',
        'pb ef': 'Pb_EF',
    }
    
    @staticmethod
    def normalize_column_name(name):
        """
        Normalize column names to match canonical forms.
        
        Strategy:
        1. Strip whitespace
        2. Convert to lowercase for lookup
        3. Match against known column mappings
        4. If no match, preserve original with minimal cleanup
        
        Examples:
            'Sample ID' -> 'Sample_ID'
            'Zr ppm' -> 'Zr_ppm'
            'sample_id' -> 'Sample_ID'
            'ZR_PPM' -> 'Zr_ppm'
            'Unknown_Column' -> 'Unknown_Column' (preserved)
        """
        if not name:
            return name
        
        # Strip whitespace from ends
        cleaned = str(name).strip()
        
        # Create lookup key (lowercase, normalized spacing)
        lookup_key = cleaned.lower()
        lookup_key = re.sub(r'\s+', ' ', lookup_key)  # Normalize multiple spaces
        lookup_key = lookup_key.replace(' ', '_')  # Convert spaces to underscores for lookup
        
        # Try direct mapping first
        if lookup_key in LeftPanel.COLUMN_MAPPINGS:
            return LeftPanel.COLUMN_MAPPINGS[lookup_key]
        
        # Try without underscores (for "sample id" vs "sample_id")
        lookup_key_nospace = lookup_key.replace('_', ' ')
        if lookup_key_nospace in LeftPanel.COLUMN_MAPPINGS:
            return LeftPanel.COLUMN_MAPPINGS[lookup_key_nospace]
        
        # If no mapping found, preserve original but clean it up minimally
        # Just replace multiple spaces with single underscore
        result = re.sub(r'\s+', '_', cleaned)
        
        return result
    def __init__(self, parent, app):
        self.app = app
        self.frame = ttk.Frame(parent, relief=tk.RAISED, borderwidth=1)

        # Entry variables
        self.sample_id_var = tk.StringVar()
        self.notes_var = tk.StringVar()

        # Hardware buttons container
        self.hw_container = None
        self.hw_buttons = []

        # Track panel height for dynamic sizing
        self.frame.bind("<Configure>", self._on_frame_resize)

        self._build_ui()

    def _build_ui(self):
        """Build left panel UI with proper spacing"""

        # ============ 1. IMPORT DATA (Single Button - fixed at top) ============
        self.import_btn = ttk.Button(self.frame, text="📂 Import Data",
                                     command=self._import_file_dialog)
        self.import_btn.pack(fill=tk.X, padx=2, pady=2, side=tk.TOP)

        # ============ 2. MANUAL ENTRY (will be dynamically sized) ============
        self.entry_frame = ttk.LabelFrame(self.frame, text="📝 Manual Entry", padding=3)
        self.entry_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2, side=tk.TOP)

        # Sample ID
        ttk.Label(self.entry_frame, text="Sample ID:", font=("TkDefaultFont", 8)).grid(
            row=0, column=0, sticky="w", pady=1)
        self.sample_id_entry = ttk.Entry(self.entry_frame, textvariable=self.sample_id_var, width=15)
        self.sample_id_entry.grid(row=0, column=1, pady=1, padx=2, sticky="ew")
        self.sample_id_entry.bind("<Return>", lambda e: self.notes_entry.focus())

        # Notes
        ttk.Label(self.entry_frame, text="Notes:", font=("TkDefaultFont", 8)).grid(
            row=1, column=0, sticky="w", pady=1)
        self.notes_entry = ttk.Entry(self.entry_frame, textvariable=self.notes_var, width=15)
        self.notes_entry.grid(row=1, column=1, pady=1, padx=2, sticky="ew")
        self.notes_entry.bind("<Return>", lambda e: self._add_row())

        # Add Row button
        self.add_btn = ttk.Button(self.entry_frame, text="➕ Add Row", command=self._add_row)
        self.add_btn.grid(row=2, column=0, columnspan=2, pady=3, sticky="ew")

        # Spacer to push content to top of entry frame
        self.entry_frame.grid_rowconfigure(3, weight=1)

        self.entry_frame.columnconfigure(1, weight=1)

        # ============ 3. HARDWARE PLUGINS (fixed at bottom) ============
        hw_label = ttk.Label(self.frame, text="🔌 Hardware", font=("TkDefaultFont", 8, "bold"))
        hw_label.pack(anchor=tk.W, padx=2, pady=(5,0), side=tk.BOTTOM)

        # Container with fixed height for exactly 5 buttons (150px = 5 * 30px)
        self.hw_container = ttk.Frame(self.frame, height=190, relief=tk.SUNKEN, borderwidth=1)
        self.hw_container.pack(fill=tk.X, padx=2, pady=2, side=tk.BOTTOM, expand=False)
        self.hw_container.pack_propagate(False)  # Fixed height

        # Scrollable frame inside container (in case more than 5 plugins)
        self.hw_canvas = tk.Canvas(self.hw_container, highlightthickness=0, height=150)
        self.hw_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(self.hw_container, orient="vertical", command=self.hw_canvas.yview)
        self.hw_scrollable = ttk.Frame(self.hw_canvas)

        self.hw_scrollable.bind("<Configure>", lambda e: self.hw_canvas.configure(
            scrollregion=self.hw_canvas.bbox("all")))

        self.hw_canvas.create_window((0, 0), window=self.hw_scrollable, anchor="nw")

        # Update canvas width when container resizes
        def _configure_canvas(event):
            # Update the width of the canvas window to match canvas width
            self.hw_canvas.itemconfig(1, width=event.width)

        self.hw_canvas.bind("<Configure>", _configure_canvas)
        self.hw_canvas.configure(yscrollcommand=scrollbar.set)
        self.hw_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Placeholder (will be removed when first plugin is added)
        self._placeholder = ttk.Label(self.hw_scrollable, text="No hardware plugins installed",
                                     font=("TkDefaultFont", 7), foreground="gray")
        self._placeholder.pack(fill=tk.X, pady=10)

    def _on_frame_resize(self, event):
        """Handle frame resize to adjust Manual Entry height"""
        if event.widget != self.frame:
            return

        total_height = event.height

        # Calculate heights:
        # - Import button: ~30px
        # - Hardware label: ~20px
        # - Hardware container: 150px
        # - Padding: ~20px
        fixed_height = 30 + 20 + 150 + 20

        # Manual Entry gets the rest
        manual_height = max(100, total_height - fixed_height)

        # Set minimum height for entry frame
        self.entry_frame.configure(height=manual_height)

    def _import_file_dialog(self):
        """Open file dialog directly (no submenu)"""
        filetypes = [
            ("All supported files", "*.csv *.xlsx *.xls"),
            ("CSV files", "*.csv"),
            ("Excel files", "*.xlsx *.xls"),
            ("All files", "*.*")
        ]

        path = filedialog.askopenfilename(
            title="Import Data File",
            filetypes=filetypes
        )

        if not path:
            return

        # Just call import_csv - it handles both CSV and Excel
        self.import_csv(path)

    def import_csv(self, path=None):
        """Import CSV or Excel file with column name normalization"""
        if path is None:
            path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx *.xls")])
            if not path:
                return

        try:
            if path.lower().endswith('.csv'):
                import csv
                rows = []
                with open(path, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    if reader.fieldnames:
                        for row in reader:
                            clean_row = {}
                            for k, v in row.items():
                                if k and k.strip():
                                    # Normalize the column name to canonical form
                                    normalized_key = self.normalize_column_name(k)
                                    clean_row[normalized_key] = v.strip() if v else ''
                            if clean_row:
                                rows.append(clean_row)
            else:
                # Try to import Excel
                try:
                    import pandas as pd
                    df = pd.read_excel(path)
                    # Normalize column names
                    df.columns = [self.normalize_column_name(col) for col in df.columns]
                    rows = df.to_dict(orient='records')
                except ImportError:
                    messagebox.showerror("Error", "Excel import requires pandas. Install with: pip install pandas openpyxl")
                    return

            if rows:
                self.app.data_hub.add_samples(rows)
                messagebox.showinfo("Success", f"Imported {len(rows)} rows from {path}")
            else:
                messagebox.showwarning("Warning", "No data found in file")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to import: {e}")

    def _add_row(self):
        """Add manual row - preserves column order"""
        sample_id = self.sample_id_var.get().strip()
        notes = self.notes_var.get().strip()

        if not sample_id:
            messagebox.showerror("Error", "Sample ID is required")
            self.sample_id_entry.focus()
            return

        row = {
            'Sample_ID': sample_id,
            'Notes': notes
        }

        self.app.data_hub.add_samples([row])

        self.sample_id_var.set("")
        self.notes_var.set("")
        self.sample_id_entry.focus()

    def add_hardware_button(self, name, icon, command):
        """Add hardware plugin button (called by plugin manager) - with duplicate prevention"""
        # Check if this button already exists
        button_text = f"{icon} {name}"
        for btn in self.hw_buttons:
            if hasattr(btn, 'cget') and btn.cget('text') == button_text:
                print(f"⏭️ Button '{button_text}' already exists, skipping...")
                return

        if hasattr(self, '_placeholder') and self._placeholder.winfo_exists():
            self._placeholder.destroy()
            delattr(self, '_placeholder')

        # CHANGE: Use tk.Button instead of ttk.Button for better style control
        btn = tk.Button(self.hw_scrollable,
                    text=button_text,
                    command=command,
                    anchor='w',  # ← Left-align text
                    justify='left',  # ← Left justify
                    relief=tk.RAISED,
                    bd=1,
                    padx=4)  # ← Add a little padding
        btn.pack(fill=tk.X, pady=1, padx=2)
        self.hw_buttons.append(btn)

        self.hw_canvas.configure(scrollregion=self.hw_canvas.bbox("all"))
        self.hw_canvas.itemconfig(1, width=self.hw_canvas.winfo_width())

    def clear_form(self):
        """Clear the manual entry form"""
        self.sample_id_var.set("")
        self.notes_var.set("")
