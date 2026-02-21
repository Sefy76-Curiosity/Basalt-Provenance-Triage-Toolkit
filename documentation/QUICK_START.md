🚀 Quick Start Guide

Get Scientific Toolkit running in 5 minutes.
*70 classification engines · 50 protocols · 37 software plugins · 23 add-ons · 7 hardware suites*
⚠️ Before You Start

This software is provided "AS IS" - you are responsible for validating results.

    Always check that results make sense for your samples

    Verify methods are appropriate for your data type

    Report bugs and issues on GitLab

    Read citations for methods you use

Found a problem? → https://gitlab.com/sefy76/scientific-toolkit/-/issues
✅ Prerequisites
Requirement	Minimum	Recommended
Python	3.8	3.10+
pip	Any version	Latest
Disk Space	50 MB	500 MB (with all plugins)
RAM	2 GB	4 GB
OS	Windows 10, macOS 10.14, Linux	Latest versions
📦 Installation (3 minutes)
Step 1: Download
bash

# Clone the repository
git clone https://gitlab.com/sefy76/scientific-toolkit.git
cd scientific-toolkit

# Or download ZIP from GitLab and extract

Step 2: Install Dependencies

Choose your installation type:
Installation	Command	What You Get
Minimal	pip install numpy pandas matplotlib	Core features, 70 engines, basic plotting
Standard	pip install -r requirements.txt	All 37 software plugins + 23 add-ons
Hardware	Add pyserial hidapi bleak	All 7 hardware suites
Full	All of the above	Everything
Step 3: Launch
bash

python Scientific-Toolkit.py

Windows users: Double-click Scientific-Toolkit.py
First launch: May take 30-60 seconds to initialize plugins
🎯 First Use (2 minutes)
1. Load Sample Data
text

File → Import Data → CSV
Navigate to /samples/master_test_list.csv
Click Open

✅ You should see data loaded in the main table (center panel)
2. Run Your First Classification
text

Classify → Geochemistry → TAS Volcanic Classification

✅ Results dialog shows rock types for your samples
✅ Click "Add to Dataset" to save classifications
3. Create Your First Plot
text

1. Select samples (Ctrl+Click or Shift+Click)
2. Visualize → Scatter Plot
3. X-axis: SiO2_wt%
4. Y-axis: Na2O_wt + K2O_wt
5. Click "Plot"

✅ Congratulations! You've created a TAS diagram
4. Try a Protocol
text

Protocols → Behrensmeyer Weathering Protocol
Select a sample with weathering data
Run protocol

✅ Returns weathering stage (0-5) with description
🧭 Understanding the Interface
Main Window Layout
text

┌─────────────────────────────────────────────────────────────┐
│  Menu Bar: File | Classify | Protocols | Visualize | Hardware │
├─────────┬───────────────────────────┬───────────────────────┤
│  LEFT   │        CENTER              │        RIGHT          │
│  Panel  │     (Data Table)           │       Panel           │
│  (10%)  │        80%                 │        (10%)          │
│         │                            │                       │
│ 📂 Import│ Sample_ID  Zr_ppm  Nb_ppm  │   🔬 Classification   │
│ 📝 Manual│ HAZ-001    245     22.3    │   • TAS Diagram       │
│ Entry   │ HAZ-002    238     21.8    │   • AFM Series        │
│         │ HAZ-003    252     23.1    │   • REE Patterns      │
│ 🔌      │ ...                       │   ▶ Apply              │
│ Hardware│                            │                       │
│ Buttons │                            │   📊 HUD Preview       │
└─────────┴───────────────────────────┴───────────────────────┘
│  Status: 156 samples | 24 columns | Memory: 245MB | Ready   │
└─────────────────────────────────────────────────────────────┘

Key Controls
Shortcut	Action
Ctrl+A	Select all samples
Ctrl+F	Focus search box
Ctrl+S	Save project
Delete	Remove selected samples
Right-click	Context menu with quick actions
F1	Keyboard shortcuts help
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
text

File → Import Data → Choose format → Select file

Task 2: Connect a Hardware Device

Example: Mitutoyo Digital Caliper
text

Hardware → Physical Properties → Digital Calipers
Select brand: Mitutoyo
Connection: USB HID
Click "Connect"
Place caliper in measurement field
Click "Read"

✅ Value appears in the field

All 7 hardware suites work the same way:

    Barcode/QR Scanner

    Elemental Geochemistry

    Mineralogy (RRUFF)

    Physical Properties

    Solution Chemistry

    Spectroscopy

    Zooarchaeology

Task 3: Apply a Classification

Example: Soil Texture

    Ensure you have Sand_%, Silt_%, Clay_% columns

    Classify → Soil Science → USDA Soil Texture

    Results show texture class (e.g., "Loam", "Sandy Clay")

    Click "Add to Dataset"

Available classifications: 70 across all fields
Task 4: Run a Protocol

Example: Zooarchaeology Fragmentation
text

Protocols → Zooarchaeology Fragmentation Protocol
Select sample with bone measurements
Run protocol

✅ Returns fragmentation index, breakage pattern, freshness
Task 5: Statistical Analysis

Example: PCA
text

1. Select samples with numeric data
2. Advanced → PCA+LDA Explorer
3. Choose variables (e.g., Zr, Nb, Ba, Rb)
4. Click "Run PCA"
5. Interactive biplot appears with variance explained

Task 6: Export Publication Figure
text

1. Create your plot
2. Plot → Apply Template → Journal Styles → Nature Style
3. Adjust labels as needed
4. File → Export → High-Resolution PDF
5. 300 DPI publication-ready output

🔍 Example Workflows by Field
🌋 Igneous Petrology Workflow
text

1. Import XRF data (CSV or direct from instrument)
2. Classify → TAS Volcanic Classification (Le Bas et al. 1986)
3. Classify → AFM Series (Irvine & Baragar 1971)
4. Classify → REE Patterns (Sun & McDonough 1989)
5. Software → Advanced Normative Calculations (CIPW norm)
6. Visualize → Ternary Diagram (QAPF)
7. Apply Template → AGU Style
8. Export → PDF

Time: 5 minutes | Outputs: Rock type, magma series, normative minerals
🦴 Zooarchaeology Workflow
text

1. Hardware → Zooarchaeology Suite → Connect calipers
2. Measure bone (GL, Bd, SD, etc.)
3. Protocol → Behrensmeyer Weathering Protocol
4. Protocol → Shipman & Rose Burning Protocol
5. Classify → Bone Collagen QC (C:N ratio)
6. Classify → Trophic Level (Sr/Ca)
7. Software → Zooarchaeology Analytics (NISP/MNI)
8. Export results to CSV

Time: 10 minutes | Outputs: Species, age, taphonomy, diet
⛏️ Field Geology Workflow
text

1. Hardware → GNSS (connect Emlid Reach)
2. Start streaming position
3. Hardware → pXRF (connect SciAps/Bruker)
4. Scan samples in field
5. Data auto-imports with coordinates
6. Classify → Provenance Fingerprinting
7. Visualize → 3D GIS Viewer
8. Export → Google Earth KML

Time: Real-time | Outputs: Geochemical maps with coordinates
🌱 Soil Science Workflow
text

1. Import field data (texture, EC, pH, coordinates)
2. Classify → USDA Soil Texture
3. Classify → Soil Salinity (EC-based)
4. Classify → Soil Sodicity (SAR)
5. Protocol → USDA Soil Morphology Protocol
6. Visualize → 3D GIS Viewer with terrain
7. Export → Google Earth KML

Time: 5 minutes | Outputs: Soil classification, salinity hazard, 3D maps
⏳ Geochronology Workflow
text

1. Import LA-ICP-MS data
2. Software → LA-ICP-MS Pro (signal processing)
3. Software → Geochronology Suite
4. Plot U-Pb concordia (Wetherill or Tera-Wasserburg)
5. Calculate ages with discordance filter
6. Export ages to main table

Time: 10 minutes | Outputs: U-Pb ages, concordia diagrams
🧪 Isotope Geochemistry Workflow
text

1. Import Sr-Nd-Pb isotope data
2. Software → Isotope Mixing Models
3. Select end-members (MORB, OIB, EM1, EM2, HIMU)
4. Run binary or ternary mixing
5. Optional: Monte Carlo for uncertainty
6. Optional: Bayesian MCMC inversion
7. Export mixing proportions

Time: 5 minutes | Outputs: Mixing proportions, provenance
🔌 Enabling Optional Features
Enable AI Assistants
text

Advanced → Plugin Manager → Add-ons → Select AI plugin
Click "Install Dependencies" (auto-installs required packages)
Enter API key when prompted

Free options:

    Ollama AI - Fully local, no API key needed

    Claude/Gemini/ChatGPT - Free tiers available

Enable Advanced Plotting

Already included in full installation:

    Matplotlib Plotter: Standard plots

    Seaborn Plotter: Statistical visualizations

    Ternary Plotter: Three-component diagrams

    GIS Plotter: Spatial maps with basemaps

Enable Hardware Devices

No additional software needed - plugins auto-detect:

    USB serial (XRF, FTIR, GPS, meters)

    USB HID (calipers)

    Bluetooth LE (wireless devices)

    File monitoring (universal fallback)

🆘 Troubleshooting Quick Fixes
"Module not found" error
bash

pip install [module-name]
# Or use Plugin Manager (auto-installs dependencies)

Data won't import

    Check file encoding (UTF-8 recommended)

    Ensure first row has column headers

    Check for special characters in column names

    Try: File → Import Data → CSV with explicit delimiter

Classification returns no results

    Verify required columns exist (check engine documentation)

    Check for numeric data (not text) in measurement columns

    Look for missing values (NaN)

    Try with sample data first to verify engine works

Protocol fails

    Check that all required fields are present

    Verify data types (text vs numbers)

    Some protocols need specific fields (e.g., weathering stage needs integer)

Hardware not detected

    Check USB connection

    Ensure device is powered on

    Linux: Add user to dialout group

    Windows: Install device driver

    Try File Monitor fallback

Plots look wrong

    Try different templates (some optimize for B&W, others for color)

    Check data ranges (outliers can skew axes)

    Use "Auto-scale" button to reset view

    Log scale may help with wide ranges

Slow performance

    Large datasets (>10,000 samples)? Enable pagination in settings

    Close unused plugin windows

    Restart application to clear memory

    Use filters to work with subsets

📚 Next Steps
Learn More
Document	What It Covers
User Guide	Complete reference for all features
CITATIONS.md	200+ academic citations for all methods
Plugin Guide	Deep dive into all 67 plugins
Protocol Guide	Using the 50 scientific protocols
Hardware Guide	Setting up all 7 hardware suites
Get Help

    FAQ - Common questions answered

    Troubleshooting - Detailed problem solving

    GitLab Issues - Ask the community

Contribute

    Share your workflows

    Request new features

    Report bugs

    Add translations

    Create new classification schemes

💡 Tips for Success

✅ Start small: Import 10-20 samples to learn the interface
✅ Use sample data: Practice with included datasets in /samples/
✅ One field at a time: Don't try to learn all fields at once
✅ Read descriptions: Hover over engines to see what they do
✅ Save often: Projects save to .stproj files (Ctrl+S)
✅ Use macros: Record repetitive tasks (Ctrl+R to start)
✅ Explore templates: Try different journal styles
✅ Join community: Share questions and discoveries
✅ Report bugs: Every report makes the software better
✅ Cite properly: Use CITATIONS.md for references
📋 Quick Reference Card
File Operations
Action	Menu Path	Shortcut
Import CSV	File → Import Data → CSV	Ctrl+I
Save Project	File → Save Project	Ctrl+S
Open Project	File → Open Project	Ctrl+O
Export CSV	File → Export → CSV	Ctrl+E
Export Script	File → Export to Python Script	(menu)
Classification (70 engines)
Field	Menu Path
Geochemistry	Classify → Geochemistry
Metamorphic	Classify → Metamorphic
Sedimentology	Classify → Sedimentology
Archaeology	Classify → Archaeology
Soil Science	Classify → Soil Science
Environmental	Classify → Environmental
Meteoritics	Classify → Meteoritics
Isotope	Classify → Isotope Geochemistry
Protocols (50 workflows)
Field	Menu Path
Taphonomy	Protocols → Behrensmeyer Weathering
Sediment	Protocols → Folk–Shepard Texture
Environmental	Protocols → Hakanson Ecological Risk
Igneous	Protocols → IUGS Igneous
Zooarch	Protocols → Maresha Zooarchaeology
Visualization
Plot Type	Menu Path
Scatter	Visualize → Scatter Plot
Ternary	Visualize → Ternary Diagram
Spider	Visualize → REE Spider
3D Map	Advanced → 3D GIS Viewer
Statistical	Advanced → PCA+LDA Explorer
Hardware (7 suites)
Device Category	Menu Path
Barcode/QR	Hardware → Barcode Scanner
XRF	Hardware → Elemental Geochemistry
Mineralogy	Hardware → Mineralogy
Calipers/Balances	Hardware → Physical Properties
pH/EC Meters	Hardware → Solution Chemistry
Spectrometers	Hardware → Spectroscopy
Zooarchaeology	Hardware → Zooarchaeology
🎉 You're Ready!

You now know enough to:

    ✅ Import data from files or instruments

    ✅ Run 70 classification engines

    ✅ Execute 50 scientific protocols

    ✅ Create publication-quality plots

    ✅ Export results and scripts

    ✅ Record macros for automation

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

Every bug report and piece of feedback makes this better for the entire scientific community.
📞 Quick Contacts

    Email: sefy76@gmail.com

    GitLab Issues: https://gitlab.com/sefy76/scientific-toolkit/-/issues

    DOI: https://doi.org/10.5281/zenodo.18499129

Questions? See FAQ or open an issue on GitLab.

Want to go deeper? Continue to User Guide.
<p align="center"> <a href="README.md">← Back to Main</a> • <a href="INSTALLATION.md">Installation Details</a> • <a href="USER_GUIDE.md">Full User Guide →</a> </p>
📊 Quick Stats Summary
Category	Count
Classification Engines	70
Scientific Protocols	50
Software Plugins	37
Add-on Plugins	23
Hardware Suites	7
Total Plugins	67
Built-in Citations	200+
Sample Files	15+
Lines of Code	~77,000

⬇️ Download Now | ⭐ Star on GitLab | 🐛 Report Bug
