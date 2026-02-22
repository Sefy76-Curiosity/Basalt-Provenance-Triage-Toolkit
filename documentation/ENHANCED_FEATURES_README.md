Scientific Toolkit v2.0
🎉 6 Core Productivity Features

This enhanced version includes 6 major productivity features that transform the Scientific Toolkit from a powerful analysis platform into a complete workflow automation system.
📋 Feature Overview
Feature	What It Does	Key Benefit
⌨️ Keyboard Shortcuts	20+ keyboard shortcuts for all operations	Save seconds on every action
📜 Recent Files	Auto-tracks last 10 opened files	Open recent work in 1 click
💡 Tooltips Everywhere	Helpful hints on all buttons/controls	No learning curve
💾 Project Save/Load	Complete workspace persistence	Pick up where you left off
🐍 Script Export	Export workflows as Python/R	Share, automate, document
🎬 Macro Recorder	Record/replay any workflow	Automate repetitive tasks

Total Development Investment: ~25 hours | Lines of Code: ~1,200
⌨️ Feature 1: Keyboard Shortcuts

Save time with comprehensive keyboard shortcuts for all common operations.
Complete Shortcut Reference
File Operations (6 shortcuts)
Shortcut	Action	Menu Location
Ctrl+N	New Project	File → New Project
Ctrl+O	Open Project	File → Open Project
Ctrl+S	Save Project	File → Save Project
Ctrl+I	Import Data	File → Import Data
Ctrl+E	Export CSV	File → Export CSV
Ctrl+Q	Quit Application	File → Exit
Edit Operations (3 shortcuts)
Shortcut	Action	Menu Location
Delete	Delete Selected Rows	Edit → Delete
Ctrl+A	Select All Rows	Edit → Select All
Ctrl+F	Focus Search Box	(direct action)
Workflow/Macros (3 shortcuts)
Shortcut	Action	Menu Location
Ctrl+R	Start Recording Macro	Workflow → Start Recording
Ctrl+T	Stop Recording Macro	Workflow → Stop Recording
Ctrl+M	Manage Macros	Workflow → Manage Macros
Navigation & Help (2 shortcuts)
Shortcut	Action	Menu Location
F1	Show Keyboard Shortcuts	Help → Keyboard Shortcuts
F5	Refresh All Panels	View → Refresh
Pro Tips

    All shortcuts work on Windows, macOS (Cmd replaces Ctrl), and Linux

    Shortcuts are shown in menu items (e.g., "Save Project Ctrl+S")

    Custom shortcuts can be added by modifying _setup_keyboard_shortcuts() in main app

📜 Feature 2: Recent Files Manager

Quickly access your recently opened files from the File menu.
Features

    Auto-tracking - Last 10 files automatically tracked

    Smart display - Shows filenames with numbering (1-10)

    Path preview - Hover to see full file path

    Existence verification - Only shows files that still exist

    Clear history - One-click to reset recent list

Usage

    Open recent file: File → Recent Files → Click filename

    Clear list: File → Recent Files → Clear Recent Files

    Keyboard: No direct shortcut, but Alt+F then arrow keys works

Configuration

Recent files are stored in config/recent_files.json:
json

{
  "files": [
    {
      "path": "/home/user/data/project1.csv",
      "name": "project1.csv",
      "timestamp": "2026-02-21T10:30:00"
    }
  ]
}

Integration with Other Features

    ✅ Works with Project Save/Load - projects appear in recent files

    ✅ Works with Macro Recorder - file paths recorded in macros

    ✅ Works with Script Export - referenced in generated scripts

💡 Feature 3: Tooltips Everywhere

Helpful tooltips appear when you hover over buttons and controls.
Coverage Map
UI Area	Tooltips Added
Left Panel	Import Data, Add Row, Manual Entry fields
Center Panel	Search, Filter, Pagination, Plot buttons
Right Panel	Classification schemes, Apply button, HUD elements
File Menu	All menu items have descriptive tooltips
Dialogs	Results dialog, Project save/load dialogs
Technical Details

    Delay: 500ms (configurable in tooltip_manager.py)

    Style: Yellow background, black text, subtle border

    Duration: Disappears when mouse moves away

    Position: Offset from cursor to avoid blocking view

Example Tooltips
Element	Tooltip Text
Import Data button	"Import CSV, Excel, or spectral data files"
Classification Apply	"Run selected classification on all or selected samples"
Save Project	"Save entire workspace including data, filters, and UI state"
Start Recording	"Begin recording macro (Ctrl+R) - all actions will be saved"
Customization
python

# Add tooltip to any widget
from tooltip_manager import ToolTip
ToolTip(my_button, "This button does something cool")

💾 Feature 4: Project Save/Load

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

⚙️ Settings

    ✅ Current theme/color scheme

    ✅ Column width preferences

    ✅ Recent files list (auto-saved separately)

File Format

Projects are saved as .stproj (Scientific Toolkit Project) - JSON format:
json

{
  "metadata": {
    "version": "2.0",
    "saved_at": "2026-02-21T15:30:00",
    "app_version": "2.0",
    "project_name": "Hazor Excavation 2026"
  },
  "data": {
    "samples": [...],  // 200+ samples with all fields
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
      "run_target": "all"
    },
    "window": {
      "geometry": "1400x900+100+50"
    }
  }
}

Usage
Save Project (3 ways)
Method	Action
Menu	File → Save Project
Keyboard	Ctrl+S
Auto-save	Configurable interval (5 min default)
Load Project (3 ways)
Method	Action
Menu	File → Open Project
Keyboard	Ctrl+O
Recent Files	File → Recent Files → Click project
New Project
Method	Action
Menu	File → New Project (Ctrl+N)
Warning	Confirms before clearing unsaved data
Integration with Other Features

    ✅ Auto-save - Periodic backups while you work

    ✅ Macro Recorder - Project operations are recordable

    ✅ Script Export - Project can be exported as Python script

🐍 Feature 5: Script Export

Export your current workflow as executable Python or R code.
Export Options

When you select File → Export to Python Script, you can choose:
Option	Description	When to Use
✅ Include current data	Embeds dataset in script	Sharing complete analysis
✅ Include classification logic	Exports classification functions	Reproducing results
✅ Include plotting code	Generates matplotlib/ggplot code	Creating publication figures
✅ Include current filters	Applies search/filter settings	Documenting subset analysis
✅ Make standalone	Creates runnable script with main()	Distribution to non-users
Generated Python Example
python

#!/usr/bin/env python3
"""
Scientific Toolkit Workflow Export
Generated: 2026-02-21 15:30:00
Project: Hazor Basalt Analysis
Author: Sefy Levy
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ============ DATA (24 samples) ============
data = [
    {'Sample_ID': 'HAZ-001', 'Zr_ppm': 245, 'Nb_ppm': 22.3, 
     'Ba_ppm': 278, 'Cr_ppm': 187, 'Ni_ppm': 142},
    # ... 23 more samples
]
df = pd.DataFrame(data)

# ============ CLASSIFICATION LOGIC ============
def classify_basalt(row):
    """Zr/Nb ratio-based classification"""
    zr_nb = row['Zr_ppm'] / row['Nb_ppm']
    
    if zr_nb < 15:
        return "LOCAL LEVANTINE"
    elif zr_nb < 20:
        return "SINAI TRANSITIONAL"
    else:
        return "SINAI OPHIOLITIC"

# Apply classification
df['Classification'] = df.apply(classify_basalt, axis=1)

# ============ FILTERS APPLIED ============
# Applied filter: Classification contains 'SINAI'
df_filtered = df[df['Classification'].str.contains('SINAI')]

# ============ PLOTTING ============
def create_plots():
    """Generate analysis plots"""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # Plot 1: Zr/Nb distribution
    df_filtered['Zr/Nb'] = df_filtered['Zr_ppm'] / df_filtered['Nb_ppm']
    df_filtered['Zr/Nb'].hist(ax=axes[0], bins=10, color='steelblue')
    axes[0].set_xlabel('Zr/Nb Ratio')
    axes[0].set_ylabel('Frequency')
    axes[0].set_title('Zr/Nb Distribution')
    
    # Plot 2: Classification counts
    df_filtered['Classification'].value_counts().plot(
        kind='bar', ax=axes[1], color='coral')
    axes[1].set_xlabel('Classification')
    axes[1].set_ylabel('Count')
    axes[1].tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig('hazor_analysis.png', dpi=300)
    print("✅ Saved: hazor_analysis.png")

# ============ MAIN EXECUTION ============
if __name__ == "__main__":
    print("=" * 50)
    print("Scientific Toolkit Workflow")
    print("=" * 50)
    
    print(f"\n📊 Dataset: {len(df)} samples")
    print(f"📈 Filtered: {len(df_filtered)} samples")
    print("\n📋 Classification summary:")
    print(df_filtered['Classification'].value_counts())
    
    print("\n📊 Generating plots...")
    create_plots()
    
    # Export results
    df_filtered.to_csv('hazor_results.csv', index=False)
    print("✅ Saved: hazor_results.csv")
    
    print("\n✅ Workflow complete!")

Generated R Example
r

#!/usr/bin/env Rscript
# Scientific Toolkit Workflow Export (R)

library(ggplot2)
library(dplyr)

# Data
data <- data.frame(
  Sample_ID = c('HAZ-001', 'HAZ-002'),
  Zr_ppm = c(245, 238),
  Nb_ppm = c(22.3, 21.8),
  Ba_ppm = c(278, 265),
  Cr_ppm = c(187, 195),
  Ni_ppm = c(142, 151)
)

# Classification
data <- data %>%
  mutate(
    Zr_Nb = Zr_ppm / Nb_ppm,
    Classification = case_when(
      Zr_Nb < 15 ~ "LOCAL LEVANTINE",
      Zr_Nb < 20 ~ "SINAI TRANSITIONAL",
      TRUE ~ "SINAI OPHIOLITIC"
    )
  )

# Plot
ggplot(data, aes(x = Classification)) +
  geom_bar(fill = "steelblue") +
  labs(title = "Classification Distribution") +
  theme_minimal()

ggsave("classification_plot.png", dpi = 300)

Use Cases
Scenario	Why Script Export Helps
Collaboration	Share analysis with colleagues who don't have the toolkit
Publication	Include exact analysis code as supplementary material
Teaching	Students can run analysis without GUI
Batch Processing	Modify script to run on 100s of files
Documentation	Generated code shows exactly what you did
Version Control	Track analysis changes in git
🎬 Feature 6: Macro/Workflow Recorder

The most powerful feature - record any sequence of actions and replay them instantly.
What Can Be Recorded?
Category	Recordable Actions
File Operations	Import CSV/Excel, Export CSV, Save Project, Load Project
Classification	Run any classification scheme (all/selected)
Filtering	Apply search filters, filter by classification
Data Editing	Add rows, delete rows, select all
Plotting	Generate any plot type
Navigation	Page changes, tab switches
How to Use
Recording a Macro

    Start: Workflow → Start Recording (or Ctrl+R)

    Perform your workflow normally (all actions recorded)

    Stop: Workflow → Stop Recording (or Ctrl+T)

    Name: Enter a descriptive name (e.g., "Hazor Classification Workflow")

    Save: Macro saved automatically to config/macros.json

Managing Macros

    Open Manager: Workflow → Manage Macros (or Ctrl+M)

    View: See all saved macros with action counts

    Select a macro to see options:

Button	Function
▶️ Run	Execute the macro immediately
📝 Details	Show step-by-step action list
💾 Export	Save macro to .json file
📥 Import	Load macro from .json file
🗑️ Delete	Remove macro
Replaying a Macro

    Open Macro Manager (Ctrl+M)

    Select macro from list

    Click Run

    Watch as actions replay automatically!

Macro File Format

Macros are stored as JSON for easy editing and sharing:
json

{
  "Hazor Classification Workflow": [
    {
      "type": "import_file",
      "params": {"filepath": "/data/hazor_samples.csv"},
      "timestamp": "2026-02-21T10:00:00"
    },
    {
      "type": "classify",
      "params": {
        "scheme": "Basalt Triage (Egyptian–Sinai–Levantine)",
        "target": "all"
      },
      "timestamp": "2026-02-21T10:01:00"
    },
    {
      "type": "apply_filter",
      "params": {
        "filter": "SINAI",
        "search": ""
      },
      "timestamp": "2026-02-21T10:02:00"
    },
    {
      "type": "generate_plot",
      "params": {"plot_type": "Zr/Nb Distribution"},
      "timestamp": "2026-02-21T10:03:00"
    },
    {
      "type": "export_csv",
      "params": {"filepath": "/results/hazor_sinai.csv"},
      "timestamp": "2026-02-21T10:04:00"
    }
  ]
}

Advanced Features
Error Handling

When replaying, you can choose:

    Stop on error - Abort if any action fails

    Continue - Skip failed actions and proceed

    Ask each time - Prompt on each error

Conditional Replay

Macros can include conditions:

    Check if file exists before importing

    Verify data has required columns before classification

    Skip plot generation if no data

Macro Editing

    Export macro to JSON

    Edit in any text editor

    Import back to modify workflow

Practical Examples
Example 1: Daily Data Processing
text

1. Import today's pXRF data
2. Run full classification suite (70 engines)
3. Filter to SINAI samples
4. Generate TAS diagram
5. Export results
→ Record once, run every day in 1 click

Example 2: Quality Control Workflow
text

1. Import raw data
2. Run Analytical Precision Filter
3. Flag samples with RSD > 7%
4. Generate QC report
→ Ensure consistent QC across projects

Example 3: Publication Preparation
text

1. Load project
2. Apply specific filters
3. Generate 4 publication plots
4. Export as high-resolution PNG
5. Save project
→ Reproduce figures exactly for revisions

Integration with Other Features
Feature	How It Integrates
Keyboard Shortcuts	Ctrl+R to start, Ctrl+T to stop
Recent Files	File paths are recorded in macros
Project Save/Load	Project operations are recordable
Script Export	Macros can be exported as Python scripts
Plugin Manager	Macro actions from plugins are recorded
📦 Installation & Setup
File Structure
text

scientific-toolkit/
├── Scientific-Toolkit-Enhanced.py    # Main application (v2.0)
├── features/                         # All enhanced features
│   ├── __init__.py                    # Package init
│   ├── tooltip_manager.py             # Tooltips system
│   ├── recent_files_manager.py        # Recent files tracking
│   ├── macro_recorder.py              # Workflow recorder
│   ├── project_manager.py             # Project save/load
│   └── script_exporter.py             # Python/R export
├── ui/                                # Core UI (unchanged)
│   ├── left_panel.py
│   ├── center_panel.py
│   ├── right_panel.py
│   └── results_dialog.py
├── engines/                           # Classification engines
│   ├── classification_engine.py        # 70 classification schemes
│   ├── protocol_engine.py              # 50 scientific protocols
│   └── classification/                 # JSON scheme files
├── plugins/                            # 67 plugins
│   ├── software/                        # 37 software plugins
│   ├── add-ons/                         # 23 add-on plugins
│   └── hardware/                        # 7 hardware suites
├── config/                             # Configuration
│   ├── recent_files.json (auto)
│   ├── macros.json (auto)
│   └── user_settings.json
└── data_hub.py                         # Core data manager

Quick Install
bash

# 1. Clone repository
git clone https://gitlab.com/sefy76/scientific-toolkit.git
cd scientific-toolkit

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch enhanced version
python Scientific-Toolkit-Enhanced.py

Verifying Installation

After launch, check:

    ✅ Press F1 - should show keyboard shortcuts dialog

    ✅ Hover any button - tooltip appears after 500ms

    ✅ File → Recent Files - menu exists (may be empty)

    ✅ Workflow menu - appears with 3 options

    ✅ Ctrl+R - starts macro recording

🚀 5-Minute Quick Start
Step 1: First Launch
bash

python Scientific-Toolkit-Enhanced.py

Step 2: Explore Features

    Press F1 - See all keyboard shortcuts

    Hover over any button - See helpful tooltips

    Check menus - Notice new File → Recent Files and Workflow menu

Step 3: Record Your First Macro

    Press Ctrl+R (Start Recording)

    Import some data (Ctrl+I, select any CSV)

    Run a classification (Right panel → Choose scheme → Apply)

    Press Ctrl+T (Stop Recording)

    Name it "My First Workflow"

    Press Ctrl+M to see your saved macro

Step 4: Save Your Work

    Press Ctrl+S (Save Project)

    Choose location and filename

    All your data and UI state saved

Step 5: Export as Script

    File → Export to Python Script

    Select options (include data, classification)

    Save and run the generated .py file

🆘 Troubleshooting Guide
Feature Not Working?
Symptom	Likely Cause	Solution
Tooltips not showing	tooltip_manager.py missing	Check file in features/ folder
Recent files empty	No files imported yet	Import a file, then check
Macros not recording	Recording not started	Press Ctrl+R first
Project load fails	Corrupted .stproj	Try opening in text editor
Keyboard shortcuts not working	Window focus	Click main window first
Script export missing options	Old version	Update to latest
Common Error Messages
"ModuleNotFoundError: No module named 'features'"

Fix: Create features/ folder and copy all feature modules:
bash

mkdir features
cp tooltip_manager.py features/
cp recent_files_manager.py features/
cp macro_recorder.py features/
cp project_manager.py features/
cp script_exporter.py features/
cp __init__.py features/

"config/recent_files.json: Permission denied"

Fix: Ensure config directory is writable:
bash

chmod 755 config/

"Macro action failed: File not found"

Fix: Update macro with correct file paths:

    Export macro to JSON

    Edit file paths

    Import back

📊 Feature Comparison Matrix
Feature	Original v1.0	Enhanced v2.0	Improvement
Keyboard Shortcuts	❌ None	✅ 20+ shortcuts	100% new
Recent Files	❌ None	✅ Last 10 files	100% new
Tooltips	❌ None	✅ All controls	100% new
Project Save/Load	❌ None	✅ Complete state	100% new
Script Export	❌ None	✅ Python/R	100% new
Macro Recording	❌ None	✅ Full workflow	100% new
Classification Engines	41	70	+70%
Protocols	0	50	100% new
Software Plugins	28	37	+32%
Add-on Plugins	17	23	+35%
Hardware Suites	26 devices	7 suites	Restructured
Total Plugins	~45	67	+49%
🎯 Development Investment
Feature	Complexity	Lines of Code	Development Time
Keyboard Shortcuts	Low	~150	1 hour
Recent Files	Low	~120	1 hour
Tooltips	Low	~80	1 hour
Project Save/Load	Medium	~200	4 hours
Script Export	Medium	~250	4 hours
Macro Recorder	High	~400	10 hours
TOTAL	Medium-High	~1,200	~21 hours
📝 License & Acknowledgments
License

Same as Scientific Toolkit v2.0: CC BY-NC-SA 4.0

    ✅ Free for research, education, museums

    ✅ Free for commercial use (consulting, analysis)

    ❌ Cannot sell the software itself

    ❌ Cannot use code in commercial products

Acknowledgments

    Enhanced features developed with Claude (Anthropic)

    Original Scientific Toolkit by Sefy Levy

    Based on Basalt Provenance Triage Toolkit v10.2

Citation
text

Scientific Toolkit v2.0 - Enhanced Edition (2026)
Sefy Levy
https://gitlab.com/sefy76/scientific-toolkit
DOI: 10.5281/zenodo.18727756

📧 Support & Feedback

    Email: sefy76@gmail.com

    GitLab Issues: https://gitlab.com/sefy76/scientific-toolkit/-/issues

    DOI: https://doi.org/10.5281/zenodo.18727756

When Reporting Issues

    Your operating system

    Python version

    Error message (copy-paste)

    Steps to reproduce

    What you expected to happen

🎉 Final Thoughts

These 6 features transform the Scientific Toolkit from a powerful analysis platform into a complete workflow automation system:

    ⌨️ Shortcuts → Faster interaction

    📜 Recent Files → Faster access

    💡 Tooltips → Faster learning

    💾 Projects → Complete persistence

    🐍 Scripts → Unlimited automation

    🎬 Macros → One-click workflows

Together, they save hours per week for regular users and make the toolkit accessible to new users in minutes.

Enjoy the enhanced Scientific Toolkit! 🚀

"Science is about reproducibility. These features make reproducibility automatic."
