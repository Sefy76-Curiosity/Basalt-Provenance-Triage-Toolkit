"""
Macro/Workflow Recorder - Record and replay user actions
"""

import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Callable

class MacroAction:
    """Represents a single macro action"""
    def __init__(self, action_type: str, **kwargs):
        self.action_type = action_type
        self.params = kwargs
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        return {
            'type': self.action_type,
            'params': self.params,
            'timestamp': self.timestamp
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'MacroAction':
        action = MacroAction(data['type'], **data.get('params', {}))
        action.timestamp = data.get('timestamp', datetime.now().isoformat())
        return action


class MacroRecorder:
    """
    Records and replays user workflows
    """
    def __init__(self, app):
        self.app = app
        self.is_recording = False
        self.current_macro: List[MacroAction] = []
        self.saved_macros: Dict[str, List[MacroAction]] = {}
        self.config_dir = Path("config")
        self.macros_file = self.config_dir / "macros.json"
        self._load_macros()
    
    def _load_macros(self):
        """Load saved macros from file"""
        if self.macros_file.exists():
            try:
                with open(self.macros_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for name, actions in data.items():
                        self.saved_macros[name] = [
                            MacroAction.from_dict(a) for a in actions
                        ]
                print(f"✅ Loaded {len(self.saved_macros)} macros")
            except Exception as e:
                print(f"⚠️ Error loading macros: {e}")
    
    def _save_macros(self):
        """Save macros to file"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        try:
            data = {}
            for name, actions in self.saved_macros.items():
                data[name] = [a.to_dict() for a in actions]
            
            with open(self.macros_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            print(f"✅ Saved {len(self.saved_macros)} macros")
        except Exception as e:
            print(f"⚠️ Error saving macros: {e}")
    
    def start_recording(self):
        """Start recording a new macro"""
        self.is_recording = True
        self.current_macro = []
        print("🔴 Recording macro...")
    
    def stop_recording(self) -> List[MacroAction]:
        """Stop recording and return the macro"""
        self.is_recording = False
        macro = self.current_macro.copy()
        print(f"⏸️ Recording stopped. {len(macro)} actions recorded.")
        return macro
    
    def record_action(self, action_type: str, **kwargs):
        """Record a single action"""
        if not self.is_recording:
            return
        
        action = MacroAction(action_type, **kwargs)
        self.current_macro.append(action)
        print(f"  📝 Recorded: {action_type} - {kwargs}")
    
    def save_macro(self, name: str, macro: List[MacroAction] = None):
        """Save a macro with a name"""
        if macro is None:
            macro = self.current_macro
        
        if not macro:
            messagebox.showwarning("Empty Macro", "No actions to save")
            return
        
        self.saved_macros[name] = macro
        self._save_macros()
        messagebox.showinfo("Success", f"Macro '{name}' saved with {len(macro)} actions")
    
    def delete_macro(self, name: str):
        """Delete a saved macro"""
        if name in self.saved_macros:
            del self.saved_macros[name]
            self._save_macros()
    
    def get_macro_names(self) -> List[str]:
        """Get list of saved macro names"""
        return list(self.saved_macros.keys())
    
    def replay_macro(self, name: str):
        """Replay a saved macro"""
        if name not in self.saved_macros:
            messagebox.showerror("Error", f"Macro '{name}' not found")
            return
        
        macro = self.saved_macros[name]
        self._execute_macro(macro)
    
    def _execute_macro(self, macro: List[MacroAction]):
        """Execute a macro (replay actions)"""
        print(f"▶️ Replaying macro with {len(macro)} actions...")
        
        for i, action in enumerate(macro):
            try:
                self._execute_action(action)
                print(f"  ✓ Action {i+1}/{len(macro)}: {action.action_type}")
            except Exception as e:
                print(f"  ✗ Action {i+1}/{len(macro)} failed: {e}")
                if not messagebox.askyesno("Error", 
                    f"Action {i+1} failed: {e}\n\nContinue?"):
                    break
        
        print("✅ Macro replay complete")
        messagebox.showinfo("Complete", f"Macro replay finished")
    
    def _execute_action(self, action: MacroAction):
        """Execute a single action"""
        action_type = action.action_type
        params = action.params
        
        # Import data
        if action_type == "import_file":
            filepath = params.get('filepath')
            if filepath and Path(filepath).exists():
                self.app.left.import_csv(filepath)
        
        # Classification
        elif action_type == "classify":
            scheme = params.get('scheme')
            target = params.get('target', 'all')
            if scheme and hasattr(self.app, 'right'):
                self.app.right.scheme_var.set(scheme)
                self.app.right.run_target.set(target)
                self.app.right._run_classification()
        
        # Export data
        elif action_type == "export_csv":
            filepath = params.get('filepath')
            if filepath:
                self.app._export_csv(filepath)
        
        # Apply filter
        elif action_type == "apply_filter":
            filter_val = params.get('filter')
            search_text = params.get('search', '')
            if hasattr(self.app, 'center'):
                if filter_val:
                    self.app.center.filter_var.set(filter_val)
                if search_text:
                    self.app.center.search_var.set(search_text)
                self.app.center._apply_filter()
        
        # Delete rows
        elif action_type == "delete_selected":
            if hasattr(self.app, 'center'):
                indices = self.app.center.get_selected_indices()
                if indices:
                    self.app.data_hub.delete_rows(indices)
        
        # Plot generation
        elif action_type == "generate_plot":
            plot_type = params.get('plot_type')
            if plot_type and hasattr(self.app, 'center'):
                self.app.center.plot_type_var.set(plot_type)
                self.app.center._generate_plot()
        
        # Add manual row
        elif action_type == "add_row":
            sample_id = params.get('sample_id')
            notes = params.get('notes', '')
            if sample_id and hasattr(self.app, 'left'):
                self.app.left.sample_id_var.set(sample_id)
                self.app.left.notes_var.set(notes)
                self.app.left._add_row()
        
        else:
            print(f"⚠️ Unknown action type: {action_type}")


class MacroManagerDialog:
    """
    Dialog for managing macros
    """
    def __init__(self, parent, recorder: MacroRecorder):
        self.recorder = recorder
        self.window = tk.Toplevel(parent)
        self.window.title("Macro Manager")
        self.window.geometry("600x400")
        self.window.transient(parent)
        
        self._build_ui()
        self._refresh_list()
    
    def _build_ui(self):
        """Build the UI"""
        main = ttk.Frame(self.window, padding=10)
        main.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(main, text="Workflow Macros", 
                 font=("TkDefaultFont", 14, "bold")).pack(pady=(0, 10))
        
        # List frame
        list_frame = ttk.Frame(main)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview
        columns = ("Name", "Actions", "Last Modified")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=12)
        
        self.tree.heading("Name", text="Macro Name")
        self.tree.heading("Actions", text="Actions")
        self.tree.heading("Last Modified", text="Last Modified")
        
        self.tree.column("Name", width=200)
        self.tree.column("Actions", width=100, anchor="center")
        self.tree.column("Last Modified", width=200)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(btn_frame, text="▶️ Run", command=self._run_macro).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="📝 Details", command=self._show_details).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="💾 Export", command=self._export_macro).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="📥 Import", command=self._import_macro).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="🗑️ Delete", command=self._delete_macro).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(main, text="Close", command=self.window.destroy).pack(pady=(10, 0))
    
    def _refresh_list(self):
        """Refresh the macro list"""
        self.tree.delete(*self.tree.get_children())
        
        for name in self.recorder.get_macro_names():
            macro = self.recorder.saved_macros[name]
            last_modified = macro[-1].timestamp if macro else "Unknown"
            self.tree.insert("", tk.END, values=(name, len(macro), last_modified))
    
    def _run_macro(self):
        """Run selected macro"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a macro")
            return
        
        values = self.tree.item(selection[0], "values")
        name = values[0]
        self.recorder.replay_macro(name)
    
    def _show_details(self):
        """Show macro details"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a macro")
            return
        
        values = self.tree.item(selection[0], "values")
        name = values[0]
        macro = self.recorder.saved_macros[name]
        
        details = f"Macro: {name}\n"
        details += f"Actions: {len(macro)}\n\n"
        details += "Steps:\n"
        
        for i, action in enumerate(macro):
            details += f"{i+1}. {action.action_type}"
            if action.params:
                details += f" ({', '.join(f'{k}={v}' for k, v in action.params.items())})"
            details += "\n"
        
        messagebox.showinfo("Macro Details", details)
    
    def _delete_macro(self):
        """Delete selected macro"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a macro")
            return
        
        values = self.tree.item(selection[0], "values")
        name = values[0]
        
        if messagebox.askyesno("Confirm Delete", f"Delete macro '{name}'?"):
            self.recorder.delete_macro(name)
            self._refresh_list()
    
    def _export_macro(self):
        """Export macro to file"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a macro")
            return
        
        values = self.tree.item(selection[0], "values")
        name = values[0]
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=f"{name}.json"
        )
        
        if filepath:
            try:
                macro = self.recorder.saved_macros[name]
                data = {
                    'name': name,
                    'actions': [a.to_dict() for a in macro]
                }
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                messagebox.showinfo("Success", f"Macro exported to {filepath}")
            except Exception as e:
                messagebox.showerror("Error", f"Export failed: {e}")
    
    def _import_macro(self):
        """Import macro from file"""
        filepath = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                name = data.get('name', Path(filepath).stem)
                actions = [MacroAction.from_dict(a) for a in data['actions']]
                
                self.recorder.save_macro(name, actions)
                self._refresh_list()
                messagebox.showinfo("Success", f"Macro '{name}' imported")
            except Exception as e:
                messagebox.showerror("Error", f"Import failed: {e}")
