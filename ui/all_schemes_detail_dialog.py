"""
All Schemes Detail Dialog
Fully converted to ttkbootstrap with dark theme consistency
Double-click a scheme to see detailed explanation with Back navigation
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *


class AllSchemesDetailDialog:
    def __init__(self, parent, app, samples, all_results, current_index, scheme_names):
        self.parent = parent
        self.app = app
        self.samples = samples
        self.all_results = all_results
        self.current_index = current_index
        self.scheme_names = scheme_names

        self.detail_mode = False
        self.current_scheme = None
        self.current_classification = None

        self.window = ttk.Toplevel(parent)
        self.window.title(f"All Schemes: {self._get_sample_id()}")
        self.window.geometry("780x520")
        self.window.transient(parent)

        main = ttk.Frame(self.window, padding=10)
        main.pack(fill=BOTH, expand=True)

        # Header with navigation
        header = ttk.Frame(main)
        header.pack(fill=X, pady=(0, 8))

        self.back_btn = ttk.Button(
            header,
            text="◀ Back to Overview",
            command=self._return_to_overview,
            bootstyle="secondary",
            width=15
        )
        # Hidden initially

        self.prev_btn = ttk.Button(
            header,
            text="◀ Previous",
            command=self._prev_sample,
            bootstyle="secondary",
            width=10
        )
        self.prev_btn.pack(side=LEFT, padx=2)

        self.sample_label = ttk.Label(
            header,
            text=self._get_header_text(),
            font=("TkDefaultFont", 13, "bold"),
            bootstyle="light"
        )
        self.sample_label.pack(side=LEFT, expand=True, padx=10)

        self.next_btn = ttk.Button(
            header,
            text="Next ▶",
            command=self._next_sample,
            bootstyle="secondary",
            width=10
        )
        self.next_btn.pack(side=RIGHT, padx=2)

        ttk.Separator(main, bootstyle="secondary").pack(fill=X, pady=(0, 8))

        # Content area
        self.content_frame = ttk.Frame(main)
        self.content_frame.pack(fill=BOTH, expand=True)

        # Status bar
        status_frame = ttk.Frame(main)
        status_frame.pack(fill=X, pady=(8, 0))

        self.status_label = ttk.Label(
            status_frame,
            text="",
            font=("TkDefaultFont", 10),
            bootstyle="light"
        )
        self.status_label.pack(side=LEFT)

        # Bindings
        self.window.bind("<Left>", lambda e: self._prev_sample())
        self.window.bind("<Right>", lambda e: self._next_sample())
        self.window.bind("<Escape>", lambda e: self._handle_escape())

        self._center_window()
        self._show_overview()
        self.window.focus_force()
        self.window.grab_set()

    def _get_sample_id(self):
        return self.samples[self.current_index].get('Sample_ID', f'Sample_{self.current_index}')

    def _get_header_text(self):
        sample_id = self._get_sample_id()
        total = len(self.samples)
        return f"Sample: {sample_id}  ({self.current_index + 1} of {total})"

    def _update_nav_buttons(self):
        if self.detail_mode:
            self.prev_btn.pack_forget()
            self.next_btn.pack_forget()
            self.back_btn.pack(side=LEFT, padx=2)
        else:
            self.back_btn.pack_forget()
            self.prev_btn.pack(side=LEFT, padx=2)
            self.next_btn.pack(side=RIGHT, padx=2)

            if self.current_index > 0:
                self.prev_btn.configure(state=NORMAL)
            else:
                self.prev_btn.configure(state=DISABLED)

            if self.current_index < len(self.samples) - 1:
                self.next_btn.configure(state=NORMAL)
            else:
                self.next_btn.configure(state=DISABLED)

    def _handle_escape(self):
        if self.detail_mode:
            self._return_to_overview()
        else:
            self.window.destroy()

    def _show_overview(self):
        """Show overview table of all schemes"""
        self.detail_mode = False
        self._update_nav_buttons()

        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Create table
        columns = ("Scheme", "Classification", "Confidence")
        self.tree = ttk.Treeview(
            self.content_frame,
            columns=columns,
            show="headings",
            height=20,
            bootstyle="dark"
        )

        self.tree.heading("Scheme", text="Classification Scheme", anchor=W)
        self.tree.heading("Classification", text="Result", anchor=W)
        self.tree.heading("Confidence", text="Confidence", anchor=CENTER)

        self.tree.column("Scheme", width=310, anchor=W)
        self.tree.column("Classification", width=310, anchor=W)
        self.tree.column("Confidence", width=100, anchor=CENTER)

        scrollbar = ttk.Scrollbar(
            self.content_frame,
            orient="vertical",
            command=self.tree.yview,
            bootstyle="dark-round"
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        self.tree.bind("<Double-1>", self._on_scheme_double_click)

        # Populate data
        results_list = self.all_results[self.current_index]
        matched = 0

        for scheme_name, classification, confidence in results_list:
            # Format confidence
            conf_str = ""
            if confidence not in (None, 'N/A', ''):
                try:
                    conf_val = float(confidence)
                    conf_str = f"{conf_val:.2f}" if conf_val <= 1.0 else str(int(conf_val))
                except (ValueError, TypeError):
                    conf_str = str(confidence)

            item_id = self.tree.insert("", tk.END, values=(scheme_name, classification, conf_str))

            if classification not in ['UNCLASSIFIED', 'INVALID_SAMPLE', 'SCHEME_NOT_FOUND', '']:
                matched += 1
                if hasattr(self.app, 'color_manager'):
                    try:
                        self.tree.item(item_id, tags=(classification,))
                    except:
                        pass

        # Configure colors
        if hasattr(self.app, 'color_manager'):
            for classification in self.app.color_manager.get_all_classifications():
                bg = self.app.color_manager.get_background(classification)
                fg = self.app.color_manager.get_foreground(classification)
                self.tree.tag_configure(classification, background=bg, foreground=fg)

        self.status_label.configure(
            text=f"✅ {matched} of {len(results_list)} schemes matched this sample"
        )
        self.window.title(f"All Schemes: {self._get_sample_id()}")

    def _on_scheme_double_click(self, event):
        """Double-click to show scheme details"""
        selection = self.tree.selection()
        if not selection:
            return

        item = selection[0]
        values = self.tree.item(item, 'values')
        if not values or len(values) < 2:
            return

        scheme_name, classification = values[0], values[1]

        if classification in ['UNCLASSIFIED', 'INVALID_SAMPLE', 'SCHEME_NOT_FOUND', '']:
            return

        self.current_scheme = scheme_name
        self.current_classification = classification
        self._show_detail()

    def _show_detail(self):
        """Show detailed explanation for selected scheme"""
        self.detail_mode = True
        self._update_nav_buttons()

        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Get sample data
        sample = self.samples[self.current_index]

        # Create detail view
        text_frame = ttk.Frame(self.content_frame)
        text_frame.pack(fill=BOTH, expand=True, pady=5)

        style = ttk.Style.get_instance()
        bg = style.colors.get('dark') if hasattr(style, 'colors') else "#2b2b2b"
        fg = style.colors.get('light') if hasattr(style, 'colors') else "#dddddd"

        text_widget = tk.Text(
            text_frame,
            wrap=tk.WORD,
            font=("TkDefaultFont", 11),
            height=20,
            bg=bg,
            fg=fg,
            relief=tk.FLAT,
            bd=0
        )
        scrollbar = ttk.Scrollbar(
            text_frame,
            command=text_widget.yview,
            bootstyle="dark-round"
        )
        text_widget.configure(yscrollcommand=scrollbar.set)

        text_widget.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        # Generate explanation
        explanation = self._generate_explanation(sample)
        text_widget.insert(tk.END, explanation)
        text_widget.config(state=tk.DISABLED)

        self.window.title(f"Detail: {self.current_scheme} - {self._get_sample_id()}")

    def _generate_explanation(self, sample):
        """Generate simple explanation text"""
        lines = []
        lines.append(f"Scheme: {self.current_scheme}")
        lines.append(f"Classification: {self.current_classification}")
        lines.append("")
        lines.append("=" * 50)
        lines.append("")

        # Show relevant geochemical data
        lines.append("📊 Geochemical Values:")
        relevant = ['Zr_ppm', 'Nb_ppm', 'Ba_ppm', 'Rb_ppm', 'Cr_ppm', 'Ni_ppm',
                   'SiO2_wt', 'TiO2_wt', 'Al2O3_wt', 'Fe2O3_T_wt']

        for key in relevant:
            if key in sample and sample[key]:
                lines.append(f"  {key}: {sample[key]}")

        lines.append("")
        lines.append("=" * 50)
        lines.append("")
        lines.append("ℹ️ This classification is based on the scheme's rules.")
        lines.append("Double-click another scheme in the overview to see its details.")

        return "\n".join(lines)

    def _return_to_overview(self):
        """Return to overview from detail view"""
        self._show_overview()

    def _prev_sample(self):
        if self.current_index > 0 and not self.detail_mode:
            self.current_index -= 1
            self._show_overview()

    def _next_sample(self):
        if self.current_index < len(self.samples) - 1 and not self.detail_mode:
            self.current_index += 1
            self._show_overview()

    def _center_window(self):
        self.window.update_idletasks()
        w = self.window.winfo_width()
        h = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (w // 2)
        y = (self.window.winfo_screenheight() // 2) - (h // 2)
        self.window.geometry(f"+{x}+{y}")
