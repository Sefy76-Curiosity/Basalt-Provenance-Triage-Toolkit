"""
Demo Data Generator - UI Add-on
Generates sample archaeological data for testing

Author: Sefy Levy
Category: UI Add-on
"""

import random

PLUGIN_INFO = {
    'id': 'demo_data_generator',
    'name': 'Demo Data Generator',
    'category': 'add-on',
    'icon': '🎲',
    'requires': [],
    'description': 'Generate sample basalt artifacts from Tel Hazor excavations for testing'
}


def generate_demo_samples(count=8):
    """Generate demo basalt artifact samples"""
    samples = []
    
    # Egyptian Haddadin samples (2)
    for i in range(2):
        samples.append({
            "Sample_ID": f"HAZOR-M-{i+1:03d}",
            "Museum_Code": f"HAZ-2010-M-BV-{i+1:03d}",
            "Wall_Thickness_mm": f"{random.uniform(2.8, 3.8):.1f}",
            "Zr_ppm": f"{random.randint(90, 110)}",
            "Nb_ppm": f"{random.uniform(9.5, 11.5):.1f}",
            "Ba_ppm": f"{random.randint(250, 280)}",
            "Rb_ppm": f"{random.randint(40, 50)}",
            "Cr_ppm": f"{random.randint(120, 140)}",
            "Ni_ppm": f"{random.randint(90, 105)}",
            "Museum_URL": "https://www.parks.org.il/en/reserve-park/tel-hazor-national-park/"
        })
    
    # Egyptian Alkaline samples (2)
    for i in range(2):
        samples.append({
            "Sample_ID": f"HAZOR-A-{i+1:03d}",
            "Museum_Code": f"HAZ-1990-A-BV-{i+1:03d}",
            "Wall_Thickness_mm": f"{random.uniform(2.8, 3.2):.1f}",
            "Zr_ppm": f"{random.randint(280, 320)}",
            "Nb_ppm": f"{random.uniform(11, 13):.1f}",
            "Ba_ppm": f"{random.randint(420, 480)}",
            "Rb_ppm": f"{random.randint(54, 62)}",
            "Cr_ppm": f"{random.randint(140, 160)}",
            "Ni_ppm": f"{random.randint(88, 98)}",
            "Museum_URL": "https://www.parks.org.il/en/reserve-park/tel-hazor-national-park/"
        })
    
    # Sinai Ophiolitic samples (2)
    for i in range(2):
        samples.append({
            "Sample_ID": f"HAZOR-S-{i+1:03d}",
            "Museum_Code": f"HAZ-1992-S-BV-{i+1:03d}",
            "Wall_Thickness_mm": f"{random.uniform(4.2, 4.8):.1f}",
            "Zr_ppm": f"{random.randint(210, 225)}",
            "Nb_ppm": f"{random.uniform(9.8, 10.5):.1f}",
            "Ba_ppm": f"{random.randint(110, 125)}",
            "Rb_ppm": f"{random.randint(16, 21)}",
            "Cr_ppm": f"{random.randint(210, 225)}",
            "Ni_ppm": f"{random.randint(102, 112)}",
            "Museum_URL": "https://www.parks.org.il/en/reserve-park/tel-hazor-national-park/"
        })
    
    # Local Levantine samples (2)
    for i in range(2):
        samples.append({
            "Sample_ID": f"HAZOR-L-{i+1:03d}",
            "Museum_Code": f"HAZ-2003-L-BV-{i+1:03d}",
            "Wall_Thickness_mm": f"{random.uniform(5.2, 6.2):.1f}",
            "Zr_ppm": f"{random.randint(105, 120)}",
            "Nb_ppm": f"{random.uniform(11, 12.5):.1f}",
            "Ba_ppm": f"{random.randint(165, 180)}",
            "Rb_ppm": f"{random.randint(12, 16)}",
            "Cr_ppm": f"{random.randint(185, 200)}",
            "Ni_ppm": f"{random.randint(65, 72)}",
            "Museum_URL": "https://www.parks.org.il/en/reserve-park/tel-hazor-national-park/"
        })
    
    return samples


class DemoDataGeneratorPlugin:
    """Demo data generator add-on"""
    
    def __init__(self, parent_app):
        self.app = parent_app
    
    def show(self):
        """Generate and load demo data"""
        from tkinter import messagebox
        
        # Generate samples
        demo_samples = generate_demo_samples(8)
        
        # Add to app
        self.app.samples.extend(demo_samples)
        self.app.refresh_tree()
        self.app._mark_unsaved_changes()
        
        messagebox.showinfo("Demo Data Generated",
            f"✅ Generated 8 sample artifacts from Tel Hazor!\n\n"
            f"Distribution:\n"
            f"• 2 Egyptian (Haddadin Flow)\n"
            f"• 2 Egyptian (Alkaline/Exotic)\n"
            f"• 2 Sinai Ophiolitic\n"
            f"• 2 Local Levantine\n\n"
            f"Based on published research:\n"
            f"Gluhak et al. (2016, 2022)\n"
            f"Ebeling & Rosenberg (2015)")


def register_plugin(parent_app):
    """Register this add-on with the main application"""
    return DemoDataGeneratorPlugin(parent_app)
