"""
Literature Comparison Plugin for Basalt Provenance Toolkit
Find published samples similar to yours and auto-generate citations

Author: Sefy Levy
License: CC BY-NC-SA 4.0
"""

PLUGIN_INFO = {
      "category": "software",
    "id": "literature_comparison",
    "name": "Literature Comparison",
    "description": "Find published basalt samples similar to yours. Built-in reference database from Hartung, Rosenberg, and more",
    "icon": "📚",
    "version": "1.0",
    "requires": ["numpy"],
    "author": "Sefy Levy"
}

import tkinter as tk
from tkinter import ttk, messagebox
import math

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


class LiteratureComparisonPlugin:
    """Plugin for finding similar published samples"""
    
    # Built-in reference database (subset - full database would be much larger)
    REFERENCE_DATABASE = {
        "hartung_2017": {
            "citation": "Hartung, J. (2017). Egyptian basalt provenance study",
            "samples": [
                {  "category": "software",
    "id": "EG-18", "source": "Northern Egypt", "Zr": 142, "Nb": 19, "Cr": 1850, "Ni": 980},
                {  "category": "software",
    "id": "EG-24", "source": "Sinai ophiolite", "Zr": 95, "Nb": 8, "Cr": 3200, "Ni": 1450},
                {  "category": "software",
    "id": "EG-31", "source": "Wadi Hammamat", "Zr": 178, "Nb": 23, "Cr": 1200, "Ni": 650},
            ]
        },
        "rosenberg_2016": {
            "citation": "Rosenberg, D. et al. (2016). Basalt vessels and groundstone tools in the Levant",
            "samples": [
                {  "category": "software",
    "id": "GAL-24", "source": "Golan Heights", "Zr": 165, "Nb": 21, "Cr": 2100, "Ni": 1100},
                {  "category": "software",
    "id": "GAL-37", "source": "Galilee", "Zr": 158, "Nb": 20, "Cr": 2250, "Ni": 1200},
                {  "category": "software",
    "id": "JOR-12", "source": "Harrat Ash Shaam", "Zr": 188, "Nb": 24, "Cr": 1650, "Ni": 850},
            ]
        },
        "philip_2001": {
            "citation": "Philip, G., & Williams-Thorpe, O. (2001). Archaeological basalt sourcing",
            "samples": [
                {  "category": "software",
    "id": "HAS-08", "source": "Jordan Plateau", "Zr": 195, "Nb": 26, "Cr": 1500, "Ni": 780},
                {  "category": "software",
    "id": "GOL-15", "source": "Golan basanite", "Zr": 172, "Nb": 22, "Cr": 2050, "Ni": 1050},
            ]
        }
    }
    
    def __init__(self, main_app):
        """Initialize plugin"""
        self.app = main_app
        self.window = None
        self.comparison_results = []
    
    def open_literature_comparison_window(self):
        """Open the literature comparison interface"""
        if not HAS_NUMPY:
            messagebox.showerror(
                "Missing Dependency",
                "Literature Comparison requires numpy:\n\n"
                "Install with:\n"
                "pip3 install numpy"
            )
            return
        
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return
        
        self.window = tk.Toplevel(self.app.root)
        self.window.title("Literature Comparison")
        self.window.geometry("750x520")
        
        # Make window stay on top
        self.window.transient(self.app.root)
        
        self._create_interface()
        
        # Bring to front
        self.window.lift()
        self.window.focus_force()
    
    def _create_interface(self):
        """Create the literature comparison interface"""
        # Header
        header = tk.Frame(self.window, bg="#3F51B5")
        header.pack(fill=tk.X)
        
        tk.Label(header,
                text="📚 Literature Comparison",
                font=("Arial", 16, "bold"),
                bg="#3F51B5", fg="white",
                pady=5).pack()
        
        tk.Label(header,
                text="Find published samples similar to yours - save days of literature review",
                font=("Arial", 10),
                bg="#3F51B5", fg="white",
                pady=5).pack()
        
        # Main content
        content = tk.Frame(self.window, padx=10, pady=8)
        content.pack(fill=tk.BOTH, expand=True)
        
        # Sample selection
        select_frame = tk.LabelFrame(content, text="Select Your Sample",
                                    font=("Arial", 11, "bold"),
                                    padx=8, pady=5)
        select_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(select_frame, text="Choose a sample to compare:",
                font=("Arial", 9)).pack(anchor=tk.W, pady=5)
        
        self.sample_combo = ttk.Combobox(select_frame,
                                        values=[s.get('Sample_ID', 'Unknown')
                                               for s in self.app.samples],
                                        state="readonly",
                                        font=("Arial", 10),
                                        width=40)
        self.sample_combo.pack(anchor=tk.W, pady=5)
        
        if self.app.samples:
            self.sample_combo.current(0)
        
        # Comparison method
        method_frame = tk.Frame(select_frame)
        method_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(method_frame, text="Comparison method:",
                font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        
        self.method = tk.StringVar(value="euclidean")
        
        tk.Radiobutton(method_frame, text="Euclidean distance (simple)",
                      variable=self.method, value="euclidean",
                      font=("Arial", 9)).pack(side=tk.LEFT, padx=10)
        
        tk.Radiobutton(method, text="Weighted (emphasize provenance elements)",
                      variable=self.method, value="weighted",
                      font=("Arial", 9)).pack(side=tk.LEFT, padx=10)
        
        # Search button
        tk.Button(select_frame, text="🔍 Find Similar Samples",
                 command=self._find_similar,
                 bg="#2196F3", fg="white",
                 font=("Arial", 11, "bold"),
                 width=25, height=2).pack(pady=5)
        
        # Results frame
        results_frame = tk.LabelFrame(content, text="Similar Published Samples",
                                     font=("Arial", 11, "bold"),
                                     padx=10, pady=5)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Results tree
        tree_container = tk.Frame(results_frame)
        tree_container.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(tree_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.results_tree = ttk.Treeview(tree_container,
                                        columns=('Rank', 'Reference', 'Sample ID',
                                                'Source', 'Similarity', 'Distance'),
                                        show='headings',
                                        yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.results_tree.yview)
        
        self.results_tree.heading('Rank', text='#')
        self.results_tree.heading('Reference', text='Reference')
        self.results_tree.heading('Sample ID', text='Sample ID')
        self.results_tree.heading('Source', text='Source')
        self.results_tree.heading('Similarity', text='Similarity %')
        self.results_tree.heading('Distance', text='Distance')
        
        self.results_tree.column('Rank', width=40)
        self.results_tree.column('Reference', width=180)
        self.results_tree.column('Sample ID', width=100)
        self.results_tree.column('Source', width=180)
        self.results_tree.column('Similarity', width=100)
        self.results_tree.column('Distance', width=80)
        
        self.results_tree.pack(fill=tk.BOTH, expand=True)
        
        # Bind double-click to show citation
        self.results_tree.bind('<Double-Button-1>', self._show_citation)
        
        # Action buttons
        action_frame = tk.Frame(content)
        action_frame.pack(pady=5)
        
        tk.Button(action_frame, text="📋 Copy Citation",
                 command=self._copy_citation,
                 font=("Arial", 9),
                 width=15).pack(side=tk.LEFT, padx=5)
        
        tk.Button(action_frame, text="📊 View Comparison",
                 command=self._view_comparison,
                 font=("Arial", 9),
                 width=15).pack(side=tk.LEFT, padx=5)
    
    def _find_similar(self):
        """Find similar samples in literature"""
        if not self.app.samples:
            messagebox.showwarning("No Data", "No samples to compare")
            return
        
        selected_idx = self.sample_combo.current()
        if selected_idx < 0:
            messagebox.showwarning("No Selection", "Please select a sample")
            return
        
        # Get selected sample
        sample = self.app.samples[selected_idx]
        
        # Extract elements
        try:
            sample_data = {
                'Zr': float(sample.get('Zr_ppm', 0) or 0),
                'Nb': float(sample.get('Nb_ppm', 0) or 0),
                'Cr': float(sample.get('Cr_ppm', 0) or 0),
                'Ni': float(sample.get('Ni_ppm', 0) or 0)
            }
        except (ValueError, TypeError):
            messagebox.showerror("Invalid Data",
                               "Selected sample has invalid geochemical data")
            return
        
        # Show progress
        if hasattr(self.app, '_show_progress'):
            self.app._show_progress("Comparing with literature...", 20)
        
        # Compare with all reference samples
        comparisons = []
        
        for ref_key, ref_data in self.REFERENCE_DATABASE.items():
            citation = ref_data['citation']
            
            for ref_sample in ref_data['samples']:
                distance = self._calculate_distance(sample_data, ref_sample)
                
                # Convert distance to similarity percentage
                # Lower distance = higher similarity
                similarity = max(0, 100 - (distance / 10))  # Rough conversion
                
                comparisons.append({
                    'reference': ref_key,
                    'citation': citation,
                    'sample_id': ref_sample['id'],
                    'source': ref_sample['source'],
                    'distance': distance,
                    'similarity': similarity
                })
        
        # Sort by distance (closest first)
        comparisons.sort(key=lambda x: x['distance'])
        
        # Store results
        self.comparison_results = comparisons
        
        # Display results
        self._display_results(comparisons[:10])  # Top 10
        
        if hasattr(self.app, '_hide_progress'):
            self.app._hide_progress()
    
    def _calculate_distance(self, sample1, sample2):
        """Calculate Euclidean distance between samples"""
        elements = ['Zr', 'Nb', 'Cr', 'Ni']
        
        if self.method.get() == "weighted":
            # Weight provenance-discriminating elements more
            weights = {'Zr': 1.5, 'Nb': 1.5, 'Cr': 1.2, 'Ni': 1.2}
        else:
            weights = {'Zr': 1.0, 'Nb': 1.0, 'Cr': 1.0, 'Ni': 1.0}
        
        sum_sq = 0
        for elem in elements:
            val1 = sample1.get(elem, 0)
            val2 = sample2.get(elem, 0)
            weight = weights.get(elem, 1.0)
            sum_sq += weight * (val1 - val2) ** 2
        
        return math.sqrt(sum_sq)
    
    def _display_results(self, results):
        """Display comparison results"""
        # Clear tree
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # Add results
        for i, result in enumerate(results, 1):
            # Shorten reference name
            ref_short = result['reference'].replace('_', ' ').title()
            
            self.results_tree.insert('', tk.END, values=(
                i,
                ref_short,
                result['sample_id'],
                result['source'],
                f"{result['similarity']:.1f}%",
                f"{result['distance']:.1f}"
            ))
        
        # Color code by similarity
        for item in self.results_tree.get_children():
            values = self.results_tree.item(item, 'values')
            similarity = float(values[4].replace('%', ''))
            
            if similarity >= 90:
                self.results_tree.item(item, tags=('high',))
            elif similarity >= 75:
                self.results_tree.item(item, tags=('medium',))
            else:
                self.results_tree.item(item, tags=('low',))
        
        self.results_tree.tag_configure('high', foreground='green')
        self.results_tree.tag_configure('medium', foreground='orange')
        self.results_tree.tag_configure('low', foreground='gray')
    
    def _show_citation(self, event):
        """Show full citation for selected item"""
        selection = self.results_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.results_tree.item(item, 'values')
        rank = int(values[0]) - 1
        
        if rank < len(self.comparison_results):
            result = self.comparison_results[rank]
            
            messagebox.showinfo(
                "Full Citation",
                f"{result['citation']}\n\n"
                f"Sample: {result['sample_id']}\n"
                f"Source: {result['source']}\n"
                f"Similarity: {result['similarity']:.1f}%\n\n"
                "Click 'Copy Citation' to copy to clipboard"
            )
    
    def _copy_citation(self):
        """Copy citation to clipboard"""
        selection = self.results_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection",
                                  "Please select a result to copy citation")
            return
        
        item = selection[0]
        values = self.results_tree.item(item, 'values')
        rank = int(values[0]) - 1
        
        if rank < len(self.comparison_results):
            result = self.comparison_results[rank]
            
            citation_text = (
                f"{result['citation']}\n"
                f"Sample {result['sample_id']} ({result['source']})"
            )
            
            self.window.clipboard_clear()
            self.window.clipboard_append(citation_text)
            
            messagebox.showinfo("Copied",
                              "Citation copied to clipboard!")
    
    def _view_comparison(self):
        """View detailed comparison"""
        selection = self.results_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection",
                                  "Please select a result to view details")
            return
        
        messagebox.showinfo("Feature Coming Soon",
                          "Detailed comparison view will show:\n\n"
                          "• Element-by-element comparison\n"
                          "• Radar/spider plot overlay\n"
                          "• Statistical similarity metrics\n\n"
                          "Coming in next version!")
