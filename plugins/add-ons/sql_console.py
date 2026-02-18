"""
SQL Console Plugin - Uses SQLite (built into Python)
"""
import tkinter as tk
from tkinter import ttk
import sqlite3
import io
import pandas as pd
from contextlib import redirect_stdout, redirect_stderr

PLUGIN_INFO = {
    'id': 'sql_console',
    'name': 'SQL Console',
    'category': 'console',
    'icon': '🗄️',
    'version': '1.0',
    'description': 'Query your samples using SQL (SQLite built-in)'
}

class SQLConsolePlugin:
    def __init__(self, main_app):
        self.app = main_app
        self.history = []
        self.history_index = -1
        self.conn = None
        self._create_database()

    def _create_database(self):
        """Create in-memory SQLite database with samples"""
        self.conn = sqlite3.connect(':memory:')
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries

        # Get samples
        samples = self.app.data_hub.get_all()
        if not samples:
            return

        # Convert to DataFrame for easy SQLite creation
        df = pd.DataFrame(samples)

        # Create table and insert data
        df.to_sql('samples', self.conn, index=False, if_exists='replace')

        # Create indexes for faster queries
        cursor = self.conn.cursor()
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_classification ON samples(Auto_Classification)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_zr ON samples(Zr_ppm)')
        self.conn.commit()

    def _refresh_database(self):
        """Refresh database when samples change"""
        self._create_database()

    def create_tab(self, parent):
        """Create SQL console UI"""
        # Create output area
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

        # Scrollbar
        scrollbar = ttk.Scrollbar(output_frame, orient=tk.VERTICAL,
                                  command=self.output.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.output.configure(yscrollcommand=scrollbar.set)

        # Input area
        input_frame = ttk.Frame(parent)
        input_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(input_frame, text="SQL>", font=('Consolas', 10, 'bold')).pack(side=tk.LEFT, padx=2)

        self.input = tk.Text(
            input_frame,
            height=4,
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

        # Button frame
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(button_frame, text="Run (Ctrl+Enter)",
                  command=self.execute).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Clear",
                  command=self._clear_screen).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Show Tables",
                  command=self._show_tables).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Refresh Data",
                  command=self._refresh_database).pack(side=tk.LEFT, padx=2)

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_label = tk.Label(parent, textvariable=self.status_var,
                                font=('Consolas', 8), anchor=tk.W)
        status_label.pack(fill=tk.X, padx=5, pady=2)

        self._print_welcome()

    def _print_welcome(self):
        """Print welcome message"""
        # Get table info
        if self.conn:
            cursor = self.conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()

            # Get column names - with safety check
            columns = []
            try:
                cursor.execute("PRAGMA table_info(samples)")
                columns = [col[1] for col in cursor.fetchall()]
            except:
                columns = []  # No columns yet

            sample_count = len(self.app.data_hub.get_all())

            # Build columns display with proper alignment
            if columns:
                columns_text = ', '.join(columns[:5])
                if len(columns) > 5:
                    columns_text += '...'
            else:
                columns_text = ""

            # Pad to exactly 38 characters to match the border
            columns_display = f"{columns_text:<38}"

            # Fix the table row alignment too
            table_row = f"  Table: samples ({sample_count} rows)"
            table_display = f"{table_row:<49}"  # Pad to 49 chars

            welcome = f"""
╔══════════════════════════════════════════════════════════╗
║                  SQL Console - SQLite                    ║
╠══════════════════════════════════════════════════════════╣
║  Database: :memory:                                      ║
║  {table_display}       ║
║  Columns: {columns_display}         ║
║                                                          ║
║  Examples:                                               ║
║    SELECT * FROM samples LIMIT 5;                        ║
║    SELECT Sample_ID, Zr_ppm, Nb_ppm FROM samples         ║
║    WHERE Zr_ppm > 200;                                   ║
║                                                          ║
║    SELECT Auto_Classification, COUNT(*) as count         ║
║    FROM samples GROUP BY Auto_Classification;            ║
║                                                          ║
║    SELECT AVG(Zr_ppm) as Avg_Zr, AVG(Nb_ppm) as Avg_Nb   ║
║    FROM samples WHERE Auto_Classification LIKE '%SINAI%';║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """
            self._print_output(welcome)

    def execute(self, event=None):
        """Execute SQL query"""
        sql = self.input.get("1.0", tk.END).strip()
        if not sql:
            return

        self.history.append(sql)
        self.history_index = len(self.history)

        self._print_output(f"SQL> {sql}\n")
        self.input.delete("1.0", tk.END)

        if not self.conn:
            self._print_output("Error: Database not initialized\n", error=True)
            return

        try:
            # Execute query
            cursor = self.conn.cursor()
            cursor.execute(sql)

            # Check if it's a SELECT query
            if sql.strip().upper().startswith('SELECT'):
                rows = cursor.fetchall()

                if rows:
                    # Get column names
                    columns = [description[0] for description in cursor.description]

                    # Format as table
                    self._print_output(self._format_table(columns, rows))
                    self.status_var.set(f"Returned {len(rows)} rows")
                else:
                    self._print_output("(no rows returned)\n")
                    self.status_var.set("Query executed - no results")
            else:
                # For INSERT, UPDATE, DELETE, etc.
                self.conn.commit()
                changes = cursor.rowcount
                self._print_output(f"Query OK, {changes} rows affected\n")
                self.status_var.set(f"{changes} rows affected")

        except sqlite3.Error as e:
            self._print_output(f"SQL Error: {str(e)}\n", error=True)
            self.status_var.set("Error")

        self._print_output("\n")

    def _format_table(self, columns, rows, max_width=80):
        """Format query results as a nice table"""
        if not rows:
            return "(empty)\n"

        # Calculate column widths
        col_widths = []
        for i, col in enumerate(columns):
            # Start with column name width
            width = len(str(col))
            # Check data in first few rows
            for row in rows[:20]:
                val = str(row[i]) if row[i] is not None else 'NULL'
                width = max(width, len(val))
            # Cap width
            width = min(width, 30)
            col_widths.append(width + 2)

        # Create separator line
        separator = '+' + '+'.join('-' * w for w in col_widths) + '+'

        # Format header
        lines = [separator]
        header = '|'
        for i, col in enumerate(columns):
            header += f" {str(col):<{col_widths[i]-1}}|"
        lines.append(header)
        lines.append(separator.replace('-', '='))

        # Format rows (limit to 100 rows for display)
        for row in rows[:100]:
            line = '|'
            for i, val in enumerate(row):
                if val is None:
                    text = 'NULL'
                else:
                    text = str(val)
                line += f" {text:<{col_widths[i]-1}}|"
            lines.append(line)

        if len(rows) > 100:
            lines.append(f"... and {len(rows) - 100} more rows")

        lines.append(separator)
        lines.append(f"({len(rows)} rows total)\n")

        return '\n'.join(lines)

    def _show_tables(self):
        """Show all tables and schema"""
        if not self.conn:
            return

        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()

        output = "\n📋 Tables:\n"
        for table in tables:
            table_name = table[0]
            output += f"\n  {table_name}:\n"

            # Get schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            for col in columns:
                output += f"    • {col[1]} ({col[2]})\n"

        self._print_output(output)

    def _print_output(self, text, error=False):
        """Print to output"""
        self.output.config(state=tk.NORMAL)
        if error:
            self.output.insert(tk.END, text, 'error')
            self.output.tag_config('error', foreground='#f48771')
        else:
            self.output.insert(tk.END, text)
        self.output.see(tk.END)
        self.output.config(state=tk.DISABLED)

    def _on_enter(self, event):
        """Handle Enter key"""
        if not (event.state & 0x1):  # Not Shift
            self.execute()
            return "break"
        return None

    def _insert_newline(self, event):
        """Insert newline on Shift+Enter"""
        self.input.insert(tk.INSERT, "\n")
        return "break"

    def _history_up(self, event):
        """Navigate history up"""
        if self.history and self.history_index > 0:
            self.history_index -= 1
            self.input.delete("1.0", tk.END)
            self.input.insert("1.0", self.history[self.history_index])
        return "break"

    def _history_down(self, event):
        """Navigate history down"""
        if self.history and self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.input.delete("1.0", tk.END)
            self.input.insert("1.0", self.history[self.history_index])
        elif self.history_index == len(self.history) - 1:
            self.history_index = len(self.history)
            self.input.delete("1.0", tk.END)
        return "break"

    def _clear_screen(self):
        """Clear output"""
        self.output.config(state=tk.NORMAL)
        self.output.delete("1.0", tk.END)
        self.output.config(state=tk.DISABLED)
        self._print_welcome()

def register_plugin(main_app):
    """Register this plugin"""
    plugin = SQLConsolePlugin(main_app)

    # THIS IS THE KEY CHANGE - use add_console_plugin, not add_tab_plugin
    if hasattr(main_app.center, 'add_console_plugin'):
        main_app.center.add_console_plugin(
            console_name="SQL",
            console_icon="🗄️",
            console_instance=plugin
        )
    return None  # Important! Return None so it doesn't go to Advanced menu
