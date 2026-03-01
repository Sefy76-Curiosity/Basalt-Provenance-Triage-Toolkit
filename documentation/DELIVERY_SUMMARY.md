🎉 Scientific Toolkit v2.5 - Complete Package
✅ All Features Successfully Integrated

Last updated: February 28, 2026

📦 What's New in v2.5 (Summary)
Feature                 Description
🧠 Toolkit AI v2.2      Built-in AI assistant — scans all plugins/schemes, recommends workflows,
                        suggests and installs plugins. Offline, no API key required.
🔬 Field Panels v3.0    16 domain-specific right panels (geochemistry, spectroscopy, zooarch, etc.)
                        Auto-detect data type and switch panel. Embedded live diagrams.
📊 Statistical Console  Plain-language stats for non-programmers. Summary, correlate, t-test,
                        groups — all via buttons or text commands. No scipy required.
🎬 Macro Recorder+      Extended from 4 to 13 recordable action types: now captures protocol runs,
                        column sorts, tab switches, scheme changes, pagination, and more.
💾 Auto-Save (Fixed)    Thread-safe auto-save with atomic writes. Two threading.Lock objects
                        prevent race conditions. Crash recovery prompt on startup.
🎨 ttkbootstrap UI      Full UI migration from tkinter.ttk to ttkbootstrap across all panels,
                        dialogs, and features. Modern themed look throughout.
📁 Sample Data +20      16 new domain-specific test CSV files (one per field panel domain).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📦 Complete File Inventory

Core Application Files
File                        Size    Description
Scientific-Toolkit.py       ~300 KB Main application entry point (ttkbootstrap UI)
data_hub.py                 18 KB   Central data management with observer pattern
color_manager.py            12 KB   Manages classification colors and themes
update_checker.py           8 KB    GitLab/GitHub update checking

UI Modules (ui/)
File                            Size    Description
left_panel.py                   ~35 KB  Data import, manual entry, hardware buttons
center_panel.py                 ~55 KB  Main data table, plots tab, status bar,
                                        Statistical Console integration
right_panel.py                  ~30 KB  Classification HUD, scheme selection,
                                        field panel switcher
right_panel_archaeology.py      ~25 KB  NEW — Archaeology/archaeometry field panel
right_panel_chromatography.py   ~23 KB  NEW — Chromatography field panel
right_panel_electrochem.py      ~23 KB  NEW — Electrochemistry field panel
right_panel_geochemistry.py     ~27 KB  NEW — Geochemistry panel (TAS + AFM embedded)
right_panel_geochronology.py    ~23 KB  NEW — Geochronology field panel
right_panel_geophysics.py       ~24 KB  NEW — Geophysics field panel
right_panel_materials.py        ~23 KB  NEW — Materials science field panel
right_panel_meteorology.py      ~26 KB  NEW — Meteorology field panel
right_panel_molecular.py        ~25 KB  NEW — Molecular biology field panel
right_panel_petrology.py        ~25 KB  NEW — Petrology field panel
right_panel_physics.py          ~25 KB  NEW — Physics/measurement field panel
right_panel_solution.py         ~29 KB  NEW — Solution chemistry field panel
right_panel_spatial.py          ~25 KB  NEW — Spatial/GIS field panel
right_panel_spectroscopy.py     ~32 KB  NEW — Spectroscopy field panel
right_panel_structural.py       ~26 KB  NEW — Structural geology field panel
right_panel_zooarch.py          ~22 KB  NEW — Zooarchaeology field panel
right_panel_patch.py            ~3 KB   Selection-sync patch documentation
results_dialog.py               6 KB    Classification results popup
all_schemes_detail_dialog.py    6 KB    "Run All" results viewer
__init__.py                     0.5 KB  Package init

Engines (2 engines + classification/protocol files)
Component                   Count   Location
Classification Engine       1       engines/classification_engine.py
Classification Schemes      70      engines/classification/*.json
Protocol Engine             1       engines/protocol_engine.py (JSON-based, v2.5)
Scientific Protocols        50      engines/protocols/*.json
Derived Fields              1       engines/derived_fields.json

Plugins
Category            Count   Location
Software Plugins    37      plugins/software/*.py
Add-on Plugins      25      plugins/add-ons/*.py  (was 23 — added toolkit_ai, statistical_console)
Hardware Suites     16      plugins/hardware/*.py  (was 7 files — expanded to 16 suites)
Plugin Registry     1       plugins/plugins.json
Plugin Manager      1       plugins/plugin_manager.py

Notable New Add-ons
File                            Size    Description
plugins/add-ons/toolkit_ai.py   ~120 KB NEW — Built-in AI assistant v2.2
                                         Plugin recommendation, scheme lookup,
                                         offline, no API key
plugins/add-ons/statistical_console.py
                                ~34 KB  NEW — Stats console for non-programmers
                                         Summary, describe, correlate, groups, t-test

Productivity Features (features/)
File                        Size    Description
auto_save.py                ~6 KB   Thread-safe auto-save with atomic writes (UPDATED)
macro_recorder.py           ~40 KB  Workflow recorder — 13 action types (UPDATED)
project_manager.py          8 KB    Saves/loads complete project state
script_exporter.py          11 KB   Exports workflows as Python/R scripts
tooltip_manager.py          3 KB    Hover tooltips for all UI elements
recent_files_manager.py     3 KB    Tracks last 10 opened files
__init__.py                 0.5 KB  Package initialization

Configuration (config/)
File                        Description
chemical_elements.json      Column name mappings (58 KB)
scatter_colors.json         Classification color schemes
user_settings.json          User preferences (auto-created)
recent_files.json           Recent files list (auto-created)
macros.json                 Saved macros (auto-created)
disabled_schemes.json       Disabled classification schemes
ai_knowledge_cache.json     NEW — Toolkit AI plugin/scheme scan cache (auto-created, 1h TTL)

Sample Data (samples/) — 30+ files
File                            Description
master_test_list.csv            Master test dataset (multi-domain)
classifications_master_test.csv Classification test data
geochemistry.csv                Geochemistry examples
geochemistry_location.csv       Geochemistry with coordinates
structural_data.csv             Structural geology data
thermobarometry_test_data.csv   Thermobarometry examples
Geochemistry.csv                Extended geochemistry test set
archaeology_test.csv            NEW — Archaeology field panel test data
chromatography_test.csv         NEW — Chromatography field panel test data
electrochem_test.csv            NEW — Electrochemistry field panel test data
geochemistry_test.csv           NEW — Geochemistry field panel test data
geochronology_test.csv          NEW — Geochronology field panel test data
geophysics_test.csv             NEW — Geophysics field panel test data
materials_test.csv              NEW — Materials science field panel test data
meteorology_test.csv            NEW — Meteorology field panel test data
molecular_test.csv              NEW — Molecular biology field panel test data
petrology_test.csv              NEW — Petrology field panel test data
physics_test.csv                NEW — Physics field panel test data
solution_test.csv               NEW — Solution chemistry field panel test data
spatial_test.csv                NEW — Spatial/GIS field panel test data
spectroscopy_test.csv           NEW — Spectroscopy field panel test data
structural_test.csv             NEW — Structural geology field panel test data
zooarch_test.csv                NEW — Zooarchaeology field panel test data

Auto-Save Directory (auto_save/) — auto-created
File                    Description
recovery.stproj         Auto-saved project recovery file (created automatically)
                        Atomic write pattern — never partially written

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Summary Stats v2.0 → v2.5
Metric                  v2.0    v2.5    Change
Classification Engines  70      70      —
Scientific Protocols    50      50      —
Software Plugins        37      37      —
Add-on Plugins          23      25      +2 (toolkit_ai, statistical_console)
Hardware Suites         7 files 16      +9 suites
Domain Field Panels     0       16      +16 NEW
Recordable Macro Types  4       13      +9 NEW
UI Framework            ttk     ttkbootstrap  Migrated
Sample Test Files       10      30+     +20 NEW
Auto-Save               Basic   Thread-safe + atomic  Fixed
Toolkit AI              —       v2.2    NEW

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 License & Contact

License: CC BY-NC-SA 4.0
    ✅ Free for research, education, museums, and commercial use
    ❌ Cannot sell or incorporate into commercial products

Author:     Sefy Levy
Email:      sefy76@gmail.com
GitLab:     https://gitlab.com/sefy76/scientific-toolkit
DOI:        https://doi.org/10.5281/zenodo.18727756
Citation:   Levy, S. (2026). Scientific Toolkit v2.5 [Computer software].
