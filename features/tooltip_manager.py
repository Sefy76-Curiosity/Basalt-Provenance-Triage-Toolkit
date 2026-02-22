"""
Tooltip Manager - Provides hover tooltips for all UI elements
Converted to use ttkbootstrap-compatible dark tooltip styling.
"""

import tkinter as tk
import ttkbootstrap as ttk
from typing import Optional


class ToolTip:
    """
    Create a tooltip for a given widget.
    Uses a dark-themed popup consistent with the ttkbootstrap 'darkly' theme.
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
        self.schedule()

    def on_leave(self, event=None):
        self.unschedule()
        self.hide()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.delay, self.show)

    def unschedule(self):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None

    def show(self):
        if self.tooltip_window:
            return

        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5

        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")

        # Get colors from current theme
        style = ttk.Style()
        bg = style.colors.bg
        fg = style.colors.fg

        label = tk.Label(
            self.tooltip_window,
            text=self.text,
            justify=tk.LEFT,
            background=bg,
            foreground=fg,
            relief=tk.SOLID,
            borderwidth=1,
            font=("TkDefaultFont", 9, "normal"),
            padx=6,
            pady=4
        )
        label.pack()

    def hide(self):
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
        tooltip = ToolTip(widget, text, delay)
        self.tooltips.append(tooltip)
        return tooltip

    def clear_all(self):
        for tooltip in self.tooltips:
            tooltip.hide()
        self.tooltips.clear()
