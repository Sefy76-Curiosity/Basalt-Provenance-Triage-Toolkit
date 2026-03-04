"""
Zooarchaeology Right Panel
============================
Features:
  - Dynamic updates when rows are selected in main table
  - Compact header with key metrics
  - Small abundance chart (top 5 taxa)
  - Carousel for rotating insights (3 cards)
  - Controls at bottom
"""

import tkinter as tk
from tkinter import ttk
import numpy as np
import math
from collections import Counter
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from .right_panel import FieldPanelBase, OK_ICON, WARN_ICON, ERROR_ICON, INFO_ICON


class ZooarchPanel(FieldPanelBase):
    PANEL_ID = "zooarchaeology"
    PANEL_NAME = "Zooarchaeology"
    PANEL_ICON = "🦴"
    DETECT_COLUMNS = ['taxon', 'taxa', 'nisp', 'mni', 'element',
                      'side', 'skeletal', 'species', 'bone',
                      'd13c', 'd15n', 'collagen', 'ftir', 'crystallinity']
    is_right_panel = True

    def __init__(self, parent, app):
        super().__init__(parent, app)

        # Initialize data storage
        self.taxa = []
        self.nisp_by_taxon = Counter()
        self.elements = []
        self.sides = []
        self.modifications = []
        self.samples = []
        self.specimen_summary = []

        # Selection tracking
        self.selected_indices = set()

        # UI elements
        self.header_frame = None
        self.abundance_frame = None
        self.figures = []

        # Carousel state
        self.current_card_index = 0
        self.carousel_paused = False
        self.cards = []
        self.card_timer = None

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
        self._update_header()
        self._create_abundance_chart(self.abundance_frame)
        self._update_cards_data()

    def _update_header(self):
        """Update compact header with key metrics."""
        if not hasattr(self, 'header_frame') or not self.header_frame:
            return

        try:
            # Clear header
            for widget in self.header_frame.winfo_children():
                widget.destroy()

            # Line 1: Selection info
            if not self.selected_indices:
                text = f"🦴 ZOOARCH · {len(self.specimen_summary)} specimens · {len(self.nisp_by_taxon)} taxa"
            elif len(self.selected_indices) == 1:
                idx = next(iter(self.selected_indices))
                if idx < len(self.specimen_summary):
                    text = f"🦴 Specimen: {self.specimen_summary[idx].get('id', idx+1)}"
                else:
                    text = "🦴 Selected specimen"
            else:
                text = f"🦴 {len(self.selected_indices)} selected specimens"

            line1 = ttk.Label(self.header_frame, text=text, font=("Segoe UI", 9, "bold"))
            line1.pack(anchor="w")

            # Line 2: Key metrics
            H, J, S = self._calculate_diversity()
            total_nisp = sum(self.nisp_by_taxon.values())
            mni = self._estimate_mni()

            metrics = []
            if H is not None:
                metrics.append(f"H':{H:.2f}")
            metrics.append(f"NISP:{total_nisp}")
            metrics.append(f"MNI:{mni}")
            if mni > 0:
                metrics.append(f"R:{total_nisp/mni:.1f}")

            line2 = ttk.Label(self.header_frame, text="  ".join(metrics), font=("Segoe UI", 8))
            line2.pack(anchor="w")

        except Exception as e:
            print(f"Header update error: {e}")

    # ------------------------------------------------------------------
    # Data extraction
    # ------------------------------------------------------------------
    def _extract_data(self):
        """Extract zooarchaeological data from samples."""
        self.taxa = []
        self.nisp_by_taxon = Counter()
        self.elements = []
        self.sides = []
        self.modifications = []
        self.specimen_summary = []

        if not self.samples:
            return

        # Find columns
        taxon_col = self._find_column(self.samples, 'taxon', 'taxa', 'species')
        nisp_col = self._find_column(self.samples, 'nisp', 'count')
        element_col = self._find_column(self.samples, 'element', 'bone')
        side_col = self._find_column(self.samples, 'side')
        mod_col = self._find_column(self.samples, 'modification', 'taphonomy')

        # Isotope-related columns
        d13c_col = self._find_column(self.samples, 'd13c', 'δ13c', 'delta13c')
        d15n_col = self._find_column(self.samples, 'd15n', 'δ15n', 'delta15n')
        collagen_col = self._find_column(self.samples, 'collagen', 'collagen_yield')
        ftir_col = self._find_column(self.samples, 'ftir', 'crystallinity')

        # Age-related columns
        age_col = self._find_column(self.samples, 'age', 'age_stage', 'fusion')

        # Taphonomy columns
        burning_col = self._find_column(self.samples, 'burning', 'burn')
        butchery_col = self._find_column(self.samples, 'butchery', 'cutmarks')
        gnawing_col = self._find_column(self.samples, 'gnawing', 'gnaw')

        for i, sample in enumerate(self.samples):
            specimen = {
                'index': i,
                'id': sample.get('Sample_ID', f"Specimen {i+1}"),
                'taxon': None,
                'nisp': 1,
                'element': None,
                'side': None,
                'modification': None,
                'has_d13c': False,
                'has_d15n': False,
                'has_collagen': False,
                'has_ftir': False,
                'age_stage': None,
                'burning': None,
                'butchery': None,
                'gnawing': None,
                'raw_data': sample
            }

            # Taxon
            if taxon_col:
                taxon = sample.get(taxon_col)
                if taxon and str(taxon).strip():
                    self.taxa.append(str(taxon))
                    specimen['taxon'] = str(taxon)

                    # NISP
                    nisp = 1
                    if nisp_col:
                        try:
                            nisp_val = sample.get(nisp_col)
                            if nisp_val is not None:
                                nisp = int(float(nisp_val))
                        except:
                            pass
                    specimen['nisp'] = nisp
                    self.nisp_by_taxon[str(taxon)] += nisp

            # Element
            if element_col:
                element = sample.get(element_col)
                if element:
                    self.elements.append(str(element))
                    specimen['element'] = str(element)

            # Side
            if side_col:
                side = sample.get(side_col)
                if side:
                    self.sides.append(str(side).lower())
                    specimen['side'] = str(side)

            # Modifications
            if mod_col:
                mod = sample.get(mod_col)
                if mod:
                    self.modifications.append(str(mod))
                    specimen['modification'] = str(mod)

            # Isotope data
            if d13c_col:
                val = sample.get(d13c_col)
                specimen['has_d13c'] = val is not None and str(val).strip()

            if d15n_col:
                val = sample.get(d15n_col)
                specimen['has_d15n'] = val is not None and str(val).strip()

            if collagen_col:
                val = sample.get(collagen_col)
                specimen['has_collagen'] = val is not None and str(val).strip()

            if ftir_col:
                val = sample.get(ftir_col)
                specimen['has_ftir'] = val is not None and str(val).strip()

            # Age data
            if age_col:
                val = sample.get(age_col)
                if val:
                    specimen['age_stage'] = str(val).lower()

            # Taphonomy data
            if burning_col:
                val = sample.get(burning_col)
                if val:
                    specimen['burning'] = str(val)

            if butchery_col:
                val = sample.get(butchery_col)
                if val:
                    specimen['butchery'] = str(val)

            if gnawing_col:
                val = sample.get(gnawing_col)
                if val:
                    specimen['gnawing'] = str(val)

            self.specimen_summary.append(specimen)

    def _calculate_diversity(self):
        """Calculate Shannon diversity index based on selection."""
        # Get NISP counts based on selection
        nisp_counts = Counter()

        indices = self.selected_indices if self.selected_indices else range(len(self.specimen_summary))

        for idx in indices:
            if idx >= len(self.specimen_summary):
                continue
            spec = self.specimen_summary[idx]
            if spec['taxon']:
                nisp_counts[spec['taxon']] += spec['nisp']

        total_nisp = sum(nisp_counts.values())
        if total_nisp == 0:
            return None, None, 0

        # Shannon index H' = -Σ p_i * ln(p_i)
        H = 0
        for count in nisp_counts.values():
            p = count / total_nisp
            if p > 0:
                H -= p * math.log(p)

        # Evenness J = H' / ln(S)
        S = len(nisp_counts)
        J = H / math.log(S) if S > 1 else 1

        return H, J, S

    def _estimate_mni(self):
        """Estimate Minimum Number of Individuals."""
        # Simplified MNI based on unique specimens
        return len(self.selected_indices) if self.selected_indices else len(self.specimen_summary)

    def _tof(self, v):
        try:
            if v is None:
                return None
            return float(v)
        except:
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
        rows.append(("N specimens", str(n)))

        # Total NISP
        total_nisp = sum(self.nisp_by_taxon.values())
        rows.append(("Total NISP", str(total_nisp)))

        # Number of taxa
        n_taxa = len(self.nisp_by_taxon)
        rows.append(("N taxa (richness)", str(n_taxa)))

        # Most abundant taxon
        if self.nisp_by_taxon:
            most_common = self.nisp_by_taxon.most_common(1)[0]
            rows.append(("Top taxon", f"{most_common[0]} ({most_common[1]})"))

        return rows

    def _calc_validation(self, samples, columns):
        """Data validation."""
        rows = []

        if not samples:
            rows.append((WARN_ICON, "No data"))
            return rows

        # Check for taxon column
        taxon_col = self._find_column(samples, 'taxon', 'taxa', 'species')
        if taxon_col:
            rows.append((OK_ICON, f"Taxon column: {taxon_col}"))

            # Check for missing taxa
            missing = sum(1 for s in samples if not s.get(taxon_col))
            if missing == 0:
                rows.append((OK_ICON, "All specimens identified"))
            else:
                rows.append((WARN_ICON, f"{missing} unidentified specimens"))
        else:
            rows.append((ERROR_ICON, "No taxon column"))

        return rows

    def _calc_quick(self, samples, columns):
        """Quick calculations - diversity and MNI."""
        rows = []

        # Shannon diversity
        H, J, S = self._calculate_diversity()
        if H is not None:
            rows.append(("Shannon H'", f"{H:.3f}"))
            if J is not None:
                rows.append(("Evenness J", f"{J:.3f}"))
            rows.append(("Richness S", str(S)))

        # MNI estimate
        mni = self._estimate_mni()
        rows.append(("MNI estimate", str(mni)))

        # NISP/MNI ratio
        total_nisp = 0
        indices = self.selected_indices if self.selected_indices else range(len(self.specimen_summary))
        for idx in indices:
            if idx < len(self.specimen_summary):
                total_nisp += self.specimen_summary[idx]['nisp']

        if mni > 0:
            rows.append(("NISP/MNI", f"{total_nisp/mni:.1f}"))

        return rows

    # ------------------------------------------------------------------
    # Custom UI elements
    # ------------------------------------------------------------------
    def _add_custom_widgets(self):
        """Add custom widgets to the scrollable frame."""
        container = self.scrollable_frame

        # COMPACT HEADER (two lines)
        self.header_frame = ttk.Frame(container)
        self.header_frame.pack(fill=tk.X, padx=5, pady=2)

        # SMALL ABUNDANCE CHART (top 5 taxa, horizontal)
        self.abundance_frame = ttk.Frame(container)
        self.abundance_frame.pack(fill="x", padx=5, pady=2)
        self._create_abundance_chart(self.abundance_frame)

        # CAROUSEL SECTION
        carousel_container = ttk.LabelFrame(container, text="Quick Insights", padding=5)
        carousel_container.pack(fill="x", padx=5, pady=2)

        # Card display area
        self.card_area = ttk.Frame(carousel_container, height=100)
        self.card_area.pack(fill="x", pady=2)
        self.card_area.pack_propagate(False)

        # Create cards (3 condensed cards)
        self._create_cards()

        # CAROUSEL CONTROLS (at bottom)
        self._add_carousel_controls(carousel_container)

        # Start carousel
        self._start_carousel()

    def _create_cards(self):
        """Create 3 condensed rotating cards."""
        self.cards = []

        # Card 1: ISOTOPE & PRESERVATION (TDF focus)
        card1 = ttk.Frame(self.card_area)
        ttk.Label(card1, text="🔬 ISOTOPE & PRESERVATION",
                 font=("Segoe UI", 8, "bold"), foreground="#2c3e50").pack(anchor="w")

        self.card1_isotope_ready = ttk.Label(card1, text="• Loading...", font=("Segoe UI", 7))
        self.card1_isotope_ready.pack(anchor="w")

        self.card1_collagen = ttk.Label(card1, text="• Loading...", font=("Segoe UI", 7))
        self.card1_collagen.pack(anchor="w")

        self.card1_tdf = ttk.Label(card1, text="• TDF taxa: Loading...", font=("Segoe UI", 7))
        self.card1_tdf.pack(anchor="w")

        # Card 2: TAPHONOMY & AGE
        card2 = ttk.Frame(self.card_area)
        ttk.Label(card2, text="🔥 TAPHONOMY & AGE",
                 font=("Segoe UI", 8, "bold"), foreground="#2c3e50").pack(anchor="w")

        self.card2_age = ttk.Label(card2, text="• Age: Loading...", font=("Segoe UI", 7))
        self.card2_age.pack(anchor="w")

        self.card2_taph = ttk.Label(card2, text="• Taph: Loading...", font=("Segoe UI", 7))
        self.card2_taph.pack(anchor="w")

        self.card2_weather = ttk.Label(card2, text="• Weather: Loading...", font=("Segoe UI", 7))
        self.card2_weather.pack(anchor="w")

        # Card 3: TAXON SPOTLIGHT
        card3 = ttk.Frame(self.card_area)
        ttk.Label(card3, text="🦌 TAXON SPOTLIGHT",
                 font=("Segoe UI", 8, "bold"), foreground="#2c3e50").pack(anchor="w")

        self.card3_common = ttk.Label(card3, text="• Most common: Loading...", font=("Segoe UI", 7))
        self.card3_common.pack(anchor="w")

        self.card3_rare = ttk.Label(card3, text="• Rare: Loading...", font=("Segoe UI", 7))
        self.card3_rare.pack(anchor="w")

        self.card3_richness = ttk.Label(card3, text="• Richness: Loading...", font=("Segoe UI", 7))
        self.card3_richness.pack(anchor="w")

        self.cards = [card1, card2, card3]

        # Initially show first card
        if self.cards:
            self.cards[0].pack(fill="both", expand=True)

        # Update card data
        self._update_cards_data()

    def _add_carousel_controls(self, parent):
        """Add prev/pause/next controls at bottom."""
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill="x", pady=2, side=tk.BOTTOM)

        # Center the controls
        control_frame.columnconfigure(0, weight=1)
        control_frame.columnconfigure(1, weight=1)
        control_frame.columnconfigure(2, weight=1)

        self.prev_btn = ttk.Button(control_frame, text="◀ Prev",
                                   command=self._prev_card, width=6)
        self.prev_btn.grid(row=0, column=0, padx=2)

        self.pause_btn = ttk.Button(control_frame, text="⏸ Pause",
                                    command=self._toggle_pause, width=6)
        self.pause_btn.grid(row=0, column=1, padx=2)

        self.next_btn = ttk.Button(control_frame, text="▶ Next",
                                   command=self._next_card, width=6)
        self.next_btn.grid(row=0, column=2, padx=2)

    def _show_card(self, index):
        """Show card at index, hide others."""
        if not self.cards:
            return

        # Hide all cards
        for card in self.cards:
            card.pack_forget()

        # Show selected card
        self.cards[index].pack(fill="both", expand=True)
        self.current_card_index = index

    def _next_card(self):
        """Show next card."""
        if not self.cards:
            return
        next_idx = (self.current_card_index + 1) % len(self.cards)
        self._show_card(next_idx)
        self._restart_carousel()

    def _prev_card(self):
        """Show previous card."""
        if not self.cards:
            return
        prev_idx = (self.current_card_index - 1) % len(self.cards)
        self._show_card(prev_idx)
        self._restart_carousel()

    def _toggle_pause(self):
        """Pause or resume carousel."""
        self.carousel_paused = not self.carousel_paused

        if self.carousel_paused:
            self.pause_btn.config(text="▶ Resume")
            if self.card_timer:
                self.frame.after_cancel(self.card_timer)
                self.card_timer = None
        else:
            self.pause_btn.config(text="⏸ Pause")
            self._schedule_next_card()

    def _start_carousel(self):
        """Start the automatic rotation."""
        self._schedule_next_card()

    def _restart_carousel(self):
        """Restart the timer after manual navigation."""
        if self.card_timer:
            self.frame.after_cancel(self.card_timer)
            self.card_timer = None
        if not self.carousel_paused:
            self._schedule_next_card()

    def _schedule_next_card(self):
        """Schedule the next card rotation."""
        if self.carousel_paused or not self.cards:
            return
        self.card_timer = self.frame.after(3000, self._rotate_card)  # 3 seconds

    def _rotate_card(self):
        """Rotate to next card if not paused."""
        if not self.carousel_paused and self.cards:
            next_idx = (self.current_card_index + 1) % len(self.cards)
            self._show_card(next_idx)
            self._schedule_next_card()

    def _update_cards_data(self):
        """Update card content with current data."""
        indices = self.selected_indices if self.selected_indices else range(len(self.specimen_summary))

        # Card 1: Isotope & Preservation
        collagen_count = sum(1 for i in indices if i < len(self.specimen_summary) and
                            self.specimen_summary[i].get('has_collagen', False))
        d13c_count = sum(1 for i in indices if i < len(self.specimen_summary) and
                        self.specimen_summary[i].get('has_d13c', False))

        # Collagen quality
        collagen_good = sum(1 for i in indices if i < len(self.specimen_summary) and
                           self.specimen_summary[i].get('has_collagen', False))
        collagen_poor = len(indices) - collagen_good

        # Get unique taxa in selection
        taxa_in_selection = set()
        for i in indices:
            if i < len(self.specimen_summary):
                taxon = self.specimen_summary[i].get('taxon')
                if taxon:
                    taxa_in_selection.add(taxon)

        taxa_list = ", ".join(list(taxa_in_selection)[:3])
        if len(taxa_in_selection) > 3:
            taxa_list += f" +{len(taxa_in_selection)-3} more"

        isotope_ready = collagen_count if collagen_count > 0 else d13c_count

        self.card1_isotope_ready.config(
            text=f"• Isotope-ready: {isotope_ready}/{len(indices)}"
        )
        self.card1_collagen.config(
            text=f"• Collagen: Good {collagen_good} | Poor {collagen_poor}"
        )
        self.card1_tdf.config(
            text=f"• TDF taxa: {taxa_list if taxa_list else 'none'}"
        )

        # Card 2: Taphonomy & Age
        # Age - count juvenile vs adult
        juvenile_keywords = ['juv', 'young', 'unfused', 'neonate']
        juvenile = 0
        adult = 0
        for i in indices:
            if i < len(self.specimen_summary):
                age = self.specimen_summary[i].get('age_stage', '')
                if age and any(k in str(age).lower() for k in juvenile_keywords):
                    juvenile += 1
                elif age:
                    adult += 1

        if juvenile + adult > 0:
            pct_juv = (juvenile / (juvenile + adult)) * 100
            self.card2_age.config(text=f"• Age: {pct_juv:.0f}% Juv / {100-pct_juv:.0f}% Adult")
        else:
            self.card2_age.config(text="• Age: No data")

        # Taph - count modifications
        burning = sum(1 for i in indices if i < len(self.specimen_summary) and
                     self.specimen_summary[i].get('burning'))
        butchery = sum(1 for i in indices if i < len(self.specimen_summary) and
                      self.specimen_summary[i].get('butchery'))
        gnawing = sum(1 for i in indices if i < len(self.specimen_summary) and
                     self.specimen_summary[i].get('gnawing'))

        self.card2_taph.config(
            text=f"• Taph: 🔥{burning} 🥩{butchery} 🐕{gnawing}"
        )

        # Weathering stages
        weathering_counts = {'1':0, '2':0, '3':0, '4':0, '5':0}
        for i in indices:
            if i < len(self.specimen_summary):
                mod = self.specimen_summary[i].get('modification', '')
                if 'weather' in str(mod).lower():
                    for stage in weathering_counts:
                        if f'stage{stage}' in str(mod).lower():
                            weathering_counts[stage] += 1
                            break

        weather_str = " ".join([f"S{s}:{c}" for s, c in weathering_counts.items() if c > 0])
        self.card2_weather.config(text=f"• Weather: {weather_str if weather_str else 'No data'}")

        # Card 3: Taxon Spotlight
        taxon_counts = Counter()
        for i in indices:
            if i < len(self.specimen_summary):
                taxon = self.specimen_summary[i].get('taxon')
                if taxon:
                    taxon_counts[taxon] += self.specimen_summary[i].get('nisp', 1)

        if taxon_counts:
            most_common = taxon_counts.most_common(1)[0]
            self.card3_common.config(text=f"• Most common: {most_common[0]} ({most_common[1]})")

            rare = [t for t, c in taxon_counts.items() if c <= 2][:3]
            if rare:
                self.card3_rare.config(text=f"• Rare: {', '.join(rare)}")
            else:
                self.card3_rare.config(text="• Rare: None")

            self.card3_richness.config(text=f"• Richness: {len(taxon_counts)} taxa")
        else:
            self.card3_common.config(text="• Most common: No data")
            self.card3_rare.config(text="• Rare: No data")
            self.card3_richness.config(text="• Richness: 0")

    def _create_abundance_chart(self, parent):
        """Create small horizontal bar chart of top 5 taxa."""
        # Clear existing chart
        for widget in parent.winfo_children():
            widget.destroy()

        frame = ttk.LabelFrame(parent, text="Top 5 Taxa", padding=5)
        frame.pack(fill="x")

        fig = Figure(figsize=(5, 1.5), dpi=100)
        ax = fig.add_subplot(111)

        # Get NISP counts based on selection
        nisp_counts = Counter()

        indices = self.selected_indices if self.selected_indices else range(len(self.specimen_summary))

        for idx in indices:
            if idx >= len(self.specimen_summary):
                continue
            spec = self.specimen_summary[idx]
            if spec['taxon']:
                nisp_counts[spec['taxon']] += spec['nisp']

        if nisp_counts:
            # Get top 5 taxa
            top_taxa = nisp_counts.most_common(5)
            names = [t[0][:10] + "..." if len(t[0]) > 10 else t[0] for t in top_taxa]
            counts = [t[1] for t in top_taxa]

            y_pos = range(len(names))
            ax.barh(y_pos, counts, align='center', alpha=0.7, color='steelblue', height=0.5)
            ax.set_yticks(y_pos)
            ax.set_yticklabels(names, fontsize=7)
            ax.invert_yaxis()
            ax.set_xlabel('NISP', fontsize=7)
            ax.tick_params(axis='x', labelsize=7)

            # Add value labels
            for i, v in enumerate(counts):
                ax.text(v + 0.5, i, str(v), va='center', fontsize=7)
        else:
            ax.text(0.5, 0.5, "No abundance data", ha='center', va='center',
                   transform=ax.transAxes, fontsize=8)

        fig.tight_layout(pad=1.0)
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="x", expand=True)
        self.figures.append(fig)

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

    def destroy(self):
        """Clean up resources."""
        if self.card_timer:
            self.frame.after_cancel(self.card_timer)
        for fig in self.figures:
            try:
                plt.close(fig)
            except:
                pass
        super().destroy()
