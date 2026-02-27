"""
Script Exporter - Export data processing workflows as executable scripts
Fully converted to ttkbootstrap with improved architecture and error handling.
"""

import tkinter as tk
from tkinter import messagebox, filedialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
import json
import csv


class ScriptExporter:
    """
    Exports data processing workflows as executable Python or R scripts.

    This class captures the current application state and generates
    standalone scripts that can reproduce the analysis workflow.
    """

    # Language configurations
    LANGUAGES = {
        'python': {
            'name': '🐍 Python',
            'extension': '.py',
            'file_types': [("Python files", "*.py"), ("All files", "*.*")],
            'generator': '_generate_python_script'
        },
        'r': {
            'name': '📊 R',
            'extension': '.R',
            'file_types': [("R files", "*.R"), ("All files", "*.*")],
            'generator': '_generate_r_script'
        }
    }

    def __init__(self, app):
        """
        Initialize the script exporter.

        Args:
            app: The main application instance containing data_hub and UI components
        """
        self.app = app
        self._export_dialog: Optional[ttk.Toplevel] = None

    def is_available(self) -> bool:
        """Check if exporter is properly initialized and ready."""
        return hasattr(self.app, 'data_hub') and self.app.data_hub is not None

    def export_current_workflow(self):
        """
        Export current state as a Python or R script.
        Safe to call even if exporter is not fully initialized.
        """
        if not self.is_available():
            messagebox.showinfo(
                "Not Available",
                "Script exporter is not ready.\n"
                "Please ensure data is loaded and try again."
            )
            return

        self._show_export_dialog()

    # ------------------------------------------------------------
    # DIALOG CREATION
    # ------------------------------------------------------------

    def _show_export_dialog(self):
        """Create and show the export configuration dialog."""
        # Prevent multiple dialogs
        if self._export_dialog and self._export_dialog.winfo_exists():
            self._export_dialog.lift()
            return

        dialog = ttk.Toplevel(self.app.root)
        dialog.title("Export Workflow to Script")
        dialog.geometry("550x500")
        dialog.transient(self.app.root)
        dialog.resizable(False, False)

        # Center on parent
        dialog.update_idletasks()
        x = self.app.root.winfo_x() + (self.app.root.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.app.root.winfo_y() + (self.app.root.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        self._export_dialog = dialog
        self._build_dialog_content(dialog)

        # Clean up reference when closed
        dialog.protocol("WM_DELETE_WINDOW", lambda: self._on_dialog_close(dialog))

    def _build_dialog_content(self, parent: ttk.Toplevel):
        """Build the dialog content."""
        main = ttk.Frame(parent, padding=15)
        main.pack(fill=BOTH, expand=True)

        # Header
        self._add_header(main)

        # Language selection
        lang_frame = self._add_language_selection(main)

        # Options section
        options_frame = self._add_options_section(main)

        # Preview section (optional)
        preview_frame = self._add_preview_section(main)

        # Buttons
        self._add_buttons(main, lang_frame, options_frame, preview_frame)

    def _add_header(self, parent: ttk.Frame):
        """Add header section."""
        header = ttk.Frame(parent)
        header.pack(fill=X, pady=(0, 15))

        ttk.Label(
            header,
            text="📤 Export Workflow to Script",
            font=("TkDefaultFont", 14, "bold"),
            bootstyle="inverse-primary"
        ).pack()

        ttk.Label(
            header,
            text="Generate a standalone script that reproduces your current analysis",
            font=("TkDefaultFont", 9),
            bootstyle="secondary"
        ).pack(pady=(2, 0))

    def _add_language_selection(self, parent: ttk.Frame) -> ttk.Frame:
        """Add language selection section."""
        lang_frame = ttk.LabelFrame(parent, text="Script Language", padding=10)
        lang_frame.pack(fill=X, pady=(0, 10))

        self.language = tk.StringVar(value="python")

        # Create radio buttons for each language
        radio_frame = ttk.Frame(lang_frame)
        radio_frame.pack()

        for i, (lang_code, lang_config) in enumerate(self.LANGUAGES.items()):
            ttk.Radiobutton(
                radio_frame,
                text=lang_config['name'],
                variable=self.language,
                value=lang_code,
                bootstyle="primary-outline-toolbutton"
            ).pack(side=LEFT, padx=5 if i > 0 else 0)

        return lang_frame

    def _add_options_section(self, parent: ttk.Frame) -> Dict[str, tk.BooleanVar]:
        """Add export options section."""
        options_frame = ttk.LabelFrame(parent, text="Export Options", padding=10)
        options_frame.pack(fill=X, pady=(0, 10))

        # Tooltip-like description
        ttk.Label(
            options_frame,
            text="Select components to include in the generated script:",
            font=("TkDefaultFont", 9, "italic"),
            bootstyle="secondary"
        ).pack(anchor=W, pady=(0, 8))

        # Options with descriptions
        options = [
            ("Include current data", "include_data",
             "Embed the current dataset in the script", True),
            ("Include classification logic", "include_classification",
             "Add classification rules and schemes", True),
            ("Include plotting code", "include_plots",
             "Generate code to recreate visualizations", True),
            ("Include current filters", "include_filters",
             "Preserve active filters and search terms", True),
            ("Make standalone (runnable)", "standalone",
             "Add main() function for direct execution", True),
            ("Add comments and documentation", "include_docs",
             "Include explanatory comments in the code", True),
        ]

        # Create checkboxes
        self.options_vars = {}
        for text, key, desc, default in options:
            var = tk.BooleanVar(value=default)
            self.options_vars[key] = var

            cb_frame = ttk.Frame(options_frame)
            cb_frame.pack(fill=X, pady=2)

            ttk.Checkbutton(
                cb_frame,
                text=text,
                variable=var,
                bootstyle="primary"
            ).pack(side=LEFT)

            # Add tooltip-like description
            ttk.Label(
                cb_frame,
                text=f"({desc})",
                font=("TkDefaultFont", 8),
                bootstyle="secondary"
            ).pack(side=LEFT, padx=(10, 0))

        return self.options_vars

    def _add_preview_section(self, parent: ttk.Frame) -> Optional[ttk.Frame]:
        """Add optional preview section."""
        if not hasattr(self.app, 'center'):
            return None

        preview_frame = ttk.LabelFrame(parent, text="Workflow Summary", padding=10)
        preview_frame.pack(fill=BOTH, expand=True, pady=(0, 10))

        # Get current workflow state
        summary = self._get_workflow_summary()

        # Display as text
        text_widget = tk.Text(
            preview_frame,
            height=4,
            wrap=tk.WORD,
            font=("Courier", 9),
            bg=parent.style.colors.bg if hasattr(parent, 'style') else "#f0f0f0"
        )
        text_widget.pack(fill=BOTH, expand=True)
        text_widget.insert("1.0", summary)
        text_widget.config(state=tk.DISABLED)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=text_widget.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        text_widget.config(yscrollcommand=scrollbar.set)

        return preview_frame

    def _add_buttons(self, parent: ttk.Frame, *args):
        """Add action buttons."""
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=X, pady=(10, 0))

        # Export button
        ttk.Button(
            btn_frame,
            text="📥 Export Script",
            command=self._do_export,
            bootstyle="success",
            width=15
        ).pack(side=LEFT, padx=5)

        # Preview button (optional)
        ttk.Button(
            btn_frame,
            text="👁️ Preview",
            command=self._preview_script,
            bootstyle="info-outline",
            width=12
        ).pack(side=LEFT, padx=5)

        # Cancel button
        ttk.Button(
            btn_frame,
            text="❌ Cancel",
            command=lambda: self._on_dialog_close(parent.winfo_toplevel()),
            bootstyle="secondary-outline",
            width=12
        ).pack(side=RIGHT, padx=5)

    # ------------------------------------------------------------
    # WORKFLOW SUMMARY
    # ------------------------------------------------------------

    def _get_workflow_summary(self) -> str:
        """Generate a summary of the current workflow state."""
        lines = []

        # Data info
        data = self.app.data_hub.get_all()
        lines.append(f"📊 Data: {len(data)} samples")

        # Filters
        if hasattr(self.app, 'center'):
            search = self.app.center.search_var.get()
            filter_val = self.app.center.filter_var.get()
            if search:
                lines.append(f"🔍 Search: '{search}'")
            if filter_val and filter_val != 'All':
                lines.append(f"🎯 Filter: {filter_val}")

        # Classification
        if hasattr(self.app, 'right') and hasattr(self.app.right, 'scheme_var'):
            scheme = self.app.right.scheme_var.get()
            if scheme and scheme != '🔁 Run All Schemes':
                lines.append(f"📋 Scheme: {scheme}")

        # Plot
        if hasattr(self.app, 'center') and hasattr(self.app.center, 'plot_type_var'):
            plot = self.app.center.plot_type_var.get()
            if plot:
                lines.append(f"📈 Plot: {plot}")

        return "\n".join(lines) if lines else "No active workflow configuration"

    # ------------------------------------------------------------
    # EXPORT LOGIC
    # ------------------------------------------------------------

    def _do_export(self):
        """Execute the export with current options."""
        # Gather options
        options = {
            key: var.get() for key, var in self.options_vars.items()
        }
        options['language'] = self.language.get()

        # Validate options
        if not self._validate_options(options):
            return

        # Get language config
        lang_config = self.LANGUAGES[options['language']]

        # Generate script
        generator = getattr(self, lang_config['generator'])
        script_content = generator(options)

        # Get save location
        filepath = self._get_save_path(lang_config)
        if not filepath:
            return

        # Save file
        if self._save_script(filepath, script_content):
            self._on_export_success(filepath)

    def _validate_options(self, options: Dict) -> bool:
        """Validate export options."""
        if not options.get('include_data') and not options.get('include_classification'):
            result = messagebox.askyesno(
                "Empty Export",
                "You haven't selected any content to export.\n"
                "This will generate an empty script. Continue?",
                icon='warning'
            )
            return result
        return True

    def _get_save_path(self, lang_config: Dict) -> Optional[str]:
        """Get save path from user."""
        initial_name = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}{lang_config['extension']}"

        return filedialog.asksaveasfilename(
            defaultextension=lang_config['extension'],
            filetypes=lang_config['file_types'],
            initialfile=initial_name,
            title=f"Export {lang_config['name']} Script"
        )

    def _save_script(self, filepath: str, content: str) -> bool:
        """Save script to file."""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            messagebox.showerror(
                "Export Failed",
                f"Could not save script:\n{str(e)}"
            )
            return False

    def _preview_script(self):
        """Show a preview of the script in a separate window."""
        options = {
            key: var.get() for key, var in self.options_vars.items()
        }
        options['language'] = self.language.get()

        # Generate preview
        lang_config = self.LANGUAGES[options['language']]
        generator = getattr(self, lang_config['generator'])
        preview_content = generator(options)

        # Show preview dialog
        self._show_preview_dialog(preview_content, lang_config['name'])

    def _show_preview_dialog(self, content: str, language: str):
        """Show script preview dialog."""
        preview = ttk.Toplevel(self.app.root)
        preview.title(f"Script Preview - {language}")
        preview.geometry("600x500")
        preview.transient(self.app.root)

        # Text widget with syntax highlighting simulation
        frame = ttk.Frame(preview, padding=10)
        frame.pack(fill=BOTH, expand=True)

        ttk.Label(
            frame,
            text=f"Preview ({language})",
            font=("TkDefaultFont", 11, "bold")
        ).pack(anchor=W, pady=(0, 5))

        # Text area
        text_frame = ttk.Frame(frame)
        text_frame.pack(fill=BOTH, expand=True)

        text_widget = tk.Text(
            text_frame,
            wrap=tk.NONE,
            font=("Courier", 10),
            bg="#f8f8f8"
        )

        v_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        h_scrollbar = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=text_widget.xview)

        text_widget.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        text_widget.pack(side=LEFT, fill=BOTH, expand=True)
        v_scrollbar.pack(side=RIGHT, fill=Y)
        h_scrollbar.pack(side=BOTTOM, fill=X)

        # Insert content
        text_widget.insert("1.0", content)
        text_widget.config(state=tk.DISABLED)

        # Close button
        ttk.Button(
            frame,
            text="Close",
            command=preview.destroy,
            bootstyle="secondary"
        ).pack(pady=(10, 0))

    def _on_export_success(self, filepath: str):
        """Handle successful export."""
        messagebox.showinfo(
            "Export Successful",
            f"Script exported to:\n{filepath}\n\n"
            "You can now run this script to reproduce your analysis."
        )
        if self._export_dialog and self._export_dialog.winfo_exists():
            self._export_dialog.destroy()

    def _on_dialog_close(self, dialog: ttk.Toplevel):
        """Clean up dialog reference."""
        dialog.destroy()
        if self._export_dialog == dialog:
            self._export_dialog = None

    # ------------------------------------------------------------
    # SCRIPT GENERATORS
    # ------------------------------------------------------------

    def _generate_python_script(self, options: Dict) -> str:
        """Generate Python script with current workflow."""
        lines = []

        # Shebang and header
        if options.get('standalone'):
            lines.append("#!/usr/bin/env python3")

        lines.extend([
            '"""',
            "Scientific Toolkit - Exported Workflow Script",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            '"""',
            ""
        ])

        # Imports
        if options.get('include_docs'):
            lines.append("# Required imports")
        lines.extend([
            "import csv",
            "import json",
            "from pathlib import Path",
            "from typing import List, Dict, Any",
            ""
        ])

        # Data section
        if options.get('include_data'):
            lines.extend(self._generate_python_data_section(options))

        # Filters section
        if options.get('include_filters'):
            lines.extend(self._generate_python_filters_section(options))

        # Classification section
        if options.get('include_classification'):
            lines.extend(self._generate_python_classification_section(options))

        # Plots section
        if options.get('include_plots'):
            lines.extend(self._generate_python_plots_section(options))

        # Standalone main
        if options.get('standalone'):
            lines.extend(self._generate_python_main_section(options))

        return "\n".join(lines)

    def _generate_python_data_section(self, options: Dict) -> List[str]:
        """Generate Python data section."""
        lines = [
            "# ── Data ──────────────────────────────────────────────",
            "# Embedded dataset from export time",
            "data = " + repr(self.app.data_hub.get_all()),
            f"print(f'📊 Loaded {{len(data)}} samples')",
            ""
        ]
        return lines

    def _generate_python_filters_section(self, options: Dict) -> List[str]:
        """Generate Python filters section."""
        lines = []

        if hasattr(self.app, 'center'):
            search = self.app.center.search_var.get()
            filter_val = self.app.center.filter_var.get()

            if search or (filter_val and filter_val not in ('All', '')):
                lines.extend([
                    "# ── Filters ──────────────────────────────────────────",
                    "# Active filters from export time"
                ])

                if search:
                    lines.extend([
                        f"search_text = {repr(search)}",
                        "if search_text:",
                        "    data = [row for row in data if any(",
                        "        search_text.lower() in str(v).lower()",
                        "        for v in row.values()",
                        "    )]",
                        f"    print(f'🔍 Search applied: {{len(data)}} samples remain')",
                        ""
                    ])

                if filter_val and filter_val not in ('All', ''):
                    lines.extend([
                        f"filter_value = {repr(filter_val)}",
                        "if filter_value:",
                        "    # Apply filter logic here",
                        "    # This is a placeholder - customize for your needs",
                        f"    print(f'🎯 Filter: {{filter_value}}')",
                        ""
                    ])

        return lines

    def _generate_python_classification_section(self, options: Dict) -> List[str]:
        """Generate Python classification section."""
        lines = []

        if hasattr(self.app, 'right') and hasattr(self.app.right, 'scheme_var'):
            scheme = self.app.right.scheme_var.get()
            if scheme and scheme != '🔁 Run All Schemes':
                lines.extend([
                    "# ── Classification ───────────────────────────────────",
                    f"selected_scheme = {repr(scheme)}",
                    "# Note: Full classification requires the Scientific Toolkit engine",
                    "# To re-run classification, use the ProtocolEngine class",
                    "",
                    "# Example:",
                    "# from protocol_engine import ProtocolEngine",
                    "# engine = ProtocolEngine()",
                    "# data = engine.run_protocol(data, selected_scheme)",
                    ""
                ])

        return lines

    def _generate_python_plots_section(self, options: Dict) -> List[str]:
        """Generate Python plots section."""
        lines = []

        if hasattr(self.app, 'center') and hasattr(self.app.center, 'plot_type_var'):
            plot_type = self.app.center.plot_type_var.get()
            if plot_type:
                lines.extend([
                    "# ── Plots ────────────────────────────────────────────",
                    "import matplotlib.pyplot as plt",
                    "import seaborn as sns",
                    "",
                    f"plot_type = {repr(plot_type)}",
                    "",
                    "# Configure plot style",
                    "sns.set_style('whitegrid')",
                    "plt.figure(figsize=(10, 6))",
                    "",
                    f"# Generate {plot_type} plot",
                    "# Add your plotting code here based on the data structure",
                    "",
                    "plt.title(f'{plot_type} Plot')",
                    "plt.tight_layout()",
                    "plt.show()",
                    ""
                ])

        return lines

    def _generate_python_main_section(self, options: Dict) -> List[str]:
        """Generate Python main section."""
        return [
            "# ── Main ─────────────────────────────────────────────",
            "def main():",
            "    \"\"\"Main execution function.\"\"\"",
            "    print('=' * 50)",
            "    print('Scientific Toolkit - Exported Workflow')",
            "    print('=' * 50)",
            "    print(f'Total samples: {len(data)}')",
            "",
            "    # Show sample preview",
            "    print('\\n📋 Sample preview (first 3 rows):')",
            "    for i, row in enumerate(data[:3]):",
            "        print(f'  {i+1}. {row}')",
            "",
            "if __name__ == '__main__':",
            "    main()"
        ]

    def _generate_r_script(self, options: Dict) -> str:
        """Generate R script with current workflow."""
        lines = [
            "# Scientific Toolkit - Exported Workflow Script",
            f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "# Load required libraries",
            "library(jsonlite)",
            "library(dplyr)",
            "library(ggplot2)",
            ""
        ]

        # Data section
        if options.get('include_data'):
            data = self.app.data_hub.get_all()
            # Convert to R-friendly format
            r_data = self._convert_to_r_dataframe(data)
            lines.extend([
                "# ── Data ──────────────────────────────────────────────",
                "# Embedded dataset from export time",
                r_data,
                "",
                "cat('📊 Loaded', nrow(data), 'samples\\n')",
                ""
            ])

        # Filters section
        if options.get('include_filters') and hasattr(self.app, 'center'):
            search = self.app.center.search_var.get()
            if search:
                lines.extend([
                    "# ── Filters ──────────────────────────────────────────",
                    "# Apply search filter",
                    f"search_text <- '{search}'",
                    "data <- data[apply(data, 1, function(row) {",
                    "    any(grepl(search_text, row, ignore.case=TRUE))",
                    "}), ]",
                    "cat('🔍 After search:', nrow(data), 'samples\\n')",
                    ""
                ])

        # Classification section
        if options.get('include_classification') and hasattr(self.app, 'right'):
            scheme = self.app.right.scheme_var.get()
            if scheme and scheme != '🔁 Run All Schemes':
                lines.extend([
                    "# ── Classification ───────────────────────────────────",
                    f"selected_scheme <- '{scheme}'",
                    "# Add classification logic here",
                    ""
                ])

        # Plots section
        if options.get('include_plots') and hasattr(self.app, 'center'):
            plot_type = self.app.center.plot_type_var.get()
            if plot_type:
                lines.extend([
                    "# ── Plots ────────────────────────────────────────────",
                    "# Generate plot",
                    "ggplot(data, aes(x=1:nrow(data), y=value)) +",
                    "    geom_point() +",
                    "    labs(title=paste('Plot Type:', 'placeholder')) +",
                    "    theme_minimal()",
                    ""
                ])

        return "\n".join(lines)

    def _convert_to_r_dataframe(self, data: List[Dict]) -> str:
        """Convert Python data to R data frame representation."""
        if not data:
            return "data <- data.frame()"

        # Get all column names
        columns = set()
        for row in data:
            columns.update(row.keys())
        columns = sorted(columns)

        # Build R data frame
        lines = ["data <- data.frame("]

        for col in columns:
            values = [str(row.get(col, "NA")) for row in data]
            # Quote string values
            values = [f"'{v}'" if not v.replace('.', '').replace('-', '').isdigit() else v
                     for v in values]
            values_str = ", ".join(values)
            lines.append(f"    {col} = c({values_str}),")

        lines[-1] = lines[-1].rstrip(',')  # Remove trailing comma
        lines.append(")")

        return "\n".join(lines)
