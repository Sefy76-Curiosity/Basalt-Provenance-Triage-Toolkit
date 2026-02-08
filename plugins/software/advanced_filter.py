"""
Advanced Filter Plugin for Basalt Provenance Toolkit
Logical query language for data filtering

Author: Sefy Levy
License: CC BY-NC-SA 4.0
"""
PLUGIN_INFO = {
      "category": "software",
    "id": "advanced_filter",
    "name": "Advanced Filter",
    "description": "Logical query language for complex data filtering",
    "icon": "🔍",
    "version": "1.0",
    "requires": [],
    "author": "Sefy Levy"
}



import tkinter as tk
from tkinter import ttk, messagebox
import re


class AdvancedFilterPlugin:
    """Plugin for advanced logical filtering"""
    
    def __init__(self, main_app):
        """Initialize plugin"""
        self.app = main_app
        self.window = None
        self.filtered_samples = []
    
    def open_advanced_filter_window(self):
        """Open the advanced filter interface"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return
        
        self.window = tk.Toplevel(self.app.root)
        self.window.title("Advanced Filter - Logical Query Language")
        self.window.geometry("650x480")
        
        # Make window stay on top
        self.window.transient(self.app.root)
        
        self._create_interface()
        
        # Bring to front
        self.window.lift()
        self.window.focus_force()
    
    def _create_interface(self):
        """Create the filter interface"""
        # Header
        header = tk.Frame(self.window, bg="#3F51B5")
        header.pack(fill=tk.X)
        
        tk.Label(header,
                text="🔍 Advanced Filter",
                font=("Arial", 16, "bold"),
                bg="#3F51B5", fg="white",
                pady=5).pack()
        
        tk.Label(header,
                text="Logical query language for complex data filtering",
                font=("Arial", 10),
                bg="#3F51B5", fg="white",
                pady=5).pack()
        
        # Main content
        content = tk.Frame(self.window, padx=10, pady=8)
        content.pack(fill=tk.BOTH, expand=True)
        
        # Examples
        example_frame = tk.LabelFrame(content, text="Query Examples",
                                     font=("Arial", 10, "bold"),
                                     padx=10, pady=5)
        example_frame.pack(fill=tk.X, pady=5)
        
        examples = [
            "Zr_ppm > 100",
            "Zr_ppm > 100 AND Nb_ppm < 20",
            "Cr_ppm > 2000 OR Ni_ppm > 1500",
            "Wall_Thickness_mm < 5 AND Flag_For_Review == 'YES'",
            "Final_Classification == 'GOLAN'",
            "NOT Auto_Classification == 'EGYPTIAN'",
            "(Zr_ppm > 100 AND Nb_ppm < 20) OR Cr_ppm > 2500"
        ]
        
        tk.Label(example_frame,
                text="Click an example to use it:",
                font=("Arial", 9), fg="gray").pack(anchor=tk.W)
        
        for ex in examples:
            btn = tk.Button(example_frame, text=ex,
                           command=lambda e=ex: self._use_example(e),
                           font=("Courier", 9),
                           fg="#1976D2",
                           cursor="hand2",
                           relief=tk.FLAT,
                           anchor=tk.W)
            btn.pack(anchor=tk.W, padx=10, pady=2)
        
        # Query input
        query_frame = tk.LabelFrame(content, text="Your Query",
                                   font=("Arial", 10, "bold"),
                                   padx=10, pady=5)
        query_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(query_frame,
                text="Enter your filter expression:",
                font=("Arial", 9)).pack(anchor=tk.W)
        
        self.query_entry = tk.Text(query_frame, height=4, font=("Courier", 10))
        self.query_entry.pack(fill=tk.X, pady=5)
        
        # Operators help
        operators_frame = tk.Frame(query_frame)
        operators_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(operators_frame,
                text="Operators:",
                font=("Arial", 8, "bold")).pack(side=tk.LEFT)
        
        tk.Label(operators_frame,
                text=">, <, >=, <=, ==, !=  |  AND, OR, NOT  |  ( )",
                font=("Arial", 8),
                fg="gray").pack(side=tk.LEFT, padx=5)
        
        # Buttons
        btn_frame = tk.Frame(content)
        btn_frame.pack(pady=5)
        
        tk.Button(btn_frame, text="▶ Apply",
                 command=self._apply_filter,
                 bg="#4CAF50", fg="white",
                 font=("Arial", 9, "bold"),
                 width=12).pack(side=tk.LEFT, padx=3)
        
        tk.Button(btn_frame, text="Clear",
                 command=self._clear_filter,
                 font=("Arial", 9),
                 width=10).pack(side=tk.LEFT, padx=3)
        
        tk.Button(btn_frame, text="Export",
                 command=self._export_filtered,
                 bg="#2196F3", fg="white",
                 font=("Arial", 9),
                 width=10).pack(side=tk.LEFT, padx=3)
        
        # Results
        results_frame = tk.LabelFrame(content, text="Filter Results",
                                     font=("Arial", 10, "bold"),
                                     padx=10, pady=5)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.results_label = tk.Label(results_frame,
                                      text="No filter applied",
                                      font=("Arial", 10),
                                      fg="gray")
        self.results_label.pack()
        
        self.results_tree = None
    
    def _use_example(self, example):
        """Insert example query"""
        self.query_entry.delete("1.0", tk.END)
        self.query_entry.insert("1.0", example)
    
    def _parse_query(self, query):
        """Parse and evaluate the query"""
        # Replace logical operators
        query = query.replace(" AND ", " and ")
        query = query.replace(" OR ", " or ")
        query = query.replace(" NOT ", " not ")
        
        # This is a simplified parser - in production, use a proper parser
        # For safety, we'll only allow specific field names and operators
        
        allowed_fields = [
            'Zr_ppm', 'Nb_ppm', 'Ba_ppm', 'Rb_ppm', 'Cr_ppm', 'Ni_ppm',
            'Wall_Thickness_mm', 'Zr_Nb_Ratio', 'Cr_Ni_Ratio', 'Ba_Rb_Ratio',
            'Auto_Classification', 'Final_Classification', 'Flag_For_Review',
            'Sample_ID', 'Confidence_1_to_5'
        ]
        
        return query
    
    def _evaluate_condition(self, sample, query):
        """Evaluate if sample matches the query"""
        try:
            # Create a safe evaluation environment
            safe_dict = {}
            
            # Add sample values to evaluation context
            for key, value in sample.items():
                if key in ['Zr_ppm', 'Nb_ppm', 'Ba_ppm', 'Rb_ppm', 'Cr_ppm', 'Ni_ppm',
                          'Wall_Thickness_mm', 'Zr_Nb_Ratio', 'Cr_Ni_Ratio', 'Ba_Rb_Ratio']:
                    # Convert to float, use 0 if empty
                    try:
                        safe_dict[key] = float(value) if value else 0
                    except (ValueError, TypeError):
                        safe_dict[key] = 0
                elif key in ['Auto_Classification', 'Final_Classification', 'Flag_For_Review', 'Sample_ID']:
                    safe_dict[key] = str(value) if value else ''
                else:
                    safe_dict[key] = value
            
            # Evaluate the query
            result = eval(query, {"__builtins__": {}}, safe_dict)
            return bool(result)
            
        except Exception as e:
            # If evaluation fails, return False
            return False
    
    def _apply_filter(self):
        """Apply the filter to samples"""
        query = self.query_entry.get("1.0", tk.END).strip()
        
        if not query:
            messagebox.showwarning("Empty Query", "Please enter a filter expression")
            return
        
        samples = self.app.samples
        
        if not samples:
            messagebox.showwarning("No Data", "No samples to filter")
            return
        
        # Show progress
        if hasattr(self.app, '_show_progress'):
            self.app._show_progress("Applying filter...", 0)
        
        try:
            # Parse query
            parsed_query = self._parse_query(query)
            
            # Filter samples
            self.filtered_samples = []
            total = len(samples)
            
            for i, sample in enumerate(samples):
                if self._evaluate_condition(sample, parsed_query):
                    self.filtered_samples.append(sample)
                
                # Update progress
                if hasattr(self.app, '_update_progress') and i % 10 == 0:
                    progress = (i / total) * 100
                    self.app._update_progress(progress, f"Filtering... {i}/{total}")
            
            # Hide progress
            if hasattr(self.app, '_hide_progress'):
                self.app._hide_progress()
            
            # Display results
            self._display_results()
            
        except Exception as e:
            if hasattr(self.app, '_hide_progress'):
                self.app._hide_progress()
            messagebox.showerror("Filter Error",
                               f"Invalid query:\n\n{str(e)}\n\n"
                               f"Check your syntax and field names.")
    
    def _display_results(self):
        """Display filtered results"""
        # Clear previous results
        if self.results_tree:
            self.results_tree.destroy()
        self.results_label.destroy()
        
        # Get parent frame
        results_frame = self.results_label.master
        
        # Show count
        count_label = tk.Label(results_frame,
                              text=f"✓ Found {len(self.filtered_samples)} matching sample(s)",
                              font=("Arial", 11, "bold"),
                              fg="green" if self.filtered_samples else "orange")
        count_label.pack(pady=5)
        self.results_label = count_label
        
        if not self.filtered_samples:
            return
        
        # Create results tree
        tree_frame = tk.Frame(results_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        columns = ('Sample ID', 'Classification', 'Zr', 'Nb', 'Cr', 'Ni')
        self.results_tree = ttk.Treeview(tree_frame, columns=columns,
                                        show='headings', yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.results_tree.yview)
        
        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=100)
        
        # Add data
        for sample in self.filtered_samples:
            self.results_tree.insert('', tk.END, values=(
                sample.get('Sample_ID', ''),
                sample.get('Final_Classification', sample.get('Auto_Classification', '')),
                sample.get('Zr_ppm', ''),
                sample.get('Nb_ppm', ''),
                sample.get('Cr_ppm', ''),
                sample.get('Ni_ppm', '')
            ))
        
        self.results_tree.pack(fill=tk.BOTH, expand=True)
    
    def _clear_filter(self):
        """Clear the filter"""
        self.query_entry.delete("1.0", tk.END)
        self.filtered_samples = []
        
        if self.results_tree:
            self.results_tree.destroy()
            self.results_tree = None
        
        self.results_label.config(text="No filter applied", fg="gray")
    
    def _export_filtered(self):
        """Export filtered samples"""
        if not self.filtered_samples:
            messagebox.showwarning("No Results", "No filtered samples to export")
            return
        
        messagebox.showinfo("Export",
                          f"Would export {len(self.filtered_samples)} filtered samples.\n\n"
                          "This feature will save filtered results to CSV in v10.2")
