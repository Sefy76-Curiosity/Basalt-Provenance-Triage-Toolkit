"""
Google Earth Plugin for Basalt Provenance Toolkit
Export samples to Google Earth with beautiful 3D visualization

Features:
- TIER 1: Basic KML Export (simplekml)
- TIER 2: Advanced KML with 3D terrain (simplekml + features)
- TIER 3: Google Earth Engine integration (optional - requires account)

Author: Sefy Levy
License: CC BY-NC-SA 4.0
"""

PLUGIN_INFO = {
    "id": "google_earth",
    "name": "Google Earth Export",
    "description": "Export samples as KML for Google Earth visualization",
    "icon": "🌏",
    "version": "1.0",
    "requires": ["simplekml", "earthengine-api"],  # <-- ADD THIS!
    "author": "Sefy Levy"
}

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import subprocess
import sys
import webbrowser

# Check for dependencies - FIXED VERSION
HAS_REQUIREMENTS = False
HAS_SIMPLEKML = False
HAS_EARTHENGINE = False
IMPORT_ERROR = ""

try:
    import simplekml
    HAS_SIMPLEKML = True
except ImportError as e:
    IMPORT_ERROR += f"simplekml: {str(e)}\n"

try:
    import ee
    HAS_EARTHENGINE = True
except ImportError as e:
    IMPORT_ERROR += f"earthengine-api: {str(e)}\n"

# Plugin can load if we have minimum requirements (simplekml is essential)
HAS_REQUIREMENTS = HAS_SIMPLEKML


def safe_float(value):
    """Safely convert value to float"""
    if value is None or value == '':
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


class GoogleEarthPlugin:
    """Plugin for Google Earth export and visualization"""

    def __init__(self, main_app):
        """Initialize plugin"""
        self.app = main_app
        self.window = None

    def open_google_earth_window(self):
        """Open the Google Earth export interface"""
        # Check minimum requirements
        if not HAS_REQUIREMENTS:
            response = messagebox.askyesno(
                "Missing Dependencies",
                f"Google Earth Export requires these packages:\n\n"
                f"• simplekml (required for KML export)\n"
                f"• earthengine-api (optional for Earth Engine)\n\n"
                f"Missing:\n{IMPORT_ERROR}\n\n"
                f"Do you want to install missing dependencies now?",
                parent=self.app.root
            )
            if response:
                # Try to open plugin manager
                if hasattr(self.app, 'open_plugin_manager'):
                    self.app.open_plugin_manager()
                elif hasattr(self.app, 'plugin_manager'):
                    self.app.plugin_manager()
                else:
                    messagebox.showinfo(
                        "Install Manually",
                        "Please use:\n"
                        "1. Tools → Plugin Manager → 'Install All Missing'\n"
                        "OR\n"
                        "2. Run in terminal:\n"
                        "   pip3 install simplekml earthengine-api",
                        parent=self.app.root
                    )
            return

        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app.root)
        self.window.title("Google Earth Export")
        # self.window.geometry("620x450")
        # self.window.minsize(800, 550)
        self.window.minsize(850, 600)

        # Make window stay on top
        self.window.transient(self.app.root)

        self._create_interface()

        # AUTO-ADJUST WINDOW SIZE
        self._auto_adjust_window()

        # Bring to front
        self.window.lift()
        self.window.focus_force()

    def _create_interface(self):
        """Create the Google Earth export interface"""
        # Header
        header = tk.Frame(self.window, bg="#1565C0")
        header.pack(fill=tk.X)

        tk.Label(header,
                text="🌏 Google Earth Export",
                font=("Arial", 16, "bold"),
                bg="#1565C0", fg="white",
                pady=5).pack()

        tk.Label(header,
                text="Visualize your samples in Google Earth's 3D globe",
                font=("Arial", 10),
                bg="#1565C0", fg="white",
                pady=5).pack()

        # Create notebook
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Tab 1: Basic KML Export
        self._create_basic_kml_tab(notebook)

        # Tab 2: Advanced KML Features
        self._create_advanced_kml_tab(notebook)

        # Tab 3: Google Earth Engine
        self._create_earth_engine_tab(notebook)

        # Tab 4: Help
        self._create_help_tab(notebook)

    def _create_basic_kml_tab(self, notebook):
        """Create basic KML export tab"""
        frame = tk.Frame(notebook)
        notebook.add(frame, text="🌍 Basic KML Export")

        # Status banner
        status_frame = tk.Frame(frame, bg="#E8F5E9" if HAS_SIMPLEKML else "#FFEBEE",
                               relief=tk.RAISED, borderwidth=2)
        status_frame.pack(fill=tk.X, padx=10, pady=5)

        if HAS_SIMPLEKML:
            tk.Label(status_frame,
                    text="✅ simplekml Available - KML export enabled!",
                    font=("Arial", 10, "bold"),
                    bg="#E8F5E9", fg="green",
                    pady=5).pack()

            if not HAS_EARTHENGINE:
                tk.Label(status_frame,
                        text="⚠ Note: Earth Engine API not installed (optional)",
                        font=("Arial", 8),
                        bg="#E8F5E9", fg="orange",
                        pady=5).pack()
        else:
            tk.Label(status_frame,
                    text="❌ simplekml Not Installed",
                    font=("Arial", 10, "bold"),
                    bg="#FFEBEE", fg="red",
                    pady=5).pack()
            tk.Label(status_frame,
                    text="Install with: pip3 install simplekml",
                    font=("Courier", 9),
                    bg="#FFEBEE",
                    pady=5).pack()
            # Install button
            install_btn = tk.Button(status_frame,
                                  text="Install Now",
                                  command=self._install_simplekml,
                                  bg="#FF9800", fg="white",
                                  font=("Arial", 9, "bold"),
                                  cursor="hand2")
            install_btn.pack(pady=5)

        # Content
        content = tk.Frame(frame)
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Description
        tk.Label(content,
                text="Export to Google Earth KML",
                font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=5)

        tk.Label(content,
                text="• Generate KML file for Google Earth\n"
                     "• Color-coded 3D pins by classification\n"
                     "• Click pins to see sample geochemistry\n"
                     "• Famous 'fly-to' effect showing patterns\n"
                     "• Works with Google Earth Desktop & Web",
                font=("Arial", 9),
                justify=tk.LEFT).pack(anchor=tk.W, pady=5)

        # Preview
        preview_frame = tk.LabelFrame(content, text="What You'll Get",
                                     font=("Arial", 10, "bold"),
                                     padx=10, pady=5)
        preview_frame.pack(fill=tk.X, pady=5)

        tk.Label(preview_frame,
                text="Your samples will appear as 3D pins on Earth's surface:\n\n"
                     "📍 Egyptian samples → Red pins\n"
                     "📍 Sinai samples → Orange pins\n"
                     "📍 Local Levantine → Green pins\n"
                     "📍 Harrat Ash Shaam → Purple pins\n\n"
                     "Click any pin to see:\n"
                     "• Sample ID\n"
                     "• Classification\n"
                     "• Zr, Nb, Cr, Ni values\n"
                     "• Zr/Nb ratio",
                font=("Arial", 9),
                justify=tk.LEFT).pack(anchor=tk.W)

        if HAS_SIMPLEKML:
            # Options
            options_frame = tk.LabelFrame(content, text="Export Options",
                                         font=("Arial", 10, "bold"),
                                         padx=10, pady=5)
            options_frame.pack(fill=tk.X, pady=5)

            self.auto_open_var = tk.BooleanVar(value=True)
            tk.Checkbutton(options_frame,
                          text="Automatically open in Google Earth after export",
                          variable=self.auto_open_var,
                          font=("Arial", 9)).pack(anchor=tk.W, pady=2)

            self.include_elevation_var = tk.BooleanVar(value=True)
            tk.Checkbutton(options_frame,
                          text="Use elevation data (if available)",
                          variable=self.include_elevation_var,
                          font=("Arial", 9)).pack(anchor=tk.W, pady=2)

            self.organize_folders_var = tk.BooleanVar(value=True)
            tk.Checkbutton(options_frame,
                          text="Organize pins into folders by classification",
                          variable=self.organize_folders_var,
                          font=("Arial", 9)).pack(anchor=tk.W, pady=2)

            # Export buttons - HORIZONTAL layout
            btn_frame = tk.Frame(content)
            btn_frame.pack(pady=5)

            tk.Button(btn_frame, text="🌏 Export KML",
                     command=self._export_basic_kml,
                     bg="#1565C0", fg="white",
                     font=("Arial", 10, "bold"),
                     width=18, height=2).pack(side=tk.LEFT, padx=3)
            
            tk.Button(btn_frame, text="🌐 View in Web",
                     command=self._open_google_earth_web,
                     bg="#4285F4", fg="white",
                     font=("Arial", 10, "bold"),
                     width=18, height=2).pack(side=tk.LEFT, padx=3)
        else:
            # Installation help
            tk.Label(content,
                    text="\nTo enable KML export:\n\n"
                         "pip3 install simplekml\n\n"
                         "simplekml is a lightweight library (< 100 KB)\n"
                         "that creates KML files for Google Earth.\n\n"
                         "After installing, restart the application.",
                    font=("Arial", 9),
                    fg="gray",
                    justify=tk.LEFT).pack(pady=8)

    def _create_advanced_kml_tab(self, notebook):
        """Create advanced KML features tab"""
        frame = tk.Frame(notebook)
        notebook.add(frame, text="⭐ Advanced Features")

        # Content
        content = tk.Frame(frame)
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        tk.Label(content,
                text="Advanced KML Features",
                font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=5)

        tk.Label(content,
                text="Enhance your Google Earth visualization with these options:",
                font=("Arial", 9),
                fg="gray").pack(anchor=tk.W, pady=5)

        # Features list
        features_frame = tk.LabelFrame(content, text="Available Enhancements",
                                      font=("Arial", 10, "bold"),
                                      padx=8, pady=5)
        features_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        features = [
            ("🎨 Custom Pin Styles", "Use custom icons for different classifications"),
            ("📊 Data Cards", "Rich HTML popups with charts and statistics"),
            ("🎬 Animated Tours", "Create fly-through tours of your samples"),
            ("📏 Distance Lines", "Show connections between related samples"),
            ("🎯 Regions/Polygons", "Draw source regions on the map"),
            ("⛰️ 3D Terrain", "Drape samples on actual terrain elevation"),
            ("📸 Photo Integration", "Link sample photos to pins"),
            ("🗂️ Smart Folders", "Hierarchical organization by site/context"),
        ]

        for icon_title, description in features:
            feature_frame = tk.Frame(features_frame)
            feature_frame.pack(fill=tk.X, pady=5)

            tk.Label(feature_frame,
                    text=icon_title,
                    font=("Arial", 9, "bold"),
                    width=25,
                    anchor=tk.W).pack(side=tk.LEFT)

            tk.Label(feature_frame,
                    text=description,
                    font=("Arial", 9),
                    fg="gray",
                    anchor=tk.W).pack(side=tk.LEFT, padx=10)

        # Status
        if HAS_SIMPLEKML:
            tk.Label(content,
                    text="\n✅ Advanced features available with simplekml installed!",
                    font=("Arial", 10, "bold"),
                    fg="green").pack(pady=5)

            btn_frame = tk.Frame(content)
            btn_frame.pack(pady=5)

            tk.Button(btn_frame, text="🌟 Export with Advanced Features",
                     command=self._export_advanced_kml,
                     bg="#F57C00", fg="white",
                     font=("Arial", 11, "bold"),
                     width=30, height=2).pack()
        else:
            tk.Label(content,
                    text="\n❌ Install simplekml to enable advanced features",
                    font=("Arial", 10, "bold"),
                    fg="red").pack(pady=5)

    def _create_earth_engine_tab(self, notebook):
        """Create Google Earth Engine tab"""
        frame = tk.Frame(notebook)
        notebook.add(frame, text="🛰️ Earth Engine")

        # Content
        content = tk.Frame(frame)
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        tk.Label(content,
                text="Google Earth Engine Integration",
                font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=5)

        tk.Label(content,
                text="Access petabytes of satellite data and global DEMs",
                font=("Arial", 9),
                fg="gray").pack(anchor=tk.W, pady=5)

        # Status banner
        if HAS_EARTHENGINE:
            status_bg = "#E8F5E9"
            status_color = "green"
            status_text = "✅ Earth Engine API installed"
        else:
            status_bg = "#FFEBEE"
            status_color = "orange"
            status_text = "⚠ Earth Engine API not installed"

        status_frame = tk.Frame(frame, bg=status_bg, relief=tk.RAISED, borderwidth=2)
        status_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(status_frame, text=status_text,
                font=("Arial", 10, "bold"),
                bg=status_bg, fg=status_color,
                pady=5).pack()

        if not HAS_EARTHENGINE:
            tk.Label(status_frame,
                    text="Install with: pip3 install earthengine-api",
                    font=("Courier", 9),
                    bg=status_bg,
                    pady=5).pack()
            # Install button
            install_btn = tk.Button(status_frame,
                                  text="Install Now",
                                  command=self._install_earthengine,
                                  bg="#FF9800", fg="white",
                                  font=("Arial", 9, "bold"),
                                  cursor="hand2")
            install_btn.pack(pady=5)

        # Info box
        info_frame = tk.LabelFrame(content, text="What is Earth Engine?",
                                  font=("Arial", 10, "bold"),
                                  padx=8, pady=5)
        info_frame.pack(fill=tk.X, pady=5)

        tk.Label(info_frame,
                text="Google Earth Engine is a cloud platform for:\n\n"
                     "• Global satellite imagery (Landsat, Sentinel)\n"
                     "• Digital Elevation Models (SRTM, ASTER)\n"
                     "• Climate and environmental data\n"
                     "• Planetary-scale geospatial analysis\n\n"
                     "With Earth Engine, you can overlay your basalt samples\n"
                     "on satellite imagery and correlate with terrain data.",
                font=("Arial", 9),
                justify=tk.LEFT).pack(anchor=tk.W)

        # Status frame
        status_frame2 = tk.LabelFrame(content, text="Current Status",
                                     font=("Arial", 10, "bold"),
                                     padx=8, pady=5)
        status_frame2.pack(fill=tk.X, pady=5)

        if HAS_EARTHENGINE:
            tk.Label(status_frame2,
                    text="✅ Earth Engine API installed",
                    font=("Arial", 10, "bold"),
                    fg="green").pack(anchor=tk.W, pady=5)

            tk.Label(status_frame2,
                    text="⚠️ You need a Google Earth Engine account\n"
                         "Sign up at: https://earthengine.google.com/signup/",
                    font=("Arial", 9),
                    fg="orange",
                    justify=tk.LEFT).pack(anchor=tk.W, pady=5)

            # Authentication button
            tk.Button(status_frame2, text="Authenticate Earth Engine",
                     command=self._authenticate_earth_engine,
                     bg="#4285F4", fg="white",
                     font=("Arial", 10),
                     width=25).pack(pady=5)
        else:
            tk.Label(status_frame2,
                    text="❌ Earth Engine not installed",
                    font=("Arial", 10, "bold"),
                    fg="red").pack(anchor=tk.W, pady=5)

            tk.Label(status_frame2,
                    text="Install with: pip3 install earthengine-api",
                    font=("Courier", 9),
                    fg="gray").pack(anchor=tk.W, pady=5)

        # Coming soon
        tk.Label(content,
                text="\n📌 Earth Engine features coming in v10.2:\n"
                     "• DEM overlay on samples\n"
                     "• Satellite imagery integration\n"
                     "• Terrain analysis\n"
                     "• Landscape evolution studies",
                font=("Arial", 9),
                fg="gray",
                justify=tk.LEFT).pack(anchor=tk.W, pady=8)

    def _create_help_tab(self, notebook):
        """Create help tab"""
        frame = tk.Frame(notebook)
        notebook.add(frame, text="❓ Help")

        from tkinter import scrolledtext
        text = scrolledtext.ScrolledText(frame, wrap=tk.WORD,
                                        font=("Arial", 10),
                                        width=80, height=25,  # Set reasonable size
                                        padx=8, pady=5)
        text.pack(fill=tk.BOTH, expand=True)

        help_text = """
GOOGLE EARTH EXPORT - USER GUIDE
═══════════════════════════════════════════════════════════════

OVERVIEW
────────────────────────────────────────────────────────────────
This plugin exports your samples to Google Earth for stunning
3D visualization on a global scale.

THREE TIERS OF FEATURES:

TIER 1 - Basic KML Export (Requires: simplekml)
• Create KML file with color-coded pins
• Auto-open in Google Earth
• Sample details in popups
• Perfect for presentations

TIER 2 - Advanced Features (Requires: simplekml)
• Custom pin icons and styles
• Rich HTML data cards
• Animated tours
• Photo integration
• 3D terrain draping

TIER 3 - Earth Engine (Requires: earthengine-api + GEE account)
• Satellite imagery overlays
• DEM integration
• Advanced geospatial analysis
• Cloud-based processing

═══════════════════════════════════════════════════════════════

DATA REQUIREMENTS
────────────────────────────────────────────────────────────────
Your samples MUST have:
• Latitude (decimal degrees)
• Longitude (decimal degrees)

Optional but recommended:
• Elevation (meters) - for 3D effect

Example good coordinates:
✓ Latitude: 32.5420
✓ Longitude: 35.2167
✓ Elevation: 450

═══════════════════════════════════════════════════════════════

INSTALLATION
────────────────────────────────────────────────────────────────

For Basic KML Export:
    pip3 install simplekml

For Earth Engine (optional):
    pip3 install earthengine-api

If pip3 not found:
    python -m pip install simplekml earthengine-api
    python3 -m pip install simplekml earthengine-api

═══════════════════════════════════════════════════════════════

BASIC WORKFLOW
────────────────────────────────────────────────────────────────

1. Make sure samples have Latitude/Longitude
2. Go to "Basic KML Export" tab
3. Choose your options:
   ✓ Auto-open in Google Earth
   ✓ Use elevation data
   ✓ Organize into folders
4. Click "Export to Google Earth"
5. Save KML file
6. Google Earth opens automatically!

═══════════════════════════════════════════════════════════════

UNDERSTANDING THE VISUALIZATION
────────────────────────────────────────────────────────────────

Color Coding:
• 🔴 Red pins = Egyptian (Haddadin Flow)
• 🟠 Orange pins = Sinai Ophiolitic
• 🟢 Green pins = Local Levantine
• 🟣 Purple pins = Harrat Ash Shaam
• 🟡 Yellow pins = Sinai/Transitional

Clicking a Pin Shows:
• Sample ID
• Final Classification
• Zr, Nb, Cr, Ni values (ppm)
• Zr/Nb ratio
• Elevation (if available)

═══════════════════════════════════════════════════════════════

ADVANCED FEATURES EXPLAINED
────────────────────────────────────────────────────────────────

Custom Pin Styles:
Use different icon shapes for different sample types
(e.g., circles for sherds, squares for tools)

Data Cards:
Rich HTML popups with:
• Spider diagrams
• Classification confidence
• All geochemical data
• Links to photos

Animated Tours:
Create automatic fly-throughs showing:
• Sample locations in sequence
• Archaeological sites
• Trade routes
• Provenance regions

Distance Lines:
Connect related samples to show:
• Trade networks
• Distribution patterns
• Source-to-site connections

Regions/Polygons:
Draw areas showing:
• Source regions (Golan, Sinai, etc.)
• Archaeological sites
• Geological provinces

═══════════════════════════════════════════════════════════════

GOOGLE EARTH ENGINE
────────────────────────────────────────────────────────────────

What You Can Do:
• Overlay samples on satellite imagery
• Integrate with Digital Elevation Models
• Analyze terrain around sample locations
• Study landscape evolution
• Correlate geology with sample chemistry

Requirements:
1. Google Earth Engine account (free for research)
2. Sign up: https://earthengine.google.com/signup/
3. Install: pip3 install earthengine-api
4. Authenticate using the plugin

Note: Earth Engine features are OPTIONAL and advanced.
Basic KML export works perfectly without it!

═══════════════════════════════════════════════════════════════

USE CASES
────────────────────────────────────────────────────────────────

Archaeological Presentations:
• Show excavation sites in 3D
• Fly through different periods
• Demonstrate trade networks
• Impress reviewers!

Publication Supplementary Materials:
• Interactive KML files for journals
• Readers can explore your data
• More engaging than static maps
• Easy to share

Field Planning:
• Visualize sampling coverage
• Identify gaps
• Plan new excavations
• Share with field teams

Education:
• Teaching provenance concepts
• Show students real data
• Interactive learning
• Makes archaeology exciting!

═══════════════════════════════════════════════════════════════

TIPS & TRICKS
────────────────────────────────────────────────────────────────

For Best Results:
1. Check coordinates before export
2. Use elevation data if available
3. Organize into folders by classification
4. Add descriptive names to samples
5. Include photos when possible

Sharing Your KML:
• KML files are small (~few KB)
• Email to collaborators
• Upload to Google Drive
• Include in publications
• Works on mobile too!

Google Earth Controls:
• Left mouse: Rotate globe
• Right mouse: Tilt view
• Scroll: Zoom in/out
• Double-click pin: Fly to location
• Use timeline for temporal data

Performance:
• KML handles thousands of samples
• Google Earth caches data
• Mobile version works too
• No internet needed after loading

═══════════════════════════════════════════════════════════════

TROUBLESHOOTING
────────────────────────────────────────────────────────────────

"No samples with coordinates":
→ Add Latitude/Longitude columns to your data
→ Make sure values are decimal degrees

"Google Earth won't open":
→ Install Google Earth Desktop (free)
→ Or use Google Earth Web (earth.google.com)
→ Check file associations

"Pins in wrong location":
→ Verify coordinate format
→ Check positive/negative signs
→ Ensure Lat/Long not swapped

"simplekml won't install":
→ Try: python -m pip install simplekml
→ Check internet connection
→ May need admin rights

═══════════════════════════════════════════════════════════════

WHY THIS IS AMAZING
────────────────────────────────────────════════════────────────

NO OTHER BASALT TOOLKIT HAS THIS!

IoGAS: ❌ No Google Earth export
Your Toolkit: ✅ One-click Google Earth

This gives you:
• Geographic context for your samples
• Visual trade route identification
• Stunning presentations
• Easy collaboration
• Professional publications

All with one click! 🌏✨

═══════════════════════════════════════════════════════════════

RESOURCES
────────────────────────────────────────────────────────────────

Google Earth Download:
https://www.google.com/earth/download/

Google Earth Web (no install):
https://earth.google.com/web/

Google Earth Engine:
https://earthengine.google.com/

simplekml Documentation:
https://simplekml.readthedocs.io/

═══════════════════════════════════════════════════════════════
"""

        text.insert('1.0', help_text)
        text.config(state='disabled')

    def _export_basic_kml(self):
        """Export basic KML file"""
        if not HAS_SIMPLEKML:
            response = messagebox.askyesno(
                "simplekml Required",
                "KML export requires simplekml.\n\n"
                "Install with: pip3 install simplekml\n\n"
                "Do you want to install it now?",
                parent=self.window
            )
            if response:
                self._install_simplekml()
            return

        # Get samples with coordinates
        samples_with_coords = []
        for s in self.app.samples:
            lat = safe_float(s.get('Latitude'))
            lon = safe_float(s.get('Longitude'))
            if lat is not None and lon is not None:
                samples_with_coords.append(s)

        if not samples_with_coords:
            messagebox.showwarning("No Coordinates",
                                 "No samples have Latitude/Longitude data.",
                                 parent=self.window)
            return

        # Get save path
        path = filedialog.asksaveasfilename(
            title="Save KML File",
            defaultextension=".kml",
            filetypes=[("KML files", "*.kml"), ("All files", "*.*")],
            parent=self.window
        )

        if not path:
            return

        try:
            import simplekml

            # Create KML
            kml = simplekml.Kml()
            kml.document.name = "Basalt Provenance Samples"

            # Color map (KML uses AABBGGRR format)
            color_map = {
                "EGYPTIAN (HADDADIN FLOW)": "ff0000ff",  # Red
                "EGYPTIAN (ALKALINE / EXOTIC)": "ff00ffff",  # Yellow
                "SINAI / TRANSITIONAL": "ff00a5ff",  # Orange
                "SINAI OPHIOLITIC": "ff0080ff",  # Dark orange
                "LOCAL LEVANTINE": "ff00ff00",  # Green
                "HARRAT ASH SHAAM": "ffff00ff",  # Purple
            }

            # Organize into folders if requested
            if self.organize_folders_var.get():
                folders = {}
                for sample in samples_with_coords:
                    classification = sample.get('Final_Classification',
                                               sample.get('Auto_Classification', 'UNKNOWN'))

                    if classification not in folders:
                        folders[classification] = kml.newfolder(name=classification)

                    self._add_sample_to_kml(folders[classification], sample, color_map)
            else:
                # Add all samples to main document
                for sample in samples_with_coords:
                    self._add_sample_to_kml(kml, sample, color_map)

            # Save KML
            kml.save(path)

            # Auto-open if requested
            if self.auto_open_var.get():
                self._open_in_google_earth(path)

            messagebox.showinfo("KML Exported",
                              f"Successfully exported {len(samples_with_coords)} samples!\n\n"
                              f"File: {path}\n\n"
                              f"{'Google Earth should open automatically.' if self.auto_open_var.get() else 'Open the file in Google Earth to view.'}",
                              parent=self.window)

        except Exception as e:
            messagebox.showerror("Export Error",
                               f"Error exporting KML:\n\n{str(e)}",
                               parent=self.window)
    
    def _open_google_earth_web(self):
        """Open Google Earth Web in browser centered on samples"""
        
        # Get samples with coordinates
        samples_with_coords = []
        for s in self.app.samples:
            lat = safe_float(s.get('Latitude'))
            lon = safe_float(s.get('Longitude'))
            if lat is not None and lon is not None:
                samples_with_coords.append({'lat': lat, 'lon': lon})
        
        if not samples_with_coords:
            # No coordinates - just open Google Earth Web
            messagebox.showinfo("Opening Google Earth Web",
                              "No samples with coordinates found.\n\n"
                              "Google Earth Web will open, but you'll need to\n"
                              "manually navigate to your region of interest.\n\n"
                              "To see your samples: Add Latitude/Longitude\n"
                              "columns to your data and re-import.",
                              parent=self.window)
            webbrowser.open("https://earth.google.com/web/")
            return
        
        # Calculate center point of all samples
        avg_lat = sum(s['lat'] for s in samples_with_coords) / len(samples_with_coords)
        avg_lon = sum(s['lon'] for s in samples_with_coords) / len(samples_with_coords)
        
        # Calculate approximate zoom level based on spread
        lats = [s['lat'] for s in samples_with_coords]
        lons = [s['lon'] for s in samples_with_coords]
        lat_range = max(lats) - min(lats)
        lon_range = max(lons) - min(lons)
        max_range = max(lat_range, lon_range)
        
        # Estimate altitude for view (in meters)
        # Smaller range = closer view
        if max_range < 0.01:  # ~1 km
            altitude = 1000
        elif max_range < 0.1:  # ~10 km
            altitude = 5000
        elif max_range < 1:  # ~100 km
            altitude = 50000
        else:
            altitude = 500000
        
        # Build Google Earth Web URL
        # Format: https://earth.google.com/web/@lat,lon,altitude,0y,0h,0t,0r
        url = f"https://earth.google.com/web/@{avg_lat},{avg_lon},{altitude}d,35y,0h,0t,0r"
        
        # Open in browser
        try:
            webbrowser.open(url)
            messagebox.showinfo("Google Earth Web",
                              f"Opening Google Earth Web in your browser!\n\n"
                              f"Centered on: {avg_lat:.4f}°, {avg_lon:.4f}°\n"
                              f"Showing {len(samples_with_coords)} sample location(s)\n\n"
                              f"Note: To see pins on the map, you'll need to:\n"
                              f"1. Export KML file first\n"
                              f"2. Upload it to Google Earth Web (My Places)",
                              parent=self.window)
        except Exception as e:
            messagebox.showerror("Browser Error",
                               f"Could not open browser:\n\n{str(e)}\n\n"
                               f"You can manually visit:\n"
                               f"https://earth.google.com/web/",
                               parent=self.window)

    def _add_sample_to_kml(self, kml_parent, sample, color_map):
        """Add a single sample to KML"""
        import simplekml

        lat = safe_float(sample['Latitude'])
        lon = safe_float(sample['Longitude'])
        elev = safe_float(sample.get('Elevation', 0))

        if elev is None:
            elev = 0
        elif not self.include_elevation_var.get():
            elev = 0

        # Create point
        sample_id = sample.get('Sample_ID', 'Unknown')
        pnt = kml_parent.newpoint(name=sample_id)
        pnt.coords = [(lon, lat, elev)]

        # Set color
        classification = sample.get('Final_Classification',
                                   sample.get('Auto_Classification', 'UNKNOWN'))
        pnt.style.iconstyle.color = color_map.get(classification, 'ffffffff')
        pnt.style.iconstyle.scale = 1.2

        # Create description
        zr = sample.get('Zr_ppm', 'N/A')
        nb = sample.get('Nb_ppm', 'N/A')
        cr = sample.get('Cr_ppm', 'N/A')
        ni = sample.get('Ni_ppm', 'N/A')

        # Calculate ratio
        try:
            if zr != 'N/A' and nb != 'N/A' and float(nb) > 0:
                ratio = float(zr) / float(nb)
                ratio_str = f"{ratio:.2f}"
            else:
                ratio_str = "N/A"
        except:
            ratio_str = "N/A"

        description = f"""
        <b>Sample ID:</b> {sample_id}<br/>
        <b>Classification:</b> {classification}<br/>
        <br/>
        <b>Geochemistry:</b><br/>
        Zr: {zr} ppm<br/>
        Nb: {nb} ppm<br/>
        Cr: {cr} ppm<br/>
        Ni: {ni} ppm<br/>
        Zr/Nb: {ratio_str}<br/>
        """

        if elev and elev != 0:
            description += f"<br/><b>Elevation:</b> {elev:.0f} m"

        pnt.description = description

    def _export_advanced_kml(self):
        """Export KML with advanced features"""
        messagebox.showinfo("Advanced Features",
                          "Advanced KML features are coming in v10.2!\n\n"
                          "For now, use Basic KML Export which provides:\n"
                          "• Color-coded pins\n"
                          "• Sample details\n"
                          "• Folder organization\n"
                          "• 3D elevation support\n\n"
                          "This covers 90% of use cases!",
                          parent=self.window)

    def _authenticate_earth_engine(self):
        """Authenticate with Google Earth Engine"""
        if not HAS_EARTHENGINE:
            response = messagebox.askyesno(
                "Earth Engine Not Installed",
                "Earth Engine requires earthengine-api package.\n\n"
                "Install with: pip3 install earthengine-api\n\n"
                "Do you want to install it now?",
                parent=self.window
            )
            if response:
                self._install_earthengine()
            return

        try:
            import ee
            ee.Authenticate()
            messagebox.showinfo("Authentication",
                              "Please follow the instructions in your browser\n"
                              "to authenticate with Google Earth Engine.",
                              parent=self.window)
        except Exception as e:
            messagebox.showerror("Authentication Error",
                               f"Error: {str(e)}",
                               parent=self.window)

    def _open_in_google_earth(self, kml_path):
        """Open KML file in Google Earth"""
        try:
            if sys.platform == 'win32':
                os.startfile(kml_path)
            elif sys.platform == 'darwin':  # macOS
                subprocess.call(['open', kml_path])
            else:  # Linux
                subprocess.call(['xdg-open', kml_path])
        except Exception as e:
            # Silent fail - user can open manually
            pass

    def _install_simplekml(self):
        """Install simplekml dependency"""
        self._install_packages(["simplekml"], "simplekml")

    def _install_earthengine(self):
        """Install earthengine-api dependency"""
        self._install_packages(["earthengine-api"], "Earth Engine API")

    def _install_packages(self, packages, feature_name):
        """Install packages using the plugin manager"""
        # First try to use plugin manager if available
        if hasattr(self.app, 'open_plugin_manager'):
            # We can trigger installation through plugin manager
            messagebox.showinfo(
                "Install via Plugin Manager",
                f"Please install {feature_name} dependencies:\n\n"
                f"Packages: {', '.join(packages)}\n\n"
                f"1. Go to Tools → Plugin Manager\n"
                f"2. Find 'Google Earth Export' plugin\n"
                f"3. Click 'Install' button\n"
                f"4. Restart application after installation",
                parent=self.window
            )
            self.window.destroy()  # Close current window
            self.app.open_plugin_manager()
        else:
            # Manual installation instructions
            pip_cmd = "pip3 install " + " ".join(packages)
            python_cmd = "python -m pip install " + " ".join(packages)
            python3_cmd = "python3 -m pip install " + " ".join(packages)

            messagebox.showinfo(
                "Install Manually",
                f"To install {feature_name}, run in terminal:\n\n"
                f"Option 1 (recommended):\n"
                f"  {pip_cmd}\n\n"
                f"Option 2 (if pip3 not found):\n"
                f"  {python3_cmd}\n\n"
                f"Option 3 (if above doesn't work):\n"
                f"  {python_cmd}\n\n"
                f"After installation, restart the application.",
                parent=self.window
            )
    # ADD THIS NEW METHOD RIGHT HERE:
    def _auto_adjust_window(self):
        """Auto-adjust window size based on content"""
        # Update window to calculate actual size
        self.window.update_idletasks()

        # Get the requested size (what the widgets want)
        width = self.window.winfo_reqwidth()
        height = self.window.winfo_reqheight()

        # Add some padding
        width = min(width + 20, 1000)  # Max width 1000px
        height = min(height + 40, 750)  # Max height 750px

        # Get screen dimensions
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()

        # Center window
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)

        # Set geometry
        self.window.geometry(f"{width}x{height}+{x}+{y}")
