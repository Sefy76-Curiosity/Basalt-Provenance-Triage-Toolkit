"""
Advanced Filter Plugin for Scientific Toolkit v2.0
Safe expression parser - follows working plugin pattern
Author: Sefy Levy
"""

PLUGIN_INFO = {
    "category": "software",
    "id": "advanced_filter",
    "name": "Advanced Filter",
    "description": "Safe logical query language for complex data filtering",
    "icon": "🔍",
    "version": "2.0",
    "requires": [],
    "author": "Sefy Levy"
}

import tkinter as tk
from tkinter import ttk, messagebox
import re
import ast
import operator
from typing import Dict, Any, List
from datetime import datetime

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


class AdvancedFilterPlugin:
    """Plugin for advanced logical filtering - SAFE VERSION"""

    def __init__(self, main_app):
        """Initialize plugin with reference to main app"""
        self.app = main_app
        self.window = None
        self.filtered_samples = []
        self.filtered_indices = []

    def open_window(self):
        """Open the advanced filter interface - CRITICAL: This is what the menu calls"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("Advanced Filter - Safe Query Language")
        self.window.geometry("800x600")
        self.window.transient(self.app.root)

        self._create_interface()
        self.window.lift()
        self.window.focus_force()

    def _create_interface(self):
        """Create the filter interface"""
        # Header
        header = tk.Frame(self.window, bg="#3F51B5", height=40)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="🔍", font=("Arial", 16),
                bg="#3F51B5", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Label(header, text="Advanced Filter", font=("Arial", 14, "bold"),
                bg="#3F51B5", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Label(header, text="Safe Expression Parser", font=("Arial", 9),
                bg="#3F51B5", fg="#FFD700").pack(side=tk.LEFT, padx=10)

        # Main content
        content = tk.Frame(self.window, padx=10, pady=8)
        content.pack(fill=tk.BOTH, expand=True)

        # Query input
        query_frame = tk.LabelFrame(content, text="Filter Expression",
                                   font=("Arial", 10, "bold"),
                                   padx=10, pady=5)
        query_frame.pack(fill=tk.X, pady=5)

        tk.Label(query_frame, text="Enter your query:",
                font=("Arial", 9)).pack(anchor=tk.W)

        self.query_text = tk.Text(query_frame, height=4, font=("Courier", 10))
        self.query_text.pack(fill=tk.X, pady=5)

        # Examples
        examples_frame = tk.Frame(query_frame)
        examples_frame.pack(fill=tk.X, pady=2)

        tk.Label(examples_frame, text="Examples:",
                font=("Arial", 8, "bold")).pack(side=tk.LEFT, padx=2)

        examples = [
            ("Zr_ppm > 100", "> 100"),
            ("Nb_ppm < 20", "< 20"),
            ("Cr_ppm > 2000 or Ni_ppm > 1500", "OR condition"),
            ("'HADDADIN' in Final_Classification", "contains text"),
        ]

        for expr, desc in examples:
            btn = tk.Button(examples_frame, text=expr,
                          command=lambda e=expr: self._insert_example(e),
                          font=("Courier", 8), fg="blue",
                          cursor="hand2", bd=0)
            btn.pack(side=tk.LEFT, padx=5)

        # Buttons
        btn_frame = tk.Frame(content)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="▶ Apply Filter",
                 command=self._apply_filter,
                 bg="#4CAF50", fg="white",
                 font=("Arial", 11, "bold"),
                 width=15, height=2).pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame, text="✓ Validate",
                 command=self._validate_expression,
                 bg="#FF9800", fg="white",
                 width=10, height=2).pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame, text="Clear",
                 command=self._clear_query,
                 width=8, height=2).pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame, text="📤 Export",
                 command=self._export_filtered,
                 bg="#9C27B0", fg="white",
                 width=10, height=2).pack(side=tk.RIGHT, padx=5)

        # Results
        results_frame = tk.LabelFrame(content, text="Results",
                                     font=("Arial", 10, "bold"),
                                     padx=10, pady=5)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Summary
        self.summary_label = tk.Label(results_frame, text="No filter applied",
                                     font=("Arial", 9, "bold"),
                                     fg="gray")
        self.summary_label.pack(anchor=tk.W, pady=2)

        # Treeview for results
        tree_frame = tk.Frame(results_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        columns = ('Sample ID', 'Classification', 'Zr', 'Nb', 'Cr', 'Ni')
        self.results_tree = ttk.Treeview(tree_frame, columns=columns,
                                         show='headings',
                                         yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.results_tree.yview)

        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=100)

        self.results_tree.pack(fill=tk.BOTH, expand=True)

    def _insert_example(self, expr):
        """Insert example expression"""
        self.query_text.delete("1.0", tk.END)
        self.query_text.insert("1.0", expr)

    def _validate_expression(self):
        """Validate expression syntax"""
        expr = self.query_text.get("1.0", tk.END).strip()
        if not expr:
            messagebox.showinfo("Validation", "No expression to validate")
            return

        if not self.app.samples:
            messagebox.showwarning("No Data", "No samples in database")
            return

        try:
            # Test on first sample
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
            messagebox.showwarning("Empty Query", "Please enter a filter expression")
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
            except Exception as e:
                errors.append(f"Sample {i}: Unexpected error")

        # Display results
        self._display_results()

        # Update summary
        total = len(samples)
        matched = len(self.filtered_samples)
        self.summary_label.config(
            text=f"✓ Found {matched} matching sample(s) ({matched/total*100:.1f}% of data)",
            fg="#27ae60" if matched > 0 else "#e74c3c"
        )

        # Show errors if any
        if errors:
            error_msg = "\n".join(errors[:5])
            if len(errors) > 5:
                error_msg += f"\n... and {len(errors)-5} more errors"
            messagebox.showwarning("Filter Warnings",
                                 f"Filter applied with {len(errors)} warnings:\n\n{error_msg}")

    def _display_results(self):
        """Display filtered results in tree"""
        # Clear tree
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        # Add filtered samples
        for sample in self.filtered_samples[:100]:  # Limit display
            self.results_tree.insert('', tk.END, values=(
                sample.get('Sample_ID', 'Unknown')[:15],
                sample.get('Final_Classification',
                          sample.get('Auto_Classification', 'N/A'))[:20],
                sample.get('Zr_ppm', ''),
                sample.get('Nb_ppm', ''),
                sample.get('Cr_ppm', ''),
                sample.get('Ni_ppm', '')
            ))

        if len(self.filtered_samples) > 100:
            tk.Label(self.results_tree.master,
                    text=f"... and {len(self.filtered_samples)-100} more",
                    fg="gray").pack()

    def _clear_query(self):
        """Clear query and results"""
        self.query_text.delete("1.0", tk.END)
        self.filtered_samples = []
        self.filtered_indices = []
        self.summary_label.config(text="No filter applied", fg="gray")

        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

    def _export_filtered(self):
        """Export filtered samples - USING WORKING PATTERN"""
        if not self.filtered_samples:
            messagebox.showwarning("No Results", "No filtered samples to export")
            return

        # Prepare data for main app
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        export_data = []

        for sample in self.filtered_samples:
            row = {
                'Sample_ID': sample.get('Sample_ID', 'Unknown'),
                'Timestamp': timestamp,
                'Source': 'Advanced Filter',
                'Plugin': PLUGIN_INFO['name'],
                'Notes': f"Filtered using: {self.query_text.get('1.0', tk.END).strip()}"
            }

            # Copy all original data
            for key, value in sample.items():
                if key not in row:
                    row[key] = value

            export_data.append(row)

        # Send to main app using the STANDARDIZED method
        if hasattr(self.app, 'import_data_from_plugin'):
            self.app.import_data_from_plugin(export_data)
            messagebox.showinfo("Success",
                              f"✅ Exported {len(export_data)} filtered samples to main table")
        else:
            messagebox.showerror("Error", "Main app doesn't support plugin data import")


def setup_plugin(main_app):
    """Plugin setup function - CRITICAL: This is what the plugin manager calls"""
    plugin = AdvancedFilterPlugin(main_app)
    return plugin
