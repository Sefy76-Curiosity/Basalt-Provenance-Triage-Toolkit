"""
GPS NMEA Plugin for Basalt Provenance Triage Toolkit v10.2
Universal GPS support via NMEA-0183 protocol

Works with: Garmin, Trimble, Emlid, Magellan, ALL GPS devices!
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

try:
    import pynmea2
    PYNMEA_AVAILABLE = True
except ImportError:
    PYNMEA_AVAILABLE = False

PLUGIN_INFO = {
    "id": "hardware_gps_nmea",
    "name": "GPS (NMEA Universal)",
    "category": "hardware",
    "type": "gps",
    "manufacturer": "Universal",
    "models": ["Garmin (all)", "Trimble (all)", "Emlid Reach", "Magellan", "Generic NMEA GPS"],
    "connection": "USB/Serial/Bluetooth",
    "icon": "📍",
    "description": "Universal GPS plugin. Works with ALL GPS devices via NMEA protocol!",
    "data_types": ["coordinates", "elevation"],
    "requires": ["pyserial", "pynmea2"]
}

class GPSNMEAPlugin:
    """Universal GPS Plugin using NMEA-0183 protocol"""
    
    def __init__(self, app):
        self.app = app
        self.window = None
        self.serial_port = None
        self.connected = False
        self.listening = False
        self.current_position = None
        
    def show_interface(self):
        """Show GPS interface"""
        if not SERIAL_AVAILABLE or not PYNMEA_AVAILABLE:
            messagebox.showerror("Missing Dependencies", 
                                "Required libraries not installed!\n\n"
                                "Install with:\n"
                                "pip install pyserial pynmea2")
            return
        
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return
        
        self.window = tk.Toplevel(self.app.root)
        self.window.title("📍 GPS Coordinates")
        self.window.geometry("500x400")
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Connection frame
        frame_conn = ttk.LabelFrame(self.window, text="Connection", padding=10)
        frame_conn.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(frame_conn, text="Port:").pack(side="left")
        self.port_var = tk.StringVar()
        ports = self.get_ports()
        port_combo = ttk.Combobox(frame_conn, textvariable=self.port_var, 
                                  values=ports, width=15)
        port_combo.pack(side="left", padx=5)
        if ports:
            port_combo.current(0)
        
        ttk.Button(frame_conn, text="🔌 Connect", 
                  command=self.connect_gps).pack(side="left", padx=5)
        
        self.status_label = ttk.Label(frame_conn, text="● Disconnected", 
                                     foreground="red")
        self.status_label.pack(side="right")
        
        # Position frame
        frame_pos = ttk.LabelFrame(self.window, text="Current Position", padding=10)
        frame_pos.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.lat_label = ttk.Label(frame_pos, text="Latitude: ---", 
                                   font=("Arial", 12))
        self.lat_label.pack(anchor="w", pady=5)
        
        self.lon_label = ttk.Label(frame_pos, text="Longitude: ---", 
                                   font=("Arial", 12))
        self.lon_label.pack(anchor="w", pady=5)
        
        self.alt_label = ttk.Label(frame_pos, text="Elevation: ---", 
                                   font=("Arial", 12))
        self.alt_label.pack(anchor="w", pady=5)
        
        self.sat_label = ttk.Label(frame_pos, text="Satellites: ---", 
                                   font=("Arial", 10))
        self.sat_label.pack(anchor="w", pady=5)
        
        # Buttons
        frame_buttons = ttk.Frame(self.window)
        frame_buttons.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(frame_buttons, text="📍 Capture Location", 
                  command=self.capture_location,
                  style="Accent.TButton").pack(side="left", padx=5)
        
        ttk.Button(frame_buttons, text="❌ Close", 
                  command=self.on_close).pack(side="right", padx=5)
    
    def get_ports(self):
        """Get available serial ports"""
        if not SERIAL_AVAILABLE:
            return []
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]
    
    def connect_gps(self):
        """Connect to GPS"""
        port = self.port_var.get()
        if not port:
            messagebox.showwarning("No Port", "Select a port first")
            return
        
        try:
            self.serial_port = serial.Serial(port, baudrate=9600, timeout=0.5)
            self.connected = True
            self.listening = True
            self.status_label.config(text="● Connected", foreground="green")
            
            # Start listener
            threading.Thread(target=self.listen_gps, daemon=True).start()
            messagebox.showinfo("Connected", f"✅ Connected to GPS on {port}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect:\n{e}")
    
    def listen_gps(self):
        """Listen for GPS data"""
        while self.listening and self.serial_port and self.serial_port.is_open:
            try:
                line = self.serial_port.readline().decode('ascii', errors='replace')
                
                if line.startswith('$GPGGA') or line.startswith('$GNGGA'):
                    msg = pynmea2.parse(line)
                    
                    if msg.gps_qual > 0:  # Valid fix
                        self.current_position = {
                            'latitude': msg.latitude,
                            'longitude': msg.longitude,
                            'altitude': msg.altitude if msg.altitude else 0,
                            'num_sats': int(msg.num_sats) if msg.num_sats else 0
                        }
                        
                        # Update UI
                        self.window.after(0, self.update_display)
                
                time.sleep(0.1)
            except Exception as e:
                print(f"GPS error: {e}")
                time.sleep(1)
    
    def update_display(self):
        """Update position display"""
        if self.current_position:
            self.lat_label.config(
                text=f"Latitude: {self.current_position['latitude']:.6f}°")
            self.lon_label.config(
                text=f"Longitude: {self.current_position['longitude']:.6f}°")
            self.alt_label.config(
                text=f"Elevation: {self.current_position['altitude']:.1f} m")
            self.sat_label.config(
                text=f"Satellites: {self.current_position['num_sats']}")
    
    def capture_location(self):
        """Capture current location to sample"""
        if not self.current_position:
            messagebox.showwarning("No Fix", "Waiting for GPS fix...")
            return
        
        if not hasattr(self.app, 'selected_sample') or not self.app.selected_sample:
            messagebox.showwarning("No Sample", "Select a sample first!")
            return
        
        # Add coordinates to sample
        self.app.selected_sample['Latitude'] = self.current_position['latitude']
        self.app.selected_sample['Longitude'] = self.current_position['longitude']
        self.app.selected_sample['Elevation_m'] = self.current_position['altitude']
        
        # Refresh
        if hasattr(self.app, '_populate_tree'):
            self.app._populate_tree()
        
        messagebox.showinfo("Success", 
                           f"✅ Location saved to {self.app.selected_sample['Sample_ID']}")
    
    def on_close(self):
        """Handle window close"""
        self.listening = False
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        if self.window:
            self.window.destroy()
    
    def test_connection(self):
        """Test connection"""
        if not SERIAL_AVAILABLE or not PYNMEA_AVAILABLE:
            return False, "Required libraries not installed"
        
        ports = self.get_ports()
        if ports:
            return True, f"Found {len(ports)} port(s)"
        return False, "No ports found"


def register_plugin(app):
    """Register plugin"""
    return GPSNMEAPlugin(app)
