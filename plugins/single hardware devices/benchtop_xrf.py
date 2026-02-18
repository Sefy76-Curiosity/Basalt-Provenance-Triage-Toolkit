"""
Benchtop XRF Plugin
Generic CSV-based import (Bruker, PANalytical, Rigaku, etc.)
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
import os
import time

PLUGIN_INFO = {
    "id": "hardware_benchtop_xrf",
    "name": "Benchtop XRF (CSV Import)",
    "category": "hardware",
    "type": "xrf",
    "manufacturer": "Generic",
    "models": ["Bruker S2/S6", "PANalytical", "Rigaku", "Other CSV XRF"],
    "connection": "File (CSV/XLS export)",
    "icon": "🧪",
    "description": "Imports elemental data from benchtop XRF CSV files.",
    "data_types": ["elements_ppm", "elements_wt%"],
    "requires": []
}


class BenchtopXRFPlugin:
    """Benchtop XRF CSV import plugin"""

    def __init__(self, app):
        self.app = app
        self.window = None
        self.last_file = None
        self.current_elements = {}

    def show_interface(self):
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("🧪 Benchtop XRF – CSV Import")
        self.window.geometry("650x500")

        info = ttk.LabelFrame(self.window, text="How it works", padding=10)
        info.pack(fill="x", padx=10, pady=5)
        ttk.Label(
            info,
            text=(
                "1. Export your XRF results as CSV from vendor software\n"
                "2. Click 'Load CSV' and select the file\n"
                "3. Map columns if needed\n"
                "4. Add to current sample"
            ),
            justify="left"
        ).pack(anchor="w")

        file_frame = ttk.LabelFrame(self.window, text="File", padding=10)
        file_frame.pack(fill="x", padx=10, pady=5)

        self.file_label = ttk.Label(file_frame, text="No file loaded")
        self.file_label.pack(side="left", padx=5)

        ttk.Button(file_frame, text="📂 Load CSV", command=self.load_csv).pack(side="right", padx=5)

        data_frame = ttk.LabelFrame(self.window, text="Parsed Elements (ppm)", padding=10)
        data_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.data_text = tk.Text(data_frame, height=15, font=("Consolas", 9))
        self.data_text.pack(fill="both", expand=True)

        btn_frame = ttk.Frame(self.window)
        btn_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(btn_frame, text="💾 Add to Current Sample",
                   command=self.add_to_sample,
                   style="Accent.TButton").pack(side="left", padx=5)

        ttk.Button(btn_frame, text="🗑️ Clear",
                   command=self.clear_display).pack(side="left", padx=5)

        ttk.Button(btn_frame, text="❌ Close",
                   command=self.window.destroy).pack(side="right", padx=5)

    def load_csv(self):
        path = filedialog.askopenfilename(
            title="Select XRF CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not path:
            return

        self.last_file = path
        self.file_label.config(text=os.path.basename(path))
        self.current_elements = {}

        try:
            with open(path, newline='', encoding="utf-8", errors="ignore") as f:
                reader = csv.DictReader(f)
                # Assume first row is the sample of interest
                row = next(reader, None)
                if not row:
                    raise ValueError("Empty CSV")

                for key, val in row.items():
                    if not val:
                        continue
                    try:
                        v = float(str(val).replace(",", ""))
                    except ValueError:
                        continue

                    # Heuristic: element names like 'Fe', 'Fe_ppm', 'Fe (ppm)'
                    col = key.strip()
                    elem = col.split()[0].split("_")[0].split("(")[0]
                    if len(elem) <= 3 and elem[0].isalpha():
                        self.current_elements[f"{elem}_ppm"] = v

            self.refresh_text()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to parse CSV:\n{e}")

    def refresh_text(self):
        self.data_text.delete("1.0", tk.END)
        if not self.current_elements:
            self.data_text.insert(tk.END, "No elements parsed.\n")
            return
        self.data_text.insert(tk.END, f"File: {self.last_file}\n\n")
        for k, v in sorted(self.current_elements.items()):
            self.data_text.insert(tk.END, f"{k:10} = {v:.2f}\n")

    def add_to_sample(self):
        if not self.current_elements:
            messagebox.showwarning("No Data", "No elements parsed yet.")
            return
        if not hasattr(self.app, "selected_sample") or not self.app.selected_sample:
            messagebox.showwarning("No Sample", "Select a sample first.")
            return

        for k, v in self.current_elements.items():
            self.app.selected_sample[k] = v

        if hasattr(self.app, "refresh_tree"):
            self.app.refresh_tree()
        if hasattr(self.app, "_mark_unsaved_changes"):
            self.app._mark_unsaved_changes()

        messagebox.showinfo("Success", "Benchtop XRF data added to current sample.")
        self.clear_display()

    def clear_display(self):
        self.current_elements = {}
        self.data_text.delete("1.0", tk.END)

    def test_connection(self):
        return True, "Benchtop XRF uses CSV export – no live connection required."


def register_plugin(app):
    return BenchtopXRFPlugin(app)
