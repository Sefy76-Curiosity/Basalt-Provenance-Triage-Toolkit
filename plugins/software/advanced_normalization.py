"""
Advanced Normalization & Matrix Correction Plugin
Industry-standard corrections for pXRF/ICP with full functionality
"""

PLUGIN_INFO = {
    "category": "software",
    "field": "Geology & Geochemistry",
    "id": "advanced_normalization",
    "name": "Advanced Normalization",
    "description": "Lucas-Tooth & Compton normalization for pXRF/ICP with comparison tables",
    "icon": "⚖️",
    "version": "1.2",
    "requires": ["numpy", "pandas", "matplotlib"],
    "author": "Sefy Levy & DeepSeek",

    "item": {
        "type": "plugin",
        "subtype": "normalization_tool",
        "tags": ["normalization", "matrix", "pXRF", "ICP", "Lucas-Tooth", "Compton"],
        "compatibility": ["main_app_v2+"],
        "dependencies": ["numpy>=1.19.0", "pandas>=1.0.0", "matplotlib>=3.3.0"],
        "settings": {
            "default_method": "lucas_tooth",
            "show_comparison": True,
            "auto_import": True
        }
    }
}

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import pandas as pd
import numpy as np
import threading
import time
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class AdvancedNormalizationPlugin:
    def __init__(self, main_app):
        self.app = main_app
        self.window = None
        self.df = pd.DataFrame()
        self.is_processing = False
        self.progress = None

        # Industry-standard correction methods
        self.CORRECTION_METHODS = {
            "Lucas-Tooth (Pyne)": "Linear correction using reference element intensity",
            "Compton Normalization": "Scatter peak normalization for pXRF",
            "Net Peak Area": "Simple background subtraction",
            "Ratio Normalization": "Normalize to internal standard"
        }

        # Reference elements for different methods
        self.REFERENCE_ELEMENTS = ["Rh", "Mo", "Zr", "Sr", "Rb", "In", "Re", "Y"]

        # Common elements in geochemistry
        self.COMMON_ELEMENTS = [
            "Si", "Al", "Fe", "Ca", "K", "Ti", "Mn", "Mg", "Na",
            "Sr", "Zr", "Rb", "Zn", "Cu", "Pb", "Ni", "Cr", "V"
        ]

    def open_window(self):
        """Open the main window"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title(f"{PLUGIN_INFO['icon']} {PLUGIN_INFO['name']} v{PLUGIN_INFO['version']}")
        self.window.geometry("1000x700")
        self._create_ui()

        # Auto-load data from main table if available
        if hasattr(self.app, 'samples') and self.app.samples:
            self.window.after(200, self._start_processing)

    def _create_ui(self):
        """Create the user interface"""
        # Header
        header = tk.Frame(self.window, bg="#2c3e50")
        header.pack(fill=tk.X)
        tk.Label(header, text="⚖️ Advanced Matrix Correction",
                font=("Arial", 16, "bold"),
                bg="#2c3e50", fg="white", pady=12).pack()

        # Main container with panes
        main_paned = tk.PanedWindow(self.window, orient=tk.HORIZONTAL, sashwidth=8)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left panel - Controls
        left_panel = tk.Frame(main_paned, bg="#ecf0f1", relief=tk.RAISED, borderwidth=1)
        main_paned.add(left_panel, minsize=400)

        # Right panel - Results
        right_panel = tk.Frame(main_paned, bg="white")
        main_paned.add(right_panel, minsize=900)

        self._setup_left_panel(left_panel)
        self._setup_right_panel(right_panel)

    def _setup_left_panel(self, parent):
        """Setup control panel"""
        # Method selection frame
        method_frame = tk.LabelFrame(parent, text="🔄 Correction Method",
                                    padx=10, pady=10, bg="#ecf0f1")
        method_frame.pack(fill=tk.X, padx=10, pady=10)

        self.method_var = tk.StringVar(value="Lucas-Tooth (Pyne)")
        for method in self.CORRECTION_METHODS.keys():
            tk.Radiobutton(method_frame, text=method, variable=self.method_var,
                          value=method, bg="#ecf0f1").pack(anchor=tk.W, pady=2)

        # Method description
        self.method_desc = tk.Label(method_frame, text=self.CORRECTION_METHODS["Lucas-Tooth (Pyne)"],
                                   wraplength=350, bg="#ecf0f1", justify=tk.LEFT, height=2)
        self.method_desc.pack(fill=tk.X, pady=5)

        # Parameters frame
        params_frame = tk.LabelFrame(parent, text="⚙️ Parameters",
                                    padx=10, pady=10, bg="#ecf0f1")
        params_frame.pack(fill=tk.X, padx=10, pady=10)

        # Reference element for Lucas-Tooth
        tk.Label(params_frame, text="Reference Element:", bg="#ecf0f1").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.ref_element_var = tk.StringVar(value="Rh")
        ref_combo = ttk.Combobox(params_frame, textvariable=self.ref_element_var,
                                values=self.REFERENCE_ELEMENTS, width=15, state="readonly")
        ref_combo.grid(row=0, column=1, padx=5, pady=5)

        # Calibration factor
        tk.Label(params_frame, text="Calibration Factor:", bg="#ecf0f1").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.calib_var = tk.DoubleVar(value=1.0)
        tk.Spinbox(params_frame, from_=0.1, to=5.0, increment=0.1,
                  textvariable=self.calib_var, width=10).grid(row=1, column=1, padx=5, pady=5)

        # Elements selection
        elem_frame = tk.LabelFrame(parent, text="🧪 Elements to Correct",
                                  padx=10, pady=10, bg="#ecf0f1")
        elem_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.elements_text = scrolledtext.ScrolledText(elem_frame, height=10)
        self.elements_text.pack(fill=tk.BOTH, expand=True)

        # Add default elements
        default_elements = "\n".join(self.COMMON_ELEMENTS[:10])
        self.elements_text.insert(1.0, default_elements)

        # Action buttons frame
        button_frame = tk.Frame(parent, bg="#ecf0f1", pady=10)
        button_frame.pack(fill=tk.X, padx=10)

        # MAIN PROCESS BUTTON
        self.process_btn = tk.Button(button_frame, text="⚡ Apply Correction",
                                    bg="#9b59b6", fg="white", font=("Arial", 10, "bold"),
                                    width=20, command=self._start_processing)
        self.process_btn.pack(side=tk.LEFT, padx=5)

        # COMPARE BUTTON - Show raw vs corrected
        self.compare_btn = tk.Button(button_frame, text="📊 Compare Results",
                                    bg="#3498db", fg="white", width=15,
                                    command=self._show_comparison)
        self.compare_btn.pack(side=tk.LEFT, padx=5)

        # IMPORT BUTTON
        self.import_btn = tk.Button(button_frame, text="📥 Import to App",
                                   bg="#27ae60", fg="white", width=15,
                                   command=self._import_to_main)
        self.import_btn.pack(side=tk.LEFT, padx=5)

        # CLEAR BUTTON
        tk.Button(button_frame, text="🗑️ Clear Results", bg="#e74c3c", fg="white",
                 width=15, command=self._clear_results).pack(side=tk.LEFT, padx=5)

        # Checkboxes frame
        check_frame = tk.Frame(parent, bg="#ecf0f1")
        check_frame.pack(fill=tk.X, padx=10, pady=5)

        self.show_plot_var = tk.BooleanVar(value=True)
        tk.Checkbutton(check_frame, text="Show Comparison Plot",
                      variable=self.show_plot_var, bg="#ecf0f1").pack(side=tk.LEFT, padx=5)

        self.auto_import_var = tk.BooleanVar(value=True)
        tk.Checkbutton(check_frame, text="Auto-import after processing",
                      variable=self.auto_import_var, bg="#ecf0f1").pack(side=tk.LEFT, padx=5)

        # Status and progress
        status_frame = tk.Frame(parent, bg="#ecf0f1")
        status_frame.pack(fill=tk.X, padx=10, pady=5)

        self.status_label = tk.Label(status_frame, text="Ready to process",
                                    bg="#ecf0f1", fg="#7f8c8d", anchor=tk.W)
        self.status_label.pack(fill=tk.X, side=tk.LEFT)

        self.progress = ttk.Progressbar(parent, mode='indeterminate', length=100)
        self.progress.pack(fill=tk.X, padx=10, pady=5)

    def _setup_right_panel(self, parent):
        """Setup results panel"""
        # Notebook for tabs
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Results table tab
        results_tab = tk.Frame(self.notebook)
        self.notebook.add(results_tab, text="📋 Results Table")

        # Treeview for results
        tree_frame = tk.Frame(results_tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")

        self.tree = ttk.Treeview(tree_frame, yscrollcommand=vsb.set,
                                xscrollcommand=hsb.set, selectmode="extended")
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)

        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Plot tab
        plot_tab = tk.Frame(self.notebook)
        self.notebook.add(plot_tab, text="📈 Comparison Plot")

        self.figure = plt.Figure(figsize=(7, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, plot_tab)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Stats tab
        stats_tab = tk.Frame(self.notebook)
        self.notebook.add(stats_tab, text="📊 Statistics")

        self.stats_text = scrolledtext.ScrolledText(stats_tab, wrap=tk.WORD, font=("Courier", 10))
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Log tab
        log_tab = tk.Frame(self.notebook)
        self.notebook.add(log_tab, text="📝 Processing Log")

        self.log_text = scrolledtext.ScrolledText(log_tab, wrap=tk.WORD, font=("Courier", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # ==================== BUTTON FUNCTIONS ====================

    def _start_processing(self):
        """Start processing data"""
        if self.is_processing:
            return

        # Check if app has data
        if not hasattr(self.app, 'samples') or not self.app.samples:
            self.window.lift()
            messagebox.showwarning("No Data", "Please load data in the main application first!")
            return

        self.is_processing = True
        self.process_btn.config(state=tk.DISABLED, text="Processing...")
        self.compare_btn.config(state=tk.DISABLED)
        self.import_btn.config(state=tk.DISABLED)
        self.progress.start()
        self.status_label.config(text="Processing data...", fg="orange")

        # Get elements from text widget
        elements_text = self.elements_text.get(1.0, tk.END)
        elements = [e.strip() for e in elements_text.replace('\n', ',').split(',')
                   if e.strip() and not e.startswith('#')]

        # Start processing thread
        thread = threading.Thread(target=self._process_data, args=(elements,), daemon=True)
        thread.start()

    def _process_data(self, elements):
        """Process matrix correction in thread"""
        try:
            # Get data from main app
            self.df = pd.DataFrame(self.app.samples)

            # Convert numeric columns
            for col in self.df.columns:
                if col not in ['Sample_ID', 'Notes']:
                    try:
                        self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
                    except:
                        pass

            # Get method and apply correction
            method = self.method_var.get()
            corrected_data = self._apply_correction(method, elements)

            # Update DataFrame
            self._update_dataframe(corrected_data, method)

            # Update UI in main thread
            self.window.after(0, self._update_results_ui)

        except Exception as e:
            self.window.after(0, lambda: messagebox.showerror("Error", f"Processing failed: {str(e)}"))
        finally:
            self.window.after(0, self._reset_processing_ui)

    def _apply_correction(self, method, elements):
        """Apply the selected correction method"""
        results = {}

        if "Lucas-Tooth" in method:
            # Lucas-Tooth linear correction
            ref_element = self.ref_element_var.get()
            alpha = self.calib_var.get()

            # Find reference element in data
            ref_col = next((col for col in self.df.columns if ref_element.lower() in col.lower()), None)

            if ref_col:
                I_ref = self.df[ref_col].fillna(1).values

                for element in elements:
                    element_col = next((col for col in self.df.columns if element.lower() in col.lower()), None)
                    if element_col:
                        I_element = self.df[element_col].values
                        # Lucas-Tooth: C = α * (I_element / I_ref)
                        C_corrected = alpha * (I_element / I_ref)
                        results[f"{element}_raw"] = I_element
                        results[f"{element}_corr"] = C_corrected

        elif "Compton" in method:
            # Compton normalization (simplified)
            total_counts = self.df.select_dtypes(include=[np.number]).sum(axis=1).fillna(1).values

            for element in elements:
                element_col = next((col for col in self.df.columns if element.lower() in col.lower()), None)
                if element_col:
                    I_element = self.df[element_col].values
                    # Compton: C = I_element / total_counts
                    C_corrected = I_element / total_counts
                    results[f"{element}_raw"] = I_element
                    results[f"{element}_corr"] = C_corrected

        else:
            # Simple ratio normalization
            for element in elements:
                element_col = next((col for col in self.df.columns if element.lower() in col.lower()), None)
                if element_col:
                    I_element = self.df[element_col].values
                    # Simple: subtract minimum as background
                    bg = np.nanmin(I_element)
                    C_corrected = I_element - bg
                    C_corrected[C_corrected < 0] = 0
                    results[f"{element}_raw"] = I_element
                    results[f"{element}_corr"] = C_corrected

        return results

    def _update_dataframe(self, corrected_data, method):
        """Update DataFrame with corrected results"""
        # Add corrected columns
        for col, values in corrected_data.items():
            self.df[col] = values

        # Add metadata
        self.df['Correction_Method'] = method
        self.df['Process_Date'] = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Calculate changes for elements with both raw and corrected
        for col in self.df.columns:
            if '_raw' in col:
                element = col.replace('_raw', '')
                corr_col = f"{element}_corr"
                if corr_col in self.df.columns:
                    raw_vals = self.df[col]
                    corr_vals = self.df[corr_col]
                    # Calculate percent change where raw > 0
                    mask = (raw_vals > 0) & (~pd.isna(raw_vals))
                    pct_change = np.where(mask, ((corr_vals - raw_vals) / raw_vals) * 100, np.nan)
                    self.df[f"{element}_pct"] = pct_change

    def _update_results_ui(self):
        """Update all UI elements after processing"""
        # Update results table
        self._update_results_table()

        # Update plot if enabled
        if self.show_plot_var.get():
            self._update_plot()

        # Update statistics
        self._update_statistics()

        # Add to log
        log_msg = f"[{datetime.now().strftime('%H:%M:%S')}] Processed {len(self.df)} samples using {self.method_var.get()}\n"
        self.log_text.insert(tk.END, log_msg)
        self.log_text.see(tk.END)

        # Update status
        self.status_label.config(text=f"Processed {len(self.df)} samples", fg="green")

        # Auto-import if enabled
        if self.auto_import_var.get():
            self.window.after(100, self._import_to_main)

    def _update_results_table(self):
        """Update the results treeview"""
        # Clear existing
        for item in self.tree.get_children():
            self.tree.delete(item)

        if self.df.empty:
            return

        # Setup columns - show Sample_ID and first few corrected elements
        columns = ['Sample_ID']
        # Add corrected columns (limit to 5 for display)
        corr_cols = [col for col in self.df.columns if '_corr' in col][:5]
        columns.extend(corr_cols)

        self.tree["columns"] = columns
        self.tree["show"] = "headings"

        # Configure columns
        for col in columns:
            display_name = col.replace('_corr', ' (Corr)')
            self.tree.heading(col, text=display_name)
            self.tree.column(col, width=100, anchor=tk.CENTER)

        # Add data (first 20 samples)
        display_df = self.df.head(20)
        for idx, row in display_df.iterrows():
            values = [row.get('Sample_ID', f"SMP_{idx}")]
            for col in corr_cols:
                val = row.get(col, np.nan)
                values.append(f"{val:.2f}" if not pd.isna(val) else "")
            self.tree.insert("", tk.END, values=values)

    def _update_plot(self):
        """Update the comparison plot"""
        self.ax.clear()

        # Find elements to plot
        plot_elements = []
        for col in self.df.columns:
            if '_raw' in col:
                element = col.replace('_raw', '')
                if f"{element}_corr" in self.df.columns:
                    plot_elements.append(element)

        if not plot_elements:
            self.ax.text(0.5, 0.5, 'No corrected data to plot\nApply correction first',
                        ha='center', va='center', transform=self.ax.transAxes, fontsize=12)
            self.canvas.draw()
            return

        # Plot first element
        element = plot_elements[0]
        samples = self.df.head(15)  # Limit to 15 samples for clarity

        x = np.arange(len(samples))
        width = 0.35

        raw_vals = samples[f"{element}_raw"].values
        corr_vals = samples[f"{element}_corr"].values

        self.ax.bar(x - width/2, raw_vals, width, label=f'{element} (Raw)', alpha=0.7, color='skyblue')
        self.ax.bar(x + width/2, corr_vals, width, label=f'{element} (Corrected)', alpha=0.7, color='lightcoral')

        self.ax.set_xlabel('Sample Index')
        self.ax.set_ylabel('Value')
        self.ax.set_title(f'Raw vs Corrected: {element}')
        self.ax.legend()
        self.ax.grid(True, alpha=0.3)
        self.ax.set_xticks(x)
        self.ax.set_xticklabels([f"S{i}" for i in range(len(samples))])

        self.canvas.draw()

    def _update_statistics(self):
        """Update statistics text"""
        if self.df.empty:
            self.stats_text.delete(1.0, tk.END)
            return

        stats_text = "CORRECTION STATISTICS\n"
        stats_text += "=" * 40 + "\n\n"
        stats_text += f"Method: {self.method_var.get()}\n"
        stats_text += f"Reference Element: {self.ref_element_var.get()}\n"
        stats_text += f"Calibration Factor: {self.calib_var.get()}\n"
        stats_text += f"Samples Processed: {len(self.df)}\n\n"

        stats_text += "ELEMENT CHANGES:\n"
        stats_text += "-" * 30 + "\n"

        # Calculate stats for each corrected element
        for col in self.df.columns:
            if '_corr' in col:
                element = col.replace('_corr', '')
                raw_col = f"{element}_raw"
                pct_col = f"{element}_pct"

                if raw_col in self.df.columns:
                    raw_mean = self.df[raw_col].mean()
                    corr_mean = self.df[col].mean()

                    if pct_col in self.df.columns:
                        pct_mean = self.df[pct_col].mean()
                        stats_text += f"{element:5s}: {raw_mean:7.2f} → {corr_mean:7.2f} (Δ{pct_mean:+6.1f}%)\n"
                    else:
                        stats_text += f"{element:5s}: {raw_mean:7.2f} → {corr_mean:7.2f}\n"

        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats_text)

    def _reset_processing_ui(self):
        """Reset UI after processing"""
        self.is_processing = False
        self.process_btn.config(state=tk.NORMAL, text="⚡ Apply Correction")
        self.compare_btn.config(state=tk.NORMAL)
        self.import_btn.config(state=tk.NORMAL)
        self.progress.stop()

    def _show_comparison(self):
        """Show comparison table"""
        if self.df.empty:
            messagebox.showinfo("No Data", "Process data first to see comparison")
            return

        # Switch to results tab
        self.notebook.select(0)

    def _clear_results(self):
        """Clear all results"""
        self.df = pd.DataFrame()

        # Clear treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Clear plot
        self.ax.clear()
        self.ax.text(0.5, 0.5, 'No data\nProcess data to see results',
                    ha='center', va='center', transform=self.ax.transAxes, fontsize=12)
        self.canvas.draw()

        # Clear stats
        self.stats_text.delete(1.0, tk.END)

        # Clear log
        self.log_text.delete(1.0, tk.END)

        # Update status
        self.status_label.config(text="Results cleared", fg="blue")

    # ==================== IMPORT METHOD ====================

    def _import_to_main(self):
        """Import processed data to main app - using working pattern from geochem_advanced"""
        if self.df.empty:
            self.window.lift()
            messagebox.showwarning("No Data", "No processed data to import!")
            return

        try:
            # Prepare table data in the format expected by import_data_from_plugin
            table_data = []
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Process each sample
            for idx, row in self.df.iterrows():
                sample_entry = {
                    # REQUIRED: Sample_ID
                    'Sample_ID': row.get('Sample_ID', f"NOR-{idx+1:04d}"),

                    # Metadata
                    'Timestamp': timestamp,
                    'Source': 'Matrix Correction',
                    'Analysis_Type': 'Normalized Data',
                    'Plugin': PLUGIN_INFO['name'],

                    # REQUIRED: Notes field
                    'Notes': f"Method: {self.method_var.get()} | Ref: {self.ref_element_var.get()}"
                }

                # Add all data columns
                for col in self.df.columns:
                    if col not in ['Sample_ID', 'Timestamp', 'Plugin']:  # Skip as we already set them
                        val = row[col]
                        if pd.notna(val):
                            # Format numbers appropriately
                            if isinstance(val, (int, float)):
                                if '_ppm' in col.lower() or col in ['Zr', 'Nb', 'Ba', 'Rb', 'Cr', 'Ni']:
                                    sample_entry[col] = f"{val:.1f}"
                                elif '_pct' in col or 'ratio' in col.lower():
                                    sample_entry[col] = f"{val:.2f}"
                                else:
                                    sample_entry[col] = f"{val:.3f}"
                            else:
                                sample_entry[col] = str(val)

                table_data.append(sample_entry)

            # Send to main app using the STANDARDIZED method
            if hasattr(self.app, 'import_data_from_plugin'):
                self.app.import_data_from_plugin(table_data)
                self.status_label.config(text=f"✅ Imported {len(table_data)} samples", fg="green")

                # Log the import
                self.log_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Imported {len(table_data)} normalized samples\n")
                self.log_text.see(tk.END)

                # Show success message
                self.window.lift()
                messagebox.showinfo("Success", f"✅ Imported {len(table_data)} normalized samples to main table!")
            else:
                # Fallback if method doesn't exist
                messagebox.showerror("Error", "Main application doesn't support plugin data import")

        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import data: {str(e)}")

def setup_plugin(main_app):
    """Plugin setup function"""
    plugin = AdvancedNormalizationPlugin(main_app)
    return plugin
