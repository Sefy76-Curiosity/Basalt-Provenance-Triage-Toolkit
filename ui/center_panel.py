"""
Center Panel - 80% width, Dynamic Table with Tabs
Includes status bar between navigation and selection controls
"""

import tkinter as tk
from tkinter import ttk, messagebox
from collections import Counter

class CenterPanel:
    def __init__(self, parent, app):
        self.app = app
        self.frame = ttk.Frame(parent, relief=tk.RAISED, borderwidth=1)

        # State
        self.current_page = 0
        self.page_size = 50
        self.selected_rows = set()
        self.filtered_indices = None

        # Track if this is the first refresh (for auto-sizing columns)
        self._first_refresh = True

        # UI elements
        self.notebook = None
        self.tree = None
        self.search_var = tk.StringVar()
        self.filter_var = tk.StringVar(value="All")

        # Plot types
        self.plot_types = []
        self.ai_plugins = []
        self.current_ai_plugin = None
        self.ai_tab_created = False
        self._is_syncing_scroll = False

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        self.last_classification_summary = ""

        self._build_ui()

    def _build_ui(self):
        """Build center panel with tabs"""
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Tab 1: Data Table
        self.table_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.table_tab, text="📊 Data Table")
        self._build_table_tab()

        # Tab 2: Plots
        self.plots_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.plots_tab, text="📈 Plots")
        self._build_plots_tab()

    def _build_table_tab(self):
        """Build the data table tab"""
        # ============ FILTER BAR ============
        filter_frame = ttk.Frame(self.table_tab)
        filter_frame.pack(fill=tk.X, padx=2, pady=2)

        ttk.Label(filter_frame, text="🔍 Search:").pack(side=tk.LEFT)
        self.search_var.trace("w", lambda *a: self._apply_filter())
        ttk.Entry(filter_frame, textvariable=self.search_var, width=30).pack(side=tk.LEFT, padx=5)

        ttk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT, padx=5)
        self.filter_combo = ttk.Combobox(filter_frame, textvariable=self.filter_var,
                                        values=["All"], state="readonly", width=15)
        self.filter_combo.pack(side=tk.LEFT, padx=5)
        self.filter_combo.bind('<<ComboboxSelected>>', lambda e: self._apply_filter())

        ttk.Button(filter_frame, text="Clear", command=self._clear_filter).pack(side=tk.LEFT, padx=5)
        ttk.Button(filter_frame, text="↔ Reset Columns", command=self._reset_column_widths).pack(side=tk.LEFT, padx=5)
        self.sel_label = tk.Label(filter_frame, text="Selected: 0")
        self.sel_label.pack(side=tk.RIGHT, padx=10)

        # ============ TABLE with HORIZONTAL SCROLLBAR ============
        table_container = ttk.Frame(self.table_tab)
        table_container.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Create treeview
        self.tree = ttk.Treeview(table_container, show="headings", height=20)

        # Scrollbars - BOTH horizontal and vertical
        vsb = ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Grid layout
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)

        # Bindings
        self.tree.bind("<Button-1>", self._on_click)
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Button-3>", self._show_context_menu)

        # Track when user manually resizes columns
        self.tree.bind("<ButtonRelease-1>", self._on_column_resize)

        # Mouse wheel for scroll sync
        self.tree.bind("<MouseWheel>", self._on_tree_mousewheel)
        self.tree.bind("<Button-4>", self._on_tree_mousewheel)
        self.tree.bind("<Button-5>", self._on_tree_mousewheel)

        self._configure_row_colors()

    def _configure_row_colors(self):
        """Configure row colors from color manager"""
        configured_tags = set()
        for classification in self.app.color_manager.get_all_classifications():
            bg_color = self.app.color_manager.get_background(classification)
            if classification not in configured_tags:
                self.tree.tag_configure(classification, background=bg_color)
                configured_tags.add(classification)
            upper = classification.upper()
            if upper not in configured_tags:
                self.tree.tag_configure(upper, background=bg_color)
                configured_tags.add(upper)

    def _build_plots_tab(self):
        """Build the plots tab"""
        ctrl_frame = ttk.Frame(self.plots_tab)
        ctrl_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(ctrl_frame, text="Plot type:").pack(side=tk.LEFT, padx=5)

        self.plot_type_var = tk.StringVar()
        self.plot_type_combo = ttk.Combobox(ctrl_frame, textvariable=self.plot_type_var,
                                           state="readonly", width=30)
        self.plot_type_combo.pack(side=tk.LEFT, padx=5)

        self.plot_btn = ttk.Button(ctrl_frame, text="Generate Plot",
                                   command=self._generate_plot, state="disabled")
        self.plot_btn.pack(side=tk.LEFT, padx=5)

        self.plot_area = tk.Frame(self.plots_tab, bg="white", relief=tk.SUNKEN, borderwidth=1)
        self.plot_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        placeholder = tk.Label(self.plot_area, text="Select a plot type and click Generate",
                               font=("Arial", 12), fg="gray")
        placeholder.pack(expand=True)
        self.plot_placeholder = placeholder

    def update_plot_types(self, plot_types):
        """Update available plot types from plugins"""
        self.plot_types = plot_types
        if plot_types:
            values = [name for name, func in plot_types]
            self.plot_type_combo['values'] = values
            if values:
                self.plot_type_combo.current(0)
                self.plot_btn.config(state="normal")

    def _generate_plot(self):
        """Generate the selected plot"""
        if not self.plot_types or not self.plot_type_var.get():
            return
        selected = self.plot_type_var.get()
        plot_func = None
        for name, func in self.plot_types:
            if name == selected:
                plot_func = func
                break
        if plot_func:
            samples = self.app.data_hub.get_page(self.current_page, self.page_size)
            for widget in self.plot_area.winfo_children():
                widget.destroy()
            try:
                plot_func(self.plot_area, samples)
            except Exception as e:
                error_label = tk.Label(self.plot_area, text=f"Plot error: {e}",
                                      fg="red", font=("Arial", 10))
                error_label.pack(expand=True)

    # ============ SCROLL SYNC ============
    def _on_tree_scroll(self, *args):
        if self._is_syncing_scroll:
            return
        self.tree.yview(*args)
        first, last = self.tree.yview()
        if hasattr(self.app, 'right') and hasattr(self.app.right, 'hud_tree'):
            self._is_syncing_scroll = True
            self.app.right.hud_tree.yview_moveto(first)
            self._is_syncing_scroll = False

    def _on_tree_mousewheel(self, event):
        if self._is_syncing_scroll:
            return
        if event.delta:
            self.tree.yview_scroll(int(-1 * (event.delta / 120)), "units")
        else:
            if event.num == 4:
                self.tree.yview_scroll(-1, "units")
            elif event.num == 5:
                self.tree.yview_scroll(1, "units")
        first, last = self.tree.yview()
        if hasattr(self.app, 'right') and hasattr(self.app.right, 'hud_tree'):
            self._is_syncing_scroll = True
            self.app.right.hud_tree.yview_moveto(first)
            self._is_syncing_scroll = False
        return "break"

    # ============ DATA OBSERVER ============
    def on_data_changed(self, event, *args):
        self._refresh()

    # ============ REFRESH - SIMPLIFIED ============
    def _refresh(self):
        """Refresh table - fixed columns first, then chemical data"""
        if not self.tree:
            return

        samples = self.app.data_hub.get_page(self.current_page, self.page_size)
        total = self.app.data_hub.row_count()

        # Get ALL columns from DataHub (already normalized)
        all_columns = self.app.data_hub.get_column_names()

        # ============ FIXED COLUMNS (ALWAYS FIRST IN THIS ORDER) ============
        fixed_columns = ["Sample_ID", "Notes", "Museum_Code", "Date", "Latitude", "Longitude"]

        # Also include any other "wordy" metadata columns that should appear early
        metadata_keywords = ["Context", "Location", "Site", "Area", "Square", "Locus",
                            "Basket", "Bag", "Field", "Description", "Comment"]

        # Separate fixed columns from chemical data
        priority = []
        chemical = []

        for col in all_columns:
            if col in fixed_columns:
                priority.append(col)
            elif any(keyword.lower() in col.lower() for keyword in metadata_keywords):
                priority.append(col)
            elif col not in ["☐", "Display_Color", "Auto_Classification_Color"]:
                chemical.append(col)

        # Remove duplicates while preserving order
        seen = set()
        priority_deduped = []
        for col in priority:
            if col not in seen:
                seen.add(col)
                priority_deduped.append(col)

        chemical_deduped = []
        for col in chemical:
            if col not in seen:
                seen.add(col)
                chemical_deduped.append(col)

        # Final column order: Checkbox + priority + chemical
        final_cols = ["☐"] + priority_deduped + chemical_deduped

        # Update column configuration if changed
        if list(self.tree["columns"]) != final_cols:
            self.tree["columns"] = final_cols
            for col in final_cols:
                if col == "☐":
                    self.tree.heading(col, text="")
                    self.tree.column(col, width=30, anchor=tk.CENTER, stretch=False)
                else:
                    # Create display name
                    display_name = col.replace("_", " ")
                    if col == "Sample_ID":
                        display_name = "ID"
                    elif col == "Museum_Code":
                        display_name = "Museum"
                    elif col.endswith("_ppm"):
                        display_name = col.replace("_ppm", " (ppm)")
                    elif col.endswith("_pct") or col.endswith("_wt"):
                        display_name = col.replace("_pct", "%").replace("_wt", "%")

                    self.tree.heading(col, text=display_name, anchor=tk.CENTER)
                    # Set reasonable default width
                    if col in priority_deduped:
                        self.tree.column(col, width=120, anchor=tk.W, minwidth=80)
                    else:
                        self.tree.column(col, width=100, anchor=tk.CENTER, minwidth=60)

        # Clear and repopulate
        self.tree.delete(*self.tree.get_children())

        for i, sample in enumerate(samples):
            actual_idx = self.current_page * self.page_size + i
            checkbox = "☑" if actual_idx in self.selected_rows else "☐"

            values = [checkbox]

            # Add priority columns
            for col in priority_deduped:
                val = sample.get(col, "")
                if val is None:
                    val = ""
                values.append(str(val))

            # Add chemical columns
            for col in chemical_deduped:
                val = sample.get(col, "")
                if val is None:
                    val = ""
                # Format numbers nicely
                if isinstance(val, (int, float)):
                    if abs(val) < 0.01 or abs(val) > 1000:
                        values.append(f"{val:.2e}")
                    elif val == int(val):
                        values.append(str(int(val)))
                    else:
                        values.append(f"{val:.2f}")
                else:
                    values.append(str(val))

            item_id = self.tree.insert("", tk.END, values=tuple(values))

            # Apply color tag if classification exists
            if 'Auto_Classification' in sample:
                tag = sample['Auto_Classification']
                self.tree.item(item_id, tags=(tag,))
            else:
                self.tree.item(item_id, tags=("UNCLASSIFIED",))

        # Auto-size columns (only on first refresh, unless forced)
        if self._first_refresh:
            self.app.auto_size_columns(self.tree, samples, force=False)
            self._first_refresh = False
        # After first refresh, columns retain their size (user can manually adjust)

        # Update pagination
        pages = (total + self.page_size - 1) // self.page_size if total > 0 else 1
        self.app.update_pagination(self.current_page, pages, total)
        self.sel_label.config(text=f"Selected: {len(self.selected_rows)}")

    # ============ SELECTION ============
    def _on_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            item = self.tree.identify_row(event.y)
            if column == "#1" and item:
                self._toggle_row(item)

    def _on_column_resize(self, event):
        """
        Detect when user manually resizes a column.
        Mark the tree so auto-sizing doesn't override their changes.
        """
        region = self.tree.identify("region", event.x, event.y)
        if region == "separator":
            # User just finished resizing a column
            self.tree._columns_manually_sized = True

    def _toggle_row(self, item_id):
        item_idx = self.tree.index(item_id)
        actual_idx = self.current_page * self.page_size + item_idx

        if actual_idx in self.selected_rows:
            self.selected_rows.remove(actual_idx)
            checkbox = "☐"
        else:
            self.selected_rows.add(actual_idx)
            checkbox = "☑"

        values = list(self.tree.item(item_id, "values"))
        if values:
            values[0] = checkbox
            self.tree.item(item_id, values=tuple(values))

        self.sel_label.config(text=f"Selected: {len(self.selected_rows)}")
        self.app.update_selection(len(self.selected_rows))

    def select_all(self):
        total = self.app.data_hub.row_count()
        start = self.current_page * self.page_size
        end = min(start + self.page_size, total)
        for i in range(start, end):
            self.selected_rows.add(i)
        self._refresh()

    def deselect_all(self):
        self.selected_rows.clear()
        self._refresh()

    def get_selected_indices(self):
        return list(self.selected_rows)

    # ============ PAGINATION ============
    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self._refresh()

    def next_page(self):
        total = self.app.data_hub.row_count()
        pages = (total + self.page_size - 1) // self.page_size
        if self.current_page < pages - 1:
            self.current_page += 1
            self._refresh()

    # ============ FILTER ============
    def _apply_filter(self):
        self._refresh()

    def _clear_filter(self):
        self.search_var.set("")
        self.filter_var.set("All")
        self._refresh()

    def _reset_column_widths(self):
        """Reset column widths to auto-calculated sizes"""
        # Clear the manual sizing flag
        if hasattr(self.tree, '_columns_manually_sized'):
            self.tree._columns_manually_sized = False

        # Force re-auto-sizing
        samples = self.app.data_hub.get_page(self.current_page, self.page_size)
        if samples:
            self.app.auto_size_columns(self.tree, samples, force=True)

    # ============ EDITING ============
    def _on_double_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        item = self.tree.identify_row(event.y)
        if not item:
            return
        item_idx = self.tree.index(item)
        sample_idx = self.current_page * self.page_size + item_idx
        samples = self.app.data_hub.get_all()
        if sample_idx < len(samples):
            sample = samples[sample_idx]
            self._show_classification_explanation(sample)

    def _show_classification_explanation(self, sample):
        """Show classification explanation popup"""
        win = tk.Toplevel(self.app.root)
        win.title(f"Classification: {sample.get('Sample_ID', 'Unknown')}")
        win.geometry("600x500")
        win.transient(self.app.root)

        def set_grab():
            win.grab_set()
            win.focus_force()
        win.after(100, set_grab)

        main = ttk.Frame(win, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text=f"Sample: {sample.get('Sample_ID', 'Unknown')}",
                 font=("Arial", 14, "bold")).pack(pady=5)

        classification = self.app.right._get_classification(sample)
        confidence = sample.get('Auto_Confidence', 'N/A')

        class_frame = ttk.Frame(main)
        class_frame.pack(fill=tk.X, pady=10)
        ttk.Label(class_frame, text="Classification:", font=("Arial", 11, "bold")).pack(side=tk.LEFT)
        fg_color = self.app.color_manager.get_foreground(classification)
        ttk.Label(class_frame, text=classification, font=("Arial", 11),
                 foreground=fg_color).pack(side=tk.LEFT, padx=10)
        ttk.Label(class_frame, text=f"Confidence: {confidence}",
                 font=("Arial", 10)).pack(side=tk.RIGHT)

        ttk.Separator(main, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        ttk.Label(main, text="Geochemical Data:", font=("Arial", 11, "bold")).pack(anchor=tk.W)

        data_frame = ttk.Frame(main)
        data_frame.pack(fill=tk.X, pady=5)

        elements = ['Zr_ppm', 'Nb_ppm', 'Ba_ppm', 'Rb_ppm', 'Cr_ppm', 'Ni_ppm']
        ratios = ['Zr_Nb_Ratio', 'Cr_Ni_Ratio', 'Ba_Rb_Ratio']

        row = 0
        for elem in elements:
            if elem in sample and sample[elem]:
                val = sample[elem]
                if val:
                    ttk.Label(data_frame, text=f"{elem}:", font=("Arial", 9)).grid(
                        row=row, column=0, sticky=tk.W, padx=5, pady=2)
                    ttk.Label(data_frame, text=str(val), font=("Arial", 9)).grid(
                        row=row, column=1, sticky=tk.W, padx=5, pady=2)
                    row += 1

        for ratio in ratios:
            if ratio in sample and sample[ratio]:
                val = sample[ratio]
                if val:
                    ttk.Label(data_frame, text=f"{ratio}:", font=("Arial", 9)).grid(
                        row=row, column=0, sticky=tk.W, padx=5, pady=2)
                    ttk.Label(data_frame, text=f"{float(val):.2f}", font=("Arial", 9)).grid(
                        row=row, column=1, sticky=tk.W, padx=5, pady=2)
                    row += 1

        ttk.Separator(main, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        ttk.Label(main, text="Classification Logic:", font=("Arial", 11, "bold")).pack(anchor=tk.W, pady=5)

        text_frame = ttk.Frame(main)
        text_frame.pack(fill=tk.BOTH, expand=True)

        text_widget = tk.Text(text_frame, wrap=tk.WORD, font=("Arial", 10), height=10)
        scrollbar = ttk.Scrollbar(text_frame, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)

        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        explanation = self._generate_classification_explanation(sample, classification)
        text_widget.insert(tk.END, explanation)
        text_widget.config(state=tk.DISABLED)

        ttk.Button(main, text="Close", command=win.destroy).pack(pady=10)

    def _generate_classification_explanation(self, sample, classification):
        """Generate explanation text with safe float handling"""
        lines = []
        lines.append(f"This sample was classified as: {classification}\n")
        lines.append("\n📊 Data values:")

        # Helper function for safe float formatting
        def safe_float_display(value, format_str="{:.2f}"):
            if value is None or value == '':
                return "N/A"
            try:
                return format_str.format(float(value))
            except (ValueError, TypeError):
                return f"{value} (invalid)"

        if 'Zr_ppm' in sample:
            lines.append(f"  • Zr: {sample['Zr_ppm']} ppm")
        if 'Nb_ppm' in sample:
            lines.append(f"  • Nb: {sample['Nb_ppm']} ppm")
        if 'Zr_Nb_Ratio' in sample:
            lines.append(f"  • Zr/Nb: {safe_float_display(sample['Zr_Nb_Ratio'])}")

        if 'Cr_ppm' in sample:
            lines.append(f"  • Cr: {sample['Cr_ppm']} ppm")
        if 'Ni_ppm' in sample:
            lines.append(f"  • Ni: {sample['Ni_ppm']} ppm")
        if 'Cr_Ni_Ratio' in sample:
            lines.append(f"  • Cr/Ni: {safe_float_display(sample['Cr_Ni_Ratio'])}")

        if 'Ba_ppm' in sample:
            lines.append(f"  • Ba: {sample['Ba_ppm']} ppm")
        if 'Rb_ppm' in sample:
            lines.append(f"  • Rb: {sample['Rb_ppm']} ppm")
        if 'Ba_Rb_Ratio' in sample:
            lines.append(f"  • Ba/Rb: {safe_float_display(sample['Ba_Rb_Ratio'])}")

        lines.append("\n🎯 Classification criteria:")
        if "EGYPTIAN" in classification:
            if "HADDADIN" in classification:
                lines.append("  • Matches Egyptian Haddadin Flow basalt")
                lines.append("  • Zr/Nb ratio in range 7.0-12.0")
                lines.append("  • Ba between 240-300 ppm")
                lines.append("  • Cr/Ni between 1.1-1.6")
                lines.append("\n📚 Reference: Hartung 2017")
            elif "ALKALINE" in classification:
                lines.append("  • Egyptian alkaline/exotic basalt")
                lines.append("  • Zr/Nb > 22.0 (highly fractionated)")
                lines.append("  • Ba > 350 ppm (enriched)")
                lines.append("\n📚 Reference: Philip & Williams-Thorpe 2001")
        elif "SINAI" in classification:
            if "OPHIOLITIC" in classification:
                lines.append("  • Sinai ophiolitic basalt")
                lines.append("  • Zr/Nb ≥ 20.0 (depleted mantle)")
                lines.append("  • Cr/Ni 1.8-2.3 (mantle-derived)")
                lines.append("  • Ba ≤ 150 ppm (low)")
                lines.append("  • Rb ≤ 30 ppm (very low)")
                lines.append("\n📚 Reference: Williams-Thorpe & Thorpe 1993")
            elif "TRANSITIONAL" in classification:
                lines.append("  • Sinai transitional basalt")
                lines.append("  • Zr/Nb 15.0-22.0 (intermediate)")
                lines.append("\n📚 Reference: Williams-Thorpe & Thorpe 1993")
        elif "LOCAL LEVANTINE" in classification:
            lines.append("  • Local Levantine source (Golan/Galilee/Hula)")
            lines.append("  • Zr/Nb < 15.0")
            lines.append("  • Cr/Ni > 2.5 (distinctive high Cr/Ni)")
            lines.append("  • Ba < 200 ppm")
            lines.append("\n📚 Reference: Rosenberg et al. 2016")
        elif "REVIEW REQUIRED" in classification:
            lines.append("  • Sample does not match any known classification")
            lines.append("  • May have missing data or unusual chemistry")
            lines.append("  • Manual review recommended")
        elif "UNCLASSIFIED" in classification:
            lines.append("  • Sample has not been classified")
            lines.append("  • Run classification from the right panel")

        return "\n".join(lines)

    def _show_context_menu(self, event):
        """Right-click context menu"""
        item = self.tree.identify_row(event.y)
        if not item:
            return
        self.tree.selection_set(item)

        item_idx = self.tree.index(item)
        sample_idx = self.current_page * self.page_size + item_idx
        sample = self.app.data_hub.get_all()[sample_idx]

        menu = tk.Menu(self.tree, tearoff=0)
        menu.add_command(label="Edit Cell",
                        command=lambda: self._edit_selected_cell(event, item, sample_idx))
        menu.add_separator()
        menu.add_command(label="Copy Value", command=lambda: self._copy_cell_value(item))
        menu.add_command(label="Copy Row", command=lambda: self._copy_row(sample))
        menu.add_separator()
        menu.add_command(label="Delete Row", command=lambda: self._delete_row(sample_idx))

        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _edit_selected_cell(self, event, item, sample_idx):
        column = self.tree.identify_column(event.x)
        if column == "#1":
            return
        col_idx = int(column[1:]) - 1
        columns = self.tree["columns"]
        if col_idx >= len(columns):
            return
        col_name = columns[col_idx]
        values = self.tree.item(item, "values")
        if col_idx < len(values):
            current = values[col_idx]
            self._create_edit_popup(event, item, col_name, current, sample_idx)

    def _create_edit_popup(self, event, item, col_name, current_value, sample_idx):
        x, y, width, height = self.tree.bbox(item, column=col_name)
        entry = ttk.Entry(self.tree)
        entry.place(x=x, y=y, width=width, height=height)
        entry.insert(0, current_value)
        entry.select_range(0, tk.END)
        entry.focus()

        def save_edit(event=None):
            new_value = entry.get().strip()
            entry.destroy()
            if new_value != current_value:
                self.app.data_hub.update_row(sample_idx, {col_name: new_value})

        def cancel_edit(event=None):
            entry.destroy()

        entry.bind("<Return>", save_edit)
        entry.bind("<Escape>", cancel_edit)
        entry.bind("<FocusOut>", save_edit)

    def _copy_cell_value(self, item):
        selection = self.tree.selection()
        if not selection:
            return
        values = self.tree.item(selection[0], "values")
        if values and len(values) > 1:
            self.tree.clipboard_clear()
            self.tree.clipboard_append(str(values[1]))

    def _copy_row(self, sample):
        import json
        text = json.dumps(sample, indent=2)
        self.tree.clipboard_clear()
        self.tree.clipboard_append(text)

    def _delete_row(self, sample_idx):
        if messagebox.askyesno("Confirm Delete", "Delete this row?"):
            self.app.data_hub.delete_rows([sample_idx])

    # ============ STATUS BAR METHODS ============

    def show_classification_status(self, scheme_name, total_samples, classified_count, classification_counts):
        """
        Update status bar with classification results
        Called from right_panel after classification
        """
        # Store details for popup
        self.last_classification_details = {
            'scheme': scheme_name,
            'total': total_samples,
            'classified': classified_count,
            'breakdown': classification_counts
        }

        # Also store console-like output
        console_lines = []
        console_lines.append(f"📊 Classification Results for '{scheme_name}':")
        console_lines.append(f"   Total samples: {total_samples}")
        console_lines.append(f"   New classifications: {classified_count}")
        console_lines.append(f"   Unclassified: {total_samples - classified_count}")
        if classification_counts:
            console_lines.append("   Breakdown:")
            for class_name, count in sorted(classification_counts.items(), key=lambda x: x[1], reverse=True):
                console_lines.append(f"     • {class_name}: {count}")
        self.last_console_output = "\n".join(console_lines)

        if classified_count == 0:
            self.status_var.set(f"⚠️ No matches found for {scheme_name} (click for details)")
        else:
            # Create a concise summary of top classifications
            counter = Counter(classification_counts)
            top_classes = counter.most_common(3)
            summary_parts = []
            for class_name, count in top_classes:
                # Shorten class names if needed
                short_name = class_name[:20] + "..." if len(class_name) > 20 else class_name
                summary_parts.append(f"{short_name}: {count}")

            if len(counter) > 3:
                summary_parts.append(f"+{len(counter)-3} more")

            summary = " | ".join(summary_parts)
            self.status_var.set(f"✅ {classified_count}/{total_samples} classified: {summary} (click for details)")

        # Force update
        self.app.root.update_idletasks()

    def set_status(self, message, message_type="info"):
        """
        Set status bar message with optional icon
        message_type: "info", "success", "warning", "error", "processing"
        """
        icons = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
            "processing": "🔄"
        }
        icon = icons.get(message_type, "ℹ️")

        # Clear previous details when setting a new status that's not classification-related
        if message_type not in ["success"] or "classified" not in message.lower():
            self.last_classification_details = None
            self.last_console_output = None

        self.status_var.set(f"{icon} {message}")
        self.app.root.update_idletasks()

    def clear_status(self):
        """Reset status bar to default"""
        self.status_var.set("Ready")
