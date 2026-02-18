# Scientific Toolkit v2.0 - Enhanced Edition

## 🎉 New Features Added

This enhanced version includes 6 major new features to improve your workflow efficiency and productivity:

---

## ✨ Feature 1: Keyboard Shortcuts

Save time with comprehensive keyboard shortcuts for all common operations.

### Available Shortcuts:

#### File Operations
- `Ctrl+N` - New Project
- `Ctrl+O` - Open Project
- `Ctrl+S` - Save Project
- `Ctrl+I` - Import Data
- `Ctrl+E` - Export CSV
- `Ctrl+Q` - Quit Application

#### Edit Operations
- `Delete` - Delete Selected Rows
- `Ctrl+A` - Select All Rows
- `Ctrl+F` - Focus Search Box

#### Workflow/Macros
- `Ctrl+R` - Start Recording Macro
- `Ctrl+T` - Stop Recording Macro
- `Ctrl+M` - Manage Macros

#### Other
- `F1` - Show Keyboard Shortcuts Help
- `F5` - Refresh All Panels

### Usage:
Simply press the key combination while the application is focused. All shortcuts are also shown in the menu bars with their accelerator keys.

---

## 📜 Feature 2: Recent Files

Quickly access your recently opened files from the File menu.

### Features:
- Tracks last 10 opened files automatically
- Displays file names with numbering (1-10)
- Shows full file path on hover
- Files are verified to exist before display
- Can clear recent files list

### Usage:
1. Go to `File → Recent Files`
2. Click on any recent file to open it
3. Use `Clear Recent Files` to reset the list

### Storage:
Recent files are stored in `config/recent_files.json` and persist between sessions.

---

## 💡 Feature 3: Tooltips Everywhere

Helpful tooltips appear when you hover over buttons and controls.

### Coverage:
- Import/Export buttons with detailed explanations
- Plot generation controls
- Classification apply button
- All major UI elements

### Features:
- 500ms delay before tooltip appears (not intrusive)
- Clear, concise descriptions
- Yellow background for easy visibility
- Automatically disappears when mouse moves away

### Customization:
Tooltips are managed through `tooltip_manager.py` and can be easily extended.

---

## 💾 Feature 4: Project Save/Load

Save your entire workspace and restore it later!

### What Gets Saved:
- All data samples with their current state
- Column order and structure
- Current filters and search terms
- Selected classification scheme
- Window size and position
- UI state (selected tabs, page numbers)

### File Format:
Projects are saved as `.stproj` files (JSON format) which include:
```json
{
  "metadata": {
    "version": "2.0",
    "saved_at": "2026-02-17T...",
    "app_version": "2.0"
  },
  "data": {
    "samples": [...],
    "column_order": [...]
  },
  "ui_state": {
    "center": {...},
    "right": {...},
    "window": {...}
  }
}
```

### Usage:

#### Save Project:
1. `File → Save Project` (or `Ctrl+S`)
2. Choose location and filename
3. Project saved with `.stproj` extension

#### Load Project:
1. `File → Open Project` (or `Ctrl+O`)
2. Select a `.stproj` file
3. Everything restored to saved state

#### New Project:
1. `File → New Project` (or `Ctrl+N`)
2. Confirms before clearing current data
3. Resets all UI to default state

---

## 🐍 Feature 5: Export to Python Scripts

Generate executable Python code from your current workflow!

### Features:
- Exports data processing as standalone Python scripts
- Includes classification logic
- Generates plotting code
- Can create fully runnable scripts
- Preserves your current filters and settings

### Export Options:

When you select `File → Export to Python Script`, you can choose:

- ✅ **Include current data** - Embeds your dataset in the script
- ✅ **Include classification logic** - Exports classification functions
- ✅ **Include plotting code** - Generates matplotlib visualization code
- ✅ **Include current filters** - Applies your search/filter settings
- ✅ **Make standalone** - Creates a runnable script with main() function

### Generated Script Includes:
```python
#!/usr/bin/env python3
"""
Scientific Toolkit Workflow Export
Generated: 2026-02-17 10:30:00
"""

import pandas as pd
import matplotlib.pyplot as plt

# Your data
data = [...]
df = pd.DataFrame(data)

# Classification logic
def classify_sample(sample):
    # Your classification rules
    return "CLASSIFICATION"

# Generate plots
def create_plots():
    # Your visualization code
    plt.figure(figsize=(10, 6))
    # ...

if __name__ == "__main__":
    # Run the workflow
    print("Scientific Toolkit Workflow")
    # ...
```

### Usage:
1. Set up your workflow (import data, classify, filter, etc.)
2. Go to `File → Export to Python Script`
3. Select which components to include
4. Click Export and choose filename
5. Run the generated `.py` file standalone!

### Use Cases:
- **Share workflows** with colleagues who don't have the toolkit
- **Batch processing** - modify the script for multiple files
- **Documentation** - generated code shows exactly what you did
- **Integration** - incorporate into larger Python pipelines
- **Learning** - see the Python code behind your GUI actions

---

## 🎬 Feature 6: Macro/Workflow Recorder

Record your actions and replay them later - the most powerful new feature!

### What It Does:
Records all your interactions with the toolkit and allows you to:
- Save them as reusable macros
- Replay them with one click
- Share them with colleagues
- Import/export macro files

### Recordable Actions:
- File import operations
- Classification runs
- Filter applications
- Data exports
- Plot generation
- Row additions
- Delete operations

### How to Use:

#### Recording a Macro:
1. Click `Workflow → Start Recording` (or `Ctrl+R`)
2. Perform your workflow normally
3. Click `Workflow → Stop Recording` (or `Ctrl+T`)
4. Enter a name for your macro
5. Macro saved automatically

#### Managing Macros:
1. Go to `Workflow → Manage Macros` (or `Ctrl+M`)
2. See all your saved macros with action counts
3. Select a macro to:
   - **Run** - Execute the workflow
   - **Details** - See step-by-step actions
   - **Export** - Save to `.json` file
   - **Import** - Load from `.json` file
   - **Delete** - Remove macro

#### Replaying a Macro:
1. Open Macro Manager
2. Select macro from list
3. Click **Run**
4. Watch as actions replay automatically!

### Macro File Format:
```json
{
  "name": "My Workflow",
  "actions": [
    {
      "type": "import_file",
      "params": {"filepath": "/path/to/data.csv"},
      "timestamp": "2026-02-17T10:00:00"
    },
    {
      "type": "classify",
      "params": {"scheme": "Basalt Classification", "target": "all"},
      "timestamp": "2026-02-17T10:01:00"
    },
    {
      "type": "export_csv",
      "params": {"filepath": "/path/to/output.csv"},
      "timestamp": "2026-02-17T10:02:00"
    }
  ]
}
```

### Storage:
Macros are stored in `config/macros.json` and persist between sessions.

### Use Cases:
- **Repetitive tasks** - Record once, replay forever
- **Consistency** - Ensure same steps every time
- **Training** - Share workflows with new users
- **Quality control** - Standardize data processing
- **Batch processing** - Process multiple datasets identically

### Advanced Features:
- **Error handling** - Continues or stops on error (user choice)
- **Action verification** - Checks file existence before replay
- **Conditional replay** - Skip actions if data doesn't match
- **Macro editing** - Export, modify JSON, re-import

---

## 📦 Installation

### New Dependencies:
The enhanced version requires the same dependencies as the original, plus the new module files:

```
Scientific-Toolkit-Enhanced.py  (main application)
tooltip_manager.py              (tooltips feature)
recent_files_manager.py         (recent files feature)
macro_recorder.py               (macro recording feature)
project_manager.py              (project save/load feature)
script_exporter.py              (Python script export feature)
```

### File Structure:
```
your_project/
├── Scientific-Toolkit-Enhanced.py
├── tooltip_manager.py
├── recent_files_manager.py
├── macro_recorder.py
├── project_manager.py
├── script_exporter.py
├── data_hub.py
├── ui/
│   ├── left_panel.py
│   ├── center_panel.py
│   ├── right_panel.py
│   └── results_dialog.py
├── config/
│   ├── recent_files.json (auto-created)
│   ├── macros.json (auto-created)
│   └── ...
└── engines/
    └── ...
```

---

## 🚀 Quick Start Guide

### First Launch:
1. Run `python Scientific-Toolkit-Enhanced.py`
2. Press `F1` to see all keyboard shortcuts
3. Import some data (`Ctrl+I`)
4. Try recording a macro (`Ctrl+R`)
5. Explore the new File menu options!

### Essential Workflow:
```
1. Import data (Ctrl+I)
2. Start recording (Ctrl+R)
3. Classify your samples
4. Apply filters
5. Export results (Ctrl+E)
6. Stop recording (Ctrl+T)
7. Save as macro for next time!
```

### Tips & Tricks:
- Use `Ctrl+F` to quickly find samples
- `Ctrl+A` to select all for bulk operations
- Save your project (`Ctrl+S`) before experiments
- Export workflows to Python for documentation
- Create macros for common tasks to save hours!

---

## 🆘 Troubleshooting

### Tooltips Not Showing:
- Check if `features/tooltip_manager.py` exists in the features folder
- Wait 500ms for tooltip to appear
- Try moving mouse off and back on the widget

### Macros Not Recording:
- Ensure recording started successfully (check menu)
- Some actions may not be recordable yet
- Check console for recording confirmation messages

### Recent Files Not Updating:
- Ensure `config/` directory is writable
- Check `config/recent_files.json` exists
- File must exist to appear in recent list

### Project Load Fails:
- Verify `.stproj` file is valid JSON
- Check file wasn't corrupted
- Try opening in text editor to inspect

### Keyboard Shortcuts Not Working:
- Ensure application window has focus
- Some shortcuts may conflict with OS
- Check Help → Keyboard Shortcuts for full list

---

## 📝 Feature Comparison

| Feature | Original | Enhanced |
|---------|----------|----------|
| Keyboard Shortcuts | ❌ | ✅ Full coverage |
| Recent Files | ❌ | ✅ Last 10 files |
| Tooltips | ❌ | ✅ All controls |
| Project Save/Load | ❌ | ✅ Complete state |
| Script Export | ❌ | ✅ Python code |
| Macro Recording | ❌ | ✅ Full workflow |
| Import/Export | ✅ | ✅ + Macros |
| Classification | ✅ | ✅ + Record |
| Plotting | ✅ | ✅ + Export |

---

## 🎯 Development Time Estimates

| Feature | Priority | Est. Time | Status |
|---------|----------|-----------|--------|
| Keyboard Shortcuts | Low | 1 hour | ✅ Complete |
| Recent Files | Low | 1 hour | ✅ Complete |
| Tooltips | Medium | 3-4 hours | ✅ Complete |
| Project Save/Load | Medium | 4-5 hours | ✅ Complete |
| Script Export | Medium | 3-4 hours | ✅ Complete |
| Macro Recorder | High | 8-10 hours | ✅ Complete |

**Total Development Time: ~20-25 hours**

---

## 📄 License

Same as original Scientific Toolkit v2.0:
- CC BY-NC-SA 4.0
- Free for research and educational use
- Created by Sefy Levy (2026)

---

## 🙏 Acknowledgments

Enhanced features developed with assistance from Claude (Anthropic).

Original Scientific Toolkit by Sefy Levy based on Basalt Provenance Triage Toolkit v10.2.

---

## 📧 Support & Feedback

- Email: sefy76@gmail.com
- DOI: https://doi.org/10.5281/zenodo.18499129

If these enhancements have improved your workflow, please consider supporting the project!

---

**Enjoy the enhanced Scientific Toolkit! 🚀**
