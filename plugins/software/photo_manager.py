"""
Photo Manager Plugin for Basalt Provenance Toolkit
Link sample photos and manage photo directories

Author: Sefy Levy
License: CC BY-NC-SA 4.0
"""

PLUGIN_INFO = {
      "category": "software",
    "id": "photo_manager",
    "name": "Photo Manager",
    "description": "Link sample photos, organize field photography, and open photo folders directly",
    "icon": "📷",
    "version": "1.0",
    "requires": [],  # No dependencies!
    "author": "Sefy Levy"
}

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import platform
from pathlib import Path


class PhotoManagerPlugin:
    """Plugin for managing sample photos"""
    
    def __init__(self, main_app):
        """Initialize plugin"""
        self.app = main_app
        self.window = None
    
    def open_window(self):
        """Open the photo manager interface"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return
        
        self.window = tk.Toplevel(self.app.root)
        self.window.title("Photo Manager")
        self.window.geometry("650x480")
        
        # Make window stay on top
        self.window.transient(self.app.root)
        
        self._create_interface()
        
        # Bring to front
        self.window.lift()
        self.window.focus_force()
    
    def _create_interface(self):
        """Create the photo manager interface"""
        # Header
        header = tk.Frame(self.window, bg="#FF9800")
        header.pack(fill=tk.X)
        
        tk.Label(header,
                text="📷 Photo Manager",
                font=("Arial", 16, "bold"),
                bg="#FF9800", fg="white",
                pady=5).pack()
        
        tk.Label(header,
                text="Link photos to samples and organize field photography",
                font=("Arial", 10),
                bg="#FF9800", fg="white",
                pady=5).pack()
        
        # Main content
        content = tk.Frame(self.window, padx=10, pady=8)
        content.pack(fill=tk.BOTH, expand=True)
        
        # Instructions
        info_frame = tk.LabelFrame(content, text="How It Works",
                                  font=("Arial", 11, "bold"),
                                  padx=8, pady=5)
        info_frame.pack(fill=tk.X, pady=5)
        
        instructions = "Add Photo_Path column to your data (folder or file path) • Click Open Folder to view in file browser"
        
        tk.Label(info_frame, text=instructions,
                font=("Arial", 9),
                justify=tk.LEFT,
                fg="#555").pack(anchor=tk.W)
        
        # Sample list with photo paths
        list_frame = tk.LabelFrame(content, text="Sample Photo Paths",
                                  font=("Arial", 11, "bold"),
                                  padx=10, pady=5)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create treeview
        tree_container = tk.Frame(list_frame)
        tree_container.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(tree_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree = ttk.Treeview(tree_container,
                                columns=('Sample ID', 'Photo Path', 'Status'),
                                show='headings',
                                yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.tree.yview)
        
        self.tree.heading('Sample ID', text='Sample ID')
        self.tree.heading('Photo Path', text='Photo Path')
        self.tree.heading('Status', text='Status')
        
        self.tree.column('Sample ID', width=150)
        self.tree.column('Photo Path', width=400)
        self.tree.column('Status', width=100)
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Populate tree
        self._populate_tree()
        
        # Buttons
        btn_frame = tk.Frame(content)
        btn_frame.pack(pady=5)
        
        tk.Button(btn_frame, text="👁️ Open Folder",
                 command=self._open_selected_folder,
                 bg="#2196F3", fg="white",
                 font=("Arial", 9, "bold"),
                 width=15).pack(side=tk.LEFT, padx=3)
        
        tk.Button(btn_frame, text="📁 Set Path",
                 command=self._set_photo_path,
                 bg="#4CAF50", fg="white",
                 font=("Arial", 9),
                 width=12).pack(side=tk.LEFT, padx=3)
        
        tk.Button(btn_frame, text="🔄 Refresh",
                 command=self._populate_tree,
                 font=("Arial", 9),
                 width=10).pack(side=tk.LEFT, padx=3)
    
    def _populate_tree(self):
        """Populate tree with samples and their photo paths"""
        # Clear existing
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add samples
        for sample in self.app.samples:
            sample_id = sample.get('Sample_ID', 'Unknown')
            photo_path = sample.get('Photo_Path', '')
            
            if photo_path:
                # Check if path exists
                path_obj = Path(photo_path)
                if path_obj.exists():
                    status = "✓ Found"
                    status_color = ""
                else:
                    status = "⚠ Not Found"
                    status_color = ""
            else:
                photo_path = "(not set)"
                status = "—"
                status_color = ""
            
            item = self.tree.insert('', tk.END, values=(sample_id, photo_path, status))
            
            # Color code by status
            if status == "⚠ Not Found":
                self.tree.item(item, tags=('missing',))
            elif status == "—":
                self.tree.item(item, tags=('notset',))
        
        self.tree.tag_configure('missing', foreground='orange')
        self.tree.tag_configure('notset', foreground='gray')
    
    def _open_selected_folder(self):
        """Open the selected sample's photo folder"""
        selection = self.tree.selection()
        
        if not selection:
            messagebox.showwarning("No Selection",
                                  "Please select a sample from the list")
            return
        
        # Get photo path
        item = selection[0]
        values = self.tree.item(item, 'values')
        photo_path = values[1]
        
        if photo_path == "(not set)" or not photo_path:
            messagebox.showinfo("No Photo Path",
                              "This sample has no photo path set.\n\n"
                              "Use 'Set Photo Path' to add one.")
            return
        
        # Open folder in OS file browser
        self._open_in_file_browser(photo_path)
    
    def _open_in_file_browser(self, path):
        """Open path in OS-specific file browser"""
        path_obj = Path(path)
        
        # If it's a file, open parent directory
        if path_obj.is_file():
            path_obj = path_obj.parent
        
        if not path_obj.exists():
            messagebox.showerror("Path Not Found",
                               f"The path does not exist:\n\n{path}\n\n"
                               "Please check the Photo_Path field.")
            return
        
        try:
            system = platform.system()
            
            if system == "Windows":
                subprocess.run(['explorer', str(path_obj)])
            elif system == "Darwin":  # macOS
                subprocess.run(['open', str(path_obj)])
            else:  # Linux and others
                subprocess.run(['xdg-open', str(path_obj)])
            
        except Exception as e:
            messagebox.showerror("Error Opening Folder",
                               f"Could not open folder:\n{e}")
    
    def _set_photo_path(self):
        """Set photo path for selected sample"""
        selection = self.tree.selection()
        
        if not selection:
            messagebox.showwarning("No Selection",
                                  "Please select a sample from the list")
            return
        
        # Get sample
        item = selection[0]
        values = self.tree.item(item, 'values')
        sample_id = values[0]
        
        # Find sample in data
        sample_index = None
        for i, sample in enumerate(self.app.samples):
            if sample.get('Sample_ID') == sample_id:
                sample_index = i
                break
        
        if sample_index is None:
            messagebox.showerror("Error", "Could not find sample in data")
            return
        
        # Ask for path
        path = filedialog.askdirectory(
            title=f"Select photo folder for {sample_id}",
            initialdir=Path.home()
        )
        
        if path:
            # Update sample
            self.app.samples[sample_index]['Photo_Path'] = path
            
            # Refresh tree
            self._populate_tree()
            
            # Refresh main app if it has a refresh method
            if hasattr(self.app, '_refresh_table_page'):
                self.app._refresh_table_page()
            
            messagebox.showinfo("Path Set",
                              f"Photo path set for {sample_id}:\n\n{path}")

def setup_plugin(main_app):
    """Plugin setup function"""
    plugin = PhotoManagerPlugin(main_app)
    return plugin
