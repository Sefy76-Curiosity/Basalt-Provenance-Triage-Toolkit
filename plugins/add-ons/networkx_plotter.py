"""
NetworkX Plotter - UI Add-on
Trade route and relationship networks

Author: Sefy Levy
Category: UI Add-on
"""
import tkinter as tk
from tkinter import ttk

HAS_NETWORKX = False
HAS_MATPLOTLIB = False
try:
    import matplotlib
    matplotlib.use('TkAgg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import networkx as nx
    import numpy as np
    HAS_NETWORKX = True
    HAS_MATPLOTLIB = True
except ImportError:
    pass

PLUGIN_INFO = {
    'id': 'networkx_plotter',
    'name': 'Network Analysis Plotter',
    'category': 'add-on',
    'icon': '🕸️',
    'requires': ['networkx', 'matplotlib', 'numpy'],
    'description': 'Visualize trade routes and sample relationships',
    'exclusive_group': 'plotter'
}

class NetworkXPlotterPlugin:
    """NetworkX plotter add-on"""
    def __init__(self, parent_app):
        self.app = parent_app

def register_plugin(parent_app):
    """Register this add-on and return an instance."""
    return NetworkXPlotterPlugin(parent_app)

def plot_networkx(frame, samples):
    """Draw network graphs inside tkinter frame."""
    if not HAS_NETWORKX:
        for widget in frame.winfo_children():
            widget.destroy()
        label = tk.Label(frame, text="NetworkX not available\nInstall with: pip install networkx matplotlib numpy",
                         fg="red", font=("Arial", 12))
        label.pack(expand=True)
        return

    # Clear frame
    for widget in frame.winfo_children():
        widget.destroy()

    if len(samples) < 2:
        label = tk.Label(frame, text="Need at least 2 samples for network analysis", font=("Arial", 12))
        label.pack(expand=True)
        return

    # Control panel for network layout
    control_frame = ttk.Frame(frame)
    control_frame.pack(fill=tk.X, pady=5)

    ttk.Label(control_frame, text="Layout:").pack(side=tk.LEFT, padx=5)
    layout_var = tk.StringVar(value="Spring")
    layout_combo = ttk.Combobox(control_frame, textvariable=layout_var,
                                values=["Spring", "Circular", "Random", "Spectral", "Kamada-Kawai"],
                                state='readonly', width=15)
    layout_combo.pack(side=tk.LEFT, padx=5)

    ttk.Label(control_frame, text="Threshold:").pack(side=tk.LEFT, padx=5)
    threshold_var = tk.StringVar(value="0.7")
    threshold_spin = ttk.Spinbox(control_frame, from_=0.1, to=1.0, increment=0.1,
                                 textvariable=threshold_var, width=5)
    threshold_spin.pack(side=tk.LEFT, padx=5)

    def update_network():
        plot_network(layout_var.get(), float(threshold_var.get()))

    ttk.Button(control_frame, text="Update Network", command=update_network).pack(side=tk.LEFT, padx=10)

    # Frame for network plot
    network_frame = ttk.Frame(frame)
    network_frame.pack(fill=tk.BOTH, expand=True, pady=5)

    def plot_network(layout_type='Spring', similarity_threshold=0.7):
        # Clear network frame
        for widget in network_frame.winfo_children():
            widget.destroy()

        # Create figure with 2 subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
        fig.suptitle('Archaeological Network Analysis', fontsize=14, fontweight='bold')

        # Create canvas
        canvas = FigureCanvasTkAgg(fig, master=network_frame)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Extract geochemical fingerprints
        fingerprints = []
        sample_names = []

        for s in samples:
            try:
                # Create geochemical fingerprint vector
                fingerprint = [
                    float(s.get('Zr_ppm', 0)),
                    float(s.get('Nb_ppm', 0)),
                    float(s.get('Cr_ppm', 0)),
                    float(s.get('Ni_ppm', 0)),
                    float(s.get('Ba_ppm', 0)),
                    float(s.get('Rb_ppm', 0)),
                    float(s.get('SiO2', 0)),
                    float(s.get('TiO2', 0)),
                    float(s.get('Al2O3', 0)),
                    float(s.get('Fe2O3', 0))
                ]
                # Check if we have valid data
                if any(v > 0 for v in fingerprint):
                    fingerprints.append(fingerprint)
                    sample_names.append(s.get('Sample_ID', f'Sample {len(sample_names)+1}'))
            except:
                continue

        if len(fingerprints) < 2:
            ax1.text(0.5, 0.5, "Insufficient geochemical data for network analysis",
                    transform=ax1.transAxes, ha='center', va='center')
            canvas.draw()
            return

        # Normalize fingerprints
        fingerprints = np.array(fingerprints)
        fingerprints = (fingerprints - fingerprints.min(axis=0)) / (fingerprints.max(axis=0) - fingerprints.min(axis=0) + 1e-10)

        # Calculate similarity matrix (cosine similarity)
        norms = np.linalg.norm(fingerprints, axis=1, keepdims=True)
        similarity = np.dot(fingerprints, fingerprints.T) / (norms * norms.T + 1e-10)

        # Create graph
        G = nx.Graph()

        # Add nodes
        for i, name in enumerate(sample_names):
            G.add_node(i, label=name, size=fingerprints[i].sum())

        # Add edges based on similarity threshold
        for i in range(len(fingerprints)):
            for j in range(i+1, len(fingerprints)):
                if similarity[i, j] > similarity_threshold:
                    G.add_edge(i, j, weight=similarity[i, j])

        # Choose layout
        if layout_type == 'Spring':
            pos = nx.spring_layout(G, k=2, iterations=50)
        elif layout_type == 'Circular':
            pos = nx.circular_layout(G)
        elif layout_type == 'Random':
            pos = nx.random_layout(G)
        elif layout_type == 'Spectral':
            pos = nx.spectral_layout(G)
        else:  # Kamada-Kawai
            pos = nx.kamada_kawai_layout(G)

        # Draw network (left subplot)
        node_sizes = [G.nodes[i]['size'] * 500 + 300 for i in G.nodes]
        nx.draw_networkx_nodes(G, pos, ax=ax1, node_size=node_sizes,
                              node_color='lightblue', edgecolors='black', linewidths=1)
        nx.draw_networkx_edges(G, pos, ax=ax1, alpha=0.5, width=1.5)

        # Add labels for important nodes
        important_nodes = [i for i in G.nodes if G.degree(i) > 1]
        labels = {i: G.nodes[i]['label'] for i in important_nodes}
        nx.draw_networkx_labels(G, pos, labels, ax=ax1, font_size=8)

        ax1.set_title(f'Sample Similarity Network\n(Threshold: {similarity_threshold})')
        ax1.axis('off')

        # Draw degree distribution (right subplot)
        degrees = [G.degree(n) for n in G.nodes]
        ax2.hist(degrees, bins=range(max(degrees)+2), color='coral', edgecolor='black', alpha=0.7)
        ax2.set_xlabel('Degree (connections)')
        ax2.set_ylabel('Number of Samples')
        ax2.set_title('Network Degree Distribution')
        ax2.grid(True, alpha=0.3)

        # Add network statistics text
        stats_text = f"Nodes: {G.number_of_nodes()}\nEdges: {G.number_of_edges()}\nDensity: {nx.density(G):.3f}"
        ax2.text(0.7, 0.95, stats_text, transform=ax2.transAxes,
                bbox=dict(boxstyle="round", facecolor='wheat', alpha=0.8),
                verticalalignment='top')

        canvas.draw()

    # Initial plot
    plot_network()

# Expose plot types
PLOT_TYPES = {
    "Network Analysis (Trade Routes)": plot_networkx
}
