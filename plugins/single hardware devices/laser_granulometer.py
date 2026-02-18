"""
Laser Granulometer Plugin
Imports particle size distributions for soil texture
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv

PLUGIN_INFO = {
    "id": "hardware_granulometer",
    "name": "Laser Granulometer",
    "category": "hardware",
    "type": "granulometer",
    "manufacturer": "Generic",
    "models": ["Malvern Mastersizer", "Horiba LA", "Other"],
    "connection": "File (CSV export)",
    "icon": "🌾",
    "description": "Imports sand/silt/clay percentages from granulometer CSV.",
    "data_types": ["Sand_pct", "Silt_pct", "Clay_pct"],
    "requires": []
}


class GranulometerPlugin:
    """Laser granulometer CSV plugin"""

    def __init__(self, app):
        self.app = app
        self.window = None
        self.current_texture = {}

    def show_interface(self):
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("🌾 Laser Granulometer – Soil Texture")
        self.window.geometry("500x350")

        info = ttk.LabelFrame(self.window, text="How it works", padding=10)
        info.pack(fill="x", padx=10, pady=5)
        ttk.Label(
            info,
            text=(
                "1. Export sand/silt/clay percentages as CSV\n"
                "2. Load CSV\n"
                "3. Add texture data to sample"
            ),
            justify="left"
        ).pack(anchor="w")

        btn_frame = ttk.Frame(self.window)
        btn_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(btn_frame, text="📂 Load CSV", command=self.load_csv).pack(side="left", padx=5)

        data_frame = ttk.LabelFrame(self.window, text="Current Texture", padding=10)
        data_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.data_text = tk.Text(data_frame, height=8, font=("Consolas", 9))
        self.data_text.pack(fill="both", expand=True)

        bottom = ttk.Frame(self.window)
        bottom.pack(fill="x", padx=10, pady=10)

        ttk.Button(bottom, text="➕ Add to Sample",
                   command=self.add_to_sample,
                   style="Accent.TButton").pack(side="left", padx=5)
        ttk.Button(bottom, text="🗑️ Clear",
                   command=self.clear_data).pack(side="left", padx=5)
        ttk.Button(bottom, text="❌ Close",
                   command=self.window.destroy).pack(side="right", padx=5)

    def load_csv(self):
        path = filedialog.askopenfilename(
            title="Select granulometer CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not path:
            return

        self.current_texture = {}
        try:
            with open(path, newline='', encoding="utf-8", errors="ignore") as f:
                reader = csv.DictReader(f)
                row = next(reader, None)
                if not row:
                    raise ValueError("Empty CSV")

                for key, val in row.items():
                    if not val:
                        continue
                    k = key.strip().lower()
                    try:
                        v = float(str(val).replace(",", ""))
                    except ValueError:
                        continue

                    if "sand" in k:
                        self.current_texture["Sand_pct"] = v
                    elif "silt" in k:
                        self.current_texture["Silt_pct"] = v
                    elif "clay" in k:
                        self.current_texture["Clay_pct"] = v

            self.refresh_text()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to parse CSV:\n{e}")

    def refresh_text(self):
        self.data_text.delete("1.0", tk.END)
        if not self.current_texture:
            self.data_text.insert(tk.END, "No texture data.\n")
            return
        for k, v in self.current_texture.items():
            self.data_text.insert(tk.END, f"{k}: {v:.1f} %\n")

    def add_to_sample(self):
        if not self.current_texture:
            messagebox.showwarning("No Data", "No texture data loaded.")
            return
        if not hasattr(self.app, "selected_sample") or not self.app.selected_sample:
            messagebox.showwarning("No Sample", "Select a sample first.")
            return

        for k, v in self.current_texture.items():
            self.app.selected_sample[k] = v

        if hasattr(self.app, "refresh_tree"):
            self.app.refresh_tree()
        if hasattr(self.app, "_mark_unsaved_changes"):
            self.app._mark_unsaved_changes()

        messagebox.showinfo("Success", "Texture data added to current sample.")

    def clear_data(self):
        self.current_texture = {}
        self.data_text.delete("1.0", tk.END)

    def test_connection(self):
        return True, "Granulometer plugin uses CSV import – no live connection required."


def register_plugin(app):
    return GranulometerPlugin(app)
