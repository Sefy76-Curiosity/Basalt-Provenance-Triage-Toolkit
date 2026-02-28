"""
Right Panel - 10% width, Classification Hub
Redesigned with compact top controls and full-height HUD
Now supports "Run All Schemes" via dropdown option.
Fully converted to ttkbootstrap
"""

import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from collections import Counter
import json
from pathlib import Path
from .all_schemes_detail_dialog import AllSchemesDetailDialog

class RightPanel:
    def __init__(self, parent, app):
        self.app = app
        self.frame = ttk.Frame(parent, bootstyle="dark")

        # UI elements (will be created in _build_ui)
        self.hud_tree = None

        # HUD sort state
        self.hud_headings = {
            "ID": "ID",
            "Class": "Classification",
            "Conf": "Conf",
            "Flag": "🚩"
        }
        self.hud_sort_column = None
        self.hud_sort_reverse = False

        self.scheme_var = tk.StringVar()
        self.protocol_var = tk.StringVar()
        self.run_target = tk.StringVar(value="all")
        self.scheme_list = []
        self.protocol_list = []
        self.sorted_indices = None
        self.is_sorted = False
        self.classification_results = []

        self.all_results = None
        self.all_derived_fields = None
        self.all_mode = False
        self.all_schemes_list = []

        # Build the UI
        self._build_ui()
        self.hud_tree.bind("<Button-1>", self._on_hud_header_click)
        self._refresh_results_cache()

    def _on_hud_header_click(self, event):
        region = self.hud_tree.identify("region", event.x, event.y)
        if region == "heading":
            column = self.hud_tree.identify_column(event.x)
            col_index = int(column[1:]) - 1
            col_name = list(self.hud_headings.keys())[col_index]
            self._sort_by_hud_column(col_name)

    def _sort_by_hud_column(self, col_name):
        if self.hud_sort_column == col_name:
            self.hud_sort_reverse = not self.hud_sort_reverse
        else:
            self.hud_sort_column = col_name
            self.hud_sort_reverse = False

        all_samples = self.app.data_hub.get_all()
        if not all_samples:
            return

        total = len(all_samples)

        def get_key(idx):
            sample = all_samples[idx]

            if col_name == "ID":
                return sample.get('Sample_ID', '')

            elif col_name == "Class":
                if self.all_mode and self.all_results and self.all_results[idx]:
                    best_class = "UNCLASSIFIED"
                    best_conf = -1.0
                    for _, cls, conf in self.all_results[idx]:
                        if cls not in ['UNCLASSIFIED','INVALID_SAMPLE','SCHEME_NOT_FOUND','']:
                            if conf > best_conf:
                                best_class = cls
                                best_conf = conf
                    return best_class
                else:
                    if idx < len(self.classification_results) and self.classification_results[idx]:
                        return self.classification_results[idx].get('classification', 'UNCLASSIFIED')
                    return 'UNCLASSIFIED'

            elif col_name == "Conf":
                if self.all_mode and self.all_results and self.all_results[idx]:
                    best_conf = 0.0
                    for _, cls, conf in self.all_results[idx]:
                        if cls not in ['UNCLASSIFIED','INVALID_SAMPLE','SCHEME_NOT_FOUND','']:
                            best_conf = max(best_conf, conf)
                    return best_conf
                else:
                    if idx < len(self.classification_results) and self.classification_results[idx]:
                        return self.classification_results[idx].get('confidence', 0.0)
                    return 0.0

            elif col_name == "Flag":
                if self.all_mode and self.all_results and self.all_results[idx]:
                    match_count = sum(1 for _, cls, _ in self.all_results[idx]
                                    if cls not in ['UNCLASSIFIED','INVALID_SAMPLE','SCHEME_NOT_FOUND',''])
                    return match_count
                else:
                    if idx < len(self.classification_results) and self.classification_results[idx]:
                        return 1 if self.classification_results[idx].get('flag_for_review', False) else 0
                    return 0

        indexed = list(range(total))
        indexed.sort(key=get_key, reverse=self.hud_sort_reverse)

        self.app.center.sorted_indices = indexed
        self.app.center.sort_column = None
        self.app.center.sort_reverse = False
        self.app.center._update_header_indicators()
        self.app.center._refresh()

        self._update_hud()
        self._update_hud_header_indicators()

    def _update_hud_header_indicators(self):
        for i, col_name in enumerate(self.hud_headings.keys(), start=1):
            base = self.hud_headings[col_name]
            if col_name == self.hud_sort_column:
                arrow = " ↑" if not self.hud_sort_reverse else " ↓"
                self.hud_tree.heading(f"#{i}", text=base + arrow)
            else:
                self.hud_tree.heading(f"#{i}", text=base)

    def _build_ui(self):
        """Build right panel with compact top and full-height HUD"""
        # ============ ENGINE FRAME ============
        self.engine_frame = ttk.Frame(self.frame, bootstyle="dark")
        self.engine_frame.pack(fill=tk.X, padx=1, pady=1)

        self.refresh_for_engine(getattr(self.app, 'current_engine_name', 'classification'))

        # ============ RUN OPTIONS ============
        self.row2_frame = ttk.Frame(self.frame, bootstyle="dark")
        self.row2_frame.pack(fill=tk.X, padx=1, pady=1)

        self.all_rows_radio = ttk.Radiobutton(
            self.row2_frame,
            text="All Rows",
            variable=self.run_target,
            value="all",
            bootstyle="primary-toolbutton"
        )
        self.all_rows_radio.pack(side=tk.LEFT, padx=2)

        self.selected_radio = ttk.Radiobutton(
            self.row2_frame,
            text="Selected",
            variable=self.run_target,
            value="selected",
            bootstyle="primary-toolbutton"
        )
        self.selected_radio.pack(side=tk.LEFT, padx=2)

        # ============ HUD ============
        self.hud_frame = ttk.Frame(self.frame, bootstyle="dark")
        self.hud_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        tree_frame = ttk.Frame(self.hud_frame, bootstyle="dark")
        tree_frame.pack(fill=tk.BOTH, expand=True)

        self.hud_tree = ttk.Treeview(
            tree_frame,
            columns=("ID", "Class", "Conf", "Flag"),
            show='headings',
            height=1,
            bootstyle="dark"
        )

        self.hud_tree.heading("ID", text="ID")
        self.hud_tree.heading("Class", text="Classification")
        self.hud_tree.heading("Conf", text="Conf")
        self.hud_tree.heading("Flag", text="🚩")

        self.hud_tree.column("ID", width=60, anchor="center")
        self.hud_tree.column("Class", width=150, anchor="w")
        self.hud_tree.column("Conf", width=45, anchor="center")
        self.hud_tree.column("Flag", width=30, anchor="center")

        vsb = ttk.Scrollbar(
            tree_frame,
            orient="vertical",
            command=self._on_hud_scroll,
            bootstyle="dark-round"
        )
        hsb = ttk.Scrollbar(
            tree_frame,
            orient="horizontal",
            command=self.hud_tree.xview,
            bootstyle="dark-round"
        )
        self.hud_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.hud_tree.bind("<MouseWheel>", self._on_hud_mousewheel)
        self.hud_tree.bind("<Button-4>", self._on_hud_mousewheel)
        self.hud_tree.bind("<Button-5>", self._on_hud_mousewheel)
        self.hud_tree.bind("<Double-1>", self._on_hud_double_click)

        self.hud_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        self._configure_hud_colors()

    def update_hud_with_sort(self, sorted_indices, is_sorted):
        self.sorted_indices = sorted_indices
        self.is_sorted = is_sorted

        self.hud_sort_column = None
        self.hud_sort_reverse = False
        self._update_hud_header_indicators()
        self._update_hud()

    # ============ ENGINE SWITCHING ============

    def refresh_for_engine(self, engine_type):
        """Switch UI based on engine type"""
        for widget in self.engine_frame.winfo_children():
            widget.destroy()

        if engine_type == 'protocol':
            self.protocol_combo = ttk.Combobox(
                self.engine_frame,
                textvariable=self.protocol_var,
                state="readonly",
                width=15,
                bootstyle="light"
            )
            self.protocol_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))

            self.run_protocol_btn = ttk.Button(
                self.engine_frame,
                text="Run",
                width=6,
                command=self._run_protocol,
                bootstyle="primary"
            )
            self.run_protocol_btn.pack(side=tk.RIGHT)

            self._refresh_protocols()
        else:
            self.scheme_combo = ttk.Combobox(
                self.engine_frame,
                textvariable=self.scheme_var,
                state="readonly",
                width=15,
                bootstyle="light"
            )
            self.scheme_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))

            self.apply_btn = ttk.Button(
                self.engine_frame,
                text="Apply",
                width=6,
                command=self._run_classification,
                bootstyle="primary"
            )
            self.apply_btn.pack(side=tk.RIGHT)

            self._refresh_schemes()

    def _refresh_protocols(self):
        """Refresh protocol dropdown"""
        if not hasattr(self.app, 'protocol_engine') or self.app.protocol_engine is None:
            self.protocol_combo['values'] = ["⚠️ Protocol engine not found"]
            self.protocol_combo.set("⚠️ Protocol engine not found")
            return

        try:
            self.protocol_list = []
            protocol_items = []

            for pid, protocol_data in self.app.protocol_engine.protocols.items():
                display_name = protocol_data.get('protocol_name', protocol_data.get('name', pid))
                icon = protocol_data.get('icon', '📋')
                display = f"{icon} {display_name}"
                self.protocol_list.append((display, pid))
                protocol_items.append(display)

            self.protocol_list.sort(key=lambda x: x[0])

            if protocol_items:
                self.protocol_combo['values'] = [p[0] for p in self.protocol_list]
                self.protocol_combo.current(0)
            else:
                self.protocol_combo['values'] = ["No protocols found"]
                self.protocol_combo.set("No protocols found")

        except Exception as e:
            self.protocol_combo['values'] = ["Error loading protocols"]
            self.protocol_combo.set("Error loading protocols")

    def _run_protocol(self):
        """Run selected protocol"""
        messagebox.showinfo("Protocol", "Protocol engine not fully implemented")

    # ============ SCROLL SYNC ============

    def _sync_center_scroll(self):
        """Sync center table scroll position to match HUD."""
        center = getattr(self.app, 'center', None)
        if not center:
            return
        first, _ = self.hud_tree.yview()
        center._is_syncing_scroll = True
        center.tree.yview_moveto(first)
        center._is_syncing_scroll = False

    def _on_hud_scroll(self, *args):
        """Sync HUD scroll with main table."""
        center = getattr(self.app, 'center', None)
        if center and getattr(center, '_is_syncing_scroll', False):
            return
        self.hud_tree.yview(*args)
        self._sync_center_scroll()

    def _on_hud_mousewheel(self, event):
        """Handle mouse wheel on HUD."""
        center = getattr(self.app, 'center', None)
        if center and getattr(center, '_is_syncing_scroll', False):
            return
        if event.delta:
            self.hud_tree.yview_scroll(int(-1 * (event.delta / 120)), "units")
        elif event.num == 4:
            self.hud_tree.yview_scroll(-1, "units")
        elif event.num == 5:
            self.hud_tree.yview_scroll(1, "units")
        self._sync_center_scroll()
        return "break"

    # ============ COLORS ============

    def _configure_hud_colors(self):
        """Configure HUD colors from color manager"""
        configured_tags = set()
        for classification in self.app.color_manager.get_all_classifications():
            bg_color = self.app.color_manager.get_background(classification)
            fg_color = self.app.color_manager.get_foreground(classification)

            if classification not in configured_tags:
                self.hud_tree.tag_configure(
                    classification,
                    background=bg_color,
                    foreground=fg_color
                )
                configured_tags.add(classification)

            upper = classification.upper()
            if upper not in configured_tags:
                self.hud_tree.tag_configure(
                    upper,
                    background=bg_color,
                    foreground=fg_color
                )
                configured_tags.add(upper)

        self.hud_tree.tag_configure('UNCLASSIFIED', background='#3b3b3b', foreground='white')

    # ============ DOUBLE CLICK ============

    def _open_sample_detail(self, sample_idx, samples=None):
        """Open the appropriate detail dialog for a given sample index."""
        if samples is None:
            samples = self.app.data_hub.get_all()
        if sample_idx >= len(samples):
            return
        if self.all_mode and self.all_results is not None:
            AllSchemesDetailDialog(self.app.root, self.app, samples, self.all_results, sample_idx, self.all_schemes_list)
            return
        if sample_idx < len(self.classification_results):
            result = self.classification_results[sample_idx]
            if result:
                classification = result.get('classification', 'UNCLASSIFIED')
                confidence = result.get('confidence', 0.0)
                color = result.get('color', '#A9A9A9')
                derived = result.get('derived_fields', {})
                flag = result.get('flag_for_review', False)
                self.app.center._show_classification_explanation(
                    samples[sample_idx], classification, confidence, color, derived, flag
                )
                return
        self.app.center._show_classification_explanation(samples[sample_idx])

    def _on_hud_double_click(self, event):
        """Show appropriate detail dialog based on mode."""
        item = self.hud_tree.identify_row(event.y)
        if not item:
            return

        values = self.hud_tree.item(item, "values")
        if not values or len(values) < 1:
            return

        short_id = values[0]
        samples = self.app.data_hub.get_all()
        target_idx = None

        for idx, sample in enumerate(samples):
            full_id = sample.get('Sample_ID', '')
            if full_id.endswith(short_id) or full_id == short_id:
                target_idx = idx
                break

        if target_idx is None:
            return

        if self.all_mode and self.all_results is not None:
            from ui.all_schemes_detail_dialog import AllSchemesDetailDialog
            AllSchemesDetailDialog(
                self.app.root,
                self.app,
                samples,
                self.all_results,
                target_idx,
                self.all_schemes_list,
                all_derived=self.all_derived_fields
            )
            return

        self._open_sample_detail(target_idx, samples)
        return "break"

    # ============ SCHEMES ============

    def _refresh_schemes(self):
        """Refresh scheme dropdown from classification engine, adding a "Run All" option."""
        if getattr(self.app, 'current_engine_name', 'classification') == 'protocol':
            return

        if not hasattr(self.app, 'classification_engine') or self.app.classification_engine is None:
            self.scheme_combo['values'] = ["No engine"]
            self.scheme_combo.set("No engine")
            return

        try:
            all_schemes = self.app.classification_engine.get_available_schemes()
            disabled = self._load_disabled_schemes()
            schemes = [s for s in all_schemes if s['id'] not in disabled]

            self.scheme_list = []
            self.all_schemes_list = ["🔁 Run All Schemes"]

            self.scheme_list.append(("🔁 Run All Schemes", "__ALL__"))

            normal_schemes = []
            for scheme in schemes:
                display = f"{scheme.get('icon', '📊')} {scheme['name']}"
                normal_schemes.append((display, scheme['id']))
                self.all_schemes_list.append(display)

            normal_schemes.sort(key=lambda x: x[0].split(' ', 1)[-1].lower())
            self.scheme_list.extend(normal_schemes)

            if self.scheme_list:
                self.scheme_combo['values'] = [s[0] for s in self.scheme_list]
                self.scheme_combo.current(0)
            else:
                self.scheme_combo['values'] = ["No schemes"]
                self.scheme_combo.set("No schemes")
        except Exception as e:
            self.scheme_combo['values'] = ["No schemes"]
            self.scheme_combo.set("No schemes")

    def _load_disabled_schemes(self):
        """Return set of disabled scheme ids from config/disabled_schemes.json."""
        config = Path("config/disabled_schemes.json")
        if config.exists():
            try:
                with open(config, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return set(data) if isinstance(data, list) else set()
            except Exception:
                pass
        return set()

    # ============ DATA OBSERVER ============

    def on_data_changed(self, event, *args):
        """When data changes, reset all caches and refresh HUD."""
        self._refresh_results_cache()
        self.all_results = None
        self.all_mode = False
        self._update_hud()

        samples = self.app.data_hub.get_all()
        if samples:
            self.app.root.after(300, lambda: self._check_for_field_switch(samples))

    def _refresh_results_cache(self):
        """Reset single‑scheme cache to empty."""
        num_rows = self.app.data_hub.row_count()
        self.classification_results = [None] * num_rows

    # ============ HUD MANAGEMENT ============

    def _update_hud(self):
        """Update HUD with EXACT same rows shown in CenterPanel (fully synced)"""

        if not self.hud_tree:
            return

        for item in self.hud_tree.get_children():
            self.hud_tree.delete(item)

        center = self.app.center
        all_samples = self.app.data_hub.get_all()

        if hasattr(center, "sorted_indices") and center.sorted_indices:
            ordered_indices = center.sorted_indices
        else:
            ordered_indices = list(range(len(all_samples)))

        search = center.search_var.get().lower().strip()
        filter_class = center.filter_var.get()
        all_results = getattr(self, 'classification_results', [])

        filtered_indices = []

        for idx in ordered_indices:
            if idx >= len(all_samples):
                continue

            s = all_samples[idx]

            if search:
                if not any(search in str(v).lower() for v in s.values()):
                    continue

            if filter_class and filter_class != "All":
                cls = ''
                if idx < len(all_results) and all_results[idx]:
                    cls = all_results[idx].get('classification', '')
                if not cls:
                    cls = (s.get('Auto_Classification') or s.get('Classification') or '')
                if cls != filter_class:
                    continue

            filtered_indices.append(idx)

        start = center.current_page * center.page_size
        page_indices = filtered_indices[start:start + center.page_size]

        if not page_indices:
            return

        for actual_idx in page_indices:

            sample = all_samples[actual_idx]
            sample_id = sample.get('Sample_ID', 'N/A')
            if len(sample_id) > 8:
                sample_id = sample_id[:8]

            if self.all_mode and self.all_results is not None and actual_idx < len(self.all_results):
                results_list = self.all_results[actual_idx]
                if results_list:
                    best_class = "UNCLASSIFIED"
                    best_conf = 0.0
                    match_count = 0

                    for scheme_name, classification, confidence in results_list:
                        if classification not in ['UNCLASSIFIED', 'INVALID_SAMPLE', 'SCHEME_NOT_FOUND', '']:
                            match_count += 1
                            if confidence > best_conf:
                                best_class = classification
                                best_conf = confidence

                    if match_count > 0:
                        flag = f"🎯 {match_count}"
                        classification_tag = 'MULTI_MATCH' if match_count > 1 else best_class
                    else:
                        flag = "0"
                        classification_tag = 'ALL_NONE'

                    classification = best_class
                    confidence = f"{best_conf:.2f}" if best_conf > 0 else ""
                else:
                    classification = "UNCLASSIFIED"
                    confidence = ""
                    flag = "0"
                    classification_tag = 'ALL_NONE'
            else:
                result = self.classification_results[actual_idx] if actual_idx < len(self.classification_results) else None
                if result:
                    classification = result.get('classification', 'UNCLASSIFIED')
                    confidence = result.get('confidence', '')
                    flag = "🚩" if result.get('flag_for_review', False) else ""
                    classification_tag = classification if classification not in ['UNCLASSIFIED'] else 'UNCLASSIFIED'
                else:
                    classification = "UNCLASSIFIED"
                    confidence = ""
                    flag = ""
                    classification_tag = 'UNCLASSIFIED'

                if confidence and confidence not in ('', 'N/A'):
                    try:
                        conf_val = float(confidence)
                        confidence = f"{conf_val:.2f}" if conf_val <= 1.0 else str(int(conf_val))
                    except (ValueError, TypeError):
                        confidence = str(confidence)

            item_id = self.hud_tree.insert(
                "",
                tk.END,
                values=(sample_id, classification[:20], confidence, flag)
            )

            if classification_tag not in ['UNCLASSIFIED', 'INVALID_SAMPLE', 'SCHEME_NOT_FOUND', '']:
                self.hud_tree.item(item_id, tags=(classification_tag,))

        self.hud_tree.tag_configure('MULTI_MATCH', background='#8B4513', foreground='white')
        self._auto_size_hud_columns()

    def _auto_size_hud_columns(self):
        """Auto-size HUD columns based on content"""
        if not self.hud_tree or not self.hud_tree.get_children():
            return

        self.hud_tree.column('#0', width=50)
        self.hud_tree.column('#1', width=80)
        self.hud_tree.column('#2', width=150)
        self.hud_tree.column('#3', width=60)
        self.hud_tree.column('#4', width=60)

        for col in ['#1', '#2', '#3', '#4']:
            max_width = 0
            for item in self.hud_tree.get_children():
                text = self.hud_tree.item(item, 'values')[int(col[1:])-1]
                width = len(str(text)) * 8
                if width > max_width:
                    max_width = width

            max_width = min(max(max_width, 50), 200)
            self.hud_tree.column(col, width=max_width)

    # ============ CLASSIFICATION ============

    def _run_classification(self):
        """Run selected classification scheme."""
        if not hasattr(self.app, 'classification_engine') or self.app.classification_engine is None:
            self.app.center.show_error('classification', "Classification engine not available")
            messagebox.showerror("Error", "Classification engine not available", parent=self.app.root)
            return

        if not self.scheme_list or not self.scheme_var.get():
            self.app.center.show_warning('classification', "No scheme selected")
            messagebox.showwarning("No Scheme", "Please select a classification scheme", parent=self.app.root)
            return

        selected_display = self.scheme_var.get()
        scheme_id = None
        for display, sid in self.scheme_list:
            if display == selected_display:
                scheme_id = sid
                break

        if not scheme_id:
            return

        if scheme_id == "__ALL__":
            self._run_all_classifications()
            return

        if self.run_target.get() == "all":
            samples = self.app.data_hub.get_all()
            indices = list(range(len(samples)))
        else:
            all_samples = self.app.data_hub.get_all()
            indices = self.app.center.get_selected_indices()
            samples = [all_samples[i] for i in indices if i < len(all_samples)]

        if not samples:
            self.app.center.show_warning('classification', "No samples to classify")
            messagebox.showinfo("Info", "No samples to classify", parent=self.app.root)
            return

        try:
            total_samples = len(samples)
            self.app.center.show_progress('classification', 0, total_samples,
                                        f"Starting classification with {selected_display}...")

            results = self.app.classification_engine.classify_all_samples(samples, scheme_id)

            for i, idx in enumerate(indices):
                if i < len(results) and idx < len(self.classification_results):
                    self.classification_results[idx] = results[i]

            classified_count = sum(1 for r in results if r.get('classification') not in ['UNCLASSIFIED', 'INVALID_SAMPLE'])

            classification_counts = Counter(
                r['classification'] for r in results
                if r.get('classification') not in ['UNCLASSIFIED', 'INVALID_SAMPLE', 'SCHEME_NOT_FOUND', '']
            )

            self.app.center.show_classification_status(
                scheme_name=selected_display,
                total_samples=len(samples),
                classified_count=classified_count,
                classification_counts=dict(classification_counts)
            )
            self.app.center.show_operation_complete('classification',
                                                f"{classified_count}/{total_samples} classified")

            self.all_mode = False
            self._update_hud()
            self.app.center._refresh()

        except Exception as e:
            self.app.center.show_error('classification', str(e)[:50])
            messagebox.showerror("Classification Error", f"Failed to classify: {e}", parent=self.app.root)

    def _run_all_classifications(self):
        """Run all available classification schemes."""
        if not hasattr(self.app, 'classification_engine') or self.app.classification_engine is None:
            self.app.center.show_error('classification', "Classification engine not available")
            messagebox.showerror("Error", "Classification engine not available", parent=self.app.root)
            return

        schemes = self.app.classification_engine.get_available_schemes()
        disabled = self._load_disabled_schemes()
        schemes = [s for s in schemes if s['id'] not in disabled]
        if not schemes:
            messagebox.showinfo("No Schemes", "No classification schemes available", parent=self.app.root)
            return

        if self.run_target.get() == "all":
            samples = self.app.data_hub.get_all()
            indices = list(range(len(samples)))
        else:
            all_samples = self.app.data_hub.get_all()
            indices = self.app.center.get_selected_indices()
            samples = [all_samples[i] for i in indices if i < len(all_samples)]

        if not samples:
            self.app.center.show_warning('classification', "No samples to classify")
            messagebox.showinfo("Info", "No samples to classify", parent=self.app.root)
            return

        total_samples = len(samples)
        total_schemes = len(schemes)
        self.app.center.show_progress('classification', 0, total_samples * total_schemes,
                                      f"Running {total_schemes} schemes on {total_samples} samples...")

        all_results = [[] for _ in range(len(samples))]
        all_derived = [{} for _ in range(len(samples))]

        processed = 0
        for s_idx, scheme in enumerate(schemes):
            scheme_id = scheme['id']
            scheme_name = f"{scheme.get('icon', '📊')} {scheme['name']}"

            results = self.app.classification_engine.classify_all_samples(samples, scheme_id)

            for samp_idx, res in enumerate(results):
                classification = res.get('classification', 'UNCLASSIFIED')
                confidence = res.get('confidence', 0.0)
                derived = res.get('derived_fields', {})
                all_results[samp_idx].append((scheme_name, classification, confidence))
                all_derived[samp_idx][scheme_name] = derived

            processed += len(samples)
            self.app.center.show_progress('classification', processed, total_samples * total_schemes,
                                          f"Completed {s_idx+1}/{total_schemes} schemes")

        total_data_rows = self.app.data_hub.row_count()
        self.all_results = [None] * total_data_rows
        self.all_derived_fields = [None] * total_data_rows
        for batch_idx, global_idx in enumerate(indices):
            self.all_results[global_idx] = all_results[batch_idx]
            self.all_derived_fields[global_idx] = all_derived[batch_idx]

        self.all_mode = True
        self._update_hud()
        self.app.center._refresh()

        self.app.center.show_operation_complete('classification',
                                                f"Ran {total_schemes} schemes on {total_samples} samples")
        messagebox.showinfo("Batch Complete",
                            f"Ran {total_schemes} schemes on {total_samples} samples.\n"
                            "Double‑click any row in the HUD to see full details.",
                            parent=self.app.root)

    # ============ v3.0 FIELD DETECTION & PANEL SWITCHING ============

    _HARDWARE_PLUGIN_MAP = {
        "archaeology_archaeometry_unified_suite":     "archaeology",
        "barcode_scanner_unified_suite":              "archaeology",
        "chromatography_analytical_unified_suite":    "chromatography",
        "clinical_molecular_diagnostics_suite":       "molecular",
        "electrochemistry_unified_suite":             "electrochem",
        "elemental_geochemistry_unified_suite":       "geochemistry",
        "geophysics_unified_suite":                   "geophysics",
        "materials_characterization_unified_suite":   "materials",
        "meteorology_environmental_unified_suite":    "meteorology",
        "molecular_biology_unified_suite":            "molecular",
        "physical_properties_unified_suite":          "physics",
        "physics_test_and_measurement_suite":         "physics",
        "solution_chemistry_unified_suite":           "solution",
        "spectroscopy_unified_suite":                  "spectroscopy",
        "thermal_analysis_calorimetry_unified_suite": "materials",
        "zooarchaeology_unified_suite":               "zooarch",
    }

    _FIELD_DETECTION = {
        "geochemistry":   ("Geochemistry",          "🪨", ["sio2", "tio2", "al2o3", "fe2o3", "mgo", "cao", "na2o", "k2o"]),
        "geochronology":  ("Geochronology",         "⏳", ["pb206", "pb207", "u238", "ar40", "ar39"]),
        "petrology":      ("Petrology",             "🔥", ["quartz", "plagioclase", "feldspar", "modal", "normative", "cipw"]),
        "structural":     ("Structural Geology",    "📐", ["strike", "dip", "plunge", "trend", "azimuth"]),
        "geophysics":     ("Geophysics",            "🌍", ["resistivity", "velocity", "gravity", "mgal", "susceptibility"]),
        "spatial":        ("GIS & Spatial",         "🗺️", ["latitude", "longitude", "easting", "northing", "utm"]),
        "archaeology":    ("Archaeology",           "🏺", ["length_mm", "width_mm", "platform", "lithic", "artifact"]),
        "zooarch":        ("Zooarchaeology",        "🦴", ["taxon", "nisp", "mni", "faunal"]),
        "spectroscopy":   ("Spectroscopy",          "🔬", [
            "technique", "ftir", "raman", "uv-vis", "nir",
            "peak_positions", "peaks", "peak", "compound",
            "wavenumber", "wavelength", "absorbance", "intensity"
        ]),
        "chromatography": ("Chromatography",        "⚗️", ["retention_time", "peak_area", "abundance"]),
        "electrochem":    ("Electrochemistry",      "⚡", ["potential", "scan_rate", "impedance"]),
        "materials":      ("Materials Science",     "🧱", ["stress", "strain", "modulus", "hardness", "tensile"]),
        "solution":       ("Solution Chemistry",    "💧", ["conductivity", "tds", "alkalinity", "turbidity"]),
        "molecular":      ("Molecular Biology",     "🧬", ["ct_value", "cq", "melt_temp", "qpcr", "copies"]),
        "meteorology":    ("Meteorology",           "🌤️", ["humidity", "rainfall", "dew", "wind_speed"]),
        "physics":        ("Physics & Measurement", "📡", ["time_s", "fft", "signal", "amplitude"]),
    }

    def _check_for_field_switch(self, samples):
        """Two-stage detection: hardware source or column scoring"""
        if self.app._is_closing:
            return

        if not hasattr(self, '_current_field_panel'):
            self._current_field_panel = 'classification'
        if not hasattr(self, '_never_ask'):
            self._never_ask = set()

        hw_plugin = getattr(self.app, '_active_hw_plugin', None)
        if hw_plugin:
            self.app._active_hw_plugin = None
            field_id = self._HARDWARE_PLUGIN_MAP.get(hw_plugin)
            if field_id and field_id != self._current_field_panel:
                if field_id not in self._never_ask:
                    name, icon, _ = self._FIELD_DETECTION[field_id]
                    self._show_switch_notification(field_id, name, icon, source="hardware")
            return

        columns = set()
        for s in samples[:10]:
            columns.update(k.lower() for k in s.keys())

        best_field = None
        best_score = 0

        for field_id, (name, icon, fragments) in self._FIELD_DETECTION.items():
            score = sum(1 for frag in fragments if any(frag in col for col in columns))
            if score > best_score:
                best_score = score
                best_field = field_id

        if best_score < 2:
            return

        if best_field == self._current_field_panel:
            return

        if best_field in self._never_ask:
            return

        name, icon, _ = self._FIELD_DETECTION[best_field]
        self._show_switch_notification(best_field, name, icon, source="columns")

    def _show_switch_notification(self, field_id, name, icon, source="columns"):
        """Show a compact yes/no/never notification bar"""
        if hasattr(self, '_notification_frame') and self._notification_frame:
            try:
                self._notification_frame.destroy()
            except tk.TclError:
                pass
            self._notification_frame = None

        notif = ttk.Frame(self.frame, bootstyle="info", relief=tk.RIDGE)
        self._notification_frame = notif

        if source == "hardware":
            detail_text = f"{icon} {name} device active"
        else:
            detail_text = f"{icon} {name} detected"

        ttk.Label(
            notif,
            text=detail_text,
            font=("Segoe UI", 8, "bold"),
            bootstyle="inverse-info",
            anchor="center",
        ).pack(fill=tk.X, padx=4, pady=(4, 1))

        ttk.Label(
            notif,
            text="Switch to specialised panel?",
            font=("Segoe UI", 8),
            bootstyle="info",
            anchor="center",
        ).pack(fill=tk.X, padx=4)

        btn_row = ttk.Frame(notif, bootstyle="info")
        btn_row.pack(fill=tk.X, padx=4, pady=(3, 4))

        def on_yes():
            self._dismiss_notification()
            self._load_field_panel(field_id)

        def on_no():
            self._dismiss_notification()
            if not hasattr(self, '_never_ask'):
                self._never_ask = set()
            self._never_ask.add(field_id)

        def on_never():
            self._dismiss_notification()
            if not hasattr(self, '_never_ask'):
                self._never_ask = set()
            self._never_ask.add(field_id)
            self._save_never_ask(field_id)

        ttk.Button(
            btn_row, text="Yes",
            command=on_yes,
            bootstyle="success",
            width=5,
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            btn_row, text="No",
            command=on_no,
            bootstyle="secondary",
            width=5,
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            btn_row, text="Never",
            command=on_never,
            bootstyle="danger-link",
            width=5,
        ).pack(side=tk.LEFT, padx=2)

        try:
            notif.pack(fill=tk.X, padx=1, pady=1, before=self.engine_frame)
        except tk.TclError:
            notif.pack(fill=tk.X, padx=1, pady=1)

        self._notif_after_id = self.app.root.after(
            20000, self._dismiss_notification
        )

    def _dismiss_notification(self):
        """Remove the notification bar cleanly."""
        if hasattr(self, '_notif_after_id') and self._notif_after_id:
            try:
                self.app.root.after_cancel(self._notif_after_id)
            except Exception:
                pass
            self._notif_after_id = None

        if hasattr(self, '_notification_frame') and self._notification_frame:
            try:
                self._notification_frame.destroy()
            except tk.TclError:
                pass
            self._notification_frame = None

    def _load_field_panel(self, field_id):
        """
        Dynamically import right_panel_<field_id>.py and render it
        """
        import importlib.util
        from pathlib import Path
        from .right_panel import FieldPanelBase

        this_dir = Path(__file__).parent
        stub_path = this_dir / f"right_panel_{field_id}.py"

        if not stub_path.exists():
            messagebox.showwarning(
                "Panel Not Found",
                f"Panel file not found:\n{stub_path.name}",
                parent=self.app.root
            )
            return

        try:
            import sys as _sys
            full_name = f"ui.right_panel_{field_id}"
            spec = importlib.util.spec_from_file_location(full_name, stub_path)
            module = importlib.util.module_from_spec(spec)
            module.__package__ = "ui"
            _sys.modules[full_name] = module
            spec.loader.exec_module(module)

            panel_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and
                    issubclass(attr, FieldPanelBase) and
                    attr != FieldPanelBase and
                    getattr(attr, 'is_right_panel', False)):
                    panel_class = attr
                    break

            if panel_class is None:
                messagebox.showwarning(
                    "Panel Error",
                    f"No valid panel class found in {stub_path.name}",
                    parent=self.app.root
                )
                return

            # Hide current classification UI
            for widget in self.frame.winfo_children():
                widget.pack_forget()

            back_bar = ttk.Frame(self.frame, bootstyle="dark")
            back_bar.pack(fill=tk.X, padx=1, pady=1)

            name, icon, _ = self._FIELD_DETECTION[field_id]

            ttk.Label(
                back_bar,
                text=f"{icon} {name}",
                font=("Segoe UI", 8, "bold"),
                bootstyle="light",
            ).pack(side=tk.LEFT, padx=4)

            ttk.Button(
                back_bar,
                text="← Back",
                command=self._restore_classification_panel,
                bootstyle="secondary-link",
                width=7,
            ).pack(side=tk.RIGHT, padx=2)

            panel_container = ttk.Frame(self.frame, bootstyle="dark")
            panel_container.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

            self._active_field_panel = panel_class(panel_container, self.app)
            self._current_field_panel = field_id
            self._back_bar = back_bar
            self._panel_container = panel_container

            self.app.center.set_status(
                f"Switched to {name} panel", "success"
            )

        except Exception as e:
            messagebox.showerror(
                "Panel Load Error",
                f"Could not load {field_id} panel:\n{e}",
                parent=self.app.root
            )

    def _restore_classification_panel(self):
        """Put the original classification UI back."""
        if hasattr(self, '_back_bar') and self._back_bar:
            try:
                self._back_bar.destroy()
            except tk.TclError:
                pass
            self._back_bar = None

        if hasattr(self, '_panel_container') and self._panel_container:
            try:
                self._panel_container.destroy()
            except tk.TclError:
                pass
            self._panel_container = None

        for widget in self.frame.winfo_children():
            widget.pack_forget()

        self.engine_frame.pack(fill=tk.X, padx=1, pady=1)
        self.row2_frame.pack(fill=tk.X, padx=1, pady=1)
        self.hud_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        self._current_field_panel = 'classification'
        self._active_field_panel = None

        # Force a refresh of the center panel
        if hasattr(self.app, 'center'):
            if hasattr(self.app.center, '_refresh'):
                self.app.center._refresh()
            self.app.center.frame.update_idletasks()

        self.app.root.update_idletasks()
        self.app.center.set_status("Restored Classification panel", "info")

    def _save_never_ask(self, field_id):
        """Persist a 'never ask' preference for a field to config."""
        config_path = Path("config/panel_preferences.json")
        try:
            prefs = {}
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    prefs = json.load(f)
            never = prefs.get('never_ask', [])
            if field_id not in never:
                never.append(field_id)
            prefs['never_ask'] = never
            config_path.parent.mkdir(exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(prefs, f, indent=2)
        except Exception:
            pass


# ============================================================================
# FIELD PANEL BASE CLASS
# ============================================================================

OK_ICON    = "✅"
WARN_ICON  = "⚠️"
ERROR_ICON = "❌"
INFO_ICON  = "ℹ️"

_SECTION_FONT      = ("Segoe UI", 8, "bold")
_VALUE_FONT        = ("Segoe UI", 8)
_LABEL_FONT        = ("Segoe UI", 8)
_PLACEHOLDER_COLOR = "#666666"
_COMING_SOON_TEXT  = "Coming soon"


class FieldPanelBase:
    """
    Base class for all 16 field-specific right panels.
    """

    PANEL_ID       = "base"
    PANEL_NAME     = "Base Panel"
    PANEL_ICON     = "📊"
    DETECT_COLUMNS = []
    is_right_panel = True

    def __init__(self, parent, app):
        self.parent = parent
        self.app    = app

        self.frame = ttk.Frame(parent, bootstyle="dark")
        self.frame.pack(fill=tk.BOTH, expand=True)

        self._collapsed = {
            "summary":    False,
            "validation": False,
            "quick":      False,
        }

        self._build_ui()

    def _build_ui(self):
        self._summary_outer, self._summary_body = self._make_section(
            self.frame, "📊 Summary Statistics", "summary"
        )
        self._validation_outer, self._validation_body = self._make_section(
            self.frame, "✅ Data Validation", "validation"
        )
        self._quick_outer, self._quick_body = self._make_section(
            self.frame, "⚡ Quick Calculation", "quick"
        )

    def _make_section(self, parent, title, key):
        outer = ttk.Frame(parent, bootstyle="dark")
        outer.pack(fill=tk.X, padx=2, pady=(2, 0))

        header = ttk.Button(
            outer,
            text=f"▼  {title}",
            command=lambda k=key: self._toggle_section(k),
            bootstyle="secondary-link",
            width=26,
        )
        header.pack(fill=tk.X)

        setattr(self, f"_{key}_header", header)
        setattr(self, f"_{key}_title",  title)

        body = ttk.Frame(outer, bootstyle="dark")
        body.pack(fill=tk.X, padx=4, pady=(0, 4))

        ttk.Separator(parent, orient="horizontal").pack(
            fill=tk.X, padx=2, pady=(0, 2)
        )
        return outer, body

    def _toggle_section(self, key):
        self._collapsed[key] = not self._collapsed[key]
        body   = getattr(self, f"_{key}_body")
        header = getattr(self, f"_{key}_header")
        title  = getattr(self, f"_{key}_title")
        if self._collapsed[key]:
            body.pack_forget()
            header.config(text=f"▶  {title}")
        else:
            body.pack(fill=tk.X, padx=4, pady=(0, 4))
            header.config(text=f"▼  {title}")

    def refresh(self):
        samples = self.app.data_hub.get_all() if hasattr(self.app, 'data_hub') else []
        columns = self._get_columns(samples)
        self._render_summary(samples, columns)
        self._render_validation(samples, columns)
        self._render_quick(samples, columns)

    def on_data_changed(self, event=None, *args):
        self.refresh()

    def _render_summary(self, samples, columns):
        self._clear(self._summary_body)
        if not samples:
            self._placeholder(self._summary_body, "No data loaded")
            return
        rows = self._calc_summary(samples, columns)
        if not rows:
            self._placeholder(self._summary_body)
            return
        for label, value in rows:
            self._kv_row(self._summary_body, label, value)

    def _render_validation(self, samples, columns):
        self._clear(self._validation_body)
        if not samples:
            self._placeholder(self._validation_body, "No data loaded")
            return
        rows = self._calc_validation(samples, columns)
        if not rows:
            self._placeholder(self._validation_body)
            return
        for icon, message in rows:
            self._status_row(self._validation_body, icon, message)

    def _render_quick(self, samples, columns):
        self._clear(self._quick_body)
        if not samples:
            self._placeholder(self._quick_body, "No data loaded")
            return
        rows = self._calc_quick(samples, columns)
        if not rows:
            self._placeholder(self._quick_body)
            return
        for label, value in rows:
            self._kv_row(self._quick_body, label, value)

    def _clear(self, frame):
        for w in frame.winfo_children():
            w.destroy()

    def _kv_row(self, parent, label, value):
        row = ttk.Frame(parent, bootstyle="dark")
        row.pack(fill=tk.X, pady=1)
        ttk.Label(
            row, text=str(label)[:18],
            font=_LABEL_FONT, bootstyle="secondary",
            anchor="w", width=14,
        ).pack(side=tk.LEFT)
        ttk.Label(
            row, text=str(value)[:16],
            font=_VALUE_FONT, bootstyle="light",
            anchor="e",
        ).pack(side=tk.RIGHT)

    def _status_row(self, parent, icon, message):
        row = ttk.Frame(parent, bootstyle="dark")
        row.pack(fill=tk.X, pady=1)
        ttk.Label(row, text=icon, font=_LABEL_FONT).pack(
            side=tk.LEFT, padx=(0, 3)
        )
        ttk.Label(
            row, text=str(message)[:22],
            font=_VALUE_FONT, bootstyle="light", anchor="w",
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _placeholder(self, parent, text=_COMING_SOON_TEXT):
        ttk.Label(
            parent, text=text,
            font=_LABEL_FONT, foreground=_PLACEHOLDER_COLOR,
        ).pack(anchor="w", pady=2)

    def _get_columns(self, samples):
        if not samples:
            return set()
        cols = set()
        for s in samples[:5]:
            cols.update(k.lower() for k in s.keys())
        return cols

    def _numeric_values(self, samples, key):
        vals = []
        for s in samples:
            v = s.get(key)
            if v is None:
                continue
            try:
                vals.append(float(v))
            except (ValueError, TypeError):
                pass
        return vals

    def _find_column(self, samples, *fragments):
        if not samples:
            return None
        for key in samples[0].keys():
            kl = key.lower()
            for frag in fragments:
                if frag in kl:
                    return key
        return None

    def _safe_mean(self, vals):
        return round(sum(vals) / len(vals), 3) if vals else None

    def _safe_min(self, vals):
        return round(min(vals), 3) if vals else None

    def _safe_max(self, vals):
        return round(max(vals), 3) if vals else None

    def _fmt(self, val, decimals=2):
        if val is None:
            return "—"
        try:
            return f"{float(val):.{decimals}f}"
        except (ValueError, TypeError):
            return str(val)

    def _calc_summary(self, samples, columns):
        return []

    def _calc_validation(self, samples, columns):
        return []

    def _calc_quick(self, samples, columns):
        return []