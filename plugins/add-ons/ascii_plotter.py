"""
ASCII Plotter - UI Add-on
Text-based plotting for CLI users
Category: add-ons (provides PLOT_TYPES)
"""
import tkinter as tk
from tkinter import scrolledtext

PLUGIN_INFO = {
    'id': 'ascii_plotter',
    'name': 'ASCII Plotter (CLI)',
    'category': 'add-ons',
    'icon': '📟',
    'version': '2.0',
    'requires': [],
    'description': 'Text-based plots (no graphics libraries needed)'
}

def plot_ascii(frame, samples):
    """Draw ASCII histogram inside the given tkinter frame."""
    for widget in frame.winfo_children():
        widget.destroy()

    text_widget = scrolledtext.ScrolledText(frame,
                                             font=("Courier", 9),
                                             bg='black', fg='lime')
    text_widget.pack(fill=tk.BOTH, expand=True)

    if not samples:
        text_widget.insert('1.0', "No data to plot")
        return

    # Extract ratios
    zr_nb = []
    for s in samples:
        try:
            zr = float(s.get('Zr_ppm', 0))
            nb = float(s.get('Nb_ppm', 1))
            if zr > 0 and nb > 0:
                zr_nb.append(zr/nb)
        except:
            pass

    if not zr_nb:
        text_widget.insert('1.0', "No valid ratio data")
        return

    # Create ASCII histogram
    output = []
    output.append("=" * 70)
    output.append("  Zr/Nb DISTRIBUTION (ASCII HISTOGRAM)")
    output.append("=" * 70)
    output.append("")

    bins = 15
    max_val = max(zr_nb)
    min_val = min(zr_nb)
    bin_size = (max_val - min_val) / bins if max_val > min_val else 1

    counts = [0] * bins
    for val in zr_nb:
        bin_idx = int((val - min_val) / bin_size) if bin_size > 0 else 0
        if 0 <= bin_idx < bins:
            counts[bin_idx] += 1

    max_count = max(counts) if counts else 1
    scale = 50 / max_count if max_count > 0 else 1

    for i, count in enumerate(counts):
        bin_start = min_val + i * bin_size
        bin_end = bin_start + bin_size
        bar = '█' * int(count * scale)
        output.append(f"{bin_start:6.1f}-{bin_end:6.1f} | {bar} ({count})")

    output.append("")
    output.append(f"Total samples: {len(zr_nb)}")
    output.append(f"Range: {min_val:.2f} - {max_val:.2f}")
    output.append(f"Mean: {sum(zr_nb)/len(zr_nb):.2f}")
    output.append("=" * 70)

    # Statistics
    output.append("")
    output.append("CLASSIFICATION DISTRIBUTION:")
    output.append("-" * 70)

    classifications = {}
    for s in samples:
        cls = s.get('Auto_Classification', 'UNCLASSIFIED')
        classifications[cls] = classifications.get(cls, 0) + 1

    for cls, count in sorted(classifications.items(), key=lambda x: -x[1]):
        bar = '▓' * int((count / len(samples)) * 40)
        pct = (count / len(samples)) * 100
        output.append(f"{cls:30s} | {bar} {count:3d} ({pct:5.1f}%)")

    output.append("=" * 70)

    text_widget.insert('1.0', '\n'.join(output))

# Expose plot types for dynamic plot tab
PLOT_TYPES = {
    "ASCII Histogram": plot_ascii
}

def register_plugin(main_app):
    return None
