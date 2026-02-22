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

class CenterPanel:
    def __init__(self, parent, app):
        self.app = app
        self.frame = ttk.Frame(parent, bootstyle="dark")

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
        self.console_plugins = []
        self.console_tab_created = False
        self._is_syncing_scroll = False

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        self.last_classification_summary = ""
        self.last_operation = {'type': 'none'}
        self.last_classification_details = None

        self._build_ui()

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
        self.tree.bind("<Button-1>", self._on_click)
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Button-3>", self._show_context_menu)
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
        """Refresh table - fixed columns first, then chemical data"""
        if not self.tree:
            return

        samples = self.app.data_hub.get_page(self.current_page, self.page_size)
        total = self.app.data_hub.row_count()
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
        remaining = sorted([col for col in all_columns
                            if col not in final_cols
                            and col not in ["☐", "Display_Color", "Auto_Classification_Color"]])
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
            actual_idx = self.current_page * self.page_size + i
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

            # Determine tag for this row
            if hasattr(self.app.right, 'all_mode') and self.app.right.all_mode:
                all_results = getattr(self.app.right, 'all_results', None)
                if all_results and actual_idx < len(all_results) and all_results[actual_idx] is not None:
                    best_class = "UNCLASSIFIED"
                    best_conf = 0.0
                    for r in all_results[actual_idx]:
                        if r[1] not in ['UNCLASSIFIED', 'INVALID_SAMPLE', 'SCHEME_NOT_FOUND', '']:
                            if r[2] > best_conf:
                                best_class = r[1]
                                best_conf = r[2]
                    tag = best_class
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

            self.tree.insert("", tk.END, values=tuple(values), tags=(tag,))

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
        for col in columns:
            if col == "☐":
                tree.column(col, width=30, minwidth=30)
                continue

            header_text = self._get_display_name(col)
            max_width = len(header_text) * 8

            for item in tree.get_children()[:50]:
                values = tree.item(item, "values")
                col_idx = columns.index(col)
                if col_idx < len(values):
                    text = str(values[col_idx])
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
        self._refresh()

    def _clear_filter(self):
        self.search_var.set("")
        self.filter_var.set("All")
        self._refresh()

    def _reset_column_widths(self):
        if hasattr(self.tree, '_columns_manually_sized'):
            self.tree._columns_manually_sized = False
        samples = self.app.data_hub.get_page(self.current_page, self.page_size)
        if samples:
            self.app.auto_size_columns(self.tree, samples, force=True)

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
            if hasattr(self.app.right, 'classification_results') and sample_idx < len(self.app.right.classification_results):
                result = self.app.right.classification_results[sample_idx]
                if result:
                    classification = result.get('classification', 'UNCLASSIFIED')
                    confidence = result.get('confidence', 0.0)
                    color = result.get('color', '#A9A9A9')
                    derived = result.get('derived_fields', {})
                    flag = result.get('flag_for_review', False)
                    self._show_classification_explanation(
                        sample, classification, confidence, color, derived, flag
                    )
                    return
            self._show_classification_explanation(sample)

    def _show_classification_explanation(self, sample, classification=None, confidence=None, color=None, derived=None, flag=False):
        win = ttk.Toplevel(self.app.root)
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
                 font=("Arial", 14, "bold"), bootstyle="light").pack(pady=5)

        if classification is None:
            classification = (sample.get('Final_Classification') or
                              sample.get('Auto_Classification') or
                              sample.get('Classification') or
                              "UNCLASSIFIED")
        if confidence is None:
            confidence = sample.get('Auto_Confidence', 'N/A')
        if color is None:
            color = '#A9A9A9'

        class_frame = ttk.Frame(main)
        class_frame.pack(fill=tk.X, pady=10)
        ttk.Label(class_frame, text="Classification:", font=("Arial", 11, "bold"), bootstyle="light").pack(side=tk.LEFT)
        fg_color = self.app.color_manager.get_foreground(classification)
        ttk.Label(class_frame, text=classification, font=("Arial", 11),
                 foreground=fg_color, bootstyle="light").pack(side=tk.LEFT, padx=10)
        ttk.Label(class_frame, text=f"Confidence: {confidence}",
                 font=("Arial", 10), bootstyle="light").pack(side=tk.RIGHT)

        ttk.Separator(main, orient=tk.HORIZONTAL, bootstyle="secondary").pack(fill=tk.X, pady=10)
        ttk.Label(main, text="Geochemical Data:", font=("Arial", 11, "bold"), bootstyle="light").pack(anchor=tk.W)

        data_frame = ttk.Frame(main)
        data_frame.pack(fill=tk.X, pady=5)

        elements = ['Zr_ppm', 'Nb_ppm', 'Ba_ppm', 'Rb_ppm', 'Cr_ppm', 'Ni_ppm']
        ratios = ['Zr_Nb_Ratio', 'Cr_Ni_Ratio', 'Ba_Rb_Ratio']

        row = 0
        for elem in elements:
            if elem in sample and sample[elem]:
                val = sample[elem]
                if val:
                    ttk.Label(data_frame, text=f"{elem}:", font=("Arial", 9), bootstyle="light").grid(
                        row=row, column=0, sticky=tk.W, padx=5, pady=2)
                    ttk.Label(data_frame, text=str(val), font=("Arial", 9), bootstyle="light").grid(
                        row=row, column=1, sticky=tk.W, padx=5, pady=2)
                    row += 1

        for ratio in ratios:
            if ratio in sample and sample[ratio]:
                val = sample[ratio]
                if val:
                    ttk.Label(data_frame, text=f"{ratio}:", font=("Arial", 9), bootstyle="light").grid(
                        row=row, column=0, sticky=tk.W, padx=5, pady=2)
                    try:
                        display_val = f"{float(val):.2f}"
                    except:
                        display_val = str(val)
                    ttk.Label(data_frame, text=display_val, font=("Arial", 9), bootstyle="light").grid(
                        row=row, column=1, sticky=tk.W, padx=5, pady=2)
                    row += 1

        ttk.Separator(main, orient=tk.HORIZONTAL, bootstyle="secondary").pack(fill=tk.X, pady=10)
        ttk.Label(main, text="Classification Logic:", font=("Arial", 11, "bold"), bootstyle="light").pack(anchor=tk.W, pady=5)

        text_frame = ttk.Frame(main)
        text_frame.pack(fill=tk.BOTH, expand=True)

        style = ttk.Style.get_instance()
        bg = style.colors.get('dark') if hasattr(style, 'colors') else "#2b2b2b"
        fg = style.colors.get('light') if hasattr(style, 'colors') else "#dddddd"
        text_widget = tk.Text(text_frame, wrap=tk.WORD, font=("TkDefaultFont", 10), height=10,
                              bg=bg, fg=fg, insertbackground=fg, relief=tk.FLAT, bd=0)
        scrollbar = ttk.Scrollbar(text_frame, command=text_widget.yview, bootstyle="dark-round")
        text_widget.configure(yscrollcommand=scrollbar.set)

        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        explanation = self._generate_classification_explanation(sample, classification)
        text_widget.insert(tk.END, explanation)
        text_widget.config(state=tk.DISABLED)

        ttk.Button(main, text="Close", command=win.destroy, bootstyle="primary").pack(pady=10)

    def _generate_classification_explanation(self, sample, classification):
        lines = []
        lines.append(f"This sample was classified as: {classification}\n")
        lines.append("\n📊 Data values:")

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

    def _classify_selected_sample(self, sample_idx):
        print(f"\n🔍 CLASSIFY SELECTED SAMPLE - Index: {sample_idx}")

        samples = self.app.data_hub.get_all()
        if sample_idx >= len(samples):
            print(f"❌ Sample index {sample_idx} out of range (max: {len(samples)-1})")
            return

        sample = samples[sample_idx]
        print(f"📋 Sample ID: {sample.get('Sample_ID', 'Unknown')}")

        if not hasattr(self.app, 'right') or not hasattr(self.app.right, 'scheme_var'):
            messagebox.showerror("Error", "Right panel not available")
            return

        display_name = self.app.right.scheme_var.get()
        print(f"🎯 Selected scheme display name: '{display_name}'")

        if not display_name:
            messagebox.showinfo("No Scheme", "Please select a classification scheme first")
            return

        scheme_id = None
        if hasattr(self.app.right, 'schemes'):
            for sid, info in self.app.right.schemes.items():
                if info.get('name') == display_name or info.get('scheme_name') == display_name:
                    scheme_id = sid
                    break

        if not scheme_id and self.app.classification_engine:
            for sid, scheme in self.app.classification_engine.schemes.items():
                if scheme.get('scheme_name') == display_name:
                    scheme_id = sid
                    break

        if not scheme_id:
            import re
            clean_name = re.sub(r'[✅🔬🏛🌍🪐🏺💎⚒🌋🎯]', '', display_name).strip()
            if self.app.classification_engine:
                for sid, scheme in self.app.classification_engine.schemes.items():
                    scheme_clean = re.sub(r'[✅🔬🏛🌍🪐🏺💎⚒🌋🎯]', '', scheme.get('scheme_name', '')).strip()
                    if scheme_clean == clean_name:
                        scheme_id = sid
                        break

        if not scheme_id:
            print(f"❌ Could not find scheme ID for '{display_name}'")
            messagebox.showerror("Error", f"Could not find scheme ID for '{display_name}'")
            return

        if self.app.classification_engine:
            try:
                print(f"🚀 Running classification with scheme: {scheme_id}")

                classification, confidence, color, derived = self.app.classification_engine.classify_sample(sample, scheme_id)
                print(f"✅ Classification result: {classification}")
                print(f"   Confidence: {confidence}")
                print(f"   Color: {color}")
                print(f"   Derived: {derived}")

                scheme_info = self.app.classification_engine.get_scheme_info(scheme_id)
                flag_uncertain = scheme_info.get('flag_uncertain', False)
                uncertain_threshold = scheme_info.get('uncertain_threshold', 0.7)
                flag = (confidence < uncertain_threshold) if flag_uncertain else False

                self._show_classification_explanation(
                    sample, classification, confidence, color, derived, flag
                )

                if hasattr(self.app.right, 'classification_results') and sample_idx < len(self.app.right.classification_results):
                    result = {
                        'classification': classification,
                        'confidence': confidence,
                        'color': color,
                        'derived_fields': derived,
                        'flag_for_review': flag
                    }
                    self.app.right.classification_results[sample_idx] = result
                    self.app.right._update_hud()

                self._refresh()
                self.set_status(f"✅ Classified as: {classification}", "success")

            except Exception as e:
                print(f"❌ Classification error: {e}")
                import traceback
                traceback.print_exc()
                messagebox.showerror("Error", f"Classification failed: {e}")
        else:
            print(f"❌ Classification engine not available")
            messagebox.showerror("Error", "Classification engine not available")

    def _show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        self.tree.selection_set(item)

        item_idx = self.tree.index(item)
        sample_idx = self.current_page * self.page_size + item_idx
        sample = self.app.data_hub.get_all()[sample_idx]

        menu = tk.Menu(self.tree, tearoff=0)
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
        icons = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
            "processing": "🔄"
        }
        icon = icons.get(message_type, "ℹ️")

        if message_type not in ["success"] or "classified" not in message.lower():
            self.last_classification_details = None
            self.last_console_output = None

        self.status_var.set(f"{icon} {message}")
        self.app.root.update_idletasks()

    def clear_status(self):
        self.status_var.set("Ready")

    def show_progress(self, operation, current=None, total=None, message=""):
        icons = {
            "import": "📥", "export": "📤", "classification": "🔬",
            "save": "💾", "load": "📂", "delete": "🗑️",
            "filter": "🔍", "plot": "📈", "macro": "🎬",
            "plugin": "🔌", "processing": "🔄", "complete": "✅",
            "error": "❌", "warning": "⚠️"
        }
        icon = icons.get(operation, "🔄")

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
        icons = {
            "import": "📥", "export": "📤", "classification": "🔬",
            "save": "💾", "load": "📂", "delete": "🗑️",
            "filter": "🔍", "plot": "📈", "macro": "🎬", "plugin": "🔌"
        }
        icon = icons.get(operation, "✅")

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
