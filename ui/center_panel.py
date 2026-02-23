"""
Center Panel - 80% width, Dynamic Table with Tabs
Includes status bar between navigation and selection controls
Fully converted to ttkbootstrap with minimal borders
"""

import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from collections import Counter
import os
import json

class CenterPanel:
    # Icon map shared by set_status / show_progress / show_operation_complete
    STATUS_ICONS = {
        "info":       "ℹ️",
        "success":    "✅",
        "warning":    "⚠️",
        "error":      "❌",
        "processing": "🔄",
        "import":     "📥",
        "export":     "📤",
        "classification": "🔬",
        "save":       "💾",
        "load":       "📂",
        "delete":     "🗑️",
        "filter":     "🔍",
        "plot":       "📈",
        "macro":      "🎬",
        "plugin":     "🔌",
        "complete":   "✅",
    }
    def __init__(self, parent, app):
        self.app = app
        self.frame = ttk.Frame(parent, bootstyle="dark")

        # State
        self.current_page = 0
        self.page_size = 50
        self.selected_rows = set()
        self.filtered_indices = None

        # >>> COLUMNS SORTING <<<
        self.sort_column = None
        self.sort_reverse = False
        self.sorted_indices = None

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
        self.console_plugins = []
        self.console_tab_created = False
        self._is_syncing_scroll = False

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        self.last_classification_summary = ""
        self.last_operation = {'type': 'none'}
        self.last_classification_details = None

        self._build_ui()
        # Add sorting state

    def _build_ui(self):
        """Build center panel with tabs"""
        self.notebook = ttk.Notebook(self.frame, bootstyle="dark")
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        # Tab 1: Data Table
        self.table_tab = ttk.Frame(self.notebook, bootstyle="dark")
        self.notebook.add(self.table_tab, text="📊 Data Table")
        self._build_table_tab()

        # Tab 2: Plots
        self.plots_tab = ttk.Frame(self.notebook, bootstyle="dark")
        self.notebook.add(self.plots_tab, text="📈 Plots")
        self._build_plots_tab()

    def _build_table_tab(self):
        """Build the data table tab with minimal borders"""
        # ============ FILTER BAR ============
        filter_frame = ttk.Frame(self.table_tab, bootstyle="dark")
        filter_frame.pack(fill=tk.X, padx=1, pady=1)

        ttk.Label(
            filter_frame,
            text="🔍 Search:",
            bootstyle="light"
        ).pack(side=tk.LEFT)

        self.search_var.trace("w", lambda *a: self._apply_filter())
        self.search_entry = ttk.Entry(
            filter_frame,
            textvariable=self.search_var,
            width=30,
            bootstyle="light"
        )
        self.search_entry.pack(side=tk.LEFT, padx=5)

        ttk.Label(
            filter_frame,
            text="Filter:",
            bootstyle="light"
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            filter_frame,
            text="↺ Clear Sort",
            command=self.clear_sort,
            bootstyle="secondary"
        ).pack(side=tk.LEFT, padx=5)

        self.filter_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.filter_var,
            values=["All"],
            state="readonly",
            width=15,
            bootstyle="light"
        )
        self.filter_combo.pack(side=tk.LEFT, padx=5)
        self.filter_combo.bind('<<ComboboxSelected>>', lambda e: self._apply_filter())

        ttk.Button(
            filter_frame,
            text="Clear",
            command=self._clear_filter,
            bootstyle="secondary"
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            filter_frame,
            text="↔ Reset Columns",
            command=self._reset_column_widths,
            bootstyle="secondary"
        ).pack(side=tk.LEFT, padx=5)

        self.sel_label = ttk.Label(
            filter_frame,
            text="Selected: 0",
            bootstyle="light"
        )
        self.sel_label.pack(side=tk.RIGHT, padx=10)

        # ============ TABLE with MINIMAL BORDERS ============
        table_container = ttk.Frame(self.table_tab, bootstyle="dark")
        table_container.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        # Create treeview with minimal border
        self.tree = ttk.Treeview(
            table_container,
            show="headings",
            height=20
        )

        self.tree.bind("<Button-1>", self._on_header_click)

        # Scrollbars - minimal styling
        vsb = ttk.Scrollbar(
            table_container,
            orient="vertical",
            command=self.tree.yview,
            bootstyle="dark-round"
        )
        hsb = ttk.Scrollbar(
            table_container,
            orient="horizontal",
            command=self.tree.xview,
            bootstyle="dark-round"
        )
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Grid layout with no extra borders
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)

        # Bindings
        self.tree.bind("<ButtonRelease-3>", self._show_context_menu)      # Windows / Linux
        self.tree.bind("<ButtonRelease-2>", self._show_context_menu)      # macOS alt
        self.tree.bind("<Control-ButtonRelease-1>", self._show_context_menu)  # macOS ctrl-click
        self.tree.bind("<Double-1>", self._on_double_click)

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
            fg_color = self.app.color_manager.get_foreground(classification)

            if classification not in configured_tags:
                self.tree.tag_configure(
                    classification,
                    background=bg_color,
                    foreground=fg_color
                )
                configured_tags.add(classification)

            upper = classification.upper()
            if upper not in configured_tags:
                self.tree.tag_configure(
                    upper,
                    background=bg_color,
                    foreground=fg_color
                )
                configured_tags.add(upper)

        # Configure special tags
        self.tree.tag_configure('ALL_MATCHED', background='#1a4a2e', foreground='white')
        self.tree.tag_configure('ALL_NONE', background='#3b3b3b', foreground='white')
        self.tree.tag_configure('UNCLASSIFIED', background='#3b3b3b', foreground='white')
        self.tree.tag_configure('MULTI_MATCH', background='#8B4513', foreground='white')  # Brown/terra cotta to stand out

    def _build_plots_tab(self):
        """Build the plots tab with immediate plotter UI loading"""
        ctrl_frame = ttk.Frame(self.plots_tab, bootstyle="dark")
        ctrl_frame.pack(fill=tk.X, padx=2, pady=2)

        ttk.Label(
            ctrl_frame,
            text="Plot type:",
            bootstyle="light"
        ).pack(side=tk.LEFT, padx=5)

        self.plot_type_var = tk.StringVar()
        self.plot_type_combo = ttk.Combobox(
            ctrl_frame,
            textvariable=self.plot_type_var,
            state="readonly",
            width=30,
            bootstyle="light"
        )
        self.plot_type_combo.pack(side=tk.LEFT, padx=5)

        # Generate Plot button
        self.plot_btn = ttk.Button(
            ctrl_frame,
            text="🎨 Generate Plot",
            command=self._generate_plot,
            bootstyle="primary"
        )
        self.plot_btn.pack(side=tk.LEFT, padx=5)

        # Bind selection to immediately load the plotter UI
        self.plot_type_combo.bind('<<ComboboxSelected>>', self._load_plotter_ui)

        self.plot_area = ttk.Frame(
            self.plots_tab,
            bootstyle="dark"
        )
        self.plot_area.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

    def _create_console_tab(self):
        """Create the console tab with dropdown selector"""
        self.console_tab = ttk.Frame(self.notebook, bootstyle="dark")
        self.notebook.add(self.console_tab, text="💻 Console")

        selector_frame = ttk.Frame(self.console_tab, bootstyle="dark")
        selector_frame.pack(fill=tk.X, padx=2, pady=2)

        ttk.Label(
            selector_frame,
            text="Console:",
            bootstyle="light"
        ).pack(side=tk.LEFT, padx=5)

        self.console_var = tk.StringVar()
        self.console_combo = ttk.Combobox(
            selector_frame,
            textvariable=self.console_var,
            state="readonly",
            width=30,
            bootstyle="light"
        )
        self.console_combo.pack(side=tk.LEFT, padx=5)
        self.console_combo.bind('<<ComboboxSelected>>', self._switch_console)

        self.console_container = ttk.Frame(self.console_tab, bootstyle="dark")
        self.console_container.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        self.console_tab_created = True
        self._update_console_dropdown()

    def _update_console_dropdown(self):
        """Update the console dropdown with available consoles"""
        if not self.console_tab_created or not self.console_plugins:
            return

        values = [f"{icon} {name}" for name, icon, _ in self.console_plugins]
        self.console_combo['values'] = values
        if values:
            self.console_combo.current(0)
            self._switch_console()

    def _switch_console(self, event=None):
        """Switch to selected console"""
        if not self.console_plugins or not self.console_var.get():
            return

        selected = self.console_var.get()
        for name, icon, instance in self.console_plugins:
            if f"{icon} {name}" == selected:
                for widget in self.console_container.winfo_children():
                    widget.destroy()
                instance.create_tab(self.console_container)
                break

    def _create_ai_tab(self):
        """Create AI assistant tab"""
        self.ai_tab = ttk.Frame(self.notebook, bootstyle="dark")
        self.notebook.add(self.ai_tab, text="🤖 AI Assistant")

        selector_frame = ttk.Frame(self.ai_tab, bootstyle="dark")
        selector_frame.pack(fill=tk.X, padx=2, pady=2)

        ttk.Label(
            selector_frame,
            text="Assistant:",
            bootstyle="light"
        ).pack(side=tk.LEFT, padx=5)

        self.ai_var = tk.StringVar()
        self.ai_combo = ttk.Combobox(
            selector_frame,
            textvariable=self.ai_var,
            state="readonly",
            width=30,
            bootstyle="light"
        )
        self.ai_combo.pack(side=tk.LEFT, padx=5)
        self.ai_combo.bind('<<ComboboxSelected>>', self._switch_ai)

        self.ai_container = ttk.Frame(self.ai_tab, bootstyle="dark")
        self.ai_container.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        self.ai_tab_created = True
        self._update_ai_dropdown()

    def _update_ai_dropdown(self):
        """Update AI assistant dropdown"""
        if not self.ai_tab_created or not self.ai_plugins:
            return

        values = [f"{icon} {name}" for name, icon, _ in self.ai_plugins]
        self.ai_combo['values'] = values
        if values:
            self.ai_combo.current(0)
            self._switch_ai()

    def _switch_ai(self, event=None):
        """Switch AI assistant"""
        if not self.ai_plugins or not self.ai_var.get():
            return

        selected = self.ai_var.get()
        for name, icon, instance in self.ai_plugins:
            if f"{icon} {name}" == selected:
                for widget in self.ai_container.winfo_children():
                    widget.destroy()
                if hasattr(instance, 'create_tab'):
                    instance.create_tab(self.ai_container)
                break

    def add_tab_plugin(self, plugin_id, plugin_name, plugin_icon, plugin_instance):
        """Add a plugin that gets its own dedicated tab"""
        tab_frame = ttk.Frame(self.notebook, bootstyle="dark")
        plugin_instance.create_tab(tab_frame)
        tab_text = f"{plugin_icon} {plugin_name}"

        tab_count = self.notebook.index("end")
        if tab_count > 1:
            insert_pos = 2
        else:
            insert_pos = tab_count

        try:
            self.notebook.insert(insert_pos, tab_frame, text=tab_text)
            print(f"✅ Added plugin tab: {tab_text} at position {insert_pos}")
        except tk.TclError:
            print(f"⚠️ Could not insert at position {insert_pos}, appending instead")
            self.notebook.add(tab_frame, text=tab_text)

    def add_console_plugin(self, console_name, console_icon, console_instance):
        """Add a console plugin to the console dropdown"""
        for existing_name, existing_icon, _ in self.console_plugins:
            if existing_name == console_name and existing_icon == console_icon:
                print(f"⚠️ Console {console_name} already exists, skipping...")
                return

        self.console_plugins.append((console_name, console_icon, console_instance))
        print(f"✅ Added console: {console_name}")

        if not self.console_tab_created:
            self._create_console_tab()
        else:
            self._update_console_dropdown()

    def add_ai_plugin(self, plugin_name, plugin_icon, plugin_instance):
        """Add an AI plugin to the AI assistant dropdown"""
        for existing_name, existing_icon, _ in self.ai_plugins:
            if existing_name == plugin_name and existing_icon == plugin_icon:
                print(f"⚠️ AI plugin {plugin_name} already exists, skipping...")
                return

        self.ai_plugins.append((plugin_name, plugin_icon, plugin_instance))
        print(f"✅ Added AI plugin: {plugin_name}")

        if not self.ai_tab_created:
            self._create_ai_tab()
        else:
            self._update_ai_dropdown()

    def on_data_changed(self, event, *args):
        self._refresh()

    def _refresh(self):
        """Refresh table - fixed columns first, then chemical data (sorted-sync enabled)"""
        if not self.tree:
            return

        search = self.search_var.get().lower().strip()
        filter_class = self.filter_var.get()

        all_samples = self.app.data_hub.get_all()
        all_results = getattr(self.app.right, 'classification_results', [])
        total_rows = len(all_samples)

        # =====================================================
        # MASTER ORDER (this is the important new part)
        # =====================================================
        if getattr(self, "sorted_indices", None):
            ordered_indices = self.sorted_indices
        else:
            ordered_indices = list(range(total_rows))

        # =====================================================
        # FILTERING (applied on ordered list)
        # =====================================================
        filtered = []

        for idx in ordered_indices:
            s = all_samples[idx]

            # Search filter — match any field value
            if search:
                if not any(search in str(v).lower() for v in s.values()):
                    continue

            # Classification filter
            if filter_class and filter_class != "All":
                cls = ''
                if idx < len(all_results) and all_results[idx]:
                    cls = all_results[idx].get('classification', '')
                if not cls:
                    cls = (s.get('Auto_Classification') or s.get('Classification') or '')
                if cls != filter_class:
                    continue

            filtered.append((idx, s))

        total = len(filtered)

        # =====================================================
        # PAGINATION
        # =====================================================
        start = self.current_page * self.page_size
        page_items = filtered[start:start + self.page_size]
        samples = [s for _, s in page_items]
        page_actual_indices = [i for i, _ in page_items]

        all_columns = self.app.data_hub.get_column_names()

        # ============ PRIORITY COLUMN ORDER ============
        priority_order = [
            "Sample_ID", "Notes", "Museum_Code", "Date", "Latitude", "Longitude",
        ]

        early_metadata = [
            "Depth_cm", "C14_age_BP", "C14_error",
            "Zr_ppm", "Nb_ppm", "Ba_ppm", "Rb_ppm", "Cr_ppm", "Ni_ppm",
            "SiO2_wt", "TiO2_wt", "Al2O3_wt", "Fe2O3_T_wt",
        ]

        classification_columns = [
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
            "Auto_Confidence", "Flag_For_Review", "Display_Color"
        ]

        final_cols = ["☐"]

        for col in priority_order:
            if col in all_columns and col not in final_cols:
                final_cols.append(col)

        for col in early_metadata:
            if col in all_columns and col not in final_cols:
                final_cols.append(col)

        for col in classification_columns:
            if col in all_columns and col not in final_cols:
                final_cols.append(col)

        remaining = sorted([
            col for col in all_columns
            if col not in final_cols
            and col not in ["☐", "Display_Color", "Auto_Classification_Color"]
        ])

        final_cols.extend(remaining)

        if list(self.tree["columns"]) != final_cols:
            self.tree["columns"] = final_cols
            for col in final_cols:
                if col == "☐":
                    self.tree.heading(col, text="")
                    self.tree.column(col, width=30, anchor=tk.CENTER, stretch=False)
                else:
                    display_name = self._get_display_name(col)
                    self.tree.heading(col, text=display_name, anchor=tk.CENTER)

                    if col in priority_order[:2]:
                        self.tree.column(col, width=150, anchor=tk.W, minwidth=100)
                    elif col in priority_order[2:]:
                        self.tree.column(col, width=120, anchor=tk.W, minwidth=80)
                    elif col in classification_columns:
                        self.tree.column(col, width=130, anchor=tk.W, minwidth=100)
                    elif col == "Auto_Confidence":
                        self.tree.column(col, width=70, anchor=tk.CENTER, minwidth=50)
                    elif col == "Flag_For_Review":
                        self.tree.column(col, width=50, anchor=tk.CENTER, minwidth=40)
                    else:
                        self.tree.column(col, width=100, anchor=tk.CENTER, minwidth=60)

        self.tree.delete(*self.tree.get_children())

        for i, sample in enumerate(samples):
            actual_idx = page_actual_indices[i]
            checkbox = "☑" if actual_idx in self.selected_rows else "☐"
            values = [checkbox]

            for col in final_cols[1:]:
                val = sample.get(col, "")
                if val is None or val == "":
                    values.append("")
                elif isinstance(val, (int, float)):
                    if abs(val) < 0.01 or abs(val) > 1000:
                        values.append(f"{val:.2e}")
                    elif val == int(val):
                        values.append(str(int(val)))
                    else:
                        values.append(f"{val:.2f}")
                else:
                    if col in classification_columns and len(str(val)) > 30:
                        values.append(str(val)[:27] + "...")
                    else:
                        values.append(str(val))

            # Tag logic unchanged
            if hasattr(self.app.right, 'all_mode') and self.app.right.all_mode:
                all_results = getattr(self.app.right, 'all_results', None)
                if all_results and actual_idx < len(all_results) and all_results[actual_idx] is not None:
                    match_count = 0
                    best_class = None
                    best_conf = -1.0

                    for r in all_results[actual_idx]:
                        if r[1] not in ['UNCLASSIFIED', 'INVALID_SAMPLE', 'SCHEME_NOT_FOUND', '']:
                            match_count += 1
                            if r[2] > best_conf:
                                best_class = r[1]
                                best_conf = r[2]

                    if match_count > 1:
                        tag = 'MULTI_MATCH'
                    elif match_count == 1:
                        tag = best_class
                    else:
                        tag = 'ALL_NONE'
                else:
                    tag = 'ALL_NONE'
            else:
                tag = "UNCLASSIFIED"
                if hasattr(self.app.right, 'classification_results') and actual_idx < len(self.app.right.classification_results):
                    result = self.app.right.classification_results[actual_idx]
                    if result and result.get('classification'):
                        tag = result['classification']
                if tag == "UNCLASSIFIED":
                    for class_col in ["Auto_Classification", "TAS_Classification", "Weathering_State"]:
                        if class_col in sample and sample[class_col] and sample[class_col] != "UNCLASSIFIED":
                            tag = sample[class_col]
                            break

            item_id = f"row_{actual_idx}"
            self.tree.insert("", tk.END, iid=item_id, values=tuple(values), tags=(tag,))

        if not hasattr(self, '_multi_match_configured'):
            self.tree.tag_configure('MULTI_MATCH', background='#8B4513', foreground='white')
            self._multi_match_configured = True

        if self._first_refresh:
            self.app.auto_size_columns(self.tree, samples, force=False)
            self._first_refresh = False

        pages = (total + self.page_size - 1) // self.page_size if total > 0 else 1
        self.app.update_pagination(self.current_page, pages, total)
        self._notify_selection_changed()

    def auto_size_columns(self, tree, samples, force=False):
        """Auto-size columns based on content"""
        if not samples or not tree.get_children():
            return

        columns = tree["columns"]
        # Pre-compute index map to avoid O(n) .index() call inside double loop
        col_index = {col: i for i, col in enumerate(columns)}

        for col in columns:
            if col == "☐":
                tree.column(col, width=30, minwidth=30)
                continue

            header_text = self._get_display_name(col)
            max_width = len(header_text) * 8

            idx = col_index[col]
            for item in tree.get_children()[:50]:
                values = tree.item(item, "values")
                if idx < len(values):
                    text = str(values[idx])
                    width = len(text) * 7
                    if width > max_width:
                        max_width = width

            if col in ["Sample_ID", "Notes"]:
                new_width = min(max(100, max_width), 300)
            else:
                new_width = min(max(80, max_width), 200)

            tree.column(col, width=new_width)

    def _on_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            item = self.tree.identify_row(event.y)
            if column == "#1" and item:
                self._toggle_row(item)

    def _on_column_resize(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "separator":
            self.tree._columns_manually_sized = True

    def _toggle_row(self, item_id):
        """Toggle selection for a row identified by its tree item id (iid)"""
        # Extract original index from the item's iid (which we set in _refresh)
        if item_id.startswith('row_'):
            try:
                actual_idx = int(item_id.split('_')[1])
            except (ValueError, IndexError):
                return
        else:
            # Fallback for any rows that might not have the new iid (shouldn't happen)
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
        self._notify_selection_changed()

    def select_all(self):
        total = self.app.data_hub.row_count()
        for i in range(total):
            self.selected_rows.add(i)
        self._notify_selection_changed()
        self._refresh()

    def deselect_all(self):
        self.selected_rows.clear()
        self._notify_selection_changed()
        self._refresh()

    def _notify_selection_changed(self):
        count = len(self.selected_rows)

        # If in all-schemes mode, show multi-match count
        if hasattr(self.app.right, 'all_mode') and self.app.right.all_mode:
            multi_count = 0
            for idx in self.selected_rows:
                if (hasattr(self.app.right, 'all_results') and
                    idx < len(self.app.right.all_results) and
                    self.app.right.all_results[idx]):
                    # Check if any scheme matched
                    for r in self.app.right.all_results[idx]:
                        if r[1] not in ['UNCLASSIFIED', 'INVALID_SAMPLE', 'SCHEME_NOT_FOUND', '']:
                            multi_count += 1
                            break
            self.sel_label.config(text=f"Selected: {count} ({multi_count} multi-match)")
        else:
            self.sel_label.config(text=f"Selected: {count}")

        self.app.update_selection(count)

    def get_selected_indices(self):
        return list(self.selected_rows)

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self._refresh()
            if hasattr(self.app.right, '_update_hud'):
                self.app.right._update_hud()

    def next_page(self):
        total = self.app.data_hub.row_count()
        pages = (total + self.page_size - 1) // self.page_size
        if self.current_page < pages - 1:
            self.current_page += 1
            self._refresh()
            if hasattr(self.app.right, '_update_hud'):
                self.app.right._update_hud()

    def _get_display_name(self, column_name):
        if hasattr(self.app, 'chemical_elements'):
            for elem_info in self.app.chemical_elements.values():
                if elem_info.get('standard') == column_name:
                    return elem_info.get('display_name', column_name.replace('_', ' '))

        name = column_name
        if name.endswith('_ppm'):
            return name[:-4] + ' (ppm)'
        elif name.endswith('_pct'):
            return name[:-4] + '%'
        elif name.endswith('_wt'):
            return name[:-3] + '%'
        else:
            return name.replace('_', ' ')

    def _apply_filter(self):
        self.current_page = 0
        self._refresh()
        self.app.right._update_hud()          # <-- add this

    def _clear_filter(self):
        self.search_var.set("")
        self.filter_var.set("All")
        self.current_page = 0
        self._refresh()
        self.app.right._update_hud()          # <-- add this

    def _on_header_click(self, event):
        """Handle click on column header for sorting"""
        region = self.tree.identify("region", event.x, event.y)
        if region == "heading":
            column = self.tree.identify_column(event.x)
            if column and column != "#1":  # Don't sort checkbox column
                col_index = int(column[1:]) - 1
                col_name = self.tree["columns"][col_index]
                self._sort_by_column(col_name)

    def _sort_by_column(self, column_name):
        """Sort all data by the given column (table + HUD synced)"""

        # Toggle sort direction if same column clicked
        if self.sort_column == column_name:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column_name
            self.sort_reverse = False

        # Get all samples
        all_samples = self.app.data_hub.get_all()
        if not all_samples:
            return

        # Create list of (original_index, sample) pairs
        indexed_samples = list(enumerate(all_samples))

        # Sort based on column values
        indexed_samples.sort(
            key=lambda x: self._get_sort_value(x[1], column_name),
            reverse=self.sort_reverse
        )

        # Store the sorted indices mapping (new position -> original index)
        self.sorted_indices = [orig_idx for orig_idx, _ in indexed_samples]

        # Update column headers to show sort direction
        self._update_header_indicators()

        # Refresh the display with sorted data
        self._refresh()

        # ==========================================================
        # 🔥 NEW PART — Sync RightPanel HUD with this sorted order
        # ==========================================================
        if hasattr(self.app, "right") and hasattr(self.app.right, "update_hud_with_sort"):
            self.app.right.update_hud_with_sort(
                self.sorted_indices,
                is_sorted=True
            )

    def _get_sort_value(self, sample, column_name):
        """Extract and normalize value for sorting"""
        value = sample.get(column_name, "")

        # Handle empty values
        if value == "" or value is None:
            return (1, "")  # Empty values go to bottom

        # Try to convert to number for numeric sorting
        try:
            # Check if it's already a number
            if isinstance(value, (int, float)):
                return (0, value)
            # Try to convert string to float
            num_val = float(value)
            return (0, num_val)
        except (ValueError, TypeError):
            # Fall back to string comparison (case-insensitive)
            return (2, str(value).lower())

    def _update_header_indicators(self):
        """Update column headers to show sort direction"""
        for col in self.tree["columns"]:
            if col == "☐":
                continue

            display_name = self._get_display_name(col)
            if col == self.sort_column:
                indicator = " ↑" if not self.sort_reverse else " ↓"
                self.tree.heading(col, text=display_name + indicator)
            else:
                self.tree.heading(col, text=display_name)

    def clear_sort(self):
        """Clear sorting and restore natural order"""
        self.sort_column = None
        self.sort_reverse = False
        self.sorted_indices = None

        self._update_header_indicators()
        self._refresh()

        # Notify HUD that sorting was cleared
        if hasattr(self.app, "right") and hasattr(self.app.right, "update_hud_with_sort"):
            self.app.right.update_hud_with_sort(None, False)
    def _reset_column_widths(self):
        if hasattr(self.tree, '_columns_manually_sized'):
            self.tree._columns_manually_sized = False
        samples = self.app.data_hub.get_page(self.current_page, self.page_size)
        if samples:
            self.app.auto_size_columns(self.tree, samples, force=True)

    def _on_double_click(self, event):
        """Handle double-click on table"""
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        item = self.tree.identify_row(event.y)
        if not item:
            return

        # Extract original index from the item's iid (which we set in _refresh)
        if item.startswith('row_'):
            try:
                sample_idx = int(item.split('_')[1])
            except (ValueError, IndexError):
                return
        else:
            # Fallback for any rows that might not have the new iid (shouldn't happen)
            item_idx = self.tree.index(item)
            sample_idx = self.current_page * self.page_size + item_idx

        samples = self.app.data_hub.get_all()

        if sample_idx >= len(samples):
            return

        # IMPORTANT: Check if we're in all-mode - if so, show all-schemes dialog
        if hasattr(self.app.right, 'all_mode') and self.app.right.all_mode and self.app.right.all_results is not None:
            # Import here to avoid circular imports
            from ui.all_schemes_detail_dialog import AllSchemesDetailDialog
            AllSchemesDetailDialog(
                self.app.root,
                self.app,
                samples,
                self.app.right.all_results,
                sample_idx,
                self.app.right.all_schemes_list
            )
        else:
            # Delegate to right_panel for single scheme
            self.app.right._open_sample_detail(sample_idx, samples)

        return "break"  # Important: prevents event propagation

    def _show_classification_explanation(self, sample, classification=None, confidence=None, color=None, derived=None, flag=False):
        """Show detailed explanation for single scheme classification"""
        # Get the current scheme name from right panel
        scheme_name = "Unknown Scheme"
        if hasattr(self.app.right, 'scheme_var'):
            scheme_name = self.app.right.scheme_var.get()

        win = ttk.Toplevel(self.app.root)
        win.title(f"Classification: {sample.get('Sample_ID', 'Unknown')}")
        win.geometry("700x600")
        win.transient(self.app.root)

        def set_grab():
            win.grab_set()
            win.focus_force()
        win.after(100, set_grab)

        main = ttk.Frame(win, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        # Header
        header_frame = ttk.Frame(main)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(
            header_frame,
            text=f"Sample: {sample.get('Sample_ID', 'Unknown')}",
            font=("Arial", 14, "bold"),
            bootstyle="light"
        ).pack(anchor=tk.W)

        if classification is None:
            classification = (sample.get('Final_Classification') or
                            sample.get('Auto_Classification') or
                            sample.get('Classification') or
                            "UNCLASSIFIED")
        if confidence is None:
            confidence = sample.get('Auto_Confidence', 'N/A')
        if color is None:
            color = '#A9A9A9'

        # Classification and confidence
        class_frame = ttk.Frame(main)
        class_frame.pack(fill=tk.X, pady=5)

        ttk.Label(
            class_frame,
            text="Classification:",
            font=("Arial", 11, "bold"),
            bootstyle="light"
        ).pack(side=tk.LEFT)

        fg_color = self.app.color_manager.get_foreground(classification)
        ttk.Label(
            class_frame,
            text=classification,
            font=("Arial", 11),
            foreground=fg_color,
            bootstyle="light"
        ).pack(side=tk.LEFT, padx=10)

        ttk.Label(
            class_frame,
            text=f"Confidence: {confidence}",
            font=("Arial", 10),
            bootstyle="light"
        ).pack(side=tk.RIGHT)

        ttk.Separator(main, orient=tk.HORIZONTAL, bootstyle="secondary").pack(fill=tk.X, pady=10)

        # Create notebook for tabs
        notebook = ttk.Notebook(main, bootstyle="dark")
        notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Explanation
        explanation_frame = ttk.Frame(notebook, padding=10)
        notebook.add(explanation_frame, text="📝 Explanation")

        style = ttk.Style.get_instance()
        bg = style.colors.get('dark') if hasattr(style, 'colors') else "#2b2b2b"
        fg = style.colors.get('light') if hasattr(style, 'colors') else "#dddddd"

        text_widget = tk.Text(
            explanation_frame,
            wrap=tk.WORD,
            font=("TkDefaultFont", 11),
            height=20,
            bg=bg,
            fg=fg,
            insertbackground=fg,
            relief=tk.FLAT,
            bd=0
        )
        scrollbar = ttk.Scrollbar(
            explanation_frame,
            command=text_widget.yview,
            bootstyle="dark-round"
        )
        text_widget.configure(yscrollcommand=scrollbar.set)

        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Generate intelligent explanation
        explanation = self._generate_single_scheme_explanation(scheme_name, classification, sample)
        text_widget.insert(tk.END, explanation)
        text_widget.config(state=tk.DISABLED)

        # Tab 2: Raw Data
        raw_frame = ttk.Frame(notebook, padding=10)
        notebook.add(raw_frame, text="📋 All Fields")

        raw_text = tk.Text(
            raw_frame,
            wrap=tk.NONE,
            font=("Courier", 9),
            height=20,
            bg=bg,
            fg=fg,
            relief=tk.FLAT,
            bd=0
        )
        raw_scroll_y = ttk.Scrollbar(
            raw_frame,
            orient=tk.VERTICAL,
            command=raw_text.yview,
            bootstyle="dark-round"
        )
        raw_scroll_x = ttk.Scrollbar(
            raw_frame,
            orient=tk.HORIZONTAL,
            command=raw_text.xview,
            bootstyle="dark-round"
        )
        raw_text.configure(yscrollcommand=raw_scroll_y.set, xscrollcommand=raw_scroll_x.set)

        raw_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        raw_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        raw_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        # Show all sample data
        import json
        raw_text.insert(tk.END, json.dumps(sample, indent=2))
        raw_text.config(state=tk.DISABLED)

        # Close button
        ttk.Button(
            main,
            text="Close",
            command=win.destroy,
            bootstyle="primary",
            width=15
        ).pack(pady=10)

    def _generate_single_scheme_explanation(self, scheme_name, classification_name, sample):
        """Generate detailed explanation using the scheme's JSON definition (for single scheme mode)"""

        # Strip emojis and clean up scheme name for lookup
        import re
        # Comprehensive emoji pattern
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
            u"\U00002702-\U000027B0"  # dingbats
            u"\U000024C2-\U0001F251"  # enclosed characters
            u"\U0001F900-\U0001F9FF"  # supplemental symbols
            u"\U0001FA70-\U0001FAFF"  # symbols and pictographs extended
            u"\U00002600-\U000026FF"  # miscellaneous symbols
            u"\U00002B50"              # star
            "]+", flags=re.UNICODE)

        clean_scheme_name = emoji_pattern.sub('', scheme_name).strip()

        # Also remove any other common emoji that might appear
        common_emojis = ['✅', '🔬', '🏛', '🌍', '🪐', '🏺', '💎', '⚒', '🌋', '🎯',
                         '📊', '🧱', '🌱', '🪨', '☄️', '⚙️', '📈', '🧪', '🥩', '🦴']
        for emoji in common_emojis:
            clean_scheme_name = clean_scheme_name.replace(emoji, '')
        clean_scheme_name = clean_scheme_name.strip()

        # Determine path to classification schemes
        possible_paths = [
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'engines', 'classification'),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'engines', 'classification'),
            os.path.join(self.app.app_dir, 'engines', 'classification') if hasattr(self.app, 'app_dir') else None,
            os.path.join(os.getcwd(), 'engines', 'classification')
        ]

        schemes_dir = None
        for path in possible_paths:
            if path and os.path.exists(path):
                schemes_dir = path
                break

        if not schemes_dir:
            return self._fallback_single_explanation(sample, classification_name, "Scheme directory not found")

        # Find the matching scheme JSON
        scheme_data = None
        try:
            for filename in os.listdir(schemes_dir):
                if filename.endswith('.json'):
                    with open(os.path.join(schemes_dir, filename), 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if data.get('scheme_name') == clean_scheme_name:
                            scheme_data = data
                            break
        except Exception as e:
            return self._fallback_single_explanation(sample, classification_name, f"Error loading scheme: {str(e)}")

        if not scheme_data:
            return self._fallback_single_explanation(sample, classification_name, f"Scheme data not found")

        # Find the matching classification
        classification = None
        for c in scheme_data.get('classifications', []):
            if c['name'] == classification_name:
                classification = c
                break

        if not classification:
            return self._fallback_single_explanation(sample, classification_name, f"Classification details not found")

        # Build rich explanation (reuse the same formatting logic)
        return self._format_explanation(scheme_data, classification, clean_scheme_name, classification_name, sample)

    def _format_explanation(self, scheme_data, classification, scheme_name, classification_name, sample):
        """Format the explanation text (shared between single and all schemes mode)"""
        lines = []

        # Header
        lines.append("=" * 70)
        lines.append(f"📋 {scheme_name}")
        lines.append(f"🎯 Classification: {classification_name}")
        lines.append("=" * 70)
        lines.append("")

        # Description
        if classification.get('description'):
            lines.append(f"📌 Description: {classification['description']}")
            lines.append("")

        # Rules that triggered
        rules = classification.get('rules', [])
        if rules:
            lines.append("⚖️ Classification Criteria:")
            lines.append("")

            for i, rule in enumerate(rules, 1):
                field = rule.get('field')
                operator = rule.get('operator')

                # Handle nested OR rules
                if operator == 'OR' and 'rules' in rule:
                    lines.append(f"  {i}. One of the following conditions must be true:")
                    for sub_rule in rule['rules']:
                        sub_field = sub_rule.get('field')
                        sub_op = sub_rule.get('operator')
                        sub_val = sub_rule.get('value')

                        # Get sample value
                        sample_val = sample.get(sub_field, 'N/A')
                        if sample_val != 'N/A' and isinstance(sample_val, (int, float)):
                            sample_val = f"{sample_val:.3f}".rstrip('0').rstrip('.')

                        if sub_op == '>':
                            lines.append(f"     • {sub_field} > {sub_val}")
                            lines.append(f"       Your sample: {sample_val}")
                            if self._compare_values(sample, sub_field, '>', sub_val):
                                lines.append(f"       ✓ Condition met")
                            else:
                                lines.append(f"       ✗ Condition not met")
                        elif sub_op == '<':
                            lines.append(f"     • {sub_field} < {sub_val}")
                            lines.append(f"       Your sample: {sample_val}")
                            if self._compare_values(sample, sub_field, '<', sub_val):
                                lines.append(f"       ✓ Condition met")
                            else:
                                lines.append(f"       ✗ Condition not met")
                        elif sub_op == 'between':
                            min_val = sub_rule.get('min')
                            max_val = sub_rule.get('max')
                            lines.append(f"     • {sub_field} between {min_val} and {max_val}")
                            lines.append(f"       Your sample: {sample_val}")
                            if self._compare_values(sample, sub_field, 'between', (min_val, max_val)):
                                lines.append(f"       ✓ Condition met")
                            else:
                                lines.append(f"       ✗ Condition not met")
                    lines.append("")
                    continue

                # Handle regular rules
                sample_val = sample.get(field, 'N/A')
                if sample_val != 'N/A' and isinstance(sample_val, (int, float)):
                    sample_val = f"{sample_val:.3f}".rstrip('0').rstrip('.')

                if operator == '>':
                    threshold = rule.get('value')
                    lines.append(f"  {i}. {field} > {threshold}")
                    lines.append(f"     Your sample: {sample_val}")
                    if self._compare_values(sample, field, '>', threshold):
                        lines.append(f"     ✓ Threshold exceeded")
                        if isinstance(sample.get(field), (int, float)) and isinstance(threshold, (int, float)):
                            diff = sample[field] - threshold
                            lines.append(f"       (by {diff:.3f})")
                    else:
                        lines.append(f"     ✗ Threshold not met")

                elif operator == '<':
                    threshold = rule.get('value')
                    lines.append(f"  {i}. {field} < {threshold}")
                    lines.append(f"     Your sample: {sample_val}")
                    if self._compare_values(sample, field, '<', threshold):
                        lines.append(f"     ✓ Below threshold")
                        if isinstance(sample.get(field), (int, float)) and isinstance(threshold, (int, float)):
                            diff = threshold - sample[field]
                            lines.append(f"       (by {diff:.3f})")
                    else:
                        lines.append(f"     ✗ Threshold not met")

                elif operator == 'between':
                    min_val = rule.get('min')
                    max_val = rule.get('max')
                    lines.append(f"  {i}. {field} between {min_val} and {max_val}")
                    lines.append(f"     Your sample: {sample_val}")
                    if self._compare_values(sample, field, 'between', (min_val, max_val)):
                        lines.append(f"     ✓ Within range")
                    else:
                        lines.append(f"     ✗ Outside range")

                elif operator == '=':
                    threshold = rule.get('value')
                    lines.append(f"  {i}. {field} = {threshold}")
                    lines.append(f"     Your sample: {sample_val}")
                    if self._compare_values(sample, field, '=', threshold):
                        lines.append(f"     ✓ Matches exactly")
                    else:
                        lines.append(f"     ✗ Does not match")

                lines.append("")

        # Priority/confidence info
        if 'priority' in classification:
            lines.append(f"📊 Priority: {classification['priority']}")
        if 'confidence_score' in classification:
            lines.append(f"📈 Base confidence: {classification['confidence_score']}")

        lines.append("")
        lines.append("=" * 70)

        # References
        if scheme_data.get('reference'):
            lines.append(f"📚 **Reference:** {scheme_data['reference']}")
        if scheme_data.get('author'):
            lines.append(f"👤 **Author:** {scheme_data['author']}")
        if scheme_data.get('date_created'):
            lines.append(f"📅 **Date:** {scheme_data['date_created']}")

        lines.append("=" * 70)

        return "\n".join(lines)

    def _fallback_single_explanation(self, sample, classification, error_msg=None):
        """Fallback explanation if JSON loading fails (for single scheme mode)"""
        lines = []
        lines.append(f"Classification: {classification}")
        lines.append("")
        lines.append("=" * 50)
        lines.append("")

        if error_msg:
            lines.append(f"⚠️ {error_msg}")
            lines.append("")
            lines.append("Showing available geochemical data instead:")
            lines.append("")

        # Show relevant geochemical data
        lines.append("📊 Geochemical Values:")
        relevant = ['Zr_ppm', 'Nb_ppm', 'Ba_ppm', 'Rb_ppm', 'Cr_ppm', 'Ni_ppm',
                   'SiO2_wt', 'TiO2_wt', 'Al2O3_wt', 'Fe2O3_T_wt', 'CaO_wt', 'MgO_wt',
                   'K2O_wt', 'Na2O_wt', 'P2O5_wt']

        found = False
        for key in relevant:
            if key in sample and sample[key]:
                val = sample[key]
                if isinstance(val, (int, float)):
                    val = f"{val:.3f}".rstrip('0').rstrip('.')
                lines.append(f"  {key}: {val}")
                found = True

        if not found:
            # Show all available numeric fields
            for key, val in sample.items():
                if isinstance(val, (int, float)) and val not in (None, ''):
                    lines.append(f"  {key}: {val:.3f}")

        lines.append("")
        lines.append("=" * 50)

        return "\n".join(lines)

    def _compare_values(self, sample, field, operator, threshold):
        """Compare sample value against threshold"""
        if field not in sample:
            return False

        sample_val = sample[field]
        if sample_val in (None, '', 'N/A'):
            return False

        try:
            sample_val = float(sample_val)

            if operator == '>':
                return sample_val > float(threshold)
            elif operator == '<':
                return sample_val < float(threshold)
            elif operator == 'between':
                min_val, max_val = threshold
                return float(min_val) <= sample_val <= float(max_val)
            elif operator == '=':
                return abs(sample_val - float(threshold)) < 0.0001
        except (ValueError, TypeError):
            return False

        return False

    def _show_context_menu(self, event):
        """Show right-click context menu with correct sample index"""
        item = self.tree.identify_row(event.y)
        if not item:
            return
        self.tree.selection_set(item)

        # Extract original index from the item's iid (set in _refresh)
        if item.startswith('row_'):
            try:
                sample_idx = int(item.split('_')[1])
            except (ValueError, IndexError):
                return
        else:
            # Fallback (should not happen, but kept for safety)
            item_idx = self.tree.index(item)
            sample_idx = self.current_page * self.page_size + item_idx

        sample = self.app.data_hub.get_all()[sample_idx]
        clicked_col = self.tree.identify_column(event.x)

        menu = tk.Menu(self.tree, tearoff=0)
        menu.add_command(label="🔍 Classify This Sample",
                        command=lambda: self._classify_selected_sample(sample_idx))
        menu.add_command(label="Edit Cell",
                        command=lambda: self._edit_selected_cell(event, item, sample_idx))
        menu.add_separator()
        menu.add_command(label="Copy Value", command=lambda: self._copy_cell_value(item, clicked_col))
        menu.add_command(label="Copy Row", command=lambda: self._copy_row(sample))
        menu.add_separator()
        menu.add_command(label="Delete Row", command=lambda: self._delete_row(sample_idx))

        menu.tk_popup(event.x_root, event.y_root)
        return "break"

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
        entry = ttk.Entry(self.tree, bootstyle="light")
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

    def _copy_cell_value(self, item, column="#2"):
        """Copy the value of the right-clicked cell to the clipboard."""
        values = self.tree.item(item, "values")
        if not values:
            return
        try:
            col_idx = int(column[1:]) - 1  # "#3" → 2
            if 0 <= col_idx < len(values):
                self.tree.clipboard_clear()
                self.tree.clipboard_append(str(values[col_idx]))
        except (ValueError, IndexError):
            pass

    def _copy_row(self, sample):
        import json
        text = json.dumps(sample, indent=2)
        self.tree.clipboard_clear()
        self.tree.clipboard_append(text)

    def _delete_row(self, sample_idx):
        if messagebox.askyesno("Confirm Delete", "Delete this row?"):
            self.app.data_hub.delete_rows([sample_idx])

    def show_classification_status(self, scheme_name, total_samples, classified_count, classification_counts):
        self.last_classification_details = {
            'scheme': scheme_name,
            'total': total_samples,
            'classified': classified_count,
            'breakdown': classification_counts
        }

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
            counter = Counter(classification_counts)
            top_classes = counter.most_common(3)
            summary_parts = []
            for class_name, count in top_classes:
                short_name = class_name[:20] + "..." if len(class_name) > 20 else class_name
                summary_parts.append(f"{short_name}: {count}")

            if len(counter) > 3:
                summary_parts.append(f"+{len(counter)-3} more")

            summary = " | ".join(summary_parts)
            self.status_var.set(f"✅ {classified_count}/{total_samples} classified: {summary} (click for details)")

        self.app.root.update_idletasks()

    def set_status(self, message, message_type="info"):
        icon = self.STATUS_ICONS.get(message_type, "ℹ️")

        if message_type not in ["success"] or "classified" not in message.lower():
            self.last_classification_details = None
            self.last_console_output = None

        self.status_var.set(f"{icon} {message}")
        self.app.root.update_idletasks()

    def clear_status(self):
        self.status_var.set("Ready")

    def show_progress(self, operation, current=None, total=None, message=""):
        icon = self.STATUS_ICONS.get(operation, "🔄")

        if current is not None and total is not None and total > 0:
            percentage = (current / total) * 100
            bar_length = 20
            filled = int(bar_length * current // total)
            bar = "█" * filled + "░" * (bar_length - filled)
            status = f"{icon} {operation.title()}: [{bar}] {current}/{total} ({percentage:.1f}%)"
            if message:
                status += f" - {message}"
        else:
            if message:
                status = f"{icon} {message}"
            else:
                status = f"{icon} {operation.title()} in progress..."

        self.status_var.set(status)
        self.last_operation = {
            'type': operation, 'current': current, 'total': total,
            'message': message, 'icon': icon
        }
        self.app.root.update_idletasks()

    def show_operation_complete(self, operation, details=""):
        icon = self.STATUS_ICONS.get(operation, "✅")

        if details:
            status = f"{icon} {operation.title()} complete: {details}"
        else:
            status = f"{icon} {operation.title()} complete"

        self.status_var.set(status)
        self.last_operation = {'type': operation, 'complete': True, 'details': details}
        self.app.root.update_idletasks()
        self.app.root.after(5000, self._clear_if_complete)

    def _clear_if_complete(self):
        current = self.status_var.get()
        if "complete" in current.lower() or "✅" in current:
            self.clear_status()

    def show_error(self, operation, error_message):
        self.status_var.set(f"❌ {operation} failed: {error_message[:50]}...")
        self.last_operation = {'type': operation, 'error': error_message}
        self.app.root.update_idletasks()

    def show_warning(self, operation, warning_message):
        self.status_var.set(f"⚠️ {operation}: {warning_message[:50]}...")
        self.last_operation = {'type': operation, 'warning': warning_message}
        self.app.root.update_idletasks()

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

    def update_plot_types(self, plot_types):
        self.plot_types = plot_types
        if plot_types:
            values = [name for name, func in plot_types]
            self.plot_type_combo['values'] = values
            if values:
                self.plot_type_combo.set("")
                for widget in self.plot_area.winfo_children():
                    widget.destroy()
                placeholder = ttk.Label(
                    self.plot_area,
                    text="Select a plot type from the dropdown above",
                    font=("Arial", 12),
                    bootstyle="secondary"
                )
                placeholder.pack(expand=True)
                self.plot_placeholder = placeholder

    def _load_plotter_ui(self, event=None):
        if not self.plot_types or not self.plot_type_var.get():
            return
        selected = self.plot_type_var.get()
        plot_func = next((func for name, func in self.plot_types if name == selected), None)
        if plot_func:
            for widget in self.plot_area.winfo_children():
                widget.destroy()
            samples = self.app.data_hub.get_page(self.current_page, self.page_size)
            try:
                plot_func(self.plot_area, samples)
            except Exception as e:
                error_label = ttk.Label(
                    self.plot_area,
                    text=f"Error loading plotter: {e}",
                    bootstyle="danger"
                )
                error_label.pack(expand=True)
                import traceback
                traceback.print_exc()

    def _generate_plot(self):
        if not self.plot_types or not self.plot_type_var.get():
            return
        selected = self.plot_type_var.get()
        plot_func = next((func for name, func in self.plot_types if name == selected), None)
        if plot_func:
            samples = self.app.data_hub.get_page(self.current_page, self.page_size)
            for widget in self.plot_area.winfo_children():
                widget.destroy()
            try:
                plot_func(self.plot_area, samples)
            except Exception as e:
                error_label = ttk.Label(
                    self.plot_area,
                    text=f"Plot error: {e}",
                    bootstyle="danger"
                )
                error_label.pack(expand=True)
