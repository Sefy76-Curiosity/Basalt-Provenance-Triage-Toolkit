"""
Molecular Biology / qPCR Right Panel
=======================================
Features:
  - Dynamic updates when rows are selected in main table
  - Scrollable interface for all content
  - Shows Ct values and relative expression
"""

import tkinter as tk
from tkinter import ttk
import numpy as np
import math
from collections import defaultdict
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from .right_panel import FieldPanelBase, OK_ICON, WARN_ICON, ERROR_ICON, INFO_ICON


class MolecularPanel(FieldPanelBase):
    PANEL_ID = "molecular"
    PANEL_NAME = "Molecular Biology (qPCR)"
    PANEL_ICON = "🧬"
    DETECT_COLUMNS = ['ct', 'cq', 'cycle', 'threshold', 'target',
                      'reference', 'efficiency', 'sample_id', 'gene']
    is_right_panel = True

    def __init__(self, parent, app):
        super().__init__(parent, app)

        # Initialize data storage
        self.ct_values = []
        self.target_ct = defaultdict(list)  # target -> list of Ct values
        self.ref_ct = defaultdict(list)     # reference gene -> list of Ct values
        self.efficiencies = {}
        self.ntc_results = []
        self.samples = []
        self.reaction_summary = []

        # Selection tracking
        self.selected_indices = set()

        # UI elements
        self.current_selection_label = None
        self.ct_plot_frame = None
        self.expression_frame = None
        self.figures = []

        # Create scrollable container
        self._create_scrollable_container()

        # Load data and compute
        self.refresh()

    # ------------------------------------------------------------------
    # Public API called by CenterPanel
    # ------------------------------------------------------------------
    def on_selection_changed(self, selected_rows: set):
        """Called by CenterPanel when selection changes."""
        if selected_rows == self.selected_indices:
            return
        self.selected_indices = selected_rows
        self._update_for_selection()

    # ------------------------------------------------------------------
    # Scrollable container
    # ------------------------------------------------------------------
    def _create_scrollable_container(self):
        """Create a scrollable container for all content."""
        self.canvas = tk.Canvas(self.frame, borderwidth=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self._bind_mousewheel()

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        def _configure_canvas(event):
            if self.canvas.winfo_width() > 0:
                self.canvas.itemconfig(1, width=event.width)
        self.canvas.bind('<Configure>', _configure_canvas)

    def _bind_mousewheel(self):
        """Bind mouse wheel for scrolling."""
        def _on_mousewheel(event):
            if event.delta:
                self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            elif event.num == 4:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self.canvas.yview_scroll(1, "units")
            return "break"

        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        self.canvas.bind_all("<Button-4>", _on_mousewheel)
        self.canvas.bind_all("<Button-5>", _on_mousewheel)

    # ------------------------------------------------------------------
    # Selection → display routing
    # ------------------------------------------------------------------
    def _update_for_selection(self):
        """Update display based on current selection."""
        self._set_info_label()
        self._redraw_ct_plot()
        self._redraw_expression_table()

    def _set_info_label(self):
        """Update selection info label."""
        if not hasattr(self, 'current_selection_label') or not self.current_selection_label:
            return

        if not self.selected_indices:
            text = "Showing: ALL reactions"
            color = "black"
        elif len(self.selected_indices) == 1:
            idx = next(iter(self.selected_indices))
            if idx < len(self.reaction_summary):
                text = f"Showing: Reaction {idx+1}"
                color = "blue"
            else:
                text = "Showing: Selected reaction"
                color = "blue"
        else:
            text = f"Showing: {len(self.selected_indices)} selected reactions"
            color = "green"

        try:
            self.current_selection_label.config(text=text, foreground=color)
        except:
            pass

    def _redraw_ct_plot(self):
        """Redraw Ct plot with current selection."""
        if not hasattr(self, 'ct_plot_frame') or not self.ct_plot_frame:
            return
        try:
            for widget in self.ct_plot_frame.winfo_children():
                widget.destroy()
            self._create_ct_plot(self.ct_plot_frame)
        except:
            pass

    def _redraw_expression_table(self):
        """Redraw expression table with current selection."""
        if not hasattr(self, 'expression_frame') or not self.expression_frame:
            return
        try:
            for widget in self.expression_frame.winfo_children():
                widget.destroy()
            self._create_expression_table(self.expression_frame)
        except:
            pass

    # ------------------------------------------------------------------
    # Data extraction
    # ------------------------------------------------------------------
    def _extract_data(self):
        """Extract qPCR data from samples."""
        self.ct_values = []
        self.target_ct = defaultdict(list)
        self.ref_ct = defaultdict(list)
        self.efficiencies = {}
        self.ntc_results = []
        self.reaction_summary = []

        if not self.samples:
            return

        # Find columns
        ct_col = self._find_column(self.samples, 'ct', 'cq', 'threshold_cycle')
        target_col = self._find_column(self.samples, 'target', 'gene', 'target_name')
        ref_col = self._find_column(self.samples, 'reference', 'ref_gene', 'housekeeping')
        sample_col = self._find_column(self.samples, 'sample_id', 'sample')
        ntc_col = self._find_column(self.samples, 'ntc', 'control', 'no_template')
        eff_col = self._find_column(self.samples, 'efficiency', 'eff')

        # Extract efficiencies
        if eff_col:
            for sample in self.samples:
                eff = self._tof(sample.get(eff_col))
                if eff is not None:
                    gene = sample.get(target_col, 'unknown')
                    self.efficiencies[gene] = eff

        # Extract Ct values by target/reference
        for i, sample in enumerate(self.samples):
            reaction = {
                'index': i,
                'id': sample.get('Sample_ID', f"Reaction {i+1}"),
                'ct': None,
                'target': None,
                'is_reference': False,
                'is_ntc': False,
                'efficiency': None,
                'raw_data': sample
            }

            ct = self._tof(sample.get(ct_col))
            if ct is None:
                self.reaction_summary.append(reaction)
                continue

            reaction['ct'] = ct
            self.ct_values.append(ct)

            # Check if NTC
            is_ntc = False
            if ntc_col:
                ntc_val = sample.get(ntc_col)
                is_ntc = str(ntc_val).lower() in ['yes', 'true', '1', 'ntc', 'control']
                reaction['is_ntc'] = is_ntc

            if is_ntc:
                self.ntc_results.append(ct)
                self.reaction_summary.append(reaction)
                continue

            # Determine if target or reference
            gene = sample.get(target_col, 'unknown')
            reaction['target'] = gene

            if ref_col:
                ref_val = sample.get(ref_col)
                is_ref = str(ref_val).lower() in ['yes', 'true', '1', 'ref', 'reference']
                reaction['is_reference'] = is_ref

                if is_ref:
                    self.ref_ct[gene].append(ct)
                else:
                    self.target_ct[gene].append(ct)
            else:
                self.target_ct[gene].append(ct)

            self.reaction_summary.append(reaction)

    def _calculate_dct(self, target_gene, ref_gene='reference'):
        """Calculate ΔCt for a target gene relative to reference."""
        if not self.target_ct[target_gene] or not self.ref_ct[ref_gene]:
            return None

        mean_target = np.mean(self.target_ct[target_gene])
        mean_ref = np.mean(self.ref_ct[ref_gene])

        return mean_target - mean_ref

    def _tof(self, v):
        try:
            if v is None:
                return None
            if isinstance(v, (int, float)):
                return float(v)
            if isinstance(v, str):
                v = v.strip()
                if not v or v.lower() in ['nan', 'na', 'none', 'null', '']:
                    return None
                return float(v)
            return None
        except (TypeError, ValueError):
            return None

    # ------------------------------------------------------------------
    # Base class overrides
    # ------------------------------------------------------------------
    def _calc_summary(self, samples, columns):
        """Summary statistics."""
        rows = []

        if not samples:
            rows.append(("Status", "No samples loaded"))
            return rows

        n = len(samples)
        rows.append(("N reactions", str(n)))

        if self.ct_values:
            rows.append(("Mean Ct", f"{np.mean(self.ct_values):.2f}"))
            rows.append(("Ct range", f"{min(self.ct_values):.2f}-{max(self.ct_values):.2f}"))

        # Number of targets
        n_targets = len(self.target_ct)
        if n_targets > 0:
            rows.append(("Target genes", str(n_targets)))

        # Reference genes
        n_ref = len(self.ref_ct)
        if n_ref > 0:
            rows.append(("Reference genes", str(n_ref)))

        return rows

    def _calc_validation(self, samples, columns):
        """Data validation."""
        rows = []

        if not samples:
            rows.append((WARN_ICON, "No data"))
            return rows

        # Check for Ct column
        ct_col = self._find_column(samples, 'ct', 'cq')
        if ct_col:
            rows.append((OK_ICON, f"Ct column: {ct_col}"))
        else:
            rows.append((ERROR_ICON, "No Ct column"))

        # NTC check
        if self.ntc_results:
            positive_ntc = sum(1 for ct in self.ntc_results if ct < 35)
            if positive_ntc == 0:
                rows.append((OK_ICON, "NTC negative"))
            else:
                rows.append((ERROR_ICON, f"{positive_ntc} NTC positive!"))

        # Replicate variability
        all_replicates = []
        for gene, cts in self.target_ct.items():
            if len(cts) > 1:
                all_replicates.extend(cts)
        for gene, cts in self.ref_ct.items():
            if len(cts) > 1:
                all_replicates.extend(cts)

        if all_replicates:
            sd = np.std(all_replicates)
            if sd <= 0.5:
                rows.append((OK_ICON, f"Replicates SD: {sd:.3f}"))
            else:
                rows.append((WARN_ICON, f"High variability SD: {sd:.3f}"))

        return rows

    def _calc_quick(self, samples, columns):
        """Quick calculations."""
        rows = []

        # ΔCt for first target gene
        if self.target_ct and self.ref_ct:
            first_target = list(self.target_ct.keys())[0]
            first_ref = list(self.ref_ct.keys())[0]
            dct = self._calculate_dct(first_target, first_ref)
            if dct is not None:
                rows.append((f"ΔCt ({first_target})", f"{dct:.2f}"))

        # Approximate relative expression (simplified)
        if self.target_ct and self.ref_ct:
            target_mean = np.mean(list(self.target_ct.values())[0])
            ref_mean = np.mean(list(self.ref_ct.values())[0])

            # 2^-ΔCt (assuming 100% efficiency)
            ratio = 2 ** (-(target_mean - ref_mean))
            rows.append(("Relative expr", f"{ratio:.3f}"))

        return rows

    # ------------------------------------------------------------------
    # Custom UI elements
    # ------------------------------------------------------------------
    def _add_custom_widgets(self):
        """Add custom widgets to the scrollable frame."""
        container = self.scrollable_frame

        # Selection info label
        info_frame = ttk.Frame(container)
        info_frame.pack(fill=tk.X, padx=5, pady=5)

        self.current_selection_label = ttk.Label(
            info_frame,
            text="Select rows in main table to filter reactions",
            font=("Segoe UI", 9, "italic")
        )
        self.current_selection_label.pack(side=tk.LEFT)

        # Ct plot
        self.ct_plot_frame = ttk.Frame(container)
        self.ct_plot_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self._create_ct_plot(self.ct_plot_frame)

        # Expression table
        self.expression_frame = ttk.Frame(container)
        self.expression_frame.pack(fill="x", padx=5, pady=5)
        self._create_expression_table(self.expression_frame)

        # Data table
        self._create_data_table(container)

    def _create_ct_plot(self, parent):
        """Create Ct value bar chart."""
        frame = ttk.LabelFrame(parent, text="Ct Values by Gene", padding=10)
        frame.pack(fill="both", expand=True)

        fig = Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)

        # Collect data based on selection
        genes = []
        means = []
        errors = []
        colors = []

        # Filter target genes based on selection
        target_ct_filtered = defaultdict(list)
        indices = self.selected_indices if self.selected_indices else range(len(self.reaction_summary))

        for idx in indices:
            if idx >= len(self.reaction_summary):
                continue
            rxn = self.reaction_summary[idx]
            if rxn['is_ntc'] or rxn['ct'] is None:
                continue
            if rxn['is_reference']:
                self.ref_ct[rxn['target']].append(rxn['ct'])
            else:
                target_ct_filtered[rxn['target']].append(rxn['ct'])

        # Target genes
        for gene, cts in target_ct_filtered.items():
            if cts:
                genes.append(gene[:10] + "..." if len(gene) > 10 else gene)
                means.append(np.mean(cts))
                errors.append(np.std(cts) if len(cts) > 1 else 0)
                colors.append('steelblue')

        # Reference genes (always show all if no selection, otherwise filtered)
        ref_genes_to_show = self.ref_ct
        if self.selected_indices:
            ref_genes_to_show = defaultdict(list)
            for idx in indices:
                if idx >= len(self.reaction_summary):
                    continue
                rxn = self.reaction_summary[idx]
                if rxn['is_reference'] and rxn['ct'] is not None:
                    ref_genes_to_show[rxn['target']].append(rxn['ct'])

        for gene, cts in ref_genes_to_show.items():
            if cts:
                genes.append(gene[:10] + "..." if len(gene) > 10 else gene)
                means.append(np.mean(cts))
                errors.append(np.std(cts) if len(cts) > 1 else 0)
                colors.append('lightcoral')

        if genes:
            x_pos = range(len(genes))
            ax.bar(x_pos, means, yerr=errors, capsize=5,
                  color=colors, alpha=0.7, edgecolor='black')
            ax.set_xticks(x_pos)
            ax.set_xticklabels(genes, rotation=45, ha='right')
            ax.set_ylabel('Ct Value')
            ax.set_title('Mean Ct Values by Gene')
            ax.axhline(y=35, color='red', linestyle='--', alpha=0.5,
                      label='Detection limit')
            ax.legend(['Detection limit'], loc='upper left')
            ax.grid(True, linestyle=':', alpha=0.3, axis='y')

            # Add value labels
            for i, (v, e) in enumerate(zip(means, errors)):
                ax.text(i, v + e + 0.5, f'{v:.1f}',
                       ha='center', va='bottom', fontsize=8)
        else:
            ax.text(0.5, 0.5, "No Ct data", ha='center', va='center',
                   transform=ax.transAxes, fontsize=12)

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.figures.append(fig)

    def _create_expression_table(self, parent):
        """Create table of relative expression."""
        frame = ttk.LabelFrame(parent, text="Relative Expression", padding=10)
        frame.pack(fill="x")

        if self.target_ct and self.ref_ct:
            # Use filtered data based on selection
            ref_genes = list(self.ref_ct.keys())
            if not ref_genes:
                ttk.Label(frame, text="No reference genes in selection").pack(pady=10)
                return

            ref_gene = ref_genes[0]
            ref_mean = np.mean(self.ref_ct[ref_gene])

            cols = ["Target", "Mean Ct", "ΔCt", "2^-ΔCt"]
            tree = ttk.Treeview(frame, columns=cols, show="headings", height=5)

            for col in cols:
                tree.heading(col, text=col)
                tree.column(col, width=100, anchor="center")

            # Filter target genes based on selection
            target_genes = set()
            indices = self.selected_indices if self.selected_indices else range(len(self.reaction_summary))

            for idx in indices:
                if idx >= len(self.reaction_summary):
                    continue
                rxn = self.reaction_summary[idx]
                if not rxn['is_reference'] and not rxn['is_ntc'] and rxn['target']:
                    target_genes.add(rxn['target'])

            for gene in target_genes:
                if gene in self.target_ct and self.target_ct[gene]:
                    cts = self.target_ct[gene]
                    mean_ct = np.mean(cts)
                    dct = mean_ct - ref_mean
                    expr = 2 ** (-dct)

                    gene_short = gene[:15] + "..." if len(gene) > 15 else gene
                    tree.insert("", "end", values=(
                        gene_short,
                        f"{mean_ct:.2f}",
                        f"{dct:.2f}",
                        f"{expr:.3f}"
                    ))

            scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)

            tree.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
        else:
            ttk.Label(frame, text="Need both target and reference genes for expression analysis"
                     ).pack(pady=10)

    def _create_data_table(self, parent):
        """Create table of reaction data."""
        frame = ttk.LabelFrame(parent, text="Reaction Data", padding=10)
        frame.pack(fill="x", padx=5, pady=5)

        cols = ["ID", "Ct", "Target", "Type"]
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=6)

        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor="center")

        # Filter data based on selection
        indices = self.selected_indices if self.selected_indices else range(len(self.reaction_summary))

        for i in sorted(indices)[:20]:  # Limit to 20 rows
            if i >= len(self.reaction_summary):
                continue

            rxn = self.reaction_summary[i]

            rid = rxn['id'][:8]
            ct = f"{rxn['ct']:.2f}" if rxn['ct'] is not None else "-"
            target = rxn['target'][:10] if rxn['target'] else "-"

            if rxn['is_ntc']:
                rxn_type = "NTC"
            elif rxn['is_reference']:
                rxn_type = "Reference"
            else:
                rxn_type = "Target"

            tree.insert("", "end", values=(rid, ct, target, rxn_type))

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind click to select main table row
        tree.bind('<ButtonRelease-1>', lambda e: self._on_table_click(e, tree))
        self.data_tree = tree

    def _on_table_click(self, event, tree):
        """Handle click on data table → select matching row in main table."""
        item = tree.identify_row(event.y)
        if not item:
            return
        try:
            idx = int(tree.index(item))
            if idx < len(self.reaction_summary):
                hub_idx = self.reaction_summary[idx]['index']
                if hasattr(self.app, 'center') and hasattr(self.app.center, 'selected_rows'):
                    self.app.center.selected_rows = {hub_idx}
                    if hasattr(self.app.center, '_refresh'):
                        self.app.center._refresh()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------
    def refresh(self):
        """Reload data and rebuild the entire panel UI."""
        self.samples = self.app.data_hub.get_all() if hasattr(self.app, 'data_hub') else []
        self._extract_data()

        # Rebuild base section widgets
        super().refresh()

        # Rebuild custom widgets
        if hasattr(self, 'scrollable_frame'):
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()
            self._add_custom_widgets()

        # Re-apply current selection
        self._update_for_selection()
