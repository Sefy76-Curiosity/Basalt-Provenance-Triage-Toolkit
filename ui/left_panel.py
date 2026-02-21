"""
Left Panel - 10% width, Data Input
Manual Entry takes fixed height, Hardware at bottom (dynamically sized height only)
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

        # ============ 3. HARDWARE PLUGINS (dynamic height only, fixed width) ============
        hw_label = ttk.Label(self.frame, text="🔌 Hardware", font=("TkDefaultFont", 8, "bold"))
        hw_label.pack(anchor=tk.W, padx=2, pady=(5,0), side=tk.BOTTOM)

        # Container with dynamic height but fixed width (fills X)
        self.hw_container = ttk.Frame(self.frame, relief=tk.SUNKEN, borderwidth=1)
        self.hw_container.pack(fill=tk.X, padx=2, pady=2, side=tk.BOTTOM, expand=False)
        # NO pack_propagate(False) - allow height to adjust to content

        # Simple frame for buttons - no canvas/scrollbar if we want dynamic height
        # This will grow with content
        self.hw_button_frame = ttk.Frame(self.hw_container)
        self.hw_button_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        # Placeholder (will be removed when first plugin is added)
        self._placeholder = ttk.Label(self.hw_button_frame, text="No hardware plugins installed",
                                     font=("TkDefaultFont", 7), foreground="gray")
        self._placeholder.pack(fill=tk.X, pady=5, padx=2)

    def _on_frame_resize(self, event):
        """Handle frame resize to adjust Manual Entry height"""
        if event.widget != self.frame:
            return

        # Prevent recursive calls
        if getattr(self, '_resizing', False):
            return

        self._resizing = True
        try:
            total_height = event.height

            # Fixed heights: import button (~30px), hardware label (~20px), padding (~20px)
            fixed_height = 30 + 20 + 20

            # Get current hardware container height (no forced update needed)
            hw_height = self.hw_container.winfo_height()

            # Manual Entry gets the rest, with a minimum of 100px
            manual_height = max(100, total_height - fixed_height - hw_height)

            # Only change if the height actually differs (prevents unnecessary configure events)
            current_height = self.entry_frame.winfo_height()
            if abs(current_height - manual_height) > 2:  # small threshold to avoid micro-changes
                self.entry_frame.configure(height=manual_height)
        finally:
            self._resizing = False

    def _import_file_dialog(self):
        """Open file dialog with multi‑file selection support."""
        filetypes = [
            ("All supported files", "*.csv *.xlsx *.xls *.ods *.txt *.mca *.spec"),
            ("CSV files", "*.csv"),
            ("Excel files", "*.xlsx *.xls"),
            ("LibreOffice Calc", "*.ods"),
            ("Amptek spectra", "*.txt *.mca *.spec"),
            ("All files", "*.*")
        ]
        paths = filedialog.askopenfilenames(
            title="Import Data Files (Ctrl+Click to select multiple)",
            filetypes=filetypes
        )
        if not paths:
            return

        total = len(paths)
        for i, path in enumerate(paths):
            self.app.center.set_status(
                f"Importing file {i+1} of {total}: {Path(path).name}",
                "processing"
            )
            self.import_csv(path, silent=True)   # suppress per‑file success dialogs

        self.app.center.set_status(f"Imported {total} files", "success")
        messagebox.showinfo("Batch Import Complete", f"Successfully imported {total} files.")

    def import_csv(self, path=None, silent=False):
        """
        Unified import dispatcher.
        If silent=True, suppress success/warning messageboxes (errors still shown).
        """
        if path is None:
            path = filedialog.askopenfilename(
                title="Import Data File",
                filetypes=[
                    ("All supported files", "*.csv *.xlsx *.xls *.ods *.txt *.mca *.spec"),
                    ("CSV files", "*.csv"),
                    ("Excel files", "*.xlsx *.xls"),
                    ("LibreOffice Calc", "*.ods"),
                    ("Amptek spectra", "*.txt *.mca *.spec"),
                    ("All files", "*.*")
                ]
            )
            if not path:
                return
            silent = False   # when user picks a single file, show dialogs

        try:
            ext = path.lower()
            rows = []

            if ext.endswith('.csv'):
                rows = self._parse_csv(path)
            elif ext.endswith(('.xlsx', '.xls', '.ods')):
                rows = self._parse_excel_ods(path)
            elif ext.endswith(('.txt', '.mca', '.spec')):
                rows = self._parse_amptek_spectrum(path)
            else:
                self.app.center.show_error('import', f"Unsupported file format: {path}")
                messagebox.showerror("Error", f"Unsupported file format: {path}")
                return

            if rows:
                self.app.data_hub.add_samples(rows)
                self.app.center.show_operation_complete('import', f"{len(rows)} rows imported")
                if not silent:
                    messagebox.showinfo("Success", f"Imported {len(rows)} rows from {path}")
            else:
                self.app.center.show_warning('import', "No data found in file")
                if not silent:
                    messagebox.showwarning("Warning", f"No data found in {path}")

        except Exception as e:
            self.app.center.show_error('import', str(e))
            messagebox.showerror("Error", f"Failed to import {path}: {e}")
            import traceback
            traceback.print_exc()

    def _parse_excel_ods(self, path):
        """Parse Excel or LibreOffice ODS file, return list of row dictionaries."""
        try:
            import pandas as pd
        except ImportError:
            self.app.center.show_error('import', "pandas not installed")
            messagebox.showerror(
                "Error",
                "Excel/ODS import requires pandas. Install with:\n"
                "pip install pandas openpyxl odfpy"
            )
            return []

        rows = []
        ext = path.lower()
        engine = 'odf' if ext.endswith('.ods') else None
        df = pd.read_excel(path, engine=engine)

        total_rows = len(df)
        self.app.center.show_progress('import', 0, total_rows, f"Found {total_rows} rows")

        data_rows = []
        for _, row in df.iterrows():
            row_dict = {}
            for col in df.columns:
                val = row[col]
                row_dict[col] = '' if pd.isna(val) else str(val).strip()
            data_rows.append(row_dict)

        for i, raw_row in enumerate(data_rows):
            if i % 10 == 0 or i == total_rows - 1:
                self.app.center.show_progress('import', i+1, total_rows,
                                            f"Processing row {i+1}")

            clean_row = self._normalize_row(raw_row, rows)
            if clean_row:
                rows.append(clean_row)

        return rows

    def _parse_amptek_spectrum(self, path):
        """
        Parse an Amptek spectrum file (.txt, .mca, .spec) and return a list
        with one dictionary representing the spectrum.
        Handles various encodings gracefully.
        """
        # Try multiple encodings in order of likelihood
        encodings = ['utf-8', 'latin-1', 'cp1252']
        lines = None
        for enc in encodings:
            try:
                with open(path, 'r', encoding=enc) as f:
                    lines = f.readlines()
                break
            except UnicodeDecodeError:
                continue

        if lines is None:
            with open(path, 'rb') as f:
                raw = f.read()
                lines = raw.decode('utf-8', errors='ignore').splitlines()

        data_start = None
        data_end = None
        calibration = None
        metadata = {}
        data_counts = []

        for i, line in enumerate(lines):
            line = line.strip()
            if line == '<<DATA>>':
                data_start = i + 1
            elif line == '<<END>>':
                data_end = i
            elif line == '<<CALIBRATION>>':
                if i + 2 < len(lines):
                    parts1 = lines[i+1].strip().split()
                    parts2 = lines[i+2].strip().split()
                    if len(parts1) == 2 and len(parts2) == 2:
                        calibration = {
                            'ch1': float(parts1[0]), 'e1': float(parts1[1]),
                            'ch2': float(parts2[0]), 'e2': float(parts2[1])
                        }
            elif line.startswith('LIVE_TIME'):
                metadata['Live_Time'] = line.split('-')[-1].strip()
            elif line.startswith('REAL_TIME'):
                metadata['Real_Time'] = line.split('-')[-1].strip()
            elif line.startswith('START_TIME'):
                metadata['Start_Time'] = line.split('-')[-1].strip()
            elif line.startswith('SERIAL_NUMBER'):
                metadata['Serial_Number'] = line.split('-')[-1].strip()
            # Add more metadata fields if needed

        if data_start is None or data_end is None:
            raise ValueError("Could not find <<DATA>> section in spectrum file")

        for line in lines[data_start:data_end]:
            line = line.strip()
            if line:
                try:
                    data_counts.append(int(line))
                except ValueError:
                    # Skip any non‑integer lines (should not happen in valid files)
                    continue

        sample = {
            'Sample_ID': Path(path).stem,
            'Notes': f"Amptek spectrum, {len(data_counts)} channels",
            'Channel_Count': len(data_counts),
            'Spectrum_Data': ','.join(str(c) for c in data_counts),
        }

        if calibration:
            sample['Calib_Ch1'] = calibration['ch1']
            sample['Calib_e1']  = calibration['e1']
            sample['Calib_Ch2'] = calibration['ch2']
            sample['Calib_e2']  = calibration['e2']
            slope = (calibration['e2'] - calibration['e1']) / (calibration['ch2'] - calibration['ch1'])
            intercept = calibration['e1'] - slope * calibration['ch1']
            sample['keV_per_channel'] = slope
            sample['keV_offset'] = intercept

        sample.update(metadata)

        return [sample]

    def _normalize_row(self, raw_row, existing_rows):
        """
        Apply column name normalization, type conversion, and ensure Sample_ID.
        raw_row: dict from parser
        existing_rows: list of already processed rows (used for generating IMP_ IDs)
        Returns a cleaned dictionary or None if row is empty.
        """
        clean_row = {}
        notes_parts = []
        seen_standards = set()
        sample_id_found = False

        for k, v in raw_row.items():
            if not k or not k.strip():
                continue
            raw_key = k.strip()
            clean_val = v.strip() if v else ''
            if not clean_val:
                continue

            normalized_key = self.normalize_column_name(raw_key, self.column_mappings)

            if normalized_key == 'Sample_ID':
                if normalized_key not in seen_standards:
                    clean_row[normalized_key] = clean_val
                    seen_standards.add(normalized_key)
                    sample_id_found = True
            elif normalized_key in self.column_mappings.values():
                if normalized_key not in seen_standards:
                    try:
                        clean_val = clean_val.replace(',', '')
                        num_val = float(clean_val)
                        clean_row[normalized_key] = num_val
                    except ValueError:
                        clean_row[normalized_key] = clean_val
                    seen_standards.add(normalized_key)
            else:
                if raw_key not in seen_standards:
                    try:
                        clean_val = clean_val.replace(',', '')
                        num_val = float(clean_val)
                        clean_row[raw_key] = num_val
                    except ValueError:
                        clean_row[raw_key] = clean_val
                    seen_standards.add(raw_key)

        if not sample_id_found:
            clean_row['Sample_ID'] = f"IMP_{len(existing_rows)+1:04d}"

        if notes_parts:
            clean_row['Notes'] = ' | '.join(notes_parts)

        return clean_row if clean_row else None

    def _parse_csv(self, path):
        """Parse a CSV file and return a list of row dictionaries."""
        import csv, io
        rows = []
        with open(path, 'r', encoding='utf-8-sig') as f:
            non_comment_lines = [line for line in f if not line.strip().startswith('#')]
            filtered_file = io.StringIO(''.join(non_comment_lines))
            reader = csv.DictReader(filtered_file)
            if not reader.fieldnames:
                return rows
            data_rows = list(reader)
            total_rows = len(data_rows)
            self.app.center.show_progress('import', 0, total_rows, f"Found {total_rows} rows")

            for i, raw_row in enumerate(data_rows):
                if i % 10 == 0 or i == total_rows - 1:
                    self.app.center.show_progress('import', i+1, total_rows,
                                                f"Processing row {i+1}")

                # THIS IS THE CORRECT LINE - calls _normalize_row
                clean_row = self._normalize_row(raw_row, rows)
                if clean_row:
                    rows.append(clean_row)

        return rows

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
        """Add hardware plugin button - with dynamic height adjustment (width fixed)"""
        # Check if this button already exists
        button_text = f"{icon} {name}"
        for btn in self.hw_buttons:
            if hasattr(btn, 'cget') and btn.cget('text') == button_text:
                print(f"⏭️ Button '{button_text}' already exists, skipping...")
                return

        if hasattr(self, '_placeholder') and self._placeholder.winfo_exists():
            self._placeholder.destroy()
            delattr(self, '_placeholder')

        # Use tk.Button for better style control
        btn = tk.Button(self.hw_button_frame,
                    text=button_text,
                    command=command,
                    anchor='w',
                    justify='left',
                    relief=tk.RAISED,
                    bd=1,
                    padx=4)
        btn.pack(fill=tk.X, pady=1, padx=2)  # fill=X keeps width fixed to container
        self.hw_buttons.append(btn)

        # Force the container to update its height and trigger a resize event
        self.hw_container.update_idletasks()

        # Trigger frame resize to recalculate manual entry height
        self.frame.event_generate("<Configure>")

    def remove_hardware_button(self, name, icon):
        """Remove a hardware plugin button by name and icon."""
        button_text = f"{icon} {name}"
        for btn in self.hw_buttons:
            if hasattr(btn, 'cget') and btn.cget('text') == button_text:
                btn.destroy()
                self.hw_buttons.remove(btn)
                break

        # Restore placeholder if no buttons remain
        if not self.hw_buttons and not hasattr(self, '_placeholder'):
            self._placeholder = ttk.Label(self.hw_button_frame,
                                          text="No hardware plugins installed",
                                          foreground="gray")
            self._placeholder.pack(pady=4)

        self.hw_container.update_idletasks()
        self.frame.event_generate("<Configure>")

    def clear_form(self):
        """Clear the manual entry form"""
        self.sample_id_var.set("")
        self.notes_var.set("")
