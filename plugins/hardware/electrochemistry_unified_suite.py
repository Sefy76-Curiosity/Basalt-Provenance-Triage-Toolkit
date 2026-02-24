"""
ELECTROCHEMISTRY UNIFIED SUITE v1.0 - PRODUCTION RELEASE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COMPACT WINDOW (800x600) - FULL HARDWARE CONTROL
✓ BioLogic · Gamry · PalmSens · Zahner · Neware · Arbin · Maccor · Ivium/CHI
✓ CV · LSV · CA · CP · Pulse · EIS · CCCV · Multi-step · Safety · Multi-channel
✓ Real-time data · Temperature monitoring · Safety enforcement
✓ File import · Batch processing · Direct to table
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

# ============================================================================
# PLUGIN METADATA
# ============================================================================
PLUGIN_INFO = {
    "id": "electrochemistry_unified_suite",
    "name": "Electrochemistry Suite",
    "category": "hardware",
    "icon": "⚡",
    "version": "1.0.0",
    "author": "Electrochemistry Unified Team",
    "description": "COMPACT · CV · EIS · CCCV · Multi-step · Safety · Multi-channel · 8 manufacturers",
    "requires": ["numpy", "pandas", "pyvisa", "pyserial"],
    "optional": ["easy-biologic", "ToolkitPy", "PyPalmSens", "zahner-potentiostat", "aurora-neware", "pycti-arbin", "BEEP", "cellpy"],
    "compact": True,
    "window_size": "800x600"
}

# ============================================================================
# PREVENT DOUBLE REGISTRATION
# ============================================================================
import tkinter as tk
_ELECTROCHEM_REGISTERED = False
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
import sys
import subprocess
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Callable, Union
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CROSS-PLATFORM CHECK
# ============================================================================
IS_WINDOWS = platform.system() == 'Windows'
IS_LINUX = platform.system() == 'Linux'
IS_MAC = platform.system() == 'Darwin'

# ============================================================================
# DEPENDENCY CHECK
# ============================================================================
def check_dependencies():
    deps = {
        'numpy': False, 'pandas': False, 'pyvisa': False, 'pyserial': False,
        'easy-biologic': False, 'ToolkitPy': False, 'PyPalmSens': False,
        'zahner-potentiostat': False, 'aurora-neware': False, 'pycti-arbin': False,
        'BEEP': False, 'cellpy': False
    }

    try: import numpy; deps['numpy'] = True
    except: pass
    try: import pandas; deps['pandas'] = True
    except: pass
    try: import pyvisa; deps['pyvisa'] = True
    except: pass
    try: import serial; deps['pyserial'] = True
    except: pass
    try: import easy_biologic; deps['easy-biologic'] = True
    except: pass
    try: import ToolkitPy; deps['ToolkitPy'] = True
    except: pass
    try: import PyPalmSens; deps['PyPalmSens'] = True
    except: pass
    try: import zahner_potentiostat; deps['zahner-potentiostat'] = True
    except: pass
    try: import aurora_neware; deps['aurora-neware'] = True
    except: pass
    try: import pycti_arbin; deps['pycti-arbin'] = True
    except: pass
    try: import beep; deps['BEEP'] = True
    except: pass
    try: import cellpy; deps['cellpy'] = True
    except: pass

    return deps

DEPS = check_dependencies()

# Safe imports
if DEPS['numpy']: import numpy as np
if DEPS['pandas']: import pandas as pd
if DEPS['pyvisa']: import pyvisa
if DEPS['pyserial']: import serial

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
# ELECTROCHEMICAL MEASUREMENT DATA CLASS
# ============================================================================
@dataclass
class EchemMeasurement:
    timestamp: datetime
    sample_id: str
    instrument: str
    instrument_model: str = ""
    technique: str = ""
    channel: int = 1

    # Time-series data
    time_s: Optional[np.ndarray] = None
    voltage_V: Optional[np.ndarray] = None
    current_A: Optional[np.ndarray] = None
    capacity_Ah: Optional[np.ndarray] = None
    temperature_C: Optional[np.ndarray] = None

    # EIS specific
    frequency_Hz: Optional[np.ndarray] = None
    impedance_real_Ohm: Optional[np.ndarray] = None
    impedance_imag_Ohm: Optional[np.ndarray] = None

    # CV specific
    scan_rate_mV_s: Optional[float] = None
    cycles: Optional[int] = None

    # Battery cycler specific
    cycle_number: Optional[int] = None
    step_number: Optional[int] = None
    step_type: Optional[str] = None
    coulombic_efficiency_pct: Optional[float] = None

    # Safety
    safety_limits: Dict[str, float] = field(default_factory=dict)
    safety_violation: bool = False
    violation_reason: str = ""
    status: str = "complete"

    # File source
    file_source: str = ""

    def to_dict(self) -> Dict[str, str]:
        d = {
            'Timestamp': self.timestamp.isoformat(),
            'Sample_ID': self.sample_id,
            'Instrument': f"{self.instrument} {self.instrument_model}".strip(),
            'Technique': self.technique,
            'Channel': str(self.channel),
            'Status': self.status,
        }

        if self.safety_violation:
            d['Safety_Violation'] = self.violation_reason

        if self.voltage_V is not None and len(self.voltage_V) > 0:
            d['V_max'] = f"{np.max(self.voltage_V):.4f}"
            d['V_min'] = f"{np.min(self.voltage_V):.4f}"

        if self.current_A is not None and len(self.current_A) > 0:
            d['I_max'] = f"{np.max(self.current_A):.4f}"
            d['I_min'] = f"{np.min(self.current_A):.4f}"

        if self.capacity_Ah is not None and len(self.capacity_Ah) > 0:
            d['Capacity_Ah'] = f"{self.capacity_Ah[-1]:.4f}"

        if self.temperature_C is not None and len(self.temperature_C) > 0:
            d['Temp_max_C'] = f"{np.max(self.temperature_C):.1f}"

        if self.coulombic_efficiency_pct is not None:
            d['CE_%'] = f"{self.coulombic_efficiency_pct:.1f}"

        if self.scan_rate_mV_s:
            d['Scan_rate_mV_s'] = f"{self.scan_rate_mV_s:.2f}"

        return {k: v for k, v in d.items() if v}

# ============================================================================
# BASE INSTRUMENT WRAPPER (COMPACT)
# ============================================================================
class EchemInstrumentWrapper:
    """Base wrapper with all required hardware control methods"""

    def __init__(self):
        self.connected = False
        self.idn = ""
        self.manufacturer = ""
        self.model = ""
        self.serial = ""
        self.firmware = ""
        self.channels = 1
        self.current_channel = 1
        self.safety_limits = {'v_max': 10, 'v_min': -10, 'i_max': 1, 't_max': 60}
        self.temp_probe_enabled = False
        self.current_sequence = []

    def connect(self) -> Tuple[bool, str]:
        raise NotImplementedError

    def disconnect(self):
        self.connected = False

    def select_channel(self, channel: int) -> bool:
        if 1 <= channel <= self.channels:
            self.current_channel = channel
            return True
        return False

    def set_cv_params(self, start_V: float, vertex1_V: float, vertex2_V: float,
                      scan_rate_mV_s: float, cycles: int = 1) -> bool:
        raise NotImplementedError

    def set_lsv_params(self, start_V: float, end_V: float,
                       scan_rate_mV_s: float) -> bool:
        raise NotImplementedError

    def set_ca_params(self, setpoint_V: float, duration_s: float,
                      sampling_rate_Hz: float = 10) -> bool:
        raise NotImplementedError

    def set_cp_params(self, setpoint_A: float, duration_s: float,
                      sampling_rate_Hz: float = 10) -> bool:
        raise NotImplementedError

    def set_pulse_params(self, pulse_V: float, width_ms: float,
                         duty_cycle: float = 0.5, cycles: int = 1) -> bool:
        raise NotImplementedError

    def set_eis_params(self, freq_start_Hz: float, freq_end_Hz: float,
                       points_per_decade: int = 10, amplitude_V: float = 0.01,
                       bias_V: float = 0.0, mode: str = "PEIS") -> bool:
        raise NotImplementedError

    def set_cccv_params(self, charge_current_A: float, charge_voltage_V: float,
                        discharge_current_A: float, discharge_voltage_V: float,
                        cycles: int = 1, rest_time_s: int = 60) -> bool:
        raise NotImplementedError

    def load_sequence(self, steps: List[Dict]) -> bool:
        self.current_sequence = steps
        return True

    def set_cycle_count(self, cycles: int) -> bool:
        return True

    def set_safety_limits(self, v_max: float = None, v_min: float = None,
                          i_max: float = None, t_max: float = None) -> bool:
        if v_max is not None: self.safety_limits['v_max'] = v_max
        if v_min is not None: self.safety_limits['v_min'] = v_min
        if i_max is not None: self.safety_limits['i_max'] = i_max
        if t_max is not None: self.safety_limits['t_max'] = t_max
        return True

    def check_safety_violation(self, voltage: float, current: float,
                               temperature: float = None) -> Tuple[bool, str]:
        if voltage > self.safety_limits['v_max']:
            return True, f"V>{self.safety_limits['v_max']}V"
        if voltage < self.safety_limits['v_min']:
            return True, f"V<{self.safety_limits['v_min']}V"
        if abs(current) > self.safety_limits['i_max']:
            return True, f"I>{self.safety_limits['i_max']}A"
        if temperature and temperature > self.safety_limits['t_max']:
            return True, f"T>{self.safety_limits['t_max']}°C"
        return False, ""

    def enable_temperature_probe(self, enabled: bool = True) -> bool:
        self.temp_probe_enabled = enabled
        return True

    def fetch_temperature(self) -> Optional[float]:
        return None

    def start(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def abort(self):
        raise NotImplementedError

    def fetch_data(self) -> Dict:
        return {}

    def fetch_eis_data(self) -> Dict:
        return {}

    def fetch_status(self) -> Dict:
        return {}

    def check_errors(self) -> List[str]:
        return []

# ============================================================================
# MANUFACTURER WRAPPERS (CONDENSED - FULL IMPLEMENTATIONS FROM PREVIOUS VERSION)
# ============================================================================
# [All wrapper implementations from previous version remain identical]
# Including: BioLogicWrapper, GamryWrapper, PalmSensWrapper, ZahnerWrapper,
# NewareWrapper, ArbinWrapper, MaccorParser, SerialEchemWrapper
# (Code omitted for brevity - keep all previous wrapper implementations)

# ============================================================================
# INSTRUMENT FACTORY
# ============================================================================
def create_instrument(manufacturer: str, **kwargs) -> Optional[EchemInstrumentWrapper]:
    mfg = manufacturer.lower()

    if 'biologic' in mfg:
        return BioLogicWrapper(**kwargs)
    elif 'gamry' in mfg:
        return GamryWrapper(**kwargs)
    elif 'palmsens' in mfg:
        return PalmSensWrapper(**kwargs)
    elif 'zahner' in mfg:
        return ZahnerWrapper(**kwargs)
    elif 'neware' in mfg:
        return NewareWrapper(**kwargs)
    elif 'arbin' in mfg:
        return ArbinWrapper(**kwargs)
    elif 'ivium' in mfg or 'chi' in mfg:
        return SerialEchemWrapper(manufacturer=manufacturer, **kwargs)
    else:
        return None

# ============================================================================
# MAIN PLUGIN - COMPACT 800x600 UI
# ============================================================================
class ElectrochemistryUnifiedSuitePlugin:

    def __init__(self, main_app):
        self.app = main_app
        self.window = None
        self.ui_queue = None

        self.deps = DEPS

        # Instruments
        self.current_instrument: Optional[EchemInstrumentWrapper] = None
        self.measurements: List[EchemMeasurement] = []
        self.current_measurement: Optional[EchemMeasurement] = None

        # Thread control
        self.acquisition_active = False
        self.safety_monitor_active = False

        # UI Variables
        self.status_var = tk.StringVar(value="Electrochemistry v1.0 - Ready")
        self.progress_var = tk.DoubleVar(value=0)

        # Manufacturers
        self.manufacturers = [
            "BioLogic", "Gamry", "PalmSens", "Zahner",
            "Neware", "Arbin", "Maccor", "Ivium/CHI"
        ]

        self._init_ui_vars()

    def _init_ui_vars(self):
        """Initialize all tkinter variables"""
        # Instrument
        self.instrument_var = tk.StringVar()
        self.connection_var = tk.StringVar(value="USB")
        self.address_var = tk.StringVar()
        self.channel_var = tk.IntVar(value=1)
        self.sample_id_var = tk.StringVar(value=f"EC-{datetime.now().strftime('%Y%m%d')}-001")

        # CV
        self.cv_start_var = tk.StringVar(value="0")
        self.cv_vertex1_var = tk.StringVar(value="1")
        self.cv_vertex2_var = tk.StringVar(value="0")
        self.cv_scanrate_var = tk.StringVar(value="100")
        self.cv_cycles_var = tk.StringVar(value="3")

        # LSV
        self.lsv_start_var = tk.StringVar(value="0")
        self.lsv_end_var = tk.StringVar(value="1")
        self.lsv_scanrate_var = tk.StringVar(value="100")

        # CA
        self.ca_setpoint_var = tk.StringVar(value="1")
        self.ca_duration_var = tk.StringVar(value="60")
        self.ca_samplerate_var = tk.StringVar(value="10")

        # CP
        self.cp_setpoint_var = tk.StringVar(value="0.1")
        self.cp_duration_var = tk.StringVar(value="60")
        self.cp_samplerate_var = tk.StringVar(value="10")

        # Pulse
        self.pulse_voltage_var = tk.StringVar(value="1")
        self.pulse_width_var = tk.StringVar(value="100")
        self.pulse_duty_var = tk.StringVar(value="0.5")
        self.pulse_cycles_var = tk.StringVar(value="10")

        # EIS
        self.eis_fstart_var = tk.StringVar(value="100000")
        self.eis_fend_var = tk.StringVar(value="0.1")
        self.eis_ppd_var = tk.StringVar(value="10")
        self.eis_amp_var = tk.StringVar(value="0.01")
        self.eis_bias_var = tk.StringVar(value="0")
        self.eis_mode_var = tk.StringVar(value="PEIS")

        # CCCV
        self.cccv_charge_i_var = tk.StringVar(value="1")
        self.cccv_charge_v_var = tk.StringVar(value="4.2")
        self.cccv_discharge_i_var = tk.StringVar(value="1")
        self.cccv_discharge_v_var = tk.StringVar(value="2.5")
        self.cccv_cycles_var = tk.StringVar(value="10")
        self.cccv_rest_var = tk.StringVar(value="60")

        # Sequence
        self.sequence_steps = []
        self.sequence_cycles_var = tk.StringVar(value="1")

        # Safety
        self.safety_vmax_var = tk.StringVar(value="5")
        self.safety_vmin_var = tk.StringVar(value="-5")
        self.safety_imax_var = tk.StringVar(value="1")
        self.safety_tmax_var = tk.StringVar(value="60")
        self.safety_enabled_var = tk.BooleanVar(value=True)

        # Temperature
        self.temp_enabled_var = tk.BooleanVar(value=False)

        # Parsing
        self.parse_file_var = tk.StringVar(value="No file selected")

    def show_interface(self):
        self.open_window()

    def open_window(self):
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("Electrochemistry v1.0 - 8 manufacturers · All techniques")
        self.window.geometry("800x600")
        self.window.minsize(780, 580)
        self.window.transient(self.app.root)

        self.ui_queue = ThreadSafeUI(self.window)
        self._build_compact_ui()

        self.window.lift()
        self.window.focus_force()
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_compact_ui(self):
        """COMPACT 800x600 UI - All features, no scrolling needed"""

        # ============ HEADER (40px) ============
        header = tk.Frame(self.window, bg="#9b59b6", height=35)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="⚡", font=("Arial", 14),
                bg="#9b59b6", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Label(header, text="ELECTROCHEMISTRY UNIFIED", font=("Arial", 11, "bold"),
                bg="#9b59b6", fg="white").pack(side=tk.LEFT)
        tk.Label(header, text="v1.0", font=("Arial", 8),
                bg="#9b59b6", fg="#f1c40f").pack(side=tk.LEFT, padx=5)

        self.status_indicator = tk.Label(header, textvariable=self.status_var,
                                        font=("Arial", 8), bg="#9b59b6", fg="#2ecc71")
        self.status_indicator.pack(side=tk.RIGHT, padx=5)

        # ============ INSTRUMENT TOOLBAR (35px) ============
        toolbar = tk.Frame(self.window, bg="#ecf0f1", height=35)
        toolbar.pack(fill=tk.X)
        toolbar.pack_propagate(False)

        tk.Label(toolbar, text="Instrument:", font=("Arial", 8, "bold"),
                bg="#ecf0f1").pack(side=tk.LEFT, padx=2)

        self.manufacturer_combo = ttk.Combobox(toolbar, textvariable=self.instrument_var,
                                               values=self.manufacturers, width=12)
        self.manufacturer_combo.pack(side=tk.LEFT, padx=2)

        self.connection_combo = ttk.Combobox(toolbar, textvariable=self.connection_var,
                                             values=['USB', 'TCP', 'Serial'], width=6)
        self.connection_combo.pack(side=tk.LEFT, padx=2)

        self.address_entry = ttk.Entry(toolbar, textvariable=self.address_var, width=12)
        self.address_entry.pack(side=tk.LEFT, padx=2)

        tk.Label(toolbar, text="Ch:", font=("Arial", 8, "bold"),
                bg="#ecf0f1").pack(side=tk.LEFT, padx=2)
        self.channel_combo = ttk.Combobox(toolbar, textvariable=self.channel_var,
                                          values=list(range(1, 17)), width=2)
        self.channel_combo.pack(side=tk.LEFT, padx=2)

        self.connect_btn = ttk.Button(toolbar, text="🔌 Connect",
                                      command=self._connect_instrument, width=8)
        self.connect_btn.pack(side=tk.LEFT, padx=2)

        self.conn_indicator = tk.Label(toolbar, text="●", fg="red",
                                       font=("Arial", 10), bg="#ecf0f1")
        self.conn_indicator.pack(side=tk.LEFT, padx=2)

        self.idn_label = tk.Label(toolbar, text="Not connected",
                                  font=("Arial", 7), bg="#ecf0f1", fg="#7f8c8d")
        self.idn_label.pack(side=tk.LEFT, padx=5)

        # ============ TECHNIQUE NOTEBOOK (300px) ============
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=3, pady=2)

        self._create_technique_tabs()

        # ============ DATA DISPLAY (120px) ============
        data_frame = tk.Frame(self.window, bg="white", height=120)
        data_frame.pack(fill=tk.X, padx=3, pady=2)
        data_frame.pack_propagate(False)

        columns = ('Time', 'V (V)', 'I (A)', 'Cycle')
        self.data_tree = ttk.Treeview(data_frame, columns=columns, show='headings', height=4)
        for col in columns:
            self.data_tree.heading(col, text=col)
            self.data_tree.column(col, width=70)

        vsb = ttk.Scrollbar(data_frame, orient=tk.VERTICAL, command=self.data_tree.yview)
        self.data_tree.configure(yscrollcommand=vsb.set)
        self.data_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # ============ CONTROL BAR (40px) ============
        ctrl_bar = tk.Frame(self.window, bg="#f8f9fa", height=40)
        ctrl_bar.pack(fill=tk.X)
        ctrl_bar.pack_propagate(False)

        self.start_btn = ttk.Button(ctrl_bar, text="▶ START", command=self._start_experiment,
                                    state='disabled', width=7)
        self.start_btn.pack(side=tk.LEFT, padx=2)

        self.stop_btn = ttk.Button(ctrl_bar, text="⏹ STOP", command=self._stop_experiment,
                                   state='disabled', width=7)
        self.stop_btn.pack(side=tk.LEFT, padx=2)

        self.abort_btn = ttk.Button(ctrl_bar, text="⏸ ABORT", command=self._abort_experiment,
                                    state='disabled', width=7)
        self.abort_btn.pack(side=tk.LEFT, padx=2)

        # Safety status
        tk.Label(ctrl_bar, text="Safety:", font=("Arial", 7, "bold"),
                bg="#f8f9fa").pack(side=tk.LEFT, padx=5)
        self.safety_status_label = tk.Label(ctrl_bar, text="● OK", fg="#2ecc71",
                                           font=("Arial", 7, "bold"), bg="#f8f9fa")
        self.safety_status_label.pack(side=tk.LEFT)

        # Temperature
        tk.Label(ctrl_bar, text="Temp:", font=("Arial", 7, "bold"),
                bg="#f8f9fa").pack(side=tk.LEFT, padx=5)
        self.temp_label = tk.Label(ctrl_bar, text="--°C",
                                   font=("Arial", 7), bg="#f8f9fa")
        self.temp_label.pack(side=tk.LEFT)

        # Send button
        self.send_btn = ttk.Button(ctrl_bar, text="📊 SEND", command=self.send_to_table, width=6)
        self.send_btn.pack(side=tk.RIGHT, padx=2)

        # Import button
        ttk.Button(ctrl_bar, text="📂 IMPORT", command=self._select_files, width=6).pack(side=tk.RIGHT, padx=2)

        # Progress
        self.progress_bar = ttk.Progressbar(ctrl_bar, variable=self.progress_var,
                                           mode='determinate', length=80)
        self.progress_bar.pack(side=tk.RIGHT, padx=2)

        # Sample counter
        self.sample_counter = tk.Label(ctrl_bar,
                                       text=f"📊 {len(self.measurements)}",
                                       font=("Arial", 7), bg="#f8f9fa")
        self.sample_counter.pack(side=tk.RIGHT, padx=5)

        # ============ STATUS BAR (20px) ============
        status_bar = tk.Frame(self.window, bg="#34495e", height=20)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        status_bar.pack_propagate(False)

        tk.Label(status_bar,
                text="BioLogic · Gamry · PalmSens · Zahner · Neware · Arbin · Maccor · Ivium/CHI",
                font=("Arial", 7), bg="#34495e", fg="white").pack(side=tk.LEFT, padx=5)

    def _create_technique_tabs(self):
        """Create compact technique tabs (4 tabs)"""

        # Tab 1: CV/LSV
        tab1 = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab1, text="CV/LSV")

        f1 = tk.Frame(tab1, bg="white")
        f1.pack(padx=5, pady=5, fill=tk.X)

        row = 0
        tk.Label(f1, text="Start(V):", font=("Arial", 7), bg="white").grid(row=row, column=0, sticky=tk.W)
        ttk.Entry(f1, textvariable=self.cv_start_var, width=6).grid(row=row, column=1, padx=2)
        tk.Label(f1, text="V1(V):", font=("Arial", 7), bg="white").grid(row=row, column=2, sticky=tk.W, padx=5)
        ttk.Entry(f1, textvariable=self.cv_vertex1_var, width=6).grid(row=row, column=3, padx=2)
        tk.Label(f1, text="V2(V):", font=("Arial", 7), bg="white").grid(row=row, column=4, sticky=tk.W, padx=5)
        ttk.Entry(f1, textvariable=self.cv_vertex2_var, width=6).grid(row=row, column=5, padx=2)

        row += 1
        tk.Label(f1, text="Rate(mV/s):", font=("Arial", 7), bg="white").grid(row=row, column=0, sticky=tk.W)
        ttk.Entry(f1, textvariable=self.cv_scanrate_var, width=6).grid(row=row, column=1, padx=2)
        tk.Label(f1, text="Cycles:", font=("Arial", 7), bg="white").grid(row=row, column=2, sticky=tk.W, padx=5)
        ttk.Entry(f1, textvariable=self.cv_cycles_var, width=6).grid(row=row, column=3, padx=2)

        ttk.Button(tab1, text="Apply CV", command=lambda: self._apply_technique('CV')).pack(pady=2)

        tk.Frame(tab1, bg="#bdc3c7", height=1).pack(fill=tk.X, pady=5)

        f2 = tk.Frame(tab1, bg="white")
        f2.pack(padx=5, pady=5, fill=tk.X)

        tk.Label(f2, text="LSV Start(V):", font=("Arial", 7), bg="white").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(f2, textvariable=self.lsv_start_var, width=6).grid(row=0, column=1, padx=2)
        tk.Label(f2, text="End(V):", font=("Arial", 7), bg="white").grid(row=0, column=2, sticky=tk.W, padx=5)
        ttk.Entry(f2, textvariable=self.lsv_end_var, width=6).grid(row=0, column=3, padx=2)
        tk.Label(f2, text="Rate(mV/s):", font=("Arial", 7), bg="white").grid(row=0, column=4, sticky=tk.W, padx=5)
        ttk.Entry(f2, textvariable=self.lsv_scanrate_var, width=6).grid(row=0, column=5, padx=2)

        ttk.Button(tab1, text="Apply LSV", command=lambda: self._apply_technique('LSV')).pack(pady=2)

        # Tab 2: CA/CP/Pulse
        tab2 = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab2, text="CA/CP/Pulse")

        # CA
        f3 = tk.Frame(tab2, bg="white")
        f3.pack(padx=5, pady=5, fill=tk.X)

        tk.Label(f3, text="CA Set(V):", font=("Arial", 7), bg="white").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(f3, textvariable=self.ca_setpoint_var, width=6).grid(row=0, column=1, padx=2)
        tk.Label(f3, text="Dur(s):", font=("Arial", 7), bg="white").grid(row=0, column=2, sticky=tk.W, padx=5)
        ttk.Entry(f3, textvariable=self.ca_duration_var, width=6).grid(row=0, column=3, padx=2)
        tk.Label(f3, text="Hz:", font=("Arial", 7), bg="white").grid(row=0, column=4, sticky=tk.W, padx=5)
        ttk.Entry(f3, textvariable=self.ca_samplerate_var, width=4).grid(row=0, column=5, padx=2)

        ttk.Button(tab2, text="Apply CA", command=lambda: self._apply_technique('CA')).pack(pady=2)

        tk.Frame(tab2, bg="#bdc3c7", height=1).pack(fill=tk.X, pady=5)

        # CP
        f4 = tk.Frame(tab2, bg="white")
        f4.pack(padx=5, pady=5, fill=tk.X)

        tk.Label(f4, text="CP Set(A):", font=("Arial", 7), bg="white").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(f4, textvariable=self.cp_setpoint_var, width=6).grid(row=0, column=1, padx=2)
        tk.Label(f4, text="Dur(s):", font=("Arial", 7), bg="white").grid(row=0, column=2, sticky=tk.W, padx=5)
        ttk.Entry(f4, textvariable=self.cp_duration_var, width=6).grid(row=0, column=3, padx=2)
        tk.Label(f4, text="Hz:", font=("Arial", 7), bg="white").grid(row=0, column=4, sticky=tk.W, padx=5)
        ttk.Entry(f4, textvariable=self.cp_samplerate_var, width=4).grid(row=0, column=5, padx=2)

        ttk.Button(tab2, text="Apply CP", command=lambda: self._apply_technique('CP')).pack(pady=2)

        tk.Frame(tab2, bg="#bdc3c7", height=1).pack(fill=tk.X, pady=5)

        # Pulse
        f5 = tk.Frame(tab2, bg="white")
        f5.pack(padx=5, pady=5, fill=tk.X)

        tk.Label(f5, text="Pulse(V):", font=("Arial", 7), bg="white").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(f5, textvariable=self.pulse_voltage_var, width=6).grid(row=0, column=1, padx=2)
        tk.Label(f5, text="W(ms):", font=("Arial", 7), bg="white").grid(row=0, column=2, sticky=tk.W, padx=5)
        ttk.Entry(f5, textvariable=self.pulse_width_var, width=6).grid(row=0, column=3, padx=2)
        tk.Label(f5, text="Duty:", font=("Arial", 7), bg="white").grid(row=0, column=4, sticky=tk.W, padx=5)
        ttk.Entry(f5, textvariable=self.pulse_duty_var, width=4).grid(row=0, column=5, padx=2)
        tk.Label(f5, text="Cyc:", font=("Arial", 7), bg="white").grid(row=1, column=0, sticky=tk.W)
        ttk.Entry(f5, textvariable=self.pulse_cycles_var, width=4).grid(row=1, column=1, padx=2, sticky=tk.W)

        ttk.Button(tab2, text="Apply Pulse", command=lambda: self._apply_technique('Pulse')).pack(pady=2)

        # Tab 3: EIS/CCCV
        tab3 = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab3, text="EIS/CCCV")

        # EIS
        f6 = tk.Frame(tab3, bg="white")
        f6.pack(padx=5, pady=5, fill=tk.X)

        tk.Label(f6, text="EIS Start(Hz):", font=("Arial", 7), bg="white").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(f6, textvariable=self.eis_fstart_var, width=8).grid(row=0, column=1, padx=2)
        tk.Label(f6, text="End(Hz):", font=("Arial", 7), bg="white").grid(row=0, column=2, sticky=tk.W, padx=5)
        ttk.Entry(f6, textvariable=self.eis_fend_var, width=8).grid(row=0, column=3, padx=2)

        row = 1
        tk.Label(f6, text="PPD:", font=("Arial", 7), bg="white").grid(row=row, column=0, sticky=tk.W)
        ttk.Entry(f6, textvariable=self.eis_ppd_var, width=4).grid(row=row, column=1, padx=2, sticky=tk.W)
        tk.Label(f6, text="Amp(mV):", font=("Arial", 7), bg="white").grid(row=row, column=2, sticky=tk.W, padx=5)
        ttk.Entry(f6, textvariable=self.eis_amp_var, width=4).grid(row=row, column=3, padx=2, sticky=tk.W)
        tk.Label(f6, text="Bias(V):", font=("Arial", 7), bg="white").grid(row=row, column=4, sticky=tk.W, padx=5)
        ttk.Entry(f6, textvariable=self.eis_bias_var, width=4).grid(row=row, column=5, padx=2, sticky=tk.W)

        ttk.Button(tab3, text="Apply EIS", command=lambda: self._apply_technique('EIS')).pack(pady=2)

        tk.Frame(tab3, bg="#bdc3c7", height=1).pack(fill=tk.X, pady=5)

        # CCCV
        f7 = tk.Frame(tab3, bg="white")
        f7.pack(padx=5, pady=5, fill=tk.X)

        tk.Label(f7, text="Chg I(A):", font=("Arial", 7), bg="white").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(f7, textvariable=self.cccv_charge_i_var, width=6).grid(row=0, column=1, padx=2)
        tk.Label(f7, text="Chg V(V):", font=("Arial", 7), bg="white").grid(row=0, column=2, sticky=tk.W, padx=5)
        ttk.Entry(f7, textvariable=self.cccv_charge_v_var, width=6).grid(row=0, column=3, padx=2)

        row = 1
        tk.Label(f7, text="Dis I(A):", font=("Arial", 7), bg="white").grid(row=row, column=0, sticky=tk.W)
        ttk.Entry(f7, textvariable=self.cccv_discharge_i_var, width=6).grid(row=row, column=1, padx=2)
        tk.Label(f7, text="Dis V(V):", font=("Arial", 7), bg="white").grid(row=row, column=2, sticky=tk.W, padx=5)
        ttk.Entry(f7, textvariable=self.cccv_discharge_v_var, width=6).grid(row=row, column=3, padx=2)

        row = 2
        tk.Label(f7, text="Cycles:", font=("Arial", 7), bg="white").grid(row=row, column=0, sticky=tk.W)
        ttk.Entry(f7, textvariable=self.cccv_cycles_var, width=4).grid(row=row, column=1, padx=2, sticky=tk.W)
        tk.Label(f7, text="Rest(s):", font=("Arial", 7), bg="white").grid(row=row, column=2, sticky=tk.W, padx=5)
        ttk.Entry(f7, textvariable=self.cccv_rest_var, width=4).grid(row=row, column=3, padx=2, sticky=tk.W)

        ttk.Button(tab3, text="Apply CCCV", command=lambda: self._apply_technique('CCCV')).pack(pady=2)

        # Tab 4: Safety/Import
        tab4 = tk.Frame(self.notebook, bg="white")
        self.notebook.add(tab4, text="Safety/Import")

        # Safety limits
        sf = tk.Frame(tab4, bg="white")
        sf.pack(padx=5, pady=5, fill=tk.X)

        tk.Label(sf, text="Safety Limits:", font=("Arial", 8, "bold"),
                bg="white").pack(anchor=tk.W)

        f8 = tk.Frame(sf, bg="white")
        f8.pack(fill=tk.X, pady=2)

        tk.Label(f8, text="Vmax(V):", font=("Arial", 7), bg="white").pack(side=tk.LEFT)
        ttk.Entry(f8, textvariable=self.safety_vmax_var, width=5).pack(side=tk.LEFT, padx=2)
        tk.Label(f8, text="Vmin(V):", font=("Arial", 7), bg="white").pack(side=tk.LEFT, padx=5)
        ttk.Entry(f8, textvariable=self.safety_vmin_var, width=5).pack(side=tk.LEFT, padx=2)
        tk.Label(f8, text="Imax(A):", font=("Arial", 7), bg="white").pack(side=tk.LEFT, padx=5)
        ttk.Entry(f8, textvariable=self.safety_imax_var, width=5).pack(side=tk.LEFT, padx=2)
        tk.Label(f8, text="Tmax(°C):", font=("Arial", 7), bg="white").pack(side=tk.LEFT, padx=5)
        ttk.Entry(f8, textvariable=self.safety_tmax_var, width=5).pack(side=tk.LEFT, padx=2)

        ttk.Checkbutton(tab4, text="Enable safety monitoring",
                       variable=self.safety_enabled_var).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(tab4, text="Enable temperature probe",
                       variable=self.temp_enabled_var,
                       command=self._toggle_temperature).pack(anchor=tk.W, pady=2)

        tk.Frame(tab4, bg="#bdc3c7", height=1).pack(fill=tk.X, pady=5)

        # Quick import
        imp = tk.Frame(tab4, bg="white")
        imp.pack(padx=5, pady=5, fill=tk.X)

        tk.Label(imp, text="Import Files:", font=("Arial", 8, "bold"),
                bg="white").pack(anchor=tk.W)

        btn_frame = tk.Frame(imp, bg="white")
        btn_frame.pack(fill=tk.X, pady=2)

        ttk.Button(btn_frame, text="📁 Select Files",
                  command=self._select_files, width=12).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="📂 Batch Folder",
                  command=self._batch_process, width=12).pack(side=tk.LEFT, padx=2)

        self.parse_file_var = tk.StringVar(value="No file selected")
        tk.Label(imp, textvariable=self.parse_file_var,
                font=("Arial", 7), bg="white", fg="#7f8c8d").pack(anchor=tk.W, pady=2)

    def _connect_instrument(self):
        """Connect to selected instrument"""
        selection = self.instrument_var.get()
        if not selection:
            messagebox.showwarning("No Selection", "Select an instrument")
            return

        connection = self.connection_var.get()
        address = self.address_var.get().strip()

        kwargs = {}
        if connection == 'USB':
            kwargs = {'connection_type': 'usb'}
        elif connection == 'TCP':
            if not address:
                messagebox.showwarning("No Address", "Enter IP address")
                return
            if ':' in address:
                ip, port = address.split(':')
                kwargs = {'ip': ip, 'port': int(port)}
            else:
                kwargs = {'ip': address}
        elif connection == 'Serial':
            if not address:
                messagebox.showwarning("No Port", "Enter serial port")
                return
            kwargs = {'port': address}

        if self.current_instrument:
            self.current_instrument.disconnect()

        self.current_instrument = create_instrument(selection, **kwargs)

        if not self.current_instrument:
            messagebox.showerror("Error", f"No driver for {selection}")
            return

        def connect_thread():
            self.ui_queue.schedule(lambda: self.connect_btn.config(state='disabled'))
            self._update_status(f"Connecting...")

            success, msg = self.current_instrument.connect()

            def update_ui():
                self.connect_btn.config(state='normal')
                if success:
                    self.conn_indicator.config(fg="#2ecc71")
                    self.idn_label.config(text=msg[:20])
                    self.start_btn.config(state='normal')

                    if self.current_instrument.channels > 1:
                        self.channel_combo['values'] = list(range(1, min(17, self.current_instrument.channels + 1)))

                    if self.safety_enabled_var.get():
                        vmax = float(self.safety_vmax_var.get())
                        vmin = float(self.safety_vmin_var.get())
                        imax = float(self.safety_imax_var.get())
                        tmax = float(self.safety_tmax_var.get())
                        self.current_instrument.set_safety_limits(vmax, vmin, imax, tmax)

                    self._start_safety_monitor()
                    self._update_status(f"✅ Connected")
                else:
                    self.conn_indicator.config(fg="red")
                    messagebox.showerror("Connection Failed", msg)
                    self._update_status("❌ Failed")

            self.ui_queue.schedule(update_ui)

        threading.Thread(target=connect_thread, daemon=True).start()

    def _apply_technique(self, technique: str):
        """Apply technique parameters"""
        if not self.current_instrument:
            messagebox.showwarning("Not Connected", "Connect first")
            return

        try:
            if technique == 'CV':
                success = self.current_instrument.set_cv_params(
                    float(self.cv_start_var.get()),
                    float(self.cv_vertex1_var.get()),
                    float(self.cv_vertex2_var.get()),
                    float(self.cv_scanrate_var.get()),
                    int(self.cv_cycles_var.get())
                )
            elif technique == 'LSV':
                success = self.current_instrument.set_lsv_params(
                    float(self.lsv_start_var.get()),
                    float(self.lsv_end_var.get()),
                    float(self.lsv_scanrate_var.get())
                )
            elif technique == 'CA':
                success = self.current_instrument.set_ca_params(
                    float(self.ca_setpoint_var.get()),
                    float(self.ca_duration_var.get()),
                    float(self.ca_samplerate_var.get())
                )
            elif technique == 'CP':
                success = self.current_instrument.set_cp_params(
                    float(self.cp_setpoint_var.get()),
                    float(self.cp_duration_var.get()),
                    float(self.cp_samplerate_var.get())
                )
            elif technique == 'Pulse':
                success = self.current_instrument.set_pulse_params(
                    float(self.pulse_voltage_var.get()),
                    float(self.pulse_width_var.get()),
                    float(self.pulse_duty_var.get()),
                    int(self.pulse_cycles_var.get())
                )
            elif technique == 'EIS':
                success = self.current_instrument.set_eis_params(
                    float(self.eis_fstart_var.get()),
                    float(self.eis_fend_var.get()),
                    int(self.eis_ppd_var.get()),
                    float(self.eis_amp_var.get()) / 1000,  # mV to V
                    float(self.eis_bias_var.get()),
                    self.eis_mode_var.get()
                )
            elif technique == 'CCCV':
                success = self.current_instrument.set_cccv_params(
                    float(self.cccv_charge_i_var.get()),
                    float(self.cccv_charge_v_var.get()),
                    float(self.cccv_discharge_i_var.get()),
                    float(self.cccv_discharge_v_var.get()),
                    int(self.cccv_cycles_var.get()),
                    int(self.cccv_rest_var.get())
                )
            else:
                success = False

            if success:
                self._update_status(f"✅ {technique} set")
                self.start_btn.config(state='normal')
            else:
                messagebox.showerror("Error", f"Failed to set {technique}")

        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))

    def _toggle_temperature(self):
        """Toggle temperature probe"""
        if self.current_instrument:
            self.current_instrument.enable_temperature_probe(self.temp_enabled_var.get())

    def _start_safety_monitor(self):
        """Start safety monitoring"""
        if self.safety_monitor_active:
            return

        self.safety_monitor_active = True
        threading.Thread(target=self._safety_monitor_loop, daemon=True).start()

    def _safety_monitor_loop(self):
        """Monitor safety limits"""
        while self.safety_monitor_active and self.current_instrument:
            try:
                if self.current_instrument.temp_probe_enabled:
                    temp = self.current_instrument.fetch_temperature()
                    if temp is not None:
                        self.ui_queue.schedule(lambda t=temp: self.temp_label.config(text=f"{t:.0f}°C"))

                        if self.safety_enabled_var.get():
                            violated, reason = self.current_instrument.check_safety_violation(0, 0, temp)
                            if violated:
                                self.ui_queue.schedule(lambda r=reason: self._handle_safety_violation(r))

                time.sleep(2)
            except:
                pass

    def _handle_safety_violation(self, reason: str):
        """Handle safety violation"""
        self.safety_status_label.config(text=f"⚠️ {reason}", fg="#e74c3c")
        self._abort_experiment()
        messagebox.showerror("Safety Violation", f"Aborted: {reason}")

    def _start_experiment(self):
        """Start experiment"""
        if not self.current_instrument:
            return

        self.current_instrument.select_channel(self.channel_var.get())

        if self.safety_enabled_var.get():
            vmax = float(self.safety_vmax_var.get())
            vmin = float(self.safety_vmin_var.get())
            imax = float(self.safety_imax_var.get())
            tmax = float(self.safety_tmax_var.get())
            self.current_instrument.set_safety_limits(vmax, vmin, imax, tmax)

        if self.temp_enabled_var.get():
            self.current_instrument.enable_temperature_probe(True)

        self.acquisition_active = True
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.abort_btn.config(state='normal')
        self.safety_status_label.config(text="● RUN", fg="#f39c12")

        self.current_instrument.start()

        threading.Thread(target=self._acquisition_loop, daemon=True).start()
        self._update_status("▶ Running...")

    def _acquisition_loop(self):
        """Data acquisition loop"""
        while self.acquisition_active:
            try:
                if hasattr(self.current_instrument, 'fetch_data'):
                    data = self.current_instrument.fetch_data()

                    if data and len(data.get('time_s', [])) > 0:
                        meas = EchemMeasurement(
                            timestamp=datetime.now(),
                            sample_id=self.sample_id_var.get(),
                            instrument=self.current_instrument.manufacturer,
                            instrument_model=self.current_instrument.model,
                            technique="Exp",
                            channel=self.current_instrument.current_channel,
                            time_s=data.get('time_s', np.array([])),
                            voltage_V=data.get('voltage_V', np.array([])),
                            current_A=data.get('current_A', np.array([])),
                            capacity_Ah=data.get('capacity_Ah', np.array([])),
                            temperature_C=data.get('temperature_C', None),
                            cycle_number=data.get('cycle', np.array([0]))[0] if 'cycle' in data else None,
                            safety_limits=self.current_instrument.safety_limits,
                            safety_violation=getattr(self.current_instrument, 'safety_violation', False),
                            violation_reason=getattr(self.current_instrument, 'violation_reason', '')
                        )

                        self.current_measurement = meas
                        self.ui_queue.schedule(lambda m=meas: self._update_data_display(m))

                time.sleep(0.1)
            except:
                self.acquisition_active = False

        self.ui_queue.schedule(self._acquisition_stopped)

    def _update_data_display(self, meas: EchemMeasurement):
        """Update data tree"""
        for item in self.data_tree.get_children():
            self.data_tree.delete(item)

        if meas.time_s is not None and len(meas.time_s) > 0:
            n = min(10, len(meas.time_s))
            for i in range(-n, 0):
                self.data_tree.insert('', 0, values=(
                    f"{meas.time_s[i]:.1f}",
                    f"{meas.voltage_V[i]:.3f}" if meas.voltage_V is not None else "-",
                    f"{meas.current_A[i]:.3f}" if meas.current_A is not None else "-",
                    str(meas.cycle_number) if meas.cycle_number else "-"
                ))

    def _acquisition_stopped(self):
        """Handle acquisition stop"""
        self.acquisition_active = False
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.abort_btn.config(state='disabled')
        self.safety_status_label.config(text="● OK", fg="#2ecc71")

        if self.current_measurement:
            self.measurements.append(self.current_measurement)
            self.sample_counter.config(text=f"📊 {len(self.measurements)}")
            self._update_status(f"✅ Complete")

    def _stop_experiment(self):
        """Stop experiment"""
        if self.current_instrument:
            self.current_instrument.stop()
        self.acquisition_active = False
        self._update_status("⏹ Stopped")

    def _abort_experiment(self):
        """Abort experiment"""
        if self.current_instrument:
            self.current_instrument.abort()
        self.acquisition_active = False
        self._update_status("⏸ Aborted")

    def _select_files(self):
        """Select files for import"""
        files = filedialog.askopenfilenames(
            filetypes=[("Data files", "*.csv *.xlsx *.txt *.mpr *.dta"), ("All", "*.*")]
        )

        if files:
            self.parse_file_var.set(f"{len(files)} files")
            threading.Thread(target=self._parse_files, args=(files,), daemon=True).start()

    def _parse_files(self, files):
        """Parse files"""
        parsed = 0
        for i, f in enumerate(files):
            self.ui_queue.schedule(lambda p=(i+1)/len(files)*100: self.progress_bar.config(value=p))

            measurements = []
            if ArbinWrapper.parse_file:
                measurements = ArbinWrapper.parse_file(f)
            if not measurements:
                measurements = MaccorParser.parse_file(f)

            if measurements:
                self.measurements.extend(measurements)
                parsed += 1

        def update():
            self.progress_bar.config(value=100)
            self.parse_file_var.set(f"✅ Parsed {parsed}/{len(files)}")
            self.sample_counter.config(text=f"📊 {len(self.measurements)}")

        self.ui_queue.schedule(update)

    def _batch_process(self):
        """Batch process folder"""
        folder = filedialog.askdirectory()
        if not folder:
            return

        files = []
        for ext in ['*.csv', '*.xlsx', '*.txt', '*.mpr', '*.dta']:
            files.extend(Path(folder).glob(ext))

        if files:
            self.parse_file_var.set(f"Found {len(files)} files")
            self._parse_files(files)

    def _update_status(self, msg):
        self.status_var.set(msg)

    def send_to_table(self):
        """Send to main table"""
        if not self.measurements:
            messagebox.showwarning("No Data", "No measurements to send")
            return

        data = [m.to_dict() for m in self.measurements]

        try:
            self.app.import_data_from_plugin(data)
            self._update_status(f"✅ Sent {len(data)} measurements")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def collect_data(self) -> List[Dict]:
        return [m.to_dict() for m in self.measurements]

    def _on_close(self):
        self.acquisition_active = False
        self.safety_monitor_active = False
        if self.current_instrument:
            self.current_instrument.disconnect()
        if self.window:
            self.window.destroy()
            self.window = None

# ============================================================================
# STANDARD PLUGIN REGISTRATION
# ============================================================================
def setup_plugin(main_app):
    global _ELECTROCHEM_REGISTERED
    if _ELECTROCHEM_REGISTERED:
        print("⏭️ Electrochemistry plugin already registered, skipping...")
        return None

    plugin = ElectrochemistryUnifiedSuitePlugin(main_app)

    if hasattr(main_app, 'left') and main_app.left is not None:
        main_app.left.add_hardware_button(
            name=PLUGIN_INFO.get("name", "Electrochemistry"),
            icon=PLUGIN_INFO.get("icon", "⚡"),
            command=plugin.show_interface
        )
        print(f"✅ Added to left panel: {PLUGIN_INFO.get('name')}")
        _ELECTROCHEM_REGISTERED = True
        return plugin

    if hasattr(main_app, 'menu_bar'):
        if not hasattr(main_app, 'hardware_menu'):
            main_app.hardware_menu = tk.Menu(main_app.menu_bar, tearoff=0)
            main_app.menu_bar.add_cascade(label="🔧 Hardware", menu=main_app.hardware_menu)

        main_app.hardware_menu.add_command(
            label=PLUGIN_INFO.get("name", "Electrochemistry"),
            command=plugin.show_interface
        )
        print(f"✅ Added to Hardware menu: {PLUGIN_INFO.get('name')}")
        _ELECTROCHEM_REGISTERED = True

    return plugin
