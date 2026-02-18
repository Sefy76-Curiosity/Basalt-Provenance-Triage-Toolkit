"""
Julia Console - High-performance scientific computing
"""
import tkinter as tk
from tkinter import ttk
import subprocess
import tempfile
import os
import csv
import re

PLUGIN_INFO = {
    'id': 'julia_console',
    'name': 'Julia Console',
    'category': 'console',
    'icon': '⚡',
    'version': '1.0',
    'requires': ['Julia'],
    'description': 'High-performance scientific computing with Julia (requires Julia installed: https://julialang.org/downloads/)'
}

class JuliaConsolePlugin:
    def __init__(self, main_app):
        self.app = main_app
        self.history = []
        self.history_index = -1
        self.has_julia = self._check_julia()
        self.julia_version = self._get_julia_version() if self.has_julia else "Not installed"
        self.samples_file = None

    def _check_julia(self):
        """Check if Julia is installed"""
        try:
            result = subprocess.run(['julia', '--version'],
                                   capture_output=True,
                                   text=True,
                                   timeout=5)
            return result.returncode == 0
        except:
            return False

    def _get_julia_version(self):
        """Get Julia version string"""
        try:
            result = subprocess.run(['julia', '--version'],
                                   capture_output=True,
                                   text=True,
                                   timeout=5)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return "Julia"

    def create_tab(self, parent):
        """Create Julia console UI"""
        if not self.has_julia:
            # Show installation message
            frame = ttk.Frame(parent)
            frame.pack(fill=tk.BOTH, expand=True)

            msg = f"""
╔══════════════════════════════════════════════════════════╗
║                  Julia Not Installed                     ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  The Julia Console requires Julia to be installed on     ║
║  your system. Julia is a high-performance language       ║
║  for scientific computing - as fast as C, as easy as     ║
║  Python!                                                 ║
║                                                          ║
║  📥 Download Julia from:                                 ║
║     https://julialang.org/downloads/                     ║
║                                                          ║
║  After installing Julia, restart the application.        ║
║                                                          ║
║  💡 Quick install:                                       ║
║     • Windows: Download installer, run it                ║
║     • macOS: brew install julia                          ║
║     • Linux: sudo apt install julia                      ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
"""
            label = tk.Label(frame, text=msg, font=('Consolas', 10),
                           justify=tk.LEFT, bg='#1e1e1e', fg='#d4d4d4')
            label.pack(expand=True)

            def open_julia_website():
                import webbrowser
                webbrowser.open('https://julialang.org/downloads/')

            ttk.Button(frame, text="Download Julia",
                      command=open_julia_website).pack(pady=10)
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
            ("⚡ Version", lambda: self.execute("VERSION")),
            ("📊 Stats", lambda: self.execute("""
                using Statistics
                println("Mean: ", mean(samples_zr))
                println("Std:  ", std(samples_zr))
            """)),
            ("📈 Plot", lambda: self._show_plot_example()),
            ("🧮 Matrix", lambda: self.execute("""
                A = [1 2; 3 4]
                println("Matrix A:")
                display(A)
                println("\\nEigenvalues: ", eigvals(A))
            """)),
            ("🔬 Geochem", lambda: self._show_geochem_example()),
        ]

        for text, cmd in commands:
            ttk.Button(quick_frame, text=text, command=cmd).pack(side=tk.LEFT, padx=2)

        # Package installer
        pkg_frame = ttk.Frame(parent)
        pkg_frame.pack(fill=tk.X, padx=5, pady=2)

        ttk.Label(pkg_frame, text="Add package:").pack(side=tk.LEFT, padx=2)
        self.pkg_var = tk.StringVar()
        pkg_entry = ttk.Entry(pkg_frame, textvariable=self.pkg_var, width=20)
        pkg_entry.pack(side=tk.LEFT, padx=2)
        ttk.Button(pkg_frame, text="Install",
                  command=self._install_package).pack(side=tk.LEFT, padx=2)
        ttk.Button(pkg_frame, text="Update",
                  command=lambda: self.execute("using Pkg; Pkg.update()")).pack(side=tk.LEFT, padx=2)

        # Input area
        input_frame = ttk.Frame(parent)
        input_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(input_frame, text="julia>", font=('Consolas', 10, 'bold')).pack(side=tk.LEFT, padx=2)

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
        self.input.bind('<Control-l>', self._clear_screen)

        # Button frame
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(button_frame, text="Run (Ctrl+Enter)",
                  command=self.execute_input).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Clear",
                  command=self._clear_screen).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Help",
                  command=self._show_help).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Cleanup",
                  command=self._cleanup_temp).pack(side=tk.LEFT, padx=2)

        # Export samples for Julia
        self._export_samples()
        self._print_welcome()

    def _export_samples(self):
        """Export samples for Julia to access"""
        samples = self.app.data_hub.get_all()
        if not samples:
            return

        # Create temporary file with samples as Julia code
        self.samples_file = tempfile.NamedTemporaryFile(
            mode='w', suffix='.jl', delete=False, encoding='utf-8'
        )

        # Write samples as Julia arrays
        with open(self.samples_file.name, 'w') as f:
            f.write("# Sample data from Scientific Toolkit\n")
            f.write("# Access with: samples_df, samples_zr, samples_nb, etc.\n\n")

            # Get all numeric columns
            numeric_cols = []
            sample_dict = samples[0]
            for key in sample_dict.keys():
                if key not in ['Sample_ID', 'Notes', 'Display_Color', 'Flag_For_Review']:
                    if isinstance(sample_dict[key], (int, float)):
                        numeric_cols.append(key)

            # Create arrays for each numeric column
            for col in numeric_cols:
                values = []
                for s in samples:
                    val = s.get(col)
                    if val is not None and isinstance(val, (int, float)):
                        values.append(str(val))
                    else:
                        values.append("NaN")

                f.write(f"samples_{col} = [{', '.join(values)}]\n")

            # Create a DataFrame if possible
            f.write("""
# Try to create a DataFrame if DataFrames is installed
try
    using DataFrames
    samples_df = DataFrame()
"""[1:])

            for col in numeric_cols:
                f.write(f"    samples_df[!, :{col}] = samples_{col}\n")

            f.write("    println(\"✓ Created samples_df DataFrame\")\n")
            f.write("catch\n")
            f.write("    println(\"ℹ️ Install DataFrames.jl for DataFrame support\")\n")
            f.write("end\n")

    def _print_welcome(self):
        """Print welcome message"""
        if not self.has_julia:
            return

        welcome = f"""
╔══════════════════════════════════════════════════════════╗
║                     Julia Console                        ║
║              {self.julia_version:<36} ║
╠══════════════════════════════════════════════════════════╣
║  Julia combines the speed of C with the ease of Python! ║
║                                                          ║
║  📊 Your data is available as:                           ║
║     samples_zr  - Zr_ppm array                          ║
║     samples_nb  - Nb_ppm array                          ║
║     samples_ba  - Ba_ppm array                          ║
║     ... and more for each numeric column                ║
║                                                          ║
║  📦 Built-in for geochemistry:                           ║
║     using Statistics  # mean, std, cor, etc.            ║
║     using LinearAlgebra # eigvals, inv, etc.            ║
║     using Plots        # Beautiful plots                ║
║                                                          ║
║  ⚡ Speed example:                                        ║
║     @time for i in 1:10_000_000                         ║
║         x = i * 2.0                                      ║
║     end  # Runs in milliseconds!                         ║
║                                                          ║
║  Examples:                                               ║
║    julia> using Statistics                               ║
║    julia> mean(samples_zr)                               ║
║    julia> cor(samples_zr, samples_nb)                    ║
║    julia> using Plots; scatter(samples_zr, samples_nb)   ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
"""
        self._print_output(welcome)

    def _show_help(self):
        """Show detailed help"""
        help_text = """
⚡ JULIA CONSOLE HELP
═══════════════════════════════════════════════════════════

BASIC SYNTAX:
  x = 5                    # Variable assignment
  arr = [1,2,3,4,5]        # Array
  matrix = [1 2; 3 4]       # Matrix
  function f(x) return x^2 end  # Function

YOUR DATA:
  samples_zr  - Array of Zr_ppm values
  samples_nb  - Array of Nb_ppm values
  samples_ba  - Array of Ba_ppm values
  etc. for all numeric columns

STATISTICS (using Statistics):
  using Statistics
  mean(samples_zr)          # Mean
  std(samples_zr)           # Standard deviation
  cor(samples_zr, samples_nb)  # Correlation
  quantile(samples_zr, 0.95)   # 95th percentile

LINEAR ALGEBRA (using LinearAlgebra):
  using LinearAlgebra
  A = [1 2; 3 4]
  eigvals(A)                 # Eigenvalues
  inv(A)                     # Inverse matrix
  A * B                      # Matrix multiplication

PLOTTING (using Plots):
  using Plots
  scatter(samples_zr, samples_nb)  # Scatter plot
  histogram(samples_zr)            # Histogram
  boxplot(samples_zr)               # Box plot
  plot(samples_zr)                  # Line plot

PERFORMANCE TIPS:
  • Use @time to measure speed: @time sum(samples_zr)
  • Use @benchmark for detailed analysis
  • Always put loops in functions for speed
  • Use .= for in-place operations

INSTALLING PACKAGES:
  using Pkg
  Pkg.add("PackageName")     # Install package
  Pkg.update()               # Update all packages
  Pkg.status()               # List installed packages

USEFUL PACKAGES FOR GEOCHEMISTRY:
  Pkg.add("DataFrames")      # Data manipulation
  Pkg.add("CSV")             # Read CSV files
  Pkg.add("Plots")           # Plotting
  Pkg.add("Statistics")      # Statistics
  Pkg.add("Distributions")   # Statistical distributions
  Pkg.add("Clustering")      # Cluster analysis
  Pkg.add("MultivariateStats") # PCA, etc.
"""
        self._print_output(help_text)

    def _show_plot_example(self):
        """Show plot example"""
        example = """
using Plots
scatter(samples_zr, samples_nb,
    xlabel = "Zr (ppm)",
    ylabel = "Nb (ppm)",
    title = "Zr-Nb Scatter Plot",
    markersize = 5,
    alpha = 0.7,
    color = :blue)
"""
        self.execute(example)

    def _show_geochem_example(self):
        """Show geochemistry example"""
        example = """
using Statistics

# Calculate ratios
zr_nb_ratio = samples_zr ./ samples_nb

println("Zr/Nb Ratio Statistics:")
println("  Mean: ", mean(zr_nb_ratio))
println("  Std:  ", std(zr_nb_ratio))
println("  Min:  ", minimum(zr_nb_ratio))
println("  Max:  ", maximum(zr_nb_ratio))

# Quick classification (example thresholds)
sinai_idx = findall(zr_nb_ratio .> 20)
egypt_idx = findall(7 .< zr_nb_ratio .< 15)

println("\\nPotential classifications:")
println("  Sinai-like: ", length(sinai_idx), " samples")
println("  Egyptian-like: ", length(egypt_idx), " samples")
"""
        self.execute(example)

    def _install_package(self):
        """Install a Julia package"""
        pkg = self.pkg_var.get().strip()
        if pkg:
            self.execute(f'using Pkg; Pkg.add("{pkg}")')
            self.pkg_var.set("")

    def execute_input(self):
        """Execute command from input"""
        code = self.input.get("1.0", tk.END).strip()
        if code:
            self.execute(code)

    def execute(self, code):
        """Execute Julia code"""
        if not code:
            return

        self.history.append(code)
        self.history_index = len(self.history)

        self._print_output(f"julia> {code}\n")
        self.input.delete("1.0", tk.END)

        # Create temporary Julia script
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jl',
                                        delete=False, encoding='utf-8') as f:
            script = f'''
# Load samples if available
if isfile("{self.samples_file.name}")
    include("{self.samples_file.name}")
    println("✓ Loaded sample data")
end

# User code
{code}

# Force display of results
if !isnothing(ans)
    println(ans)
end
'''
            f.write(script)
            script_path = f.name

        try:
            # Run Julia script
            result = subprocess.run(
                ['julia', '--color=no', '--banner=no', script_path],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.stdout:
                self._print_output(result.stdout)
            if result.stderr:
                # Filter out informational messages
                stderr = result.stderr
                if "Precompiling" not in stderr and "INFO" not in stderr:
                    self._print_output(stderr, error=True)

        except subprocess.TimeoutExpired:
            self._print_output("⏱️ Julia script timed out (30s limit)\n", error=True)
        except Exception as e:
            self._print_output(f"❌ Error: {str(e)}\n", error=True)
        finally:
            try:
                os.unlink(script_path)
            except:
                pass

        self._print_output("\n")

    def _cleanup_temp(self):
        """Clean up temporary files"""
        try:
            if self.samples_file and os.path.exists(self.samples_file.name):
                os.unlink(self.samples_file.name)
                self._print_output("✓ Cleaned up temporary files\n")
                self._export_samples()  # Create new ones
        except:
            pass

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
            self.execute_input()
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
    plugin = JuliaConsolePlugin(main_app)

    # Add to console dropdown
    if hasattr(main_app.center, 'add_console_plugin'):
        main_app.center.add_console_plugin(
            console_name="Julia",
            console_icon="⚡",
            console_instance=plugin
        )
    return None
