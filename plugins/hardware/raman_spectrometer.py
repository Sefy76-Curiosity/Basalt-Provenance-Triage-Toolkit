"""
Raman Spectrometer Plugin
Generic serial/API-based Raman integration
"""

import tkinter as tk
from tkinter import ttk, messagebox
import time

try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

PLUGIN_INFO = {
    "id": "hardware_raman_generic",
    "name": "Raman Spectrometer (Generic)",
    "category": "hardware",
    "type": "raman",
    "manufacturer": "Generic",
    "models": ["B&W Tek", "Ocean Insight", "Other serial/API Raman"],
    "connection": "USB/Serial or API",
    "icon": "📈",
    "description": "Generic Raman spectrometer plugin (serial-based, simple peak detection).",
    "data_types": ["raman_spectrum", "peaks"],
    "requires": ["pyserial"]
}


class RamanGenericPlugin:
    """Generic Raman spectrometer plugin (serial-based mock)"""

    def __init__(self, app):
        self.app = app
        self.window = None
        self.connected = False
        self.serial_port = None
        self.current_spectrum = None
        self.identified_phases = []

    def show_interface(self):
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("📈 Raman Spectrometer (Generic)")
        self.window.geometry("700x600")

        header = ttk.Frame(self.window)
        header.pack(fill="x", padx=10, pady=10)
        ttk.Label(header, text="📈 Raman Spectrometer (Generic)",
                  font=("Arial", 14, "bold")).pack(side="left")

        conn_frame = ttk.LabelFrame(self.window, text="Connection (mock/serial)", padding=10)
        conn_frame.pack(fill="x", padx=10, pady=5)

        self.status_label = ttk.Label(conn_frame, text="● Not Connected", foreground="red")
        self.status_label.pack(side="left", padx=5)

        self.connect_btn = ttk.Button(conn_frame, text="🔌 Connect", command=self.connect_device)
        self.connect_btn.pack(side="left", padx=5)

        ttk.Button(conn_frame, text="🔍 Test", command=self.test_connection).pack(side="left", padx=5)

        spectrum_frame = ttk.LabelFrame(self.window, text="Spectral Data", padding=10)
        spectrum_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.spectrum_text = tk.Text(spectrum_frame, height=12, font=("Courier", 9))
        self.spectrum_text.pack(fill="both", expand=True)

        phase_frame = ttk.LabelFrame(self.window, text="Identified Phases", padding=10)
        phase_frame.pack(fill="x", padx=10, pady=5)

        self.phase_listbox = tk.Listbox(phase_frame, height=5, font=("Arial", 10))
        self.phase_listbox.pack(fill="both", expand=True)

        btn_frame = ttk.Frame(self.window)
        btn_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(btn_frame, text="📥 Scan Now",
                   command=self.acquire_spectrum).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="➕ Add to Sample",
                   command=self.add_to_sample).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🗑️ Clear",
                   command=self.clear_data).pack(side="left", padx=5)

    def connect_device(self):
        # For now, just mark as connected (you can extend to real serial/API)
        self.connected = True
        self.status_label.config(text="● Connected (mock)", foreground="green")
        self.connect_btn.config(text="🔌 Disconnect", command=self.disconnect_device)
        messagebox.showinfo("Connected", "Raman spectrometer (mock) connected.\nExtend this to real serial/API later.")

    def disconnect_device(self):
        self.connected = False
        self.status_label.config(text="● Not Connected", foreground="red")
        self.connect_btn.config(text="🔌 Connect", command=self.connect_device)

    def test_connection(self):
        if not self.connected:
            messagebox.showwarning("Not Connected", "Connect first.")
            return
        messagebox.showinfo("Connection Test", "✅ Raman connection OK (mock).")

    def acquire_spectrum(self):
        if not self.connected:
            messagebox.showwarning("Not Connected", "Connect first.")
            return

        # Mock spectrum: in real life, read from serial/API
        import math
        wavenumbers = list(range(100, 2001, 2))
        intensities = [math.exp(-((wn - 500) ** 2) / 50000) +
                       0.7 * math.exp(-((wn - 1000) ** 2) / 50000)
                       for wn in wavenumbers]

        self.current_spectrum = {
            "wavenumbers": wavenumbers,
            "intensities": intensities,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        self.spectrum_text.delete("1.0", tk.END)
        self.spectrum_text.insert(
            tk.END,
            f"Spectrum acquired: {self.current_spectrum['timestamp']}\n"
            f"Points: {len(wavenumbers)}\nRange: {min(wavenumbers)}–{max(wavenumbers)} cm⁻¹\n\n"
        )

        self.identify_phases(wavenumbers, intensities)
        messagebox.showinfo("Success", "Raman spectrum acquired (mock).")

    def identify_phases(self, wavenumbers, intensities):
        self.identified_phases = []
        self.phase_listbox.delete(0, tk.END)

        peaks = []
        for i in range(1, len(intensities) - 1):
            if intensities[i] > intensities[i - 1] and intensities[i] > intensities[i + 1]:
                if intensities[i] > 0.2:
                    peaks.append(wavenumbers[i])

        if any(460 < p < 470 for p in peaks):
            self.identified_phases.append("Quartz")
        if any(660 < p < 680 for p in peaks):
            self.identified_phases.append("Hematite")
        if any(990 < p < 1010 for p in peaks):
            self.identified_phases.append("Carbonate / organics")

        for ph in self.identified_phases:
            self.phase_listbox.insert(tk.END, f"✓ {ph}")
        if not self.identified_phases:
            self.phase_listbox.insert(tk.END, "No distinct phases identified")

    def add_to_sample(self):
        if not self.current_spectrum:
            messagebox.showwarning("No Data", "Acquire a spectrum first.")
            return
        if not hasattr(self.app, "selected_sample") or not self.app.selected_sample:
            messagebox.showwarning("No Sample", "Select a sample first.")
            return

        s = self.app.selected_sample
        s["Raman_Timestamp"] = self.current_spectrum["timestamp"]
        s["Raman_Points"] = len(self.current_spectrum["wavenumbers"])
        s["Raman_Phases"] = ", ".join(self.identified_phases) if self.identified_phases else "None"

        if hasattr(self.app, "refresh_tree"):
            self.app.refresh_tree()
        if hasattr(self.app, "_mark_unsaved_changes"):
            self.app._mark_unsaved_changes()

        messagebox.showinfo("Success", "Raman data added to current sample.")

    def clear_data(self):
        self.current_spectrum = None
        self.identified_phases = []
        self.spectrum_text.delete("1.0", tk.END)
        self.phase_listbox.delete(0, tk.END)

    def test_connection_simple(self):
        return True, "Raman plugin ready (mock)."


def register_plugin(app):
    return RamanGenericPlugin(app)
