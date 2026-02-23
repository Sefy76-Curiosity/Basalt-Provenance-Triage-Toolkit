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

        # UI elements
        self.hud_tree = None
        self.scheme_var = tk.StringVar()
        self.protocol_var = tk.StringVar()
        self.run_target = tk.StringVar(value="all")
        self.scheme_list = []
        self.protocol_list = []

        # Cache for single‑scheme results
        self.classification_results = []

        # Cache for "Run All" results
        self.all_results = None
        self.all_mode = False
        self.all_schemes_list = []  # Store list of scheme names for reference

        self._build_ui()
        self._refresh_results_cache()

    def _build_ui(self):
        """Build right panel with compact top and full-height HUD"""
        # ============ ENGINE FRAME ============
        self.engine_frame = ttk.Frame(self.frame, bootstyle="dark")
        self.engine_frame.pack(fill=tk.X, padx=1, pady=1)

        self.refresh_for_engine(getattr(self.app, 'current_engine_name', 'classification'))

        # ============ RUN OPTIONS ============
        row2 = ttk.Frame(self.frame, bootstyle="dark")
        row2.pack(fill=tk.X, padx=1, pady=1)

        self.all_rows_radio = ttk.Radiobutton(
            row2,
            text="All Rows",
            variable=self.run_target,
            value="all",
            bootstyle="primary-toolbutton"
        )
        self.all_rows_radio.pack(side=tk.LEFT, padx=2)

        self.selected_radio = ttk.Radiobutton(
            row2,
            text="Selected",
            variable=self.run_target,
            value="selected",
            bootstyle="primary-toolbutton"
        )
        self.selected_radio.pack(side=tk.LEFT, padx=2)

        # ============ HUD ============
        hud_frame = ttk.Frame(self.frame, bootstyle="dark")
        hud_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        tree_frame = ttk.Frame(hud_frame, bootstyle="dark")
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
            print(f"⚠️ Error refreshing protocols: {e}")
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

        # Configure default tags
        self.hud_tree.tag_configure('UNCLASSIFIED', background='#3b3b3b', foreground='white')

        print(f"✅ Configured {len(configured_tags)} HUD colors")

    # ============ DOUBLE CLICK ============

    def _open_sample_detail(self, sample_idx, samples=None):
        """Open the appropriate detail dialog for a given sample index.
        Called by center_panel._on_double_click so the dialog logic stays in one place.
        """
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

        # IMPORTANT: If we're in all-mode, ALWAYS show the all-schemes dialog
        if self.all_mode and self.all_results is not None:
            # Import here to avoid circular imports
            from ui.all_schemes_detail_dialog import AllSchemesDetailDialog
            AllSchemesDetailDialog(self.app.root, self.app, samples, self.all_results, target_idx, self.all_schemes_list)
            return

        # Otherwise show single-scheme explanation (this should only happen when not in all-mode)
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

            # Add "Run All" as first item
            self.scheme_list.append(("🔁 Run All Schemes", "__ALL__"))

            # Build list of normal schemes
            normal_schemes = []
            for scheme in schemes:
                display = f"{scheme.get('icon', '📊')} {scheme['name']}"
                normal_schemes.append((display, scheme['id']))
                self.all_schemes_list.append(display)

            # Sort normal schemes alphabetically by name
            normal_schemes.sort(key=lambda x: x[0].split(' ', 1)[-1].lower())

            # Add to scheme_list
            self.scheme_list.extend(normal_schemes)

            if self.scheme_list:
                self.scheme_combo['values'] = [s[0] for s in self.scheme_list]
                self.scheme_combo.current(0)
            else:
                self.scheme_combo['values'] = ["No schemes"]
                self.scheme_combo.set("No schemes")
        except Exception as e:
            print(f"⚠️ Error refreshing schemes: {e}")
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

    def _refresh_results_cache(self):
        """Reset single‑scheme cache to empty."""
        num_rows = self.app.data_hub.row_count()
        self.classification_results = [None] * num_rows

    # ============ HUD MANAGEMENT ============

    def _update_hud(self):
        """Update HUD with current page samples."""
        if not self.hud_tree:
            return

        for item in self.hud_tree.get_children():
            self.hud_tree.delete(item)

        samples = self.app.data_hub.get_page(
            self.app.center.current_page,
            self.app.center.page_size
        )

        if not samples:
            return

        start_idx = self.app.center.current_page * self.app.center.page_size

        for i, sample in enumerate(samples):
            actual_idx = start_idx + i
            sample_id = sample.get('Sample_ID', 'N/A')
            if len(sample_id) > 8:
                sample_id = sample_id[:8]

            if self.all_mode and self.all_results is not None and actual_idx < len(self.all_results):
                # All‑schemes mode - show best classification with multi-match indicator
                results_list = self.all_results[actual_idx]
                if results_list:
                    # Find the best (non-UNCLASSIFIED) classification
                    best_class = "UNCLASSIFIED"
                    best_conf = 0.0
                    match_count = 0

                    for scheme_name, classification, confidence in results_list:
                        if classification not in ['UNCLASSIFIED', 'INVALID_SAMPLE', 'SCHEME_NOT_FOUND', '']:
                            match_count += 1
                            if confidence > best_conf:
                                best_class = classification
                                best_conf = confidence

                    # Format flag based on match count
                    if match_count > 0:
                        flag = f"🎯 {match_count}"  # Target icon with count
                        # Use multi-match tag if more than one scheme matched
                        if match_count > 1:
                            classification_tag = 'MULTI_MATCH'
                        else:
                            classification_tag = best_class
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
                # Single‑scheme mode
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

                # Format confidence
                if confidence and confidence not in ('', 'N/A'):
                    try:
                        conf_val = float(confidence)
                        if conf_val <= 1.0:
                            confidence = f"{conf_val:.2f}"
                        else:
                            confidence = str(int(conf_val))
                    except (ValueError, TypeError):
                        confidence = str(confidence)

            item_id = self.hud_tree.insert("", tk.END,
                                        values=(sample_id, classification[:20], confidence, flag))

            # Apply color tag
            if classification_tag not in ['UNCLASSIFIED', 'INVALID_SAMPLE', 'SCHEME_NOT_FOUND', '']:
                self.hud_tree.item(item_id, tags=(classification_tag,))

        # Ensure MULTI_MATCH tag is configured
        self.hud_tree.tag_configure('MULTI_MATCH', background='#8B4513', foreground='white')
        self._auto_size_hud_columns()

    def _auto_size_hud_columns(self):
        """Auto-size HUD columns based on content"""
        if not self.hud_tree or not self.hud_tree.get_children():
            return

        # Set minimum widths for each column
        self.hud_tree.column('#0', width=50)  # Tree column
        self.hud_tree.column('#1', width=80)  # Sample ID
        self.hud_tree.column('#2', width=150) # Classification
        self.hud_tree.column('#3', width=60)  # Confidence
        self.hud_tree.column('#4', width=60)  # Flag (increase this!)

        # Or better - auto-size based on content
        for col in ['#1', '#2', '#3', '#4']:
            max_width = 0
            for item in self.hud_tree.get_children():
                text = self.hud_tree.item(item, 'values')[int(col[1:])-1]
                width = len(str(text)) * 8
                if width > max_width:
                    max_width = width

            # Add padding
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

        # Single scheme
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
            self.app.center._refresh()  # Refresh table to update colors

        except Exception as e:
            self.app.center.show_error('classification', str(e)[:50])
            print(f"❌ Classification error: {e}")
            import traceback
            traceback.print_exc()
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

        # Store results as list of lists for each sample
        all_results = [[] for _ in range(len(samples))]

        processed = 0
        for s_idx, scheme in enumerate(schemes):
            scheme_id = scheme['id']
            scheme_name = f"{scheme.get('icon', '📊')} {scheme['name']}"

            results = self.app.classification_engine.classify_all_samples(samples, scheme_id)

            for samp_idx, res in enumerate(results):
                classification = res.get('classification', 'UNCLASSIFIED')
                confidence = res.get('confidence', 0.0)
                all_results[samp_idx].append((scheme_name, classification, confidence))

            processed += len(samples)
            self.app.center.show_progress('classification', processed, total_samples * total_schemes,
                                          f"Completed {s_idx+1}/{total_schemes} schemes")

        # Store in global index structure
        total_data_rows = self.app.data_hub.row_count()
        self.all_results = [None] * total_data_rows
        for batch_idx, global_idx in enumerate(indices):
            self.all_results[global_idx] = all_results[batch_idx]

        self.all_mode = True
        self._update_hud()
        self.app.center._refresh()  # Refresh table to update colors

        self.app.center.show_operation_complete('classification',
                                                f"Ran {total_schemes} schemes on {total_samples} samples")
        messagebox.showinfo("Batch Complete",
                            f"Ran {total_schemes} schemes on {total_samples} samples.\n"
                            "Double‑click any row in the HUD to see full details.",
                            parent=self.app.root)
