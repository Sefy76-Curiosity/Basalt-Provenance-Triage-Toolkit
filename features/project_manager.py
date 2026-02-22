"""
Project Manager - Save and load entire project state
Fully converted to ttkbootstrap with dark theme consistency
"""

import json
import tkinter as tk
from tkinter import messagebox, filedialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
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

            # Use ttkbootstrap style messagebox (tkinter messagebox doesn't support theming)
            messagebox.showinfo("✅ Success", f"Project saved to:\n{filepath}")
            return True

        except Exception as e:
            messagebox.showerror("❌ Save Error", f"Failed to save project:\n{e}")
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
            messagebox.showerror("❌ Error", f"File not found:\n{filepath}")
            return False

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                project_data = json.load(f)

            self._restore_project_data(project_data)

            self.current_project_file = filepath
            messagebox.showinfo("✅ Success", f"Project loaded from:\n{filepath}")
            return True

        except Exception as e:
            messagebox.showerror("❌ Load Error", f"Failed to load project:\n{e}")
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
            if not messagebox.askyesno("🆕 New Project",
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

        messagebox.showinfo("✅ New Project", "New project created")
        return True

    def get_current_project_name(self) -> str:
        """Get current project filename"""
        if self.current_project_file:
            return Path(self.current_project_file).name
        return "Untitled Project"


class ProjectDialog:
    """
    Project management dialog for creating/loading/saving projects
    """
    def __init__(self, parent, project_manager):
        self.project_manager = project_manager
        self.app = project_manager.app
        self.window = ttk.Toplevel(parent)
        self.window.title("📁 Project Manager")
        self.window.geometry("500x400")
        self.window.transient(parent)
        self.window.grab_set()

        self._build_ui()
        self._center_window()

    def _center_window(self):
        """Center the window on screen"""
        self.window.update_idletasks()
        w = self.window.winfo_width()
        h = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (w // 2)
        y = (self.window.winfo_screenheight() // 2) - (h // 2)
        self.window.geometry(f"+{x}+{y}")

    def _build_ui(self):
        """Build the project management UI"""
        # Main container
        main = ttk.Frame(self.window, padding=20)
        main.pack(fill=BOTH, expand=True)

        # Title
        ttk.Label(main, text="Project Manager",
                 font=("TkDefaultFont", 16, "bold")).pack(pady=(0, 20))

        # Current project info
        info_frame = ttk.LabelFrame(main, text="Current Project", padding=10)
        info_frame.pack(fill=X, pady=(0, 20))

        current_name = self.project_manager.get_current_project_name()
        ttk.Label(info_frame, text=f"Project: {current_name}",
                 font=("TkDefaultFont", 11)).pack(anchor=W)

        if self.project_manager.current_project_file:
            ttk.Label(info_frame,
                     text=f"Location: {self.project_manager.current_project_file}",
                     bootstyle="secondary",
                     wraplength=400).pack(anchor=W, pady=(5, 0))

        # Action buttons
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=X, pady=10)

        # New Project
        new_btn = ttk.Button(btn_frame, text="🆕 New Project",
                            command=self._new_project,
                            bootstyle="info-outline", width=20)
        new_btn.pack(pady=5, fill=X)

        # Open Project
        open_btn = ttk.Button(btn_frame, text="📂 Open Project",
                             command=self._open_project,
                             bootstyle="primary-outline", width=20)
        open_btn.pack(pady=5, fill=X)

        # Save Project
        save_btn = ttk.Button(btn_frame, text="💾 Save Project",
                             command=self._save_project,
                             bootstyle="success-outline", width=20)
        save_btn.pack(pady=5, fill=X)

        # Save As
        saveas_btn = ttk.Button(btn_frame, text="💾 Save Project As...",
                               command=self._save_project_as,
                               bootstyle="warning-outline", width=20)
        saveas_btn.pack(pady=5, fill=X)

        # Recent projects (if implemented)
        recent_frame = ttk.LabelFrame(main, text="Recent Projects", padding=10)
        recent_frame.pack(fill=BOTH, expand=True, pady=(20, 10))

        # Placeholder for recent projects list
        ttk.Label(recent_frame,
                 text="Recent projects will appear here",
                 bootstyle="secondary").pack(expand=True)

        # Close button
        ttk.Button(main, text="Close", command=self.window.destroy,
                  bootstyle="secondary", width=15).pack(pady=(10, 0))

    def _new_project(self):
        """Create a new project"""
        if self.project_manager.new_project():
            self.window.destroy()

    def _open_project(self):
        """Open a project"""
        if self.project_manager.load_project():
            self.window.destroy()

    def _save_project(self):
        """Save current project"""
        if self.project_manager.current_project_file:
            if self.project_manager.save_project(self.project_manager.current_project_file):
                self.window.destroy()
        else:
            self._save_project_as()

    def _save_project_as(self):
        """Save project with new filename"""
        if self.project_manager.save_project():
            self.window.destroy()


class ProjectInfoBar(ttk.Frame):
    """
    Project information bar for main window status area
    """
    def __init__(self, master, project_manager, **kwargs):
        super().__init__(master, **kwargs)
        self.project_manager = project_manager

        self._build_ui()
        self._update_display()

    def _build_ui(self):
        """Build the info bar UI"""
        # Project icon
        ttk.Label(self, text="📁", font=("TkDefaultFont", 12)).pack(side=LEFT, padx=(5, 2))

        # Project name
        self.name_label = ttk.Label(self, text="", font=("TkDefaultFont", 10, "bold"))
        self.name_label.pack(side=LEFT, padx=2)

        # Save indicator (if unsaved changes)
        self.save_indicator = ttk.Label(self, text="", font=("TkDefaultFont", 12))
        self.save_indicator.pack(side=LEFT, padx=2)

        # Project buttons
        ttk.Button(self, text="Save", command=self._quick_save,
                  bootstyle="success-link", width=6).pack(side=LEFT, padx=5)

        ttk.Button(self, text="Open", command=self._open_project_dialog,
                  bootstyle="primary-link", width=6).pack(side=LEFT, padx=2)

        ttk.Button(self, text="Manage", command=self._open_project_dialog,
                  bootstyle="info-link", width=8).pack(side=LEFT, padx=2)

    def _quick_save(self):
        """Quick save current project"""
        if self.project_manager.current_project_file:
            self.project_manager.save_project(self.project_manager.current_project_file)
        else:
            self.project_manager.save_project()
        self._update_display()

    def _open_project_dialog(self):
        """Open the full project manager dialog"""
        ProjectDialog(self, self.project_manager)

    def _update_display(self):
        """Update the display with current project info"""
        name = self.project_manager.get_current_project_name()
        self.name_label.config(text=name)

        # Check for unsaved changes
        if hasattr(self.project_manager.app, 'data_hub'):
            if self.project_manager.app.data_hub.has_unsaved_changes():
                self.save_indicator.config(text="●", bootstyle="danger")
            else:
                self.save_indicator.config(text="○", bootstyle="secondary")

        # Schedule next update
        self.after(1000, self._update_display)
