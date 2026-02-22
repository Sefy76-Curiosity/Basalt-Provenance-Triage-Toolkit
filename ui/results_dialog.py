"""
Results Dialog - Shows detailed classification results
Fully converted to ttkbootstrap with dark theme consistency
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from collections import Counter


class ClassificationResultsDialog:
    def __init__(self, parent, scheme_name, results_data):
        self.window = ttk.Toplevel(parent)
        self.window.title(f"Classification Results: {scheme_name}")
        self.window.geometry("620x440")
        self.window.transient(parent)

        # Main container with padding
        main = ttk.Frame(self.window, padding=12)
        main.pack(fill=BOTH, expand=True)

        total = results_data['total']
        classified = results_data['classified']

        # ---- Summary frame ----
        summary_frame = ttk.LabelFrame(main, text="Summary", padding=8, bootstyle="secondary")
        summary_frame.pack(fill=X, pady=(0, 10))

        # Summary content
        ttk.Label(
            summary_frame,
            text=f"Total samples processed: {total}",
            bootstyle="light"
        ).pack(anchor=W, padx=8, pady=1)

        ttk.Label(
            summary_frame,
            text=f"Successfully classified: {classified}",
            font=("TkDefaultFont", 10, "bold"),
            bootstyle="success"
        ).pack(anchor=W, padx=8, pady=1)

        ttk.Label(
            summary_frame,
            text=f"Unclassified: {total - classified}",
            bootstyle="secondary"
        ).pack(anchor=W, padx=8, pady=(1, 8))

        if classified == 0:
            ttk.Label(
                summary_frame,
                text="⚠️ No samples matched any classification criteria.\n"
                     "Check if required fields are present in your data.",
                bootstyle="danger",
                wraplength=540
            ).pack(pady=(0, 8), padx=8)

        # ---- Breakdown section ----
        if results_data.get('breakdown'):
            breakdown_frame = ttk.LabelFrame(main, text="Classification Breakdown", padding=8, bootstyle="secondary")
            breakdown_frame.pack(fill=BOTH, expand=True, pady=(0, 10))

            # Treeview container
            tree_container = ttk.Frame(breakdown_frame)
            tree_container.pack(fill=BOTH, expand=True)

            # Create treeview with ttkbootstrap styling
            columns = ("Classification", "Count", "Percentage")
            tree = ttk.Treeview(
                tree_container,
                columns=columns,
                show="headings",
                height=8,
                bootstyle="dark"
            )

            # Configure headings
            tree.heading("Classification", text="Classification", anchor=W)
            tree.heading("Count", text="Count", anchor=CENTER)
            tree.heading("Percentage", text="%", anchor=CENTER)

            # Configure columns
            tree.column("Classification", width=320, anchor=W)
            tree.column("Count", width=80, anchor=CENTER)
            tree.column("Percentage", width=80, anchor=CENTER)

            # Scrollbar
            scrollbar = ttk.Scrollbar(
                tree_container,
                orient="vertical",
                command=tree.yview,
                bootstyle="dark-round"
            )
            tree.configure(yscrollcommand=scrollbar.set)

            # Layout
            tree.pack(side=LEFT, fill=BOTH, expand=True)
            scrollbar.pack(side=RIGHT, fill=Y)

            # Insert data
            for class_name, count in sorted(results_data['breakdown'].items(),
                                            key=lambda x: x[1], reverse=True):
                percentage = (count / classified) * 100 if classified > 0 else 0
                tree.insert("", tk.END, values=(class_name, count, f"{percentage:.1f}"))

        # ---- Close button ----
        ttk.Button(
            main,
            text="Close",
            command=self.window.destroy,
            bootstyle="secondary",
            width=15
        ).pack(pady=8)

        # Center the window
        self._center_window()

    def _center_window(self):
        """Center the window on screen"""
        self.window.update_idletasks()
        w = self.window.winfo_width()
        h = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (w // 2)
        y = (self.window.winfo_screenheight() // 2) - (h // 2)
        self.window.geometry(f"+{x}+{y}")
        self.window.grab_set()
