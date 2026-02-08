"""
Pillow Plotter - UI Add-on
Basic plotting with PIL/Pillow

Author: Sefy Levy
Category: UI Add-on
"""

import tkinter as tk
from tkinter import ttk

HAS_PILLOW = False
try:
    from PIL import Image, ImageDraw, ImageTk
    HAS_PILLOW = True
except ImportError:
    pass

PLUGIN_INFO = {
    'id': 'pillow_plotter',
    'name': 'Pillow Plotter (Basic)',
    'category': 'add-on',
    'icon': '📈',
    'requires': ['pillow'],
    'description': 'Basic plots with PIL/Pillow (exclusive plotter)',
    'exclusive_group': 'plotter'
}

class PillowPlotterPlugin:
    """Pillow plotter add-on"""
    
    def __init__(self, parent_app):
        self.app = parent_app
        self.canvas = None
        
    def create_plot_frame(self, parent):
        """Create pillow plot in parent frame"""
        if not HAS_PILLOW:
            label = tk.Label(parent, text="Pillow not available\nInstall with: pip install pillow",
                           fg="red", font=("Arial", 12))
            label.pack(expand=True)
            return None
        
        self.canvas = tk.Canvas(parent, bg='white')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        return self.canvas
    
    def plot(self, samples):
        """Draw basic plots with Pillow"""
        if not HAS_PILLOW or not self.canvas:
            return
        
        # Clear canvas
        self.canvas.delete('all')
        
        if not samples:
            return
        
        # Create image
        width = 800
        height = 600
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
            # Simple histogram
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
            
            # Draw bars
            for i, count in enumerate(counts):
                if count > 0:
                    bar_height = int((count / max_count) * (height - 100))
                    x1 = i * bar_width
                    y1 = height - 50 - bar_height
                    x2 = x1 + bar_width - 2
                    y2 = height - 50
                    draw.rectangle([x1, y1, x2, y2], fill='steelblue', outline='black')
            
            # Labels
            draw.text((10, 10), "Zr/Nb Distribution (Basic Plot)", fill='black')
            draw.text((10, height - 30), f"Min: {min_ratio:.1f}", fill='black')
            draw.text((width - 100, height - 30), f"Max: {max_ratio:.1f}", fill='black')
        
        # Convert to PhotoImage
        photo = ImageTk.PhotoImage(img)
        self.canvas.photo = photo  # Keep reference
        self.canvas.create_image(0, 0, anchor=tk.NW, image=photo)

def register_plugin(parent_app):
    """Register this add-on"""
    return PillowPlotterPlugin(parent_app)
