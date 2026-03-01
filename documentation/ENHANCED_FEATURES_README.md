Scientific Toolkit v2.5
🎉 10 Core Productivity & Intelligence Features

This version adds 4 major new features on top of the original 6, transforming the toolkit into
a fully AI-assisted, domain-intelligent workflow platform.

📋 Feature Overview
Feature                    What It Does                                   Key Benefit
⌨️ Keyboard Shortcuts      20+ keyboard shortcuts for all operations       Save seconds on every action
📜 Recent Files            Auto-tracks last 10 opened files                Open recent work in 1 click
💡 Tooltips Everywhere     Helpful hints on all buttons/controls           No learning curve
💾 Project Save/Load       Complete workspace persistence                  Pick up where you left off
🐍 Script Export           Export workflows as Python/R                    Share, automate, document
🎬 Macro Recorder          Record/replay any workflow (13 action types)    Automate repetitive tasks
🧠 Toolkit AI v2.2         Built-in AI with plugin-aware deep knowledge    Instant expert guidance
🔬 Field Panels v3.0       16 domain-specific right panels                 Instant domain analysis
📊 Statistical Console     Plain-language stats for non-programmers        Stats without coding
💾 Auto-Save (Fixed)       Thread-safe auto-save with crash recovery       Never lose work again

────────────────────────────────────────────────────────────────────────────────────
⌨️ Feature 1: Keyboard Shortcuts
────────────────────────────────────────────────────────────────────────────────────

Save time with comprehensive keyboard shortcuts for all common operations.

Complete Shortcut Reference

File Operations (6 shortcuts)
Shortcut    Action              Menu Location
Ctrl+N      New Project         File → New Project
Ctrl+O      Open Project        File → Open Project
Ctrl+S      Save Project        File → Save Project
Ctrl+I      Import Data         File → Import Data
Ctrl+E      Export CSV          File → Export CSV
Ctrl+Q      Quit Application    File → Exit

Edit Operations (3 shortcuts)
Shortcut    Action              Menu Location
Delete      Delete Selected     Edit → Delete
Ctrl+A      Select All Rows     Edit → Select All
Ctrl+F      Focus Search Box    (direct action)

Workflow/Macros (3 shortcuts)
Shortcut    Action              Menu Location
Ctrl+R      Start Recording     Workflow → Start Recording
Ctrl+T      Stop Recording      Workflow → Stop Recording
Ctrl+M      Manage Macros       Workflow → Manage Macros

Navigation & Help (2 shortcuts)
Shortcut    Action              Menu Location
F1          Keyboard Shortcuts  Help → Keyboard Shortcuts
F5          Refresh All Panels  View → Refresh

Pro Tips
  - All shortcuts work on Windows, macOS (Cmd replaces Ctrl), and Linux
  - Shortcuts are shown in menu items (e.g., "Save Project  Ctrl+S")
  - Custom shortcuts can be added via _setup_keyboard_shortcuts() in main app

────────────────────────────────────────────────────────────────────────────────────
📜 Feature 2: Recent Files Manager
────────────────────────────────────────────────────────────────────────────────────

Quickly access your recently opened files from the File menu.

Features
  - Auto-tracking — Last 10 files automatically tracked
  - Smart display — Shows filenames with numbering (1–10)
  - Path preview — Hover to see full file path
  - Existence verification — Only shows files that still exist
  - Clear history — One-click to reset recent list

Usage
  Open recent file:  File → Recent Files → Click filename
  Clear list:        File → Recent Files → Clear Recent Files

Configuration
Recent files are stored in config/recent_files.json:

  {
    "files": [
      {
        "path": "/home/user/data/project1.csv",
        "name": "project1.csv",
        "timestamp": "2026-02-21T10:30:00"
      }
    ]
  }

────────────────────────────────────────────────────────────────────────────────────
💡 Feature 3: Tooltips Everywhere
────────────────────────────────────────────────────────────────────────────────────

Helpful tooltips appear when you hover over buttons and controls.

Coverage Map
UI Area         Tooltips Added
Left Panel      Import Data, Add Row, Manual Entry fields
Center Panel    Search, Filter, Pagination, Plot buttons
Right Panel     Classification schemes, Apply button, HUD elements
Field Panels    All 16 domain panels (NEW in v2.5)
File Menu       All menu items have descriptive tooltips
Dialogs         Results dialog, Project save/load dialogs

Technical Details
  - Delay: 500ms (configurable in tooltip_manager.py)
  - Style: Yellow background, black text, subtle border
  - Duration: Disappears when mouse moves away

Customization
  from tooltip_manager import ToolTip
  ToolTip(my_button, "This button does something cool")

────────────────────────────────────────────────────────────────────────────────────
💾 Feature 4: Project Save/Load
────────────────────────────────────────────────────────────────────────────────────

Save your entire workspace and restore it later with a single click.

What Gets Saved (Complete State)

📊 Data Layer
  ✅ All sample data with current values
  ✅ Column order and visibility settings
  ✅ Classification results and confidence scores
  ✅ Derived fields and calculations

🔍 UI State
  ✅ Current filters and search terms
  ✅ Selected rows and pagination position
  ✅ Active tab in notebook (Table/Plots)
  ✅ Selected classification scheme
  ✅ Window size and position
  ✅ Active field panel (NEW in v2.5)

⚙️ Settings
  ✅ Current theme/color scheme
  ✅ Column width preferences
  ✅ Recent files list (auto-saved separately)

File Format
Projects are saved as .stproj (Scientific Toolkit Project) — JSON format:

  {
    "metadata": {
      "version": "2.5",
      "saved_at": "2026-02-28T15:30:00",
      "app_version": "2.5",
      "project_name": "Hazor Excavation 2026"
    },
    "data": {
      "samples": [...],
      "column_order": ["Sample_ID", "Zr_ppm", "Nb_ppm", ...]
    },
    "ui_state": {
      "center": {
        "current_page": 3,
        "page_size": 50,
        "search_text": "SINAI",
        "filter_value": "All",
        "selected_tab": 0
      },
      "right": {
        "selected_scheme": "Basalt Triage",
        "run_target": "all",
        "active_field_panel": "geochemistry"
      },
      "window": { "geometry": "1400x900+100+50" }
    }
  }

Usage
  Save Project:  File → Save Project  (Ctrl+S)
  Load Project:  File → Open Project  (Ctrl+O)
  New Project:   File → New Project   (Ctrl+N) — confirms before clearing unsaved data

────────────────────────────────────────────────────────────────────────────────────
🐍 Feature 5: Script Export
────────────────────────────────────────────────────────────────────────────────────

Export your current workflow as executable Python or R code.

When you select File → Export to Python Script, you can choose:
Option                          Description                     When to Use
✅ Include current data          Embeds dataset in script        Sharing complete analysis
✅ Include classification logic  Exports classification functions Reproducing results
✅ Include plotting code          Generates matplotlib code       Creating publication figures
✅ Include current filters        Applies search/filter settings  Documenting subset analysis
✅ Make standalone               Creates runnable main()         Distribution to non-users

Use Cases
Collaboration    Share analysis with colleagues who don't have the toolkit
Publication      Include exact analysis code as supplementary material
Teaching         Students can run analysis without the GUI
Batch Processing Modify script to run on hundreds of files
Documentation    Generated code shows exactly what you did

────────────────────────────────────────────────────────────────────────────────────
🎬 Feature 6: Macro/Workflow Recorder  ← UPDATED in v2.5
────────────────────────────────────────────────────────────────────────────────────

Record any sequence of actions and replay them instantly.
Now captures 13 action types (previously 4).

What Can Be Recorded?
Category              Recordable Actions (v2.5)
File Operations       Import CSV/Excel, Export CSV, Save Project, Load Project
Classification        Run any classification scheme (all/selected), Run All Schemes
Scheme Selection      Dropdown changes recorded automatically (NEW)
Filtering             Apply search filters, filter by classification
Data Editing          Add rows, delete rows, update individual cells (NEW)
Plotting              Generate any plot type
Navigation            Page prev/next (NEW), tab switches (NEW)
Hardware/Protocols    Protocol execution (NEW)
Sorting               Column header clicks (NEW)

Complete List of Recorded Action Types
Action Type       Trigger
import_file       CSV/Excel import via left panel
add_row           Manual row addition
classify          Classification scheme run (records scheme + target)
scheme_changed    Scheme dropdown selection  ← NEW
run_protocol      Hardware protocol execution  ← NEW
sort_by           Column header click in main table  ← NEW
tab_switched      Tab change in center notebook  ← NEW
generate_plot     Plot generation
apply_filter      Filter/search applied
delete_selected   Row deletion
update_row        DataHub row update  ← NEW
prev_page         Pagination — previous page  ← NEW
next_page         Pagination — next page  ← NEW

How It Works
The recorder uses method patching to intercept UI events in real time.
When recording is active, each captured action is saved as a MacroAction:

  {
    "type": "classify",
    "params": { "scheme": "TAS", "target": "all" },
    "timestamp": "2026-02-27T14:32:01.123456"
  }

Macros are persisted to config/macros.json and survive application restarts.

How to Use
  1. Start:   Workflow → Start Recording  (Ctrl+R)
  2. Work:    Perform your workflow normally — all 13 action types captured
  3. Stop:    Workflow → Stop Recording   (Ctrl+T)
  4. Name:    Enter a descriptive name (e.g., "Hazor Daily Pipeline")
  5. Manage:  Ctrl+M — view, run, export, import, delete macros

Macro Manager Buttons
Button     Function
▶️ Run      Execute the macro immediately
📝 Details  Show step-by-step action list
💾 Export   Save macro to .json file
📥 Import   Load macro from .json file
🗑️ Delete   Remove macro

Error Handling During Replay
  - Stop on error  — Abort if any action fails
  - Continue       — Skip failed actions and proceed
  - Ask each time  — Prompt on each error

Known Limitation
  In-table manual cell edits are intercepted but not yet replayed in this version.
  The cell_edit action type is reserved for a future release.

Practical Examples

Example 1: Daily Data Processing
  1. Import today's pXRF data
  2. Run full classification suite
  3. Filter to SINAI samples
  4. Generate TAS diagram
  5. Export results
  → Record once, run every day in 1 click

Example 2: Publication Preparation
  1. Load project
  2. Apply specific filters
  3. Generate 4 publication plots
  4. Export as high-resolution PNG
  5. Save project
  → Reproduce figures exactly for revisions

────────────────────────────────────────────────────────────────────────────────────
🧠 Feature 7: Toolkit AI v2.2  ← NEW in v2.5
────────────────────────────────────────────────────────────────────────────────────

A built-in AI assistant with deep knowledge of the entire toolkit.
Unlike the external AI plugins (Claude, ChatGPT etc.), Toolkit AI understands
the toolkit's own structure — its plugins, classification schemes, and data workflows.

Enabling
  Advanced → Plugin Manager → Add-ons → Toolkit AI → Enable

What Toolkit AI Knows
  - Every plugin installed (scanned from source at startup)
  - Every classification scheme available
  - The toolkit's complete architecture and data flow
  - Appropriate scientific methods for your data type
  - Python package dependencies for all plugins

Key Capabilities

Plugin Recommendation Engine
  Based on your data type, Toolkit AI recommends relevant plugins and can
  trigger one-click installation:

  Domain                              Key Suggestions
  Geology & Geochemistry              Compositional Stats Pro, Thermobarometry Suite,
                                      Petrogenetic Modeling, Normative Calculator
  Archaeology & Archaeometry          Museum Database, Lithic Morphometrics,
                                      Report Generator, Photo Manager
  Spectroscopy                        Spectral Toolbox, Spectroscopy Analysis Suite
  GIS & Spatial                       Quartz GIS Pro, 3D GIS Viewer, Spatial Kriging
  Zooarchaeology                      Zooarchaeology Analysis Suite
  Chromatography                      Chromatography Analysis Suite
  Electrochemistry                    Electrochemistry Analysis Suite
  Materials Science                   Materials Science Analysis Suite
  Molecular Biology / Clinical        Clinical Diagnostics Suite
  General                             PCA/LDA Explorer, Uncertainty Propagation,
                                      Publication Layouts, DataPrep Pro

Deep Toolkit Knowledge
  Toolkit AI understands the full architecture:
  - Left Panel → DataHub → Center + Right panels (observer pattern)
  - How to apply classification schemes step by step
  - What hardware plugin maps to which field analysis panel
  - Which Python packages each plugin requires

Knowledge Caching
  - On first run, scans all plugins using static AST parsing (no import needed)
  - Cache saved to config/ai_knowledge_cache.json (1-hour TTL)
  - Rescans automatically when cache expires or plugins change
  - All scan errors are non-fatal and stored for diagnostics

How It Differs From External AI Plugins
  External AI plugins (Claude, ChatGPT, Gemini, etc.):
    - Require API keys
    - Can answer general scientific questions
    - Do not inherently know the toolkit's structure

  Toolkit AI:
    - No API key required
    - Knows every plugin, scheme, and field panel by scanning the codebase
    - Can trigger actions (install plugins, recommend workflows)
    - Works 100% offline

────────────────────────────────────────────────────────────────────────────────────
🔬 Feature 8: Intelligent Field Panels v3.0  ← NEW in v2.5
────────────────────────────────────────────────────────────────────────────────────

The right panel now automatically detects your data type and offers to switch to a
domain-specific analysis panel. The original Classification HUD remains accessible
via the ← Back button at any time.

16 Supported Scientific Domains
Panel ID        Human Name          Auto-Detected Columns / Data Type
geochemistry    Geochemistry        SiO2, TiO2, Al2O3, Fe2O3, MgO, CaO, Na2O, K2O
geochronology   Geochronology       U-Pb, Ar-Ar, and related radiometric fields
petrology       Petrology           Modal/normative mineralogy fields
structural      Structural Geology  Strike, dip, plunge, trend, azimuth
geophysics      Geophysics          Seismic, gravity, magnetics, ERT fields
spatial         Spatial / GIS       Latitude, longitude, UTM, easting/northing
archaeology     Archaeology         Lithic/artifact morphometrics, catalogue fields
zooarch         Zooarchaeology      NISP, MNI, taxon, skeletal element
spectroscopy    Spectroscopy        Wavelength/wavenumber vs intensity
chromatography  Chromatography      Retention time, peak area, m/z, abundance
electrochem     Electrochemistry    Potential, current, impedance, scan rate
materials       Materials Science   Stress, strain, hardness, elastic modulus
solution        Solution Chemistry  pH, conductivity, TDS, alkalinity
molecular       Molecular Biology   Ct, Cq, melt temperature, qPCR fields
meteorology     Meteorology         Temperature, humidity, pressure, wind, rainfall
physics         Physics             Time-series, FFT, signal, voltage

Geochemistry Panel — Detailed Features
  - Live TAS diagram (Le Bas et al. 1986) rendered inside the panel
  - AFM diagram and Mg# histogram
  - Derived values: oxide total, Mg#, FeOt, alkali sum
  - Updates dynamically when rows are selected in the main table
  - Fully scrollable interface

How Auto-Detection Works
  1. When data is loaded, the right panel inspects column names
  2. If recognised columns are found, a prompt offers to switch panels
  3. Switching loads the domain panel in place of the Classification HUD
  4. The ← Back button restores the Classification HUD

Hardware → Field Panel Auto-Mapping
  When hardware data is collected, the toolkit automatically maps the instrument
  to the appropriate field panel:

  spectroscopy_unified_suite           → spectroscopy panel
  elemental_geochemistry_unified_suite → geochemistry panel
  zooarchaeology_unified_suite         → zooarch panel
  archaeology_archaeometry_...         → archaeology panel
  ... (16 total hardware-to-panel mappings)

Selection Sync
  When you click rows in the main table, the active field panel updates immediately.
  This is managed by center_panel._notify_field_panel_selection() calling
  field_panel.on_selection_changed(selected_rows).

────────────────────────────────────────────────────────────────────────────────────
📊 Feature 9: Statistical Console  ← NEW in v2.5
────────────────────────────────────────────────────────────────────────────────────

A plain-language statistical console for users who aren't Python programmers.
Runs inside its own tab in the center panel.

Enabling
  Advanced → Plugin Manager → Add-ons → Statistical Console → Enable

Interface
  - Dark-themed terminal-style output area (Consolas font)
  - Command history — up/down arrow navigation
  - Quick-action toolbar with one-click buttons

One-Click Quick Commands
Button          Action
📊 Summary      Column-by-column descriptive statistics for all numeric fields
📈 Describe     Full describe across every numeric column
🔍 Correlate    Pairwise correlation matrix
📋 Groups       Value counts grouped by a categorical column
📉 T-Test       Two-sample t-test between two groups

Text Commands (typed at the 📊> prompt)
Command                                 Result
summary                                 Statistics for all numeric columns
describe                                Full describe
correlate                               Correlation between all numeric pairs
groups [column]                         Value counts for a categorical column
ttest [col] [group_col] [a] [b]         Two-sample t-test

No scipy required — uses Python's built-in statistics module.

────────────────────────────────────────────────────────────────────────────────────
💾 Feature 10: Auto-Save — Race Condition Fixed  ← UPDATED in v2.5
────────────────────────────────────────────────────────────────────────────────────

The auto-save system was completely rewritten to be thread-safe and use
atomic file writes, preventing corrupt saves and data loss.

What Was Fixed
  Previously, the background auto-save thread called data_hub.mark_saved()
  with no lock, while the UI thread could simultaneously modify data.
  This was a classic TOCTOU (time-of-check/time-of-use) race condition.

New Thread Safety
  Two threading.Lock objects now protect all shared state:

  Lock            Protects
  _save_lock      Prevents two concurrent save operations
  _data_lock      Guards all reads/writes to data_hub from background thread

Atomic Write Pattern
  The save now writes to a temp file first, then renames atomically:
  1. Write complete project data → recovery.tmp
  2. Rename recovery.tmp → recovery.stproj  (atomic on POSIX)
  This guarantees the recovery file is never in a partial/corrupt state.

Crash Recovery on Startup
  On launch, if auto_save/recovery.stproj exists and is less than 24 hours old,
  a recovery dialog appears:

    "Found unsaved work from 2026-02-27 14:32:01 (47 minutes ago).
     Would you like to recover it?"

  Yes → loads the recovery file and restores your session
  No  → deletes the recovery file, starts fresh

Status Bar Integration
  After each successful auto-save, the status bar briefly shows:
    💾 Auto-saved at 14:32:01

Configuration
  Parameter             Default     Description
  auto_save_interval    300 s       How often to auto-save (5 minutes)
  Recovery file path    auto_save/  Fixed location
                        recovery.stproj
  Max recovery age      24 hours    Older files are silently ignored

────────────────────────────────────────────────────────────────────────────────────
📦 Installation & Setup
────────────────────────────────────────────────────────────────────────────────────

File Structure (v2.5)

scientific-toolkit/
├── Scientific-Toolkit.py              ← Main application
├── data_hub.py                        ← Central data management
│
├── features/                          ← PRODUCTIVITY FEATURES
│   ├── auto_save.py                    ← Thread-safe auto-save (UPDATED)
│   ├── macro_recorder.py               ← Workflow recorder (UPDATED — 13 types)
│   ├── project_manager.py              ← Project save/load
│   ├── script_exporter.py              ← Python/R export
│   ├── tooltip_manager.py              ← Hover tooltips
│   └── recent_files_manager.py         ← Tracks last 10 files
│
├── ui/                                ← USER INTERFACE (EXPANDED in v2.5)
│   ├── right_panel.py                  ← Classification HUD (updated)
│   ├── right_panel_archaeology.py      ← NEW domain panel
│   ├── right_panel_chromatography.py   ← NEW domain panel
│   ├── right_panel_electrochem.py      ← NEW domain panel
│   ├── right_panel_geochemistry.py     ← NEW domain panel (TAS + AFM embedded)
│   ├── right_panel_geochronology.py    ← NEW domain panel
│   ├── right_panel_geophysics.py       ← NEW domain panel
│   ├── right_panel_materials.py        ← NEW domain panel
│   ├── right_panel_meteorology.py      ← NEW domain panel
│   ├── right_panel_molecular.py        ← NEW domain panel
│   ├── right_panel_petrology.py        ← NEW domain panel
│   ├── right_panel_physics.py          ← NEW domain panel
│   ├── right_panel_solution.py         ← NEW domain panel
│   ├── right_panel_spatial.py          ← NEW domain panel
│   ├── right_panel_spectroscopy.py     ← NEW domain panel
│   ├── right_panel_structural.py       ← NEW domain panel
│   ├── right_panel_zooarch.py          ← NEW domain panel
│   ├── right_panel_patch.py            ← Selection sync patch notes
│   ├── center_panel.py                 ← Main table (updated)
│   └── left_panel.py                   ← Import + hardware (updated)
│
├── plugins/
│   ├── add-ons/
│   │   ├── toolkit_ai.py               ← NEW — Built-in AI assistant
│   │   ├── statistical_console.py      ← NEW — Stats for non-programmers
│   │   └── [23 other add-ons]
│   ├── hardware/
│   │   └── [16 hardware suites]
│   └── software/
│       └── [37+ software plugins]
│
├── config/
│   ├── ai_knowledge_cache.json         ← NEW — Toolkit AI scan cache
│   ├── macros.json
│   ├── recent_files.json
│   └── user_settings.json
│
└── samples/                           ← EXPANDED in v2.5 (30+ test files)
    ├── archaeology_test.csv
    ├── chromatography_test.csv
    ├── electrochem_test.csv
    ├── geochemistry_test.csv
    ├── geochronology_test.csv
    ├── geophysics_test.csv
    ├── materials_test.csv
    ├── meteorology_test.csv
    ├── molecular_test.csv
    ├── petrology_test.csv
    ├── physics_test.csv
    ├── solution_test.csv
    ├── spatial_test.csv
    ├── spectroscopy_test.csv
    ├── structural_test.csv
    ├── zooarch_test.csv
    └── [master test datasets]

Quick Install
  git clone https://gitlab.com/sefy76/scientific-toolkit.git
  cd scientific-toolkit
  pip install -r requirements.txt
  python Scientific-Toolkit.py

New Dependency (v2.5)
  ttkbootstrap >= 1.10.0    # Modern UI framework (replaces ttk throughout)
  Install:  pip install ttkbootstrap

Verifying New Features
  ✅ Press F1                       — keyboard shortcuts dialog
  ✅ Hover any button               — tooltip appears after 500ms
  ✅ File → Recent Files            — menu exists
  ✅ Ctrl+R → do something → Ctrl+T — macro recorded with all 13 action types
  ✅ Advanced → Plugin Manager      — Toolkit AI and Statistical Console listed
  ✅ Import geochemistry data       — right panel offers to switch to Geochemistry panel
  ✅ Check auto_save/ folder        — recovery.stproj created after 5 minutes

────────────────────────────────────────────────────────────────────────────────────
🆘 Troubleshooting
────────────────────────────────────────────────────────────────────────────────────

Symptom                         Likely Cause                Solution
Tooltips not showing            tooltip_manager.py missing  Check features/ folder
Recent files empty              No files imported yet       Import a file, then check
Macros not recording            Recording not started       Press Ctrl+R first
Project load fails              Corrupted .stproj           Open in text editor to inspect
Field panel not switching       Column names not recognised Check column naming conventions
Toolkit AI not appearing        Plugin not enabled          Enable via Plugin Manager
Statistical Console missing     Plugin not enabled          Enable via Plugin Manager
Auto-save recovery not shown    File >24h old               Recovery file expired, ignored
ttkbootstrap import error       Not installed               pip install ttkbootstrap

────────────────────────────────────────────────────────────────────────────────────
📊 Feature Comparison Matrix
────────────────────────────────────────────────────────────────────────────────────

Feature                 v1.0     v2.0      v2.5          Improvement
Keyboard Shortcuts      ❌        ✅         ✅             100% new in v2.0
Recent Files            ❌        ✅         ✅             100% new in v2.0
Tooltips                ❌        ✅         ✅             100% new in v2.0
Project Save/Load       ❌        ✅         ✅             100% new in v2.0
Script Export           ❌        ✅         ✅             100% new in v2.0
Macro Recorder          ❌        ✅ 4 types  ✅ 13 types    +9 action types in v2.5
Toolkit AI              ❌        ❌         ✅ v2.2        100% new in v2.5
Field Panels            ❌        ❌         ✅ 16 domains  100% new in v2.5
Statistical Console     ❌        ❌         ✅             100% new in v2.5
Auto-Save (thread-safe) ❌        ❌         ✅             Race condition fixed in v2.5
Classification Engines  41        70         70            +70% in v2.0
Scientific Protocols    0         50         50            100% new in v2.0
Software Plugins        28        37         37            +32% in v2.0
Add-on Plugins          17        23         25            +2 in v2.5
Hardware Suites         4 files   7 files    16 suites     Expanded in v2.5
Total Plugins           ~45       67         90+           Growing
UI Framework            tkinter   ttk        ttkbootstrap  Modernised in v2.5
Sample Files            5         10         30+           +20 domain test files in v2.5

────────────────────────────────────────────────────────────────────────────────────
📝 License & Acknowledgments
────────────────────────────────────────────────────────────────────────────────────

License
  CC BY-NC-SA 4.0
  ✅ Free for research, education, museums
  ✅ Free for commercial use (consulting, analysis)
  ❌ Cannot sell the software itself
  ❌ Cannot use code in commercial products

Acknowledgments
  v2.5 features developed with Claude (Anthropic)
  Original Scientific Toolkit by Sefy Levy
  Based on Basalt Provenance Triage Toolkit v10.2

Citation
  Scientific Toolkit v2.5 (2026)
  Sefy Levy
  https://gitlab.com/sefy76/scientific-toolkit
  DOI: 10.5281/zenodo.18727756

📧 Support & Feedback
  Email:         sefy76@gmail.com
  GitLab Issues: https://gitlab.com/sefy76/scientific-toolkit/-/issues
  DOI:           https://doi.org/10.5281/zenodo.18727756

When Reporting Issues
  - Your operating system
  - Python version
  - Error message (copy-paste)
  - Steps to reproduce
  - What you expected to happen

🎉 Final Thoughts

These 10 features transform Scientific Toolkit into a complete workflow automation
and AI-assisted analysis platform:

  ⌨️ Shortcuts         → Faster interaction
  📜 Recent Files      → Faster access
  💡 Tooltips          → Faster learning
  💾 Projects          → Complete persistence
  🐍 Scripts           → Unlimited automation
  🎬 Macros            → One-click workflows  (now 13 action types)
  🧠 Toolkit AI        → Built-in expert guidance
  🔬 Field Panels      → Instant domain analysis
  📊 Stats Console     → Stats without coding
  💾 Auto-Save (fixed) → Never lose work again

Enjoy Scientific Toolkit v2.5! 🚀

"Science is about reproducibility. These features make reproducibility automatic."
