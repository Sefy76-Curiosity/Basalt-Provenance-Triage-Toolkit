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
        self.console_plugins = []  # Track console plugins
        self.console_tab_created = False
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

    def _create_console_tab(self):
            """Create the console tab with dropdown selector (like AI tab)"""
            # Create console tab
            self.console_tab = ttk.Frame(self.notebook)
            self.notebook.add(self.console_tab, text="💻 Console")

            # Create selector frame (like AI tab)
            selector_frame = ttk.Frame(self.console_tab)
            selector_frame.pack(fill=tk.X, padx=5, pady=5)

            ttk.Label(selector_frame, text="Console:").pack(side=tk.LEFT, padx=5)

            self.console_var = tk.StringVar()
            self.console_combo = ttk.Combobox(
                selector_frame,
                textvariable=self.console_var,
                state="readonly",
                width=30
            )
            self.console_combo.pack(side=tk.LEFT, padx=5)
            self.console_combo.bind('<<ComboboxSelected>>', self._switch_console)

            # Container for console UI
            self.console_container = ttk.Frame(self.console_tab)
            self.console_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

            self.console_tab_created = True
            self._update_console_dropdown()

    def _update_console_dropdown(self):
        """Update the console dropdown with available consoles"""
        if not self.console_tab_created or not self.console_plugins:
            return

        values = [f"{icon} {name}" for name, icon, _ in self.console_plugins]
        self.console_combo['values'] = values
        self.console_combo.current(0)
        self._switch_console()

    def _switch_console(self, event=None):
        """Switch to selected console"""
        if not self.console_plugins or not self.console_var.get():
            return

        selected = self.console_var.get()

        # Find selected console
        for name, icon, instance in self.console_plugins:
            if f"{icon} {name}" == selected:
                # Clear container
                for widget in self.console_container.winfo_children():
                    widget.destroy()

                # Build new console UI
                instance.create_tab(self.console_container)
                break

    def show_progress(self, operation, current=None, total=None, message=""):
        """
        Show progress for any operation
        operation: str - type of operation (import, export, classification, etc.)
        current: int - current progress count
        total: int - total items to process
        message: str - custom message
        """
        icons = {
            "import": "📥",
            "export": "📤",
            "classification": "🔬",
            "save": "💾",
            "load": "📂",
            "delete": "🗑️",
            "filter": "🔍",
            "plot": "📈",
            "macro": "🎬",
            "plugin": "🔌",
            "processing": "🔄",
            "complete": "✅",
            "error": "❌",
            "warning": "⚠️"
        }

        icon = icons.get(operation, "🔄")

        if current is not None and total is not None and total > 0:
            # Show progress bar style
            percentage = (current / total) * 100
            bar_length = 20
            filled = int(bar_length * current // total)
            bar = "█" * filled + "░" * (bar_length - filled)

            status = f"{icon} {operation.title()}: [{bar}] {current}/{total} ({percentage:.1f}%)"
            if message:
                status += f" - {message}"
        else:
            # Show simple status
            if message:
                status = f"{icon} {message}"
            else:
                status = f"{icon} {operation.title()} in progress..."

        self.status_var.set(status)
        self.last_operation = {
            'type': operation,
            'current': current,
            'total': total,
            'message': message,
            'icon': icon
        }
        self.app.root.update_idletasks()

    def show_operation_complete(self, operation, details=""):
        """Show completion message for an operation"""
        icons = {
            "import": "📥",
            "export": "📤",
            "classification": "🔬",
            "save": "💾",
            "load": "📂",
            "delete": "🗑️",
            "filter": "🔍",
            "plot": "📈",
            "macro": "🎬",
            "plugin": "🔌"
        }

        icon = icons.get(operation, "✅")

        if details:
            status = f"{icon} {operation.title()} complete: {details}"
        else:
            status = f"{icon} {operation.title()} complete"

        self.status_var.set(status)
        self.last_operation = {
            'type': operation,
            'complete': True,
            'details': details
        }
        self.app.root.update_idletasks()

        # Auto-clear after 5 seconds
        self.app.root.after(5000, self._clear_if_complete)

    def _clear_if_complete(self):
        """Clear status if it's still showing a completion message"""
        current = self.status_var.get()
        if "complete" in current.lower() or "✅" in current:
            self.clear_status()

    def show_error(self, operation, error_message):
        """Show error message"""
        self.status_var.set(f"❌ {operation} failed: {error_message[:50]}...")
        self.last_operation = {
            'type': operation,
            'error': error_message
        }
        self.app.root.update_idletasks()

    def show_warning(self, operation, warning_message):
        """Show warning message"""
        self.status_var.set(f"⚠️ {operation}: {warning_message[:50]}...")
        self.last_operation = {
            'type': operation,
            'warning': warning_message
        }
        self.app.root.update_idletasks()

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
        """Build the plots tab with immediate plotter UI loading"""
        ctrl_frame = ttk.Frame(self.plots_tab)
        ctrl_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(ctrl_frame, text="Plot type:").pack(side=tk.LEFT, padx=5)

        self.plot_type_var = tk.StringVar()
        self.plot_type_combo = ttk.Combobox(ctrl_frame, textvariable=self.plot_type_var,
                                            state="readonly", width=30)
        self.plot_type_combo.pack(side=tk.LEFT, padx=5)

        # ADD BACK THE GENERATE PLOT BUTTON
        self.plot_btn = ttk.Button(ctrl_frame, text="🎨 Generate Plot",
                                command=self._generate_plot,
                                style='Accent.TButton')
        self.plot_btn.pack(side=tk.LEFT, padx=5)

        # Bind selection to immediately load the plotter UI
        self.plot_type_combo.bind('<<ComboboxSelected>>', self._load_plotter_ui)

        self.plot_area = tk.Frame(self.plots_tab, bg="white", relief=tk.SUNKEN, borderwidth=1)
        self.plot_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _load_plotter_ui(self, event=None):
        """Immediately load the selected plotter's UI"""
        if not self.plot_types or not self.plot_type_var.get():
            return

        selected = self.plot_type_var.get()
        plot_func = None
        for name, func in self.plot_types:
            if name == selected:
                plot_func = func
                break

        if plot_func:
            # Clear the plot area
            for widget in self.plot_area.winfo_children():
                widget.destroy()

            # Get current samples
            samples = self.app.data_hub.get_page(self.current_page, self.page_size)

            try:
                # Call the plotter function - it should create its own UI
                # including its own "Generate" button
                plot_func(self.plot_area, samples)
            except Exception as e:
                error_label = tk.Label(self.plot_area, text=f"Error loading plotter: {e}",
                                    fg="red", font=("Arial", 10))
                error_label.pack(expand=True)
                import traceback
                traceback.print_exc()

    def update_plot_types(self, plot_types):
        """Update available plot types from plugins"""
        self.plot_types = plot_types
        if plot_types:
            values = [name for name, func in plot_types]
            self.plot_type_combo['values'] = values
            if values:
                # Don't auto-select first one - let user choose
                self.plot_type_combo.set("")
                # Clear plot area
                for widget in self.plot_area.winfo_children():
                    widget.destroy()
                placeholder = tk.Label(self.plot_area,
                                    text="Select a plot type from the dropdown above",
                                    font=("Arial", 12), fg="gray")
                placeholder.pack(expand=True)
                self.plot_placeholder = placeholder

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

    def _on_tree_mousewheel(self, event):
        """Handle mouse wheel on tree - sync with HUD"""
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

    def add_tab_plugin(self, plugin_id, plugin_name, plugin_icon, plugin_instance):
        """
        Add a plugin that gets its own dedicated tab
        """
        # Create the tab frame - this will be added to notebook
        tab_frame = ttk.Frame(self.notebook)

        # Let the plugin build its UI DIRECTLY in tab_frame
        plugin_instance.create_tab(tab_frame)

        # Add to notebook with plugin's icon and name
        tab_text = f"{plugin_icon} {plugin_name}"

        # SAFELY determine insert position
        # Count current tabs
        tab_count = self.notebook.index("end")

        # Insert after plots tab (index 1) but only if it exists
        if tab_count > 1:
            # We have at least 2 tabs (Table and Plots), insert at position 2
            insert_pos = 2
        else:
            # Something's wrong, just append at the end
            insert_pos = tab_count

        try:
            self.notebook.insert(insert_pos, tab_frame, text=tab_text)
            print(f"✅ Added plugin tab: {tab_text} at position {insert_pos}")
        except tk.TclError as e:
            # If insert fails, just add to the end
            print(f"⚠️ Could not insert at position {insert_pos}, appending instead")
            self.notebook.add(tab_frame, text=tab_text)

    def add_console_plugin(self, console_name, console_icon, console_instance):
        """Add a console plugin to the console dropdown"""
        # Check if this console already exists (PREVENT DUPLICATES)
        for existing_name, existing_icon, _ in self.console_plugins:
            if existing_name == console_name and existing_icon == console_icon:
                print(f"⚠️ Console {console_name} already exists, skipping...")
                return

        # Add new console
        self.console_plugins.append((console_name, console_icon, console_instance))
        print(f"✅ Added console: {console_name}")

        # Create console tab if it doesn't exist yet
        if not self.console_tab_created:
            self._create_console_tab()
        else:
            # Update dropdown with new console
            self._update_console_dropdown()

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

        print(f"🔄 Refreshing table with columns: {all_columns}")

        # ============ PRIORITY COLUMN ORDER ============
        # These must be the first columns in EXACT order
        priority_order = [
            "Sample_ID",      # MUST be first
            "Notes",          # MUST be second
            "Museum_Code",    # Third
            "Date",           # Fourth
            "Latitude",       # Fifth
            "Longitude",      # Sixth
        ]

        # Additional metadata that should appear early
        early_metadata = [
            "Depth_cm", "C14_age_BP", "C14_error",  # Chronology data
            "Zr_ppm", "Nb_ppm", "Ba_ppm", "Rb_ppm", "Cr_ppm", "Ni_ppm",  # Key trace elements
            "SiO2_wt", "TiO2_wt", "Al2O3_wt", "Fe2O3_T_wt",  # Major oxides
        ]

        # ============ ALL CLASSIFICATION COLUMNS ============
        # These need to be visible in the table!
        classification_columns = [
            # Primary classification columns
            "Auto_Classification", "TAS_Classification", "Weathering_State",
            "Enrichment_Status", "Planetary_Analog", "Provenance_Fingerprint",
            "CIPW_Category", "Anomaly_Status", "Eruption_Style",
            "Slag_Basicity_Class", "Magmatic_Series", "Collagen_Status",
            "Apatite_Classification", "Trophic_Level", "Estimated_Firing_Temp",
            "Chondrite_Class", "Carbonate_Type", "Bone_Preservation_Status",
            "Pollution_Grade_Igeo", "Glass_Family_Type", "Shock_Stage",
            "Weathering_Grade", "Exploration_Priority", "REE_Pattern_Type",
            "Wentworth_Class", "Salinity_Class", "Sodicity_Class",
            "USDA_Texture_Class", "Full_USDA_Class", "Hardness_Level",
            "Dietary_Group", "IUGS_Volcanic_Class", "TAS_Magmatic_Series",

            # Metadata columns
            "Auto_Confidence", "Flag_For_Review", "Display_Color"
        ]

        # Build final column order
        final_cols = ["☐"]  # Checkbox first

        # Add priority columns that exist
        for col in priority_order:
            if col in all_columns and col not in final_cols:
                final_cols.append(col)

        # Add early metadata that exist and aren't already added
        for col in early_metadata:
            if col in all_columns and col not in final_cols:
                final_cols.append(col)

        # Add classification columns that exist (these are important!)
        for col in classification_columns:
            if col in all_columns and col not in final_cols:
                final_cols.append(col)

        # Add all remaining columns in alphabetical order
        remaining = sorted([col for col in all_columns
                        if col not in final_cols
                        and col not in ["☐", "Display_Color", "Auto_Classification_Color"]])
        final_cols.extend(remaining)

        print(f"📊 Final column order: {final_cols}")

        # Update column configuration if changed
        if list(self.tree["columns"]) != final_cols:
            self.tree["columns"] = final_cols
            for col in final_cols:
                if col == "☐":
                    self.tree.heading(col, text="")
                    self.tree.column(col, width=30, anchor=tk.CENTER, stretch=False)
                else:
                    # Create display name
                    display_name = self._get_display_name(col)
                    self.tree.heading(col, text=display_name, anchor=tk.CENTER)

                    # Set column width based on type
                    if col in priority_order[:2]:  # Sample_ID and Notes
                        self.tree.column(col, width=150, anchor=tk.W, minwidth=100)
                    elif col in priority_order[2:]:  # Other priority
                        self.tree.column(col, width=120, anchor=tk.W, minwidth=80)
                    elif col in classification_columns:  # Classification columns
                        self.tree.column(col, width=130, anchor=tk.W, minwidth=100)
                    elif col in ["Auto_Confidence"]:  # Confidence column
                        self.tree.column(col, width=70, anchor=tk.CENTER, minwidth=50)
                    elif col in ["Flag_For_Review"]:  # Flag column
                        self.tree.column(col, width=50, anchor=tk.CENTER, minwidth=40)
                    else:
                        self.tree.column(col, width=100, anchor=tk.CENTER, minwidth=60)

        # Clear and repopulate
        self.tree.delete(*self.tree.get_children())

        for i, sample in enumerate(samples):
            actual_idx = self.current_page * self.page_size + i
            checkbox = "☑" if actual_idx in self.selected_rows else "☐"

            values = [checkbox]

            # Add values in the same order as columns
            for col in final_cols[1:]:  # Skip checkbox
                val = sample.get(col, "")
                if val is None or val == "":
                    values.append("")
                else:
                    # Format numbers nicely
                    if isinstance(val, (int, float)):
                        if abs(val) < 0.01 or abs(val) > 1000:
                            values.append(f"{val:.2e}")
                        elif val == int(val):
                            values.append(str(int(val)))
                        else:
                            values.append(f"{val:.2f}")
                    else:
                        # For classification names, don't truncate
                        if col in classification_columns and len(str(val)) > 30:
                            values.append(str(val)[:27] + "...")
                        else:
                            values.append(str(val))

            item_id = self.tree.insert("", tk.END, values=tuple(values))

            # Apply color tag if classification exists
            # Try to get the most relevant classification for coloring
            tag = "UNCLASSIFIED"
            for class_col in ["Auto_Classification", "TAS_Classification", "Weathering_State"]:
                if class_col in sample and sample[class_col] and sample[class_col] != "UNCLASSIFIED":
                    tag = sample[class_col]
                    break

            self.tree.item(item_id, tags=(tag,))

        # Auto-size columns
        if self._first_refresh:
            self.app.auto_size_columns(self.tree, samples, force=False)
            self._first_refresh = False

        # Update pagination
        pages = (total + self.page_size - 1) // self.page_size if total > 0 else 1
        self.app.update_pagination(self.current_page, pages, total)
        self.sel_label.config(text=f"Selected: {len(self.selected_rows)}")

    def auto_size_columns(self, tree, samples, force=False):
        """Auto-size columns based on content"""
        if not samples or not tree.get_children():
            return

        columns = tree["columns"]
        for col in columns:
            if col == "☐":
                tree.column(col, width=30, minwidth=30)
                continue

            # Get header width from display name
            header_text = self._get_display_name(col)
            max_width = len(header_text) * 8

            # Check content
            for item in tree.get_children()[:50]:  # Check first 50 rows
                values = tree.item(item, "values")
                col_idx = columns.index(col)
                if col_idx < len(values):
                    text = str(values[col_idx])
                    width = len(text) * 7
                    if width > max_width:
                        max_width = width

            # Set width with reasonable limits
            if col in ["Sample_ID", "Notes"]:
                new_width = min(max(100, max_width), 300)
            elif col in ["Weathering_Features", "Support_Type", "Expected_Classification"]:
                new_width = min(max(120, max_width), 250)
            else:
                new_width = min(max(80, max_width), 200)

            tree.column(col, width=new_width)

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

    def _get_display_name(self, column_name):
        """Get display name from chemical_elements.json"""
        # First, try to find in chemical_elements
        if hasattr(self.app, 'chemical_elements'):
            for elem_key, elem_info in self.app.chemical_elements.items():
                if elem_info.get('standard') == column_name:
                    return elem_info.get('display_name', column_name.replace('_', ' '))

        # If not found, fall back to a clean version
        # Remove common suffixes
        name = column_name
        if name.endswith('_ppm'):
            name = name[:-4] + ' (ppm)'
        elif name.endswith('_pct'):
            name = name[:-4] + '%'
        elif name.endswith('_wt'):
            name = name[:-3] + '%'
        else:
            name = name.replace('_', ' ')

        return name
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
        # ADD THIS LINE 👇
        menu.add_command(label="🔍 Classify This Sample",
                        command=lambda: self._classify_selected_sample(sample_idx))
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

    def _classify_selected_sample(self, sample_idx):
        """Classify a single selected sample"""
        print(f"\n🔍 CLASSIFY SELECTED SAMPLE - Index: {sample_idx}")

        samples = self.app.data_hub.get_all()
        if sample_idx >= len(samples):
            print(f"❌ Sample index {sample_idx} out of range (max: {len(samples)-1})")
            return

        sample = samples[sample_idx]
        print(f"📋 Sample ID: {sample.get('Sample_ID', 'Unknown')}")

        # Get current classification scheme from right panel
        if hasattr(self.app, 'right') and hasattr(self.app.right, 'scheme_var'):
            display_name = self.app.right.scheme_var.get()
            print(f"🎯 Selected scheme display name: '{display_name}'")

            if not display_name:
                messagebox.showinfo("No Scheme", "Please select a classification scheme first")
                return

            # Find scheme ID
            scheme_id = None
            if hasattr(self.app.right, 'schemes'):
                print("🔍 Checking right panel schemes:")
                for sid, info in self.app.right.schemes.items():
                    print(f"   {sid} -> {info.get('name', '')}")
                    if info.get('name') == display_name or info.get('scheme_name') == display_name:
                        scheme_id = sid
                        print(f"✓ Found in right panel: {scheme_id}")
                        break

            if not scheme_id and self.app.classification_engine:
                print("🔍 Checking engine schemes directly:")
                for sid, scheme in self.app.classification_engine.schemes.items():
                    print(f"   {sid} -> {scheme.get('scheme_name', '')}")
                    if scheme.get('scheme_name') == display_name:
                        scheme_id = sid
                        print(f"✓ Found in engine: {scheme_id}")
                        break

            if not scheme_id:
                import re
                clean_name = re.sub(r'[✅🔬🏛🌍🪐🏺💎⚒🌋🎯]', '', display_name).strip()
                print(f"🔍 Trying clean name: '{clean_name}'")

                if self.app.classification_engine:
                    for sid, scheme in self.app.classification_engine.schemes.items():
                        scheme_clean = re.sub(r'[✅🔬🏛🌍🪐🏺💎⚒🌋🎯]', '', scheme.get('scheme_name', '')).strip()
                        if scheme_clean == clean_name:
                            scheme_id = sid
                            print(f"✓ Found via clean name: {scheme_id}")
                            break

            if not scheme_id:
                print(f"❌ Could not find scheme ID for '{display_name}'")
                messagebox.showerror("Error", f"Could not find scheme ID for '{display_name}'")
                return

            if self.app.classification_engine:
                try:
                    print(f"🚀 Running classification with scheme: {scheme_id}")

                    # Run classification
                    result, confidence, color = self.app.classification_engine.classify_sample(sample, scheme_id)
                    print(f"✅ Classification result: {result}")
                    print(f"   Confidence: {confidence}")
                    print(f"   Color: {color}")

                    # ============ FIX: SAVE THE RESULT ============
                    # Get scheme info to know which column to update
                    scheme_info = self.app.classification_engine.get_scheme_info(scheme_id)
                    output_column = scheme_info.get('output_column', 'Auto_Classification')
                    confidence_column = scheme_info.get('confidence_column_name', 'Auto_Confidence')
                    flag_column = scheme_info.get('flag_column_name', 'Flag_For_Review')

                    print(f"📌 Output column: {output_column}")
                    print(f"📌 Confidence column: {confidence_column}")

                    # Create updates dictionary
                    updates = {
                        output_column: result,
                        confidence_column: confidence,
                        'Display_Color': color
                    }

                    print(f"📝 Updates to apply: {updates}")

                    # Add flag if scheme uses it
                    if scheme_info.get('flag_uncertain', False):
                        uncertain_threshold = scheme_info.get('uncertain_threshold', 0.7)
                        updates[flag_column] = (confidence < uncertain_threshold)
                        print(f"🚩 Flag set to: {updates[flag_column]}")

                    # Also add any computed ratios that might be useful
                    ratio_keys = ['Zr_Nb_Ratio', 'Cr_Ni_Ratio', 'Ba_Rb_Ratio',
                                'Ti_V_Ratio', 'Nb_Yb_Ratio', 'Th_Yb_Ratio',
                                'Fe_Mn_Ratio', 'CIA_Value', 'V_Ratio',
                                'Total_Alkali', 'Mg_Number', 'ACNK']

                    for key in ratio_keys:
                        if key in sample and sample[key] is not None:
                            updates[key] = sample[key]
                            print(f"📊 Adding computed ratio: {key} = {sample[key]}")

                    # Update the sample in DataHub
                    print(f"💾 Updating DataHub row {sample_idx}")
                    self.app.data_hub.update_row(sample_idx, updates)

                    # Force a refresh of the table to show the new classification
                    print(f"🔄 Refreshing table...")
                    self._refresh()

                    # Also update the HUD in right panel
                    if hasattr(self.app, 'right') and hasattr(self.app.right, '_update_hud'):
                        print(f"🔄 Updating HUD...")
                        self.app.right._update_hud()

                    # Show result popup
                    print(f"📊 Showing result popup...")
                    self._show_classification_result(result, confidence, color, sample)

                    # Show success in status bar
                    self.set_status(f"✅ Classified as: {result}", "success")

                    print(f"✅ Classification complete!")

                except Exception as e:
                    print(f"❌ Classification error: {e}")
                    import traceback
                    traceback.print_exc()
                    messagebox.showerror("Error", f"Classification failed: {e}")
            else:
                print(f"❌ Classification engine not available")
                messagebox.showerror("Error", "Classification engine not available")

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

    def _show_classification_result(self, result, confidence, color, sample):
        """Show classification result in a popup"""
        win = tk.Toplevel(self.app.root)
        win.title("Classification Result")
        win.geometry("500x400")
        win.transient(self.app.root)

        main = ttk.Frame(win, padding=15)
        main.pack(fill=tk.BOTH, expand=True)

        # Sample ID
        sample_id = sample.get('Sample_ID', 'Unknown')
        ttk.Label(main, text=f"Sample: {sample_id}",
                font=("Arial", 12, "bold")).pack(pady=(0, 10))

        # Result with color
        result_frame = tk.Frame(main, bg=color, height=40, relief=tk.RAISED, bd=1)
        result_frame.pack(fill=tk.X, pady=10)
        result_frame.pack_propagate(False)

        tk.Label(result_frame, text=result, bg=color,
                font=("Arial", 14, "bold")).pack(expand=True)

        # Confidence
        conf_text = f"{confidence:.1%}" if isinstance(confidence, (int, float)) else str(confidence)
        ttk.Label(main, text=f"Confidence: {conf_text}").pack(pady=5)

        # Sample values
        values_frame = ttk.LabelFrame(main, text="Sample Values", padding=10)
        values_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Create text widget with scrollbar
        text_frame = ttk.Frame(values_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        text_widget = tk.Text(text_frame, wrap=tk.WORD, font=("Courier", 9), height=10)
        scrollbar = ttk.Scrollbar(text_frame, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)

        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Add values
        for key, value in sample.items():
            if key not in ['Sample_ID', 'Notes'] and value not in [None, '', 'None']:
                if isinstance(value, float):
                    text_widget.insert(tk.END, f"{key}: {value:.2f}\n")
                else:
                    text_widget.insert(tk.END, f"{key}: {value}\n")

        text_widget.config(state=tk.DISABLED)

        # Close button
        ttk.Button(main, text="Close", command=win.destroy).pack(pady=10)

        # Center window
        win.update_idletasks()
        x = (win.winfo_screenwidth() // 2) - (win.winfo_width() // 2)
        y = (win.winfo_screenheight() // 2) - (win.winfo_height() // 2)
        win.geometry(f"+{x}+{y}")

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
