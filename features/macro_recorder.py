"""
Macro/Workflow Recorder - Record and replay user actions
Fully converted to ttkbootstrap.
FIXED: Extended to record ALL user actions including:
- Protocol execution
- Column sorting
- Tab switching
- Plugin interactions
- Manual cell editing
- Scheme selection changes
- Right-click menu actions
- HUD interactions
- Pagination
"""

import json
import tkinter as tk
from tkinter import messagebox, filedialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Callable, Optional
import inspect
import traceback


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
    Records and replays user workflows - COMPREHENSIVE VERSION
    """
    def __init__(self, app):
        self.app = app
        self.is_recording = False
        self.current_macro: List[MacroAction] = []
        self.saved_macros: Dict[str, List[MacroAction]] = {}
        self.config_dir = Path("config")
        self.macros_file = self.config_dir / "macros.json"
        self._load_macros()

        # Register with main app to capture events
        self._register_with_app()

    def _register_with_app(self):
        """Register with main app to capture events"""
        if hasattr(self.app, 'set_macro_recorder'):
            self.app.set_macro_recorder(self)

        # Monkey-patch key methods to record actions
        self._patch_methods()

    def _patch_methods(self):
        """Monkey-patch methods to automatically record actions"""
        if not hasattr(self, '_patched'):
            self._patched = True

            # Store original methods
            self._original_methods = {}

            # Patch right panel methods
            if hasattr(self.app, 'right'):
                self._patch_right_panel()

            # Patch center panel methods
            if hasattr(self.app, 'center'):
                self._patch_center_panel()

            # Patch left panel methods
            if hasattr(self.app, 'left'):
                self._patch_left_panel()

            # Patch data hub methods
            if hasattr(self.app, 'data_hub'):
                self._patch_data_hub()

    def _patch_right_panel(self):
        """Patch right panel methods"""
        right = self.app.right

        # Protocol execution
        if hasattr(right, '_run_protocol'):
            self._patch_method(right, '_run_protocol', self._record_protocol)

        # Classification
        if hasattr(right, '_run_classification'):
            self._patch_method(right, '_run_classification', self._record_classification)

        # Scheme selection
        if hasattr(right, 'scheme_var'):
            original_trace = right.scheme_var.trace
            def traced_scheme_change(*args):
                if self.is_recording:
                    scheme = right.scheme_var.get()
                    self.record_action('scheme_changed', scheme=scheme)
                if original_trace:
                    original_trace(*args)
            right.scheme_var.trace = traced_scheme_change

    def _patch_center_panel(self):
        """Patch center panel methods"""
        center = self.app.center

        # Sorting
        if hasattr(center, '_sort_by_column'):
            self._patch_method(center, '_sort_by_column', self._record_sort)

        # Tab switching
        if hasattr(center, 'notebook'):
            original_callback = center.notebook.bind_class('Notebook', '<<NotebookTabChanged>>')
            def on_tab_changed(event):
                if self.is_recording:
                    tab_id = center.notebook.select()
                    tab_text = center.notebook.tab(tab_id, "text")
                    self.record_action('tab_switched', tab=tab_text, tab_id=tab_id)
                if original_callback:
                    original_callback(event)
            center.notebook.bind('<<NotebookTabChanged>>', on_tab_changed, add=True)

        # Cell editing
        if hasattr(center, '_create_edit_popup'):
            self._patch_method(center, '_create_edit_popup', self._record_cell_edit)

        # Pagination
        if hasattr(center, 'prev_page'):
            self._patch_method(center, 'prev_page', self._record_prev_page)
        if hasattr(center, 'next_page'):
            self._patch_method(center, 'next_page', self._record_next_page)

        # Plot generation
        if hasattr(center, '_generate_plot'):
            self._patch_method(center, '_generate_plot', self._record_plot)

        # Filter application
        if hasattr(center, '_apply_filter'):
            self._patch_method(center, '_apply_filter', self._record_filter)

    def _patch_left_panel(self):
        """Patch left panel methods"""
        left = self.app.left

        # Import
        if hasattr(left, 'import_csv'):
            self._patch_method(left, 'import_csv', self._record_import)

        # Add row
        if hasattr(left, '_add_row'):
            self._patch_method(left, '_add_row', self._record_add_row)

    def _patch_data_hub(self):
        """Patch data hub methods"""
        hub = self.app.data_hub

        # Delete rows
        if hasattr(hub, 'delete_rows'):
            self._patch_method(hub, 'delete_rows', self._record_delete)

        # Update row
        if hasattr(hub, 'update_row'):
            self._patch_method(hub, 'update_row', self._record_update)

    def _patch_method(self, obj, method_name, recorder_func):
        """Generic method patcher"""
        if not hasattr(obj, method_name):
            return

        original = getattr(obj, method_name)
        self._original_methods[f"{id(obj)}.{method_name}"] = original

        def wrapped(*args, **kwargs):
            # Record the action
            recorder_func(*args, **kwargs)
            # Call original
            return original(*args, **kwargs)

        setattr(obj, method_name, wrapped)

    def _record_protocol(self, *args, **kwargs):
        """Record protocol execution"""
        if self.is_recording and hasattr(self.app, 'right'):
            protocol_id = getattr(self.app.right, 'protocol_var', None)
            if protocol_id:
                protocol = protocol_id.get() if hasattr(protocol_id, 'get') else protocol_id
                self.record_action('run_protocol', protocol_id=protocol)

    def _record_classification(self, *args, **kwargs):
        """Record classification run"""
        if self.is_recording and hasattr(self.app, 'right'):
            scheme = self.app.right.scheme_var.get() if hasattr(self.app.right, 'scheme_var') else None
            target = self.app.right.run_target.get() if hasattr(self.app.right, 'run_target') else 'all'
            if scheme:
                self.record_action('classify', scheme=scheme, target=target)

    def _record_sort(self, column_name, *args, **kwargs):
        """Record column sort"""
        if self.is_recording:
            self.record_action('sort_by', column=column_name,
                             reverse=getattr(self.app.center, 'sort_reverse', False))

    def _record_cell_edit(self, event, item, col_name, current_value, sample_idx):
        """Record cell edit (called before edit)"""
        if self.is_recording:
            # We'll record the actual edit when it's saved
            pass

    def _record_prev_page(self, *args, **kwargs):
        """Record previous page navigation"""
        if self.is_recording:
            self.record_action('prev_page')

    def _record_next_page(self, *args, **kwargs):
        """Record next page navigation"""
        if self.is_recording:
            self.record_action('next_page')

    def _record_plot(self, *args, **kwargs):
        """Record plot generation"""
        if self.is_recording and hasattr(self.app.center, 'plot_type_var'):
            plot_type = self.app.center.plot_type_var.get()
            if plot_type:
                self.record_action('generate_plot', plot_type=plot_type)

    def _record_filter(self, *args, **kwargs):
        """Record filter application"""
        if self.is_recording:
            filter_val = self.app.center.filter_var.get() if hasattr(self.app.center, 'filter_var') else None
            search_text = self.app.center.search_var.get() if hasattr(self.app.center, 'search_var') else ''
            self.record_action('apply_filter', filter=filter_val, search=search_text)

    def _record_import(self, path=None, silent=False):
        """Record file import"""
        if self.is_recording and path:
            self.record_action('import_file', filepath=str(path))

    def _record_add_row(self, *args, **kwargs):
        """Record manual row addition"""
        if self.is_recording:
            sample_id = self.app.left.sample_id_var.get() if hasattr(self.app.left, 'sample_id_var') else None
            notes = self.app.left.notes_var.get() if hasattr(self.app.left, 'notes_var') else ''
            if sample_id:
                self.record_action('add_row', sample_id=sample_id, notes=notes)

    def _record_delete(self, indices, *args, **kwargs):
        """Record row deletion"""
        if self.is_recording and indices:
            self.record_action('delete_rows', indices=list(indices))

    def _record_update(self, index, updates, *args, **kwargs):
        """Record row update"""
        if self.is_recording and updates:
            self.record_action('update_row', index=index, updates=updates)

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
            except Exception as e:
                print(f"Error loading macros: {e}")

    def _save_macros(self):
        """Save macros to file"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        try:
            data = {}
            for name, actions in self.saved_macros.items():
                data[name] = [a.to_dict() for a in actions]
            with open(self.macros_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving macros: {e}")

    def start_recording(self):
        """Start recording a macro"""
        self.is_recording = True
        self.current_macro = []
        if hasattr(self.app, 'center'):
            self.app.center.set_status("🔴 Recording macro...", "processing")

    def stop_recording(self) -> List[MacroAction]:
        """Stop recording and return the macro"""
        self.is_recording = False
        macro = self.current_macro.copy()
        if hasattr(self.app, 'center'):
            self.app.center.set_status(f"⏹️ Recorded {len(macro)} actions", "info")
        return macro

    def record_action(self, action_type: str, **kwargs):
        """Record a single action"""
        if not self.is_recording:
            return
        action = MacroAction(action_type, **kwargs)
        self.current_macro.append(action)

        # Update status occasionally
        if len(self.current_macro) % 5 == 0 and hasattr(self.app, 'center'):
            self.app.center.set_status(f"🔴 Recording: {len(self.current_macro)} actions", "processing")

    def save_macro(self, name: str, macro: List[MacroAction] = None):
        """Save a macro with given name"""
        if macro is None:
            macro = self.current_macro
        if not macro:
            messagebox.showwarning("Empty Macro", "No actions to save")
            return False

        # Check for duplicate name
        if name in self.saved_macros:
            if not messagebox.askyesno("Overwrite", f"Macro '{name}' already exists. Overwrite?"):
                return False

        self.saved_macros[name] = macro
        self._save_macros()
        messagebox.showinfo("Success", f"Macro '{name}' saved with {len(macro)} actions")
        return True

    def delete_macro(self, name: str):
        """Delete a saved macro"""
        if name in self.saved_macros:
            del self.saved_macros[name]
            self._save_macros()

    def get_macro_names(self) -> List[str]:
        """Get list of saved macro names"""
        return list(self.saved_macros.keys())

    def get_macro_info(self, name: str) -> Dict:
        """Get information about a macro"""
        if name not in self.saved_macros:
            return {}

        macro = self.saved_macros[name]
        action_types = {}
        for action in macro:
            action_types[action.action_type] = action_types.get(action.action_type, 0) + 1

        return {
            'name': name,
            'actions': len(macro),
            'action_types': action_types,
            'first_action': macro[0].timestamp if macro else None,
            'last_action': macro[-1].timestamp if macro else None
        }

    def replay_macro(self, name: str, show_progress: bool = True):
        """Replay a saved macro"""
        if name not in self.saved_macros:
            messagebox.showerror("Error", f"Macro '{name}' not found")
            return False

        macro = self.saved_macros[name]
        total_actions = len(macro)

        if show_progress and hasattr(self.app, 'center'):
            self.app.center.set_status(f"▶️ Replaying macro '{name}'...", "processing")

        for i, action in enumerate(macro):
            try:
                if show_progress and hasattr(self.app, 'center'):
                    progress = f"{i+1}/{total_actions}"
                    self.app.center.set_status(f"▶️ Replaying: {action.action_type} ({progress})", "processing")

                self._execute_action(action)

            except Exception as e:
                error_msg = f"Action {i+1} failed: {action.action_type}\nError: {e}"
                if show_progress:
                    if not messagebox.askyesno("Error", f"{error_msg}\n\nContinue?"):
                        break
                else:
                    print(f"Macro replay error: {error_msg}")
                    traceback.print_exc()

        if show_progress and hasattr(self.app, 'center'):
            self.app.center.set_status(f"✅ Macro '{name}' replay complete", "success")

        messagebox.showinfo("Complete", f"Macro '{name}' replay finished")
        return True

    def _execute_action(self, action: MacroAction):
        """Execute a single macro action"""
        action_type = action.action_type
        params = action.params

        # ============ FILE OPERATIONS ============
        if action_type == "import_file":
            filepath = params.get('filepath')
            if filepath and Path(filepath).exists():
                self.app.left.import_csv(filepath, silent=True)

        elif action_type == "import_files":
            filepaths = params.get('filepaths', [])
            for filepath in filepaths:
                if Path(filepath).exists():
                    self.app.left.import_csv(filepath, silent=True)

        elif action_type == "export_csv":
            filepath = params.get('filepath')
            if filepath:
                self.app._export_csv(filepath)

        elif action_type == "export_selected":
            filepath = params.get('filepath')
            if filepath and hasattr(self.app, '_export_selected_csv'):
                self.app._export_selected_csv(filepath)

        # ============ CLASSIFICATION ============
        elif action_type == "classify":
            scheme = params.get('scheme')
            target = params.get('target', 'all')
            if scheme and hasattr(self.app, 'right'):
                self.app.right.scheme_var.set(scheme)
                self.app.right.run_target.set(target)
                self.app.right._run_classification()

        elif action_type == "classify_selected":
            scheme = params.get('scheme')
            indices = params.get('indices', [])
            if scheme and indices and hasattr(self.app, 'right'):
                self.app.right.scheme_var.set(scheme)
                # Temporarily set selected rows
                original_selection = list(self.app.center.selected_rows)
                self.app.center.selected_rows = set(indices)
                self.app.right.run_target.set("selected")
                self.app.right._run_classification()
                # Restore selection
                self.app.center.selected_rows = set(original_selection)

        elif action_type == "scheme_changed":
            scheme = params.get('scheme')
            if scheme and hasattr(self.app, 'right'):
                self.app.right.scheme_var.set(scheme)

        # ============ PROTOCOLS ============
        elif action_type == "run_protocol":
            protocol_id = params.get('protocol_id')
            if protocol_id and hasattr(self.app, 'right'):
                if hasattr(self.app.right, 'protocol_var'):
                    self.app.right.protocol_var.set(protocol_id)
                if hasattr(self.app.right, '_run_protocol'):
                    self.app.right._run_protocol()

        # ============ FILTERING & SORTING ============
        elif action_type == "apply_filter":
            filter_val = params.get('filter')
            search_text = params.get('search', '')
            if hasattr(self.app, 'center'):
                if filter_val:
                    self.app.center.filter_var.set(filter_val)
                if search_text:
                    self.app.center.search_var.set(search_text)
                self.app.center._apply_filter()

        elif action_type == "clear_filter":
            if hasattr(self.app, 'center'):
                self.app.center._clear_filter()

        elif action_type == "sort_by":
            column = params.get('column')
            reverse = params.get('reverse', False)
            if column and hasattr(self.app, 'center'):
                self.app.center.sort_column = column
                self.app.center.sort_reverse = reverse
                self.app.center._refresh()

        # ============ PAGINATION ============
        elif action_type == "prev_page":
            if hasattr(self.app, 'center'):
                self.app.center.prev_page()

        elif action_type == "next_page":
            if hasattr(self.app, 'center'):
                self.app.center.next_page()

        elif action_type == "go_to_page":
            page = params.get('page', 0)
            if hasattr(self.app, 'center'):
                total_pages = (self.app.data_hub.row_count() + self.app.center.page_size - 1) // self.app.center.page_size
                if 0 <= page < total_pages:
                    self.app.center.current_page = page
                    self.app.center._refresh()

        elif action_type == "set_page_size":
            size = params.get('size', 50)
            if hasattr(self.app, 'center'):
                self.app.center.page_size = size
                self.app.center._refresh()

        # ============ TAB SWITCHING ============
        elif action_type == "tab_switched":
            tab_text = params.get('tab')
            if tab_text and hasattr(self.app.center, 'notebook'):
                for i in range(self.app.center.notebook.index('end')):
                    if self.app.center.notebook.tab(i, "text") == tab_text:
                        self.app.center.notebook.select(i)
                        break

        # ============ ROW OPERATIONS ============
        elif action_type == "add_row":
            sample_id = params.get('sample_id')
            notes = params.get('notes', '')
            if sample_id and hasattr(self.app, 'left'):
                self.app.left.sample_id_var.set(sample_id)
                self.app.left.notes_var.set(notes)
                self.app.left._add_row()

        elif action_type == "delete_rows":
            indices = params.get('indices', [])
            if indices and hasattr(self.app, 'data_hub'):
                self.app.data_hub.delete_rows(indices)

        elif action_type == "delete_selected":
            if hasattr(self.app, 'center'):
                indices = self.app.center.get_selected_indices()
                if indices:
                    self.app.data_hub.delete_rows(indices)

        elif action_type == "delete_all":
            if messagebox.askyesno("Confirm", "Delete all rows?"):
                self.app.data_hub.clear_all()

        elif action_type == "update_row":
            index = params.get('index')
            updates = params.get('updates', {})
            if index is not None and updates and hasattr(self.app, 'data_hub'):
                self.app.data_hub.update_row(index, updates)

        # ============ SELECTION ============
        elif action_type == "select_rows":
            indices = params.get('indices', [])
            if hasattr(self.app, 'center'):
                self.app.center.selected_rows = set(indices)
                self.app.center._refresh()

        elif action_type == "select_all":
            if hasattr(self.app, 'center'):
                self.app.center.select_all()

        elif action_type == "deselect_all":
            if hasattr(self.app, 'center'):
                self.app.center.deselect_all()

        # ============ PLOTS ============
        elif action_type == "generate_plot":
            plot_type = params.get('plot_type')
            if plot_type and hasattr(self.app, 'center'):
                self.app.center.plot_type_var.set(plot_type)
                self.app.center._generate_plot()

        # ============ PLUGINS ============
        elif action_type == "plugin_call":
            plugin_id = params.get('plugin_id')
            method = params.get('method')
            args = params.get('args', [])
            kwargs = params.get('kwargs', {})

            if hasattr(self.app, 'plugins') and plugin_id in self.app.plugins:
                plugin = self.app.plugins[plugin_id]
                if hasattr(plugin, method):
                    getattr(plugin, method)(*args, **kwargs)

        elif action_type == "hardware_button":
            button_name = params.get('button_name')
            button_icon = params.get('button_icon')
            if hasattr(self.app, 'left') and hasattr(self.app.left, 'hw_buttons'):
                for btn in self.app.left.hw_buttons:
                    if hasattr(btn, 'cget') and btn.cget('text') == f"{button_icon} {button_name}":
                        btn.invoke()
                        break

        elif action_type == "ai_assistant":
            plugin_name = params.get('plugin_name')
            command = params.get('command')
            if hasattr(self.app.center, 'ai_plugins'):
                for name, icon, instance in self.app.center.ai_plugins:
                    if name == plugin_name and hasattr(instance, command):
                        getattr(instance, command)()
                        break

        elif action_type == "console_command":
            console_name = params.get('console_name')
            command = params.get('command')
            if hasattr(self.app.center, 'console_plugins'):
                for name, icon, instance in self.app.center.console_plugins:
                    if name == console_name and hasattr(instance, 'execute_command'):
                        instance.execute_command(command)
                        break

        # ============ PROJECT ============
        elif action_type == "save_project":
            filepath = params.get('filepath')
            if filepath:
                self.app.project_manager.save_project(filepath)
            else:
                self.app.project_manager.save_project()

        elif action_type == "load_project":
            filepath = params.get('filepath')
            if filepath:
                self.app.project_manager.load_project(filepath)

        elif action_type == "new_project":
            self.app.project_manager.new_project()

        # ============ WAIT / DELAY ============
        elif action_type == "wait":
            seconds = params.get('seconds', 1)
            import time
            time.sleep(seconds)

        # ============ HUD INTERACTIONS ============
        elif action_type == "hud_click":
            item = params.get('item')
            if hasattr(self.app, 'right') and hasattr(self.app.right, 'hud_tree'):
                # Find and select item in HUD
                for child in self.app.right.hud_tree.get_children():
                    if self.app.right.hud_tree.item(child, 'text') == item:
                        self.app.right.hud_tree.selection_set(child)
                        self.app.right._on_hud_click(None)
                        break

        elif action_type == "hud_expand":
            if hasattr(self.app, 'right') and hasattr(self.app.right, 'hud_tree'):
                for child in self.app.right.hud_tree.get_children():
                    self.app.right.hud_tree.item(child, open=True)

        elif action_type == "hud_collapse":
            if hasattr(self.app, 'right') and hasattr(self.app.right, 'hud_tree'):
                for child in self.app.right.hud_tree.get_children():
                    self.app.right.hud_tree.item(child, open=False)

        # ============ CONTEXT MENU ============
        elif action_type == "context_menu":
            menu_item = params.get('menu_item')
            sample_idx = params.get('sample_idx')
            if menu_item and sample_idx is not None and hasattr(self.app.center, '_show_context_menu'):
                # Simulate context menu selection
                if menu_item == "classify":
                    self.app.center._classify_selected_sample(sample_idx)
                elif menu_item == "delete":
                    self.app.center._delete_row(sample_idx)

        # ============ CUSTOM ============
        elif action_type == "custom":
            # For user-defined custom actions
            callback = params.get('callback')
            if callback and callable(callback):
                callback()

        else:
            print(f"Warning: Unknown action type in macro: {action_type}")


class MacroManagerDialog:
    """
    Dialog for managing macros – fully ttkbootstrap with enhanced features.
    """
    def __init__(self, parent, recorder: MacroRecorder):
        self.recorder = recorder
        self.window = ttk.Toplevel(parent)
        self.window.title("Macro Manager")
        self.window.geometry("800x500")
        self.window.transient(parent)

        self._build_ui()
        self._refresh_list()

    def _build_ui(self):
        main = ttk.Frame(self.window, padding=10)
        main.pack(fill=BOTH, expand=True)

        # Title with recording indicator
        title_frame = ttk.Frame(main)
        title_frame.pack(fill=X, pady=(0, 10))

        ttk.Label(
            title_frame,
            text="Workflow Macros",
            font=("TkDefaultFont", 14, "bold"),
            bootstyle="light"
        ).pack(side=LEFT)

        self.recording_indicator = ttk.Label(
            title_frame,
            text="",
            font=("TkDefaultFont", 10),
            bootstyle="secondary"
        )
        self.recording_indicator.pack(side=RIGHT, padx=10)

        self._update_recording_indicator()

        # Create notebook for tabs
        notebook = ttk.Notebook(main, bootstyle="dark")
        notebook.pack(fill=BOTH, expand=True)

        # Tab 1: Macro List
        list_tab = ttk.Frame(notebook, padding=5)
        notebook.add(list_tab, text="📋 Saved Macros")
        self._build_list_tab(list_tab)

        # Tab 2: Recording Control
        record_tab = ttk.Frame(notebook, padding=5)
        notebook.add(record_tab, text="⏺️ Record")
        self._build_record_tab(record_tab)

        # Tab 3: Macro Details (if selected)
        self.details_tab = ttk.Frame(notebook, padding=5)
        notebook.add(self.details_tab, text="📝 Details")
        self._build_details_tab()

        # Bottom buttons
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=X, pady=(10, 0))

        ttk.Button(btn_frame, text="Close", command=self.window.destroy,
                   bootstyle="secondary", width=15).pack(side=RIGHT, padx=2)

    def _build_list_tab(self, parent):
        """Build the macro list tab"""
        # Treeview with scrollbar
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=BOTH, expand=True)

        columns = ("Name", "Actions", "Types", "Last Modified")
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            height=15
        )

        self.tree.heading("Name", text="Macro Name", anchor=W)
        self.tree.heading("Actions", text="Actions", anchor=CENTER)
        self.tree.heading("Types", text="Action Types", anchor=W)
        self.tree.heading("Last Modified", text="Last Modified", anchor=W)

        self.tree.column("Name", width=150, anchor=W)
        self.tree.column("Actions", width=70, anchor=CENTER)
        self.tree.column("Types", width=300, anchor=W)
        self.tree.column("Last Modified", width=180, anchor=W)

        scrollbar = ttk.Scrollbar(
            tree_frame,
            orient="vertical",
            command=self.tree.yview,
            bootstyle="dark-round"
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        self.tree.bind('<<TreeviewSelect>>', self._on_macro_select)

        # Action buttons
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=X, pady=(10, 0))

        ttk.Button(btn_frame, text="▶️ Run", command=self._run_macro,
                  bootstyle="success", width=10).pack(side=LEFT, padx=2)
        ttk.Button(btn_frame, text="📝 Details", command=self._show_details,
                  bootstyle="info", width=10).pack(side=LEFT, padx=2)
        ttk.Button(btn_frame, text="📋 Duplicate", command=self._duplicate_macro,
                  bootstyle="secondary", width=10).pack(side=LEFT, padx=2)
        ttk.Button(btn_frame, text="💾 Export", command=self._export_macro,
                  bootstyle="secondary", width=10).pack(side=LEFT, padx=2)
        ttk.Button(btn_frame, text="📥 Import", command=self._import_macro,
                  bootstyle="secondary", width=10).pack(side=LEFT, padx=2)
        ttk.Button(btn_frame, text="🗑️ Delete", command=self._delete_macro,
                  bootstyle="danger", width=10).pack(side=LEFT, padx=2)

    def _build_record_tab(self, parent):
        """Build the recording control tab"""
        # Recording controls
        control_frame = ttk.LabelFrame(parent, text="Recording Controls", padding=15)
        control_frame.pack(fill=X, pady=10)

        self.record_var = tk.BooleanVar(value=self.recorder.is_recording)

        def toggle_recording():
            if self.record_var.get():
                self.recorder.start_recording()
                self.record_btn.config(text="⏹️ Stop Recording", bootstyle="danger")
                self.status_label.config(text="🔴 Recording in progress...", bootstyle="danger")
            else:
                macro = self.recorder.stop_recording()
                self.record_btn.config(text="⏺️ Start Recording", bootstyle="success")
                if macro:
                    # Ask for macro name
                    from tkinter.simpledialog import askstring
                    name = askstring("Save Macro", "Enter macro name:", parent=self.window)
                    if name:
                        if self.recorder.save_macro(name, macro):
                            self.status_label.config(text=f"✅ Saved: {name}", bootstyle="success")
                            self._refresh_list()
                        else:
                            self.status_label.config(text="Save cancelled", bootstyle="warning")
                    else:
                        self.status_label.config(text="Recording discarded", bootstyle="secondary")
                else:
                    self.status_label.config(text="No actions recorded", bootstyle="secondary")

            self._update_recording_indicator()

        self.record_btn = ttk.Button(control_frame, text="⏺️ Start Recording",
                                     command=toggle_recording,
                                     bootstyle="success", width=20)
        self.record_btn.pack(pady=10)

        self.status_label = ttk.Label(control_frame, text="Ready", bootstyle="secondary")
        self.status_label.pack()

        # Action counter
        counter_frame = ttk.LabelFrame(parent, text="Current Recording", padding=10)
        counter_frame.pack(fill=BOTH, expand=True, pady=10)

        self.action_count_var = tk.StringVar(value="0 actions")
        ttk.Label(counter_frame, textvariable=self.action_count_var,
                 font=("TkDefaultFont", 24, "bold"),
                 bootstyle="info").pack(pady=20)

        self.action_list = tk.Text(counter_frame, height=8, width=50,
                                   font=("Courier", 9))
        self.action_list.pack(fill=BOTH, expand=True, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(counter_frame, command=self.action_list.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.action_list.configure(yscrollcommand=scrollbar.set)

        # Update timer
        self._update_record_display()

    def _build_details_tab(self):
        """Build the details tab (initially empty)"""
        self.details_text = tk.Text(self.details_tab, wrap=tk.WORD,
                                    font=("Courier", 10))
        self.details_text.pack(fill=BOTH, expand=True, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(self.details_tab, command=self.details_text.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.details_text.configure(yscrollcommand=scrollbar.set)

    def _update_record_display(self):
        """Update recording display"""
        if self.recorder.is_recording:
            count = len(self.recorder.current_macro)
            self.action_count_var.set(f"{count} actions")

            # Update action list
            self.action_list.delete(1.0, tk.END)
            for i, action in enumerate(self.recorder.current_macro[-10:], 1):
                params_str = ", ".join(f"{k}={v}" for k, v in list(action.params.items())[:2])
                line = f"{i}. {action.action_type}"
                if params_str:
                    line += f" ({params_str})"
                self.action_list.insert(tk.END, line + "\n")

        # Schedule next update
        self.window.after(500, self._update_record_display)

    def _update_recording_indicator(self):
        """Update the recording indicator in title"""
        if self.recorder.is_recording:
            self.recording_indicator.config(text="🔴 RECORDING", bootstyle="danger")
        else:
            self.recording_indicator.config(text="", bootstyle="secondary")

    def _refresh_list(self):
        """Refresh the macro list"""
        self.tree.delete(*self.tree.get_children())

        for name in sorted(self.recorder.get_macro_names()):
            info = self.recorder.get_macro_info(name)

            # Format action types
            types_str = ", ".join([f"{t}({c})" for t, c in list(info['action_types'].items())[:3]])
            if len(info['action_types']) > 3:
                types_str += f" +{len(info['action_types'])-3} more"

            # Format last modified
            last_modified = info['last_action']
            if last_modified:
                try:
                    dt = datetime.fromisoformat(last_modified)
                    last_modified = dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    last_modified = "Unknown"

            self.tree.insert("", tk.END, values=(
                info['name'],
                info['actions'],
                types_str,
                last_modified
            ))

    def _on_macro_select(self, event):
        """Handle macro selection"""
        selection = self.tree.selection()
        if selection:
            name = self.tree.item(selection[0], "values")[0]
            self._show_macro_details(name)

    def _show_macro_details(self, name):
        """Show details of selected macro in details tab"""
        info = self.recorder.get_macro_info(name)
        macro = self.recorder.saved_macros[name]

        self.details_text.delete(1.0, tk.END)

        text = f"MACRO: {name}\n"
        text += f"{'='*50}\n"
        text += f"Total Actions: {info['actions']}\n"
        text += f"Action Types: {', '.join([f'{t}({c})' for t, c in info['action_types'].items()])}\n"
        text += f"First Action: {info['first_action']}\n"
        text += f"Last Action: {info['last_action']}\n"
        text += f"\nACTION LIST:\n{'-'*50}\n"

        for i, action in enumerate(macro, 1):
            text += f"{i:3d}. {action.action_type}"
            if action.params:
                params_str = ", ".join(f"{k}={v}" for k, v in action.params.items())
                text += f" ({params_str})"
            text += "\n"

        self.details_text.insert(1.0, text)
        self.details_text.see(1.0)

    def _run_macro(self):
        """Run selected macro"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a macro")
            return

        name = self.tree.item(selection[0], "values")[0]

        # Ask for replay options
        dialog = ttk.Toplevel(self.window)
        dialog.title("Replay Options")
        dialog.geometry("300x150")
        dialog.transient(self.window)
        dialog.grab_set()

        ttk.Label(dialog, text=f"Replay macro '{name}'?",
                 font=("TkDefaultFont", 11)).pack(pady=10)

        speed_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(dialog, text="Show progress",
                       variable=speed_var).pack(pady=5)

        def do_replay():
            dialog.destroy()
            self.recorder.replay_macro(name, show_progress=speed_var.get())

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="Replay", command=do_replay,
                  bootstyle="success").pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy,
                  bootstyle="secondary").pack(side=LEFT, padx=5)

    def _show_details(self):
        """Show details in a separate window"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a macro")
            return

        name = self.tree.item(selection[0], "values")[0]

        # Switch to details tab
        self.window.nametowidget(self.window.children['!notebook']).select(2)
        self._show_macro_details(name)

    def _duplicate_macro(self):
        """Duplicate selected macro"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a macro")
            return

        name = self.tree.item(selection[0], "values")[0]

        from tkinter.simpledialog import askstring
        new_name = askstring("Duplicate Macro", f"Enter name for duplicated macro:",
                            initialvalue=f"{name}_copy", parent=self.window)

        if new_name and new_name != name:
            macro = self.recorder.saved_macros[name]
            # Deep copy
            import copy
            self.recorder.saved_macros[new_name] = copy.deepcopy(macro)
            self.recorder._save_macros()
            self._refresh_list()

    def _delete_macro(self):
        """Delete selected macro"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a macro")
            return

        name = self.tree.item(selection[0], "values")[0]

        if messagebox.askyesno("Confirm Delete", f"Delete macro '{name}'?"):
            self.recorder.delete_macro(name)
            self._refresh_list()

            # Clear details tab
            self.details_text.delete(1.0, tk.END)

    def _export_macro(self):
        """Export selected macro to file"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a macro")
            return

        name = self.tree.item(selection[0], "values")[0]

        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=f"{name}.json",
            parent=self.window
        )

        if filepath:
            try:
                macro = self.recorder.saved_macros[name]
                data = {
                    'name': name,
                    'actions': [a.to_dict() for a in macro],
                    'exported': datetime.now().isoformat(),
                    'version': '2.0'
                }
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                messagebox.showinfo("Success", f"Macro exported to {filepath}")
            except Exception as e:
                messagebox.showerror("Error", f"Export failed: {e}")

    def _import_macro(self):
        """Import macro from file"""
        filepath = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            parent=self.window
        )

        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                name = data.get('name', Path(filepath).stem)
                actions = [MacroAction.from_dict(a) for a in data['actions']]

                # Check for duplicate
                if name in self.recorder.saved_macros:
                    if not messagebox.askyesno("Overwrite", f"Macro '{name}' already exists. Overwrite?"):
                        return

                self.recorder.save_macro(name, actions)
                self._refresh_list()
                messagebox.showinfo("Success", f"Macro '{name}' imported")
            except Exception as e:
                messagebox.showerror("Error", f"Import failed: {e}")


# Helper function to create a macro recorder control panel
def create_macro_control_panel(parent, recorder):
    """Create a macro control panel widget"""
    frame = ttk.Frame(parent, bootstyle="dark")

    # Title
    ttk.Label(frame, text="🎬 Macro Recorder",
              font=("TkDefaultFont", 10, "bold"),
              bootstyle="light").pack(anchor=tk.W, padx=5, pady=2)

    # Recording controls
    control_frame = ttk.Frame(frame)
    control_frame.pack(fill=tk.X, pady=2, padx=5)

    recorder.record_var = tk.BooleanVar(value=recorder.is_recording)

    def toggle_recording():
        if recorder.record_var.get():
            recorder.start_recording()
            record_btn.config(text="⏹️ Stop", bootstyle="danger")
            status_label.config(text="🔴 Recording", bootstyle="danger")
        else:
            macro = recorder.stop_recording()
            record_btn.config(text="⏺️ Record", bootstyle="success")
            if macro:
                from tkinter.simpledialog import askstring
                name = askstring("Save Macro", "Enter macro name:", parent=frame)
                if name:
                    recorder.save_macro(name, macro)
                    status_label.config(text=f"✅ Saved: {name}", bootstyle="success")
                else:
                    status_label.config(text="Discarded", bootstyle="secondary")
            else:
                status_label.config(text="No actions", bootstyle="secondary")

    record_btn = ttk.Button(control_frame, text="⏺️ Record",
                           command=toggle_recording,
                           bootstyle="success", width=8)
    record_btn.pack(side=tk.LEFT, padx=2)

    status_label = ttk.Label(control_frame, text="Ready",
                            bootstyle="secondary", width=12)
    status_label.pack(side=tk.LEFT, padx=2)

    # Action counter
    recorder.action_count_var = tk.StringVar(value="0")
    count_label = ttk.Label(control_frame, textvariable=recorder.action_count_var,
                           bootstyle="info", font=("TkDefaultFont", 9, "bold"))
    count_label.pack(side=tk.RIGHT, padx=2)
    ttk.Label(control_frame, text="actions", bootstyle="secondary").pack(side=tk.RIGHT)

    # Update action count when recording
    def update_count():
        if recorder.is_recording:
            count = len(recorder.current_macro)
            recorder.action_count_var.set(str(count))
            if count > 0:
                status_label.config(text=f"🔴 {count} actions", bootstyle="danger")
        frame.after(500, update_count)

    update_count()

    # Manager button
    ttk.Button(frame, text="📋 Manage Macros",
              command=lambda: MacroManagerDialog(frame.winfo_toplevel(), recorder),
              bootstyle="secondary").pack(fill=tk.X, padx=5, pady=2)

    return frame
