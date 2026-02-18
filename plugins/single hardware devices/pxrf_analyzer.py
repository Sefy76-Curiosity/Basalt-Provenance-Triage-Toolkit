"""
pXRF Analyzer Plugin for Basalt Provenance Triage Toolkit v10.2
Supports: Thermo Niton, Olympus/Evident Vanta, Bruker Tracer/S1 Titan + generic fallback

Automatically imports element data from pXRF via USB/Serial connection
"""
import sys
import os

# Critical fix: make Python look in THIS file's folder for the sibling parsers
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import re

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

# ────────────────────────────────────────────────
# Import the separate parsers (one file per brand)
# ────────────────────────────────────────────────
from niton_parser import NitonParser
from vanta_parser import VantaParser
from bruker_tracer_parser import BrukerTracerParser

PLUGIN_INFO = {
    "id": "hardware_pxrf_analyzer",
    "name": "pXRF Analyzer (Universal)",
    "category": "hardware",
    "icon": "📡",
    "description": "Connects to pXRF devices (Niton, Vanta, Bruker Tracer, etc.) and auto-imports element data.",
    "requires": ["pyserial"]
}

class pXRFAnalyzerPlugin:
    """
    Universal pXRF Analyzer Plugin

    Supports multiple brands via serial/USB.
    Uses dedicated parsers per manufacturer + fallback.
    """

    def __init__(self, app):
        self.app = app
        self.window = None
        self.serial_port = None
        self.connected = False
        self.listening = False
        self.listener_thread = None

        # Current scan data
        self.current_elements = {}

        # UI references
        self.port_var = None
        self.status_label = None
        self.data_text = None
        self.element_labels = {}

    def show_interface(self):
        """Open the pXRF control window"""
        if not SERIAL_AVAILABLE:
            messagebox.showerror("Missing Dependency",
                               "pyserial not installed!\n\nInstall with:\npip install pyserial")
            return

        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("📡 pXRF Analyzer – Live Import")
        self.window.geometry("780x680")
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

        # ── Connection Panel ───────────────────────────────────────
        conn_frame = ttk.LabelFrame(self.window, text="Device Connection", padding=12)
        conn_frame.pack(fill="x", padx=12, pady=(12, 6))

        ttk.Label(conn_frame, text="Serial Port:").pack(side="left", padx=(0, 8))

        self.port_var = tk.StringVar()
        ports = self.get_available_ports()
        self.port_combo = ttk.Combobox(conn_frame, textvariable=self.port_var,
                                      values=ports, width=22, state="readonly")
        self.port_combo.pack(side="left", padx=6)
        if ports:
            self.port_combo.current(0)

        ttk.Button(conn_frame, text="↻ Refresh Ports", command=self.refresh_ports).pack(side="left", padx=6)

        ttk.Button(conn_frame, text="🔌 Connect", command=self.connect_device).pack(side="left", padx=6)
        ttk.Button(conn_frame, text="⏹ Disconnect", command=self.disconnect_device).pack(side="left", padx=6)

        self.status_label = ttk.Label(conn_frame, text="● Disconnected", foreground="red", font=("Arial", 10, "bold"))
        self.status_label.pack(side="right", padx=12)

        # ── Instructions ───────────────────────────────────────────
        instr_frame = ttk.LabelFrame(self.window, text="How to Use", padding=10)
        instr_frame.pack(fill="x", padx=12, pady=6)

        instr_text = """
1. Connect your pXRF device via USB
2. Select the correct COM port above
3. Click "Connect"
4. Take a measurement on your sample
5. Data appears automatically here
6. Click "Add to Current Sample" when ready
        """
        ttk.Label(instr_frame, text=instr_text.strip(), justify="left", font=("Arial", 9)).pack(anchor="w")

        # ── Live Element Display ───────────────────────────────────
        elements_frame = ttk.LabelFrame(self.window, text="Current Measurement (ppm)", padding=10)
        elements_frame.pack(fill="both", expand=True, padx=12, pady=6)

        self.create_element_display(elements_frame)

        # ── Raw Data Log ───────────────────────────────────────────
        raw_frame = ttk.LabelFrame(self.window, text="Raw Device Output", padding=8)
        raw_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.data_text = tk.Text(raw_frame, height=8, font=("Consolas", 9), wrap="word")
        self.data_text.pack(fill="both", expand=True)
        scrollbar = ttk.Scrollbar(raw_frame, command=self.data_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.data_text.config(yscrollcommand=scrollbar.set)

        # ── Action Buttons ─────────────────────────────────────────
        btn_frame = ttk.Frame(self.window)
        btn_frame.pack(fill="x", padx=12, pady=12)

        ttk.Button(btn_frame, text="💾 Add to Current Sample",
                  command=self.add_to_sample,
                  style="Accent.TButton").pack(side="left", padx=8)

        ttk.Button(btn_frame, text="🧹 Clear Display",
                  command=self.clear_display).pack(side="left", padx=8)

        ttk.Button(btn_frame, text="✖ Close Window",
                  command=self.on_close).pack(side="right", padx=8)

    def create_element_display(self, parent):
        """Grid of common elements with live value labels"""
        elements = [
            'Zr', 'Nb', 'Ti', 'Ba', 'Rb', 'Sr',
            'Cr', 'Ni', 'V', 'Y', 'La', 'Ce',
            'Fe', 'Mn', 'Ca', 'K', 'Al', 'Si'
        ]

        row, col = 0, 0
        for elem in elements:
            f = ttk.Frame(parent, relief="ridge", borderwidth=1)
            f.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")

            ttk.Label(f, text=elem, font=("Arial", 11, "bold")).pack()
            val_lbl = ttk.Label(f, text="---", font=("Arial", 14))
            val_lbl.pack()
            ttk.Label(f, text="ppm", foreground="gray", font=("Arial", 8)).pack()

            self.element_labels[elem] = val_lbl

            col += 1
            if col >= 6:
                col = 0
                row += 1

        for i in range(6):
            parent.columnconfigure(i, weight=1)

    def get_available_ports(self):
        if not SERIAL_AVAILABLE:
            return []
        return [p.device for p in serial.tools.list_ports.comports()]

    def refresh_ports(self):
        ports = self.get_available_ports()
        self.port_combo['values'] = ports
        if ports:
            self.port_combo.current(0)
            messagebox.showinfo("Ports Updated", f"Found {len(ports)} ports.")
        else:
            messagebox.showwarning("No Ports", "No serial devices detected.")

    def connect_device(self):
        port = self.port_var.get()
        if not port:
            messagebox.showwarning("No Port", "Select a port first.")
            return

        try:
            self.serial_port = serial.Serial(
                port=port,
                baudrate=9600,          # most pXRF default
                timeout=1,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS
            )
            self.connected = True
            self.status_label.config(text=f"● Connected: {port}", foreground="green")

            self.listening = True
            self.listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
            self.listener_thread.start()

            messagebox.showinfo("Connected", f"Listening on {port}")

        except Exception as e:
            messagebox.showerror("Connection Failed", str(e))

    def disconnect_device(self):
        self.listening = False
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.connected = False
        self.status_label.config(text="● Disconnected", foreground="red")
        messagebox.showinfo("Disconnected", "pXRF connection closed.")

    def _listen_loop(self):
        buffer = ""
        while self.listening and self.serial_port and self.serial_port.is_open:
            try:
                if self.serial_port.in_waiting > 0:
                    chunk = self.serial_port.read(self.serial_port.in_waiting)
                    decoded = chunk.decode('utf-8', errors='replace')
                    buffer += decoded

                    if self._looks_like_complete_scan(buffer):
                        self._process_scan(buffer)
                        buffer = ""

                time.sleep(0.08)  # ~12 Hz polling
            except Exception as e:
                print(f"Listener error: {e}")
                time.sleep(1)

    def _looks_like_complete_scan(self, text: str) -> bool:
        # Heuristic: at least 4 element lines or known end marker
        element_matches = len(re.findall(r'[A-Z][a-z]?[:= ]\d', text))
        return element_matches >= 4 or 'END' in text.upper() or 'MEASUREMENT COMPLETE' in text.upper()

    def _process_scan(self, raw_text: str):
        elements = self._parse_with_best_parser(raw_text)

        if elements:
            self.current_elements = elements
            self.window.after(0, self._update_ui_with_elements, elements)
            self.window.after(0, self._update_raw_text, raw_text)

    def _parse_with_best_parser(self, raw_text: str):
        parsers = [
            NitonParser(),
            VantaParser(),
            BrukerTracerParser(),
        ]

        best = {}
        best_count = 0

        for parser in parsers:
            try:
                res = parser.parse(raw_text)
                if len(res) > best_count:
                    best = res
                    best_count = len(res)
            except:
                pass

        # If nothing useful found → fallback regex
        if best_count < 3:
            result = {}
            pattern = r'([A-Z][a-z]?)\s*[:=]?\s*([\d\.,]+)\s*(ppm|%)?'
            for m in re.finditer(pattern, raw_text, re.I):
                elem, val_str, unit = m.groups()
                try:
                    val = float(val_str.replace(',', ''))
                    if unit and '%' in unit.lower():
                        val *= 10000
                    result[f"{elem}_ppm"] = val
                except:
                    pass
            return result

        return best

    def _update_ui_with_elements(self, elements):
        # Reset all
        for lbl in self.element_labels.values():
            lbl.config(text="---", foreground="black")

        # Fill found values
        for key, val in elements.items():
            elem = key.replace('_ppm', '')
            if elem in self.element_labels:
                self.element_labels[elem].config(
                    text=f"{val:.1f}",
                    foreground="#1e88e5",
                    font=("Arial", 14, "bold")
                )

    def _update_raw_text(self, text: str):
        self.data_text.delete("1.0", tk.END)
        self.data_text.insert(tk.END, text.strip())
        self.data_text.see(tk.END)

    def add_to_sample(self):
        if not self.current_elements:
            messagebox.showwarning("No Data", "No measurement available yet.")
            return

        if not hasattr(self.app, 'selected_sample') or not self.app.selected_sample:
            messagebox.showwarning("No Sample", "Select a sample in the main window first.")
            return

        added = 0
        for key, val in self.current_elements.items():
            self.app.selected_sample[key] = val
            added += 1

        self.app.refresh_tree() if hasattr(self.app, 'refresh_tree') else None
        self.app._mark_unsaved_changes() if hasattr(self.app, '_mark_unsaved_changes') else None

        messagebox.showinfo("Success", f"Added {added} element(s) to {self.app.selected_sample.get('Sample_ID', 'current sample')}")

        self.clear_display()

    def clear_display(self):
        self.current_elements = {}
        self._update_ui_with_elements({})
        self.data_text.delete("1.0", tk.END)

    def on_close(self):
        self.disconnect_device()
        if self.window:
            self.window.destroy()

    def test_connection(self):
        ports = self.get_available_ports()
        if ports:
            return True, f"Found {len(ports)} ports:\n" + "\n".join(ports[:5])
        return False, "No serial ports detected."


def register_plugin(app):
    return pXRFAnalyzerPlugin(app)
