"""
BARCODE/QR SCANNER UNIFIED SUITE v2.4 - POLISHED PRODUCTION RELEASE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ FULL-WIDTH TABS: USB HID | USB Serial | Bluetooth SPP | Bluetooth LE | Webcam
✓ LEFT PANEL: Device controls + Context fields
✓ RIGHT PANEL: Square preview (200-400px) + Scrollable scan log
✓ SETTINGS GEAR: Global settings in header
✓ BLE SUPPORT: Socket, Zebra, Honeywell, Datalogic, Inateck, Eyoyo
✓ Plugin Manager compatible dependency checking
✓ INSTALL BUTTONS: One-click dependency installation
✓ TOOLTIPS: Helpful hints on all controls
✓ RSSI BARS: Visual signal strength indicators
✓ CONNECTION COLORS: 🟢 Connected, ⚪ Disconnected
✓ CLEAR LOG: One-click log clearing
✓ COPY ALL: Copy entire log to clipboard
✓ CONTEXT PERSISTENCE: Saved between tab switches
✓ EMPTY STATES: Helpful messages when no devices found
✓ KEYBOARD SHORTCUTS: Ctrl+C copy, Ctrl+T send to table
✓ SCANNING ANIMATION: Visual feedback during BLE scan
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

PLUGIN_INFO = {
    "category": "hardware",
    "id": "barcode_scanner_unified_suite",
    "name": "Barcode/QR Scanner Unified Suite",
    "icon": "📷",
    "description": "USB HID · Serial · Bluetooth SPP/LE · Webcam · Unified UI",
    "version": "2.4.0",
    "requires": ["numpy", "pandas", "pyserial", "bleak", "opencv-python", "pyzbar", "pillow"],
    "optional": [],
    "author": "Sefy Levy",
    "compact": True,
}

# ============================================================================
# PREVENT DOUBLE REGISTRATION
# ============================================================================

import tkinter as tk
_SCANNER_REGISTERED = False
from tkinter import ttk, messagebox, filedialog
import numpy as np
import pandas as pd
from datetime import datetime
import time
import re
import json
import threading
import queue
import subprocess
import asyncio
import sys
from pathlib import Path
import platform
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Callable
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# SAFE BLEAK IMPORT - Placeholders prevent crashes if not installed
# ============================================================================
try:
    from bleak import BleakClient, BleakScanner
    HAS_BLEAK = True
except ImportError:
    HAS_BLEAK = False
    # Create placeholder classes so code doesn't crash
    class BleakClient:
        def __init__(self, *args, **kwargs):
            self.address = args[0] if args else None
        async def connect(self): pass
        async def disconnect(self): pass
        async def get_services(self): return []
        async def start_notify(self, *args): pass
        async def stop_notify(self, *args): pass

    class BleakScanner:
        @staticmethod
        async def discover(*args, **kwargs): return []

# ============================================================================
# PLATFORM DETECTION
# ============================================================================
IS_WINDOWS = platform.system() == 'Windows'
IS_LINUX = platform.system() == 'Linux'
IS_MAC = platform.system() == 'Darwin'

# ============================================================================
# TOOLTIP CLASS
# ============================================================================

class ToolTip:
    """Create tooltips for any widget"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind('<Enter>', self.show_tip)
        widget.bind('<Leave>', self.hide_tip)

    def show_tip(self, event):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
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
# DEPENDENCY CHECK - For runtime warnings
# ============================================================================

def check_dependencies():
    """Check all dependencies with graceful fallbacks"""
    deps = {
        'numpy': False,
        'pandas': False,
        'pyserial': False,
        'bleak': False,
        'opencv': False,
        'pyzbar': False,
        'pillow': False
    }

    try:
        import numpy
        deps['numpy'] = True
    except: pass

    try:
        import pandas
        deps['pandas'] = True
    except: pass

    try:
        import serial
        import serial.tools.list_ports
        deps['pyserial'] = True
    except: pass

    try:
        import bleak
        deps['bleak'] = HAS_BLEAK
    except: pass

    try:
        import cv2
        deps['opencv'] = True
    except: pass

    try:
        from pyzbar import pyzbar as pyzbar_lib
        _ = pyzbar_lib.decode
        deps['pyzbar'] = True
    except: pass

    try:
        from PIL import Image
        deps['pillow'] = True
    except: pass

    return deps

DEPS = check_dependencies()

try:
    from pyzbar import pyzbar as pyzbar
    HAS_PYZBAR = True
except ImportError:
    pyzbar = None
    HAS_PYZBAR = False
# ============================================================================
# BLUETOOTH SPP SCANNER DATABASE - 50+ MODELS
# ============================================================================
BLUETOOTH_SPP_MODELS = {
    # Zebra / Symbol / Motorola
    'Zebra CS3070':       {'manufacturer': 'Zebra',    'default_baud': 9600},
    'Zebra CS60':         {'manufacturer': 'Zebra',    'default_baud': 9600},
    'Zebra CS6080':       {'manufacturer': 'Zebra',    'default_baud': 9600},
    'Zebra DS3678-ER':    {'manufacturer': 'Zebra',    'default_baud': 115200},
    'Zebra DS3678':       {'manufacturer': 'Zebra',    'default_baud': 115200},
    'Zebra DS8108':       {'manufacturer': 'Zebra',    'default_baud': 9600},
    'Zebra DS8178':       {'manufacturer': 'Zebra',    'default_baud': 9600},
    'Symbol LS3578-ER':   {'manufacturer': 'Symbol',   'default_baud': 9600},
    'Symbol LS4278':      {'manufacturer': 'Symbol',   'default_baud': 9600},
    'Motorola DS6878':    {'manufacturer': 'Motorola', 'default_baud': 9600},

    # Honeywell
    'Honeywell 1902':             {'manufacturer': 'Honeywell', 'default_baud': 9600},
    'Honeywell 1902g':            {'manufacturer': 'Honeywell', 'default_baud': 9600},
    'Honeywell 1902i':            {'manufacturer': 'Honeywell', 'default_baud': 9600},
    'Honeywell 1990i':            {'manufacturer': 'Honeywell', 'default_baud': 115200},
    'Honeywell 1991i':            {'manufacturer': 'Honeywell', 'default_baud': 115200},
    'Honeywell 8675i':            {'manufacturer': 'Honeywell', 'default_baud': 9600},
    'Honeywell VuQuest 3310g':    {'manufacturer': 'Honeywell', 'default_baud': 9600},
    'Honeywell Granit 1990i':     {'manufacturer': 'Honeywell', 'default_baud': 115200},
    'Honeywell Granit 1991i':     {'manufacturer': 'Honeywell', 'default_baud': 115200},
    'Honeywell Xenon 1900':       {'manufacturer': 'Honeywell', 'default_baud': 9600},

    # Datalogic
    'Datalogic QuickScan QBT2131': {'manufacturer': 'Datalogic', 'default_baud': 9600},
    'Datalogic QuickScan QBT2400': {'manufacturer': 'Datalogic', 'default_baud': 9600},
    'Datalogic QuickScan QBT2430': {'manufacturer': 'Datalogic', 'default_baud': 9600},
    'Datalogic Gryphon GM4100':    {'manufacturer': 'Datalogic', 'default_baud': 9600},
    'Datalogic Gryphon GM4400':    {'manufacturer': 'Datalogic', 'default_baud': 9600},
    'Datalogic PowerScan PM9100':  {'manufacturer': 'Datalogic', 'default_baud': 115200},
    'Datalogic PowerScan PBT9100': {'manufacturer': 'Datalogic', 'default_baud': 115200},

    # Inateck
    'Inateck BCST-52': {'manufacturer': 'Inateck', 'default_baud': 9600},
    'Inateck BCST-70': {'manufacturer': 'Inateck', 'default_baud': 9600},
    'Inateck BCST-60': {'manufacturer': 'Inateck', 'default_baud': 9600},

    # Eyoyo
    'Eyoyo EY-026': {'manufacturer': 'Eyoyo', 'default_baud': 9600},
    'Eyoyo EY-031': {'manufacturer': 'Eyoyo', 'default_baud': 9600},
    'Eyoyo EY-042': {'manufacturer': 'Eyoyo', 'default_baud': 9600},

    # Socket Mobile
    'Socket S740': {'manufacturer': 'Socket', 'default_baud': 9600},
    'Socket S720': {'manufacturer': 'Socket', 'default_baud': 9600},
    'Socket S700': {'manufacturer': 'Socket', 'default_baud': 9600},
}

# Group by manufacturer for dropdowns
SPP_MANUFACTURERS: dict = {}
for _model, _info in BLUETOOTH_SPP_MODELS.items():
    SPP_MANUFACTURERS.setdefault(_info['manufacturer'], []).append(_model)

# ============================================================================
# BLUETOOTH LE SCANNER DATABASE - CONFIRMED WORKING MODELS
# ============================================================================

BLE_SERVICE_UUIDS = {
    'HID': '00001812-0000-1000-8000-00805f9b34fb',
    'NORDIC_UART': '0000ffe0-0000-1000-8000-00805f9b34fb',
    'SOCKET': '49535343-1e4d-4bd9-ba61-23c647249616',
    'TI_SENSOR': 'f000ffc0-0451-4000-b000-000000000000',
}

BLE_CHAR_UUIDS = {
    'HID_REPORT': '00002a4d-0000-1000-8000-00805f9b34fb',
    'NORDIC_RX': '0000ffe1-0000-1000-8000-00805f9b34fb',
    'NORDIC_TX': '0000ffe2-0000-1000-8000-00805f9b34fb',
    'SOCKET_RX': '49535343-1e4d-4bd9-ba61-23c647249617',
    'SOCKET_TX': '49535343-6d8a-4b5c-a1f1-157f125a12e6',
}

BLE_SCANNER_DATABASE = {
    'Socket S740': {
        'manufacturer': 'Socket',
        'service_uuid': BLE_SERVICE_UUIDS['SOCKET'],
        'rx_char': BLE_CHAR_UUIDS['SOCKET_RX'],
        'tx_char': BLE_CHAR_UUIDS['SOCKET_TX'],
    },
    'Socket S820': {
        'manufacturer': 'Socket',
        'service_uuid': BLE_SERVICE_UUIDS['SOCKET'],
        'rx_char': BLE_CHAR_UUIDS['SOCKET_RX'],
        'tx_char': BLE_CHAR_UUIDS['SOCKET_TX'],
    },
    'Socket S860': {
        'manufacturer': 'Socket',
        'service_uuid': BLE_SERVICE_UUIDS['SOCKET'],
        'rx_char': BLE_CHAR_UUIDS['SOCKET_RX'],
        'tx_char': BLE_CHAR_UUIDS['SOCKET_TX'],
    },
    'Socket DuraScan 700': {
        'manufacturer': 'Socket',
        'service_uuid': BLE_SERVICE_UUIDS['SOCKET'],
        'rx_char': BLE_CHAR_UUIDS['SOCKET_RX'],
        'tx_char': BLE_CHAR_UUIDS['SOCKET_TX'],
    },
    'Socket DuraScan 800': {
        'manufacturer': 'Socket',
        'service_uuid': BLE_SERVICE_UUIDS['SOCKET'],
        'rx_char': BLE_CHAR_UUIDS['SOCKET_RX'],
        'tx_char': BLE_CHAR_UUIDS['SOCKET_TX'],
    },
    'Zebra CS60-HC': {
        'manufacturer': 'Zebra',
        'service_uuid': BLE_SERVICE_UUIDS['HID'],
        'rx_char': BLE_CHAR_UUIDS['HID_REPORT'],
        'tx_char': None,
    },
    'Zebra CS6080-HC': {
        'manufacturer': 'Zebra',
        'service_uuid': BLE_SERVICE_UUIDS['HID'],
        'rx_char': BLE_CHAR_UUIDS['HID_REPORT'],
        'tx_char': None,
    },
    'Honeywell 1952g-bf': {
        'manufacturer': 'Honeywell',
        'service_uuid': BLE_SERVICE_UUIDS['HID'],
        'rx_char': BLE_CHAR_UUIDS['HID_REPORT'],
        'tx_char': None,
    },
    'Honeywell Granit 1991i': {
        'manufacturer': 'Honeywell',
        'service_uuid': BLE_SERVICE_UUIDS['HID'],
        'rx_char': BLE_CHAR_UUIDS['HID_REPORT'],
        'tx_char': None,
    },
    'Datalogic QBT2430-HC': {
        'manufacturer': 'Datalogic',
        'service_uuid': BLE_SERVICE_UUIDS['HID'],
        'rx_char': BLE_CHAR_UUIDS['HID_REPORT'],
        'tx_char': None,
    },
    'Datalogic GM4400-HC': {
        'manufacturer': 'Datalogic',
        'service_uuid': BLE_SERVICE_UUIDS['HID'],
        'rx_char': BLE_CHAR_UUIDS['HID_REPORT'],
        'tx_char': None,
    },
    'Inateck BCST-70 BLE': {
        'manufacturer': 'Inateck',
        'service_uuid': BLE_SERVICE_UUIDS['NORDIC_UART'],
        'rx_char': BLE_CHAR_UUIDS['NORDIC_RX'],
        'tx_char': BLE_CHAR_UUIDS['NORDIC_TX'],
    },
    'Inateck BCST-52 BLE': {
        'manufacturer': 'Inateck',
        'service_uuid': BLE_SERVICE_UUIDS['NORDIC_UART'],
        'rx_char': BLE_CHAR_UUIDS['NORDIC_RX'],
        'tx_char': BLE_CHAR_UUIDS['NORDIC_TX'],
    },
    'Eyoyo EY-042 BLE': {
        'manufacturer': 'Eyoyo',
        'service_uuid': BLE_SERVICE_UUIDS['NORDIC_UART'],
        'rx_char': BLE_CHAR_UUIDS['NORDIC_RX'],
        'tx_char': BLE_CHAR_UUIDS['NORDIC_TX'],
    },
    'Eyoyo EY-031 BLE': {
        'manufacturer': 'Eyoyo',
        'service_uuid': BLE_SERVICE_UUIDS['NORDIC_UART'],
        'rx_char': BLE_CHAR_UUIDS['NORDIC_RX'],
        'tx_char': BLE_CHAR_UUIDS['NORDIC_TX'],
    },
}

# Group BLE by manufacturer for dropdowns
BLE_MANUFACTURERS: dict = {}
for _model, _info in BLE_SCANNER_DATABASE.items():
    BLE_MANUFACTURERS.setdefault(_info['manufacturer'], []).append(_model)

# ============================================================================
# THREAD-SAFE UI QUEUE
# ============================================================================

class ThreadSafeUI:
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

    def schedule(self, callback):
        self.queue.put(callback)


# ============================================================================
# SCAN RESULT DATA CLASS
# ============================================================================

@dataclass
class ScanResult:
    timestamp: datetime
    barcode: str
    symbology: str
    scanner_type: str
    scanner_model: str = ""
    port: str = ""
    batch_id: str = ""
    sample_id: str = ""
    context: str = ""
    notes: str = ""

    def to_dict(self) -> Dict[str, str]:
        return {
            'Timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'Barcode': self.barcode,
            'Symbology': self.symbology,
            'Scanner_Type': self.scanner_type,
            'Scanner_Model': self.scanner_model,
            'Port': self.port,
            'Batch_ID': self.batch_id,
            'Sample_ID': self.sample_id,
            'Context': self.context,
            'Notes': self.notes
        }


# ============================================================================
# SYMBOLOGY DETECTION
# ============================================================================

def detect_symbology(barcode: str) -> str:
    """Detect barcode symbology from pattern"""
    if not barcode:
        return "UNKNOWN"

    if barcode.startswith(('http://', 'https://', 'www.')) and len(barcode) > 20:
        return "QR_CODE"

    if barcode.isdigit():
        if len(barcode) == 12:
            return "UPC-A"
        elif len(barcode) == 13:
            return "EAN-13"
        elif len(barcode) == 8:
            return "EAN-8"
        elif len(barcode) == 6:
            return "UPC-E"
        elif len(barcode) in [14, 16, 20]:
            return "ITF-14"
        else:
            return "CODE128"

    if barcode.startswith('*') and barcode.endswith('*'):
        return "CODE39"

    return "CODE128"


# ============================================================================
# FOCUSED SCANNER (USB HID Keyboard Emulation)
# ============================================================================

class FocusedScanner:
    """USB HID Keyboard scanner - works with focused Tkinter fields"""

    def __init__(self, callback: Callable):
        self.callback = callback
        self.buffer = ""
        self.last_char_time = time.time()
        self.timeout = 0.5
        self.connected = True
        self.model = "USB HID Keyboard Scanner"

    def process_key(self, key: str) -> Optional[str]:
        now = time.time()
        if now - self.last_char_time > self.timeout:
            self.buffer = ""

        if key in ('\r', '\n', '<Return>'):
            if self.buffer:
                barcode = self.buffer
                self.buffer = ""
                return barcode
        elif len(key) == 1:
            self.buffer += key
            self.last_char_time = now
        return None

    def disconnect(self):
        self.connected = False


# ============================================================================
# USB SERIAL SCANNER
# ============================================================================

class USBSerialScanner:
    """USB Serial / RS-232 scanner with background thread"""

    COMMON_BAUDS = [9600, 19200, 38400, 57600, 115200]

    def __init__(self, port: str, baudrate: int, callback: Callable, ui_queue: ThreadSafeUI):
        self.port = port
        self.baudrate = baudrate
        self.callback = callback
        self.ui_queue = ui_queue
        self.serial = None
        self.running = False
        self.thread = None
        self.model = f"Serial Scanner ({port})"

    def connect(self) -> Tuple[bool, str]:
        if not DEPS['pyserial']:
            return False, "pyserial not installed"

        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=8,
                parity='N',
                stopbits=1,
                timeout=0.1
            )
            return True, f"Connected to {self.port} at {self.baudrate} baud"
        except Exception as e:
            return False, str(e)

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        buffer = ""
        while self.running and self.serial:
            try:
                if self.serial.in_waiting:
                    data = self.serial.read(self.serial.in_waiting)
                    text = data.decode('utf-8', errors='ignore')

                    for ch in text:
                        if ch.isprintable():
                            buffer += ch
                        elif ch in ('\r', '\n') and buffer:
                            barcode = buffer.strip()
                            if barcode:
                                self.callback(barcode, 'SERIAL', self.model)
                            buffer = ""
                time.sleep(0.01)
            except:
                time.sleep(0.1)

    def stop(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)
        if self.serial and self.serial.is_open:
            self.serial.close()

    def disconnect(self):
        self.stop()


# ============================================================================
# BLUETOOTH SPP SCANNER
# ============================================================================

class BluetoothSPPScanner(USBSerialScanner):
    """Bluetooth SPP scanner - same as serial but with device discovery"""

    def __init__(self, port: str, baudrate: int, callback: Callable, ui_queue: ThreadSafeUI):
        super().__init__(port, baudrate, callback, ui_queue)
        self.model = f"Bluetooth SPP ({port})"

    @classmethod
    def discover_ports(cls) -> List[Dict]:
        ports = []
        if not DEPS['pyserial']:
            return ports

        try:
            for p in serial.tools.list_ports.comports():
                desc = p.description.lower()
                hwid = p.hwid.lower()

                if ('bluetooth' in desc or 'rfcomm' in desc or
                    'bth' in hwid or 'blue' in desc):

                    model_info = cls._identify_model(p.description)

                    ports.append({
                        'port': p.device,
                        'description': p.description,
                        'model': model_info['model'],
                        'manufacturer': model_info['manufacturer'],
                        'default_baud': model_info['default_baud']
                    })
        except:
            pass

        return ports

    @classmethod
    def _identify_model(cls, name: str) -> Dict:
        name_lower = name.lower()

        for model, info in BLUETOOTH_SPP_MODELS.items():
            if model.lower() in name_lower:
                return {
                    'model': model,
                    'manufacturer': info['manufacturer'],
                    'default_baud': info['default_baud']
                }

        if 'zebra' in name_lower or 'symbol' in name_lower or 'motorola' in name_lower:
            return {'model': 'Zebra/Symbol', 'manufacturer': 'Zebra', 'default_baud': 9600}
        if 'honeywell' in name_lower:
            return {'model': 'Honeywell', 'manufacturer': 'Honeywell', 'default_baud': 9600}
        if 'datalogic' in name_lower:
            return {'model': 'Datalogic', 'manufacturer': 'Datalogic', 'default_baud': 9600}
        if 'inateck' in name_lower:
            return {'model': 'Inateck', 'manufacturer': 'Inateck', 'default_baud': 9600}
        if 'eyoyo' in name_lower:
            return {'model': 'Eyoyo', 'manufacturer': 'Eyoyo', 'default_baud': 9600}
        if 'socket' in name_lower:
            return {'model': 'Socket', 'manufacturer': 'Socket', 'default_baud': 9600}

        return {'model': 'Bluetooth SPP', 'manufacturer': 'Unknown', 'default_baud': 9600}


# ============================================================================
# BLUETOOTH LE SCANNER
# ============================================================================

class BluetoothLEScanner:
    """Bluetooth LE scanner using bleak"""

    def __init__(self, address: str, model_info: Dict, callback: Callable, ui_queue: ThreadSafeUI):
        self.address = address
        self.model_info = model_info
        self.model = model_info.get('model', 'Unknown BLE Device')
        self.manufacturer = model_info.get('manufacturer', 'Unknown')
        self.callback = callback
        self.ui_queue = ui_queue
        self.client = None
        self.running = False
        self.thread = None
        self.connected = False
        self.characteristic_uuid = None
        self.buffer = ""

    async def connect_async(self) -> Tuple[bool, str]:
        """Async connection to BLE device"""
        try:
            self.client = BleakClient(self.address)
            await self.client.connect()

            if not self.client.is_connected:
                return False, "Failed to connect"

            # Discover services
            services = await self.client.get_services()

            # Try to find the right characteristic
            # First check if we have a known UUID from database
            if self.model_info.get('rx_char'):
                self.characteristic_uuid = self.model_info['rx_char']
            else:
                # Fallback: look for any characteristic with notify or read
                for service in services:
                    for char in service.characteristics:
                        if 'notify' in char.properties or 'read' in char.properties:
                            self.characteristic_uuid = char.uuid
                            break
                    if self.characteristic_uuid:
                        break

            if not self.characteristic_uuid:
                return False, "No suitable characteristic found"

            return True, f"Connected to {self.model}"

        except Exception as e:
            return False, str(e)

    def connect(self) -> Tuple[bool, str]:
        """Synchronous wrapper for connect_async"""
        if not DEPS['bleak']:
            return False, "bleak not installed"

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(self.connect_async())
        loop.close()
        return result

    def start(self):
        """Start notification handler"""
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        """Background thread for BLE notifications - thread-safe version"""
        if not self.client or not self.characteristic_uuid:
            return

        def notification_handler(sender, data):
            """Handle incoming BLE data"""
            try:
                text = data.decode('utf-8', errors='ignore')
                for ch in text:
                    if ch.isprintable():
                        self.buffer += ch
                    elif ch in ('\r', '\n') and self.buffer:
                        barcode = self.buffer.strip()
                        if barcode:
                            self.callback(barcode, 'BLE', self.model)
                        self.buffer = ""
            except:
                pass

        async def notification_loop():
            """Async setup with proper cleanup"""
            await self.client.start_notify(self.characteristic_uuid, notification_handler)
            try:
                while self.running:
                    await asyncio.sleep(0.1)
            finally:
                await self.client.stop_notify(self.characteristic_uuid)

        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(notification_loop())
        except Exception as e:
            # Schedule error message on UI thread
            if self.ui_queue:
                self.ui_queue.schedule(lambda: messagebox.showerror("BLE Error", f"Connection lost: {str(e)}"))
        finally:
            loop.close()

    def stop(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)

    def disconnect(self):
        self.stop()
        if self.client:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.client.disconnect())
            loop.close()
            self.client = None
        self.connected = False


# ============================================================================
# WEBCAM SCANNER
# ============================================================================

class WebcamScanner:
    """Webcam-based QR/barcode scanner"""

    def __init__(self, camera_id: int, callback: Callable, ui_queue: ThreadSafeUI,
                 preview_queue: Optional[queue.Queue] = None):
        self.camera_id = camera_id
        self.callback = callback
        self.ui_queue = ui_queue
        self.preview_queue = preview_queue
        self.cap = None
        self.running = False
        self.thread = None
        self.model = f"Webcam (Camera {camera_id})"
        self.cooldown = {}

    def connect(self) -> Tuple[bool, str]:
        if not DEPS['opencv'] or not DEPS['pyzbar']:
            return False, "OpenCV or pyzbar not installed"

        try:
            self.cap = cv2.VideoCapture(self.camera_id)
            if self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.cap.set(cv2.CAP_PROP_FPS, 15)
                return True, f"Camera {self.camera_id} opened"
            return False, f"Could not open camera {self.camera_id}"
        except Exception as e:
            return False, str(e)

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        while self.running and self.cap:
            try:
                ret, frame = self.cap.read()
                if not ret:
                    time.sleep(0.1)
                    continue

                try:
                    barcodes = pyzbar.decode(frame)
                    for barcode in barcodes:
                        data = barcode.data.decode('utf-8')
                        barcode_type = barcode.type

                        now = time.time()
                        if now - self.cooldown.get(data, 0) < 2.0:
                            continue
                        self.cooldown[data] = now

                        x, y, w, h = barcode.rect
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                        self.callback(data, barcode_type, self.model)
                except:
                    pass

                if self.preview_queue is not None:
                    try:
                        h, w = frame.shape[:2]
                        max_h = 200
                        if h > max_h:
                            scale = max_h / h
                            new_w = int(w * scale)
                            frame = cv2.resize(frame, (new_w, max_h))

                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                        if self.preview_queue.qsize() < 3:
                            self.preview_queue.put(frame_rgb.copy())
                    except:
                        pass

                time.sleep(0.03)
            except:
                time.sleep(0.1)

    def stop(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)
        if self.cap:
            self.cap.release()

    def disconnect(self):
        self.stop()


# ============================================================================
# CONFIG MANAGER
# ============================================================================

class ConfigManager:
    def __init__(self):
        self.config_dir = Path.home() / ".barcode_scanner"
        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / "settings.json"
        self.settings = self._load()

    def _defaults(self):
        return {
            'beep_on_scan': True,
            'auto_clear': True,
            'preview_enabled': True,
            'last_tab': 'USB HID'
        }

    def _load(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return self._defaults()

    def save(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except:
            pass

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings[key] = value
        self.save()


# ============================================================================
# DEPENDENCY INSTALLATION
# ============================================================================

def install_dependencies(parent, plugin_name: str, packages: List[str]):
    """Install pip packages in a separate window"""
    win = tk.Toplevel(parent)
    win.title(f"📦 Installing: {plugin_name}")
    win.geometry("600x400")
    win.transient(parent)

    header = tk.Frame(win, bg="#3498db", height=32)
    header.pack(fill=tk.X)
    header.pack_propagate(False)
    tk.Label(header, text=f"pip install {' '.join(packages)}",
            font=("Consolas", 9), bg="#3498db", fg="white").pack(pady=6)

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
            text.insert(tk.END, "\n✅ SUCCESS! Dependencies installed.\n")
            text.insert(tk.END, "Restart the plugin to use new features.\n")
            win.after(3000, win.destroy)
        else:
            text.insert(tk.END, f"\n❌ FAILED (code {proc.returncode})\n")

    threading.Thread(target=run, daemon=True).start()


# ============================================================================
# SETTINGS DIALOG
# ============================================================================

class SettingsDialog:
    def __init__(self, parent, config, beep_var, auto_clear_var, preview_var):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("⚙️ Scanner Settings")
        self.dialog.geometry("300x200")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.config = config
        self.beep_var = beep_var
        self.auto_clear_var = auto_clear_var
        self.preview_var = preview_var

        self._build_ui()
        self._center_window()

    def _build_ui(self):
        main = tk.Frame(self.dialog, bg="white", padx=20, pady=20)
        main.pack(fill=tk.BOTH, expand=True)

        tk.Label(main, text="Scanner Settings", font=("Arial", 12, "bold"),
                bg="white", fg="#27ae60").pack(pady=(0,10))

        self.beep_cb = tk.Checkbutton(main, text="Beep on scan",
                                       variable=self.beep_var,
                                       bg="white")
        self.beep_cb.pack(anchor=tk.W, pady=2)

        self.auto_cb = tk.Checkbutton(main, text="Auto-clear after send",
                                       variable=self.auto_clear_var,
                                       bg="white")
        self.auto_cb.pack(anchor=tk.W, pady=2)

        self.preview_cb = tk.Checkbutton(main, text="Enable preview",
                                          variable=self.preview_var,
                                          bg="white")
        self.preview_cb.pack(anchor=tk.W, pady=2)

        btn_frame = tk.Frame(main, bg="white")
        btn_frame.pack(fill=tk.X, pady=(20,0))

        tk.Button(btn_frame, text="Save", command=self._save,
                  bg="#27ae60", fg="white", width=10).pack(side=tk.RIGHT, padx=2)
        tk.Button(btn_frame, text="Cancel", command=self.dialog.destroy,
                  bg="#95a5a6", fg="white", width=10).pack(side=tk.RIGHT, padx=2)

    def _save(self):
        self.config.set('beep_on_scan', self.beep_var.get())
        self.config.set('auto_clear', self.auto_clear_var.get())
        self.config.set('preview_enabled', self.preview_var.get())
        self.dialog.destroy()

    def _center_window(self):
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")


# ============================================================================
# MAIN PLUGIN
# ============================================================================

class BarcodeScannerUnifiedSuitePlugin:

    def __init__(self, main_app):
        self.app = main_app
        self.window = None
        self.ui_queue = None
        self.preview_queue = queue.Queue(maxsize=5)
        self.config = ConfigManager()
        self.saved_context = {}  # For context persistence

        # Dependency status
        self.deps = DEPS

        # Check core deps at startup
        if not self.deps['numpy'] or not self.deps['pandas']:
            missing = []
            if not self.deps['numpy']: missing.append("numpy")
            if not self.deps['pandas']: missing.append("pandas")
            messagebox.showerror(
                "Missing Dependencies",
                f"Core dependencies missing:\n{', '.join(missing)}\n\n"
                f"Please install via plugin manager or:\npip install {' '.join(missing)}"
            )
            return

        # Scan history
        self.scans: List[ScanResult] = []
        self.current_scan: Optional[ScanResult] = None

        # Scanner instances
        self._disconnecting = False
        self.focused_scanner = None
        self.serial_scanner = None
        self.bluetooth_spp_scanner = None
        self.bluetooth_le_scanner = None
        self.webcam_scanner = None
        self.active_scanner = None
        self.active_type = ""

        # UI Variables
        self.status_var = tk.StringVar(value="Barcode Scanner Unified Suite v2.4 - Ready")
        self.last_scan_var = tk.StringVar(value="---")
        self.scan_count_var = tk.StringVar(value="0 scans")
        self.progress_var = tk.DoubleVar(value=0)

        # Settings
        self.auto_clear_var = tk.BooleanVar(value=self.config.get('auto_clear', True))
        self.beep_var = tk.BooleanVar(value=self.config.get('beep_on_scan', True))
        self.preview_var = tk.BooleanVar(value=self.config.get('preview_enabled', True))

        # Tab buttons
        self.tab_buttons = []
        self.tab_var = tk.StringVar(value=self.config.get('last_tab', 'USB HID'))

        # UI Elements
        self.left_panel = None
        self.left_panel_content = None
        self.right_panel = None
        self.preview_frame = None
        self.preview_label = None
        self.preview_image = None
        self.log_listbox = None
        self.status_progress = None
        self.progress_label = None
        self.conn_indicator = None  # Connection status indicator

        # Device controls
        self.focused_entry = None
        self.manual_var = None
        self.context_vars = {}

        # Serial controls
        self.serial_port_combo = None
        self.serial_baud_combo = None
        self.serial_connect_btn = None
        self.serial_status = None

        # Bluetooth SPP controls
        self.bt_spp_manufacturer_combo = None
        self.bt_spp_model_combo = None
        self.bt_spp_port_combo = None
        self.bt_spp_baud_combo = None
        self.bt_spp_connect_btn = None
        self.bt_spp_info = None
        self.bt_spp_devices = []

        # Bluetooth LE controls
        self.ble_scan_btn = None
        self.ble_device_list = None
        self.ble_connect_btn = None
        self.ble_info = None
        self.ble_devices = []
        self.filtered_ble_devices = []
        self.ble_manufacturer_combo = None
        self.ble_model_combo = None
        self.selected_ble_device = None
        self._scanning = False
        self._scan_anim_count = 0

        # Webcam controls
        self.webcam_combo = None
        self.webcam_connect_btn = None
        self.webcam_status = None

        self._processing = False

    def show_interface(self):
        self.open_window()

    def open_window(self):
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("Barcode/QR Scanner Unified Suite v2.4")
        self.window.geometry("1000x650")
        self.window.minsize(900, 600)
        self.window.transient(self.app.root)

        self.ui_queue = ThreadSafeUI(self.window)
        self._build_ui()

        self.window.bind('<Key>', self._on_key_press)
        self.window.bind('<Control-c>', lambda e: self._copy_last_scan())
        self.window.bind('<Control-t>', lambda e: self.send_to_table())
        self.window.bind('<Control-l>', lambda e: self._clear_log())

        self._start_processor()
        self.window.lift()
        self.window.focus_force()
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        # Header with settings gear and connection indicator
        header = tk.Frame(self.window, bg="#27ae60", height=40)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="📷", font=("Arial", 16),
                bg="#27ae60", fg="white").pack(side=tk.LEFT, padx=8)
        tk.Label(header, text="Barcode/QR Scanner Unified", font=("Arial", 12, "bold"),
                bg="#27ae60", fg="white").pack(side=tk.LEFT, padx=2)
        tk.Label(header, text="v2.4 · POLISHED", font=("Arial", 8),
                bg="#27ae60", fg="#f1c40f").pack(side=tk.LEFT, padx=8)

        # Connection indicator
        self.conn_indicator = tk.Label(header, text="⚪ Disconnected",
                                       font=("Arial", 8, "bold"),
                                       bg="#27ae60", fg="#e74c3c")
        self.conn_indicator.pack(side=tk.RIGHT, padx=10)

        # Settings gear button
        tk.Button(header, text="⚙️", font=("Arial", 14),
                 bg="#27ae60", fg="white", bd=0,
                 command=self._show_settings).pack(side=tk.RIGHT, padx=10)

        self.status_indicator = tk.Label(header, textvariable=self.status_var,
                                        font=("Arial", 8), bg="#27ae60", fg="#2ecc71")
        self.status_indicator.pack(side=tk.RIGHT, padx=10)

        # Full-width tabs - 5 TABS
        tab_frame = tk.Frame(self.window, bg="#f8f9fa", height=35)
        tab_frame.pack(fill=tk.X)
        tab_frame.pack_propagate(False)

        tabs = [("⌨️ USB HID", "USB HID"),
                ("🔌 USB Serial", "USB Serial"),
                ("📱 Bluetooth SPP", "Bluetooth SPP"),
                ("📡 Bluetooth LE", "Bluetooth LE"),
                ("📹 Webcam", "Webcam")]

        self.tab_buttons = []
        for display, value in tabs:
            btn = tk.Button(tab_frame, text=display,
                           bg="#27ae60" if self.tab_var.get() == value else "#f8f9fa",
                           fg="white" if self.tab_var.get() == value else "black",
                           relief=tk.FLAT, padx=15, pady=5,
                           command=lambda v=value: self._switch_tab(v))
            btn.pack(side=tk.LEFT, padx=1, pady=2)
            self.tab_buttons.append(btn)

        # Main split
        main = tk.PanedWindow(self.window, orient=tk.HORIZONTAL, sashwidth=4)
        main.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left panel
        self.left_panel = tk.Frame(main, bg="white", width=380)
        main.add(self.left_panel, width=380)
        self.left_panel_content = tk.Frame(self.left_panel, bg="white")
        self.left_panel_content.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Right panel
        self.right_panel = tk.Frame(main, bg="white")
        main.add(self.right_panel)
        self._build_right_panel()

        # Status bar
        self._build_status_bar()

        self._switch_tab(self.tab_var.get())

    def _build_right_panel(self):
        """Build the universal right panel with preview + log - now with dynamic sizing"""

        # Use PanedWindow to allow user to adjust split between preview and log
        right_paned = ttk.PanedWindow(self.right_panel, orient=tk.VERTICAL)
        right_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # ============ PREVIEW SECTION (Top - expands both ways) ============
        preview_container = tk.Frame(right_paned, bg="white")
        right_paned.add(preview_container, weight=2)  # Preview gets 2/3 of space by default

        # Preview label
        tk.Label(preview_container, text="🔍 Live Preview", font=("Arial", 8, "bold"),
                bg="white", anchor=tk.W).pack(fill=tk.X, pady=(0,2))

        # Preview frame that maintains square aspect ratio
        preview_frame_container = tk.Frame(preview_container, bg="white")
        preview_frame_container.pack(fill=tk.BOTH, expand=True)

        self.preview_frame = tk.Frame(preview_frame_container, bg="black")
        self.preview_frame.pack(expand=True, fill=tk.BOTH)

        # Preview label (will show video or instructions)
        self.preview_label = tk.Label(self.preview_frame, bg="black", fg="white",
                                    text="Preview", font=("Arial", 10))
        self.preview_label.pack(fill=tk.BOTH, expand=True)

        # ============ LOG SECTION (Bottom - fixed height but can be resized) ============
        log_container = tk.Frame(right_paned, bg="white")
        right_paned.add(log_container, weight=1)  # Log gets 1/3 of space by default

        log_header = tk.Frame(log_container, bg="white")
        log_header.pack(fill=tk.X)

        tk.Label(log_header, text="📋 Scan Log", font=("Arial", 8, "bold"),
                bg="white").pack(side=tk.LEFT)

        # Log control buttons
        tk.Button(log_header, text="📋 Copy All", command=self._copy_all_log,
                bg="white", bd=0, font=("Arial", 7), fg="#3498db",
                cursor="hand2").pack(side=tk.RIGHT, padx=2)
        tk.Button(log_header, text="🗑️ Clear", command=self._clear_log,
                bg="white", bd=0, font=("Arial", 7), fg="#e74c3c",
                cursor="hand2").pack(side=tk.RIGHT, padx=2)
        tk.Label(log_header, text="(right-click to copy)", font=("Arial", 7),
                bg="white", fg="#7f8c8d").pack(side=tk.RIGHT, padx=5)

        # Log listbox with scrollbar
        log_frame = tk.Frame(log_container, bg="white")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(2,0))

        self.log_listbox = tk.Listbox(log_frame, font=("Courier", 9))
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_listbox.yview)
        self.log_listbox.configure(yscrollcommand=scrollbar.set)
        self.log_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_listbox.bind('<Button-3>', self._on_log_right_click)

    def _build_status_bar(self):
        status = tk.Frame(self.window, bg="#34495e", height=24)
        status.pack(fill=tk.X, side=tk.BOTTOM)
        status.pack_propagate(False)

        self.status_text = tk.Label(status, textvariable=self.status_var,
                                    font=("Arial", 7), bg="#34495e", fg="white")
        self.status_text.pack(side=tk.LEFT, padx=8)

        progress_frame = tk.Frame(status, bg="#34495e")
        progress_frame.pack(side=tk.RIGHT, padx=8)

        self.status_progress = ttk.Progressbar(progress_frame, variable=self.progress_var,
                                               mode='determinate', length=150)
        self.status_progress.pack(side=tk.LEFT)

        self.progress_label = tk.Label(progress_frame, text="0%", font=("Arial", 7),
                                       bg="#34495e", fg="#bdc3c7")
        self.progress_label.pack(side=tk.LEFT, padx=5)

        self.last_scan_label = tk.Label(status, textvariable=self.last_scan_var,
                                        font=("Arial", 7), bg="#34495e", fg="#bdc3c7")
        self.last_scan_label.pack(side=tk.LEFT, padx=20)

    def _show_settings(self):
        SettingsDialog(self.window, self.config,
                      self.beep_var, self.auto_clear_var, self.preview_var)

    def _on_preview_resize(self, event):
        size = min(event.width, event.height)
        size = max(200, min(400, size))
        self.preview_frame.config(width=size, height=size)

    def _on_log_right_click(self, event):
        try:
            index = self.log_listbox.nearest(event.y)
            line = self.log_listbox.get(index)
            if '] ' in line:
                barcode = line.split('] ', 1)[1]
                self.window.clipboard_clear()
                self.window.clipboard_append(barcode)
                self.status_var.set(f"Copied: {barcode[:30]}")
        except:
            pass

    def _copy_last_scan(self):
        """Copy last scan to clipboard (Ctrl+C)"""
        if self.scans:
            last = self.scans[-1]
            self.window.clipboard_clear()
            self.window.clipboard_append(last.barcode)
            self.status_var.set(f"Copied last scan: {last.barcode[:30]}")

    def _copy_all_log(self):
        """Copy entire log to clipboard"""
        items = self.log_listbox.get(0, tk.END)
        if items:
            text = '\n'.join(items)
            self.window.clipboard_clear()
            self.window.clipboard_append(text)
            self.status_var.set(f"Copied {len(items)} scans")

    def _clear_log(self):
        """Clear the scan log"""
        self.log_listbox.delete(0, tk.END)
        self.status_var.set("Log cleared")

    def _update_connection_status(self, connected=True):
        """Update connection indicator with color"""
        if connected:
            self.conn_indicator.config(text="🟢 Connected", fg="#2ecc71")
        else:
            self.conn_indicator.config(text="⚪ Disconnected", fg="#e74c3c")

    def _rssi_to_bars(self, rssi: int) -> str:
        """Convert RSSI to signal strength bars"""
        if rssi > -50:
            return "📶📶📶"  # Excellent
        elif rssi > -65:
            return "📶📶"    # Good
        elif rssi > -80:
            return "📶"      # Fair
        else:
            return "📶-"     # Poor

    def _update_progress(self, value, text=None):
        """Update progress bar with optional text"""
        self.progress_var.set(value)
        if text:
            self.progress_label.config(text=text)

    def _animate_scanning(self):
        """Animation for BLE scanning"""
        if not self._scanning:
            return
        frames = ["🔍", "🔍.", "🔍..", "🔍..."]
        self._scan_anim_count += 1
        frame = frames[self._scan_anim_count % 4]
        self.ble_scan_btn.config(text=f"{frame} Scanning")
        self.window.after(300, self._animate_scanning)

    def _save_context(self):
        """Save context field values"""
        for key, var in self.context_vars.items():
            self.saved_context[key] = var.get()

    def _restore_context(self):
        """Restore context field values"""
        if hasattr(self, 'saved_context'):
            for key, value in self.saved_context.items():
                if key in self.context_vars:
                    self.context_vars[key].set(value)

    def _switch_tab(self, tab_name):
        # Save current context before switching
        self._save_context()

        self.tab_var.set(tab_name)
        self.config.set('last_tab', tab_name)

        for btn in self.tab_buttons:
            if tab_name in btn.cget('text'):
                btn.config(bg="#27ae60", fg="white")
            else:
                btn.config(bg="#f8f9fa", fg="black")

        for widget in self.left_panel_content.winfo_children():
            widget.destroy()

        self.context_vars = {}

        if tab_name == "USB HID":
            self._build_hid_controls()
            self._activate_hid_scanner()
        elif tab_name == "USB Serial":
            self._build_serial_controls()
        elif tab_name == "Bluetooth SPP":
            self._build_bluetooth_spp_controls()
        elif tab_name == "Bluetooth LE":
            self._build_bluetooth_le_controls()
        elif tab_name == "Webcam":
            self._build_webcam_controls()

        # Restore context if available
        self._restore_context()
        self._update_preview_for_device(tab_name)

    def _build_hid_controls(self):
        tk.Label(self.left_panel_content, text="⌨️ USB HID Keyboard Scanner",
                font=("Arial", 10, "bold"), bg="white", fg="#27ae60").pack(anchor=tk.W, pady=5)

        instr = tk.Label(self.left_panel_content,
                        text="Click in the field below and scan.\nScanner acts like a keyboard.",
                        font=("Arial", 8), bg="white", fg="#555", justify=tk.LEFT)
        instr.pack(anchor=tk.W, pady=5)

        tk.Label(self.left_panel_content, text="Scan Field:", font=("Arial", 8, "bold"),
                bg="white").pack(anchor=tk.W, pady=(10,2))

        self.focused_entry = tk.Entry(self.left_panel_content, font=("Arial", 10),
                                      bg="#f0f8ff")
        self.focused_entry.pack(fill=tk.X, pady=2, ipady=3)
        self.focused_entry.bind('<FocusIn>', lambda e: self.focused_entry.delete(0, tk.END))
        ToolTip(self.focused_entry, "Click here, then scan - barcode appears when you press Enter")

        self._build_manual_entry()
        self._build_context_fields()

    def _build_serial_controls(self):
        tk.Label(self.left_panel_content, text="🔌 USB Serial Scanner",
                font=("Arial", 10, "bold"), bg="white", fg="#27ae60").pack(anchor=tk.W, pady=5)

        if not self.deps['pyserial']:
            self._show_install_button("pyserial", ["pyserial"])
            return

        tk.Label(self.left_panel_content, text="Port:", font=("Arial", 8, "bold"),
                bg="white").pack(anchor=tk.W, pady=(10,2))

        port_frame = tk.Frame(self.left_panel_content, bg="white")
        port_frame.pack(fill=tk.X, pady=2)

        self.serial_port_combo = ttk.Combobox(port_frame, width=20)
        self.serial_port_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ToolTip(self.serial_port_combo, "Select the COM port your scanner is connected to")
        tk.Button(port_frame, text="⟳", command=self._refresh_serial_ports,
                 width=2).pack(side=tk.RIGHT, padx=(2,0))

        tk.Label(self.left_panel_content, text="Baud Rate:", font=("Arial", 8, "bold"),
                bg="white").pack(anchor=tk.W, pady=(5,2))

        self.serial_baud_combo = ttk.Combobox(self.left_panel_content,
                                              values=["9600", "19200", "38400", "57600", "115200"],
                                              width=10)
        self.serial_baud_combo.set("9600")
        self.serial_baud_combo.pack(anchor=tk.W, pady=2)
        ToolTip(self.serial_baud_combo, "Baud rate must match scanner setting (usually 9600)")

        self.serial_connect_btn = tk.Button(self.left_panel_content, text="🔌 Connect",
                                            command=self._connect_serial,
                                            bg="#27ae60", fg="white", font=("Arial", 9, "bold"),
                                            height=1)
        self.serial_connect_btn.pack(fill=tk.X, pady=10)
        ToolTip(self.serial_connect_btn, "Connect to selected serial port")

        self.serial_status = tk.Label(self.left_panel_content, text="⚪ Not Connected",
                                      font=("Arial", 8), bg="white", fg="#e74c3c")
        self.serial_status.pack(anchor=tk.W)

        self._build_manual_entry()
        self._build_context_fields()
        self._refresh_serial_ports()

    def _build_bluetooth_spp_controls(self):
        tk.Label(self.left_panel_content, text="📱 Bluetooth SPP Scanner (50+ models)",
                font=("Arial", 10, "bold"), bg="white", fg="#27ae60").pack(anchor=tk.W, pady=5)

        if not self.deps['pyserial']:
            self._show_install_button("pyserial", ["pyserial"])
            return

        # Pairing helper
        pair_frame = tk.Frame(self.left_panel_content, bg="white")
        pair_frame.pack(fill=tk.X, pady=5)
        tk.Button(pair_frame, text="🔓 Open Bluetooth Settings",
                 command=self._open_bluetooth_settings,
                 bg="#3498db", fg="white", width=20).pack()
        ToolTip(pair_frame, "Open system Bluetooth settings to pair your scanner")
        tk.Label(pair_frame, text="(Pair your scanner first, then refresh)",
                font=("Arial", 7), bg="white", fg="#7f8c8d").pack()

        # Manufacturer
        tk.Label(self.left_panel_content, text="Manufacturer:", font=("Arial", 8, "bold"),
                bg="white").pack(anchor=tk.W, pady=(10,2))

        self.bt_spp_manufacturer_combo = ttk.Combobox(self.left_panel_content,
                                                  values=list(SPP_MANUFACTURERS.keys()),
                                                  width=30)
        self.bt_spp_manufacturer_combo.pack(fill=tk.X, pady=2)
        self.bt_spp_manufacturer_combo.bind('<<ComboboxSelected>>', self._on_bt_spp_manufacturer_select)
        ToolTip(self.bt_spp_manufacturer_combo, "Select your scanner manufacturer")

        # Model
        tk.Label(self.left_panel_content, text="Model:", font=("Arial", 8, "bold"),
                bg="white").pack(anchor=tk.W, pady=(5,2))

        self.bt_spp_model_combo = ttk.Combobox(self.left_panel_content, width=30)
        self.bt_spp_model_combo.pack(fill=tk.X, pady=2)
        self.bt_spp_model_combo.bind('<<ComboboxSelected>>', self._on_bt_spp_model_select)
        ToolTip(self.bt_spp_model_combo, "Select your specific model")

        # Port
        tk.Label(self.left_panel_content, text="Port:", font=("Arial", 8, "bold"),
                bg="white").pack(anchor=tk.W, pady=(5,2))

        port_frame = tk.Frame(self.left_panel_content, bg="white")
        port_frame.pack(fill=tk.X, pady=2)

        self.bt_spp_port_combo = ttk.Combobox(port_frame, width=25)
        self.bt_spp_port_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ToolTip(self.bt_spp_port_combo, "Select the COM port for your paired scanner")
        tk.Button(port_frame, text="⟳", command=self._refresh_bluetooth_spp_ports,
                 width=2).pack(side=tk.RIGHT, padx=(2,0))

        # Baud
        tk.Label(self.left_panel_content, text="Baud Rate:", font=("Arial", 8, "bold"),
                bg="white").pack(anchor=tk.W, pady=(5,2))

        self.bt_spp_baud_combo = ttk.Combobox(self.left_panel_content,
                                          values=["9600", "19200", "38400", "57600", "115200"],
                                          width=10)
        self.bt_spp_baud_combo.set("9600")
        self.bt_spp_baud_combo.pack(anchor=tk.W, pady=2)
        ToolTip(self.bt_spp_baud_combo, "Baud rate (auto-filled when model selected)")

        # Connect button
        self.bt_spp_connect_btn = tk.Button(self.left_panel_content, text="🔌 Connect Bluetooth",
                                        command=self._connect_bluetooth_spp,
                                        bg="#27ae60", fg="white", font=("Arial", 9, "bold"))
        self.bt_spp_connect_btn.pack(fill=tk.X, pady=10)
        ToolTip(self.bt_spp_connect_btn, "Connect to selected Bluetooth SPP device")

        # Device info
        self.bt_spp_info = tk.Label(self.left_panel_content, text="No device selected",
                                font=("Arial", 7), bg="white", fg="#555", justify=tk.LEFT)
        self.bt_spp_info.pack(anchor=tk.W, pady=2)

        # Linux rfcomm hint
        if IS_LINUX:
            tk.Label(self.left_panel_content,
                    text="💡 Linux: If no ports appear, run:\n  sudo rfcomm bind 0 <device_address>",
                    font=("Arial", 7), bg="white", fg="#e67e22", justify=tk.LEFT).pack(anchor=tk.W, pady=2)

        self._build_manual_entry()
        self._build_context_fields()
        self._refresh_bluetooth_spp_ports()

    def _build_bluetooth_le_controls(self):
        tk.Label(self.left_panel_content, text="📡 Bluetooth LE Scanner (20+ models)",
                font=("Arial", 10, "bold"), bg="white", fg="#27ae60").pack(anchor=tk.W, pady=5)

        if not self.deps['bleak']:
            self._show_install_button("bleak", ["bleak"])
            return

        # Manufacturer dropdown (optional filter)
        mfg_frame = tk.Frame(self.left_panel_content, bg="white")
        mfg_frame.pack(fill=tk.X, pady=2)

        tk.Label(mfg_frame, text="Filter by:", font=("Arial", 7),
                bg="white").pack(side=tk.LEFT, padx=2)

        self.ble_manufacturer_combo = ttk.Combobox(mfg_frame,
                                                   values=["All"] + list(BLE_MANUFACTURERS.keys()),
                                                   width=15, state="readonly")
        self.ble_manufacturer_combo.set("All")
        self.ble_manufacturer_combo.pack(side=tk.LEFT, padx=2)
        self.ble_manufacturer_combo.bind('<<ComboboxSelected>>', self._on_ble_filter_change)
        ToolTip(self.ble_manufacturer_combo, "Filter devices by manufacturer")

        # Scan button
        btn_frame = tk.Frame(self.left_panel_content, bg="white")
        btn_frame.pack(fill=tk.X, pady=5)

        self.ble_scan_btn = tk.Button(btn_frame, text="🔍 Scan for BLE Devices",
                                      command=self._scan_ble_devices,
                                      bg="#3498db", fg="white", width=20)
        self.ble_scan_btn.pack(side=tk.LEFT)
        ToolTip(self.ble_scan_btn, "Scan for nearby Bluetooth LE scanners")

        tk.Button(btn_frame, text="🔓 Pair Device",
                 command=self._open_bluetooth_settings,
                 bg="#95a5a6", fg="white", width=12).pack(side=tk.RIGHT)

        # Device list
        tk.Label(self.left_panel_content, text="Available Devices:", font=("Arial", 8, "bold"),
                bg="white").pack(anchor=tk.W, pady=(5,2))

        list_frame = tk.Frame(self.left_panel_content, bg="white")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=2)

        self.ble_device_list = tk.Listbox(list_frame, height=6, font=("Courier", 8))
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.ble_device_list.yview)
        self.ble_device_list.configure(yscrollcommand=scrollbar.set)

        self.ble_device_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.ble_device_list.bind('<<ListboxSelect>>', self._on_ble_device_select)

        # Connect button
        self.ble_connect_btn = tk.Button(self.left_panel_content, text="🔌 Connect Selected",
                                         command=self._connect_bluetooth_le,
                                         bg="#27ae60", fg="white", font=("Arial", 9, "bold"),
                                         state=tk.DISABLED)
        self.ble_connect_btn.pack(fill=tk.X, pady=10)
        ToolTip(self.ble_connect_btn, "Connect to selected BLE device")

        # Device info
        self.ble_info = tk.Label(self.left_panel_content, text="No device selected",
                                  font=("Arial", 7), bg="white", fg="#555", justify=tk.LEFT, height=3)
        self.ble_info.pack(anchor=tk.W, pady=2, fill=tk.X)

        self._build_manual_entry()
        self._build_context_fields()

        # Initial empty state
        self.ble_device_list.insert(tk.END, "✨ No devices found - click Scan")
        self.ble_device_list.itemconfig(0, fg="#7f8c8d")

    def _build_webcam_controls(self):
        tk.Label(self.left_panel_content, text="📹 Webcam Scanner",
                font=("Arial", 10, "bold"), bg="white", fg="#27ae60").pack(anchor=tk.W, pady=5)

        missing = []
        install_packages = []
        if not self.deps['opencv']:
            missing.append("opencv-python")
            install_packages.append("opencv-python")
        if not self.deps['pyzbar']:
            missing.append("pyzbar")
            install_packages.append("pyzbar")
        if not self.deps['pillow']:
            missing.append("pillow")
            install_packages.append("pillow")

        if missing:
            self._show_install_button("Webcam", install_packages, missing)
            return

        tk.Label(self.left_panel_content, text="Camera:", font=("Arial", 8, "bold"),
                bg="white").pack(anchor=tk.W, pady=(10,2))

        cam_frame = tk.Frame(self.left_panel_content, bg="white")
        cam_frame.pack(fill=tk.X, pady=2)

        self.webcam_combo = ttk.Combobox(cam_frame, values=["Camera 0", "Camera 1", "Camera 2"],
                                         width=15)
        self.webcam_combo.set("Camera 0")
        self.webcam_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ToolTip(self.webcam_combo, "Select camera device (0 = built-in, 1+ = external)")
        tk.Button(cam_frame, text="⟳", command=self._refresh_cameras,
                 width=2).pack(side=tk.RIGHT, padx=(2,0))

        btn_frame = tk.Frame(self.left_panel_content, bg="white")
        btn_frame.pack(fill=tk.X, pady=10)

        self.webcam_connect_btn = tk.Button(btn_frame, text="▶ Start Camera",
                                            command=self._connect_webcam,
                                            bg="#27ae60", fg="white", font=("Arial", 9, "bold"),
                                            width=15)
        self.webcam_connect_btn.pack(side=tk.LEFT)
        ToolTip(self.webcam_connect_btn, "Start webcam and begin scanning")

        self.webcam_status = tk.Label(btn_frame, text="⚪", fg="#e74c3c",
                                      font=("Arial", 10), bg="white")
        self.webcam_status.pack(side=tk.LEFT, padx=5)

        self._build_manual_entry()
        self._build_context_fields()

    def _install_and_refresh(self, feature: str, packages: List[str]):
        """Install dependencies directly to the current Python environment"""
        import sys
        import subprocess
        import os

        win = tk.Toplevel(self.window)
        win.title(f"📦 Installing: {feature}")
        win.geometry("600x400")
        win.transient(self.window)

        header = tk.Frame(win, bg="#f39c12", height=32)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text=f"Installing to: {sys.executable}",
                font=("Consolas", 8), bg="#f39c12", fg="white").pack(pady=2)
        tk.Label(header, text=f"pip install {' '.join(packages)}",
                font=("Consolas", 9), bg="#f39c12", fg="white").pack(pady=2)

        text = tk.Text(win, wrap=tk.WORD, font=("Consolas", 9),
                    bg="#1e1e1e", fg="#d4d4d4")
        scroll = tk.Scrollbar(win, command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=5)

        def run_install():
            text.insert(tk.END, f"$ {sys.executable} -m pip install {' '.join(packages)}\n\n")

            # Use --user flag if needed
            cmd = [sys.executable, "-m", "pip", "install"]

            # Add --user if we're in a system location
            if sys.prefix.startswith('/usr') and not os.access(sys.prefix, os.W_OK):
                cmd.append("--user")
                text.insert(tk.END, "Note: Using --user (system site-packages not writable)\n\n")

            cmd.extend(packages)

            proc = subprocess.Popen(
                cmd,
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
                text.insert(tk.END, "\n✅ SUCCESS! Dependencies installed.\n")

                # On Linux, pyzbar needs libzbar0
                if IS_LINUX and 'pyzbar' in str(packages):
                    text.insert(tk.END, "\nChecking for libzbar0...\n")
                    try:
                        subprocess.run(['ldconfig', '-p'], capture_output=True, text=True)
                        # Can't easily install system libs from here, just warn
                        text.insert(tk.END, "NOTE: If you get import errors, you may need:\n")
                        text.insert(tk.END, "  sudo apt-get install libzbar0\n")
                    except:
                        pass

                text.insert(tk.END, "\nRestarting plugin to load new modules...\n")
                win.update()
                time.sleep(2)

                # Restart the plugin
                self.window.after(0, self._restart_plugin)
                win.after(500, win.destroy)
            else:
                text.insert(tk.END, f"\n❌ FAILED (code {proc.returncode})\n")

        threading.Thread(target=run_install, daemon=True).start()

    def _restart_plugin(self):
        """Completely restart the plugin window"""
        # Remember current tab
        last_tab = self.tab_var.get()

        # Close current window
        self._on_close()

        # Re-create plugin instance
        self.__init__(self.app)

        # Open new window
        self.open_window()

        # Switch to last tab
        if hasattr(self, 'tab_var'):
            self.tab_var.set(last_tab)
            self._switch_tab(last_tab)

        # Refresh the current tab
        current_tab = self.tab_var.get()

        self.status_var.set("✅ Dependencies installed - view refreshed")

    def _show_install_button(self, feature: str, packages: List[str], missing=None):
        """Show install button for missing dependencies"""
        if missing is None:
            missing = packages

        msg_frame = tk.Frame(self.left_panel_content, bg="white")
        msg_frame.pack(pady=20)

        tk.Label(msg_frame,
                text=f"❌ Missing: {', '.join(missing)}",
                fg="#e74c3c", bg="white", font=("Arial", 10, "bold")).pack()

        # Install button
        tk.Button(msg_frame, text=f"📦 Install Dependencies",
                command=lambda: self._install_and_refresh(feature, packages),
                bg="#f39c12", fg="white", font=("Arial", 9, "bold"),
                padx=20, pady=5).pack(pady=5)

        tk.Label(msg_frame,
                text="Click to install required packages",
                fg="#7f8c8d", bg="white", font=("Arial", 8)).pack()

    def _build_manual_entry(self):
        tk.Label(self.left_panel_content, text="Manual Entry:", font=("Arial", 8, "bold"),
                bg="white").pack(anchor=tk.W, pady=(10,2))

        manual_frame = tk.Frame(self.left_panel_content, bg="white")
        manual_frame.pack(fill=tk.X, pady=2)

        self.manual_var = tk.StringVar()
        manual_entry = tk.Entry(manual_frame, textvariable=self.manual_var)
        manual_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ToolTip(manual_entry, "Type barcode manually and click Add")
        tk.Button(manual_frame, text="Add", command=self._add_manual,
                 bg="#3498db", fg="white", width=6).pack(side=tk.RIGHT, padx=(5,0))

    def _build_context_fields(self):
        tk.Label(self.left_panel_content, text="Context Fields:", font=("Arial", 8, "bold"),
                bg="white").pack(anchor=tk.W, pady=(10,2))

        fields = [("Batch ID:", "batch_var"), ("Sample ID:", "sample_var"),
                  ("Context:", "context_var")]

        for label, name in fields:
            f = tk.Frame(self.left_panel_content, bg="white")
            f.pack(fill=tk.X, pady=1)
            tk.Label(f, text=label, font=("Arial", 7),
                    bg="white", width=8, anchor=tk.W).pack(side=tk.LEFT)
            var = tk.StringVar()
            entry = tk.Entry(f, textvariable=var, width=20)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            ToolTip(entry, f"Enter {label.lower()} for这批 scans")
            self.context_vars[name] = var

    def _update_preview_for_device(self, device_type):
        if device_type == "Webcam" and self.preview_var.get():
            self.preview_label.config(text="Camera starting...", fg="white")
        elif device_type == "USB HID":
            self.preview_label.config(text="⌨️ USB HID Mode\n\nClick in the scan field\nand scan with your device",
                                     fg="#ccc", font=("Arial", 9))
        elif device_type == "USB Serial":
            self.preview_label.config(text="🔌 USB Serial Mode\n\nConnect to a port\nand start scanning",
                                     fg="#ccc", font=("Arial", 9))
        elif device_type == "Bluetooth SPP":
            self.preview_label.config(text="📱 Bluetooth SPP Mode\n\nSelect a device and connect",
                                     fg="#ccc", font=("Arial", 9))
        elif device_type == "Bluetooth LE":
            self.preview_label.config(text="📡 Bluetooth LE Mode\n\nScan for devices and connect",
                                     fg="#ccc", font=("Arial", 9))

    def _activate_hid_scanner(self):
        if self._disconnecting:
            return
        if self.active_type == "USB HID" and self.focused_scanner:
            return
        self._disconnect_scanner()
        self.focused_scanner = FocusedScanner(self._on_scan)
        self.active_scanner = self.focused_scanner
        self.active_type = "USB HID"
        self.status_var.set("USB HID mode - Click field and scan")
        self._update_connection_status(True)

    def _open_bluetooth_settings(self):
        try:
            if IS_WINDOWS:
                subprocess.run('start ms-settings:bluetooth', shell=True)
            elif IS_MAC:
                subprocess.run('open /System/Library/PreferencePanes/Bluetooth.prefPane', shell=True)
            else:
                try:
                    subprocess.run('gnome-control-center bluetooth', shell=True)
                except:
                    try:
                        subprocess.run('blueman-manager', shell=True)
                    except:
                        messagebox.showinfo("Bluetooth", "Please pair your scanner using system Bluetooth settings")
        except:
            messagebox.showinfo("Bluetooth", "Please pair your scanner using system Bluetooth settings")

    # ========================================================================
    # SCANNER CONNECTION METHODS
    # ========================================================================

    def _refresh_serial_ports(self):
        if not self.deps['pyserial'] or not self.serial_port_combo:
            return
        try:
            ports = [p.device for p in serial.tools.list_ports.comports()]
            if ports:
                self.serial_port_combo['values'] = ports
                self.serial_port_combo.current(0)
        except:
            pass

    def _refresh_bluetooth_spp_ports(self):
        if not self.deps['pyserial'] or not self.bt_spp_port_combo:
            return
        try:
            self.bt_spp_devices = BluetoothSPPScanner.discover_ports()
            port_displays = [f"{d['port']} - {d['model']}" for d in self.bt_spp_devices]
            if port_displays:
                self.bt_spp_port_combo['values'] = port_displays
                self.bt_spp_port_combo.current(0)
                if self.bt_spp_devices:
                    first = self.bt_spp_devices[0]
                    if first['manufacturer'] != 'Unknown':
                        mfg = first['manufacturer']
                        if mfg in SPP_MANUFACTURERS:
                            self.bt_spp_manufacturer_combo.set(mfg)
                            self._on_bt_spp_manufacturer_select()
                            if first['model'] in SPP_MANUFACTURERS.get(mfg, []):
                                self.bt_spp_model_combo.set(first['model'])
                                self._on_bt_spp_model_select()
                            self.preview_label.config(
                                text=f"📱 Detected: {first['model']}\nPort: {first['port']}\nClick Connect",
                                fg="#ccc", font=("Arial", 9))
            else:
                self.bt_spp_port_combo['values'] = ["No Bluetooth ports found"]
        except Exception as e:
            print(f"Error refreshing BT ports: {e}")

    def _refresh_cameras(self):
        if not self.deps['opencv'] or not self.webcam_combo:
            return
        cameras = []
        for i in range(5):
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    cameras.append(f"Camera {i}")
                    cap.release()
            except:
                pass
        if cameras:
            self.webcam_combo['values'] = cameras
            self.webcam_combo.current(0)

    def _on_bt_spp_manufacturer_select(self, event=None):
        mfg = self.bt_spp_manufacturer_combo.get()
        if mfg in SPP_MANUFACTURERS:
            models = SPP_MANUFACTURERS[mfg]
            self.bt_spp_model_combo['values'] = models
            if models:
                self.bt_spp_model_combo.current(0)
                self._on_bt_spp_model_select()

    def _on_bt_spp_model_select(self, event=None):
        model = self.bt_spp_model_combo.get()
        if model in BLUETOOTH_SPP_MODELS:
            info = BLUETOOTH_SPP_MODELS[model]
            self.bt_spp_baud_combo.set(str(info['default_baud']))
            self.bt_spp_info.config(
                text=f"Model: {model}\nManufacturer: {info['manufacturer']}\nDefault Baud: {info['default_baud']}"
            )

    def _connect_serial(self):
        if not self.deps['pyserial']:
            messagebox.showerror("Error", "pyserial not installed")
            return
        port = self.serial_port_combo.get()
        if not port:
            messagebox.showwarning("No Port", "Select a COM port")
            return
        try:
            baud = int(self.serial_baud_combo.get())
        except:
            baud = 9600
        self._update_progress(30, "Connecting...")
        self._disconnect_scanner()
        self.serial_scanner = USBSerialScanner(port, baud, self._on_scan, self.ui_queue)
        success, msg = self.serial_scanner.connect()
        if success:
            self.serial_scanner.start()
            self.active_scanner = self.serial_scanner
            self.active_type = "Serial"
            self._update_progress(100, "Connected")
            self.status_var.set(f"Connected to {port}")
            self.serial_status.config(text=f"🟢 Connected", fg="#27ae60")
            self.serial_connect_btn.config(text="🔌 Disconnect", command=self._disconnect_scanner,
                                          bg="#e74c3c")
            self.preview_label.config(text=f"Serial Scanner Active\n{port} @ {baud} baud",
                                     fg="#ccc", font=("Arial", 9))
            self._update_connection_status(True)
        else:
            self._update_progress(0, "Failed")
            messagebox.showerror("Connection Failed", msg)

    def _connect_bluetooth_spp(self):
        if not self.deps['pyserial']:
            messagebox.showerror("Error", "pyserial not installed")
            return
        port_info = self.bt_spp_port_combo.get()
        if not port_info or port_info.startswith('No'):
            messagebox.showwarning("No Port", "Select a Bluetooth port")
            return
        port = port_info.split(' - ')[0]
        baud = int(self.bt_spp_baud_combo.get())
        self._update_progress(30, "Connecting...")
        self._disconnect_scanner()
        self.bluetooth_spp_scanner = BluetoothSPPScanner(port, baud, self._on_scan, self.ui_queue)
        success, msg = self.bluetooth_spp_scanner.connect()
        if success:
            self.bluetooth_spp_scanner.start()
            self.active_scanner = self.bluetooth_spp_scanner
            self.active_type = "Bluetooth SPP"
            self._update_progress(100, "Connected")
            self.status_var.set(f"Connected to {port}")
            self.bt_spp_connect_btn.config(text="🔌 Disconnect", command=self._disconnect_scanner,
                                          bg="#e74c3c")
            model = self.bt_spp_model_combo.get() or "Bluetooth Scanner"
            self.preview_label.config(text=f"Bluetooth SPP Active\n{model}\n{port}",
                                     fg="#ccc", font=("Arial", 9))
            self._update_connection_status(True)
        else:
            self._update_progress(0, "Failed")
            messagebox.showerror("Connection Failed", msg)

    def _scan_ble_devices(self):
        """Scan for BLE devices - thread-safe version with animation"""
        self._scanning = True
        self._animate_scanning()
        self.ble_scan_btn.config(state=tk.DISABLED)
        self._update_progress(50, "Scanning for BLE devices...")
        self.ble_device_list.delete(0, tk.END)
        self.ble_devices = []
        self.filtered_ble_devices = []

        async def scan_async():
            devices = []
            scanner = BleakScanner()
            found = await scanner.discover(timeout=5)

            for d in found:
                if d.name and any(x in d.name.lower() for x in ['socket', 'zebra', 'honeywell', 'datalogic', 'inateck', 'eyoyo', 'scan', 'bar']):
                    model_info = self._identify_ble_model(d.name)
                    devices.append({
                        'address': d.address,
                        'name': d.name,
                        'rssi': d.rssi,
                        'model': model_info['model'],
                        'manufacturer': model_info['manufacturer'],
                    })
            return devices

        def scan_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                devices = loop.run_until_complete(scan_async())
            except Exception as e:
                devices = []
                error_msg = str(e)
            finally:
                loop.close()

            def update_ui():
                self._scanning = False
                self.ble_devices = devices
                self.ble_device_list.delete(0, tk.END)
                self.filtered_ble_devices = []

                if devices:
                    for d in devices:
                        bars = self._rssi_to_bars(d['rssi'])
                        display = f"{bars} {d['model']}"
                        self.ble_device_list.insert(tk.END, display)
                        self.filtered_ble_devices.append(d)
                else:
                    self.ble_device_list.insert(tk.END, "✨ No devices found")
                    self.ble_device_list.itemconfig(0, fg="#7f8c8d")

                self.ble_scan_btn.config(state=tk.NORMAL, text="🔍 Scan for BLE Devices")
                self._update_progress(100, f"Found {len(devices)} devices")

                if not devices:
                    self.ble_info.config(text="No BLE scanners found.\nMake sure device is discoverable.")

            self.ui_queue.schedule(update_ui)

        threading.Thread(target=scan_thread, daemon=True).start()

    def _identify_ble_model(self, name: str) -> Dict:
        """Identify BLE scanner model from name"""
        name_lower = name.lower()

        # Check database
        for model, info in BLE_SCANNER_DATABASE.items():
            if model.lower() in name_lower:
                return {
                    'model': model,
                    'manufacturer': info['manufacturer'],
                    'service_uuid': info.get('service_uuid'),
                    'rx_char': info.get('rx_char'),
                }

        # Fallback by manufacturer
        if 'socket' in name_lower:
            return {'model': 'Socket BLE', 'manufacturer': 'Socket'}
        if 'zebra' in name_lower:
            return {'model': 'Zebra BLE', 'manufacturer': 'Zebra'}
        if 'honeywell' in name_lower:
            return {'model': 'Honeywell BLE', 'manufacturer': 'Honeywell'}
        if 'datalogic' in name_lower:
            return {'model': 'Datalogic BLE', 'manufacturer': 'Datalogic'}
        if 'inateck' in name_lower:
            return {'model': 'Inateck BLE', 'manufacturer': 'Inateck'}
        if 'eyoyo' in name_lower:
            return {'model': 'Eyoyo BLE', 'manufacturer': 'Eyoyo'}

        return {'model': 'Unknown BLE Device', 'manufacturer': 'Unknown'}

    def _on_ble_filter_change(self, event=None):
        """Filter BLE device list by manufacturer"""
        filter_mfg = self.ble_manufacturer_combo.get()
        self.ble_device_list.delete(0, tk.END)
        self.filtered_ble_devices = []

        if self.ble_devices:
            for d in self.ble_devices:
                if filter_mfg == "All" or d['manufacturer'] == filter_mfg:
                    bars = self._rssi_to_bars(d['rssi'])
                    display = f"{bars} {d['model']}"
                    self.ble_device_list.insert(tk.END, display)
                    self.filtered_ble_devices.append(d)

        if not self.filtered_ble_devices:
            self.ble_device_list.insert(tk.END, "✨ No matching devices")
            self.ble_device_list.itemconfig(0, fg="#7f8c8d")

    def _on_ble_device_select(self, event):
        """Handle BLE device selection"""
        selection = self.ble_device_list.curselection()
        if selection and hasattr(self, 'filtered_ble_devices'):
            if selection[0] < len(self.filtered_ble_devices):
                device = self.filtered_ble_devices[selection[0]]
                self.ble_connect_btn.config(state=tk.NORMAL)

                info_text = f"Model: {device['model']}\nManufacturer: {device['manufacturer']}\nAddress: {device['address'][:15]}..."
                self.ble_info.config(text=info_text)
                self.selected_ble_device = device

    def _connect_bluetooth_le(self):
        """Connect to selected BLE device"""
        if not hasattr(self, 'selected_ble_device') or not self.selected_ble_device:
            messagebox.showwarning("No Device", "Select a device first")
            return

        device = self.selected_ble_device

        self._update_progress(30, "Connecting to BLE...")

        self._disconnect_scanner()
        self.bluetooth_le_scanner = BluetoothLEScanner(
            device['address'],
            device,
            self._on_scan,
            self.ui_queue
        )
        success, msg = self.bluetooth_le_scanner.connect()

        if success:
            self.bluetooth_le_scanner.start()
            self.active_scanner = self.bluetooth_le_scanner
            self.active_type = "Bluetooth LE"

            self._update_progress(100, "Connected")
            self.status_var.set(f"Connected to {device['model']}")
            self.ble_connect_btn.config(text="🔌 Disconnect", command=self._disconnect_scanner,
                                        bg="#e74c3c")
            self.ble_scan_btn.config(state=tk.DISABLED)
            self._update_connection_status(True)

            self.preview_label.config(text=f"BLE Active\n{device['model']}",
                                     fg="#ccc", font=("Arial", 9))
        else:
            self._update_progress(0, "Failed")
            self.ble_connect_btn.config(state=tk.NORMAL)
            messagebox.showerror("Connection Failed", msg)

    def _connect_webcam(self):
        if not self.deps['opencv'] or not self.deps['pyzbar']:
            messagebox.showerror("Error", "OpenCV or pyzbar not installed")
            return
        try:
            cam_sel = self.webcam_combo.get()
            cam_id = int(cam_sel.split(' ')[1])
        except:
            cam_id = 0
        self._update_progress(30, "Starting camera...")
        self._disconnect_scanner()
        preview_queue = self.preview_queue if self.preview_var.get() else None
        self.webcam_scanner = WebcamScanner(cam_id, self._on_scan, self.ui_queue, preview_queue)
        success, msg = self.webcam_scanner.connect()
        if success:
            self.webcam_scanner.start()
            self.active_scanner = self.webcam_scanner
            self.active_type = "Webcam"
            self._update_progress(100, "Camera active")
            self.status_var.set(f"Camera {cam_id} started")
            self.webcam_status.config(text="🟢", fg="#2ecc71")
            self.webcam_connect_btn.config(text="⏹ Stop Camera", command=self._disconnect_scanner,
                                          bg="#e74c3c")
            self._update_connection_status(True)
            self._update_preview()
        else:
            self._update_progress(0, "Failed")
            messagebox.showerror("Connection Failed", msg)

    def _disconnect_scanner(self):
        """Disconnect current scanner - FIXED: with BLE cleanup"""
        if self._disconnecting:
            return
        self._disconnecting = True
        try:
            if self.active_scanner:
                self.active_scanner.disconnect()
                self.active_scanner = None
                self.active_type = ""

            if self.window and self.window.winfo_exists():
                current_tab = self.tab_var.get()

                if current_tab == "USB Serial":
                    if hasattr(self, 'serial_connect_btn') and self.serial_connect_btn:
                        self.serial_connect_btn.config(text="🔌 Connect", command=self._connect_serial,
                                                    bg="#27ae60")
                    if hasattr(self, 'serial_status') and self.serial_status:
                        self.serial_status.config(text="⚪ Not Connected", fg="#e74c3c")

                elif current_tab == "Bluetooth SPP":
                    if hasattr(self, 'bt_spp_connect_btn') and self.bt_spp_connect_btn:
                        self.bt_spp_connect_btn.config(text="🔌 Connect Bluetooth", command=self._connect_bluetooth_spp,
                                                    bg="#27ae60")

                elif current_tab == "Bluetooth LE":
                    # Clear selected device
                    if hasattr(self, 'selected_ble_device'):
                        delattr(self, 'selected_ble_device')
                    if hasattr(self, 'filtered_ble_devices'):
                        delattr(self, 'filtered_ble_devices')

                    # Reset buttons
                    if hasattr(self, 'ble_connect_btn') and self.ble_connect_btn:
                        self.ble_connect_btn.config(text="🔌 Connect Selected", command=self._connect_bluetooth_le,
                                                    bg="#27ae60", state=tk.NORMAL)
                    if hasattr(self, 'ble_scan_btn') and self.ble_scan_btn:
                        self.ble_scan_btn.config(state=tk.NORMAL)

                    # Clear device list
                    if hasattr(self, 'ble_device_list') and self.ble_device_list:
                        self.ble_device_list.delete(0, tk.END)
                        self.ble_device_list.insert(tk.END, "✨ No devices found - click Scan")
                        self.ble_device_list.itemconfig(0, fg="#7f8c8d")

                    # Reset info text
                    if hasattr(self, 'ble_info') and self.ble_info:
                        self.ble_info.config(text="No device selected")

                elif current_tab == "Webcam":
                    if hasattr(self, 'webcam_connect_btn') and self.webcam_connect_btn:
                        self.webcam_connect_btn.config(text="▶ Start Camera", command=self._connect_webcam,
                                                    bg="#27ae60")
                    if hasattr(self, 'webcam_status') and self.webcam_status:
                        self.webcam_status.config(text="⚪", fg="#e74c3c")
                    if self.preview_label and self.preview_label.winfo_exists():
                        self.preview_label.config(text="Camera stopped", fg="#ccc")

            self._update_progress(0, "")
            self.status_var.set("Disconnected")
            self._update_connection_status(False)

        finally:
            self._disconnecting = False

    # ========================================================================
    # SCAN HANDLING
    # ========================================================================

    def _on_scan(self, barcode: str, symbology: str, device: str):
        batch_id = ""
        sample_id = ""
        context = ""
        if hasattr(self, 'context_vars'):
            if 'batch_var' in self.context_vars:
                batch_id = self.context_vars['batch_var'].get()
            if 'sample_var' in self.context_vars:
                sample_id = self.context_vars['sample_var'].get()
            if 'context_var' in self.context_vars:
                context = self.context_vars['context_var'].get()

        evt = ScanResult(
            timestamp=datetime.now(),
            barcode=barcode,
            symbology=detect_symbology(barcode) or symbology,
            scanner_type=self.active_type,
            scanner_model=device,
            port="",
            batch_id=batch_id,
            sample_id=sample_id,
            context=context
        )
        self.scans.append(evt)
        self.current_scan = evt
        if self.ui_queue:
            self.ui_queue.schedule(lambda: self._add_scan_to_ui(evt))

    def _add_scan_to_ui(self, evt: ScanResult):
        display = f"[{evt.timestamp.strftime('%H:%M:%S')}] {evt.barcode}"
        self.log_listbox.insert(0, display)
        if self.log_listbox.size() > 50:
            self.log_listbox.delete(50, tk.END)
        self.last_scan_var.set(f"Last: {evt.barcode[:30]}")
        self.scan_count_var.set(f"{len(self.scans)} scans")
        if self.beep_var.get():
            self.window.bell()

    def _on_key_press(self, event):
        if self.active_type != "USB HID" or not self.focused_scanner:
            return
        barcode = self.focused_scanner.process_key(event.keysym)
        if barcode:
            self._on_scan(barcode, "HID", "USB HID Scanner")
            if self.focused_entry and self.focused_entry.focus_get() == self.focused_entry:
                self.focused_entry.delete(0, tk.END)
                self.focused_entry.insert(0, barcode)

    def _add_manual(self):
        barcode = self.manual_var.get().strip()
        if barcode:
            self._on_scan(barcode, "MANUAL", "Manual Entry")
            self.manual_var.set("")

    def _update_preview(self):
        if not self.active_scanner or self.active_type != "Webcam" or not self.deps['pillow']:
            return
        try:
            latest_frame = None
            try:
                while True:
                    latest_frame = self.preview_queue.get_nowait()
            except queue.Empty:
                pass
            if latest_frame is not None:
                img = Image.fromarray(latest_frame)
                w = self.preview_frame.winfo_width()
                h = self.preview_frame.winfo_height()
                if w > 10 and h > 10:
                    img.thumbnail((w, h), Image.Resampling.LANCZOS)
                self.preview_image = ImageTk.PhotoImage(img)
                self.preview_label.config(image=self.preview_image, text="")
        except:
            pass
        if self._processing:
            self.window.after(50, self._update_preview)

    def _start_processor(self):
        self._processing = True
        self.window.after(100, self._process_queue)

    def _process_queue(self):
        if not self._processing or not self.window or not self.window.winfo_exists():
            return
        try:
            while True:
                callback = self.ui_queue.queue.get_nowait()
                callback()
        except queue.Empty:
            pass
        self.window.after(100, self._process_queue)

    # ========================================================================
    # EXPORT & INTEGRATION
    # ========================================================================

    def send_to_table(self):
        if not self.scans:
            messagebox.showwarning("No Data", "No scans to send")
            return
        data = [s.to_dict() for s in self.scans]
        try:
            self.app.import_data_from_plugin(data)
            self.status_var.set(f"✅ Sent {len(data)} scans to main table")
            if self.auto_clear_var.get():
                self.scans.clear()
                self.log_listbox.delete(0, tk.END)
                self.scan_count_var.set("0 scans")
                self.last_scan_var.set("---")
        except AttributeError:
            messagebox.showwarning("Integration", "Main app: import_data_from_plugin() required")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def collect_data(self) -> List[Dict]:
        return [s.to_dict() for s in self.scans]

    def _export_csv(self):
        if not self.scans:
            messagebox.showwarning("No Data", "No scans to export")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("All files", "*.*")],
            initialfile=f"scans_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        if not path:
            return
        try:
            if self.deps['pandas']:
                df = pd.DataFrame([s.to_dict() for s in self.scans])
                df.to_csv(path, index=False)
            else:
                import csv
                with open(path, 'w', newline='', encoding='utf-8') as f:
                    if self.scans:
                        writer = csv.DictWriter(f, fieldnames=self.scans[0].to_dict().keys())
                        writer.writeheader()
                        for scan in self.scans:
                            writer.writerow(scan.to_dict())
            self.status_var.set(f"Exported to {Path(path).name}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _on_close(self):
        self._processing = False
        self._scanning = False
        if hasattr(self, '_disconnect_scanner'):
            try:
                self._disconnecting = True
                if self.active_scanner:
                    self.active_scanner.disconnect()
                    self.active_scanner = None
            except:
                pass
        if self.window:
            self.window.destroy()
            self.window = None


# ============================================================================
# STANDARD PLUGIN REGISTRATION
# ============================================================================

def setup_plugin(main_app):
    global _SCANNER_REGISTERED
    if _SCANNER_REGISTERED:
        print(f"⏭️ Barcode Scanner plugin already registered, skipping...")
        return None

    plugin = BarcodeScannerUnifiedSuitePlugin(main_app)

    if hasattr(main_app, 'left') and main_app.left is not None:
        main_app.left.add_hardware_button(
            name=PLUGIN_INFO.get("name", "Barcode/QR Scanner"),
            icon=PLUGIN_INFO.get("icon", "📷"),
            command=plugin.show_interface
        )
        print(f"✅ Added to left panel: {PLUGIN_INFO.get('name')}")
        _SCANNER_REGISTERED = True
        return plugin

    if hasattr(main_app, 'menu_bar'):
        if not hasattr(main_app, 'hardware_menu'):
            main_app.hardware_menu = tk.Menu(main_app.menu_bar, tearoff=0)
            main_app.menu_bar.add_cascade(label="🔧 Hardware", menu=main_app.hardware_menu)

        main_app.hardware_menu.add_command(
            label=PLUGIN_INFO.get("name", "Barcode/QR Scanner"),
            command=plugin.show_interface
        )
        print(f"✅ Added to Hardware menu: {PLUGIN_INFO.get('name')}")
        _SCANNER_REGISTERED = True

    return plugin
