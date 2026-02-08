"""
Agilent FTIR Hardware Plugin
Supports: 4300 Handheld FTIR, 5500 Compact FTIR

Uses: pythonnet to interface with .NET-based MicroLab SDK
Best for: Mineral phase identification, weathered basalt vs palagonite

Author: Sefy Levy
License: CC BY-NC-SA 4.0
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time

# FTIR SDK interface (requires pythonnet)
HAS_PYTHONNET = False
try:
    import clr
    HAS_PYTHONNET = True
except ImportError:
    pass

PLUGIN_INFO = {
      'category': 'hardware',
    'id': 'agilent_ftir',
    'name': 'Agilent FTIR (4300/5500)',
    'version': '1.0',
    'author': 'Sefy Levy',
    'description': 'Agilent Handheld & Portable FTIR analyzer integration',
    'category': 'Hardware',
    'icon': '📊',
    'requires': ['pythonnet'],
    'supported_models': [
        'Agilent 4300 Handheld FTIR',
        'Agilent 5500 Compact FTIR'
    ]
}


class AgilentFTIRPlugin:
    """Agilent FTIR analyzer hardware plugin"""
    
    def __init__(self, parent_app):
        self.app = parent_app
        self.window = None
        self.connected = False
        self.device = None
        self.monitor_thread = None
        self.stop_monitoring = False
        
        # Spectrum data
        self.current_spectrum = None
        self.mineral_phases = []
        
    def show(self):
        """Show the Agilent FTIR interface"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return
            
        self.window = tk.Toplevel(self.app.root)
        self.window.title("📊 Agilent FTIR - 4300/5500 Series")
        self.window.geometry("700x600")
        
        # Header
        header = ttk.Frame(self.window)
        header.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(header, text="📊 Agilent FTIR Analyzer", 
                 font=("Arial", 14, "bold")).pack(side="left")
        
        # Models info
        info_frame = ttk.LabelFrame(self.window, text="Supported Models", padding=10)
        info_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(info_frame, text="✓ Agilent 4300 Handheld FTIR").pack(anchor="w")
        ttk.Label(info_frame, text="✓ Agilent 5500 Compact FTIR").pack(anchor="w")
        ttk.Label(info_frame, text="Interface: MicroLab SDK (.NET)").pack(anchor="w")
        
        # Connection frame
        conn_frame = ttk.LabelFrame(self.window, text="Connection", padding=10)
        conn_frame.pack(fill="x", padx=10, pady=5)
        
        self.status_label = ttk.Label(conn_frame, text="● Not Connected", 
                                      foreground="red")
        self.status_label.pack(side="left", padx=5)
        
        self.connect_btn = ttk.Button(conn_frame, text="🔌 Connect", 
                                      command=self.connect_device)
        self.connect_btn.pack(side="left", padx=5)
        
        ttk.Button(conn_frame, text="🔍 Test", 
                  command=self.test_connection).pack(side="left", padx=5)
        
        # Spectrum display
        spectrum_frame = ttk.LabelFrame(self.window, text="Spectral Data", padding=10)
        spectrum_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Wavenumber range
        range_frame = ttk.Frame(spectrum_frame)
        range_frame.pack(fill="x", pady=5)
        ttk.Label(range_frame, text="Range: 4000-400 cm⁻¹ (Mid-IR)").pack(side="left")
        
        # Spectrum text view
        self.spectrum_text = tk.Text(spectrum_frame, height=10, width=60, 
                                     font=("Courier", 9))
        self.spectrum_text.pack(fill="both", expand=True, pady=5)
        
        # Mineral identification
        mineral_frame = ttk.LabelFrame(self.window, text="Identified Mineral Phases", 
                                       padding=10)
        mineral_frame.pack(fill="x", padx=10, pady=5)
        
        self.mineral_listbox = tk.Listbox(mineral_frame, height=4, 
                                          font=("Arial", 10))
        self.mineral_listbox.pack(fill="both", expand=True)
        
        # Action buttons
        btn_frame = ttk.Frame(self.window)
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(btn_frame, text="📥 Scan Now", 
                  command=self.acquire_spectrum).pack(side="left", padx=5)
        
        ttk.Button(btn_frame, text="➕ Add to Sample", 
                  command=self.add_to_sample).pack(side="left", padx=5)
        
        ttk.Button(btn_frame, text="🗑️ Clear", 
                  command=self.clear_data).pack(side="left", padx=5)
        
        # Dependency check
        if not HAS_PYTHONNET:
            self.show_dependency_warning()
    
    def show_dependency_warning(self):
        """Show warning about missing dependencies"""
        warning = tk.Label(self.window, 
                          text="⚠️ pythonnet not installed. Install with: pip install pythonnet",
                          bg="#FFF3CD", fg="#856404", padx=10, pady=5)
        warning.pack(fill="x", padx=10, pady=5)
        self.connect_btn.config(state="disabled")
    
    def connect_device(self):
        """Connect to Agilent FTIR device"""
        if not HAS_PYTHONNET:
            messagebox.showerror("Error", 
                "pythonnet library not installed!\n\n"
                "Install with: pip install pythonnet")
            return
        
        try:
            # Load Agilent MicroLab SDK
            clr.AddReference("Agilent.MicroLab")
            from Agilent.MicroLab import Instrument, SpectrumAcquisition
            
            # Initialize connection
            self.device = Instrument.Connect()
            
            if self.device:
                self.connected = True
                self.status_label.config(text="● Connected", foreground="green")
                self.connect_btn.config(text="🔌 Disconnect", 
                                       command=self.disconnect_device)
                messagebox.showinfo("Success", 
                    "Connected to Agilent FTIR!\n\n"
                    "Ready to acquire spectra.")
            else:
                raise Exception("Failed to connect to device")
                
        except Exception as e:
            messagebox.showerror("Connection Error", 
                f"Could not connect to Agilent FTIR:\n{str(e)}\n\n"
                "Make sure:\n"
                "• Device is powered on\n"
                "• MicroLab SDK is installed\n"
                "• Device drivers are installed")
    
    def disconnect_device(self):
        """Disconnect from device"""
        self.stop_monitoring = True
        if self.device:
            try:
                self.device.Disconnect()
            except:
                pass
        self.device = None
        self.connected = False
        self.status_label.config(text="● Not Connected", foreground="red")
        self.connect_btn.config(text="🔌 Connect", command=self.connect_device)
    
    def test_connection(self):
        """Test device connection"""
        if not self.connected:
            messagebox.showwarning("Not Connected", 
                "Please connect to device first!")
            return
        
        try:
            # Query device info
            model = self.device.GetModelName()
            serial = self.device.GetSerialNumber()
            
            messagebox.showinfo("Connection Test", 
                f"✅ Connection Successful!\n\n"
                f"Model: {model}\n"
                f"Serial: {serial}\n"
                f"Status: Ready")
        except Exception as e:
            messagebox.showerror("Test Failed", 
                f"Connection test failed:\n{str(e)}")
    
    def acquire_spectrum(self):
        """Acquire FTIR spectrum"""
        if not self.connected:
            messagebox.showwarning("Not Connected", 
                "Please connect to device first!")
            return
        
        try:
            from Agilent.MicroLab import SpectrumAcquisition
            
            # Acquire spectrum
            acq = SpectrumAcquisition(self.device)
            spectrum = acq.AcquireSpectrum()
            
            # Parse spectral data
            wavenumbers = spectrum.GetWavenumbers()
            intensities = spectrum.GetIntensities()
            
            # Store spectrum
            self.current_spectrum = {
                'wavenumbers': list(wavenumbers),
                'intensities': list(intensities),
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Display spectrum info
            self.spectrum_text.delete("1.0", "end")
            self.spectrum_text.insert("end", 
                f"Spectrum acquired: {self.current_spectrum['timestamp']}\n"
                f"Data points: {len(wavenumbers)}\n"
                f"Range: {min(wavenumbers):.1f} - {max(wavenumbers):.1f} cm⁻¹\n\n"
                f"Peak wavenumbers (top 5):\n")
            
            # Find top 5 peaks
            peak_indices = sorted(range(len(intensities)), 
                                 key=lambda i: intensities[i], reverse=True)[:5]
            for idx in peak_indices:
                self.spectrum_text.insert("end", 
                    f"  {wavenumbers[idx]:.1f} cm⁻¹ (I={intensities[idx]:.2f})\n")
            
            # Identify mineral phases
            self.identify_minerals(wavenumbers, intensities)
            
            messagebox.showinfo("Success", "Spectrum acquired successfully!")
            
        except Exception as e:
            messagebox.showerror("Acquisition Error", 
                f"Failed to acquire spectrum:\n{str(e)}")
    
    def identify_minerals(self, wavenumbers, intensities):
        """Identify mineral phases from spectrum"""
        self.mineral_phases = []
        self.mineral_listbox.delete(0, "end")
        
        # Simple peak-based mineral identification
        # (In production, use spectral library matching)
        
        peaks = []
        for i, wn in enumerate(wavenumbers):
            if 900 < wn < 1200:  # Silicate region
                if intensities[i] > 0.5:  # Threshold
                    peaks.append(wn)
        
        # Identify based on characteristic peaks
        if any(1000 < p < 1100 for p in peaks):
            self.mineral_phases.append("Quartz (SiO₂)")
        
        if any(950 < p < 1050 for p in peaks):
            self.mineral_phases.append("Feldspar (Plagioclase)")
        
        if any(3600 < wn < 3700 for wn in wavenumbers):
            self.mineral_phases.append("Hydroxyl minerals (Clay/Zeolite)")
        
        if any(2800 < wn < 3000 for wn in wavenumbers):
            self.mineral_phases.append("Organic compounds detected")
        
        # Display identified phases
        for phase in self.mineral_phases:
            self.mineral_listbox.insert("end", f"✓ {phase}")
        
        if not self.mineral_phases:
            self.mineral_listbox.insert("end", "No distinct phases identified")
    
    def add_to_sample(self):
        """Add FTIR data to current sample"""
        if not self.current_spectrum:
            messagebox.showwarning("No Data", 
                "Please acquire a spectrum first!")
            return
        
        if not self.app.samples:
            messagebox.showwarning("No Sample", 
                "Please create or select a sample first!")
            return
        
        # Get current sample
        current_sample = self.app.samples[-1]
        
        # Add FTIR data
        current_sample["FTIR_Timestamp"] = self.current_spectrum['timestamp']
        current_sample["FTIR_Peaks"] = len(self.current_spectrum['wavenumbers'])
        current_sample["FTIR_Minerals"] = ", ".join(self.mineral_phases) if self.mineral_phases else "None"
        
        # Refresh display
        self.app.refresh_tree()
        self.app._mark_unsaved_changes()
        
        messagebox.showinfo("Success", 
            f"FTIR data added to sample: {current_sample.get('Sample_ID', 'Unknown')}\n\n"
            f"Identified phases: {len(self.mineral_phases)}")
    
    def clear_data(self):
        """Clear current spectrum data"""
        self.current_spectrum = None
        self.mineral_phases = []
        self.spectrum_text.delete("1.0", "end")
        self.mineral_listbox.delete(0, "end")


def register_plugin(parent_app):
    """Register this plugin with the main application"""
    return AgilentFTIRPlugin(parent_app)
