"""
PHYSICS TEST & MEASUREMENT SUITE v1.2 - FINAL POLISH
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Oscilloscopes · DMMs · Power Supplies · Function Generators · LCR meters
Keysight · Tektronix · Rigol · Keithley · Rohde & Schwarz — SCPI/VISA unified
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

PLUGIN_INFO = {
    "category": "hardware",
    "id": "physics_test_and_measurement_suite",
    "name": "Physics T&M Suite",
    "icon": "📟",
    "description": "Oscilloscopes · DMMs · Power Supplies · Function Generators · LCR — Keysight · Tektronix · Rigol · Keithley · SCPI/VISA",
    "version": "1.2.0",
    "requires": ["numpy", "pandas", "pyvisa"],
    "optional": ["pymeasure", "matplotlib", "scipy", "openpyxl", "pyvisa-py"],
    "author": "Physics Unified Team",
    "compact": True,
}

# ============================================================================
# PREVENT DOUBLE REGISTRATION
# ============================================================================
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import pandas as pd
from datetime import datetime
import time
import re
import json
import threading
import queue
import platform
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Callable, Union
import warnings
warnings.filterwarnings('ignore')
from pathlib import Path

# ============================================================================
# DEPENDENCY CHECK
# ============================================================================
def check_dependencies():
    deps = {
        'numpy': False, 'pandas': False, 'pyvisa': False,
        'pymeasure': False, 'matplotlib': False, 'scipy': False,
        'openpyxl': False, 'pyvisa-py': False
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
        import pyvisa
        deps['pyvisa'] = True
    except: pass
    try:
        import pymeasure
        deps['pymeasure'] = True
    except: pass
    try:
        import matplotlib
        deps['matplotlib'] = True
    except: pass
    try:
        import scipy
        deps['scipy'] = True
    except: pass
    try:
        import openpyxl
        deps['openpyxl'] = True
    except: pass
    # pyvisa-py is not directly importable, but we can check if it's installed via pyvisa
    try:
        import pyvisa
        if hasattr(pyvisa, 'pyvisa_py'):
            deps['pyvisa-py'] = True
    except: pass
    return deps

DEPS = check_dependencies()

# Safe imports
if DEPS['numpy']:
    import numpy as np
else:
    np = None

if DEPS['pandas']:
    import pandas as pd
else:
    pd = None

if DEPS['pyvisa']:
    import pyvisa
    try:
        rm = pyvisa.ResourceManager()
    except:
        rm = None
else:
    pyvisa = None
    rm = None

if DEPS['pymeasure']:
    from pymeasure.instruments import Instrument
    from pymeasure.instruments.keithley import Keithley2400, Keithley2450, Keithley2000
    from pymeasure.instruments.rigol import RigolDS1000Z
    from pymeasure.instruments.agilent import Agilent34410A
    from pymeasure.instruments.keysight import Keysight34461A
    from pymeasure.instruments.tektronix import TektronixTBS2000
    HAS_PYMEASURE = True
else:
    HAS_PYMEASURE = False

if DEPS['matplotlib']:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    HAS_MPL = True
else:
    HAS_MPL = False

if DEPS['scipy']:
    from scipy import signal
    HAS_SCIPY = True
else:
    HAS_SCIPY = False

# ============================================================================
# TOOLTIP CLASS (copied from your barcode scanner)
# ============================================================================
class ToolTip:
    """Create tooltips for any widget - improved version that properly disappears"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.after_id = None
        widget.bind('<Enter>', self.enter)
        widget.bind('<Leave>', self.leave)
        widget.bind('<ButtonPress>', self.leave)  # Hide on click

    def enter(self, event=None):
        # Schedule showing the tooltip after a short delay
        self.after_id = self.widget.after(500, self.show_tip)  # 500ms delay

    def leave(self, event=None):
        # Cancel scheduled show and hide tooltip
        if self.after_id:
            self.widget.after_cancel(self.after_id)
            self.after_id = None
        self.hide_tip()

    def show_tip(self):
        # Get widget coordinates
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 20

        # Create toplevel window
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)  # Remove window decorations
        tw.wm_geometry(f"+{x}+{y}")

        # Make sure it's on top but not stealing focus
        tw.attributes('-topmost', True)

        # Add a frame with border
        frame = tk.Frame(tw, bg="#ffffe0", relief=tk.SOLID, borderwidth=1)
        frame.pack()

        # Add the text
        label = tk.Label(frame, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", font=("Arial", "8", "normal"),
                         padx=3, pady=2)
        label.pack()

        # Bind events to the tooltip itself
        tw.bind('<Leave>', self.hide_tip)

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

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
# DATA CLASS FOR MEASUREMENTS
# ============================================================================
@dataclass
class Measurement:
    timestamp: datetime
    instrument: str
    resource: str
    channel: Optional[int] = None
    measurement_type: str = ""
    value: Optional[float] = None
    unit: str = ""
    raw_data: Optional[Any] = None   # for waveforms, etc.

    def to_dict(self) -> Dict[str, str]:
        d = {
            'Timestamp': self.timestamp.isoformat(),
            'Instrument': self.instrument,
            'Resource': self.resource,
            'Channel': str(self.channel) if self.channel else '',
            'Type': self.measurement_type,
            'Value': f"{self.value:.6f}" if self.value is not None else '',
            'Unit': self.unit,
        }
        return {k: v for k, v in d.items() if v}

# ============================================================================
# IMPROVED INSTRUMENT WRAPPERS (with proper SCPI and model awareness)
# ============================================================================
class VisaInstrumentWrapper:
    """Base wrapper for raw VISA communication with error checking."""
    def __init__(self, resource):
        self.resource = resource
        self.connected = False
        self.idn = ""
        self.manufacturer = ""
        self.model = ""
        self.serial = ""
        self.firmware = ""

    def connect(self):
        try:
            self.resource.open()
            self.connected = True
            self.idn = self.query('*IDN?').strip()
            # Parse IDN: typically "Manufacturer,Model,Serial,Firmware"
            parts = self.idn.split(',')
            if len(parts) >= 4:
                self.manufacturer = parts[0].strip()
                self.model = parts[1].strip()
                self.serial = parts[2].strip()
                self.firmware = parts[3].strip()
            elif len(parts) == 3:
                self.manufacturer = parts[0].strip()
                self.model = parts[1].strip()
                self.serial = parts[2].strip()
            elif len(parts) == 2:
                self.manufacturer = parts[0].strip()
                self.model = parts[1].strip()
            else:
                self.manufacturer = self.idn[:20]
            return True, self.idn
        except Exception as e:
            return False, str(e)

    def disconnect(self):
        try:
            self.resource.close()
        except:
            pass
        self.connected = False

    def write(self, cmd):
        if self.connected:
            self.resource.write(cmd)

    def query(self, cmd):
        if self.connected:
            return self.resource.query(cmd).strip()
        return ""

    def read(self):
        if self.connected:
            return self.resource.read().strip()
        return ""

    def query_ascii_values(self, cmd, **kwargs):
        if self.connected:
            return self.resource.query_ascii_values(cmd, **kwargs)
        return []

    def query_binary_values(self, cmd, **kwargs):
        if self.connected:
            return self.resource.query_binary_values(cmd, **kwargs)
        return []

    def check_errors(self):
        """Poll error queue until empty."""
        errors = []
        while True:
            err = self.query(':SYST:ERR?')
            if err.startswith('0,"No error"'):
                break
            errors.append(err)
        return errors

# ============================================================================
# Manufacturer-specific wrappers with enhanced functionality
# ============================================================================
class RigolDS1000ZWrapper(VisaInstrumentWrapper):
    def auto_scale(self):
        self.write(':AUToscale')

    def get_waveform(self, channel=1, mode='NORM', points=None):
        """
        Fetch waveform from specified channel.
        Returns (x_data, y_data) in seconds and volts.
        """
        try:
            # Set source
            self.write(f':WAV:SOUR CHAN{channel}')
            # Set mode (RAW = normal acquisition, NORM = memory)
            self.write(f':WAV:MODE {mode}')
            # Optionally set points (MAX for all available)
            if points is None:
                self.write(':WAV:POIN MAX')
            else:
                self.write(f':WAV:POIN {points}')

            # Query preamble to get scaling
            preamble = self.query(':WAV:PRE?').strip()
            # Format: format, type, points, count, xincrement, xorigin, xreference, yincrement, yorigin, yreference
            parts = preamble.split(',')
            if len(parts) >= 10:
                points = int(parts[2])
                xinc = float(parts[4])
                xorig = float(parts[5])
                yinc = float(parts[7])
                yorig = float(parts[8])
                yref = float(parts[9])
            else:
                # fallback
                xinc = 1e-6
                xorig = 0
                yinc = 1
                yorig = 0
                yref = 0

            # Fetch data in binary WORD format (2 bytes per point) for speed
            self.write(':WAV:FORM WORD')
            raw = self.query_binary_values(':WAV:DATA?', datatype='h', is_big_endian=False)
            # Convert to volts using preamble info
            y_data = [(val - yorig - yref) * yinc for val in raw]
            # Generate x-axis (time)
            x_data = [xorig + i * xinc for i in range(len(y_data))]
            return x_data, y_data
        except Exception as e:
            return None, None

    def run(self):
        self.write(':RUN')

    def stop(self):
        self.write(':STOP')

    def single(self):
        self.write(':SINGLE')

class RigolDG800Wrapper(VisaInstrumentWrapper):
    def set_waveform(self, channel=1, wave='SIN', freq=1000, amp=1, offset=0):
        wave_map = {'SIN': 'SIN', 'SQU': 'SQU', 'RAMP': 'RAMP', 'PULS': 'PULS', 'NOISE': 'NOISE'}
        w = wave_map.get(wave, 'SIN')
        self.write(f':SOUR{channel}:FUNC {w}')
        self.write(f':SOUR{channel}:FREQ {freq}')
        self.write(f':SOUR{channel}:VOLT {amp}')
        self.write(f':SOUR{channel}:VOLT:OFFS {offset}')
        self.write(f':OUTP{channel} ON')

class Keithley2400Wrapper(VisaInstrumentWrapper):
    def set_voltage(self, volts):
        self.write(f':SOUR:VOLT {volts}')
    def set_current_compliance(self, amps):
        self.write(f':SENS:CURR:PROT {amps}')
    def output_on(self):
        self.write(':OUTP ON')
    def output_off(self):
        self.write(':OUTP OFF')
    def measure_voltage(self):
        return float(self.query(':MEAS:VOLT?'))
    def measure_current(self):
        return float(self.query(':MEAS:CURR?'))
    def measure_resistance(self):
        return float(self.query(':MEAS:RES?'))

class KeysightE3631Wrapper(VisaInstrumentWrapper):
    def __init__(self, resource):
        super().__init__(resource)
        self.channel_map = {'1': 'P6V', '2': 'P25V', '3': 'N25V'}

    def set_voltage(self, volts, channel='1'):
        ch = self.channel_map.get(str(channel), 'P6V')
        self.write(f'APPL {ch}, {volts}, 1')
    def output_on(self):
        self.write('OUTP ON')
    def output_off(self):
        self.write('OUTP OFF')
    def measure(self, channel='1'):
        ch = self.channel_map.get(str(channel), 'P6V')
        return float(self.query(f'MEAS:VOLT? {ch}'))

class Keysight34461AWrapper(VisaInstrumentWrapper):
    def configure_dcv(self, nplc=1, auto_range=True):
        self.write(':CONF:VOLT:DC')
        if auto_range:
            self.write(':VOLT:DC:RANG:AUTO ON')
        self.write(f':VOLT:DC:NPLC {nplc}')
    def read(self):
        return float(self.query(':READ?'))
    def fetch(self):
        return float(self.query(':FETC?'))

class TektronixTBS2000Wrapper(VisaInstrumentWrapper):
    def auto_set(self):
        self.write('AUTOSet EXECute')
    def acquire(self, channel=1):
        # Simplified: fetch waveform
        self.write('DAT:SOU CH1')
        self.write('DAT:ENC RIB')  # signed binary
        self.write('DAT:WID 1')
        ymult = float(self.query('WFMO:YMULT?'))
        yzero = float(self.query('WFMO:YZERO?'))
        yoff = float(self.query('WFMO:YOFF?'))
        xinc = float(self.query('WFMO:XINC?'))
        xzero = float(self.query('WFMO:XZERO?'))
        data = self.query_binary_values('CURV?', datatype='b')
        y_data = [(d - yoff) * ymult + yzero for d in data]
        x_data = [xzero + i * xinc for i in range(len(y_data))]
        return x_data, y_data

# ============================================================================
# Factory to create appropriate wrapper (now using PyMeasure when available)
# ============================================================================
def create_instrument_wrapper(resource):
    """Try to identify instrument type and return appropriate wrapper or PyMeasure class."""
    # First, open resource temporarily to get IDN
    try:
        resource.open()
        idn = resource.query('*IDN?').strip()
        resource.close()
    except:
        # Fallback to generic
        return VisaInstrumentWrapper(resource)

    idn_lower = idn.lower()

    # Try PyMeasure first if available
    if HAS_PYMEASURE:
        try:
            if 'rigol' in idn_lower and 'ds' in idn_lower and ('1000' in idn_lower or '1054' in idn_lower):
                return RigolDS1000Z(resource)
            elif 'keithley' in idn_lower:
                if '2400' in idn_lower:
                    return Keithley2400(resource)
                elif '2450' in idn_lower:
                    # Keithley2450 exists in pymeasure? Not in base; fallback to manual
                    pass
            elif 'keysight' in idn_lower or 'agilent' in idn_lower:
                if '34461' in idn_lower:
                    return Keysight34461A(resource)
                elif '34410' in idn_lower:
                    return Agilent34410A(resource)
            elif 'tektronix' in idn_lower and 'tbs' in idn_lower:
                return TektronixTBS2000(resource)
        except:
            pass  # fallback to manual wrappers

    # Manual wrappers
    if 'rigol' in idn_lower:
        if 'ds' in idn_lower:
            return RigolDS1000ZWrapper(resource)
        elif 'dg' in idn_lower:
            return RigolDG800Wrapper(resource)
    elif 'keithley' in idn_lower:
        if '2400' in idn_lower:
            return Keithley2400Wrapper(resource)
    elif 'keysight' in idn_lower or 'agilent' in idn_lower:
        if '34461' in idn_lower or '34460' in idn_lower:
            return Keysight34461AWrapper(resource)
        elif 'e3631' in idn_lower:
            return KeysightE3631Wrapper(resource)
    elif 'tektronix' in idn_lower and 'tbs' in idn_lower:
        return TektronixTBS2000Wrapper(resource)

    # Generic fallback
    wrapper = VisaInstrumentWrapper(resource)
    wrapper.idn = idn
    return wrapper

# ============================================================================
# MAIN PLUGIN
# ============================================================================
class PhysicsTestMeasurementSuitePlugin:
    def __init__(self, main_app):
        self.app = main_app
        self.window = None
        self.ui_queue = None

        # VISA resource manager
        self.rm = None
        self.resources = []
        self.instruments = {}   # resource -> instrument object

        # Measurements
        self.measurements: List[Measurement] = []
        self.current_measurement = None

        # UI variables
        self.status_var = tk.StringVar(value="Physics Test & Measurement Suite v1.2 - Ready")
        self.progress_var = tk.DoubleVar(value=0)
        self.logging = False
        self.logging_interval = 1.0
        self._continuous = False   # for DMM continuous

        # UI elements
        self.notebook = None
        self.resource_combo = None
        self.connect_btn = None
        self.idn_label = None
        self.status_indicator = None
        self.conn_indicator = None
        self.log_tree = None  # replaced listbox with treeview for better readability
        self.measurement_vars = {}   # For instrument-specific controls

        # Threads
        self.log_thread = None
        self.waveform_progress = None  # progress bar during waveform capture
        self._current_warning_shown = False  # guard for E3631 note

        # Check dependencies
        self.deps = DEPS
        if not self.deps['pyvisa']:
            messagebox.showerror("Missing Dependency", "PyVISA is required.\nPlease install: pip install pyvisa")

    def show_interface(self):
        self.open_window()

    def open_window(self):
        if not self.deps['pyvisa']:
            return

        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("Physics Test & Measurement Suite v1.2")
        self.window.geometry("1000x650")
        self.window.minsize(900, 600)
        self.window.transient(self.app.root)

        self.ui_queue = ThreadSafeUI(self.window)
        self._build_ui()
        self._init_visa()

        self.window.lift()
        self.window.focus_force()
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

    def _init_visa(self):
        try:
            self.rm = pyvisa.ResourceManager()
            self._refresh_resources()
        except Exception as e:
            self.status_var.set(f"VISA init error: {e}")

    def _refresh_resources(self):
        if not self.rm:
            return
        try:
            self.resources = self.rm.list_resources()
            if self.resource_combo:
                self.resource_combo['values'] = self.resources
                if self.resources:
                    self.resource_combo.current(0)
                else:
                    # Empty state
                    self.idn_label.config(text="No VISA resources — connect instrument & refresh")
        except Exception as e:
            self.status_var.set(f"Resource scan error: {e}")

    def _build_ui(self):
        # Header
        header = tk.Frame(self.window, bg="#2980b9", height=40)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="📟", font=("Arial", 16),
                bg="#2980b9", fg="white").pack(side=tk.LEFT, padx=8)
        tk.Label(header, text="PHYSICS TEST & MEASUREMENT SUITE", font=("Arial", 12, "bold"),
                bg="#2980b9", fg="white").pack(side=tk.LEFT, padx=2)
        tk.Label(header, text="v1.2 · SCPI/VISA · PyMeasure", font=("Arial", 8),
                bg="#2980b9", fg="#f1c40f").pack(side=tk.LEFT, padx=8)

        self.status_indicator = tk.Label(header, textvariable=self.status_var,
                                         font=("Arial", 8), bg="#2980b9", fg="#2ecc71")
        self.status_indicator.pack(side=tk.RIGHT, padx=10)

        # Add a "Disconnect All" button
        ttk.Button(header, text="🔌 Disconnect All", command=self._disconnect_all,
                  width=12).pack(side=tk.RIGHT, padx=5)

        # Resource toolbar
        tool_frame = tk.Frame(self.window, bg="#ecf0f1", height=35)
        tool_frame.pack(fill=tk.X)
        tool_frame.pack_propagate(False)

        tk.Label(tool_frame, text="VISA Resource:", font=("Arial", 9, "bold"),
                bg="#ecf0f1").pack(side=tk.LEFT, padx=5)

        self.resource_combo = ttk.Combobox(tool_frame, width=50)
        self.resource_combo.pack(side=tk.LEFT, padx=5)
        ToolTip(self.resource_combo, "Select the VISA resource string for your instrument.\nExample: USB0::0x1AB1::0x0588::DS1ZB245000123::INSTR")

        self.connect_btn = ttk.Button(tool_frame, text="🔌 Connect",
                                       command=self._connect_device)
        self.connect_btn.pack(side=tk.LEFT, padx=5)
        ToolTip(self.connect_btn, "Connect to selected instrument")

        ttk.Button(tool_frame, text="⟳ Refresh", command=self._refresh_resources,
                  width=8).pack(side=tk.LEFT, padx=2)
        ToolTip(self.connect_btn, "Scan for available VISA resources")

        self.conn_indicator = tk.Label(tool_frame, text="●", fg="red",
                                       font=("Arial", 12), bg="#ecf0f1")
        self.conn_indicator.pack(side=tk.LEFT, padx=5)

        self.idn_label = tk.Label(tool_frame, text="Not connected",
                                  font=("Arial", 8), bg="#ecf0f1", fg="#7f8c8d")
        self.idn_label.pack(side=tk.LEFT, padx=10)

        # Notebook for instrument categories
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self._create_oscilloscope_tab()
        self._create_dmm_tab()
        self._create_power_supply_tab()
        self._create_function_gen_tab()
        self._create_logging_tab()

        # Status bar
        status_bar = tk.Frame(self.window, bg="#34495e", height=24)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        status_bar.pack_propagate(False)

        deps_str = " · ".join([k for k, v in self.deps.items() if v])
        tk.Label(status_bar,
                text=f"PyVISA: {'✓' if self.deps['pyvisa'] else '✗'} · PyMeasure: {'✓' if self.deps['pymeasure'] else '✗'} · {deps_str}",
                font=("Arial", 7), bg="#34495e", fg="white").pack(side=tk.LEFT, padx=8)

    # ========== Oscilloscope Tab ==========
    def _create_oscilloscope_tab(self):
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="📈 Oscilloscope")

        # Controls
        frame = tk.LabelFrame(tab, text="Oscilloscope Controls", bg="white", padx=10, pady=10)
        frame.pack(fill=tk.X, padx=10, pady=10)

        self.scope_channel_var = tk.IntVar(value=1)
        tk.Label(frame, text="Channel:").grid(row=0, column=0, sticky=tk.W)

        # FIX: Store the spinbox widget in a variable and create ToolTip for it
        channel_spinbox = ttk.Spinbox(frame, from_=1, to=4, textvariable=self.scope_channel_var, width=5)
        channel_spinbox.grid(row=0, column=1, padx=5)
        ToolTip(channel_spinbox, "Select channel to acquire waveform from")  # ToolTip on widget, not variable

        ttk.Button(frame, text="Auto Scale", command=self._scope_auto_scale).grid(row=0, column=2, padx=5)
        ttk.Button(frame, text="Run", command=self._scope_run).grid(row=0, column=3, padx=5)
        ttk.Button(frame, text="Stop", command=self._scope_stop).grid(row=0, column=4, padx=5)
        ttk.Button(frame, text="Single", command=self._scope_single).grid(row=0, column=5, padx=5)
        ttk.Button(frame, text="Get Waveform", command=self._scope_get_waveform).grid(row=0, column=6, padx=5)
        ttk.Button(frame, text="Save CSV", command=self._scope_save_csv).grid(row=0, column=7, padx=5)

        # Progress bar for waveform acquisition
        self.waveform_progress = ttk.Progressbar(frame, mode='indeterminate', length=150)
        self.waveform_progress.grid(row=1, column=0, columnspan=8, pady=5, sticky=tk.W+tk.E)
        self.waveform_progress.grid_remove()  # hidden initially

        # Waveform plot (if matplotlib available)
        if HAS_MPL:
            self.scope_fig = plt.Figure(figsize=(5, 3), dpi=80)
            self.scope_ax = self.scope_fig.add_subplot(111)
            self.scope_canvas = FigureCanvasTkAgg(self.scope_fig, tab)
            self.scope_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            self.scope_ax.set_title("Waveform Preview")
            self.scope_ax.set_xlabel("Time (s)")
            self.scope_ax.set_ylabel("Voltage (V)")
            self.scope_ax.grid(True, alpha=0.3)

    def _scope_auto_scale(self):
        inst = self._get_current_instrument()
        if inst and hasattr(inst, 'auto_scale'):
            inst.auto_scale()
            self.status_var.set("Auto-scale executed")
        else:
            messagebox.showwarning("Not Supported", "This instrument does not support auto-scale")

    def _scope_run(self):
        inst = self._get_current_instrument()
        if inst and hasattr(inst, 'run'):
            inst.run()

    def _scope_stop(self):
        inst = self._get_current_instrument()
        if inst and hasattr(inst, 'stop'):
            inst.stop()

    def _scope_single(self):
        inst = self._get_current_instrument()
        if inst and hasattr(inst, 'single'):
            inst.single()

    def _scope_get_waveform(self):
        inst = self._get_current_instrument()
        if not inst:
            messagebox.showwarning("No Instrument", "Connect an oscilloscope first")
            return

        # Show progress
        self.waveform_progress.grid()
        self.waveform_progress.start(10)

        def fetch():
            try:
                channel = self.scope_channel_var.get()
                x_data = y_data = None

                # Try PyMeasure methods first
                if HAS_PYMEASURE:
                    # Check for common waveform retrieval methods
                    if hasattr(inst, 'waveform') and callable(inst.waveform):
                        # Some PyMeasure instruments have waveform as a property that returns data
                        data = inst.waveform
                        if data is not None and len(data) == 2:
                            x_data, y_data = data
                    elif hasattr(inst, 'read_waveform') and callable(inst.read_waveform):
                        data = inst.read_waveform()
                        if data is not None and len(data) == 2:
                            x_data, y_data = data
                    elif hasattr(inst, 'get_waveform') and callable(inst.get_waveform):
                        # Our manual wrapper method
                        x_data, y_data = inst.get_waveform(channel=channel)

                # Fallback to manual wrapper
                if x_data is None and hasattr(inst, 'get_waveform'):
                    x_data, y_data = inst.get_waveform(channel=channel)

                def update_ui():
                    self.waveform_progress.stop()
                    self.waveform_progress.grid_remove()
                    if x_data is not None and y_data is not None:
                        if HAS_MPL:
                            self.scope_ax.clear()
                            self.scope_ax.plot(x_data, y_data)
                            self.scope_ax.set_title(f"Channel {channel}")
                            self.scope_ax.set_xlabel("Time (s)")
                            self.scope_ax.set_ylabel("Voltage (V)")
                            self.scope_ax.grid(True, alpha=0.3)
                            self.scope_canvas.draw()
                        # Store waveform in measurement
                        meas = Measurement(
                            timestamp=datetime.now(),
                            instrument=self._get_instrument_name(inst),
                            resource=self.resource_combo.get(),
                            measurement_type="Waveform",
                            value=len(y_data),
                            unit="points",
                            raw_data=(x_data, y_data)  # store as tuple
                        )
                        self.measurements.append(meas)
                        self._add_to_log(meas)
                        self.status_var.set(f"Waveform captured, {len(y_data)} points")
                    else:
                        messagebox.showerror("Waveform Error", "Failed to acquire waveform")
                self.ui_queue.schedule(update_ui)
            except Exception as e:
                self.ui_queue.schedule(lambda: messagebox.showerror("Error", str(e)))
                self.ui_queue.schedule(lambda: self.waveform_progress.stop())
                self.ui_queue.schedule(lambda: self.waveform_progress.grid_remove())

        threading.Thread(target=fetch, daemon=True).start()

    def _scope_save_csv(self):
        """Save current waveform to CSV."""
        # Find last waveform measurement
        waveform_meas = None
        for m in reversed(self.measurements):
            if m.measurement_type == "Waveform" and m.raw_data is not None:
                waveform_meas = m
                break
        if waveform_meas is None:
            messagebox.showwarning("No Waveform", "No waveform captured yet")
            return

        x_data, y_data = waveform_meas.raw_data
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile=f"waveform_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        if path:
            try:
                df = pd.DataFrame({'Time_s': x_data, 'Voltage_V': y_data})
                df.to_csv(path, index=False)
                self.status_var.set(f"Waveform saved to {Path(path).name}")
            except Exception as e:
                messagebox.showerror("Save Error", str(e))

    # ========== DMM Tab ==========
    def _create_dmm_tab(self):
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="⚡ DMM")

        frame = tk.LabelFrame(tab, text="Digital Multimeter", bg="white", padx=10, pady=10)
        frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(frame, text="Function:").grid(row=0, column=0, sticky=tk.W)
        self.dmm_func_var = tk.StringVar(value="DCV")
        func_combo = ttk.Combobox(frame, textvariable=self.dmm_func_var,
                                values=["DCV", "ACV", "DCI", "ACI", "2WΩ", "4WΩ", "Freq"])
        func_combo.grid(row=0, column=1, padx=5)
        ToolTip(func_combo, "Select measurement function")  # Fixed: ToolTip on widget, not variable

        tk.Label(frame, text="Range:").grid(row=1, column=0, sticky=tk.W)
        self.dmm_range_var = tk.StringVar(value="Auto")
        range_combo = ttk.Combobox(frame, textvariable=self.dmm_range_var,
                                    values=["Auto", "0.1", "1", "10", "100", "1000"], width=8)
        range_combo.grid(row=1, column=1, padx=5)
        ToolTip(range_combo, "Select measurement range (Auto or manual)")  # Fixed: ToolTip on widget, not variable

        self.dmm_nplc_var = tk.DoubleVar(value=1.0)
        tk.Label(frame, text="NPLC:").grid(row=2, column=0, sticky=tk.W)
        nplc_entry = ttk.Entry(frame, textvariable=self.dmm_nplc_var, width=5)
        nplc_entry.grid(row=2, column=1, sticky=tk.W)
        ToolTip(nplc_entry, "Number of power line cycles (integration time)")  # Fixed: ToolTip on widget, not variable

        ttk.Button(frame, text="Read", command=self._dmm_read).grid(row=3, column=0, pady=5)
        ttk.Button(frame, text="Continuous", command=self._dmm_continuous).grid(row=3, column=1)
        ttk.Button(frame, text="Stop", command=self._dmm_stop_continuous).grid(row=3, column=2)

        self.dmm_value_label = tk.Label(frame, text="---", font=("Arial", 24), fg="#2c3e50")
        self.dmm_value_label.grid(row=4, column=0, columnspan=3, pady=10)

        self.dmm_stats_label = tk.Label(frame, text="", font=("Arial", 8), fg="#7f8c8d")
        self.dmm_stats_label.grid(row=5, column=0, columnspan=3)

        # For continuous statistics
        self.dmm_readings = []

    def _dmm_read(self):
        inst = self._get_current_instrument()
        if not inst:
            messagebox.showwarning("No Instrument", "Connect a DMM first")
            return
        try:
            # Try to configure based on function
            func = self.dmm_func_var.get()
            if func == "DCV":
                if hasattr(inst, 'configure_dcv'):
                    inst.configure_dcv(nplc=self.dmm_nplc_var.get())
            # Read
            if hasattr(inst, 'read'):
                val = inst.read()
            elif hasattr(inst, 'measure_voltage') and func == "DCV":
                val = inst.measure_voltage()
            else:
                # Fallback: try simple query
                val = float(inst.query('READ?'))
            self.dmm_value_label.config(text=f"{val:.6f}")
            # Log measurement
            meas = Measurement(
                timestamp=datetime.now(),
                instrument=self._get_instrument_name(inst),
                resource=self.resource_combo.get(),
                measurement_type=func,
                value=val,
                unit="V" if "V" in func else "A" if "A" in func else "Ω"
            )
            self.measurements.append(meas)
            self._add_to_log(meas)
            # Update stats
            self.dmm_readings.append(val)
            if len(self.dmm_readings) > 100:
                self.dmm_readings.pop(0)
            if len(self.dmm_readings) > 1:
                mean = np.mean(self.dmm_readings)
                std = np.std(self.dmm_readings)
                self.dmm_stats_label.config(text=f"Mean: {mean:.6f}   Std: {std:.6f}")
        except Exception as e:
            messagebox.showerror("Read Error", str(e))

    def _dmm_continuous(self):
        if self._continuous:
            return
        self._continuous = True
        def loop():
            while self._continuous:
                # Schedule UI update via queue
                self.ui_queue.schedule(self._dmm_read)
                time.sleep(self.logging_interval)
        threading.Thread(target=loop, daemon=True).start()

    def _dmm_stop_continuous(self):
        self._continuous = False

    # ========== Power Supply Tab ==========
    def _create_power_supply_tab(self):
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="🔋 Power Supply")

        frame = tk.LabelFrame(tab, text="DC Power Supply / SourceMeter", bg="white", padx=10, pady=10)
        frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(frame, text="Channel:").grid(row=0, column=0, sticky=tk.W)
        self.ps_channel_var = tk.StringVar(value="1")
        ps_channel_combo = ttk.Combobox(frame, textvariable=self.ps_channel_var,
                                        values=["1", "2", "3", "P6V", "P25V", "N25V"], width=5)
        ps_channel_combo.grid(row=0, column=1, padx=5)
        ToolTip(ps_channel_combo, "Channel number (1-3) or specific output for Keysight E3631")

        tk.Label(frame, text="Voltage (V):").grid(row=1, column=0, sticky=tk.W)
        self.ps_voltage_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.ps_voltage_var, width=10).grid(row=1, column=1, padx=5)

        tk.Label(frame, text="Current (A):").grid(row=2, column=0, sticky=tk.W)
        self.ps_current_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.ps_current_var, width=10).grid(row=2, column=1, padx=5)

        ttk.Button(frame, text="Set", command=self._ps_set).grid(row=3, column=0, pady=5)
        ttk.Button(frame, text="Output ON", command=self._ps_on).grid(row=3, column=1)
        ttk.Button(frame, text="Output OFF", command=self._ps_off).grid(row=3, column=2)
        ttk.Button(frame, text="Measure", command=self._ps_measure).grid(row=4, column=0, columnspan=2)

        self.ps_read_label = tk.Label(frame, text="", font=("Arial", 12))
        self.ps_read_label.grid(row=5, column=0, columnspan=2, pady=5)

    def _ps_set(self):
        inst = self._get_current_instrument()
        if not inst:
            return
        try:
            v = float(self.ps_voltage_var.get())
            channel = self.ps_channel_var.get()
            # Use appropriate method
            if hasattr(inst, 'set_voltage'):
                # For Keithley 2400, single channel
                inst.set_voltage(v)
            elif hasattr(inst, 'set_voltage') and hasattr(inst, 'channel_map'):
                # Keysight E3631 style
                inst.set_voltage(v, channel)
            # Set current compliance if supported
            if hasattr(inst, 'set_current_compliance') and self.ps_current_var.get():
                c = float(self.ps_current_var.get())
                inst.set_current_compliance(c)
            self.status_var.set("Output parameters set")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _ps_on(self):
        inst = self._get_current_instrument()
        if inst and hasattr(inst, 'output_on'):
            inst.output_on()
            self.status_var.set("Output ON")

    def _ps_off(self):
        inst = self._get_current_instrument()
        if inst and hasattr(inst, 'output_off'):
            inst.output_off()
            self.status_var.set("Output OFF")

    def _ps_measure(self):
        inst = self._get_current_instrument()
        if not inst:
            return
        try:
            channel = self.ps_channel_var.get()
            v = None
            i = None
            if hasattr(inst, 'measure_voltage'):
                v = inst.measure_voltage()
                i = inst.measure_current()
            elif hasattr(inst, 'measure') and hasattr(inst, 'channel_map'):
                # Keysight E3631
                v = inst.measure(channel)
                # E3631 often can't measure current directly
                try:
                    i = float(inst.query(f'MEAS:CURR? {inst.channel_map.get(channel, "P6V")}'))
                except:
                    i = None
                    # Show note once per session
                    if not self._current_warning_shown and 'E3631' in self._get_instrument_name(inst):
                        self._current_warning_shown = True
                        self.status_var.set("Note: Current readback not available on Keysight E3631")
            else:
                # Generic query
                v = float(inst.query('MEAS:VOLT?'))
                i = float(inst.query('MEAS:CURR?'))

            if v is not None:
                self.ps_read_label.config(text=f"V={v:.4f} V, I={i:.4f} A" if i else f"V={v:.4f} V")
                # Log
                meas = Measurement(
                    timestamp=datetime.now(),
                    instrument=self._get_instrument_name(inst),
                    resource=self.resource_combo.get(),
                    measurement_type="V",
                    value=v,
                    unit="V"
                )
                self.measurements.append(meas)
                self._add_to_log(meas)
                if i is not None:
                    meas2 = Measurement(
                        timestamp=datetime.now(),
                        instrument=self._get_instrument_name(inst),
                        resource=self.resource_combo.get(),
                        measurement_type="I",
                        value=i,
                        unit="A"
                    )
                    self.measurements.append(meas2)
                    self._add_to_log(meas2)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ========== Function Generator Tab ==========
    def _create_function_gen_tab(self):
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="📶 Function Gen")

        frame = tk.LabelFrame(tab, text="Function Generator", bg="white", padx=10, pady=10)
        frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(frame, text="Waveform:").grid(row=0, column=0, sticky=tk.W)
        self.fg_wave_var = tk.StringVar(value="SIN")
        wave_combo = ttk.Combobox(frame, textvariable=self.fg_wave_var,
                                   values=["SIN", "SQU", "RAMP", "PULS", "NOISE"])
        wave_combo.grid(row=0, column=1, padx=5)
        ToolTip(wave_combo, "Select waveform type")

        tk.Label(frame, text="Frequency (Hz):").grid(row=1, column=0, sticky=tk.W)
        self.fg_freq_var = tk.StringVar(value="1000")
        ttk.Entry(frame, textvariable=self.fg_freq_var, width=10).grid(row=1, column=1)

        tk.Label(frame, text="Amplitude (Vpp):").grid(row=2, column=0, sticky=tk.W)
        self.fg_amp_var = tk.StringVar(value="1")
        ttk.Entry(frame, textvariable=self.fg_amp_var, width=10).grid(row=2, column=1)

        tk.Label(frame, text="Offset (V):").grid(row=3, column=0, sticky=tk.W)
        self.fg_offset_var = tk.StringVar(value="0")
        ttk.Entry(frame, textvariable=self.fg_offset_var, width=10).grid(row=3, column=1)

        ttk.Button(frame, text="Apply", command=self._fg_apply).grid(row=4, column=0, columnspan=2, pady=10)
        ttk.Button(frame, text="Output ON", command=self._fg_on).grid(row=4, column=2)
        ttk.Button(frame, text="Output OFF", command=self._fg_off).grid(row=4, column=3)

    def _fg_apply(self):
        inst = self._get_current_instrument()
        if not inst:
            return
        try:
            wave = self.fg_wave_var.get()
            freq = float(self.fg_freq_var.get())
            amp = float(self.fg_amp_var.get())
            offset = float(self.fg_offset_var.get())

            if hasattr(inst, 'set_waveform'):
                # Manufacturer-specific method (Rigol, etc.)
                inst.set_waveform(channel=1, wave=wave, freq=freq, amp=amp, offset=offset)
                self.status_var.set("Waveform applied")
            else:
                # Fallback: generic multi-command sequence (may work on some)
                self.status_var.set("Waveform applied (generic fallback — verify on device)")
                inst.write(f":SOUR1:FUNC {wave}")
                inst.write(f":SOUR1:FREQ {freq}")
                inst.write(f":SOUR1:VOLT {amp}")
                inst.write(f":SOUR1:VOLT:OFFS {offset}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _fg_on(self):
        inst = self._get_current_instrument()
        if inst:
            inst.write(':OUTP1 ON')

    def _fg_off(self):
        inst = self._get_current_instrument()
        if inst:
            inst.write(':OUTP1 OFF')

    # ========== Logging Tab ==========
    def _create_logging_tab(self):
        tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab, text="📋 Logging")

        # Log control buttons
        ctrl_frame = tk.Frame(tab, bg="white")
        ctrl_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(ctrl_frame, text="Clear Log", command=self._clear_log).pack(side=tk.LEFT, padx=2)
        ttk.Button(ctrl_frame, text="Copy All", command=self._copy_log).pack(side=tk.LEFT, padx=2)
        ttk.Button(ctrl_frame, text="Send to Table", command=self.send_to_table).pack(side=tk.LEFT, padx=2)
        ttk.Button(ctrl_frame, text="Export CSV", command=self._export_csv).pack(side=tk.LEFT, padx=2)

        ttk.Label(ctrl_frame, text="Interval (s):").pack(side=tk.LEFT, padx=10)
        self.interval_var = tk.DoubleVar(value=1.0)
        interval_entry = ttk.Entry(ctrl_frame, textvariable=self.interval_var, width=5)
        interval_entry.pack(side=tk.LEFT)
        ToolTip(interval_entry, "Logging interval for continuous measurements (seconds)")

        # Use Treeview for better readability
        tree_frame = tk.Frame(tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ('Time', 'Instrument', 'Type', 'Value', 'Unit')
        self.log_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
        self.log_tree.heading('Time', text='Time')
        self.log_tree.heading('Instrument', text='Instrument')
        self.log_tree.heading('Type', text='Type')
        self.log_tree.heading('Value', text='Value')
        self.log_tree.heading('Unit', text='Unit')
        self.log_tree.column('Time', width=70)
        self.log_tree.column('Instrument', width=120)
        self.log_tree.column('Type', width=80)
        self.log_tree.column('Value', width=100)
        self.log_tree.column('Unit', width=50)

        # Configure tags for color coding and alternating rows
        self.log_tree.tag_configure('waveform', background='#e1f5fe')   # light blue
        self.log_tree.tag_configure('voltage', background='#fff3e0')    # light orange
        self.log_tree.tag_configure('current', background='#e8f5e8')    # light green
        self.log_tree.tag_configure('resistance', background='#f3e5f5') # light purple
        self.log_tree.tag_configure('even', background='#f9f9f9')
        self.log_tree.tag_configure('odd', background='white')

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.log_tree.yview)
        self.log_tree.configure(yscrollcommand=scrollbar.set)
        self.log_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # ========== Helper Methods ==========
    def _get_current_instrument(self):
        res = self.resource_combo.get()
        return self.instruments.get(res)

    def _get_instrument_name(self, inst):
        if hasattr(inst, 'idn') and inst.idn:
            parts = inst.idn.split(',')
            if len(parts) >= 2:
                return f"{parts[0]} {parts[1]}".strip()
            else:
                return inst.idn[:30]
        return "Unknown"

    def _connect_device(self):
        res = self.resource_combo.get()
        if not res:
            return
        if res in self.instruments:
            # Disconnect first
            self._disconnect_device(res)

        try:
            if not self.rm:
                self.rm = pyvisa.ResourceManager()
            visa_resource = self.rm.open_resource(res)

            # Use factory to get appropriate wrapper
            inst = create_instrument_wrapper(visa_resource)
            success, msg = inst.connect()
            if success:
                self.instruments[res] = inst
                self.conn_indicator.config(fg="#2ecc71")
                self.connect_btn.config(text="🔌 Disconnect",
                                        command=lambda: self._disconnect_device(res))
                self.idn_label.config(text=msg[:60])
                self.status_var.set(f"Connected: {msg[:60]}")
                # Optionally check errors
                errors = inst.check_errors()
                if errors:
                    self.status_var.set(f"Device has {len(errors)} errors in queue")
            else:
                messagebox.showerror("Connection Failed", msg)
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))

    def _disconnect_device(self, res):
        inst = self.instruments.pop(res, None)
        if inst:
            inst.disconnect()
        if not self.instruments:  # if no instruments left, update indicator
            self.conn_indicator.config(fg="red")
            self.connect_btn.config(text="🔌 Connect", command=self._connect_device)
            self.idn_label.config(text="Not connected")
        self.status_var.set("Disconnected")

    def _disconnect_all(self):
        for res in list(self.instruments.keys()):
            self._disconnect_device(res)

    def _add_to_log(self, meas: Measurement):
        entry = (meas.timestamp.strftime('%H:%M:%S'),
                 meas.instrument,
                 meas.measurement_type,
                 f"{meas.value:.6f}" if meas.value is not None else "",
                 meas.unit)

        # Alternating row color first
        row_count = len(self.log_tree.get_children())
        base_tag = 'even' if row_count % 2 == 0 else 'odd'

        # Then type-specific tag (overwrites background if present)
        if meas.measurement_type == "Waveform":
            tag = ('waveform', base_tag)
        elif meas.unit == 'V':
            tag = ('voltage', base_tag)
        elif meas.unit == 'A':
            tag = ('current', base_tag)
        elif meas.unit == 'Ω':
            tag = ('resistance', base_tag)
        else:
            tag = (base_tag,)

        self.log_tree.insert('', 0, values=entry, tags=tag)

        # Limit to 100 entries
        children = self.log_tree.get_children()
        if len(children) > 100:
            self.log_tree.delete(children[-1])

    def _clear_log(self):
        for item in self.log_tree.get_children():
            self.log_tree.delete(item)

    def _copy_log(self):
        items = self.log_tree.get_children()
        if items:
            lines = []
            for item in items:
                values = self.log_tree.item(item, 'values')
                lines.append('\t'.join(str(v) for v in values))
            text = '\n'.join(lines)
            self.window.clipboard_clear()
            self.window.clipboard_append(text)
            self.status_var.set(f"Copied {len(items)} entries")

    def _export_csv(self):
        if not self.measurements:
            messagebox.showwarning("No Data", "No measurements to export")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile=f"measurements_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        if path:
            try:
                df = pd.DataFrame([m.to_dict() for m in self.measurements])
                df.to_csv(path, index=False)
                self.status_var.set(f"Exported to {Path(path).name}")
            except Exception as e:
                messagebox.showerror("Export Error", str(e))

    def send_to_table(self):
        data = self.collect_data()
        try:
            self.app.import_data_from_plugin(data)
            self.status_var.set(f"✅ Sent {len(data)} measurements to main table")
        except AttributeError:
            messagebox.showwarning("Integration", "Main app: import_data_from_plugin() required")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def collect_data(self) -> List[Dict]:
        return [m.to_dict() for m in self.measurements]

    def _on_close(self):
        self._continuous = False  # stop any continuous threads
        # Disconnect all instruments
        self._disconnect_all()
        if self.window:
            self.window.destroy()
            self.window = None

# ============================================================================
# SIMPLE PLUGIN REGISTRATION - NO DUPLICATES
# ============================================================================

def setup_plugin(main_app):
    """Register plugin - simple, no duplicates"""

    # Create plugin instance
    plugin = PhysicsTestMeasurementSuitePlugin(main_app)

    # Add to left panel if available
    if hasattr(main_app, 'left') and main_app.left is not None:
        main_app.left.add_hardware_button(
            name=PLUGIN_INFO.get("name", "Physics T&M Suite"),
            icon=PLUGIN_INFO.get("icon", "📟"),
            command=plugin.show_interface
        )
        print(f"✅ Added: {PLUGIN_INFO.get('name')}")

    return plugin
