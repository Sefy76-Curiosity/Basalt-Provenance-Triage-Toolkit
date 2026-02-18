"""
File Monitor Plugin for Basalt Provenance Triage Toolkit v10.2
Universal fallback - works with ANY device that saves files!

Monitors a folder and auto-imports new CSV/Excel files
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
from pathlib import Path

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False

PLUGIN_INFO = {
    "id": "hardware_file_monitor",
    "name": "File Monitor (Universal)",
    "category": "hardware",
    "icon": "📁",
    "description": "Universal fallback! Watches folder and auto-imports new files.",
    "requires": ["watchdog"]
}

class FileMonitorPlugin:
    """Universal File Monitor - works with everything!"""
    
    def __init__(self, app):
        self.app = app
        self.window = None
        self.monitoring = False
        self.monitor_thread = None
        self.watch_folder = None
        
    def show_interface(self):
        """Show file monitor interface"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return
        
        self.window = tk.Toplevel(self.app.root)
        self.window.title("📁 File Monitor")
        self.window.geometry("600x400")
        
        # Folder selection
        frame_folder = ttk.LabelFrame(self.window, text="Watch Folder", padding=10)
        frame_folder.pack(fill="x", padx=10, pady=5)
        
        self.folder_var = tk.StringVar(value="Not selected")
        ttk.Label(frame_folder, textvariable=self.folder_var, 
                 font=("Arial", 10)).pack(side="left", fill="x", expand=True)
        
        ttk.Button(frame_folder, text="📂 Browse", 
                  command=self.select_folder).pack(side="right", padx=5)
        
        # Monitoring controls
        frame_controls = ttk.Frame(self.window)
        frame_controls.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(frame_controls, text="▶️ Start Monitoring", 
                  command=self.start_monitoring,
                  style="Accent.TButton").pack(side="left", padx=5)
        
        ttk.Button(frame_controls, text="⏹ Stop", 
                  command=self.stop_monitoring).pack(side="left", padx=5)
        
        self.status_label = ttk.Label(frame_controls, text="● Not monitoring", 
                                     foreground="gray")
        self.status_label.pack(side="right")
        
        # Log frame
        frame_log = ttk.LabelFrame(self.window, text="Activity Log", padding=5)
        frame_log.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.log_text = tk.Text(frame_log, height=15, wrap=tk.WORD)
        self.log_text.pack(fill="both", expand=True)
        scrollbar = ttk.Scrollbar(frame_log, command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # Instructions
        frame_instructions = ttk.LabelFrame(self.window, text="How It Works", padding=5)
        frame_instructions.pack(fill="x", padx=10, pady=5)
        
        instructions = """
Point your instrument to save files in the watched folder.
When new CSV/Excel files appear, they're auto-imported!
Perfect fallback when direct connection isn't available.
        """
        
        ttk.Label(frame_instructions, text=instructions, 
                 justify="left", font=("Arial", 9)).pack()
        
        ttk.Button(self.window, text="❌ Close", 
                  command=self.window.destroy).pack(pady=10)
    
    def select_folder(self):
        """Select folder to monitor"""
        folder = filedialog.askdirectory(title="Select Folder to Monitor")
        if folder:
            self.watch_folder = folder
            self.folder_var.set(folder)
            self.log(f"📂 Selected: {folder}")
    
    def start_monitoring(self):
        """Start monitoring folder"""
        if not self.watch_folder:
            messagebox.showwarning("No Folder", "Select a folder first!")
            return
        
        if not Path(self.watch_folder).exists():
            messagebox.showerror("Error", "Folder doesn't exist!")
            return
        
        self.monitoring = True
        self.status_label.config(text="● Monitoring", foreground="green")
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        self.log(f"▶️ Started monitoring: {self.watch_folder}")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        self.status_label.config(text="● Stopped", foreground="red")
        self.log("⏹ Monitoring stopped")
    
    def monitor_loop(self):
        """Simple file monitoring loop"""
        known_files = set()
        
        # Get initial files
        folder = Path(self.watch_folder)
        for file in folder.glob("*.csv"):
            known_files.add(file.name)
        for file in folder.glob("*.xlsx"):
            known_files.add(file.name)
        
        while self.monitoring:
            try:
                # Check for new files
                current_files = set()
                for file in folder.glob("*.csv"):
                    current_files.add(file.name)
                for file in folder.glob("*.xlsx"):
                    current_files.add(file.name)
                
                # Find new files
                new_files = current_files - known_files
                
                if new_files:
                    for filename in new_files:
                        filepath = folder / filename
                        self.log(f"📄 New file detected: {filename}")
                        self.import_file(filepath)
                    
                    known_files = current_files
                
                time.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                self.log(f"⚠️ Error: {e}")
                time.sleep(5)
    
    def import_file(self, filepath):
        """Import a file"""
        try:
            # Simple CSV import (can be enhanced)
            import csv
            
            with open(filepath, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            if rows:
                self.log(f"✅ Imported {len(rows)} sample(s) from {filepath.name}")
                
                # Add to app samples
                for row in rows:
                    if hasattr(self.app, 'samples'):
                        self.app.samples.append(row)
                
                # Refresh tree
                if hasattr(self.app, '_populate_tree'):
                    self.app.after(0, self.app._populate_tree)
            
        except Exception as e:
            self.log(f"⚠️ Import failed: {e}")
    
    def log(self, message):
        """Add message to log"""
        if hasattr(self, 'log_text'):
            timestamp = time.strftime("%H:%M:%S")
            self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.log_text.see(tk.END)
    
    def test_connection(self):
        """Test connection"""
        return True, "File monitor ready! Select a folder to start."


def register_plugin(app):
    """Register plugin"""
    return FileMonitorPlugin(app)
