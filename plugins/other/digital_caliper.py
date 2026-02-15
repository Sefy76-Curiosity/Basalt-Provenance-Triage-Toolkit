"""
Digital Caliper Plugin for Basalt Provenance Triage Toolkit v10.2
Supports: Mitutoyo Digimatic, Generic USB calipers

Hardware acts as HID keyboard - numbers type automatically into focused field!
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading

PLUGIN_INFO = {
    "id": "hardware_digital_caliper",
    "name": "Digital Caliper (USB HID)",
    "category": "hardware",
    "type": "measurement",
    "manufacturer": "Multiple (Mitutoyo, Generic)",
    "models": ["Mitutoyo Digimatic 500-series", "Generic USB calipers"],
    "connection": "USB (HID Keyboard mode)",
    "icon": "📏",
    "description": "Digital calipers with USB data output. Numbers type automatically!",
    "data_types": ["thickness", "diameter", "length"],
    "requires": []  # No Python packages - it's just keyboard input!
}

class DigitalCaliperPlugin:
    """
    Digital Caliper Plugin
    
    Supports any digital caliper with USB HID keyboard output.
    The caliper acts as a keyboard - when you press the DATA button,
    it types the measurement into the focused input field!
    """
    
    def __init__(self, app):
        self.app = app
        self.window = None
        self.entry_widgets = {}
        self.connected = True  # Always "connected" since it's HID
        
    def show_interface(self):
        """Show caliper measurement interface"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return
        
        self.window = tk.Toplevel(self.app.root)
        self.window.title("📏 Digital Caliper Measurements")
        self.window.geometry("500x400")
        
        # Instructions
        frame_instructions = ttk.LabelFrame(self.window, text="Instructions", padding=10)
        frame_instructions.pack(fill="x", padx=10, pady=5)
        
        instructions = """
1. Connect your digital caliper via USB adapter
2. Click in the measurement field below
3. Measure your artifact with the caliper
4. Press the DATA button on the caliper
5. Number types automatically!
6. Click "Save to Sample" to add measurement
        """
        
        ttk.Label(frame_instructions, text=instructions, 
                 justify="left", wraplength=450).pack()
        
        # Measurement fields
        frame_measurements = ttk.LabelFrame(self.window, 
                                           text="Measurements", padding=10)
        frame_measurements.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.create_measurement_field(frame_measurements, 
                                     "Wall Thickness (mm):", "Wall_Thickness_mm")
        self.create_measurement_field(frame_measurements, 
                                     "Rim Diameter (mm):", "Rim_Diameter_mm")
        self.create_measurement_field(frame_measurements, 
                                     "Base Diameter (mm):", "Base_Diameter_mm")
        self.create_measurement_field(frame_measurements, 
                                     "Height (mm):", "Height_mm")
        
        # Sample info
        frame_sample = ttk.Frame(self.window)
        frame_sample.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(frame_sample, text="Current Sample:").pack(side="left")
        self.sample_label = ttk.Label(frame_sample, text="None selected", 
                                      font=("Arial", 10, "bold"))
        self.sample_label.pack(side="left", padx=10)
        
        # Buttons
        frame_buttons = ttk.Frame(self.window)
        frame_buttons.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(frame_buttons, text="💾 Save to Sample", 
                  command=self.save_measurements,
                  style="Accent.TButton").pack(side="left", padx=5)
        
        ttk.Button(frame_buttons, text="🔄 Clear Fields", 
                  command=self.clear_fields).pack(side="left", padx=5)
        
        ttk.Button(frame_buttons, text="❌ Close", 
                  command=self.window.destroy).pack(side="right", padx=5)
        
        # Update sample label
        self.update_sample_label()
    
    def create_measurement_field(self, parent, label_text, field_name):
        """Create a measurement input field"""
        frame = ttk.Frame(parent)
        frame.pack(fill="x", pady=5)
        
        label = ttk.Label(frame, text=label_text, width=20, anchor="w")
        label.pack(side="left")
        
        entry = ttk.Entry(frame, width=15, font=("Arial", 12))
        entry.pack(side="left", padx=10)
        
        # Hint label
        hint = ttk.Label(frame, text="← Press DATA on caliper", 
                        foreground="gray")
        hint.pack(side="left")
        
        self.entry_widgets[field_name] = entry
        
        # Focus hint - show which field is active
        def on_focus_in(event):
            hint.config(text="← READY! Press DATA button", 
                       foreground="green", font=("Arial", 9, "bold"))
        
        def on_focus_out(event):
            hint.config(text="← Press DATA on caliper", 
                       foreground="gray", font=("Arial", 9))
        
        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)
    
    def update_sample_label(self):
        """Update the current sample label"""
        if hasattr(self, 'sample_label'):
            if hasattr(self.app, 'selected_sample') and self.app.selected_sample:
                sample_id = self.app.selected_sample.get('Sample_ID', 'Unknown')
                self.sample_label.config(text=sample_id)
            else:
                self.sample_label.config(text="None selected - select a sample first!")
    
    def save_measurements(self):
        """Save measurements to current sample"""
        if not hasattr(self.app, 'selected_sample') or not self.app.selected_sample:
            messagebox.showwarning("No Sample", 
                                  "Please select a sample in the main window first!")
            return
        
        # Get measurements from entry fields
        measurements_added = 0
        for field_name, entry in self.entry_widgets.items():
            value = entry.get().strip()
            if value:
                try:
                    # Convert to float
                    float_value = float(value)
                    self.app.selected_sample[field_name] = float_value
                    measurements_added += 1
                except ValueError:
                    messagebox.showerror("Invalid Value", 
                                        f"'{value}' is not a valid number for {field_name}")
                    return
        
        if measurements_added > 0:
            # Refresh the tree view
            if hasattr(self.app, '_populate_tree'):
                self.app._populate_tree()
            
            messagebox.showinfo("Success", 
                               f"✅ Added {measurements_added} measurement(s) to {self.app.selected_sample['Sample_ID']}")
            
            # Clear fields
            self.clear_fields()
        else:
            messagebox.showwarning("No Data", 
                                  "No measurements entered. Use the caliper DATA button!")
    
    def clear_fields(self):
        """Clear all measurement fields"""
        for entry in self.entry_widgets.values():
            entry.delete(0, tk.END)
        
        # Focus on first field
        first_entry = list(self.entry_widgets.values())[0]
        first_entry.focus()
    
    def test_connection(self):
        """Test connection (always returns success for HID)"""
        return True, "Digital caliper ready! Connect USB adapter and press DATA button to test."


# Plugin registration
def register_plugin(app):
    """Register plugin with main application"""
    return DigitalCaliperPlugin(app)
