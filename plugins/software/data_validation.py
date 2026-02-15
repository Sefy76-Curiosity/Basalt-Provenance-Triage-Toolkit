"""
Data Validation Plugin for Basalt Provenance Toolkit
IoGAS-style data quality checks and validation

Author: Sefy Levy
License: CC BY-NC-SA 4.0
"""
PLUGIN_INFO = {
      "category": "software",
    "id": "data_validation",
    "name": "Data Validation Wizard",
    "description": "IoGAS-style data quality checks, outlier detection, missing data reports",
    "icon": "✓",
    "version": "1.0",
    "requires": ["numpy", "matplotlib"],
    "author": "Sefy Levy"
}



import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import numpy as np

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


class DataValidationPlugin:
    """Plugin for data quality validation and checks"""
    
    def __init__(self, main_app):
        """Initialize plugin"""
        self.app = main_app
        self.window = None
        self.validation_results = {}
    
    def open_window(self):
        """Open the data validation interface"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return
        
        self.window = tk.Toplevel(self.app.root)
        self.window.title("Data Validation Wizard")
        self.window.geometry("700x520")
        
        # Make window stay on top
        self.window.transient(self.app.root)
        
        self._create_interface()
        
        # Bring to front
        self.window.lift()
        self.window.focus_force()
    
    def _create_interface(self):
        """Create the validation interface"""
        # Header
        header = tk.Frame(self.window, bg="#673AB7")
        header.pack(fill=tk.X)
        
        tk.Label(header,
                text="✓ Data Validation Wizard",
                font=("Arial", 16, "bold"),
                bg="#673AB7", fg="white",
                pady=5).pack()
        
        tk.Label(header,
                text="Professional data quality checks for provenance analysis",
                font=("Arial", 10),
                bg="#673AB7", fg="white",
                pady=5).pack()
        
        # Create notebook
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Tab 1: Quick Check
        self._create_quick_check_tab(notebook)
        
        # Tab 2: Missing Data
        self._create_missing_data_tab(notebook)
        
        # Tab 3: Outliers
        self._create_outlier_tab(notebook)
        
        # Tab 4: Report
        self._create_report_tab(notebook)
    
    def _create_quick_check_tab(self, notebook):
        """Create quick validation check tab"""
        frame = tk.Frame(notebook)
        notebook.add(frame, text="Quick Check")
        
        # Controls
        controls = tk.Frame(frame, relief=tk.RAISED, borderwidth=2)
        controls.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        tk.Label(controls,
                text="Quick Data Quality Check",
                font=("Arial", 12, "bold")).pack(anchor=tk.W, padx=10, pady=5)
        
        tk.Label(controls,
                text="Run a fast validation of all samples",
                font=("Arial", 9), fg="gray").pack(anchor=tk.W, padx=10)
        
        tk.Button(controls, text="▶ Run Quick Check",
                 command=self._run_quick_check,
                 bg="#4CAF50", fg="white",
                 font=("Arial", 10, "bold"),
                 width=20, height=2).pack(pady=5)
        
        # Results frame
        self.quick_check_frame = tk.Frame(frame)
        self.quick_check_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        tk.Label(self.quick_check_frame,
                text="Click 'Run Quick Check' to analyze your data",
                font=("Arial", 11), fg="gray").pack(expand=True)
    
    def _run_quick_check(self):
        """Run quick validation check"""
        samples = self.app.samples
        
        if not samples:
            messagebox.showwarning("No Data", "No samples to validate")
            return
        
        # Clear previous results
        for widget in self.quick_check_frame.winfo_children():
            widget.destroy()
        
        # Create results display
        results_text = scrolledtext.ScrolledText(self.quick_check_frame,
                                                font=("Courier", 10),
                                                height=30)
        results_text.pack(fill=tk.BOTH, expand=True)
        
        # Run checks
        report = []
        report.append("═" * 70)
        report.append("DATA VALIDATION REPORT")
        report.append("═" * 70)
        report.append("")
        
        # Basic stats
        report.append(f"Total Samples: {len(samples)}")
        report.append("")
        
        # Check each element
        elements = ['Zr_ppm', 'Nb_ppm', 'Ba_ppm', 'Rb_ppm', 'Cr_ppm', 'Ni_ppm']
        
        report.append("ELEMENT COVERAGE:")
        report.append("-" * 70)
        
        for elem in elements:
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
            
            if values:
                report.append(f"   Range: {min(values):.1f} - {max(values):.1f} ppm")
                report.append(f"   Mean:  {np.mean(values):.1f} ± {np.std(values):.1f} ppm")
        
        report.append("")
        
        # Classification status
        report.append("CLASSIFICATION STATUS:")
        report.append("-" * 70)
        
        classified = sum(1 for s in samples if s.get('Final_Classification', '').strip())
        auto_classified = sum(1 for s in samples if s.get('Auto_Classification', '').strip())
        flagged = sum(1 for s in samples if s.get('Flag_For_Review') == 'YES')
        
        report.append(f"Manually classified: {classified}/{len(samples)} ({classified/len(samples)*100:.1f}%)")
        report.append(f"Auto-classified:     {auto_classified}/{len(samples)} ({auto_classified/len(samples)*100:.1f}%)")
        report.append(f"Flagged for review:  {flagged}/{len(samples)} ({flagged/len(samples)*100:.1f}%)")
        
        report.append("")
        
        # Wall thickness check
        wall_thickness = []
        for sample in samples:
            wt = sample.get('Wall_Thickness_mm', '')
            if wt and wt != '':
                try:
                    wall_thickness.append(float(wt))
                except (ValueError, TypeError):
                    pass
        
        report.append("MORPHOLOGICAL DATA:")
        report.append("-" * 70)
        report.append(f"Wall thickness data: {len(wall_thickness)}/{len(samples)} samples")
        if wall_thickness:
            report.append(f"Range: {min(wall_thickness):.1f} - {max(wall_thickness):.1f} mm")
            report.append(f"Mean:  {np.mean(wall_thickness):.1f} ± {np.std(wall_thickness):.1f} mm")
        
        report.append("")
        report.append("=" * 70)
        report.append("RECOMMENDATIONS:")
        report.append("=" * 70)
        
        if missing > len(samples) * 0.3:
            report.append("⚠ More than 30% missing data detected")
            report.append("  → Consider re-analyzing samples with XRF or ICP-MS")
        
        if flagged > len(samples) * 0.2:
            report.append("⚠ More than 20% of samples flagged for review")
            report.append("  → Check samples with unusual geochemistry")
        
        if len(wall_thickness) < len(samples) * 0.5:
            report.append("⚠ Less than 50% of samples have wall thickness data")
            report.append("  → Morphological data aids classification")
        
        if classified < len(samples):
            report.append("ℹ Not all samples have final classifications")
            report.append("  → Review auto-classifications and assign final values")
        
        report.append("")
        report.append("✓ Validation complete")
        
        # Display report
        results_text.insert("1.0", "\n".join(report))
        results_text.config(state=tk.DISABLED)
    
    def _create_missing_data_tab(self, notebook):
        """Create missing data analysis tab"""
        frame = tk.Frame(notebook)
        notebook.add(frame, text="Missing Data")
        
        tk.Label(frame,
                text="Missing Data Analysis",
                font=("Arial", 12, "bold")).pack(pady=5)
        
        tk.Label(frame,
                text="Identify samples with incomplete geochemical data",
                font=("Arial", 9), fg="gray").pack()
        
        tk.Button(frame, text="▶ Analyze Missing Data",
                 command=self._analyze_missing,
                 bg="#2196F3", fg="white",
                 font=("Arial", 10, "bold"),
                 width=20, height=2).pack(pady=8)
        
        self.missing_frame = tk.Frame(frame)
        self.missing_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
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
        elements = ['Zr_ppm', 'Nb_ppm', 'Ba_ppm', 'Rb_ppm', 'Cr_ppm', 'Ni_ppm']
        
        missing_by_sample = []
        
        for sample in samples:
            missing_count = 0
            for elem in elements:
                val = sample.get(elem, '')
                if val == '' or val is None:
                    missing_count += 1
                else:
                    try:
                        float(val)
                    except (ValueError, TypeError):
                        missing_count += 1
            
            if missing_count > 0:
                missing_by_sample.append({
                    'id': sample.get('Sample_ID', 'Unknown'),
                    'missing': missing_count,
                    'percent': missing_count / len(elements) * 100
                })
        
        if not missing_by_sample:
            tk.Label(self.missing_frame,
                    text="✓ No missing data detected!\n\nAll samples have complete geochemical data.",
                    font=("Arial", 12),
                    fg="green").pack(expand=True)
            return
        
        # Display results
        tk.Label(self.missing_frame,
                text=f"Found {len(missing_by_sample)} samples with missing data:",
                font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=10, pady=5)
        
        # Create table
        tree_frame = tk.Frame(self.missing_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        tree = ttk.Treeview(tree_frame, columns=('Sample ID', 'Missing Elements', 'Percent'),
                           show='headings', yscrollcommand=scrollbar.set)
        scrollbar.config(command=tree.yview)
        
        tree.heading('Sample ID', text='Sample ID')
        tree.heading('Missing Elements', text='Missing Elements')
        tree.heading('Percent', text='% Missing')
        
        tree.column('Sample ID', width=200)
        tree.column('Missing Elements', width=150)
        tree.column('Percent', width=100)
        
        # Sort by missing count
        missing_by_sample.sort(key=lambda x: x['missing'], reverse=True)
        
        for item in missing_by_sample:
            tree.insert('', tk.END, values=(
                item['id'],
                f"{item['missing']} of 6",
                f"{item['percent']:.0f}%"
            ))
        
        tree.pack(fill=tk.BOTH, expand=True)
    
    def _create_outlier_tab(self, notebook):
        """Create outlier detection tab"""
        frame = tk.Frame(notebook)
        notebook.add(frame, text="Outliers")
        
        tk.Label(frame,
                text="Statistical Outlier Detection",
                font=("Arial", 12, "bold")).pack(pady=5)
        
        tk.Label(frame,
                text="Identify samples with unusual geochemistry (>3σ from mean)",
                font=("Arial", 9), fg="gray").pack()
        
        tk.Button(frame, text="▶ Detect Outliers",
                 command=self._detect_outliers,
                 bg="#FF9800", fg="white",
                 font=("Arial", 10, "bold"),
                 width=20, height=2).pack(pady=8)
        
        self.outlier_frame = tk.Frame(frame)
        self.outlier_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
    def _detect_outliers(self):
        """Detect statistical outliers"""
        samples = self.app.samples
        
        if not samples:
            messagebox.showwarning("No Data", "No samples to analyze")
            return
        
        # Clear previous
        for widget in self.outlier_frame.winfo_children():
            widget.destroy()
        
        elements = ['Zr_ppm', 'Nb_ppm', 'Ba_ppm', 'Rb_ppm', 'Cr_ppm', 'Ni_ppm']
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
            
            if len(values) > 3:
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
                    font=("Arial", 12),
                    fg="green").pack(expand=True)
            return
        
        # Display outliers
        tk.Label(self.outlier_frame,
                text=f"Found {len(outliers)} statistical outlier(s):",
                font=("Arial", 10, "bold"),
                fg="orange").pack(anchor=tk.W, padx=10, pady=5)
        
        tk.Label(self.outlier_frame,
                text="(Values more than 3 standard deviations from mean)",
                font=("Arial", 8), fg="gray").pack(anchor=tk.W, padx=10)
        
        # Create table
        tree_frame = tk.Frame(self.outlier_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        tree = ttk.Treeview(tree_frame, 
                           columns=('Sample', 'Element', 'Value', 'Z-Score', 'Mean'),
                           show='headings', yscrollcommand=scrollbar.set)
        scrollbar.config(command=tree.yview)
        
        tree.heading('Sample', text='Sample ID')
        tree.heading('Element', text='Element')
        tree.heading('Value', text='Value')
        tree.heading('Z-Score', text='Z-Score')
        tree.heading('Mean', text='Population Mean')
        
        for col in ('Sample', 'Element', 'Value', 'Z-Score', 'Mean'):
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
    
    def _create_report_tab(self, notebook):
        """Create validation report tab"""
        frame = tk.Frame(notebook)
        notebook.add(frame, text="Report")
        
        tk.Label(frame,
                text="Generate Validation Report",
                font=("Arial", 12, "bold")).pack(pady=5)
        
        tk.Button(frame, text="▶ Generate Full Report",
                 command=self._generate_report,
                 bg="#9C27B0", fg="white",
                 font=("Arial", 10, "bold"),
                 width=20, height=2).pack(pady=8)
        
        tk.Label(frame,
                text="Creates a comprehensive validation report with all checks",
                font=("Arial", 9), fg="gray").pack()

def setup_plugin(main_app):
    """Plugin setup function"""
    plugin = DataValidationPlugin(main_app)
    return plugin  # ← REMOVE ALL MENU CODE
