"""
Pillow Plotter - UI Add-on
Basic plotting with PIL/Pillow
Category: add-ons (provides PLOT_TYPES)
"""
import tkinter as tk

HAS_PILLOW = False
try:
    from PIL import Image, ImageDraw, ImageTk
    HAS_PILLOW = True
except ImportError:
    pass

PLUGIN_INFO = {
    'id': 'pillow_plotter',
    'name': 'Pillow Plotter (Basic)',
    'category': 'add-ons',
    'icon': '📈',
    'requires': ['pillow'],
    'description': 'Basic plots with PIL/Pillow'
}

def plot_pillow(frame, samples):
    """Draw a basic Pillow histogram inside the given tkinter frame."""
    if not HAS_PILLOW:
        for widget in frame.winfo_children():
            widget.destroy()
        label = tk.Label(frame, text="Pillow not available\nInstall with: pip install pillow",
                         fg="red", font=("Arial", 12))
        label.pack(expand=True)
        return

    for widget in frame.winfo_children():
        widget.destroy()

    canvas = tk.Canvas(frame, bg='white')
    canvas.pack(fill=tk.BOTH, expand=True)

    if not samples:
        canvas.create_text(400, 300, text="No data to plot", fill='gray')
        return

    width, height = 800, 600
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)

    # Extract Zr/Nb ratios
    ratios = []
    for s in samples:
        try:
            zr = float(s.get('Zr_ppm', 0))
            nb = float(s.get('Nb_ppm', 1))
            if zr > 0 and nb > 0:
                ratios.append(zr/nb)
        except:
            pass

    if not ratios:
        draw.text((width//2 - 50, height//2), "No data to plot", fill='gray')
    else:
        bins = 20
        max_ratio = max(ratios)
        min_ratio = min(ratios)
        bin_width = (max_ratio - min_ratio) / bins if max_ratio > min_ratio else 1

        counts = [0] * bins
        for r in ratios:
            bin_idx = int((r - min_ratio) / bin_width) if bin_width > 0 else 0
            if 0 <= bin_idx < bins:
                counts[bin_idx] += 1

        max_count = max(counts) if counts else 1
        bar_width = width // bins

        for i, count in enumerate(counts):
            if count > 0:
                bar_height = int((count / max_count) * (height - 100))
                x1 = i * bar_width
                y1 = height - 50 - bar_height
                x2 = x1 + bar_width - 2
                y2 = height - 50
                draw.rectangle([x1, y1, x2, y2], fill='steelblue', outline='black')

        draw.text((10, 10), "Zr/Nb Distribution (Pillow)", fill='black')
        draw.text((10, height - 30), f"Min: {min_ratio:.1f}", fill='black')
        draw.text((width - 100, height - 30), f"Max: {max_ratio:.1f}", fill='black')

    photo = ImageTk.PhotoImage(img)
    canvas.photo = photo
    canvas.create_image(0, 0, anchor=tk.NW, image=photo)

PLOT_TYPES = {
    "Pillow Histogram": plot_pillow
}

def register_plugin(main_app):
    return None
