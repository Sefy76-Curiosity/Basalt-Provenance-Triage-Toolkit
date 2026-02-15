"""
Ion Meter / IC Plugin
Reads Na, Ca, Mg from serial/CSV for SAR
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

PLUGIN_INFO = {
    "id": "hardware_ion_meter",
    "name": "Ion Meter / IC (Na, Ca, Mg)",
    "category": "hardware",
    "type": "ion",
    "manufacturer": "Generic",
    "models": ["Metrohm", "Dionex", "Hach", "Other"],
    "connection": "Serial or CSV",
    "icon": "🧂",
    "description": "Imports Na, Ca, Mg for SAR calculation.",
    "data_types": ["Na_meqL", "Ca_meqL", "Mg_meqL"],
    "requires": ["pyserial"]
}


class IonMeterPlugin:
    """Ion meter / IC plugin (serial or CSV)"""

    def __init__(self, app):
        self.app = app
        self.window = None
        self.current_ions = {}

    def show_interface(self):
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("🧂 Ion Meter / IC – Na, Ca, Mg")
        self.window.geometry("550x400")

        mode_frame = ttk.LabelFrame(self.window, text="Import Mode", padding=10)
        mode_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(mode_frame, text="📂 Load CSV", command=self.load_csv).pack(side="left", padx=5)
        if SERIAL_AVAILABLE:
            ttk.Button(mode_frame, text="🔌 Serial Read (simple)", command=self.serial_read_once).pack(side="left", padx=5)

        data_frame = ttk.LabelFrame(self.window, text="Current Ions", padding=10)
        data_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.data_text = tk.Text(data_frame, height=10, font=("Consolas", 9))
        self.data_text.pack(fill="both", expand=True)

        btn_frame = ttk.Frame(self.window)
        btn_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(btn_frame, text="➕ Add to Sample",
                   command=self.add_to_sample,
                   style="Accent.TButton").pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🗑️ Clear",
                   command=self.clear_data).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="❌ Close",
                   command=self.window.destroy).pack(side="right", padx=5)

    def load_csv(self):
        path = filedialog.askopenfilename(
            title="Select ion CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not path:
            return

        self.current_ions = {}
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

                    if "na" in k:
                        self.current_ions["Na_meqL"] = v
                    elif "ca" in k:
                        self.current_ions["Ca_meqL"] = v
                    elif "mg" in k:
                        self.current_ions["Mg_meqL"] = v

            self.refresh_text()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to parse CSV:\n{e}")

    def serial_read_once(self):
        if not SERIAL_AVAILABLE:
            messagebox.showerror("Missing Dependency", "pyserial not installed.")
            return

        ports = [p.device for p in serial.tools.list_ports.comports()]
        if not ports:
            messagebox.showwarning("No Ports", "No serial ports found.")
            return

        import serial
        try:
            ser = serial.Serial(ports[0], baudrate=9600, timeout=2)
            line = ser.readline().decode("ascii", errors="ignore").strip()
            ser.close()
            # Expect something like "Na=3.2;Ca=2.1;Mg=1.5"
            self.current_ions = {}
            for part in line.split(";"):
                if "=" in part:
                    k, v = part.split("=", 1)
                    k = k.strip().lower()
                    try:
                        val = float(v)
                    except ValueError:
                        continue
                    if "na" in k:
                        self.current_ions["Na_meqL"] = val
                    elif "ca" in k:
                        self.current_ions["Ca_meqL"] = val
                    elif "mg" in k:
                        self.current_ions["Mg_meqL"] = val
            self.refresh_text()
        except Exception as e:
            messagebox.showerror("Error", f"Serial read failed:\n{e}")

    def refresh_text(self):
        self.data_text.delete("1.0", tk.END)
        if not self.current_ions:
            self.data_text.insert(tk.END, "No ion data.\n")
            return
        for k, v in self.current_ions.items():
            self.data_text.insert(tk.END, f"{k}: {v:.3f}\n")

    def add_to_sample(self):
        if not self.current_ions:
            messagebox.showwarning("No Data", "No ion data loaded.")
            return
        if not hasattr(self.app, "selected_sample") or not self.app.selected_sample:
            messagebox.showwarning("No Sample", "Select a sample first.")
            return

        for k, v in self.current_ions.items():
            self.app.selected_sample[k] = v

        if hasattr(self.app, "refresh_tree"):
            self.app.refresh_tree()
        if hasattr(self.app, "_mark_unsaved_changes"):
            self.app._mark_unsaved_changes()

        messagebox.showinfo("Success", "Ion data added to current sample.")

    def clear_data(self):
        self.current_ions = {}
        self.data_text.delete("1.0", tk.END)

    def test_connection(self):
        return True, "Ion meter plugin ready (CSV/serial)."


def register_plugin(app):
    return IonMeterPlugin(app)
