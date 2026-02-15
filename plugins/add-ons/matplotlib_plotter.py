"""
Matplotlib Plotter - UI Add-on
High-quality plotting with matplotlib
Category: add-ons (provides PLOT_TYPES)
"""
import tkinter as tk

HAS_MATPLOTLIB = False
try:
    import matplotlib
    matplotlib.use('TkAgg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    HAS_MATPLOTLIB = True
except ImportError:
    pass

PLUGIN_INFO = {
    'id': 'matplotlib_plotter',
    'name': 'Matplotlib Plotter (High Quality)',
    'category': 'add-ons',
    'icon': '📊',
    'requires': ['matplotlib'],
    'description': 'High-quality scientific plots with matplotlib'
}

def plot_matplotlib(frame, samples):
    """Draw matplotlib dashboard inside the given tkinter frame."""
    if not HAS_MATPLOTLIB:
        for widget in frame.winfo_children():
            widget.destroy()
        label = tk.Label(frame, text="Matplotlib not available\nInstall with: pip install matplotlib",
                         fg="red", font=("Arial", 12))
        label.pack(expand=True)
        return

    for widget in frame.winfo_children():
        widget.destroy()

    # Create figure
    fig, axes = plt.subplots(2, 2, figsize=(10, 8))
    fig.tight_layout(pad=3.0)

    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    if not samples:
        canvas.draw()
        return

    # Extract data
    zr_nb = []
    cr_ni = []
    ba_rb = []

    for s in samples:
        try:
            zr = float(s.get('Zr_ppm', 0))
            nb = float(s.get('Nb_ppm', 1))
            cr = float(s.get('Cr_ppm', 0))
            ni = float(s.get('Ni_ppm', 1))
            ba = float(s.get('Ba_ppm', 0))
            rb = float(s.get('Rb_ppm', 1))

            if zr > 0 and nb > 0:
                zr_nb.append(zr/nb)
            if cr > 0 and ni > 0:
                cr_ni.append(cr/ni)
            if ba > 0 and rb > 0:
                ba_rb.append(ba/rb)
        except:
            pass

    ax_list = fig.axes

    if zr_nb:
        ax_list[0].hist(zr_nb, bins=20, color='steelblue', edgecolor='black')
        ax_list[0].set_xlabel('Zr/Nb Ratio')
        ax_list[0].set_ylabel('Frequency')
        ax_list[0].set_title('Zr/Nb Distribution')
        ax_list[0].grid(True, alpha=0.3)

    if cr_ni:
        ax_list[1].hist(cr_ni, bins=20, color='coral', edgecolor='black')
        ax_list[1].set_xlabel('Cr/Ni Ratio')
        ax_list[1].set_ylabel('Frequency')
        ax_list[1].set_title('Cr/Ni Distribution')
        ax_list[1].grid(True, alpha=0.3)

    if zr_nb and cr_ni and len(zr_nb) == len(cr_ni):
        ax_list[2].scatter(zr_nb, cr_ni, alpha=0.6, s=50, c='green', edgecolors='black')
        ax_list[2].set_xlabel('Zr/Nb Ratio')
        ax_list[2].set_ylabel('Cr/Ni Ratio')
        ax_list[2].set_title('Provenance Discrimination')
        ax_list[2].grid(True, alpha=0.3)

    if ba_rb:
        ax_list[3].hist(ba_rb, bins=20, color='purple', edgecolor='black')
        ax_list[3].set_xlabel('Ba/Rb Ratio')
        ax_list[3].set_ylabel('Frequency')
        ax_list[3].set_title('Ba/Rb Distribution')
        ax_list[3].grid(True, alpha=0.3)

    canvas.draw()

PLOT_TYPES = {
    "Matplotlib Dashboard (2x2)": plot_matplotlib
}

def register_plugin(main_app):
    return None
