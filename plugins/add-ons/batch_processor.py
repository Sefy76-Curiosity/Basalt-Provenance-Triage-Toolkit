"""
Batch Processor - UI Add-on
Process multiple CSV files in a directory

Author: Sefy Levy
Category: UI Add-on
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
from pathlib import Path

PLUGIN_INFO = {
    'id': 'batch_processor',
    'name': 'Batch Processor',
    'category': 'add-on',
    'icon': '📁',
    'requires': [],
    'description': 'Process multiple CSV files in a directory at once'
}


class BatchProcessorPlugin:
    """Batch processor add-on"""
    
    def __init__(self, parent_app):
        self.app = parent_app
    
    def show(self):
        """Show batch processing dialog"""
        window = tk.Toplevel(self.app.root)
        window.title("Batch Processor")
        window.geometry("500x300")
        
        # Header
        ttk.Label(window, text="📁 Batch Process Directory", 
                 font=("Arial", 14, "bold")).pack(pady=10)
        
        ttk.Label(window, text="Select a directory containing CSV files to process",
                 font=("Arial", 10)).pack(pady=5)
        
        # Directory selection
        dir_frame = ttk.Frame(window)
        dir_frame.pack(pady=20, padx=20, fill="x")
        
        self.dir_label = ttk.Label(dir_frame, text="No directory selected", 
                                   foreground="gray")
        self.dir_label.pack()
        
        ttk.Button(dir_frame, text="Select Directory", 
                  command=lambda: self.select_directory(window)).pack(pady=10)
        
        # Options
        options_frame = ttk.LabelFrame(window, text="Options", padding=10)
        options_frame.pack(pady=10, padx=20, fill="both")
        
        self.classify_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Auto-classify all samples",
                       variable=self.classify_var).pack(anchor="w")
        
        self.recursive_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Include subdirectories",
                       variable=self.recursive_var).pack(anchor="w")
        
        # Process button
        ttk.Button(window, text="Process Files", 
                  command=lambda: self.process_batch(window)).pack(pady=20)
    
    def select_directory(self, window):
        """Select directory to process"""
        directory = filedialog.askdirectory(title="Select Directory")
        if directory:
            self.selected_dir = directory
            self.dir_label.config(text=directory, foreground="black")
    
    def process_batch(self, window):
        """Process all CSV files in directory"""
        if not hasattr(self, 'selected_dir'):
            messagebox.showwarning("No Directory", "Please select a directory first!")
            return
        
        try:
            path = Path(self.selected_dir)
            pattern = "**/*.csv" if self.recursive_var.get() else "*.csv"
            csv_files = list(path.glob(pattern))
            
            if not csv_files:
                messagebox.showinfo("No Files", "No CSV files found in directory!")
                return
            
            # Process files
            total_samples = 0
            for csv_file in csv_files:
                try:
                    with open(csv_file, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            if row.get('Sample_ID'):
                                self.app.samples.append(row)
                                total_samples += 1
                except Exception as e:
                    print(f"Error processing {csv_file}: {e}")
            
            # Classify if requested
            if self.classify_var.get() and total_samples > 0:
                self.app.classify_all()
            
            # Refresh
            self.app.refresh_tree()
            self.app._mark_unsaved_changes()
            
            messagebox.showinfo("Batch Processing Complete",
                f"✅ Processed {len(csv_files)} file(s)\n"
                f"Imported {total_samples} sample(s)")
            
            window.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Batch processing failed:\n{str(e)}")


def register_plugin(parent_app):
    """Register this add-on with the main application"""
    return BatchProcessorPlugin(parent_app)
