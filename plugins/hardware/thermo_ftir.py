"""
Thermo Scientific FTIR Hardware Plugin
Supports: Nicolet iS5, Summit Mobile

Uses: REST API / OMNIC SDK
Best for: Environmental health, microplastics detection

Author: Sefy Levy
License: CC BY-NC-SA 4.0
"""

import tkinter as tk
from tkinter import ttk, messagebox
import time

# REST API interface (requires requests)
HAS_REQUESTS = False
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    pass

PLUGIN_INFO = {
      'category': 'hardware',
    'id': 'thermo_ftir',
    'name': 'Thermo FTIR (Nicolet)',
    'version': '1.0',
    'author': 'Sefy Levy',
    'description': 'Thermo Scientific Nicolet FTIR integration',
    'category': 'Hardware',
    'icon': '🌡️',
    'requires': ['requests'],
    'supported_models': [
        'Thermo Nicolet iS5',
        'Thermo Nicolet Summit (Mobile)'
    ]
}


class ThermoFTIRPlugin:
    """Thermo Scientific FTIR hardware plugin"""
    
    def __init__(self, parent_app):
        self.app = parent_app
        self.window = None
        self.connected = False
        self.api_url = "http://localhost:8080/api"  # Default OMNIC API endpoint
        self.current_spectrum = None
        self.detected_compounds = []
        
    def show(self):
        """Show the Thermo FTIR interface"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return
            
        self.window = tk.Toplevel(self.app.root)
        self.window.title("🌡️ Thermo FTIR - Nicolet Series")
        self.window.geometry("700x600")
        
        # Header
        header = ttk.Frame(self.window)
        header.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(header, text="🌡️ Thermo Scientific FTIR", 
                 font=("Arial", 14, "bold")).pack(side="left")
        
        # Models info
        info_frame = ttk.LabelFrame(self.window, text="Supported Models", padding=10)
        info_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(info_frame, text="✓ Thermo Nicolet iS5").pack(anchor="w")
        ttk.Label(info_frame, text="✓ Thermo Nicolet Summit (Mobile)").pack(anchor="w")
        ttk.Label(info_frame, text="Interface: OMNIC REST API").pack(anchor="w")
        
        # Connection frame
        conn_frame = ttk.LabelFrame(self.window, text="Connection", padding=10)
        conn_frame.pack(fill="x", padx=10, pady=5)
        
        # API URL
        url_frame = ttk.Frame(conn_frame)
        url_frame.pack(fill="x", pady=5)
        ttk.Label(url_frame, text="API URL:").pack(side="left", padx=5)
        self.url_entry = ttk.Entry(url_frame, width=40)
        self.url_entry.insert(0, self.api_url)
        self.url_entry.pack(side="left", padx=5)
        
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
        
        # Compound identification
        compound_frame = ttk.LabelFrame(self.window, text="Detected Compounds", 
                                        padding=10)
        compound_frame.pack(fill="x", padx=10, pady=5)
        
        self.compound_listbox = tk.Listbox(compound_frame, height=4, 
                                           font=("Arial", 10))
        self.compound_listbox.pack(fill="both", expand=True)
        
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
        if not HAS_REQUESTS:
            self.show_dependency_warning()
    
    def show_dependency_warning(self):
        """Show warning about missing dependencies"""
        warning = tk.Label(self.window, 
                          text="⚠️ requests not installed. Install with: pip install requests",
                          bg="#FFF3CD", fg="#856404", padx=10, pady=5)
        warning.pack(fill="x", padx=10, pady=5)
        self.connect_btn.config(state="disabled")
    
    def connect_device(self):
        """Connect to OMNIC API"""
        if not HAS_REQUESTS:
            messagebox.showerror("Error", 
                "requests library not installed!\n\n"
                "Install with: pip install requests")
            return
        
        try:
            self.api_url = self.url_entry.get()
            
            # Test API connection
            response = requests.get(f"{self.api_url}/status", timeout=5)
            
            if response.status_code == 200:
                self.connected = True
                self.status_label.config(text="● Connected", foreground="green")
                self.connect_btn.config(text="🔌 Disconnect", 
                                       command=self.disconnect_device)
                
                data = response.json()
                instrument = data.get('instrument', 'Unknown')
                
                messagebox.showinfo("Success", 
                    f"Connected to Nicolet FTIR!\n\nInstrument: {instrument}")
            else:
                raise Exception(f"HTTP {response.status_code}")
                
        except Exception as e:
            messagebox.showerror("Connection Error", 
                f"Could not connect to OMNIC API:\n{str(e)}\n\n"
                "Make sure:\n"
                "• OMNIC software is running\n"
                "• API server is enabled\n"
                "• Correct URL is entered")
    
    def disconnect_device(self):
        """Disconnect from API"""
        self.connected = False
        self.status_label.config(text="● Not Connected", foreground="red")
        self.connect_btn.config(text="🔌 Connect", command=self.connect_device)
    
    def test_connection(self):
        """Test API connection"""
        if not self.connected:
            messagebox.showwarning("Not Connected", 
                "Please connect to device first!")
            return
        
        try:
            response = requests.get(f"{self.api_url}/instrument/info", timeout=5)
            data = response.json()
            
            messagebox.showinfo("Connection Test", 
                f"✅ Connection Successful!\n\n"
                f"Model: {data.get('model', 'Unknown')}\n"
                f"Serial: {data.get('serial', 'Unknown')}\n"
                f"Status: {data.get('status', 'Ready')}")
        except Exception as e:
            messagebox.showerror("Test Failed", 
                f"Connection test failed:\n{str(e)}")
    
    def acquire_spectrum(self):
        """Acquire FTIR spectrum via API"""
        if not self.connected:
            messagebox.showwarning("Not Connected", 
                "Please connect to device first!")
            return
        
        try:
            # Trigger measurement
            response = requests.post(f"{self.api_url}/measure", 
                                    json={"mode": "sample"}, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Store spectrum
                self.current_spectrum = {
                    'wavenumbers': data.get('wavenumbers', []),
                    'intensities': data.get('intensities', []),
                    'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                      'category': 'hardware',
    'id': data.get('spectrum_id', '')
                }
                
                # Display spectrum info
                self.spectrum_text.delete("1.0", "end")
                self.spectrum_text.insert("end", 
                    f"Spectrum acquired: {self.current_spectrum['timestamp']}\n"
                    f"Spectrum ID: {self.current_spectrum['id']}\n"
                    f"Data points: {len(self.current_spectrum['wavenumbers'])}\n\n")
                
                # Identify compounds
                self.identify_compounds(self.current_spectrum['wavenumbers'], 
                                       self.current_spectrum['intensities'])
                
                messagebox.showinfo("Success", "Spectrum acquired successfully!")
            else:
                raise Exception(f"HTTP {response.status_code}")
                
        except Exception as e:
            messagebox.showerror("Acquisition Error", 
                f"Failed to acquire spectrum:\n{str(e)}")
    
    def identify_compounds(self, wavenumbers, intensities):
        """Identify organic compounds (environmental focus)"""
        self.detected_compounds = []
        self.compound_listbox.delete(0, "end")
        
        # Environmental compound detection
        peaks = {wn: intensities[i] for i, wn in enumerate(wavenumbers) 
                if intensities[i] > 0.5}
        
        # Microplastics
        if any(2800 < p < 3000 for p in peaks) and any(1450 < p < 1480 for p in peaks):
            self.detected_compounds.append("Polyethylene (PE) microplastics")
        
        if any(1720 < p < 1750 for p in peaks):
            self.detected_compounds.append("PVC or PET microplastics")
        
        # Hydrocarbons
        if any(2900 < p < 2960 for p in peaks):
            self.detected_compounds.append("Aliphatic hydrocarbons (oil/fuel)")
        
        # PAHs
        if any(3000 < p < 3100 for p in peaks):
            self.detected_compounds.append("Aromatic hydrocarbons (PAHs)")
        
        # Display detected compounds
        for compound in self.detected_compounds:
            self.compound_listbox.insert("end", f"⚠️ {compound}")
        
        if not self.detected_compounds:
            self.compound_listbox.insert("end", "✓ No pollutants detected")
    
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
        current_sample["FTIR_Nicolet_Timestamp"] = self.current_spectrum['timestamp']
        current_sample["FTIR_Nicolet_ID"] = self.current_spectrum.get('id', '')
        current_sample["FTIR_Nicolet_Compounds"] = ", ".join(self.detected_compounds) if self.detected_compounds else "None detected"
        
        # Refresh display
        self.app.refresh_tree()
        self.app._mark_unsaved_changes()
        
        messagebox.showinfo("Success", 
            f"Thermo FTIR data added to sample: {current_sample.get('Sample_ID', 'Unknown')}")
    
    def clear_data(self):
        """Clear current spectrum data"""
        self.current_spectrum = None
        self.detected_compounds = []
        self.spectrum_text.delete("1.0", "end")
        self.compound_listbox.delete(0, "end")


def register_plugin(parent_app):
    """Register this plugin with the main application"""
    return ThermoFTIRPlugin(parent_app)
