"""
All Schemes Detail Dialog
Fully converted to ttkbootstrap with dark theme consistency
Double-click a scheme to see detailed explanation with Back navigation
Now with smart explanation generation from scheme JSON files
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import os
import json

def generate_explanation_text(app, scheme_name, classification_name, sample):
    """Shared explanation generator used by both single and all‑schemes dialogs."""
    import re, os, json
    from pathlib import Path

    # Clean scheme name (remove emojis)
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F" u"\U0001F300-\U0001F5FF" u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF" u"\U00002702-\U000027B0" u"\U000024C2-\U0001F251"
        u"\U0001F900-\U0001F9FF" u"\U0001FA70-\U0001FAFF" u"\U00002600-\U000026FF"
        u"\U00002B50" "]+", flags=re.UNICODE)
    clean_scheme_name = emoji_pattern.sub('', scheme_name).strip()
    for emoji in ['✅','🔬','🏛','🌍','🪐','🏺','💎','⚒','🌋','🎯','📊','🧱','🌱','🪨','☄️','⚙️','📈','🧪','🥩','🦴']:
        clean_scheme_name = clean_scheme_name.replace(emoji, '')
    clean_scheme_name = clean_scheme_name.strip()

    # Helper to get a value from sample with multiple possible keys
    def get_field_value(field_name):
        possible_keys = {
            'Zr_ppm': ['Zr_ppm', 'Zr', 'zirconium', 'Zirconium'],
            'Nb_ppm': ['Nb_ppm', 'Nb', 'niobium', 'Niobium'],
            'Ba_ppm': ['Ba_ppm', 'Ba', 'barium', 'Barium'],
            'Cr_ppm': ['Cr_ppm', 'Cr', 'chromium', 'Chromium'],
            'Ni_ppm': ['Ni_ppm', 'Ni', 'nickel', 'Nickel'],
        }
        if field_name in possible_keys:
            for key in possible_keys[field_name]:
                if key in sample and sample[key] not in (None, ''):
                    try:
                        return float(sample[key])
                    except:
                        pass
        if field_name in sample and sample[field_name] not in (None, ''):
            try:
                return float(sample[field_name])
            except:
                pass
        return None

    # Determine path to classification schemes
    possible_paths = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'engines', 'classification'),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'engines', 'classification'),
        os.path.join(app.app_dir, 'engines', 'classification') if hasattr(app, 'app_dir') else None,
        os.path.join(os.getcwd(), 'engines', 'classification')
    ]
    schemes_dir = None
    for path in possible_paths:
        if path and os.path.exists(path):
            schemes_dir = path
            break
    if not schemes_dir:
        return _fallback_explanation_text(sample, classification_name, "Scheme directory not found")

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
        return _fallback_explanation_text(sample, classification_name, f"Error loading scheme: {str(e)}")

    if not scheme_data:
        return _fallback_explanation_text(sample, classification_name, f"Scheme data not found")

    # Find the matching classification
    classification = None
    for c in scheme_data.get('classifications', []):
        if c['name'] == classification_name:
            classification = c
            break
    if not classification:
        return _fallback_explanation_text(sample, classification_name, f"Classification details not found")

    # Build explanation
    lines = [ "="*50, f"📋 {clean_scheme_name}", f"🎯 Classification: {classification_name}", "="*50, "" ]
    if classification.get('description'):
        lines.append(f"📌 Description: {classification['description']}\n")

    rules = classification.get('rules', [])
    if rules:
        lines.append("⚖️ Classification Criteria:\n")
        for i, rule in enumerate(rules, 1):
            field = rule['field']
            operator = rule['operator']

            # Get value for this field (compute ratios if needed)
            if field == 'Zr_Nb_Ratio':
                zr = get_field_value('Zr_ppm')
                nb = get_field_value('Nb_ppm')
                if zr is not None and nb is not None and nb != 0:
                    val = zr / nb
                    sample_val = f"{val:.3f}".rstrip('0').rstrip('.')
                else:
                    sample_val = 'N/A'
            elif field == 'Cr_Ni_Ratio':
                cr = get_field_value('Cr_ppm')
                ni = get_field_value('Ni_ppm')
                if cr is not None and ni is not None and ni != 0:
                    val = cr / ni
                    sample_val = f"{val:.3f}".rstrip('0').rstrip('.')
                else:
                    sample_val = 'N/A'
            else:
                raw_val = get_field_value(field)
                if raw_val is not None:
                    sample_val = f"{raw_val:.3f}".rstrip('0').rstrip('.')
                else:
                    sample_val = sample.get(field, 'N/A')
                    if isinstance(sample_val, (int, float)):
                        sample_val = f"{sample_val:.3f}".rstrip('0').rstrip('.')

            # Evaluate condition
            condition_met = False
            if operator == '>':
                threshold = rule['value']
                try:
                    v = float(val) if field in ['Zr_Nb_Ratio','Cr_Ni_Ratio'] else float(get_field_value(field))
                    condition_met = v > float(threshold)
                except:
                    pass
            elif operator == '<':
                threshold = rule['value']
                try:
                    v = float(val) if field in ['Zr_Nb_Ratio','Cr_Ni_Ratio'] else float(get_field_value(field))
                    condition_met = v < float(threshold)
                except:
                    pass
            elif operator == 'between':
                min_val = rule.get('min') or rule['value'][0]
                max_val = rule.get('max') or rule['value'][1]
                try:
                    v = float(val) if field in ['Zr_Nb_Ratio','Cr_Ni_Ratio'] else float(get_field_value(field))
                    condition_met = float(min_val) <= v <= float(max_val)
                except:
                    pass
            elif operator == '==':
                threshold = rule['value']
                try:
                    v = float(val) if field in ['Zr_Nb_Ratio','Cr_Ni_Ratio'] else float(get_field_value(field))
                    condition_met = abs(v - float(threshold)) < 0.0001
                except:
                    pass

            # Build rule line
            if operator == '>':
                threshold = rule['value']
                lines.append(f"  {i}. {field} > {threshold}")
                lines.append(f"     Your sample: {sample_val}")
                lines.append("     ✓ Threshold exceeded" if condition_met else "     ✗ Threshold not met")
            elif operator == '<':
                threshold = rule['value']
                lines.append(f"  {i}. {field} < {threshold}")
                lines.append(f"     Your sample: {sample_val}")
                lines.append("     ✓ Below threshold" if condition_met else "     ✗ Threshold not met")
            elif operator == 'between':
                min_val = rule.get('min') or rule['value'][0]
                max_val = rule.get('max') or rule['value'][1]
                lines.append(f"  {i}. {field} between {min_val} and {max_val}")
                lines.append(f"     Your sample: {sample_val}")
                lines.append("     ✓ Within range" if condition_met else "     ✗ Outside range")
            elif operator == '==':
                threshold = rule['value']
                lines.append(f"  {i}. {field} = {threshold}")
                lines.append(f"     Your sample: {sample_val}")
                lines.append("     ✓ Matches exactly" if condition_met else "     ✗ Does not match")
            lines.append("")

    if 'priority' in classification:
        lines.append(f"📊 Priority: {classification['priority']}")
    if 'confidence_score' in classification:
        lines.append(f"📈 Base confidence: {classification['confidence_score']}")
    lines.append("")
    lines.append("="*53)
    if scheme_data.get('reference'):
        lines.append(f"📚 **Reference:** {scheme_data['reference']}")
    if scheme_data.get('author'):
        lines.append(f"👤 **Author:** {scheme_data['author']}")
    if scheme_data.get('date_created'):
        lines.append(f"📅 **Date:** {scheme_data['date_created']}")
    lines.append("="*53)

    return "\n".join(lines)


def _fallback_explanation_text(sample, classification, error_msg=None):
    """Fallback explanation when scheme loading fails."""
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
        for key, val in sample.items():
            if isinstance(val, (int, float)) and val not in (None, ''):
                lines.append(f"  {key}: {val:.3f}")
    lines.append("")
    lines.append("=" * 50)
    return "\n".join(lines)

class AllSchemesDetailDialog:
    def __init__(self, parent, app, samples, all_results, current_index, scheme_names, all_derived=None):
        self.parent = parent
        self.app = app
        self.samples = samples
        self.all_results = all_results
        self.current_index = current_index
        self.scheme_names = scheme_names
        self.all_derived = all_derived  # New: store derived fields if provided

        self.detail_mode = False
        self.current_scheme = None
        self.current_classification = None

        self.window = ttk.Toplevel(parent)
        self.window.title(f"All Schemes: {self._get_sample_id()}")
        self.window.geometry("780x620")
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

        # Create detail view with notebook for tabs
        notebook = ttk.Notebook(self.content_frame, bootstyle="dark")
        notebook.pack(fill=BOTH, expand=True)

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

        text_widget.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        # Generate intelligent explanation
        explanation = self._generate_explanation(self.current_scheme, self.current_classification, sample)
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
            orient=VERTICAL,
            command=raw_text.yview,
            bootstyle="dark-round"
        )
        raw_scroll_x = ttk.Scrollbar(
            raw_frame,
            orient=HORIZONTAL,
            command=raw_text.xview,
            bootstyle="dark-round"
        )
        raw_text.configure(yscrollcommand=raw_scroll_y.set, xscrollcommand=raw_scroll_x.set)

        raw_text.pack(side=LEFT, fill=BOTH, expand=True)
        raw_scroll_y.pack(side=RIGHT, fill=Y)
        raw_scroll_x.pack(side=BOTTOM, fill=X)

        # Show all sample data
        raw_text.insert(tk.END, json.dumps(sample, indent=2))
        raw_text.config(state=tk.DISABLED)

        self.window.title(f"Detail: {self.current_scheme} - {self._get_sample_id()}")

    def _generate_explanation(self, scheme_name, classification_name, sample):
        """Generate detailed explanation using the shared function."""
        return generate_explanation_text(self.app, scheme_name, classification_name, sample)


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
