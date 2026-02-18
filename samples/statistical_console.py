"""
Statistical Console - Easy statistics for non-programmers
"""
import tkinter as tk
from tkinter import ttk
import statistics
import math
import re
from collections import Counter

PLUGIN_INFO = {
    'id': 'statistical_console',
    'name': 'Statistical Console',
    'category': 'console',
    'icon': '📊',
    'version': '1.0',
    'description': 'Simple statistical commands for data analysis'
}

class StatisticalConsolePlugin:
    def __init__(self, main_app):
        self.app = main_app
        self.history = []
        self.history_index = -1
        self.data = None  # Will hold current samples
        self.numeric_columns = []  # Will be populated

    def create_tab(self, parent):
        """Create statistical console UI"""
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
            ("📊 Summary", self._cmd_summary),
            ("📈 Describe", self._cmd_describe_all),
            ("🔍 Correlate", self._cmd_correlate),
            ("📋 Groups", self._cmd_groups),
            ("📉 T-Test", self._cmd_ttest),
        ]

        for text, cmd in commands:
            ttk.Button(quick_frame, text=text, command=cmd).pack(side=tk.LEFT, padx=2)

        # Input area
        input_frame = ttk.Frame(parent)
        input_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(input_frame, text="📊>", font=('Consolas', 10, 'bold')).pack(side=tk.LEFT, padx=2)

        self.input = tk.Text(
            input_frame,
            height=2,
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

        ttk.Button(button_frame, text="Run",
                  command=self.execute_input).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Clear",
                  command=self._clear_screen).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Help",
                  command=self._show_help).pack(side=tk.LEFT, padx=2)

        # Update data reference
        self._update_data()
        self._print_welcome()

    def _update_data(self):
        """Get current samples and identify numeric columns"""
        self.data = self.app.data_hub.get_all()
        if not self.data:
            return

        # Find numeric columns
        if self.data:
            sample = self.data[0]
            self.numeric_columns = [
                col for col in sample.keys()
                if col not in ['Sample_ID', 'Notes', 'Display_Color', 'Flag_For_Review']
                and isinstance(sample[col], (int, float))
            ]

    def _get_values(self, column):
        """Get numeric values for a column, filtering out None"""
        if not self.data:
            return []
        values = []
        for s in self.data:
            val = s.get(column)
            if val is not None and isinstance(val, (int, float)):
                values.append(float(val))
        return values

    def _get_groups(self, column, group_col='Auto_Classification'):
        """Get values grouped by classification"""
        groups = {}
        for s in self.data:
            group = s.get(group_col, 'UNCLASSIFIED')
            val = s.get(column)
            if val is not None and isinstance(val, (int, float)):
                if group not in groups:
                    groups[group] = []
                groups[group].append(float(val))
        return groups

    def _print_welcome(self):
        """Print welcome message"""
        if not self.data:
            welcome = """
╔══════════════════════════════════════════════════════════╗
║                 Statistical Console                      ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  ⚠️ No data loaded                                        ║
║                                                          ║
║  Import samples first using the left panel.             ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
"""
        else:
            welcome = f"""
╔══════════════════════════════════════════════════════════╗
║                 Statistical Console                      ║
╠══════════════════════════════════════════════════════════╣
║  📊 Samples: {len(self.data)} total                       ║
║  📈 Numeric columns: {len(self.numeric_columns)}          ║
║                                                          ║
║  Available commands:                                     ║
║    mean <col>              - Calculate mean             ║
║    median <col>            - Calculate median           ║
║    std <col>               - Standard deviation         ║
║    summary <col>           - All statistics             ║
║    describe                - Describe all columns       ║
║    correlate <col1> <col2> - Correlation                ║
║    ttest <col> by <group>  - T-test between groups      ║
║    groups <col>            - Statistics by group        ║
║    histogram <col>         - Show distribution          ║
║    outliers <col>          - Find outliers              ║
║                                                          ║
║  Examples:                                               ║
║    >>> mean Zr_ppm                                       ║
║    >>> correlate Zr_ppm Nb_ppm                           ║
║    >>> ttest Zr_ppm by Auto_Classification              ║
║    >>> groups Zr_ppm                                     ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
"""
        self._print_output(welcome)

    def _show_help(self):
        """Show detailed help"""
        help_text = """
📊 STATISTICAL CONSOLE HELP
═══════════════════════════════════════════════════════════

BASIC STATISTICS:
  mean <column>              - Arithmetic mean
  median <column>            - Median value
  mode <column>              - Most common value
  std <column>               - Standard deviation
  var <column>               - Variance
  min <column>               - Minimum value
  max <column>               - Maximum value
  range <column>             - Range (max - min)
  sum <column>               - Sum of all values
  count <column>             - Number of values
  summary <column>           - All basic statistics

MULTIVARIATE:
  correlate <col1> <col2>    - Pearson correlation
  covariance <col1> <col2>    - Covariance
  describe                   - Statistics for all columns

GROUP ANALYSIS:
  groups <col>               - Statistics by classification
  ttest <col> by <groupcol>  - T-test between groups
  anova <col> by <groupcol>  - One-way ANOVA

DATA QUALITY:
  outliers <col>             - Find outliers (IQR method)
  missing <col>              - Count missing values
  unique <col>               - Count unique values
  freq <col>                 - Frequency table

DISTRIBUTIONS:
  histogram <col>            - Show distribution
  quantile <col> <q>         - Calculate quantile
  iqr <col>                  - Interquartile range
  skew <col>                 - Skewness
  kurtosis <col>             - Kurtosis

EXAMPLES:
  >>> mean Zr_ppm
  >>> correlate Zr_ppm Nb_ppm
  >>> ttest Zr_ppm by Auto_Classification
  >>> outliers Ba_ppm
  >>> groups Zr_ppm
"""
        self._print_output(help_text)

    def _cmd_summary(self):
        """Quick command for summary"""
        self.input.delete("1.0", tk.END)
        self.input.insert("1.0", "summary Zr_ppm")
        self.execute_input()

    def _cmd_describe_all(self):
        """Quick command for describe all"""
        self.input.delete("1.0", tk.END)
        self.input.insert("1.0", "describe")
        self.execute_input()

    def _cmd_correlate(self):
        """Quick command for correlation"""
        if len(self.numeric_columns) >= 2:
            self.input.delete("1.0", tk.END)
            self.input.insert("1.0", f"correlate {self.numeric_columns[0]} {self.numeric_columns[1]}")
            self.execute_input()

    def _cmd_groups(self):
        """Quick command for groups"""
        if self.numeric_columns:
            self.input.delete("1.0", tk.END)
            self.input.insert("1.0", f"groups {self.numeric_columns[0]}")
            self.execute_input()

    def _cmd_ttest(self):
        """Quick command for t-test"""
        if self.numeric_columns:
            self.input.delete("1.0", tk.END)
            self.input.insert("1.0", f"ttest {self.numeric_columns[0]} by Auto_Classification")
            self.execute_input()

    def execute_input(self):
        """Execute command from input"""
        cmd = self.input.get("1.0", tk.END).strip()
        if cmd:
            self.execute(cmd)

    def execute(self, cmd):
        """Execute statistical command"""
        if not cmd:
            return

        self.history.append(cmd)
        self.history_index = len(self.history)

        self._print_output(f"📊> {cmd}\n")
        self.input.delete("1.0", tk.END)

        # Update data reference
        self._update_data()

        if not self.data:
            self._print_output("No data loaded. Import samples first.\n")
            self._print_output("\n")
            return

        # Parse and execute command
        parts = cmd.lower().split()
        if not parts:
            return

        command = parts[0]
        result = None

        try:
            if command == 'mean':
                result = self._cmd_mean(parts)
            elif command == 'median':
                result = self._cmd_median(parts)
            elif command == 'mode':
                result = self._cmd_mode(parts)
            elif command == 'std':
                result = self._cmd_std(parts)
            elif command == 'var':
                result = self._cmd_var(parts)
            elif command == 'min':
                result = self._cmd_min(parts)
            elif command == 'max':
                result = self._cmd_max(parts)
            elif command == 'range':
                result = self._cmd_range(parts)
            elif command == 'sum':
                result = self._cmd_sum(parts)
            elif command == 'count':
                result = self._cmd_count(parts)
            elif command == 'summary':
                result = self._cmd_summary_col(parts)
            elif command == 'describe':
                result = self._cmd_describe()
            elif command == 'correlate' or command == 'cor':
                result = self._cmd_correlate_cols(parts)
            elif command == 'covariance' or command == 'cov':
                result = self._cmd_covariance(parts)
            elif command == 'groups':
                result = self._cmd_groups_col(parts)
            elif command == 'ttest':
                result = self._cmd_ttest_col(parts)
            elif command == 'outliers':
                result = self._cmd_outliers(parts)
            elif command == 'missing':
                result = self._cmd_missing(parts)
            elif command == 'unique':
                result = self._cmd_unique(parts)
            elif command == 'histogram':
                result = self._cmd_histogram(parts)
            elif command == 'quantile':
                result = self._cmd_quantile(parts)
            elif command == 'iqr':
                result = self._cmd_iqr(parts)
            elif command == 'help':
                self._show_help()
                return
            else:
                result = f"Unknown command: {command}\nType 'help' for available commands"

            if result:
                self._print_output(result)

        except Exception as e:
            self._print_output(f"Error: {str(e)}\n", error=True)

        self._print_output("\n")

    def _get_column_name(self, parts, expected_pos=1):
        """Extract column name from command parts"""
        if len(parts) <= expected_pos:
            return None
        return parts[expected_pos]

    def _format_number(self, value):
        """Format number nicely"""
        if isinstance(value, float):
            if abs(value) < 0.01 or abs(value) > 1000:
                return f"{value:.2e}"
            else:
                return f"{value:.3f}".rstrip('0').rstrip('.')
        return str(value)

    # Statistical commands
    def _cmd_mean(self, parts):
        col = self._get_column_name(parts)
        if not col:
            return "Usage: mean <column>"
        values = self._get_values(col)
        if not values:
            return f"No numeric data in '{col}'"
        mean_val = statistics.mean(values)
        return f"Mean of {col}: {self._format_number(mean_val)} (n={len(values)})"

    def _cmd_median(self, parts):
        col = self._get_column_name(parts)
        if not col:
            return "Usage: median <column>"
        values = self._get_values(col)
        if not values:
            return f"No numeric data in '{col}'"
        median_val = statistics.median(values)
        return f"Median of {col}: {self._format_number(median_val)} (n={len(values)})"

    def _cmd_mode(self, parts):
        col = self._get_column_name(parts)
        if not col:
            return "Usage: mode <column>"
        values = self._get_values(col)
        if not values:
            return f"No numeric data in '{col}'"
        try:
            mode_val = statistics.mode(values)
            return f"Mode of {col}: {self._format_number(mode_val)}"
        except statistics.StatisticsError:
            return f"No unique mode found for {col}"

    def _cmd_std(self, parts):
        col = self._get_column_name(parts)
        if not col:
            return "Usage: std <column>"
        values = self._get_values(col)
        if len(values) < 2:
            return f"Need at least 2 values for std dev in '{col}'"
        std_val = statistics.stdev(values)
        return f"Standard deviation of {col}: {self._format_number(std_val)} (n={len(values)})"

    def _cmd_var(self, parts):
        col = self._get_column_name(parts)
        if not col:
            return "Usage: var <column>"
        values = self._get_values(col)
        if len(values) < 2:
            return f"Need at least 2 values for variance in '{col}'"
        var_val = statistics.variance(values)
        return f"Variance of {col}: {self._format_number(var_val)} (n={len(values)})"

    def _cmd_min(self, parts):
        col = self._get_column_name(parts)
        if not col:
            return "Usage: min <column>"
        values = self._get_values(col)
        if not values:
            return f"No numeric data in '{col}'"
        min_val = min(values)
        return f"Minimum of {col}: {self._format_number(min_val)}"

    def _cmd_max(self, parts):
        col = self._get_column_name(parts)
        if not col:
            return "Usage: max <column>"
        values = self._get_values(col)
        if not values:
            return f"No numeric data in '{col}'"
        max_val = max(values)
        return f"Maximum of {col}: {self._format_number(max_val)}"

    def _cmd_range(self, parts):
        col = self._get_column_name(parts)
        if not col:
            return "Usage: range <column>"
        values = self._get_values(col)
        if not values:
            return f"No numeric data in '{col}'"
        range_val = max(values) - min(values)
        return f"Range of {col}: {self._format_number(range_val)}"

    def _cmd_sum(self, parts):
        col = self._get_column_name(parts)
        if not col:
            return "Usage: sum <column>"
        values = self._get_values(col)
        if not values:
            return f"No numeric data in '{col}'"
        sum_val = sum(values)
        return f"Sum of {col}: {self._format_number(sum_val)} (n={len(values)})"

    def _cmd_count(self, parts):
        col = self._get_column_name(parts)
        if not col:
            return "Usage: count <column>"
        values = self._get_values(col)
        return f"Count of {col}: {len(values)} non-null values"

    def _cmd_summary_col(self, parts):
        col = self._get_column_name(parts)
        if not col:
            return "Usage: summary <column>"
        values = self._get_values(col)
        if not values:
            return f"No numeric data in '{col}'"

        lines = [f"\n📊 Summary for {col}:"]
        lines.append("-" * 40)
        lines.append(f"Count:   {len(values)}")
        lines.append(f"Mean:    {self._format_number(statistics.mean(values))}")
        lines.append(f"Median:  {self._format_number(statistics.median(values))}")
        if len(values) > 1:
            lines.append(f"StdDev:  {self._format_number(statistics.stdev(values))}")
        lines.append(f"Min:     {self._format_number(min(values))}")
        lines.append(f"Max:     {self._format_number(max(values))}")
        lines.append(f"Range:   {self._format_number(max(values) - min(values))}")
        lines.append(f"Sum:     {self._format_number(sum(values))}")

        # Add quartiles
        values.sort()
        q1 = values[len(values)//4]
        q3 = values[3*len(values)//4]
        lines.append(f"Q1:      {self._format_number(q1)}")
        lines.append(f"Q3:      {self._format_number(q3)}")
        lines.append(f"IQR:     {self._format_number(q3 - q1)}")

        return "\n".join(lines)

    def _cmd_describe(self):
        """Describe all numeric columns"""
        if not self.numeric_columns:
            return "No numeric columns found"

        lines = ["\n📈 Summary of all numeric columns:"]
        lines.append("=" * 60)

        # Header
        header = f"{'Column':<15} {'Count':>6} {'Mean':>10} {'StdDev':>10} {'Min':>8} {'Max':>8}"
        lines.append(header)
        lines.append("-" * 60)

        for col in self.numeric_columns:
            values = self._get_values(col)
            if values:
                mean_val = statistics.mean(values)
                if len(values) > 1:
                    std_val = statistics.stdev(values)
                else:
                    std_val = 0
                lines.append(
                    f"{col:<15} {len(values):>6} {mean_val:>10.2f} {std_val:>10.2f} "
                    f"{min(values):>8.1f} {max(values):>8.1f}"
                )

        return "\n".join(lines)

    def _cmd_correlate_cols(self, parts):
        if len(parts) < 3:
            return "Usage: correlate <column1> <column2>"
        col1, col2 = parts[1], parts[2]

        values1 = self._get_values(col1)
        values2 = self._get_values(col2)

        if not values1 or not values2:
            return "One or both columns have no numeric data"

        # Pair up values by index
        pairs = []
        for i, s in enumerate(self.data):
            v1 = s.get(col1)
            v2 = s.get(col2)
            if v1 is not None and v2 is not None and isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                pairs.append((float(v1), float(v2)))

        if len(pairs) < 3:
            return "Need at least 3 paired values for correlation"

        # Calculate correlation
        n = len(pairs)
        sum_x = sum(p[0] for p in pairs)
        sum_y = sum(p[1] for p in pairs)
        sum_xy = sum(p[0] * p[1] for p in pairs)
        sum_x2 = sum(p[0]**2 for p in pairs)
        sum_y2 = sum(p[1]**2 for p in pairs)

        numerator = n * sum_xy - sum_x * sum_y
        denominator = math.sqrt((n * sum_x2 - sum_x**2) * (n * sum_y2 - sum_y**2))

        if denominator == 0:
            return "Correlation undefined (denominator zero)"

        r = numerator / denominator

        # Interpret correlation
        strength = ""
        abs_r = abs(r)
        if abs_r < 0.3:
            strength = "weak"
        elif abs_r < 0.7:
            strength = "moderate"
        else:
            strength = "strong"

        direction = "positive" if r > 0 else "negative"

        return f"""
Correlation: {col1} vs {col2}
  r = {r:.4f}
  n = {n}
  {strength.capitalize()} {direction} correlation
  r² = {r*r:.4f} ({r*r*100:.1f}% of variance explained)"""

    def _cmd_groups_col(self, parts):
        col = self._get_column_name(parts)
        if not col:
            return "Usage: groups <column>"

        groups = self._get_groups(col)
        if not groups:
            return f"No grouped data for {col}"

        lines = [f"\n📊 {col} by Classification:"]
        lines.append("=" * 60)

        for group, values in sorted(groups.items()):
            if len(values) > 0:
                lines.append(f"\n{group}:")
                lines.append(f"  n = {len(values)}")
                lines.append(f"  mean = {statistics.mean(values):.2f}")
                if len(values) > 1:
                    lines.append(f"  std = {statistics.stdev(values):.2f}")
                lines.append(f"  min = {min(values):.2f}")
                lines.append(f"  max = {max(values):.2f}")

        return "\n".join(lines)

    def _cmd_ttest_col(self, parts):
        """Simple t-test between two groups"""
        # Parse: ttest <col> by <groupcol>
        # For simplicity, assume groups are in Auto_Classification
        if len(parts) < 4 or parts[2] != 'by':
            return "Usage: ttest <column> by <groupcolumn>"

        col = parts[1]
        group_col = parts[3]

        groups = self._get_groups(col, group_col)
        if len(groups) < 2:
            return "Need at least 2 groups for t-test"

        # Take first two groups for simplicity
        group_names = list(groups.keys())[:2]
        group1, group2 = group_names
        values1 = groups[group1]
        values2 = groups[group2]

        if len(values1) < 2 or len(values2) < 2:
            return "Each group needs at least 2 values"

        # Calculate t-statistic (Welch's t-test)
        mean1 = statistics.mean(values1)
        mean2 = statistics.mean(values2)
        var1 = statistics.variance(values1)
        var2 = statistics.variance(values2)
        n1, n2 = len(values1), len(values2)

        t = (mean1 - mean2) / math.sqrt(var1/n1 + var2/n2)

        # Degrees of freedom (Welch–Satterthwaite)
        df = (var1/n1 + var2/n2)**2 / (
            (var1/n1)**2/(n1-1) + (var2/n2)**2/(n2-1)
        )

        # Rough p-value approximation (simplified)
        from scipy.stats import t as t_dist
        try:
            p = 2 * t_dist.cdf(-abs(t), df)
        except:
            p = "N/A"

        return f"""
T-Test: {col}
  {group1}: n={n1}, mean={mean1:.2f}, var={var1:.2f}
  {group2}: n={n2}, mean={mean2:.2f}, var={var2:.2f}

  t = {t:.4f}
  df = {df:.1f}
  p = {p if p == "N/A" else f"{p:.4f}"}

  {'Significant difference' if p != "N/A" and p < 0.05 else 'No significant difference'} (α=0.05)"""

    def _cmd_outliers(self, parts):
        col = self._get_column_name(parts)
        if not col:
            return "Usage: outliers <column>"

        values = self._get_values(col)
        if len(values) < 4:
            return "Need at least 4 values to detect outliers"

        # IQR method
        values.sort()
        q1 = values[len(values)//4]
        q3 = values[3*len(values)//4]
        iqr = q3 - q1

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outliers = [v for v in values if v < lower_bound or v > upper_bound]

        if not outliers:
            return f"No outliers detected in {col} (IQR method)"
        else:
            return f"Outliers in {col}: {', '.join(self._format_number(v) for v in outliers)}"

    def _cmd_missing(self, parts):
        col = self._get_column_name(parts)
        if not col:
            return "Usage: missing <column>"

        missing = sum(1 for s in self.data if s.get(col) is None)
        total = len(self.data)
        pct = (missing / total) * 100

        return f"Missing values in {col}: {missing}/{total} ({pct:.1f}%)"

    def _cmd_unique(self, parts):
        col = self._get_column_name(parts)
        if not col:
            return "Usage: unique <column>"

        values = [s.get(col) for s in self.data if s.get(col) is not None]
        unique_vals = set(values)

        return f"Unique values in {col}: {len(unique_vals)}"

    def _cmd_histogram(self, parts):
        col = self._get_column_name(parts)
        if not col:
            return "Usage: histogram <column>"

        values = self._get_values(col)
        if not values:
            return f"No numeric data in '{col}'"

        # Create simple text histogram
        bins = 10
        min_val, max_val = min(values), max(values)
        bin_width = (max_val - min_val) / bins if max_val > min_val else 1

        hist = [0] * bins
        for v in values:
            idx = min(int((v - min_val) / bin_width), bins - 1)
            hist[idx] += 1

        max_count = max(hist)

        lines = [f"\n📊 Histogram of {col} (n={len(values)})"]
        lines.append("-" * 40)

        for i in range(bins):
            bin_start = min_val + i * bin_width
            bin_end = bin_start + bin_width
            count = hist[i]
            bar_length = int(30 * count / max_count) if max_count > 0 else 0
            bar = "█" * bar_length

            lines.append(f"{bin_start:8.1f}-{bin_end:8.1f}: {bar} ({count})")

        return "\n".join(lines)

    def _cmd_quantile(self, parts):
        if len(parts) < 3:
            return "Usage: quantile <column> <q>"
        col = parts[1]
        try:
            q = float(parts[2])
            if q < 0 or q > 1:
                return "Quantile must be between 0 and 1"
        except:
            return "Quantile must be a number"

        values = self._get_values(col)
        if not values:
            return f"No numeric data in '{col}'"

        values.sort()
        idx = int(q * (len(values) - 1))
        quantile_val = values[idx]

        return f"{q*100:.0f}th percentile of {col}: {self._format_number(quantile_val)}"

    def _cmd_iqr(self, parts):
        col = self._get_column_name(parts)
        if not col:
            return "Usage: iqr <column>"

        values = self._get_values(col)
        if len(values) < 4:
            return "Need at least 4 values for IQR"

        values.sort()
        q1 = values[len(values)//4]
        q3 = values[3*len(values)//4]
        iqr = q3 - q1

        return f"Interquartile range of {col}: {self._format_number(iqr)}"

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

    def _clear_screen(self):
        """Clear output"""
        self.output.config(state=tk.NORMAL)
        self.output.delete("1.0", tk.END)
        self.output.config(state=tk.DISABLED)
        self._print_welcome()

def register_plugin(main_app):
    """Register this plugin"""
    plugin = StatisticalConsolePlugin(main_app)

    if hasattr(main_app.center, 'add_console_plugin'):
        main_app.center.add_console_plugin(
            console_name="Statistics",
            console_icon="📊",
            console_instance=plugin
        )
    return None
