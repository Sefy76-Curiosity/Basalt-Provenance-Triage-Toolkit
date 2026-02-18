"""
R Console Plugin - Using subprocess (no rpy2 needed)
"""
import tkinter as tk
from tkinter import ttk
import subprocess
import tempfile
import os
import json

PLUGIN_INFO = {
    'id': 'r_console',
    'name': 'R Console',
    'category': 'console',
    'icon': '📊',
    'version': '1.0',
    'requires': ['R'],  # ← Clear requirement
    'description': 'Run R code for statistical analysis (requires R installed: https://cran.r-project.org/)'
}

class RConsolePlugin:
    def __init__(self, main_app):
        self.app = main_app
        self.history = []
        self.history_index = -1
        self.has_r = self._check_r()
        self.r_version = self._get_r_version() if self.has_r else "Not installed"

    def _check_r(self):
        """Check if R is installed"""
        try:
            result = subprocess.run(['R', '--version'],
                                   capture_output=True,
                                   text=True,
                                   timeout=5)
            return result.returncode == 0
        except:
            return False

    def _get_r_version(self):
        """Get R version string"""
        try:
            result = subprocess.run(['R', '--version'],
                                   capture_output=True,
                                   text=True,
                                   timeout=5)
            if result.returncode == 0:
                # Extract first line of version info
                return result.stdout.split('\n')[0][:40]  # Limit length
        except:
            pass
        return "R"

    def create_tab(self, parent):
        """Create R console UI"""
        if not self.has_r:
            # Show installation message
            frame = ttk.Frame(parent)
            frame.pack(fill=tk.BOTH, expand=True)

            msg = f"""
╔══════════════════════════════════════════════════════════╗
║                    R Not Installed                       ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  The R Console requires R to be installed on your        ║
║  system. It provides powerful statistical analysis       ║
║  and plotting capabilities.                              ║
║                                                          ║
║  📥 Download R from:                                     ║
║     https://cran.r-project.org/                          ║
║                                                          ║
║  After installing R, restart the application.            ║
║                                                          ║
║  💡 Tip: You can verify your installation by typing      ║
║     'R --version' in your terminal.                      ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
"""
            label = tk.Label(frame, text=msg, font=('Consolas', 10),
                           justify=tk.LEFT, bg='#1e1e1e', fg='#d4d4d4')
            label.pack(expand=True)

            # Add a button to open R website
            def open_r_website():
                import webbrowser
                webbrowser.open('https://cran.r-project.org/')

            ttk.Button(frame, text="Download R",
                      command=open_r_website).pack(pady=10)
            return

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

        # Quick commands bar
        quick_frame = ttk.Frame(parent)
        quick_frame.pack(fill=tk.X, padx=5, pady=2)

        commands = [
            ("📊 Summary", lambda: self.execute("summary(samples)")),
            ("📈 Plot", lambda: self.execute("plot(samples$Zr_ppm, samples$Nb_ppm)")),
            ("📋 Head", lambda: self.execute("head(samples)")),
            ("🔬 Stats", lambda: self.execute("""
                cat("Mean Zr:", mean(samples$Zr_ppm, na.rm=TRUE), "\\n")
                cat("SD Zr:", sd(samples$Zr_ppm, na.rm=TRUE), "\\n")
            """)),
        ]

        for text, cmd in commands:
            ttk.Button(quick_frame, text=text, command=cmd).pack(side=tk.LEFT, padx=2)

        # Package installer
        pkg_frame = ttk.Frame(parent)
        pkg_frame.pack(fill=tk.X, padx=5, pady=2)

        ttk.Label(pkg_frame, text="Install package:").pack(side=tk.LEFT, padx=2)
        self.pkg_var = tk.StringVar()
        pkg_entry = ttk.Entry(pkg_frame, textvariable=self.pkg_var, width=20)
        pkg_entry.pack(side=tk.LEFT, padx=2)
        ttk.Button(pkg_frame, text="Install",
                  command=self._install_package).pack(side=tk.LEFT, padx=2)

        # Input area
        input_frame = ttk.Frame(parent)
        input_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(input_frame, text="R>", font=('Consolas', 10, 'bold')).pack(side=tk.LEFT, padx=2)

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

        ttk.Button(button_frame, text="Run (Ctrl+Enter)",
                  command=self.execute).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Clear",
                  command=self._clear_screen).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Help",
                  command=self._show_help).pack(side=tk.LEFT, padx=2)

        # Export samples to CSV for R to read
        self._export_samples_to_csv()
        self._print_welcome()

    def _export_samples_to_csv(self):
        """Export current samples to CSV for R to access"""
        samples = self.app.data_hub.get_all()
        if samples:
            import csv
            self.samples_csv = tempfile.NamedTemporaryFile(
                mode='w', suffix='.csv', delete=False, encoding='utf-8'
            )
            with open(self.samples_csv.name, 'w', newline='', encoding='utf-8') as f:
                if samples:
                    writer = csv.DictWriter(f, fieldnames=samples[0].keys())
                    writer.writeheader()
                    writer.writerows(samples)

    def _print_welcome(self):
        """Print welcome message"""
        if not self.has_r:
            return

        welcome = f"""
╔══════════════════════════════════════════════════════════╗
║                      R Console                           ║
║              {self.r_version:<36} ║
╠══════════════════════════════════════════════════════════╣
║  Your samples are available as: 'samples' data frame     ║
║                                                          ║
║  📊 Built-in functions:                                  ║
║    summary(samples)    - Summary statistics             ║
║    head(samples)       - First 6 rows                   ║
║    plot(x, y)          - Scatter plot                   ║
║    hist(samples$Zr_ppm) - Histogram                     ║
║    boxplot(Zr_ppm ~ Auto_Classification, data=samples)   ║
║                                                          ║
║  📦 Useful packages for geochemistry:                    ║
║    install.packages("compositions")  - Compositional data║
║    install.packages("robCompositions") - Robust methods  ║
║    install.packages("ggplot2")       - Beautiful plots  ║
║    install.packages("dplyr")         - Data manipulation║
║                                                          ║
║  Examples:                                               ║
║    > samples <- read.csv('{os.path.basename(self.samples_csv.name)}')║
║    > summary(samples)                                    ║
║    > plot(samples$Zr_ppm, samples$Nb_ppm)               ║
║    > boxplot(Zr_ppm ~ Auto_Classification, data=samples) ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
"""
        self._print_output(welcome)

    def _show_help(self):
        """Show detailed help"""
        help_text = """
📊 R CONSOLE HELP
═══════════════════════════════════════════════════════════

BASIC COMMANDS:
  samples <- read.csv('filename.csv')  - Load your data
  summary(samples)                     - Summary statistics
  head(samples)                        - First 6 rows
  str(samples)                          - Structure of data

STATISTICS:
  mean(samples$Zr_ppm, na.rm=TRUE)     - Mean (ignore NA)
  sd(samples$Zr_ppm, na.rm=TRUE)       - Standard deviation
  cor(samples$Zr_ppm, samples$Nb_ppm)  - Correlation
  t.test(Zr_ppm ~ Auto_Classification, data=samples)  - T-test

PLOTTING:
  plot(samples$Zr_ppm, samples$Nb_ppm)  - Scatter plot
  hist(samples$Zr_ppm)                  - Histogram
  boxplot(Zr_ppm ~ Auto_Classification, data=samples)  - Boxplot
  pairs(samples[,1:5])                  - Pairwise scatter plots

INSTALLING PACKAGES:
  install.packages("ggplot2")           - Install a package
  library(ggplot2)                      - Load a package
  update.packages()                      - Update all packages

💡 TIPS:
  • Use $ to access columns: samples$Zr_ppm
  • Use na.rm=TRUE to ignore missing values
  • Use ?function to get help: ?mean
"""
        self._print_output(help_text)

    def _install_package(self):
        """Install an R package"""
        pkg = self.pkg_var.get().strip()
        if pkg:
            self.execute(f'install.packages("{pkg}")')
            self.pkg_var.set("")

    def execute(self, code=None, event=None):
        """Execute R code"""
        if code is None:
            code = self.input.get("1.0", tk.END).strip()

        if not code:
            return

        self.history.append(code)
        self.history_index = len(self.history)

        self._print_output(f"R> {code}\n")
        self.input.delete("1.0", tk.END)

        # Create temporary R script
        with tempfile.NamedTemporaryFile(mode='w', suffix='.R',
                                        delete=False, encoding='utf-8') as f:
            # First load the samples if they exist
            script = f'''
# Load samples if available
if(file.exists("{self.samples_csv.name}")) {{
  samples <- read.csv("{self.samples_csv.name}")
  cat("✓ Loaded", nrow(samples), "samples\\n\\n")
}}

# Set options for better output
options(width=100)
options(max.print=1000)

# Capture output
sink("/dev/stdout", type="output")
sink("/dev/stderr", type="message")

# User code
{code}

# Close sinks
sink(type="output")
sink(type="message")
'''
            f.write(script)
            script_path = f.name

        try:
            # Run R script
            result = subprocess.run(
                ['Rscript', script_path],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.stdout:
                self._print_output(result.stdout)
            if result.stderr:
                self._print_output(result.stderr, error=True)

        except subprocess.TimeoutExpired:
            self._print_output("⏱️ R script timed out (30s limit)\n", error=True)
        except Exception as e:
            self._print_output(f"❌ Error: {str(e)}\n", error=True)
        finally:
            try:
                os.unlink(script_path)
            except:
                pass

        self._print_output("\n")

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

    def _clear_screen(self, event=None):
        """Clear output"""
        self.output.config(state=tk.NORMAL)
        self.output.delete("1.0", tk.END)
        self.output.config(state=tk.DISABLED)
        self._print_welcome()
        return "break"

def register_plugin(main_app):
    """Register this plugin"""
    plugin = RConsolePlugin(main_app)

    # Use add_console_plugin, not add_tab_plugin
    if hasattr(main_app.center, 'add_console_plugin'):
        main_app.center.add_console_plugin(
            console_name="R",
            console_icon="📊",
            console_instance=plugin
        )
    return None  # Important! Return None so it doesn't go to Advanced menu
