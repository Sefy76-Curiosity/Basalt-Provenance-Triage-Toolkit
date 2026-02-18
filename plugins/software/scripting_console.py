"""
Scripting Console Plugin v1.0 - Python Console & Scripting Environment
FOR SCIENTIFIC TOOLKIT:

FEATURES:
✓ Interactive Python console with full access to app
✓ Script editor with syntax highlighting
✓ Command history (↑/↓ arrows)
✓ Variable inspector
✓ Batch processing
✓ Macro recording
✓ Export/import scripts
✓ Auto-completion (basic)
"""

PLUGIN_INFO = {
    "category": "software",
    "id": "scripting_console",
    "name": "Python Console",
    "description": "Interactive Python console, script editor, batch processing",
    "icon": "🐍",
    "version": "1.0.0",
    "requires": ["tkinter"],
    "author": "Scientific Toolkit"
}

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys
import io
import code
import traceback
from datetime import datetime
import json
from pathlib import Path
import builtins

class ScriptingConsolePlugin:
    """
    Python Console & Scripting Environment

    Provides:
    - Interactive Python console with access to 'app' (main app instance)
    - Script editor with syntax highlighting
    - Command history
    - Variable inspector
    - Macro recorder
    - Batch processor
    """

    def __init__(self, main_app):
        self.app = main_app
        self.window = None

        # Console state
        self.history = []
        self.history_index = -1
        self.locals = {
            'app': self.app,
            'data_hub': self.app.data_hub,
            'samples': self.app.samples,
            'np': __import__('numpy'),
            'pd': __import__('pandas'),
            'plt': __import__('matplotlib.pyplot'),
            'datetime': datetime,
            'print': print,
            'len': len,
            'type': type,
            'dir': dir,
            'help': help
        }

        # Macro recording
        self.recording = False
        self.recorded_commands = []
        self.macros = {}

        # Console output redirection
        self.stdout = io.StringIO()
        self.stderr = io.StringIO()

    def open_window(self):
        """Open the scripting console"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("🐍 Python Console - Scientific Toolkit")
        self.window.geometry("1000x700")

        self._create_interface()
        self._update_locals()
        self.window.transient(self.app.root)

    def _create_interface(self):
        """Create the console interface"""
        # Main paned window
        main_pane = ttk.PanedWindow(self.window, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left panel - Console + Editor
        left = ttk.Frame(main_pane)
        main_pane.add(left, weight=3)

        # Right panel - Variable Inspector + Macros
        right = ttk.Frame(main_pane, width=300)
        main_pane.add(right, weight=1)

        # ========== LEFT PANEL ==========
        # Notebook for Console/Editor
        notebook = ttk.Notebook(left)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Interactive Console
        console_tab = ttk.Frame(notebook)
        notebook.add(console_tab, text="💬 Console")
        self._build_console_tab(console_tab)

        # Tab 2: Script Editor
        editor_tab = ttk.Frame(notebook)
        notebook.add(editor_tab, text="📝 Script Editor")
        self._build_editor_tab(editor_tab)

        # Tab 3: Batch Processing
        batch_tab = ttk.Frame(notebook)
        notebook.add(batch_tab, text="⚡ Batch Process")
        self._build_batch_tab(batch_tab)

        # ========== RIGHT PANEL ==========
        # Variable Inspector
        var_frame = ttk.LabelFrame(right, text="📊 Variable Inspector", padding=5)
        var_frame.pack(fill=tk.BOTH, expand=True, pady=(0,5))

        self.var_tree = ttk.Treeview(var_frame, columns=('type', 'value'), show='tree headings', height=15)
        self.var_tree.heading('#0', text='Variable')
        self.var_tree.heading('type', text='Type')
        self.var_tree.heading('value', text='Value')
        self.var_tree.column('#0', width=120)
        self.var_tree.column('type', width=80)
        self.var_tree.column('value', width=100)

        vsb = ttk.Scrollbar(var_frame, orient="vertical", command=self.var_tree.yview)
        self.var_tree.configure(yscrollcommand=vsb.set)

        self.var_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Button(var_frame, text="🔄 Refresh", command=self._update_var_inspector).pack(pady=2)

        # Macro Recorder
        macro_frame = ttk.LabelFrame(right, text="🎬 Macro Recorder", padding=5)
        macro_frame.pack(fill=tk.X, pady=5)

        self.rec_btn = ttk.Button(macro_frame, text="⏺ Record", command=self._toggle_recording)
        self.rec_btn.pack(fill=tk.X, pady=2)

        self.macro_list = tk.Listbox(macro_frame, height=5)
        self.macro_list.pack(fill=tk.X, pady=2)

        btn_frame = ttk.Frame(macro_frame)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="▶ Run", command=self._run_macro).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        ttk.Button(btn_frame, text="💾 Save", command=self._save_macro).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        ttk.Button(btn_frame, text="🗑️ Delete", command=self._delete_macro).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)

        # Load saved macros
        self._load_macros()

        # Status bar
        status = ttk.Frame(self.window)
        status.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(status, textvariable=self.status_var).pack(side=tk.LEFT, padx=5)

    def _build_console_tab(self, parent):
        """Build interactive console tab"""
        # Output area
        output_frame = ttk.Frame(parent)
        output_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.output_text = tk.Text(output_frame, wrap=tk.WORD, font=("Courier", 10),
                                   bg="#1e1e1e", fg="#d4d4d4", height=15)
        output_scroll = ttk.Scrollbar(output_frame, command=self.output_text.yview)
        self.output_text.configure(yscrollcommand=output_scroll.set)

        self.output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        output_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Configure tags for colors
        self.output_text.tag_configure("prompt", foreground="#569cd6")
        self.output_text.tag_configure("output", foreground="#d4d4d4")
        self.output_text.tag_configure("error", foreground="#f48771")
        self.output_text.tag_configure("input", foreground="#9cdcfe")

        # Input area
        input_frame = ttk.Frame(parent)
        input_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(input_frame, text=">>>", font=("Courier", 10, "bold")).pack(side=tk.LEFT, padx=2)

        self.input_var = tk.StringVar()
        self.input_entry = ttk.Entry(input_frame, textvariable=self.input_var, font=("Courier", 10))
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.input_entry.bind("<Return>", self._execute_command)
        self.input_entry.bind("<Up>", self._history_up)
        self.input_entry.bind("<Down>", self._history_down)

        ttk.Button(input_frame, text="Run", command=lambda: self._execute_command()).pack(side=tk.RIGHT)

        # Toolbar
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, padx=5, pady=2)

        ttk.Button(toolbar, text="🧹 Clear", command=self._clear_console).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📋 Copy", command=self._copy_output).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="💾 Save Log", command=self._save_log).pack(side=tk.LEFT, padx=2)

        # Welcome message
        self._print_welcome()

    def _build_editor_tab(self, parent):
        """Build script editor tab"""
        # Editor area
        editor_frame = ttk.Frame(parent)
        editor_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Line numbers
        line_frame = ttk.Frame(editor_frame)
        line_frame.pack(side=tk.LEFT, fill=tk.Y)

        self.line_numbers = tk.Text(line_frame, width=4, padx=3, takefocus=0, border=0,
                                   background="#2d2d2d", foreground="#666666", state='disabled')
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)

        # Editor text
        self.editor_text = tk.Text(editor_frame, wrap=tk.NONE, font=("Courier", 10),
                                   bg="#1e1e1e", fg="#d4d4d4", undo=True)
        editor_scroll_y = ttk.Scrollbar(editor_frame, command=self.editor_text.yview)
        editor_scroll_x = ttk.Scrollbar(editor_frame, orient=tk.HORIZONTAL, command=self.editor_text.xview)
        self.editor_text.configure(yscrollcommand=editor_scroll_y.set, xscrollcommand=editor_scroll_x.set)

        self.editor_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        editor_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        editor_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        # Bind events for line numbers
        self.editor_text.bind('<KeyRelease>', self._update_line_numbers)
        self.editor_text.bind('<MouseWheel>', self._update_line_numbers)

        # Simple syntax highlighting tags
        self.editor_text.tag_configure("keyword", foreground="#569cd6")
        self.editor_text.tag_configure("string", foreground="#ce9178")
        self.editor_text.tag_configure("comment", foreground="#6a9955")
        self.editor_text.tag_configure("function", foreground="#dcdcaa")
        self.editor_text.tag_configure("number", foreground="#b5cea8")

        # Toolbar
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, padx=5, pady=2)

        ttk.Button(toolbar, text="▶ Run", command=self._run_script).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="💾 Save", command=self._save_script).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📂 Load", command=self._load_script).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🧹 Clear", command=lambda: self.editor_text.delete(1.0, tk.END)).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🔍 Inspect", command=self._inspect_code).pack(side=tk.LEFT, padx=2)

        # Insert template
        self._insert_template()

    def _build_batch_tab(self, parent):
        """Build batch processing tab"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # File selection
        file_frame = ttk.LabelFrame(frame, text="📁 Files to Process", padding=5)
        file_frame.pack(fill=tk.X, pady=5)

        self.file_list = tk.Listbox(file_frame, height=5)
        self.file_list.pack(fill=tk.X, pady=2)

        btn_frame = ttk.Frame(file_frame)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="➕ Add Files", command=self._add_batch_files).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="🗑️ Clear", command=lambda: self.file_list.delete(0, tk.END)).pack(side=tk.LEFT, padx=2)

        # Script selection
        script_frame = ttk.LabelFrame(frame, text="📜 Processing Script", padding=5)
        script_frame.pack(fill=tk.X, pady=5)

        self.script_combo = ttk.Combobox(script_frame, values=list(self.macros.keys()) + ["<Current Editor>"])
        self.script_combo.set("<Current Editor>")
        self.script_combo.pack(fill=tk.X, pady=2)

        ttk.Button(script_frame, text="📝 Edit Script", command=self._edit_batch_script).pack(pady=2)

        # Options
        opt_frame = ttk.LabelFrame(frame, text="⚙️ Options", padding=5)
        opt_frame.pack(fill=tk.X, pady=5)

        self.save_output_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opt_frame, text="Save output to file", variable=self.save_output_var).pack(anchor=tk.W)

        self.stop_on_error_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opt_frame, text="Stop on error", variable=self.stop_on_error_var).pack(anchor=tk.W)

        # Run button
        ttk.Button(frame, text="▶ RUN BATCH PROCESS", command=self._run_batch,
                  style='Accent.TButton').pack(pady=10)

        # Progress
        self.batch_progress = ttk.Progressbar(frame, mode='determinate')
        self.batch_progress.pack(fill=tk.X, pady=5)

        self.batch_status = tk.StringVar(value="Ready")
        ttk.Label(frame, textvariable=self.batch_status).pack()

    # ========== CONSOLE METHODS ==========

    def _print_welcome(self):
        """Print welcome message"""
        welcome = f"""
╔══════════════════════════════════════════════════════════════╗
║  🐍 Python Console - Scientific Toolkit                       ║
╠════════════════════════════════════════════════════════════════╣
║  Available objects:                                            ║
║    • app         - Main application instance                  ║
║    • data_hub    - Data storage and management                ║
║    • samples     - Current samples list                       ║
║    • np          - NumPy (if available)                       ║
║    • pd          - Pandas (if available)                      ║
║    • plt         - Matplotlib pyplot                          ║
║                                                               ║
║  Examples:                                                    ║
║    >>> len(samples)                                           ║
║    >>> app.center.get_selected_indices()                      ║
║    >>> data_hub.get_column_names()                            ║
║    >>> plt.plot([s['Zr_ppm'] for s in samples])               ║
║    >>> plt.show()                                             ║
╚════════════════════════════════════════════════════════════════╝
"""
        self._print_output(welcome, "output")
        self._print_prompt()

    def _print_prompt(self):
        """Print prompt"""
        self.output_text.insert(tk.END, "\n>>> ", "prompt")
        self.output_text.see(tk.END)

    def _print_output(self, text, tag="output"):
        """Print output with tag"""
        self.output_text.insert(tk.END, text + "\n", tag)
        self.output_text.see(tk.END)

    def _execute_command(self, event=None):
        """Execute command in console"""
        cmd = self.input_var.get().strip()
        if not cmd:
            self._print_prompt()
            return

        # Add to history
        self.history.append(cmd)
        self.history_index = len(self.history)

        # Show command
        self.output_text.insert(tk.END, f"\n>>> {cmd}\n", "input")

        # Record if recording
        if self.recording:
            self.recorded_commands.append(cmd)

        # Execute
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = self.stdout
        sys.stderr = self.stderr

        try:
            # Clear buffers
            self.stdout.truncate(0)
            self.stdout.seek(0)
            self.stderr.truncate(0)
            self.stderr.seek(0)

            # Execute
            result = eval(cmd, self.locals, self.locals)

            # Get output
            output = self.stdout.getvalue()
            if output:
                self._print_output(output, "output")

            # Show result
            if result is not None:
                self._print_output(repr(result), "output")

        except SyntaxError:
            # Try as statement
            try:
                exec(cmd, self.locals, self.locals)
                output = self.stdout.getvalue()
                if output:
                    self._print_output(output, "output")
            except Exception as e:
                self._print_output(traceback.format_exc(), "error")
        except Exception as e:
            self._print_output(traceback.format_exc(), "error")
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        # Clear input
        self.input_var.set("")

        # Update variable inspector
        self._update_var_inspector()

        # New prompt
        self._print_prompt()

    def _history_up(self, event):
        """Navigate up in history"""
        if self.history and self.history_index > 0:
            self.history_index -= 1
            self.input_var.set(self.history[self.history_index])

    def _history_down(self, event):
        """Navigate down in history"""
        if self.history and self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.input_var.set(self.history[self.history_index])
        else:
            self.history_index = len(self.history)
            self.input_var.set("")

    def _clear_console(self):
        """Clear console output"""
        self.output_text.delete(1.0, tk.END)
        self._print_welcome()

    def _copy_output(self):
        """Copy output to clipboard"""
        self.window.clipboard_clear()
        self.window.clipboard_append(self.output_text.get(1.0, tk.END))

    def _save_log(self):
        """Save console log to file"""
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("Log files", "*.log")]
        )
        if path:
            with open(path, 'w') as f:
                f.write(self.output_text.get(1.0, tk.END))
            self.status_var.set(f"✅ Log saved to {Path(path).name}")

    # ========== EDITOR METHODS ==========

    def _update_line_numbers(self, event=None):
        """Update line numbers in editor"""
        self.line_numbers.config(state='normal')
        self.line_numbers.delete(1.0, tk.END)

        lines = self.editor_text.get(1.0, tk.END).split('\n')
        line_count = len(lines)

        line_numbers = '\n'.join(str(i) for i in range(1, line_count))
        self.line_numbers.insert(1.0, line_numbers)
        self.line_numbers.config(state='disabled')

        # Simple syntax highlighting
        self._apply_syntax_highlighting()

    def _apply_syntax_highlighting(self):
        """Apply basic syntax highlighting"""
        # Remove existing tags
        for tag in ["keyword", "string", "comment", "function", "number"]:
            self.editor_text.tag_remove(tag, 1.0, tk.END)

        # Keywords
        keywords = ['def', 'class', 'if', 'elif', 'else', 'for', 'while',
                   'try', 'except', 'finally', 'with', 'as', 'import', 'from',
                   'return', 'yield', 'break', 'continue', 'pass', 'in', 'is',
                   'not', 'and', 'or', 'True', 'False', 'None']

        content = self.editor_text.get(1.0, tk.END)

        # Very basic highlighting - in reality you'd want a proper lexer
        start = 1.0
        while True:
            pos = self.editor_text.search(r'\b(' + '|'.join(keywords) + r')\b', start, tk.END, regexp=True)
            if not pos:
                break
            end = f"{pos}+{len(self.editor_text.get(pos, f'{pos} wordend'))}c"
            self.editor_text.tag_add("keyword", pos, end)
            start = end

    def _insert_template(self):
        """Insert default script template"""
        template = """# Scientific Toolkit Script
# Access 'app' for main application, 'samples' for data

def process_samples(samples):
    '''Process samples and return results'''
    results = []
    for sample in samples:
        # Your processing here
        if sample.get('Zr_ppm', 0) > 200:
            results.append(sample)
    return results

# Example: Get selected samples
selected_indices = app.center.get_selected_indices()
selected = [samples[i] for i in selected_indices if i < len(samples)]

print(f"Selected {len(selected)} samples")
processed = process_samples(selected)
print(f"Processed {len(processed)} samples")

# Return results to main app
if processed:
    # Add as new column
    for i, idx in enumerate(selected_indices):
        if i < len(processed):
            app.data_hub.update_row(idx, {'Processed': True})
"""
        self.editor_text.insert(1.0, template)
        self._update_line_numbers()

    def _run_script(self):
        """Run script from editor"""
        script = self.editor_text.get(1.0, tk.END)

        # Create temporary namespace
        namespace = self.locals.copy()

        # Redirect output
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = self.stdout
        sys.stderr = self.stderr

        try:
            self.stdout.truncate(0)
            self.stdout.seek(0)

            exec(script, namespace)

            output = self.stdout.getvalue()
            if output:
                self._show_script_output(output)
            else:
                self.status_var.set("✅ Script executed successfully")

        except Exception as e:
            error = traceback.format_exc()
            self._show_script_output(error, is_error=True)
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        self._update_var_inspector()

    def _show_script_output(self, output, is_error=False):
        """Show script output in popup"""
        win = tk.Toplevel(self.window)
        win.title("📋 Script Output")
        win.geometry("600x400")

        text = tk.Text(win, wrap=tk.WORD, font=("Courier", 10))
        scroll = ttk.Scrollbar(win, command=text.yview)
        text.configure(yscrollcommand=scroll.set)

        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        text.insert(1.0, output)
        if is_error:
            text.tag_add("error", 1.0, tk.END)
            text.tag_config("error", foreground="red")

        text.config(state=tk.DISABLED)

    def _save_script(self):
        """Save script to file"""
        path = filedialog.asksaveasfilename(
            defaultextension=".py",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )
        if path:
            with open(path, 'w') as f:
                f.write(self.editor_text.get(1.0, tk.END))
            self.status_var.set(f"✅ Script saved to {Path(path).name}")

    def _load_script(self):
        """Load script from file"""
        path = filedialog.askopenfilename(
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )
        if path:
            with open(path, 'r') as f:
                self.editor_text.delete(1.0, tk.END)
                self.editor_text.insert(1.0, f.read())
            self._update_line_numbers()
            self.status_var.set(f"✅ Loaded {Path(path).name}")

    def _inspect_code(self):
        """Inspect code for errors"""
        script = self.editor_text.get(1.0, tk.END)
        try:
            compile(script, '<string>', 'exec')
            messagebox.showinfo("Code Check", "✅ No syntax errors found!")
        except SyntaxError as e:
            messagebox.showerror("Syntax Error", str(e))

    # ========== VARIABLE INSPECTOR ==========

    def _update_var_inspector(self):
        """Update variable inspector"""
        self.var_tree.delete(*self.var_tree.get_children())

        for name, value in self.locals.items():
            if name.startswith('_'):  # Skip private
                continue

            # Get type
            var_type = type(value).__name__

            # Get value string
            try:
                if isinstance(value, (str, int, float, bool)):
                    val_str = repr(value)
                elif isinstance(value, (list, tuple)):
                    val_str = f"{var_type}[{len(value)}]"
                elif isinstance(value, dict):
                    val_str = f"dict[{len(value)}]"
                elif hasattr(value, '__len__'):
                    val_str = f"{var_type}[{len(value)}]"
                else:
                    val_str = str(value)[:50]
            except:
                val_str = "<unable to display>"

            self.var_tree.insert('', tk.END, text=name, values=(var_type, val_str))

    def _update_locals(self):
        """Update local variables with current app state"""
        self.locals['samples'] = self.app.samples
        self.locals['data_hub'] = self.app.data_hub

        # Add common modules if available
        try:
            import numpy as np
            self.locals['np'] = np
        except: pass

        try:
            import pandas as pd
            self.locals['pd'] = pd
        except: pass

        try:
            import matplotlib.pyplot as plt
            self.locals['plt'] = plt
        except: pass

        self._update_var_inspector()

    # ========== MACRO RECORDER ==========

    def _toggle_recording(self):
        """Toggle macro recording"""
        if not self.recording:
            self.recording = True
            self.recorded_commands = []
            self.rec_btn.config(text="⏹ Stop Recording", style='Accent.TButton')
            self.status_var.set("🔴 Recording...")
        else:
            self.recording = False
            self.rec_btn.config(text="⏺ Record", style='TButton')

            if self.recorded_commands:
                name = simpledialog.askstring("Macro Name", "Enter macro name:", parent=self.window)
                if name:
                    self.macros[name] = self.recorded_commands.copy()
                    self.macro_list.insert(tk.END, name)
                    self._save_macros()
                    self.status_var.set(f"✅ Macro '{name}' saved")
                else:
                    self.status_var.set("Recording cancelled")

    def _run_macro(self):
        """Run selected macro"""
        selection = self.macro_list.curselection()
        if not selection:
            return

        name = self.macro_list.get(selection[0])
        commands = self.macros.get(name, [])

        for cmd in commands:
            self.input_var.set(cmd)
            self._execute_command()

        self.status_var.set(f"✅ Macro '{name}' executed")

    def _save_macro(self):
        """Save selected macro to file"""
        selection = self.macro_list.curselection()
        if not selection:
            return

        name = self.macro_list.get(selection[0])
        commands = self.macros.get(name, [])

        path = filedialog.asksaveasfilename(
            defaultextension=".macro",
            filetypes=[("Macro files", "*.macro"), ("All files", "*.*")]
        )
        if path:
            with open(path, 'w') as f:
                json.dump({'name': name, 'commands': commands}, f)
            self.status_var.set(f"✅ Macro saved to {Path(path).name}")

    def _delete_macro(self):
        """Delete selected macro"""
        selection = self.macro_list.curselection()
        if selection:
            name = self.macro_list.get(selection[0])
            if messagebox.askyesno("Delete", f"Delete macro '{name}'?"):
                del self.macros[name]
                self.macro_list.delete(selection[0])
                self._save_macros()

    def _save_macros(self):
        """Save macros to file"""
        macro_file = Path("config/macros.json")
        macro_file.parent.mkdir(exist_ok=True)
        with open(macro_file, 'w') as f:
            json.dump(self.macros, f)

    def _load_macros(self):
        """Load macros from file"""
        macro_file = Path("config/macros.json")
        if macro_file.exists():
            try:
                with open(macro_file, 'r') as f:
                    self.macros = json.load(f)
                for name in self.macros:
                    self.macro_list.insert(tk.END, name)
            except:
                self.macros = {}

    # ========== BATCH PROCESSING ==========

    def _add_batch_files(self):
        """Add files to batch list"""
        files = filedialog.askopenfilenames(
            title="Select Files to Process",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        for f in files:
            self.file_list.insert(tk.END, f)

    def _edit_batch_script(self):
        """Edit batch script"""
        script = self.script_combo.get()
        if script == "<Current Editor>":
            self.notebook.select(1)  # Switch to editor tab
        elif script in self.macros:
            # Load macro into editor
            self.editor_text.delete(1.0, tk.END)
            self.editor_text.insert(1.0, '\n'.join(self.macros[script]))
            self.notebook.select(1)

    def _run_batch(self):
        """Run batch processing"""
        files = list(self.file_list.get(0, tk.END))
        if not files:
            messagebox.showwarning("No Files", "Add files to process first")
            return

        # Get script
        script_source = self.script_combo.get()
        if script_source == "<Current Editor>":
            script = self.editor_text.get(1.0, tk.END)
        elif script_source in self.macros:
            script = '\n'.join(self.macros[script_source])
        else:
            return

        self.batch_progress['maximum'] = len(files)
        results = []
        errors = []

        for i, file in enumerate(files):
            self.batch_status.set(f"Processing {Path(file).name}...")
            self.batch_progress['value'] = i + 1
            self.window.update()

            try:
                # Load file
                if file.endswith('.csv'):
                    import csv
                    with open(file, 'r') as f:
                        data = list(csv.DictReader(f))
                elif file.endswith(('.xlsx', '.xls')):
                    import pandas as pd
                    df = pd.read_excel(file)
                    data = df.to_dict('records')
                else:
                    with open(file, 'r') as f:
                        data = f.read()

                # Execute script with file data
                namespace = self.locals.copy()
                namespace['file'] = file
                namespace['data'] = data
                namespace['filename'] = Path(file).name

                exec(script, namespace)

                if self.save_output_var.get():
                    # Save results
                    result_file = Path(file).with_suffix('.processed.csv')
                    if 'result' in namespace:
                        import csv
                        with open(result_file, 'w', newline='') as f:
                            if isinstance(namespace['result'], list):
                                if namespace['result'] and isinstance(namespace['result'][0], dict):
                                    writer = csv.DictWriter(f, fieldnames=namespace['result'][0].keys())
                                    writer.writeheader()
                                    writer.writerows(namespace['result'])
                    results.append(str(result_file))

            except Exception as e:
                errors.append(f"{Path(file).name}: {str(e)}")
                if self.stop_on_error_var.get():
                    break

        # Show results
        if errors:
            messagebox.showerror("Batch Processing Errors", "\n".join(errors))
        else:
            messagebox.showinfo("Batch Complete",
                              f"Processed {len(files)} files\n"
                              f"Results saved to: {', '.join(results)}")

        self.batch_status.set("Ready")
        self.batch_progress['value'] = 0


def setup_plugin(main_app):
    """Plugin setup function"""
    print("🐍 Scripting Console v1.0 loading...")
    return ScriptingConsolePlugin(main_app)
