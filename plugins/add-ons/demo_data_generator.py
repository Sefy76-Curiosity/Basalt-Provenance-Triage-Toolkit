"""
Demo Data Generator Plugin - Adds a toolbar button to generate Tel Hazor data.
Category: software (appears as a button on the toolbar)
"""

import random
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

PLUGIN_INFO = {
    'id': 'demo_data_generator',
    'name': 'Demo Data Generator',
    'category': 'software',          # still software, but we bypass the menu
    'icon': '🧪',
    'requires': [],
    'version': '2.0',
    'description': 'Robust Geochemical Data Generator for Tel Hazor',
    'author': 'Sefy Levy'
}

def generate_robust_samples():
    """Generates 8 samples with pure floats and oxides needed for classification"""
    samples = []
    specs = [
        ("HAZ-Haddadin", 49.2, 2.8, 0.9, 100, 10.0, 265, 45, 130, 95),
        ("HAZ-Alkaline", 45.1, 3.8, 1.6, 295, 14.5, 450, 58, 155, 90),
        ("HAZ-Sinai", 51.8, 1.7, 0.4, 212, 7.8, 118, 18, 220, 105),
        ("HAZ-Local", 49.8, 2.9, 1.1, 115, 11.5, 172, 14, 190, 65)
    ]

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for prefix, sio2, na2o, k2o, zr, nb, ba, rb, cr, ni in specs:
        for i in range(2):
            samples.append({
                "Sample_ID": f"{prefix}-{i+1:02d}",
                "SiO2": float(round(sio2 + random.uniform(-0.4, 0.4), 2)),
                "Na2O": float(round(na2o + random.uniform(-0.2, 0.2), 2)),
                "K2O": float(round(k2o + random.uniform(-0.1, 0.1), 2)),
                "Zr_ppm": zr + random.randint(-5, 5),
                "Nb_ppm": round(nb + random.uniform(-0.5, 0.5), 1),
                "Ba_ppm": ba + random.randint(-10, 10),
                "Rb_ppm": rb + random.randint(-3, 3),
                "Cr_ppm": cr + random.randint(-10, 10),
                "Ni_ppm": ni + random.randint(-5, 5),
                "Museum_Code": f"REF-{prefix}-{i+1:02d}",
                "Context": "Tel Hazor Strata",
                "Timestamp": timestamp,
                "Plugin": PLUGIN_INFO['name'],
                "Notes": f"Tel Hazor sample from {prefix} context"
            })
    return samples


class DemoDataGeneratorPlugin:
    """Plugin that adds a toolbar button to generate demo data."""

    def __init__(self, main_app):
        self.app = main_app
        self.button = None   # will hold the toolbar button reference

    def show(self):
        """Generate and import demo data."""
        try:
            demo_data = generate_robust_samples()
            if not demo_data:
                messagebox.showwarning("No Data", "Failed to generate demo data!")
                return

            if hasattr(self.app, 'import_data_from_plugin'):
                self.app.import_data_from_plugin(demo_data)
                if hasattr(self.app, 'classify_all_with_scheme'):
                    try:
                        self.app.classify_all_with_scheme()
                    except Exception as e:
                        print(f"Classification trigger error: {e}")
                messagebox.showinfo(
                    "Success",
                    f"✅ Generated {len(demo_data)} Tel Hazor samples!\n"
                    f"Classification engine triggered."
                )
            else:
                self._legacy_import(demo_data)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate data: {str(e)}")

    def _legacy_import(self, demo_data):
        """Fallback for older app versions."""
        if hasattr(self.app, 'samples'):
            self.app.samples.clear()
            self.app.samples.extend(demo_data)
        if hasattr(self.app, 'tree'):
            self.app.tree.configure(columns=[], displaycolumns=[])
            if hasattr(self.app, 'setup_dynamic_columns'):
                headers = list(demo_data[0].keys())
                self.app.setup_dynamic_columns(headers)
            self.app.refresh_tree()
        if hasattr(self.app, 'classify_all_with_scheme'):
            try:
                self.app.classify_all_with_scheme()
            except Exception as e:
                print(f"Classification Trigger Error: {e}")
        if hasattr(self.app, '_mark_unsaved_changes'):
            self.app._mark_unsaved_changes()
        messagebox.showinfo(
            "Success",
            f"✅ Generated {len(demo_data)} Tel Hazor samples!\n"
            f"Classification engine triggered."
        )


def register_plugin(main_app):
    """
    Called by the main app when loading plugins.
    Creates the plugin instance and adds a command to the Tools menu.
    """
    plugin = DemoDataGeneratorPlugin(main_app)

    # Add to Tools menu if it exists
    if hasattr(main_app, 'tools_menu') and main_app.tools_menu:
        main_app.tools_menu.add_command(
            label=f"{PLUGIN_INFO['icon']} Generate Demo Data",
            command=plugin.show
        )
    # Alternative: if the menu is accessed via menubar
    elif hasattr(main_app, 'menubar'):
        # Check if Tools menu exists, create if it doesn't
        tools_menu = None
        for i, menu in enumerate(main_app.menubar.winfo_children()):
            if isinstance(menu, tk.Menu) and hasattr(menu, 'entrycget'):
                # Try to find existing Tools menu
                pass

        # Or simply add to an existing menu (like File or Edit)
        if hasattr(main_app, 'file_menu'):
            main_app.file_menu.add_command(
                label=f"{PLUGIN_INFO['icon']} Generate Demo Data",
                command=plugin.show
            )

    return plugin
