"""
Electrochemistry Right Panel (Cyclic Voltammetry / EIS)
=========================================================
Features:
  - Dynamic updates when rows are selected in main table
  - Scrollable interface for all content
  - Shows cyclic voltammogram and electrochemical parameters
"""

import tkinter as tk
from tkinter import ttk
import numpy as np
import math
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from .right_panel import FieldPanelBase, OK_ICON, WARN_ICON, ERROR_ICON, INFO_ICON


class ElectrochemPanel(FieldPanelBase):
    PANEL_ID = "electrochemistry"
    PANEL_NAME = "Electrochemistry"
    PANEL_ICON = "⚡"
    DETECT_COLUMNS = ['potential', 'current', 'voltage', 'epa', 'epc',
                      'ipa', 'ipc', 'scan_rate', 'impedance', 'frequency']
    is_right_panel = True

    def __init__(self, parent, app):
        super().__init__(parent, app)

        # Initialize data storage
        self.potential = []
        self.current = []
        self.scan_rate = None
        self.epa = None  # anodic peak potential
        self.epc = None  # cathodic peak potential
        self.ipa = None  # anodic peak current
        self.ipc = None  # cathodic peak current
        self.samples = []
        self.cv_summary = []

        # Selection tracking
        self.selected_indices = set()

        # UI elements
        self.current_selection_label = None
        self.cv_plot_frame = None
        self.params_frame = None
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
        self._redraw_cv_plot()
        self._redraw_params_table()

    def _set_info_label(self):
        """Update selection info label."""
        if not hasattr(self, 'current_selection_label') or not self.current_selection_label:
            return

        if not self.selected_indices:
            text = "Showing: ALL scans"
            color = "black"
        elif len(self.selected_indices) == 1:
            idx = next(iter(self.selected_indices))
            if idx < len(self.cv_summary):
                text = f"Showing: CV Scan {idx+1}"
                color = "blue"
            else:
                text = "Showing: Selected scan"
                color = "blue"
        else:
            text = f"Showing: {len(self.selected_indices)} selected scans"
            color = "green"

        try:
            self.current_selection_label.config(text=text, foreground=color)
        except:
            pass

    def _redraw_cv_plot(self):
        """Redraw CV plot with current selection."""
        if not hasattr(self, 'cv_plot_frame') or not self.cv_plot_frame:
            return
        try:
            for widget in self.cv_plot_frame.winfo_children():
                widget.destroy()
            self._create_cv_plot(self.cv_plot_frame)
        except:
            pass

    def _redraw_params_table(self):
        """Redraw parameters table with current selection."""
        if not hasattr(self, 'params_frame') or not self.params_frame:
            return
        try:
            for widget in self.params_frame.winfo_children():
                widget.destroy()
            self._create_parameters_table(self.params_frame)
        except:
            pass

    # ------------------------------------------------------------------
    # Data extraction
    # ------------------------------------------------------------------
    def _extract_data(self):
        """Extract electrochemical data from samples."""
        self.potential = []
        self.current = []
        self.epa = None
        self.epc = None
        self.ipa = None
        self.ipc = None
        self.cv_summary = []

        if not self.samples:
            return

        # Find columns
        potential_col = self._find_column(self.samples, 'potential', 'voltage', 'e', 'v')
        current_col = self._find_column(self.samples, 'current', 'i', 'current_density')
        scan_rate_col = self._find_column(self.samples, 'scan_rate', 'scanrate', 'nu')

        # Peak columns (if already computed)
        epa_col = self._find_column(self.samples, 'epa', 'e_pa', 'anodic_peak')
        epc_col = self._find_column(self.samples, 'epc', 'e_pc', 'cathodic_peak')
        ipa_col = self._find_column(self.samples, 'ipa', 'i_pa', 'anodic_current')
        ipc_col = self._find_column(self.samples, 'ipc', 'i_pc', 'cathodic_current')

        # Extract scan rate (assumed constant)
        if scan_rate_col and self.samples:
            self.scan_rate = self._tof(self.samples[0].get(scan_rate_col))

        # Extract potential and current data
        if potential_col and current_col:
            for i, sample in enumerate(self.samples):
                e = self._tof(sample.get(potential_col))
                i_val = self._tof(sample.get(current_col))
                if e is not None and i_val is not None:
                    self.potential.append(e)
                    self.current.append(i_val)

                    # Create summary entry
                    self.cv_summary.append({
                        'index': i,
                        'id': sample.get('Sample_ID', f"CV-{i+1:03d}"),
                        'potential': e,
                        'current': i_val,
                        'raw_data': sample
                    })

        # Sort by potential for proper CV plotting
        if self.potential and self.current:
            pairs = sorted(zip(self.potential, self.current))
            self.potential, self.current = zip(*pairs)

        # Extract peak values if available
        if epa_col and self.samples:
            epa_vals = [self._tof(s.get(epa_col)) for s in self.samples if self._tof(s.get(epa_col)) is not None]
            self.epa = np.mean(epa_vals) if epa_vals else None

        if epc_col and self.samples:
            epc_vals = [self._tof(s.get(epc_col)) for s in self.samples if self._tof(s.get(epc_col)) is not None]
            self.epc = np.mean(epc_vals) if epc_vals else None

        if ipa_col and self.samples:
            ipa_vals = [self._tof(s.get(ipa_col)) for s in self.samples if self._tof(s.get(ipa_col)) is not None]
            self.ipa = np.mean(ipa_vals) if ipa_vals else None

        if ipc_col and self.samples:
            ipc_vals = [self._tof(s.get(ipc_col)) for s in self.samples if self._tof(s.get(ipc_col)) is not None]
            self.ipc = np.mean(ipc_vals) if ipc_vals else None

        # If peaks not provided, try to detect them
        if self.epa is None and self.potential and self.current:
            self._detect_peaks()

    def _detect_peaks(self):
        """Simple peak detection for CV."""
        if len(self.current) < 10:
            return

        # Filter data based on selection
        if self.selected_indices:
            potentials_filtered = []
            currents_filtered = []
            for idx in self.selected_indices:
                if idx < len(self.cv_summary):
                    cv = self.cv_summary[idx]
                    potentials_filtered.append(cv['potential'])
                    currents_filtered.append(cv['current'])
            if potentials_filtered and currents_filtered:
                potential = np.array(potentials_filtered)
                current = np.array(currents_filtered)
            else:
                potential = np.array(self.potential)
                current = np.array(self.current)
        else:
            potential = np.array(self.potential)
            current = np.array(self.current)

        # Find peaks
        from scipy.signal import find_peaks
        try:
            # Anodic peaks (positive current)
            anodic_peaks, _ = find_peaks(current, height=np.std(current)*0.5)
            if len(anodic_peaks) > 0:
                idx = anodic_peaks[np.argmax(current[anodic_peaks])]
                self.epa = potential[idx]
                self.ipa = current[idx]

            # Cathodic peaks (negative current - find minima)
            cathodic_peaks, _ = find_peaks(-current, height=np.std(current)*0.5)
            if len(cathodic_peaks) > 0:
                idx = cathodic_peaks[np.argmax(-current[cathodic_peaks])]
                self.epc = potential[idx]
                self.ipc = current[idx]
        except:
            pass

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
        rows.append(("N data points", str(n)))

        if self.potential:
            rows.append(("E range (V)", f"{min(self.potential):.3f}-{max(self.potential):.3f}"))

        if self.current:
            rows.append(("i range (A)", f"{min(self.current):.3e}-{max(self.current):.3e}"))
            rows.append(("Peak current", f"{max(abs(np.array(self.current))):.3e} A"))

        if self.scan_rate:
            rows.append(("Scan rate", f"{self.scan_rate:.0f} mV/s"))

        return rows

    def _calc_validation(self, samples, columns):
        """Data validation."""
        rows = []

        if not samples:
            rows.append((WARN_ICON, "No data"))
            return rows

        # Check for required columns
        potential_col = self._find_column(samples, 'potential', 'voltage')
        current_col = self._find_column(samples, 'current')

        if potential_col:
            rows.append((OK_ICON, f"Potential: {potential_col}"))
        else:
            rows.append((ERROR_ICON, "No potential column"))

        if current_col:
            rows.append((OK_ICON, f"Current: {current_col}"))
        else:
            rows.append((ERROR_ICON, "No current column"))

        # Check scan rate
        scan_rate_col = self._find_column(samples, 'scan_rate', 'scanrate')
        if scan_rate_col:
            rows.append((OK_ICON, "Scan rate found"))
        else:
            rows.append((INFO_ICON, "No scan rate (optional)"))

        return rows

    def _calc_quick(self, samples, columns):
        """Quick calculations."""
        rows = []

        if self.epa and self.epc:
            # Formal potential E⁰' = (Epa + Epc)/2
            e0 = (self.epa + self.epc) / 2
            rows.append(("E⁰' formal", f"{e0:.4f} V"))

            # Peak separation ΔEp
            dep = abs(self.epa - self.epc) * 1000  # in mV
            rows.append(("ΔEp", f"{dep:.1f} mV"))

            # Reversibility check
            if dep <= 70:
                rows.append((OK_ICON, "Reversible"))
            elif dep <= 200:
                rows.append((WARN_ICON, "Quasi-reversible"))
            else:
                rows.append((ERROR_ICON, "Irreversible"))

        if self.ipa and self.ipc:
            # Peak current ratio
            if abs(self.ipc) > 0:
                ratio = abs(self.ipa / self.ipc)
                rows.append(("ipa/ipc", f"{ratio:.3f}"))

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
            text="Select rows in main table to filter scans",
            font=("Segoe UI", 9, "italic")
        )
        self.current_selection_label.pack(side=tk.LEFT)

        # CV plot
        self.cv_plot_frame = ttk.Frame(container)
        self.cv_plot_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self._create_cv_plot(self.cv_plot_frame)

        # Parameters table
        self.params_frame = ttk.Frame(container)
        self.params_frame.pack(fill="x", padx=5, pady=5)
        self._create_parameters_table(self.params_frame)

        # Data table
        self._create_data_table(container)

    def _create_cv_plot(self, parent):
        """Create cyclic voltammogram plot."""
        frame = ttk.LabelFrame(parent, text="Cyclic Voltammogram", padding=10)
        frame.pack(fill="both", expand=True)

        fig = Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)

        ax.set_xlabel("Potential (V)")
        ax.set_ylabel("Current (A)")
        ax.set_title("Cyclic Voltammetry")
        ax.grid(True, linestyle=':', alpha=0.6)

        # Filter data based on selection
        potentials = []
        currents = []

        indices = self.selected_indices if self.selected_indices else range(len(self.cv_summary))

        for idx in indices:
            if idx < len(self.cv_summary):
                cv = self.cv_summary[idx]
                potentials.append(cv['potential'])
                currents.append(cv['current'])

        if potentials and currents:
            # Sort for plotting
            pairs = sorted(zip(potentials, currents))
            p, c = zip(*pairs)
            ax.plot(p, c, 'b-', linewidth=1.5, label='CV')

            # Mark peaks if detected
            if self.epa and self.ipa:
                ax.plot(self.epa, self.ipa, 'ro', markersize=8, label='Epa')
                ax.annotate(f'Epa', (self.epa, self.ipa),
                           xytext=(5, 5), textcoords='offset points')

            if self.epc and self.ipc:
                ax.plot(self.epc, self.ipc, 'go', markersize=8, label='Epc')
                ax.annotate(f'Epc', (self.epc, self.ipc),
                           xytext=(5, -10), textcoords='offset points')

            # Add zero current line
            ax.axhline(y=0, color='gray', linestyle='-', linewidth=0.5, alpha=0.5)

            ax.legend(loc='best')
        else:
            ax.text(0.5, 0.5, "No CV data", ha='center', va='center',
                   transform=ax.transAxes, fontsize=12)

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.figures.append(fig)

    def _create_parameters_table(self, parent):
        """Create table of electrochemical parameters."""
        frame = ttk.LabelFrame(parent, text="Electrochemical Parameters", padding=10)
        frame.pack(fill="x")

        # Create a simple grid of parameters
        params_frame = ttk.Frame(frame)
        params_frame.pack(fill="x")

        # Row 1
        row1 = ttk.Frame(params_frame)
        row1.pack(fill="x", pady=2)

        ttk.Label(row1, text="Epa:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=5)
        ttk.Label(row1, text=f"{self.epa:.4f} V" if self.epa else "N/A").pack(side=tk.LEFT, padx=5)

        ttk.Label(row1, text="Epc:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=20)
        ttk.Label(row1, text=f"{self.epc:.4f} V" if self.epc else "N/A").pack(side=tk.LEFT, padx=5)

        # Row 2
        row2 = ttk.Frame(params_frame)
        row2.pack(fill="x", pady=2)

        ttk.Label(row2, text="ipa:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=5)
        ttk.Label(row2, text=f"{self.ipa:.3e} A" if self.ipa else "N/A").pack(side=tk.LEFT, padx=5)

        ttk.Label(row2, text="ipc:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=20)
        ttk.Label(row2, text=f"{self.ipc:.3e} A" if self.ipc else "N/A").pack(side=tk.LEFT, padx=5)

        # Row 3 - Derived parameters
        if self.epa and self.epc:
            row3 = ttk.Frame(params_frame)
            row3.pack(fill="x", pady=2)

            e0 = (self.epa + self.epc) / 2
            dep = abs(self.epa - self.epc) * 1000

            ttk.Label(row3, text="E⁰':", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=5)
            ttk.Label(row3, text=f"{e0:.4f} V").pack(side=tk.LEFT, padx=5)

            ttk.Label(row3, text="ΔEp:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=20)
            ttk.Label(row3, text=f"{dep:.1f} mV").pack(side=tk.LEFT, padx=5)

    def _create_data_table(self, parent):
        """Create table of CV data points."""
        frame = ttk.LabelFrame(parent, text="Data Points", padding=10)
        frame.pack(fill="x", padx=5, pady=5)

        cols = ["ID", "Potential (V)", "Current (A)"]
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=6)

        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor="center")

        # Filter data based on selection
        indices = self.selected_indices if self.selected_indices else range(len(self.cv_summary))

        for i in sorted(indices)[:20]:  # Limit to 20 rows
            if i >= len(self.cv_summary):
                continue

            cv = self.cv_summary[i]

            tree.insert("", "end", values=(
                cv['id'][:10],
                f"{cv['potential']:.4f}",
                f"{cv['current']:.3e}"
            ))

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
            if idx < len(self.cv_summary):
                hub_idx = self.cv_summary[idx]['index']
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
