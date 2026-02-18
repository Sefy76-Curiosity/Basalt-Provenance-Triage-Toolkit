"""
Project Manager - Save and load entire project state
"""

import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

class ProjectManager:
    """
    Manages project save/load functionality
    """
    def __init__(self, app):
        self.app = app
        self.current_project_file = None
    
    def save_project(self, filepath: str = None) -> bool:
        """
        Save entire project state to file
        
        Includes:
        - All data samples
        - Current filters and view settings
        - Classification results
        - UI state (selected tab, etc.)
        """
        if filepath is None:
            filepath = filedialog.asksaveasfilename(
                defaultextension=".stproj",
                filetypes=[
                    ("Scientific Toolkit Project", "*.stproj"),
                    ("JSON files", "*.json"),
                    ("All files", "*.*")
                ],
                initialfile=f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}.stproj"
            )
        
        if not filepath:
            return False
        
        try:
            project_data = self._collect_project_data()
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=2)
            
            # Notify auto-save that manual save happened
            if hasattr(self.app, 'auto_save'):
                self.app.auto_save.manual_save_triggered()

            messagebox.showinfo("Success", f"Project saved to:\n{filepath}")
            return True
            
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save project:\n{e}")
            return False
    
    def load_project(self, filepath: str = None) -> bool:
        """
        Load project from file
        """
        if filepath is None:
            filepath = filedialog.askopenfilename(
                filetypes=[
                    ("Scientific Toolkit Project", "*.stproj"),
                    ("JSON files", "*.json"),
                    ("All files", "*.*")
                ]
            )
        
        if not filepath:
            return False
        
        if not Path(filepath).exists():
            messagebox.showerror("Error", f"File not found:\n{filepath}")
            return False
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
            
            self._restore_project_data(project_data)
            
            self.current_project_file = filepath
            messagebox.showinfo("Success", f"Project loaded from:\n{filepath}")
            return True
            
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load project:\n{e}")
            return False
    
    def _collect_project_data(self) -> Dict[str, Any]:
        """Collect all project data"""
        data = {
            'metadata': {
                'version': '2.0',
                'saved_at': datetime.now().isoformat(),
                'app_version': '2.0'
            },
            'data': {
                'samples': self.app.data_hub.get_all(),
                'column_order': self.app.data_hub.column_order.copy()
            },
            'ui_state': {},
            'settings': {}
        }
        
        # Collect UI state from center panel
        if hasattr(self.app, 'center'):
            data['ui_state']['center'] = {
                'current_page': self.app.center.current_page,
                'page_size': self.app.center.page_size,
                'search_text': self.app.center.search_var.get(),
                'filter_value': self.app.center.filter_var.get(),
                'selected_tab': self.app.center.notebook.index(
                    self.app.center.notebook.select()
                ) if self.app.center.notebook else 0
            }
        
        # Collect classification state from right panel
        if hasattr(self.app, 'right'):
            data['ui_state']['right'] = {
                'selected_scheme': self.app.right.scheme_var.get(),
                'run_target': self.app.right.run_target.get()
            }
        
        # Collect window geometry
        data['ui_state']['window'] = {
            'geometry': self.app.root.geometry()
        }
        
        return data
    
    def _restore_project_data(self, project_data: Dict[str, Any]):
        """Restore project data"""
        
        # Clear existing data
        self.app.data_hub.clear_all()
        
        # Restore samples
        data = project_data.get('data', {})
        samples = data.get('samples', [])
        if samples:
            self.app.data_hub.add_samples(samples)
        
        # Restore column order
        if 'column_order' in data:
            self.app.data_hub.column_order = data['column_order']
        
        # Restore UI state
        ui_state = project_data.get('ui_state', {})
        
        # Restore center panel state
        if 'center' in ui_state and hasattr(self.app, 'center'):
            center_state = ui_state['center']
            
            if 'search_text' in center_state:
                self.app.center.search_var.set(center_state['search_text'])
            
            if 'filter_value' in center_state:
                self.app.center.filter_var.set(center_state['filter_value'])
            
            if 'current_page' in center_state:
                self.app.center.current_page = center_state['current_page']
            
            if 'selected_tab' in center_state and self.app.center.notebook:
                try:
                    self.app.center.notebook.select(center_state['selected_tab'])
                except:
                    pass
        
        # Restore right panel state
        if 'right' in ui_state and hasattr(self.app, 'right'):
            right_state = ui_state['right']
            
            if 'selected_scheme' in right_state:
                self.app.right.scheme_var.set(right_state['selected_scheme'])
            
            if 'run_target' in right_state:
                self.app.right.run_target.set(right_state['run_target'])
        
        # Restore window geometry
        if 'window' in ui_state:
            window_state = ui_state['window']
            if 'geometry' in window_state:
                try:
                    self.app.root.geometry(window_state['geometry'])
                except:
                    pass
        
        # Refresh UI
        self.app.data_hub.notify_observers()
    
    def new_project(self):
        """Create a new project (clear everything)"""
        if self.app.data_hub.get_all():
            if not messagebox.askyesno("New Project", 
                "This will clear all current data. Continue?"):
                return False
        
        self.app.data_hub.clear_all()
        self.current_project_file = None
        
        # Reset UI state
        if hasattr(self.app, 'center'):
            self.app.center.search_var.set("")
            self.app.center.filter_var.set("All")
            self.app.center.current_page = 0
        
        if hasattr(self.app, 'right'):
            self.app.right.run_target.set("all")
        
        messagebox.showinfo("New Project", "New project created")
        return True
    
    def get_current_project_name(self) -> str:
        """Get current project filename"""
        if self.current_project_file:
            return Path(self.current_project_file).name
        return "Untitled Project"
