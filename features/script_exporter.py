"""
Script Exporter - Export data processing workflows as Python scripts
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

class ScriptExporter:
    """
    Exports data processing workflows as executable Python scripts
    """
    def __init__(self, app):
        self.app = app
    
    def export_current_workflow(self):
        """Export current state as a Python or R script"""
        
        dialog = tk.Toplevel(self.app.root)
        dialog.title("Export to Script")
        dialog.geometry("500x450")
        dialog.transient(self.app.root)
        
        main = ttk.Frame(dialog, padding=10)
        main.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main, text="Export Workflow to Script", 
                 font=("TkDefaultFont", 12, "bold")).pack(pady=(0, 10))
        
        # Language selection
        lang_frame = ttk.LabelFrame(main, text="Script Language", padding=10)
        lang_frame.pack(fill=tk.X, pady=(0, 10))
        
        language = tk.StringVar(value="python")
        ttk.Radiobutton(lang_frame, text="🐍 Python", 
                       variable=language, value="python").pack(anchor=tk.W)
        ttk.Radiobutton(lang_frame, text="📊 R", 
                       variable=language, value="r").pack(anchor=tk.W)
        
        ttk.Label(main, text="Select components to include:").pack(anchor=tk.W, pady=(0, 5))
        
        # Checkboxes for options
        options_frame = ttk.Frame(main)
        options_frame.pack(fill=tk.X, pady=5)
        
        include_data = tk.BooleanVar(value=True)
        include_classification = tk.BooleanVar(value=True)
        include_plots = tk.BooleanVar(value=True)
        include_filters = tk.BooleanVar(value=True)
        standalone = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(options_frame, text="Include current data", 
                       variable=include_data).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(options_frame, text="Include classification logic", 
                       variable=include_classification).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(options_frame, text="Include plotting code", 
                       variable=include_plots).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(options_frame, text="Include current filters", 
                       variable=include_filters).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(options_frame, text="Make standalone (runnable)", 
                       variable=standalone).pack(anchor=tk.W, pady=2)
        
        def do_export():
            options = {
                'include_data': include_data.get(),
                'include_classification': include_classification.get(),
                'include_plots': include_plots.get(),
                'include_filters': include_filters.get(),
                'standalone': standalone.get(),
                'language': language.get()
            }
            
            if language.get() == "python":
                script_content = self._generate_python_script(options)
                extension = ".py"
                file_types = [("Python files", "*.py"), ("All files", "*.*")]
            else:
                script_content = self._generate_r_script(options)
                extension = ".R"
                file_types = [("R files", "*.R"), ("All files", "*.*")]
            
            filepath = filedialog.asksaveasfilename(
                defaultextension=extension,
                filetypes=file_types,
                initialfile=f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}{extension}"
            )
            
            if filepath:
                try:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(script_content)
                    messagebox.showinfo("Success", f"Script exported to:\n{filepath}")
                    dialog.destroy()
                except Exception as e:
                    messagebox.showerror("Error", f"Export failed:\n{e}")
        
        ttk.Button(main, text="Export", command=do_export).pack(pady=10)
        ttk.Button(main, text="Cancel", command=dialog.destroy).pack()
    
    def _generate_python_script(self, options: Dict[str, bool]) -> str:
        """Generate Python script content"""
        
        lines = []
        
        # Header
        lines.append('#!/usr/bin/env python3')
        lines.append('"""')
        lines.append(f'Scientific Toolkit Workflow Export')
        lines.append(f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        lines.append('"""')
        lines.append('')
        
        # Imports
        if options['standalone']:
            lines.append('import pandas as pd')
            lines.append('import json')
            lines.append('from pathlib import Path')
            
            if options['include_plots']:
                lines.append('import matplotlib.pyplot as plt')
                lines.append('import seaborn as sns')
            
            lines.append('')
        
        # Data section
        if options['include_data']:
            lines.append('# ============ DATA ============')
            lines.append('# Current dataset')
            lines.append('data = [')
            
            samples = self.app.data_hub.get_all()
            for sample in samples[:10]:  # Limit to first 10 for readability
                lines.append(f'    {sample},')
            
            if len(samples) > 10:
                lines.append(f'    # ... and {len(samples) - 10} more samples')
            
            lines.append(']')
            lines.append('')
            lines.append('# Convert to DataFrame')
            lines.append('df = pd.DataFrame(data)')
            lines.append(f'print(f"Loaded {{len(df)}} samples")')
            lines.append('')
        
        # Filters section
        if options['include_filters'] and hasattr(self.app, 'center'):
            search_text = self.app.center.search_var.get()
            filter_val = self.app.center.filter_var.get()
            
            if search_text or filter_val != "All":
                lines.append('# ============ FILTERS ============')
                
                if search_text:
                    lines.append(f'# Apply search filter: "{search_text}"')
                    lines.append(f'search_term = "{search_text}"')
                    lines.append('df_filtered = df[df.astype(str).apply(')
                    lines.append('    lambda row: row.str.contains(search_term, case=False).any(), axis=1')
                    lines.append(')]')
                    lines.append('')
                
                if filter_val and filter_val != "All":
                    lines.append(f'# Apply classification filter: "{filter_val}"')
                    lines.append(f'df_filtered = df[df["Classification"] == "{filter_val}"]')
                    lines.append('')
        
        # Classification section
        if options['include_classification']:
            lines.append('# ============ CLASSIFICATION LOGIC ============')
            lines.append('def classify_sample(sample):')
            lines.append('    """')
            lines.append('    Classification logic based on current scheme')
            lines.append('    """')
            lines.append('    # Add your classification logic here')
            lines.append('    return "UNCLASSIFIED"')
            lines.append('')
            lines.append('# Apply classification')
            lines.append('if "Classification" not in df.columns:')
            lines.append('    df["Classification"] = df.apply(classify_sample, axis=1)')
            lines.append('')
        
        # Plotting section
        if options['include_plots']:
            lines.append('# ============ PLOTTING ============')
            lines.append('def create_plots():')
            lines.append('    """Generate analysis plots"""')
            lines.append('    ')
            lines.append('    # Example: Classification distribution')
            lines.append('    if "Classification" in df.columns:')
            lines.append('        plt.figure(figsize=(10, 6))')
            lines.append('        df["Classification"].value_counts().plot(kind="bar")')
            lines.append('        plt.title("Classification Distribution")')
            lines.append('        plt.xlabel("Classification")')
            lines.append('        plt.ylabel("Count")')
            lines.append('        plt.xticks(rotation=45, ha="right")')
            lines.append('        plt.tight_layout()')
            lines.append('        plt.savefig("classification_distribution.png")')
            lines.append('        print("Saved: classification_distribution.png")')
            lines.append('        plt.close()')
            lines.append('')
        
        # Main execution
        if options['standalone']:
            lines.append('# ============ MAIN ============')
            lines.append('if __name__ == "__main__":')
            lines.append('    print("="*50)')
            lines.append('    print("Scientific Toolkit Workflow")')
            lines.append('    print("="*50)')
            lines.append('    ')
            
            if options['include_data']:
                lines.append('    print(f"\\nDataset: {len(df)} samples")')
                lines.append('    print(f"Columns: {list(df.columns)}")')
            
            if options['include_classification']:
                lines.append('    ')
                lines.append('    print("\\nRunning classification...")')
                lines.append('    # Classification already applied above')
            
            if options['include_plots']:
                lines.append('    ')
                lines.append('    print("\\nGenerating plots...")')
                lines.append('    create_plots()')
            
            lines.append('    ')
            lines.append('    print("\\n✓ Workflow complete!")')
        
        return '\n'.join(lines)
    
    def _generate_r_script(self, options: Dict[str, bool]) -> str:
        """Generate R script content"""
        
        lines = []
        
        # Header
        lines.append('#!/usr/bin/env Rscript')
        lines.append('#')
        lines.append(f'# Scientific Toolkit Workflow Export (R)')
        lines.append(f'# Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        lines.append('#')
        lines.append('')
        
        # Imports/Libraries
        if options['standalone']:
            lines.append('# Load required libraries')
            lines.append('library(dplyr)')
            lines.append('library(tidyr)')
            
            if options['include_plots']:
                lines.append('library(ggplot2)')
            
            lines.append('')
        
        # Data section
        if options['include_data']:
            lines.append('# ============ DATA ============')
            lines.append('# Current dataset')
            lines.append('')
            
            samples = self.app.data_hub.get_all()
            
            if samples:
                # Extract column names from first sample
                columns = list(samples[0].keys())
                
                lines.append('# Create data frame')
                lines.append('data <- data.frame(')
                
                # Add data for each column
                for i, col in enumerate(columns):
                    values = [str(sample.get(col, 'NA')) for sample in samples[:10]]
                    values_str = ', '.join([f'"{v}"' if isinstance(v, str) else str(v) for v in values])
                    
                    if len(samples) > 10:
                        suffix = ', # ... truncated'
                    else:
                        suffix = ''
                    
                    comma = ',' if i < len(columns) - 1 else ''
                    lines.append(f'  {col} = c({values_str}{suffix}){comma}')
                
                lines.append(')')
                lines.append('')
                lines.append(f'cat("Loaded", nrow(data), "samples\\n")')
                lines.append('')
        
        # Filters section
        if options['include_filters'] and hasattr(self.app, 'center'):
            search_text = self.app.center.search_var.get()
            filter_val = self.app.center.filter_var.get()
            
            if search_text or filter_val != "All":
                lines.append('# ============ FILTERS ============')
                lines.append('')
                
                if filter_val and filter_val != "All":
                    lines.append(f'# Filter by classification: "{filter_val}"')
                    lines.append(f'data_filtered <- data %>%')
                    lines.append(f'  filter(Classification == "{filter_val}")')
                    lines.append('')
                
                if search_text:
                    lines.append(f'# Search filter: "{search_text}"')
                    lines.append('# Note: R string matching implementation needed')
                    lines.append('')
        
        # Classification section
        if options['include_classification']:
            lines.append('# ============ CLASSIFICATION LOGIC ============')
            lines.append('')
            lines.append('classify_sample <- function(row) {')
            lines.append('  # Add your classification logic here')
            lines.append('  # Example:')
            lines.append('  # if (row$Zr_ppm / row$Nb_ppm > 10) {')
            lines.append('  #   return("HIGH_ZR_NB")')
            lines.append('  # }')
            lines.append('  return("UNCLASSIFIED")')
            lines.append('}')
            lines.append('')
            lines.append('# Apply classification')
            lines.append('if (!"Classification" %in% colnames(data)) {')
            lines.append('  data$Classification <- apply(data, 1, classify_sample)')
            lines.append('}')
            lines.append('')
        
        # Plotting section
        if options['include_plots']:
            lines.append('# ============ PLOTTING ============')
            lines.append('')
            lines.append('create_plots <- function() {')
            lines.append('  # Classification distribution plot')
            lines.append('  if ("Classification" %in% colnames(data)) {')
            lines.append('    p <- ggplot(data, aes(x = Classification)) +')
            lines.append('      geom_bar(fill = "steelblue") +')
            lines.append('      labs(')
            lines.append('        title = "Classification Distribution",')
            lines.append('        x = "Classification",')
            lines.append('        y = "Count"')
            lines.append('      ) +')
            lines.append('      theme_minimal() +')
            lines.append('      theme(axis.text.x = element_text(angle = 45, hjust = 1))')
            lines.append('    ')
            lines.append('    ggsave("classification_distribution.png", p, width = 10, height = 6)')
            lines.append('    cat("Saved: classification_distribution.png\\n")')
            lines.append('  }')
            lines.append('}')
            lines.append('')
        
        # Main execution
        if options['standalone']:
            lines.append('# ============ MAIN ============')
            lines.append('cat("================================================\\n")')
            lines.append('cat("Scientific Toolkit Workflow (R)\\n")')
            lines.append('cat("================================================\\n")')
            lines.append('')
            
            if options['include_data']:
                lines.append('cat("\\nDataset:", nrow(data), "samples\\n")')
                lines.append('cat("Columns:", paste(colnames(data), collapse = ", "), "\\n")')
            
            if options['include_classification']:
                lines.append('')
                lines.append('cat("\\nRunning classification...\\n")')
                lines.append('# Classification already applied above')
            
            if options['include_plots']:
                lines.append('')
                lines.append('cat("\\nGenerating plots...\\n")')
                lines.append('create_plots()')
            
            lines.append('')
            lines.append('cat("\\n✓ Workflow complete!\\n")')
        
        return '\n'.join(lines)
    
    def export_data_only(self):
        """Export just the data as a Python script"""
        
        lines = []
        lines.append('#!/usr/bin/env python3')
        lines.append('"""Data export from Scientific Toolkit"""')
        lines.append('')
        lines.append('import pandas as pd')
        lines.append('')
        lines.append('# Dataset')
        lines.append('data = [')
        
        samples = self.app.data_hub.get_all()
        for sample in samples:
            lines.append(f'    {sample},')
        
        lines.append(']')
        lines.append('')
        lines.append('# Create DataFrame')
        lines.append('df = pd.DataFrame(data)')
        lines.append('')
        lines.append('if __name__ == "__main__":')
        lines.append('    print(df)')
        lines.append('    ')
        lines.append('    # Save to CSV')
        lines.append('    df.to_csv("exported_data.csv", index=False)')
        lines.append('    print("\\nSaved to: exported_data.csv")')
        
        script_content = '\n'.join(lines)
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".py",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")],
            initialfile=f"data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
        )
        
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(script_content)
                messagebox.showinfo("Success", f"Data script exported to:\n{filepath}")
            except Exception as e:
                messagebox.showerror("Error", f"Export failed:\n{e}")
