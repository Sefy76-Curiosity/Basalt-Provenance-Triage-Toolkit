"""
All Schemes Detail Dialog
Shows a table of all scheme results for a single sample.
Includes Previous/Next navigation.
"""

import tkinter as tk
from tkinter import ttk

class AllSchemesDetailDialog:
    def __init__(self, parent, samples, all_results, current_index, scheme_names):
        """
        samples: list of sample dicts
        all_results: list of lists, each inner list is (scheme_name, classification, confidence)
        current_index: index of sample to display
        scheme_names: list of all scheme names for reference
        """
        self.parent = parent
        self.samples = samples
        self.all_results = all_results
        self.current_index = current_index
        self.scheme_names = scheme_names

        self.window = tk.Toplevel(parent)
        self.window.title(f"All Schemes: {self._get_sample_id()}")
        self.window.geometry("750x500")
        self.window.transient(parent)

        main = ttk.Frame(self.window, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        # Header with navigation
        header = ttk.Frame(main)
        header.pack(fill=tk.X, pady=(0, 10))

        self.prev_btn = ttk.Button(header, text="◀ Previous", command=self._prev_sample, width=10)
        self.prev_btn.pack(side=tk.LEFT, padx=2)

        self.sample_label = ttk.Label(header, text=self._get_header_text(),
                                      font=("TkDefaultFont", 12, "bold"))
        self.sample_label.pack(side=tk.LEFT, expand=True, padx=10)

        self.next_btn = ttk.Button(header, text="Next ▶", command=self._next_sample, width=10)
        self.next_btn.pack(side=tk.RIGHT, padx=2)

        ttk.Separator(main, orient='horizontal').pack(fill=tk.X, pady=(0, 10))

        # Results table
        table_frame = ttk.Frame(main)
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("Scheme", "Classification", "Confidence")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)

        self.tree.heading("Scheme", text="Classification Scheme")
        self.tree.heading("Classification", text="Result")
        self.tree.heading("Confidence", text="Confidence")

        self.tree.column("Scheme", width=300, anchor="w", minwidth=250)
        self.tree.column("Classification", width=300, anchor="w", minwidth=250)
        self.tree.column("Confidence", width=100, anchor="center", minwidth=80)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Status bar
        status_frame = ttk.Frame(main)
        status_frame.pack(fill=tk.X, pady=(10, 0))

        self.status_label = ttk.Label(status_frame, text="", font=("TkDefaultFont", 9))
        self.status_label.pack(side=tk.LEFT)

        self._update_nav_buttons()
        self.window.bind("<Left>", lambda e: self._prev_sample())
        self.window.bind("<Right>", lambda e: self._next_sample())
        self.window.bind("<Escape>", lambda e: self.window.destroy())

        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (self.window.winfo_width() // 2)
        y = (self.window.winfo_screenheight() // 2) - (self.window.winfo_height() // 2)
        self.window.geometry(f"+{x}+{y}")

        self._display_current_sample()
        self.window.focus_force()
        self.window.grab_set()

    def _get_sample_id(self):
        return self.samples[self.current_index].get('Sample_ID', f'Sample_{self.current_index}')

    def _get_header_text(self):
        sample_id = self._get_sample_id()
        total = len(self.samples)
        return f"Sample: {sample_id}  ({self.current_index + 1} of {total})"

    def _update_nav_buttons(self):
        self.prev_btn.config(state=tk.NORMAL if self.current_index > 0 else tk.DISABLED)
        self.next_btn.config(state=tk.NORMAL if self.current_index < len(self.samples) - 1 else tk.DISABLED)

    def _display_current_sample(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        results_list = self.all_results[self.current_index]

        if not results_list:
            self.tree.insert("", tk.END, values=("No results available", "", ""))
            self.status_label.config(text="⚠️ No classification results for this sample")
            return

        matched = 0
        total = len(results_list)

        for scheme_name, classification, confidence in results_list:
            if confidence not in (None, 'N/A', ''):
                try:
                    conf_val = float(confidence)
                    if conf_val <= 1.0:
                        conf_str = f"{conf_val:.2f}"
                    else:
                        conf_str = str(int(conf_val))
                except (ValueError, TypeError):
                    conf_str = str(confidence)
            else:
                conf_str = ""

            self.tree.insert("", tk.END, values=(scheme_name, classification, conf_str))

            if classification not in ['UNCLASSIFIED', 'INVALID_SAMPLE', 'SCHEME_NOT_FOUND', '']:
                matched += 1

        self.status_label.config(text=f"✅ {matched} of {total} schemes matched this sample")
        self.sample_label.config(text=self._get_header_text())
        self.window.title(f"All Schemes: {self._get_sample_id()}")

    def _prev_sample(self):
        if self.current_index > 0:
            self.current_index -= 1
            self._update_nav_buttons()
            self._display_current_sample()

    def _next_sample(self):
        if self.current_index < len(self.samples) - 1:
            self.current_index += 1
            self._update_nav_buttons()
            self._display_current_sample()
