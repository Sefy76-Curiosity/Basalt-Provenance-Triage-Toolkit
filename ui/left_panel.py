"""
Left Panel - 10% width, Data Input
Manual Entry takes fixed height, Hardware at bottom
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import re
import json
from pathlib import Path

class LeftPanel:
    def __init__(self, parent, app):
        self.app = app
        self.frame = ttk.Frame(parent, relief=tk.RAISED, borderwidth=1)

        # Load column mappings from JSON
        self.column_mappings = self._load_column_mappings()
        self.element_reverse_map = self._build_reverse_map()

        # Entry variables
        self.sample_id_var = tk.StringVar()
        self.notes_var = tk.StringVar()

        # Hardware buttons container
        self.hw_container = None
        self.hw_buttons = []

        # Track panel height for dynamic sizing
        self.frame.bind("<Configure>", self._on_frame_resize)

        self._build_ui()

    def _load_column_mappings(self):
        """Load column mappings from chemical_elements.json"""
        config_file = Path("config/chemical_elements.json")
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    elements = data.get("elements", {})

                    # Build mappings dictionary
                    mappings = {}
                    for elem, info in elements.items():
                        standard = info["standard"]
                        for var in info["variations"]:
                            mappings[var.lower()] = standard

                    print(f"✅ LeftPanel loaded {len(mappings)} column mappings")
                    return mappings
            except Exception as e:
                print(f"⚠️ Error loading chemical_elements.json: {e}")
                return {}
        else:
            print(f"⚠️ chemical_elements.json not found in config folder")
            return {}

    def _build_reverse_map(self):
        """Build reverse lookup map for quick access"""
        reverse_map = {}
        for var, standard in self.column_mappings.items():
            reverse_map[var] = standard
        return reverse_map

    @staticmethod
    def normalize_column_name(name, mappings=None):
        """
        Normalize column names using JSON mappings

        Strategy:
        1. Strip whitespace
        2. Convert to lowercase for lookup
        3. Match against loaded JSON mappings
        4. If no match, preserve original with minimal cleanup
        """
        if not name:
            return name

        # Strip whitespace from ends
        cleaned = str(name).strip()

        # Create lookup key (lowercase, normalized spacing)
        lookup_key = cleaned.lower()
        lookup_key = re.sub(r'\s+', ' ', lookup_key)  # Normalize multiple spaces

        # Try with spaces
        if mappings and lookup_key in mappings:
            return mappings[lookup_key]

        # Try with underscores (replace spaces with underscores)
        lookup_key_underscore = lookup_key.replace(' ', '_')
        if mappings and lookup_key_underscore in mappings:
            return mappings[lookup_key_underscore]

        # Try without any separators
        lookup_key_nosep = re.sub(r'[\s_]+', '', lookup_key)
        if mappings and lookup_key_nosep in mappings:
            return mappings[lookup_key_nosep]

        # If no mapping found, preserve original but clean it up minimally
        # Just replace multiple spaces with single underscore
        result = re.sub(r'\s+', '_', cleaned)

        return result

    def _build_ui(self):
        """Build left panel UI with proper spacing"""
        # ... (rest of your existing _build_ui method remains exactly the same)
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
        """Import CSV or Excel file with column name normalization using JSON mappings"""
        if path is None:
            path = filedialog.askopenfilename(
                filetypes=[
                    ("All supported files", "*.csv *.xlsx *.xls"),
                    ("CSV files", "*.csv"),
                    ("Excel files", "*.xlsx *.xls"),
                    ("All files", "*.*")
                ]
            )
            if not path:
                return

        try:
            rows = []

            # Show initial progress
            self.app.center.show_progress('import', 0, 1, "Reading file...")

            # Handle CSV files
            if path.lower().endswith('.csv'):
                import csv
                with open(path, 'r', encoding='utf-8-sig') as f:
                    # Read all lines and filter out comments
                    non_comment_lines = [line for line in f if not line.strip().startswith('#')]

                    # Create a StringIO object to feed to DictReader
                    import io
                    filtered_file = io.StringIO(''.join(non_comment_lines))

                    reader = csv.DictReader(filtered_file)
                    if reader.fieldnames:
                        print(f"\n📥 Original CSV columns: {reader.fieldnames}")

                        # Convert reader to list to get total count
                        all_rows = list(reader)
                        total_rows = len(all_rows)

                        self.app.center.show_progress('import', 0, total_rows, f"Found {total_rows} rows")

                        for i, row in enumerate(all_rows):
                            # Update progress every 10 rows or so to avoid too many updates
                            if i % 10 == 0 or i == total_rows - 1:
                                self.app.center.show_progress('import', i+1, total_rows,
                                                            f"Processing row {i+1}: {row.get('Sample_ID', 'Unknown')[:20]}")

                            clean_row = {}
                            notes_parts = []
                            seen_standards = set()

                            # First, look for Sample_ID explicitly
                            sample_id_found = False
                            for k, v in row.items():
                                if not k or not k.strip():
                                    continue

                                # Get the raw column name and value
                                raw_key = k.strip()
                                clean_val = v.strip() if v else ''

                                # Skip empty values
                                if not clean_val:
                                    continue

                                # Normalize the column name
                                normalized_key = self.normalize_column_name(raw_key, self.column_mappings)

                                # Handle Sample_ID - this is critical
                                if normalized_key == 'Sample_ID':
                                    if normalized_key not in seen_standards:
                                        clean_row[normalized_key] = clean_val
                                        seen_standards.add(normalized_key)
                                        sample_id_found = True

                                # Handle mapped columns (chemical elements, etc.)
                                elif normalized_key in self.column_mappings.values():
                                    if normalized_key not in seen_standards:
                                        try:
                                            # Try to convert to float for numeric columns
                                            if clean_val and clean_val.strip():
                                                # Handle commas in numbers
                                                clean_val = clean_val.replace(',', '')
                                                num_val = float(clean_val)
                                                clean_row[normalized_key] = num_val
                                            else:
                                                clean_row[normalized_key] = None
                                        except ValueError:
                                            clean_row[normalized_key] = clean_val
                                        seen_standards.add(normalized_key)

                                # For all other columns (including Depth_cm, C14_age_BP, etc.)
                                # Keep them with their original names if they're not in mappings
                                else:
                                    # Check if this is likely a data column we want to keep
                                    if raw_key not in seen_standards:
                                        # Try to convert to number if possible
                                        try:
                                            if clean_val and clean_val.strip():
                                                # Handle commas in numbers
                                                clean_val = clean_val.replace(',', '')
                                                num_val = float(clean_val)
                                                clean_row[raw_key] = num_val
                                            else:
                                                clean_row[raw_key] = None
                                        except ValueError:
                                            clean_row[raw_key] = clean_val
                                        seen_standards.add(raw_key)

                            # If no Sample_ID found, create one
                            if not sample_id_found:
                                clean_row['Sample_ID'] = f"IMP_{len(rows)+1:04d}"

                            # Only add Notes if there's actually something to note
                            if notes_parts:
                                clean_row['Notes'] = ' | '.join(notes_parts)

                            if clean_row:
                                rows.append(clean_row)

            # Handle Excel files
            else:  # .xlsx or .xls
                try:
                    import pandas as pd
                    # Read Excel file
                    df = pd.read_excel(path)

                    print(f"\n📥 Original Excel columns: {list(df.columns)}")

                    total_rows = len(df)
                    self.app.center.show_progress('import', 0, total_rows, f"Found {total_rows} rows")

                    # Process each row
                    for i, (_, row) in enumerate(df.iterrows()):
                        # Update progress every 10 rows
                        if i % 10 == 0 or i == total_rows - 1:
                            self.app.center.show_progress('import', i+1, total_rows,
                                                        f"Processing row {i+1}")

                        clean_row = {}
                        notes_parts = []
                        seen_standards = set()
                        sample_id_found = False

                        # Convert row to dictionary, handling NaN values
                        row_dict = {}
                        for col in df.columns:
                            val = row[col]
                            if pd.isna(val):
                                row_dict[col] = ''
                            else:
                                row_dict[col] = str(val).strip()

                        for raw_key, clean_val in row_dict.items():
                            if not raw_key or not raw_key.strip():
                                continue

                            if not clean_val:
                                continue

                            # Normalize the column name
                            normalized_key = self.normalize_column_name(raw_key, self.column_mappings)

                            # Handle Sample_ID
                            if normalized_key == 'Sample_ID':
                                if normalized_key not in seen_standards:
                                    clean_row[normalized_key] = clean_val
                                    seen_standards.add(normalized_key)
                                    sample_id_found = True

                            # Handle mapped columns
                            elif normalized_key in self.column_mappings.values():
                                if normalized_key not in seen_standards:
                                    try:
                                        if clean_val and clean_val.strip():
                                            clean_val = clean_val.replace(',', '')
                                            num_val = float(clean_val)
                                            clean_row[normalized_key] = num_val
                                        else:
                                            clean_row[normalized_key] = None
                                    except ValueError:
                                        clean_row[normalized_key] = clean_val
                                    seen_standards.add(normalized_key)

                            # Keep all other columns with their original names
                            else:
                                if raw_key not in seen_standards:
                                    try:
                                        if clean_val and clean_val.strip():
                                            clean_val = clean_val.replace(',', '')
                                            num_val = float(clean_val)
                                            clean_row[raw_key] = num_val
                                        else:
                                            clean_row[raw_key] = None
                                    except ValueError:
                                        clean_row[raw_key] = clean_val
                                    seen_standards.add(raw_key)

                        # If no Sample_ID found, create one
                        if not sample_id_found:
                            clean_row['Sample_ID'] = f"IMP_{len(rows)+1:04d}"

                        # Only add Notes if there's actually something to note
                        if notes_parts:
                            clean_row['Notes'] = ' | '.join(notes_parts)

                        if clean_row:
                            rows.append(clean_row)

                except ImportError:
                    self.app.center.show_error('import', "pandas not installed")
                    messagebox.showerror(
                        "Error",
                        "Excel import requires pandas. Install with: pip install pandas openpyxl"
                    )
                    return
                except Exception as e:
                    self.app.center.show_error('import', str(e))
                    messagebox.showerror("Error", f"Failed to read Excel file: {e}")
                    return

            # Handle the imported rows
            if rows:
                print(f"✅ Imported {len(rows)} rows")
                print(f"📊 Columns found: {list(rows[0].keys())}")
                self.app.data_hub.add_samples(rows)
                self.app.center.show_operation_complete('import', f"{len(rows)} rows imported")
                messagebox.showinfo("Success", f"Imported {len(rows)} rows from {path}")
            else:
                self.app.center.show_warning('import', "No data found in file")
                messagebox.showwarning("Warning", "No data found in file")

        except Exception as e:
            self.app.center.show_error('import', str(e))
            messagebox.showerror("Error", f"Failed to import: {e}")
            import traceback
            traceback.print_exc()

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

        # Use tk.Button instead of ttk.Button for better style control
        btn = tk.Button(self.hw_scrollable,
                    text=button_text,
                    command=command,
                    anchor='w',
                    justify='left',
                    relief=tk.RAISED,
                    bd=1,
                    padx=4)
        btn.pack(fill=tk.X, pady=1, padx=2)
        self.hw_buttons.append(btn)

        self.hw_canvas.configure(scrollregion=self.hw_canvas.bbox("all"))
        self.hw_canvas.itemconfig(1, width=self.hw_canvas.winfo_width())

    def clear_form(self):
        """Clear the manual entry form"""
        self.sample_id_var.set("")
        self.notes_var.set("")
