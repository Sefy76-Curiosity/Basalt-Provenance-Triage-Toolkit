"""
METEOROLOGY & ENVIRONMENTAL MONITORING UNIFIED SUITE v1.3.0 - PRODUCTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ POLISHED: Robust WeatherFlow parsing (obs_air/obs_sky, partial packets)
✓ POLISHED: Fine Offset soil calibration (per-model lookup + user calibration)
✓ POLISHED: Oregon Scientific parsing (weewx-derived, multi-model support)
✓ UI ICONS: Visual indicators for all measurements (🌡️ 💧 🌬️ etc.)
✓ TIMESTAMPS: Per-station last update in selector
✓ STATION PANEL: Connection status, battery, RSSI at a glance
✓ CLOUD: Retry logic + exponential backoff + softwaretype tagging
✓ LOCATION: Indoor/Outdoor/Greenhouse tagging per station
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
    "version": "1.3.0",
    "author": "Environmental Monitoring Team",
    "description": "Multi-station · Soil/Lightning/Gusts · Cloud · Indoor/Outdoor",
    "requires": ["numpy", "pandas", "pyserial", "requests"],
    "optional": [
        "pywws", "ambient-api", "pyecowitt", "meteostat",
        "metpy", "python-metar", "pymodbus", "smbus2",
        "bme280", "bme680", "sensirion-i2c", "pyusb", "hid"
    ],
    "compact": True,
    "window_size": "600x480"
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
import struct
import socket
import json
import requests
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Set

# ============================================================================
# CROSS-PLATFORM CHECK
# ============================================================================
IS_WINDOWS = platform.system() == 'Windows'
IS_LINUX = platform.system() == 'Linux'
IS_MAC = platform.system() == 'Darwin'

# ============================================================================
# THREAD-SAFE UI QUEUE
# ============================================================================
class ThreadSafeUI:
    """Thread-safe UI updates using queue"""

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
        'bme680': False, 'sensirion_i2c': False, 'pyusb': False, 'hid': False
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
    try: import usb.core; deps['pyusb'] = True
    except: pass
    try: import hid; deps['hid'] = True
    except: pass
    return deps

DEPS = check_dependencies()

# ============================================================================
# ENHANCED MEASUREMENT DATA CLASS (with location tagging)
# ============================================================================
@dataclass
class EnvironmentalMeasurement:
    timestamp: datetime
    station_id: str
    station_name: str = ""
    device_type: str = ""
    manufacturer: str = ""
    model: str = ""

    # Location tagging
    location: str = "outdoor"  # "outdoor", "indoor", "greenhouse"

    # Core measurements
    temperature_c: Optional[float] = None
    relative_humidity_pct: Optional[float] = None
    pressure_hpa: Optional[float] = None
    wind_speed_ms: Optional[float] = None
    wind_gust_ms: Optional[float] = None
    wind_direction_deg: Optional[float] = None
    rainfall_mm: Optional[float] = None
    solar_radiation_w_m2: Optional[float] = None
    uv_index: Optional[float] = None

    # Soil and vegetation sensors
    soil_moisture_pct: Optional[float] = None
    soil_temperature_c: Optional[float] = None
    leaf_wetness_pct: Optional[float] = None

    # Lightning detection
    lightning_strike_count: Optional[int] = None
    lightning_distance_km: Optional[float] = None

    # Gas sensors
    co2_ppm: Optional[float] = None
    gas_resistance_ohm: Optional[float] = None
    voc_index: Optional[float] = None
    pm2_5: Optional[float] = None
    pm10: Optional[float] = None

    # Quality
    quality_flag: str = "good"
    battery_voltage: Optional[float] = None
    rssi: Optional[int] = None
    uptime_days: Optional[float] = None

    def to_dict(self) -> Dict[str, str]:
        d = {'Timestamp': self.timestamp.isoformat() if self.timestamp else '',
             'Station_ID': self.station_id, 'Station_Name': self.station_name,
             'Location': self.location, 'Device': f"{self.manufacturer} {self.model}".strip()}
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

        # Heat index (if temperature > 27°C)
        if self.temperature_c is not None and self.temperature_c > 27 and self.relative_humidity_pct is not None:
            Tf = self.temperature_c * 9/5 + 32
            hi_f = -42.379 + 2.04901523*Tf + 10.14333127*self.relative_humidity_pct - 0.22475541*Tf*self.relative_humidity_pct - 6.83783e-3*Tf**2 - 5.481717e-2*self.relative_humidity_pct**2 + 1.22874e-3*Tf**2*self.relative_humidity_pct + 8.5282e-4*Tf*self.relative_humidity_pct**2 - 1.99e-6*Tf**2*self.relative_humidity_pct**2
            self.heat_index_c = (hi_f - 32) * 5/9

        # Wind chill (if temperature < 10°C and wind > 1.34 m/s)
        if (self.temperature_c is not None and self.temperature_c < 10 and
            self.wind_speed_ms is not None and self.wind_speed_ms > 1.34):
            self.wind_chill_c = 13.12 + 0.6215*self.temperature_c - 11.37*self.wind_speed_ms**0.16 + 0.3965*self.temperature_c*self.wind_speed_ms**0.16

        return self

# ============================================================================
# ENHANCED CLOUD UPLOADER (with retry logic + softwaretype)
# ============================================================================
class WeatherUndergroundUploader:
    """Upload data to Weather Underground (PWS) with retry logic"""

    def __init__(self, station_id: str, password: str):
        self.station_id = station_id
        self.password = password
        self.base_url = "https://weatherstation.wunderground.com/weatherstation/updateweatherstation.php"
        self.max_retries = 3
        self.backoff_factor = 2

    def upload(self, meas: EnvironmentalMeasurement) -> Tuple[bool, str]:
        """Upload measurement to WU with retry logic"""
        for attempt in range(self.max_retries):
            try:
                params = {
                    'ID': self.station_id,
                    'PASSWORD': self.password,
                    'dateutc': meas.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'action': 'updateraw',
                    'softwaretype': 'Sefy%20Meteorology%20Suite%20v1.3.0'
                }

                if meas.temperature_c is not None:
                    params['tempf'] = round(meas.temperature_c * 9/5 + 32, 1)
                if meas.relative_humidity_pct is not None:
                    params['humidity'] = round(meas.relative_humidity_pct)
                if meas.pressure_hpa is not None:
                    params['baromin'] = round(meas.pressure_hpa * 0.02953, 3)
                if meas.wind_speed_ms is not None:
                    params['windspeedmph'] = round(meas.wind_speed_ms * 2.23694, 1)
                if meas.wind_gust_ms is not None:
                    params['windgustmph'] = round(meas.wind_gust_ms * 2.23694, 1)
                if meas.wind_direction_deg is not None:
                    params['winddir'] = round(meas.wind_direction_deg)
                if meas.rainfall_mm is not None:
                    params['rainin'] = round(meas.rainfall_mm * 0.0393701, 2)
                if meas.solar_radiation_w_m2 is not None:
                    params['solarradiation'] = round(meas.solar_radiation_w_m2)
                if meas.uv_index is not None:
                    params['UV'] = round(meas.uv_index, 1)

                response = requests.get(self.base_url, params=params, timeout=10)
                if response.status_code == 200 and 'success' in response.text.lower():
                    return True, f"WU uploaded (attempt {attempt+1})"
                else:
                    if attempt < self.max_retries - 1:
                        time.sleep(self.backoff_factor ** attempt)
                    continue

            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.backoff_factor ** attempt)
                else:
                    return False, f"WU failed: {str(e)}"

        return False, "WU upload failed after retries"


class CWOPUploader:
    """Upload to Citizen Weather Observer Program (CWOP/APRS)"""

    def __init__(self, station_id: str, passcode: str, server="cwop.aprs.net", port=14580):
        self.station_id = station_id
        self.passcode = passcode
        self.server = server
        self.port = port
        self.socket = None
        self.max_retries = 3
        self.backoff_factor = 2

    def connect(self) -> bool:
        """Connect to CWOP server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server, self.port))

            login = f"user {self.station_id} pass {self.passcode} vers MeteorologySuite 1.3.0\n"
            self.socket.send(login.encode())

            response = self.socket.recv(1024).decode()
            return '# logresp' in response

        except Exception:
            return False

    def upload(self, meas: EnvironmentalMeasurement) -> Tuple[bool, str]:
        """Upload to CWOP with retry logic"""
        for attempt in range(self.max_retries):
            try:
                if not self.socket:
                    if not self.connect():
                        if attempt < self.max_retries - 1:
                            time.sleep(self.backoff_factor ** attempt)
                            continue
                        return False, "Could not connect to CWOP"

                packet = f"{self.station_id}>APRS,TCPIP*:"
                packet += "@" + meas.timestamp.strftime("%d%H%M") + "z"
                packet += "0000.00N/00000.00W"

                if meas.wind_direction_deg is not None:
                    packet += f"c{int(meas.wind_direction_deg):03d}s"
                if meas.wind_speed_ms is not None:
                    packet += f"{int(meas.wind_speed_ms * 1.94384):03d}"
                if meas.wind_gust_ms is not None:
                    packet += f"g{int(meas.wind_gust_ms * 1.94384):03d}"
                if meas.temperature_c is not None:
                    packet += f"t{int(meas.temperature_c * 9/5 + 32):03d}"
                if meas.rainfall_mm is not None:
                    packet += f"r{int(meas.rainfall_mm * 0.03937 * 100):03d}"
                if meas.pressure_hpa is not None:
                    packet += f"b{int(meas.pressure_hpa * 10):05d}"
                if meas.relative_humidity_pct is not None:
                    packet += f"h{int(meas.relative_humidity_pct):02d}"

                packet += "\n"

                self.socket.send(packet.encode())
                return True, f"CWOP uploaded (attempt {attempt+1})"

            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.backoff_factor ** attempt)
                    self.socket = None
                else:
                    return False, f"CWOP failed: {str(e)}"

        return False, "CWOP upload failed after retries"

    def disconnect(self):
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None


class EcowittCloudUploader:
    """Upload to Ecowitt cloud (for Fine Offset/Ecowitt stations)"""

    def __init__(self, station_mac: str, application_key: str):
        self.station_mac = station_mac
        self.application_key = application_key
        self.base_url = "https://api.ecowitt.net/api/v3/device/real_time"
        self.max_retries = 3
        self.backoff_factor = 2

    def upload(self, meas: EnvironmentalMeasurement) -> Tuple[bool, str]:
        """Upload to Ecowitt cloud with retry logic"""
        for attempt in range(self.max_retries):
            try:
                data = {
                    "station_mac": self.station_mac,
                    "application_key": self.application_key,
                    "data": {
                        "timestamp": int(meas.timestamp.timestamp()),
                        "temp": meas.temperature_c,
                        "humidity": meas.relative_humidity_pct,
                        "pressure": meas.pressure_hpa,
                        "wind_speed": meas.wind_speed_ms,
                        "wind_gust": meas.wind_gust_ms,
                        "wind_direction": meas.wind_direction_deg,
                        "rain": meas.rainfall_mm,
                        "solar": meas.solar_radiation_w_m2,
                        "uv": meas.uv_index,
                        "softwaretype": "Sefy Meteorology Suite v1.3.0"
                    }
                }

                if meas.soil_moisture_pct is not None:
                    data["data"]["soil_moisture"] = meas.soil_moisture_pct
                if meas.soil_temperature_c is not None:
                    data["data"]["soil_temp"] = meas.soil_temperature_c
                if meas.leaf_wetness_pct is not None:
                    data["data"]["leaf_wetness"] = meas.leaf_wetness_pct

                response = requests.post(self.base_url, json=data, timeout=10)
                if response.status_code == 200:
                    return True, f"Ecowitt uploaded (attempt {attempt+1})"
                else:
                    if attempt < self.max_retries - 1:
                        time.sleep(self.backoff_factor ** attempt)
                    continue

            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.backoff_factor ** attempt)
                else:
                    return False, f"Ecowitt failed: {str(e)}"

        return False, "Ecowitt upload failed after retries"

# ============================================================================
# ENHANCED WEATHERFLOW DRIVER (with obs_air/obs_sky and partial packet handling)
# ============================================================================
class WeatherFlowDriver:
    """
    WeatherFlow Smart Weather stations - ENHANCED PARSING
    - Handles obs_air, obs_sky, obs_st separately
    - Partial packet recovery
    - Separate Tempest modules
    """

    def __init__(self, host="0.0.0.0", port=50222, model="Tempest"):
        self.host = host
        self.port = port
        self.model = model
        self.connected = False
        self.socket = None
        self.listener_thread = None
        self.running = False

        # Separate module data
        self.air_data = {}
        self.sky_data = {}
        self.st_data = {}

        self.last_data = None
        self.last_rapid_wind = None
        self.lightning_strikes = []
        self.station_id = f"WF-{model}-{int(time.time())}"
        self.station_name = f"WeatherFlow {model}"
        self.partial_buffer = ""

    def connect(self) -> Tuple[bool, str]:
        """Start UDP listener for WeatherFlow broadcast"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.settimeout(1.0)
            self.socket.bind((self.host, self.port))

            self.connected = True
            self.running = True

            self.listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
            self.listener_thread.start()

            return True, f"WeatherFlow {self.model} listening on UDP {self.port}"

        except Exception as e:
            return False, str(e)

    def _listen_loop(self):
        """Listen for WeatherFlow UDP broadcasts with partial packet handling"""
        while self.running and self.socket:
            try:
                data, addr = self.socket.recvfrom(2048)

                try:
                    message_str = data.decode('utf-8')

                    if message_str.startswith('{') and message_str.endswith('}\n'):
                        message = json.loads(message_str)
                        self._parse_message(message, addr)
                    else:
                        self.partial_buffer += message_str
                        if self.partial_buffer.startswith('{') and '}\n' in self.partial_buffer:
                            complete, remainder = self.partial_buffer.split('}\n', 1)
                            complete += '}'
                            try:
                                message = json.loads(complete)
                                self._parse_message(message, addr)
                            except:
                                pass
                            self.partial_buffer = remainder

                except UnicodeDecodeError:
                    pass

            except socket.timeout:
                continue
            except Exception:
                if self.running:
                    time.sleep(0.1)

    def _parse_message(self, message: dict, addr: tuple):
        """Parse WeatherFlow JSON message with separate module handling"""
        try:
            msg_type = message.get('type')

            if msg_type == 'obs_st':
                data = message.get('obs', [[]])[0]
                if len(data) >= 10:
                    self.st_data = {
                        'timestamp': datetime.now(),
                        'wind_dir': data[1] if len(data) > 1 else None,
                        'wind_speed': data[2] if len(data) > 2 else None,
                        'wind_gust': data[3] if len(data) > 3 else None,
                        'pressure': data[4] if len(data) > 4 else None,
                        'temp': data[5] if len(data) > 5 else None,
                        'humidity': data[6] if len(data) > 6 else None,
                        'lightning_count': data[7] if len(data) > 7 else None,
                        'lightning_dist': data[8] if len(data) > 8 else None
                    }

            elif msg_type == 'obs_air':
                data = message.get('obs', [[]])[0]
                if len(data) >= 5:
                    self.air_data = {
                        'timestamp': datetime.now(),
                        'pressure': data[2] if len(data) > 2 else None,
                        'temp': data[3] if len(data) > 3 else None,
                        'humidity': data[4] if len(data) > 4 else None
                    }

            elif msg_type == 'obs_sky':
                data = message.get('obs', [[]])[0]
                if len(data) >= 10:
                    self.sky_data = {
                        'timestamp': datetime.now(),
                        'illuminance': data[2] if len(data) > 2 else None,
                        'uv': data[3] if len(data) > 3 else None,
                        'wind_dir': data[5] if len(data) > 5 else None,
                        'wind_speed': data[6] if len(data) > 6 else None,
                        'wind_gust': data[7] if len(data) > 7 else None,
                        'solar_rad': data[9] if len(data) > 9 else None
                    }

            elif msg_type == 'rapid_wind':
                data = message.get('ob', [])
                if len(data) >= 3:
                    self.last_rapid_wind = {
                        'speed': data[1],
                        'direction': data[2],
                        'timestamp': datetime.now()
                    }

            elif msg_type == 'evt_strike':
                data = message.get('evt', [])
                if len(data) >= 3:
                    strike = {
                        'timestamp': datetime.now(),
                        'distance_km': data[1],
                        'energy': data[2]
                    }
                    self.lightning_strikes.append(strike)
                    if len(self.lightning_strikes) > 10:
                        self.lightning_strikes.pop(0)

            self._combine_data()

        except Exception as e:
            print(f"WeatherFlow parse error: {e}")

    def _combine_data(self):
        """Combine data from all modules into single measurement"""
        meas = EnvironmentalMeasurement(
            timestamp=datetime.now(),
            station_id=self.station_id,
            station_name=self.station_name,
            device_type="WeatherStation",
            manufacturer="WeatherFlow",
            model=self.model
        )

        if self.st_data:
            meas.temperature_c = self.st_data.get('temp')
            meas.relative_humidity_pct = self.st_data.get('humidity')
            meas.pressure_hpa = self.st_data.get('pressure')
            meas.wind_speed_ms = self.st_data.get('wind_speed')
            meas.wind_gust_ms = self.st_data.get('wind_gust')
            meas.wind_direction_deg = self.st_data.get('wind_dir')
            meas.lightning_strike_count = self.st_data.get('lightning_count')
            meas.lightning_distance_km = self.st_data.get('lightning_dist')
        else:
            if self.air_data:
                meas.temperature_c = self.air_data.get('temp')
                meas.relative_humidity_pct = self.air_data.get('humidity')
                meas.pressure_hpa = self.air_data.get('pressure')

            if self.sky_data:
                meas.wind_speed_ms = self.sky_data.get('wind_speed')
                meas.wind_gust_ms = self.sky_data.get('wind_gust')
                meas.wind_direction_deg = self.sky_data.get('wind_dir')
                meas.solar_radiation_w_m2 = self.sky_data.get('solar_rad')
                meas.uv_index = self.sky_data.get('uv')

        if self.last_rapid_wind:
            if meas.wind_gust_ms is None or self.last_rapid_wind['speed'] > meas.wind_gust_ms:
                meas.wind_gust_ms = self.last_rapid_wind['speed']

        if self.lightning_strikes:
            latest = self.lightning_strikes[-1]
            meas.lightning_distance_km = latest['distance_km']
            meas.lightning_strike_count = len(self.lightning_strikes)

        self.last_data = meas.calculate_derived_metrics()

    def read_live_data(self) -> Optional[EnvironmentalMeasurement]:
        return self.last_data

    def get_rapid_wind(self) -> Optional[Dict]:
        return self.last_rapid_wind

    def get_lightning_strikes(self) -> List[Dict]:
        return self.lightning_strikes

    def disconnect(self):
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        self.connected = False

# ============================================================================
# ENHANCED FINE OFFSET DRIVER (with soil calibration)
# ============================================================================
class FineOffsetDriver:
    """
    Fine Offset Electronics weather stations
    Enhanced with soil moisture calibration per model
    """

    FINE_OFFSET_IDS = [
        (0x1941, 0x8021, "WH1080"),
        (0x1941, 0x8022, "WH2080"),
        (0x1941, 0x8023, "WH3080"),
        (0x1941, 0x8024, "WH4000"),
        (0x1941, 0x8025, "WS1080"),
        (0x10C4, 0xEA60, "CP2102"),
        (0x10C4, 0xEA70, "CP2105"),
        (0x0403, 0x6001, "FT232"),
        (0x0403, 0x6015, "FT231X"),
    ]

    SOIL_CALIBRATION = {
        "WH3080": (0, 200, 0, 100),
        "WH4000": (200, 800, 0, 100),
        "default": (0, 200, 0, 100)
    }

    def __init__(self, port=None, model="WH3080", soil_cal_factor=None):
        self.port = port
        self.model = model
        self.connected = False
        self.serial_conn = None
        self.hid_device = None
        self.station_id = f"FO-{model}-{int(time.time())}"
        self.has_soil_sensors = model in ["WH3080", "WH4000"]
        self.soil_cal_factor = soil_cal_factor

    def _calibrate_soil_moisture(self, raw_value: int) -> Optional[float]:
        """Convert raw soil sensor value to percentage with calibration"""
        if raw_value is None or raw_value == 0xFFFF:
            return None

        cal = self.SOIL_CALIBRATION.get(self.model, self.SOIL_CALIBRATION["default"])
        raw_min, raw_max, pct_min, pct_max = cal

        if self.soil_cal_factor is not None:
            raw_max = raw_max * self.soil_cal_factor

        raw_value = max(raw_min, min(raw_max, raw_value))

        if raw_max == raw_min:
            return 0.0
        pct = pct_min + (pct_max - pct_min) * (raw_value - raw_min) / (raw_max - raw_min)

        return round(pct, 1)

    def connect(self) -> Tuple[bool, str]:
        """Connect to Fine Offset station"""
        try:
            if not self.port or "HID" in self.port:
                try:
                    import hid

                    for vid, pid, name in self.FINE_OFFSET_IDS:
                        try:
                            device = hid.enumerate(vid, pid)
                            if device:
                                self.hid_device = hid.Device(vid, pid)
                                self.model = name if "WH" in name else self.model
                                self.connected = True
                                return True, f"Fine Offset {self.model} connected via HID"
                        except:
                            continue

                except ImportError:
                    pass
                except Exception:
                    pass

            if self.port and ("COM" in self.port or "/dev/" in self.port):
                import serial
                import serial.tools.list_ports

                if not self.port:
                    ports = serial.tools.list_ports.comports()
                    for p in ports:
                        if any(x in p.description.lower() for x in ['cp210', 'silicon', 'fine', 'offset']):
                            self.port = p.device
                            break

                if self.port:
                    self.serial_conn = serial.Serial(
                        port=self.port,
                        baudrate=9600,
                        bytesize=serial.EIGHTBITS,
                        parity=serial.PARITY_NONE,
                        stopbits=serial.STOPBITS_ONE,
                        timeout=2
                    )
                    self.connected = True
                    return True, f"Fine Offset {self.model} connected on {self.port}"

            return False, "No Fine Offset station found"

        except Exception as e:
            return False, str(e)

    def read_live_data(self) -> Optional[EnvironmentalMeasurement]:
        """Read current data from Fine Offset station"""
        if not self.connected:
            return None

        try:
            if self.hid_device:
                self.hid_device.write([0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
                data = self.hid_device.read(64, timeout=5000)

                if data and len(data) >= 32:
                    temp_raw = (data[4] << 8) | data[5]
                    temp_c = (temp_raw - 400) / 10.0 if temp_raw != 0xFFFF else None

                    humid = data[6] if data[6] != 0xFF else None

                    pressure_raw = (data[12] << 8) | data[13]
                    pressure_hpa = pressure_raw / 10.0 if pressure_raw != 0xFFFF else None

                    wind_raw = (data[7] << 8) | data[8]
                    wind_ms = wind_raw / 10.0 if wind_raw != 0xFFFF else None

                    wind_dir_raw = (data[9] << 8) | data[10]
                    wind_dir = wind_dir_raw if wind_dir_raw != 0xFFFF else None

                    rain_raw = (data[14] << 8) | data[15]
                    rain_mm = rain_raw * 0.3 if rain_raw != 0xFFFF else None

                    soil_moisture = None
                    soil_temp = None

                    if self.has_soil_sensors and len(data) >= 32:
                        soil_raw = (data[28] << 8) | data[29]
                        if soil_raw != 0xFFFF:
                            soil_moisture = self._calibrate_soil_moisture(soil_raw)

                        soil_temp_raw = (data[30] << 8) | data[31]
                        if soil_temp_raw != 0xFFFF:
                            soil_temp = (soil_temp_raw - 400) / 10.0

                    meas = EnvironmentalMeasurement(
                        timestamp=datetime.now(),
                        station_id=self.station_id,
                        station_name=f"Fine Offset {self.model}",
                        device_type="WeatherStation",
                        manufacturer="Fine Offset",
                        model=self.model,
                        temperature_c=temp_c,
                        relative_humidity_pct=humid,
                        pressure_hpa=pressure_hpa,
                        wind_speed_ms=wind_ms,
                        wind_direction_deg=wind_dir,
                        rainfall_mm=rain_mm,
                        soil_moisture_pct=soil_moisture,
                        soil_temperature_c=soil_temp
                    )
                    return meas.calculate_derived_metrics()

            elif self.serial_conn:
                self.serial_conn.reset_input_buffer()
                self.serial_conn.write(b'\x01')
                time.sleep(0.5)

                if self.serial_conn.in_waiting >= 16:
                    data = self.serial_conn.read(16)

                    temp_raw = (data[4] << 8) | data[5]
                    temp_c = (temp_raw - 400) / 10.0 if temp_raw != 0xFFFF else None

                    humid = data[6] if data[6] != 0xFF else None

                    meas = EnvironmentalMeasurement(
                        timestamp=datetime.now(),
                        station_id=self.station_id,
                        station_name=f"Fine Offset {self.model}",
                        device_type="WeatherStation",
                        manufacturer="Fine Offset",
                        model=self.model,
                        temperature_c=temp_c,
                        relative_humidity_pct=humid
                    )
                    return meas.calculate_derived_metrics()

            return None

        except Exception as e:
            print(f"Fine Offset read error: {e}")
            return None

    def disconnect(self):
        """Disconnect from station"""
        if self.hid_device:
            try:
                self.hid_device.close()
            except:
                pass
        if self.serial_conn:
            try:
                self.serial_conn.close()
            except:
                pass
        self.connected = False

# ============================================================================
# ENHANCED OREGON SCIENTIFIC DRIVER (weewx-derived parsing)
# ============================================================================
class OregonScientificDriver:
    """
    Oregon Scientific weather stations
    Enhanced with weewx-derived parsing for multiple models
    """

    MESSAGE_TYPES = {
        b'\xD4': {
            'len': 12,
            'sensors': ['TH1', 'TH2', 'TH3', 'TH4', 'TH5', 'TH6', 'TH7', 'TH8']
        },
        b'\x46': {
            'len': 11,
            'sensors': ['wind']
        },
        b'\x42': {
            'len': 10,
            'sensors': ['rain']
        },
        b'\x48': {
            'len': 10,
            'sensors': ['pressure']
        },
        b'\x4E': {
            'len': 9,
            'sensors': ['uv']
        },
        b'\x4C': {
            'len': 11,
            'sensors': ['soil']
        }
    }

    def __init__(self, port=None, model="WMR200"):
        self.port = port
        self.model = model
        self.connected = False
        self.serial_conn = None
        self.station_id = f"OS-{model}-{int(time.time())}"
        self.buffer = bytearray()

        self.sensor_data = {
            'temperature': {},
            'humidity': {},
            'pressure': None,
            'wind_speed': None,
            'wind_dir': None,
            'rain': None,
            'uv': None,
            'soil_moisture': None,
            'soil_temp': None
        }

    def connect(self) -> Tuple[bool, str]:
        """Connect to Oregon Scientific station"""
        try:
            import serial
            import serial.tools.list_ports

            if not self.port:
                ports = serial.tools.list_ports.comports()
                for p in ports:
                    if any(x in p.description.lower() for x in ['oregon', 'wmr', 'cp210', 'silicon']):
                        self.port = p.device
                        break
                if not self.port:
                    if IS_LINUX:
                        if os.path.exists('/dev/ttyUSB0'):
                            self.port = '/dev/ttyUSB0'
                        elif os.path.exists('/dev/ttyACM0'):
                            self.port = '/dev/ttyACM0'
                    elif IS_WINDOWS:
                        self.port = 'COM3'

            if not self.port:
                return False, "No Oregon Scientific station found"

            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=9600,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=2
            )

            self.serial_conn.reset_input_buffer()
            self.buffer = bytearray()
            self.connected = True
            return True, f"Oregon Scientific {self.model} connected on {self.port}"

        except Exception as e:
            return False, str(e)

    def _parse_wmr_packet(self, packet: bytes) -> Optional[EnvironmentalMeasurement]:
        """Parse Oregon Scientific WMR protocol packet"""
        try:
            if len(packet) < 2:
                return None

            msg_type = packet[0:1]
            msg_len = len(packet)

            if msg_type in self.MESSAGE_TYPES:
                info = self.MESSAGE_TYPES[msg_type]

                if msg_len >= info['len']:
                    if msg_type == b'\xD4':
                        channel = (packet[2] & 0xF0) >> 4
                        temp_raw = (packet[4] << 8) | packet[5]
                        humid_raw = packet[6]

                        if temp_raw != 0xFFFF:
                            temp_c = (temp_raw - 400) / 10.0
                            self.sensor_data['temperature'][channel] = temp_c

                        if humid_raw != 0xFF:
                            self.sensor_data['humidity'][channel] = humid_raw

                    elif msg_type == b'\x46':
                        wind_speed_raw = (packet[3] << 8) | packet[4]
                        wind_dir_raw = (packet[5] << 8) | packet[6]

                        if wind_speed_raw != 0xFFFF:
                            self.sensor_data['wind_speed'] = wind_speed_raw / 10.0

                        if wind_dir_raw != 0xFFFF:
                            self.sensor_data['wind_dir'] = wind_dir_raw / 10.0

                    elif msg_type == b'\x42':
                        rain_raw = (packet[3] << 8) | packet[4]
                        if rain_raw != 0xFFFF:
                            self.sensor_data['rain'] = rain_raw * 0.2

                    elif msg_type == b'\x48':
                        pressure_raw = (packet[3] << 8) | packet[4]
                        if pressure_raw != 0xFFFF:
                            self.sensor_data['pressure'] = pressure_raw / 10.0

                    elif msg_type == b'\x4C':
                        soil_moisture_raw = packet[3]
                        soil_temp_raw = packet[4]

                        if soil_moisture_raw != 0xFF:
                            self.sensor_data['soil_moisture'] = soil_moisture_raw
                        if soil_temp_raw != 0xFF:
                            self.sensor_data['soil_temp'] = (soil_temp_raw - 40) / 2.0

            meas = EnvironmentalMeasurement(
                timestamp=datetime.now(),
                station_id=self.station_id,
                station_name=f"Oregon Scientific {self.model}",
                device_type="WeatherStation",
                manufacturer="Oregon Scientific",
                model=self.model,
                temperature_c=self.sensor_data['temperature'].get(1),
                relative_humidity_pct=self.sensor_data['humidity'].get(1),
                pressure_hpa=self.sensor_data['pressure'],
                wind_speed_ms=self.sensor_data['wind_speed'],
                wind_direction_deg=self.sensor_data['wind_dir'],
                rainfall_mm=self.sensor_data['rain'],
                soil_moisture_pct=self.sensor_data['soil_moisture'],
                soil_temperature_c=self.sensor_data['soil_temp']
            )
            return meas.calculate_derived_metrics()

        except Exception as e:
            print(f"Oregon parse error: {e}")
            return None

    def read_live_data(self) -> Optional[EnvironmentalMeasurement]:
        """Read and parse Oregon Scientific data"""
        if not self.connected or not self.serial_conn:
            return None

        try:
            if self.serial_conn.in_waiting > 0:
                data = self.serial_conn.read(self.serial_conn.in_waiting)
                self.buffer.extend(data)

                while len(self.buffer) >= 3:
                    if self.buffer[0] == 0xFF:
                        meas = self._parse_wmr_packet(self.buffer)
                        if meas:
                            self.buffer = self.buffer[meas_bytes:]
                            return meas
                        else:
                            self.buffer = self.buffer[1:]
                    else:
                        self.buffer = self.buffer[1:]

            return None

        except Exception as e:
            print(f"Oregon read error: {e}")
            return None

    def disconnect(self):
        if self.serial_conn:
            try:
                self.serial_conn.close()
            except:
                pass
        self.connected = False

# ============================================================================
# ECOWITT DRIVER (with soil/lightning support)
# ============================================================================
class EcowittDriver:
    def __init__(self, host=None, port=45000, model="GW1000"):
        self.host = host
        self.port = port
        self.model = model
        self.listener = None
        self.connected = False
        self.listener_thread = None
        self.has_soil_sensors = model in ["GW1000", "GW1100"]
        self.has_lightning = model in ["WH57"]

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
            if not data:
                return None

            meas = EnvironmentalMeasurement(
                timestamp=datetime.now(),
                station_id=getattr(self.listener, 'mac', 'Ecowitt'),
                station_name=f"Ecowitt {self.model}",
                device_type="WeatherStation",
                manufacturer="Ecowitt",
                model=self.model,

                temperature_c=(data.get('tempf', 0) - 32) * 5/9 if 'tempf' in data else None,
                relative_humidity_pct=data.get('humidity'),
                pressure_hpa=data.get('baromabs', 0) * 33.8639 if 'baromabs' in data else None,
                wind_speed_ms=data.get('windspeedmph', 0) * 0.44704 if 'windspeedmph' in data else None,
                wind_direction_deg=data.get('winddir'),
                rainfall_mm=data.get('rainin', 0) * 25.4 if 'rainin' in data else None,
                solar_radiation_w_m2=data.get('solarradiation'),
                uv_index=data.get('uv'),

                soil_moisture_pct=data.get('soilmoisture') if self.has_soil_sensors else None,
                soil_temperature_c=(data.get('soiltempf', 0) - 32) * 5/9 if 'soiltempf' in data and self.has_soil_sensors else None,
                leaf_wetness_pct=data.get('leafwetness') if self.has_soil_sensors else None,

                lightning_strike_count=data.get('lightning_count') if self.has_lightning else None,
                lightning_distance_km=data.get('lightning_distance') if self.has_lightning else None
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
# DAVIS DRIVER (preserved)
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

# ============================================================================
# AMBIENT WEATHER DRIVER (preserved)
# ============================================================================
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

# ============================================================================
# FIXED PLUGIN BROWSER (preserved)
# ============================================================================
class FixedPluginBrowser:
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

        plugins = [
            ("🌦️ Meteorology & Environment", "Multi-station · Soil/Lightning/Gusts · Cloud"),
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
# MAIN PLUGIN CLASS - ULTRA COMPACT 600x480 UI
# ============================================================================
class MeteorologyEnvironmentalSuitePlugin:

    def __init__(self, main_app):
        self.app = main_app
        self.window = None
        self.ui_queue = None
        self.deps = DEPS

        # Multi-station support with location tagging
        self.devices: Dict[str, Dict] = {}
        self.active_station = None

        # Measurements per station
        self.measurements: Dict[str, List[EnvironmentalMeasurement]] = {}
        self.last_measurement: Dict[str, EnvironmentalMeasurement] = {}

        # Cloud uploaders
        self.wu_uploader = None
        self.cwop_uploader = None
        self.ecowitt_uploader = None
        self.upload_queue = queue.Queue()
        self.upload_thread = None
        self.upload_active = False

        # Device instances
        self.davis = None
        self.ambient = None
        self.ecowitt = None
        self.fine_offset = None
        self.oregon = None
        self.weatherflow = None

        # UI Variables
        self.status_var = tk.StringVar(value="Meteorology v1.3 - Ready")
        self.device_var = tk.StringVar()
        self.port_var = tk.StringVar()
        self.api_key_var = tk.StringVar()
        self.app_key_var = tk.StringVar()
        self.station_id_var = tk.StringVar()
        self.interval_var = tk.StringVar(value="60")

        # Cloud upload variables
        self.wu_id_var = tk.StringVar()
        self.wu_password_var = tk.StringVar()
        self.cwop_id_var = tk.StringVar()
        self.cwop_passcode_var = tk.StringVar()
        self.ecowitt_mac_var = tk.StringVar()
        self.ecowitt_app_key_var = tk.StringVar()
        self.upload_enabled_var = tk.BooleanVar(value=False)

        # Location tagging
        self.location_var = tk.StringVar(value="outdoor")

        # Soil calibration factor
        self.soil_cal_var = tk.StringVar(value="1.0")

        # All devices
        self.all_devices = [
            "Davis Vantage Pro2", "Davis Vantage Vue", "Davis Envoy8X",
            "Ambient Weather WS-2902", "Ambient Weather WS-2000", "Ambient Weather WS-5000",
            "Ecowitt GW1000/GW1100", "Ecowitt HP2551", "Ecowitt WS6006", "Ecowitt WH57 Lightning",
            "Fine Offset WH1080", "Fine Offset WH2080", "Fine Offset WH3080",
            "Oregon Scientific WMR88", "Oregon Scientific WMR89", "Oregon Scientific WMR200",
            "WeatherFlow Tempest", "WeatherFlow Air", "WeatherFlow Sky",
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

        self.window = tk.Toplevel(self.app.root)
        self.window.title("Meteorology v1.3")
        self.window.geometry("600x480")
        self.window.minsize(580, 460)
        self.window.transient(self.app.root)

        self.ui_queue = ThreadSafeUI(self.window)
        self._build_compact_ui()

        self.upload_active = True
        self.upload_thread = threading.Thread(target=self._upload_loop, daemon=True)
        self.upload_thread.start()

        self.window.lift()
        self.window.focus_force()
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_compact_ui(self):
        """600x480 UI - Enhanced with icons and station panel"""
        # ============ HEADER ============
        header = tk.Frame(self.window, bg="#3498db", height=35)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="🌦️", font=("Arial", 14),
                bg="#3498db", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Label(header, text="METEOROLOGY", font=("Arial", 10, "bold"),
                bg="#3498db", fg="white").pack(side=tk.LEFT)
        tk.Label(header, text="v1.3", font=("Arial", 7),
                bg="#3498db", fg="#f1c40f").pack(side=tk.LEFT, padx=3)

        self.status_indicator = tk.Label(header, textvariable=self.status_var,
                                        font=("Arial", 7), bg="#3498db", fg="white")
        self.status_indicator.pack(side=tk.RIGHT, padx=5)

        # ============ DEVICE TOOLBAR ============
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

        tk.Label(self.param_frame, text="Port:", font=("Arial", 7),
                bg="#ecf0f1").pack(side=tk.LEFT, padx=2)
        ttk.Entry(self.param_frame, textvariable=self.port_var, width=12).pack(side=tk.LEFT, padx=2)

        self.search_btn = ttk.Button(self.param_frame, text="🔍 Search",
                                     command=self._search_stations, width=6)
        self.search_btn.pack(side=tk.LEFT, padx=2)

        tk.Label(self.param_frame, text="Station:", font=("Arial", 7),
                bg="#ecf0f1").pack(side=tk.LEFT, padx=2)
        self.station_selector = ttk.Combobox(self.param_frame, values=[], width=8)
        self.station_selector.pack(side=tk.LEFT, padx=2)
        self.station_selector.bind('<<ComboboxSelected>>', self._switch_station)

        self.last_reading_label = tk.Label(toolbar, text="No data",
                                          font=("Arial", 7, "bold"),
                                          bg="#ecf0f1", fg="#7f8c8d")
        self.last_reading_label.pack(side=tk.BOTTOM, pady=2)

        # ============ MAIN CONTENT - NOTEBOOK ============
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=3, pady=2)

        # Tab 1: Live Data (with icons)
        live_tab = tk.Frame(notebook, bg="white")
        notebook.add(live_tab, text="Live")

        grid = tk.Frame(live_tab, bg="white")
        grid.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        measurements = [
            ("🌡️ Temperature", "---°C", 0, 0),
            ("💧 Humidity", "---%", 0, 1),
            ("📊 Pressure", "---hPa", 0, 2),
            ("🌬️ Wind", "---m/s", 1, 0),
            ("💨 Gust", "---m/s", 1, 1),
            ("🧭 Direction", "---°", 1, 2),
            ("☔ Rain", "---mm", 2, 0),
            ("☀️ Solar", "---W/m²", 2, 1),
            ("🕶️ UV", "---", 2, 2),
            ("🌱 Soil Moisture", "---%", 3, 0),
            ("🌡️ Soil Temp", "---°C", 3, 1),
            ("⚡ Lightning", "---km", 3, 2),
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
            self.meas_labels[label.split(' ', 1)[1]] = val

        for i in range(4): grid.rowconfigure(i, weight=1)
        for i in range(3): grid.columnconfigure(i, weight=1)

        # Tab 2: Station Info
        station_tab = tk.Frame(notebook, bg="white")
        notebook.add(station_tab, text="Stations")

        self.station_frame = tk.Frame(station_tab, bg="white")
        self.station_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        header_frame = tk.Frame(self.station_frame, bg="#f0f0f0")
        header_frame.pack(fill=tk.X, pady=2)
        for col, text in enumerate(["Station", "Location", "Last Update", "Battery", "RSSI", "Uptime"]):
            tk.Label(header_frame, text=text, font=("Arial", 7, "bold"),
                    bg="#f0f0f0").grid(row=0, column=col, padx=4, sticky=tk.W)

        self.station_canvas = tk.Canvas(self.station_frame, bg="white", height=100)
        scrollbar = ttk.Scrollbar(self.station_frame, orient="vertical",
                                  command=self.station_canvas.yview)
        self.station_list_frame = tk.Frame(self.station_canvas, bg="white")

        self.station_list_frame.bind(
            "<Configure>",
            lambda e: self.station_canvas.configure(
                scrollregion=self.station_canvas.bbox("all")
            )
        )

        self.station_canvas.create_window((0, 0), window=self.station_list_frame, anchor="nw")
        self.station_canvas.configure(yscrollcommand=scrollbar.set)

        self.station_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        loc_frame = tk.Frame(station_tab, bg="white")
        loc_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(loc_frame, text="Default Location:", font=("Arial", 7, "bold"),
                bg="white").pack(side=tk.LEFT, padx=2)
        ttk.Combobox(loc_frame, textvariable=self.location_var,
                     values=["outdoor", "indoor", "greenhouse"],
                     width=10, state="readonly").pack(side=tk.LEFT, padx=2)

        tk.Label(loc_frame, text="Soil Cal:", font=("Arial", 7, "bold"),
                bg="white").pack(side=tk.LEFT, padx=(10,2))
        ttk.Entry(loc_frame, textvariable=self.soil_cal_var, width=5).pack(side=tk.LEFT)
        tk.Label(loc_frame, text="(cal factor)", font=("Arial", 6),
                bg="white", fg="#888").pack(side=tk.LEFT, padx=2)

        # Tab 3: Log
        log_tab = tk.Frame(notebook, bg="white")
        notebook.add(log_tab, text="Log")

        self.log_listbox = tk.Listbox(log_tab, font=("Courier", 8), height=10)
        scroll = ttk.Scrollbar(log_tab, orient=tk.VERTICAL, command=self.log_listbox.yview)
        self.log_listbox.configure(yscrollcommand=scroll.set)
        self.log_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=5)

        # Tab 4: Controls
        ctrl_tab = tk.Frame(notebook, bg="white")
        notebook.add(ctrl_tab, text="Controls")

        ttk.Button(ctrl_tab, text="📊 Read Now",
                  command=self._read_now,
                  width=15).pack(pady=5)

        self.live_btn = ttk.Button(ctrl_tab, text="▶ Start Live",
                                   command=self._toggle_live,
                                   width=15)
        self.live_btn.pack(pady=2)

        int_frame = tk.Frame(ctrl_tab, bg="white")
        int_frame.pack(pady=5)
        tk.Label(int_frame, text="Interval (s):", font=("Arial", 7),
                bg="white").pack(side=tk.LEFT)
        ttk.Entry(int_frame, textvariable=self.interval_var, width=5).pack(side=tk.LEFT, padx=2)

        # Cloud Upload Section
        cloud_frame = tk.LabelFrame(ctrl_tab, text="☁️ Cloud Upload", bg="white",
                                   font=("Arial", 8, "bold"), fg="#3498db")
        cloud_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Checkbutton(cloud_frame, text="Enable Auto-Upload",
                      variable=self.upload_enabled_var,
                      bg="white").pack(anchor=tk.W, padx=5)

        wu_frame = tk.Frame(cloud_frame, bg="white")
        wu_frame.pack(fill=tk.X, pady=2)
        tk.Label(wu_frame, text="WU ID:", font=("Arial", 7),
                bg="white").pack(side=tk.LEFT, padx=2)
        ttk.Entry(wu_frame, textvariable=self.wu_id_var, width=8).pack(side=tk.LEFT, padx=2)
        tk.Label(wu_frame, text="Key:", font=("Arial", 7),
                bg="white").pack(side=tk.LEFT, padx=2)
        ttk.Entry(wu_frame, textvariable=self.wu_password_var, width=8, show="*").pack(side=tk.LEFT, padx=2)

        cwop_frame = tk.Frame(cloud_frame, bg="white")
        cwop_frame.pack(fill=tk.X, pady=2)
        tk.Label(cwop_frame, text="CWOP ID:", font=("Arial", 7),
                bg="white").pack(side=tk.LEFT, padx=2)
        ttk.Entry(cwop_frame, textvariable=self.cwop_id_var, width=8).pack(side=tk.LEFT, padx=2)
        tk.Label(cwop_frame, text="Code:", font=("Arial", 7),
                bg="white").pack(side=tk.LEFT, padx=2)
        ttk.Entry(cwop_frame, textvariable=self.cwop_passcode_var, width=8, show="*").pack(side=tk.LEFT, padx=2)

        eco_frame = tk.Frame(cloud_frame, bg="white")
        eco_frame.pack(fill=tk.X, pady=2)
        tk.Label(eco_frame, text="MAC:", font=("Arial", 7),
                bg="white").pack(side=tk.LEFT, padx=2)
        ttk.Entry(eco_frame, textvariable=self.ecowitt_mac_var, width=8).pack(side=tk.LEFT, padx=2)
        tk.Label(eco_frame, text="App Key:", font=("Arial", 7),
                bg="white").pack(side=tk.LEFT, padx=2)
        ttk.Entry(eco_frame, textvariable=self.ecowitt_app_key_var, width=8, show="*").pack(side=tk.LEFT, padx=2)

        # Horizontal button row
        button_row = tk.Frame(ctrl_tab, bg="white")
        button_row.pack(pady=5)

        ttk.Button(button_row, text="📤 Test Upload",
                  command=self._test_upload,
                  width=12).pack(side=tk.LEFT, padx=2)

        ttk.Button(button_row, text="📤 Send to Table",
                  command=self.send_to_table,
                  width=12).pack(side=tk.LEFT, padx=2)

        ttk.Button(button_row, text="🗑️ Clear Log",
                  command=self._clear_log,
                  width=12).pack(side=tk.LEFT, padx=2)

        # ============ STATUS BAR ============
        status = tk.Frame(self.window, bg="#34495e", height=20)
        status.pack(fill=tk.X, side=tk.BOTTOM)
        status.pack_propagate(False)

        self.count_label = tk.Label(status,
            text=f"📊 0 readings · 0 stations",
            font=("Arial", 7), bg="#34495e", fg="white")
        self.count_label.pack(side=tk.LEFT, padx=5)

        self.status_icons = tk.Label(status,
            text="",
            font=("Arial", 7), bg="#34495e", fg="#bdc3c7")
        self.status_icons.pack(side=tk.RIGHT, padx=5)

        self.live_active = False
        self.live_thread = None

    def _on_device_select(self, event=None):
        """Update parameter fields based on device"""
        device = self.device_var.get()

        for widget in self.param_frame.winfo_children():
            if widget not in [self.station_selector]:
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

        elif "Fine Offset" in device:
            tk.Label(self.param_frame, text="Port/HID:", font=("Arial", 7),
                    bg="#ecf0f1").pack(side=tk.LEFT, padx=2)
            ttk.Entry(self.param_frame, textvariable=self.port_var, width=12).pack(side=tk.LEFT, padx=2)

        elif "Oregon" in device:
            tk.Label(self.param_frame, text="Port:", font=("Arial", 7),
                    bg="#ecf0f1").pack(side=tk.LEFT, padx=2)
            ttk.Entry(self.param_frame, textvariable=self.port_var, width=12).pack(side=tk.LEFT, padx=2)

        elif "WeatherFlow" in device:
            tk.Label(self.param_frame, text="UDP Port:", font=("Arial", 7),
                    bg="#ecf0f1").pack(side=tk.LEFT, padx=2)
            ttk.Entry(self.param_frame, textvariable=self.port_var, width=8).pack(side=tk.LEFT, padx=2)
            tk.Label(self.param_frame, text="(50222)", font=("Arial", 6),
                    bg="#ecf0f1", fg="#7f8c8d").pack(side=tk.LEFT, padx=2)

        elif "Meteostat" in device or "METAR" in device:
            tk.Label(self.param_frame, text="Station ID:", font=("Arial", 7),
                    bg="#ecf0f1").pack(side=tk.LEFT, padx=2)
            ttk.Entry(self.param_frame, textvariable=self.station_id_var, width=8).pack(side=tk.LEFT, padx=2)

        else:
            tk.Label(self.param_frame, text="Port:", font=("Arial", 7),
                    bg="#ecf0f1").pack(side=tk.LEFT, padx=2)
            ttk.Entry(self.param_frame, textvariable=self.port_var, width=12).pack(side=tk.LEFT, padx=2)

    def _search_stations(self):
        """Enhanced station search with auto-discovery"""
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

        elif "Fine Offset" in device:
            try:
                import hid
                found = []
                for vid, pid, name in FineOffsetDriver.FINE_OFFSET_IDS:
                    try:
                        devices = hid.enumerate(vid, pid)
                        if devices:
                            found.append(f"{name} (VID:{vid:04x} PID:{pid:04x})")
                    except:
                        pass

                if found:
                    msg = "Found Fine Offset devices:\n\n" + "\n".join(found)
                else:
                    msg = "No Fine Offset devices found.\nTry entering port manually (e.g., COM3, /dev/ttyUSB0, or 'HID')"
                messagebox.showinfo("Scan Results", msg)
            except:
                messagebox.showinfo("Port Scan", "Enter port manually (e.g., COM3, /dev/ttyUSB0, or 'HID')")

        elif "WeatherFlow" in device:
            msg = "WeatherFlow stations broadcast on UDP port 50222\n\n"
            msg += "To discover stations:\n"
            msg += "1. Ensure station is on same network\n"
            msg += "2. Start listening (connect)\n"
            msg += "3. Check logs for 'evt_strike' or 'obs_st' messages"
            messagebox.showinfo("WeatherFlow Discovery", msg)

        elif "Oregon" in device:
            try:
                import serial.tools.list_ports
                ports = serial.tools.list_ports.comports()
                oregon_ports = []
                for p in ports:
                    if any(x in p.description.lower() for x in ['oregon', 'wmr', 'cp210']):
                        oregon_ports.append(f"{p.device}: {p.description}")

                if oregon_ports:
                    msg = "Found Oregon Scientific devices:\n\n" + "\n".join(oregon_ports)
                else:
                    msg = "No Oregon Scientific devices found.\nTry entering port manually (e.g., COM3, /dev/ttyUSB0)"
                messagebox.showinfo("Scan Results", msg)
            except:
                messagebox.showinfo("Port Scan", "Enter port manually (e.g., COM3, /dev/ttyUSB0)")

        else:
            try:
                import serial.tools.list_ports
                ports = serial.tools.list_ports.comports()
                if ports:
                    port_list = "\n".join([f"{p.device}: {p.description}" for p in ports[:10]])
                    messagebox.showinfo("Available Ports", f"Found ports:\n\n{port_list}")
                else:
                    messagebox.showinfo("No Ports", "No serial ports found")
            except:
                messagebox.showinfo("Port Scan", "Enter port manually")

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
            driver = None
            device_type = ""
            station_id = ""

            try:
                if "Davis" in device:
                    driver = DavisWeatherStationDriver(port=self.port_var.get(), model=device)
                    success, msg = driver.connect()
                    device_type = "davis"
                    station_id = driver.serial_num

                elif "Ambient" in device:
                    driver = AmbientWeatherDriver(
                        api_key=self.api_key_var.get(),
                        app_key=self.app_key_var.get()
                    )
                    success, msg = driver.connect()
                    device_type = "ambient"
                    station_id = driver.station.mac_address if driver.station else "ambient"

                elif "Ecowitt" in device:
                    driver = EcowittDriver(host=self.port_var.get(), model=device)
                    success, msg = driver.connect()
                    device_type = "ecowitt"
                    station_id = getattr(driver.listener, 'mac', 'ecowitt') if driver.listener else "ecowitt"

                elif "Fine Offset" in device:
                    try:
                        soil_cal = float(self.soil_cal_var.get())
                    except:
                        soil_cal = None
                    driver = FineOffsetDriver(port=self.port_var.get(), model=device, soil_cal_factor=soil_cal)
                    success, msg = driver.connect()
                    device_type = "fine_offset"
                    station_id = driver.station_id

                elif "Oregon" in device:
                    driver = OregonScientificDriver(port=self.port_var.get(), model=device)
                    success, msg = driver.connect()
                    device_type = "oregon"
                    station_id = driver.station_id

                elif "WeatherFlow" in device:
                    port = int(self.port_var.get()) if self.port_var.get() else 50222
                    driver = WeatherFlowDriver(port=port, model=device)
                    success, msg = driver.connect()
                    device_type = "weatherflow"
                    station_id = driver.station_id

                else:
                    success = False
                    msg = f"Driver for {device} not implemented"

            except Exception as e:
                success = False
                msg = str(e)

            def update_ui():
                self.connect_btn.config(state='normal')
                if success:
                    self.devices[station_id] = {
                        'driver': driver,
                        'type': device_type,
                        'model': device,
                        'name': f"{device} ({station_id[:8]})",
                        'connected': True,
                        'location': self.location_var.get()
                    }

                    if station_id not in self.measurements:
                        self.measurements[station_id] = []

                    self.station_selector['values'] = [d['name'] for d in self.devices.values()]
                    self.station_selector.set(self.devices[station_id]['name'])
                    self.active_station = station_id

                    self.conn_indicator.config(fg="#2ecc71")
                    self._update_status(f"✅ Connected: {len(self.devices)} stations", "#27ae60")
                    self._update_station_list()
                else:
                    self.conn_indicator.config(fg="red")
                    self._update_status(f"❌ {msg[:30]}", "#e74c3c")
                    messagebox.showerror("Connection Failed", msg)

            self.ui_queue.schedule(update_ui)

        threading.Thread(target=connect_thread, daemon=True).start()

    def _switch_station(self, event=None):
        """Switch active station in UI"""
        station_name = self.station_selector.get()
        for sid, info in self.devices.items():
            if info['name'] == station_name:
                self.active_station = sid
                if sid in self.last_measurement:
                    self._update_display(self.last_measurement[sid])
                break

    def _update_station_list(self):
        """Update the station info panel"""
        for widget in self.station_list_frame.winfo_children():
            widget.destroy()

        for row, (station_id, info) in enumerate(self.devices.items()):
            frame = tk.Frame(self.station_list_frame, bg="white")
            frame.pack(fill=tk.X, pady=1)

            tk.Label(frame, text=info['name'][:15], font=("Arial", 7),
                    bg="white", width=15, anchor=tk.W).grid(row=0, column=0, padx=2)

            location = info.get('location', 'outdoor')
            loc_icon = "🏠" if location == "indoor" else "🌳" if location == "outdoor" else "🌱"
            tk.Label(frame, text=f"{loc_icon} {location}", font=("Arial", 7),
                    bg="white", width=10, anchor=tk.W).grid(row=0, column=1, padx=2)

            if station_id in self.last_measurement:
                last = self.last_measurement[station_id].timestamp
                time_str = last.strftime("%H:%M:%S")
            else:
                time_str = "---"
            tk.Label(frame, text=time_str, font=("Arial", 7),
                    bg="white", width=8, anchor=tk.W).grid(row=0, column=2, padx=2)

            battery = ""
            if station_id in self.last_measurement:
                meas = self.last_measurement[station_id]
                if meas.battery_voltage:
                    batt = meas.battery_voltage
                    if batt > 2.8:
                        battery = "🔋 Good"
                    elif batt > 2.5:
                        battery = "🪫 Low"
                    else:
                        battery = "⚠️ Critical"
            tk.Label(frame, text=battery, font=("Arial", 7),
                    bg="white", width=8, anchor=tk.W).grid(row=0, column=3, padx=2)

            rssi = ""
            if station_id in self.last_measurement:
                rssi_val = self.last_measurement[station_id].rssi
                if rssi_val:
                    rssi = f"{rssi_val} dBm"
            tk.Label(frame, text=rssi, font=("Arial", 7),
                    bg="white", width=8, anchor=tk.W).grid(row=0, column=4, padx=2)

            uptime = ""
            if station_id in self.last_measurement:
                uptime_val = self.last_measurement[station_id].uptime_days
                if uptime_val:
                    uptime = f"{uptime_val:.1f}d"
            tk.Label(frame, text=uptime, font=("Arial", 7),
                    bg="white", width=6, anchor=tk.W).grid(row=0, column=5, padx=2)

    def _read_now(self):
        """Read current data from all connected stations"""
        if not self.devices:
            messagebox.showwarning("Not Connected", "Connect a device first")
            return

        def read_thread():
            for station_id, info in self.devices.items():
                try:
                    driver = info['driver']
                    device_type = info['type']

                    if device_type == "davis":
                        meas = driver.read_live_data()
                    elif device_type == "ambient":
                        meas = driver.read_live_data()
                    elif device_type == "ecowitt":
                        meas = driver.read_live_data()
                    elif device_type == "fine_offset":
                        meas = driver.read_live_data()
                    elif device_type == "oregon":
                        meas = driver.read_live_data()
                    elif device_type == "weatherflow":
                        meas = driver.read_live_data()
                    else:
                        meas = None

                    if meas:
                        meas.station_id = station_id
                        meas.location = info.get('location', 'outdoor')
                        self.measurements[station_id].append(meas)
                        self.last_measurement[station_id] = meas

                        if self.upload_enabled_var.get():
                            self.upload_queue.put(meas)

                        if station_id == self.active_station:
                            self.ui_queue.schedule(self._update_display, meas)

                except Exception as e:
                    print(f"Read error for {station_id}: {e}")

        threading.Thread(target=read_thread, daemon=True).start()

    def _update_display(self, meas: EnvironmentalMeasurement):
        """Update UI with new measurement"""
        self.meas_labels["Temperature"].config(
            text=f"{meas.temperature_c:.1f}°C" if meas.temperature_c else "---°C")
        self.meas_labels["Humidity"].config(
            text=f"{meas.relative_humidity_pct:.0f}%" if meas.relative_humidity_pct else "---%")
        self.meas_labels["Pressure"].config(
            text=f"{meas.pressure_hpa:.1f}hPa" if meas.pressure_hpa else "---hPa")
        self.meas_labels["Wind"].config(
            text=f"{meas.wind_speed_ms:.1f}m/s" if meas.wind_speed_ms else "---m/s")
        self.meas_labels["Gust"].config(
            text=f"{meas.wind_gust_ms:.1f}m/s" if meas.wind_gust_ms else "---m/s")
        self.meas_labels["Direction"].config(
            text=f"{meas.wind_direction_deg:.0f}°" if meas.wind_direction_deg else "---°")
        self.meas_labels["Rain"].config(
            text=f"{meas.rainfall_mm:.1f}mm" if meas.rainfall_mm else "---mm")
        self.meas_labels["Solar"].config(
            text=f"{meas.solar_radiation_w_m2:.0f}" if meas.solar_radiation_w_m2 else "---")
        self.meas_labels["UV"].config(
            text=f"{meas.uv_index:.1f}" if meas.uv_index else "---")

        self.meas_labels["Soil Moisture"].config(
            text=f"{meas.soil_moisture_pct:.0f}%" if meas.soil_moisture_pct else "---%")
        self.meas_labels["Soil Temp"].config(
            text=f"{meas.soil_temperature_c:.1f}°C" if meas.soil_temperature_c else "---°C")

        lightning_text = "---"
        if meas.lightning_distance_km:
            lightning_text = f"{meas.lightning_distance_km:.1f}km"
            if meas.lightning_strike_count:
                lightning_text += f" ({meas.lightning_strike_count})"
        self.meas_labels["Lightning"].config(text=lightning_text)

        temp_str = f"{meas.temperature_c:.1f}°C" if meas.temperature_c else "---"
        station_name = self.devices.get(meas.station_id, {}).get('name', '')
        self.last_reading_label.config(text=f"{station_name}: {temp_str}")

        if meas.quality_flag != "good":
            self.status_indicator.config(fg="#e74c3c")
        else:
            self.status_indicator.config(fg="white")

        timestamp = meas.timestamp.strftime("%H:%M:%S")
        temp = f"{meas.temperature_c:.1f}°C" if meas.temperature_c else "---"
        humid = f"{meas.relative_humidity_pct:.0f}%" if meas.relative_humidity_pct else "---"
        soil = f"Soil:{meas.soil_moisture_pct:.0f}%" if meas.soil_moisture_pct else ""
        lightning = f"⚡{meas.lightning_distance_km:.0f}km" if meas.lightning_distance_km else ""

        log_entry = f"[{timestamp}] {station_name[:10]}: {temp} {humid} {soil} {lightning}"
        self.log_listbox.insert(0, log_entry)
        if self.log_listbox.size() > 50:
            self.log_listbox.delete(50, tk.END)

        self._update_station_list()

        station_icons = []
        for station_id, info in self.devices.items():
            if station_id in self.last_measurement:
                icon = "✅" if info.get('connected') else "❌"
                station_icons.append(icon)

        self.status_icons.config(text=" ".join(station_icons))

        total_readings = sum(len(v) for v in self.measurements.values())
        outdoor = sum(1 for sid in self.devices if self.devices[sid].get('location') == 'outdoor')
        indoor = sum(1 for sid in self.devices if self.devices[sid].get('location') == 'indoor')

        self.count_label.config(
            text=f"📊 {total_readings} readings · {outdoor}🌳 {indoor}🏠"
        )

    def _test_upload(self):
        """Test cloud upload with last measurement"""
        if not self.last_measurement:
            messagebox.showwarning("No Data", "Collect data first")
            return

        self._upload_to_clouds(self.last_measurement.get(self.active_station))

    def _upload_to_clouds(self, meas: EnvironmentalMeasurement):
        """Upload measurement to all configured cloud services"""
        if not meas:
            return

        if self.wu_id_var.get() and self.wu_password_var.get():
            if not self.wu_uploader:
                self.wu_uploader = WeatherUndergroundUploader(
                    self.wu_id_var.get(),
                    self.wu_password_var.get()
                )
            success, msg = self.wu_uploader.upload(meas)
            self.ui_queue.schedule(self._log_message, f"WU: {msg}")

        if self.cwop_id_var.get() and self.cwop_passcode_var.get():
            if not self.cwop_uploader:
                self.cwop_uploader = CWOPUploader(
                    self.cwop_id_var.get(),
                    self.cwop_passcode_var.get()
                )
            success, msg = self.cwop_uploader.upload(meas)
            self.ui_queue.schedule(self._log_message, f"CWOP: {msg}")

        if self.ecowitt_mac_var.get() and self.ecowitt_app_key_var.get():
            if not self.ecowitt_uploader:
                self.ecowitt_uploader = EcowittCloudUploader(
                    self.ecowitt_mac_var.get(),
                    self.ecowitt_app_key_var.get()
                )
            success, msg = self.ecowitt_uploader.upload(meas)
            self.ui_queue.schedule(self._log_message, f"Ecowitt: {msg}")

    def _upload_loop(self):
        """Background thread for cloud uploads with change detection"""
        last_uploaded = {}

        while self.upload_active:
            try:
                meas = self.upload_queue.get(timeout=1)

                if meas and self.upload_enabled_var.get():
                    station_id = meas.station_id

                    value_hash = hash((
                        round(meas.temperature_c or 0, 1),
                        round(meas.relative_humidity_pct or 0),
                        round(meas.wind_speed_ms or 0, 1),
                        meas.lightning_strike_count or 0
                    ))

                    last_hash = last_uploaded.get(station_id)
                    if last_hash != value_hash or meas.lightning_strike_count:
                        self._upload_to_clouds(meas)
                        last_uploaded[station_id] = value_hash

            except queue.Empty:
                continue
            except:
                pass

    def _log_message(self, msg: str):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_listbox.insert(0, f"[{timestamp}] {msg}")
        if self.log_listbox.size() > 50:
            self.log_listbox.delete(50, tk.END)

    def _toggle_live(self):
        """Toggle live data streaming"""
        if not self.devices:
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
        """Start live data thread for all stations"""
        def live_loop():
            interval = int(self.interval_var.get())
            while self.live_active:
                self._read_now()
                time.sleep(interval)

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
        """Send measurements from all stations to main table"""
        if not self.measurements:
            messagebox.showwarning("No Data", "No measurements to send")
            return

        all_data = []
        for station_id, meas_list in self.measurements.items():
            for meas in meas_list:
                all_data.append(meas.to_dict())

        try:
            self.app.import_data_from_plugin(all_data)
            self._update_status(f"✅ Sent {len(all_data)} measurements")
        except AttributeError:
            messagebox.showwarning("Integration", "Main app: import_data_from_plugin() required")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def collect_data(self) -> List[Dict]:
        """Collect all measurements for external use"""
        all_data = []
        for station_id, meas_list in self.measurements.items():
            for meas in meas_list:
                all_data.append(meas.to_dict())
        return all_data

    def _on_close(self):
        """Clean shutdown"""
        self.live_active = False
        self.upload_active = False

        for station_id, info in self.devices.items():
            driver = info['driver']
            if driver and hasattr(driver, 'disconnect'):
                try:
                    driver.disconnect()
                except:
                    pass

        if self.window:
            self.window.destroy()
            self.window = None

# ============================================================================
# SIMPLE PLUGIN REGISTRATION
# ============================================================================
def setup_plugin(main_app):
    """Register plugin"""
    plugin = MeteorologyEnvironmentalSuitePlugin(main_app)

    if hasattr(main_app, 'left') and main_app.left is not None:
        main_app.left.add_hardware_button(
            name=PLUGIN_INFO.get("name", "Meteorology & Environment"),
            icon=PLUGIN_INFO.get("icon", "🌦️"),
            command=plugin.show_interface
        )
        print(f"✅ Added: {PLUGIN_INFO.get('name')} v1.3.0")

    return plugin
