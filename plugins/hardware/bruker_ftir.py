"""
Bruker FTIR Hardware Plugin
Supports: ALPHA II, MOBILE IR II

Uses: pywin32 to interface with OPUS/RS DCOM API
Best for: Museum conservation, archaeometallurgy

Author: Sefy Levy
License: CC BY-NC-SA 4.0
"""

import tkinter as tk
from tkinter import ttk, messagebox
import time

# OPUS DCOM interface (requires pywin32)
HAS_PYWIN32 = False
try:
    import win32com.client
    HAS_PYWIN32 = True
except ImportError:
    pass

PLUGIN_INFO = {
      'category': 'hardware',
    'id': 'bruker_ftir',
    'name': 'Bruker FTIR (ALPHA/MOBILE)',
    'version': '1.0',
    'author': 'Sefy Levy',
    'description': 'Bruker FTIR analyzer integration via OPUS API',
    'category': 'Hardware',
    'icon': '🔬',
    'requires': ['pywin32'],
    'supported_models': [
        'Bruker ALPHA II',
        'Bruker MOBILE IR II'
    ]
}


class BrukerFTIRPlugin:
    """Bruker FTIR analyzer hardware plugin"""
    
    def __init__(self, parent_app):
        self.app = parent_app
        self.window = None
        self.connected = False
        self.opus = None
        self.current_spectrum = None
        self.mineral_phases = []
        
    def show(self):
        """Show the Bruker FTIR interface"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return
            
        self.window = tk.Toplevel(self.app.root)
        self.window.title("🔬 Bruker FTIR - ALPHA/MOBILE Series")
        self.window.geometry("700x600")
        
        # Header
        header = ttk.Frame(self.window)
        header.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(header, text="🔬 Bruker FTIR Analyzer", 
                 font=("Arial", 14, "bold")).pack(side="left")
        
        # Models info
        info_frame = ttk.LabelFrame(self.window, text="Supported Models", padding=10)
        info_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(info_frame, text="✓ Bruker ALPHA II").pack(anchor="w")
        ttk.Label(info_frame, text="✓ Bruker MOBILE IR II").pack(anchor="w")
        ttk.Label(info_frame, text="Interface: OPUS/RS (DCOM)").pack(anchor="w")
        
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
        
        self.spectrum_text = tk.Text(spectrum_frame, height=10, width=60, 
                                     font=("Courier", 9))
        self.spectrum_text.pack(fill="both", expand=True, pady=5)
        
        # Mineral identification
        mineral_frame = ttk.LabelFrame(self.window, text="Identified Phases", 
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
        if not HAS_PYWIN32:
            self.show_dependency_warning()
    
    def show_dependency_warning(self):
        """Show warning about missing dependencies"""
        warning = tk.Label(self.window, 
                          text="⚠️ pywin32 not installed. Install with: pip install pywin32",
                          bg="#FFF3CD", fg="#856404", padx=10, pady=5)
        warning.pack(fill="x", padx=10, pady=5)
        self.connect_btn.config(state="disabled")
    
    def connect_device(self):
        """Connect to Bruker OPUS software via DCOM"""
        if not HAS_PYWIN32:
            messagebox.showerror("Error", 
                "pywin32 library not installed!\n\n"
                "Install with: pip install pywin32")
            return
        
        try:
            # Connect to OPUS via DCOM
            self.opus = win32com.client.Dispatch("OPUS.Application")
            
            if self.opus:
                self.connected = True
                self.status_label.config(text="● Connected to OPUS", foreground="green")
                self.connect_btn.config(text="🔌 Disconnect", 
                                       command=self.disconnect_device)
                
                # Get instrument info
                try:
                    instrument = self.opus.GetInstrumentName()
                    messagebox.showinfo("Success", 
                        f"Connected to Bruker OPUS!\n\nInstrument: {instrument}")
                except:
                    messagebox.showinfo("Success", "Connected to Bruker OPUS!")
            else:
                raise Exception("Failed to connect to OPUS")
                
        except Exception as e:
            messagebox.showerror("Connection Error", 
                f"Could not connect to OPUS:\n{str(e)}\n\n"
                "Make sure:\n"
                "• OPUS software is running\n"
                "• Instrument is powered on\n"
                "• OPUS/RS is configured")
    
    def disconnect_device(self):
        """Disconnect from OPUS"""
        self.opus = None
        self.connected = False
        self.status_label.config(text="● Not Connected", foreground="red")
        self.connect_btn.config(text="🔌 Connect", command=self.connect_device)
    
    def test_connection(self):
        """Test OPUS connection"""
        if not self.connected:
            messagebox.showwarning("Not Connected", 
                "Please connect to OPUS first!")
            return
        
        try:
            version = self.opus.GetVersionNumber()
            instrument = self.opus.GetInstrumentName()
            
            messagebox.showinfo("Connection Test", 
                f"✅ Connection Successful!\n\n"
                f"OPUS Version: {version}\n"
                f"Instrument: {instrument}\n"
                f"Status: Ready")
        except Exception as e:
            messagebox.showerror("Test Failed", 
                f"Connection test failed:\n{str(e)}")
    
    def acquire_spectrum(self):
        """Acquire FTIR spectrum via OPUS"""
        if not self.connected:
            messagebox.showwarning("Not Connected", 
                "Please connect to OPUS first!")
            return
        
        try:
            # Trigger measurement in OPUS
            self.opus.MeasureSample()
            
            # Wait for measurement completion
            time.sleep(2)
            
            # Retrieve spectrum data
            spectrum_file = self.opus.GetLastMeasuredFile()
            spectrum_data = self.opus.ReadSpectrum(spectrum_file)
            
            # Parse spectral data
            wavenumbers = spectrum_data.GetXData()
            intensities = spectrum_data.GetYData()
            
            # Store spectrum
            self.current_spectrum = {
                'wavenumbers': list(wavenumbers),
                'intensities': list(intensities),
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                'file': spectrum_file
            }
            
            # Display spectrum info
            self.spectrum_text.delete("1.0", "end")
            self.spectrum_text.insert("end", 
                f"Spectrum acquired: {self.current_spectrum['timestamp']}\n"
                f"File: {spectrum_file}\n"
                f"Data points: {len(wavenumbers)}\n"
                f"Range: {min(wavenumbers):.1f} - {max(wavenumbers):.1f} cm⁻¹\n\n")
            
            # Identify phases
            self.identify_phases(wavenumbers, intensities)
            
            messagebox.showinfo("Success", "Spectrum acquired successfully!")
            
        except Exception as e:
            messagebox.showerror("Acquisition Error", 
                f"Failed to acquire spectrum:\n{str(e)}")
    
    def identify_phases(self, wavenumbers, intensities):
        """Identify mineral/organic phases"""
        self.mineral_phases = []
        self.mineral_listbox.delete(0, "end")
        
        # Conservation-specific phase identification
        peaks = {wn: intensities[i] for i, wn in enumerate(wavenumbers) 
                if intensities[i] > 0.5}
        
        # Organic consolidants
        if any(2800 < p < 3000 for p in peaks):
            self.mineral_phases.append("Organic compounds (wax/resin)")
        
        # Carbonates (corrosion products)
        if any(1400 < p < 1500 for p in peaks):
            self.mineral_phases.append("Carbonate (corrosion/patina)")
        
        # Silicates
        if any(950 < p < 1100 for p in peaks):
            self.mineral_phases.append("Silicate minerals")
        
        # Sulfates (salt efflorescence)
        if any(1100 < p < 1200 for p in peaks):
            self.mineral_phases.append("Sulfate salts (efflorescence)")
        
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
        current_sample["FTIR_Bruker_Timestamp"] = self.current_spectrum['timestamp']
        current_sample["FTIR_Bruker_File"] = self.current_spectrum.get('file', '')
        current_sample["FTIR_Bruker_Phases"] = ", ".join(self.mineral_phases) if self.mineral_phases else "None"
        
        # Refresh display
        self.app.refresh_tree()
        self.app._mark_unsaved_changes()
        
        messagebox.showinfo("Success", 
            f"Bruker FTIR data added to sample: {current_sample.get('Sample_ID', 'Unknown')}")
    
    def clear_data(self):
        """Clear current spectrum data"""
        self.current_spectrum = None
        self.mineral_phases = []
        self.spectrum_text.delete("1.0", "end")
        self.mineral_listbox.delete(0, "end")


def register_plugin(parent_app):
    """Register this plugin with the main application"""
    return BrukerFTIRPlugin(parent_app)
