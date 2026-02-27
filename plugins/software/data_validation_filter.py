"""
DATA VALIDATION & FILTERING PLUGIN v1.0
================================================================================
✓ DATA VALIDATION - IoGAS-style quality checks, missing data, outliers
✓ ADVANCED FILTER - Safe expression parser for complex queries
✓ COMPACT TABBED INTERFACE - All tools in one window
✓ EXPORT TO MAIN TABLE - Seamless integration
================================================================================
"""

PLUGIN_INFO = {
    "category": "software",
    "field": "GIS & Spatial Science",
    "id": "data_validation_filter",
    "name": "Data Quality & Filter",
    "description": "IoGAS-style validation + advanced filtering in one tool",
    "icon": "✓",
    "version": "1.0",
    "requires": ["numpy", "matplotlib"],
    "author": "Merged from Sefy Levy"
}

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import numpy as np
import re
import ast
import operator
from datetime import datetime
from typing import Dict, Any, List

# ============================================================================
# SAFE FILTER EVALUATOR (from advanced_filter.py)
# ============================================================================

class FilterSyntaxError(Exception):
    """Custom exception for filter syntax errors"""
    pass

class SafeFilterEvaluator:
    """Safe expression evaluator using AST parsing - NO eval()"""

    OPERATORS = {
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
        ast.And: lambda a, b: a and b,
        ast.Or: lambda a, b: a or b,
        ast.Not: lambda a: not a,
        ast.In: lambda a, b: a in b,
        ast.NotIn: lambda a, b: a not in b,
    }

    ALLOWED_FUNCTIONS = {
        'abs': abs,
        'round': round,
        'len': len,
        'str': str,
        'float': float,
        'int': int,
        'startswith': str.startswith,
        'endswith': str.endswith,
        'contains': lambda s, sub: sub in s if isinstance(s, str) else False,
    }

    ALLOWED_CONSTANTS = {
        'True': True,
        'False': False,
        'None': None,
    }

    def __init__(self, data_context: Dict[str, Any]):
        self.context = data_context.copy()

    def evaluate(self, expression: str) -> bool:
        """Safely evaluate a boolean expression."""
        try:
            tree = ast.parse(expression, mode='eval')
            result = self._eval_node(tree.body)
            return bool(result)
        except SyntaxError as e:
            raise FilterSyntaxError(f"Syntax error: {e}")
        except Exception as e:
            raise FilterSyntaxError(f"Evaluation error: {e}")

    def _eval_node(self, node: ast.AST) -> Any:
        """Recursively evaluate an AST node."""
        if isinstance(node, ast.Constant):
            return node.value

        elif isinstance(node, ast.Name):
            if node.id in self.context:
                return self.context[node.id]
            elif node.id in self.ALLOWED_CONSTANTS:
                return self.ALLOWED_CONSTANTS[node.id]
            else:
                raise FilterSyntaxError(f"Unknown variable: {node.id}")

        elif isinstance(node, ast.Attribute):
            obj = self._eval_node(node.value)
            if hasattr(obj, node.attr):
                return getattr(obj, node.attr)
            raise FilterSyntaxError(f"Cannot access attribute {node.attr}")

        elif isinstance(node, ast.Compare):
            left = self._eval_node(node.left)
            result = True
            current_left = left

            for op, comparator in zip(node.ops, node.comparators):
                right = self._eval_node(comparator)
                if type(op) in self.OPERATORS:
                    op_func = self.OPERATORS[type(op)]
                    result = result and op_func(current_left, right)
                else:
                    raise FilterSyntaxError(f"Unsupported operator: {type(op)}")
                current_left = right
            return result

        elif isinstance(node, ast.BoolOp):
            values = [self._eval_node(v) for v in node.values]
            if isinstance(node.op, ast.And):
                return all(values)
            elif isinstance(node.op, ast.Or):
                return any(values)

        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            if isinstance(node.op, ast.Not):
                return not operand
            elif isinstance(node.op, ast.USub):
                return -operand

        elif isinstance(node, ast.Call):
            func = self._eval_node(node.func)
            func_name = getattr(func, '__name__', str(func))
            if func_name in self.ALLOWED_FUNCTIONS or callable(func):
                args = [self._eval_node(arg) for arg in node.args]
                kwargs = {kw.arg: self._eval_node(kw.value) for kw in node.keywords}
                return func(*args, **kwargs)
            else:
                raise FilterSyntaxError(f"Function not allowed: {func_name}")

        else:
            raise FilterSyntaxError(f"Unsupported syntax: {type(node)}")


# ============================================================================
# MERGED PLUGIN CLASS
# ============================================================================

class DataValidationFilterPlugin:
    """Merged Data Validation and Advanced Filter plugin"""

    def __init__(self, main_app):
        """Initialize plugin with reference to main app"""
        self.app = main_app
        self.window = None

        # Filter state
        self.filtered_samples = []
        self.filtered_indices = []

        # Validation state
        self.validation_results = {}

        # Common elements for validation
        self.TRACE_ELEMENTS = ['Zr_ppm', 'Nb_ppm', 'Ba_ppm', 'Rb_ppm', 'Cr_ppm', 'Ni_ppm',
                               'La_ppm', 'Ce_ppm', 'Nd_ppm', 'Y_ppm']
        self.MAJOR_ELEMENTS = ['SiO2', 'TiO2', 'Al2O3', 'Fe2O3', 'FeO', 'MnO',
                               'MgO', 'CaO', 'Na2O', 'K2O', 'P2O5']

    def open_window(self):
        """Open merged interface"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("Data Quality & Filter - Validation + Advanced Filter")
        self.window.geometry("900x650")
        self.window.transient(self.app.root)

        self._create_interface()
        self.window.lift()
        self.window.focus_force()

    def _create_interface(self):
        """Create compact tabbed interface"""

        # Header
        header = tk.Frame(self.window, bg="#3F51B5", height=45)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="✓🔍", font=("Arial", 18),
                bg="#3F51B5", fg="white").pack(side=tk.LEFT, padx=10)
        tk.Label(header, text="Data Quality & Filter", font=("Arial", 14, "bold"),
                bg="#3F51B5", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Label(header, text="Validation + Advanced Filter", font=("Arial", 9),
                bg="#3F51B5", fg="#FFD700").pack(side=tk.LEFT, padx=10)

        # Status indicator
        sample_count = len(self.app.samples) if self.app.samples else 0
        tk.Label(header, text=f"📊 {sample_count} samples",
                font=("Arial", 9), bg="#3F51B5", fg="white").pack(side=tk.RIGHT, padx=10)

        # Notebook for tabs
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create tabs (merged functionality)
        self._create_quick_check_tab()      # Tab 1: Quick Validation
        self._create_missing_data_tab()     # Tab 2: Missing Data Analysis
        self._create_outlier_tab()           # Tab 3: Outlier Detection
        self._create_filter_tab()            # Tab 4: Advanced Filter
        self._create_report_tab()             # Tab 5: Full Report

        # Status bar
        status = tk.Frame(self.window, bg="#ecf0f1", height=22)
        status.pack(fill=tk.X, side=tk.BOTTOM)
        status.pack_propagate(False)

        self.status_label = tk.Label(status, text="Ready", font=("Arial", 8),
                                     bg="#ecf0f1", fg="#2c3e50")
        self.status_label.pack(side=tk.LEFT, padx=5)

        # Export button in status bar
        self.export_btn = tk.Button(status, text="📤 Export to Main Table",
                                    command=self._export_to_main,
                                    bg="#9C27B0", fg="white",
                                    font=("Arial", 7), state=tk.DISABLED)
        self.export_btn.pack(side=tk.RIGHT, padx=5)

    # ============================================================================
    # TAB 1: QUICK CHECK
    # ============================================================================

    def _create_quick_check_tab(self):
        """Tab 1: Quick validation check"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📋 Quick Check")

        # Controls
        ctrl = tk.Frame(tab)
        ctrl.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(ctrl, text="Run quick validation of all samples",
                font=("Arial", 9)).pack(side=tk.LEFT, padx=5)

        tk.Button(ctrl, text="▶ Run Quick Check",
                 command=self._run_quick_check,
                 bg="#4CAF50", fg="white",
                 font=("Arial", 9, "bold"),
                 width=15).pack(side=tk.RIGHT)

        # Results area
        self.quick_frame = tk.Frame(tab)
        self.quick_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Placeholder
        self.quick_placeholder = tk.Label(self.quick_frame,
                                         text="Click 'Run Quick Check' to analyze your data",
                                         font=("Arial", 10), fg="gray")
        self.quick_placeholder.pack(expand=True)

    def _run_quick_check(self):
        """Run quick validation check"""
        samples = self.app.samples

        if not samples:
            messagebox.showwarning("No Data", "No samples to validate")
            return

        # Clear placeholder
        for widget in self.quick_frame.winfo_children():
            widget.destroy()

        # Create results display
        results_text = scrolledtext.ScrolledText(self.quick_frame,
                                                font=("Courier", 9),
                                                height=30)
        results_text.pack(fill=tk.BOTH, expand=True)

        # Generate report
        report = []
        report.append("═" * 80)
        report.append("DATA VALIDATION REPORT - QUICK CHECK")
        report.append("═" * 80)
        report.append("")

        # Basic stats
        report.append(f"Total Samples: {len(samples)}")
        report.append("")

        # Element coverage
        report.append("ELEMENT COVERAGE:")
        report.append("-" * 60)

        all_elements = self.TRACE_ELEMENTS + self.MAJOR_ELEMENTS
        for elem in all_elements[:15]:  # Limit display
            values = []
            missing = 0

            for sample in samples:
                val = sample.get(elem, '')
                if val == '' or val is None:
                    missing += 1
                else:
                    try:
                        values.append(float(val))
                    except (ValueError, TypeError):
                        missing += 1

            coverage = ((len(samples) - missing) / len(samples) * 100) if samples else 0
            status = "✓" if coverage > 90 else "⚠" if coverage > 50 else "✗"
            report.append(f"{status} {elem:15s}: {coverage:5.1f}% coverage ({len(values)}/{len(samples)} samples)")

        report.append("")

        # Classification status
        report.append("CLASSIFICATION STATUS:")
        report.append("-" * 60)

        classified = sum(1 for s in samples if s.get('Final_Classification', '').strip())
        auto_classified = sum(1 for s in samples if s.get('Auto_Classification', '').strip())
        flagged = sum(1 for s in samples if s.get('Flag_For_Review') == 'YES')

        report.append(f"Manually classified: {classified}/{len(samples)} ({classified/len(samples)*100:.1f}%)")
        report.append(f"Auto-classified:     {auto_classified}/{len(samples)} ({auto_classified/len(samples)*100:.1f}%)")
        report.append(f"Flagged for review:  {flagged}/{len(samples)} ({flagged/len(samples)*100:.1f}%)")

        report.append("")
        report.append("═" * 80)
        report.append("RECOMMENDATIONS:")
        report.append("═" * 80)

        if missing > len(samples) * 0.3:
            report.append("⚠ More than 30% missing data detected")
            report.append("  → Check Missing Data tab for details")

        if flagged > len(samples) * 0.2:
            report.append("⚠ More than 20% of samples flagged for review")
            report.append("  → Review in main table")

        if classified < len(samples):
            report.append("ℹ Not all samples have final classifications")
            report.append("  → Use Filter tab to find unclassified samples")

        # Display
        results_text.insert("1.0", "\n".join(report))
        results_text.config(state=tk.DISABLED)
        self.status_label.config(text="✓ Quick check complete")

    # ============================================================================
    # TAB 2: MISSING DATA
    # ============================================================================

    def _create_missing_data_tab(self):
        """Tab 2: Missing data analysis"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="❓ Missing Data")

        # Controls
        ctrl = tk.Frame(tab)
        ctrl.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(ctrl, text="Analyze missing data patterns",
                font=("Arial", 9)).pack(side=tk.LEFT, padx=5)

        tk.Button(ctrl, text="▶ Analyze Missing Data",
                 command=self._analyze_missing,
                 bg="#2196F3", fg="white",
                 font=("Arial", 9, "bold"),
                 width=18).pack(side=tk.RIGHT)

        # Results area
        self.missing_frame = tk.Frame(tab)
        self.missing_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _analyze_missing(self):
        """Analyze missing data patterns"""
        samples = self.app.samples

        if not samples:
            messagebox.showwarning("No Data", "No samples to analyze")
            return

        # Clear previous
        for widget in self.missing_frame.winfo_children():
            widget.destroy()

        # Analyze
        all_elements = self.TRACE_ELEMENTS + self.MAJOR_ELEMENTS
        missing_by_sample = []

        for sample in samples:
            missing_count = 0
            missing_elements = []

            for elem in all_elements:
                val = sample.get(elem, '')
                if val == '' or val is None:
                    missing_count += 1
                    missing_elements.append(elem)
                else:
                    try:
                        float(val)
                    except (ValueError, TypeError):
                        missing_count += 1
                        missing_elements.append(elem)

            if missing_count > 0:
                missing_by_sample.append({
                    'id': sample.get('Sample_ID', 'Unknown'),
                    'missing': missing_count,
                    'percent': missing_count / len(all_elements) * 100,
                    'elements': missing_elements[:5]  # First 5
                })

        if not missing_by_sample:
            tk.Label(self.missing_frame,
                    text="✓ No missing data detected!\n\nAll samples have complete data.",
                    font=("Arial", 12), fg="green").pack(expand=True)
            self.status_label.config(text="No missing data found")
            return

        # Summary
        summary = tk.Frame(self.missing_frame, bg="#f8f9fa", height=40)
        summary.pack(fill=tk.X, pady=2)
        summary.pack_propagate(False)

        tk.Label(summary,
                text=f"Found {len(missing_by_sample)} samples with missing data "
                     f"({len(missing_by_sample)/len(samples)*100:.1f}% of total)",
                font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=10)

        # Table
        tree_frame = tk.Frame(self.missing_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        tree = ttk.Treeview(tree_frame,
                           columns=('Sample ID', 'Missing', 'Percent', 'Examples'),
                           show='headings',
                           yscrollcommand=scrollbar.set)
        scrollbar.config(command=tree.yview)

        tree.heading('Sample ID', text='Sample ID')
        tree.heading('Missing', text='Missing Elements')
        tree.heading('Percent', text='% Missing')
        tree.heading('Examples', text='Examples')

        tree.column('Sample ID', width=150)
        tree.column('Missing', width=80, anchor='center')
        tree.column('Percent', width=80, anchor='center')
        tree.column('Examples', width=200)

        # Sort by missing count
        missing_by_sample.sort(key=lambda x: x['missing'], reverse=True)

        for item in missing_by_sample:
            tree.insert('', tk.END, values=(
                item['id'],
                f"{item['missing']}",
                f"{item['percent']:.1f}%",
                ", ".join(item['elements'])
            ))

        tree.pack(fill=tk.BOTH, expand=True)
        self.status_label.config(text=f"✓ Found {len(missing_by_sample)} samples with missing data")

    # ============================================================================
    # TAB 3: OUTLIER DETECTION
    # ============================================================================

    def _create_outlier_tab(self):
        """Tab 3: Outlier detection"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="⚠️ Outliers")

        # Controls
        ctrl = tk.Frame(tab)
        ctrl.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(ctrl, text="Detect statistical outliers (>3σ)",
                font=("Arial", 9)).pack(side=tk.LEFT, padx=5)

        tk.Button(ctrl, text="▶ Detect Outliers",
                 command=self._detect_outliers,
                 bg="#FF9800", fg="white",
                 font=("Arial", 9, "bold"),
                 width=15).pack(side=tk.RIGHT)

        # Results area
        self.outlier_frame = tk.Frame(tab)
        self.outlier_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _detect_outliers(self):
        """Detect statistical outliers"""
        samples = self.app.samples

        if not samples:
            messagebox.showwarning("No Data", "No samples to analyze")
            return

        # Clear previous
        for widget in self.outlier_frame.winfo_children():
            widget.destroy()

        elements = self.TRACE_ELEMENTS
        outliers = []

        for elem in elements:
            values = []
            sample_ids = []

            for sample in samples:
                val = sample.get(elem, '')
                if val and val != '':
                    try:
                        values.append(float(val))
                        sample_ids.append(sample.get('Sample_ID', 'Unknown'))
                    except (ValueError, TypeError):
                        pass

            if len(values) > 5:
                mean = np.mean(values)
                std = np.std(values)

                for i, val in enumerate(values):
                    z_score = abs((val - mean) / std) if std > 0 else 0
                    if z_score > 3:
                        outliers.append({
                            'sample': sample_ids[i],
                            'element': elem,
                            'value': val,
                            'z_score': z_score,
                            'mean': mean,
                            'std': std
                        })

        if not outliers:
            tk.Label(self.outlier_frame,
                    text="✓ No statistical outliers detected!\n\nAll values within 3σ of mean.",
                    font=("Arial", 12), fg="green").pack(expand=True)
            self.status_label.config(text="No outliers found")
            return

        # Summary
        summary = tk.Frame(self.outlier_frame, bg="#f8f9fa", height=40)
        summary.pack(fill=tk.X, pady=2)
        summary.pack_propagate(False)

        tk.Label(summary,
                text=f"Found {len(outliers)} statistical outlier(s)",
                font=("Arial", 9, "bold"), fg="orange").pack(side=tk.LEFT, padx=10)

        # Table
        tree_frame = tk.Frame(self.outlier_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        tree = ttk.Treeview(tree_frame,
                           columns=('Sample', 'Element', 'Value', 'Z-Score', 'Mean ± Std'),
                           show='headings',
                           yscrollcommand=scrollbar.set)
        scrollbar.config(command=tree.yview)

        tree.heading('Sample', text='Sample ID')
        tree.heading('Element', text='Element')
        tree.heading('Value', text='Value')
        tree.heading('Z-Score', text='Z-Score')
        tree.heading('Mean ± Std', text='Population Mean ± Std')

        for col in ('Sample', 'Element', 'Value', 'Z-Score', 'Mean ± Std'):
            tree.column(col, width=120)

        for item in outliers:
            tree.insert('', tk.END, values=(
                item['sample'],
                item['element'],
                f"{item['value']:.1f}",
                f"{item['z_score']:.2f}σ",
                f"{item['mean']:.1f} ± {item['std']:.1f}"
            ))

        tree.pack(fill=tk.BOTH, expand=True)
        self.status_label.config(text=f"✓ Found {len(outliers)} outliers")

    # ============================================================================
    # TAB 4: ADVANCED FILTER
    # ============================================================================

    def _create_filter_tab(self):
        """Tab 4: Advanced filter"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🔍 Advanced Filter")

        # Query input
        query_frame = tk.LabelFrame(tab, text="Filter Expression", padx=5, pady=5)
        query_frame.pack(fill=tk.X, padx=5, pady=5)

        self.query_text = tk.Text(query_frame, height=3, font=("Courier", 9))
        self.query_text.pack(fill=tk.X, pady=2)

        # Examples
        ex_frame = tk.Frame(query_frame)
        ex_frame.pack(fill=tk.X)

        examples = [
            ("Zr_ppm > 100", "> 100"),
            ("Cr_ppm > 2000 or Ni_ppm > 1500", "OR condition"),
            ("'BASALT' in Final_Classification", "contains text"),
            ("SiO2 > 45 and SiO2 < 52", "range"),
        ]

        for expr, desc in examples:
            btn = tk.Button(ex_frame, text=expr,
                          command=lambda e=expr: self._insert_example(e),
                          font=("Courier", 7), fg="blue",
                          cursor="hand2", bd=0)
            btn.pack(side=tk.LEFT, padx=5)

        # Buttons
        btn_frame = tk.Frame(tab)
        btn_frame.pack(pady=5)

        tk.Button(btn_frame, text="▶ Apply Filter",
                 command=self._apply_filter,
                 bg="#4CAF50", fg="white",
                 width=12).pack(side=tk.LEFT, padx=2)

        tk.Button(btn_frame, text="✓ Validate",
                 command=self._validate_filter,
                 bg="#FF9800", fg="white",
                 width=10).pack(side=tk.LEFT, padx=2)

        tk.Button(btn_frame, text="Clear",
                 command=self._clear_filter,
                 width=8).pack(side=tk.LEFT, padx=2)

        # Results
        res_frame = tk.LabelFrame(tab, text="Filter Results", padx=5, pady=5)
        res_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Summary
        self.filter_summary = tk.Label(res_frame, text="No filter applied",
                                       font=("Arial", 8), fg="gray")
        self.filter_summary.pack(anchor=tk.W)

        # Tree
        tree_frame = tk.Frame(res_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=2)

        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.filter_tree = ttk.Treeview(tree_frame,
                                        columns=('Sample ID', 'Classification', 'Zr', 'Nb', 'Cr'),
                                        show='headings',
                                        yscrollcommand=scrollbar.set,
                                        height=8)
        scrollbar.config(command=self.filter_tree.yview)

        for col in ('Sample ID', 'Classification', 'Zr', 'Nb', 'Cr'):
            self.filter_tree.heading(col, text=col)
            self.filter_tree.column(col, width=100)

        self.filter_tree.pack(fill=tk.BOTH, expand=True)

    def _insert_example(self, expr):
        """Insert example expression"""
        self.query_text.delete("1.0", tk.END)
        self.query_text.insert("1.0", expr)

    def _validate_filter(self):
        """Validate filter expression"""
        expr = self.query_text.get("1.0", tk.END).strip()
        if not expr:
            messagebox.showinfo("Validation", "No expression to validate")
            return

        if not self.app.samples:
            messagebox.showwarning("No Data", "No samples in database")
            return

        try:
            test_sample = self.app.samples[0]
            evaluator = SafeFilterEvaluator(test_sample)
            result = evaluator.evaluate(expr)
            messagebox.showinfo("Valid Expression",
                               f"✅ Expression is valid!\n\nTest on first sample: {result}")
        except FilterSyntaxError as e:
            messagebox.showerror("Syntax Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _apply_filter(self):
        """Apply filter to samples"""
        expr = self.query_text.get("1.0", tk.END).strip()

        if not expr:
            messagebox.showwarning("Empty Query", "Enter a filter expression")
            return

        samples = self.app.samples
        if not samples:
            messagebox.showwarning("No Data", "No samples to filter")
            return

        # Apply filter
        self.filtered_samples = []
        self.filtered_indices = []
        errors = []

        for i, sample in enumerate(samples):
            try:
                evaluator = SafeFilterEvaluator(sample)
                if evaluator.evaluate(expr):
                    self.filtered_samples.append(sample)
                    self.filtered_indices.append(i)
            except FilterSyntaxError as e:
                errors.append(f"Sample {i}: {e}")
            except Exception:
                errors.append(f"Sample {i}: Unexpected error")

        # Display results
        self._display_filter_results()

        # Update summary
        total = len(samples)
        matched = len(self.filtered_samples)
        self.filter_summary.config(
            text=f"✓ Found {matched} matching sample(s) ({matched/total*100:.1f}% of data)",
            fg="#27ae60" if matched > 0 else "#e74c3c"
        )

        # Enable export if results
        self.export_btn.config(state=tk.NORMAL if matched > 0 else tk.DISABLED)

        # Show errors
        if errors:
            error_msg = "\n".join(errors[:3])
            if len(errors) > 3:
                error_msg += f"\n... and {len(errors)-3} more errors"
            messagebox.showwarning("Filter Warnings", error_msg)

        self.status_label.config(text=f"✓ Filter applied: {matched} matches")

    def _display_filter_results(self):
        """Display filtered results in tree"""
        # Clear tree
        for item in self.filter_tree.get_children():
            self.filter_tree.delete(item)

        # Add filtered samples
        for sample in self.filtered_samples[:100]:
            self.filter_tree.insert('', tk.END, values=(
                sample.get('Sample_ID', 'Unknown')[:15],
                sample.get('Final_Classification',
                          sample.get('Auto_Classification', 'N/A'))[:15],
                sample.get('Zr_ppm', ''),
                sample.get('Nb_ppm', ''),
                sample.get('Cr_ppm', '')
            ))

        if len(self.filtered_samples) > 100:
            tk.Label(self.filter_tree.master,
                    text=f"... and {len(self.filtered_samples)-100} more",
                    fg="gray", font=("Arial", 7)).pack()

    def _clear_filter(self):
        """Clear filter and results"""
        self.query_text.delete("1.0", tk.END)
        self.filtered_samples = []
        self.filtered_indices = []
        self.filter_summary.config(text="No filter applied", fg="gray")
        self.export_btn.config(state=tk.DISABLED)

        for item in self.filter_tree.get_children():
            self.filter_tree.delete(item)

        self.status_label.config(text="Filter cleared")

    # ============================================================================
    # TAB 5: FULL REPORT
    # ============================================================================

    def _create_report_tab(self):
        """Tab 5: Full validation report"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📄 Full Report")

        # Controls
        ctrl = tk.Frame(tab)
        ctrl.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(ctrl, text="Generate comprehensive validation report",
                font=("Arial", 9)).pack(side=tk.LEFT, padx=5)

        tk.Button(ctrl, text="▶ Generate Report",
                 command=self._generate_full_report,
                 bg="#9C27B0", fg="white",
                 font=("Arial", 9, "bold"),
                 width=15).pack(side=tk.RIGHT)

        # Report area
        self.report_frame = tk.Frame(tab)
        self.report_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Placeholder
        self.report_placeholder = tk.Label(self.report_frame,
                                          text="Click 'Generate Report' for full analysis",
                                          font=("Arial", 10), fg="gray")
        self.report_placeholder.pack(expand=True)

    def _generate_full_report(self):
        """Generate full validation report"""
        samples = self.app.samples

        if not samples:
            messagebox.showwarning("No Data", "No samples to analyze")
            return

        # Clear placeholder
        for widget in self.report_frame.winfo_children():
            widget.destroy()

        # Create report text
        report_text = scrolledtext.ScrolledText(self.report_frame,
                                                font=("Courier", 8),
                                                height=30)
        report_text.pack(fill=tk.BOTH, expand=True)

        # Generate report
        report = []
        report.append("═" * 80)
        report.append("COMPREHENSIVE DATA VALIDATION REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("═" * 80)
        report.append("")

        # Section 1: Overview
        report.append("1. DATASET OVERVIEW")
        report.append("-" * 60)
        report.append(f"Total Samples: {len(samples)}")
        report.append(f"Total Columns: {len(samples[0]) if samples else 0}")
        report.append("")

        # Section 2: Element Coverage
        report.append("2. ELEMENT COVERAGE")
        report.append("-" * 60)

        all_elements = self.TRACE_ELEMENTS + self.MAJOR_ELEMENTS
        for elem in all_elements:
            present = sum(1 for s in samples if elem in s)
            pct = present / len(samples) * 100
            report.append(f"{elem:15s}: {present:3d}/{len(samples)} samples ({pct:5.1f}%)")

        report.append("")

        # Section 3: Missing Data
        report.append("3. MISSING DATA SUMMARY")
        report.append("-" * 60)

        missing_counts = []
        for sample in samples:
            missing = 0
            for elem in all_elements[:10]:  # Limit for readability
                if elem not in sample:
                    missing += 1
            missing_counts.append(missing)

        if missing_counts:
            report.append(f"Samples with missing data: {sum(1 for m in missing_counts if m > 0)}")
            report.append(f"Average missing elements: {np.mean(missing_counts):.1f}")
            report.append(f"Max missing elements: {max(missing_counts)}")

        report.append("")

        # Section 4: Outliers
        report.append("4. OUTLIER SUMMARY")
        report.append("-" * 60)

        outlier_count = 0
        for elem in self.TRACE_ELEMENTS:
            values = []
            for s in samples:
                val = s.get(elem, '')
                if val and val != '':
                    try:
                        values.append(float(val))
                    except:
                        pass

            if len(values) > 5:
                mean = np.mean(values)
                std = np.std(values)
                outliers = sum(1 for v in values if abs(v - mean) > 3 * std)
                if outliers > 0:
                    outlier_count += outliers
                    report.append(f"{elem:15s}: {outliers} outliers ({outliers/len(values)*100:.1f}%)")

        report.append("")
        report.append(f"Total outliers detected: {outlier_count}")

        # Section 5: Recommendations
        report.append("")
        report.append("5. RECOMMENDATIONS")
        report.append("-" * 60)

        if outlier_count > 10:
            report.append("• Multiple outliers detected - review in Outliers tab")

        if any(m > 5 for m in missing_counts):
            report.append("• Significant missing data - check Missing Data tab")

        report.append("• Use Advanced Filter to subset data for analysis")
        report.append("• Export filtered data to main table for further work")

        # Display
        report_text.insert("1.0", "\n".join(report))
        report_text.config(state=tk.DISABLED)
        self.status_label.config(text="✓ Full report generated")

    # ============================================================================
    # EXPORT FUNCTION
    # ============================================================================

    def _export_to_main(self):
        """Export filtered samples to main table"""
        if not self.filtered_samples:
            messagebox.showwarning("No Results", "No filtered samples to export")
            return

        # Prepare data for main app
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        query = self.query_text.get("1.0", tk.END).strip()
        export_data = []

        for sample in self.filtered_samples:
            row = {
                'Sample_ID': sample.get('Sample_ID', 'Unknown'),
                'Timestamp': timestamp,
                'Source': 'Advanced Filter',
                'Plugin': PLUGIN_INFO['name'],
                'Notes': f"Filtered using: {query}" if query else "Filtered results"
            }

            # Copy all original data
            for key, value in sample.items():
                if key not in row:
                    row[key] = value

            export_data.append(row)

        # Send to main app
        if hasattr(self.app, 'import_data_from_plugin'):
            self.app.import_data_from_plugin(export_data)
            messagebox.showinfo("Success",
                              f"✅ Exported {len(export_data)} filtered samples to main table")
            self.status_label.config(text=f"✓ Exported {len(export_data)} samples")
        else:
            messagebox.showerror("Error", "Main app doesn't support plugin data import")


def setup_plugin(main_app):
    """Plugin setup function"""
    plugin = DataValidationFilterPlugin(main_app)
    return plugin
