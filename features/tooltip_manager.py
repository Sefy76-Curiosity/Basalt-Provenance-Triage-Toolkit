"""
Tooltip Manager - Provides hover tooltips for all UI elements
"""

import tkinter as tk
from typing import Optional

class ToolTip:
    """
    Create a tooltip for a given widget
    """
    def __init__(self, widget, text: str, delay: int = 500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tooltip_window: Optional[tk.Toplevel] = None
        self.id: Optional[str] = None
        
        self.widget.bind("<Enter>", self.on_enter)
        self.widget.bind("<Leave>", self.on_leave)
        self.widget.bind("<ButtonPress>", self.on_leave)
    
    def on_enter(self, event=None):
        """Schedule tooltip to appear"""
        self.schedule()
    
    def on_leave(self, event=None):
        """Hide tooltip"""
        self.unschedule()
        self.hide()
    
    def schedule(self):
        """Schedule tooltip display after delay"""
        self.unschedule()
        self.id = self.widget.after(self.delay, self.show)
    
    def unschedule(self):
        """Cancel scheduled tooltip"""
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None
    
    def show(self):
        """Display tooltip"""
        if self.tooltip_window:
            return
        
        # Get widget position
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        
        # Create tooltip window
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
        # Create label with tooltip text
        label = tk.Label(
            self.tooltip_window,
            text=self.text,
            justify=tk.LEFT,
            background="#ffffe0",
            foreground="#000000",
            relief=tk.SOLID,
            borderwidth=1,
            font=("TkDefaultFont", 9, "normal"),
            padx=5,
            pady=3
        )
        label.pack()
    
    def hide(self):
        """Hide tooltip"""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


class ToolTipManager:
    """
    Centralized tooltip management
    """
    def __init__(self):
        self.tooltips = []
    
    def add(self, widget, text: str, delay: int = 500):
        """Add tooltip to a widget"""
        tooltip = ToolTip(widget, text, delay)
        self.tooltips.append(tooltip)
        return tooltip
    
    def clear_all(self):
        """Remove all tooltips"""
        for tooltip in self.tooltips:
            tooltip.hide()
        self.tooltips.clear()
