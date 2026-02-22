"""
Script Exporter - Export data processing workflows as Python scripts
Fully converted to ttkbootstrap.
"""

import tkinter as tk
from tkinter import messagebox, filedialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any


class ScriptExporter:
    """
    Exports data processing workflows as executable Python scripts
    """
    def __init__(self, app):
        self.app = app

    def export_current_workflow(self):
        """Export current state as a Python or R script"""
        dialog = ttk.Toplevel(self.app.root)
        dialog.title("Export to Script")
        dialog.geometry("500x450")
        dialog.transient(self.app.root)

        main = ttk.Frame(dialog, padding=10)
        main.pack(fill=BOTH, expand=True)

        ttk.Label(
            main,
            text="Export Workflow to Script",
            font=("TkDefaultFont", 12, "bold"),
            bootstyle="light"
        ).pack(pady=(0, 10))

        # Language selection
        lang_frame = ttk.LabelFrame(main, text="Script Language", padding=10)
        lang_frame.pack(fill=X, pady=(0, 10))

        language = tk.StringVar(value="python")
        ttk.Radiobutton(lang_frame, text="🐍 Python", variable=language, value="python",
                        bootstyle="primary-toolbutton").pack(anchor=W)
        ttk.Radiobutton(lang_frame, text="📊 R", variable=language, value="r",
                        bootstyle="primary-toolbutton").pack(anchor=W)

        ttk.Label(main, text="Select components to include:", bootstyle="light").pack(anchor=W, pady=(0, 5))

        # Checkboxes
        options_frame = ttk.Frame(main)
        options_frame.pack(fill=X, pady=5)

        include_data           = tk.BooleanVar(value=True)
        include_classification = tk.BooleanVar(value=True)
        include_plots          = tk.BooleanVar(value=True)
        include_filters        = tk.BooleanVar(value=True)
        standalone             = tk.BooleanVar(value=True)

        for text, var in [
            ("Include current data",          include_data),
            ("Include classification logic",  include_classification),
            ("Include plotting code",         include_plots),
            ("Include current filters",       include_filters),
            ("Make standalone (runnable)",    standalone),
        ]:
            ttk.Checkbutton(options_frame, text=text, variable=var,
                            bootstyle="primary").pack(anchor=W, pady=2)

        def do_export():
            options = {
                'include_data':           include_data.get(),
                'include_classification': include_classification.get(),
                'include_plots':          include_plots.get(),
                'include_filters':        include_filters.get(),
                'standalone':             standalone.get(),
                'language':               language.get()
            }

            if language.get() == "python":
                script_content = self._generate_python_script(options)
                extension = ".py"
                file_types = [("Python files", "*.py"), ("All files", "*.*")]
            else:
                script_content = self._generate_r_script(options)
                extension = ".R"
                file_types = [("R files", "*.R"), ("All files", "*.*")]

            filepath = filedialog.asksaveasfilename(
                defaultextension=extension,
                filetypes=file_types,
                initialfile=f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}{extension}"
            )
            if filepath:
                try:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(script_content)
                    messagebox.showinfo("Success", f"Script exported to:\n{filepath}")
                    dialog.destroy()
                except Exception as e:
                    messagebox.showerror("Error", f"Export failed:\n{e}")

        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=X, pady=10)

        ttk.Button(btn_frame, text="Export", command=do_export, bootstyle="primary", width=12).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy, bootstyle="secondary", width=12).pack(side=LEFT, padx=5)

    def _generate_python_script(self, options: Dict) -> str:
        lines = [
            "#!/usr/bin/env python3",
            '"""',
            "Scientific Toolkit - Exported Workflow Script",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            '"""',
            "",
        ]

        if options.get('include_data'):
            lines.extend([
                "import csv",
                "import json",
                "",
                "# ── Data ──────────────────────────────────────────────",
                "data = " + repr(self.app.data_hub.get_all()),
                "",
            ])

        if options.get('include_filters'):
            if hasattr(self.app, 'center'):
                search = self.app.center.search_var.get()
                filter_val = self.app.center.filter_var.get()
                if search or filter_val not in ('All', ''):
                    lines.extend([
                        "# ── Filters ──────────────────────────────────────────",
                        f"search_text = {repr(search)}",
                        f"filter_value = {repr(filter_val)}",
                        "",
                        "if search_text:",
                        "    data = [r for r in data if any(search_text.lower() in str(v).lower()",
                        "                                   for v in r.values())]",
                        "",
                    ])

        if options.get('include_classification') and hasattr(self.app, 'right'):
            scheme = self.app.right.scheme_var.get()
            if scheme and scheme != '🔁 Run All Schemes':
                lines.extend([
                    "# ── Classification ───────────────────────────────────",
                    f"selected_scheme = {repr(scheme)}",
                    "# To re-run classification, use the Scientific Toolkit engine.",
                    "",
                ])

        if options.get('include_plots') and hasattr(self.app, 'center'):
            plot_type = getattr(self.app.center, 'plot_type_var', None)
            if plot_type and plot_type.get():
                lines.extend([
                    "# ── Plots ────────────────────────────────────────────",
                    f"plot_type = {repr(plot_type.get())}",
                    "# Use a plotting library (matplotlib / plotly) to reproduce the plot.",
                    "",
                ])

        if options.get('standalone'):
            lines.extend([
                "# ── Main ─────────────────────────────────────────────",
                "if __name__ == '__main__':",
                f"    print(f'Loaded {{len(data)}} samples')",
                "    for row in data[:5]:",
                "        print(row)",
            ])

        return "\n".join(lines)

    def _generate_r_script(self, options: Dict) -> str:
        lines = [
            "# Scientific Toolkit - Exported Workflow Script",
            f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            'library(jsonlite)',
            "",
        ]

        if options.get('include_data'):
            import json
            data_json = json.dumps(self.app.data_hub.get_all(), indent=2)
            lines.extend([
                "# ── Data ──────────────────────────────────────────────",
                f"data <- fromJSON('{data_json}')",
                f"cat(paste('Loaded', nrow(data), 'samples\\n'))",
                "",
            ])

        if options.get('include_classification') and hasattr(self.app, 'right'):
            scheme = self.app.right.scheme_var.get()
            if scheme:
                lines.extend([
                    "# ── Classification ───────────────────────────────────",
                    f"selected_scheme <- {repr(scheme)}",
                    "",
                ])

        return "\n".join(lines)
