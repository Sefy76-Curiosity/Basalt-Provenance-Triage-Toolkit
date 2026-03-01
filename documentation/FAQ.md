❓ Frequently Asked Questions

Honest answers to common questions about Scientific Toolkit.
Updated February 2026 to reflect v2.5 (70 engines, 50 protocols, 90+ plugins, 16 hardware suites,
16 field panels, Toolkit AI, Statistical Console, extended Macro Recorder, thread-safe Auto-Save).

⚠️ DISCLAIMER: Read This First

This software is provided "AS IS" without any warranty.

Your responsibilities as a user:
    Validate all results — Check that classifications make sense for your samples
    Verify methods are appropriate — Not every classification applies to every sample type
    Check your input data — Errors in your data = errors in results
    Use scientific judgment — This is a tool to assist you, not replace expertise
    Report bugs and issues — If something seems wrong, report it!

This is scientific software in active development. You MUST:
    Understand the methods you're using (read the citations)
    Verify results are reasonable for your samples
    Cross-check critical results with other methods/tools
    Report any bugs or unexpected behavior

We rely on users to test and report issues. Your bug reports help everyone.
→ Report issues on GitLab

📊 Quick Stats Reference
Category                Count
Classification Engines  70
Scientific Protocols    50
Software Plugins        37
Add-on Plugins          25
Hardware Suites         16
Domain Field Panels     16
Total Plugins           90+
Built-in Citations      200+
Lines of Code           ~100,000+
Active Development      2024–2026

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
General Questions
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

What is Scientific Toolkit?

A free, open-source desktop application (Python / ttkbootstrap) for scientific data analysis
across multiple domains: geochemistry, archaeology, soil science, meteoritics, spectroscopy,
zooarchaeology, and many more. It combines data management, 70 classification engines,
50 scientific protocols, 90+ plugins, 16 hardware integration suites, 16 domain-specific
field panels, and a built-in AI assistant — all in one tool.

Who made this?

Created by Sefy Levy, based on the Basalt Provenance Triage Toolkit v10.2.
Implements published scientific methods from 200+ researchers worldwide (see CITATIONS.md).

Is it really free?

Yes, completely free under CC BY-NC-SA 4.0 license.
Free for research, education, museums, and commercial use forever.

Can I use this for commercial work?

Yes! You can use Scientific Toolkit for commercial purposes — a mining company can use
it for exploration, a consulting firm for client work, a museum for paid exhibitions.

What you CANNOT do:
    ❌ Sell the software itself (charging for Scientific Toolkit)
    ❌ Incorporate the code into commercial products you sell
    ❌ Take the code and use it in proprietary software you're selling

Example scenarios:
Scenario                                                Allowed?
Mining company uses toolkit for client soil analysis    ✅ ALLOWED
Museum uses it to classify artifacts for exhibitions    ✅ ALLOWED
Consultant uses it to generate reports for customers    ✅ ALLOWED
Company sells "GeoAnalyzer Pro" based on this code      ❌ NOT ALLOWED
Charging $500 for the toolkit download                  ❌ NOT ALLOWED

Contact sefy76@gmail.com to discuss commercial licensing of the source code.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 Capabilities
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

What can Scientific Toolkit do?
Category            Capabilities
Classification      70 engines (TAS, AFM, REE, soil texture, bone diagenesis,
                    meteorite shock, etc.)
Protocols           50 multi-stage workflows (Behrensmeyer, EPA, IUGS, Maresha, etc.)
Software Analysis   37 plugins (PCA/LDA, geochronology, isotope mixing, normative
                    calculations, 14 discipline suites)
Hardware            16 suites (archaeology, barcode, chromatography, clinical,
                    electrochemistry, elemental, geophysics, materials, meteorology,
                    molecular bio, physical, physics, solution chemistry,
                    spectroscopy, thermal, zooarchaeology)
Plotting            25 add-ons (matplotlib, seaborn, ternary, GIS, ASCII, missingno,
                    6 consoles including Statistical Console, 7+ AI assistants)
Field Panels        16 domain-specific right panels (v3.0): geochemistry, spectroscopy,
                    zooarchaeology, structural, spatial, petrology, geochronology,
                    geophysics, archaeology, chromatography, electrochem, materials,
                    solution, molecular, meteorology, physics
AI Assistants       8 options: Toolkit AI (built-in, offline), Claude, ChatGPT,
                    Gemini, DeepSeek, Grok, Copilot, Ollama

What can't it do?
    ❌ Handle massive datasets (performance degrades >10,000 samples)
    ❌ Replace specialized commercial tools in their single domains
    ❌ Provide enterprise-level support contracts
    ❌ Run in a web browser (desktop only)
    ❌ Replay manual in-table cell edits in macros (coming in future release)

How does this compare to commercial software?
Tool                Cost            Strengths                               Weaknesses
ioGAS               $2,000+/year    Polished UI, mining focus               Expensive, no hardware, no archaeology
GCDkit              Free            Excellent igneous petrology             R-based, steep learning curve
PAST                Free            400+ statistical tests                  1990s UI, limited geochemistry
SPSS                $1,500+/year    Advanced statistics                     Expensive, no geochemistry
Scientific Toolkit  Free            Cross-disciplinary, hardware, AI,       Smaller community
                                    16 field panels, 16 hardware suites

Best use: Budget-constrained researchers, students, teaching labs, cross-disciplinary
projects, museums, field work with portable instruments.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💻 Installation & Technical
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

What are the system requirements?
Component   Minimum                         Recommended
Python      3.8                             3.10+
OS          Windows 10, macOS 10.14, Linux  Latest versions
RAM         2 GB                            4 GB (8 GB for large datasets)
Disk Space  50 MB                           500 MB (with all plugins)
Display     1280×800                        1920×1080

See INSTALLATION.md for details.

Do I need to know Python?

No. This is a GUI application — you interact through menus and buttons.
However, knowing Python helps if you want to create custom plugins or modify engines.

Is ttkbootstrap required?

Yes, as of v2.5. The entire UI has been migrated to ttkbootstrap for a modern look
and consistent theming. Install it with:

    pip install ttkbootstrap

Does it work offline?

Yes! All functionality works offline except:
    AI assistant plugins using external APIs (Claude, ChatGPT, Gemini, etc.)
    Downloading additional dependencies via Plugin Manager
    Some online data sources (EarthChem, USGS)

Toolkit AI (built-in) works 100% offline — no API key needed.

How do I update to new versions?

    cd scientific-toolkit
    git pull origin main
    pip install --upgrade -r requirements.txt

Your data, projects, and settings are preserved.
Clear the AI knowledge cache after updates: delete config/ai_knowledge_cache.json
so Toolkit AI rescans the new plugins.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📁 Data & Files
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

What file formats are supported?

Import:
    ✅ CSV (any delimiter)
    ✅ Excel (.xlsx, .xls)
    ✅ Tab-delimited text
    ✅ Hardware-specific: Bruker, Niton, Olympus, SciAps, Thermo
    ✅ Spectral: .spa, .opj, .dpt, .wdf, .ngs, .jdx
    ✅ Images: .jpg, .png, .tif (for lithics/photos)

Export:
    ✅ CSV
    ✅ Excel
    ✅ JSON
    ✅ PDF (figures)
    ✅ PNG/SVG (figures)
    ✅ KML (for Google Earth)
    ✅ Shapefile (GIS)

Can I save my work and come back later?

Yes. Projects are saved as .stproj files (JSON format). They store:
    All sample data
    Column order and structure
    Current filters and search terms
    Selected classification scheme
    Active field panel (NEW in v2.5)
    UI state (tabs, page numbers)
    Window size and position

Auto-save creates recovery.stproj every 5 minutes and prompts for recovery on startup
if unsaved work is detected (see Auto-Save section below).

How big can my datasets be?
Size                Performance
<1,000 samples      ✅ Smooth, instant
1,000–5,000 samples ⚠️ Good, slight delay on some operations
5,000–10,000 samples ⚠️ Slower but usable
>10,000 samples     ❌ Not recommended

For large datasets: use filters, enable pagination, or export to R/Python.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧬 Classifications & Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

How many classification engines are there?

70 classification engines + 50 protocols across 2 engine types:
Engine Type             Count   Description
Classification Engine   70      Rule-based JSON schemes
Protocol Engine         50      Multi-stage workflows

These cover: Geochemistry (20+), Metamorphic petrology (5+), Sedimentology (12+),
Geochronology (3+), Isotope geochemistry (3+), Environmental (8+), Soil science (8+),
Archaeology (10+), Meteoritics (6+), Archaeometallurgy (5+), Hydrogeochemistry (5+),
Provenance & tectonics (5+), Alteration & weathering (3+), Analytical QA/QC (4+).

Are the methods peer-reviewed?

Yes. We implement published methods from scientific literature.
See CITATIONS.md for all 200+ references.

Can I add my own classification schemes?

Yes! Classification engines are JSON files in engines/classification/:
    Copy _TEMPLATE.json to a new file
    Add your rules using supported operators (>, <, between, etc.)
    Save and restart — your scheme appears in the dropdown

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔬 Field Panels (NEW in v2.5)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

What are Field Panels?

Field Panels are domain-specific right-panel modules (v3.0) that replace the
Classification HUD when a recognised data type is loaded. They show live diagrams,
computed summaries, and domain-relevant derived values — all updated instantly
when you select rows in the main table.

16 domains are supported: geochemistry, geochronology, petrology, structural,
geophysics, spatial, archaeology, zooarchaeology, spectroscopy, chromatography,
electrochemistry, materials, solution chemistry, molecular biology,
meteorology, and physics.

How does auto-detection work?

When data is imported, the right panel checks column names against each domain's
detection list. If a match is found (e.g., sio2, tio2, al2o3 → geochemistry),
a prompt appears: "Switch to [Domain] Panel?" Clicking Yes loads the field panel.
The ← Back button always returns you to the Classification HUD.

Can I switch panels manually?

Yes. The right panel menu lets you load any of the 16 field panels regardless of
auto-detection — useful when columns are named non-standardly.

Does the geochemistry panel actually draw diagrams?

Yes. The Geochemistry Field Panel embeds live Matplotlib/TkAgg figures directly
inside the right panel, rendering a TAS diagram (Le Bas et al. 1986), AFM diagram,
and Mg# histogram. These update as you select or deselect rows.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧠 Toolkit AI (NEW in v2.5)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

What is Toolkit AI? How is it different from the other AI plugins?

Toolkit AI is a built-in AI assistant (v2.2) that understands the toolkit's own
structure. It scans every plugin file at startup using static AST analysis, reads
all classification scheme JSON files, and builds an internal knowledge index.

Unlike external AI plugins (Claude, ChatGPT, Gemini), Toolkit AI:
    - Requires no API key
    - Works completely offline
    - Knows every plugin, scheme, and field panel by name
    - Can recommend plugins based on your data type
    - Can trigger one-click plugin installation

Can Toolkit AI recommend plugins for my data?

Yes. Based on what data you've loaded and what analyses you've run,
Toolkit AI suggests relevant plugins. For example:
    Loading geochemistry data → suggests Thermobarometry Suite, Normative Calculator
    Loading spectral data → suggests Spectral Toolbox, MCR-ALS
    Loading zooarch data → suggests Zooarchaeology Analysis Suite

Does Toolkit AI need internet access?

No. It scans the local codebase only. Internet is only needed if you ask it to
check the online plugin store for new plugins to download.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Statistical Console (NEW in v2.5)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

What is the Statistical Console?

A plain-language statistics terminal for users who aren't programmers.
It runs inside the center panel as its own tab, with a dark terminal-style interface.

One-click buttons run: Summary, Describe, Correlate, Groups, T-Test.
Text commands at the 📊> prompt offer finer control.

Does it require scipy or R?

No. It uses Python's built-in statistics module only.
No additional dependencies beyond the core install.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎬 Macro Recorder
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

What actions can the macro recorder capture?

As of v2.5, 13 action types are captured:
    import_file, add_row, classify, scheme_changed, run_protocol, sort_by,
    tab_switched, generate_plot, apply_filter, delete_selected, update_row,
    prev_page, next_page

Previous versions only captured 4 action types. The new types include protocol
execution, column sorting, tab switching, scheme dropdown changes, pagination,
and DataHub row updates.

Can I replay macros on different datasets?

Yes. Macros are replayed against whatever data is currently loaded.
File paths recorded during import will be replayed literally — use macro
editing (export → edit JSON → import) to update paths.

What about manual cell edits?

Manual in-table cell edits are intercepted but not yet fully replayed.
The action type is reserved for a future release. Other edit actions
(delete_selected, update_row via DataHub) are captured and replayed.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💾 Auto-Save
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

How does auto-save work?

Every 5 minutes (configurable), the background thread checks for unsaved changes.
If found, it writes project data to auto_save/recovery.stproj using an atomic
write-then-rename pattern — meaning the recovery file is never in a partial state.

What was the race condition that was fixed?

The previous version called data_hub.mark_saved() from the background thread with
no lock, while the UI thread could be modifying data simultaneously.
v2.5 adds two threading.Lock objects (_save_lock and _data_lock) that guard all
shared state between the UI and background threads.

Will I be prompted to recover if the application crashed?

Yes. On startup, if recovery.stproj is less than 24 hours old, a dialog asks:
"Found unsaved work from [time]. Would you like to recover it?"
Yes loads it; No deletes the file.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔌 Hardware Integration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Which instruments are supported?

16 hardware suites supporting hundreds of device models:
Suite                           Devices Supported
Archaeology & Archaeometry      UAV/GNSS systems, portable XRF, GPR
Barcode/QR Scanner              Zebra, Honeywell, Datalogic, Socket, Inateck (50+ models)
Chromatography & Analytical     GC, HPLC, IC (Agilent, Thermo, Waters, Shimadzu)
Clinical & Molecular Diagnostics PCR, plate readers, sequencers, clinical analyzers
Electrochemistry                Potentiostats, galvanostats, impedance analyzers
Elemental Geochemistry          SciAps X-550/X-505, Olympus Vanta/Delta, Bruker S1/Tracer,
                                Thermo Niton, ICP-MS
Geophysics                      Magnetometers, gravimeters, seismographs, GPR
Materials Characterization      SEM/EDX, XRD, nanoindentation, hardness testers
Meteorology & Environmental     Weather stations, air quality monitors (Davis, Vaisala)
Molecular Biology               Spectrophotometers, gel imagers, qPCR systems
Physical Properties             AGICO Kappabridge, Bartington MS2/MS3, Mitutoyo calipers,
                                Sylvac Bluetooth, Mahr, iGaging
Physics Test & Measurement      Oscilloscopes, multimeters (Keysight, Tektronix, Rigol)
Solution Chemistry              Mettler Toledo, Thermo Orion, Hanna, Horiba LAQUA (45+ models)
Spectroscopy                    Thermo Nicolet, PerkinElmer, Bruker ALPHA, Agilent,
                                B&W Tek Raman, Ocean Optics, Avantes (50+ models)
Thermal Analysis & Calorimetry  DSC, TGA, TMA, DMA (Netzsch, TA Instruments)
Zooarchaeology                  Mitutoyo calipers, Sylvac Bluetooth, Ohaus/Sartorius balances,
                                Emlid Reach GNSS, Dino-Lite microscopes

What if my instrument isn't supported?

Option 1: File Monitor — watches a folder and auto-imports CSV/Excel from your instrument
Option 2: Universal Parser — handles any 2-column or tabular CSV
Option 3: Create a plugin — follow patterns in existing hardware plugins

Do I need special drivers?

Usually not. USB serial, USB HID, Bluetooth, and file monitoring all use OS-native support.
Some Windows devices may need a manufacturer's USB serial driver (FTDI, Prolific, etc.).

Linux users: add yourself to the dialout group:
    sudo usermod -a -G dialout $USER    # then log out and back in

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 Visualization & Plotting
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

What plot types are available?

Built-in (from add-on plugins):
    Scatter plots, ternary diagrams, REE spider diagrams
    Bar charts, histograms, box plots, violin plots (seaborn)
    Heatmaps, contour plots, 3D scatter/surface
    GIS maps with terrain, ASCII art plots, missing data visualizations

From software plugins:
    PCA biplots, LDA projections, U-Pb concordia diagrams
    Ar-Ar age spectra, KDE density plots, ternary mixing diagrams

From Field Panels (NEW in v2.5):
    TAS diagram (embedded in Geochemistry Panel)
    AFM diagram (embedded in Geochemistry Panel)
    Mg# histogram (embedded in Geochemistry Panel)
    Domain-specific plots in all 16 panels

Are plots publication-quality?

Yes. Export as PDF (vector), SVG (editable), PNG (adjustable DPI), or EPS (LaTeX).
Journal-specific templates: Nature, Science, AGU, Elsevier, GSA.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 AI Features
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

How many AI assistants are available?

8 total:
Plugin          Provider        Requires
Toolkit AI      Built-in        Nothing — offline, no API key
Claude AI       Anthropic       API key (free tier available)
ChatGPT         OpenAI          API key (free tier available)
Gemini AI       Google          API key (free tier available)
DeepSeek AI     DeepSeek        API key (free tier available)
Grok AI         xAI             API key
Copilot AI      Microsoft       API key
Ollama AI       Local           Ollama installation (free, no key, offline)

What's the difference between Toolkit AI and the other AI plugins?

Toolkit AI knows the toolkit. It scans all plugins and schemes and recommends
workflows based on what you've actually installed and loaded. It cannot answer
general scientific questions about topics outside the toolkit.

External AI plugins (Claude, ChatGPT, etc.) can answer general scientific questions
and interpret your data in broad context, but don't inherently know the toolkit's
structure unless you explain it.

Is my data sent to AI companies?

Only if you use external AI assistant plugins AND explicitly query them.
Your data stays local otherwise. Toolkit AI and Ollama never send anything externally.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🐞 Errors & Troubleshooting
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"No module named ttkbootstrap"

    pip install ttkbootstrap

"Module not found" for other packages

    pip install [module-name]
    # OR use Plugin Manager (auto-installs)

Classification returns no results
    Required columns missing — check engine description
    Data is text instead of numbers
    Missing values (NaN) in critical columns

Field panel not auto-switching
    Column names must match standard abbreviations (e.g., sio2, tio2 for geochemistry)
    Case-insensitive but spelling must be correct
    Test with one of the domain CSV files in samples/

Toolkit AI not appearing
    Enable via: Advanced → Plugin Manager → Add-ons → Toolkit AI
    If knowledge cache is stale: delete config/ai_knowledge_cache.json

Recovery prompt not showing after crash
    The recovery file may be more than 24 hours old (auto-ignored)
    Check auto_save/recovery.stproj manually

Application is slow
    Large dataset? Try filtering/paging (bottom right)
    Many plugins loaded? Close unused windows
    Restart application to clear memory

Hardware device not detected
    Check USB connection and power
    Correct port selected?
    Linux: user in dialout group?
    Windows: driver installed?
    Try Hardware → File Monitor as fallback

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤝 Contributing & Development
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Can I contribute?

Yes! Contributions welcome:
Contribution Type   How to Help
Bug reports         Open GitLab issue with details
Feature requests    Describe what you need
Classification      Add JSON schemes to engines/classification/
Protocols           Create multi-stage workflow JSON files
Hardware plugins    Add new device support
Field panels        New domain panels following FieldPanelBase
Documentation       Improve guides, fix typos
Testing             Try on your hardware, report results
Sample data         Share anonymised domain test files

I found a bug. What should I do?

1. Search existing issues (may already be reported)
2. Test with sample data from /samples/ to confirm it's reproducible
3. Open issue at https://gitlab.com/sefy76/scientific-toolkit/-/issues

Include: OS, Python version, full error message, steps to reproduce.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💭 Misc
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Why ttkbootstrap instead of vanilla tkinter/ttk?

ttkbootstrap provides a modern, themed widget set built on top of tkinter.
The migration (completed in v2.5) gives the UI:
    - Consistent modern theming across all panels
    - Better visual hierarchy
    - Easier widget styling (bootstyle= parameter)
    - No external dependency beyond Python

Why was this created?

To provide free, integrated tools for budget-constrained researchers.
Many labs cannot afford $5,000–8,000/year in software subscriptions.

Software                    Annual Cost
ioGAS                       ~$2,000
SPSS                        ~$1,500
ArcGIS                      ~$1,600
MATLAB                      ~$2,150
Specialized petrology tools ~$1,000–3,000
Total commercial stack       $5,000–10,000/year
Scientific Toolkit           $0

What's the long-term plan?

Timeline    Plans
2026 Q2     Video tutorials, more classification engines
2026 Q3     Performance optimization for large datasets
2026 Q4     Peer-reviewed methods publication
2027        Community plugin repository, possible web interface

Will this always be free?

Yes. Free to use forever. Just don't try to sell it or profit from the code itself.

📝 Still have questions?

    Email:         sefy76@gmail.com
    GitLab Issues: https://gitlab.com/sefy76/scientific-toolkit/-/issues
    Documentation: See /documentation/ folder for all guides

📋 Quick Reference
Topic                   Go To
Getting started         QUICK_START.md
Installation            INSTALLATION.md
All 10 features         ENHANCED_FEATURES_README.md
Citations               CITATIONS.md
Structure guide         STRUCTURE_GUIDE.md

This FAQ is updated based on real user questions. Last updated: February 2026 (v2.5)
