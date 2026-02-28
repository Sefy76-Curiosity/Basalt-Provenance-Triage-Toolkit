"""
Spectroscopy Right Panel (FTIR / Raman / UV-Vis)
===================================================
Enhanced to handle both:
  - Long-form: one row per wavelength/intensity point
  - Wide-form: summary with peak lists (like library search results)

Features:
  - Dynamic updates when rows are selected in main table
  - Scrollable interface for all content
  - Shows actual waveform/spectrum

FIXED: Selection sync now uses on_selection_changed() pushed by CenterPanel
       instead of polling or <<TreeviewSelect>> (which never fires for custom
       checkbox-based selection).
"""

import tkinter as tk
from tkinter import ttk
import numpy as np
import json
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt          # needed for cm.tab10
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import re
from collections import Counter

from .right_panel import FieldPanelBase, OK_ICON, WARN_ICON, ERROR_ICON, INFO_ICON


class SpectroscopyPanel(FieldPanelBase):
    PANEL_ID = "spectroscopy"
    PANEL_NAME = "Spectroscopy"
    PANEL_ICON = "🔬"
    DETECT_COLUMNS = [
        'wavenumber', 'wavelength', 'raman_shift', 'shift', 'nm', 'cm-1', 'cm^-1',
        'absorbance', 'transmittance', 'intensity', 'counts', 'signal', 'reflectance',
        'ftir', 'raman', 'uv-vis', 'uv_vis', 'uvvis', 'ir', 'near_ir', 'nir',
        'peak_positions', 'peaks', 'peak_list', 'peak_table', 'peak'
    ]
    is_right_panel = True

    def __init__(self, parent, app):
        super().__init__(parent, app)

        # Initialize data storage
        self.data_format = None
        self.x_values = []
        self.y_values = []
        self.peak_positions = []
        self.peak_heights = []
        self.spectra_summary = []
        self.figures = []
        self.samples = []
        self.x_col = None
        self.y_col = None
        self.peak_col = None
        self.spectrum_id_col = None
        self.compound_col = None
        self.technique = None
        self.confidence_col = None
        self.x_data_col = None
        self.y_data_col = None
        self.x_label_col = None
        self.y_label_col = None
        self.spectrum_x_data = []
        self.spectrum_y_data = []

        # Selection tracking — populated via on_selection_changed()
        self.selected_indices = set()

        # UI elements
        self.peak_histogram_frame = None
        self.spectra_table = None
        self.current_spectrum_label = None
        self.spectrum_viewer_frame = None
        self.spectrum_viewer_canvas = None
        self.compound_chart_canvas = None
        self.peak_histogram_canvas = None

        # Create scrollable container
        self._create_scrollable_container()

        # Load data and compute
        self.refresh()

    # ------------------------------------------------------------------
    # Public API called by CenterPanel._notify_field_panel_selection()
    # ------------------------------------------------------------------

    def on_selection_changed(self, selected_rows: set):
        """
        Called by CenterPanel every time the user clicks a row.

        selected_rows  –  set of data-hub indices (ints) that are currently
                          checked/selected in the main table.
        """
        if selected_rows == self.selected_indices:
            return  # nothing changed

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
        """Route to the right display mode based on selection size."""
        if not self.selected_indices:
            self._update_display_for_all()
        elif len(self.selected_indices) == 1:
            idx = next(iter(self.selected_indices))
            # Map data-hub index → spectra_summary index
            spec_idx = self._hub_index_to_spec_index(idx)
            if spec_idx is not None:
                self._update_display_for_spectrum(spec_idx)
            else:
                self._update_display_for_all()
        else:
            self._update_display_for_selected()

    def _hub_index_to_spec_index(self, hub_idx):
        """
        Convert a data-hub row index to an index into self.spectra_summary.
        Since self.samples = data_hub.get_all(), the indices are the same.
        Falls back to None if out of range.
        """
        if 0 <= hub_idx < len(self.spectra_summary):
            return hub_idx
        return None

    def _update_display_for_all(self):
        """Show summary across all spectra."""
        self._set_info_label("Showing: ALL spectra", "black", normal=True)
        self._rebuild_peak_histogram()
        self._redraw_spectrum_viewer()

    def _update_display_for_spectrum(self, spec_idx):
        """Show a single selected spectrum."""
        if spec_idx >= len(self.spectra_summary):
            return
        spec = self.spectra_summary[spec_idx]
        self._set_info_label(
            f"Showing: {spec['id']} — {spec['compound']}",
            "blue", bold=True
        )
        self._rebuild_peak_histogram(selected_idx=spec_idx)
        self._redraw_spectrum_viewer()

    def _update_display_for_selected(self):
        """Show the set of selected spectra."""
        self._set_info_label(
            f"Showing: {len(self.selected_indices)} selected spectra",
            "green", bold=True
        )
        # Map hub indices → spec indices
        spec_indices = {
            si for hi in self.selected_indices
            for si in [self._hub_index_to_spec_index(hi)]
            if si is not None
        }
        self._rebuild_peak_histogram(selected_indices=spec_indices)
        self._redraw_spectrum_viewer()

    def _set_info_label(self, text, color, bold=False, normal=False):
        if not (hasattr(self, 'current_spectrum_label') and self.current_spectrum_label):
            return
        try:
            font_style = "bold" if bold else "normal"
            self.current_spectrum_label.config(
                text=text,
                foreground=color,
                font=("Segoe UI", 9, font_style)
            )
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Redraw helpers
    # ------------------------------------------------------------------

    def _redraw_spectrum_viewer(self):
        """Redraw the spectrum viewer with current selection."""
        if not hasattr(self, 'spectrum_viewer_frame') or not self.spectrum_viewer_frame:
            return
        try:
            for widget in self.spectrum_viewer_frame.winfo_children():
                widget.destroy()
            self._create_spectrum_viewer(self.spectrum_viewer_frame)
        except Exception:
            pass

    def _rebuild_peak_histogram(self, selected_idx=None, selected_indices=None):
        """Rebuild the peak histogram with filtered data."""
        if not hasattr(self, 'peak_histogram_frame') or not self.peak_histogram_frame:
            return
        try:
            for widget in self.peak_histogram_frame.winfo_children():
                widget.destroy()
            self._create_peak_histogram(self.peak_histogram_frame, selected_idx, selected_indices)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Data detection / extraction
    # ------------------------------------------------------------------

    def _detect_format(self):
        """Detect data format."""
        if not self.samples:
            return None

        peak_candidates = ['peak_positions', 'peaks', 'peak_list', 'peak_table', 'peak']
        for cand in peak_candidates:
            col = self._find_column(self.samples, cand)
            if col:
                self.peak_col = col
                return 'peak_list'

        intensity_candidates = ['absorbance', 'intensity', 'transmittance', 'counts', 'signal']
        for cand in intensity_candidates:
            if self._find_column(self.samples, cand):
                return 'long'

        return None

    def _parse_peak_list(self, peak_str):
        """Parse peak list string into list of floats."""
        if not peak_str:
            return []
        try:
            if isinstance(peak_str, (int, float)):
                return [float(peak_str)]
            if isinstance(peak_str, str):
                peak_str = re.sub(r'[\[\]"\'(){}]', '', peak_str)
                peaks = []
                for p in peak_str.split(','):
                    p = p.strip()
                    if p:
                        num_match = re.search(r'-?\d+\.?\d*', p)
                        if num_match:
                            peaks.append(float(num_match.group()))
                return peaks
        except Exception:
            pass
        return []

    def _extract_data(self):
        """Extract spectral data."""
        self.data_format = self._detect_format()
        self.x_values = []
        self.y_values = []
        self.peak_positions = []
        self.peak_heights = []
        self.spectra_summary = []
        self.spectrum_x_data = []
        self.spectrum_y_data = []

        if not self.samples:
            return

        self.spectrum_id_col = self._find_column(self.samples, 'sample_id', 'spectrum_id', 'id', 'Sample_ID')
        self.compound_col = self._find_column(self.samples, 'compound', 'Compound', 'mineral', 'material', 'name')
        self.confidence_col = self._find_column(self.samples, 'confidence', 'Confidence', 'match', 'quality')

        technique_col = self._find_column(self.samples, 'technique', 'instrument_type', 'instrument', 'Technique')
        if technique_col and self.samples:
            tech_val = self.samples[0].get(technique_col)
            if tech_val:
                self.technique = str(tech_val).lower()

        # Peak-list format must be extracted FIRST so spectra_summary is populated
        # before _extract_spectrum_data() tries to back-fill x/y data into it.
        if self.data_format == 'long':
            self._extract_long_format()
        elif self.data_format == 'peak_list':
            self._extract_peak_list_format()

        self._extract_spectrum_data()

    def _extract_spectrum_data(self):
        """Extract full spectrum data from JSON columns."""
        x_candidates = ['x_data', 'X_Data', 'xdata', 'wavenumber_array', 'wavelength_array']
        y_candidates = ['y_data', 'Y_Data', 'ydata', 'intensity_array', 'absorbance_array']

        for cand in x_candidates:
            self.x_data_col = self._find_column(self.samples, cand)
            if self.x_data_col:
                break

        for cand in y_candidates:
            self.y_data_col = self._find_column(self.samples, cand)
            if self.y_data_col:
                break

        self.x_label_col = self._find_column(self.samples, 'x_label', 'X_Label', 'xaxis')
        self.y_label_col = self._find_column(self.samples, 'y_label', 'Y_Label', 'yaxis')

        if not (self.x_data_col and self.y_data_col):
            return

        for i, sample in enumerate(self.samples):
            try:
                x_json = sample.get(self.x_data_col)
                y_json = sample.get(self.y_data_col)
                if x_json and y_json:
                    x_list = json.loads(x_json)
                    y_list = json.loads(y_json)
                    self.spectrum_x_data.append((i, np.array(x_list)))
                    self.spectrum_y_data.append((i, np.array(y_list)))
                    # Back-fill into spectra_summary if present
                    if i < len(self.spectra_summary):
                        self.spectra_summary[i]['x_data'] = np.array(x_list)
                        self.spectra_summary[i]['y_data'] = np.array(y_list)
            except Exception:
                pass

    def _extract_long_format(self):
        """Extract long format data."""
        x_candidates = ['wavenumber', 'wavelength', 'raman_shift', 'shift', 'nm', 'cm-1', 'cm^-1']
        y_candidates = ['absorbance', 'intensity', 'transmittance', 'counts', 'signal']

        for cand in x_candidates:
            self.x_col = self._find_column(self.samples, cand)
            if self.x_col:
                break

        for cand in y_candidates:
            self.y_col = self._find_column(self.samples, cand)
            if self.y_col:
                break

        if not self.x_col or not self.y_col:
            return

        for sample in self.samples:
            x = self._tof(sample.get(self.x_col))
            y = self._tof(sample.get(self.y_col))
            if x is not None and y is not None:
                self.x_values.append(x)
                self.y_values.append(y)

    def _extract_peak_list_format(self):
        """Extract peak list format."""
        for i, sample in enumerate(self.samples):
            spec_id = f"Spectrum {i+1}"
            if self.spectrum_id_col:
                val = sample.get(self.spectrum_id_col)
                if val:
                    spec_id = str(val)

            compound = "Unknown"
            if self.compound_col:
                val = sample.get(self.compound_col)
                if val:
                    compound = str(val)

            confidence = None
            if self.confidence_col:
                val = sample.get(self.confidence_col)
                if val:
                    confidence = val

            spectrum = {
                'index': i,
                'id': spec_id,
                'compound': compound,
                'confidence': confidence,
                'technique': self.technique or 'FTIR',
                'peaks': [],
                'raw_data': sample
            }

            if self.peak_col:
                peak_str = sample.get(self.peak_col)
                if peak_str:
                    peaks = self._parse_peak_list(peak_str)
                    if peaks:
                        spectrum['peaks'] = peaks
                        self.peak_positions.extend(peaks)

            self.spectra_summary.append(spectrum)

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
                if '%' in v:
                    v = v.replace('%', '')
                return float(v)
            return None
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Base class overrides
    # ------------------------------------------------------------------

    def _calc_summary(self, samples, columns):
        rows = []
        if not samples:
            rows.append(("Status", "No samples loaded"))
            return rows

        rows.append(("N rows", str(len(samples))))

        if self.data_format == 'peak_list':
            rows.append(("Format", "Peak List"))
            rows.append(("N spectra", str(len(self.spectra_summary))))
            if self.peak_positions:
                rows.append(("Total peaks", str(len(self.peak_positions))))
                rows.append(("Peak range",
                              f"{min(self.peak_positions):.1f} – {max(self.peak_positions):.1f} cm⁻¹"))
        elif self.data_format == 'long':
            rows.append(("Format", "Continuous"))
            if self.x_values:
                rows.append(("X range", f"{min(self.x_values):.1f} – {max(self.x_values):.1f}"))
            if self.y_values:
                rows.append(("Max intensity", f"{max(self.y_values):.4g}"))

        if self.technique:
            rows.append(("Technique", self.technique.upper()))

        return rows

    def _calc_validation(self, samples, columns):
        rows = []
        if not samples:
            rows.append((WARN_ICON, "No data"))
            return rows

        if self.data_format == 'peak_list':
            rows.append((OK_ICON, "Peak list format"))
            if self.peak_col:
                rows.append((OK_ICON, f"Peak column: {self.peak_col}"))
            if self.compound_col and self.spectra_summary:
                identified = sum(1 for s in self.spectra_summary if s['compound'] != "Unknown")
                rows.append((OK_ICON, f"{identified}/{len(self.spectra_summary)} identified"))
        elif self.data_format == 'long':
            rows.append((OK_ICON, "Continuous format"))
            if self.x_col:
                rows.append((OK_ICON, f"X-axis: {self.x_col}"))
            if self.y_col:
                rows.append((OK_ICON, f"Intensity: {self.y_col}"))
        else:
            rows.append((WARN_ICON, "Unknown data format"))

        return rows

    def _calc_quick(self, samples, columns):
        rows = []
        if self.data_format == 'peak_list':
            if self.peak_positions:
                rows.append(("Total peaks", str(len(self.peak_positions))))
            if self.spectra_summary:
                compounds = set(
                    s['compound'] for s in self.spectra_summary if s['compound'] != "Unknown"
                )
                if compounds:
                    rows.append(("Unique compounds", str(len(compounds))))
        return rows

    # ------------------------------------------------------------------
    # Custom UI elements
    # ------------------------------------------------------------------

    def _add_custom_widgets(self):
        """Add custom widgets to the scrollable frame."""
        container = self.scrollable_frame

        # Info label showing current selection state
        info_frame = ttk.Frame(container)
        info_frame.pack(fill=tk.X, padx=5, pady=5)

        self.current_spectrum_label = ttk.Label(
            info_frame,
            text="Select rows in main table to view spectra",
            font=("Segoe UI", 9, "italic")
        )
        self.current_spectrum_label.pack(side=tk.LEFT)

        # Spectrum viewer — always shown
        self.spectrum_viewer_frame = ttk.Frame(container)
        self.spectrum_viewer_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self._create_spectrum_viewer(self.spectrum_viewer_frame)

        if self.data_format == 'peak_list':
            self._create_compound_chart(container)

            self.peak_histogram_frame = ttk.Frame(container)
            self.peak_histogram_frame.pack(fill="both", expand=True, padx=5, pady=5)
            self._create_peak_histogram(self.peak_histogram_frame)

            table_frame = ttk.Frame(container)
            table_frame.pack(fill="both", expand=True, padx=5, pady=5)
            self._create_spectra_table(table_frame)

    def _create_spectrum_viewer(self, parent):
        """Create spectrum viewer showing actual waveform."""
        frame = ttk.LabelFrame(parent, text="Spectrum Viewer", padding=10)
        frame.pack(fill="both", expand=True)

        fig = Figure(figsize=(6, 4), dpi=100)
        ax = fig.add_subplot(111)

        xlabel = "Wavenumber (cm⁻¹)" if self.technique and 'ftir' in self.technique else "Wavelength (nm)"
        ylabel = "Intensity"
        ax.set_xlabel(xlabel, fontweight='bold')
        ax.set_ylabel(ylabel, fontweight='bold')
        ax.grid(True, linestyle=':', alpha=0.6)

        x_dict = dict(self.spectrum_x_data)
        y_dict = dict(self.spectrum_y_data)

        # Resolve which spec-summary indices to draw
        # selected_indices holds data-hub indices; map them to spec indices
        if self.selected_indices:
            spec_indices = {
                si for hi in self.selected_indices
                for si in [self._hub_index_to_spec_index(hi)]
                if si is not None
            }
        else:
            spec_indices = set()

        if x_dict and y_dict:
            if len(spec_indices) == 1:
                idx = next(iter(spec_indices))
                x_data = x_dict.get(idx)
                y_data = y_dict.get(idx)

                if x_data is not None and y_data is not None:
                    ax.plot(x_data, y_data, 'b-', linewidth=2.5)
                    if idx < len(self.spectra_summary):
                        spec = self.spectra_summary[idx]
                        ax.set_title(f"{spec['id']} – {spec['compound']}", fontweight='bold')
                        if spec['peaks']:
                            peak_ys = [y_data[np.argmin(np.abs(x_data - p))] for p in spec['peaks']]
                            ax.scatter(spec['peaks'], peak_ys, c='red', s=40, zorder=5, alpha=0.8)
                else:
                    ax.text(0.5, 0.5, "No spectrum data for selected row",
                            ha='center', va='center', transform=ax.transAxes)

            elif len(spec_indices) > 1:
                colors = plt.cm.tab10(np.linspace(0, 1, len(spec_indices)))
                for i, idx in enumerate(sorted(spec_indices)):
                    x_data = x_dict.get(idx)
                    y_data = y_dict.get(idx)
                    if x_data is not None and y_data is not None:
                        label = (self.spectra_summary[idx]['id']
                                 if idx < len(self.spectra_summary) else f"Spectrum {idx}")
                        ax.plot(x_data, y_data, color=colors[i], linewidth=1.5, alpha=0.8, label=label)
                if len(spec_indices) <= 8:
                    ax.legend(fontsize=8)
                ax.set_title(f"{len(spec_indices)} Selected Spectra", fontweight='bold')

            else:
                # Nothing selected — prompt user
                ax.text(0.5, 0.5, "Select a row in the main table",
                        ha='center', va='center', transform=ax.transAxes, fontsize=12)
        else:
            ax.text(0.5, 0.5, "No spectrum data available",
                    ha='center', va='center', transform=ax.transAxes, fontsize=12)

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.figures.append(canvas.figure)
        self.spectrum_viewer_canvas = canvas
        return frame

    def _create_compound_chart(self, parent):
        """Create bar chart of top compounds."""
        frame = ttk.LabelFrame(parent, text="Top Compounds", padding=10)
        frame.pack(fill="both", expand=True, padx=5, pady=5)

        fig = Figure(figsize=(5, 3), dpi=100)
        ax = fig.add_subplot(111)

        if self.compound_col and self.samples:
            compounds = [
                str(s.get(self.compound_col))
                for s in self.samples
                if s.get(self.compound_col) and str(s.get(self.compound_col)).strip()
            ]
            if compounds:
                counts = Counter(compounds)
                top = counts.most_common(10)
                names = [c[0][:15] + "…" if len(c[0]) > 15 else c[0] for c in top]
                values = [c[1] for c in top]
                y_pos = range(len(names))
                ax.barh(y_pos, values, align='center', alpha=0.7, color='steelblue')
                ax.set_yticks(y_pos)
                ax.set_yticklabels(names)
                ax.invert_yaxis()
                ax.set_xlabel('Frequency')
                ax.set_title('Most Common Compounds')
                for i, v in enumerate(values):
                    ax.text(v + 0.1, i, str(v), va='center')
            else:
                ax.text(0.5, 0.5, "No compound data", ha='center', va='center', transform=ax.transAxes)
        else:
            ax.text(0.5, 0.5, "No compound column", ha='center', va='center', transform=ax.transAxes)

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.figures.append(canvas.figure)
        self.compound_chart_canvas = canvas

    def _create_peak_histogram(self, parent_frame, selected_idx=None, selected_indices=None):
        """Create histogram of peak positions."""
        frame = ttk.LabelFrame(parent_frame, text="Peak Distribution", padding=10)
        frame.pack(fill="both", expand=True)

        fig = Figure(figsize=(5, 3), dpi=100)
        ax = fig.add_subplot(111)
        ax.set_xlabel("Wavenumber (cm⁻¹)")
        ax.set_ylabel("Frequency")
        ax.grid(True, linestyle=':', alpha=0.6)

        peaks = []
        if selected_idx is not None and selected_idx < len(self.spectra_summary):
            spec = self.spectra_summary[selected_idx]
            peaks = spec['peaks']
            title = f"Peaks: {spec['id']} – {spec['compound']} ({len(peaks)} peaks)"
        elif selected_indices is not None:
            for idx in selected_indices:
                if idx < len(self.spectra_summary):
                    peaks.extend(self.spectra_summary[idx]['peaks'])
            title = f"Selected ({len(selected_indices)} spectra, {len(peaks)} peaks)"
        else:
            for spec in self.spectra_summary:
                peaks.extend(spec['peaks'])
            title = f"All Spectra ({len(self.spectra_summary)} spectra, {len(peaks)} peaks)"

        ax.set_title(title)

        if peaks:
            ax.hist(peaks, bins=20, edgecolor='black', alpha=0.7, color='steelblue')
        else:
            ax.text(0.5, 0.5, "No peak data", ha='center', va='center', transform=ax.transAxes)

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.figures.append(canvas.figure)
        self.peak_histogram_canvas = canvas

    def _create_spectra_table(self, parent_frame):
        """Create table of spectra information."""
        frame = ttk.LabelFrame(parent_frame, text="Spectra Details", padding=10)
        frame.pack(fill="both", expand=True)

        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill="both", expand=True)

        cols = ["Index", "Sample ID", "Compound", "Confidence", "# Peaks"]
        tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=8)

        for col in cols:
            tree.heading(col, text=col)
            if col == "Index":
                tree.column(col, width=40, anchor="center")
            elif col == "# Peaks":
                tree.column(col, width=60, anchor="center")
            elif col == "Confidence":
                tree.column(col, width=70, anchor="center")
            else:
                tree.column(col, width=120, anchor="w")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        for i, spec in enumerate(self.spectra_summary):
            conf = spec['confidence'] if spec['confidence'] else "-"
            if conf and not isinstance(conf, str):
                conf = f"{conf}%"
            elif isinstance(conf, str) and '%' not in conf and conf != "-":
                try:
                    conf = f"{float(conf):.0f}%"
                except Exception:
                    pass

            tags = ('selected',) if i in self.selected_indices else ()
            tree.insert("", "end", iid=str(i), tags=tags, values=(
                str(i + 1),
                str(spec['id'])[:20],
                str(spec['compound'])[:25],
                conf,
                len(spec['peaks'])
            ))

        tree.tag_configure('selected', background='#cce5ff')
        tree.bind('<ButtonRelease-1>', lambda e: self._on_table_click(e, tree))
        self.spectra_tree = tree

    def _on_table_click(self, event, tree):
        """Handle click on spectra table → select matching row in main table."""
        item = tree.identify_row(event.y)
        if not item:
            return
        try:
            idx = int(item)
            if hasattr(self.app, 'center') and hasattr(self.app.center, 'selected_rows'):
                self.app.center.selected_rows = {idx}
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

        # Rebuild base section widgets (summary / validation / quick)
        super().refresh()

        # Rebuild custom widgets
        if hasattr(self, 'scrollable_frame'):
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()
            self._add_custom_widgets()

        # Re-apply current selection so the viewer is immediately correct
        self._update_for_selection()
