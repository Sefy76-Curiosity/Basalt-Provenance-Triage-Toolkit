"""
Results Dialog - Shows detailed classification results
"""

import tkinter as tk
from tkinter import ttk
from collections import Counter

class ClassificationResultsDialog:
    def __init__(self, parent, scheme_name, results_data):
        self.window = tk.Toplevel(parent)
        self.window.title(f"Classification Results: {scheme_name}")
        self.window.geometry("600x400")
        self.window.transient(parent)

        main = ttk.Frame(self.window, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        # Summary
        total = results_data['total']
        classified = results_data['classified']

        summary_frame = ttk.LabelFrame(main, text="Summary", padding=10)
        summary_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(summary_frame, text=f"Total samples processed: {total}",
                 font=("TkDefaultFont", 10)).pack(anchor=tk.W)
        ttk.Label(summary_frame, text=f"Successfully classified: {classified}",
                 font=("TkDefaultFont", 10, "bold")).pack(anchor=tk.W)
        ttk.Label(summary_frame, text=f"Unclassified: {total - classified}",
                 font=("TkDefaultFont", 10)).pack(anchor=tk.W)

        if classified == 0:
            ttk.Label(summary_frame,
                     text="⚠️ No samples matched any classification criteria.\nCheck if required fields are present in your data.",
                     foreground="red", wraplength=500).pack(pady=(10, 0))

        # Detailed breakdown
        if results_data['breakdown']:
            breakdown_frame = ttk.LabelFrame(main, text="Classification Breakdown", padding=10)
            breakdown_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

            # Create treeview for breakdown
            columns = ("Classification", "Count", "Percentage")
            tree = ttk.Treeview(breakdown_frame, columns=columns, show="headings", height=8)

            tree.heading("Classification", text="Classification")
            tree.heading("Count", text="Count")
            tree.heading("Percentage", text="%")

            tree.column("Classification", width=300)
            tree.column("Count", width=80, anchor="center")
            tree.column("Percentage", width=80, anchor="center")

            # Add scrollbar
            scrollbar = ttk.Scrollbar(breakdown_frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)

            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            # Populate data
            for class_name, count in sorted(results_data['breakdown'].items(),
                                           key=lambda x: x[1], reverse=True):
                percentage = (count / classified) * 100 if classified > 0 else 0
                tree.insert("", tk.END, values=(class_name, count, f"{percentage:.1f}"))

        # Close button
        ttk.Button(main, text="Close", command=self.window.destroy).pack(pady=10)

        # Center window
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"+{x}+{y}")
        self.window.grab_set()
