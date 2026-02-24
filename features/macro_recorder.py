"""
Macro/Workflow Recorder - Record and replay user actions
Fully converted to ttkbootstrap.
"""

import json
import tkinter as tk
from tkinter import messagebox, filedialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
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
        if self.macros_file.exists():
            try:
                with open(self.macros_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for name, actions in data.items():
                        self.saved_macros[name] = [
                            MacroAction.from_dict(a) for a in actions
                        ]
            except Exception as e:
                pass

    def _save_macros(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        try:
            data = {}
            for name, actions in self.saved_macros.items():
                data[name] = [a.to_dict() for a in actions]
            with open(self.macros_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            pass

    def start_recording(self):
        self.is_recording = True
        self.current_macro = []

    def stop_recording(self) -> List[MacroAction]:
        self.is_recording = False
        macro = self.current_macro.copy()
        return macro

    def record_action(self, action_type: str, **kwargs):
        if not self.is_recording:
            return
        action = MacroAction(action_type, **kwargs)
        self.current_macro.append(action)

    def save_macro(self, name: str, macro: List[MacroAction] = None):
        if macro is None:
            macro = self.current_macro
        if not macro:
            messagebox.showwarning("Empty Macro", "No actions to save")
            return
        self.saved_macros[name] = macro
        self._save_macros()
        messagebox.showinfo("Success", f"Macro '{name}' saved with {len(macro)} actions")

    def delete_macro(self, name: str):
        if name in self.saved_macros:
            del self.saved_macros[name]
            self._save_macros()

    def get_macro_names(self) -> List[str]:
        return list(self.saved_macros.keys())

    def replay_macro(self, name: str):
        if name not in self.saved_macros:
            messagebox.showerror("Error", f"Macro '{name}' not found")
            return
        self._execute_macro(self.saved_macros[name])

    def _execute_macro(self, macro: List[MacroAction]):
        for i, action in enumerate(macro):
            try:
                self._execute_action(action)
            except Exception as e:
                if not messagebox.askyesno("Error", f"Action {i+1} failed: {e}\n\nContinue?"):
                    break
        messagebox.showinfo("Complete", "Macro replay finished")

    def _execute_action(self, action: MacroAction):
        action_type = action.action_type
        params = action.params

        if action_type == "import_file":
            filepath = params.get('filepath')
            if filepath and Path(filepath).exists():
                self.app.left.import_csv(filepath)

        elif action_type == "classify":
            scheme = params.get('scheme')
            target = params.get('target', 'all')
            if scheme and hasattr(self.app, 'right'):
                self.app.right.scheme_var.set(scheme)
                self.app.right.run_target.set(target)
                self.app.right._run_classification()

        elif action_type == "export_csv":
            filepath = params.get('filepath')
            if filepath:
                self.app._export_csv(filepath)

        elif action_type == "apply_filter":
            filter_val = params.get('filter')
            search_text = params.get('search', '')
            if hasattr(self.app, 'center'):
                if filter_val:
                    self.app.center.filter_var.set(filter_val)
                if search_text:
                    self.app.center.search_var.set(search_text)
                self.app.center._apply_filter()

        elif action_type == "delete_selected":
            if hasattr(self.app, 'center'):
                indices = self.app.center.get_selected_indices()
                if indices:
                    self.app.data_hub.delete_rows(indices)

        elif action_type == "generate_plot":
            plot_type = params.get('plot_type')
            if plot_type and hasattr(self.app, 'center'):
                self.app.center.plot_type_var.set(plot_type)
                self.app.center._generate_plot()

        elif action_type == "add_row":
            sample_id = params.get('sample_id')
            notes = params.get('notes', '')
            if sample_id and hasattr(self.app, 'left'):
                self.app.left.sample_id_var.set(sample_id)
                self.app.left.notes_var.set(notes)
                self.app.left._add_row()

        else:
            pass  # Unknown action type - silently skip


class MacroManagerDialog:
    """
    Dialog for managing macros – fully ttkbootstrap.
    """
    def __init__(self, parent, recorder: MacroRecorder):
        self.recorder = recorder
        self.window = ttk.Toplevel(parent)
        self.window.title("Macro Manager")
        self.window.geometry("600x400")
        self.window.transient(parent)

        self._build_ui()
        self._refresh_list()

    def _build_ui(self):
        main = ttk.Frame(self.window, padding=10)
        main.pack(fill=BOTH, expand=True)

        ttk.Label(
            main,
            text="Workflow Macros",
            font=("TkDefaultFont", 14, "bold"),
            bootstyle="light"
        ).pack(pady=(0, 10))

        # List frame
        list_frame = ttk.Frame(main)
        list_frame.pack(fill=BOTH, expand=True)

        columns = ("Name", "Actions", "Last Modified")
        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            height=12
        )

        self.tree.heading("Name", text="Macro Name", anchor=W)
        self.tree.heading("Actions", text="Actions", anchor=CENTER)
        self.tree.heading("Last Modified", text="Last Modified", anchor=W)

        self.tree.column("Name", width=200, anchor=W)
        self.tree.column("Actions", width=100, anchor=CENTER)
        self.tree.column("Last Modified", width=200, anchor=W)

        scrollbar = ttk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self.tree.yview,
            bootstyle="dark-round"
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        # Buttons
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=X, pady=(10, 0))

        ttk.Button(btn_frame, text="▶️ Run",     command=self._run_macro,     bootstyle="primary").pack(side=LEFT, padx=2)
        ttk.Button(btn_frame, text="📝 Details", command=self._show_details,  bootstyle="secondary").pack(side=LEFT, padx=2)
        ttk.Button(btn_frame, text="💾 Export",  command=self._export_macro,  bootstyle="secondary").pack(side=LEFT, padx=2)
        ttk.Button(btn_frame, text="📥 Import",  command=self._import_macro,  bootstyle="secondary").pack(side=LEFT, padx=2)
        ttk.Button(btn_frame, text="🗑️ Delete", command=self._delete_macro,  bootstyle="danger").pack(side=LEFT, padx=2)

        ttk.Button(main, text="Close", command=self.window.destroy,
                   bootstyle="secondary", width=10).pack(pady=(10, 0))

    def _refresh_list(self):
        self.tree.delete(*self.tree.get_children())
        for name in self.recorder.get_macro_names():
            macro = self.recorder.saved_macros[name]
            last_modified = macro[-1].timestamp if macro else "Unknown"
            self.tree.insert("", tk.END, values=(name, len(macro), last_modified))

    def _run_macro(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a macro")
            return
        name = self.tree.item(selection[0], "values")[0]
        self.recorder.replay_macro(name)

    def _show_details(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a macro")
            return
        name = self.tree.item(selection[0], "values")[0]
        macro = self.recorder.saved_macros[name]

        details = f"Macro: {name}\nActions: {len(macro)}\n\nSteps:\n"
        for i, action in enumerate(macro):
            details += f"{i+1}. {action.action_type}"
            if action.params:
                details += f" ({', '.join(f'{k}={v}' for k, v in action.params.items())})"
            details += "\n"
        messagebox.showinfo("Macro Details", details)

    def _delete_macro(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a macro")
            return
        name = self.tree.item(selection[0], "values")[0]
        if messagebox.askyesno("Confirm Delete", f"Delete macro '{name}'?"):
            self.recorder.delete_macro(name)
            self._refresh_list()

    def _export_macro(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a macro")
            return
        name = self.tree.item(selection[0], "values")[0]

        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=f"{name}.json"
        )
        if filepath:
            try:
                macro = self.recorder.saved_macros[name]
                data = {'name': name, 'actions': [a.to_dict() for a in macro]}
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                messagebox.showinfo("Success", f"Macro exported to {filepath}")
            except Exception as e:
                messagebox.showerror("Error", f"Export failed: {e}")

    def _import_macro(self):
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
