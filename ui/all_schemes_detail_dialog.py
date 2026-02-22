"""
All Schemes Detail Dialog
Fully converted to ttkbootstrap with dark theme consistency
Navigation uses ttkbootstrap buttons, treeview is ttkbootstrap-themed
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *


class AllSchemesDetailDialog:
    def __init__(self, parent, samples, all_results, current_index, scheme_names):
        self.parent = parent
        self.samples = samples
        self.all_results = all_results
        self.current_index = current_index
        self.scheme_names = scheme_names

        # Use ttkbootstrap Toplevel
        self.window = ttk.Toplevel(parent)
        self.window.title(f"All Schemes: {self._get_sample_id()}")
        self.window.geometry("780x520")
        self.window.transient(parent)

        # Main container with padding
        main = ttk.Frame(self.window, padding=10)
        main.pack(fill=BOTH, expand=True)

        # ---- Header with navigation ----
        header = ttk.Frame(main)
        header.pack(fill=X, pady=(0, 8))

        # Previous button
        self.prev_btn = ttk.Button(
            header,
            text="◀ Previous",
            command=self._prev_sample,
            bootstyle="secondary",
            width=10
        )
        self.prev_btn.pack(side=LEFT, padx=2)

        # Sample label
        self.sample_label = ttk.Label(
            header,
            text=self._get_header_text(),
            font=("TkDefaultFont", 13, "bold"),
            bootstyle="light"
        )
        self.sample_label.pack(side=LEFT, expand=True, padx=10)

        # Next button
        self.next_btn = ttk.Button(
            header,
            text="Next ▶",
            command=self._next_sample,
            bootstyle="secondary",
            width=10
        )
        self.next_btn.pack(side=RIGHT, padx=2)

        # Separator
        ttk.Separator(main, bootstyle="secondary").pack(fill=X, pady=(0, 8))

        # ---- Results table ----
        table_frame = ttk.Frame(main)
        table_frame.pack(fill=BOTH, expand=True)

        # Treeview with ttkbootstrap styling
        columns = ("Scheme", "Classification", "Confidence")
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=20,
            bootstyle="dark"
        )

        # Configure headings
        self.tree.heading("Scheme", text="Classification Scheme", anchor=W)
        self.tree.heading("Classification", text="Result", anchor=W)
        self.tree.heading("Confidence", text="Confidence", anchor=CENTER)

        # Configure columns
        self.tree.column("Scheme", width=310, anchor=W, minwidth=250)
        self.tree.column("Classification", width=310, anchor=W, minwidth=250)
        self.tree.column("Confidence", width=100, anchor=CENTER, minwidth=80)

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview,
            bootstyle="dark-round"
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Layout
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        # ---- Status bar ----
        status_frame = ttk.Frame(main)
        status_frame.pack(fill=X, pady=(8, 0))

        self.status_label = ttk.Label(
            status_frame,
            text="",
            font=("TkDefaultFont", 10),
            bootstyle="light"
        )
        self.status_label.pack(side=LEFT)

        # ---- Keyboard bindings ----
        self._update_nav_buttons()
        self.window.bind("<Left>", lambda e: self._prev_sample())
        self.window.bind("<Right>", lambda e: self._next_sample())
        self.window.bind("<Escape>", lambda e: self.window.destroy())

        # Initialize display
        self._center_window()
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
        """Enable/disable navigation buttons based on position"""
        if self.current_index > 0:
            self.prev_btn.configure(state=NORMAL)
        else:
            self.prev_btn.configure(state=DISABLED)

        if self.current_index < len(self.samples) - 1:
            self.next_btn.configure(state=NORMAL)
        else:
            self.next_btn.configure(state=DISABLED)

    def _display_current_sample(self):
        """Display results for current sample"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        results_list = self.all_results[self.current_index]

        if not results_list:
            self.tree.insert("", tk.END, values=("No results available", "", ""))
            self.status_label.configure(text="⚠️ No classification results for this sample")
            return

        matched = 0
        total = len(results_list)

        for scheme_name, classification, confidence in results_list:
            # Format confidence
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

            # Insert row
            item_id = self.tree.insert("", tk.END, values=(scheme_name, classification, conf_str))

            # Apply tag for classification if valid
            if classification not in ['UNCLASSIFIED', 'INVALID_SAMPLE', 'SCHEME_NOT_FOUND', '']:
                matched += 1
                # Try to apply color tag if available
                if hasattr(self.parent, 'color_manager'):
                    try:
                        self.tree.item(item_id, tags=(classification,))
                    except:
                        pass

        # Configure colors if color manager exists
        if hasattr(self.parent, 'color_manager'):
            for classification in self.parent.color_manager.get_all_classifications():
                bg = self.parent.color_manager.get_background(classification)
                fg = self.parent.color_manager.get_foreground(classification)
                self.tree.tag_configure(classification, background=bg, foreground=fg)

        # Update status
        self.status_label.configure(
            text=f"✅ {matched} of {total} schemes matched this sample",
            bootstyle="success" if matched > 0 else "secondary"
        )

        # Update header
        self.sample_label.configure(text=self._get_header_text())
        self.window.title(f"All Schemes: {self._get_sample_id()}")

    def _prev_sample(self):
        """Navigate to previous sample"""
        if self.current_index > 0:
            self.current_index -= 1
            self._update_nav_buttons()
            self._display_current_sample()

    def _next_sample(self):
        """Navigate to next sample"""
        if self.current_index < len(self.samples) - 1:
            self.current_index += 1
            self._update_nav_buttons()
            self._display_current_sample()

    def _center_window(self):
        """Center the window on screen"""
        self.window.update_idletasks()
        w = self.window.winfo_width()
        h = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (w // 2)
        y = (self.window.winfo_screenheight() // 2) - (h // 2)
        self.window.geometry(f"+{x}+{y}")
