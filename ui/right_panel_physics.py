"""
Physics / Test & Measurement Right Panel
==========================================
Features:
  - Dynamic updates when rows are selected in main table
  - Scrollable interface for all content
  - Shows time and frequency domain plots
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


class PhysicsPanel(FieldPanelBase):
    PANEL_ID = "physics"
    PANEL_NAME = "Physics / Test"
    PANEL_ICON = "📡"
    DETECT_COLUMNS = ['signal', 'amplitude', 'voltage', 'current',
                      'time', 'frequency', 'power', 'acceleration',
                      'force', 'pressure', 'displacement']
    is_right_panel = True

    def __init__(self, parent, app):
        super().__init__(parent, app)

        # Initialize data storage
        self.time = []
        self.signal = []
        self.sample_rate = None
        self.samples = []
        self.point_summary = []

        # Derived values
        self.mean = None
        self.rms = None
        self.peak = None
        self.crest_factor = None
        self.snr = None
        self.dominant_freq = None

        # Selection tracking
        self.selected_indices = set()

        # UI elements
        self.current_selection_label = None
        self.time_plot_frame = None
        self.fft_plot_frame = None
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
        self._redraw_time_plot()
        self._redraw_fft_plot()
        self._update_stats_display()

    def _set_info_label(self):
        """Update selection info label."""
        if not hasattr(self, 'current_selection_label') or not self.current_selection_label:
            return

        if not self.selected_indices:
            text = "Showing: ALL data points"
            color = "black"
        elif len(self.selected_indices) == 1:
            idx = next(iter(self.selected_indices))
            if idx < len(self.point_summary):
                text = f"Showing: Point {idx+1}"
                color = "blue"
            else:
                text = "Showing: Selected point"
                color = "blue"
        else:
            text = f"Showing: {len(self.selected_indices)} selected points"
            color = "green"

        try:
            self.current_selection_label.config(text=text, foreground=color)
        except:
            pass

    def _redraw_time_plot(self):
        """Redraw time plot with current selection."""
        if not hasattr(self, 'time_plot_frame') or not self.time_plot_frame:
            return
        try:
            for widget in self.time_plot_frame.winfo_children():
                widget.destroy()
            self._create_time_plot(self.time_plot_frame)
        except:
            pass

    def _redraw_fft_plot(self):
        """Redraw FFT plot with current selection."""
        if not hasattr(self, 'fft_plot_frame') or not self.fft_plot_frame:
            return
        try:
            for widget in self.fft_plot_frame.winfo_children():
                widget.destroy()
            self._create_fft_plot(self.fft_plot_frame)
        except:
            pass

    def _update_stats_display(self):
        """Update statistics display with current selection."""
        if hasattr(self, 'stats_frame'):
            try:
                for widget in self.stats_frame.winfo_children():
                    widget.destroy()
                self._create_stats_display(self.stats_frame)
            except:
                pass

    # ------------------------------------------------------------------
    # Data extraction
    # ------------------------------------------------------------------
    def _extract_data(self):
        """Extract time-series data from samples."""
        self.time = []
        self.signal = []
        self.sample_rate = None
        self.point_summary = []

        if not self.samples:
            return

        # Find columns
        time_col = self._find_column(self.samples, 'time', 't', 'timestamp')
        signal_col = self._find_column(self.samples, 'signal', 'amplitude',
                                       'voltage', 'current', 'acceleration',
                                       'force', 'pressure', 'displacement')

        if not signal_col:
            return

        # Extract data
        for i, sample in enumerate(self.samples):
            point = {
                'index': i,
                'id': sample.get('Sample_ID', f"Point {i+1}"),
                'signal': None,
                'time': None,
                'raw_data': sample
            }

            s = self._tof(sample.get(signal_col))
            if s is not None:
                self.signal.append(s)
                point['signal'] = s

            # Extract time data if available
            if time_col:
                t = self._tof(sample.get(time_col))
                if t is not None:
                    self.time.append(t)
                    point['time'] = t

            self.point_summary.append(point)

        # Calculate sample rate from time differences
        if len(self.time) > 1:
            time_diffs = np.diff(self.time)
            mean_dt = np.mean(time_diffs)
            if mean_dt > 0:
                self.sample_rate = 1.0 / mean_dt

        # Calculate statistics on filtered data
        self._calculate_stats()

    def _calculate_stats(self):
        """Calculate signal statistics based on selection."""
        # Get signal data based on selection
        signal_vals = []

        indices = self.selected_indices if self.selected_indices else range(len(self.point_summary))

        for idx in indices:
            if idx >= len(self.point_summary):
                continue
            point = self.point_summary[idx]
            if point['signal'] is not None:
                signal_vals.append(point['signal'])

        if not signal_vals:
            self.mean = self.rms = self.peak = self.crest_factor = self.snr = None
            return

        signal_array = np.array(signal_vals)

        # Basic stats
        self.mean = np.mean(signal_array)
        self.rms = np.sqrt(np.mean(signal_array**2))
        self.peak = np.max(np.abs(signal_array))

        # Crest factor
        if self.rms > 0:
            self.crest_factor = self.peak / self.rms

        # Estimate SNR (simplified)
        noise_std = np.std(signal_array)
        if noise_std > 0 and self.peak > noise_std * 3:
            self.snr = 20 * math.log10(self.peak / noise_std)

        # Dominant frequency (if we have time data and enough points)
        if len(signal_vals) > 10 and self.sample_rate and not self.selected_indices:
            # Only calculate on full dataset for now
            try:
                from scipy import signal as scipy_signal
                frequencies, power = scipy_signal.periodogram(
                    np.array(self.signal), fs=self.sample_rate
                )
                dominant_idx = np.argmax(power[1:]) + 1  # Skip DC
                self.dominant_freq = frequencies[dominant_idx]
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

        if self.signal:
            rows.append(("Signal range", f"{min(self.signal):.3g} - {max(self.signal):.3g}"))

        if self.sample_rate:
            rows.append(("Sample rate", f"{self.sample_rate:.1f} Hz"))

        if self.time and len(self.time) > 1:
            duration = max(self.time) - min(self.time)
            rows.append(("Duration", f"{duration:.3f} s"))

        return rows

    def _calc_validation(self, samples, columns):
        """Data validation."""
        rows = []

        if not samples:
            rows.append((WARN_ICON, "No data"))
            return rows

        # Check for signal column
        signal_col = self._find_column(samples, 'signal', 'amplitude',
                                      'voltage', 'current')
        if signal_col:
            rows.append((OK_ICON, f"Signal: {signal_col}"))
        else:
            rows.append((ERROR_ICON, "No signal column"))

        # Check for missing values
        if self.signal:
            missing = len(samples) - len(self.signal)
            if missing == 0:
                rows.append((OK_ICON, "Complete data"))
            else:
                rows.append((WARN_ICON, f"{missing} missing values"))

        return rows

    def _calc_quick(self, samples, columns):
        """Quick calculations."""
        rows = []

        if self.mean is not None:
            rows.append(("Mean", f"{self.mean:.4g}"))

        if self.rms is not None:
            rows.append(("RMS", f"{self.rms:.4g}"))

        if self.peak is not None:
            rows.append(("Peak", f"{self.peak:.4g}"))

        if self.crest_factor is not None:
            status = " ⚠" if self.crest_factor > 3 else ""
            rows.append(("Crest factor", f"{self.crest_factor:.2f}{status}"))

        if self.snr is not None:
            rows.append(("SNR", f"{self.snr:.1f} dB"))

        if self.dominant_freq is not None:
            rows.append(("Dominant freq", f"{self.dominant_freq:.1f} Hz"))

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
            text="Select rows in main table to filter data points",
            font=("Segoe UI", 9, "italic")
        )
        self.current_selection_label.pack(side=tk.LEFT)

        # Time plot
        self.time_plot_frame = ttk.Frame(container)
        self.time_plot_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self._create_time_plot(self.time_plot_frame)

        # FFT plot
        self.fft_plot_frame = ttk.Frame(container)
        self.fft_plot_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self._create_fft_plot(self.fft_plot_frame)

        # Statistics display
        self.stats_frame = ttk.Frame(container)
        self.stats_frame.pack(fill="x", padx=5, pady=5)
        self._create_stats_display(self.stats_frame)

        # Data table
        self._create_data_table(container)

    def _create_time_plot(self, parent):
        """Create time-domain plot."""
        frame = ttk.LabelFrame(parent, text="Time Domain", padding=10)
        frame.pack(fill="both", expand=True)

        fig = Figure(figsize=(5, 3), dpi=100)
        ax = fig.add_subplot(111)

        ax.set_xlabel("Time (s)" if self.time else "Sample")
        ax.set_ylabel("Amplitude")
        ax.set_title("Signal Waveform")
        ax.grid(True, linestyle=':', alpha=0.6)

        # Filter data based on selection
        times = []
        signals = []

        indices = self.selected_indices if self.selected_indices else range(len(self.point_summary))

        for idx in indices:
            if idx >= len(self.point_summary):
                continue
            point = self.point_summary[idx]
            if point['signal'] is not None:
                if point['time'] is not None:
                    times.append(point['time'])
                signals.append(point['signal'])

        if signals:
            x = times if times and len(times) == len(signals) else range(len(signals))

            if self.selected_indices:
                ax.plot(x, signals, 'r-', linewidth=1.5, alpha=0.7, marker='o', markersize=4, label='Selected')
            else:
                ax.plot(x, signals, 'b-', linewidth=1.5, alpha=0.7, label='All')
            ax.legend()

            # Add mean line
            if self.mean is not None:
                ax.axhline(y=self.mean, color='gray', linestyle='--',
                          alpha=0.5, label=f'Mean = {self.mean:.3g}')

            # Add peak markers
            if signals:
                max_idx = np.argmax(signals)
                min_idx = np.argmin(signals)
                ax.plot(x[max_idx], signals[max_idx], 'ro', markersize=6)
                ax.plot(x[min_idx], signals[min_idx], 'go', markersize=6)
        else:
            ax.text(0.5, 0.5, "No signal data", ha='center', va='center',
                   transform=ax.transAxes, fontsize=12)

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.figures.append(fig)

    def _create_fft_plot(self, parent):
        """Create frequency domain plot."""
        frame = ttk.LabelFrame(parent, text="Frequency Domain", padding=10)
        frame.pack(fill="both", expand=True)

        fig = Figure(figsize=(5, 3), dpi=100)
        ax = fig.add_subplot(111)

        # Only calculate FFT on full dataset if no selection
        if not self.selected_indices and len(self.signal) > 10 and self.sample_rate:
            try:
                from scipy import signal as scipy_signal
                frequencies, power = scipy_signal.periodogram(
                    np.array(self.signal), fs=self.sample_rate
                )

                ax.semilogy(frequencies[1:], power[1:], 'b-', linewidth=1.5)
                ax.set_xlabel("Frequency (Hz)")
                ax.set_ylabel("Power Spectral Density")
                ax.set_title("Frequency Spectrum")
                ax.grid(True, linestyle=':', alpha=0.6)

                if self.dominant_freq:
                    ax.axvline(x=self.dominant_freq, color='r', linestyle='--',
                              alpha=0.7, label=f'Dominant: {self.dominant_freq:.1f} Hz')
                    ax.legend()
            except:
                ax.text(0.5, 0.5, "FFT failed", ha='center', va='center',
                       transform=ax.transAxes, fontsize=12)
        else:
            msg = "Need full dataset for FFT" if self.selected_indices else "Need more data for FFT"
            ax.text(0.5, 0.5, msg, ha='center', va='center',
                   transform=ax.transAxes, fontsize=12)

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.figures.append(fig)

    def _create_stats_display(self, parent):
        """Create statistics display panel."""
        frame = ttk.LabelFrame(parent, text="Signal Statistics", padding=10)
        frame.pack(fill="x")

        # Create a grid of statistics
        stats_frame = ttk.Frame(frame)
        stats_frame.pack(fill="x")

        stats = [
            ("Mean", f"{self.mean:.4g}" if self.mean is not None else "N/A"),
            ("RMS", f"{self.rms:.4g}" if self.rms is not None else "N/A"),
            ("Peak", f"{self.peak:.4g}" if self.peak is not None else "N/A"),
            ("Peak-Peak", f"{2*self.peak:.4g}" if self.peak else "N/A"),
            ("Crest Factor", f"{self.crest_factor:.2f}" if self.crest_factor else "N/A"),
            ("SNR", f"{self.snr:.1f} dB" if self.snr else "N/A"),
            ("Sample Rate", f"{self.sample_rate:.1f} Hz" if self.sample_rate else "N/A"),
            ("Dominant Freq", f"{self.dominant_freq:.1f} Hz" if self.dominant_freq else "N/A"),
        ]

        # Display in two columns
        left_col = ttk.Frame(stats_frame)
        left_col.pack(side=tk.LEFT, fill="both", expand=True, padx=5)

        right_col = ttk.Frame(stats_frame)
        right_col.pack(side=tk.RIGHT, fill="both", expand=True, padx=5)

        for i, (name, value) in enumerate(stats):
            col = left_col if i % 2 == 0 else right_col
            row = ttk.Frame(col)
            row.pack(fill="x", pady=2)

            ttk.Label(row, text=f"{name}:", font=("Segoe UI", 9, "bold"),
                     width=12, anchor="w").pack(side=tk.LEFT)
            ttk.Label(row, text=value, width=12, anchor="w").pack(side=tk.LEFT)

    def _create_data_table(self, parent):
        """Create table of data points."""
        frame = ttk.LabelFrame(parent, text="Data Points", padding=10)
        frame.pack(fill="x", padx=5, pady=5)

        cols = ["ID", "Time (s)", "Signal"]
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=6)

        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor="center")

        # Filter data based on selection
        indices = self.selected_indices if self.selected_indices else range(len(self.point_summary))

        for i in sorted(indices)[:20]:  # Limit to 20 rows
            if i >= len(self.point_summary):
                continue

            point = self.point_summary[i]

            pid = point['id'][:8]
            time = f"{point['time']:.3f}" if point['time'] is not None else "-"
            signal = f"{point['signal']:.4g}" if point['signal'] is not None else "-"

            tree.insert("", "end", values=(pid, time, signal))

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
            if idx < len(self.point_summary):
                hub_idx = self.point_summary[idx]['index']
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
