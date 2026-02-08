import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

PLUGIN_INFO = {
    "category": "software",
    "id": "petrology_modeling",
    "name": "Petrological Modeling",
    "description": "Isocon Analysis, Magma Mixing, and Stratigraphic Profiling",
    "icon": "🧪",
    "version": "1.0",
    "requires": ["matplotlib", "numpy", "scipy"],
    "author": "Sefy Levy"
}

class PetrologyModelingPlugin:
    def __init__(self, main_app):
        self.app = main_app
        self.window = None

    def open_window(self):
        self.window = tk.Toplevel(self.app.root)
        self.window.title("Advanced Petrological Modeling")
        self.window.geometry("900x700")

        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True)

        # 1. Isocon Tab
        isocon_frame = ttk.Frame(notebook)
        notebook.add(isocon_frame, text="Isocon (Mass Balance)")
        self._setup_isocon_ui(isocon_frame)

        # 2. Mixing Tab
        mixing_frame = ttk.Frame(notebook)
        notebook.add(mixing_frame, text="Magma Mixing")
        self._setup_mixing_ui(mixing_frame)

        # 3. Stratigraphy Tab
        strat_frame = ttk.Frame(notebook)
        notebook.add(strat_frame, text="Stratigraphic Profiling")
        self._setup_stratigraphy_ui(strat_frame)

    def _setup_isocon_ui(self, frame):
        # UI for selecting 'Fresh' vs 'Altered' samples and plotting
        ttk.Label(frame, text="Compare Altered vs. Parent Composition", font=("Arial", 10, "bold")).pack(pady=5)
        btn_plot = ttk.Button(frame, text="Generate Isocon Plot", command=self._plot_isocon)
        btn_plot.pack(pady=5)
        self.isocon_plot_area = ttk.Frame(frame)
        self.isocon_plot_area.pack(fill=tk.BOTH, expand=True)

    def _plot_isocon(self):
        # Example logic for plotting Isocon
        fig, ax = plt.subplots(figsize=(5, 5))
        # Placeholder data: In reality, pull from self.app.samples
        x = [100, 20, 1500] # Parent (Zr, Nb, Cr)
        y = [110, 22, 1400] # Altered
        ax.scatter(x, y)
        ax.plot([0, max(x)], [0, max(y)], 'r--', label='Isocon')
        ax.set_xlabel("Parent Concentration (ppm)")
        ax.set_ylabel("Altered Concentration (ppm)")

        canvas = FigureCanvasTkAgg(fig, master=self.isocon_plot_area)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _setup_mixing_ui(self, frame):
        # UI with a slider for mixing percentage (f)
        self.mix_val = tk.DoubleVar(value=0.5)
        slider = ttk.Scale(frame, from_=0, to=1, variable=self.mix_val, orient=tk.HORIZONTAL)
        slider.pack(fill="x", padx=20, pady=10)
        ttk.Label(frame, text="Mixing Ratio (Source A <-> Source B)").pack()

        self.mixing_plot_area = ttk.Frame(frame)
        self.mixing_plot_area.pack(fill=tk.BOTH, expand=True)

    def _setup_stratigraphy_ui(self, frame):
        # UI for selecting element to plot against Depth/Locus
        ttk.Label(frame, text="Element vs. Stratigraphic Depth").pack(pady=5)
        self.strat_plot_area = ttk.Frame(frame)
        self.strat_plot_area.pack(fill=tk.BOTH, expand=True)

def register_plugin(app):
    return PetrologyModelingPlugin(app)
