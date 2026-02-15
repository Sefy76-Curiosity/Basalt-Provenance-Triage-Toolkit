"""
XRD Plugin (Powder Diffraction)
Generic import of XRD patterns from text/CSV
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

PLUGIN_INFO = {
    "id": "hardware_xrd_generic",
    "name": "XRD (Powder Diffraction)",
    "category": "hardware",
    "type": "xrd",
    "manufacturer": "Generic",
    "models": ["Bruker D8", "Rigaku", "PANalytical", "Other XRD"],
    "connection": "File (TXT/CSV export)",
    "icon": "📐",
    "description": "Imports XRD patterns and does simple phase hints.",
    "data_types": ["xrd_pattern"],
    "requires": []
}


class XRDGenericPlugin:
    """Generic XRD pattern import plugin"""

    def __init__(self, app):
        self.app = app
        self.window = None
        self.current_pattern = None
        self.phase_hints = []

    def show_interface(self):
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("📐 XRD – Powder Diffraction (Generic)")
        self.window.geometry("650x500")

        info = ttk.LabelFrame(self.window, text="How it works", padding=10)
        info.pack(fill="x", padx=10, pady=5)
        ttk.Label(
            info,
            text=(
                "1. Export XRD pattern as 2-column TXT/CSV (2θ, intensity)\n"
                "2. Load file\n"
                "3. Simple peak-based phase hints\n"
                "4. Add summary to sample"
            ),
            justify="left"
        ).pack(anchor="w")

        file_frame = ttk.LabelFrame(self.window, text="File", padding=10)
        file_frame.pack(fill="x", padx=10, pady=5)

        self.file_label = ttk.Label(file_frame, text="No file loaded")
        self.file_label.pack(side="left", padx=5)

        ttk.Button(file_frame, text="📂 Load Pattern", command=self.load_pattern).pack(side="right", padx=5)

        pattern_frame = ttk.LabelFrame(self.window, text="Pattern Info", padding=10)
        pattern_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.pattern_text = tk.Text(pattern_frame, height=15, font=("Consolas", 9))
        self.pattern_text.pack(fill="both", expand=True)

        btn_frame = ttk.Frame(self.window)
        btn_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(btn_frame, text="➕ Add to Sample",
                   command=self.add_to_sample,
                   style="Accent.TButton").pack(side="left", padx=5)

        ttk.Button(btn_frame, text="🗑️ Clear",
                   command=self.clear_data).pack(side="left", padx=5)

        ttk.Button(btn_frame, text="❌ Close",
                   command=self.window.destroy).pack(side="right", padx=5)

    def load_pattern(self):
        path = filedialog.askopenfilename(
            title="Select XRD pattern file",
            filetypes=[("Text/CSV", "*.txt *.csv"), ("All files", "*.*")]
        )
        if not path:
            return

        twotheta = []
        intensity = []

        try:
            with open(path, encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.replace(",", " ").split()
                    if len(parts) < 2:
                        continue
                    try:
                        x = float(parts[0])
                        y = float(parts[1])
                    except ValueError:
                        continue
                    twotheta.append(x)
                    intensity.append(y)

            if not twotheta:
                raise ValueError("No numeric data found")

            self.current_pattern = {
                "twotheta": twotheta,
                "intensity": intensity,
                "file": path
            }

            self.analyze_pattern()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read pattern:\n{e}")

    def analyze_pattern(self):
        self.phase_hints = []
        self.pattern_text.delete("1.0", tk.END)

        t = self.current_pattern["twotheta"]
        i = self.current_pattern["intensity"]

        self.pattern_text.insert(
            tk.END,
            f"Points: {len(t)}\nRange: {min(t):.2f}–{max(t):.2f}° 2θ\n\n"
        )

        # Simple peak detection
        peaks = []
        for idx in range(1, len(i) - 1):
            if i[idx] > i[idx - 1] and i[idx] > i[idx + 1] and i[idx] > 0.1 * max(i):
                peaks.append(t[idx])

        self.pattern_text.insert(tk.END, "Peak positions (top ~10):\n")
        for p in peaks[:10]:
            self.pattern_text.insert(tk.END, f"  {p:.2f}° 2θ\n")

        # Very rough phase hints
        if any(26 < p < 27 for p in peaks):
            self.phase_hints.append("Quartz")
        if any(28 < p < 30 for p in peaks):
            self.phase_hints.append("Feldspar")
        if any(35 < p < 37 for p in peaks):
            self.phase_hints.append("Pyroxene / Fe-oxides")

        self.pattern_text.insert(tk.END, "\nPhase hints:\n")
        if self.phase_hints:
            for ph in self.phase_hints:
                self.pattern_text.insert(tk.END, f"  ✓ {ph}\n")
        else:
            self.pattern_text.insert(tk.END, "  None (library match needed)\n")

    def add_to_sample(self):
        if not self.current_pattern:
            messagebox.showwarning("No Data", "Load a pattern first.")
            return
        if not hasattr(self.app, "selected_sample") or not self.app.selected_sample:
            messagebox.showwarning("No Sample", "Select a sample first.")
            return

        s = self.app.selected_sample
        s["XRD_File"] = self.current_pattern["file"]
        s["XRD_Points"] = len(self.current_pattern["twotheta"])
        s["XRD_Phase_Hints"] = ", ".join(self.phase_hints) if self.phase_hints else "None"

        if hasattr(self.app, "refresh_tree"):
            self.app.refresh_tree()
        if hasattr(self.app, "_mark_unsaved_changes"):
            self.app._mark_unsaved_changes()

        messagebox.showinfo("Success", "XRD summary added to current sample.")

    def clear_data(self):
        self.current_pattern = None
        self.phase_hints = []
        self.pattern_text.delete("1.0", tk.END)

    def test_connection(self):
        return True, "XRD plugin uses file import – no live connection required."


def register_plugin(app):
    return XRDGenericPlugin(app)
