"""
Python Console Plugin - Gets its own tab
"""
import tkinter as tk
from tkinter import ttk
import sys
import io
from contextlib import redirect_stdout, redirect_stderr

PLUGIN_INFO = {
    'id': 'python_console',
    'name': 'Python Console',
    'category': 'console',
    'icon': '🐍',
    'version': '1.0',
    'description': 'Interactive Python console for data analysis'
}

class PythonConsolePlugin:
    def __init__(self, main_app):
        self.app = main_app
        self.history = []
        self.history_index = -1

        # Local namespace for executed code
        self.locals = {
            'app': main_app,
            'data_hub': main_app.data_hub,
            'get_samples': main_app.data_hub.get_all,
            'classify_all': self._classify_all,
            'export_csv': main_app._export_csv,
            'center': main_app.center,
            'right': main_app.right,
            'left': main_app.left,
            'help': self._show_help,
            'commands': self._list_commands,
            'stats': self._stats,
            'describe': self._describe,
            'find': self._find_samples
        }

    def create_tab(self, parent):
        """
        Create the console UI directly in the provided parent frame
        parent is the tab frame that will be added to the notebook
        """
        # Create output area with scrollbar
        output_frame = ttk.Frame(parent)
        output_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.output = tk.Text(
            output_frame,
            bg='#1e1e1e',
            fg='#d4d4d4',
            font=('Consolas', 10),
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        output_scrollbar = ttk.Scrollbar(
            output_frame,
            orient=tk.VERTICAL,
            command=self.output.yview
        )
        output_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.output.configure(yscrollcommand=output_scrollbar.set)

        # Input area
        input_frame = ttk.Frame(parent)
        input_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(input_frame, text=">>>", font=('Consolas', 10, 'bold')).pack(side=tk.LEFT, padx=2)

        self.input = tk.Text(
            input_frame,
            height=3,
            bg='#2d2d2d',
            fg='#ffffff',
            font=('Consolas', 10),
            insertbackground='white',
            wrap=tk.WORD
        )
        self.input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Bind keys
        self.input.bind('<Return>', self._on_enter)
        self.input.bind('<Shift-Return>', self._insert_newline)
        self.input.bind('<Up>', self._history_up)
        self.input.bind('<Down>', self._history_down)
        self.input.bind('<Control-l>', self._clear_screen)

        # Button frame
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(
            button_frame,
            text="Run (Ctrl+Enter)",
            command=self.execute
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            button_frame,
            text="Clear",
            command=self._clear_screen
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            button_frame,
            text="Clear History",
            command=self._clear_history
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            button_frame,
            text="Help",
            command=lambda: self._print_output(self._list_commands())
        ).pack(side=tk.LEFT, padx=2)

        # Welcome message
        self._print_welcome()

    def _print_welcome(self):
        """Print welcome message"""
        welcome = """
╔══════════════════════════════════════════════════════════╗
║            Python Console - Scientific Toolkit           ║
╠══════════════════════════════════════════════════════════╣
║  Available commands:                                     ║
║    help()          - Show detailed help                  ║
║    commands()      - List all commands                   ║
║    stats(col)      - Show statistics for a column        ║
║    describe(sample)- Show sample details                 ║
║    find(**kwargs)  - Find samples matching criteria      ║
║                                                          ║
║  Available objects:                                      ║
║    app            - Main application                     ║
║    data_hub       - Data manager                         ║
║    center/right/left - Panel references                  ║
║                                                          ║
║  Examples:                                               ║
║    >>> len(get_samples())                                ║
║    >>> stats('Zr_ppm')                                   ║
║    >>> find(Auto_Classification='SINAI_OPHIOLITIC')      ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
"""
        self._print_output(welcome)

    def _print_output(self, text, error=False):
        """Print text to output"""
        self.output.config(state=tk.NORMAL)
        if error:
            self.output.insert(tk.END, text, 'error')
            self.output.tag_config('error', foreground='#f48771')
        else:
            self.output.insert(tk.END, text)
        self.output.see(tk.END)
        self.output.config(state=tk.DISABLED)

    def _show_help(self, topic=None):
        """Show detailed help for a specific topic"""
        help_texts = {
            'data_hub': """
📊 DataHub - Main data manager
  data_hub.row_count()              - Number of samples
  data_hub.get_all()                 - Get all samples
  data_hub.get_page(page, size)      - Get paginated samples
  data_hub.add_samples(rows)         - Add new samples
  data_hub.update_row(index, updates) - Update a sample
  data_hub.delete_rows(indices)       - Delete samples
  data_hub.get_column_names()         - Get all column names
""",
            'samples': """
📋 Working with Samples
  Samples are dictionaries with keys like:
    'Sample_ID'      - Sample identifier
    'Zr_ppm'         - Element concentrations
    'Auto_Classification' - Classification result
    'Notes'          - Sample notes

  Access sample data:
    sample = get_samples()[0]
    sample['Sample_ID']
    sample.get('Zr_ppm', 0)
""",
            'classification': """
🔬 Classification
  classify_all()                    - Run current classification scheme
  right.scheme_var.get()             - Get current scheme name

  Get classification results:
    [s['Auto_Classification'] for s in get_samples()]
""",
            'stats': """
📊 Statistics
  stats(column) - Show statistics for a numeric column
  Example:
    >>> stats('Zr_ppm')
    Count: 42  Mean: 245.30  Stdev: 45.67  Min: 120.00  Max: 380.00
""",
            'describe': """
🔍 Describe Sample
  describe(sample) - Show detailed information about a sample
  Example:
    >>> describe(get_samples()[0])
    Shows all available data for that sample
""",
            'find': """
🔎 Find Samples
  find(**criteria) - Find samples matching criteria
  Example:
    >>> find(Auto_Classification='SINAI_OPHIOLITIC')
    >>> find(Zr_ppm=245)
"""
        }

        if topic is None:
            return "Use help('topic') where topic is: data_hub, samples, classification, stats, describe, find"

        return help_texts.get(topic, f"No help for '{topic}'")

    def _list_commands(self):
        """List all available commands and objects"""
        return """
╔══════════════════════════════════════════════════════════╗
║                    AVAILABLE COMMANDS                    ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  OBJECTS:                                                ║
║    app         - Main application                        ║
║    data_hub    - Data manager                            ║
║    center      - Center panel (table/plots)              ║
║    right       - Right panel (classification)            ║
║    left        - Left panel (data entry)                 ║
║                                                          ║
║  FUNCTIONS:                                              ║
║    get_samples()          - Get all samples              ║
║    classify_all()         - Run classification           ║
║    export_csv()           - Export to CSV                ║
║    stats(column)          - Statistics for a column      ║
║    describe(sample)       - Show sample details          ║
║    find(**kwargs)         - Find samples by criteria     ║
║    help([topic])          - Show detailed help           ║
║    commands()             - Show this list               ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
"""

    def _stats(self, column):
        """Show basic statistics for a numeric column"""
        samples = self.app.data_hub.get_all()
        values = [s.get(column) for s in samples
                 if s.get(column) is not None and isinstance(s.get(column), (int, float))]

        if not values:
            return f"No numeric data in column '{column}'"

        try:
            import statistics
            mean = statistics.mean(values)
            stdev = statistics.stdev(values) if len(values) > 1 else 0
            return f"""
📊 Statistics for {column}:
  Count: {len(values)}
  Mean:  {mean:.2f}
  Stdev: {stdev:.2f}
  Min:   {min(values):.2f}
  Max:   {max(values):.2f}
"""
        except:
            return f"Error calculating statistics for {column}"

    def _describe(self, sample):
        """Show detailed information about a sample"""
        if not sample:
            return "No sample provided"

        lines = [f"\n📋 Sample: {sample.get('Sample_ID', 'Unknown')}"]
        lines.append("-" * 40)

        # Show classification
        classification = sample.get('Auto_Classification', 'UNCLASSIFIED')
        lines.append(f"Classification: {classification}")

        # Show all numeric data
        lines.append("\nData:")
        for key, value in sorted(sample.items()):
            if key not in ['Sample_ID', 'Notes', 'Display_Color'] and value not in [None, '']:
                if isinstance(value, float):
                    lines.append(f"  {key}: {value:.2f}")
                else:
                    lines.append(f"  {key}: {value}")

        return "\n".join(lines)

    def _find_samples(self, **criteria):
        """Find samples matching criteria"""
        samples = self.app.data_hub.get_all()
        results = []

        for s in samples:
            match = True
            for key, value in criteria.items():
                if s.get(key) != value:
                    match = False
                    break
            if match:
                results.append(s)

        if not results:
            return "No matching samples found"

        output = [f"\n🔎 Found {len(results)} matching samples:"]
        for s in results[:10]:  # Show first 10
            output.append(f"  • {s.get('Sample_ID', 'Unknown')}: {s.get('Auto_Classification', 'UNCLASSIFIED')}")

        if len(results) > 10:
            output.append(f"  ... and {len(results) - 10} more")

        return "\n".join(output)

    def execute(self):
        """Execute the current code"""
        code = self.input.get("1.0", tk.END).strip()
        if not code:
            return

        # Add to history
        self.history.append(code)
        self.history_index = len(self.history)

        # Show the command
        self._print_output(f">>> {code}\n")

        # Clear input
        self.input.delete("1.0", tk.END)

        # Capture output
        stdout = io.StringIO()
        stderr = io.StringIO()

        try:
            with redirect_stdout(stdout), redirect_stderr(stderr):
                # Check if it's a help command that returns string
                if code.startswith('help(') or code.startswith('commands(') or \
                   code.startswith('stats(') or code.startswith('describe(') or \
                   code.startswith('find('):
                    result = eval(code, globals(), self.locals)
                    if result:
                        self._print_output(str(result) + "\n")
                else:
                    exec(code, globals(), self.locals)

                    output = stdout.getvalue()
                    if output:
                        self._print_output(output)

                    error = stderr.getvalue()
                    if error:
                        self._print_output(error, error=True)

        except Exception as e:
            self._print_output(f"Error: {str(e)}\n", error=True)

        self._print_output("\n")

    def _classify_all(self, scheme_name=None):
        """Helper to run classification"""
        if hasattr(self.app, 'right'):
            self.app.right._run_classification()
            return "Classification complete"
        return "Classification engine not available"

    def _on_enter(self, event):
        """Handle Enter key - execute if not Shift+Enter"""
        if not (event.state & 0x1):  # Not Shift
            self.execute()
            return "break"
        return None

    def _insert_newline(self, event):
        """Insert newline on Shift+Enter"""
        self.input.insert(tk.INSERT, "\n")
        return "break"

    def _history_up(self, event):
        """Navigate up in history"""
        if self.history and self.history_index > 0:
            self.history_index -= 1
            self._set_input_from_history()
        return "break"

    def _history_down(self, event):
        """Navigate down in history"""
        if self.history and self.history_index < len(self.history) - 1:
            self.history_index += 1
            self._set_input_from_history()
        elif self.history_index == len(self.history) - 1:
            self.history_index = len(self.history)
            self.input.delete("1.0", tk.END)
        return "break"

    def _set_input_from_history(self):
        """Set input field from history"""
        self.input.delete("1.0", tk.END)
        self.input.insert("1.0", self.history[self.history_index])
        self.input.mark_set(tk.INSERT, tk.END)
        self.input.see(tk.END)

    def _clear_screen(self, event=None):
        """Clear the output screen"""
        self.output.config(state=tk.NORMAL)
        self.output.delete("1.0", tk.END)
        self.output.config(state=tk.DISABLED)
        self._print_welcome()
        return "break"

    def _clear_history(self):
        """Clear command history"""
        self.history = []
        self.history_index = -1
        self._print_output("History cleared\n")

# Required for plugin system
def register_plugin(main_app):
    """Register this plugin"""
    plugin = PythonConsolePlugin(main_app)

    # THIS IS THE KEY CHANGE - use add_console_plugin, not add_tab_plugin
    if hasattr(main_app.center, 'add_console_plugin'):
        main_app.center.add_console_plugin(
            console_name="Python",
            console_icon="🐍",
            console_instance=plugin
        )
    return None  # Important! Return None so it doesn't go to Advanced menu
