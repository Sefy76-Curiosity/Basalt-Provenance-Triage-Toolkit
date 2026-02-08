"""
PerkinElmer FTIR Hardware Plugin
Supports: Spectrum Two (Portable)

Uses: ctypes to interface with Windows DLL
Best for: Lab-based high-accuracy basalt mineralogy

Author: Sefy Levy
License: CC BY-NC-SA 4.0
"""

import tkinter as tk
from tkinter import ttk, messagebox
import time
import sys

# Windows DLL interface (requires ctypes - built-in)
HAS_CTYPES = True
try:
    import ctypes
    if sys.platform != 'win32':
        HAS_CTYPES = False
except ImportError:
    HAS_CTYPES = False

PLUGIN_INFO = {
      'category': 'hardware',
    'id': 'perkinelmer_ftir',
    'name': 'PerkinElmer FTIR (Spectrum)',
    'version': '1.0',
    'author': 'Sefy Levy',
    'description': 'PerkinElmer Spectrum FTIR integration',
    'category': 'Hardware',
    'icon': '⚗️',
    'requires': ['ctypes (built-in)', 'Windows OS'],
    'supported_models': [
        'PerkinElmer Spectrum Two (Portable)'
    ]
}


class PerkinElmerFTIRPlugin:
    """PerkinElmer FTIR hardware plugin"""
    
    def __init__(self, parent_app):
        self.app = parent_app
        self.window = None
        self.connected = False
        self.dll = None
        self.current_spectrum = None
        self.mineral_composition = []
        
    def show(self):
        """Show the PerkinElmer FTIR interface"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return
            
        self.window = tk.Toplevel(self.app.root)
        self.window.title("⚗️ PerkinElmer FTIR - Spectrum Series")
        self.window.geometry("700x600")
        
        # Header
        header = ttk.Frame(self.window)
        header.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(header, text="⚗️ PerkinElmer FTIR", 
                 font=("Arial", 14, "bold")).pack(side="left")
        
        # Models info
        info_frame = ttk.LabelFrame(self.window, text="Supported Models", padding=10)
        info_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(info_frame, text="✓ PerkinElmer Spectrum Two (Portable)").pack(anchor="w")
        ttk.Label(info_frame, text="Interface: Spectrum 10 SDK (Windows DLL)").pack(anchor="w")
        
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
        
        ttk.Label(spectrum_frame, text="High-accuracy lab-grade FTIR analysis", 
                 font=("Arial", 9, "italic")).pack(pady=5)
        
        self.spectrum_text = tk.Text(spectrum_frame, height=10, width=60, 
                                     font=("Courier", 9))
        self.spectrum_text.pack(fill="both", expand=True, pady=5)
        
        # Mineral composition
        mineral_frame = ttk.LabelFrame(self.window, text="Mineral Composition", 
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
        
        # Platform check
        if not HAS_CTYPES:
            self.show_platform_warning()
    
    def show_platform_warning(self):
        """Show warning about platform requirements"""
        warning = tk.Label(self.window, 
                          text="⚠️ Windows platform required for PerkinElmer SDK",
                          bg="#FFF3CD", fg="#856404", padx=10, pady=5)
        warning.pack(fill="x", padx=10, pady=5)
        self.connect_btn.config(state="disabled")
    
    def connect_device(self):
        """Connect to PerkinElmer device via DLL"""
        if not HAS_CTYPES:
            messagebox.showerror("Error", 
                "Windows platform required for PerkinElmer SDK!")
            return
        
        try:
            # Load PerkinElmer Spectrum 10 DLL
            dll_path = "C:\\Program Files\\PerkinElmer\\Spectrum10\\SDK\\Spectrum10.dll"
            self.dll = ctypes.CDLL(dll_path)
            
            # Initialize connection
            result = self.dll.InitializeDevice()
            
            if result == 0:  # Success
                self.connected = True
                self.status_label.config(text="● Connected", foreground="green")
                self.connect_btn.config(text="🔌 Disconnect", 
                                       command=self.disconnect_device)
                
                # Get device info
                model_buffer = ctypes.create_string_buffer(100)
                self.dll.GetModelName(model_buffer, 100)
                model = model_buffer.value.decode('utf-8')
                
                messagebox.showinfo("Success", 
                    f"Connected to PerkinElmer FTIR!\n\nModel: {model}")
            else:
                raise Exception(f"Initialization failed with code {result}")
                
        except FileNotFoundError:
            messagebox.showerror("DLL Not Found", 
                "PerkinElmer SDK not found!\n\n"
                "Expected location:\n"
                "C:\\Program Files\\PerkinElmer\\Spectrum10\\SDK\\Spectrum10.dll\n\n"
                "Please install Spectrum 10 software.")
        except Exception as e:
            messagebox.showerror("Connection Error", 
                f"Could not connect to device:\n{str(e)}\n\n"
                "Make sure:\n"
                "• Spectrum 10 software is installed\n"
                "• Device is powered on\n"
                "• USB drivers are installed")
    
    def disconnect_device(self):
        """Disconnect from device"""
        if self.dll:
            try:
                self.dll.CloseDevice()
            except:
                pass
        self.dll = None
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
            # Query device status
            status_buffer = ctypes.create_string_buffer(100)
            self.dll.GetDeviceStatus(status_buffer, 100)
            status = status_buffer.value.decode('utf-8')
            
            # Get serial number
            serial_buffer = ctypes.create_string_buffer(100)
            self.dll.GetSerialNumber(serial_buffer, 100)
            serial = serial_buffer.value.decode('utf-8')
            
            messagebox.showinfo("Connection Test", 
                f"✅ Connection Successful!\n\n"
                f"Serial: {serial}\n"
                f"Status: {status}")
        except Exception as e:
            messagebox.showerror("Test Failed", 
                f"Connection test failed:\n{str(e)}")
    
    def acquire_spectrum(self):
        """Acquire high-accuracy FTIR spectrum"""
        if not self.connected:
            messagebox.showwarning("Not Connected", 
                "Please connect to device first!")
            return
        
        try:
            # Trigger measurement
            result = self.dll.AcquireSpectrum()
            
            if result != 0:
                raise Exception(f"Acquisition failed with code {result}")
            
            # Wait for completion
            time.sleep(3)
            
            # Get spectrum data
            num_points = ctypes.c_int()
            self.dll.GetNumDataPoints(ctypes.byref(num_points))
            
            # Allocate arrays
            wavenumbers = (ctypes.c_double * num_points.value)()
            intensities = (ctypes.c_double * num_points.value)()
            
            # Read data
            self.dll.GetWavenumbers(wavenumbers, num_points)
            self.dll.GetIntensities(intensities, num_points)
            
            # Store spectrum
            self.current_spectrum = {
                'wavenumbers': list(wavenumbers),
                'intensities': list(intensities),
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Display spectrum info
            self.spectrum_text.delete("1.0", "end")
            self.spectrum_text.insert("end", 
                f"High-accuracy spectrum acquired: {self.current_spectrum['timestamp']}\n"
                f"Data points: {num_points.value}\n"
                f"Range: {min(wavenumbers):.1f} - {max(wavenumbers):.1f} cm⁻¹\n"
                f"Resolution: 4 cm⁻¹ (lab-grade)\n\n")
            
            # Analyze mineralogy
            self.analyze_mineralogy(list(wavenumbers), list(intensities))
            
            messagebox.showinfo("Success", 
                "High-accuracy spectrum acquired successfully!")
            
        except Exception as e:
            messagebox.showerror("Acquisition Error", 
                f"Failed to acquire spectrum:\n{str(e)}")
    
    def analyze_mineralogy(self, wavenumbers, intensities):
        """Analyze basalt mineralogy"""
        self.mineral_composition = []
        self.mineral_listbox.delete(0, "end")
        
        # High-precision mineralogy analysis
        peaks = {wn: intensities[i] for i, wn in enumerate(wavenumbers) 
                if intensities[i] > 0.5}
        
        # Olivine
        if any(820 < p < 880 for p in peaks):
            self.mineral_composition.append("Olivine (Mg,Fe)₂SiO₄")
        
        # Pyroxene (Augite)
        if any(950 < p < 1050 for p in peaks):
            self.mineral_composition.append("Pyroxene (Augite)")
        
        # Plagioclase feldspar
        if any(1050 < p < 1150 for p in peaks):
            self.mineral_composition.append("Plagioclase feldspar")
        
        # Volcanic glass
        if any(1000 < p < 1200 for p in peaks) and len([p for p in peaks if 1000 < p < 1200]) > 3:
            self.mineral_composition.append("Volcanic glass (high content)")
        
        # Magnetite
        if any(550 < p < 600 for p in peaks):
            self.mineral_composition.append("Magnetite Fe₃O₄")
        
        # Alteration products
        if any(3400 < p < 3700 for p in peaks):
            self.mineral_composition.append("Hydroxyl minerals (alteration)")
        
        # Display composition
        for mineral in self.mineral_composition:
            self.mineral_listbox.insert("end", f"✓ {mineral}")
        
        if not self.mineral_composition:
            self.mineral_listbox.insert("end", "Amorphous or poorly crystalline")
    
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
        current_sample["FTIR_PE_Timestamp"] = self.current_spectrum['timestamp']
        current_sample["FTIR_PE_Minerals"] = ", ".join(self.mineral_composition) if self.mineral_composition else "None"
        current_sample["FTIR_PE_Datapoints"] = len(self.current_spectrum['wavenumbers'])
        
        # Refresh display
        self.app.refresh_tree()
        self.app._mark_unsaved_changes()
        
        messagebox.showinfo("Success", 
            f"PerkinElmer FTIR data added to sample: {current_sample.get('Sample_ID', 'Unknown')}\n\n"
            f"Identified minerals: {len(self.mineral_composition)}")
    
    def clear_data(self):
        """Clear current spectrum data"""
        self.current_spectrum = None
        self.mineral_composition = []
        self.spectrum_text.delete("1.0", "end")
        self.mineral_listbox.delete(0, "end")


def register_plugin(parent_app):
    """Register this plugin with the main application"""
    return PerkinElmerFTIRPlugin(parent_app)
