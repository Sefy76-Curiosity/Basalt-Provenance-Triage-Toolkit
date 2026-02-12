"""
MINERALOGY UNIFIED SUITE v2.2 - STABLE RRUFF MIRROR · 5,185 MINERALS · 1-CLICK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ TIER 1 ⭐ - Spectragryph mirror (5,185 spectra) - 1-CLICK DOWNLOAD
✓ TIER 2 🔗 - Custom URL download - PASTE ANY LINK
✓ TIER 3 🌐 - Official RRUFF browser link - WITH INSTRUCTIONS
✓ PROPER BUTTON STATE MANAGEMENT - ONLY ENABLED WHEN DATA IS READY
✓ ONE-CLICK SEND TO DYNAMIC TABLE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

PLUGIN_INFO = {
    "category": "hardware",
    "id": "mineralogy_unified_suite",
    "name": "Mineralogy Unified Suite",
    "icon": "💎",
    "description": "5,185 STABLE RRUFF minerals · 3-tier download · Smart button",
    "version": "2.2.0",
    "requires": ["numpy"],
    "author": "Mineralogy Unified Team",
    "compact": True,
}

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import platform
import json
import time
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from abc import ABC, abstractmethod
from enum import Enum
import zipfile
import urllib.parse
import tempfile
import csv
import webbrowser
import re
import os
warnings.filterwarnings('ignore')

# ============================================================================
# DEPENDENCIES
# ============================================================================
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None

try:
    from scipy.signal import find_peaks
    from scipy import sparse
    from scipy.sparse.linalg import spsolve
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

# ============================================================================
# ENUMS
# ============================================================================
class InstrumentType(Enum):
    XRD = "xrd"
    RAMAN = "raman"
    FTIR = "ftir"
    UNKNOWN = "unknown"


# ============================================================================
# EMBEDDED DATABASE - FALLBACK ONLY
# ============================================================================
FALLBACK_DATABASE = {
    "raman": {
        "Quartz": {"peaks": [464, 206, 128], "group": "Silicate", "formula": "SiO₂"},
        "Calcite": {"peaks": [1086, 711, 281], "group": "Carbonate", "formula": "CaCO₃"},
        "Hematite": {"peaks": [670, 410, 225], "group": "Oxide", "formula": "Fe₂O₃"},
        "Magnetite": {"peaks": [668, 538, 306], "group": "Oxide", "formula": "Fe₃O₄"},
        "Gypsum": {"peaks": [1008, 494, 414], "group": "Sulfate", "formula": "CaSO₄·2H₂O"},
        "Olivine": {"peaks": [855, 825, 544], "group": "Silicate", "formula": "(Mg,Fe)₂SiO₄"},
        "Zircon": {"peaks": [1008, 975, 438], "group": "Silicate", "formula": "ZrSiO₄"},
    },
    "xrd": {
        "Quartz": {"peaks": [20.86, 26.64, 36.54], "group": "Silicate", "formula": "SiO₂"},
        "Calcite": {"peaks": [23.05, 29.40, 31.42], "group": "Carbonate", "formula": "CaCO₃"},
        "Hematite": {"peaks": [24.14, 33.15, 35.61], "group": "Oxide", "formula": "Fe₂O₃"},
    }
}


# ============================================================================
# TIER 1: SPECTRAGRPH MIRROR - STABLE RRUFF SOURCE
# ============================================================================
class SpectragryphMirror:
    """TIER 1 ⭐ - Stable RRUFF mirror - ALWAYS WORKS"""

    MIRRORS = {
        "excellent": {
            "name": "🌟 5,185 Excellent Spectra (RECOMMENDED)",
            "url": "https://www.effemm2.de/spectragryph/databases/RRUFF_Raman_DB_5185excellent_entries_2017_01.zip",
            "size": "90 MB",
            "count": 5185,
        },
        "complete": {
            "name": "📊 3,087 Complete Spectra",
            "url": "https://www.effemm2.de/spectragryph/databases/RRUFF_Raman_DB_3087entries_02.zip",
            "size": "55 MB",
            "count": 3087,
        }
    }

    @classmethod
    def download(cls, key: str, progress_callback=None) -> Dict:
        """Download and process mirror"""
        if key not in cls.MIRRORS or not HAS_REQUESTS:
            return {"raman": {}, "total": 0}

        mirror = cls.MIRRORS[key]
        result = {"raman": {}, "total": 0}

        try:
            if progress_callback:
                progress_callback(f"📥 Downloading {mirror['name']}...")

            response = requests.get(mirror["url"], stream=True, timeout=30)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        tmp.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size > 0:
                            percent = int(50 * downloaded / total_size)
                            progress_callback(f"📥 Downloading: {'█' * percent}{'░' * (50-percent)}")
                tmp_path = tmp.name

            if progress_callback:
                progress_callback(f"🔍 Processing {mirror['name']}...")

            # Process ZIP
            minerals = {}
            with zipfile.ZipFile(tmp_path, 'r') as zf:
                txt_files = [f for f in zf.namelist() if f.endswith('.txt')]

                for i, filename in enumerate(txt_files):
                    if progress_callback and i % 100 == 0:
                        progress_callback(f"📚 Processing spectra: {i}/{len(txt_files)}")

                    try:
                        content = zf.read(filename).decode('utf-8', errors='ignore')

                        # Extract mineral name
                        name_parts = Path(filename).stem.split('__')
                        mineral_name = name_parts[0].replace('_', ' ').strip()
                        mineral_name = ' '.join(w.capitalize() for w in mineral_name.split())

                        # Extract peaks
                        x_vals, y_vals = [], []
                        for line in content.split('\n')[:500]:
                            parts = line.strip().split()
                            if len(parts) >= 2:
                                try:
                                    x_vals.append(float(parts[0]))
                                    y_vals.append(float(parts[1]))
                                except:
                                    continue

                        if len(x_vals) > 10 and HAS_SCIPY:
                            y_norm = (np.array(y_vals) - min(y_vals)) / (max(y_vals) - min(y_vals) + 1e-10)
                            peaks_idx, _ = find_peaks(y_norm, height=0.2, distance=15)
                            peaks = [x_vals[i] for i in peaks_idx[:10]]

                            if len(peaks) >= 2:
                                if mineral_name not in minerals:
                                    minerals[mineral_name] = {
                                        'peaks': peaks[:10],
                                        'group': cls._infer_group(peaks),
                                        'formula': '',
                                        'source': 'Spectragryph'
                                    }
                    except:
                        continue

            Path(tmp_path).unlink(missing_ok=True)

            result["raman"] = minerals
            result["total"] = len(minerals)

            if progress_callback:
                progress_callback(f"✅ Loaded {len(minerals)} minerals!")

        except Exception as e:
            if progress_callback:
                progress_callback(f"❌ Error: {str(e)[:50]}")

        return result

    @classmethod
    def _infer_group(cls, peaks):
        if not peaks:
            return "Unknown"
        avg = sum(peaks) / len(peaks)
        if avg < 300:
            return "Framework Silicate"
        elif 400 <= avg <= 500:
            return "Tectosilicate"
        elif 600 <= avg <= 700:
            return "Oxide"
        elif 1000 <= avg <= 1100:
            return "Carbonate"
        return "Silicate"


# ============================================================================
# TIER 2: CUSTOM URL HANDLER
# ============================================================================
class CustomURLHandler:
    """TIER 2 🔗 - Download from any URL"""

    @classmethod
    def download(cls, url: str, progress_callback=None) -> Dict:
        """Download and process from custom URL"""
        if not HAS_REQUESTS:
            return {"raman": {}, "total": 0}

        result = {"raman": {}, "total": 0}

        try:
            if progress_callback:
                progress_callback(f"🌐 Connecting to {url[:50]}...")

            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            filename = Path(urllib.parse.urlparse(url).path).name or "download.zip"

            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as tmp:
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0

                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        tmp.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size > 0:
                            percent = int(50 * downloaded / total_size)
                            progress_callback(f"📥 Downloading: {'█' * percent}{'░' * (50-percent)}")
                tmp_path = tmp.name

            if progress_callback:
                progress_callback(f"🔍 Processing {filename}...")

            # Try Spectragryph format first
            minerals = SpectragryphMirror._process_spectragryph_zip(tmp_path, progress_callback)

            if minerals:
                result["raman"] = minerals
                result["total"] = len(minerals)
            else:
                # Try generic format
                minerals = cls._process_generic_zip(tmp_path, progress_callback)
                result["raman"] = minerals
                result["total"] = len(minerals)

            Path(tmp_path).unlink(missing_ok=True)

        except Exception as e:
            if progress_callback:
                progress_callback(f"❌ Error: {str(e)[:50]}")

        return result

    @classmethod
    def _process_generic_zip(cls, zip_path, progress_callback=None):
        minerals = {}
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                txt_files = [f for f in zf.namelist() if f.endswith('.txt')]

                for i, filename in enumerate(txt_files[:500]):
                    try:
                        content = zf.read(filename).decode('utf-8', errors='ignore')
                        name = Path(filename).stem.split('__')[0].replace('_', ' ')
                        name = ' '.join(w.capitalize() for w in name.split())

                        x_vals, y_vals = [], []
                        for line in content.split('\n')[:500]:
                            parts = line.strip().split()
                            if len(parts) >= 2:
                                try:
                                    x_vals.append(float(parts[0]))
                                    y_vals.append(float(parts[1]))
                                except:
                                    continue

                        if len(x_vals) > 10 and HAS_SCIPY:
                            y_norm = (np.array(y_vals) - min(y_vals)) / (max(y_vals) - min(y_vals) + 1e-10)
                            peaks_idx, _ = find_peaks(y_norm, height=0.2, distance=15)
                            peaks = [x_vals[i] for i in peaks_idx[:10]]

                            if len(peaks) >= 2:
                                minerals[name] = {
                                    'peaks': peaks[:10],
                                    'group': 'Unknown',
                                    'formula': '',
                                    'source': 'Custom URL'
                                }
                    except:
                        continue
        except:
            pass
        return minerals


# ============================================================================
# TIER 3: OFFICIAL RRUFF HELPER
# ============================================================================
class OfficialRRUFFHelper:
    """TIER 3 🌐 - Official RRUFF website"""

    URL = "https://rruff.info/about/download-data/"

    @classmethod
    def open_browser(cls):
        webbrowser.open(cls.URL)

    @classmethod
    def get_instructions(cls):
        return "1. Click 'Raman' → 'excellent_unoriented.zip'\n2. Save the ZIP file\n3. Use TIER 2 → 'Browse Local File'"


# ============================================================================
# 3-TIER DOWNLOAD DIALOG - COMPLETE
# ============================================================================
class DownloadDialog:
    """COMPLETE 3-TIER DOWNLOAD DIALOG"""

    def __init__(self, parent, callback):
        self.parent = parent
        self.callback = callback
        self.dialog = None
        self.url_var = tk.StringVar()

    def show(self):
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("📥 Download RRUFF Database - 3-TIER")
        self.dialog.geometry("750x700")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        self.dialog.configure(bg='#f5f5f5')

        main = tk.Frame(self.dialog, bg='#f5f5f5', padx=20, pady=20)
        main.pack(fill=tk.BOTH, expand=True)

        # ============ TIER 1 - STABLE MIRROR ============
        tier1 = tk.Frame(main, bg='#e8f5e9', relief=tk.RIDGE, bd=2)
        tier1.pack(fill=tk.X, pady=(0, 15))

        tk.Label(tier1, text="⭐ TIER 1 - STABLE MIRROR (ALWAYS WORKS)",
                font=("Arial", 11, "bold"), bg='#e8f5e9', fg='#2e7d32').pack(anchor=tk.W, padx=15, pady=10)

        # Excellent mirror
        btn1 = tk.Button(tier1,
                       text="🌟 5,185 Excellent Spectra (90 MB) - RECOMMENDED",
                       bg='#2e7d32', fg='white', font=("Arial", 10, "bold"),
                       padx=10, pady=8, bd=0, cursor='hand2',
                       command=lambda: self._download_mirror('excellent'))
        btn1.pack(fill=tk.X, padx=15, pady=5)

        # Complete mirror
        btn2 = tk.Button(tier1,
                       text="📊 3,087 Complete Spectra (55 MB)",
                       bg='#81c784', fg='white', font=("Arial", 10),
                       padx=10, pady=6, bd=0, cursor='hand2',
                       command=lambda: self._download_mirror('complete'))
        btn2.pack(fill=tk.X, padx=15, pady=5)

        # ============ TIER 2 - CUSTOM URL ============
        tier2 = tk.Frame(main, bg='#fff3e0', relief=tk.RIDGE, bd=2)
        tier2.pack(fill=tk.X, pady=(0, 15))

        tk.Label(tier2, text="🔗 TIER 2 - CUSTOM URL / LOCAL FILE",
                font=("Arial", 11, "bold"), bg='#fff3e0', fg='#e65100').pack(anchor=tk.W, padx=15, pady=10)

        # URL Entry
        url_frame = tk.Frame(tier2, bg='#fff3e0')
        url_frame.pack(fill=tk.X, padx=15, pady=5)

        tk.Entry(url_frame, textvariable=self.url_var, font=("Arial", 9), width=50).pack(side=tk.LEFT, padx=(0, 10))
        tk.Button(url_frame, text="Download URL", bg='#e65100', fg='white',
                 command=self._download_url).pack(side=tk.LEFT)

        # Browse button
        btn_frame = tk.Frame(tier2, bg='#fff3e0')
        btn_frame.pack(fill=tk.X, padx=15, pady=5)

        tk.Button(btn_frame, text="📁 Browse Local File", bg='#ffb74d', fg='black',
                 command=self._browse_file).pack(side=tk.LEFT, padx=(0, 10))
        tk.Button(btn_frame, text="📋 Paste URL", bg='#ffe0b2', fg='black',
                 command=self._paste_url).pack(side=tk.LEFT)

        # ============ TIER 3 - OFFICIAL RRUFF ============
        tier3 = tk.Frame(main, bg='#e3f2fd', relief=tk.RIDGE, bd=2)
        tier3.pack(fill=tk.X, pady=(0, 15))

        tk.Label(tier3, text="🌐 TIER 3 - OFFICIAL RRUFF WEBSITE",
                font=("Arial", 11, "bold"), bg='#e3f2fd', fg='#0d47a1').pack(anchor=tk.W, padx=15, pady=10)

        tk.Button(tier3, text="Open RRUFF Download Page", bg='#0d47a1', fg='white',
                 font=("Arial", 10), padx=20, pady=8,
                 command=OfficialRRUFFHelper.open_browser).pack(padx=15, pady=5)

        # Instructions
        instr = tk.Text(tier3, height=4, width=60, bg='#e3f2fd', fg='#0d47a1',
                       font=("Arial", 9), bd=0, wrap=tk.WORD)
        instr.pack(padx=15, pady=10, fill=tk.X)
        instr.insert(1.0, OfficialRRUFFHelper.get_instructions())
        instr.config(state=tk.DISABLED)

        # Close button
        tk.Button(main, text="Close", bg='#95a5a6', fg='white',
                 font=("Arial", 10), padx=30, pady=5,
                 command=self.dialog.destroy).pack(pady=20)

    def _download_mirror(self, key):
        self.dialog.destroy()
        if self.callback:
            self.callback('mirror', key)

    def _download_url(self):
        url = self.url_var.get().strip()
        if url:
            self.dialog.destroy()
            if self.callback:
                self.callback('url', url)

    def _browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select RRUFF Database File",
            filetypes=[("ZIP files", "*.zip"), ("All files", "*.*")]
        )
        if filename:
            self.dialog.destroy()
            if self.callback:
                self.callback('file', filename)

    def _paste_url(self):
        try:
            url = self.dialog.clipboard_get()
            if url.startswith('http'):
                self.url_var.set(url)
                self.status_var.set("✅ URL pasted")
        except:
            pass


# ============================================================================
# PREPROCESSING
# ============================================================================
class Preprocessor:
    @staticmethod
    def find_peaks(x, y, instrument_type):
        if not HAS_SCIPY or x is None or y is None or len(y) == 0:
            return np.array([])

        try:
            y_norm = (y - y.min()) / (y.max() - y.min() + 1e-10)
            height = 0.1 if instrument_type == InstrumentType.XRD else 0.15
            distance = 30 if instrument_type == InstrumentType.XRD else 15
            peaks, _ = find_peaks(y_norm, height=height, distance=distance)
            return x[peaks]
        except:
            return np.array([])


# ============================================================================
# MAIN PLUGIN - WITH COMPLETE 3-TIER DOWNLOAD
# ============================================================================
class MineralogyUnifiedSuitePlugin:
    def __init__(self, main_app):
        self.app = main_app
        self.window = None

        # Data state
        self.x_data = None
        self.y_data = None
        self.peaks = np.array([])
        self.identifications = []
        self.filename = ""
        self.instrument_type = InstrumentType.UNKNOWN

        # Database
        self.database = {
            "raman": FALLBACK_DATABASE.get("raman", {}).copy(),
            "xrd": FALLBACK_DATABASE.get("xrd", {}).copy(),
            "ftir": {},
            "xrf": {}
        }

        # UI Elements
        self.send_btn = None
        self.status_var = tk.StringVar(value="Ready")
        self.ax = None
        self.canvas = None
        self.tree = None
        self.peak_label = None
        self.file_label = None
        self.db_label = None
        self.progress_bar = None
        self.progress_label = None

    # ========================================================================
    # BUTTON STATE MANAGEMENT
    # ========================================================================
    def _update_button_state(self):
        """Enable Send button ONLY when ALL data is ready"""
        if self.send_btn:
            has_spectrum = self.x_data is not None and self.y_data is not None
            has_peaks = len(self.peaks) > 0
            has_minerals = len(self.identifications) > 0

            if has_spectrum and has_peaks and has_minerals:
                self.send_btn.config(state='normal')
                self.status_var.set("✅ Ready to send to table")
            else:
                self.send_btn.config(state='disabled')
                if not has_spectrum:
                    self.status_var.set("📂 Load a spectrum file")
                elif not has_peaks:
                    self.status_var.set("🔍 Click 'Find Peaks'")
                elif not has_minerals:
                    self.status_var.set("Click 'Identify'")

    # ========================================================================
    # 3-TIER DOWNLOAD HANDLER
    # ========================================================================
    def _show_download_dialog(self):
        """Show the complete 3-tier download dialog"""
        def callback(download_type, value):
            if download_type == 'mirror':
                self._download_mirror(value)
            elif download_type == 'url':
                self._download_custom_url(value)
            elif download_type == 'file':
                self._process_local_file(value)

        dialog = DownloadDialog(self.window, callback)
        dialog.show()

    def _download_mirror(self, key):
        """TIER 1 - Download from Spectragryph mirror"""
        def download_thread():
            self._show_progress(True)
            self._update_progress(0, f"📥 Downloading Spectragryph mirror...")

            def progress(msg):
                self._update_progress(self.progress_bar['value'] + 1, msg)
                self.status_var.set(msg)
                if self.window:
                    self.window.update_idletasks()

            result = SpectragryphMirror.download(key, progress)

            if result and result.get("total", 0) > 0:
                count = 0
                for name, data in result.get("raman", {}).items():
                    if name not in self.database["raman"]:
                        self.database["raman"][name] = data
                        count += 1

                self._update_db_stats()
                self._show_progress(False)

                if count > 0:
                    self.status_var.set(f"✅ Added {count} minerals!")
                    messagebox.showinfo("Success", f"Added {count} new minerals!\n\nDatabase now has {self._get_db_count()} minerals")
            else:
                self._show_progress(False)
                messagebox.showerror("Error", "Download failed")

        threading.Thread(target=download_thread, daemon=True).start()

    def _download_custom_url(self, url):
        """TIER 2 - Download from custom URL"""
        def download_thread():
            self._show_progress(True)
            self._update_progress(0, f"📥 Downloading from URL...")

            def progress(msg):
                self._update_progress(self.progress_bar['value'] + 1, msg)
                self.status_var.set(msg)
                if self.window:
                    self.window.update_idletasks()

            result = CustomURLHandler.download(url, progress)

            if result and result.get("total", 0) > 0:
                count = 0
                for name, data in result.get("raman", {}).items():
                    if name not in self.database["raman"]:
                        self.database["raman"][name] = data
                        count += 1

                self._update_db_stats()
                self._show_progress(False)

                if count > 0:
                    self.status_var.set(f"✅ Added {count} minerals from URL")
                    messagebox.showinfo("Success", f"Added {count} new minerals from URL!")
            else:
                self._show_progress(False)
                messagebox.showerror("Error", "No valid minerals found in URL")

        threading.Thread(target=download_thread, daemon=True).start()

    def _process_local_file(self, filepath):
        """TIER 2 - Process local ZIP file"""
        def process_thread():
            self._show_progress(True)
            self._update_progress(10, f"📂 Processing {Path(filepath).name}...")

            def progress(msg):
                self.status_var.set(msg)
                if self.window:
                    self.window.update_idletasks()

            # Try Spectragryph format
            minerals = SpectragryphMirror._process_spectragryph_zip(filepath, progress)

            if not minerals:
                # Try generic format
                minerals = CustomURLHandler._process_generic_zip(filepath, progress)

            if minerals:
                count = 0
                for name, data in minerals.items():
                    if name not in self.database["raman"]:
                        self.database["raman"][name] = data
                        count += 1

                self._update_db_stats()
                self._show_progress(False)

                if count > 0:
                    self.status_var.set(f"✅ Added {count} minerals from file")
                    messagebox.showinfo("Success", f"Added {count} minerals from file!")
            else:
                self._show_progress(False)
                messagebox.showerror("Error", "No valid minerals found in file")

        threading.Thread(target=process_thread, daemon=True).start()

    # ========================================================================
    # SEND TO TABLE - ONE BUTTON
    # ========================================================================
    def send_to_table(self):
        """ONE BUTTON - Sends ALL data to dynamic table"""
        if self.x_data is None or self.y_data is None or len(self.peaks) == 0 or len(self.identifications) == 0:
            return

        try:
            table_data = []
            sample_id = f"MIN-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

            # 1. METADATA
            table_data.append({
                "Sample_ID": sample_id,
                "Type": "Analysis",
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Instrument": self.instrument_type.value if self.instrument_type else "unknown",
                "Filename": self.filename or "Live",
                "Technique": self.instrument_type.name if self.instrument_type else "UNKNOWN",
                "Peaks_Found": len(self.peaks),
                "Minerals_Identified": len(self.identifications),
                "Database_Size": self._get_db_count()
            })

            # 2. PEAKS
            for i, peak in enumerate(self.peaks[:15]):
                idx = np.abs(self.x_data - peak).argmin()
                intensity = self.y_data[idx]
                table_data.append({
                    "Sample_ID": sample_id,
                    "Type": "Peak",
                    "Peak_Number": i + 1,
                    "Position": round(peak, 2),
                    "Intensity": round(intensity, 2),
                    "Relative_Intensity": f"{round((intensity / self.y_data.max() * 100), 1)}%"
                })

            # 3. MINERALS
            for i, m in enumerate(self.identifications[:20]):
                table_data.append({
                    "Sample_ID": sample_id,
                    "Type": "Mineral",
                    "Rank": i + 1,
                    "Name": m.get('name', 'Unknown'),
                    "Confidence": f"{m.get('confidence', 0)}%",
                    "Group": m.get('group', ''),
                    "Formula": m.get('formula', ''),
                    "Matches": f"{m.get('matches', 0)}/{len(m.get('peaks', []))}"
                })

            # Send to main app
            if hasattr(self.app, 'import_data_from_plugin'):
                self.app.import_data_from_plugin(table_data)
                self.status_var.set(f"✅ Sent {len(table_data)} rows")
                messagebox.showinfo("Success", f"Sent {len(table_data)} rows to table")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to send: {str(e)}")

    # ========================================================================
    # FILE OPERATIONS
    # ========================================================================
    def _load_file(self):
        path = filedialog.askopenfilename(
            title="Load Spectrum File",
            filetypes=[("Spectrum files", "*.csv *.txt *.spc"), ("All files", "*.*")]
        )
        if not path:
            return

        x, y = [], []
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if not line or line[0] in '#@%':
                        continue
                    for sep in [',', '\t', ' ']:
                        parts = line.split(sep)
                        if len(parts) >= 2:
                            try:
                                x.append(float(parts[0]))
                                y.append(float(parts[1]))
                                break
                            except:
                                continue
        except Exception as e:
            messagebox.showerror("Error", f"Could not parse file: {str(e)}")
            return

        if len(x) == 0:
            messagebox.showerror("Error", "No numeric data found")
            return

        self.x_data = np.array(x)
        self.y_data = np.array(y)
        self.filename = Path(path).name
        self.file_label.config(text=self.filename[:25])
        self.peaks = np.array([])
        self.identifications = []
        self._plot()
        self._clear_tree()
        self.status_var.set(f"Loaded: {self.filename}")
        self._update_button_state()

    def _find_peaks(self):
        if self.x_data is None:
            messagebox.showwarning("No Data", "Load a spectrum file first")
            return

        self.peaks = Preprocessor.find_peaks(self.x_data, self.y_data, self.instrument_type)
        self._plot()
        self.peak_label.config(text=f"⚡ {len(self.peaks)} peaks detected" if len(self.peaks) > 0 else "⚡ No peaks found")
        self._update_button_state()

    def _identify(self):
        if len(self.peaks) == 0:
            messagebox.showwarning("No Peaks", "Find peaks first")
            return

        # Auto-detect technique
        if self.x_data is not None and len(self.x_data) > 0:
            x_mean = self.x_data.mean()
            if 5 <= x_mean <= 80:
                self.instrument_type = InstrumentType.XRD
            elif 100 <= x_mean <= 2000:
                self.instrument_type = InstrumentType.RAMAN

        technique = 'raman' if self.instrument_type == InstrumentType.RAMAN else 'xrd'
        library = self.database.get(technique, {})

        if not library:
            messagebox.showinfo("No Database", "Click 'RRUFF' to download minerals!")
            return

        results = []
        peaks_list = self.peaks.tolist()
        tolerance = 5.0 if technique == 'raman' else 0.2

        for name, data in library.items():
            ref_peaks = data.get('peaks', [])
            if not ref_peaks:
                continue

            matches = 0
            for rp in ref_peaks[:5]:
                for dp in peaks_list:
                    if abs(dp - rp) <= tolerance:
                        matches += 1
                        break

            confidence = (matches / min(len(ref_peaks), 5)) * 100
            if confidence >= 25:
                results.append({
                    'name': name,
                    'confidence': round(confidence, 1),
                    'group': data.get('group', 'Unknown'),
                    'formula': data.get('formula', ''),
                    'matches': matches,
                    'peaks': ref_peaks[:5]
                })

        results.sort(key=lambda x: x['confidence'], reverse=True)
        self.identifications = results
        self._update_tree()
        self._update_button_state()
        self.status_var.set(f"✅ Identified {len(results)} minerals" if results else "❌ No minerals identified")

    def _clear_all(self):
        self.peaks = np.array([])
        self.identifications = []
        self.peak_label.config(text="⚡ No peaks")
        self._clear_tree()
        self._plot()
        self._update_button_state()
        self.status_var.set("Cleared")

    # ========================================================================
    # UTILITIES
    # ========================================================================
    def _get_db_count(self):
        count = 0
        for tech in self.database:
            count += len(self.database[tech])
        return count

    def _update_db_stats(self):
        if self.db_label:
            count = self._get_db_count()
            self.db_label.config(text=f"📚 Database: {count} minerals")

    def _show_progress(self, show=True):
        if self.progress_bar:
            if show:
                self.progress_bar.pack(fill=tk.X, pady=2)
                self.progress_bar['value'] = 0
            else:
                self.progress_bar.pack_forget()

    def _update_progress(self, value, text=None):
        if self.progress_bar:
            self.progress_bar['value'] = value % 100
        if text and self.progress_label:
            self.progress_label.config(text=text)
        if self.window:
            self.window.update_idletasks()

    # ========================================================================
    # UI
    # ========================================================================
    def open_window(self):
        if not HAS_NUMPY:
            messagebox.showerror("Error", "NumPy is required")
            return

        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("Mineralogy Unified Suite - 3-Tier RRUFF Download")
        self.window.geometry("1000x650")
        self.window.minsize(950, 600)

        self._build_ui()
        self.window.lift()
        self.window.focus_force()

    def _build_ui(self):
        # Header
        header = tk.Frame(self.window, bg="#2c3e50", height=40)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="💎", font=("Arial", 16), bg="#2c3e50", fg="white").pack(side=tk.LEFT, padx=8)
        tk.Label(header, text="Mineralogy Unified Suite", font=("Arial", 12, "bold"), bg="#2c3e50", fg="white").pack(side=tk.LEFT, padx=2)
        tk.Label(header, text="v2.2", font=("Arial", 8), bg="#2c3e50", fg="#f1c40f").pack(side=tk.LEFT, padx=8)

        self.status_indicator = tk.Label(header, textvariable=self.status_var,
                                        font=("Arial", 8), bg="#2c3e50", fg="#2ecc71")
        self.status_indicator.pack(side=tk.RIGHT, padx=10)

        # Progress bar
        progress_frame = tk.Frame(self.window, bg="white", height=25)
        progress_frame.pack(fill=tk.X, padx=5, pady=2)
        progress_frame.pack_propagate(False)

        self.progress_label = tk.Label(progress_frame, text="Ready", font=("Arial", 7), bg="white", anchor=tk.W)
        self.progress_label.pack(fill=tk.X)

        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', length=1000)
        self.progress_bar.pack(fill=tk.X, pady=2)
        self.progress_bar.pack_forget()

        # Main content
        main = tk.PanedWindow(self.window, orient=tk.HORIZONTAL, sashwidth=4)
        main.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # LEFT PANEL
        left = tk.Frame(main, bg="white")
        main.add(left, width=600)

        # Toolbar
        toolbar = tk.Frame(left, bg="#ecf0f1", height=35)
        toolbar.pack(fill=tk.X)
        toolbar.pack_propagate(False)

        ttk.Button(toolbar, text="📂 Load File", width=12, command=self._load_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🔍 Find Peaks", width=12, command=self._find_peaks).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Identify", width=12, command=self._identify).pack(side=tk.LEFT, padx=2)

        self.send_btn = ttk.Button(toolbar, text="📊 Send to Table", width=15,
                                  command=self.send_to_table, state='disabled')
        self.send_btn.pack(side=tk.LEFT, padx=2)

        self.file_label = tk.Label(toolbar, text="No file loaded", font=("Arial", 8),
                                  bg="#ecf0f1", fg="#7f8c8d")
        self.file_label.pack(side=tk.RIGHT, padx=10)

        # Plot
        if HAS_MPL:
            plot_frame = tk.Frame(left, bg="white")
            plot_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

            self.fig = plt.Figure(figsize=(6, 3.5), dpi=85, facecolor='white')
            self.ax = self.fig.add_subplot(111)
            self.ax.set_xlabel("X Axis")
            self.ax.set_ylabel("Intensity")
            self.ax.set_title("Load a spectrum to begin", fontsize=9)
            self.ax.grid(True, alpha=0.2)
            self.fig.tight_layout(pad=1.8)

            self.canvas = FigureCanvasTkAgg(self.fig, plot_frame)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Peak info
        peak_bar = tk.Frame(left, bg="#bdc3c7", height=24)
        peak_bar.pack(fill=tk.X)
        peak_bar.pack_propagate(False)

        self.peak_label = tk.Label(peak_bar, text="⚡ No peaks detected", font=("Arial", 7),
                                  bg="#bdc3c7", anchor=tk.W)
        self.peak_label.pack(fill=tk.X, padx=8)

        # RIGHT PANEL
        right = tk.Frame(main, bg="white")
        main.add(right, width=350)

        # Database controls - 3-TIER DOWNLOAD BUTTON
        db_frame = tk.Frame(right, bg="#ecf0f1", height=35)
        db_frame.pack(fill=tk.X)
        db_frame.pack_propagate(False)

        tk.Label(db_frame, text="RRUFF:", font=("Arial", 8, "bold"), bg="#ecf0f1").pack(side=tk.LEFT, padx=5)

        # 3-TIER DOWNLOAD BUTTON
        download_btn = tk.Button(db_frame,
                                text="⭐ 3-TIER DOWNLOAD",
                                bg="#2e7d32", fg="white",
                                font=("Arial", 9, "bold"),
                                padx=10, pady=4, bd=0,
                                cursor="hand2",
                                command=self._show_download_dialog)
        download_btn.pack(side=tk.LEFT, padx=5, pady=2, fill=tk.X, expand=True)

        ttk.Button(db_frame, text="Clear", width=6, command=self._clear_all).pack(side=tk.RIGHT, padx=5)

        # Database stats
        stats_frame = tk.Frame(right, bg="white")
        stats_frame.pack(fill=tk.X, pady=2)

        self.db_label = tk.Label(stats_frame, text=f"📚 Database: {self._get_db_count()} minerals",
                                font=("Arial", 8), bg="white", anchor=tk.W)
        self.db_label.pack(fill=tk.X, padx=5, pady=2)

        # Confidence filter
        conf_frame = tk.Frame(right, bg="white")
        conf_frame.pack(fill=tk.X, pady=2)

        tk.Label(conf_frame, text="Confidence ≥", font=("Arial", 8), bg="white").pack(side=tk.LEFT, padx=2)
        self.conf_var = tk.IntVar(value=50)
        conf_combo = ttk.Combobox(conf_frame, textvariable=self.conf_var,
                                 values=[25, 50, 75, 90], width=3, state='readonly')
        conf_combo.pack(side=tk.LEFT, padx=2)
        conf_combo.bind('<<ComboboxSelected>>', lambda e: self._update_tree())
        tk.Label(conf_frame, text="%", font=("Arial", 8), bg="white").pack(side=tk.LEFT)

        # Results tree
        tree_frame = tk.Frame(right, bg="white")
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        columns = ('Mineral', 'Conf', 'Group', 'Formula')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=20)
        self.tree.heading('Mineral', text='Mineral')
        self.tree.heading('Conf', text='%')
        self.tree.heading('Group', text='Group')
        self.tree.heading('Formula', text='Formula')
        self.tree.column('Mineral', width=120)
        self.tree.column('Conf', width=45, anchor='center')
        self.tree.column('Group', width=80)
        self.tree.column('Formula', width=100)

        scroll = ttk.Scrollbar(tree_frame, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.tag_configure('high', background='#d4edda')
        self.tree.tag_configure('med', background='#fff3cd')
        self.tree.tag_configure('low', background='#f8d7da')

        # Status bar
        status_bar = tk.Frame(self.window, bg="#34495e", height=24)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        status_bar.pack_propagate(False)

        tk.Label(status_bar,
                text="Mineralogy Unified v2.2 · 3-Tier Download · Spectragryph · Custom URL · Official RRUFF",
                font=("Arial", 7), bg="#34495e", fg="white").pack(side=tk.LEFT, padx=8)

        self._update_button_state()

    def _plot(self):
        if self.x_data is None or not HAS_MPL or self.ax is None:
            return

        self.ax.clear()
        self.ax.plot(self.x_data, self.y_data, 'b-', linewidth=1.2, alpha=0.7)

        if len(self.peaks) > 0:
            y_vals = [self.y_data[np.abs(self.x_data - p).argmin()] for p in self.peaks]
            self.ax.scatter(self.peaks, y_vals, c='red', s=30, zorder=5)
            self.ax.set_title(f"{len(self.peaks)} peaks detected", fontsize=9)
        else:
            self.ax.set_title(self.filename[:30] or "Spectrum", fontsize=9)

        self.ax.grid(True, alpha=0.2)
        self.fig.tight_layout()
        self.canvas.draw()

    def _update_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        threshold = self.conf_var.get()
        for m in self.identifications[:20]:
            if m['confidence'] >= threshold:
                tag = 'high' if m['confidence'] >= 70 else 'med' if m['confidence'] >= 50 else 'low'
                formula = m['formula'][:15] + '...' if len(m['formula']) > 15 else m['formula']
                self.tree.insert('', tk.END, values=(
                    m['name'],
                    f"{m['confidence']:.0f}",
                    m['group'],
                    formula
                ), tags=(tag,))

    def _clear_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)


# ============================================================================
# PLUGIN REGISTRATION
# ============================================================================
def setup_plugin(main_app):
    try:
        plugin = MineralogyUnifiedSuitePlugin(main_app)

        if hasattr(main_app, 'menu_bar'):
            if not hasattr(main_app, 'hardware_menu'):
                main_app.hardware_menu = tk.Menu(main_app.menu_bar, tearoff=0)
                main_app.menu_bar.add_cascade(label="🔧 Hardware", menu=main_app.hardware_menu)

            main_app.hardware_menu.add_command(
                label="Mineralogy Unified Suite",
                command=plugin.open_window
            )

        return plugin
    except Exception as e:
        print(f"Warning: Could not load plugin: {e}")
        return None
