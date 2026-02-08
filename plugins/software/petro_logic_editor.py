"""
Petro-Logic Custom Equation Editor Plugin
Create, save, and apply custom geochemical calculations and formulas

Features:
- Custom equation creation with math functions
- Element/element ratio calculations
- Geochemical indices (CIA, MMI, SI, etc.)
- Formula library with save/load
- Real-time preview and validation
- Export to Excel/CSV
- Unit conversion helpers

Author: Sefy Levy
License: CC BY-NC-SA 4.0
"""

PLUGIN_INFO = {
    "category": "software",
    "id": "petro_logic_editor",
    "name": "Petro-Logic Equation Editor",
    "description": "Create and apply custom geochemical calculations",
    "icon": "🧮",
    "version": "1.0",
    "requires": ["numpy", "sympy", "pandas", "matplotlib"],
    "author": "Sefy Levy"
}

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import math
import re
import json
import numpy as np
from io import StringIO
import traceback
from datetime import datetime

# Check dependencies
HAS_NUMPY = False
HAS_SYMPY = False
HAS_PANDAS = False
HAS_MATPLOTLIB = False

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    NUMPY_ERROR = "numpy not found"

try:
    import sympy
    HAS_SYMPY = True
except ImportError:
    SYMPY_ERROR = "sympy not found"

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    PANDAS_ERROR = "pandas not found"

try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    MATPLOTLIB_ERROR = "matplotlib not found"

HAS_REQUIREMENTS = HAS_NUMPY and HAS_SYMPY and HAS_PANDAS


class PetroLogicPlugin:
    """Plugin for custom equation editing and calculation"""

    def __init__(self, main_app):
        """Initialize plugin"""
        self.app = main_app
        self.window = None
        self.equations = []
        self.current_equation = None
        self.variable_list = []
        self.load_formula_library()

        # Math functions available in equations
        self.math_functions = {
            'sqrt': math.sqrt, 'log': math.log, 'log10': math.log10,
            'exp': math.exp, 'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
            'asin': math.asin, 'acos': math.acos, 'atan': math.atan,
            'abs': abs, 'round': round, 'floor': math.floor, 'ceil': math.ceil,
            'pi': math.pi, 'e': math.e
        }

        # Built-in geochemical formulas
        self.builtin_formulas = {
            'CIA (Chemical Index of Alteration)': {
                'expression': 'Al2O3 / (Al2O3 + CaO + Na2O + K2O) * 100',
                'description': 'Chemical weathering index (Nesbitt & Young, 1982)',
                'variables': ['Al2O3', 'CaO', 'Na2O', 'K2O'],
                'category': 'Weathering'
            },
            'Zr/Nb Ratio': {
                'expression': 'Zr_ppm / Nb_ppm',
                'description': 'Tectonic discrimination (Pearce, 2008)',
                'variables': ['Zr_ppm', 'Nb_ppm'],
                'category': 'Tectonic'
            },
            'Mg# (Magnesium Number)': {
                'expression': 'MgO / (MgO + Fe2O3) * 100',
                'description': 'Magnesium number - mantle melting indicator',
                'variables': ['MgO', 'Fe2O3'],
                'category': 'Petrology'
            },
            'SI (Solidification Index)': {
                'expression': 'MgO * 100 / (MgO + Fe2O3 + Na2O + K2O)',
                'description': 'Differentiation index',
                'variables': ['MgO', 'Fe2O3', 'Na2O', 'K2O'],
                'category': 'Petrology'
            },
            'Alkali-Lime Index (ALI)': {
                'expression': '(Na2O + K2O) - (CaO - 3.3 * P2O5)',
                'description': 'Alkaline vs calc-alkaline discrimination',
                'variables': ['Na2O', 'K2O', 'CaO', 'P2O5'],
                'category': 'Classification'
            },
            'A/CNK (Alumina Saturation)': {
                'expression': 'Al2O3 / (CaO + Na2O + K2O)',
                'description': 'Peraluminous vs metaluminous',
                'variables': ['Al2O3', 'CaO', 'Na2O', 'K2O'],
                'category': 'Petrology'
            }
        }

    def open_equation_editor(self):
        """Open the equation editor interface"""
        if not HAS_REQUIREMENTS:
            missing = []
            if not HAS_NUMPY: missing.append("numpy")
            if not HAS_SYMPY: missing.append("sympy")
            if not HAS_PANDAS: missing.append("pandas")

            response = messagebox.askyesno(
                "Missing Dependencies",
                f"Petro-Logic Editor requires these packages:\n\n"
                f"• numpy\n• sympy\n• pandas\n\n"
                f"Missing: {', '.join(missing)}\n\n"
                f"Do you want to install missing dependencies now?",
                parent=self.app.root
            )
            if response:
                self._install_dependencies(missing)
            return

        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("Petro-Logic Equation Editor")
        self.window.geometry("1100x750")

        # Make window stay on top
        self.window.transient(self.app.root)

        self._create_interface()

        # Bring to front
        self.window.lift()
        self.window.focus_force()

    def _create_interface(self):
        """Create the equation editor interface"""
        # Header
        header = tk.Frame(self.window, bg="#5D4037")
        header.pack(fill=tk.X)

        tk.Label(header,
                text="🧮 Petro-Logic Equation Editor",
                font=("Arial", 16, "bold"),
                bg="#5D4037", fg="white",
                pady=10).pack()

        tk.Label(header,
                text="Create custom geochemical calculations and apply to your data",
                font=("Arial", 10),
                bg="#5D4037", fg="white").pack(pady=(0, 10))

        # Create main container
        main_container = tk.Frame(self.window)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Left panel - Equation editor
        left_panel = tk.Frame(main_container, relief=tk.RAISED, borderwidth=1)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Right panel - Preview and library
        right_panel = tk.Frame(main_container, width=300)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        right_panel.pack_propagate(False)

        # Create left panel content
        self._create_editor_panel(left_panel)

        # Create right panel content
        self._create_library_panel(right_panel)

    def _create_editor_panel(self, parent):
        """Create the equation editor panel"""
        # Equation name
        name_frame = tk.Frame(parent, padx=10, pady=10)
        name_frame.pack(fill=tk.X)

        tk.Label(name_frame, text="Equation Name:",
                font=("Arial", 11, "bold")).pack(side=tk.LEFT)

        self.eq_name_var = tk.StringVar()
        tk.Entry(name_frame, textvariable=self.eq_name_var,
                font=("Arial", 11), width=40).pack(side=tk.LEFT, padx=10)

        # Category
        cat_frame = tk.Frame(parent, padx=10, pady=5)
        cat_frame.pack(fill=tk.X)

        tk.Label(cat_frame, text="Category:").pack(side=tk.LEFT)

        self.eq_category_var = tk.StringVar(value="Custom")
        categories = ["Custom", "Weathering", "Tectonic", "Petrology",
                     "Classification", "Ratios", "Indices", "Provenance"]
        ttk.Combobox(cat_frame, textvariable=self.eq_category_var,
                    values=categories, state='readonly',
                    width=20).pack(side=tk.LEFT, padx=10)

        # Description
        desc_frame = tk.LabelFrame(parent, text="Description", padx=10, pady=10)
        desc_frame.pack(fill=tk.X, padx=10, pady=5)

        self.eq_desc_text = scrolledtext.ScrolledText(desc_frame, height=3,
                                                     wrap=tk.WORD,
                                                     font=("Arial", 10))
        self.eq_desc_text.pack(fill=tk.X)

        # Expression editor
        expr_frame = tk.LabelFrame(parent, text="Expression", padx=10, pady=10)
        expr_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Help bar
        help_frame = tk.Frame(expr_frame)
        help_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(help_frame, text="Available: + - * / ** ( ) sqrt() log() log10() exp()",
                font=("Courier", 9), fg="gray").pack(side=tk.LEFT)

        # Expression text with syntax highlighting
        self.expr_text = scrolledtext.ScrolledText(expr_frame,
                                                  wrap=tk.WORD,
                                                  font=("Courier", 12),
                                                  height=8)
        self.expr_text.pack(fill=tk.BOTH, expand=True)

        # Insert example
        self.expr_text.insert("1.0", "(Zr_ppm + Nb_ppm) / 2  # Average of Zr and Nb")

        # Variable list
        var_frame = tk.LabelFrame(parent, text="Detected Variables", padx=10, pady=10)
        var_frame.pack(fill=tk.X, padx=10, pady=5)

        self.var_listbox = tk.Listbox(var_frame, height=4)
        self.var_listbox.pack(fill=tk.X)

        # Buttons frame
        button_frame = tk.Frame(parent, pady=15)
        button_frame.pack(fill=tk.X, padx=10)

        tk.Button(button_frame, text="🔍 Parse Expression",
                 command=self._parse_expression,
                 bg="#FF9800", fg="white",
                 font=("Arial", 10, "bold"),
                 width=20).pack(side=tk.LEFT, padx=5)

        tk.Button(button_frame, text="💾 Save Equation",
                 command=self._save_equation,
                 bg="#4CAF50", fg="white",
                 font=("Arial", 10, "bold"),
                 width=20).pack(side=tk.LEFT, padx=5)

        tk.Button(button_frame, text="🚀 Apply to Data",
                 command=self._apply_to_data,
                 bg="#2196F3", fg="white",
                 font=("Arial", 10, "bold"),
                 width=20).pack(side=tk.LEFT, padx=5)

        tk.Button(button_frame, text="📊 Preview Results",
                 command=self._preview_results,
                 bg="#9C27B0", fg="white",
                 font=("Arial", 10, "bold"),
                 width=20).pack(side=tk.LEFT, padx=5)

        # Status bar
        self.status_label = tk.Label(parent, text="Ready",
                                    bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

    def _create_library_panel(self, parent):
        """Create the formula library panel"""
        # Library header
        header_frame = tk.Frame(parent, bg="#3F51B5", pady=5)
        header_frame.pack(fill=tk.X)

        tk.Label(header_frame,
                text="📚 Formula Library",
                font=("Arial", 12, "bold"),
                bg="#3F51B5", fg="white").pack()

        # Search
        search_frame = tk.Frame(parent, pady=10, padx=10)
        search_frame.pack(fill=tk.X)

        tk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        tk.Entry(search_frame, textvariable=self.search_var,
                width=20).pack(side=tk.LEFT, padx=5)

        tk.Button(search_frame, text="🔍",
                 command=self._search_library).pack(side=tk.LEFT)

        # Category filter
        filter_frame = tk.Frame(parent, padx=10)
        filter_frame.pack(fill=tk.X, pady=5)

        tk.Label(filter_frame, text="Filter by:").pack(side=tk.LEFT)
        self.filter_var = tk.StringVar(value="All")
        ttk.Combobox(filter_frame, textvariable=self.filter_var,
                    values=["All", "Built-in", "Custom", "Weathering",
                           "Tectonic", "Petrology", "Classification"],
                    state='readonly', width=15).pack(side=tk.LEFT, padx=5)

        # Library list
        list_frame = tk.LabelFrame(parent, text="Available Formulas",
                                  padx=10, pady=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Treeview for formulas
        columns = ("Name", "Category", "Variables")
        self.library_tree = ttk.Treeview(list_frame, columns=columns,
                                        show="headings", height=15)

        for col in columns:
            self.library_tree.heading(col, text=col)
            self.library_tree.column(col, width=100)

        self.library_tree.column("Name", width=150)
        self.library_tree.column("Variables", width=100)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL,
                                 command=self.library_tree.yview)
        self.library_tree.configure(yscrollcommand=scrollbar.set)

        self.library_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind selection
        self.library_tree.bind("<<TreeviewSelect>>", self._on_formula_select)

        # Action buttons
        action_frame = tk.Frame(parent, pady=10)
        action_frame.pack(fill=tk.X, padx=10)

        tk.Button(action_frame, text="📥 Load Selected",
                 command=self._load_selected_formula,
                 width=15).pack(side=tk.LEFT, padx=2)

        tk.Button(action_frame, text="🗑️ Delete",
                 command=self._delete_formula,
                 width=15).pack(side=tk.LEFT, padx=2)

        tk.Button(action_frame, text="📋 Export Library",
                 command=self._export_library,
                 width=15).pack(side=tk.LEFT, padx=2)

        tk.Button(action_frame, text="📄 Import Library",
                 command=self._import_library,
                 width=15).pack(side=tk.LEFT, padx=2)

        # Built-in formulas info
        info_frame = tk.LabelFrame(parent, text="Quick Insert", padx=10, pady=10)
        info_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(info_frame,
                text="Common variables:\n• Element_ppm (e.g., Zr_ppm)\n• Oxide_wt (e.g., SiO2)\n• Ratios (e.g., Zr_Nb_Ratio)",
                font=("Arial", 9), justify=tk.LEFT).pack(anchor=tk.W)

        # Insert buttons for common formulas
        insert_frame = tk.Frame(info_frame, pady=5)
        insert_frame.pack(fill=tk.X)

        common_formulas = ["CIA", "Zr/Nb", "Mg#", "SI"]
        for formula in common_formulas:
            tk.Button(insert_frame, text=formula,
                     command=lambda f=formula: self._insert_builtin(f),
                     width=8).pack(side=tk.LEFT, padx=2)

        # Refresh library
        self._refresh_library()

    def _parse_expression(self):
        """Parse the expression and extract variables"""
        expression = self.expr_text.get("1.0", tk.END).strip()

        if not expression:
            messagebox.showwarning("Empty Expression",
                                 "Please enter an expression.")
            return

        try:
            # Remove comments (anything after #)
            expression = expression.split('#')[0].strip()

            # Extract variables (words that aren't math functions)
            variables = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', expression)

            # Remove math functions from variable list
            math_funcs = list(self.math_functions.keys()) + ['pi', 'e']
            variables = [v for v in variables if v not in math_funcs]

            # Remove duplicates
            variables = list(set(variables))

            # Update variable listbox
            self.var_listbox.delete(0, tk.END)
            for var in sorted(variables):
                self.var_listbox.insert(tk.END, var)

            self.variable_list = variables

            # Validate expression
            self._validate_expression(expression, variables)

            self.status_label.config(text=f"✅ Parsed: {len(variables)} variables found")

        except Exception as e:
            messagebox.showerror("Parse Error", f"Error parsing expression:\n\n{str(e)}")

    def _validate_expression(self, expression, variables):
        """Validate the expression syntax"""
        try:
            # Create a test environment
            test_env = self.math_functions.copy()

            # Add dummy values for variables
            for var in variables:
                test_env[var] = 1.0

            # Try to compile and evaluate
            compiled = compile(expression, '<string>', 'eval')
            result = eval(compiled, {"__builtins__": {}}, test_env)

            # Check if result is numeric
            if not isinstance(result, (int, float, complex)):
                raise ValueError("Expression must evaluate to a number")

            return True

        except SyntaxError as e:
            raise SyntaxError(f"Syntax error: {str(e)}")
        except NameError as e:
            raise NameError(f"Undefined variable: {str(e)}")
        except Exception as e:
            raise Exception(f"Evaluation error: {str(e)}")

    def _save_equation(self):
        """Save the current equation to library"""
        name = self.eq_name_var.get().strip()
        category = self.eq_category_var.get()
        description = self.eq_desc_text.get("1.0", tk.END).strip()
        expression = self.expr_text.get("1.0", tk.END).strip()

        if not name:
            messagebox.showwarning("Missing Name",
                                 "Please enter an equation name.")
            return

        if not expression:
            messagebox.showwarning("Missing Expression",
                                 "Please enter an expression.")
            return

        # Parse variables
        self._parse_expression()

        # Create equation object
        equation = {
            'name': name,
            'category': category,
            'description': description,
            'expression': expression.split('#')[0].strip(),  # Remove comments
            'variables': self.variable_list,
            'created': datetime.now().isoformat(),
            'type': 'custom'
        }

        # Check if updating existing
        existing_idx = -1
        for i, eq in enumerate(self.equations):
            if eq['name'] == name and eq.get('type') == 'custom':
                existing_idx = i
                break

        if existing_idx >= 0:
            # Update existing
            self.equations[existing_idx] = equation
            self.status_label.config(text=f"✅ Updated: {name}")
        else:
            # Add new
            self.equations.append(equation)
            self.status_label.config(text=f"✅ Saved: {name}")

        # Save to file
        self._save_formula_library()

        # Refresh library display
        self._refresh_library()

    def _apply_to_data(self):
        """Apply current equation to all samples"""
        if not self.app.samples:
            messagebox.showwarning("No Data", "No samples loaded.")
            return

        expression = self.expr_text.get("1.0", tk.END).strip()
        expression = expression.split('#')[0].strip()  # Remove comments

        if not expression:
            messagebox.showwarning("No Expression",
                                 "Please enter an expression.")
            return

        # Parse variables
        self._parse_expression()

        # Get new column name
        col_name = self.eq_name_var.get().strip()
        if not col_name:
            col_name = "Custom_Calculation"

        # Clean column name (remove spaces, special chars)
        col_name = re.sub(r'[^a-zA-Z0-9_]', '_', col_name)

        try:
            # Apply to each sample
            results = []
            missing_vars_samples = []

            for i, sample in enumerate(self.app.samples):
                # Create evaluation environment
                env = self.math_functions.copy()

                # Add variable values
                missing_vars = []
                for var in self.variable_list:
                    value = sample.get(var)
                    if value is not None and value != '':
                        try:
                            env[var] = float(value)
                        except (ValueError, TypeError):
                            missing_vars.append(var)
                    else:
                        missing_vars.append(var)

                if missing_vars:
                    missing_vars_samples.append((i, missing_vars))
                    results.append(None)
                    continue

                try:
                    # Evaluate expression
                    compiled = compile(expression, '<string>', 'eval')
                    result = eval(compiled, {"__builtins__": {}}, env)

                    # Store result
                    sample[col_name] = result
                    results.append(result)

                except Exception as e:
                    results.append(None)
                    missing_vars_samples.append((i, [f"Eval error: {str(e)}"]))

            # Update app data
            if hasattr(self.app, 'update_display'):
                self.app.update_display()

            # Show summary
            success_count = sum(1 for r in results if r is not None)
            total_count = len(results)

            if missing_vars_samples:
                missing_msg = f"\n\nMissing variables in {len(missing_vars_samples)} samples."
                if len(missing_vars_samples) <= 5:
                    for idx, vars in missing_vars_samples[:5]:
                        missing_msg += f"\nSample {idx}: {', '.join(vars[:3])}"
                        if len(vars) > 3:
                            missing_msg += "..."
            else:
                missing_msg = ""

            messagebox.showinfo("Applied Successfully",
                              f"Applied '{col_name}' to {success_count}/{total_count} samples.{missing_msg}")

            self.status_label.config(text=f"✅ Applied to {success_count}/{total_count} samples")

        except Exception as e:
            messagebox.showerror("Application Error",
                               f"Error applying equation:\n\n{str(e)}\n\n{traceback.format_exc()}")

    def _preview_results(self):
        """Preview calculation results on selected samples"""
        if not self.app.samples:
            messagebox.showwarning("No Data", "No samples loaded.")
            return

        expression = self.expr_text.get("1.0", tk.END).strip()
        expression = expression.split('#')[0].strip()

        if not expression:
            messagebox.showwarning("No Expression",
                                 "Please enter an expression.")
            return

        # Parse variables
        self._parse_expression()

        try:
            # Calculate for first 10 samples
            preview_data = []

            for i, sample in enumerate(self.app.samples[:10]):
                # Create evaluation environment
                env = self.math_functions.copy()

                # Add variable values
                row = {'Sample': sample.get('Sample_ID', f'Sample_{i}')}
                missing = False

                for var in self.variable_list:
                    value = sample.get(var)
                    if value is not None and value != '':
                        try:
                            val = float(value)
                            env[var] = val
                            row[var] = f"{val:.3f}"
                        except (ValueError, TypeError):
                            row[var] = "N/A"
                            missing = True
                    else:
                        row[var] = "N/A"
                        missing = True

                if missing:
                    row['Result'] = "Missing data"
                else:
                    try:
                        compiled = compile(expression, '<string>', 'eval')
                        result = eval(compiled, {"__builtins__": {}}, env)
                        row['Result'] = f"{result:.4f}"
                    except Exception as e:
                        row['Result'] = f"Error: {str(e)[:30]}"

                preview_data.append(row)

            # Show preview window
            self._show_preview_window(preview_data, expression)

        except Exception as e:
            messagebox.showerror("Preview Error", f"Error: {str(e)}")

    def _show_preview_window(self, data, expression):
        """Show preview window with results"""
        preview_win = tk.Toplevel(self.window)
        preview_win.title("Calculation Preview")
        preview_win.geometry("800x400")

        # Header
        tk.Label(preview_win,
                text="📊 Calculation Preview",
                font=("Arial", 14, "bold"),
                pady=10).pack()

        tk.Label(preview_win,
                text=f"Expression: {expression}",
                font=("Courier", 10),
                pady=5).pack()

        # Create treeview
        columns = ["Sample"] + self.variable_list + ["Result"]
        tree = ttk.Treeview(preview_win, columns=columns, show="headings")

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=80)

        tree.column("Sample", width=100)
        tree.column("Result", width=120)

        # Add data
        for row in data:
            values = [row.get(col, "") for col in columns]
            tree.insert("", tk.END, values=values)

        # Scrollbars
        vsb = ttk.Scrollbar(preview_win, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(preview_win, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)

        # Statistics
        if data and data[0]['Result'] not in ["Missing data", "Error"]:
            try:
                results = [float(row['Result']) for row in data
                          if 'Result' in row and row['Result'] not in ["Missing data", "Error"]]
                if results:
                    stats_frame = tk.Frame(preview_win, pady=10)
                    stats_frame.pack(fill=tk.X)

                    stats_text = (f"Statistics (n={len(results)}): "
                                 f"Mean={np.mean(results):.3f}, "
                                 f"Std={np.std(results):.3f}, "
                                 f"Min={min(results):.3f}, "
                                 f"Max={max(results):.3f}")

                    tk.Label(stats_frame, text=stats_text,
                            font=("Arial", 9)).pack()
            except:
                pass

    def _refresh_library(self):
        """Refresh the formula library display"""
        # Clear tree
        for item in self.library_tree.get_children():
            self.library_tree.delete(item)

        # Get filter
        filter_cat = self.filter_var.get()
        search_term = self.search_var.get().lower()

        # Add built-in formulas
        if filter_cat in ["All", "Built-in"]:
            for name, formula in self.builtin_formulas.items():
                if search_term and search_term not in name.lower():
                    continue

                self.library_tree.insert("", tk.END,
                                       values=(name,
                                              formula['category'],
                                              ", ".join(formula['variables'][:3])),
                                       tags=("builtin",))

        # Add custom formulas
        for eq in self.equations:
            if filter_cat not in ["All", "Custom"] and eq['category'] != filter_cat:
                continue

            if search_term and search_term not in eq['name'].lower():
                continue

            vars_display = ", ".join(eq['variables'][:3])
            if len(eq['variables']) > 3:
                vars_display += "..."

            self.library_tree.insert("", tk.END,
                                   values=(eq['name'],
                                          eq['category'],
                                          vars_display),
                                   tags=("custom",))

        # Tag colors
        self.library_tree.tag_configure("builtin", background="#E8F5E9")
        self.library_tree.tag_configure("custom", background="#E3F2FD")

    def _on_formula_select(self, event):
        """When a formula is selected from library"""
        selection = self.library_tree.selection()
        if not selection:
            return

        item = self.library_tree.item(selection[0])
        name = item['values'][0]

        # Check if built-in or custom
        if "builtin" in item['tags']:
            formula = self.builtin_formulas.get(name)
            if formula:
                self.eq_name_var.set(name)
                self.eq_category_var.set(formula['category'])
                self.eq_desc_text.delete("1.0", tk.END)
                self.eq_desc_text.insert("1.0", formula['description'])
                self.expr_text.delete("1.0", tk.END)
                self.expr_text.insert("1.0", formula['expression'])
                self._parse_expression()
        else:
            # Find custom formula
            for eq in self.equations:
                if eq['name'] == name:
                    self.eq_name_var.set(eq['name'])
                    self.eq_category_var.set(eq['category'])
                    self.eq_desc_text.delete("1.0", tk.END)
                    self.eq_desc_text.insert("1.0", eq['description'])
                    self.expr_text.delete("1.0", tk.END)
                    self.expr_text.insert("1.0", eq['expression'])
                    self.variable_list = eq['variables']

                    # Update variable listbox
                    self.var_listbox.delete(0, tk.END)
                    for var in sorted(eq['variables']):
                        self.var_listbox.insert(tk.END, var)
                    break

    def _load_selected_formula(self):
        """Load selected formula into editor"""
        self._on_formula_select(None)
        self.status_label.config(text="✅ Formula loaded")

    def _delete_formula(self):
        """Delete selected formula"""
        selection = self.library_tree.selection()
        if not selection:
            return

        item = self.library_tree.item(selection[0])
        name = item['values'][0]

        # Don't delete built-in formulas
        if "builtin" in item['tags']:
            messagebox.showinfo("Cannot Delete",
                              "Built-in formulas cannot be deleted.")
            return

        # Confirm deletion
        if not messagebox.askyesno("Confirm Delete",
                                  f"Delete formula '{name}'?"):
            return

        # Delete from equations list
        self.equations = [eq for eq in self.equations if eq['name'] != name]

        # Save library
        self._save_formula_library()

        # Refresh display
        self._refresh_library()

        self.status_label.config(text=f"🗑️ Deleted: {name}")

    def _export_library(self):
        """Export formula library to JSON file"""
        path = filedialog.asksaveasfilename(
            title="Export Formula Library",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if path:
            try:
                export_data = {
                    'equations': self.equations,
                    'export_date': datetime.now().isoformat(),
                    'version': '1.0'
                }

                with open(path, 'w') as f:
                    json.dump(export_data, f, indent=2)

                messagebox.showinfo("Export Successful",
                                  f"Library exported to:\n{path}")

            except Exception as e:
                messagebox.showerror("Export Error", f"Error: {str(e)}")

    def _import_library(self):
        """Import formula library from JSON file"""
        path = filedialog.askopenfilename(
            title="Import Formula Library",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if path:
            try:
                with open(path, 'r') as f:
                    import_data = json.load(f)

                # Merge equations
                imported_eqs = import_data.get('equations', [])

                # Check for duplicates
                existing_names = [eq['name'] for eq in self.equations]
                new_eqs = []

                for eq in imported_eqs:
                    if eq['name'] not in existing_names:
                        new_eqs.append(eq)

                # Add new equations
                self.equations.extend(new_eqs)

                # Save library
                self._save_formula_library()

                # Refresh display
                self._refresh_library()

                messagebox.showinfo("Import Successful",
                                  f"Imported {len(new_eqs)} new formulas.")

            except Exception as e:
                messagebox.showerror("Import Error", f"Error: {str(e)}")

    def _insert_builtin(self, formula_name):
        """Insert built-in formula into editor"""
        formula_map = {
            'CIA': 'Al2O3 / (Al2O3 + CaO + Na2O + K2O) * 100',
            'Zr/Nb': 'Zr_ppm / Nb_ppm',
            'Mg#': 'MgO / (MgO + Fe2O3) * 100',
            'SI': 'MgO * 100 / (MgO + Fe2O3 + Na2O + K2O)'
        }

        if formula_name in formula_map:
            self.expr_text.insert(tk.END, f"\n{formula_map[formula_name]}")
            self._parse_expression()

    def _search_library(self):
        """Search library"""
        self._refresh_library()

    def load_formula_library(self):
        """Load saved formula library from file"""
        try:
            import os
            lib_path = "config/petro_logic_library.json"
            if os.path.exists(lib_path):
                with open(lib_path, 'r') as f:
                    data = json.load(f)
                    self.equations = data.get('equations', [])
        except:
            self.equations = []

    def _save_formula_library(self):
        """Save formula library to file"""
        try:
            import os
            os.makedirs("config", exist_ok=True)

            lib_path = "config/petro_logic_library.json"
            data = {
                'equations': self.equations,
                'saved': datetime.now().isoformat()
            }

            with open(lib_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving library: {e}")

    def _install_dependencies(self, missing_packages):
        """Install missing dependencies"""
        response = messagebox.askyesno(
            "Install Dependencies",
            f"Install these packages:\n\n{', '.join(missing_packages)}\n\n"
            f"This may take a few minutes.",
            parent=self.window
        )

        if response:
            if hasattr(self.app, 'open_plugin_manager'):
                self.window.destroy()
                self.app.open_plugin_manager()


# Bind to application menu
def setup_plugin(main_app):
    """Setup function called by main application"""
    plugin = PetroLogicPlugin(main_app)

    # Add to Tools menu
    if hasattr(main_app, 'menu_bar'):
        main_app.menu_bar.add_command(
            label="Petro-Logic Equation Editor",
            command=plugin.open_equation_editor
        )

    return plugin
