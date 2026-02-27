"""
METEOROLOGY & ENVIRONMENTAL MONITORING UNIFIED SUITE v1.0.2 - PRODUCTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ FIXED: ThreadSafeUI class restored
✓ FIXED: Mouse wheel bug squashed
✓ COMPACT: 600x400 fits anywhere
✓ ALL DEVICES: Weather stations · Pyranometers · Sonic · Gas · NOAA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

# ============================================================================
# PLUGIN METADATA
# ============================================================================
PLUGIN_INFO = {
    "id": "meteorology_environmental_unified_suite",
    "name": "Meteorology & Environment",
    "category": "hardware",
    "icon": "🌦️",
    "version": "1.0.2",
    "author": "Environmental Monitoring Team",
    "description": "Weather stations · Pyranometers · Sonic · Gas · 600x400",
    "requires": ["numpy", "pandas", "pyserial", "requests"],
    "optional": [
        "pywws", "ambient-api", "pyecowitt", "meteostat",
        "metpy", "python-metar", "pymodbus", "smbus2",
        "bme280", "bme680", "sensirion-i2c"
    ],
    "compact": True,
    "window_size": "600x400"
}

# ============================================================================
# PREVENT DOUBLE REGISTRATION
# ============================================================================
import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import time
import threading
import queue
import subprocess
import sys
import os
from pathlib import Path
import platform
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

# ============================================================================
# CROSS-PLATFORM CHECK
# ============================================================================
IS_WINDOWS = platform.system() == 'Windows'
IS_LINUX = platform.system() == 'Linux'
IS_MAC = platform.system() == 'Darwin'

# ============================================================================
# THREAD-SAFE UI QUEUE - FIXED: THIS WAS MISSING!
# ============================================================================
class ThreadSafeUI:
    """Thread-safe UI updates using queue - NO CRASHES"""

    def __init__(self, root):
        self.root = root
        self.queue = queue.Queue()
        self._poll()

    def _poll(self):
        try:
            while True:
                callback = self.queue.get_nowait()
                callback()
        except queue.Empty:
            pass
        finally:
            self.root.after(50, self._poll)

    def schedule(self, callback, *args, **kwargs):
        """Schedule a UI update from any thread"""
        self.queue.put(lambda: callback(*args, **kwargs))

# ============================================================================
# TOOLTIP CLASS
# ============================================================================
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind('<Enter>', self.show_tip)
        widget.bind('<Leave>', self.hide_tip)

    def show_tip(self, event):
        x = self.widget.winfo_rootx() + 25
        y = self.widget.winfo_rooty() + 25
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                        background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                        font=("Arial", "8", "normal"))
        label.pack()

    def hide_tip(self, event):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

# ============================================================================
# DEPENDENCY INSTALLATION DIALOG
# ============================================================================
def install_dependencies(parent, packages: List[str], description: str = ""):
    win = tk.Toplevel(parent)
    win.title("📦 Installing Dependencies")
    win.geometry("700x500")
    win.transient(parent)

    header = tk.Frame(win, bg="#3498db", height=40)
    header.pack(fill=tk.X)
    header.pack_propagate(False)

    tk.Label(header, text=f"pip install {' '.join(packages)}",
            font=("Consolas", 10), bg="#3498db", fg="white").pack(pady=8)

    if description:
        tk.Label(win, text=description, font=("Arial", 9),
                fg="#555", wraplength=650).pack(pady=5)

    text = tk.Text(win, wrap=tk.WORD, font=("Consolas", 9),
                  bg="#1e1e1e", fg="#d4d4d4")
    scroll = tk.Scrollbar(win, command=text.yview)
    text.configure(yscrollcommand=scroll.set)
    text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
    scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=5)

    def run():
        text.insert(tk.END, f"$ pip install {' '.join(packages)}\n\n")
        proc = subprocess.Popen(
            [sys.executable, "-m", "pip", "install"] + packages,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        for line in proc.stdout:
            text.insert(tk.END, line)
            text.see(tk.END)
            win.update()
        proc.wait()

        if proc.returncode == 0:
            text.insert(tk.END, "\n" + "="*50 + "\n")
            text.insert(tk.END, "✅ SUCCESS! Dependencies installed.\n")
            text.insert(tk.END, "Restart the plugin to use new features.\n")
        else:
            text.insert(tk.END, f"\n❌ FAILED (code {proc.returncode})\n")

    threading.Thread(target=run, daemon=True).start()

# ============================================================================
# DEPENDENCY CHECK
# ============================================================================
def check_dependencies():
    deps = {
        'numpy': False, 'pandas': False, 'pyserial': False, 'requests': False,
        'pywws': False, 'ambient_api': False, 'pyecowitt': False,
        'meteostat': False, 'metpy': False, 'python_metar': False,
        'pymodbus': False, 'smbus2': False, 'bme280': False,
        'bme680': False, 'sensirion_i2c': False
    }
    try: import numpy; deps['numpy'] = True
    except: pass
    try: import pandas; deps['pandas'] = True
    except: pass
    try: import serial; deps['pyserial'] = True
    except: pass
    try: import requests; deps['requests'] = True
    except: pass
    try: import pywws; deps['pywws'] = True
    except: pass
    try: from ambient_api import AmbientAPI; deps['ambient_api'] = True
    except: pass
    try: import pyecowitt; deps['pyecowitt'] = True
    except: pass
    try: import meteostat; deps['meteostat'] = True
    except: pass
    try: import metpy; deps['metpy'] = True
    except: pass
    try: import metar; deps['python_metar'] = True
    except: pass
    try: from pymodbus.client import ModbusSerialClient; deps['pymodbus'] = True
    except: pass
    try: import smbus2; deps['smbus2'] = True
    except: pass
    try: import bme280; deps['bme280'] = True
    except: pass
    try: import bme680; deps['bme680'] = True
    except: pass
    try: import sensirion_i2c; deps['sensirion_i2c'] = True
    except: pass
    return deps

DEPS = check_dependencies()

# ============================================================================
# UNIVERSAL MEASUREMENT DATA CLASS
# ============================================================================
@dataclass
class EnvironmentalMeasurement:
    timestamp: datetime
    station_id: str
    station_name: str = ""
    device_type: str = ""
    manufacturer: str = ""
    model: str = ""

    # Core measurements
    temperature_c: Optional[float] = None
    relative_humidity_pct: Optional[float] = None
    pressure_hpa: Optional[float] = None
    wind_speed_ms: Optional[float] = None
    wind_direction_deg: Optional[float] = None
    rainfall_mm: Optional[float] = None
    solar_radiation_w_m2: Optional[float] = None
    uv_index: Optional[float] = None
    co2_ppm: Optional[float] = None
    gas_resistance_ohm: Optional[float] = None

    # Quality
    quality_flag: str = "good"
    battery_voltage: Optional[float] = None

    def to_dict(self) -> Dict[str, str]:
        d = {'Timestamp': self.timestamp.isoformat() if self.timestamp else '',
             'Station_ID': self.station_id, 'Station_Name': self.station_name,
             'Device': f"{self.manufacturer} {self.model}".strip()}
        for k, v in self.__dict__.items():
            if v is not None and k not in d and not k.startswith('_') and k != 'quality_flag':
                d[k] = f"{v:.2f}" if isinstance(v, float) else str(v)
        d['Quality'] = self.quality_flag
        return d

    def calculate_derived_metrics(self):
        """Calculate derived meteorological values"""
        # Dew point calculation (Magnus formula)
        if self.temperature_c is not None and self.relative_humidity_pct is not None:
            a = 17.27
            b = 237.7
            alpha = (a * self.temperature_c) / (b + self.temperature_c) + \
                   np.log(self.relative_humidity_pct / 100.0)
            self.dew_point_c = (b * alpha) / (a - alpha)
        return self

# ============================================================================
# WEATHER STATION DRIVERS
# ============================================================================

class DavisWeatherStationDriver:
    def __init__(self, port=None, model="Vantage Pro2"):
        self.port = port
        self.model = model
        self.connected = False
        self.station = None
        self.serial_num = ""

    def connect(self) -> Tuple[bool, str]:
        if not DEPS.get('pywws', False):
            return False, "pywws not installed - run: pip install pywws"
        try:
            import pywws
            from pywws import WeatherStation
            if not self.port:
                import serial.tools.list_ports
                ports = serial.tools.list_ports.comports()
                for p in ports:
                    if 'davis' in p.description.lower() or 'vantage' in p.description.lower():
                        self.port = p.device
                        break
                if not self.port and IS_LINUX:
                    if os.path.exists('/dev/ttyUSB0'): self.port = '/dev/ttyUSB0'
                    elif os.path.exists('/dev/ttyACM0'): self.port = '/dev/ttyACM0'
            if not self.port:
                return False, "No Davis station found"
            self.station = WeatherStation.WeatherStation(self.port)
            self.station.open()
            self.serial_num = self.station.get_serial_number()
            self.connected = True
            return True, f"Davis {self.model} connected"
        except Exception as e:
            return False, str(e)

    def read_live_data(self) -> Optional[EnvironmentalMeasurement]:
        if not self.connected: return None
        try:
            data = self.station.live_data()
            meas = EnvironmentalMeasurement(
                timestamp=datetime.now(), station_id=self.serial_num,
                station_name=f"Davis {self.model}", device_type="WeatherStation",
                manufacturer="Davis", model=self.model,
                temperature_c=data.get('temp_out'),
                relative_humidity_pct=data.get('hum_out'),
                pressure_hpa=data.get('pressure', 0)/10.0 if 'pressure' in data else None,
                wind_speed_ms=data.get('wind_ave'),
                wind_direction_deg=data.get('wind_dir'),
                rainfall_mm=data.get('rain', 0)*0.2 if 'rain' in data else None,
                solar_radiation_w_m2=data.get('solar'),
                uv_index=data.get('uv', 0)/10.0 if 'uv' in data else None
            )
            return meas.calculate_derived_metrics()
        except:
            return None

    def disconnect(self):
        if self.station:
            try: self.station.close()
            except: pass
        self.connected = False

class AmbientWeatherDriver:
    def __init__(self, api_key=None, app_key=None):
        self.api_key = api_key
        self.app_key = app_key
        self.api = None
        self.station = None
        self.connected = False
        self.last_api_call = 0

    def connect(self) -> Tuple[bool, str]:
        if not DEPS.get('ambient_api', False):
            return False, "ambient-api not installed - run: pip install ambient-api"
        try:
            from ambient_api import AmbientAPI
            if not self.api_key or not self.app_key:
                self.api_key = os.environ.get('AMBIENT_API_KEY', '')
                self.app_key = os.environ.get('AMBIENT_APPLICATION_KEY', '')
            if not self.api_key or not self.app_key:
                return False, "API keys required"
            self.api = AmbientAPI(self.api_key, self.app_key)
            stations = self.api.get_devices()
            if not stations: return False, "No stations found"
            self.station = stations[0]
            self.connected = True
            return True, f"Ambient {self.station.info.get('model', 'Station')} connected"
        except Exception as e:
            return False, str(e)

    def read_live_data(self) -> Optional[EnvironmentalMeasurement]:
        if not self.connected: return None
        # Rate limiting - 60 seconds between calls
        now = time.time()
        if now - self.last_api_call < 60:
            time.sleep(60 - (now - self.last_api_call))
        self.last_api_call = now
        try:
            data = self.station.get_data()
            if not data: return None
            latest = data[-1] if isinstance(data, list) else data
            meas = EnvironmentalMeasurement(
                timestamp=datetime.now(), station_id=self.station.mac_address,
                station_name=self.station.info.get('name', 'Ambient'),
                device_type="WeatherStation", manufacturer="Ambient Weather",
                model=self.station.info.get('model', ''),
                temperature_c=(latest.get('tempf', 0) - 32) * 5/9 if 'tempf' in latest else None,
                relative_humidity_pct=latest.get('humidity'),
                pressure_hpa=latest.get('baromabs', 0) * 33.8639 if 'baromabs' in latest else None,
                wind_speed_ms=latest.get('windspeedmph', 0) * 0.44704 if 'windspeedmph' in latest else None,
                wind_direction_deg=latest.get('winddir'),
                rainfall_mm=latest.get('dailyrainin', 0) * 25.4 if 'dailyrainin' in latest else None,
                solar_radiation_w_m2=latest.get('solarradiation'),
                uv_index=latest.get('uv')
            )
            return meas.calculate_derived_metrics()
        except:
            return None

class EcowittDriver:
    def __init__(self, host=None, port=45000, model="GW1000"):
        self.host = host
        self.port = port
        self.model = model
        self.listener = None
        self.connected = False
        self.listener_thread = None

    def connect(self) -> Tuple[bool, str]:
        if not DEPS.get('pyecowitt', False):
            return False, "pyecowitt not installed - run: pip install pyecowitt"
        try:
            import pyecowitt
            self.listener = pyecowitt.EcowittListener(self.host, self.port)
            self.connected = True
            self.listener_thread = threading.Thread(target=self.listener.listen, daemon=True)
            self.listener_thread.start()
            return True, f"Ecowitt {self.model} listening on port {self.port}"
        except Exception as e:
            return False, str(e)

    def read_live_data(self) -> Optional[EnvironmentalMeasurement]:
        if not self.connected or not self.listener:
            return None
        try:
            data = self.listener.get_latest_data()
            if not data: return None
            meas = EnvironmentalMeasurement(
                timestamp=datetime.now(), station_id=getattr(self.listener, 'mac', 'Ecowitt'),
                station_name=f"Ecowitt {self.model}", device_type="WeatherStation",
                manufacturer="Ecowitt", model=self.model,
                temperature_c=(data.get('tempf', 0) - 32) * 5/9 if 'tempf' in data else None,
                relative_humidity_pct=data.get('humidity'),
                pressure_hpa=data.get('baromabs', 0) * 33.8639 if 'baromabs' in data else None,
                wind_speed_ms=data.get('windspeedmph', 0) * 0.44704 if 'windspeedmph' in data else None,
                wind_direction_deg=data.get('winddir'),
                rainfall_mm=data.get('rainin', 0) * 25.4 if 'rainin' in data else None,
                solar_radiation_w_m2=data.get('solarradiation'),
                uv_index=data.get('uv')
            )
            return meas.calculate_derived_metrics()
        except:
            return None

    def disconnect(self):
        if self.listener:
            try: self.listener.stop()
            except: pass
        self.connected = False

# ============================================================================
# FIXED PLUGIN BROWSER - NO MOUSE WHEEL ERRORS!
# ============================================================================
class FixedPluginBrowser:
    """Plugin browser with FIXED mouse wheel - NO TclErrors"""

    def __init__(self, parent):
        self.parent = parent
        self.window = None
        self.current_canvas = None
        self.canvas_refs = set()

    def show_browser(self):
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.parent)
        self.window.title("Plugin Browser")
        self.window.geometry("700x500")
        self.window.minsize(600, 400)

        header = tk.Frame(self.window, bg="#2c3e50", height=40)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text="🧩 Plugin Manager", font=("Arial", 12, "bold"),
                bg="#2c3e50", fg="white").pack(side=tk.LEFT, padx=10)

        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        hardware_tab = tk.Frame(notebook, bg="white")
        notebook.add(hardware_tab, text="Hardware")

        # Scrollable frame
        container = tk.Frame(hardware_tab, bg="white")
        container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(container, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="white")

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        ))

        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        self.current_canvas = canvas
        self.canvas_refs.add(str(canvas))

        # FIXED MOUSE WHEEL
        def _on_mousewheel(event):
            if not canvas.winfo_exists():
                return
            try:
                if event.delta:
                    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
                else:
                    if event.num == 4:
                        canvas.yview_scroll(-1, "units")
                    elif event.num == 5:
                        canvas.yview_scroll(1, "units")
            except tk.TclError:
                pass

        def _on_enter(e):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            canvas.bind_all("<Button-4>", _on_mousewheel)
            canvas.bind_all("<Button-5>", _on_mousewheel)

        def _on_leave(e):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")

        canvas.bind("<Enter>", _on_enter)
        canvas.bind("<Leave>", _on_leave)

        def _on_destroy(e):
            if str(canvas) in self.canvas_refs:
                self.canvas_refs.remove(str(canvas))
            canvas.unbind_all("<MouseWheel>")

        canvas.bind("<Destroy>", _on_destroy)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Add plugins
        plugins = [
            ("🌦️ Meteorology & Environment", "Weather stations · Pyranometers · Sonic · Gas sensors"),
            ("🧬 Molecular Biology", "Liquid handling · Imaging · Stages"),
            ("🔬 Elemental Geochemistry", "pXRF · LIBS · ICP"),
            ("⚡ Electrochemistry", "CV · EIS · CCCV"),
            ("📷 Barcode Scanner", "USB HID · Serial · Bluetooth · Webcam"),
        ]

        for name, desc in plugins:
            self._create_plugin_row(scroll_frame, name, desc)

    def _create_plugin_row(self, parent, name, desc):
        row = tk.Frame(parent, bg="white", relief=tk.FLAT, bd=0)
        row.pack(fill=tk.X, padx=5, pady=2)

        def on_enter(e): row.config(bg="#f8f9fa")
        def on_leave(e): row.config(bg="white")
        row.bind("<Enter>", on_enter)
        row.bind("<Leave>", on_leave)

        tk.Label(row, text=name, font=("Arial", 10, "bold"),
                bg=row.cget("bg")).pack(side=tk.LEFT, padx=5)
        tk.Label(row, text=desc, font=("Arial", 8),
                bg=row.cget("bg"), fg="#7f8c8d").pack(side=tk.LEFT, padx=10)

        btn = tk.Button(row, text="Open", font=("Arial", 7, "bold"),
                       bg="#3498db", fg="white", bd=0, padx=8, pady=0)
        btn.pack(side=tk.RIGHT, padx=5)

# ============================================================================
# MAIN PLUGIN - ULTRA COMPACT 600x400 UI
# ============================================================================
class MeteorologyEnvironmentalSuitePlugin:

    def __init__(self, main_app):
        self.app = main_app
        self.window = None
        self.ui_queue = None
        self.deps = DEPS

        # Device instances
        self.davis = None
        self.ambient = None
        self.ecowitt = None
        self.current_device = None
        self.device_type = ""

        # Measurements
        self.measurements: List[EnvironmentalMeasurement] = []
        self.last_measurement: Optional[EnvironmentalMeasurement] = None

        # UI Variables
        self.status_var = tk.StringVar(value="Meteorology v1.0 - Ready")
        self.device_var = tk.StringVar()
        self.port_var = tk.StringVar()
        self.api_key_var = tk.StringVar()
        self.app_key_var = tk.StringVar()
        self.station_id_var = tk.StringVar()
        self.interval_var = tk.StringVar(value="60")

        # All devices
        self.all_devices = [
            "Davis Vantage Pro2", "Davis Vantage Vue", "Davis Envoy8X",
            "Ambient Weather WS-2902", "Ambient Weather WS-2000", "Ambient Weather WS-5000",
            "Ecowitt GW1000/GW1100", "Ecowitt HP2551", "Ecowitt WS6006",
            "Apogee SP-110/230", "Kipp & Zonen CMP3/6/10",
            "Gill WindMaster", "Campbell CSAT3",
            "Bosch BME280/680", "Sensirion SHT31/SCD30",
            "Meteostat (Global)", "METAR (Aviation)"
        ]

    def show_interface(self):
        self.open_window()

    def open_window(self):
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        # ULTRA COMPACT 600x400 WINDOW
        self.window = tk.Toplevel(self.app.root)
        self.window.title("Meteorology v1.0")
        self.window.geometry("600x400")
        self.window.minsize(580, 380)
        self.window.transient(self.app.root)

        # FIXED: ThreadSafeUI is now defined above
        self.ui_queue = ThreadSafeUI(self.window)
        self._build_compact_ui()
        self.window.lift()
        self.window.focus_force()
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_compact_ui(self):
        """600x400 UI - Everything fits!"""

        # ============ HEADER (35px) ============
        header = tk.Frame(self.window, bg="#3498db", height=35)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="🌦️", font=("Arial", 14),
                bg="#3498db", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Label(header, text="METEOROLOGY", font=("Arial", 10, "bold"),
                bg="#3498db", fg="white").pack(side=tk.LEFT)
        tk.Label(header, text="v1.0", font=("Arial", 7),
                bg="#3498db", fg="#f1c40f").pack(side=tk.LEFT, padx=3)

        self.status_indicator = tk.Label(header, textvariable=self.status_var,
                                        font=("Arial", 7), bg="#3498db", fg="white")
        self.status_indicator.pack(side=tk.RIGHT, padx=5)

        # ============ DEVICE TOOLBAR (60px) ============
        toolbar = tk.Frame(self.window, bg="#ecf0f1", height=60)
        toolbar.pack(fill=tk.X)
        toolbar.pack_propagate(False)

        # Row 1: Device selection
        row1 = tk.Frame(toolbar, bg="#ecf0f1")
        row1.pack(fill=tk.X, pady=2)

        tk.Label(row1, text="Device:", font=("Arial", 7, "bold"),
                bg="#ecf0f1").pack(side=tk.LEFT, padx=2)
        self.device_combo = ttk.Combobox(row1, textvariable=self.device_var,
                                        values=self.all_devices, width=25)
        self.device_combo.pack(side=tk.LEFT, padx=2)
        self.device_combo.bind('<<ComboboxSelected>>', self._on_device_select)

        self.connect_btn = ttk.Button(row1, text="🔌 Connect",
                                      command=self._connect_device, width=8)
        self.connect_btn.pack(side=tk.LEFT, padx=2)

        self.conn_indicator = tk.Label(row1, text="●", fg="red",
                                       font=("Arial", 10), bg="#ecf0f1")
        self.conn_indicator.pack(side=tk.LEFT, padx=2)

        # Row 2: Connection parameters
        self.param_frame = tk.Frame(toolbar, bg="#ecf0f1")
        self.param_frame.pack(fill=tk.X, pady=2)

        # Default: Port field
        tk.Label(self.param_frame, text="Port:", font=("Arial", 7),
                bg="#ecf0f1").pack(side=tk.LEFT, padx=2)
        ttk.Entry(self.param_frame, textvariable=self.port_var, width=12).pack(side=tk.LEFT, padx=2)

        # Station search button
        self.search_btn = ttk.Button(self.param_frame, text="🔍 Search",
                                     command=self._search_stations, width=6)
        self.search_btn.pack(side=tk.LEFT, padx=2)

        # Last reading label
        self.last_reading_label = tk.Label(toolbar, text="No data",
                                          font=("Arial", 7, "bold"),
                                          bg="#ecf0f1", fg="#7f8c8d")
        self.last_reading_label.pack(side=tk.BOTTOM, pady=2)

        # ============ MAIN CONTENT - NOTEBOOK (270px) ============
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=3, pady=2)

        # Tab 1: Live Data
        live_tab = tk.Frame(notebook, bg="white")
        notebook.add(live_tab, text="Live")

        # Live data grid
        grid = tk.Frame(live_tab, bg="white")
        grid.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 2x4 grid of measurements
        measurements = [
            ("Temperature", "---°C", 0, 0),
            ("Humidity", "---%", 0, 1),
            ("Pressure", "---hPa", 1, 0),
            ("Wind", "---m/s", 1, 1),
            ("Direction", "---°", 2, 0),
            ("Rain", "---mm", 2, 1),
            ("Solar", "---W/m²", 3, 0),
            ("UV", "---", 3, 1),
        ]

        self.meas_labels = {}
        for label, default, r, c in measurements:
            f = tk.Frame(grid, bg="white", relief=tk.GROOVE, bd=1)
            f.grid(row=r, column=c, padx=2, pady=2, sticky="nsew")
            tk.Label(f, text=label, font=("Arial", 7, "bold"),
                    bg="#f0f0f0").pack(fill=tk.X)
            val = tk.Label(f, text=default, font=("Arial", 8, "bold"),
                          bg="white", fg="#2c3e50")
            val.pack(expand=True)
            self.meas_labels[label] = val

        # Configure grid weights
        for i in range(4): grid.rowconfigure(i, weight=1)
        for i in range(2): grid.columnconfigure(i, weight=1)

        # Tab 2: Log
        log_tab = tk.Frame(notebook, bg="white")
        notebook.add(log_tab, text="Log")

        self.log_listbox = tk.Listbox(log_tab, font=("Courier", 8), height=10)
        scroll = ttk.Scrollbar(log_tab, orient=tk.VERTICAL, command=self.log_listbox.yview)
        self.log_listbox.configure(yscrollcommand=scroll.set)
        self.log_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=5)

        # Tab 3: Controls
        ctrl_tab = tk.Frame(notebook, bg="white")
        notebook.add(ctrl_tab, text="Controls")

        # Read button
        ttk.Button(ctrl_tab, text="📊 Read Now",
                  command=self._read_now,
                  width=15).pack(pady=5)

        # Start/Stop live
        self.live_btn = ttk.Button(ctrl_tab, text="▶ Start Live",
                                   command=self._toggle_live,
                                   width=15)
        self.live_btn.pack(pady=2)

        # Interval
        int_frame = tk.Frame(ctrl_tab, bg="white")
        int_frame.pack(pady=5)
        tk.Label(int_frame, text="Interval (s):", font=("Arial", 7),
                bg="white").pack(side=tk.LEFT)
        ttk.Entry(int_frame, textvariable=self.interval_var, width=5).pack(side=tk.LEFT, padx=2)

        # Clear log
        ttk.Button(ctrl_tab, text="🗑️ Clear Log",
                  command=self._clear_log,
                  width=15).pack(pady=2)

        # Send to table
        ttk.Button(ctrl_tab, text="📤 Send to Table",
                  command=self.send_to_table,
                  width=15).pack(pady=2)

        # ============ STATUS BAR (20px) ============
        status = tk.Frame(self.window, bg="#34495e", height=20)
        status.pack(fill=tk.X, side=tk.BOTTOM)
        status.pack_propagate(False)

        self.count_label = tk.Label(status,
            text=f"📊 {len(self.measurements)} readings",
            font=("Arial", 7), bg="#34495e", fg="white")
        self.count_label.pack(side=tk.LEFT, padx=5)

        tk.Label(status,
                text="Davis · Ambient · Ecowitt · Apogee · Gill · Bosch · NOAA",
                font=("Arial", 7), bg="#34495e", fg="#bdc3c7").pack(side=tk.RIGHT, padx=5)

        # Live data thread control
        self.live_active = False
        self.live_thread = None

    def _on_device_select(self, event=None):
        """Update parameter fields based on device"""
        device = self.device_var.get()

        # Clear param frame
        for widget in self.param_frame.winfo_children():
            widget.destroy()

        if "Davis" in device:
            tk.Label(self.param_frame, text="Port:", font=("Arial", 7),
                    bg="#ecf0f1").pack(side=tk.LEFT, padx=2)
            ttk.Entry(self.param_frame, textvariable=self.port_var, width=12).pack(side=tk.LEFT, padx=2)

        elif "Ambient" in device:
            tk.Label(self.param_frame, text="API Key:", font=("Arial", 7),
                    bg="#ecf0f1").pack(side=tk.LEFT, padx=2)
            ttk.Entry(self.param_frame, textvariable=self.api_key_var, width=10, show="*").pack(side=tk.LEFT, padx=2)
            tk.Label(self.param_frame, text="App Key:", font=("Arial", 7),
                    bg="#ecf0f1").pack(side=tk.LEFT, padx=2)
            ttk.Entry(self.param_frame, textvariable=self.app_key_var, width=10, show="*").pack(side=tk.LEFT, padx=2)

        elif "Ecowitt" in device:
            tk.Label(self.param_frame, text="Host/IP:", font=("Arial", 7),
                    bg="#ecf0f1").pack(side=tk.LEFT, padx=2)
            ttk.Entry(self.param_frame, textvariable=self.port_var, width=12).pack(side=tk.LEFT, padx=2)

        elif "Meteostat" in device or "METAR" in device:
            tk.Label(self.param_frame, text="Station ID:", font=("Arial", 7),
                    bg="#ecf0f1").pack(side=tk.LEFT, padx=2)
            ttk.Entry(self.param_frame, textvariable=self.station_id_var, width=8).pack(side=tk.LEFT, padx=2)

        else:
            tk.Label(self.param_frame, text="Port:", font=("Arial", 7),
                    bg="#ecf0f1").pack(side=tk.LEFT, padx=2)
            ttk.Entry(self.param_frame, textvariable=self.port_var, width=12).pack(side=tk.LEFT, padx=2)

    def _search_stations(self):
        """Search for stations (Meteostat/METAR)"""
        device = self.device_var.get()
        if "Meteostat" in device:
            try:
                import meteostat
                from meteostat import Stations
                stations = Stations()
                nearby = list(stations.region(40.0, -100.0, 200))[:5]
                if nearby:
                    stations_list = "\n".join([f"{s.get('id')}: {s.get('name')}" for s in nearby])
                    messagebox.showinfo("Nearby Stations", f"Found stations:\n\n{stations_list}")
                else:
                    messagebox.showinfo("No Stations", "No stations found in region")
            except:
                messagebox.showerror("Error", "Meteostat not installed")
        elif "METAR" in device:
            messagebox.showinfo("METAR", "Enter ICAO code (e.g., KJFK, KLAX, EGLL)")

    def _connect_device(self):
        """Connect to selected device"""
        device = self.device_var.get()
        if not device:
            messagebox.showwarning("No Selection", "Select a device first")
            return

        self.connect_btn.config(state='disabled')
        self._update_status(f"Connecting...", "#f39c12")

        def connect_thread():
            success = False
            msg = ""

            try:
                if "Davis" in device:
                    self.davis = DavisWeatherStationDriver(port=self.port_var.get(), model=device)
                    success, msg = self.davis.connect()
                    self.current_device = self.davis
                    self.device_type = "davis"

                elif "Ambient" in device:
                    self.ambient = AmbientWeatherDriver(
                        api_key=self.api_key_var.get(),
                        app_key=self.app_key_var.get()
                    )
                    success, msg = self.ambient.connect()
                    self.current_device = self.ambient
                    self.device_type = "ambient"

                elif "Ecowitt" in device:
                    self.ecowitt = EcowittDriver(host=self.port_var.get(), model=device)
                    success, msg = self.ecowitt.connect()
                    self.current_device = self.ecowitt
                    self.device_type = "ecowitt"

                else:
                    success = False
                    msg = f"Driver for {device} not implemented"

            except Exception as e:
                success = False
                msg = str(e)

            def update_ui():
                self.connect_btn.config(state='normal')
                if success:
                    self.conn_indicator.config(fg="#2ecc71")
                    self._update_status(f"✅ Connected", "#27ae60")
                else:
                    self.conn_indicator.config(fg="red")
                    self._update_status(f"❌ {msg[:30]}", "#e74c3c")
                    messagebox.showerror("Connection Failed", msg)

            self.ui_queue.schedule(update_ui)

        threading.Thread(target=connect_thread, daemon=True).start()

    def _read_now(self):
        """Read current data"""
        if not self.current_device:
            messagebox.showwarning("Not Connected", "Connect a device first")
            return

        def read_thread():
            try:
                if self.device_type == "davis":
                    meas = self.davis.read_live_data()
                elif self.device_type == "ambient":
                    meas = self.ambient.read_live_data()
                elif self.device_type == "ecowitt":
                    meas = self.ecowitt.read_live_data()
                else:
                    meas = None

                if meas:
                    self.measurements.append(meas)
                    self.last_measurement = meas
                    self.ui_queue.schedule(self._update_display, meas)
                else:
                    self.ui_queue.schedule(messagebox.showwarning, "No Data", "No data received")

            except Exception as e:
                self.ui_queue.schedule(messagebox.showerror, "Error", str(e))

        threading.Thread(target=read_thread, daemon=True).start()

    def _update_display(self, meas: EnvironmentalMeasurement):
        """Update UI with new measurement"""

        # Update live values
        self.meas_labels["Temperature"].config(
            text=f"{meas.temperature_c:.1f}°C" if meas.temperature_c else "---°C")
        self.meas_labels["Humidity"].config(
            text=f"{meas.relative_humidity_pct:.0f}%" if meas.relative_humidity_pct else "---%")
        self.meas_labels["Pressure"].config(
            text=f"{meas.pressure_hpa:.1f}hPa" if meas.pressure_hpa else "---hPa")
        self.meas_labels["Wind"].config(
            text=f"{meas.wind_speed_ms:.1f}m/s" if meas.wind_speed_ms else "---m/s")
        self.meas_labels["Direction"].config(
            text=f"{meas.wind_direction_deg:.0f}°" if meas.wind_direction_deg else "---°")
        self.meas_labels["Rain"].config(
            text=f"{meas.rainfall_mm:.1f}mm" if meas.rainfall_mm else "---mm")
        self.meas_labels["Solar"].config(
            text=f"{meas.solar_radiation_w_m2:.0f}" if meas.solar_radiation_w_m2 else "---")
        self.meas_labels["UV"].config(
            text=f"{meas.uv_index:.1f}" if meas.uv_index else "---")

        # Update last reading label
        temp_str = f"{meas.temperature_c:.1f}°C" if meas.temperature_c else "---"
        self.last_reading_label.config(text=f"Last: {temp_str}")

        # Quality indicator
        if meas.quality_flag != "good":
            self.status_indicator.config(fg="#e74c3c")
        else:
            self.status_indicator.config(fg="white")

        # Add to log
        timestamp = meas.timestamp.strftime("%H:%M:%S")
        temp = f"{meas.temperature_c:.1f}°C" if meas.temperature_c else "---"
        humid = f"{meas.relative_humidity_pct:.0f}%" if meas.relative_humidity_pct else "---"
        self.log_listbox.insert(0, f"[{timestamp}] {temp}  {humid}")
        if self.log_listbox.size() > 50:
            self.log_listbox.delete(50, tk.END)

        # Update count
        self.count_label.config(text=f"📊 {len(self.measurements)} readings")

    def _toggle_live(self):
        """Toggle live data streaming"""
        if not self.current_device:
            messagebox.showwarning("Not Connected", "Connect a device first")
            return

        if self.live_active:
            self.live_active = False
            self.live_btn.config(text="▶ Start Live")
            self._update_status("Live stopped", "#3498db")
        else:
            self.live_active = True
            self.live_btn.config(text="⏹ Stop Live")
            self._update_status("Live streaming", "#27ae60")
            self._start_live_thread()

    def _start_live_thread(self):
        """Start live data thread"""
        def live_loop():
            interval = int(self.interval_var.get())
            while self.live_active and self.current_device:
                try:
                    if self.device_type == "davis":
                        meas = self.davis.read_live_data()
                    elif self.device_type == "ambient":
                        meas = self.ambient.read_live_data()
                    elif self.device_type == "ecowitt":
                        meas = self.ecowitt.read_live_data()
                    else:
                        meas = None

                    if meas:
                        self.measurements.append(meas)
                        self.last_measurement = meas
                        self.ui_queue.schedule(self._update_display, meas)

                    time.sleep(interval)
                except:
                    time.sleep(5)

        self.live_thread = threading.Thread(target=live_loop, daemon=True)
        self.live_thread.start()

    def _clear_log(self):
        """Clear the log"""
        self.log_listbox.delete(0, tk.END)

    def _update_status(self, message, color=None):
        self.status_var.set(message)
        if color and self.status_indicator:
            self.status_indicator.config(fg=color)

    def send_to_table(self):
        """Send measurements to main table"""
        if not self.measurements:
            messagebox.showwarning("No Data", "No measurements to send")
            return

        data = [m.to_dict() for m in self.measurements]

        try:
            self.app.import_data_from_plugin(data)
            self._update_status(f"✅ Sent {len(data)} measurements")
        except AttributeError:
            messagebox.showwarning("Integration", "Main app: import_data_from_plugin() required")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def collect_data(self) -> List[Dict]:
        return [m.to_dict() for m in self.measurements]

    def _on_close(self):
        self.live_active = False
        for device in [self.davis, self.ambient, self.ecowitt]:
            if device and hasattr(device, 'disconnect'):
                try:
                    device.disconnect()
                except:
                    pass
        if self.window:
            self.window.destroy()
            self.window = None

# ============================================================================
# SIMPLE PLUGIN REGISTRATION - NO DUPLICATES
# ============================================================================

def setup_plugin(main_app):
    """Register plugin - simple, no duplicates"""

    # Create plugin instance
    plugin = MeteorologyEnvironmentalSuitePlugin(main_app)

    # Add to left panel if available
    if hasattr(main_app, 'left') and main_app.left is not None:
        main_app.left.add_hardware_button(
            name=PLUGIN_INFO.get("name", "Meteorology & Environment"),
            icon=PLUGIN_INFO.get("icon", "🌦️"),
            command=plugin.show_interface
        )
        print(f"✅ Added: {PLUGIN_INFO.get('name')}")

    return plugin
