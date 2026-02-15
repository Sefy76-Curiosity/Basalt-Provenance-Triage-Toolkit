"""
Right Panel - 10% width, Classification Hub
Redesigned with compact top controls and full-height HUD
"""

import tkinter as tk
from tkinter import ttk, messagebox

class RightPanel:
    def __init__(self, parent, app):
        self.app = app
        self.frame = ttk.Frame(parent, relief=tk.RAISED, borderwidth=1)

        # UI elements
        self.hud_tree = None
        self.scheme_var = tk.StringVar()
        self.protocol_var = tk.StringVar()
        self.run_target = tk.StringVar(value="all")
        self.scheme_list = []
        self.protocol_list = []

        self._build_ui()

    def _build_ui(self):
        """Build right panel with compact top and full-height HUD"""

        # ============ ENGINE FRAME (dynamic content) ============
        self.engine_frame = ttk.Frame(self.frame)
        self.engine_frame.pack(fill=tk.X, padx=2, pady=2)

        # Initial UI based on current engine
        self.refresh_for_engine(getattr(self.app, '_current_engine', 'classification'))

        # ============ ROW 2: Run Options (Radio Buttons) ============
        row2 = ttk.Frame(self.frame)
        row2.pack(fill=tk.X, padx=2, pady=2)

        ttk.Radiobutton(row2, text="All Rows",
                       variable=self.run_target,
                       value="all").pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(row2, text="Selected",
                       variable=self.run_target,
                       value="selected").pack(side=tk.LEFT, padx=2)

        # ============ ROW 3: HUD ============
        hud_frame = ttk.Frame(self.frame)
        hud_frame.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)

        tree_frame = ttk.Frame(hud_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        self.hud_tree = ttk.Treeview(tree_frame, columns=("ID", "Class", "Conf", "Flag"),
                                     show='headings', height=1)

        self.hud_tree.heading("ID", text="ID")
        self.hud_tree.heading("Class", text="Classification")
        self.hud_tree.heading("Conf", text="Conf")
        self.hud_tree.heading("Flag", text="🚩")

        self.hud_tree.column("ID", width=60, anchor="center")
        self.hud_tree.column("Class", width=150, anchor="w")
        self.hud_tree.column("Conf", width=45, anchor="center")
        self.hud_tree.column("Flag", width=30, anchor="center")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self._on_hud_scroll)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.hud_tree.xview)
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
            # Protocol UI
            self.protocol_combo = ttk.Combobox(self.engine_frame, textvariable=self.protocol_var,
                                              state="readonly", width=15)
            self.protocol_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))

            self.run_protocol_btn = ttk.Button(self.engine_frame, text="Run", width=6,
                                              command=self._run_protocol)
            self.run_protocol_btn.pack(side=tk.RIGHT)

            self._refresh_protocols()
        else:
            # Classification UI
            self.scheme_combo = ttk.Combobox(self.engine_frame, textvariable=self.scheme_var,
                                            state="readonly", width=15)
            self.scheme_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))

            self.apply_btn = ttk.Button(self.engine_frame, text="Apply", width=6,
                                       command=self._run_classification)
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
        if not hasattr(self.app, 'protocol_engine') or self.app.protocol_engine is None:
            messagebox.showerror("Error", "Protocol engine not available")
            return

        selected_display = self.protocol_var.get()
        if not selected_display or selected_display in ["⚠️ Protocol engine not found", "No protocols found"]:
            messagebox.showwarning("No Protocol", "Please select a protocol")
            return

        protocol_id = None
        for display, pid in self.protocol_list:
            if display == selected_display:
                protocol_id = pid
                break

        if not protocol_id:
            return

        if self.run_target.get() == "all":
            samples = self.app.data_hub.get_all()
            indices = list(range(len(samples)))
        else:
            indices = self.app.center.get_selected_indices()
            samples = [self.app.data_hub.get_all()[i] for i in indices if i < len(self.app.data_hub.get_all())]

        if not samples:
            messagebox.showinfo("Info", "No samples to process")
            return

        try:
            result = self.app.protocol_engine.run_protocol(samples, protocol_id)

            if self.run_target.get() == "all":
                for i, sample in enumerate(result):
                    if i < len(self.app.data_hub.get_all()):
                        self.app.data_hub.update_row(i, sample)
            else:
                for i, idx in enumerate(indices):
                    if i < len(result) and idx < len(self.app.data_hub.get_all()):
                        self.app.data_hub.update_row(idx, result[i])

            messagebox.showinfo("Success", f"Protocol completed")
        except Exception as e:
            messagebox.showerror("Error", f"Protocol failed: {e}")

    # ============ SCROLL SYNC ============

    def _on_hud_scroll(self, *args):
        """Sync HUD scroll with main table"""
        if hasattr(self.app.center, '_is_syncing_scroll') and self.app.center._is_syncing_scroll:
            return

        self.hud_tree.yview(*args)
        first, last = self.hud_tree.yview()

        if hasattr(self.app, 'center'):
            self.app.center._is_syncing_scroll = True
            self.app.center.tree.yview_moveto(first)
            self.app.center._is_syncing_scroll = False

    def _on_hud_mousewheel(self, event):
        """Handle mouse wheel on HUD"""
        if hasattr(self.app.center, '_is_syncing_scroll') and self.app.center._is_syncing_scroll:
            return

        if event.delta:
            self.hud_tree.yview_scroll(int(-1 * (event.delta / 120)), "units")
        else:
            if event.num == 4:
                self.hud_tree.yview_scroll(-1, "units")
            elif event.num == 5:
                self.hud_tree.yview_scroll(1, "units")

        first, last = self.hud_tree.yview()

        if hasattr(self.app, 'center'):
            self.app.center._is_syncing_scroll = True
            self.app.center.tree.yview_moveto(first)
            self.app.center._is_syncing_scroll = False

        return "break"

    # ============ COLORS ============

    def _configure_hud_colors(self):
        """Configure HUD colors from color manager - background only (text stays black)"""
        configured_tags = set()

        for classification in self.app.color_manager.get_all_classifications():
            bg_color = self.app.color_manager.get_background(classification)

            if classification not in configured_tags:
                # Set ONLY background - let text use default foreground (black)
                self.hud_tree.tag_configure(classification,
                                        background=bg_color)
                configured_tags.add(classification)

            if classification.upper() not in configured_tags:
                self.hud_tree.tag_configure(classification.upper(),
                                        background=bg_color)
                configured_tags.add(classification.upper())

        print(f"✅ Configured {len(configured_tags)} HUD colors (background only)")

    # ============ DOUBLE CLICK ============

    def _on_hud_double_click(self, event):
        """Show classification explanation on double-click"""
        item = self.hud_tree.identify_row(event.y)
        if not item:
            return

        values = self.hud_tree.item(item, "values")
        if not values or len(values) < 1:
            return

        short_id = values[0]
        samples = self.app.data_hub.get_all()
        target_sample = None

        for sample in samples:
            full_id = sample.get('Sample_ID', '')
            if full_id.endswith(short_id):
                target_sample = sample
                break

        if target_sample:
            self.app.center._show_classification_explanation(target_sample)

    # ============ SCHEMES ============

    def _refresh_schemes(self):
        """Refresh scheme dropdown from classification engine"""
        if getattr(self.app, '_current_engine', 'classification') == 'protocol':
            return

        if not hasattr(self.app, 'classification_engine') or self.app.classification_engine is None:
            self.scheme_combo['values'] = ["No engine"]
            self.scheme_combo.set("No engine")
            return

        try:
            schemes = self.app.classification_engine.get_available_schemes()
            self.scheme_list = []
            for scheme in schemes:
                display = f"{scheme.get('icon', '📊')} {scheme['name']}"
                self.scheme_list.append((display, scheme['id']))

            self.scheme_list.sort(key=lambda x: x[0].split(' ', 1)[1] if ' ' in x[0] else x[0])

            if self.scheme_list:
                self.scheme_combo['values'] = [s[0] for s in self.scheme_list]
                self.scheme_combo.current(0)
            else:
                self.scheme_combo['values'] = ["No schemes"]
                self.scheme_combo.set("No schemes")
        except:
            self.scheme_combo['values'] = ["No schemes"]
            self.scheme_combo.set("No schemes")

    # ============ DATA OBSERVER ============

    def on_data_changed(self, event, *args):
        """Refresh HUD when data changes"""
        self._update_hud()

    # ============ HUD MANAGEMENT ============

    def _update_hud(self):
        """Update HUD with current page samples"""
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

        for sample in samples:
            sample_id = sample.get('Sample_ID', 'N/A')
            if len(sample_id) > 6:
                sample_id = sample_id[-6:]

            classification = self._get_classification(sample)
            
            # Get confidence value
            confidence = sample.get('Auto_Confidence', 'N/A')
            if confidence != 'N/A' and confidence is not None:
                try:
                    # Format confidence based on scale
                    conf_val = float(confidence)
                    if conf_val <= 1.0:
                        confidence = f"{conf_val:.2f}"  # Decimal scale (0.95)
                    else:
                        confidence = f"{int(conf_val)}"  # Integer scale (4)
                except (ValueError, TypeError):
                    confidence = 'N/A'
            
            # Get flag status
            flag_value = sample.get('Flag_For_Review', False)
            if flag_value == True or flag_value == 'True' or flag_value == 'YES':
                flag = "🚩"
            else:
                flag = ""

            item_id = self.hud_tree.insert("", tk.END,
                                          values=(sample_id, classification[:15], confidence, flag))
            self.hud_tree.item(item_id, tags=(classification,))

        self._auto_size_hud_columns()

    def _auto_size_hud_columns(self):
        """Auto-size HUD columns"""
        if not self.hud_tree or not self.hud_tree.get_children():
            return

        items = self.hud_tree.get_children()
        col_widths = {
            "ID": len("ID") * 8,
            "Class": len("Classification") * 8,
            "Conf": len("Conf") * 8,
            "Flag": len("🚩") * 8
        }

        for item in items[:50]:
            values = self.hud_tree.item(item, "values")
            if len(values) >= 4:
                col_widths["ID"] = max(col_widths["ID"], len(str(values[0])) * 8)
                col_widths["Class"] = max(col_widths["Class"], len(str(values[1])) * 8)
                col_widths["Conf"] = max(col_widths["Conf"], len(str(values[2])) * 8)
                col_widths["Flag"] = max(col_widths["Flag"], len(str(values[3])) * 8)

        self.hud_tree.column("ID", width=min(max(40, col_widths["ID"]), 70))
        self.hud_tree.column("Class", width=min(max(80, col_widths["Class"]), 150))
        self.hud_tree.column("Conf", width=min(max(35, col_widths["Conf"]), 50))
        self.hud_tree.column("Flag", width=min(max(25, col_widths["Flag"]), 35))

    # ============ CLASSIFICATION ============

    def _get_classification(self, sample):
        """Get classification from sample"""
        return (sample.get('Final_Classification') or
                sample.get('Auto_Classification') or
                sample.get('Classification') or
                "UNCLASSIFIED")

    def _run_classification(self):
        """Run selected classification scheme"""
        # Validate classification engine
        if not hasattr(self.app, 'classification_engine') or self.app.classification_engine is None:
            messagebox.showerror("Error", "Classification engine not available")
            return

        # Validate scheme selection
        if not self.scheme_list or not self.scheme_var.get():
            messagebox.showwarning("No Scheme", "Please select a classification scheme")
            return

        selected_display = self.scheme_var.get()
        scheme_id = None
        for display, sid in self.scheme_list:
            if display == selected_display:
                scheme_id = sid
                break

        if not scheme_id:
            return

        # Get samples to process
        if self.run_target.get() == "all":
            samples = self.app.data_hub.get_all()
            indices = list(range(len(samples)))
        else:
            indices = self.app.center.get_selected_indices()
            samples = [self.app.data_hub.get_all()[i] for i in indices if i < len(self.app.data_hub.get_all())]

        if not samples:
            messagebox.showinfo("Info", "No samples to classify")
            return

        try:
            # Show processing status in center panel
            self.app.center.set_status(f"Processing {len(samples)} samples using {selected_display}...", "processing")

            # Store original classifications to track changes
            original_classifications = [s.get('Auto_Classification', 'UNCLASSIFIED') for s in samples]

            # Run classification
            classified = self.app.classification_engine.classify_all_samples(samples, scheme_id)

            # Count results
            newly_classified = 0
            classification_counts = {}

            for i, sample in enumerate(classified):
                new_class = sample.get('Auto_Classification', 'UNCLASSIFIED')
                if new_class != 'UNCLASSIFIED':
                    if new_class != original_classifications[i]:
                        newly_classified += 1
                    classification_counts[new_class] = classification_counts.get(new_class, 0) + 1

            # Update data hub
            if self.run_target.get() == "all":
                for i, classified_sample in enumerate(classified):
                    if i < len(self.app.data_hub.get_all()):
                        updates = {}
                        if 'Auto_Classification' in classified_sample:
                            updates['Auto_Classification'] = classified_sample['Auto_Classification']
                        if 'Auto_Confidence' in classified_sample:
                            updates['Auto_Confidence'] = classified_sample['Auto_Confidence']
                        if 'Flag_For_Review' in classified_sample:
                            updates['Flag_For_Review'] = classified_sample['Flag_For_Review']
                        for key in ['Zr_Nb_Ratio', 'Cr_Ni_Ratio', 'Ba_Rb_Ratio']:
                            if key in classified_sample and key not in self.app.data_hub.get_all()[i]:
                                updates[key] = classified_sample[key]
                        if updates:
                            self.app.data_hub.update_row(i, updates)
            else:
                for i, idx in enumerate(indices):
                    if i < len(classified) and idx < len(self.app.data_hub.get_all()):
                        updates = {}
                        if 'Auto_Classification' in classified[i]:
                            updates['Auto_Classification'] = classified[i]['Auto_Classification']
                        if 'Auto_Confidence' in classified[i]:
                            updates['Auto_Confidence'] = classified[i]['Auto_Confidence']
                        if 'Flag_For_Review' in classified[i]:
                            updates['Flag_For_Review'] = classified[i]['Flag_For_Review']
                        current_sample = self.app.data_hub.get_all()[idx]
                        for key in ['Zr_Nb_Ratio', 'Cr_Ni_Ratio', 'Ba_Rb_Ratio']:
                            if key in classified[i] and key not in current_sample:
                                updates[key] = classified[i][key]
                        if updates:
                            self.app.data_hub.update_row(idx, updates)

            # Update status in center panel
            self.app.center.show_classification_status(
                scheme_name=selected_display,
                total_samples=len(samples),
                classified_count=newly_classified,
                classification_counts=classification_counts
            )

            # Also print detailed info to console for debugging
            print(f"\n📊 Classification Results for '{selected_display}':")
            print(f"   Total samples: {len(samples)}")
            print(f"   New classifications: {newly_classified}")
            print(f"   Unclassified: {len(samples) - newly_classified}")
            if classification_counts:
                print("   Breakdown:")
                for class_name, count in sorted(classification_counts.items(), key=lambda x: x[1], reverse=True):
                    print(f"     • {class_name}: {count}")

        except Exception as e:
            self.app.center.set_status(f"Classification failed: {str(e)[:50]}", "error")
            print(f"❌ Classification error: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Classification Error", f"Failed to classify: {e}")
