🚀 Quick Start Guide

Get Scientific Toolkit running in 5 minutes.
*70 classification engines · 50 protocols · 37 software plugins · 25 add-ons · 16 hardware suites*

⚠️ Before You Start

This software is provided "AS IS" - you are responsible for validating results.

    Always check that results make sense for your samples
    Verify methods are appropriate for your data type
    Report bugs and issues on GitLab
    Read citations for methods you use

Found a problem? → https://gitlab.com/sefy76/scientific-toolkit/-/issues

✅ Prerequisites
Requirement     Minimum             Recommended
Python          3.8                 3.10+
pip             Any version         Latest
Disk Space      50 MB               500 MB (with all plugins)
RAM             2 GB                4 GB
OS              Windows 10,         Latest versions
                macOS 10.14, Linux

📦 Installation (3 minutes)
Step 1: Download

    # Clone the repository
    git clone https://gitlab.com/sefy76/scientific-toolkit.git
    cd scientific-toolkit

    # Or download ZIP from GitLab and extract

Step 2: Install Dependencies

Choose your installation type:
Installation    Command                                         What You Get
Minimal         pip install numpy pandas matplotlib             Core features, 70 engines, basic plotting
Standard        pip install -r requirements.txt                 All plugins + add-ons
Hardware        Add pyserial hidapi bleak                       All 16 hardware suites
Full            pip install -r requirements.txt                 Everything
                + pip install ttkbootstrap

Note: ttkbootstrap is required for the modern UI (v2.5+):
    pip install ttkbootstrap

Step 3: Launch

    python Scientific-Toolkit.py

Windows users: Double-click Scientific-Toolkit.py
First launch: May take 30-60 seconds to initialize plugins

🎯 First Use (2 minutes)
1. Load Sample Data

    File → Import Data → CSV
    Navigate to /samples/master_test_list.csv
    Click Open

✅ You should see data loaded in the main table (center panel)

2. Run Your First Classification

    Right panel → Select scheme from dropdown (e.g., TAS Volcanic Classification)
    Click Apply

✅ Results appear in the HUD and colour-code the table rows
✅ Double-click any row for the full classification detail

3. Try a Field Panel (NEW in v2.5)

    Import geochemistry data (e.g., samples/geochemistry_test.csv)
    Right panel shows: "Switch to Geochemistry Panel?"
    Click Yes
    See TAS diagram, AFM diagram, Mg# histogram — live!
    Use ← Back to return to the Classification HUD

4. Create Your First Plot

    Select samples (Ctrl+Click or Shift+Click)
    Visualize → Scatter Plot
    X-axis: SiO2_wt%
    Y-axis: Na2O_wt + K2O_wt
    Click "Plot"

✅ Congratulations! You've created a TAS diagram

5. Try a Protocol

    Protocols → Behrensmeyer Weathering Protocol
    Select a sample with weathering data
    Run protocol → Returns weathering stage (0–5) with description

🧭 Understanding the Interface
Main Window Layout

    ┌─────────────────────────────────────────────────────────────────┐
    │  Menu Bar: File | Classify | Protocols | Visualize | Hardware   │
    ├─────────┬─────────────────────────────┬─────────────────────────┤
    │  LEFT   │        CENTER               │        RIGHT            │
    │  Panel  │     (Data Table)            │   (Classification HUD   │
    │  (10%)  │        80%                  │    or Field Panel v3.0) │
    │         │                             │         (10%)           │
    │ 📂 Import│ Sample_ID  SiO2  TiO2 MgO  │   🔬 Geochemistry Panel  │
    │ 📝 Manual│ HAZ-001    48.3  1.2  7.4  │   TAS: Basalt            │
    │  Entry  │ HAZ-002    49.1  1.1  7.9  │   Mg#: 52.3              │
    │         │ HAZ-003    50.2  1.3  7.1  │   [TAS diagram embedded] │
    │ 🔌      │ ...                         │   ← Back to HUD         │
    │Hardware │                             │                         │
    └─────────┴─────────────────────────────┴─────────────────────────┘
    │  Status: 156 samples | 24 columns | Memory: 245MB | Ready       │
    └─────────────────────────────────────────────────────────────────┘

Key Controls
Shortcut    Action
Ctrl+A      Select all samples
Ctrl+F      Focus search box
Ctrl+S      Save project
Ctrl+R      Start macro recording
Ctrl+M      Manage macros
Delete      Remove selected samples
Right-click Context menu with quick actions
F1          Keyboard shortcuts help
F5          Refresh all panels

📋 Common First Tasks
Task 1: Import Your Own Data

Supported formats:
    ✅ CSV files (any delimiter)
    ✅ Excel (.xlsx, .xls)
    ✅ Tab-delimited text
    ✅ Spectral files (.spa, .opj, .dpt)

Required columns:
    Sample_ID (will auto-generate if missing)
    Your measurement columns (any naming works)

Import steps:
    File → Import Data → Choose format → Select file

Task 2: Connect a Hardware Device

Example: Mitutoyo Digital Caliper

    Hardware → Physical Properties → Digital Calipers
    Select brand: Mitutoyo
    Connection: USB HID
    Click "Connect"
    Place caliper in measurement field
    Click "Read"

✅ Value appears in the field

All 16 hardware suites work the same way:

    Archaeology & Archaeometry
    Barcode/QR Scanner
    Chromatography & Analytical
    Clinical & Molecular Diagnostics
    Electrochemistry
    Elemental Geochemistry
    Geophysics
    Materials Characterization
    Meteorology & Environmental
    Molecular Biology
    Physical Properties
    Physics Test & Measurement
    Solution Chemistry
    Spectroscopy
    Thermal Analysis & Calorimetry
    Zooarchaeology

Task 3: Apply a Classification

Example: Soil Texture
    1. Ensure you have Sand_%, Silt_%, Clay_% columns
    2. Classify → Soil Science → USDA Soil Texture
    3. Results show texture class (e.g., "Loam", "Sandy Clay")
    4. Click "Add to Dataset"

Available classifications: 70 across all fields

Task 4: Use a Domain Field Panel (NEW in v2.5)

Each of the 16 supported domains has a dedicated analysis panel.
Example: Zooarchaeology
    1. Import samples/zooarch_test.csv
    2. Right panel prompts: "Switch to Zooarchaeology Panel?"
    3. Click Yes — see NISP/MNI summaries, element distribution
    4. Select specific rows — panel updates instantly
    5. Click ← Back to return to Classification HUD

Task 5: Run a Protocol

Example: Zooarchaeology Fragmentation

    Protocols → Zooarchaeology Fragmentation Protocol
    Select sample with bone measurements
    Run protocol → Returns fragmentation index, breakage pattern, freshness

Task 6: Statistical Analysis (NEW in v2.5)

Example: Quick Summary
    1. Advanced → Plugin Manager → Add-ons → Statistical Console → Enable
    2. Open Statistical Console tab in center panel
    3. Click 📊 Summary button — instant column statistics
    4. Click 🔍 Correlate — pairwise correlation matrix
    5. Type: groups Classification — value counts by class

Task 7: Record a Macro

    1. Ctrl+R to start recording
    2. Import a file, run a classification, apply a filter
    3. Ctrl+T to stop recording
    4. Name it "My Pipeline"
    5. Ctrl+M → select it → Run
    ✅ All 13 action types are captured: imports, classifications, filters,
       sorts, tab switches, protocol runs, pagination, and more

Task 8: Statistical Analysis

Example: PCA
    1. Select samples with numeric data
    2. Advanced → PCA+LDA Explorer
    3. Choose variables (e.g., Zr, Nb, Ba, Rb)
    4. Click "Run PCA"
    5. Interactive biplot appears with variance explained

Task 9: Export Publication Figure

    1. Create your plot
    2. Plot → Apply Template → Journal Styles → Nature Style
    3. Adjust labels as needed
    4. File → Export → High-Resolution PDF
    5. 300 DPI publication-ready output

🔍 Example Workflows by Field

🌋 Igneous Petrology Workflow

    1. Import XRF data (CSV or direct from instrument)
    2. Import geochemistry_test.csv → switch to Geochemistry Field Panel
    3. Classify → TAS Volcanic Classification (Le Bas et al. 1986)
    4. Classify → AFM Series (Irvine & Baragar 1971)
    5. Classify → REE Patterns (Sun & McDonough 1989)
    6. Software → Advanced Normative Calculations (CIPW norm)
    7. Visualize → Ternary Diagram (QAPF)
    8. Apply Template → AGU Style
    9. Export → PDF

Time: 5 minutes | Outputs: Rock type, magma series, normative minerals

🦴 Zooarchaeology Workflow

    1. Hardware → Zooarchaeology Suite → Connect calipers
    2. Measure bone (GL, Bd, SD, etc.)
    3. Right panel: switch to Zooarchaeology Field Panel
    4. Protocol → Behrensmeyer Weathering Protocol
    5. Protocol → Shipman & Rose Burning Protocol
    6. Classify → Bone Collagen QC (C:N ratio)
    7. Classify → Trophic Level (Sr/Ca)
    8. Software → Zooarchaeology Analytics (NISP/MNI)
    9. Export results to CSV

Time: 10 minutes | Outputs: Species, age, taphonomy, diet

⛏️ Field Geology Workflow

    1. Hardware → GNSS (connect Emlid Reach)
    2. Start streaming position
    3. Hardware → pXRF (connect SciAps/Bruker)
    4. Scan samples in field
    5. Data auto-imports with coordinates
    6. Right panel: switch to Spatial Field Panel
    7. Classify → Provenance Fingerprinting
    8. Visualize → 3D GIS Viewer
    9. Export → Google Earth KML

Time: Real-time | Outputs: Geochemical maps with coordinates

🌱 Soil Science Workflow

    1. Import field data (texture, EC, pH, coordinates)
    2. Classify → USDA Soil Texture
    3. Classify → Soil Salinity (EC-based)
    4. Classify → Soil Sodicity (SAR)
    5. Protocol → USDA Soil Morphology Protocol
    6. Visualize → 3D GIS Viewer with terrain
    7. Export → Google Earth KML

Time: 5 minutes | Outputs: Soil classification, salinity hazard, 3D maps

⏳ Geochronology Workflow

    1. Import LA-ICP-MS data
    2. Right panel: switch to Geochronology Field Panel
    3. Software → LA-ICP-MS Pro (signal processing)
    4. Software → Geochronology Suite
    5. Plot U-Pb concordia (Wetherill or Tera-Wasserburg)
    6. Calculate ages with discordance filter
    7. Export ages to main table

Time: 10 minutes | Outputs: U-Pb ages, concordia diagrams

🌡️ Spectroscopy Workflow (NEW in v2.5)

    1. Hardware → Spectroscopy Suite → Connect spectrometer
    2. Collect spectra
    3. Right panel: switch to Spectroscopy Field Panel
    4. Software → Spectroscopy Analysis Suite
    5. Peak detection, baseline correction, library search
    6. Export: labelled spectra + peak table

Time: 5 minutes | Outputs: Identified compounds, peak assignments

🔌 Enabling Optional Features

Enable Toolkit AI (NEW in v2.5)

    Advanced → Plugin Manager → Add-ons → Toolkit AI → Enable
    No API key required — works offline
    Ask about your data, get plugin recommendations, understand methods

Enable Statistical Console (NEW in v2.5)

    Advanced → Plugin Manager → Add-ons → Statistical Console → Enable
    Instant statistics without any Python knowledge

Enable External AI Assistants

    Advanced → Plugin Manager → Add-ons → Select AI plugin
    Click "Install Dependencies" (auto-installs required packages)
    Enter API key when prompted

Free options:
    Ollama AI  — Fully local, no API key needed
    Claude/Gemini/ChatGPT — Free tiers available

Enable Advanced Plotting

Already included in full installation:
    Matplotlib Plotter: Standard plots
    Seaborn Plotter: Statistical visualizations
    Ternary Plotter: Three-component diagrams
    GIS Plotter: Spatial maps with basemaps

Enable Hardware Devices

No additional software needed — plugins auto-detect:
    USB serial (XRF, FTIR, GPS, meters)
    USB HID (calipers)
    Bluetooth LE (wireless devices)
    File monitoring (universal fallback)

🆘 Troubleshooting Quick Fixes

"Module not found" error

    pip install [module-name]
    # Or use Plugin Manager (auto-installs dependencies)

"No module named ttkbootstrap"

    pip install ttkbootstrap

Data won't import
    - Check file encoding (UTF-8 recommended)
    - Ensure first row has column headers
    - Check for special characters in column names
    - Try: File → Import Data → CSV with explicit delimiter

Classification returns no results
    - Verify required columns exist (check engine documentation)
    - Check for numeric data (not text) in measurement columns
    - Look for missing values (NaN)
    - Try with sample data first to verify engine works

Field panel not switching automatically
    - Column names must be recognised (check spelling of SiO2, TiO2, etc.)
    - The toolkit is case-insensitive but checks for standard abbreviations
    - Import one of the domain test files in samples/ to verify

Protocol fails
    - Check that all required fields are present
    - Verify data types (text vs numbers)
    - Some protocols need specific fields (e.g., weathering stage needs integer)

Hardware not detected
    - Check USB connection
    - Ensure device is powered on
    - Linux: Add user to dialout group
    - Windows: Install device driver
    - Try File Monitor fallback

Plots look wrong
    - Try different templates (some optimize for B&W, others for color)
    - Check data ranges (outliers can skew axes)
    - Use "Auto-scale" button to reset view
    - Log scale may help with wide ranges

📚 Next Steps
Learn More
Document                    What It Covers
ENHANCED_FEATURES_README    Complete guide to all 10 productivity features
CITATIONS.md                200+ academic citations for all methods
INSTALLATION.md             Detailed setup for all platforms
FAQ.md                      Common questions answered

Get Help
    FAQ — Common questions answered
    GitLab Issues — Ask the community
    Email: sefy76@gmail.com

💡 Tips for Success

✅ Start small: Import 10–20 samples to learn the interface
✅ Use sample data: 30+ domain test files in /samples/
✅ Let the AI guide you: Toolkit AI recommends the right plugins for your data
✅ Use Field Panels: Let the right panel switch to match your data domain
✅ Record macros: Ctrl+R to start — captures 13 types of actions
✅ One field at a time: Don't try to learn all fields at once
✅ Save often: Ctrl+S — auto-save also runs every 5 minutes
✅ Cite properly: Use CITATIONS.md for references
✅ Report bugs: Every report makes the software better

📋 Quick Reference Card

File Operations
Action          Menu Path                       Shortcut
Import CSV      File → Import Data → CSV        Ctrl+I
Save Project    File → Save Project             Ctrl+S
Open Project    File → Open Project             Ctrl+O
Export CSV      File → Export → CSV             Ctrl+E
Export Script   File → Export to Python Script  (menu)

Classification (70 engines)
Field           Menu Path
Geochemistry    Classify → Geochemistry
Metamorphic     Classify → Metamorphic
Sedimentology   Classify → Sedimentology
Archaeology     Classify → Archaeology
Soil Science    Classify → Soil Science
Environmental   Classify → Environmental
Meteoritics     Classify → Meteoritics
Isotope         Classify → Isotope Geochemistry

Field Panels (NEW — 16 domains)
Domain          Open via
Geochemistry    Auto-detect OR right panel menu
Spectroscopy    Auto-detect OR right panel menu
Zooarchaeology  Auto-detect OR right panel menu
[... all 16]    Auto-detect OR right panel menu

Protocols (50 workflows)
Field           Menu Path
Taphonomy       Protocols → Behrensmeyer Weathering
Sediment        Protocols → Folk–Shepard Texture
Environmental   Protocols → Hakanson Ecological Risk
Igneous         Protocols → IUGS Igneous
Zooarch         Protocols → Maresha Zooarchaeology

Hardware (16 suites)
Device Category     Menu Path
Archaeology         Hardware → Archaeology & Archaeometry
Barcode/QR          Hardware → Barcode Scanner
Chromatography      Hardware → Chromatography & Analytical
Clinical/Molecular  Hardware → Clinical & Molecular Diagnostics
Electrochemistry    Hardware → Electrochemistry
XRF/ICP-MS          Hardware → Elemental Geochemistry
Geophysics          Hardware → Geophysics
Materials           Hardware → Materials Characterization
Meteorology         Hardware → Meteorology & Environmental
Molecular Bio       Hardware → Molecular Biology
Calipers/Balances   Hardware → Physical Properties
Physics Instruments Hardware → Physics Test & Measurement
pH/EC Meters        Hardware → Solution Chemistry
Spectrometers       Hardware → Spectroscopy
DSC/TGA/TMA         Hardware → Thermal Analysis & Calorimetry
Zooarchaeology      Hardware → Zooarchaeology

🎉 You're Ready!

You now know enough to:
    ✅ Import data from files or instruments
    ✅ Run 70 classification engines
    ✅ Execute 50 scientific protocols
    ✅ View domain-specific Field Panels (16 domains)
    ✅ Create publication-quality plots
    ✅ Export results and scripts
    ✅ Record macros for automation (13 action types)
    ✅ Get AI-assisted guidance with Toolkit AI

Explore at your own pace. Scientific Toolkit grows with your needs.

🧪 Help Improve This Software

Your testing and feedback is essential!

As you use the toolkit:
    ✅ Verify results make sense for your samples
    ✅ Cross-check important results with other tools
    ✅ Report bugs or unexpected behavior
    ✅ Share what works well (and what doesn't)

Found an issue? → Report on GitLab
Everything working great? → Star the repository and tell colleagues!

📞 Quick Contacts
    Email:         sefy76@gmail.com
    GitLab Issues: https://gitlab.com/sefy76/scientific-toolkit/-/issues
    DOI:           https://doi.org/10.5281/zenodo.18727756

📊 Quick Stats Summary
Category                Count
Classification Engines  70
Scientific Protocols    50
Software Plugins        37
Add-on Plugins          25
Hardware Suites         16
Total Plugins           90+
Domain Field Panels     16
Built-in Citations      200+
Sample Files            30+
Lines of Code           ~100,000+

⬇️ Download Now | ⭐ Star on GitLab | 🐛 Report Bug
