"""
EC Meter Plugin
Soil/water electrical conductivity via serial
"""

import tkinter as tk
from tkinter import ttk, messagebox
import time

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

PLUGIN_INFO = {
    "id": "hardware_ec_meter",
    "name": "EC Meter (Salinity)",
    "category": "hardware",
    "type": "ec",
    "manufacturer": "Generic",
    "models": ["Hanna", "Extech", "YSI", "Other serial EC"],
    "connection": "USB/Serial",
    "icon": "⚡",
    "description": "Reads EC (dS/m) from serial EC meters.",
    "data_types": ["EC_dS_m"],
    "requires": ["pyserial"]
}


class ECMeterPlugin:
    """Serial EC meter plugin"""

    def __init__(self, app):
        self.app = app
        self.window = None
        self.serial_port = None
        self.connected = False
        self.current_ec = None

    def show_interface(self):
        if not SERIAL_AVAILABLE:
            messagebox.showerror("Missing Dependency", "pyserial not installed.")
            return

        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("⚡ EC Meter – Salinity")
        self.window.geometry("450x300")

        conn = ttk.LabelFrame(self.window, text="Connection", padding=10)
        conn.pack(fill="x", padx=10, pady=5)

        ttk.Label(conn, text="Port:").pack(side="left")
        self.port_var = tk.StringVar()
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.port_combo = ttk.Combobox(conn, textvariable=self.port_var, values=ports, width=15)
        self.port_combo.pack(side="left", padx=5)
        if ports:
            self.port_combo.current(0)

        self.status_label = ttk.Label(conn, text="● Disconnected", foreground="red")
        self.status_label.pack(side="right")

        ttk.Button(conn, text="🔌 Connect", command=self.connect_device).pack(side="left", padx=5)

        val_frame = ttk.LabelFrame(self.window, text="Current EC", padding=10)
        val_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.ec_label = ttk.Label(val_frame, text="EC: --- dS/m", font=("Arial", 16))
        self.ec_label.pack(pady=10)

        btn_frame = ttk.Frame(self.window)
        btn_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(btn_frame, text="📥 Read Once", command=self.read_once).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="➕ Add to Sample", command=self.add_to_sample).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="❌ Close", command=self.on_close).pack(side="right", padx=5)

    def connect_device(self):
        port = self.port_var.get()
        if not port:
            messagebox.showwarning("No Port", "Select a port first.")
            return
        try:
            self.serial_port = serial.Serial(port, baudrate=9600, timeout=1)
            self.connected = True
            self.status_label.config(text=f"● Connected ({port})", foreground="green")
            messagebox.showinfo("Connected", f"Connected to EC meter on {port}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect:\n{e}")

    def read_once(self):
        if not self.connected or not self.serial_port:
            messagebox.showwarning("Not Connected", "Connect to EC meter first.")
            return
        try:
            line = self.serial_port.readline().decode("ascii", errors="ignore").strip()
            # Expect something like "EC=1.23 dS/m" or "1.23"
            import re
            m = re.search(r"([\d\.]+)", line)
            if not m:
                raise ValueError(f"Unrecognized line: {line}")
            val = float(m.group(1))
            self.current_ec = val
            self.ec_label.config(text=f"EC: {val:.2f} dS/m")
        except Exception as e:
            messagebox.showerror("Read Error", f"Failed to read EC:\n{e}")

    def add_to_sample(self):
        if self.current_ec is None:
            messagebox.showwarning("No Data", "Read EC first.")
            return
        if not hasattr(self.app, "selected_sample") or not self.app.selected_sample:
            messagebox.showwarning("No Sample", "Select a sample first.")
            return

        self.app.selected_sample["EC_dS_m"] = self.current_ec

        if hasattr(self.app, "refresh_tree"):
            self.app.refresh_tree()
        if hasattr(self.app, "_mark_unsaved_changes"):
            self.app._mark_unsaved_changes()

        messagebox.showinfo("Success", "EC value added to current sample.")

    def on_close(self):
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        if self.window:
            self.window.destroy()

    def test_connection(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        if ports:
            return True, f"Found {len(ports)} serial port(s)."
        return False, "No serial ports found."


def register_plugin(app):
    return ECMeterPlugin(app)
